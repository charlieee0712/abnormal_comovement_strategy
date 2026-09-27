# -*- coding: utf-8 -*-
"""E6j 交付（brief v1.2 §9 / §13 / §15；plan §10.5 / §10.7）：
  --objects     results/research_object_results.parquet（B 全部描述符 × 四段 × 成本 / 资本视图；P 全部描述符 × 四段），负结果照常在内
  --hypotheses  results/hypothesis_outcomes.json：Q01–Q17（PLAN_COPY.md 行号引用 + 真实 query_id + 执行端写的 效果 / 机制 / 未知 / 下一次设计改变
                + hypothesis_update_card 八字段；文字来自 results/hypothesis_text_input.json，由执行端在读完结果后写）
  --review      reports/E6j_REVIEW_input.md：全部事实表 / 账本 / 登记 / 版本 / 源代码路径与 sha256、query_id 登记
  --gate        交付闭包门：登记对象全有账户、回执全 SUCCEEDED（FAILED 有同名 _rerun 覆盖）、封存核对、报告扫描、query_id 唯一
不写判词、不写共享 memory。"""
import e6j_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time

import numpy as np
import pandas as pd

import e6j_core as J

RES = J.RES
QIDS = ['Q%02d' % i for i in range(1, 18)]                  # Q 卡原文按 PLAN_COPY.md 的 "### Qxx" 标题定位，行号现算
Q_QUERIES = {'Q01': ['R0-Q05', 'R0-Q10', 'P3-Q20'], 'Q02': ['P1-Q03', 'P1B-Q01', 'P2-Q01', 'P2-Q07'], 'Q03': ['P1-Q03', 'P1-Q09', 'P2-Q01', 'P2-Q07'],
             'Q04': ['P1-Q04', 'P2-Q01', 'P2-Q07'], 'Q05': ['P1-Q05', 'P1B-Q06', 'P2-Q07'], 'Q06': ['P1-Q06', 'P2-Q01', 'P2-Q07'],
             'Q07': ['P3-Q09', 'P3-Q01', 'P3-Q07', 'P3-Q34', 'P3-Q30', 'P3-Q32'],
             'Q08': ['P3-Q16', 'P3-Q15', 'P3-Q28', 'P1B-Q01'], 'Q09': ['P3-Q14'], 'Q10': ['P1-Q07', 'P2-Q01', 'P2-Q07'], 'Q11': ['P1-Q08', 'P2-Q01', 'P2-Q07'],
             'Q12': ['P1-Q09', 'P2-Q01', 'P2-Q07'], 'Q13': ['P3-Q01', 'P3-Q02', 'P3-Q03', 'P3-Q04', 'P3-Q05', 'P3-Q06', 'P3-Q12', 'P3-Q23'],
             'Q14': ['P1-Q10', 'P1-Q11', 'P2-Q01', 'P2-Q07'],
             'Q15': ['P3-Q01', 'P3-Q17', 'P3-Q24', 'P3-Q12', 'P3-Q23', 'CAR-Q01', 'CAR-Q02', 'P2-Q05'],
             'Q16': ['P3-Q01', 'P3-Q07', 'P3-Q08', 'P3-Q21', 'P3-Q22', 'P3-Q25', 'P3-Q26', 'P3-Q29', 'P3-Q30', 'P3-Q31', 'P3-Q32', 'P3-Q33', 'P3-Q35'],
             'Q17': []}
CARD = ('source_claim', 'exposure', 'missing_assumption', 'experiment', 'result_query', 'supported_scope', 'alternative_surviving', 'next_design_change')


def objects():
    parts = []
    for s in J.SEGMENTS:
        f = os.path.join(RES, 'results_B', 'descriptor_stats_%s_final.csv' % s)
        if os.path.exists(f):
            x = pd.read_csv(f); x['package'] = 'B'; parts.append(x)
    pol = os.path.join(RES, 'results_P', 'pilot_policy.csv')
    if os.path.exists(pol):
        p = pd.read_csv(pol)
        long = []
        for s in J.SEGMENTS:
            y = p[['form', 'arm', 'alpha', 'H', 'D_%s' % s, 'n_%s' % s, 'Dsc_%s' % s, 'Dimp_%s' % s]].rename(
                columns={'D_%s' % s: 'D', 'n_%s' % s: 'n', 'Dsc_%s' % s: 'D_sc', 'Dimp_%s' % s: 'D_imp'})
            y['segment'] = s; y['package'] = 'P'; long.append(y)
        parts.append(pd.concat(long, ignore_index=True))
    df = pd.concat(parts, ignore_index=True)
    os.makedirs(os.path.join(RES, 'results'), exist_ok=True)
    out = os.path.join(RES, 'results', 'research_object_results.parquet')
    tmp = out + '.tmp.%d' % os.getpid(); df.to_parquet(tmp, index=False); os.replace(tmp, out)
    J.write_receipt('deliver_objects', [out], 'SUCCEEDED', rows=len(df))
    print('objects', len(df))


def hypotheses():
    txt = json.load(open(os.path.join(RES, 'results', 'hypothesis_text_input.json'), encoding='utf-8'))
    reg = json.load(open(os.path.join(RES, 'reports', 'query_registry.json')))
    plan = open(os.path.join(RES, 'PLAN_COPY.md'), encoding='utf-8').read().splitlines()
    out = {}
    for q in QIDS:
        t = txt.get(q, {})
        qs = [x for x in Q_QUERIES[q] if x in reg]
        # Q 卡原文：按 "### Qxx" 标题定位（行号只作指针）
        i0 = next(i for i, l in enumerate(plan) if l.startswith('### %s' % q))
        i1 = next((i for i in range(i0 + 1, len(plan)) if plan[i].startswith('### Q') or plan[i].startswith('## ')), len(plan))
        out[q] = dict(plan_text='\n'.join(plan[i0:i1]).strip(), plan_lines='%d–%d' % (i0 + 1, i1), queries=qs,
                      query_files={x: reg[x]['file'] for x in qs}, effect=t.get('effect', ''), mechanism=t.get('mechanism', ''),
                      unknown=t.get('unknown', ''), next_design_change=t.get('next_design_change', ''),
                      hypothesis_update_card={k: t.get('card', {}).get(k, '') for k in CARD})
    p = os.path.join(RES, 'results', 'hypothesis_outcomes.json'); J.atomic_write_json(p, out)
    miss = [q for q, v in out.items() if not v['effect'] or any(not v['hypothesis_update_card'][k] for k in CARD)]
    J.write_receipt('deliver_hypotheses', [p], 'SUCCEEDED' if not miss else 'FAILED', missing=miss)
    print('hypotheses', len(out), 'missing', miss)


def review():
    lines = ['# E6j REVIEW_input —— 事实块索引（执行端，交付随附）', '',
             '用途：给独立复核（协议 v1.1：决策端 `E6j_VERIFY_brief.md` → 执行端 V → 决策端 D + REVIEW）的全部事实表 / 账本 / 登记 / 版本 / 源代码路径与 sha256；'
             '正文之外的事实块也在此登记。结果目录 `results/20260927_0038_E6j_k_two_dimension_pilot/`。', '',
             '## 1. 报告与 query_id']
    reg = json.load(open(os.path.join(RES, 'reports', 'query_registry.json')))
    byf = {}
    for q, v in reg.items():
        byf.setdefault(v['file'], []).append(q)
    for f in sorted(byf):
        p = os.path.join(RES, 'reports', f)
        lines.append('- `reports/%s`（sha256 %s）：%d 个 query_id（%s）' % (f, J.sha_file(p)[:16] if os.path.exists(p) else '缺', len(byf[f]),
                                                                        '、'.join(sorted(byf[f]))))
    lines += ['', '## 2. 登记、授权、封存']
    for f in sorted(glob.glob(os.path.join(RES, 'registration', '**', '*'), recursive=True)) + sorted(glob.glob(os.path.join(RES, 'registry', '**', '*'), recursive=True)):
        if os.path.isfile(f):
            lines.append('- `%s`（%s）' % (os.path.relpath(f, RES), J.sha_file(f)[:16]))
    lines += ['', '## 3. 结果与账本（目录级）']
    for d in ('anchors', 'accounts/P', 'accounts/B', 'randoms/P', 'randoms/B', 'results_P', 'results_B', 'results', 'diagnostics', 'carried', 'stage0', 'stage1',
              'checks', 'cache'):
        fs = [p for p in glob.glob(os.path.join(RES, d, '**', '*'), recursive=True) if os.path.isfile(p)]
        tot = sum(os.path.getsize(p) for p in fs)
        lines.append('- `%s/`：%d 个文件，%.1f MB' % (d, len(fs), tot / 1e6))
    lines += ['', '## 4. 源代码（本轮新增 e6j_*，只读复用的源文件）']
    for p in sorted(glob.glob(os.path.join(J.CODE, 'e6j_*.py'))):
        lines.append('- `%s`（%s）' % (os.path.basename(p), J.sha_file(p)[:16]))
    sm = json.load(open(os.path.join(RES, 'source_manifest.json')))
    for f, h in sm['code_sha256'].items():
        lines.append('- 源 `%s`（%s，只读）' % (f, h[:16]))
    lines += ['', '## 5. 任务回执', '- `task_status/` 共 %d 个回执；状态计数见闭包门。' % len(glob.glob(os.path.join(RES, 'task_status', '*.json')))]
    p = os.path.join(RES, 'reports', 'E6j_REVIEW_input.md')
    J.atomic_write_text(p, '\n'.join(lines) + '\n')
    J.write_receipt('deliver_review_input', [p], 'SUCCEEDED')
    print('review_input written')


def gate():
    res = []
    def chk(i, what, ok, detail=''):
        res.append(dict(item=i, what=what, status='PASS' if ok else 'FAIL', detail=detail))
    st = {}
    for p in glob.glob(os.path.join(RES, 'task_status', '*.receipt.json')):
        st[os.path.basename(p)[:-13]] = json.load(open(p))['status']
    failed = [k for k, v in st.items() if v != 'SUCCEEDED' and (k + '_rerun') not in st]
    chk(1, '任务回执：FAILED 均有同名 _rerun 成功覆盖', not failed, '回执 %d；未覆盖 FAILED %s' % (len(st), failed[:5]))
    import e6j_seal as SEAL
    for pkg in ('P', 'B_post'):
        ok, bad = SEAL.verify(pkg)
        chk(2, '封存核对 %s' % pkg, ok, '不符 %d' % len(bad))
    reg = json.load(open(os.path.join(RES, 'reports', 'query_registry.json')))
    chk(3, 'query_id 跨文件唯一（登记表）', len(reg) == len(set(reg)), '%d 个' % len(reg))
    from e6j_report import FORBIDDEN, LEAK_PATTERNS
    bad = []
    for p in glob.glob(os.path.join(RES, 'reports', '*.md')):
        t = open(p, encoding='utf-8').read()
        if any(w in t for w in FORBIDDEN) or any(re.search(pt, t, flags=re.I) for pt in LEAK_PATTERNS):
            bad.append(os.path.basename(p))
    chk(4, '报告扫描（禁用词 / 主机地址 / 账号 / 家目录路径 / 连接串）', not bad, str(bad))
    ob = pd.read_parquet(os.path.join(RES, 'results', 'research_object_results.parquet'))
    nB = ob[ob.package == 'B'].groupby('segment').size().to_dict(); nP = ob[ob.package == 'P'].groupby('segment').size().to_dict()
    chk(5, '登记对象全有账户：B 每段 13,398；P 每段 504 个非恒等描述符（+ 24 个 C0 母体）',
        all(v == 13398 for v in nB.values()) and len(nB) == 4 and all(v == 504 for v in nP.values()) and len(nP) == 4, 'B %s；P %s' % (nB, nP))
    df = pd.DataFrame(res)
    p = os.path.join(RES, 'checks', 'closure_gate.csv'); J.atomic_write_csv(p, df)
    allp = bool((df.status == 'PASS').all())
    J.write_receipt('closure_gate', [p], 'SUCCEEDED' if allp else 'FAILED', all_pass=allp)
    print(df.to_string())
    return 0 if allp else 2


if __name__ == '__main__':
    a = sys.argv
    if '--objects' in a:
        objects()
    if '--hypotheses' in a:
        hypotheses()
    if '--review' in a:
        review()
    if '--gate' in a:
        sys.exit(gate())
