#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 2 主账户合并与验收 (brief §0.2 ④: 父进程验收后写 DONE, 状态表求和 = 登记总数)。

每段每路线: 读 accounts/<seg>/<route>_<shard>.csv 与 *_rerun.csv (同一描述符 SUCCEEDED 优先, 否则取最后一次),
写 accounts/<seg>/merged_<route>.csv + merged_index.csv (描述符 -> 逐日序列所在 npz 与行号);
断言: 每 (段, 路线) 的描述符集合 == A0 该路线描述符集合; SUCCEEDED + NOT_APPLICABLE + FAILED_TECH == A0 计数;
全部通过才写 task_status/stage2_DONE.json 与 registry/stage2_status_table.csv。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import glob
import json
import time

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I

MAIN_ROUTES = ('FOURARM', 'RA', 'RC', 'RK', 'RL', 'RO', 'RR', 'RS', 'RT', 'RV', 'TPAIR')
EXTRA_ROUTES = ('M1', 'M2')          # 伴随行 (companion=True) 不计入 A0 登记数; 缺产物时跳过、不挡主 DONE


def main():
    t0 = time.time()
    post = "--post" in sys.argv[1:]          # Stage 3 技术修复: 后段合并 (默认推导段, 行为不变)
    SEGS = I.POST_SEGS if post else I.DERIV_SEGS
    stg = "stage3" if post else "stage2"
    sfx = "_post" if post else ""
    a0 = pd.read_csv(os.path.join(I.RES, 'registry', 'descriptors_A0.csv'), low_memory=False)
    status_rows, problems, extra_problems = [], [], []
    for seg in SEGS:
        od = os.path.join(I.RES, 'accounts', seg)
        idx_rows = []
        for route in MAIN_ROUTES + EXTRA_ROUTES:
            main_r = route in MAIN_ROUTES
            probs = problems if main_r else extra_problems
            want = set(a0.loc[a0.route_id == route, 'descriptor_id'])
            parts = []
            for f in sorted(glob.glob(os.path.join(od, '%s_[0-9][0-9]*.csv' % route))):
                if '_timing' in f:
                    continue
                d = pd.read_csv(f, low_memory=False)
                d['_src'] = os.path.basename(f)
                d['_order'] = 1 if f.endswith('_rerun.csv') else 0
                parts.append(d)
            if not parts:
                if main_r:
                    problems.append('%s %s: 无产物' % (seg, route))
                continue
            d = pd.concat(parts, ignore_index=True)
            d['_ok'] = (d.status == 'SUCCEEDED').astype(int)
            d = d.sort_values(['descriptor_id', '_ok', '_order']).drop_duplicates('descriptor_id', keep='last')
            comp = d['companion'].fillna(False).astype(bool) if 'companion' in d.columns else \
                pd.Series(False, index=d.index)
            base = d[~comp]
            got = set(base.descriptor_id)
            miss, extra = want - got, got - want
            if miss or extra:
                probs.append('%s %s: 缺 %d / 多 %d' % (seg, route, len(miss), len(extra)))
            cnt = base.status.value_counts().to_dict()
            n_s, n_na, n_f = cnt.get('SUCCEEDED', 0), cnt.get('NOT_APPLICABLE', 0), cnt.get('FAILED_TECH', 0)
            if n_s + n_na + n_f != len(want):
                probs.append('%s %s: 状态和 %d != A0 %d' % (seg, route, n_s + n_na + n_f, len(want)))
            if n_f:
                probs.append('%s %s: FAILED_TECH %d' % (seg, route, n_f))
            status_rows.append(dict(segment=seg, route=route, a0_count=len(want), succeeded=n_s,
                                    not_applicable=n_na, failed_tech=n_f,
                                    from_rerun=int((d._order == 1).sum()), companion_rows=int(comp.sum())))
            I.atomic_write_csv(os.path.join(od, 'merged_%s.csv' % route), d.drop(columns=['_ok', '_order']))
            # 逐日序列索引
            for src in d._src.unique():
                npz = os.path.join(od, src.replace('.csv', '.npz'))
                if not os.path.exists(npz):
                    continue
                with np.load(npz) as z:
                    ids = list(z['descriptor_id'])
                pos = {k: i for i, k in enumerate(ids)}
                for did in d.loc[(d._src == src) & (d.status == 'SUCCEEDED'), 'descriptor_id']:
                    if did in pos:
                        idx_rows.append(dict(descriptor_id=did, route=route, npz=os.path.basename(npz),
                                             row=pos[did]))
                    else:
                        probs.append('%s %s: %s 无逐日序列' % (seg, route, did))
        I.atomic_write_csv(os.path.join(od, 'merged_index.csv'), pd.DataFrame(idx_rows))
    st = pd.DataFrame(status_rows)
    I.atomic_write_csv(os.path.join(I.RES, 'registry', '%s_status_table.csv' % stg), st)
    print(st.to_string(index=False))
    stm = st[st.route.isin(MAIN_ROUTES)]
    tot = stm.groupby('segment')[['a0_count', 'succeeded', 'not_applicable', 'failed_tech']].sum()
    print(tot)
    for rt in EXTRA_ROUTES:
        sx = st[st.route == rt]
        if len(sx) == len(SEGS) and (sx.succeeded == sx.a0_count).all() and (sx.failed_tech == 0).all():
            I.atomic_write_json(os.path.join(I.RES, 'task_status', '%s%s_DONE.json' % (rt.lower(), sfx)), dict(
                stage=rt, totals=sx.to_dict('records'), accepted_at=time.strftime('%Y-%m-%d %H:%M:%S'),
                rule='非伴随行状态和 = A0 登记数; 伴随行另计'))
            print('%s DONE 写入' % rt)
        elif len(sx):
            print('%s 未完成 / 有问题: %s' % (rt, [p for p in extra_problems if (' %s:' % rt) in p][:5]))
    if problems:
        print('问题:', *problems[:30], sep='\n  ')
        sys.exit(1)
    I.atomic_write_json(os.path.join(I.RES, 'task_status', '%s_DONE.json' % stg), dict(
        stage='%s_main_accounts' % stg, segments=list(SEGS), routes=list(MAIN_ROUTES),
        totals=tot.reset_index().to_dict('records'), accepted_at=time.strftime('%Y-%m-%d %H:%M:%S'),
        rule='状态表求和 = A0 登记数 (M1/M2 另计)', elapsed_s=round(time.time() - t0, 1)))
    print('DONE 写入; %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
