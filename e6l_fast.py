# -*- coding: utf-8 -*-
"""E6l 随机层提速件（numba 0.58；error_model='numpy' = IEEE 语义，除零得 inf / nan 不抛错）。只换算法路径，
结果与参照实现逐位相同，Stage 0 在真实数据上逐格 / 逐位核（e6l_stage0_output --fast）：
  order_U     逐日 np.argsort(kind='stable') 的全序 O 与前 K 的无带门 U（与 e6i_randoms.KeepDom.keep 同一调用）
  rec_single  HG / STATE / LAG1 / RMARK（单一折让水平）：按全序 O 拆成"有标记 / 无标记"两列；无标记列 v = s − 0.0 = s；
              有标记列 v = s − b 在 O 序上单调不减，舍入并列段（s 不同而 s − b 相同）按位置重排；两路按 (v, 位置) 归并取前 K
              = 对 s − b·mark 做 stable argsort 取前 K（e6l_ops.mem_gate / e6k_ops.hg_gate 同式）
  rec_decay   DECAY：逐日对 s − bon 稳定归并排序（折让多水平，不用归并技巧）；last_confirmed 用"当前连续在域段"判有效
  rec_inv     INV：库存计数 > 0 → 单一折让归并 → 逐日下游 → 形成日 d 的批次在 d + H + 1 日退出（e6l_ops.inv_path 同式）
  down        门 → 最终名单（A4b = e6i_randoms.dep_stage2_keep 同算式、同累加次序 + ~drop；union ∧ base；mean ∧ ~drop）
  acct        名单 → e6i_sparse.SparseEngine.dev + pnl 多 H（bincount / cumsum 顺序累加；numpy 行和的 pairwise 求和逐位复刻：
              结果 = 0.0 + pairwise(全行)，块长 128、八路展开——Stage 0 在 47 NumPy 1.26.1 上核 1,200 行 0 差）"""
import numpy as np
import numba as nb

import e6i_randoms as IR

NJ = dict(cache=True, error_model='numpy', nogil=True)
STAMP0 = -1000000
KIND_CODE = {'A4b': 0, 'union': 1, 'mean': 2}


# ====================================================================== numpy pairwise 行和
@nb.njit(**NJ)
def _pairwise(a, lo, n):
    """numpy pairwise_sum 的非递归实现（numba 缓存递归函数会段错误）：显式栈后序求值，每个内部结点 = 左 + 右（同一棵树）。"""
    if n <= 128:
        return _block(a, lo, n)
    slo = np.empty(128, np.int64)
    sn = np.empty(128, np.int64)
    sst = np.zeros(128, np.int64)
    vs = np.empty(128)
    top = 0
    nv = 0
    slo[0] = lo
    sn[0] = n
    sst[0] = 0
    while top >= 0:
        l0 = slo[top]
        nn = sn[top]
        if nn <= 128:
            vs[nv] = _block(a, l0, nn)
            nv += 1
            top -= 1
        elif sst[top] == 0:
            sst[top] = 1
            n2 = nn // 2
            n2 -= n2 % 8
            slo[top + 1] = l0 + n2
            sn[top + 1] = nn - n2
            sst[top + 1] = 0
            slo[top + 2] = l0
            sn[top + 2] = n2
            sst[top + 2] = 0
            top += 2
        else:
            r = vs[nv - 1]
            left = vs[nv - 2]
            nv -= 2
            vs[nv] = left + r
            nv += 1
            top -= 1
    return vs[0]


@nb.njit(**NJ)
def _block(a, lo, n):
    if n < 8:
        res = 0.0
        for i in range(n):
            res += a[lo + i]
        return res
    else:
        r0 = a[lo]
        r1 = a[lo + 1]
        r2 = a[lo + 2]
        r3 = a[lo + 3]
        r4 = a[lo + 4]
        r5 = a[lo + 5]
        r6 = a[lo + 6]
        r7 = a[lo + 7]
        i = 8
        lim = n - (n % 8)
        while i < lim:
            r0 += a[lo + i]
            r1 += a[lo + i + 1]
            r2 += a[lo + i + 2]
            r3 += a[lo + i + 3]
            r4 += a[lo + i + 4]
            r5 += a[lo + i + 5]
            r6 += a[lo + i + 6]
            r7 += a[lo + i + 7]
            i += 8
        res = ((r0 + r1) + (r2 + r3)) + ((r4 + r5) + (r6 + r7))
        while i < n:
            res += a[lo + i]
            i += 1
        return res


@nb.njit(**NJ)
def rowsum(a):
    return 0.0 + _pairwise(a, 0, len(a))


# ====================================================================== DEV + 多 H 账本
@nb.njit(**NJ)
def dev_nb(t, c, T, icd, capd, G, max_stock):
    """= SparseEngine.dev（同式、同顺序；行业和 = w0 顺序累加 cnt 次）。"""
    n = len(t)
    w = np.empty(n)
    if n == 0:
        return w
    cnt_t = np.zeros(T, np.int64)
    for i in range(n):
        cnt_t[t[i]] += 1
    gcnt = np.zeros(T * G, np.int64)
    for i in range(n):
        ic = icd[t[i], c[i]]
        if ic >= 0:
            gcnt[t[i] * G + ic] += 1
    for i in range(n):
        x = 1.0 / cnt_t[t[i]]
        w0 = x if x <= max_stock else max_stock
        ic = icd[t[i], c[i]]
        if ic >= 0:
            k = gcnt[t[i] * G + ic]
            gs = w0
            for _ in range(1, k):
                gs += w0
            capv = capd[t[i], ic]
            if gs > capv:
                w[i] = w0 * (capv / gs)
            else:
                w[i] = w0
        else:
            w[i] = w0
    return w


@nb.njit(**NJ)
def pnl_nb(t, c, w, Hs, T, r0T, bench, cost, Wd, out):
    """= SparseEngine.pnl（Hs 升序；单元按 (t, c) 升序给出）；out (len(Hs), 4, T) ← gross / pos / turn / net。
    与源同一累加次序：日和 / 滞后收益每个箱只收一个形成日的批次（单元序顺加）；换手 min 项按 (t, c) 有序归并（非命中 = + 0.0，
    对非负和不改值）；前 je + 1 行的稠密差分只在该段有名单时算（Wd：(T, Nc) 零矩阵，只用前 Hmax + 1 行，用后复零）。"""
    n = len(t)
    nH = len(Hs)
    if n == 0:
        for h in range(nH):
            for j in range(T):
                z = 0.0 - bench[j] * 0.0
                out[h, 0, j] = z
                out[h, 1, j] = 0.0
                out[h, 2, j] = 0.0
                out[h, 3, j] = z
        return
    Hmax = Hs[nH - 1]
    Nc = Wd.shape[1]
    doff = np.zeros(T + 1, np.int64)
    for i in range(n):
        doff[t[i] + 1] += 1
    for j in range(T):
        doff[j + 1] += doff[j]
    sw = np.zeros(T)
    for i in range(n):
        sw[t[i]] += w[i]
    Q = np.zeros((Hmax, T))
    acc = np.zeros(Hmax)
    tmin = t[0]
    for tau in range(T):
        i0 = doff[tau]
        i1 = doff[tau + 1]
        if i1 == i0:
            continue
        if tau < tmin:
            tmin = tau
        nl = Hmax
        if tau + 2 + nl > T:
            nl = T - tau - 2
        if nl <= 0:
            continue
        for l in range(nl):
            acc[l] = 0.0
        for i in range(i0, i1):
            base = c[i] * T + tau + 2
            wi = w[i]
            for l in range(nl):
                acc[l] += wi * r0T[base + l]
        for l in range(nl):
            Q[l, tau + 2 + l] = acc[l]
    for l in range(1, Hmax):
        for j in range(T):
            Q[l, j] = Q[l - 1, j] + Q[l, j]
    wrow = Hmax + 1 if Hmax + 1 < T else T
    for i in range(n):
        if t[i] < wrow:
            Wd[t[i], c[i]] = w[i]
    port = np.zeros(T)
    pos = np.zeros(T)
    turn = np.zeros(T)
    rs = np.zeros(T)
    d = np.zeros(T)
    Acum = np.zeros(Nc)
    act_prev = np.zeros(Nc)
    act_cur = np.zeros(Nc)
    buf = np.zeros(Nc)
    M = np.zeros(T)
    for h in range(nH):
        H = Hs[h]
        for j in range(T):
            port[j] = 0.0
            pos[j] = 0.0
            turn[j] = 0.0
        if T > 2:
            for j in range(2, T):
                dn = j - 1 if j - 1 < H else H
                port[j] = Q[H - 1, j] / dn
            for j in range(T):
                rs[j] = sw[j]
            for k in range(1, H):
                if k >= T:
                    break
                for j in range(k, T):
                    rs[j] += sw[j - k]
            for j in range(2, T):
                dn = j - 1 if j - 1 < H else H
                pos[j] = rs[j - 2] / dn
        if T > 3:
            for j in range(T):
                d[j] = 0.0
            je = H if H < T - 1 else T - 1
            if tmin <= je:
                for col in range(Nc):
                    Acum[col] = Wd[0, col]
                    act_prev[col] = Acum[col] / 1.0
                for r in range(1, je + 1):
                    dr = r + 1 if r + 1 < H else H
                    for col in range(Nc):
                        Acum[col] = Acum[col] + Wd[r, col]
                        if r == H:
                            av = Acum[col] - Wd[0, col]
                        else:
                            av = Acum[col]
                        act_cur[col] = av / dr
                        buf[col] = abs(act_cur[col] - act_prev[col])
                    d[r] = 0.0 + _pairwise(buf, 0, Nc)
                    for col in range(Nc):
                        act_prev[col] = act_cur[col]
            if T - 1 > H:
                for j in range(T):
                    M[j] = 0.0
                for j in range(H + 1, T):
                    i0 = doff[j]
                    i1 = doff[j + 1]
                    k = doff[j - H]
                    k1 = doff[j - H + 1]
                    for i in range(i0, i1):
                        ci_ = c[i]
                        while k < k1 and c[k] < ci_:
                            k += 1
                        if k < k1 and c[k] == ci_:
                            x = w[k]
                            wi = w[i]
                            M[j] += wi if wi <= x else x
                for j in range(H + 1, T):
                    d[j] = (sw[j] + sw[j - H] - 2.0 * M[j]) / H
            for j in range(3, T):
                turn[j] = 0.5 * d[j - 2]
        for j in range(T):
            g = port[j] - bench[j] * pos[j]
            out[h, 0, j] = g
            out[h, 1, j] = pos[j]
            out[h, 2, j] = turn[j]
            out[h, 3, j] = g - turn[j] * cost
    for i in range(n):
        if t[i] < wrow:
            Wd[t[i], c[i]] = 0.0


@nb.njit(**NJ)
def acct_nb(Frow, ci_t, ci_c, T, icd, capd, G, max_stock, Hs, r0T, bench, cost, Wd, out):
    """一条最终名单（pool0 单元 bool）→ DEV → 多 H 账本；返回名单格数。"""
    n = 0
    for i in range(len(Frow)):
        if Frow[i]:
            n += 1
    t = np.empty(n, np.int64)
    c = np.empty(n, np.int64)
    k = 0
    for i in range(len(Frow)):
        if Frow[i]:
            t[k] = ci_t[i]
            c[k] = ci_c[i]
            k += 1
    w = dev_nb(t, c, T, icd, capd, G, max_stock)
    pnl_nb(t, c, w, Hs, T, r0T, bench, cost, Wd, out)
    return n


# ====================================================================== 第二关与下游
@nb.njit(**NJ)
def _stage2(cells, nc, logm, Traw, kof, keep, vbuf, vals, ibuf):
    """一日 s1（cells[:nc]，升序单元号）→ keep[:nc]（dep_stage2_keep 同式）。返回保留数。"""
    for j in range(nc):
        keep[j] = False
    nv = 0.0
    sx = 0.0
    sy = 0.0
    for j in range(nc):
        x = logm[cells[j]]
        y = Traw[cells[j]]
        if np.isfinite(y) and np.isfinite(x):
            nv += 1.0
            sx += x
            sy += y
    xm = sx / nv
    ym = sy / nv
    sxx = 0.0
    sxy = 0.0
    for j in range(nc):
        x = logm[cells[j]]
        y = Traw[cells[j]]
        if np.isfinite(y) and np.isfinite(x):
            dx = x - xm
            dy = y - ym
            sxx += dx * dx
            sxy += dx * dy
    var = sxx / nv
    cov = sxy / nv
    beta = cov / var
    alpha = ym - beta * xm
    use_raw = nv < 10
    nfin = 0
    for j in range(nc):
        x = logm[cells[j]]
        y = Traw[cells[j]]
        val = np.nan
        if use_raw:
            if np.isfinite(y):
                val = y
        elif np.isfinite(y) and np.isfinite(x):
            val = y - (alpha + beta * x)
        vbuf[j] = val
        if np.isfinite(val):
            nfin += 1
    if nc < 6 or nfin < 6:
        return 0
    k = 0
    for j in range(nc):
        if np.isfinite(vbuf[j]):
            ibuf[k] = j
            vals[k] = vbuf[j]
            k += 1
    o = np.argsort(vals[:k], kind='mergesort')
    Kg = kof[k]
    for q in range(Kg):
        keep[ibuf[o[q]]] = True
    return Kg


@nb.njit(**NJ)
def _down_day(p, a, m, gate, ids, kind, drop, base, logm, Traw, kof, F, cells, keep, vbuf, vals, ibuf, fin_cells):
    """门（gate[a:a+m] 位置）→ 该日最终名单写 F[p]；返回最终单元数（单元号写 fin_cells）。"""
    nc = 0
    for r in range(m):
        if gate[a + r]:
            cells[nc] = ids[a + r]
            nc += 1
    nf = 0
    if kind == 0:
        if nc > 0:
            _stage2(cells, nc, logm, Traw, kof, keep, vbuf, vals, ibuf)
            for j in range(nc):
                if keep[j] and not drop[cells[j]]:
                    F[p, cells[j]] = True
                    fin_cells[nf] = cells[j]
                    nf += 1
    elif kind == 1:
        for j in range(nc):
            if base[cells[j]]:
                F[p, cells[j]] = True
                fin_cells[nf] = cells[j]
                nf += 1
    else:
        for j in range(nc):
            if not drop[cells[j]]:
                F[p, cells[j]] = True
                fin_cells[nf] = cells[j]
                nf += 1
    return nf


@nb.njit(**NJ)
def down_nb(Gt, off, K, ids, kind, drop, base, logm, Traw, kof, n):
    """门 (P, N) → 最终名单 (P, n)（Struct.down 同式）。"""
    P, N = Gt.shape
    T = len(K)
    F = np.zeros((P, n), np.bool_)
    mmax = 1
    for d in range(T):
        if off[d + 1] - off[d] > mmax:
            mmax = off[d + 1] - off[d]
    cells = np.empty(mmax, np.int64)
    keep = np.zeros(mmax, np.bool_)
    vbuf = np.empty(mmax)
    vals = np.empty(mmax)
    ibuf = np.empty(mmax, np.int64)
    fin = np.empty(mmax, np.int64)
    for p in range(P):
        g = Gt[p]
        for d in range(T):
            a = off[d]
            m = off[d + 1] - a
            if m == 0:
                continue
            _down_day(p, a, m, g, ids, kind, drop, base, logm, Traw, kof, F, cells, keep, vbuf, vals, ibuf, fin)
    return F


# ====================================================================== 门层递推
@nb.njit(**NJ)
def _select_single(p, a, m, Kd, be, mark, sc, O, U, G, mpos, upos, mv):
    """单一折让水平：mark[:m]（位置）→ G[p, a:a+m]。= stable argsort(s − be·mark)[:K]；无标记或 be = 0 → U。"""
    nm = 0
    nu = 0
    for r in range(m):
        i = O[p, a + r]
        if mark[i] and be != 0.0:
            mpos[nm] = i
            nm += 1
        else:
            upos[nu] = i
            nu += 1
    if nm == 0:
        for r in range(m):
            G[p, a + r] = U[p, a + r]
        return
    for j in range(nm):
        mv[j] = sc[p, a + mpos[j]] - be
    j = 0
    while j < nm:                                    # 舍入并列段按位置重排
        k = j + 1
        while k < nm and mv[k] == mv[j]:
            k += 1
        if k - j > 1:
            for x in range(j + 1, k):
                key = mpos[x]
                y = x - 1
                while y >= j and mpos[y] > key:
                    mpos[y + 1] = mpos[y]
                    y -= 1
                mpos[y + 1] = key
        j = k
    ia = 0
    ib = 0
    for _ in range(Kd):
        takeA = False
        if ia < nm:
            if ib >= nu:
                takeA = True
            else:
                va = mv[ia]
                vb = sc[p, a + upos[ib]] - 0.0
                if va < vb or (va == vb and mpos[ia] < upos[ib]):
                    takeA = True
        if takeA:
            G[p, a + mpos[ia]] = True
            ia += 1
        else:
            G[p, a + upos[ib]] = True
            ib += 1


@nb.njit(**NJ)
def rec_single(sc, O, U, off, K, cols, be_day, Nc, lag):
    """HG / STATE（lag = 0：标记 = 本路径 G_{t−1}）与 LAG1（lag = 1：标记 = U_{t−1}）。返回门 (P, N)。"""
    P, N = sc.shape
    T = len(K)
    G = np.zeros((P, N), np.bool_)
    mmax = 1
    for d in range(T):
        if off[d + 1] - off[d] > mmax:
            mmax = off[d + 1] - off[d]
    mpos = np.empty(mmax, np.int64)
    upos = np.empty(mmax, np.int64)
    mv = np.empty(mmax)
    mark = np.zeros(mmax, np.bool_)
    gst = np.empty(Nc, np.int64)
    ust = np.empty(Nc, np.int64)
    for p in range(P):
        gst[:] = STAMP0
        ust[:] = STAMP0
        for d in range(T):
            a = off[d]
            m = off[d + 1] - a
            if m == 0 or K[d] == 0:
                continue
            for r in range(m):
                col = cols[a + r]
                mark[r] = (ust[col] == d - 1) if lag else (gst[col] == d - 1)
            _select_single(p, a, m, K[d], be_day[d], mark, sc, O, U, G, mpos, upos, mv)
            for r in range(m):
                col = cols[a + r]
                if G[p, a + r]:
                    gst[col] = d
                if U[p, a + r]:
                    ust[col] = d
    return G


@nb.njit(**NJ)
def rec_rmark(sc, O, U, off, K, cols, be_day, Nc, grp, uu):
    """R-MARK：本路径 G_{t−1} 在当日分组（grp：逐日重编 0..）内按 key = g·2 + (1 − u) 稳定序的前 m_g 名得标记，再单一折让。"""
    P, N = sc.shape
    T = len(K)
    G = np.zeros((P, N), np.bool_)
    mmax = 1
    for d in range(T):
        if off[d + 1] - off[d] > mmax:
            mmax = off[d + 1] - off[d]
    mpos = np.empty(mmax, np.int64)
    upos = np.empty(mmax, np.int64)
    mv = np.empty(mmax)
    mark = np.zeros(mmax, np.bool_)
    prevm = np.zeros(mmax, np.bool_)
    key = np.empty(mmax)
    mg = np.zeros(mmax + 1, np.int64)
    cg = np.zeros(mmax + 1, np.int64)
    gst = np.empty(Nc, np.int64)
    for p in range(P):
        gst[:] = STAMP0
        for d in range(T):
            a = off[d]
            m = off[d + 1] - a
            if m == 0 or K[d] == 0:
                continue
            ng = 0
            for r in range(m):
                if grp[a + r] + 1 > ng:
                    ng = grp[a + r] + 1
            for g in range(ng):
                mg[g] = 0
                cg[g] = 0
            for r in range(m):
                prevm[r] = gst[cols[a + r]] == d - 1
                if prevm[r]:
                    mg[grp[a + r]] += 1
                key[r] = grp[a + r] * 2.0 + (1.0 - uu[p, a + r])
                mark[r] = False
            o = np.argsort(key[:m], kind='mergesort')
            for q in range(m):
                r = o[q]
                g = grp[a + r]
                if cg[g] < mg[g]:
                    mark[r] = True
                cg[g] += 1
            _select_single(p, a, m, K[d], be_day[d], mark, sc, O, U, G, mpos, upos, mv)
            for r in range(m):
                if G[p, a + r]:
                    gst[cols[a + r]] = d
    return G


@nb.njit(**NJ)
def rec_decay(sc, U, off, K, cols, be_day, Nc, L, Linf):
    """DECAY：bon = (be·1(G_{t−1}))·fac，fac = max(0, 1 − max(age − 1, 0)/L)（age 无限 → 0；L 无穷 → 1）；逐日稳定排序。"""
    P, N = sc.shape
    T = len(K)
    G = np.zeros((P, N), np.bool_)
    mmax = 1
    for d in range(T):
        if off[d + 1] - off[d] > mmax:
            mmax = off[d + 1] - off[d]
    v = np.empty(mmax)
    gst = np.empty(Nc, np.int64)
    domst = np.empty(Nc, np.int64)
    spell = np.empty(Nc, np.int64)
    last = np.empty(Nc)
    for p in range(P):
        gst[:] = STAMP0
        domst[:] = STAMP0
        spell[:] = 0
        last[:] = -np.inf
        for d in range(T):
            a = off[d]
            m = off[d + 1] - a
            if m == 0 or K[d] == 0:
                continue
            be = be_day[d]
            for r in range(m):
                col = cols[a + r]
                if domst[col] != d - 1:
                    spell[col] = d
                domst[col] = d
            for r in range(m):
                if U[p, a + r]:
                    last[cols[a + r]] = d
            anynz = False
            for r in range(m):
                col = cols[a + r]
                prevf = 1.0 if gst[col] == d - 1 else 0.0
                lc = last[col]
                if lc >= spell[col]:
                    age = d - lc
                    if Linf:
                        fac = 1.0
                    else:
                        x = age - 1.0
                        x = x if x >= 0.0 else 0.0
                        y = 1.0 - x / L
                        fac = 0.0 if 0.0 >= y else y
                else:
                    fac = 0.0
                bon = be * prevf * fac
                v[r] = sc[p, a + r] - bon
                if bon != 0.0:
                    anynz = True
            if anynz:
                o = np.argsort(v[:m], kind='mergesort')
                for q in range(K[d]):
                    G[p, a + o[q]] = True
            else:
                for r in range(m):
                    G[p, a + r] = U[p, a + r]
            for r in range(m):
                if G[p, a + r]:
                    gst[cols[a + r]] = d
    return G


@nb.njit(**NJ)
def rec_inv(sc, O, U, off, K, cols, ids, be, H, Nc, n, kind, drop, base, logm, Traw, kof):
    """INV：标记 = 本路径最终名单在形成日 [T − H, T − 1] 的批次计数 > 0；门 → 逐日下游 → 批次在 d + H + 1 日退出。
    返回 (门 (P, N), 最终名单 (P, n))。"""
    P, N = sc.shape
    T = len(K)
    G = np.zeros((P, N), np.bool_)
    F = np.zeros((P, n), np.bool_)
    mmax = 1
    for d in range(T):
        if off[d + 1] - off[d] > mmax:
            mmax = off[d + 1] - off[d]
    mpos = np.empty(mmax, np.int64)
    upos = np.empty(mmax, np.int64)
    mv = np.empty(mmax)
    mark = np.zeros(mmax, np.bool_)
    cells = np.empty(mmax, np.int64)
    keep = np.zeros(mmax, np.bool_)
    vbuf = np.empty(mmax)
    vals = np.empty(mmax)
    ibuf = np.empty(mmax, np.int64)
    fin = np.empty(mmax, np.int64)
    cnt = np.zeros(Nc, np.int64)
    for p in range(P):
        cnt[:] = 0
        for d in range(T):
            dd = d - H - 1
            if dd >= 0:                                  # 形成日 d − H − 1 的批次退出窗口 [d − H, d − 1]
                a0 = off[dd]
                m0 = off[dd + 1] - a0
                for r in range(m0):
                    if F[p, ids[a0 + r]]:
                        cnt[cols[a0 + r]] -= 1
            a = off[d]
            m = off[d + 1] - a
            if m == 0 or K[d] == 0:
                continue
            for r in range(m):
                mark[r] = cnt[cols[a + r]] > 0
            _select_single(p, a, m, K[d], be, mark, sc, O, U, G, mpos, upos, mv)
            nf = _down_day(p, a, m, G[p], ids, kind, drop, base, logm, Traw, kof, F, cells, keep, vbuf, vals, ibuf, fin)
            for r in range(m):
                if F[p, ids[a + r]]:
                    cnt[cols[a + r]] += 1
    return G, F


# ====================================================================== Python 包装
def order_U(sc, off, K):
    """(P, N) 门分数 → 逐日稳定全序 O（当日内位置，int64）与无带门 U（= KeepDom.keep）。K = 0 的日子 O 不用。"""
    P, N = sc.shape
    O = np.zeros((P, N), np.int64)
    U = np.zeros((P, N), bool)
    for d in np.flatnonzero(K > 0):
        a, b = off[d], off[d + 1]
        o = np.argsort(sc[:, a:b], axis=1, kind='stable')
        O[:, a:b] = o
        np.put_along_axis(U[:, a:b], o[:, :K[d]], True, axis=1)
    return O, U


def kof_table(b, nmax):
    return np.array([IR.k_of(int(n), b) if n else 0 for n in range(nmax + 1)], np.int64)


class StructFast(object):
    """一个 Struct 的 numba 输入（与路径无关，算一次）。"""

    def __init__(self, st):
        seg = st.seg
        self.st = st
        self.kind = KIND_CODE[st.kind]
        self.off = np.asarray(st.dom.off, np.int64)
        self.K = np.asarray(st.dom.K, np.int64)
        self.ids = np.asarray(st.ids, np.int64)
        self.cols = np.asarray(seg.ci.c[st.ids], np.int64)
        self.Nc = int(seg.Nc)
        self.n = int(seg.n)
        s = st.st
        self.drop = np.ascontiguousarray(getattr(s, 'drop', np.zeros(seg.n, bool)), dtype=np.bool_)
        self.base = np.ascontiguousarray(getattr(s, 'base', np.ones(seg.n, bool)), dtype=np.bool_)
        self.logm = np.ascontiguousarray(seg.env.R.logm_c, dtype=np.float64)
        if st.kind == 'A4b':
            self.Traw = np.ascontiguousarray(s.M.T_raw_c, dtype=np.float64)
            mm = int(np.diff(self.off).max()) if len(self.off) > 1 else 1
            self.kof = kof_table(s.b, max(mm, 16))
        else:
            self.Traw = np.zeros(1)
            self.kof = np.zeros(1, np.int64)

    def down(self, Gt):
        return down_nb(np.ascontiguousarray(Gt), self.off, self.K, self.ids, self.kind, self.drop, self.base, self.logm, self.Traw,
                       self.kof, self.n)


class AcctFast(object):
    """一个段的账本输入（与路径无关）。"""

    def __init__(self, seg):
        SE = seg.SE
        import e6e_core as EE
        self.T = int(SE.T)
        self.Nc = int(SE.Nc)
        self.icd = np.ascontiguousarray(np.asarray(SE.ic), dtype=np.int64)
        self.capd = np.ascontiguousarray(np.asarray(SE.cap), dtype=np.float64)
        self.G = int(SE.G)
        self.max_stock = float(EE.MAX_STOCK)
        self.r0T = SE.r0T
        self.bench = np.ascontiguousarray(SE.bench, dtype=np.float64)
        self.ci_t = np.asarray(seg.ci.t, np.int64)
        self.ci_c = np.asarray(seg.ci.c, np.int64)
        self.Wd = np.zeros((self.T, self.Nc))

    def run(self, Frow, Hs, cost_bp=8.0):
        Hs = np.asarray(sorted(set(int(h) for h in Hs)), np.int64)
        out = np.empty((len(Hs), 4, self.T))
        nn = acct_nb(np.ascontiguousarray(Frow), self.ci_t, self.ci_c, self.T, self.icd, self.capd, self.G, self.max_stock, Hs, self.r0T,
                     self.bench, cost_bp / 1e4, self.Wd, out)
        return out, nn


def warmup():
    """父进程 fork 前编译（缓存在 NUMBA_CACHE_DIR）。"""
    a = np.array([0.0, 1.0])
    rowsum(a)
    T, Nc = 8, 3
    t = np.array([0, 2, 5], np.int64)
    c = np.array([0, 1, 2], np.int64)
    icd = np.zeros((T, Nc), np.int64)
    capd = np.ones((T, 1))
    w = dev_nb(t, c, T, icd, capd, 1, 0.1)
    out = np.empty((2, 4, T))
    pnl_nb(t, c, w, np.array([1, 2], np.int64), T, np.zeros(T * Nc), np.zeros(T), 8e-4, np.zeros((T, Nc)), out)
    F = np.zeros(3, np.bool_)
    F[1] = True
    acct_nb(F, t, c, T, icd, capd, 1, 0.1, np.array([1], np.int64), np.zeros(T * Nc), np.zeros(T), 8e-4, np.zeros((T, Nc)), out[:1])
    return True
