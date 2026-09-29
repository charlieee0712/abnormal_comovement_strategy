# -*- coding: utf-8 -*-
"""E6k MC 增补队列（执行端补充 X15；plan §10.2）：读 results/<阶段>/mc_plan_<段>_*.csv（只含随机路径的离散度，不含真实账户），
对 topup > 0 的比较组（段 × 任务 × 机制）按 512 一批生成分片 rand <段> <任务> <机制> <起> 512，起 = 已有路径数、已有 + 512 …（上限 8,192）。
同一组若已有同名分片回执则跳过（重复运行安全）。"""
import sys
import glob
import os

import pandas as pd

import e6k_core as K


def main():
    phase, out = sys.argv[1], sys.argv[2]
    lines = []
    latest = {}
    for f in sorted(glob.glob(K.P('results', phase, 'mc_plan_*.csv'))):          # 每段只取最新一版规划
        latest[os.path.basename(f).split('_')[2]] = f
    for f in sorted(latest.values()):
        P = pd.read_csv(f)
        for r in P[P.topup > 0].itertuples():
            for p0 in range(int(r.have), int(r.target), 512):
                stem = '%s__%s__p%d_%d' % (r.task.split('|')[0], r.task.split('|')[1], p0, 512)
                rec = K.P('task_status', 'run_rand_%s_%s_%s.receipt.json' % (r.mechanism, r.segment, stem))
                if not os.path.exists(rec):
                    lines.append('rand %s %s %s %d 512' % (r.segment, r.task, r.mechanism, p0))
    lines = sorted(set(lines))
    with open(out, 'w') as fh:
        fh.write('\n'.join(lines) + ('\n' if lines else ''))
    print(len(lines), 'top-up shards', flush=True)


if __name__ == '__main__':
    main()
