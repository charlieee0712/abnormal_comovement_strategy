# -*- coding: utf-8 -*-
"""E6m B3 配对与随机内核（numba；不缓存编译结果，避免 E6l lessons 38 的缓存段错误）。纯函数，不读文件。
成员约定：一个 (日, 对比, 匹配层) 的合法集合，可分层成员按 (层, d, ticker) 预排序放在前段，层 s 的成员在 [off[s], off[s+1])；
不可分层成员放在 off[-1] 之后（参加置换、不参加匹配）。
标签：1 = HIGH 侧，0 = LOW 侧，−1 = 其他 / 未知（不参与）。配对 = min_distance_pairs 规范（plan §7.4；e6m_b3_tools 参考实现）：
小侧全配、大侧可跳；D[i,j] = min(D[i,j−1], D[i−1,j−1] + |a_i − b_j|)；同代价跳过较晚的大侧对象。
实现：D 只留两行（逐行滚动），回溯表 take 由调用方预分配并复用（只读写过的格；j ≥ i 的格每行都先写后读）。"""
import numpy as np
import numba as nb


@nb.njit(cache=False)
def splitmix64(x):
    z = x + np.uint64(0x9E3779B97F4A7C15)
    z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return z ^ (z >> np.uint64(31))


@nb.njit(cache=False)
def hkey(seed, path, block, ident):
    return splitmix64(seed ^ splitmix64(np.uint64(path) ^ splitmix64(np.uint64(block) ^ splitmix64(np.uint64(ident)))))


@nb.njit(cache=False)
def dp_core(a, b, out_i, out_j, take, prev, cur):
    """a：小侧值（按 (d, ticker) 升序）；b：大侧值（同序）；len(a) ≤ len(b)。take ≥ (m+1)×(n+1)，prev / cur ≥ n+1。
    返回配对数 k，out_i[:k] / out_j[:k] 为 a / b 内下标（升序）。"""
    m = a.shape[0]
    n = b.shape[0]
    if m == 0:
        return 0
    for j in range(n + 1):
        prev[j] = 0.0
    for i in range(1, m + 1):
        cur[i - 1] = np.inf
        ai = a[i - 1]
        for j in range(i, n + 1):
            match = prev[j - 1] + abs(ai - b[j - 1])
            skip = cur[j - 1]
            if match < skip:
                cur[j] = match
                take[i, j] = 1
            else:
                cur[j] = skip
                take[i, j] = 0
        for j in range(i - 1, n + 1):
            prev[j] = cur[j]
    k = 0
    i = m
    j = n
    while i > 0:
        if take[i, j] == 1:
            out_i[k] = i - 1
            out_j[k] = j - 1
            k += 1
            i -= 1
        j -= 1
    for t in range(k // 2):
        out_i[t], out_i[k - 1 - t] = out_i[k - 1 - t], out_i[t]
        out_j[t], out_j[k - 1 - t] = out_j[k - 1 - t], out_j[t]
    return k


@nb.njit(cache=False)
def dp_pairs(a, b, out_i, out_j):
    """自带缓冲的便捷版（测试 / 零星调用）。"""
    n = b.shape[0]
    take = np.empty((a.shape[0] + 1, n + 1), np.uint8)
    prev = np.empty(n + 1)
    cur = np.empty(n + 1)
    return dp_core(a, b, out_i, out_j, take, prev, cur)


@nb.njit(cache=False)
def match_day_buf(off, d, lab, Y, pair_h, pair_l, take, prev, cur, hi_idx, lo_idx, oi, oj, a_buf, b_buf):
    """一个 (日, 对比, 匹配层) 在给定标签下的分层配对（缓冲由调用方给）。返回 (配对数, 逐列和, 逐列有效数, 逐列是否含 NaN)。"""
    C = Y.shape[1]
    s_sum = np.zeros(C)
    s_cnt = np.zeros(C, np.int64)
    s_nan = np.zeros(C, np.bool_)
    npair = 0
    for s in range(off.shape[0] - 1):
        nh = 0
        nl = 0
        for t in range(off[s], off[s + 1]):
            if lab[t] == 1:
                hi_idx[nh] = t
                nh += 1
            elif lab[t] == 0:
                lo_idx[nl] = t
                nl += 1
        if nh == 0 or nl == 0:
            continue
        if nh <= nl:
            for q in range(nh):
                a_buf[q] = d[hi_idx[q]]
            for q in range(nl):
                b_buf[q] = d[lo_idx[q]]
            k = dp_core(a_buf[:nh], b_buf[:nl], oi, oj, take, prev, cur)
            for q in range(k):
                pair_h[npair] = hi_idx[oi[q]]
                pair_l[npair] = lo_idx[oj[q]]
                npair += 1
        else:
            for q in range(nl):
                a_buf[q] = d[lo_idx[q]]
            for q in range(nh):
                b_buf[q] = d[hi_idx[q]]
            k = dp_core(a_buf[:nl], b_buf[:nh], oi, oj, take, prev, cur)
            for q in range(k):
                pair_l[npair] = lo_idx[oi[q]]
                pair_h[npair] = hi_idx[oj[q]]
                npair += 1
    for q in range(npair):
        for c in range(C):
            v = Y[pair_h[q], c] - Y[pair_l[q], c]
            if np.isfinite(v):
                s_sum[c] += v
                s_cnt[c] += 1
            else:
                s_nan[c] = True
    return npair, s_sum, s_cnt, s_nan


@nb.njit(cache=False)
def bufs(n):
    """一组匹配缓冲（n = 合法集合人数）。"""
    return (np.empty((n + 1, n + 1), np.uint8), np.empty(n + 1), np.empty(n + 1), np.empty(n, np.int64), np.empty(n, np.int64),
            np.empty(n + 1, np.int64), np.empty(n + 1, np.int64), np.empty(n), np.empty(n))


@nb.njit(cache=False)
def match_day(off, d, lab, Y, pair_h, pair_l):
    n = d.shape[0]
    take, prev, cur, hi_idx, lo_idx, oi, oj, a_buf, b_buf = bufs(n)
    return match_day_buf(off, d, lab, Y, pair_h, pair_l, take, prev, cur, hi_idx, lo_idx, oi, oj, a_buf, b_buf)


@nb.njit(cache=False)
def permute_labels(lab, tick, recv, seed, path, block):
    """R_CELL_REMATCH：已知类别码（≥ 0）在合法集合内按块哈希键置换（接收者按 ticker 升序；供体按键稳定升序）；未知（−1）不动。"""
    n = lab.shape[0]
    known = np.empty(n, np.int64)
    nk = 0
    for t in range(n):
        if lab[recv[t]] >= 0:
            known[nk] = recv[t]
            nk += 1
    keys = np.empty(nk, np.uint64)
    for t in range(nk):
        keys[t] = hkey(seed, path, block, tick[known[t]])
    order = np.argsort(keys, kind='mergesort')
    out = lab.copy()
    for t in range(nk):
        out[known[t]] = lab[known[order[t]]]
    return out


@nb.njit(cache=False)
def means_diff(lab, Y):
    """U0（非配对）：HIGH 侧与 LOW 侧逐列等权均值之差（各侧只对有限值平均）；任一侧无有限值 → NaN。"""
    C = Y.shape[1]
    sh = np.zeros(C)
    sl = np.zeros(C)
    nh = np.zeros(C, np.int64)
    nl = np.zeros(C, np.int64)
    for t in range(lab.shape[0]):
        if lab[t] == 1:
            for c in range(C):
                v = Y[t, c]
                if np.isfinite(v):
                    sh[c] += v
                    nh[c] += 1
        elif lab[t] == 0:
            for c in range(C):
                v = Y[t, c]
                if np.isfinite(v):
                    sl[c] += v
                    nl[c] += 1
    out = np.full(C, np.nan)
    for c in range(C):
        if nh[c] > 0 and nl[c] > 0:
            out[c] = sh[c] / nh[c] - sl[c] / nl[c]
    return out


@nb.njit(cache=False)
def sides_of(code, smap):
    """类别码（0..K−1；−1 未知）→ 侧标签（1 / 0 / −1），smap[k] = 类别 k 所在侧。"""
    out = np.full(code.shape[0], -1, np.int8)
    for t in range(code.shape[0]):
        if code[t] >= 0:
            out[t] = smap[code[t]]
    return out


@nb.njit(cache=False)
def paths_rematch(off, d, code, smap, Y, tick, recv, seed, block, P, matched):
    """R_CELL_REMATCH 的 P 条路径：类别码在合法集合内置换（保持各类人数、未知不动）→ 映射两侧 → 重新匹配（matched）或均值差。
    返回 (P, C) 可估子集日值与严格版（非配对时两者相同，调用方只用前者）。"""
    C = Y.shape[1]
    est = np.full((P, C), np.nan)
    strict = np.full((P, C), np.nan)
    n = d.shape[0]
    ph = np.empty(n, np.int64)
    pl = np.empty(n, np.int64)
    take, prev, cur, hi_idx, lo_idx, oi, oj, a_buf, b_buf = bufs(n)
    for p in range(P):
        lp = sides_of(permute_labels(code, tick, recv, seed, p, block), smap)
        if matched:
            npair, s_sum, s_cnt, s_nan = match_day_buf(off, d, lp, Y, ph, pl, take, prev, cur, hi_idx, lo_idx, oi, oj, a_buf, b_buf)
            for c in range(C):
                if s_cnt[c] > 0:
                    est[p, c] = s_sum[c] / s_cnt[c]
                if npair > 0 and not s_nan[c]:
                    strict[p, c] = s_sum[c] / npair
        else:
            md = means_diff(lp, Y)
            for c in range(C):
                est[p, c] = md[c]
                strict[p, c] = md[c]
    return est, strict


@nb.njit(cache=False)
def paths_pairswap(ph, pl, npair, Y, tick, seed, block, P):
    """R_PAIR_SWAP：固定真实配对，逐对按块哈希最低位翻转 HIGH / LOW。返回 (P, C) 可估子集日值与严格版。"""
    C = Y.shape[1]
    est = np.full((P, C), np.nan)
    strict = np.full((P, C), np.nan)
    for p in range(P):
        s_sum = np.zeros(C)
        s_cnt = np.zeros(C, np.int64)
        s_nan = np.zeros(C, np.bool_)
        for q in range(npair):
            key = hkey(seed, p, block, np.uint64(tick[ph[q]]) * np.uint64(1000003) + np.uint64(tick[pl[q]]))
            sg = 1.0 if (key & np.uint64(1)) == np.uint64(0) else -1.0
            for c in range(C):
                v = Y[ph[q], c] - Y[pl[q], c]
                if np.isfinite(v):
                    s_sum[c] += sg * v
                    s_cnt[c] += 1
                else:
                    s_nan[c] = True
        for c in range(C):
            if s_cnt[c] > 0:
                est[p, c] = s_sum[c] / s_cnt[c]
            if npair > 0 and not s_nan[c]:
                strict[p, c] = s_sum[c] / npair
    return est, strict
