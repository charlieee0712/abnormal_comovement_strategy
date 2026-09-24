#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""焦点行修复后的小检查 (RR replace_cr5 / RO gap 状态 / RS weak_or_dispersed): 每类取 A0 里的真实描述符行
   建掩码; 断言 all_on == 母体 B 逐格, all_off / real_state / new 与 B 的差异格数为正且 real_state 位于两者之间。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import json

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6i_stage2 as S2


def main():
    seg = sys.argv[1]
    FE.build_catalog()
    FE.CATALOG_IDS = {m['member_id'] for m in FE.CATALOG}
    I.set_protected_members(FE.protected_ids())
    dd = pd.read_csv(os.path.join(I.RES, 'registry', 'descriptors_A0.csv'), low_memory=False)
    fo = dd[(dd.role == 'FOCAL_NEW') & dd.route_id.isin(['RR', 'RO', 'RS']) & (dd.H == 5)]
    S = I.seg_i(seg, warm=False)
    RN = S2.Runner(S)
    out, ok = [], True
    for route in ('RR', 'RO', 'RS'):
        sub = fo[fo.route_id == route]
        for mn in sub.mother_id.unique():
            pick = sub[sub.mother_id == mn]
            if route == 'RR':
                pick = pick.head(2)
            else:
                st0 = pick.direction_role.iloc[0] if route == 'RS' else pick.policy.iloc[0]
                pick = pick[(pick.direction_role if route == 'RS' else pick.policy) == st0]
                pick = pick[pick.member_id == pick.member_id.iloc[0]]
            M = RN.mother(mn)
            for r in pick.to_dict('records'):
                m, _, info = RN.build(r)
                diff = int((m != M.B).sum())
                out.append(dict(route=route, mother=mn, desc=r['descriptor_id'], arm=r['strength'],
                                n_diff_vs_parent=diff, n_mean=float(m.sum(1).mean()),
                                parent_n_mean=float(M.B.sum(1).mean()), note=info.get('note', '')))
                if str(r['strength']) == 'all_on' and diff != 0:
                    ok = False
    d = pd.DataFrame(out)
    print(d.to_string(index=False))
    for (rt, mn), g in d[d.route.isin(['RO', 'RS'])].groupby(['route', 'mother']):
        a = g.set_index('arm').n_diff_vs_parent
        if not (a.get('all_on', 1) == 0 and a.get('all_off', 0) > 0 and
                0 < a.get('real_state', 0) < a.get('all_off', 0)):
            ok = False
            print('!! 状态臂顺序不符', rt, mn, dict(a))
    I.atomic_write_json(os.path.join(I.RES, 'checks', 'focal_fix_check_%s.json' % seg),
                        dict(ok=ok, rows=out))
    print('OK' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
