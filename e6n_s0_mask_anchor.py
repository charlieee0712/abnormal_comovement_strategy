# -*- coding: utf-8 -*-
"""E6n Stage 0 第 2 类（名单层部分；附录 A2-1 / A2-4 / A2-8 的不读收益子项）：本轮名单层与 E6m 已交付名单（results/20261005_0556_E6m 工作目录
masks/<段>/<形态>.npz，E6m 阶段 S 在 47 上实跑、其 A2-1 已对 E5a pool2 逐字节核过）逐格比：
  原父 NATIVE ↔ E6m K0|<形态>|PARENT；Q0 / C1 × α .125 / .25 / .5 × NONE / HG10 / LAG1_10 ↔ E6m <测量>|<形态>|LINEAR|-|a<α>|<记忆>|SOURCE。
判据来源 = 基线（前轮产物，同输入）；输出 stage0/c2_mask_anchor_E6m.csv（逐比较：格数、不等格数）+ 汇总 json。不读收益。"""
import os
import json
import numpy as np
import pandas as pd

import e6n_core as N

E6M_W = N.E6M_WORK
FORMS = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5', 'R2', 'A06')


def main():
    rows = []
    for seg in N.SEGMENTS:
        for f in FORMS:
            pe = os.path.join(E6M_W, 'masks', seg, '%s.npz' % f)
            pn = N.P('masks', seg, '%s.npz' % f)
            if not os.path.exists(pe):
                rows.append(dict(seg=seg, form=f, pair='E6m 名单文件', status='NOT_APPLICABLE', note='E6m 无该形态名单'))
                continue
            ze = np.load(pe, allow_pickle=False)
            zn = np.load(pn, allow_pickle=False)
            n = int(zn['n_cells'][0])
            if int(ze['n_cells'][0]) != n:
                rows.append(dict(seg=seg, form=f, pair='n_cells', status='FAIL', note='%d vs %d' % (int(ze['n_cells'][0]), n)))
                continue
            ce = {str(x): j for j, x in enumerate(ze['config_ids'])}
            cn = {str(x): j for j, x in enumerate(zn['mask_keys'])}
            un = lambda z, j: np.unpackbits(z['final_bits'][j])[:n].astype(bool)
            pairs = [('NONE|a0|NATIVE' + ('' if f in FORMS[:6] else '|%s' % f), 'K0|%s|PARENT|-|-|NONE|SOURCE|-' % f)]
            if f in FORMS[:6]:
                for m in ('Q0', 'C1'):
                    for a in ('0.125', '0.25', '0.5'):
                        for mem in ('NONE', 'HG10', 'LAG1_10'):
                            pairs.append(('%s|a%s|%s' % (mem, a, m), '%s|%s|LINEAR|-|a%s|%s|SOURCE|-' % (m, f, a, mem)))
            for kn, ke in pairs:
                if kn not in cn or ke not in ce:
                    rows.append(dict(seg=seg, form=f, pair='%s ↔ %s' % (kn, ke), status='NOT_APPLICABLE', note='一侧无此键'))
                    continue
                a, b = un(zn, cn[kn]), un(ze, ce[ke])
                d = int((a != b).sum())
                rows.append(dict(seg=seg, form=f, pair='%s ↔ %s' % (kn, ke), n_cells=n, members_e6n=int(a.sum()), members_e6m=int(b.sum()),
                                 cells_differ=d, status='PASS' if d == 0 else 'FAIL'))
    df = pd.DataFrame(rows)
    os.makedirs(N.P('stage0'), exist_ok=True)
    p = N.P('stage0', 'c2_mask_anchor_E6m.csv')
    N.atomic_write_csv(p, N.to_status(df))
    s = df.status.value_counts().to_dict()
    N.atomic_write_json(N.P('stage0', 'c2_mask_anchor_E6m.json'), dict(counts=s, n=len(df)))
    N.write_receipt('E6n_s0_mask_anchor', [p], code=[__file__], **{'n_' + k: v for k, v in s.items()})
    print(json.dumps(dict(counts=s, n=len(df)), ensure_ascii=False))


if __name__ == '__main__':
    main()
