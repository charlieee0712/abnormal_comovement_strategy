# -*- coding: utf-8 -*-
"""E6p 公共常量与工程工具（brief `E6p_state_dependent_holding.md` b1b78440；plan v1.1 efd382ee；spec 5c7742ad）。
只放与经济口径无关的工程件：路径、段、E7 截止守卫、缓存命名空间、原子写、回执、状态词、身份（logical_id / exec_id / exec_hash）。
- 本轮产物只写 E6P_WORK（环境变量）；E6o / E6n 结果目录只读（复用 E6o 引擎、面板内存映射、源形成名单、触发机器，brief §1.1 / §7）。
- 工具函数沿 e6o_core / e6n_core（只 import 不改）。"""
import os
import re
import json
import time
import hashlib

import numpy as np
import pandas as pd

VERSION = 'E6p-v1.1'
PLAN_SHA256 = 'efd382ee81e27fb8b06a57c0eb59b61f5e97ec8080ed42b9cfe2ad1a8f99570f'
SPEC_SHA256 = '5c7742adc8752f75410551e24258c573069aafe4f3d62ba45b15076ff4f219ba'
BRIEF_SHA256 = 'b1b78440035d68d00ee70a082cef69a362c36b6a399702750a6182955b38b8fd'
APPENDIX_SHA256 = '7e7277c997b8e4a0ae4f073ceb365bb2fb614b93868c9922b6b0e8bfeb8d9e97'
D_SCRIPT_SHA256 = '4274d7fee453070f9b730d8dbd8d678b16c95cb2e99f947b988af1957231c65f'
CACHE_TAG = 'E6p-v1.1-efd382ee'
CUTOFF = '2026-03-27'
SEGS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')
DERIV_SEGS = ('2010-2014', '2015-2018')
POST_SEGS = ('2019-2023', '2024-2026')
FORMS = ('A4b_CVRv5', 'A4b', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
MAIN_FORM = 'A4b_CVRv5'
MEMS = ('NONE', 'HG10', 'LAG1_10')
MEMKEY = {'NONE': 'NONE|a0.25|Q0', 'HG10': 'HG10|a0.25|Q0', 'LAG1_10': 'LAG1_10|a0.25|Q0'}
HS = (5, 10, 15, 20, 30, 40)
DEPLOYS = ('NATIVE', 'D80', 'D95', 'CASH_REMAIN', 'RECYCLE_HALF', 'RECYCLE_COST0', 'RECYCLE_COSTNET', 'MIRROR_LAG1', 'SOURCE_ROLLING')
TRIGGERS = ('NONE', 'T1a', 'T1b_LEVEL', 'T1b_EDGE', 'T3b15', 'UNION', 'T8_LIMIT_CLOSE')
ANN_PP = 252.0 * 100.0
FEE_RATE = 4e-4             # 单边每单位净成交名义 4bp（沿 E6o C9）
STOCK_CAP = 0.01
IND_DEV = 0.03
V0 = 1e8                    # 账户起始资本（内部单位 = 人民币，起始 1 亿；成本曲线按 A / V0 换算）
P0_PIVOT = 0.01             # 参与率锚（plan §9.2）
ROUTE_A_REF, ROUTE_KAPPA, ROUTE_DELTA = 1e8, 0.5, 0.5   # 再投资成本路由常数（plan §6.6；不是用户资金）
ETA_HALF = 0.5
TARGETS = {'D80': 0.80, 'D95': 0.95}
A_GRID = (50000000, 100000000, 200000000, 500000000, 1000000000)
KAPPAS = (0.5, 1.0)
EXPONENTS = (0.5, 0.7)
AGE_BUCKETS = ((1, 1), (2, 2), (3, 5), (6, 10), (11, 20), (21, 10 ** 6))   # V2 匹配层（执行日批次日龄 e − e0）
NOT_COMPARABLE_UNMATCHED = 0.25   # CONTROL_NOT_COMPARABLE 标签规则（A1 冻结；FULL 未匹配金额份额 > .25）
MACHINE = '47'
SUPPORT = 'FULLHIST'
COST_PROFILE = 'FIXED_PATH_V1'
POLICY_VERSION = 'E6P_V11'
STATUS_WORDS = ('COMPUTED', 'UNKNOWN', 'NOT_APPLICABLE', 'UNMATCHED', 'MC_LIMIT', 'SOURCE_BINDING_PENDING', 'POLICY_MAPPING_UNRESOLVED',
                'RIGHT_CENSORED', 'NOT_RUN', 'NO_RANDOM_BY_SCOPE', 'NO_ACTION_OPPORTUNITY', 'CONTROL_NOT_COMPARABLE', 'KNOWN_DEGENERATE_FALLBACK',
                'LOCAL_ORDER_COST_ONLY', 'SCENARIO_NOT_CALIBRATED', 'BLOCKED', 'BOUND', 'PASS', 'DIFFERS', 'INFO')

_HERE = os.path.dirname(os.path.abspath(__file__))
import e6j_core as _J  # noqa: E402  （results 根由既有常量推出，不另写含目录名的字面量）
RES_ROOT = os.path.dirname(_J.E6I_RES)
E6N_DIR = os.path.join(RES_ROOT, '20261015_0827_E6n_minute_path_stage')
E6O_DIR = os.path.join(RES_ROOT, '20261017_2138_E6o_account_exit_stage')
os.environ.setdefault('E6N_WORK', E6N_DIR)
import e6n_core as N  # noqa: E402

assert_end_ok = N.assert_end_ok
assert_index_ok = N.assert_index_ok
sha_file = N.sha_file
sha_bytes = N.sha_bytes
san = N.san


def canonical(x):
    """与 plan 附录 C `canonical` 逐字同式（logical_id 重算用）。"""
    return json.dumps(x, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False)


def digest(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()


def work():
    w = os.environ.get('E6P_WORK', '')
    if not w:
        raise RuntimeError('E6P_WORK 未设：E6p 产物只写本轮结果目录')
    a = os.path.abspath(w)
    for ro in (E6N_DIR, E6O_DIR):
        if a.startswith(os.path.abspath(ro)):
            raise RuntimeError('E6P_WORK 不得指向 E6n / E6o 目录')
    return w


def P(*parts):
    return os.path.join(work(), *parts)


def E6N(*parts):
    return os.path.join(E6N_DIR, *parts)


def E6O(*parts):
    return os.path.join(E6O_DIR, *parts)


def e6o_cache():
    ds = [d for d in os.listdir(E6O_DIR) if d.startswith('cache_E6o-v1.1_plance9e98c2_')]
    if len(ds) != 1:
        raise RuntimeError('E6o 缓存目录不唯一：%d' % len(ds))
    return os.path.join(E6O_DIR, ds[0])


def rel(p):
    return os.path.relpath(p, work())


def cache_dir():
    """缓存命名空间：目录名含 'E6p-v1.1' 与 plan sha 前 8 位 efd382ee（闭包门 ⑮）；E6p v1.0 缓存不复用。"""
    ev = N.env_versions()
    det = dict(version=VERSION, plan_sha256=PLAN_SHA256, spec_sha256=SPEC_SHA256, cache_tag=CACHE_TAG,
               numeric_env=dict(python=ev['python'], numpy=ev['numpy'], pandas=ev['pandas'], numba=ev.get('numba', '')))
    h = sha_bytes(canonical(det).encode())[:12]
    d = P('cache_%s_plan%s_%s' % (VERSION, PLAN_SHA256[:8], h))
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, 'namespace.json')
    if not os.path.exists(p):
        atomic_write_json(p, det)
    return d


def log(msg):
    line = san('[%s] %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg))
    print(line, flush=True)


def _guard_path(p):
    a = os.path.abspath(p)
    for ro in (E6N_DIR, E6O_DIR):
        if a.startswith(os.path.abspath(ro)):
            raise RuntimeError('拒绝写入只读目录')
    if not a.startswith(os.path.abspath(work())):
        raise RuntimeError('拒绝写入本轮结果目录之外')


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


def atomic_save_npy(p, a):
    _guard_path(p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + '.tmp%d.npy' % os.getpid()
    np.save(tmp, np.ascontiguousarray(a))
    os.replace(tmp, p)
    return p


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
    """稳定 64 位种子：逻辑 ID / 机制 / 路径序号派生（brief §7；不用 worker 编号或 PID）。"""
    h = hashlib.sha256('|'.join(str(x) for x in parts).encode()).digest()
    return int.from_bytes(h[:8], 'little')


def spec_logical_id(spec):
    """plan 附录 C Spec.id：'E6P-' + sha256(canonical(11 字段))[:24]（字段名 / 类型照原 dataclass）。"""
    keys = ('form', 'memory', 'H', 'deploy', 'trigger', 'renew', 'cap', 'role', 'owner', 'mirror_H', 'version')
    d = {k: spec[k] for k in keys}
    for k in ('H', 'renew', 'mirror_H'):
        d[k] = int(d[k])
    return 'E6P-' + digest(d)[:24]


def exec_id(logical_id, profile, start_state='CASH_V0'):
    return '|'.join([logical_id, profile, SUPPORT, start_state, COST_PROFILE, POLICY_VERSION])


def exec_hash(eid, trigger_formula_hash, source_ref_contract, source_hash):
    return hashlib.sha256((eid + trigger_formula_hash + source_ref_contract + source_hash).encode()).hexdigest()[:16]


def age_bucket(age):
    for k, (lo, hi) in enumerate(AGE_BUCKETS):
        if lo <= age <= hi:
            return k
    return -1
