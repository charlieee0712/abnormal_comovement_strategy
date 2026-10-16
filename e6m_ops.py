# -*- coding: utf-8 -*-
"""E6m 新算子（plan §5 / §6；brief §1.3 契约 3–4；参考实现 = e6m_spec_tests.py 的 band_parts / band_gate / band_native_metric /
priority_pass / hard_conj / exact_swap / copy_gate_coordinates / memory_reference / qpair）。逐日、纯函数、不读任何文件。

统一坐标（brief §1.3-2）：
  E      当日技术合法域（源门的有限评分集合），长度 N；
  order  冻结源总序：按 (s0, 源平局位次) 升序（源 = pd.Series.rank(method='first') 的出现顺序）；源 U = order[:n]；
  s0     源门评分（A4b / Munion = K 第一关坏度；Mmean = 综合分），大值更差；
  kQ     源中性化 Q 坏度 ∈ [0,1]，大值更差；缺失 = NaN（缺失者原门身份固定，不当好也不当坏）；
  ids    稳定 ticker（唯一，否则报错）。
全部函数返回长度 N 的布尔名单（E 内位置）；不改 n（BAND / PRIORITY）或只删不补（HARD）。"""
from fractions import Fraction

import numpy as np

EPS_Q = 1e-4


# ------------------------------------------------------------------ 基础
def check_ids(ids):
    ids = np.asarray(ids, str)
    if ids.ndim != 1 or len(set(ids)) != len(ids):
        raise ValueError('ticker 必须唯一且一维')
    return ids


def total_order(s0, tie):
    """冻结源总序：(s0, tie) 升序；s0 必须有限（E 的定义）。"""
    s0 = np.asarray(s0, float)
    if not np.isfinite(s0).all():
        raise ValueError('合法域评分必须有限')
    return np.lexsort((np.asarray(tie), s0))


def ranks_of(order):
    r = np.empty(len(order), int)
    r[order] = np.arange(len(order))
    return r


def source_mask(order, n):
    if not 0 <= n <= len(order):
        raise ValueError('名额越界')
    m = np.zeros(len(order), bool)
    m[order[:n]] = True
    return m


def band_width_count(w, N, n):
    """m = min(floor(w·N) 十进制有理, n, N − n)。"""
    if not 0 <= float(w) <= 1:
        raise ValueError('带宽越界')
    f = Fraction(str(w))
    return int(min((f.numerator * N) // f.denominator, n, N - n))


def band_parts(order, n, w):
    N = len(order)
    j = band_width_count(w, N, n)
    return order[:n - j], order[n - j:n + j], order[n + j:], j


def check_threshold(c):
    c = float(c)
    if not np.isfinite(c) or not 0 <= c <= 1:
        raise ValueError('资格阈值 c 必须是 [0,1] 有限值（0–100 混用拒绝）')
    return c


# ------------------------------------------------------------------ BAND_Q / BAND_BLEND（含 PROTECTED_LAG10 = SLOT_MAPPED）
def band(order, s0, kq, n, w, inside=None, prev_natural=None, b=0.0, loading=None, ids=None):
    """B 内有限 Q 者按 inside 优先序（BAND_Q：kQ；BAND_BLEND：native_s(α)；COPY：copy 坐标）重取原名额。
    prev_natural 给出时 = PROTECTED_LAG10：先把 B 内可动股票的 s0 评分槽按无记忆新优先序重分配（保留多重集），
    再减 b·loading·1(昨日同算子无 bonus 自然 U)，只在 B 可动部分内重取；A / C / Q 缺失身份不变。"""
    N = len(order)
    s0 = np.asarray(s0, float)
    kq = np.asarray(kq, float)
    ids = check_ids(ids if ids is not None else np.arange(N).astype(str))
    base = source_mask(order, n)
    A, B, C, j = band_parts(order, n, w)
    if j == 0:
        return base
    good = B[np.isfinite(kq[B])]
    if not len(good):
        return base
    k = int(base[good].sum())
    pri = kq if inside is None else np.asarray(inside, float)
    if not np.isfinite(pri[good]).all():
        raise ValueError('可动优先序必须有限')
    rk = ranks_of(order)
    target = good[np.lexsort((ids[good], rk[good], pri[good]))]          # 无记忆新优先序
    if prev_natural is None:
        take = target[:k]
    else:
        slot = np.sort(s0[good])
        z = np.full(N, np.nan)
        z[target] = slot
        ell = np.ones(N) if loading is None else np.asarray(loading, float)
        z[good] -= float(b) * ell[good] * np.asarray(prev_natural, bool)[good]
        tr = np.empty(N, int)
        tr[target] = np.arange(len(target))
        take = good[np.lexsort((ids[good], tr[good], z[good]))][:k]
    out = base.copy()
    out[good] = False
    out[take] = True
    return out


def band_native_metric(order, s0, kq, n, w, inside, prev_natural=None, b=0.0, loading=None, ids=None):
    """NATIVE_METRIC_LAG（plan §5.3a）：同可动域 / 名额 / 自然 U，但不重分配评分槽，直接在 native_s(α) 上减 bonus。"""
    N = len(order)
    kq = np.asarray(kq, float)
    z = np.asarray(inside, float).copy()
    ids = check_ids(ids if ids is not None else np.arange(N).astype(str))
    base = source_mask(order, n)
    A, B, C, j = band_parts(order, n, w)
    if j == 0:
        return base
    good = B[np.isfinite(kq[B])]
    if not len(good):
        return base
    k = int(base[good].sum())
    if not np.isfinite(z[good]).all():
        raise ValueError('可动优先序必须有限')
    rk = ranks_of(order)
    natural = good[np.lexsort((ids[good], rk[good], z[good]))]
    tie = np.empty(N, int)
    tie[natural] = np.arange(len(good))
    if prev_natural is not None:
        ell = np.ones(N) if loading is None else np.asarray(loading, float)
        if not np.isfinite(ell[good]).all():
            raise ValueError('K_loading 必须有限')
        z[good] -= float(b) * ell[good] * np.asarray(prev_natural, bool)[good]
    take = good[np.lexsort((ids[good], tie[good], z[good]))][:k]
    out = base.copy()
    out[good] = False
    out[take] = True
    return out


def band_unprotected(order, s0, kq, n, w, inside, prev_natural, b=0.10, loading=None, ids=None):
    """UNPROTECTED_LAG10 桥（plan §5.3）：同一重排分数（B 外有限股票保留原 s0），折让后在整个 E 的 Q 有限部分重选；
    Q 缺失者锁原 U0 身份；有限部分名额 = n − 原 U0 中 Q 缺失数。返回 (名单, outside_band_edits)。"""
    N = len(order)
    s0 = np.asarray(s0, float)
    kq = np.asarray(kq, float)
    ids = check_ids(ids if ids is not None else np.arange(N).astype(str))
    base = source_mask(order, n)
    A, B, C, j = band_parts(order, n, w)
    fin = np.isfinite(kq)
    good = B[fin[B]]
    z = s0.copy()
    rk = ranks_of(order)
    if len(good):
        pri = np.asarray(inside, float)
        target = good[np.lexsort((ids[good], rk[good], pri[good]))]
        z[target] = np.sort(s0[good])
    ell = np.ones(N) if loading is None else np.asarray(loading, float)
    zz = z - float(b) * ell * np.asarray(prev_natural, bool)
    F = np.flatnonzero(fin)
    k = n - int((base & ~fin).sum())
    # 二级键 = 当天无记忆新次序（plan §5.3 第 2 步，与 PROTECTED 同）：A / C 原秩，B 有限者按新优先序占用 B 有限者原来的秩位
    newpos = rk.astype(float)
    if len(good):
        newpos[target] = np.sort(rk[good])
    take = F[np.lexsort((ids[F], newpos[F], zz[F]))][:k]
    out = base & ~fin
    out[take] = True
    inside_band = np.zeros(N, bool)
    inside_band[B] = True
    edits = int(((out != base) & ~inside_band).sum())
    return out, edits


# ------------------------------------------------------------------ PRIORITY_PASS / HARD_CONJ（含 RULE_LAG10）
def priority_pass(order, s0, kq, n, c, prev_natural=None, b=0.0, loading=None, ids=None):
    """PASS = (kQ ≤ c)；Q 缺失者原身份固定；有限者按 (不合格, s0[−bonus], 原总序, ticker) 填满剩余名额，不足回填。
    RULE_LAG10：只在 PASS / FAIL 各自分区内给昨日同规则无记忆 U 折让，不能把 FAIL 排到 PASS 之前。返回 (名单, 回填数)。"""
    c = check_threshold(c)
    N = len(order)
    s0 = np.asarray(s0, float)
    kq = np.asarray(kq, float)
    ids = check_ids(ids if ids is not None else np.arange(N).astype(str))
    rk = ranks_of(order)
    sfull = s0.copy()
    if prev_natural is not None:
        ell = np.ones(N) if loading is None else np.asarray(loading, float)
        sfull = s0 - float(b) * ell * np.asarray(prev_natural, bool)
        # 记忆版：Q 缺失者保留"记忆基门"身份（与 HARD 的 U_oldlag 同口径）；减 bonus 后平局按 ticker（= 源 LAG1 / mem_gate 的位置序），
        # 使附录 A3-6 端点 c = 1 ≡ OLD_LAG 逐格成立（无记忆版 (s0, 原总序) 与 (s0, ticker) 等价）
        base = source_mask(np.lexsort((ids, sfull)), n)
        sec = np.zeros(N, int)
    else:
        base = source_mask(order, n)
        sec = rk
    known = np.isfinite(kq)
    out = base & ~known
    k = n - int(out.sum())
    ix = np.flatnonzero(known)
    passing = kq[ix] <= c
    sc = sfull[ix]
    o = ix[np.lexsort((ids[ix], sec[ix], sc, ~passing))]
    out[o[:k]] = True
    refill = int((out & known & ~(np.isfinite(kq) & (kq <= c))).sum())
    return out, refill


def hard_conj(base_gate, kq, c):
    """G = 原门 ∩ (Q 缺失原样保留 ∪ PASS)；不补回。base_gate = 无记忆 U0 或记忆版的源 LAG1_10 旧核心门 U_oldlag。"""
    c = check_threshold(c)
    kq = np.asarray(kq, float)
    g = np.asarray(base_gate, bool)
    return g & (~np.isfinite(kq) | (kq <= c))


# ------------------------------------------------------------------ 同编辑预算（plan §5.6）
def edit_match(order, kq, n, w, native_mask, native_s, ids=None):
    """J = NATIVE_MASKFIX 相对 U0 的换入数；J* = min(J, B 中有限 Q 原入选数, B 中有限 Q 原未选数, NATIVE 可用换入数, NATIVE 可用换出数)。
    返回 dict(LOCAL, GLOBAL, NATIVE_TRIM 名单, J, J*)。三账户恰换 J* 对；负优势对也不临场少换。"""
    N = len(order)
    kq = np.asarray(kq, float)
    ns = np.asarray(native_s, float)
    ids = check_ids(ids if ids is not None else np.arange(N).astype(str))
    u0 = source_mask(order, n)
    nat = np.asarray(native_mask, bool)
    rk = ranks_of(order)
    A, B, C, j = band_parts(order, n, w)
    inB = np.zeros(N, bool)
    inB[B] = True
    fin = np.isfinite(kq)
    J = int((nat & ~u0).sum())
    nin = np.flatnonzero(nat & ~u0)
    nout = np.flatnonzero(u0 & ~nat)
    Js = int(min(J, (inB & fin & u0).sum(), (inB & fin & ~u0).sum(), len(nin), len(nout)))

    def swap(domain):
        outs = np.flatnonzero(u0 & domain & fin)
        ins = np.flatnonzero(~u0 & domain & fin)
        outs = outs[np.lexsort((ids[outs], -rk[outs], -kq[outs]))][:Js]          # 换出 Q 最差
        ins = ins[np.lexsort((ids[ins], rk[ins], kq[ins]))][:Js]                  # 换入 Q 最好
        g = u0.copy()
        g[outs] = False
        g[ins] = True
        return g
    loc = swap(inB)
    glo = swap(np.ones(N, bool))
    tin = nin[np.lexsort((ids[nin], rk[nin], ns[nin]))][:Js]                      # native_s 好 → 劣
    tout = nout[np.lexsort((ids[nout], -rk[nout], -ns[nout]))][:Js]               # native_s 劣 → 好
    trim = u0.copy()
    trim[tout] = False
    trim[tin] = True
    return dict(LOCAL=loc, GLOBAL=glo, NATIVE_TRIM=trim, J=J, J_star=Js)


# ------------------------------------------------------------------ 复制坐标与记忆
def copy_coordinates(order, owner_values):
    """COPY_GATE_ORDER（plan §4.3）：完整 E 冻结总序上 (r − .5)/N，之后再施加 owner 有限 / 缺失掩码。"""
    N = len(order)
    out = np.empty(N)
    if N:
        out[order] = (np.arange(N) + 0.5) / N
    out[~np.isfinite(np.asarray(owner_values, float))] = np.nan
    return out


def memory_reference(kind, prev_natural, prev_actual):
    if kind == 'HG10':
        return np.asarray(prev_actual, bool).copy()
    if kind in ('LAG1_10', 'PROTECTED_LAG10', 'UNPROTECTED_LAG10', 'RULE_LAG10'):
        return np.asarray(prev_natural, bool).copy()
    if kind == 'NONE':
        return np.zeros(len(prev_natural), bool)
    raise ValueError('未知记忆合同：%s' % kind)


def align_prev(prev_ids, prev_mask, ids):
    """昨日名单按 ticker 对齐到今日 E（今日不在 E 者不恢复）。"""
    s = set(np.asarray(prev_ids, str)[np.asarray(prev_mask, bool)])
    return np.array([t in s for t in np.asarray(ids, str)], bool)


# ------------------------------------------------------------------ 两日测量（plan §6.1；raw 先合成，再在 T 做一次源中性化）
def two_day_raw(d_T, d_prev, op):
    d0 = np.asarray(d_T, float)
    d1 = np.asarray(d_prev, float)
    ok = np.isfinite(d0) & np.isfinite(d1) & (d0 >= 0) & (d1 >= 0)
    v = {'MAX': np.maximum(d0, d1), 'MIN': np.minimum(d0, d1), 'LAG': d1, 'MEAN': (d0 + d1) / 2.0}[op]
    out = np.full(v.shape, np.nan)
    out[ok] = 1.0 / (v[ok] + EPS_Q)
    return out


TWO_DAY_OPS = {'Q_MAX2': 'MAX', 'Q_MIN2': 'MIN', 'Q_LAGRAW1': 'LAG', 'Q_MEAN2': 'MEAN'}
