#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 只读复核程序（VERIFY brief v1 = exec_briefs/E6i_VERIFY_brief.md；review 协议 v1.0 §2）。

回答"报告里每个数是不是这个数"。规则（brief §1 / §3）：
  - 只读；不 import 任何 e6i_*.py / e6i_vendor（运行中自检 sys.modules）；不复用本轮进程内状态与 cache/。
  - 输入 = brief §1 封闭清单（结果目录的 registry / registration / statistics / accounts / randoms / m2 / sealed /
    carried / checks / task_status / logs / reports/*_tables / 五份 REPORT 三处副本 / git 只读命令）；
    钉住的引擎（四地基 + e6e–e6h 脚本，按 source_manifest SHA）只用于 V-B 母体重放。
  - 输出只写 <结果目录>/verify/：probes.csv、probe_results.csv、closure_gate.json、verify.log 等。
  - 判定只有 REPRODUCED / DIFFERS / NOT_COMPUTABLE（附 ROUNDING / STOCHASTIC 标记）；DIFFERS 印出来不修。
用法：python3 -u verify_e6i_readonly.py --stage gate|A|B|C|D|E [--part ...]
"""
from __future__ import annotations
import os
import sys

# 与本轮 e6i_boot 相同的两行进程设置（抄技术、不 import 本轮模块）：pyarrow 不起 S3 线程；BLAS 线程上限 4
sys.modules.setdefault('pyarrow._s3fs', None)
for _k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_MAX_THREADS'):
    os.environ.setdefault(_k, '4')

import re
import json
import glob
import time
import hashlib
import argparse
import subprocess

import numpy as np
import pandas as pd

RD = '/mnt/sda2/lichenchen/results/20260923_0254_E6i_measurement_need_fit'
PC = '/mnt/sda2/lichenchen/code/project_core'
EB = os.path.join(PC, 'exec_briefs')
VD = os.path.join(RD, 'verify')
SEGS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')
DER, POST = SEGS[:2], SEGS[2:]
ANN = 252 * 100.0
HEAD_EXPECTED = '569c810bad870a7ef367c9bb6d1fe773e120cb5a'
REPORTS = ('E6i_REPORT_R0.md', 'E6i_REPORT_part1.md', 'E6i_REPORT_part1b.md', 'E6i_REPORT_part2.md', 'E6i_REPORT_part3.md')
KNOWN_UNTRACKED = {'autochain.sh', 'chain.sh', 'chain2.sh', 'chain3.sh', 'chain4.sh', 'wave2.sh', 'wave3.sh',
                   'full_a_single_factor.py', 'sharpe_credibility_diagnosis.py', 'single_factor_groups.py',
                   'exec_briefs/E6i_record_B_draft.md'}
RESULTS = []          # 本次运行的探针结果（子检查粒度）
T0 = time.time()


# ============================================================ 基础
def log(msg):
    line = '[%s +%5.0fs] %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), time.time() - T0, msg)
    print(line, flush=True)
    with open(os.path.join(VD, 'verify.log'), 'a', encoding='utf-8') as fh:
        fh.write(line + '\n')


def assert_no_e6i():
    bad = sorted(m for m in sys.modules if m.split('.')[0].startswith('e6i'))
    if bad:
        raise SystemExit('只读规则被破坏：已 import 本轮模块 %s' % bad)


def sha256(p, chunk=1 << 22):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(chunk), b''):
            h.update(b)
    return h.hexdigest()


def md5(p, chunk=1 << 22):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(chunk), b''):
            h.update(b)
    return h.hexdigest()


def git(*args):
    return subprocess.run(['git', '-C', PC] + list(args), capture_output=True, text=True).stdout


def rd(p, **kw):
    return pd.read_csv(p, low_memory=False, **kw)


def fmt(x):
    if isinstance(x, (float, np.floating)):
        return repr(float(x))
    return str(x)


def rec(pid, sub, expected, got, verdict, tol='', inputs='', func='', note=''):
    """一条子检查。verdict ∈ REPRODUCED / DIFFERS / NOT_COMPUTABLE（可带 |ROUNDING 或 |STOCHASTIC）。"""
    diff = ''
    try:
        if isinstance(expected, (int, float, np.number)) and isinstance(got, (int, float, np.number)):
            diff = repr(float(got) - float(expected))
    except Exception:
        pass
    ins = []
    for p in (inputs if isinstance(inputs, (list, tuple)) else ([inputs] if inputs else [])):
        ap = p if os.path.isabs(p) else os.path.join(RD, p)
        ins.append('%s:%s' % (os.path.relpath(ap, RD) if ap.startswith(RD) else ap,
                              sha256(ap)[:16] if os.path.isfile(ap) else '-'))
    RESULTS.append(dict(probe_id=pid, sub=sub, expected=fmt(expected), recomputed=fmt(got), diff=diff,
                        verdict=verdict, tolerance=tol, inputs=';'.join(ins), func=func, note=note))


def v_exact(pid, sub, expected, got, **kw):
    ok = expected == got
    rec(pid, sub, expected, got, 'REPRODUCED' if ok else 'DIFFERS', tol='EXACT', **kw)
    return ok


def v_close(pid, sub, expected, got, tol, **kw):
    try:
        e, g = float(expected), float(got)
        ok = (np.isnan(e) and np.isnan(g)) or abs(e - g) <= tol
    except Exception:
        ok = False
    rec(pid, sub, expected, got, 'REPRODUCED' if ok else 'DIFFERS', tol='|d|<=%g' % tol, **kw)
    return ok


def decimals(s):
    s = str(s).strip().replace(',', '')
    m = re.fullmatch(r'[+\-−]?\d+(?:\.(\d+))?%?', s)
    return len(m.group(1)) if (m and m.group(1)) else 0


def to_float(s):
    s = str(s).strip().replace(',', '').replace('−', '-').replace('+', '')
    pct = s.endswith('%')
    s = s.rstrip('%')
    return float(s), pct


def v_printed(pid, sub, printed, got, scale=1.0, **kw):
    """按印出位数比较：round(got, d) == printed → REPRODUCED；末位差 1 → REPRODUCED|ROUNDING；否则 DIFFERS。
       scale：印出为百分数时 got 先乘 100。"""
    try:
        e, pct = to_float(printed)
        d = decimals(printed)
        g = float(got) * (100.0 if pct and scale == 1.0 else scale)
        step = 10.0 ** (-d)
        r = round(g, d)
        if abs(r - e) < step * 0.5:
            v = 'REPRODUCED'
        elif abs(r - e) <= step * 1.0 + 1e-12:
            v = 'REPRODUCED|ROUNDING'
        else:
            v = 'DIFFERS'
        rec(pid, sub, printed, g, v, tol='printed %d dp' % d, **kw)
        return v != 'DIFFERS'
    except Exception as ex:
        rec(pid, sub, printed, got, 'NOT_COMPUTABLE', note='比较失败 %s' % ex, **kw)
        return False


def flush_results(stage):
    """把本次运行的结果追加进 probe_results.csv（同一 stage 重跑时先删该 stage 的旧行；不同 stage 可写同一 probe_id）。"""
    p = os.path.join(VD, 'probe_results.csv')
    new = pd.DataFrame(RESULTS)
    if not len(new):
        return
    new.insert(0, 'stage', stage)
    new['run_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    if os.path.exists(p):
        old = rd(p)
        old = old[old.stage.astype(str) != stage]
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(p + '.tmp', index=False)
    os.replace(p + '.tmp', p)
    c = pd.DataFrame(RESULTS).verdict.str.split('|').str[0].value_counts().to_dict()
    log('stage %s 写出 %d 条子检查：%s' % (stage, len(RESULTS), c))
    RESULTS.clear()


# ============================================================ probes.csv（brief §5 机器转录）
def transcribe_probes():
    src = os.path.join(VD, 'VERIFY_brief_copy.md')
    txt = open(src, encoding='utf-8').read()
    sec = txt.split('## 5. V 探针', 1)[1].split('## 6. D 探针', 1)[0]
    rows, cat = [], ''
    for ln in sec.split('\n'):
        m = re.match(r'### (V-[A-E])', ln)
        if m:
            cat = m.group(1)
            continue
        if ln.startswith('| ') and not ln.startswith('| id') and not ln.startswith('|---'):
            cells = [c.strip() for c in ln.strip().strip('|').split('|')]
            if len(cells) >= 5:
                pid = cells[0].replace('⟂', '').strip()
                rows.append(dict(probe_id=pid, category=cat, overlaps_D=('⟂' in cells[0]), probe=cells[1],
                                 expected_source=cells[2], recompute=cells[3], tolerance=cells[4]))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(VD, 'probes.csv'), index=False)
    log('probes.csv：自 brief §5 转录 %d 条（%s）' % (len(df), df.category.value_counts().to_dict()))
    return df


# ============================================================ 闭包门（C-3 / 报告 §4）
VERIFY_DELIV = ('E6i_VERIFY_report.md', 'E6i_lessons_delta.md', 'E6i_MIRROR.md5')     # 结果目录副本在 verify/
FP_POST = os.path.join(VD, 'handoff_fingerprint_postverify.json')


def write_postverify_fingerprint():
    """C-3：VERIFY 交付后的交接指纹（另写到 verify/；registry/handoff_fingerprint.json 原文件不改）。"""
    fp0 = json.load(open(os.path.join(RD, 'registry', 'handoff_fingerprint.json')))
    head = git('rev-parse', 'HEAD').strip()
    tree = {ln.split('\t')[1]: ln.split()[2] for ln in git('ls-tree', '-r', 'HEAD').split('\n') if '\t' in ln}
    eb = {f: sha256(os.path.join(EB, f)) for f in list(fp0['exec_briefs']) + list(VERIFY_DELIV)}
    res = {f: sha256(os.path.join(RD, f)) for f in fp0['results']}
    skip = {'verify.log', os.path.basename(FP_POST), 'closure_gate_post_V.json'}
    for dp, dn, fn in os.walk(VD):
        for f in sorted(fn):
            rel = os.path.relpath(os.path.join(dp, f), RD)
            if f not in skip and not f.startswith('run_'):
                res[rel] = sha256(os.path.join(dp, f))
    blobs = {k: tree.get(k) for k in list(fp0['git_e6i_blobs']) + ['verify_e6i_readonly.py']}
    out = dict(round='E6i', stage='post_verify', written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
               note='VERIFY 交付后指纹（C-3）：原 registry/handoff_fingerprint.json 不改；exec_briefs 加 VERIFY 三份交付物，results 加 verify/ 全部产物'
                    '（verify.log、run_*.log 与本文件除外）；本文件不记录自身 hash',
               git_head=head, git_tracked_dirty=git('status', '--short', '--untracked-files=no').strip(), git_e6i_blobs=blobs,
               exec_briefs=eb, results=res, based_on=dict(file='registry/handoff_fingerprint.json', written_at=fp0['written_at'],
                                                            git_head=fp0['git_head']))
    json.dump(out, open(FP_POST, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    log('交付后指纹：%s（HEAD %s；exec_briefs %d、results %d、blob %d）' % (FP_POST, head[:12], len(eb), len(res), len(blobs)))


def closure_gate(tag):
    g = dict(tag=tag, checked_at=time.strftime('%Y-%m-%d %H:%M:%S'))
    # 1 运行中作业（本账号、命令行含 e6i_ 的 python；排除本进程）
    ps = subprocess.run(['ps', '-u', str(os.getuid()), '-o', 'pid=,lstart=,args='], capture_output=True, text=True).stdout
    jobs = [ln.strip() for ln in ps.split('\n')
            if re.search(r'python3?\s+(?:-u\s+)?\S*e6i_\w+\.py', ln) and 'verify_e6i_readonly' not in ln]
    g['running_e6i_jobs'] = jobs
    # 2 DONE 标记
    done = sorted(os.path.basename(p) for p in glob.glob(os.path.join(RD, 'task_status', '*_DONE.json')))
    g['done_markers'] = done
    fails = {}
    for p in done:
        d = json.load(open(os.path.join(RD, 'task_status', p)))
        fails[p] = sum(int(t.get('failed_tech', 0)) for t in d.get('totals', []))
    g['done_failed_tech'] = fails
    # 3 receipt 非空非失败
    rs = glob.glob(os.path.join(RD, 'task_status', '*.receipt.json'))
    st = {}
    empty, failed = [], []
    for p in rs:
        d = json.load(open(p))
        st[d.get('status')] = st.get(d.get('status'), 0) + 1
        if not (d.get('rows') or d.get('outputs') or d.get('n_rows') or d.get('n_programs')):   # m2boot / m2_samples 记 n_programs
            empty.append(os.path.basename(p))
        if d.get('status') != 'SUCCEEDED':
            rr = p.replace('.receipt.json', '_rerun.receipt.json')
            sup = os.path.exists(rr) and json.load(open(rr)).get('status') == 'SUCCEEDED'
            failed.append(dict(receipt=os.path.basename(p), status=d.get('status'), written_at=d.get('written_at'),
                               n_fail=d.get('n_fail'), superseded_by=os.path.basename(rr) if sup else None))
    g['receipts'] = dict(n=len(rs), status=st, empty_rows_and_outputs=len(empty), empty_examples=empty[:5],
                         non_succeeded=failed,
                         all_non_succeeded_superseded_by_rerun=all(f['superseded_by'] for f in failed))
    # 4 交接指纹重算（只比，不改原文件；post_V 比 verify/ 里的交付后指纹）
    fp = json.load(open(os.path.join(RD, 'registry', 'handoff_fingerprint.json') if tag == 'pre_V' else FP_POST))
    mism = []
    for f, s in fp['exec_briefs'].items():
        if sha256(os.path.join(EB, f)) != s:
            mism.append('exec_briefs/' + f)
    for f, s in fp['results'].items():
        p = os.path.join(RD, f)
        if not os.path.exists(p) or sha256(p) != s:
            mism.append(f)
    head = git('rev-parse', 'HEAD').strip()
    tree = {ln.split('\t')[1]: ln.split()[2] for ln in git('ls-tree', '-r', 'HEAD').split('\n') if '\t' in ln}
    blob_mism = [k for k, v in fp['git_e6i_blobs'].items() if tree.get(k) != v]
    g['fingerprint'] = dict(written_at=fp['written_at'], git_head_recorded=fp['git_head'], git_head_now=head,
                            n_blobs_recorded=len(fp['git_e6i_blobs']), blob_mismatches=blob_mism,
                            file_mismatches=mism, n_files_checked=len(fp['exec_briefs']) + len(fp['results']))
    # 5 git：远端 main、跟踪文件干净、untracked 只有既知项
    remote = subprocess.run(['git', '-C', PC, 'ls-remote', 'origin', 'refs/heads/main'], capture_output=True,
                            text=True).stdout.split()
    g['git'] = dict(remote_main=remote[0] if remote else '', head=head,
                    tracked_dirty=git('status', '--short', '--untracked-files=no').strip(),
                    untracked=sorted(ln[3:] for ln in git('status', '--short').split('\n') if ln.startswith('??')))
    g['git']['untracked_unknown'] = sorted(set(g['git']['untracked']) - KNOWN_UNTRACKED)
    # 6 三处镜像（本地哈希由本地工作站算好、作输入放 verify/）
    loc = json.load(open(os.path.join(VD, 'local_exec_briefs_hashes.json')))
    mir = {}
    for f in REPORTS + ('E6i_record_B_draft.md',) + (VERIFY_DELIV if tag == 'post_V' else ()):
        a = sha256(os.path.join(RD, 'verify' if f in VERIFY_DELIV else 'reports', f))
        b, c = sha256(os.path.join(EB, f)), loc[f]['sha256']
        mir[f] = dict(rd=a[:16], eb47=b[:16], local=c[:16], same=(a == b == c))
    g['mirrors'] = mir
    g['gate_pass'] = (not jobs and len(done) == 6 and all(v == 0 for v in fails.values())
                      and g['receipts']['all_non_succeeded_superseded_by_rerun'] and not empty and not mism and not blob_mism
                      and head == fp['git_head'] and g['git']['remote_main'] == head and not g['git']['tracked_dirty']
                      and not g['git']['untracked_unknown'] and all(v['same'] for v in mir.values()))
    p = os.path.join(VD, 'closure_gate%s.json' % ('' if tag == 'pre_V' else '_' + tag))
    json.dump(g, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    log('闭包门 %s：%s（作业 %d / DONE %d / receipt %s / 指纹不符 文件 %d blob %d / 远端 %s / untracked 未知 %d / 镜像 %s）' % (
        tag, 'PASS' if g['gate_pass'] else 'FAIL', len(jobs), len(done), st, len(mism), len(blob_mism),
        g['git']['remote_main'][:12], len(g['git']['untracked_unknown']), all(v['same'] for v in mir.values())))
    return g


# ============================================================ V-A 闭包与指纹
def ts(s):
    return pd.Timestamp(s)


def mtime(p):
    return pd.Timestamp(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p))))


def stage_A():
    loc = json.load(open(os.path.join(VD, 'local_exec_briefs_hashes.json')))
    # ---- A1 三处镜像
    exp = {'E6i_REPORT_R0.md': '7790f4c5', 'E6i_REPORT_part1.md': 'ad44f38c', 'E6i_REPORT_part1b.md': '0a082b65',
           'E6i_REPORT_part2.md': '6b6ccdb7', 'E6i_REPORT_part3.md': 'a68eb4de', 'E6i_record_B_draft.md': 'f1cb751e'}
    for f, pre in exp.items():
        a = sha256(os.path.join(RD, 'reports', f))
        b = sha256(os.path.join(EB, f))
        c = loc[f]['sha256']
        for place, h in (('RD', a), ('EB47', b), ('EBLOCAL', c)):
            v_exact('A1', '%s@%s 前缀' % (f, place), pre, h[:8], inputs=[os.path.join(RD, 'reports', f)] if place == 'RD' else [],
                    func='sha256')
        v_exact('A1', '%s 三处逐字节相同' % f, True, a == b == c, func='sha256')
    # ---- A2 交接指纹
    fp = json.load(open(os.path.join(RD, 'registry', 'handoff_fingerprint.json')))
    head = git('rev-parse', 'HEAD').strip()
    v_exact('A2', 'git_head（记录）', HEAD_EXPECTED, fp['git_head'], inputs='registry/handoff_fingerprint.json', func='json')
    v_exact('A2', 'git rev-parse HEAD', HEAD_EXPECTED, head, func='git rev-parse')
    v_exact('A2', 'git_tracked_dirty（记录）', '', fp.get('git_tracked_dirty', None), func='json')
    v_exact('A2', 'git status --untracked-files=no', '', git('status', '--short', '--untracked-files=no').strip(), func='git status')
    tree = {ln.split('\t')[1]: ln.split()[2] for ln in git('ls-tree', '-r', 'HEAD').split('\n') if '\t' in ln}
    e6i_tree = {k: v for k, v in tree.items() if k.startswith('e6i_')}
    v_exact('A2', 'git_e6i_blobs 个数', 66, len(fp['git_e6i_blobs']), func='json')
    v_exact('A2', 'HEAD 中 e6i_* 条目数', 66, len(e6i_tree), func='git ls-tree')
    v_exact('A2', 'blob 逐项一致（不符个数）', 0, sum(e6i_tree.get(k) != v for k, v in fp['git_e6i_blobs'].items())
            + len(set(e6i_tree) ^ set(fp['git_e6i_blobs'])), func='git ls-tree')
    # ---- A3 白名单提交
    def files_of(c):
        return [x for x in git('show', '--name-only', '--format=', c).split('\n') if x.strip()]
    f1, f2, f3 = files_of('f8bb4d9'), files_of('0d0f5cd'), files_of('569c810')
    rep = {'exec_briefs/' + r for r in REPORTS}
    v_exact('A3', 'f8bb4d9 文件数', 72, len(f1), func='git show')
    v_exact('A3', 'f8bb4d9 e6i_*.py 个数', 58, sum(bool(re.fullmatch(r'e6i_\w+\.py', x)) for x in f1), func='git show')
    v_exact('A3', 'f8bb4d9 e6i_vendor/ 个数', 7, sum(x.startswith('e6i_vendor/') for x in f1), func='git show')
    v_exact('A3', 'f8bb4d9 含 brief + source_corrections + 五份 REPORT', True,
            {'exec_briefs/E6i_measurement_need_fit.md', 'source_corrections_E6i.md'} | rep <= set(f1), func='git show')
    v_exact('A3', 'f8bb4d9 白名单外文件', [], sorted(x for x in f1 if not (re.fullmatch(r'e6i_\w+\.py', x) or x.startswith('e6i_vendor/')
                                                     or x in rep or x in ('exec_briefs/E6i_measurement_need_fit.md', 'source_corrections_E6i.md'))),
            func='git show')
    v_exact('A3', '0d0f5cd 文件集合', ['e6i_stage4_docs.py'], f2, func='git show')
    exp3 = sorted(['e6i_c1_capital.py', 'e6i_outcome_judgments.py', 'e6i_report_part2.py', 'e6i_report_part3.py',
                   'e6i_stage4_docs.py', 'e6i_stage4_registry.py', 'exec_briefs/E6i_REPORT_part2.md', 'exec_briefs/E6i_REPORT_part3.md'])
    v_exact('A3', '569c810 文件集合（6 个 e6i 脚本 + part2 + part3）', exp3, sorted(f3), func='git show')
    # ---- A4 A0 四版计数与 v1.2→v1.3 差异
    vers = {'v1.0': 'registry/A0_v1_0/descriptors_A0.csv', 'v1.1': 'registry/A0_v1_1/descriptors_A0.csv',
            'v1.2': 'registry/A0_v1_2/descriptors_A0.csv', 'v1.3': 'registry/descriptors_A0.csv'}
    expn = {'v1.0': 35104, 'v1.1': 35176, 'v1.2': 35656, 'v1.3': 37360}
    A0 = {k: rd(os.path.join(RD, p)) for k, p in vers.items()}
    for k in vers:
        v_exact('A4', '%s 行数' % k, expn[k], len(A0[k]), inputs=vers[k], func='len')
    a2, a3 = A0['v1.2'].set_index('descriptor_id'), A0['v1.3'].set_index('descriptor_id')
    new = a3.index.difference(a2.index)
    gone = a2.index.difference(a3.index)
    com = a2.index.intersection(a3.index)
    cols = [c for c in a2.columns if c in a3.columns]
    x2, x3 = a2.loc[com, cols].astype(str), a3.loc[com, cols].astype(str)
    changed = int((x2 != x3).any(axis=1).sum())
    v_exact('A4', 'v1.2→v1.3 新增', 1704, len(new), func='index diff')
    rc = a3.loc[new].route_id.value_counts().to_dict() if 'route_id' in a3.columns else {}
    v_exact('A4', '新增构成 RA', 1656, int(rc.get('RA', 0)), func='value_counts')
    v_exact('A4', '新增构成 M2', 48, int(rc.get('M2', 0)), func='value_counts')
    v_exact('A4', 'gone', 0, len(gone), func='index diff')
    v_exact('A4', 'changed（共同行逐字段）', 0, changed, func='field diff')
    # ---- A5 修订时间先于结果
    mf = json.load(open(os.path.join(RD, 'registry', 'manifest_A0.json')))
    reg13 = ts(mf['compiled_at'])
    radd = [json.load(open(p)) for p in glob.glob(os.path.join(RD, 'task_status', 'stage2_*_RA_*_add.receipt.json'))]
    first_start = min(ts(d['written_at']) - pd.Timedelta(seconds=float(d.get('elapsed_s') or 0)) for d in radd)
    first_out = min(ts(d['written_at']) for d in radd)
    mt = min(mtime(p) for p in glob.glob(os.path.join(RD, 'accounts', '*', 'RA_*_add.*')))
    v_exact('A5', 'v1.3 compiled_at（manifest_A0.json）', '2026-09-23 22:33:57', str(reg13), inputs='registry/manifest_A0.json', func='json')
    v_exact('A5', 'v1.3 登记 ≤ RA v1.3 首个作业启动（receipt written_at − elapsed）', True, reg13 <= first_start,
            func='receipt', note='首个启动 %s；首个完成 %s；RA_*_add 文件最早 mtime %s' % (first_start, first_out, mt))
    v_exact('A5', 'v1.3 登记 < RA_*_add 账户文件最早 mtime', True, reg13 < mt, func='mtime')
    ex = rd(os.path.join(RD, 'registry', 'exposure_ledger.csv'))
    v_exact('A5', 'exposure_ledger 有 v1.2 信息暴露条目', True, bool(ex.event.astype(str).str.contains('A0 v1.2').any()),
            inputs='registry/exposure_ledger.csv', func='contains')
    # ---- A6 preregistration
    pr = os.path.join(RD, 'preregistration.md')
    txt = open(pr, encoding='utf-8').read()
    m = re.search(r'落盘时间：(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)', txt)
    v_exact('A6', 'sha256 前缀', 'd5312ce8', sha256(pr)[:8], inputs='preregistration.md', func='sha256')
    v_exact('A6', '内文落盘时间', '2026-09-23 16:21:24', m.group(1) if m else None, func='regex')
    s2 = [json.load(open(p)) for p in glob.glob(os.path.join(RD, 'task_status', 'stage2_*.receipt.json'))]
    s2start = min(ts(d['written_at']) - pd.Timedelta(seconds=float(d.get('elapsed_s') or 0)) for d in s2)
    acc_mt = min(mtime(p) for p in glob.glob(os.path.join(RD, 'accounts', '2010-2014', '*')))
    v_exact('A6', '落盘时间 ≤ 首个 Stage 2 作业启动', True, ts(m.group(1)) <= s2start, func='receipt',
            note='首个 Stage 2 启动 %s' % s2start)
    v_exact('A6', '落盘时间 < accounts/2010-2014 最早 mtime', True, ts(m.group(1)) < acc_mt, func='mtime', note='最早 mtime %s' % acc_mt)
    # ---- A7 记录 B
    cm = os.path.join(RD, 'registry', 'record_B_candidate_manifest.json')
    ap = os.path.join(RD, 'registration', 'record_B_approved_E6i.json')
    A = json.load(open(ap))
    M = json.load(open(cm))
    v_exact('A7', 'candidate manifest sha 前缀', '2a44b92750f5', sha256(cm)[:12], inputs=cm, func='sha256')
    v_exact('A7', '批准文件 sha 前缀', 'ccb13b59b86c', sha256(ap)[:12], inputs=ap, func='sha256')
    v_exact('A7', '批准文件记的 manifest sha = 实际', sha256(cm), A['manifest_sha256'], func='json')
    v_exact('A7', 'approval_id', 'E6I-B-20260924-FULL', A['approval_id'], func='json')
    v_exact('A7', 'approved_at', '2026-09-24 01:42:08', A['approved_at'], func='json')
    v_exact('A7', 'user_reply_verbatim', 'ultrathink 继续跑完', A['user_reply_verbatim'], func='json')
    pk = A['approved_packages']
    v_exact('A7', '需求域包数（不含技术包）', 43, len([p for p in pk if 'CARRIED' not in p]), func='json')
    v_exact('A7', '技术包 E6I-B-CARRIED-C1C2', True, 'E6I-B-CARRIED-C1C2' in pk, func='json')
    v_exact('A7', '批准描述符数', 37360, len(A['approved_descriptors']), func='json')
    v_exact('A7', '批准受保护成员数', 236, len(A['approved_members']), func='json')
    v_exact('A7', '未批 8 成员', sorted(['K_css20', 'K_css60', 'K_edges20', 'K_edges60', 'K_notrade20', 'K_notrade60', 'T_zero20',
                                     'T_zero60']), sorted(A['protected_members_not_approved']), func='json')
    v_exact('A7', 'manifest_check 51/51', (51, 51), (A['manifest_check']['n_objects'], A['manifest_check']['n_ok']), func='json')
    v_exact('A7', 'manifest code_sha256 文件数', 48, len(M['code_sha256']), func='json')
    chg = json.load(open(os.path.join(RD, 'registry', 'stage3_code_changes', 'changes.json')))
    bad = [c['file'] for c in chg['changed'] if M['code_sha256'].get(c['file']) != c['sha_before']]
    v_exact('A7', 'Stage 3 改前 sha = manifest code_sha256（不符个数）', 0, len(bad), func='json', note=';'.join(bad))
    # ---- A8 首次观察封存
    flp = os.path.join(RD, 'registry', 'first_look_receipts.json')
    FL = json.load(open(flp))
    v_exact('A8', '回执时间', '2026-09-24 14:48:50', FL['written_at'], inputs=flp, func='json')
    v_exact('A8', '回执 status', 'SEALED', FL['status'], func='json')
    v_exact('A8', '封存文件数', 2865, len(FL['files']), func='json')
    v_exact('A8', '封存字节（MB，印出 7,234.6）', '7234.6', '%.1f' % (FL['total_bytes'] / 1e6), func='json')
    nbad, nmiss = 0, 0
    for e in FL['files']:
        p = os.path.join(RD, e['path'])
        if not os.path.exists(p):
            nmiss += 1
        elif sha256(p) != e['sha256']:
            nbad += 1
    v_exact('A8', '(i) 封存文件逐个 sha256 一致（不符 / 缺失）', (0, 0), (nbad, nmiss), func='sha256 x 2865')
    tr = ts(FL['written_at'])
    groups = {'statistics/post/*': 'statistics/post/*', 'reports/part2_tables/*': 'reports/part2_tables/*',
              'm2/2019-2023/ledger_*': 'm2/2019-2023/ledger_*', 'm2/2024-2026/*': 'm2/2024-2026/*'}
    sealed_paths = {e['path'] for e in FL['files']}
    for lab, pat in groups.items():
        fs = glob.glob(os.path.join(RD, pat))
        mn = min(mtime(p) for p in fs)
        ins = sum(os.path.relpath(p, RD) in sealed_paths for p in fs)
        v_exact('A8', '(ii) %s 最早 mtime ≥ 回执' % lab, True, mn >= tr, func='mtime',
                note='最早 mtime %s；该组 %d 个文件中 %d 个在回执封存清单内' % (mn, len(fs), ins))
    lg = os.path.join(RD, 'logs', 'stats_post.log')
    if os.path.exists(lg):
        first = open(lg, encoding='utf-8', errors='replace').readline()
        v_exact('A8', '(ii) 后段统计日志文件 mtime ≥ 回执', True, mtime(lg) >= tr, func='mtime', note=first.strip()[:80])
    zr = [json.load(open(p)) for s in POST for p in glob.glob(os.path.join(RD, 'task_status', 'zmap_%s_*.receipt.json' % s))]
    zstart = min(ts(d['written_at']) - pd.Timedelta(seconds=float(d.get('elapsed_s') or 0)) for d in zr)
    v_exact('A8', '(iii) Z-MAP 后段首个作业启动 ≥ 批准 01:42:08', True, zstart >= ts(A['approved_at']), func='receipt',
            note='首个启动 %s（%d 个后段 Z-MAP receipt）' % (zstart, len(zr)))
    # ---- A9 状态表求和
    s2t = rd(os.path.join(RD, 'registry', 'stage2_status_table.csv'))
    s3t = rd(os.path.join(RD, 'registry', 'stage3_status_table.csv'))
    for tab, segs, lab in ((s2t, DER, 'Stage 2'), (s3t, POST, 'Stage 3')):
        mm = tab[~tab.route.isin(['M1', 'M2'])]
        for s in segs:
            x = mm[mm.segment == s]
            v_exact('A9', '%s %s SUCCEEDED 和' % (lab, s), 35384, int(x.succeeded.sum()), func='sum')
            v_exact('A9', '%s %s a0_count 和' % (lab, s), 35384, int(x.a0_count.sum()), func='sum')
            v_exact('A9', '%s %s FAILED_TECH 和' % (lab, s), 0, int(x.failed_tech.sum()), func='sum')
            v_exact('A9', '%s %s NOT_APPLICABLE 和' % (lab, s), 0, int(x.not_applicable.sum()), func='sum')
    main12 = A0['v1.2'][~A0['v1.2'].route_id.isin(['M1', 'M2'])]
    v_exact('A9', 'v1.2 主路线描述符数', 33728, len(main12), func='len')
    v_exact('A9', 'v1.3 主路线描述符数 = 33,728 + 1,656', 35384, len(A0['v1.3'][~A0['v1.3'].route_id.isin(['M1', 'M2'])]), func='len')
    for f, segs in (('m1_DONE.json', DER), ('m1_post_DONE.json', POST)):
        d = json.load(open(os.path.join(RD, 'task_status', f)))
        for t in d['totals']:
            v_exact('A9', '%s %s M1 SUCCEEDED' % (f, t['segment']), 1512, int(t['succeeded']), func='json')
            v_exact('A9', '%s %s M1 伴随行' % (f, t['segment']), 1512, int(t.get('companion_rows', -1)), func='json')
    for f in ('m2_DONE.json', 'm2_post_DONE.json'):
        d = json.load(open(os.path.join(RD, 'task_status', f)))
        for t in d['totals']:
            v_exact('A9', '%s %s M2 SUCCEEDED' % (f, t['segment']), 464, int(t['succeeded']), func='json')
    # ---- A10 守卫与契约
    g0 = json.load(open(os.path.join(RD, 'checks', 'guard_attack_tests.json')))
    g1 = json.load(open(os.path.join(RD, 'checks', 'guard_attack_tests_post.json')))
    v_exact('A10', '守卫 must_block', (25, 25), (g0['n_must_block_ok'], g0['n_must_block']), func='json')
    v_exact('A10', '守卫 must_pass', (7, 7), (g0['n_must_pass_ok'], g0['n_must_pass']), func='json')
    v_exact('A10', '守卫 post', (48, 48), (g1['n_ok'], g1['n']), func='json')
    sf = pd.concat([rd(p) for p in glob.glob(os.path.join(RD, 'checks', 'suffix_guard_*.csv'))])
    v_exact('A10', 'suffix_guard 检查数', 1952, len(sf), func='concat')
    v_exact('A10', 'suffix_guard 失败数', 0, int((~sf.ok.astype(bool)).sum()), func='sum')
    pc_ = json.load(open(os.path.join(RD, 'checks', 'plan_contract_tests', 'e6i_plan_contract_test_results.json')))
    v_exact('A10', 'plan 契约', (61, 61), (pc_['passed'], pc_['tests']), func='json')
    vc = json.load(open(os.path.join(RD, 'checks', 'vendor_check.json')))
    v_exact('A10', 'EDGE vendor', (5, 5), (vc['n_pass'], vc['n']), func='json')
    # ---- A11 Stage 3 代码改动
    v_exact('A11', '修改文件数', 12, len(chg['changed']), func='json')
    v_exact('A11', '新文件数', 5, len(chg['new_files']), func='json')
    for c in chg['changed']:
        cont = subprocess.run(['git', '-C', PC, 'show', 'HEAD:%s' % c['file']], capture_output=True).stdout
        v_exact('A11', '%s 改后 sha = HEAD 内容 sha' % c['file'], c['sha_after'], hashlib.sha256(cont).hexdigest(), func='git show')
        dp = os.path.join(RD, 'registry', 'stage3_code_changes', c['file'][:-3] + '.diff')   # 登记目录里 diff 名 = 去 .py
        bp = os.path.join(RD, 'registry', 'stage3_code_changes', 'before', c['file'])
        v_exact('A11', '%s diff 与改前副本存在' % c['file'], True, os.path.exists(dp) and os.path.exists(bp), func='exists')
        if os.path.exists(bp):
            v_exact('A11', '%s 改前副本 sha = sha_before' % c['file'], c['sha_before'], sha256(bp), func='sha256')
    for n in chg['new_files']:
        if n['file'].startswith('runtime/'):          # 运行脚本放在结果目录 runtime/，不进仓库
            h = sha256(os.path.join(RD, n['file']))
            v_exact('A11', '新文件 %s 登记 sha = 结果目录文件 sha' % n['file'], n['sha'], h, func='sha256')
            continue
        cont = subprocess.run(['git', '-C', PC, 'show', 'HEAD:%s' % n['file']], capture_output=True)
        h = hashlib.sha256(cont.stdout).hexdigest() if cont.returncode == 0 else '(不在 HEAD)'
        v_exact('A11', '新文件 %s 登记 sha = HEAD 内容 sha' % n['file'], n['sha'], h, func='git show')
    # ---- A12 源 manifest
    sm = json.load(open(os.path.join(RD, 'source_manifest.json')))
    files = {}
    for sec in ('foundation_readonly', 'engine_readonly_by_contract', 'e6e_frozen', 'e6f_frozen', 'e6g_frozen', 'e6h_frozen'):
        v = sm.get(sec, {})
        if isinstance(v, dict):
            files.update(v)
        elif isinstance(v, list):
            for e in v:
                files[e.get('file') or e.get('path')] = e.get('sha256')
    v_exact('A12', '源脚本条目数', 100, len(files), inputs='source_manifest.json', func='json',
            note='counts 段：%s' % json.dumps(sm.get('counts'), ensure_ascii=False)[:150])
    nb = [f for f, s in files.items() if not os.path.exists(os.path.join(PC, f)) or sha256(os.path.join(PC, f)) != s]
    v_exact('A12', '源脚本当前 sha = manifest（不符个数）', 0, len(nb), func='sha256', note=';'.join(nb[:5]))
    dd = git('diff', '--stat', '4b1ee8e', HEAD_EXPECTED, '--', *files.keys()).strip()
    v_exact('A12', 'git diff 4b1ee8e..569c810 -- <源脚本> 为空', '', dd, func='git diff')
    # ---- A13 coverage 与目录对照
    cv = rd(os.path.join(RD, 'registry', 'coverage.csv'))
    vc_ = cv.status.value_counts().to_dict()
    for k, n in (('done', 27), ('changed', 4), ('deferred', 1), ('unavailable', 1)):
        v_exact('A13', 'coverage %s' % k, n, int(vc_.get(k, 0)), inputs='registry/coverage.csv', func='value_counts')
    v_exact('A13', 'coverage 其它状态', 0, int(sum(v for k, v in vc_.items() if k not in ('done', 'changed', 'deferred', 'unavailable'))),
            func='value_counts')
    lm = rd(os.path.join(RD, 'registry', 'layout_map_plan12_1.csv'))
    v_exact('A13', 'layout_map 项数', 45, len(lm), inputs='registry/layout_map_plan12_1.csv', func='len')
    v_exact('A13', 'layout_map MISSING', 0, int((lm.status == 'MISSING').sum()), func='sum')
    # ---- A14 limit_register L1–L17
    lr = open(os.path.join(RD, 'reports', 'limit_register.md'), encoding='utf-8').read()
    rows = {m.group(1): m.group(0) for m in re.finditer(r'^\| (L\d+) \|.*$', lr, flags=re.M)}
    v_exact('A14', 'L1–L17 齐全', ['L%d' % i for i in range(1, 18)], sorted([k for k in rows if int(k[1:]) <= 17], key=lambda s: int(s[1:])),
            inputs='reports/limit_register.md', func='regex')
    need = {'L1': ('A1', 'deferred'), 'L5': ('RK 在 A08', 'NOT_APPLICABLE'), 'L6': ('8 个',) + ('K_css20', 'T_zero60'),
            'L16': ('C1 资本分解', 'LIMIT', '逐日投入资金'), 'L17': ('B 后事后补充',)}
    for k, words in need.items():
        v_exact('A14', '%s 含 %s' % (k, ' / '.join(words)), True, all(w in rows.get(k, '') for w in words), func='contains')


# ============================================================ V-C 核心：从日账本独立重算逐描述符统计（全量）
WORK = os.path.join(VD, 'work')
BOOT_CODE = {'2010-2014': 1, '2015-2018': 2, '2019-2023': 3, '2024-2026': 4}
SEED0, B_DRAWS, BLOCKS = 20260923, 2000, (20, 60)


def calendar(seg):
    c = np.load(os.path.join(RD, 'm2', seg, 'calendar.npy'))
    return pd.to_datetime(pd.Series(c).astype(str), format='%Y%m%d')


def load_ledgers(seg, series=('dnet8', 'dcore', 'dsamecap')):
    """逐段读 accounts/<段>/ 的合并元数据与日账本；每个 npz 只打开一次、每个键只取一次。
       同时核：npz 内 descriptor_id 与索引行一致；net8 = gross − 8e−4·turn 的逐日残差（E2）。"""
    od = os.path.join(RD, 'accounts', seg)
    meta = pd.concat([rd(f) for f in sorted(glob.glob(os.path.join(od, 'merged_*.csv'))) if not f.endswith('merged_index.csv')],
                     ignore_index=True)
    meta = meta[meta.status == 'SUCCEEDED'].reset_index(drop=True)
    idx = rd(os.path.join(od, 'merged_index.csv'))
    pos = dict(zip(idx.descriptor_id, zip(idx.npz, idx.row)))
    meta = meta[meta.descriptor_id.isin(pos)].reset_index(drop=True)
    J = len(meta)
    by = {}
    for j, did in enumerate(meta.descriptor_id):
        f, r = pos[did]
        by.setdefault(f, []).append((j, int(r)))
    arrs, T = {}, None
    idmis, e2 = 0, 0.0
    for f, lst in by.items():
        with np.load(os.path.join(od, f)) as z:
            names = set(z.files)
            ids = z['descriptor_id']
            jj = np.array([a for a, _ in lst])
            rr = np.array([b for _, b in lst])
            idmis += int((ids[rr] != meta.descriptor_id.values[jj]).sum())
            if T is None:
                T = z['dnet8'].shape[1]
                arrs = {k: np.full((T, J), np.nan) for k in series}
            for k in series:
                if k in names:
                    arrs[k][:, jj] = z[k][rr].T
            n8, g8, tu = z['net8'][rr], z['gross'][rr], z['turn'][rr]
            with np.errstate(all='ignore'):
                d = np.abs(n8 - (g8 - tu * 8.0 / 1e4))
            if np.isfinite(d).any():
                e2 = max(e2, float(np.nanmax(d)))
    return meta, arrs, T, idmis, e2


def nw(X, lag):
    """有掩码 NW：自协方差只在两端都有值的日对上累加，分母 = 有效日；Bartlett 权 1 − L/(lag+1)。"""
    m = np.isfinite(X)
    n = m.sum(0).astype(float)
    with np.errstate(all='ignore'):
        mu = np.where(m, X, 0.0).sum(0) / n
        e = np.where(m, X - mu, 0.0)
        s = (e * e).sum(0) / n
        for L in range(1, lag + 1):
            if L >= X.shape[0]:
                break
            s = s + 2.0 * (1.0 - L / (lag + 1.0)) * ((e[L:] * e[:-L]).sum(0) / n)
        se = np.sqrt(np.maximum(s, 0.0) / n)
    return mu, se, n


def nw_by_h(X, Hs, lagf):
    se = np.full(X.shape[1], np.nan)
    for h in np.unique(Hs):
        c = np.flatnonzero(Hs == h)
        se[c] = nw(X[:, c], lagf(int(h)))[1]
    return se


def merged(parts, Hs):
    """段间不拼接：各段 NW(lag H) 按有效日加权合并；se = sqrt(Σ (n_s·s_s)²) / Σ n_s。"""
    J = parts[0].shape[1]
    num, cnt, vv = np.zeros(J), np.zeros(J), np.zeros(J)
    for X in parts:
        m = np.isfinite(X)
        num += np.where(m, X, 0.0).sum(0)
        cnt += m.sum(0)
    se = np.full(J, np.nan)
    for h in np.unique(Hs):
        c = np.flatnonzero(Hs == h)
        v = np.zeros(len(c))
        for X in parts:
            _, s_, n_ = nw(X[:, c], int(h))
            v += np.where(n_ > 0, (n_ * s_) ** 2, 0.0)
        with np.errstate(all='ignore'):
            se[c] = np.sqrt(v) / cnt[c]
    with np.errstate(all='ignore'):
        mu = num / cnt
    return mu, se, cnt


def sb_weights(T, B, L, seed):
    """循环 stationary bootstrap 的日期重数 (B, T)；随机数调用顺序与原实现一致（同 seed 可逐位重放）。"""
    rng = np.random.default_rng(seed)
    W = np.zeros((B, T))
    p = 1.0 / L
    for b in range(B):
        idx = np.empty(T, np.int64)
        cur = rng.integers(T)
        jumps = rng.random(T) < p
        starts = rng.integers(T, size=T)
        for t in range(T):
            if t == 0 or jumps[t]:
                cur = starts[t]
            else:
                cur = (cur + 1) % T
            idx[t] = cur
        W[b] = np.bincount(idx, minlength=T)
    return W


def boot_nd(X, W, chunk=4000):
    m = np.isfinite(X)
    X0, M = np.where(m, X, 0.0), m.astype(float)
    B, J = W.shape[0], X.shape[1]
    num, den = np.empty((B, J)), np.empty((B, J))
    for a in range(0, J, chunk):
        num[:, a:a + chunk] = W @ X0[:, a:a + chunk]
        den[:, a:a + chunk] = W @ M[:, a:a + chunk]
    return num, den


def families(meta):
    sem = rd(os.path.join(RD, 'registry', 'feature_semantics_v2.csv'))
    ax = dict(zip(sem.member_id, sem.axis_id))
    axis = np.array([ax.get(str(m).split('|')[0].split('+')[0], '') for m in meta.member_id], dtype=object)
    fams = {}
    for (rt, mo), g in meta.groupby(['route_id', 'mother_id']):
        fams[('domain', '%s|%s' % (rt, mo))] = g.index.values
    for a_ in sorted(set(axis) - {''}):
        fams[('axis', a_)] = np.flatnonzero(axis == a_)
    fams[('headline', 'all')] = meta.index.values
    return fams


def bands(res, num, den, fams, crit_rows, scope, L, write):
    mu = res['d_net8_ann'].values / ANN
    with np.errstate(all='ignore'):
        mstar = num / den
        sd = np.nanstd(mstar, axis=0, ddof=1)
        tabs = np.abs((mstar - mu[None, :]) / sd[None, :])
    tabs = np.where(np.isfinite(tabs), tabs, 0.0)
    valid = np.isfinite(sd) & (sd > 0) & np.isfinite(mu)
    for (lvl, name), cols in fams.items():
        cv = cols[valid[cols]]
        c = float(np.quantile(tabs[:, cv].max(1), 0.95)) if len(cv) else np.nan
        crit_rows.append(dict(scope=scope, block=L, level=lvl, family=name, n_members=len(cols), n_valid=len(cv),
                              n_zero_se=int((~valid[cols]).sum()), crit=c))
        if write:
            for side, sgn in (('lo', -1.0), ('hi', 1.0)):
                col = 'band_%s_%s' % (lvl, side)
                if col not in res:
                    res[col] = np.nan
                res.loc[cols, col] = (mu[cols] + sgn * c * sd[cols]) * ANN
    return sd


def state_word(lo, hi, est, delta=0.25):
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return 'inconclusive'
    if lo >= -delta and hi <= delta:
        return 'materially_small_under_declared_delta'
    if lo < -delta and hi > delta:
        return 'inconclusive'
    return 'positive_estimate_uncertain' if est > 0 else 'negative_estimate_uncertain'


def finish(res):
    se, est = res['se_nwH'].values, res['d_net8_ann'].values
    lo, hi = est - 1.96 * se, est + 1.96 * se
    res['ci_lo_nwH'], res['ci_hi_nwH'] = lo, hi
    res['ci_excludes_zero'] = (lo > 0) | (hi < 0)
    res['discernible_scale'] = 1.96 * se
    res['mde80'] = (1.96 + 0.84) * se
    res['state_word'] = [state_word(a_, b_, e_) for a_, b_, e_ in zip(lo, hi, est)]
    return res


def stage_C0():
    """全量重算 → work/rc_<scope>.csv，并与 statistics/ 的描述符统计表逐列比较（|d| ≤ 1e−12；计数 EXACT）。"""
    os.makedirs(WORK, exist_ok=True)
    data, idmis, e2 = {}, {}, {}
    for s in SEGS:
        meta, arrs, T, im, r2 = load_ledgers(s)
        cal = calendar(s)
        assert len(cal) == T, (s, len(cal), T)
        data[s] = (meta, arrs, T, cal)
        idmis[s], e2[s] = im, r2
        log('[%s] 账本 %d 描述符 x %d 日；npz 行 id 不符 %d；E2 net8 残差 max %.2e' % (s, len(meta), T, im, r2))
    common = sorted(set.intersection(*[set(data[s][0].descriptor_id) for s in SEGS]))
    for s in SEGS:
        meta, arrs, T, cal = data[s]
        o = meta.set_index('descriptor_id').index.get_indexer(common)
        data[s] = (meta.iloc[o].reset_index(drop=True), {k: v[:, o] for k, v in arrs.items()}, T, cal)
    meta0 = data[SEGS[0]][0]
    Hs = meta0.H.astype(int).values
    J = len(common)
    fams = families(meta0)
    out, crit_rows = {}, []
    acc = {}                     # (scope, L) -> [num, den]
    ys, yc = {}, {}
    for s in SEGS:
        meta, arrs, T, cal = data[s]
        X = arrs['dnet8']
        res = pd.DataFrame({'descriptor_id': common})
        mu, _, n = nw(X, 1)
        res['n_days'], res['d_net8_ann'] = n, mu * ANN
        res['se_nwH'] = nw_by_h(X, Hs, lambda h: h) * ANN
        res['se_nw2H20'] = nw_by_h(X, Hs, lambda h: max(2 * h, 20)) * ANN
        res['se_nw5'] = nw_by_h(X, Hs, lambda h: 5) * ANN
        for k in ('dcore', 'dsamecap'):
            res['%s_ann' % k] = nw(arrs[k], 1)[0] * ANN
            res['%s_se_nwH' % k] = nw_by_h(arrs[k], Hs, lambda h: h) * ANN
        yrs = cal.dt.year.values
        m = np.isfinite(X)
        for y in sorted(set(yrs)):
            sel = yrs == y
            ys[y] = np.where(m[sel], X[sel], 0.0).sum(0)
            yc[y] = m[sel].sum(0).astype(float)
            with np.errstate(all='ignore'):
                res['y%d' % y] = ys[y] / yc[y] * ANN
                res['loyo_ex%d' % y] = np.where(m[~sel], X[~sel], 0.0).sum(0) / m[~sel].sum(0) * ANN
        for L in BLOCKS:
            W = sb_weights(T, B_DRAWS, L, SEED0 + 1000 * L + BOOT_CODE[s])
            num, den = boot_nd(X, W)
            sd = bands(res, num, den, fams, crit_rows, s, L, write=(L == BLOCKS[0]))
            res['se_boot%d' % L] = sd * ANN
            for sc, segs in (('full', DER), ('post', POST), ('all4', SEGS)):
                if s in segs:
                    if (sc, L) not in acc:
                        acc[(sc, L)] = [np.zeros_like(num), np.zeros_like(den)]
                    acc[(sc, L)][0] += num
                    acc[(sc, L)][1] += den
            del num, den, W
        out[s] = finish(res)
        log('[%s] 分段统计 + bootstrap 重放完成' % s)
    for sc, segs in (('full', DER), ('post', POST), ('all4', SEGS)):
        res = pd.DataFrame({'descriptor_id': common})
        mu, se, n = merged([data[s][1]['dnet8'] for s in segs], Hs)
        res['n_days'], res['d_net8_ann'], res['se_nwH'] = n, mu * ANN, se * ANN
        for k in ('dcore', 'dsamecap'):
            mk, sk, _ = merged([data[s][1][k] for s in segs], Hs)
            res['%s_ann' % k], res['%s_se_nwH' % k] = mk * ANN, sk * ANN
        yy = sorted(y for s in segs for y in set(data[s][3].dt.year.values))
        ts_, tc_ = sum(ys[y] for y in yy), sum(yc[y] for y in yy)
        with np.errstate(all='ignore'):
            for y in yy:
                res['y%d' % y] = ys[y] / yc[y] * ANN
                res['loyo_ex%d' % y] = (ts_ - ys[y]) / (tc_ - yc[y]) * ANN
        for L in BLOCKS:
            num, den = acc[(sc, L)]
            sd = bands(res, num, den, fams, crit_rows, sc, L, write=(L == BLOCKS[0]))
            res['se_boot%d' % L] = sd * ANN
        out[sc] = finish(res)
        log('[%s] 合并统计完成' % sc)
    acc.clear()
    for sc, rule in (('all4_ex1516', lambda s, d: ~np.isin(d.dt.year.values, [2015, 2016])),
                     ('all4_ex2024p', lambda s, d: np.full(len(d), s != '2024-2026'))):
        res = pd.DataFrame({'descriptor_id': common})
        for k, lab in (('dnet8', 'd_net8'), ('dcore', 'dcore'), ('dsamecap', 'dsamecap')):
            parts = [np.where(rule(s, data[s][3])[:, None], data[s][1][k], np.nan) for s in SEGS]
            mu, se, n = merged(parts, Hs)
            if k == 'dnet8':
                res['n_days'], res['d_net8_ann'], res['se_nwH'] = n, mu * ANN, se * ANN
            else:
                res['%s_ann' % lab], res['%s_se_nwH' % lab] = mu * ANN, se * ANN
        out[sc] = finish(res)
    meta0[['descriptor_id', 'route_id', 'mother_id', 'member_id', 'role', 'strength', 'policy', 'direction',
           'direction_role', 'H', 'representative']].to_csv(os.path.join(WORK, 'meta.csv'), index=False)
    for sc, res in out.items():
        res.to_csv(os.path.join(WORK, 'rc_%s.csv' % sc), index=False)
    pd.DataFrame(crit_rows).to_csv(os.path.join(WORK, 'rc_family_crit.csv'), index=False)
    json.dump(dict(idmis=idmis, e2_max=e2, n_common=J), open(os.path.join(WORK, 'rc_checks.json'), 'w'))
    compare_C0(out, crit_rows, idmis, e2)


TABLES = {'2010-2014': 'statistics/descriptor_stats_2010-2014.csv', '2015-2018': 'statistics/descriptor_stats_2015-2018.csv',
          'full': 'statistics/descriptor_stats_full.csv', '2019-2023': 'statistics/post/descriptor_stats_2019-2023.csv',
          '2024-2026': 'statistics/post/descriptor_stats_2024-2026.csv', 'post': 'statistics/post/descriptor_stats_post.csv',
          'all4': 'statistics/post/descriptor_stats_all4.csv', 'all4_ex1516': 'statistics/post/descriptor_stats_all4_ex1516.csv',
          'all4_ex2024p': 'statistics/post/descriptor_stats_all4_ex2024p.csv'}


def compare_C0(out, crit_rows, idmis, e2):
    for s in SEGS:
        v_exact('C1', '(ii) %s npz 内 descriptor_id = 索引行（不符个数）' % s, 0, idmis[s], func='load_ledgers')
    for sc, res in out.items():
        tab = rd(os.path.join(RD, TABLES[sc])).set_index('descriptor_id')
        r = res.set_index('descriptor_id')
        v_exact('C1', '(ii) %s 描述符集合（表 %d / 重算 %d；对称差个数）' % (sc, len(tab), len(r)), 0,
                len(set(tab.index) ^ set(r.index)), inputs=TABLES[sc], func='set')
        tab = tab.loc[r.index]
        for c in r.columns:
            if c not in tab.columns:
                continue
            a, b = tab[c], r[c]
            if c == 'state_word':
                v_exact('C1', '(ii) %s.state_word 逐描述符不符个数' % sc, 0, int((a.astype(str).values != b.astype(str).values).sum()),
                        func='stage_C0')
                continue
            if a.dtype == bool or b.dtype == bool or c == 'ci_excludes_zero':
                nd = int((a.astype(bool).values != b.astype(bool).values).sum())
                v_exact('C1', '(ii) %s.%s 逐描述符不符个数' % (sc, c), 0, nd, func='stage_C0')
                continue
            a, b = pd.to_numeric(a, errors='coerce').values, pd.to_numeric(b, errors='coerce').values
            nan_mis = int((np.isnan(a) != np.isnan(b)).sum())
            mm = np.isfinite(a) & np.isfinite(b)
            d = float(np.max(np.abs(a[mm] - b[mm]))) if mm.any() else 0.0
            tol = 0 if c == 'n_days' else 1e-12
            ok = nan_mis == 0 and d <= tol
            rec('C1', '(ii) %s.%s 全量 %d 个 max|d|（NaN 位置不符 %d）' % (sc, c, len(r), nan_mis), 0.0, d,
                'REPRODUCED' if ok else 'DIFFERS', tol='|d|<=%g' % tol, func='stage_C0')
    fb = pd.concat([rd(os.path.join(RD, 'statistics', 'family_bands.csv')),
                    rd(os.path.join(RD, 'statistics', 'post', 'family_bands_post.csv'))], ignore_index=True)
    cr = pd.DataFrame(crit_rows)
    k = ['scope', 'block', 'level', 'family']
    j = fb.merge(cr, on=k, suffixes=('_tab', '_rc'), how='outer', indicator=True)
    v_exact('C8', '家族临界值行集合（表 %d / 重放 %d）' % (len(fb), len(cr)), 0, int((j._merge != 'both').sum()),
            inputs=['statistics/family_bands.csv', 'statistics/post/family_bands_post.csv'], func='merge')
    jj = j[j._merge == 'both']
    for c in ('n_members', 'n_valid', 'n_zero_se'):
        v_exact('C8', '家族 %s 不符个数' % c, 0, int((jj[c + '_tab'] != jj[c + '_rc']).sum()), func='bands')
    d = np.abs(jj.crit_tab - jj.crit_rc)
    rec('C8', '家族临界值 crit max|d|（%d 行；同 seed 重放）' % len(jj), 0.0, float(d.max()),
        'REPRODUCED' if float(d.max()) <= 1e-12 else 'DIFFERS', tol='|d|<=1e-12', func='bands')
    v_close('E2', '日账本 net8 = gross − 8e−4·turn 逐日残差 max（四段全部描述符）', 0.0, max(e2.values()), 1e-12, func='load_ledgers')


# ============================================================ V-B 服役集与锚
MOTHERS = ('R1', 'R2', 'A06', 'A08')
WCACHE = '/mnt/sda2/lichenchen/data/cache_e6f'       # 钉住引擎的影子缓存目录（只在未命中时写）


def dir_snapshot(d):
    snap = {}
    if os.path.isdir(d):
        for f in os.listdir(d):
            p = os.path.join(d, f)
            st = os.lstat(p)
            snap[f] = (st.st_size, int(st.st_mtime), os.path.islink(p))
    return snap


def stored_mother_net8(seg, pn, h, k=5):
    """账本导出的母体逐日 net8 = 子 net8 − dnet8（同 H 真实母体）；取最多 k 个主路线描述符，互相核一致。"""
    od = os.path.join(RD, 'accounts', seg)
    idx = rd(os.path.join(od, 'merged_index.csv'))
    meta = pd.concat([rd(f, usecols=['descriptor_id', 'status', 'route_id', 'mother_id', 'H'])
                      for f in sorted(glob.glob(os.path.join(od, 'merged_*.csv'))) if not f.endswith('merged_index.csv')])
    meta = meta[(meta.status == 'SUCCEEDED') & (meta.mother_id == pn) & (meta.H.astype(int) == h)
                & ~meta.route_id.isin(['M1', 'M2', 'FOURARM'])]
    sel = idx[idx.descriptor_id.isin(set(meta.descriptor_id))]
    sel = sel.groupby('route').head(1).head(k)
    xs, ids = [], []
    for r in sel.itertuples():
        with np.load(os.path.join(od, r.npz)) as z:
            assert z['descriptor_id'][r.row] == r.descriptor_id
            xs.append(z['net8'][r.row] - z['dnet8'][r.row])
            ids.append(r.descriptor_id)
    return xs, ids


def stage_B(part):
    ck = os.path.join(RD, 'checks')
    if part in ('all', 'anchors'):
        for s in DER:
            e = json.load(open(os.path.join(ck, 'engine_anchor_%s.json' % s)))
            v_exact('B2', '引擎锚 %s 通过/检查' % s, (48, 48), (e['n_pass'], e['n_checked']), inputs='checks/engine_anchor_%s.json' % s,
                    func='json')
            mx = max(r_['net8_max_abs'] for r_ in e['rows'])
            v_close('B2', '引擎锚 %s 逐日 net8 最大差（≤ 2.3e−15）' % s, 0.0, mx, 2.3e-15, func='json',
                    note='REPORT R0 §1 印 1.2e−15 / 2.3e−15')
            fa = json.load(open(os.path.join(ck, 'feature_anchors_%s.json' % s)))
            v_exact('B3', '特征锚 %s' % s, (19, 19), (fa['n_pass'], fa['n_anchor']), func='json')
            ra = json.load(open(os.path.join(ck, 'rule_anchors_%s.json' % s)))
            v_exact('B3', '算子锚 %s' % s, (65, 65), (ra['n_pass'], ra['n']), func='json')
            la = json.load(open(os.path.join(ck, 'label_anchor_%s.json' % s)))
            v_exact('B3', '标签锚 %s max|d| bp' % s, 0.0, float(la['max_abs_bp']), func='json')
            sp = json.load(open(os.path.join(ck, 'sparse_engine_anchor_%s.json' % s)))
            v_exact('B3', '稀疏引擎锚 %s' % s, (168, 168), (sp['n_pass'], sp['n_rows']), func='json')
            v_exact('B3', '稀疏引擎锚 %s DEV 逐位' % s, 0.0, float(sp['dev_max_abs']), func='json')
            v_close('B3', '稀疏引擎锚 %s 账本 max|d|（≤ 6e−15）' % s, 0.0, float(sp['pnl_max_abs']), 6e-15, func='json')
        # SLOT 恒等（brief B3）：按构造等于母体的焦点臂——state=all_on（保留原焦点 = 母体）与 state=old（原 CVR 焦点 = 母体）——
        # 逐日 dnet8 必须恒为 0；另报逐日 dnet8 恒为 0 的其余描述符（M2 在该段每年都选零修改时等于母体）
        per, n_id, n_id0, n_oth, m2z = [], 0, 0, 0, {}
        for s in SEGS:
            od = os.path.join(RD, 'accounts', s)
            ids_all, zero_all = [], []
            for f in sorted(glob.glob(os.path.join(od, '*.npz'))):
                with np.load(f) as z:
                    d = z['dnet8']
                    fin = np.isfinite(d)
                    zero_all.append((np.where(fin, np.abs(d), 0.0).max(1) == 0) & fin.any(1))
                    ids_all.append(z['descriptor_id'].astype(str))
            ids, zero = np.concatenate(ids_all), np.concatenate(zero_all)
            ident = np.array([('|FOCAL_NEW|state=all_on|' in x) or ('|FOCAL_NEW|state=old|' in x) for x in ids])
            ism2 = np.array([x.startswith('M2|') for x in ids])
            n_id += int(ident.sum())
            n_id0 += int((ident & zero).sum())
            n_oth += int((zero & ~ident & ~ism2).sum())
            m2z[s] = '%d / %d' % (int((zero & ism2).sum()), int(ism2.sum()))
            per.append('%s %d/%d' % (s, int((ident & zero).sum()), int(ident.sum())))
        v_exact('B3', 'SLOT 恒等：按构造等于母体的焦点臂（state=all_on / old）逐日 dnet8 恒为 0（四段合计：个数 / 恒为 0 的个数）', (n_id, n_id),
                (n_id, n_id0), func='npz scan', note='逐段 %s' % '，'.join(per))
        v_exact('B3', '逐日 dnet8 恒为 0 的其余描述符（非上述恒等臂、非 M2）', 0, n_oth, func='npz scan',
                note='M2 中逐日 dnet8 恒为 0 的（该段每年都选零修改）：%s' % m2z)
    if part in ('all', 'replay'):
        before = dir_snapshot(WCACHE)
        sys.path.insert(0, PC)
        import e6h_core as H            # 钉住的引擎（E6h / E6g / E6f / E6e + 四地基），SHA 由 A12 核
        import e6h_run_routes as RR
        import e6h_rules as RU
        assert_no_e6i()
        HS = (1, 2, 3, 5, 10, 20)
        rows = []
        for s in SEGS:
            t0 = time.time()
            S = H.seg(s)
            need = rd(os.path.join(RD, 'registry', 'mother_needs_%s.csv' % s)).set_index('mother_id')
            for pn in MOTHERS:
                P = RR.ParentCtx(S, pn)
                g, p, u, n8 = P.pnl
                base = dict(pool0_per_day=float(S.p0c.sum(1).mean()), final_B_per_day=float(P.nb.mean()),
                            capital_pos_mean=float(np.nanmean(p[2:])), gross_ann=float(np.nanmean(g)) * ANN,
                            net8_ann=float(np.nanmean(n8)) * ANN)
                for c, v in base.items():
                    tol = 1e-12                  # brief §5 B1 预注册容差（人数 / 持仓的日均也是浮点均值）
                    v_close('B1', '%s %s %s（重放 vs mother_needs）' % (s, pn, c), float(need.loc[pn, c]), v, tol,
                            inputs='registry/mother_needs_%s.csv' % s, func='pinned H.seg + ParentCtx')
                rows.append(dict(segment=s, mother=pn, **base, net8_per_capital=base['net8_ann'] / base['capital_pos_mean']))
                for h in HS:
                    xs, ids = stored_mother_net8(s, pn, h)
                    if not xs:
                        rec('B2', '%s %s H%d 重放 vs 账本母体' % (s, pn, h), '账本母体序列', None, 'NOT_COMPUTABLE',
                            func='stored_mother_net8', note='账本里没有该 (母体, H) 的主路线描述符')
                        continue
                    _, _, _, rn = RU.run_mask(S, P.B, H_hold=h)
                    rn = np.asarray(rn, float)
                    inner = max(float(np.nanmax(np.abs(x - xs[0]))) for x in xs)
                    x0 = xs[0]
                    same_nan = bool(np.array_equal(np.isnan(x0), np.isnan(rn)))
                    mm = np.isfinite(x0) & np.isfinite(rn)
                    d = float(np.max(np.abs(x0[mm] - rn[mm]))) if mm.any() else np.nan
                    ok = same_nan and d <= 2.3e-15
                    rec('B2', '%s %s H%d 重放 vs 账本母体 逐日 max|d|' % (s, pn, h), 0.0, d, 'REPRODUCED' if ok else 'DIFFERS',
                        tol='<=2.3e-15 且 NaN 位置同', func='RU.run_mask vs net8−dnet8',
                        note='账本 %d 个描述符互差 max %.1e；NaN 位置同=%s；%s' % (len(xs), inner, same_nan, ids[0]))
            log('[%s] 母体重放完成 %.0fs' % (s, time.time() - t0))
            del S
        pd.DataFrame(rows).to_csv(os.path.join(WORK, 'mother_baseline_replay.csv'), index=False)
        after = dir_snapshot(WCACHE)
        chg = sorted(set(after) ^ set(before)) + sorted(k for k in set(after) & set(before) if after[k] != before[k])
        v_exact('B1', '重放期间钉住引擎缓存目录的新增 / 改动文件', [], chg, func='dir_snapshot',
                note='目录 %s（引擎未命中时才写）' % WCACHE)
        # part3 §0 印出值（T0_mother_baseline.csv 与 REPORT 两位小数）
        t0b = rd(os.path.join(RD, 'reports', 'part3_tables', 'T0_mother_baseline.csv'))
        rp = pd.DataFrame(rows).set_index(['segment', 'mother'])
        for r_ in t0b.itertuples():
            k = (r_.segment, r_.mother)
            for c_tab, c_rp in (('pool0_per_day', 'pool0_per_day'), ('held_per_day', 'final_B_per_day'), ('capital', 'capital_pos_mean'),
                                ('gross_ann', 'gross_ann'), ('net8_ann', 'net8_ann'), ('net8_per_capital', 'net8_per_capital')):
                v_close('B1', 'T0 表 %s %s %s（表值 vs 重放）' % (k[0], k[1], c_tab), float(getattr(r_, c_tab)), float(rp.loc[k, c_rp]),
                        1e-12, inputs='reports/part3_tables/T0_mother_baseline.csv', func='replay')


# ============================================================ V-C 聚合：从重算的逐描述符统计按报告口径重新汇总
MAIN = ('RT', 'RK', 'RV', 'RR', 'RO', 'RC', 'RA', 'RS', 'RL', 'TPAIR', 'FOURARM')
PRIM = ('primary', 'primary_inverse_mapped')
KINDS = ('basic', 'industry', 'persist20')
TAB2, TAB3, TAB1, TABR0 = ('reports/part2_tables', 'reports/part3_tables', 'reports/part1_tables', 'reports/R0_tables')


def panel():
    """part1 / part2 / part3 共用的逐描述符面板；数值列全部取自 V-C 核心从日账本重算的 work/rc_*.csv。"""
    meta = rd(os.path.join(WORK, 'meta.csv'))
    rc = {sc: rd(os.path.join(WORK, 'rc_%s.csv' % sc)).set_index('descriptor_id') for sc in TABLES}
    F = meta.copy()
    ix = F.descriptor_id

    def g(sc, c):
        return ix.map(rc[sc][c])
    F['d1'], F['d2'] = g('2010-2014', 'd_net8_ann'), g('2015-2018', 'd_net8_ann')
    for k, s in (('10-14', '2010-2014'), ('15-18', '2015-2018'), ('full', 'full')):     # part1 面板同名列
        F['d_' + k], F['se_' + k], F['state_' + k] = g(s, 'd_net8_ann'), g(s, 'se_nwH'), g(s, 'state_word')
        F['cix0_' + k], F['bdlo_' + k], F['bdhi_' + k] = g(s, 'ci_excludes_zero').astype(bool), g(s, 'band_domain_lo'), g(s, 'band_domain_hi')
    for k, s in (('10-14', '2010-2014'), ('15-18', '2015-2018')):
        F['dcore_ann_' + k], F['dcore_se_nwH_' + k] = g(s, 'dcore_ann'), g(s, 'dcore_se_nwH')
        F['dsamecap_ann_' + k] = g(s, 'dsamecap_ann')
    F['deriv'], F['se_deriv'], F['ci_deriv'] = g('full', 'd_net8_ann'), g('full', 'se_nwH'), g('full', 'ci_excludes_zero').astype(bool)
    for lv in ('domain', 'headline'):
        F['bdf_%s_lo' % lv], F['bdf_%s_hi' % lv] = g('full', 'band_%s_lo' % lv), g('full', 'band_%s_hi' % lv)
    F['p1'], F['p2'] = g('2019-2023', 'd_net8_ann'), g('2024-2026', 'd_net8_ann')
    F['post'], F['se_post'], F['ci_post'] = g('post', 'd_net8_ann'), g('post', 'se_nwH'), g('post', 'ci_excludes_zero').astype(bool)
    for lv in ('domain', 'axis', 'headline'):
        F['bd_%s_lo' % lv], F['bd_%s_hi' % lv] = g('post', 'band_%s_lo' % lv), g('post', 'band_%s_hi' % lv)
    F['state_post'], F['mde_post'] = g('post', 'state_word'), g('post', 'mde80')
    F['all4'], F['se_all4'], F['ci_all4'] = g('all4', 'd_net8_ann'), g('all4', 'se_nwH'), g('all4', 'ci_excludes_zero').astype(bool)
    F['state_all4'] = g('all4', 'state_word')
    F['ex1516'], F['ex2024p'] = g('all4_ex1516', 'd_net8_ann'), g('all4_ex2024p', 'd_net8_ann')
    for k, s in ((1, '2019-2023'), (2, '2024-2026')):
        F['dcore_ann_%d' % k], F['dsamecap_ann_%d' % k] = g(s, 'dcore_ann'), g(s, 'dsamecap_ann')
    F['dcore_ann_post'], F['dsamecap_ann_post'] = g('post', 'dcore_ann'), g('post', 'dsamecap_ann')
    for y in range(2010, 2027):
        F['y%d' % y] = g('all4', 'y%d' % y)
        F['all4_loyo_ex%d' % y] = g('all4', 'loyo_ex%d' % y)
    for y in range(2019, 2027):
        F['post_loyo_ex%d' % y] = g('post', 'loyo_ex%d' % y)
    for s in SEGS:
        z = rd(os.path.join(RD, 'statistics', 'zmap_summary_%s.csv' % s))
        zb = z[z.kind == 'basic'].set_index('descriptor_id')
        F['z_%s' % s] = ix.map(zb.d_real_minus_rand)
    F['z1'], F['z2'] = F['z_2019-2023'], F['z_2024-2026']
    sem = rd(os.path.join(RD, 'registry', 'feature_semantics_v2.csv')).set_index('member_id')
    F['family'] = F.member_id.map(sem.family_id)
    F['companion'] = F.descriptor_id.str.contains(r'\|(?:eqcap|cost_target|winsor)$')
    return F, rc


def md_tables(path):
    """解析 REPORT 里的 markdown 表：[(表头前一行的十项表头文本, 列名, 行字符串列表)]。"""
    L = open(path, encoding='utf-8').read().split('\n')
    out, i = [], 0
    while i < len(L):
        if L[i].startswith('|') and i + 1 < len(L) and L[i + 1].startswith('|---'):
            j = i - 1
            while j >= 0 and not L[j].strip():
                j -= 1
            hdr_ = L[j] if j >= 0 and L[j].startswith('> **汇总算子**') else ''
            cols = [c.strip() for c in L[i].strip().strip('|').split('|')]
            rows, k = [], i + 2
            while k < len(L) and L[k].startswith('|'):
                rows.append([c.strip() for c in L[k].strip().strip('|').split('|')])
                k += 1
            out.append((hdr_, cols, rows, i + 1))
            i = k
        else:
            i += 1
    return out


def find_table(path, cols_needed, hdr_has=''):
    for h, cols, rows, ln in md_tables(path):
        if all(c in cols for c in cols_needed) and hdr_has in h:
            return pd.DataFrame(rows, columns=cols), ln
    return None, None


def cmp_frame(pid, lab, rec_df, tab_df, keys, num_cols, cnt_cols=(), tol=1e-12, inputs=''):
    """重算表 vs 存档 CSV：行集合 EXACT；数值列 max|d| ≤ tol；计数列 EXACT。"""
    a = rec_df.set_index(keys)
    b = tab_df.set_index(keys)
    v_exact(pid, '%s 行集合（对称差）' % lab, 0, len(set(a.index) ^ set(b.index)), inputs=inputs, func='cmp_frame')
    com = a.index.intersection(b.index)
    for c in num_cols:
        x, y = pd.to_numeric(a.loc[com, c], errors='coerce').values, pd.to_numeric(b.loc[com, c], errors='coerce').values
        nm = int((np.isnan(x) != np.isnan(y)).sum())
        mm = np.isfinite(x) & np.isfinite(y)
        d = float(np.max(np.abs(x[mm] - y[mm]))) if mm.any() else 0.0
        rec(pid, '%s.%s max|d|（NaN 位置不符 %d）' % (lab, c, nm), 0.0, d, 'REPRODUCED' if (d <= tol and nm == 0) else 'DIFFERS',
            tol='|d|<=%g' % tol, func='cmp_frame')
    for c in cnt_cols:
        x = pd.to_numeric(a.loc[com, c], errors='coerce').fillna(-1).astype(int).values
        y = pd.to_numeric(b.loc[com, c], errors='coerce').fillna(-1).astype(int).values
        v_exact(pid, '%s.%s 不符行数' % (lab, c), 0, int((x != y).sum()), func='cmp_frame')


def cmp_printed_table(pid, lab, rec_df, rep_path, keys, colmap, hdr_has=''):
    """重算表 vs REPORT 印出表：逐格按印出位数。colmap = {REPORT 列名: 重算列名}。"""
    t, ln = find_table(rep_path, list(keys) + list(colmap), hdr_has)
    if t is None:
        rec(pid, '%s（REPORT 表）' % lab, '表存在', None, 'NOT_COMPUTABLE', func='find_table', note='REPORT 中未找到列 %s' % list(colmap))
        return
    r = rec_df.copy()
    for k in keys:
        r[k] = r[k].astype(str)
    r = r.set_index(list(keys))
    nd, nr, nrd, bad = 0, 0, 0, []
    for _, row in t.iterrows():
        key = tuple(str(row[k]) for k in keys)
        key = key[0] if len(key) == 1 else key
        if key not in r.index:
            nr += 1
            continue
        for cr_, cc in colmap.items():
            s = row[cr_]
            if s in ('—', '', 'nan', 'NA'):
                continue
            try:
                e, pct = to_float(s)
            except Exception:
                if str(r.loc[key, cc]) != s:
                    nd += 1
                    bad.append('%s/%s' % (key, cr_))
                continue
            g = float(r.loc[key, cc]) * (100.0 if pct else 1.0)
            dd = decimals(s)
            if abs(round(g, dd) - e) < 0.5 * 10 ** (-dd):
                continue
            if abs(round(g, dd) - e) <= 10 ** (-dd) + 1e-12:
                nrd += 1
                continue
            nd += 1
            bad.append('%s/%s 印 %s 算 %.6g' % (key, cr_, s, g))
    v = 'DIFFERS' if (nd or nr) else ('REPRODUCED|ROUNDING' if nrd else 'REPRODUCED')
    rec(pid, '%s：REPORT 表（第 %d 行）%d 行 x %d 列逐格按印出位数' % (lab, ln, len(t), len(colmap)), 0, nd + nr, v,
        tol='印出位数', inputs=rep_path, func='cmp_printed_table',
        note='不符 %d 格、未匹配行 %d、末位舍入 %d；%s' % (nd, nr, nrd, '; '.join(bad[:6])))


def block(g):
    ci = g.ci_post
    return dict(n=len(g), deriv=g.deriv.median(), p1=g.p1.median(), p2=g.p2.median(), post=g.post.median(),
                all4=g.all4.median(), post_pos=(g.post > 0).mean(), both_post_pos=((g.p1 > 0) & (g.p2 > 0)).mean(),
                ci_pos=int((ci & (g.post > 0)).sum()), ci_neg=int((ci & (g.post < 0)).sum()),
                band_pos=int((g.bd_domain_lo > 0).sum()), band_neg=int((g.bd_domain_hi < 0).sum()))


def fam_tab(g, by='family'):
    YC = ['y%d' % y for y in range(2010, 2027)]
    rows = []
    for key, x in g.groupby(by):
        ym = x[YC].median()
        ci = x.ci_post.astype(bool)
        rows.append({by: key, 'n_mem': int(x.member_id.nunique()), 'n': len(x), 'd10_14': x.d1.median(), 'd15_18': x.d2.median(),
                     'p19_23': x.p1.median(), 'p24_26': x.p2.median(),
                     'yrs_pos': '%d/%d' % (int((ym > 0).sum()), int(ym.notna().sum())),
                     'ci_pos': int((ci & (x.post > 0)).sum()), 'ci_neg': int((ci & (x.post < 0)).sum()), 'post': x.post.median(),
                     'samecap_19_23': x.dsamecap_ann_1.median(), 'samecap_24_26': x.dsamecap_ann_2.median(),
                     'vs_rand_19_23': x.z1.median(), 'vs_rand_24_26': x.z2.median(), 'mde80_post': x.mde_post.median()})
    return pd.DataFrame(rows)


def spearman(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    return float(pd.Series(a[m]).rank().corr(pd.Series(b[m]).rank())) if m.sum() >= 5 else np.nan


def cmp_panel(pid, lab, F, path, cols):
    """REPORT 各节汇总的输入面板（part1 / part2 descriptor_panel）逐列对重算面板：数值 1e−12、布尔 / 文本逐个。"""
    P = rd(path).set_index('descriptor_id')
    R_ = F.set_index('descriptor_id')
    v_exact(pid, '%s 描述符集合（面板 %d / 重算 %d；对称差）' % (lab, len(P), len(R_)), 0, len(set(P.index) ^ set(R_.index)),
            inputs=path, func='cmp_panel')
    com = P.index.intersection(R_.index)
    nnum, worst, bad = 0, 0.0, []
    for c in cols:
        if c not in P.columns or c not in R_.columns:
            bad.append('%s（缺列）' % c)
            continue
        a, b = P.loc[com, c], R_.loc[com, c]
        if a.dtype == bool or b.dtype == bool or c.startswith(('ci_', 'cix0_')) or c == 'companion':
            nd = int((a.astype(bool).values != b.astype(bool).values).sum())
        elif a.dtype == object or b.dtype == object:
            nd = int((a.astype(str).values != b.astype(str).values).sum())
        else:
            x, y = pd.to_numeric(a, errors='coerce').values, pd.to_numeric(b, errors='coerce').values
            nd = int((np.isnan(x) != np.isnan(y)).sum())
            mm = np.isfinite(x) & np.isfinite(y)
            if mm.any():
                d = float(np.max(np.abs(x[mm] - y[mm])))
                worst = max(worst, d)
                nd += int((np.abs(x[mm] - y[mm]) > 1e-12).sum())
            nnum += 1
        if nd:
            bad.append('%s:%d' % (c, nd))
    rec(pid, '%s：%d 列 x %d 描述符逐格（数值列 %d，max|d| %.1e）' % (lab, len(cols), len(com), nnum, worst), 0, len(bad),
        'DIFFERS' if bad else 'REPRODUCED', tol='数值 |d|<=1e-12；布尔 / 文本逐个', inputs=path, func='cmp_panel',
        note='不符列：%s' % ('; '.join(bad[:12]) if bad else '无'))


def stage_C():
    F, rc = panel()
    P2R, P3R, P1R = (os.path.join(RD, 'reports', f) for f in ('E6i_REPORT_part2.md', 'E6i_REPORT_part3.md', 'E6i_REPORT_part1.md'))
    M = F[~F.companion & F.route_id.isin(MAIN)].copy()                 # part2 主描述符
    D = F[~F.companion & ~F.route_id.isin(['M1', 'M2'])].copy()          # part1 主描述符
    v_exact('C7', 'part2 主描述符数', 35384, len(M), func='panel')
    v_exact('C7', 'part1 主描述符数', 35384, len(D), func='panel')
    # ---- C1 part2 §2 路线 x 母体
    t2 = pd.DataFrame([dict(route=rt, mother=mo, **block(g)) for (rt, mo), g in M.groupby(['route_id', 'mother_id'])])
    cmp_frame('C1', 'T2_route_mother_post', t2, rd(os.path.join(RD, TAB2, 'T2_route_mother_post.csv')), ['route', 'mother'],
              ['deriv', 'p1', 'p2', 'post', 'all4', 'post_pos', 'both_post_pos'], ['n', 'ci_pos', 'ci_neg', 'band_pos', 'band_neg'],
              inputs=os.path.join(TAB2, 'T2_route_mother_post.csv'))
    v_exact('C1', 'T2 行数（brief 写 33）', 33, len(t2), func='block', note='T2_route_mother_post.csv 与 REPORT §2 表均为 %d 行' % len(t2))
    cmp_printed_table('C1', 'part2 §2 表', t2, P2R, ['route', 'mother'],
                      {c: c for c in ('n', 'deriv', 'p1', 'p2', 'post', 'all4', 'post_pos', 'both_post_pos', 'ci_pos', 'ci_neg',
                                      'band_pos', 'band_neg')}, hdr_has='需求域内全部描述符')
    rk = t2[(t2.route == 'RK') & (t2.mother == 'R2')].iloc[0]
    for c, e in (('n', '1368'), ('deriv', '0.107'), ('p1', '-0.075'), ('p2', '-0.354'), ('post', '-0.130'), ('all4', '0.010'),
                 ('post_pos', '0.379'), ('both_post_pos', '0.172'), ('ci_pos', '64'), ('ci_neg', '393'), ('band_pos', '0'),
                 ('band_neg', '120')):
        v_printed('C1', 'RK R2 %s（brief 例）' % c, e, rk[c], scale=1.0, func='block')
    # ---- C2 K 槽位
    K = M[(M.route_id == 'RK') & M.direction_role.isin(PRIM) & (M.policy == 'FALLBACK')].copy()
    K['a'] = pd.to_numeric(K.strength, errors='coerce')
    v_exact('C2', 'K 槽位描述符数', 1134, len(K), func='filter')
    v_exact('C2', 'K 槽位每母体 378', {'A06': 378, 'R1': 378, 'R2': 378}, {k: int(v) for k, v in K.mother_id.value_counts().items()},
            func='value_counts')
    for lab, val, e in (('推导合并', K.deriv.median(), '+0.278'), ('2019-23', K.p1.median(), '+0.099'),
                        ('2024-26', K.p2.median(), '-0.193'), ('四段合并', K.all4.median(), '+0.146')):
        v_printed('C2', 'K 槽位 %s 中位〔P3-S-K〕' % lab, e, val, func='median')
    ci = K.ci_post
    v_exact('C2', 'K 后段合并 NW 排除 0 正 / 负〔P2-S-K〕', (88, 68), (int((ci & (K.post > 0)).sum()), int((ci & (K.post < 0)).sum())),
            func='count')
    v_exact('C2', 'K 后段 need 域同步带 正 / 负〔P2-S-K〕', (1, 2), (int((K.bd_domain_lo > 0).sum()), int((K.bd_domain_hi < 0).sum())),
            func='count')
    exp_a = {0.125: ('+0.095', '+0.219', '+0.082', '-0.078'), 0.25: ('+0.181', '+0.414', '+0.114', '-0.149'),
             0.5: ('+0.277', '+0.761', '+0.161', '-0.804')}
    for a_, es in exp_a.items():
        x = K[K.a == a_]
        for c, e in zip(('d1', 'd2', 'p1', 'p2'), es):
            v_printed('C2', 'K α=%g %s 中位〔P3-FAM-AH / part3 §1b〕' % (a_, c), e, x[c].median(), func='median')
    for h_, es in ((1, ('+0.232', '-0.089')), (20, ('+0.042', '+0.008'))):
        x = K[K.H == h_]
        for c, e in zip(('p1', 'p2'), es):
            v_printed('C2', 'K H%d %s 中位' % (h_, c), e, x[c].median(), func='median')
    ah = []
    for lab, col, vals in (('α', 'a', sorted(K.a.dropna().unique())), ('H', 'H', sorted(K.H.unique()))):
        for v_ in vals:
            x = K[K[col] == v_]
            ah.append(dict(group='%s=%g' % (lab, v_), n=len(x), d10_14=x.d1.median(), d15_18=x.d2.median(),
                           p19_23=x.p1.median(), p24_26=x.p2.median()))
    cmp_frame('C2', 'T1e_K_alpha_H', pd.DataFrame(ah), rd(os.path.join(RD, TAB3, 'T1e_K_alpha_H.csv')), ['group'],
              ['d10_14', 'd15_18', 'p19_23', 'p24_26'], ['n'], inputs=os.path.join(TAB3, 'T1e_K_alpha_H.csv'))
    kf = fam_tab(K)
    numc = ['d10_14', 'd15_18', 'p19_23', 'p24_26', 'post', 'samecap_19_23', 'samecap_24_26', 'vs_rand_19_23', 'vs_rand_24_26', 'mde80_post']
    cmp_frame('C2', 'T1c_K_family', kf, rd(os.path.join(RD, TAB3, 'T1c_K_family.csv')), ['family'], numc,
              ['n_mem', 'n', 'ci_pos', 'ci_neg'], inputs=os.path.join(TAB3, 'T1c_K_family.csv'))
    t1c = rd(os.path.join(RD, TAB3, 'T1c_K_family.csv')).set_index('family')
    v_exact('C2', 'T1c yrs_pos 列逐行一致', 0, int((kf.set_index('family').yrs_pos != t1c.loc[kf.family, 'yrs_pos']).sum()), func='fam_tab')
    ar = kf.set_index('family').loc['amount_response']
    for c, e in (('n', '144'), ('d10_14', '0.196'), ('d15_18', '0.591'), ('p19_23', '0.192'), ('p24_26', '0.041'),
                 ('ci_pos', '30'), ('ci_neg', '11'), ('samecap_19_23', '0.195'), ('samecap_24_26', '0.090'),
                 ('vs_rand_19_23', '0.259'), ('vs_rand_24_26', '0.239'), ('mde80_post', '0.493')):
        v_printed('C2', 'amount_response %s（brief 例）' % c, e, ar[c], func='fam_tab')
    v_exact('C2', 'amount_response yrs_pos', '14/17', ar['yrs_pos'], func='fam_tab')
    ks = fam_tab(K[(K.a <= 0.25) & (K.H >= 10)])
    cmp_frame('C2', 'T1f_K_family_slice', ks, rd(os.path.join(RD, TAB3, 'T1f_K_family_slice.csv')), ['family'], numc,
              ['n_mem', 'n', 'ci_pos', 'ci_neg'], inputs=os.path.join(TAB3, 'T1f_K_family_slice.csv'))
    km = fam_tab(K[K.family.isin(['amount_response', 'turnover_response', 'source_bridge'])], by='member_id')
    cmp_frame('C2', 'T1d_K_members_response', km, rd(os.path.join(RD, TAB3, 'T1d_K_members_response.csv')), ['member_id'], numc,
              ['n', 'ci_pos', 'ci_neg'], inputs=os.path.join(TAB3, 'T1d_K_members_response.csv'))
    # ---- C3 两期为正 11 成员（研究目录规则）
    PRIMc = ('primary', 'primary_inverse_mapped', 'high_role', 'reversal_domain')
    single = M[~M.member_id.astype(str).str.contains(r'[|+]')]
    single = single[single.direction_role.isin(PRIMc)]
    mem = single.groupby('member_id').agg(n=('descriptor_id', 'size'), deriv=('deriv', 'median'), post=('post', 'median'),
                                          all4=('all4', 'median'))
    both = mem[(mem.deriv > 0.05) & (mem.post > 0.05)]
    exp11 = {'K_sdsx20': ('0.879', '0.084', '0.404'), 'K_samt20': ('0.790', '0.218', '0.365'), 'K_dxr20': ('0.717', '0.067', '0.361'),
             'T_std20': ('0.454', '0.098', '0.303'), 'K_amt20': ('0.679', '0.211', '0.263'), 'K_slope20': ('0.458', '0.102', '0.250'),
             'K_MA3_E6F': ('0.199', '0.246', '0.220'), 'K_amt5': ('0.540', '0.071', '0.213'), 'T_iqr20': ('0.240', '0.109', '0.169'),
             'K_MA5_E6F': ('0.198', '0.120', '0.166'), 'T_mad20': ('0.166', '0.113', '0.113')}
    v_exact('C3', '两期为正成员集合', sorted(exp11), sorted(both.index), func='catalog rule')
    for mid, es in exp11.items():
        if mid in both.index:
            for c, e in zip(('deriv', 'post', 'all4'), es):
                v_printed('C3', '%s %s' % (mid, c), e, both.loc[mid, c], func='median')
    t1b = rd(os.path.join(RD, TAB3, 'T1b_members_both_periods.csv')).set_index('member_id')
    for c_rec, c_tab in (('deriv', 'deriv_median'), ('post', 'post_median'), ('all4', 'all4_median'), ('n', 'n_primary_single')):
        d = np.abs(both[c_rec].astype(float) - t1b.loc[both.index, c_tab].astype(float))
        v_close('C3', 'T1b.%s max|d|' % c_tab, 0.0, float(d.max()), 1e-12, inputs=os.path.join(TAB3, 'T1b_members_both_periods.csv'),
                func='catalog rule')
    # ---- C4 P20
    rep = M[(M.route_id == 'RT') & (M.direction_role == 'primary') & M.policy.isin(['FULL_REPLACE', 'FALLBACK_REPLACE'])]
    tp = M[M.route_id == 'TPAIR']
    v_exact('C4', 'P20 完全替换描述符数', 1312, len(rep), func='filter')
    for lab, val, e in (('核心 2019-23', rep.dcore_ann_1.median(), '-1.577'), ('核心 2024-26', rep.dcore_ann_2.median(), '-1.022'),
                        ('母体 2019-23', rep.p1.median(), '-1.641'), ('母体 2024-26', rep.p2.median(), '-1.114'),
                        ('TPAIR 2019-23', tp.p1.median(), '-0.603'), ('TPAIR 2024-26', tp.p2.median(), '-1.244'),
                        ('TPAIR 核心 2019-23', tp.dcore_ann_1.median(), '-0.619'), ('TPAIR 核心 2024-26', tp.dcore_ann_2.median(), '-1.217')):
        v_printed('C4', 'P20 %s〔P20-CORE / P20-TPAIR〕' % lab, e, val, func='median')
    # ---- C5 P21
    rr = M[(M.route_id == 'RR') & M.role.isin(['SWAP', 'ADD_SCORE'])]
    exp21 = {('continuation', 'ADD_SCORE'): (1080, '-0.067', '-0.070', '+0.026', '+0.095'),
             ('continuation', 'SWAP'): (1080, '-1.179', '-1.061', '-0.455', '-0.334'),
             ('reversal', 'ADD_SCORE'): (1080, '-0.075', '-0.224', '+0.025', '-0.070'),
             ('reversal', 'SWAP'): (1128, '-0.894', '-1.063', '-0.237', '-0.307')}
    for (dr_, ro_), g_ in rr.groupby(['direction_role', 'role']):
        key = ('continuation' if 'contin' in dr_ else ('reversal' if 'rever' in dr_ else dr_), ro_)
        if key not in exp21:
            rec('C5', 'P21 %s / %s' % (dr_, ro_), '(brief 无此组)', len(g_), 'NOT_COMPUTABLE', func='groupby', note='brief 未列')
            continue
        n_, a_, b_, c_, d_ = exp21[key]
        v_exact('C5', 'P21 %s / %s 个数' % (dr_, ro_), n_, len(g_), func='groupby')
        for lab, val, e in (('对母体 2019-23', g_.p1.median(), a_), ('对母体 2024-26', g_.p2.median(), b_),
                            ('对随机 2019-23', g_.z1.median(), c_), ('对随机 2024-26', g_.z2.median(), d_)):
            v_printed('C5', 'P21 %s / %s %s〔P21-Z〕' % (dr_, ro_, lab), e, val, func='median')
    # ---- C6 RV 反向、RC 槽位
    rv = M[(M.route_id == 'RV') & (M.direction_role == 'reverse_control') & M.role.isin(['VETO_NEW', 'SOFT_HARD'])]
    v_printed('C6', 'RV 反向删除 2024-26〔Q3P-REV〕', '+0.991', rv.p2.median(), func='median')
    v_printed('C6', 'RV 反向删除 2019-23〔Q3P-REV〕', '-0.794', rv.p1.median(), func='median')
    sl = M[(M.route_id == 'RC') & (M.direction_role == 'primary') & (M.role == 'SLOT')]
    for lab, val, e in (('2019-23', sl.p1.median(), '+0.008'), ('2024-26', sl.p2.median(), '+0.073'), ('推导', sl.deriv.median(), '-0.243')):
        v_printed('C6', 'RC A06 槽位 %s〔Q6P-SLOT〕' % lab, e, val, func='median')
    fo = M[(M.route_id == 'RC') & (M.direction_role == 'focal_arm') & (M.role == 'FOCAL_NEW')]
    for lab, val, e in (('2019-23', fo.p1.median(), '-0.117'), ('2024-26', fo.p2.median(), '-0.149')):
        v_printed('C6', 'RC none 臂 %s' % lab, e, val, func='median')
    # ---- C7 NW 计数
    cd = D.ci_deriv
    v_exact('C7', '推导合并 NW 排除 0 正 / 负〔P1-ALL-CI〕', (2093, 16284), (int((cd & (D.deriv > 0)).sum()), int((cd & (D.deriv < 0)).sum())),
            func='count')
    cp = M.ci_post
    v_exact('C7', '后段合并 NW 排除 0 正 / 负〔P2-ALL-CI〕', (231, 14791), (int((cp & (M.post > 0)).sum()), int((cp & (M.post < 0)).sum())),
            func='count')
    v_printed('C7', '零增量参照 35,384 x 0.025', '885', 0.025 * len(M), func='arith')
    # ---- C8 同步带计数
    v_exact('C8', '推导 need 域同步带 正 / 负〔P1-ALL-BAND〕', (242, 6533),
            (int((D.bdf_domain_lo > 0).sum()), int((D.bdf_domain_hi < 0).sum())), func='count')
    v_exact('C8', '推导全 headline 同步带 正 / 负〔P1-ALL-BAND〕', (68, 4026),
            (int((D.bdf_headline_lo > 0).sum()), int((D.bdf_headline_hi < 0).sum())), func='count')
    v_exact('C8', '后段 need 域同步带 正 / 负〔P2-ALL-BAND〕', (3, 3690), (int((M.bd_domain_lo > 0).sum()), int((M.bd_domain_hi < 0).sum())),
            func='count')
    v_exact('C8', 'headline 家族规模（全部描述符）', 39800, len(F), func='len')
    # ---- C9 Z-MAP
    exp_z = {'2010-2014': (2.89, '0.011'), '2015-2018': (3.70, '0.017'), '2019-2023': (3.85, '0.017'), '2024-2026': (5.86, '0.022')}
    for s in SEGS:
        zp = os.path.join(RD, 'statistics', 'zmap_summary_%s.csv' % s)
        z = rd(zp)
        zk = z[z.kind.isin(KINDS)].copy()
        zk['cfg'] = zk.descriptor_id.str.replace(r'\|H\d+$', '', regex=True)
        gg = zk.groupby(['cfg', 'kind']).n_paths.agg(['max', 'min'])
        v_exact('C9', '%s (描述符, 机制) 行数' % s, 104856, len(zk), inputs=zp, func='zmap_summary')
        if s in DER:
            v_exact('C9', '%s (配置, 机制) 数' % s, 27264, len(gg), func='groupby')
        v_printed('C9', '%s 路径（按配置计，百万）' % s, '%.2f' % exp_z[s][0], gg['max'].sum() / 1e6, func='groupby')
        v_exact('C9', '%s 组内各 H 的 n_paths 不齐的组数' % s, 0, int((gg['max'] != gg['min']).sum()), func='groupby')
        v_printed('C9', '%s MCSE 中位' % s, exp_z[s][1], zk.rand_net8_mcse.median(), func='median')
        v_printed('C9', '%s MCSE 最大' % s, '0.050', zk.rand_net8_mcse.max(), func='max')
        v_exact('C9', '%s MCSE > 0.05 行数' % s, 0, int((zk.rand_net8_mcse > 0.05).sum()), func='count')
        rd_ = os.path.join(RD, 'randoms', s)
        fs = [f for f in sorted(glob.glob(os.path.join(rd_, '*.csv')))
              if not (os.path.basename(f).startswith('selftest') or f.endswith('_anchor.csv'))]
        sh = pd.concat([rd(f, usecols=lambda c: c in ('descriptor_id', 'kind', 'n_paths', 'status', 'rand_net8_mean', 'real_net8_ann'))
                        for f in fs], ignore_index=True)
        sh = sh[(sh.status == 'SUCCEEDED') & sh.kind.isin(KINDS)].copy()
        sh['wm'] = sh.n_paths * sh.rand_net8_mean
        agg = sh.groupby(['descriptor_id', 'kind']).agg(n=('n_paths', 'sum'), wm=('wm', 'sum'), real=('real_net8_ann', 'first'))
        zz = zk.set_index(['descriptor_id', 'kind'])
        com = agg.index.intersection(zz.index)
        v_exact('C9', '%s 分片 n_paths 之和 = 汇总 n_paths（不符 / 汇总有而分片无）' % s, (0, 0),
                (int((agg.loc[com, 'n'] != zz.loc[com, 'n_paths']).sum()), len(zz.index.difference(agg.index))), func='randoms shard csv',
                note='%d 个分片文件（含补轮 p64_n192 与 v13 分片；补轮为增量路径）' % len(fs))
        wmean = agg.loc[com, 'wm'] / agg.loc[com, 'n']
        v_close('C9', '%s 汇总 rand_net8_mean = 分片按路径数加权均值 max|d|' % s, 0.0,
                float(np.nanmax(np.abs(wmean.values - zz.loc[com, 'rand_net8_mean'].values))), 1e-12, func='randoms shard csv')
        dz = (zz.loc[com, 'real_net8_ann'] - zz.loc[com, 'rand_net8_mean']) - zz.loc[com, 'd_real_minus_rand']
        v_close('C9', '%s 汇总 d_real_minus_rand = real − rand_mean 残差 max' % s, 0.0, float(np.nanmax(np.abs(dz.values))), 1e-12,
                func='identity')
    t4 = rd(os.path.join(RD, TAB2, 'T4_mechanism_post.csv')).set_index('route')
    for rt, e1, e2 in (('RK', '+0.063', '+0.064'), ('RS', '-0.218', '-0.139')):
        g_ = M[M.route_id == rt]
        v_printed('C9', '%s 后段 2019-23 真实−随机 中位' % rt, e1, g_.z1.median(), func='median')
        v_printed('C9', '%s 后段 2024-26 真实−随机 中位' % rt, e2, g_.z2.median(), func='median')
    t4r = []
    for rt, g_ in M.groupby('route_id'):
        r_ = dict(route=rt, n=len(g_))
        for k, lab in (('1', '19-2023'), ('2', '24-2026')):
            r_['%s 子−母' % lab] = g_['p' + k].median()
            r_['%s 子−同人数核心' % lab] = g_['dcore_ann_' + k].median()
            r_['%s 同资本' % lab] = g_['dsamecap_ann_' + k].median()
            r_['%s 真实−随机' % lab] = g_['z' + k].median()
            r_['%s 真实−随机>0' % lab] = (g_['z' + k] > 0).mean() if g_['z' + k].notna().any() else np.nan
        t4r.append(r_)
    t4r = pd.DataFrame(t4r)
    cmp_frame('C9', 'T4_mechanism_post（Δgross / Δturn 两列是表层，不在账本；其余从重算面板）', t4r, t4.reset_index(), ['route'],
              [c for c in t4r.columns if c not in ('route', 'n')], ['n'], inputs=os.path.join(TAB2, 'T4_mechanism_post.csv'))
    sw = M.pivot_table(index='route_id', columns='state_post', values='descriptor_id', aggfunc='size', fill_value=0)
    sw['mde80_median'] = M.groupby('route_id').mde_post.median()
    cmp_printed_table('C7', 'part2 §8 状态词计数表（δ = 0.25）', sw.reset_index(), P2R, ['route_id'],
                      {c: c for c in list(sw.columns)})
    # ---- C14 延续
    v_printed('C14', '推导 vs 后段秩相关（全部主描述符）〔P2-PERSIST〕', '+0.648', spearman(M.deriv.values, M.post.values), func='spearman')
    v_printed('C14', '同号占比', '78%', float((np.sign(M.deriv) == np.sign(M.post)).mean()), func='mean')
    v_exact('C14', '推导 NW 正 → 后段 > 0', (2093, 1104), (int((M.ci_deriv & (M.deriv > 0)).sum()),
                                                         int((M.ci_deriv & (M.deriv > 0) & (M.post > 0)).sum())), func='count')
    v_printed('C14', 'K 主方向秩相关〔P2-S-PERS〕', '+0.129', spearman(K.deriv.values, K.post.values), func='spearman')
    t3 = pd.DataFrame([dict(route=rt, n=len(g), rho_deriv_post=spearman(g.deriv.values, g.post.values),
                            same_sign=float((np.sign(g.deriv) == np.sign(g.post)).mean()),
                            deriv_pos_post_pos=float(((g.deriv > 0) & (g.post > 0)).sum() / max((g.deriv > 0).sum(), 1)),
                            deriv_ci_pos=int((g.ci_deriv & (g.deriv > 0)).sum()),
                            of_which_post_pos=int((g.ci_deriv & (g.deriv > 0) & (g.post > 0)).sum()),
                            mde80_post_median=g.mde_post.median(), mde80_deriv_median=(2.8 * g.se_deriv).median())
                       for rt, g in M.groupby('route_id')])
    cmp_frame('C14', 'T3_persistence', t3, rd(os.path.join(RD, TAB2, 'T3_persistence.csv')), ['route'],
              ['rho_deriv_post', 'same_sign', 'deriv_pos_post_pos', 'mde80_post_median', 'mde80_deriv_median'],
              ['n', 'deriv_ci_pos', 'of_which_post_pos'], inputs=os.path.join(TAB2, 'T3_persistence.csv'))
    # ---- C16 逐年 / LOYO
    ycols = ['y%d' % y for y in range(2010, 2027)]
    t7 = []
    for rt, g in M.groupby('route_id'):
        r_ = dict(route=rt)
        for c in ycols:
            r_[c[1:]] = g[c].median()
        r_['all4'], r_['all4 去15+16'], r_['all4 去2024+'] = g.all4.median(), g.ex1516.median(), g.ex2024p.median()
        t7.append(r_)
    t7 = pd.DataFrame(t7)
    t7t = rd(os.path.join(RD, TAB2, 'T7_yearly_route.csv'))
    t7t.columns = [str(c) for c in t7t.columns]
    cmp_frame('C16', 'T7_yearly_route', t7, t7t, ['route'], [c[1:] for c in ycols] + ['all4', 'all4 去15+16', 'all4 去2024+'],
              inputs=os.path.join(TAB2, 'T7_yearly_route.csv'))
    v_printed('C16', '后段合并去 2020 中位〔Q9-LOYO〕', '-0.398', M.post_loyo_ex2020.median(), func='median')
    v_printed('C16', '后段合并中位〔Q9-LOYO〕', '-0.377', M.post.median(), func='median')
    v_printed('C16', '后段合并去 2024 中位〔Q9-LOYO〕', '-0.377', M.post_loyo_ex2024.median(), func='median')
    t6 = []
    for rt, g in D.groupby('route_id'):
        r_ = dict(route=rt)
        for y in range(2010, 2019):
            r_[str(y)] = g['y%d' % y].median()
        t6.append(r_)
    cmp_printed_table('C16', 'part1 §6 逐年表', pd.DataFrame(t6), P1R, ['route'], {str(y): str(y) for y in range(2010, 2019)})
    # ---- C15 相对生产 H5
    stage_C15(F, M, D)
    # ---- C10 M2
    stage_C10(F, rc)
    # ---- C11 C1 / C12 C2
    stage_C11()
    stage_C12(rc)
    # ---- C13 R0 / C17 SWAP 分布
    stage_C13()
    stage_C17()
    # ---- 输入面板（REPORT 各节汇总全部从这两张面板出）逐列对重算面板
    c2 = ['p1', 'p2', 'post', 'se_post', 'ci_post', 'bd_domain_lo', 'bd_domain_hi', 'bd_axis_lo', 'bd_axis_hi', 'bd_headline_lo',
          'bd_headline_hi', 'state_post', 'mde_post', 'all4', 'se_all4', 'ci_all4', 'state_all4', 'ex1516', 'ex2024p', 'deriv', 'se_deriv',
          'ci_deriv', 'dcore_ann_1', 'dsamecap_ann_1', 'dcore_ann_2', 'dsamecap_ann_2', 'dcore_ann_post', 'dsamecap_ann_post'] +          ['y%d' % y for y in range(2010, 2027)] + ['post_loyo_ex%d' % y for y in range(2019, 2027)] +          ['all4_loyo_ex%d' % y for y in range(2010, 2027)] + ['companion', 'z1', 'z2', 'family'] +          ['%s_%s' % (a_, b_) for a_ in ('h1', 'h2', 'hp', 'h4') for b_ in ('prodH5', 'R1H5', 'R2H5')]
    cmp_panel('C1', '(iii) part2 输入面板 descriptor_panel_post', F, os.path.join(RD, TAB2, 'descriptor_panel_post.csv'), c2)
    c1 = ['%s_%s' % (a_, k) for k in ('10-14', '15-18', 'full') for a_ in ('d', 'se', 'state', 'cix0', 'bdlo', 'bdhi')] +          ['%s_%s' % (a_, k) for k in ('10-14', '15-18') for a_ in ('dcore_ann', 'dcore_se_nwH')] + ['companion']
    cmp_panel('C1', '(iii) part1 输入面板 descriptor_panel', F, os.path.join(RD, TAB1, 'descriptor_panel.csv'), c1)


def stage_C15(F, M, D):
    """vs 生产 H5：逐日 子 net8（自身 H）− 同母体 H5 net8（该母体任一非 M1/M2 的 H5 描述符的 net8 − dnet8），
       均值与 NW(lag 子的 H)；合并口径段间不拼接。与 statistics/vs_prodH5_*.csv 全量逐列比。"""
    per = {}
    REFS = (('prodH5', None, 'd_vs_prodH5_ann', 'se_nwH'), ('R1H5', 'R1', 'd_vs_R1H5_ann', 'se_vs_R1H5_nwH'),
            ('R2H5', 'R2', 'd_vs_R2H5_ann', 'se_vs_R2H5_nwH'))

    def cmp_cols(lab, r, tabp, pairs):
        tab = rd(tabp).set_index('descriptor_id')
        com = r.index.intersection(tab.index)
        v_exact('C15', '%s 描述符集合（表 %d / 重算 %d；对称差）' % (lab, len(tab), len(r)), 0, len(set(tab.index) ^ set(r.index)),
                inputs=tabp, func='stage_C15')
        for c_rec, c_tab in pairs:
            x, y = r.loc[com, c_rec].values.astype(float), tab.loc[com, c_tab].values.astype(float)
            nm = int((np.isnan(x) != np.isnan(y)).sum())
            mm = np.isfinite(x) & np.isfinite(y)
            d = float(np.max(np.abs(x[mm] - y[mm]))) if mm.any() else 0.0
            tol = 0 if c_tab == 'n_days' else 1e-12
            rec('C15', '%s.%s 全量 max|d|（NaN 位置不符 %d）' % (lab, c_tab, nm), 0.0, d,
                'REPRODUCED' if (d <= tol and nm == 0) else 'DIFFERS', tol='|d|<=%g' % tol, func='stage_C15')
    for s in SEGS:
        od = os.path.join(RD, 'accounts', s)
        meta = pd.concat([rd(f, usecols=['descriptor_id', 'status', 'route_id', 'mother_id', 'H'])
                          for f in sorted(glob.glob(os.path.join(od, 'merged_*.csv'))) if not f.endswith('merged_index.csv')])
        meta = meta[meta.status == 'SUCCEEDED'].reset_index(drop=True)
        idx = rd(os.path.join(od, 'merged_index.csv'))
        pos = dict(zip(idx.descriptor_id, zip(idx.npz, idx.row)))
        meta = meta[meta.descriptor_id.isin(pos)].reset_index(drop=True)
        by = {}
        for j, did in enumerate(meta.descriptor_id):
            f, r = pos[did]
            by.setdefault(f, []).append((j, int(r)))
        N8 = D8 = None
        for f, lst in by.items():
            with np.load(os.path.join(od, f)) as z:
                if N8 is None:
                    T = z['net8'].shape[1]
                    N8, D8 = np.full((T, len(meta)), np.nan), np.full((T, len(meta)), np.nan)
                jj = np.array([a for a, _ in lst])
                rr = np.array([b for _, b in lst])
                N8[:, jj] = z['net8'][rr].T
                D8[:, jj] = z['dnet8'][rr].T
        mH5, src = {}, {}
        for mo in MOTHERS:
            c = np.flatnonzero((meta.mother_id.values == mo) & (meta.H.astype(int).values == 5)
                               & ~meta.route_id.isin(['M1', 'M2']).values)
            if len(c):
                mH5[mo] = N8[:, c[0]] - D8[:, c[0]]
                with np.errstate(all='ignore'):
                    dd = np.abs((N8[:, c[:50]] - D8[:, c[:50]]) - mH5[mo][:, None])
                src[mo] = (len(c), float(np.nanmax(dd)) if np.isfinite(dd).any() else 0.0)
        mx = max(v[1] for v in src.values())
        rec('C15', '%s 母体 H5 逐日序列（同母体各 H5 描述符的 net8 − dnet8 互差 max，每母体前 50 个）' % s, 0.0, mx,
            'REPRODUCED' if mx <= 1e-12 else 'DIFFERS', tol='|d|<=1e-12', func='stage_C15',
            note='；'.join('%s %d 个' % (k, v[0]) for k, v in src.items()))
        Hs = meta.H.astype(int).values
        res = pd.DataFrame({'descriptor_id': meta.descriptor_id, 'H': Hs})
        for ref, key, cd, cs in REFS:
            X = np.full_like(N8, np.nan)
            for mo in MOTHERS:
                cols = np.flatnonzero(meta.mother_id.values == mo)
                base = mH5.get(key or mo)
                if base is not None and len(cols):
                    X[:, cols] = N8[:, cols] - base[:, None]
            mu, _, n = nw(X, 1)
            res[cd], res[cs] = mu * ANN, nw_by_h(X, Hs, lambda h: h) * ANN
            if ref == 'prodH5':
                res['n_days'] = n
            per.setdefault(s, {})[ref] = (meta.descriptor_id.values, Hs, X)
            if s in POST:                               # part2 面板 h1_* / h2_*
                F['h%d_%s' % (POST.index(s) + 1, ref)] = F.descriptor_id.map(pd.Series(mu * ANN, index=meta.descriptor_id.values))
        cmp_cols(s, res.set_index('descriptor_id'), os.path.join(RD, 'statistics', 'vs_prodH5_%s.csv' % s),
                 [('n_days', 'n_days')] + [(c, c) for _, _, cd, cs in REFS for c in (cd, cs)])
        del N8, D8
    for sc, segs, fn in (('full', DER, 'vs_prodH5_full.csv'), ('post_full', POST, 'vs_prodH5_post_full.csv'),
                         ('all4', SEGS, 'vs_prodH5_all4.csv')):
        ids0 = per[segs[0]]['prodH5'][0]
        keep = set(ids0)
        for s in segs[1:]:
            keep &= set(per[s]['prodH5'][0])
        ids = np.array([d for d in ids0 if d in keep], dtype=object)
        order = {s: pd.Index(per[s]['prodH5'][0]).get_indexer(ids) for s in segs}
        Hs = per[segs[0]]['prodH5'][1][order[segs[0]]]
        res = pd.DataFrame({'descriptor_id': ids, 'H': Hs})
        for ref, key, cd, cs in REFS:
            parts = [per[s][ref][2][:, order[s]] for s in segs]
            mu, se, n = merged(parts, Hs)
            res[cd], res[cs] = mu * ANN, se * ANN
            ser = pd.Series(mu * ANN, index=ids)
            if ref == 'prodH5' and sc == 'full':
                F['vs_full'] = F.descriptor_id.map(ser)
            if sc in ('post_full', 'all4'):
                F['%s_%s' % ('hp' if sc == 'post_full' else 'h4', ref)] = F.descriptor_id.map(ser)
        cmp_cols(sc, res.set_index('descriptor_id'), os.path.join(RD, 'statistics', fn),
                 [(c, c) for _, _, cd, cs in REFS for c in (cd, cs)])
    D2 = F[~F.companion & ~F.route_id.isin(['M1', 'M2'])]
    mg = (D2.vs_full - D2.deriv).groupby(D2.H).median()
    for h, e in ((1, '-1.259'), (2, '+0.331'), (3, '+0.589'), (5, '+0.000'), (10, '-1.325'), (20, '-1.813')):
        v_printed('C15', 'P1-VSH5 H%d 中位（vs_prod_H5 − same_H）' % h, e, mg.loc[h], func='median')
    g5 = D2.groupby(['route_id', 'H']).agg(n=('descriptor_id', 'size'), same_H=('deriv', 'median'), vs_prod_H5=('vs_full', 'median'),
                                          vs_H5_pos=('vs_full', lambda x: (x > 0).mean())).reset_index()
    v_exact('C15', 'part1 §5c 行数', 50, len(g5), func='groupby')
    cmp_printed_table('C15', 'part1 §5c 表', g5.rename(columns={'route_id': 'route_id'}), os.path.join(RD, 'reports', 'E6i_REPORT_part1.md'),
                      ['route_id', 'H'], {'n': 'n', 'same_H': 'same_H', 'vs_prod_H5': 'vs_prod_H5', 'vs_H5_pos': 'vs_H5_pos'})
    M2_ = F[~F.companion & F.route_id.isin(MAIN)]
    g9 = M2_.groupby(['route_id', 'H'])[['post', 'hp_prodH5', 'hp_R1H5', 'hp_R2H5']].median().reset_index()
    cmp_frame('C15', 'T9_vs_H5_post', g9, rd(os.path.join(RD, TAB2, 'T9_vs_H5_post.csv')), ['route_id', 'H'],
              ['post', 'hp_prodH5', 'hp_R1H5', 'hp_R2H5'], inputs=os.path.join(TAB2, 'T9_vs_H5_post.csv'))


def stage_C10(F, rc):
    P1B = os.path.join(RD, 'reports', 'E6i_REPORT_part1b.md')
    der = pd.concat([rd(f) for s in DER for f in glob.glob(os.path.join(RD, 'm2', s, 'ledger_*.csv')) if '_timing' not in f],
                    ignore_index=True)
    act = der.groupby(['segment', 'variant', 'action']).size().unstack(fill_value=0).reset_index()
    cmp_printed_table('C10', 'part1b §3 程序动作计数表', act, P1B, ['segment', 'variant'],
                      {c: c for c in act.columns if c not in ('segment', 'variant')})
    lm = der[der.action == 'modified'].groupby(['segment', 'variant', 'lam']).size().unstack(fill_value=0)
    lm.columns = [str(c) for c in lm.columns]
    cmp_printed_table('C10', 'part1b §3 λ 计数表', lm.reset_index(), P1B, ['segment', 'variant'], {c: c for c in lm.columns})
    for s in SEGS:
        fs = [f for f in glob.glob(os.path.join(RD, 'm2', s, 'ledger_*.csv')) if '_timing' not in f]
        L = pd.concat([rd(f) for f in fs], ignore_index=True)
        pr = L[L.variant == 'primary']
        zs = float((pr.action == 'zero_modification').mean())
        e = {'2010-2014': '13%', '2015-2018': '53%', '2019-2023': '46%', '2024-2026': '77%'}[s]
        v_printed('C10', '%s primary 零修改占比〔P1B-ZERO / P2-M2ZERO〕' % s, e, zs, func='m2 ledger', inputs=fs[0])
        if s in DER:
            v_exact('C10', '%s primary (程序 x 年) = modified + zero' % s, {'2010-2014': 1392, '2015-2018': 1856}[s],
                    int(pr.action.isin(['modified', 'zero_modification']).sum()), func='m2 ledger',
                    note='其它 action：%s' % pr.action.value_counts().to_dict())
            lam = pr[pr.action == 'modified'].lam.value_counts().sort_index()
            e_l = {'2010-2014': (81, 1002, 125), '2015-2018': (308, 211, 346)}[s]
            v_exact('C10', '%s primary modified 的 λ 计数（0.1 / 1 / 10）' % s, e_l, tuple(int(lam.get(k, 0)) for k in (0.1, 1.0, 10.0)),
                    func='m2 ledger')
    m2p = rd(os.path.join(RD, TAB1, 'M2_panel.csv'))
    ids = m2p.descriptor_id
    mm = rc['full'].reindex(ids).reset_index()
    mm['d1'] = ids.map(rc['2010-2014'].d_net8_ann).values
    mm['d2'] = ids.map(rc['2015-2018'].d_net8_ann).values
    numc = ['n_days', 'd_net8_ann', 'se_nwH', 'se_boot20', 'se_boot60', 'band_domain_lo', 'band_domain_hi', 'band_axis_lo',
            'band_axis_hi', 'band_headline_lo', 'band_headline_hi', 'ci_lo_nwH', 'ci_hi_nwH', 'discernible_scale', 'mde80', 'd1', 'd2']
    cmp_frame('C10', 'M2_panel 统计列（M2 全部变体 %d 个）' % len(m2p), mm, m2p, ['descriptor_id'], numc, inputs=os.path.join(TAB1, 'M2_panel.csv'))
    v_exact('C10', 'M2_panel ci_excludes_zero / state_word 不符个数', (0, 0),
            (int((mm.ci_excludes_zero.astype(bool).values != m2p.ci_excludes_zero.astype(bool).values).sum()),
             int((mm.state_word.astype(str).values != m2p.state_word.astype(str).values).sum())), func='cmp')
    pr = m2p[m2p.variant == 'primary'].copy()
    v_exact('C10', 'M2 primary 程序数〔P1B-ALL〕', 464, len(pr), func='M2_panel')
    Fi = F.set_index('descriptor_id')
    pr['d1r'], pr['d2r'] = pr.descriptor_id.map(Fi.d1), pr.descriptor_id.map(Fi.d2)
    pr['fr'], pr['cir'] = pr.descriptor_id.map(Fi.deriv), pr.descriptor_id.map(Fi.ci_deriv)
    v_printed('C10', 'M2 primary 2010-14 中位', '-0.011', pr.d1r.median(), func='median')
    v_printed('C10', 'M2 primary 2015-18 中位', '+0.000', pr.d2r.median(), func='median')
    ci = pr.cir.astype(bool)
    v_exact('C10', 'M2 primary NW 排除 0 正 / 负', (32, 16), (int((ci & (pr.fr > 0)).sum()), int((ci & (pr.fr < 0)).sum())), func='count')
    m2m0 = pr.fr - pr.m0_same_budget_full
    v_printed('C10', 'M2 − 同预算 M0 full 中位〔P1B-M0〕', '+0.010', m2m0.median(), func='median', note='M0 值取 M2_panel 表列')
    v_printed('C10', 'M2 − M0 > 0 占比', '47%', float((m2m0 > 0).mean()), func='mean')
    v_exact('C10', 'M2 − M0 可配对数', 412, int(m2m0.notna().sum()), func='count')
    bp = glob.glob(os.path.join(RD, 'm2', '*', 'boot_[0-9][0-9].csv'))
    bt = pd.concat([rd(p) for p in bp], ignore_index=True)
    bt = bt[bt.b >= 0]
    bq = bt.groupby(['segment', 'program']).d_net8_outer.agg(['size', 'median', lambda x: x.quantile(.05),
                                                              lambda x: x.quantile(.95)]).reset_index()
    bq.columns = ['segment', 'program', 'n_boot', 'median', 'q05', 'q95']
    cmp_frame('C10', 'M2_boot_quantiles', bq, rd(os.path.join(RD, TAB1, 'M2_boot_quantiles.csv')), ['segment', 'program'],
              ['median', 'q05', 'q95'], ['n_boot'], inputs=os.path.join(TAB1, 'M2_boot_quantiles.csv'))
    sq = bq.groupby('segment')[['median', 'q05', 'q95']].median()
    for s, es in (('2010-2014', ('-0.022', '-0.119', '0.080')), ('2015-2018', ('0.000', '-0.130', '0.112'))):
        for c, e in zip(('median', 'q05', 'q95'), es):
            v_printed('C10', '学习不确定性 %s %s 中位' % (s, c), e, sq.loc[s, c], func='median')


def stage_C11():
    cs = os.path.join(RD, 'carried', 'summary')
    st = rd(os.path.join(cs, 'C1_strict_rows.csv'))
    ok = st[(st.common_days >= 60) & st.d.notna()]
    cell = ok.groupby(['segment', 'mother', 'q', 'scope', 'alloc', 'contrast', 'fixed']).agg(
        mean=('d', 'mean'), sd=('d', 'std'), share_pos=('d', lambda x: (x > 0).mean()), n_seed=('d', 'size'),
        common_days=('common_days', 'mean')).reset_index()
    cmp_frame('C11', 'C1_T3_contrasts_min60', cell, rd(os.path.join(cs, 'C1_T3_contrasts_min60.csv')),
              ['segment', 'mother', 'q', 'scope', 'alloc', 'contrast', 'fixed'], ['mean', 'sd', 'share_pos', 'common_days'], ['n_seed'],
              inputs='carried/summary/C1_T3_contrasts_min60.csv')
    main_ = cell[(cell.scope == 'frozen') & (cell.alloc == 'equal')]
    g = main_.groupby(['segment', 'contrast', 'fixed']).agg(n_cells=('mean', 'size'), mean_of_means=('mean', 'mean'),
                                                            cells_pos=('mean', lambda x: int((x > 0).sum())),
                                                            seeds=('n_seed', 'sum'), common_days=('common_days', 'mean')).reset_index()
    v_exact('C11', '严格交叉主表行数', 11, len(g), func='groupby')
    gi = g.set_index(['segment', 'contrast', 'fixed'])
    for key, es in ((('2019-2023', 'N250−N100', 'B=16'), ('4.866', 12, 708, '231.559')),
                    (('2024-2026', 'B16−B8', 'N=150'), ('-0.666', 0, 540, '300.156'))):
        r_ = gi.loc[key]
        v_printed('C11', '%s mean_of_means' % '/'.join(key), es[0], r_.mean_of_means, func='groupby')
        v_exact('C11', '%s cells_pos' % '/'.join(key), es[1], int(r_.cells_pos), func='groupby')
        v_exact('C11', '%s seeds' % '/'.join(key), es[2], int(r_.seeds), func='groupby')
        v_printed('C11', '%s common_days' % '/'.join(key), es[3], r_.common_days, func='groupby')
    cmp_printed_table('C11', 'part3 §2 严格交叉主表', g, os.path.join(RD, 'reports', 'E6i_REPORT_part3.md'),
                      ['segment', 'contrast', 'fixed'], {'n_cells': 'n_cells', 'mean_of_means': 'mean_of_means', 'cells_pos': 'cells_pos',
                                                         'seeds': 'seeds', 'common_days': 'common_days'})
    t2 = st.groupby(['segment', 'contrast', 'fixed', 'alloc', 'scope']).agg(
        n=('d', 'size'), n_feasible=('d', lambda x: int(x.notna().sum())), common_days_mean=('common_days', 'mean'),
        common_days_min=('common_days', 'min')).reset_index()
    cmp_frame('C11', 'C1_T2_strict', t2, rd(os.path.join(cs, 'C1_T2_strict.csv')), ['segment', 'contrast', 'fixed', 'alloc', 'scope'],
              ['common_days_mean', 'common_days_min'], ['n', 'n_feasible'], inputs='carried/summary/C1_T2_strict.csv')
    fz = t2[(t2.scope == 'frozen') & (t2.alloc == 'equal')]
    v_exact('C11', 'Q10-SUPPORT 行数（frozen x equal 的 (段, 对比, 固定维)）', 24, len(fz), func='filter')
    txt = '各 (段, 对比, 固定维) 的共同可行日均值：' + '；'.join('%s %s %s %.0f 天' % (r_.segment, r_.contrast, r_.fixed, r_.common_days_mean)
                                                         for r_ in fz.itertuples())
    qt = rd(os.path.join(RD, TAB3, 'query_ids_part3.csv')).set_index('query_id').text
    v_exact('C11', 'Q10-SUPPORT 现算全文 = query_ids_part3 存档全文', True, txt == qt.get('Q10-SUPPORT'),
            inputs=os.path.join(TAB3, 'query_ids_part3.csv'), func='format')
    for ctr in ('B16−B8', 'N250−N100'):
        sp = main_[main_.contrast == ctr].groupby('segment')['mean'].apply(lambda s: (s > 0).mean())
        for s_, v_ in sp.items():
            e = {('B16−B8', '2015-2018'): '50%', ('B16−B8', '2019-2023'): '88%', ('B16−B8', '2024-2026'): '22%',
                 ('N250−N100', '2019-2023'): '100%', ('N250−N100', '2024-2026'): '100%'}.get((ctr, s_))
            if e:
                v_printed('C11', '%s %s 格均值>0 占比〔Q10-SIGN〕' % (ctr, s_), e, v_, func='mean')
    P = rd(os.path.join(cs, 'C1_T9_capital_pairs.csv'))
    cap = P.groupby(['segment', 'scope', 'alloc', 'contrast', 'fixed']).agg(
        n_pairs=('d_deploy', 'size'), d_strict=('d_strict', 'mean'), d_deploy=('d_deploy', 'mean'), cap_part=('cap_part', 'mean'),
        sel_part=('sel_part', 'mean'), pos_a=('pos_a', 'mean'), pos_b=('pos_b', 'mean'), held_a=('held_a', 'mean'),
        held_b=('held_b', 'mean'), e_a=('e_a', 'median'), e_b=('e_b', 'median')).reset_index()
    cap['cap_share'] = cap.cap_part / cap.d_deploy
    cmp_frame('C11', 'C1_T9_capital', cap, rd(os.path.join(cs, 'C1_T9_capital.csv')), ['segment', 'scope', 'alloc', 'contrast', 'fixed'],
              ['d_strict', 'd_deploy', 'cap_part', 'sel_part', 'pos_a', 'pos_b', 'held_a', 'held_b', 'e_a', 'e_b', 'cap_share'],
              ['n_pairs'], inputs='carried/summary/C1_T9_capital.csv')
    ci_ = cap.set_index(['segment', 'scope', 'alloc', 'contrast', 'fixed'])
    v_printed('C11', 'cap_share 2019-23 N250−N100 B=16 frozen/equal', '0.585',
              ci_.loc[('2019-2023', 'frozen', 'equal', 'N250−N100', 'B=16'), 'cap_share'], func='ratio')
    v_printed('C11', 'cap_share 2024-26 N250−N100 B=16 frozen/equal', '0.677',
              ci_.loc[('2024-2026', 'frozen', 'equal', 'N250−N100', 'B=16'), 'cap_share'], func='ratio')
    pn = P[P.contrast == 'N250−N100'].groupby('segment')[['d_deploy', 'cap_part']].mean()
    for s_, e in (('2019-2023', '66%'), ('2024-2026', '81%')):
        v_printed('C11', 'Q10-CAP 全部口径合并 资金部分 %s' % s_, e, pn.loc[s_, 'cap_part'] / pn.loc[s_, 'd_deploy'], func='ratio')
    # 配对的底数：逐 seed 行（部署视图）→ 重建配对，与 pairs 表逐值比
    rows = []
    for s in SEGS:
        if s in POST:
            fs = [f for f in sorted(glob.glob(os.path.join(RD, 'sealed', s, 'c1_*.csv')))
                  if '_feasible' not in f and '_63-63' not in f and not f.endswith('.receipt.json')]
        else:
            fs = [f for f in sorted(glob.glob(os.path.join(RD, 'carried', 'C1', s, 'c1_*.csv'))) if '_feasible' not in f and '_63-63' not in f]
        if fs:
            rows.append(pd.concat([rd(f) for f in fs], ignore_index=True).assign(segment=s))
    R_ = pd.concat(rows, ignore_index=True)
    cr = R_[R_.part == 'cross']
    pairs = [('B16−B8', 'N=%d' % n, (n, 8), (n, 16)) for n in (100, 150, 250)] + \
            [('N250−N100', 'B=%d' % b, (100, b), (250, b)) for b in (8, 12, 16)]
    out = []
    for (s, seed, alloc, mn, qq, sc), g_ in cr.groupby(['segment', 'seed', 'alloc', 'mother', 'q', 'scope']):
        cell_ = {(int(r_.N), int(r_.B)): r_ for r_ in g_.itertuples()}
        for ctr, fixed, ca, cb in pairs:
            if ca in cell_ and cb in cell_ and cell_[ca].pos_mean > 0 and cell_[cb].pos_mean > 0:
                a, b = cell_[ca], cell_[cb]
                ea, eb = a.net8_ann / a.pos_mean, b.net8_ann / b.pos_mean
                out.append(dict(segment=s, mother=mn, q=qq, scope=sc, alloc=alloc, seed=seed, contrast=ctr, fixed=fixed,
                                d_deploy=b.net8_ann - a.net8_ann, cap_part=(b.pos_mean - a.pos_mean) * ea,
                                sel_part=b.pos_mean * (eb - ea)))
    O = pd.DataFrame(out)
    k = ['segment', 'mother', 'q', 'scope', 'alloc', 'seed', 'contrast', 'fixed']
    J = P.merge(O, on=k, suffixes=('', '_rc'))
    J[k + ['d_deploy_rc', 'cap_part_rc', 'sel_part_rc']].rename(columns=lambda c: c.replace('_rc', '')).to_csv(
        os.path.join(WORK, 'c1_pairs_rc.csv'), index=False)
    v_exact('C11', '资本配对：pairs 表 %d 个全部可由逐 seed 行重建' % len(P), len(P), len(J), func='per-seed rows')
    for c in ('d_deploy', 'cap_part', 'sel_part'):
        v_close('C11', '资本配对 %s（pairs 表 vs 逐 seed 行重建）max|d|' % c, 0.0, float(np.max(np.abs(J[c] - J[c + '_rc']))), 1e-12,
                func='per-seed rows')
    b4 = rd(os.path.join(cs, 'C1_T4_bridges.csv'))
    b4['N'] = b4['N'].astype('Int64')
    bb = b4[b4.scope.isin(['frozen', 'source'])].groupby(['segment', 'part', 'N'], dropna=False).net8_mean.median().unstack('part').reset_index()
    bb['N'] = bb['N'].astype(str)
    v_exact('C11', 'part3 §2 桥表行数', 16, len(bb), func='groupby')
    cmp_printed_table('C11', 'part3 §2 桥表', bb, os.path.join(RD, 'reports', 'E6i_REPORT_part3.md'), ['segment', 'N'],
                      {c: c for c in ('bridge_full', 'bridge_randomN', 'bridge_topN', 'mother_source') if c in bb.columns})
    t5 = rd(os.path.join(cs, 'C1_T5_instrument.csv'))
    for s_, e in zip(SEGS, ('-0.001', '-0.054', '-0.026', '-0.013')):
        v_printed('C11', '仪器效应 %s 中位〔Q10-INSTR〕' % s_, e, t5[t5.segment == s_]['mean'].median(), func='median')


def stage_C12(rc):
    cs = os.path.join(RD, 'carried', 'summary')
    K_ = rd(os.path.join(cs, 'C2_children_delta.csv'))
    cols = [c for c in K_.columns if c.startswith('net8_minus_sqrt_')]
    res_n = float(np.nanmax(np.abs(K_.d_net8_ann - (K_.net8_ann - K_.m_net8_ann))))
    res_i = max(float(np.nanmax(np.abs(K_['d_' + c] - (K_[c] - K_['m_' + c])))) for c in cols)
    v_close('C12', '恒等：d_net8 = 子 net8 − 母 net8（逐描述符）max 残差', 0.0, res_n, 1e-12, inputs='carried/summary/C2_children_delta.csv',
            func='identity')
    v_close('C12', '恒等：d_(net8 − 冲击) = 子 − 母（9 个情景列）max 残差', 0.0, res_i, 1e-12, func='identity')
    # 源模型 MI = κ·sqrt(A)·bracket：逐描述符 冲击 c(A, κ) = net8 − net8_minus_sqrt(A, κ) 应等于 κ·sqrt(A)·c(1, 1)
    c11 = K_.net8_ann - K_['net8_minus_sqrt_A1_k1']
    worst = 0.0
    for A in (1, 5, 10):
        for kp in ('0.25', '0.5', '1'):
            c = K_.net8_ann - K_['net8_minus_sqrt_A%d_k%s' % (A, kp)]
            worst = max(worst, float(np.nanmax(np.abs(c - float(kp) * np.sqrt(A) * c11))))
    v_close('C12', '恒等：冲击 c(A, κ) = κ·√A·c(1, 1)（逐描述符 x 9 情景）max 残差', 0.0, worst, 1e-12, func='identity',
            note='源模型 FORMS[sqrt] = κ·sqrt(A·YI)·bracket（e6g_c.py:152），读源码确认形式，不 import')
    ok_all, rs_all = [], []
    for s in SEGS:
        x = K_[K_.segment == s].set_index('descriptor_id')
        d = (x.d_net8_ann - rc[s].d_net8_ann.reindex(x.index)).abs()
        dm = (x.m_net8_ann - (x.net8_ann - x.d_net8_ann)).abs()
        rnd = x.index.str.contains('state=random_state', regex=False)
        ok_all.append(float(d[~rnd].max()))
        rs_all.append((s, int(rnd.sum()), int((d[rnd] > 1e-12).sum()), round(float(d[rnd].max()), 3)))
    v_close('C12', 'C2 表 d_net8_ann vs 账本重算的分段 d_net8_ann（两条链；random_state 焦点臂以外全部子描述符）max|d|', 0.0, max(ok_all),
            1e-12, func='cross-chain')
    nb = sum(r_[2] for r_ in rs_all)
    rec('C12', 'C2 表 d_net8_ann vs 账本重算（state=random_state 焦点臂）|d|>1e-12 的描述符数（四段合计）', 0, nb,
        'DIFFERS' if nb else 'REPRODUCED', tol='|d|<=1e-12', func='cross-chain',
        note='逐段 (random_state 臂数, |d|>1e-12 个数, max|d|)：%s；这些行的母体列 m_net8_ann 与母体账户一致、差全在子账户 net8；'
             'e6i_stage2.py:152 以 np.random.default_rng(abs(hash(descriptor_id)) %% 2**32) 取 random_state 臂的随机状态，'
             '项目脚本、runtime 目录与 47 登录环境均未设 PYTHONHASHSEED' % rs_all)
    grp = ['segment', 'route_id', 'mother_id', 'H']
    cols6 = ['d_net8_ann'] + ['d_' + c for c in cols]
    T6p = os.path.join(RD, 'carried', 'summary', 'C2_T6_impact_delta.csv')
    T6 = rd(T6p)
    t6r = K_.groupby(grp)[cols6].median().reset_index()
    t6r['n'] = K_.groupby(grp).size().values
    cmp_frame('C12', 'C2_T6_impact_delta（由 C2_children_delta 重新汇总）', t6r, T6, grp, cols6, ['n'], inputs='carried/summary/C2_T6_impact_delta.csv')
    kid = K_[grp + ['descriptor_id']].copy()
    kid['dn'] = [rc[s_].d_net8_ann.get(d_, np.nan) for s_, d_ in zip(kid.segment, kid.descriptor_id)]
    t6l = kid.groupby(grp).dn.median().reset_index()
    j = t6l.merge(T6[grp + ['d_net8_ann']], on=grp)
    dd = (j.dn - j.d_net8_ann).abs()
    rec('C12', 'C2_T6 的 d_net8_ann 格（子取账本重算值）vs 表：|d|>1e-12 的格数（共 %d 格）' % len(j), 0, int((dd > 1e-12).sum()),
        'DIFFERS' if (dd > 1e-12).any() else 'REPRODUCED', tol='|d|<=1e-12', func='median',
        note='涉及 (段, 路线)：%s；max|d| %.3g' % (sorted(set(zip(j[dd > 1e-12].segment, j[dd > 1e-12].route_id))), float(dd.max())))
    P3R = os.path.join(RD, 'reports', 'E6i_REPORT_part3.md')
    c5s = [c for c in cols6 if c.startswith('d_net8_minus_sqrt_A5')]
    gt = T6.groupby(['segment', 'route_id'])[['d_net8_ann'] + c5s].median().reset_index()
    cmp_printed_table('C12', 'part3 §3 第一表（由 C2_T6 表汇总，表层）', gt, P3R, ['segment', 'route_id'], {c: c for c in ['d_net8_ann'] + c5s})
    gl = t6l.groupby(['segment', 'route_id']).dn.median().reset_index().rename(columns={'dn': 'd_net8_ann'})
    cmp_printed_table('C12', 'part3 §3 第一表 d_net8_ann 列（子取账本重算值）', gl, P3R, ['segment', 'route_id'], {'d_net8_ann': 'd_net8_ann'})
    k = K_[(K_.route_id == 'RK') & K_.direction_role.isin(PRIM) & (K_.policy == 'FALLBACK')]
    c10 = 'd_net8_minus_sqrt_A10_k1'
    c5 = 'd_net8_minus_sqrt_A5_k0.5'
    kh = k.groupby(['segment', 'H'])[['d_net8_ann', c10]].median().unstack('segment')
    kh.columns = ['%s %s' % (a_.replace(c10, 'A10κ1').replace('d_net8_ann', '无冲击'), b_) for a_, b_ in kh.columns]
    kh = kh.reset_index()
    cmp_frame('C12', 'C2_K_by_H', kh, rd(os.path.join(RD, TAB3, 'C2_K_by_H.csv')), ['H'], [c for c in kh.columns if c != 'H'],
              inputs=os.path.join(TAB3, 'C2_K_by_H.csv'))
    kx = kh.set_index('H')
    for s, e0, e1 in zip(SEGS, ('0.133', '0.202', '0.042', '0.008'), ('0.125', '0.195', '0.037', '0.012')):
        v_printed('C12', 'K H20 %s 无冲击' % s, e0, kx.loc[20, '无冲击 %s' % s], func='median')
        v_printed('C12', 'K H20 %s A10κ1' % s, e1, kx.loc[20, 'A10κ1 %s' % s], func='median')
    kk = k.groupby('segment')[['d_net8_ann', c5, c10]].median()
    for c, e in (('d_net8_ann', '+0.099'), (c5, '+0.167'), (c10, '+0.213')):
        v_printed('C12', 'Q7-KIMPACT 2019-2023 %s' % c, e, kk.loc['2019-2023', c], func='median')
    short = k[k.H <= 3].groupby('segment')[c10].median()
    long_ = k[k.H >= 10].groupby('segment')[[c10, 'd_net8_ann']].median()
    mo = K_[['segment', 'mother_id', 'H', 'm_net8_minus_sqrt_A10_k1']].drop_duplicates()
    mshort = mo[mo.H <= 3].groupby('segment').m_net8_minus_sqrt_A10_k1.median()
    for s, a_, b_, c_, d_ in zip(SEGS, ('+0.762', '+1.482', '+1.058', '+0.701'), ('-31.5', '-38.3', '-48.4', '-49.3'),
                                 ('+0.155', '+0.235', '+0.070', '-0.013'), ('+0.170', '+0.247', '+0.057', '-0.024')):
        v_printed('C12', 'Q7-KH %s 短 H 增量' % s, a_, short.loc[s], func='median')
        v_printed('C12', 'Q7-KH %s 母体短 H 净值' % s, b_, mshort.loc[s], func='median')
        v_printed('C12', 'Q7-KH %s 长 H A10κ1' % s, c_, long_.loc[s, c10], func='median')
        v_printed('C12', 'Q7-KH %s 长 H 无冲击' % s, d_, long_.loc[s, 'd_net8_ann'], func='median')
    rl = K_[K_.route_id == 'RL'].groupby('segment')[['d_net8_ann', c5, c10]].median()
    exp_rl = {'2010-2014': ('-0.293', '-0.073', '+0.155'), '2015-2018': ('-0.467', '-0.164', '+0.195'),
              '2019-2023': ('-0.314', '-0.075', '+0.155'), '2024-2026': ('-0.162', '-0.141', '-0.081')}
    for s, es in exp_rl.items():
        for c, e in zip(('d_net8_ann', c5, c10), es):
            v_printed('C12', 'Q7-RL %s %s' % (s, c), e, rl.loc[s, c], func='median')


def stage_C13():
    p = lambda f: os.path.join(RD, TABR0, f)
    fa = rd(p('first_table.csv'))
    cr = fa[fa.quantity == 'cr5_source_unadjusted_simple'].set_index('segment')
    lt = fa[fa.quantity == 'limit_touch_days_last5'].set_index('segment')
    for s, e_med, e_pos, e_n in (('2010-2014', '-0.42%', '46.0%', 185737), ('2015-2018', '-0.41%', '45.2%', 246405)):
        v_printed('C13', 'W01 %s cr5 中位' % s, e_med, cr.loc[s, 'p50'], func='first_table', inputs=p('first_table.csv'))
        v_printed('C13', 'W01 %s 正值占比' % s, e_pos, cr.loc[s, 'frac_pos'], func='first_table')
        v_exact('C13', 'W01 %s n' % s, e_n, int(cr.loc[s, 'n']), func='first_table')
    for s, e in (('2010-2014', '9.0%'), ('2015-2018', '14.1%')):
        v_printed('C13', 'TOUCH %s' % s, e, lt.loc[s, 'frac_pos'], func='first_table')
    rec('C13', '首表从 measurements/ 原值重算分位', '原值分位', None, 'NOT_COMPUTABLE', func='-',
        note='measurements/ 只有诊断汇总（diag_* / cost_exposure_*），逐格原值只在 cache/（不在允许输入）；首表只在表层复核')
    v_exact('C13', '首表行数', 18, len(fa), func='len')
    pdg = rd(p('prediction_all_members_src5.csv'))
    mm = pdg.groupby(['segment', 'setn', 'axis', 'member_id']).ic_mean.mean().reset_index()
    fr = mm.pivot_table(index=['segment', 'member_id'], columns='setn', values='ic_mean')
    fr = fr[np.isfinite(fr.econ_reject) & (fr.econ_reject.abs() > 0.02)]
    ratio = (fr.final.abs() / fr.econ_reject.abs()).groupby('segment').median()
    nfr = fr.groupby('segment').size()
    for s, e, n_ in (('2010-2014', '0.43', 189), ('2015-2018', '0.59', 194)):
        v_printed('C13', 'FINAL %s |IC| 比中位' % s, e, ratio.loc[s], func='prediction', inputs=p('prediction_all_members_src5.csv'))
        v_exact('C13', 'FINAL %s 成员数' % s, n_, int(nfr.loc[s]), func='prediction')
    piv = mm.groupby(['segment', 'setn', 'axis']).ic_mean.median().reset_index()
    pv = rd(p('prediction_axis_set_pivot.csv'), header=[0, 1])        # 两级表头（段, 集合）
    pv = pv.set_index(pv.columns[0])
    v_exact('C13', '预测层轴 x 集合表 行 x 列', (8, 8), pv.shape, func='len')
    piv = piv[piv.setn.isin(['pool0', 'final', 'edge', 'econ_reject'])]
    diffs = [abs(float(pv.loc[r_.axis, (r_.segment, r_.setn)]) - float(r_.ic_mean)) for r_ in piv.itertuples()
             if r_.axis in pv.index and (r_.segment, r_.setn) in pv.columns]
    v_exact('C13', '预测层轴 x 集合表可对上的格数', int(pv.size), len(diffs), func='pivot')
    v_close('C13', '预测层轴 x 集合表 max|d|（%d 格）' % len(diffs), 0.0, max(diffs) if diffs else np.nan, 1e-12, func='pivot')
    dl = rd(p('decision_layer_all.csv'))
    dpos = dl[dl.swap_in_minus_out_mean > 0]
    v_exact('C13', 'DPOS 换入 − 换出为正 / 总', (434, 4416), (len(dpos), len(dl)), func='decision', inputs=p('decision_layer_all.csv'))
    both = dpos.groupby(['member_id', 'side', 'mother']).segment.nunique()
    v_exact('C13', 'DPOS2 两段都为正', 92, int((both == 2).sum()), func='decision')
    ax_side = dpos.groupby(['side', 'axis']).size().sort_values(ascending=False)
    v_exact('C13', 'DPOS3 前两名 (端, 轴)', [('member_low_in', 'T', 117), ('member_low_in', 'K', 89)],
            [(a, b, int(n)) for (a, b), n in ax_side.head(2).items()], func='decision')
    t0p = rd(p('T0_portrait_all.csv'))
    t0a = t0p[t0p.stratum == 'all'].copy()
    t0a['z'] = (t0a.pct_diff_winner_minus_loser - t0a.perm_mean) / t0a.perm_sd
    t0m = t0a.groupby(['segment', 'member_id']).agg(diff=('pct_diff_winner_minus_loser', 'mean'), z=('z', 'mean')).reset_index()
    for s, e in (('2010-2014', (276, 142, 30)), ('2015-2018', (276, 178, 24))):
        x = t0m[t0m.segment == s]
        v_exact('C13', 'T0Z %s 成员 / z<−3 / z>3' % s, e, (len(x), int((x.z < -3).sum()), int((x.z > 3).sum())), func='T0 portrait',
                inputs=p('T0_portrait_all.csv'))
    cmpd = rd(p('T0_reject_vs_references.csv'))
    sg = cmpd[cmpd.z.abs() > 3]
    for s, e in (('2010-2014', (172, 172, 148, '0.98')), ('2015-2018', (202, 202, 197, '0.91'))):
        x = sg[sg.segment == s]
        v_exact('C13', 'T0SPEC %s |z|>3 / 同人数同号 / 保留集同号' % s, e[:3],
                (len(x), int((np.sign(x.d_reject) == np.sign(x.d_p0_sameN)).sum()), int((np.sign(x.d_reject) == np.sign(x.d_final)).sum())),
                func='T0 references', inputs=p('T0_reject_vs_references.csv'))
        v_printed('C13', 'T0SPEC %s 差之比中位' % s, e[3], (x.d_reject / x.d_p0_sameN).median(), func='median')
    t0mm = t0m.set_index(['segment', 'member_id'])
    cm = cmpd.set_index(['segment', 'member_id'])
    com = cm.index.intersection(t0mm.index)
    v_close('C13', 'T0 references 的 z / d_reject 与画像重算一致 max|d|', 0.0,
            float(max(np.nanmax(np.abs(cm.loc[com, 'z'] - t0mm.loc[com, 'z'])), np.nanmax(np.abs(cm.loc[com, 'd_reject'] - t0mm.loc[com, 'diff'])))),
            1e-12, func='T0 portrait')
    sh = pdg.copy()
    gcols = ['g5_1', 'g5_2', 'g5_3', 'g5_4', 'g5_5']
    sh['g_range'] = sh[gcols].max(1) - sh[gcols].min(1)
    sh['shape_flag'] = (sh.ic_mean.abs() < 0.01) & (sh.u_shape_index.abs() > 0.5 * sh.g_range) & (sh.g_range > 5)
    q17c = sh.groupby(['segment', 'setn', 'axis']).agg(n=('member_id', 'size'), k=('shape_flag', 'sum')).reset_index()
    cmp_frame('C13', 'Q17_shape_counts', q17c, rd(p('Q17_shape_counts.csv')), ['segment', 'setn', 'axis'], [], ['n', 'k'],
              inputs=p('Q17_shape_counts.csv'))
    tot = q17c.groupby('segment')[['k', 'n']].sum()
    for s, e in (('2010-2014', (683, 5796)), ('2015-2018', (561, 5796))):
        v_exact('C13', 'Q17A %s 标出 / 总' % s, e, (int(tot.loc[s, 'k']), int(tot.loc[s, 'n'])), func='shape')
    qm = rd(p('Q17_shape_members.csv'))
    qb = qm.groupby(['member_id', 'setn', 'mother']).segment.nunique()
    v_exact('C13', 'Q17B 两段都标出', 139, int((qb == 2).sum()), func='shape', inputs=p('Q17_shape_members.csv'))
    cost = rd(p('cost_exposure.csv'))
    ce = cost.groupby(['segment', 'member_id', 'set']).day_mean_of_means.mean().unstack('set')
    ce = ce.assign(r=ce.edge / ce.final)
    for s, e in (('2010-2014', (3, 9)), ('2015-2018', (8, 9))):
        x = ce.loc[s]
        v_exact('C13', 'COST %s edge 高于 final / 摩擦成员' % s, e, (int((x.r > 1).sum()), int(x.r.notna().sum())), func='cost',
                inputs=p('cost_exposure.csv'))


def stage_C17():
    sw = sorted(f for f in glob.glob(os.path.join(RD, 'statistics', 'swap_in_out_*_[0-9][0-9].csv'))
                if os.path.basename(f)[12:21] in DER)          # part1 生成时只有推导两段的文件
    S_ = pd.concat([rd(f).assign(seg=os.path.basename(f)[12:21]) for f in sw], ignore_index=True)
    S_ = S_[S_.get('status').isna()] if 'status' in S_ else S_
    S_['out_rule'] = np.where(S_.policy.astype(str).str.contains('max_K'), 'max_K', 'mother_worst')
    g = S_.groupby(['seg', 'route_id', 'direction_role', 'out_rule']).agg(
        n=('descriptor_id', 'size'), in_mean=('in_mean', 'median'), out_mean=('out_mean', 'median'),
        in_pneg=('in_p_neg', 'median'), out_pneg=('out_p_neg', 'median'), in_p10=('in_p10', 'median'),
        out_p10=('out_p10', 'median'), in_p90=('in_p90', 'median'), out_p90=('out_p90', 'median'),
        in_minus_out=('in_minus_out_daymean', 'median')).reset_index()
    v_exact('C17', '5b 表行数', 14, len(g), func='groupby', inputs=sw[0])
    x = g[(g.seg == '2010-2014') & (g.route_id == 'RR') & g.direction_role.str.contains('contin')]
    if len(x):
        x = x.iloc[0]
        for c, e in (('in_mean', '-40.568'), ('out_mean', '16.831'), ('in_minus_out', '-52.817')):
            v_printed('C17', '2010-2014 RR continuation %s（brief 例）' % c, e, x[c], func='median')
    cmp_printed_table('C17', 'part1 §5b 表', g, os.path.join(RD, 'reports', 'E6i_REPORT_part1.md'),
                      ['seg', 'route_id', 'direction_role', 'out_rule'],
                      {c: c for c in ('n', 'in_mean', 'out_mean', 'in_pneg', 'out_pneg', 'in_p10', 'out_p10', 'in_p90', 'out_p90', 'in_minus_out')})
    v_printed('C17', 'P1-SWAPDIST 中位 bp', '-26.7', S_.in_minus_out_daymean.median(), func='median')
    v_printed('C17', 'P1-SWAPDIST >0 占比', '17%', float((S_.in_minus_out_daymean > 0).mean()), func='mean')


# ============================================================ V-D 报告 ↔ 表
QFILES = {'query_ids_part1.csv': TAB1, 'query_ids_part1_text.csv': TAB1, 'query_ids_part1b.csv': TAB1,
          'query_ids_part2.csv': TAB2, 'query_ids_part3.csv': TAB3, 'query_ids.csv': TABR0}
REPORT_OF = {'query_ids_part1.csv': None,               # 问题卡事实句：写在 reports/part1_facts.md（不在五份 REPORT 正文）
             'query_ids_part1_text.csv': 'E6i_REPORT_part1.md', 'query_ids_part1b.csv': 'E6i_REPORT_part1b.md',
             'query_ids_part2.csv': 'E6i_REPORT_part2.md', 'query_ids_part3.csv': 'E6i_REPORT_part3.md',
             'query_ids.csv': 'E6i_REPORT_R0.md'}
MUST = ('P3-BASE', 'P3-BOTH', 'P3-FAM-K', 'P3-FAM-KR', 'P3-FAM-AH', 'P3-FAM-SLICE', 'P3-CARDS', 'P3-DELTA', 'P3-COV',
        'Q9-LOYO', 'Q9-STATE', 'Q9-VSDERIV', 'Q2P-READ', 'Q2P-MECH', 'P20-CORE', 'P21-Z')
HDR10 = ('汇总算子', '分母及构成', '基准', '子集', '单位', '日期支持', 'H', '成本', '支持口径', '资本口径')
NUMTOK = re.compile(r'[+\-−]?\d+(?:\.\d+)?%?')


def norm(s):
    return re.sub(r'\s+', ' ', str(s))


def f3(x, nd=3):                                    # 生成器 TX.f / facts.f3 同一格式
    return ('%+.' + str(nd) + 'f') % x if np.isfinite(x) else 'NA'


def pc(x):
    return '%.0f%%' % (100 * x) if np.isfinite(x) else 'NA'


def sgn_word(a, b, eps=0.05):
    if not (np.isfinite(a) and np.isfinite(b)):
        return '（缺）'
    if a > eps and b > eps:
        return '两段为正'
    if a < -eps and b < -eps:
        return '两段为负'
    if abs(a) <= eps and abs(b) <= eps:
        return '两段接近 0（|中位| ≤ %.2f）' % eps
    return '两段不同向或一段接近 0'


def load_qids():
    rows = []
    for fn, tab in QFILES.items():
        for r_ in rd(os.path.join(RD, tab, fn)).itertuples():
            rows.append(dict(file=fn, query_id=str(r_.query_id), text=str(r_.text)))
    return pd.DataFrame(rows)


def cmp_text(pid, qid, stored, built, src):
    """现算全文 vs 存档全文：逐字相同 → REPRODUCED；否则逐个数字 token 按印出位数比。"""
    if built is None:
        return
    s_, b_ = norm(stored), norm(built)
    if s_ == b_:
        rec(pid, '%s 全文逐字' % qid, s_, b_, 'REPRODUCED', tol='EXACT 字符串', inputs=src, func='rebuild')
        return
    ts, tb = NUMTOK.findall(s_), NUMTOK.findall(b_)
    nd, nr, bad = 0, 0, []
    if len(ts) != len(tb) or NUMTOK.sub('#', s_) != NUMTOK.sub('#', b_):
        rec(pid, '%s 全文（结构不同）' % qid, s_, b_, 'DIFFERS', tol='EXACT 字符串', inputs=src, func='rebuild',
            note='非数字部分不同或数字个数不同（存 %d / 算 %d）' % (len(ts), len(tb)))
        return
    for a, b in zip(ts, tb):
        if a == b:
            continue
        ea, pa = to_float(a)
        eb, _ = to_float(b)
        d = decimals(a)
        if abs(ea - eb) <= 10 ** (-d) + 1e-12:
            nr += 1
        else:
            nd += 1
            bad.append('%s→%s' % (a, b))
    v = 'DIFFERS' if nd else 'REPRODUCED|ROUNDING'
    rec(pid, '%s 全文（数字 token 逐个）' % qid, s_, b_, v, tol='印出位数', inputs=src, func='rebuild',
        note='末位差 1：%d 个；不符：%d 个 %s' % (nr, nd, '; '.join(bad[:8])))


def m1_table(P1, main_):
    m1 = P1[P1.route_id == 'M1'].copy()
    m1['variant'] = np.where(m1.descriptor_id.str.endswith('|eqcap'), 'eqcap_merge', 'consensus')
    parts_ = m1.descriptor_id.str.split('|')
    m1['m1_route'] = parts_.str[1]
    dr_map = main_.groupby(['route_id', 'member_id', 'direction']).direction_role.agg(lambda s: s.mode().iloc[0]).to_dict()

    def m1_role(rt_, mems_, dirn_):
        got = {dr_map.get((rt_, m_, dirn_)) for m_ in str(mems_).split('|')} - {None}
        return '|'.join(sorted(got)) if got else '?'
    m1['dir_role'] = [m1_role(a_, b_, c_) for a_, b_, c_ in zip(m1.m1_route, m1.member_id, m1.direction)]
    rows = []
    for key, x in m1.groupby(['m1_route', 'dir_role', 'direction', 'variant']):
        rows.append(dict(m1_route=key[0], dir_role=key[1], direction=key[2], variant=key[3], d1=x.d1.median(), d2=x.d2.median()))
    mb = pd.DataFrame(rows)
    return mb[mb.variant == 'consensus'].set_index(['m1_route', 'dir_role', 'direction'])


def facts_texts(P, Z, Qn, routes):
    """part1 事实块（问题卡通用句）同一公式；P = part1 面板口径（非伴随）。"""
    out = {}
    g = P[P.route_id.isin(routes)]
    n = len(g)
    ci = g['cix0_full'].astype(bool)
    d = g['d_full']
    out['%s-N' % Qn] = '描述符 %d 个（路线 %s）；full 子−母中位 %s、正值占比 %.1f%%；两段中位 %s / %s' % (
        n, '/'.join(routes), f3(d.median()), 100 * (d > 0).mean(), f3(g['d_10-14'].median()), f3(g['d_15-18'].median()))
    out['%s-CI' % Qn] = 'NW(lag H) 95%% 区间排除 0 且为正 %d 个、为负 %d 个（零增量下约 %.0f 个为随机，正负各半）' % (
        int((ci & (d > 0)).sum()), int((ci & (d < 0)).sum()), 0.05 * n)
    out['%s-BAND' % Qn] = 'need 域同步带（2,000 次 bootstrap，块 20）排除 0：为正 %d 个、为负 %d 个' % (
        int((g.bdlo_full > 0).sum()), int((g.bdhi_full < 0).sum()))
    sv = g['state_full'].value_counts()
    out['%s-STATE' % Qn] = '状态词（δ=0.25）：' + '；'.join('%s %d' % (k, int(v)) for k, v in sv.items())
    same = (np.sign(g['d_10-14']) == np.sign(g['d_15-18']))
    out['%s-SIGN' % Qn] = '两段同号 %.1f%%（同为正 %d、同为负 %d）' % (
        100 * same.mean(), int(((g['d_10-14'] > 0) & (g['d_15-18'] > 0)).sum()), int(((g['d_10-14'] < 0) & (g['d_15-18'] < 0)).sum()))
    for k in ('10-14', '15-18'):
        c = 'dcore_ann_%s' % k
        out['%s-SAMEN-%s' % (Qn, k)] = '%s 子−同人数核心 中位 %s、正值占比 %.1f%%；子−母 %s' % (
            k, f3(g[c].median()), 100 * (g[c] > 0).mean(), f3(g['d_%s' % k].median()))
        zz = Z[(Z.seg == k) & Z.route_id.isin(routes) & (Z.kind == 'basic')]
        if len(zz):
            out['%s-ZMAP-%s' % (Qn, k)] = '%s Z-MAP（basic）真实−随机均值 中位 %s、>0 占比 %.1f%%、tail<0.05 占比 %.1f%%（%d 行）' % (
                k, f3(zz.d_real_minus_rand.median()), 100 * (zz.d_real_minus_rand > 0).mean(),
                100 * (zz.diagnostic_tail_fraction < 0.05).mean(), len(zz))
    by_h = g.groupby('H').d_full.median()
    out['%s-H' % Qn] = '按 H（full 中位）：' + '；'.join('H%d %s' % (int(h), f3(v)) for h, v in by_h.items())
    return out


def fourarm_recompute():
    """四臂交互：逐日 Δ_AB − Δ_A − Δ_B（dnet8 取自日账本），分段 NW(lag H)、合并段间不拼接。缓存到 work/。"""
    p = os.path.join(WORK, 'fourarm_rc.csv')
    if os.path.exists(p):
        return rd(p)
    series = {}
    for s in SEGS:
        od = os.path.join(RD, 'accounts', s)
        meta = pd.concat([rd(f) for f in sorted(glob.glob(os.path.join(od, 'merged_*.csv'))) if not f.endswith('merged_index.csv')])
        meta = meta[(meta.status == 'SUCCEEDED') & (meta.route_id == 'FOURARM')]
        idx = rd(os.path.join(od, 'merged_index.csv')).set_index('descriptor_id')
        for r_ in meta.itertuples():
            f, row = idx.loc[r_.descriptor_id, 'npz'], int(idx.loc[r_.descriptor_id, 'row'])
            series[(s, r_.descriptor_id)] = (f, row, r_.policy, r_.mother_id, str(r_.strength), int(r_.H), str(r_.direction_role))
    cache = {}
    for (s, did), (f, row, *_rest) in series.items():
        cache.setdefault((s, f), []).append((did, row))
    X = {}
    for (s, f), lst in cache.items():
        with np.load(os.path.join(RD, 'accounts', s, f)) as z:
            for did, row in lst:
                assert z['descriptor_id'][row] == did
                X[(s, did)] = z['dnet8'][row].astype(float)
    groups = {}
    for (s, did), (f, row, pol, mo, pv, H, arm) in series.items():
        groups.setdefault((pol, mo, pv, H), {}).setdefault(s, {})[arm] = X[(s, did)]
    rows = []
    for (pol, mo, pv, H), segd in groups.items():
        per = {}
        for s, arms in segd.items():
            if not all(k in arms for k in ('A', 'B', 'AB')):
                continue
            inter = arms['AB'] - arms['A'] - arms['B']
            mu, se, n = nw(inter[:, None], H)
            per[s] = (inter, arms)
            rows.append(dict(fourarm=pol, mother=mo, param=pv, H=H, scope=s, interaction_ann=float(mu[0]) * ANN,
                             interaction_se_nwH=float(se[0]) * ANN,
                             **{'d_%s_ann' % k: float(np.nanmean(arms[k])) * ANN for k in ('A', 'B', 'AB')}))
        for sc, segs in (('full', DER), ('post', POST), ('all4', SEGS)):
            if all(s in per for s in segs):
                parts = [per[s][0][:, None] for s in segs]
                mu, se, n = merged(parts, np.array([H]))
                rows.append(dict(fourarm=pol, mother=mo, param=pv, H=H, scope=sc, interaction_ann=float(mu[0]) * ANN,
                                 interaction_se_nwH=float(se[0]) * ANN,
                                 **{'d_%s_ann' % k: float(np.nanmean(np.concatenate([per[s][1][k] for s in segs]))) * ANN
                                    for k in ('A', 'B', 'AB')}))
    out = pd.DataFrame(rows)
    out.to_csv(p, index=False)
    return out


def build_texts(F, rc):
    """必做 45 + 随机 18 条的现算句：公式照生成器，数值全部来自本程序的重算（面板 / 账本 / 母体重放）。"""
    T = {}
    TT = {}                       # 同 id 第二句（Q13-SIGN 在两个文件各一句）
    M = F[~F.companion & F.route_id.isin(MAIN)].copy()
    # ---- part1 口径框架（推导段）
    P1 = F.copy()
    P1['d_net8_ann'], P1['ci_excludes_zero'] = P1.deriv, P1.ci_deriv
    P1['band_domain_lo'], P1['band_domain_hi'] = P1.bdf_domain_lo, P1.bdf_domain_hi
    P1['d_vs_core_matchN_1'], P1['d_vs_core_matchN_2'] = P1['dcore_ann_10-14'], P1['dcore_ann_15-18']
    P1['d_same_capital_1'], P1['d_same_capital_2'] = P1['dsamecap_ann_10-14'], P1['dsamecap_ann_15-18']
    P1['z1'], P1['z2'] = P1['z_2010-2014'], P1['z_2015-2018']
    main_ = P1[~P1.companion & ~P1.route_id.isin(['M1', 'M2'])]
    ci, d = main_.ci_excludes_zero.astype(bool), main_.d_net8_ann
    T['P1-S-ALL'] = 'NW 区间排除 0 的为正 %d、为负 %d（每侧随机约 %.0f）' % (int((ci & (d > 0)).sum()), int((ci & (d < 0)).sum()),
                                                                   0.025 * len(main_))
    k = main_[(main_.route_id == 'RK') & main_.direction_role.isin(PRIM) & (main_.policy == 'FALLBACK')]
    kc = main_[(main_.route_id == 'RK') & (main_.direction_role == 'competing')]
    t = main_[(main_.route_id == 'RT') & (main_.direction_role == 'primary') & (main_.policy == 'FALLBACK')
              & pd.to_numeric(main_.strength, errors='coerce').isin([0.125, 0.25])]
    T['P1-S-K'] = '主方向 + 部分混入（α .125/.25/.5）的 %d 个描述符，两段中位 %s / %s，NW 区间排除 0 的为正 %d、为负 %d，need 域同步带为正 %d、为负 %d' % (
        len(k), f3(k.d1.median()), f3(k.d2.median()), int((k.ci_excludes_zero.astype(bool) & (k.d_net8_ann > 0)).sum()),
        int((k.ci_excludes_zero.astype(bool) & (k.d_net8_ann < 0)).sum()), int((k.band_domain_lo > 0).sum()), int((k.band_domain_hi < 0).sum()))
    yc = ['y%d' % y for y in range(2010, 2019)]
    kym = k[yc].median()
    kst = k.assign(a=pd.to_numeric(k.strength, errors='coerce')).groupby('a').d_net8_ann.median().sort_index()
    mono = bool(np.all(np.diff(kst.values) > 0))
    ctrl = [k.d_vs_core_matchN_1.median(), k.d_vs_core_matchN_2.median(), k.d_same_capital_1.median(), k.d_same_capital_2.median(),
            k.z1.median(), k.z2.median()]
    T['P1-S-K2'] = '同人数核心 / 同资本 / 匹配随机三种对照的两段中位 %s；随 α %s（%s）；逐年中位 %d / %d 年为正（最低 %s %s）' % (
        ' / '.join(f3(x) for x in ctrl), '单调上升' if mono else '不单调', '、'.join('%.3g: %s' % (a_, f3(v_)) for a_, v_ in kst.items()),
        int((kym > 0).sum()), len(kym), kym.idxmin()[1:], f3(kym.min(), 2))
    T['P1-S-KC'] = '中位 %s / %s' % (f3(kc.d1.median()), f3(kc.d2.median()))
    T['P1-S-T'] = '主方向 α .125/.25 两段中位 %s / %s' % (f3(t.d1.median()), f3(t.d2.median()))
    tp = main_[(main_.route_id == 'TPAIR') & main_.member_id.astype(str).str.startswith('T_mean20')
               & (pd.to_numeric(main_.strength, errors='coerce') <= 0.5)]
    T['P1-S-TP'] = '20 日 level x CV 复合（TPAIR β ≤ .5，含 β=0 纯水平）%d 个描述符两段中位 %s / %s' % (
        len(tp), f3(tp.d1.median()), f3(tp.d2.median()))
    om = main_[main_.route_id.isin(['RV', 'RO', 'RR', 'RC', 'RA', 'RS', 'RL'])].groupby('route_id')[['d1', 'd2']].median()
    T['P1-S-OTHER'] = '，'.join('%s %s / %s' % (r_, f3(v_.d1, 2), f3(v_.d2, 2)) for r_, v_ in om.iterrows())
    T['P1-S-Z'] = '全部主描述符真实 − 匹配随机（basic）> 0 的占比两段 %s / %s' % (pc((main_.z1 > 0).mean()), pc((main_.z2 > 0).mean()))
    fi = fourarm_recompute()
    ft = fi[(fi.scope == 'full') & (fi.fourarm == 'T_level_x_CV')]
    tt = ft.interaction_ann / ft.interaction_se_nwH
    T['P1-S-FA'] = '四臂 T level x CV 的交互项 full 为正 %d / %d、|t|>2 且为正 %d' % (int((ft.interaction_ann > 0).sum()), len(ft), int((tt > 2).sum()))
    cz = m1_table(P1, main_)
    T['P1-S-M1'] = 'M1 共识里两段都为正的组：' + ('；'.join('%s %s %s %s / %s' % (i_[0], i_[1], i_[2], f3(r_.d1), f3(r_.d2))
                                                     for i_, r_ in cz.iterrows() if r_.d1 > 0 and r_.d2 > 0) or '无')
    T['Q8-M1'] = '共识（consensus）两段中位：' + '；'.join('%s %s %s %s / %s' % (i_[0], i_[1], i_[2], f3(r_.d1), f3(r_.d2))
                                                   for i_, r_ in cz.iterrows())
    ff = fi[fi.scope == 'full'].reset_index(drop=True)
    tt_ = ff.interaction_ann / ff.interaction_se_nwH
    T['Q15-BY'] = '；'.join('%s：交互为正 %d / %d、t>2 %d、t<−2 %d' % (
        nm_, int((g_.interaction_ann > 0).sum()), len(g_), int((tt_[g_.index] > 2).sum()), int((tt_[g_.index] < -2).sum()))
        for nm_, g_ in ff.groupby('fourarm'))
    v = main_[main_.route_id == 'RV'].copy()
    v['base'] = v.member_id.str.replace(r'_(obs|ls)$', '', regex=True)
    v['pol'] = v.member_id.str.extract(r'_(obs|ls)$')[0]
    vv = v[v.pol.notna()]
    pv = vv.pivot_table(index=['base', 'mother_id', 'role', 'strength', 'direction', 'H'], columns='pol', values=['d1', 'd2'])
    dd1 = (pv['d1']['obs'] - pv['d1']['ls']).dropna()
    dd2 = (pv['d2']['obs'] - pv['d2']['ls']).dropna()
    T['Q12-ACC'] = 'OBS − LIMIT_SENS 配对账户差（%d 对）中位 %s / %s，四分位距 %s~%s / %s~%s' % (
        len(dd1), f3(dd1.median()), f3(dd2.median()), f3(dd1.quantile(.25)), f3(dd1.quantile(.75)), f3(dd2.quantile(.25)), f3(dd2.quantile(.75)))
    ra = main_[main_.route_id == 'RA']
    sl_p = ra[(ra.role == 'SLOT') & ra.direction_role.isin(PRIM)]
    sl_c = ra[(ra.role == 'SLOT') & (ra.direction_role == 'competing')]
    TT['Q13-SIGN'] = 'K_rar SLOT 主方向两段中位 %s / %s、竞争方向 %s / %s' % (
        f3(sl_p.d1.median()), f3(sl_p.d2.median()), f3(sl_c.d1.median()), f3(sl_c.d2.median()))
    # ---- part1 事实块（问题卡通用句）
    Pf = F[~F.companion].copy()
    zs = []
    for s in DER:
        z = rd(os.path.join(RD, 'statistics', 'zmap_summary_%s.csv' % s))
        z['seg'] = s[2:4] + '-' + s[-2:]
        zs.append(z)
    Z = pd.concat(zs, ignore_index=True)
    QR = {'Q1': ('RT', 'TPAIR'), 'Q2': ('RK',), 'Q3': ('RV',), 'Q4': ('RO',), 'Q5': ('RR',), 'Q6': ('RC',), 'Q7': ('RL',),
          'Q13': ('RA',), 'Q14': ('RS',), 'Q15': ('FOURARM',)}
    for Qn, routes in QR.items():
        T.update(facts_texts(Pf, Z, Qn, routes))
    # ---- part1b 四臂 M2
    m2p = rd(os.path.join(RD, TAB1, 'M2_panel.csv'))
    m2p['d1r'], m2p['d2r'] = m2p.descriptor_id.map(rc['2010-2014'].d_net8_ann), m2p.descriptor_id.map(rc['2015-2018'].d_net8_ann)
    m2p['fr'] = m2p.descriptor_id.map(rc['full'].d_net8_ann)
    fa_ = P1[(P1.route_id == 'FOURARM') & (P1.policy.astype(str) == 'K_resid_x_A_event')]
    fa_idx = {(r_.mother_id, '%g' % float(re.search(r'\|a=([0-9.]+)\|', r_.descriptor_id).group(1)), str(r_.direction_role), int(r_.H)): r_.deriv
              for r_ in fa_.itertuples()}
    pr = m2p[m2p.variant == 'primary'].copy()
    fa = pr[pr.kind != 'rep'].copy()
    fa['m0r'] = [fa_idx.get((r_.mother_id, '%g' % float(r_.alpha), 'A' if r_.kind == 'fourarm_uni' else 'AB', int(r_.H)), np.nan)
                 for r_ in fa.itertuples()]
    fa['mm'] = fa.fr - fa.m0r
    T['P1B-FA'] = '；'.join('%s：%d 个，两段中位 %s / %s，M2 − 同 α 线性臂 full 中位 %s、>0 占比 %s' % (
        kd_, len(g_), f3(g_.d1r.median()), f3(g_.d2r.median()), f3(g_.mm.median()), pc((g_.mm > 0).mean())) for kd_, g_ in fa.groupby('kind'))
    T['P1B-S-FA'] = '四臂 M2：' + '；'.join('%s 两段中位 %s / %s、M2 − 同 α 线性臂 %s' % (
        kd_, f3(g_.d1r.median()), f3(g_.d2r.median()), f3(g_.mm.median())) for kd_, g_ in fa.groupby('kind'))
    # ---- part2
    st = rd(os.path.join(RD, 'registry', 'stage3_status_table.csv'))
    tot = st[~st.route.isin(['M1', 'M2'])].groupby('segment')[['succeeded', 'failed_tech']].sum()
    T['P2-S-RUN'] = '两后段主路线各 %s SUCCEEDED、FAILED_TECH 合计 %d' % (
        ' / '.join(str(int(tot.loc[s, 'succeeded'])) for s in POST), int(tot.failed_tech.sum()))
    ci = M.ci_post
    T['P2-S-ALL'] = 'NW 区间排除 0：推导 正 %d / 负 %d → 后段 正 %d / 负 %d（每侧随机约 %.0f）；全体主描述符中位 推导合并 %s → 后段合并 %s' % (
        int((M.ci_deriv & (M.deriv > 0)).sum()), int((M.ci_deriv & (M.deriv < 0)).sum()), int((ci & (M.post > 0)).sum()),
        int((ci & (M.post < 0)).sum()), 0.025 * len(M), f3(M.deriv.median()), f3(M.post.median()))
    kk = M[(M.route_id == 'RK') & M.direction_role.isin(PRIM) & (M.policy == 'FALLBACK')]
    kst2 = kk.assign(a=pd.to_numeric(kk.strength, errors='coerce')).groupby('a').post.median()
    T['P2-S-K'] = '同一批 %d 个描述符，推导 %s → 后段两段 %s / %s（%s）；后段合并 NW 排除 0 正 %d / 负 %d、同步带 正 %d / 负 %d；随 α：%s' % (
        len(kk), f3(kk.deriv.median()), f3(kk.p1.median()), f3(kk.p2.median()), sgn_word(kk.p1.median(), kk.p2.median()),
        int((kk.ci_post & (kk.post > 0)).sum()), int((kk.ci_post & (kk.post < 0)).sum()), int((kk.bd_domain_lo > 0).sum()),
        int((kk.bd_domain_hi < 0).sum()), '、'.join('%.3g: %s' % (a_, f3(v_)) for a_, v_ in kst2.items()))
    T['P2-S-K2'] = '对匹配随机 %s / %s、对同人数核心 %s / %s' % (f3(kk.z1.median()), f3(kk.z2.median()), f3(kk.dcore_ann_1.median()),
                                                           f3(kk.dcore_ann_2.median()))
    T['P2-S-PERS'] = '推导 vs 后段点估秩相关：全部主描述符 %s、K 主方向 %s' % (f3(spearman(M.deriv.values, M.post.values)),
                                                                   f3(spearman(kk.deriv.values, kk.post.values)))
    t2 = M[(M.route_id == 'RT') & (M.direction_role == 'primary') & (M.policy == 'FALLBACK')
           & pd.to_numeric(M.strength, errors='coerce').isin([0.125, 0.25])]
    T['P2-S-T'] = '小权重加两后段 %s / %s' % (f3(t2.p1.median()), f3(t2.p2.median()))
    rep_ = M[(M.route_id == 'RT') & (M.direction_role == 'primary') & M.policy.isin(['FULL_REPLACE', 'FALLBACK_REPLACE'])]
    T['P2-S-P20'] = '对同人数核心 %s / %s' % (f3(rep_.dcore_ann_1.median()), f3(rep_.dcore_ann_2.median()))
    rrs = M[(M.route_id == 'RR') & (M.role == 'SWAP')]
    T['P2-S-P21'] = 'RR 同人数 SWAP 对匹配随机 两后段 %s / %s' % (f3(rrs.z1.median()), f3(rrs.z2.median()))
    rs = M[(M.route_id == 'RS') & (M.role == 'SWAP')]
    T['P2-S-RS'] = '对母体 %s / %s、对匹配随机 %s / %s' % (f3(rs.p1.median()), f3(rs.p2.median()), f3(rs.z1.median()), f3(rs.z2.median()))
    rvr = M[(M.route_id == 'RV') & (M.direction_role == 'reverse_control') & M.role.isin(['VETO_NEW', 'SOFT_HARD'])]
    T['P2-S-V'] = '反向删除（删低风险）2019-23 %s、2024-26 %s' % (f3(rvr.p1.median()), f3(rvr.p2.median()))
    rcs = M[(M.route_id == 'RC') & (M.direction_role == 'primary') & (M.role == 'SLOT')]
    T['P2-S-C'] = 'A06 的 C 核心槽位混入 两后段 %s / %s（推导 %s）' % (f3(rcs.p1.median()), f3(rcs.p2.median()), f3(rcs.deriv.median()))
    led = pd.concat([rd(p_) for s in POST for p_ in glob.glob(os.path.join(RD, 'm2', s, 'ledger_[0-9][0-9]*.csv')) if '_timing' not in p_],
                    ignore_index=True)
    zs_ = led[led.variant == 'primary'].groupby('segment').action.apply(lambda x: (x == 'zero_modification').mean())
    T['P2-S-M2'] = '内层选择零修改的 (程序 x 年) 占比 ' + '，'.join('%s %s' % (s_, pc(v_)) for s_, v_ in zs_.items())
    T['Q9-LOYO'] = '后段合并去 2020 的描述符中位 %s（不去 %s）；去 2024 %s' % (
        f3(M.post_loyo_ex2020.median()), f3(M.post.median()), f3(M.post_loyo_ex2024.median()))
    T['Q9-STATE'] = '后段合并状态词：' + '，'.join('%s %d' % (k_, v_) for k_, v_ in M.state_post.value_counts().items())
    T['Q9-VSDERIV'] = 'NW 区间排除 0：推导合并 正 %d / 负 %d → 后段合并 正 %d / 负 %d（同一批 %d 个主描述符）' % (
        int((M.ci_deriv & (M.deriv > 0)).sum()), int((M.ci_deriv & (M.deriv < 0)).sum()), int((M.ci_post & (M.post > 0)).sum()),
        int((M.ci_post & (M.post < 0)).sum()), len(M))
    T['Q2P-MECH'] = '同人数核心两段中位 %s / %s、同资本 %s / %s、真实−匹配随机 %s / %s（>0 占比 %s / %s）' % (
        f3(kk.dcore_ann_1.median()), f3(kk.dcore_ann_2.median()), f3(kk.dsamecap_ann_1.median()), f3(kk.dsamecap_ann_2.median()),
        f3(kk.z1.median()), f3(kk.z2.median()), pc((kk.z1 > 0).mean()), pc((kk.z2 > 0).mean()))
    T['Q2P-READ'] = '同一批 %d 个冻结描述符：推导合并 %s → 后段 %s / %s' % (len(kk), f3(kk.deriv.median()), f3(kk.p1.median()), f3(kk.p2.median()))
    T['P20-CORE'] = 'T 腿完全替换（FULL / FALLBACK_REPLACE，主方向）%d 个描述符：子−同人数核心两后段中位 %s / %s（%s）；对真实母体 %s / %s' % (
        len(rep_), f3(rep_.dcore_ann_1.median()), f3(rep_.dcore_ann_2.median()), sgn_word(rep_.dcore_ann_1.median(), rep_.dcore_ann_2.median()),
        f3(rep_.p1.median()), f3(rep_.p2.median()))
    rr = M[M.route_id == 'RR']
    T['P21-Z'] = '；'.join('%s / %s（%d 个）：对母体 %s / %s；真实−匹配随机 %s / %s（%s）' % (
        dr_, ro_, len(g_), f3(g_.p1.median()), f3(g_.p2.median()), f3(g_.z1.median()), f3(g_.z2.median()), sgn_word(g_.z1.median(), g_.z2.median()))
        for (dr_, ro_), g_ in rr[rr.role.isin(['SWAP', 'ADD_SCORE'])].groupby(['direction_role', 'role']))
    MID = {'SLOT': ('0.25', 'FALLBACK'), 'COMMON_SUPPORT': ('0.25', 'COMMON_SUPPORT'), 'VETO_NEW': ('10', None), 'SOFT': ('0.5', None),
           'SOFT_HARD': ('10', None), 'ADD_SCORE': ('0.125', None), 'SWAP': ('0.1', None), 'T_PAIR': ('0.5', None), 'RL': ('edge_replace', None)}
    repm = M[M.representative.astype(str).str.lower().isin(['true', '1', '1.0'])]
    keep = []
    for i, r_ in repm.iterrows():
        m_ = MID.get(r_.role)
        if m_ is None or int(r_.H) != 5:
            continue
        if str(r_.strength) != m_[0]:
            try:
                if abs(float(r_.strength) - float(m_[0])) > 1e-9:
                    continue
            except ValueError:
                continue
        if m_[1] is not None and str(r_.policy) != m_[1]:
            continue
        keep.append(i)
    rp = repm.loc[keep]
    T['P2-REP'] = 'M0_FIXED（与 part1a 同一选法：代表成员 x 中间档预算 x H5）%d 个描述符：两后段中位 %s / %s；后段合并 NW 排除 0 为正 %d、为负 %d' % (
        len(rp), f3(rp.p1.median()), f3(rp.p2.median()), int((rp.ci_post & (rp.post > 0)).sum()), int((rp.ci_post & (rp.post < 0)).sum()))
    # ---- part3
    b = rd(os.path.join(WORK, 'mother_baseline_replay.csv')).rename(columns={'final_B_per_day': 'held', 'capital_pos_mean': 'capital'})
    post = b[b.segment.isin(POST)]
    seg_cap = b.groupby('segment').capital.agg(['min', 'max'])
    seg_pc = b.groupby('segment').net8_per_capital.agg(['min', 'max'])
    T['P3-BASE'] = '两后段母体 net8 年化 %s ~ %s、持仓 %.0f ~ %.0f 名 / 日、投入资金 %.2f ~ %.2f；投入资金各段 %s；单位资金 net8 各段 %s' % (
        f3(post.net8_ann.min(), 2), f3(post.net8_ann.max(), 2), post.held.min(), post.held.max(), post.capital.min(), post.capital.max(),
        '，'.join('%s %.2f–%.2f' % (s_, r_['min'], r_['max']) for s_, r_ in seg_cap.iterrows()),
        '，'.join('%s %.1f–%.1f' % (s_, r_['min'], r_['max']) for s_, r_ in seg_pc.iterrows()))
    T['P3-S-BASE'] = '母体基线：两后段 net8 年化 %s ~ %s、投入资金 %.2f ~ %.2f' % (f3(post.net8_ann.min(), 2), f3(post.net8_ann.max(), 2),
                                                                     post.capital.min(), post.capital.max())
    single = M[~M.member_id.astype(str).str.contains(r'[|+]') & M.direction_role.isin(('primary', 'primary_inverse_mapped', 'high_role',
                                                                                          'reversal_domain'))]
    mem = single.groupby('member_id').agg(deriv=('deriv', 'median'), post=('post', 'median'), all4=('all4', 'median'))
    both = mem[(mem.deriv > 0.05) & (mem.post > 0.05)].sort_values('all4', ascending=False)
    T['P3-BOTH'] = '两期都为正的成员 %d 个：%s' % (len(both), '、'.join(both.index))
    T['P3-S-BOTH'] = '两期都为正的成员 %d 个（K 响应族 / 源桥与 T 20 日绝对尺度）' % len(both)
    X = M.copy()
    X['a'] = pd.to_numeric(X.strength, errors='coerce')
    K = X[(X.route_id == 'RK') & X.direction_role.isin(PRIM) & (X.policy == 'FALLBACK')]
    kf = fam_tab(K)
    derpos = kf[(kf.d10_14 > 0) & (kf.d15_18 > 0)]
    postpos = kf[(kf.p19_23 > 0) & (kf.p24_26 > 0)]
    neg24 = kf[kf.p24_26 < 0].sort_values('p24_26')
    T['P3-FAM-K'] = '推导两段中位都为正的族 %d / %d；后段两段中位都为正的族：%s；2024-26 中位为负的族：%s' % (
        len(derpos), len(kf), '、'.join(postpos.family) or '无', '、'.join('%s %s' % (r_.family, f3(r_.p24_26)) for r_ in neg24.itertuples()))

    def four(r_):
        return '%s / %s / %s / %s' % (f3(r_.d10_14), f3(r_.d15_18), f3(r_.p19_23), f3(r_.p24_26))
    kfi = kf.set_index('family')
    resp = kfi.loc[[x for x in kfi.index if x in ('amount_response', 'turnover_response')]]
    br = kfi.loc['source_bridge']
    T['P3-FAM-KR'] = '；'.join('%s 四段 %s，逐年为正 %s，后段显著 正 %d / 负 %d，同资本后段 %s / %s，对匹配随机后段 %s / %s' % (
        fam_, four(r_), r_.yrs_pos, r_.ci_pos, r_.ci_neg, f3(r_.samecap_19_23), f3(r_.samecap_24_26), f3(r_.vs_rand_19_23), f3(r_.vs_rand_24_26))
        for fam_, r_ in resp.iterrows()) + '；源桥（原 K 的平滑 / 比值和）四段 %s，逐年为正 %s' % (four(br), br.yrs_pos)
    km = fam_tab(K[K.family.isin(['amount_response', 'turnover_response', 'source_bridge'])], by='member_id')
    km['family'] = km.member_id.map(K.drop_duplicates('member_id').set_index('member_id').family)
    km = km.sort_values(['family', 'member_id'])
    am = km[km.family == 'amount_response']
    T['P3-FAM-KM'] = 'amount_response 成员后段两段中位与显著个数：' + '；'.join('%s %s / %s（正 %d / 负 %d）' % (
        r_.member_id, f3(r_.p19_23), f3(r_.p24_26), r_.ci_pos, r_.ci_neg) for r_ in am.itertuples())
    ah = []
    for lab, col, vals in (('α', 'a', sorted(K.a.dropna().unique())), ('H', 'H', sorted(K.H.unique()))):
        for v_ in vals:
            x = K[K[col] == v_]
            ah.append(dict(group='%s=%g' % (lab, v_), d10_14=x.d1.median(), d15_18=x.d2.median(), p19_23=x.p1.median(), p24_26=x.p2.median()))
    ah = pd.DataFrame(ah)
    a_ = ah[ah.group.str.startswith('α')].set_index('group')
    h_ = ah[ah.group.str.startswith('H')].set_index('group')
    ia, ih = (a_.d10_14 + a_.d15_18).idxmax(), (h_.d10_14 + h_.d15_18).idxmax()
    T['P3-FAM-AH'] = '2024-26 中位：按 α %s；按 H %s；推导两段中位最高的是 %s（%s / %s）与 %s（%s / %s）' % (
        '，'.join('%s %s' % (k_, f3(v_)) for k_, v_ in a_.p24_26.items()), '，'.join('%s %s' % (k_, f3(v_)) for k_, v_ in h_.p24_26.items()),
        ia, f3(a_.loc[ia, 'd10_14']), f3(a_.loc[ia, 'd15_18']), ih, f3(h_.loc[ih, 'd10_14']), f3(h_.loc[ih, 'd15_18']))
    sl = fam_tab(K[(K.a <= 0.25) & (K.H >= 10)]).set_index('family')
    T['P3-FAM-SLICE'] = '；'.join('%s 四段 %s，逐年为正 %s，后段显著 正 %d / 负 %d，后段 MDE80 中位 %s' % (
        fam_, four(sl.loc[fam_]), sl.loc[fam_, 'yrs_pos'], sl.loc[fam_, 'ci_pos'], sl.loc[fam_, 'ci_neg'], f3(sl.loc[fam_, 'mde80_post']))
        for fam_ in ('amount_response', 'turnover_response', 'source_bridge') if fam_ in sl.index)
    Tt = X[(X.route_id == 'RT') & (X.direction_role == 'primary') & (X.policy == 'FALLBACK') & X.a.isin([0.125, 0.25])]
    tf = fam_tab(Tt)
    tpos = tf[(tf.p19_23 > 0) & (tf.p24_26 > 0)]
    T['P3-FAM-T'] = 'T 小权重加：后段两段中位都为正的族：%s；各族后段两段中位都在 ±%.2f 以内' % (
        '、'.join('%s %s / %s' % (r_.family, f3(r_.p19_23), f3(r_.p24_26)) for r_ in tpos.itertuples()) or '无',
        np.nanmax(np.abs(tf[['p19_23', 'p24_26']].values)))
    res = K[K.family == 'cross_sectional_residual']
    T['P3-FAM-Q18'] = 'K_res_log 所在的 cross_sectional_residual 族在账户层后段两段中位 %s / %s' % (f3(res.p1.median()), f3(res.p2.median()))
    cv = rd(os.path.join(RD, 'registry', 'coverage.csv'))
    T['P3-COV'] = 'coverage 状态计数：' + '，'.join('%s %d' % (k_, v_) for k_, v_ in cv.status.value_counts().items())
    T['P3-S-K'] = 'K 槽位（K 轴 9 个估计量族部分混入，%d 个描述符）：推导合并 %s → 后段 %s / %s → 四段合并 %s' % (
        len(K), f3(K.deriv.median()), f3(K.p1.median()), f3(K.p2.median()), f3(K.all4.median()))
    ar = kfi.loc['amount_response']
    rep5 = kfi[kfi.index.isin(['log_repr', 'cross_sectional_residual', 'component', 'aggregation_bridge', 'pointwise_inverse_bridge'])]
    T['P3-S-FAM'] = 'K 分族：amount_response 四段中位 %s（逐年为正 %s，同资本后段 %s / %s）；改表示 / 中性化 / 聚合顺序 / 点态倒数各族 2024-26 为 %s ~ %s' % (
        four(ar), ar.yrs_pos, f3(ar.samecap_19_23), f3(ar.samecap_24_26), f3(rep5.p24_26.min()), f3(rep5.p24_26.max()))
    g1 = M.groupby('route_id').agg(deriv=('deriv', 'median'), post=('post', 'median')).reset_index()
    T['P3-S-NEG'] = '推导合并与后段合并中位都为负的路线：%s；后段合并中位低于推导合并的路线 %d / %d（%s），高于的：%s' % (
        '、'.join(r_.route_id for r_ in g1.itertuples() if r_.deriv < 0 and r_.post < 0), int((g1.post < g1.deriv).sum()), len(g1),
        '、'.join(r_.route_id for r_ in g1.itertuples() if r_.post < r_.deriv), '、'.join(r_.route_id for r_ in g1.itertuples() if r_.post > r_.deriv) or '无')
    capp = os.path.join(WORK, 'c1_pairs_rc.csv')
    if os.path.exists(capp):
        O = rd(capp)
        pn = O[O.contrast == 'N250−N100'].groupby('segment')[['d_deploy', 'cap_part']].mean()
        T['P3-S-C1'] = '但 N250−N100 的部署视图差里投入资金部分占 %s' % '，'.join('%s %s' % (s_, pc(r_.cap_part / r_.d_deploy)) for s_, r_ in pn.iterrows())
    K_ = rd(os.path.join(RD, 'carried', 'summary', 'C2_children_delta.csv'),
            usecols=['segment', 'route_id', 'direction_role', 'policy', 'H', 'descriptor_id', 'd_net8_minus_sqrt_A10_k1'])
    kk_ = K_[(K_.route_id == 'RK') & K_.direction_role.isin(PRIM) & (K_.policy == 'FALLBACK') & (K_.H >= 10)].copy()
    kk_['dn'] = [rc[s_].d_net8_ann.get(d_, np.nan) for s_, d_ in zip(kk_.segment, kk_.descriptor_id)]    # 无冲击列用账本重算值
    lg = kk_.groupby('segment')[['dn', 'd_net8_minus_sqrt_A10_k1']].median()
    T['P3-S-C2'] = '长 H（≥10）K 增量 A10 亿 κ1 下各段 %s，无冲击 %s' % (' / '.join(f3(v_) for v_ in lg.d_net8_minus_sqrt_A10_k1),
                                                                ' / '.join(f3(v_) for v_ in lg.dn))
    return T, TT


def stage_D():
    F, rc = panel()
    Q = load_qids()
    reps = {f: norm(open(os.path.join(RD, 'reports', f), encoding='utf-8').read()) for f in REPORTS}
    # ---- D1 现算文本 ↔ 正文
    rows = []
    for r_ in Q.itertuples():
        mk = '〔%s〕' % r_.query_id
        tgt = REPORT_OF[r_.file]
        rows.append(dict(file=r_.file, query_id=r_.query_id, report=tgt or '', marker_in=';'.join(f for f, t in reps.items() if mk in t),
                         text_match=bool(tgt and (norm(r_.text) + mk) in reps[tgt])))
    D1 = pd.DataFrame(rows)
    D1.to_csv(os.path.join(VD, 'D1_query_text.csv'), index=False)
    for fn in QFILES:
        x = D1[D1.file == fn]
        if REPORT_OF[fn] is None:
            rec('D1', '%s %d 条：正文逐字核对' % (fn, len(x)), '五份 REPORT 正文中的〔id〕句', int((x.marker_in != '').sum()), 'NOT_COMPUTABLE',
                inputs=os.path.join(TAB1, fn), func='substring',
                note='这些问题卡事实句写在 reports/part1_facts.md（part1 REPORT 第 3 行指向它），不在五份 REPORT 正文，也不在 brief §1 封闭输入清单；'
                     '其中 %d 条的 id 在 REPORT 正文出现（%s）' % (int((x.marker_in != '').sum()), ','.join(x[x.marker_in != ''].query_id)))
        else:
            miss = x[~x.text_match]
            v_exact('D1', '%s → %s：%d 条现算文本 + 〔id〕逐字出现在正文（空白归一）' % (fn, REPORT_OF[fn], len(x)), len(x), int(x.text_match.sum()),
                    inputs=os.path.join(QFILES[fn], fn), func='substring', note='不符：%s' % ','.join(miss.query_id) if len(miss) else '')
    allmk = {f: set(re.findall(r'〔([A-Za-z0-9\-]+)〕', t)) for f, t in reps.items()}
    known = set(Q.query_id)
    for f, ids in allmk.items():
        v_exact('D1', '%s 正文里的〔id〕都有存档文本（无存档的个数）' % f, 0, len(ids - known), func='regex', note=','.join(sorted(ids - known)))
    dup = Q.groupby('query_id').filter(lambda g: len(g) > 1)
    v_exact('D1', 'query_id 唯一（跨 6 个存档文件重复的 id 个数）', 0, int(dup.query_id.nunique()), func='groupby',
            note='；'.join('%s：%s' % (q_, ' | '.join('%s「%s」' % (r_.file, r_.text) for r_ in g_.itertuples())) for q_, g_ in dup.groupby('query_id')))
    txt = open(os.path.join(RD, 'reports', 'E6i_REVIEW_input.md'), encoding='utf-8').read().split('## query_id（235 条）', 1)[1]
    ri = []
    for ln in txt.split('\n'):
        if ln.startswith('| reports/'):
            c = [x.strip() for x in ln.strip().strip('|').split('|', 2)]
            ri.append(dict(file=os.path.basename(c[0]), query_id=c[1], text=c[2].strip().replace('\\|', '|')))
    RI = pd.DataFrame(ri)
    j = RI.merge(Q, on=['file', 'query_id'], how='left', suffixes=('_ri', '_csv'))
    numd = [NUMTOK.findall(norm(a)) != NUMTOK.findall(norm(b)) for a, b in zip(j.text_ri, j.text_csv)]
    txtd = j[[norm(a) != norm(b) for a, b in zip(j.text_ri, j.text_csv)]]
    v_exact('D1', 'REVIEW_input §query_id %d 条 vs 存档文本：数字部分不符的条数（brief 容差 = EXACT 字符串（数字部分））' % len(RI), 0,
            int(sum(numd)), inputs='reports/E6i_REVIEW_input.md', func='merge',
            note='非数字字符不同的 %d 条：%s' % (len(txtd), '；'.join('%s（REVIEW_input 把 | 写成 /）' % q_ if '/' in a and '|' in b else q_
                                                          for q_, a, b in zip(txtd.query_id, txtd.text_ri, txtd.text_csv))))
    # ---- D2 60 条（必做 45 + 随机 18）
    ids = sorted(set(RI.query_id))
    must = [q_ for q_ in ids if q_.startswith(('P1-S-', 'P2-S-', 'P3-S-')) or q_ in MUST]
    rest = sorted(set(ids) - set(must))
    pick = [rest[i] for i in np.random.default_rng(20260925).choice(len(rest), 18, replace=False)]
    rec('D2', '抽样：必做条数（brief 预注册 42）+ 随机 18（其余 %d 个唯一 id 排序后 default_rng(20260925).choice）' % len(rest),
        42, len(must), 'REPRODUCED' if len(must) == 42 else 'DIFFERS', tol='EXACT', func='rng',
        note='必做实际 45 条（P2-S-* 有 12 条）；REVIEW_input 235 行只有 234 个唯一 id（Q13-SIGN 两条）；随机：%s' % ','.join(pick))
    T, TT = build_texts(F, rc)
    src = {r_.query_id: r_ for r_ in Q.itertuples()}
    rows = []
    for q_ in must + pick:
        for r_ in Q[Q.query_id == q_].itertuples():
            built = TT.get(q_) if (q_ in TT and r_.file == 'query_ids_part1_text.csv') else T.get(q_)
            if q_ in ('P3-CARDS', 'P3-DELTA'):
                rec('D2', '%s' % q_, r_.text, None, 'NOT_COMPUTABLE', inputs=os.path.join(QFILES[r_.file], r_.file), func='-',
                    note='所引 reports/hypothesis_outcomes.json / reports/factor_iteration_delta.csv 不在 brief §1 封闭输入清单')
                continue
            if built is None:
                rec('D2', '%s' % q_, r_.text, None, 'NOT_COMPUTABLE', func='-', note='无重算公式')
                continue
            cmp_text('D2', '%s（%s）' % (q_, r_.file), r_.text, built, os.path.join(QFILES[r_.file], r_.file))
            rows.append(dict(query_id=q_, file=r_.file, stored=norm(r_.text), rebuilt=norm(built)))
    pd.DataFrame(rows).to_csv(os.path.join(VD, 'D2_rebuild.csv'), index=False)
    # ---- D3 表头十项
    want = {'E6i_REPORT_R0.md': 20, 'E6i_REPORT_part1.md': 28, 'E6i_REPORT_part1b.md': 7, 'E6i_REPORT_part2.md': 22, 'E6i_REPORT_part3.md': 17}
    ri_n = {m.group(1): int(m.group(2)) for m in re.finditer(r'## (E6i_REPORT_\w+\.md)（(\d+) 张表）',
                                                          open(os.path.join(RD, 'reports', 'E6i_REVIEW_input.md'), encoding='utf-8').read())}
    for f, n in want.items():
        tabs = md_tables(os.path.join(RD, 'reports', f))
        nohdr = [ln for h, c, r_, ln in tabs if not h]
        miss = [(ln, [it for it in HDR10 if '**%s**' % it not in h]) for h, c, r_, ln in tabs if h]
        miss = [(ln, m_) for ln, m_ in miss if m_]
        v_exact('D3', '%s 表数（brief / REVIEW_input 期望 %d / %s）' % (f, n, ri_n.get(f)), n, len(tabs), func='md_tables',
                note='REPORT 当前版本解析出 %d 张' % len(tabs))
        v_exact('D3', '%s 缺十项表头的表（无表头 / 缺项）' % f, (0, 0), (len(nohdr), len(miss)), func='md_tables',
                note='无表头行号 %s；缺项 %s' % (nohdr[:8], miss[:4]))
    # ---- D4 禁用词
    bad_words = ('穷尽', '到平台', '饱和', '改无可改', '可交付', '已确证', '必须换核')
    for f in REPORTS:
        raw = open(os.path.join(RD, 'reports', f), encoding='utf-8').read().split('\n')
        hits = [(i + 1, w) for i, ln in enumerate(raw) for w in bad_words if w in ln]
        v_exact('D4', '%s 禁用词出现次数' % f, 0, len(hits), func='grep', note='；'.join('行 %d「%s」' % h for h in hits[:10]))
    # ---- D5 全称句：全部列出；brief 点名的 5 句用表计数复核
    kw = ('全部', '没有', '唯一', '两段同号', '都为正', '最')
    rows = []
    for f in REPORTS:
        for i, ln in enumerate(open(os.path.join(RD, 'reports', f), encoding='utf-8').read().split('\n')):
            if ln.startswith('|') or ln.startswith('> **汇总算子**'):
                continue
            for sent in re.split(r'(?<=[。；])', ln):
                hit = [w for w in kw if w in sent]
                if hit:
                    rows.append(dict(report=f, line=i + 1, words='/'.join(hit), sentence=sent.strip()))
    U = pd.DataFrame(rows)
    D2IDS = set(must) | set(pick) | {'P3-FAM-ALL', 'Q2P-COMP', 'Q15P-INT', 'P3-BOTH', 'P3-FAM-K', 'Q-R0-DPOS2', 'Q-R0-DPOS3', 'Q-R0-Q12A',
                                       'P1-ZMAP', 'P2-ZMAP', 'P1-ALL-BAND', 'P2-PERSIST', 'P1-SWAPDIST', 'Q7-KIMPACT', 'P3-FAM-AH'}

    R0_, P1_, P2_, P3_ = REPORTS[0], REPORTS[1], REPORTS[3], REPORTS[4]
    CHECKED = [(R0_, 13, '43% / 59%', 'C13'), (R0_, 265, '92', 'C13'), (R0_, 265, '117', 'C13'), (R0_, 329, 'R_peervol5', 'D5'),
               (R0_, 530, 'R_peervol5', 'D5'), (R0_, 493, '48/49', 'D5'), (R0_, 497, '44 / 49', 'D5'), (R0_, 498, '9.0% / 14.1%', 'C13'),
               (R0_, 513, '0.958', 'D5'), (P1_, 16, 'RK primary high_bad', 'D2'), (P1_, 24, '104856', 'C9'),
               (P1_, 142, '全部 H 上都改善母体', 'D5'), (P1_, 228, '更大权重为负', 'D5'), (P1_, 270, '真实状态并不优于随机状态', 'D5'),
               (P1_, 363, '+0.002', 'D5'), (P2_, 12, 'amount_response、source_bridge', 'D5'), (P2_, 27, '104856', 'C9'),
               (P2_, 92, '+0.648', 'C14'), (P2_, 180, '-1.160', 'D5'), (P2_, 181, 'amount_response、source_bridge', 'D5'),
               (P3_, 110, '9 / 9', 'D2'), (P3_, 110, 'amount_response、source_bridge', 'D2'), (P3_, 179, 'relative_scale', 'D2'),
               (P3_, 179, '±0.14', 'D2'), (P3_, 193, 'RV idiosyncratic', 'D5'), (P3_, 196, '9 个族都为正', 'D2'),
               (P3_, 199, 'idiosyncratic', 'D5'), (P3_, 257, '66%', 'C11'), (P3_, 333, '+0.160', 'C12'), (P3_, 347, '0 / 4', 'D5')]

    def cover(sent, rep, line):
        ids = set(re.findall(r'〔([A-Za-z0-9\-]+)〕', sent))
        hit = [c for f_, l_, key, c in CHECKED if f_ == rep and l_ == line and key in sent]
        if ids & D2IDS or hit:
            return 'D2 / D5 / V-C 重算（%s）' % ','.join(sorted((ids & D2IDS) | set(hit)))
        if NUMTOK.search(sent):
            return '有数字：D1 只核正文 = 存档文本' if ids else '有数字：本程序未逐句重算'
        return '无数字（定性 / 范围句）'
    U['coverage'] = [cover(r_.sentence, r_.report, r_.line) for r_ in U.itertuples()]
    U.to_csv(os.path.join(VD, 'D5_universal_sentences.csv'), index=False)
    cc = U.coverage.str.split('（').str[0].value_counts().to_dict()
    rec('D5', '全称句清单（五份 REPORT 正文，表格行与表头除外）：%d 句' % len(U), '逐句用表计数复核', cc,
        'NOT_COMPUTABLE' if any(k_.startswith('有数字') for k_ in cc) else 'REPRODUCED', func='regex',
        note='逐句清单与覆盖列 verify/D5_universal_sentences.csv；点名句与可计数句见下列各行')
    X = F[~F.companion & F.route_id.isin(MAIN)].copy()
    K = X[(X.route_id == 'RK') & X.direction_role.isin(PRIM) & (X.policy == 'FALLBACK')]
    kf = fam_tab(K)
    single = X[~X.member_id.astype(str).str.contains(r'[|+]') & X.direction_role.isin(('primary', 'primary_inverse_mapped', 'high_role', 'reversal_domain'))]
    mem = single.groupby('member_id').agg(deriv=('deriv', 'median'), post=('post', 'median'))
    v_exact('D5', 'P3-BOTH「两期都为正的成员 11 个」', 11, int(((mem.deriv > 0.05) & (mem.post > 0.05)).sum()), func='count')
    v_exact('D5', 'P3-FAM-K「推导两段中位都为正的族 9 / 9」', (9, 9), (int(((kf.d10_14 > 0) & (kf.d15_18 > 0)).sum()), len(kf)), func='count')
    v_exact('D5', 'P3-FAM-K「后段两段中位都为正的族：amount_response、source_bridge」', ['amount_response', 'source_bridge'],
            list(kf[(kf.p19_23 > 0) & (kf.p24_26 > 0)].family), func='filter')
    fam2 = K.groupby('family')[['p1', 'p2', 'post']].median().sort_values('post', ascending=False)   # 生成器按后段合并中位降序列族
    kh = K.groupby('H')[['p1', 'p2']].median()
    km_ = K.groupby('mother_id')[['p1', 'p2']].median()
    got = ('、'.join(x for x, r_ in fam2.iterrows() if r_.p1 > 0 and r_.p2 > 0) or '无', '、'.join('H%d' % h for h, r_ in kh.iterrows() if r_.p1 > 0 and r_.p2 > 0) or '无',
           '、'.join(m_ for m_, r_ in km_.iterrows() if r_.p1 > 0 and r_.p2 > 0) or '无')
    v_exact('D5', 'Q2 后段「两后段都为正的子集：族 amount_response、source_bridge；H：H20；母体：无」', ('amount_response、source_bridge', 'H20', '无'), got,
            func='filter')
    fi = fourarm_recompute()
    pp = fi[fi.scope == 'post']
    tt = pp.interaction_ann / pp.interaction_se_nwH
    v_exact('D5', 'Q15P-INT「后段合并交互项 t>2 的 32、t<−2 的 0（共 72）」', (32, 0, 72), (int((tt > 2).sum()), int((tt < -2).sum()), len(pp)),
            func='fourarm_recompute')
    d5_extra(F, rc, Q)


def d5_extra(F, rc, Q):
    """D5：可计数的全称句逐句复核（REPORT 正文里未被 D2 覆盖、带数字或可计数的句子）。"""
    qt = {r_.query_id: r_.text for r_ in Q.itertuples() if r_.file != 'query_ids_part1.csv'}
    P1 = F.copy()
    P1['z1'], P1['z2'] = P1['z_2010-2014'], P1['z_2015-2018']
    main_ = P1[~P1.companion & ~P1.route_id.isin(['M1', 'M2'])]
    # (1) part1 Q2：K 槽位在三个母体、两段、全部 H 上都改善母体（按组中位）
    k = main_[(main_.route_id == 'RK') & main_.direction_role.isin(PRIM) & (main_.policy == 'FALLBACK')]
    bm = k.groupby('mother_id')[['d1', 'd2']].median()
    bh = k.groupby('H')[['d1', 'd2']].median()
    v_exact('D5', 'part1 Q2「三个母体、两段、全部 H 上都改善母体」：母体组 / H 组中两段中位都 > 0 的组数', (3, 3, 6, 6),
            (len(bm), int(((bm.d1 > 0) & (bm.d2 > 0)).sum()), len(bh), int(((bh.d1 > 0) & (bh.d2 > 0)).sum())), func='groupby',
            note='母体组 %s；H 组 %s' % (bm.round(3).to_dict('index'), bh.round(3).to_dict('index')))
    # (2) part1 Q3：ADD 在最小权重两段接近 0、更大权重为负
    ad = main_[(main_.route_id == 'RV') & (main_.role == 'ADD_SCORE') & (main_.direction_role == 'primary')]
    bs = ad.assign(a=pd.to_numeric(ad.strength, errors='coerce')).groupby('a')[['d1', 'd2']].median().sort_index()
    big = bs.iloc[1:]
    bf = ad.assign(a=pd.to_numeric(ad.strength, errors='coerce')).groupby('a').deriv.median().sort_index().iloc[1:]
    nt = '各档（强度: d1 / d2 / full）%s；最小权重两段 %s / %s（"接近 0"不计数）' % (
        {float(i): (round(r_.d1, 3), round(r_.d2, 3), round(float(bf.get(i, np.nan)), 3)) for i, r_ in bs.iterrows()},
        f3(bs.iloc[0].d1), f3(bs.iloc[0].d2))
    v_exact('D5', 'part1 Q3「ADD 更大权重为负」按两段各自读：最小权重以外两段中位都 < 0 的档数 / 档数', len(big),
            int(((big.d1 < 0) & (big.d2 < 0)).sum()), func='groupby', note=nt)
    v_exact('D5', 'part1 Q3「ADD 更大权重为负」按 full 列读：最小权重以外 full 中位 < 0 的档数 / 档数', len(bf), int((bf < 0).sum()),
            func='groupby', note='句子没有写明按哪一列；两种读法并列')
    # (3) part1 Q4：真实状态并不优于随机状态（RO 焦点臂）
    fo = main_[(main_.route_id == 'RO') & (main_.role == 'FOCAL_NEW')]
    fr = fo.groupby(['direction_role', 'strength'])[['d1', 'd2']].median()
    cnt, tot, det = 0, 0, {}
    for dr_ in fr.index.get_level_values(0).unique():
        x = fr.loc[dr_]
        if 'real_state' in x.index and 'random_state' in x.index:
            for c in ('d1', 'd2'):
                tot += 1
                cnt += int(x.loc['real_state', c] > x.loc['random_state', c])
                det['%s %s' % (dr_, c)] = (round(x.loc['real_state', c], 3), round(x.loc['random_state', c], 3))
    v_exact('D5', 'part1 Q4「真实状态并不优于随机状态」：real_state 中位 > random_state 中位 的 (方向, 段) 个数 / 总数', (0, 4), (cnt, tot),
            func='groupby', note='(real, random)：%s' % det)
    # (4) part3 §1b P3-FAM-ALL：其余路线后段两段中位都为正的族
    X = F[~F.companion & F.route_id.isin(MAIN)].copy()
    other = [('RV', X[(X.route_id == 'RV') & (X.direction_role == 'primary') & X.role.isin(['VETO_NEW', 'SOFT', 'SOFT_HARD'])]),
             ('RO', X[(X.route_id == 'RO') & (X.direction_role == 'high_role')]), ('RR', X[(X.route_id == 'RR') & (X.role == 'SWAP')]),
             ('RC', X[(X.route_id == 'RC') & (X.direction_role == 'primary')]), ('RA', X[(X.route_id == 'RA') & (X.role == 'SWAP')]),
             ('RS', X[(X.route_id == 'RS') & (X.role == 'SWAP')]), ('RL', X[X.route_id == 'RL'])]
    parts, allpos = [], []
    for rid, g in other:
        t = fam_tab(g)
        pos = t[(t.p19_23 > 0) & (t.p24_26 > 0)]
        parts.append('%s %s' % (rid, '、'.join(pos.family) or '—'))
        allpos += [(rid, r_.family, round(r_.d10_14, 3), round(r_.p19_23, 3), round(r_.p24_26, 3)) for r_ in pos.itertuples()]
    rc_ = X[(X.route_id == 'RC') & (X.direction_role == 'primary')]
    built = '其余路线后段两段中位都为正的族：' + '；'.join(parts) + '；C 主方向：对母体后段中位 %s / %s，对匹配随机 %s / %s' % (
        f3(rc_.p1.median()), f3(rc_.p2.median()), f3(rc_.z1.median()), f3(rc_.z2.median()))
    cmp_text('D5', 'P3-FAM-ALL（part3 §1b「其余路线后段两段中位都为正的族：RV idiosyncratic」）', qt.get('P3-FAM-ALL', ''), built,
             os.path.join(TAB3, 'query_ids_part3.csv'))
    ok4 = (len(allpos) == 1 and allpos[0][:2] == ('RV', 'idiosyncratic') and round(allpos[0][2], 2) == -0.26
           and round(allpos[0][3], 2) == 0.03 and round(allpos[0][4], 2) == 0.02)
    rec('D5', 'part3 §1b 读法 4「V 的 idiosyncratic 族后段两段小正约 +0.03 / +0.02，但 2010-14 为 −0.26」', '(RV, idiosyncratic, −0.26, +0.03, +0.02)',
        allpos, 'REPRODUCED' if ok4 else 'DIFFERS', tol='印出位数', func='fam_tab')
    # (5) R0：z 最负的三个成员（10-14）
    t0p = rd(os.path.join(RD, TABR0, 'T0_portrait_all.csv'))
    t0a = t0p[t0p.stratum == 'all'].copy()
    t0a['z'] = (t0a.pct_diff_winner_minus_loser - t0a.perm_mean) / t0a.perm_sd
    zz = t0a[t0a.segment == '2010-2014'].groupby('member_id').z.mean().sort_values().head(3)
    v_exact('D5', 'R0「z 最负的三个成员：10-14 R_peervol5（-14.4）、R_resid5（-14.4）、R_peer5（-14.2）」',
            [('R_peervol5', -14.4), ('R_resid5', -14.4), ('R_peer5', -14.2)], [(i, round(v, 1)) for i, v in zz.items()], func='sort')
    # (6) R0 Q3：V 轴分层 IC 为负的成员数
    vs = rd(os.path.join(RD, TABR0, 'Q3_v_strata.csv'))
    cn = vs.groupby(['segment', 'stratum']).agg(neg=('ic_mean', lambda x: int((x < 0).sum())), n=('member_id', 'nunique'))
    mn = cn[cn.index.get_level_values(1) != 'all'].neg.idxmin()
    v_exact('D5', 'R0 Q3「10-14 drift_low 48/49」「各段各层 IC 为负的成员数最少 44 / 49（10-14 range_high）」',
            (48, 49, 44, ('2010-2014', 'range_high')), (int(cn.loc[('2010-2014', 'drift_low'), 'neg']), int(cn.loc[('2010-2014', 'drift_low'), 'n']),
                                                         int(cn.loc[mn, 'neg']), mn), inputs=os.path.join(TABR0, 'Q3_v_strata.csv'), func='groupby')
    # (7) R0 Q12：Spearman 日均最低 0.958（15-18 park10）、排名移动 >5 个百分位的格占比最高 26.5%
    lp = rd(os.path.join(RD, TABR0, 'limit_policy.csv'))
    lm = lp.loc[lp.spearman_obs_vs_ls_daymean.idxmin()]
    v_exact('D5', 'R0 Q12「Spearman 日均最低 0.958（15-18 park10）、排名移动 >5 个百分位的格占比最高 26.5%」', ('0.958', '2015-2018', 'park', 10, '26.5%'),
            ('%.3f' % lm.spearman_obs_vs_ls_daymean, lm.segment, lm.estimator, int(lm.window), '%.1f%%' % (100 * lp.frac_rank_move_gt5pct.max())),
            inputs=os.path.join(TABR0, 'limit_policy.csv'), func='min / max')
    # (8) part3 §3：RL 中等冲击 0 / 4 段为正，最重冲击 3 / 4 段为正
    K_ = rd(os.path.join(RD, 'carried', 'summary', 'C2_children_delta.csv'),
            usecols=['segment', 'route_id', 'd_net8_minus_sqrt_A5_k0.5', 'd_net8_minus_sqrt_A10_k1'])
    rr = K_[K_.route_id == 'RL'].groupby('segment')[['d_net8_minus_sqrt_A5_k0.5', 'd_net8_minus_sqrt_A10_k1']].median()
    v_exact('D5', 'part3 §3「RL 中等冲击（A5 亿 κ.5）下 0 / 4 段为正，最重冲击（A10 亿 κ1）下 3 / 4 段为正」', (0, 4, 3, 4),
            (int((rr['d_net8_minus_sqrt_A5_k0.5'] > 0).sum()), len(rr), int((rr['d_net8_minus_sqrt_A10_k1'] > 0).sum()), len(rr)), func='count',
            note='冲击列为 C2 表层值')
    # (9) part2 Q2 后段：登记的竞争方向（全部强度）两后段中位；主方向完全替换
    kall = X[X.route_id == 'RK']
    cp_ = kall[kall.direction_role == 'competing']
    rp_ = kall[kall.direction_role.isin(PRIM) & kall.policy.isin(['FULL_REPLACE', 'FALLBACK_REPLACE'])]
    cmp_text('D5', 'Q2P-COMP（part2 Q2「登记的竞争方向（全部强度）两后段中位 -1.160 / -1.579」）', qt.get('Q2P-COMP', ''),
             '登记的竞争方向（全部强度）两后段中位 %s / %s；主方向完全替换（α=1）%s / %s' % (
                 f3(cp_.p1.median()), f3(cp_.p2.median()), f3(rp_.p1.median()), f3(rp_.p2.median())),
             os.path.join(TAB2, 'query_ids_part2.csv'))
    # (10) part1 Q13：两规则中位最大差 +0.002
    ra = main_[main_.route_id == 'RA'].copy()
    ra['swap_out'] = np.where(ra.policy.astype(str).str.contains('max_K'), 'max_K', np.where(ra.role == 'SWAP', 'mother_worst', ''))
    zm_ = ra[ra.role == 'SWAP'].groupby(['direction_role', 'swap_out'])[['z1', 'z2']].median()
    dd_ = [np.abs(zm_.xs(dr_, level=0).diff().iloc[1:].values).max() for dr_ in zm_.index.get_level_values(0).unique()
           if len(zm_.xs(dr_, level=0)) == 2]
    v_printed('D5', 'part1 Q13「换出最高 K 与换出母体最差对匹配随机的两规则中位最大差 +0.002」', '+0.002', max(dd_), func='groupby')


# ============================================================ V-E 装配恒等式
def stage_E():
    F, rc = panel()
    # E1 进入 + 退出 + 共同
    rec('E1', '逐日 Δgross = 进入 + 退出 + 共同（从日账本重算三项）', '逐日残差 ≤ 1e−12', None, 'NOT_COMPUTABLE', func='-',
        note='日账本 npz 只存 net8 / gross / pos / turn / dnet8 / dcore / dsamecap（子账户），没有进入 / 退出 / 共同三项与母体 gross；'
             '年化列 attr_* 与 d_gross_ann 的日期掩码不同（attr 为全日均值、Δgross 为两边都有值日），年化层面不是恒等式，不作替代检查')
    mx = {}
    for s in SEGS:
        vals = []
        for p_ in glob.glob(os.path.join(RD, 'accounts', s, 'merged_*.csv')):
            if p_.endswith('merged_index.csv'):
                continue
            try:
                a = rd(p_, usecols=['attr_identity_resid'])
            except ValueError:
                continue
            if len(a):
                vals.append(float(np.nanmax(np.abs(a.attr_identity_resid.values))))
        mx[s] = max(vals) if vals else np.nan
    v_printed('E1', '存档逐描述符残差列 attr_identity_resid 的最大值（推导两段；REPORT part1 §1 印 6.1e−18）', '6.1',
              max(mx[s] for s in DER) * 1e18, func='merged_*.csv', note='表层复核（值是运行时写入的残差，不是本程序从账本重算）；四段最大 %s' % mx)
    # E2 表层 net8 恒等
    for sc in SEGS:
        t = rd(os.path.join(RD, TABLES[sc]), usecols=['descriptor_id', 'd_net8_ann', 'net8_ann', 'parent_net8_ann'])
        r_ = (t.d_net8_ann - (t.net8_ann - t.parent_net8_ann)).abs()
        v_close('E2', '%s 表层 d_net8_ann = net8_ann − parent_net8_ann（全部 %d 描述符）max 残差' % (sc, len(t)), 0.0, float(r_.max()), 1e-12,
                inputs=TABLES[sc], func='identity')
    # E3 四臂交互
    fi = fourarm_recompute()
    tab = pd.concat([rd(os.path.join(RD, 'statistics', 'fourarm_interaction.csv')),
                     rd(os.path.join(RD, 'statistics', 'post', 'fourarm_interaction_post.csv'))], ignore_index=True)
    tab['param'], fi['param'] = tab.param.astype(str), fi.param.astype(str)
    fi['param'] = fi.param.map(lambda x: str(float(x)) if re.fullmatch(r'[0-9.]+', x) else x)
    tab['param'] = tab.param.map(lambda x: str(float(x)) if re.fullmatch(r'[0-9.]+', x) else x)
    cmp_frame('E3', '四臂交互表（推导 216 + 后段 288 行）vs 从日账本重算', fi, tab, ['fourarm', 'mother', 'param', 'H', 'scope'],
              ['interaction_ann', 'interaction_se_nwH', 'd_A_ann', 'd_B_ann', 'd_AB_ann'],
              inputs=['statistics/fourarm_interaction.csv', 'statistics/post/fourarm_interaction_post.csv'])
    res = (tab.interaction_ann - (tab.d_AB_ann - tab.d_A_ann - tab.d_B_ann)).abs()
    v_close('E3', '表内 交互 = Δ_AB − Δ_A − Δ_B 逐行残差 max（%d 行）' % len(tab), 0.0, float(res.max()), 1e-12, func='identity',
            note='交互均值按三臂同时有值日、三臂 Δ 各按自身有值日；三臂掩码一致时两者相等')
    ff = fi[fi.scope == 'full']
    t_ = ff.interaction_ann / ff.interaction_se_nwH
    v_exact('E3', '推导 full |t|>2 / 总（正 / 负）', (12, 72, 8, 4), (int((t_.abs() > 2).sum()), len(ff), int((t_ > 2).sum()), int((t_ < -2).sum())),
            func='count')
    pp = fi[fi.scope == 'post']
    t_ = pp.interaction_ann / pp.interaction_se_nwH
    v_exact('E3', '后段合并 t>2 / t<−2 / 总', (32, 0, 72), (int((t_ > 2).sum()), int((t_ < -2).sum()), len(pp)), func='count')
    # E4 C1 分解
    P = rd(os.path.join(RD, 'carried', 'summary', 'C1_T9_capital_pairs.csv'))
    v_close('E4', 'C1 资本分解 d_deploy = cap_part + sel_part（%d 配对）max 残差' % len(P), 0.0,
            float((P.d_deploy - (P.cap_part + P.sel_part)).abs().max()), 1e-12, inputs='carried/summary/C1_T9_capital_pairs.csv', func='identity')
    v_close('E4', 'C1 d_deploy = net8_b − net8_a max 残差', 0.0, float((P.d_deploy - (P.net8_b - P.net8_a)).abs().max()), 1e-12, func='identity')
    # E5 计数闭合
    a0 = rd(os.path.join(RD, 'registry', 'descriptors_A0.csv'), usecols=lambda c: c in ('descriptor_id', 'route_id'))
    vc = a0.route_id.value_counts()
    v_exact('E5', 'A0 v1.3 = 主 + M1 + M2', (37360, 35384, 1512, 464),
            (len(a0), int(vc.drop(['M1', 'M2'], errors='ignore').sum()), int(vc.get('M1', 0)), int(vc.get('M2', 0))), inputs='registry/descriptors_A0.csv',
            func='value_counts')
    st_ = rd(os.path.join(RD, TABLES['full']), usecols=['descriptor_id', 'route_id'])
    comp = st_.descriptor_id.str.contains(r'\|(?:eqcap|cost_target|winsor)$')
    v_exact('E5', '统计表 39,800 = 主 35,384 + M1 3,024 + M2 1,392', (39800, 35384, 3024, 1392),
            (len(st_), int((~comp & ~st_.route_id.isin(['M1', 'M2'])).sum()), int((st_.route_id == 'M1').sum()), int((st_.route_id == 'M2').sum())),
            func='count', note='伴随账户（eqcap / cost_target / winsor）在主路线中 %d 个' % int((comp & ~st_.route_id.isin(['M1', 'M2'])).sum()))
    M = F[~F.companion & F.route_id.isin(MAIN)]
    rn = M.route_id.value_counts()
    exp_rn = {'FOURARM': 216, 'RA': 3456, 'RC': 1620, 'RK': 4104, 'RL': 360, 'RO': 4644, 'RR': 5328, 'RS': 1656, 'RT': 7216, 'RV': 6624, 'TPAIR': 160}
    v_exact('E5', 'part2 §2 各路线 n（与 brief 列出的 11 个数）', exp_rn, {k_: int(rn.get(k_, 0)) for k_ in exp_rn}, func='value_counts',
            note='和 = %d' % int(rn.sum()))
    der = pd.concat([rd(f) for s in DER for f in glob.glob(os.path.join(RD, 'm2', s, 'ledger_*.csv')) if '_timing' not in f], ignore_index=True)
    pr = der[der.variant == 'primary']
    v_exact('E5', 'M2 primary modified + zero（2010-14 / 2015-18）', (1392, 1856),
            tuple(int(pr[(pr.segment == s) & pr.action.isin(['modified', 'zero_modification'])].shape[0]) for s in DER), func='count')
    # E6 Z-MAP 行闭合
    z = rd(os.path.join(RD, 'statistics', 'zmap_summary_2010-2014.csv'), usecols=['descriptor_id', 'kind'])
    zk = z[z.kind.isin(KINDS)]
    nb = zk.groupby('kind').descriptor_id.nunique()
    v_exact('E6', '104,856 = 3 机制 x 34,952 描述符', (104856, 34952, 34952, 34952), (len(zk), int(nb.get('basic', 0)), int(nb.get('industry', 0)),
                                                                                    int(nb.get('persist20', 0))), func='groupby')
    miss = M[~M.descriptor_id.isin(set(zk[zk.kind == 'basic'].descriptor_id))]
    br_ = miss.groupby(['route_id', 'role']).size().to_dict()
    v_exact('E6', '无随机对照的主描述符个数', 432, len(miss), func='set difference')
    v_exact('E6', '无随机对照的 432 个的构成（brief 预期 FOURARM 216 + TPAIR 160 + 56 个其他）',
            {('FOURARM', 'FOURARM'): 216, ('TPAIR', '*'): 160, ('其他', '*'): 56},
            {('%s' % k_[0], '%s' % k_[1]): int(v_) for k_, v_ in br_.items()}, func='groupby',
            note='实际：%s；TPAIR 160 个在 Z-MAP 里有 basic 行（part2 §4 表 TPAIR 真实−随机 有值）' % br_)
    miss[['descriptor_id', 'route_id', 'role', 'direction_role']].to_csv(os.path.join(VD, 'E6_no_random_control.csv'), index=False)
    t4 = rd(os.path.join(RD, TAB2, 'T4_mechanism_post.csv')).set_index('route')
    has = {rt: bool(np.isfinite(t4.loc[rt, '19-2023 真实−随机'])) for rt in ('FOURARM', 'TPAIR')}
    v_exact('E6', 'part2 §4 表头括注「FOURARM / TPAIR 等确定性臂无随机对照」vs T4 表（真实−随机 是否有值）',
            {'FOURARM': False, 'TPAIR': False}, has, inputs=os.path.join(TAB2, 'T4_mechanism_post.csv'), func='isfinite',
            note='T4 TPAIR 行 真实−随机 %.3f / %.3f' % (t4.loc['TPAIR', '19-2023 真实−随机'], t4.loc['TPAIR', '24-2026 真实−随机']))


# ============================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True)
    ap.add_argument('--part', default=None)
    a = ap.parse_args()
    os.makedirs(VD, exist_ok=True)
    log('开始 stage=%s；程序 sha256 %s' % (a.stage, sha256(os.path.abspath(__file__))[:16]))
    if a.stage == 'gate':
        transcribe_probes()
        closure_gate('pre_V')
    elif a.stage == 'gate_post':                 # V 完成、VERIFY 交付物 push 之后
        write_postverify_fingerprint()
        closure_gate('post_V')
    elif a.stage == 'A':
        stage_A()
        flush_results('A')
    elif a.stage == 'C0':
        stage_C0()
        flush_results('C0')
    elif a.stage == 'C':
        stage_C()
        flush_results('C')
    elif a.stage == 'D':
        stage_D()
        flush_results('D')
    elif a.stage == 'E':
        stage_E()
        flush_results('E')
    elif a.stage == 'B':
        stage_B(a.part or 'all')
        flush_results('B' if (a.part or 'all') == 'all' else 'B_' + a.part)
    assert_no_e6i()


if __name__ == '__main__':
    main()
