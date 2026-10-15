# -*- coding: utf-8 -*-
"""E6n Stage B 冻结、A1-auto、记录 B（brief §4 / §5 S3、W02 / W10 / W11、A2 / A9 / A12；附录 C / D；e6m_s_stage_b 同构）。不读任何收益。
  queries    registry/query_registry_E6n.csv + reports_skeleton/queries/<qid>.csv（每 query 一张骨架，表头固定 + status 行）
  stage-b    registration/{cards_stageB_E6n, claims_E6n, source_claim_reconciliation, hypothesis_lineage, idea_ledger_G, execution_ledger_E,
             exposure_ledger}.csv；registration/policy_profiles_E6n.json（E6m 转录件 + 本轮新增条款）；registry/{b2,b3}_manifest_E6n.csv；
             reports/SCHEMA.md 骨架（计划表 + 预期列；交付时由 e6n_deliver 按实测刷新）
  a1auto     registration/a1_auto_E6n.{csv,json}（E6m ⑬–⑳ 同类 + 本轮 ㉑–㉘；任一 FAIL 阻断 B 草稿）
  freeze     registration/stageB_freeze_E6n.json（P / B 两包 = registry + 登记文档 sha）+ 方式 B：record_B_preauthorized_E6n.json（照录用户原话 + 日期 + 冻结 sha）
  conditions registration/record_B_conditions_receipt_E6n.json（Stage 0 全 PASS ∧ A1-auto 全 PASS ∧ seal_B1_0 ∧ seal_deriv ∧ 冻结 sha 不变）"""
import os
import re
import sys
import json
import glob
import time
import argparse

import numpy as np
import pandas as pd

import e6n_core as N

E6M_W = N.E6M_WORK
CARD_FEATURE = {'H03': ('PL_REL20',), 'H04': ('Q_PATH', 'Q_RV', 'Q_RANGE'), 'H05': ('TAIL_PUSH',), 'H06': ('TAIL_VOL_REL20', 'JSD_PROFILE20'),
                'H07': ('Q_CLOSE_THIN', 'Q_CLOSE_LEVEL'), 'H08': ('RV_REL20', 'K_RANGE_SOURCE', 'CLV20_SOURCE'), 'H11': ('Q_BOTH',)}
B1_MEMBER_OF = {'H03': ('PL_REL20_f5', 'PL_5'), 'H04': ('h_path_f5', 'sqrtRV_f5', 'log_hl'), 'H05': ('TAIL_PUSH', 'L_TAIL'), 'H06': ('TAIL_VOL_REL20', 'S_TAIL', 'JSD_PROFILE20'),
                'H07': ('h_close', 'u_close'), 'H08': ('RV_REL20_f5', 'RV_5', 'PL_REL20_f1', 'PL_REL20_f10', 'RV_REL20_f1', 'RV_REL20_f10', 'K_RANGE_SOURCE', 'CLV20_SOURCE'),
                'H15': ('TAIL_PUSH', 'h_close', 'TAIL_VOL_REL20')}


# ====================================================================== query 注册表 + 骨架
def query_rows():
    CM = pd.read_csv(N.P('registry', 'comparison_manifest_E6n.csv'), keep_default_na=False)
    rows = []

    def q(card, letter, schema, rule, table, unit='ann_pp', placeholder=False, bound=''):
        rows.append(dict(query_id='E6N-%s-%s' % (card, letter), card=card, schema=schema, object_rule=rule, table=table, unit=unit,
                         placeholder=placeholder, bound_fixed_table=bound or table))
    q('H01', 'a', 'DATA', 'stage0/c7_minute/c7_summary.json 各项 + a7_8_official_bridge', 'stage0/c7_minute/a7_8_official_bridge.csv', 'log_return')
    q('H01', 'b', 'DATA', 'stage0/stage0_gate.json + checks_*', 'stage0/stage0_summary.csv', 'count')
    q('H01', 'c', 'DATA', 'results/coverage_by_feature_year_exchange.csv', 'results/coverage_by_feature_year_exchange.csv', 'decimal')
    q('H02', 'a', 'ANCHOR', 'stage0/c2_anchor_accounts_E6m.csv（锚对象逐日 = E6m）', 'stage0/c2_anchor_accounts_E6m.csv', 'decimal')
    q('H02', 'b', 'POLICY', 'policy_E6n.csv kind ∈ {ANCHOR}', 'results/full/policy_E6n.csv')
    letters = iter('cdefghijklmnopqrstuvwxyz')
    for card in ('H03', 'H04', 'H05', 'H06', 'H07', 'H08', 'H09', 'H10', 'H11'):
        views = sorted(set(CM.view[CM.card == card]))
        lt = iter('abcdefghijklmnopqrstuvwxyz')
        if card in B1_MEMBER_OF:
            q(card, next(lt), 'B1_0', 'b1_0_pairs member ∈ {%s}' % ','.join(B1_MEMBER_OF[card]), 'results/b1_0/b1_0_pairs.csv', 'bp')
            q(card, next(lt), 'B1_0', 'b1_0_matched member ∈ {%s}' % ','.join(B1_MEMBER_OF[card]), 'results/b1_0/b1_0_matched.csv', 'bp')
        for v in views:
            q(card, next(lt), 'COMPARISON', 'comparison_stats view == %s' % v, 'results/full/comparison_stats_<段>.csv')
        if card == 'H09':
            q(card, next(lt), 'FOUR_ACCOUNT', 'four_account_ledger kind == INFO_X_MEMORY', 'results/full/four_account_ledger.csv')
        if card == 'H10':
            q(card, next(lt), 'SUPPORT', 'support_four_accounts', 'results/full/support_four_accounts.csv')
            q(card, next(lt), 'DATA', 'coverage_by_feature_year_exchange', 'results/coverage_by_feature_year_exchange.csv', 'decimal')
        if card == 'H11':
            q(card, next(lt), 'FOUR_ACCOUNT', 'four_account_ledger kind == COMBINATION', 'results/full/four_account_ledger.csv')
        if card in ('H04', 'H07'):
            q(card, next(lt), 'COMPONENT_DOSE', 'component_dose_ledger owner feature ∈ %s' % ('Q_PATH' if card == 'H04' else 'Q_CLOSE_THIN'),
              'results/full/component_dose_ledger.csv')
        if card == 'H05':
            q(card, next(lt), 'DATA', '市场尾盘 β 诊断（A13 UNKNOWN）', 'stage0/data_contract.json', 'decimal', placeholder=True, bound='stage0/data_contract.json')
    q('H12', 'a', 'B2', 'b2_risk_set', 'results/full/b2/b2_risk_set.csv', 'count')
    q('H12', 'b', 'B2', 'b2_order_overlay（SOLO / JOINT_FROZEN）', 'results/full/b2/b2_order_overlay.csv', 'bp')
    q('H12', 'c', 'B2', 'b2_mirrors（CASH / NEXT_RANK）', 'results/full/b2/b2_mirrors.csv', 'bp')
    q('H12', 'd', 'B2', 'b2_controls（同率随机 / CVR 水平 / Bernoulli）', 'results/full/b2/b2_controls.csv', 'bp')
    q('H13', 'a', 'B3', 'b3_same_count', 'results/full/b3/b3_same_count.csv')
    q('H13', 'b', 'B3', 'b3_same_count 按位置 / 制度期', 'results/full/b3/b3_same_count_split.csv')
    q('H14', 'a', 'B4', 'b4_bridges（clean / pool0 / clean\\pool0；桥 A / B）', 'results/full/b4/b4_bridges.csv', 'decimal')
    q('H14', 'b', 'B4', 'b4_matched_non_i11', 'results/full/b4/b4_matched_non_i11.csv', 'bp')
    q('H15', 'a', 'B1_0', 'b1_0_regimes', 'results/b1_0/b1_0_regimes.csv', 'bp')
    q('H15', 'b', 'B3', 'b3_same_count 制度期', 'results/full/b3/b3_same_count_split.csv')
    q('H16', 'a', 'LINEAGE', 'idea_ledger_G / probe_ledger / execution_ledger_E / exposure_ledger 绑定', 'registration/execution_ledger_E.csv', 'count')
    q('H16', 'b', 'LINEAGE', 'source_claim_reconciliation', 'registration/source_claim_reconciliation.csv', 'count')
    Q = pd.DataFrame(rows)
    return Q


SKELETON_COLS = {
    'COMPARISON': ['query_id', 'comparison_id', 'view', 'left_desc_id', 'right_desc_id', 'segment', 'D_ann_pp', 'n', 'hac_se_ann_pp', 'FULL_ann_pp', 'G4_ann_pp', 'status'],
    'B1_0': ['query_id', 'member', 'domain', 'scope', 'segment', 'label', 'H', 'tercile', 'stat', 'value', 'unit', 'n_days', 'n_events', 'status'],
    'DATA': ['query_id', 'item', 'key', 'value', 'unit', 'status'],
    'ANCHOR': ['query_id', 'segment', 'parent', 'desc_id', 'max_abs_diff', 'status'],
    'POLICY': ['query_id', 'desc_id', 'FULL_ann_pp', 'G4_ann_pp', 'policy_verdict', 'status'],
    'FOUR_ACCOUNT': ['query_id', 'kind', 'parent', 'feature', 'memory', 'segment', 'I_ann_pp', 'R_ann_pp', 'X_ann_pp', 'closure_maxabs', 'status'],
    'SUPPORT': ['query_id', 'owner_desc_id', 'segment', 'native_diff_ann_pp', 'support_diff_ann_pp', 'child_shrink_ann_pp', 'parent_shrink_ann_pp', 'closure_maxabs', 'status'],
    'COMPONENT_DOSE': ['query_id', 'comp_id', 'owner_desc_id', 'segment', 'D_ann_pp', 'oob_share_decimal', 'unresolved_days', 'status'],
    'B2': ['query_id', 'form', 'object_key', 'trigger', 'H', 'horizon_mode', 'mirror', 'fee_mode', 'control', 'segment', 'stat', 'value', 'unit', 'n_events', 'status'],
    'B3': ['query_id', 'form', 'object_key', 'control', 'weights', 'H', 'split', 'cell', 'segment', 'D_ann_pp', 'n', 'status'],
    'B4': ['query_id', 'factor', 'domain', 'bridge', 'H', 'segment', 'stat', 'value', 'unit', 'n_days', 'status'],
    'LINEAGE': ['query_id', 'ledger', 'id', 'field', 'value', 'status'],
}


def write_queries():
    Q = query_rows()
    p = N.P('registry', 'query_registry_E6n.csv')
    N.atomic_write_csv(p, Q)
    sk = N.P('reports_skeleton', 'queries')
    os.makedirs(sk, exist_ok=True)
    for r in Q.itertuples():
        cols = SKELETON_COLS[r.schema] if r.schema in SKELETON_COLS else SKELETON_COLS['DATA']
        row = {c: '' for c in cols}
        row['query_id'], row['status'] = r.query_id, 'NOT_RUN'
        N.atomic_write_csv(os.path.join(sk, '%s.csv' % r.query_id), pd.DataFrame([row], columns=cols))
    return Q


# ====================================================================== 账本与卡
def proposal_lines():
    return open(N.P('handoff_in', 'exec_briefs', 'E6n_proposal.md'), encoding='utf-8').read().split('\n')


def reconciliation():
    L = proposal_lines()
    R = open(N.P('handoff_in', 'exec_briefs', 'E6m_REVIEW.md'), encoding='utf-8').read().split('\n')
    rows = []
    cid = [0]

    def add(author, version, text, status, supersedes='NOT_APPLICABLE', mv='NOT_RUN', qid='NOT_APPLICABLE', locator=''):
        cid[0] += 1
        rows.append(dict(claim_id='E6N-SRC%03d' % cid[0], author=author, version=version, source_locator=locator, source_text=text.strip(), status=status,
                         supersedes_id=supersedes, machine_value=mv, query_id=qid))
    find = lambda pat: next((i for i, l in enumerate(L) if re.search(pat, l)), None)
    i151 = find(r'^\- \*预测（第一道 B1-0 要验的）\*')
    if i151 is not None:
        txt = L[i151]
        add('CC', 'E6n_proposal v2（82f439f2）', txt, 'PREDICTION', 'E6N-H03-P|E6N-H05-P|E6N-H06-P1|E6N-H06-P2|E6N-H08', 'NOT_RUN', 'E6N-H03-a|E6N-H05-a|E6N-H06-a|E6N-H08-a',
            'proposal §3.2 C-B（第 %d 行）' % (i151 + 1))
        for k, sent in enumerate(re.split(r'[；;]', txt.split('：', 1)[-1])):
            if sent.strip():
                add('CC', 'E6n_proposal v2（82f439f2）', sent, 'PREDICTION', 'NOT_APPLICABLE', 'NOT_RUN', 'E6N-H03-a', 'proposal §3.2 C-B 分句 %d' % (k + 1))
    for pat, loc, sup, qid in ((r'^- \*预测\*：CVR 跳升退出', 'proposal §3.2 C-A', 'E6N-H12-P', 'E6N-H12-a'),
                               (r'^\*\*C-C 否决层同数对照', 'proposal §3.2 C-C', 'E6N-H13-P', 'E6N-H13-a'),
                               (r'^\*\*C-D 全 A 池检验', 'proposal §3.2 C-D', 'E6N-H14', 'E6N-H14-a')):
        i = find(pat)
        if i is not None:
            add('CC', 'E6n_proposal v2（82f439f2）', L[i], 'SUPERSEDED', sup, 'NOT_RUN', qid, '%s（第 %d 行）' % (loc, i + 1))
    i0, i1 = find(r'^### 3\.3 第一道验证'), find(r'^### 3\.4 候选对照')
    if i0 is not None and i1 is not None:
        for i in range(i0 + 1, i1):
            l = L[i].strip()
            if l and not l.startswith('|---'):
                add('CC', 'E6n_proposal v2（82f439f2）', l, 'FACT', 'NOT_APPLICABLE', '决策端第一道 probes（E6n_probes_stage1.py；2026-10-12 19:39–19:45 本机时间）已见表', 'NOT_APPLICABLE',
                    'proposal §3.3 第 %d 行（W03：已见表的读法）' % (i + 1))
    j0, j1 = find(r'^### 2\.1 E6m 第二道结算'), find(r'^### 2\.2 跨轮 miss')
    if j0 is not None:
        for i in range(j0 + 1, j1):
            l = L[i].strip()
            if l and not l.startswith('|---'):
                add('CC', 'E6n_proposal v2（82f439f2）', l, 'FACT', 'NOT_APPLICABLE', 'E6m REVIEW v0.95 结算（W09 原样归档）', 'NOT_APPLICABLE', 'proposal §2.1 第 %d 行' % (i + 1))
    i38 = find(r'^### 3\.8 生成式九问')
    if i38 is not None:
        add('CC', 'E6n_proposal v2（82f439f2）', 'Q3 … 若信息在 T 日路径里，H1 应最大、H5 衰减（E6l H 剖面形状）', 'PREDICTION', 'NOT_APPLICABLE', 'NOT_RUN', 'E6N-H08-a',
            'proposal §3.8 Q3（第 %d 行；原句节选，全文见该行）' % (i38 + 2))
    k0 = next((i for i, l in enumerate(R) if l.startswith('## 5. 机制判读')), None)
    if k0 is not None:
        for i in range(k0 + 1, min(len(R), k0 + 14)):
            l = R[i].strip()
            if l.startswith('- **B6') or l.startswith('- **B4') or l.startswith('- **四账户') or l.startswith('- **随机层'):
                add('决策端（E6m REVIEW）', 'E6m_REVIEW v1.0（读数 = v0.95）', l, 'FACT', 'NOT_APPLICABLE', 'E6m 固定表（reports/fixed_full）', 'NOT_APPLICABLE',
                    'E6m_REVIEW §5 第 %d 行' % (i + 1))
    C = pd.read_csv(N.P('registry', 'cc_carry_E6n.csv'), keep_default_na=False)
    for r in C.itertuples():
        add('CC', r.version, r.source_locator, r.status, 'plan §10.1（%s）' % r.plan_treatment[:80], 'NOT_RUN', 'NOT_APPLICABLE', 'plan §10.1 携带表 %s；评分规则：%s' % (r.carry_id, r.scoring_rule))
    return pd.DataFrame(rows)


def ledgers(cards, claims, Q):
    qmap = Q.groupby('card').query_id.apply(lambda s: '|'.join(s)).to_dict()
    W03 = '2026-10-12 19:39–19:45（本机；北京时间 10-13 07:39–07:45）：决策端第一道 probes 只读 E6m B3 固定表'
    G = []
    for idea, author, src, mot, comp, h0, dom, stat, fma, child in (
        ('G-H03', 'CC+Web', 'proposal §3.2 C-B；plan H03', '争夺后收平 ≠ 真安静', '争夺后恢复 = 有效承接', 'E[低 − 高] = 0', 'QGOOD ∩ Q0|A4b_CVRv5|α.25|HG10 形成集', 'PL_REL20 低 − 高（H5）', 'B1-0 封存时间', ''),
        ('G-H04', 'Web', 'plan §3.3 Q_PATH', '同净变化下折返多 = 价稳质量差', '只是低波偏好（Q_RV / Q_RANGE 同样好）', 'E[Q_PATH − Q_RV] = 0', '同上 + 账户', 'h_path 低 − 高；Q_PATH − Q_RV', 'B1-0 封存时间', ''),
        ('G-H05', 'CC（Web 改估计对象）', 'proposal §3.2 C-B 尾盘推力', '尾盘推升会回吐', '尾盘上移反映新信息', 'E[低 − 高] = 0', '同上', 'TAIL_PUSH 低 − 高', 'B1-0 封存时间', ''),
        ('G-H06', 'CC（Web 改估计对象）', 'proposal §3.2 C-B 尾盘量 / vsds', '量分布偏离常态 = 异常交易', '集中交易多解释（流动性 / 指数调仓）', 'E[低 − 高] = 0', '同上', 'TAIL_VOL_REL20 / JSD_PROFILE20 低 − 高', 'B1-0 封存时间', ''),
        ('G-H07', 'Web', 'plan §3.3 Q_CLOSE_THIN', '尾端抬升且量不足 = 孤立端点', '持续支持的收盘不应扣分', 'E[THIN − LEVEL] = 0', '同上 + 账户', 'h_close 低 − 高；THIN − LEVEL', 'B1-0 封存时间', ''),
        ('G-H08', 'CC+Web', 'plan H08；proposal §3.8 Q3', '绝对路径与平方路径不同；H 剖面', '高频噪声 / 频率选择', '无单一最优', '同上', 'RV / PL 频率桥 / OHLC 桥', 'B1-0 封存时间', ''),
        ('G-P61', 'CC', 'proposal §3.3 P1–P4（FACT）', '位置 × 活动调节 CVR / 价稳', '池子层面画像', '门内无增量', 'pool0 / 门内 / 被拒 / clean', 'P1–P4 固定表', W03, 'G-H03|G-H05|G-H06'),
        ('G-OHLC', 'CC', 'proposal §3.2 C-G ②', 'OHLC 级日内 / 隔夜 / 区间 / CLV 已测', '—', 'E6j / E6i 已测无增量（桥）', '桥', 'K_RANGE_SOURCE / CLV20_SOURCE', '历史（E6i / E6j）', ''),
        ('G-SKEWKURT', 'CC', 'proposal §3.2 C-G ⑨', '481 B1.3 日内偏度 / 峰度', '与 E6i D 轴峰度族同源', '不选（未提名）', 'NOT_APPLICABLE', 'NOT_APPLICABLE', 'NOT_MEASURED', ''),
        ('G-TICK', 'CC', 'proposal §3.2 C-G ⑧ / W07 B2.5 #10 / #11', '逐笔级成员', 'L2 先行条件不具备', '不做（未提名）', 'NOT_APPLICABLE', 'NOT_APPLICABLE', 'NOT_MEASURED', ''),
        ('G-H12', 'CC（Web 改估计对象）', 'proposal §3.2 C-A', 'CVR 跳升 = 入场论点被破坏', '价格触发 / 随机退出同样好', 'E[触发 − 同率随机] = 0', 'Q0 HG 主母体 H5 风险集', '剩余收益差', 'E6m B6（FACT）', ''),
        ('G-H13', 'CC（Web 改估计对象）', 'proposal §3.2 C-C', 'CVR 否决有超过同数删除的价值', '只是少持仓', 'E[CVR − 同数随机删] = 0', 'Q0 HG 主裸 A4b', 'D', 'E6e / 第一道 P1（FACT）', '')):
        G.append(dict(idea_id=idea, author=author, version='plan v1.1（af5ff33f）/ proposal v2（82f439f2）', source_ids=src, motivation=mot, competing_mechanism=comp,
                      H0_before_probe=h0, target_domain=dom, intended_statistic=stat, first_measurement_at=fma, probe_result='NOT_RUN',
                      miss_root_hypotheses='NOT_RUN', triggered_child_idea_ids=child or 'NOT_APPLICABLE'))
    E = []
    for r in cards.itertuples():
        cat = {'H01': '统计·实施压力', 'H02': '复现', 'H16': '统计·实施压力', 'H12': '新账户迁移', 'H13': '新账户迁移', 'H14': '新账户迁移', 'H15': '正式新测量'}.get(r.card, '正式新测量')
        E.append(dict(claim_id=r.claim_id, author=r.author, exact_text=r.new_prediction, inherited_or_new='NEW' if r.card not in ('H02',) else 'INHERITED',
                      evidence_already_seen=r.first_stage_evidence, outcome_not_yet_seen=r.card not in ('H02',), estimand=r.estimand, comparator=r.control,
                      exposure_scope=r.exposure, implementation_id=r.implementation, query_id=qmap.get(r.card, 'NOT_APPLICABLE'), result='NOT_RUN',
                      interpretation='NOT_RUN', next_design_change='NOT_RUN', category=cat, record_type='CARD'))
    for r in claims.itertuples():
        E.append(dict(claim_id='E6N-' + r.assertion_id, author=r.author, exact_text='%s：%s' % (r.first_object, r.frozen_direction), inherited_or_new='NEW',
                      evidence_already_seen='INLINE_STAGE1_NOT_YET_MEASURED' if r.card in ('H03', 'H05', 'H06') else 'E6m 主表 / B6 / 第一道 P1（FACT）',
                      outcome_not_yet_seen=True, estimand=r.estimand, comparator=r.comparator, exposure_scope=N.LABEL_FIRST_LOOK, implementation_id='见 query',
                      query_id=qmap.get(r.card, 'NOT_APPLICABLE'), result='NOT_RUN', interpretation='NOT_RUN', next_design_change='NOT_RUN',
                      category='新账户迁移' if r.card in ('H04', 'H07', 'H12', 'H13') else '正式新测量', record_type='ASSERTION'))
    D = pd.read_csv(N.P('registry', 'descriptors_E6n.csv'), keep_default_na=False)
    X = []
    for (kind, feat), g in D.groupby(['kind', 'feature']):
        X.append(dict(exposure_id='X-%s-%s' % (kind, feat), family=kind, feature=feat, n_objects_per_segment=len(g), segments='|'.join(N.SEGMENTS),
                      exposure=g.exposure.iloc[0], selection_or_redirection='NONE（全部预登记、一次不中途选材，plan §2.2）', source='registry/descriptors_E6n.csv'))
    for nm, n in (('AUXILIARY_MASK_CLONE_DOSE', 6984), ('MATCHED_COMPONENT', 414), ('COMPONENT_DOSE', 864)):
        X.append(dict(exposure_id='X-' + nm, family=nm, feature='ALL', n_objects_per_segment=n, segments='|'.join(N.SEGMENTS), exposure=N.LABEL_FIRST_LOOK,
                      selection_or_redirection='NONE', source='registry'))
    X.append(dict(exposure_id='X-B1_0', family='B1_0', feature='ALL', n_objects_per_segment=0, segments='|'.join(N.DERIV_SEGS), exposure='FIRST_MEASUREMENT',
                  selection_or_redirection='只打标签（A2），不触发挑支 / 换频率 / 改阈值', source='registry/b1_0_manifest_E6n.csv'))
    X.append(dict(exposure_id='X-P1P4', family='DECISION_PROBES', feature='P1–P4', n_objects_per_segment=0, segments='|'.join(N.DERIV_SEGS), exposure='SEEN_FACT',
                  selection_or_redirection='位置 × 活动族 park（P61）；分钟方向由此提名（W03）', source='exec_briefs/E6n_probe_P1_cvr_tail_by_position_activity.csv'))
    return pd.DataFrame(G), pd.DataFrame(E), pd.DataFrame(X)


def b2_manifest():
    rows = []
    forms = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
    objs = [(f, 'NONE|a0|NATIVE') for f in forms] + [(f, '%s|a0.25|Q0' % m) for f in forms for m in ('HG10', 'LAG1_10')]
    for f, k in objs:
        for trig, role in (('CVR_JUMP', 'MAIN'), ('PRICE_BREAK', 'OLD_CONTROL'), ('TREND_DOWN', 'OLD_CONTROL'), ('CVR_FIRST_VISIBLE_HIGH', 'BRIDGE')):
            for H in (1, 3, 5, 10, 20):
                for hm in ('FIXED_H', 'LONGEST_H'):
                    for mirror in ('CASH', 'NEXT_RANK'):
                        for fee in ('SOLO', 'JOINT_FROZEN'):
                            rows.append(dict(form=f, object_key=k, trigger=trig, trigger_role=role, H=H, horizon_mode=hm, mirror=mirror, fee_mode=fee,
                                             controls='SAME_RATE_RANDOM|CVR_LEVEL_WORST|BERNOULLI_RISK' if trig == 'CVR_JUMP' else 'NOT_APPLICABLE',
                                             account_level_exit='NOT_AUTHORIZED（B2 只账本诊断，brief A15）'))
    return pd.DataFrame(rows)


def b3_manifest():
    rows = []
    for core, cvr in (('A4b', 'A4b_CVRv5'), ('M_mean3_v2', 'M_mean3_v2_CVRv5'), ('M_union3_v2', 'M_union3_v2_CVRv5')):
        for k in ('NONE|a0|NATIVE', 'NONE|a0.25|Q0', 'HG10|a0.25|Q0', 'LAG1_10|a0.25|Q0'):
            for ctl in ('RANDOM_LEGAL_CVR', 'WORST_OLD_K', 'SOURCE_PRIORITY' if core != 'M_union3_v2' else 'MAX_EXISTING_RANK'):
                for w in ('FROZEN', 'REDO_DEV'):
                    for H in (1, 5, 10):
                        rows.append(dict(core=core, cvr_form=cvr, object_key=k, control=ctl, weights=w, H=H, main=(H == 5 and w == 'REDO_DEV'),
                                         splits='POSITION_T-1|YEAR|SSE_REFORM_20180820|SZ_MIRROR', denominator='固定总体分母（全部形成日）'))
    return pd.DataFrame(rows)


def policy_profiles():
    src = json.load(open(os.path.join(E6M_W, 'registration', 'policy_profiles_E6m_stageN.json'), encoding='utf-8'))
    out = dict(src)
    out['source'] = 'E6m registration/policy_profiles_E6m_stageN.json 原样转录（sha %s）+ E6n 本轮补充条款（brief §6 / W11 / W12）' % N.sha_file(
        os.path.join(E6M_W, 'registration', 'policy_profiles_E6m_stageN.json'))[:16]
    out['e6n_additions'] = dict(
        policy_undecidable_history='分钟历史不足以覆盖原政策要求的年数 / 早晚段时标 POLICY_UNDECIDABLE_HISTORY，另出可用期研究表；不把不能证明通过改成通过（plan §12.1）',
        e_random='源政策随机 = LEGACY_POLICY_RANDOM（E6l / E6m 新测量 P 机制：对象自身 Q 槽 kf 当日 IID 置换；registry/e_random_contract_E6n.json）；新增内容随机为诊断，不替代（plan §7.1）',
        no_additive_entry_for_q_minute='不给 Q 的分钟派生项造一套加法准入；三句加法只对原登记适用对象（plan §12.1）',
        improvement_table='实质改善表（对当前 Q0 HG / LAG 的 Δnet8 / 同资本 / 分辨度 / 支持 / 相对简单控制 / 维护代价）与资格表分列（plan §12.1）',
        replacement_preference_status='NOT_AUTHORIZED（全部新对象）', deployment_authorized=False, protocol='v1.5 候选（按流程建议、协议未正式裁定）')
    return out


SCHEMA_PLAN = [
    ('results/full/policy_E6n.csv', 'csv', 'desc_id', 'desc_id / kind / feature / parent / memory / H / strength / outer_alpha / applicability / frequency / direction / D_<段>×4 / n_<段>×4 / FULL_ann_pp / G4_ann_pp / FULL_sc_ann_pp / policy_<profile>_<agg> / replacement_preference_status / deployment_authorized / exposure', 'e6n_policy.py'),
    ('results/full/descriptor_stats_<段>.csv', 'csv', 'desc_id', 'desc_id / D_ann_pp / n / gross_ann_pp / turn / …', 'e6n_stats.py'),
    ('results/full/comparison_stats_<段>.csv', 'csv', 'comparison_id', 'comparison_id / view / left_desc_id / right_desc_id / D_ann_pp / n / hac_se_ann_pp', 'e6n_stats.py'),
    ('results/full/random_refs.csv', 'csv', 'desc_id+mechanism+segment', 'desc_id / mechanism / segment / real / rand_mean / rmr / rand_sd / paths_run / mcse / status', 'e6n_stats.py'),
    ('results/full/primary72_E6n.csv', 'csv', 'desc_id', 'desc_id / recipe / parent', 'e6n_stats.py'),
    ('results/full/four_account_ledger.csv', 'csv', 'kind+parent+feature+memory+segment', 'I / R / X / closure', 'e6n_decomp.py'),
    ('results/full/support_four_accounts.csv', 'csv', 'owner_desc_id+segment', 'native / support / shrink / closure', 'e6n_decomp.py'),
    ('results/full/component_dose_ledger.csv', 'csv', 'comp_id+segment', 'D / oob / unresolved', 'e6n_decomp.py'),
    ('results/full/frontier_E6n.csv', 'csv', 'desc_id', 'frontier', 'e6n_policy.py'),
    ('results/full/improvement_E6n.csv', 'csv', 'desc_id', 'Δnet8 vs Q0 HG / LAG …', 'e6n_policy.py'),
    ('results/b1_0/b1_0_*.csv', 'csv', 'member+domain+scope+segment+label+H+tercile+stat', 'member / domain / segment / tercile / stat / value / unit / n_days / n_events / status / query_id', 'e6n_b1_0.py'),
    ('registration/seal_B1_0.json / seal_deriv.json / seal_post.json', 'json', 'keys', 'written_at / n_files / queued_missing / n_receipts / sha256_manifest', 'e6n_b1_0.py / e6n_seal.py'),
    ('registration/probe_ledger.csv', 'csv', 'member', 'idea_id / member / domain / table / cell / seg1_value / seg2_value / same_sign / n / label / miss_root_hypotheses', 'e6n_b1_0.py'),
    ('registration/idea_ledger_G.csv / execution_ledger_E.csv / exposure_ledger.csv / source_claim_reconciliation.csv', 'csv', 'id', '见各表', 'e6n_stage_b.py'),
    ('accounts/<段>/<form>.npz', 'npz', 'desc', 'desc / desc_H / dates / d_net8 / d_gross / d_turn / d_pos / d_sc_child / d_sc_parent / … / holdings_sha / feature_version / contract_version', 'e6n_accounts.py'),
    ('randoms/<机制>/<段>/<组>__p<起>_<数>.npz', 'npz', 'desc+H', 'desc / H / form / mask_key / s_net / n_net / … / fp', 'e6n_rand.py'),
    ('results/full/b2/*.csv · b3/*.csv · b4/*.csv · b5/*.csv · b6/*.csv', 'csv', '见各表', '见各表', 'e6n_b2.py … e6n_b6.py'),
    ('registry/*_E6n.csv', 'csv', '见各表', '见各表', 'e6n_a0.py / e6n_rand.py / e6n_b1_0.py / e6n_stage_b.py'),
]


def write_schema_skeleton():
    L = ['# E6n SCHEMA.md（骨架：Stage B 冻结时生成；交付时由 e6n_deliver 按文件实测刷新行数 / 列名，闭包门 ⑤ 核）', '',
         '| 文件（相对结果目录） | 类型 | 行数或键数 | 键列 | 列名全列（npz 为键名） | 单位列说明 | 生成脚本 | query_id 列 |', '|---|---|---|---|---|---|---|---|']
    for f, typ, key, cols, scr in SCHEMA_PLAN:
        L.append('| %s | %s | 交付时实测 | %s | %s | ann_pp / bp / bp_per_h / decimal / count | %s | 交付时实测 |' % (f, typ, key, cols, scr))
    p = N.P('reports_skeleton', 'SCHEMA.md')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    N.atomic_write_text(p, '\n'.join(L) + '\n')
    return p


def stage_b():
    import e6n_b1_0 as B10
    t0 = time.time()
    Q = write_queries()
    K = pd.read_csv(N.P('registry', 'cards_E6n.csv'), keep_default_na=False)
    A = pd.read_csv(N.P('registry', 'claims_E6n.csv'), keep_default_na=False)
    qmap = Q.groupby('card').query_id.apply(lambda s: '|'.join(s)).to_dict()
    K['query'] = K.card.map(qmap).fillna('NOT_APPLICABLE')
    K['frozen_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    A['query_id'] = A.card.map(qmap).fillna('NOT_APPLICABLE')
    R = reconciliation()
    G, E, X = ledgers(K, A, Q)
    lin = []
    for r in K.itertuples():
        lin.append(dict(claim_id=r.claim_id, source_sha=N.PLAN_SHA256[:16], source_section='plan §10 %s' % r.card, verbatim_claim=r.new_prediction, author_role=r.author,
                        status='adopted', test_id=qmap.get(r.card, 'NOT_APPLICABLE'), query_id=qmap.get(r.card, 'NOT_APPLICABLE'),
                        first_exposure='E6n B1-0 / 推导段' if r.card not in ('H01', 'H02', 'H16') else 'NOT_APPLICABLE', result_status='PENDING', design_update=''))
    sup = ['§5.1 B1-0 进退规则（执行门）→ 第一道读法真值表（A2）', '§4.1 / §5.2 条件账户只对过 B1-0 的支 → 全部支', '§4.1 尾盘推力 = r(14:30→15:00)/|r_day| → TAIL_PUSH = asinh(L/b20(|L|))',
           '§5.0 尾盘推力剔指数为主版本 → 主成员不剔市场，另出等价检查与 β 诊断', '§4.1 vsds_1d 作主成员 → JSD_PROFILE20 主、481 原式作源桥',
           '§5.0 签名图定 bar 频率 → 5 分钟固定、1 / 10 分钟预登记桥', '§4.1 Q′ 线性混入 Q 槽（α .25）→ 外层 α_K + 内层 η / raw λ 两层',
           '§4 进候选库条件（两段同号 + 门内同向 + 匹配随机正 + 重叠 < .9 + 用户闸）→ 六条 + PORT3_T，其余为披露列',
           '§3.2 C-A 预测量级（≥ +.5、补入 ≥ 现金）→ 撤去，B2 只账本诊断', '§3.2 C-C ≥ 70% / C-D 不到一半 → 无比例先验',
           '§5.8 卡 Q01–Q12 → plan H01–H16', '模板 v6 ㉖ 两推导段同号门 → 披露列', '§6 R18 P37–P41 恢复条件 → plan §11.2 P41 写法']
    for i, s in enumerate(sup):
        lin.append(dict(claim_id='E6N-PROPOSAL-A1-%d' % (i + 1), source_sha='82f439f2（E6n_proposal.md）', source_section='brief A1 ①–⑬', verbatim_claim=s,
                        author_role='proposal（执行前研究起点）', status='superseded', test_id='NOT_APPLICABLE', query_id='NOT_APPLICABLE', first_exposure='NOT_APPLICABLE',
                        result_status='SUPERSEDED_BY_PLAN', design_update='见 brief A1'))
    Lg = pd.DataFrame(lin)
    rd = N.P('registration')
    outs = []
    for nm, D in (('cards_stageB_E6n.csv', K), ('claims_E6n.csv', A), ('source_claim_reconciliation.csv', R), ('hypothesis_lineage.csv', Lg),
                  ('idea_ledger_G.csv', G), ('execution_ledger_E.csv', E), ('exposure_ledger.csv', X)):
        p = os.path.join(rd, nm)
        N.atomic_write_csv(p, N.to_status(D))
        outs.append(p)
    pp = os.path.join(rd, 'policy_profiles_E6n.json')
    N.atomic_write_json(pp, policy_profiles())
    outs.append(pp)
    for nm, D in (('b2_manifest_E6n.csv', b2_manifest()), ('b3_manifest_E6n.csv', b3_manifest()), ('b1_0_manifest_E6n.csv', B10.manifest())):
        p = N.P('registry', nm)
        N.atomic_write_csv(p, D)
        outs.append(p)
    outs.append(write_schema_skeleton())
    N.write_receipt('E6n_stage_b', outs, code=[__file__], cards=len(K), claims=len(A), reconciliation=len(R), lineage=len(Lg), G=len(G), E=len(E), X=len(X),
                    queries=len(Q), wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(cards=len(K), claims=len(A), reconciliation=len(R), lineage=len(Lg), G=len(G), E=len(E), X=len(X), queries=len(Q)), ensure_ascii=False))


# ====================================================================== A1-auto
NUM = re.compile(r'[+−\-]?\d[\d,]*(?:\.\d+)?|[+−\-]?\.\d+')


def leaves(x, pre=''):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, '%s/%s' % (pre, k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, '%s[%d]' % (pre, i))
    else:
        yield pre, str(x)


def a1auto():
    t0 = time.time()
    rows = []
    add = lambda item, check, ok, detail='': rows.append(dict(item=item, check=check, status=(('PASS' if bool(ok) else 'FAIL') if isinstance(ok, (bool, np.bool_)) else str(ok)),
                                                              detail=N.san(str(detail))[:600]))
    D = pd.read_csv(N.P('registry', 'descriptors_E6n.csv'), keep_default_na=False)
    A = pd.read_csv(N.P('registry', 'auxiliary_E6n.csv'), keep_default_na=False)
    C = pd.read_csv(N.P('registry', 'component_controls_E6n.csv'), keep_default_na=False)
    CM = pd.read_csv(N.P('registry', 'comparison_manifest_E6n.csv'), keep_default_na=False)
    cnt = json.load(open(N.P('registration', 'a0_counts_E6n.json'), encoding='utf-8'))
    rep = json.load(open(N.P('stage0', 'plan_tests', 'report.json'), encoding='utf-8'))
    add('1', '主 3,784 / 附属 6,984 / 主 72 / MATCHED 414 / COMPONENT_DOSE 864 / 比较引用 2,178；registry_sha256 = spec 输出',
        (len(D), len(A), int(D.is_primary72.astype(str).eq('True').sum()), int((C.kind == 'MATCHED_COMPONENT').sum()), int((C.kind == 'COMPONENT_DOSE').sum()),
         cnt['registry_sha256']) == (3784, 6984, 72, 414, 864, rep['registry_sha256']) and cnt['comparisons'] == 2178,
        '%d / %d / %d / %d / %d；cmp %s；sha %s' % (len(D), len(A), int(D.is_primary72.astype(str).eq('True').sum()), int((C.kind == 'MATCHED_COMPONENT').sum()),
                                                  int((C.kind == 'COMPONENT_DOSE').sum()), cnt['comparisons'], cnt['registry_sha256'][:16]))
    add('1', 'desc_id 唯一；按 kind 分块 = plan 附录 A', D.desc_id.is_unique and D.kind.value_counts().to_dict() == rep['main_by_kind'], D.kind.value_counts().to_dict())
    add('1', 'policy 行 = 主对象除 ANCHOR ORIGINAL 30 / STRONG_ANCHOR 10 → 3,744', int(D.in_policy_table.astype(str).eq('True').sum()) == 3744,
        int(D.in_policy_table.astype(str).eq('True').sum()))
    # 2 政策合同转录
    pe = json.load(open(os.path.join(E6M_W, 'registration', 'policy_profiles_E6m_stageN.json'), encoding='utf-8'))
    pn = json.load(open(N.P('registration', 'policy_profiles_E6n.json'), encoding='utf-8'))
    same = all(pn.get(k) == v for k, v in pe.items() if k != 'source')
    add('2', 'PX 转录 = E6m 转录件（逐叶相同，除 source 说明）；E6m 对 E6l 原件的人工逐句核放行（用户 2026-10-11 原话）沿用（registration/a1_auto_item2_reconciliation_E6n.json）', same,
        'E6m 转录 sha %s' % N.sha_file(os.path.join(E6M_W, 'registration', 'policy_profiles_E6m_stageN.json'))[:16])
    rc = dict(item='2', basis='brief W11：沿 E6m policy_profiles_E6m.json + PX 文本逐句复现；机械判据对 E6l 原件 FAIL 时按 E6m 先例人工逐句核放行',
              e6m_reconciliation='E6m registration/a1_auto_item2_reconciliation_E6m_S.json（verdict PASS；用户 2026-10-11 原话"同意按人工逐句核结论放行A1-auto第2项，冻结件不改"）',
              e6m_reconciliation_sha256=N.sha_file(os.path.join(E6M_W, 'registration', 'a1_auto_item2_reconciliation_E6m_S.json')),
              e6n_transcription_identical_to_e6m=bool(same), verdict='PASS' if same else 'FAIL',
              note='本轮转录与 E6m 转录逐叶相同（只改 source 说明、追加 e6n_additions）→ E6m 的逐句核结论原样适用；新增条款逐条出自 brief §6 / W11 / W12 与 plan §12.1',
              written_at=time.strftime('%Y-%m-%d %H:%M:%S'), written_by='执行端（按 brief W11 先例；新增条款非 PX 原件内容）')
    N.atomic_write_json(N.P('registration', 'a1_auto_item2_reconciliation_E6n.json'), rc)
    add('2', 'policy_provisional = false；PORT3_T 正式；LEADER 只披露；deployment_authorized = false；新对象 NOT_AUTHORIZED',
        pn.get('policy_provisional') is False and 'PORT3_T' in str(pn.get('size_profiles')) and pn.get('deployment_authorized') is False)
    # 3 卡
    K = pd.read_csv(N.P('registration', 'cards_stageB_E6n.csv'), keep_default_na=False)
    Q = pd.read_csv(N.P('registry', 'query_registry_E6n.csv'), keep_default_na=False)
    plan = open(N.P('PLAN_COPY.md'), encoding='utf-8').read()
    add('3', '16 卡 H01–H16；标题行出自 PLAN_COPY 原文', len(K) == 16 and all(t in plan for t in K.title), '%d 卡' % len(K))
    add('3/⑬', '每卡 ≥ 1 query 且都在 query 注册表；estimand / control / miss_reason 非空',
        all(r.query != 'NOT_APPLICABLE' and all(x in set(Q.query_id) for x in r.query.split('|')) for r in K.itertuples())
        and (K.estimand.str.len() > 0).all() and (K.control.str.len() > 0).all() and (K.miss_reason.str.len() > 0).all(), '')
    add('㉓', '每卡 first_stage_evidence 非空（分钟成员 = INLINE_STAGE1_NOT_YET_MEASURED）；miss_reason 规则非空',
        (K.first_stage_evidence.str.len() > 0).all() and (K.miss_reason.str.len() > 0).all(), K.first_stage_evidence.str[:30].value_counts().to_dict())
    Cl = pd.read_csv(N.P('registration', 'claims_E6n.csv'), keep_default_na=False)
    add('3', '10 条方向断言各绑定 estimand 与 comparator', len(Cl) == 10 and (Cl.estimand.str.len() > 0).all() and (Cl.comparator.str.len() > 0).all(), len(Cl))
    # 4 测量与方向
    feats = set(D.feature)
    need = {'ORIGINAL', 'Q0', 'C1', 'PL_REL20', 'TAIL_PUSH', 'TAIL_VOL_REL20', 'JSD_PROFILE20', 'RV_REL20', 'Q_PATH', 'Q_CLOSE_THIN', 'Q_RV', 'Q_RANGE', 'Q_CLOSE_LEVEL',
            'Q_BOTH', 'K_RANGE_SOURCE', 'CLV20_SOURCE'}
    add('4', '测量集合 = plan（五面 / 两构造 / 三 raw 控制 / Q_BOTH / 两 OHLC 桥 / Q0 / C1 / 原父）', need <= feats, sorted(feats - need))
    dirs = D[D.kind == 'DIRECTION']
    add('4', '反方向只在 DIRECTION（d−1，五面 H5 / .25）', set(dirs.direction.astype(int)) == {-1} and set(D[D.kind != 'DIRECTION'].direction.astype(int)) == {1}, len(dirs))
    # 5 参数
    nb = D[D.random_bound.astype(str) == 'True']
    add('5', 'η / λ ∈ {.125, .25, .5}；α_K ∈ {.125, .25, .5}；H ∈ {1, 3, 5, 10, 20}；记忆 ∈ {NONE, HG10, LAG1_10}；频率 ∈ {1, 5, 10}',
        set(nb.strength.astype(float)) <= {.125, .25, .5} and set(D.outer_alpha.astype(float)) <= {0.0, .125, .25, .5} and set(D.H.astype(int)) == {1, 3, 5, 10, 20}
        and set(D.memory) == {'NONE', 'HG10', 'LAG1_10'} and set(D.frequency.astype(int)) <= {1, 5, 10}, '')
    import e6n_rand as RN
    add('5', '随机 1,024 / 512 / 8,192 / MCSE .03；bootstrap 2,000 × 20 / 60；HAC H / 2H', (RN.FIRST, RN.TOPUP, RN.MAXP, RN.MCSE_MAX) == (1024, 512, 8192, 0.03)
        and pn.get('bootstrap', {}).get('reps') == 2000 and pn.get('bootstrap', {}).get('block_lengths') == [20, 60], '')
    # 6 骨架
    sk = N.P('reports_skeleton', 'queries')
    miss = [q for q in Q.query_id if not os.path.exists(os.path.join(sk, '%s.csv' % q))]
    add('6', '每个 query 一张骨架（status 行）', not miss, '%d query；缺 %d' % (len(Q), len(miss)))
    # 7 暴露 / 授权
    add('7', '新对象 replacement_preference_status = NOT_AUTHORIZED；deployment_authorized 全 False；锚 = SECOND_EVALUATION',
        (nb.replacement_preference_status == 'NOT_AUTHORIZED').all() and (D.deployment_authorized.astype(str) == 'False').all()
        and (D[D.kind.isin(['ANCHOR', 'STRONG_ANCHOR'])].exposure == N.LABEL_SECOND).all(), '')
    an = pd.read_csv(N.P('stage0', 'c2_anchor_accounts_E6m.csv'), keep_default_na=False)
    add('7', 'SECOND_EVALUATION 对象 = E6m 已评同对象（锚账户 1,168 行全有 E6m 同 ID 且逐日相同）', (an.status == 'PASS').all() and len(an) == 1168, an.status.value_counts().to_dict())
    # ⑭ / ⑮ / ⑯
    R = __import__('e6n_masks').registry_rows()
    add('⑭', 'NATIVE 名单键 α = 0；非 NATIVE α 有值', ((R.alpha_eff == 0) == R.variant.str.startswith('NATIVE')).all(), '')
    M = pd.read_csv(N.P('registry', 'random_manifest_E6n.csv'), keep_default_na=False)
    add('⑮', '带记忆对象 memory_reference：HG = 本账户实际 G（e6l_fast.rec_single lag=0）；LAG = 同算子自然 U（lag=1）；R_MEMORY 只在主 72 带记忆新行',
        set(M[M.mechanism == 'R_MEMORY'].memory) <= {'HG10', 'LAG1_10'}, M[M.mechanism == 'R_MEMORY'].memory.value_counts().to_dict())
    # ⑰ B3 / B2 manifest
    b3 = pd.read_csv(N.P('registry', 'b3_manifest_E6n.csv'), keep_default_na=False)
    b2 = pd.read_csv(N.P('registry', 'b2_manifest_E6n.csv'), keep_default_na=False)
    add('⑰', 'B3 三种同数对照 × 冻权 / 重定权 × H × 拆分；B2 触发 × H × 两 H 口径 × 两镜像 × SOLO / JOINT', len(b3) > 0 and len(b2) > 0, '%d / %d 行' % (len(b3), len(b2)))
    # ⑱ 外部输入
    X = pd.read_csv(N.P('registry', 'external_inputs_E6n.csv'), keep_default_na=False)
    okx = X.apply(lambda r: bool(r.sha256) or r.status in ('SOURCE_WAIT', 'UNKNOWN', 'INFO'), axis=1).all()
    add('⑱', '外部输入每行有 sha 或 SOURCE_WAIT / UNKNOWN', bool(okx) and not (X.status == 'FAIL').any(), X.status.value_counts().to_dict())
    # ⑲ 状态词
    bad = []
    for f in glob.glob(N.P('registry', '*.csv')) + glob.glob(N.P('registration', '*.csv')):
        df = pd.read_csv(f, keep_default_na=False, dtype=str)
        for c in [c for c in df.columns if c.lower() in ('status', 'result', 'label', 'probe_result')]:
            if df[c].isin(['N/A', 'NA', 'nan', 'NaN', 'null', 'None']).any():
                bad.append('%s:%s' % (os.path.basename(f), c))
    add('⑲', '状态词扫描（registry / registration）无 N/A / NA / nan / null / None', not bad, bad[:5])
    # ⑳ 生成器缺列 / 空表报错（合成）
    try:
        import e6n_queries as QG
        e1 = QG.selftest_errors()
        add('⑳', '生成器对缺列报错、对 0 行报错（合成缺列 / 空表各触发一次）', e1 is True, e1)
    except Exception as e:                                                        # noqa: BLE001
        add('⑳', '生成器对缺列报错、对 0 行报错（合成）', False, repr(e)[:200])
    # ㉑ MASK_CLONE / DOSE 一一对应
    own = A.groupby('owner_desc_id').kind.value_counts().unstack(fill_value=0)
    nonanchor = set(nb.desc_id)
    okk = (set(own.index) == nonanchor) and (own.get('MASK_CLONE', pd.Series(dtype=int)) == 1).all() and (own.get('DOSE', pd.Series(dtype=int)) == 1).all()
    add('㉑', '每个非锚 owner 有且只有一条 MASK_CLONE 与一条 DOSE；支持签名解析到 owner', bool(okk), '%d owners' % len(own))
    # ㉒ 分量控制
    qo = nb[nb.feature.isin(['Q_PATH', 'Q_CLOSE_THIN'])]
    cd = C[C.kind == 'COMPONENT_DOSE']
    have = set(cd.owner_desc_id)
    add('㉒', '每个 Q_PATH / Q_CLOSE_THIN 确定性 owner 有 COMPONENT_DOSE（同坐标同支持；控制变体同支持族）',
        set(qo.desc_id) <= have and (cd.input_control_desc_id != 'NOT_APPLICABLE').all(), '%d owners / %d cdose' % (len(qo), len(cd)))
    # ㉔ data_contract
    dc = json.load(open(N.P('stage0', 'data_contract.json'), encoding='utf-8'))
    req = ('provider', 'table', 'schema', 'version', 'asof', 'window', 'cutoff', 'coverage', 'units', 'calendar', 'auction', 'timestamp_convention', 'revisions', 'sha')
    add('㉔', 'data_contract 每字段有值或 SOURCE_WAIT；timestamp_convention 已实测', all(dc.get(k) not in (None, '') for k in req) and '实测' in dc.get('timestamp_convention', ''),
        [k for k in req if dc.get(k) in (None, '')])
    # ㉕ 缓存命名空间
    import e6n_meas as ME
    pr = ME.panel_root()
    ns = json.load(open(os.path.join(pr, 'namespace.json'), encoding='utf-8'))
    add('㉕', '缓存命名空间含 contract_version E6n-v1.1 + plan sha 前缀 + source / data / adapter 版本', 'E6n-v1.1' in os.path.basename(pr) and N.PLAN_SHA256[:8] in os.path.basename(pr)
        and all(k in json.dumps(ns) for k in ('MatrixDailyFix', 'e6n_minute@')), os.path.basename(pr))
    # ㉖ Q0 / C1 同剂量锚
    an_ = D[(D.kind == 'ANCHOR') & D.feature.isin(['Q0', 'C1'])]
    add('㉖', 'Q0 / C1 在 α .125 / .5 的同剂量锚存在（六形态 × 三记忆 × H5）', {.125, .25, .5} <= set(an_.outer_alpha.astype(float)), sorted(set(an_.outer_alpha.astype(float))))
    # ㉗ B1-0 manifest
    bm = pd.read_csv(N.P('registry', 'b1_0_manifest_E6n.csv'), keep_default_na=False)
    import e6n_b1_0 as B10
    add('㉗', 'B1-0 manifest 成员 × 域 × 作用域齐全；A2 规则在主域行事前登记；seal_B1_0 在任何推导段账户之前（闭包门 ⑦ 复核）',
        bm.member.nunique() == len(B10.MEMBER_IDS) and bm.domain.nunique() == len(B10.domains()) and (bm.a2_rule != 'NOT_APPLICABLE').sum() == len(B10.MEMBER_IDS)
        and not os.path.isdir(N.P('accounts')), '%d 行；%d 成员 / %d 域' % (len(bm), bm.member.nunique(), bm.domain.nunique()))
    # ㉘ SCHEMA 骨架
    sch = N.P('reports_skeleton', 'SCHEMA.md')
    add('㉘', 'SCHEMA.md 骨架存在且含每张计划表', os.path.exists(sch) and all(f.split(' ')[0] in open(sch, encoding='utf-8').read() for f, *_ in SCHEMA_PLAN), '')
    df = pd.DataFrame(rows)
    p1 = N.P('registration', 'a1_auto_E6n.csv')
    N.atomic_write_csv(p1, df)
    j = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), n_items=len(df), counts=df.status.value_counts().to_dict(), all_pass=bool((df.status == 'PASS').all()),
             not_pass=df[df.status != 'PASS'][['item', 'status', 'detail']].to_dict('records'))
    p2 = N.P('registration', 'a1_auto_E6n.json')
    N.atomic_write_json(p2, j)
    N.write_receipt('E6n_a1_auto', [p1, p2], code=[__file__], counts=j['counts'], all_pass=j['all_pass'], wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(counts=j['counts'], all_pass=j['all_pass'], not_pass=[(x['item'], x['detail'][:120]) for x in j['not_pass']]), ensure_ascii=False))


# ====================================================================== 冻结 / 记录 B / 条件
def freeze():
    import e6n_gate as GT
    rd = N.P('registration')
    fz = os.path.join(rd, GT.FREEZE)
    pre = os.path.join(rd, GT.AUTH_PRE)
    if os.path.exists(fz):
        raise RuntimeError('冻结清单已存在（只增不覆盖；语义 amendment 需新授权）')
    a1 = json.load(open(os.path.join(rd, 'a1_auto_E6n.json'), encoding='utf-8'))
    if not a1.get('all_pass'):
        raise RuntimeError('A1-auto 未全过：阻断 B 草稿 / 冻结')
    auth = json.load(open(os.path.join(rd, GT.AUTH_STATUS), encoding='utf-8'))
    reg = sorted(glob.glob(N.P('registry', '*.csv')) + glob.glob(N.P('registry', '*.json')))
    docs = [os.path.join(rd, f) for f in ('cards_stageB_E6n.csv', 'claims_E6n.csv', 'source_claim_reconciliation.csv', 'hypothesis_lineage.csv', 'idea_ledger_G.csv',
                                          'execution_ledger_E.csv', 'exposure_ledger.csv', 'policy_profiles_E6n.json', 'a1_auto_E6n.json', 'a1_auto_item2_reconciliation_E6n.json',
                                          'a0_counts_E6n.json', 'mask_facts_E6n.csv', 'stage_a_E6n.json', GT.AUTH_STATUS)]
    docs += [N.P('PLAN_COPY.md'), N.P('reports_skeleton', 'SCHEMA.md'), N.P('stage0', 'data_contract.json')]
    man = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), machine=N.MACHINE, contract_version=N.CONTRACT_VERSION, plan_sha256=N.PLAN_SHA256,
               registry_sha256={os.path.basename(p): N.sha_file(p) for p in reg}, documents_sha256={N.rel(p): N.sha_file(p) for p in docs if os.path.exists(p)},
               no_returns_read_before=True, note='Stage A（掩码层事实）与 Stage B（卡 / 断言 / 携带 / 账本）两包；任何新对象收益读取之前', w10_mode=auth.get('w10_mode'))
    N.atomic_write_json(fz, man)
    fsha = N.sha_file(fz)
    rec = dict(written_at=man['written_at'], w10_mode=auth.get('w10_mode'), freeze_manifest=GT.FREEZE, freeze_sha256=fsha,
               effective_conditions=['Stage 0 全 PASS', 'A1-auto 全 PASS', 'B1-0 已封存（seal_B1_0）', 'seal_deriv 已写', '进入后段时冻结清单 sha 不变'],
               rule='方式 B：转交消息含 "B" → 两包冻结时照录用户原话 + 日期 + 清单 sha；任何语义 amendment 使授权失效')
    p2 = os.path.join(rd, 'record_B_mode_%s_E6n.json' % auth.get('w10_mode'))
    N.atomic_write_json(p2, rec)
    outs = [fz, p2]
    if auth.get('w10_mode') == 'B':
        if os.path.exists(pre):
            raise RuntimeError('%s 已存在（不覆盖）' % GT.AUTH_PRE)
        N.atomic_write_json(pre, dict(mode='B', user_quote=auth['user_quote'], user_quote_date=auth['user_quote_date'], user_message_verbatim=auth['user_quote'],
                                      written_at=man['written_at'], written_by='执行端照录用户原话（两包冻结时）', status_file=GT.AUTH_STATUS,
                                      status_file_sha256=N.sha_file(os.path.join(rd, GT.AUTH_STATUS)), freeze_manifest=GT.FREEZE, freeze_sha256=fsha,
                                      effective_conditions=rec['effective_conditions'], amendment_rule='任何语义 amendment（冻结清单变化）使本授权失效，须重新授权',
                                      scope='E6n 两后段（2019-2023 / 2024-2026）：确定性 + 随机 + 增补 + 全段统计 / 政策 / bootstrap / 四账户 / 分解 / B2–B6 后段部分',
                                      not_reused=auth.get('not_reused')))
        outs.append(pre)
    N.write_receipt('E6n_stage_b_freeze', outs, code=[__file__], mode=auth.get('w10_mode'), registry_files=len(reg), freeze_sha256=fsha)
    print(json.dumps(dict(mode=auth.get('w10_mode'), registry_files=len(reg), docs=len(docs), freeze_sha=fsha[:16]), ensure_ascii=False))


def conditions():
    import e6n_gate as GT
    rd = N.P('registration')
    g = json.load(open(N.P('stage0', 'stage0_gate.json'), encoding='utf-8')) if os.path.exists(N.P('stage0', 'stage0_gate.json')) else {}
    a1 = json.load(open(os.path.join(rd, 'a1_auto_E6n.json'), encoding='utf-8')) if os.path.exists(os.path.join(rd, 'a1_auto_E6n.json')) else {}
    fz = os.path.join(rd, GT.FREEZE)
    pre = os.path.join(rd, GT.AUTH_PRE)
    s10 = os.path.exists(os.path.join(rd, GT.SEAL_B10))
    sd = os.path.exists(os.path.join(rd, GT.SEAL_DERIV))
    bound = os.path.exists(pre) and json.load(open(pre, encoding='utf-8')).get('freeze_sha256') == (N.sha_file(fz) if os.path.exists(fz) else None)
    # "进入后段时清单 sha 不变"：冻结清单里逐个文件现算 sha 与冻结时相同（只看冻结文件本身的 sha 查不出清单内容被改）
    changed, n_checked, added = [], 0, []
    if os.path.exists(fz):
        man = json.load(open(fz, encoding='utf-8'))
        for p, s in [(N.P('registry', k), v) for k, v in man.get('registry_sha256', {}).items()] + [(N.P(k), v) for k, v in man.get('documents_sha256', {}).items()]:
            n_checked += 1
            if not (os.path.exists(p) and N.sha_file(p) == s):
                changed.append(N.rel(p))
        now = sorted(os.path.basename(p) for p in glob.glob(N.P('registry', '*.csv')) + glob.glob(N.P('registry', '*.json')))
        added = [x for x in now if x not in man.get('registry_sha256', {})]
    ok = bool(g.get('all_pass')) and bool(a1.get('all_pass')) and s10 and sd and bound and n_checked > 0 and not changed
    rec = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), all_pass=ok, stage0_all_pass=bool(g.get('all_pass')), stage0_blocking=g.get('blocking', [])[:20],
               a1_auto_all_pass=bool(a1.get('all_pass')), seal_B1_0=s10, seal_deriv=sd, authorization_bound_to_freeze=bound,
               frozen_files_checked=n_checked, frozen_files_changed=changed, registry_files_added_after_freeze=added,
               frozen_manifest_sha256=N.sha_file(fz) if os.path.exists(fz) else '')
    p = os.path.join(rd, GT.AUTH_COND)
    N.atomic_write_json(p, rec)
    N.write_receipt('E6n_record_B_conditions', [p], code=[__file__], all_pass=ok)
    print(json.dumps({k: v for k, v in rec.items() if k != 'stage0_blocking'}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['queries', 'stage-b', 'a1auto', 'freeze', 'conditions'])
    a = ap.parse_args()
    {'queries': write_queries, 'stage-b': stage_b, 'a1auto': a1auto, 'freeze': freeze, 'conditions': conditions}[a.step]()
    return 0


if __name__ == '__main__':
    sys.exit(main())
