# -*- coding: utf-8 -*-
"""E6l REPORT 生成器公共件（brief §9 / A10；纪律 56–63；E6k e6k_report 同式，路径改本轮）。
  - 每张表前一行表头块：主体 / 算子 / 分母 / 基准 / 子集 / 单位 / 日期 / H / 成本模型 / 支持 / 资本视图 / exposure / query_id（缺项即抛错）；
  - 数字与全称句由同一结构化查询产生：表与正文引用同一 query_id；query_id 跨文件唯一（reports/query_registry_E6l.json）；
  - 取绝对值的列须有同名带符号列（E6j #70 / #74；纪律 ㊻）；段均列名带 _segavg、单位后缀（纪律 57 / 58）由各生成器负责；
  - 单元格状态词：NaN 印空；'nan' / 'None' 等禁用状态词印 UNDEFINED（纪律 56）；
  - 扫描：禁用判词（协议 + brief §10 / 纪律 62："证伪 / 穷尽 / 饱和 / 到平台 / 改无可改" 等）、主机 / 账号 / 家目录 / 连接串，任一命中抛错。"""
import os
import re
import json

import pandas as pd

import e6l_core as L

HEAD_KEYS = ('主体', '算子', '分母', '基准', '子集', '单位', '日期', 'H', '成本模型', '支持', '资本视图', 'exposure', 'query_id')
FORBIDDEN = ('可交付', '已确证', '必须换核', '饱和', '穷尽', '到平台', '改无可改', '可以上线', '半样本外', '替代 E7', '替代E7', '证实', '证伪')
LEAK_PATTERNS = (r'\b\d{1,3}(?:\.\d{1,3}){3}\b', r'/home/', r'\.conda/envs/', r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
                 r'ssh\s+-p', 'pass' + 'word|pass' + 'wd|口令|密钥')
QID_FILE = L.P('reports', 'query_registry_E6l.json')


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
        cols = list(map(str, df.columns))
        for c in [c for c in cols if 'abs' in c.lower()]:
            cands = {c.replace('absmean', 'mean'), c.replace('absmean', 'signed'), c.replace('_abs', ''), c.replace('abs_', ''),
                     c.replace('abs', 'signed'), c.replace('p95abs', 'p95signed'), c.replace('maxabs', 'max'), c.replace('_abs_', '_')}
            if not (cands - {c}) & set(cols):
                raise RuntimeError('取绝对值的列 %s 缺同名带符号列：%s' % (c, query_id))
        self.qids[query_id] = dict(rows=len(df), cols=cols, head={k: str(v) for k, v in head.items()})
        hb = '｜'.join('%s=%s' % (k, head[k]) for k in HEAD_KEYS if k != 'query_id') + '｜query_id=%s' % query_id
        self.parts.append('> 表头：%s\n\n' % hb)
        lines = ['| ' + ' | '.join(cols) + ' |', '|' + '|'.join(['---'] * len(cols)) + '|']
        for _, r in df.iterrows():
            cells = []
            for v in r.values:
                if isinstance(v, float):
                    cells.append('' if pd.isna(v) else (float_fmt % v))
                else:
                    cells.append(L.txt(v).replace('|', '\\|'))
            lines.append('| ' + ' | '.join(cells) + ' |')
        self.parts.append('\n'.join(lines) + '\n\n')
        os.makedirs(L.P('results', 'full', 'query_tables'), exist_ok=True)
        L.atomic_write_csv(L.P('results', 'full', 'query_tables', '%s.csv' % query_id.replace('-', '_')), df)

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
        reg = json.load(open(QID_FILE, encoding='utf-8')) if os.path.exists(QID_FILE) else {}
        dup = [q for q in self.qids if q in reg and reg[q]['file'] != os.path.basename(path)]
        if dup:
            raise RuntimeError('query_id 跨文件重复 %s' % dup)
        for q, v in self.qids.items():
            reg[q] = dict(file=os.path.basename(path), **v)
        os.makedirs(os.path.dirname(QID_FILE), exist_ok=True)
        L.atomic_write_json(QID_FILE, reg)
        return L.atomic_write_text(path, self.text())
