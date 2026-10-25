# -*- coding: utf-8 -*-
"""E6r 公共常量与工程工具（brief `E6r_entry_quality_roles.md` d6cdc0b3；附录 5dc01f4e；plan v1.1 c89305fb；合同脚本 7aa0338f）。
只放与经济口径无关的工程件：路径、段、E7 截止守卫、缓存命名空间、原子写、回执、状态词、身份（canon / logical_id / exec_id / exec_hash）。
- 本轮产物只写 E6R_WORK（环境变量）；E6i / E6n / E6o / E6p / E6q 结果目录只读（复用 E6q 引擎、面板 mmap、源形成名单、触发机器，brief §1.1 / §7）。
- canon 沿 plan 附录 C：indent = 2、sort_keys、ensure_ascii = False、allow_nan = False、末尾 LF（与 E6q 的紧凑分隔不同）。
- read_csv：空单元格保持空串（E6q lesson：共享读表把空串读成 NaN，下游按空串写的判断对 NaN 恒真）。
- 临时文件：TMPDIR / tempfile 指向 E6R_WORK/tmp/tmpdir（47 根分区为他人占用）。"""
import os
import re
import json
import time
import hashlib
import tempfile

import numpy as np
import pandas as pd

import e6q_core as Q6

VERSION = 'E6r-v1.1'
PLAN_SHA256 = 'c89305fb648fda9c8ca6dd4c4c36e34747b0953bc3983c25732aad17b7117812'
PLAN_BODY_SHA256 = 'fe51dcbbefc069559a2b54a2cdae196efdbca4fcf8f3ec126387699e089468c5'
CONTRACT_SHA256 = '7aa0338f88e28d8dcce3d042e2bef4bda01ce39e6efd2354f63c490ebabff682'
BRIEF_SHA256 = 'd6cdc0b35f54af06ad729ca2289f3636d68b86d3c3be8f57b160013c4d69fdcd'
APPENDIX_SHA256 = '5dc01f4e9c917e81dc20cdb59788c9692f40f6712553aacbd3346c9a7e53ece8'
D_SCRIPT_SHA256 = '51256b059cdc5b73f28818d5c3ab0c3c6f547d012ae0c27fa148fe0e0b79ee11'
START_MSG_SHA256 = '16792e544fbd8c0b0d1e019c8b8063bba42983569633825724a459ad10b5ae04'
PROPOSAL_SHA256 = 'e3114b07dde9dd065ce9b9675bd065674d85987eca0717245e6689894bfd8261'
E6Q_REVIEW_SHA256 = 'c7ff02a5cfbbbf118e50fe260a43e2d4aaf33b82a29281b5841e0c33f82324bf'
CACHE_TAG = 'E6r-v1.1-c89305fb'
SPEC_SHA = {'registry.json': 'fe68664db1ee40eb36971edced1f59472f011d5bb6d901d42a54d353e8caacd3',
            'comparisons.json': '0fc99c5e18cd5c4ce25f53a4a813340e9a2c4b17a977e7b9af1d5727f32d32f3',
            'compound.json': '8e41125ada7ed61cbad0d5893c9fba56bf7b4b7d4089824ddc054cb3ee8f2317',
            'random_refs.json': 'ee9a1a2ed695bdc8694297a097b9bad03297620a8c69b0a389fef0ecfb8c675f',
            'feedback_refs.json': '7b0198628460517ee7d005e46ff39c464ca99489b201fa204216199f880046a4',
            'primary.json': '3c42a68698a5c9058bf057bcfdd28cfb5edebc029a110a11ed0c3b9bfd64df00',
            'claims.json': '045e161b19346e1b952de8c8e3321dddc24da6ee0781347063faac5ed9d64bb5',
            'cc_statement_carry.csv': '91d9db75fed2c86bc748fa4ff4991fbde01fcd3870a72b04d40a1a8a7bf2d6c3',
            'test_results.json': 'e8454502f43ba0107bd2b74a2e315717f77d1e8b44a38865bcf970c2004b156f',
            'counts.json': 'a741250f81be0bced81db48010ef0cd2d9224512963fb3a643d0956405450b7a',
            'manifest.json': '39e1eda2c8bdc9fcbf101bcb540c9b3bf2292f57a6d6fa2ac93e437c397facee'}
COUNTS = dict(E=7, Q=18, accounts=350, comparisons=2988, compound=20, deterministic_refs=94, feasible=341, feedback_comparisons=1822,
              feedback_paths=202, ideal=9, primary=9, random_refs=1408, snapshot_refs=359, stochastic_refs=1314)
CUTOFF = '2026-03-27'
DERIV_END = '2018-12-31'
SEGS = Q6.SEGS
DERIV_SEGS = Q6.DERIV_SEGS
POST_SEGS = Q6.POST_SEGS
SEG6 = SEGS + ('FULL', 'G4')
FORMS = ('A4b_CVRv5', 'A4b', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
MAIN_FORM = 'A4b_CVRv5'
MEMS = ('NONE', 'HG10', 'LAG1_10')
TRIGGERS = ('NONE', 'T1a', 'T1b_LEVEL', 'T8', 'UNION_T1a_T8', 'UNION_LEVEL_T8', 'T1A_TIME_LEVEL_RANK')
EXIT_OPS = ('NATIVE', 'EXIT_GATE_LIQ_1E8', 'EXIT_GATE_LIQ_5E8', 'EXIT_HALF_REARM', 'GATE_REARM_1E8', 'GATE_REARM_5E8')
CORE_SCHEMES = ('FLAT', 'GATE_STATE', 'TILT_CVR_L050', 'TILT_CVR_L025', 'DROP_T3', 'TILT_H', 'UNIFORM_CAP15', 'TILT_SIZE_L050', 'GATE_TILT')
TILT_SCHEMES = ('TILT_CVR_L050', 'TILT_CVR_L025', 'TILT_SIZE_L050', 'GATE_TILT', 'TILT_CVR5_L050', 'TILT_CVR_CELL_L050')
SCHEMES = CORE_SCHEMES + ('TILT_CVR5_L050', 'TILT_CVR_CELL_L050')
RESEARCH_CAP_SCHEMES = TILT_SCHEMES + ('UNIFORM_CAP15',)
HS = (5, 20, 30, 40)
SCENARIOS = ('FEASIBLE_DAILY', 'IDEALIZED_SOURCE_FILL')
FEAS, IDEAL = SCENARIOS
ANN_PP = 252.0 * 100.0
FEE_RATE = Q6.FEE_RATE
STOCK_CAP = Q6.STOCK_CAP
RESEARCH_CAP = 0.015
IND_DEV = Q6.IND_DEV
V0 = Q6.V0
P0_PIVOT = Q6.P0_PIVOT
P_STAR = 0.02
THETA = 0.5
QUEUE_DAYS = 5
A_MAIN = 100000000
A_SUB = (50000000, 500000000)
A_GRID = (50000000, 100000000, 200000000, 500000000, 1000000000)
KAPPAS = (0.5, 1.0)
EXPONENTS = (0.5, 0.7, 1.0)
MCSE_TARGET = 0.01
NOT_COMPARABLE_UNMATCHED = 0.25
MACHINE = '47'
EXEC_SUFFIX = ('FULLHIST', 'CASH_V0', 'FIXED_PATH_V1', 'E6R_V11')
SEED_PROTOCOL = 'E6R_BLOCK5_STABLE_SECURITY_V11'
E_DECLARED_AT = '2026-10-23T23:38:25+00:00'
FRONTIER_LID = 'E6R-ad902abcc9cb9534'
FRONTIER_E6Q_LID = 'E6Q-9f826422e6d4c39c'
AUTHORIZED_BY = '用户 2026-10-24 消息（决策端转交）'
AUTHORIZED_AT = '2026-10-24T12:18:00+08:00'                  # 开工消息与合同件转交时间（决策端；本机文件时间 10-24 00:18 UTC−4）
AUTHORIZATIONS = dict(main_A_cny=100000000, sub_A_cny=[50000000, 500000000], research_metric='EXCESS_SCALED_BENCHMARK',
                      product_metric='TOTAL_RETURN_AND_MAX_DRAWDOWN', frontier_anchor_logical_id=FRONTIER_LID, mainline='entry_quality_roles',
                      deployment_authorized=False, e7='HOLD', r5_single_stock_research_parameter=0.015)
PAYLOAD_KEYS = ('version', 'form', 'memory', 'funding_H', 'trigger', 'weight_scheme', 'exit_op', 'scenario', 'alpha', 'cutoff', 'start_state',
                'capital_route', 'funding_lag', 'reentry', 'measurement_clock', 'weight_contract', 'cap_profile', 'cap_single_parameter',
                'lambda_weight', 'H_by_tertile', 'cost_profile', 'deployment_authorized')
STATUS_WORDS = ('COMPUTED', 'UNKNOWN', 'NOT_APPLICABLE', 'MC_LIMIT', 'SOURCE_BINDING_PENDING', 'RIGHT_CENSORED', 'NOT_RUN', 'NO_RANDOM_BY_SCOPE',
                'CONTROL_NOT_COMPARABLE', 'LIQ_DATA_FALLBACK', 'SCENARIO_NOT_CALIBRATED', 'RECONCILED', 'NOT_POSITIVE_DENOMINATOR', 'LOW_INTERVENTION',
                'STRUCTURAL_DEGENERATE', 'PROVED_NO_MATCH', 'ALGORITHM_LIMIT', 'FEASIBLE', 'BLOCKED', 'BOUND', 'PASS', 'DIFFERS', 'INFO', 'OUT_OF_GRID',
                'NUMERICAL_RANGE', 'NOT_EVALUABLE', 'IDENTITY_NO_NEW_TEST', 'NEW_COORDINATE', 'ALIAS_OF_SOURCE', 'RESERVED')

RES_ROOT = Q6.RES_ROOT
E6I_DIR = os.path.join(RES_ROOT, '20260923_0254_E6i_measurement_need_fit')
E6P_DIR = Q6.E6P_DIR
E6Q_DIR = os.path.join(RES_ROOT, '20261023_0040_E6q_sell_reinvest_split')
E6Q_CACHE = os.path.join(E6Q_DIR, 'cache_E6q-v1.1_plan86c246dd_acce4d9165c8')
E6Q_HANDOFF = os.path.join(E6Q_DIR, 'handoff', 'E6q_20261023_1032')
RO_DIRS = (Q6.E6N_DIR, Q6.E6O_DIR, E6P_DIR, E6Q_DIR, E6I_DIR)

assert_end_ok = Q6.assert_end_ok
assert_index_ok = Q6.assert_index_ok
sha_file = Q6.sha_file
sha_bytes = Q6.sha_bytes
san = Q6.san
seg_of_date = Q6.seg_of_date
age_bucket = Q6.age_bucket


def canon(x):
    """plan 附录 C `canon` 逐字同式。"""
    return (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def digest(x):
    return hashlib.sha256(canon(x)).hexdigest()


def stable_key(*x):
    return hashlib.sha256(canon(list(x))).hexdigest()


def logical_id_of(payload):
    return 'E6R-' + digest(payload)[:16]


def exec_id(lid, scenario):
    return '|'.join((lid, scenario) + EXEC_SUFFIX)


def exec_hash(eid, source_fingerprint):
    return hashlib.sha256((eid + '|' + source_fingerprint).encode()).hexdigest()[:16]


def path_seed(owner_key, mechanism, path_id):
    """E6R_BLOCK5_STABLE_SECURITY_V11：owner 语义坐标 / 机制 / path_id 的稳定种子（63 位）；五日块与证券键在引擎内混入（hash_u(seed, (d+1)//5, seckey)）。"""
    return int(stable_key(SEED_PROTOCOL, owner_key, mechanism, int(path_id))[:15], 16)


def work():
    w = os.environ.get('E6R_WORK', '')
    if not w:
        raise RuntimeError('E6R_WORK 未设：E6r 产物只写本轮结果目录')
    a = os.path.abspath(w)
    for ro in RO_DIRS:
        if a.startswith(os.path.abspath(ro)):
            raise RuntimeError('E6R_WORK 不得指向 E6i / E6n / E6o / E6p / E6q 目录')
    return w


def _tmp_setup():
    w = os.environ.get('E6R_WORK', '')
    if w:
        t = os.path.join(w, 'tmp', 'tmpdir')
        os.makedirs(t, exist_ok=True)
        os.environ['TMPDIR'] = t
        tempfile.tempdir = t


_tmp_setup()


def P(*parts):
    return os.path.join(work(), *parts)


def E6Q(*parts):
    return os.path.join(E6Q_DIR, *parts)


def rel(p):
    return os.path.relpath(p, work())


def cache_dir():
    """缓存命名空间：目录名含 'E6r-v1.1' 与 plan sha 前 8 位 c89305fb（闭包门 ㉑）；v1.0 缓存不复用；E6q / E6p / E6i 缓存只读。"""
    ev = Q6.P6.N.env_versions()
    det = dict(version=VERSION, plan_sha256=PLAN_SHA256, contract_sha256=CONTRACT_SHA256, cache_tag=CACHE_TAG,
               numeric_env=dict(python=ev['python'], numpy=ev['numpy'], pandas=ev['pandas'], numba=ev.get('numba', '')))
    h = sha_bytes(json.dumps(det, sort_keys=True).encode())[:12]
    d = P('cache', 'cache_%s_plan%s_%s' % (VERSION, PLAN_SHA256[:8], h))
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, 'namespace.json')
    if not os.path.exists(p):
        atomic_write_json(p, det)
    return d


def log(msg):
    print(san('[%s] %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg)), flush=True)


def _guard_path(p):
    a = os.path.abspath(p)
    for ro in RO_DIRS:
        if a.startswith(os.path.abspath(ro)):
            raise RuntimeError('拒绝写入只读目录')
    if not a.startswith(os.path.abspath(work())):
        raise RuntimeError('拒绝写入本轮结果目录之外')


def atomic_write_bytes(p, b):
    _guard_path(p)
    return Q6.P6.N.atomic_write_bytes(p, b)


def atomic_write_json(p, obj):
    _guard_path(p)
    return Q6.P6.N.atomic_write_json(p, obj)


def atomic_write_text(p, s):
    _guard_path(p)
    return Q6.P6.N.atomic_write_text(p, s)


def fmt_df(df):
    """机器表写出口径：布尔 → true / false；NaN / None → 空；其余原样（B 节通用规则）。"""
    out = df.copy()
    for c in out.columns:
        col = out[c]
        if col.dtype == bool:
            out[c] = np.where(col, 'true', 'false')
        elif col.dtype == object:
            out[c] = [('true' if v else 'false') if isinstance(v, (bool, np.bool_)) else ('' if v is None or (isinstance(v, float) and v != v) else v)
                      for v in col]
    return out


def atomic_write_csv(p, df, fmt=True):
    _guard_path(p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + '.tmp%d' % os.getpid()
    (fmt_df(df) if fmt else df).to_csv(tmp, index=False, lineterminator='\n', na_rep='')
    os.replace(tmp, p)
    return p


def atomic_write_csv_gz(p, df, fmt=True):
    """大表无损 gzip（mtime = 0 可复现）；D 脚本两种都读。"""
    import gzip
    _guard_path(p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + '.tmp%d' % os.getpid()
    data = (fmt_df(df) if fmt else df).to_csv(index=False, lineterminator='\n', na_rep='').encode()
    with open(tmp, 'wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', compresslevel=6, mtime=0) as gz:
            gz.write(data)
    os.replace(tmp, p)
    return p


def atomic_write_npz(p, **arrs):
    _guard_path(p)
    return Q6.P6.N.atomic_write_npz(p, **arrs)


def atomic_write_npz_c(p, **arrs):
    """压缩 npz（随机路径 A2 末状态等；np.savez_compressed 写临时文件后替换）。"""
    _guard_path(p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + '.tmp%d.npz' % os.getpid()
    np.savez_compressed(tmp, **arrs)
    os.replace(tmp, p)
    return p


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
    """空单元格保持空串（dtype=str 时）；数值列由调用方显式转换。"""
    kw.setdefault('dtype', str)
    return pd.read_csv(p, keep_default_na=False, **kw)


def num(s):
    """空串 → NaN 的显式数值转换。"""
    return pd.to_numeric(pd.Series(s).replace('', np.nan), errors='coerce').to_numpy(float)


def segs_of_dates(dates):
    return np.array([seg_of_date(d) for d in dates])
