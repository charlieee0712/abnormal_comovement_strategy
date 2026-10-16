# -*- coding: utf-8 -*-
"""E6m 阶段 S 交付（brief §5 S4；附录 D-5 / D-8；E6l 交付件同构）。
  review   reports/E6m_REVIEW_input.md：交付件索引——每个文件 `相对路径`（sha256 前 16）、行数 / 体积，分组（报告 / query 表 / 固定表 / 统计与政策 /
           登记与授权 / 封存与门 / 代码与登记 / 副本包 manifest）；reports/E6m_MIRROR.md5：md5  sha256  RD  路径（RD = 本轮结果目录）
  copy     闭包门 all_pass 之后：复制交付件到 handoff/E6m/stageS_<时间>/ 并写 HANDOFF_SHA256.txt，复制后逐件重算 sha（0 不符才算交付）；
           大体积账户 / 随机 / 名单不进交接目录（在副本包 P1 / P2 与结果目录里）。
不读任何数值；只列文件与 sha。"""
import e6j_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time
import shutil
import hashlib
import argparse

import e6m_core as M

HANDOFF = os.path.join(M.RUNS, 'handoff', 'E6m')
GROUPS = [
    ('报告', ['reports/*.md']),
    ('query 表', ['reports/queries_full/*.csv', 'reports/queries_deriv/*.csv']),
    ('固定表', ['reports/fixed_full/*.csv', 'reports/fixed_deriv/*.csv']),
    ('报告附表', ['reports/tables/*.csv']),
    ('统计与政策', ['results/full/*.csv', 'results/full/bootstrap/*.csv', 'results/deriv/*.csv', 'results/full/decomp/*.csv', 'results/full/b4/*.csv',
               'results/full/b5/*.csv', 'results/full/b6/*.csv', 'results/full/aux_status/*.csv', 'results/full/continuous/*.csv', 'results/mc/*.csv']),
    ('登记与授权', ['registry/*.csv', 'registry/*.json', 'registration/*.json', 'registration/*.csv']),
    ('Stage 0 S', ['stage0_S/**/*.csv', 'stage0_S/**/*.json', 'stage0_S/**/*.md']),
    ('封存与门', ['seal_*.json', 'closure_gate_stageS.*', 'stageN/B3_anchor_status_S.json']),
    ('代码与登记', ['stageN/code_change_register_stageS_dev.md', 'stageN/STAGE_S_IMPL_PLAN.md', 'stageN/limit_register_stageS_draft.md',
               'stageN/E6m_stageS_decisions_*.md']),                    # 代拟决定记录（2026-10-11 起；待决策端追认）
    ('副本包 manifest', ['replica/replica_manifest_*.json']),
    ('补充件 S1', ['supp/S1/supp_S1_manifest.json', 'supp/S1/supp_S1_summary.csv', 'supp/S1/**/facts_aux*.csv']),     # 补丁十九（用户 2026-10-12 定）
]


def collect():
    W = M.work()
    out = []
    for g, pats in GROUPS:
        fs = set()
        for p in pats:
            fs |= set(f for f in glob.glob(os.path.join(W, p), recursive=True) if os.path.isfile(f))
        out.append((g, sorted(os.path.relpath(f, W) for f in fs)))
    return out


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def review():
    W = M.work()
    L = ['# E6m REVIEW_input —— 阶段 S 交付件索引（执行端生成；只列文件与 sha，不含任何读数）', '',
         '用途：协议复核（决策端 VERIFY brief 探针表由脚本生成；执行端 §C + V；决策端 D + REVIEW）。每行 `相对路径`（sha256 前 16）；RD = 本轮结果目录。', '']
    mirror = ['# E6m_MIRROR.md5（md5  sha256  位置  文件）']
    n = 0
    for g, fs in collect():
        L += ['## %s（%d）' % (g, len(fs)), '']
        for f in fs:
            p = os.path.join(W, f)
            s = M.sha_file(p)
            L.append('- `%s`（%s）%s' % (f, s[:16], '' if not f.endswith('.csv') else '，%d 行' % max(sum(1 for _ in open(p, 'rb')) - 1, 0)))
            mirror.append('%s  %s  RD  %s' % (md5(p), s, f))
            n += 1
        L.append('')
    p1, p2 = M.P('reports', 'E6m_REVIEW_input.md'), M.P('reports', 'E6m_MIRROR.md5')
    M.atomic_write_text(p1, '\n'.join(L) + '\n')
    M.atomic_write_text(p2, '\n'.join(mirror) + '\n')
    return p1, p2, n


DOCS = (('E6m_limit_register.md', '# E6m 限制登记（交付版）', ('stageN/limit_register_stageS_draft.md',)),
        ('E6m_lessons_delta.md', '# E6m 经验增量（lessons_delta）', ('stageN/lessons_stageN.md', 'stageN/lessons_N8.md', 'stageN/lessons_stageS.md')),
        ('E6m_code_change_register.md', '# E6m 代码变更登记（交付版）', ('stageN/code_change_register_stageN.md', 'stageN/code_change_register_N8.md',
                                                                  'stageN/code_change_register_stageS_dev.md')))
NOTES = 'E6m_REVIEW_input_notes.md'
SKELETON_MARK = 'NOTES_SKELETON'


def docs(out=None):
    """brief §9 交付文档进 reports/（out 只给冒烟测试用）：限制登记 / 经验增量 / 代码变更登记，各由 stageN 原件拼成，逐件注明来源与 sha（原件不改）。"""
    out = out or M.P('reports')
    os.makedirs(out, exist_ok=True)
    outs = []
    for name, title, srcs in DOCS:
        L = [title, '', '用途：brief §9 交付件；由执行端从下列原件拼成（原件不改），交付后冻结，补充另起 supplement。', '']
        for s in srcs:
            p = M.P(s)
            if not os.path.exists(p):
                raise RuntimeError('交付文档原件缺：%s' % s)
            L.append('- `%s`（sha256 前 16 = %s）' % (s, M.sha_file(p)[:16]))
        L.append('')
        for s in srcs:
            body = open(M.P(s), encoding='utf-8').read().split('\n')
            if body and body[0].startswith('# '):
                body = body[1:]
            L += ['## 来源：`%s`' % s, ''] + body + ['']
        p = os.path.join(out, name)
        M.atomic_write_text(p, '\n'.join(L) + '\n')
        outs.append(p)
    return outs


def notes_check(p=None):
    """执行端读结果后写的 notes 必须在、且不是骨架（brief §9；E6l REVIEW_input_notes 同）。p 只给冒烟测试用。"""
    p = p or M.P('reports', NOTES)
    if not os.path.exists(p):
        raise RuntimeError('%s 缺：执行端读结果后按 stageN/REVIEW_input_notes_skeleton.md 写' % M.rel(p))
    txt = open(p, encoding='utf-8').read()
    if SKELETON_MARK in txt or '（待写）' in txt:
        raise RuntimeError('%s 仍是骨架（含 %s 或"（待写）"）' % (M.rel(p), SKELETON_MARK))
    return p


def pick(path, col, where=None):
    """notes 取数（brief A9：数字从机器表取、带口径）：path = 机器表（相对工作目录或绝对路径）；where = pandas query 串；col = 列名。
    返回 (值或值列表, 单位, 聚合, 行数)；长表用其 unit / aggregation 列，宽表按列名后缀给单位。"""
    import pandas as pd
    p = path if os.path.isabs(path) else M.P(path)
    X = pd.read_csv(p, keep_default_na=False, na_values=[''], low_memory=False)
    if where:
        X = X.query(where, engine='python')
    vals = X[col].tolist()
    unit = str(X['unit'].iloc[0]) if 'unit' in X.columns and len(X) else ('ann_pp' if col.endswith('ann_pp') else ('decimal' if col.endswith('decimal') else ''))
    agg = str(X['aggregation'].iloc[0]) if 'aggregation' in X.columns and len(X) else ''
    return (vals[0] if len(vals) == 1 else vals), unit, agg, len(X)


def copy():
    g = json.load(open(M.P('closure_gate_stageS.json'), encoding='utf-8')) if os.path.exists(M.P('closure_gate_stageS.json')) else {}
    if not g.get('all_pass'):
        raise RuntimeError('闭包门未通过：不交付')
    W = M.work()
    dst = os.path.join(HANDOFF, 'stageS_%s' % time.strftime('%Y%m%d_%H%M'))
    os.makedirs(dst, exist_ok=False)
    lines = []
    files = [f for _, fs in collect() for f in fs] + ['reports/E6m_REVIEW_input.md', 'reports/E6m_MIRROR.md5']
    for f in sorted(set(files)):
        q = os.path.join(dst, f)
        os.makedirs(os.path.dirname(q), exist_ok=True)
        shutil.copy2(os.path.join(W, f), q)
        lines.append('%s  %s' % (M.sha_file(q), f))
    M.atomic_write_text(os.path.join(dst, 'HANDOFF_SHA256.txt'), '\n'.join(lines) + '\n')
    bad = [l for l in lines if M.sha_file(os.path.join(W, l.split('  ', 1)[1])) != l.split('  ', 1)[0]]
    if bad:
        raise RuntimeError('复制后 sha 不符：%s' % bad[:5])
    return dst, len(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['review', 'copy', 'docs', 'notes-check', 'pick'])
    ap.add_argument('--path', default='')
    ap.add_argument('--col', default='')
    ap.add_argument('--where', default='')
    ap.add_argument('--out', default='', help='docs 的输出目录（只给冒烟测试；缺省 reports/）')
    a = ap.parse_args()
    t0 = time.time()
    if a.task == 'docs':
        outs = docs(a.out or None)
        M.write_receipt(os.environ.get('E6M_TASK', 'S_deliver_docs'), outs, status='SUCCEEDED', code=[__file__, M.__file__], files=len(outs))
        print(json.dumps(dict(docs=[M.rel(p) for p in outs]), ensure_ascii=False))
        return 0
    if a.task == 'notes-check':
        p = notes_check()
        print(json.dumps(dict(notes=M.rel(p), sha16=M.sha_file(p)[:16]), ensure_ascii=False))
        return 0
    if a.task == 'pick':
        v, u, g, n = pick(a.path, a.col, a.where or None)
        print(json.dumps(dict(value=v, unit=u, aggregation=g, rows=n), ensure_ascii=False, default=str))
        return 0
    if a.task == 'review':
        p1, p2, n = review()
        M.write_receipt(os.environ.get('E6M_TASK', 'S_review_input'), [p1, p2], status='SUCCEEDED', code=[__file__, M.__file__], files=n)
        print(json.dumps(dict(files=n, review=M.rel(p1), mirror=M.rel(p2)), ensure_ascii=False))
        return 0
    dst, n = copy()
    M.write_receipt(os.environ.get('E6M_TASK', 'S_deliver_copy'), [], status='SUCCEEDED', code=[__file__, M.__file__], handoff_dir=M.san(dst), files=n,
                    wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(handoff=M.san(dst), files=n), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
