#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Z-MAP 后段 MCSE 加轮规划 (plan §6.4: MCSE > 0.05 个年化百分点 -> 按 MCSE 加到 256 / 512 / 1024, 不看收益)。
读 statistics/zmap_need_more_paths_post.csv (e6i_zmap_summary.py --post 写), 对每个 (段, 路线, 机制, 当前路径数)
取阶梯中最小的 L 使 n x (MCSE / 0.05)^2 <= L (且 L > n; n >= 1024 不再加), 路径编号接当前之后 (新 draw)。
输出 runtime/zmap_post_esc<k>_<seg>_<route>_<kind>_p<n>_n<add>.csv (only-list) 与 runtime/zmap_post_esc<k>_jobs.txt;
无需加轮时写空作业文件。用法: python3 e6i_zmap_escalate.py --round 1"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import math
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I

LADDER = (256, 512, 1024)
TARGET = 0.05
SEC_PER_PATH = 0.08          # 计时经验 (55–75 ms/路径; R1 K 槽位 ~170 ms) -> 只用于分片数
JOB_SEC = 600.0
CODE = '/mnt/sda2/lichenchen/code/project_core'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--round', type=int, required=True)
    a = ap.parse_args()
    rt = os.path.join(I.RES, 'runtime')
    p = os.path.join(I.RES, 'statistics', 'zmap_need_more_paths_post.csv')
    jobs = []
    rows = []
    if os.path.exists(p):
        d = pd.read_csv(p, low_memory=False)
        d = d[d.segment.isin(I.POST_SEGS)].copy()
        d['cfg'] = d.descriptor_id.str.replace(r'\|H\d+$', '', regex=True)
        g = d.groupby(['segment', 'route_id', 'kind', 'cfg']).agg(n=('n_paths', 'max'), mcse=('rand_net8_mcse', 'max'),
                                                                   did=('descriptor_id', 'first')).reset_index()
        tgt = []
        for r in g.itertuples():
            need = r.n * (r.mcse / TARGET) ** 2
            L = next((x for x in LADDER if x > r.n and x >= need), LADDER[-1] if r.n < LADDER[-1] else None)
            tgt.append(L)
        g['target'] = tgt
        g = g[g.target.notna()].copy()
        g['target'] = g.target.astype(int)
        g['add'] = g.target - g.n
        for (seg, route, kind, n, add), gg in g.groupby(['segment', 'route_id', 'kind', 'n', 'add']):
            tag = 'zmap_post_esc%d_%s_%s_%s_p%d_n%d' % (a.round, seg, route, kind, n, add)
            lst = os.path.join(rt, tag + '.csv')
            I.atomic_write_csv(lst, pd.DataFrame({'descriptor_id': gg.did.values}))
            k = int(min(24, max(1, math.ceil(len(gg) * add * SEC_PER_PATH / JOB_SEC))))
            for i in range(k):
                jobs.append('cd %s && taskset -c 96-191,288-383 python3 -u e6i_randoms.py --segment %s --route %s '
                            '--shard %d --nshard %d --kinds %s --path-start %d --npaths %d --only-list %s '
                            '--tag-suffix _pe%d > %s/logs/zesc_post%d_%s_%s_%s_p%d_%02d.log 2>&1'
                            % (CODE, seg, route, i, k, kind, n, add, lst, a.round, I.RES, a.round, seg, route, kind,
                               n, i))
            rows.append(dict(round=a.round, segment=seg, route=route, kind=kind, n_from=n, add=add,
                             n_configs=len(gg), n_shards=k))
    jf = os.path.join(rt, 'zmap_post_esc%d_jobs.txt' % a.round)
    open(jf, 'w').write('\n'.join(jobs) + ('\n' if jobs else ''))
    I.atomic_write_csv(os.path.join(I.RES, 'statistics', 'zmap_post_escalation_plan_r%d.csv' % a.round),
                       pd.DataFrame(rows))
    print('加轮 %d: %d 组 / %d 配置 / %d 作业 -> %s' % (a.round, len(rows), sum(r['n_configs'] for r in rows),
                                                  len(jobs), jf))


if __name__ == '__main__':
    main()
