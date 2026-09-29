# -*- coding: utf-8 -*-
"""E6k_REPORT_part2（plan §13.5：同冻结版本后段；首次算子评价、衰减场景、真实同日配对；brief W16 首看读法）。
两后段各自估计、合并（n 加权）、bootstrap CI（段内分层 stationary，L 20 / 60）、与推导差、与原生对应版本差、随机位置（LEGACY / NEW，MCSE）、
风险变化（组合层 size 区间、Δturn、小盘 30%）一起报；新算子标签 NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY；不用显著性过门；
推导接近 0 或为负时不写"保留率"；两段同负不叫符号支持。"""
import e6k_boot  # noqa: F401
import os
import sys

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_report as RP
import e6k_seal as SEAL

OUT = K.P('reports', 'E6k_REPORT_part2.md')
POST = K.POST_SEGS
DATES = '2019-01-02..2026-03-27（两后段；2026 partial）'


def head(subject, sub, H='5', expo='新算子：NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY；原生：见暴露台账', unit='年化百分点'):
    return {'主体': subject, '算子': '见列', '分母': '两后段有效配对日（n 加权）', '基准': '同 H 原父（8bp）', '子集': sub, '单位': unit, '日期': DATES,
            'H': H, '成本模型': '源 8bp', '支持': '原生（FALLBACK）', '资本视图': '实际源 DEV', 'exposure': expo}


def main():
    for pkg in ('deriv', 'post'):
        ok, bad = SEAL.verify(pkg)
        if not ok:
            raise RuntimeError('seal_%s 核对失败：%s' % (pkg, bad[:5]))
    P = pd.read_csv(K.P('results', 'full', 'policy_E6k.csv'))
    B = pd.read_csv(K.P('results', 'full', 'bootstrap', 'bootstrap_comparisons.csv'))
    R = pd.concat([pd.read_csv(K.P('results', 'full', 'random_refs_%s.csv' % s)).assign(segment=s) for s in POST], ignore_index=True)
    P['n_post'] = P['n_2019-2023'] + P['n_2024-2026']
    P['D_post'] = (P['D_2019-2023'] * P['n_2019-2023'] + P['D_2024-2026'] * P['n_2024-2026']) / P.n_post
    P['n_deriv'] = P['n_2010-2014'] + P['n_2015-2018']
    P['D_deriv'] = (P['D_2010-2014'] * P['n_2010-2014'] + P['D_2015-2018'] * P['n_2015-2018']) / P.n_deriv
    P['post_minus_deriv'] = P.D_post - P.D_deriv
    for L in (20, 60):
        b = B[(B.L == L) & (B.scope == 'POST')].set_index('comparison_id')
        P['post_ci_L%d_lo' % L] = P.desc_id.map(lambda d: b.q025.get('CP|' + d, np.nan))
        P['post_ci_L%d_hi' % L] = P.desc_id.map(lambda d: b.q975.get('CP|' + d, np.nan))
    for m in ('LEGACY_POLICY_RANDOM', 'NEW_COND_ISK_P5'):
        for s in POST:
            x = R[(R.mechanism == m) & (R.segment == s)].drop_duplicates(['desc_id', 'H']).set_index(['desc_id', 'H'])
            P['rmr_%s_%s' % (m[:6], s)] = [x.real_minus_rand.get((d, h), np.nan) for d, h in zip(P.desc_id, P.H)]
            P['mcse_%s_%s' % (m[:6], s)] = [x.mcse.get((d, h), np.nan) for d, h in zip(P.desc_id, P.H)]
    P['post_vs_native'] = (P['D_vs_native_2019-2023'] * P['n_2019-2023'] + P['D_vs_native_2024-2026'] * P['n_2024-2026']) / P.n_post
    P['deriv_sign_note'] = np.where(P.D_deriv > 0.05, '', np.where(P.D_deriv < -0.05, '推导为负：不写保留率', '推导近 0：不写保留率'))
    fl = P['first_look_label'].fillna('').astype(str) if 'first_look_label' in P.columns else pd.Series('', index=P.index)
    P['label'] = np.where(fl == K.LABEL_FIRST_LOOK, K.LABEL_FIRST_LOOK, P.evidence_exposure)      # 新算子统一首看标签；原生按暴露台账
    rp = RP.Report('part2')
    rp.h(1, 'E6k REPORT part2 —— 两后段（2019-2023 / 2024-2026）：首次算子评价与原生对象复现')
    rp.p('用途：plan §13.5 part2 与 brief W16。两后段按 E6k 自身授权、同冻结版本一次算完并封存（`registration/seal_post.json`）。新算子标签 `%s`：'
         '构思已使用这些年份的多轮结果，封存只防本轮临时改动，不重置历史；不称样本外，不顶替 E7 的独立性，不因新算子结果改写旧对象的证据次数。'
         '不用显著性过门；推导接近 0 或为负时不写"保留率"；两段同负不叫符号支持。' % K.LABEL_FIRST_LOOK)
    cols = ['meas', 'mother', 'op', 'D_2019-2023', 'D_2024-2026', 'D_post', 'post_ci_L20_lo', 'post_ci_L20_hi', 'D_deriv', 'post_minus_deriv',
            'post_vs_native', 'rmr_LEGACY_2019-2023', 'rmr_LEGACY_2024-2026', 'mcse_LEGACY_2019-2023', 'rmr_NEW_CO_2019-2023', 'rmr_NEW_CO_2024-2026',
            'port_size_lo_T_2019-2023', 'port_size_hi_T_2019-2023', 'turn_rel_2019-2023', 'deriv_sign_note', 'label']
    main_ = P[P.primary144 & (P.alpha == 0.25) & (P.H == 5)]
    for f in ('S', 'M', 'Q', 'C1'):
        t = main_[main_.meas == f].sort_values(['mother', 'op'])
        rp.table(t[[c for c in cols if c in t.columns]], head('测量 %s 主展示（六形态 × 六接入）' % f, 'primary144'), 'E6K-P2-144-%s' % f)
    t = P[P.c1_hi | P.meas.eq('SM')]
    rp.table(t[[c for c in cols if c in t.columns]], head('C1_hi 与 SM 锚', 'c1_hi | sm_anchor', 'H 见描述符'), 'E6K-P2-C1HI-SM')
    rp.h(2, '研究块（全部登记对象；按算子 × α 汇总，H 1…20 与测量 × 母体）')
    g = P[P.op != 'PARENT'].groupby(['family', 'op', 'alpha']).agg(cells=('D_post', 'count'), share_post_pos=('D_post', lambda x: float((x > 0).mean())),
                                                                   median_post=('D_post', 'median'), median_deriv=('D_deriv', 'median'),
                                                                   median_post_minus_deriv=('post_minus_deriv', 'median')).reset_index()
    rp.table(g, head('研究块后段分布', '全部登记（不含 PARENT）', 'H 1…20'), 'E6K-P2-GRID')
    dec = K.P('diagnostics', 'decay', 'decay_scenarios_v2.csv')         # v2：前瞻版独立 draw（v1 退化，保留不删，见 lessons）
    if os.path.exists(dec):
        rp.h(2, '衰减场景（E6j 638 对象；回顾性条件场景，不给因果份额；plan §10.5）')
        D = pd.read_csv(dec)
        rp.table(D, head('衰减场景相容性', 'E6j part2_main_config_all_objects（638）', expo='E6j 已暴露对象', unit='份额'), 'E6K-P2-DECAY')
        rp.p('本表为 v2（`diagnostics/decay/decay_scenarios_v2.csv`）：前瞻版（deriv_only_prospective）的后段误差取推导段误差的另一个独立 draw、按后段离散重缩放。'
             '首版 `decay_scenarios.csv` 的前瞻版误用同一 draw（选择事件与后段结果同号，θ0 翻号率恒为 0，退化），保留不删、不作读数。'
             '只读"与哪些场景相容 / 不相容"（观测值是否落在 [q05, q95]），不输出选择效应 / 噪声 / 市场变化的份额。')
    rp.write(OUT)
    K.write_receipt('report_part2', [OUT], 'SUCCEEDED', queries=len(rp.qids))
    print('part2 写出：%d 个 query' % len(rp.qids), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
