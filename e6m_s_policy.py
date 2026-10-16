# -*- coding: utf-8 -*-
"""E6m 政策评分（brief §6；plan §11；registration/policy_profiles_E6m_stageN.json）。
判定函数沿 E6l，只 import 不改：e6l_policy.tri_sign / e_rand / size_status / verdict / DELTAS / VERDICT_PROFILES / MC_Z。
- 判定串：c、d、f、正向门槛、e 资本、e 随机、size(profile)。
- 逐描述符 × 四个 verdict profile × {FULL, G4}；EXEC_LEADER_VS_PARENT 只披露。
- e 随机按登记 e_random_mechanism 取对应随机机制的 real − 随机与 MCSE：LEGACY_POLICY_RANDOM / DELETE_BUDGET_COND；
  其余按状态词（RANDOM_NOT_SCHEDULED / NO_NEW_CONTENT_TO_PERMUTE）。
- PX1 三句加法：只对原生 LINEAR 的 Q0 / C1 / S / M（α .25 × H5，记忆 NONE）；含 Q 的新规则不自动得资格（plan §11.1）；E6m 无 SM 对象。
- deployment_authorized 恒 False；policy_provisional = False。
用法：e6m_s_policy.py --stats <统计目录> [--randoms <随机统计目录>] --out <输出目录>（B2 开发期在合成统计上跑通管道）。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
import e6j_stats as ST
from e6l_policy import tri_sign, e_rand, size_status, verdict, DELTAS, VERDICT_PROFILES, MC_Z

SEGS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')
POST = ('2019-2023', '2024-2026')
KEYS = ('D', 'n', 'D_sc', 'D_imp', 'D_str', 'D_6bp', 'D_12bp', 'D_gross', 'edit_gap_absmean_T', 'edit_gap_mean_T', 'port_size_lo_T', 'port_size_hi_T',
        'port_size_lo_L', 'port_size_hi_L', 'lv5_mean', 'parent_lv5_mean', 'small30_delta', 'unkT_mean', 'turn_rel', 'se_H', 'se_2H', 'net8_ann',
        'parent_net8_ann')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stats', required=True)
    ap.add_argument('--randoms', default='')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    pp = json.load(open(M.P('registration', 'policy_profiles_E6m_stageN.json'), encoding='utf-8'))
    S = {s: pd.read_csv(os.path.join(a.stats, 'descriptor_stats_%s.csv' % s), keep_default_na=False, na_values=['']).set_index('desc_id') for s in SEGS}
    R = []
    for s in SEGS:
        p = os.path.join(a.randoms, 'random_refs_%s.csv' % s) if a.randoms else ''
        if p and os.path.exists(p):
            R.append(pd.read_csv(p, keep_default_na=False, na_values=['']).assign(segment=s))
    R = pd.concat(R, ignore_index=True) if R else pd.DataFrame(columns=['desc_id', 'segment', 'mechanism', 'real_minus_rand', 'mcse', 'n'])
    refs = {m: g.set_index(['desc_id', 'segment']) for m, g in R.groupby('mechanism')}
    rows = []
    for r in D[D.block != 'PARENT'].itertuples():
        mech = r.e_random_mechanism
        content = mech if mech in ('NO_NEW_CONTENT_TO_PERMUTE', 'RANDOM_NOT_SCHEDULED') else 'SCHEDULED'
        row = dict(desc_id=r.desc_id, measurement=r.measurement, parent=r.parent, operator=r.operator, param=r.param, alpha=r.alpha, memory=r.memory,
                   H=r.H, block=r.block, family=r.family, adapter=r.adapter, condition=r.condition, is_primary72=r.is_primary72,
                   primary_recipe=r.primary_recipe, random_mechanism=mech, random_content=content, evidence_exposure=r.exposure)
        Ds, ns, Dsc, Dimp = [], [], [], []
        for s in SEGS:
            x = S[s].loc[r.desc_id] if r.desc_id in S[s].index else None
            for k in KEYS:
                row['%s_%s' % (k, s)] = float(x[k]) if (x is not None and k in x.index and pd.notna(x[k])) else np.nan
            Ds.append(row['D_%s' % s])
            ns.append(row['n_%s' % s])
            Dsc.append(row['D_sc_%s' % s])
            Dimp.append(row['D_imp_%s' % s])
            if x is not None:
                for k in x.index:
                    if k.startswith('Y') and k[1:].isdigit() and pd.notna(x[k]) and not np.isfinite(row.get(k, np.nan)):
                        row[k] = float(x[k])
            ref = refs.get(mech)
            if ref is not None and (r.desc_id, s) in ref.index:
                lr = ref.loc[(r.desc_id, s)]
                lr = lr.iloc[0] if isinstance(lr, pd.DataFrame) else lr
                row['rmr_%s' % s], row['mcse_%s' % s], row['npaths_%s' % s] = float(lr.real_minus_rand), float(lr.mcse), int(lr.n)
            else:
                row['rmr_%s' % s], row['mcse_%s' % s], row['npaths_%s' % s] = np.nan, np.nan, 0
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
        ys = {int(k[1:]): v for k, v in row.items() if k.startswith('Y') and k[1:].isdigit()}
        vals = [v for v in ys.values() if np.isfinite(v)]
        row['years_pos'] = int(sum(v > 0 for v in vals))
        row['years_n'] = len(vals)
        row['d_ok'] = row['years_pos'] >= 12
        row['d_ok_10of17'] = row['years_pos'] >= 10
        row['e_rand'] = e_rand(row)
        for prof in VERDICT_PROFILES + ('EXEC_LEADER_VS_PARENT',):
            row['size_%s' % prof] = size_status(row, prof)
        for prof in VERDICT_PROFILES:
            for agg in ('FULL', 'G4'):
                row['policy_%s_%s' % (prof, agg)] = verdict(row, agg, prof)
            row['POLICY_INTERPRETATION_PENDING_%s' % prof] = row['policy_%s_FULL' % prof][:3] != row['policy_%s_G4' % prof][:3]
        rows.append(row)
    P = pd.DataFrame(rows)
    P['economic_effect_FULL_ann_pp'] = P.FULL
    P['policy_profile'] = 'PROPOSED_PORT3_T'
    P['policy_result'] = P['policy_PROPOSED_PORT3_T_FULL']
    P['mechanism_status'] = '未分离（见 E6m REPORT mechanisms）'
    P['historical_exposure'] = P.evidence_exposure
    P['replacement_status'] = np.where(P.evidence_exposure == M.LABEL_FIRST_LOOK, 'NOT_AUTHORIZED', 'NOT_APPLICABLE')
    P['deployment_authorized'] = False
    P['policy_provisional'] = False
    P['evidence_column'] = np.where(P.evidence_exposure == M.LABEL_SECOND, '上一轮（同构再评，只作锚）', '本轮新证据（首评，重复使用的历史）')
    P['edge_c_margin_ann_pp'] = P[['D_%s' % s for s in SEGS]].min(axis=1) + 0.10
    P['edge_f_margin_ann_pp'] = P[['D_imp_%s' % s for s in SEGS]].min(axis=1) + 0.10
    P['edge_positive_margin_FULL_ann_pp'] = P.FULL - 0.10
    P['edge_years_margin'] = P.years_pos - 12
    P['edge_erand_margin_ann_pp'] = pd.concat([P['rmr_%s' % s] - MC_Z * P['mcse_%s' % s] for s in POST], axis=1).min(axis=1)
    P['edge_port3_margin_pct_pt'] = pd.concat([3.0 - P['port_size_hi_T_%s' % s] for s in SEGS] + [P['port_size_lo_T_%s' % s] + 3.0 for s in SEGS],
                                              axis=1).min(axis=1)
    os.makedirs(a.out, exist_ok=True)
    p1 = os.path.join(a.out, 'policy_E6m.csv')
    M.atomic_write_csv(p1, P)
    add = []
    nat = P[(P.operator == 'LINEAR') & (P.memory == 'NONE') & (P.alpha == '0.25') & (P.H == '5') & P.measurement.isin(['S', 'M', 'Q0', 'C1'])]
    nat = nat.set_index(['parent', 'measurement'])
    for form in sorted(set(nat.index.get_level_values(0))):
        m = nat.loc[form]
        for prof in VERDICT_PROFILES:
            for agg in ('FULL', 'G4'):
                col = 'policy_%s_%s' % (prof, agg)
                elig = [x for x in ('C1', 'M', 'S', 'Q0') if x in m.index and m.loc[x, col] == '通过']
                chosen, why = None, ''
                if 'C1' in elig:
                    chosen, why = 'C1', 'C1 合格 → 默认简单 C1'
                    beat = []
                    for arm in ('M', 'S', 'Q0'):
                        if arm in elig:
                            dseg = np.array([m.loc[arm, 'D_%s' % s] - m.loc['C1', 'D_%s' % s] for s in SEGS], float)
                            nseg = np.array([m.loc[arm, 'n_%s' % s] for s in SEGS], float)
                            full, g4 = ST.full_g4(dseg, nseg)
                            md = full if agg == 'FULL' else g4
                            if int((dseg >= 0.05).sum()) >= 3 and md >= 0.05:
                                beat.append((md, arm))
                    if beat:
                        md, arm = sorted(beat, key=lambda x: (-x[0], ('M', 'S', 'Q0').index(x[1])))[0]
                        chosen, why = arm, '%s − C1：≥ 3/4 段 ≥ +.05，合并配对差 %.3f ≥ +.05' % (arm, md)
                elif elig:
                    best = sorted(elig, key=lambda x: (-m.loc[x, agg], ('C1', 'M', 'S', 'Q0').index(x)))[0]
                    chosen, why = best, 'C1 不合格；取最佳合格单臂'
                add.append(dict(form=form, profile=prof, aggregation=agg, eligible='|'.join(elig) if elig else 'NONE', chosen=chosen or '无',
                                why=why or 'NOT_APPLICABLE', sm_clause='NOT_APPLICABLE（E6m 无 SM 对象）'))
    p2 = os.path.join(a.out, 'policy_additions_E6m.csv')
    M.atomic_write_csv(p2, pd.DataFrame(add))
    M.write_receipt(os.environ.get('E6M_TASK', 'S_policy'), [p1, p2], status='SUCCEEDED', code=[__file__, M.__file__], n_objects=len(P),
                    profile_source=pp.get('source', '')[:80])
    vc = P.policy_result.str[:3].value_counts().to_dict()
    print(json.dumps(dict(objects=len(P), policy_result_heads=vc, additions=len(add)), ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
