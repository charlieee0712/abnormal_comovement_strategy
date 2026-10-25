# -*- coding: utf-8 -*-
"""E6o 公共常量与工程工具（brief `E6o_account_exit_stage.md`；plan v1.1 = 结果目录 PLAN_COPY.md，sha256 前 16 ce9e98c26ccbcb91）。
只放与经济口径无关的工程件：路径、段、E7 截止守卫、缓存命名空间、原子写、回执、状态词。
- 本轮产物只写 E6O_WORK（环境变量）；E6n 结果目录只读（E6N_WORK 指向它，供 e6n_* 读取函数使用）。
- 工具函数沿 e6n_core / e6m_core（只 import 不改）。"""
import os
import re
import json
import time
import hashlib

import numpy as np
import pandas as pd

VERSION = 'E6o-v1.1'
PLAN_SHA256 = 'ce9e98c26ccbcb9177a55fe10fe2d105f4d80e4232371bf400f8a9795a38b46a'
SPEC_SHA256 = 'f2cb96d6cfe512fb3e2375d674a530dd026c0d7d985885e6c338926105ac130b'
CUTOFF = '2026-03-27'
SEGS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')
DERIV_SEGS = ('2010-2014', '2015-2018')
POST_SEGS = ('2019-2023', '2024-2026')
SEG_SPAN = {'2010-2014': ('2010-01-04', '2014-12-31'), '2015-2018': ('2015-01-01', '2018-12-31'),
            '2019-2023': ('2019-01-01', '2023-12-31'), '2024-2026': ('2024-01-01', '2026-03-27')}
MINUTE_START = '2013-08-01'
FORMS = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
MAIN_FORM = 'A4b_CVRv5'
MEMS = ('NONE', 'HG10', 'LAG1_10')
MEMKEY = {'NONE': 'NONE|a0.25|Q0', 'HG10': 'HG10|a0.25|Q0', 'LAG1_10': 'LAG1_10|a0.25|Q0'}
HS = (5, 10, 20)
ANN_PP = 252.0 * 100.0
FEE_RATE = 4e-4            # 源：换手 ½Σ|Δact| × 8bp ⇒ 每单位成交名义 4bp（不再乘 2）
STOCK_CAP = 0.01
IND_DEV = 0.03
MACHINE = '47'
STATUS_OK = ('COMPUTED', 'UNKNOWN', 'NOT_APPLICABLE', 'UNMATCHED', 'MC_LIMIT', 'SOURCE_BINDING_PENDING',
             'POLICY_MAPPING_UNRESOLVED', 'RIGHT_CENSORED', 'NOT_RUN', 'NO_RANDOM_BY_SCOPE', 'BLOCKED', 'PASS', 'DIFFERS', 'INFO')

_HERE = os.path.dirname(os.path.abspath(__file__))
import e6j_core as _J  # noqa: E402  （results 根由既有常量推出，不另写含目录名的字面量）
RES_ROOT = os.path.dirname(_J.E6I_RES)
E6N_DIR = os.path.join(RES_ROOT, '20261015_0827_E6n_minute_path_stage')
os.environ.setdefault('E6N_WORK', E6N_DIR)
import e6n_core as N  # noqa: E402

assert_end_ok = N.assert_end_ok
assert_index_ok = N.assert_index_ok
sha_file = N.sha_file
sha_bytes = N.sha_bytes
canonical_json = N.canonical_json
san = N.san


def work():
    w = os.environ.get('E6O_WORK', '')
    if not w:
        raise RuntimeError('E6O_WORK 未设：E6o 产物只写本轮结果目录')
    if os.path.abspath(w).startswith(os.path.abspath(E6N_DIR)):
        raise RuntimeError('E6O_WORK 不得指向 E6n 目录')
    return w


def P(*parts):
    return os.path.join(work(), *parts)


def E6N(*parts):
    return os.path.join(E6N_DIR, *parts)


def rel(p):
    return os.path.relpath(p, work())


def cache_dir():
    """缓存命名空间：目录名含 'E6o-v1.1' 与 plan sha 前 8 位（闭包门 ⑮）；v1.0 缓存不复用。"""
    ev = N.env_versions()
    det = dict(version=VERSION, plan_sha256=PLAN_SHA256, spec_sha256=SPEC_SHA256,
               numeric_env=dict(python=ev['python'], numpy=ev['numpy'], pandas=ev['pandas'], numba=ev.get('numba', '')))
    h = sha_bytes(canonical_json(det).encode())[:12]
    d = P('cache_%s_plan%s_%s' % (VERSION, PLAN_SHA256[:8], h))
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, 'namespace.json')
    if not os.path.exists(p):
        atomic_write_json(p, det)
    return d


def log(msg, logfile=None):
    line = san('[%s] %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg))
    print(line, flush=True)
    if logfile:
        with open(logfile, 'a', encoding='utf-8') as fh:
            fh.write(line + '\n')


def _guard_path(p):
    a = os.path.abspath(p)
    if a.startswith(os.path.abspath(E6N_DIR)):
        raise RuntimeError('拒绝写入 E6n 目录：%s' % p)
    if not a.startswith(os.path.abspath(work())):
        raise RuntimeError('拒绝写入本轮结果目录之外：%s' % p)


def atomic_write_bytes(p, b):
    _guard_path(p)
    return N.atomic_write_bytes(p, b)


def atomic_write_json(p, obj):
    _guard_path(p)
    return N.atomic_write_json(p, obj)


def atomic_write_text(p, s):
    _guard_path(p)
    return N.atomic_write_text(p, s)


def atomic_write_csv(p, df):
    _guard_path(p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + '.tmp%d' % os.getpid()
    df.to_csv(tmp, index=False, lineterminator='\n', na_rep='')
    os.replace(tmp, p)
    return p


def atomic_write_npz(p, **arrs):
    _guard_path(p)
    return N.atomic_write_npz(p, **arrs)


def write_receipt(task_id, outputs, status='SUCCEEDED', code=(), **extra):
    outs, rows, cs = {}, {}, {}
    for p in outputs:
        if os.path.exists(p):
            outs[san(rel(p))] = sha_file(p)
            if p.endswith('.csv'):
                with open(p, 'rb') as fh:
                    rows[san(rel(p))] = max(sum(1 for _ in fh) - 1, 0)
    for p in code:
        if os.path.exists(p):
            cs[os.path.basename(p)] = sha_file(p)
    rec = dict(task_id=task_id, status=status, written_at=time.strftime('%Y-%m-%d %H:%M:%S'), version=VERSION, machine=MACHINE,
               pid=os.getpid(), outputs=outs, csv_rows=rows, code=cs, **json.loads(san(json.dumps(extra, ensure_ascii=False, default=str))))
    p = P('task_status', '%s.receipt.json' % re.sub(r'[:/|]', '_', task_id))
    atomic_write_json(p, rec)
    return p


def seg_of_date(d):
    y = int(str(d)[:4])
    return '2010-2014' if y <= 2014 else ('2015-2018' if y <= 2018 else ('2019-2023' if y <= 2023 else '2024-2026'))


def stable_u64(*parts):
    """稳定 64 位种子：对象语义 ID / 机制 / 路径序号派生（不用 worker 编号或 PID；plan §14.2）。"""
    h = hashlib.sha256('|'.join(str(x) for x in parts).encode()).digest()
    return int.from_bytes(h[:8], 'little')
