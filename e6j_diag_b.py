# -*- coding: utf-8 -*-
"""E6j B 块诊断（plan §5.1a / §4.1a / §5.4 C）：一个进程 = (段, 母体)。
  CS       每登记行 × 母体：J = 新分量有效 ∩ 旧腿有效；在 J 上按源口径重做旧腿与新分量的市值中性化和排名（其余母体输入不变）；
           C0（共同支持母）/ C1（共同支持子）@ α .25 × H{3,5,10,20}；闭合 N1−N0 = (C1−C0)+(C0−N0)+(N1−C1)
  TR       S_source（K_rar20 低坏）、J SLOPE20_TR_CC（低坏，M 的 J 版）、J MR3_TR_CC（高坏，MA3 的 J 版）主配置 α .25 × H5 的 TRANSPORT 版
  DOSE     B3-C：COMMON-DOSE（J_t 内统一用 α·mean(r)）与 r-shuffle（r 在同日旧 K 三档内按五日优先序置换、固定 qM；1,024 路径）
R1 的 T 槽位：旧腿 = 母体第二阶段 T 分数（S1 内），CS 在 S1 ∧ J 内重做。写 diagnostics/B/<段>/<母体>.csv。"""
import e6j_boot  # noqa: F401
import os
import sys
import time

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_engine as EN
import e6j_random as RND
import e6j_run_b as RB
import e6j_slot as SL

OUT = os.path.join(J.RES, 'diagnostics', 'B')
HS_CS = (3, 5, 10, 20)
A = 0.25


def ann(x):
    return float(np.nanmean(x)) * J.ANN


def pct_on(env, raw_c, set_cells, direction):
    """(T, Nc) 原值在给定单元集合（pool0 内）上按源 NS 口径中性化 → 方向排名 → 单元（集合外 NaN）。"""
    import e6f_core as F
    import e6g_core as G
    S, ci = env.S, env.ci
    df = pd.DataFrame(np.full((S.T, S.Nfull), np.nan), index=S.pool0.index, columns=S.pool0.columns)
    df.iloc[:, S.ccols] = raw_c
    sm = np.zeros((S.T, S.Nfull)); sm[ci.t[set_cells], np.asarray(S.ccols)[ci.c[set_cells]]] = 1.0
    sdf = pd.DataFrame(sm, index=S.pool0.index, columns=S.pool0.columns)
    cache, _ = F.neu_cache(df, sdf, S.log_mcap, S.icodes_neu, 'NS')
    return env.cells_of_dense(G.pct_dense_dir(cache, S.dates, S.ccolpos, S.Nc, 'hi' if direction == 'high_bad' else 'lo'))


def cs_structure(env, mother, slot, legJ):
    """与 EN.research_structure 相同结构，只把槽位旧腿换成 J 上重算的腿（J 外 NaN，按源规则处理）。"""
    if mother == 'R1':
        if slot == 'K':
            return EN.DepK(env, True, q0=legJ)
        st = EN.DepT(env)
        st.q0 = legJ
        import e6i_randoms as IR
        st.dom = IR.KeepDom(env.ci, np.isfinite(legJ) & st.M.s1_c, st.M.core['b'])
        return st
    M = env.R.mother(mother)
    i = M.leg_roles.index(slot)
    legs = list(M.legs_c); legs[i] = legJ
    return EN.MeanSlot(env, legs, i, M.core['s'], M.core['fam'].startswith('KTC'), M.dr_c)


def run(pname, mother):
    t0 = time.time()
    RB.gate(pname)
    import e6i_ops as O
    rows_reg = pd.read_csv(os.path.join(J.RES, 'registry', 'rows_B.csv'))
    rows_reg = rows_reg[rows_reg.mothers.str.split('|').apply(lambda m: mother in m)]
    env = EN.Env(pname, with_prod=False)
    ci, SE, T, S = env.ci, env.SE, env.S.T, env.S
    M = env.R.mother(mother)
    out = []
    # 旧腿原值
    old_raw = {}
    if mother == 'R1':
        old_raw['K'] = SL.e6i_member_raw(pname, 'K0_LEGACY')[0]
        old_raw['T'] = None
    else:
        for i, role in enumerate(M.leg_roles):
            old_raw[role] = O._raw_c(S, M.core['comps'][i])
    for (slot, mid), grp in rows_reg.groupby(['slot', 'measurement_id']):
        if slot not in old_raw:
            continue
        st = EN.research_structure(env, mother, slot)
        parent = st.kept(st.q0[None, :])[0]
        ledN0 = SE.pnl(ci.t[parent], ci.c[parent], SE.dev(ci.t[parent], ci.c[parent]), HS_CS, 8.0)
        b3c = grp.block.iloc[0] == 'B3C'
        if b3c:                                           # B3-C：新分量 = qM（低坏），α 数组 = α·r
            yn = mid.split('_')[-1]
            qm_id, qm_src = ('K_slope20', 'E6I') if yn == 'CC' else ('J_B2_SLOPE20_TR_ID', 'J')
            raw = RB.raw_cells(env, pname, qm_id, qm_src)
            rr = env.cells_of_dense(RB.raw_cells(env, pname, mid, 'J')); rr = np.where(np.isfinite(rr), rr, 0.0)
        else:
            raw = RB.raw_cells(env, pname, mid, grp.source.iloc[0])
            rr = None
        for _, row in grp.iterrows():
            aa = A * rr if rr is not None else A
            if mother == 'R1' and slot == 'T':
                znew = RB.s1_pct(env, raw, row.direction)
                Jc = np.isfinite(znew) & np.isfinite(st.q0) & M.s1_c
                legJ = pct_on(env, _dense(env, M.T_raw_c), Jc, 'high_bad')
                newJ = pct_on(env, raw, Jc, row.direction)
            else:
                znew = RB.ns_pct(env, raw, row.direction)
                Jc = np.isfinite(znew) & np.isfinite(st.q0)
                legJ = pct_on(env, old_raw[slot], Jc, 'high_bad')
                newJ = pct_on(env, raw, Jc, row.direction)
            child = st.kept(EN.blend(st.q0, [(1.0, znew[None, :])], aa))[0]
            stJ = cs_structure(env, mother, slot, legJ)
            c0 = stJ.kept(stJ.q0[None, :])[0]
            c1 = stJ.kept(EN.blend(stJ.q0, [(1.0, newJ[None, :])], aa))[0]
            L = {}
            for lab, k in (('N1', child), ('C0', c0), ('C1', c1)):
                t, c = ci.t[k], ci.c[k]
                L[lab] = SE.pnl(t, c, SE.dev(t, c), HS_CS, 8.0)
            for H in HS_CS:
                n0, n1, x0, x1 = ledN0[H][3], L['N1'][H][3], L['C0'][H][3], L['C1'][H][3]
                out.append(dict(segment=pname, mother=mother, slot=slot, measurement_id=mid, direction=row.direction, block=row.block, H=H,
                                diag='CS', N1_minus_N0=ann(n1 - n0), C1_minus_C0=ann(x1 - x0), C0_minus_N0=ann(x0 - n0), N1_minus_C1=ann(n1 - x1),
                                closure_resid=ann((n1 - n0) - ((x1 - x0) + (x0 - n0) + (n1 - x1))), J_share=float(Jc.mean())))
    # ---- TRANSPORT（S / M / MA3 主配置）
    trs = [('K_rar20', 'E6I', 'low_bad'), ('J_B2_SLOPE20_TR_CC', 'J', 'low_bad'), ('J_B2_MR3_TR_CC', 'J', 'high_bad')]
    st = EN.research_structure(env, mother, 'K') if 'K' in (M.leg_roles if mother != 'R1' else ['K']) else None
    if st is not None and mother != 'A08':
        parent = st.kept(st.q0[None, :])[0]
        n0 = SE.pnl(ci.t[parent], ci.c[parent], SE.dev(ci.t[parent], ci.c[parent]), (5,), 8.0)[5][3]
        for mid, src, d in trs:
            raw = RB.raw_cells(env, pname, mid, src)
            cache = RB.ns_cache(env, raw)
            z = RB.pct_of(env, cache, d)
            ztr = transport_cells(env, st.q0, cache, d)
            for lab, zz in (('SRC', z), ('TRANSPORT', ztr)):
                k = st.kept(EN.blend(st.q0, [(1.0, zz[None, :])], A))[0]
                n = SE.pnl(ci.t[k], ci.c[k], SE.dev(ci.t[k], ci.c[k]), (5,), 8.0)[5][3]
                out.append(dict(segment=pname, mother=mother, slot='K', measurement_id=mid, direction=d, H=5, diag='TR_%s' % lab,
                                child_minus_parent=ann(n - n0), cells_vs_parent=int((k != parent).sum())))
    # ---- DOSE（B3-C）
    if mother != 'A08':
        st = EN.research_structure(env, mother, 'K')
        parent = st.kept(st.q0[None, :])[0]
        n0 = SE.pnl(ci.t[parent], ci.c[parent], SE.dev(ci.t[parent], ci.c[parent]), (5,), 8.0)[5][3]
        oldk3 = RND.terciles_rowwise(_dense(env, st.q0), _dense_b(env, np.isfinite(st.q0)))[ci.t, ci.c]
        for yn, qm_id, qm_src in (('CC', 'K_slope20', 'E6I'), ('ID', 'J_B2_SLOPE20_TR_ID', 'J')):
            qM = RB.ns_pct(env, RB.raw_cells(env, pname, qm_id, qm_src), 'low_bad')
            r = env.cells_of_dense(RB.raw_cells(env, pname, 'J_B3C_REL_%s' % yn, 'J')); r = np.where(np.isfinite(r), r, 0.0)
            Jc = np.isfinite(qM) & np.isfinite(st.q0)
            rbar = np.bincount(ci.t[Jc], weights=r[Jc], minlength=T) / np.maximum(np.bincount(ci.t[Jc], minlength=T), 1)
            for a in (0.125, 0.25, 0.5):
                kR = st.kept(EN.blend(st.q0, [(1.0, qM[None, :])], a * r))[0]
                kD = st.kept(EN.blend(st.q0, [(1.0, qM[None, :])], a * np.where(Jc, rbar[ci.t], 0.0)))[0]
                nR = SE.pnl(ci.t[kR], ci.c[kR], SE.dev(ci.t[kR], ci.c[kR]), (5,), 8.0)[5][3]
                nD = SE.pnl(ci.t[kD], ci.c[kD], SE.dev(ci.t[kD], ci.c[kD]), (5,), 8.0)[5][3]
                sh = []
                V = Jc
                cell = ci.t[V].astype(np.int64) * 3 + np.maximum(oldk3[V], 0)
                for p in range(1024):
                    key = RND.path_key('E6j.B', 'r-shuffle|%s' % yn, mother, 'native', 'RSHUF', p)
                    u = env.grid.u_cells(key, ci.t[V], ci.c[V], 5)
                    rp = r.copy(); rp[V] = RND.assign_by_priority(r[V], cell, u)
                    kS = st.kept(EN.blend(st.q0, [(1.0, qM[None, :])], a * rp))[0]
                    sh.append(ann(SE.pnl(ci.t[kS], ci.c[kS], SE.dev(ci.t[kS], ci.c[kS]), (5,), 8.0)[5][3] - n0))
                sh = np.array(sh)
                out.append(dict(segment=pname, mother=mother, slot='K', measurement_id='J_B3C_REL_%s' % yn, direction='low_bad', alpha=a, H=5,
                                diag='DOSE', reliable_minus_parent=ann(nR - n0), common_dose_minus_parent=ann(nD - n0),
                                rshuffle_mean_minus_parent=float(sh.mean()), rshuffle_mcse=float(sh.std(ddof=1) / np.sqrt(len(sh))),
                                reliable_minus_common_dose=ann(nR - nD), mean_alpha_eff=float(np.mean(a * r[Jc])) if Jc.any() else np.nan))
    od = os.path.join(OUT, pname); os.makedirs(od, exist_ok=True)
    p = os.path.join(od, '%s.csv' % mother); J.atomic_write_csv(p, pd.DataFrame(out))
    J.write_receipt('diag_b_%s_%s' % (pname, mother), [p], 'SUCCEEDED', n=len(out), wall_s=round(time.time() - t0, 1))
    return 0


def _dense(env, cells_vals):
    ci = env.ci
    D = np.full((ci.T, ci.Nc), np.nan); D[ci.t, ci.c] = cells_vals
    return D


def _dense_b(env, cells_bool):
    ci = env.ci
    D = np.zeros((ci.T, ci.Nc), bool); D[ci.t[cells_bool], ci.c[cells_bool]] = True
    return D


def transport_cells(env, q0c, neu_cache, direction):
    """单元坐标的 TRANSPORT：逐日在 J（新残差有效 ∩ q0 有效）内把 q0 的有序值按新坏度次序分配；平局取均值；J 外保留 q0。"""
    ci, S = env.ci, env.S
    out = q0c.copy()
    colpos = S.ccolpos
    for t, d in enumerate(S.dates):
        s = neu_cache.get(d)
        if s is None:
            continue
        sl = np.flatnonzero(ci.t == t)
        pos = {c: i for i, c in enumerate(ci.c[sl])}
        idx = np.fromiter((pos.get(colpos.get(x, -1), -1) for x in s.index), int, len(s))
        ok = idx >= 0
        cells = sl[idx[ok]]; vals = s.to_numpy()[ok]
        m = np.isfinite(q0c[cells])
        cells, vals = cells[m], vals[m]
        if not len(cells):
            continue
        bad = vals if direction == 'high_bad' else -vals
        old_sorted = np.sort(q0c[cells], kind='mergesort')
        order = np.argsort(bad, kind='mergesort')
        v = np.empty(len(order)); v[order] = old_sorted
        v = pd.Series(v).groupby(bad).transform('mean').to_numpy()
        out[cells] = v
    return out


if __name__ == '__main__':
    a = sys.argv
    sys.exit(run(a[a.index('--segment') + 1], a[a.index('--mother') + 1]))
