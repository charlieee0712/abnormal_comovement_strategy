# -*- coding: utf-8 -*-
"""E6l Stage B 与登记冻结（brief §1.4 / W11 / W12 / §6；plan §3 / §10 / §12 / §13.2；附录 A1-3 / D）。不读任何收益。
  --stage-b   registration/policy_profiles_E6l.json（E6k policy_profiles + amend_1 / amend_2 逐句转录 + W12 补写：PORT3_T 正式列、
              policy_provisional = false、LEGACY_EDIT5 未定义段 = UNDEFINED、状态词表、新算子 NOT_AUTHORIZED、同构对象 SECOND_EVALUATION）；
              registry/cards_stageB_E6l.csv（16 卡 × 模板 v4：①②④⑨⑩ 取 plan 卡原文，⑬ = PENDING_DERIV_MDE80（推导段账户后由 MDE80 表机械填），
              ⑮–⑱ 由 A0 机械字段（t15_account / t16_timescale / t17_random / t18_state）按 query 对象集合汇总；绑定比较 kind × 条数）；
              registry/hypothesis_lineage_E6l.csv（plan 16 卡 adopted；proposal 11 卡与 plan §1.3 更正的 6 句 superseded）；
              registry/P_objects_E6l.csv（P 包 = 主展示 72 + α .5 剂量 72 + α .125 邻域 72 + PARENT 160）；
              registration/preregistration_P_E6l.md / preregistration_B_E6l.md
  --freeze    （A1-auto --pre 全 PASS 后）P / B 两包清单（registry / 登记文档 sha）→ record_B_preauthorized_E6l.json（方式 B：用户原话 + 日期 +
              B 包清单 sha；生效条件）→ record_B_conditions_receipt_E6l.json（Stage 0 全 PASS + A1-auto 全 PASS + 冻结清单 sha）"""
import e6l_boot  # noqa: F401
import os
import sys
import json

import numpy as np
import pandas as pd

import e6l_core as L

PROPOSAL_CARDS = [('P-Q1', 253, 'E6l-Q1 滞回 vs 平滑', 'Q09|Q06|Q04'), ('P-Q2', 254, 'E6l-Q2 规则 / 信息 / 交互份额按形态', 'Q02'),
                  ('P-Q3', 255, 'E6l-Q3 叠加（替代 / 互补比率）', 'Q09'), ('P-Q4', 256, 'E6l-Q4 剂量–倾斜前沿', 'Q11'),
                  ('P-Q5', 257, 'E6l-Q5 时间尺度', 'Q04|Q15'), ('P-Q6', 258, 'E6l-Q6 状态条件（读法）', 'Q12|Q13'),
                  ('P-Q7', 259, 'E6l-Q7 状态相依 b', 'Q12'), ('P-Q8', 260, 'E6l-Q8 并集核资本视图', 'Q14'),
                  ('P-Q9', 261, 'E6l-Q9 S 对照', 'Q15'), ('P-Q10', 262, 'E6l-Q10 对同结构随机', 'Q10'), ('P-Q11', 263, 'E6l-Q11 方法', 'Q16')]
PLAN_CORRECTIONS = [('PC-1', 'α .5 = 机制读数配置', '不预设为机制真相；α .5 同 72 行为剂量面板，α .125 为邻域（plan §1.3 / §9.1；brief A2）', 'Q11'),
                    ('PC-2', 'Munion 同资本 FULL_sc ≥ +.10 且 ≥ 3/4 段作门', '不加门；FULL 与 FULL_sc 双主视图并印（plan §10.3；brief A3）', 'Q14'),
                    ('PC-3', '按换手插值挑最好平滑窗', '撤销；真实前沿 + 逐对费用交叉点 c* + 单位收费量收益诊断（plan §2.8 / §7.6；brief A5）', 'Q11'),
                    ('PC-4', 'R-HG：同数量折让全给非成员', '改 R-MARK：本路径自己的 G_{t−1} 标记在分区内置换（plan §7.3；brief A4）', 'Q10'),
                    ('PC-5', '16 格正号给二项概率', '不给朴素 binomial；报完整符号矩阵与共享日期重采样（plan §11.2）', 'Q13'),
                    ('PC-6', '状态样本 n ≥ 120 才报告', '不设 n 门；短样本照报带 n 与区间精度限制（plan §6.1 / §11.2a）', 'Q13')]


def policy_profiles():
    e = json.load(open(L.K6('registration', 'policy_profiles_E6k.json'), encoding='utf-8'))
    a1 = json.load(open(L.K6('registration', 'policy_profiles_E6k_amend_1.json'), encoding='utf-8'))
    a2 = json.load(open(L.K6('registration', 'policy_profiles_E6k_amend_2.json'), encoding='utf-8'))
    cc = dict(e['common_conditions'])
    cc['e_random'] = ('对 LEGACY_POLICY_RANDOM 两后段：rmr = real − 随机均值（net8 年化，各段各自有效日）；逐段 rmr > 0 且 rmr ≥ 2·MCSE → 正已定；'
                      'rmr ≤ 0 且 |rmr| ≥ 2·MCSE → 非正已定；其余 MC_UNRESOLVED；任一段非正已定 → FAIL；两段正已定 → PASS；'
                      '未排随机 → RANDOM_NOT_SCHEDULED（不可判）；K0 规则对象 → NO_NEW_CONTENT_TO_PERMUTE（不可判）')
    cc['d'] = ('逐年正数 ≥ 12 / 17（2010–2026，2026 截至 03-27 partial）；另印 2010–2025 16 年与 10 / 17 敏感列，不替换主分母')
    cc['simplicity'] = ('三句加法（PX1）只对原生四测量 NATIVE 的 S / M / Q0 / C1；E6l 无 SM 对象（SM 部分 NOT_APPLICABLE）；新算子 / 新表达 '
                        'replacement_preference_status = NOT_AUTHORIZED（不 chosen、不继承三句加法资格）')
    cc['verdict_order'] = 'c、d、f、正向门槛、e资本、e随机、size(profile)'
    sp = dict(e['size_profiles'])
    sp['LEGACY_EDIT5'] = dict(sp['LEGACY_EDIT5'])
    sp['LEGACY_EDIT5']['rule'] = sp['LEGACY_EDIT5']['rule'].replace('四段全 NaN → N/A', '只在有编辑日的段上判；四段全无编辑 → UNDEFINED（纪律 ㊿ / 56）')
    sp['PROPOSED_PORT3_T'] = dict(sp['PROPOSED_PORT3_T'], role='正式列（用户 RULING 第 2 项；policy_provisional = false；形成日 T clean 市值分位）')
    sp['EXEC_LEADER_VS_PARENT'] = dict(sp['EXEC_LEADER_VS_PARENT'], role='只披露（brief §6；不给 verdict 列）')
    items = a1['items'] + a2['items']
    for it in items:
        if it['id'] == 'PX1':
            it['decision_E6l'] = '同 E6k；测量 Q 即 Q0；E6l 无 SM 对象，SM 条款 NOT_APPLICABLE'
        if it['id'] == 'PX2':
            it['decision_E6l'] = ('同 E6k，并印的配对差扩为：相对同形态 NATIVE_C1、同测量 NATIVE、同算子 C1、同算子 Q0、Q0 HG10、规则 ONLY（K0 同算子）'
                                  '（FULL 与 G4）')
        if it['id'] == 'PX3':
            it['decision_E6l'] = ('LEGACY_POLICY_RANDOM 与 CONTENT_COND_ISK_P5 排在全部非 K0 对象的 H ∈ {1, 2, 3, 5, 10, 20}（含全部 α）；'
                                  '其余 H 的 e-随机 = RANDOM_NOT_SCHEDULED（不可判）')
        if it['id'] == 'PX6':
            it['decision_E6l'] = 'K0 的 OLD_RULE / EDGE_OLD 规则对象（α0，不读新测量）= NO_NEW_CONTENT_TO_PERMUTE（不可判，不记 FAIL）'
    items.append(dict(id='PX7', topic='LEGACY_EDIT5 未定义段（W12 补写）',
                      decision='只在有编辑日（gap_T 有定义）的段上判 |mean_t gap_t|·100 ≤ 5；四段全无编辑 → UNDEFINED；状态词禁用 N/A / NA / nan / null'))
    items.append(dict(id='PX8', topic='同构对象与首评标签（W08 / W12）',
                      decision=('E6k 同构对象 evidence_exposure = SECOND_EVALUATION_SAME_HISTORY，只作锚与基线，不进"本轮新证据"栏；其余新对象 = '
                                'NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY；每对象七列证据状态 economic_effect / policy_profile / policy_result / '
                                'mechanism_status / historical_exposure / replacement_status / deployment_authorized（plan §10.4）')))
    out = dict(record_id='E6L-POLICY-PROFILES-20260930', kind='政策 profile 与执行口径（读数前；brief W12 / §6；plan §10）',
                policy_provisional=False, economic_ruling='E6k RULING 第 2 项：PROPOSED_PORT3_T 为正式列（brief W11 (c) / W12）',
                source_e6k=dict(policy_profiles_E6k=L.sha_file(L.K6('registration', 'policy_profiles_E6k.json')),
                                amend_1=L.sha_file(L.K6('registration', 'policy_profiles_E6k_amend_1.json')),
                                amend_2=L.sha_file(L.K6('registration', 'policy_profiles_E6k_amend_2.json'))),
                common_conditions=cc, size_profiles=sp, verdict_profiles=['PROPOSED_PORT3_T', 'LEGACY_EDIT5', 'PROPOSED_PORT3_LAG1', 'EXEC_DISCLOSE_ONLY'],
                disclosure_only_profiles=['EXEC_LEADER_VS_PARENT'], disclosure_columns=e['disclosure_columns'],
                status_words=list(L.STATUS_WORDS), forbidden_status_words_ref='e6l_core.FORBIDDEN_STATUS（读写一律 keep_default_na=False）', items=items,
                labels=['economic_effect', 'policy_profile', 'policy_result', 'mechanism_status', 'historical_exposure', 'replacement_status',
                        'deployment_authorized = false'],
                first_look_label=L.LABEL_FIRST_LOOK, second_label=L.LABEL_SECOND, no_new_gates='plan §10.3：Munion 同资本、R-MARK ≥ +.10、随机通过率、状态 n、同时带下界都不是门',
                edge_list='边缘清单列全部条件距离（不只"只差一条"）', written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), no_returns_read_before=True)
    out = norm_status(out)
    out['normalization_note'] = ('E6k 原文中的缺失类状态词（清单见 e6l_core.FORBIDDEN_STATUS）在本轮转录时统一写 UNDEFINED（纪律 56；brief W12）；原件逐字以 source_e6k 的 sha 为准，'
                                 '规则语义不变')
    return out


def norm_status(x):
    """转录时把 E6k 原文的 N/A / NA / NaN 状态词写成 UNDEFINED（只在文本里作状态词出现处；sha 字段不动）。"""
    import re
    if isinstance(x, dict):
        return {k: (v if k in ('source_e6k',) else norm_status(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [norm_status(v) for v in x]
    if isinstance(x, str):
        y = x.replace('N/A', 'UNDEFINED').replace('NaN', 'UNDEFINED')
        return re.sub(r'(?<![A-Za-z_])NA(?![A-Za-z_])', 'UNDEFINED', y)
    return x


def card_field(text, key):
    if key not in text:
        return 'SEE_CARD_TEXT'
    s = text.split(key, 1)[1]
    for stop in ('**动机', '**工作假设', '**对照', '**判别', '**更新', '**削弱', '**竞争预测', '**检查', '**读法'):
        if stop in s and stop != key:
            s = s.split(stop, 1)[0]
    return s.strip(' ：:*').strip()


def stage_b(tag=''):
    reg = L.P('registry')
    rgn = L.P('registration')
    D = L.read_csv_keep(os.path.join(reg, 'descriptors_E6l.csv'))
    C = L.read_csv_keep(os.path.join(reg, 'cards_E6l.csv'))
    Qy = L.read_csv_keep(os.path.join(reg, 'query_registry_E6l.csv'))
    Q2O = L.read_csv_keep(os.path.join(reg, 'question_to_objects_E6l.csv'))
    CM = L.read_csv_keep(os.path.join(reg, 'comparison_manifest_E6l.csv'), usecols=['cmp_id', 'kind', 'view', 'query_id'])
    plan_sha = L.sha_file(L.P('PLAN_COPY.md'))
    pp = policy_profiles()
    p_pol = os.path.join(rgn, 'policy_profiles_E6l.json')
    if os.path.exists(p_pol):
        raise RuntimeError('policy_profiles_E6l.json 已存在（只增不删）')
    L.atomic_write_json(p_pol, pp)
    Dx = D.set_index('desc_id')
    rows = []
    for r in C.itertuples():
        qids = r.queries.split('|')
        objs = set(Q2O[Q2O.query_id.isin(qids)].desc_id) - {'ALL_DESCRIPTORS'}
        sub = Dx.loc[sorted(objs)] if objs else Dx.iloc[:0]
        cm = CM[CM.query_id.isin(qids)]
        text = r.text
        rows.append(dict(card=r.card, plan_line=r.plan_line, title=r.title, queries=r.queries, n_objects=len(sub) if objs else len(D),
                         t01_mechanism=card_field(text, '**动机'), t02_direction=card_field(text, '**工作假设'),
                         t04_competitors_discriminators=card_field(text, '**判别') if '**判别' in text else card_field(text, '**对照'),
                         t09_null_reverse_reading=card_field(text, '**更新'), t10_unit='对象（描述符 = 测量 × 母体 × α × H × 算子）',
                         t13_decidability='PENDING_DERIV_MDE80（推导段账户后由 paired_mde80_deriv 机械填；不改预测）',
                         t15_account='；'.join(sorted(sub.t15_account.str.split('（').str[0].value_counts().head(4).index)) if objs else 'ALL',
                         t16_timescale='；'.join('%s×%d' % (k, v) for k, v in sub.t16_timescale.str.replace(r'\|H=\d+$', '', regex=True).value_counts().head(6).items()) if objs else 'ALL',
                         t17_random='；'.join('%s×%d' % (k, v) for k, v in sub.t17_random.value_counts().items()) if objs else 'ALL',
                         t18_state='；'.join('%s×%d' % (k, v) for k, v in sub.t18_state.value_counts().items()) if objs else 'ALL',
                         bound_comparisons='；'.join('%s/%s×%d' % (k[0], k[1], v) for k, v in cm.groupby(['kind', 'view']).size().items()),
                         n_bound_comparisons=int(len(cm)), plan_sha256=plan_sha))
    Cb = pd.DataFrame(rows)
    p_cb = os.path.join(reg, 'cards_stageB_E6l.csv')
    L.atomic_write_csv(p_cb, Cb)
    # 假设血缘
    prop_path = L.P('E6l_proposal_copy.md')                               # 与 exec_briefs 同 sha（Stage 0 A1-1）
    prop = open(prop_path, encoding='utf-8').read().split('\n')
    prop_sha = L.sha_file(prop_path)
    X = L.read_csv_keep(os.path.join(reg, 'selection_exposure_ledger_E6l.csv'))
    lin = []
    for r in Cb.itertuples():
        objs = set(Q2O[Q2O.query_id.isin(r.queries.split('|'))].desc_id)
        ex = X[X.desc_id.isin(objs)].evidence_exposure.value_counts().to_dict() if objs else {}
        lin.append(dict(claim_id='E6L-%s' % r.card, author_role='web_plan_v1.1', exact_text=r.t02_direction, source_sha=plan_sha,
                        source_section='PLAN_COPY.md §12 L%d–L%d' % (r.plan_line, r.plan_line + 1), status='adopted', brief_id='W01',
                        executed_test_id=r.queries, outcome_query=r.queries, exposure=json.dumps(ex, ensure_ascii=False)))
    for cid, ln, title, repl in PROPOSAL_CARDS:
        lin.append(dict(claim_id=cid, author_role='decision_side_proposal', exact_text=prop[ln - 1][:800], source_sha=prop_sha,
                        source_section='E6l_proposal.md §5.7 L%d（%s）' % (ln, title), status='superseded',
                        brief_id='W01（plan §3 / §12 / §14 取代；proposal 为参考输入）', executed_test_id='NOT_APPLICABLE',
                        outcome_query='|'.join('E6L-%s-a' % q for q in repl.split('|')), exposure='见取代卡'))
    for cid, old, new, q in PLAN_CORRECTIONS:
        lin.append(dict(claim_id=cid, author_role='decision_side_proposal', exact_text=old, source_sha=prop_sha,
                        source_section='plan §1.3 / §10.3 / §14 对 proposal 的更正：%s' % new, status='superseded', brief_id='W01 / A2–A5',
                        executed_test_id='NOT_APPLICABLE', outcome_query='E6L-%s-a' % q, exposure='NOT_APPLICABLE'))
    Lg = pd.DataFrame(lin)
    p_lin = os.path.join(reg, 'hypothesis_lineage_E6l.csv')
    L.atomic_write_csv(p_lin, Lg)
    Pm = D[D.primary72 | D.dose72 | D.nbhd72 | (D.family == 'PARENT')][['desc_id', 'meas', 'mother', 'alpha', 'H', 'op', 'recipe', 'primary72', 'dose72',
                                                                            'nbhd72', 'evidence_exposure']]
    p_po = os.path.join(reg, 'P_objects_E6l.csv')
    L.atomic_write_csv(p_po, Pm)
    a0 = json.load(open(os.path.join(rgn, 'a0_manifest_E6l.json'), encoding='utf-8'))
    cnt = a0['counts']
    P_md = ['# E6l preregistration_P（P 包：固定展示与源锚；任何新收益读取前落盘）', '',
            '用途：冻结 plan §9.1 的 72 行主展示（12 配方 × 六形态，α .25 × H5）、同 72 配方的 α .5 剂量面板与 α .125 邻域、八母体 PARENT 全 H；'
            '政策合同 `registration/policy_profiles_E6l.json`（policy_provisional = false，PROPOSED_PORT3_T 正式列）；与 B 包同时冻结。', '',
            '## 1. 身份', '- PLAN_COPY.md sha256 `%s`；brief `4c55fb4b`；附录 `f5c33bc7`；spec `fb9908d6`；A0 清单 `registration/a0_manifest_E6l.json`（与 spec 逐元组相等）' % plan_sha,
            '- Stage 0：`source_manifest.json` 六类全 PASS；engine_contract.md / source_resolution.md', '',
            '## 2. 对象（`registry/P_objects_E6l.csv`，%d 个描述符 / 段）' % len(Pm),
            '- 72 主展示：Q0:NATIVE、Q0:HG10、Q0:LAG1_10、Q0:DECAY5_10、Q0:INV10、Q_D3:NATIVE、Q_D5:NATIVE、Q_D5:HG10、Q_RANK5:NATIVE、Q_RANK5:HG10、'
            'Q_DEW5:NATIVE、Q_DEW5:HG10 × 六形态，α .25 × H5；同 72 配方 α .5（剂量面板）与 α .125（邻域）；任一剂量同一正式尺子评分',
            '- PARENT：六生产形态 + R2 / A06 × H1…20（源锚；R2 / A06 只作既有研究参照曲线）', '',
            '## 3. 政策（`registration/policy_profiles_E6l.json` 全文）', '```json', json.dumps(pp, ensure_ascii=False, indent=1), '```', '',
            '## 4. 暴露（`registry/selection_exposure_ledger_E6l.csv`）',
            '- P 包内：%s' % json.dumps(D[D.desc_id.isin(Pm.desc_id)].evidence_exposure.value_counts().to_dict(), ensure_ascii=False),
            '- 已见选择史：W08 锚值与 W09 的 α .5 四段 lo / hi（selection_note 列）；E6k 的 Q H 剖面（H1 / H5 / H20）', '']
    B_md = ['# E6l preregistration_B（B 包：全部其他接入 / 机制 / 对照 / 附属；任何新收益读取前落盘）', '',
            '用途：冻结 plan §4–§11 的全部研究描述符（A0 现编）、附属 2,160 项与支持桥、随机登记、比较清单、16 张卡（模板 v4）与假设血缘；设计全文 = PLAN_COPY.md（sha `%s`）。' % plan_sha, '',
            '## 1. 计数（`registration/a0_manifest_E6l.json`）',
            '- 每段原始描述符 **%d**（块计数 %s）；目标（与 H 无关，INV 按 H）%d；任务 %d' % (cnt['raw_id_count'], json.dumps(cnt['block_counts'], ensure_ascii=False),
                                                                           cnt['targets'], cnt['tasks']),
            '- 附属：%s' % json.dumps(cnt['accessory'], ensure_ascii=False),
            '- 比较：基础 %d（SOURCE_RAW）+ 扩展 %d（%s）' % (cnt['comparisons_base'], cnt['comparisons_extended'], json.dumps(cnt['comparison_kinds'], ensure_ascii=False)),
            '- 随机：%s（首 1,024 路径；MCSE ≤ .03 按 512 增补至 8,192）' % json.dumps(cnt['randoms'], ensure_ascii=False),
            '- bootstrap 比较族：%s（2,000 × L 20 / 60，段内分层）' % json.dumps(cnt['bootstrap'], ensure_ascii=False),
            '- 暴露：%s（E6k 同构 %d）' % (json.dumps(cnt['exposure'], ensure_ascii=False), cnt['e6k_isomorphic']), '',
            '## 2. Stage A（掩码层事实，推导两段；`results/stage_a/`，不读收益）',
            '- mask_facts_deriv_E6l.csv（每目标 × 段）、measure_facts / rmark_partition / state_days / calibration；A2-7 与 E6k mask_facts 同构目标逐值（1e−9）', '',
            '## 3. 16 张卡（`registry/cards_stageB_E6l.csv`：模板 v4 ⑮–⑱ 由 A0 机械字段汇总；⑬ = 推导段 MDE80 后机械填；卡片原文 PLAN_COPY 逐字）'] + \
        sum([['### %s（PLAN_COPY L%d）' % (r.title, r.plan_line), '- queries：%s；绑定比较 %d 条' % (r.queries, r.n_bound_comparisons),
              '- ⑮ %s' % r.t15_account, '- ⑯ %s' % r.t16_timescale, '- ⑰ %s' % r.t17_random, '- ⑱ %s' % r.t18_state, ''] for r in Cb.itertuples()], []) + [
        '## 4. 假设血缘（`registry/hypothesis_lineage_E6l.csv`）',
        '- plan 16 卡 adopted（W01）；proposal §5.7 的 11 卡与 plan 对 proposal 的 6 处更正 superseded（plan §1.3 / §10.3 / §14；proposal 为参考输入）', '',
        '## 5. 读数与授权边界（方式 B）',
        '- 推导两段 masks（已算，Stage A）→ accounts → 推导段随机首 1,024 → MC 增补 → `seal_deriv.json` → part1 + 记录 B 草稿 → 后段（`e6l_core.post_gate`：'
        '`record_B_preauthorized_E6l.json` + 条件回执 all_pass + 冻结 B 包清单 sha 未变）',
        '- 不按推导段收益预筛或改网格；不在出数后选 profile / 随机机制 / bootstrap 块长；新算子不 chosen；任何语义 amendment 使后段授权失效（W11）']
    pP = os.path.join(rgn, 'preregistration_P_E6l.md')
    pB = os.path.join(rgn, 'preregistration_B_E6l.md')
    L.atomic_write_text(pP, '\n'.join(P_md) + '\n')
    L.atomic_write_text(pB, '\n'.join(B_md) + '\n')
    L.write_receipt('stage_b' + ('_' + tag if tag else ''), [p_pol, p_cb, p_lin, p_po, pP, pB], 'SUCCEEDED', cards=len(Cb), lineage=len(Lg), P_objects=len(Pm))
    print('Stage B：卡 %d；血缘 %d；P 对象 %d' % (len(Cb), len(Lg), len(Pm)), flush=True)
    return 0


def freeze():
    reg = L.P('registry')
    rgn = L.P('registration')
    a1n = 'a1_auto_E6l%s.json' % L.last_rerun('a1_auto_pre')[len('a1_auto_pre'):]
    a1 = json.load(open(os.path.join(rgn, a1n), encoding='utf-8'))
    sm = json.load(open(L.P('source_manifest.json'), encoding='utf-8'))
    if not (a1.get('all_pass') and sm.get('stage0_all_pass')):
        raise RuntimeError('冻结前提不满足：Stage 0 %s / A1-auto %s' % (sm.get('stage0_all_pass'), a1.get('all_pass')))
    for nm in (L.MANIFEST_P, L.MANIFEST_B, L.AUTH_PRE, L.AUTH_COND):
        if os.path.exists(os.path.join(rgn, nm)):
            raise RuntimeError('%s 已存在（只增不删）' % nm)
    reg_files = sorted(f for f in os.listdir(reg) if f.endswith('.csv'))
    regsha = {f: L.sha_file(os.path.join(reg, f)) for f in reg_files}
    docs = {f: L.sha_file(os.path.join(rgn, f)) for f in ('a0_manifest_E6l.json', 'policy_profiles_E6l.json', a1n,
                                                         'authorization_intake_E6l.json', 'preregistration_P_E6l.md', 'preregistration_B_E6l.md')}
    docs.update({f: L.sha_file(L.P(f)) for f in ('PLAN_COPY.md', 'engine_contract.md', 'source_resolution.md', 'source_manifest.json')})
    sa = {os.path.basename(p): L.sha_file(p) for p in sorted(__import__('glob').glob(L.P('results', 'stage_a', '*.csv')))}
    D = L.read_csv_keep(os.path.join(reg, 'P_objects_E6l.csv'), usecols=['desc_id'])
    nP = len(D)
    now = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    for nm, objs in (('P', nP), ('B', 34120 - nP)):
        L.atomic_write_json(os.path.join(rgn, '%s_package_manifest_E6l.json' % nm),
                            dict(package=nm, written_at=now, version=L.VERSION, preregistration='preregistration_%s_E6l.md' % nm,
                                 registry_sha256=regsha, registration_docs_sha256=docs, stage_a_sha256=sa, objects_per_segment=objs,
                                 authorization='方式 B（record_B_preauthorized_E6l.json）', no_returns_read_before=True))
    man_sha = L.sha_file(os.path.join(rgn, L.MANIFEST_B))
    intake = json.load(open(os.path.join(rgn, 'authorization_intake_E6l.json'), encoding='utf-8'))
    pre = dict(record_id='E6L-RECORD-B-PREAUTHORIZED-%s' % pd.Timestamp.now().strftime('%Y%m%d'), mode='B', written_at=now,
               user_forwarding_message_quote=intake.get('user_forwarding_message_quote'), executor_question_quote=intake.get('executor_question_quote'),
               user_answer_quote=intake.get('user_answer_quote'), user_quote_date=intake.get('user_quote_date'),
               scope='E6l 完整清单：推导两段 + 两后段的全部登记对象、附属、随机与分析（P / B 两包；brief §5 A2 次序）',
               frozen_manifests={L.MANIFEST_P: L.sha_file(os.path.join(rgn, L.MANIFEST_P)), L.MANIFEST_B: man_sha},
               conditions=['Stage 0 六类全 PASS（source_manifest.json stage0_all_pass）', 'A1-auto --pre 全 PASS（registration/a1_auto_E6l.json）',
                           '进入后段时 B 包清单 sha 不变（任何语义 amendment 使后代授权失效，W11）'],
               not_authorization=['不含生产 / 地基 / v2 / v3 / U34 / U35 / I11 / DEV / 源时钟改动', 'deployment_authorized = false 不变',
                                  '不含 E7；不含 E6k 38 遗留进程处置'],
               source='brief W11 (b)：方式 B = 用户选择"一口气跑完"（执行端当场询问，用户原话见上）')
    L.atomic_write_json(os.path.join(rgn, L.AUTH_PRE), pre)
    cond = dict(record_id='E6L-RECORD-B-CONDITIONS', written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                stage0_all_pass=bool(sm.get('stage0_all_pass')), a1_auto_all_pass=bool(a1.get('all_pass')),
                all_pass=bool(sm.get('stage0_all_pass') and a1.get('all_pass')), frozen_manifest_sha256=man_sha,
                source_manifest_sha256=L.sha_file(L.P('source_manifest.json')), a1_auto_file=a1n, a1_auto_sha256=L.sha_file(os.path.join(rgn, a1n)))
    L.atomic_write_json(os.path.join(rgn, L.AUTH_COND), cond)
    L.write_receipt('prereg_freeze', [os.path.join(rgn, x) for x in (L.MANIFEST_P, L.MANIFEST_B, L.AUTH_PRE, L.AUTH_COND)], 'SUCCEEDED',
                    frozen_manifest_sha256=man_sha)
    print('冻结：P %d / B %d；B 清单 sha %s；条件 all_pass=%s' % (nP, 34120 - nP, man_sha[:16], cond['all_pass']), flush=True)
    return 0


def main():
    if '--stage-b' in sys.argv:
        return stage_b(sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else '')
    if '--freeze' in sys.argv:
        return freeze()
    raise SystemExit('用法：--stage-b | --freeze')


if __name__ == '__main__':
    sys.exit(main())
