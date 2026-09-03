#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# E2 DECOMPOSITION (2026-09) -- 引擎修正 (E1, commit cb9fea2) 后的生产损害表.
# 权重算一次 (与 delivery/I11_candidate_pools_20260708/export_delivery_pools.py 逐 config 同构),
# 引擎调 4 次 {exec_lag 0/1} x {adjust False/True}, 把每个 cfg 每段的 DEV net 变化拆成 时点项 / 复权项 / 交互项.
# 硬自检: (exec_lag=0, adjust=False) 必须复现 phase3 summary.csv 的 24 个锚点 (tol 0.02), 否则 [ABORT] 不出最终表.
# 软自检: phase1 summary.csv 的 cond / rev_solo 8 个锚点, FAIL 只 WARN.
# READ-ONLY / import-only. 窗口 = PERIODS 不变. 不写交付文件.
import sys, os
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import define_i11_signal, build_observation_pool, apply_hard_constraints
import comprehensive_factor_diagnosis as C

OUT_DIR = C.make_output_dir('E2_decomposition')
C.setup_dual_logging(OUT_DIR)
print('[out]', OUT_DIR, flush=True)

F_COND, F_TVOL, F_REV, F_CMF = 'conditional_turnover', 'turnover_volatility_60d', 'reversal_skip1', 'cmf_change_neg'
COMBOS = [(0, False), (1, False), (0, True), (1, True)]     # (exec_lag, adjust)
def tag(lag, adj): return 'L%d%s' % (lag, 'A' if adj else 'R')  # L0R 旧口径 / L1R 只改时点 / L0A 只改复权 / L1A 新口径
TOL = 0.02
CFGS = ['M_mean3', 'A4b', 'M_union3', 'M_mean3_CMFv5', 'A4b_CMFv5', 'M_union3_CMFv5',
        'cond_solo', 'tvol_solo', 'rev_solo', 'pool0_DEV', 'detS_pool']
HARD = {  # phase3 summary.csv (== 交付脚本 ANCHORS), DEV net_ann %
 ('2010-2014','M_mean3'):7.985758, ('2010-2014','A4b'):3.969673, ('2010-2014','M_union3'):4.419393,
 ('2010-2014','M_mean3_CMFv5'):7.540463, ('2010-2014','A4b_CMFv5'):3.816861, ('2010-2014','M_union3_CMFv5'):3.781008,
 ('2015-2018','M_mean3'):8.976133, ('2015-2018','A4b'):6.979786, ('2015-2018','M_union3'):6.604926,
 ('2015-2018','M_mean3_CMFv5'):11.634438, ('2015-2018','A4b_CMFv5'):7.153561, ('2015-2018','M_union3_CMFv5'):6.565501,
 ('2019-2023','M_mean3'):6.982466, ('2019-2023','A4b'):8.567354, ('2019-2023','M_union3'):7.703888,
 ('2019-2023','M_mean3_CMFv5'):10.259273, ('2019-2023','A4b_CMFv5'):9.913383, ('2019-2023','M_union3_CMFv5'):8.210896,
 ('2024-2026','M_mean3'):7.012710, ('2024-2026','A4b'):10.673320, ('2024-2026','M_union3'):7.135630,
 ('2024-2026','M_mean3_CMFv5'):9.905665, ('2024-2026','A4b_CMFv5'):13.227420, ('2024-2026','M_union3_CMFv5'):8.151385,
}
SOFT = {  # phase1 summary.csv (results/20260618_1831_agg_matrix_phase1): cfg 'cond' / 'rev_solo'
 ('2010-2014','cond_solo'):4.951607, ('2015-2018','cond_solo'):2.224300, ('2019-2023','cond_solo'):3.674860, ('2024-2026','cond_solo'):7.677520,
 ('2010-2014','rev_solo'):5.506075, ('2015-2018','rev_solo'):8.643241, ('2019-2023','rev_solo'):2.799376, ('2024-2026','rev_solo'):2.186813,
}

# ---------- verbatim helpers (export_delivery_pools.py) ----------
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
# -----------------------------------------------------------------

records=[]; check_rows=[]; hard_pass=True

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

    fac_cond=specs[F_COND]['func'](data,feats,industry)
    fac_tvol=specs[F_TVOL]['func'](data,feats,industry)
    fac_rev =specs[F_REV ]['func'](data,feats,industry)
    fac_cmf =specs[F_CMF ]['func'](data,feats,industry)
    neu_cond=C.precompute_neutralized_factor(fac_cond, pool0, log_mcap)
    neu_tvol=C.precompute_neutralized_factor(fac_tvol, pool0, log_mcap)
    neu_rev0=C.precompute_neutralized_factor(fac_rev , pool0, log_mcap)
    neu_rev ={d:-s for d,s in neu_rev0.items()}          # negate: high(neg)=low(reversal)=worst=drop
    neu_cmf =C.precompute_neutralized_factor(fac_cmf , pool0, log_mcap)
    pcond,ptvol,prev=pct_cache(neu_cond),pct_cache(neu_tvol),pct_cache(neu_rev)
    tri=[pcond,ptvol,prev]

    # ---- base masks (== phase1 M_mean / A4b_2f / M_union; verbatim) ----
    m_mean=(C.build_factor_strategy_holdings_cached(combine(tri,'mean'), pool0,2,[2]).values==1)
    hc=C.build_factor_strategy_holdings_cached(neu_cond, pool0,2,[2])
    m_a4b=(C.build_factor_strategy_holdings_cached(
            C.precompute_neutralized_factor(fac_tvol, hc, log_mcap), hc,2,[2]).values==1)
    dc,dt,dr=drop_mask(neu_cond,pool0),drop_mask(neu_tvol,pool0),drop_mask(neu_rev,pool0)
    flags=dc.astype(int)+dt.astype(int)+dr.astype(int); p0=(pool0.values==1)
    m_union=(p0 & (flags==0))
    tox5=drop_mask(neu_cmf, pool0, 5)
    # ---- E2 extra masks ----
    m_cond=(hc.values==1)                                                        # == phase1 'cond'
    m_tvol=(C.build_factor_strategy_holdings_cached(neu_tvol, pool0,2,[2]).values==1)
    m_rev =(C.build_factor_strategy_holdings_cached(neu_rev , pool0,2,[2]).values==1)   # == phase1 'rev_solo'
    S=(close/data['vwap']-1).where(pool0==1)                                     # 只含 T 日盘中信息的探测器
    m_detS=((S.rank(axis=1,pct=True)>0.5).values & p0)
    masks={'M_mean3':m_mean,'A4b':m_a4b,'M_union3':m_union,
           'M_mean3_CMFv5':(m_mean&~tox5),'A4b_CMFv5':(m_a4b&~tox5),'M_union3_CMFv5':(m_union&~tox5),
           'cond_solo':m_cond,'tvol_solo':m_tvol,'rev_solo':m_rev,'pool0_DEV':p0,'detS_pool':m_detS}

    for cfg in CFGS:
        hold=pd.DataFrame(masks[cfg].astype(float), index=pool0.index, columns=pool0.columns)
        w=assign_weights_dev(hold, industry, shares)
        nh=(hold>0).sum(axis=1); pos=w.sum(axis=1)
        for lag,adj in COMBOS:
            pr=C.compute_calendar_pnl(w, data, clean, hold_days=5, cost_bp_bilateral=6.0, exec_lag=lag, adjust=adj)
            nann,nnv,nnw,n=nw_stats(pr['net_excess_daily'].values)
            gann,_,_,_=nw_stats(pr['gross_excess_daily'].values)
            mm=C.calendar_pnl_metrics(pr['net_excess_daily']); mdd=mm['mdd'] if mm else np.nan
            records.append(dict(period=pname,cfg=cfg,combo=tag(lag,adj),exec_lag=lag,adjust=adj,
                                net_ann=nann,net_naive=nnv,net_nw=nnw,gross_ann=gann,mdd_net=mdd,
                                avg_nh=float(nh[nh>0].mean()),avg_pos=float(pos[pos>0].mean()),
                                turn=float(pr['turnover_annual']),n=n))
            if (lag,adj)==(0,False):
                key=(pname,cfg)
                if key in HARD or key in SOFT:
                    anc=HARD.get(key, SOFT.get(key)); level='HARD' if key in HARD else 'SOFT'
                    d=abs(nann-anc); ok=bool(d<TOL)
                    if level=='HARD': hard_pass&=ok
                    check_rows.append(dict(period=pname,cfg=cfg,level=level,got=round(nann,4),anchor=anc,dabs=round(d,4),ok=ok))
                    print('    [CHECK %s] %-16s got %+8.4f  anchor %+8.4f  |d|%.4f  %s'
                          %(level,cfg,nann,anc,d,'OK' if ok else ('FAIL!!' if level=='HARD' else 'WARN')), flush=True)
        print('  [cfg done] %-16s nh=%.1f pos=%.3f'%(cfg, float(nh[nh>0].mean()), float(pos[pos>0].mean())), flush=True)
    del data,feats,neu_cond,neu_tvol,neu_rev0,neu_rev,neu_cmf,masks
    print('[period done] %s'%pname, flush=True)

# ---------------- write + gate ----------------
df=pd.DataFrame(records); df.to_csv(os.path.join(OUT_DIR,'summary.csv'), index=False)
chk=pd.DataFrame(check_rows); chk.to_csv(os.path.join(OUT_DIR,'check.csv'), index=False)
print('\n'+'='*66); print(chk.to_string(index=False))
if not hard_pass:
    print('\n[ABORT] HARD SELF-CHECK FAILED -- summary.csv/check.csv written, no final tables.', flush=True); sys.exit(1)
print('\n[SELF-CHECK] HARD 24/24 PASS%s'%('' if chk[chk.level=="SOFT"].ok.all() else '  (SOFT has WARN, see above)'), flush=True)

# ---------------- final tables ----------------
segs=list(PERIODS.keys())
piv=df.pivot_table(index=['cfg','period'], columns='combo', values='net_ann')
piv['d_timing']=piv['L1R']-piv['L0R']; piv['d_adjust']=piv['L0A']-piv['L0R']
piv['d_both']=piv['L1A']-piv['L0R']; piv['d_interact']=piv['d_both']-piv['d_timing']-piv['d_adjust']
nw=df.pivot_table(index=['cfg','period'], columns='combo', values='net_nw')[['L0R','L1A']].rename(columns={'L0R':'nw_old','L1A':'nw_new'})
ex=df[df.combo=='L1A'].set_index(['cfg','period'])[['gross_ann','mdd_net','turn','avg_nh','avg_pos']].rename(
    columns={'gross_ann':'gross_new','mdd_net':'mdd_new','turn':'turn_new','avg_nh':'nh_new','avg_pos':'pos_new'})
dec=piv.join(nw).join(ex).reset_index()
dec['cfg']=pd.Categorical(dec.cfg, CFGS, ordered=True); dec['period']=pd.Categorical(dec.period, segs, ordered=True)
dec=dec.sort_values(['cfg','period']); dec.to_csv(os.path.join(OUT_DIR,'decomp.csv'), index=False)

print('\n'+'='*66); print('DECOMPOSITION  DEV net ann %  (L0R 旧口径 / L1R 只改时点 / L0A 只改复权 / L1A 新口径)  [6bp, 4 段]')
cols=['cfg','period','L0R','L1R','L0A','L1A','d_timing','d_adjust','d_interact','nw_old','nw_new','gross_new','mdd_new','turn_new','nh_new','pos_new']
print(dec[cols].to_string(index=False, float_format=lambda v:'%+7.2f'%v))

print('\n'+'='*66); print('VETO MARGINAL  (cfg_CMFv5 - cfg)  net ann %:  old (L0R)  ->  new (L1A)')
for base in ['M_mean3','A4b','M_union3']:
    for combo in ['L0R','L1A']:
        vals=[float(piv.loc[(base+'_CMFv5',s),combo]-piv.loc[(base,s),combo]) for s in segs]
        print('  %-9s %s  %s'%(base, combo, '  '.join('%+6.2f'%v for v in vals)))

print('\n'+'='*66); print('CANDIDATES  net ann % | NW   old (L0R) -> new (L1A), 4 段')
for cfg in CFGS:
    o=[float(piv.loc[(cfg,s),'L0R']) for s in segs]; nn=[float(piv.loc[(cfg,s),'L1A']) for s in segs]
    no=[float(nw.loc[(cfg,s),'nw_old']) for s in segs]; nnw=[float(nw.loc[(cfg,s),'nw_new']) for s in segs]
    print('  %-15s old %s | NW %s'%(cfg, '/'.join('%.2f'%v for v in o), '/'.join('%.2f'%v for v in no)))
    print('  %-15s new %s | NW %s'%('', '/'.join('%.2f'%v for v in nn), '/'.join('%.2f'%v for v in nnw)))
print('\n[ALLDONE]', OUT_DIR, flush=True)
