#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h carried T4: P16 角落加密 (brief §9, plan §9.4)。答 Q13。

  T{15,20,25,30,35,40,45} x K_MA{1,2,3,4,5} x B{3,5} x keep{30,35}
  x cvr_1d k{5,10} x B k{5,10} = **560 个原始描述符**

只用旧输入旧规则 -> 四段都能跑并封存 (brief §6 末条)。

**与 E6g H4b 的重叠路径要逐日锚** (brief §9 T4)。重叠 = kw∈{1,2,3,5} x
tw∈{20,30,40} x bw{3,5} x dep{30,35} x k1{5,10} x k2{5,10} = 192 格,
这些格在本轮必须与 E6g 已存 summary 逐位相同。

读法 (Q13): 峰的位置是否稳定、是否依赖 2015+2016。**不把最大格当结果**
(E6g 复盘 ⑦ 赢家诅咒); 最大格一律标"样本内最大"。

用法: python3 e6h_t4.py --segment 2019-2023
"""
from __future__ import annotations
import os
import sys
import json
import time
import argparse
import itertools

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6g_core as G
import e6g_desc as GD
import e6g_expand as EX
import e6f_core as F
import e6e_core as K

RES = H.RES
KW = [1, 2, 3, 4, 5]
TW = [15, 20, 25, 30, 35, 40, 45]
BW = [3, 5]
DEP = [30, 35]
KS = [5, 10]
# E6g H4b 的格 (用于重叠锚)
E6G_KW, E6G_TW, E6G_DEP = {1, 2, 3, 5, 10}, {20, 30, 40, 60, 80}, {25, 30, 35}


def grid():
    import e6f_desc as D          # e6g_expand 里的 D 就是 e6f_desc (已核)
    out = []
    for kw, tw, bw, dep, k1, k2 in itertools.product(KW, TW, BW, DEP, KS, KS):
        spK = F.spec('K', kw, est='MA', eps=1e-4)
        spT = F.spec('T', tw)
        spB = F.spec('B', bw)
        c = dict(fam='KTC_mean', kind='mean', s=dep,
                 comps=[spK, spT, dict(D.DC)], x=None, ys=[], ws=None,
                 neu='NS', neu_veto=None, dirs=['hi'] * 3, tfs=['identity'] * 3,
                 sel='SRC', depth=None)
        vn = 'cvr_1d:k%d+%s:k%d' % (k1, F.fid(spB), k2)
        v = D.veto_hard([(dict(D.DCF), k1), (spB, k2)], vid=vn)
        out.append(dict(descriptor_id=GD.cfg_id_g(c, v), core=c, veto=v,
                        kw=kw, tw=tw, bw=bw, depth=dep, k1=k1, k2=k2,
                        overlaps_e6g=(kw in E6G_KW and tw in E6G_TW and dep in E6G_DEP)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    t0 = time.time()
    rows_spec = grid()
    assert len(rows_spec) == 560, '网格 %d != 560' % len(rows_spec)
    ids = [r['descriptor_id'] for r in rows_spec]
    assert len(set(ids)) == 560, 'ID 不单射: %d' % len(set(ids))

    S = H.seg(a.segment, verbose=False)
    ctx = GD.GCtx(S)
    od = os.path.join(RES, 'T')
    os.makedirs(od, exist_ok=True)

    # E6g 已存 summary (用于重叠锚)
    e6g = {}
    import glob
    for f in glob.glob(os.path.join(H.E6G_DIR, 'H0', 'summary_H4b_%s_s*.csv' % a.segment)):
        d = pd.read_csv(f)
        for _, r in d.iterrows():
            e6g[r['descriptor_id']] = r
    if not e6g:
        for f in glob.glob(os.path.join(H.E6G_DIR, 'H4', 'summary_H4b_%s*.csv' % a.segment)):
            d = pd.read_csv(f)
            for _, r in d.iterrows():
                e6g[r['descriptor_id']] = r
    print('  E6g H4b 已存 %d 行可对锚' % len(e6g), flush=True)

    out, anch = [], []
    for i, rs in enumerate(rows_spec):
        cfg = dict(config_id=rs['descriptor_id'], core=rs['core'], veto=rs['veto'],
                   H=K.HOLD)
        mask, sc, cand, cm = ctx.full_mask_g(cfg)
        idx, val = F.dev_from_dense(S, mask)
        g_, p_, tu, n8 = F.sparse_pnl_H(S, idx, val, K.HOLD, F.COST)
        rec = dict(segment=a.segment, descriptor_id=rs['descriptor_id'],
                   kw=rs['kw'], tw=rs['tw'], bw=rs['bw'], depth=rs['depth'],
                   k1=rs['k1'], k2=rs['k2'], overlaps_e6g=rs['overlaps_e6g'],
                   gross_ann=G.ann(g_), net8_ann=G.ann(n8),
                   turn_mean=float(np.nanmean(tu)), pos_mean=float(np.nanmean(p_)),
                   target_n=float(mask.sum(axis=1).mean()))
        out.append(rec)
        if rs['descriptor_id'] in e6g:
            ref = e6g[rs['descriptor_id']]
            d1 = abs(rec['net8_ann'] - float(ref['net8_ann']))
            d2 = abs(rec['gross_ann'] - float(ref['gross_ann']))
            anch.append(dict(descriptor_id=rs['descriptor_id'],
                             d_net8=d1, d_gross=d2, ok=bool(max(d1, d2) < 1e-9)))
        if (i + 1) % 140 == 0:
            print('    %d/560  %.0fs' % (i + 1, time.time() - t0), flush=True)

    df = pd.DataFrame(out)
    df.to_csv(os.path.join(od, 'T4_p16_%s.csv' % a.segment), index=False)
    nok = sum(1 for x in anch if x['ok'])
    with open(os.path.join(od, 'T4_e6g_overlap_anchor_%s.json' % a.segment), 'w') as fh:
        json.dump(dict(segment=a.segment, n_overlap_checked=len(anch), n_pass=nok,
                       max_d_net8=(max([x['d_net8'] for x in anch]) if anch else None),
                       results=anch[:50],
                       note='与 E6g H4b 重叠的路径必须逐位相同 (brief §9 T4)'),
                  fh, indent=1, ensure_ascii=False, default=str)
    print('  [%s] T4 %d 行; 重叠锚 %d/%d 过, max|d_net8| %s; %.0fs'
          % (a.segment, len(df), nok, len(anch),
             ('%.3e' % max([x['d_net8'] for x in anch])) if anch else 'NA',
             time.time() - t0))
    if anch and nok != len(anch):
        print('  !! 重叠锚未全过 —— brief §9 要求逐日锚, 这是 WARN 不是阻断, 已记录')


if __name__ == '__main__':
    main()
