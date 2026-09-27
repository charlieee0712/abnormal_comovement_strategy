# -*- coding: utf-8 -*-
"""E6j Stage 0 第 4 项（brief v1.2 §2；plan §3.3 / §3.4 / §5）：新测量合成检验 + 真实字段检验 + J 成员缓存。
  --synthetic       玩具网格（稳定哈希种子）上的代数 / 因果 / 退化状态检验（不碰行情）
  --segment <段>    E6i 同款预热网格上计算全部 J 原值：真实字段恒等、与 E6i 源成员的别名 / 近别名对照、覆盖与状态码；
                    J 原值写 cache/<段>/<mid>.npy + sidecar（段网格 T × Nc，按 Base.to_seg；sha 校验）
  --merge           汇总 → stage0/features/ 与 feature_contracts_J.csv；回执
不算任何收益。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob
import json
import time
import resource

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_features as FJ

TASK = 'stage0_item4_features'
OUT = os.path.join(J.RES, 'stage0', 'features')
CACHE = os.path.join(J.RES, 'cache')
EPS = FJ.EPS


# ================================================================ 合成网格
class FakeBase(object):
    """与 e6i_features.Base 同名字段的玩具网格：价格由 LC→O→C 生成（H/L 包住 O/C），含停牌、零换手、零收益、触发。"""

    def __init__(self, T=260, N=40, key='base', zero_ret_frac=0.05):
        g = J.rng_for('E6j', 'stage0', 'feature_synth', key)
        LC = 10.0 * np.exp(np.cumsum(g.normal(0, 0.02, (T, N)), axis=0))
        on = g.normal(0, 0.01, (T, N)); idr = g.normal(0, 0.02, (T, N))
        zr = g.random((T, N)) < zero_ret_frac                    # 零收益日：O = C = LC
        on[zr] = 0.0; idr[zr] = 0.0
        O = LC * np.exp(on); C = O * np.exp(idr)
        H = np.maximum(O, C) * np.exp(np.abs(g.normal(0, 0.005, (T, N))))
        L = np.minimum(O, C) * np.exp(-np.abs(g.normal(0, 0.005, (T, N))))
        susp = g.random((T, N)) < 0.03
        self.open = ~susp
        self.valid = self.open & (O > 0) & (C > 0) & (LC > 0) & (H > 0) & (L > 0)
        x = np.exp(g.normal(-4.5, 0.6, (T, N)))
        x[g.random((T, N)) < 0.01] = 0.0                         # 零换手（开市）
        self.x = np.where(self.open, x, np.nan)
        self.amt = np.where(self.open, x * 1e9 * np.exp(g.normal(0, 0.3, (T, N))), np.nan)
        v = self.valid
        with np.errstate(all='ignore'):
            self.r = np.where(v, np.log(C / LC), np.nan)
            self.o = np.where(v, np.log(O / LC), np.nan)
            self.c = np.where(v, np.log(C / O), np.nan)
            self.h = np.where(v, np.log(H / O), np.nan)
            self.l = np.where(v, np.log(L / O), np.nan)
        self.d = np.abs(self.r)
        self.trig = g.random((T, N)) < 0.03
        self.p0 = self._p0_from_trig(self.trig, 5)
        self._tau = None

    @staticmethod
    def _p0_from_trig(trig, w):
        p = np.zeros_like(trig)
        for k in range(1, w + 1):
            p[k:] |= trig[:-k]
        return p

    def tau(self):
        if self._tau is None:
            T, N = self.trig.shape
            idx = np.where(self.trig, np.arange(T)[:, None], -1)
            self._tau = np.maximum.accumulate(idx, axis=0)
        return self._tau

    def perturb_after(self, t0, key):
        """t0 之后所有输入随机改写（后缀扰动）；返回新对象。"""
        import copy
        b = copy.deepcopy(self)
        g = J.rng_for('E6j', 'stage0', 'feature_synth', 'perturb', key)
        T, N = b.x.shape
        sl = slice(t0 + 1, T)
        for k in ('x', 'amt', 'r', 'o', 'c', 'h', 'l'):
            A = getattr(b, k).copy()
            A[sl] = A[sl] * (1.0 + g.normal(0, 0.5, A[sl].shape)) + g.normal(0, 0.01, A[sl].shape)
            if k in ('x', 'amt'):
                A[sl] = np.abs(A[sl])
            setattr(b, k, A)
        b.d = np.abs(b.r)
        b.trig = b.trig.copy(); b.trig[sl] = g.random(b.trig[sl].shape) < 0.2
        b.p0 = b.p0.copy(); b.p0[sl] = g.random(b.p0[sl].shape) < 0.3
        b._tau = None
        return b


def _eq(a, b):
    return bool(np.array_equal(np.asarray(a, float), np.asarray(b, float), equal_nan=True))


def run_synthetic():
    rows = []

    def chk(tid, what, ok, detail=''):
        rows.append(dict(test=tid, what=what, status='PASS' if ok else 'FAIL', detail=detail))

    B = FakeBase()
    mem, diag = FJ.all_members(B, B.p0)
    keys = sorted(k for k in mem if not k.startswith('__'))
    chk('F00', '成员数（B1 7 + B2 32 + B3A 16 + B3B 6 + B3C 2 + B4 12 + B5 32 + B6 3 = 110 个 J 原值）', len(keys) == 110, str(len(keys)))
    # F01 前缀不变（后缀扰动）
    t0 = 150
    B2_ = B.perturb_after(t0, 'F01')
    mem2, _ = FJ.all_members(B2_, B2_.p0)
    bad = [k for k in keys if not _eq(mem[k][:t0 + 1], mem2[k][:t0 + 1])]
    chk('F01', '后缀扰动（t0 之后全部输入 / 触发 / pool0 改写）→ 所有 J 原值在 ≤ t0 逐位不变', not bad, ','.join(bad[:5]))
    changed = [k for k in keys if not _eq(mem[k][t0 + 1:], mem2[k][t0 + 1:])]
    chk('F01b', '同一扰动确实改变了 t0 之后的值（扰动有效，反"空检验"）', len(changed) >= 100, '%d/%d' % (len(changed), len(keys)))
    # F02 日夜有符号恒等
    m = np.isfinite(B.r) & np.isfinite(B.o) & np.isfinite(B.c)
    err = float(np.max(np.abs(B.r[m] - (B.o[m] + B.c[m]))))
    chk('F02', 'r_cc = r_on + r_id（有符号；浮点）', err <= 1e-12, '%.2e' % err)
    # F03 涨跌零三分区与频率闭合
    for yn in ('CC', 'ID'):
        d = diag['b4'][yn]
        ok = _eq(d['n_up'] + d['n_dn'] + d['n_zero'], d['n_all'])
        chk('F03', '%s：n_up + n_down + n_zero = n_all（逐格）' % yn, ok)
    # 频率加权贡献闭合：Σ_s p_s·mean_s[(|r|+ε)/x] = mean[(|r|+ε)/x]（x > 0 的配对，逐窗暴力）
    g = J.rng_for('E6j', 'stage0', 'feature_synth', 'F03b')
    worst = 0.0
    for _ in range(200):
        t = int(g.integers(19, B.x.shape[0])); i = int(g.integers(0, B.x.shape[1]))
        xw, rw = B.x[t - 19:t + 1, i], B.r[t - 19:t + 1, i]
        v = np.isfinite(xw) & np.isfinite(rw) & (xw > 0)
        if v.sum() < 3:
            continue
        resp = (np.abs(rw[v]) + EPS) / xw[v]
        tot = resp.mean()
        parts = 0.0
        for side in (rw[v] > 0, rw[v] < 0, rw[v] == 0):
            if side.any():
                parts += side.mean() * resp[side].mean()
        worst = max(worst, abs(parts - tot) / max(abs(tot), 1e-300))
    chk('F03b', '频率加权三组贡献之和 = 全体响应均值（相对误差）', worst <= 1e-12, '%.2e' % worst)
    # F04 R_ev 恒等过程 ≡ 1：d_ε = k·x
    Bc = FakeBase(key='const')
    k = 0.37
    Bc.x = np.where(np.isfinite(Bc.x) & (Bc.x > 0), Bc.x, 0.02)
    Bc.r = np.where(np.isfinite(Bc.r), np.sign(Bc.r + 1e-12) * (k * Bc.x - EPS), np.nan)
    Bc.d = np.abs(Bc.r)
    Bc.c = Bc.r.copy()
    mc, _ = FJ.all_members(Bc, Bc.p0)
    for nm in ('J_B5_REV_CC_W20_LT', 'J_B5_REV5_CC_W20_LT', 'J_B5_REV_CC_W60_SE', 'J_B5_REV5_ID_W20_SE'):
        v = mc[nm][np.isfinite(mc[nm])]
        err = float(np.max(np.abs(v - 1.0))) if len(v) else float('nan')
        chk('F04', '%s：常数比例过程 ≡ 1（有效格 %d）' % (nm, len(v)), len(v) > 100 and err <= 1e-9, '%.2e' % err)
    # F05 R_ev(m=0) ≡ R_ev
    a = g.random((50, 7)) + 0.1; b_ = g.random((50, 7)) + 0.1; c_ = g.random((50, 7)) + 0.1; d_ = g.random((50, 7)) + 0.1
    chk('F05', 'R_ev(m=0) 逐位 = 原始 R_ev 公式', _eq(FJ.rev_shrunk(a, b_, c_, d_, 0.0), FJ.sdiv(FJ.sdiv(a, b_), FJ.sdiv(c_, d_))))
    # F06 OLS 退化状态
    T = 40
    z = np.tile(np.linspace(1, 2, T)[:, None], (1, 3)); y = np.tile((0.5 + 0.1 * np.sin(np.arange(T)))[:, None], (1, 3))
    z[:, 0] = 0.3                                   # 列 0：z 无变异
    y[:, 1] = 0.02                                  # 列 1：y 常数
    beta, rho, scale, _, _, _, code = FJ.ols_slope(z, y, 20)
    chk('F06', 'z 无变异 → β NA、码 2', bool(np.isnan(beta[-1, 0]) and code[-1, 0] == 2))
    chk('F06', 'y 常数 → β = 0 有效、ρ NA、码 3', bool(beta[-1, 1] == 0.0 and np.isnan(rho[-1, 1]) and code[-1, 1] == 3))
    chk('F06', '正常列 → β 有效、码 0', bool(np.isfinite(beta[-1, 2]) and code[-1, 2] == 0))
    chk('F06', '窗内不足 10 对 → 码 1', bool(code[8, 2] == 1 and np.isnan(beta[8, 2])))
    # F07 Q_λ=1 ≡ MR；β = ρ·scale；COV/P 在 P ≤ 0 → NA
    for yn, w, mr in (('CC', 3, 'J_B2_MR3_TR_CC'), ('ID', 3, 'J_B2_MR3_TR_ID')):
        q1 = mem['J_B3A_Q1_%s_W%d' % (yn, w)]; mrv = mem[mr]
        f = np.isfinite(q1) & np.isfinite(mrv)
        err = float(np.max(np.abs(q1[f] - mrv[f]) / np.maximum(np.abs(mrv[f]), 1e-300)))
        chk('F07', 'Q_1 = MR（%s W%d，相对误差）' % (yn, w), err <= 1e-10 and _eq(np.isfinite(q1), np.isfinite(mrv)), '%.2e' % err)
    for yn in ('CC', 'ID'):
        bb, rr, ss, *_ = FJ.ols_slope(B.x, FJ.ys(B)[yn], 20)
        f = np.isfinite(rr) & np.isfinite(ss) & np.isfinite(bb)
        err = float(np.max(np.abs(bb[f] - rr[f] * ss[f]) / np.maximum(np.abs(bb[f]), 1e-12)))
        chk('F07', 'β = ρ · sd(y)/sd(x)（%s）' % yn, err <= 1e-9, '%.2e' % err)
    Bz = FakeBase(key='zero_x')
    Bz.x = np.where(np.isfinite(Bz.x), 0.0, np.nan)
    mz, _ = FJ.all_members(Bz, Bz.p0)
    chk('F07', 'x 全 0 → P = 0 → COV/P 全 NA', bool(np.isnan(mz['J_B3A_COVP_CC_W20']).all()))
    # F08 留一可靠性 vs 暴力 np.polyfit
    r, bet, code = FJ.loo_reliability(B.x, B.d, 20, 10)
    worst_r = worst_b = 0.0; n_chk = 0
    for _ in range(300):
        t = int(g.integers(19, B.x.shape[0])); i = int(g.integers(0, B.x.shape[1]))
        xw, yw = B.x[t - 19:t + 1, i], B.d[t - 19:t + 1, i]
        v = np.isfinite(xw) & np.isfinite(yw)
        n = int(v.sum())
        if n < 11 or np.var(xw[v]) <= 0:
            continue
        b_full = np.polyfit(xw[v], yw[v], 1)[0]
        loo = np.array([np.polyfit(np.delete(xw[v], j), np.delete(yw[v], j), 1)[0] for j in range(n)])
        med = np.median(np.abs(loo - b_full)); medb = np.median(np.abs(loo))
        seps = 32 * np.finfo(float).eps * max(abs(b_full), medb)
        u = med / (abs(b_full) + med + seps)
        rr_ = min(max((n / 20.0) * (1 - u), 0.0), 1.0)
        worst_r = max(worst_r, abs(rr_ - r[t, i])); worst_b = max(worst_b, abs(b_full - bet[t, i]) / max(abs(b_full), 1e-12))
        n_chk += 1
    chk('F08', '留一可靠性 r 与 β 对暴力 polyfit（%d 窗）' % n_chk, n_chk > 100 and worst_r <= 1e-8 and worst_b <= 1e-8,
        'max|Δr|=%.2e max relΔβ=%.2e' % (worst_r, worst_b))
    # F09 B4 侧别对暴力
    worst = 0.0; n_chk = 0
    for _ in range(300):
        t = int(g.integers(19, B.x.shape[0])); i = int(g.integers(0, B.x.shape[1]))
        xw, rw = B.x[t - 19:t + 1, i], B.r[t - 19:t + 1, i]
        v = np.isfinite(xw) & np.isfinite(rw)
        if v.sum() < 10:
            continue
        for side, sm, key in (('UP', rw > 0, 'UP'), ('DN', rw < 0, 'DN')):
            s = v & sm
            if s.sum() < 3:
                continue
            ros = xw[s].sum() / (np.abs(rw[s]).sum() + s.sum() * EPS)
            mr = np.mean(xw[s] / (np.abs(rw[s]) + EPS))
            worst = max(worst, abs(ros - mem['J_B4_ROS_%s_CC' % key][t, i]) / abs(ros), abs(mr - mem['J_B4_MR_%s_CC' % key][t, i]) / abs(mr))
            n_chk += 1
    chk('F09', 'B4 侧别 ROS / MR 对暴力（%d 窗×侧）' % n_chk, n_chk > 100 and worst <= 1e-10, '%.2e' % worst)
    # F10 spell_entry 时钟
    p = np.array([[0], [1], [1], [0], [1], [1], [1], [0], [0], [1]], bool)
    se = FJ.clock_spell_entry(p)[:, 0].tolist()
    chk('F10', 'spell_entry 行号 = 最近连续段首日（含延长；段外保持上一段）', se == [-1, 1, 1, 1, 4, 4, 4, 4, 4, 9], str(se))
    # F11 事件钟只用 ≤ t：在 t1 加一个新触发，t1 之前 B5 全部不变
    t1 = 200
    B3_ = FakeBase()
    B3_.trig = B3_.trig.copy(); B3_.trig[t1, :] = True; B3_._tau = None
    m3, _ = FJ.all_members(B3_, B3_.p0)
    bad = [k for k in keys if k.startswith('J_B5') and not _eq(mem[k][:t1], m3[k][:t1])]
    chk('F11', 't1 新增触发 → t1 之前事件成员逐位不变', not bad, ','.join(bad[:5]))
    # F12 基线冻结在 [τ−W, τ−1]：同一事件内（τ 不变），改 τ 当日及之后的 x 不改变 rarpre 的分母（事件前均值）
    B4_ = FakeBase(key='F12')
    tau = B4_.tau()
    rows_ok = True; n_cells = 0
    x2 = B4_.x.copy()
    for i in range(B4_.x.shape[1]):
        ev = np.where(B4_.trig[:, i])[0]
        ev = ev[(ev >= 70) & (ev < B4_.x.shape[0] - 5)]
        if not len(ev):
            continue
        s = int(ev[0]); allev = np.where(B4_.trig[:, i])[0]; nxt = allev[allev > s]   # 下一个触发取全部触发（含末 5 行）
        e = int(nxt[0]) if len(nxt) else B4_.x.shape[0]
        x2[s:e, i] = x2[s:e, i] * 3.0
    B5_ = FakeBase(key='F12'); B5_.x = x2
    ma, _ = FJ.all_members(B4_, B4_.p0); mb, _ = FJ.all_members(B5_, B5_.p0)
    # rarpre = x_t / mean_pre / (d+ε)：x 放大 3 倍、分母不变 → 事件内比值恰为 3 倍
    ra, rb = ma['J_B5_RARPRE_CC_W20_LT'], mb['J_B5_RARPRE_CC_W20_LT']
    for i in range(B4_.x.shape[1]):
        ev = np.where(B4_.trig[:, i])[0]
        ev = ev[(ev >= 70) & (ev < B4_.x.shape[0] - 5)]
        if not len(ev):
            continue
        s = int(ev[0]); allev = np.where(B4_.trig[:, i])[0]; nxt = allev[allev > s]   # 下一个触发取全部触发（含末 5 行）
        e = int(nxt[0]) if len(nxt) else B4_.x.shape[0]
        f = np.isfinite(ra[s:e, i]) & np.isfinite(rb[s:e, i]) & (ra[s:e, i] != 0)
        n_cells += int(f.sum())
        rows_ok &= bool(np.allclose(rb[s:e, i][f], 3.0 * ra[s:e, i][f], rtol=1e-12, atol=0))
    chk('F12', '基线冻结在 [τ−W, τ−1]：事件内放大 x 不改 rarpre 分母（%d 格）' % n_cells, rows_ok and n_cells > 20)
    res = pd.DataFrame(rows)
    return res


# ================================================================ 真实字段
E6I_ALIAS = [  # (E6i 源成员, J 成员, 预期关系)
    ('K0_LEGACY', 'J_B2_POINT_TR_CC', 'K0 锚：同式；有效掩码不同处可能差'),
    ('K_MA3_E6F', 'J_B2_MR3_TR_CC', '源 mp(3)=2 与 J 至少 2 同；有效掩码不同'),
    ('K_MA5_E6F', 'J_B2_MR5_TR_CC', '源 mp(5)=3 vs J 至少 4'),
    ('K_ROS20_E6F', 'J_B2_ROS20_TR_CC', '源 mp(20)=10 vs J 10'),
    ('K_slope20', 'J_B2_SLOPE20_TR_CC', '源 minobs 14 vs J 10'),
    ('K_rar20', 'J_B1_S20lag', '源 minobs 14 vs J 10（代数同式）'),
    ('K_rarpre', 'J_B5_RARPRE_CC_W20_LT', '源 minobs 14 vs J 10；同 last_trigger 时钟'),
    ('T_cv20', 'J_B6_CV20', '源 minobs 14 vs J 10'),
    ('K_amt20', 'J_B2_SLOPE20_AMT_CC', '不同估计量（均比 vs 斜率），只作量纲参照'),
]


def run_segment(pname):
    import e6i_core as I
    import e6i_features as FE
    import e6j_slot as SL
    t0 = time.time()
    log = os.path.join(J.RES, 'logs', '%s_%s.log' % (TASK, pname))
    S = I.seg_i(pname, warm=True)
    J.assert_index_ok(S.wdata_i['close'].index, 'wdata_i %s' % pname)
    B = FE.Base(S)
    p0w = S.pool0.reindex(index=B.dates_w, columns=B.own_cols).fillna(0).values == 1
    mem, diag = FJ.all_members(B, p0w)
    J.log('%s members computed %.0fs' % (pname, time.time() - t0), log)
    rows, cov = [], []

    def chk(tid, what, ok, detail='', gate=True):
        rows.append(dict(segment=pname, test=tid, what=what, status=('PASS' if ok else ('FAIL' if gate else 'DIFFERS')) if ok is not None else 'INFO',
                         detail=detail))

    m = np.isfinite(B.r) & np.isfinite(B.o) & np.isfinite(B.c)
    err = float(np.max(np.abs(B.r[m] - (B.o[m] + B.c[m]))))
    chk('R01', '真实字段 r_cc = r_on + r_id（有符号）', err <= 1e-12, '%.2e; cells=%d' % (err, int(m.sum())))
    for yn in ('CC', 'ID'):
        d = diag['b4'][yn]
        chk('R02', '真实字段 %s 涨跌零计数闭合' % yn, _eq(d['n_up'] + d['n_dn'] + d['n_zero'], d['n_all']))
        q1, mr = mem['J_B3A_Q1_%s_W3' % yn], mem['J_B2_MR3_TR_%s' % yn]
        f = np.isfinite(q1) & np.isfinite(mr)
        e = float(np.max(np.abs(q1[f] - mr[f]) / np.maximum(np.abs(mr[f]), 1e-300)))
        chk('R03', '真实字段 Q_1 = MR3（%s）' % yn, e <= 1e-10, '%.2e' % e)
        bb, rr, ss, *_ = FJ.ols_slope(B.x, FJ.ys(B)[yn], 20)
        f = np.isfinite(rr) & np.isfinite(ss) & np.isfinite(bb) & (np.abs(bb) > 0)
        e = float(np.max(np.abs(bb[f] - rr[f] * ss[f]) / np.abs(bb[f])))
        chk('R04', '真实字段 β = ρ·scale（%s）' % yn, e <= 1e-8, '%.2e' % e)
    # 段网格 + pool0 覆盖；写缓存
    p0c = S.p0c
    os.makedirs(os.path.join(CACHE, pname), exist_ok=True)
    wstart = str(B.dates_w[0])[:10]
    for k in sorted(mem):
        if k.startswith('__'):
            continue
        A = B.to_seg(mem[k])
        vals = A[p0c]
        fin = np.isfinite(vals)
        path = os.path.join(CACHE, pname, '%s.npy' % k)
        tmp = path + '.tmp.%d.npy' % os.getpid()
        np.save(tmp, A, allow_pickle=False); os.replace(tmp, path)
        meta = dict(member_id=k, segment=pname, shape=list(A.shape), dtype='float64', sha256=J.sha_file(path),
                    formula_module='e6j_features', warm_tag=S.warm_tag_i, warm_start=str(S.warm_start_i),
                    max_feature_date=str(B.dates_w[-1])[:10], finite_frac_pool0=float(fin.mean()),
                    written_at=time.strftime('%Y-%m-%d %H:%M:%S'))
        J.atomic_write_json(path.replace('.npy', '.json'), meta)
        q = np.nanpercentile(vals[fin], [1, 50, 99]) if fin.any() else [np.nan] * 3
        cov.append(dict(segment=pname, member_id=k, finite_frac_pool0=float(fin.mean()), n_pool0=int(len(vals)),
                        p01=q[0], p50=q[1], p99=q[2], sha256=meta['sha256'], warm_tag=S.warm_tag_i, warm_start=str(S.warm_start_i)))
    # E6i 源成员别名 / 近别名（pool0 格）
    for src, jm, note in E6I_ALIAS:
        try:
            arr, meta = SL.e6i_member_raw(pname, src)
        except Exception as e:   # noqa: BLE001
            chk('R05', '%s vs %s' % (src, jm), None, 'UNAVAILABLE %r' % e); continue
        a = arr[p0c]; b = B.to_seg(mem[jm])[p0c]
        fa, fb = np.isfinite(a), np.isfinite(b)
        both = fa & fb
        eq = both & (a == b)
        rel = np.abs(a[both] - b[both]) / np.maximum(np.abs(a[both]), 1e-300) if both.any() else np.zeros(1)
        chk('R05', '%s vs %s（%s）' % (src, jm, note), None,
            'both=%.4f exact_eq=%.4f maxrel=%.2e only_src=%d only_J=%d' % (both.mean(), eq.sum() / max(both.sum(), 1), float(rel.max()),
                                                                        int((fa & ~fb).sum()), int((fb & ~fa).sum())))
    # 状态码（OLS / 留一）
    for yn in ('CC', 'ID'):
        code = B.to_seg(mem['__code_%s' % yn].astype(float))[p0c]
        chk('R06', 'J_B3C_REL_%s 状态码（pool0 格）' % yn, None,
            '0 有效 %.4f / 1 数据不足 %.4f / 2 留一不可估 %.4f' % tuple((code == c).mean() for c in (0, 1, 2)))
    res = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    J.atomic_write_csv(os.path.join(OUT, 'real_%s.csv' % pname), res)
    J.atomic_write_csv(os.path.join(OUT, 'coverage_%s.csv' % pname), pd.DataFrame(cov))
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 / 1024.0
    J.log('%s done %.0fs maxrss %.1f GB; FAIL=%d' % (pname, time.time() - t0, rss, int((res.status == 'FAIL').sum())), log)
    return 0


def merge():
    parts = sorted(glob.glob(os.path.join(OUT, 'real_*.csv')))
    syn = pd.read_csv(os.path.join(OUT, 'synthetic.csv'))
    real = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)
    cov = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(os.path.join(OUT, 'coverage_*.csv')))], ignore_index=True)
    fc = cov.pivot_table(index='member_id', columns='segment', values='finite_frac_pool0').reset_index()
    fc_path = os.path.join(J.RES, 'feature_contracts_J.csv'); J.atomic_write_csv(fc_path, fc)
    n_fail = int((syn.status == 'FAIL').sum() + (real.status == 'FAIL').sum())
    segs = sorted(real.segment.unique())
    man = dict(task=TASK, synthetic=syn.status.value_counts().to_dict(), real=real.status.value_counts().to_dict(),
               segments=segs, n_members=int(cov.member_id.nunique()),
               src_sha256={f: J.sha_file(os.path.join(J.CODE, f)) for f in ('e6j_features.py', 'e6j_stage0_features.py', 'e6i_features.py')})
    man_path = os.path.join(OUT, 'features_manifest.json'); J.atomic_write_json(man_path, man)
    ok = n_fail == 0 and len(segs) == 4
    J.write_receipt(TASK, [os.path.join(OUT, 'synthetic.csv'), fc_path, man_path] + parts, 'SUCCEEDED' if ok else 'FAILED',
                    n_fail=n_fail, segments=segs, blocker=not ok)
    print('merge: synthetic %s; real %s; members %d; segments %s' % (man['synthetic'], man['real'], man['n_members'], segs), flush=True)
    return 0 if ok else 2


if __name__ == '__main__':
    if '--synthetic' in sys.argv:
        res = run_synthetic()
        os.makedirs(OUT, exist_ok=True)
        J.atomic_write_csv(os.path.join(OUT, 'synthetic.csv'), res)
        print(res.to_string(), flush=True)
        sys.exit(0 if (res.status == 'PASS').all() else 2)
    if '--merge' in sys.argv:
        sys.exit(merge())
    sys.exit(run_segment(sys.argv[sys.argv.index('--segment') + 1]))
