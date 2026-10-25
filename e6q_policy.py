# -*- coding: utf-8 -*-
"""E6q 政策（附录 B.13 / B.14；plan §13.2）：每个执行对象 × {LEGACY_E6O_A5（只审计）, POLICY_E6Q_A1_CANONICAL}；policy_fields 长表（c1–c6、port3t、positive：
true / false / NA + 原因 + 分母 + 阈值 + query + 来源 + 批准状态）；verdict 只由字段按 e6q_rules.policy_verdict 重算（任一 false → 不通过；无 false 有 NA → 不可判；
全 true → 通过；显式 Python bool）。不新增任何资格门；kappa_consistent 只作采纳候选列。
- 正式资格参照 = 同臂无退出父；trigger = NONE 的父账户自身无资格参照 → 全字段 NA（MAPPING_UNRESOLVED）、不可判、研究状态 未覆盖。
- LEGACY_E6O_A5：E6o 已批准字段原式（c5 = 旧审计冲击 legacy D_imp，A = 5 亿 κ .5）；只在 H ∈ {5, 20} 可判，H30 → c5 / c6 = NA（H_DOMAIN_NOT_IN_LEGACY）。
- POLICY_E6Q_A1_CANONICAL：c5 = CANONICAL 仪器（S0-A 选定 curve）A 主 1 亿、κ .5、δ .5 后四段 D ≥ −.10；副读 .5 / 5 亿另两列；S0-A 未闭合 → NA。
main32 = primary32 一行一对象。用法：python3 e6q_policy.py [--root <输出根>]（与 e6q_stats.py 同根）"""
import os
import json
import argparse

import numpy as np
import pandas as pd

import e6q_core as O
import e6q_rules as RU

SEG4 = list(O.SEGS)
FIELDS = ('c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'port3t', 'positive')
UNDEC_ORDER = ('SOURCE_BINDING_PENDING', 'UNDECIDABLE_RECONCILIATION', 'H_DOMAIN_NOT_IN_LEGACY', 'RANDOM_NOT_COVERED', 'CONTROL_NOT_COMPARABLE', 'PARTIAL_YEAR_ONLY',
               'MAPPING_UNRESOLVED', 'KAPPA_SIGN_DEPENDENT')
PCOLS = ['exec_id', 'scenario', 'profile_name', 'policy_version', 'A_main_cny', 'reconciliation_status', 'c1_segment_tolerance_ok', 'c2_year_positive_share', 'c2_ok',
         'c3_full_sc_same_sign', 'c4_random_post_ok', 'c5_impact_ok', 'c5_A_used_cny', 'c5_sub_5e7_ok', 'c5_sub_5e8_ok', 'kappa_consistent', 'c6_declared_ok', 'port3t_dev_pp',
         'port3t_ok', 'verdict', 'research_status', 'known_failure', 'undecidable_reason', 'mapping_unresolved_fields', 'status', 'positive_ok', 'years_positive',
         'years_evaluable']


def rd(root, rel):
    return pd.read_csv(os.path.join(root, rel), keep_default_na=False, na_values=[''])


def research_status(D, G4, segD):
    if not np.isfinite(D) or not np.isfinite(G4):
        return '未覆盖'
    nneg = sum(1 for x in segD if np.isfinite(x) and x < 0)
    if D <= 0 and G4 <= 0:
        return '方向不支持'
    if D >= 0.10 and G4 > 0:
        return '有改善点估'
    if D > 0 and (G4 <= 0 or nneg >= 2):
        return '结构依赖'
    return '证据有限'


def tri(v):
    return 'NA' if v is None else ('true' if v else 'false')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    root = O.P(*a.root.split('/')) if a.root else O.work()
    R = O.read_csv(O.P('registration', 'registry_E6q.csv'), dtype=str).fillna('')
    fz = json.load(open(O.P('registration', 'freeze_E6q.json'), encoding='utf-8'))
    recon = fz['reconciliation_status']
    AS = rd(root, 'statistics/account_summary_E6q.csv')
    Y = rd(root, 'statistics/yearly_E6q.csv')
    CC = rd(root, 'statistics/cost_curve_E6q.csv')
    rp = os.path.join(root, 'statistics', 'randoms_E6q.csv')
    RD = rd(root, 'statistics/randoms_E6q.csv') if os.path.exists(rp) else pd.DataFrame(columns=['owner_exec_id', 'mechanism', 'segment'])
    S = AS.set_index(['exec_id', 'segment'])
    yv = {e: g for e, g in Y.groupby('exec_id')}
    rmap = RD.set_index(['owner_exec_id', 'mechanism', 'segment'])
    cc = CC[(CC.comparator_kind == 'SAME_ARM_PARENT') & (CC.exponent.astype(float) == 0.5)].set_index(['exec_id', 'A_cny', 'kappa', 'segment']).net_after_impact_diff_ann_pp

    def get(e, s, c='D_same_arm_ann_pp'):
        return float(S[c].get((e, s), np.nan)) if (e, s) in S.index else np.nan

    def ccv(e, A_, k, s):
        key = (e, int(A_), float(k), s)
        return float(cc.get(key, np.nan)) if key in cc.index else np.nan
    prow, frow = [], []
    for r in R.itertuples(index=False):
        e = r.exec_id
        has_par = bool(r.parent_same_arm_exec_id)
        segD = [get(e, s) for s in SEG4]
        Df, Dsc, G4 = get(e, 'FULL'), get(e, 'FULL', 'D_sc_ann_pp'), get(e, 'G4')
        Dleg = [get(e, s, 'D_imp_legacy_5e8_ann_pp') for s in SEG4]
        sz = [get(e, s, 'size_dev_pp') for s in SEG4]
        yy = yv.get(e)
        yD = yy.D_same_arm_ann_pp.to_numpy(float) if yy is not None else np.array([])
        yfin = yD[np.isfinite(yD)]
        pos_years = int((yfin > 0).sum())
        share = pos_years / len(yfin) if len(yfin) else np.nan
        f, why = {}, {}
        f['c1'] = RU.to_bool(all(x >= -0.10 for x in segD)) if (has_par and all(np.isfinite(x) for x in segD)) else None
        f['c2'] = RU.to_bool(pos_years >= 12) if (has_par and len(yfin) == 17) else None
        if has_par and len(yfin) != 17:
            why['c2'] = 'PARTIAL_YEAR_ONLY'
        f['c3'] = RU.to_bool(np.sign(Df) == np.sign(Dsc)) if (has_par and np.isfinite(Df) and np.isfinite(Dsc)) else None
        c4 = None
        ok4 = []
        for s in ('2019-2023', '2024-2026'):
            k = (e, 'AMOUNT_MATCH_V2', s)
            if k in rmap.index:
                x = rmap.loc[k]
                rm, mc = float(x.rand_mean_D_ann_pp) if x.rand_mean_D_ann_pp != '' else np.nan, float(x.mcse) if x.mcse != '' else np.nan
                if x.status in ('COMPUTED', 'MC_LIMIT') and np.isfinite(float(x.real_D_ann_pp)) and np.isfinite(rm) and np.isfinite(mc):
                    ok4.append(RU.to_bool(float(x.real_D_ann_pp) - rm >= 2.0 * mc))
        comp = rmap.loc[(e, 'AMOUNT_MATCH_V2', 'FULL')].control_comparability if (e, 'AMOUNT_MATCH_V2', 'FULL') in rmap.index else None
        if has_par and len(ok4) == 2 and comp != 'CONTROL_NOT_COMPARABLE':
            c4 = RU.to_bool(all(ok4))
        f['c4'] = c4
        if c4 is None and has_par:
            why['c4'] = 'CONTROL_NOT_COMPARABLE' if comp == 'CONTROL_NOT_COMPARABLE' else 'RANDOM_NOT_COVERED'
        dev = float(np.nanmax(np.abs(sz))) if any(np.isfinite(x) for x in sz) else np.nan
        f['port3t'] = RU.to_bool(dev <= 3.0) if (has_par and np.isfinite(dev)) else None
        f['positive'] = RU.to_bool(Df >= 0.10) if (has_par and np.isfinite(Df)) else None
        in_leg = r.H in ('5', '20')
        c5_leg = RU.to_bool(all(x >= -0.10 for x in Dleg)) if (has_par and in_leg and all(np.isfinite(x) for x in Dleg)) else None
        cseg = {A_: [ccv(e, A_, 0.5, s) for s in SEG4] for A_ in (5e7, 1e8, 5e8)}
        c5c = {A_: (RU.to_bool(all(x >= -0.10 for x in v)) if (has_par and all(np.isfinite(x) for x in v)) else None) for A_, v in cseg.items()}
        k5, k1 = ccv(e, 1e8, 0.5, 'FULL'), ccv(e, 1e8, 1.0, 'FULL')
        kc = RU.to_bool(np.sign(k5) == np.sign(k1)) if (has_par and np.isfinite(k5) and np.isfinite(k1)) else None
        for prof in ('LEGACY_E6O_A5', 'POLICY_E6Q_A1_CANONICAL'):
            ff = dict(f)
            wy = dict(why)
            if prof == 'LEGACY_E6O_A5':
                ff['c5'] = c5_leg
                ff['c6'] = True if (in_leg and has_par) else None
                if has_par and not in_leg:
                    wy['c5'] = wy['c6'] = 'H_DOMAIN_NOT_IN_LEGACY'
                A_used = 500000000
            else:
                if recon == 'RECONCILED':
                    ff['c5'] = c5c[1e8]
                else:
                    ff['c5'] = None
                    wy['c5'] = 'UNDECIDABLE_RECONCILIATION'
                ff['c6'] = True if has_par else None
                A_used = 100000000
            for k in FIELDS:
                if ff[k] is None and k not in wy:
                    wy[k] = 'MAPPING_UNRESOLVED'
            verdict, na = RU.policy_verdict({k: ff[k] for k in FIELDS})
            reasons = [wy[k] for k in FIELDS if ff[k] is None]
            und = next((x for x in UNDEC_ORDER if x in reasons), '') if verdict == '不可判' else ''
            known = ';'.join(k for k in FIELDS if ff[k] is False)
            rs = research_status(Df, G4, segD) if has_par else '未覆盖'
            prow.append(dict(exec_id=e, scenario=r.scenario, profile_name=prof, policy_version=O.POLICY_VERSION, A_main_cny=100000000, reconciliation_status=recon,
                             c1_segment_tolerance_ok=tri(ff['c1']), c2_year_positive_share=share if has_par else '', c2_ok=tri(ff['c2']), c3_full_sc_same_sign=tri(ff['c3']),
                             c4_random_post_ok=tri(ff['c4']), c5_impact_ok=tri(ff['c5']), c5_A_used_cny=A_used,
                             c5_sub_5e7_ok=tri(c5c[5e7]) if (prof != 'LEGACY_E6O_A5' and recon == 'RECONCILED') else 'NA',
                             c5_sub_5e8_ok=tri(c5c[5e8]) if (prof != 'LEGACY_E6O_A5' and recon == 'RECONCILED') else 'NA',
                             kappa_consistent=tri(kc) if prof != 'LEGACY_E6O_A5' else 'NA', c6_declared_ok=tri(ff['c6']), port3t_dev_pp=dev, port3t_ok=tri(ff['port3t']),
                             verdict=verdict, research_status=rs, known_failure=known, undecidable_reason=und,
                             mapping_unresolved_fields=';'.join('%s:%s' % (k, wy[k]) for k in FIELDS if ff[k] is None), status='COMPUTED', positive_ok=tri(ff['positive']),
                             years_positive=pos_years if has_par else '', years_evaluable=len(yfin) if has_par else ''))
            src = 'E6o registration/policy_profile_E6o.json（经 E6p 逐字段携带）' if prof == 'LEGACY_E6O_A5' else 'registration/policy_profile_E6q.json'
            appr = 'APPROVED_E6O' if prof == 'LEGACY_E6O_A5' else 'PROPOSED_E6Q'
            spec = dict(c1=('四段 D_same_arm', '≥ −0.10 每段', 'QRY-POL-C1'), c2=('17 个观察年（2026 部分年）', '正年 ≥ 12', 'QRY-POL-C2'),
                        c3=('FULL D 与 FULL D_sc', '同号', 'QRY-POL-C3'), c4=('两后段 real − AMOUNT_MATCH_V2 均值', '≥ 2·MCSE（两段都）', 'QRY-POL-C4'),
                        c5=(('四段 D_imp（legacy；5 亿 κ .5）', '≥ −0.10 每段', 'QRY-POL-C5L') if prof == 'LEGACY_E6O_A5' else
                            ('四段 D（CANONICAL curve；1 亿 κ .5 δ .5）', '≥ −0.10 每段', 'QRY-POL-C5C')),
                        c6=('A1 冻结声明' + ('（E6o 已批准域 H ∈ {5, 20}）' if prof == 'LEGACY_E6O_A5' else ''), '在域内且已声明', 'QRY-POL-C6'),
                        port3t=('四段 size_dev_pp', '|·| ≤ 3', 'QRY-POL-P3'), positive=('FULL D_same_arm', '≥ +0.10', 'QRY-POL-POS'))
            for k in FIELDS:
                v = ff[k]
                frow.append(dict(exec_id=e, profile_name=prof, field=k, value=tri(v), reason=wy.get(k, '') if v is None else '', denominator=spec[k][0], threshold=spec[k][1],
                                 query_id=spec[k][2], source=src, approval_status=appr))
    PO = pd.DataFrame(prow, columns=PCOLS)
    PF = pd.DataFrame(frow)
    os.makedirs(os.path.join(root, 'statistics'), exist_ok=True)
    O.atomic_write_csv(os.path.join(root, 'statistics', 'policy_E6q.csv'), PO)
    O.atomic_write_csv(os.path.join(root, 'statistics', 'policy_fields_E6q.csv'), PF)
    # main32
    pol = PO.set_index(['exec_id', 'profile_name'])
    m = []
    for r in R[R.is_primary32 == '1'].itertuples(index=False):
        e = r.exec_id
        rv = lambda mech, c: (float(rmap[c].get((e, mech, 'FULL'))) if (e, mech, 'FULL') in rmap.index and rmap[c].get((e, mech, 'FULL')) != '' else np.nan)
        m.append({'exec_id': e, 'logical_id': r.logical_id, 'trigger': r.trigger, 'H': int(r.H), 'arm': r.arm, 'A_ref': r.A_ref, 'FULL_net_ann_pp': get(e, 'FULL', 'net_ann_pp'),
                  'FULL_D_same_arm_ann_pp': get(e, 'FULL'), 'FULL_D_native_same_trigger_ann_pp': get(e, 'FULL', 'D_native_same_trigger_ann_pp'), 'G4_D_same_arm_ann_pp': get(e, 'G4'),
                  'D_2010-2014': get(e, '2010-2014'), 'D_2015-2018': get(e, '2015-2018'), 'D_2019-2023': get(e, '2019-2023'), 'D_2024-2026': get(e, '2024-2026'),
                  'FULL_D_h5_global_ann_pp': get(e, 'FULL', 'D_h5_global_ann_pp'), 'FULL_D_frontier_ann_pp': get(e, 'FULL', 'D_frontier_ann_pp'),
                  'FULL_D_level_h20_ann_pp': get(e, 'FULL', 'D_level_h20_ann_pp'), 'cost_1e8_D_same_arm_ann_pp': ccv(e, 1e8, 0.5, 'FULL'),
                  'cost_5e8_D_same_arm_ann_pp': ccv(e, 5e8, 0.5, 'FULL'), 'rank_vs_amount_match_v2': rv('AMOUNT_MATCH_V2', 'rank_real'),
                  'rank_vs_amount_isk_v2': rv('AMOUNT_ISK_V2', 'rank_real'), 'verdict_legacy': pol.loc[(e, 'LEGACY_E6O_A5'), 'verdict'],
                  'verdict_canonical': pol.loc[(e, 'POLICY_E6Q_A1_CANONICAL'), 'verdict'], 'research_status': pol.loc[(e, 'POLICY_E6Q_A1_CANONICAL'), 'research_status']})
    M = pd.DataFrame(m).sort_values(['trigger', 'H', 'arm'])
    O.atomic_write_csv(os.path.join(root, 'statistics', 'main32_E6q.csv'), M)
    vc = {'|'.join(k): int(v) for k, v in PO.groupby(['profile_name', 'scenario', 'verdict']).size().items()}
    O.atomic_write_json(os.path.join(root, 'statistics', 'policy_facts_E6q.json'), dict(policy_rows=len(PO), fields=len(PF), main32=len(M), verdicts=vc, reconciliation=recon))
    print(json.dumps(dict(policy_rows=len(PO), fields=len(PF), main32=len(M), verdicts=vc), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
