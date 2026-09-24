#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i hypothesis_outcomes.md (brief §9; plan §10.2 结果卡模板, 每 Q 一张)。
计算字段 (对象 / 日期 / 母体 / 算子 / 推导段与后段主读数 / 不确定性 / δ 尺度 / 分解) 全部由 part2 面板与统计表现算;
判断字段 (prediction_status / root_cause_evidence / 未测 / 不能得出 / 下一步设计 / 理由 / 所需新信息) 取自
e6i_outcome_judgments.J (执行端读法, 规划 session 复核)。输出 reports/hypothesis_outcomes.md + .json。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import json
import time
import hashlib

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_outcome_judgments as OJ

R = I.RES
PRIM = ('primary', 'primary_inverse_mapped')
DER_DATES = '2010-01-04..2018-12-28（推导两段）'


def mask(s):
    """引用预登记原文时, 原文里"不得写成……"所列的禁用词不复述 (其余逐字)。"""
    s = str(s)
    for b in ('可交付', '已确证', '必须换核', '饱和', '穷尽', '到平台'):
        s = s.replace(b, '〔禁用词，原文不复述〕')
    return s


def prereg_fields(meta):
    """A0 登记字段 -> 卡片的四个引用字段。Q1–Q16 的 A0 把动机 / 问题 / 竞争机制合为一栏;
    Q17 / Q18 是规划 session 补充, 只有一段 text (问题？读法 = …；备择 = …；边界)。"""
    if 'text' in meta:
        t = str(meta['text'])
        q, _, rest = t.partition('读法 = ')
        rd, _, alt = rest.partition('；备择 = ')
        return dict(source_fact='A0 登记的补充问题（source = %s）' % meta.get('source', ''),
                    competing_mechanisms=mask(q.split('：', 1)[-1]),
                    chosen_contrast=mask(rd), expected_pattern=mask('备择 = ' + alt if alt else ''))
    return dict(source_fact='（A0 登记把动机 / 问题 / 竞争机制合为一栏，见下一项）',
                competing_mechanisms=mask(meta.get('motivation_question_competing', '')),
                chosen_contrast=mask(meta.get('experiment_primary_reading', '')),
                expected_pattern=mask(meta.get('allowed_and_forbidden', '')))


def fx(x, nd=3):
    return ('%+.' + str(nd) + 'f') % x if np.isfinite(x) else 'NA'


def scope_sets(P):
    s = pd.to_numeric(P.strength, errors='coerce')
    return {
        'Q1': ('RT 主方向小权重加（FALLBACK α .125/.25）', P[(P.route_id == 'RT') & (P.direction_role == 'primary') &
                                                        (P.policy == 'FALLBACK') & s.isin([0.125, 0.25])]),
        'Q2': ('RK 主方向部分混入（FALLBACK α .125/.25/.5）', P[(P.route_id == 'RK') & P.direction_role.isin(PRIM) &
                                                           (P.policy == 'FALLBACK')]),
        'Q3': ('RV 主方向删除 / 缩减（VETO_NEW / SOFT / SOFT_HARD）', P[(P.route_id == 'RV') & (P.direction_role == 'primary') &
                                                                 P.role.isin(['VETO_NEW', 'SOFT', 'SOFT_HARD'])]),
        'Q4': ('RO 保留集删除（高值端）', P[(P.route_id == 'RO') & (P.direction_role == 'high_role')]),
        'Q5': ('RR 同人数 SWAP（两个域）', P[(P.route_id == 'RR') & (P.role == 'SWAP')]),
        'Q6': ('RC 主方向（核心槽位 + 焦点替换 new）', P[(P.route_id == 'RC') & (P.direction_role == 'primary')]),
        'Q7': ('RL 边缘成本替换 + 轻摩擦否决', P[P.route_id == 'RL']),
        'Q8': ('M1 共识（非伴随）', P[(P.route_id == 'M1') & ~P.companion.astype(bool)]),
        'Q9': ('全部主路线描述符', P[P.route_id.isin(['RT', 'RK', 'RV', 'RR', 'RO', 'RC', 'RA', 'RS', 'RL', 'TPAIR', 'FOURARM'])]),
        'Q13': ('RA 同预算换入（SWAP，两种换出规则）', P[(P.route_id == 'RA') & (P.role == 'SWAP')]),
        'Q14': ('RS 状态内条件 SWAP', P[(P.route_id == 'RS') & (P.role == 'SWAP')]),
        'Q15': ('四臂（全部臂）', P[P.route_id == 'FOURARM']),
    }


def computed(g, q):
    ci_p = g.ci_post.astype(bool)
    ci_d = g.ci_deriv.astype(bool)
    sw = g.state_post.value_counts()
    rows = dict(
        actual_members='%d 个成员 / %d 个描述符' % (g.member_id.nunique(), len(g)),
        actual_dates='%s；后段 2019-01..2026-03-27（两段）' % DER_DATES,
        mother='、'.join(sorted(g.mother_id.astype(str).unique())),
        operator='、'.join(sorted(g.role.astype(str).unique())),
        costs='8bp 线性（主）；net12 解析；冲击见 C2（part3 §3）',
        support='各段有效日、段间不拼接；同 H 真实母体逐日配对',
        primary_estimate='推导合并中位 %s；后段两段中位 %s / %s（后段合并 %s）；四段合并 %s' % (
            fx(g.deriv.median()), fx(g.p1.median()), fx(g.p2.median()), fx(g.post.median()), fx(g.all4.median())),
        uncertainty='NW(lag H) 95%% 区间排除 0：推导 正 %d / 负 %d；后段合并 正 %d / 负 %d（每侧随机约 %.0f）；后段 MDE80 中位 %s' % (
            int((ci_d & (g.deriv > 0)).sum()), int((ci_d & (g.deriv < 0)).sum()), int((ci_p & (g.post > 0)).sum()),
            int((ci_p & (g.post < 0)).sum()), 0.025 * len(g), fx(g.mde_post.median())),
        practical_scale='后段合并状态词（δ = 0.25）：' + '，'.join('%s %d' % (k, v) for k, v in sw.items()),
        decomposition='后段两段：同人数核心 %s / %s，同资本 %s / %s，真实−匹配随机 %s / %s；Δgross %s / %s' % (
            fx(g.dcore_ann_1.median()), fx(g.dcore_ann_2.median()), fx(g.dsamecap_ann_1.median()),
            fx(g.dsamecap_ann_2.median()), fx(g.z1.median()), fx(g.z2.median()),
            fx(g.d_gross_ann_1.median()) if 'd_gross_ann_1' in g else 'NA',
            fx(g.d_gross_ann_2.median()) if 'd_gross_ann_2' in g else 'NA'))
    return rows


def main():
    t0 = time.time()
    P = pd.read_csv(os.path.join(R, 'reports', 'part2_tables', 'descriptor_panel_post.csv'), low_memory=False)
    H = json.load(open(os.path.join(R, 'registry', 'hypotheses_A0.json')))
    qs = {x['q']: x for x in H['questions']}
    pre = hashlib.sha256(open(os.path.join(R, 'preregistration.md'), 'rb').read()).hexdigest()
    extra = getattr(OJ, 'EXTRA', {})
    sets = scope_sets(P)
    cards = []
    md = ['# E6i hypothesis_outcomes（Q1–Q18 结果卡；plan §10.2 模板）\n',
          '计算字段由 `e6i_hypothesis_outcomes.py` 现算（part2 面板 / 统计表 / carried 汇总 / R0 query）；判断字段是执行端读法（`e6i_outcome_judgments.py`），'
          '定案权在规划 session 与用户。"预测反向"不是"必须丢掉因子"；"信息不足"也不是永远继续的理由（plan §10.2）。preregistration sha `%s…`。\n' % pre[:12]]
    for q in ['Q%d' % i for i in range(1, 19)]:
        meta = qs.get(q, {})
        j = OJ.J.get(q)
        card = dict(hypothesis_id='E6i-%s' % q, motive_id='plan §10 %s（%s）' % (q, meta.get('label', '')),
                    preregistration_hash=pre[:12],
                    exposure_class=('推导段（A0 登记后）+ 后段首次观察（记录 B）' if q in sets else
                                    ('推导段 + 旧输入后段封存格（B 后读取）' if q == 'Q10' else 'Stage 1 推导段 / 方法层')),
                    **prereg_fields(meta))
        if q in sets:
            label, g = sets[q]
            card['scope'] = label
            card.update(computed(g, q))
        if q in extra:
            card.update(extra[q])
        if j:
            card.update(prediction_status=j['prediction_status'], root_cause_evidence=', '.join(j['root_cause_evidence']) or '—',
                        root_note=j['root_note'], what_was_not_tested=j['what_was_not_tested'],
                        what_cannot_be_concluded=j['what_cannot_be_concluded'], next_design_change=j['next_design_change'],
                        why_it_addresses_the_failure=j['why'], new_information_needed=j['new_information_needed'])
        else:
            card.update(prediction_status='untested', root_cause_evidence='unknown', root_note='（判断待写）')
        cards.append(card)
        md.append('## %s %s\n' % (q, meta.get('label', '')))
        for k, v in card.items():
            md.append('- **%s**：%s' % (k, v))
        md.append('')
    tab = pd.DataFrame([dict(Q=c['hypothesis_id'], status=c.get('prediction_status'), root=c.get('root_cause_evidence'))
                        for c in cards])
    md.insert(2, '| 卡 | prediction_status | root_cause_evidence |\n|---|---|---|\n' + '\n'.join(
        '| %s | %s | %s |' % (r.Q, r.status, r.root) for r in tab.itertuples()) + '\n')
    txt = '\n'.join(md) + '\n'
    for b in ('可交付', '已确证', '必须换核', '饱和', '穷尽', '到平台'):
        if b in txt:
            raise SystemExit('禁用词 %s' % b)
    open(os.path.join(R, 'reports', 'hypothesis_outcomes.md'), 'w', encoding='utf-8').write(txt)
    I.atomic_write_json(os.path.join(R, 'reports', 'hypothesis_outcomes.json'), cards)
    print('hypothesis_outcomes: %d 张卡; status %s; %.0fs' % (len(cards), tab.status.value_counts().to_dict(),
                                                              time.time() - t0))


if __name__ == '__main__':
    main()
