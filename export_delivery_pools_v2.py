#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DELIVERY POOL EXPORTER v2 (2026-09) -- 引擎修正 (E1 cb9fea2) + 复审 (E2-E4) 后的六候选形态 v2.
# v2 = {A4b, M_mean3_v2 (cond+tvol+cum_return_20d mean 剔上半), M_union3_v2 (三 drop 并集之外)} x {pure, +CVRv5 (剔 CVR_20d 最高 quintile)}.
# 变化 vs 2026-07-08 v1: 反转代表 reversal_skip1 -> cum_return_20d; 规则池 cmf_change_high veto -> CVR_20d veto; 引擎新口径 (T+1 vwap 成交 + 后复权).
# 自检: A4b / A4b_CVRv5 / M_mean3_v2 逐格复现 E4 L1A (tol 0.02), 任一 FAIL -> ABORT 不写交付; 池1 md5 == 7/8 那份.
# 输出: results/<ts>_delivery_pools_v2/ {pool1, 6 x pool2, _delivery_stats.csv, summary.csv, README.md}. 不碰公共库.
# READ-ONLY / import-only. 窗口 = PERIODS 不变.
import sys, os, hashlib
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import define_i11_signal, build_observation_pool, apply_hard_constraints
import comprehensive_factor_diagnosis as C

OUT_DIR = C.make_output_dir('delivery_pools_v2')
C.setup_dual_logging(OUT_DIR)
print('[out]', OUT_DIR, flush=True)

F_COND, F_TVOL, F_CR20, F_CVR = 'conditional_turnover', 'turnover_volatility_60d', 'cum_return_20d', 'CVR_20d'
SEGS = list(PERIODS.keys())
ANCHORS = {  # E4 summary.csv L1A
 ('2010-2014','A4b'):2.5046, ('2015-2018','A4b'):5.0447, ('2019-2023','A4b'):7.5665, ('2024-2026','A4b'):8.9262,
 ('2010-2014','A4b_CVRv5'):3.0584, ('2015-2018','A4b_CVRv5'):6.9892, ('2019-2023','A4b_CVRv5'):8.4299, ('2024-2026','A4b_CVRv5'):10.3293,
 ('2010-2014','M_mean3_v2'):3.5462, ('2015-2018','M_mean3_v2'):7.0335, ('2019-2023','M_mean3_v2'):5.5572, ('2024-2026','M_mean3_v2'):6.3298,
}
POOL1_MD5 = '6006780eb791fe6a7f66e3829cb23763'
DELIV = ['A4b','M_mean3_v2','M_union3_v2','A4b_CVRv5','M_mean3_v2_CVRv5','M_union3_v2_CVRv5']
FNAME = {'A4b':'A4b_pure','M_mean3_v2':'Mmean_v2_pure','M_union3_v2':'Munion_v2_pure',
         'A4b_CVRv5':'A4b_cvrveto','M_mean3_v2_CVRv5':'Mmean_v2_cvrveto','M_union3_v2_CVRv5':'Munion_v2_cvrveto'}
TOL = 0.02
E2_DECOMP = '/mnt/sda2/lichenchen/results/20260903_0935_E2_decomposition/decomp.csv'

# ---------- verbatim helpers (export_delivery_pools.py / E2) ----------
def is_bse(code):
    s = str(code); return s[:1] in ('4','8') or s[:2]=='92'

def nw_stats(x, L=5):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n=len(x)
    if n==0: return float('nan'),float('nan'),float('nan'),0
    mu=x.mean(); sd=x.std(ddof=1)
    naive = mu/(sd/np.sqrt(n)) if sd>0 else float('nan')
    e=x-mu; S=(e@e)/n
    for l in range(1,L+1):
        w=1.0-l/(L+1.0); S+=2.0*w*(e[l:]@e[:-l])/n
    se=np.sqrt(S/n) if S>0 else float('nan')
    nw= mu/se if (se==se and se>0) else float('nan')
    return mu*252*100.0, naive, nw, n

def pct_cache(cache): return {d: s.rank(pct=True) for d,s in cache.items()}

def combine(caches, how):
    keys=set(caches[0])
    for c in caches[1:]: keys &= set(c)
    out={}
    for d in keys:
        df=pd.concat([c[d] for c in caches], axis=1)
        out[d]= df.max(axis=1) if how=='max' else (df.median(axis=1) if how=='median' else df.mean(axis=1))
    return out

def bench_industry_shares(clean_df, industry_df):
    cl=clean_df.values; ind=industry_df.values if industry_df is not None else None; shares=[]
    for t in range(cl.shape[0]):
        idx=np.where(cl[t]==1)[0]; tot=len(idx)
        if tot==0 or ind is None: shares.append({}); continue
        vc=pd.Series(ind[t,idx]).value_counts(dropna=True); shares.append((vc/tot).to_dict())
    return shares

def assign_weights_dev(holdings, industry_df, shares, max_stock=0.01, max_ind_dev=0.03):
    h=holdings.values; ind=industry_df.values if industry_df is not None else None
    T,N=h.shape; out=np.zeros((T,N))
    for t in range(T):
        sel=np.where(h[t]==1)[0]; n=len(sel)
        if n==0: continue
        w=np.full(n, min(1.0/n, max_stock))
        if ind is not None and shares[t]:
            si=pd.Series(ind[t,sel])
            for indcode,grp in si.groupby(si).groups.items():
                gi=np.asarray(grp,dtype=int); cap=shares[t].get(indcode,0.0)+max_ind_dev; ssum=w[gi].sum()
                if ssum>cap: w[gi]*=cap/ssum
        out[t,sel]=w
    return pd.DataFrame(out, index=holdings.index, columns=holdings.columns)

def drop_mask(neu_f, pool0, k=2):  # worst tail (top group, high=worst) flagged for drop
    kept=C.build_factor_strategy_holdings_cached(neu_f, pool0, k, [k])
    return (pool0.values==1) & ~(kept.values==1)
# ---------------------------------------------------------------------

def st(x): return nw_stats(np.asarray(x, float))

pool1_parts=[]; pool2_parts={cfg:[] for cfg in DELIV}
rows=[]; check_rows=[]; all_pass=True

for pname,(ps,pe) in PERIODS.items():
    print('\n'+'#'*70); print('PERIOD %s (%s..%s)'%(pname,ps,pe), flush=True)
    data=load_all_daily_data(start_date=ps,end_date=pe)
    feats=calc_all_daily_features(data)
    close=data['close']; bse=[c for c in close.columns if is_bse(c)]
    base_pool=get_base_pool(data)
    mature=close.notna().astype(float).rolling(20,min_periods=1).sum()>=20
    clean=((base_pool==1)&mature).astype(float)
    if bse: clean[bse]=0.0
    signal=define_i11_signal(feats, base_pool)
    obs=build_observation_pool(signal, obs_window=5)
    pool0=apply_hard_constraints(obs, data, feats, min_mcap=0)
    log_mcap=C.compute_log_mcap(data.get('mcap'))
    industry=data.get('industry_zx1', data.get('industry'))
    if industry is not None:
        industry=industry.reindex(index=close.index, columns=close.columns)
    shares=bench_industry_shares(clean, industry)
    specs={s['name']:s for s in C.get_default_factor_specs()}
    def neu(fname): return C.precompute_neutralized_factor(specs[fname]['func'](data,feats,industry), pool0, log_mcap)

    fac_tvol=specs[F_TVOL]['func'](data,feats,industry)
    neu_cond=neu(F_COND); neu_tvol=neu(F_TVOL); neu_cr20=neu(F_CR20); neu_cvr=neu(F_CVR)
    pcond,ptvol,pcr20=pct_cache(neu_cond),pct_cache(neu_tvol),pct_cache(neu_cr20)
    p0=(pool0.values==1)

    hc=C.build_factor_strategy_holdings_cached(neu_cond, pool0,2,[2])
    m_a4b=(C.build_factor_strategy_holdings_cached(
            C.precompute_neutralized_factor(fac_tvol, hc, log_mcap), hc,2,[2]).values==1)
    m_mean3=(C.build_factor_strategy_holdings_cached(combine([pcond,ptvol,pcr20],'mean'), pool0,2,[2]).values==1)
    dc,dt,dr=drop_mask(neu_cond,pool0),drop_mask(neu_tvol,pool0),drop_mask(neu_cr20,pool0)
    m_union3=(p0 & ((dc.astype(int)+dt.astype(int)+dr.astype(int))==0))
    tox_cvr=drop_mask(neu_cvr, pool0, 5)
    masks={'A4b':m_a4b,'M_mean3_v2':m_mean3,'M_union3_v2':m_union3,
           'A4b_CVRv5':(m_a4b&~tox_cvr),'M_mean3_v2_CVRv5':(m_mean3&~tox_cvr),'M_union3_v2_CVRv5':(m_union3&~tox_cvr)}

    # 副基准: pool0 DEV 同机制
    w_pool=assign_weights_dev(pd.DataFrame(p0.astype(float),index=pool0.index,columns=pool0.columns), industry, shares)
    pr_pool=C.compute_calendar_pnl(w_pool, data, clean, hold_days=5, cost_bp_bilateral=6.0)
    bm2=pr_pool['port_daily']/pr_pool['daily_position'].replace(0,np.nan)

    col_ids=np.array([int(str(c).split('.')[0]) for c in pool0.columns], dtype=np.int64)
    date_ids=np.array([pd.Timestamp(str(d)).strftime('%Y-%m-%d') for d in pool0.index])
    rr,cc=np.nonzero(p0)
    pool1_parts.append(pd.DataFrame({'ticker':col_ids[cc],'tradeDate':date_ids[rr],'in_pool':np.int8(1)}))

    print('  --- SELF-CHECK %s (vs E4 L1A) ---'%pname, flush=True)
    for cfg in DELIV:
        hold=pd.DataFrame(masks[cfg].astype(float), index=pool0.index, columns=pool0.columns)
        w=assign_weights_dev(hold, industry, shares); nh=(hold>0).sum(axis=1); pos=w.sum(axis=1)
        pr=C.compute_calendar_pnl(w, data, clean, hold_days=5, cost_bp_bilateral=6.0)
        nann,_,nnw,n=st(pr['net_excess_daily']); gann,_,_,_=st(pr['gross_excess_daily'])
        mm=C.calendar_pnl_metrics(pr['net_excess_daily']); mdd=mm['mdd'] if mm else np.nan
        ex2=pr['port_daily']-bm2*pr['daily_position']; net2=ex2-pr['daily_turnover']*6.0/1e4; n2ann,_,n2nw,_=st(net2)
        rows.append(dict(period=pname,cfg=cfg,net_ann=nann,net_nw=nnw,gross_ann=gann,mdd_net=mdd,net2_ann=n2ann,net2_nw=n2nw,
                         avg_nh=float(nh[nh>0].mean()),avg_pos=float(pos[pos>0].mean()),turn=float(pr['turnover_annual']),n=n))
        if (pname,cfg) in ANCHORS:
            anc=ANCHORS[(pname,cfg)]; d=abs(nann-anc); ok=bool(d<TOL); all_pass&=ok
            check_rows.append(dict(period=pname,cfg=cfg,got=round(nann,4),anchor=anc,dabs=round(d,4),ok=ok))
            print('    %-18s got %+8.4f  anchor %+8.4f  |d|%.4f  %s'%(cfg,nann,anc,d,'OK' if ok else 'FAIL!!'), flush=True)
        else:
            print('    %-18s got %+8.4f  (首次出数)'%(cfg,nann), flush=True)
        wv=w.values; rr,cc=np.nonzero(wv)
        pool2_parts[cfg].append(pd.DataFrame({'ticker':col_ids[cc],'tradeDate':date_ids[rr],'weight':wv[rr,cc]}))
    del data,feats,neu_cond,neu_tvol,neu_cr20,neu_cvr,masks
    print('[period done] %s'%pname, flush=True)

# ---------------- gate ----------------
chk=pd.DataFrame(check_rows); chk.to_csv(os.path.join(OUT_DIR,'check.csv'), index=False)
df=pd.DataFrame(rows); df.to_csv(os.path.join(OUT_DIR,'summary.csv'), index=False)
print('\n'+'='*66); print(chk.to_string(index=False))
if not all_pass:
    print('\n[ABORT] SELF-CHECK FAILED -- NO delivery files written.', flush=True); sys.exit(1)
print('\n[SELF-CHECK] ALL %d PASS -- writing delivery files.'%len(check_rows), flush=True)

# ---------------- 池1 ----------------
p1=pd.concat(pool1_parts, ignore_index=True).sort_values(['tradeDate','ticker']).reset_index(drop=True)
p1_path=os.path.join(OUT_DIR,'pool1_I11_screening.csv'); p1.to_csv(p1_path, index=False)
md5=hashlib.md5(open(p1_path,'rb').read()).hexdigest()
print('  [pool1] rows=%d dates=%s..%s avg_names/day=%.1f md5=%s %s'%(len(p1),p1.tradeDate.min(),p1.tradeDate.max(),len(p1)/p1.tradeDate.nunique(),md5,
      'OK(==0708)' if md5==POOL1_MD5 else 'MISMATCH!!'), flush=True)

# ---------------- 6 x 池2 ----------------
STATS=[]
for cfg in DELIV:
    dfp=pd.concat(pool2_parts[cfg], ignore_index=True).sort_values(['tradeDate','ticker']).reset_index(drop=True)
    fn='pool2_%s.csv'%FNAME[cfg]; dfp.to_csv(os.path.join(OUT_DIR,fn), index=False, float_format='%.8g')
    nd=dfp.tradeDate.nunique()
    STATS.append(dict(cfg=cfg, file=fn, rows=len(dfp), days=nd, avg_names=round(len(dfp)/nd,1),
                      avg_wsum=round(dfp.weight.sum()/nd,4), wmax=float(dfp.weight.max()), dmin=dfp.tradeDate.min(), dmax=dfp.tradeDate.max()))
    print('  [pool2] %-24s rows=%8d days=%4d avg_names/day=%6.1f avg_pos=%.3f wmax=%.6f'%(fn,len(dfp),nd,len(dfp)/nd,dfp.weight.sum()/nd,dfp.weight.max()), flush=True)
pd.DataFrame(STATS).to_csv(os.path.join(OUT_DIR,'_delivery_stats.csv'), index=False)

# ---------------- old(v1) vs new(v2) 对照 (v1 数字读 E2 decomp.csv) ----------------
e2=pd.read_csv(E2_DECOMP).set_index(['cfg','period'])
V1={'M_mean3':'Mmean_v1','A4b':'A4b','M_union3':'Munion_v1','M_mean3_CMFv5':'Mmean_v1+cmfveto','A4b_CMFv5':'A4b+cmfveto','M_union3_CMFv5':'Munion_v1+cmfveto'}
L=df.set_index(['cfg','period'])
def r4(ix,col,src): return '/'.join('%+5.2f'%float(src.loc[(ix,s),col]) for s in SEGS)
lines=[]
lines.append('OLD vs NEW  DEV net ann %% (NW)  4 段 = %s'%' / '.join(SEGS))
lines.append('-- v1 形态 (7/8 交付): 7 月报的旧口径 (L0R) -> 同形态新口径 (L1A)')
for k,lab in V1.items():
    lines.append('  %-18s L0R %s | L1A %s (NW %s)'%(lab, r4(k,'L0R',e2), r4(k,'L1A',e2), r4(k,'nw_new',e2)))
lines.append('-- v2 形态 (本次): 新口径 主基准 net1 (NW1) | 副基准 net2 (NW2) | turn | nh')
for cfg in DELIV:
    lines.append('  %-18s net1 %s (NW %s) | net2 %s (NW %s) | turn %s | nh %s'%(cfg, r4(cfg,'net_ann',L), r4(cfg,'net_nw',L), r4(cfg,'net2_ann',L), r4(cfg,'net2_nw',L),
                 '/'.join('%4.1f'%float(L.loc[(cfg,s),'turn']) for s in SEGS), '/'.join('%5.1f'%float(L.loc[(cfg,s),'avg_nh']) for s in SEGS)))
cmp_txt='\n'.join(lines); print('\n'+cmp_txt, flush=True)
open(os.path.join(OUT_DIR,'old_vs_new.txt'),'w',encoding='utf-8').write(cmp_txt+'\n')

# ---------------- README ----------------
tbl='\n'.join('| %s | %s | %s | %s | %s | %s | %s |'%(cfg, r4(cfg,'net_ann',L), r4(cfg,'net_nw',L), r4(cfg,'net2_ann',L), r4(cfg,'net2_nw',L),
              '/'.join('%.1f'%float(L.loc[(cfg,s),'turn']) for s in SEGS), '/'.join('%.0f'%float(L.loc[(cfg,s),'avg_nh']) for s in SEGS)) for cfg in DELIV)
readme='''# I11 候选池 v2（2026-09 引擎修正后）

交付人：陈荔辰。本目录取代 2026-07-08 的 `I11_candidate_pools/`（v1）。**池1 与 v1 逐字节相同；6 个池2 全部更新。**

## 文件
- `pool1_I11_screening.csv` — I11 初筛母池（ticker / tradeDate / in_pool=1），与 v1 相同（md5 %s）
- `pool2_<形态>.csv` — 6 个候选精选池（ticker / tradeDate / weight）；weight = 偏离约束目标权重（个股 ≤1%%、行业相对基准偏离 ≤3%%、不归一），每日权重和 = 当日仓位
- ticker = 去后缀去前导零的整数（600000.SH → 600000，000001.SZ → 1），可直接 join `clc_ts_all_*`；tradeDate = YYYY-MM-DD；全历史 %s ～ %s

## 六个形态
| 形态 | 文件 | 说明 |
|---|---|---|
| A4b | `pool2_A4b_pure.csv` | conditional_turnover 剔高半 → 组内 turnover_volatility_60d 再剔高半（顺序双筛），与 v1 相同 |
| Mmean_v2 | `pool2_Mmean_v2_pure.csv` | conditional_turnover / turnover_volatility_60d / cum_return_20d 三因子池内百分位取均值，剔最差半 |
| Munion_v2 | `pool2_Munion_v2_pure.csv` | 三因子各自剔最差半，取并集之外（最集中） |
| *_cvrveto | `pool2_*_cvrveto.csv` | 上述三形态再剔除 CVR_20d（20 日收盘价/VWAP−1 均值）池内最高的 1/5 |

## 相对 v1 的三处变化
1. **回测引擎修正**（2026-09-02）：① 记账时点改为"T 收盘出信号、T+1 VWAP 成交"（原实现从 T 日 VWAP 起记，有半天前视）；② 收益改用后复权价（原实现除权除息日记成假跌）。v1 六形态在修正口径下的数字见 `old_vs_new.txt`。
2. **反转代表**：reversal_skip1（跳过当日的 10 日反转）换为 cum_return_20d（20 日反转）。修正口径下不跳过当日的反转更强、跨段更一致。
3. **规则池**：cmf_change 否决层撤销（其抬升在修正口径下消失，且方向本身存疑）；换为 CVR_20d 否决（日内强势后反转），四段与三种底座上均为正贡献。

## 回测口径与数字（DEV net，年化 %%，Newey-West t，段序 2010-14 / 15-18 / 19-23 / 24-26）
持有 5 日、双边成本 6bp、T+1 VWAP 成交、后复权。主基准 = 干净全市场等权（剔北交所 / ST / 次新近似）；副基准 = I11 池自身等机制（读"池内选股能力"，I11 池本身早段跑输市场约 2～5 个点）。

| 形态 | 主基准 net | 主基准 NW t | 副基准 net | 副基准 NW t | 年换手(x) | 日均持仓 |
|---|---|---|---|---|---|---|
%s

## 注意
- 近段（2024-26）NW t 多在 1.3～2.0，边际显著；成本按 6bp，实盘预计 10～15bp；T+1 一字板 / 停牌的可成交性尚未在回测里剔除。
- 反转代表与否决因子的更换是在同一样本内选定的，2026-04 之后的样本延长验证列为下一步。
- 复现：`export_delivery_pools_v2.py`（自检对 E4 锚点 12/12，池1 md5 对 v1）。
'''%(md5, p1.tradeDate.min(), p1.tradeDate.max(), tbl)
open(os.path.join(OUT_DIR,'README.md'),'w',encoding='utf-8').write(readme)
print('\n[ALLDONE] delivery v2 files in %s  (pool1 md5 %s)'%(OUT_DIR, 'OK' if md5==POOL1_MD5 else 'MISMATCH'), flush=True)
