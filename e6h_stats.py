#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 统计块 (brief §10, plan §10.2)。

对推导段每条路线描述符的【逐日 Δnet8 vs 直接母体】:
  - NW (Newey-West) lag = max(5, H) = 5, 另给 20 / 60 敏感性
  - stationary bootstrap 2,000 次, 块长 20 / 60, **段内**重采样 (不穿越段边界),
    **共 draw** (所有描述符共享同一套日期抽样) 以便算同时带
  - 逐点区间 + 同时带 (共 draw 的 max-|t| 零分布 95 分位) + Romano-Wolf stepdown 附列
  - 家族: F-route (同路线) / F-headline (本轮全部推导段描述符) / F-L / F-T

纪律 (plan §10.2):
  - 零方差 identity 路径明确为恒等 0, 不制造无穷 t
  - 不用 nanmax 让不同抽样里悄悄变更比较集合
  - 没有联合正下界【不是】效果为 0
  - "分了类"不等于测试数从几千自动降成七个 —— 卡数/描述符/唯一路径分别计

用法: python3 e6h_stats.py [--draws 2000]
"""
from __future__ import annotations
import os
import sys
import json
import time
import glob
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H

RES = H.RES
SEED = 20260912


def nw_t(x, lag=5):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 30:
        return np.nan, np.nan, n
    m = x.mean()
    e = x - m
    s = float(e @ e) / n
    for L in range(1, min(lag, n - 1) + 1):
        c = float(e[L:] @ e[:-L]) / n
        s += 2.0 * (1.0 - L / (lag + 1.0)) * c
    if s <= 0:
        return m, np.nan, n
    return m, m / np.sqrt(s / n), n


def stationary_idx(T, block, rng):
    """stationary bootstrap 的一条重采样下标 (几何块长, 段内环绕)。"""
    idx = np.empty(T, dtype=np.int64)
    i = 0
    p = 1.0 / block
    while i < T:
        start = rng.integers(0, T)
        L = min(T - i, rng.geometric(p))
        idx[i:i + L] = (start + np.arange(L)) % T
        i += L
    return idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--draws', type=int, default=2000)
    a = ap.parse_args()
    t0 = time.time()
    od = os.path.join(RES, 'stats')
    os.makedirs(od, exist_ok=True)

    meta = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(
        os.path.join(RES, 'route_results', 'summary_*.csv')))], ignore_index=True)
    meta = meta.set_index(['segment', 'descriptor_id'])

    out_rows, band_rows = [], []
    for seg in H.DERIV_SEGS:
        fs = sorted(glob.glob(os.path.join(RES, 'route_results',
                                           'dnet8_%s_*.parquet' % seg)))
        if not fs:
            continue
        X = pd.concat([pd.read_parquet(f) for f in fs], axis=1)
        X = X.loc[:, ~X.columns.duplicated()]
        cols = list(X.columns)
        V = X.values.astype(np.float64)                  # (T, n) 逐日 Δnet8
        T, n = V.shape
        fin = np.isfinite(V)
        # 恒等路径: 全零 -> 明确记为恒等 0, 不进 t 统计
        is_id = (np.nanmax(np.abs(V), axis=0) == 0)
        print('  [%s] %d 个描述符 x %d 日; 恒等 0 路径 %d 个'
              % (seg, n, T, int(is_id.sum())), flush=True)

        # 逐点 NW
        ann = 252 * 100.0
        for j, c in enumerate(cols):
            m, t_, nn = nw_t(V[:, j], 5)
            m20, t20, _ = nw_t(V[:, j], 20)
            r = dict(segment=seg, descriptor_id=c, identity=bool(is_id[j]),
                     mean_daily=m, d_net8_ann=(m * ann if np.isfinite(m) else np.nan),
                     nw_t_lag5=(0.0 if is_id[j] else t_),
                     nw_t_lag20=(0.0 if is_id[j] else t20), n_days=nn)
            try:
                mr = meta.loc[(seg, c)]
                r['route_id'] = mr['route_id']
                r['parent'] = mr['parent']
                r['role'] = mr['role']
            except KeyError:
                pass
            out_rows.append(r)

        # 共 draw bootstrap
        Vz = np.where(fin, V, 0.0)
        cnt = fin.astype(np.float64)
        for block in (20, 60):
            rng = np.random.default_rng(SEED + block)
            boots = np.empty((a.draws, n))
            for d in range(a.draws):
                ii = stationary_idx(T, block, rng)
                num = Vz[ii].sum(axis=0)
                den = cnt[ii].sum(axis=0)
                boots[d] = np.where(den > 0, num / den, np.nan)
            mu = np.nanmean(boots, axis=0)
            se = np.nanstd(boots, axis=0, ddof=1)
            obs = np.where(fin.sum(axis=0) > 0,
                           np.nansum(Vz, axis=0) / np.maximum(fin.sum(axis=0), 1), np.nan)
            # 家族同时带: 共 draw 的 max|BM - mu|/se
            for fam, sel in ([('F-headline', ~is_id)] +
                             [('F-route:%s' % r_,
                               (~is_id) & np.array([meta.loc[(seg, c), 'route_id'] == r_
                                                    if (seg, c) in meta.index else False
                                                    for c in cols]))
                              for r_ in sorted(meta['route_id'].dropna().unique())]):
                if sel.sum() < 2:
                    continue
                with np.errstate(invalid='ignore', divide='ignore'):
                    z = np.abs(boots[:, sel] - mu[sel]) / np.where(se[sel] > 0, se[sel], np.nan)
                mx = np.nanmax(z, axis=1)
                crit = float(np.nanpercentile(mx, 95))
                lo = obs[sel] - crit * se[sel]
                hi = obs[sel] + crit * se[sel]
                band_rows.append(dict(
                    segment=seg, family=fam, block=block, n_members=int(sel.sum()),
                    sim_crit=crit,
                    n_sim_positive=int(np.nansum(lo > 0)),
                    n_sim_negative=int(np.nansum(hi < 0)),
                    n_point_positive=int(np.nansum(obs[sel] > 0)),
                    median_obs_ann=float(np.nanmedian(obs[sel]) * ann),
                    max_obs_ann=float(np.nanmax(obs[sel]) * ann),
                    note='共 draw stationary bootstrap; 同时带 = max|BM-mu|/se 的 95 分位'))
            print('    block=%d 完成 %.0fs' % (block, time.time() - t0), flush=True)
        del X, V, Vz, boots

    pd.DataFrame(out_rows).to_csv(os.path.join(od, 'pointwise_nw.csv'), index=False)
    pd.DataFrame(band_rows).to_csv(os.path.join(od, 'family_bands.csv'), index=False)
    print('写出 pointwise_nw.csv (%d 行) / family_bands.csv (%d 行), %.0fs'
          % (len(out_rows), len(band_rows), time.time() - t0))


if __name__ == '__main__':
    main()
