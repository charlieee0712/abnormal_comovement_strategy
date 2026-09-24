#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i part1 事实块生成器: 每个问题 (Q1-Q8, Q12 账户部分, Q13-Q15) 的计数 / 中位 / 占比句全部由表计算并带 query_id,
写 reports/part1_facts.md (供叙述引用) 与 reports/part1_tables/query_ids_part1.csv。叙述另写, 只引用这里的 query_id。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import re
import sys
import json

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I

R = I.RES
TAB = os.path.join(R, 'reports', 'part1_tables')
QIDS = []
Q_ROUTES = {'Q1': ('RT', 'TPAIR'), 'Q2': ('RK',), 'Q3': ('RV',), 'Q4': ('RO',), 'Q5': ('RR',), 'Q6': ('RC',),
            'Q7': ('RL',), 'Q13': ('RA',), 'Q14': ('RS',), 'Q15': ('FOURARM',)}
Q_TEXT = {'Q1': 'T：活动水平 / 不稳定 / 趋势 / 事件前基线', 'Q2': 'K：价格响应分量、点态倒数、ROS、残差',
          'Q3': 'V：保留集风险（VETO / SOFT / ADD）', 'Q4': 'O：保留集昼夜结构与焦点状态', 'Q5': 'R：同人数 SWAP、轻量 R 腿、收益焦点替换',
          'Q6': 'C：A06 核心槽位与 R1/R2/A08 的 CVR 焦点替换', 'Q7': '摩擦：边缘成本替换与轻摩擦否决',
          'Q13': 'A：事件基线 / 峰衰减 / 同预算换入', 'Q14': 'S：同行状态下的条件换入与焦点', 'Q15': '四臂交互'}


def q(qid, text):
    QIDS.append(dict(query_id=qid, text=re.sub(r'\s+', ' ', text)))
    return '%s〔%s〕' % (text, qid)


def f3(x):
    return '%+.3f' % x if np.isfinite(x) else 'NA'


def main():
    P = pd.read_csv(os.path.join(TAB, 'descriptor_panel.csv'), low_memory=False)
    P = P[~P.companion.astype(bool)]
    zs = []
    for s in I.DERIV_SEGS:
        f = os.path.join(R, 'statistics', 'zmap_summary_%s.csv' % s)
        if os.path.exists(f):
            z = pd.read_csv(f, low_memory=False)
            z['seg'] = s[2:4] + '-' + s[-2:]
            zs.append(z)
    Z = pd.concat(zs, ignore_index=True) if zs else pd.DataFrame()
    L = ['# E6i part1 事实块（全部由表计算；叙述只引用 query_id）\n']
    for Qn, routes in Q_ROUTES.items():
        g = P[P.route_id.isin(routes)]
        if not len(g):
            continue
        L.append('## %s %s\n' % (Qn, Q_TEXT[Qn]))
        n = len(g)
        ci = g['cix0_full'].astype(str).isin(['True', 'true', '1'])
        d = g['d_full']
        L.append('- ' + q('%s-N' % Qn, '描述符 %d 个（路线 %s）；full 子−母中位 %s、正值占比 %.1f%%；两段中位 %s / %s' % (
            n, '/'.join(routes), f3(d.median()), 100 * (d > 0).mean(), f3(g['d_10-14'].median()),
            f3(g['d_15-18'].median()))))
        L.append('- ' + q('%s-CI' % Qn, 'NW(lag H) 95%% 区间排除 0 且为正 %d 个、为负 %d 个（零增量下约 %.0f 个为随机，正负各半）' % (
            int((ci & (d > 0)).sum()), int((ci & (d < 0)).sum()), 0.05 * n)))
        if 'bdlo_full' in g:
            L.append('- ' + q('%s-BAND' % Qn, 'need 域同步带（2,000 次 bootstrap，块 20）排除 0：为正 %d 个、为负 %d 个' % (
                int((g.bdlo_full > 0).sum()), int((g.bdhi_full < 0).sum()))))
        sv = g['state_full'].value_counts()
        L.append('- ' + q('%s-STATE' % Qn, '状态词（δ=0.25）：' + '；'.join('%s %d' % (k, int(v)) for k, v in sv.items())))
        same = (np.sign(g['d_10-14']) == np.sign(g['d_15-18']))
        L.append('- ' + q('%s-SIGN' % Qn, '两段同号 %.1f%%（同为正 %d、同为负 %d）' % (
            100 * same.mean(), int(((g['d_10-14'] > 0) & (g['d_15-18'] > 0)).sum()),
            int(((g['d_10-14'] < 0) & (g['d_15-18'] < 0)).sum()))))
        for k in ('10-14', '15-18'):
            c = 'd_vs_core_matchN_%s' % k
            if c in g:
                L.append('- ' + q('%s-SAMEN-%s' % (Qn, k), '%s 子−同人数核心 中位 %s、正值占比 %.1f%%；子−母 %s' % (
                    k, f3(g[c].median()), 100 * (g[c] > 0).mean(), f3(g['d_%s' % k].median()))))
        if len(Z):
            for k in ('10-14', '15-18'):
                zz = Z[(Z.seg == k) & Z.route_id.isin(routes) & (Z.kind == 'basic')]
                if len(zz):
                    L.append('- ' + q('%s-ZMAP-%s' % (Qn, k), '%s Z-MAP（basic）真实−随机均值 中位 %s、>0 占比 %.1f%%、'
                                                           'tail<0.05 占比 %.1f%%（%d 行）' % (
                        k, f3(zz.d_real_minus_rand.median()), 100 * (zz.d_real_minus_rand > 0).mean(),
                        100 * (zz.diagnostic_tail_fraction < 0.05).mean(), len(zz))))
        by_m = g.groupby('mother_id').d_full.agg(['size', 'median', lambda x: (x > 0).mean()])
        L.append('- ' + q('%s-MOTHER' % Qn, '按母体（full 中位 / 正值占比）：' + '；'.join(
            '%s %s / %.0f%%' % (m, f3(r['median']), 100 * r['<lambda_0>']) for m, r in by_m.iterrows())))
        by_h = g.groupby('H').d_full.median()
        L.append('- ' + q('%s-H' % Qn, '按 H（full 中位）：' + '；'.join('H%d %s' % (int(h), f3(v)) for h, v in by_h.items())))
        by_r = g.groupby(['role', 'strength']).d_full.median()
        L.append('- ' + q('%s-STR' % Qn, '按角色 x 强度（full 中位）：' + '；'.join(
            '%s %s %s' % (a, b, f3(v)) for (a, b), v in by_r.items())[:900]))
        L.append('')
    open(os.path.join(R, 'reports', 'part1_facts.md'), 'w', encoding='utf-8').write('\n'.join(L))
    pd.DataFrame(QIDS).to_csv(os.path.join(TAB, 'query_ids_part1.csv'), index=False)
    print('facts: %d query_id' % len(QIDS))


if __name__ == '__main__':
    main()
