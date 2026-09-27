# -*- coding: utf-8 -*-
"""E6j 公共常量与工具（brief v1.2 `exec_briefs/E6j_k_two_dimension_pilot.md`；plan v1.1 = 结果目录 PLAN_COPY.md）。
只放与经济口径无关的工程工具：路径、段、E7 截止守卫、稳定哈希种子、原子写、回执。
四地基与 e6e–e6i 脚本只读；本模块不 import 任何 e6i_* 模块。"""
import os
import sys
import json
import time
import hashlib

import numpy as np
import pandas as pd

VERSION = 'E6j-v1'
CODE = '/mnt/sda2/lichenchen/code/project_core'
RES = os.environ.get('E6J_RES', '/mnt/sda2/lichenchen/results/20260927_0038_E6j_k_two_dimension_pilot')
E6I_RES = '/mnt/sda2/lichenchen/results/20260923_0254_E6i_measurement_need_fit'
E5A_RES = '/mnt/sda2/lichenchen/results/20260903_1214_delivery_pools_v2'
SEGMENTS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')
DERIV_SEGS = SEGMENTS[:2]
POST_SEGS = SEGMENTS[2:]
MARKET_DATA_END_MAX = '2026-03-27'          # E7 守卫：任何真实行情不得晚于此日
ANN = 252 * 100.0
if CODE not in sys.path:
    sys.path.insert(0, CODE)


# ---------------------------------------------------------------- E7 守卫
def assert_end_ok(end, where=''):
    """数据读取入口的截止日检查：end 必须 ≤ 2026-03-27（接受 'YYYYMMDD' / 'YYYY-MM-DD' / Timestamp）。"""
    e = pd.Timestamp(str(end))
    if e > pd.Timestamp(MARKET_DATA_END_MAX):
        raise RuntimeError('E7 守卫：%s 的截止日 %s 晚于 %s' % (where, e.date(), MARKET_DATA_END_MAX))
    return e


def assert_index_ok(idx, where=''):
    """已加载数据的日期索引检查：最大日期 ≤ 2026-03-27。"""
    if len(idx):
        mx = pd.Timestamp(str(max(idx)))
        if mx > pd.Timestamp(MARKET_DATA_END_MAX):
            raise RuntimeError('E7 守卫：%s 含 %s 之后的日期 %s' % (where, MARKET_DATA_END_MAX, mx.date()))


# ---------------------------------------------------------------- 稳定哈希种子（协议 v1.1 ⑪；plan §8.2）
def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def stable_seed_int(*key):
    """blake2b(canonical_json(key)) → 128 位整数；与进程、PYTHONHASHSEED、调度顺序无关。不得用内置 hash()。"""
    return int.from_bytes(hashlib.blake2b(canonical_json(list(key)).encode('ascii'), digest_size=16).digest(), 'big')


def rng_for(*key):
    """由稳定键派生 numpy Generator（PCG64 + SeedSequence）；键写进账本元数据。"""
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(stable_seed_int(*key))))


# ---------------------------------------------------------------- 文件工具
def sha_file(p, chunk=1 << 22):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(chunk), b''):
            h.update(b)
    return h.hexdigest()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def atomic_write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp.%d' % os.getpid()
    with open(tmp, 'wb') as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return sha_bytes(data)


def atomic_write_json(path, obj):
    return atomic_write_bytes(path, json.dumps(obj, ensure_ascii=False, indent=1, default=str).encode('utf-8'))


def atomic_write_text(path, text):
    return atomic_write_bytes(path, text.encode('utf-8'))


def atomic_write_csv(path, df, **kw):
    return atomic_write_bytes(path, df.to_csv(index=False, **kw).encode('utf-8'))


def atomic_write_npz(path, **arrays):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp.%d.npz' % os.getpid()
    np.savez(tmp, **arrays)
    os.replace(tmp, path)
    return sha_file(path)


def write_receipt(task_id, outputs, status='SUCCEEDED', **extra):
    """父进程验收产物后写 SUCCESS 回执：输出路径、sha、行数等；FAILED 须由同名 _rerun 成功回执覆盖（协议 v1.1 ⑤）。"""
    rec = dict(task_id=task_id, status=status, written_at=time.strftime('%Y-%m-%d %H:%M:%S'), version=VERSION,
               outputs={os.path.relpath(p, RES): sha_file(p) for p in outputs if os.path.exists(p)}, **extra)
    p = os.path.join(RES, 'task_status', '%s.receipt.json' % task_id.replace(':', '_').replace('/', '_'))
    atomic_write_json(p, rec)
    return p


def log(msg, logfile=None):
    line = '[%s] %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg)
    print(line, flush=True)
    if logfile:
        with open(logfile, 'a', encoding='utf-8') as fh:
            fh.write(line + '\n')


def env_versions():
    import platform
    return dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                bitgenerator='PCG64', seed_derivation='blake2b-128(canonical_json(key)) -> SeedSequence')
