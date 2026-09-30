# -*- coding: utf-8 -*-
"""E6l 固定输出（plan §13.4 十五张 + brief §9 追加五张）→ results/full/<表>.csv（骨架表头见 results/skeleton/）。seal_deriv + seal_post 与
政策 / 统计之后运行；--memory 先算记忆年龄（逐日门层重跑，一段一个进程）。每张表带 query_id 列。
  source_lineage / kernel_contracts / memory_contracts / hypothesis_lineage / candidate72 / dose72 / comparison_manifest / policy_profiles /
  memory_age_daily / state_clock_ledger / turn_cost_frontier / risk_tight_bounds / random_refs / mc_precision / completion_coverage /
  paired_mde80_deriv / state_unknown_days / inventory_saturation / membership_age_ledger / frontier_dose_tilt"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import json
import shutil
import argparse

import numpy as np
import pandas as pd

import e6l_core as L
import e6l_registry as RG

FULL = ('results', 'full')


def memory_age(pname):
    """主展示记忆对象（HG10 / LAG1_10 / DECAY5_10 / INV10 与 Q_D5 / Q_RANK5 / Q_DEW5 的 HG10）：逐日靠 bonus 续选份额、连续依靠日数与重确认年龄。"""
    import e6l_env as V
    import e6l_ops as O
    import e6l_run_det as RD
    if pname in L.POST_SEGS:
        L.post_gate(pname, 'memory age')
    seg = V.SegL(pname)
    D = L.read_csv_keep(L.P('registry', 'descriptors_E6l.csv'))
    P = D[(D.primary72.astype(str) == 'True') & (D.op != 'NATIVE')]
    rows, ages = [], []
    dates = [str(x)[:10] for x in seg.dates]
    for r in P.itertuples():
        st = seg.struct(r.mother)
        ctx = RD.DetCtx(seg, st, st.q0, seg.meas_kf(r.meas), r.meas)
        a = float(r.alpha)
        sc, U = ctx.sc(a), ctx.U(a)
        rule = O.parse_op(r.op)
        if rule['kind'] == 'INV':
            G, F, _, _ = O.inv_path(st, sc[None, :], U[None, :], rule['b'], int(r.H))
        else:
            G, _, _ = O.mem_gate(st, sc[None, :], U[None, :], rule, b_day=ctx.b_day(rule))
        G = G[0]
        dom = st.dom
        cols = seg.ci.c[st.ids]
        run = np.zeros(seg.Nc, np.int64)
        age = np.full(seg.Nc, -1, np.int64)
        hist = np.zeros(6, np.int64)
        for d in range(seg.T):
            a0, b0 = dom.off[d], dom.off[d + 1]
            if b0 == a0 or dom.K[d] == 0:
                run[:] = 0
                age[:] = -1
                continue
            cc = cols[a0:b0]
            g, u = G[a0:b0], U[a0:b0]
            rel = g & ~u
            nr = np.zeros(seg.Nc, np.int64)
            nr[cc[rel]] = run[cc[rel]] + 1
            run = nr
            na = np.full(seg.Nc, -1, np.int64)
            na[cc[u]] = 0
            keep = g & ~u & (age[cc] >= 0)
            na[cc[keep]] = age[cc[keep]] + 1
            age = na
            ng = int(g.sum())
            if ng:
                ag = age[cc[g]]
                rows.append(dict(segment=pname, target_id=r.target_id, date=dates[d], reliant_share=float(rel.sum() / ng),
                                 reliant_run_mean=float(run[cc[rel]].mean()) if rel.any() else 0.0,
                                 confirm_age_mean=float(ag[ag >= 0].mean()) if (ag >= 0).any() else np.nan, query_id='E6L-Q06-b'))
                b = np.clip(np.where(ag < 0, 5, ag), 0, 5)
                hist += np.bincount(np.minimum(b, 5), minlength=6)[:6]
        tot = max(int(hist.sum()), 1)
        for i, lab in enumerate(('0', '1', '2', '3', '4', '5+_or_unconfirmed')):
            ages.append(dict(segment=pname, target_id=r.target_id, age_bucket=lab, cells=int(hist[i]), share=float(hist[i] / tot), query_id='E6L-Q06-b'))
    od = L.P('results', 'full', 'memory_age')
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, '%s_daily.csv' % pname)
    p2 = os.path.join(od, '%s_ages.csv' % pname)
    L.atomic_write_csv(p1, pd.DataFrame(rows))
    L.atomic_write_csv(p2, pd.DataFrame(ages))
    L.write_receipt(L.next_rerun('memory_age_%s' % pname), [p1, p2], 'SUCCEEDED', rows=len(rows))
    print('%s memory age %d 行' % (pname, len(rows)), flush=True)
    return 0


def build():
    out = {}
    D = L.read_csv_keep(L.P('registry', 'descriptors_E6l.csv'))
    P = pd.read_csv(L.P(*FULL, 'policy_E6l.csv'), keep_default_na=False, na_values=[''])
    sm = json.load(open(L.P('source_manifest.json'), encoding='utf-8'))
    base = sm['readonly_code_sha256']
    src = [('Q0 测量', 'e6j_features.b1', 'e6j_features.py', ':120', 'e6j_slot.neu_of → pct_dir(lo)', 'EPS 1e−4', 'Stage 0 A3-1 / A4-3'),
           ('源中性化', 'pool_screening_v2.neutralize_by_mcap', 'pool_screening_v2.py', ':292', 'precompute_neutralized_factor :315', '有效 < 10 原值直返', 'A3-11'),
           ('门 / 合法域', 'e6k_env.Struct', 'e6k_env.py', ':145', 'gate_scores / gate_keep / down / legal', 'bunit 1/(100·nlegs)', 'A3-12'),
           ('KeepDom', 'e6i_randoms.KeepDom.keep', 'e6i_randoms.py', ':165', '逐日 stable argsort 前 K', 'k_of qcut 前缀', 'fast_identity'),
           ('A4b 第二关', 'e6i_randoms.dep_stage2_keep', 'e6i_randoms.py', ':187', 'Struct.down', 'k_of(ng, b)', 'fast_identity'),
           ('HG', 'e6k_ops.hg_gate', 'e6k_ops.py', ':185', 'e6l_ops.mem_gate(HG) 逐位', 'hold_init False', 'fast_identity / trial'),
           ('DEV', 'e6i_sparse.SparseEngine.dev', 'e6i_sparse.py', ':61', 'export_delivery_pools_v2.assign_weights_dev :71', 'w0 = min(1/n, 1%)', 'fast_identity'),
           ('账本', 'e6i_sparse.SparseEngine.pnl', 'e6i_sparse.py', ':85', 'compute_calendar_pnl :488', '8bp；T+1 VWAP', 'A2-2'),
           ('同资本', 'e6k_acct.Acct.ledgers', 'e6k_acct.py', ':45', 'sc_child / sc_parent', 'MATCH_CAP_FIXED_PATH', 'A2-4'),
           ('紧区间', 'e6k_acct.Acct.target_stats', 'e6k_acct.py', ':127', 'szT_lo / szT_hi', '×100', 'A2-7'),
           ('随机 LEGACY', 'e6k_random.Legacy', 'e6k_random.py', ':71', 'e6j_random.path_key :27', 'E6j.P / E6j.B', 'A2-6'),
           ('随机 COND', 'e6k_random.NewCond', 'e6k_random.py', ':174', 'tree_leaves :129', 'ISK 块 5', 'A2-6'),
           ('全程缓存', 'e6f_core.guarded_load', 'e6f_core.py', ':56', 'e6l_state.load_full', 'E7 守卫在前', 'A1-5 / A4-1')]
    out['source_lineage'] = pd.DataFrame([dict(object_id=a, source_function=b, source_file=c, source_sha256=base.get(c, 'NOT_IN_BASELINE')[:16], call_site=d + '；' + e,
                                                 default=f, evidence=g, query_id='E6L-Q01-a') for a, b, c, d, e, f, g in src])
    mfd = [pd.read_csv(f, keep_default_na=False, na_values=['']) for f in glob.glob(L.P('results', 'stage_a', 'measure_facts_*_E6l.csv'))]
    MF = pd.concat(mfd, ignore_index=True) if mfd else pd.DataFrame()
    kc = D.drop_duplicates('meas')[['meas', 'kernel_id', 'kernel_window', 'kernel_min_valid', 'kernel_lambda']]
    if len(MF) and 'meas_valid_share_pool0' in MF.columns:
        g = MF.groupby(['segment', 'meas'])[[c for c in ('meas_valid_share_pool0', 'meas_kf_finite_share') if c in MF.columns]].first().reset_index()
        kc = kc.merge(g, on='meas', how='left')
    kc['query_id'] = 'E6L-Q03-a'
    out['kernel_contracts'] = kc
    mc = D.drop_duplicates('op')[['op', 'memory_rule', 'memory_kind', 'b_points', 'inv_state_key']].copy()
    mc['checkpoint_fields'] = np.where(mc.op == 'INV10', 'next_day|next_date|ids|H|cnt|ring', np.where(mc.op == 'NATIVE', 'NOT_APPLICABLE', 'next_day|next_date|ids|G|U|last'))
    mc['query_id'] = 'E6L-Q06-a'
    out['memory_contracts'] = mc
    hl = L.read_csv_keep(L.P('registry', 'hypothesis_lineage_E6l.csv'))
    out['hypothesis_lineage'] = hl.assign(query_id=hl.outcome_query.str.split('|').str[0])
    pcols = ['desc_id', 'recipe', 'mother', 'alpha', 'FULL', 'G4', 'FULL_sc', 'G4_sc', 'FULL_imp'] + ['D_%s' % s for s in L.SEGMENTS] + \
            ['policy_%s_%s' % (p, a) for p in ('PROPOSED_PORT3_T', 'LEGACY_EDIT5', 'PROPOSED_PORT3_LAG1', 'EXEC_DISCLOSE_ONLY') for a in ('FULL', 'G4')] + \
            ['size_EXEC_LEADER_VS_PARENT', 'e_rand', 'e_cap_FULL', 'years_pos', 'evidence_exposure']
    for nm, col in (('candidate72', 'primary72'), ('dose72', 'dose72')):
        x = P[P[col].astype(str) == 'True'][[c for c in pcols if c in P.columns]].rename(columns={'FULL': 'FULL_ann_pp', 'G4': 'G4_ann_pp', 'FULL_sc': 'FULL_sc_ann_pp'})
        x['query_id'] = 'E6L-Q01-b' if nm == 'candidate72' else 'E6L-Q11-a'
        out[nm] = x
    out['policy_profiles'] = pd.concat([P[['desc_id', 'policy_%s_%s' % (p, a)]].rename(columns={'policy_%s_%s' % (p, a): 'verdict'}).assign(profile=p, aggregation=a)
                                        for p in ('PROPOSED_PORT3_T', 'LEGACY_EDIT5', 'PROPOSED_PORT3_LAG1', 'EXEC_DISCLOSE_ONLY') for a in ('FULL', 'G4')],
                                       ignore_index=True).assign(query_id='E6L-Q01-b')
    md = [pd.read_csv(f, keep_default_na=False, na_values=['']) for f in sorted(glob.glob(L.P('results', 'full', 'memory_age', '*_daily.csv')))]
    out['memory_age_daily'] = pd.concat(md, ignore_index=True) if md else pd.DataFrame()
    ma = [pd.read_csv(f, keep_default_na=False, na_values=['']) for f in sorted(glob.glob(L.P('results', 'full', 'memory_age', '*_ages.csv')))]
    out['membership_age_ledger'] = pd.concat(ma, ignore_index=True) if ma else pd.DataFrame()
    scl = L.P(*FULL, 'state_clock_ledger.csv')
    if os.path.exists(scl):
        out['state_clock_ledger'] = pd.read_csv(scl, keep_default_na=False, na_values=[''])
    S = pd.concat([pd.read_csv(L.P(*FULL, 'descriptor_stats_%s.csv' % s), keep_default_na=False, na_values=['']) for s in L.SEGMENTS], ignore_index=True)
    fr = S[S.kind == 'registered'][['segment', 'desc_id', 'gross_ann', 'turn_mean_decimal', 'net8_ann', 'D', 'D_gross', 'turn_rel']].copy()
    fr = fr.rename(columns={'gross_ann': 'gross_ann_pp', 'net8_ann': 'net8_ann_pp', 'turn_mean_decimal': 'charged_turn_decimal', 'D': 'D_net8_ann_pp', 'D_gross': 'D_gross_ann_pp'})
    fr['fee_diff_ann_pp'] = fr.D_net8_ann_pp - fr.D_gross_ann_pp
    with np.errstate(all='ignore'):
        dturn = -fr.fee_diff_ann_pp / (8e-4 * L.ANN)                    # 子 − 父 的日均收费换手差（decimal）
        fr['c_star_bp'] = np.where(np.abs(dturn) > 1e-12, fr.D_gross_ann_pp / L.ANN / dturn * 1e4, np.nan)
    fr['c_star_note'] = np.where(np.abs(dturn) > 1e-12, 'c* = ΔG / ΔT（与原父，收费单位 bp；负值 / 量级失真单列，不作实际费用预测）', 'UNDEFINED（ΔT = 0）')
    fr['query_id'] = 'E6L-Q02-b'
    out['turn_cost_frontier'] = fr
    rt = S[S.kind == 'registered'][['segment', 'desc_id', 'port_size_lo_T', 'port_size_hi_T']].rename(columns={'port_size_lo_T': 'port_size_lo_T_segavg_pct_pt',
                                                                                                           'port_size_hi_T': 'port_size_hi_T_segavg_pct_pt'})
    rt['status'] = np.where(rt.port_size_lo_T_segavg_pct_pt.isna(), 'UNDEFINED', np.where((rt.port_size_lo_T_segavg_pct_pt >= -3) & (rt.port_size_hi_T_segavg_pct_pt <= 3), 'PASS',
                            np.where((rt.port_size_hi_T_segavg_pct_pt < -3) | (rt.port_size_lo_T_segavg_pct_pt > 3), 'FAIL', 'SIZE_PARTIALLY_IDENTIFIED')))
    rt['query_id'] = 'E6L-Q11-a'
    out['risk_tight_bounds'] = rt
    R = pd.concat([pd.read_csv(L.P(*FULL, 'random_refs_%s.csv' % s), keep_default_na=False, na_values=['']).assign(segment=s) for s in L.SEGMENTS], ignore_index=True)
    out['random_refs'] = R.rename(columns={'rand_mean': 'rand_mean_ann_pp', 'rand_sd': 'rand_sd_ann_pp', 'mcse': 'mcse_ann_pp', 'real_minus_rand': 'real_minus_rand_ann_pp',
                                           'n': 'n_paths'}).assign(query_id='E6L-Q10-a')
    mcr = []
    for s in L.SEGMENTS:
        phase = 'deriv' if s in L.DERIV_SEGS else 'post'
        fs = sorted(glob.glob(L.P('results', phase, 'mc_plan_%s_*.csv' % s)), key=os.path.getmtime)
        if fs:
            x = pd.read_csv(fs[-1])
            x['status'] = np.where(x.worst_mcse <= 0.03, 'MCSE_LE_0.03', np.where(x.have >= 8192, 'CAP_8192', 'MC_UNRESOLVED'))
            mcr.append(x.rename(columns={'worst_mcse': 'worst_mcse_ann_pp', 'have': 'n_paths'}).assign(target_mcse_ann_pp=0.03, query_id='E6L-Q10-a'))
    out['mc_precision'] = pd.concat(mcr, ignore_index=True) if mcr else pd.DataFrame()
    cov = []
    A = L.read_csv_keep(L.P('registry', 'accessory_E6l.csv'))
    for s in L.SEGMENTS:
        ss = S[S.segment == s]
        for b in ('CORE', 'CONTROL', 'MEMORY', 'STATE', 'OLD_RULE', 'BRIDGE', 'EDGE', 'EDGE_OLD'):
            ids = set(D[D.blocks.str.contains(b)].desc_id)
            got = len(ids & set(ss.desc_id))
            cov.append(dict(segment=s, block=b, registered=len(ids), computed=got, status='COMPLETE' if got == len(ids) else 'INCOMPLETE', query_id='E6L-Q16-a'))
        for k in sorted(A.kind.unique()):
            if k in ('BOUNDARY_CONT_PARENT_PAIR', 'BOUNDARY_CONT_PARENT', 'INV_CAP_LOOP_PARENT'):
                continue
            ids = set(A[A.kind == k].acc_id)
            got = len(ids & set(ss.desc_id))
            cov.append(dict(segment=s, block=k, registered=len(ids), computed=got, status='COMPLETE' if got == len(ids) else 'INCOMPLETE', query_id='E6L-Q16-a'))
        rr = R[R.segment == s]
        for m in rr.mechanism.unique():
            reg_n = int(len(pd.read_csv(L.P('registry', 'randoms_E6l.csv'), usecols=['mechanism']).query('mechanism == @m')))
            got = int(rr[rr.mechanism == m].groupby(['desc_id', 'H']).ngroups)
            cov.append(dict(segment=s, block='RANDOM_' + m, registered=reg_n, computed=got, status='COMPLETE' if got == reg_n else 'INCOMPLETE', query_id='E6L-Q16-a'))
    out['completion_coverage'] = pd.DataFrame(cov)
    shutil.copyfile(L.P('results', 'deriv', 'paired_mde80_deriv.csv'), L.P(*FULL, 'paired_mde80_deriv.csv.tmp'))
    os.replace(L.P(*FULL, 'paired_mde80_deriv.csv.tmp'), L.P(*FULL, 'paired_mde80_deriv.csv'))
    su = [pd.read_csv(L.P('stage0', 'c4_data', 'state_unknown_days.csv'), keep_default_na=False, na_values=[''])]
    out['state_unknown_days'] = su[0]
    MFa = pd.concat([pd.read_csv(f, keep_default_na=False, na_values=['']) for f in glob.glob(L.P('results', 'stage_a', 'mask_facts_*_E6l.csv'))], ignore_index=True)
    inv = MFa[MFa.op == 'INV10'][['segment', 'target_id', 'inv_H', 'inv_mark_coverage', 'inv_saturated_day_share', 'pending_expiry_overlap', 'variant']].rename(
        columns={'inv_H': 'H', 'inv_mark_coverage': 'mark_coverage', 'inv_saturated_day_share': 'saturated_day_share'})
    inv['query_id'] = 'E6L-Q08-b'
    out['inventory_saturation'] = inv
    ft = P[(P.meas == 'Q0') & P.op.isin(['NATIVE', 'HG5', 'HG10', 'HG15', 'HG20', 'HG30']) & (P.H.astype(int) == 5)].copy()
    ft['b'] = ft.op.str.replace('NATIVE', '0').str.replace('HG', '').astype(int)
    rows = []
    for r in ft.to_dict('records'):
        for s in L.SEGMENTS:
            lo, hi = float(r.get('port_size_lo_T_%s' % s, np.nan)), float(r.get('port_size_hi_T_%s' % s, np.nan))
            rows.append(dict(segment=s, recipe='Q0:%s' % r['op'], mother=r['mother'], alpha=r['alpha'], b=r['b'], FULL_ann_pp=r['FULL'],
                             port_size_mid_T_pct_pt=0.5 * (lo + hi) if np.isfinite(lo) and np.isfinite(hi) else np.nan, query_id='E6L-Q11-a'))
    out['frontier_dose_tilt'] = pd.DataFrame(rows)
    for nm, df in out.items():
        L.atomic_write_csv(L.P(*FULL, '%s.csv' % nm), df)
    cm = L.P(*FULL, 'comparison_manifest.csv')
    shutil.copyfile(L.P('registry', 'comparison_manifest_E6l.csv'), cm + '.tmp')
    os.replace(cm + '.tmp', cm)
    fixed = [L.P(*FULL, '%s.csv' % n) for n in list(out) + ['paired_mde80_deriv', 'comparison_manifest']]
    L.write_receipt(L.next_rerun('fixed_tables'), fixed, 'SUCCEEDED', tables=len(fixed))
    print('固定表 %d 张' % len(fixed), flush=True)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--memory', default=None)
    a = ap.parse_args()
    if a.memory:
        return memory_age(a.memory)
    return build()


if __name__ == '__main__':
    sys.exit(main())
