#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i C1 资本分解（B 后事后补充，2026-09-25（47 时间）；不改任何账户与登记读数）。
问题：C1 的 N250 − N100（固定 B）与 B16 − B8（固定 N）账户差，有多少来自"持仓名数 / 投入资金变多"（DEV 每只 min(1/n, 1%)、不归一 →
投入资金随持仓数上升），有多少来自"单位资金的超额变高"（选得更好）？
口径：逐 seed 行（部署视图 = 全日历 min(N, N_t)）的 net8_ann 与 pos_mean（平均投入资金）；单位资金超额 e = net8_ann / pos_mean。
对每个配对（同段、母体、q、评分口径、分配、seed）：Δ = net8_b − net8_a = (pos_b − pos_a)·e_a【资金部分】+ pos_b·(e_b − e_a)【单位资金超额部分】，恒等。
配对集合 = 严格交叉里逐 seed 共同可行日 ≥ 60 的配对（与 part3 §2 主表同一集合）；严格视图的逐日投入资金未保存，
所以分解只能在部署视图上做——严格视图的差（同一配对）并列给出，两者支持不同、数值不同。
输出 carried/summary/C1_T9_capital.csv（分段 x 对比 x 固定维）与 C1_T9_capital_pairs.csv（逐配对）。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_carried_summary as CSUM

OUT = CSUM.OUT
PAIRS = [('B16−B8', 'N=%d' % n, (n, 8), (n, 16)) for n in (100, 150, 250)] + \
        [('N250−N100', 'B=%d' % b, (100, b), (250, b)) for b in (8, 12, 16)]
KEY = ['segment', 'mother', 'q', 'scope', 'alloc', 'seed', 'contrast', 'fixed']


def main():
    t0 = time.time()
    strict = pd.read_csv(os.path.join(OUT, 'C1_strict_rows.csv'))
    ok = strict[(strict.common_days >= CSUM.MIN_COMMON) & strict.d.notna()]
    rows = []
    for seg in I.SEGMENTS:
        parts = CSUM.c1_files(seg)
        if not parts:
            continue
        d = pd.concat([x for x, _, _ in parts], ignore_index=True)
        cr = d[d.part == 'cross']
        for (seed, alloc, mn, qq, sc), g in cr.groupby(['seed', 'alloc', 'mother', 'q', 'scope']):
            cell = {(int(r_.N), int(r_.B)): r_ for r_ in g.itertuples()}
            for ctr, fixed, ca, cb in PAIRS:
                if ca not in cell or cb not in cell:
                    continue
                a, b = cell[ca], cell[cb]
                if not (a.pos_mean > 0 and b.pos_mean > 0):
                    continue
                ea, eb = a.net8_ann / a.pos_mean, b.net8_ann / b.pos_mean
                rows.append(dict(segment=seg, mother=mn, q=qq, scope=sc, alloc=alloc, seed=seed, contrast=ctr, fixed=fixed,
                                 net8_a=a.net8_ann, net8_b=b.net8_ann, d_deploy=b.net8_ann - a.net8_ann,
                                 pos_a=a.pos_mean, pos_b=b.pos_mean, held_a=a.held_mean, held_b=b.held_mean,
                                 e_a=ea, e_b=eb, cap_part=(b.pos_mean - a.pos_mean) * ea, sel_part=b.pos_mean * (eb - ea)))
    P = pd.DataFrame(rows)
    P = P.merge(ok[KEY + ['d', 'common_days']].rename(columns={'d': 'd_strict'}), on=KEY, how='inner')
    I.atomic_write_csv(os.path.join(OUT, 'C1_T9_capital_pairs.csv'), P)
    g = P.groupby(['segment', 'scope', 'alloc', 'contrast', 'fixed']).agg(
        n_pairs=('d_deploy', 'size'), d_strict=('d_strict', 'mean'), d_deploy=('d_deploy', 'mean'),
        cap_part=('cap_part', 'mean'), sel_part=('sel_part', 'mean'), pos_a=('pos_a', 'mean'), pos_b=('pos_b', 'mean'),
        held_a=('held_a', 'mean'), held_b=('held_b', 'mean'), e_a=('e_a', 'median'), e_b=('e_b', 'median')).reset_index()
    g['cap_share'] = g.cap_part / g.d_deploy
    g['e_ratio'] = g.e_b / g.e_a
    I.atomic_write_csv(os.path.join(OUT, 'C1_T9_capital.csv'), g)
    m = g[(g.scope == 'frozen') & (g.alloc == 'equal')]
    for r_ in m.itertuples():
        print('  %s %s %s: 配对 %d, 严格 %+.3f, 部署 %+.3f = 资金 %+.3f + 单位资金超额 %+.3f; 资金 %.2f→%.2f, 持仓 %.1f→%.1f, e %.1f→%.1f' % (
            r_.segment, r_.contrast, r_.fixed, r_.n_pairs, r_.d_strict, r_.d_deploy, r_.cap_part, r_.sel_part,
            r_.pos_a, r_.pos_b, r_.held_a, r_.held_b, r_.e_a, r_.e_b))
    print('C1 资本分解: %d 配对; %.0fs' % (len(P), time.time() - t0))


if __name__ == '__main__':
    main()
