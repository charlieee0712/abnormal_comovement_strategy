# -*- coding: utf-8 -*-
"""E6m 公共常量与工程工具（brief `exec_briefs/E6m_access_form_stage.md` v1；plan v1.1 = 工作目录 PLAN_COPY.md）。
只放与经济口径无关的工程件：路径、段、E7 截止守卫、稳定种子、原子写、回执、脱敏、状态词。
- import 期不读任何数据文件（brief A8 / 纪律 78）；工作目录在调用时从环境变量 E6M_WORK 取。
- 只 import 数据侧闭包 e6j_core（不经 e6e_core，brief W15）。"""
import os
import re
import json
import time
import platform

import numpy as np
import pandas as pd

import e6j_core as J

VERSION = 'E6m-v1'
CODE = J.CODE
SEGMENTS = J.SEGMENTS
DERIV_SEGS = J.DERIV_SEGS
POST_SEGS = J.POST_SEGS
MARKET_DATA_END_MAX = J.MARKET_DATA_END_MAX
ANN = J.ANN
MACHINE = os.environ.get('E6M_MACHINE', 'autodl-factor')           # 只写别名
STAGE = os.environ.get('E6M_STAGE', 'N')
RUNS = os.environ.get('E6M_RUNS', os.path.expanduser('~/autodl-tmp/factor_runs/resonance'))   # handoff / replica 的上级目录（缺省 = 云机；47 由运行环境设到本轮结果目录）
SEALED = os.environ.get('E6M_SEALED', os.path.expanduser('~/autodl-tmp/sealed_after_20260327'))  # 云机封存目录；47 无此目录（E7 靠代码守卫，S15 照实报）
LABEL_FIRST_LOOK = 'NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY'
LABEL_SECOND = 'SECOND_EVALUATION_SAME_HISTORY'
# 状态词（避开 pandas 默认 NA 集合；读写 keep_default_na=False）
STATUS_WORDS = ('UNDEFINED', 'NOT_APPLICABLE', 'NOT_AUTHORIZED', 'NOT_REQUIRED', 'SOURCE_WAIT', 'ANCHOR_PENDING', 'UNKNOWN',
                'STATE_UNKNOWN', 'RANDOM_NOT_SCHEDULED', 'NO_NEW_CONTENT_TO_PERMUTE', 'PRESENT', 'NOT_RUN', 'PASS', 'FAIL', 'INFO')
FORBIDDEN_STATUS = ('N/A', 'NA', 'nan', 'NaN', 'null', 'NULL', 'None', '#N/A', 'n/a', '<NA>')

assert_end_ok = J.assert_end_ok
assert_index_ok = J.assert_index_ok
canonical_json = J.canonical_json
stable_seed_int = J.stable_seed_int
rng_for = J.rng_for
sha_file = J.sha_file
sha_bytes = J.sha_bytes
atomic_write_bytes = J.atomic_write_bytes
atomic_write_json = J.atomic_write_json
atomic_write_text = J.atomic_write_text
atomic_write_csv = J.atomic_write_csv
atomic_write_npz = J.atomic_write_npz


def work():
    w = os.environ.get('E6M_WORK', '')
    if not w:
        raise RuntimeError('E6M_WORK 未设：E6m 产物只写本轮工作目录')
    return w


def P(*parts):
    return os.path.join(work(), *parts)


def rel(p):
    return os.path.relpath(p, work())


def log(msg, logfile=None):
    line = san('[%s] %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg))
    print(line, flush=True)
    if logfile:
        with open(logfile, 'a', encoding='utf-8') as fh:
            fh.write(line + '\n')


# ---------------------------------------------------------------- 脱敏（写出层统一；名字在调用时取，不写进源码）
def _names():
    parts = os.path.realpath(CODE).split(os.sep)
    udir = parts[parts.index('sda2') + 1] if 'sda2' in parts else ''
    accts = [d for d in os.listdir('/mnt/big/base') if d != 'public'] if os.path.isdir('/mnt/big/base') else []
    return udir, accts


def san(s):
    s = str(s)
    udir, accts = _names()
    if udir:
        s = s.replace(os.sep + udir + os.sep, os.sep + '<用户目录>' + os.sep)
    for a in accts:
        s = s.replace('/base/' + a + '/', '/base/<账号>/')
    home = os.path.expanduser('~')
    return s.replace(home + os.sep, '~' + os.sep)


def read_csv_keep(p, **kw):
    """状态词保留字面：只把空串当缺失。"""
    return pd.read_csv(p, keep_default_na=False, na_values=[''], **kw)


def env_versions():
    import scipy
    out = dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__)
    for m in ('numba', 'statsmodels', 'pyarrow', 'sklearn', 'polars', 'threadpoolctl'):
        try:
            out[m] = __import__(m).__version__
        except Exception:                                   # noqa: BLE001
            out[m] = 'NOT_INSTALLED'
    out['blas_env'] = {k: os.environ.get(k, '') for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS',
                                                          'NUMBA_NUM_THREADS', 'NUMBA_CACHE_DIR')}
    return out


def write_receipt(task_id, outputs, status='SUCCEEDED', inputs=(), code=(), **extra):
    """回执（附录 D-1）：参数 / 输入 / 输出 sha、CSV 行数、状态、代码 sha、机器别名、阶段。FAILED 由同名 _rerun 覆盖。"""
    outs, rows, ins, cs = {}, {}, {}, {}
    for p in outputs:
        if os.path.exists(p):
            outs[san(rel(p))] = sha_file(p)
            if p.endswith('.csv'):
                with open(p, 'rb') as fh:
                    rows[san(rel(p))] = max(sum(1 for _ in fh) - 1, 0)
    for p in inputs:
        if os.path.exists(p):
            ins[san(p)] = sha_file(p)
    for p in code:
        if os.path.exists(p):
            cs[os.path.basename(p)] = sha_file(p)
    rec = dict(task_id=task_id, status=status, written_at=time.strftime('%Y-%m-%d %H:%M:%S'), version=VERSION, machine=MACHINE,
               stage=STAGE, pid=os.getpid(), outputs=outs, csv_rows=rows, inputs=ins, code=cs,
               **json.loads(san(json.dumps(extra, ensure_ascii=False, default=str))))
    p = P('task_status', '%s.receipt.json' % re.sub(r'[:/|]', '_', task_id))
    atomic_write_json(p, rec)
    return p


def scan_status_words(df):
    """表内状态词扫描：返回命中禁用词的 (列, 值) 清单。"""
    hits = []
    for c in df.columns:
        if df[c].dtype == object:
            v = set(df[c].astype(str)) & set(FORBIDDEN_STATUS)
            hits += [(c, x) for x in sorted(v)]
    return hits
