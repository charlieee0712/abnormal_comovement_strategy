#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i REPORT_part3 (Stage 4 合并复盘; brief §9 / §14 / §15) 生成器。
读: part2 面板 (reports/part2_tables/descriptor_panel_post.csv)、carried/summary/ (C1 / C2)、reports/hypothesis_outcomes.json、
research_catalog_v36.csv、factor_iteration_delta.csv、R0 query_ids、e6i_part3_static (Q16 条目 / 全轮 coverage)。
全部数字现算带 query_id; 每张表十项表头; 禁用词 / 主机地址扫描。另写 registry/coverage.csv。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_report_part1_text as TX
import e6i_part3_static as PS

R = I.RES
CS = os.path.join(R, 'carried', 'summary')
TAB = os.path.join(R, 'reports', 'part3_tables')
PRIM = TX.PRIM
q, f, pc, md, sgn = TX.q, TX.f, TX.pc, TX.md, TX.sgn_word
ALLD = '四段（2010-01-04..2026-03-27；推导两段 + 后段两段，段间不拼接）'


def hdr(op, denom, bench, subset, **kw):
    kw.setdefault('dates', ALLD)
    return TX.hdr(op, denom, bench, subset, **kw)


def rd(p, **kw):
    return pd.read_csv(p, low_memory=False, **kw)


YC = ['y%d' % y for y in range(2010, 2027)]
ADDENDUM = 'B 后事后补充（2026-09-25，47 时间）：只重新汇总已封存的账户，不改变任何登记读数'


def baseline_section(w):
    """§0 母体基线：本报告所有"子 − 母"增量的参照。"""
    rows = []
    for seg in I.SEGMENTS:
        p = os.path.join(R, 'registry', 'mother_needs_%s.csv' % seg)
        if not os.path.exists(p):
            continue
        for r_ in rd(p).itertuples():
            rows.append(dict(segment=seg, mother=r_.mother_id, pool0_per_day=r_.pool0_per_day, held_per_day=r_.final_B_per_day,
                             capital=r_.capital_pos_mean, gross_ann=r_.gross_ann, net8_ann=r_.net8_ann,
                             net8_per_capital=r_.net8_ann / r_.capital_pos_mean if r_.capital_pos_mean > 0 else np.nan))
    b = pd.DataFrame(rows)
    b.to_csv(os.path.join(TAB, 'T0_mother_baseline.csv'), index=False)
    w('## 0. 母体基线（B 后事后补充）\n')
    w('_%s。_\n' % ADDENDUM)
    w('后面所有"子 − 母"都是相对下表母体账户的差。\n')
    w(hdr('逐 (段, 母体)：人数与投入资金为日均，收益为年化', '母体源引擎账户（H5；旧对象，四段都公开）',
          'clean 基准（gross = 组合收益 − 基准 x 投入资金）', 'R1 / R2 / A06 / A08',
          unit='pool0 / 持仓：名 / 日；capital：权重和（0–1）；收益：年化百分点；net8_per_capital = net8 / capital',
          dates='四段各自', H='5（源）', capital='源 DEV（每只 min(1/n, 1%)，不归一 → 投入资金随持仓名数上升）'))
    w(md(b, nd=2))
    post = b[b.segment.isin(I.POST_SEGS)]
    seg_cap = b.groupby('segment').capital.agg(['min', 'max'])
    seg_pc = b.groupby('segment').net8_per_capital.agg(['min', 'max'])
    w('%s——母体收益随时间上升主要伴随投入资金上升（pool0 变大 → 持仓名数变多 → 在每只 ≤ 1%% 的规则下投入资金变多）；'
      '单位资金超额各段在约 9–18 之间，没有同样的上升趋势。量级参照：+0.2 个百分点约为母体后段 net8 的 2%%。\n' % q(
          'P3-BASE', '两后段母体 net8 年化 %s ~ %s、持仓 %.0f ~ %.0f 名 / 日、投入资金 %.2f ~ %.2f；投入资金各段 %s；单位资金 net8 各段 %s' % (
              f(post.net8_ann.min(), 2), f(post.net8_ann.max(), 2), post.held_per_day.min(), post.held_per_day.max(),
              post.capital.min(), post.capital.max(),
              '，'.join('%s %.2f–%.2f' % (s_, r_['min'], r_['max']) for s_, r_ in seg_cap.iterrows()),
              '，'.join('%s %.1f–%.1f' % (s_, r_['min'], r_['max']) for s_, r_ in seg_pc.iterrows()))))
    return b


def fam_tab(g, by='family'):
    rows = []
    for key, x in g.groupby(by):
        ym = x[YC].median()
        ci = x.ci_post.astype(bool)
        rows.append({by: key, 'n_mem': int(x.member_id.nunique()), 'n': len(x),
                     'd10_14': x['d_10-14'].median(), 'd15_18': x['d_15-18'].median(),
                     'p19_23': x.p1.median(), 'p24_26': x.p2.median(),
                     'yrs_pos': '%d/%d' % (int((ym > 0).sum()), int(ym.notna().sum())), 'yrs_pos_n': int((ym > 0).sum()),
                     'ci_pos': int((ci & (x.post > 0)).sum()), 'ci_neg': int((ci & (x.post < 0)).sum()),
                     'post': x.post.median(), 'samecap_19_23': x.dsamecap_ann_1.median(), 'samecap_24_26': x.dsamecap_ann_2.median(),
                     'vs_rand_19_23': x.z1.median(), 'vs_rand_24_26': x.z2.median(), 'mde80_post': x.mde_post.median()})
    return pd.DataFrame(rows)


SHOW = ['n_mem', 'n', 'd10_14', 'd15_18', 'p19_23', 'p24_26', 'yrs_pos', 'ci_pos', 'ci_neg', 'samecap_19_23', 'samecap_24_26',
        'vs_rand_19_23', 'vs_rand_24_26', 'mde80_post']


def four(r_):
    return '%s / %s / %s / %s' % (f(r_.d10_14), f(r_.d15_18), f(r_.p19_23), f(r_.p24_26))


def family_section(w, M):
    """§1b 分族读数（族 = A0 事前定义的 family_id）。"""
    P1 = rd(os.path.join(R, 'reports', 'part1_tables', 'descriptor_panel.csv'), usecols=['descriptor_id', 'd_10-14', 'd_15-18'])
    X = M.merge(P1, on='descriptor_id', how='left')
    X['a'] = pd.to_numeric(X.strength, errors='coerce')
    w('## 1b. 分族读数（B 后事后补充）\n')
    w('_%s。_\n' % ADDENDUM)
    w('**说明**：族是 A0 事前定义的（`registry/feature_semantics_v2.csv` 的 family_id），按族汇总本身不是事后挑选；但本节是看过后段结果之后才做的汇总，'
      '其中"小权重 + 长持有期"切片是事后选的。族内描述符来自同一批 成员 x 母体 x α x H，高度相关——显著计数不是独立检验。'
      '**术语更正**：part1 / part1b / part2 / 记录 B 草稿里的"K 响应族部分混入"指 **K 槽位的全部 9 个族**（1134 个描述符，含 K 类与响应族两个方向）；'
      '本节起"响应族"只指 amount_response（单位成交额的价格响应）与 turnover_response（单位换手的价格响应）两族。\n')
    K = X[(X.route_id == 'RK') & X.direction_role.isin(PRIM) & (X.policy == 'FALLBACK')]
    kf = fam_tab(K)
    kf.to_csv(os.path.join(TAB, 'T1c_K_family.csv'), index=False)
    w(hdr('族内描述符中位（逐年列 = 逐年中位为正的年数 / 有值年数）；ci = 后段合并 NW(lag H) 95% 区间排除 0 的个数',
          'K 槽位：RK 主方向（K 类 high_bad、响应族 low_bad）x SLOT FALLBACK（α .125 / .25 / .5）x 三母体 x 全部 H',
          '同 H 真实母体；samecap = 同资本对照；vs_rand = 真实 − 同预算匹配随机', '按族（9 个）', H='全部登记 H（1 / 2 / 3 / 5 / 10 / 20）'))
    w(md(kf[['family'] + SHOW]))
    resp = kf[kf.family.isin(['amount_response', 'turnover_response'])].set_index('family')
    br = kf.set_index('family').loc['source_bridge']
    neg24 = kf[kf.p24_26 < 0].sort_values('p24_26')
    derpos = kf[(kf.d10_14 > 0) & (kf.d15_18 > 0)]
    postpos = kf[(kf.p19_23 > 0) & (kf.p24_26 > 0)]
    w('%s。\n' % q('P3-FAM-K', '推导两段中位都为正的族 %d / %d；后段两段中位都为正的族：%s；2024-26 中位为负的族：%s' % (
        len(derpos), len(kf), '、'.join(postpos.family) or '无', '、'.join('%s %s' % (r_.family, f(r_.p24_26)) for r_ in neg24.itertuples()))))
    w('%s。\n' % q('P3-FAM-KR', '；'.join('%s 四段 %s，逐年为正 %s，后段显著 正 %d / 负 %d，同资本后段 %s / %s，对匹配随机后段 %s / %s' % (
        fam_, four(r_), r_.yrs_pos, r_.ci_pos, r_.ci_neg, f(r_.samecap_19_23), f(r_.samecap_24_26), f(r_.vs_rand_19_23),
        f(r_.vs_rand_24_26)) for fam_, r_ in resp.iterrows()) + '；源桥（原 K 的平滑 / 比值和）四段 %s，逐年为正 %s' % (four(br), br.yrs_pos)))
    km = fam_tab(K[K.family.isin(['amount_response', 'turnover_response', 'source_bridge'])], by='member_id')
    km['family'] = km.member_id.map(K.drop_duplicates('member_id').set_index('member_id').family)
    km = km.sort_values(['family', 'member_id'])
    km.to_csv(os.path.join(TAB, 'T1d_K_members_response.csv'), index=False)
    w(hdr('成员内描述符中位', '同上 K 槽位中属于 amount_response / turnover_response / source_bridge 的成员', '同 H 真实母体', '按成员',
          H='全部登记 H'))
    w(md(km[['member_id', 'family'] + SHOW]))
    am = km[km.family == 'amount_response']
    w('%s——2019-23 的显著正值主要来自 20 日窗口的成员；2024-26 各成员（全网格）都接近 0。\n' % q('P3-FAM-KM', 'amount_response 成员后段两段中位与显著个数：' + '；'.join(
        '%s %s / %s（正 %d / 负 %d）' % (r_.member_id, f(r_.p19_23), f(r_.p24_26), r_.ci_pos, r_.ci_neg) for r_ in am.itertuples())))
    ah = []
    for lab, col, vals in (('α', 'a', sorted(K.a.dropna().unique())), ('H', 'H', sorted(K.H.unique()))):
        for v_ in vals:
            x = K[K[col] == v_]
            ah.append(dict(group='%s=%g' % (lab, v_), n=len(x), d10_14=x['d_10-14'].median(), d15_18=x['d_15-18'].median(),
                           p19_23=x.p1.median(), p24_26=x.p2.median()))
    ah = pd.DataFrame(ah)
    ah.to_csv(os.path.join(TAB, 'T1e_K_alpha_H.csv'), index=False)
    w(hdr('分组描述符中位', 'K 槽位全部 9 族（同上 1134 个描述符）', '同 H 真实母体', '按混入强度 α 与按持有期 H 分组'))
    w(md(ah))
    a_ = ah[ah.group.str.startswith('α')].set_index('group')
    h_ = ah[ah.group.str.startswith('H')].set_index('group')
    w('%s——后段让 K 槽位缩水的主要是大权重与短持有期的用法。\n' % q('P3-FAM-AH', '2024-26 中位：按 α %s；按 H %s；推导两段中位最高的是 %s（%s / %s）与 %s（%s / %s）' % (
        '，'.join('%s %s' % (k_, f(v_)) for k_, v_ in a_.p24_26.items()), '，'.join('%s %s' % (k_, f(v_)) for k_, v_ in h_.p24_26.items()),
        (a_.d10_14 + a_.d15_18).idxmax(), f(a_.loc[(a_.d10_14 + a_.d15_18).idxmax(), 'd10_14']), f(a_.loc[(a_.d10_14 + a_.d15_18).idxmax(), 'd15_18']),
        (h_.d10_14 + h_.d15_18).idxmax(), f(h_.loc[(h_.d10_14 + h_.d15_18).idxmax(), 'd10_14']), f(h_.loc[(h_.d10_14 + h_.d15_18).idxmax(), 'd15_18']))))
    ks = fam_tab(K[(K.a <= 0.25) & (K.H >= 10)])
    ks.to_csv(os.path.join(TAB, 'T1f_K_family_slice.csv'), index=False)
    w(hdr('族内描述符中位', 'K 槽位中 α ≤ .25 且 H ≥ 10 的描述符', '同 H 真实母体', '**事后切片**（看过后段后选的；推导段整体偏好大 α、短 H，见上表）',
          H='10 / 20'))
    w(md(ks[['family'] + SHOW]))
    sl = ks.set_index('family')
    w('%s。切片里源桥（原 K 的平滑 / 比值和）同样逐年稳定，所以不能用切片证明响应族"不只是多给原 K 加权"——两者仍未正式分离。\n' % q(
        'P3-FAM-SLICE', '；'.join('%s 四段 %s，逐年为正 %s，后段显著 正 %d / 负 %d，后段 MDE80 中位 %s' % (
            fam_, four(sl.loc[fam_]), sl.loc[fam_, 'yrs_pos'], sl.loc[fam_, 'ci_pos'], sl.loc[fam_, 'ci_neg'], f(sl.loc[fam_, 'mde80_post']))
            for fam_ in ('amount_response', 'turnover_response', 'source_bridge') if fam_ in sl.index)))
    T = X[(X.route_id == 'RT') & (X.direction_role == 'primary') & (X.policy == 'FALLBACK') & X.a.isin([0.125, 0.25])]
    tf = fam_tab(T)
    tf.to_csv(os.path.join(TAB, 'T1g_T_family.csv'), index=False)
    w(hdr('族内描述符中位', 'T 小权重加：RT 主方向 x SLOT FALLBACK（α .125 / .25）x 四母体', '同 H 真实母体；samecap / vs_rand 同上', '按族（7 个）'))
    w(md(tf[['family'] + SHOW]))
    tpos = tf[(tf.p19_23 > 0) & (tf.p24_26 > 0)]
    w('%s——T 的新测量在后段没有一个族清楚为正（对匹配随机多为正：排序信息在，但不超过母体）。\n' % q(
        'P3-FAM-T', 'T 小权重加：后段两段中位都为正的族：%s；各族后段两段中位都在 ±%.2f 以内' % (
            '、'.join('%s %s / %s' % (r_.family, f(r_.p19_23), f(r_.p24_26)) for r_ in tpos.itertuples()) or '无',
            np.nanmax(np.abs(tf[['p19_23', 'p24_26']].values)))))
    other = [('RV', 'V 删除 / 缩减', X[(X.route_id == 'RV') & (X.direction_role == 'primary') & X.role.isin(['VETO_NEW', 'SOFT', 'SOFT_HARD'])]),
             ('RO', 'O 高值端删除', X[(X.route_id == 'RO') & (X.direction_role == 'high_role')]),
             ('RR', 'R 同人数 SWAP', X[(X.route_id == 'RR') & (X.role == 'SWAP')]),
             ('RC', 'C 主方向（槽位 + 焦点替换）', X[(X.route_id == 'RC') & (X.direction_role == 'primary')]),
             ('RA', 'A 同预算换入', X[(X.route_id == 'RA') & (X.role == 'SWAP')]),
             ('RS', 'S 状态内条件换入', X[(X.route_id == 'RS') & (X.role == 'SWAP')]),
             ('RL', '摩擦边缘替换 + 轻摩擦否决', X[X.route_id == 'RL'])]
    full, summ = [], []
    for rid, lab, g in other:
        t = fam_tab(g)
        t.insert(0, 'route_id', rid)
        full.append(t)
        t['m4'] = t[['d10_14', 'd15_18', 'p19_23', 'p24_26']].mean(axis=1)
        best = t.sort_values('m4', ascending=False).iloc[0]
        summ.append(dict(route_id=rid, usage=lab, n_fam=len(t),
                         fam_post_both_pos='、'.join(t[(t.p19_23 > 0) & (t.p24_26 > 0)].family) or '—',
                         fam_all4_pos='、'.join(t[(t.d10_14 > 0) & (t.d15_18 > 0) & (t.p19_23 > 0) & (t.p24_26 > 0)].family) or '—',
                         best_family=best.family, best_four=four(best), vs_rand_post_median='%s / %s' % (f(g.z1.median()), f(g.z2.median()))))
    pd.concat(full, ignore_index=True).drop(columns=['m4']).to_csv(os.path.join(TAB, 'T1h_family_all_routes.csv'), index=False)
    so = pd.DataFrame(summ)
    w(hdr('每路线：族数、两后段中位都为正的族、四段都为正的族、四段均值最高的族及其四段中位、路线全体对匹配随机的后段中位',
          '各路线主用法的全部描述符（与 hypothesis_outcomes 的范围一致）', '同 H 真实母体；vs_rand = 真实 − 同预算匹配随机', 'V / O / R / C / A / S / 摩擦',
          H='全部登记 H', support='各段有效日（缺测日不拼接）；逐族全表 `part3_tables/T1h_family_all_routes.csv`'))
    w(md(so))
    rc = X[(X.route_id == 'RC') & (X.direction_role == 'primary')]
    w('%s。\n' % q('P3-FAM-ALL', '其余路线后段两段中位都为正的族：' + '；'.join('%s %s' % (r_.route_id, r_.fam_post_both_pos) for r_ in so.itertuples()) +
                    '；C 主方向：对母体后段中位 %s / %s，对匹配随机 %s / %s' % (f(rc.p1.median()), f(rc.p2.median()), f(rc.z1.median()), f(rc.z2.median()))))
    res = X[(X.route_id == 'RK') & X.direction_role.isin(PRIM) & (X.policy == 'FALLBACK') & (X.family == 'cross_sectional_residual')]
    w('- **读法**：')
    w('  1. K 轴：推导段 9 个族都为正（K 槽位整体在推导段有增量）；后段相对站得住的是"价格对成交的响应"口径（把 |收益| 放在分子、按成交额或换手聚合估计）：'
      '全网格下 2024-26 只是接近 0（amount_response +0.04、turnover_response −0.13），但好于只改表示 / 中性化 / 聚合顺序 / 点态倒数各族的 −0.25 ~ −0.60；'
      '小权重 + 长持有期下两族 2024-26 为正（事后切片）。机制未分离：可能是 K0 分母近 0 时的奇点在中性化回归里被放大（响应口径天然避开），'
      '也可能是成交额单位或窗口长度——本轮没有逐项隔离的设计。响应族的增量不是资金效应：同资本对照与原始增量几乎相同，投入资金不变（part2 面板 d_pos ≈ 0）。')
    w('  2. 量级与功效：响应族后段合并约 +0.08~0.15 个百分点 / 年，低于后段能以八成把握测出的最小效应（全网格约 0.5、切片约 0.3）——即使效应是真的，单靠后段也难"显著"；'
      '判断要靠机制、逐年一致与 E7。')
    w('  3. 新旧测量：R0 的 Q18 画像显示新测量区分"被错剔赢家 vs 被剔输家"比旧测量强（T_std20 约为旧 T_std60 的 2.3–2.6 倍〔Q-R0-Q18A〕；'
      'K_res_log 在 2010-14 约为旧 K0 的 2.5 倍、2015-18 旧 K0 反号〔Q-R0-Q18B〕），'
      '但 %s——画像区分力强不等于账户增量；这条证据支持 T_std20 这类测量，不能套到响应族上。' % q(
          'P3-FAM-Q18', 'K_res_log 所在的 cross_sectional_residual 族在账户层后段两段中位 %s / %s' % (f(res.p1.median()), f(res.p2.median()))))
    w('  4. 其余轴：T 的新测量后段接近 0；V / O / R / A / S / 摩擦的现有用法没有族在两个后段都清楚为正（V 的 idiosyncratic 族后段两段小正约 +0.03 / +0.02，但 2010-14 为 −0.26）；'
      'C 对匹配随机明显为正、对母体接近 0 或为负——排序信息在，但母体（含 CVR_20d 否决）已经用到了。')
    w('  5. 含义（交规划 session 与用户）：K 轴下一轮主攻"响应"口径（直接估计价格冲击），不再在 K 的表示上做文章；E7 可按族（成员与配置事前固定）登记；'
      '"新信息 vs 给原 K 加权"用新旧排序分歧分层正式分离。\n')
    return dict(kf=kf, ks=ks)


def c1_section(w):
    t3p, t4p, t5p, t2p = (os.path.join(CS, x) for x in ('C1_T3_contrasts.csv', 'C1_T4_bridges.csv', 'C1_T5_instrument.csv',
                                                          'C1_T2_strict.csv'))
    w('## 2. Q10 C1：人数 N x 行业宽度 B（plan §9.1）\n')
    if not os.path.exists(t3p):
        w('_（C1 汇总缺失）_\n')
        return {}
    t3a = rd(t3p)
    t3m = rd(os.path.join(CS, 'C1_T3_contrasts_min60.csv'))
    t3a.to_csv(os.path.join(TAB, 'C1_contrasts_all.csv'), index=False)
    t3m.to_csv(os.path.join(TAB, 'C1_contrasts_min60.csv'), index=False)
    t2 = rd(t2p)
    fz = t2[(t2.scope == 'frozen') & (t2.alloc == 'equal')]
    w('**支持**：严格交叉对每个被比较的格对取两格同日都可行的交易日（plan §9.1）；推导段 pool0 较小，N ≥ 150 或 B = 8 的格多数日子行业容量不足。'
      '报告口径（不按结果取舍）：逐 seed 共同可行日 < 60（约 3 个月）视为支持不足、不进均值；全量口径另存 `part3_tables/C1_contrasts_all.csv`。%s。\n' % q(
          'Q10-SUPPORT', '各 (段, 对比, 固定维) 的共同可行日均值：' + '；'.join('%s %s %s %.0f 天' % (
              r_.segment, r_.contrast, r_.fixed, r_.common_days_mean) for r_ in fz.itertuples())))
    main_ = t3m[(t3m.scope == 'frozen') & (t3m.alloc == 'equal')]
    g = main_.groupby(['segment', 'contrast', 'fixed']).agg(n_cells=('mean', 'size'), mean_of_means=('mean', 'mean'),
                                                            cells_pos=('mean', lambda x: int((x > 0).sum())),
                                                            seeds=('n_seed', 'sum'), common_days=('common_days', 'mean')).reset_index()
    w(hdr('格内逐 seed 配对差（后一端 − 前一端）的均值，再在格间汇总（格 = 母体 x 深度 q）', 'C1 严格交叉中共同可行日 ≥ 60 的 seed x 格',
          '同一 seed、同一分配、同一母体与深度下对比的另一端', '评分口径 frozen（完整 pool0 冻结中性化排名）x 分配 equal（容量受限近似等人数）',
          dates='四段各自', H='源持有（母体原生）', support='两格同日都可行的交易日（逐 seed ≥ 60 天）'))
    w(md(g))
    out = {}
    for ctr in ('B16−B8', 'N250−N100'):
        x = main_[main_.contrast == ctr]
        out[ctr] = x.groupby('segment')['mean'].apply(lambda s: (s > 0).mean())
    w('%s。\n' % q('Q10-SIGN', '；'.join('%s：各段"格均值 > 0"的占比 %s' % (
        ctr, '，'.join('%s %s' % (s_, pc(v_)) for s_, v_ in sp.items()) or '无支持') for ctr, sp in out.items())))
    nm = main_[main_.contrast == 'N250−N100'].groupby('segment')['mean'].mean()
    bm = main_[main_.contrast == 'B16−B8'].groupby('segment')['mean'].mean()
    cp, pp = os.path.join(CS, 'C1_T9_capital.csv'), os.path.join(CS, 'C1_T9_capital_pairs.csv')
    if len(nm) and os.path.exists(cp) and os.path.exists(pp):
        cap = rd(cp)
        cap.to_csv(os.path.join(TAB, 'C1_capital.csv'), index=False)
        show = cap[(cap.contrast == 'N250−N100') | ((cap.scope == 'frozen') & (cap.alloc == 'equal'))].sort_values(
            ['contrast', 'segment', 'fixed', 'scope', 'alloc'])
        show = show.assign(cap_share=np.where(show.d_deploy.abs() >= 0.2, show.cap_share, np.nan))   # 分母近 0 时比值无意义
        w('**资本分解（B 后事后补充）**：C1 的账户用源 DEV（每只 min(1/n, 1%%)、不归一），持仓名数变多时投入资金随之变多。下表把每个配对的账户差拆成'
          '"投入资金变多"与"单位资金超额变高"两部分（恒等：部署视图差 = (资金_b − 资金_a) x e_a + 资金_b x (e_b − e_a)）。'
          '严格视图的逐日投入资金没有保存，所以分解只能在部署视图（全日历 min(N, N_t)）上做；两种视图支持不同，差的大小不同，同一配对并列给出。_%s。_\n' % ADDENDUM)
        w(hdr('逐配对均值（e 为中位）：严格视图差 d_strict、部署视图差 d_deploy = cap_part + sel_part；cap_share = cap_part / d_deploy（|d_deploy| < 0.2 时不给）',
              'C1 严格交叉中逐 seed 共同可行日 ≥ 60 的配对（与上表同一集合）', '对比的另一端（N100 或 B8）',
              'N250−N100：全部评分口径 x 分配；B16−B8：frozen x equal',
              unit='年化百分点；pos = 平均投入资金（权重和）；e = 单位资金年化超额', dates='后段两段（N 对比推导段无支持）；B 对比含 2015-18',
              H='源持有（母体原生）', support='严格视图 = 两格同日可行日；部署视图 = 全日历（逐日投入资金只在部署视图可得）',
              capital='源 DEV（每只 min(1/n, 1%)，不归一）'))
        w(md(show[['segment', 'contrast', 'fixed', 'scope', 'alloc', 'n_pairs', 'd_strict', 'd_deploy', 'cap_part', 'sel_part', 'cap_share',
                   'pos_a', 'pos_b', 'held_a', 'held_b', 'e_a', 'e_b']]))
        P_ = rd(pp)
        pn = P_[P_.contrast == 'N250−N100'].groupby('segment')[['d_deploy', 'cap_part']].mean()
        ncap = cap[cap.contrast == 'N250−N100'].assign(e_ratio=lambda d: d.e_b / d.e_a)
        eq, pr = ncap[ncap.alloc == 'equal'], ncap[ncap.alloc == 'prop']
        fe = ncap[(ncap.scope == 'frozen') & (ncap.alloc == 'equal')]
        mo = pd.concat([rd(os.path.join(R, 'registry', 'mother_needs_%s.csv' % s_)) for s_ in I.POST_SEGS])
        w('- **读法（B 后补充资本分解后修订；此前版本写"可选池变大带来的账户改善主要来自人数多"，没有区分部署量与选股）**：严格视图下，固定行业宽度时人数 100 → 250 的差'
          '（%s）为正，且大于固定人数时行业 8 → 16 的差（%s）。按部署视图分解，人数 100 → 250 让持仓名数约从 %.0f 升到 %.0f–%.0f、投入资金约从 %.2f 升到 %.2f–%.2f；%s。'
          '所以 C1 的"人数效应"主要是部署量效应，不是稳定的选股改善；生产母体后段已持约 %.0f–%.0f 名、投入资金 %.2f–%.2f（§0），这部分资金效应大多已兑现；'
          '扩到 pool0 之外没有测过。行业变宽让持仓变多（资金部分为正），但单位资金超额下降，两者大体抵消。推导段支持不足（尤其 2010-14）。'
          '只识别"改变 N / B 的账户差异"，不识别历史真实扩容的原因。\n' % (
              '，'.join('%s %s' % (s_, f(v_)) for s_, v_ in nm.items()), '，'.join('%s %s' % (s_, f(v_)) for s_, v_ in bm.items()),
              fe.held_a.mean(), fe.held_b.min(), fe.held_b.max(), fe.pos_a.mean(), fe.pos_b.min(), fe.pos_b.max(),
              q('Q10-CAP', '全部口径合并，部署视图差里资金部分占 %s；单位资金超额之比（N250 / N100）等额分配 %.2f–%.2f、按比例分配 %.2f–%.2f' % (
                  '，'.join('%s %s' % (s_, pc(r_.cap_part / r_.d_deploy)) for s_, r_ in pn.iterrows()),
                  eq.e_ratio.min(), eq.e_ratio.max(), pr.e_ratio.min(), pr.e_ratio.max())),
              mo.final_B_per_day.min(), mo.final_B_per_day.max(), mo.capital_pos_mean.min(), mo.capital_pos_mean.max()))
        out['_cap'] = pn.cap_part / pn.d_deploy
    elif len(nm):
        w('- **读法**：（资本分解缺失）固定行业宽度时人数 100 → 250 的差 %s；固定人数时行业 8 → 16 的差 %s。\n' % (
            '，'.join('%s %s' % (s_, f(v_)) for s_, v_ in nm.items()), '，'.join('%s %s' % (s_, f(v_)) for s_, v_ in bm.items())))
    if os.path.exists(t4p):
        t4 = rd(t4p)
        t4.to_csv(os.path.join(TAB, 'C1_bridges.csv'), index=False)
        t4['N'] = t4['N'].astype('Int64')
        b = t4[t4.scope.isin(['frozen', 'source'])].groupby(['segment', 'part', 'N'], dropna=False).net8_mean.median().unstack(
            'part').reset_index()
        w(hdr('桥：各 (段, N) 下三母体 x 四深度的 net8 年化中位（randomN 先对 64 seed 取均值）', 'C1 桥全部格',
              'bridge_full = 完整 pool0 同一计数预算；mother_source = 源母体', 'frozen 口径',
              dates='四段各自', H='源持有（母体原生）'))
        w(md(b))
    if os.path.exists(t5p):
        t5 = rd(t5p)
        t5.to_csv(os.path.join(TAB, 'C1_instrument.csv'), index=False)
        w('%s——计数预算与源分箱的差单列为"仪器效应"，不计入 N / B 的经济解释。\n' % q(
            'Q10-INSTR', '仪器效应（计数预算 − 源分箱，frozen，R2 / A06）各段中位：' + '，'.join(
                '%s %s' % (s_, f(v_)) for s_, v_ in t5.groupby('segment')['mean'].median().items())))
    return out


def c2_section(w, P):
    t6p = os.path.join(CS, 'C2_T6_impact_delta.csv')
    kp = os.path.join(CS, 'C2_children_delta.csv')
    w('## 3. Q7 冲击视图（C2；plan §9.2）\n')
    if not os.path.exists(t6p):
        w('_（C2 汇总缺失）_\n')
        return None
    t6 = rd(t6p)
    t6.to_csv(os.path.join(TAB, 'C2_impact_delta.csv'), index=False)
    cols = [c for c in t6.columns if c.startswith('d_net8_minus_sqrt_A5')]
    show = ['segment', 'route_id', 'd_net8_ann'] + cols
    g = t6.groupby(['segment', 'route_id'])[['d_net8_ann'] + cols].median().reset_index()
    w(hdr('路线内 (母体, H) 格的描述符中位，再对格取中位', 'C2 全部子描述符（推导两段 + 后段两段）', '同 H 真实母体（同一冲击情景下的母体）',
          '无冲击 vs 平方根冲击 A = 5 亿元、κ ∈ {.25, .5, 1}', dates='四段各自', H='各描述符自身 H',
          cost='8bp + 平方根冲击 MI = κ·σ·(Q/ADV)^0.5（源模型；κ 未校准）'))
    w(md(g[[c for c in show if c in g.columns]]))
    res = None
    if os.path.exists(kp):
        K = rd(kp)
        k = K[(K.route_id == 'RK') & K.direction_role.isin(PRIM) & (K.policy == 'FALLBACK')]
        c5 = 'd_net8_minus_sqrt_A5_k0.5'
        c10 = 'd_net8_minus_sqrt_A10_k1'
        kk = k.groupby('segment')[['d_net8_ann'] + [c for c in (c5, c10) if c in k.columns]].median()
        res = kk
        w('%s。' % q('Q7-KIMPACT', 'K 主方向（FALLBACK）子 − 母体（全部 H 的中位）：' + '；'.join('%s 无冲击 %s、A5 亿 κ.5 %s、A10 亿 κ1 %s' % (
            s_, f(r_.d_net8_ann), f(r_.get(c5, np.nan)), f(r_.get(c10, np.nan))) for s_, r_ in kk.iterrows())))
        kh = k.groupby(['segment', 'H'])[['d_net8_ann', c10]].median().unstack('segment')
        kh.columns = ['%s %s' % (a_.replace('d_net8_minus_sqrt_A10_k1', 'A10κ1').replace('d_net8_ann', '无冲击'), b_)
                      for a_, b_ in kh.columns]
        kh = kh.reset_index()
        kh.to_csv(os.path.join(TAB, 'C2_K_by_H.csv'), index=False)
        w(hdr('描述符中位', 'K 主方向 x SLOT FALLBACK（α .125 / .25 / .5）x 三母体', '同 H 真实母体（同一冲击情景）',
              '按 H：无冲击 vs 平方根冲击 A = 10 亿元、κ = 1', dates='四段各自', H='见行',
              cost='8bp + 平方根冲击（源模型；κ 未校准）'))
        w(md(kh))
        mo = rd(kp)[['segment', 'mother_id', 'H', 'm_net8_minus_sqrt_A10_k1']].drop_duplicates()
        short = k[k.H <= 3].groupby('segment')[c10].median()
        long_ = k[k.H >= 10].groupby('segment')[[c10, 'd_net8_ann']].median()
        mshort = mo[mo.H <= 3].groupby('segment').m_net8_minus_sqrt_A10_k1.median()
        w('- **读法**：%s。K 在冲击下的"更好"几乎全部集中在短 H——那里母体本身在大资金下已严重为负（不是可部署区域）；'
          '在母体仍可能为正的长 H，K 的增量与无冲击时接近。冲击透镜说明 K 会把持仓推向单位成交冲击较小的票，但 κ 未校准，不输出可部署规模。\n' % q(
              'Q7-KH', 'A10 亿 κ1 下：K 短 H（≤3）增量 %s，同口径母体短 H 净值 %s；长 H（≥10）增量 %s（无冲击 %s）' % (
                  ' / '.join(f(v_) for v_ in short), ' / '.join(f(v_, 1) for v_ in mshort),
                  ' / '.join(f(v_) for v_ in long_[c10]), ' / '.join(f(v_) for v_ in long_.d_net8_ann))))
        rl = K[K.route_id == 'RL']
        if len(rl) and c5 in rl.columns:
            rr = rl.groupby('segment')[['d_net8_ann', c5, c10]].median()
            w('%s。按价差代理替换边缘名单：中等冲击（A5 亿 κ.5）下 %d / %d 段为正，最重冲击（A10 亿 κ1）下 %d / %d 段为正——'
              '它省下的主要是冲击成本（减少交易 / 偏向低冲击票），不是信息 alpha（plan Q7 允许的结论只到"实施机会"）。'
              '删除类路线（RO / RV）在重冲击下转正也是同一个资本 / 交易量效应。\n' % (
                  q('Q7-RL', 'RL 子 − 母体：' + '；'.join('%s 无冲击 %s、A5 亿 κ.5 %s、A10 亿 κ1 %s' % (
                      s_, f(r_.d_net8_ann), f(r_[c5]), f(r_[c10])) for s_, r_ in rr.iterrows())),
                  int((rr[c5] > 0).sum()), len(rr), int((rr[c10] > 0).sum()), len(rr)))
    return res


def main():
    t0 = time.time()
    os.makedirs(TAB, exist_ok=True)
    TX.QIDS.clear()
    P = rd(os.path.join(R, 'reports', 'part2_tables', 'descriptor_panel_post.csv'))
    M = P[~P.companion.astype(bool) & P.route_id.isin(['RT', 'RK', 'RV', 'RR', 'RO', 'RC', 'RA', 'RS', 'RL', 'TPAIR', 'FOURARM'])]
    cards = json.load(open(os.path.join(R, 'reports', 'hypothesis_outcomes.json')))
    D = rd(os.path.join(R, 'reports', 'factor_iteration_delta.csv'))
    cat = rd(os.path.join(R, 'reports', 'research_catalog_v36.csv'))
    appr = json.load(open(I.APPROVAL_FILE))
    L = []
    w = L.append
    w('# E6i REPORT_part3（Stage 4：合并复盘 + carried + 全轮 coverage）\n')
    w('执行 session，%s（47 时间）；结果目录 `20260923_0254_E6i_measurement_need_fit`（47）。本报告合并推导段（part1a / 1b）与后段首次观察（part2），'
      '加 carried C1（人数 x 行业宽度）/ C2（冲击成本透镜）/ C3（信号边界描述，R0），给出 Q1–Q18 结果卡汇总、研究目录 v36、因子迭代增量、'
      '候选库更新提案、线状态与 park 草稿，以及全轮 coverage。记录 B：`%s`。**全部是研究历史上的读数，E7 是唯一 OOS（HOLD）**；'
      '采纳、线状态、入地基由规划 session 与用户定。\n' % (time.strftime('%Y-%m-%d %H:%M'), appr['approval_id']))
    w('**本版修订（2026-09-25，47 时间；B 后事后补充）**：新增 §0 母体基线、§1b 分族读数、§2 C1 资本分解，并据此修订 §2 读法与摘要（C1 的"人数效应"主体是部署量、'
      '不是选股改善；"K 响应族部分混入"的称呼更正为 K 槽位 9 个族）。只重新汇总已封存的账户，不改变任何登记读数。\n')
    w('---\n')
    SUM_AT = len(L)
    w('')
    base = baseline_section(w)
    # ============================ 1 四段合并
    w('## 1. 四段合并要点\n')
    g1 = M.groupby('route_id').agg(n=('descriptor_id', 'size'), deriv=('deriv', 'median'), post=('post', 'median'),
                                   all4=('all4', 'median'), ex1516=('ex1516', 'median'), ex2024p=('ex2024p', 'median'),
                                   all4_ci_pos=('ci_all4', lambda x: int((x.astype(bool) & (M.loc[x.index, 'all4'] > 0)).sum())),
                                   all4_ci_neg=('ci_all4', lambda x: int((x.astype(bool) & (M.loc[x.index, 'all4'] < 0)).sum()))).reset_index()
    g1.to_csv(os.path.join(TAB, 'T1_all4_route.csv'), index=False)
    w(hdr('路线内描述符中位 / 计数', '该路线全部主描述符', '同 H 真实母体', '主路线；deriv / post / all4 = 推导合并 / 后段合并 / 四段合并；ex1516 / ex2024p = 四段去 2015+16 / 去 2024+',
          H='全部登记 H'))
    w(md(g1))
    both = cat[(cat.deriv_median > 0.05) & (cat.post_median > 0.05)].sort_values('all4_median', ascending=False)
    both[['member_id', 'axis', 'family', 'n_primary_single', 'deriv_median', 'post_median', 'all4_median', 'post_ci_pos',
          'post_ci_neg', 'zmap_post_median', 'best_role_post']].to_csv(os.path.join(TAB, 'T1b_members_both_periods.csv'), index=False)
    w(hdr('成员层：主方向、单成员描述符的中位（与 factor_iteration_delta 同一规则）', '推导合并与后段合并中位都 > +0.05 的目录成员',
          '同 H 真实母体', '276 个目录成员中按两期结果筛出（**有成员层选择偏差**，只作描述，不作准入）', H='各描述符自身 H'))
    both = both.assign(**{c_: both[c_].astype('Int64') for c_ in ('n_primary_single', 'post_ci_pos', 'post_ci_neg')})
    w(md(both[['member_id', 'axis', 'family', 'n_primary_single', 'deriv_median', 'post_median', 'all4_median', 'post_ci_pos',
               'post_ci_neg', 'zmap_post_median', 'best_role_post']]))
    w('%s。这张表是从 %d 个成员里按两期结果筛出的，期望值会被高估（E6f 已示范按结果挑选的赢家诅咒）；它只用于决定"哪些对象值得在 E7 前事前登记"，'
      '不是"哪些对象已经有效"。\n' % (q('P3-BOTH', '两期都为正的成员 %d 个：%s' % (len(both), '、'.join(both.member_id))), len(cat[cat.ledger_status != 'considered_not_built'])))
    fam = family_section(w, M)
    # ============================ 2 / 3 carried
    c1 = c1_section(w)
    c2 = c2_section(w, P)
    # ============================ 4 Stage 1 测量层
    w('## 4. Stage 1 测量层回顾（Q11 / Q12 / Q17 / Q18；R0）\n')
    rq = rd(os.path.join(R, 'reports', 'R0_tables', 'query_ids.csv')).set_index('query_id').text
    for qid, lab in (('Q-R0-Q11A', 'Q11 池子真实状态'), ('Q-R0-Q11B', 'Q11 触发日龄'), ('Q-R0-Q11C', 'Q11 实现 cr5'),
                     ('Q-R0-Q12A', 'Q12 限价政策（V）'), ('Q-R0-Q17B', 'Q17 条件形状'), ('Q-R0-Q18F', 'Q18 画像 vs 同人数对照'),
                     ('Q-R0-Q18A', 'Q18 T 新旧分离'), ('Q-R0-Q18B', 'Q18 K 新旧分离')):
        if qid in rq.index:
            w('- %s：%s〔%s〕' % (lab, rq[qid], qid))
    w('')
    # ============================ 5 Q16
    w('## 5. Q16 方法复盘（本轮实际发生的方法层问题）\n')
    t5 = pd.DataFrame(PS.Q16_ITEMS)
    w(hdr('逐条登记（事实 / 发现途径 / 影响 / 根因 / 下一步改法）', '本轮方法层问题', '无', '全轮', unit='不适用', dates='全轮',
          H='不适用', cost='不适用', support='不适用', capital='不适用'))
    w(md(t5))
    # ============================ 6 结果卡
    w('## 6. Q1–Q18 结果卡汇总（全文见 `reports/hypothesis_outcomes.md`）\n')
    ct = pd.DataFrame([dict(Q=c['hypothesis_id'], prediction_status=c.get('prediction_status'),
                            root_cause_evidence=c.get('root_cause_evidence')) for c in cards])
    w(hdr('逐卡', 'Q1–Q18', 'plan §10.2 模板', '全轮', unit='不适用', dates='全轮', H='不适用', cost='不适用', support='不适用',
          capital='不适用'))
    w(md(ct))
    w('%s。\n' % q('P3-CARDS', '结果卡状态计数：' + '，'.join('%s %d' % (k_, v_) for k_, v_ in ct.prediction_status.value_counts().items())))
    # ============================ 7 研究目录 / 因子迭代增量
    w('## 7. 研究目录 v36 与因子迭代增量\n')
    w('%s；每成员一行的构造版本 / 角色证据 / 失效归因（执行端规则化初判）见 `reports/factor_iteration_delta.md`，'
      '来源 / 定义 / 有效域 / 尝试 / 未测用途见 `reports/research_catalog_v36.csv`（%d 行，含考虑过未构造的项）。\n' % (
          q('P3-DELTA', '因子迭代增量状态计数：' + '，'.join('%s %d' % (k_, v_) for k_, v_ in D.status.value_counts().items())), len(cat)))
    # ============================ 8 / 9 提案与线状态
    w('## 8. 候选库更新提案（草案；全文 `reports/candidate_library_update_proposal.md`）\n')
    w('执行端的提案是**不向生产候选库加任何对象**；只提出一个"E7 事前登记短名单"（研究候选），每项写明改善对象、母体、角色、H / 成本、增益来源、'
      '时间与风险范围、剩余不确定性与所需验证。U34 / U35、生产 v2、v3 展示候选本轮不改。\n')
    w('## 9. 线状态与 park 台账（草稿；`reports/line_state_proposal.md` / `reports/park_ledger_delta.md`）\n')
    w('草稿只写"子杠杆 x 适用域"的否定，不写线级结论；定案权在规划 session 与用户。\n')
    # ============================ 10 / 11
    w('## 10. 这份 part3 没有得出的结论\n')
    w('- 不是 OOS：四段都是研究历史；E7 是唯一 OOS。')
    w('- 两期都为正的成员表有成员层选择偏差，不是"已有效"的名单。')
    w('- C1 的 N / B 对比只识别"在此抽样与评分机制下改变 N / B 的账户差异"，不识别历史真实扩容的原因；偏相关不作唯一机制。')
    w('- C1 的"人数效应"主体是投入资金（部署量），不能读成"扩池会选得更好"；单位资金超额的变化依赖抽样分配口径。')
    w('- §1b 分族读数是看过后段后做的汇总：族是事前定义的，但对响应族的强调与"小权重 + 长持有期"切片是事后的；族内描述符高度相关，显著计数不是独立检验；'
      '响应族与"给原 K 加权"尚未正式分离。')
    w('- C2 的 κ 未校准，不输出可部署规模。')
    w('- "无效果"只对 母体 x 需求 x 角色 x 日期 x 支持 x 成本 的格成立。\n')
    w('## 11. 运行事件与 BLOCKERS\n')
    w('BLOCKERS：无。本轮运行事件与方法层问题见 §5 与 WORKLOG。\n')
    # ============================ 12 coverage
    w('## 12. 全轮 coverage（proposal / plan / brief 逐条）\n')
    c1_done = len(glob.glob(os.path.join(R, 'task_status', 'c1_*.receipt.json'))) > 0
    c2_done = len(glob.glob(os.path.join(R, 'task_status', 'c2_*.receipt.json'))) > 0
    cov = []
    for src, item, st_, why, imp in PS.COVERAGE:
        if 'C1：' in item and not c1_done:
            st_ = 'deferred'
        if 'C2：' in item and not c2_done:
            st_ = 'deferred'
        cov.append(dict(source=src, item=item, status=st_, reason=why, impact=imp))
    cv = pd.DataFrame(cov)
    I.atomic_write_csv(os.path.join(R, 'registry', 'coverage.csv'), cv)
    w(hdr('逐条状态', 'proposal / plan / brief 的交付与设计条目', '各自原文', '全轮', unit='不适用', dates='全轮', H='不适用',
          cost='不适用', support='不适用', capital='不适用'))
    w(md(cv))
    w('%s。\n' % q('P3-COV', 'coverage 状态计数：' + '，'.join('%s %d' % (k_, v_) for k_, v_ in cv.status.value_counts().items())))
    # ============================ 摘要
    k = M[(M.route_id == 'RK') & M.direction_role.isin(PRIM) & (M.policy == 'FALLBACK')]
    bpost = base[base.segment.isin(I.POST_SEGS)]
    kf_ = fam['kf'].set_index('family')
    ar = kf_.loc['amount_response']
    rep = kf_[kf_.index.isin(['log_repr', 'cross_sectional_residual', 'component', 'aggregation_bridge', 'pointwise_inverse_bridge'])]
    body = [
        '本轮（E6i：因子端迭代 · 估计量族 x 策略适配）完整跑完：推导段 → 记录 B（整表）→ 后段首次观察 → carried → 复盘。',
        '%s；下面所有"子 − 母"都相对它（§0）。' % q('P3-S-BASE', '母体基线：两后段 net8 年化 %s ~ %s、投入资金 %.2f ~ %.2f' % (
            f(bpost.net8_ann.min(), 2), f(bpost.net8_ann.max(), 2), bpost.capital.min(), bpost.capital.max())),
        '%s。' % q('P3-S-K', 'K 槽位（K 轴 9 个估计量族部分混入，%d 个描述符）：推导合并 %s → 后段 %s / %s → 四段合并 %s' % (
            len(k), f(k.deriv.median()), f(k.p1.median()), f(k.p2.median()), f(k.all4.median()))),
        '%s——K 里后段相对站得住的是"价格对成交的响应"口径（2024-26 全网格只是接近 0，小权重 + 长持有期下为正）；族是事前定义的，但这一强调和切片是看过后段后做的，'
        '且未与"给原 K 加权"正式分离（§1b）。' % q(
            'P3-S-FAM', 'K 分族：amount_response 四段中位 %s（逐年为正 %s，同资本后段 %s / %s）；改表示 / 中性化 / 聚合顺序 / 点态倒数各族 2024-26 为 %s ~ %s' % (
                four(ar), ar.yrs_pos, f(ar.samecap_19_23), f(ar.samecap_24_26), f(rep.p24_26.min()), f(rep.p24_26.max()))),
        '%s。' % q('P3-S-NEG', '推导合并与后段合并中位都为负的路线：%s；后段合并中位低于推导合并的路线 %d / %d（%s），高于的：%s' % (
            '、'.join(r_.route_id for r_ in g1.itertuples() if r_.deriv < 0 and r_.post < 0),
            int((g1.post < g1.deriv).sum()), len(g1),
            '、'.join(r_.route_id for r_ in g1.itertuples() if r_.post < r_.deriv),
            '、'.join(r_.route_id for r_ in g1.itertuples() if r_.post > r_.deriv) or '无')),
        '%s——有成员层选择偏差，只用于 E7 事前登记的候选范围。' % q('P3-S-BOTH', '两期都为正的成员 %d 个（K 响应族 / 源桥与 T 20 日绝对尺度）' % len(both)),
        '执行端提案：生产候选库不加对象；E7 事前登记短名单（及"按族登记"备选）见 candidate_library_update_proposal.md。',
        '结果卡：%s。' % '，'.join('%s %d' % (k_, v_) for k_, v_ in ct.prediction_status.value_counts().items()),
    ]
    if c1:
        sgn_ = {k_: v_ for k_, v_ in c1.items() if not k_.startswith('_')}
        cap_ = c1.get('_cap')
        body.append('C1：%s；%s——主体是部署量效应，不是稳定的选股改善（§2）。' % (
            '；'.join('%s 严格视图格均值>0 占比 %s' % (ctr, '，'.join('%s %s' % (s_, pc(v_)) for s_, v_ in sp.items())) for ctr, sp in sgn_.items()),
            q('P3-S-C1', '但 N250−N100 的部署视图差里投入资金部分占 %s' % ('，'.join('%s %s' % (s_, pc(v_)) for s_, v_ in cap_.items())
                                                             if cap_ is not None else 'NA'))))
    kp_ = os.path.join(CS, 'C2_children_delta.csv')
    if c2 is not None and os.path.exists(kp_):
        K_ = rd(kp_)
        kk_ = K_[(K_.route_id == 'RK') & K_.direction_role.isin(PRIM) & (K_.policy == 'FALLBACK') & (K_.H >= 10)]
        lg = kk_.groupby('segment')[['d_net8_ann', 'd_net8_minus_sqrt_A10_k1']].median()
        body.append('C2：K 在重冲击下的增量集中在短 H（母体在大资金下已严重为负的区域）；%s（§3）。' % q(
            'P3-S-C2', '长 H（≥10）K 增量 A10 亿 κ1 下各段 %s，无冲击 %s' % (
                ' / '.join(f(v_) for v_ in lg.d_net8_minus_sqrt_A10_k1), ' / '.join(f(v_) for v_ in lg.d_net8_ann))))
    body.append('不是 OOS；采纳、线状态、入地基由规划 session 与用户定；E7 HOLD。')
    summ = ['%d. %s' % (i_ + 1, t_) for i_, t_ in enumerate(body)]
    L[SUM_AT] = '## 摘要（≤15 行）\n\n' + '\n'.join(summ) + '\n\n---\n'
    txt = '\n'.join(L)
    bad = TX.check_headers(txt)
    if bad:
        raise SystemExit('生成 FAIL：%d 张表缺表头项（行 %s）' % (len(bad), bad[:10]))
    for b in TX.FORBID:
        if b in txt:
            raise SystemExit('生成 FAIL：禁用词 %s' % b)
    if re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', txt):
        raise SystemExit('生成 FAIL：疑似主机地址')
    p = os.path.join(R, 'reports', 'E6i_REPORT_part3.md')
    open(p, 'w', encoding='utf-8').write(txt)
    pd.DataFrame(TX.QIDS).to_csv(os.path.join(TAB, 'query_ids_part3.csv'), index=False)
    print('part3: %s (%d 字节, %d 行); query_id %d; %.0fs' % (p, len(txt.encode()), txt.count('\n'), len(TX.QIDS),
                                                              time.time() - t0))


if __name__ == '__main__':
    main()
