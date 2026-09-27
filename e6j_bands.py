# -*- coding: utf-8 -*-
"""E6j 平稳块自助的计数矩阵形式（plan §8.4）：与 e6j_stats.bootstrap_full 同一组 draw（同 rng 键、同段序、同抽样次序），
每段 W[b, t] = 第 b 个 draw 中源日 t 被抽中的次数；位置年份另给 Wy[y][b, t] = 落在 y 年位置上的次数（逐年条件按位置日历重算）。
任意日序列族的重采样段均值 / 逐年均值 / FULL 均为矩阵乘；缺失日携带 mask、分母逐 draw 重算；中心化 = 段内减有效日均值（零均值基线）。"""
import numpy as np
import pandas as pd

import e6j_core as J
import e6j_stats as ST


def count_mats(seg_lengths, seg_dates, L, n_draws, key):
    """seg_lengths / seg_dates：按 J.SEGMENTS 顺序的 {段: 长度} / {段: 日期}。返回 {段: (W, {年: Wy}, 该段位置年份)}。"""
    rng = J.rng_for('E6j', 'bootstrap', key, L)
    out = {}
    for s in seg_lengths:                                   # 次序同 bootstrap_full：逐段、段内逐 draw
        n = int(seg_lengths[s])
        yrs = pd.to_datetime(pd.Index(seg_dates[s]).astype(str)).year.values
        assert len(yrs) == n
        W = np.zeros((n_draws, n))
        Wy = {int(y): np.zeros((n_draws, n)) for y in sorted(set(yrs))}
        for b in range(n_draws):
            ix = ST.stationary_indices(n, L, rng)
            np.add.at(W[b], ix, 1.0)
            for y in Wy:
                np.add.at(Wy[y][b], ix[yrs == y], 1.0)
        out[s] = (W, Wy, yrs)
    return out


def center(X):
    M = np.isfinite(X)
    mu = np.where(M.any(0), np.where(M, X, 0.0).sum(0) / np.maximum(M.sum(0), 1), 0.0)
    return np.where(M, X - mu[None, :], np.nan)


def resample(cm, X_by_seg, centered=False):
    """X_by_seg[段]：(n_s, K) 日序列（NaN = 无效）。返回 dict：
       seg_sum / seg_cnt：{段: (draws, K)}；year_sum / year_cnt：{年: (draws, K)}；另给原样本同口径的段和 / 段计数（real）。"""
    out = dict(seg_sum={}, seg_cnt={}, year_sum={}, year_cnt={}, real_sum={}, real_cnt={})
    for s, (W, Wy, yrs) in cm.items():
        X = X_by_seg[s]
        if centered:
            X = center(X)
        M = np.isfinite(X).astype(float); X0 = np.where(M > 0, X, 0.0)
        out['seg_sum'][s] = W @ X0; out['seg_cnt'][s] = W @ M
        out['real_sum'][s] = X0.sum(0); out['real_cnt'][s] = M.sum(0)
        for y, Wyy in Wy.items():
            out['year_sum'][y] = out['year_sum'].get(y, 0.0) + Wyy @ X0
            out['year_cnt'][y] = out['year_cnt'].get(y, 0.0) + Wyy @ M
    return out


def seg_D(rs, s):
    c = rs['seg_cnt'][s]
    return np.where(c > 0, rs['seg_sum'][s] / np.where(c > 0, c, 1.0), np.nan) * J.ANN


def full(rs, segs):
    num = sum(rs['seg_sum'][s] for s in segs); den = sum(rs['seg_cnt'][s] for s in segs)
    return np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan) * J.ANN


def g4(rs, segs):
    return np.nanmedian(np.stack([seg_D(rs, s) for s in segs], 0), axis=0)


def years_pos(rs):
    ys = sorted(rs['year_sum'])
    Y = np.stack([np.where(rs['year_cnt'][y] > 0, rs['year_sum'][y] / np.where(rs['year_cnt'][y] > 0, rs['year_cnt'][y], 1.0), np.nan)
                  for y in ys], 0)
    return np.sum(Y > 0, axis=0), ys


def max_t_band(draws, real, level=0.95):
    """draws：(n_draws, K) 未中心化重采样统计；SE = bootstrap sd；零 sd 列不进 max 统计（另报）。返回 (q, sd, 逐点 lo/hi, 同时 lo/hi, 入族标志)。"""
    sd = np.nanstd(draws, axis=0, ddof=1)
    fam = np.isfinite(sd) & (sd > 0) & np.isfinite(real)
    if fam.any():
        t = np.abs((draws[:, fam] - real[None, fam]) / sd[None, fam])
        q = float(np.nanquantile(np.nanmax(t, axis=1), level))
    else:
        q = np.nan
    z = 1.959963984540054
    return q, sd, real - z * sd, real + z * sd, real - q * sd, real + q * sd, fam
