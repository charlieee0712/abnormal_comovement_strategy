# -*- coding: utf-8 -*-
"""E6j 提速件逐位等价测试（真实数据；不写结果、只写 checks/fast_equivalence_<段>_<部分>.csv 与回执）：
  --part P  --segment S  六形态 × 四臂 × 七机制 × 三 α × 路径 {0, 5, 1023}：新 Perm.draw 与原 assign_by_priority 逐值相同；
            多路径批的结构算子掩码（第二关 stage2_fast vs IR.dep_stage2_keep）逐格相同；EDIT / EDIT_IID / EDITB 新计划 vs 原 edit_masks 逐格相同
  --part B  --segment S  R1(K) / R1(T) / R2 / A06 / A08 / B3C 首组 × 三机制 × 全部组合 × 路径 {0, 7}：DonorMapper vs donor_map 逐值、
            子掩码逐格相同（第二关同上），EDIT 新计划 vs 原 edit_entry 逐格相同
任何不同即 FAIL（不设容差）。"""
import e6j_boot  # noqa: F401
import os
import sys
import time

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_prod as P
import e6j_slot as SL
import e6j_engine as EN
import e6j_random as RND
import e6j_fast as FAST
import e6j_run_prand as RR
import e6j_run_b as RB
import e6j_run_brand as RBR

rows_out = []


def check(part, what, ok, detail=''):
    rows_out.append(dict(part=part, what=what, status='PASS' if ok else 'FAIL', detail=str(detail)[:300]))


def kept_both(st, Q):
    EN.STAGE2 = None
    k_old = st.kept(Q)
    EN.STAGE2 = FAST.stage2_fast
    k_new = st.kept(Q)
    return k_old, k_new


def draw_ref(perm, mech, path):
    """原单分量抽取（assign_by_priority）；SM 走原共享 donor 代码（未改）。"""
    env, ci = perm.env, perm.env.ci
    names = list(perm.comps)
    if len(names) == 2:
        return perm.draw(mech, path)
    bd = 1 if mech in ('IID', 'COND_IID') else 5
    k = names[0]
    v = perm.valid[k]; vals = perm.comps[k][v]
    cell = (perm.cond[k][0] if mech.startswith('COND') else perm.day[k])[v]
    key = RND.path_key('E6j.P', RR.COMP_ID.get(k, k), 'P_production_v2', 'native', mech, path)
    u = env.grid.u_cells(key, ci.t[v], ci.c[v], bd)
    o = np.full(ci.n, np.nan); o[v] = RND.assign_by_priority(vals, cell, u)
    return {k: o}


def part_P(seg, forms, arms, paths):
    env = EN.Env(seg, with_prod=True)
    ctx, ci = env.ctx, env.ci
    for form in forms:
        EN.STAGE2 = None
        st = EN.prod_structure(env, form)
        parent = st.kept(st.q0[None, :])[0]
        legal = ~env.cvr if form.endswith('_CVRv5') else np.ones(ci.n, bool)
        for arm in arms:
            t0 = time.time()
            names = [m for _, m in RR.ARMS[arm]]
            comps = {k: env._dense_cells(SL.member_pct(ctx, *RR.COMP[k])[0]) for k in names}
            perm = RR.Perm(env, comps, env.pK)
            EN.STAGE2 = None
            real = {a: st.kept(EN.blend(st.q0, [(sh, comps[m][None, :]) for sh, m in RR.ARMS[arm]], a))[0] for a in RR.ALPHAS}
            plans = RR.edit_plans(env, parent, real, legal, env.pK, form)
            pl0 = plans[RR.ALPHAS[0]]
            nbad_draw = nbad_mask = nbad_edit = ncmp = 0
            for mech in RR.MECHS:
                if mech.startswith('EDIT'):
                    for p in paths:
                        if mech in ('EDIT', 'EDIT_IID'):
                            bd = 1 if mech == 'EDIT_IID' else 5
                            u = env.grid.u_cells(RND.path_key('E6j.P', 'EDIT-ENTRY', form, 'native', mech, p), pl0.cand_rc[0], pl0.cand_rc[1], bd)
                        else:
                            uo = env.grid.u_cells(RND.path_key('E6j.P', 'EDIT-BOTH:out', form, 'native', mech, p), pl0.par_rc[0], pl0.par_rc[1], 5)
                            ui = env.grid.u_cells(RND.path_key('E6j.P', 'EDIT-BOTH:in', form, 'native', mech, p), pl0.cand_rc[0], pl0.cand_rc[1], 5)
                        for a in RR.ALPHAS:
                            k_old = RR.edit_masks(env, parent, real[a], legal, env.pK, mech, p, form)
                            k_new = plans[a].entry(u) if mech != 'EDITB' else plans[a].both(uo, ui)
                            nbad_edit += int((k_old != k_new).sum()); ncmp += 1
                else:
                    DV = []
                    for p in paths:
                        d_old, d_new = draw_ref(perm, mech, p), perm.draw(mech, p)
                        nbad_draw += sum(int((~((d_old[k] == d_new[k]) | (np.isnan(d_old[k]) & np.isnan(d_new[k])))).sum()) for k in d_old)
                        DV.append(d_new)
                    for a in RR.ALPHAS:
                        Q = np.vstack([EN.blend(st.q0, [(sh, dv[m][None, :]) for sh, m in RR.ARMS[arm]], a) for dv in DV])
                        k_old, k_new = kept_both(st, Q)
                        nbad_mask += int((k_old != k_new).sum()); ncmp += 1
            check('P', '%s %s %s：draw / 掩码 / EDIT 逐格' % (seg, form, arm), nbad_draw == 0 and nbad_mask == 0 and nbad_edit == 0,
                  'draw 不同 %d；结构掩码不同 %d；EDIT 不同 %d；比较 %d 组；%.0fs' % (nbad_draw, nbad_mask, nbad_edit, ncmp, time.time() - t0))
            print(rows_out[-1], flush=True)


def part_B(seg, cfgs, paths):
    env = EN.Env(seg, with_prod=False)
    ci = env.ci
    ind = np.asarray(env.S.icodes)
    lm = env.S.log_mcap.reindex(index=env.S.pool0.index, columns=env.S.pool0.columns).values[:, env.S.ccols]
    reg = pd.read_csv(os.path.join(J.RES, 'registry', 'rows_B.csv'))
    for mother, block in cfgs:
        t0 = time.time()
        rows = reg[(reg.block == block) & reg.mothers.str.split('|').apply(lambda m: mother in m)]
        if not len(rows):
            check('B', '%s %s %s' % (seg, mother, block), False, '无登记行'); continue
        (slot, mid), grp = next(iter(rows.groupby(['slot', 'measurement_id'], sort=True)))
        EN.STAGE2 = None
        st = EN.research_structure(env, mother, slot)
        parent = st.kept(st.q0[None, :])[0]; legal = ~st.drop
        if block == 'B3C':
            yn = mid.split('_')[-1]
            qm_id, qm_src = ('K_slope20', 'E6I') if yn == 'CC' else ('J_B2_SLOPE20_TR_ID', 'J')
            zc = {'low_bad': RB.ns_pct(env, RB.raw_cells(env, seg, qm_id, qm_src), 'low_bad')}
            zhi = 1.0 - zc['low_bad']
            r = env.cells_of_dense(RB.raw_cells(env, seg, mid, 'J')); r = np.where(np.isfinite(r), r, 0.0)
        else:
            raw = RB.raw_cells(env, seg, mid, grp.source.iloc[0])
            if mother == 'R1' and slot == 'T':
                zc = {d: RB.s1_pct(env, raw, d) for d in grp.direction.unique()}
                zhi = RB.s1_pct(env, raw, 'high_bad') if 'high_bad' not in zc else zc['high_bad']
            else:
                cache = RB.ns_cache(env, raw)
                zc = {d: RB.pct_of(env, cache, d) for d in grp.direction.unique()}
                zhi = zc['high_bad'] if 'high_bad' in zc else RB.pct_of(env, cache, 'high_bad')
            r = None
        V = np.isfinite(zhi); vt, vc = ci.t[V], ci.c[V]
        Vd = np.zeros((ci.T, ci.Nc), bool); Vd[vt, vc] = True
        oldk = np.full((ci.T, ci.Nc), np.nan); oldk[ci.t, ci.c] = st.q0
        rr_, cc_, cell, _ = RND.cond_cells(Vd, ind, lm, oldk)
        cid = np.full((ci.T, ci.Nc), -1, np.int64); cid[rr_, cc_] = cell
        cond_cell = cid[vt, vc]
        combos = [(row.direction, a) for _, row in grp.iterrows() for a in RBR.ALPHAS]
        real = {}
        for (d, a) in combos:
            aa = a * r if r is not None else a
            real[(d, a)] = st.kept(EN.blend(st.q0, [(1.0, zc[d][None, :])], aa))[0]

        def dense_b(b):
            A = np.zeros((ci.T, ci.Nc), bool); A[ci.t[b], ci.c[b]] = True
            return A
        Pd, Ld = dense_b(parent), dense_b(legal)
        k3 = RND.terciles_rowwise(oldk, Ld)
        mapper = {'IID': FAST.DonorMapper(zhi[V], vt.astype(np.int64)), 'COND': FAST.DonorMapper(zhi[V], cond_cell)}
        plans = {k: FAST.EditPlan(ci, ind, k3, parent, v, legal) for k, v in real.items()}
        pl0 = plans[combos[0]]
        nbad_don = nbad_mask = nbad_edit = ncmp = 0
        for mech in RBR.MECHS:
            if mech == 'EDIT':
                for p in paths:
                    key = RND.path_key('E6j.B', 'EDIT-ENTRY', mother, 'native', 'EDIT', p)
                    u = env.grid.u_cells(key, pl0.cand_rc[0], pl0.cand_rc[1], 5)
                    for combo in combos:
                        m_old, _ = RND.edit_entry(Pd, dense_b(real[combo]), Ld, env.grid, key, ind, oldk, 5, k3=k3)
                        nbad_edit += int((m_old[ci.t, ci.c] != plans[combo].entry(u)).sum()); ncmp += 1
            else:
                bd = 1 if mech == 'IID' else 5
                cl = vt.astype(np.int64) if mech == 'IID' else cond_cell
                DON = []
                for p in paths:
                    u = env.grid.u_cells(RND.path_key('E6j.B', mid, mother, 'native', mech, p), vt, vc, bd)
                    d_old, d_new = RBR.donor_map(zhi[V], cl, u), mapper[mech](u)
                    nbad_don += int((d_old != d_new).sum()); DON.append(d_new)
                for (d, a) in combos:
                    aa = a * r if r is not None else a
                    Q = []
                    for don in DON:
                        zp = np.full(ci.n, np.nan); zp[V] = zc[d][V][don]
                        Q.append(EN.blend(st.q0, [(1.0, zp[None, :])], aa)[0])
                    k_old, k_new = kept_both(st, np.vstack([q[None, :] for q in Q]))
                    nbad_mask += int((k_old != k_new).sum()); ncmp += 1
        check('B', '%s %s %s %s %s：donor / 掩码 / EDIT 逐格' % (seg, mother, block, slot, mid), nbad_don == 0 and nbad_mask == 0 and nbad_edit == 0,
              'donor 不同 %d；结构掩码不同 %d；EDIT 不同 %d；比较 %d 组；%.0fs' % (nbad_don, nbad_mask, nbad_edit, ncmp, time.time() - t0))
        print(rows_out[-1], flush=True)


if __name__ == '__main__':
    a = sys.argv
    seg, part = a[a.index('--segment') + 1], a[a.index('--part') + 1]
    if part == 'P':
        forms = a[a.index('--forms') + 1].split(',') if '--forms' in a else list(P.DELIV)
        part_P(seg, forms, list(RR.ARMS), [0, 5, 1023])
    else:
        part_B(seg, [('R1', 'B1'), ('R1', 'B6'), ('R2', 'B2'), ('A06', 'B4'), ('A08', 'B6'), ('R2', 'B3C')], [0, 7])
    df = pd.DataFrame(rows_out)
    tag = '%s_%s' % (seg, part) + ('_' + a[a.index('--forms') + 1].replace(',', '+') if '--forms' in a else '')
    p = os.path.join(J.RES, 'checks', 'fast_equivalence_%s.csv' % tag)
    J.atomic_write_csv(p, df)
    ok = bool((df.status == 'PASS').all())
    J.write_receipt('fast_equivalence_%s' % tag, [p], 'SUCCEEDED' if ok else 'FAILED', all_pass=ok, n=len(df))
    print(df.to_string())
    sys.exit(0 if ok else 1)
