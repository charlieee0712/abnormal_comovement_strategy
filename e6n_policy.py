# -*- coding: utf-8 -*-
"""E6n 政策评分、实质改善表、前沿表（brief §6、W11；plan §12.1；registration/policy_profiles_E6n.json）。
判定函数沿 E6l，只 import 不改：e6l_policy.tri_sign / e_rand / size_status / verdict / DELTAS / VERDICT_PROFILES / MC_Z（E6m e6m_s_policy 同式）。
- 判定串 c、d、f、正向门槛、e资本、e随机、size(profile)；四个 verdict profile × {FULL, G4}；EXEC_LEADER_VS_PARENT 只披露。
- e随机（原资格项）= LEGACY_POLICY_RANDOM：新对象取本轮 random_refs；锚对象（Q0 / C1，E6m 同对象）取 E6m random_refs 同 ID（A2-6 已逐路径复现）。
  新增内容随机（IID / ISK / QRANGE / R_MEMORY）只作披露列 diag_<机制>_post（两后段 rmr ≥ 2·MCSE 三态），不进判定、不新增门。
- POLICY_UNDECIDABLE_HISTORY（plan §12.1）：分钟成员在分钟未覆盖的段 / 年（2010-2014 段覆盖 < .9；年覆盖 < .9）上，c / d 若只能靠回源 Q0 的日子才"过"，
  标不可判（已在已覆盖部分失败者照常不通过）；另出可用期研究表（只报数，不给通过）。
- 实质改善表：对当前 Q0 HG10 / LAG1_10（同形态 / α / H）的 Δnet8（FULL / G4 / 段）、同资本、配对 se、支持、相对简单控制；与资格表分列。
- 前沿表：主 72 与全部新对象相对当前前沿 Q0|A4b_CVRv5|α.25|HG10|H5。全部 deployment_authorized = false；新对象 replacement_preference_status = NOT_AUTHORIZED。"""
import os
import sys
import json
import argparse

import numpy as np
import pandas as pd

import e6n_core as N

E6M_W = N.E6M_WORK
MINUTE_FEATS = ('PL_REL20', 'TAIL_PUSH', 'TAIL_VOL_REL20', 'JSD_PROFILE20', 'RV_REL20', 'Q_PATH', 'Q_CLOSE_THIN', 'Q_RV', 'Q_CLOSE_LEVEL', 'Q_BOTH')
RENAME = {'D_ann_pp': 'D', 'D_sc_ann_pp': 'D_sc', 'D_imp_ann_pp': 'D_imp', 'D_str_ann_pp': 'D_str', 'D_6bp_ann_pp': 'D_6bp', 'D_12bp_ann_pp': 'D_12bp',
          'D_gross_ann_pp': 'D_gross', 'port_size_lo_T_pct_pt': 'port_size_lo_T', 'port_size_hi_T_pct_pt': 'port_size_hi_T', 'port_size_lo_L_pct_pt': 'port_size_lo_L',
          'port_size_hi_L_pct_pt': 'port_size_hi_L', 'edit_gap_mean_T_pct_pt': 'edit_gap_mean_T', 'turn_rel_decimal': 'turn_rel', 'se_H_ann_pp': 'se_H',
          'se_2H_ann_pp': 'se_2H', 'net8_ann_pp': 'net8_ann', 'parent_net8_ann_pp': 'parent_net8_ann'}
KEYS = ('D', 'n', 'D_sc', 'D_imp', 'D_str', 'D_6bp', 'D_12bp', 'D_gross', 'edit_gap_absmean_T', 'edit_gap_mean_T', 'port_size_lo_T', 'port_size_hi_T',
        'port_size_lo_L', 'port_size_hi_L', 'lv5_mean', 'parent_lv5_mean', 'small30_delta', 'unkT_mean', 'turn_rel', 'se_H', 'se_2H', 'net8_ann', 'parent_net8_ann')


def coverage():
    """分钟覆盖：段份额与年份额（pool0 股票日，minute_present）。"""
    seg_cov, yr_cov = {}, {}
    for seg in N.SEGMENTS:
        p = np.load(N.P('meas', seg, 'col_minute_present.npy'))
        t = np.load(N.P('meas', seg, 'cells_t.npy'))
        d = np.load(N.P('meas', seg, 'dates.npy'))
        pres = p == 1
        seg_cov[seg] = float(pres.mean())
        y = d[t] // 10000
        for yy in np.unique(y):
            yr_cov[int(yy)] = float(pres[y == yy].mean())
    return seg_cov, yr_cov


def e6m_refs():
    out = {}
    for s in N.SEGMENTS:
        R = pd.read_csv(os.path.join(E6M_W, 'results', 'full', 'random_refs_%s.csv' % s), keep_default_na=False, na_values=[''])
        R = R[R.mechanism == 'LEGACY_POLICY_RANDOM']
        for r in R.itertuples():
            out[(r.desc_id, int(r.H), s)] = (float(r.real_minus_rand), float(r.mcse), int(r.n))
    return out


def e6m_id(did):
    import e6n_s0_anchor_acct as AA
    return AA.e6m_id(did)


def diag_state(rmr, mcse):
    if not (np.isfinite(rmr) and np.isfinite(mcse)):
        return 'MISSING'
    if rmr > 0 and rmr >= 2 * mcse:
        return 'POS'
    if rmr <= 0 and -rmr >= 2 * mcse:
        return 'NONPOS'
    return 'UNRES'


def main():
    from e6l_policy import tri_sign, e_rand, size_status, verdict, DELTAS, VERDICT_PROFILES, MC_Z
    import e6j_stats as ST
    import e6n_gate as GT
    ap = argparse.ArgumentParser()
    ap.add_argument('--stats', default='results/full')
    ap.add_argument('--out', default='results/full')
    a = ap.parse_args()
    for s in N.POST_SEGS:
        GT.post_gate(s, 'policy')
    sd = N.P(a.stats)
    od = N.P(a.out)
    D = pd.read_csv(N.P('registry', 'descriptors_E6n.csv'), keep_default_na=False)
    S = {}
    for s in N.SEGMENTS:
        x = pd.read_csv(os.path.join(sd, 'descriptor_stats_%s.csv' % s), keep_default_na=False, na_values=[''])
        x = x.rename(columns=RENAME)
        if 'edit_gap_mean_T' in x:
            x['edit_gap_absmean_T'] = x['edit_gap_mean_T'].abs()
        S[s] = x.set_index('desc_id')
    R = pd.read_csv(os.path.join(sd, 'random_refs.csv'), keep_default_na=False, na_values=[''])
    R = R[R.kind == 'OBJECT']
    refs = {m: g.set_index(['desc_id', 'segment']) for m, g in R.groupby('mechanism')}
    E6M = e6m_refs()
    seg_cov, yr_cov = coverage()
    rows = []
    for r in D[D.in_policy_table.astype(str) == 'True'].itertuples():
        minute = r.feature in MINUTE_FEATS
        row = dict(desc_id=r.desc_id, kind=r.kind, feature=r.feature, parent=r.parent, memory=r.memory, H=int(r.H), strength=r.strength, outer_alpha=r.outer_alpha,
                   applicability=r.applicability, frequency=r.frequency, direction=r.direction, is_primary72=r.is_primary72, primary_recipe=r.primary_recipe,
                   exposure=r.exposure, e_random_mechanism=r.e_random_mechanism, minute_member=minute)
        Ds, ns, Dsc, Dimp = [], [], [], []
        for s in N.SEGMENTS:
            x = S[s].loc[r.desc_id] if r.desc_id in S[s].index else None
            for k in KEYS:
                row['%s_%s' % (k, s)] = float(x[k]) if (x is not None and k in x.index and pd.notna(x[k])) else np.nan
            Ds.append(row['D_%s' % s])
            ns.append(row['n_%s' % s])
            Dsc.append(row['D_sc_%s' % s])
            Dimp.append(row['D_imp_%s' % s])
            if x is not None:
                for k in x.index:
                    if k.startswith('Y') and k.endswith('_ann_pp') and k[1:5].isdigit() and pd.notna(x[k]):
                        row['Y%s' % k[1:5]] = float(x[k])
            if r.kind == 'ANCHOR':
                e = E6M.get((e6m_id(r.desc_id), int(r.H), s))
                row['rmr_%s' % s], row['mcse_%s' % s], row['npaths_%s' % s] = e if e else (np.nan, np.nan, 0)
                row['e_random_source'] = 'E6m random_refs 同对象（SECOND_EVALUATION；A2-6 逐路径复现）'
            else:
                ref = refs.get('LEGACY_POLICY_RANDOM')
                if ref is not None and (r.desc_id, s) in ref.index:
                    lr = ref.loc[(r.desc_id, s)]
                    lr = lr.iloc[0] if isinstance(lr, pd.DataFrame) else lr
                    row['rmr_%s' % s], row['mcse_%s' % s], row['npaths_%s' % s] = float(lr.rmr), float(lr.mcse), int(lr.paths_run)
                else:
                    row['rmr_%s' % s], row['mcse_%s' % s], row['npaths_%s' % s] = np.nan, np.nan, 0
                row['e_random_source'] = '本轮 LEGACY_POLICY_RANDOM（对象自身 Q 槽 kf 当日 IID 置换）'
            for mech in ('CONTENT_IID', 'CONTENT_ISK_P5', 'CONTENT_QRANGE_P5', 'R_MEMORY'):
                ref = refs.get(mech)
                if ref is not None and (r.desc_id, s) in ref.index:
                    lr = ref.loc[(r.desc_id, s)]
                    lr = lr.iloc[0] if isinstance(lr, pd.DataFrame) else lr
                    row['diag_rmr_%s_%s' % (mech, s)], row['diag_mcse_%s_%s' % (mech, s)] = float(lr.rmr), float(lr.mcse)
        row['random_content'] = 'SCHEDULED' if (r.kind != 'ANCHOR' or np.isfinite(row.get('rmr_2019-2023', np.nan))) else 'RANDOM_NOT_SCHEDULED'
        for mech in ('CONTENT_IID', 'CONTENT_ISK_P5', 'CONTENT_QRANGE_P5', 'R_MEMORY'):
            st = [diag_state(row.get('diag_rmr_%s_%s' % (mech, s), np.nan), row.get('diag_mcse_%s_%s' % (mech, s), np.nan)) for s in N.POST_SEGS]
            row['diag_%s_post' % mech] = 'NOT_SCHEDULED' if all(x == 'MISSING' for x in st) else ('PASS' if all(x == 'POS' for x in st) else
                                                                                                      ('FAIL' if 'NONPOS' in st else 'MC_UNRESOLVED'))
        row['FULL'], row['G4'] = ST.full_g4(Ds, ns)
        row['FULL_sc'], row['G4_sc'] = ST.full_g4(Dsc, ns)
        row['FULL_imp'], row['G4_imp'] = ST.full_g4(Dimp, ns)
        for dl in DELTAS:
            tag = 'd%02d' % int(round(dl * 100))
            row['c_%s' % tag] = bool(np.all([np.isfinite(v) and v >= -dl for v in Ds]))
            row['f_%s' % tag] = bool(np.all([np.isfinite(v) and v >= -dl for v in Dimp]))
        for agg in ('FULL', 'G4'):
            sn, sc = tri_sign(row[agg]), tri_sign(row['%s_sc' % agg])
            row['e_cap_%s' % agg] = 'UNDEFINED' if (np.isnan(sn) or np.isnan(sc)) else ('PASS' if sn == sc else 'FAIL')
            row['positive_%s' % agg] = bool(np.isfinite(row[agg]) and row[agg] >= 0.10)
        ys = {int(k[1:]): v for k, v in row.items() if k.startswith('Y') and k[1:].isdigit() and len(k) == 5}
        vals = [v for v in ys.values() if np.isfinite(v)]
        row['years_pos'] = int(sum(v > 0 for v in vals))
        row['years_n'] = len(vals)
        row['d_ok'] = row['years_pos'] >= 12
        row['d_ok_10of17'] = row['years_pos'] >= 10
        row['e_rand'] = e_rand(row)
        # 分钟历史不可判（plan §12.1）
        und = []
        if minute:
            unc_segs = [s for s in N.SEGMENTS if seg_cov.get(s, 0) < 0.9]
            cov_years = [y for y in ys if yr_cov.get(y, 0) >= 0.9 and np.isfinite(ys[y])]
            unc_years = [y for y in ys if yr_cov.get(y, 0) < 0.9]
            pos_cov = sum(ys[y] > 0 for y in cov_years)
            row['years_covered'] = len(cov_years)
            row['years_pos_covered'] = int(pos_cov)
            row['segments_uncovered'] = '|'.join(unc_segs) or 'NONE'
            for dl in DELTAS:
                tag = 'd%02d' % int(round(dl * 100))
                cov_ok = all(np.isfinite(row['D_%s' % s]) and row['D_%s' % s] >= -dl for s in N.SEGMENTS if s not in unc_segs)
                row['c_%s_decidable' % tag] = (not unc_segs) or (not cov_ok)
            if pos_cov >= 12:
                row['d_status_history'] = 'PASS_DECIDABLE'
            elif pos_cov + len(unc_years) < 12:
                row['d_status_history'] = 'FAIL_DECIDABLE'
            else:
                row['d_status_history'] = 'POLICY_UNDECIDABLE_HISTORY'
        for prof in VERDICT_PROFILES + ('EXEC_LEADER_VS_PARENT',):
            row['size_%s' % prof] = size_status(row, prof)
        for prof in VERDICT_PROFILES:
            for agg in ('FULL', 'G4'):
                v = verdict(row, agg, prof)
                if minute and not v.startswith('不通过'):
                    tags = []
                    if not row['c_d10_decidable']:
                        tags.append('c[%s]' % row['segments_uncovered'])
                    if row['d_status_history'] == 'POLICY_UNDECIDABLE_HISTORY':
                        tags.append('d[已覆盖年 %d，正 %d]' % (row['years_covered'], row['years_pos_covered']))
                    if tags:
                        v = '不可判（POLICY_UNDECIDABLE_HISTORY：%s）' % '、'.join(tags) + ('' if v == '通过' else '；' + v)
                elif minute and v.startswith('不通过'):
                    fails = v[v.find('（') + 1:-1].split('、')
                    rest = [f for f in fails if not ((f == 'c' and not row['c_d10_decidable']) or (f == 'd' and row['d_status_history'] == 'POLICY_UNDECIDABLE_HISTORY'))]
                    if not rest:
                        v = '不可判（POLICY_UNDECIDABLE_HISTORY：失败项只在分钟未覆盖的段 / 年：%s）' % '、'.join(fails)
                row['policy_%s_%s' % (prof, agg)] = v
            row['POLICY_INTERPRETATION_PENDING_%s' % prof] = row['policy_%s_FULL' % prof][:3] != row['policy_%s_G4' % prof][:3]
        rows.append(row)
    P = pd.DataFrame(rows)
    for s in N.SEGMENTS:
        P['D_%s_ann_pp' % s] = P['D_%s' % s]
    P['FULL_ann_pp'], P['G4_ann_pp'], P['FULL_sc_ann_pp'] = P.FULL, P.G4, P.FULL_sc
    P['policy_profile'] = 'PROPOSED_PORT3_T'
    P['policy_result'] = P['policy_PROPOSED_PORT3_T_FULL']
    newo = P.exposure == N.LABEL_FIRST_LOOK
    P['replacement_preference_status'] = np.where(newo, 'NOT_AUTHORIZED', 'NOT_APPLICABLE')
    P['deployment_authorized'] = False
    P['policy_provisional'] = False
    P['policy_pass'] = P.policy_result.eq('通过')
    P['economic_improvement'] = 'SEE improvement_E6n.csv'
    P['mechanism_status'] = '见 E6n_REPORT_mechanisms（卡 H03–H11）'
    P['new_evidence'] = np.where(newo, '本轮新证据（首评，重复使用的历史）', '上一轮（同构再评，只作锚）')
    P['replacement_authorized'] = False
    P['edge_c_margin_ann_pp'] = P[['D_%s' % s for s in N.SEGMENTS]].min(axis=1) + 0.10
    P['edge_positive_margin_FULL_ann_pp'] = P.FULL - 0.10
    P['edge_years_margin'] = P.years_pos - 12
    P['edge_erand_margin_ann_pp'] = pd.concat([P['rmr_%s' % s] - MC_Z * P['mcse_%s' % s] for s in N.POST_SEGS], axis=1).min(axis=1)
    P['edge_port3_margin_pct_pt'] = pd.concat([3.0 - P['port_size_hi_T_%s' % s] for s in N.SEGMENTS] + [P['port_size_lo_T_%s' % s] + 3.0 for s in N.SEGMENTS],
                                              axis=1).min(axis=1)
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, 'policy_E6n.csv')
    N.atomic_write_csv(p1, N.to_status(P))
    # 可用期研究表（分钟成员；只报数）
    av = P[P.minute_member][['desc_id', 'feature', 'parent', 'memory', 'H', 'strength', 'outer_alpha'] + ['D_%s' % s for s in N.SEGMENTS] +
                           ['years_covered', 'years_pos_covered', 'segments_uncovered', 'd_status_history']].copy()
    cov_s = [s for s in N.SEGMENTS if seg_cov.get(s, 0) >= 0.9]
    av['covered_segments'] = '|'.join(cov_s)
    av['min_D_covered_ann_pp'] = av[['D_%s' % s for s in cov_s]].min(axis=1)
    av['status'] = 'RESEARCH_ONLY_NO_VERDICT'
    p2 = os.path.join(od, 'policy_available_period_E6n.csv')
    N.atomic_write_csv(p2, N.to_status(av))
    # 实质改善表：对 Q0 HG10 / LAG1_10（同形态 / α / H）的 Δnet8
    CF = pd.read_csv(os.path.join(sd, 'comparison_full.csv'), keep_default_na=False, na_values=[''], dtype={'comparison_id': str})
    imp = []
    for view in ('VS_Q0_HG10', 'VS_Q0_LAG1_10', 'VS_SAME_MEMORY_Q0'):
        g = CF[CF.view == view]
        for r in g.itertuples():
            imp.append(dict(desc_id=r.left_desc_id, versus=view, right_desc_id=r.right_desc_id, dnet8_FULL_ann_pp=r.FULL_ann_pp, dnet8_G4_ann_pp=r.G4_ann_pp))
    I = pd.DataFrame(imp)
    if len(I):
        segs = []
        for s in N.SEGMENTS:
            cs = pd.read_csv(os.path.join(sd, 'comparison_stats_%s.csv' % s), keep_default_na=False, na_values=[''], dtype={'comparison_id': str})
            cs = cs[cs.view.isin(['VS_Q0_HG10', 'VS_Q0_LAG1_10', 'VS_SAME_MEMORY_Q0'])][['left_desc_id', 'view', 'D_ann_pp', 'hac_se_ann_pp']]
            cs.columns = ['desc_id', 'versus', 'dnet8_%s_ann_pp' % s, 'se_%s_ann_pp' % s]
            segs.append(cs)
        for cs in segs:
            I = I.merge(cs, on=['desc_id', 'versus'], how='left')
        pol = P.set_index('desc_id')
        I['policy_result'] = I.desc_id.map(pol.policy_result)
        I['maintenance'] = np.where(I.desc_id.map(pol.minute_member).fillna(False), '新增分钟数据管线（ETL / 基线 / 覆盖回退）', '无新增数据依赖')
        I['improves_frontier_FULL'] = pd.to_numeric(I.dnet8_FULL_ann_pp, errors='coerce') > 0
        I['status'] = 'COMPUTED'
    p3 = os.path.join(od, 'improvement_E6n.csv')
    N.atomic_write_csv(p3, N.to_status(I) if len(I) else pd.DataFrame([dict(status='NOT_COMPUTABLE')]))
    # 前沿表：相对当前前沿 Q0|A4b_CVRv5|α.25|HG10|H5
    fr_id = 'ANCHOR|Q0|A4b_CVRv5|HG10|H5|s0|ALL|a0.25|f5|d+1'
    fr = []
    fl = P.set_index('desc_id')
    for r in P[(P.parent == 'A4b_CVRv5') & (P.H == 5)].itertuples():
        if r.desc_id not in fl.index or fr_id not in fl.index:
            continue
        dd = [fl.at[r.desc_id, 'D_%s' % s] - fl.at[fr_id, 'D_%s' % s] for s in N.SEGMENTS]
        nn = [fl.at[r.desc_id, 'n_%s' % s] for s in N.SEGMENTS]
        full, g4 = ST.full_g4(np.array(dd, float), np.array(nn, float))
        fr.append(dict(desc_id=r.desc_id, frontier_desc_id=fr_id, **{'d_vs_frontier_%s_ann_pp' % s: v for s, v in zip(N.SEGMENTS, dd)}, d_vs_frontier_FULL_ann_pp=full,
                       d_vs_frontier_G4_ann_pp=g4, is_primary72=r.is_primary72, policy_result=r.policy_result, status='COMPUTED'))
    p4 = os.path.join(od, 'frontier_E6n.csv')
    N.atomic_write_csv(p4, N.to_status(pd.DataFrame(fr)) if fr else pd.DataFrame([dict(status='NOT_COMPUTABLE')]))
    D72 = D[D.is_primary72.astype(str) == 'True'][['desc_id', 'parent', 'primary_recipe', 'feature', 'memory']]
    p5 = os.path.join(od, 'primary72_E6n.csv')
    N.atomic_write_csv(p5, D72)
    N.write_receipt('E6n_policy', [p1, p2, p3, p4, p5], code=[__file__], n_objects=len(P), heads=P.policy_result.str[:3].value_counts().to_dict())
    print(json.dumps(dict(objects=len(P), heads=P.policy_result.str[:3].value_counts().to_dict()), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
