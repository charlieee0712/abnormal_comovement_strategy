#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# E3 SINGLE-FACTOR RE-ADJUDICATION (2026-09) -- 全候选库在新口径下的单因子表 (视角① 形状 + 视角② DEV 剔尾), 每段一进程.
# 用法: python e3_single_factor_rerun.py --period 2010-2014 --out <dir>   (4 段各起一进程, 并行)
#       python e3_single_factor_rerun.py --merge --out <dir>               (4 段跑完后合并 + 打印汇总)
# 口径 = 生产口径 (== E2): I11 pool0 (mcap=0) 内 mcap 中性化; DEV 偏离约束权重; 干净全市场等权基准; hold 5; 6bp;
#        引擎 L0R=(exec_lag 0, adjust False) 旧口径 与 L1A=(1, True) 新口径 并列.
# 因子 = C.get_default_factor_specs() 全部 34 + 登记因子 intraday_cvr_1d (= close/vwap-1, 台账 H1, 探索性级).
# 每因子: k in {2,5} x side in {keepH(剔最低组), keepL(剔最高组)}; 形状 = 5 组 fwd-5d 超额 (bench=pool0, 已复权) + Spearman rho.
# READ-ONLY / import-only. 窗口 = PERIODS 不变. 只出表, 不判定.
import sys, os, argparse, time
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import define_i11_signal, build_observation_pool, apply_hard_constraints
import comprehensive_factor_diagnosis as C

ap = argparse.ArgumentParser()
ap.add_argument('--period', default=None); ap.add_argument('--out', required=True); ap.add_argument('--merge', action='store_true')
args = ap.parse_args()
OUT = args.out; os.makedirs(OUT, exist_ok=True)
COMBOS = [(0, False), (1, True)]
def tag(lag, adj): return 'L%d%s' % (lag, 'A' if adj else 'R')
KS = (2, 5)
SIDES = {'keepH': lambda k: [1], 'keepL': lambda k: [k]}     # drop_groups
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
# ---------------------------------------------------------------------

def spearman5(vals):
    v = np.asarray(vals, float)
    if np.isnan(v).any() or len(v) < 3: return np.nan
    r = pd.Series(v).rank().values; g = np.arange(1, len(v) + 1)
    return float(np.corrcoef(r, g)[0, 1])

def run_period(pname):
    ps, pe = PERIODS[pname]
    log = open(os.path.join(OUT, 'log_%s.txt' % pname), 'w', encoding='utf-8')
    def P(*a):
        s = ' '.join(str(x) for x in a); print(s, flush=True); log.write(s + '\n'); log.flush()
    P('PERIOD', pname, ps, pe); t0 = time.time()
    data = load_all_daily_data(start_date=ps, end_date=pe)
    feats = calc_all_daily_features(data)
    close = data['close']; bse = [c for c in close.columns if is_bse(c)]
    base_pool = get_base_pool(data)
    mature = close.notna().astype(float).rolling(20, min_periods=1).sum() >= 20
    clean = ((base_pool == 1) & mature).astype(float)
    if bse: clean[bse] = 0.0
    signal = define_i11_signal(feats, base_pool)
    obs = build_observation_pool(signal, obs_window=5)
    pool0 = apply_hard_constraints(obs, data, feats, min_mcap=0)
    log_mcap = C.compute_log_mcap(data.get('mcap'))
    industry = data.get('industry_zx1', data.get('industry'))
    if industry is not None:
        industry = industry.reindex(index=close.index, columns=close.columns)
    shares = bench_industry_shares(clean, industry)
    fwd5 = C.compute_forward_5d_excess(data, pool0, hold_days=5)          # 视角① 形状: bench=pool0, 已复权 (默认)
    specs = list(C.get_default_factor_specs())
    specs.append({'name': 'intraday_cvr_1d', 'func': lambda d, f, i: d['close'] / d['vwap'] - 1})   # 台账 H1, 探索性级
    P('pipeline ready %.0fs  n_factors=%d  pool0 avg=%.1f' % (time.time() - t0, len(specs), float((pool0 == 1).sum(axis=1).mean())))
    rows = []; shapes = []
    for si, s in enumerate(specs):
        name = s['name']; t1 = time.time()
        try:
            raw = s['func'](data, feats, industry)
            neu = C.precompute_neutralized_factor(raw, pool0, log_mcap)
        except Exception as e:
            P('  [SKIP] %s: %r' % (name, e)); shapes.append(dict(period=pname, factor=name, err=repr(e))); continue
        es = C.event_study_analysis_cached(neu, fwd5, pool0, 5, name)
        if es is not None:
            gm = es['group_means_bp']; g = [gm.get(i, np.nan) for i in range(1, 6)]
            shapes.append(dict(period=pname, factor=name, g1=g[0], g2=g[1], g3=g[2], g4=g[3], g5=g[4],
                               rho=spearman5(g), worst=int(np.nanargmin(g)) + 1 if not all(np.isnan(g)) else -1,
                               ls_sharpe=es['long_short_gross_sharpe'], n_dates=len(neu)))
        else:
            shapes.append(dict(period=pname, factor=name, n_dates=len(neu)))
        for k in KS:
            for side, dg in SIDES.items():
                hold = C.build_factor_strategy_holdings_cached(neu, pool0, k, dg(k))
                w = assign_weights_dev(hold, industry, shares)
                nh = (hold > 0).sum(axis=1); pos = w.sum(axis=1)
                for lag, adj in COMBOS:
                    pr = C.compute_calendar_pnl(w, data, clean, hold_days=5, cost_bp_bilateral=6.0, exec_lag=lag, adjust=adj)
                    nann, nnv, nnw, n = nw_stats(pr['net_excess_daily'].values)
                    gann, _, _, _ = nw_stats(pr['gross_excess_daily'].values)
                    mm = C.calendar_pnl_metrics(pr['net_excess_daily']); mdd = mm['mdd'] if mm else np.nan
                    rows.append(dict(period=pname, factor=name, k=k, side=side, combo=tag(lag, adj),
                                     net_ann=nann, net_naive=nnv, net_nw=nnw, gross_ann=gann, mdd_net=mdd,
                                     avg_nh=float(nh[nh > 0].mean()) if (nh > 0).any() else np.nan,
                                     avg_pos=float(pos[pos > 0].mean()) if (pos > 0).any() else np.nan,
                                     turn=float(pr['turnover_annual']), n=n))
        P('  [%2d/%d] %-26s %.0fs' % (si + 1, len(specs), name, time.time() - t1))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'sf_%s.csv' % pname), index=False)
    pd.DataFrame(shapes).to_csv(os.path.join(OUT, 'shape_%s.csv' % pname), index=False)
    P('[PERIOD DONE] %s  rows=%d  %.0fs' % (pname, len(rows), time.time() - t0)); log.close()

def merge():
    sf = pd.concat([pd.read_csv(os.path.join(OUT, 'sf_%s.csv' % p)) for p in SEGS], ignore_index=True)
    sh = pd.concat([pd.read_csv(os.path.join(OUT, 'shape_%s.csv' % p)) for p in SEGS], ignore_index=True)
    sf.to_csv(os.path.join(OUT, 'single_factor.csv'), index=False); sh.to_csv(os.path.join(OUT, 'shape.csv'), index=False)
    out = open(os.path.join(OUT, 'summary.txt'), 'w', encoding='utf-8')
    def P(s=''): print(s, flush=True); out.write(s + '\n')
    factors = list(dict.fromkeys(sf.factor))
    P('SINGLE-FACTOR TABLE   DEV net ann %% | NW | turn   4 段 = %s   L1A=新口径  L0R=旧口径' % ' / '.join(SEGS))
    for f in factors:
        P('== ' + f)
        for k in KS:
            for side in SIDES:
                for combo in ('L1A', 'L0R'):
                    d = sf[(sf.factor == f) & (sf.k == k) & (sf.side == side) & (sf.combo == combo)].set_index('period')
                    net = '/'.join('%+6.2f' % d.net_ann.get(s, np.nan) for s in SEGS)
                    nw = '/'.join('%+5.2f' % d.net_nw.get(s, np.nan) for s in SEGS)
                    tn = '/'.join('%4.1f' % d.turn.get(s, np.nan) for s in SEGS)
                    P('   k=%d %-5s %s  net %s | NW %s | turn %s' % (k, side, combo, net, nw, tn))
        shp = sh[sh.factor == f].set_index('period')
        if 'rho' in shp.columns:
            P('   shape(新口径 5组 fwd5d 超额, bench=pool0)  ' + '  '.join(
                '%s rho %+.2f worst G%d' % (s, shp.rho.get(s, np.nan), int(shp.worst.get(s, -1))) for s in SEGS))
    P('\n[MERGE DONE] factors=%d rows=%d' % (len(factors), len(sf)))
    out.close()

if args.merge:
    merge()
else:
    assert args.period in PERIODS, args.period
    run_period(args.period)
