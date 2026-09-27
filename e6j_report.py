# -*- coding: utf-8 -*-
"""E6j REPORT 生成器公共件（brief §13 / W17 / W18；plan §10.7）。
  - 每张表前一行表头块：主体、算子、分母、基准、子集、单位、日期、H、成本模型、支持、资本视图、exposure、query_id（缺项 FAIL）；
  - 数字 / 计数 / 全称句由同一结构化查询产生：Q(query_id, 函数) 注册，表与正文引用同一 query_id；query_id 跨文件唯一；
  - 扫描：禁用词（E6i brief §15 + 协议）、主机地址 / 账号 / 家目录路径 / 连接串；任一命中 FAIL。"""
import os
import re
import json

import pandas as pd

import e6j_core as J

HEAD_KEYS = ('主体', '算子', '分母', '基准', '子集', '单位', '日期', 'H', '成本模型', '支持', '资本视图', 'exposure', 'query_id')
FORBIDDEN = ('可交付', '已确证', '必须换核', '饱和', '穷尽', '到平台', '改无可改', '可以上线')
LEAK_PATTERNS = (r'\b\d{1,3}(?:\.\d{1,3}){3}\b', r'/home/', r'\.conda/envs/', r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
                 r'ssh\s+-p', r'password|passwd|口令|密钥')
QID_FILE = os.path.join(J.RES, 'reports', 'query_registry.json')


class Report(object):
    def __init__(self, name):
        self.name = name
        self.parts = []
        self.qids = {}

    def h(self, level, text):
        self.parts.append('%s %s\n' % ('#' * level, text))

    def p(self, text):
        self.parts.append(text.rstrip() + '\n')

    def table(self, df, head, query_id, float_fmt='%.4g'):
        miss = [k for k in HEAD_KEYS if k not in head and k != 'query_id']
        if miss:
            raise RuntimeError('表头缺项 %s（%s）' % (miss, query_id))
        if query_id in self.qids:
            raise RuntimeError('query_id 重复 %s' % query_id)
        self.qids[query_id] = dict(rows=len(df), cols=list(map(str, df.columns)))
        hb = '｜'.join('%s=%s' % (k, head[k]) for k in HEAD_KEYS if k != 'query_id') + '｜query_id=%s' % query_id
        self.parts.append('> 表头：%s\n\n' % hb)
        cols = list(map(str, df.columns))
        lines = ['| ' + ' | '.join(cols) + ' |', '|' + '|'.join(['---'] * len(cols)) + '|']
        for _, r in df.iterrows():
            cells = []
            for v in r.values:
                if isinstance(v, float):
                    cells.append('' if pd.isna(v) else (float_fmt % v))
                else:
                    cells.append(str(v).replace('|', '\\|'))
            lines.append('| ' + ' | '.join(cells) + ' |')
        self.parts.append('\n'.join(lines) + '\n\n')

    def text(self):
        return '\n'.join(self.parts)

    def scan(self):
        t = self.text()
        hits = [w for w in FORBIDDEN if w in t]
        leaks = [p for p in LEAK_PATTERNS if re.search(p, t, flags=re.I)]
        return hits, leaks

    def write(self, path):
        hits, leaks = self.scan()
        if hits or leaks:
            raise RuntimeError('REPORT 扫描 FAIL：禁用词 %s；泄露模式 %s' % (hits, leaks))
        reg = json.load(open(QID_FILE)) if os.path.exists(QID_FILE) else {}
        dup = [q for q in self.qids if q in reg and reg[q]['file'] != os.path.basename(path)]
        if dup:
            raise RuntimeError('query_id 跨文件重复 %s' % dup)
        for q, v in self.qids.items():
            reg[q] = dict(file=os.path.basename(path), **v)
        J.atomic_write_json(QID_FILE, reg)
        return J.atomic_write_text(path, self.text())
