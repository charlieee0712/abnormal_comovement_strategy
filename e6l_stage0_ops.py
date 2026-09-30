# -*- coding: utf-8 -*-
"""E6l Stage 0 第 3 类：新算子恒等锚（brief §2 第 3 类；附录 A3-1 … A3-12；plan §13.1）。推导两段真实数据；只比较掩码 / 评分 / 名单（不读收益）。
每条写 which_switch_is_off / comparator_id。
  A3-1  Q_MA1 ≡ Q0（raw → 源中性化 → 秩逐位）；Q_DEW(λ = 1) ≡ Q0；Q_RANK1 与 Q0 同支持源秩（ties / 覆盖差 INFO）
  A3-2  每种规则 b = 0 ≡ 同测量 NATIVE（HG / LAG1 / DECAY / INV / 四调度（b 全 0））；零 bonus 直返 source_U
  A3-3  每种规则 α = 0 ≡ 自己的 ONLY（K0 同规则）；≠ 原母体（报差异格数）
  A3-4  DECAY(L = ∞) ≡ HG10（逐位）；L = 10⁶ 与 HG10 的差异格数（INFO：有限 L 的折让 < b 会改变近似并列，spec decay_bonus 以 L = ∞ 为机械端点）
  A3-5  LAG1 与 HG10：U_{t−1} ≠ G_{t−1} 的日数与份额 > 0
  A3-6  INV 标记 = 形成日 [T−H, T−1] 本账户最终名单批次（由最终名单现算逐位）；单格目标持仓 T+2 … T+H+1 行（T+1 进、T+1+H 出）；H 不同 → 名单不同
  A3-7  调度 b_high = b_low ≡ 固定 HG；UNKNOWN 日 b = 10；p_t 只用 T−250 … T−1 位置（改当日状态不改 p_t；与暴力式逐位）
  A3-8  KERNEL_DOSE：C 内同均值 / 同 RMS（1e−12）；状态计数
  A3-9  checkpoint 拆分一致性（HG10 / LAG1 / DECAY5 / INV10 / VOL_HI15 / Q_DEW5 各一个真实账户）：前 300 日一次跑 = 150 + 150 续跑逐位；
        错股票身份 / 不连续日期 → 拒绝
  A3-10 R-MARK：每路径每日分组标记数守恒；全 0 / 全 1 组计数；b = 0 ≡ NATIVE
  A3-11 RANK 延伸源锚：成员 kQ = 源 J_B1_qCC 中性化秩逐位；回退日集合（SKIP / RAW）与源缓存一致；池外延伸只在 ≥ 2 个不同结点时定义
  A3-12 门合同：最终名单 ⊂ Struct.legal()；每日选取恰 dom.K[d]；名额不可行 0 次；Mmean b 单位 = 1/300；Mmean K 腿系数（门域内三腿齐的份额）"""
import e6l_boot  # noqa: F401
import os
import sys
import time
import argparse

import numpy as np
import pandas as pd

import e6l_core as L

A = 0.25


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--rerun', action='store_true')
    a = ap.parse_args()
    L.deriv_only(a.segment, 'Stage 0 第 3 类')
    import e6l_env as V
    import e6l_ops as O
    import e6l_state as S
    import e6k_ops as KO
    import e6k_env as E
    import e6j_slot as SL
    import e6l_run_det as RD
    out = L.P('stage0', 'c3_ops' + ('_rerun' if a.rerun else ''))
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    seg = V.SegL(a.segment)
    rows = []
    tim = [dict(step='env_load', seconds=round(time.time() - t0, 1))]

    def chk(cid, form, meas, what, switch_off, comparator, got, ok, note=''):
        rows.append(dict(check_id=cid, segment=a.segment, form=form, meas=meas, what=what, which_switch_is_off=switch_off,
                         comparator_id=comparator, got=L.txt(got)[:300], status='INFO' if ok is None else ('PASS' if ok else 'FAIL'), note=note))

    def same(x, y):
        x, y = np.asarray(x), np.asarray(y)
        return bool(np.array_equal(np.isnan(x), np.isnan(y)) and np.array_equal(x[np.isfinite(x)], y[np.isfinite(y)]))
    ci = seg.ci
    kQ = seg.meas_kf('Q0')
    # ---------------- A3-1
    B = seg.base()
    for key, how in (('MA1', 'mean'), ('DEW_lambda1', 'ew')):
        if how == 'mean':
            m, _ = V.win_stat(B.d, 1, 'mean')
            raw_w = V.sdiv(1.0, m + V.EPS)
        else:
            m, _ = V.ew_norm(B.d, 1.0)
            raw_w = V.sdiv(1.0, m + V.EPS)
        raw_w = np.where(np.isfinite(B.d), raw_w, np.nan)
        raw = B.to_seg(raw_w)
        rq = seg.raw('Q')
        chk('A3-1', '-', 'Q_%s' % key, 'raw = Q0 raw（J_B1_qCC）逐位（pool0 单元）', 'window=1' if how == 'mean' else 'lambda=1', 'Q0_raw',
            same(raw[ci.t, ci.c], rq[ci.t, ci.c]), same(raw[ci.t, ci.c], rq[ci.t, ci.c]))
        neu = SL.neu_of(seg.ctx, SL.full_frame(seg.ctx, raw))
        kk = seg.env._dense_cells(SL.pct_dir(neu, 'lo'))
        chk('A3-1', '-', 'Q_%s' % key, 'kf ≡ Q0 kQ 逐位', 'window=1' if how == 'mean' else 'lambda=1', 'Q0', same(kk, kQ), same(kk, kQ))
    ext, facts = seg.rank_ext()
    kqd = np.full((seg.T, seg.Nc), np.nan)
    kqd[ci.t, ci.c] = kQ
    avg1 = np.where(np.isfinite(kqd), ext, np.nan)[ci.t, ci.c]
    r1 = pd.DataFrame({'t': ci.t[np.isfinite(avg1)], 'v': avg1[np.isfinite(avg1)]}).groupby('t')['v'].rank(pct=True).to_numpy()
    k1 = np.full(seg.n, np.nan)
    k1[np.isfinite(avg1)] = r1
    chk('A3-1', '-', 'Q_RANK1', '同支持再 rank 与 Q0 的差格数（ties / 覆盖；桥接 INFO，不改 Q0 锚）', 'window=1', 'Q0',
        '%d / %d（支持差 %d）' % (int((np.abs(k1 - kQ) > 1e-12).sum()), int(np.isfinite(kQ).sum()), int((np.isfinite(k1) != np.isfinite(kQ)).sum())), None)
    tim.append(dict(step='A3-1', seconds=round(time.time() - t0, 1)))
    # ---------------- A3-11
    mem = np.isfinite(kQ)
    chk('A3-11', '-', 'Q_RANK*', '延伸成员 kQ = 源 J_B1_qCC 中性化秩逐位（pool0 成员 %d 格）' % int(mem.sum()), 'extension', 'source_kQ',
        same(ext[ci.t, ci.c][mem], kQ[mem]), same(ext[ci.t, ci.c][mem], kQ[mem]))
    src_days = set(np.flatnonzero(np.bincount(ci.t[mem], minlength=seg.T) > 0))
    ext_days = set(facts.u[facts['mode'] != 'SKIP'].tolist())
    chk('A3-11', '-', 'Q_RANK*', '源有秩日集合 = 延伸非 SKIP 日集合', 'fallback', 'source_cache', '%d / %d 日' % (len(src_days), len(ext_days)),
        src_days == ext_days)
    raw_days = int((facts['mode'] == 'RAW').sum())
    chk('A3-11', '-', 'Q_RANK*', '回退：RAW（有效 < 10）日数 / SKIP 日数', 'fallback', 'neutralize_by_mcap', '%d / %d' % (raw_days, int((facts['mode'] == 'SKIP').sum())), None)
    bad_knot = int(((facts.n_knots < 2) & (facts.n_off_ext > 0)).sum())
    chk('A3-11', '-', 'Q_RANK*', '池外延伸只在 ≥ 2 个不同结点时定义（违例日数）', 'knots', 'plan §4.3', bad_knot, bad_knot == 0)
    tim.append(dict(step='A3-11', seconds=round(time.time() - t0, 1)))
    # ---------------- 逐形态
    kD5 = seg.meas_kf('Q_D5')
    for form in E.P6:
        st = seg.struct(form)
        k0 = st.q0
        ctx = RD.DetCtx(seg, st, k0, kQ, 'Q0')
        parent = ctx.parent
        nat = ctx.final('NATIVE', A)
        U = ctx.U(A)
        sc = ctx.sc(A)
        # A3-12
        legal = st.legal()
        fin_hg = ctx.final('HG10', A, tag='hg')
        chk('A3-12', form, 'Q0', '最终名单 ⊂ Struct.legal()（NATIVE / HG10 / 母体）', 'legal', 'E_t', '%d / %d / %d' % (
            (nat & ~legal).sum(), (fin_hg & ~legal).sum(), (parent & ~legal).sum()), not ((nat | fin_hg | parent) & ~legal).any())
        G, _, _ = O.mem_gate(st, sc[None, :], U[None, :], O.parse_op('HG10'), b_day=np.full(seg.T, 10.0))
        cnt = np.bincount(ci.t[st.ids][G[0]], minlength=seg.T)
        chk('A3-12', form, 'Q0', 'HG10 每日门选取数 = dom.K[d]', 'quota', 'dom.K', int((cnt != st.dom.K).sum()), (cnt == st.dom.K).all())
        dom_n = np.diff(st.dom.off)
        chk('A3-12', form, '-', '名额不可行（K[d] > 门域人数）日数', 'quota', 'dom', int((st.dom.K > dom_n).sum()), (st.dom.K <= dom_n).all())
        chk('A3-12', form, '-', 'b 单位 bunit（Mmean = 1/300；其余 1/100）', 'bunit', 'Struct.bunit', st.bunit,
            abs(st.bunit - (1 / 300.0 if st.kind == 'mean' else 1 / 100.0)) < 1e-18)
        if st.kind == 'mean':
            legs = st.st.legs
            okl = np.ones(seg.n, bool)
            for lg in legs:
                okl &= np.isfinite(lg)
            share = float(okl[st.ids].mean())
            chk('A3-12', form, '-', 'Mmean 门域内三腿齐份额（= 1 ⇒ K 腿系数恒 1/3，b/3 精确；complete=%s）' % getattr(st.st, 'complete', '?'), 'K_loading',
                'combine', '%.6f' % share, None)
        # A3-2
        for op in ('HG10', 'LAG1_10', 'DECAY5_10', 'VOL_HI15'):
            rule = O.parse_op(op)
            Gz, _, _ = O.mem_gate(st, sc[None, :], U[None, :], rule, b_day=np.zeros(seg.T))
            chk('A3-2', form, 'Q0', '%s b = 0 ≡ 同测量 NATIVE 门（source_U 含源平局）' % op, 'b', 'NATIVE_gate', int((Gz[0] != U).sum()), (Gz[0] == U).all())
        Gi, Fi, _, _ = O.inv_path(st, sc[None, :], U[None, :], 0.0, 5)
        chk('A3-2', form, 'Q0', 'INV b = 0 ≡ 同测量 NATIVE（最终名单）', 'b', 'NATIVE', int((Fi[0] != nat).sum()), (Fi[0] == nat).all())
        # A3-3
        ctx0 = RD.DetCtx(seg, st, k0, None, 'K0')
        for op in ('HG10', 'LAG1_10', 'DECAY5_10', 'INV10', 'VOL_HI15'):
            H = 5 if op == 'INV10' else None
            f_a0 = ctx.final(op, 0.0, H, tag='a0')
            f_only = ctx0.final(op, 0.0, H, tag='only')
            chk('A3-3', form, 'Q0', '%s α = 0 ≡ 自己的 ONLY（K0 同规则）' % op, 'alpha', 'K0|%s' % op, int((f_a0 != f_only).sum()), (f_a0 == f_only).all())
            chk('A3-3', form, 'Q0', '%s α = 0 与原母体的差格数（> 0 ⇒ 规则确有作用）' % op, 'alpha', 'PARENT', int((f_only != parent).sum()), None)
        # A3-4
        Ginf, _, _ = O.mem_gate(st, sc[None, :], U[None, :], dict(kind='DECAY', L=np.inf, b=10.0), b_day=np.full(seg.T, 10.0))
        chk('A3-4', form, 'Q0', 'DECAY(L = ∞) ≡ HG10（门逐位）', 'L', 'HG10', int((Ginf[0] != G[0]).sum()), (Ginf[0] == G[0]).all())
        G6, _, _ = O.mem_gate(st, sc[None, :], U[None, :], dict(kind='DECAY', L=1e6, b=10.0), b_day=np.full(seg.T, 10.0))
        chk('A3-4', form, 'Q0', 'DECAY(L = 10⁶) 与 HG10 门差异格数（有限 L 折让 < b 改变近似并列；INFO）', 'L', 'HG10', int((G6[0] != G[0]).sum()), None)
        # A3-5
        GL, _, _ = O.mem_gate(st, sc[None, :], U[None, :], O.parse_op('LAG1_10'), b_day=np.full(seg.T, 10.0))
        cols = ci.c[st.ids]
        ndiff = 0
        ndays = 0
        for d in range(1, seg.T):
            a0, b0 = st.dom.off[d - 1], st.dom.off[d]
            if b0 > a0 and st.dom.K[d - 1] > 0:
                ndays += 1
                ndiff += int(set(cols[a0:b0][G[0, a0:b0]]) != set(cols[a0:b0][U[a0:b0]]))
        chk('A3-5', form, 'Q0', 'G_{t−1} ≠ U_{t−1} 的日数 / 形成日数（递归与非递归确被分开）', 'recursion', 'HG10', '%d / %d' % (ndiff, ndays), ndiff > 0)
        chk('A3-5', form, 'Q0', 'LAG1 与 HG10 门差异格数', 'recursion', 'HG10', int((GL[0] != G[0]).sum()), None)
        # A3-6
        for H in (5, 10):
            Gv, Fv, _, _ = O.inv_path(st, sc[None, :], U[None, :], 10.0, H)
            F = Fv[0]
            fd = np.zeros((seg.T, seg.Nc), bool)
            fd[ci.t[F], ci.c[F]] = True
            be = 10.0 * st.bunit
            bad = 0
            for d in range(seg.T):
                a0, b0 = st.dom.off[d], st.dom.off[d + 1]
                if b0 == a0 or st.dom.K[d] == 0:
                    continue
                cc = cols[a0:b0]
                mark = fd[max(0, d - H):d][:, cc].any(axis=0)
                s = sc[a0:b0] - be * mark
                ref = np.zeros(b0 - a0, bool)
                if (be * mark != 0).any():
                    ref[np.argsort(s, kind='stable')[:st.dom.K[d]]] = True
                else:
                    ref = U[a0:b0]
                bad += int((ref != Gv[0, a0:b0]).sum())
            chk('A3-6', form, 'Q0', 'INV H%d：门 = 由最终名单现算的库存标记（形成日 [T−H, T−1]，不含当日）逐位' % H, 'inventory', 'final_lists', bad, bad == 0)
            if H == 5:
                F5 = F
        F10 = F
        dd = np.flatnonzero(np.bincount(ci.t[F5 != F10], minlength=seg.T) > 0)
        chk('A3-6', form, 'Q0', 'INV H5 与 H10 最终名单不同的日数（H 进状态键）', 'H', 'INV_H10', len(dd), len(dd) > 0)
        # A3-7
        Gs, _, _ = O.mem_gate(st, sc[None, :], U[None, :], dict(kind='STATE', schedule='CONST10', b=np.nan), b_day=np.full(seg.T, 10.0))
        chk('A3-7', form, 'Q0', '调度 b_high = b_low = 10 ≡ 固定 HG10（门逐位）', 'schedule', 'HG10', int((Gs[0] != G[0]).sum()), (Gs[0] == G[0]).all())
        # A3-8
        kd, status = O.kernel_dose(seg, k0, kQ, kD5)
        C = np.isfinite(k0) & np.isfinite(kQ) & np.isfinite(kD5)
        errm = errr = 0.0
        for d in np.flatnonzero(status == 'MATCHED_MEAN_RMS'):
            a0, b0 = seg.off[d], seg.off[d + 1]
            ix = np.arange(a0, b0)[C[a0:b0]]
            ds = kD5[ix] - k0[ix]
            errm = max(errm, abs(np.mean(kd[ix]) - np.mean(ds)))
            errr = max(errr, abs(np.std(kd[ix]) - np.std(ds)))
        vals, cn = np.unique(status, return_counts=True)
        chk('A3-8', form, 'Q_D5', 'KERNEL_DOSE 同均值 / 同 RMS（MATCHED 日；1e−12）', 'dose', 'Q_D5', '%.2e / %.2e' % (errm, errr), errm <= 1e-12 and errr <= 1e-12)
        chk('A3-8', form, 'Q_D5', 'KERNEL_DOSE 日状态计数', 'dose', '-', dict(zip([str(v) for v in vals], [int(c) for c in cn])), None)
        # A3-9
        tick = O.ids_hash(seg.S.ccolnames)
        nd = 300
        cut = 150
        a300 = st.dom.off[nd]
        sub = dict(sc=sc[None, :], U=U[None, :])
        for op in ('HG10', 'LAG1_10', 'DECAY5_10', 'VOL_HI15'):
            rule = O.parse_op(op)
            bday = seg.state_b(rule['schedule']) if rule['kind'] == 'STATE' else np.full(seg.T, rule['b'])
            g1, s1, _ = O.mem_gate(st, sub['sc'], sub['U'], rule, b_day=bday, d0=0, d1=nd)
            ga, sa, _ = O.mem_gate(st, sub['sc'], sub['U'], rule, b_day=bday, d0=0, d1=cut)
            gb, sb, _ = O.mem_gate(st, sub['sc'], sub['U'], rule, b_day=bday, state=sa, d0=cut, d1=nd)
            ac = st.dom.off[cut]
            rec = np.concatenate([ga[:, :ac], gb[:, ac:a300]], axis=1)
            chk('A3-9', form, 'Q0', '%s 前 %d 日一次跑 ≡ %d + %d 续跑（门逐位）' % (op, nd, cut, nd - cut), 'checkpoint', op,
                int((rec != g1[:, :a300]).sum()), (rec == g1[:, :a300]).all())
            rej = 0
            try:
                O.mem_gate(st, sub['sc'], sub['U'], rule, b_day=bday, state=sa, d0=cut + 1, d1=nd)
            except ValueError:
                rej += 1
            bad_ids = dict(sa, ids='deadbeefdeadbeef')
            try:
                O.mem_gate(st, sub['sc'], sub['U'], rule, b_day=bday, state=bad_ids, d0=cut, d1=nd)
            except ValueError:
                rej += 1
            chk('A3-9', form, 'Q0', '%s 不连续日期 / 错股票身份恢复被拒（2 / 2）' % op, 'checkpoint', op, rej, rej == 2)
        g1, f1, s1, _ = O.inv_path(st, sub['sc'], sub['U'], 10.0, 10, d0=0, d1=nd)
        ga, fa, sa, _ = O.inv_path(st, sub['sc'], sub['U'], 10.0, 10, d0=0, d1=cut)
        gb, fb, sb, _ = O.inv_path(st, sub['sc'], sub['U'], 10.0, 10, state=sa, d0=cut, d1=nd)
        c300 = seg.off[nd]
        cc_ = seg.off[cut]
        recf = np.concatenate([fa[:, :cc_], fb[:, cc_:c300]], axis=1)
        chk('A3-9', form, 'Q0', 'INV10 H10 前 %d 日一次跑 ≡ 续跑（最终名单逐位）' % nd, 'checkpoint', 'INV10', int((recf != f1[:, :c300]).sum()),
            (recf == f1[:, :c300]).all())
        rej = 0
        try:
            O.inv_path(st, sub['sc'], sub['U'], 10.0, 10, state=sa, d0=cut + 2, d1=nd)
        except ValueError:
            rej += 1
        try:
            O.inv_path(st, sub['sc'], sub['U'], 10.0, 5, state=sa, d0=cut, d1=nd)
        except ValueError:
            rej += 1
        chk('A3-9', form, 'Q0', 'INV 不连续日期 / H 不符恢复被拒（2 / 2）', 'checkpoint', 'INV10', rej, rej == 2)
        # A3-10
        leaf_isk = __import__('e6k_random').tree_leaves(seg, np.isin(np.arange(seg.n), st.ids), k0, 'ISK')[0][st.ids]
        rng = np.random.default_rng(7)
        uu = rng.random((4, len(st.ids)))
        rmk = dict(groups=leaf_isk, u=lambda d, a0, b0: uu[:, a0:b0])
        P4 = np.repeat(sc[None, :], 4, axis=0)
        U4 = np.repeat(U[None, :], 4, axis=0)
        Gr, _, _ = O.mem_gate(st, P4, U4, dict(kind='RMARK', b=0.0), b_day=np.zeros(seg.T), rmark=rmk)
        chk('A3-10', form, 'Q0', 'R-MARK 折让 0 ≡ NATIVE 门', 'b', 'NATIVE_gate', int((Gr != U4).sum()), (Gr == U4).all())
        Gr, _, _ = O.mem_gate(st, P4, U4, dict(kind='RMARK', b=10.0), b_day=np.full(seg.T, 10.0), rmark=rmk)
        cons = 0
        g0 = g1_ = 0
        prevG = np.zeros((4, seg.Nc), bool)
        for d in range(seg.T):
            a0, b0 = st.dom.off[d], st.dom.off[d + 1]
            if b0 == a0 or st.dom.K[d] == 0:
                prevG[:] = False
                continue
            cc = cols[a0:b0]
            mk = prevG[:, cc]
            perm = O.permute_marks_day(mk, leaf_isk[a0:b0], uu[:, a0:b0])
            gids = np.unique(leaf_isk[a0:b0], return_inverse=True)[1].ravel()
            for p in range(4):
                cons += int((np.bincount(gids, weights=mk[p].astype(float)) != np.bincount(gids, weights=perm[p].astype(float))).any())
                cnt_g = np.bincount(gids)
                mk_g = np.bincount(gids, weights=mk[p].astype(float))
                g0 += int(((mk_g == 0) & (cnt_g > 0)).sum())
                g1_ += int(((mk_g == cnt_g) & (cnt_g > 0)).sum())
            prevG = np.zeros((4, seg.Nc), bool)
            for p in range(4):
                prevG[p, cc[Gr[p, a0:b0]]] = True
        chk('A3-10', form, 'Q0', 'R-MARK ISK 每路径每日分组标记数守恒（违例 路径·日）', 'partition', 'own_G', cons, cons == 0)
        chk('A3-10', form, 'Q0', 'R-MARK 退化组（全 0 / 全 1 标记）计数（路径·日·组）', 'partition', '-', '%d / %d' % (g0, g1_), None)
    # ---------------- A3-7 状态部分（与形态无关）
    vs = np.asarray(seg.st['vol_state'])
    bh = seg.state_b('VOL_HI15')
    chk('A3-7', '-', '-', 'UNKNOWN 日 b = 10（四调度）', 'state_unknown', 'b10', int((vs < 0).sum()),
        all(np.all(seg.state_b(s)[vs < 0] == 10.0) for s in S.SCHEDULES))
    code = np.array(np.random.default_rng(3).integers(-1, 3, 700), np.int8)
    p1 = S.high_freq(code)
    brute = np.array([np.mean(code[max(0, t - 250):t][code[max(0, t - 250):t] >= 0] == 2) if (code[max(0, t - 250):t] >= 0).any() else 0.5
                      for t in range(len(code))])
    chk('A3-7', '-', '-', 'p_t = T−250 … T−1 位置已定义值 high 比例（与暴力式逐位；当前 T 不进；无定义 .5）', 'p_t', 'brute', same(p1, brute), same(p1, brute))
    code2 = code.copy()
    code2[400] = 2 if code[400] != 2 else 0
    p2 = S.high_freq(code2)
    chk('A3-7', '-', '-', '改变 T 日状态不改 p_T（只影响 T+1 … T+250）', 'p_t', 'PIT', int((p2[:401] != p1[:401]).sum()), (p2[:401] == p1[:401]).all())
    tim.append(dict(step='forms', seconds=round(time.time() - t0, 1)))
    # ---------------- A3-9 Q_DEW5 checkpoint
    Bd = B.d[:300]
    full, _ = V.ew_norm(Bd, 1.0 / 3.0, ids_hash='x')
    p_a, _ = V.ew_norm(Bd[:150], 1.0 / 3.0, ids_hash='x')
    sa = dict(V.ew_norm.last_state)
    p_b, _ = V.ew_norm(Bd[150:], 1.0 / 3.0, state=sa, t0=150, ids_hash='x')
    rec = np.vstack([p_a, p_b])
    chk('A3-9', '-', 'Q_DEW5', 'EW 前 300 行一次跑 ≡ 150 + 150 续跑（A / B 状态逐位）', 'checkpoint', 'Q_DEW5', same(rec, full), same(rec, full))
    rej = 0
    for bad in (dict(state=sa, t0=151, ids_hash='x'), dict(state=sa, t0=150, ids_hash='y')):
        try:
            V.ew_norm(Bd[150:], 1.0 / 3.0, **bad)
        except ValueError:
            rej += 1
    chk('A3-9', '-', 'Q_DEW5', 'EW 不连续 / 错身份恢复被拒（2 / 2）', 'checkpoint', 'Q_DEW5', rej, rej == 2)
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'ops_identity_%s.csv' % a.segment)
    L.atomic_write_csv(p, df)
    pt = os.path.join(out, 'ops_timing_%s.csv' % a.segment)
    L.atomic_write_csv(pt, pd.DataFrame(tim))
    ok = not (df.status == 'FAIL').any()
    L.write_receipt('stage0_c3_ops_%s%s' % (a.segment, '_rerun' if a.rerun else ''), [p, pt], 'SUCCEEDED' if ok else 'FAILED',
                    counts=df.status.value_counts().to_dict(), blocker=not ok, wall_s=round(time.time() - t0, 1))
    print(df.status.value_counts().to_dict(), 'OK' if ok else 'FAIL', 'wall %.0fs' % (time.time() - t0), flush=True)
    print(df[df.status != 'PASS'].to_string(max_colwidth=70), flush=True)
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
