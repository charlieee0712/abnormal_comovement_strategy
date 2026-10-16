# -*- coding: utf-8 -*-
"""E6m 新算子的"路径 × 股票"向量化版（随机层提速；与 e6m_ops 逐路径版逐位相同，由 e6m_vec_bench.py 在真实数据上对拍）。
前提：同一天各路径的 Q 缺失位置相同（LEGACY / ISK_P5 等置换只在有限值之间交换，缺失不动）；不满足时调用方回退逐路径版。
平局：原总序名次 rk 在当日唯一，先按 rk 排列列，再对优先值做稳定排序 = (优先值, rk) 字典序（与逐路径版的 (pri, rk, ids) 相同，因 rk 已唯一）。"""
import numpy as np

import e6m_ops as O


def _cols_by_rank(idx, rk):
    return idx[np.argsort(rk[idx], kind='stable')]


def band_paths(order, s0, KQ, n, w, INSIDE=None, PREV=None, b=0.0, loading=None):
    """KQ / INSIDE / PREV：(P, N)。返回 (P, N) bool。"""
    P, N = KQ.shape
    base = O.source_mask(order, n)
    A, B, C, j = O.band_parts(order, n, w)
    out = np.repeat(base[None, :], P, axis=0)
    if j == 0:
        return out
    fin = np.isfinite(KQ[:, B])
    if not (fin == fin[0]).all():
        raise ValueError('各路径 Q 缺失位置不同：回退逐路径版')
    good = B[fin[0]]
    if not len(good):
        return out
    k = int(base[good].sum())
    rk = O.ranks_of(order)
    g = _cols_by_rank(good, rk)                                   # 按 rk 排好的可动列
    pri = (KQ if INSIDE is None else INSIDE)[:, g]
    if not np.isfinite(pri).all():
        raise ValueError('可动优先序必须有限')
    tgt = np.argsort(pri, axis=1, kind='stable')                   # 每路径无记忆新优先序（列位置）
    if PREV is None:
        take = np.take_along_axis(np.broadcast_to(g, pri.shape), tgt[:, :k], axis=1)
    else:
        slot = np.sort(s0[g])
        cols_t = np.take_along_axis(np.broadcast_to(g, pri.shape), tgt, axis=1)      # 每路径按新优先序排列的股票
        ell = np.ones(N) if loading is None else np.asarray(loading, float)
        z = slot[None, :] - float(b) * ell[cols_t] * np.take_along_axis(PREV, cols_t, axis=1)
        sel = np.argsort(z, axis=1, kind='stable')[:, :k]            # 平局按新优先序位置（= 逐路径版 tr）
        take = np.take_along_axis(cols_t, sel, axis=1)
    out[:, good] = False
    rows = np.repeat(np.arange(P), take.shape[1])
    out[rows, take.ravel()] = True
    return out


def priority_paths(order, s0, KQ, n, c):
    """无记忆 PRIORITY_PASS（路径向量化）。"""
    c = O.check_threshold(c)
    P, N = KQ.shape
    base = O.source_mask(order, n)
    known = np.isfinite(KQ)
    if not (known == known[0]).all():
        raise ValueError('各路径 Q 缺失位置不同：回退逐路径版')
    kn = known[0]
    out = np.repeat((base & ~kn)[None, :], P, axis=0)
    k = n - int((base & ~kn).sum())
    rk = O.ranks_of(order)
    ix = _cols_by_rank(np.flatnonzero(kn), rk)
    fail = (KQ[:, ix] > c).astype(np.int64)
    sel = np.argsort(fail, axis=1, kind='stable')[:, :k]            # (不合格, rk) 字典序
    take = np.take_along_axis(np.broadcast_to(ix, fail.shape), sel, axis=1)
    rows = np.repeat(np.arange(P), take.shape[1])
    out[rows, take.ravel()] = True
    return out


def hard_paths(order, KQ, n, c):
    c = O.check_threshold(c)
    base = O.source_mask(order, n)
    return base[None, :] & (~np.isfinite(KQ) | (KQ <= c))
