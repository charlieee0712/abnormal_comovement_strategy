#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i P0: 源数据事实核对 (brief §2 source_resolution.md 的数据部分)。只读, 不改任何口径。

核: turnover_rate 单位与分母 / amount 单位 / vwap 是否落在 [low, high] /
    limitUp/Down 覆盖与按 ticker 对齐 / 触板与一字板频率 / |chg|>=9.8% 与真实触板的混淆 /
    is_open / 行业 PIT 覆盖与变更 / adj_factor 变动频率。
输出 checks/p0_source_facts.json (数字) —— source_resolution.md 由这些数字写成。

用法: python3 e6i_p0_source.py --segment 2015-2018 --out <RES>/checks
"""
from __future__ import annotations
import e6i_boot  # noqa: F401  (必须最先: 关掉 pyarrow S3 的 192 个 AwsEventLoop 线程)
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6f_core as F
import e6e_core as K

TOL = 0.005          # 触板容差 (元): 价格 tick 0.01 的一半


def q(x, ps=(0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {}
    return {('p%02d' % int(p * 100)): float(np.quantile(x, p)) for p in ps} | dict(n=int(len(x)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', default='2015-2018')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    t0 = time.time()
    ps, pe = F.PERIODS[a.segment]
    data = F.guarded_load(ps, pe)
    close = data['close']
    idx, cols = close.index, close.columns
    out = dict(segment=a.segment, period=[ps, pe], shape=list(close.shape),
               fields=sorted(data.keys()))
    isopen = data['is_open'].reindex(index=idx, columns=cols) == 1
    ok = isopen & close.notna()
    out['is_open_frac_of_nonnull_close'] = float(isopen[close.notna()].mean().mean())

    # ---- 1. turnover_rate 单位与分母 ----
    tr = data['turnover_rate'].reindex(index=idx, columns=cols)
    out['turnover_rate_quantiles_open'] = q(tr.values[ok.values])
    vol = data['volume'].reindex(index=idx, columns=cols)
    mcap = data['mcap'].reindex(index=idx, columns=cols)      # negMarketValue
    float_sh = mcap / close
    implied = vol / float_sh                                    # 比例口径的流通换手
    m = ok & (tr > 0) & (implied > 0)
    ratio = (tr / implied).values[m.values]
    out['turnover_rate_over_vol_div_floatshares'] = q(ratio)
    # ---- 2. amount 单位 ----
    amt = data['amount'].reindex(index=idx, columns=cols)
    vw = data['vwap'].reindex(index=idx, columns=cols)
    m2 = ok & (vol > 0) & (amt > 0) & (vw > 0)
    out['amount_over_vol_x_vwap'] = q((amt / (vol * vw)).values[m2.values])
    # ---- 3. vwap 落在 [low, high] ----
    hi = data['high'].reindex(index=idx, columns=cols)
    lo = data['low'].reindex(index=idx, columns=cols)
    op = data['open'].reindex(index=idx, columns=cols)
    m3 = ok & vw.notna() & hi.notna() & lo.notna()
    inside = ((vw >= lo - 1e-6) & (vw <= hi + 1e-6))
    out['vwap_inside_low_high_frac'] = float(inside.values[m3.values].mean())
    out['vwap_outside_examples'] = int((~inside).values[m3.values].sum())
    ohlc_ok = (lo <= np.minimum(op, close) + 1e-6) & (hi >= np.maximum(op, close) - 1e-6)
    out['ohlc_consistent_frac'] = float(ohlc_ok.values[m3.values].mean())

    # ---- 4. 涨跌停价: 列对齐 + 覆盖 + 触板 ----
    lu_raw, ld_raw = data.get('limit_up'), data.get('limit_down')
    out['limit_tables_present'] = bool(lu_raw is not None and ld_raw is not None)
    if out['limit_tables_present']:
        out['limit_up_raw_shape'] = list(lu_raw.shape)
        out['limit_cols_equal_close_cols_positionally'] = bool(
            lu_raw.shape[1] == len(cols) and (np.asarray(lu_raw.columns) == np.asarray(cols)).all())
        lu = lu_raw.reindex(index=idx, columns=cols)           # 按 ticker 标签对齐 (E6g F: 位置索引错位)
        ld = ld_raw.reindex(index=idx, columns=cols)
        cov = (lu.notna() & ld.notna())
        out['limit_coverage_on_open_days'] = float(cov.values[ok.values].mean())
        out['limit_coverage_by_year'] = {
            str(y): float(cov[ok].loc[cov.index.year == y].stack().mean())
            for y in sorted(set(idx.year))}
        # 合理性: 涨停价 ≈ 前收 × (1+限幅)
        rat = (lu / data['lclose'].reindex(index=idx, columns=cols)).values[(ok & cov).values]
        out['limit_up_over_lclose'] = q(rat)
        touch_up = hi >= lu - TOL
        touch_dn = lo <= ld + TOL
        touch = (touch_up | touch_dn) & cov
        one_word = touch & (hi == lo)
        hl_eq = (hi == lo)
        out['touch_frac_open'] = float(touch.values[ok.values].mean())
        out['one_word_frac_open'] = float(one_word.values[ok.values].mean())
        out['hl_equal_frac_open'] = float(hl_eq.values[ok.values].mean())
        out['hl_equal_not_touch_frac_open'] = float((hl_eq & ~touch & cov).values[ok.values].mean())
        out['hl_equal_limit_unknown_frac_open'] = float((hl_eq & ~cov).values[ok.values].mean())
        # |chg|>=9.8% 与真实触板的混淆 (plan W14)
        chg = data['change_pct'].reindex(index=idx, columns=cols)
        chg_abs = chg.abs()
        # change_pct 单位 (百分数 or 比例) 先看分位
        out['change_pct_quantiles_open'] = q(chg.values[ok.values], ps=(0.001, 0.01, 0.5, 0.99, 0.999))
        thr = 9.8 if np.nanquantile(chg_abs.values[ok.values], 0.999) > 1.5 else 0.098
        big = (chg_abs >= thr) & cov
        tt = touch & cov
        mm = ok.values & cov.values
        out['chg98_vs_touch'] = dict(
            threshold_used=thr,
            both=int((big & tt).values[mm].sum()), big_only=int((big & ~tt).values[mm].sum()),
            touch_only=int((~big & tt).values[mm].sum()), neither=int((~big & ~tt).values[mm].sum()))

    # ---- 5. 行业 PIT ----
    ind = data.get('industry_zx1', data.get('industry'))
    if ind is not None:
        ind = ind.reindex(index=idx, columns=cols)
        out['industry_coverage_open'] = float(ind.notna().values[ok.values].mean())
        chgs = (ind != ind.shift(1)) & ind.notna() & ind.shift(1).notna()
        out['industry_changes_total'] = int(chgs.values.sum())
        out['industry_n_distinct'] = int(pd.unique(ind.values.ravel()[pd.notna(ind.values.ravel())]).size)

    # ---- 6. 复权因子 ----
    af = data['adj_factor'].reindex(index=idx, columns=cols)
    ch = (af != af.shift(1)) & af.notna() & af.shift(1).notna()
    out['adj_factor_change_events'] = int(ch.values.sum())
    out['adj_factor_change_frac_open'] = float(ch.values[ok.values].mean())

    out['elapsed_s'] = round(time.time() - t0, 1)
    os.makedirs(a.out, exist_ok=True)
    p = os.path.join(a.out, 'p0_source_facts_%s.json' % a.segment)
    with open(p, 'w') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False, default=str)
    for k, v in out.items():
        if k in ('fields', 'limit_coverage_by_year'):
            continue
        print('%-44s %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:150]))
    print('by_year limit coverage:', out.get('limit_coverage_by_year'))


if __name__ == '__main__':
    main()
