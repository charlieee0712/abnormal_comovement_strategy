# -*- coding: utf-8 -*-
"""E6m 随机层 · 逐路径名单（plan §9.3；brief W10 / W13；附录 A5）。只产生每条路径的门 / 最终名单，不读收益；
账户累计（e6l_fast.AcctFast + e6l_run_rand.accum_nb 同构）在阶段 S 的 e6m_s_rand_run 里接。

种子与优先序沿 E6j 随机契约（e6j_random：路径键 = blake2b-64(canonical_json)；u(路径, 绝对交易块, ticker) = splitmix64 计数器哈希；
P5 = 绝对交易日 // 5；IID = 绝对交易日）。键 namespace = 'E6m.<机制>'，group = owner 配置（去 H），parent = 形态，support = 机会域名，kind = 'P5' / 'IID'。

机制（plan §9.3 表；执行端实现口径登记于 STAGE_S_IMPL_PLAN §5）：
- 内容随机 LEGACY_POLICY_RANDOM / CONTENT_ISK_P5：
  - 阶段 S 用 e6k_random.Legacy / NewCond（E6k 键）与 e6l_run_rand.Draws 同构；
  - B2 开发期只给"段内当日有限值置换"的替身（kind = 'PROFILE_STANDIN'），用于打通各算子的逐路径管道，不冒称 LEGACY。
  - 置换后的坏度 → 各 owner 算子按自身合同重跑（记忆用本路径自己的无记忆 U / 实际 G）。
- R-BAND：固定 E、B、有限支持、可动名额与原门；在 B 的有限 Q 成员之间按 P5 优先序置换 kQ（多重集守恒），重跑同一 BAND（含其记忆）。
- R-FILTER_LABEL：同日门域内 owner 有限成员之间置换 kQ（PASS 数守恒，缺失身份不动），重跑同一 PRIORITY / HARD。
- DELETE_BUDGET_COND：HARD → 从前置门（U0 / U_oldlag）里 owner 有限成员按 (行业, size3) 层随机删与真实同层同数。
  V_STATE → 从父最终名单中 V 有限且满足条件者，按 (Trend, 行业, size3) 层随机删同数。均为 e6m_b3_tools.delete_count_control 同式，P5 键。
- R-EDIT_FIXED_OUT / R-EDIT_BOTH_RANDOM：e6j_random.edit_entry / edit_both。
  - 机会域：LOCAL = B 的有限 Q，GLOBAL = E 的有限 Q，NATIVE_TRIM = NATIVE_MASKFIX 的真实换入 / 换出候选。
  - 层 = 行业 × 旧 K3 → 逐层并粗。
- R-MEMORY-HG：每日把本路径自己的昨日实际 G 在当前门域内的标记数，按 P5 优先序重新分给门域成员，递归运行同 HG。
- R-MEMORY-LAG：每日把同算子昨日无 bonus 自然 U 的标记数重新分配，分配范围按各自合同：
  LINEAR LAG1 = 门域；BAND PROTECTED = B 的可动部分；PRIORITY RULE_LAG = PASS / FAIL 各自分区。"""
import numpy as np
import pandas as pd

import e6j_random as RND
import e6m_ops as O
import e6m_ops_vec as V
import e6m_s_ops as S


class Keys(object):
    """一个 (段, 形态) 的随机坐标：绝对交易日序号（全程日历）与 ticker 整数；门域 / 单元 → u。"""

    def __init__(self, seg, calendar):
        self.seg = seg
        self.day = RND.day_index(pd.to_datetime(pd.Index([str(d)[:10] for d in seg.dates])), pd.to_datetime(pd.Index(calendar)))
        self.tid = np.asarray(seg.tid_c if hasattr(seg, 'tid_c') else seg.tid, np.int64)

    def u(self, key, cells, block=5):
        seg = self.seg
        return RND.uniform(key, self.day[seg.ci.t[cells]] // int(block), self.tid[seg.ci.c[cells]])


def key_of(mech, owner, form, support, kind, path):
    return RND.path_key('E6m.' + mech, owner, form, support, kind, path)


def permute_within(vals, groups, u):
    """组内按 u 降序把 vals 的降序值依次分配（e6j_random.assign_by_priority 同式；NaN 不参与，原位保留）。"""
    out = vals.copy()
    ok = np.isfinite(vals)
    ix = np.flatnonzero(ok)
    if len(ix):
        out[ix] = RND.assign_by_priority(vals[ix], groups[ix], u[ix])
    return out


# ---------------------------------------------------------------- 内容置换（B2 替身）
def standin_content(ctx, paths, mech, owner, form):
    """PROFILE_STANDIN：门域内当日有限 kQ 按 P5 键置换（每路径一份）。返回 (P, len(ids))。阶段 S 换 e6k_random。"""
    K = Keys(ctx.seg, ctx._cal)
    ids = ctx.ids
    day = ctx.seg.ci.t[ids]
    out = np.empty((len(paths), len(ids)))
    for i, p in enumerate(paths):
        u = K.u(key_of(mech, owner, form, 'DOMAIN', 'PROFILE_STANDIN', p), ids)
        out[i] = permute_within(ctx.kq, day.astype(np.int64), u)
    return out


# ---------------------------------------------------------------- 逐路径算子（门域坐标；KQ (P, len(ids))）
def band_paths(ctx, KQ, w, alpha=None, memory='NONE', copy=False, inside_override=None):
    """每路径 BAND（含 PROTECTED_LAG10：本路径自己的无记忆自然 U 作记忆）。返回 (G_nomem, G_mem) 各 (P, len(ids))。"""
    P = KQ.shape[0]
    n = len(ctx.ids)
    Gn = np.zeros((P, n), bool)
    Gm = np.zeros((P, n), bool) if memory != 'NONE' else None
    prev = np.zeros((P, ctx.seg.Nc), bool)
    last = None
    NS = None
    if alpha is not None and not copy:
        NS = np.vstack([ctx.st.gate_scores(S.native_q(ctx.q0, _cells(ctx, KQ[i]), alpha)[None, :])[0] for i in range(P)])
    for d, a, e, K in ctx.days:
        if last is not None and d != last + 1:
            prev[:] = False
        o = ctx.orders[d]
        kq = KQ[:, a:e]
        if inside_override is not None:
            ins = inside_override[:, a:e]
        elif copy:
            ins = np.repeat((ctx.sc0[a:e] if alpha is not None else O.copy_coordinates(o, ctx.kq[a:e]))[None, :], P, axis=0)
        else:
            ins = kq if alpha is None else NS[:, a:e]
        u = V.band_paths(o, ctx.sc0[a:e], kq, K, w, INSIDE=ins)
        Gn[:, a:e] = u
        if memory == 'PROTECTED_LAG10':
            mark = prev[:, ctx.cols[a:e]]
            Gm[:, a:e] = V.band_paths(o, ctx.sc0[a:e], kq, K, w, INSIDE=ins, PREV=mark, b=S.B_MEM, loading=ctx.load[a:e])
        prev[:] = False
        rr, jj = np.nonzero(u)
        prev[rr, ctx.cols[a:e][jj]] = True
        last = d
    return Gn, Gm


def _cells(ctx, kq_dom):
    out = np.full(ctx.seg.n, np.nan)
    out[ctx.ids] = kq_dom
    return out


def priority_paths(ctx, KQ, c, memory='NONE'):
    P = KQ.shape[0]
    out = []
    for i in range(P):
        c_ = S.Ctx.__new__(S.Ctx)
        c_.__dict__.update(ctx.__dict__)
        c_.kq = KQ[i]
        gn, gm, _ = S.priority_gates(c_, c, memory)
        out.append(gn if memory == 'NONE' else gm)
    return np.vstack(out)


def hard_paths(ctx, KQ, c, memory='NONE'):
    base = ctx.U0 if memory == 'NONE' else S.source_gate(S._OldCtx(ctx), 0.0, 'LAG1_10')[0]
    return base[None, :] & (~np.isfinite(KQ) | (KQ <= c))


def source_paths(ctx, KQ, a, memory='NONE'):
    st = ctx.st
    Q = np.vstack([S.native_q(ctx.q0, _cells(ctx, KQ[i]), a) for i in range(KQ.shape[0])])
    sc = st.gate_scores(Q)
    U = st.gate_keep(sc)
    if memory == 'NONE':
        return U
    kind, b = {'HG10': ('HG', 10.0), 'LAG1_10': ('LAG1', 10.0)}[memory]
    return ctx.mem_gate(st, sc, U, kind, b)


# ---------------------------------------------------------------- 机制随机
def r_band_content(ctx, paths, owner, form, w):
    """R-BAND：B 的有限 Q 成员之间按 P5 键置换 kQ。返回 (P, len(ids))。"""
    K = Keys(ctx.seg, ctx._cal)
    out = np.repeat(ctx.kq[None, :], len(paths), axis=0)
    for d, a, e, Kd in ctx.days:
        o = ctx.orders[d]
        A, B, C, j = O.band_parts(o, Kd, w)
        if j == 0:
            continue
        Bc = a + B[np.isfinite(ctx.kq[a + B])]
        if len(Bc) < 2:
            continue
        for i, p in enumerate(paths):
            u = K.u(key_of('R-BAND', owner, form, 'B', 'P5', p), ctx.ids[Bc])
            out[i, Bc] = RND.assign_by_priority(ctx.kq[Bc], np.zeros(len(Bc), np.int64), u)
    return out


def r_filter_content(ctx, paths, owner, form):
    """R-FILTER_LABEL：门域内 owner 有限成员之间置换 kQ（PASS 数守恒；缺失不动）。"""
    K = Keys(ctx.seg, ctx._cal)
    day = ctx.seg.ci.t[ctx.ids].astype(np.int64)
    return np.vstack([permute_within(ctx.kq, day, K.u(key_of('R-FILTER_LABEL', owner, form, 'DOMAIN', 'P5', p), ctx.ids)) for p in paths])


def delete_budget(seg, keys, parent_cells, deleted_cells, groups, eligible, owner, form, paths, mech='DELETE_BUDGET_COND'):
    """同日同层同删除数的随机删除（父 / 前置门内、eligible 内）；P5 键。返回 (P, n) 删除后名单。"""
    out = np.zeros((len(paths), seg.n), bool)
    cand = parent_cells & eligible
    if (deleted_cells & ~cand).any():
        raise ValueError('真实删除集超出候选域')
    for i, p in enumerate(paths):
        g = parent_cells.copy()
        for d in range(seg.T):
            a0, a1 = int(seg.off[d]), int(seg.off[d + 1])
            sl = np.arange(a0, a1)
            cd = sl[cand[sl]]
            if not len(cd):
                continue
            dd = sl[deleted_cells[sl]]
            if not len(dd):
                continue
            u = keys.u(key_of(mech, owner, form, 'PARENT', 'P5', p), cd)
            gg = groups[cd]
            for gv in np.unique(groups[dd]):
                m = int((groups[dd] == gv).sum())
                pool = cd[gg == gv]
                o = pool[np.argsort(-u[gg == gv], kind='stable')]
                g[o[:m]] = False
        out[i] = g
    return out


# ---------------------------------------------------------------- R-EDIT（e6j_random.edit_entry / edit_both；单元网格 (T, Nc)）
def r_edit(ctx, paths, owner, form, alpha, w, which, mode, ind_c, k0_c):
    """which ∈ {LOCAL, GLOBAL, NATIVE_TRIM}；mode ∈ {FIXED_OUT, BOTH_RANDOM}。父 = 源 U0，子 = 真实 EDIT 门。
    机会域 D（门域坐标）：LOCAL = B 的有限 Q；GLOBAL = E 的有限 Q；NATIVE_TRIM = 真实 NATIVE_MASKFIX 的换入 ∪ 换出集合。
    只在 D 内调用 e6j_random.edit_entry / edit_both（换出只从 U0 ∩ D 抽，换入只从 D ∖ U0 抽；层 = 行业 × 旧 K3 → 逐层并粗），D 外保持 U0。
    ind_c / k0_c：(T, Nc) 行业码与旧 K。返回 (P, len(ids)) 门。"""
    seg = ctx.seg
    T, Nc = seg.T, seg.Nc
    r, f = S.edit_gates(ctx, alpha, w)
    child_dom = r[which]
    U0 = ctx.U0
    Dm = np.zeros(len(ctx.ids), bool)
    ns = ctx.native_s(alpha)
    for d, a, e, K in ctx.days:
        o = ctx.orders[d]
        fin = np.isfinite(ctx.kq[a:e])
        if which == 'LOCAL':
            A, B, C, j = O.band_parts(o, K, w)
            m = np.zeros(e - a, bool)
            m[B] = True
            Dm[a:e] = m & fin
        elif which == 'GLOBAL':
            Dm[a:e] = fin
        else:
            mf = S.native_maskfix_day(o, ctx.kq[a:e], K, ns[a:e])
            Dm[a:e] = mf ^ U0[a:e]
    if (child_dom != U0)[~Dm].any():
        raise RuntimeError('真实 EDIT 编辑出了机会域')

    def grid(x):
        out = np.zeros((T, Nc), bool)
        ids = ctx.ids[x]
        out[seg.ci.t[ids], seg.ci.c[ids]] = True
        return out
    parent, child, legal = grid(U0 & Dm), grid(child_dom & Dm), grid(Dm)
    cn = [str(x) for x in (seg.ccolnames if hasattr(seg, 'ccolnames') else seg.S.ccolnames)]   # mock = MockSeg；真实 = e6l_env.SegL（列名在 .S）（2026-10-11）
    G = RND.Grid(pd.to_datetime(pd.Index([str(dd)[:10] for dd in seg.dates])), cn, pd.to_datetime(pd.Index(ctx._cal)))
    k3 = RND.terciles_rowwise(k0_c, grid(np.ones(len(ctx.ids), bool)))
    out = np.zeros((len(paths), len(ctx.ids)), bool)
    keep = U0 & ~Dm
    shorts = 0
    for i, p in enumerate(paths):
        if mode == 'FIXED_OUT':
            m, sh = RND.edit_entry(parent, child, legal, G, key_of('R-EDIT_FIXED_OUT', owner, form, which, 'P5', p), ind_c, k0_c, 5, k3=k3)
            shorts += int(np.sum(sh))
        else:
            m, sh = RND.edit_both(parent, child, legal, G, key_of('R-EDIT_BOTH_RANDOM', owner, form, which + '|OUT', 'P5', p),
                                  key_of('R-EDIT_BOTH_RANDOM', owner, form, which + '|IN', 'P5', p), ind_c, k0_c, 5, k3=k3)
            shorts += int(np.sum(sh[0]) + np.sum(sh[1]))
        out[i] = keep | m[seg.ci.t[ctx.ids], seg.ci.c[ctx.ids]]
    return out, dict(J_star=int(f['J_star']), shortfall=shorts)


# ---------------------------------------------------------------- R-MEMORY（标记数守恒的重分配）
def r_memory(ctx, paths, owner, form, kind, nomem_fn, select_fn, scope_fn):
    """kind ∈ {HG, LAG}。每日：标记 = 本路径昨日实际 G（HG）或同算子昨日无 bonus 自然 U（LAG）在当前门域的格；
    在 scope_fn(d, a, e, K, o) 给出的分区内按 P5 优先序重新分给同数成员（计数守恒），然后 select_fn(d, a, e, K, o, mark) 选门。
    nomem_fn(d, a, e, K, o) → 当日无记忆自然 U（LAG 的标记来源）。返回 (P, len(ids))。"""
    Kk = Keys(ctx.seg, ctx._cal)
    P = len(paths)
    out = np.zeros((P, len(ctx.ids)), bool)
    prevG = np.zeros((P, ctx.seg.Nc), bool)
    prevU = np.zeros((P, ctx.seg.Nc), bool)
    last = None
    for d, a, e, K in ctx.days:
        if last is not None and d != last + 1:
            prevG[:] = False
            prevU[:] = False
        o = ctx.orders[d]
        u_nat = nomem_fn(d, a, e, K, o)
        grp = scope_fn(d, a, e, K, o)
        cells = ctx.ids[a:e]
        for i, p in enumerate(paths):
            src = (prevG if kind == 'HG' else prevU)[i, ctx.cols[a:e]]
            uu = Kk.u(key_of('R-MEMORY-' + kind, owner, form, 'SCOPE', 'P5', p), cells)
            mark = np.zeros(e - a, bool)
            for gv in np.unique(grp[grp >= 0]):
                mem = np.flatnonzero(grp == gv)
                m = int(src[mem].sum())
                if m:
                    mark[mem[np.argsort(-uu[mem], kind='stable')[:m]]] = True
            g = select_fn(d, a, e, K, o, mark)
            out[i, a:e] = g
            prevG[i] = False
            prevG[i, ctx.cols[a:e][g]] = True
            prevU[i] = False
            prevU[i, ctx.cols[a:e][u_nat]] = True
        last = d
    return out
