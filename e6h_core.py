#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 共享库: 在 E6g 之上加【注册层 + 扩展守卫 + 新派生键】。

为什么要自己一层: `e6g_core.assert_registered_spec` 只放行 U35 ∪ NEW40 的键
(已读源码确认), 而本轮要用 TCV / JUMP / IND_* 三类新派生键; 又按 brief §0.2
硬约束③ `e6g_*.py` 一个字都不能改。所以这里【包】而不是【改】: 新键走 e6h 的
注册表与 build_raw_h, 已有键原样委托回 e6g。

守卫语义 (brief §0.2 ②):
  受保护对象 = NEW40 血缘键 ∪ 新派生键 (TCV/JUMP/IND_*) ∪ 新规则对象
               (SLOT / FOCAL_CONDITION / ADD / SWAP / CONJ / MARGIN / 软降权)
  记录 B 批准【之前】: 只允许 2010-2014 / 2015-2018, label_end <= 2018-12-31
  记录 B 批准【之后】: 只允许清单里冻结的 route_id 进 2019+, 其余照旧
不带受保护血缘、也不是新规则对象的计算一律放行 —— L/T 的旧输入旧规则格因此
可以先跑后段并封存 (brief §6 末条)。
"""
from __future__ import annotations
import os
import json
import hashlib

import numpy as np
import pandas as pd

import e6g_core as G
import e6e_core as K
import e6f_core as F
import comprehensive_factor_diagnosis as C

VERSION = 'E6h-v1'
SEGMENTS = list(G.SEGMENTS)
DERIV_SEGS = ('2010-2014', '2015-2018')
POST_SEGS = ('2019-2023', '2024-2026')
PROTECTED_LABEL_END = '2018-12-31'
MARKET_DATA_END_MAX = '2026-03-27'

E6G_DIR = G.RES
RES = os.environ.get(
    'E6H_RES', '/mnt/sda2/lichenchen/results/20260912_1147_E6h_need_driven_routing')
CODE = '/mnt/sda2/lichenchen/code/project_core'


# ============================================================
# 1. 新派生键的注册表
# ============================================================
DERIVED_SPECS = {
    'TCV_20': dict(family='activity_stability', w=20, minv=10, src=('turnover_rate',),
                   econ='换手变异系数 std20/mean20 (尺度不变的活动不稳定度)'),
    'TCV_60': dict(family='activity_stability', w=60, minv=30, src=('turnover_rate',),
                   econ='换手变异系数 std60/mean60'),
    'JUMP_5': dict(family='overnight_share', w=5, minv=3, src=('open', 'close', 'lclose'),
                   econ='隔夜平方收益占比 sum(on2)/(sum(on2)+sum(in2)), 5 日'),
    'JUMP_20': dict(family='overnight_share', w=20, minv=10, src=('open', 'close', 'lclose'),
                    econ='隔夜平方收益占比, 20 日'),
    'IND_CUR_5': dict(family='industry_peer', w=5, minv=5,
                      src=('close', 'adj_factor', 'industry_zx1'),
                      econ='T 时可见同业(剔自身) 5 日复权端点收益等权均值'),
    'IND_CUR_20': dict(family='industry_peer', w=20, minv=5,
                       src=('close', 'adj_factor', 'industry_zx1'),
                       econ='T 时可见同业(剔自身) 20 日复权端点收益等权均值'),
    'IND_ROLL_5': dict(family='industry_peer', w=5, minv=5,
                       src=('close', 'adj_factor', 'industry_zx1'),
                       econ='按每个历史日 PIT 归属聚合当日同业收益再滚动 5 日'),
    'IND_ROLL_20': dict(family='industry_peer', w=20, minv=5,
                        src=('close', 'adj_factor', 'industry_zx1'),
                        econ='同上, 20 日'),
    'REL_IND_5': dict(family='industry_relative', w=5, minv=5,
                      src=('close', 'adj_factor', 'industry_zx1'),
                      econ='个股 5 日复权端点收益 - IND_CUR_5 (相对同业响应)'),
    'REL_IND_20': dict(family='industry_relative', w=20, minv=5,
                       src=('close', 'adj_factor', 'industry_zx1'),
                       econ='个股 20 日复权端点收益 - IND_CUR_20'),
    'OWN_RET_5': dict(family='own_endpoint', w=5, minv=1, src=('close', 'adj_factor'),
                      econ='个股 5 日复权端点收益 (与 IND_CUR 同口径, 作分解用)'),
    'OWN_RET_20': dict(family='own_endpoint', w=20, minv=1, src=('close', 'adj_factor'),
                       econ='个股 20 日复权端点收益'),
}
DERIVED = frozenset(DERIVED_SPECS)

RULE_OBJECTS = frozenset([
    'SLOT_FALLBACK', 'SLOT_REPLACE', 'FOCAL_REPLACE', 'FOCAL_CONDITION',
    'ADD', 'SWAP', 'CONJ', 'MARGIN', 'SOFT_DEWEIGHT',
])

U35 = frozenset(getattr(G, 'U35', ()))
NEW40 = frozenset(getattr(G, '_NEW40_SET', ()))
U74 = U35 | NEW40
REGISTERED = U74 | DERIVED


class GuardViolationH(Exception):
    pass


def is_protected_key(key):
    """键层保护: 本轮新派生键, 或 NEW40 血缘 (沿用 e6g 的公式别名判定)。"""
    if key in DERIVED:
        return True
    try:
        return bool(G.has_new40_blood(key))
    except Exception:
        return False


def protected_keys(lin_keys):
    return sorted(k for k in lin_keys if is_protected_key(k))


_APPROVAL = {'loaded': False, 'routes': frozenset(), 'path': None, 'sha': None}


def load_approval(path=None):
    """载入记录 B 的后段冻结清单。没有文件 = 未批准, 受保护对象只能跑推导段。"""
    p = path or os.path.join(RES, 'registration', 'record_B_approved.json')
    if not os.path.exists(p):
        _APPROVAL.update(loaded=False, routes=frozenset(), path=p, sha=None)
        return _APPROVAL
    raw = open(p, 'rb').read()
    d = json.loads(raw.decode('utf-8'))
    _APPROVAL.update(loaded=True, path=p, sha=hashlib.sha256(raw).hexdigest(),
                     routes=frozenset(d.get('approved_route_ids', ())))
    return _APPROVAL


_GUARD_LOG = []


def guard_h(lin_keys=(), use_type='trade', segment=None, label_end=None,
            where='', route_id=None, rule_objects=(), strict=True):
    """扩展守卫。lin_keys = 该次计算用到的登记键名 (表达式 DAG 之并)。"""
    pk = protected_keys(lin_keys)
    ro = sorted(set(rule_objects) & RULE_OBJECTS)
    protected = bool(pk or ro)
    reasons = []
    if protected and segment is not None and segment not in DERIV_SEGS:
        ap = _APPROVAL if _APPROVAL['loaded'] else load_approval()
        if not ap['loaded']:
            reasons.append('受保护对象 (键 %s / 规则 %s) 用于段 %s, 但记录 B 未批准'
                           % (pk, ro, segment))
        elif route_id is None or route_id not in ap['routes']:
            reasons.append('受保护对象 (键 %s / 规则 %s) 用于段 %s, route_id=%r 不在记录 B 清单'
                           % (pk, ro, segment, route_id))
    if protected and label_end is not None and str(label_end)[:10] > PROTECTED_LABEL_END:
        if (segment in DERIV_SEGS) or (not _APPROVAL['loaded']):
            reasons.append('label_end=%s > %s' % (label_end, PROTECTED_LABEL_END))
    reason = '; '.join(reasons) if reasons else None
    rec = dict(where=where, use_type=use_type, segment=segment, label_end=str(label_end),
               protected_keys=pk, rule_objects=ro, route_id=route_id,
               passed=reason is None, reason=reason)
    _GUARD_LOG.append(rec)
    if reason is not None and strict:
        raise GuardViolationH('[E6h 守卫] %s @ %s' % (reason, where))
    return True if strict else (reason is None, reason)


def guard_log():
    return list(_GUARD_LOG)


def clear_guard_log():
    del _GUARD_LOG[:]


def assert_registered_h(sp, where=''):
    """任何进入计算的规格必须已登记。挡住"自己写公式造新键绕过守卫"。"""
    if sp.get('role') == 'F':
        k = sp['key'] if sp['key'] in DERIVED else G.resolve_key(sp['key'])
        if k not in REGISTERED:
            raise GuardViolationH('[E6h 守卫] 未登记键 %r @ %s' % (sp['key'], where))
        return True
    return G.assert_registered_spec(sp, where=where)


def specH(key, w=1):
    """任意已登记键 (含新派生键) 的规格。"""
    sp = dict(role='F', key=key, w=int(w), est='MA', eps=0.0, base='diff', adj=False)
    assert_registered_h(sp, where='specH(%s)' % key)
    return sp


# ============================================================
# 2. 新派生键的计算
# ============================================================
def adj_close(data):
    """复权 close, 与 e6f_core 同口径 (cl * C.adjust_factor(data))。"""
    return data['close'] * C.adjust_factor(data)


def tcv(data, w, minv):
    """TCV_w = std_w(turnover)/mean_w(turnover)。ddof 沿 pandas 默认 (=1, 同源 std);
       mean <= 0 或有效数不足 -> NA (不用 epsilon 改变低量排序)。"""
    t = data['turnover_rate']
    sd = t.rolling(w, min_periods=minv).std()
    mu = t.rolling(w, min_periods=minv).mean()
    out = sd / mu.where(mu > 0)
    return out.replace([np.inf, -np.inf], np.nan)


def jump(data, w, minv):
    """JUMP_w = sum(on^2) / (sum(on^2)+sum(in^2)), on=log(open/lclose), in=log(close/open)。
       只计成对有效日; 有效数 < minv 或分母 <= 0 -> NA (全零 -> NA)。"""
    op, cl, lc = data['open'], data['close'], data['lclose']
    on = np.log(op / lc.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
    inn = np.log(cl / op.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
    ok = on.notna() & inn.notna()
    s_on = (on ** 2).where(ok).rolling(w, min_periods=minv).sum()
    s_in = (inn ** 2).where(ok).rolling(w, min_periods=minv).sum()
    n_ok = ok.astype(float).rolling(w, min_periods=1).sum()
    den = s_on + s_in
    out = s_on / den.where(den > 0)
    out = out.where(n_ok >= minv)
    return out.replace([np.inf, -np.inf], np.nan)


def endpoint_ret(data, w):
    """复权端点收益 close_adj[T]/close_adj[T-w] - 1。"""
    cl = adj_close(data)
    return (cl / cl.shift(w) - 1.0).replace([np.inf, -np.inf], np.nan)


def _ind_codes_full(industry, index, columns):
    """(T,N) 行业标签 -> 整数码 (缺行业 = -1)。每行按该日归属, 天然 PIT。"""
    ind = industry.reindex(index=index, columns=columns)
    codes, uniq = pd.factorize(pd.Series(ind.values.ravel()))
    return codes.reshape(ind.shape), list(uniq)


def _peer_mean_excl_self(vals, codes):
    """逐日: 同码组均值剔自身。vals (T,N) float, codes (T,N) int (-1=缺)。
       返回 (peer_mean, n_peer)。单成员 -> NA。"""
    T, N = vals.shape
    peer = np.full((T, N), np.nan)
    npeer = np.zeros((T, N))
    gmax = int(codes.max()) + 1 if codes.size and codes.max() >= 0 else 0
    if gmax == 0:
        return peer, npeer
    okall = np.isfinite(vals)
    for t in range(T):
        ct = codes[t]
        valid = okall[t] & (ct >= 0)
        if not valid.any():
            continue
        idx = np.where(valid)[0]
        cv = ct[idx]
        s = np.bincount(cv, weights=vals[t, idx], minlength=gmax)
        n = np.bincount(cv, minlength=gmax).astype(float)
        others = n[cv] - 1.0
        with np.errstate(invalid='ignore', divide='ignore'):
            peer[t, idx] = (s[cv] - vals[t, idx]) / np.where(others > 0, others, np.nan)
        npeer[t, idx] = others
    return peer, npeer


def ind_peer_current(data, industry, w, thin=5):
    """IND_FEATURE_CURRENT(i,T,w): 用 T 时可见的 PIT 行业归属划同业, 剔自身,
       对同一 w 的复权端点收益等权平均。返回 (peer_mean, n_peer, thin_flag)。
       单成员/无同业 -> NA; 同业 < thin 只标记不禁用 (plan §7.1)。"""
    r = endpoint_ret(data, w)
    codes, _ = _ind_codes_full(industry, r.index, r.columns)
    peer, npeer = _peer_mean_excl_self(r.values, codes)
    pm = pd.DataFrame(peer, index=r.index, columns=r.columns)
    npf = pd.DataFrame(npeer, index=r.index, columns=r.columns)
    return pm, npf, (npf < thin)


def ind_peer_rolling(data, industry, w):
    """IND_FEATURE_ROLLING: 先按每个历史日的 PIT 归属算当日同业等权日收益,
       再滚动 w 日累乘。与 CURRENT 含义不同 (成员随历史日变), 分名并行。"""
    dr = C.vwap_daily_return(data, K.ADJUST)
    codes, _ = _ind_codes_full(industry, dr.index, dr.columns)
    daily, _ = _peer_mean_excl_self(dr.values, codes)
    d = pd.DataFrame(daily, index=dr.index, columns=dr.columns)
    lg = np.log1p(d)
    out = np.expm1(lg.rolling(w, min_periods=max(1, w // 2)).sum())
    return out.replace([np.inf, -np.inf], np.nan)


_DERIV_CACHE_ATTR = '_e6h_derived'


def derived_frame(S, key):
    """按需算一个新派生键, 缓存在段对象上。"""
    st = getattr(S, _DERIV_CACHE_ATTR, None)
    if st is None:
        st = {}
        setattr(S, _DERIV_CACHE_ATTR, st)
    if key in st:
        return st[key]
    spec = DERIVED_SPECS[key]
    w, minv = spec['w'], spec['minv']
    data = S.wdata if getattr(S, 'wdata', None) is not None else S.data
    ind = getattr(S, 'industry', None)
    if key.startswith('TCV_'):
        out = tcv(data, w, minv)
    elif key.startswith('JUMP_'):
        out = jump(data, w, minv)
    elif key.startswith('IND_CUR_'):
        out = ind_peer_current(data, ind, w)[0]
    elif key.startswith('IND_ROLL_'):
        out = ind_peer_rolling(data, ind, w)
    elif key.startswith('OWN_RET_'):
        out = endpoint_ret(data, w)
    elif key.startswith('REL_IND_'):
        out = endpoint_ret(data, w) - ind_peer_current(data, ind, w)[0]
    else:
        raise KeyError('未知派生键 %r' % key)
    st[key] = out.astype(float)
    return st[key]


def build_raw_h(S, sp):
    """原始因子帧。新派生键在这里算, 其余原样委托回 e6g。"""
    assert_registered_h(sp, where='build_raw_h')
    if sp.get('role') == 'F' and sp['key'] in DERIVED:
        raw = derived_frame(S, sp['key'])
        w = int(sp.get('w', 1))
        if w > 1:
            raw = raw.rolling(w, min_periods=F.mp(w)).mean()
        return raw.astype(float)
    return G.build_raw_g(S, sp)


def seg(pname, support='legacy_all', verbose=False):
    S = G.seg(pname, support=support, verbose=verbose)
    setattr(S, _DERIV_CACHE_ATTR, {})
    return S


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def ann(x):
    return G.ann(x)
