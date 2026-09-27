# -*- coding: utf-8 -*-
"""E6j 统计公共件（plan §4.5 / §7 / §8；brief W07–W09）。只做计算，不写判词。
  - 配对增量：d_t = net_child − net_parent（同日两者都有限）；段增量 D_s = 252·100·mean(d_t)；n_s = 有效配对日数
  - FULL = Σ n_s D_s / Σ n_s（W07：E6i descriptor_stats_all4 的四段按有效日合并）；G4 = median_s D_s（并印，不交叉）
  - 逐年 D_y（2010–2026，2026 截至 03-27 标 partial）
  - HAC（plan §8.5a）：保留原日历 mask，u_t = I_t(d_t − μ)，Bartlett 权重，滞后 L（主 H、敏感 max(2H, 20)）；MDE80 = 2.80·SE
  - stationary bootstrap（块均长 20 / 60，各 2,000 次；四段内分别抽，共享 draw；点估区间用原序列、零基线用中心化序列，分文件）
  - 冲击：c_t = κ·√(A·1e8)·bracket_t（E6g / E6h 源平方根模型，A 以亿元计；bracket 缺 = 当日无定价交易，另报未定价换手）"""
import numpy as np
import pandas as pd

import e6j_core as J

ANN = J.ANN
YEARS = list(range(2010, 2027))


def paired(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    return np.where(m, a - b, np.nan), m


def seg_D(d):
    m = np.isfinite(d)
    return (float(np.mean(d[m])) * ANN if m.any() else np.nan), int(m.sum())


def full_g4(Ds, ns):
    Ds, ns = np.asarray(Ds, float), np.asarray(ns, float)
    ok = np.isfinite(Ds) & (ns > 0)
    full = float(np.sum(Ds[ok] * ns[ok]) / np.sum(ns[ok])) if ok.any() else np.nan
    g4 = float(np.median(Ds[ok])) if ok.any() else np.nan
    return full, g4


def yearly(d, dates):
    yrs = pd.to_datetime(pd.Index(dates)).year.values
    out = {}
    for y in YEARS:
        m = (yrs == y) & np.isfinite(d)
        out[y] = float(np.mean(d[m])) * ANN if m.any() else np.nan
    return out


def hac_se(d, L):
    """plan §8.5a：原时间轴、内部缺失保留（u_t = 0），Bartlett(L)；返回均值的 SE（日单位）与 n。"""
    I = np.isfinite(d)
    n = int(I.sum())
    if n < 3:
        return np.nan, n
    mu = float(np.mean(d[I]))
    u = np.where(I, d - mu, 0.0)
    s = float(u @ u)
    for l in range(1, int(L) + 1):
        if l >= len(u):
            break
        s += 2.0 * (1.0 - l / (L + 1.0)) * float(u[l:] @ u[:-l])
    v = s / (n * n)
    return (np.sqrt(v) if v > 0 else np.nan), n


def impact_cost(bracket, A_yi, kappa):
    return kappa * np.sqrt(A_yi * 1e8) * np.nan_to_num(bracket, nan=0.0)


def stationary_indices(n, L, rng):
    """Politis–Romano 平稳块自助：几何块长（均值 L），环绕；返回长度 n 的下标。"""
    if n <= 0:
        return np.zeros(0, dtype=np.int64)
    p = 1.0 / L
    idx = np.empty(n, dtype=np.int64)
    i = 0
    while i < n:
        start = int(rng.integers(0, n))
        ln = int(rng.geometric(p))
        take = min(ln, n - i)
        idx[i:i + take] = (start + np.arange(take)) % n
        i += take
    return idx


def bootstrap_full(d_by_seg, L, n_draws, key, centered=False):
    """四段内分别平稳块抽样（共享 draw 由稳定哈希键决定），每 draw 携带数值与 mask、分母重算；返回 FULL 的 draw 数组。"""
    rng = J.rng_for('E6j', 'bootstrap', key, L)
    segs = list(d_by_seg)
    draws = np.full(n_draws, np.nan)
    idxs = {s: [stationary_indices(len(d_by_seg[s]), L, rng) for _ in range(n_draws)] for s in segs}
    for b in range(n_draws):
        num = den = 0.0
        for s in segs:
            d = d_by_seg[s]
            if centered:
                m = np.isfinite(d)
                d = np.where(m, d - (np.mean(d[m]) if m.any() else 0.0), np.nan)
            x = d[idxs[s][b]]
            m = np.isfinite(x)
            num += float(np.sum(x[m])); den += float(m.sum())
        draws[b] = num / den * ANN if den > 0 else np.nan
    return draws
