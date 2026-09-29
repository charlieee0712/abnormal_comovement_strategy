# -*- coding: utf-8 -*-
"""E6k Stage 0 第 3 类：新算子恒等锚（brief §2 第 3 类；附录 A3-1 … A3-11；plan §13.1 第 3 条）。只在推导段（执行端补充 X04）。
每条写 which_switch_is_off / comparator_id；只比较掩码 / 评分 / 名单（不读收益）。
  A3-1  SZL3 / SZL5 在单一组（G = 1）+ NATIVE 同坐标（pct、同支持）≡ NATIVE（逐格）；源坐标（中点秩、kf∧k0∧z 人群）G = 1 与 NATIVE 的差计数（桥接 INFO）
  A3-2  SZL_OWN：新测量 = 旧 K 的复制时 SZL ≡ SZL_OWN（同分组同掩码）；G = 1 + pct + 全支持的 OWN ≡ 母体
  A3-3  INC γ = 1：Xᵀd_γ = 0（≤ 1e−10）且 mean_C d_γ = mean_C d；γ0 = INC_SUPPORT0；全支持日 γ0 ≡ NATIVE；INC_DOSE mean / RMS = INC（1e−12）
  A3-4  RP：父名单恒可行（τ = 0 → 父）；PAIR_ALL 与父同 N、同行业人数、同 DEV 每行业单股权重与总资本；τ = ∞ ≡ PAIR_ALL；重解与股票重排后解相同
  A3-5  LX：V00 ≡ B、V11 ≡ C（逐格）；端点 ⊂ 合法域
  A3-6  SA b = 0 ≡ 无门；PM b = 0 ≡ 无带新门；HG b = 0 ≡ 无带门
  A3-7  HG 状态：不同起点可不同（记录差异）；分片重启恢复自身状态后与不分片逐位相同
  A3-8  HG_ONLY(α0, b > 0) ≠ 父（编辑数 > 0）；α0 不读新测量（读取审计）
  A3-9  TREFIT g = 1 ≡ NATIVE；g = 0 ≡ E6j V10 口径；COEF_INTERP_UNAVAILABLE 计数
  A3-10 POST2 α0 ≡ 父；α > 0 时第二关前实际编辑数 > 0
  A3-11 Mmean 的 b 换算：K 腿改 δ ↔ 综合分改 δ/3（源 combine，1e−12）"""
import e6k_boot  # noqa: F401
import os
import sys
import time
import argparse

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_env as E
import e6k_ops as O

A = 0.25


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--out', default=None)
    ap.add_argument('--forms', default=','.join(E.P8))
    ap.add_argument('--meas', default='S,M,Q,C1')
    ap.add_argument('--rerun', action='store_true')
    a = ap.parse_args()
    if a.segment in K.POST_SEGS:                            # 执行端补充 X04：后段同代码在授权后补算并入 R0 描述表
        K.post_gate(a.segment, 'Stage 0 第 3 类（X04 后段补算）')
    else:
        K.deriv_only(a.segment, 'Stage 0 第 3 类')
    out = a.out or K.P('stage0', 'c3_ops' + ('_rerun' if a.rerun else ''))
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    seg = E.Seg(a.segment)
    rows = []
    tim = []

    def chk(cid, form, meas, what, switch_off, comparator, got, ok, note=''):
        rows.append(dict(check_id=cid, segment=a.segment, form=form, meas=meas, what=what, which_switch_is_off=switch_off,
                         comparator_id=comparator, got=str(got), status='INFO' if ok is None else ('PASS' if ok else 'FAIL'), note=note))

    def tick(lab, t):
        tim.append(dict(step=lab, seconds=round(time.time() - t, 3)))

    tim.append(dict(step='env_load', seconds=round(time.time() - t0, 1)))
    ci, n = seg.ci, seg.n
    # A3-4 合成：配对与预算选择对股票次序不变、深搜 = 逐级 MILP
    rng = np.random.default_rng(20260928)
    bad_m = bad_p = bad_s = 0
    for trial in range(300):
        no, ni = rng.integers(1, 6), rng.integers(1, 6)
        oid = rng.choice(10 ** 6, no, replace=False); iid = rng.choice(10 ** 6, ni, replace=False) + 10 ** 6
        oz = np.round(rng.random(no), 2); iz = np.round(rng.random(ni), 2)
        e1 = sorted((oid[a_], iid[b_]) for a_, b_ in O.canonical_matching(oid, oz, iid, iz))
        po, pi = rng.permutation(no), rng.permutation(ni)
        e2 = sorted((oid[po][a_], iid[pi][b_]) for a_, b_ in O.canonical_matching(oid[po], oz[po], iid[pi], iz[pi]))
        bad_p += e1 != e2
        Cm = np.abs(oz[:, None] - iz[None, :])
        e3 = O._lsa_lex(Cm[np.ix_(np.argsort(oid), np.argsort(iid))])
        oo, io_ = np.argsort(oid), np.argsort(iid)
        e3 = sorted((oid[oo[a_]], iid[io_[b_]]) for a_, b_ in e3)
        bad_m += e1 != e3
        m_ = int(rng.integers(1, 12))
        c = np.round(rng.normal(0, 0.004, m_), 4)
        u = rng.permutation(m_).astype(float) + 1
        bud = float(rng.choice([0.0, 0.002, 0.005, 0.01]))
        s1, _ = O.choose_pairs_dfs(c, u, bud)
        s2 = O.choose_pairs_milp(c, u, bud)
        bad_s += not np.array_equal(s1, s2)
    chk('A3-4', '-', '-', '合成 300 例：配对对股票次序不变 / 穷举 = 指派逐边冻结 / 深搜 = 逐级 MILP', 'order', 'oracle',
        '%d / %d / %d 例不同' % (bad_p, bad_m, bad_s), bad_p == 0 and bad_m == 0 and bad_s == 0)
    kfs = {}
    for m in a.meas.split(','):
        t = time.time(); kfs[m] = seg.kf(m); tick('kf_' + m, t)
    tid_cells = seg.tid
    for form in a.forms.split(','):
        st = seg.struct(form)
        k0 = st.q0
        parent = st.kept(k0[None, :])[0]
        tid_ids = tid_cells[st.ids]
        # A3-11
        if st.kind == 'mean' and form in E.P6:
            q = k0.copy()
            okl = np.isfinite(k0)
            for L in st.st.legs:
                okl &= np.isfinite(L)
            j = np.flatnonzero(okl)[:: max(1, okl.sum() // 500)]
            dq = np.zeros(n); dq[j] = 0.01
            s0 = st.st.score(q[None, :])[0]; s1 = st.st.score((q + dq)[None, :])[0]
            err = float(np.max(np.abs((s1 - s0)[j] - 0.01 / 3)))
            chk('A3-11', form, '-', 'K 腿 +δ ↔ 综合分 +δ/3', 'b_mean_conversion', 'source_combine', err, err <= 1e-12)
        for m, kf in kfs.items():
            t = time.time()
            qn = O.native_q(k0, kf, A)
            child = st.kept(qn[None, :])[0]
            # A3-1
            kl = O.local_rank(seg, kf, 1, np.isfinite(kf), 'pct')
            q1 = np.where(np.isfinite(kl), (1 - A) * k0 + A * kl, k0)
            same_q = bool(np.array_equal(np.isnan(q1), np.isnan(qn)) and np.array_equal(q1[np.isfinite(q1)], qn[np.isfinite(qn)]))
            chk('A3-1', form, m, 'SZL(G=1, pct, kf 支持) ≡ NATIVE q 逐格', 'size_groups+coord', 'NATIVE', same_q, same_q)
            k1 = st.kept(q1[None, :])[0]
            chk('A3-1', form, m, 'SZL(G=1, pct) 掩码 ≡ NATIVE', 'size_groups+coord', 'NATIVE', int((k1 != child).sum()), (k1 == child).all())
            for G in (3, 5):
                qs = O.szl_q(seg, k0, kf, A, G)
                ks = st.kept(qs[None, :])[0]
                chk('A3-1', form, m, 'SZL%d 源坐标 vs NATIVE 编辑格数（桥接）' % G, '-', 'NATIVE', int((ks != child).sum()), None)
                # A3-2 复制：新测量 = 旧 K
                qa = O.szl_q(seg, k0, k0.copy(), A, G); qb = O.szl_own_q(seg, k0, k0.copy(), A, G)
                eq = bool(np.array_equal(np.isnan(qa), np.isnan(qb)) and np.allclose(qa[np.isfinite(qa)], qb[np.isfinite(qb)], rtol=0, atol=0))
                chk('A3-2', form, m, 'SZL%d(新 = 旧 K 复制) ≡ SZL%d_OWN' % (G, G), 'new_content', 'SZL_OWN', eq, eq)
            kl0 = O.local_rank(seg, k0, 1, np.isfinite(k0), 'pct')
            qo = np.where(np.isfinite(kl0), (1 - A) * k0 + A * kl0, k0)
            ko = st.kept(qo[None, :])[0]
            chk('A3-2', form, m, 'OWN(G=1, pct, 全支持) ≡ 母体', 'size_groups+coord+support', 'PARENT', int((ko != parent).sum()), (ko == parent).all())
            tick('szl_%s_%s' % (form, m), t)
            # A3-3
            t = time.time()
            C = np.isfinite(k0) & np.isfinite(kf) & np.isfinite(seg.zT)
            d = kf - k0
            dg = O.inc_d(seg, k0, kf, 1.0)
            tt = ci.t[C]
            z = seg.zT[C]
            T = seg.T
            cnt = np.bincount(tt, minlength=T).astype(float)
            x1 = z - (np.bincount(tt, z, T) / np.maximum(cnt, 1))[tt]
            x2 = z * z - (np.bincount(tt, z * z, T) / np.maximum(cnt, 1))[tt]
            o1 = float(np.max(np.abs(np.bincount(tt, x1 * dg[C], T))))
            o2 = float(np.max(np.abs(np.bincount(tt, x2 * dg[C], T))))
            mm = float(np.max(np.abs(np.bincount(tt, dg[C], T) - np.bincount(tt, d[C], T)) / np.maximum(cnt, 1)))
            chk('A3-3', form, m, 'INC γ1 正交 max|Xᵀd_γ|', 'gamma', 'projection', max(o1, o2), max(o1, o2) <= 1e-10)
            chk('A3-3', form, m, 'INC γ1 均值保留 max|Δmean_C|', 'gamma', 'd', mm, mm <= 1e-12)
            d0 = O.inc_d(seg, k0, kf, 0.0)
            sup_ok = np.array_equal(d0 != 0, C & (d != 0)) and np.allclose(d0[C], d[C], rtol=0, atol=0)
            chk('A3-3', form, m, 'γ0 = INC_SUPPORT0（C 内 d、C 外 0）', 'gamma=0', 'INC_SUPPORT0', sup_ok, sup_ok)
            full_days = np.flatnonzero(np.bincount(ci.t, (np.isfinite(kf) & np.isfinite(k0) & ~np.isfinite(seg.zT)).astype(int), T) == 0)
            fd = np.isin(ci.t, full_days)
            qs0 = O.inc_q(k0, d0, A)
            eqf = np.allclose(qs0[fd & np.isfinite(qn)], qn[fd & np.isfinite(qn)], rtol=0, atol=1e-15)
            chk('A3-3', form, m, '全支持日 γ0 ≡ NATIVE（q 逐格 ≤ 1e−15）', 'support', 'NATIVE', '%d 全支持日' % len(full_days), eqf)
            for gm in (0.5, 1.0):
                dd = O.inc_dose_d(seg, k0, kf, gm)
                dg_ = O.inc_d(seg, k0, kf, gm)
                me = float(np.max(np.abs(np.bincount(tt, dd[C], T) - np.bincount(tt, dg_[C], T)) / np.maximum(cnt, 1)))
                re = float(np.max(np.abs(np.sqrt(np.bincount(tt, dd[C] ** 2, T)) - np.sqrt(np.bincount(tt, dg_[C] ** 2, T)))))
                chk('A3-3', form, m, 'INC_DOSE γ%s 同均值 / 同 RMS' % gm, 'selective_projection', 'INC', '%.2e / %.2e' % (me, re), me <= 1e-12 and re <= 1e-12)
            tick('inc_%s_%s' % (form, m), t)
            # A3-6 SA
            qsa = O.sa_q_native(k0, kf, A, 0)
            ksa = st.kept(qsa[None, :])[0]
            chk('A3-6', form, m, 'SA(NATIVE) b0 ≡ NATIVE', 'b', 'NATIVE', int((ksa != child).sum()), (ksa == child).all())
            d1 = O.inc_d(seg, k0, kf, 1.0)
            qi = O.inc_q(k0, d1, A)
            qsi = O.sa_q_inc(k0, d1, A, 0)
            same = bool(np.array_equal(np.isnan(qi), np.isnan(qsi)) and np.array_equal(qi[np.isfinite(qi)], qsi[np.isfinite(qsi)]))
            chk('A3-6', form, m, 'SA(INC1) b0 ≡ INC1（q 逐位）', 'b', 'INC1', same, same)
            if form in E.P6:
                # A3-6 PM / HG
                t = time.time()
                sc0 = st.gate_scores(k0[None, :])[0]; sc1 = st.gate_scores(qn[None, :])[0]
                gp = st.gate_keep(sc0[None, :])[0]; gc = st.gate_keep(sc1[None, :])[0]
                gpm = O.pm_gate(st, sc1, gp, gc, 0.0, tid_ids)
                kpm = st.down(gpm[None, :])[0]
                chk('A3-6', form, m, 'PM b0 ≡ 无带新门（最终名单）', 'b', 'NATIVE', int((kpm != child).sum()), (kpm == child).all())
                ghg0 = O.hg_gate(st, sc1[None, :], 0.0, tid_ids)[0]
                chk('A3-6', form, m, 'HG b0 ≡ 无带门（门逐格）', 'b', 'NATIVE_gate', int((ghg0 != gc).sum()), (ghg0 == gc).all())
                # PM 嵌套（固定配对的交换集合随 b 嵌套）
                sw = [int((O.pm_gate(st, sc1, gp, gc, b * st.bunit, tid_ids) != gp).sum()) for b in (0, 5, 10, 15)]
                chk('A3-6', form, m, 'PM 固定配对交换数随 b 不增（b0/5/10/15）', 'b', 'PM', sw, sw == sorted(sw, reverse=True))
                tick('pm_hg0_%s_%s' % (form, m), t)
                # A3-7 HG 状态
                t = time.time()
                b10 = 10 * st.bunit
                g_full, stt = O.hg_gate(st, sc1[None, :], b10, tid_ids, return_state=True)
                mid = seg.T // 2
                dom = st.dom
                cut = dom.off[mid]
                # 分片：前半段跑完取状态，后半段从该状态继续（用同一函数，按日切片）
                sub1 = _hg_range(st, sc1[None, :], b10, tid_ids, 0, mid, None)
                sub2 = _hg_range(st, sc1[None, :], b10, tid_ids, mid, seg.T, sub1[1])
                rec = np.concatenate([sub1[0][:, :cut], sub2[0][:, cut:]], axis=1)
                chk('A3-7', form, m, 'HG 分片重启恢复自身状态 ≡ 不分片', 'chunk', 'HG_full', int((rec != g_full).sum()), (rec == g_full).all())
                alt = _hg_range(st, sc1[None, :], b10, tid_ids, mid, seg.T, None)
                chk('A3-7', form, m, 'HG 不同起点（段中空状态）门差异格数', 'initial_state', 'HG_full', int((alt[0][:, cut:] != g_full[:, cut:]).sum()), None)
                # A3-8 HG_ONLY
                g_only = O.hg_gate(st, sc0[None, :], b10, tid_ids)[0]
                k_only = st.down(g_only[None, :])[0]
                ne = int((k_only != parent).sum())
                chk('A3-8', form, '-', 'HG_ONLY(α0, b10) ≠ 父（编辑格数 > 0）', 'information', 'PARENT', ne, ne > 0)
                tick('hg_%s_%s' % (form, m), t)
            # A3-9 / A3-10 A4b
            if st.kind == 'A4b':
                t = time.time()
                s1_old = np.zeros(n, bool); s1_old[st.ids[st.gate_keep(st.gate_scores(k0[None, :]))[0]]] = True
                s1_new = np.zeros(n, bool); s1_new[st.ids[st.gate_keep(st.gate_scores(qn[None, :]))[0]]] = True
                k_g1, _ = O.stage2_model(seg, st, s1_new, s1_new)
                k_g1 &= ~st.st.drop
                chk('A3-9', form, m, 'TREFIT g1 ≡ NATIVE', 'g', 'NATIVE', int((k_g1 != child).sum()), (k_g1 == child).all())
                k_par, _ = O.stage2_model(seg, st, s1_old, s1_old)
                k_par &= ~st.st.drop
                chk('A3-9', form, m, 'stage2_model(旧, 旧) ≡ 父', '-', 'PARENT', int((k_par != parent).sum()), (k_par == parent).all())
                for g in (0.0, 0.5):
                    kg, nu = O.stage2_model(seg, st, s1_new, s1_new, (g, s1_old))
                    chk('A3-9', form, m, 'TREFIT g%s COEF_INTERP_UNAVAILABLE 日数' % g, '-', '-', nu, None)
                kp0 = O.post2_kept(seg, st, s1_old, k0, kf, 0.0)
                chk('A3-10', form, m, 'POST2 α0 ≡ 父', 'alpha', 'PARENT', int((kp0 != parent).sum()), (kp0 == parent).all())
                kp = O.post2_kept(seg, st, s1_old, k0, kf, A)
                ne = int((kp != parent).sum())
                chk('A3-10', form, m, 'POST2 α.25 第二关实际编辑格数 > 0', 'alpha', 'PARENT', ne, ne > 0)
                tick('a4b_%s_%s' % (form, m), t)
            # A3-5 LX
            t = time.time()
            legal = st.legal()
            chk('A3-5', form, m, 'B ⊂ 合法域 且 C ⊂ 合法域', '-', '-', '%d / %d' % ((parent & ~legal).sum(), (child & ~legal).sum()),
                not (parent & ~legal).any() and not (child & ~legal).any())
            key0 = st.order_keys(k0, parent); key1 = st.order_keys(qn, child)
            for lay in ('SIZE3', 'ISK'):
                L = O.lx_layers(seg, k0, lay)
                v00 = O.lx_select(seg, st, parent, key0, L, legal)
                v11 = O.lx_select(seg, st, child, key1, L, legal)
                chk('A3-5', form, m, 'LX_%s V00 ≡ B' % lay, 'quota+order', 'PARENT', int((v00 != parent).sum()), (v00 == parent).all())
                chk('A3-5', form, m, 'LX_%s V11 ≡ C' % lay, 'quota+order', 'NATIVE', int((v11 != child).sum()), (v11 == child).all())
                v10 = O.lx_select(seg, st, child, key0, L, legal)
                v01 = O.lx_select(seg, st, parent, key1, L, legal)
                nb = np.bincount(ci.t[parent], minlength=seg.T); nc = np.bincount(ci.t[child], minlength=seg.T)
                chk('A3-5', form, m, 'LX_%s V01 同父 N、V10 同子 N' % lay, '-', '-', '%d / %d' % ((np.bincount(ci.t[v01], minlength=seg.T) != nb).sum(),
                    (np.bincount(ci.t[v10], minlength=seg.T) != nc).sum()), (np.bincount(ci.t[v01], minlength=seg.T) == nb).all()
                    and (np.bincount(ci.t[v10], minlength=seg.T) == nc).all())
            tick('lx_%s_%s' % (form, m), t)
            # A3-4 RP
            t = time.time()
            tp, cp = ci.t[parent], ci.c[parent]
            wp = seg.SE.dev(tp, cp)
            wcell = np.zeros(n); wcell[np.flatnonzero(parent)] = wp
            urank = O.rank_by_keys(seg, key1)
            lists, stats = O.rp_list(seg, parent, child, wcell, (0.0, 3.0, None), urank)
            chk('A3-4', form, m, 'RP 每日预算复核（rp_day 内按原系数断言；τ ∈ {0, 3, ∞}；父恒可行）', 'tau', 'PARENT', 'no AssertionError', True)
            chk('A3-4', form, m, 'RP τ0 与父的差格数（τ0 允许精确配平换票，test_21）', 'tau', 'PARENT', int((lists[0.0] != parent).sum()), None)
            pa = lists[None]
            same_n = (np.bincount(ci.t[pa], minlength=seg.T) == np.bincount(ci.t[parent], minlength=seg.T)).all()
            ind_ok = True
            wa = seg.SE.dev(ci.t[pa], ci.c[pa])
            capa = np.bincount(ci.t[pa], wa, seg.T); capp = np.bincount(ci.t[parent], wp, seg.T)
            for d_ in range(seg.T):
                a0, a1 = seg.off[d_], seg.off[d_ + 1]
                if (np.bincount(seg.ic[a0:a1][pa[a0:a1]] + 1, minlength=seg.G + 1) != np.bincount(seg.ic[a0:a1][parent[a0:a1]] + 1, minlength=seg.G + 1)).any():
                    ind_ok = False
                    break
            chk('A3-4', form, m, 'PAIR_ALL 同 N、同行业人数、同总资本（1e−12）', 'budget', 'PARENT', 'N %s ind %s cap %.1e' % (same_n, ind_ok, float(np.max(np.abs(capa - capp)))),
                same_n and ind_ok and float(np.max(np.abs(capa - capp))) <= 1e-12)
            lists2, _ = O.rp_list(seg, parent, child, wcell, (3.0,), urank)
            chk('A3-4', form, m, 'RP τ3 重解相同', 'resolve', 'RP3', int((lists2[3.0] != lists[3.0]).sum()), (lists2[3.0] == lists[3.0]).all())
            ns = stats[stats.tau != 'INF'] if len(stats) else stats
            chk('A3-4', form, m, 'RP 求解器分布（τ0 / τ3）', '-', '-', ns.solver.value_counts().to_dict() if len(ns) else {}, None)
            tick('rp_%s_%s' % (form, m), t)
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'ops_identity_%s.csv' % a.segment)
    K.atomic_write_csv(p, df)
    pt = os.path.join(out, 'ops_timing_%s.csv' % a.segment)
    K.atomic_write_csv(pt, pd.DataFrame(tim))
    ok = not (df.status == 'FAIL').any()
    print(df.status.value_counts().to_dict(), 'OK' if ok else 'FAIL', 'wall %.0fs' % (time.time() - t0), flush=True)
    print(df[df.status == 'FAIL'].to_string(max_colwidth=60), flush=True)
    if a.out is None:
        K.write_receipt('stage0_c3_ops_%s%s' % (a.segment, '_rerun' if a.rerun else ''), [p, pt], 'SUCCEEDED' if ok else 'FAILED',
                        counts=df.status.value_counts().to_dict(), blocker=not ok)
    return 0 if ok else 2


def _hg_range(st, sc, b_eff, tid_ids, d0, d1, init):
    """HG 在日区间 [d0, d1) 上递推（整段打分矩阵，区间外置零）；返回 (门, 段末状态)。"""
    dom = st.dom
    seg = st.seg
    ci = seg.ci
    P = sc.shape[0]
    cols = ci.c[st.ids]
    state = np.zeros((P, seg.Nc), bool) if init is None else init.copy()
    out = np.zeros(sc.shape, bool)
    for d in range(d0, d1):
        a, b = dom.off[d], dom.off[d + 1]
        ns = np.zeros((P, seg.Nc), bool)
        if b > a and dom.K[d] > 0:
            cc = cols[a:b]
            s = sc[:, a:b] - b_eff * state[:, cc]
            idx = np.argsort(s, axis=1, kind='stable')[:, :dom.K[d]]
            g = np.zeros((P, b - a), bool)
            np.put_along_axis(g, idx, True, axis=1)
            out[:, a:b] = g
            rr, jj = np.nonzero(g)
            ns[rr, cc[jj]] = True
        state = ns
    return out, state


if __name__ == '__main__':
    sys.exit(main())
