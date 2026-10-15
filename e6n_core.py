# -*- coding: utf-8 -*-
"""E6n 公共常量与工程工具（brief `exec_briefs/E6n_minute_path_stage.md` v1；plan v1.1 = 结果目录 PLAN_COPY.md）。
只放与经济口径无关的工程件：路径、段、E7 截止守卫、契约版本、缓存命名空间、原子写、回执、脱敏、状态词。
- import 期不读任何数据文件（brief A8 / 纪律 78）；结果目录在调用时从环境变量 E6N_WORK 取。
- 工具函数沿 e6m_core（只 import 不改；e6m_core 再只 import 数据侧闭包 e6j_core）。"""
import os
import re
import json
import time

import numpy as np
import pandas as pd

import e6m_core as M

VERSION = 'E6n-v1.1'
CONTRACT_VERSION = 'E6n-v1.1'
PLAN_SHA256 = 'af5ff33f582dcade7017d5756d3717250a249216e320cbb7313bd79236903d1d'
CODE = M.CODE
SEGMENTS = M.SEGMENTS
DERIV_SEGS = M.DERIV_SEGS
POST_SEGS = M.POST_SEGS
MARKET_DATA_END_MAX = M.MARKET_DATA_END_MAX            # '2026-03-27'：日频与分钟同一截止
MARKET_DATA_END_INT = int(MARKET_DATA_END_MAX.replace('-', ''))
ANN = M.ANN
MACHINE = os.environ.get('E6N_MACHINE', '47')          # 只写别名
LABEL_FIRST_LOOK = M.LABEL_FIRST_LOOK
LABEL_SECOND = M.LABEL_SECOND
STATUS_WORDS = ('UNDEFINED', 'NOT_APPLICABLE', 'NOT_AUTHORIZED', 'NOT_REQUIRED', 'SOURCE_WAIT', 'UNKNOWN', 'NOT_COMPUTABLE',
                'POLICY_UNDECIDABLE_HISTORY', 'MC_LIMIT', 'DOSE_UNRESOLVED', 'NOT_RUN', 'PASS', 'FAIL', 'INFO', 'COMPUTED',
                'NOT_COVERED', 'RANDOM_NOT_SCHEDULED', 'NO_NEW_CONTENT_TO_PERMUTE', 'PRESENT')
FORBIDDEN_STATUS = M.FORBIDDEN_STATUS

import e6j_core as _J
RES_ROOT = os.path.dirname(_J.E6I_RES)                     # results 根（沿 e6j_core 已有常量推出，不另写含目录名的路径字面量）
USER_ROOT = os.path.dirname(RES_ROOT)                       # data / code / results 的共同上级
E6M_WORK = os.path.join(RES_ROOT, '20261005_0556_E6m', 'E6m_stageN_20261005_0556')
DATA_CACHE = os.path.join(USER_ROOT, 'data', 'cache')
DAILY_FULL = os.path.join(DATA_CACHE, 'daily_kline_20100101_20260327.parquet')

assert_end_ok = M.assert_end_ok
assert_index_ok = M.assert_index_ok
canonical_json = M.canonical_json
stable_seed_int = M.stable_seed_int
rng_for = M.rng_for
sha_file = M.sha_file
sha_bytes = M.sha_bytes
atomic_write_bytes = M.atomic_write_bytes
atomic_write_json = M.atomic_write_json
atomic_write_text = M.atomic_write_text
atomic_write_csv = M.atomic_write_csv
atomic_write_npz = M.atomic_write_npz
san = M.san
read_csv_keep = M.read_csv_keep
env_versions = M.env_versions
scan_status_words = M.scan_status_words


def work():
    w = os.environ.get('E6N_WORK', '')
    if not w:
        raise RuntimeError('E6N_WORK 未设：E6n 产物只写本轮结果目录')
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


def cache_namespace(source_version='', data_version='', adapter_version='', support='', init='SEGMENT_RESET_19D_WARMUP'):
    """缓存命名空间（plan §12.3 最终约定；brief W13）：contract_version + plan 字节 sha + source / data / adapter 版本 + 支持集 / 初始化 + 数值环境。
    返回 (目录名, 明细 dict)。目录名含 'E6n-v1.1' 与 plan sha 前 8 位（闭包门 ⑩）。"""
    ev = env_versions()
    det = dict(contract_version=CONTRACT_VERSION, plan_sha256=PLAN_SHA256, source_version=source_version, data_version=data_version,
               adapter_version=adapter_version, support=support, init=init,
               numeric_env=dict(python=ev['python'], numpy=ev['numpy'], pandas=ev['pandas'], scipy=ev['scipy'], numba=ev.get('numba', '')))
    h = sha_bytes(canonical_json(det).encode())[:12]
    return 'cache_%s_plan%s_%s' % (CONTRACT_VERSION, PLAN_SHA256[:8], h), det


def write_receipt(task_id, outputs, status='SUCCEEDED', inputs=(), code=(), **extra):
    """回执（附录 D 固定键）：参数 / 输入 / 输出 sha、CSV 行数、状态、代码 sha、机器别名。FAILED 由同名 _rerun 覆盖。"""
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
               pid=os.getpid(), outputs=outs, csv_rows=rows, inputs=ins, code=cs,
               **json.loads(san(json.dumps(extra, ensure_ascii=False, default=str))))
    p = P('task_status', '%s.receipt.json' % re.sub(r'[:/|]', '_', task_id))
    atomic_write_json(p, rec)
    return p


def to_status(df, cols=None, word='UNDEFINED'):
    """写出前把 None / NaN 文本格映射为状态词（经验 N2）；数值列保留 NaN（CSV 写空串，读时 keep_default_na=False 下为空）。"""
    df = df.copy()
    for c in (cols or [c for c in df.columns if df[c].dtype == object]):
        df[c] = df[c].map(lambda v: word if (v is None or (isinstance(v, float) and not np.isfinite(v))) else v)
    return df
