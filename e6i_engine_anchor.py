#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 稠密引擎的阻断锚: 对真实母体 x H x 段, 与源 e6f_core.sparse_pnl_H / dev_from_dense 比。

判据 (brief §2 代数等价路径): 逐日序列 max|差| <= atol 1e-12 (另报相对误差); DEV 权重逐位相同。
另测批量版 (P 条路径一起算) 与单账户版一致。锚不过 -> 退出码 1, 稠密引擎不许用。

用法: python3 e6i_engine_anchor.py --segment 2015-2018
"""
from __future__ import annotations
import e6i_boot  # noqa: F401  (必须最先: 关掉 pyarrow S3 的 192 个 AwsEventLoop 线程)
import os
import sys
import time
import json
import argparse

import numpy as np

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_engine as E
import e6h_run_routes as RR
import e6f_core as F

HS = [1, 2, 3, 5, 10, 15, 20, 30]
ATOL = 1e-12


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    t0 = time.time()
    S = I.seg_i(a.segment, warm=False)
    print('段就绪 %.0fs T=%d Nc=%d' % (time.time() - t0, S.T, S.Nc), flush=True)
    rows, bad = [], 0
    t_sp = t_de = 0.0
    for pn in I.MOTHERS + I.ANCHOR_MOTHERS:
        P = RR.ParentCtx(S, pn)
        idx, val = F.dev_from_dense(S, P.B)
        W = E.dev_weights(S, P.B)
        # DEV 逐位
        Wsp = np.zeros_like(W)
        for t in range(S.T):
            if len(idx[t]):
                Wsp[t, idx[t]] = val[t]
        dev_diff = float(np.max(np.abs(W - Wsp)))
        for Hh in HS:
            ta = time.time()
            g0, p0, u0, n0 = F.sparse_pnl_H(S, idx, val, Hh, F.COST)
            t_sp += time.time() - ta
            ta = time.time()
            g1, p1, u1, n1 = E.pnl_W(S, W, Hh, F.COST)
            t_de += time.time() - ta
            d = {}
            for nm, x0, x1 in (('gross', g0, g1), ('pos', p0, p1), ('turn', u0, u1),
                               ('net8', n0, n1)):
                x0, x1 = np.asarray(x0, float), np.asarray(x1, float)
                nan_same = bool(np.array_equal(np.isnan(x0), np.isnan(x1)))
                m = np.isfinite(x0) & np.isfinite(x1)
                d[nm] = (float(np.max(np.abs(x0[m] - x1[m]))) if m.any() else 0.0, nan_same)
            worst = max(v[0] for v in d.values())
            ok = worst <= ATOL and all(v[1] for v in d.values()) and dev_diff == 0.0
            bad += (not ok)
            rows.append(dict(mother=pn, H=Hh, ok=ok, dev_max_abs=dev_diff,
                             **{'%s_max_abs' % k: v[0] for k, v in d.items()},
                             **{'%s_nan_same' % k: v[1] for k, v in d.items()},
                             net8_ann_src=I.ann(n0), net8_ann_dense=I.ann(n1)))
        print('  %-4s DEV 差 %.1e | H 网格最差 %.2e' % (
            pn, dev_diff, max(r['net8_max_abs'] for r in rows if r['mother'] == pn)), flush=True)

    # 批量版: 4 母体叠成 P=4 一次算, 与单账户版比
    Ms = np.stack([RR.ParentCtx(S, pn).B for pn in I.MOTHERS])
    Wb = E.dev_weights_batch(S, Ms)
    Ws = np.stack([E.dev_weights(S, m) for m in Ms])
    bdev = float(np.max(np.abs(Wb - Ws)))
    gb = E.pnl_W_batch(S, Wb, 5, F.COST)
    gs = [E.pnl_W(S, w, 5, F.COST) for w in Ws]
    bpnl = max(float(np.nanmax(np.abs(gb[k][i] - gs[i][k]))) for i in range(len(Ms)) for k in range(4))
    batch_ok = bdev <= ATOL and bpnl <= ATOL
    bad += (not batch_ok)

    out = dict(segment=a.segment, atol=ATOL, n_checked=len(rows), n_pass=sum(r['ok'] for r in rows),
               batch_dev_max_abs=bdev, batch_pnl_max_abs=bpnl, batch_ok=batch_ok,
               sec_sparse=round(t_sp, 2), sec_dense=round(t_de, 2),
               speedup=round(t_sp / max(t_de, 1e-9), 1), rows=rows)
    I.atomic_write_json(os.path.join(I.RES, 'checks', 'engine_anchor_%s.json' % a.segment), out)
    print('锚 %d/%d 过; 批量 DEV 差 %.1e / 账本差 %.1e; 源 %.1fs vs 稠密 %.1fs (x%.1f)'
          % (out['n_pass'], out['n_checked'], bdev, bpnl, t_sp, t_de, out['speedup']))
    sys.exit(0 if bad == 0 else 1)


if __name__ == '__main__':
    main()
