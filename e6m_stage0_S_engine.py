# -*- coding: utf-8 -*-
"""E6m Stage 0 · 阶段 S 的引擎侧锚（附录 A2-2 / A2-3 / A2-4 抽样 / A2-5 / A2-6 / A3 真实结构；e6l_stage0_source / e6l_stage0_random 同构，
输出只写 E6m 工作目录）。**阶段 S 才跑**：需要 X01（e6e_core import 期读 roles.csv）与 E6i / E6j / E6k / E6l 原件。
B2 开发期红线：不运行本文件任何账户函数（Acct / AcctFast / compute_calendar_pnl）；只允许 `imports` 任务核 import 闭包与函数签名。
  structid --seg S  A3：真实 Struct 与 mock 逐位（ids / dom.off / dom.K / gate_scores(q0) / gate_keep / kept(q0) / down(U0) / down(Q0 α .25 门)）；
                    转录 src_mem_gate 与源 e6l_ops.mem_gate（HG10 / LAG1_10）逐位；本轮云机 kQ0 与引擎 seg.meas_kf('Q0') 逐位（A2-5 坐标）
  engine --seg S    A2-2 8bp 恒等：P8 父 × H1…20 + P6 Q0 NATIVE × 3α × H1…20 逐日 net8 = gross − 8e−4·turn（1e−12）；年化 = 252·100·mean（1e−9）
                    A2-3 R2 / A06 母体 H5 net8 日账本 = E6i 已存母体（1e−12）；六形态母体 H5 8bp 年化 = E6j 领导表（1e−9）
                    A2-5 Q（J_B1_qCC）× α .25 × H5 在 R1(= A4b_CVRv5) / R2 / A06 = E6j accounts/B 同 ID 逐日（1e−12）
                    A2-4 E6k 同构（W08 四锚 + 每类 ≤ 8 抽样）段 D / n / D_sc = policy_E6k（1e−9）；E6l 同构（Q0 × LAG1_10 抽样）= policy_E6l
                         （标 SOURCE_NUMERIC_VERIFICATION_PENDING）。对象名单用本轮算子（e6m_s_ops，源记忆门）在真实结构上生成
  random            A2-6 LEGACY_POLICY_RANDOM / CONTENT_ISK_P5（E6k 键，e6l_run_rand.Draws）× Q0 × {NATIVE, HG10, LAG1_10} × α .25 × H5 × 六形态，
                    2010-2014，1,024 路径 → 路径均值 / sd / n = E6k random_refs（LEGACY / NEW_COND_ISK_P5）与 E6l random_refs（LAG1_10；1e−12）
  imports           B2 可跑：只 import 本文件依赖的账户侧模块（需 X01），不建 Seg、不算账户；失败 → SOURCE_WAIT"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import argparse
import resource

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_stage0_S as S0

RN = S0.RN
TOL_DAILY = 1e-12
TOL_ANN = 1e-9
P6 = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
P8 = P6 + ('R2', 'A06')
W08 = ('Q0|A4b_CVRv5|LINEAR|-|a0.25|NONE|H5|SOURCE|-', 'Q0|A4b_CVRv5|LINEAR|-|a0.25|HG10|H5|SOURCE|-',
       'K0|A4b_CVRv5|OLD_RULE|-|a0|HG10|H5|SOURCE|-', 'Q0|M_union3_v2_CVRv5|LINEAR|-|a0.25|HG10|H5|SOURCE|-')
ACCOUNT_MODULES = ('e6l_env', 'e6k_env', 'e6k_acct', 'e6k_ops', 'e6l_ops', 'e6l_fast', 'e6l_run_rand', 'e6k_random', 'e6j_stats',
                   'e6j_stage0_parent_identity')


def fcmp(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    na, nb = np.isnan(a), np.isnan(b)
    m = ~(na | nb)
    return bool((na == nb).all()), float(np.max(np.abs(a[m] - b[m]))) if m.any() else 0.0


def real_seg(pname):
    import e6l_env as V
    return V.SegL(pname, state=False)


def source_mem_gate(st, sc, U, kind, b):
    """源记忆门（e6l_ops.mem_gate）包成 e6m_s_ops.Ctx(mem_gate=…) 的接口：(st, sc, U, 'HG'|'LAG1', b) → G (P, len(ids))。"""
    import e6l_ops as LO
    op = {'HG': 'HG%d', 'LAG1': 'LAG1_%d'}[kind] % int(b)
    G, _, _ = LO.mem_gate(st, sc, U, LO.parse_op(op), b_day=np.full(st.seg.T, float(b)))
    return G


def kept_of(seg, st, did, kfs):
    """E6m SOURCE / OLD_RULE / PARENT 描述符 → 真实结构上的最终名单（本轮算子 + 源记忆门）。"""
    import e6m_s_ops as SO
    f, p, op, prm, a, mem, H, ad, cond = did.split('|')
    ctx = SO.Ctx(st, kfs.get(f), mem_gate=source_mem_gate)
    if op == 'PARENT':
        G = ctx.U0
    elif op == 'OLD_RULE':
        G = SO.source_gate(SO._OldCtx(ctx), 0.0, mem)[0]
    else:
        G = SO.source_gate(ctx, float(a[1:]), mem)[0]
    return st.down(G[None, :])[0]


# ====================================================================== structid（A3 真实结构 = mock；A2-5 坐标）
def task_structid(pname, B):
    import e6m_s_mock as MK
    import e6m_s_ops as SO
    import e6m_stage0_S_feat as FT
    seg = real_seg(pname)
    mk = MK.MockSeg(pname)
    need = ('pool0', 'p0', 'data', 'clean', 'log_mcap', 'industry', 'pcond', 'ptvol', 'pcr20', 'fac_tvol', 'neu_tvol', 'neu_cr20', 'neu_cvr')
    miss = [k for k in need if k not in seg.ctx]                     # mock 坐标代码（SizeCtx / Targets / v_tails / aux stage2 / 随机入口）读这些键
    B.ok('A3', pname, '真实 Env.ctx 含 mock 坐标代码用到的键（%d 个）' % len(need), '缺 0', '缺 %s' % miss, not miss)
    B.ok('A3', pname, '单元数 / T / Nc（真实 vs mock）', '%d / %d / %d' % (seg.n, seg.T, seg.Nc), '%d / %d / %d' % (mk.n, mk.T, mk.Nc),
         (seg.n, seg.T, seg.Nc) == (mk.n, mk.T, mk.Nc))
    B.ok('A3', pname, '单元次序 (t, c) 与 ticker 整数', '逐位', '', np.array_equal(seg.ci.t, mk.ci.t) and np.array_equal(seg.ci.c, mk.ci.c)
         and np.array_equal(np.asarray(seg.tid), np.asarray(mk.tid)))
    kq_eng = seg.meas_kf('Q0')
    kq_me = FT.meas(pname)['kQ0']
    eq, pat, neq, md = FT.cmp_cells(np.asarray(kq_eng, float), np.asarray(kq_me, float)) if len(kq_eng) == len(kq_me) else (False, -1, -1, np.nan)
    B.ok('A2-5', pname, '本轮云机 kQ0（meas）= 引擎 seg.meas_kf(Q0)（E6j 缓存经源中性化 / 方向 / 秩）逐位', '0 / 0',
         'NaN 模式 %d / 不等 %d / max|Δ| %.3e' % (pat, neq, md), eq, '通过 → 阶段 N 的 ANCHOR_PENDING（kQ / B3 坐标）转 ANCHOR_PASSED 的前提之一')
    for form in P6:
        st, sm = seg.struct(form), mk.struct(form)
        same_ids = np.array_equal(st.ids, sm.ids) and np.array_equal(st.dom.off, sm.dom.off) and np.array_equal(np.asarray(st.dom.K), np.asarray(sm.dom.K))
        B.ok('A3', '%s %s' % (pname, form), 'dom.ids / dom.off / dom.K', '逐位', '', same_ids)
        if not same_ids:
            continue
        s1, s2 = st.gate_scores(st.q0[None, :]), sm.gate_scores(sm.q0[None, :])
        U1, U2 = st.gate_keep(s1), sm.gate_keep(s2)
        same_kept = np.array_equal(U1, U2) and np.array_equal(st.kept(st.q0[None, :]), sm.kept(sm.q0[None, :]))
        same_down = np.array_equal(st.down(U1), sm.down(U2))
        same_sc = np.array_equal(s1, s2, equal_nan=True)
        # 阶段 S 全部在真实结构上重算：门分不逐位但名单 / 下游逐位只记 INFO（不卡门）；名单 / 下游不逐位才 FAIL
        B.add('A3', '%s %s' % (pname, form), 'gate_scores(q0)', '逐位', 'max|Δ| %.3e' % float(np.nanmax(np.abs(s1 - s2))) if not same_sc else '逐位',
              'PASS' if same_sc else ('INFO' if (same_kept and same_down) else 'FAIL'))
        B.ok('A3', '%s %s' % (pname, form), 'gate_keep / kept(q0)', '逐位', '', same_kept)
        B.ok('A3', '%s %s' % (pname, form), 'down(U0)', '逐位', '', same_down)
        c1, c2 = SO.Ctx(st, kq_eng), SO.Ctx(sm, kq_me)
        g1, g2 = SO.source_gate(c1, 0.25)[0], SO.source_gate(c2, 0.25)[0]
        B.ok('A3', '%s %s' % (pname, form), 'Q0 α .25 门与 down（编辑过的门）', '逐位', '', np.array_equal(g1, g2) and np.array_equal(st.down(g1[None, :]), sm.down(g2[None, :])))
        lo1, lo2 = SO.k_loading_cells(st), SO.k_loading_cells(sm)
        B.ok('A3', '%s %s' % (pname, form), 'K_loading（plan §4.2）', '逐位', '', np.array_equal(np.asarray(lo1, float), np.asarray(lo2, float), equal_nan=True))
        sc = c1.native_s(0.25)[None, :]
        U = st.gate_keep(sc)
        import e6m_s_real as RL
        dk = SO.mid_gate_day(st)
        for kind in ('HG', 'LAG1'):
            a_ = SO.src_mem_gate(st, sc, U, kind, 10.0)
            b_ = source_mem_gate(st, sc, U, kind, 10.0)
            B.ok('A3', '%s %s' % (pname, form), '转录 src_mem_gate = 源 e6l_ops.mem_gate（%s10，Q0 α .25）' % kind, '逐位', int((a_ != b_).sum()), np.array_equal(a_, b_))
            ga, sa = SO.src_mem_gate_s(st, sc, U, kind, 10.0, d1=dk)               # 断点续跑（plan §13.3；附属第 7 项连续链）：中段门日切分
            gb, sb = SO.src_mem_gate_s(st, sc, U, kind, 10.0, state=sa, d0=dk)
            ha, ta = RL.source_mem_gate_s(st, sc, U, kind, 10.0, d1=dk)
            hb, tb = RL.source_mem_gate_s(st, sc, U, kind, 10.0, state=ta, d0=dk)
            ok_ = (np.array_equal(ga | gb, a_) and np.array_equal(ha | hb, b_) and np.array_equal(ga, ha) and np.array_equal(gb, hb)
                   and SO.states_equal(sa, ta) and SO.states_equal(sb, tb))
            B.ok('A3', '%s %s' % (pname, form), '断点续跑：转录 = 源（%s10，Q0 α .25，d%d 切分；分片 G = 全程、两段末状态逐键）' % (kind, dk), '逐位',
                 int(((ga | gb) != (ha | hb)).sum()), ok_)
    targets_vs_acct(seg, mk, kq_eng, B)


def targets_vs_acct(seg, mk, kq, B):
    """Stage A 的目标层统计转录（e6m_s_stage_a.Targets + SizeCtx，mock 坐标）= 源 e6k_acct.Acct.target_stats（真实 Seg）逐键逐位：
    同一组名单（父、Q0 α .25、BAND_Q w .1、PRIORITY c .2、HARD c .2）分别送两边。单元坐标相同由上面的 A3 次序检查保证。"""
    import e6k_acct as AC
    import e6m_s_ops as SO
    import e6m_s_stage_a as SA
    acct = AC.Acct(seg)
    TG = SA.Targets(mk)
    for form in P6:
        st = seg.struct(form)
        F0 = st.kept(st.q0[None, :])[0]
        ctx = SO.Ctx(st, kq)
        masks = [('父', F0), ('Q0 α .25', st.down(SO.source_gate(ctx, 0.25)[0][None, :])[0]),
                 ('BAND_Q w .1', st.down(SO.band_gates(ctx, 0.1)[0][None, :])[0]),
                 ('PRIORITY c .2', st.down(SO.priority_gates(ctx, 0.2)[0][None, :])[0]),
                 ('HARD c .2', st.down(SO.hard_gates(ctx, 0.2)[0][None, :])[0])]
        tp = acct.target(F0)
        for name, kept in masks:
            par = None if name == '父' else F0
            ref = acct.target_stats(acct.target(kept), kept, par, None if par is None else tp)
            mine = TG.stats(kept, par)
            ks = sorted(set(ref) & set(mine))
            bad = [k for k in ks if not np.array_equal(np.asarray(ref[k], float), np.asarray(mine[k], float), equal_nan=True)]
            near = [k for k in bad if np.nanmax(np.abs(np.asarray(ref[k], float) - np.asarray(mine[k], float))) <= 1e-12]
            B.ok('A3', '%s %s %s' % (seg.pname, form, name), 'Stage A Targets.stats = e6k_acct.target_stats（%d 键）' % len(ks), '0 键不逐位',
                 '不逐位 %d（其中 ≤ 1e−12：%d）：%s' % (len(bad), len(near), bad[:6]), len(bad) == len(near),
                 '只在一边的键：%s' % sorted(set(ref) ^ set(mine))[:8])


# ====================================================================== engine（A2-2 / A2-3 / A2-5 / A2-4）
def task_engine(pname, B, root):
    import e6k_env as E
    import e6k_ops as KO
    import e6k_acct as AC
    import e6j_stats as ST
    import e6j_stage0_parent_identity as PI
    import e6m_stage0_S_feat as FT
    seg = real_seg(pname)
    acct = AC.Acct(seg)
    Hs = tuple(range(1, 21))
    worst = worst_ann = 0.0
    nacc = 0
    kQ = seg.meas_kf('Q0')
    for form in P8:
        st = seg.struct(form)
        tp = acct.target(st.kept(st.q0[None, :])[0])
        lists = [acct.ledgers(tp, Hs, impact=False, roll=False)]
        if form in P6:
            for a in (0.125, 0.25, 0.5):
                kept = st.kept(KO.native_q(st.q0, kQ, a)[None, :])[0]
                lists.append(acct.ledgers(acct.target(kept), Hs, par=tp, impact=False, roll=False))
        for lg in lists:
            for H in Hs:
                x = lg[H]
                r = x['net8'] - (x['gross'] - 8e-4 * x['turn'])
                m = np.isfinite(r)
                worst = max(worst, float(np.max(np.abs(r[m]))) if m.any() else 0.0)
                worst_ann = max(worst_ann, abs(float(np.nanmean(x['net8'])) * M.ANN - 252.0 * 100.0 * float(np.nanmean(x['net8']))))
                nacc += 1
    B.ok('A2-2', '%s PARENT × H1…20 + Q0 NATIVE × 3α × H1…20' % pname, '逐日 net8 − (gross − 8e−4·turn)（%d 账户）' % nacc, '≤ 1e−12', '%.2e' % worst,
         worst <= TOL_DAILY)
    B.ok('A2-2', '%s ANN' % pname, '年化 = 252 × 100 × mean', '≤ 1e−9', '%.2e' % worst_ann, worst_ann <= TOL_ANN)
    if os.path.isdir(os.path.join(root, RN['I'], 'accounts', pname)):
        for mn in ('R2', 'A06'):
            st = seg.struct(mn)
            par = st.kept(st.q0[None, :])[0]
            led = acct.ledgers(acct.target(par), (5,), impact=False, roll=False)[5]
            ref = PI.e6i_parent_ledger(pname, mn)
            both = np.isfinite(ref['parent'])
            sn, md = fcmp(np.where(both, led['net8'], np.nan), ref['parent'])
            B.ok('A2-3', '%s %s' % (pname, mn), 'H5 net8 日账本 vs E6i 已存母体（%s）' % ref['descriptor_id'], '≤ 1e−12', '%.3e' % md, sn and md <= TOL_DAILY)
            ann = float(np.nanmean(led['net8'])) * M.ANN
            B.ok('A2-3', '%s %s' % (pname, mn), 'net8 年化 vs E6i parent_net8_ann', ref['parent_net8_ann'], ann, abs(ann - ref['parent_net8_ann']) <= TOL_ANN)
    else:
        B.add('A2-3', '%s R2 / A06' % pname, 'H5 net8 日账本 vs E6i 已存母体', '≤ 1e−12', 'X09 未到', 'SOURCE_WAIT')
    lp = os.path.join(root, RN['J'], 'carried', 'leader_six_forms_capital.csv')
    if os.path.exists(lp):
        lead = pd.read_csv(lp)
        for form in P6:
            st = seg.struct(form)
            led = acct.ledgers(acct.target(st.kept(st.q0[None, :])[0]), (5,), impact=False, roll=False)[5]
            ann = float(np.nanmean(led['net8'])) * M.ANN
            ref = float(lead[(lead.segment == pname) & (lead.form == form)].total_net8_ann.iloc[0])
            B.ok('A2-3', '%s %s' % (pname, form), '母体 H5 8bp 年化 = E6j 领导表 total_net8_ann', ref, ann, abs(ann - ref) <= TOL_ANN)
    else:
        B.add('A2-3', '%s 六形态' % pname, '母体 H5 8bp 年化 = E6j 领导表', '≤ 1e−9', 'X08 未到', 'SOURCE_WAIT')
    keys = ('gross', 'pos', 'turn', 'net8', 'sc_child', 'sc_parent', 'bracket', 'qmiss')
    for mn, e6j_m in (('A4b_CVRv5', 'R1'), ('R2', 'R2'), ('A06', 'A06')):
        bp = os.path.join(root, RN['J'], 'accounts', 'B', pname, '%s__B1.npz' % e6j_m)
        if not os.path.exists(bp):
            B.add('A2-5', '%s %s|Q' % (pname, mn), 'Q × α .25 × H5 = E6j accounts/B 逐日', '≤ 1e−12', 'X08 未到', 'SOURCE_WAIT')
            continue
        st = seg.struct(mn)
        tp = acct.target(st.kept(st.q0[None, :])[0])
        zb = np.load(bp, allow_pickle=False)
        did = 'B|B1|%s|K|%s|low_bad|FALLBACK|a=0.25|H5' % (e6j_m, E.MEAS['Q'][1])
        desc = [str(x) for x in zb['desc']]
        if did not in desc:
            B.add('A2-5', '%s %s|Q' % (pname, mn), 'E6j 描述符存在', did, 'MISSING', 'FAIL')
            continue
        row = desc.index(did)
        kept = st.kept(KO.native_q(st.q0, seg.kf('Q'), 0.25)[None, :])[0]
        led = acct.ledgers(acct.target(kept), (5,), par=tp, roll=False)[5]
        for k in keys:
            if k in zb.files:
                sn, md = fcmp(led[k], zb[k][row])
                B.ok('A2-5', '%s %s|Q' % (pname, mn), '%s 逐日（NaN 位置一致）' % k, '≤ 1e−12', '%.3e' % md, sn and md <= TOL_DAILY)
    # ---- A2-4 抽样锚
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    kfs = {'Q0': kQ, 'C1': seg.meas_kf('C1')}
    rng = np.random.default_rng(M.stable_seed_int('E6m.stage0S.A2-4', pname) % (2 ** 63))
    KC = ('E6K_POLICY', 'E6K_POLICY(K0×HG_ONLY10)')
    kpp = os.path.join(root, RN['K'], 'results', 'full', 'policy_E6k.csv')
    if os.path.exists(kpp):   # 登记为 E6K_POLICY 但 policy_E6k 无同构行 → 改由 E6l 锚（2026-10-10 用户定；登记不改；前提 = anchormap 的 E6k∩E6l 一致性检查）
        kidx = set(pd.read_csv(kpp, usecols=['desc_id']).desc_id)
        D = D.copy()
        D.loc[D.anchor_candidate.isin(KC) & ~D.desc_id.map(FT.e6k_equiv).isin(kidx), 'anchor_candidate'] = 'E6K_UNCOVERED'
    for ref_name, src, cands, eqf, label in (('E6k', 'E6k', KC, FT.e6k_equiv, ''),
                                        ('E6l', 'E6l', ('E6L_POLICY',), FT.e6l_equiv, 'SOURCE_NUMERIC_VERIFICATION_PENDING'),
                                             ('E6l（E6k 未覆盖）', 'E6l', ('E6K_UNCOVERED',), FT.e6l_equiv,
                                              'E6K_UNCOVERED→E6L（前提 = anchormap 的 E6k∩E6l 一致性检查）')):
        pp = os.path.join(root, RN['K' if src == 'E6k' else 'L'], 'results', 'full', 'policy_%s.csv' % src)
        if not os.path.exists(pp):
            B.add('A2-4', '%s %s 同构抽样' % (pname, ref_name), '段 D / n / D_sc = policy_%s' % src, '≤ 1e−9', '%s policy 未到' % ref_name, 'SOURCE_WAIT')
            continue
        pol = pd.read_csv(pp, keep_default_na=False, na_values=['']).set_index('desc_id')
        Dq = D[D.anchor_candidate.isin(cands)].copy()
        Dq['cls'] = Dq.measurement + ':' + Dq.memory + ':' + Dq.operator
        pick = set(x for x in W08 if x in set(Dq.desc_id))
        for cls, g in Dq.groupby('cls'):
            pick |= set(rng.choice(g.desc_id.values, size=min(len(g), 8), replace=False))
        worst, nbad, n = 0.0, 0, 0
        for did in sorted(pick):
            r = Dq[Dq.desc_id == did].iloc[0]
            rid = eqf(did)
            if rid not in pol.index:
                B.add('A2-4', did, '%s policy 有同构行' % src, rid, '缺', 'FAIL')
                nbad += 1
                continue
            st = seg.struct(r.parent)
            H = int(r.H)
            kept = kept_of(seg, st, did, kfs)
            tp = acct.target(st.kept(st.q0[None, :])[0])
            led = acct.ledgers(acct.target(kept), (H,), par=tp, impact=False, roll=False)[H]
            lpar = acct.ledgers(tp, (H,), impact=False, roll=False)[H]
            Dm, nm = ST.seg_D(ST.paired(led['net8'], lpar['net8'])[0])
            Dsc, _ = ST.seg_D(ST.paired(led['sc_child'], led['sc_parent'])[0])
            e = pol.loc[rid]
            De, ne, Dsce = float(e['D_%s' % pname]), float(e['n_%s' % pname]), float(e['D_sc_%s' % pname])
            err = max(abs(Dm - De), abs(Dsc - Dsce), abs(nm - ne))
            worst = max(worst, err)
            ok = err <= TOL_ANN
            nbad += int(not ok)
            n += 1
            if did in W08 or not ok:
                B.ok('A2-4', did, 'D / n / D_sc = policy_%s[%s]' % (src, rid), '%.6f / %d / %.6f' % (De, ne, Dsce), '%.6f / %d / %.6f' % (Dm, nm, Dsc), ok, label)
        B.ok('A2-4', '%s %s 抽样 %d 个（全集 %d）' % (pname, ref_name, n, len(Dq)), 'max |Δ|（D / D_sc / n）', '≤ 1e−9', '%.2e（不符 %d）' % (worst, nbad),
             nbad == 0, label)
    B.add('A6-2', pname, 'maxrss（engine）', '≤ 80 GB', '%.2f GB' % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576.0), 'INFO')


# ====================================================================== random（A2-6）
def make_draws(seg, kfs=None):
    """E6m 机制名 → E6l / E6k 内容置换器（E6k 键；e6l_run_rand.Draws）。
    kfs：本轮测量坏度（e6m_s_real.kfs_of；与 E6l meas_kf 同表示）——只在 E6l 环境不认识该测量时用（E6m 新增两日测量；2026-10-11）。"""
    import e6l_run_rand as RR
    cache = {}
    names = {'LEGACY_POLICY_RANDOM': 'LEGACY_POLICY_RANDOM', 'CONTENT_ISK_P5': 'CONTENT_COND_ISK_P5'}

    def kf_of(meas):
        try:
            return seg.meas_kf(meas)
        except ValueError as e:
            if kfs is None or meas not in kfs or str(e) != meas:
                raise
            return kfs[meas]

    def draws(mech, meas, form, paths):
        k = (mech, meas)
        if k not in cache:
            cache[k] = RR.Draws(seg, names[mech], meas, kf_of(meas))
        return cache[k].draw(form, list(paths), seg.struct(form).q0)
    return draws


def _rand_one(args):
    pname, form, out_dir, npaths = args
    import e6l_fast as FA
    import e6m_s_rand_run as RR
    import e6m_s_real as RL
    seg = RL.seg_of(pname, 'real')                             # 与阶段 S 随机驱动同一适配视图
    AF = FA.AcctFast(seg)
    cal = np.load(M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), allow_pickle=False)['dates']   # P5 绝对日序的全程日历（plan §5 第 11 项）
    rt = RR.RT(seg, form, None, cal, None, None, {'Q0': seg.meas_kf('Q0')}, mem_gate=source_mem_gate)   # 阶段 S：源记忆门
    draws = make_draws(seg)
    rows = [dict(owner_id='Q0|%s|LINEAR|-|a0.25|%s|H5|SOURCE|-' % (form, mem), H=5, aux_id='S0_A2_6|%s|%s' % (form, mem)) for mem in ('NONE', 'HG10', 'LAG1_10')]
    outs = []
    for mech in ('LEGACY_POLICY_RANDOM', 'CONTENT_ISK_P5'):
        p = os.path.join(out_dir, mech, pname, '%s__p0_%d.npz' % (form, npaths))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        outs.append(RR.run_accounts(rt, AF, rows, mech, 0, npaths, p, draws=draws))
    return outs


def task_random(B, root, workers, npaths=1024, pname='2010-2014'):
    import glob
    import multiprocessing as mp
    import e6m_stage0_S_feat as FT
    od = M.P('stage0_S', 'c5', 'randoms')
    with mp.get_context('spawn').Pool(min(workers, len(P6))) as pool:
        pool.map(_rand_one, [(pname, f, od, npaths) for f in P6])
    refs = {}
    for nm, rr in (('E6k', 'K'), ('E6l', 'L')):
        p = os.path.join(root, RN[rr], 'results', 'full', 'random_refs_%s.csv' % pname)
        refs[nm] = pd.read_csv(p) if os.path.exists(p) else None
    emap = {('E6k', 'LEGACY_POLICY_RANDOM'): 'LEGACY_POLICY_RANDOM', ('E6k', 'CONTENT_ISK_P5'): 'NEW_COND_ISK_P5',
            ('E6l', 'LEGACY_POLICY_RANDOM'): 'LEGACY_POLICY_RANDOM', ('E6l', 'CONTENT_ISK_P5'): 'CONTENT_COND_ISK_P5'}
    for mech in ('LEGACY_POLICY_RANDOM', 'CONTENT_ISK_P5'):
        acc = {}
        for f in sorted(glob.glob(os.path.join(od, mech, pname, '*.npz'))):
            z = np.load(f, allow_pickle=False)
            for i, (did, H) in enumerate(zip([str(x) for x in z['desc']], z['H'])):
                acc[(did, int(H))] = z['s_net'][i] / z['n_net'][i] * M.ANN
        for nm, eqf, mems in (('E6k', FT.e6k_equiv, ('NONE', 'HG10')), ('E6l', FT.e6l_equiv, ('LAG1_10',))):
            E = refs[nm]
            if E is None:
                B.add('A2-6', '%s %s' % (nm, mech), '路径均值 / sd / n = %s random_refs' % nm, '≤ 1e−12', 'random_refs 未到', 'SOURCE_WAIT')
                continue
            worst, nobj, det = 0.0, 0, []
            for (did, H), v in sorted(acc.items()):
                if did.split('|')[5] not in mems:
                    continue
                e = E[(E.desc_id == eqf(did)) & (E.H == H) & (E.mechanism == emap[(nm, mech)])]
                if not len(e):
                    det.append('%s：%s 无同对象' % (did, nm))
                    worst = max(worst, 1.0)
                    continue
                e = e.iloc[0]
                m, sd = float(np.mean(v)), float(np.std(v, ddof=1))
                err = max(abs(m - e.rand_mean), abs(sd - e.rand_sd)) if len(v) == int(e.n) else 1.0
                worst = max(worst, err)
                nobj += 1
                det.append('%s n %d/%d mean %.6f/%.6f' % (did.split('|')[1], len(v), int(e.n), m, e.rand_mean))
            want = 12 if nm == 'E6k' else 6
            B.ok('A2-6', '%s → %s %s' % (mech, nm, emap[(nm, mech)]), '%d 个对象路径均值 / sd / n（1e−12）' % nobj, '%d 对象' % want,
                 'max|Δ| %.2e；%s' % (worst, '; '.join(det[:3])), nobj == want and worst <= 1e-12)


# ====================================================================== imports（B2 可跑）
def task_imports(B):
    for m in ACCOUNT_MODULES:
        try:
            __import__(m)
            B.add('A3', m, '账户侧模块 import', 'OK', 'OK', 'PASS')
        except Exception as e:                                   # noqa: BLE001
            B.add('A3', m, '账户侧模块 import', 'OK', type(e).__name__, 'SOURCE_WAIT', 'X01 到达前 import 期读 roles.csv 失败属预期')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['structid', 'engine', 'random', 'imports'])
    ap.add_argument('--seg', default='2010-2014')
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--npaths', type=int, default=1024)
    a = ap.parse_args()
    t0 = time.time()
    root = S0.default_root()
    B = S0.Book()
    od = M.P('stage0_S', {'structid': 'c3', 'engine': 'c2_c4', 'random': 'c5', 'imports': 'c3'}[a.task])
    os.makedirs(od, exist_ok=True)
    if a.task == 'structid':
        task_structid(a.seg, B)
        tag = 'structid_%s' % a.seg
    elif a.task == 'engine':
        task_engine(a.seg, B, root)
        tag = 'engine_%s' % a.seg
    elif a.task == 'random':
        task_random(B, root, a.workers, a.npaths)
        tag = 'random'
    else:
        task_imports(B)
        tag = 'imports'
    p = os.path.join(od, 'checks_%s.csv' % tag)
    B.write(p)
    df = B.df()
    cnt = df.status.value_counts().to_dict()
    M.write_receipt(os.environ.get('E6M_TASK', 'S0_engine_' + tag), [p], status='SUCCEEDED', code=[__file__, S0.__file__, M.__file__], counts=cnt,
                    wall_s=round(time.time() - t0, 1), maxrss_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576.0, 2),
                    note='FAIL 行是检查结果（Stage 0 门在 close 汇总），不是任务失败')
    print(json.dumps(dict(task=tag, counts=cnt, wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    show = df[df.status.isin(['FAIL', 'NOT_RUN'])]
    if len(show):
        print(show[['item', 'object', 'metric', 'expected', 'got', 'status']].head(40).to_string(max_colwidth=70))
    return 0


if __name__ == '__main__':
    sys.exit(main())
