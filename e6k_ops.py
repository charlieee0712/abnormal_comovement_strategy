# -*- coding: utf-8 -*-
"""E6k 接入算子（plan §5–§7；brief W01 / W07；执行端补充 X02 / X03 / X06–X10）。
全部在 pool0 单元坐标（e6k_env.Seg）上；输入 k0 = 母体 K 腿坏度（= Struct.q0）、kf = 统一方向后的新坏度（pct），均为大值不利。
q 层（给 Struct.kept）：NATIVE / SZL / SZL_OWN / INC / INC_SUPPORT0 / INC_DOSE / SA
门层（给 Struct.down）：PM / HG / HG_ONLY
名单层（给 DEV）：RP（同业配对预算修复）/ LX（四账户配额 × 优先序移植）
A4b 专属：TREFIT（第二关 T 模型系数插值）/ POST2_INCREMENT（第二关前加入新增局部坏度）"""
import itertools

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment, milp, Bounds, LinearConstraint

import e6k_env as E

TOL_MATCH = 1e-12       # 配对总距离同值容差（百分位单位；X08）
TOL_BUDGET = 1e-12      # 预算复核容差（归一 size 单位）


# ====================================================================== q 层
def native_q(k0, kf, a):
    """FALLBACK：k = k0 + a·(kf − k0)，kf 缺失处取 k0（与 e6j_engine.blend 单分量同式）；a 可为 (n,) 数组。"""
    a = np.asarray(a, dtype=float)
    return np.where(np.isfinite(kf), (1 - a) * k0 + a * kf, k0)


def native_d(k0, kf):
    """NATIVE 的新增量 d = kf − k0（kf 缺失 → 0）。"""
    return np.where(np.isfinite(kf) & np.isfinite(k0), kf - k0, 0.0)


def local_rank(seg, v, G, valid, coord='mid'):
    """组内平均平局秩：G ≥ 2 按 z_T 固定阈值分组（缺 z → 不排、回退）；G = 1 = 当日全体（只作恒等桥接诊断）。
    coord='mid' → (rank − .5)/n（plan §5.2 源式）；'pct' → rank/n（与 NATIVE 坐标同式，只用于 A3-1 恒等锚）。组内有效 < 2 → NaN。"""
    ok = np.isfinite(v) & valid
    if G == 1:
        g = np.zeros(seg.n, np.int64)
    else:
        g = E.size_bins(seg.zT, G)
        ok &= g != E.UNK
    out = np.full(seg.n, np.nan)
    ix = np.flatnonzero(ok)
    if not len(ix):
        return out
    key = seg.ci.t[ix].astype(np.int64) * max(G, 1) + g[ix]
    df = pd.DataFrame({'k': key, 'v': v[ix]})
    r = df.groupby('k')['v'].rank(method='average').to_numpy()
    nn = df.groupby('k')['v'].transform('size').to_numpy().astype(float)
    val = (r - 0.5) / nn if coord == 'mid' else r / nn
    val[nn < 2] = np.nan
    out[ix] = val
    return out


def szl_q(seg, k0, kf, a, G):
    """SZL：k = (1−a)·k0 + a·kf_local；排名人群 = 同组 kf ∧ k0 ∧ z 有效（与 SZL_OWN 同一人群，执行端口径 X13）；
    kf_local 缺（n<2 / 新测量缺 / 缺 z）→ k0（plan §5.2）。"""
    kl = local_rank(seg, kf, G, np.isfinite(k0))
    return np.where(np.isfinite(kl), (1 - a) * k0 + a * kl, k0)


def szl_own_q(seg, k0, kf, a, G):
    """SZL_OWN：同分组、同缺失掩码（该测量 kf 有效）与同坐标处理施于旧 K，再混入旧 K（plan §5.2；K07）。"""
    kl = local_rank(seg, k0, G, np.isfinite(kf))
    return np.where(np.isfinite(kl), (1 - a) * k0 + a * kl, k0)


def inc_d(seg, k0, kf, gamma):
    """INC：C = 当日 k0 / kf / z_T 全有效；d = kf − k0；X = [z − mean_C z, z² − mean_C z²]；p = 投影；d_γ = d − γ·p；C 外 0（plan §5.3）。
    γ = 0 即 INC_SUPPORT0（C 外 0，C 内 d）。"""
    t = seg.ci.t
    z = seg.zT
    C = np.isfinite(k0) & np.isfinite(kf) & np.isfinite(z)
    out = np.zeros(seg.n)
    if not C.any():
        return out
    ix = np.flatnonzero(C)
    tt = t[ix]
    T = seg.T
    d = kf[ix] - k0[ix]
    zz = z[ix]
    if gamma == 0:
        out[ix] = d
        return out
    cnt = np.bincount(tt, minlength=T).astype(float)
    m1 = np.bincount(tt, zz, T) / np.maximum(cnt, 1)
    m2 = np.bincount(tt, zz * zz, T) / np.maximum(cnt, 1)
    x1 = zz - m1[tt]
    x2 = zz * zz - m2[tt]
    A = np.zeros((T, 2, 2))
    A[:, 0, 0] = np.bincount(tt, x1 * x1, T)
    A[:, 0, 1] = A[:, 1, 0] = np.bincount(tt, x1 * x2, T)
    A[:, 1, 1] = np.bincount(tt, x2 * x2, T)
    bvec = np.zeros((T, 2))
    bvec[:, 0] = np.bincount(tt, x1 * d, T)
    bvec[:, 1] = np.bincount(tt, x2 * d, T)
    beta = np.einsum('tij,tj->ti', np.linalg.pinv(A), bvec)
    p = x1 * beta[tt, 0] + x2 * beta[tt, 1]
    out[ix] = d - gamma * p
    return out


def inc_dose_d(seg, k0, kf, gamma):
    """INC_DOSE：C 与 INC 相同；m = mean_C d，u = d − m，v = d_γ − m，r = ‖v‖/‖u‖（逐日；‖u‖ = 0 → r = 0）；d_dose = m + r·u；C 外 0（plan §5.3）。"""
    t = seg.ci.t
    z = seg.zT
    C = np.isfinite(k0) & np.isfinite(kf) & np.isfinite(z)
    out = np.zeros(seg.n)
    if not C.any():
        return out
    ix = np.flatnonzero(C)
    tt = t[ix]
    T = seg.T
    d = kf[ix] - k0[ix]
    dg = inc_d(seg, k0, kf, gamma)[ix]
    cnt = np.bincount(tt, minlength=T).astype(float)
    m = np.bincount(tt, d, T) / np.maximum(cnt, 1)
    u = d - m[tt]
    v = dg - m[tt]
    nu = np.sqrt(np.bincount(tt, u * u, T))
    nv = np.sqrt(np.bincount(tt, v * v, T))
    r = np.where(nu > 0, nv / np.where(nu > 0, nu, 1), 0.0)
    out[ix] = m[tt] + r[tt] * u
    return out


def inc_q(k0, d, a):
    """k = k0 + a·d（不截零、不再 rank；评分可越原秩端点）。"""
    return k0 + np.asarray(a, dtype=float) * d


def sa_q_native(k0, kf, a, b):
    """SA（NATIVE 起点）：k = k0 + a·d·1(|d| ≥ b/100)（plan §7.1；X06：b 以 K 腿 0–1 单位）；指示为 1 处用与 native_q
    完全相同的算式 (1−a)·k0 + a·kf，保证 b = 0 逐位回无门账户（plan §7.1「b0 严格回对应无门账户」）。"""
    ind = np.isfinite(kf) & (np.abs(kf - k0) >= b / 100.0 - 1e-15)
    return np.where(ind, (1 - a) * k0 + a * kf, k0)


def sa_q_inc(k0, d, a, b):
    """SA（INC1 起点）：k = k0 + a·d·1(|d| ≥ b/100)；与 inc_q 同算式（b = 0 逐位 = INC1）。"""
    return k0 + a * (d * (np.abs(d) >= b / 100.0 - 1e-15))


def sa_dose_alpha(seg, d, a, b):
    """SA 共同剂量：a_t = a·Σ_C|d|·1(|d| ≥ b/100) / Σ_C|d|（分母 0 → 0），逐日（plan §7.4）。返回 (n,) 数组 α。"""
    t = seg.ci.t
    T = seg.T
    ad = np.abs(d)
    num = np.bincount(t, ad * (ad >= b / 100.0 - 1e-15), T)
    den = np.bincount(t, ad, T)
    at = np.where(den > 0, a * num / np.where(den > 0, den, 1), 0.0)
    return at[t]


# ====================================================================== 门层
def pm_gate(st, sc_child, gate_parent, gate_child, b_eff, tid_ids):
    """PM（plan §7.2）：同日固定配对——新晋成员按无带新分数由好到坏、退出成员由坏到好一一匹配（平局按规范 ticker），
    每对 score_out − score_in ≥ b_eff 才交换；结构单边编辑按无带规则执行；b = 0 直接返回无带新门（保留源平局端点）。
    输入均为门域坐标 (len(ids),)；返回修改后的门 (len(ids),) bool。"""
    if b_eff == 0:
        return gate_child.copy()
    dom = st.dom
    out = gate_parent.copy()
    for d in dom.days:
        a, b = dom.off[d], dom.off[d + 1]
        gp, gc, s = gate_parent[a:b], gate_child[a:b], sc_child[a:b]
        ins = np.flatnonzero(gc & ~gp)
        outs = np.flatnonzero(gp & ~gc)
        if not len(ins) and not len(outs):
            continue
        tid = tid_ids[a:b]
        ins = ins[np.lexsort((tid[ins], s[ins]))]
        outs = outs[np.lexsort((tid[outs], -s[outs]))]
        k = min(len(ins), len(outs))
        seg_out = out[a:b]
        seg_out[ins[k:]] = True
        seg_out[outs[k:]] = False
        if k:
            sw = (s[outs[:k]] - s[ins[:k]]) >= b_eff - 1e-15
            seg_out[outs[:k][sw]] = False
            seg_out[ins[:k][sw]] = True
    return out


def hg_gate(st, sc, b_eff, tid_ids, init_cols=None, return_state=False, hold_init=False):
    """HG（plan §7.3）：s_HG = s − b_eff·1(上一形成日本账户门内成员)；当日技术合法域（门域）取无带门同数（dom.K[d]）。
    状态按列（规范 ticker）跨日传递；池外 / 无效者不因曾入选而恢复；K[d] = 0 的日子门空 → 次日状态空。
    sc：(P, len(ids))；返回 (P, len(ids)) bool（与 init_cols：(P, Nc) bool 段首状态；默认全空）。
    hold_init（只供 X09 跨段连续诊断 v2；登记账户恒 False，路径不变）：段首预热日（K = 0）不清空 init，带到第一个形成日。"""
    dom = st.dom
    seg = st.seg
    ci = seg.ci
    P = sc.shape[0]
    cols = ci.c[st.ids]
    state = np.zeros((P, seg.Nc), bool) if init_cols is None else init_cols.copy()
    out = np.zeros(sc.shape, bool)
    Kd = dom.K
    started = False
    for d in range(seg.T):
        a, b = dom.off[d], dom.off[d + 1]
        newstate = np.zeros((P, seg.Nc), bool)
        if b > a and Kd[d] > 0:
            started = True
            cc = cols[a:b]
            s = sc[:, a:b] - b_eff * state[:, cc]
            if b_eff == 0:
                s = sc[:, a:b]
            idx = np.argsort(s, axis=1, kind='stable')[:, :Kd[d]]
            g = np.zeros((P, b - a), bool)
            np.put_along_axis(g, idx, True, axis=1)
            out[:, a:b] = g
            rr, jj = np.nonzero(g)
            newstate[rr, cc[jj]] = True
        if hold_init and not started:
            continue
        state = newstate
    if return_state:
        return out, state
    return out


def dose_alpha_from_edits(seg, st, gate_band, gate_nob, gate_parent, a):
    """PM / HG 共同剂量：a_t = a·min(1, e_b / e_0)；e_b / e_0 = 带 / 无带门相对父门的对称差人数；e_0 = 0 → a_t = a（NO_DOSE_MATCH）（plan §7.4）。"""
    dom = st.dom
    T = seg.T
    tt = seg.ci.t[st.ids]
    eb = np.bincount(tt, (gate_band ^ gate_parent).astype(float), T)
    e0 = np.bincount(tt, (gate_nob ^ gate_parent).astype(float), T)
    at = np.where(e0 > 0, a * np.minimum(1.0, eb / np.where(e0 > 0, e0, 1)), a)
    nodose = (e0 == 0)
    return at[seg.ci.t], nodose


# ====================================================================== A4b 专属：第二关带模型
def stage2_model(seg, st, ev_cells, fit_cells, coef_mix=None):
    """E6j diag_p.stage2_with_model 的逐日实现（源 neutralize_by_mcap：拟合集有效 < 10 → 原值）；
    coef_mix = (g, fit_old_cells)：T 系数 = (1−g)·coef_old + g·coef_new（两边都有合法同一模型才插值，否则沿 new 原生并计 COEF_INTERP_UNAVAILABLE）。
    返回 (kept 单元 bool, 插值不可用日数)。"""
    ci = seg.ci
    x = seg.env.R.logm_c
    y = st.st.M.T_raw_c
    out = np.zeros(seg.n, bool)
    n_unavail = 0
    pk = st.st.b

    def fit(cells):
        fv = cells[np.isfinite(x[cells]) & np.isfinite(y[cells])]
        if len(fv) >= 10:
            xm, ym = x[fv].mean(), y[fv].mean()
            b = np.mean((x[fv] - xm) * (y[fv] - ym)) / np.var(x[fv])
            return ym - b * xm, b
        return None

    for d in range(seg.T):
        a0, a1 = seg.off[d], seg.off[d + 1]
        if a0 == a1:
            continue
        sl = np.arange(a0, a1)
        ev = sl[ev_cells[sl]]
        if len(ev) < 6:
            continue
        cn = fit(sl[fit_cells[sl]])
        if coef_mix is not None:
            g, fit_old = coef_mix
            co = fit(sl[fit_old[sl]])
            if g == 0:                                   # 端点 g = 0：旧模型按其实际规则（无效 → 原值）
                cn = co
            elif cn is not None and co is not None:
                cn = ((1 - g) * co[0] + g * cn[0], (1 - g) * co[1] + g * cn[1])
            else:                                        # g ∈ (0,1) 无合法同一模型 → 沿新原生模型
                n_unavail += 1
        if cn is not None:
            val = y[ev] - (cn[0] + cn[1] * x[ev])
        else:
            val = y[ev].copy()
        ok = np.isfinite(val)
        if ok.sum() < 6:
            continue
        evv, vv = ev[ok], val[ok]
        pct = pd.Series(vv).rank(pct=True).to_numpy()
        Kk = E.IR.k_of(len(evv), pk)
        order = np.lexsort((ci.c[evv], pct))
        out[evv[order[:Kk]]] = True
    return out, n_unavail


def post2_kept(seg, st, s1_old, k0, kf, a):
    """POST2_INCREMENT（plan §5.6）：固定原 K 第一关 s1_old；在 s1_old 内完成源 T 中性化与 pct（dep_stage2_keep 同口径）；
    第二关截尾前对 T 坏度加 a·(新测量局部坏度 − 旧 K 局部坏度)，两局部秩在 s1_old ∩ 共同支持（k0 / kf 有效）上取 pct；
    共同支持外增量 0；之后按原第二关人数 keep、CVR。a = 0 ≡ 父。返回 kept 单元。"""
    ci = seg.ci
    x = seg.env.R.logm_c
    y = st.st.M.T_raw_c
    out = np.zeros(seg.n, bool)
    pk = st.st.b
    for d in range(seg.T):
        a0, a1 = seg.off[d], seg.off[d + 1]
        if a0 == a1:
            continue
        sl = np.arange(a0, a1)
        ev = sl[s1_old[sl]]
        if len(ev) < 6:
            continue
        fv = ev[np.isfinite(x[ev]) & np.isfinite(y[ev])]
        if len(fv) >= 10:
            xm, ym = x[fv].mean(), y[fv].mean()
            b = np.mean((x[fv] - xm) * (y[fv] - ym)) / np.var(x[fv])
            val = y[ev] - (ym - b * xm + b * x[ev])
        else:
            val = y[ev].copy()
        ok = np.isfinite(val)
        if ok.sum() < 6:
            continue
        evv, vv = ev[ok], val[ok]
        tb = pd.Series(vv).rank(pct=True).to_numpy()
        if a != 0:
            cs = np.isfinite(k0[evv]) & np.isfinite(kf[evv])
            if cs.sum() >= 1:
                ln = pd.Series(kf[evv][cs]).rank(pct=True).to_numpy()
                lo = pd.Series(k0[evv][cs]).rank(pct=True).to_numpy()
                inc = np.zeros(len(evv))
                inc[cs] = ln - lo
                tb = tb + a * inc
        Kk = E.IR.k_of(len(evv), pk)
        order = np.lexsort((ci.c[evv], tb))
        out[evv[order[:Kk]]] = True
    return out & ~st.st.drop


# ====================================================================== 名单层：LX
def lx_select(seg, st, quota_mask, order_keys, layers, legal):
    """V_ab：每层配额 n_g = |quota_mask ∩ g|，在合法域按优先序 (key1, key2, key3, 列位) 取前 n_g（plan §6.2；test_25–27 / 72–74）。"""
    if (quota_mask & ~legal).any():
        raise ValueError('LX：端点名单越出固定合法域（接线错误）')
    ci = seg.ci
    k1, k2, k3 = order_keys
    L = np.flatnonzero(legal)
    lay = layers[L]
    t = ci.t[L]
    grp = t.astype(np.int64) * (int(layers.max()) + 2) + (lay + 1)
    quota = pd.Series(quota_mask[L]).groupby(grp).transform('sum').to_numpy()
    o = np.lexsort((ci.c[L], k3[L], k2[L], k1[L], grp))
    gs = grp[o]
    newg = np.r_[True, gs[1:] != gs[:-1]]
    start = np.maximum.accumulate(np.where(newg, np.arange(len(gs)), 0))
    rank = np.arange(len(gs)) - start
    sel = rank < quota[o]
    out = np.zeros(seg.n, bool)
    out[L[o[sel]]] = True
    return out


def lx_layers(seg, k0, kind):
    """SIZE3 = z_T 三档（UNK 显式）；ISK = 行业 × size3 × 旧 K3（各自 UNK 显式）。返回每单元层号（≥ 0 的整数编码）。"""
    s3 = E.size_bins(seg.zT, 3) + 1                      # 0 = UNK
    if kind == 'SIZE3':
        return s3.astype(np.int64)
    k3 = E.size_bins(np.where(np.isfinite(k0), np.clip(k0, 1e-12, 1.0), np.nan), 3) + 1
    ind = seg.ic + 1                                     # 0 = UNK
    return (ind.astype(np.int64) * 4 + s3) * 4 + k3


# ====================================================================== 名单层：RP
def canonical_matching(out_ids, out_z, in_ids, in_z):
    """行业内一对一最小总 |z_in − z_out| 匹配，数量 = min；并列按排序后 (out_id, in_id) 边序逐项冻结（小图穷举、大图指派逐边冻结重解）。
    返回边列表 [(oi, ii)]（输入下标）。"""
    no, ni = len(out_ids), len(in_ids)
    k = min(no, ni)
    if k == 0:
        return []
    oo = np.argsort(out_ids, kind='stable')
    io = np.argsort(in_ids, kind='stable')
    oz, iz = np.asarray(out_z, float)[oo], np.asarray(in_z, float)[io]
    Cm = np.abs(oz[:, None] - iz[None, :])
    if k <= 3 and max(no, ni) <= 6:
        cands = []
        if no <= ni:
            for perm in itertools.permutations(range(ni), no):
                cands.append((sum(Cm[j, perm[j]] for j in range(no)), tuple(sorted((j, perm[j]) for j in range(no)))))
        else:
            for perm in itertools.permutations(range(no), ni):
                cands.append((sum(Cm[perm[j], j] for j in range(ni)), tuple(sorted((perm[j], j) for j in range(ni)))))
        best = min(c for c, _ in cands)
        edges = min(e for c, e in cands if abs(c - best) <= TOL_MATCH)
    else:
        edges = _lsa_lex(Cm)
    return [(int(oo[a]), int(io[b])) for a, b in edges]


def _lsa_cost(Cm):
    r, c = linear_sum_assignment(Cm)
    return float(Cm[r, c].sum())


def _lsa_lex(Cm):
    """指派逐边冻结：边按 (out, in) 排序逐项试纳入——纳入后剩余子问题最优 + 已纳入代价 = 全局最优（容差内）则冻结。"""
    no, ni = Cm.shape
    k = min(no, ni)
    best = _lsa_cost(Cm)
    fixed = []
    used_o, used_i = set(), set()
    acc = 0.0
    for a in range(no):
        if len(fixed) == k:
            break
        if a in used_o:
            continue
        for b in range(ni):
            if b in used_i:
                continue
            ro = [x for x in range(no) if x not in used_o and x != a]
            rc = [y for y in range(ni) if y not in used_i and y != b]
            need = k - len(fixed) - 1
            if need > 0:
                sub = Cm[np.ix_(ro, rc)]
                if min(sub.shape) < need:
                    continue
                rest = _lsa_cost(sub)
            else:
                rest = 0.0
            if abs(acc + Cm[a, b] + rest - best) <= TOL_MATCH:
                fixed.append((a, b)); used_o.add(a); used_i.add(b); acc += Cm[a, b]
                break
    if len(fixed) != k:
        raise RuntimeError('指派逐边冻结失败')
    return tuple(sorted(fixed))


def choose_pairs_dfs(c, util, budget, max_nodes=20_000_000):
    """预算选择三级词典序（数量 → 整数效用 → 配对 ID 字典序，1 优先）的精确深搜；c / util 已按配对 ID 排序。
    返回 (选择 bool 数组, 节点数)；节点超限返回 (None, 节点数) 由 MILP 兜底。"""
    m = len(c)
    c = np.asarray(c, float)
    u = np.asarray(util, float)
    if m == 0:
        return np.zeros(0, bool), 0
    if np.isinf(budget) or abs(c.sum()) <= budget + TOL_BUDGET:
        return np.ones(m, bool), 0
    rem_abs = np.r_[np.cumsum(np.abs(c)[::-1])[::-1], 0.0]
    rem_u = np.r_[np.cumsum(u[::-1])[::-1], 0.0]
    best = [-1, -1.0, None]
    x = np.zeros(m, bool)
    nodes = [0]

    def rec(j, cnt, s, ut):
        nodes[0] += 1
        if nodes[0] > max_nodes:
            return
        if j == m:
            if abs(s) <= budget + TOL_BUDGET:
                if cnt > best[0] or (cnt == best[0] and ut > best[1] + 0.5):
                    best[0], best[1], best[2] = cnt, ut, x.copy()
            return
        left = m - j
        if cnt + left < best[0]:
            return
        if cnt + left == best[0] and ut + rem_u[j] <= best[1] + 0.5:
            return
        if abs(s) - rem_abs[j] > budget + TOL_BUDGET:
            return
        x[j] = True
        rec(j + 1, cnt + 1, s + c[j], ut + u[j])
        x[j] = False
        rec(j + 1, cnt, s, ut)

    rec(0, 0, 0.0, 0.0)
    if nodes[0] > max_nodes:
        return None, nodes[0]
    return best[2], nodes[0]


def choose_pairs_milp(c, util, budget, scale=1e6):
    """plan §16.3 choose_pairs_lex 的逐级 MILP（贡献缩放 scale 以消去求解器可行性容差；X08），解按原系数复核。c / util 已按配对 ID 排序。"""
    c = np.asarray(c, float)
    uu = np.asarray(util, float)
    n = len(c)
    if n == 0:
        return np.zeros(0, bool)
    if np.isinf(budget) or abs(c.sum()) <= budget + TOL_BUDGET:
        return np.ones(n, bool)
    cc = c * scale
    B = budget * scale
    mat = [cc]
    lo = [-B]
    hi = [B]

    def solve(obj, lower=None, upper=None):
        return milp(np.asarray(obj, float), integrality=np.ones(n),
                    bounds=Bounds(np.zeros(n) if lower is None else lower, np.ones(n) if upper is None else upper),
                    constraints=LinearConstraint(np.asarray(mat), lo, hi), options={'mip_rel_gap': 0.})
    r = solve(-np.ones(n))
    if not r.success:
        raise RuntimeError(r.message)
    count = int(np.rint(r.x).sum())
    mat.append(np.ones(n)); lo.append(count); hi.append(count)
    r = solve(-uu)
    if not r.success:
        raise RuntimeError(r.message)
    util = int(np.rint(uu @ np.rint(r.x)))
    mat.append(uu); lo.append(util); hi.append(util)
    low = np.zeros(n)
    high = np.ones(n)
    for j in range(n):
        trial = low.copy()
        trial[j] = 1
        r = solve(np.zeros(n), trial, high)
        if r.success:
            low[j] = 1
        elif r.status == 2:
            high[j] = 0
        else:
            raise RuntimeError('unresolved tie feasibility')
    z = low.astype(bool)
    if z.sum() != count or int(uu @ z) != util or abs(c @ z) > budget + TOL_BUDGET:
        raise AssertionError('lex verification failed')
    return z


def choose_pairs_milp_checked(c, util, budget, scale=1e6):
    """恢复路径 1（只在主路径复核失败的日用；X08 / plan §5.4 第 6 条）：逐级 MILP 关闭 presolve，每一级求解器返回的见证解都按原系数复核
    （预算 / 已冻结的数量与效用 / 当前上下界）；任一复核不过即抛错，不接受求解器的可行声明本身。"""
    c = np.asarray(c, float)
    uu = np.asarray(util, float)
    n = len(c)
    mat, lo, hi = [c * scale], [-budget * scale], [budget * scale]

    def solve(obj, lower, upper):
        return milp(np.asarray(obj, float), integrality=np.ones(n), bounds=Bounds(lower, upper),
                    constraints=LinearConstraint(np.asarray(mat), lo, hi), options={'mip_rel_gap': 0., 'presolve': False})

    def witness(r, lower, upper, count=None, util_=None):
        if not r.success:
            raise RuntimeError('recovery: %s' % r.message)
        x = np.rint(r.x)
        if (abs(c @ x) > budget + TOL_BUDGET or (x < lower).any() or (x > upper).any()
                or (count is not None and int(x.sum()) != count) or (util_ is not None and int(uu @ x) != util_)):
            raise AssertionError('recovery witness failed')
        return x

    zero, one = np.zeros(n), np.ones(n)
    count = int(witness(solve(-one, zero, one), zero, one).sum())
    mat.append(one); lo.append(count); hi.append(count)
    ut = int(uu @ witness(solve(-uu, zero, one), zero, one, count))
    mat.append(uu); lo.append(ut); hi.append(ut)
    low, high = zero.copy(), one.copy()
    for j in range(n):
        trial = low.copy()
        trial[j] = 1
        r = solve(zero, trial, high)
        if r.success:
            witness(r, trial, high, count, ut)
            low[j] = 1
        elif r.status == 2:
            high[j] = 0
        else:
            raise RuntimeError('recovery: unresolved tie feasibility')
    z = low.astype(bool)
    if z.sum() != count or int(uu @ z) != ut or abs(c @ z) > budget + TOL_BUDGET:
        raise AssertionError('recovery lex verification failed')
    return z


def choose_pairs_dfs_signed(c, util, budget, max_nodes=50_000_000):
    """恢复路径 2：与 choose_pairs_dfs 同一三级词典序的精确深搜，另加带符号可达界剪枝（剩余正 / 负贡献之和）；节点超限返回 (None, 节点数)。"""
    m = len(c)
    c = np.asarray(c, float)
    u = np.asarray(util, float)
    rem_pos = np.r_[np.cumsum(np.maximum(c, 0.0)[::-1])[::-1], 0.0]
    rem_neg = np.r_[np.cumsum(np.minimum(c, 0.0)[::-1])[::-1], 0.0]
    rem_u = np.r_[np.cumsum(u[::-1])[::-1], 0.0]
    best = [-1, -1.0, None]
    x = np.zeros(m, bool)
    nodes = [0]

    def rec(j, cnt, s, ut):
        nodes[0] += 1
        if nodes[0] > max_nodes:
            return
        if s + rem_neg[j] > budget + TOL_BUDGET or s + rem_pos[j] < -budget - TOL_BUDGET:
            return
        if j == m:
            if abs(s) <= budget + TOL_BUDGET and (cnt > best[0] or (cnt == best[0] and ut > best[1] + 0.5)):
                best[0], best[1], best[2] = cnt, ut, x.copy()
            return
        left = m - j
        if cnt + left < best[0]:
            return
        if cnt + left == best[0] and ut + rem_u[j] <= best[1] + 0.5:
            return
        x[j] = True
        rec(j + 1, cnt + 1, s + c[j], ut + u[j])
        x[j] = False
        rec(j + 1, cnt, s, ut)

    rec(0, 0, 0.0, 0.0)
    if nodes[0] > max_nodes:
        return None, nodes[0]
    return best[2], nodes[0]


def recover_lex(c, util, budget):
    """主路径（DFS 节点上限 → 逐级 MILP）复核失败的日：两条独立精确路径各求一次。两者都成且一致 → 采用（'recovered_both'）；
    只一条成 → 采用该解（'recovered_milp_checked' / 'recovered_dfs_signed'）；都不成或两者不一致 → (None, 原因)，调用方隔离回父并标 SOLVER_LIMIT。"""
    try:
        zm = choose_pairs_milp_checked(c, util, budget)
    except (AssertionError, RuntimeError, ValueError):
        zm = None
    try:
        zd, _ = choose_pairs_dfs_signed(c, util, budget)
    except RecursionError:
        zd = None
    if zm is not None and zd is not None:
        return (zm, 'recovered_both') if np.array_equal(zm, zd) else (None, 'SOLVER_LIMIT_RECOVERY_DISAGREE')
    if zm is not None:
        return zm, 'recovered_milp_checked'
    if zd is not None:
        return zd, 'recovered_dfs_signed'
    return None, 'SOLVER_LIMIT'


def rp_day(seg, d, parent_d, child_d, w_par, tau, util_rank):
    """一日 RP。parent_d / child_d：当日单元 bool（切片坐标）；w_par：父当日 DEV 权重（切片坐标）；util_rank：子边扩展优先序名次（切片坐标，越小越优先）。
    返回 (修复后当日名单, 统计 dict)。"""
    a0, a1 = seg.off[d], seg.off[d + 1]
    z = seg.zT[a0:a1]
    ic = seg.ic[a0:a1]
    tid = seg.tid[a0:a1]
    ins_all = np.flatnonzero(child_d & ~parent_d)
    outs_all = np.flatnonzero(parent_d & ~child_d)
    stats = dict(n_in=len(ins_all), n_out=len(outs_all), n_pairs=0, n_keep=0, solver='none', nodes=0, unk=0)
    P = float(w_par.sum())
    res = parent_d.copy()
    if P <= 0 or not len(ins_all) or not len(outs_all):
        return res, stats
    okz = lambda ix: ix[np.isfinite(z[ix]) & (ic[ix] >= 0)]
    ins, outs = okz(ins_all), okz(outs_all)
    stats['unk'] = (len(ins_all) - len(ins)) + (len(outs_all) - len(outs))
    pairs = []
    for g in np.intersect1d(np.unique(ic[ins]), np.unique(ic[outs])):
        ii = ins[ic[ins] == g]
        oo = outs[ic[outs] == g]
        for oi, jj in canonical_matching(tid[oo], z[oo], tid[ii], z[ii]):
            pairs.append((oo[oi], ii[jj]))
    if not pairs:
        return res, stats
    pairs.sort(key=lambda e: (tid[e[0]], tid[e[1]]))
    m = len(pairs)
    stats['n_pairs'] = m
    cvec = np.array([w_par[o] * (z[i] - z[o]) / P for o, i in pairs])
    inr = np.array([util_rank[i] for _, i in pairs])
    r = np.empty(m, np.int64)
    r[np.argsort(inr, kind='stable')] = np.arange(1, m + 1)
    util = (m + 1 - r).astype(float)
    budget = np.inf if tau is None else tau / 100.0
    if np.isinf(budget) or abs(cvec.sum()) <= budget + TOL_BUDGET:
        sel = np.ones(m, bool)
        stats['solver'] = 'accept_all'
    else:
        sel, nodes = (choose_pairs_dfs(cvec, util, budget) if m <= 40 else (None, 0))
        stats['nodes'] = nodes
        stats['solver'] = 'dfs'
        if sel is None:
            try:
                sel = choose_pairs_milp(cvec, util, budget)
                stats['solver'] = 'milp'
            except (AssertionError, RuntimeError):              # X08 异常日：先独立恢复，不成则隔离回父并标 SOLVER_LIMIT（plan §5.4 第 6 条）
                sel, how = recover_lex(cvec, util, budget)
                stats['solver'] = how
                print('RP_RECOVERY day=%d m=%d tau=%s outcome=%s' % (d, m, tau, how), flush=True)
                if sel is None:
                    return parent_d.copy(), stats
    if abs(cvec @ sel) > budget + TOL_BUDGET:
        raise AssertionError('RP 预算复核失败')
    for k_, (o, i) in enumerate(pairs):
        if sel[k_]:
            res[o] = False
            res[i] = True
    stats['n_keep'] = int(sel.sum())
    return res, stats


def rp_list(seg, parent, child, w_parent_cells, taus, util_rank):
    """全段 RP：返回 {tau: 名单 (n,) bool} 与逐日统计 DataFrame。w_parent_cells：父 DEV 权重（单元坐标）。"""
    out = {tau: parent.copy() for tau in taus}
    rows = []
    for d in range(seg.T):
        a0, a1 = seg.off[d], seg.off[d + 1]
        if a0 == a1:
            continue
        pd_, cd_ = parent[a0:a1], child[a0:a1]
        if (pd_ == cd_).all():
            continue
        for tau in taus:
            r, st = rp_day(seg, d, pd_, cd_, w_parent_cells[a0:a1], tau, util_rank[a0:a1])
            out[tau][a0:a1] = r
            st.update(day=d, tau=('INF' if tau is None else tau))
            rows.append(st)
    return out, pd.DataFrame(rows)


def rank_by_keys(seg, keys):
    """每日按 (key1, key2, key3, 列位) 的名次（0 起），单元坐标。"""
    ci = seg.ci
    k1, k2, k3 = keys
    o = np.lexsort((ci.c, k3, k2, k1, ci.t))
    ts = ci.t[o]
    newg = np.r_[True, ts[1:] != ts[:-1]]
    start = np.maximum.accumulate(np.where(newg, np.arange(len(ts)), 0))
    r = np.empty(seg.n, np.int64)
    r[o] = np.arange(len(ts)) - start
    return r
