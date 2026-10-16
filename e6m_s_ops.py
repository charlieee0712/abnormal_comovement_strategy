# -*- coding: utf-8 -*-
"""E6m 阶段 S 算子层（plan §4.2–§5.7 / §6；stageN/STAGE_S_IMPL_PLAN.md §1–§2）。不读任何收益。

在引擎门域坐标上运行：Struct.ids 按 (t, c) 排序，逐日用 dom.off / dom.K。逐日调用 e6m_ops 的逐日算子（阶段 N 合成对拍过），
拼成整路径门 G（len(ids) bool），再交 st.down（源下游）。st 可以是真实 e6k_env.Struct，也可以是 e6m_s_mock.MockStruct。

坐标：
- 源总序 = 当日门域内 (s0, 位置) 升序；位置 = ticker 升序 = 源 rank(method='first') 出现顺序；
- s0 = 父门分；K 混合 = native_q（e6k_ops.native_q 转录：kf 缺失处取 k0）。

记忆：
- 新算子（PROTECTED / UNPROTECTED / RULE / NATIVE_METRIC / COPY_*）：参照 = 昨日同算子无 bonus 的自然 U，按 ticker 对齐，今日不在门域者不恢复，空门日清空；
  bonus = B_MEM · K_loading_i（B_MEM = .10，K 坏度百分位单位）。
- SOURCE HG10 / LAG1_10 与 OLD_RULE：源 e6l_ops.mem_gate 口径（b · bunit）。阶段 S 用源函数；
  B2 开发期在 mock 上用本文件的转录 src_mem_gate，Stage 0 S 核两者逐位相同。

断点续跑（plan §13.3；附属第 7 项连续链用）：HG 存自己的实际 G、LAG1 / 新算子存同算子昨日无记忆 U，状态都带绝对交易日位置
（next_day / next_date）与列 ticker 哈希，身份不符即拒绝。源路径 src_mem_gate_s / source_gate_s（= 源 mem_gate 的 state / d0 / d1），
新算子路径 run_days(state, d0, d1)。不传状态时与旧版逐位相同。"""
import hashlib

import numpy as np

import e6m_ops as O

B_MEM = 0.10


def native_q(k0, kf, a):
    """e6k_ops.native_q 转录：k = (1 − a)·k0 + a·kf；kf 缺失处取 k0。"""
    a = np.asarray(a, dtype=float)
    return np.where(np.isfinite(kf), (1 - a) * k0 + a * kf, k0)


def k_loading_cells(st):
    """K_loading（plan §4.2）：A4b / union = 1；mean = 1 / 当日可得腿数，K 腿缺失时为 0。"""
    if hasattr(st, 'K_loading_cells'):
        return st.K_loading_cells
    if st.kind != 'mean':
        return np.ones(st.seg.n)
    legs = list(st.st.legs)
    i = getattr(st.st, 'i', 0)
    avail = sum(np.isfinite(L).astype(int) for L in legs)
    return np.where(np.isfinite(legs[i]) & (avail > 0), 1.0 / np.maximum(avail, 1), 0.0)


def select_rows(s, K):
    out = np.zeros(s.shape, bool)
    if K <= 0:
        return out
    idx = np.argsort(s, axis=1, kind='stable')[:, :K]
    np.put_along_axis(out, idx, True, axis=1)
    return out


def ids_hash(tickers):
    """e6l_ops.ids_hash 转录（续跑身份 = 列 ticker 哈希）。"""
    return hashlib.blake2b(','.join(map(str, tickers)).encode(), digest_size=8).hexdigest()


def colnames(seg):
    """源 mem_gate 读 seg.S.ccolnames；mock 段没有 S，用同值的 seg.ccolnames。"""
    return seg.S.ccolnames if hasattr(seg, 'S') else seg.ccolnames


def date_at(seg, d):
    """e6l_ops._date_at 转录。"""
    return str(seg.dates[d])[:10] if d < seg.T else 'END'


def check_resume(state, d0, tick, seg):
    """e6l_ops._check_resume 转录：下一日序号、下一绝对交易日、列 ticker 哈希三者都须一致，否则拒绝（不重映射）。"""
    bad = state['next_day'] != d0 or state['ids'] != tick
    if state.get('next_date') is not None:
        bad |= state['next_date'] != date_at(seg, d0)
    if bad:
        raise ValueError('checkpoint 身份不符：next_day %s vs %s；next_date %s vs %s；ids %s vs %s' % (
            state['next_day'], d0, state.get('next_date'), date_at(seg, d0), state['ids'], tick))


def states_equal(x, y):
    """两个续跑状态逐键相同（数组逐位；−inf 相等）。"""
    if set(x) != set(y):
        return False
    for k in x:
        a, b = x[k], y[k]
        if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
            if not np.array_equal(np.asarray(a), np.asarray(b)):
                return False
        elif a != b:
            return False
    return True


def mid_gate_day(st):
    """门域非空的中间一个门日（断点测试切分点）。"""
    k = np.flatnonzero((np.asarray(st.dom.K) > 0) & (np.diff(np.asarray(st.dom.off)) > 0))
    return int(k[len(k) // 2])


def src_mem_gate(st, sc, U, kind, b):
    """e6l_ops.mem_gate 的 HG / LAG1 分支转录（B2 开发期用；阶段 S 用源函数并核逐位相同）。sc、U：(P, len(ids))。"""
    return src_mem_gate_s(st, sc, U, kind, b)[0]


def src_mem_gate_s(st, sc, U, kind, b, state=None, d0=0, d1=None):
    """同上，带源断点续跑口径：state = None → cold_state（G / U 全 False、last = −inf）；否则先核身份再从 d0 续跑；只跑 [d0, d1)。
    返回 (G (P, len(ids)), 末状态 dict(next_day = d1, next_date, ids, G, U, last))。"""
    if kind not in ('HG', 'LAG1'):
        raise ValueError(kind)
    dom, seg = st.dom, st.seg
    P = sc.shape[0]
    Nc = seg.Nc
    d1 = seg.T if d1 is None else d1
    cols = seg.ci.c[st.ids]
    tick = ids_hash(colnames(seg))
    if state is None:
        stt = dict(next_day=0, ids=tick, G=np.zeros((P, Nc), bool), U=np.zeros((P, Nc), bool), last=np.full((P, Nc), -np.inf))
    else:
        stt = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in state.items()}
        check_resume(stt, d0, tick, seg)
    G = np.zeros(sc.shape, bool)
    Gs, Us, last = stt['G'], stt['U'], stt['last']
    be = float(b) * st.bunit
    for d in range(d0, d1):
        a, e = dom.off[d], dom.off[d + 1]
        if e == a or dom.K[d] == 0:
            Gs = np.zeros((P, Nc), bool)
            Us = np.zeros((P, Nc), bool)
            last[:] = -np.inf
            continue
        cc = cols[a:e]
        s = sc[:, a:e]
        Ud = U[:, a:e]
        mark = Gs[:, cc] if kind == 'HG' else Us[:, cc]
        bon = be * mark
        nz = (bon != 0).any(axis=1)
        g = Ud.copy()
        if nz.any():
            g[nz] = select_rows(s[nz] - bon[nz], int(dom.K[d]))
        G[:, a:e] = g
        Gs = np.zeros((P, Nc), bool)
        rr, jj = np.nonzero(g)
        Gs[rr, cc[jj]] = True
        Us = np.zeros((P, Nc), bool)
        rr, jj = np.nonzero(Ud)
        Us[rr, cc[jj]] = True
    stt.update(next_day=d1, next_date=date_at(seg, d1), G=Gs, U=Us, last=last)
    return G, stt


class Ctx(object):
    """一个 (结构, 测量) 的门域上下文：父门分 s0、源门 U0、测量坏度 kq（门域坐标）、逐日源总序、K_loading、ticker。
    mem_gate(st, sc, U, kind, b) → G；mem_gate_s(…, state, d0, d1) → (G, 末状态)（断点续跑版；缺省 = 本文件转录）。"""

    def __init__(self, st, kf, q0=None, mem_gate=None, mem_gate_s=None):
        self.st, self.seg = st, st.seg
        seg = self.seg
        self.q0 = st.q0 if q0 is None else q0
        self.ids, self.dom = st.ids, st.dom
        self.sc0 = st.gate_scores(self.q0[None, :])[0]
        self.U0 = st.gate_keep(self.sc0[None, :])[0]
        self.kf = kf
        self.kq = None if kf is None else np.asarray(kf, float)[self.ids]
        self.cols = seg.ci.c[self.ids]
        self.tk = np.array(['%06d' % x for x in np.asarray(seg.tid)[self.ids]])
        self.load = k_loading_cells(st)[self.ids]
        dom = self.dom
        self.days = [(d, int(dom.off[d]), int(dom.off[d + 1]), int(dom.K[d])) for d in range(seg.T) if dom.K[d] > 0 and dom.off[d + 1] > dom.off[d]]
        self.orders = {d: np.lexsort((np.arange(e - a), self.sc0[a:e])) for d, a, e, K in self.days}
        self._ns = {}
        self.mem_gate = mem_gate or src_mem_gate
        self.mem_gate_s = mem_gate_s or src_mem_gate_s

    def native_s(self, a):
        """源 native_s(α)（门分坐标；mean = 真实三腿综合式，K 腿换混合值）。"""
        a = float(a)
        if a not in self._ns:
            self._ns[a] = self.st.gate_scores(native_q(self.q0, self.kf, a)[None, :])[0]
        return self._ns[a]

    def copy_coord_day(self, a, e, order):
        """COPY_GATE_ORDER 坐标（plan §4.3）：完整门域冻结总序上 (r − .5)/N，再施加 owner（本测量）有限 / 缺失掩码。"""
        return O.copy_coordinates(order, self.kq[a:e])


def run_days(ctx, nomem, mem=None, state=None, d0=0, d1=None):
    """逐日运行。nomem(d, a, e, K, order) → (名单, 事实 dict)；mem(d, a, e, K, order, mark) → (名单, 事实 dict)。
    mark = 昨日同算子无记忆自然 U（按列对齐；空门日清空）。返回 (G_nomem, G_mem, facts)。
    断点续跑（plan §13.3）：只跑 [d0, d1) 的门日；state = dict(next_day, next_date, ids, U)，U = d0 前一日同算子无记忆自然 U
    （本段列坐标 (Nc,) bool；该日不是门日则全 False），先核身份（check_resume）；state = None → 冷启动（d0 = 0、d1 = None 时与旧版逐位同）。
    facts['state'] = 末状态（next_day = d1；d1 − 1 不是已跑门日则 U 全 False，与源 mem_gate 空门日清空同式）。"""
    seg = ctx.seg
    d1 = seg.T if d1 is None else d1
    tick = ids_hash(colnames(seg))
    n = len(ctx.ids)
    Gn = np.zeros(n, bool)
    Gm = np.zeros(n, bool) if mem is not None else None
    if state is None:
        prev = np.zeros(seg.Nc, bool)
        last = None
    else:
        check_resume(state, d0, tick, seg)
        prev = np.asarray(state['U'], bool).copy()
        if prev.shape != (seg.Nc,):
            raise ValueError('续跑状态 U 形状 %s ≠ (%d,)' % (prev.shape, seg.Nc))
        last = d0 - 1                                          # d0 是门日 → 与状态相接；否则首个门日前有空门日 → 清空
    facts = dict(days=0, nomem={}, mem={})

    def addf(dst, f):
        for k, v in (f or {}).items():
            dst[k] = dst.get(k, 0) + v
    for d, a, e, K in ctx.days:
        if d < d0 or d >= d1:
            continue
        if last is not None and d != last + 1:
            prev = np.zeros(ctx.seg.Nc, bool)                 # 中间有空门日 → 记忆清空（e6l_ops.mem_gate 同）
        order = ctx.orders[d]
        u, fu = nomem(d, a, e, K, order)
        Gn[a:e] = u
        addf(facts['nomem'], fu)
        if mem is not None:
            mark = prev[ctx.cols[a:e]]
            g, fg = mem(d, a, e, K, order, mark)
            Gm[a:e] = g
            addf(facts['mem'], fg)
            addf(facts['mem'], dict(marked=int(mark.sum()), reliant=int((g & ~u).sum())))
        prev = np.zeros(ctx.seg.Nc, bool)
        prev[ctx.cols[a:e][u]] = True
        last = d
        facts['days'] += 1
    end = prev if (last is not None and last == d1 - 1) else np.zeros(seg.Nc, bool)
    facts['state'] = dict(next_day=d1, next_date=date_at(seg, d1), ids=tick, U=end)
    return Gn, Gm, facts


# ---------------------------------------------------------------- SOURCE（LINEAR NATIVE / HG10 / LAG1_10）与 OLD_RULE
def source_gate(ctx, a, memory='NONE'):
    """源线性 K 混合（FALLBACK）全域门；memory ∈ {NONE, HG10, LAG1_10}。a = 0 / 测量缺 → 旧 K。"""
    st = ctx.st
    q = ctx.q0 if (ctx.kf is None or float(a) == 0.0) else native_q(ctx.q0, ctx.kf, a)
    sc = st.gate_scores(q[None, :])
    U = st.gate_keep(sc)
    if memory == 'NONE':
        return U[0], {}
    kind, b = {'HG10': ('HG', 10.0), 'LAG1_10': ('LAG1', 10.0)}[memory]
    G = ctx.mem_gate(st, sc, U, kind, b)
    return G[0], dict(reliant=int((G[0] & ~U[0]).sum()), **gate_facts(G[0], U[0], st))


def source_gate_s(ctx, a, memory, state=None, d0=0, d1=None):
    """source_gate 的断点续跑版（memory ∈ {HG10, LAG1_10}；状态 = 源 mem_gate 口径）。返回 (G, 无记忆 U, 末状态)，G / U 为门域坐标 (len(ids),)；
    [d0, d1) 之外 G 为 False（U 是逐日无状态的源门，全程给出）。"""
    st = ctx.st
    q = ctx.q0 if (ctx.kf is None or float(a) == 0.0) else native_q(ctx.q0, ctx.kf, a)
    sc = st.gate_scores(q[None, :])
    U = st.gate_keep(sc)
    kind, b = {'HG10': ('HG', 10.0), 'LAG1_10': ('LAG1', 10.0)}[memory]
    G, stt = ctx.mem_gate_s(st, sc, U, kind, b, state=state, d0=d0, d1=d1)
    return G[0], U[0], stt


def gate_facts(G, U, st, daily=None):
    """e6l_run_det.gate_facts 转录（Stage A 门层记忆事实；附录 A2-7 对 E6l mask_facts 用；不含 rec 计数两列）：
    靠 bonus 续选份额、连续依靠 bonus 日数分位、自然重确认年龄分位、门成员日留存率。G、U：门域坐标 (len(ids),) bool。
    daily：传入空 list 时逐日追加 (d, reliant_share, reliant_run_p50, confirm_age_p50)（固定表 memory_age_daily；E6l a0 同列），汇总值不变。"""
    dom, seg = st.dom, st.seg
    rel = G & ~U
    n_g = max(int(G.sum()), 1)
    cols = seg.ci.c[st.ids]
    run = np.zeros(seg.Nc, np.int64)
    runs = []
    age = np.full(seg.Nc, -1, np.int64)
    ages = []
    prevg = np.zeros(seg.Nc, bool)
    kept_n = kept_d = 0
    for d in range(seg.T):
        a, b = dom.off[d], dom.off[d + 1]
        if b == a or dom.K[d] == 0:
            run[:] = 0
            age[:] = -1
            prevg[:] = False
            continue
        cc = cols[a:b]
        r = rel[a:b]
        u = U[a:b]
        g = G[a:b]
        if prevg.any():
            kept_n += int((prevg[cc] & g).sum())
            kept_d += int(prevg.sum())
        newrun = np.zeros(seg.Nc, np.int64)
        newrun[cc[r]] = run[cc[r]] + 1
        run = newrun
        newage = np.full(seg.Nc, -1, np.int64)
        newage[cc[u]] = 0
        keep = g & ~u & (age[cc] >= 0)
        newage[cc[keep]] = age[cc[keep]] + 1
        age = newage
        prevg = np.zeros(seg.Nc, bool)
        prevg[cc[g]] = True
        if r.any():
            runs.append(run[cc[r]])
        if g.any():
            ages.append(age[cc[g]])
        if daily is not None:
            ng = int(g.sum())
            ag = age[cc[g]]
            ag = ag[ag >= 0]
            daily.append((d, float(r.sum()) / ng if ng else float('nan'), float(np.median(run[cc[r]])) if r.any() else float('nan'),
                          float(np.median(ag)) if len(ag) else float('nan')))
    rr = np.concatenate(runs) if runs else np.zeros(0)
    aa = np.concatenate(ages) if ages else np.zeros(0)

    def q(x, p):
        return float(np.percentile(x, p)) if len(x) else float('nan')
    return dict(bonus_reliant_share=float(rel.sum()) / n_g, reliant_run_p50=q(rr, 50), reliant_run_p90=q(rr, 90),
                reliant_run_max=float(rr.max()) if len(rr) else 0.0, confirm_age_p50=q(aa, 50), confirm_age_p90=q(aa, 90),
                confirm_age_max=float(aa.max()) if len(aa) else 0.0, gate_retention=float(kept_n / kept_d) if kept_d else float('nan'))


def native_maskfix_day(order, kq, n, ns):
    """NATIVE_MASKFIX(α)（plan §4.3）：Q 缺失者锁原 U0 身份；有限者按 (native_s, 原总序) 取 n − 原 U0 中缺失数。"""
    u0 = O.source_mask(order, n)
    fin = np.isfinite(kq)
    out = u0 & ~fin
    k = n - int(out.sum())
    rk = O.ranks_of(order)
    F = np.flatnonzero(fin)
    out[F[np.lexsort((rk[F], ns[F]))][:k]] = True
    return out


def maskfix_gate(ctx, a):
    ns = ctx.native_s(a)
    return run_days(ctx, lambda d, s, e, K, o: (native_maskfix_day(o, ctx.kq[s:e], K, ns[s:e]), {}))[0]


# ---------------------------------------------------------------- BAND_Q / BAND_BLEND / NATIVE_METRIC / COPY
def band_gates(ctx, w, alpha=None, memory='NONE', copy=False, metric=False, state=None, d0=0, d1=None):
    """返回 (G_无记忆, G_记忆或 None, facts)。
    alpha = None → BAND_Q（带内优先序 = kQ；COPY = 总序坐标）；alpha = 数 → BAND_BLEND（native_s(α)；COPY = s0 直接分值）。
    memory ∈ {NONE, PROTECTED_LAG10, UNPROTECTED_LAG10}；metric = True → NATIVE_METRIC_LAG（只用于 BAND_BLEND）。
    state / d0 / d1：断点续跑（见 run_days；facts['state'] = 末状态）。"""
    s0 = ctx.sc0
    kq = ctx.kq
    ns = ctx.native_s(alpha) if alpha is not None else None

    def inside(a, e, order):
        if copy:
            return s0[a:e] if alpha is not None else ctx.copy_coord_day(a, e, order)
        return kq[a:e] if alpha is None else ns[a:e]

    def nomem(d, a, e, K, order):
        return O.band(order, s0[a:e], kq[a:e], K, w, inside=inside(a, e, order), ids=ctx.tk[a:e]), {}
    mem = None
    if memory == 'PROTECTED_LAG10' and not metric:
        def mem(d, a, e, K, order, mark):
            return O.band(order, s0[a:e], kq[a:e], K, w, inside=inside(a, e, order), prev_natural=mark, b=B_MEM, loading=ctx.load[a:e],
                          ids=ctx.tk[a:e]), {}
    elif memory == 'PROTECTED_LAG10' and metric:
        def mem(d, a, e, K, order, mark):
            return O.band_native_metric(order, s0[a:e], kq[a:e], K, w, inside(a, e, order), prev_natural=mark, b=B_MEM,
                                        loading=ctx.load[a:e], ids=ctx.tk[a:e]), {}
    elif memory == 'UNPROTECTED_LAG10':
        def mem(d, a, e, K, order, mark):
            g, ed = O.band_unprotected(order, s0[a:e], kq[a:e], K, w, inside(a, e, order), mark, b=B_MEM, loading=ctx.load[a:e],
                                       ids=ctx.tk[a:e])
            return g, dict(outside_band_edits=ed)
    elif memory != 'NONE':
        raise ValueError(memory)
    return run_days(ctx, nomem, mem, state=state, d0=d0, d1=d1)


# ---------------------------------------------------------------- PRIORITY_PASS / HARD_CONJ / COPY_PASS
def priority_gates(ctx, c, memory='NONE', copy=False, state=None, d0=0, d1=None):
    s0 = ctx.sc0
    kq = ctx.kq

    def q(a, e, order):
        return ctx.copy_coord_day(a, e, order) if copy else kq[a:e]

    def nomem(d, a, e, K, order):
        g, r = O.priority_pass(order, s0[a:e], q(a, e, order), K, c, ids=ctx.tk[a:e])
        return g, dict(refill=r)
    mem = None
    if memory == 'RULE_LAG10':
        def mem(d, a, e, K, order, mark):
            g, r = O.priority_pass(order, s0[a:e], q(a, e, order), K, c, prev_natural=mark, b=B_MEM, loading=ctx.load[a:e], ids=ctx.tk[a:e])
            return g, dict(refill=r)
    elif memory != 'NONE':
        raise ValueError(memory)
    return run_days(ctx, nomem, mem, state=state, d0=d0, d1=d1)


def hard_gates(ctx, c, memory='NONE', copy=False):
    """无记忆：U0 ∩ (缺失 ∪ PASS)；记忆：旧核心源 LAG1_10 门 U_oldlag ∩ (缺失 ∪ PASS)（plan §5.5）。"""
    if memory == 'NONE':
        base = ctx.U0
    elif memory == 'RULE_LAG10':
        base, _ = source_gate(_OldCtx(ctx), 0.0, 'LAG1_10')
    else:
        raise ValueError(memory)
    G = np.zeros(len(ctx.ids), bool)
    dele = 0
    for d, a, e, K in ctx.days:
        q = ctx.copy_coord_day(a, e, ctx.orders[d]) if copy else ctx.kq[a:e]
        G[a:e] = O.hard_conj(base[a:e], q, c)
        dele += int((base[a:e] & ~G[a:e]).sum())
    return G, dict(deleted=dele, base_members=int(base.sum()))


class _OldCtx(object):
    """旧核心视图（无测量）：source_gate(·, 0) = 父门。"""

    def __init__(self, ctx):
        self.st, self.q0, self.kf, self.mem_gate = ctx.st, ctx.q0, None, ctx.mem_gate
        self.mem_gate_s = getattr(ctx, 'mem_gate_s', src_mem_gate_s)


# ---------------------------------------------------------------- 同编辑预算（plan §5.6）
def edit_gates(ctx, alpha, w):
    """返回 dict(LOCAL, GLOBAL, NATIVE_TRIM → G) 与逐日 J / J* 合计。"""
    ns = ctx.native_s(alpha)
    out = {k: np.zeros(len(ctx.ids), bool) for k in ('LOCAL', 'GLOBAL', 'NATIVE_TRIM')}
    J = Js = 0
    for d, a, e, K in ctx.days:
        o = ctx.orders[d]
        mf = native_maskfix_day(o, ctx.kq[a:e], K, ns[a:e])
        r = O.edit_match(o, ctx.kq[a:e], K, w, mf, ns[a:e], ids=ctx.tk[a:e])
        for k in out:
            out[k][a:e] = r[k]
        J += r['J']
        Js += r['J_star']
    return out, dict(J=J, J_star=Js)


# ---------------------------------------------------------------- Mmean K 槽位桥（plan §5.7）
def slot_bridge_gate(ctx, w, mode):
    """K_SLOT：按旧 K 自身前半名次定义局部带（源两组第一组 + band_width_count），带内有限 Q 者按 Q（SLOT_Q）或 K 混合 α .25（SLOT_BLEND25）
    重排，把原 K 评分槽的多重集按新优先序分配回去，再按原综合公式在完整 Mmean 门上取名额。只用于 mean 结构。"""
    st = ctx.st
    if st.kind != 'mean':
        raise ValueError('K_SLOT 只用于 Mmean')
    seg = ctx.seg
    import e6m_s_mock as MK
    k0 = np.asarray(ctx.q0, float)
    kf = np.asarray(ctx.kf, float)
    newk = k0.copy()
    moved = 0
    for d in range(seg.T):
        c0, c1 = int(seg.off[d]), int(seg.off[d + 1])
        ix = np.arange(c0, c1)[np.isfinite(k0[c0:c1])]
        N = len(ix)
        n = MK.k_of(N)
        if n == 0:
            continue
        order = ix[np.lexsort((np.asarray(seg.tid)[ix], k0[ix]))]
        j = O.band_width_count(w, N, n)
        if j == 0:
            continue
        B = order[n - j:n + j]
        good = B[np.isfinite(kf[B])]
        if not len(good):
            continue
        rk = np.empty(c1 - c0, int)
        rk[order - c0] = np.arange(N)
        pri = kf[good] if mode == 'SLOT_Q' else native_q(k0[good], kf[good], 0.25)
        target = good[np.lexsort((rk[good - c0], pri))]
        newk[target] = np.sort(k0[good])
        moved += int((newk[good] != k0[good]).sum())
    sc = st.gate_scores(newk[None, :])
    return st.gate_keep(sc)[0], dict(slot_values_moved=moved)
