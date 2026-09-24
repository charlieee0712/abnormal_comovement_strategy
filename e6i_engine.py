#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 稠密引擎: 与 e6f_core.sparse_pnl_H / dev_from_dense 数学等价的向量化实现。

为什么: Stage 2 的随机路径与 C1 全交叉要跑几十万到上百万个账户, 源引擎的逐日 Python 循环
(约 0.3-0.5 s/账户/段) 撑不住。这里只改【算法路径】, 不改任何口径:
  * DEV 权重逐日直接调 K.dev_day (与 dev_from_dense 同一函数, 逐位相同);
  * 持仓 act[i] = sum_{s=i-H+1..i} W[s] / min(i+1, H)  (与 amap / act_sum 同式);
  * port[t] = r0[t] . act[t-2];  pos[t] = sum act[t-2];  turn[t] = 0.5 sum |act[t-2]-act[t-3]|;
  * gross = port - bench*pos;  net = gross - turn*cost_bp/1e4。
浮点累加顺序与源不同, 所以验收用代数等价容差 atol 1e-12 / rtol 1e-10 (brief §2), 由
e6i_engine_anchor.py 对真实母体 x H x 段阻断验收 —— 锚不过, 本模块不许用。
"""
from __future__ import annotations
import numpy as np

import e6e_core as K


def dev_weights(S, mask_c):
    """(T, Nc) bool -> (T, Nc) float64 DEV 目标权重; 逐日 K.dev_day, 与 dev_from_dense 同值。"""
    mask_c = np.asarray(mask_c, bool)
    T, Nc = mask_c.shape
    W = np.zeros((T, Nc), dtype=np.float64)
    for t in range(T):
        h = np.flatnonzero(mask_c[t])
        if len(h):
            W[t, h] = K.dev_day(h, S.icodes[t], S.cap[t], S.G)
    return W


def dev_weights_batch(S, masks):
    """(P, T, Nc) bool -> (P, T, Nc) float64。逐日向量化: 同一天各路径一起算。"""
    masks = np.asarray(masks, bool)
    P, T, Nc = masks.shape
    W = np.zeros((P, T, Nc), dtype=np.float64)
    G = S.G
    for t in range(T):
        m = masks[:, t, :]                                   # (P, Nc)
        n = m.sum(1)
        if not n.any():
            continue
        w0 = np.where(n > 0, np.minimum(1.0 / np.maximum(n, 1), K.MAX_STOCK), 0.0)   # (P,)
        ic = S.icodes[t]                                     # (Nc,)
        v = ic >= 0
        wm = m * w0[:, None]                                 # (P, Nc)
        # 每条路径的行业和 (one-hot 矩阵乘, 与 bincount 同值)
        gs = np.zeros((P, G))
        if v.any():
            iv = ic[v]
            O = np.zeros((len(iv), G))
            O[np.arange(len(iv)), iv] = 1.0
            gs = wm[:, v] @ O
        cap = S.cap[t]                                       # (G,)
        over = gs > cap[None, :]
        sc = np.ones((P, G))
        np.divide(np.broadcast_to(cap, (P, G)), gs, out=sc, where=over)
        sc[~over] = 1.0
        scale = np.ones((P, Nc))
        if v.any():
            scale[:, v] = sc[:, ic[v]]
        W[:, t, :] = wm * scale
    return W


def _act(W, H):
    """act[i] = sum_{k=0..H-1} W[i-k] / min(i+1, H)  (最后一轴前是时间轴)。"""
    T = W.shape[-2]
    A = np.array(W, dtype=np.float64, copy=True)
    for k in range(1, H):
        if k >= T:
            break
        A[..., k:, :] += W[..., :T - k, :]
    den = np.minimum(np.arange(1, T + 1), H).astype(np.float64)
    return A / den[:, None]


def pnl_W(S, W, H=K.HOLD, cost_bp=8.0):
    """单账户: W (T, Nc) 目标权重 -> (gross, pos, turn, net), 与 sparse_pnl_H 同式。"""
    T = S.T
    act = _act(W, H)
    port = np.zeros(T)
    pos = np.zeros(T)
    turn = np.zeros(T)
    if T > 2:
        port[2:] = np.einsum('tc,tc->t', S.r0[2:], act[:-2])
        pos[2:] = act[:-2].sum(1)
    if T > 3:
        turn[3:] = 0.5 * np.abs(act[1:-2] - act[:-3]).sum(1)
    gross = port - S.bench * pos
    return gross, pos, turn, gross - turn * (cost_bp / 1e4)


def pnl_W_batch(S, Wb, H=K.HOLD, cost_bp=8.0):
    """多账户: Wb (P, T, Nc) -> 每个 (P, T) 的 gross/pos/turn/net。"""
    P, T, Nc = Wb.shape
    act = _act(Wb, H)
    port = np.zeros((P, T))
    pos = np.zeros((P, T))
    turn = np.zeros((P, T))
    if T > 2:
        port[:, 2:] = np.einsum('tc,ptc->pt', S.r0[2:], act[:, :-2])
        pos[:, 2:] = act[:, :-2].sum(2)
    if T > 3:
        turn[:, 3:] = 0.5 * np.abs(act[:, 1:-2] - act[:, :-3]).sum(2)
    gross = port - S.bench[None, :] * pos
    return gross, pos, turn, gross - turn * (cost_bp / 1e4)


def pnl_mask(S, mask_c, H=K.HOLD, cost_bp=8.0, wmul=None):
    """mask -> DEV -> (可选乘性权重, 如软缩减 λ) -> 账本。wmul 只向下缩, 不重分配。"""
    W = dev_weights(S, mask_c)
    if wmul is not None:
        W = W * np.asarray(wmul, np.float64)
    return pnl_W(S, W, H, cost_bp)


def scale_to_common(W1, W0):
    """同资本对照 (plan §6.5): 逐形成日把两条目标权重都【向下】缩到二者较小的总资本。
       只缩不放, 系数 <= 1; 返回 (W1', W0')。"""
    s1 = W1.sum(-1, keepdims=True)
    s0 = W0.sum(-1, keepdims=True)
    m = np.minimum(s1, s0)
    f1 = np.where(s1 > 0, m / np.where(s1 > 0, s1, 1.0), 1.0)
    f0 = np.where(s0 > 0, m / np.where(s0 > 0, s0, 1.0), 1.0)
    return W1 * f1, W0 * f0
