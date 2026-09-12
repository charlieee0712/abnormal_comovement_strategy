#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 同仓位对照 (plan §4.4/§4.5 要求, 主运行里漏了这一个, 这里补)。

问题: M-T 的增益会不会只是"仓位略升 = 多敞口"?
plan §4.5 的做法: **每形成日**把两边目标权重缩至两者【较小】的总仓位, 系数 <= 1,
再 rolling 并重计交易。它不是等风险策略, 也不做看完评估段后的全局归一化。

用法: python3 e6h_samepos.py --segment 2010-2014 [--route M-T-tcv-vs-t60]
"""
from __future__ import annotations
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_rules as RU
import e6h_run_routes as RR
import e6h_expand as EX
import e6f_core as F
import e6e_core as K

RES = H.RES


def scale_to_min(ivA, ivB):
    """逐形成日把两边缩到较小总仓位 (系数 <= 1)。返回两套缩过的 (idx, val)。"""
    iA, vA = ivA
    iB, vB = ivB
    T = len(iA)
    oA, oB = [], []
    for t in range(T):
        sa = float(vA[t].sum()) if len(vA[t]) else 0.0
        sb = float(vB[t].sum()) if len(vB[t]) else 0.0
        m = min(sa, sb)
        ca = (m / sa) if sa > 0 else 1.0
        cb = (m / sb) if sb > 0 else 1.0
        oA.append(vA[t] * min(1.0, ca))
        oB.append(vB[t] * min(1.0, cb))
    return (iA, oA), (iB, oB)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--route', default='M-T-tcv-vs-t60')
    a = ap.parse_args()
    t0 = time.time()
    rows = [r for r in EX.all_descriptors()
            if r['route_id'] == a.route and not r.get('is_identity')]
    S = H.seg(a.segment, verbose=False)
    out, pctx = [], {}
    for r in rows:
        p = r['parent']
        if p not in pctx:
            pctx[p] = RR.ParentCtx(S, p)
        P = pctx[p]
        mask, wmul, _ = RR.build_mask(P, r)
        ivC = F.dev_from_dense(S, mask)
        if wmul is not None:
            ivC = (ivC[0], [v * wmul[t, ivC[0][t]] if len(ivC[0][t]) else v
                            for t, v in enumerate(ivC[1])])
        ivP = F.dev_from_dense(S, P.B)
        sC, sP = scale_to_min(ivC, ivP)
        pC = F.sparse_pnl_H(S, sC[0], sC[1], K.HOLD, F.COST)
        pP = F.sparse_pnl_H(S, sP[0], sP[1], K.HOLD, F.COST)
        raw = F.sparse_pnl_H(S, ivC[0], ivC[1], K.HOLD, F.COST)
        both = np.isfinite(pC[0]) & np.isfinite(pP[0])
        out.append(dict(descriptor_id=r['descriptor_id'], route_id=a.route,
                        parent=p, segment=a.segment,
                        new_key=r.get('new_key'), alpha=r.get('alpha'),
                        policy=r.get('policy'),
                        d_net8_native=H.ann(np.asarray(raw[3]) - np.asarray(P.pnl[3])),
                        d_net8_samepos=H.ann(np.where(both,
                                                      np.asarray(pC[3]) - np.asarray(pP[3]),
                                                      np.nan)),
                        pos_child=float(np.nanmean(raw[1])),
                        pos_parent=float(np.nanmean(P.pnl[1])),
                        pos_after_scale_child=float(np.nanmean(pC[1])),
                        pos_after_scale_parent=float(np.nanmean(pP[1]))))
    od = os.path.join(RES, 'paired_controls')
    os.makedirs(od, exist_ok=True)
    d = pd.DataFrame(out)
    d.to_csv(os.path.join(od, 'samepos_%s_%s.csv' % (a.route, a.segment)), index=False)
    sub = d[d.alpha < 1.0]
    print('[%s %s] n=%d, %.0fs' % (a.route, a.segment, len(d), time.time() - t0))
    print('  全部:      原生 中位 %+.3f | 同仓位 中位 %+.3f'
          % (d.d_net8_native.median(), d.d_net8_samepos.median()))
    print('  alpha<1:   原生 中位 %+.3f 均值 %+.3f | 同仓位 中位 %+.3f 均值 %+.3f 正比例 %.0f%%'
          % (sub.d_net8_native.median(), sub.d_net8_native.mean(),
             sub.d_net8_samepos.median(), sub.d_net8_samepos.mean(),
             100 * (sub.d_net8_samepos > 0).mean()))
    print('  缩放后仓位: 子 %.4f vs 父 %.4f (必须几乎相等)'
          % (sub.pos_after_scale_child.mean(), sub.pos_after_scale_parent.mean()))


if __name__ == '__main__':
    main()
