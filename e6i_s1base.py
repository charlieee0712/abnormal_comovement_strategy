#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 1 / Stage 2 共用底座: 成员的 NS 中性化分位缓存、多期限标签、六集合。

pct 链与 E6h 同一路径 (特征锚 C 组逐位): F.neu_cache(raw, pool0, log_mcap, icodes, 'NS')
  -> G.pct_dense_dir(..., 'hi' | 'lo')。'hi' = 高值坏 (原序 pct); 'lo' = (-s).rank(pct) 真实反序。
标签 (plan §6.1 时钟分名):
  src5      = compute_forward_5d_excess (日龄线性归因, H=5, bp) —— E6h R0 源标签 (精确旧桥)
  alin_H    = Σ_{k=2..1+H} (dr_{t+k} - bm_{t+k})            日龄线性归因, H∈{1,3,5,10,20}
  entry_H   = Π_{k=2..1+H}(1+dr_{t+k}) - Π(1+bm_{t+k})       entry-fixed (端点复利), 同上
  bm = base_pool 等权 VWAP 日收益 (与源标签同基准); 段内, 段尾自然 NaN (不读段外)。
六集合 (plan §6.1; 每母体): pool0 / pre_focal (进入核排序的候选, DEP 母体为第一阶段存活 S1) /
  core_kept (C) / final (B) / econ_reject (D = 候选 ∩ 有核分 ∩ 未被核保留) /
  edge (B 中按核分最差 20% ∪ D 中按核分最好的同样多只 —— 决策边缘)。
"""
from __future__ import annotations
import os
import io
import json
import time

import numpy as np
import pandas as pd

import e6i_core as I
import e6i_features as FE
import e6f_core as F
import e6g_core as G
import comprehensive_factor_diagnosis as C
from event_study import get_base_pool

HS_LABEL = (1, 3, 5, 10, 20)


# ------------------------------------------------------------------ pct 缓存
def _pct_paths(segment, mid, policy):
    base = os.path.join(I.CACHE, segment, '%s__%s' % (mid, policy))
    return base + '__NShi.npy', base + '__NSlo.npy'


def pct_member(S, mid, policy=None, direction='hi', build=True):
    """(T, Nc) NS 分位 (pool0 内当日 log 流通市值 OLS 残差再排名)。读写都过守卫。"""
    m = FE.member(mid)
    policy = policy or m['policy']
    I.guard_i([mid], segment=S.name, use='read', where='pct_member')
    ph, pl = _pct_paths(S.name, mid, policy)
    want = ph if direction == 'hi' else pl
    if os.path.exists(want):
        return np.load(want, allow_pickle=False)
    if not build:
        return None
    raw, _ = I.load_member(S.name, mid, policy, where='pct_member')
    if raw is None:
        raise RuntimeError('成员缓存缺失: %s/%s' % (S.name, mid))
    df = pd.DataFrame(np.full((S.T, S.Nfull), np.nan), index=S.pool0.index, columns=S.pool0.columns)
    df.iloc[:, S.ccols] = raw
    cache, _ = F.neu_cache(df, S.pool0, S.log_mcap, S.icodes_neu, 'NS')
    hi = G.pct_dense_dir(cache, S.dates, S.ccolpos, S.Nc, 'hi')
    lo = G.pct_dense_dir(cache, S.dates, S.ccolpos, S.Nc, 'lo')
    for p, a in ((ph, hi), (pl, lo)):
        buf = io.BytesIO()
        np.save(buf, a.astype(np.float64), allow_pickle=False)
        I.atomic_write_bytes(p, buf.getvalue())
    return hi if direction == 'hi' else lo


def raw_member(S, mid, policy=None):
    m = FE.member(mid)
    arr, _ = I.load_member(S.name, mid, policy or m['policy'], where='raw_member')
    return arr


# ------------------------------------------------------------------ 标签
def labels(S):
    """dict: 'src5' / 'alin_H' / 'entry_H' -> (T, Nc) bp; 另附 'bm' (T,) 与 'dr' (T, Nc)。"""
    if getattr(S, '_lab', None) is not None:
        return S._lab
    bp = get_base_pool(S.data)
    dr = C.vwap_daily_return(S.data, True)
    bm = dr.where(bp.reindex(index=dr.index, columns=dr.columns).fillna(0) == 1).mean(axis=1)
    src = C.compute_forward_5d_excess(S.data, bp, hold_days=5, adjust=True)
    out = {'src5': I.to_grid(S, src)}
    D = dr.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]
    b = bm.reindex(S.pool0.index).values
    T = S.T
    for H in HS_LABEL:
        al = np.zeros((T, S.Nc))
        pr = np.ones((T, S.Nc))
        pb = np.ones(T)
        ok = np.ones((T, S.Nc), bool)
        for k in range(2, 2 + H):
            sh_d = np.full((T, S.Nc), np.nan)
            sh_b = np.full(T, np.nan)
            if k < T:
                sh_d[:T - k] = D[k:]
                sh_b[:T - k] = b[k:]
            al = al + (sh_d - sh_b[:, None])
            pr = pr * (1.0 + sh_d)
            pb = pb * (1.0 + sh_b)
        out['alin_%d' % H] = al * 1e4
        out['entry_%d' % H] = (pr - pb[:, None]) * 1e4
    out['bm'] = b
    S._lab = out
    return out


def label_anchor(S):
    """alin_5 必须与源标签 src5 逐位 (atol 1e-9 bp; 同式不同累加顺序)。"""
    L = labels(S)
    a, s = L['alin_5'], L['src5']
    m = np.isfinite(s)
    both = m & np.isfinite(a)
    return dict(n=int(m.sum()), missing=int((m & ~np.isfinite(a)).sum()),
                max_abs_bp=float(np.max(np.abs(a[both] - s[both]))) if both.any() else 0.0)


# ------------------------------------------------------------------ 六集合
def sets_for_mother(S, P):
    """P = e6h_run_routes.ParentCtx。返回 dict 集合名 -> (T, Nc) bool, 另附 edge 的构成计数。"""
    p0 = S.p0c
    cand = np.asarray(P.cand)
    if cand.shape[1] != S.Nc:
        cand = cand[:, S.ccols]
    cand = cand.astype(bool) & p0
    Cm = P.C.astype(bool)
    Bm = P.B.astype(bool)
    Dm = P.D.astype(bool)
    sc = P.score
    edge = np.zeros_like(Bm)
    for t in range(S.T):
        b = np.where(Bm[t] & np.isfinite(sc[t]))[0]
        d = np.where(Dm[t] & np.isfinite(sc[t]))[0]
        if len(b) == 0:
            continue
        k = max(1, int(np.floor(0.2 * len(b))))
        # 核分 低 = 好: B 中最差 = 分最大; D 中最好 = 分最小
        edge[t, b[np.argsort(-sc[t][b], kind='stable')[:k]]] = True
        if len(d):
            edge[t, d[np.argsort(sc[t][d], kind='stable')[:min(k, len(d))]]] = True
    return dict(pool0=p0, pre_focal=cand, core_kept=Cm & p0, final=Bm & p0,
                econ_reject=Dm & p0, edge=edge & p0)


# ------------------------------------------------------------------ 统计工具 (逐形成日先聚合)
def row_rank(A, mask):
    """逐行 (日) 在 mask 内求平均并列 pct 排名; mask 外 NaN。"""
    X = np.where(mask & np.isfinite(A), A, np.nan)
    return pd.DataFrame(X).rank(axis=1, pct=True).values


def row_spearman(xr, yr, min_n=10):
    """xr, yr 已是同一集合内的排名 (NaN 外)。逐日 Pearson(秩) = Spearman。返回 (T,)。"""
    m = np.isfinite(xr) & np.isfinite(yr)
    n = m.sum(1).astype(float)
    x = np.where(m, xr, 0.0)
    y = np.where(m, yr, 0.0)
    with np.errstate(all='ignore'):
        mx = x.sum(1) / n
        my = y.sum(1) / n
        cx = np.where(m, x - mx[:, None], 0.0)
        cy = np.where(m, y - my[:, None], 0.0)
        r = (cx * cy).sum(1) / np.sqrt((cx ** 2).sum(1) * (cy ** 2).sum(1))
    return np.where(n >= min_n, r, np.nan)


def group_means(xr, y, n_groups, min_n=None):
    """逐日按 xr 分 n_groups 组 (等频, 秩 pct 切), 每日每组 y 均值 -> (T, G); 组内 <1 名 NaN。"""
    min_n = min_n or 2 * n_groups
    m = np.isfinite(xr) & np.isfinite(y)
    g = np.clip(np.ceil(np.where(m, xr, 0.0) * n_groups).astype(int), 1, n_groups)
    out = np.full((xr.shape[0], n_groups), np.nan)
    ok = m.sum(1) >= min_n
    for k in range(1, n_groups + 1):
        sel = m & (g == k)
        cnt = sel.sum(1)
        s = np.where(sel, y, 0.0).sum(1)
        with np.errstate(all='ignore'):
            out[:, k - 1] = np.where(ok & (cnt > 0), s / cnt, np.nan)
    return out


def nw_t(x, lag):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 30:
        return np.nan
    e = x - x.mean()
    s = float(e @ e) / n
    for L in range(1, min(lag, n - 1) + 1):
        s += 2.0 * (1.0 - L / (lag + 1.0)) * float(e[L:] @ e[:-L]) / n
    return float(x.mean() / np.sqrt(s / n)) if s > 0 else np.nan
