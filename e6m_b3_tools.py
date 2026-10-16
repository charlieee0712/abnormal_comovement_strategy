# -*- coding: utf-8 -*-
"""E6m B3–B6 与对照工具（plan §7.2 / §7.4 / §8.1a / §8.3 / §8.4 / §9.3；参考实现 = e6m_spec_tests.py 同名函数，逐条转写并加生产所需的
有效性检查）。纯函数，不读文件。"""
import hashlib

import numpy as np

STATE_KNOWN = ('UP', 'DOWN', 'MIXED')


def activity_terciles(a, dom):
    """活动三分：当日参考域内有限 a 的中点百分位（(#< + .5·#=)/n）→ LOW ≤ 1/3 < MID ≤ 2/3 < HIGH；缺失 / 域外 = UNKNOWN；平局不打散。"""
    a = np.asarray(a, float)
    dom = np.asarray(dom, bool)
    ok = dom & np.isfinite(a)
    out = np.full(len(a), 'UNKNOWN', dtype=object)
    v = a[ok]
    if len(v):
        s = np.sort(v)
        lo = np.searchsorted(s, v, 'left')
        hi = np.searchsorted(s, v, 'right')
        p = (lo + 0.5 * (hi - lo)) / len(v)
        out[np.flatnonzero(ok)] = np.where(p <= 1 / 3, 'LOW', np.where(p <= 2 / 3, 'MID', 'HIGH'))
    return out


def price_reaction(r, dom):
    """r = log(C / lclose)。先核 r 有限：无效 → UNKNOWN（不进 QUIET）；QUIET = d = |r| 在当日参考域有限 d 的最低三分位（中点百分位 ≤ 1/3），
    其余 r > 0 → UP、r < 0 → DOWN；真实零 r → QUIET。"""
    r = np.asarray(r, float)
    dom = np.asarray(dom, bool)
    out = np.full(len(r), 'UNKNOWN', dtype=object)
    ok = dom & np.isfinite(r)
    d = np.abs(r[ok])
    if len(d):
        s = np.sort(d)
        lo = np.searchsorted(s, d, 'left')
        hi = np.searchsorted(s, d, 'right')
        p = (lo + 0.5 * (hi - lo)) / len(d)
        rr = r[ok]
        lab = np.where((p <= 1 / 3) | (rr == 0), 'QUIET', np.where(rr > 0, 'UP', 'DOWN'))
        out[np.flatnonzero(ok)] = lab
    return out


def order(score, ids):
    s = np.asarray(score, float)
    if np.any(~np.isfinite(s)):
        raise ValueError('finite scores required')
    ids = np.asarray(ids, str)
    if ids.ndim != 1 or len(ids) != len(s) or len(set(ids)) != len(ids):
        raise ValueError('unique aligned stock IDs required')
    return np.lexsort((ids, s))


def min_distance_pairs(x, y, xids=None, yids=None):
    """一维最大基数、最小 L1 匹配（plan §7.4；参考实现逐条转写）：(值, ticker) 排序；小侧全配、大侧可跳过；
    D[i,j] = min(D[i,j−1], D[i−1,j−1] + |a_i − b_j|)；同代价跳过较晚的大侧对象。返回输入下标对。"""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if x.ndim != 1 or y.ndim != 1 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('finite vectors required')
    xi = np.arange(len(x)).astype(str) if xids is None else np.asarray(xids, str)
    yi = np.arange(len(y)).astype(str) if yids is None else np.asarray(yids, str)
    if len(set(xi)) != len(xi) or len(set(yi)) != len(yi):
        raise ValueError('duplicate IDs')
    if len(x) > len(y):
        return [(j, i) for i, j in min_distance_pairs(y, x, yi, xi)]
    ox = order(x, xi)
    oy = order(y, yi)
    a = x[ox]
    b = y[oy]
    m, n = len(a), len(b)
    if not m:
        return []
    D = np.full((m + 1, n + 1), np.inf)
    D[0, :] = 0.0
    take = np.zeros((m + 1, n + 1), bool)
    for i in range(1, m + 1):
        for j in range(i, n + 1):
            match = D[i - 1, j - 1] + abs(a[i - 1] - b[j - 1])
            skip = D[i, j - 1]
            if match < skip:
                D[i, j] = match
                take[i, j] = True
            else:
                D[i, j] = skip
    pairs = []
    i, j = m, n
    while i:
        if take[i, j]:
            pairs.append((int(ox[i - 1]), int(oy[j - 1])))
            i -= 1
        j -= 1
    return list(reversed(pairs))


def label_pair(price, entry, exit_):
    """FWD_ENDPOINT（终点 / 入场 − 1，首尾有效即可）与 FWD_LINEAR（逐日简单收益之和，要求全路径有效）。"""
    p = np.asarray(price, float)
    if entry < 0 or exit_ >= len(p) or exit_ <= entry:
        raise ValueError('unavailable interval')
    z = p[entry:exit_ + 1]
    ends = np.isfinite(z[[0, -1]]).all() and (z[[0, -1]] > 0).all()
    endpoint = float(z[-1] / z[0] - 1) if ends else np.nan
    complete = np.isfinite(z).all() and (z > 0).all()
    linear = float((z[1:] / z[:-1] - 1).sum()) if complete else np.nan
    return {'endpoint': endpoint, 'linear_daily': linear}


def symmetric_states(pa, ma, pb, mb):
    """SYMDEC（plan §8.1a）：frequency + within + one_sided = mean_b − mean_a；占用状态均值未知 → 报错，不按 0 闭合。"""
    pa, pb, ma, mb = (np.asarray(v, float) for v in (pa, pb, ma, mb))
    if not np.isclose(pa.sum(), 1) or not np.isclose(pb.sum(), 1):
        raise ValueError('state masses must sum to one')
    if np.any((pa > 0) & ~np.isfinite(ma)) or np.any((pb > 0) & ~np.isfinite(mb)):
        raise ValueError('unknown occupied-state mean')
    common = (pa > 0) & (pb > 0)
    only = ~common
    ca = pa * np.where(np.isfinite(ma), ma, 0.0)
    cb = pb * np.where(np.isfinite(mb), mb, 0.0)
    freq = float(np.sum((pb[common] - pa[common]) * (ma[common] + mb[common]) / 2))
    within = float(np.sum((mb[common] - ma[common]) * (pa[common] + pb[common]) / 2))
    one = float(np.sum((cb - ca)[only]))
    return {'frequency': freq, 'within': within, 'one_sided': one, 'total': float((cb - ca).sum())}


def first_feasible_exit(trigger, normal, entry, sell_allowed):
    """B6 主读（plan §8.4）：目标退出 = min(正常目标退出日, 触发日 + 1)，再取最早可卖日；卖不掉继续持有；不晚于原正常退出。"""
    x = np.asarray(sell_allowed, bool)

    def after(day):
        a = np.flatnonzero(x[max(day, entry + 1):])
        return int(max(day, entry + 1) + a[0]) if len(a) else None
    baseline = after(normal)
    early = after(min(normal, trigger + 1)) if trigger is not None else baseline
    return early, baseline


def v_condition_mask(state, condition):
    """V 条件（plan §8.3）：ALL 不读 Trend；ALL_KNOWN 只已知；DOWN_MIXED / UP 在 UNKNOWN 不施加。"""
    s = np.asarray(state, str)
    known = np.isin(s, STATE_KNOWN)
    if condition == 'ALL':
        return np.ones(len(s), bool)
    if condition == 'ALL_KNOWN':
        return known
    if condition == 'DOWN_MIXED':
        return np.isin(s, ['DOWN', 'MIXED'])
    if condition == 'UP':
        return s == 'UP'
    raise ValueError('unknown V condition')


def stable_permute(vals, ids, seed, block):
    """显式种子置换（缺失保持；有限值多重集保持；与行序无关）。"""
    vals = np.asarray(vals, float)
    ids = np.asarray(ids, str)
    out = vals.copy()
    ix = np.flatnonzero(np.isfinite(vals))
    receiver = sorted(ix, key=lambda j: ids[j])
    donor = sorted(ix, key=lambda j: (hashlib.blake2b(('%s|%s|%s' % (seed, block, ids[j])).encode(), digest_size=16).digest(), ids[j]))
    out[receiver] = vals[donor]
    return out


def delete_count_control(parent, deleted, groups, ids, seed=11, day=0, eligible=None):
    """DELETE_BUDGET_COND：父门内同层同删除数随机删除；不从父外 / owner 缺失者取。"""
    u = np.asarray(parent, bool)
    d = np.asarray(deleted, bool)
    g = np.asarray(groups, str)
    ids = np.asarray(ids, str)
    e = np.ones_like(u) if eligible is None else np.asarray(eligible, bool)
    cand = u & e
    if np.any(d & ~cand):
        raise ValueError('deleted set outside eligible parent')
    out = u.copy()
    for cell in sorted(set(g[cand])):
        ix = np.flatnonzero(cand & (g == cell))
        m = int(np.sum(d[ix]))
        ix = sorted(ix, key=lambda j: (hashlib.blake2b(('%s|%s|%s' % (seed, day, ids[j])).encode(), digest_size=16).digest(), ids[j]))
        out[ix[:m]] = False
    return out


def classify_weight_change(parent, child, returns):
    """Δgross = 新增 + 消失 + 共同重定权（plan §9.1）。"""
    p, c, r = (np.asarray(v, float) for v in (parent, child, returns))
    added = (p == 0) & (c > 0)
    removed = (p > 0) & (c == 0)
    common = (p > 0) & (c > 0)
    return {'added': float(c[added] @ r[added]), 'removed': float(-p[removed] @ r[removed]),
            'common_reweight': float((c[common] - p[common]) @ r[common]), 'total': float((c - p) @ r)}
