#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# E6b WIDE SCAN v2 (2026-09) -- 探索从宽: 否决层跨轴叠加 + 新深度底座 + 主题 sleeve 与组合层 1/N 合并. 全部报出, 不淘汰.
# 用法: python e6b_stack_sleeves.py --period <seg> --out <dir>   (4 段并行);  --merge --out <dir>
# (A) 底座: A4b / M_mean2@keep30 / M_mean2@keep20 (+ 对照 M_mean2 / M_mean3_v2 / A4b 深度变体 3 个)
# (B) 单否决: 11 因子 × k{5,10} × 3 底座
# (C) 双否决 C×B: 3×3 因子对 × kC{5,10} × kB{5,10} × 3 底座
# (D) 三否决: 9 个 C×B 对 (k10,k10) + 其他轴 5 因子 (k10) × 3 底座
# (E) 主题 sleeve S_A/S_B/S_C 各 2 构造 × 2 深度 + 组合层 1/N 合并 {ABC, AB, AC, BC} × 2 深度 + sleeve 日收益相关矩阵
# 配对 NW t: 每配置 vs 底座 (dt_base), 叠加配置另 vs 其最好的单否决父 (dt_parent). 成本 8bp.
import sys, os, argparse, time, itertools
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

COST = 8.0; TOL = 0.02
SEGS = list(PERIODS.keys())
E6_SCAN = '/mnt/sda2/lichenchen/results/20260904_1051_E6_wide_scan/scan_all.csv'
ANCHORS = {'A4b': 'A4b', 'A4b|CVR_20d:k5': 'A4b|veto:CVR_20d:high:k5', 'M_mean2@keep30': 'M_mean2@keep30'}   # E6b 名 -> E6 scan_all 名
F_COND, F_TVOL, F_CR20, F_CR5, F_CVR, F_CVR1, F_CI5 = ('conditional_turnover', 'turnover_volatility_60d', 'cum_return_20d',
                                                        'cum_return_5d', 'CVR_20d', 'intraday_cvr_1d', 'cum_intraday_ret_5d')
BASES = ['A4b', 'M_mean2@keep30', 'M_mean2@keep20']
VETO = {  # factor: (axis, direction)
 'intraday_cvr_1d': ('C', 'high'), 'cum_intraday_ret_5d': ('C', 'high'), 'CVR_20d': ('C', 'high'),
 'cum_return_5d': ('B', 'high'), 'cum_return_10d': ('B', 'high'), 'cum_return_20d': ('B', 'high'),
 'stealth_score': ('A', 'high'), 'max_abs_return_10d': ('D', 'high'), 'vol_ratio_5d_20d': ('D', 'high'),
 'CCV_20d': ('E', 'high'), 'drawdown_volume_ratio': ('E', 'low'),
}
C_AX = [f for f, (a, _) in VETO.items() if a == 'C']; B_AX = [f for f, (a, _) in VETO.items() if a == 'B']
OTHER = [f for f, (a, _) in VETO.items() if a not in ('B', 'C')]
KS = (5, 10)

# ---------- verbatim helpers (E6) ----------
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
# -------------------------------------------

def st(x): return nw_stats(np.asarray(x, float))
def keep_mask(comp, pool0, keep):   # 十分位, 保留最低 keep% (high=worst)
    m = keep // 10
    return (C.build_factor_strategy_holdings_cached(comp, pool0, 10, list(range(m + 1, 11))).values == 1)

def run_period(pname):
    ps, pe = PERIODS[pname]; t0 = time.time()
    log = open(os.path.join(OUT, 'log_%s.txt' % pname), 'w', encoding='utf-8')
    def P(*a):
        s = ' '.join(str(x) for x in a); print(s, flush=True); log.write(s + '\n'); log.flush()
    P('PERIOD', pname, ps, pe)
    e6 = pd.read_csv(E6_SCAN).set_index('cfg'); ycol = 'net_%s' % pname[:4]
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
    need = sorted(set([F_COND, F_TVOL, F_CR20, F_CR5, F_CVR, F_CVR1, F_CI5] + list(VETO)))
    raw = {n: specs[n]['func'](data, feats, industry) for n in need}
    neu = {n: C.precompute_neutralized_factor(raw[n], pool0, log_mcap) for n in need}
    pct = {n: pct_cache(neu[n]) for n in need}
    P('pipeline+neutralize %d factors %.0fs  pool0 avg=%.1f' % (len(neu), time.time() - t0, float(p0.sum(axis=1).mean())))

    # ---- bases + cousins ----
    hc = C.build_factor_strategy_holdings_cached(neu[F_COND], pool0, 2, [2])
    m_a4b = (C.build_factor_strategy_holdings_cached(C.precompute_neutralized_factor(raw[F_TVOL], hc, log_mcap), hc, 2, [2]).values == 1)
    comp2 = combine([pct[F_COND], pct[F_TVOL]], 'mean'); comp3 = combine([pct[F_COND], pct[F_TVOL], pct[F_CR20]], 'mean')
    m_mean2 = keep_mask(comp2, pool0, 50); m_k30 = keep_mask(comp2, pool0, 30); m_k20 = keep_mask(comp2, pool0, 20)
    m_mean3 = keep_mask(comp3, pool0, 50)
    def a4b_variant(kc, kt):   # cond 保留最低 kc% -> 组内 tvol 重中性化保留最低 kt%
        h1 = pd.DataFrame(keep_mask(pct[F_COND], pool0, kc).astype(float), index=pool0.index, columns=pool0.columns)
        return keep_mask(pct_cache(C.precompute_neutralized_factor(raw[F_TVOL], h1, log_mcap)), h1, kt)
    m_a4b_60_50 = a4b_variant(60, 50); m_a4b_50_60 = a4b_variant(50, 60); m_a4b_40_50 = a4b_variant(40, 50)
    base_masks = {'A4b': m_a4b, 'M_mean2@keep30': m_k30, 'M_mean2@keep20': m_k20}

    # ---- veto masks ----
    tox = {}
    for f, (ax, d) in VETO.items():
        for k in KS:
            kept = C.build_factor_strategy_holdings_cached(neu[f], pool0, k, [k] if d == 'high' else [1])
            tox[(f, k)] = p0 & ~(kept.values == 1)

    rows = []; daily = {}; wcache = {}
    def evaluate(mask=None, cfg='', base=None, parent=None, kind='', W=None):
        if W is None:
            hold = pd.DataFrame(mask.astype(float), index=pool0.index, columns=pool0.columns)
            W = assign_weights_dev(hold, industry, shares)
        nh = (W > 0).sum(axis=1); pos = W.sum(axis=1)
        pr = C.compute_calendar_pnl(W, data, clean, hold_days=5, cost_bp_bilateral=COST)
        nann, _, nnw, n = st(pr['net_excess_daily']); gann, _, _, _ = st(pr['gross_excess_daily'])
        mm = C.calendar_pnl_metrics(pr['net_excess_daily']); mdd = mm['mdd'] if mm else np.nan
        rows.append(dict(period=pname, cfg=cfg, kind=kind, base=base, parent=parent, net_ann=nann, net_nw=nnw, gross_ann=gann, mdd_net=mdd,
                         turn=float(pr['turnover_annual']), avg_nh=float(nh[nh > 0].mean()) if (nh > 0).any() else np.nan,
                         avg_pos=float(pos[pos > 0].mean()) if (pos > 0).any() else np.nan, n=n))
        daily[cfg] = pr['net_excess_daily']
        if kind == 'sleeve': wcache[cfg] = W      # 只缓存 sleeve 权重 (组合层 1/N 用); 全缓存 337 × ~52 MB ≈ 18 GB/进程
        return nann

    # ---- (A) bases + cousins; anchors ----
    for cfg, m in (('A4b', m_a4b), ('M_mean2@keep30', m_k30), ('M_mean2@keep20', m_k20), ('M_mean2', m_mean2), ('M_mean3_v2', m_mean3),
                   ('A4b_var_c60_t50', m_a4b_60_50), ('A4b_var_c50_t60', m_a4b_50_60), ('A4b_var_c40_t50', m_a4b_40_50)):
        evaluate(m, cfg, base=('A4b' if cfg != 'A4b' else None), kind='base')
    evaluate(m_a4b & ~tox[(F_CVR, 5)], 'A4b|CVR_20d:k5', base='A4b', kind='single')   # 锚点单否决, 命名与 (B) 一致
    ok_all = True
    for cfg, e6name in ANCHORS.items():
        got = [r['net_ann'] for r in rows if r['cfg'] == cfg][0]; anc = float(e6.loc[e6name, ycol]); d = abs(got - anc); ok = d < TOL; ok_all &= ok
        P('  [ANCHOR E6@8bp] %-28s got %+8.4f anchor %+8.4f |d|%.4f %s' % (cfg, got, anc, d, 'OK' if ok else 'FAIL!!'))
    if not ok_all:
        P('[ABORT] anchor FAIL in %s' % pname); pd.DataFrame(rows).to_csv(os.path.join(OUT, 'sf_%s.csv' % pname), index=False); log.close(); sys.exit(1)
    P('  bases done %.0fs' % (time.time() - t0))

    # ---- (B) singles on 3 bases ----
    for b in BASES:
        for f, (ax, d) in VETO.items():
            for k in KS:
                cfg = '%s|%s:k%d' % (b, f, k)
                if cfg == 'A4b|CVR_20d:k5': continue   # 已作为锚点行先算过
                evaluate(base_masks[b] & ~tox[(f, k)], cfg, base=b, kind='single')
    P('  singles done %.0fs' % (time.time() - t0))

    # ---- (C) C×B pairs ----
    for b in BASES:
        for fc in C_AX:
            for fb in B_AX:
                for kc in KS:
                    for kb in KS:
                        evaluate(base_masks[b] & ~tox[(fc, kc)] & ~tox[(fb, kb)], '%s|%s:k%d+%s:k%d' % (b, fc, kc, fb, kb), base=b,
                                 parent='%s|%s:k%d;%s|%s:k%d' % (b, fc, kc, b, fb, kb), kind='pair')
    P('  pairs done %.0fs' % (time.time() - t0))

    # ---- (D) triples: C×B at (10,10) + one other-axis at k10 ----
    for b in BASES:
        for fc in C_AX:
            for fb in B_AX:
                for fo in OTHER:
                    evaluate(base_masks[b] & ~tox[(fc, 10)] & ~tox[(fb, 10)] & ~tox[(fo, 10)], '%s|%s:k10+%s:k10+%s:k10' % (b, fc, fb, fo), base=b,
                             parent='%s|%s:k10+%s:k10' % (b, fc, fb), kind='triple')
    P('  triples done %.0fs' % (time.time() - t0))

    # ---- (E) theme sleeves + portfolio-level 1/N ----
    sleeves = {}
    compB = combine([pct[F_CR5], pct[F_CR20]], 'mean'); compC = combine([pct[F_CVR1], pct[F_CI5], pct[F_CVR]], 'mean')
    for keep in (50, 30):
        sleeves['S_A(cond+tvol)@%d' % keep] = keep_mask(comp2, pool0, keep)
        sleeves['S_B(cr20)@%d' % keep] = keep_mask(pct[F_CR20], pool0, keep)
        sleeves['S_B(cr5+cr20)@%d' % keep] = keep_mask(compB, pool0, keep)
        sleeves['S_C(CVR20)@%d' % keep] = keep_mask(pct[F_CVR], pool0, keep)
        sleeves['S_C(cvr1+ci5+CVR20)@%d' % keep] = keep_mask(compC, pool0, keep)
    for cfg, m in sleeves.items():
        evaluate(m, cfg, base='A4b', kind='sleeve')
    for keep in (50, 30):
        A, B1, B2, C1, C2 = ['S_A(cond+tvol)@%d' % keep, 'S_B(cr20)@%d' % keep, 'S_B(cr5+cr20)@%d' % keep, 'S_C(CVR20)@%d' % keep, 'S_C(cvr1+ci5+CVR20)@%d' % keep]
        for name, parts in (('P_ABC', [A, B1, C1]), ('P_ABC_comp', [A, B2, C2]), ('P_AB', [A, B1]), ('P_AC', [A, C1]), ('P_BC', [B1, C1])):
            W = sum(wcache[p] for p in parts) / len(parts)
            evaluate(None, '%s@%d' % (name, keep), base='A4b', parent=';'.join(parts), kind='portfolio', W=W)
    P('  sleeves done %.0fs' % (time.time() - t0))

    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'sf_%s.csv' % pname), index=False)
    pd.DataFrame(daily).to_parquet(os.path.join(OUT, 'daily_%s.parquet' % pname))
    P('[PERIOD DONE] %s rows=%d %.0fs' % (pname, len(rows), time.time() - t0)); log.close()

def merge():
    sf = pd.concat([pd.read_csv(os.path.join(OUT, 'sf_%s.csv' % p)) for p in SEGS], ignore_index=True)
    daily = pd.concat([pd.read_parquet(os.path.join(OUT, 'daily_%s.parquet' % p)) for p in SEGS]).sort_index()
    sf.to_csv(os.path.join(OUT, 'sf_all.csv'), index=False); daily.to_parquet(os.path.join(OUT, 'daily_all.parquet'))
    seg_idx = {p: (pd.to_datetime(PERIODS[p][0]), pd.to_datetime(PERIODS[p][1])) for p in SEGS}
    meta = sf.drop_duplicates('cfg').set_index('cfg')[['kind', 'base', 'parent']]
    def paired(cfg, ref):
        d = daily[cfg] - daily[ref]; out = {}; npos = 0
        for p in SEGS:
            a, e = seg_idx[p]; da, _, dt_, _ = st(d.loc[a:e]); out['dnet_%s' % p[:4]] = da; out['dt_%s' % p[:4]] = dt_; npos += int(da > 0)
        da, _, dt_, _ = st(d); out['dnet_full'] = da; out['dt_full'] = dt_; out['n_seg_pos'] = npos; return out
    out = []
    for cfg in meta.index:
        r = dict(cfg=cfg, **meta.loc[cfg].to_dict()); s = sf[sf.cfg == cfg].set_index('period')
        for p in SEGS: r['net_%s' % p[:4]] = s.net_ann.get(p, np.nan); r['nw_%s' % p[:4]] = s.net_nw.get(p, np.nan)
        r['turn'] = s.turn.mean(); r['nh'] = s.avg_nh.mean(); r['pos'] = s.avg_pos.mean()
        fa, _, fnw, _ = st(daily[cfg]); r['net_full'] = fa; r['nw_full'] = fnw
        b = r['base']
        if isinstance(b, str) and b in daily.columns:
            r.update(paired(cfg, b))
        # parent: 叠加配置对"最好的单否决父"的增量 (取父列表中全窗口 net 最高者)
        par = r['parent']
        if isinstance(par, str) and r['kind'] in ('pair', 'triple'):
            cands = [c for c in par.split(';') if c in daily.columns]
            if cands:
                best = max(cands, key=lambda c: st(daily[c])[0]); pp = paired(cfg, best)
                r['parent_best'] = best; r['dnet_vs_parent'] = pp['dnet_full']; r['dt_vs_parent'] = pp['dt_full']; r['segpos_vs_parent'] = pp['n_seg_pos']
        r['watch'] = bool(r.get('dt_full', np.nan) > 1.0 and r.get('n_seg_pos', 0) >= 2)
        out.append(r)
    scan = pd.DataFrame(out)
    nh_base = scan.set_index('cfg').nh
    scan['nh_ratio'] = [scan.nh[i] / nh_base.get(scan.base[i], np.nan) if isinstance(scan.base[i], str) else np.nan for i in range(len(scan))]
    scan.to_csv(os.path.join(OUT, 'scan_all.csv'), index=False)
    # sleeve correlation
    sl = [c for c in daily.columns if c.startswith('S_')]
    corr = daily[sl].corr(); corr.to_csv(os.path.join(OUT, 'sleeve_corr.csv'))
    f = open(os.path.join(OUT, 'summary.txt'), 'w', encoding='utf-8')
    def P(s=''): print(s, flush=True); f.write(s + '\n')
    def seg4(r, pre, w='%+6.2f'): return '/'.join(w % r['%s_%s' % (pre, p[:4])] for p in SEGS)
    def line(r, show_parent=False):
        s = '  %-58s net %s nw %s | full %+5.2f t %+4.2f | nh %5.1f (%.2f) turn %4.1f' % (r.cfg, seg4(r, 'net'), seg4(r, 'nw', '%+5.2f'), r.net_full, r.nw_full, r.nh, r.nh_ratio if pd.notna(r.nh_ratio) else float('nan'), r.turn)
        if pd.notna(r.get('dt_full', np.nan)): s += ' | vs base dnet %+5.2f dt %+5.2f segs+ %d' % (r.dnet_full, r.dt_full, int(r.n_seg_pos))
        if show_parent and pd.notna(r.get('dt_vs_parent', np.nan)): s += ' | vs best-single dnet %+5.2f dt %+5.2f segs+ %d' % (r.dnet_vs_parent, r.dt_vs_parent, int(r.segpos_vs_parent))
        return s + (' *watch' if r.watch else '')
    P('E6b  成本 %.0fbp  4 段 = %s  |  nh(比) = 日均持仓 (相对底座)  dt = 逐日 Δnet 配对 NW t' % (COST, ' / '.join(SEGS)))
    P('\n== (A) 底座与对照'); [P(line(r)) for _, r in scan[scan.kind == 'base'].iterrows()]
    P('\n== (B) 单否决 × 3 底座 (按 dt_full 降序, 每底座前 12)')
    for b in BASES:
        P('  -- base %s' % b); [P(line(r)) for _, r in scan[(scan.kind == 'single') & (scan.base == b)].sort_values('dt_full', ascending=False).head(12).iterrows()]
    P('\n== (C) 双否决 C×B (按 vs best-single 的 dt 降序, 每底座前 15; 全部见 scan_all.csv)')
    for b in BASES:
        P('  -- base %s' % b); [P(line(r, True)) for _, r in scan[(scan.kind == 'pair') & (scan.base == b)].sort_values('dt_vs_parent', ascending=False).head(15).iterrows()]
    P('\n== (D) 三否决 (C×B @k10 + 其他轴 k10; 按 vs pair 的 dt 降序, 每底座前 10)')
    for b in BASES:
        P('  -- base %s' % b); [P(line(r, True)) for _, r in scan[(scan.kind == 'triple') & (scan.base == b)].sort_values('dt_vs_parent', ascending=False).head(10).iterrows()]
    P('\n== (E) 主题 sleeve (vs A4b 只作参照)'); [P(line(r)) for _, r in scan[scan.kind == 'sleeve'].iterrows()]
    P('\n== (E2) 组合层 1/N 合并 (vs A4b)'); [P(line(r)) for _, r in scan[scan.kind == 'portfolio'].iterrows()]
    P('\n== (E3) sleeve 日超额收益相关'); P(corr.round(2).to_string())
    P('\n== 三种合并方式并排 (全窗口 net | t | turn | nh): 决策层 M_mean3_v2 / 否决层 A4b+CVR k5 与最佳 pair / 组合层 P_ABC@30')
    for cfg in ['M_mean3_v2', 'A4b|CVR_20d:k5', 'P_ABC@30', 'P_ABC_comp@30', 'P_ABC@50']:
        r = scan[scan.cfg == cfg].iloc[0]; P('  %-28s %+5.2f | %+4.2f | %4.1f | %5.1f' % (cfg, r.net_full, r.nw_full, r.turn, r.nh))
    bp = scan[scan.kind == 'pair'].sort_values('net_full', ascending=False).iloc[0]; P('  best pair by full net: %s  %+5.2f | %+4.2f | %4.1f | %5.1f' % (bp.cfg, bp.net_full, bp.nw_full, bp.turn, bp.nh))
    P('\n== 叠加是否普遍有增量 (对最佳单否决父的增量分布; 防只看最大值)')
    for kind in ('pair', 'triple'):
        g = scan[scan.kind == kind]; gn = g.dnet_vs_parent.dropna(); gt = g.dt_vs_parent.dropna(); sp = g.segpos_vs_parent.dropna()
        P('  %-6s n=%d  dnet_vs_parent 中位 %+5.2f  >0 占比 %.0f%%  dt 中位 %+4.2f  dt>1 占比 %.0f%%  ≥3/4 段正占比 %.0f%%'
          % (kind, len(gn), gn.median(), 100 * (gn > 0).mean(), gt.median(), 100 * (gt > 1).mean(), 100 * (sp >= 3).mean()))
    P('\nwatch 建议 (dt_full>1 且 ≥2/4 段正; 非闸门): %d / %d' % (int(scan.watch.sum()), len(scan)))
    P('[MERGE DONE] cfgs=%d rows=%d' % (len(scan), len(sf))); f.close()

if args.merge: merge()
else:
    assert args.period in PERIODS, args.period; run_period(args.period)
