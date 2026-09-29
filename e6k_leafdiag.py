# -*- coding: utf-8 -*-
"""E6k 八子集条件置换的可移动份额与置换熵（E6K-Q05-c；plan §10.1；e6k_mechanisms 文档列出但未落盘的一项，2026-09-29 补）。
只用分区结构（当日根 → 行业 / 旧 K 三档 / size 三档的分层树叶，与 e6k_run_rand 同一 tree_leaves 与 k0 = struct.q0）与新测量有效掩码，不读收益。
对象 = 八子集随机登记的 24 个 NATIVE 主对象（四测量 × 六生产形态，α .25 × H5）× 八子集 × 段。后段过 post_gate。
输出 diagnostics/mechanisms/<段>_leafdiag.csv。"""
import e6k_boot  # noqa: F401
import os
import sys
import json
import argparse

import numpy as np
import pandas as pd

import e6k_core as K


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    K.post_gate(a.segment, 'leafdiag')
    import e6k_env as E
    import e6k_random as RN
    seg = E.Seg(a.segment)
    rows = []
    for p in E.P6:
        k0 = seg.struct(p).q0
        for f in ('S', 'M', 'Q', 'C1'):
            V = np.isfinite(seg.kf(f))
            for sub in RN.SUBSETS:
                leaf, ts = RN.tree_leaves(seg, V, k0, sub)
                d = RN.leaf_diagnostics(seg, leaf, V)
                rows.append(dict(segment=a.segment, desc_id='%s|%s|a0.25|H5|NATIVE' % (f, p), subset=sub, valid_cells=int(V.sum()), **d,
                                 tree=json.dumps(ts, ensure_ascii=False)))
    od = K.P('diagnostics', 'mechanisms')
    os.makedirs(od, exist_ok=True)
    pth = os.path.join(od, '%s_leafdiag.csv' % a.segment)
    K.atomic_write_csv(pth, pd.DataFrame(rows))
    K.write_receipt('leafdiag_%s' % a.segment, [pth], 'SUCCEEDED', rows=len(rows))
    print('leafdiag %s：%d 行' % (a.segment, len(rows)), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
