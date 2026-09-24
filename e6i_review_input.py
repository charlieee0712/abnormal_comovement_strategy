#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i_REVIEW_input.md (brief §15): 每份 REPORT 的每张主表 —— 所在节 / 汇总算子 / 分母及构成 / 基准 / 子集 / 单位 / 日期支持 / H /
成本 / 支持口径 / 资本口径 / 行数; 另列全部 query_id 及其现算文本 (供规划 session 复核时逐条回查)。
从 reports/*.md 的十项表头行机器解析, 不手抄。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import re
import sys
import glob

import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I

R = I.RES
KEYS = ('汇总算子', '分母及构成', '基准', '子集', '单位', '日期支持', 'H', '成本', '支持口径', '资本口径')
REPORTS = ('E6i_REPORT_R0.md', 'E6i_REPORT_part1.md', 'E6i_REPORT_part1b.md', 'E6i_REPORT_part2.md', 'E6i_REPORT_part3.md')


def parse(path):
    lines = open(path, encoding='utf-8').read().split('\n')
    sec = ''
    out = []
    for i, ln in enumerate(lines):
        if ln.startswith('#'):
            sec = ln.lstrip('#').strip()
        if ln.startswith('> **汇总算子**'):
            rec = dict(section=sec, line=i + 1)
            for k in KEYS:
                m = re.search(r'\*\*%s\*\*：(.*?)(?: ｜ \*\*|$)' % re.escape(k), ln)
                rec[k] = m.group(1).strip() if m else ''
            j = i + 1
            while j < len(lines) and not lines[j].startswith('|'):
                j += 1
            n = 0
            if j < len(lines):
                k2 = j + 2
                while k2 < len(lines) and lines[k2].startswith('|'):
                    n += 1
                    k2 += 1
            rec['rows'] = n
            out.append(rec)
    return out


def main():
    md = ['# E6i_REVIEW_input（逐表清单与 query_id；由报告表头机器解析）\n',
          '用途：规划 session 写 E6i_REVIEW 时逐表核对"数字 / 算子 / 分母 / 基准 / 子集"。每行 = 报告里一张表（十项表头原文）。'
          '数字本身在报告正文与 `reports/*_tables/*.csv`；query_id 文本是生成时现算的句子。\n']
    for rp in REPORTS:
        p = os.path.join(R, 'reports', rp)
        if not os.path.exists(p):
            md.append('## %s\n\n_（尚未生成）_\n' % rp)
            continue
        recs = parse(p)
        md.append('## %s（%d 张表）\n' % (rp, len(recs)))
        md.append('| # | 节 | 行号 | 汇总算子 | 分母及构成 | 基准 | 子集 | 单位 | H | 成本 | 行数 |')
        md.append('|---|---|---|---|---|---|---|---|---|---|---|')
        for i, r in enumerate(recs, 1):
            md.append('| %d | %s | %d | %s | %s | %s | %s | %s | %s | %s | %d |' % (
                i, r['section'].replace('|', '/'), r['line'], r['汇总算子'].replace('|', '/'), r['分母及构成'].replace('|', '/'),
                r['基准'].replace('|', '/'), r['子集'].replace('|', '/'), r['单位'].replace('|', '/'), r['H'], r['成本'], r['rows']))
        md.append('')
    qs = []
    for f in sorted(glob.glob(os.path.join(R, 'reports', '*_tables', 'query_ids_*.csv'))):
        d = pd.read_csv(f)
        d['file'] = os.path.relpath(f, R)
        qs.append(d)
    if qs:
        Q = pd.concat(qs, ignore_index=True)
        md.append('## query_id（%d 条）\n' % len(Q))
        md.append('| 文件 | query_id | 现算文本 |')
        md.append('|---|---|---|')
        for r in Q.itertuples():
            md.append('| %s | %s | %s |' % (r.file, r.query_id, str(r.text).replace('|', '/')))
    out = os.path.join(R, 'reports', 'E6i_REVIEW_input.md')
    open(out, 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    print('REVIEW_input: %s' % out)


if __name__ == '__main__':
    main()
