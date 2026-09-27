# -*- coding: utf-8 -*-
"""E6j 随机层提速件（2026-09-27 06:xx，用户同意提速与放宽并发之后）。只换算法路径，结果与原实现逐位相同，
由 e6j_test_fast.py 在真实数据上逐格核对（六形态 × 四臂 × 七机制 × 三 α；B 各母体槽位 × 三机制 × 全部组合）：
  Assigner      e6j_random.assign_by_priority 的缓存版：值序 o_v 与路径无关只算一次；日格（0 ≤ cellid < 2048）的 u 序
                用单键 uint64 稳定排序：u = k·2^-53（k < 2^53 整数，精确），键 = cellid<<53 | (2^53−1−k)，
                与 lexsort((−u, cellid)) 同序（含平局按原下标）；其余格仍用 lexsort
  DonorMapper   e6j_run_brand.donor_map 的缓存版（同上）
  stage2_fast   e6i_randoms.dep_stage2_keep 的逐路径版：每 (路径, 日) 组内 padded 2D 稳定排序代替全局 lexsort；
                bincount 累加次序与原批量版逐组相同（原版组内元素次序 = 该路径该日的单元升序），秩 / 分位 / 选取同式
  EditPlan      EDIT-ENTRY / EDIT-BOTH：候选、需求、各层联合组号与路径无关先算；每路径只算 u 与配额抽样；
                配额为 0 的组不进排序（这些候选永不入选，不改其余组内名次）；输出直接在单元坐标"""
import numpy as np

import e6j_random as RND
import e6i_randoms as IR

_TWO53 = 9007199254740992.0
_LOW = np.uint64((1 << 53) - 1)
_SH = np.uint64(53)


def order_u_desc(cellid, u, small):
    """与 np.lexsort((-u, cellid)) 相同的次序。small = cellid 全在 [0, 2048)。"""
    if small:
        k = (u * _TWO53).astype(np.uint64)                   # u 是 2^-53 的整数倍：乘法与取整都精确
        key = (cellid.astype(np.uint64) << _SH) | (_LOW - k)
        return np.argsort(key, kind='stable')
    return np.lexsort((-u, cellid))


def _small(cellid):
    return bool(len(cellid) == 0 or (int(cellid.min()) >= 0 and int(cellid.max()) < 2048))


class Assigner(object):
    """同一 (vals, cellid) 与不同路径 u 配对：u 降序第 k 个得 vals 降序第 k 个（同 assign_by_priority）。"""

    def __init__(self, vals, cellid):
        self.cellid = np.asarray(cellid, dtype=np.int64)
        self.small = _small(self.cellid)
        self.vs = vals[np.lexsort((-vals, self.cellid))]
        self.n, self.dtype = len(vals), vals.dtype

    def __call__(self, u):
        out = np.empty(self.n, dtype=self.dtype)
        out[order_u_desc(self.cellid, u, self.small)] = self.vs
        return out


class DonorMapper(object):
    """同 e6j_run_brand.donor_map：cell 内 u 降序第 k 个 recipient ← vals_hi 降序第 k 个 donor；vals_hi 序缓存。"""

    def __init__(self, vals_hi, cell):
        self.cell = np.asarray(cell, dtype=np.int64)
        self.small = _small(self.cell)
        self.o_v = np.lexsort((-vals_hi, self.cell))

    def __call__(self, u):
        don = np.empty(len(self.o_v), dtype=np.int64)
        don[order_u_desc(self.cell, u, self.small)] = self.o_v
        return don


def stage2_fast(R, M, s1b, pctkeep_b):
    """= IR.dep_stage2_keep(R, M, s1b, pctkeep_b)，逐路径计算。"""
    ci = R.ci
    P, n = s1b.shape
    T = ci.T
    kept = np.zeros((P, n), bool)
    logm, Traw, ct, cc_all = R.logm_c, M.T_raw_c, ci.t, ci.c
    for p in range(P):
        cid = np.flatnonzero(s1b[p])
        if not len(cid):
            continue
        t = ct[cid]
        npool = np.bincount(t, minlength=T)
        x = logm[cid]; y = Traw[cid]
        fy = np.isfinite(y)
        valid = fy & np.isfinite(x)
        nv = np.bincount(t, weights=valid.astype(float), minlength=T)
        tv, xv, yv = t[valid], x[valid], y[valid]
        with np.errstate(all='ignore'):
            xm = np.bincount(tv, weights=xv, minlength=T) / nv
            ym = np.bincount(tv, weights=yv, minlength=T) / nv
            dx = xv - xm[tv]
            dy = yv - ym[tv]
            var = np.bincount(tv, weights=dx * dx, minlength=T) / nv
            cov = np.bincount(tv, weights=dx * dy, minlength=T) / nv
            beta = cov / var
            alpha = ym - beta * xm
        use_raw = nv[t] < 10
        val = np.full(len(cid), np.nan)
        a_ = use_raw & fy
        val[a_] = y[a_]
        r_ = (~use_raw) & valid
        with np.errstate(all='ignore'):
            val[r_] = y[r_] - (alpha[t[r_]] + beta[t[r_]] * x[r_])
        fv = np.isfinite(val)
        nfin = np.bincount(t[fv], minlength=T)
        ok = fv & (npool[t] >= 6) & (nfin[t] >= 6)
        tk, vv, cc = t[ok], val[ok], cid[ok]
        if not len(tk):
            continue
        ng = np.bincount(tk, minlength=T)
        off = np.r_[0, np.cumsum(ng)]
        pos = np.arange(len(tk)) - off[tk]
        L = int(ng.max())
        V = np.full((T, L), np.inf)
        V[tk, pos] = vv
        o = np.argsort(V, axis=1, kind='stable')             # 组内升序（平局按组内原次序），+inf 填充在后
        sv = np.take_along_axis(V, o, axis=1)
        col = np.broadcast_to(np.arange(L)[None, :], (T, L))
        newr = np.ones((T, L), bool)
        newr[:, 1:] = sv[:, 1:] != sv[:, :-1]
        endr = np.ones((T, L), bool)
        endr[:, :-1] = sv[:, 1:] != sv[:, :-1]
        first = np.maximum.accumulate(np.where(newr, col, 0), axis=1)
        last = np.minimum.accumulate(np.where(endr, col, L - 1)[:, ::-1], axis=1)[:, ::-1]
        rank = (first + last) / 2.0 + 1.0
        with np.errstate(all='ignore'):
            pct_sorted = rank / ng[:, None]
        PCT = np.full((T, L), np.inf)
        np.put_along_axis(PCT, o, pct_sorted, axis=1)
        PCT[col >= ng[:, None]] = np.inf
        o2 = np.argsort(PCT, axis=1, kind='stable')          # 源 keep：(pct, 列) 升序；组内原次序 = 列升序
        Kg = np.zeros(T, np.int64)
        for d in np.flatnonzero(ng):
            Kg[d] = IR.k_of(int(ng[d]), pctkeep_b)
        rs, cs = np.nonzero(col < Kg[:, None])
        kept[p, cc[off[rs] + o2[rs, cs]]] = True
    return kept


class _LevelPlan(object):
    """_pick_levels 的路径无关部分：各层（候选 ∪ 需求）联合组号。"""

    def __init__(self, cr, cc, nr, nc_, ind, k3):
        self.nc, self.nn = len(cr), len(nr)
        self.need_rows = nr
        ck = RND._level_keys(cr, cc, ind, k3)
        nk = RND._level_keys(nr, nc_, ind, k3)
        self.labc, self.labn, self.G = [], [], []
        for L in range(len(ck)):
            allk = np.vstack([ck[L], nk[L]])
            if len(allk):
                _, inv = np.unique(allk, axis=0, return_inverse=True)
                inv = inv.ravel()
                g = int(inv.max()) + 1
            else:
                inv, g = np.zeros(0, np.int64), 0
            self.labc.append(inv[:self.nc]); self.labn.append(inv[self.nc:]); self.G.append(g)

    def pick(self, u):
        taken = np.zeros(self.nc, bool)
        need_left = np.ones(self.nn, bool)
        for L in range(len(self.labc)):
            if not need_left.any():
                break
            nidx = np.flatnonzero(need_left)
            ineed = self.labn[L][nidx]
            quota = np.bincount(ineed, minlength=self.G[L])
            lc = self.labc[L]
            avail = np.flatnonzero(~taken & (quota[lc] > 0))
            ic = lc[avail]
            o = np.lexsort((-u[avail], ic))
            rk = np.empty(len(avail), dtype=np.int64)
            rk[o] = RND._rank_within(ic[o])
            sel = rk < quota[ic]
            taken[avail[sel]] = True
            got = np.bincount(ic[sel], minlength=self.G[L])
            sat = RND._rank_within(ineed) < got[ineed]
            need_left[nidx[sat]] = False
        short = np.bincount(self.need_rows[need_left]) if need_left.any() else np.zeros(0, dtype=np.int64)
        return np.flatnonzero(taken), short


class EditPlan(object):
    """一个 (父, 真实子, 合法域) 的 EDIT 计划（单元坐标进出）。both=True 另备 EDIT-BOTH 的换出计划。"""

    def __init__(self, ci, ind, k3, parent_c, child_c, legal_c, both=False):
        T, Nc = ci.T, ci.Nc

        def dense(b):
            A = np.zeros((T, Nc), bool); A[ci.t[b], ci.c[b]] = True
            return A
        P_, C_, L_ = dense(parent_c), dense(child_c), dense(legal_c)
        cmap = np.full((T, Nc), -1, np.int64); cmap[ci.t, ci.c] = np.arange(ci.n)
        cr, cc = np.nonzero(L_ & ~P_)
        ar, ac = np.nonzero(C_ & ~P_)
        self.cand_rc = (cr, cc)
        self.inp = _LevelPlan(cr, cc, ar, ac, ind, k3)
        self.in_cells = cmap[cr, cc]
        self.I_cells = np.flatnonzero(parent_c & child_c)
        self.parent_c = parent_c
        self.n = ci.n
        if both:
            dr, dc = np.nonzero(P_ & ~C_)
            br, bc = np.nonzero(P_)
            self.par_rc = (br, bc)
            self.outp = _LevelPlan(br, bc, dr, dc, ind, k3)
            self.par_cells = cmap[br, bc]
        if (self.in_cells < 0).any() or (both and (self.par_cells < 0).any()):
            raise RuntimeError('EDIT 候选落在 pool0 单元之外')

    def entry(self, u_in):
        chosen, _ = self.inp.pick(u_in)
        m = np.zeros(self.n, bool)
        m[self.I_cells] = True
        m[self.in_cells[chosen]] = True
        return m

    def both(self, u_out, u_in):
        dsel, _ = self.outp.pick(u_out)
        m = self.parent_c.copy()
        m[self.par_cells[dsel]] = False
        asel, _ = self.inp.pick(u_in)
        m[self.in_cells[asel]] = True
        return m
