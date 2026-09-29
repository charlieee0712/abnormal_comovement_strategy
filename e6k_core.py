# -*- coding: utf-8 -*-
"""E6k 公共常量与工程工具（brief `exec_briefs/E6k_k_binding_stage.md` v1；plan v1.1 = 结果目录 PLAN_COPY.md）。
只放与经济口径无关的工程件：路径、段、E7 截止守卫、稳定哈希种子、原子写、回执、后段授权门。
E6j 的通用工具（种子、原子写、sha）只 import 复用（e6j_core 不改）；E6j 结果目录与缓存一律只读——
本模块不改 e6j_core.RES（E6j 的 J 成员缓存 / 交易日历仍从 E6j 目录读），E6k 的一切产物只写本轮 RES。"""
import os
import json
import time

import numpy as np
import pandas as pd

import e6j_core as J

VERSION = 'E6k-v1'
CODE = J.CODE
RES = os.environ.get('E6K_RES', '/mnt/sda2/lichenchen/results/20260928_2325_E6k_k_binding_stage')
E6J_RES = '/mnt/sda2/lichenchen/results/20260927_0038_E6j_k_two_dimension_pilot'
E6I_RES = J.E6I_RES
E5A_RES = J.E5A_RES
TRIAL = '/mnt/sda2/lichenchen/tmp/e6k_trial'          # 试跑 / profile 一律写这里（E6j #74 / lessons 26）
SEGMENTS = J.SEGMENTS
DERIV_SEGS = J.DERIV_SEGS
POST_SEGS = J.POST_SEGS
MARKET_DATA_END_MAX = J.MARKET_DATA_END_MAX
ANN = J.ANN
LABEL_FIRST_LOOK = 'NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY'
if J.RES != E6J_RES:
    raise RuntimeError('e6j_core.RES 被改动（E6J_RES 环境变量？）：E6k 只读 E6j 目录，不得重定向')

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


def rel(p):
    return os.path.relpath(p, RES)


def write_receipt(task_id, outputs, status='SUCCEEDED', **extra):
    """父进程验收产物后写回执（协议 v1.1 ⑤：FAILED 须由同名 _rerun 成功回执覆盖）。只写 E6k RES/task_status。"""
    rec = dict(task_id=task_id, status=status, written_at=time.strftime('%Y-%m-%d %H:%M:%S'), version=VERSION,
               pid=os.getpid(), outputs={rel(p): sha_file(p) for p in outputs if os.path.exists(p)}, **extra)
    p = P('task_status', '%s.receipt.json' % task_id.replace(':', '_').replace('/', '_'))
    atomic_write_json(p, rec)
    return p


def env_versions():
    import platform
    import scipy
    out = dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__)
    try:
        import numba
        out['numba'] = numba.__version__
    except Exception:                                   # noqa: BLE001
        out['numba'] = None
    return out


# ---------------------------------------------------------------- 后段授权门（brief W11；plan §13.2 / §13.3）
def post_gate(pname, what=''):
    """新对象（本轮新算子 / 新登记描述符）在两后段的任何计算（含掩码）之前调用。
    方式 B：registration/record_B_preauthorized_E6k.json + 条件回执 all_pass 且冻结清单 sha 未变；
    方式 A：registration/record_B_approved_E6k.json（用户一句话后写）+ 同一条件回执。
    推导段与 E6j 已暴露对象的历史复现不经此门。"""
    if pname not in POST_SEGS:
        return True
    rc = P('registration', 'record_B_conditions_receipt_E6k.json')
    pre = P('registration', 'record_B_preauthorized_E6k.json')
    appr = P('registration', 'record_B_approved_E6k.json')
    if not (os.path.exists(pre) or os.path.exists(appr)):
        raise RuntimeError('后段守卫（%s）：E6k 后段未授权（方式 A 停等用户）' % what)
    if not os.path.exists(rc):
        raise RuntimeError('后段守卫（%s）：授权生效条件未核验' % what)
    r = json.load(open(rc, encoding='utf-8'))
    man = P('registration', 'B_package_manifest_E6k.json')
    if not (r.get('all_pass') and os.path.exists(man) and r.get('frozen_manifest_sha256') == sha_file(man)):
        raise RuntimeError('后段守卫（%s）：条件未全过或冻结清单 sha 已变' % what)
    return True


def deriv_only(pname, what=''):
    if pname not in DERIV_SEGS:
        raise RuntimeError('%s：本步只允许推导段' % what)


class NpzDict(dict):
    """np.load 的整读版：NpzFile 每次 z[key] 都从磁盘整读该数组（循环里 z[k][i] 会重复读盘）；这里每个数组只读一次。"""
    @property
    def files(self):
        return list(self.keys())


def npz(path):
    z = np.load(path, allow_pickle=False)
    try:
        return NpzDict({k: z[k] for k in z.files})
    finally:
        z.close()
