#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# E4 AGGREGATION RE-REVIEW (2026-09) -- 新口径 (exec_lag=1, adjust=True) 下的聚合层复审.
# 配置 = 3 生产候选 (硬锚点=E2 L1A) + M_mean2(≡A5, 软锚点=phase3 A5 旧口径) + 反转代表替换 2 变体
#      + CVR_20d 新轴 (合成 M_mean4 / veto k5 x3) + cmf 正向 veto (剔 cmf_change 激增 quintile) x3.
# 双基准: 主 = 干净全市场等权 (E2 同); 副 = pool0 DEV 同机制 (池内选股能力).
# 相关矩阵 = 8 因子池内 pct 日截面 Pearson(=Spearman) 均值, 每段一张.
# READ-ONLY / import-only. 窗口 = PERIODS 不变. 只出表, 不判定.
import sys, os, time
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import define_i11_signal, build_observation_pool, apply_hard_constraints
import comprehensive_factor_diagnosis as C

OUT_DIR = C.make_output_dir('E4_agg_review')
C.setup_dual_logging(OUT_DIR)
print('[out]', OUT_DIR, flush=True)

F_COND, F_TVOL, F_REV, F_CMF = 'conditional_turnover', 'turnover_volatility_60d', 'reversal_skip1', 'cmf_change_neg'
F_CVR, F_CR5, F_CR20, F_CI5 = 'CVR_20d', 'cum_return_5d', 'cum_return_20d', 'cum_intraday_ret_5d'
TOL = 0.02
HARD = {  # E2 decomp.csv L1A (results/20260903_0935_E2_decomposition)
 ('2010-2014','M_mean3'):3.3127, ('2015-2018','M_mean3'):6.0531, ('2019-2023','M_mean3'):5.4185, ('2024-2026','M_mean3'):5.2565,
 ('2010-2014','A4b'):2.5046, ('2015-2018','A4b'):5.0447, ('2019-2023','A4b'):7.5665, ('2024-2026','A4b'):8.9262,
 ('2010-2014','M_union3'):2.4084, ('2015-2018','M_union3'):4.5991, ('2019-2023','M_union3'):5.9298, ('2024-2026','M_union3'):5.9499,
}
SOFT_L0R = {('2010-2014','M_mean2'):6.4231, ('2015-2018','M_mean2'):6.5845, ('2019-2023','M_mean2'):6.5189, ('2024-2026','M_mean2'):6.9157}
CFGS = ['A4b','M_mean3','M_union3','M_mean2','M_mean3_cr5','M_mean3_cr20','M_mean4_cvr',
        'A4b_CVRv5','M_mean3_CVRv5','M_union3_CVRv5','A4b_CMFsurge5','M_mean3_CMFsurge5','M_union3_CMFsurge5']
CORR_F = ['cond','tvol','rev_neg','cr5','cr20','cvr','ci5','cmf_neg']
SEGS = list(PERIODS.keys())

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

def st(series):
    return nw_stats(np.asarray(series, float))

records=[]; checks=[]; hard_pass=True
for pname,(ps,pe) in PERIODS.items():
    print('\n'+'#'*70); print('PERIOD %s (%s..%s)'%(pname,ps,pe), flush=True); t0=time.time()
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
    neu_cond=neu(F_COND); neu_tvol=neu(F_TVOL); neu_rev0=neu(F_REV); neu_rev={d:-s for d,s in neu_rev0.items()}
    neu_cmf=neu(F_CMF); neu_cvr=neu(F_CVR); neu_cr5=neu(F_CR5); neu_cr20=neu(F_CR20); neu_ci5=neu(F_CI5)
    pcond,ptvol,prev,pcvr,pcr5,pcr20,pci5,pcmf=[pct_cache(x) for x in (neu_cond,neu_tvol,neu_rev,neu_cvr,neu_cr5,neu_cr20,neu_ci5,neu_cmf)]
    p0=(pool0.values==1)
    print('  neutralized 9 factors %.0fs'%(time.time()-t0), flush=True)

    # ---- production masks (verbatim E2) ----
    m_mean3=(C.build_factor_strategy_holdings_cached(combine([pcond,ptvol,prev],'mean'), pool0,2,[2]).values==1)
    hc=C.build_factor_strategy_holdings_cached(neu_cond, pool0,2,[2])
    m_a4b=(C.build_factor_strategy_holdings_cached(
            C.precompute_neutralized_factor(fac_tvol, hc, log_mcap), hc,2,[2]).values==1)
    dc,dt,dr=drop_mask(neu_cond,pool0),drop_mask(neu_tvol,pool0),drop_mask(neu_rev,pool0)
    m_union3=(p0 & ((dc.astype(int)+dt.astype(int)+dr.astype(int))==0))
    # ---- E4 new masks ----
    m_mean2=(C.build_factor_strategy_holdings_cached(combine([pcond,ptvol],'mean'), pool0,2,[2]).values==1)
    m_mean3_cr5=(C.build_factor_strategy_holdings_cached(combine([pcond,ptvol,pcr5],'mean'), pool0,2,[2]).values==1)
    m_mean3_cr20=(C.build_factor_strategy_holdings_cached(combine([pcond,ptvol,pcr20],'mean'), pool0,2,[2]).values==1)
    m_mean4_cvr=(C.build_factor_strategy_holdings_cached(combine([pcond,ptvol,prev,pcvr],'mean'), pool0,2,[2]).values==1)
    tox_cvr=drop_mask(neu_cvr, pool0, 5)                                        # 剔 CVR_20d 最高 quintile (high=worst)
    kept_surge=C.build_factor_strategy_holdings_cached(neu_cmf, pool0, 5, [1])  # 剔 cmf_change_neg 最低组 = cmf_change 激增 quintile
    tox_surge=p0 & ~(kept_surge.values==1)
    masks={'A4b':m_a4b,'M_mean3':m_mean3,'M_union3':m_union3,'M_mean2':m_mean2,
           'M_mean3_cr5':m_mean3_cr5,'M_mean3_cr20':m_mean3_cr20,'M_mean4_cvr':m_mean4_cvr,
           'A4b_CVRv5':m_a4b&~tox_cvr,'M_mean3_CVRv5':m_mean3&~tox_cvr,'M_union3_CVRv5':m_union3&~tox_cvr,
           'A4b_CMFsurge5':m_a4b&~tox_surge,'M_mean3_CMFsurge5':m_mean3&~tox_surge,'M_union3_CMFsurge5':m_union3&~tox_surge}

    # ---- secondary benchmark: pool0 DEV same-mechanism ----
    w_pool=assign_weights_dev(pd.DataFrame(p0.astype(float),index=pool0.index,columns=pool0.columns), industry, shares)
    pr_pool=C.compute_calendar_pnl(w_pool, data, clean, hold_days=5, cost_bp_bilateral=6.0)
    bm2=pr_pool['port_daily']/pr_pool['daily_position'].replace(0,np.nan)
    pa,_,pnw,_=st(pr_pool['net_excess_daily'])
    print('  pool0_DEV vs market: net %+.2f NW %+.2f'%(pa,pnw), flush=True)

    for cfg in CFGS:
        hold=pd.DataFrame(masks[cfg].astype(float), index=pool0.index, columns=pool0.columns)
        w=assign_weights_dev(hold, industry, shares); nh=(hold>0).sum(axis=1); pos=w.sum(axis=1)
        combos=[(1,True)]+([(0,False)] if cfg=='M_mean2' else [])
        for lag,adj in combos:
            pr=C.compute_calendar_pnl(w, data, clean, hold_days=5, cost_bp_bilateral=6.0, exec_lag=lag, adjust=adj)
            nann,nnv,nnw,n=st(pr['net_excess_daily']); gann,_,_,_=st(pr['gross_excess_daily'])
            mm=C.calendar_pnl_metrics(pr['net_excess_daily']); mdd=mm['mdd'] if mm else np.nan
            if (lag,adj)==(1,True):
                ex2=pr['port_daily']-bm2*pr['daily_position']; net2=ex2-pr['daily_turnover']*6.0/1e4
                n2ann,_,n2nw,_=st(net2)
            else:
                n2ann=n2nw=np.nan
            records.append(dict(period=pname,cfg=cfg,combo=('L1A' if adj else 'L0R'),net_ann=nann,net_nw=nnw,gross_ann=gann,
                                mdd_net=mdd,net2_ann=n2ann,net2_nw=n2nw,avg_nh=float(nh[nh>0].mean()),avg_pos=float(pos[pos>0].mean()),
                                turn=float(pr['turnover_annual']),n=n))
            key=(pname,cfg)
            if (lag,adj)==(1,True) and key in HARD:
                d=abs(nann-HARD[key]); ok=bool(d<TOL); hard_pass&=ok
                checks.append(dict(period=pname,cfg=cfg,level='HARD',got=round(nann,4),anchor=HARD[key],dabs=round(d,4),ok=ok))
                print('    [CHECK HARD] %-10s L1A got %+8.4f anchor(E2) %+8.4f |d|%.4f %s'%(cfg,nann,HARD[key],d,'OK' if ok else 'FAIL!!'), flush=True)
            if (lag,adj)==(0,False) and key in SOFT_L0R:
                d=abs(nann-SOFT_L0R[key]); ok=bool(d<TOL)
                checks.append(dict(period=pname,cfg=cfg,level='SOFT',got=round(nann,4),anchor=SOFT_L0R[key],dabs=round(d,4),ok=ok))
                print('    [CHECK SOFT] %-10s L0R got %+8.4f anchor(phase3 A5) %+8.4f |d|%.4f %s'%(cfg,nann,SOFT_L0R[key],d,'OK' if ok else 'WARN'), flush=True)
        print('  [cfg done] %-18s nh=%.1f pos=%.3f'%(cfg,float(nh[nh>0].mean()),float(pos[pos>0].mean())), flush=True)

    # ---- correlation matrix ----
    caches=dict(zip(CORR_F,[pcond,ptvol,prev,pcr5,pcr20,pcvr,pci5,pcmf]))
    keys=set(caches['cond'])
    for c in caches.values(): keys&=set(c)
    acc=None; nd=0
    for d in sorted(keys):
        df=pd.concat([caches[f][d].rename(f) for f in CORR_F], axis=1).dropna()
        if len(df)<30: continue
        cm=df.corr().values; acc=cm if acc is None else acc+cm; nd+=1
    cm=pd.DataFrame(acc/nd, index=CORR_F, columns=CORR_F); cm.to_csv(os.path.join(OUT_DIR,'corr_%s.csv'%pname))
    print('\n  CORR %s (pct 日截面 Pearson=Spearman 均值, n_days=%d)'%(pname,nd)); print(cm.round(2).to_string(), flush=True)
    del data,feats
    print('[period done] %s %.0fs'%(pname,time.time()-t0), flush=True)

# ---------------- write + gate ----------------
df=pd.DataFrame(records); df.to_csv(os.path.join(OUT_DIR,'summary.csv'), index=False)
chk=pd.DataFrame(checks); chk.to_csv(os.path.join(OUT_DIR,'check.csv'), index=False)
print('\n'+'='*66); print(chk.to_string(index=False))
if not hard_pass:
    print('\n[ABORT] HARD SELF-CHECK FAILED -- summary.csv/check.csv written, no final tables.', flush=True); sys.exit(1)
print('\n[SELF-CHECK] HARD 12/12 PASS', flush=True)

# ---------------- final tables ----------------
L=df[df.combo=='L1A'].set_index(['cfg','period'])
def row(cfg,col): return [float(L.loc[(cfg,s),col]) for s in SEGS]
def fmt(v,w='%+6.2f'): return '/'.join(w%x for x in v)
print('\n'+'='*66); print('MAIN  新口径 L1A  主基准=全市场等权 | 副基准=pool0 DEV 同机制   4 段 = %s'%' / '.join(SEGS))
for cfg in CFGS:
    print('  %-18s net1 %s NW1 %s | net2 %s NW2 %s | turn %s nh %s'%(
        cfg, fmt(row(cfg,'net_ann')), fmt(row(cfg,'net_nw'),'%+5.2f'), fmt(row(cfg,'net2_ann')), fmt(row(cfg,'net2_nw'),'%+5.2f'),
        fmt(row(cfg,'turn'),'%4.1f'), fmt(row(cfg,'avg_nh'),'%5.1f')))
def marg(a,b,label):
    d1=[x-y for x,y in zip(row(a,'net_ann'),row(b,'net_ann'))]; dn=[x-y for x,y in zip(row(a,'net_nw'),row(b,'net_nw'))]
    d2=[x-y for x,y in zip(row(a,'net2_ann'),row(b,'net2_ann'))]
    print('  %-34s Δnet1 %s ΔNW1 %s | Δnet2 %s'%(label, fmt(d1), fmt(dn,'%+5.2f'), fmt(d2)))
print('\n'+'='*66); print('MARGINALS (a − b)')
marg('M_mean3','M_mean2','rev 席位: M_mean3 − M_mean2')
marg('M_mean3_cr5','M_mean3','反转代表: cr5 − reversal_skip1')
marg('M_mean3_cr20','M_mean3','反转代表: cr20 − reversal_skip1')
marg('M_mean4_cvr','M_mean3','CVR 合成: M_mean4_cvr − M_mean3')
for b in ('A4b','M_mean3','M_union3'):
    marg(b+'_CVRv5', b, 'CVR veto: %s'%b)
for b in ('A4b','M_mean3','M_union3'):
    marg(b+'_CMFsurge5', b, 'cmf 激增 veto: %s'%b)
print('\n[ALLDONE]', OUT_DIR, flush=True)
