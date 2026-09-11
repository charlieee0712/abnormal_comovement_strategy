# -*- coding: utf-8 -*-
"""E6g 阶段 0-a: pool0 池事实 + 涨跌停实际分支核实与计数 (brief §1.3 / §2 必交列)。

只读地基文件, 不改任何源码。对每段报:
  (1) limit_up/limit_down 原始覆盖与 has_limit_data 判定 -> 实际走哪支
  (2) not_limit 在四种写法下各剔掉多少【观察池形成日 x 票】
  (3) 形成日 pool0 成员触及涨跌停的数量与比例 (逐段逐年)
  (4) flag_buy/flag_sell 覆盖、age 分布、基准全 NaN 日
"""
import os, sys, json, time
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e6f_core as F
import e6e_core as K
import comprehensive_factor_diagnosis as C
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import (define_i11_signal, build_observation_pool,
                               apply_hard_constraints)

RES = '/mnt/sda2/lichenchen/results/20260911_1140_E6g_structure_layer'


def run(pname):
    t0 = time.time()
    ps, pe = PERIODS[pname]
    data = F.guarded_load(ps, pe)
    feats = C.calc_all_daily_features(data)
    close = data['close']
    ref_idx, ref_col = close.index, close.columns

    def align(df, fill=0):
        if df is None:
            return None
        return df.reindex(index=ref_idx, columns=ref_col).fillna(fill)

    lu_raw, ld_raw = data.get('limit_up'), data.get('limit_down')
    lu, ld = align(lu_raw), align(ld_raw)

    base_pool = get_base_pool(data)
    signal = define_i11_signal(feats, base_pool)
    obs = build_observation_pool(signal, obs_window=5)
    pool0 = apply_hard_constraints(obs, data, feats, min_mcap=0)     # 源实际调用

    # ---- (1) 实际分支 ----
    o = {'segment': pname, 'start': ps, 'end': pe,
         'T': int(close.shape[0]), 'N': int(close.shape[1])}
    o['limit_field_present'] = bool(lu_raw is not None and ld_raw is not None)
    if lu_raw is not None:
        o['limit_up_nonnull_raw'] = int(lu_raw.notna().sum().sum())
        g0 = (lu > 0)
        o['limit_up_gt0_aligned'] = int(g0.sum().sum())
        o['limit_up_gt0_frac_of_grid'] = float(g0.mean().mean())
        dd = g0.any(axis=1)
        o['limit_up_first_day_with_data'] = str(dd.idxmax().date()) if dd.any() else None
        o['limit_up_days_with_any_data'] = int(dd.sum())
        o['limit_up_day_coverage'] = float(dd.mean())
    has_limit_data = bool((lu > 0).any().any()) if lu is not None else False
    o['has_limit_data'] = has_limit_data
    o['branch_taken'] = ('OR_limit_price' if (lu is not None and ld is not None and has_limit_data)
                         else 'fallback_unadjusted_9.8pct')

    # ---- (2) 四种写法的 not_limit ----
    dret_raw = close / close.shift(1) - 1                       # 未复权 (源回退分支)
    adjf = C.adjust_factor(data)
    cadj = close * adjf
    dret_adj = cadj / cadj.shift(1) - 1                         # 复权对照
    valid_lim = (lu > 0) & (ld > 0)

    nl = {}
    nl['A_or_as_coded'] = (close < lu - 0.01) | (close > ld + 0.01)
    nl['A2_and_intended'] = (~valid_lim) | ((close < lu - 0.01) & (close > ld + 0.01))
    nl['B_fallback_unadj'] = (dret_raw < 0.098) & (dret_raw > -0.098)
    nl['B_adj_reference'] = (dret_adj < 0.098) & (dret_adj > -0.098)

    obsm = (obs.reindex(index=ref_idx, columns=ref_col).fillna(0).values == 1)
    n_obs = int(obsm.sum())
    o['obs_cells'] = n_obs
    o['not_limit_excluded'] = {}
    for kk, v in nl.items():
        ex = int((obsm & (~v.values)).sum())
        o['not_limit_excluded'][kk] = {'cells': ex,
                                       'frac_of_obs': float(ex / n_obs) if n_obs else None}
    # 回退分支把除权日误当跌停: 未复权 < -9.8% 但复权 > -9.8%
    exdiv = obsm & (dret_raw.values < -0.098) & (dret_adj.values > -0.098)
    o['fallback_exdiv_false_exclusions'] = int(np.nansum(exdiv))

    # 源实际 pool0 vs 换支后的 pool0
    def pool_with(nlmask):
        is_open = align(data.get('is_open'), fill=0)
        amount = align(data.get('amount'), fill=1e10)
        tradable = (is_open == 1)
        liquid = (amount.rolling(20, min_periods=10).mean() > 2e7)
        listd = close.notna().astype(float).rolling(20, min_periods=1).sum() >= 20
        return (obs.reindex(index=ref_idx, columns=ref_col).fillna(0)
                * (tradable & nlmask & liquid & listd).astype(float))
    o['pool0_cells_source'] = int((pool0.values == 1).sum())
    o['pool0_cells_by_branch'] = {kk: int((pool_with(v).values == 1).sum())
                                  for kk, v in nl.items()}

    # ---- (3) 形成日 pool0 成员触及涨跌停 (必交列) ----
    p0 = (pool0.values == 1)
    at_up = (valid_lim & (close >= lu - 0.01)).values
    at_dn = (valid_lim & (close <= ld + 0.01)).values
    unk = (~valid_lim).values
    yr = pd.Index(ref_idx).year.values
    rows = []
    for y in sorted(set(yr)):
        m = (yr == y)[:, None] & p0
        tot = int(m.sum())
        rows.append(dict(segment=pname, year=int(y), pool0_cells=tot,
                         at_limit_up=int((m & at_up).sum()),
                         at_limit_down=int((m & at_dn).sum()),
                         limit_price_unknown=int((m & unk).sum()),
                         frac_at_up=float((m & at_up).sum() / tot) if tot else None,
                         frac_at_down=float((m & at_dn).sum() / tot) if tot else None,
                         frac_unknown=float((m & unk).sum() / tot) if tot else None))
    lim_year = pd.DataFrame(rows)

    # ---- (4) flag / age / 基准 ----
    for fl in ('flag_buy', 'flag_sell', 'flag_st'):
        fr = data.get(fl)
        o[fl + '_present'] = fr is not None
        if fr is not None:
            fa = fr.reindex(index=ref_idx, columns=ref_col)
            o[fl + '_pool0_coverage'] = float(np.nanmean(fa.notna().values[p0]))

    sg = signal.reindex(index=ref_idx, columns=ref_col).fillna(0).values
    age = np.full(sg.shape, 0, np.int8)
    for lag in range(5, 0, -1):
        sh = np.zeros_like(sg); sh[lag:] = sg[:-lag]
        age = np.where(sh > 0, lag, age)
    o['age_distribution_on_pool0'] = {int(a): int(((age == a) & p0).sum()) for a in range(0, 6)}

    mature = close.notna().astype(float).rolling(20, min_periods=1).sum() >= 20
    clean = ((base_pool == 1) & mature).astype(float)
    bse = [c for c in close.columns if K.is_bse(c)]
    if bse:
        clean[bse] = 0.0
    dr = C.vwap_daily_return(data, K.ADJUST)
    bench = dr.where(clean == 1).mean(axis=1)
    o['bench_all_nan_days'] = int(bench.isna().sum())
    o['clean_zero_days'] = int((clean.sum(axis=1) == 0).sum())
    o['pool0_zero_days'] = int((pool0.sum(axis=1) == 0).sum())
    o['pool0_daily_size_median'] = float(pool0.sum(axis=1).median())
    o['signal_cells'] = int((sg > 0).sum())
    o['elapsed_s'] = round(time.time() - t0, 1)

    os.makedirs(os.path.join(RES, 'H0'), exist_ok=True)
    with open(os.path.join(RES, 'H0', 'pool_facts_%s.json' % pname), 'w') as fh:
        json.dump(o, fh, indent=1, ensure_ascii=False)
    lim_year.to_csv(os.path.join(RES, 'H0', 'limit_hits_%s.csv' % pname), index=False)
    print(json.dumps(o, indent=1, ensure_ascii=False))
    return o


if __name__ == '__main__':
    run(sys.argv[1])
