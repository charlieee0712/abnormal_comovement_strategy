# -*- coding: utf-8 -*-
"""E6q EDGE 价差（brief §0.1 #11 / A-H；W14 = Ardia, Guidotti & Kroencke, JFE 161 (2024) 103916）。
- `edge`：作者实现 bidask 2.1.0 `python/bidask/edge.py` 的函数体逐行照搬（MIT License，Copyright (c) 2024 Emanuele Guidotti），唯一改动：五个指示变量里的
  相等判断（h != l、l != c1、o != h、o != l、c1 != h1、c1 != l1）改在原始价格上做。数学上等价（log 严格单调）；原式在对数价格上比较，numpy 的 SIMD 与标量
  两条 log 路径对同一价格可差 1 ulp（取决于数组内存对齐），使"相等"随机翻转——47 上同一进程重复调用作者含缺失样例得 0.010133 / 0.009752 两种结果，已复现。
  `edge_author`：作者原式（未改），只供对照。
- `rolling_panel`：T × N 面板；日 t 的值 = 止于 t−1 的 21 个交易日窗（行 t−21…t−1）上的 `edge(...)`；窗内完整 OHLC 观测 < 3 → 缺失（EDGE_WINDOW_RULE）；
  缺失价保留为 NaN 交给作者函数处理，不回填。输入为后复权 OHLC（raw × adj_factor，开盘日外 NaN）。按股票分块多进程，逐窗调用 `edge`（与作者函数逐位一致）。
- `selftest`：作者 `tests/test_edge.py` 的四例（全样本、前 10 行带号、含缺失样本、平价三行 NaN）。"""
import os
import warnings

import numpy as np

VERSION = 'bidask-2.1.0-edge'
LICENSE = 'MIT License, Copyright (c) 2024 Emanuele Guidotti'
SOURCE = 'https://github.com/eguidotti/bidask python/bidask/edge.py (v2.1.0)'
WINDOW = 21
MIN_COMPLETE = 3
AUTHOR_TESTS = (('ohlc.csv full', 0.0101849034905478), ('ohlc.csv rows 0-9 signed', -0.016889917516422),
                ('ohlc-miss.csv full', 0.01013284969780197), ('flat three rows', float('nan')))


def edge(open, high, low, close, sign=False):
    # check that the open, high, low, and close prices have the same length
    nobs = len(open)
    if len(high) != nobs or len(low) != nobs or len(close) != nobs:
        raise ValueError("Open, high, low, and close prices must have the same length")

    # return missing if there are less than 3 observations
    if nobs < 3:
        return np.nan

    # compute log-prices
    O_ = np.ascontiguousarray(np.asarray(open, dtype=np.float64))
    H_ = np.ascontiguousarray(np.asarray(high, dtype=np.float64))
    L_ = np.ascontiguousarray(np.asarray(low, dtype=np.float64))
    C_ = np.ascontiguousarray(np.asarray(close, dtype=np.float64))
    o = np.log(O_)
    h = np.log(H_)
    l = np.log(L_)
    c = np.log(C_)
    m = (h + l) / 2.

    # shift log-prices by one period
    h1, l1, c1, m1 = h[:-1], l[:-1], c[:-1], m[:-1]
    o, h, l, c, m = o[1:], h[1:], l[1:], c[1:], m[1:]
    # E6q：相等判断在原始价格上做（log 严格单调，o != h ⇔ log o != log h；避免 numpy SIMD / 标量两条 log 路径对同一价格差 1 ulp 使指示变量翻转）
    Hr1, Lr1, Cr1 = H_[:-1], L_[:-1], C_[:-1]
    Or, Hr, Lr = O_[1:], H_[1:], L_[1:]

    # compute log-returns
    r1 = m - o
    r2 = o - m1
    r3 = m - c1
    r4 = c1 - m1
    r5 = o - c1

    # compute indicator variables
    tau = np.where(np.isnan(h) | np.isnan(l) | np.isnan(c1), np.nan, (Hr != Lr) | (Lr != Cr1))
    po1 = tau * np.where(np.isnan(o) | np.isnan(h), np.nan, Or != Hr)
    po2 = tau * np.where(np.isnan(o) | np.isnan(l), np.nan, Or != Lr)
    pc1 = tau * np.where(np.isnan(c1) | np.isnan(h1), np.nan, Cr1 != Hr1)
    pc2 = tau * np.where(np.isnan(c1) | np.isnan(l1), np.nan, Cr1 != Lr1)

    # ignore warnings raised by nanmean for all-NaN slices
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)

        # compute probabilities
        pt = np.nanmean(tau)
        po = np.nanmean(po1) + np.nanmean(po2)
        pc = np.nanmean(pc1) + np.nanmean(pc2)

        # return missing if there are less than two periods with tau=1
        # or po or pc is zero
        if np.nansum(tau) < 2 or po == 0 or pc == 0:
            return np.nan

        # compute de-meaned log-returns
        d1 = r1 - np.nanmean(r1) / pt * tau
        d3 = r3 - np.nanmean(r3) / pt * tau
        d5 = r5 - np.nanmean(r5) / pt * tau

        # compute input vectors
        x1 = -4. / po * d1 * r2 + -4. / pc * d3 * r4
        x2 = -4. / po * d1 * r5 + -4. / pc * d5 * r4

        # compute expectations
        e1 = np.nanmean(x1)
        e2 = np.nanmean(x2)

        # compute variances
        v1 = np.nanmean(x1 ** 2) - e1 ** 2
        v2 = np.nanmean(x2 ** 2) - e2 ** 2

    # compute square spread by using a (equally) weighted
    # average if the total variance is (not) positive
    vt = v1 + v2
    s2 = (v2 * e1 + v1 * e2) / vt if vt > 0 else (e1 + e2) / 2.

    # compute signed root
    s = np.sqrt(np.abs(s2))
    if sign:
        s *= np.sign(s2)

    # return the spread
    return float(s)


def edge_author(open, high, low, close, sign=False):
    """作者原式（bidask 2.1.0，相等判断在对数价格上；只供对照与诊断，不用于面板）。"""
    nobs = len(open)
    if len(high) != nobs or len(low) != nobs or len(close) != nobs:
        raise ValueError("Open, high, low, and close prices must have the same length")
    if nobs < 3:
        return np.nan
    o = np.log(np.asarray(open))
    h = np.log(np.asarray(high))
    l = np.log(np.asarray(low))
    c = np.log(np.asarray(close))
    m = (h + l) / 2.
    h1, l1, c1, m1 = h[:-1], l[:-1], c[:-1], m[:-1]
    o, h, l, c, m = o[1:], h[1:], l[1:], c[1:], m[1:]
    r1 = m - o
    r2 = o - m1
    r3 = m - c1
    r4 = c1 - m1
    r5 = o - c1
    tau = np.where(np.isnan(h) | np.isnan(l) | np.isnan(c1), np.nan, (h != l) | (l != c1))
    po1 = tau * np.where(np.isnan(o) | np.isnan(h), np.nan, o != h)
    po2 = tau * np.where(np.isnan(o) | np.isnan(l), np.nan, o != l)
    pc1 = tau * np.where(np.isnan(c1) | np.isnan(h1), np.nan, c1 != h1)
    pc2 = tau * np.where(np.isnan(c1) | np.isnan(l1), np.nan, c1 != l1)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        pt = np.nanmean(tau)
        po = np.nanmean(po1) + np.nanmean(po2)
        pc = np.nanmean(pc1) + np.nanmean(pc2)
        if np.nansum(tau) < 2 or po == 0 or pc == 0:
            return np.nan
        d1 = r1 - np.nanmean(r1) / pt * tau
        d3 = r3 - np.nanmean(r3) / pt * tau
        d5 = r5 - np.nanmean(r5) / pt * tau
        x1 = -4. / po * d1 * r2 + -4. / pc * d3 * r4
        x2 = -4. / po * d1 * r5 + -4. / pc * d5 * r4
        e1 = np.nanmean(x1)
        e2 = np.nanmean(x2)
        v1 = np.nanmean(x1 ** 2) - e1 ** 2
        v2 = np.nanmean(x2 ** 2) - e2 ** 2
    vt = v1 + v2
    s2 = (v2 * e1 + v1 * e2) / vt if vt > 0 else (e1 + e2) / 2.
    s = np.sqrt(np.abs(s2))
    if sign:
        s *= np.sign(s2)
    return float(s)


def _read_ohlc_csv(path):
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        head = f.readline()
        for line in f:
            p = line.strip().split(',')
            rows.append([float(x) if x not in ('', 'NA') else np.nan for x in p])
    a = np.array(rows, dtype=np.float64)
    return a[:, 0], a[:, 1], a[:, 2], a[:, 3]


def selftest(ref_dir):
    """作者四例；返回 [(name, expected, got, ok)]。"""
    o, h, l, c = _read_ohlc_csv(os.path.join(ref_dir, 'pseudocode_ohlc.csv'))
    om, hm, lm, cm = _read_ohlc_csv(os.path.join(ref_dir, 'pseudocode_ohlc-miss.csv'))
    got = [edge(o, h, l, c), edge(o[0:10], h[0:10], l[0:10], c[0:10], True), edge(om, hm, lm, cm),
           edge([18.21, 17.61, 17.61], [18.21, 17.61, 17.61], [17.61, 17.61, 17.61], [17.61, 17.61, 17.61])]
    out = []
    for (name, exp), g in zip(AUTHOR_TESTS, got):
        ok = (np.isnan(g) and np.isnan(exp)) or (np.isfinite(g) and abs(g - exp) <= 1e-12 + 1e-9 * abs(exp))
        out.append((name, exp, g, bool(ok)))
    return out


_G = {}


def _init(paths):
    _G['o'] = np.load(paths[0], mmap_mode='r')
    _G['h'] = np.load(paths[1], mmap_mode='r')
    _G['l'] = np.load(paths[2], mmap_mode='r')
    _G['c'] = np.load(paths[3], mmap_mode='r')


def _block(cols):
    j0, j1 = cols
    o = np.asarray(_G['o'][:, j0:j1], dtype=np.float64)
    h = np.asarray(_G['h'][:, j0:j1], dtype=np.float64)
    l = np.asarray(_G['l'][:, j0:j1], dtype=np.float64)
    c = np.asarray(_G['c'][:, j0:j1], dtype=np.float64)
    T = o.shape[0]
    out = np.full(o.shape, np.nan)
    comp = (np.isfinite(o) & np.isfinite(h) & np.isfinite(l) & np.isfinite(c)).astype(np.int64)
    cs = np.vstack([np.zeros((1, comp.shape[1]), np.int64), np.cumsum(comp, axis=0)])
    n_eval = 0
    for jj in range(o.shape[1]):
        for t in range(WINDOW, T):
            a, b = t - WINDOW, t
            if cs[b, jj] - cs[a, jj] < MIN_COMPLETE:
                continue
            out[t, jj] = edge(o[a:b, jj], h[a:b, jj], l[a:b, jj], c[a:b, jj])
            n_eval += 1
    return j0, j1, out, n_eval


def rolling_panel(paths, T, N, workers=96, chunk=24):
    """paths = (open_adj, high_adj, low_adj, close_adj) 的 .npy；返回 (T × N 面板, 实算窗数)。"""
    import multiprocessing as mp
    blocks = [(j, min(j + chunk, N)) for j in range(0, N, chunk)]
    res = np.full((T, N), np.nan)
    n_eval = 0
    ctx = mp.get_context('fork')
    with ctx.Pool(workers, initializer=_init, initargs=(paths,)) as pool:
        for j0, j1, blk, ne in pool.imap_unordered(_block, blocks):
            res[:, j0:j1] = blk
            n_eval += ne
    return res, n_eval
