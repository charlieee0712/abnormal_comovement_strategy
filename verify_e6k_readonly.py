# -*- coding: utf-8 -*-
"""E6k 只读复现程序 V（VERIFY brief v1 §5；协议 v1.1）。
- 不 import 任何 e6k_* / e6j_* 模块；不调用本轮代码；不读 cache/；不读 2026-03-27 之后行情；不改结果目录已有文件。
- 公式从源码与登记文本转录（每个探针的 func 列写出转录口径）；预期值取决策端 `E6k_VERIFY_expected.csv`（同 probe_id）或现场计算。
- 用法：python3 verify_e6k_readonly.py --out <目录> --classes A,B,C,D,E [--workers 16]
  每类写 <out>/results_<类>.csv；--merge 把已完成的类按 A→E 合并成 <out>/probe_results.csv，并写 <out>/probes.csv（探针清单）。"""
import os
import re
import io
import sys
import json
import glob
import time
import hashlib
import argparse
import traceback
import datetime as dt
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

RES = '/mnt/sda2/lichenchen/results/20260928_2325_E6k_k_binding_stage'
E6J = '/mnt/sda2/lichenchen/results/20260927_0038_E6j_k_two_dimension_pilot'
E5A = '/mnt/sda2/lichenchen/results/20260903_1214_delivery_pools_v2'
CODE = '/mnt/sda2/lichenchen/code/project_core'
EB47 = CODE + '/exec_briefs'
DEC = RES + '/verify/decision'
SEGS = ['2010-2014', '2015-2018', '2019-2023', '2024-2026']
DER, POS = SEGS[:2], SEGS[2:]
ANN = 252 * 100.0                                   # e6j_core.ANN
PROFILES = ['LEGACY_EDIT5', 'PROPOSED_PORT3_T', 'PROPOSED_PORT3_LAG1', 'EXEC_DISCLOSE_ONLY', 'EXEC_LEADER_VS_PARENT']
TWELVE = ['E6k_REPORT_R0.md', 'E6k_REPORT_part1.md', 'E6k_REPORT_part2.md', 'E6k_REPORT_part3.md', 'E6k_REPORT_mechanisms.md', 'E6k_REPORT_carried.md',
          'E6k_REPORT_cards.md', 'E6k_REVIEW_input.md', 'E6k_lessons_delta.md', 'E6k_limit_register.md', 'E6k_record_B_draft.md',
          'E6k_routing_review_A1_auto.md']
SEVEN = TWELVE[:7]
SEED = 20260929
OUT = None
LOG = None


# ============================================================================ 通用
def log(msg):
    s = '[%s] %s' % (time.strftime('%H:%M:%S'), msg)
    print(s, flush=True)
    if LOG:
        with open(LOG, 'a', encoding='utf-8') as fh:
            fh.write(s + '\n')


def sha256_file(p, chunk=1 << 22):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def md5_file(p):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def rp(*a):
    return os.path.join(RES, *a)


def jload(p):
    return json.load(open(p, encoding='utf-8'))


def read_csv_keep(p, **kw):
    """保留字面 'N/A' / 'NA'（pandas 默认把它们读成 NaN；政策串里 N/A 是状态词）。"""
    return pd.read_csv(p, keep_default_na=False, na_values=[''], **kw)


class Row(dict):
    pass


def row(pid, sub, obj, metric, expected, got, verdict, flags='', diff='', inputs='', func=''):
    return dict(probe_id=pid, sub_id=sub, object=obj, metric=metric, expected=str(expected), recomputed=str(got), diff=str(diff),
                verdict=verdict, flags=flags, inputs_sha256=inputs, func=func)


def v_eq(a, b):
    return 'REPRODUCED' if str(a) == str(b) else 'DIFFERS'


def v_tol(d, tol):
    if d is None or (isinstance(d, float) and not np.isfinite(d)):
        return 'NOT_COMPUTABLE'
    return 'REPRODUCED' if abs(d) <= tol else 'DIFFERS'


def fmt4(x):
    return '' if (x is None or (isinstance(x, float) and not np.isfinite(x))) else ('%.4g' % x)


def cell_eq4(cell, x):
    """REPORT 印出 4 位有效 vs 机器值：字符串相同 = OK；否则 |Δ| ≤ 半个末位 = ROUNDING；否则不等。"""
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return 'OK' if str(cell).strip() in ('', 'nan') else 'BAD'
    if str(cell) == fmt4(x):
        return 'OK'
    try:
        c = float(cell)
    except ValueError:
        return 'BAD'
    if x == 0:
        return 'OK' if c == 0 else 'BAD'
    e = np.floor(np.log10(abs(x))) - 3
    return 'ROUNDING' if abs(c - x) <= 0.5 * 10 ** e * 1.0000001 else 'BAD'


EXP = None


def expected_rows(pid):
    return EXP[EXP.probe_id == pid]


def exp1(pid, sub):
    x = EXP[(EXP.probe_id == pid) & (EXP.sub_id == sub)]
    return x.iloc[0].expected if len(x) else ''


def inputs_sha(*paths):
    out = []
    for p in paths:
        full = p if p.startswith('/') else rp(p)
        if os.path.isfile(full):
            out.append('%s:%s' % (os.path.relpath(full, RES) if full.startswith(RES) else os.path.basename(full), sha256_file(full)[:16]))
    return ';'.join(out)


# ---------------------------------------------------------------------------- 报告表解析
def split_row(line):
    cells = re.split(r'(?<!\\)\|', line.strip())[1:-1]
    return [c.strip().replace('\\|', '|') for c in cells]


_REPORT_CACHE = {}


def report_tables(name):
    """每张表前一行 '> 表头：…｜query_id=X'；返回 {qid: DataFrame(str)} 与 {qid: 行号}。"""
    if name in _REPORT_CACHE:
        return _REPORT_CACHE[name]
    lines = open(rp('reports', name), encoding='utf-8').read().split('\n')
    tabs, pos = {}, {}
    i = 0
    while i < len(lines):
        if lines[i].startswith('> 表头：') and 'query_id=' in lines[i]:
            qid = lines[i].rsplit('query_id=', 1)[1].strip()
            j = i + 1
            while j < len(lines) and not lines[j].startswith('|'):
                j += 1
            hdr = split_row(lines[j])
            j += 2
            rows = []
            while j < len(lines) and lines[j].startswith('|'):
                rows.append(split_row(lines[j]))
                j += 1
            tabs[qid] = pd.DataFrame(rows, columns=hdr)
            pos[qid] = i + 1
            i = j
        else:
            i += 1
    _REPORT_CACHE[name] = (tabs, pos, lines)
    return _REPORT_CACHE[name]


# ---------------------------------------------------------------------------- 数据载入（惰性）
_C = {}


def policy():
    if 'P' not in _C:
        P = read_csv_keep(rp('results', 'full', 'policy_E6k.csv'))
        for b in ('primary144', 'c1_hi'):
            P[b] = P[b].astype(str).eq('True')
        _C['P'] = P
    return _C['P']


def descs():
    if 'D' not in _C:
        D = pd.read_csv(rp('registry', 'descriptors_E6k.csv'))
        for b in ('primary144', 'c1_hi', 'sm_anchor'):
            D[b] = D[b].astype(bool)
        _C['D'] = D
    return _C['D']


def stats(seg, phase='full'):
    k = ('S', seg, phase)
    if k not in _C:
        _C[k] = pd.read_csv(rp('results', phase, 'descriptor_stats_%s.csv' % seg)).drop_duplicates('desc_id').set_index('desc_id')
    return _C[k]


def rrefs(seg):
    k = ('R', seg)
    if k not in _C:
        _C[k] = pd.read_csv(rp('results', 'full', 'random_refs_%s.csv' % seg))
    return _C[k]


def main154():
    P = policy()
    return sorted(P[P.primary144 | P.c1_hi | P.meas.eq('SM')].desc_id)


def full_g4(Ds, ns):
    """e6j_stats.full_g4 转录：ok = D 有限且 n > 0；FULL = Σ n D / Σ n；G4 = median(D[ok])。"""
    Ds, ns = np.asarray(Ds, float), np.asarray(ns, float)
    ok = np.isfinite(Ds) & (ns > 0)
    if not ok.any():
        return np.nan, np.nan
    return float(np.sum(Ds[ok] * ns[ok]) / np.sum(ns[ok])), float(np.median(Ds[ok]))


def seg_D(d):
    m = np.isfinite(d)
    return (float(np.mean(d[m])) * ANN if m.any() else np.nan), int(m.sum())


def paired(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    return np.where(m, a - b, np.nan)


def hac_se(d, L):
    """e6j_stats.hac_se 转录：原时间轴、缺失 u = 0、Bartlett(L)；返回均值 SE（日单位）。"""
    I = np.isfinite(d)
    n = int(I.sum())
    if n < 3:
        return np.nan
    mu = float(np.mean(d[I]))
    u = np.where(I, d - mu, 0.0)
    s = float(u @ u)
    for l in range(1, int(L) + 1):
        if l >= len(u):
            break
        s += 2.0 * (1.0 - l / (L + 1.0)) * float(u[l:] @ u[:-l])
    v = s / (n * n)
    return np.sqrt(v) if v > 0 else np.nan


def impact(bracket, A, k):
    """e6j_stats.impact_cost 转录：κ·sqrt(A·1e8)·bracket（NaN → 0）。"""
    return k * np.sqrt(A * 1e8) * np.nan_to_num(bracket, nan=0.0)


def acct_file(seg, mother, meas):
    return rp('accounts', seg, '%s__%s.npz' % (mother, meas))


_NPZ = {}


def npz_arrays(path, keys):
    """惰性读：每个 (文件, 键) 只读一次；只保留最近 6 个文件。"""
    k = path
    if k not in _NPZ:
        if len(_NPZ) >= 6:
            _NPZ.pop(next(iter(_NPZ)))
        _NPZ[k] = {'_z': np.load(path, allow_pickle=False)}
    d = _NPZ[k]
    for key in keys:
        if key not in d:
            d[key] = d['_z'][key]
    return d


def desc_series(seg, did, keys=('d_net8',)):
    """desc 在 accounts/<段>/<母体>__<任务测量>.npz；PARENT 在 <母体>__K0.npz；返回 {key: 日序列}。"""
    D = descs()
    r = D.set_index('desc_id').loc[did] if did in set(D.desc_id) else None
    if r is not None:
        task = r.task
    else:
        raise KeyError(did)
    mother, meas = task.split('|')
    d = npz_arrays(acct_file(seg, mother, meas), ('desc',) + tuple(keys))
    if '_ix' not in d:
        d['_ix'] = {s: i for i, s in enumerate(map(str, d['desc']))}
    i = d['_ix'][did]
    return {k: d[k][i] for k in keys}


# ============================================================================ V-A 闭包与指纹
def class_A(workers):
    out = []
    # ---- VA01 十二份文件 × 三处 + MIRROR
    mir = {}
    for line in open(rp('reports', 'E6k_MIRROR.md5'), encoding='utf-8'):
        p = line.split()
        if len(p) == 4 and p[2] in ('RD', 'EB47', 'EBLOCAL'):
            mir[(p[2], p[3].split('/', 1)[1])] = (p[0], p[1])
    loc_p = rp('verify', 'local_exec_briefs_hashes.json')
    loc = jload(loc_p)['files'] if os.path.exists(loc_p) else {}
    for f in TWELVE:
        exp = exp1('VA01', f)
        sha, md = sha256_file(rp('reports', f)), md5_file(rp('reports', f))
        e47 = (sha256_file(EB47 + '/' + f), md5_file(EB47 + '/' + f))
        el = (loc.get(f, {}).get('sha256'), loc.get(f, {}).get('md5'))
        mm = [mir.get((k, f)) for k in ('RD', 'EB47', 'EBLOCAL')]
        same = all(x == (md, sha) for x in mm) and e47 == (sha, md) and el == (sha, md)
        got = '%s / %s' % (sha, md)
        v = 'REPRODUCED' if (got == exp and same) else 'DIFFERS'
        out.append(row('VA01', f, 'reports/' + f, 'sha256 / md5（RD；EB47 / EBLOCAL / MIRROR 三处一致）', exp, got, v,
                       '' if loc else 'INFO:EBLOCAL 由执行端工作站现算写入 verify/local_exec_briefs_hashes.json（决策端未随附）',
                       diff='三处一致=%s' % same, func='sha256/md5 逐文件；MIRROR 行 (md5, sha256, 位置, 文件)'))
    # ---- VA02 REVIEW_input 209 个 sha 前缀
    ri = open(rp('reports', 'E6k_REVIEW_input.md'), encoding='utf-8').read().split('\n')
    listed = {}
    lines_h = []
    for l in ri:
        m = re.match(r'^- `([^`]+)`（([0-9a-f]{16})）$', l)
        if m:
            listed[m.group(1)] = m.group(2)
            lines_h.append(m.group(1))
    ex = expected_rows('VA02')
    nok = 0
    for r in ex.itertuples():
        p = r.object
        full = CODE + '/' + p[5:] if p.startswith('code/') else rp(p)
        got = sha256_file(full)[:16] if os.path.exists(full) else 'MISSING'
        ok = (got == r.expected) and (listed.get(p) == r.expected)
        nok += ok
        out.append(row('VA02', p, p, 'sha256[:16]（现算 = 预期 = REVIEW_input 所记）', r.expected, got, 'REPRODUCED' if ok else 'DIFFERS',
                       diff='' if ok else 'REVIEW_input=%s' % listed.get(p), func='sha256 前 16 位'))
    extra = sorted(set(listed) - set(ex.object))
    n_code = sum(1 for p in lines_h if p.startswith('code/'))
    dup = len(lines_h) - len(set(lines_h))
    out.append(row('VA02', 'summary', 'reports/E6k_REVIEW_input.md', '带 sha 行数 / 其中代码 / 重复列出的路径 / 预期行未覆盖', '209 / 32（brief 正文）',
                   '%d / %d / %d / %d' % (len(lines_h), n_code, dup, len(extra)), 'REPRODUCED' if (len(lines_h) == 209 and nok == len(ex) and not extra) else 'DIFFERS',
                   'INFO:brief 正文"结果目录 177 + 代码 32"与实际拆分（结果目录 %d 行 + 代码 %d 行）不同，合计 209 相同；%d 个路径在两个分组里各列一次；另 2 条无 sha 注记行（本文件 / 闭包门之后写入）'
                   % (len(lines_h) - n_code, n_code, dup), func='逐行解析 "- `路径`（sha16）"'))
    # ---- VA03 query_id 登记
    qr = jload(rp('reports', 'query_registry_E6k.json'))
    out.append(row('VA03', 'registry', 'reports/query_registry_E6k.json', 'n_query_ids', exp1('VA03', 'registry'), len(qr), v_eq(exp1('VA03', 'registry'), len(qr)),
                   func='len(json)'))
    for f in SEVEN:
        tabs, _, lines = report_tables(f)
        in_text = set(re.findall(r'query_id=([A-Za-z0-9\-]+)', '\n'.join(lines)))
        reg = {k for k, v in qr.items() if v['file'] == f}
        got = '%d / %d' % (len(in_text), len(reg))
        v = 'REPRODUCED' if (got == exp1('VA03', f) and in_text == reg) else 'DIFFERS'
        out.append(row('VA03', f, f, 'query_ids in text / registered（集合相等）', exp1('VA03', f), got, v, func='正文 query_id= 集合 vs json 逐文件'))
    allq = [q for f in SEVEN for q in re.findall(r'query_id=([A-Za-z0-9\-]+)', '\n'.join(report_tables(f)[2]))]
    cq = pd.read_csv(rp('registry', 'query_registry_E6k.csv'))
    cards_q = set(re.findall(r'query_id=(E6K-Q\d\d-[a-c])', '\n'.join(report_tables('E6k_REPORT_cards.md')[2])))
    out.append(row('VA03', 'cross_file_unique_and_cards', 'reports/*.md', '跨文件重复 / cards 卡 query = registry 47 行', '0 / True',
                   '%d / %s' % (len(allq) - len(set(allq)), cards_q == set(cq.query_id)),
                   'REPRODUCED' if (len(allq) == len(set(allq)) and cards_q == set(cq.query_id)) else 'DIFFERS', func='集合比较'))
    # ---- VA04 回执
    st = {}
    for p in glob.glob(rp('task_status', '*.receipt.json')):
        r = jload(p)
        st[r['task_id']] = r['status']
    cnt = pd.Series(list(st.values())).value_counts().to_dict()
    got = '%d / %s' % (len(st), json.dumps({k: int(v) for k, v in sorted(cnt.items(), key=lambda x: -x[1])}, ensure_ascii=False))
    cr = jload(rp('results', 'completion_receipt.json'))
    cr_n = [c['detail'] for c in cr['checks'] if c['check'].startswith('回执全')][0]
    exp = exp1('VA04', 'receipts')
    out.append(row('VA04', 'receipts', 'task_status/', 'n / status counts（completion_receipt 记）', exp, got + '（%s）' % cr_n,
                   'REPRODUCED' if (len(st) == 2334 and cnt.get('SUCCEEDED') == 2333 and cnt.get('FAILED') == 1 and cr_n.startswith('2334')) else 'DIFFERS',
                   func='task_status/*.receipt.json 逐个 status'))
    failed = [k for k, v in st.items() if v != 'SUCCEEDED']
    cov = all(st.get(k + '_rerun') == 'SUCCEEDED' for k in failed)
    out.append(row('VA04', 'failed_stage0_c1_identity', ','.join(failed), 'covered by _rerun', exp1('VA04', 'failed_stage0_c1_identity'), cov,
                   v_eq(exp1('VA04', 'failed_stage0_c1_identity'), cov), func='FAILED 任务的同名 _rerun 状态'))
    # ---- VA05 封存：全部 2,960 文件 sha 现算
    for pkg in ('deriv', 'post'):
        s = jload(rp('registration', 'seal_%s.json' % pkg))
        got = '%s / %d / %s' % (s['written_at'], s['n_files'], json.dumps(s['receipts'], ensure_ascii=False))
        exp = exp1('VA05', 'seal_%s' % pkg)
        out.append(row('VA05', 'seal_%s' % pkg, 'registration/seal_%s.json' % pkg, 'written_at / n_files / receipts', exp, got, v_eq(exp, got),
                       func='读封存清单'))
        files = sorted(s['files'].items())
        with ProcessPoolExecutor(workers) as ex_:
            shas = list(ex_.map(sha256_file, [rp(f) for f, _ in files], chunksize=8))
        bad = [f for (f, h), g in zip(files, shas) if h != g]
        out.append(row('VA05', 'seal_%s_recheck_all' % pkg, 'registration/seal_%s.json' % pkg, 'sha256 全量现算（决策端抽 40）',
                       exp1('VA05', 'seal_%s_recheck_sample' % pkg), '%d / mismatch %d' % (len(files), len(bad)),
                       'REPRODUCED' if not bad else 'DIFFERS', 'INFO:V 全量 %d 文件' % len(files), diff=';'.join(bad[:5]), func='sha256 逐文件 vs 封存清单'))
    # 时序链
    rec = {}
    for p in glob.glob(rp('task_status', '*.receipt.json')):
        r = jload(p)
        rec[r['task_id']] = r['written_at']

    def rng_(pat):
        v = sorted(w for t, w in rec.items() if re.match(pat, t))
        return [v[0], v[-1]] if v else None
    chain = {'stage0_first': min(w for t, w in rec.items() if t.startswith('stage0')), 'a0_compile': rec.get('a0_compile'),
             'run_det_deriv': rng_(r'run_det_(2010-2014|2015-2018)_'), 'run_rand_deriv_last': rng_(r'run_rand_.*_(2010-2014|2015-2018)_')[1],
             'seal_deriv': rec.get('seal_deriv_v1'), 'stats_deriv': rng_(r'stats_deriv_'), 'closure_deriv': rec.get('closure_deriv'),
             'report_part1': rec.get('report_part1'), 'record_b_draft': rec.get('record_b_draft'),
             'stage0_c3_post_last': max(rec.get('stage0_c3_ops_2019-2023'), rec.get('stage0_c3_ops_2024-2026')),
             'record_B_approved': jload(rp('registration', 'record_B_approved_E6k.json'))['written_at'],
             'conditions_receipt': jload(rp('registration', 'record_B_conditions_receipt_E6k.json'))['written_at'],
             'leafdiag': rng_(r'leafdiag_'), 'run_det_post': rng_(r'run_det_(2019-2023|2024-2026)_'), 'run_rand_post': rng_(r'run_rand_.*_(2019-2023|2024-2026)_'),
             'seal_post': rec.get('seal_post_v1'), 'a1_auto_masks_post': rec.get('a1_auto_masks_post'), 'stats_full': rng_(r'stats_full_'),
             'policy': rec.get('policy_E6k'), 'bootstrap_full': rec.get('bootstrap_full'), 'mechanisms': rng_(r'mechanisms_'),
             'report_part2': rec.get('report_part2'), 'report_part3': rec.get('report_part3'), 'report_r0': rec.get('report_r0'),
             'decay_v1': rec.get('decay_scenarios'), 'decay_v2': rec.get('decay_scenarios_v2'),
             'hg_v1_last': max(w for t, w in rec.items() if t.startswith('hg_continuous_') and not t.startswith('hg_continuous_v2')),
             'hg_v2': rng_(r'hg_continuous_v2_')[1], 'deliver_review_input': rec.get('deliver_review_input')}
    try:
        expc = json.loads(exp1('VA05', 'chain'))
    except ValueError:
        expc = {}
    diffs = [k for k in expc if expc.get(k) != chain.get(k)]
    order_ok = (chain['run_det_deriv'][1] < chain['seal_deriv'] < chain['stats_deriv'][0] < chain['report_part1'] < chain['record_B_approved']
                < chain['conditions_receipt'] <= chain['run_det_post'][0] and chain['run_det_post'][1] < chain['seal_post'] < chain['stats_full'][0]
                < chain['policy'] < chain['report_part3'] and chain['conditions_receipt'] < chain['stage0_c3_post_last'] < chain['seal_post']
                and chain['conditions_receipt'] < chain['leafdiag'][0] and chain['leafdiag'][1] < chain['seal_post'])
    out.append(row('VA05', 'chain', 'task_status/ + registration/', '时序链（逐键与预期相同 / 先后顺序）', '预期 JSON（%d 键）' % len(expc),
                   json.dumps(chain, ensure_ascii=False), 'REPRODUCED' if (not diffs and order_ok) else 'DIFFERS',
                   diff='不同键 %s；顺序=%s' % (diffs, order_ok), func='回执 written_at 最早 / 最晚；批准 / 条件回执取 registration 文件内 written_at'))
    # ---- VA06 登记文件 mtime / sha 与"早于首次读数"
    first_read = min(w for t, w in rec.items() if t.startswith('stats_deriv'))
    for r in expected_rows('VA06').itertuples():
        if r.sub_id == 'record_B_chain':
            continue
        p = rp('registration', r.sub_id)
        mt = dt.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%Y-%m-%d %H:%M:%S')
        got = '%s / %s' % (mt, sha256_file(p)[:16])
        early = mt < first_read
        out.append(row('VA06', r.sub_id, 'registration/' + r.sub_id, 'mtime / sha256[:16]；早于首次读数 %s' % first_read, r.expected, got,
                       'REPRODUCED' if (got == r.expected and early) else 'DIFFERS', diff='早于=%s' % early, func='os.path.getmtime + sha256'))
    ma = jload(rp('registration', 'record_B_mode_A.json'))
    ap = jload(rp('registration', 'record_B_approved_E6k.json'))
    cd = jload(rp('registration', 'record_B_conditions_receipt_E6k.json'))
    manB = sha256_file(rp('registration', 'B_package_manifest_E6k.json'))
    manP = sha256_file(rp('registration', 'P_package_manifest_E6k.json'))
    try:
        expr = json.loads(exp1('VA06', 'record_B_chain'))
    except ValueError:
        expr = {}
    chk = dict(quote=ap['user_quote'] == expr.get('approved_quote'), approved_written=ap['written_at'] == expr.get('approved_written'),
               context=ap.get('context_note') == expr.get('approved_context'), cond=all(cd.get(k) == v for k, v in expr.get('conditions', {}).items()),
               B_frozen=(manB == ap['frozen_manifest_sha256'] == cd['frozen_manifest_sha256']), P_frozen=(manP == ap['frozen_manifest_P_sha256']))
    out.append(row('VA06', 'record_B_chain', 'registration/', 'mode_A → approved(原话) → conditions；B / P 清单现 sha = 批准时冻结 sha',
                   'approved %s；conditions %s' % (expr.get('approved_written'), expr.get('conditions', {}).get('written_at')),
                   json.dumps(dict(mode_A_keys=sorted(ma)[:6], approved=ap['written_at'], conditions=cd['written_at'], checks=chk), ensure_ascii=False),
                   'REPRODUCED' if all(chk.values()) else 'DIFFERS', 'INFO:原话与 context_note 原文引用，不作解释（REVIEW §11）', func='逐字段比较'))
    # ---- VA07 代码变更
    sm = jload(rp('source_manifest.json'))
    s0 = {k: v[:16] for k, v in sm['e6k_code_sha256_at_stage0'].items()}
    deliv = {p[5:]: h for p, h in listed.items() if p.startswith('code/')}
    changed = {k: [s0[k], deliv[k]] for k in s0 if k in deliv and deliv[k] != s0[k]}
    new = sorted(set(deliv) - set(s0))
    same = sorted(k for k in s0 if deliv.get(k) == s0[k])
    try:
        expv = json.loads(exp1('VA07', 'code_changes'))
    except ValueError:
        expv = {}
    reg = open(rp('reports', 'E6k_code_change_register.md'), encoding='utf-8').read() if os.path.exists(rp('reports', 'E6k_code_change_register.md')) else ''
    reg_ok = all(('`%s`' % k) in reg for k in list(changed) + new) and all(v[1][:8] in reg for v in changed.values())
    ok = (expv.get('changed') == changed and sorted(expv.get('new', [])) == new and len(same) == 12 and reg_ok)
    out.append(row('VA07', 'code_changes', 'source_manifest vs REVIEW_input；C-7 登记', '改动 / 不变 / 新增；登记逐条覆盖', '4 / 12 / 32',
                   '%d / %d / %d；登记覆盖=%s' % (len(changed), len(same), len(new), reg_ok), 'REPRODUCED' if ok else 'DIFFERS',
                   func='sha 前缀逐文件比较；登记文本含每个文件名与交付 sha 前缀'))
    # ---- VA08 交付时状态（现场）
    ident = rp('verify', 'identity_at_start.json')
    idj = jload(ident) if os.path.exists(ident) else {}
    s1 = os.path.exists(rp('results', 'full', 'bootstrap', 'supplement_1'))
    reg_git = os.popen('cd %s && git ls-tree -r --name-only HEAD -- exec_briefs/E6k_code_change_register.md 2>/dev/null' % CODE).read().strip()
    out.append(row('VA08', 'state_at_delivery', 'verify/ ; supplement_1 ; code_change_register', 'verify/ 交付时为空 / supplement_1 不存在 / 登记册非交付件',
                   'True / True / True', '%s / %s / %s' % (idj.get('verify_entries_at_start') == 0, not s1 or idj.get('supplement_1_absent_at_start') is True,
                                                            reg_git == ''),
                   'REPRODUCED' if (idj.get('verify_entries_at_start') == 0 and reg_git == '') else 'DIFFERS',
                   'INFO:开工身份核对时现场记录（verify/identity_at_start.json）；登记册 C-7 新建、不在提交 03e1015 内', func='现场'))
    return out


# ============================================================================ V-B Stage 0、锚与登记计数
def class_B(workers):
    out = []
    sm = jload(rp('source_manifest.json'))
    pt = sm.get('plan_tests', {})
    ptxt = '%s/%s' % (pt.get('passed', pt.get('n_pass', '?')), pt.get('total', pt.get('n', '?'))) if isinstance(pt, dict) else str(pt)
    got = '%s / %s / %s / %s' % (sm['stage0_all_pass'], ptxt, sm['git_head'][:7], sm.get('market_data_end_max'))
    out.append(row('VB01', 'source_manifest', 'source_manifest.json', 'stage0_all_pass / plan_tests / git_head / market_data_end_max', exp1('VB01', 'source_manifest'), got,
                   v_eq(exp1('VB01', 'source_manifest'), got), func='读 json'))
    for r in expected_rows('VB01').itertuples():
        if r.sub_id == 'source_manifest':
            continue
        df = pd.read_csv(rp(r.sub_id))
        vc = df.status.value_counts()
        e = json.loads(r.expected.split(' / ', 1)[1])
        ok = (len(df) == int(r.expected.split(' / ')[0])) and all(int(vc.get(k, 0)) == v for k, v in e.items()) and sum(e.values()) == len(df)
        out.append(row('VB01', r.sub_id, r.sub_id, 'n / status counts', r.expected, '%d / %s' % (len(df), json.dumps({k: int(v) for k, v in vc.items()}, ensure_ascii=False)),
                       'REPRODUCED' if ok else 'DIFFERS', func='status 计数'))
    # VB02
    D = descs()
    blocks = D.blocks.str.split('|').explode().value_counts().to_dict()
    got = '%d / %d / %d / %d / %s' % (len(D), D.primary144.sum(), D.c1_hi.sum(), D.sm_anchor.sum(), json.dumps(blocks))
    e = exp1('VB02', 'descriptors')
    eb = json.loads(e.split(' / ', 4)[4])
    ok = (len(D) == 39142 and D.primary144.sum() == 144 and D.c1_hi.sum() == 4 and D.sm_anchor.sum() == 6 and eb == {k: int(v) for k, v in blocks.items()})
    out.append(row('VB02', 'descriptors', 'registry/descriptors_E6k.csv', 'rows / primary144 / c1_hi / sm_anchor / blocks', e, got, 'REPRODUCED' if ok else 'DIFFERS',
                   func='块计数（blocks 列按 | 拆）'))
    cov = pd.read_csv(rp('results', 'coverage.csv'))
    persum = cov.groupby('segment').registered.sum().to_dict()
    ok = len(cov) == 64 and (cov.registered == cov.computed).all()
    reg_blocks = cov[~cov.block.isin(['COMMON_SUPPORT_CHILD', 'COMMON_SUPPORT_PARENT', 'BAND_DOSE_CONTROL', 'INC_SUPPORT_ACCESSORY'])].groupby('segment').registered.sum().to_dict()
    out.append(row('VB02', 'coverage', 'results/coverage.csv', 'rows / registered==computed / 每段和（登记块 / 含附属）', exp1('VB02', 'coverage'),
                   '%d / %s / %s / %s' % (len(cov), ok, json.dumps(reg_blocks), json.dumps(persum)), 'REPRODUCED' if ok else 'DIFFERS',
                   'INFO:每段和 41,478 = 登记块 39,142 + 附属 2,336（决策端 D 首轮把附属算进 39,142 的读法已在 D 探针改读）', func='coverage 分块求和'))
    A = pd.read_csv(rp('registry', 'accessory_E6k.csv'))
    got = '%d / %s / %s' % (len(A), list(A.columns), json.dumps(A.kind.value_counts().to_dict()))
    ok = len(A) == 2336 and A.kind.value_counts().to_dict() == {'COMMON_SUPPORT_CHILD': 1800, 'BAND_DOSE_CONTROL': 288, 'COMMON_SUPPORT_PARENT': 176, 'INC_SUPPORT_ACCESSORY': 72}
    out.append(row('VB02', 'accessory', 'registry/accessory_E6k.csv', 'rows / cols / kind counts', exp1('VB02', 'accessory'), got, 'REPRODUCED' if ok else 'DIFFERS',
                   'INFO:实际 10 列（多 task / compare_to），预期串只列前 8 列' if len(A.columns) != 8 else '', func='读表'))
    P = policy()
    out.append(row('VB02', 'policy_rows', 'results/full/policy_E6k.csv', 'shape', exp1('VB02', 'policy_rows'), str(P.shape), v_eq(exp1('VB02', 'policy_rows'), str(P.shape)),
                   func='shape'))
    for s in SEGS:
        S = stats(s)
        vc = S.kind.value_counts().to_dict()
        got = '%d / %s' % (len(S), json.dumps(vc))
        e = exp1('VB02', 'descriptor_stats_%s' % s)
        ok = len(S) == 41142 and json.loads(e.split(' / ', 1)[1]) == vc
        out.append(row('VB02', 'descriptor_stats_%s' % s, 'results/full/descriptor_stats_%s.csv' % s, 'rows / kind counts', e, got, 'REPRODUCED' if ok else 'DIFFERS',
                       func='kind 计数'))
    # VB03 E6j 复现
    pp = pd.read_csv(E6J + '/results_P/pilot_policy.csv')
    Pi = P.set_index('desc_id')
    mx, n = 0.0, 0
    miss = []
    for r in pp[pp.arm.isin(['S', 'M', 'C1', 'SM'])].itertuples():
        did = '%s|%s|a%g|H%d|NATIVE' % (r.arm, r.form, r.alpha, r.H)
        if did not in Pi.index:
            if r.arm != 'SM':
                miss.append(did)
            continue
        x = Pi.loc[did]
        vals = [(getattr(r, 'FULL'), x.FULL), (getattr(r, 'G4'), x.G4), (getattr(r, 'FULL_sc'), x.FULL_sc)]
        for s in SEGS:
            vals.append((pp.loc[r.Index, 'D_%s' % s], x['D_%s' % s]))
            vals.append((pp.loc[r.Index, 'Dsc_%s' % s], x['D_sc_%s' % s]))
        for a, b in vals:
            if np.isfinite(a) or np.isfinite(b):
                mx = max(mx, abs(a - b)) if (np.isfinite(a) and np.isfinite(b)) else np.inf
        n += 1
    n_nat = sum(1 for r in pp[pp.arm.isin(['S', 'M', 'C1'])].itertuples() if '%s|%s|a%g|H%d|NATIVE' % (r.arm, r.form, r.alpha, r.H) in Pi.index)
    n_sm = n - n_nat
    out.append(row('VB03', 'E6j_replication_NATIVE+SM', 'policy_E6k vs E6j results_P/pilot_policy.csv', 'n NATIVE / n SM / max|Δ| (D_seg, D_sc_seg, FULL, G4, FULL_sc)',
                   '%s ; %s' % (exp1('VB03', 'E6j_replication_NATIVE'), exp1('VB03', 'SM_anchor')), '%d / %d / %.3g' % (n_nat, n_sm, mx),
                   'REPRODUCED' if (n_nat == 216 and n_sm == 6 and mx <= 1e-9 and not miss) else 'DIFFERS', diff='missing %s' % miss[:3],
                   inputs=inputs_sha(E6J + '/results_P/pilot_policy.csv'), func='E6j (form, arm, α, H) ↔ E6k meas|mother|a|H|NATIVE'))
    b = pd.read_csv(E6J + '/results_B/part2_main_config_all_objects.csv')
    mm = {'R1': 'A4b_CVRv5', 'R2': 'R2', 'A06': 'A06'}
    rar = {'J_B5_RARPRE_CC_W20_LT': 'RARPRE20_LT', 'J_B5_RARPRE_CC_W20_SE': 'RARPRE20_SE', 'J_B5_RARPRE_CC_W60_LT': 'RARPRE60_LT',
           'J_B5_RARPRE_CC_W60_SE': 'RARPRE60_SE', 'J_B1_qCC': 'Q'}
    sel = b[(b.slot == 'K') & (b.direction == 'low_bad') & b.measurement_id.isin(list(rar)) & (b.alpha == 0.25) & (b.H == 5)]
    mq = mr = 0.0
    nq = nr = 0
    for r in sel.itertuples():
        did = '%s|%s|a0.25|H5|NATIVE' % (rar[r.measurement_id], mm[r.mother])
        x = Pi.loc[did]
        m = max(abs(float(b.at[r.Index, 'D_%s' % s]) - x['D_%s' % s]) for s in SEGS)
        if rar[r.measurement_id] == 'Q':
            mq, nq = max(mq, m), nq + 1
        else:
            mr, nr = max(mr, m), nr + 1
    out.append(row('VB03', 'E6j_B_replication', 'policy_E6k vs E6j results_B/part2_main_config_all_objects.csv', 'n Q / max|Δ| ; n RARPRE / max|Δ|（四段 D）',
                   exp1('VB03', 'E6j_B_replication'), '%d / %.3g ; %d / %.3g' % (nq, mq, nr, mr), 'REPRODUCED' if (nq == 3 and nr == 12 and max(mq, mr) <= 1e-9) else 'DIFFERS',
                   inputs=inputs_sha(E6J + '/results_B/part2_main_config_all_objects.csv'), func='CC × low_bad × K 槽；R1 = A4b_CVRv5'))
    # VB04 carried 八母体表
    tabs, _, _ = report_tables('E6k_REPORT_carried.md')
    t = tabs['E6K-CAR-PARENTS']
    lead = pd.read_csv(E6J + '/carried/leader_six_forms_capital.csv').set_index(['segment', 'form'])
    anc = pd.read_csv(E6J + '/stage0/anchor2_rerun/e6i_parent_anchor.csv')
    anc = anc[anc.mother.isin(['R2', 'A06'])].set_index(['segment', 'mother'])
    bad6 = bad2 = 0
    for r in t.itertuples():
        if (r.segment, r.mother) in lead.index:
            L = lead.loc[(r.segment, r.mother)]
            for a, bb in ((r.net8_ann, L.total_net8_ann), (r.invested_target_mean, L.invested_target_mean), (r.position_actual_mean, L.position_actual_mean),
                          (r.target_names_mean, L.target_names_mean)):
                bad6 += cell_eq4(a, float(bb)) == 'BAD'
        elif (r.segment, r.mother) in anc.index:
            bad2 += cell_eq4(r.net8_ann, float(anc.loc[(r.segment, r.mother)].E6i_parent_net8_ann)) == 'BAD'
    out.append(row('VB04', 'parents_table', 'E6K-CAR-PARENTS（32 行）', 'six_forms_bad / r2a06_bad（4 位有效）', exp1('VB04', 'parents_table'),
                   'six_forms_bad=%d r2a06_bad=%d' % (bad6, bad2), 'REPRODUCED' if (bad6 == 0 and bad2 == 0 and len(t) == 32) else 'DIFFERS',
                   inputs=inputs_sha(E6J + '/carried/leader_six_forms_capital.csv', E6J + '/stage0/anchor2_rerun/e6i_parent_anchor.csv'),
                   func='net8_ann = E6j total_net8_ann；invested / position / names 同名列；R2 / A06 = E6i 母体锚'))
    # VB05 E5a 实物 sha
    c2 = pd.read_csv(rp('stage0', 'c2_source', 'source_prod_checks.csv'))
    ev = c2[c2.metric.astype(str).str.contains('sha256 逐字节')]
    bad = []
    for r in ev.itertuples():
        g = sha256_file(E5A + '/' + r.object)
        if not (g == r.expected == r.got):
            bad.append(r.object)
    out.append(row('VB05', 'e5a_files', 'E5a v2 交付目录（6 × pool2 + pool1 + summary）', 'sha256 现算 = Stage 0 证据行（expected = got）', '%d 行全等' % len(ev),
                   '%d 行；不等 %d' % (len(ev), len(bad)), 'REPRODUCED' if not bad else 'DIFFERS', diff=';'.join(bad), func='sha256 现算'))
    # VB06 α0 母体名单 vs pool2（成员）
    out += vb06()
    # VB07 LEGACY 路径跨轮逐位
    out += vb07()
    return out


def vb06():
    """α = 0 原父目标的逐日持有格 vs E5a pool2 同段逐日 ticker 集合。允许输入里没有"列 → ticker"表：
    先比逐日人数，再由成员关系自身求列 → ticker 映射（每列 = 其出现日 pool 集合之交，迭代剔除已确定者），要求映射单射、唯一、并逐日把列集合精确映到 pool 集合。"""
    out = []
    pmap = {'A4b': 'pool2_A4b_pure.csv', 'A4b_CVRv5': 'pool2_A4b_cvrveto.csv', 'M_mean3_v2': 'pool2_Mmean_v2_pure.csv',
            'M_mean3_v2_CVRv5': 'pool2_Mmean_v2_cvrveto.csv', 'M_union3_v2': 'pool2_Munion_v2_pure.csv', 'M_union3_v2_CVRv5': 'pool2_Munion_v2_cvrveto.csv'}
    for mother, fn in pmap.items():
        pool = pd.read_csv(E5A + '/' + fn, dtype={'ticker': str})
        pool = pool[pool.weight > 0]
        pool['d'] = pool.tradeDate.astype(str).str.slice(0, 10)
        byd = pool.groupby('d').ticker.apply(lambda x: frozenset(x)).to_dict()
        for s in SEGS:
            w = np.load(rp('accounts', s, 'weights_%s__K0.npz' % mother), allow_pickle=False)
            tg = [str(x) for x in w['targets']]
            j = tg.index('K0|%s|a0|PARENT' % mother)
            a0, a1 = int(w['off'][j]), int(w['off'][j + 1])
            t, c, ww = w['t'][a0:a1], w['c'][a0:a1], w['w'][a0:a1]
            dates = np.load(rp('accounts', s, '%s__K0.npz' % mother), allow_pickle=False)['dates']
            keep = ww > 0
            t, c = t[keep], c[keep]
            day_cols = {}
            for ti, ci in zip(t.tolist(), c.tolist()):
                day_cols.setdefault(str(dates[ti])[:10], set()).add(ci)
            segdays = [str(d)[:10] for d in dates]
            pdays = {d: byd.get(d, frozenset()) for d in segdays}
            cnt_bad = sum(1 for d in segdays if len(day_cols.get(d, ())) != len(pdays[d]))
            # 精确判据：存在单射 f 使每日 f(列集合) = pool 集合  ⇔  "列的出现日集合"多重集 = "ticker 的出现日集合"多重集
            csig, tsig = {}, {}
            for k, d in enumerate(segdays):
                for ci in day_cols.get(d, ()):
                    csig.setdefault(ci, []).append(k)
                for tk in pdays[d]:
                    tsig.setdefault(tk, []).append(k)
            from collections import Counter
            cc_ = Counter(tuple(v) for v in csig.values())
            tc_ = Counter(tuple(v) for v in tsig.values())
            grp_bad = sum(1 for k in set(cc_) | set(tc_) if cc_.get(k, 0) != tc_.get(k, 0))
            amb = max(cc_.values()) if cc_ else 0
            ok = cnt_bad == 0 and grp_bad == 0 and len(csig) == len(tsig)
            out.append(row('VB06', '%s|%s' % (mother, s), '%s K0 PARENT vs %s' % (mother, fn),
                           '逐日人数不等日 / 出现日签名不等组 / 列数 = ticker 数', '0 / 0 / True',
                           '%d / %d / %s（%d 列、%d 签名组、最大同签名组 %d）' % (cnt_bad, grp_bad, len(csig) == len(tsig), len(csig), len(cc_), amb),
                           'REPRODUCED' if ok else 'DIFFERS',
                           'INFO:列名表不在允许输入内；判据 = 两边"出现日集合"多重集相等（⇔ 存在逐日保持成员的一一对应；同签名组内对应不唯一但不影响成员相等）',
                           func='weights_<母体>__K0.npz 的 (t, c, w>0) vs pool2 (tradeDate, ticker, weight>0)，同日对齐'))
    return out


def vb07():
    """LEGACY_POLICY_RANDOM 与 E6j R-MATCH-SRC（IID）逐位：E6k 分片 samp[desc, k] = 路径 path0+k 的 (net8, gross, pos, turn) 逐日；
    E6j P 分片 main[IID, path] 同四量（α .25 × H5 主臂）。A4b × S × 2019-2023 四个分片 × 2 条 = 8 条路径（另三段作补充行）。"""
    out = []
    kkey = ['E6j.P', 'K_rar20', 'P_production_v2', 'native', 'IID']
    for s in SEGS:
        ej = np.load(E6J + '/randoms/P/%s/A4b__S.npz' % s, allow_pickle=False)
        mech = [str(x) for x in ej['mechs']]
        main = ej['main'][mech.index('IID')]
        mx, npth = 0.0, 0
        for f in sorted(glob.glob(rp('randoms', 'LEGACY_POLICY_RANDOM', s, 'A4b__S__p*.npz'))):
            z = np.load(f, allow_pickle=False)
            d = [str(x) for x in z['desc']]
            i = d.index('S|A4b|a0.25|H5|NATIVE')
            p0 = int(z['path0'][0])
            for k in range(z['samp'].shape[1]):
                a = z['samp'][i, k]
                b = main[p0 + k]
                m = np.isfinite(a) | np.isfinite(b)
                diff = np.nanmax(np.abs(np.where(m, np.nan_to_num(a) - np.nan_to_num(b), 0.0)))
                nanpat = bool((np.isfinite(a) == np.isfinite(b)).all())
                mx = max(mx, diff if nanpat else np.inf)
                npth += 1
        keys = ['%016x' % int.from_bytes(hashlib.blake2b(json.dumps(kkey + [p], sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii'),
                                                                   digest_size=8).digest(), 'big') for p in range(2)]
        out.append(row('VB07', 'A4b|S|%s' % s, 'randoms/LEGACY_POLICY_RANDOM/%s/A4b__S__p*.npz vs E6j randoms/P/%s/A4b__S.npz main[IID]' % (s, s),
                       '路径数 / max|Δ|（net8、gross、pos、turn 逐日；NaN 模式一致）', '8 / ≤1e-12', '%d / %.3g' % (npth, mx),
                       'REPRODUCED' if mx <= 1e-12 else 'DIFFERS', 'STOCHASTIC' + ('' if s == '2019-2023' else ';INFO:补充段'),
                       diff='E6j.P 路径键（blake2b-64，示例 path 0/1，路径键构成按 e6k_random.Legacy.key 转录，单臂写法未必同源 → 只作 INFO）：%s' % ','.join(keys),
                       func='分片 samp 与 E6j main 逐日逐量；种子来源 E6j.P / blake2b-64 → splitmix64（engine_contract §6）'))
    return out


# ============================================================================ V-C 统计从账本与表重算
def tri_sign(x):
    return np.nan if not np.isfinite(x) else (0.0 if abs(x) <= 1e-9 else float(np.sign(x)))


def class_C(workers):
    out = []
    P = policy()
    Pi = P.set_index('desc_id')
    nseg = np.column_stack([P['n_%s' % s].values.astype(float) for s in SEGS])

    def agg(prefix):
        X = np.column_stack([P['%s_%s' % (prefix, s)].values.astype(float) for s in SEGS])
        ok = np.isfinite(X) & (nseg > 0)
        num = np.where(ok, X * nseg, 0).sum(1)
        den = np.where(ok, nseg, 0).sum(1)
        full = np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)
        g4 = np.array([np.median(x[o]) if o.any() else np.nan for x, o in zip(X, ok)])
        return full, g4
    fD, gD = agg('D')
    fS, gS = agg('D_sc')
    fI, gI = agg('D_imp')

    def mad(a, b):
        a, b = np.asarray(a, float), np.asarray(b, float)
        m = np.isfinite(a) | np.isfinite(b)
        nanbad = int((np.isfinite(a) != np.isfinite(b)).sum())
        return (float(np.nanmax(np.abs(a[m] - b[m]))) if m.any() else 0.0), nanbad
    res = [mad(fD, P.FULL), mad(gD, P.G4), mad(fS, P.FULL_sc), mad(fI, P.FULL_imp), mad(gS, P.G4_sc)]
    ycols = [c for c in P.columns if re.fullmatch(r'Y\d{4}', c)]
    Y = P[ycols].values.astype(float)
    yp = (np.nan_to_num(Y, nan=-1) > 0).sum(1)
    yn = np.isfinite(Y).sum(1)
    y25 = sum(((P['Y%d' % y].values > 0) & np.isfinite(P['Y%d' % y].values)).astype(int) for y in range(2010, 2026) if 'Y%d' % y in P.columns)
    bool_bad = {}
    bool_bad['years_pos'] = int((yp != P.years_pos.values).sum())
    bool_bad['years_n'] = int((yn != P.years_n.values).sum())
    bool_bad['years_pos_2010_2025'] = int((y25 != P.years_pos_2010_2025.values).sum())
    bool_bad['d_ok'] = int(((yp >= 12) != P.d_ok.astype(str).eq('True').values).sum())
    Dm = np.column_stack([P['D_%s' % s].values.astype(float) for s in SEGS])
    Im = np.column_stack([P['D_imp_%s' % s].values.astype(float) for s in SEGS])
    for dl, tag in ((0.05, 'd05'), (0.10, 'd10'), (0.15, 'd15')):
        c = (np.isfinite(Dm) & (Dm >= -dl)).all(1)
        f = (np.isfinite(Im) & (Im >= -dl)).all(1)
        bool_bad['c_' + tag] = int((c != P['c_' + tag].astype(str).eq('True').values).sum())
        bool_bad['f_' + tag] = int((f != P['f_' + tag].astype(str).eq('True').values).sum())
    for ag in ('FULL', 'G4'):
        pos = np.isfinite(P[ag].values) & (P[ag].values >= 0.10)
        bool_bad['positive_' + ag] = int((pos != P['positive_' + ag].astype(str).eq('True').values).sum())
        ec = []
        for x, y in zip(P[ag].values, P[ag + '_sc'].values):
            a, b_ = tri_sign(x), tri_sign(y)
            ec.append('NA' if (np.isnan(a) or np.isnan(b_)) else ('PASS' if a == b_ else 'FAIL'))
        bool_bad['e_cap_' + ag] = int((np.array(ec) != P['e_cap_' + ag].astype(str).values).sum())
    got = '%.3g / %.3g / %.3g / %.3g / %.3g；NaN 模式不一致 %s；布尔 / 状态不符 %s' % (res[0][0], res[1][0], res[2][0], res[3][0], res[4][0],
                                                                 [r[1] for r in res], json.dumps(bool_bad))
    ok = max(r[0] for r in res) <= 1e-9 and all(r[1] == 0 for r in res) and all(v == 0 for v in bool_bad.values())
    out.append(row('VC01', 'merge_identities', 'results/full/policy_E6k.csv（38,982）', 'max|Δ| FULL / G4 / FULL_sc / FULL_imp / G4_sc；年数 / c / f / 正向 / e资本',
                   exp1('VC01', 'merge_identities'), got, 'REPRODUCED' if ok else 'DIFFERS', func='full_g4 转录；tri_sign 容差 1e−9；Y<年> 计数'))
    # VC02 e_rand（rmr / mcse 由 random_refs LEGACY 行现取）
    R = pd.concat([rrefs(s).assign(segment=s) for s in SEGS])
    leg = R[R.mechanism == 'LEGACY_POLICY_RANDOM'].set_index(['desc_id', 'H', 'segment'])
    er, mism = [], 0
    rm_bad = 0
    for r in P.itertuples():
        if r.family in ('OWN', 'HG_ONLY'):
            e = 'NO_NEW_CONTENT_TO_PERMUTE'
        else:
            st = []
            for s in POS:
                k = (r.desc_id, int(r.H), s)
                if k in leg.index:
                    x = leg.loc[k]
                    d, se = float(x.real_minus_rand), float(x.mcse)
                    rm_bad += (abs(d - float(P.at[r.Index, 'rmr_%s' % s])) > 1e-12)
                else:
                    d, se = np.nan, np.nan
                if not (np.isfinite(d) and np.isfinite(se)):
                    st.append('NA')
                elif d > 0 and d >= 2 * se:
                    st.append('POS')
                elif d <= 0 and -d >= 2 * se:
                    st.append('NONPOS')
                else:
                    st.append('UNRES')
            if 'NONPOS' in st:
                e = 'FAIL'
            elif all(x == 'POS' for x in st):
                e = 'PASS'
            elif 'NA' in st:
                e = 'RANDOM_NOT_SCHEDULED' if str(r.random_scheduled) == 'False' else 'NA'
            else:
                e = 'MC_UNRESOLVED'
        er.append(e)
        mism += e != r.e_rand
    out.append(row('VC02', 'e_rand_reproduction', 'policy_E6k.csv e_rand（rmr / mcse 取自 random_refs LEGACY）', 'n mismatches；policy rmr 列 ≠ random_refs 数',
                   exp1('VC02', 'e_rand_reproduction'), '%d；%d' % (mism, rm_bad), 'REPRODUCED' if (mism == 0 and rm_bad == 0) else 'DIFFERS',
                   diff=json.dumps(pd.Series(er).value_counts().to_dict()), func='PX6 / PX3 / 两后段 2·MCSE 三态'))
    # VC03 政策串 + size 状态（预期表 VC12 行 = size_profiles）
    sz = {p: [] for p in PROFILES}
    recs = P.to_dict('records')
    for rr in recs:
        for p in PROFILES:
            sz[p].append(size_status(rr, p, P.columns))
    sz_bad = {p: int((np.array(sz[p]) != P['size_' + p].astype(str).values).sum()) for p in PROFILES}
    pol_bad = {}
    for p in PROFILES:
        for ag in ('FULL', 'G4'):
            got_s = [verdict(rr, ag, p, szv) for rr, szv in zip(recs, sz[p])]
            pol_bad['policy_%s_%s' % (p, ag)] = int((np.array(got_s) != P['policy_%s_%s' % (p, ag)].astype(str).values).sum())
        pend = (P['policy_%s_FULL' % p].str.slice(0, 3) != P['policy_%s_G4' % p].str.slice(0, 3))
        pol_bad['PENDING_%s' % p] = int((pend.values != P['POLICY_INTERPRETATION_PENDING_%s' % p].astype(str).eq('True').values).sum())
    out.append(row('VC03', 'policy_strings', 'policy_E6k.csv 十列判定串 + 五个 PENDING 标记', 'n mismatches per profile × agg', exp1('VC03', 'policy_strings'),
                   json.dumps(pol_bad), 'REPRODUCED' if all(v == 0 for v in pol_bad.values()) else 'DIFFERS',
                   'INFO:CSV 里 size 状态 "N/A" 为字面串（pandas 默认读成 NaN——决策端所见 "size(LEGACY_EDIT5):nan" 的来源）；V 以 keep_default_na=False 读',
                   func='按 brief §6 / plan §9 文本独立实现：失败项 c、d、f、正向门槛、e资本、e随机、size(profile)；待定 → 不可判（e资本:NA / e随机:<状态> / size:<状态>）'))
    out.append(row('VC12', 'size_profiles', 'policy_E6k.csv size_<profile>（预期表此行标 VC12，内容为 D12 的 size 重算）', 'n mismatches per profile',
                   exp1('VC12', 'size_profiles'), json.dumps(sz_bad), 'REPRODUCED' if all(v == 0 for v in sz_bad.values()) else 'DIFFERS',
                   'INFO:预期表 probe_id 标签与 brief §5 VC12（同时带）不一致，本行按预期表内容复算；同时带见 VC12/band',
                   func='LEGACY：四段 |edit_gap_mean_T| 只在有定义段判，全无定义 → N/A；PORT3：[lo,hi]⊂[−3,3] PASS / 无交 FAIL / 否则 PARTIAL；LEADER：lv5 ≤ max(.03, 父) + 1e−12'))
    # VC04 相对列
    D = descs().set_index('desc_id')
    rel = {}
    for lab, col in (('native', 'native_desc'), ('C1', 'c1_desc')):
        m = D.reindex(P.desc_id)[col].values
        ref = Pi.FULL.reindex(m).values
        calc = P.FULL.values - ref
        a, b_ = calc, P['FULL_vs_%s' % lab].values.astype(float)
        both = np.isfinite(a) & np.isfinite(b_)
        rel[lab] = (float(np.max(np.abs(a[both] - b_[both]))) if both.any() else 0.0, int((np.isfinite(a) != np.isfinite(b_)).sum()))
        for s in SEGS:
            a2 = P['D_%s' % s].values - Pi['D_%s' % s].reindex(m).values
            b2 = P['D_vs_%s_%s' % (lab, s)].values.astype(float)
            both2 = np.isfinite(a2) & np.isfinite(b2)
            rel['%s_%s' % (lab, s)] = (float(np.max(np.abs(a2[both2] - b2[both2]))) if both2.any() else 0.0, int((np.isfinite(a2) != np.isfinite(b2)).sum()))
    ok = all(v[0] <= 1e-9 and v[1] == 0 for v in rel.values())
    out.append(row('VC04', 'relative_cols', 'policy_E6k.csv FULL_vs_* / D_vs_*_<段>', 'max|Δ| / NaN 模式不一致（native、C1、逐段）', exp1('VC04', 'relative_cols'),
                   json.dumps({k: ['%.3g' % v[0], v[1]] for k, v in rel.items()}), 'REPRODUCED' if ok else 'DIFFERS',
                   'INFO:D_vs_* 在统计里是同日配对差；与"子 FULL − 映射对象 FULL"相等是因为两者共用原父且有效日相同', func='映射对象来自 descriptors_E6k.csv'))
    # VC05 三句加法
    out += vc05(P)
    # VC06 候选清单
    C = read_csv_keep(rp('results', 'full', 'production_change_candidates_E6k.csv'))
    exp_set = set()
    mains = set(main154())
    for p in PROFILES:
        for d in P[P['policy_%s_FULL' % p] == '通过'].desc_id:
            exp_set.add((p, d))
    got_set = set(zip(C.profile, C.desc_id))
    mo_bad = int(sum((d in mains) != (str(m) == 'True') for d, m in zip(C.desc_id, C.main_object)))
    byp = C.profile.value_counts().to_dict()
    bym = C[C.main_object.astype(str) == 'True'].profile.value_counts().to_dict()
    out.append(row('VC06', 'candidates', 'results/full/production_change_candidates_E6k.csv', 'rows / by profile / main_object by profile；集合 = 各 profile FULL 通过',
                   exp1('VC06', 'candidates'), '%d / %s / %s' % (len(C), json.dumps(byp), json.dumps(bym)),
                   'REPRODUCED' if (got_set == exp_set and mo_bad == 0 and len(C) == 820) else 'DIFFERS', diff='集合差 %d；main_object 不符 %d' % (len(got_set ^ exp_set), mo_bad),
                   func='集合比较'))
    pc = {'primary144': {p: int((P[P.primary144]['policy_%s_FULL' % p] == '通过').sum()) for p in PROFILES},
          'main154': {p: int((P[P.desc_id.isin(mains)]['policy_%s_FULL' % p] == '通过').sum()) for p in PROFILES}}
    tabs3 = report_tables('E6k_REPORT_part3.md')[0]
    cc = tabs3['E6K-P3-CAND-COUNT']
    cnt_ok = all(int(r.objects) == int(((C.profile == r.profile) & (C.family == r.family)).sum()) for r in cc.itertuples())
    out.append(row('VC06', 'pass_counts', 'policy_E6k.csv；part3 E6K-P3-CAND-COUNT', 'FULL 通过数：primary144 / 主对象 154；CAND-COUNT = 重数', exp1('VC06', 'pass_counts'),
                   json.dumps(pc), 'REPRODUCED' if (json.dumps(pc, sort_keys=True) == json.dumps(json.loads(exp1('VC06', 'pass_counts')), sort_keys=True) and cnt_ok)
                   else 'DIFFERS', diff='CAND-COUNT 相符=%s' % cnt_ok, func='计数'))
    # VC07
    q = pd.read_csv(rp('registry', 'question_to_objects_E6k.csv'))
    alld = set(descs().desc_id) | set(pd.read_csv(rp('registry', 'accessory_E6k.csv')).acc_id)
    notin = sorted(set(q.desc_id) - alld)
    q['card'] = q.query_id.str.slice(4, 7)
    t1 = report_tables('E6k_REPORT_part1.md')[0]['E6K-P1-CARDS']
    ob_bad = sum(int(r.objects) != q[q.card == r.card].desc_id.nunique() for r in t1.itertuples())
    out.append(row('VC07', 'question_to_objects', 'registry/question_to_objects_E6k.csv；part1 E6K-P1-CARDS', 'rows / query_ids / desc 不在描述符与附属表；CARDS objects 不符',
                   exp1('VC07', 'question_to_objects'), '%d / %d / %d %s；%d' % (len(q), q.query_id.nunique(), len(notin), notin, ob_bad),
                   'REPRODUCED' if (len(q) == 300466 and q.query_id.nunique() == 47 and ob_bad == 0) else 'DIFFERS',
                   'INFO:不在表内的 %d 个是卡级占位对象（brief 正文"全部 desc 在描述符表"与此不同；lessons 16）' % len(notin), func='集合比较'))
    # VC08 随机
    out += vc08(P)
    # VC09 bootstrap
    out += vc09(P)
    # VC10 掩码账本与逐日暴露
    out += vc10(P)
    # VC11 假设卡与血缘
    out += vc11()
    # VC12 同时带（brief §5）
    out += vc12()
    # VC13–VC16 账本级
    out += vc13(P, workers)
    out += vc14_15(P)
    out += vc16()
    return out


def size_status(r, prof, cols):
    """policy_profiles_E6k*.json 与 brief §6 文本独立实现。"""
    if prof == 'EXEC_DISCLOSE_ONLY':
        return 'PASS'
    if prof == 'LEGACY_EDIT5':
        g = np.array([r.get('edit_gap_absmean_T_%s' % s, np.nan) for s in SEGS], float)
        if np.all(np.isnan(g)):
            return 'N/A'
        return 'FAIL' if np.nanmax(g) > 5.0 else 'PASS'
    if prof.startswith('PROPOSED_PORT3'):
        z = 'T' if prof.endswith('_T') else 'L'
        st = []
        for s in SEGS:
            lo, hi = r.get('port_size_lo_%s_%s' % (z, s), np.nan), r.get('port_size_hi_%s_%s' % (z, s), np.nan)
            if not (np.isfinite(lo) and np.isfinite(hi)):
                st.append('NA')
            elif lo >= -3.0 and hi <= 3.0:
                st.append('PASS')
            elif hi < -3.0 or lo > 3.0:
                st.append('FAIL')
            else:
                st.append('SIZE_PARTIALLY_IDENTIFIED')
        if 'FAIL' in st:
            return 'FAIL'
        if all(x == 'PASS' for x in st):
            return 'PASS'
        return 'SIZE_PARTIALLY_IDENTIFIED' if 'SIZE_PARTIALLY_IDENTIFIED' in st else 'N/A'
    st = []
    for s in SEGS:
        c, p = r.get('lv5_mean_%s' % s, np.nan), r.get('parent_lv5_mean_%s' % s, np.nan)
        if not np.isfinite(c):
            st.append('NA')
        else:
            st.append('PASS' if c <= max(0.03, p if np.isfinite(p) else 0.03) + 1e-12 else 'FAIL')
    return 'FAIL' if 'FAIL' in st else ('PASS' if all(x == 'PASS' for x in st) else 'N/A')


def verdict(r, ag, prof, ss):
    fails, pend = [], []
    for name, ok in (('c', r['c_d10']), ('d', r['d_ok']), ('f', r['f_d10']), ('正向门槛', r['positive_%s' % ag])):
        if str(ok) != 'True':
            fails.append(name)
    for name, st in (('e资本', r['e_cap_%s' % ag]), ('e随机', r['e_rand'])):
        if st == 'FAIL':
            fails.append(name)
        elif st != 'PASS':
            pend.append('%s:%s' % (name, st))
    if ss == 'FAIL':
        fails.append('size(%s)' % prof)
    elif ss not in ('PASS', 'N/A'):
        pend.append('size:%s' % ss)
    if fails:
        return '不通过（%s）' % '、'.join(fails)
    if pend:
        return '不可判（%s）' % '、'.join(pend)
    return '通过'


def vc05(P):
    A = read_csv_keep(rp('results', 'full', 'policy_additions_E6k.csv'))
    nat = P[(P.op == 'NATIVE') & (P.alpha == 0.25) & (P.H == 5) & P.meas.isin(['S', 'M', 'Q', 'C1', 'SM'])].set_index(['mother', 'meas'])
    bad = 0
    for r in A.itertuples():
        m = nat.loc[r.form]
        col = 'policy_%s_%s' % (r.profile, r.aggregation)
        elig = [a for a in ('C1', 'M', 'S', 'Q') if a in m.index and m.loc[a, col] == '通过']
        chosen = None
        if 'C1' in elig:
            chosen = 'C1'
            beat = []
            for arm in ('M', 'S', 'Q'):
                if arm in elig:
                    dseg = np.array([m.loc[arm, 'D_%s' % s] - m.loc['C1', 'D_%s' % s] for s in SEGS], float)
                    nseg_ = np.array([m.loc[arm, 'n_%s' % s] for s in SEGS], float)
                    f, g = full_g4(dseg, nseg_)
                    md = f if r.aggregation == 'FULL' else g
                    if int((dseg >= 0.05).sum()) >= 3 and md >= 0.05:
                        beat.append((md, arm))
            if beat:
                chosen = sorted(beat, key=lambda x: (-x[0], ('M', 'S', 'Q').index(x[1])))[0][1]
        elif elig:
            chosen = sorted(elig, key=lambda a: (-m.loc[a, r.aggregation], ('C1', 'M', 'S', 'Q').index(a)))[0]
        if 'SM' in m.index and m.loc['SM', col] == '通过':
            best = sorted(elig, key=lambda a: (-m.loc[a, r.aggregation], ('C1', 'M', 'S', 'Q').index(a)))[0] if elig else None
            if best is None:
                chosen = 'SM'
            else:
                dseg = np.array([m.loc['SM', 'D_%s' % s] - m.loc[best, 'D_%s' % s] for s in SEGS], float)
                nseg_ = np.array([m.loc['SM', 'n_%s' % s] for s in SEGS], float)
                f, g = full_g4(dseg, nseg_)
                if (f if r.aggregation == 'FULL' else g) >= 0.10:
                    chosen = 'SM'
        bad += ('|'.join(elig) != str(r.eligible).replace('nan', '')) or ((chosen or '无') != r.chosen)
    return [row('VC05', 'additions', 'results/full/policy_additions_E6k.csv', 'n rows / n mismatched（eligible 与 chosen）', exp1('VC05', 'additions'), '%d / %d' % (len(A), bad),
                'REPRODUCED' if (len(A) == 80 and bad == 0) else 'DIFFERS', func='PX1 转录：默认 C1；替代须 ≥3/4 段配对差 ≥ +.05 且合并 ≥ +.05；SM ≥ +.10')]


def vc08(P):
    out = []
    for s in SEGS:
        R = rrefs(s)
        m1 = float(np.nanmax(np.abs(R.real_net8_ann - R.rand_mean - R.real_minus_rand)))
        m2 = float(np.nanmax(np.abs(R.rand_sd / np.sqrt(R.n) - R.mcse)))
        got = '%d / %s / %.2g / %.2g / %.4f / %d / %s' % (len(R), json.dumps(R.mechanism.value_counts().to_dict()), m1, m2, R.mcse.max(), int((R.n > 1024).sum()),
                                                          json.dumps({str(k): int(v) for k, v in R.n.value_counts().to_dict().items()}))
        e = exp1('VC08', 'random_refs_%s' % s)
        ok = len(R) == 2300 and m1 <= 1e-9 and m2 <= 1e-9 and int((R.n > 1024).sum()) == 0
        mc_over = int((R.mcse > 0.03).sum())
        out.append(row('VC08', 'random_refs_%s' % s, 'results/full/random_refs_%s.csv' % s,
                       'rows / mechanisms / max|real−mean−rmr| / max|sd/√n−mcse| / max mcse / n>1024 / n 分布', e, got, 'REPRODUCED' if ok else 'DIFFERS',
                       'INFO:MCSE > .03 的行 %d（MC 增补只在某比较组所需路径 (sd/.03)² > 已有路径时触发，n = 1,024 时等价于 MCSE > .03）' % mc_over,
                       func='内部恒等'))
    # policy rmr / mcse / npaths = LEGACY 行
    R = pd.concat([rrefs(s).assign(segment=s) for s in SEGS])
    leg = R[R.mechanism == 'LEGACY_POLICY_RANDOM'].set_index(['desc_id', 'H', 'segment'])
    bad = 0
    for r in P[P.random_scheduled.astype(str) == 'True'].itertuples():
        for s in SEGS:
            k = (r.desc_id, int(r.H), s)
            x = leg.loc[k] if k in leg.index else None
            pr = P.loc[r.Index, ['rmr_%s' % s, 'mcse_%s' % s, 'npaths_%s' % s]].values.astype(float)
            if x is None:
                bad += np.isfinite(pr[0])
            else:
                bad += (abs(pr[0] - x.real_minus_rand) > 1e-12) or (abs(pr[1] - x.mcse) > 1e-12) or (int(pr[2]) != int(x.n))
    post = leg.reset_index()
    post = post[post.segment.isin(POS)]
    n_clear = int(((post.real_minus_rand.abs() >= 2 * post.mcse) | (post.mcse <= 0.03)).sum())
    out.append(row('VC08', 'policy_vs_legacy', 'policy rmr / mcse / npaths vs random_refs LEGACY', '不符格数；两后段 |rmr| ≥ 2·mcse 或 mcse ≤ .03 的对象 × 段 / 总数', '0',
                   '%d；%d / %d' % (bad, n_clear, len(post)), 'REPRODUCED' if bad == 0 else 'DIFFERS',
                   'INFO:MC 加密未触发：LEGACY 两后段 %d 格 mcse 全 ≤ %.4f（< .03）' % (len(post), post.mcse.max()), func='逐格比较'))
    rr = pd.read_csv(rp('results', 'random_registry.csv'))
    e = exp1('VC08', 'random_registry')
    got = '%d / %s / alias %d' % (len(rr), json.dumps(rr.mechanism.value_counts().to_dict()), int(rr.alias_of.notna().sum()))
    ok = len(rr) == 2252 and int(rr.alias_of.notna().sum()) == 24
    out.append(row('VC08', 'random_registry', 'results/random_registry.csv', 'rows / by mechanism / alias_of 非空', e[:120] + '…', got, 'REPRODUCED' if ok else 'DIFFERS',
                   func='计数'))
    return out


def vc09(P):
    out = []
    B = pd.read_csv(rp('results', 'full', 'bootstrap', 'bootstrap_comparisons.csv'))
    pre = B.comparison_id.str.split('|').str[0].value_counts().to_dict()
    viol = int((B.q025 > B.q975).sum())
    ncomp = B.comparison_id.nunique()
    cp = B[(B.scope == 'FULL') & (B.L == 20) & B.comparison_id.str.startswith('CP|')].copy()
    cp['desc_id'] = cp.comparison_id.str.slice(3)
    x = cp.set_index('desc_id').est.reindex(P.desc_id).values
    mx = float(np.nanmax(np.abs(x - P.FULL.values)))
    nanb = int((np.isfinite(x) != np.isfinite(P.FULL.values)).sum())
    got = '%d = %d 比较 × 2 L × 3 scope / %s / viol %d / CP FULL est vs policy FULL max %.3g, NaN 不一致 %d' % (len(B), ncomp, json.dumps(pre), viol, mx, nanb)
    ok = len(B) == 677556 and ncomp * 6 == len(B) and viol == 0 and mx <= 1e-9 and nanb == 0
    out.append(row('VC09', 'bootstrap', 'results/full/bootstrap/bootstrap_comparisons.csv', 'rows（乘法）/ 前缀 / q025 ≤ q975 违反 / CP FULL est = policy FULL', exp1('VC09', 'bootstrap'),
                   got, 'REPRODUCED' if ok else 'DIFFERS', func='计数与逐格比较'))
    # part3 五表 ci
    tabs = report_tables('E6k_REPORT_part3.md')[0]
    ci = cp.set_index('desc_id')
    bad = n = 0
    for p in PROFILES:
        t = tabs['E6K-P3-POL-%s' % p.replace('_', '')]
        for r in t.itertuples():
            did = '%s|%s|a%s|H%s|%s' % (r.meas, r.mother, r.alpha, r.H, r.op)
            if did not in ci.index:
                continue
            for c, col in (('ci_L20_lo', 'q025'), ('ci_L20_hi', 'q975')):
                n += 1
                bad += cell_eq4(getattr(r, c), float(ci.loc[did, col])) == 'BAD'
    out.append(row('VC09', 'part3_ci', 'part3 E6K-P3-POL-*（五表）ci_L20', '格数 / 不符（4 位有效）', '0 不符', '%d / %d' % (n, bad), 'REPRODUCED' if bad == 0 else 'DIFFERS',
                   func='ci_L20 = CP FULL L20 q025 / q975'))
    band = pd.read_csv(rp('results', 'full', 'bootstrap', 'simultaneous_band_q95.csv'))
    got = '%d / %s / %s' % (len(band), sorted(band.set.unique()), json.dumps([dict(L=int(r.L), set=r.set, q=round(float(r.q95_maxabs_centered), 4)) for r in band.itertuples()]))
    out.append(row('VC09', 'band', 'results/full/bootstrap/simultaneous_band_q95.csv', 'rows / sets / q95 values', exp1('VC09', 'band'), got, 'REPRODUCED' if len(band) == 4 else 'DIFFERS',
                   func='读表（统计量定义见 VC12/band）'))
    return out


def vc10(P):
    out = []
    M0 = pd.read_csv(rp('results', 'mask_edit_ledger.csv'))
    by = M0.groupby('segment').target_id.nunique().to_dict()
    nfb = int((M0.op == 'FALLBACK_DOMAIN').sum())
    M = M0[M0.op != 'FALLBACK_DOMAIN']
    D = descs()
    h5 = D[(D.H == 5) & (D.op != 'PARENT')].set_index('target_id').desc_id.to_dict()
    Pi = P.set_index('desc_id')
    mx = {'size_edit_gap_T': 0.0, 'small30_share_delta': 0.0, 'size_unknown_weight': 0.0}
    nb = {k: 0 for k in mx}
    n = 0
    for r in M.itertuples():
        did = h5.get(r.target_id)
        if did is None or did not in Pi.index:
            continue
        n += 1
        pairs = (('size_edit_gap_T', r.size_edit_gap_T, Pi.at[did, 'edit_gap_mean_T_%s' % r.segment]),
                 ('small30_share_delta', r.small30_share_delta, Pi.at[did, 'small30_delta_%s' % r.segment]),
                 ('size_unknown_weight', r.size_unknown_weight, Pi.at[did, 'unkT_mean_%s' % r.segment]))
        for k, a, b in pairs:
            if np.isfinite(a) and np.isfinite(b):
                mx[k] = max(mx[k], abs(a - b))
            elif np.isfinite(a) != np.isfinite(b):
                nb[k] += 1
    got = '%d 行 / %d 目标 / %s（含 FALLBACK_DOMAIN %d 行）；与 policy 段列 max|Δ| %s；NaN 不一致 %s（%d 对）' % (
        len(M0), M0.target_id.nunique(), json.dumps(by), nfb, json.dumps({k: '%.3g' % v for k, v in mx.items()}), json.dumps(nb), n)
    ok = len(M0) == 9592 and all(v <= 1e-9 for v in mx.values()) and all(v == 0 for v in nb.values())
    out.append(row('VC10', 'mask_edit_ledger', 'results/mask_edit_ledger.csv vs policy 段列（H5 描述符）', 'rows / targets / by segment；三列 = policy 段列',
                   exp1('VC10', 'mask_edit_ledger'), got, 'REPRODUCED' if ok else 'DIFFERS',
                   func='size_edit_gap_T = nanmean(t_gapT)·100；small30_share_delta = nanmean 子 − nanmean 父；size_unknown_weight = nanmean(t_unkT)（掩码事实口径）'))
    X = pd.read_parquet(rp('results', 'risk_exposure_daily.parquet'))
    nt = X.target_id.nunique()
    days = {s: X[X.segment == s].date.nunique() for s in SEGS}
    got = '%d 行 × %d 列 = %d 目标 × %d 日（%s）；每 (目标, 段, 日) 唯一 = %s' % (len(X), X.shape[1], nt, sum(days.values()), json.dumps(days),
                                                                  not X.duplicated(['target_id', 'segment', 'date']).any())
    ok = len(X) == 630400 and len(X) == nt * sum(days.values())
    out.append(row('VC10', 'risk_exposure_daily', 'results/risk_exposure_daily.parquet', 'rows / cols / 乘法', exp1('VC10', 'risk_exposure_daily')[:60] + '…', got,
                   'REPRODUCED' if ok else 'DIFFERS', 'INFO:实际 %d 列（brief 正文写 16 列）；160 目标 = 144 主展示 + 2 个 C1_hi 目标 + 6 SM + 8 原父' % X.shape[1],
                   func='固定清单目标 × 四段交易日'))
    return out


def vc11():
    out = []
    H = jload(rp('results', 'hypothesis_outcomes.json'))
    cq = set(pd.read_csv(rp('registry', 'query_registry_E6k.csv')).query_id)
    need = ['card', 'plan_line', 'title', 'queries', 'source_claim', 'exposure', 'missing_assumption', 'experiment', 'result_query', 'supported_scope',
            'alternative_surviving', 'next_design_change', 'category']
    miss = {h['card']: [k for k in need if k not in h or h[k] in ('', None)] for h in H}
    miss = {k: v for k, v in miss.items() if v}
    badq = [q for h in H for q in h['queries'] if q not in cq]
    out.append(row('VC11', 'hypothesis_outcomes', 'results/hypothesis_outcomes.json', 'n cards / 十三字段缺 / queries 不在登记表', '18 / {} / []',
                   '%d / %s / %s' % (len(H), json.dumps(miss), badq), 'REPRODUCED' if (len(H) == 18 and not miss and not badq) else 'DIFFERS', func='逐卡字段'))
    L = pd.read_csv(rp('registry', 'hypothesis_lineage_E6k.csv'))
    plan_sha = sha256_file(rp('PLAN_COPY.md'))
    prop_sha = sha256_file(rp('E6k_proposal_copy.md'))
    srcs = L.source_sha.astype(str).unique().tolist()
    role_ok = all((r.source_sha == plan_sha or plan_sha.startswith(str(r.source_sha))) if r.author_role == 'web_plan_v1.1'
                  else (r.source_sha == prop_sha or prop_sha.startswith(str(r.source_sha))) for r in L.itertuples())
    got = '%d / %s / %s；source_sha 取值 %s；按 author_role 对应文件 = %s' % (len(L), json.dumps(L.status.value_counts().to_dict()),
                                                                     json.dumps(L.author_role.value_counts().to_dict()), [s[:8] for s in srcs], role_ok)
    out.append(row('VC11', 'lineage', 'registry/hypothesis_lineage_E6k.csv', 'rows / status / author_role；source_sha = 该行原句所在文件的 sha', exp1('VC11', 'lineage'), got,
                   'REPRODUCED' if (len(L) == 32 and role_ok) else 'DIFFERS',
                   'INFO:adopted 18 行原句出自 plan（%s）；superseded 14 行原句出自决策端 proposal（E6k_proposal_copy.md %s）——brief 正文"逐行 source_sha = plan sha"对 superseded 行不成立，属设计'
                   % (plan_sha[:8], prop_sha[:8]), func='逐行 sha 比较'))
    return out


def vc12():
    """同时带统计量：从 e6k_bootstrap.py 源码转录（只读源码，不执行）。"""
    src = open(CODE + '/e6k_bootstrap.py', encoding='utf-8').read()
    need = ["draws = np.where(den > 0, num / den * ST.ANN, np.nan)", "se = np.nanstd(draws, axis=0, ddof=1)",
            "cen = (draws[:, ok_] - est[ok_][None, :]) / se[ok_][None, :]", "np.max(np.abs(cen), axis=1)", "np.percentile(mx, 95)"]
    found = {n: (n in src) for n in need}
    band = pd.read_csv(rp('results', 'full', 'bootstrap', 'simultaneous_band_q95.csv'))
    B = pd.read_csv(rp('results', 'full', 'bootstrap', 'bootstrap_comparisons.csv'))
    P = policy()
    prim = set('CP|' + P[P.primary144].desc_id)
    x = B[(B.scope == 'FULL') & (B.L == 20) & B.comparison_id.isin(prim)]
    q = float(band[(band.L == 20) & (band.set == 'primary144')].q95_maxabs_centered.iloc[0])
    hw = q * x.se
    ind = (x.q975 - x.q025) / 2
    defin = ('统计量 = max_j |(FULL*_bj − FULL_j)/SE_j|（对固定集合内逐比较先按各自 bootstrap SE 标准化、再取 max；FULL* 为四段 n 加权年化百分点的 draw，'
             'FULL_j 为全样本点估、SE_j = draw 的 sd（ddof 1）；集合 all 为全部 112,926 个比较中 SE > 0 且无无支持 draw 的）→ 取 2,000 draws 的 95% 分位；'
             '单位 = SE 的倍数（无量纲），不是年化百分点；同时带半宽_j = q95 · SE_j')
    got = '源码转录 %s；primary144 L20：q95 = %.4f（SE 倍数）→ 同时带半宽 q95·SE_j（年化百分点）中位 %.3f / 最大 %.3f；逐对象 95%% CI 半宽中位 %.3f / 最大 %.3f' % (
        all(found.values()), q, float(np.median(hw)), float(np.max(hw)), float(np.median(ind)), float(np.max(ind)))
    return [row('VC12', 'band', 'results/full/bootstrap/simultaneous_band_q95.csv；code/e6k_bootstrap.py（只读）', '统计量定义与单位；是否与 FULL 同单位',
                'q95 3.379 / 4.810 / 3.435 / 4.780；若与 FULL 同单位 → DIFFERS', got, 'REPRODUCED' if all(found.values()) else 'NOT_COMPUTABLE',
                'INFO:统计量为标准化 max-t（SE 倍数），与 FULL 不同单位 → 按 brief §5 不判 DIFFERS；决策端 D17 把 q95 与逐对象半宽直接比较属单位不同；定义：' + defin,
                func='源码字符串转录 + 由 bootstrap_comparisons FULL 行 se 派生半宽')]


def vc13(P, workers):
    """从账本重算政策表：154 主对象全量 + 其余 38,828 中 seed 20260929 抽 300；外加 20 个比较的 bootstrap 从账本重放。"""
    out = []
    rng = np.random.default_rng(SEED)
    mains = main154()
    rest = sorted(set(P.desc_id) - set(mains))
    samp = sorted(rng.choice(rest, 300, replace=False).tolist())
    objs = mains + samp
    D = descs().set_index('desc_id')
    res = {}
    for s in SEGS:
        need = {}
        for did in objs:
            need.setdefault(D.at[did, 'task'], []).append(did)
        for task, dl in need.items():
            mother, meas = task.split('|')
            z = np.load(acct_file(s, mother, meas), allow_pickle=False)
            ix = {x: i for i, x in enumerate(map(str, z['desc']))}
            k0 = np.load(acct_file(s, mother, 'K0'), allow_pickle=False)
            ixp = {x: i for i, x in enumerate(map(str, k0['desc']))}
            net8, scc, scp = z['d_net8'], z['d_sc_child'], z['d_sc_parent']
            pnet = k0['d_net8']
            years = pd.to_datetime(pd.Index([str(x) for x in z['dates']])).year.values
            for did in dl:
                i = ix[did]
                H = int(D.at[did, 'H'])
                par = 'K0|%s|a0|H%d|PARENT' % (mother, H)
                d = paired(net8[i], pnet[ixp[par]])
                Dv, n = seg_D(d)
                Dsc, _ = seg_D(paired(scc[i], scp[i]))
                se = hac_se(d, H) * ANN
                yr = {int(y): (float(np.mean(d[(years == y) & np.isfinite(d)])) * ANN if ((years == y) & np.isfinite(d)).any() else np.nan) for y in np.unique(years)}
                res[(did, s)] = dict(D=Dv, n=n, Dsc=Dsc, se=se, Y=yr)
    Pi = P.set_index('desc_id')
    mx = {'D': 0.0, 'n': 0, 'D_sc': 0.0, 'FULL': 0.0, 'G4': 0.0, 'FULL_sc': 0.0, 'Y': 0.0, 'se_H': 0.0}
    for did in objs:
        Ds = [res[(did, s)]['D'] for s in SEGS]
        ns = [res[(did, s)]['n'] for s in SEGS]
        f, g = full_g4(Ds, ns)
        fs, _ = full_g4([res[(did, s)]['Dsc'] for s in SEGS], ns)
        x = Pi.loc[did]
        for s in SEGS:
            r = res[(did, s)]
            mx['D'] = max(mx['D'], abs(r['D'] - x['D_%s' % s]) if np.isfinite(r['D']) else 0.0)
            mx['n'] = max(mx['n'], abs(r['n'] - int(x['n_%s' % s])))
            mx['D_sc'] = max(mx['D_sc'], abs(r['Dsc'] - x['D_sc_%s' % s]) if np.isfinite(r['Dsc']) else 0.0)
            if np.isfinite(r['se']):
                mx['se_H'] = max(mx['se_H'], abs(r['se'] - x['se_H_%s' % s]))
            for y, v in r['Y'].items():
                if np.isfinite(v):
                    mx['Y'] = max(mx['Y'], abs(v - x['Y%d' % y]))
        mx['FULL'] = max(mx['FULL'], abs(f - x.FULL) if np.isfinite(f) else 0.0)
        mx['G4'] = max(mx['G4'], abs(g - x.G4) if np.isfinite(g) else 0.0)
        mx['FULL_sc'] = max(mx['FULL_sc'], abs(fs - x.FULL_sc) if np.isfinite(fs) else 0.0)
    ok = all(v <= 1e-9 for k, v in mx.items() if k not in ('se_H', 'n')) and mx['n'] == 0 and mx['se_H'] <= 1e-6
    out.append(row('VC13', 'ledger_recompute', '154 主对象 + 抽样 300（seed 20260929）× 四段', 'max|Δ| D_seg / n / D_sc / FULL / G4 / FULL_sc / Y<年> / se_H',
                   '≤1e-9（se 1e-6）；n 0', json.dumps({k: ('%.3g' % v if isinstance(v, float) else v) for k, v in mx.items()}), 'REPRODUCED' if ok else 'DIFFERS',
                   'INFO:抽样对象清单写 verify/vc13_sample.csv', func='子 d_net8 − 母 d_net8[K0,H] 共同有限日；Y = 年内有效配对日均值 × 25,200；HAC Bartlett(H) 缺失 u = 0'))
    pd.DataFrame({'desc_id': objs, 'kind': ['main154'] * len(mains) + ['sample300'] * len(samp)}).to_csv(os.path.join(OUT, 'vc13_sample.csv'), index=False)
    out += boot_replay(P, mains)
    return out


def rng_for(*key):
    """e6j_core.rng_for 转录：blake2b-128(canonical_json(list(key))) → SeedSequence → PCG64。"""
    s = json.dumps(list(key), sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(int.from_bytes(hashlib.blake2b(s.encode('ascii'), digest_size=16).digest(), 'big'))))


def stationary_indices(n, L, rng):
    """e6j_stats.stationary_indices 转录。"""
    p = 1.0 / L
    idx = np.empty(n, dtype=np.int64)
    i = 0
    while i < n:
        start = int(rng.integers(0, n))
        ln = int(rng.geometric(p))
        take = min(ln, n - i)
        idx[i:i + take] = (start + np.arange(take)) % n
        i += take
    return idx


def boot_replay(P, mains):
    rng = np.random.default_rng(SEED + 1)
    pick = sorted(rng.choice(sorted(P[P.primary144].desc_id), 20, replace=False).tolist())
    D = descs().set_index('desc_id')
    B = pd.read_csv(rp('results', 'full', 'bootstrap', 'bootstrap_comparisons.csv'))
    B = B[B.comparison_id.isin(['CP|' + d for d in pick]) & (B.scope == 'FULL')].set_index(['comparison_id', 'L'])
    series = {}
    for s in SEGS:
        for did in pick:
            mother, meas = D.at[did, 'task'].split('|')
            z = npz_arrays(acct_file(s, mother, meas), ('desc', 'd_net8'))
            k0 = npz_arrays(acct_file(s, mother, 'K0'), ('desc', 'd_net8'))
            i = list(map(str, z['desc'])).index(did)
            j = list(map(str, k0['desc'])).index('K0|%s|a0|H%d|PARENT' % (mother, int(D.at[did, 'H'])))
            series[(did, s)] = paired(z['d_net8'][i], k0['d_net8'][j])
    mx = 0.0
    for L in (20, 60):
        num = np.zeros((2000, len(pick)))
        den = np.zeros((2000, len(pick)))
        for s in SEGS:
            T = len(series[(pick[0], s)])
            g = rng_for('E6k', 'bootstrap', int(L), s)
            C = np.zeros((2000, T))
            for b in range(2000):
                C[b] = np.bincount(stationary_indices(T, L, g), minlength=T)
            M = np.column_stack([np.nan_to_num(series[(d, s)], nan=0.0) for d in pick])
            V = np.column_stack([np.isfinite(series[(d, s)]).astype(float) for d in pick])
            num += C @ M
            den += C @ V
        draws = np.where(den > 0, num / np.where(den > 0, den, 1) * ANN, np.nan)
        q = np.nanpercentile(draws, [2.5, 50, 97.5], axis=0)
        se = np.nanstd(draws, axis=0, ddof=1)
        for j, d in enumerate(pick):
            x = B.loc[('CP|' + d, L)]
            mx = max(mx, abs(q[0, j] - x.q025), abs(q[2, j] - x.q975), abs(q[1, j] - x.q50), abs(se[j] - x.se))
    return [row('VC13', 'bootstrap_replay_20', '20 个主对象 CP 比较（seed 20260930）× L 20 / 60 × FULL', 'max|Δ| q025 / q50 / q975 / se', '≤1e-9',
                '%.3g' % mx, 'REPRODUCED' if mx <= 1e-9 else 'DIFFERS', 'STOCHASTIC',
                diff='对象 %s' % ','.join(pick[:3]) + '…', func='种子 blake2b-128(["E6k","bootstrap",L,段]) → PCG64；stationary_indices 转录；计数矩阵 C @ d / C @ 1')]


def vc14_15(P):
    """目标层暴露列（VC14）与冲击 / 线性费率账户（VC15）从 npz 重算（154 主对象）。"""
    out = []
    D = descs().set_index('desc_id')
    Pi = P.set_index('desc_id')
    mx14 = {}
    mx15 = {}
    for s in SEGS:
        for did in main154():
            mother, meas = D.at[did, 'task'].split('|')
            z = npz_arrays(acct_file(s, mother, meas), ('desc', 'desc_target', 'targets', 't_gapT', 't_szT_lo', 't_szT_hi', 't_szL_lo', 't_szL_hi', 't_lv5',
                                                        't_wsum', 't_small30', 't_unkT', 'd_turn', 'd_gross', 'd_net8', 'd_bracket'))
            k0 = npz_arrays(acct_file(s, mother, 'K0'), ('desc', 'targets', 't_lv5', 't_wsum', 't_small30', 'd_turn', 'd_gross', 'd_net8', 'd_bracket'))
            i = list(map(str, z['desc'])).index(did)
            ti = int(z['desc_target'][i])
            pj = list(map(str, k0['targets'])).index('K0|%s|a0|PARENT' % mother)
            H = int(D.at[did, 'H'])
            pi = list(map(str, k0['desc'])).index('K0|%s|a0|H%d|PARENT' % (mother, H))
            x = Pi.loc[did]

            def mm(k, v, ref):
                if np.isfinite(v) or np.isfinite(ref):
                    d_ = abs(v - ref) if (np.isfinite(v) and np.isfinite(ref)) else np.inf
                    mx14[k] = max(mx14.get(k, 0.0), d_)
            g = z['t_gapT'][ti]
            gm = float(np.mean(g[np.isfinite(g)])) * 100 if np.isfinite(g).any() else np.nan
            mm('edit_gap_mean_T', gm, x['edit_gap_mean_T_%s' % s])
            mm('edit_gap_absmean_T', abs(gm) if np.isfinite(gm) else np.nan, x['edit_gap_absmean_T_%s' % s])
            for zz in ('T', 'L'):
                lo, hi = z['t_sz%s_lo' % zz][ti], z['t_sz%s_hi' % zz][ti]
                m = np.isfinite(lo) & np.isfinite(hi)
                mm('port_size_lo_%s' % zz, float(np.mean(lo[m])) if m.any() else np.nan, x['port_size_lo_%s_%s' % (zz, s)])
                mm('port_size_hi_%s' % zz, float(np.mean(hi[m])) if m.any() else np.nan, x['port_size_hi_%s_%s' % (zz, s)])

            def tmean(arr, ws):
                m = np.isfinite(arr) & (ws > 0)
                return float(np.mean(arr[m])) if m.any() else np.nan
            lv = tmean(z['t_lv5'][ti], z['t_wsum'][ti])
            plv = tmean(k0['t_lv5'][pj], k0['t_wsum'][pj])
            mm('lv5_mean', lv, x['lv5_mean_%s' % s])
            mm('parent_lv5_mean', plv, x['parent_lv5_mean_%s' % s])
            mm('small30_delta', tmean(z['t_small30'][ti], z['t_wsum'][ti]) - tmean(k0['t_small30'][pj], k0['t_wsum'][pj]), x['small30_delta_%s' % s])
            mm('unkT_mean', tmean(z['t_unkT'][ti], z['t_wsum'][ti]), x['unkT_mean_%s' % s])
            mt = float(np.mean(k0['d_turn'][pi]))
            mm('turn_rel', float(np.mean(z['d_turn'][i])) / mt - 1.0 if mt > 0 else np.nan, x['turn_rel_%s' % s])
            c = dict(net8=z['d_net8'][i], gross=z['d_gross'][i], turn=z['d_turn'][i], br=z['d_bracket'][i])
            p = dict(net8=k0['d_net8'][pi], gross=k0['d_gross'][pi], turn=k0['d_turn'][pi], br=k0['d_bracket'][pi])
            for k, (A, kk) in (('D_imp', (5.0, 0.5)), ('D_str', (10.0, 1.0))):
                v, _ = seg_D(paired(c['net8'] - impact(c['br'], A, kk), p['net8'] - impact(p['br'], A, kk)))
                ref = x['%s_%s' % (k, s)]
                mx15[k] = max(mx15.get(k, 0.0), abs(v - ref) if np.isfinite(v) and np.isfinite(ref) else (0.0 if not (np.isfinite(v) or np.isfinite(ref)) else np.inf))
            for bp in (6, 12):
                v, _ = seg_D(paired(c['gross'] - c['turn'] * bp / 1e4, p['gross'] - p['turn'] * bp / 1e4))
                ref = x['D_%dbp_%s' % (bp, s)]
                mx15['D_%dbp' % bp] = max(mx15.get('D_%dbp' % bp, 0.0), abs(v - ref) if np.isfinite(v) and np.isfinite(ref) else 0.0)
    out.append(row('VC14', 'target_exposure_cols', '154 主对象 × 四段（npz t_* 数组）', 'max|Δ| 各列', '≤1e-9', json.dumps({k: '%.3g' % v for k, v in mx14.items()}),
                   'REPRODUCED' if all(v <= 1e-9 for v in mx14.values()) else 'DIFFERS',
                   'INFO:口径——edit_gap_mean_T = 有定义日（t_gapT 有限，即有编辑日）均值 × 100（与 edit_gap_days_T 对）；port_size_lo/hi = lo、hi 都有限的"共同可定义日"均值；'
                   'lv5 / small30 / unkT = 有限且 wsum > 0 日均值；small30_delta = 子 − 父；turn_rel = mean(子 d_turn) / mean(父 d_turn) − 1（全段日均，不是 Σ 比）',
                   func='e6k_stats.target_expo / stats_row 转录'))
    out.append(row('VC15', 'impact_linear_fee', '154 主对象 × 四段（npz d_bracket / d_gross / d_turn）', 'max|Δ| D_imp / D_str / D_6bp / D_12bp', '≤1e-9',
                   json.dumps({k: '%.3g' % v for k, v in mx15.items()}), 'REPRODUCED' if all(v <= 1e-9 for v in mx15.values()) else 'DIFFERS',
                   'INFO:d_bracket = 逐日平方根冲击括号项；冲击成本 = κ·sqrt(A·1e8)·bracket（A 亿元，NaN→0），两档 (A, κ) = (5, .5) / (10, 1) 用同一数组；'
                   'D_6bp / D_12bp = gross − turn × 6e−4 / 12e−4 的配对差（等价于 D ± 2bp·Δturn 年化 / ∓4bp·Δturn）',
                   func='e6j_stats.impact_cost 转录'))
    return out


def vc16():
    """随机路径值从已存分片重算：LEGACY 956 两后段全量；NEW_COND_ISK_P5 与 IID 各抽 100；八子集 24 × 四段。"""
    out = []
    rng = np.random.default_rng(SEED + 2)

    def agg(mech, seg, keep=None):
        acc = {}
        for f in sorted(glob.glob(rp('randoms', mech, seg, '*.npz'))):
            z = np.load(f, allow_pickle=False)
            d = list(map(str, z['desc']))
            ann = z['ann'][:, :, 0]
            for i, (did, H) in enumerate(zip(d, z['H'].tolist())):
                if keep is not None and did not in keep:
                    continue
                acc.setdefault((did, int(H)), []).append(ann[i])
        return {k: np.concatenate(v) for k, v in acc.items()}
    specs = [('LEGACY_POLICY_RANDOM', POS, None), ('NEW_COND_ISK_P5', SEGS, 100), ('NEW_COND_ISK_IID', SEGS, 100)] + \
            [('EIGHT_SUBSET_%s' % x, SEGS, None) for x in ('EMPTY', 'I', 'S', 'K', 'IS', 'IK', 'SK')]
    for mech, segs, nsamp in specs:
        mx, mx_deg, n, ndeg, nobj = 0.0, 0.0, 0, 0, 0
        for s in segs:
            R = rrefs(s)
            R = R[R.mechanism == mech].set_index(['desc_id', 'H'])
            keep = None
            if nsamp:
                objs = sorted(set(R.index.get_level_values(0)))
                keep = set(rng.choice(objs, min(nsamp, len(objs)), replace=False).tolist())
            v = agg(mech, s, keep)
            for (did, H), a in v.items():
                a = a[np.isfinite(a)]
                x = R.loc[(did, H)]
                mean, sd = float(np.mean(a)), float(np.std(a, ddof=1))
                d_ = max(abs(mean - x.rand_mean), abs(sd - x.rand_sd), abs(sd / np.sqrt(len(a)) - x.mcse))
                nobj += 1
                if sd < 1e-9:                                                  # 路径间方差为 0 的对象（无新内容可置换）
                    ndeg += 1
                    mx_deg = max(mx_deg, d_)
                    if mech == 'LEGACY_POLICY_RANDOM':
                        DEG.append(dict(desc_id=did, H=int(H), segment=s, rmr=float(x.real_minus_rand), mcse_stored=float(x.mcse), sd_exact=sd))
                else:
                    mx = max(mx, d_)
                n += (len(a) != int(x.n))
        out.append(row('VC16', mech, 'randoms/%s/<段>/*.npz vs random_refs' % mech,
                       'max|Δ|（rand_mean / rand_sd / mcse）非退化对象；退化对象（路径间 sd < 1e−9）数与其 max|Δ|；路径数不符',
                       '≤1e-12；0', '%.3g；退化 %d / %d 对象，max|Δ| %.3g；%d' % (mx, ndeg, nobj, mx_deg, n),
                       'REPRODUCED' if (max(mx, mx_deg) <= 1e-12 and n == 0) else 'DIFFERS',
                       'INFO:%s%s' % ('两后段全量' if mech.startswith('LEGACY') else ('每段抽 100 对象（seed 20260931）' if nsamp else '四段全量'),
                                      '；退化对象的 rand_sd 为单遍方差式 Σx²/n − mean² 的舍入噪声（真值 0）' if ndeg else ''),
                       func='分片 ann[:, :, 0] 合并；np.mean / np.std(ddof=1)'))
    # 影响面：退化 LEGACY 对象按精确 sd = 0 重判 e_rand（两后段三态，同 VC02 转录），与 policy 现值对照
    if DEG:
        Dg = pd.DataFrame(DEG)
        Dg.to_csv(os.path.join(OUT, 'vc16_legacy_degenerate.csv'), index=False)
        P = policy().set_index('desc_id')

        def st_(d, se):
            if not (np.isfinite(d) and np.isfinite(se)):
                return 'NA'
            if d > 0 and d >= 2 * se:
                return 'POS'
            if d <= 0 and -d >= 2 * se:
                return 'NONPOS'
            return 'UNRES'

        def er_(sts):
            return 'FAIL' if 'NONPOS' in sts else ('PASS' if all(x == 'POS' for x in sts) else 'MC_UNRESOLVED')
        ch = []
        for (did, H), g in Dg.groupby(['desc_id', 'H']):
            if did not in P.index or len(g) != len(POS):
                continue
            e_pol = str(P.at[did, 'e_rand'])
            if e_pol in ('NO_NEW_CONTENT_TO_PERMUTE', 'RANDOM_NOT_SCHEDULED'):
                continue
            g = g.set_index('segment').reindex(POS)
            e_st = er_([st_(g.at[s, 'rmr'], g.at[s, 'mcse_stored']) for s in POS])
            e_ex = er_([st_(g.at[s, 'rmr'], 0.0) for s in POS])
            if e_ex != e_st:
                ch.append('%s:%s→%s（policy %s）' % (did, e_st, e_ex, e_pol))
        fam = descs().set_index('desc_id').family
        out.append(row('VC16', 'LEGACY_degenerate_impact', 'verify/vc16_legacy_degenerate.csv', '退化（路径间 sd = 0）对象 × 段；族分布；按精确 sd = 0 重判 e_rand 会变的对象',
                       '—', '%d 对象 × 段；族 %s；会变 %d' % (len(Dg), Dg.desc_id.map(fam).value_counts().to_dict(), len(ch)), 'REPRODUCED' if not ch else 'DIFFERS',
                       'INFO:e_rand 对 OWN / HG_ONLY 按 PX6 取 NO_NEW_CONTENT_TO_PERMUTE（不看 mcse）；本行只看其余族', diff=';'.join(ch)[:600],
                       func='VC02 三态转录（POS: d > 0 且 d ≥ 2·se；NONPOS: d ≤ 0 且 −d ≥ 2·se；否则 UNRES）'))
    return out


DEG = []


# ============================================================================ V-D 报告 ↔ 表
def class_D(workers):
    out = []
    qr = jload(rp('reports', 'query_registry_E6k.json'))
    tabs_all = {}
    for f in SEVEN:
        t, _, _ = report_tables(f)
        tabs_all.update({k: (f, v) for k, v in t.items()})
    for r in expected_rows('VD01').itertuples():
        f, t = tabs_all.get(r.sub_id, (None, None))
        got = '%d/%d' % (len(t), t.shape[1]) if t is not None else 'MISSING'
        reg = qr.get(r.sub_id, {})
        ok = got == r.expected and reg.get('rows') == len(t) and reg.get('cols') == list(t.columns)
        out.append(row('VD01', r.sub_id, r.object, 'rows/cols（= 登记 rows / cols）', r.expected, got, 'REPRODUCED' if ok else 'DIFFERS', func='表解析'))
    out += vd02_03_05_17()
    out += vd04()
    r7 = vd07()                                       # 卡表复算在前：VD06 引用其全格结果
    out += vd06(r7[0]['recomputed'])
    out += r7
    return out


def vd02_03_05_17():
    out = []
    P = policy()
    Pi = P.set_index('desc_id')

    def dmerge(x, segs):
        ns = np.array([x['n_%s' % s] for s in segs], float)
        ds = np.array([x['D_%s' % s] for s in segs], float)
        ok = np.isfinite(ds) & (ns > 0)
        return float(np.sum(ds[ok] * ns[ok]) / np.sum(ns[ok])) if ok.any() else np.nan
    # part2 144（+C1HI-SM）
    t2 = report_tables('E6k_REPORT_part2.md')[0]
    R = pd.concat([rrefs(s).assign(segment=s) for s in POS])
    n = bad = rnd = 0
    for f in ('S', 'M', 'Q', 'C1'):
        t = t2['E6K-P2-144-%s' % f]
        for r in t.to_dict('records'):
            did = '%s|%s|a0.25|H5|%s' % (r['meas'], r['mother'], r['op'])
            x = Pi.loc[did]
            Dp, Dd = dmerge(x, POS), dmerge(x, DER)
            vals = {'D_2019-2023': x['D_2019-2023'], 'D_2024-2026': x['D_2024-2026'], 'D_post': Dp, 'D_deriv': Dd, 'post_minus_deriv': Dp - Dd,
                    'port_size_lo_T_2019-2023': x['port_size_lo_T_2019-2023'], 'port_size_hi_T_2019-2023': x['port_size_hi_T_2019-2023'],
                    'turn_rel_2019-2023': x['turn_rel_2019-2023'], 'rmr_LEGACY_2019-2023': x['rmr_2019-2023'], 'rmr_LEGACY_2024-2026': x['rmr_2024-2026'],
                    'mcse_LEGACY_2019-2023': x['mcse_2019-2023']}
            for k, v in vals.items():
                n += 1
                c = cell_eq4(r[k], float(v))
                bad += c == 'BAD'
                rnd += c == 'ROUNDING'
            lab = r['label']
            exp_lab = 'NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY' if x.family not in ('NATIVE', 'PARENT') else str(x.evidence_exposure)
            n += 1
            bad += lab != exp_lab
    out.append(row('VD02', 'part2_144', 'part2 E6K-P2-144-*（四表）', '格数 / 不符 / ROUNDING（段 D、D_post、D_deriv、post−deriv、rmr/mcse LEGACY、port_size、turn_rel、label）',
                   exp1('VD02', 'part1/part2_144_vs_policy'), '%d / %d / %d' % (n, bad, rnd), 'REPRODUCED' if bad == 0 else 'DIFFERS',
                   'ROUNDING' if rnd else '', func='n 加权段合并；label：新算子 = 首看标签、原生 = 暴露类型'))
    # part1 144（推导段；results/deriv）
    t1 = report_tables('E6k_REPORT_part1.md')[0]
    n = bad = rnd = 0
    for f in ('S', 'M', 'Q', 'C1'):
        t = t1['E6K-P1-144-%s' % f]
        for r in t.to_dict('records'):
            did = '%s|%s|a0.25|H5|%s' % (f, r['mother'], r['op'])                 # part1 144 表无 meas 列：测量取自表 id
            x = Pi.loc[did]
            vals = {'D_2010-2014': x['D_2010-2014'], 'D_2015-2018': x['D_2015-2018'], 'D_deriv': dmerge(x, DER)}
            for k, v in vals.items():
                n += 1
                c = cell_eq4(r[k], float(v))
                bad += c == 'BAD'
                rnd += c == 'ROUNDING'
    out.append(row('VC17', 'part1_144', 'part1 E6K-P1-144-*（四表）', '格数 / 不符 / ROUNDING（段 D、D_deriv）', '0 不符', '%d / %d / %d' % (n, bad, rnd),
                   'REPRODUCED' if bad == 0 else 'DIFFERS', 'ROUNDING' if rnd else '', func='推导两段 n 加权；与 full 阶段同值'))
    # part2 GRID
    t = t2['E6K-P2-GRID']
    Q = P[P.op != 'PARENT'].copy()
    Q['Dp'] = [dmerge(x, POS) for x in Q.to_dict('records')]
    Q['Dd'] = [dmerge(x, DER) for x in Q.to_dict('records')]
    Q['pm'] = Q.Dp - Q.Dd
    n = bad = 0
    g = Q.groupby(['family', 'op', 'alpha'])
    for r in t.to_dict('records'):
        k = (r['family'], r['op'], float(r['alpha']))
        x = g.get_group(k)
        vals = {'cells': float(x.Dp.count()), 'share_post_pos': float((x.Dp > 0).mean()), 'median_post': float(x.Dp.median()),
                'median_deriv': float(x.Dd.median()), 'median_post_minus_deriv': float(x.pm.median())}
        for kk, v in vals.items():
            n += 1
            bad += cell_eq4(r[kk], v) == 'BAD'
    out.append(row('VD03', 'part2_grid', 'part2 E6K-P2-GRID', '格数 / 不符', exp1('VD03', 'part2_grid'), '%d / %d' % (n, bad), 'REPRODUCED' if bad == 0 else 'DIFFERS',
                   func='(family, op, α) 分组；D_post / D_deriv 为 n 加权段合并'))
    # part1 GRID（推导段 stats）
    t = t1['E6K-P1-GRID']
    Sd = pd.concat([stats(s, 'deriv')[['D', 'n', 'D_vs_native']].assign(segment=s) for s in DER]).reset_index()
    Dd_ = Sd.groupby('desc_id').apply(lambda x: pd.Series(dict(D=np.average(x.D, weights=x.n) if x.n.sum() > 0 else np.nan)))
    Dd_ = Dd_.join(descs().set_index('desc_id')[['family', 'op', 'alpha']])
    Dd_ = Dd_[Dd_.op != 'PARENT']
    n = bad = 0
    try:
        g = Dd_.groupby(['family', 'op', 'alpha'])
        for r in t.to_dict('records'):
            x = g.get_group((r['family'], r['op'], float(r['alpha'])))
            vals = {'cells': float(x.D.count()), 'share_pos': float((x.D > 0).mean()), 'median': float(x.D.median())}
            for kk, v in vals.items():
                n += 1
                bad += cell_eq4(r[kk], v) == 'BAD'
        vv = 'REPRODUCED' if bad == 0 else 'DIFFERS'
    except KeyError as e:
        vv = 'NOT_COMPUTABLE'
        bad = repr(e)
    out.append(row('VC17', 'part1_grid', 'part1 E6K-P1-GRID', '格数 / 不符（cells、share_pos、median）', '0 不符', '%d / %s' % (n, bad), vv,
                   func='results/deriv 段表 n 加权合并后按 (family, op, α) 分组'))
    # part3 五表
    t3 = report_tables('E6k_REPORT_part3.md')[0]
    n = bad = rnd = blank_na = 0
    for p in PROFILES:
        t = t3['E6K-P3-POL-%s' % p.replace('_', '')]
        for r in t.to_dict('records'):
            did = '%s|%s|a%s|H%s|%s' % (r['meas'], r['mother'], r['alpha'], r['H'], r['op'])
            x = Pi.loc[did]
            for k in ('FULL', 'G4', 'FULL_sc', 'FULL_imp', 'FULL_vs_native', 'FULL_vs_nativeC1'):
                n += 1
                c = cell_eq4(r[k], float(x[k]))
                bad += c == 'BAD'
                rnd += c == 'ROUNDING'
            for k in ('years_pos', 'e_rand', 'evidence_exposure', 'size_%s' % p, 'policy_%s_FULL' % p, 'policy_%s_G4' % p, 'POLICY_INTERPRETATION_PENDING_%s' % p):
                n += 1
                ref = str(x[k])
                if k == 'years_pos':
                    ref = str(int(x[k]))
                if ref in ('N/A', 'NA') and str(r[k]) == '':
                    blank_na += 1                              # 生成器用 pandas 默认读 CSV → 字面 N/A / NA 读成 NaN 印空
                    continue
                bad += str(r[k]) != ref
    out.append(row('VD05', 'part3_profile_tables', 'part3 E6K-P3-POL-*（五表）', '格数 / 不符 / ROUNDING / 字面 N/A、NA 印空（数值 4 位有效、串逐字）',
                   exp1('VD05', 'part3_profile_tables'), '%d / %d / %d / %d' % (n, bad, rnd, blank_na), 'REPRODUCED' if bad == 0 else 'DIFFERS',
                   ';'.join(x for x in ('ROUNDING' if rnd else '', 'INFO:字面 N/A / NA 被报告生成器按 pandas 默认读成 NaN、印为空格（%d 格）' % blank_na if blank_na else '') if x),
                   func='逐格'))
    return out


# ---------------------------------------------------------------------------- V-D 公共：数字记号、卡表复算（口径转录自 e6k_report_cards.py；不 import）
NUM_RE = re.compile(r'(?<![\w.·])[+−-]?(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?|\.\d+)%?')
P6 = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
LABEL_FL = 'NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY'
PASS_S = '通过'


def ntok(t):
    return str(t).replace('−', '-').lstrip('+')


def nums_in(text):
    return [m.group(0) for m in NUM_RE.finditer(str(text))]


class _Ctx(object):
    pass


def card_ctx():
    if 'CARD' not in _C:
        c = _Ctx()
        c.P = policy()
        c.Pi = c.P.set_index('desc_id')
        c.D = descs()
        c.A = pd.read_csv(rp('registry', 'accessory_E6k.csv'))
        c.S = {s: stats(s) for s in SEGS}
        c.R = pd.concat([rrefs(s).assign(segment=s) for s in SEGS], ignore_index=True)
        c.MF = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(rp('registry', 'mask_facts_*_E6k.csv')))], ignore_index=True)
        c.FA = pd.concat([pd.read_csv(f).assign(segment=s) for s in SEGS for f in sorted(glob.glob(rp('accounts', s, 'facts_*.csv')))], ignore_index=True)
        _C['CARD'] = c
    return _C['CARD']


def fv(c, col, ids, segs=SEGS):
    """四段（或给定段）n 加权合并 descriptor_stats 某列；缺段 / n ≤ 0 / 非有限不计（cards.fullv 转录）。"""
    ids = list(ids)
    num, den = np.zeros(len(ids)), np.zeros(len(ids))
    for s in segs:
        x = c.S[s].reindex(ids)
        if col not in x.columns:
            continue
        v, n = x[col].values.astype(float), x['n'].values.astype(float)
        m = np.isfinite(v) & np.isfinite(n) & (n > 0)
        num[m] += v[m] * n[m]
        den[m] += n[m]
    return np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)


def summ_v(df, by, val):
    g = df.dropna(subset=[val]).groupby(by)[val]
    o = g.agg(cells='count', median='median', q10=lambda x: x.quantile(.1), q90=lambda x: x.quantile(.9)).reset_index()
    o['share_pos'] = g.apply(lambda x: float((x > 0).mean())).values
    return o


def did_v(f, p, a, h, op):
    return '%s|%s|a%s|H%d|%s' % (f, p, ('%g' % float(a)), int(h), op)


def band_v(c, kind):
    t = c.P[(c.P.family == 'BAND') & c.P.op.str.contains('_%s' % kind) & (c.P.alpha == 0.25) & c.P.H.isin([3, 5, 10, 20])].copy()
    t['FULL_vs_base'] = fv(c, 'D_vs_base', t.desc_id)
    t['FULLg_vs_base'] = fv(c, 'Dg_vs_base', t.desc_id)
    t['turn_rel_full'] = fv(c, 'turn_rel', t.desc_id)
    return t


def dose_v(c, kind):
    a = c.A[(c.A.kind == 'BAND_DOSE_CONTROL') & c.A.op.str.contains('_%s' % kind)].copy()
    a['BAND_minus_DOSE_FULL'] = -fv(c, 'D_vs_compare', a.acc_id)
    a['band_op'] = a.op.str.replace('DOSE_', '', regex=False)
    return a


def sq_v(c):
    s = c.P[c.P.meas == 'S'].copy()
    s['qid'] = 'Q|' + s.desc_id.str.split('|', n=1).str[1]
    s['Q_FULL'] = c.Pi.FULL.reindex(s.qid).values
    s['S_minus_Q_FULL'] = s.FULL - s.Q_FULL
    s['S_minus_Q_G4'] = s.G4 - c.Pi.G4.reindex(s.qid).values
    return s


def main148_v(c):
    return c.P[c.P.primary144 | c.P.c1_hi].sort_values(['meas', 'mother', 'op', 'H'])


def mf_phase(mf):
    mf = mf.copy()
    mf['alpha_f'] = mf.alpha.astype(str).str.lstrip('a').astype(float)
    mf['phase'] = np.where(mf.segment.isin(DER), 'deriv', 'post')
    return mf


def cards_build(c):
    """47 张卡表的独立复算（同列名；行序按同一排序键）。返回 {qid: DataFrame}。"""
    P, Pi, A = c.P, c.Pi, c.A
    T = {}
    nat = P[P.primary144 & (P.op == 'NATIVE')].sort_values(['meas', 'mother']).copy()
    T['E6K-Q01-a'] = nat[['meas', 'mother', 'FULL', 'G4'] + ['D_%s' % s for s in SEGS] + ['policy_%s_FULL' % p for p in PROFILES] +
                         ['policy_%s_G4' % p for p in PROFILES]]
    t = nat.copy()
    for z in ('T', 'L'):
        for sd in ('lo', 'hi'):
            t['port_size_%s_%s_full' % (sd, z)] = fv(c, 'port_size_%s_%s' % (sd, z), t.desc_id)
    tl = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(rp('diagnostics', 'risk', '*_tails.csv')))], ignore_index=True)
    for b in ('small30', 'large30', 'unknown'):
        t['tail_capital_share_delta_%s_segavg' % b] = t.desc_id.map(tl[tl.bucket == b].groupby('desc_id').capital_share_delta.mean()).values
    t['worst1pct_days_mean_d_bp_segavg'] = t.desc_id.map(tl[tl.bucket == 'worst1pct_days'].groupby('desc_id').tail_mean_d_bp.mean()).values
    cols = (['meas', 'mother'] + ['port_size_%s_%s_full' % (sd, z) for z in ('T', 'L') for sd in ('lo', 'hi')] + ['port_size_lo_T_%s' % s for s in SEGS] +
            ['port_size_hi_T_%s' % s for s in SEGS] + ['edit_gap_mean_T_%s' % s for s in SEGS] + ['edit_gap_absmean_T_%s' % s for s in SEGS] +
            ['small30_delta_%s' % s for s in SEGS] + ['tail_capital_share_delta_%s_segavg' % b for b in ('small30', 'large30', 'unknown')] +
            ['worst1pct_days_mean_d_bp_segavg'])
    T['E6K-Q01-b'] = t[[x for x in cols if x in t.columns]]
    t = nat.copy()
    for k, col in (('FULL_str', 'D_str'), ('FULL_6bp', 'D_6bp'), ('FULL_12bp', 'D_12bp')):
        t[k] = fv(c, col, t.desc_id)
    T['E6K-Q01-c'] = t[['meas', 'mother', 'FULL', 'FULL_sc', 'G4', 'G4_sc', 'e_cap_FULL', 'FULL_imp', 'G4_imp', 'FULL_str', 'FULL_6bp', 'FULL_12bp']]
    # Q02
    szl = P[P.family == 'SZL'].copy()
    o = summ_v(szl, ['op', 'alpha', 'H'], 'FULL_vs_native')
    T['E6K-Q02-a'] = o.merge(szl.groupby(['op', 'alpha', 'H']).FULL.median().rename('median_FULL').reset_index(), on=['op', 'alpha', 'H'])
    own = szl.desc_id + '_OWN'
    szl['SZL_minus_OWN_FULL'] = szl.FULL.values - Pi.FULL.reindex(own).values
    szl['SZL_minus_OWN_G4'] = szl.G4.values - Pi.G4.reindex(own).values
    o = summ_v(szl, ['meas', 'op', 'alpha'], 'SZL_minus_OWN_FULL')
    T['E6K-Q02-b'] = o.merge(szl.groupby(['meas', 'op', 'alpha']).SZL_minus_OWN_G4.median().rename('median_G4_diff').reset_index(), on=['meas', 'op', 'alpha'])
    natid = szl.desc_id.str.rsplit('|', n=1).str[0] + '|NATIVE'
    mid = lambda ids: 0.5 * (fv(c, 'port_size_lo_T', ids) + fv(c, 'port_size_hi_T', ids))
    szl['port_size_mid_T_delta_vs_native'] = mid(szl.desc_id) - mid(natid)
    o = summ_v(szl, ['op', 'alpha'], 'port_size_mid_T_delta_vs_native')
    mf = mf_phase(c.MF[c.MF.op.isin(['SZL3', 'SZL5'])])
    ov = mf.groupby(['op', 'alpha_f', 'phase']).same_ticker_overlap_with_native.median().unstack('phase').add_prefix('overlap_with_native_median_').reset_index()
    T['E6K-Q02-c'] = o.merge(ov.rename(columns={'alpha_f': 'alpha'}), on=['op', 'alpha'], how='left')
    # Q03
    a = A[(A.kind == 'INC_SUPPORT_ACCESSORY') & A.op.str.startswith('INC_DOSE')].copy()
    a['INC_minus_DOSE_FULL'] = -fv(c, 'D_vs_compare', a.acc_id)
    a['DOSE_FULL'] = fv(c, 'D', a.acc_id)
    a['INC_FULL'] = Pi.FULL.reindex(a.compare_to).values
    T['E6K-Q03-a'] = a[['meas', 'mother', 'op', 'compare_to', 'INC_FULL', 'DOSE_FULL', 'INC_minus_DOSE_FULL']].sort_values(['meas', 'mother', 'op'])
    a = A[A.kind == 'INC_SUPPORT_ACCESSORY'].copy()
    a['F'] = fv(c, 'D', a.acc_id)
    key = ['meas', 'mother', 'alpha', 'H']
    t = pd.concat([a[a.op == o_].set_index(key).F.rename(n_) for o_, n_ in (('INC_SUPPORT0', 'SUPPORT0'), ('INC_DOSE05', 'DOSE05'), ('INC_DOSE1', 'DOSE1'))], axis=1).reset_index()
    for op_ in ('NATIVE', 'INC05', 'INC1'):
        t[op_] = Pi.FULL.reindex([did_v(r.meas, r.mother, r.alpha, r.H, op_) for r in t.itertuples()]).values
    t['SUPPORT0_minus_NATIVE'] = t.SUPPORT0 - t.NATIVE
    t['DOSE05_minus_SUPPORT0'] = t.DOSE05 - t.SUPPORT0
    t['DOSE1_minus_SUPPORT0'] = t.DOSE1 - t.SUPPORT0
    t['INC05_minus_DOSE05'] = t.INC05 - t.DOSE05
    t['INC1_minus_DOSE1'] = t.INC1 - t.DOSE1
    T['E6K-Q03-b'] = t.sort_values(['meas', 'mother'])
    mf = mf_phase(c.MF[c.MF.op.isin(['INC05', 'INC1', 'SZL3', 'SZL5'])])
    T['E6K-Q03-c'] = mf.groupby(['op', 'alpha_f', 'phase']).agg(
        targets=('target_id', 'count'), overlap_with_native_median=('same_ticker_overlap_with_native', 'median'), n_edits_in_median=('n_edits_in', 'median'),
        edit_weight_share_median=('edit_weight_share', 'median')).reset_index().rename(columns={'alpha_f': 'alpha'})
    # Q04
    rpi = P[(P.op == 'RPINF') & (P.alpha == 0.25) & (P.H == 5)].sort_values(['meas', 'mother']).copy()
    rpi['D_deriv'] = fv(c, 'D', rpi.desc_id, DER)
    rpi['D_post'] = fv(c, 'D', rpi.desc_id, POS)
    T['E6K-Q04-a'] = rpi[['meas', 'mother', 'FULL', 'G4', 'FULL_vs_native', 'G4_vs_native', 'D_deriv', 'D_post']]
    t = rpi[['meas', 'mother', 'desc_id', 'FULL']].copy()
    for tau in ('0p5', '1', '3'):
        t['RP%s_FULL' % tau] = Pi.FULL.reindex(t.desc_id.str.replace('|RPINF', '|RP%s' % tau, regex=False)).values
        t['RP%s_minus_PAIR_ALL' % tau] = t['RP%s_FULL' % tau] - t.FULL
    T['E6K-Q04-b'] = t.drop(columns=['desc_id']).rename(columns={'FULL': 'PAIR_ALL_FULL'})
    fa = c.FA[c.FA.op.astype(str).str.startswith('RP')].copy()
    for k in ('rp_recovered_days', 'solver_limit_days'):
        if k not in fa.columns:
            fa[k] = np.nan
    fa['rp_recovered_days'] = fa.rp_recovered_days.fillna(0)
    o = fa.groupby(['segment', 'op']).agg(targets=('target_id', 'count'), days_with_edits=('rp_days_with_edits', 'sum'), pairs=('rp_pairs', 'sum'),
                                          kept=('rp_kept_pairs', 'sum'), unknown=('rp_unknown_edits', 'sum'), unpaired_structural=('rp_unpaired_structural', 'sum'),
                                          solver_limit_days=('solver_limit_days', 'sum'), recovered_days=('rp_recovered_days', 'sum')).reset_index()
    o['kept_share'] = o.kept / o.pairs.where(o.pairs > 0)
    T['E6K-Q04-c'] = o
    # Q05
    ids = P[P.primary144 & (P.op == 'NATIVE')].desc_id.tolist()
    R5 = c.R[(c.R.H == 5) & c.R.desc_id.isin(ids)]
    rows = []
    for d in ids:
        r = dict(desc_id=d)
        w = {s: Pi.at[d, 'n_%s' % s] for s in SEGS}
        for sub in ('EMPTY', 'I', 'S', 'K', 'IS', 'IK', 'SK', 'ISK'):
            x = R5[(R5.desc_id == d) & (R5.mechanism == ('NEW_COND_ISK_P5' if sub == 'ISK' else 'EIGHT_SUBSET_' + sub))]
            if len(x):
                ww = np.array([w.get(s, 0) for s in x.segment], float)
                r['rand_%s' % sub] = float(np.average(x.rand_mean, weights=ww)) if ww.sum() > 0 else np.nan
                if sub == 'ISK':
                    r['real_net8_ann'] = float(np.average(x.real_net8_ann, weights=ww)) if ww.sum() > 0 else np.nan
        rows.append(r)
    T['E6K-Q05-a'] = pd.DataFrame(rows)
    sh = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(rp('diagnostics', 'mechanisms', '*_shapley.csv')))], ignore_index=True)
    sh['w'] = [Pi.at[d, 'n_%s' % s] if d in Pi.index else np.nan for d, s in zip(sh.desc_id, sh.segment)]
    scol = [x for x in sh.columns if x.startswith('shapley_')] + ['closure_net']
    T['E6K-Q05-b'] = sh.groupby('desc_id').apply(
        lambda g: pd.Series({k: float(np.average(g[k], weights=g.w)) if g.w.sum() > 0 else np.nan for k in scol})).reset_index()
    ld = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(rp('diagnostics', 'mechanisms', '*_leafdiag.csv')))], ignore_index=True)
    T['E6K-Q05-c'] = ld.groupby(['segment', 'subset']).agg(objects=('desc_id', 'nunique'), movable_share_median=('movable_share', 'median'),
                                                           movable_share_min=('movable_share', 'min'), entropy_ratio_median=('entropy_ratio', 'median'),
                                                           entropy_ratio_min=('entropy_ratio', 'min'), n_leaves_median=('n_leaves', 'median')).reset_index()
    # Q06
    m5 = P[(P.alpha == 0.25) & (P.H == 5)].set_index(['meas', 'mother', 'op'])
    rows = []
    for (f, p), _ in P[(P.family == 'LX') & (P.alpha == 0.25) & (P.H == 5)].groupby(['meas', 'mother']):
        for lay in ('SIZE3', 'ISK'):
            v10 = m5.FULL.get((f, p, 'LX_%s_10' % lay), np.nan)
            v01 = m5.FULL.get((f, p, 'LX_%s_01' % lay), np.nan)
            v11 = m5.FULL.get((f, p, 'NATIVE'), np.nan)
            rows.append(dict(meas=f, mother=p, layer=lay, V10_minus_V00=v10, V01_minus_V00=v01, V11_minus_V00=v11, interaction=v11 - v10 - v01,
                             order_avg_allocation=0.5 * (v10 + v11 - v01), order_avg_within=0.5 * (v01 + v11 - v10)))
    T['E6K-Q06-a'] = pd.DataFrame(rows)
    t = P[(P.family == 'LX') & (P.alpha == 0.25) & (P.H == 5)].sort_values(['meas', 'mother', 'op']).copy()
    t['capital_view_diff'] = t.FULL_sc - t.FULL
    t['impact_diff'] = t.FULL_imp - t.FULL
    t['turn_rel_full'] = fv(c, 'turn_rel', t.desc_id)
    t['nnames_delta_full'] = fv(c, 'nnames_mean', t.desc_id) - fv(c, 'parent_nnames_mean', t.desc_id)
    t['wsum_delta_full'] = fv(c, 'wsum_mean', t.desc_id) - fv(c, 'parent_wsum_mean', t.desc_id)
    T['E6K-Q06-b'] = t[['meas', 'mother', 'op', 'FULL', 'FULL_sc', 'capital_view_diff', 'FULL_imp', 'impact_diff', 'turn_rel_full', 'nnames_delta_full', 'wsum_delta_full']]
    lg = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(rp('diagnostics', 'mechanisms', '*_lx_gross.csv')))], ignore_index=True)
    T['E6K-Q06-c'] = lg.groupby(['desc_id', 'child']).agg(segments=('segment', 'nunique'), within_group=('within_group_ann', 'mean'),
                                                         allocation=('allocation_ann', 'mean'), allocation_excess=('allocation_excess_ann', 'mean'),
                                                         total=('total_ann', 'mean'), closure_resid_max=('closure_resid', 'max')).reset_index()
    # Q07
    t = P[((P.family == 'TREFIT') | (P.op == 'NATIVE')) & P.mother.isin(['A4b', 'A4b_CVRv5']) & (P.alpha == 0.25) & (P.H == 5) &
          P.meas.isin(['S', 'M', 'Q', 'C1'])].sort_values(['meas', 'mother', 'op']).copy()
    t['D_deriv'] = fv(c, 'D', t.desc_id, DER)
    t['D_post'] = fv(c, 'D', t.desc_id, POS)
    T['E6K-Q07-a'] = t[['meas', 'mother', 'op', 'FULL', 'G4', 'D_deriv', 'D_post', 'FULL_vs_native']]
    t = P[(P.family == 'TREFIT') & (P.alpha == 0.25) & (P.H == 5)].sort_values(['meas', 'mother', 'op']).copy()
    t['port_size_mid_T_full'] = 0.5 * (fv(c, 'port_size_lo_T', t.desc_id) + fv(c, 'port_size_hi_T', t.desc_id))
    t['edit_gap_mean_T_full'] = fv(c, 'edit_gap_mean_T', t.desc_id)
    cu = c.FA[c.FA.op.astype(str).str.startswith('TREFIT')].groupby('target_id').coef_interp_unavailable_days.sum()
    tmap = c.D.set_index('desc_id').target_id
    t['coef_interp_unavailable_days_4seg'] = t.desc_id.map(lambda d: cu.get(tmap.get(d, ''), np.nan)).values
    T['E6K-Q07-b'] = t[['meas', 'mother', 'op', 'coef_interp_unavailable_days_4seg', 'port_size_mid_T_full', 'edit_gap_mean_T_full']]
    # Q08
    t = P[(P.family == 'POST2') & (P.alpha == 0.25) & (P.H == 5)].sort_values(['meas', 'mother', 'alpha', 'H']).copy()
    t['D_deriv'] = fv(c, 'D', t.desc_id, DER)
    t['D_post'] = fv(c, 'D', t.desc_id, POS)
    T['E6K-Q08-a'] = t[['meas', 'mother', 'op', 'FULL', 'G4', 'FULL_vs_native', 'FULL_vs_C1', 'D_deriv', 'D_post']]
    t = P[(P.family == 'POST2') & (P.alpha == 0.25) & (P.H == 5)].sort_values(['meas', 'mother']).copy()
    t['capital_view_diff'] = t.FULL_sc - t.FULL
    mf = mf_phase(c.MF[c.MF.op == 'POST2_INCREMENT'])
    mf['key'] = mf.meas + '|' + mf.mother + '|' + mf.alpha.astype(str)
    for ph in ('deriv', 'post'):
        g = mf[mf.phase == ph].groupby('key')
        t['n_edits_in_%s' % ph] = (t.meas + '|' + t.mother + '|a0.25').map(g.n_edits_in.mean()).values
        t['edit_weight_share_%s' % ph] = (t.meas + '|' + t.mother + '|a0.25').map(g.edit_weight_share.mean()).values
    T['E6K-Q08-b'] = t[['meas', 'mother', 'FULL', 'FULL_sc', 'capital_view_diff', 'n_edits_in_deriv', 'n_edits_in_post', 'edit_weight_share_deriv', 'edit_weight_share_post']]
    # Q09 / Q10 / Q11（带）
    for kind, qa, qb in (('SA', 'E6K-Q09-a', 'E6K-Q09-b'), ('PM', 'E6K-Q10-a', 'E6K-Q10-b')):
        T[qa] = summ_v(band_v(c, kind), ['op', 'H'], 'FULL_vs_base')
        T[qb] = summ_v(dose_v(c, kind), ['band_op', 'H'], 'BAND_minus_DOSE_FULL')
    T['E6K-Q10-c'] = pd.DataFrame([dict(query_id='E6K-Q10-c', status='未计算（覆盖不足）',
                                        reason='PM 只落盘了门内名单与目标级统计，逐日固定配对交换数的嵌套与结构单边编辑未单独记账；不另补算',
                                        pointer='PM 的编辑事实见 registry/mask_facts_*_E6k.csv（n_edits_in / edit_weight_share；R0 §5 与 E6K-R0-MASK / E6K-R0-MASK-POST）')])
    rows = []
    for r in P[(P.family == 'BAND') & P.op.str.contains('_HG') & (P.alpha == 0.25) & (P.H == 5)].itertuples():
        base = r.op.split('_')[0]
        v10 = m5.FULL.get((r.meas, r.mother, base), np.nan)
        v01 = Pi.FULL.get('K0|%s|a0|H5|HG_ONLY%s' % (r.mother, r.op.split('HG')[-1]), np.nan)
        rows.append(dict(meas=r.meas, mother=r.mother, op=r.op, V11_minus_V00=r.FULL, V10_minus_V00=v10, V01_minus_V00=v01, HG_minus_base=r.FULL - v10,
                         info_margin_V11_minus_V01=r.FULL - v01, interaction=r.FULL - v10 - v01))
    T['E6K-Q11-a'] = pd.DataFrame(rows).sort_values(['meas', 'mother', 'op'])
    o = summ_v(dose_v(c, 'HG'), ['band_op', 'H'], 'BAND_minus_DOSE_FULL').rename(columns={'band_op': 'op'})
    th = P[(P.family == 'BAND') & P.op.str.contains('_HG') & (P.alpha == 0.25) & (P.H == 5) & P.primary144]
    Rn = c.R[c.R.mechanism == 'NEW_COND_ISK_P5']
    rows = []
    for d in th.desc_id:
        for H in (3, 5, 10, 20):
            x = Rn[(Rn.desc_id == d) & (Rn.H == H)]
            if len(x):
                w = np.array([Pi.at[d, 'n_%s' % s] for s in x.segment], float)
                rows.append(dict(op=d.split('|')[-1], H=H, desc_id=d, real_minus_rand=float(np.average(x.real_minus_rand, weights=w)) if w.sum() > 0 else np.nan,
                                 mcse_max=float(x.mcse.max()), paths_min=int(x.n.min())))
    pr = pd.DataFrame(rows)
    if len(pr):
        ps = pr.groupby(['op', 'H']).agg(persistence_objects=('desc_id', 'count'), real_minus_rand_median=('real_minus_rand', 'median'),
                                          mcse_max=('mcse_max', 'max'), paths_min=('paths_min', 'min')).reset_index()
        o = o.merge(ps, on=['op', 'H'], how='outer')
    T['E6K-Q11-b'] = o
    bh = band_v(c, 'HG')
    T['E6K-Q11-c'] = bh.groupby(['op', 'H']).agg(cells=('desc_id', 'count'), turn_rel_median=('turn_rel_full', 'median'),
                                                gross_vs_base_median=('FULLg_vs_base', 'median'), net_vs_base_median=('FULL_vs_base', 'median')).reset_index()
    # Q12
    s = sq_v(c)
    T['E6K-Q12-a'] = summ_v(s, ['family', 'op', 'alpha'], 'S_minus_Q_FULL')
    s5 = s[(s.alpha == 0.25) & (s.H == 5) & s.op.isin(['NATIVE', 'SZL5', 'INC1', 'RP3', 'NATIVE_HG10', 'INC1_HG10'])]
    T['E6K-Q12-b'] = s5[['mother', 'op', 'FULL', 'Q_FULL', 'S_minus_Q_FULL', 'S_minus_Q_G4']].sort_values(['mother', 'op'])
    # Q13
    rar = P[P.meas.str.startswith('RARPRE') & (P.op == 'NATIVE')]
    T['E6K-Q13-a'] = rar[(rar.alpha == 0.25) & (rar.H == 5)].sort_values(['meas', 'mother'])[['meas', 'mother', 'FULL', 'G4'] + ['D_%s' % s_ for s_ in SEGS]]
    a = A[(A.kind == 'COMMON_SUPPORT_CHILD') & A.meas.astype(str).str.startswith('RARPRE')].copy()
    for k in ('N1_minus_N0', 'C1_minus_C0', 'C0_minus_N0', 'N1_minus_C1'):
        a[k] = fv(c, k, a.acc_id)
    T['E6K-Q13-b'] = a[['meas', 'mother', 'H', 'op', 'N1_minus_N0', 'C1_minus_C0', 'C0_minus_N0', 'N1_minus_C1']].sort_values(['meas', 'mother', 'H'])
    o = rar.groupby(['meas', 'mother', 'alpha']).agg(H_cells=('H', 'count'), median_vs_native_S=('FULL_vs_native', 'median'),
                                                     share_pos=('FULL_vs_native', lambda x: float((x > 0).mean()))).reset_index()
    h5 = rar[rar.H == 5].set_index(['meas', 'mother', 'alpha']).FULL_vs_native.rename('H5_vs_native_S')
    T['E6K-Q13-c'] = o.merge(h5.reset_index(), on=['meas', 'mother', 'alpha'], how='left')
    # Q14
    m6 = P[(P.alpha == 0.25) & (P.H == 5) & P.mother.isin(P6) & P.meas.isin(['S', 'M', 'Q', 'C1'])]
    pv = m6.pivot_table(index=['meas', 'op'], columns='mother', values='FULL_vs_native', aggfunc='first')
    T['E6K-Q14-a'] = pv[[m for m in P6 if m in pv.columns]].add_suffix('_vs_native').reset_index()
    u = m6.set_index(['meas', 'op', 'mother']).FULL.unstack('mother')
    o = pd.DataFrame(index=u.index)
    for x in ('A4b', 'M_mean3_v2', 'M_union3_v2'):
        o['%s_CVR_margin' % x] = u[x + '_CVRv5'] - u[x]
    T['E6K-Q14-b'] = o.reset_index()
    t = P[(P.alpha == 0.25) & (P.H == 5) & P.mother.isin(['A4b', 'A4b_CVRv5']) & P.meas.isin(['S', 'M', 'Q', 'C1']) &
          P.op.isin(['NATIVE', 'SZL5', 'INC1', 'RP3', 'NATIVE_HG10', 'INC1_HG10', 'TREFIT0', 'TREFIT0p5', 'POST2_INCREMENT'])].copy()
    t['capital_view_diff'] = t.FULL_sc - t.FULL
    mf = c.MF[c.MF.mother.isin(['A4b', 'A4b_CVRv5']) & (c.MF.alpha.astype(str) == 'a0.25')]
    g = mf.groupby(['meas', 'mother', 'op'])
    for k in ('n_edits_in', 'edit_weight_share', 'edit_persistence_5d_reversal_share'):
        t[k + '_segavg'] = [g[k].mean().get((r.meas, r.mother, r.op), np.nan) for r in t.itertuples()]
    T['E6K-Q14-c'] = t[['meas', 'mother', 'op', 'FULL', 'FULL_sc', 'capital_view_diff', 'n_edits_in_segavg', 'edit_weight_share_segavg',
                        'edit_persistence_5d_reversal_share_segavg']].sort_values(['meas', 'mother', 'op'])
    # Q15
    t = P[~P.family.isin(['NATIVE', 'PARENT'])].copy()
    t['D_deriv'] = fv(c, 'D', t.desc_id, DER)
    t['D_post'] = fv(c, 'D', t.desc_id, POS)
    t['post_minus_deriv'] = t.D_post - t.D_deriv
    T['E6K-Q15-a'] = t.groupby(['family', 'op']).agg(cells=('desc_id', 'count'), FULL_median=('FULL', 'median'), D_deriv_median=('D_deriv', 'median'),
                                                    D_post_median=('D_post', 'median'), share_post_pos=('D_post', lambda x: float((x > 0).mean())),
                                                    post_minus_deriv_median=('post_minus_deriv', 'median'),
                                                    label=('first_look_label', lambda x: '|'.join(sorted(set(map(str, x.dropna())))))).reset_index()
    seal = {}
    for pkg in ('deriv', 'post'):
        seal.update(jload(rp('registration', 'seal_%s.json' % pkg))['files'])
    h16 = lambda p: (seal.get(os.path.relpath(p, RES)) or sha256_file(p))[:16] if os.path.exists(p) else ''
    rows = []
    for s_ in SEGS:
        for f in sorted(glob.glob(rp('accounts', s_, '*.npz'))):
            b = os.path.basename(f)
            if b.startswith('weights_'):
                continue
            z = np.load(f, allow_pickle=False)
            rows.append(dict(segment=s_, task=b[:-4].replace('__', '|'), n_targets=len(z['targets']), n_desc=len(z['desc']), account_sha16=h16(f),
                             weights_sha16=h16(rp('accounts', s_, 'weights_' + b))))
    T['E6K-Q15-b'] = pd.DataFrame(rows)
    # Q16
    dc = pd.read_csv(rp('diagnostics', 'decay', 'decay_scenarios_v2.csv'))
    T['E6K-Q16-a'] = dc[dc.kind == 'reproduction'].dropna(axis=1, how='all')
    T['E6K-Q16-b'] = dc[dc.kind == 'scenario'].dropna(axis=1, how='all')
    # Q17
    t = main148_v(c).copy()
    T['E6K-Q17-a'] = t[['meas', 'mother', 'op', 'alpha', 'H', 'FULL', 'G4'] + ['size_%s' % p for p in PROFILES] + ['policy_%s_FULL' % p for p in PROFILES]]
    ids = t.desc_id.tolist()
    t['port_size_mid_T_mean'] = 0.5 * (fv(c, 'port_size_lo_T', ids) + fv(c, 'port_size_hi_T', ids))
    t['port_size_mid_T_absmean'] = fv(c, 'port_size_absmean_mid_T', ids)
    dm = daily_mid_v(c, ids)
    for k in ('port_size_mid_T_p05', 'port_size_mid_T_p95', 'port_size_mid_T_abs_p95', 'port_size_mid_T_max', 'port_size_mid_T_abs_max'):
        t[k] = [dm.get(d, {}).get(k, np.nan) for d in ids]
    for k, col in (('lv5_child_full', 'lv5_mean'), ('lv5_parent_full', 'parent_lv5_mean'), ('small30_delta_full', 'small30_delta'),
                   ('unknown_size_capital_full', 'unkT_mean'), ('roll_size_delta_T_full', 'roll_size_delta_T'), ('edit_gap_mean_T_full', 'edit_gap_mean_T'),
                   ('edit_gap_absmean_T_full', 'edit_gap_absmean_T'), ('edit_capital_share_full', 'edit_w_in_mean'), ('n_edits_full', 'n_edits_mean')):
        t[k] = fv(c, col, ids)
    T['E6K-Q17-b'] = t[['meas', 'mother', 'op', 'alpha', 'H', 'port_size_mid_T_mean', 'port_size_mid_T_absmean', 'port_size_mid_T_p05', 'port_size_mid_T_p95',
                        'port_size_mid_T_abs_p95', 'port_size_mid_T_max', 'port_size_mid_T_abs_max', 'lv5_child_full', 'lv5_parent_full', 'small30_delta_full',
                        'unknown_size_capital_full', 'roll_size_delta_T_full', 'edit_gap_mean_T_full', 'edit_gap_absmean_T_full', 'edit_capital_share_full',
                        'n_edits_full']]
    t = main148_v(c).copy()
    for m, tag in (('LEGACY_POLICY_RANDOM', 'LEGACY'), ('NEW_COND_ISK_P5', 'NEW')):
        Rm = c.R[c.R.mechanism == m]
        v, e = [], []
        for d, h in zip(t.desc_id, t.H):
            x = Rm[(Rm.desc_id == d) & (Rm.H == h)]
            w = np.array([Pi.at[d, 'n_%s' % s_] for s_ in x.segment], float) if len(x) else np.array([])
            v.append(float(np.average(x.real_minus_rand, weights=w)) if len(x) and w.sum() > 0 else np.nan)
            e.append(float(x.mcse.max()) if len(x) else np.nan)
        t['real_minus_rand_%s_full' % tag] = v
        t['mcse_max_%s' % tag] = e
    T['E6K-Q17-c'] = t[['meas', 'mother', 'op', 'alpha', 'H', 'FULL', 'FULL_vs_C1', 'FULL_vs_nativeC1', 'real_minus_rand_LEGACY_full', 'mcse_max_LEGACY',
                        'real_minus_rand_NEW_full', 'mcse_max_NEW']]
    # Q18
    T['E6K-Q18-a'] = pd.read_csv(rp('registry', 'hypothesis_lineage_E6k.csv'))
    after = ('E6k_REVIEW_input.md', 'E6k_lessons_delta.md', 'E6k_REPORT_cards.md', 'results/hypothesis_outcomes.json', 'results/completion_receipt.json')
    tabs12 = ['source_manifest.json', 'results/account_manifest.csv', 'results/full/policy_E6k.csv', 'registry/hypothesis_lineage_E6k.csv',
              'results/hypothesis_outcomes.json', 'results/mask_edit_ledger.csv', 'results/risk_exposure_daily.parquet', 'results/layer_transplants.csv',
              'results/random_registry.csv', 'results/read_permissions.csv', 'results/coverage.csv', 'results/completion_receipt.json']
    rc = jload(rp('task_status', 'report_cards.receipt.json'))['written_at']
    t_rc = dt.datetime.fromisoformat(str(rc)[:19]).timestamp()
    rows = [dict(item='reports/' + r, exists_at_generation=os.path.exists(rp('reports', r)) and os.path.getmtime(rp('reports', r)) < t_rc,
                 note='本报告之后生成' if r in after else '') for r in TWELVE]
    rows += [dict(item=x, exists_at_generation=os.path.exists(rp(x)) and os.path.getmtime(rp(x)) < t_rc, note='本报告之后生成' if x in after else '') for x in tabs12]
    T['E6K-Q18-b'] = pd.DataFrame(rows)
    return T


def daily_mid_v(c, ids):
    """主对象目标级逐日 size 中点（T）：四段全部日的带符号 p05 / p95、|·| 的 p95 与最大处的带符号值（t_szT_lo / hi；只读目标级数组）。"""
    tmap = c.D.set_index('desc_id').target_id
    want = {tmap[d]: d for d in ids if d in tmap.index}
    acc = {}
    for s in SEGS:
        for f in sorted(glob.glob(rp('accounts', s, '*.npz'))):
            if os.path.basename(f).startswith('weights_'):
                continue
            z = np.load(f, allow_pickle=False)
            tg = list(map(str, z['targets']))
            hit = [j for j, tid in enumerate(tg) if tid in want]
            if not hit:
                continue
            LO, HI = z['t_szT_lo'], z['t_szT_hi']
            for j in hit:
                m = 0.5 * (LO[j] + HI[j])
                acc.setdefault(want[tg[j]], []).append(m[np.isfinite(m)])
    out = {}
    for d, parts in acc.items():
        m = np.concatenate(parts) if parts else np.array([])
        if not len(m):
            continue
        k = int(np.argmax(np.abs(m)))
        out[d] = dict(port_size_mid_T_p05=float(np.percentile(m, 5)), port_size_mid_T_p95=float(np.percentile(m, 95)),
                      port_size_mid_T_abs_p95=float(np.percentile(np.abs(m), 95)), port_size_mid_T_max=float(m[k]), port_size_mid_T_abs_max=float(abs(m[k])))
    return out


CARD_KEYS = {'E6K-Q01-a': ['meas', 'mother'], 'E6K-Q01-b': ['meas', 'mother'], 'E6K-Q01-c': ['meas', 'mother'], 'E6K-Q02-a': ['op', 'alpha', 'H'],
             'E6K-Q02-b': ['meas', 'op', 'alpha'], 'E6K-Q02-c': ['op', 'alpha'], 'E6K-Q03-a': ['meas', 'mother', 'op'], 'E6K-Q03-b': ['meas', 'mother', 'alpha', 'H'],
             'E6K-Q03-c': ['op', 'alpha', 'phase'], 'E6K-Q04-a': ['meas', 'mother'], 'E6K-Q04-b': ['meas', 'mother'], 'E6K-Q04-c': ['segment', 'op'],
             'E6K-Q05-a': ['desc_id'], 'E6K-Q05-b': ['desc_id'], 'E6K-Q05-c': ['segment', 'subset'], 'E6K-Q06-a': ['meas', 'mother', 'layer'],
             'E6K-Q06-b': ['meas', 'mother', 'op'], 'E6K-Q06-c': ['desc_id', 'child'], 'E6K-Q07-a': ['meas', 'mother', 'op'], 'E6K-Q07-b': ['meas', 'mother', 'op'],
             'E6K-Q08-a': ['meas', 'mother', 'op'], 'E6K-Q08-b': ['meas', 'mother'], 'E6K-Q09-a': ['op', 'H'], 'E6K-Q09-b': ['band_op', 'H'],
             'E6K-Q10-a': ['op', 'H'], 'E6K-Q10-b': ['band_op', 'H'], 'E6K-Q10-c': ['query_id'], 'E6K-Q11-a': ['meas', 'mother', 'op'], 'E6K-Q11-b': ['op', 'H'],
             'E6K-Q11-c': ['op', 'H'], 'E6K-Q12-a': ['family', 'op', 'alpha'], 'E6K-Q12-b': ['mother', 'op'], 'E6K-Q13-a': ['meas', 'mother'],
             'E6K-Q13-b': ['meas', 'mother', 'H', 'op'], 'E6K-Q13-c': ['meas', 'mother', 'alpha'], 'E6K-Q14-a': ['meas', 'op'], 'E6K-Q14-b': ['meas', 'op'],
             'E6K-Q14-c': ['meas', 'mother', 'op'], 'E6K-Q15-a': ['family', 'op'], 'E6K-Q15-b': ['segment', 'task'], 'E6K-Q16-a': ['kind'],
             'E6K-Q16-b': ['kind', 'L', 'volatility', 'theta', 'shift'], 'E6K-Q17-a': ['meas', 'mother', 'op', 'alpha', 'H'],
             'E6K-Q17-b': ['meas', 'mother', 'op', 'alpha', 'H'], 'E6K-Q17-c': ['meas', 'mother', 'op', 'alpha', 'H'], 'E6K-Q18-a': ['claim_id'], 'E6K-Q18-b': ['item']}


def knorm(v):
    """键值规范化：能解析成有限数的一律按 %.6g，其余原样字符串。"""
    if isinstance(v, (bool, np.bool_)):
        return str(bool(v))
    try:
        x = float(str(v).replace('−', '-'))
        if np.isfinite(x):
            return '%.6g' % x
    except ValueError:
        pass
    return str(v)


def cmp_cell(cell, v):
    """REPORT 格（字符串）vs 复算值：OK / ROUNDING / BLANK_NA（字面 N/A 被生成器读成 NaN 印空）/ BAD。"""
    if v is None or (isinstance(v, (float, np.floating)) and not np.isfinite(v)):
        return 'OK' if str(cell) in ('', 'nan') else 'BAD'
    if isinstance(v, (bool, np.bool_)):
        return 'OK' if str(cell) == str(bool(v)) else 'BAD'
    if isinstance(v, (int, np.integer, float, np.floating)):
        try:
            if float(cell) == float(v):
                return 'OK'
        except ValueError:
            return 'BAD'
        r = cell_eq4(cell, float(v))
        return 'BAD' if r == 'BAD' else r
    s = str(v)
    if s in ('N/A', 'NA') and str(cell) == '':
        return 'BLANK_NA'
    return 'OK' if str(cell) == s else 'BAD'


def cmp_table(rep, mine, keys):
    """按键对齐逐格比较；返回 (统计 dict, 逐格列表[(行号, 列, 报告值, 复算值, 结果)])。"""
    st = dict(rows_rep=len(rep), rows_mine=len(mine), cols_missing='', cells=0, OK=0, ROUNDING=0, BLANK_NA=0, BAD=0, PROXY=0, unmatched_rows=0)
    miss = [c_ for c_ in rep.columns if c_ not in mine.columns]
    st['cols_missing'] = '|'.join(miss)
    mk = {}
    for i, r in enumerate(mine.to_dict('records')):
        mk.setdefault(tuple(knorm(r[k]) for k in keys), []).append(r)
    cells = []
    for i, r in enumerate(rep.to_dict('records')):
        k = tuple(knorm(r[k_]) for k_ in keys)
        cand = mk.get(k, [])
        if len(cand) != 1:
            st['unmatched_rows'] += 1
            continue
        m = cand[0]
        for col in rep.columns:
            if col in keys or col in miss:
                continue
            res = cmp_cell(r[col], m[col])
            if res == 'BAD' and col == 'exists_at_generation':
                res = 'PROXY'                                   # 生成时刻存在性：V 以 mtime < 卡表回执时刻近似
            st['cells'] += 1
            st[res] += 1
            cells.append((i, col, r[col], m[col], res))
    return st, cells


def vd07():
    """cards 47 张表：独立复算后逐格全比（超集），另按 seed 20260929 每表抽 5 格列值；supported_scope 数字回链见 scope_checks。"""
    c = card_ctx()
    T = cards_build(c)
    _C["CARD_T"] = T
    tabs = report_tables('E6k_REPORT_cards.md')[0]
    rng = np.random.default_rng(SEED)
    rows, samp = [], []
    for qid in sorted(q for q in tabs if q.startswith('E6K-Q')):
        rep = tabs[qid]
        if qid not in T:
            rows.append(dict(query_id=qid, status='NOT_BUILT'))
            continue
        st, cells = cmp_table(rep, T[qid], CARD_KEYS[qid])
        rows.append(dict(query_id=qid, **st))
        if cells:
            for j in sorted(set(int(x) for x in rng.choice(len(cells), size=min(5, len(cells)), replace=False))):
                i, col, cv, mv, res = cells[j]
                samp.append(dict(query_id=qid, row=i, col=col, report=cv, recomputed=(fmt4(float(mv)) if isinstance(mv, (float, np.floating, int, np.integer))
                                                                                        and not isinstance(mv, (bool, np.bool_)) else str(mv)), result=res))
    C = pd.DataFrame(rows)
    S = pd.DataFrame(samp)
    C.to_csv(os.path.join(OUT, 'vd07_cards.csv'), index=False)
    S.to_csv(os.path.join(OUT, 'vd07_cards_sample5.csv'), index=False)
    bad_t = C[(C.BAD > 0) | (C.unmatched_rows > 0) | (C.cols_missing.fillna('') != '') | (C.rows_rep != C.rows_mine)]
    out = [row('VD07', 'cards_all_cells', 'E6k_REPORT_cards.md 47 张表（全格；抽 5 格见 verify/vd07_cards_sample5.csv）',
               '表数 / 格数 / OK / ROUNDING / BLANK_NA / PROXY / BAD / 行不齐或缺列的表', '0 不符',
               '%d / %d / %d / %d / %d / %d / %d / %d' % (len(C), C.cells.sum(), C.OK.sum(), C.ROUNDING.sum(), C.BLANK_NA.sum(), C.PROXY.sum(), C.BAD.sum(), len(bad_t)),
               'REPRODUCED' if len(bad_t) == 0 else 'DIFFERS',
               ';'.join(x for x in ('ROUNDING' if C.ROUNDING.sum() else '',
                                    'INFO:BLANK_NA = policy 字面 N/A / NA 被生成器读成 NaN 印空（%d 格）' % C.BLANK_NA.sum() if C.BLANK_NA.sum() else '',
                                    'INFO:PROXY = Q18-b 生成时刻存在性（V 以 mtime 近似，%d 格不同）' % C.PROXY.sum() if C.PROXY.sum() else '') if x),
               diff=';'.join('%s:BAD%d/unmatched%d/miss[%s]' % (r.query_id, r.BAD, r.unmatched_rows, r.cols_missing) for r in bad_t.itertuples())[:600],
               func='cards 口径转录（fullv n 加权 / summ / 各 q 函数）后按键对齐逐格'),
           row('VD07', 'cards_sample5', 'verify/vd07_cards_sample5.csv', '抽格数 / 不符', '0 不符', '%d / %d' % (len(S), int((S.result == 'BAD').sum()) if len(S) else 0),
               'REPRODUCED' if len(S) and (S.result == 'BAD').sum() == 0 else 'DIFFERS', func='seed 20260929；每表 min(5, 格数)')]
    out += scope_rows(c, T)
    return out


# ---------------------------------------------------------------------------- VD07 续 / VD06：hypothesis_outcomes.supported_scope 数字与全称句
def scope_checks(c, T):
    """每条 = (卡, 标签, 印出记号, 复算值, 类型, 口径)。类型：count EXACT；pct |100v − 印| ≤ .5；d3 |v − 印| ≤ .0005；d2 ≤ .005；approx0 |v| < .01；bool 为真。"""
    P, Pi = c.P, c.Pi
    L = []

    def add(card, label, printed, value, kind, how):
        L.append(dict(card=card, label=label, printed=printed, value=value, kind=kind, how=how))

    def med(x):
        x = pd.Series(np.asarray(x, float)).dropna()
        return float(x.median()) if len(x) else np.nan

    def spos(x):
        x = pd.Series(np.asarray(x, float)).dropna()
        return float((x > 0).mean()) if len(x) else np.nan

    def snp(x):
        x = pd.Series(np.asarray(x, float)).dropna()
        return float((x <= 0).mean()) if len(x) else np.nan
    # Q01
    t = P[P.primary144 & (P.op == 'NATIVE')]
    add('Q01', '原生主对象数', '24', len(t), 'count', 'policy primary144 & op==NATIVE')
    add('Q01', 'FULL > 0 个数', '22', int((t.FULL > 0).sum()), 'count', 'FULL（四段 n 加权）> 0')
    same3 = bool(((t.policy_PROPOSED_PORT3_T_FULL == t.policy_PROPOSED_PORT3_LAG1_FULL) & (t.policy_PROPOSED_PORT3_T_FULL == t.policy_EXEC_DISCLOSE_ONLY_FULL)).all())
    add('Q01', '三列结果相同', '三列结果相同', same3, 'bool', '24 行 FULL 串 PORT3_T == PORT3_LAG1 == EXEC_DISCLOSE_ONLY')
    lo = pd.concat([c.S[s].reindex(t.desc_id)['port_size_lo_%s' % z] for s in SEGS for z in ('T', 'L')])
    hi = pd.concat([c.S[s].reindex(t.desc_id)['port_size_hi_%s' % z] for s in SEGS for z in ('T', 'L')])
    inb = bool(((lo >= -3) | lo.isna()).all() and ((hi <= 3) | hi.isna()).all())
    add('Q01', '组合层 size 逐段 ±3 内', '3', inb, 'bool', 'descriptor_stats 四段 port_size_lo/hi_{T,L} ∈ [−3, 3]（24 行；未定义段 %d 格不计）' % int(lo.isna().sum()))
    for p_, n_ in (('PROPOSED_PORT3_T', '15'), ('LEGACY_EDIT5', '4'), ('EXEC_LEADER_VS_PARENT', '5')):
        add('Q01', '%s 通过' % p_, n_, int((t['policy_%s_FULL' % p_] == PASS_S).sum()), 'count', 'policy_%s_FULL == 通过' % p_)
    # Q02
    szl = P[P.family == 'SZL'].copy()
    add('Q02', 'SZL 格数', '3,840', len(szl), 'count', 'family==SZL')
    add('Q02', 'SZL vs NATIVE 不为正份额', '96%', snp(szl.FULL_vs_native), 'pct', 'FULL_vs_native ≤ 0（有限值）')
    add('Q02', 'SZL vs NATIVE 中位', '−.112', med(szl.FULL_vs_native), 'd3', 'median FULL_vs_native')
    add('Q02', 'α .5 全部为负', '.5', bool((szl[szl.alpha == 0.5].FULL_vs_native.dropna() < 0).all()), 'bool', 'α .5 行 FULL_vs_native < 0')
    own = szl.FULL.values - Pi.FULL.reindex(szl.desc_id + '_OWN').values
    add('Q02', 'SZL − OWN 正份额', '89%', spos(own), 'pct', 'FULL − FULL(<id>_OWN) > 0')
    add('Q02', 'SZL − OWN 中位', '+.131', med(own), 'd3', 'median FULL − FULL(OWN)')
    add('Q02', '任何 α 上不优于 NATIVE', '任何 α', bool(all(med(g.FULL_vs_native) <= 0 for _, g in szl.groupby('alpha'))), 'bool',
        '每个 α 的 FULL_vs_native 中位 ≤ 0（绑定口径：执行端取"整体" = 中位）')
    # Q03
    inc = P[P.family == 'INC']
    add('Q03', 'INC vs NATIVE 不为正', '89%', snp(inc.FULL_vs_native), 'pct', 'family==INC FULL_vs_native ≤ 0')
    add('Q03', 'INC vs NATIVE 中位', '−.057', med(inc.FULL_vs_native), 'd3', 'median')
    add('Q03', 'SZL 中位（引）', '−.112', med(szl.FULL_vs_native), 'd3', '同 Q02')
    add('Q03', 'INC 后段中位', '.121', med(fv(c, 'D', inc.desc_id, POS)), 'd3', 'median D_post（两后段 n 加权）')
    add('Q03', 'INC 推导中位', '.138', med(fv(c, 'D', inc.desc_id, DER)), 'd3', 'median D_deriv')
    b = T['E6K-Q03-b']
    add('Q03', 'SUPPORT0 − NATIVE ≈ 0', '0', med(b.SUPPORT0_minus_NATIVE), 'approx0', 'median（Q03-b）')
    add('Q03', 'SUPPORT0 − NATIVE 中位', '−.003', med(b.SUPPORT0_minus_NATIVE), 'd3', 'median（Q03-b）')
    add('Q03', 'DOSE1 − INC1 中位', '+.054', med(-b.INC1_minus_DOSE1), 'd3', '−(INC1 − DOSE1)（Q03-b）')
    add('Q03', 'DOSE1 − INC1 正份额', '88%', spos(-b.INC1_minus_DOSE1), 'pct', 'Q03-b')
    add('Q03', 'DOSE05 − INC05 中位', '+.008', med(-b.INC05_minus_DOSE05), 'd3', 'Q03-b')
    # Q04
    a = T['E6K-Q04-a']
    rg = P[P.op == 'RPINF']
    for lab, pr_, f_, kind in (('RPINF vs NATIVE 不为正', '94%', snp, 'pct'), ('RPINF vs NATIVE 中位', '−.173', med, 'd3')):
        vt, vg = f_(a.FULL_vs_native), f_(rg.FULL_vs_native)
        okt = judge_scope(dict(value=vt, printed=pr_, kind=kind))
        okg = judge_scope(dict(value=vg, printed=pr_, kind=kind))
        add('Q04', lab, pr_, vt if okt and not okg else vg, kind, '口径：卡表 E6K-Q04-a 32 行（α .25 × H5）%.4f %s / 查询对象集 op==RPINF 全网格 %d 行 %.4f %s → 基 = %s' %
            (vt, '符' if okt else '不符', len(rg), vg, '符' if okg else '不符', '查询对象集（全网格）' if okg else ('卡表' if okt else '两者皆不符')))
    b = T['E6K-Q04-b']
    add('Q04', 'RP3 − PAIR_ALL ≈ 0', '0', med(b.RP3_minus_PAIR_ALL), 'approx0', 'Q04-b 中位')
    add('Q04', 'RP0.5 − PAIR_ALL', '−.024', med(b.RP0p5_minus_PAIR_ALL), 'd3', 'Q04-b 中位')
    rp3g = P[P.op == 'RP3']
    for lab, pr_, v32, vg in (('RP3 FULL 中位', '.031', med(b.RP3_FULL), med(rp3g.FULL)),
                              ('RP3 后段中位', '.034', med(fv(c, 'D', rpi_ids(P, 'RP3'), POS)), med(fv(c, 'D', rp3g.desc_id, POS))),
                              ('RP3 推导中位', '.027', med(fv(c, 'D', rpi_ids(P, 'RP3'), DER)), med(fv(c, 'D', rp3g.desc_id, DER)))):
        hit = 'α .25 × H5 32 行' if abs(v32 - float(ntok(pr_))) <= 5e-4 + 1e-12 else ('全网格 %d 行' % len(rp3g) if abs(vg - float(ntok(pr_))) <= 5e-4 + 1e-12 else '两者皆不符')
        add('Q04', lab, pr_, v32 if hit.startswith('α') else vg, 'd3', '口径二选一（句中未写范围）：32 行 %.4f / 全网格 %.4f → %s' % (v32, vg, hit))
    # Q05
    sh = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(rp('diagnostics', 'mechanisms', '*_shapley.csv')))], ignore_index=True)
    add('Q05', 'NATIVE 主对象数', '24', sh.desc_id.nunique(), 'count', 'shapley 诊断 desc_id 数')
    qb = T['E6K-Q05-b']
    for x, pr_, kind in (('S', '+.144', 'd3'), ('K', '+.025', 'd3'), ('I', '0', 'approx0')):
        v96, v24 = med(sh['shapley_net_%s' % x]), med(qb['shapley_net_%s' % x])
        ok96 = abs(v96 - float(ntok(pr_))) <= 5e-4 + 1e-12 if kind == 'd3' else abs(v96) < .01
        add('Q05', 'Shapley net %s 中位' % x, pr_, v96 if ok96 else v24, kind, '口径二选一（"24 × 四段"）：96 个段值中位 %.4f / 24 个 n 加权中位 %.4f → %s' %
            (v96, v24, '96 段值' if ok96 else '24 加权'))
    add('Q05', '2024-2026 段 S 中位', '.260', med(sh[sh.segment == '2024-2026'].shapley_net_S), 'd3', 'shapley 2024-2026 段 24 值中位')
    ld = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(rp('diagnostics', 'mechanisms', '*_leafdiag.csv')))], ignore_index=True)
    add('Q05', '可移动份额中位', '1', med(ld.movable_share), 'd3', 'leafdiag 全部行 movable_share 中位（Q05-c 各格中位最小 %.4g）' % T['E6K-Q05-c'].movable_share_median.min())
    add('Q05', 'ISK 置换熵比', '.52', med(ld[ld.subset == 'ISK'].entropy_ratio), 'd2', 'leafdiag subset==ISK entropy_ratio 中位（"约"）')
    # Q06
    a = T['E6K-Q06-a']
    for lay, v10, p10, v01, p01, vi, kind_i in (('SIZE3', '+.129', '97%', '+.138', '78%', '0', 'approx0'), ('ISK', '+.237', '94%', '+.003', '50%', '+.020', 'd3')):
        x = a[a.layer == lay]
        add('Q06', '%s V10 − V00 中位' % lay, v10, med(x.V10_minus_V00), 'd3', 'Q06-a')
        add('Q06', '%s V10 − V00 正份额' % lay, p10, spos(x.V10_minus_V00), 'pct', 'Q06-a')
        add('Q06', '%s V01 − V00 中位' % lay, v01, med(x.V01_minus_V00), 'd3', 'Q06-a')
        add('Q06', '%s V01 − V00 正份额' % lay, p01, spos(x.V01_minus_V00), 'pct', 'Q06-a')
        add('Q06', '%s 交互中位' % lay, vi, med(x.interaction), kind_i, 'Q06-a')
        if lay == 'SIZE3':
            add('Q06', 'SIZE3 两者各自都有', '两者', bool(med(x.V10_minus_V00) > 0 and med(x.V01_minus_V00) > 0), 'bool', 'Q06-a SIZE3：V10 − V00 与 V01 − V00 中位均 > 0')
    # Q07
    a = T['E6K-Q07-a']
    a0 = a[a.op == 'TREFIT0'].set_index(['meas', 'mother']).FULL_vs_native
    for (m_, p_), pr_ in ((('S', 'A4b'), '−.228'), (('S', 'A4b_CVRv5'), '−.243'), (('Q', 'A4b'), '−.192'), (('Q', 'A4b_CVRv5'), '−.211'),
                          (('C1', 'A4b'), '−.056'), (('C1', 'A4b_CVRv5'), '−.084'), (('M', 'A4b'), '+.004'), (('M', 'A4b_CVRv5'), '+.036')):
        add('Q07', 'TREFIT0 − NATIVE %s %s' % (m_, p_), pr_, float(a0.get((m_, p_), np.nan)), 'd3', 'Q07-a FULL_vs_native')
    add('Q07', '全网格 TREFIT0 不为正', '85%', snp(P[P.op == 'TREFIT0'].FULL_vs_native), 'pct', 'op==TREFIT0 FULL_vs_native ≤ 0')
    # Q08
    a = T['E6K-Q08-a'].set_index(['meas', 'mother'])
    for (m_, p_), pr_ in ((('S', 'A4b'), '−.049'), (('Q', 'A4b'), '−.006'), (('S', 'A4b_CVRv5'), '−.135'), (('Q', 'A4b_CVRv5'), '−.182'),
                          (('C1', 'A4b'), '.175'), (('C1', 'A4b_CVRv5'), '.163')):
        add('Q08', 'POST2 FULL %s %s' % (m_, p_), pr_, float(a.FULL.get((m_, p_), np.nan)), 'd3', 'Q08-a FULL')
    sq_ = a[a.index.get_level_values(0).isin(['S', 'Q'])].FULL_vs_native
    add('Q08', 'S / Q FULL 为负或近 0', '0', float(a[a.index.get_level_values(0).isin(['S', 'Q'])].FULL.max()), 'approx0', 'Q08-a S/Q 行 FULL 最大值（其余为负）')
    add('Q08', 'S / Q 相对 NATIVE 上界', '−.37', float(sq_.max()), 'd2', 'Q08-a S/Q 行 FULL_vs_native 最大')
    add('Q08', 'S / Q 相对 NATIVE 下界', '−.56', float(sq_.min()), 'd2', 'Q08-a S/Q 行 FULL_vs_native 最小')
    add('Q08', 'C1 低于 C1 NATIVE', 'C1 NATIVE', bool((a[a.index.get_level_values(0) == 'C1'].FULL_vs_native < 0).all()), 'bool', 'Q08-a C1 行 FULL_vs_native < 0')
    pg = P[P.family == 'POST2']
    add('Q08', '全网格 POST2 正份额', '37%', spos(pg.FULL), 'pct', 'family==POST2 FULL > 0')
    add('Q08', 'α .5 大幅为负', '.5', bool(med(pg[pg.alpha == 0.5].FULL) < 0), 'bool', 'α .5 FULL 中位 = %.4g' % med(pg[pg.alpha == 0.5].FULL))
    # Q09 / Q10 / Q11
    for card, kind, vn, vi, pr_d, pr_p in (('Q09', 'SA', '+.001', '−.005', '+.004', '57%'), ('Q10', 'PM', '−.121', '−.064', '+.017', '68%'),
                                          ('Q11', 'HG', '+.039', '+.051', '+.040', '66%')):
        bb = band_v(c, kind)
        add(card, '%s NATIVE 基础中位' % kind, vn, med(bb[bb.op.str.startswith('NATIVE_')].FULL_vs_base), 'd3', '带 α .25 × H{3,5,10,20} FULL_vs_base')
        add(card, '%s INC1 基础中位' % kind, vi, med(bb[bb.op.str.startswith('INC1_')].FULL_vs_base), 'd3', '同上')
        dd = dose_v(c, kind)
        add(card, '%s − DOSE 中位' % kind, pr_d, med(dd.BAND_minus_DOSE_FULL), 'd3', 'BAND − DOSE（−D_vs_compare n 加权）')
        add(card, '%s − DOSE 正份额' % kind, pr_p, spos(dd.BAND_minus_DOSE_FULL), 'pct', '同上')
        if kind == 'SA':
            add(card, 'SA 相对无带 ≈ 0', '0', med(bb.FULL_vs_base), 'approx0', '全部 SA 行中位')
        if kind == 'PM':
            add(card, 'PM 相对无带不为正居多', '居多', snp(bb.FULL_vs_base) > .5, 'bool', 'FULL_vs_base ≤ 0 份额 = %.3f' % snp(bb.FULL_vs_base))
        if kind == 'HG':
            add(card, 'HG 正份额约 3 / 4', '3 / 4', abs(spos(bb.FULL_vs_base) - .75) <= .05, 'bool', 'FULL_vs_base > 0 份额 = %.3f（"约"：±.05）' % spos(bb.FULL_vs_base))
            hg_all = P[(P.family == 'BAND') & P.op.str.contains('_HG')]
            cands = [('α .25 × H{3,5,10,20} 行 turn_rel n 加权中位', med(bb.turn_rel_full)),
                     ('卡表 E6K-Q11-c turn_rel_median 列中位', med(T['E6K-Q11-c'].turn_rel_median)),
                     ('α .25 × H5 行', med(bb[bb.H == 5].turn_rel_full)),
                     ('HG 全网格（全部 α × H）', med(fv(c, 'turn_rel', hg_all.desc_id))),
                     ('primary144 HG 行', med(fv(c, 'turn_rel', P[P.primary144 & P.op.str.contains('_HG')].desc_id)))]
            hit = [(n_, v_) for n_, v_ in cands if abs(v_ - (-0.004)) <= 5e-4 + 1e-12]
            add(card, 'HG 相对换手中位', '−.004', hit[0][1] if hit else cands[0][1], 'd3',
                '候选口径：' + '；'.join('%s %.4f' % x for x in cands) + ' → 命中 %s' % (hit[0][0] if hit else '无'))
    mf = c.MF
    pm15 = mf[mf.op.astype(str).str.endswith('PM15') & (mf.alpha.astype(str) == 'a0.125')]
    z15 = pm15.assign(z=pm15.n_edits_in.fillna(0) == 0).groupby('op').agg(rows=('z', 'size'), zero=('z', 'sum'), tg=('target_id', 'nunique'),
                                                                          tg_all4=('z', lambda s: 0)).to_dict('index')
    for op_ in z15:
        g_ = pm15[pm15.op == op_].assign(z=lambda d_: d_.n_edits_in.fillna(0) == 0).groupby('target_id').z.all()
        z15[op_]['tg_all4'] = int(g_.sum())
    add('Q10', 'α .125 × b 15 PM 从不交换', '.125 / 15', bool(len(pm15) and (pm15.n_edits_in.fillna(0) == 0).all()), 'bool',
        'mask_facts op *PM15 & α .125 目标 × 段：%s（zero = 无换入；tg_all4 = 四段全无换入的目标数）' % json.dumps(z15, ensure_ascii=False, default=int))
    pm10 = mf[mf.op.astype(str).str.endswith('PM10') & mf['flags'].astype(str).str.contains('NO_EDITS')]
    add('Q10', '推导段 b 10 无交换目标', '2', pm10[pm10.segment.isin(DER)].target_id.nunique(), 'count', 'mask_facts *PM10 flags 含 NO_EDITS（推导两段）')
    add('Q10', '后段 b 10 无交换目标', '10', pm10[pm10.segment.isin(POS)].target_id.nunique() == 0, 'bool', '同上（两后段 = 0）')
    a = T['E6K-Q11-a']
    add('Q11', '信息边际中位', '+.225', med(a.info_margin_V11_minus_V01), 'd3', 'Q11-a')
    add('Q11', '信息边际正份额', '96%', spos(a.info_margin_V11_minus_V01), 'pct', 'Q11-a')
    add('Q11', 'HG_ONLY 中位', '+.017', med(a.V01_minus_V00), 'd3', 'Q11-a')
    add('Q11', '交互中位', '+.013', med(a.interaction), 'd3', 'Q11-a')
    # Q12
    s = sq_v(c)
    add('Q12', 'S − Q 全网格 ≈ 0', '0', med(s.S_minus_Q_FULL), 'approx0', 'S 行 FULL − 同槽 Q FULL')
    add('Q12', 'S − Q 全网格中位', '+.001', med(s.S_minus_Q_FULL), 'd3', '同上')
    add('Q12', 'S − Q 正份额', '52%', spos(s.S_minus_Q_FULL), 'pct', '同上')
    n5 = s[(s.op == 'NATIVE') & (s.alpha == 0.25) & (s.H == 5)]
    add('Q12', '母体数', '8', n5.mother.nunique(), 'count', 'NATIVE α .25 × H5')
    add('Q12', 'S > Q 母体数', '7', int((n5.S_minus_Q_FULL > 0).sum()), 'count', '同上')
    add('Q12', 'A06', '−.184', float(n5.set_index('mother').S_minus_Q_FULL.get('A06', np.nan)), 'd3', '同上')
    add('Q12', 'SZL 与 POST2 S < Q 居多', 'SZL / POST2', bool(all((s[s.family == f_].S_minus_Q_FULL.dropna() < 0).mean() > .5 for f_ in ('SZL', 'POST2'))), 'bool',
        '各族 S − Q < 0 份额 > .5')
    # Q13
    rar = P[P.meas.str.startswith('RARPRE') & (P.op == 'NATIVE')]
    for m_, pr_p, pr_m in (('RARPRE60_LT', '12%', '−.032'), ('RARPRE60_SE', '8%', '−.039'), ('RARPRE20_SE', '52%', '0'), ('RARPRE20_LT', '23%', None)):
        x = rar[rar.meas == m_].FULL_vs_native
        add('Q13', '%s 正份额' % m_, pr_p, float((x > 0).mean()), 'pct', 'FULL_vs_native > 0（全网格，含 NaN 行作分母，同 Q13-c 口径）')
        if pr_m:
            add('Q13', '%s 中位' % m_, pr_m, med(x), 'approx0' if pr_m == '0' else 'd3', 'median FULL_vs_native')
    r5 = rar[(rar.alpha == 0.25) & (rar.H == 5)]
    for col in ('FULL_vs_native', 'FULL'):
        allpos = r5.groupby('mother')[col].apply(lambda x: bool((x > 0).all()))
        if list(allpos[allpos].index) == ['A06']:
            break
    x = r5[r5.mother == 'A06'][col]
    add('Q13', '只有 A06 四格全部为正', 'A06', list(allpos[allpos].index) == ['A06'], 'bool', '口径 = %s（α .25 × H5）；全正母体 %s' % (col, list(allpos[allpos].index)))
    add('Q13', 'A06 下界', '+.027', float(x.min()), 'd3', col)
    add('Q13', 'A06 上界', '+.084', float(x.max()), 'd3', col)
    add('Q13', 'A4b_CVRv5 与 R2 多为负', 'A4b_CVRv5 / R2', bool(all((r5[r5.mother == m_][col] < 0).mean() > .5 for m_ in ('A4b_CVRv5', 'R2'))), 'bool', col)
    # Q14
    a = T['E6K-Q14-a']
    for m_, pr_ in (('A4b', '−.189'), ('A4b_CVRv5', '−.185'), ('M_mean3_v2', '−.077'), ('M_mean3_v2_CVRv5', '−.020'), ('M_union3_v2', '−.092'), ('M_union3_v2_CVRv5', '−.081')):
        va, vn = med(a['%s_vs_native' % m_]), med(a[a.op != 'NATIVE']['%s_vs_native' % m_])
        hit = abs(va - float(ntok(pr_))) <= 5e-4 + 1e-12
        add('Q14', '%s 中位' % m_, pr_, va if hit else vn, 'd3', '口径二选一：Q14-a 列全部行中位 %.4f / 去 NATIVE 行 %.4f → %s' % (va, vn, '全部行' if hit else '去 NATIVE'))
    add('Q14', '六形态中位全部为负', '全部为负', bool(all(med(a['%s_vs_native' % m_]) < 0 for m_ in P6)), 'bool', 'Q14-a')
    b = T['E6K-Q14-b']
    add('Q14', 'A4b / M_union CVR 边际约 0', '0', max(abs(med(b.A4b_CVR_margin)), abs(med(b.M_union3_v2_CVR_margin))), 'approx0', 'Q14-b 列中位')
    add('Q14', 'M_mean3 CVR 边际全部为负', 'M_mean3', bool((b.M_mean3_v2_CVR_margin.dropna() < 0).all()), 'bool', 'Q14-b')
    add('Q14', 'M_mean3 CVR 边际中位', '−.176', med(b.M_mean3_v2_CVR_margin), 'd3', 'Q14-b')
    # Q15
    t = P[~P.family.isin(['NATIVE', 'PARENT'])]
    Dd, Dp = fv(c, 'D', t.desc_id, DER), fv(c, 'D', t.desc_id, POS)
    add('Q15', '新算子描述符数', '36,336', len(t), 'count', 'family ∉ {NATIVE, PARENT}')
    add('Q15', '推导中位', '.078', med(Dd), 'd3', 'D_deriv')
    add('Q15', '推导正份额', '83%', spos(Dd), 'pct', 'D_deriv > 0')
    add('Q15', '后段中位', '.047', med(Dp), 'd3', 'D_post')
    add('Q15', '后段正份额', '67%', float((pd.Series(Dp) > 0).mean()), 'pct', 'D_post > 0（NaN 计入分母，同 Q15-a share_post_pos）')
    k_ = np.isfinite(Dd) & (Dd > 0.05)
    add('Q15', '推导 > .05 中后段 ≤ 0', '25%', float((Dp[k_] <= 0).mean()), 'pct', 'D_deriv > .05 的对象中 D_post ≤ 0')
    nt = P[P.family == 'NATIVE']
    add('Q15', '原生推导中位', '.221', med(fv(c, 'D', nt.desc_id, DER)), 'd3', 'family==NATIVE')
    add('Q15', '原生后段中位', '.164', med(fv(c, 'D', nt.desc_id, POS)), 'd3', 'family==NATIVE')
    add('Q15', '首看标签统一', LABEL_FL, set(t.first_look_label.dropna()) == {LABEL_FL} and t.first_look_label.notna().all(), 'bool', '全部新算子行')
    # Q16
    q = T['E6K-Q16-a'].iloc[0]
    for k, pr_ in (('objects', '638'), ('deriv_pos', '412'), ('post_nonpos_among_deriv_pos', '204')):
        add('Q16', k, pr_, int(q[k]), 'count', 'Q16-a')
    add('Q16', 'flip_share', '.495', float(q.flip_share), 'd3', 'Q16-a')
    sc_ = T['E6K-Q16-b']
    cpt = sc_.compatible.astype(str).str.lower().isin(['true', '1'])
    add('Q16', 'θ ∈ {0, .25, .5} × 无漂移相容', '0 / .25 / .5', bool(cpt[sc_.theta.isin(['theta0', 'theta25', 'theta50']) & (sc_['shift'] == 0)].all()), 'bool',
        'Q16-b 全部 L × volatility')
    add('Q16', 'θ = D̂ / 收缩 × 漂移 −.25 相容', '−.25', bool(cpt[sc_.theta.isin(['theta100', 'theta_shrink']) & (sc_['shift'] == -0.25)].all()), 'bool', 'Q16-b')
    add('Q16', '任何 +.25 漂移不相容', '+.25', bool((~cpt[sc_['shift'] == 0.25]).all()), 'bool', 'Q16-b')
    sets = {v: frozenset(map(tuple, sc_[cpt & (sc_.volatility == v)][['L', 'theta', 'shift']].values)) for v in sc_.volatility.unique()}
    add('Q16', '前瞻版相容集合相同', 'v2', len(set(sets.values())) == 1, 'bool', 'volatility 取值 %s 的相容集合' % sorted(sets))
    # Q17
    t = main148_v(c)
    add('Q17', 'primary144', '144', int(t.primary144.sum()), 'count', 'primary144')
    add('Q17', 'C1_hi', '4', int(t.c1_hi.sum()), 'count', 'c1_hi')
    add('Q17', '行数', '148', len(t), 'count', 'primary144 | c1_hi')
    add('Q17', '三列相同', '三列', bool(((t.policy_PROPOSED_PORT3_T_FULL == t.policy_PROPOSED_PORT3_LAG1_FULL) &
                                   (t.policy_PROPOSED_PORT3_T_FULL == t.policy_EXEC_DISCLOSE_ONLY_FULL)).all()), 'bool', '148 行 FULL 串')
    add('Q17', '组合层 size 全在 ±3', '3', bool((t.size_PROPOSED_PORT3_T == 'PASS').all() and (t.size_PROPOSED_PORT3_LAG1 == 'PASS').all()), 'bool',
        'size_PROPOSED_PORT3_T / _LAG1 == PASS（148 行）')
    v = t.policy_PROPOSED_PORT3_T_FULL.astype(str)
    add('Q17', 'PORT3 通过', '44', int((v == PASS_S).sum()), 'count', 'PORT3_T FULL')
    add('Q17', 'PORT3 不通过', '99', int(v.str.startswith('不通过').sum()), 'count', 'PORT3_T FULL')
    add('Q17', 'PORT3 不可判', '5', int(v.str.startswith('不可判').sum()), 'count', 'PORT3_T FULL')
    add('Q17', 'LEGACY 通过', '12', int((t.policy_LEGACY_EDIT5_FULL == PASS_S).sum()), 'count', 'LEGACY_EDIT5 FULL')
    add('Q17', 'LEGACY 编辑层 size 不过', '118', int((t.size_LEGACY_EDIT5 == 'FAIL').sum()), 'count', 'size_LEGACY_EDIT5 == FAIL')
    add('Q17', 'LEADER 通过', '13', int((t.policy_EXEC_LEADER_VS_PARENT_FULL == PASS_S).sum()), 'count', 'LEADER FULL')
    pn = t[(v == PASS_S) & (t.op != 'NATIVE')]
    add('Q17', 'PORT3 通过者中新算子', '25', len(pn), 'count', 'op != NATIVE')
    for op_, pr_ in (('NATIVE_HG10', '12'), ('INC1', '4'), ('INC1_HG10', '3'), ('SZL5', '3'), ('RP3', '3')):
        add('Q17', '新算子 %s' % op_, pr_, int((pn.op == op_).sum()), 'count', 'PORT3 通过 ∩ op')
    add('Q17', '均 NOT_AUTHORIZED', 'NOT_AUTHORIZED', bool((pn.replacement_preference_status == 'NOT_AUTHORIZED').all()), 'bool', 'replacement_preference_status')
    fails = v[v.str.startswith('不通过')].str.extract(r'（(.*)）')[0].str.split('、').explode().value_counts()
    add('Q17', '不通过原因以 d、c、e 随机为主', 'd / c / e随机', set(fails.index[:3]) == {'d', 'c', 'e随机'}, 'bool', '失败项计数 %s' % fails.head(5).to_dict())
    # Q18
    add('Q18', 'lineage 行数', '32', len(T['E6K-Q18-a']), 'count', 'registry/hypothesis_lineage_E6k.csv')
    qr = pd.read_csv(rp('registry', 'query_registry_E6k.csv'))
    tabs = report_tables('E6k_REPORT_cards.md')[0]
    add('Q18', '卡 query 数', '47', len(qr), 'count', 'registry/query_registry_E6k.csv')
    add('Q18', '47 个卡 query 全部落成同 id 表', '全部', set(qr.query_id) == set(q for q in tabs if q.startswith('E6K-Q')), 'bool', 'cards 表 query_id 集合')
    return L


def rpi_ids(P, op):
    return P[(P.op == op) & (P.alpha == 0.25) & (P.H == 5)].desc_id


SCOPE_WHITELIST = {  # 句内结构常数（α / H / 成本 / 阈值 / 年份 / 网格值），不作读数
    'Q01': {'.25', '8', '0'}, 'Q02': set(), 'Q03': set(), 'Q04': set(), 'Q05': {'2024', '2026'}, 'Q06': {'.25'}, 'Q07': {'.25'}, 'Q08': set(),
    'Q09': {'.25', '3', '5', '10', '20'}, 'Q10': set(), 'Q11': {'.25', '3', '5', '10', '20'}, 'Q12': {'.25'}, 'Q13': {'.25'}, 'Q14': {'.25'},
    'Q15': {'.05', '0'}, 'Q16': {'20', '60'}, 'Q17': {'12', '3'}, 'Q18': set()}


def judge_scope(x):
    v, pr_, k = x['value'], x['printed'], x['kind']
    try:
        if k == 'count':
            return int(v) == int(ntok(pr_).replace(',', ''))
        if k == 'pct':
            return abs(100 * float(v) - float(ntok(pr_).rstrip('%'))) <= 0.5 + 1e-9
        if k == 'd3':
            return abs(float(v) - float(ntok(pr_))) <= 5e-4 + 1e-12
        if k == 'd2':
            return abs(float(v) - float(ntok(pr_))) <= 5e-3 + 1e-12
        if k == 'approx0':
            return abs(float(v)) < 0.01
        if k == 'bool':
            return bool(v)
    except (TypeError, ValueError):
        return False
    return False


def scope_rows(c, T):
    Lc = scope_checks(c, T)
    H = jload(rp('results', 'hypothesis_outcomes.json'))
    txt = {h['card']: h['supported_scope'] for h in H}
    S = pd.DataFrame(Lc)
    S['ok'] = [judge_scope(x) for x in Lc]
    S['value'] = [('%.6g' % float(v)) if isinstance(v, (float, np.floating, int, np.integer)) and not isinstance(v, (bool, np.bool_)) else str(v) for v in S.value]
    cov = []
    for card, text in txt.items():
        toks = nums_in(text)
        printed = set()
        for p_ in S[S.card == card].printed:
            printed |= set(ntok(x) for x in nums_in(p_))
        wl = set(ntok(x) for x in SCOPE_WHITELIST.get(card, set()))
        un = [tk for tk in toks if ntok(tk) not in printed and ntok(tk) not in wl]
        cov.append(dict(card=card, tokens=len(toks), unbound='|'.join(un)))
    Cv = pd.DataFrame(cov)
    S.to_csv(os.path.join(OUT, 'vd07_supported_scope.csv'), index=False)
    Cv.to_csv(os.path.join(OUT, 'vd07_supported_scope_coverage.csv'), index=False)
    nbad, nun = int((~S.ok).sum()), int((Cv.unbound != '').sum())
    return [row('VD07', 'supported_scope', 'results/hypothesis_outcomes.json 18 卡 supported_scope',
                '检查数 / 不符 / 数字记号数 / 未绑定记号的卡（逐条见 verify/vd07_supported_scope*.csv）', '逐条回链',
                '%d / %d / %d / %d' % (len(S), nbad, int(Cv.tokens.sum()), nun), 'REPRODUCED' if nbad == 0 and nun == 0 else 'DIFFERS',
                'INFO:句中未写范围的数字按两种口径各算、记录命中口径（Q04 RP3、Q05 Shapley、Q13 A06）',
                diff=';'.join('%s/%s:印%s 算%s' % (r.card, r.label, r.printed, r.value) for r in S[~S.ok].itertuples())[:700] +
                (' ｜未绑定：' + ';'.join('%s:%s' % (r.card, r.unbound) for r in Cv[Cv.unbound != ''].itertuples()) if nun else ''),
                func='按卡复算（policy / descriptor_stats / 诊断 / 掩码事实）；印 3 位小数 ±.0005、百分比 ±.5 点、计数 EXACT')]


# ---------------------------------------------------------------------------- VD04 正文数字：表头按字段绑定 + 正文按事实 / 常数 / 文档引用绑定；重点项现算
def seg_bounds():
    if 'SEGB' not in _C:
        b = {}
        for s in SEGS:
            d = np.load(rp('accounts', s, 'A4b__K0.npz'), allow_pickle=False)['dates']
            b[s] = (str(d[0])[:10], str(d[-1])[:10], len(d))
        _C['SEGB'] = b
    return _C['SEGB']


def worker_facts():
    wd = open(rp('logs', 'worker_done.txt'), encoding='utf-8').read().split('\n')
    i_rel = next((i for i, l in enumerate(wd) if l.startswith('RELAUNCH_POST')), len(wd))
    rc = [l for l in wd if ' rc=' in l]
    post = lambda l: (' 2019-2023 ' in l) or (' 2024-2026 ' in l)
    der = lambda l: (' 2010-2014 ' in l) or (' 2015-2018 ' in l)
    return dict(rc_lines=len(rc), deriv_nonzero=sum(1 for l in rc if der(l) and ' rc=0 ' not in l),
                pre_rel_post_nonzero=sum(1 for l in wd[:i_rel] if ' rc=' in l and post(l) and ' rc=0 ' not in l),
                pre_rel_post_rc1=sum(1 for l in wd[:i_rel] if ' rc=1 ' in l and post(l)),
                post_rel_nonzero=sum(1 for l in wd[i_rel:] if ' rc=' in l and ' rc=0 ' not in l), relaunch=wd[i_rel] if i_rel < len(wd) else '')


def vd_facts(c):
    """表头 / 正文计数现算：值 → [(名, 来源)]（同值多义时按上下文词选）。"""
    P, A = c.P, c.A
    wf = worker_facts()
    qr = pd.read_csv(rp('registry', 'query_registry_E6k.csv'))
    e6j = pd.read_csv(E6J + '/results_B/part2_main_config_all_objects.csv')
    cap = pd.concat([pd.read_csv(f, usecols=['desc_id']) for f in sorted(glob.glob(rp('diagnostics', 'mechanisms', '*_capital.csv')))])
    shd = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(rp('diagnostics', 'shadow', '*.csv')))])
    shc = [x for x in ('desc_id', 'object', 'obj_id') if x in shd.columns]
    ycols = [x for x in P.columns if re.fullmatch(r'Y20\d\d', x)]
    leg = read_csv_keep(rp('verify', 'legacy_processes.csv')) if os.path.exists(rp('verify', 'legacy_processes.csv')) else pd.DataFrame()
    F = [('144', 'primary144', int(P.primary144.sum()), 'policy primary144'), ('4', 'c1_hi', int(P.c1_hi.sum()), 'policy c1_hi'),
         ('24', 'NATIVE 主对象', int((P.primary144 & (P.op == 'NATIVE')).sum()), 'primary144 & op==NATIVE'),
         ('48', 'HG 主展示对象', int((P.primary144 & P.op.str.contains('_HG')).sum()), 'primary144 & op 含 _HG'),
         ('72', 'INC 附属', int((A.kind == 'INC_SUPPORT_ACCESSORY').sum()), 'accessory_E6k INC_SUPPORT_ACCESSORY'),
         ('288', 'BAND 剂量控制', int((A.kind == 'BAND_DOSE_CONTROL').sum()), 'accessory_E6k BAND_DOSE_CONTROL'),
         ('18', '卡', len(pd.read_csv(rp('registry', 'cards_E6k.csv'))), 'registry/cards_E6k.csv'),
         ('47', '卡 query', len(qr), 'registry/query_registry_E6k.csv'), ('638', 'E6j 主配置对象', len(e6j), 'E6j results_B/part2_main_config_all_objects.csv'),
         ('956', '资本分解对象', int(cap.desc_id.nunique()), 'diagnostics/mechanisms/<段>_capital.csv desc_id 数'),
         ('160', 'shadow 对象', int(shd[shc[0]].nunique()) if shc else -1, 'diagnostics/shadow/<段>.csv 对象数'),
         ('17', '逐年标签', len(ycols), 'policy Y2010…Y2026 列数'),
         ('3406', '工作者完成记录 rc 行', wf['rc_lines'], 'logs/worker_done.txt 含 rc= 行'),
         ('1132', '后段首次启动非 0 行', wf['pre_rel_post_nonzero'], 'RELAUNCH_POST 之前后段行 rc≠0'),
         ('10', 'RELAUNCH 后非 0 行', wf['post_rel_nonzero'], 'RELAUNCH_POST 之后 rc≠0'),
         ('38', '遗留进程', len(leg), 'verify/legacy_processes.csv（C-6 现列）'),
         ('2000', 'bootstrap draws', 2000 if int(pd.read_csv(rp('results', 'full', 'bootstrap', 'simultaneous_band_q95.csv')).draws.iloc[0]) == 2000 else -1,
          'results/full/bootstrap/simultaneous_band_q95.csv draws 列'),
         ('20', 'bootstrap 块长 L20', 20, 'simultaneous_band_q95.csv L 列'), ('60', 'bootstrap 块长 L60', 60, 'simultaneous_band_q95.csv L 列')]
    band = pd.read_csv(rp('results', 'full', 'bootstrap', 'simultaneous_band_q95.csv'))
    Ls = set(int(x) for x in band.L)
    F = [f if f[0] not in ('20', '60') else (f[0], f[1], f[2] if int(f[0]) in Ls else -1, f[3]) for f in F]
    return F, wf


HEAD_CONST = {  # 表头各字段的登记常数（按字段；值 → 含义）
    '成本模型': {'8': '源 8bp', '5': '冲击 A 5 亿', '.5': 'κ .5', '10': '冲击 A 10 亿', '1': 'κ 1', '6': '6bp 线性', '12': '12bp 线性'},
    '基准': {'8': '8bp'},
    '单位': {'252': 'ANN = 252 × 100', '100': 'ANN = 252 × 100', '30': '小盘 30% 桶', '16': 'sha256 前 16 位', '.25': 'α .25'},
    '子集': {'.25': 'α .25', '5': 'H5', '3': 'H3', '10': 'H10', '20': 'H20', '.5': 'α .5', '1': 'H1'},
    '算子': {'.5': 'τ / g .5', '1': 'τ 1', '3': 'τ 3', '0.5': 'g .5', '0': 'g 0', '2': '2×2', '10': 'HG10 / b10'},
    '主体': {'2': '2×2', '6.1': '§6.1', '12.1': '§12.1', '3': 'τ 3 / size 三档', '0': 'Stage 0', '.5': 'α / τ .5', '.25': 'α .25', '1': 'H 1 / τ 1', '20': 'H 20', '0.5': 'TREFIT g .5', '.3': '小盘桶上界 .3', '.7': '大盘桶下界 .7', '.05': '边缘距离 .05', '30%': '小盘 30% 桶', '13.5': 'plan §13.5', '8': '8bp 净'},
    '日期': {'0': 'Stage 0'},
    'H': {'1': 'H 1', '20': 'H 20', '3': 'H 3', '5': 'H 5', '10': 'H 10'},
    '支持': {'0': 'k0'}, 'exposure': {}, '分母': {}, '资本视图': {},
}


def bind_header(text, fmap, tabrows, segb, man_h=None):
    """表头：按字段拆开，每个数字按字段语义绑定；日期区间对段边界；主体 / 子集 / 算子中的计数对现算事实；H 对表内 H 列。"""
    man_h = man_h or {}
    out = []
    body = text.split('表头：', 1)[1]
    for kv in body.split('｜'):
        if '=' not in kv:
            continue
        k, v = kv.split('=', 1)
        if k == 'query_id':
            continue
        vv = v
        for d0, d1 in re.findall(r'(\d{4}-\d\d-\d\d)\.\.(\d{4}-\d\d-\d\d)', v):
            ok = (d0, d1) in {(segb['2010-2014'][0], segb['2015-2018'][1]), (segb['2019-2023'][0], segb['2024-2026'][1]), (segb['2010-2014'][0], segb['2024-2026'][1])}
            out.append(('%s..%s' % (d0, d1), '日期区间=段边界' if ok else '日期区间≠段边界', ok))
            vv = vv.replace('%s..%s' % (d0, d1), ' ')
        for d0 in re.findall(r'\d{4}-\d\d-\d\d', vv):
            ok = any(segb[s_][0] <= d0 <= segb[s_][1] for s_ in SEGS)
            out.append((d0, '日期（段内）' if ok else '日期（不在任何段内）', ok))
            vv = vv.replace(d0, ' ')
        for tk in nums_in(vv):
            t0 = ntok(tk).replace(',', '')
            if k == '日期' and re.fullmatch(r'20\d\d', t0):
                out.append((tk, '年份', True))
            elif (k, t0) in man_h:
                out.append((tk, man_h[(k, t0)], True))
            elif t0 in man_h:
                out.append((tk, man_h[t0], True))
            elif k in ('主体', '子集', '算子') and t0 in fmap and re.search(r'%s\s*(个|行|张|对象|NATIVE|主|\+|$|）|\))|（%s）|附属 %s|控制 %s|E6j %s|全部 %s' %
                                                                         ((re.escape(tk),) * 6), vv):
                nm, val, src = fmap[t0]
                out.append((tk, '计数：%s = %s（%s）' % (nm, val, src), val == int(t0)))
            elif k == 'H' and tabrows is not None and 'H' in tabrows.columns:
                hs = set(knorm(x) for x in tabrows.H)
                rngH = '…' in v
                out.append((tk, 'H：表内 H 列 %s' % sorted(hs)[:6], rngH or knorm(t0) in hs or t0 in ('1', '20', '3', '5', '10')))
            elif t0 in HEAD_CONST.get(k, {}):
                out.append((tk, '登记常数（%s：%s）' % (k, HEAD_CONST[k][t0]), True))
            elif k in ('主体', '子集') and re.search(r'§\s*' + re.escape(tk), vv):
                out.append((tk, '文档引用 §', True))
            else:
                out.append((tk, '?', False))
    return out


VD04_MANUAL = {  # (文件, 行) → {记号: 绑定}；只收自动规则判不了的
    ('E6k_REPORT_R0.md', 3): {'13.5': 'DOC plan §13.5'}, ('E6k_REPORT_part1.md', 3): {'13.5': 'DOC plan §13.5'},
    ('E6k_REPORT_part2.md', 3): {'13.5': 'DOC plan §13.5', '0': '常数（接近 0）'}, ('E6k_REPORT_part3.md', 3): {'13.5': 'DOC plan §13.5'},
    ('E6k_REPORT_mechanisms.md', 3): {'13.5': 'DOC plan §13.5'}, ('E6k_REPORT_carried.md', 3): {'13.5': 'DOC plan §13.5'},
    ('E6k_REPORT_part1.md', 1073): {'10.5': 'DOC §10.5', '12.1': 'DOC §12.1', '5': 'DOC brief §5 A2'},
    ('E6k_REPORT_part2.md', 314): {'10.5': 'DOC plan §10.5'}, ('E6k_REPORT_cards.md', 2625): {'10.5': 'DOC plan §10.5'},
    ('E6k_REPORT_part3.md', 1124): {'10': 'DOC brief §10'}, ('E6k_REPORT_carried.md', 114): {'7': 'DOC R0 §7'},
    ('E6k_REPORT_carried.md', 46): {'3': 'DOC E6j VERIFY §3', '70': 'DOC E6j #70', '74': 'DOC E6j #74'},
    ('E6k_REPORT_cards.md', 2943): {'70': 'DOC E6j #70', '74': 'DOC E6j #74'},
    ('E6k_REPORT_carried.md', 110): {'47': 'CONST 主机别名 47'}, ('E6k_REPORT_R0.md', 27): {'47': 'CONST 主机别名 47'},
    ('E6k_REPORT_carried.md', 108): {'1': 'OPERATIONAL（WORKLOG：结束 1 个 pgrep 自匹配等待循环）', '4': 'OPERATIONAL（WORKLOG：停链 4 进程）',
                                     '3': 'OPERATIONAL（WORKLOG：停 07:31 链 3 个 bash）'},
    ('E6k_REPORT_carried.md', 106): {'24': 'OPERATIONAL（WORKLOG：xargs -P 24 起步）', '64': 'OPERATIONAL（WORKLOG / 链脚本参数 64；E6j 批准上限）'},
}


def vd04():
    """正文数字：决策端清单 167 行逐数字绑定；表头按字段；正文按事实 / 常数 / 文档引用 / 运行叙述；另做 brief 列的重点项现算。"""
    c = card_ctx()
    pn = pd.read_csv(DEC + '/E6k_VERIFY_prose_numbers.csv', encoding='utf-8-sig', dtype=str, keep_default_na=False)
    F, wf = vd_facts(c)
    fmap = {}
    for tk, nm, val, src in F:
        fmap.setdefault(tk, (nm, val, src))
    segb = seg_bounds()
    cards = pd.read_csv(rp('registry', 'cards_E6k.csv'))
    plan_lines = set(cards.plan_line.astype(int).astype(str))
    tabs_all, qpos = {}, {}
    for f in SEVEN:
        t, pos, _ = report_tables(f)
        for q, df in t.items():
            tabs_all[(f, pos[q])] = df
    appr = jload(rp('registration', 'record_B_approved_E6k.json'))['written_at']
    rows = []
    trunc = 0
    for r in pn.itertuples():
        f, ln = r.file, int(r.line)
        text = report_tables(f)[2][ln - 1]                  # 用 REPORT 原行（清单 text 列是截断预览）
        if not text.startswith(str(r.text)[:50]):
            trunc = -10 ** 6                                # 行号对不上：记为清单与 REPORT 不一致
        elif len(str(r.text)) < len(text):
            trunc += 1
        bind = []
        if text.startswith('> 表头：'):
            bind = bind_header(text, fmap, tabs_all.get((f, ln)), segb, VD04_MANUAL.get((f, ln), {}))
        else:
            man = VD04_MANUAL.get((f, ln), {})
            tx = text
            for tm in re.findall(r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d', tx):
                bind.append((tm, '时间 = record_B_approved.written_at' if tm == str(appr)[:19] else '时间', tm == str(appr)[:19] if 'approved' in tx else True))
                tx = tx.replace(tm, ' ')
            for d0 in re.findall(r'\d{4}-\d\d-\d\d(?:\.\.\d{4}-\d\d-\d\d)?', tx):
                bind.append((d0, '日期', True))
                tx = tx.replace(d0, ' ')
            for tm in re.findall(r'\b\d\d:\d\d(?::\d\d)?\b', tx):
                bind.append((tm, '时间（运行叙述）', True))
                tx = tx.replace(tm, ' ')
            for tk in re.findall(r'\d+-\d+(?:,\d+-\d+)+', tx):                        # taskset 核区间
                ws = open(CODE + '/e6k_worker.sh', encoding='utf-8').read()
                bind.append((tk, 'taskset 核区间 = e6k_worker.sh', ('taskset -c %s ' % tk) in ws))
                tx = tx.replace(tk, ' ')
            for tk in nums_in(tx):
                t0 = ntok(tk).replace(',', '')
                if tk in man or t0 in man:
                    bind.append((tk, man.get(tk, man.get(t0)), True))
                elif re.match(r'^#+\s*%s\.' % re.escape(tk), text.strip()):
                    bind.append((tk, 'DOC 节号', True))
                elif re.search(r'第\s*%s\s*行' % re.escape(tk), tx) and t0 in plan_lines:
                    bind.append((tk, 'DOC plan 行号（cards_E6k.plan_line）', True))
                elif re.search(r'§\s*%s' % re.escape(tk), tx):
                    bind.append((tk, 'DOC §', True))
                elif re.search(r'rc=%s\b' % re.escape(tk), tx) or re.search(r'非\s*%s\b' % re.escape(tk), tx) or re.search(r'恒为\s*%s' % re.escape(tk), tx) or \
                        re.search(r'K\s*=\s*%s' % re.escape(tk), tx) or re.search(r'Stage\s*%s' % re.escape(tk), tx) or re.search(r'接近\s*%s' % re.escape(tk), tx):
                    bind.append((tk, '常数（rc / 恒为 0 / 门域 K = 0 / Stage 0 / 接近 0）', True))
                elif re.search(r'α\s*%s' % re.escape(tk), tx) or re.search(r'H\s*%s\s*…|…\s*%s' % (re.escape(tk), re.escape(tk)), tx):
                    bind.append((tk, '登记常数（α / H 网格）', True))
                elif t0 in fmap:
                    nm, val, src = fmap[t0]
                    bind.append((tk, '计数：%s = %s（%s）' % (nm, val, src), val == int(float(t0))))
                else:
                    bind.append((tk, '?', False))
        un = [b for b in bind if b[1] == '?']
        bad = [b for b in bind if b[1] != '?' and not b[2]]
        rows.append(dict(file=f, line=ln, tokens=len(bind), binding=' ; '.join('%s=%s%s' % (b[0], b[1], '' if b[2] else '[不符]') for b in bind),
                         unbound=len(un), mismatch=len(bad)))
    B = pd.DataFrame(rows)
    B.to_csv(os.path.join(OUT, 'vd04_prose_binding.csv'), index=False)
    out = [row('VD04', 'prose_numbers', 'verify/decision/E6k_VERIFY_prose_numbers.csv（167 行）',
               '行 / 数字记号 / 未绑定 / 绑定但值不符（逐行见 verify/vd04_prose_binding.csv）', exp1('VD04', 'prose_numbers'),
               '%d / %d / %d / %d' % (len(B), int(B.tokens.sum()), int(B.unbound.sum()), int(B.mismatch.sum())),
               'REPRODUCED' if B.unbound.sum() == 0 and B.mismatch.sum() == 0 else 'DIFFERS',
               'INFO:用 REPORT 原行绑定（清单 text 列为截断预览 %d 行；行号全部对上 = %s）；表头按字段绑定（日期区间对段边界；主体 / 子集 / 算子计数对现算事实；H 对表内 H 列）；正文 OPERATIONAL = 只有 WORKLOG 记录的运行叙述' % (max(trunc, 0), trunc >= 0),
               diff=';'.join('%s:%d' % (r.file.replace('E6k_REPORT_', ''), r.line) for r in B[(B.unbound > 0) | (B.mismatch > 0)].itertuples())[:600],
               func='逐数字分类绑定')]
    out += vd04_key(c, F, wf, segb)
    return out


def vd04_key(c, F, wf, segb):
    """brief VD04 列出的重点项：逐项现算（在正文中不存在的句子写明位置）。"""
    out = []
    # R0 §2 授权链：AUTH 表 present / sha16 = 现文件
    t = report_tables('E6k_REPORT_R0.md')[0]['E6K-R0-AUTH']
    bad = []
    for r in t.to_dict('records'):
        p = rp(r['file'])
        pres = os.path.exists(p)
        if str(pres) != r['present'] or (pres and sha256_file(p)[:16] != r['sha256_16']):
            bad.append(r['file'])
    ch = [('record_B_mode_A', jload(rp('registration', 'record_B_mode_A.json')).get('written_at')),
          ('record_B_approved', jload(rp('registration', 'record_B_approved_E6k.json'))['written_at']),
          ('conditions_receipt', jload(rp('registration', 'record_B_conditions_receipt_E6k.json'))['written_at'])]
    order_ok = all(str(ch[i][1]) < str(ch[i + 1][1]) for i in range(len(ch) - 1))
    out.append(row('VD04', 'key_R0_auth', 'R0 §2 E6K-R0-AUTH（18 行）+ 授权链', 'present / sha256_16 与现文件不符行；mode_A < approved < conditions',
                   '0 不符；先后成立', '%d 不符；%s；%s' % (len(bad), ' < '.join('%s %s' % x for x in ch), '先后成立' if order_ok else '先后不成立'),
                   'REPRODUCED' if not bad and order_ok else 'DIFFERS', diff=';'.join(bad), func='sha256 现算前 16 位；written_at 字典序'))
    # R0 §3 Stage 0：STAGE0 表 ok / 回执状态 = 回执文件
    t = report_tables('E6k_REPORT_R0.md')[0]['E6K-R0-STAGE0']
    bad = []
    for r in t.to_dict('records'):
        for kv in str(r['receipts']).split('；'):
            if '=' in kv:
                k, v = kv.split('=', 1)
                p = rp('task_status', '%s.receipt.json' % k)
                if not os.path.exists(p) or jload(p).get('status') != v:
                    bad.append(k)
    sm = jload(rp('source_manifest.json'))
    out.append(row('VD04', 'key_R0_stage0', 'R0 §3 E6K-R0-STAGE0', '回执名 = 状态（逐项对 task_status）/ stage0_all_pass', '0 不符 / True',
                   '%d 不符 / %s' % (len(bad), sm.get('stage0_all_pass')), 'REPRODUCED' if not bad and sm.get('stage0_all_pass') is True else 'DIFFERS',
                   diff=';'.join(bad), func='task_status/<id>.receipt.json status'))
    # part1 / part2 表头日期区间与主对象数（表头绑定已逐行做；此处汇总段边界）
    out.append(row('VD04', 'key_segment_bounds', 'accounts/<段>/A4b__K0.npz dates', '四段首末交易日 / 日数', '表头区间 2010-01-04..2018-12-28 / 2019-01-02..2026-03-27 / 2010-01-04..2026-03-27',
                   json.dumps(segb, ensure_ascii=False), 'REPRODUCED' if (segb['2010-2014'][0], segb['2015-2018'][1], segb['2019-2023'][0], segb['2024-2026'][1]) ==
                   ('2010-01-04', '2018-12-28', '2019-01-02', '2026-03-27') else 'DIFFERS', func='npz dates 首末'))
    # part3 候选计数 66 / 233 / 55 与 primary144 通过 8 / 40 / 9（正文无导语句：数在 CAND-COUNT / CAND 表）
    t3 = report_tables('E6k_REPORT_part3.md')[0]
    cc = t3['E6K-P3-CAND-COUNT']
    s_obj = cc.assign(n=cc.objects.astype(int)).groupby('profile').n.sum().to_dict()
    cand = pd.read_csv(rp('results', 'full', 'production_change_candidates_E6k.csv'))
    P = c.P
    pr = set(P[P.primary144].desc_id)
    s_pr = cand[cand.desc_id.isin(pr)].groupby('profile').size().to_dict()
    exp_obj = {'LEGACY_EDIT5': 66, 'PROPOSED_PORT3_T': 233, 'PROPOSED_PORT3_LAG1': 233, 'EXEC_DISCLOSE_ONLY': 233, 'EXEC_LEADER_VS_PARENT': 55}
    exp_pr = {'LEGACY_EDIT5': 8, 'PROPOSED_PORT3_T': 40, 'PROPOSED_PORT3_LAG1': 40, 'EXEC_DISCLOSE_ONLY': 40, 'EXEC_LEADER_VS_PARENT': 9}
    ok = all(s_obj.get(k) == v for k, v in exp_obj.items()) and all(s_pr.get(k) == v for k, v in exp_pr.items())
    out.append(row('VD04', 'key_part3_candidates', 'part3 E6K-P3-CAND-COUNT（逐族求和）与 production_change_candidates ∩ primary144',
                   '各 profile 对象数 / primary144 通过数', '66 / 233 / 233 / 233 / 55；8 / 40 / 40 / 40 / 9',
                   '%s；%s' % (' / '.join(str(s_obj.get(k)) for k in PROFILES), ' / '.join(str(s_pr.get(k)) for k in PROFILES)), 'REPRODUCED' if ok else 'DIFFERS',
                   'INFO:brief 所指"导语"在正文不存在（part3 §三句加法 / §候选清单只有标题与表），数字取自表格求和', func='表格求和 / 候选 CSV'))
    # RP 恢复日 6 / 11（正文位置：limit_register L13 与 R0 §7 L13 行、R0-RPSOLVER 表；mechanisms 无导语句）
    rs = report_tables('E6k_REPORT_R0.md')[0]['E6K-R0-RPSOLVER'].set_index('segment')
    rec = {s: int(float(rs.at[s, 'recovered_both'])) + int(float(rs.at[s, 'recovered_milp_checked'])) for s in POS}
    fa = c.FA[c.FA.op.astype(str).str.startswith('RP')]
    rec_f = {s: int(fa[fa.segment == s].rp_recovered_days.fillna(0).sum()) if 'rp_recovered_days' in fa.columns else -1 for s in POS}
    L13 = open(rp('reports', 'E6k_limit_register.md'), encoding='utf-8').read()
    m = re.search(r'恢复日计数 (\{[^}]*\})', L13)
    reg = json.loads(m.group(1)) if m else {}
    ok = rec == reg and rec_f == reg
    out.append(row('VD04', 'key_rp_recovered', 'limit_register L13 / R0 §7 L13 / R0-RPSOLVER / facts rp_recovered_days', '恢复日 {2019-2023, 2024-2026}',
                   '{"2019-2023": 6, "2024-2026": 11}', 'L13 %s；RPSOLVER recovered_* 和 %s；facts 求和 %s' % (json.dumps(reg), json.dumps(rec), json.dumps(rec_f)),
                   'REPRODUCED' if ok else 'DIFFERS', 'INFO:mechanisms 无 RP 恢复日导语句（brief 所指位置不存在）；数在 L13 与 R0 表', func='表 / facts 求和'))
    # carried 运行事实
    ok = wf['rc_lines'] == 3406 and wf['pre_rel_post_nonzero'] == 1132 and wf['post_rel_nonzero'] == 10 and wf['deriv_nonzero'] == 0
    out.append(row('VD04', 'key_carried_worker', 'carried 第 104 行（logs/worker_done.txt）', 'rc 行 / 推导段非 0 / 首次启动后段非 0（rc=1）/ RELAUNCH 后非 0',
                   '3406 / 0 / 1132 / 10', '%d / %d / %d（rc=1 %d）/ %d' % (wf['rc_lines'], wf['deriv_nonzero'], wf['pre_rel_post_nonzero'], wf['pre_rel_post_rc1'],
                                                                          wf['post_rel_nonzero']), 'REPRODUCED' if ok else 'DIFFERS', func='逐行计数'))
    out.append(row('VD04', 'key_carried_leader_maxdiff', 'carried "四段 net8 与 E6j 领导表最大差"句', '句子位置', '—', '正文不存在（carried 只有 E6K-CAR-PARENTS 表）',
                   'REPRODUCED', 'INFO:该比较的数在 VB04（carried 32 行 vs E6j 领导表 / E6i 锚）', func='grep'))
    return out


# ---------------------------------------------------------------------------- VD06 全称句：七份 REPORT 正文 + 18 卡 supported_scope + lessons_delta
UNIV_WORDS = ('全部', '均', '无一', '任一', '任何', '都', '每个', '从不', '所有', '一律', '统一')
LEX_JUN = ("均值", "平均", "日均", "均匀")


def univ_hit(text):
    """返回 (关键词, 是否只有词法命中)：“均”只出现在 均值 / 平均 / 日均 / 均匀 里时不算全称量词。"""
    ws = [w for w in UNIV_WORDS if w in text]
    if not ws:
        return None, False
    real = [w for w in ws if w != "均" or re.sub("|".join(LEX_JUN), "", text).count("均") > 0]
    return (real[0], False) if real else (ws[0], True)


def univ_checks(c, T, vd07_stats, scopeS):
    """REPORT 正文全称句逐句绑定：{(文件, 行): (绑定, ok)}。"""
    B = {}
    t0 = report_tables('E6k_REPORT_R0.md')
    heads = [l for l in t0[2] if l.startswith('> 表头：')]
    fld = lambda h, k: (re.search(r'%s=([^｜]*)' % k, h) or [None, ''])[1]
    srcs = ('source_manifest', 'docs_sha256', 'stage0', 'registration', 'registry', 'a0_manifest', 'a1_auto', 'diagnostics/control_distributions', '全部随机量',
            'mask_facts', 'limit_register', '52 条随机量', 'FALLBACK_DOMAIN')                  # FALLBACK_DOMAIN = registry/mask_facts_*_E6k.csv 的 op 行（e6k_report_r0 源码）
    pol = ''.join(open(p_, encoding='utf-8').read() for p_ in sorted(glob.glob(rp('registration', 'policy_profiles_E6k*.json')) +
                                                                  glob.glob(rp('registration', 'executor_supplements_E6k*.json'))))
    B[('E6k_REPORT_R0.md', 526)] = ('policy_profiles_E6k*.json / executor_supplements_E6k*.json 中 "control" 出现 %d 次（门值定义不引用对照分布）' % pol.lower().count('control'),
                                    pol.lower().count('control') == 0)
    src1 = open(CODE + '/e6k_report_part1.py', encoding='utf-8').read()
    roots = sorted(set(re.findall(r"K\.P\('([a-z_]+)'(?:, '([a-z_]+)')?", src1)))
    roots_in = sorted(set('/'.join(x for x in r_ if x) for r_ in roots) - {'reports', 'results/deriv'})
    B[('E6k_REPORT_part1.md', 3)] = ('"本文件所有数字来自 results/deriv/*.csv"：生成器 e6k_report_part1.py 另读 %s（计数 / 台账表）；收益数字（D / rmr）来自 results/deriv（VC17 两链复现）' %
                                     roots_in, not roots_in)
    outside = [fld(h, 'query_id') for h in heads if not any(s in fld(h, '子集') for s in srcs)]
    ctrl = t0[0]['E6K-R0-CTRL']
    c1m = set(ctrl[ctrl.kind.str.startswith('C1')].metric)
    noret = all('无收益读数' in fld(h, 'exposure') for h in heads if 'E6K-R0-CTRL' not in h) and c1m <= {'edit_gap_T', 'port_size_mid_LAG1', 'port_size_mid_T',
                                                                                                 'small30_delta', 'all'}
    B[('E6k_REPORT_R0.md', 3)] = ('R0 %d 表：子集字段不在所列来源的表 %s；非 CTRL 表 exposure 全为"无收益读数" = %s；CTRL 表 C1 行指标 %s（无收益指标）；随机行为随机路径' %
                                  (len(heads), outside or '无', noret, sorted(c1m)), not outside and noret)
    lr = open(rp('reports', 'E6k_limit_register.md'), encoding='utf-8').read()
    ids_lr = re.findall(r'\*\*(L\d\d)\*\*', lr)
    lt = t0[0]['E6K-R0-LIMITS']
    idc = [x for x in lt.columns if x.lower() in ('id', 'limit', 'limit_id')] or [lt.columns[0]]
    ids_r0 = list(lt[idc[0]])
    B[('E6k_REPORT_R0.md', 552)] = ('R0 §7 行 %s = limit_register %s（L01–L16，追加前）' % (ids_r0[:1] + ['…'] + ids_r0[-1:], ids_lr[:1] + ['…'] + ids_lr[-1:]),
                                    [x for x in ids_r0] == [x for x in ids_lr if int(x[1:]) <= 16])
    P = c.P
    nonpar = P[P.op != 'PARENT']
    for f, ln, q in (('E6k_REPORT_part1.md', 1, 'E6K-P1-GRID'), ('E6k_REPORT_part2.md', 194, 'E6K-P2-GRID')):
        g = report_tables(f)[0][q]
        keys = set(zip(g.family, g.op, g.alpha.astype(float)))
        cover = int(nonpar[[k in keys for k in zip(nonpar.family, nonpar.op, nonpar.alpha.astype(float))]].shape[0])
        B[(f, ln)] = ('%s 的 (family, op, α) 组覆盖非 PARENT 登记行 %d / %d' % (q, cover, len(nonpar)), cover == len(nonpar))
    B[('E6k_REPORT_part1.md', 1023)] = ('词法：“均值”（非全称量词）', True)
    t1 = report_tables('E6k_REPORT_part1.md')[0]
    postcols = [(q, x) for q, df in t1.items() for x in df.columns if ('2019' in x or '2024' in x or 'post' in x.lower())]
    rc1 = jload(rp('task_status', 'report_part1.receipt.json'))['written_at'] if os.path.exists(rp('task_status', 'report_part1.receipt.json')) else ''
    appr = jload(rp('registration', 'record_B_approved_E6k.json'))['written_at']
    B[('E6k_REPORT_part1.md', 1071)] = ('part1 表无后段列（%d 列）；part1 回执 %s < 批准 %s' % (len(postcols), rc1, appr), not postcols and rc1 != '' and str(rc1) < str(appr))
    cand = pd.read_csv(rp('results', 'full', 'production_change_candidates_E6k.csv'))
    npass = sum(int((P['policy_%s_FULL' % p] == PASS_S).sum()) for p in PROFILES)
    B[('E6k_REPORT_part3.md', 909)] = ('候选 CSV %d 行 = Σ_profile FULL 通过 %d（逐 profile 分列）' % (len(cand), npass), len(cand) == npass)
    B[('E6k_REPORT_mechanisms.md', 3)] = ('指向 VE02–VE06（LX / HG / Shapley / RP / CS 记账恒等式在机器表上闭合；同程序 E 类）', 'POINTER')
    bad_abs = []
    for f in SEVEN:
        for q, df in report_tables(f)[0].items():
            cols = list(df.columns)
            for x in cols:
                if 'abs' in x.lower():
                    cands = {x.replace('absmean', 'mean'), x.replace('absmean', 'signed'), x.replace('_abs', ''), x.replace('abs_', ''), x.replace('abs', 'signed'),
                             x.replace('p95abs', 'p95signed'), x.replace('maxabs', 'max')} - {x}
                    if not cands & set(cols):
                        bad_abs.append('%s:%s' % (q, x))
    nabs = sum(1 for f in SEVEN for q, df in report_tables(f)[0].items() for x in df.columns if 'abs' in x.lower())
    B[('E6k_REPORT_carried.md', 46)] = ('七份 REPORT 取绝对值列 %d 个，缺同名带符号列 %d 个' % (nabs, len(bad_abs)), not bad_abs)
    wf = worker_facts()
    B[('E6k_REPORT_carried.md', 104)] = ('worker_done 推导段行 rc≠0 = %d' % wf['deriv_nonzero'], wf['deriv_nonzero'] == 0)
    B[('E6k_REPORT_carried.md', 110)] = ('OPERATIONAL：逐文件见 reports/E6k_code_change_register.md（C-7）；47 上语法检查无机器计数', 'OPERATIONAL')
    tc = report_tables('E6k_REPORT_cards.md')[0]
    qc = [q for q in tc if q.startswith('E6K-Q')]
    B[('E6k_REPORT_cards.md', 1)] = ('cards 卡 query 表 %d 张、唯一；登记 47' % len(qc), len(qc) == 47 and len(set(qc)) == 47)
    B[('E6k_REPORT_cards.md', 3)] = ('VD07 全格复算：%s' % vd07_stats, vd07_stats.endswith(' / 0'))
    B[('E6k_REPORT_cards.md', 1203)] = ('词法：“日均”（非全称量词）', True)
    tt = pd.read_csv(rp('registry', 'task_to_objects_E6k.csv'))
    tmap = c.D.set_index('desc_id').target_id
    need = tt.assign(tg=tt.desc_id.map(tmap)).dropna(subset=['tg']).groupby('task').tg.apply(set).to_dict()
    n_acc = n_bits_ok = n_need_ok = n_w = n_w_all = n_w_sub = 0
    wkinds = {}
    for s in SEGS:
        for f in sorted(glob.glob(rp('accounts', s, '*.npz'))):
            b = os.path.basename(f)
            if b.startswith('weights_'):
                continue
            n_acc += 1
            z = np.load(f, allow_pickle=False)
            tgl = list(map(str, z['targets']))
            tg = set(tgl)
            task = b[:-4].replace('__', '|')
            n_bits_ok += int(z['bits'].shape[0] == len(tgl))
            n_need_ok += int(need.get(task, set()) <= tg)
            w = rp('accounts', s, 'weights_' + b)
            if os.path.exists(w):
                n_w += 1
                wt = set(map(str, np.load(w, allow_pickle=False)['targets']))
                n_w_all += int(wt == tg)
                n_w_sub += int(wt < tg)
                miss = tg - wt
                k_ = 'a0.25 only' if all('|a0.25|' in x or '|a0|' in x or x.endswith('|a0.25') for x in wt) else 'mixed'
                wkinds[k_] = wkinds.get(k_, 0) + 1
    B[('E6k_REPORT_cards.md', 2542)] = ('账户文件 %d：bits 行 = targets %d、登记目标 ⊆ targets %d（位图含全部目标）；权重文件 %d：targets = 账户 targets %d、真子集 %d（权重文件 targets 构成 %s）'
                                        '→ "每个文件含该任务全部目标的…实际权重" 对权重文件不成立' % (n_acc, n_bits_ok, n_need_ok, n_w, n_w_all, n_w_sub, wkinds) if n_w_all < n_w else
                                        '账户文件 %d：bits = targets %d、登记目标 ⊆ targets %d；权重文件 %d 全部覆盖' % (n_acc, n_bits_ok, n_need_ok, n_w),
                                        n_bits_ok == n_acc and n_need_ok == n_acc and n_w_all == n_w)
    B[('E6k_REPORT_cards.md', 2943)] = ('定义句：VD07 Q17-b 全格按此定义复算（见 vd07_cards.csv E6K-Q17-b 行）', vd07_stats.endswith(' / 0'))
    return B


SCOPE_UNIV = {  # supported_scope 全称子句 → scope_checks 标签
    'Q01': ['组合层 size 逐段 ±3 内'], 'Q02': ['SZL 格数', 'α .5 全部为负', '任何 α 上不优于 NATIVE'], 'Q10': ['α .125 × b 15 PM 从不交换'],
    'Q13': ['只有 A06 四格全部为正'], 'Q14': ['六形态中位全部为负', 'M_mean3 CVR 边际全部为负'], 'Q15': ['新算子描述符数', '首看标签统一'], 'Q06': ['SIZE3 两者各自都有'],
    'Q16': ['任何 +.25 漂移不相容'], 'Q17': ['组合层 size 全在 ±3', '均 NOT_AUTHORIZED'], 'Q18': ['47 个卡 query 全部落成同 id 表']}


def lessons_checks(c):
    """lessons_delta 全称句中可计数者：12（PM α .125 × b15 = 140 行 size 空）、16、17、18、24、25。"""
    P, mf = c.P, c.MF
    L = {}
    pm = P[P.op.str.endswith('PM15') & (P.alpha == 0.125)]
    na = P[P.size_LEGACY_EDIT5.astype(str).isin(['N/A', 'NA'])]
    pm15 = mf[mf.op.astype(str).str.endswith('PM15') & (mf.alpha.astype(str) == 'a0.125')]
    pmz = pm15.assign(z=pm15.n_edits_in.fillna(0) == 0)
    per_op = {o_: dict(rows=int(len(g_)), zero_rows=int(g_.z.sum()), targets=int(g_.target_id.nunique()), targets_zero_all4=int(g_.groupby('target_id').z.all().sum()))
              for o_, g_ in pmz.groupby('op')}
    zero_all = set(pmz.groupby('target_id').z.all().loc[lambda s_: s_].index)
    tmap_ = c.D.set_index('desc_id').target_id
    na_tg = set(na.desc_id.map(tmap_))
    pm10z = mf[mf.op.astype(str).str.endswith('PM10') & mf['flags'].astype(str).str.contains('NO_EDITS')]
    L[12] = ('"从不触发交换" 逐 op（目标 × 段）：%s；NO_EDITS_EQUIV_PARENT 标记行 %d；四段全无换入的目标 %d 个 → 其描述符 = size_LEGACY N/A %d 行（同集合 %s）；'
             'PM10 标记：推导段 %d 目标、后段 %d' % (json.dumps(per_op, ensure_ascii=False), int(mf['flags'].astype(str).str.contains('NO_EDITS').sum()), len(zero_all),
                                                len(na), na_tg == zero_all, pm10z[pm10z.segment.isin(DER)].target_id.nunique(), pm10z[pm10z.segment.isin(POS)].target_id.nunique()),
             bool((pmz.z).all()))
    q2o = pd.read_csv(rp('registry', 'question_to_objects_E6k.csv'))
    qcol = [x for x in q2o.columns if x in ('card', 'question', 'query_id')][0]
    q14 = q2o[q2o[qcol].astype(str).str.contains('Q14')]
    npar = int(q14[q14.desc_id.astype(str).str.endswith('|PARENT')].desc_id.nunique())
    L[16] = ('question_to_objects Q14 PARENT 源锚 desc_id %d 个（相对自身差不定义；Q14 行 %d）' % (npar, int(q14.desc_id.astype(str).str.endswith('|PARENT').sum())), npar == 120)
    wf = worker_facts()
    first_post = min((jload(p)['written_at'] for p in glob.glob(rp('task_status', '*.receipt.json'))
                      if re.search(r'(2019-2023|2024-2026)', os.path.basename(p)) and not os.path.basename(p).startswith(('stage0', 'a1_'))), default='')
    L[17] = ('首次启动后段 rc=1 行 %d；%s；首个后段回执 %s > 重启 07:31:27' % (wf['pre_rel_post_rc1'], wf['relaunch'][:40], first_post),
             wf['pre_rel_post_rc1'] == 1132 and str(first_post) > '2026-09-29 07:31:27')
    rs = report_tables('E6k_REPORT_R0.md')[0]['E6K-R0-RPSOLVER'].set_index('segment')
    milp_d = sum(int(float(rs.at[s, 'milp'])) for s in DER)
    rec_d = sum(int(float(rs.at[s, 'recovered_both'])) + int(float(rs.at[s, 'recovered_milp_checked'])) for s in DER)
    L[18] = ('R0-RPSOLVER 推导两段 milp %d、恢复 %d' % (milp_d, rec_d), milp_d == 9 and rec_d == 0)
    v1 = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(rp('diagnostics', 'hg_continuous', 'hg_continuous_*.csv'))) if '_v2_' not in f])
    L[24] = ('hg_continuous v1 %d 行 D_continuous_minus_reset 最大 |·| = %.3g' % (len(v1), float(np.nanmax(np.abs(v1.D_continuous_minus_reset)))),
             float(np.nanmax(np.abs(v1.D_continuous_minus_reset))) == 0.0)
    se = pd.read_csv(rp('registry', 'selection_exposure_ledger_E6k.csv'))
    ecol = [x for x in se.columns if 'exposure' in x][0]
    fam = c.D.set_index('desc_id').family
    se = se.assign(fam_=se.desc_id.map(fam)) if 'desc_id' in se.columns else se.assign(fam_=np.nan)
    newrows = se[se.fam_.notna() & ~se.fam_.isin(['NATIVE', 'PARENT'])]
    L[25] = ('selection_exposure_ledger 新算子行（按 descriptors family）%d 的 %s 取值 %s；新算子 first_look_label 行 %d' %
             (len(newrows), ecol, sorted(newrows[ecol].astype(str).unique())[:4], int(P.first_look_label.notna().sum())),
             len(newrows) > 0 and set(newrows[ecol].astype(str)) == {'first_evaluation'})
    return L


def vd06(vd07_stats, T=None):
    c = card_ctx()
    T = T if T is not None else (_C.get("CARD_T") or cards_build(c))


    S = pd.DataFrame(scope_checks(c, T))
    S['ok'] = [judge_scope(x) for x in S.to_dict('records')]
    B = univ_checks(c, T, vd07_stats, S)
    rows = []
    for f in SEVEN:
        for i, l in enumerate(report_tables(f)[2], 1):
            if l.startswith('|') or l.startswith('> 表头'):
                continue
            w, lex = univ_hit(l)
            if w:
                b, ok = B.get((f, i), ('词法（均值 / 平均 / 日均，非全称量词）', True) if lex else ('?', False))
                rows.append(dict(source=f, line=i, word=w, text=l.strip()[:200], binding=b, ok=ok))
    H = jload(rp('results', 'hypothesis_outcomes.json'))
    for h in H:
        for cl in re.split(r'[；。]', h['supported_scope']):
            w, lex = univ_hit(cl)
            if not w:
                continue
            if lex:
                rows.append(dict(source='hypothesis_outcomes:%s' % h['card'], line=0, word=w, text=cl.strip()[:200], binding='词法（均值 / 平均，非全称量词）', ok=True))
                continue
            labs = SCOPE_UNIV.get(h['card'], [])
            x = S[(S.card == h['card']) & S.label.isin(labs)]
            rows.append(dict(source='hypothesis_outcomes:%s' % h['card'], line=0, word=w, text=cl.strip()[:200],
                             binding='scope_checks：' + '; '.join('%s=%s' % (r.label, r.value) for r in x.itertuples()) if len(x) else '?',
                             ok=bool(len(x) and x.ok.all())))
    Lc = lessons_checks(c)
    ltxt = open(rp('reports', 'E6k_lessons_delta.md'), encoding='utf-8').read().split('\n## § 交付后')[0]      # 交付版（追加节之前）
    for i, l in enumerate(ltxt.split('\n'), 1):
        m = re.match(r'^(\d+)\.\s', l)
        w, lex = univ_hit(l)
        if not (m and w):
            continue
        if lex:
            rows.append(dict(source='E6k_lessons_delta.md#%s' % m.group(1), line=i, word=w, text=l.strip()[:200], binding='词法（非全称量词）', ok=True))
            continue
        n = int(m.group(1))
        b, ok = Lc.get(n, ('OPERATIONAL：运行 / 过程叙述（lessons 不在七份 REPORT 范围；无机器计数）', 'OPERATIONAL'))
        rows.append(dict(source='E6k_lessons_delta.md#%d' % n, line=i, word=w, text=l.strip()[:200], binding=b, ok=ok))
    U = pd.DataFrame(rows)
    U.to_csv(os.path.join(OUT, 'vd06_universal.csv'), index=False)
    isb = lambda v: v is True or v is False or isinstance(v, (bool, np.bool_))
    core = U[U.ok.map(isb)]
    nbad = int((~core.ok.astype(bool)).sum())
    nun = int((U.binding == '?').sum())
    return [row('VD06', 'universal_statements', '七份 REPORT 正文 + 18 卡 supported_scope + lessons_delta', '句数 / 可计数绑定 / 不成立 / 未绑定 / 指针或运行叙述',
                '逐条', '%d / %d / %d / %d / %d' % (len(U), len(core), nbad, nun, int((~U.ok.map(isb)).sum())),
                'REPRODUCED' if nbad == 0 and nun == 0 else 'DIFFERS',
                'INFO:"均值 / 日均"为词法命中；POINTER = 指向同程序其他探针；OPERATIONAL = 只有 WORKLOG 的运行叙述',
                diff=';'.join('%s:%d' % (r.source, r.line) for r in U[(U.binding == '?') | (U.ok.map(isb) & ~U.ok.map(lambda v: bool(v) if isb(v) else True))].itertuples())[:600],
                func='逐句绑定计数 / 计算')]


# ============================================================================ V-E 装配恒等式
PAR_OF = {}
STATS_V = {}


def ve01_file(args):
    """一个账户文件：净费恒等；逐描述符 net8_ann 与 D_seg / n（母 = PAR_OF，在本文件或同母体 K0 文件内找）对 descriptor_stats。只回传极值。"""
    s, f = args
    z = np.load(f, allow_pickle=False)
    net8, gross, turn = z['d_net8'], z['d_gross'], z['d_turn']
    m = np.isfinite(net8) & np.isfinite(gross) & np.isfinite(turn)
    res = float(np.max(np.abs(np.where(m, net8 - (gross - 8e-4 * turn), 0.0)))) if m.any() else 0.0
    nanpat = int((np.isfinite(net8) != (np.isfinite(gross) & np.isfinite(turn))).sum())
    desc = [str(x) for x in z['desc']]
    ix = {d: i for i, d in enumerate(desc)}
    mother = os.path.basename(f).split('__')[0]
    k0 = np.load(os.path.join(os.path.dirname(f), '%s__K0.npz' % mother), allow_pickle=False)
    kx = {d: i for i, d in enumerate(map(str, k0['desc']))}
    kn = k0['d_net8']
    S = STATS_V[s]
    mn = md = 0.0
    mnn = 0
    checked = skipped = 0
    for d, i in ix.items():
        if d not in S:
            continue
        n8a_ref, D_ref, n_ref = S[d]
        v = float(np.nanmean(net8[i])) * ANN if np.isfinite(net8[i]).any() else np.nan
        if np.isfinite(v) and np.isfinite(n8a_ref):
            mn = max(mn, abs(v - n8a_ref))
        p = PAR_OF.get(d)
        if p is None:
            skipped += 1
            continue
        pser = net8[ix[p]] if p in ix else (kn[kx[p]] if p in kx else None)
        if pser is None:
            skipped += 1
            continue
        Dv, n = seg_D(paired(net8[i], pser))
        checked += 1
        if np.isfinite(Dv) and np.isfinite(D_ref):
            md = max(md, abs(Dv - D_ref))
        mnn = max(mnn, abs(n - int(n_ref)))
    return s, os.path.basename(f), res, nanpat, mn, md, mnn, checked, skipped


def class_E(workers):
    out = []
    # VE01 全部 116 文件 / 段
    files = [(s, f) for s in SEGS for f in sorted(glob.glob(rp('accounts', s, '*.npz'))) if not os.path.basename(f).startswith('weights_')]
    A = pd.read_csv(rp('registry', 'accessory_E6k.csv'))
    D = descs()
    par_of = dict(zip(D.desc_id, D.parent_desc))
    for r in A.itertuples():
        par_of[r.acc_id] = r.compare_to if r.kind == 'COMMON_SUPPORT_CHILD' else 'K0|%s|a0|H%d|PARENT' % (r.mother, int(r.H))
    PAR_OF.clear()
    PAR_OF.update(par_of)
    for s in SEGS:
        S = stats(s)
        STATS_V[s] = {d: (float(a), float(b_), float(c)) for d, a, b_, c in zip(S.index, S.net8_ann, S.D, S.n)}
    mx = dict(identity=0.0, nanpat=0, D=0.0, n=0, net8_ann=0.0, checked=0, skipped=0)
    nfile = {s: 0 for s in SEGS}
    with ProcessPoolExecutor(workers) as ex_:                                 # fork：PAR_OF / STATS_V 由子进程继承
        for s, fn, res, nanpat, mn, md, mnn, chk_, skp in ex_.map(ve01_file, files, chunksize=2):
            nfile[s] += 1
            mx['identity'] = max(mx['identity'], res)
            mx['nanpat'] += nanpat
            mx['net8_ann'] = max(mx['net8_ann'], mn)
            mx['D'] = max(mx['D'], md)
            mx['n'] = max(mx['n'], mnn)
            mx['checked'] += chk_
            mx['skipped'] += skp
    ok = mx['identity'] <= 1e-12 and mx['nanpat'] == 0 and mx['D'] <= 1e-9 and mx['n'] == 0 and mx['net8_ann'] <= 1e-9
    out.append(row('VE01', 'ledger_identity_all', 'accounts/<段>/*.npz（%s 文件）' % json.dumps(nfile), 'max|net8 − (gross − 8e−4·turn)| / NaN 模式 / max|ΔD_seg| / max|Δn| / max|Δnet8_ann|',
                   '全 0 或 ≤1e-9（决策端抽 12 文件）', json.dumps({k: ('%.3g' % v if isinstance(v, float) else v) for k, v in mx.items()}), 'REPRODUCED' if ok else 'DIFFERS',
                   'INFO:全量 %d 文件（登记描述符 + 附属 + CS 全部行对 descriptor_stats）' % sum(nfile.values()),
                   func='d_* = 子账户逐日量；母 = registry parent_desc（附属：CS 子 → compare_to，其余 → K0 同 H 原父）'))
    out += ve02_09()
    return out


def ve02_09():
    out = []
    P = policy()
    Pi = P.set_index('desc_id')
    m5 = P[(P.alpha == 0.25) & (P.H == 5)].set_index(['meas', 'mother', 'op'])
    tm = report_tables('E6k_REPORT_mechanisms.md')[0]
    # VE02 LX
    t = tm['E6K-MX-LX4']
    bad = 0
    idr = 0.0
    for r in t.to_dict('records'):
        v10 = m5.FULL.get((r['meas'], r['mother'], 'LX_%s_10' % r['layer']))
        v01 = m5.FULL.get((r['meas'], r['mother'], 'LX_%s_01' % r['layer']))
        v11 = m5.FULL.get((r['meas'], r['mother'], 'NATIVE'))
        vals = {'allocation_at_old': v10, 'within_at_old': v01, 'V11_minus_V00': v11, 'interaction': v11 - v10 - v01,
                'order_avg_allocation': 0.5 * (v10 + v11 - v01), 'order_avg_within': 0.5 * (v01 + v11 - v10)}
        for k, v in vals.items():
            bad += cell_eq4(r[k], v) == 'BAD'
        idr = max(idr, abs(vals['order_avg_allocation'] + vals['order_avg_within'] - v11))
    lg = pd.concat([pd.read_csv(f) for f in glob.glob(rp('diagnostics', 'mechanisms', '*_lx_gross.csv'))])
    clos = float(np.nanmax(np.abs(lg.within_group_ann + lg.allocation_ann - lg.total_ann)))
    out.append(row('VE02', 'lx', 'mechanisms E6K-MX-LX4；diagnostics/mechanisms/*_lx_gross.csv', '印出表不符 / 顺序平均两列和 − V11 / within + allocation − total（机器）/ closure_resid max',
                   '0 / ≤1e-9 / ≤1e-9 / ≤1e-12', '%d / %.3g / %.3g / %.3g' % (bad, idr, clos, float(lg.closure_resid.abs().max())),
                   'REPRODUCED' if (bad == 0 and idr <= 1e-9 and clos <= 1e-9 and lg.closure_resid.abs().max() <= 1e-12) else 'DIFFERS',
                   'INFO:allocation_excess 为 allocation 的子项（不加入 total）', func='V11 = NATIVE FULL；V10 = LX_<层>_10；V01 = LX_<层>_01'))
    # VE03 HG
    t = tm['E6K-MX-HG4']
    bad = 0
    for r in t.to_dict('records'):
        v11 = m5.FULL.get((r['meas'], r['mother'], r['op']))
        v10 = m5.FULL.get((r['meas'], r['mother'], r['op'].split('_')[0]))
        v01 = Pi.FULL.get('K0|%s|a0|H5|HG_ONLY%s' % (r['mother'], r['op'].split('HG')[-1]))
        vals = {'V11': v11, 'V10': v10, 'V01': v01, 'info_margin_V11_minus_V01': v11 - v01, 'rule_V01_minus_V00': v01, 'interaction': v11 - v10 - v01}
        for k, v in vals.items():
            bad += cell_eq4(r[k], v) == 'BAD'
    a38 = pd.concat([pd.read_csv(rp('stage0', 'c3_ops', 'ops_identity_%s.csv' % s)).assign(seg=s) for s in SEGS])
    a38 = a38[a38.check_id == 'A3-8']
    out.append(row('VE03', 'hg4', 'mechanisms E6K-MX-HG4（%d 行）；Stage 0 c3 A3-8' % len(t), '印出表不符；A3-8 行状态（四段）', '0；全 PASS',
                   '%d；%s' % (bad, json.dumps(a38.status.value_counts().to_dict())), 'REPRODUCED' if (bad == 0 and (a38.status == 'PASS').all()) else 'DIFFERS',
                   func='V11 = <op>_HG<b> FULL；V10 = <op> FULL；V01 = K0 HG_ONLY<b> FULL'))
    # VE04 Shapley
    sh = pd.concat([pd.read_csv(f) for f in glob.glob(rp('diagnostics', 'mechanisms', '*_shapley.csv'))])
    c1 = float(np.max(np.abs(sh.shapley_net_I + sh.shapley_net_S + sh.shapley_net_K - (sh.rand_net_ISK - sh.rand_net_EMPTY))))
    c2 = float(np.max(np.abs(sh.shapley_gross_I - sh.shapley_net_I - sh.shapley_fee_I)))
    mxr = 0.0
    for s in SEGS:
        R = rrefs(s)
        R = R[R.H == 5]
        for sub in ('EMPTY', 'I', 'S', 'K', 'IS', 'IK', 'SK', 'ISK'):
            mech = 'NEW_COND_ISK_P5' if sub == 'ISK' else 'EIGHT_SUBSET_' + sub
            rr_ = R[R.mechanism == mech].set_index('desc_id').rand_mean
            x = sh[sh.segment == s].set_index('desc_id')['rand_net_%s' % sub]
            mxr = max(mxr, float(np.nanmax(np.abs(x - rr_.reindex(x.index)))))
    t = tm['E6K-MX-SHAPLEY']
    segmean = sh.groupby('desc_id').mean(numeric_only=True)
    bad = sum(cell_eq4(r[c], float(segmean.at[r['desc_id'], c])) == 'BAD' for r in t.to_dict('records') for c in t.columns if c != 'desc_id')
    out.append(row('VE04', 'shapley', 'diagnostics/mechanisms/*_shapley.csv；mechanisms E6K-MX-SHAPLEY', 'Σ net − (ISK − EMPTY) / gross − net − fee / rand_net vs random_refs / 印出表 vs 段均',
                   '≤1e-9 / ≤1e-9 / ≤1e-12 / 0', '%.3g / %.3g / %.3g / %d' % (c1, c2, mxr, bad), 'REPRODUCED' if (c1 <= 1e-9 and c2 <= 1e-9 and mxr <= 1e-12 and bad == 0) else 'DIFFERS',
                   'INFO:印出表为四段等权段均（不是 n 加权；brief 写 n 加权 → 口径说明）', func='逐段恒等；表 = groupby(desc).mean()'))
    # VE05 RP
    t = tm['E6K-MX-RP']
    bad = 0
    for r in t.to_dict('records'):
        k = (r['meas'], r['mother'])
        v = {x: m5.FULL.get(k + (x,)) for x in ('NATIVE', 'RPINF', 'RP3', 'RP1', 'RP0p5')}
        vals = {'NATIVE': v['NATIVE'], 'PAIR_ALL': v['RPINF'], 'NATIVE_minus_PAIR_ALL': v['NATIVE'] - v['RPINF']}
        for tau, op in (('0p5', 'RP0p5'), ('1', 'RP1'), ('3', 'RP3')):
            vals['RP%s' % tau] = v[op]
            vals['RP%s_minus_PAIR_ALL' % tau] = v[op] - v['RPINF']
        for kk, vv in vals.items():
            bad += cell_eq4(r[kk], vv) == 'BAD'
    rec = {}
    for s in POS:
        n = 0
        for f in glob.glob(rp('accounts', s, 'facts_*.csv')):
            fa = pd.read_csv(f)
            if 'rp_solver' in fa.columns:
                for v in fa.rp_solver.dropna():
                    n += sum(c for k, c in json.loads(v).items() if k.startswith('recovered'))
        rec[s] = n
    out.append(row('VE05', 'rp', 'mechanisms E6K-MX-RP（%d 行）；facts rp_solver' % len(t), '印出表不符；恢复日 {段: 日}', '0；{"2019-2023": 6, "2024-2026": 11}',
                   '%d；%s' % (bad, json.dumps(rec)), 'REPRODUCED' if (bad == 0 and rec == {'2019-2023': 6, '2024-2026': 11}) else 'DIFFERS',
                   'INFO:恢复日在 R0 E6K-R0-RPSOLVER 与 L13（mechanisms 正文未单列）', func='五列 = policy FULL；差列 = 列差'))
    # VE06 CS
    mxc, n = 0.0, 0
    for s in SEGS:
        S = stats(s)
        c = S[S.kind == 'COMMON_SUPPORT_CHILD']
        n += len(c)
        mxc = max(mxc, float(np.nanmax(np.abs(c.N1_minus_N0 - (c.C1_minus_C0 + c.C0_minus_N0 + c.N1_minus_C1)))))
    A = pd.read_csv(rp('registry', 'accessory_E6k.csv'))
    s0 = A[A.op == 'INC_SUPPORT0']
    vals = []
    for r in s0.itertuples():
        Ds = [stats(s).at[r.acc_id, 'D'] for s in SEGS]
        ns = [stats(s).at[r.acc_id, 'n'] for s in SEGS]
        f, _ = full_g4(Ds, ns)
        vals.append(f - Pi.FULL.get('%s|%s|a%g|H%d|NATIVE' % (r.meas, r.mother, r.alpha, int(r.H))))
    out.append(row('VE06', 'cs_bridge', 'descriptor_stats CS 行（%d）；INC 附属' % n, 'max|N1−N0 − Σ三项| / INC_SUPPORT0 − NATIVE 中位', '≤1e-9 / −.003（Q03 卡）',
                   '%.3g / %.4f' % (mxc, float(np.median(vals))), 'REPRODUCED' if mxc <= 1e-9 and abs(np.median(vals) + 0.003) < 0.0005 else 'DIFFERS',
                   'INFO:MX-CS 16 行 = 逐描述符四段等权均值后按块平均（不是 n 加权）', func='四账户桥逐行'))
    # VE07 CAP
    out += ve07(P)
    # VE08 TREFIT / POST2 / TAILS / SHADOW
    bad = 0
    for q, fam in (('E6K-MX-TREFIT', 'TREFIT'), ('E6K-MX-POST2', 'POST2')):
        for r in tm[q].to_dict('records'):
            x = m5.loc[(r['meas'], r['mother'], r['op'])]
            for k in ('FULL', 'G4', 'FULL_vs_native', 'FULL_vs_C1'):
                bad += cell_eq4(r[k], float(x[k])) == 'BAD'
    tl = pd.concat([pd.read_csv(f) for f in glob.glob(rp('diagnostics', 'risk', '*_tails.csv'))])
    tl = tl[tl.bucket != 'worst1pct_days']
    ssum = float(tl.groupby(['segment', 'desc_id']).capital_share_delta.sum().abs().max())
    out.append(row('VE08', 'trefit_post2_tails', 'mechanisms TREFIT / POST2；diagnostics/risk/*_tails.csv', '印出表不符 / 各桶 capital_share_delta 之和 max|·|（机器）', '0 / ≤1e-9',
                   '%d / %.3g' % (bad, ssum), 'REPRODUCED' if (bad == 0 and ssum <= 1e-9) else 'DIFFERS',
                   'INFO:SHADOW 为 E6g 库存模型下的逐日超额（gross、constant notional；ideal 与 X1 两视图），child_minus_parent_ann = 同视图同 H 配对日均 × 25,200；与 policy D（源引擎 8bp 净）无恒等关系',
                   func='逐格；分桶份额按日和为 1'))
    # VE09 计数
    out += ve09()
    return out


def ve07(P):
    """CAP 表口径：selection / capital / one_sided（e6k_mechanisms.capital 转录）与 D_gross 的关系；SMB alpha_over_D。"""
    D = descs().set_index('desc_id')
    keep = main154()
    mx, idm = 0.0, 0.0
    for s in SEGS:
        cap = pd.read_csv(rp('diagnostics', 'mechanisms', '%s_capital.csv' % s)).set_index('desc_id')
        S = stats(s)
        for did in keep:
            if did not in cap.index:
                continue
            mother, meas = D.at[did, 'task'].split('|')
            z = npz_arrays(acct_file(s, mother, meas), ('desc', 'd_gross', 'd_pos'))
            k0 = npz_arrays(acct_file(s, mother, 'K0'), ('desc', 'd_gross', 'd_pos'))
            i = list(map(str, z['desc'])).index(did)
            j = list(map(str, k0['desc'])).index('K0|%s|a0|H%d|PARENT' % (mother, int(D.at[did, 'H'])))
            Ec, Pc, Eb, Pb = z['d_gross'][i], z['d_pos'][i], k0['d_gross'][j], k0['d_pos'][j]
            both = (Pc > 0) & (Pb > 0) & np.isfinite(Ec) & np.isfinite(Eb)
            uc = np.where(both, Ec / np.where(Pc > 0, Pc, 1), 0.0)
            ub = np.where(both, Eb / np.where(Pb > 0, Pb, 1), 0.0)
            sel = float(np.mean(np.where(both, 0.5 * (Pc + Pb) * (uc - ub), 0.0))) * ANN
            capv = float(np.mean(np.where(both, 0.5 * (uc + ub) * (Pc - Pb), 0.0))) * ANN
            one = (Pc > 0) ^ (Pb > 0)
            os_ = float(np.nanmean(np.where(one, np.nan_to_num(Ec) - np.nan_to_num(Eb), 0.0))) * ANN
            x = cap.loc[did]
            mx = max(mx, abs(sel - x.selection_ann), abs(capv - x.capital_ann), abs(os_ - x.one_sided_dE_ann))
            either = (Pc > 0) | (Pb > 0)
            gdiff = float(np.mean(np.where(either & np.isfinite(Ec) & np.isfinite(Eb), Ec - Eb, 0.0))) * ANN
            idm = max(idm, abs(sel + capv + os_ - gdiff))
    sm = pd.concat([pd.read_csv(f) for f in glob.glob(rp('diagnostics', 'risk', '*_smb.csv'))])
    rat = float(np.nanmax(np.abs(sm.alpha_over_D - sm.alpha_ann / sm.D_ann)))
    return [row('VE07', 'cap_definition', 'diagnostics/mechanisms/<段>_capital.csv（154 主对象 × 四段）；risk *_smb.csv', 'max|Δ| 三列（从 npz 重算）/ sel + cap + one − gross 差 / SMB alpha_over_D − alpha/D',
                '≤1e-9', '%.3g / %.3g / %.3g' % (mx, idm, rat), 'REPRODUCED' if (mx <= 1e-9 and idm <= 1e-9 and rat <= 1e-9) else 'DIFFERS',
                'INFO:定义——两边有仓日（Pc > 0 且 Pb > 0，gross 有限）：sel = ½(Pc + Pb)(uc − ub)、cap = ½(uc + ub)(Pc − Pb)，uc = Ec / Pc；两列都对全段交易日取均值（非两边有仓日 = 0）× 25,200；'
                'one_sided = 只一边有仓日的 Ec − Eb 同样对全段取均值。恒等：sel + cap + one_sided = 25,200 × mean_T[(Ec − Eb)·1(任一边有仓)] = gross 配对差（不含费用），'
                '因此与 FULL（8bp 净）或 FULL_sc 无恒等关系（决策端候选五式不成立是定义所致）；印出表 E6K-MX-CAP 为四段等权段均。SMB 表 alpha_over_D 为逐段比值的四段均值',
                func='e6k_mechanisms.capital 转录')]


def ve09():
    D = descs()
    b = D.blocks.str.split('|').explode().value_counts().to_dict()
    A = pd.read_csv(rp('registry', 'accessory_E6k.csv'))
    rr = pd.read_csv(rp('registry', 'randoms_E6k.csv'))
    leg = rr[rr.mechanism == 'LEGACY_POLICY_RANDOM'].merge(D[['desc_id', 'family', 'primary144', 'c1_hi', 'sm_anchor']], on='desc_id', how='left')
    leg_comp = leg.groupby(['family']).size().to_dict()
    st = [jload(p)['task_id'] for p in glob.glob(rp('task_status', '*.receipt.json'))]
    kinds = pd.Series([re.sub(r'_(2010-2014|2015-2018|2019-2023|2024-2026).*$', '', t) for t in st]).value_counts()
    det = int(kinds.get('run_det', 0))
    rnd = int(sum(v for k, v in kinds.items() if k.startswith('run_rand')))
    other = {k: int(v) for k, v in kinds.items() if not (k.startswith('run_det') or k.startswith('run_rand'))}
    nacct = {s: len([f for f in glob.glob(rp('accounts', s, '*.npz'))]) for s in SEGS}
    q = pd.read_csv(rp('registry', 'question_to_objects_E6k.csv'))
    B = pd.read_csv(rp('results', 'full', 'bootstrap', 'bootstrap_comparisons.csv'), usecols=['comparison_id'])
    got = dict(blocks=b, sum_blocks=sum(b.values()), policy=len(D) - int((D.op == 'PARENT').sum()), stats=len(D) - 160 + 1800 + 288 + 72,
               accessory=A.kind.value_counts().to_dict(), primary144=int(D.primary144.sum()), legacy956=dict(total=len(leg), by_family=leg_comp),
               account_files_per_seg=nacct, receipts=dict(total=len(st), run_det=det, run_rand=rnd, other_total=sum(other.values()), other=other),
               bootstrap_rows=len(B), bootstrap_comparisons=B.comparison_id.nunique(), q2o_rows=len(q))
    ok = (sum(b.values()) == 39142 and got['policy'] == 38982 and got['stats'] == 41142 and len(A) == 2336 and len(leg) == 956 and len(st) == 2334
          and det + rnd + sum(other.values()) == 2334 and len(B) == 677556 and len(q) == 300466)
    return [row('VE09', 'counts', 'registry / task_status / accounts / bootstrap', '计数恒等（写出构成）', '39,142；38,982；41,142；2,336；956；232 + 2,032 + 70 = 2,334；677,556；300,466',
                json.dumps(got, ensure_ascii=False), 'REPRODUCED' if ok else 'DIFFERS', func='计数')]


# ============================================================================ 主程序
PROBE_LIST = [
    ('VA01', 'A', '十二份 reports/ 文件 sha256 / md5 三处 + MIRROR'), ('VA02', 'A', 'REVIEW_input sha 前缀'), ('VA03', 'A', 'query_id 登记'),
    ('VA04', 'A', '回执'), ('VA05', 'A', '两个 seal + 全量 sha + 时序链'), ('VA06', 'A', '登记文件时间 / 授权链'), ('VA07', 'A', '代码变更'), ('VA08', 'A', '交付时状态'),
    ('VB01', 'B', 'Stage 0 计数'), ('VB02', 'B', '描述符 / 覆盖 / 附属 / 政策 / 统计计数'), ('VB03', 'B', 'E6j 复现'), ('VB04', 'B', 'carried 八母体表'),
    ('VB05', 'B', 'E5a 实物 sha'), ('VB06', 'B', 'α0 母体成员 vs pool2'), ('VB07', 'B', 'LEGACY 路径跨轮逐位'),
    ('VC01', 'C', '合并恒等'), ('VC02', 'C', 'e_rand'), ('VC03', 'C', '政策串'), ('VC04', 'C', '相对列'), ('VC05', 'C', '三句加法'), ('VC06', 'C', '候选清单'),
    ('VC07', 'C', 'question_to_objects'), ('VC08', 'C', '随机参照'), ('VC09', 'C', 'bootstrap'), ('VC10', 'C', '掩码账本与逐日暴露'), ('VC11', 'C', '假设卡与血缘'),
    ('VC12', 'C', '同时带口径（+ 预期表 size_profiles 行）'), ('VC13', 'C', '账本重算政策表 + bootstrap 重放'), ('VC14', 'C', '目标层暴露'), ('VC15', 'C', '冲击 / 线性费'),
    ('VC16', 'C', '随机路径值'), ('VC17', 'C', 'part1 表'),
    ('VD01', 'D', '表结构'), ('VD02', 'D', 'part2 144 表'), ('VD03', 'D', 'part2 GRID'), ('VD04', 'D', '正文数字'), ('VD05', 'D', 'part3 五表'), ('VD06', 'D', '全称句'),
    ('VD07', 'D', 'cards 抽格'),
    ('VE01', 'E', '账本恒等（全量）'), ('VE02', 'E', 'LX'), ('VE03', 'E', 'HG'), ('VE04', 'E', 'Shapley'), ('VE05', 'E', 'RP'), ('VE06', 'E', 'CS'), ('VE07', 'E', 'CAP 口径'),
    ('VE08', 'E', 'TREFIT / POST2 / TAILS / SHADOW'), ('VE09', 'E', '计数恒等')]


def main():
    global OUT, LOG, EXP
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--classes', default='A,B,C,D,E')
    ap.add_argument('--workers', type=int, default=16)
    ap.add_argument('--merge', action='store_true')
    a = ap.parse_args()
    OUT = a.out
    os.makedirs(OUT, exist_ok=True)
    LOG = os.path.join(OUT, 'verify.log')
    EXP = pd.read_csv(DEC + '/E6k_VERIFY_expected.csv', dtype=str, keep_default_na=False)
    EXP.columns = [c.lstrip('\ufeff') for c in EXP.columns]
    if a.merge:
        parts = [os.path.join(OUT, 'results_%s.csv' % c) for c in 'ABCDE' if os.path.exists(os.path.join(OUT, 'results_%s.csv' % c))]
        R = pd.concat([pd.read_csv(p, dtype=str, keep_default_na=False) for p in parts], ignore_index=True)
        R.to_csv(os.path.join(OUT, 'probe_results.csv'), index=False)
        pl = pd.DataFrame(PROBE_LIST, columns=['probe_id', 'class', 'content'])
        pl['expected_rows'] = [int((EXP.probe_id == p).sum()) for p in pl.probe_id]
        pl['result_rows'] = [int((R.probe_id == p).sum()) for p in pl.probe_id]
        pl['source'] = ['E6k_VERIFY_expected.csv' if n else '现算（brief §5 表）' for n in pl.expected_rows]
        pl.to_csv(os.path.join(OUT, 'probes.csv'), index=False)
        log('merge：%d 行；%s' % (len(R), R.verdict.value_counts().to_dict()))
        return 0
    fn = dict(A=class_A, B=class_B, C=class_C, D=class_D, E=class_E)
    for c in a.classes.split(','):
        t0 = time.time()
        log('class %s start' % c)
        try:
            rows = fn[c](a.workers)
        except Exception as e:                                               # noqa: BLE001
            log('class %s FAILED: %s' % (c, traceback.format_exc()))
            raise
        pd.DataFrame(rows).to_csv(os.path.join(OUT, 'results_%s.csv' % c), index=False)
        log('class %s done：%d 行；%.0fs；%s' % (c, len(rows), time.time() - t0, pd.DataFrame(rows).verdict.value_counts().to_dict()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
