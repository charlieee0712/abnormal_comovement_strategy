#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i: 建全部成员的 NS 分位缓存 (hi / lo) + 标签锚 (alin_5 == 源标签)。推导段。

用法: python3 e6i_s1_pct.py --segment 2015-2018 --axes T,K
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6i_s1base as SB


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--axes', default='T,K,V,R,O,C,A,S')
    ap.add_argument('--label_anchor', action='store_true')
    a = ap.parse_args()
    assert a.segment in I.DERIV_SEGS or I.post_allowed(a.segment)   # Stage 3 技术修复: 后段需 E6i 记录 B
    t0 = time.time()
    FE.build_catalog()
    I.set_protected_members(FE.protected_ids())
    post = a.segment in I.POST_SEGS
    S = I.seg_i(a.segment, warm=False)
    rows = []
    if a.label_anchor:
        r = SB.label_anchor(S)
        I.atomic_write_json(os.path.join(I.RES, 'checks', 'label_anchor_%s.json' % a.segment),
                            dict(segment=a.segment, **r, ok=bool(r['missing'] == 0 and
                                                                 r['max_abs_bp'] <= 1e-9)))
        print('标签锚 alin_5 vs 源: %s' % r, flush=True)
    axes = set(a.axes.split(','))
    todo = [m for m in FE.CATALOG if m['axis_id'] in axes]
    if post:   # 后段只建批准成员 (+ 源键) 的分位缓存
        todo = [m for m in todo if (not I.is_protected_member(m['member_id']))
                or m['member_id'] in I._APPROVAL_I['members']]
    for i, m in enumerate(todo):
        ts = time.time()
        try:
            hi = SB.pct_member(S, m['member_id'])
            SB.pct_member(S, m['member_id'], direction='lo')
            fin = np.isfinite(hi)
            rows.append(dict(member_id=m['member_id'], status='SUCCEEDED',
                             sec=round(time.time() - ts, 1),
                             pct_cov_pool0=float(fin[S.p0c].mean())))
        except Exception as e:
            rows.append(dict(member_id=m['member_id'], status='FAILED_TECH',
                             error='%s: %s' % (type(e).__name__, str(e)[:150])))
        if (i + 1) % 10 == 0:
            print('  %d/%d %.0fs' % (i + 1, len(todo), time.time() - t0), flush=True)
    d = pd.DataFrame(rows)
    tag = a.axes.replace(',', '')
    I.atomic_write_csv(os.path.join(I.RES, 'runtime', 'pct_%s_%s.csv' % (a.segment, tag)), d)
    nf = int((d.status != 'SUCCEEDED').sum())
    print('[%s %s] pct 缓存 %d 成功 / %d 失败; %.0fs' % (a.segment, a.axes,
                                                     int((d.status == 'SUCCEEDED').sum()), nf,
                                                     time.time() - t0))
    sys.exit(1 if nf else 0)


if __name__ == '__main__':
    main()
