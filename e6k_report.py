# -*- coding: utf-8 -*-
"""E6k REPORT 生成器公共件（brief W17 / W18 / §10；E6j e6j_report 同式，路径改本轮）。
  - 每张表前一行表头块：主体、算子、分母、基准、子集、单位、日期、H、成本模型、支持、资本视图、exposure、query_id（缺项即抛错）；
  - 数字 / 计数 / 全称句由同一结构化查询产生：表与正文引用同一 query_id；query_id 跨文件唯一（reports/query_registry_E6k.json）；
  - 取绝对值作门的量同时印带符号值（E6j #70 / #74）：表里有 abs 列时须有同名 signed 列（检查列名约定 *_abs* ↔ *_mean* / *_signed*）；
  - 扫描：禁用词（协议 + brief §10 判词）、主机地址 / 账号 / 家目录路径 / 连接串；任一命中抛错。"""
import os
import re
import json

import pandas as pd

import e6k_core as K

HEAD_KEYS = ('主体', '算子', '分母', '基准', '子集', '单位', '日期', 'H', '成本模型', '支持', '资本视图', 'exposure', 'query_id')
FORBIDDEN = ('可交付', '已确证', '必须换核', '饱和', '穷尽', '到平台', '改无可改', '可以上线', '半样本外', '替代 E7', '替代E7', '证实')
LEAK_PATTERNS = (r'\b\d{1,3}(?:\.\d{1,3}){3}\b', r'/home/', r'\.conda/envs/', r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
                 r'ssh\s+-p', r'password|passwd|口令|密钥')
QID_FILE = K.P('reports', 'query_registry_E6k.json')


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
        absc = [c for c in cols if 'abs' in c.lower()]
        for c in absc:
            cands = {c.replace('absmean', 'mean'), c.replace('absmean', 'signed'), c.replace('_abs', ''), c.replace('abs_', ''),
                     c.replace('abs', 'signed'), c.replace('p95abs', 'p95signed'), c.replace('maxabs', 'max')}
            if not (cands - {c}) & set(cols):
                raise RuntimeError('取绝对值的列 %s 缺同名带符号列（E6j #70；约定 absmean↔mean/signed、abs↔signed）：%s' % (c, query_id))
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
        reg = json.load(open(QID_FILE, encoding='utf-8')) if os.path.exists(QID_FILE) else {}
        dup = [q for q in self.qids if q in reg and reg[q]['file'] != os.path.basename(path)]
        if dup:
            raise RuntimeError('query_id 跨文件重复 %s' % dup)
        for q, v in self.qids.items():
            reg[q] = dict(file=os.path.basename(path), **v)
        os.makedirs(os.path.dirname(QID_FILE), exist_ok=True)
        K.atomic_write_json(QID_FILE, reg)
        return K.atomic_write_text(path, self.text())
