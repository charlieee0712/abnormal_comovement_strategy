# -*- coding: utf-8 -*-
"""E6k_REPORT_part3（plan §13.5：144 主配置 / 旧候选 / 四 C1_hi；独立政策 profile 与候选变更清单，不自动 chosen）。
输入：results/full/policy_E6k.csv、policy_additions_E6k.csv（e6k_policy）、results/full/bootstrap/bootstrap_comparisons.csv（区间）。
五列 profile 并印（三登记 + 两 print-only），FULL 主、G4 并印；政策判词只用 通过 / 不通过 / 不可判；policy_provisional = true；deployment_authorized = false。
《生产变更候选清单》= 任一 profile（FULL）判"通过"的对象，逐 profile 分列、不合并、不择优；新算子标 NOT_AUTHORIZED（不 chosen）。"""
import e6k_boot  # noqa: F401
import os
import sys

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_report as RP
import e6k_seal as SEAL

OUT = K.P('reports', 'E6k_REPORT_part3.md')
PROFILES = ('LEGACY_EDIT5', 'PROPOSED_PORT3_T', 'PROPOSED_PORT3_LAG1', 'EXEC_DISCLOSE_ONLY', 'EXEC_LEADER_VS_PARENT')
DATES = '2010-01-04..2026-03-27（四段；2026 partial）'


def head(subject, sub, H='5', expo='见 evidence_exposure 列', unit='年化百分点 / 判词'):
    return {'主体': subject, '算子': '见列', '分母': '四段有效配对日（FULL = n 加权；G4 = 段中位）', '基准': '同 H 原父（8bp）', '子集': sub, '单位': unit,
            '日期': DATES, 'H': H, '成本模型': '源 8bp（f：A 5 亿 κ .5）', '支持': '原生（FALLBACK）', '资本视图': '实际源 DEV（e 资本：MATCH-CAP）', 'exposure': expo}


def main():
    for pkg in ('deriv', 'post'):
        ok, bad = SEAL.verify(pkg)
        if not ok:
            raise RuntimeError('seal_%s 核对失败：%s' % (pkg, bad[:5]))
    P = pd.read_csv(K.P('results', 'full', 'policy_E6k.csv'))
    A = pd.read_csv(K.P('results', 'full', 'policy_additions_E6k.csv'))
    bf = K.P('results', 'full', 'bootstrap', 'bootstrap_comparisons.csv')
    B = pd.read_csv(bf) if os.path.exists(bf) else pd.DataFrame()
    if len(B):
        b20 = B[(B.L == 20) & (B.scope == 'FULL')].set_index('comparison_id')
        P['ci_L20_lo'] = P.desc_id.map(lambda d: b20.q025.get('CP|' + d, np.nan))
        P['ci_L20_hi'] = P.desc_id.map(lambda d: b20.q975.get('CP|' + d, np.nan))
    rp = RP.Report('part3')
    rp.h(1, 'E6k REPORT part3 —— 144 主配置 / 四 C1_hi / SM 锚：五列政策 profile 与生产变更候选清单')
    rp.p('用途：plan §13.5 part3。政策 profile 五列并印（`registration/policy_profiles_E6k.json` + `_amend_1`）：LEGACY_EDIT5（E6j 登记口径复现）、'
         'PROPOSED_PORT3_T、PROPOSED_PORT3_LAG1（brief W12）与两列执行端 print-only（EXEC_DISCLOSE_ONLY、EXEC_LEADER_VS_PARENT；用户"设计尽量宽松"）；'
         '差异属定义、不择优；`policy_provisional = true`；新算子 `replacement_preference_status = NOT_AUTHORIZED`；`deployment_authorized = false`。'
         '标签：新算子行 `%s`。' % K.LABEL_FIRST_LOOK)
    main_ = P[P.primary144 | P.c1_hi | P.meas.eq('SM')].copy()
    main_ = main_[(main_.alpha == 0.25) & (main_.H == 5) | main_.c1_hi]
    cols = ['meas', 'mother', 'op', 'alpha', 'H', 'FULL', 'G4', 'ci_L20_lo', 'ci_L20_hi', 'FULL_sc', 'FULL_imp', 'years_pos', 'e_rand',
            'FULL_vs_native', 'FULL_vs_nativeC1', 'evidence_exposure']
    for prof in PROFILES:
        rp.h(2, 'profile %s' % prof)
        t = main_[[c for c in cols if c in main_.columns] + ['size_%s' % prof, 'policy_%s_FULL' % prof, 'policy_%s_G4' % prof,
                                                            'POLICY_INTERPRETATION_PENDING_%s' % prof]].sort_values(['meas', 'mother', 'op'])
        rp.table(t, head('144 主展示 + C1_hi + SM 锚', 'primary144 | c1_hi | sm_anchor', 'H 见列'), 'E6K-P3-POL-%s' % prof.replace('_', ''))
    rp.h(2, '三句加法（原生四测量 + SM；逐形态 × profile × 聚合；PX1）')
    rp.table(A, head('原生对象三句加法', 'NATIVE S / M / Q / C1 + SM × 六形态', expo='原生对象按暴露台账'), 'E6K-P3-ADD')
    rp.h(2, '《生产变更候选清单》（任一 profile FULL 通过；逐 profile 分列；deployment_authorized = false）')
    P['main_object'] = (P.primary144.astype(bool) | P.c1_hi.astype(bool) | P.meas.eq('SM'))
    ccols = ['profile', 'desc_id', 'family', 'meas', 'mother', 'op', 'alpha', 'H', 'main_object', 'FULL', 'G4', 'evidence_exposure',
             'replacement_preference_status', 'deployment_authorized']
    rows = []
    for prof in PROFILES:
        x = P[P['policy_%s_FULL' % prof] == '通过']
        for r in x.itertuples():
            rs = getattr(r, 'replacement_preference_status', '')
            rows.append(dict(profile=prof, desc_id=r.desc_id, family=r.family, meas=r.meas, mother=r.mother, op=r.op, alpha=r.alpha, H=r.H,
                             main_object=bool(r.main_object), FULL=r.FULL, G4=r.G4, evidence_exposure=r.evidence_exposure,
                             replacement_preference_status='' if pd.isna(rs) else rs, deployment_authorized=False))
    C = pd.DataFrame(rows, columns=ccols)
    pc = K.P('results', 'full', 'production_change_candidates_E6k.csv')
    K.atomic_write_csv(pc, C)
    cnt = (C.groupby(['profile', 'family']).agg(objects=('desc_id', 'count'), main_objects=('main_object', 'sum')).reset_index()
           if len(C) else pd.DataFrame(columns=['profile', 'family', 'objects', 'main_objects']))
    rp.table(cnt, head('候选计数（全部登记对象；逐 profile × 族）', '政策 FULL 通过', 'H 1…20', unit='计数'), 'E6K-P3-CAND-COUNT')
    rp.table(C[C.main_object], head('候选（主展示 144 + C1_hi + SM 锚）', '政策 FULL 通过 ∩ 主对象', 'H 见列'), 'E6K-P3-CAND')
    rp.p('研究块候选全表在 `results/full/production_change_candidates_E6k.csv`（逐 profile 分列、不合并、不择优）；研究块候选不替换 144 主对象（brief §10）；'
         '新算子行 `replacement_preference_status = NOT_AUTHORIZED`，不自动 chosen。')
    rp.h(2, '边缘清单（距离、CI、MC 误差；不另设门）')
    P['edge_min_dist'] = np.fmin(P.edge_c_margin.abs(), P.edge_positive_margin_FULL.abs())
    edge = P[P.edge_min_dist < 0.05]
    ecols = ['desc_id', 'edge_c_margin', 'edge_f_margin', 'edge_positive_margin_FULL', 'edge_years_margin', 'ci_L20_lo', 'ci_L20_hi',
             'mcse_2019-2023', 'mcse_2024-2026']
    em = edge[edge.main_object].sort_values('edge_min_dist')
    rp.table(em[[c for c in ecols if c in em.columns]], head('边缘对象（主对象；c 或正向距离 < .05，按距离排序）', 'policy_E6k.csv 边缘 ∩ 主对象',
                                                            'H 见描述符'), 'E6K-P3-EDGE')
    ec = edge.groupby(['family', 'op']).agg(edge_objects=('desc_id', 'count'), median_min_dist=('edge_min_dist', 'median')).reset_index()
    rp.table(ec, head('边缘对象计数（全部登记对象；逐族 × 算子）', 'policy_E6k.csv 边缘', 'H 1…20', unit='计数 / 年化百分点'), 'E6K-P3-EDGE-COUNT')
    rp.write(OUT)
    K.write_receipt('report_part3', [OUT], 'SUCCEEDED', queries=len(rp.qids))
    print('part3 写出：%d 个 query' % len(rp.qids), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
