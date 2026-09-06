#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6e 共享内核库 (2026-09-06)。
   稀疏引擎 + 稠密参照引擎 + DEV 权重 + P114 核 + 否决族 + 随机键。
   本模块只提供构件, 不自己跑任何东西。
"""
import os, sys, time, json, hashlib
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import define_i11_signal, build_observation_pool, apply_hard_constraints
import comprehensive_factor_diagnosis as C

VERSION = 'E6e-v1'
COST, COST_HI = 8.0, 12.0
HOLD, EXEC_LAG, ADJUST = 5, 1, True
MAX_STOCK, MAX_IND_DEV = 0.01, 0.03
SEGS = list(PERIODS.keys())
E6_DIR = '/mnt/sda2/lichenchen/results/20260904_1051_E6_wide_scan'
E6B_DIR = '/mnt/sda2/lichenchen/results/20260904_1202_E6b_stack_sleeves'
E6D_DIR = '/mnt/sda2/lichenchen/results/20260906_0636_E6d_combination_taxonomy'

# ---- 因子 (§2.1) ----
FK, FT, FC = 'conditional_turnover', 'turnover_volatility_60d', 'CVR_20d'
FCR5, FCR20, FCVR1, FCI5 = 'cum_return_5d', 'cum_return_20d', 'intraday_cvr_1d', 'cum_intraday_ret_5d'
FACTORS = [FK, FT, FC, FCR5, FCR20, FCVR1, FCI5]
SHORT = {FK: 'K', FT: 'T', FC: 'C', FCR5: 'cr5', FCR20: 'cr20', FCVR1: 'cvr_1d', FCI5: 'ci5'}
_roles = pd.read_csv(os.path.join(E6_DIR, 'roles.csv')).set_index('factor')
HB = {f: (int(_roles.loc[f, 'worst_pooled']) == 5) for f in FACTORS}   # True = 高值坏

# ---- 分位映射 p->g (§2.2, 首次收益调用前锁定) ----
P2G = {20: 10, 25: 4, 30: 10, 35: 20, 40: 10, 45: 20, 50: 2, 55: 20,
       60: 10, 65: 20, 70: 10, 75: 4, 80: 10, 90: 10, 100: None}


def dgroups(high_bad, n, keep_g):
    return list(range(keep_g + 1, n + 1)) if high_bad else list(range(1, n - keep_g + 1))


def holds(cache, pool, n, keep_g, high_bad=True):
    return C.build_factor_strategy_holdings_cached(cache, pool, n, dgroups(high_bad, n, keep_g))


def mk(df):
    return (df.values == 1)


def pct_or(cache, high_bad):
    p = {d: s.rank(pct=True) for d, s in cache.items()}
    return p if high_bad else {d: 1.0 - s for d, s in p.items()}


def combine(caches, how='mean', complete=False):
    keys = set(caches[0])
    for c in caches[1:]: keys &= set(c)
    out = {}
    for d in keys:
        df = pd.concat([c[d] for c in caches], axis=1)
        if complete: df = df.dropna()
        if how == 'max':
            out[d] = df.max(axis=1)
        elif how == 'min':
            out[d] = df.min(axis=1)
        elif how == 'median':
            out[d] = df.median(axis=1)
        else:
            out[d] = df.mean(axis=1)
    return out


def keep_pct_mask(cache, pool, pctkeep, high_bad=True):
    """保留最好的 pctkeep%; 用锁定的 P2G 映射; 100 = bypass(全保留)"""
    if pctkeep >= 100: return (pool.values == 1)
    g = P2G[int(pctkeep)]
    return mk(holds(cache, pool, g, int(round(g * pctkeep / 100.0)), high_bad))


def drop_or(cache, pool, k, high_bad):
    """剔最差 1/k, 与 e6/e6b 逐字相同; 无值票也算剔除(§1.3)"""
    kept = holds(cache, pool, k, k - 1, high_bad)
    return (pool.values == 1) & ~mk(kept)


def msha(m):
    return hashlib.sha256(np.ascontiguousarray(np.asarray(m, dtype=np.uint8)).tobytes()).hexdigest()[:16]


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def is_bse(code):
    s = str(code); return s[:1] in ('4', '8') or s[:2] == '92'


def bench_industry_shares(clean_df, industry_df):
    cl = clean_df.values; ind = industry_df.values if industry_df is not None else None; shares = []
    for t in range(cl.shape[0]):
        idx = np.where(cl[t] == 1)[0]; tot = len(idx)
        if tot == 0 or ind is None: shares.append({}); continue
        vc = pd.Series(ind[t, idx]).value_counts(dropna=True); shares.append((vc / tot).to_dict())
    return shares


def assign_weights_dev(holdings, industry_df, shares, max_stock=MAX_STOCK, max_ind_dev=MAX_IND_DEV):
    """生产 DEV 权重 (逐字复制 e6/e6b/e6d), 只用于稠密参照与对账"""
    h = holdings.values; ind = industry_df.values if industry_df is not None else None
    T, N = h.shape; out = np.zeros((T, N))
    for t in range(T):
        sel = np.where(h[t] == 1)[0]; n = len(sel)
        if n == 0: continue
        w = np.full(n, min(1.0 / n, max_stock))
        if ind is not None and shares[t]:
            si = pd.Series(ind[t, sel])
            for indcode, grp in si.groupby(si).groups.items():
                gi = np.asarray(grp, dtype=int); cap = shares[t].get(indcode, 0.0) + max_ind_dev
                ssum = w[gi].sum()
                if ssum > cap: w[gi] *= cap / ssum
        out[t, sel] = w
    return pd.DataFrame(out, index=holdings.index, columns=holdings.columns)


def nw_stats(x, L=5):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    if n == 0: return float('nan'), float('nan'), float('nan'), 0
    mu = x.mean(); sd = x.std(ddof=1)
    naive = mu / (sd / np.sqrt(n)) if sd > 0 else float('nan')
    e = x - mu; S = (e @ e) / n
    for l in range(1, L + 1):
        w = 1.0 - l / (L + 1.0); S += 2.0 * w * (e[l:] @ e[:-l]) / n
    se = np.sqrt(S / n) if S > 0 else float('nan')
    nw = mu / se if (se == se and se > 0) else float('nan')
    return mu * 252 * 100.0, naive, nw, n


def score_hac(d, L=5):
    """缺口安全 HAC: 缺失日 score 记 0, Var(mean)=S/n^2"""
    d = np.asarray(d, float); obs = ~np.isnan(d); n = int(obs.sum())
    if n < 10: return np.nan, np.nan, n
    mu = float(np.nanmean(d)); e = np.where(obs, d - mu, 0.0)
    S = float(e @ e)
    for l in range(1, L + 1):
        if l < len(e): S += 2.0 * (1 - l / (L + 1.0)) * float(e[l:] @ e[:-l])
    se = np.sqrt(S) / n if S > 0 else np.nan
    return mu * 252 * 100.0, (mu / se if (se == se and se > 0) else np.nan), n


# ======================= 段上下文 =======================
class Seg(object):
    """一段的全部只读上下文"""
    pass


def load_segment(pname, factors=FACTORS, verbose=True):
    t0 = time.time()
    ps, pe = PERIODS[pname]
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
    specs[FCVR1] = {'name': FCVR1, 'func': lambda d, f, i: d['close'] / d['vwap'] - 1}

    S = Seg()
    S.name = pname; S.data = data; S.feats = feats; S.clean = clean; S.pool0 = pool0
    S.industry = industry; S.shares = shares; S.log_mcap = log_mcap; S.specs = specs
    S.T, S.Nfull = pool0.shape
    S.p0 = (pool0.values == 1)
    S.ccols = np.where(S.p0.any(axis=0))[0]
    S.Nc = len(S.ccols)
    S.dates = list(pool0.index)
    S.raw = {f: specs[f]['func'](data, feats, industry) for f in factors}
    S.neu = {f: C.precompute_neutralized_factor(S.raw[f], pool0, log_mcap) for f in factors}
    S.opct = {f: pct_or(S.neu[f], HB[f]) for f in factors}

    ind_v = industry.values
    codes, uniq = pd.factorize(pd.Series(ind_v[:, S.ccols].ravel()))
    S.icodes = codes.reshape(S.T, S.Nc)                     # -1 = 行业缺失
    S.G = int(S.icodes.max()) + 1
    code_of = {v: i for i, v in enumerate(uniq)}
    sh = np.zeros((S.T, S.G))
    for t in range(S.T):
        for k, v in shares[t].items():
            if k in code_of: sh[t, code_of[k]] = v
    S.cap = sh + MAX_IND_DEV                                # (T,G)
    dr = C.vwap_daily_return(data, ADJUST)
    S.bench = dr.where(clean == 1).mean(axis=1).values      # (T,)
    S.r0 = np.nan_to_num(dr.values[:, S.ccols], nan=0.0)    # (T,Nc)
    S.den = np.minimum(np.arange(1, S.T + 1), HOLD).astype(float)
    S.p0c = S.p0[:, S.ccols]                                # (T,Nc)
    if verbose:
        print('  [%s] pipeline %.0fs  T=%d  Nc=%d  pool0 日均 %.1f'
              % (pname, time.time() - t0, S.T, S.Nc, S.p0.sum(1).mean()), flush=True)
    return S


# ======================= DEV 权重 (稀疏) =======================
def dev_day(held, icode_row, cap_row, G):
    """一天的 DEV 权重; held = ccols 空间下的下标数组。与 assign_weights_dev 逐字等价。"""
    n = len(held)
    if n == 0: return np.empty(0)
    w = np.full(n, min(1.0 / n, MAX_STOCK))
    ic = icode_row[held]
    v = ic >= 0
    if v.any():
        gs = np.bincount(ic[v], weights=w[v], minlength=G)
        over = gs > cap_row
        if over.any():
            sc = np.ones(G)
            np.divide(cap_row, gs, out=sc, where=over)
            sc[~over] = 1.0
            w[v] = w[v] * sc[ic[v]]
    return w


def toc(S, m):
    """掩码统一到 ccols 空间; 构造器返回全市场宽度, 引擎要 ccols 宽度"""
    m = np.asarray(m)
    return m[:, S.ccols] if m.shape[1] == S.Nfull else m


def dev_from_mask(S, mask):
    """mask: (T,Nfull) 或 (T,Nc) bool -> (idx_list, val_list)"""
    mask_c = toc(S, mask)
    idx, val = [], []
    for t in range(S.T):
        h = np.where(mask_c[t])[0]
        idx.append(h)
        val.append(dev_day(h, S.icodes[t], S.cap[t], S.G))
    return idx, val


# ======================= 稀疏引擎 =======================
def sparse_pnl(S, idx, val, cost_bp=COST):
    """返回 gross, position, turnover, net (各 (T,))。与 compute_calendar_pnl 逐日等价。"""
    T, den, r0, bench = S.T, S.den, S.r0, S.bench
    wsum = np.fromiter((v.sum() if len(v) else 0.0 for v in val), float, T)
    cs = np.concatenate([[0.0], np.cumsum(wsum)])
    lo = np.maximum(np.arange(1, T + 1) - HOLD, 0)
    act_sum = (cs[1:] - cs[lo]) / den
    pos = np.zeros(T); pos[2:] = act_sum[:-2]

    port = np.zeros(T)
    for t in range(2, T):
        a = 0.0
        for s in range(max(0, t - 6), t - 1):
            if len(idx[s]): a += float(r0[t, idx[s]] @ val[s])
        port[t] = a / den[t - 2]

    turn = np.zeros(T)
    def actual_map(i):
        d = {}
        for s in range(max(0, i - HOLD + 1), i + 1):
            for c, v in zip(idx[s], val[s]): d[c] = d.get(c, 0.0) + v
        dn = den[i]
        return {c: v / dn for c, v in d.items()}
    hi = min(T, 10)
    for t in range(3, hi):
        a1, a0 = actual_map(t - 2), actual_map(t - 3)
        ks = set(a1) | set(a0)
        turn[t] = 0.5 * sum(abs(a1.get(k, 0.0) - a0.get(k, 0.0)) for k in ks)
    for t in range(hi, T):
        p, q = t - 2, t - 2 - HOLD
        ip, iq = idx[p], idx[q]
        if len(ip) == 0 and len(iq) == 0: continue
        ks = np.union1d(ip, iq)
        vp = np.zeros(len(ks)); vq = np.zeros(len(ks))
        if len(ip): vp[np.searchsorted(ks, ip)] = val[p]
        if len(iq): vq[np.searchsorted(ks, iq)] = val[q]
        turn[t] = 0.5 * float(np.abs(vp - vq).sum()) / HOLD
    gross = port - bench * pos
    cost = turn * (cost_bp / 1e4)
    return gross, pos, turn, gross - cost


def eval_mask(S, mask, cost_bp=COST):
    idx, val = dev_from_mask(S, mask)
    return sparse_pnl(S, idx, val, cost_bp)


# ======================= 稠密参照引擎 (对账用) =======================
def reference_pnl(S, mask, cost_bp=COST):
    full = np.zeros((S.T, S.Nfull), dtype=bool)
    full[:, S.ccols] = toc(S, mask)
    hold = pd.DataFrame(full.astype(float), index=S.pool0.index, columns=S.pool0.columns)
    w = assign_weights_dev(hold, S.industry, S.shares)
    pr = C.compute_calendar_pnl(w, S.data, S.clean, hold_days=HOLD, cost_bp_bilateral=cost_bp,
                                exec_lag=EXEC_LAG, adjust=ADJUST)
    return (pr['gross_excess_daily'].values, pr['daily_position'].values,
            pr['daily_turnover'].values, pr['net_excess_daily'].values)


def annualize(S, gross, pos, turn, net_mask=None):
    net8 = gross - turn * (COST / 1e4)
    net12 = gross - turn * (COST_HI / 1e4)
    m = ~np.isnan(net8) if net_mask is None else net_mask
    a8, _, t8, n = nw_stats(net8[m], 5)
    a12, _, t12, _ = nw_stats(net12[m], 5)
    ag, _, _, _ = nw_stats(gross[m], 5)
    return dict(net8_ann=a8, net12_ann=a12, gross_ann=ag, cost_ann=ag - a8, nw8=t8, nw12=t12,
                turn=252 * float(np.mean(turn[m])) if m.any() else np.nan,
                pos_mean=float(np.mean(pos[m])) if m.any() else np.nan,
                n=n, days_valid=int(m.sum()))


# ======================= 随机键 (采纳调整 1) =======================
_MIX_A = np.uint64(0xBF58476D1CE4E5B9)
_MIX_B = np.uint64(0x94D049BB133111EB)
_MIX_C = np.uint64(0x9E3779B97F4A7C15)


def _u64(b):
    return np.uint64(int.from_bytes(b[:8], 'big'))


def day_key(profile, seed, date_str):
    """SHA256(VERSION, profile, seed, date) -> u64 (每日一次, 非逐票)"""
    h = hashlib.sha256(('%s|%s|%d|%s' % (VERSION, profile, int(seed), date_str)).encode()).digest()
    return _u64(h)


def priorities(profile, seed, date_str, ticker_codes):
    """向量化 64 位混合器: 对 (day_key, ticker_code) 生成 [0,1) 优先级。
       只依赖票的身份码, 与列序/分片/并发无关。"""
    k = day_key(profile, seed, date_str)
    x = (np.asarray(ticker_codes, dtype=np.uint64) + np.uint64(1)) * _MIX_C + k
    x = (x ^ (x >> np.uint64(30))) * _MIX_A
    x = (x ^ (x >> np.uint64(27))) * _MIX_B
    x = x ^ (x >> np.uint64(31))
    return (x >> np.uint64(11)).astype(np.float64) * (1.0 / 9007199254740992.0)


# ======================= P114 核描述符 (§2.2) =======================
DEPTHS = [20, 25, 30, 35, 40, 50]
AB_P54 = [(45, 45), (50, 50), (55, 55), (60, 60), (65, 65), (70, 70)]
AB_ALLOC = [(40, 50), (50, 40), (40, 60), (60, 40), (50, 60), (60, 50), (70, 35), (35, 70),
            (80, 30), (30, 80), (90, 30), (30, 90), (80, 50), (50, 80), (90, 50), (50, 90)]
AB_REV = [(50, 50), (70, 35), (60, 50)]
AB_NR = [(50, 50), (70, 35)]
DEP_FAMS = ['KT_dep', 'CT_dep', 'K_gate_TC']
MEAN_FAMS = {'KT_mean': [FK, FT], 'TC_mean': [FT, FC], 'KTC_mean': [FK, FT, FC]}
SINGLE_FAMS = {'T': FT, 'K': FK, 'C': FC}


def core_descriptors():
    """P114 + 双胞胎。返回 list[dict]，字段进 config_registry.csv。"""
    out = []
    def add(cid, fam, kind, **kw):
        d = dict(core_id=cid, family=fam, kind=kind, set='P54', variant='main',
                 f1='', f2='', f3='', s=np.nan, a=np.nan, b=np.nan)
        d.update(kw); out.append(d)
    for fam, f in SINGLE_FAMS.items():
        for s in DEPTHS: add('%s@%d' % (fam, s), fam, 'single', f1=f, s=s)
    for fam, fs in MEAN_FAMS.items():
        for s in DEPTHS:
            add('%s@%d' % (fam, s), fam, 'mean', s=s,
                **{('f%d' % (i + 1)): x for i, x in enumerate(fs)})
    for fam in DEP_FAMS:
        for (a, b) in AB_P54: add('%s(%d,%d)' % (fam, a, b), fam, 'dep', a=a, b=b)
    for fam in DEP_FAMS:
        for (a, b) in AB_ALLOC:
            add('%s(%d,%d)' % (fam, a, b), fam, 'dep', a=a, b=b, set='alloc48')
    for fam, (x, y) in (('T_gate_K', (FT, FK)), ('T_gate_C', (FT, FC))):
        for (a, b) in AB_REV:
            add('%s(%d,%d)' % (fam, a, b), fam, 'dep_rev', a=a, b=b, set='guard12', f1=x, f2=y)
    for fam in DEP_FAMS:
        for (a, b) in AB_NR:
            add('%s_nr(%d,%d)' % (fam, a, b), fam + '_nr', 'dep_nr', a=a, b=b, set='guard12')
    return out


def twin_descriptors(cores):
    """complete_components (只对含复合的 P54) + rank_budget_diagnostic (全 P114)"""
    out = []
    for d in cores:
        if d['set'] == 'P54' and d['family'] in ('KT_mean', 'TC_mean'):
            e = dict(d); e['core_id'] = d['core_id'] + '#cc'; e['variant'] = 'complete_components'
            out.append(e)
        e = dict(d); e['core_id'] = d['core_id'] + '#rb'; e['variant'] = 'rank_budget'
        out.append(e)
    return out


def _s1_frame(S, mask):
    return pd.DataFrame(np.asarray(mask).astype(float), index=S.pool0.index, columns=S.pool0.columns)


def _rank_budget_mask(S, score_cache, pool, pctkeep, _cp=None):
    """诊断双胞胎: 同分数排序 + 稳定 tie 键, 恰好保留 ceil(s*n_valid) 只"""
    if _cp is None: _cp = col_positions(S)
    m = np.zeros((S.T, S.Nfull), bool)
    cols = np.asarray(S.pool0.columns)
    pv = (pool.values == 1)
    for i, d in enumerate(S.dates):
        s = score_cache.get(d)
        if s is None: continue
        idx = np.asarray(s.index)
        keep_in = np.isin(idx, cols[pv[i]])
        s2 = s[keep_in]
        if len(s2) < 6: continue
        k = int(np.ceil(len(s2) * pctkeep / 100.0))
        order = np.lexsort((np.asarray(s2.index), s2.values))   # 分数升序, 并列按 ticker 稳定
        sel = np.asarray(s2.index)[order[:k]]
        m[i, [_cp[x] for x in sel]] = True
    return m


def build_core(S, d):
    """返回 (mask 全宽 bool, score_cache dict{date:Series 低=好}, cand_pool DataFrame)
       score_cache = 该核末级排序分, 供 coretrim_matchN 与条件豁免用 (§3.1/§2.4)"""
    kind, var = d['kind'], d.get('variant', 'main')
    if kind == 'single':
        sc = S.opct[d['f1']]
        pool = S.pool0
        m = (_rank_budget_mask(S, sc, pool, d['s']) if var == 'rank_budget'
             else keep_pct_mask(sc, pool, d['s']))
        return m, sc, pool
    if kind == 'mean':
        fs = [d['f1'], d['f2']] + ([d['f3']] if d['f3'] else [])
        comp = d['family'] == 'KTC_mean' or var == 'complete_components'
        sc = combine([S.opct[f] for f in fs], 'mean', complete=comp)
        pool = S.pool0
        m = (_rank_budget_mask(S, sc, pool, d['s']) if var == 'rank_budget'
             else keep_pct_mask(sc, pool, d['s']))
        return m, sc, pool
    fam, a, b = d['family'], int(d['a']), int(d['b'])
    if kind == 'dep_rev':
        X, Ys = d['f1'], [d['f2']]
    elif fam.startswith('KT_dep'):
        X, Ys = FK, [FT]
    elif fam.startswith('CT_dep'):
        X, Ys = FC, [FT]
    else:
        X, Ys = FK, [FT, FC]
    s1m = keep_pct_mask(S.opct[X], S.pool0, a)
    S1 = _s1_frame(S, s1m)
    if kind == 'dep_nr':
        # 沿 pool0 中性化值, 只把排序范围换成 S1 (§2.2 结构守卫)
        cols = np.asarray(S.pool0.columns)
        parts = []
        for y in Ys:
            sub = {}
            for i, dd in enumerate(S.dates):
                s = S.neu[y].get(dd)
                if s is None: continue
                v = s[np.isin(np.asarray(s.index), cols[s1m[i]])]
                if len(v) >= 6: sub[dd] = v
            parts.append(pct_or(sub, HB[y]))
    else:
        parts = [pct_or(C.precompute_neutralized_factor(S.raw[y], S1, S.log_mcap), HB[y]) for y in Ys]
    sc = parts[0] if len(parts) == 1 else combine(parts, 'mean')
    m = (_rank_budget_mask(S, sc, S1, b) if var == 'rank_budget' else keep_pct_mask(sc, S1, b))
    return m, sc, S1


# ======================= 否决描述符 (§2.3/§2.4) =======================
VF6 = [FK, FC, FCR5, FCR20, FCVR1, FCI5]


def hard_veto_descriptors():
    out = []
    for f in VF6:
        for k in (5, 10):
            out.append(dict(veto_id='%s:k%d' % (SHORT[f], k), kind='hard', legs=[(f, k)]))
    for kc in (5, 10):
        for kb in (5, 10):
            out.append(dict(veto_id='C:k%d+cr5:k%d' % (kc, kb), kind='hard', legs=[(FC, kc), (FCR5, kb)]))
    for a, b in ((FCVR1, FCR5), (FCI5, FCR5), (FC, FCR20)):
        out.append(dict(veto_id='%s:k10+%s:k10' % (SHORT[a], SHORT[b]), kind='hard',
                        legs=[(a, 10), (b, 10)]))
    return out


def composite_veto_descriptors():
    out = []
    for (x, y) in ((FC, FCR5), (FCVR1, FCR5), (FC, FCR20)):
        for how in ('mean', 'max', 'min'):
            for k in (5, 10):
                out.append(dict(veto_id='cmp_%s(%s,%s):k%d' % (how, SHORT[x], SHORT[y], k),
                                kind='composite', legs=[(x, k), (y, k)], how=how, k=k))
    return out


SOFT_STARTS = ['C:k5', 'cr5:k10', 'K:k10', 'C:k10+cr5:k10', 'C:k5+cr5:k10', 'C:k10+cr20:k10']
EXEMPT_STARTS = ['C:k5', 'cr5:k10', 'C:k10+cr5:k10', 'C:k5+cr5:k10']


def exemption_veto_descriptors():
    return [dict(veto_id='%s^ex%d' % (s, q), kind='exempt', start=s, q=q)
            for s in EXEMPT_STARTS for q in (10, 25)]


def soft_descriptors():
    out = []
    for s in SOFT_STARTS:
        for lam in (0.25, 0.5, 0.75, 1.0):
            out.append(dict(veto_id='%s~WS%.2f' % (s, lam), kind='soft', start=s, mode='WS', lam=lam))
        for lam in (0.25, 0.5, 0.75):
            out.append(dict(veto_id='%s~WB%.2f' % (s, lam), kind='soft', start=s, mode='WB', lam=lam))
    return out


def tox_masks(S):
    """全部单腿毒尾 (f,k) -> (T,Nfull) bool; 无值票算剔除(§1.3)"""
    return {(f, k): drop_or(S.neu[f], S.pool0, k, HB[f]) for f in VF6 for k in (5, 10)}


def unscorable_mask(S, f):
    """pool0 内该因子无中性化值的 (日,票)"""
    m = np.zeros((S.T, S.Nfull), bool)
    cols = np.asarray(S.pool0.columns)
    for i, d in enumerate(S.dates):
        pm = S.p0[i]
        s = S.neu[f].get(d)
        if s is None:
            m[i] = pm
        else:
            has = np.isin(cols, np.asarray(s.index))
            m[i] = pm & ~has
    return m


def veto_drop(S, vd, tox, unsc, core_mask=None, core_score=None, cand_pool=None, extreme=None, colpos=None):
    """返回 (drop_mask 全宽 bool, info dict)。core_* 只对 exempt 需要。"""
    if colpos is None: colpos = col_positions(S)
    kind = vd["kind"]
    if kind == 'hard':
        d = np.zeros((S.T, S.Nfull), bool)
        for (f, k) in vd['legs']: d |= tox[(f, k)]
        return d, {}
    if kind == 'composite':
        xs = [S.opct[f] for (f, _) in vd['legs']]
        comp = combine(xs, vd['how'], complete=True)
        kept = holds(comp, S.pool0, vd['k'], vd['k'] - 1, True)
        return (S.p0 & ~mk(kept)), {}
    if kind == 'exempt':
        base = parse_start(S, vd['start'], tox)
        q = vd['q']
        ex = np.zeros((S.T, S.Nfull), bool)
        cols = np.asarray(S.pool0.columns)
        # 极端毒 (任一分量 pool0 坏向 pct >= 0.95) 不豁免; extreme 由调用方预算好, 不在此重复
        hard_no = np.zeros((S.T, S.Nfull), bool)
        for f in start_factors(vd['start']):
            hard_no |= extreme[f]
        for i, dd in enumerate(S.dates):
            sc = core_score.get(dd)
            if sc is None: continue
            inc = np.isin(np.asarray(sc.index), cols[core_mask[i]])
            s2 = sc[inc]
            if len(s2) < 6: continue
            k = max(1, int(np.floor(len(s2) * q / 100.0)))
            order = np.lexsort((np.asarray(s2.index), s2.values))
            best = np.asarray(s2.index)[order[:k]]
            ex[i, [colpos[x] for x in best]] = True
        return (base & ~(ex & ~hard_no)), dict(exempted=int((base & ex & ~hard_no).sum()))
    raise ValueError(vd['kind'])


def start_factors(start):
    fs = []
    for leg in start.split('+'):
        nm = leg.split(':')[0]
        fs.append([f for f, s in SHORT.items() if s == nm][0])
    return fs


def parse_start(S, start, tox):
    d = np.zeros((S.T, S.Nfull), bool)
    for leg in start.split('+'):
        nm, kk = leg.split(':')
        f = [f for f, s in SHORT.items() if s == nm][0]
        d |= tox[(f, int(kk[1:]))]
    return d


def col_positions(S):
    """ticker -> 全宽列下标; 不依赖列名有序"""
    return {c: i for i, c in enumerate(S.pool0.columns)}


def extreme_masks(S, thr=0.95):
    """任一分量 pool0 坏向 pct >= thr 的 (日,票) -> 不予豁免 (§2.4)"""
    cp = col_positions(S)
    out = {}
    for f in VF6:
        m = np.zeros((S.T, S.Nfull), bool)
        for i, d in enumerate(S.dates):
            s = S.opct[f].get(d)
            if s is None: continue
            bad = np.asarray(s.index)[s.values >= thr]
            if len(bad): m[i, [cp[x] for x in bad]] = True
        out[f] = m
    return out
