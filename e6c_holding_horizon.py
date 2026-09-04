#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# E6c 持有期 1..20 日 x 18 配置(+pool0_DEV) + 事件时间剖面 + 日龄桥 + 统计诊断. 只出表, 不淘汰.
# 用法: python e6c_holding_horizon.py --contract --out <dir>
#       python e6c_holding_horizon.py --period <seg> --out <dir>
#       python e6c_holding_horizon.py --merge --out <dir>
# 执行端按用户 2026-09-04 确认的 5 处放松执行(见 REPORT):
#   1) E6/E6b 日序列逐日比 = 诊断列(非硬闸); 硬闸只有 72 个 h5 锚点 TOL 0.02
#   2) M_mean2 / M_mean3_v2 的二分组(_bin)与十分位(_dec)两种构造都算, 锚点各对各自来源
#   3) M 视图 best-effort; 失败只记 limit_register
#   4) 会计恒等式 atol 1e-9, 失败只记 check.csv 不中止
#   5) 玩具测试分阻断/非阻断两档
import sys, os, io, json, time, hashlib, argparse, warnings
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import define_i11_signal, build_observation_pool, apply_hard_constraints
import comprehensive_factor_diagnosis as C

warnings.filterwarnings('ignore')
COST, COST12 = 8.0, 12.0
TOL_ANCHOR, ATOL_ID = 0.02, 1e-9
HS = list(range(1, 21)); HMAX = 20; B_WARM = 60; MATURE_START = B_WARM + HMAX + 1   # 81
SEGS = list(PERIODS.keys())
PC = '/mnt/sda2/lichenchen/code/project_core'
RES = '/mnt/sda2/lichenchen/results'
E6 = RES + '/20260904_1051_E6_wide_scan'
E6B = RES + '/20260904_1202_E6b_stack_sleeves'
E2D = RES + '/20260903_0935_E2_decomposition/decomp.csv'
F_COND, F_TVOL, F_CR20, F_CR5, F_CVR, F_CVR1 = ('conditional_turnover', 'turnover_volatility_60d',
                                                'cum_return_20d', 'cum_return_5d', 'CVR_20d', 'intraday_cvr_1d')

# --------------------------------------------------------------- verbatim helpers (E6b)
def is_bse(code):
    s = str(code); return s[:1] in ('4', '8') or s[:2] == '92'

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

def pct_cache(cache): return {d: s.rank(pct=True) for d, s in cache.items()}

def combine(caches, how):
    keys = set(caches[0])
    for c in caches[1:]: keys &= set(c)
    out = {}
    for d in keys:
        df = pd.concat([c[d] for c in caches], axis=1)
        out[d] = df.max(axis=1) if how == 'max' else (df.median(axis=1) if how == 'median' else df.mean(axis=1))
    return out

def bench_industry_shares(clean_df, industry_df):
    cl = clean_df.values; ind = industry_df.values if industry_df is not None else None; shares = []
    for t in range(cl.shape[0]):
        idx = np.where(cl[t] == 1)[0]; tot = len(idx)
        if tot == 0 or ind is None: shares.append({}); continue
        vc = pd.Series(ind[t, idx]).value_counts(dropna=True); shares.append((vc / tot).to_dict())
    return shares

def assign_weights_dev(holdings, industry_df, shares, max_stock=0.01, max_ind_dev=0.03):
    h = holdings.values; ind = industry_df.values if industry_df is not None else None
    T, N = h.shape; out = np.zeros((T, N))
    for t in range(T):
        sel = np.where(h[t] == 1)[0]; n = len(sel)
        if n == 0: continue
        w = np.full(n, min(1.0 / n, max_stock))
        if ind is not None and shares[t]:
            si = pd.Series(ind[t, sel])
            for indcode, grp in si.groupby(si).groups.items():
                gi = np.asarray(grp, dtype=int); cap = shares[t].get(indcode, 0.0) + max_ind_dev; ssum = w[gi].sum()
                if ssum > cap: w[gi] *= cap / ssum
        out[t, sel] = w
    return pd.DataFrame(out, index=holdings.index, columns=holdings.columns)

def drop_mask(neu_f, pool0, k=2):
    kept = C.build_factor_strategy_holdings_cached(neu_f, pool0, k, [k])
    return (pool0.values == 1) & ~(kept.values == 1)

def keep_mask(comp, pool0, keep):
    m = keep // 10
    return (C.build_factor_strategy_holdings_cached(comp, pool0, 10, list(range(m + 1, 11))).values == 1)

# --------------------------------------------------------------- 统计
def score_hac(x, L):
    """带缺口序列的 NW: m 为有效指示, 缺失处 score 显式 0. 返回 (ann%, t, n_obs)."""
    x = np.asarray(x, float); m = (~np.isnan(x)).astype(float); nm = m.sum()
    if nm < 2: return float('nan'), float('nan'), int(nm)
    xf = np.where(np.isnan(x), 0.0, x); mu = xf.sum() / nm
    u = m * (xf - mu)
    S = u @ u
    for l in range(1, int(L) + 1):
        if l >= len(u): break
        S += 2.0 * (1.0 - l / (L + 1.0)) * (u[l:] @ u[:-l])
    var = S / (nm ** 2)
    t = mu / np.sqrt(var) if var > 0 else float('nan')
    return mu * 252 * 100.0, t, int(nm)

def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def sha_arr(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()[:16]

# --------------------------------------------------------------- 配置
# canonical -> (锚点来源, 该来源里的名字);  None = 无锚点
ANCHOR_MAP = {
    'A4b': ('E6', 'A4b'), 'M_mean3_v2_bin': ('E6', 'M_mean3_v2'), 'M_union3_v2': ('E6', 'M_union3_v2'),
    'A4b_CVRv5': ('E6', 'A4b_CVRv5'), 'M_mean3_v2_CVRv5': ('E6', 'M_mean3_v2_CVRv5'),
    'M_union3_v2_CVRv5': ('E6', 'M_union3_v2_CVRv5'), 'M_mean2_bin': ('E6', 'M_mean2'),
    'M_mean3_v2_dec': ('E6b', 'M_mean3_v2'), 'M_mean2_dec': ('E6b', 'M_mean2'),
    'M_mean2@keep30': ('E6b', 'M_mean2@keep30'), 'M_mean2@keep20': ('E6b', 'M_mean2@keep20'),
    'A4b|CVR_20d:k10': ('E6b', 'A4b|CVR_20d:k10'), 'A4b|cum_return_5d:k10': ('E6b', 'A4b|cum_return_5d:k10'),
    'A4b|CVR_20d:k10+cum_return_5d:k10': ('E6b', 'A4b|CVR_20d:k10+cum_return_5d:k10'),
    'M_mean2@keep30|CVR_20d:k10': ('E6b', 'M_mean2@keep30|CVR_20d:k10'),
    'M_mean2@keep30|cum_return_5d:k10': ('E6b', 'M_mean2@keep30|cum_return_5d:k10'),
    'M_mean2@keep30|CVR_20d:k10+cum_return_5d:k10': ('E6b', 'M_mean2@keep30|CVR_20d:k10+cum_return_5d:k10'),
    'A4b|intraday_cvr_1d:k10': ('E6b', 'A4b|intraday_cvr_1d:k10'),
}
# 固定父子边 (§2D)
EDGES = [('A4b', 'A4b_CVRv5'), ('M_mean3_v2_bin', 'M_mean3_v2_CVRv5'), ('M_union3_v2', 'M_union3_v2_CVRv5'),
         ('A4b', 'A4b|intraday_cvr_1d:k10'),
         ('A4b', 'A4b|CVR_20d:k10'), ('A4b', 'A4b|cum_return_5d:k10'),
         ('A4b', 'A4b|CVR_20d:k10+cum_return_5d:k10'),
         ('A4b|CVR_20d:k10', 'A4b|CVR_20d:k10+cum_return_5d:k10'),
         ('A4b|cum_return_5d:k10', 'A4b|CVR_20d:k10+cum_return_5d:k10'),
         ('M_mean2@keep30', 'M_mean2@keep30|CVR_20d:k10'), ('M_mean2@keep30', 'M_mean2@keep30|cum_return_5d:k10'),
         ('M_mean2@keep30', 'M_mean2@keep30|CVR_20d:k10+cum_return_5d:k10'),
         ('M_mean2@keep30|CVR_20d:k10', 'M_mean2@keep30|CVR_20d:k10+cum_return_5d:k10'),
         ('M_mean2@keep30|cum_return_5d:k10', 'M_mean2@keep30|CVR_20d:k10+cum_return_5d:k10')]
SERVICE_REF = ('A4b_CVRv5', 5)

def build_masks(data, feats, pool0, log_mcap, industry, P):
    p0 = (pool0.values == 1)
    need = [F_COND, F_TVOL, F_CR20, F_CR5, F_CVR, F_CVR1]
    specs = {s['name']: s for s in C.get_default_factor_specs()}
    specs[F_CVR1] = {'name': F_CVR1, 'func': lambda d, f, i: d['close'] / d['vwap'] - 1}
    raw = {n: specs[n]['func'](data, feats, industry) for n in need}
    neu = {n: C.precompute_neutralized_factor(raw[n], pool0, log_mcap) for n in need}
    pct = {n: pct_cache(neu[n]) for n in need}
    P('  neutralized %d factors' % len(neu))
    hc = C.build_factor_strategy_holdings_cached(neu[F_COND], pool0, 2, [2])
    m_a4b = (C.build_factor_strategy_holdings_cached(
        C.precompute_neutralized_factor(raw[F_TVOL], hc, log_mcap), hc, 2, [2]).values == 1)
    comp2 = combine([pct[F_COND], pct[F_TVOL]], 'mean')
    comp3 = combine([pct[F_COND], pct[F_TVOL], pct[F_CR20]], 'mean')
    m2b = (C.build_factor_strategy_holdings_cached(comp2, pool0, 2, [2]).values == 1)
    m3b = (C.build_factor_strategy_holdings_cached(comp3, pool0, 2, [2]).values == 1)
    m2d = keep_mask(comp2, pool0, 50); m3d = keep_mask(comp3, pool0, 50)
    k30 = keep_mask(comp2, pool0, 30); k20 = keep_mask(comp2, pool0, 20)
    dc, dt, dr = drop_mask(neu[F_COND], pool0), drop_mask(neu[F_TVOL], pool0), drop_mask(neu[F_CR20], pool0)
    m_u3 = p0 & ((dc.astype(int) + dt.astype(int) + dr.astype(int)) == 0)
    tox = {}
    for f, k in [(F_CVR, 5), (F_CVR, 10), (F_CR5, 10), (F_CVR1, 10)]:
        kept = C.build_factor_strategy_holdings_cached(neu[f], pool0, k, [k])
        tox[(f, k)] = p0 & ~(kept.values == 1)
    M = {
        'A4b': m_a4b, 'M_mean3_v2_bin': m3b, 'M_mean3_v2_dec': m3d, 'M_union3_v2': m_u3,
        'A4b_CVRv5': m_a4b & ~tox[(F_CVR, 5)], 'M_mean3_v2_CVRv5': m3b & ~tox[(F_CVR, 5)],
        'M_union3_v2_CVRv5': m_u3 & ~tox[(F_CVR, 5)], 'M_mean2_bin': m2b, 'M_mean2_dec': m2d,
        'M_mean2@keep30': k30, 'M_mean2@keep20': k20,
        'A4b|CVR_20d:k10': m_a4b & ~tox[(F_CVR, 10)], 'A4b|cum_return_5d:k10': m_a4b & ~tox[(F_CR5, 10)],
        'A4b|CVR_20d:k10+cum_return_5d:k10': m_a4b & ~tox[(F_CVR, 10)] & ~tox[(F_CR5, 10)],
        'M_mean2@keep30|CVR_20d:k10': k30 & ~tox[(F_CVR, 10)],
        'M_mean2@keep30|cum_return_5d:k10': k30 & ~tox[(F_CR5, 10)],
        'M_mean2@keep30|CVR_20d:k10+cum_return_5d:k10': k30 & ~tox[(F_CVR, 10)] & ~tox[(F_CR5, 10)],
        'A4b|intraday_cvr_1d:k10': m_a4b & ~tox[(F_CVR1, 10)], 'pool0_DEV': p0,
    }
    extra = {'bin_vs_dec_M_mean2': int((m2b != m2d).sum()), 'bin_vs_dec_M_mean3_v2': int((m3b != m3d).sum()),
             'tox_CVR5': tox[(F_CVR, 5)], 'tox_CVR10': tox[(F_CVR, 10)], 'tox_cr5_10': tox[(F_CR5, 10)]}
    return M, extra

# --------------------------------------------------------------- 单段
def run_period(pname, OUT):
    ps, pe = PERIODS[pname]; t0 = time.time()
    log = io.open(os.path.join(OUT, 'log_%s.txt' % pname), 'w', encoding='utf-8', newline='\n')
    def P(*a):
        s = ' '.join(str(x) for x in a); print(s, flush=True); log.write(s + '\n'); log.flush()
    P('PERIOD %s %s..%s' % (pname, ps, pe))
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
    if industry is not None: industry = industry.reindex(index=close.index, columns=close.columns)
    shares = bench_industry_shares(clean, industry)
    idx = pool0.index; cols = pool0.columns; T = len(idx)
    P('  pipeline %.0fs  T=%d  pool0 avg=%.1f' % (time.time() - t0, T, float((pool0.values == 1).sum(axis=1).mean())))

    M, extra = build_masks(data, feats, pool0, log_mcap, industry, P)
    rdaily = C.vwap_daily_return(data, adjust=True).reindex(index=idx, columns=cols)
    rt = np.nan_to_num(rdaily.values, nan=0.0)                      # r̃: NaN -> 0 (与引擎同构)
    bench = rdaily.where(clean.values == 1).mean(axis=1).values      # clean 等权基准 (同引擎)
    W = {}; cfg_rows = []
    for cfg, m in M.items():
        hold = pd.DataFrame(m.astype(float), index=idx, columns=cols)
        w = assign_weights_dev(hold, industry, shares)
        W[cfg] = w.values
        cfg_rows.append(dict(period=pname, cfg=cfg, mask_sha=sha_arr(m), w_sha=sha_arr(np.round(w.values, 12)),
                             n_target_mean=float((m.sum(axis=1))[m.sum(axis=1) > 0].mean()),
                             days_nonempty=int((m.sum(axis=1) > 0).sum())))
    pd.DataFrame(cfg_rows).to_csv(os.path.join(OUT, 'config_registry_%s.csv' % pname), index=False)
    P('  masks+W %d cfgs %.0fs  bin_vs_dec: M_mean2=%d M_mean3=%d'
      % (len(M), time.time() - t0, extra['bin_vs_dec_M_mean2'], extra['bin_vs_dec_M_mean3_v2']))

    # ---- K_{t,j}: 与 H 无关, 一次算 20 个 lag ----
    Kall = {}
    for cfg, w in W.items():
        Kj = np.full((T, HMAX), np.nan)
        for j in range(1, HMAX + 1):
            if T - j - 1 <= 0: continue
            ws = w[:T - j - 1]                                    # W_{t-j-1}, 对齐到 t=j+1..T-1
            Kj[j + 1:, j - 1] = (ws * rt[j + 1:]).sum(axis=1) - bench[j + 1:] * ws.sum(axis=1)
        Kall[cfg] = Kj
    P('  K bridge %.0fs' % (time.time() - t0))

    # ---- 20 个 H 的引擎调用 + 日账本 ----
    ledger = []; sf = []; bridge = []
    ones_cum = np.arange(1, T + 1)
    for cfg, w in W.items():
        wdf = pd.DataFrame(w, index=idx, columns=cols)
        S = np.vstack([np.zeros((1, w.shape[1])), np.cumsum(w, axis=0)])   # S[k] = sum of first k rows
        for H in HS:
            pr = C.compute_calendar_pnl(wdf, data, clean, hold_days=H, cost_bp_bilateral=COST)
            net8 = pr['net_excess_daily'].values; gross = pr['gross_excess_daily'].values
            pos = pr['daily_position'].values; turn = pr['daily_turnover'].values
            cost8 = turn * COST / 1e4; net12 = net8 - turn * (COST12 - COST) / 1e4
            # ah 重构 (cumsum): ah_t = (S[t-1] - S[t-1-H]) / min(H, t-1)
            hi = np.clip(np.arange(T) - 1, 0, T); lo = np.clip(np.arange(T) - 1 - H, 0, T)
            ah = (S[hi] - S[lo])
            den = np.minimum(H, np.maximum(np.arange(T) - 1, 0)).astype(float); den[den == 0] = np.nan
            ah = ah / den[:, None]
            ah = np.nan_to_num(ah, nan=0.0)
            pos_rec = ah.sum(axis=1)
            n_act = (ah > 0).sum(axis=1)
            with np.errstate(divide='ignore', invalid='ignore'):
                sh = np.where(pos_rec[:, None] > 1e-12, ah / pos_rec[:, None], 0.0)
                hhi = (sh ** 2).sum(axis=1); eff = np.where(hhi > 0, 1.0 / hhi, np.nan)
                pug = np.where(pos > 1e-12, gross / pos, np.nan); pun = np.where(pos > 1e-12, net8 / pos, np.nan)
            pos_err = float(np.nanmax(np.abs(pos_rec - pos)))
            ntar = (M[cfg].sum(axis=1)).astype(float)
            ledger.append(pd.DataFrame(dict(period=pname, date=idx, cfg=cfg, hold=H,
                port=pr['port_daily'].values, bench=pr['bench_daily'].values, position=pos, turnover=turn,
                cost8=cost8, gross=gross, net8=net8, net12=net12, n_target=ntar, n_actual=n_act,
                hhi_actual=hhi, effective_n=eff, pu_gross=pug, pu_net=pun)))
            # 桥恒等式 (common_mature)
            mm = np.arange(T) >= MATURE_START
            gk = Kall[cfg][:, :H].mean(axis=1)
            bridge_err = float(np.nanmax(np.abs(gk[mm] - gross[mm]))) if mm.any() else np.nan
            for rng, msk in (('legacy_all', np.ones(T, bool)), ('common_mature', mm)):
                a_g, _, _, _ = nw_stats(gross[msk], L=max(H, 1)); a_n, _, t_n, n_n = nw_stats(net8[msk], L=max(H, 1))
                a_12, _, t_12, _ = nw_stats(net12[msk], L=max(H, 1)); a_c, _, _, _ = nw_stats(cost8[msk], L=max(H, 1))
                _, _, t5, _ = nw_stats(net8[msk], L=5)
                sf.append(dict(period=pname, cfg=cfg, hold=H, scope=rng, gross_ann=a_g, net8_ann=a_n,
                    net12_ann=a_12, cost_ann=a_c, nw_net8=t_n, nw_net12=t_12, nw5=t5, n=n_n,
                    turn_eval=252 * np.nanmean(turn[msk]), pos_mean=np.nanmean(pos[msk]),
                    pos_mean_active=np.nanmean(pos[msk][pos[msk] > 1e-12]) if (pos[msk] > 1e-12).any() else np.nan,
                    zero_pos_days=int((pos[msk] <= 1e-12).sum()),
                    zero_position_cost=float(np.nansum(cost8[msk][pos[msk] <= 1e-12])),
                    n_target=np.nanmean(ntar[msk]), n_actual=np.nanmean(n_act[msk]),
                    effective_n=np.nanmean(eff[msk]), vol_daily=np.nanstd(net8[msk]),
                    capital_day_net=25200 * np.nansum(net8[msk]) / np.nansum(pos[msk]) if np.nansum(pos[msk]) > 0 else np.nan,
                    turn_annual_engine=float(pr['turnover_annual']), pos_recon_err=pos_err, bridge_err=bridge_err))
        P('  [cfg] %-46s %.0fs' % (cfg, time.time() - t0))
    pd.concat(ledger, ignore_index=True).to_parquet(os.path.join(OUT, 'daily_%s.parquet' % pname))
    pd.DataFrame(sf).to_csv(os.path.join(OUT, 'sf_%s.csv' % pname), index=False)
    # K 落盘 (供 merge 做三项分解)
    kb = []
    for cfg, Kj in Kall.items():
        d = pd.DataFrame(Kj, index=idx, columns=['K%d' % j for j in range(1, HMAX + 1)])
        d.insert(0, 'cfg', cfg); d.insert(0, 'period', pname); d = d.reset_index().rename(columns={'index': 'date'})
        kb.append(d)
    pd.concat(kb, ignore_index=True).to_parquet(os.path.join(OUT, 'bridge_%s.parquet' % pname))
    P('  ledger+bridge written %.0fs' % (time.time() - t0))

    # ---- 事件时间剖面 (E 视图) + 触发日龄 ----
    sets = {k: v for k, v in M.items()}
    sets['pool0'] = (pool0.values == 1)
    for pa, ch in EDGES:
        sets['removed:%s->%s' % (pa, ch)] = M[pa] & ~M[ch]
    sets['pool0&tox_CVR5'] = sets['pool0'] & extra['tox_CVR5']
    sets['pool0&tox_cr5_10'] = sets['pool0'] & extra['tox_cr5_10']
    valid_T = (np.arange(T) >= B_WARM) & (np.arange(T) + HMAX + 1 <= T - 1)
    prof = []
    for sid, sm in sets.items():
        nT = sm.sum(axis=1).astype(float)
        a = np.where(nT[:, None] > 0, sm / np.where(nT[:, None] == 0, 1, nT[:, None]), 0.0)
        for j in range(1, HMAX + 1):
            fut = np.zeros_like(rt); fut[:T - (1 + j)] = rt[1 + j:]
            v = (a * fut).sum(axis=1)
            ok = valid_T & (nT > 0)
            prof.append(dict(period=pname, set_id=sid, j=j, mean=float(np.nanmean(v[ok])) if ok.any() else np.nan,
                             n_cohort=int(ok.sum()), n_mean=float(nT[ok].mean()) if ok.any() else np.nan))
    pd.DataFrame(prof).to_csv(os.path.join(OUT, 'profile_%s.csv' % pname), index=False)
    # 触发日龄 1..5
    sig = (signal.reindex(index=idx, columns=cols).fillna(0).values > 0)
    age = np.full((T, len(cols)), 0, dtype=np.int8)
    for lag in range(5, 0, -1):
        s = np.zeros_like(sig); s[lag:] = sig[:T - lag]
        age = np.where(s, lag, age)
    arows = []
    for sid in ['A4b', 'A4b_CVRv5', 'M_mean2@keep30', 'pool0']:
        sm = sets[sid]
        for ag in (1, 2, 3, 4, 5):
            sel = sm & (age == ag); n = sel.sum(axis=1).astype(float)
            arows.append(dict(period=pname, set_id=sid, age=ag, share=float(n[valid_T].sum() / max(sm.sum(axis=1)[valid_T].sum(), 1)),
                              n_mean=float(n[valid_T].mean())))
    pd.DataFrame(arows).to_csv(os.path.join(OUT, 'age_%s.csv' % pname), index=False)
    P('  profiles+age %.0fs' % (time.time() - t0))

    # ---- 可成交性暴露 (只计数) ----
    er = []
    lu = data.get('limit_up'); ld = data.get('limit_down'); iso = data.get('is_open')
    fb = data.get('flag_buy'); fs = data.get('flag_sell')
    def al(x): return None if x is None else x.reindex(index=idx, columns=cols).values
    lu, ld, iso, fb, fs, cl = al(lu), al(ld), al(iso), al(fb), al(fs), close.reindex(index=idx, columns=cols).values
    for cfg in ['A4b', 'A4b_CVRv5', 'M_mean2@keep30']:
        w = W[cfg]; S = np.vstack([np.zeros((1, w.shape[1])), np.cumsum(w, axis=0)])
        for H in (3, 5, 10, 20):
            hi = np.clip(np.arange(T) - 1, 0, T); lo = np.clip(np.arange(T) - 1 - H, 0, T)
            den = np.minimum(H, np.maximum(np.arange(T) - 1, 0)).astype(float); den[den == 0] = np.nan
            ah = np.nan_to_num((S[hi] - S[lo]) / den[:, None], nan=0.0)
            d = np.diff(ah, axis=0, prepend=np.zeros((1, ah.shape[1])))
            buy = np.clip(d, 0, None); sell = np.clip(-d, 0, None)
            bad_b = (iso == 0) if iso is not None else np.zeros_like(buy, bool)
            if lu is not None: bad_b = bad_b | (cl >= lu - 1e-9)
            if fb is not None: bad_b = bad_b | (fb == 0)
            bad_s = (iso == 0) if iso is not None else np.zeros_like(sell, bool)
            if ld is not None: bad_s = bad_s | (cl <= ld + 1e-9)
            if fs is not None: bad_s = bad_s | (fs == 0)
            er.append(dict(period=pname, cfg=cfg, hold=H,
                           buy_blocked_share=float(buy[bad_b].sum() / max(buy.sum(), 1e-12)),
                           sell_blocked_share=float(sell[bad_s].sum() / max(sell.sum(), 1e-12)),
                           flag_buy_cov=float(np.isfinite(fb).mean()) if fb is not None else np.nan,
                           flag_sell_cov=float(np.isfinite(fs).mean()) if fs is not None else np.nan))
    pd.DataFrame(er).to_csv(os.path.join(OUT, 'exposure_%s.csv' % pname), index=False)
    io.open(os.path.join(OUT, '_DONE_%s' % pname), 'w').write('%.0fs\n' % (time.time() - t0))
    P('[PERIOD DONE] %s %.0fs' % (pname, time.time() - t0)); log.close()

# --------------------------------------------------------------- 契约 / manifest
def contract(OUT):
    src = {}
    for f in ['comprehensive_factor_diagnosis.py', 'pool_screening_v2.py', 'event_study.py',
              'features_daily.py', 'data_loader.py']:
        src[f] = sha_file(os.path.join(PC, f))
    man = dict(when=time.strftime('%Y-%m-%d %H:%M:%S'), python=sys.version.split()[0],
               numpy=np.__version__, pandas=pd.__version__, periods={k: list(v) for k, v in PERIODS.items()},
               py_sha=src, inputs={p: sha_file(p) for p in [E6 + '/scan_all.csv', E6B + '/scan_all.csv', E2D]},
               engine_defaults=str(C.compute_calendar_pnl.__defaults__), cost_const=C.COST_BP_BILATERAL,
               adjustments=['E6/E6b 日序列比=诊断非硬闸', 'M_mean2/M_mean3_v2 bin+dec 双算',
                            'M 视图 best-effort', '恒等式 atol 1e-9 记录不中止', '玩具测试分两档'])
    io.open(os.path.join(OUT, 'run_manifest.json'), 'w', encoding='utf-8', newline='\n').write(
        json.dumps(man, ensure_ascii=False, indent=1))
    txt = ['# engine_contract.md（执行端读函数体复核，2026-09-04）', '',
           '- `compute_calendar_pnl`：`actual=W.rolling(H,min_periods=1).mean()`，`ah=actual.shift(exec_lag+1)`；'
           '段首分母 = 可用行数(<H)。**已核，与 brief §1.3 一致**。',
           '- `daily_ret = vwap_daily_return(data, adjust)`；`port=(ah*ret).sum(axis=1)` NaN 按 0 贡献；'
           '`position=ah.sum(axis=1)` 权重照算。**已核**。',
           '- `bench = daily_ret.where(base_pool==1).mean(axis=1)`，同一 H 下不随配置变。**已核**。',
           '- `turnover=0.5Σ|ah_t−ah_{t−1}|`（首日 fillna 0），`cost=turnover*bp/1e4`，`net=gross−cost`。**已核**。',
           '- `build_factor_strategy_holdings_cached`：两处 `len(...)<n_groups*3` 跳过 → 小池日无持仓；'
           '`qcut(rank(method="first"))` 组 1 最低；`except ValueError: continue`。**已核**。',
           '- `precompute_neutralized_factor`：`neutralize_by_mcap` 截面 OLS 残差，`dropna` 在内。**已核**。',
           '- 观察池 `build_observation_pool(signal,5)=Σ_{lag=1..5} signal.shift(lag)>0` → 日龄 1..5。**已核**。',
           '- 硬约束：`is_open==1`、非涨跌停(limit 价，缺失回退收益率)、`amount.rolling(20,min_periods=10).mean()>=2e7`、'
           '上市天数 rolling、`min_mcap=0`（调用方传）。**已核**。',
           '- 由上可证 `gross_{H,t}=(1/H)Σ_{j≤H}K_{t,j}`，K 与 H 无关（本脚本据此一次算 20 个 lag）。']
    io.open(os.path.join(OUT, 'engine_contract.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(txt) + '\n')
    print('[contract] written; py_sha ok; defaults', C.compute_calendar_pnl.__defaults__, C.COST_BP_BILATERAL)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--period'); ap.add_argument('--out', required=True)
    ap.add_argument('--contract', action='store_true'); ap.add_argument('--merge', action='store_true')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    if a.contract: contract(a.out)
    elif a.merge:
        import e6c_merge; e6c_merge.merge(a.out)
    else:
        assert a.period in PERIODS, a.period; run_period(a.period, a.out)
