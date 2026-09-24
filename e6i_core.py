#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 共享库: 常量 / 血缘守卫 (E6i 自己的授权命名空间) / 带血缘的缓存 / 段与预热数据 / 原子写。

为什么要自己一层 (brief §0.2 ② + 硬约束③):
  * e6h_core 的守卫只认 E6h 的 record_B_approved.json, 那份文件已放行两条 E6h route_id 进 2019+;
    E6i 的新测量 / 新算子 / M1 / M2 / C1 后段产物要用【自己的】授权文件与 approval_id 命名空间,
    绝不能借 H.load_approval() 的单例放行。
  * e6e / e6f / e6g / e6h 一个字都不改 —— 这里只【包】不【改】。

守卫语义:
  受保护 = 本轮全部新测量 (catalog 里 source_class != LEGACY_SOURCE 的成员)
         ∪ 新算子 (SLOT / ADD_SCORE / VETO_NEW / SOFT / SWAP / FOCAL_NEW / RL / T_PAIR / FOURARM)
         ∪ 组合程序 (M1 / M2) ∪ C1 后段产物 (sealed)
  记录 B 批准前: 只允许 2010-2014 / 2015-2018, label_end <= 2018-12-31; 缓存读取同样过守卫。
  记录 B 批准后: 只放行 E6i 授权文件里冻结的 package / member。
  旧输入旧规则 (源母体、源键、源引擎) 一律放行 —— 它们早已公开。
"""
from __future__ import annotations
import os
import io
import json
import time
import hashlib
import tempfile

import numpy as np
import pandas as pd

import e6h_core as H
import e6g_core as G
import e6f_core as F
import e6e_core as K

VERSION = 'E6i-v1'
CODE = '/mnt/sda2/lichenchen/code/project_core'
RES = os.environ.get('E6I_RES',
                     '/mnt/sda2/lichenchen/results/20260923_0254_E6i_measurement_need_fit')
E6H_RES = '/mnt/sda2/lichenchen/results/20260912_1147_E6h_need_driven_routing'
SEGMENTS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')
DERIV_SEGS = ('2010-2014', '2015-2018')
POST_SEGS = ('2019-2023', '2024-2026')
PROTECTED_LABEL_END = '2018-12-31'
MARKET_DATA_END_MAX = '2026-03-27'
MOTHERS = ('R1', 'R2', 'A06', 'A08')
ANCHOR_MOTHERS = ('A03', 'T25')            # 展示锚 (plan §3.5); Blend3 由 G.blend3_weights 另算
COST, COST_HI = 8.0, 12.0
ANN = 252 * 100.0

RULE_OBJECTS_I = frozenset([
    'SLOT', 'SLOT_FULL_REPLACE', 'SLOT_FALLBACK_REPLACE', 'COMMON_SUPPORT',
    'ADD_SCORE', 'VETO_NEW', 'SOFT', 'SWAP', 'FOCAL_NEW', 'RL', 'T_PAIR', 'FOURARM',
    'M1', 'M2', 'C1_POST',
])


# ============================================================
# 1. 授权 (E6i 自己的命名空间)
# ============================================================
APPROVAL_FILE = os.path.join(RES, 'registration', 'record_B_approved_E6i.json')
_APPROVAL_I = {'loaded': False, 'packages': frozenset(), 'members': frozenset(),
               'rule_objects': frozenset(), 'descriptors': frozenset(), 'path': None, 'sha': None,
               'approval_id': None}


def load_approval_i(path=None):
    """载入 E6i 的记录 B。没有文件 = 未批准。只认 E6i 自己的文件, 从不读 E6h 的。
    Stage 3 技术修复: 另载入 approved_descriptors (批准清单内的 A0 描述符 id), 供守卫按描述符核对。"""
    p = path or APPROVAL_FILE
    if not os.path.exists(p):
        _APPROVAL_I.update(loaded=False, packages=frozenset(), members=frozenset(),
                           rule_objects=frozenset(), descriptors=frozenset(), path=p, sha=None,
                           approval_id=None)
        return _APPROVAL_I
    raw = open(p, 'rb').read()
    d = json.loads(raw.decode('utf-8'))
    if d.get('status') != 'APPROVED' or not str(d.get('approval_id', '')).startswith('E6I-B-'):
        raise RuntimeError('E6i 授权文件格式不对 (status/approval_id): %s' % p)
    _APPROVAL_I.update(
        loaded=True, path=p, sha=hashlib.sha256(raw).hexdigest(), approval_id=d['approval_id'],
        packages=frozenset(d.get('approved_packages', ())),
        members=frozenset(d.get('approved_members', ())),
        rule_objects=frozenset(d.get('approved_rule_objects', ())),
        descriptors=frozenset(d.get('approved_descriptors', ())))
    return _APPROVAL_I


_WHERE_PREFIXES = ('zmap:', 'swapdist:', 'c2:')


def _approved_descriptor(where):
    """runner 以 A0 描述符 id 作 where (Z-MAP / swapdist / C2 带前缀)。在批准清单内 -> 返回该 id, 否则 None。"""
    w = str(where)
    D = _APPROVAL_I['descriptors']
    if w in D:
        return w
    for p_ in _WHERE_PREFIXES:
        if w.startswith(p_) and w[len(p_):] in D:
            return w[len(p_):]
    return None


def post_allowed(segment):
    """后段 runner 的段闸: 只有 E6i 记录 B 已批准时才允许 2019-2023 / 2024-2026 (逐对象仍由 guard_i 核对)。"""
    return segment in POST_SEGS and bool(load_approval_i()['loaded'])


class GuardViolationI(Exception):
    pass


_GUARD_LOG = []
_PROTECTED_MEMBERS = set()        # 由 e6i_features.register_catalog() 填


def set_protected_members(ids):
    _PROTECTED_MEMBERS.clear()
    _PROTECTED_MEMBERS.update(ids)


def is_protected_member(mid):
    return mid in _PROTECTED_MEMBERS


def guard_i(members=(), rule_objects=(), segment=None, label_end=None, use='compute',
            where='', package_id=None, strict=True, sealed=False):
    """E6i 守卫。members = 本次计算用到的 E6i 成员 id (含派生依赖); rule_objects = 新算子/程序名。
       use in {'compute', 'read', 'label', 'trade'}。返回 (ok, why)。strict 时越界抛错。
       sealed=True 只对【旧输入】的 C1/C2 后段格有意义 (brief §7 末条): 允许先算并封存,
       读取 (use='read') 在记录 B 前一律拒; 新测量血缘的一切不因 sealed 放行。"""
    pm = sorted(m for m in members if is_protected_member(m))
    ro = sorted(set(rule_objects) & RULE_OBJECTS_I)
    protected = bool(pm or ro)
    ok, why = True, 'unprotected'
    if protected:
        seg_ok = segment in DERIV_SEGS
        lab_ok = (label_end is None) or (str(label_end)[:10] <= PROTECTED_LABEL_END)
        if seg_ok and lab_ok:
            ok, why = True, 'derivation'
        elif (not pm) and set(ro) == {'C1_POST'} and use == 'compute' and sealed:
            ok, why = True, 'sealed_old_input_compute'
        else:
            if not _APPROVAL_I['loaded']:
                ok, why = False, 'protected object outside derivation before record B'
            else:
                pk_ok = package_id is not None and package_id in _APPROVAL_I['packages']
                if package_id is None:
                    # Stage 3 技术修复 (记录 B 之后; brief §7 "后段技术修复保持经济定义并记 hash"):
                    # runner 不传包名 -> 描述符 (where) 在批准清单内即视为其包已批准;
                    # 纯测量的算 / 读 (无规则对象) 只核对成员是否在批准清单内。
                    pk_ok = (_approved_descriptor(where) is not None) or \
                        (not ro and use in ('compute', 'read'))
                mem_ok = all(m in _APPROVAL_I['members'] for m in pm)
                ro_ok = all(r in _APPROVAL_I['rule_objects'] for r in ro)
                ok = bool(pk_ok and mem_ok and ro_ok)
                why = ('approved:%s' % _APPROVAL_I['approval_id']) if ok else \
                    'not in E6i record B (package=%s members_ok=%s rules_ok=%s)' % (
                        package_id, mem_ok, ro_ok)
    _GUARD_LOG.append(dict(t=time.strftime('%H:%M:%S'), where=where, use=use, segment=segment,
                           label_end=label_end, n_protected=len(pm), rule_objects=ro,
                           package_id=package_id, ok=ok, why=why))
    if not ok and strict:
        raise GuardViolationI('%s | where=%s use=%s segment=%s members=%s rules=%s'
                              % (why, where, use, segment, pm[:5], ro))
    return ok, why


def guard_log():
    return list(_GUARD_LOG)


def assert_matured(label_end_dates, decision_date, where=''):
    """M2 / 任何学习程序: 训练样本的标签结束日必须早于决策日 (plan §7.3 purge 按标签结束时间)。"""
    le = pd.to_datetime(pd.Series(label_end_dates))
    dd = pd.Timestamp(decision_date)
    bad = int((le >= dd).sum())
    if bad:
        raise GuardViolationI('未成熟标签进入训练: %d 条标签结束日 >= 决策日 %s (%s)'
                              % (bad, dd.date(), where))
    return True


def assert_old_component_unchanged(old_ref, old_in_control, where=''):
    """随机对照只许打乱新分量 / 改变的名额 (plan §6.3, W19): 旧分量必须逐位不变。"""
    a = np.asarray(old_ref, np.float64)
    b = np.asarray(old_in_control, np.float64)
    if a.shape != b.shape or not np.array_equal(np.nan_to_num(a, nan=-9e99),
                                                np.nan_to_num(b, nan=-9e99)):
        raise GuardViolationI('随机对照改动了旧分量 (%s)' % where)
    return True


SEALED = os.path.join(RES, 'sealed')


def sealed_write_csv(segment, name, df, meta=None):
    """旧输入的 C1/C2 后段格: 可先算并封存 (只写不读), receipt 记 hash。"""
    guard_i([], ['C1_POST'], segment=segment, use='compute', sealed=True,
            where='sealed_write:%s' % name)
    p = os.path.join(SEALED, segment, name + '.csv')
    atomic_write_csv(p, df)
    atomic_write_json(p + '.receipt.json', dict(segment=segment, name=name, rows=len(df),
                                                sha256=sha_file(p), sealed=True,
                                                written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
                                                meta=meta or {}))
    return p


def sealed_read_csv(segment, name, package_id=None):
    guard_i([], ['C1_POST'], segment=segment, use='read', package_id=package_id,
            where='sealed_read:%s' % name)
    p = os.path.join(SEALED, segment, name + '.csv')
    return pd.read_csv(p)


# ============================================================
# 2. 原子写 / 指纹
# ============================================================
def sha_file(p):
    return H.sha_file(p)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def atomic_write_bytes(path, data):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.tmp_')
    with os.fdopen(fd, 'wb') as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def atomic_write_json(path, obj):
    atomic_write_bytes(path, json.dumps(obj, indent=1, ensure_ascii=False,
                                        default=str).encode('utf-8'))


def atomic_write_csv(path, df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    atomic_write_bytes(path, buf.getvalue().encode('utf-8'))


def write_receipt(path, task_id, outputs, status='SUCCEEDED', **extra):
    """完成 = 退出前原子写 receipt (产物 hash + 行数); 不只靠 _DONE。"""
    outs = []
    for p in outputs:
        rec = dict(path=os.path.relpath(p, RES), bytes=os.path.getsize(p), sha256=sha_file(p))
        if p.endswith('.csv'):
            try:
                rec['rows'] = int(sum(1 for _ in open(p, 'rb')) - 1)
            except Exception:
                rec['rows'] = None
        outs.append(rec)
    atomic_write_json(path, dict(task_id=task_id, status=status, written_at=time.strftime(
        '%Y-%m-%d %H:%M:%S'), version=VERSION, outputs=outs, **extra))


# ============================================================
# 3. 带血缘的测量缓存 (读写都过守卫)
# ============================================================
CACHE = os.path.join(RES, 'cache')


def _cache_paths(segment, member_id, policy):
    base = os.path.join(CACHE, segment, '%s__%s' % (member_id, policy))
    return base + '.npy', base + '.json'


def save_member(S, member_id, policy, arr, meta):
    """arr: (T, Nc) float64 (源值, 未中性化)。meta 必含 source_lineage / formula_version。"""
    assert arr.dtype == np.float64 and arr.shape == (S.T, S.Nc), (arr.dtype, arr.shape)
    guard_i([member_id], segment=S.name, use='compute', where='save_member')
    pn, pj = _cache_paths(S.name, member_id, policy)
    os.makedirs(os.path.dirname(pn), exist_ok=True)
    buf = io.BytesIO()
    np.save(buf, arr, allow_pickle=False)
    atomic_write_bytes(pn, buf.getvalue())
    fin = np.isfinite(arr)
    meta = dict(meta)
    meta.update(member_id=member_id, policy=policy, segment=S.name, shape=list(arr.shape),
                max_feature_date=str(S.dates[-1].date()), label_end_date=None,
                exposure_status=('derivation' if S.name in DERIV_SEGS else 'post'),
                approval_id=_APPROVAL_I['approval_id'], sha256=sha_file(pn),
                finite_frac_pool0=float(fin[S.p0c].mean()) if S.p0c.any() else None,
                written_at=time.strftime('%Y-%m-%d %H:%M:%S'))
    atomic_write_json(pj, meta)
    return pn


def load_member(segment, member_id, policy, where='load_member'):
    guard_i([member_id], segment=segment, use='read', where=where)
    pn, pj = _cache_paths(segment, member_id, policy)
    if not (os.path.exists(pn) and os.path.exists(pj)):
        return None, None
    meta = json.load(open(pj))
    if meta.get('sha256') != sha_file(pn):
        raise RuntimeError('缓存 hash 与 sidecar 不符: %s' % pn)
    return np.load(pn, allow_pickle=False), meta


def has_member(segment, member_id, policy):
    pn, pj = _cache_paths(segment, member_id, policy)
    return os.path.exists(pn) and os.path.exists(pj)


# ============================================================
# 4. 段: 母体用 legacy (逐位复现 E6h), 新测量用预热数据
# ============================================================
def seg_i(pname, verbose=False, warm=True, warm_days=260):
    """S = E6h 同款段 (legacy_all, 母体逐位复现); 另挂 S.wdata_i = 段首前 warm_days 自然日起的
       允许历史 (E7 守卫仍在 F.guarded_load 入口)。新测量一律在 S.wdata_i 上算再取 pool0 网格。"""
    S = H.seg(pname, verbose=verbose)
    ps, pe = F.PERIODS[pname]
    if warm:
        ws, tag = F.warm_start(pname, calendar_days=warm_days)
        S.warm_tag_i, S.warm_start_i = tag, ws
        S.wdata_i = F.guarded_load(ws, pe) if tag in ('warmed', 'clipped_to_source_start') \
            else S.data
    else:
        S.warm_tag_i, S.warm_start_i, S.wdata_i = 'none', ps, S.data
    S._i = {}
    return S


def to_grid(S, df):
    """任意 (日期 x 全市场) 帧 -> (T, Nc) float64, 按 ticker 标签对齐 (绝不按位置)。"""
    x = df.reindex(index=S.pool0.index, columns=S.pool0.columns)
    return np.ascontiguousarray(x.values[:, S.ccols], dtype=np.float64)


def ann(x):
    return float(np.nanmean(x)) * ANN


def sp_ann(x):
    """同有效日的年化; 全 NaN 返回 NaN 而不是警告。"""
    x = np.asarray(x, float)
    return float(np.nanmean(x)) * ANN if np.isfinite(x).any() else float('nan')


# ============================================================
# 5. 进程启动即载入 E6i 记录 B (Stage 3 技术修复): 无文件 = 未批准 (推导段行为不变);
#    文件存在但格式不对 -> 抛错 (fail closed)。
# ============================================================
load_approval_i()
