# -*- coding: utf-8 -*-
"""E6j 批量账户引擎（P 块生产六形态 + B 块研究母体 R1 / R2 / A06 / A08）。

复用 E6i 已锚部件（只 import、不改）：`e6i_randoms.Cells / KeepDom / dep_stage2_keep / RCtx`（pool0 单元、源 keep 的批量版、
R1 第二阶段在新 S1 内按源口径重中性化的批量版）与 `e6i_sparse.SparseEngine`（DEV 与源逐位、账本与稠密引擎 ≤ 1e−12）。
E6j 新增：生产 Mmean_v2 / Munion_v2（± CVRv5）的批量结构；A4b（无否决）= R1 结构去掉否决；K / T 槽位 q 的批量构造
（FALLBACK 单臂 / SM / AMT4 / 数组 α 可靠性 / COMMON_SUPPORT）；E6j 随机库（e6j_random 稳定哈希）。
一切结构都在"单元"坐标（pool0 的 (t, c) 字典序）上运算；P × n 批量（P 条路径同批）。
恒等锚（engine_anchor）：q = q0 时每个结构 = 源母体掩码逐格；S / M / C1 α .25 = 生产 arm_masks / E6i Mother.slot 逐格；
DEV = 生产 assign_weights_dev 逐位；账本与生产 compute_calendar_pnl ≤ 1e−12。锚不过，本模块不许用于账户。"""
import e6j_boot  # noqa: F401
import numpy as np
import pandas as pd

import e6j_core as J
import e6j_prod as P
import e6j_slot as SL
import e6j_random as RND
import e6i_core as I
import e6i_ops as O
import e6i_randoms as IR
import e6f_core as F
import e6g_core as G

HS_B = (1, 2, 3, 5, 10, 15, 20)
HS_P = (3, 5, 10, 20)


def load_calendar():
    import os
    c = pd.read_csv(os.path.join(J.RES, 'registry', 'trade_calendar.csv'))
    return pd.Index(pd.to_datetime(c.date))


class Env(object):
    """一段的全部只读上下文：E6i 同款段（研究母体 / 单元 / 稀疏引擎）+ 可选生产上下文（生产六形态的腿与剔尾集）。"""

    def __init__(self, pname, with_prod=True):
        self.pname = pname
        S = self.S = I.seg_i(pname, warm=False)
        self.R = IR.RCtx(S, pname)
        self.ci = self.R.ci
        self.SE = self.R.SE
        self.cal = load_calendar()
        self.dates = pd.to_datetime(pd.Index(S.dates).astype(str))
        self.grid = RND.Grid(self.dates, S.ccolnames, self.cal)
        self.ctx = None
        if with_prod:
            ctx = self.ctx = P.build_period(pname)
            if not (list(ctx['pool0'].index) == list(S.pool0.index) and list(ctx['pool0'].columns) == list(S.pool0.columns)
                    and np.array_equal(ctx['pool0'].values, S.pool0.values)):
                raise RuntimeError('生产 pool0 与研究段 pool0 不一致（锚 2 L0 应已保证）')
            cc = S.ccols
            cel = lambda A: np.asarray(A)[:, cc][self.ci.t, self.ci.c]
            self.pK = self._dense_cells(ctx['pcond'])
            self.pT = self._dense_cells(ctx['ptvol'])
            self.pR = self._dense_cells(ctx['pcr20'])
            self.dT = cel(P.drop_mask(ctx['neu_tvol'], ctx['pool0']))
            self.dR = cel(P.drop_mask(ctx['neu_cr20'], ctx['pool0']))
            self.cvr = cel(P.drop_mask(ctx['neu_cvr'], ctx['pool0'], 5))

    def _dense_cells(self, cache):
        D = SL.dense(self.ctx, cache)                       # (T, Nc)，ccols 空间
        return D[self.ci.t, self.ci.c]

    def cells_of_dense(self, D):
        return np.asarray(D)[self.ci.t, self.ci.c]

    def full_mask(self, cells_bool):
        return self.ci.full(cells_bool)


# ------------------------------------------------------------------ 结构：kept(q (P, n)) → (P, n) bool
STAGE2 = None      # None = IR.dep_stage2_keep（锚过的原实现，默认）；随机层（e6j_run_prand / e6j_run_brand）设为 e6j_fast.stage2_fast（逐位相同）


class DepK(object):
    """A4b / A4b_CVRv5 / R1 的 K 槽位（两阶段完整重算：第一关 keep a%；第二关在新 S1 内 T 按源口径重中性化后 keep b%；否决）。"""

    def __init__(self, env, veto, q0=None):
        self.env = env
        self.M = env.R.mother('R1')                          # R1 ≡ A4b_CVRv5（exact_alias）
        self.a, self.b = self.M.core['a'], self.M.core['b']
        self.q0 = self.M.Px_c if q0 is None else q0          # = 生产 pcond（锚 3 T6）；COMMON_SUPPORT 时 = J 上重算的 K
        self.dom = IR.KeepDom(env.ci, np.isfinite(self.q0), self.a)
        self.drop = self.M.dr_c if veto else np.zeros(env.ci.n, bool)

    def kept(self, q):
        s1 = np.zeros(q.shape, bool)
        s1[:, self.dom.ids] = self.dom.keep(q[:, self.dom.ids])
        k = (STAGE2 or IR.dep_stage2_keep)(self.env.R, self.M, s1, self.b)
        return k & ~self.drop[None, :]


class DepT(object):
    """R1 的 T 槽位（第二阶段）：新成员原值在【母体 S1】内按源口径中性化排名（E6i slot_dep_T），与母体第二阶段分数混合后在 S1 内 keep。"""

    def __init__(self, env):
        self.env = env
        self.M = env.R.mother('R1')
        self.q0 = self.M.score_c
        sc = np.where(self.M.s1_c, self.q0, np.nan)
        self.dom = IR.KeepDom(env.ci, np.isfinite(sc) & self.M.s1_c, self.M.core['b'])
        self.drop = self.M.dr_c

    def kept(self, q):
        k = np.zeros(q.shape, bool)
        k[:, self.dom.ids] = self.dom.keep(q[:, self.dom.ids])
        return k & ~self.drop[None, :]


class MeanSlot(object):
    """均值核（生产 Mmean_v2；研究 R2 / A06；A08 单腿）：第 i 条腿换成 q，其余腿不变；源 combine（当日任一腿整行无值 → 当日无值；
       complete 时任一腿缺即缺）；keep s%；否决。"""

    def __init__(self, env, legs, i, s, complete, drop):
        self.env, self.legs, self.i, self.s, self.complete = env, legs, i, s, complete
        self.q0 = legs[i]
        self.drop = drop if drop is not None else np.zeros(env.ci.n, bool)
        ci = env.ci
        ok = np.ones(ci.T, bool)
        for j, L in enumerate(legs):
            ok &= np.bincount(ci.t[np.isfinite(L)], minlength=ci.T) > 0
        self.dayok = ok
        sc0 = self.score(self.q0[None, :])[0]
        self.dom = IR.KeepDom(ci, np.isfinite(sc0), s)

    def score(self, q):
        A = [np.broadcast_to(L[None, :], q.shape) if j != self.i else q for j, L in enumerate(self.legs)]
        if len(A) == 1:
            out = q.copy()
        else:
            tot = np.zeros(q.shape); cnt = np.zeros(q.shape, np.intp)
            for Aj in A:
                tot = tot + np.where(np.isnan(Aj), 0.0, Aj); cnt = cnt + (~np.isnan(Aj)).astype(np.intp)
            with np.errstate(invalid='ignore', divide='ignore'):
                out = tot / cnt
            if self.complete:
                anyn = np.zeros(q.shape, bool)
                for Aj in A:
                    anyn |= np.isnan(Aj)
                out = np.where(anyn, np.nan, out)
        return np.where(self.dayok[self.env.ci.t][None, :], out, np.nan)

    def kept(self, q):
        sc = self.score(q)
        k = np.zeros(q.shape, bool)
        k[:, self.dom.ids] = self.dom.keep(sc[:, self.dom.ids])
        return k & ~self.drop[None, :]


class UnionK(object):
    """生产 Munion_v2（± CVRv5）：K 腿剔尾集换成 q 的剔尾集（q 定义域外 = 剔除，源"无值票也算剔除"），与 T / cr20 剔尾集取并集之外。"""

    def __init__(self, env, veto, q0=None):
        self.env = env
        self.q0 = env.pK if q0 is None else q0
        self.dom = IR.KeepDom(env.ci, np.isfinite(self.q0), 50)
        self.base = ~env.dT & ~env.dR & (~env.cvr if veto else np.ones(env.ci.n, bool))

    def kept(self, q):
        k = np.zeros(q.shape, bool)
        k[:, self.dom.ids] = self.dom.keep(q[:, self.dom.ids])
        return k & self.base[None, :]


def prod_structure(env, form, q0=None):
    """生产六形态的 K 槽位结构；q0 覆盖 K 腿（COMMON_SUPPORT：在 J 上重算中性化与排名后的 K，J 外 NaN，按源规则处理）。"""
    veto = form.endswith('_CVRv5')
    if form.startswith('A4b'):
        return DepK(env, veto, q0)
    if form.startswith('M_mean3'):
        return MeanSlot(env, [env.pK if q0 is None else q0, env.pT, env.pR], 0, 50, False, env.cvr if veto else None)
    if form.startswith('M_union3'):
        return UnionK(env, veto, q0)
    raise ValueError(form)


def research_structure(env, mother, slot):
    """研究母体槽位结构（B 块）：R1 K = DepK(veto)；R1 T = DepT；R2 / A06 均值腿 K = 0、T = 1；A08 单腿 T。"""
    if mother == 'R1':
        return DepK(env, True) if slot == 'K' else DepT(env)
    M = env.R.mother(mother)
    i = M.leg_roles.index(slot)
    return MeanSlot(env, list(M.legs_c), i, M.core['s'], M.core['fam'].startswith('KTC'), M.dr_c)


# ------------------------------------------------------------------ q 的批量构造（FALLBACK 家族）
def blend(q0, parts, a):
    """q0: (n,)；parts: [(share, new (P, n))]；a: 标量或 (n,) 数组（可靠性 α·r）。
       单分量：新缺处逐位取 q0（与 e6i_ops._blend 同式）；多分量：分量各自回退，全缺 = q0。"""
    a = np.asarray(a, dtype=float)
    if len(parts) == 1:
        new = parts[0][1]
        return np.where(np.isfinite(new), (1 - a) * q0[None, :] + a * new, q0[None, :])
    miss_all = None
    q = (1 - a) * q0[None, :]
    for share, new in parts:
        c = np.where(np.isfinite(new), new, q0[None, :])
        q = q + (a * share) * c
        m = ~np.isfinite(new)
        miss_all = m if miss_all is None else (miss_all & m)
    return np.where(miss_all, q0[None, :], q)


# ------------------------------------------------------------------ 账户
def accounts(env, kept, Hs, cost_bp=8.0):
    """kept (P, n) bool → 每路径 {H: (gross, pos, turn, net)}（稀疏引擎）；另返回每路径目标 (t, c, w)。"""
    ci, SE = env.ci, env.SE
    out = []
    for p in range(kept.shape[0]):
        ids = np.flatnonzero(kept[p])
        t, c = ci.t[ids], ci.c[ids]
        w = SE.dev(t, c)
        out.append((SE.pnl(t, c, w, Hs, cost_bp), (t, c, w)))
    return out
