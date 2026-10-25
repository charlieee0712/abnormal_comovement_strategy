# -*- coding: utf-8 -*-
"""E6p 政策（附录 B.9 / B.10 / B.20；plan §13.2–§13.4）：每个 ACCOUNT 执行对象 × {LEGACY_E6O_A5, E6P_CURVE_RESEARCH}；policy_fields 长表（c1–c6、port3t、positive：
true / false / NA + 原因 + 分母 + 阈值 + query + 来源 + 批准状态）；verdict 只由字段按 plan 附录 C policy_verdict 重算（任一 false → 不通过；无 false 有 NA → 不可判；
全 true → 通过；显式 Python bool，不用 numpy.bool_ 的 is 判定——E6o 政策表 62 行"全真却不可判"即源于此，见 notes §8）。
LEGACY 适用域 = E6o 已批准域（H ∈ {5, 10, 20}、NATIVE / CASH_REMAIN、SOURCE 上限、无 RENEW、E6o 已测触发）；域外 c6 = NA（H_DOMAIN_NOT_IN_LEGACY / MAPPING_UNRESOLVED）。
E6P_CURVE_RESEARCH：c5 = NA（target_A 未定 → UNDECIDABLE_TARGET_A）。不新增任何资格门。main72 = primary72 × FEASIBLE 一行一对象。
用法：python3 e6p_policy.py [--root <输出根>]（与 e6p_stats.py 同根）"""
import os
import json
import argparse

import numpy as np
import pandas as pd

import e6p_core as O

SEG4 = list(O.SEGS)
FIELDS = ('c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'port3t', 'positive')
E6O_TRIGGERS = ('T1a', 'T1b_LEVEL', 'T1b_EDGE', 'T3b15')
UNDEC_ORDER = ('SOURCE_BINDING_PENDING', 'UNDECIDABLE_TARGET_A', 'H_DOMAIN_NOT_IN_LEGACY', 'MAPPING_UNRESOLVED', 'RANDOM_NOT_COVERED', 'CONTROL_NOT_COMPARABLE',
               'PARTIAL_YEAR_ONLY')


def rd(root, rel):
    return pd.read_csv(os.path.join(root, rel), keep_default_na=False, na_values=[''])


def research_status(D, G4, Dsrc, segD, need_source):
    if not np.isfinite(D) or not np.isfinite(G4):
        return '未覆盖'
    nneg = sum(1 for x in segD if np.isfinite(x) and x < 0)
    if D <= 0 and G4 <= 0:
        return '方向不支持'
    src_ok = (Dsrc > 0) if need_source else True
    src_bad = (Dsrc <= 0) if need_source else False
    if D >= 0.10 and G4 > 0 and src_ok:
        return '有改善点估'
    if D > 0 and (G4 <= 0 or nneg >= 2 or src_bad):
        return '结构依赖'
    return '证据有限'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    root = O.P(a.root) if a.root else O.work()
    R = pd.read_csv(O.P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
    AS = rd(root, 'statistics/account_summary_E6p.csv')
    Y = rd(root, 'statistics/yearly_E6p.csv')
    RD = rd(root, 'statistics/randoms_E6p.csv')
    S = AS.set_index(['exec_id', 'segment'])
    yv = {e: g for e, g in Y.groupby('exec_id')}
    rmap = RD.set_index(['owner_exec_id', 'mechanism', 'segment'])
    get = lambda e, s, c='D_same_h_ann_pp': float(S[c].get((e, s), np.nan)) if (e, s) in S.index else np.nan
    prow, frow = [], []
    for r in R[R.role == 'ACCOUNT'].itertuples(index=False):
        e = r.exec_id
        has_par = bool(r.parent_same_h_exec_id)
        segD = [get(e, s) for s in SEG4]
        Df, Dsc, G4 = get(e, 'FULL'), get(e, 'FULL', 'D_sc_ann_pp'), get(e, 'G4')
        Dsrc = get(e, 'FULL', 'D_source_ann_pp')
        Dimp = [get(e, s, 'D_imp_ann_pp') for s in SEG4]
        sz = [get(e, s, 'size_dev_pp') for s in SEG4]
        yy = yv.get(e)
        yD = yy.D_same_h_ann_pp.to_numpy(float) if yy is not None else np.array([])
        yfin = yD[np.isfinite(yD)]
        pos_years = int((yfin > 0).sum())
        share = pos_years / len(yfin) if len(yfin) else np.nan
        # 字段（显式 Python bool / None）
        f = {}
        why = {}
        f['c1'] = (all(x >= -0.10 for x in segD) if all(np.isfinite(x) for x in segD) else None) if has_par else None
        f['c2'] = (pos_years >= 12) if (has_par and len(yfin) == 17) else None
        f['c3'] = (bool(np.sign(Df) == np.sign(Dsc)) if (np.isfinite(Df) and np.isfinite(Dsc)) else None) if has_par else None
        c4 = None
        ok4 = []
        for s in ('2019-2023', '2024-2026'):
            k = (e, 'AMOUNT_MATCH_V2', s)
            if k in rmap.index:
                x = rmap.loc[k]
                if x.status in ('COMPUTED', 'MC_LIMIT') and np.isfinite(x.real_D_ann_pp) and np.isfinite(x.rand_mean_D_ann_pp) and np.isfinite(x.mcse):
                    ok4.append(bool(x.real_D_ann_pp - x.rand_mean_D_ann_pp >= 2.0 * x.mcse))
        comp = None
        kf = (e, 'AMOUNT_MATCH_V2', 'FULL')
        if kf in rmap.index:
            comp = rmap.loc[kf].control_comparability
        if len(ok4) == 2 and comp != 'CONTROL_NOT_COMPARABLE':
            c4 = all(ok4)
        f['c4'] = c4
        if c4 is None:
            why['c4'] = 'CONTROL_NOT_COMPARABLE' if comp == 'CONTROL_NOT_COMPARABLE' else 'RANDOM_NOT_COVERED'
        c5_legacy = (all(x >= -0.10 for x in Dimp) if all(np.isfinite(x) for x in Dimp) else None) if has_par else None
        dev = float(np.nanmax(np.abs(sz))) if any(np.isfinite(x) for x in sz) else np.nan
        f['port3t'] = bool(dev <= 3.0) if np.isfinite(dev) else None
        f['positive'] = bool(Df >= 0.10) if np.isfinite(Df) else None
        in_domain = (r.H in ('5', '10', '20') and r.deploy in ('NATIVE', 'CASH_REMAIN') and r.cap == 'SOURCE' and r.renew == '0' and r.trigger in E6O_TRIGGERS + ('NONE',))
        dom_reason = '' if in_domain else ('H_DOMAIN_NOT_IN_LEGACY' if r.H not in ('5', '10', '20') else 'MAPPING_UNRESOLVED')
        for prof in ('LEGACY_E6O_A5', 'E6P_CURVE_RESEARCH'):
            ff = dict(f)
            wy = dict(why)
            if prof == 'LEGACY_E6O_A5':
                ff['c5'] = c5_legacy
                ff['c6'] = True if in_domain else None
                if not in_domain:
                    wy['c6'] = dom_reason
                if c5_legacy is None:
                    wy['c5'] = 'MAPPING_UNRESOLVED'
            else:
                ff['c5'] = None
                wy['c5'] = 'UNDECIDABLE_TARGET_A'
                ff['c6'] = True
            for k in ('c1', 'c2', 'c3', 'port3t', 'positive'):
                if ff[k] is None and k not in wy:
                    wy[k] = 'MAPPING_UNRESOLVED' if not has_par else 'PARTIAL_YEAR_ONLY' if k == 'c2' else 'MAPPING_UNRESOLVED'
            vals = [ff[k] for k in FIELDS]
            for v in vals:
                if v is not None and not isinstance(v, bool):
                    raise TypeError('policy 字段须为显式 bool / None')
            if any(v is False for v in vals):
                verdict = '不通过'
            elif any(v is None for v in vals):
                verdict = '不可判'
            else:
                verdict = '通过'
            reasons = [wy[k] for k in FIELDS if ff[k] is None]
            und = ''
            if verdict == '不可判':
                und = next(x for x in UNDEC_ORDER if x in reasons)
            known = ';'.join(k for k in FIELDS if ff[k] is False)
            rs = research_status(Df, G4, Dsrc, segD, need_source=(prof == 'LEGACY_E6O_A5' or r.deploy == 'NATIVE'))
            if not has_par:
                rs = '未覆盖'
            b = lambda v: '' if v is None else (1 if v else 0)
            prow.append(dict(exec_id=e, execution_profile=r.execution_profile, profile_name=prof, policy_version=O.POLICY_VERSION, target_A_cny='',
                             target_A_status='UNDECIDABLE_TARGET_A', h_domain_authorized='true', c1_segment_tolerance_ok=b(ff['c1']), c2_year_positive_share=share,
                             c2_ok=b(ff['c2']), c3_full_sc_same_sign=b(ff['c3']), c4_random_post_ok=b(ff['c4']), c5_impact_ok=b(ff['c5']),
                             c5_A_used_cny=500000000 if prof == 'LEGACY_E6O_A5' else '', c6_declared_ok=b(ff['c6']), port3t_dev_pp=dev, port3t_ok=b(ff['port3t']),
                             verdict=verdict, research_status=rs, known_failure=known, undecidable_reason=und,
                             mapping_unresolved_fields=';'.join('%s:%s' % (k, wy[k]) for k in FIELDS if ff[k] is None), status='COMPUTED',
                             positive_ok=b(ff['positive']), years_positive=pos_years, years_evaluable=len(yfin)))
            src = 'E6o registration/policy_profile_E6o.json（逐字段携带）' if prof == 'LEGACY_E6O_A5' else 'registration/policy_profile_E6p.json'
            appr = 'APPROVED_E6O' if prof == 'LEGACY_E6O_A5' else 'PROPOSED_E6P'
            spec = dict(c1=('四段 D', '≥ −0.10 每段', 'QRY-POL-C1'), c2=('17 个观察年（2026 部分年）', '正年 ≥ 12', 'QRY-POL-C2'),
                        c3=('FULL D 与 FULL D_sc', '同号', 'QRY-POL-C3'), c4=('两后段 real − AMOUNT_MATCH_V2 均值', '≥ 2·MCSE（两段都）', 'QRY-POL-C4'),
                        c5=('四段 D_imp（5 亿 κ .5，旧审计冲击）' if prof == 'LEGACY_E6O_A5' else '成本曲线 @ target_A', '≥ −0.10 每段' if prof == 'LEGACY_E6O_A5' else 'target_A 未定',
                            'QRY-POL-C5'),
                        c6=('A1 冻结声明' + ('（E6o 已批准域）' if prof == 'LEGACY_E6O_A5' else ''), '在域内且已声明', 'QRY-POL-C6'),
                        port3t=('四段 size_dev_pp', '|·| ≤ 3', 'QRY-POL-P3'), positive=('FULL D', '≥ +0.10', 'QRY-POL-POS'))
            for k in FIELDS:
                v = ff[k]
                frow.append(dict(exec_id=e, profile_name=prof, field=k, value='NA' if v is None else ('true' if v else 'false'), reason=wy.get(k, '') if v is None else '',
                                 denominator=spec[k][0], threshold=spec[k][1], query_id=spec[k][2], source=src, approval_status=appr))
    PO = pd.DataFrame(prow)
    PF = pd.DataFrame(frow)
    cols = ['exec_id', 'execution_profile', 'profile_name', 'policy_version', 'target_A_cny', 'target_A_status', 'h_domain_authorized', 'c1_segment_tolerance_ok',
            'c2_year_positive_share', 'c2_ok', 'c3_full_sc_same_sign', 'c4_random_post_ok', 'c5_impact_ok', 'c5_A_used_cny', 'c6_declared_ok', 'port3t_dev_pp', 'port3t_ok',
            'verdict', 'research_status', 'known_failure', 'undecidable_reason', 'mapping_unresolved_fields', 'status', 'positive_ok', 'years_positive', 'years_evaluable']
    os.makedirs(os.path.join(root, 'statistics'), exist_ok=True)
    O.atomic_write_csv(os.path.join(root, 'statistics', 'policy_E6p.csv'), PO[cols])
    O.atomic_write_csv(os.path.join(root, 'statistics', 'policy_fields_E6p.csv'), PF)
    # main72（FEASIBLE；primary72）
    p72 = R[(R.is_primary72 == '1') & (R.execution_profile == 'FEASIBLE_DAILY')]
    pol = PO.set_index(['exec_id', 'profile_name'])
    m = []
    for r in p72.itertuples(index=False):
        e = r.exec_id
        rv = lambda mech, c: float(rmap[c].get((e, mech, 'FULL'), np.nan)) if (e, mech, 'FULL') in rmap.index else np.nan
        m.append({'exec_id': e, 'logical_id': r.logical_id, 'trigger': r.trigger, 'H': int(r.H), 'deploy': r.deploy, 'FULL_D_same_h_ann_pp': get(e, 'FULL'),
                  'G4_D_same_h_ann_pp': get(e, 'G4'), 'D_2010-2014': get(e, '2010-2014'), 'D_2015-2018': get(e, '2015-2018'), 'D_2019-2023': get(e, '2019-2023'),
                  'D_2024-2026': get(e, '2024-2026'), 'FULL_D_h5_same_deploy_ann_pp': get(e, 'FULL', 'D_h5_same_deploy_ann_pp'),
                  'FULL_D_h5_native_ann_pp': get(e, 'FULL', 'D_h5_native_ann_pp'), 'rank_vs_amount_match_v2': rv('AMOUNT_MATCH_V2', 'rank_real'),
                  'rank_vs_count_isk': rv('COUNT_ISK', 'rank_real'), 'level_worst_D_ann_pp': rv('LEVEL_WORST_1D', 'rand_mean_D_ann_pp'),
                  'verdict_legacy': pol.loc[(e, 'LEGACY_E6O_A5'), 'verdict'], 'verdict_curve': pol.loc[(e, 'E6P_CURVE_RESEARCH'), 'verdict'],
                  'research_status': pol.loc[(e, 'E6P_CURVE_RESEARCH'), 'research_status'], 'FULL_net_ann_pp': get(e, 'FULL', 'net_ann_pp'),
                  'FULL_D_sc_ann_pp': get(e, 'FULL', 'D_sc_ann_pp'), 'FULL_D_imp_ann_pp': get(e, 'FULL', 'D_imp_ann_pp')})
    M = pd.DataFrame(m).sort_values(['deploy', 'trigger', 'H'])
    O.atomic_write_csv(os.path.join(root, 'statistics', 'main72_E6p.csv'), M)
    vc = {'|'.join(k): int(v) for k, v in PO.groupby(['profile_name', 'execution_profile', 'verdict']).size().items()}
    O.atomic_write_json(os.path.join(root, 'statistics', 'policy_facts_E6p.json'), dict(policy_rows=len(PO), fields=len(PF), main72=len(M), verdicts=vc))
    print(json.dumps(dict(policy_rows=len(PO), fields=len(PF), main72=len(M)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
