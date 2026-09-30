# -*- coding: utf-8 -*-
"""E6l 公共常量与工程工具（brief `exec_briefs/E6l_time_memory_stage.md` v1；plan v1.1 = 结果目录 PLAN_COPY.md）。
只放与经济口径无关的工程件：路径、段、E7 截止守卫、稳定哈希种子、原子写、回执、后段授权门、状态词。
E6j / E6k 的通用工具只 import 复用（不改）；E6k / E6j / E6i / E5a 结果目录与缓存一律只读——E6l 的一切产物只写本轮 RES。"""
import os
import json
import time

import numpy as np
import pandas as pd

import e6j_core as J

VERSION = 'E6l-v1'
CODE = J.CODE
RES = os.environ.get('E6L_RES', '/mnt/sda2/lichenchen/results/20260930_1141_E6l_time_memory_stage')
E6K_RES = '/mnt/sda2/lichenchen/results/20260928_2325_E6k_k_binding_stage'
E6J_RES = '/mnt/sda2/lichenchen/results/20260927_0038_E6j_k_two_dimension_pilot'
E6I_RES = J.E6I_RES
E5A_RES = J.E5A_RES
TRIAL = '/mnt/sda2/lichenchen/tmp/e6l_trial'          # 试跑 / profile 一律写这里（E6k lessons 36）
SEGMENTS = J.SEGMENTS
DERIV_SEGS = J.DERIV_SEGS
POST_SEGS = J.POST_SEGS
MARKET_DATA_END_MAX = J.MARKET_DATA_END_MAX
ANN = J.ANN
LABEL_FIRST_LOOK = 'NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY'
LABEL_SECOND = 'SECOND_EVALUATION_SAME_HISTORY'
# 状态词（brief W12 / 纪律 56：避开 pandas 默认 NA 集合；读写统一 keep_default_na=False）
STATUS_WORDS = ('UNDEFINED', 'NOT_APPLICABLE', 'NOT_AUTHORIZED', 'NOT_REQUIRED', 'STATE_UNKNOWN', 'RANDOM_NOT_SCHEDULED',
                'NO_NEW_CONTENT_TO_PERMUTE', 'MC_UNRESOLVED', 'INSUFFICIENT_REPLICATE_SUPPORT', 'UNMATCHED_STATE_SUPPORT')
FORBIDDEN_STATUS = ('N/A', 'NA', 'nan', 'NaN', 'null', 'NULL', 'None', '#N/A', 'n/a', '<NA>')
if J.RES != E6J_RES:
    raise RuntimeError('e6j_core.RES 被改动（E6J_RES 环境变量？）：E6l 只读 E6j 目录，不得重定向')

# 复用（不改源）
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


def log(msg, logfile=None):
    J.log(msg, logfile)


def P(*parts):
    """结果目录内路径。"""
    return os.path.join(RES, *parts)


def K6(*parts):
    """E6k 结果目录内路径（只读）。"""
    return os.path.join(E6K_RES, *parts)


def rel(p):
    return os.path.relpath(p, RES)


def read_csv_keep(p, **kw):
    """状态词保留字面（纪律 56）：只把空串当缺失。"""
    return pd.read_csv(p, keep_default_na=False, na_values=[''], **kw)


def write_receipt(task_id, outputs, status='SUCCEEDED', **extra):
    """父进程验收产物后写回执（协议 v1.1 ⑤：FAILED 须由同名 _rerun 成功回执覆盖）。只写 E6l RES/task_status。
    回执含每个产物 sha、行数（CSV）与参数（extra）——brief §8 / 附录 D-1。"""
    outs, rows = {}, {}
    for p in outputs:
        if os.path.exists(p):
            outs[rel(p)] = sha_file(p)
            if p.endswith('.csv'):
                with open(p, 'rb') as fh:
                    rows[rel(p)] = max(sum(1 for _ in fh) - 1, 0)
    rec = dict(task_id=task_id, status=status, written_at=time.strftime('%Y-%m-%d %H:%M:%S'), version=VERSION,
               pid=os.getpid(), outputs=outs, csv_rows=rows, **extra)
    p = P('task_status', '%s.receipt.json' % task_id.replace(':', '_').replace('/', '_').replace('|', '__'))
    atomic_write_json(p, rec)
    return p


def env_versions():
    import platform
    import scipy
    out = dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__)
    for m in ('numba', 'statsmodels', 'polars'):
        try:
            out[m] = __import__(m).__version__
        except Exception:                                   # noqa: BLE001
            out[m] = 'NOT_INSTALLED'
    return out


# ---------------------------------------------------------------- 后段授权门（brief W11；plan §13.2；E6k lessons 17：两向实测）
AUTH_PRE = 'record_B_preauthorized_E6l.json'
AUTH_APPROVED = 'record_B_approved_E6l.json'
AUTH_COND = 'record_B_conditions_receipt_E6l.json'
MANIFEST_B = 'B_package_manifest_E6l.json'
MANIFEST_P = 'P_package_manifest_E6l.json'


def post_gate(pname, what=''):
    """新对象在两后段的任何计算（含掩码事实）之前调用。
    方式 B：registration/record_B_preauthorized_E6l.json + 条件回执 all_pass 且冻结清单 sha 未变；
    方式 A：registration/record_B_approved_E6l.json（用户一句话后写）+ 同一条件回执。推导段不经此门。"""
    if pname not in POST_SEGS:
        return True
    rc = P('registration', AUTH_COND)
    pre = P('registration', AUTH_PRE)
    appr = P('registration', AUTH_APPROVED)
    if not (os.path.exists(pre) or os.path.exists(appr)):
        raise RuntimeError('后段守卫（%s）：E6l 后段未授权' % what)
    if not os.path.exists(rc):
        raise RuntimeError('后段守卫（%s）：授权生效条件未核验' % what)
    r = json.load(open(rc, encoding='utf-8'))
    man = P('registration', MANIFEST_B)
    if not (r.get('all_pass') and os.path.exists(man) and r.get('frozen_manifest_sha256') == sha_file(man)):
        raise RuntimeError('后段守卫（%s）：条件未全过或冻结清单 sha 已变' % what)
    return True


def deriv_only(pname, what=''):
    if pname not in DERIV_SEGS:
        raise RuntimeError('%s：本步只允许推导段' % what)


class NpzDict(dict):
    """np.load 的整读版（E6k lessons 9）：每个数组只读一次。"""
    @property
    def files(self):
        return list(self.keys())


def npz(path, keys=None):
    z = np.load(path, allow_pickle=False)
    try:
        return NpzDict({k: z[k] for k in (z.files if keys is None else keys)})
    finally:
        z.close()


def status_scan_values(values):
    """状态词扫描（附录 A6-3）：返回命中禁用状态词的值。"""
    return sorted(set(str(v) for v in values if str(v) in FORBIDDEN_STATUS))


def txt(x):
    """检查表文本：禁用状态词（'nan' / 'None' 等）一律写 UNDEFINED（纪律 56；附录 A6-3）。"""
    s = str(x)
    return 'UNDEFINED' if s in FORBIDDEN_STATUS else s


def _receipt_path(task_id):
    return P('task_status', '%s.receipt.json' % task_id.replace(':', '_').replace('/', '_').replace('|', '__'))


def rerun_chain(base):
    """回执链 base → base_rerun → base_rerun2 …（协议 v1.1 ⑤：FAILED 由后继成功回执覆盖，旧回执不删）。返回已存在的名字列表。"""
    out = []
    for i in range(0, 50):
        nm = base if i == 0 else ('%s_rerun' % base if i == 1 else '%s_rerun%d' % (base, i))
        if os.path.exists(_receipt_path(nm)):
            out.append(nm)
        else:
            break
    return out


def next_rerun(base):
    ch = rerun_chain(base)
    i = len(ch)
    return base if i == 0 else ('%s_rerun' % base if i == 1 else '%s_rerun%d' % (base, i))


def last_rerun(base):
    ch = rerun_chain(base)
    if not ch:
        raise RuntimeError('无回执：%s' % base)
    return ch[-1]
