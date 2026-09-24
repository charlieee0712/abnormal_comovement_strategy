#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 稀疏引擎: 与 e6i_engine (已对源 48/48 x 2 段锚定) 数学等价, 给 Z-MAP 随机路径用。

为什么: 首轮随机路径约 505 万条 (两段 x 3 类 x 代表 256 / 非代表 64), 稠密引擎每条 ~0.18 s。
名单每日只有 ~60 只 (稠密表 1.7% 非零), 这里只改算法路径, 不改任何口径:

DEV   逐日 w0 = min(1/n, MAX_STOCK); 行业和 gs 用"同值 w0 顺序累加 cnt 次"的查表值 —— 与源
      dev_day 的 np.bincount(weights) (C 循环顺序累加) 逐位相同; 超限行业 w = w0 * (cap/gs), 与源
      同两步浮点运算 -> DEV 权重【逐位】等于 K.dev_day (锚 = 0 差)。
持仓  act[j] = sum_{k<min(j+1,H)} W[j-k] / min(j+1,H);  port[t] = r0[t].act[t-2]
      = (sum_{L=2..H+1} W[t-L].r0[t]) / den[t-2]  -> 按滞后 L 的稀疏点积再累加。
仓位  pos[t] = sum_k sw[t-2-k] / den[t-2]  (sw = 当日目标权重和)。
换手  j >= H: act[j]-act[j-1] = (W[j]-W[j-H])/H, 权重非负故 sum|a-b| = sum a + sum b - 2 sum min(a,b),
      min 只在两日交集上非零 -> 稀疏; j <= H 的起始段直接用稠密行 (<= 21 行)。
浮点累加顺序与稠密引擎不同 -> 账本验收用 atol 1e-12 (e6i_sparse --anchor)。
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import time
import json
import argparse

import numpy as np

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K


class SparseEngine(object):
    def __init__(self, S):
        self.S = S
        self.T, self.Nc = int(S.T), int(S.Nc)
        self.r0 = np.ascontiguousarray(S.r0, dtype=np.float64)
        if not np.isfinite(self.r0).all():
            raise ValueError('r0 含非有限值 (源 nan_to_num 应已处理)')
        self.r0T = np.ascontiguousarray(self.r0.T).ravel()          # 股票主序: 一格的 H 个滞后在内存里连续
        self.bench = np.asarray(S.bench, np.float64)
        self.ic = np.asarray(S.icodes)
        self.cap = np.asarray(S.cap, np.float64)
        self.G = int(S.G)
        self.Wd = np.zeros((self.T, self.Nc))
        self._tab = np.zeros((1, 1))
        self._tabn = 0
        self._ar = np.arange(1, self.T + 1)

    # ------------------------------------------------------------ DEV
    def _seq(self, nmax):
        if nmax <= self._tabn:
            return self._tab
        n2 = max(int(nmax), 2 * self._tabn, 128)
        tab = np.zeros((n2 + 1, n2 + 1))
        for n in range(1, n2 + 1):
            w0 = min(1.0 / n, K.MAX_STOCK)
            tab[n, 1:n + 1] = np.cumsum(np.full(n, w0))      # 顺序累加 = bincount 的累加顺序
        self._tab, self._tabn = tab, n2
        return tab

    def dev(self, t, c):
        """(t, c) = 一个账户全部 (形成日, 列) 单元 (无重复, 顺序任意) -> 同序 DEV 权重。"""
        T = self.T
        if len(t) == 0:
            return np.zeros(0)
        n_t = np.bincount(t, minlength=T)
        n = n_t[t]
        w0 = np.minimum(1.0 / n, K.MAX_STOCK)
        ic = self.ic[t, c]
        v = ic >= 0
        w = w0.copy()
        if v.any():
            tv, iv = t[v], ic[v]
            key = tv * self.G + iv
            cnt = np.bincount(key, minlength=T * self.G)
            gs = self._seq(int(n.max()))[n[v], cnt[key]]
            capv = self.cap[tv, iv]
            over = gs > capv
            wv = w0[v]
            with np.errstate(divide='ignore', invalid='ignore'):
                w[v] = np.where(over, wv * (capv / gs), wv)
        return w

    # ------------------------------------------------------------ 账本
    def pnl(self, t, c, w, Hs, cost_bp=8.0):
        """返回 {H: (gross, pos, turn, net)} (每个 (T,) float64), 与 e6i_engine.pnl_W 同式。"""
        T = self.T
        Hs = tuple(sorted(set(int(h) for h in Hs)))
        out = {}
        if len(t) == 0:
            z = np.zeros(T)
            for H in Hs:
                out[H] = (z - self.bench * 0.0, z.copy(), z.copy(), z - self.bench * 0.0)
            return out
        Hmax = Hs[-1]
        sw = np.bincount(t, weights=w, minlength=T)
        nL = Hmax
        Ls = np.arange(2, Hmax + 2)
        tt = t[:, None] + Ls[None, :]
        ok = tt < T
        li = np.broadcast_to(np.arange(nL)[None, :], tt.shape)
        vals = w[:, None] * self.r0T[c[:, None] * T + np.minimum(tt, T - 1)]
        Q = np.bincount((li * T + tt)[ok], weights=vals[ok], minlength=nL * T).reshape(nL, T)
        cQ = np.cumsum(Q, axis=0)                          # cQ[H-1][t] = sum_{L=2..H+1} W[t-L].r0[t]
        Wd = self.Wd
        Wd[t, c] = w
        try:
            for H in Hs:
                den = np.minimum(self._ar, H).astype(np.float64)
                port = np.zeros(T)
                pos = np.zeros(T)
                turn = np.zeros(T)
                if T > 2:
                    port[2:] = cQ[H - 1][2:] / den[:-2]
                    rs = sw.copy()
                    for k in range(1, H):
                        if k >= T:
                            break
                        rs[k:] += sw[:T - k]
                    pos[2:] = rs[:-2] / den[:-2]
                if T > 3:
                    d = np.zeros(T)
                    je = min(H, T - 1)
                    A = np.cumsum(Wd[:je + 1], axis=0)
                    if je >= H:
                        A[H] -= Wd[0]
                    act_e = A / den[:je + 1, None]
                    d[1:je + 1] = np.abs(act_e[1:] - act_e[:-1]).sum(1)
                    if T - 1 > H:
                        m = t >= H + 1
                        tm, cm, wm = t[m], c[m], w[m]
                        mn = np.minimum(wm, Wd[tm - H, cm])
                        M = np.bincount(tm, weights=mn, minlength=T)
                        j = np.arange(H + 1, T)
                        d[j] = (sw[j] + sw[j - H] - 2.0 * M[j]) / H
                    turn[3:] = 0.5 * d[1:T - 2]
                gross = port - self.bench * pos
                out[H] = (gross, pos, turn, gross - turn * (cost_bp / 1e4))
        finally:
            Wd[t, c] = 0.0
        return out


def mask_cells(mask):
    t, c = np.nonzero(np.asarray(mask, bool))
    return t, c


# ============================================================ 锚
def anchor(seg, n_random=24, seed=7):
    import e6i_core as I
    import e6i_features as FE
    import e6i_engine as EN
    import e6i_ops as OP
    FE.build_catalog()
    I.set_protected_members(FE.protected_ids())
    S = I.seg_i(seg, warm=False)
    SE = SparseEngine(S)
    rng = np.random.default_rng(seed)
    masks = []
    for mn in I.MOTHERS:
        M = OP.Mother(S, mn)
        masks.append(('mother_%s' % mn, M.B))
        # 母体名单的随机子集 / 随机 pool0 子集 (覆盖小名单、大名单、行业超限)
    p0 = S.p0c
    for i in range(n_random):
        frac = [0.02, 0.1, 0.3, 0.6][i % 4]
        masks.append(('rand_p0_%.2f_%d' % (frac, i), p0 & (rng.random(p0.shape) < frac)))
    Hs = (1, 2, 3, 5, 10, 20)
    rows = []
    worst_w = worst_p = 0.0
    t0 = time.time()
    for name, m in masks:
        Wd = EN.dev_weights(S, m)
        t, c = mask_cells(m)
        w = SE.dev(t, c)
        dw = float(np.max(np.abs(Wd[t, c] - w))) if len(t) else 0.0
        # 稠密表中名单外必须为 0
        Wd2 = Wd.copy()
        Wd2[t, c] = 0.0
        outside = float(np.abs(Wd2).max())
        worst_w = max(worst_w, dw, outside)
        res = SE.pnl(t, c, w, Hs)
        for H in Hs:
            g0, p0_, u0, n0 = EN.pnl_W(S, Wd, H, 8.0)
            g1, p1, u1, n1 = res[H]
            dmax, nan_same = 0.0, True
            for a_, b_ in ((g0, g1), (p0_, p1), (u0, u1), (n0, n1)):
                fa, fb = np.isfinite(a_), np.isfinite(b_)
                nan_same &= bool(np.array_equal(fa, fb))
                if fa.any():
                    dmax = max(dmax, float(np.max(np.abs(a_[fa] - b_[fa]))))
            worst_p = max(worst_p, dmax)
            rows.append(dict(mask=name, H=H, n_cells=int(len(t)), dev_max_abs=dw, dev_outside=outside,
                             pnl_max_abs=dmax, nonfinite_same=nan_same,
                             n_nonfinite_days=int((~np.isfinite(n0)).sum()),
                             ok=bool(dw == 0.0 and outside == 0.0 and dmax <= 1e-12 and nan_same)))
    ok = all(r['ok'] for r in rows)
    res = dict(segment=seg, n_masks=len(masks), n_rows=len(rows), n_pass=sum(r['ok'] for r in rows),
               dev_max_abs=worst_w, pnl_max_abs=worst_p, ok=ok, tolerance='DEV 逐位 (0); 账本 atol 1e-12',
               elapsed_s=round(time.time() - t0, 1), rows=rows)
    I.atomic_write_json(os.path.join(I.RES, 'checks', 'sparse_engine_anchor_%s.json' % seg), res)
    print('[%s] 稀疏引擎锚 %d/%d; DEV 最大差 %.1e; 账本最大差 %.1e; %s'
          % (seg, res['n_pass'], res['n_rows'], worst_w, worst_p, 'OK' if ok else 'FAIL'))
    # 计时: 母体 R2 名单 x 6 个 H
    t, c = mask_cells(masks[1][1])
    ts = time.time()
    for _ in range(20):
        w = SE.dev(t, c)
        SE.pnl(t, c, w, (3, 5, 10, 20))
    print('  计时: DEV + 4 个 H 账本 %.1f ms/账户' % ((time.time() - ts) / 20 * 1000))
    return ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--anchor', required=True)
    a = ap.parse_args()
    sys.exit(0 if anchor(a.anchor) else 1)
