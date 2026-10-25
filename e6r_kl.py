# -*- coding: utf-8 -*-
"""E6r 两层预算求解器（numba；plan §6.1 / 附录 C `proportional_fill` / `project_weights` / `transport_entry_budget` 逐式移植）。
- kl_project：固定总额 Σw = Σb 下的最小相对熵投影（单股上限 u、组上限 gcap、NA 固定 b、b = 0 不能新增）；嵌套单调水位法：
  外层全局乘子 a 二分（先倍增找上界 ≤ 200 次，再二分 90 次），组超限时组内 prop_fill（带上限比例填充，二分 90 次）；正偏好先按最大值归一（A15 尺度不变）。
- transport_cells：账户层（plan §6.1 第二层）ρ 只乘一次（q = x⁰·ρ）；NA 与未知格固定 x⁰；每个已知格（必须属一个行业）预算 = Σ_cell x⁰，格内投影；
  无格时直接 kl_project(x⁰, q, …)。
- 返回状态码：0 OK；1 基线不可行；2 经投影新增名字；3 自由名字偏好非正；4 投影不可行；5 固定项漂移 / 格漂移；6 格跨行业。
容差全部相对（按总额量级），1 亿量级账户不用绝对容差（E6p lesson）。"""
import numpy as np
from numba import njit

KL_OK, KL_BASE_INFEASIBLE, KL_NEW_NAME, KL_NONPOS, KL_INFEASIBLE, KL_DRIFT, KL_CELL_SPAN = range(7)


@njit(cache=True)
def prop_fill(q, cap, idx, m, target, out):
    """idx[:m] 子集上 Σ min(cap_i, a·q_i) = target 的带上限比例分配（plan 附录 C proportional_fill）；不可行返回 False。"""
    avail = 0.0
    scale = 0.0
    for t in range(m):
        i = idx[t]
        if q[i] > 0.0:
            avail += cap[i]
            if q[i] > scale:
                scale = q[i]
    tol = 2e-12 * (target if target > 1.0 else 1.0)
    if target > avail + tol:
        return False
    if target <= 0.0:
        for t in range(m):
            out[idx[t]] = 0.0
        return True
    if not (scale > 0.0):
        return False
    lo = 0.0
    hi = 1.0
    for _ in range(2000):
        v = 0.0
        for t in range(m):
            i = idx[t]
            x = hi * q[i] / scale
            v += x if x < cap[i] else cap[i]
        if v >= target - 1e-14 * (target if target > 1.0 else 1.0):
            break
        hi *= 2.0
        if not np.isfinite(hi):
            return False
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        v = 0.0
        for t in range(m):
            i = idx[t]
            x = mid * q[i] / scale
            v += x if x < cap[i] else cap[i]
        if v < target:
            lo = mid
        else:
            hi = mid
    for t in range(m):
        i = idx[t]
        x = hi * q[i] / scale
        out[i] = x if x < cap[i] else cap[i]
    return True


@njit(cache=True)
def _at(a, n, b, qs, u, grp, G, free, residual, gfree_ptr, gfree_idx, gcount, w, tmpq):
    for i in range(n):
        w[i] = b[i]
    for i in range(n):
        if free[i]:
            x = a * qs[i]
            w[i] = x if x < u[i] else u[i]
    for g in range(G):
        if gcount[g] == 0:
            continue
        s = 0.0
        for t in range(gfree_ptr[g], gfree_ptr[g] + gcount[g]):
            s += w[gfree_idx[t]]
        if s > residual[g]:
            ok = prop_fill(qs, u, gfree_idx[gfree_ptr[g]:gfree_ptr[g] + gcount[g]], gcount[g], residual[g], w)
            if not ok:
                return False
    return True


@njit(cache=True)
def kl_project(b, q, u, grp, gcap, pin_in, w):
    """plan 附录 C project_weights：返回状态码；结果写 w（与 b 等长）。grp < 0 = 无组上限。"""
    n = b.shape[0]
    G = gcap.shape[0]
    pin = pin_in.copy()
    total = 0.0
    for i in range(n):
        total += b[i]
    scl = total if total > 1.0 else 1.0
    tol = 2e-10 * scl
    for i in range(n):
        if b[i] > u[i] + tol:
            for k in range(n):
                w[k] = b[k]
            return KL_BASE_INFEASIBLE
    gsum = np.zeros(G)
    for i in range(n):
        if grp[i] >= 0:
            gsum[grp[i]] += b[i]
    for g in range(G):
        if gsum[g] > gcap[g] + tol:
            for k in range(n):
                w[k] = b[k]
            return KL_BASE_INFEASIBLE
    same = True
    allpin = True
    for i in range(n):
        if b[i] == 0.0:
            if q[i] != 0.0:
                for k in range(n):
                    w[k] = b[k]
                return KL_NEW_NAME
            pin[i] = True
        elif (not pin[i]) and not (q[i] > 0.0):
            for k in range(n):
                w[k] = b[k]
            return KL_NONPOS
        if q[i] != b[i]:
            same = False
        if not pin[i]:
            allpin = False
    if allpin or same:
        for k in range(n):
            w[k] = b[k]
        return KL_OK
    scale = 0.0
    for i in range(n):
        if not pin[i] and q[i] > scale:
            scale = q[i]
    qs = np.zeros(n)
    free = np.zeros(n, np.bool_)
    fixed_sum = 0.0
    for i in range(n):
        if pin[i]:
            fixed_sum += b[i]
        else:
            free[i] = True
            qs[i] = q[i] / scale
    target = total - fixed_sum
    if target < 1e-15 * scl:
        for k in range(n):
            w[k] = b[k]
        return KL_OK
    residual = np.zeros(G)
    for g in range(G):
        residual[g] = gcap[g]
    for i in range(n):
        if pin[i] and grp[i] >= 0:
            residual[grp[i]] -= b[i]
    for g in range(G):
        if residual[g] < 0.0:
            residual[g] = 0.0
    gcount = np.zeros(G, np.int64)
    for i in range(n):
        if free[i] and grp[i] >= 0:
            gcount[grp[i]] += 1
    gfree_ptr = np.zeros(G, np.int64)
    acc = 0
    for g in range(G):
        gfree_ptr[g] = acc
        acc += gcount[g]
    gfree_idx = np.zeros(max(acc, 1), np.int64)
    fill = np.zeros(G, np.int64)
    for i in range(n):
        if free[i] and grp[i] >= 0:
            g = grp[i]
            gfree_idx[gfree_ptr[g] + fill[g]] = i
            fill[g] += 1
    tmpq = np.zeros(n)
    lo = 0.0
    hi = 1.0
    found = False
    for _ in range(200):
        ok = _at(hi, n, b, qs, u, grp, G, free, residual, gfree_ptr, gfree_idx, gcount, w, tmpq)
        if not ok:
            for k in range(n):
                w[k] = b[k]
            return KL_INFEASIBLE
        s = 0.0
        for i in range(n):
            s += w[i]
        if s >= total - 1e-14 * scl:
            found = True
            break
        hi *= 2.0
    if not found:
        for k in range(n):
            w[k] = b[k]
        return KL_INFEASIBLE
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        _at(mid, n, b, qs, u, grp, G, free, residual, gfree_ptr, gfree_idx, gcount, w, tmpq)
        s = 0.0
        for i in range(n):
            s += w[i]
        if s < total:
            lo = mid
        else:
            hi = mid
    _at(hi, n, b, qs, u, grp, G, free, residual, gfree_ptr, gfree_idx, gcount, w, tmpq)
    for i in range(n):
        if pin[i] and w[i] != b[i]:
            return KL_DRIFT
    return KL_OK


@njit(cache=True)
def transport_cells(x0, rho, u, grp, gcap, pin, cell, use_cells, out):
    """plan 附录 C transport_entry_budget：q = x⁰·ρ（只乘一次）；NA 固定 x⁰；use_cells 时每个已知格预算 = Σ_cell x⁰、未知格（cell < 0）固定。"""
    n = x0.shape[0]
    q = np.zeros(n)
    for i in range(n):
        q[i] = x0[i] * rho[i]
        if x0[i] > 0.0 and not (q[i] > 0.0):
            for k in range(n):
                out[k] = x0[k]
            return KL_NONPOS
    if not use_cells:
        return kl_project(x0, q, u, grp, gcap, pin, out)
    pin2 = pin.copy()
    for i in range(n):
        out[i] = x0[i]
        if cell[i] < 0:
            pin2[i] = True
    # 逐格（按格 id 升序）
    order = np.argsort(cell, kind='mergesort')
    k0 = 0
    while k0 < n:
        c = cell[order[k0]]
        k1 = k0
        while k1 < n and cell[order[k1]] == c:
            k1 += 1
        if c >= 0:
            m = k1 - k0
            ix = order[k0:k1]
            g0 = grp[ix[0]]
            for t in range(m):
                if grp[ix[t]] != g0:
                    for k in range(n):
                        out[k] = x0[k]
                    return KL_CELL_SPAN
            bx = np.zeros(m)
            qx = np.zeros(m)
            ux = np.zeros(m)
            px = np.zeros(m, np.bool_)
            gx = np.zeros(m, np.int64)
            budget = 0.0
            for t in range(m):
                i = ix[t]
                bx[t] = x0[i]
                qx[t] = q[i]
                ux[t] = u[i]
                px[t] = pin2[i]
                budget += x0[i]
            gc = np.zeros(1)
            gc[0] = budget
            wx = np.zeros(m)
            st = kl_project(bx, qx, ux, gx, gc, px, wx)
            if st != KL_OK:
                for k in range(n):
                    out[k] = x0[k]
                return st
            s = 0.0
            for t in range(m):
                out[ix[t]] = wx[t]
                s += wx[t]
            if abs(s - budget) > 2e-10 * (budget if budget > 1.0 else 1.0):
                return KL_DRIFT
        k0 = k1
    for i in range(n):
        if pin2[i] and out[i] != x0[i]:
            return KL_DRIFT
    return KL_OK


@njit(cache=True)
def form_tilt(b, lab, lam, u, grp, gcap, pin_na, keep, cell, use_cells, w):
    """形成层（plan §6.1 第一层 / 附录 C tilt_weights、cell_tilt、gate_weights）：keep = 保留比例（1 保留 / 0 门掉 / 末名部分；GATE_TILT 先冻结原 cohort 标签再门）→ b. = b·keep；
    q = b'(1 + λs)，s = +1（T1）/ 0（T2、NA）/ −1（T3）；NA 与 b' = 0 固定；无格：KL 投影到 Σb'（单股 u、行业 gcap）；
    use_cells：每个已知格（cell ≥ 0）内投影、格预算 = Σ_cell b'、未知格固定 b'。λ = 0 → 精确零干预分派（w = b'）。返回状态码。"""
    n = b.shape[0]
    bb = np.zeros(n)
    for i in range(n):
        bb[i] = b[i] * keep[i]
    if lam == 0.0:
        for i in range(n):
            w[i] = bb[i]
        return KL_OK
    q = np.zeros(n)
    pin = np.zeros(n, np.bool_)
    for i in range(n):
        s = 1.0 if lab[i] == 1 else (-1.0 if lab[i] == 3 else 0.0)
        q[i] = bb[i] * (1.0 + lam * s)
        pin[i] = pin_na[i] or lab[i] == 0 or bb[i] == 0.0
    if not use_cells:
        return kl_project(bb, q, u, grp, gcap, pin, w)
    for i in range(n):
        w[i] = bb[i]
    order = np.argsort(cell, kind='mergesort')
    k0 = 0
    while k0 < n:
        c = cell[order[k0]]
        k1 = k0
        while k1 < n and cell[order[k1]] == c:
            k1 += 1
        if c >= 0:
            m = k1 - k0
            ix = order[k0:k1]
            bx = np.zeros(m)
            qx = np.zeros(m)
            ux = np.zeros(m)
            px = np.zeros(m, np.bool_)
            gx = np.zeros(m, np.int64)
            budget = 0.0
            for t in range(m):
                i = ix[t]
                bx[t] = bb[i]
                qx[t] = q[i]
                ux[t] = u[i]
                px[t] = pin[i]
                budget += bb[i]
            gc = np.zeros(1)
            gc[0] = budget
            wx = np.zeros(m)
            st = kl_project(bx, qx, ux, gx, gc, px, wx)
            if st != KL_OK:
                for k in range(n):
                    w[k] = bb[k]
                return st
            for t in range(m):
                w[ix[t]] = wx[t]
        k0 = k1
    return KL_OK


@njit(cache=True)
def tertile_codes(vals, m, out):
    """plan 附录 C tertiles：有限值 tie-aware 中点秩；< 3 有限或全同 → 全 NA（0）；T1 = 1 / T2 = 2 / T3 = 3（升序：低值 = T1）。返回 NA 原因
    （0 = 已分组；1 = 有限值 < 3；2 = 全同）。缺失格 = 0（NA）。"""
    for i in range(m):
        out[i] = 0
    nf = 0
    for i in range(m):
        if np.isfinite(vals[i]):
            nf += 1
    if nf < 3:
        return 1
    fv = np.zeros(nf)
    fi = np.zeros(nf, np.int64)
    k = 0
    for i in range(m):
        if np.isfinite(vals[i]):
            fv[k] = vals[i]
            fi[k] = i
            k += 1
    o = np.argsort(fv, kind='mergesort')
    if fv[o[0]] == fv[o[nf - 1]]:
        return 2
    k = 0
    while k < nf:
        j = k + 1
        while j < nf and fv[o[j]] == fv[o[k]]:
            j += 1
        p = (k + j) / (2.0 * nf)
        lab = 1 if p < 1.0 / 3.0 else (3 if p > 2.0 / 3.0 else 2)
        for t in range(k, j):
            out[fi[o[t]]] = lab
        k = j
    return 0
