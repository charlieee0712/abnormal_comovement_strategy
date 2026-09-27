# -*- coding: utf-8 -*-
"""E6j 只读复核程序（VERIFY brief v1 §5；执行端 V）。
不 import 任何 e6j_* 模块，不复用本轮进程状态，不读 cache/ 作答案，不读 E7（> 2026-03-27）行情，不改结果目录已有文件。
输入：结果目录只读 + E5a / E6i 目录只读 + verify/decision/ 三件。输出：verify/probes.csv、probe_results.csv、verify.log（本程序另存 sha）。
判定：REPRODUCED / DIFFERS / NOT_COMPUTABLE（附 ROUNDING / STOCHASTIC / INFO）。DIFFERS 不修，E 项另写。
用法：python3 verify_e6j_readonly.py [--only VA,VB,...]"""
import os
import re
import sys
import json
import glob
import time
import hashlib
import datetime

import numpy as np
import pandas as pd

RES = '/mnt/sda2/lichenchen/results/20260927_0038_E6j_k_two_dimension_pilot'
CODE = '/mnt/sda2/lichenchen/code/project_core'
E5A = '/mnt/sda2/lichenchen/results/20260903_1214_delivery_pools_v2'
E6I = '/mnt/sda2/lichenchen/results/20260923_0254_E6i_measurement_need_fit'
VER = os.path.join(RES, 'verify')
SEGS = ['2010-2014', '2015-2018', '2019-2023', '2024-2026']
POST = SEGS[2:]
FORMS = ['A4b', 'M_mean3_v2', 'M_union3_v2', 'A4b_CVRv5', 'M_mean3_v2_CVRv5', 'M_union3_v2_CVRv5']
ARMS = ['S', 'M', 'SM', 'C1']
ANN = 252 * 100.0
ONLY = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None

OUT = []           # 结果行
LOG = []


def log(m):
    s = '[%s] %s' % (time.strftime('%H:%M:%S'), m); LOG.append(s); print(s, flush=True)


def P(*p):
    return os.path.join(RES, *p)


_SHA = {}


def sha(path, algo='sha256'):
    k = (path, algo)
    if k not in _SHA:
        h = hashlib.new(algo)
        with open(path, 'rb') as f:
            for b in iter(lambda: f.read(1 << 22), b''):
                h.update(b)
        _SHA[k] = h.hexdigest()
    return _SHA[k]


def mtime(path):
    return datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')


def jload(path):
    return json.load(open(path, encoding='utf-8'))


# ------------------------------------------------------------------ 比较
def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _parse(s):
    """字符串 → json / 数 / ' / ' 复合 / 原串。"""
    if not isinstance(s, str):
        return s
    t = s.strip()
    if t in ('True', 'False'):
        return t == 'True'
    try:
        return json.loads(t)
    except Exception:
        pass
    v = _num(t)
    if v is not None:
        return v
    if ' / ' in t:
        return ['__composite__'] + [_parse(x) for x in t.split(' / ')]
    return t


def _decimals(lit):
    m = re.fullmatch(r'-?\d+\.(\d+)', str(lit).strip())
    return len(m.group(1)) if m else None


def _norm(v):
    return json.loads(json.dumps(v, default=lambda o: o.item() if hasattr(o, 'item') else str(o)))


def _cmp(e, m, tol, path='', lit=None):
    """返回 (ok, maxdiff, rounding, 说明)。"""
    if isinstance(e, bool) or isinstance(m, bool):
        return (bool(e) == bool(m) and type(e) == type(m)) or (str(e) == str(m)), 0.0, False, '' if e == m else '%s: %r vs %r' % (path, e, m)
    if isinstance(e, (int, float)) and isinstance(m, (int, float)):
        if (isinstance(e, float) and np.isnan(e)) or (isinstance(m, float) and np.isnan(m)):
            ok = (isinstance(e, float) and np.isnan(e)) and (isinstance(m, float) and np.isnan(m))
            return ok, 0.0, False, '' if ok else '%s: NaN 不对应' % path
        d = abs(float(e) - float(m))
        if d <= tol:
            return True, d, False, ''
        dec = _decimals(lit if lit is not None else repr(e))
        if dec is not None and dec <= 6 and d <= 0.5 * 10 ** (-dec) + 1e-12:
            return True, d, True, ''
        return False, d, False, '%s: 预期 %r 重算 %r 差 %.3g' % (path, e, m, d)
    if isinstance(e, dict) and isinstance(m, dict):
        if set(map(str, e)) != set(map(str, m)):
            return False, np.inf, False, '%s: 键不同 %s vs %s' % (path, sorted(map(str, e))[:8], sorted(map(str, m))[:8])
        mm = {str(k): v for k, v in m.items()}
        res = [_cmp(v, mm[str(k)], tol, '%s.%s' % (path, k)) for k, v in e.items()]
        return all(r[0] for r in res), max([r[1] for r in res] + [0.0]), any(r[2] for r in res), '; '.join(r[3] for r in res if r[3])[:600]
    if isinstance(e, list) and isinstance(m, list):
        if len(e) != len(m):
            return False, np.inf, False, '%s: 长度 %d vs %d' % (path, len(e), len(m))
        res = [_cmp(a, b, tol, '%s[%d]' % (path, i)) for i, (a, b) in enumerate(zip(e, m))]
        return all(r[0] for r in res), max([r[1] for r in res] + [0.0]), any(r[2] for r in res), '; '.join(r[3] for r in res if r[3])[:600]
    if e is None or m is None:
        ok = (e is None and m is None) or (e is None and isinstance(m, float) and np.isnan(m)) or (m is None and isinstance(e, float) and np.isnan(e))
        return ok, 0.0, False, '' if ok else '%s: %r vs %r' % (path, e, m)
    ok = str(e).strip() == str(m).strip()
    return ok, 0.0 if ok else np.inf, False, '' if ok else '%s: %r vs %r' % (path, str(e)[:120], str(m)[:120])


def _tol(t):
    t = str(t)
    m = re.search(r'(\d+(?:\.\d+)?e-?\d+)', t)
    return float(m.group(1)) if m else (5e-4 if t.startswith('5e') else 1e-12)


def record(probe, sub, expected, mine, tol='exact', inputs='', func='', flags='', note=''):
    """mine 可为原生对象或字符串；expected 为预期表字符串（现算探针传 None 表示无预期）。"""
    tolv = _tol(tol)
    if expected is None or (isinstance(expected, float) and np.isnan(expected)):
        verdict = 'NOT_COMPUTABLE' if mine is None else 'REPRODUCED'
        OUT.append(dict(probe_id=probe, sub_id=sub, expected='', recomputed=_short(mine), diff='', verdict=verdict, flags=flags,
                        note=note, inputs=inputs, function=func))
        return verdict
    if mine is None:
        OUT.append(dict(probe_id=probe, sub_id=sub, expected=str(expected)[:400], recomputed='', diff='', verdict='NOT_COMPUTABLE', flags=flags,
                        note=note, inputs=inputs, function=func))
        return 'NOT_COMPUTABLE'
    e = _parse(expected)
    m = _parse(mine) if isinstance(mine, str) else _norm(mine)
    if isinstance(e, list) and e and e[0] == '__composite__':
        if not (isinstance(m, list) and m and m[0] == '__composite__'):
            m = ['__composite__'] + (m if isinstance(m, list) else [m])
        e, m = e[1:], m[1:]
    ok, d, rnd, why = _cmp(e, m, tolv, lit=str(expected))
    verdict = 'REPRODUCED' if ok else 'DIFFERS'
    fl = ','.join(x for x in [flags, 'ROUNDING' if (ok and rnd) else ''] if x)
    OUT.append(dict(probe_id=probe, sub_id=sub, expected=str(expected)[:400], recomputed=_short(mine), diff=('' if d in (0.0,) else '%.3g' % d) if np.isfinite(d) else 'n/a',
                    verdict=verdict, flags=fl, note=(note + (' | ' + why if why else ''))[:900], inputs=inputs, function=func))
    return verdict


def _short(v):
    if isinstance(v, str):
        return v[:400]
    try:
        return json.dumps(_norm(v), ensure_ascii=False)[:400]
    except Exception:
        return str(v)[:400]


EXP = pd.read_csv(os.path.join(VER, 'decision', 'E6j_VERIFY_expected.csv'), encoding='utf-8-sig', dtype=str)


def rows(pid):
    return EXP[EXP.probe_id == pid]


def exp(pid, sub):
    r = EXP[(EXP.probe_id == pid) & (EXP.sub_id == sub)]
    return (r.expected.iloc[0], r.tol.iloc[0]) if len(r) else (None, 'exact')


def rec(pid, sub, mine, **kw):
    e, t = exp(pid, sub)
    return record(pid, sub, e, mine, tol=kw.pop('tol', t), **kw)


def vc(s):
    """value_counts → dict（键转字符串）。"""
    return {str(k): int(v) for k, v in pd.Series(s).value_counts(dropna=False).items()}


# ================================================================== V-A
def VA():
    names = ['E6j_REPORT_R0.md', 'E6j_REPORT_part1.md', 'E6j_REPORT_part1b.md', 'E6j_REPORT_part2.md', 'E6j_REPORT_part3.md', 'E6j_REPORT_carried.md',
             'E6j_REVIEW_input.md', 'E6j_delivery_addendum_1.md', 'E6j_lessons_delta.md', 'E6j_record_B_draft.md', 'routing_review_A1_auto.md']
    mirror = open(os.path.join(CODE, 'exec_briefs', 'E6j_MIRROR.md5'), encoding='utf-8').read()
    for _, r in rows('VA01').iterrows():
        f = P(r.object)
        algo = 'md5' if r.sub_id.endswith('|md5') else 'sha256'
        record('VA01', r.sub_id, r.expected, sha(f, algo), r.tol, inputs=r.object, func='sha')
    for n in names:                                        # 附加：47 exec_briefs 镜像与 MIRROR 行
        eb = os.path.join(CODE, 'exec_briefs', n if n.startswith('E6j_') else 'E6j_' + n)
        s = sha(P('reports', n))
        ok = os.path.exists(eb) and sha(eb) == s and (s in mirror)
        record('VA01', n + '|mirror', 'True', str(ok), inputs='exec_briefs + E6j_MIRROR.md5', func='mirror_check', flags='ADDED')
    for _, r in rows('VA02').iterrows():
        obj = r.object
        cand = [P(obj), os.path.join(CODE, obj)]
        f = next((c for c in cand if os.path.isfile(c)), None)
        record('VA02', r.sub_id, r.expected, sha(f)[:16] if f else None, r.tol, inputs=obj, func='sha256[:16]',
               note='' if f else '文件不存在')
    # VA03
    reg = jload(P('reports', 'query_registry.json'))
    rec('VA03', 'query_registry', len(reg), inputs='reports/query_registry.json', func='len')
    pre = {}
    for q in reg:
        pre[q.split('-Q')[0]] = pre.get(q.split('-Q')[0], 0) + 1
    for k, v in pre.items():
        rec('VA03', 'prefix_%s' % k, v, func='count prefix')
    for n in names[:6]:
        txt = open(P('reports', n), encoding='utf-8').read()
        inq = set(re.findall(r'query_id=([A-Z0-9]+-Q\d+)', txt))
        rg = {q for q, v in reg.items() if v['file'] == n}
        rec('VA03', n, '%d / %d' % (len(inq), len(rg)), func='header query_id vs registry',
            note='' if inq == rg else '集合不等：仅正文 %s 仅登记 %s' % (sorted(inq - rg), sorted(rg - inq)))
    # VA04
    recs = {}
    for f in glob.glob(P('task_status', '*.json')):
        recs[os.path.basename(f).replace('.receipt.json', '')] = jload(f)
    st = vc([v['status'] for v in recs.values()])
    rec('VA04', 'receipts', '%d / %s' % (len(recs), json.dumps(st)), func='count status')
    fails = [k for k, v in recs.items() if v['status'] != 'SUCCEEDED']
    cov = all((k + '_rerun') in recs and recs[k + '_rerun']['status'] == 'SUCCEEDED' for k in fails)
    rec('VA04', 'failed_stage0_anchor1_prod_path', str(cov) if fails == ['stage0_anchor1_prod_path'] else 'False', func='rerun cover',
        note='FAILED=%s' % fails)
    late = sorted([[v.get('written_at'), k] for k, v in recs.items() if str(v.get('written_at', '')) >= '2026-09-27 20:47:00'])
    rec('VA04', 'late_receipts', late, func='written_at ≥ 20:47:00',
        note='REVIEW_input 在自身回执与 closure_gate 回执写出前计数 → 1,079；closure_gate 在自身回执前计数 → 1,080；实物 1,081')
    # VA05
    for nm in ('seal_P', 'seal_B_post'):
        s = jload(P('registration', nm + '.json'))
        rec('VA05', nm, '%s / %d / %d/%d / %s / %s' % (s['sealed_at'], len(s['files']), s['receipts_base'], s['receipts_base_expected'],
                                                   s['all_succeeded'], json.dumps(s['previous_versions'])), func='seal fields')
        bad = sum(1 for f, h in s['files'].items() if not os.path.exists(P(f)) or sha(P(f)) != h)
        present = sum(1 for f in s['files'] if os.path.exists(P(f)))
        rec('VA05', nm + '_recheck', '%d / %d' % (present, bad), func='sha256 recompute', inputs='%d files' % len(s['files']))
    # VA06
    seals = {'P': jload(P('registration', 'seal_P.json'))['sealed_at'], 'B': jload(P('registration', 'seal_B_post.json'))['sealed_at']}
    for _, r in rows('VA06').iterrows():
        f = P(r.source)
        mt = mtime(f) if os.path.exists(f) else None
        req = str(r.formula)
        fl, note = '', ''
        m = re.search(r'须 > (?:seal_P |seal_B_post )?(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)', req)
        if m and mt:
            note = 'order %s' % ('OK' if mt > m.group(1) else 'VIOLATED')
            if mt <= m.group(1):
                fl = 'ORDER_FAIL'
        if '只含推导段' in req:
            fl = 'INFO'
        record('VA06', r.sub_id, r.expected, mt, inputs=r.source, func='mtime', flags=fl, note=note)
    # VA07
    pa = jload(P('registration', 'policy_P_operational_addendum.json'))
    st0 = {k: pa['state_at_write'][k] for k in ('seal_P_exists', 'policy_final_exists', 'randoms_P_exists', 'run_prand_receipts',
                                                  'first_run_prand_receipt_mtime')}
    rec('VA07', 'policy_addendum', '%s / %s' % (pa['written_at'], json.dumps(st0)), func='addendum fields',
        note='written_at < seal_P %s：%s' % (seals['P'], pa['written_at'] < seals['P']))
    rp = sorted(v['written_at'] for k, v in recs.items() if k.startswith('run_prand_'))
    rec('VA07', 'first_run_prand_receipt', rp[0], func='min written_at', note='addendum < first run_prand：%s' % (pa['written_at'] < rp[0]))
    rb = jload(P('registration', 'record_B_conditions_receipt.json'))
    rec('VA07', 'record_B_receipt', '%s / %s / %s' % (rb['checked_at'], rb['all_pass'], rb['frozen_manifest_sha256'] == rb['current_manifest_sha256']))
    rec('VA07', 'B_manifest_sha_now', sha(P('registration', 'B_package_manifest.json')), note='== frozen：%s' % (
        sha(P('registration', 'B_package_manifest.json')) == rb['frozen_manifest_sha256']))
    rbp = sorted(v['written_at'] for k, v in recs.items() if k.startswith(('run_b_2019-2023', 'run_b_2024-2026')))
    rec('VA07', 'first_B_post_account_receipt', rbp[0], note='> record_B %s：%s' % (rb['checked_at'], rbp[0] > rb['checked_at']))
    pr = jload(P('registration', 'record_B_preauthorized_E6j.json'))
    rec('VA07', 'preauth', '%s / %s / %s / %s' % (pr['written_at'], pr['user_quote'], pr['source_sha256'][:8], pr['frozen_manifest_sha256'][:16]))
    ca = jload(P('registration', 'code_amendment_20260927_fast.json'))
    rec('VA07', 'code_amendment', '%s / %s / %d' % (ca['written_at'], ca['deployed_at'], len(ca['p_tasks_finished_with_old_code_at_write'])))
    for _, r in rows('VA07').iterrows():
        if r.sub_id.startswith('code_changes/'):
            record('VA07', r.sub_id, r.expected, sha(P(r.source)), inputs=r.source, func='sha256',
                   note='amendment 记 %s' % ca['files'].get(r.sub_id.replace('code_changes/', ''), '')[:16])
        elif r.sub_id.endswith('.csv'):
            record('VA07', r.sub_id, r.expected, vc(pd.read_csv(P(r.source)).status), inputs=r.source, func='status counts')
    # VA08
    for _, r in rows('VA08').iterrows():
        if r.sub_id.startswith('dryrun/'):
            f = P('results_P', r.sub_id)
            record('VA08', r.sub_id, r.expected, '%s / %s' % (sha(f)[:16], mtime(f)), inputs=r.sub_id, func='sha/mtime')
    d = pd.read_csv(P('results_P', 'dryrun', 'pilot_policy.csv'))
    rec('VA08', 'dryrun_e_rand', vc(d.e_rand.astype(str)), func='value_counts')
    # VA09
    cg = pd.read_csv(P('checks', 'closure_gate.csv'))
    rec('VA09', 'closure_gate', '%s / %d' % (json.dumps(vc(cg.status)), len(cg)))
    a1 = jload(P('registration', 'a1_auto.json'))
    items = a1['items'] if isinstance(a1['items'], list) else json.loads(a1['items'])
    rec('VA09', 'a1_auto', [i['status'] for i in items])
    sm = jload(P('source_manifest.json'))
    rec('VA09', 'source_manifest', '%s / %s / %s / %s' % (sm['git_head'][:7], sm['stage0_all_pass'], json.dumps(sm['anchor_results']), sm['market_data_end_max']))
    for nm in ('P_package_manifest.json', 'B_package_manifest.json'):
        m = jload(P('registration', nm))
        rec('VA09', nm, '%s / %s / %s / %s' % (m['written_at'], m['git_head'][:7], json.dumps(m['counts']), json.dumps(m['policy_locks'])))
    # VA10（现场；执行端开工时的观察 + 文件时间）
    first = sorted(mtime(f) for f in glob.glob(os.path.join(VER, '**', '*'), recursive=True) if os.path.isfile(f))
    record('VA10', 'verify_dir_at_delivery', None, 'verify/ 最早文件 %s（decision 三件入库，C-8）> closure_gate 20:48:07；执行端开工身份核对时 verify/ 为空、results_P/supplement_1 不存在（WORKLOG）' % (first[0] if first else '无'),
           func='observation', flags='INFO')


# ================================================================== V-B
def VB():
    ar = pd.read_csv(P('anchor_results.csv'))
    rec('VB01', 'anchor_results', '%d / %s' % (len(ar), json.dumps(vc(ar.status))))
    piv = {s: {str(i): int(((ar.status == s) & (ar.stage0_item == i)).sum()) for i in sorted(ar.stage0_item.unique())} for s in sorted(ar.status.unique())}
    rec('VB01', 'anchor_by_item', piv)
    rec('VB01', 'anchor_DIFFERS', ar[ar.status == 'DIFFERS'][['check_id', 'object', 'metric']].to_dict('records'))
    a1 = pd.read_csv(P('stage0', 'anchor1_rerun', 'anchor1_results.csv'))
    rec('VB02', 'anchor1_rerun', '%d / %s' % (len(a1), json.dumps(vc(a1.status))))
    for _, r in rows('VB02').iterrows():
        if r.sub_id.startswith('E5a/'):
            record('VB02', r.sub_id, r.expected, sha(os.path.join(E5A, r.sub_id[4:])), inputs=r.sub_id, func='sha256')
        elif r.sub_id.endswith('|rows'):
            fn = r.sub_id.split('|')[0]
            with open(os.path.join(E5A, fn), 'rb') as f:
                n = sum(1 for _ in f) - 1
            record('VB02', r.sub_id, r.expected, n, inputs=fn, func='line count − header')
    man = jload(P('stage0', 'anchor1_rerun', 'anchor1_manifest.json'))
    e5 = man.get('e5a_sha256', {})
    bad = [k for k, v in e5.items() if os.path.exists(os.path.join(E5A, k)) and sha(os.path.join(E5A, k)) != v]
    record('VB02', 'anchor1_manifest_e5a_sha', 'True', str(len(e5) == 10 and not bad), func='manifest vs file', flags='ADDED', note='%d 项；不符 %s' % (len(e5), bad))
    # VB03
    ld = pd.read_csv(P('carried', 'leader_six_forms_capital.csv'))
    e5s = pd.read_csv(os.path.join(E5A, 'summary.csv')).rename(columns={'period': 'segment', 'cfg': 'form'})
    fmap = {'A4b': 'A4b', 'M_mean3_v2': 'M_mean3_v2', 'M_union3_v2': 'M_union3_v2', 'A4b_CVRv5': 'A4b_CVRv5', 'M_mean3_v2_CVRv5': 'M_mean3_v2_CVRv5',
            'M_union3_v2_CVRv5': 'M_union3_v2_CVRv5'}
    j = ld.merge(e5s, on=['segment', 'form'], how='inner')
    pairs = {'total_net6_ann': 'net_ann', 'total_gross_ann': 'gross_ann', 'turnover_ann': 'turn', 'target_names_mean': 'avg_nh', 'invested_target_mean': 'avg_pos'}
    rec('VB03', 'leader_vs_E5a', {k: float((j[k] - j[v]).abs().max()) for k, v in pairs.items()}, inputs='carried/leader + E5a summary (%d 行配对)' % len(j))
    a = ld[ld.form == 'A4b_CVRv5'].set_index('segment').total_net8_ann
    rec('VB03', 'A4b_CVRv5_net8', {s: round(float(a[s]), 4) for s in SEGS})
    # VB04
    im = pd.read_csv(P('stage0', 'anchor2_rerun', 'parent_identity_map_rerun.csv'))
    r0 = im.iloc[0]
    rec('VB04', 'identity_rerun', '%s / %s / %s / %s / %s' % (r0.classification, bool(im.L1_mask_exact.all()), float(im.L2_max_abs.max()),
                                                          float(im.L3_max_abs.max()), float(im.L4_max_abs.max())))
    rec('VB04', 'identity_root', float(pd.read_csv(P('parent_identity_map.csv')).L4_max_abs.max()), flags='INFO', note='首跑汇总伪值（R0 已注）')
    od = pd.read_csv(P('operator_discrepancy_manifest.csv'))
    rec('VB04', 'operator_discrepancy', '%d / %s / %s' % (len(od), json.dumps(vc(od.verdict), ensure_ascii=True), float(od.mask_cells_differ.max())))
    pa = pd.read_csv(P('stage0', 'anchor2_rerun', 'e6i_parent_anchor.csv'))
    rec('VB04', 'e6i_parent_anchor', '%s / %s / %s' % (str(pa.shape), str(list(pa.columns)), json.dumps({'max_abs_daily': float(pa.max_abs_daily.max())})))
    # VB05
    for _, r in rows('VB05').iterrows():
        if r.sub_id == 'plan_tests':
            tj = jload(P('stage0', 'plan_tests', 'test_results.json'))
            vals = tj if isinstance(tj, list) else tj.get('results', tj)
            if isinstance(vals, dict):
                vals = list(vals.values())
            st = [str(v.get('status', v) if isinstance(v, dict) else v) for v in vals]
            record('VB05', 'plan_tests', r.expected, '%d / %d' % (len(st), sum(s == 'PASS' for s in st)), inputs='stage0/plan_tests/test_results.json')
        else:
            x = pd.read_csv(P(r.sub_id))
            record('VB05', r.sub_id, r.expected, '%d / %s' % (len(x), json.dumps(vc(x.status))), inputs=r.sub_id)


# ================================================================== 账本工具
_ACC = {}


def acc(seg, form):
    k = (seg, form)
    if k not in _ACC:
        z = np.load(P('accounts', 'P', seg, form + '.npz'), allow_pickle=False)
        _ACC[k] = ({str(d): i for i, d in enumerate(z['desc'])}, {f: z[f] for f in z.files if f not in ('desc',)})
    return _ACC[k]


def did(form, arm, a, H):
    if arm == 'C0':
        return 'P|%s|C0|-|-|a=0|H%d' % (form, H)
    return None


def find_desc(form, arm, a, H, seg):
    ix, _ = acc(seg, form)
    if arm == 'C0':
        key = [d for d in ix if d.startswith('P|%s|C0|' % form) and d.endswith('|H%d' % H)]
    elif arm.startswith('COL:'):
        key = [d for d in ix if d.startswith('P|%s|COL|%s|' % (form, arm[4:])) and d.endswith('|a=%s|H%d' % (a, H))]
    else:
        key = [d for d in ix if d.startswith('P|%s|%s|' % (form, arm)) and d.endswith('|a=%s|H%d' % (a, H))]
    assert len(key) == 1, (form, arm, a, H, seg, key[:3])
    return ix[key[0]]


def series(seg, form, arm, a, H, field):
    _, z = acc(seg, form)
    return z[field][find_desc(form, arm, a, H, seg)]


def paired(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    return np.where(m, x - y, np.nan)


def segD(d):
    m = np.isfinite(d)
    return float(d[m].mean() * ANN) if m.any() else np.nan, int(m.sum())


def hac(d, L):
    I = np.isfinite(d); n = int(I.sum())
    mu = d[I].mean(); u = np.where(I, d - mu, 0.0)
    s = float(u @ u)
    for l in range(1, int(L) + 1):
        s += 2.0 * (1.0 - l / (L + 1.0)) * float(u[l:] @ u[:-l])
    return np.sqrt(s / n / n)


# ================================================================== V-C
def my_verdicts(pp):
    """addendum V-1..V-5 / MC-5 独立实现（不 import e6j_policy_p）。"""
    out = {}
    D = lambda r, s: r['D_%s' % s]
    for i, r in pp.iterrows():
        if r.arm not in ARMS:
            out[i] = ('列对象（不评分）', '列对象（不评分）'); continue
        # e-随机
        sts = []
        for s in POST:
            dd, se = r['rand_IID_%s' % s], r['mcse_IID_%s' % s]
            if not (np.isfinite(dd) and np.isfinite(se)):
                sts.append('NA')
            elif dd > 0 and dd >= 2 * se:
                sts.append('POS')
            elif dd <= 0 and -dd >= 2 * se:
                sts.append('NONPOS')
            else:
                sts.append('UNRES')
        er = 'FAIL' if 'NONPOS' in sts else 'PASS' if all(x == 'POS' for x in sts) else 'NA' if 'NA' in sts else 'MC_UNRESOLVED'
        gaps = [r['size_gap_pctpt_%s' % s] for s in SEGS]
        size_fail = any(np.isfinite(g) and g > 5.0 for g in gaps)
        res = []
        for prof in ('FULL', 'G4'):
            c = all(np.isfinite(D(r, s)) and D(r, s) >= -0.10 for s in SEGS)
            f = all(np.isfinite(r['Dimp_%s' % s]) and r['Dimp_%s' % s] >= -0.10 for s in SEGS)
            d = r.years_pos >= 12
            pos = r[prof] >= 0.10
            sgn = lambda x: np.nan if not np.isfinite(x) else (0.0 if abs(x) <= 1e-9 else np.sign(x))
            a, b = sgn(r[prof]), sgn(r[prof + '_sc'])
            ecap = 'NA' if (np.isnan(a) or np.isnan(b)) else ('PASS' if a == b else 'FAIL')
            fails, pend = [], []
            for nm, ok in (('c', c), ('d', d), ('f', f), ('正向门槛', pos)):
                if not ok:
                    fails.append(nm)
            for nm, s_ in (('e资本', ecap), ('e随机', er)):
                if s_ == 'FAIL':
                    fails.append(nm)
                elif s_ != 'PASS':
                    pend.append('%s:%s' % (nm, s_))
            if size_fail:
                fails.append('市值通道')
            res.append('不通过（%s）' % '、'.join(fails) if fails else ('不可判（%s）' % '、'.join(pend) if pend else '通过'))
        out[i] = tuple(res)
    return out


def VC():
    pp = pd.read_csv(P('results_P', 'pilot_policy.csv'))
    main = pp[pp.main_config & pp.arm.isin(ARMS)]; grid = pp[pp.arm.isin(ARMS)]
    rec('VC01', 'pilot_policy', '%s / %d / %s' % (str(pp.shape), int(pp.main_config.sum()), json.dumps(vc(pp.arm), ensure_ascii=False)))
    rec('VC01', 'policy_FULL_all504', vc(pp.policy_FULL)); rec('VC01', 'policy_G4_all504', vc(pp.policy_G4))
    rec('VC01', 'policy_FULL_main24', vc(main.policy_FULL)); rec('VC01', 'policy_FULL_grid288', vc(grid.policy_FULL))
    rec('VC01', 'size_status', '%s / %s / %s' % (json.dumps(vc(main.size_status)), json.dumps(vc(grid.size_status)), json.dumps(vc(pp.size_status))))
    # VC02
    Dm = np.stack([pp['D_%s' % s] for s in SEGS], 1); Nm = np.stack([pp['n_%s' % s] for s in SEGS], 1)
    rec('VC02', 'FULL_identity', float(np.nanmax(np.abs((Dm * Nm).sum(1) / Nm.sum(1) - pp.FULL))))
    rec('VC02', 'G4_identity', float(np.nanmax(np.abs(np.median(Dm, 1) - pp.G4))))
    for col, pre in (('FULL_sc', 'Dsc'), ('FULL_imp', 'Dimp')):
        X = np.stack([pp['%s_%s' % (pre, s)] for s in SEGS], 1)
        rec('VC02', col + '_identity', float(np.nanmax(np.abs((X * Nm).sum(1) / Nm.sum(1) - pp[col]))))
    Y = np.stack([pp['Y%d' % y] for y in range(2010, 2027)], 1)
    rec('VC02', 'years_n', sorted(set(int(v) for v in pp.years_n.dropna())), note='years_pos 恒等 max 差 %d' % int(np.nanmax(np.abs((Y > 0).sum(1) - pp.years_pos))))
    # VC03
    mv = my_verdicts(pp)
    f_mis = sum(mv[i][0] != pp.policy_FULL[i] for i in pp.index); g_mis = sum(mv[i][1] != pp.policy_G4[i] for i in pp.index)
    rec('VC03', 'policy_FULL_reproduction', f_mis, func='my_verdicts'); rec('VC03', 'policy_G4_reproduction', g_mis, func='my_verdicts')
    def mis(col, fn):
        return int(sum(bool(fn(r)) != bool(r[col]) for _, r in grid.iterrows()))
    for dl, tag in ((0.10, 'd10'), (0.05, 'd05'), (0.15, 'd15')):
        rec('VC03', 'c_FULL_' + tag, mis('c_FULL_' + tag, lambda r: all(r['D_%s' % s] >= -dl for s in SEGS)))
    rec('VC03', 'f_FULL_d10', mis('f_FULL_d10', lambda r: all(r['Dimp_%s' % s] >= -0.10 for s in SEGS)))
    rec('VC03', 'd_ok', mis('d_ok', lambda r: r.years_pos >= 12))
    rec('VC03', 'positive_FULL', mis('positive_FULL', lambda r: r.FULL >= 0.10)); rec('VC03', 'positive_G4', mis('positive_G4', lambda r: r.G4 >= 0.10))
    rec('VC03', 'size_status', int(sum((any(r['size_gap_pctpt_%s' % s] > 5 for s in SEGS if np.isfinite(r['size_gap_pctpt_%s' % s])) != (r.size_status == 'FAIL'))
                                      for _, r in grid.iterrows())))
    sgn = lambda x: 0.0 if abs(x) <= 1e-9 else np.sign(x)
    rec('VC03', 'e_cap_FULL', int(sum(((sgn(r.FULL) == sgn(r.FULL_sc)) != (r.e_cap_FULL == 'PASS')) for _, r in grid.iterrows())))
    er_mine = []
    for _, r in grid.iterrows():
        sts = []
        for s in POST:
            dd, se = r['rand_IID_%s' % s], r['mcse_IID_%s' % s]
            sts.append('POS' if (dd > 0 and dd >= 2 * se) else 'NONPOS' if (dd <= 0 and -dd >= 2 * se) else 'UNRES')
        er_mine.append('FAIL' if 'NONPOS' in sts else 'PASS' if all(x == 'POS' for x in sts) else 'MC_UNRESOLVED')
    rec('VC03', 'e_rand_reproduction', int(sum(a != b for a, b in zip(er_mine, grid.e_rand))))
    # VC04 三句加法
    ad = pd.read_csv(P('results_P', 'pilot_policy_additions.csv'))
    rec('VC04', 'additions', ad.to_dict('records'))
    mine = []
    for form in FORMS:
        m = main[main.form == form].set_index('arm')
        for prof in ('FULL', 'G4'):
            ok = lambda a: a in m.index and m.loc[a, 'policy_' + prof] == '通过'
            elig = [a for a in ('C1', 'M', 'S') if ok(a)]
            best = sorted(elig, key=lambda a: (-m.loc[a, prof], ('C1', 'M', 'S').index(a)))[0] if elig else None
            chosen = None
            if 'C1' in elig:
                chosen = 'C1'; beat = []
                for a in ('M', 'S'):
                    if a in elig:
                        dseg = np.array([m.loc[a, 'D_%s' % s] - m.loc['C1', 'D_%s' % s] for s in SEGS])
                        n = np.array([m.loc[a, 'n_%s' % s] for s in SEGS], float)
                        md = (dseg * n).sum() / n.sum() if prof == 'FULL' else float(np.median(dseg))
                        if (dseg >= 0.05).sum() >= 3 and md >= 0.05:
                            beat.append((md, a))
                if beat:
                    chosen = sorted(beat, key=lambda x: (-x[0], ('M', 'S').index(x[1])))[0][1]
            elif elig:
                chosen = best
            if ok('SM'):
                if best is None:
                    chosen = 'SM'
                else:
                    dseg = np.array([m.loc['SM', 'D_%s' % s] - m.loc[best, 'D_%s' % s] for s in SEGS]); n = np.array([m.loc['SM', 'n_%s' % s] for s in SEGS], float)
                    md = (dseg * n).sum() / n.sum() if prof == 'FULL' else float(np.median(dseg))
                    if md >= 0.10:
                        chosen = 'SM'
            mine.append(chosen or '无')
    rec('VC04', 'additions_reproduction', int(sum(a != b for a, b in zip(mine, ad.chosen))), func='three additions re-impl')
    # VC05
    mm = main[main.form == 'A4b_CVRv5'].sort_values('arm')
    cols = ['arm', 'c_FULL_d05', 'f_FULL_d05', 'c_FULL_d10', 'f_FULL_d10', 'c_FULL_d15', 'f_FULL_d15', 'd_ok', 'e_cap_FULL', 'e_rand', 'positive_FULL', 'size_status']
    rec('VC05', 'delta_sens_main_mother', mm[cols].to_dict('records'))
    # VC06
    only = grid[grid.policy_FULL == '不通过（市值通道）']
    g = only[['size_gap_pctpt_%s' % s for s in SEGS]].max(1)
    rec('VC06', 'only_size_fail_gap_dist', {'q10': round(float(g.quantile(.1)), 2), 'q50': round(float(g.quantile(.5)), 2), 'q90': round(float(g.quantile(.9)), 2),
                                            'max': round(float(g.max()), 2), 'n_le_10': int((g <= 10).sum()), 'n_le_15': int((g <= 15).sum()), 'n_le_20': int((g <= 20).sum())})
    c6 = ['form', 'arm'] + ['size_gap_pctpt_%s' % s for s in SEGS] + ['turn_rel_%s' % s for s in SEGS] + ['pos_diff_%s' % s for s in SEGS]
    rec('VC06', 'size_gap_turn_pos_main24', main[c6].round(4).to_dict('records'))
    record('VC06', 'random_refs_main24', 'file', None, flags='INFO', note='预期为决策端文件（verify/decision/）；VC19 从 randoms/P 已存路径重算主对象随机列')
    # VC07
    mc = pd.read_csv(P('checks', 'mc_topup_P_round1.csv'))
    rec('VC07', 'mc_topup', '%d / %d / %s / %s / %d-%d' % (len(mc), int(mc.over_target.sum()), round(float(mc.mcse.max()), 5), round(float(mc.mcse.median()), 6),
                                                         int(mc.n_paths.min()), int(mc.n_paths.max())))
    npc = [c for c in pp.columns if c.startswith('npaths_')]
    rec('VC07', 'npaths', sorted(set(float(v) for c in npc for v in pp[c].dropna())))
    # VC08
    for _, r in rows('VC08').iterrows():
        if r.metric == 'shape':
            record('VC08', r.sub_id, r.expected, str(pd.read_csv(P('results_P', r.sub_id)).shape), inputs=r.sub_id)
    ob = pd.read_csv(P('results_P', 'opportunity_baseline.csv'))
    rec('VC08', 'opportunity_mechanisms', '%s / %s' % (json.dumps(vc(ob.mechanism)), json.dumps(sorted(set(int(v) for v in ob.n_paths)))))
    bt = pd.read_csv(P('results_P', 'pilot_policy_bootstrap.csv'))
    cen = bt[bt.centered]; unc = bt[~bt.centered].merge(main[['form', 'arm', 'FULL']], on=['form', 'arm'])
    rec('VC08', 'bootstrap_centered_q50', '%s / %s' % (round(float(cen.q50.abs().max()), 4), round(float((unc.q50 - unc.FULL).abs().max()), 4)))
    # VC09 / VC10 / VC06-B
    p1 = pd.read_csv(P('results_B', 'part1_main_config_all_objects.csv'))
    rec('VC09', 'part1_all_objects', '%s / %s' % (str(p1.shape), json.dumps({k: int(v) for k, v in p1.groupby('block').size().items()})))
    t0 = part1_s0(p1).reset_index().rename(columns={'both_segments_pos': 'pos', 'both_segments_neg': 'neg'})
    _cmp_table('VC09', 'part1_§0_recompute', t0, ['block', 'mother'])
    g4 = p1.groupby('block')
    t4 = pd.DataFrame({'native_median': g4.D_FULL.median(), 'same_capital_median': g4.D_sc_FULL.median(), 'impact_median': g4.D_imp_FULL.median(),
                       'sign_agree': g4.apply(lambda x: float((np.sign(x.D_FULL) == np.sign(x.D_sc_FULL)).mean()))}).reset_index()
    _cmp_table('VC09', 'part1_§4_recompute', t4, ['block'])
    p2 = pd.read_csv(P('results_B', 'part2_main_config_all_objects.csv'))
    rec('VC10', 'part2_all_objects', str(p2.shape))
    g2 = p2.groupby(['block', 'mother'])
    t2 = pd.DataFrame({'objects': g2.size(), 'median_deriv': g2.D_FULL_deriv.median(), 'median_post': g2.D_FULL_post.median(), 'median_all4': g2.D_FULL_all4.median(),
                       'post_both_pos': g2.apply(lambda x: int(((x['D_2019-2023'] > 0) & (x['D_2024-2026'] > 0)).sum()))}).reset_index()
    _cmp_table('VC10', 'part2_§0_recompute', t2, ['block', 'mother'])
    ct = p2.assign(dp=p2.D_FULL_deriv > 0, pq=p2.D_FULL_post > 0).groupby(['block', 'dp', 'pq']).size().reset_index(name='objects')
    _cmp_table('VC10', 'part2_crosstab', ct, ['block', 'dp', 'pq'])
    # VC11
    rr = pd.read_csv(P('results_B', 'part1b_main_config_random_refs.csv'))
    rec('VC11', 'random_refs_B', '%s / %s' % (str(rr.shape), json.dumps({k: int(v) for k, v in rr.groupby('segment').size().items()})))
    gb = rr.groupby(['block', 'mother', 'segment'])
    tb = pd.DataFrame({'objects': gb.size(), 'median_real_minus_random': gb.rand_IID.median(), 'share_pos': gb.rand_IID.apply(lambda v: float((v > 0).mean())),
                       'max_mcse': gb.mcse_IID.max(), 'min_paths': gb.npaths_IID.min(),
                       'mc_unresolved': gb.apply(lambda x: int((x.rand_IID.abs() < 2 * x.mcse_IID).sum()))}).reset_index()
    _cmp_table('VC11', 'part1b_IID_recompute', tb, ['block', 'mother', 'segment'])
    h, b = _tables('E6j_REPORT_part1b.md')['P1B-Q01']
    tbi = tb.set_index(['block', 'mother', 'segment'])
    n = bad = 0; why = []
    for row in b:
        r = dict(zip(h, row)); k = (r['block'], r['mother'], r['segment'])
        for c in tbi.columns:
            if c in r:
                n += 1
                if not _printed_eq(r[c], tbi.loc[k, c]):
                    bad += 1; why.append('%s %s: %s vs %s' % (k, c, r[c], tbi.loc[k, c]))
    record('VC11', 'part1b_IID_recompute|vs_report', None, '%d 格 / 不符 %d' % (n, bad), func='重算 vs P1B-Q01 表', flags='' if bad == 0 else 'DIFFERS?',
           note='; '.join(why[:4]))
    rec('VC11', 'B_mcse_over_03', int((rr.mcse_IID > 0.03).sum()))
    for s in POST:
        ds = pd.read_csv(P('results_B', 'descriptor_stats_%s_final.csv' % s))
        mc_ = ds[(ds.alpha == 0.25) & (ds.H == 5)]
        rec('VC11', 'B_post_%s' % s, '%d / %d / %d / %s' % (len(ds), len(mc_), int((mc_.mcse_IID > 0.03).sum()), json.dumps(vc(mc_.mc_status_IID))))
    # VC12
    rb = pd.read_csv(P('registration', 'record_B_draft_objects.csv'))
    rec('VC12', 'record_B_draft_objects', '%s / %s' % (str(rb.shape), str(list(rb.columns))))
    rec('VC12', 'record_B_draft_per_block', {k: int(v) for k, v in rb.groupby('block').size().items()})
    # VC13
    for _, r in rows('VC13').iterrows():
        if r.metric == 'data_rows':
            record('VC13', r.sub_id, r.expected, len(pd.read_csv(P(r.source))), inputs=r.source)
    el = pd.read_csv(P('registry', 'exposure_ledger.csv'))
    e_, t_ = exp('VC13', 'exposure_types')
    record('VC13', 'exposure_types', e_, _exposure_mine(el, e_), note='ledger 列：%s' % list(el.columns))
    rec('VC13', 'pp_historical_exposed', '%s / %s' % (json.dumps({k: int(v) for k, v in pp[pp.historical_exposed].groupby('form').size().items()}),
                                                      json.dumps({k: int(v) for k, v in pp[pp.historical_exposed].groupby('arm').size().items()})))
    # VC14
    ho = jload(P('results', 'hypothesis_outcomes.json'))
    card = ('source_claim', 'exposure', 'missing_assumption', 'experiment', 'result_query', 'supported_scope', 'alternative_surviving', 'next_design_change')
    miss = {q: [k for k in ('plan_text', 'queries', 'effect', 'mechanism', 'unknown', 'next_design_change') if not v.get(k)] for q, v in ho.items()}
    missc = {q: [k for k in card if not v['hypothesis_update_card'].get(k)] for q, v in ho.items()}
    rec('VC14', 'hypothesis_outcomes', '%d / %s / %s' % (len(ho), json.dumps({q: m for q, m in miss.items() if m}), json.dumps({q: m for q, m in missc.items() if m})))
    reg = jload(P('reports', 'query_registry.json'))
    cited = sorted({q for v in ho.values() for q in v['queries']})
    rec('VC14', 'hypothesis_queries', '%d / %s' % (len(cited), json.dumps([q for q in cited if q not in reg])))


def part1_s0(p1):
    """P1-Q01：块 × 母体；both_segments_pos / neg = 两推导段增量同为正 / 负的对象数（part1 正文口径）。"""
    g = p1.groupby(['block', 'mother'])
    return pd.DataFrame({'objects': g.size(), 'median_FULL': g.D_FULL.median(), 'p10': g.D_FULL.quantile(.1), 'p90': g.D_FULL.quantile(.9),
                         'both_segments_pos': g.apply(lambda x: int(((x['D_2010-2014'] > 0) & (x['D_2015-2018'] > 0)).sum())),
                         'both_segments_neg': g.apply(lambda x: int(((x['D_2010-2014'] < 0) & (x['D_2015-2018'] < 0)).sum()))})


def _exposure_mine(el, e_):
    """按预期串的结构组装（结构取自预期键名，数值自算）。"""
    try:
        parts = [json.loads(x) if x.strip().startswith('{') else x for x in str(e_).split(' / ')]
    except Exception:
        parts = []
    out = [json.dumps(vc(el.exposure_type), ensure_ascii=False)]
    col = [c for c in el.columns if 'historical' in c.lower()]
    if col:
        h_ = el[el[col[0]].astype(str).isin(['True', 'true', '1'])]
        out.append(str(len(h_)))
        out.append(json.dumps({k: int(v) for k, v in h_.descriptor_id.map(lambda d: d.split('|')[1] if '|' in d else d).value_counts().items()}))
    return ' / '.join(out)


def _cmp_table(pid, sub, mine_df, keys):
    e, t = exp(pid, sub)
    if e is None:
        return record(pid, sub, None, mine_df.to_dict('records'))
    try:
        ev = pd.DataFrame(json.loads(e))
    except ValueError:
        OUT.append(dict(probe_id=pid, sub_id=sub, expected='（预期串 %d 字符，JSON 不完整）' % len(e), recomputed='%d 行' % len(mine_df), diff='',
                        verdict='NOT_COMPUTABLE', flags='EXPECTED_TRUNCATED', note='决策端预期值在 %d 字符处截断，无法逐行比；另以报告表替代核对（见同 probe 的 |vs_report 行）' % len(e),
                        inputs=sub, function='table recompute'))
        return
    m = mine_df.copy()
    for k in keys:
        ev[k] = ev[k].astype(str); m[k] = m[k].astype(str)
    j = ev.merge(m, on=keys, how='outer', suffixes=('_e', '_m'), indicator=True)
    only = j[j._merge != 'both']
    worst, why, rnd = 0.0, [], False
    for c in [c for c in ev.columns if c not in keys]:
        a, b = j[c + '_e'], j[c + '_m']
        for x, y in zip(a, b):
            ok, d, r_, w = _cmp(_parse(str(x)) if isinstance(x, str) else x, y if not isinstance(y, (np.integer, np.floating)) else y.item(), 1e-9, c)
            if not ok:
                why.append(w)
            elif r_:
                rnd = True
            if np.isfinite(d):
                worst = max(worst, d)
    ok = not why and not len(only)
    OUT.append(dict(probe_id=pid, sub_id=sub, expected='%d 行' % len(ev), recomputed='%d 行' % len(m), diff='%.3g' % worst, verdict='REPRODUCED' if ok else 'DIFFERS',
                    flags='ROUNDING' if (ok and rnd) else '', note=('键不对齐 %d 行；' % len(only) if len(only) else '') + '; '.join(why[:5])[:900], inputs=sub, function='table recompute'))


# ================================================================== V-D（表 ↔ 报告）
def _tables(report):
    """解析报告：query_id → (列, 行列表)。"""
    txt = open(P('reports', report), encoding='utf-8').read().splitlines()
    out, i = {}, 0
    while i < len(txt):
        m = re.search(r'query_id=([A-Z0-9]+-Q\d+)', txt[i])
        if m and txt[i].startswith('>'):
            j = i + 1
            while j < len(txt) and not txt[j].startswith('|'):
                j += 1
            hdr = _cells(txt[j])
            body = []
            k = j + 2
            while k < len(txt) and txt[k].startswith('|'):
                body.append(_cells(txt[k])); k += 1
            out[m.group(1)] = (hdr, body); i = k
        else:
            i += 1
    return out


def VD():
    reg = jload(P('reports', 'query_registry.json'))
    tabs = {}
    for rp in sorted({v['file'] for v in reg.values()}):
        tabs.update(_tables(rp))
    for _, r in rows('VD01').iterrows():
        h, b = tabs.get(r.sub_id, (None, None))
        record('VD01', r.sub_id, r.expected, '%d/%d' % (len(b), len(h)) if h is not None else None, inputs=reg.get(r.sub_id, {}).get('file', ''), func='parse table',
               note='' if h is not None else '正文未找到表')
    # VD02：part3 §1–§6 = pilot_policy
    pp = pd.read_csv(P('results_P', 'pilot_policy.csv'))
    n = bad = 0; why = []
    for i, form in enumerate(['A4b_CVRv5', 'A4b', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5']):
        h, b = tabs['P3-Q%02d' % (i + 1)]
        m = pp[pp.main_config & (pp.form == form) & pp.arm.isin(ARMS)].set_index('arm')
        for row in b:
            arm = row[0]
            for c, v in zip(h[1:], row[1:]):
                n += 1
                tv = m.loc[arm, c]
                if not _printed_eq(v, tv):
                    bad += 1; why.append('%s %s %s: %s vs %s' % (form, arm, c, v, tv))
    rec('VD02', 'part3_§1-6_vs_csv', '%d / %d' % (n, bad), note='; '.join(why[:5]))
    # VD03：part1 §0 = CSV
    p1 = pd.read_csv(P('results_B', 'part1_main_config_all_objects.csv'))
    h, b = tabs['P1-Q01']
    t0 = part1_s0(p1)
    n = bad = 0; why = []
    for row in b:
        k = (row[0], row[1])
        for c, v in zip(h[2:], row[2:]):
            if c in t0.columns:
                n += 1
                if not _printed_eq(v, t0.loc[k, c]):
                    bad += 1; why.append('%s %s: %s vs %s' % (k, c, v, t0.loc[k, c]))
    rec('VD03', 'part1_§0_vs_csv', '%d / %d' % (n, bad), note='表头 %s；%s' % (h, '; '.join(why[:4])))
    # VD06：§7 why 逐字；§19 候选；§13 网格
    ad = pd.read_csv(P('results_P', 'pilot_policy_additions.csv'))
    h, b = tabs['P3-Q07']
    tw = [dict(zip(h, row)) for row in b]
    mis = sum(str(t.get('why', '')).replace('nan', '') != (str(w) if isinstance(w, str) else '') for t, w in zip(tw, ad.why))
    record('VD06', 'additions_why_text', None, '%d 行 / 不符 %d' % (len(tw), mis), func='逐字', flags='' if mis == 0 else 'DIFFERS?')
    h, b = tabs['P3-Q21']
    main = pp[pp.main_config & pp.arm.isin(ARMS)]
    exp19 = main[main.policy_FULL == '通过'][['form', 'arm']].values.tolist()
    got19 = [[r[0], r[1]] for r in b]
    record('VD06', '§19_candidates', json.dumps(exp19, ensure_ascii=False), got19, func='表 vs pilot_policy',
           note='deployment_authorized 全 False：%s' % bool((~main.deployment_authorized).all()))
    h, b = tabs['P3-Q19']
    gridv = pp[pp.arm.isin(ARMS)].set_index(['form', 'arm', 'alpha', 'H']).FULL
    n = bad = 0
    for row in b:
        form, arm, a = row[0], row[1], float(row[2])
        for c, v in zip(h[3:], row[3:]):
            n += 1
            if not _printed_eq(v, gridv.get((form, arm, a, int(c)), np.nan)):
                bad += 1
    record('VD06', '§13_grid', None, '%d / %d' % (n, bad), func='4 位有效', flags='' if bad == 0 else 'DIFFERS?')
    # VD07：各附表与文件（每表抽 30 格，seed 20260927）
    rng = np.random.default_rng(20260927)
    for qid, fn, keys in (('P3-Q26', 'robustness_main.csv', ['form', 'arm']), ('P3-Q29', 'opportunity_baseline.csv', ['form', 'arm', 'mechanism', 'profile']),
                          ('P3-Q32', 'simultaneous_bands.csv', ['form', 'L', 'contrast']), ('P3-Q34', 'member_c_status.csv', None),
                          ('P3-Q24', 'drawdown_pair.csv', ['form', 'arm', 'segment']), ('P3-Q23', 'cs_frozen_score.csv', None)):
        h, b = tabs[qid]
        df = pd.read_csv(P('results_P', fn))
        if qid == 'P3-Q23':
            df = df[df.H == 5].dropna(axis=1, how='all')
        n = bad = 0; why = []
        idx = rng.choice(len(b), size=min(30, len(b)), replace=False)
        for i in idx:
            row = dict(zip(h, b[i]))
            cand = df
            if keys:
                for k in keys:
                    cand = cand[cand[k].astype(str) == str(row[k]).replace('.0', '') if k in ('L',) else cand[k].astype(str) == row[k]]
            else:
                cand = df.iloc[[i]]
            if len(cand) != 1:
                why.append('行定位 %s 命中 %d' % ({k: row.get(k) for k in (keys or [])}, len(cand))); bad += 1; continue
            for c in h:
                if c in df.columns and (not keys or c not in keys):
                    n += 1
                    if not _printed_eq(row[c], cand.iloc[0][c]):
                        bad += 1; why.append('%s %s vs %s' % (c, row[c], cand.iloc[0][c]))
        record('VD07', qid + '|' + fn, None, '%d 格 / 不符 %d' % (n, bad), func='抽 30 行', flags='' if bad == 0 else 'DIFFERS?', note='; '.join(why[:4]))
    # §14 别名表 = 独立路径（E6i 统计表）：只核表内最大差 ≤ 1.6e−14
    h, b = tabs['P3-Q20']
    mx = max(float(r[h.index('max_abs_diff')]) for r in b)
    record('VD07', 'P3-Q20_alias_max', None, mx, func='表内最大', note='≤ 1.6e−14：%s；D07 独立路径 1.98e−14' % (mx <= 1.6e-14))


def _printed_eq(s, v):
    """报告印出值（4 位有效）vs 表值。"""
    s = str(s).strip()
    if isinstance(v, (bool, np.bool_)):
        return s == str(bool(v))
    if isinstance(v, str) or v is None:
        return s == (v if isinstance(v, str) else '')
    try:
        fv = float(v)
    except (TypeError, ValueError):
        return s == str(v)
    if np.isnan(fv):
        return s in ('', 'nan', 'NaN')
    try:
        fs = float(s)
    except ValueError:
        return False
    if fs == fv:
        return True
    p = float('%.4g' % fv)
    return abs(fs - p) <= 1e-12 * max(1, abs(p)) or abs(fs - fv) <= 0.5 * 10 ** (np.floor(np.log10(abs(fv) + 1e-300)) - 3)


# ================================================================== V-E（装配恒等式）
def VE():
    ld = pd.read_csv(P('carried', 'leader_six_forms_capital.csv'))
    rec('VE01', 'leader_fee8', float((ld.fee8_ann - 0.08 * ld.turnover_ann).abs().max()))
    e_, _ = exp('VE01', 'leader_net6_minus_net8')
    er = pd.DataFrame(json.loads(e_))
    mine = ld.assign(n6m8=(ld.total_net6_ann - ld.total_net8_ann).round(4), exact_form=(0.02 * ld.turnover_ann * ld.days / ld.active_days).round(4))
    mine = mine[['segment', 'form', 'n6m8', 'exact_form']]
    _cmp_table('VE01', 'leader_net6_minus_net8', mine, ['segment', 'form'])
    rows_ = []; cmpr = []
    for seg in SEGS:
        for form in FORMS:
            _, z = acc(seg, form)
            i = find_desc(form, 'C0', 0, 5, seg)
            n8, g, tu = z['net8'][i], z['gross'][i], z['turn'][i]
            f = np.isfinite(n8)
            rows_.append(dict(segment=seg, form=form, n=int(f.sum()), L=len(n8), mean_net8_x252x100=round(float(n8[f].mean() * ANN), 6),
                              daily_identity_resid=float(np.nanmax(np.abs(n8 - (g - 8e-4 * tu)))), sum_turn_over_n_x252=round(float(252 * tu.sum() / f.sum()), 6)))
            l = ld[(ld.segment == seg) & (ld.form == form)].iloc[0]
            cmpr.append(dict(segment=seg, form=form, diff_net8=round(float(n8[f].mean() * ANN - l.total_net8_ann), 5),
                             diff_turn=round(float(252 * tu.sum() / f.sum() - l.turnover_ann), 5)))
    _cmp_table('VE02', 'C0_H5_ledger', pd.DataFrame(rows_), ['segment', 'form'])
    _cmp_table('VE02', 'C0_vs_leader', pd.DataFrame(cmpr), ['segment', 'form'])
    # VE03 SM 交互（由 pilot_policy 网格值）
    pp = pd.read_csv(P('results_P', 'pilot_policy.csv'))
    V = pp.set_index(['form', 'arm', 'alpha', 'H'])
    reg = jload(P('reports', 'query_registry.json'))
    h, b = _tables('E6j_REPORT_part3.md')['P3-Q09']
    n = bad = 0
    for row in b:
        r = dict(zip(h, row)); form, span = r['form'], r['span']
        k = 'D_%s' % span if span != 'FULL' else 'FULL'
        g = lambda arm, a: V.loc[(form, arm, a, 5), k]
        vals = {'I_interaction': g('SM', .25) - g('S', .125) - g('M', .125), 'SM25_minus_S25': g('SM', .25) - g('S', .25), 'SM25_minus_M25': g('SM', .25) - g('M', .25)}
        for c, v in vals.items():
            n += 1
            if not _printed_eq(r[c], v):
                bad += 1
    rec('VE03', 'SM_interaction_§9', '%d / %d' % (n, bad))
    bd = pd.read_csv(P('results_P', 'simultaneous_bands.csv'))
    m1 = (bd.point_lo - (bd.FULL - 1.959963984540054 * bd.boot_sd)).abs().max(); m2 = (bd.point_hi - (bd.FULL + 1.959963984540054 * bd.boot_sd)).abs().max()
    m3 = (bd.simul_lo - (bd.FULL - bd.maxt_q95 * bd.boot_sd)).abs().max(); m4 = (bd.simul_hi - (bd.FULL + bd.maxt_q95 * bd.boot_sd)).abs().max()
    rec('VE04', 'bands_identity', float(max(m1, m2, m3, m4)), flags='ROUNDING')
    # VE05
    out = []
    for seg in SEGS:
        d = pd.read_csv(P('diagnostics', 'P', seg, 'diagnostics_%s.csv' % seg))
        cs = d[d['diag'] == 'CS']
        c1 = cs[cs.arm == 'C1']
        mx = 0.0
        for _, r in cs[cs.H == 5].iterrows():
            Dseg = pp[(pp.form == r.form) & (pp.arm == r.arm) & np.isclose(pp.alpha, .25) & (pp.H == 5)]['D_%s' % seg].iloc[0]
            mx = max(mx, abs(r.N1_minus_N0 - Dseg))
        kinds = json.dumps({k: int(v) for k, v in d['diag'].value_counts(sort=False).items()})
        out.append(dict(segment=seg, n_rows=len(d), n_CS=len(cs), max_closure_resid=float(cs.closure_resid.abs().max()),
                        C1_rows_max_abs=float(max(c1.C0_minus_N0.abs().max(), c1.N1_minus_C1.abs().max())), max_abs_N1N0_minus_D_H5=mx, diag_kinds=kinds))
    e_, _ = exp('VE05', 'CS_closure_P')
    ev = pd.DataFrame(json.loads(e_))
    mo = pd.DataFrame(out)
    okc = all(abs(a - b) <= 1e-15 or (a <= 1e-12 and b <= 1e-12) for a, b in zip(ev.max_closure_resid, mo.max_closure_resid))
    okn = (ev[['segment', 'n_rows', 'n_CS']].astype(str).values == mo[['segment', 'n_rows', 'n_CS']].astype(str).values).all()
    okd = all(json.loads(a) == json.loads(b) for a, b in zip(ev.diag_kinds, mo.diag_kinds))
    record('VE05', 'CS_closure_P', '%s' % okc, str(okc and okn and okd and (mo.max_abs_N1N0_minus_D_H5 <= 1e-12).all() and (mo.C1_rows_max_abs == 0).all()),
           note='closure max %s；N1−N0 vs D max %s' % (mo.max_closure_resid.max(), mo.max_abs_N1N0_minus_D_H5.max()), func='CS 闭合')
    fz = pd.read_csv(P('results_P', 'cs_frozen_score.csv'))
    record('VE05', 'CS_FROZEN_closure', None, float(fz.closure_resid.abs().max()), func='11b 同式', note='≤ 1e−12：%s' % (fz.closure_resid.abs().max() <= 1e-12))
    bb = []
    rng = np.random.default_rng(20260927)
    for seg in SEGS:
        for f in glob.glob(P('diagnostics', 'B', seg, '*.csv')):
            d = pd.read_csv(f)
            if 'closure_resid' in d:
                c = d[d['diag'] == 'CS'].dropna(subset=['closure_resid'])
                for blk, x in c.groupby('block'):
                    bb.append(float(x.sample(min(50, len(x)), random_state=20260927).closure_resid.abs().max()))
    record('VE05', 'CS_closure_B', None, max(bb) if bb else None, func='按块抽 50', note='≤ 1e−12：%s' % (max(bb) <= 1e-12 if bb else None))
    # VE06
    p2 = pd.read_csv(P('results_B', 'part2_main_config_all_objects.csv'))
    n = lambda s: p2['n_%s' % s]; D = lambda s: p2['D_%s' % s]
    rec('VE06', 'B_post_merge', float(((D(POST[0]) * n(POST[0]) + D(POST[1]) * n(POST[1])) / (n(POST[0]) + n(POST[1])) - p2.D_FULL_post).abs().max()))
    rec('VE06', 'B_deriv_merge', float(((D(SEGS[0]) * n(SEGS[0]) + D(SEGS[1]) * n(SEGS[1])) / (n(SEGS[0]) + n(SEGS[1])) - p2.D_FULL_deriv).abs().max()))
    rec('VE06', 'B_all4_merge', float((sum(D(s) * n(s) for s in SEGS) / sum(n(s) for s in SEGS) - p2.D_FULL_all4).abs().max()))
    p1 = pd.read_csv(P('results_B', 'part1_main_config_all_objects.csv'))
    k = ['block', 'mother', 'slot', 'measurement_id', 'direction']
    j = p1.merge(p2, on=k)
    rec('VE06', 'part1_vs_part2_deriv', '%d / %s' % (len(j), float((j.D_FULL - j.D_FULL_deriv).abs().max())))


# ================================================================== 现算探针（账本级）
def LEDGER():
    pp = pd.read_csv(P('results_P', 'pilot_policy.csv'))
    rng = np.random.default_rng(20260927)
    main = pp[pp.main_config].index.tolist()
    rest = [i for i in pp.index if i not in main]
    pick = main + sorted(rng.choice(rest, size=200, replace=False).tolist())
    worst = {'D': 0.0, 'n': 0, 'Y': 0.0, 'FULL': 0.0, 'G4': 0.0}
    for i in pick:
        r = pp.loc[i]
        Ds, ns, ds, dt = [], [], [], []
        for s in SEGS:
            c = series(s, r.form, r.arm, r.alpha, int(r.H), 'net8'); p = series(s, r.form, 'C0', 0, int(r.H), 'net8')
            d = paired(c, p); D, n = segD(d); Ds.append(D); ns.append(n); ds.append(d); dt.append(acc(s, r.form)[1]['dates'])
            worst['D'] = max(worst['D'], abs(D - r['D_%s' % s])); worst['n'] = max(worst['n'], abs(n - r['n_%s' % s]))
        full = sum(a * b for a, b in zip(Ds, ns)) / sum(ns); g4 = float(np.median(Ds))
        worst['FULL'] = max(worst['FULL'], abs(full - r.FULL)); worst['G4'] = max(worst['G4'], abs(g4 - r.G4))
        d = np.concatenate(ds); yrs = pd.to_datetime(pd.Index(np.concatenate(dt)).astype(str)).year.values
        for y in range(2010, 2027):
            m = (yrs == y) & np.isfinite(d)
            if m.any():
                worst['Y'] = max(worst['Y'], abs(d[m].mean() * ANN - r['Y%d' % y]))
    ok = max(worst['D'], worst['Y'], worst['FULL'], worst['G4']) <= 1e-9 and worst['n'] == 0
    record('VC15', 'pilot_policy_from_ledger', 'True', str(ok), func='accounts/P 子 − 母', note='%d 对象（42 主 + 200 抽）；最大差 %s' % (len(pick), json.dumps(worst)),
           inputs='accounts/P/*/*.npz')
    # VC16 同资本、VC17 HAC、VC18 turn/pos/qmiss（42 / 24 主对象）
    m42 = pp[pp.main_config]
    wsc = 0.0; wse = 0.0; wtr = 0.0; notes = []
    for _, r in m42.iterrows():
        Dsc, ns = [], []
        for s in SEGS:
            sc = paired(series(s, r.form, r.arm, r.alpha, 5, 'sc_child'), series(s, r.form, r.arm, r.alpha, 5, 'sc_parent'))
            D, n = segD(sc); Dsc.append(D); ns.append(n)
            wsc = max(wsc, abs(D - r['Dsc_%s' % s]))
        if r.arm in ARMS:
            ds = []
            for s in SEGS:
                d = paired(series(s, r.form, r.arm, r.alpha, 5, 'net8'), series(s, r.form, 'C0', 0, 5, 'net8'))
                ds.append(d)
                wse = max(wse, abs(hac(d, 5) * ANN - r['se_H_%s' % s]), abs(hac(d, 20) * ANN - r['se_2H_%s' % s]))
                c_t, p_t = series(s, r.form, r.arm, r.alpha, 5, 'turn'), series(s, r.form, 'C0', 0, 5, 'turn')
                c_p, p_p = series(s, r.form, r.arm, r.alpha, 5, 'pos'), series(s, r.form, 'C0', 0, 5, 'pos')
                qm = series(s, r.form, r.arm, r.alpha, 5, 'qmiss')
                tr = float(np.mean(c_t)) / float(np.mean(p_t)) - 1.0
                wtr = max(wtr, abs(tr - r['turn_rel_%s' % s]), abs(float(np.mean(c_p) - np.mean(p_p)) - r['pos_diff_%s' % s]),
                          abs(float(np.nansum(qm) / max(np.sum(c_t), 1e-300)) - r['qmiss_share_%s' % s]))
            dd = np.concatenate(ds)
            wse = max(wse, abs(hac(dd, 5) * ANN - r.FULL_se_H), abs(2.80 * hac(dd, 5) * ANN - r.FULL_MDE80))
    record('VC16', 'Dsc_from_ledger', 'True', str(wsc <= 1e-9), note='42 主配置 × 4 段最大差 %.3g；Dimp 来源 = npz bracket 字段（冲击 κ√(A·1e8)·bracket，A5 κ.5）' % wsc, inputs='sc_child / sc_parent')
    record('VC17', 'HAC_from_ledger', 'True', str(wse <= 1e-6), note='24 主对象 se_H / se_2H(=max(2H,20)=20) / FULL_se_H / FULL_MDE80 最大差 %.3g' % wse, func='Bartlett，原日历 mask')
    record('VC18', 'turn_pos_qmiss', 'True', str(wtr <= 1e-9), note='turn_rel = mean(turn_子)/mean(turn_母) − 1（全日历，含零换手日）；pos_diff = mean(pos_子) − mean(pos_母)；qmiss_share = Σqmiss / Σturn_子；最大差 %.3g' % wtr)
    # VC19 随机列
    wr = 0.0; cnt = 0
    for _, r in pp[pp.main_config & pp.arm.isin(ARMS)].iterrows():
        for s in POST:
            z = np.load(P('randoms', 'P', s, '%s__%s.npz' % (r.form, r.arm)), allow_pickle=False)
            mechs = [str(m) for m in z['mechs']]
            ai = list(np.round(z['alphas'], 6)).index(0.25); hi = list(z['Hs']).index(5)
            real = float(np.nanmean(series(s, r.form, r.arm, 0.25, 5, 'net8'))) * ANN
            use = mechs if r.form == 'A4b_CVRv5' else ['IID']
            for mname in use:
                x = z['ann'][mechs.index(mname), :, ai, hi, 0]; x = x[np.isfinite(x)]
                wr = max(wr, abs(real - x.mean() - r['rand_%s_%s' % (mname, s)]), abs(x.std(ddof=1) / np.sqrt(len(x)) - r['mcse_%s_%s' % (mname, s)]))
                cnt += 1
    record('VC19', 'random_cols_from_paths', 'True', str(wr <= 1e-12), note='%d (对象, 段, 机制)；最大差 %.3g；主母体加全部七机制' % (cnt, wr))
    # VC20 B 抽样
    ds = pd.read_csv(P('results_B', 'descriptor_stats_2019-2023_final.csv'))
    smp = ds.sample(200, random_state=20260927)
    pz = np.load(P('accounts', 'B', '2019-2023', 'parents.npz'), allow_pickle=False)
    par = {str(k): i for i, k in enumerate(pz['keys'])}
    wb = 0.0; wn = 0
    cache = {}
    for _, r in smp.iterrows():
        f = P('accounts', 'B', '2019-2023', '%s__%s.npz' % (r.mother, r.block))
        if f not in cache:
            z = np.load(f, allow_pickle=False); cache[f] = ({str(d): i for i, d in enumerate(z['desc'])}, z['net8'])
        ix, net = cache[f]
        d = paired(net[ix[r.descriptor_id]], pz['net8'][par['%s|H%d' % (r.mother, int(r.H))]])
        D, n = segD(d); wb = max(wb, abs(D - r.D)); wn = max(wn, abs(n - r.n))
    record('VC20', 'B_sample_D', 'True', str(wb <= 1e-9 and wn == 0), note='200 描述符（2019-2023，seed 20260927）最大差 D %.3g n %d' % (wb, wn))
    ob = pd.read_parquet(P('results', 'research_object_results.parquet'))
    nB = int((ob.package == 'B').sum())
    s500 = []
    for s in SEGS:
        d = pd.read_csv(P('results_B', 'descriptor_stats_%s_final.csv' % s))
        s500.append(d)
    alld = pd.concat(s500).set_index(['segment', 'descriptor_id'])
    obb = ob[ob.package == 'B'].set_index(['segment', 'descriptor_id'])
    pick = obb.sample(500, random_state=20260927)
    cols = [c for c in pick.columns if c in alld.columns and c not in ('package',)]
    diffc = 0
    for k, row in pick.iterrows():
        for c in cols:
            a, b = row[c], alld.loc[k, c]
            if not ((pd.isna(a) and pd.isna(b)) or a == b or (isinstance(a, float) and abs(a - b) <= 1e-12)):
                diffc += 1
    record('VC20', 'parquet_vs_stats', 'True', str(nB == 4 * 13398 and diffc == 0), note='B 行 %d；抽 500 行 %d 列不符 %d 格' % (nB, len(cols), diffc))
    # VC21 / VE（领导表年化约定）
    ld = pd.read_csv(P('carried', 'leader_six_forms_capital.csv'))
    w1 = 0.0; w2 = 0.0
    for _, l in ld.iterrows():
        tu = series(l.segment, l.form, 'C0', 0, 5, 'turn'); n8 = series(l.segment, l.form, 'C0', 0, 5, 'net8')
        w1 = max(w1, abs(252 * tu.sum() / len(tu) - l.turnover_ann))
        w2 = max(w2, abs((l.total_net6_ann - l.total_net8_ann) - 0.02 * 252 * tu.sum() / np.isfinite(n8).sum()))
    record('VC21', 'leader_turnover_convention', 'True', str(w1 <= 1e-9 and w2 <= 1e-9),
           note='turnover_ann = 252·Σturn / L（L = 账本全部行，含未起步 / 缺净值日）→ 最大差 %.3g；net6 − net8 = 0.02·252·Σturn / n（n = 非缺失净值日）= 0.02·turnover_ann·L/n → 最大差 %.3g；与 C0 账本 252·Σturn / n 的差即 L/n 因子' % (w1, w2))
    # VE07 carried C1
    fs = sorted(glob.glob(P('carried', 'C1', '*', 'c1_capital_views_*.csv')))
    c = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    gcol = [x for x in c.columns if x.startswith('gross_d')] or ['gross_d_ann']
    ok_id = float((c.attr_unit_ann + c.attr_deploy_ann + c.attr_onesided_ann - c[gcol[0]]).abs().max()) if gcol[0] in c else None
    record('VE07', 'C1_attribution_identity', None, ok_id, note='%d 行；列 %s' % (len(c), gcol[0]))
    an = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(P('carried', 'C1', '*', 'c1_native_anchor_*.csv')))], ignore_index=True)
    record('VE07', 'C1_native_anchor', None, '%d 行 / max %s / 缺 %d' % (len(an), float(an.max_abs.max()), int(an.max_abs.isna().sum())),
           note='98304 = c1_native_anchor_*.csv 行数（逐配置日账本一行）')
    g = c.groupby(['segment', 'contrast', 'fixed', 'scope']).native_d_ann.median().reset_index()
    h, b = _tables('E6j_REPORT_carried.md')['CAR-Q01']
    bad = 0
    tb = {(r[0], r[1], r[2], r[3]): r for r in b}
    for _, r in g.iterrows():
        row = tb.get((r.segment, r.contrast, r.fixed, r.scope))
        if row is None or not _printed_eq(row[h.index('native')], r.native_d_ann):
            bad += 1
    record('VE07', 'CAR-Q01_medians', None, '%d 组 / 不符 %d' % (len(g), bad), flags='' if bad == 0 else 'DIFFERS?')
    # VE08
    m24 = pp[pp.main_config & pp.arm.isin(ARMS)]
    ms = [c for c in pp.columns if c.startswith('matched_capital_share_')]
    inr = bool(((m24[ms] > 0) & (m24[ms] <= 1 + 1e-12)).all().all())
    same = float(np.mean([np.sign(r['D_%s' % s]) == np.sign(r['Dsc_%s' % s]) for _, r in m24.iterrows() for s in SEGS]))
    w6 = 0.0
    for _, r in m24.iterrows():
        d6, d12, nn = [], [], []
        for s in SEGS:
            c_g, p_g = series(s, r.form, r.arm, .25, 5, 'gross'), series(s, r.form, 'C0', 0, 5, 'gross')
            c_t, p_t = series(s, r.form, r.arm, .25, 5, 'turn'), series(s, r.form, 'C0', 0, 5, 'turn')
            a6, n6 = segD(paired(c_g - c_t * 6e-4, p_g - p_t * 6e-4)); a12, _ = segD(paired(c_g - c_t * 12e-4, p_g - p_t * 12e-4))
            d6.append(a6); d12.append(a12); nn.append(r['n_%s' % s])
        f6 = sum(a * b for a, b in zip(d6, nn)) / sum(nn); f12 = sum(a * b for a, b in zip(d12, nn)) / sum(nn)
        w6 = max(w6, abs(f6 - r.FULL_6bp), abs(f12 - r.FULL_12bp))
    record('VE08', 'capital_and_cost', None, 'matched_capital_share∈(0,1]：%s；D 与 Dsc 同号率 %.3f；FULL_6bp / 12bp 重算最大差 %.3g' % (inr, same, w6),
           flags='' if (inr and w6 <= 1e-6) else 'DIFFERS?')
    # VE09 计数恒等
    reg = {f: len(pd.read_csv(P('registry', f))) for f in ('descriptors_P.csv', 'descriptors_B.csv', 'cs_P.csv', 'cs_B.csv')}
    nacc = len(glob.glob(P('accounts', 'B', '*', '*.npz'))); nran = len(glob.glob(P('randoms', 'B', '*', '*.npz'))); nrp = len(glob.glob(P('randoms', 'P', '*', '*.npz')))
    checks = {'504=528−24': len(pp) == reg['descriptors_P.csv'] - 24, '42=24+18': int(pp.main_config.sum()) == 42, '288=6×4×12': int(pp.arm.isin(ARMS).sum()) == 288,
              '216=6×3×12': int((~pp.arm.isin(ARMS)).sum()) == 216, '13398=202×3×21+8×4×21': reg['descriptors_B.csv'] == 13398 == 202 * 3 * 21 + 8 * 4 * 21,
              '638=202×3+8×4': 638 == 202 * 3 + 8 * 4, '5104=638×8': reg['cs_B.csv'] == 5104 == 638 * 8, '192=24×8': reg['cs_P.csv'] == 192,
              'randoms/P 96=6×4×4': nrp == 96, 'accounts/B %d' % nacc: True, 'randoms/B %d' % nran: True}
    record('VE09', 'count_identities', None, json.dumps(checks, ensure_ascii=False), flags='' if all(checks.values()) else 'DIFFERS?',
           note='accounts/B = 4 段 × (28 母体块 + 28 掩码) + 4 parents = %d；randoms/B = 740 队列分片 + 测时分片 1 = %d（B_test 另目录）' % (4 * 57, nran))


# ================================================================== VB06–VB08
def VB_LEDGER():
    lp = pd.read_parquet(P('anchors', 'mother_ledger_prod_v2.parquet'))
    record('VB06', 'ledger_columns', None, str(list(lp.columns)[:12]), flags='INFO')
    w = 0.0; n = 0
    fcol = 'form' if 'form' in lp.columns else [c for c in lp.columns if 'form' in c.lower() or 'cfg' in c.lower()][0]
    scol = 'segment' if 'segment' in lp.columns else [c for c in lp.columns if 'seg' in c.lower() or 'period' in c.lower()][0]
    for seg in SEGS:
        for form in FORMS:
            x = lp[(lp[scol] == seg) & (lp[fcol] == form)]
            for fld in ('net8', 'gross', 'pos', 'turn'):
                if fld in x:
                    a = x[fld].to_numpy(float); b = series(seg, form, 'C0', 0, 5, fld)
                    if len(a) != len(b):
                        w = np.inf; continue
                    m = np.isfinite(a) | np.isfinite(b)
                    w = max(w, float(np.nanmax(np.abs(a[m] - b[m]))) if m.any() else 0.0); n += 1
    record('VB06', 'ledger_vs_npz_C0', 'True', str(w <= 1e-12), note='%d 列序列；最大差 %s' % (n, w))
    ms = pd.read_csv(P('anchors', 'mother_summary_6bp.csv')); e5 = pd.read_csv(os.path.join(E5A, 'summary.csv'))
    common = [c for c in ms.columns if c in e5.columns and c not in ('period', 'cfg')]
    j = ms.merge(e5, on=['period', 'cfg'], suffixes=('_a', '_b')) if 'period' in ms.columns else None
    if j is not None:
        mx = max(float((j[c + '_a'] - j[c + '_b']).abs().max()) for c in common if j[c + '_a'].dtype.kind == 'f')
        record('VB06', 'mother_summary_6bp_vs_E5a', 'True', str(mx <= 1e-12), note='%d 行 %d 列最大差 %.3g' % (len(j), len(common), mx))
    # VB07 α = 0 掩码 vs E5a pool2（成员）
    pool1 = pd.read_csv(os.path.join(E5A, 'pool1_I11_screening.csv'), dtype={'ticker': str})
    dcol = 'tradeDate' if 'tradeDate' in pool1.columns else pool1.columns[1]
    pool1['d'] = pd.to_datetime(pool1[dcol].astype(str)).dt.strftime('%Y-%m-%d')
    fmap = {'A4b': 'pool2_A4b_pure.csv', 'M_mean3_v2': 'pool2_Mmean_v2_pure.csv', 'M_union3_v2': 'pool2_Munion_v2_pure.csv',
            'A4b_CVRv5': 'pool2_A4b_cvrveto.csv', 'M_mean3_v2_CVRv5': 'pool2_Mmean_v2_cvrveto.csv', 'M_union3_v2_CVRv5': 'pool2_Munion_v2_cvrveto.csv'}
    p2 = {f: pd.read_csv(os.path.join(E5A, v), dtype={'ticker': str}) for f, v in fmap.items()}
    for seg in SEGS:
        dates = [str(x)[:10] for x in acc(seg, 'A4b')[1]['dates']]
        cells = pool1[pool1.d.isin(dates)].copy()
        cells['ti'] = cells.ticker.astype(str).str.lstrip('0')
        cells = cells.sort_values(['d', 'ti'], key=lambda s: s if s.name == 'd' else s.astype(int)).reset_index(drop=True)
        for form in FORMS:
            z = np.load(P('accounts', 'P', seg, 'masks_%s.npz' % form), allow_pickle=False)
            rowsm = [str(x) for x in z['rows']]; nc = int(z['n'][0])
            if len(cells) != nc:
                record('VB07', '%s|%s' % (seg, form), None, None, flags='NOT_COMPUTABLE',
                       note='pool1 本段 %d 行 ≠ 掩码格数 %d：无格坐标（npz 只存 bits）' % (len(cells), nc)); continue
            bits = np.unpackbits(z['bits'][rowsm.index('C0|0.0')])[:nc].astype(bool)
            mine = set(zip(cells.d[bits], cells.ti[bits]))
            q = p2[form]; q['d'] = pd.to_datetime(q.tradeDate.astype(str)).dt.strftime('%Y-%m-%d'); q = q[q.d.isin(dates)]
            theirs = set(zip(q.d, q.ticker.astype(str).str.lstrip('0')))
            record('VB07', '%s|%s' % (seg, form), 'True', str(mine == theirs), note='掩码 %d 格 / pool2 %d 行；仅掩码 %d 仅 pool2 %d' % (len(mine), len(theirs), len(mine - theirs), len(theirs - mine)))
    # VB08 种子重放（只重放 u 的哈希约定）
    sj = jload(P('stage0', 'replay', 'serial.json'))
    paths = sj['paths'] if isinstance(sj['paths'], dict) else json.loads(sj['paths'].replace("'", '"'))
    ok_k = []
    for p, v in sorted(paths.items(), key=lambda kv: int(kv[0])):       # 键规则转录自 engine_contract / e6j_stage0_replay.py:67 文本（未 import）
        s = json.dumps(['E6j.stage0.replay', 'R1|K_rar20|low_bad', 'R1', 'native', 'R-SCORE-IID', int(p)], sort_keys=True, separators=(',', ':'), ensure_ascii=True)
        k = int.from_bytes(hashlib.blake2b(s.encode('ascii'), digest_size=8).digest(), 'big')
        ok_k.append(str(k) == str(v['key']))
    record('VB08', 'replay_path_keys', 'True', str(all(ok_k) and len(ok_k) == 8), flags='STOCHASTIC',
           note='%d 条路径的 blake2b-64 规范键独立重算 = serial.json 所记；掩码 / 权重 / net8 哈希需跑引擎，本程序不重放（Stage 0 Z5 / Z6 已核 serial / 并行 / 续跑逐位相同）；generator=%s' % (len(ok_k), sj.get('generator')))


def main():
    t0 = time.time()
    parts = [('VA', VA), ('VB', VB), ('VC', VC), ('VD', VD), ('VE', VE), ('LEDGER', LEDGER), ('VBL', VB_LEDGER)]
    for name, fn in parts:
        if ONLY and name not in ONLY:
            continue
        log('start %s' % name)
        try:
            fn()
        except Exception as e:
            import traceback
            OUT.append(dict(probe_id=name, sub_id='__exception__', expected='', recomputed='', diff='', verdict='NOT_COMPUTABLE', flags='ERROR',
                            note=traceback.format_exc()[-800:], inputs='', function=name))
            log('ERROR %s %s' % (name, e))
        log('done %s (%d rows so far)' % (name, len(OUT)))
    df = pd.DataFrame(OUT)
    tag = '' if not ONLY else '_' + '_'.join(ONLY)
    out = os.path.join(VER, 'probe_results%s.csv' % tag)
    tmp = out + '.tmp'; df.to_csv(tmp, index=False); os.replace(tmp, out)
    with open(os.path.join(VER, 'verify%s.log' % tag), 'w', encoding='utf-8') as f:
        f.write('\n'.join(LOG) + '\nprogram sha256 %s\nwall %.0fs\n' % (sha(os.path.abspath(__file__)), time.time() - t0))
    print(df.verdict.value_counts().to_dict(), df['flags'].value_counts().to_dict())


def _cells(line):
    """Markdown 表行 → 单元格；只在未转义的 | 处切分，并还原转义竖线。"""
    s = line.strip()
    s = s[1:] if s.startswith('|') else s
    s = s[:-1] if (s.endswith('|') and not s.endswith('\\|')) else s
    return [c.strip().replace('\\|', '|') for c in re.split(r'(?<!\\)\|', s)]


if __name__ == '__main__':
    main()
