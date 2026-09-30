# -*- coding: utf-8 -*-
"""E6l 记忆 / 状态 / 随机标记算子（plan §5 / §6.2 / §7.3；brief W03–W05 / W13；附录 A3）。
全部在门域坐标（Struct.ids，(t, c) 序）上逐日递推，P 条路径同批（每条路径独立状态）。选择与 E6k hg_gate 同算式：
  s = sc − b_eff·mark（mark ∈ {0,1} 逐格），当日取 dom.K[d] 个最小（argsort stable = 源 KeepDom 同序）；
  某路径当日 bonus 全 0 → 直接取源无带门 U（source_U 及源平局，plan §5.1a / R06）。b_eff = b·Struct.bunit（Mmean = b/3）。
规则（mark 的来源）：
  HG      上一形成日本账户门内成员 G_{t−1}（递归选择记忆）；b 常数
  STATE   同 HG，b 逐日取调度（e6l_state；未知 → 10）
  LAG1    上一形成日同测量同 α 的无带门 U_{t−1}（非递归）
  DECAY   bonus = b_eff·1(G_{t−1})·max(0, 1 − max(age − 1, 0)/L)，age = t − last_confirmed（最近一次被 U 纳入的日；当日不在门域 → 清空）
  RMARK   本路径自己的 G_{t−1} 标记在分组内打乱（组内标记数守恒；UNIFORM：全门域一组；ISK：行业 > 旧 K3 > size3 回退树叶）；
          组内按 u（E6j Grid.u_cells，稳定哈希；P5 = 绝对交易日 // 5）降序的前 m_g 名得标记
  INV     上 H 个形成日本账户最终名单（门 → 下游 → 否决之后，DEV 权重 > 0 ⇔ 在名单里）有持仓 → 标记；按 H 独立递推（plan §5.5 / W05）
          INV_LOOP（MATCH_CAP_INV_LOOP 诊断）：当日 p* = min(子提议资本, 父目标资本) = 0 时该日批次记 0（不进库存）
空门日（K[d] = 0，含段首预热）：门空、次日状态空；DECAY 的 last_confirmed 全清。
checkpoint（plan §5.6 / R04 / R05）：状态 = next_day、G / U（P × Nc）、last（P × Nc，−inf = 无）、INV 持仓计数与最近 H 日名单；
  resume 时 next_day 与股票身份（列 ticker 哈希）必须一致，否则拒绝。"""
import hashlib

import numpy as np

import e6i_randoms as IR

STATE_OPS = ('VOL_HI15', 'VOL_HI5', 'VOL_MEAN15', 'VOL_MEAN5')
RMARK_MECHS = ('RMARK_UNIFORM_IID', 'RMARK_UNIFORM_P5', 'RMARK_ISK_P5')


def parse_op(op):
    """算子名 → 规则。"""
    if op == 'NATIVE':
        return dict(kind='NATIVE', b=0.0)
    if op.startswith('HG_ONLY'):
        return dict(kind='HG', b=float(op[7:]))
    if op.startswith('HG'):
        return dict(kind='HG', b=float(op[2:]))
    if op.startswith('LAG1_'):
        return dict(kind='LAG1', b=float(op.split('_')[1]))
    if op.startswith('DECAY'):
        Lb = op[5:].split('_')
        return dict(kind='DECAY', L=float(Lb[0]), b=float(Lb[1]))
    if op.startswith('INV'):
        return dict(kind='INV', b=float(op[3:]))
    if op in STATE_OPS:
        return dict(kind='STATE', schedule=op, b=float('nan'))
    raise ValueError(op)


def ids_hash(tickers):
    return hashlib.blake2b(','.join(map(str, tickers)).encode(), digest_size=8).hexdigest()


def cold_state(P, Nc, tick_hash):
    return dict(next_day=0, ids=tick_hash, G=np.zeros((P, Nc), bool), U=np.zeros((P, Nc), bool),
                last=np.full((P, Nc), -np.inf))


def _date_at(seg, d):
    return str(seg.dates[d])[:10] if d < seg.T else 'END'


def _check_resume(state, d0, tick_hash, seg=None):
    """恢复身份（plan §5.6）：下一日序号、下一绝对交易日、股票身份（列 ticker 哈希）三者都须一致，否则拒绝（不重映射）。"""
    bad = state['next_day'] != d0 or state['ids'] != tick_hash
    if seg is not None and state.get('next_date') is not None:
        bad |= state['next_date'] != _date_at(seg, d0)
    if bad:
        raise ValueError('checkpoint 身份不符：next_day %s vs %s；next_date %s vs %s；ids %s vs %s' % (
            state['next_day'], d0, state.get('next_date'), _date_at(seg, d0) if seg is not None else '?', state['ids'], tick_hash))


def select_rows(s, K, rows=None):
    """(P, m) 每行取 K 个最小（argsort stable）→ bool。"""
    out = np.zeros(s.shape, bool)
    if K <= 0:
        return out
    idx = np.argsort(s, axis=1, kind='stable')[:, :K]
    np.put_along_axis(out, idx, True, axis=1)
    return out


def mem_gate(st, sc, U, rule, b_day=None, state=None, d0=0, d1=None, rmark=None, record=False):
    """门层递推（HG / STATE / LAG1 / DECAY / RMARK）。sc、U：(P, len(ids))；b_day：(T,) 逐日 b（K 坏度百分位点）。
    rmark：dict(groups=(len(ids),) int 组号或 None（全门域一组）, u=callable(d, a, b) → (P, b − a) 优先分数)。
    返回 (G (P, len(ids)) bool, 新状态, 记录 dict 或 None)。"""
    dom = st.dom
    seg = st.seg
    P = sc.shape[0]
    Nc = seg.Nc
    T = seg.T
    d1 = T if d1 is None else d1
    cols = seg.ci.c[st.ids]
    tick = ids_hash(seg.S.ccolnames)
    stt = cold_state(P, Nc, tick) if state is None else {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in state.items()}
    if state is not None:
        _check_resume(stt, d0, tick, seg)
    kind = rule['kind']
    L_ = rule.get('L')
    G = np.zeros(sc.shape, bool)
    rec = dict(bonus_rows=0, reliant=np.zeros(P), days=0) if record else None
    Gs, Us, last = stt['G'], stt['U'], stt['last']
    domcol = np.zeros(Nc, bool)
    for d in range(d0, d1):
        a, b = dom.off[d], dom.off[d + 1]
        if b == a or dom.K[d] == 0:
            Gs = np.zeros((P, Nc), bool)
            Us = np.zeros((P, Nc), bool)
            last[:] = -np.inf
            continue
        cc = cols[a:b]
        s = sc[:, a:b]
        Ud = U[:, a:b]
        be = float(b_day[d]) * st.bunit
        if kind == 'DECAY':
            domcol[:] = False
            domcol[cc] = True
            last[:, ~domcol] = -np.inf
            rr, jj = np.nonzero(Ud)
            last[rr, cc[jj]] = d
        if kind in ('HG', 'STATE'):
            mark = Gs[:, cc]
            bon = be * mark
        elif kind == 'LAG1':
            mark = Us[:, cc]
            bon = be * mark
        elif kind == 'DECAY':
            prev = Gs[:, cc]
            age = d - last[:, cc]
            if np.isinf(L_):                                   # 机械端点 L → ∞ ≡ HG（spec decay_bonus 同式）
                fac = np.where(np.isfinite(age), 1.0, 0.0)
            else:
                with np.errstate(invalid='ignore'):
                    fac = np.where(np.isfinite(age), np.maximum(0.0, 1.0 - np.maximum(age - 1.0, 0.0) / L_), 0.0)
            bon = be * prev * fac
        elif kind == 'RMARK':
            mark = permute_marks_day(Gs[:, cc], rmark['groups'][a:b] if rmark['groups'] is not None else None, rmark['u'](d, a, b))
            bon = be * mark
        else:
            raise ValueError(kind)
        nz = (bon != 0).any(axis=1)
        g = Ud.copy()
        if nz.any():
            g[nz] = select_rows(s[nz] - bon[nz], int(dom.K[d]))
        G[:, a:b] = g
        Gs = np.zeros((P, Nc), bool)
        rr, jj = np.nonzero(g)
        Gs[rr, cc[jj]] = True
        Us = np.zeros((P, Nc), bool)
        rr, jj = np.nonzero(Ud)
        Us[rr, cc[jj]] = True
        if record:
            rec['days'] += 1
            rec['bonus_rows'] += int(nz.sum())
            rec['reliant'] += (g & ~Ud).sum(axis=1)
    stt.update(next_day=d1, next_date=_date_at(seg, d1), G=Gs, U=Us, last=last)
    return G, stt, rec


def permute_marks_day(mark, groups, u):
    """组内标记数守恒的置换：每行（路径）每组 m_g 个标记给组内 u 降序前 m_g 名。mark (P, m) bool；groups (m,) int 或 None；u (P, m)。"""
    P, m = mark.shape
    if groups is None:
        g = np.zeros(m, np.int64)
    else:
        g = np.unique(np.asarray(groups, np.int64), return_inverse=True)[1].ravel()   # 叶号为全局编号：逐日重编
    ng = int(g.max()) + 1 if m else 0
    out = np.zeros((P, m), bool)
    if m == 0:
        return out
    key = g[None, :] * 2.0 + (1.0 - u)                 # 组升序、u 降序（u ∈ [0, 1)）
    o = np.argsort(key, axis=1, kind='stable')
    gs = g[o]                                           # (P, m) 排序后的组号
    cnt = np.bincount(g, minlength=ng)
    start = np.r_[0, np.cumsum(cnt)[:-1]]
    pos = np.arange(m)[None, :] - start[gs]
    mg = np.zeros((P, ng), np.int64)
    for p in range(P):
        mg[p] = np.bincount(g, weights=mark[p].astype(float), minlength=ng).astype(np.int64)
    sel = pos < np.take_along_axis(mg, gs, axis=1)
    np.put_along_axis(out, o, sel, axis=1)
    return out


# ====================================================================== 下游（逐日）与 INV
def stage2_day(R, M, s1, cid_day, pctkeep_b, c_of):
    """= IR.dep_stage2_keep 限于一个交易日（同算式、同累加次序）。s1：(P, m) bool（该日 pool0 单元上）；cid_day：(m,) 单元号；c_of：单元 → 列。"""
    P, m = s1.shape
    kept = np.zeros((P, m), bool)
    pi, jj = np.nonzero(s1)
    if not len(pi):
        return kept
    cid = cid_day[jj]
    key = pi
    nk = P
    npool = np.bincount(key, minlength=nk)
    x = R.logm_c[cid]
    y = M.T_raw_c[cid]
    fy = np.isfinite(y)
    valid = fy & np.isfinite(x)
    nv = np.bincount(key, weights=valid.astype(float), minlength=nk)
    kv, xv, yv = key[valid], x[valid], y[valid]
    with np.errstate(all='ignore'):
        xm = np.bincount(kv, weights=xv, minlength=nk) / nv
        ym = np.bincount(kv, weights=yv, minlength=nk) / nv
        dx = xv - xm[kv]
        dy = yv - ym[kv]
        var = np.bincount(kv, weights=dx * dx, minlength=nk) / nv
        cov = np.bincount(kv, weights=dx * dy, minlength=nk) / nv
        beta = cov / var
        alpha = ym - beta * xm
    use_raw = nv[key] < 10
    val = np.full(len(cid), np.nan)
    a_ = use_raw & fy
    val[a_] = y[a_]
    r_ = (~use_raw) & valid
    with np.errstate(all='ignore'):
        val[r_] = y[r_] - (alpha[key[r_]] + beta[key[r_]] * x[r_])
    fv = np.isfinite(val)
    nfin = np.bincount(key[fv], minlength=nk)
    ok = fv & (npool[key] >= 6) & (nfin[key] >= 6)
    kk, vv, jk = key[ok], val[ok], jj[ok]
    if len(kk) == 0:
        return kept
    o = np.lexsort((vv, kk))
    ks, vs = kk[o], vv[o]
    newg = np.r_[True, ks[1:] != ks[:-1]]
    gstart = np.maximum.accumulate(np.where(newg, np.arange(len(ks)), 0))
    pos = np.arange(len(ks)) - gstart
    newr = newg | np.r_[True, vs[1:] != vs[:-1]]
    rid = np.cumsum(newr) - 1
    rfirst = pos[newr]
    rlast = np.r_[pos[np.flatnonzero(newr)[1:] - 1], pos[-1]]
    rank = (rfirst[rid] + rlast[rid]) / 2.0 + 1.0
    ng = np.bincount(kk, minlength=nk)
    pct = np.empty(len(kk))
    pct[o] = rank / ng[ks]
    o2 = np.lexsort((c_of[cid_day[jk]], pct, kk))
    ks2 = kk[o2]
    newg2 = np.r_[True, ks2[1:] != ks2[:-1]]
    gst2 = np.maximum.accumulate(np.where(newg2, np.arange(len(ks2)), 0))
    pos2 = np.arange(len(ks2)) - gst2
    Kg = np.zeros(nk, np.int64)
    for gkey in np.flatnonzero(ng):
        Kg[gkey] = IR.k_of(int(ng[gkey]), pctkeep_b)
    sel = pos2 < Kg[ks2]
    kept[kk[o2][sel], jk[o2][sel]] = True
    return kept


def down_day(st, d, gate_day):
    """一个交易日的下游：gate_day (P, b − a) 门域格 → (P, m) 该日 pool0 单元的最终名单（含否决）。"""
    seg = st.seg
    dom = st.dom
    a, b = dom.off[d], dom.off[d + 1]
    c0, c1 = seg.off[d], seg.off[d + 1]
    m = c1 - c0
    P = gate_day.shape[0]
    g = np.zeros((P, m), bool)
    g[:, st.ids[a:b] - c0] = gate_day
    s = st.st
    cells = np.arange(c0, c1)
    if st.kind == 'A4b':
        k = stage2_day(seg.env.R, s.M, g, cells, s.b, seg.ci.c)
        return k & ~s.drop[None, c0:c1]
    if st.kind == 'union':
        return g & s.base[None, c0:c1]
    return g & ~s.drop[None, c0:c1]


def inv_path(st, sc, U, b, H, state=None, d0=0, d1=None, loop_parent_cap=None, record=False):
    """INV 递推（plan §5.5 / W05）：A_i,T = 1(本账户最终名单在 [T−H, T−1] 任一形成日含 i)；门 → 下游 → 否决逐日。
    loop_parent_cap：(T,) 父目标资本（MATCH_CAP_INV_LOOP：p* = min(子提议资本, 父资本) = 0 的日不进库存）。
    返回 (G (P, len(ids)), F (P, n) 最终名单, 状态, 记录)。"""
    dom = st.dom
    seg = st.seg
    P = sc.shape[0]
    Nc, T, n = seg.Nc, seg.T, seg.n
    d1 = T if d1 is None else d1
    cols = seg.ci.c[st.ids]
    tick = ids_hash(seg.S.ccolnames)
    if state is None:
        stt = dict(next_day=0, ids=tick, H=int(H), cnt=np.zeros((P, Nc), np.int16), ring=[[] for _ in range(int(H) + 1)])
    else:
        stt = {k: (v.copy() if isinstance(v, np.ndarray) else ([list(x) for x in v] if k == 'ring' else v)) for k, v in state.items()}
        _check_resume(stt, d0, tick, seg)
        if stt['H'] != int(H):
            raise ValueError('INV checkpoint H 不符')
    be = float(b) * st.bunit
    G = np.zeros(sc.shape, bool)
    F = np.zeros((P, n), bool)
    cnt = stt['cnt']
    ring = stt['ring']
    rec = dict(marked=np.zeros(P), dom_cells=np.zeros(P), bonus_days=0, days=0, saturated_days=np.zeros(P)) if record else None
    for d in range(d0, d1):
        slot = d % (int(H) + 1)                         # 环长 H + 1：日 d 开始时移出形成日 d − H − 1 的批次
        old = ring[slot]
        if old:                                          # 退出窗口 [d − H, d − 1] 的批次（形成日 d − H − 1）
            pp, cc_ = old
            np.subtract.at(cnt, (pp, cc_), 1)
        a, b_ = dom.off[d], dom.off[d + 1]
        fin_pairs = None
        if b_ > a and dom.K[d] > 0:
            cc = cols[a:b_]
            mark = cnt[:, cc] > 0
            bon = be * mark
            nz = (bon != 0).any(axis=1)
            g = U[:, a:b_].copy()
            if nz.any():
                g[nz] = select_rows(sc[:, a:b_][nz] - bon[nz], int(dom.K[d]))
            G[:, a:b_] = g
            fd = down_day(st, d, g)
            c0 = seg.off[d]
            F[:, c0:c0 + fd.shape[1]] = fd
            if loop_parent_cap is not None:
                keep_day = fd.any(axis=1) & (float(loop_parent_cap[d]) > 0)
                fd = fd & keep_day[:, None]
            pp, jj = np.nonzero(fd)
            if len(pp):
                cc2 = seg.ci.c[c0 + jj]
                np.add.at(cnt, (pp, cc2), 1)
                fin_pairs = (pp, cc2)
            if record:
                rec['days'] += 1
                rec['bonus_days'] += int(nz.any())
                rec['marked'] += mark.sum(axis=1)
                rec['dom_cells'] += mark.shape[1]
                rec['saturated_days'] += mark.all(axis=1)
        ring[slot] = fin_pairs if fin_pairs is not None else []
    stt.update(next_day=d1, next_date=_date_at(seg, d1), cnt=cnt, ring=ring)
    return G, F, stt, rec


# ====================================================================== KERNEL_DOSE（plan §4.4a）
def kernel_dose(seg, k0, kq0, ks):
    """逐日 C = {k0、kQ0、ksmooth 有限}：d_dose = mean_C(ds) + sd_C(ds)/sd_C(d0)·(d0 − mean_C(d0))（ddof 0）；
    tol = 64·eps·max(1, max|k0|, max|kQ0|, max|ksmooth|)（C 上）；sd(d0) ≤ tol → 只用 mean(ds)（RMS_UNMATCHED；ds 也常数 → MATCHED_CONSTANT）。
    返回 (d_dose 单元数组（C 外 0），逐日状态码数组)。"""
    ci = seg.ci
    out = np.zeros(seg.n)
    status = np.array(['NO_SUPPORT'] * seg.T, dtype=object)
    C = np.isfinite(k0) & np.isfinite(kq0) & np.isfinite(ks)
    eps = np.finfo(float).eps
    for d in range(seg.T):
        a, b = seg.off[d], seg.off[d + 1]
        ix = np.arange(a, b)[C[a:b]]
        if not len(ix):
            continue
        d0 = kq0[ix] - k0[ix]
        ds = ks[ix] - k0[ix]
        s0, sz = np.std(d0), np.std(ds)
        tol = 64 * eps * max(1.0, float(np.max(np.abs(k0[ix]))), float(np.max(np.abs(kq0[ix]))), float(np.max(np.abs(ks[ix]))))
        if s0 <= tol:
            out[ix] = np.mean(ds)
            status[d] = 'MATCHED_CONSTANT' if sz <= tol else 'RMS_UNMATCHED'
        else:
            out[ix] = np.mean(ds) + (sz / s0) * (d0 - np.mean(d0))
            status[d] = 'MATCHED_MEAN_RMS'
    return out, status
