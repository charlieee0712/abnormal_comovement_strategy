# -*- coding: utf-8 -*-
"""E6o A1 冻结（brief §3；plan §3、§11.3、§12；附录 B.3 / B.4 / E）。写：
  registration/ledger_G_E6o.csv、ledger_E_E6o.csv（事前登记；结果栏 PENDING，A2 / B 后只追加结果字段）
  registration/cards_E6o.csv（Q01–Q18 原文）、cc_carried_E6o.csv（CC-01…12 原句逐字）、policy_profile_E6o.json（POLICY_E6O_PARENT_Q /
  E6O_RESEARCH_STATUS / PARTIAL_HISTORY_RESEARCH_V1 / FROZEN_COST_STRESS / PORT3_T_EXIT_MAPPING）
  registration/freeze_E6o.json（附录 B.4 全键 + 冻结件 sha 清单）。用法：python3 e6o_a1.py"""
import os
import re
import json
import time
import hashlib
import glob

import pandas as pd

import e6o_core as O

PLAN = 'PLAN_COPY.md'
G_COLS = ['g_id', 'author', 'exact_statement', 'created_at', 'created_before_measurement', 'source_facts', 'motivation', 'competing_explanation',
          'proposed_estimand', 'probe_code_hash', 'probe_window', 'probe_result', 'status', 'root_cause_evidence', 'derived_from', 'new_direction', 'next_test',
          'operation_type', 'data_exposure', 'registration_provenance', 'timestamp_artifact', 'expectation_before_probe_verbatim', 'expected_statement_provenance',
          'measurement_at', 'result_at', 'interpretation_at', 'derived_hypothesis_at', 'original_g_id', 'linked_e_ids', 'tested_or_unmeasured', 'pre_or_post_exposure',
          'evidence_vs_candidate_explanation']
E_COLS = ['e_id', 'g_ids', 'author', 'original_version', 'exact_prediction', 'prediction_or_question', 'selected_before_outcome', 'prior_exposure', 'first_stage_evidence',
          'formal_contrast', 'target_population', 'unit', 'comparison_ids', 'support_ids', 'query_id', 'result', 'evidence_strength', 'miss_root', 'next_change']


def g(**kw):
    r = {c: '' for c in G_COLS}
    r.update(kw)
    r.setdefault('registration_provenance', 'AUTHOR_REPORTED')
    if not r['registration_provenance']:
        r['registration_provenance'] = 'AUTHOR_REPORTED'
    if not r['timestamp_artifact']:
        r['timestamp_artifact'] = 'PENDING'
    return r


def g_rows():
    R = []
    R.append(g(g_id='G-F2-01', author='CC 决策端（F2 §2.3 / §3.7）；Web plan v1.1 §3.4 携带',
               exact_statement='§2.3："变化才是新信息"的直觉遇到 LEVEL 对照与跳升接近、LEVEL 略优；§3.7 四段真 − LEVEL 为 −.004 / −.007 / −.002 / −.003 bp / 事件；作者据此生成 T1a、T2′',
               created_at='2026-10-17（proposal v2）', created_before_measurement='NO（读已暴露的 E6n B2 四段对照表）', source_facts='E6n_REPORT_carried B2 controls（CVR_JUMP × CVR_LEVEL_WORST）',
               motivation='持有期内信息的水平 / 变化之分决定触发时钟', competing_explanation='LEVEL 对照的测量（S0-0 已核：cvr_1d 水平）；"进入坏尾"可能本身是水平状态；T2′只排除 20 日状态，不是剔除日水平',
               proposed_estimand='SOURCE / LEVEL / EDGE / OWNCHANGE 并跑；同当前日 CVR、同日龄 / 剩余期限、同意向金额下读 T2 及 T2′（E01 / E02、Q02–Q05）',
               probe_window='推导段 2010-2014 / 2015-2018（G1）', status='开放', operation_type='READ_EXISTING_EXPOSED_TABLE', data_exposure='E6n B2 四段已读（F2）',
               expectation_before_probe_verbatim='F2 未留测前原句（作者回溯描述）', expected_statement_provenance='AUTHOR_REPORTED', original_g_id='F2 §2.3 第 1 条',
               linked_e_ids='E01;E02', tested_or_unmeasured='TESTED_ON_EXPOSED_TABLE', pre_or_post_exposure='POST_EXPOSURE', evidence_vs_candidate_explanation='候选解释'))
    R.append(g(g_id='G-F2-02', author='CC 决策端（F2 §2.3 / §3.7）；Web plan v1.1 §3.4 携带',
               exact_statement='§2.3 与 §3.7：NEXT_RANK 的 gross 从 2019–23 约 .77 到 2024–26 约 2.89，作者怀疑资本配置效应，提出同资本后差应缩至约 0',
               created_at='2026-10-17（proposal v2）', created_before_measurement='NO', source_facts='E6n B2 overlay NEXT_RANK 两后段',
               motivation='释放资本的去向本身是策略的一部分', competing_explanation='同资本后的变化也可能含基准缩放、行业、投资期限、资本反馈与费用；"≈0 才是配置、否则选票"是派生读法预测',
               proposed_estimand='同源事件机会的去持有 / 再买入 / 基准 / 成本 / 剩余期限明细；闭环 CASH / NATIVE / NEXT 并列；FULL_sc 只回答标准化视图（Q12 / Q13、§8.5）',
               probe_window='推导段（G1）+ 全程（B）', status='开放', operation_type='READ_EXISTING_EXPOSED_TABLE', data_exposure='E6n B2 两后段已读',
               expectation_before_probe_verbatim='"同资本后差应缩至约 0"（CC 原读法，单独评分）', expected_statement_provenance='AUTHOR_REPORTED', original_g_id='F2 §2.3 第 2 条',
               linked_e_ids='E07', tested_or_unmeasured='TESTED_ON_EXPOSED_TABLE', pre_or_post_exposure='POST_EXPOSURE', evidence_vs_candidate_explanation='派生读法预测'))
    R.append(g(g_id='G-F2-03', author='CC 决策端（F2 §2.3 / §3.7）；Web plan v1.1 §3.4 携带',
               exact_statement='§2.3：无否决形态退出增量约两倍，作者将有否决形态设主读，并称约一半信息共享；§3.7 列 .57 / .66 vs 1.11 / 1.16',
               created_at='2026-10-17（proposal v2）', created_before_measurement='NO', source_facts='E6n B2 2019–23 FIXED CASH 有 / 无否决形态',
               motivation='持有期否决还能带来多少边际', competing_explanation='母体的风险集、资本与持仓路径不同；"约两倍"不是信息份额或严格上界',
               proposed_estimand='D5 入场否决 × 退出四账户 + 共同持有 / 只在裸核 / 只在有否决核三风险集；同预算、同剩余窗口（Q06 / Q15、§8.5）',
               probe_window='推导段（G1）+ 全程（B）', status='开放', operation_type='READ_EXISTING_EXPOSED_TABLE', data_exposure='E6n B2 已读',
               expectation_before_probe_verbatim='"约一半信息共享"（CC 原读法，CC-04 另评）', expected_statement_provenance='AUTHOR_REPORTED', original_g_id='F2 §2.3 第 3 条',
               linked_e_ids='E03', tested_or_unmeasured='TESTED_ON_EXPOSED_TABLE', pre_or_post_exposure='POST_EXPOSURE', evidence_vs_candidate_explanation='候选解释'))
    for gid, obj, mot in (('G-N-LEVEL', 'T1b_LEVEL（日 CVR 持续坏尾）', '持续坏状态与跨界分开（plan §2.2）'),
                          ('G-N-OWNCHANGE', 'T1b_OWNCHANGE（昨日参考固定的股票自身跨界）', '股票变化与参考分布变化分开（plan §2.2）'),
                          ('G-N-RECONFIRM', 'RECONFIRM（坏状态解除 ∧ 自然门重新认可才提前恢复）', '重入不只 ALLOW / BLOCK（plan §2.3）'),
                          ('G-N-XR', 'XR_DOWN / XR_UP / XR_BOTH（带同行收益符号与相对位置的行业豁免）', '行业豁免不只相对最差名次（plan §2.4）'),
                          ('G-N-ENTRYEXIT', 'ENTRY × EXIT 四账户（只停新买 / 只卖已有 / 都做）', '先停止新增坏票与卖掉已有坏票分开（plan §0.1 第 6 条）'),
                          ('G-N-ORIGDUE', 'FUNDING_REMAIN（再投资只持至原标签 due）', '再投资的剩余机会窗（plan §2.5）')):
        R.append(g(g_id=gid, author='Web plan v1.1（新增设计）', exact_statement='新增对象：%s' % obj, created_at='2026-10-17（plan v1.1）', created_before_measurement='YES（本轮 G1 为第一道）',
                   source_facts='F1 / F2 / F7（plan §3.1）', motivation=mot, competing_explanation='见 plan 对应节；更精确的条件可能过窄而无用', proposed_estimand='见 plan §4–§6 与 Q 卡',
                   probe_window='推导段（G1）', status='开放', operation_type='NEW_MEASUREMENT_PROBE', data_exposure='未测', expected_statement_provenance='AUTHOR_REPORTED',
                   tested_or_unmeasured='UNMEASURED', pre_or_post_exposure='PRE_EXPOSURE', evidence_vs_candidate_explanation='待测'))
    cands = [('C-A', '账户级退出（信息触发）', '主线（本轮 966 配置）'), ('C-B', '剂量 × size', 'D-1（下一轮候选）'), ('C-C', '持仓权重倾斜（日龄 / 信号强度 / 慢质量）', 'D-2'),
             ('C-D', 'proposal §3.9 称发散 12 个候选，§3.4 原文未列 C-D（编号跳过）', '无（原文缺）'), ('C-E', '成本与容量线', 'D-3'), ('C-F', '分钟量作 K 腿活动分布', 'D-6'),
             ('C-G', '条件退出：信息型 vs 流动性型', '并入 C-A（T3a / X1 / XR）'), ('C-H', '新数据层', 'D-7（本轮默认关）'), ('C-I', '2024–26 弱化 / 拥挤包', 'D-4'),
             ('C-J', '事件定义 / 第二策略', '用户锁定，只列'), ('C-K', '否决位置拆分', 'D-5'), ('C-L', 'E7', 'HOLD')]
    for cid, what, where in cands:
        R.append(g(g_id='G-CC-%s' % cid, author='CC 决策端（proposal v2 §3.4）', exact_statement='%s：%s' % (cid, what), created_at='2026-10-17（proposal v2）',
                   created_before_measurement='YES' if cid != 'C-A' else 'PARTIAL（B2 已暴露）', source_facts='proposal §3.4 / §3.5', motivation='发散候选（构思目录，不进实测命中率分母）',
                   proposed_estimand=where, status='开放' if cid != 'C-D' else 'NO_NEW_DIRECTION_YET', operation_type='NEW_MEASUREMENT_PROBE' if cid in ('C-A', 'C-B', 'C-C', 'C-E', 'C-F', 'C-G', 'C-I', 'C-K') else 'NOT_APPLICABLE',
                   data_exposure='见 proposal', expected_statement_provenance='AUTHOR_REPORTED', tested_or_unmeasured='CATALOG', pre_or_post_exposure='MIXED',
                   evidence_vs_candidate_explanation='构思目录'))
    for gid, what in (('G-PRE-01', 'v1 自审：触发族缺放量上涨（→ T3b / T3c）'), ('G-PRE-02', 'v1 自审：T4"真实 VWAP"与日频 CVR 恒等问题（→ S0-3）'),
                      ('G-PRE-03', 'v1 自审：缺重入处理与资金去向（→ RE 两臂 + 资金三口径）')):
        R.append(g(g_id=gid, author='CC 决策端（proposal v2 §2.2 / §10）', exact_statement=what, created_at='2026-10-17', created_before_measurement='YES',
                   status='技术PASS', operation_type='PRE_EXECUTION_DESIGN_REPAIR', data_exposure='无市场 probe', tested_or_unmeasured='DESIGN_REPAIR', pre_or_post_exposure='PRE_EXPOSURE',
                   evidence_vs_candidate_explanation='设计修补，不是 probe 后 miss'))
    R.append(g(g_id='G-XP-01', author='CC 决策端（proposal v2 §3.6）', exact_statement='quant_factor_notes ACT / ESGN：个股放量下跌延续、行业抛售日超跌反弹、放量上涨反转（分类逻辑迁移）',
               created_at='2026-10-17', created_before_measurement='YES（I11 域未测）', status='开放', operation_type='CROSS_PROJECT', data_exposure='另项目已暴露（数值不移植）',
               tested_or_unmeasured='UNMEASURED', pre_or_post_exposure='CROSS_PROJECT', evidence_vs_candidate_explanation='跨项目线索，不并入 I11 命中率'))
    return pd.DataFrame(R)[G_COLS]


E_DEF = [
    ('E01', 'G-F2-01', 'SOURCE_T1b主配置NATIVE/ALLOW净FULL相对同引擎父>0，并相对amount随机>0；不预言各段全正', 'Q02',
     'MAIN_EXIT：主对象 FULL D（FEASIBLE）> 0；且 FULL D − AMOUNT_MATCH 随机均值 > 0', '主对象 A4b_CVRv5 / Q0 α .25 / HG10 / H5 / T1b / ENGINE_NATIVE / ALLOW', 'B2 四段 overlay 已暴露（冻结源账本，非账户）'),
    ('E02', 'G-F2-01', '主LEVEL在同金额/日龄下不弱于EDGE；原生LEVEL可能因多退而不同', 'Q03',
     'LEVEL_WORST_1D 同金额 / 日龄控制下：T1b_LEVEL 主配置（主母体 HG10 H5 NATIVE ALLOW）FULL D ≥ T1b_EDGE；另报原生 D 差', 'T1b_LEVEL vs T1b_EDGE（主母体 H5 坐标）', 'B2 LEVEL 对照 ≈ 跳升（E6n）'),
    ('E03', 'G-F2-03', '对日LEVEL卖已有库存相对只停新买仍有正FULL贡献', 'Q06',
     'ENTRY × EXIT：Y11 − Y10（T1b_LEVEL、主母体三记忆、两资金）FULL D > 0', 'ENTRY_EXIT 族 T1b_LEVEL', '无'),
    ('E04', '', 'T3b在旧父持有风险集的剩余收益相对同日龄匹配更弱；T3a方向开放并报延续/反转', 'Q07',
     'G1 / D 表：T3b15 触发批次的剩余超额（至原 due）− 同日同日龄全部风险集批次 < 0（父影子风险集，全程）', '主母体 HG10 H5 父影子风险集', 'F7 ACT 线索（另项目）'),
    ('E05', 'G-N-XR', 'XR_DOWN相对X1_RANK在同豁免预算下提高保留集剩余收益；账户全净另评', 'Q08',
     '保留集（T3a15 触发但被豁免者）剩余超额：XR_DOWN 豁免集 − X1_RANK 豁免集 > 0（同豁免预算口径见 D 表）；账户 T3a15_XR − T3a15_X FULL D 另列', 'T3a15_XR vs T3a15_X（主母体 H5）', '无'),
    ('E06', 'G-N-RECONFIRM', 'RECONFIRM对BLOCK的主T1b/LEVEL全净FULL增量>0；代价是早恢复可能再遇坏状态', 'Q10',
     'REENTRY_PAIR：RECONFIRM − BLOCK（T1b 与 T1b_LEVEL，主母体 HG10 H5 NATIVE）FULL D > 0', 'RECONFIRM 族 T1b / T1b_LEVEL', '无'),
    ('E07', 'G-F2-02', 'NEXT比NATIVE的增量更易被同规模冲击削弱', 'Q13',
     'FROZEN_COST_STRESS（A = 5 亿、κ = .5）：(D_NEXT − D_NEXT_imp) > (D_NATIVE − D_NATIVE_imp)，4 主触发 × 主母体三记忆 × 两重入', 'FUNDING_NEXT vs CORE NATIVE（主母体 H5）', 'E6n B2 NEXT 费用 +.32 ~ +.66'),
]


def e_rows():
    R = []
    for eid, gids, pred, qid, contrast, pop, prior in E_DEF:
        R.append(dict(e_id=eid, g_ids=gids, author='Web plan v1.1（plan §12）', original_version='plan v1.1 ce9e98c2', exact_prediction=pred, prediction_or_question='PREDICTION',
                      selected_before_outcome='YES（A1 冻结于任何退出账户读数之前）', prior_exposure=prior, first_stage_evidence='PENDING（G1）', formal_contrast=contrast,
                      target_population=pop, unit='ann_pp' if eid not in ('E04', 'E05') else 'bp', comparison_ids='见 reports/query_registry_E6o.csv', support_ids='FULLHIST',
                      query_id='Q-%s' % eid, result='PENDING', evidence_strength='PENDING', miss_root='', next_change=''))
    return pd.DataFrame(R)[E_COLS]


def cards():
    txt = open(O.P(PLAN), encoding='utf-8').read().splitlines()
    rows = []
    for ln in txt:
        m = re.match(r'^\| (Q\d\d) ([^|]*)\| ([^|]*)\| ([^|]*)\| ([^|]*)\|$', ln)
        if m:
            rows.append(dict(q_id=m.group(1), title=m.group(2).strip(), motivation=m.group(3).strip(), discrimination=m.group(4).strip(), miss_update=m.group(5).strip()))
    if len(rows) != 18:
        raise RuntimeError('Q 卡 %d != 18' % len(rows))
    return pd.DataFrame(rows)


def cc_carried():
    txt = open(O.P('inputs', 'E6o_brief_appendix_schema_probes.md'), encoding='utf-8').read().splitlines()
    rows = []
    for ln in txt:
        m = re.match(r'^\| (CC-\d\d) \| (.*) \| ([^|]*) \| ([^|]*) \|$', ln)
        if m:
            rows.append(dict(cc_id=m.group(1), original_statement=m.group(2).strip(), source=m.group(3).strip(), comparability=m.group(4).strip()))
    if len(rows) != 12:
        raise RuntimeError('CC 携带 %d != 12' % len(rows))
    return pd.DataFrame(rows)


def policy_profile():
    src = O.E6N('registration', 'policy_profiles_E6n.json')
    base = json.load(open(src, encoding='utf-8'))
    return dict(
        profile='POLICY_E6O_PARENT_Q', source_file='E6n registration/policy_profiles_E6n.json', source_sha256=O.sha_file(src),
        inherited_conditions=base['conditions'], inherited_judgement_order=base['judgement_order'], delta_main=base['delta_main'],
        mapping={
            'c1_segment_tolerance_ok': 'c：四段 D ≥ −.10（D = C_ACCOUNT − 同 Q0 α .25 / 同记忆 / 同 H / 同现金引擎 / 同情景 / 同支持的无退出 P_ACCOUNT）',
            'c2_year_positive_share': 'd：逐年 D > 0 的年份份额；c2_ok = 正年数 ≥ 12/17（10/17 敏感并印）',
            'c3_full_sc_same_sign': 'e_capital：sign(FULL D) = sign(FULL D_sc)，tol 1e−9；D_sc = 同资本视图：逐日两边净超额按 min(x_c, x_p) / x 缩放（交易后敞口共同下缩，非闭环重跑；plan §8.4）',
            'c4_random_post_ok': 'e_random：两后段 real − rand_mean ≥ 2·MCSE；随机 = AMOUNT_MATCH（同风险集同意向金额退出；ENTRY_ONLY 用 ENTRY_RANDOM；未排 → 不可判）',
            'c5_impact_ok': 'f：FROZEN_COST_STRESS（A = 5 亿元、κ = .5；固定路径再扣 Σ|Δw|^1.5·κ·σ_PRE·√(A/ADV_PRE)）后四段 D ≥ −.10；A = 10 亿 κ = 1 压力列并印',
            'c6_declared_ok': '机制 / 配置事前声明（A1 冻结件内）',
            'positive': 'FULL D ≥ +.10',
            'port3t_ok': 'PORT3_T_EXIT_MAPPING：全组合目标（幸存旧仓 + 意向买）在 T 的 clean 市值分位加权均值，相对父 ×100，四段段均值 ∈ [−3, +3]（未知 size 份额并印）'},
        verdict_rule='通过 = c1 ∧ c2 ∧ c5 ∧ positive ∧ c3 ∧ c4 ∧ port3t；任一可算条件不过 → 不通过；全部可算条件都过但有不可算条件（如 c4 无随机）→ 不可判',
        research_status=dict(
            未覆盖='status ≠ COMPUTED，或 FULL 无实际退出意向（入场暂停账户：无取消买入），或支持段 < 2',
            方向不支持='FULL D ≤ 0 且 G4 ≤ 0',
            有改善点估='FULL D ≥ +.10 且 G4 > 0 且 FULL D_source > 0',
            结构依赖='FULL D > 0 且（G4 ≤ 0 或 四段中 ≥ 2 段 < 0 或 FULL D_source ≤ 0）',
            证据有限='其余（如 0 < FULL D < .10 且 G4 > 0；FULL ≤ 0 但 G4 > 0）',
            note='研究状态不是资格门（plan §11.3）；按 A1 冻结的规则从机器表现算'),
        partial_history=dict(profile='PARTIAL_HISTORY_RESEARCH_V1', applies_to='T4a / T4b / T5（MINUTE_2013 支持）', segments=['2013-2014', '2015-2018', '2019-2023', '2024-2026'],
                             evaluable_years='2013（2013-08-01 起，部分年）…2026（至 03-27，部分年）共 14 年；正年数要求 ceil(2Y/3) = 10',
                             tolerance='同 c（四段 ≥ −.10）；不额外加严', note='旧 17 年政策对分钟触发照旧不可判（verdict 列按 17 年原式给不可判 / 通过 / 不通过；研究列另给）'),
        frozen_cost_stress=dict(A_main=5e8, kappa_main=0.5, A_stress=1e9, kappa_stress=1.0, formula='cost_d = κ √A Σ_i |Δw_i|^1.5 σ_PRE,i / √ADV_PRE,i（Δw = 净市场订单 / NAV；σ、ADV 为 T−20…T−1）'),
        hac_lags=['H', '2H', 'max(H,20)'], bootstrap=dict(reps=2000, block_main=20, block_sens=60, method='stationary（几何块长），相关账户共同抽日期'),
        mapping_unresolved=['LEGACY_EDIT5（编辑日口径，退出账户无对应编辑定义 → 不计算，只在 profile 记）', 'PROPOSED_PORT3_LAG1 / EXEC_*（印出列，非正式；本轮不计算）'],
        deployment_authorized=False)


def main():
    od = O.P('registration')
    G = g_rows()
    E = e_rows()
    O.atomic_write_csv(os.path.join(od, 'ledger_G_E6o.csv'), G)
    O.atomic_write_csv(os.path.join(od, 'ledger_E_E6o.csv'), E)
    O.atomic_write_csv(os.path.join(od, 'cards_E6o.csv'), cards())
    O.atomic_write_csv(os.path.join(od, 'cc_carried_E6o.csv'), cc_carried())
    pp = policy_profile()
    O.atomic_write_json(os.path.join(od, 'policy_profile_E6o.json'), pp)
    app = open(O.P('inputs', 'E6o_brief_appendix_schema_probes.md'), encoding='utf-8').read()
    i0 = app.index('## B. SCHEMA 合同')
    i1 = app.index('## C. 闭包门')
    schema_sha = hashlib.sha256(app[i0:i1].encode('utf-8')).hexdigest()
    srcfn = json.load(open(O.P('diagnostics', 'source_fn_sha256_E6o.json')))
    code = {os.path.basename(p): O.sha_file(p) for p in sorted(glob.glob(os.path.join(os.path.dirname(O.__file__), 'e6o_*')))}
    frozen = {}
    for f in ('registry_E6o.csv', 'comparisons_E6o.csv', 'comparisons_extra_E6o.csv', 'run_plan_E6o.csv', 'level_worst_refs_E6o.csv', 'random_scope_E6o.csv',
              'trigger_definitions_E6o.csv', 'ledger_G_E6o.csv', 'ledger_E_E6o.csv', 'cards_E6o.csv', 'cc_carried_E6o.csv', 'policy_profile_E6o.json'):
        frozen[f] = O.sha_file(os.path.join(od, f))
    st0 = pd.read_csv(O.P('diagnostics', 'stage0_E6o.csv'), keep_default_na=False, na_values=[''])
    s00 = st0[st0.probe_id == 'S0-0'].set_index('key')['value'].to_dict()
    fz = dict(plan_sha256=O.sha_file(O.P('inputs', 'E6o_plan_web_final.md')), spec_sha256=O.sha_file(O.P('inputs', 'e6o_spec_tests.py')),
              brief_sha256=O.sha_file(O.P('inputs', 'E6o_account_exit_stage.md')), appendix_sha256=O.sha_file(O.P('inputs', 'E6o_brief_appendix_schema_probes.md')),
              d_script_sha256=O.sha_file(O.P('verify', 'decision', 'E6o_D_stage2.py')), schema_contract_sha256=schema_sha,
              policy_file_sha256=O.sha_file(O.E6N('registration', 'policy_profiles_E6n.json')), source_fn_sha256=srcfn, data_cutoff=O.CUTOFF, protocol='v1.6', mode='B',
              authorized_by='用户（会话内转交 brief 与决策端开工消息 = 开工与方式 B 授权；转交消息未写"方式 A"）', authorized_at='2026-10-17 21:38（47 时间，开工 WORKLOG 行）',
              written_at=time.strftime('%Y-%m-%d %H:%M:%S'), source_t1b_binding=s00.get('SOURCE_B2_TRIGGER_BINDING'), source_cash_model=s00.get('SOURCE_CASH_MODEL'),
              frozen_registration_sha256=frozen, code_sha256=code, cache_dir=os.path.basename(O.cache_dir()),
              counts=json.load(open(os.path.join(od, 'registry_facts_E6o.json'))), deployment_authorized=False, e7_read=False,
              amendments=[], note='A1 冻结：此后任何经济规则变动都是 amendment（版本号 + 受影响依赖）；技术缺陷修复可继续（brief §3 第 9 条）。registry 的 status 列为运行状态，交付时更新为 COMPUTED，其余列不变（闭包期核）')
    O.atomic_write_json(os.path.join(od, 'freeze_E6o.json'), fz)
    print(json.dumps(dict(G=len(G), E=len(E), schema_sha=schema_sha[:16], frozen=len(frozen), code=len(code)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
