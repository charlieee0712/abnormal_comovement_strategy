#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# E6 WIDE SCAN v1 (2026-09) -- 探索从宽: 不预筛, 全部报出, 不淘汰. 采纳留给 E7 延长样本 + 用户过目.
# 用法: python e6_wide_scan.py --period <seg> --out <dir>    (4 段并行)
#       python e6_wide_scan.py --merge --out <dir>
# (B) 形状→角色表: 从 E3 shape.csv 算 tail_share / 汇总最差组 / 方向 / 轴(手工初判) -> roles.csv (不跑数)
# (C) 合成层深度曲线: M_mean2 / M_mean3_v2 在 keep 80..20% 七档 (十分位) + A4b / seq_tvol_cond 对照
# (D) 否决层全因子扫描: 35 因子 × 方向(形状定; 形状不清双向) × k∈{3,4,5,10} × 底座 {A4b, M_mean2}
# (E) 每配置对其底座的逐日 Δnet -> 配对 NW t (段 + 全窗口), 只作列; watch 标记 = 建议非闸门
# 成本 8bp; 另用 6bp 复算 A4b / M_mean3_v2 / A4b_CVRv5 对 E4 锚点 (接线自检 12 格, FAIL -> ABORT)
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
args = ap.parse_args(); OUT = args.out; os.makedirs(OUT, exist_ok=True)

COST = 8.0
SEGS = list(PERIODS.keys())
KEEPS = (80, 70, 60, 50, 40, 30, 20)          # 合成层保留比例 (%), 十分位实现
KS_VETO = (3, 4, 5, 10)                        # 否决层剔最差 1/k
BASES = ['A4b', 'M_mean2']
F_COND, F_TVOL, F_CR20, F_CVR = 'conditional_turnover', 'turnover_volatility_60d', 'cum_return_20d', 'CVR_20d'
SHAPE_CSV = '/mnt/sda2/lichenchen/results/20260903_1037_E3_single_factor/shape.csv'
ANCH6 = {  # E4 summary.csv L1A @6bp (== E5a ANCHORS)
 ('2010-2014','A4b'):2.5046, ('2015-2018','A4b'):5.0447, ('2019-2023','A4b'):7.5665, ('2024-2026','A4b'):8.9262,
 ('2010-2014','A4b_CVRv5'):3.0584, ('2015-2018','A4b_CVRv5'):6.9892, ('2019-2023','A4b_CVRv5'):8.4299, ('2024-2026','A4b_CVRv5'):10.3293,
 ('2010-2014','M_mean3_v2'):3.5462, ('2015-2018','M_mean3_v2'):7.0335, ('2019-2023','M_mean3_v2'):5.5572, ('2024-2026','M_mean3_v2'):6.3298,
}
TOL = 0.02
AXIS = {  # 规划 session 手工初判 (2026-09-03), 供读表; 后续可改
 'conditional_turnover':'A换手拥挤','turnover_volatility_60d':'A换手拥挤','abn_turnover':'A换手拥挤','stealth_score':'A换手拥挤',
 'cum_return_5d':'B价格反转','cum_return_10d':'B价格反转','cum_return_20d':'B价格反转','distance_from_high_20d':'B价格反转',
 'days_since_high':'B价格反转','recent_high_20d':'B价格反转','reversal_skip1':'B价格反转','info_discreteness_20d':'B价格反转','ou_halflife_60d':'B价格反转',
 'CVR_20d':'C日内位置','intraday_cvr_1d':'C日内位置','cum_intraday_ret_5d':'C日内位置','cum_intraday_ret_10d':'C日内位置',
 'cum_intraday_ret_20d':'C日内位置','CLV_20d':'C日内位置','shadow_asymmetry_20d':'C日内位置',
 'parkinson_vol':'D波动彩票','realized_vol_20d':'D波动彩票','vol_ratio_5d_20d':'D波动彩票','realized_kurtosis_20d':'D波动彩票',
 'realized_skewness_20d':'D波动彩票','max_abs_return_10d':'D波动彩票',
 'cmf_change_neg':'E资金流量价','CCV_20d':'E资金流量价','drawdown_volume_ratio':'E资金流量价','tug_of_war_20d':'E资金流量价',
 'RPV_20d':'E资金流量价','amihud_asymmetry_20d':'E资金流量价',
 'overnight_return_ratio_20d':'F隔夜昼夜','overnight_ret_surprise':'F隔夜昼夜','gap_survival_ratio':'F隔夜昼夜',
}

# ---------- verbatim helpers (export_delivery_pools.py / E4) ----------
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

def roles_table():
    """(B) 从 E3 shape.csv 算 tail_share / 汇总最差组 / 方向; 返回 DataFrame 与 {factor: [dirs]}"""
    sh = pd.read_csv(SHAPE_CSV); g = ['g1','g2','g3','g4','g5']; rows = []; dirs = {}
    for f, df in sh.groupby('factor'):
        m = df[g].mean().values; s = np.sort(m)
        tail = (s[1]-s[0])/(s[-1]-s[0]) if s[-1] > s[0] else np.nan
        worst = int(np.argmin(m)) + 1
        d = ['high'] if worst == 5 else (['low'] if worst == 1 else ['low','high'])
        dirs[f] = d
        role = ('渐变→合成候选' if (tail < 0.45 and abs(df.rho.mean()) > 0.6) else ('单尾→否决候选' if tail > 0.6 else '中间/弱'))
        rows.append(dict(factor=f, axis=AXIS.get(f,'?'), rho_mean=round(df.rho.mean(),2), rho_by_seg='/'.join('%+.1f'%v for v in df.rho),
                         worst_by_seg='/'.join(str(int(v)) for v in df.worst), worst_pooled=worst, tail_share=round(tail,2),
                         g_pooled='/'.join('%+.0f'%v for v in m), dirs_tested='+'.join(d), role_hint=role))
    return pd.DataFrame(rows).sort_values(['axis','tail_share']), dirs

def run_period(pname):
    ps, pe = PERIODS[pname]; t0 = time.time()
    log = open(os.path.join(OUT, 'log_%s.txt' % pname), 'w', encoding='utf-8')
    def P(*a):
        s = ' '.join(str(x) for x in a); print(s, flush=True); log.write(s + '\n'); log.flush()
    P('PERIOD', pname, ps, pe)
    roles, dirs = roles_table()
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
    specs = {s['name']: s for s in C.get_default_factor_specs()}
    specs['intraday_cvr_1d'] = {'name': 'intraday_cvr_1d', 'func': lambda d, f, i: d['close'] / d['vwap'] - 1}
    p0 = (pool0.values == 1)
    P('pipeline %.0fs  pool0 avg=%.1f' % (time.time() - t0, float(p0.sum(axis=1).mean())))

    # ---- neutralize all 35 ----
    raw = {n: s['func'](data, feats, industry) for n, s in specs.items()}
    neu = {n: C.precompute_neutralized_factor(raw[n], pool0, log_mcap) for n in specs}
    P('neutralized %d factors %.0fs' % (len(neu), time.time() - t0))
    pcond, ptvol, pcr20 = pct_cache(neu[F_COND]), pct_cache(neu[F_TVOL]), pct_cache(neu[F_CR20])

    # ---- base masks (verbatim E4/E5a) ----
    hc = C.build_factor_strategy_holdings_cached(neu[F_COND], pool0, 2, [2])
    m_a4b = (C.build_factor_strategy_holdings_cached(C.precompute_neutralized_factor(raw[F_TVOL], hc, log_mcap), hc, 2, [2]).values == 1)
    ht = C.build_factor_strategy_holdings_cached(neu[F_TVOL], pool0, 2, [2])
    m_seq_tc = (C.build_factor_strategy_holdings_cached(C.precompute_neutralized_factor(raw[F_COND], ht, log_mcap), ht, 2, [2]).values == 1)
    comp2 = combine([pcond, ptvol], 'mean'); comp3 = combine([pcond, ptvol, pcr20], 'mean')
    m_mean2 = (C.build_factor_strategy_holdings_cached(comp2, pool0, 2, [2]).values == 1)
    m_mean3 = (C.build_factor_strategy_holdings_cached(comp3, pool0, 2, [2]).values == 1)
    dc, dt, dr = drop_mask(neu[F_COND], pool0), drop_mask(neu[F_TVOL], pool0), drop_mask(neu[F_CR20], pool0)
    m_union3 = (p0 & ((dc.astype(int) + dt.astype(int) + dr.astype(int)) == 0))
    tox_cvr = drop_mask(neu[F_CVR], pool0, 5)
    base_masks = {'A4b': m_a4b, 'M_mean2': m_mean2}

    rows = []; daily = {}
    def evaluate(mask, cfg, base, factor, direction, k, cost, keep=np.nan):
        hold = pd.DataFrame(mask.astype(float), index=pool0.index, columns=pool0.columns)
        w = assign_weights_dev(hold, industry, shares); nh = (hold > 0).sum(axis=1); pos = w.sum(axis=1)
        pr = C.compute_calendar_pnl(w, data, clean, hold_days=5, cost_bp_bilateral=cost)
        nann, _, nnw, n = st(pr['net_excess_daily']); gann, _, _, _ = st(pr['gross_excess_daily'])
        mm = C.calendar_pnl_metrics(pr['net_excess_daily']); mdd = mm['mdd'] if mm else np.nan
        rows.append(dict(period=pname, cfg=cfg, base=base, factor=factor, direction=direction, k=k, keep=keep, cost=cost,
                         net_ann=nann, net_nw=nnw, gross_ann=gann, mdd_net=mdd, turn=float(pr['turnover_annual']),
                         avg_nh=float(nh[nh > 0].mean()) if (nh > 0).any() else np.nan,
                         avg_pos=float(pos[pos > 0].mean()) if (pos > 0).any() else np.nan, n=n))
        if cost == COST: daily[cfg] = pr['net_excess_daily']
        return nann

    # ---- 6bp anchor check (wiring) ----
    ok_all = True
    for cfg, mask in (('A4b', m_a4b), ('M_mean3_v2', m_mean3), ('A4b_CVRv5', m_a4b & ~tox_cvr)):
        got = evaluate(mask, cfg + '@6bp', None, None, None, None, 6.0)
        anc = ANCH6[(pname, cfg)]; d = abs(got - anc); ok = d < TOL; ok_all &= ok
        P('  [ANCHOR 6bp] %-12s got %+8.4f anchor %+8.4f |d|%.4f %s' % (cfg, got, anc, d, 'OK' if ok else 'FAIL!!'))
    if not ok_all:
        P('[ABORT] anchor FAIL in %s' % pname); pd.DataFrame(rows).to_csv(os.path.join(OUT, 'sf_%s.csv' % pname), index=False); log.close(); sys.exit(1)

    # ---- base rows @8bp ----
    evaluate(m_a4b, 'A4b', None, None, None, None, COST)
    evaluate(m_mean2, 'M_mean2', None, None, None, None, COST)
    evaluate(m_mean3, 'M_mean3_v2', 'M_mean2', F_CR20, 'high', 2, COST)
    evaluate(m_union3, 'M_union3_v2', None, None, None, None, COST)
    evaluate(m_seq_tc, 'seq_tvol_cond', 'A4b', None, None, None, COST)
    evaluate(m_a4b & ~tox_cvr, 'A4b_CVRv5', 'A4b', F_CVR, 'high', 5, COST)
    evaluate(m_mean3 & ~tox_cvr, 'M_mean3_v2_CVRv5', 'M_mean3_v2', F_CVR, 'high', 5, COST)
    evaluate(m_union3 & ~tox_cvr, 'M_union3_v2_CVRv5', 'M_union3_v2', F_CVR, 'high', 5, COST)
    P('  bases done %.0fs' % (time.time() - t0))

    # ---- (C) depth curves ----
    for name, comp, base in (('M_mean2', comp2, 'M_mean2'), ('M_mean3_v2', comp3, 'M_mean3_v2')):
        for keep in KEEPS:
            m = keep // 10
            mask = (C.build_factor_strategy_holdings_cached(comp, pool0, 10, list(range(m + 1, 11))).values == 1)
            evaluate(mask, '%s@keep%d' % (name, keep), base, None, None, 10, COST, keep=keep)
    P('  depth done %.0fs' % (time.time() - t0))

    # ---- (D) veto wide scan ----
    n_cfg = 0
    for f in sorted(neu):
        for direction in dirs.get(f, ['low', 'high']):
            for k in KS_VETO:
                kept = C.build_factor_strategy_holdings_cached(neu[f], pool0, k, [k] if direction == 'high' else [1])
                tox = p0 & ~(kept.values == 1)
                for b in BASES:
                    evaluate(base_masks[b] & ~tox, '%s|veto:%s:%s:k%d' % (b, f, direction, k), b, f, direction, k, COST); n_cfg += 1
        P('  [veto] %-26s done %.0fs' % (f, time.time() - t0))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'sf_%s.csv' % pname), index=False)
    pd.DataFrame(daily).to_parquet(os.path.join(OUT, 'daily_%s.parquet' % pname))
    P('[PERIOD DONE] %s rows=%d veto_cfgs=%d %.0fs' % (pname, len(rows), n_cfg, time.time() - t0)); log.close()

def merge():
    roles, _ = roles_table(); roles.to_csv(os.path.join(OUT, 'roles.csv'), index=False)
    sf = pd.concat([pd.read_csv(os.path.join(OUT, 'sf_%s.csv' % p)) for p in SEGS], ignore_index=True)
    daily = pd.concat([pd.read_parquet(os.path.join(OUT, 'daily_%s.parquet' % p)) for p in SEGS]).sort_index()
    sf.to_csv(os.path.join(OUT, 'sf_all.csv'), index=False); daily.to_parquet(os.path.join(OUT, 'daily_all.parquet'))
    seg_idx = {p: (pd.to_datetime(PERIODS[p][0]), pd.to_datetime(PERIODS[p][1])) for p in SEGS}
    cfgs = [c for c in dict.fromkeys(sf[sf.cost == COST].cfg)]
    meta = sf[sf.cost == COST].drop_duplicates('cfg').set_index('cfg')[['base', 'factor', 'direction', 'k', 'keep']]
    out = []
    for cfg in cfgs:
        r = dict(cfg=cfg, **meta.loc[cfg].to_dict()); r['axis'] = AXIS.get(r['factor'], '') if isinstance(r['factor'], str) else ''
        s = sf[(sf.cfg == cfg) & (sf.cost == COST)].set_index('period')
        for p in SEGS:
            r['net_%s' % p[:4]] = s.net_ann.get(p, np.nan); r['nw_%s' % p[:4]] = s.net_nw.get(p, np.nan)
        r['turn'] = s.turn.mean(); r['nh'] = s.avg_nh.mean()
        fa, _, fnw, _ = st(daily[cfg]); r['net_full'] = fa; r['nw_full'] = fnw
        b = r['base']
        if isinstance(b, str) and b in daily.columns:
            d = daily[cfg] - daily[b]; npos = 0
            for p in SEGS:
                a, e = seg_idx[p]; da, _, dt_, _ = st(d.loc[a:e]); r['dnet_%s' % p[:4]] = da; r['dt_%s' % p[:4]] = dt_; npos += int(da > 0)
            da, _, dt_, _ = st(d); r['dnet_full'] = da; r['dt_full'] = dt_; r['n_seg_pos'] = npos
            r['watch'] = bool(dt_ > 1.0 and npos >= 2)
        else:
            for p in SEGS: r['dnet_%s' % p[:4]] = np.nan; r['dt_%s' % p[:4]] = np.nan
            r['dnet_full'] = np.nan; r['dt_full'] = np.nan; r['n_seg_pos'] = np.nan; r['watch'] = False
        out.append(r)
    scan = pd.DataFrame(out); scan.to_csv(os.path.join(OUT, 'scan_all.csv'), index=False)
    f = open(os.path.join(OUT, 'summary.txt'), 'w', encoding='utf-8')
    def P(s=''): print(s, flush=True); f.write(s + '\n')
    def seg4(r, pre, w='%+6.2f'): return '/'.join(w % r['%s_%s' % (pre, p[:4])] for p in SEGS)
    P('E6 WIDE SCAN  成本 %.0fbp  4 段 = %s  |  net = DEV net ann %%  nw = NW t  dnet/dt = 对底座的逐日 Δnet 年化 / 配对 NW t' % (COST, ' / '.join(SEGS)))
    P('\n== (B) 形状→角色表 (来自 E3 shape.csv; 轴=手工初判)'); P(roles.to_string(index=False))
    P('\n== (A) v2 六形态 + 对照 @8bp')
    for cfg in ['A4b', 'M_mean2', 'M_mean3_v2', 'M_union3_v2', 'seq_tvol_cond', 'A4b_CVRv5', 'M_mean3_v2_CVRv5', 'M_union3_v2_CVRv5']:
        r = scan[scan.cfg == cfg].iloc[0]
        P('  %-18s net %s nw %s | full %+5.2f (t %+4.2f) | turn %4.1f nh %5.1f%s' % (cfg, seg4(r, 'net'), seg4(r, 'nw', '%+5.2f'), r.net_full, r.nw_full, r.turn, r.nh,
          ('' if pd.isna(r.dt_full) else ' | vs %s: dnet %s  dt %s  full dt %+4.2f' % (r.base, seg4(r, 'dnet'), seg4(r, 'dt', '%+4.2f'), r.dt_full))))
    P('\n== (C) 合成层深度曲线 (十分位; A4b 保留约 25%%, seq_tvol_cond 同)')
    for name in ('M_mean2', 'M_mean3_v2'):
        for keep in KEEPS:
            r = scan[scan.cfg == '%s@keep%d' % (name, keep)].iloc[0]
            P('  %-18s net %s nw %s | full %+5.2f (t %+4.2f) | nh %5.1f turn %4.1f | vs keep50 dt %s full %+4.2f' % (r.cfg, seg4(r, 'net'), seg4(r, 'nw', '%+5.2f'), r.net_full, r.nw_full, r.nh, r.turn, seg4(r, 'dt', '%+4.2f'), r.dt_full))
    P('\n== (D) 否决层全因子扫描, 每底座按全窗口配对 t 降序 (全部行在 scan_all.csv; 这里各列前 60)')
    v = scan[scan.cfg.str.contains(r'\|veto:', regex=True)]
    for b in BASES:
        vb = v[v.base == b].sort_values('dt_full', ascending=False)
        P('\n  -- base %s  (%d 配置, watch %d)' % (b, len(vb), int(vb.watch.sum())))
        for _, r in vb.head(60).iterrows():
            P('  %-46s %s dnet %s dt %s | full dnet %+5.2f dt %+4.2f | net %s nw %s | nh %5.1f%s' % (
                r.cfg, r.axis, seg4(r, 'dnet'), seg4(r, 'dt', '%+4.2f'), r.dnet_full, r.dt_full, seg4(r, 'net'), seg4(r, 'nw', '%+5.2f'), r.nh, ' *watch' if r.watch else ''))
    P('\n== (D2) 每轴每底座最佳 (按全窗口配对 t)')
    for b in BASES:
        vb = v[v.base == b]
        for ax, g in vb.groupby('axis'):
            r = g.sort_values('dt_full', ascending=False).iloc[0]
            P('  %-8s %-46s full dnet %+5.2f dt %+4.2f  segs+ %d/4' % (b, r.cfg, r.dnet_full, r.dt_full, int(r.n_seg_pos)))
    P('\n== watch 建议清单 (全窗口配对 t>1.0 且 ≥2/4 段 Δnet>0; 是建议不是闸门): %d 个' % int(scan.watch.sum()))
    P('[MERGE DONE] cfgs=%d rows=%d' % (len(scan), len(sf))); f.close()

if args.merge: merge()
else:
    assert args.period in PERIODS, args.period; run_period(args.period)
