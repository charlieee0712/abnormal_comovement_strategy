# -*- coding: utf-8 -*-
"""E6q 公共常量与工程工具（brief `E6q_sell_reinvest_split.md` 655d9e9e；附录 7997d462；plan v1.1 86c246dd；合同脚本 2ad9d86e）。
只放与经济口径无关的工程件：路径、段、E7 截止守卫、缓存命名空间、原子写、回执、状态词、身份（logical_id / exec_id / exec_hash）。
- 本轮产物只写 E6Q_WORK（环境变量）；E6n / E6o / E6p 结果目录只读（复用 E6p 引擎、面板内存映射、源形成名单、触发机器，brief §1.1 / §7）。
- 工具函数沿 e6p_core / e6n_core（只 import 不改）。"""
import os
import re
import json
import time
import hashlib

import numpy as np
import pandas as pd

import e6p_core as P6

VERSION = 'E6q-v1.1'
PLAN_SHA256 = '86c246ddac463e519b620bd9046604a70dcb510663df1c0e387324937c117853'
CONTRACT_SHA256 = '2ad9d86ea0f78a771ceb7c89fcc7115ad8d4d75237c9e764239d52e637e6edf6'
BRIEF_SHA256 = '655d9e9edc6b7b2998fdf9ad77ddae0b17dff3b3ae62a5262edfbc987d0d0fe4'
APPENDIX_SHA256 = '7997d462dc476f38eda8af903e85b43a651ded406cd1a0cd8cd948dfc7ec165a'
D_SCRIPT_SHA256 = 'd64c1009cf3f749d40818a810ef5a87fa11e49837d74cde6361f7677d8808be5'
PROPOSAL_SHA256 = 'ece038ea8427d5e3'
CACHE_TAG = 'E6q-v1.1-86c246dd'
JSON_SHA = {'registry.json': '58dff4fce4c5b7d13e771d8b26e6a4eeb6ae95d7863cf1c02b9c30bb2573c747',
            'comparisons.json': '528112f820f04e640629c1a83d8d6aec2adb2d856ebcd6ecdc13fdaf9ced68d6',
            'compound.json': '9e7884592e039634a587d45f2166b355f3b39420f0172d173752c644cf4289e8',
            'random_refs.json': 'cd481c6a20b343666d2bd56145b74d1c6b5f8c569ea92faac8ed2c91d1d5445b',
            'feedback_refs.json': 'f61b4009eea97dcab2d1c53ca36a874d5416bc1fc7d740b98df2fd22afa919b4',
            'primary.json': 'f6c7e0e04cc628204499de5dec6ebb74f35e3f84894b78151be90951a2e20005',
            'claims.json': '641187b468b2bf2061b3b8b5565de293a09c9392b30bd404fe7c785102293b8f'}
CUTOFF = '2026-03-27'
SEGS = P6.SEGS
DERIV_SEGS = P6.DERIV_SEGS
POST_SEGS = P6.POST_SEGS
SEG6 = SEGS + ('FULL', 'G4')
FORMS = P6.FORMS
MAIN_FORM = 'A4b_CVRv5'
MEMS = ('NONE', 'HG10', 'LAG1_10')
HS = (5, 20, 30)
CORE_ARMS = ('NATIVE', 'REINVEST_NEW', 'REINVEST_LIQ_1E8', 'REINVEST_LIQ_5E8', 'EXIT_GATE_LIQ_1E8', 'EXIT_GATE_LIQ_5E8', 'EXIT_HALF')
REF_ARMS = ('CASH_REMAIN', 'RECYCLE_HALF')
ARMS = CORE_ARMS + ('EXIT_HALF_REARM', 'EXIT_HALF_RECYCLE_HALF') + REF_ARMS
TRIGGERS = ('NONE', 'T1a', 'T1b_LEVEL', 'T8', 'UNION_T1a_T8')
SCENARIOS = ('FEASIBLE_DAILY', 'IDEALIZED_SOURCE_FILL')
GROUPS = ('MAIN', 'UNION', 'ANCHOR_OR_H5_BRIDGE', 'HALF_INTERACTION', 'HALF_STATE_BRIDGE', 'ROBUSTNESS', 'ROBUSTNESS_H5', 'IDEAL')
ANN_PP = 252.0 * 100.0
FEE_RATE = P6.FEE_RATE
STOCK_CAP = P6.STOCK_CAP
IND_DEV = P6.IND_DEV
V0 = P6.V0
P0_PIVOT = P6.P0_PIVOT
ETA_HALF = 0.5
P_STAR = 0.02
THETA = 0.5
QUEUE_DAYS = 5
A_MAIN = 100000000
A_SUB = (50000000, 500000000)
A_GRID = (50000000, 100000000, 200000000, 500000000, 1000000000)
KAPPAS = (0.5, 1.0)
KAPPA_LOW = 0.3
EXPONENTS = (0.5, 0.7, 1.0)
DENSITY_A = (100000000, 500000000)
DENSITY_EXP = (0.5, 1.0)
AGE_BUCKETS = P6.AGE_BUCKETS
NOT_COMPARABLE_UNMATCHED = 0.25
INTENSITY_BAND = (0.9, 1.1)
MACHINE = '47'
SUPPORT = 'FULLHIST'
START_STATE = 'CASH_V0'
COST_PROFILE = 'FIXED_PATH_V1'
POLICY_VERSION = 'E6Q_V11'
FRONTIER_LID = 'E6Q-9f826422e6d4c39c'
AUTHORIZED_BY = '用户 2026-10-22 消息（决策端转交）'
AUTHORIZATIONS = dict(main_A_cny=100000000, sub_A_cny=[50000000, 500000000], research_metric='EXCESS_SCALED_BENCHMARK',
                      product_metric='TOTAL_RETURN_AND_MAX_DRAWDOWN', frontier_anchor_logical_id=FRONTIER_LID, mainline='sell_reinvest_split',
                      deployment_authorized=False, e7='HOLD')
PAYLOAD_KEYS = ('version', 'form', 'memory', 'H', 'trigger', 'arm', 'A_ref', 'scenario', 'alpha', 'initial_state', 'cutoff', 'cap_profile',
                'funding_lag', 'maturity', 'reentry', 'execution', 'support', 'p_star', 'fraction', 'queue_days', 'exit_fraction',
                'reinvest_eta', 'cap_kind', 'firsthit_clock', 'cash_contract')
INT_KEYS = ('H', 'funding_lag', 'queue_days', 'A_ref')
FLOAT_KEYS = ('alpha', 'p_star', 'fraction', 'exit_fraction', 'reinvest_eta')
STATUS_WORDS = ('COMPUTED', 'UNKNOWN', 'NOT_APPLICABLE', 'UNMATCHED', 'MC_LIMIT', 'SOURCE_BINDING_PENDING', 'POLICY_MAPPING_UNRESOLVED', 'RIGHT_CENSORED',
                'NOT_RUN', 'NO_RANDOM_BY_SCOPE', 'NO_ACTION_OPPORTUNITY', 'CONTROL_NOT_COMPARABLE', 'LIQ_DATA_FALLBACK', 'LOCAL_ORDER_COST_ONLY',
                'SCENARIO_NOT_CALIBRATED', 'UNDECIDABLE_RECONCILIATION', 'RECONCILED', 'INSTRUMENT_LIMITED', 'NOT_POSITIVE_DENOMINATOR',
                'LOW_INTERVENTION', 'IDENTITY_TARGET_CONTROL', 'PROVED_NO_MATCH', 'ALGORITHM_LIMIT', 'FEASIBLE', 'BLOCKED', 'BOUND', 'PASS',
                'DIFFERS', 'INFO')

RES_ROOT = P6.RES_ROOT
E6N_DIR = P6.E6N_DIR
E6O_DIR = P6.E6O_DIR
E6P_DIR = os.path.join(RES_ROOT, '20261020_0905_E6p_state_dependent_holding')
E6P_CACHE = os.path.join(E6P_DIR, 'cache_E6p-v1.1_planefd382ee_e02fb043b0c6')
RO_DIRS = (E6N_DIR, E6O_DIR, E6P_DIR)

assert_end_ok = P6.assert_end_ok
assert_index_ok = P6.assert_index_ok
sha_file = P6.sha_file
sha_bytes = P6.sha_bytes
san = P6.san
seg_of_date = P6.seg_of_date
stable_u64 = P6.stable_u64
age_bucket = P6.age_bucket


def canonical(x):
    """与 plan 附录 C `canonical` 逐字同式：ensure_ascii=False、无空格分隔、allow_nan=False、末尾换行，按 UTF-8 编码。"""
    return (json.dumps(x, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n').encode()


def digest(x):
    return hashlib.sha256(canonical(x)).hexdigest()


def payload_of(row):
    """registry 行（str / 数）→ plan 附录 C 的 25 字段 payload（整数键 int、小数键 float、空 = None、其余 str）。"""
    d = {}
    for k in PAYLOAD_KEYS:
        v = row.get(k)
        if v is None or (isinstance(v, str) and v == '') or (isinstance(v, float) and v != v):
            d[k] = None
        elif k in INT_KEYS:
            d[k] = int(float(v))
        elif k in FLOAT_KEYS:
            d[k] = float(v)
        else:
            d[k] = str(v)
    return d


def logical_id(row):
    return 'E6Q-' + digest(payload_of(row))[:16]


def exec_id(lid, scenario):
    return '|'.join([lid, scenario, SUPPORT, START_STATE, COST_PROFILE, POLICY_VERSION])


def exec_hash(eid, trigger_formula_hash, source_ref_contract, source_hash):
    return hashlib.sha256((eid + trigger_formula_hash + source_ref_contract + source_hash).encode()).hexdigest()[:16]


def work():
    w = os.environ.get('E6Q_WORK', '')
    if not w:
        raise RuntimeError('E6Q_WORK 未设：E6q 产物只写本轮结果目录')
    a = os.path.abspath(w)
    for ro in RO_DIRS:
        if a.startswith(os.path.abspath(ro)):
            raise RuntimeError('E6Q_WORK 不得指向 E6n / E6o / E6p 目录')
    return w


def P(*parts):
    return os.path.join(work(), *parts)


def E6P(*parts):
    return os.path.join(E6P_DIR, *parts)


def rel(p):
    return os.path.relpath(p, work())


def cache_dir():
    """缓存命名空间：目录名含 'E6q-v1.1' 与 plan sha 前 8 位 86c246dd（闭包门 ⑮）；E6q v1.0 缓存不复用；E6p 缓存只读硬链。"""
    ev = P6.N.env_versions()
    det = dict(version=VERSION, plan_sha256=PLAN_SHA256, contract_sha256=CONTRACT_SHA256, cache_tag=CACHE_TAG,
               numeric_env=dict(python=ev['python'], numpy=ev['numpy'], pandas=ev['pandas'], numba=ev.get('numba', '')))
    h = sha_bytes(json.dumps(det, sort_keys=True).encode())[:12]
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
    for ro in RO_DIRS:
        if a.startswith(os.path.abspath(ro)):
            raise RuntimeError('拒绝写入只读目录')
    if not a.startswith(os.path.abspath(work())):
        raise RuntimeError('拒绝写入本轮结果目录之外')


def atomic_write_bytes(p, b):
    _guard_path(p)
    return P6.N.atomic_write_bytes(p, b)


def atomic_write_json(p, obj):
    _guard_path(p)
    return P6.N.atomic_write_json(p, obj)


def atomic_write_text(p, s):
    _guard_path(p)
    return P6.N.atomic_write_text(p, s)


def atomic_write_csv(p, df):
    _guard_path(p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + '.tmp%d' % os.getpid()
    df.to_csv(tmp, index=False, lineterminator='\n', na_rep='')
    os.replace(tmp, p)
    return p


def atomic_write_npz(p, **arrs):
    _guard_path(p)
    return P6.N.atomic_write_npz(p, **arrs)


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


def read_csv(p, **kw):
    return pd.read_csv(p, keep_default_na=False, na_values=[''], **kw)
