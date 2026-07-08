#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DELIVERY POOL EXPORTER (2026-07-08) -- 陈荔辰 / abnormal_comovement_strategy
# Export 池1 (I11 initial-screening universe) + 6 池2 candidate holdings
#   {M_mean3 / A4b / M_union3} x {pure, +cmf_change veto k=5}
# as long-format CSV (ticker, tradeDate, weight), full history 2010-2026, for the PM to self-test.
#
# Reconstructs phase3 (results/20260707_1952_agg_matrix_phase3_cmfveto) CONFIG-FOR-CONFIG using the
# SAME foundation funcs, and SELF-CHECKS every config's DEV net_ann against the phase3 summary.csv
# anchors. If ANY of the 24 checks deviates > 0.05, ABORT -- write NO delivery file.
#
# READ-ONLY / import-only: imports foundation funcs, modifies NOTHING. 4 base files untouched.
# Caliber inherited unchanged: I11 pool mcap=0; clean EW bench (剔北交所/ST/次新近似);
#   DEV deviation-constraint weights (stock<=1%, industry |w-w_bm|<=3%, NO renorm); net 6bp;
#   drop-tail worst-half; reversal NEGATED (high=worst uniform); cmf via cmf_change_neg toxic tail; hold 5d.
import sys, os
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import define_i11_signal, build_observation_pool, apply_hard_constraints
import comprehensive_factor_diagnosis as C

OUT_DIR = C.make_output_dir('delivery_pools')
C.setup_dual_logging(OUT_DIR)
print('[out]', OUT_DIR, flush=True)

F_COND, F_TVOL, F_REV, F_CMF = 'conditional_turnover', 'turnover_volatility_60d', 'reversal_skip1', 'cmf_change_neg'

# ---- phase3 summary.csv anchors: (period, cfg) -> DEV net_ann % ----
ANCHORS = {
 ('2010-2014','M_mean3'):7.985758, ('2010-2014','A4b'):3.969673, ('2010-2014','M_union3'):4.419393,
 ('2010-2014','M_mean3_CMFv5'):7.540463, ('2010-2014','A4b_CMFv5'):3.816861, ('2010-2014','M_union3_CMFv5'):3.781008,
 ('2015-2018','M_mean3'):8.976133, ('2015-2018','A4b'):6.979786, ('2015-2018','M_union3'):6.604926,
 ('2015-2018','M_mean3_CMFv5'):11.634438, ('2015-2018','A4b_CMFv5'):7.153561, ('2015-2018','M_union3_CMFv5'):6.565501,
 ('2019-2023','M_mean3'):6.982466, ('2019-2023','A4b'):8.567354, ('2019-2023','M_union3'):7.703888,
 ('2019-2023','M_mean3_CMFv5'):10.259273, ('2019-2023','A4b_CMFv5'):9.913383, ('2019-2023','M_union3_CMFv5'):8.210896,
 ('2024-2026','M_mean3'):7.012710, ('2024-2026','A4b'):10.673320, ('2024-2026','M_union3'):7.135630,
 ('2024-2026','M_mean3_CMFv5'):9.905665, ('2024-2026','A4b_CMFv5'):13.227420, ('2024-2026','M_union3_CMFv5'):8.151385,
}
DELIV = ['M_mean3','A4b','M_union3','M_mean3_CMFv5','A4b_CMFv5','M_union3_CMFv5']
FNAME = {'M_mean3':'Mmean_pure','A4b':'A4b_pure','M_union3':'Munion_pure',
         'M_mean3_CMFv5':'Mmean_cmfveto','A4b_CMFv5':'A4b_cmfveto','M_union3_CMFv5':'Munion_cmfveto'}
TOL = 0.05

# ---------- verbatim helpers (agg_matrix_phase1.py / residual_cmf_park.py) ----------
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
# ------------------------------------------------------------------------------------

pool1_parts=[]; pool2_parts={cfg:[] for cfg in DELIV}
check_rows=[]; all_pass=True

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

    # ---- base masks (== phase1 M_mean / A4b_2f / M_union) ----
    m_mean=(C.build_factor_strategy_holdings_cached(combine(tri,'mean'), pool0,2,[2]).values==1)
    hc=C.build_factor_strategy_holdings_cached(neu_cond, pool0,2,[2])
    m_a4b=(C.build_factor_strategy_holdings_cached(
            C.precompute_neutralized_factor(fac_tvol, hc, log_mcap), hc,2,[2]).values==1)
    dc,dt,dr=drop_mask(neu_cond,pool0),drop_mask(neu_tvol,pool0),drop_mask(neu_rev,pool0)
    flags=dc.astype(int)+dt.astype(int)+dr.astype(int); p0=(pool0.values==1)
    m_union=(p0 & (flags==0))
    # ---- cmf veto (narrow k=5, == residual toxic_mask) ----
    tox5=drop_mask(neu_cmf, pool0, 5)
    masks={'M_mean3':m_mean,'A4b':m_a4b,'M_union3':m_union,
           'M_mean3_CMFv5':(m_mean&~tox5),'A4b_CMFv5':(m_a4b&~tox5),'M_union3_CMFv5':(m_union&~tox5)}

    # id arrays for long-format extraction (ticker: de-suffix + de-zero-pad == factor-lib convention)
    col_ids=np.array([int(str(c).split('.')[0]) for c in pool0.columns], dtype=np.int64)
    date_ids=np.array([pd.Timestamp(str(d)).strftime('%Y-%m-%d') for d in pool0.index])

    # 池1 (I11 screening universe, shared by all candidates)
    rr,cc=np.nonzero(p0)
    pool1_parts.append(pd.DataFrame({'ticker':col_ids[cc],'tradeDate':date_ids[rr],'in_pool':np.int8(1)}))

    # per-config self-check + 池2 weight extraction
    print('  --- SELF-CHECK %s (vs phase3 summary.csv) ---'%pname, flush=True)
    for cfg in DELIV:
        hold=pd.DataFrame(masks[cfg].astype(float), index=pool0.index, columns=pool0.columns)
        w=assign_weights_dev(hold, industry, shares)
        pr=C.compute_calendar_pnl(w, data, clean, hold_days=5, cost_bp_bilateral=6.0)
        net_ann,_,net_nw,nobs=nw_stats(pr['net_excess_daily'].values)
        anc=ANCHORS[(pname,cfg)]; d=abs(net_ann-anc); ok=bool(d<TOL); all_pass&=ok
        check_rows.append(dict(period=pname,cfg=cfg,got=round(net_ann,4),anchor=anc,dabs=round(d,4),ok=ok))
        print('    %-16s got %+7.3f  anchor %+7.3f  |d|%.3f  %s'
              %(cfg,net_ann,anc,d,'OK' if ok else 'FAIL!!'), flush=True)
        wv=w.values; rr,cc=np.nonzero(wv)
        pool2_parts[cfg].append(pd.DataFrame({'ticker':col_ids[cc],'tradeDate':date_ids[rr],'weight':wv[rr,cc]}))
    del data,feats,neu_cond,neu_tvol,neu_rev0,neu_rev,neu_cmf,masks
    print('[period done] %s'%pname, flush=True)

# ---------------- gate on self-check ----------------
print('\n'+'='*66)
chk=pd.DataFrame(check_rows); print(chk.to_string(index=False))
if not all_pass:
    print('\n[ABORT] SELF-CHECK FAILED -- NO delivery files written.', flush=True); sys.exit(1)
print('\n[SELF-CHECK] ALL %d PASS -- writing delivery files.'%len(check_rows), flush=True)

# ---------------- write 池1 ----------------
p1=pd.concat(pool1_parts, ignore_index=True).sort_values(['tradeDate','ticker']).reset_index(drop=True)
p1.to_csv(os.path.join(OUT_DIR,'pool1_I11_screening.csv'), index=False)
print('  [pool1] pool1_I11_screening.csv  rows=%d  dates=%s..%s  avg_names/day=%.1f'
      %(len(p1), p1.tradeDate.min(), p1.tradeDate.max(), len(p1)/p1.tradeDate.nunique()), flush=True)

# ---------------- write 6 x 池2 ----------------
STATS=[]
for cfg in DELIV:
    dfp=pd.concat(pool2_parts[cfg], ignore_index=True).sort_values(['tradeDate','ticker']).reset_index(drop=True)
    fn='pool2_%s.csv'%FNAME[cfg]; dfp.to_csv(os.path.join(OUT_DIR,fn), index=False, float_format='%.8g')
    nd=dfp.tradeDate.nunique()
    STATS.append(dict(cfg=cfg, file=fn, rows=len(dfp), days=nd, avg_names=round(len(dfp)/nd,1),
                      avg_wsum=round(dfp.weight.sum()/nd,4), dmin=dfp.tradeDate.min(), dmax=dfp.tradeDate.max()))
    print('  [pool2] %-22s rows=%8d days=%4d avg_names/day=%6.1f avg_pos=%.3f'
          %(fn, len(dfp), nd, len(dfp)/nd, dfp.weight.sum()/nd), flush=True)

pd.DataFrame(STATS).to_csv(os.path.join(OUT_DIR,'_delivery_stats.csv'), index=False)
print('\n[ALLDONE] delivery files in %s'%OUT_DIR, flush=True)
