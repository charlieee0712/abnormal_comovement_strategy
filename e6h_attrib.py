#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 归因: Δgross 的三集合分解 (plan §4.5, brief §5)。答"改善来自哪里"。

  Δgross = Σ_i (w_child − w_parent)_i · (r_i − bench)
按【新增 / 移出 / 幸存者重新定权】三个互斥集合分解, 最后扣实际费用差与冲击差。
**逐日先相加, 再在同支持上取均值** (plan §4.5 末段: 差的中位数不等于中位数之差,
也不把几个贡献中位数相加成总效应)。

同时报: 目标人数 / live 人数 / 净仓位 / HHI / 有效 N / 行业权重。
plan §4.5: "ADD 既可能扩仓, 也可能因每股/行业权重重定而降仓; 不得用人数猜资本方向。"

用法: python3 e6h_attrib.py --segment 2010-2014 --parent A06
"""
from __future__ import annotations
import os
import sys
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_run_routes as RR
import e6h_lx as LX
import e6h_expand as EX
import e6f_core as F
import e6e_core as K

RES = H.RES
ANN = 252 * 100.0


def held_w(S, idx, val):
    """【实际 rolling 持有权重】, 不是形成日目标权重。
       plan §4.5: "源批次线性引擎用实际 rolling 权重做恒等式"。
       引擎 gross[t] = sum_i W[t,i]*(r0[t,i]-bench[t]), 所以只有用 W 才能与引擎闭合。"""
    return LX.held_weights(S, idx, val, K.HOLD, None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--parent', required=True)
    a = ap.parse_args()
    t0 = time.time()
    rows = [r for r in EX.all_descriptors()
            if r['parent'] == a.parent and not r.get('is_identity')]
    if not rows:
        print('本片无描述符'); return
    S = H.seg(a.segment, verbose=False)
    P = RR.ParentCtx(S, a.parent)
    pidx, pval = F.dev_from_dense(S, P.B)
    Wp = held_w(S, pidx, pval)
    # 逐日超额收益 (r - bench), 与引擎 gross = port - bench*pos 一致
    # 引擎: gross = port - bench*pos, port = sum W*r0, 而 S.r0 已把 NaN 置 0。
    # 所以 NaN 格对 gross 的贡献是 -bench*W, 【不能】把 ex 也置 0, 否则闭合不上。
    ex = S.r0 - np.asarray(S.bench, float)[:, None]
    Pb = P.B
    print('  就绪 %.0fs, %d 个描述符' % (time.time() - t0, len(rows)), flush=True)

    out = []
    for i, r in enumerate(rows):
        try:
            mask, wmul, _ = RR.build_mask(P, r)
        except Exception:
            continue
        idx, val = F.dev_from_dense(S, mask)
        if wmul is not None:
            val = [v * wmul[t, idx[t]] if len(idx[t]) else v for t, v in enumerate(val)]
        Wc = held_w(S, idx, val)
        dW = Wc - Wp
        # 集合在【持有层】定义 (不是形成日), 才能与引擎的 gross 闭合
        hp, hc = Wp != 0, Wc != 0
        added = (~hp) & hc
        removed = hp & (~hc)
        surv = hp & hc
        # 逐日贡献, 再在同支持上取均值 (不先取中位再相加)
        c_add = (np.where(added, dW, 0.0) * ex).sum(axis=1)
        c_rem = (np.where(removed, dW, 0.0) * ex).sum(axis=1)
        c_srv = (np.where(surv, dW, 0.0) * ex).sum(axis=1)
        tot = (dW * ex).sum(axis=1)
        resid = float(np.nanmax(np.abs(tot - (c_add + c_rem + c_srv))))
        # 与引擎的闭合: tot 必须等于引擎的逐日 Δgross
        # 费用差
        g0, p0_, t0_, n0 = P.pnl
        g1, p1, t1, n1 = RR.RU.run_mask(S, mask, wmul)
        both = np.isfinite(g0) & np.isfinite(g1)
        out.append(dict(
            segment=a.segment, descriptor_id=r['descriptor_id'],
            route_id=r['route_id'], parent=a.parent, role=r['role'],
            d_gross_ann=H.ann(np.where(both, np.asarray(g1) - np.asarray(g0), np.nan)),
            contrib_added_ann=float(np.nanmean(c_add[both])) * ANN,
            contrib_removed_ann=float(np.nanmean(c_rem[both])) * ANN,
            contrib_survivor_reweight_ann=float(np.nanmean(c_srv[both])) * ANN,
            identity_residual=resid,
            engine_closure=float(np.nanmax(np.abs(
                tot[both] - (np.asarray(g1)[both] - np.asarray(g0)[both])))),
            d_cost8_ann=float(np.nanmean(t1[both] - t0_[both])) * 8e-4 * ANN,
            d_net8_ann=H.ann(np.where(both, np.asarray(n1) - np.asarray(n0), np.nan)),
            n_added_heldcells=int(added.sum()), n_removed_heldcells=int(removed.sum()),
            n_survivor_heldcells=int(surv.sum()),
            d_pos=float(np.nanmean(p1) - np.nanmean(p0_)),
            d_target_n=float(mask.sum(axis=1).mean() - Pb.sum(axis=1).mean())))
        if (i + 1) % 300 == 0:
            print('    %d/%d  %.0fs' % (i + 1, len(rows), time.time() - t0), flush=True)

    d = pd.DataFrame(out)
    od = os.path.join(RES, 'route_results')
    tag = '%s_%s' % (a.segment, a.parent)
    d.to_csv(os.path.join(od, 'attrib_%s.csv' % tag), index=False)
    mx = float(d.identity_residual.max()) if len(d) else np.nan
    print('  [%s] 归因 %d 行; 三集合恒等残差 max %.3e; %.0fs'
          % (tag, len(d), mx, time.time() - t0))
    if np.isfinite(mx) and mx > 1e-12:
        print('  !! 三集合分解不闭合 —— 这是 plan §4.5 的恒等式, 必须为 0')


if __name__ == '__main__':
    main()
