# -*- coding: utf-8 -*-
"""E6p A1 冻结（brief §3；附录 B.3 / B.4 / B.21）：授权行五值 → permissions；政策 profile（LEGACY_E6O_A5 逐字段携带 + E6P_CURVE_RESEARCH）；
G 账本（G-P-01…11）、E 账本（E01…E10 + 卡 Q 的问题 / 复现 / 工程行）、卡 Q01–Q18、proposal 原句携带表 CC-E6p-01…11（附录 E 逐字）、F7 数字表、park 表；
冻结件 registration/freeze_E6p.json（合同 / spec / D 脚本 / SCHEMA 合同 / 政策 / 源函数 sha、授权行、缓存命名空间、注册件 sha）。
之后经济规则变动都是 amendment。用法：python3 e6p_a1.py"""
import os
import json
import time

import pandas as pd

import e6p_core as O

AUTH_BY = '用户 2026-10-19 消息（"E6p 执行合同（10-19 修订版）转交，开工……授权行按 brief §0.3 五值"）'
AUTH_AT = '2026-10-19（用户转交；47 时间 2026-10-20 09:05 开工）'
AUTH = dict(research_long_H_authorized=True, aggregate_deploy_authorized=True, recycle_arms_authorized=True, target_A_cny=None,
            target_A_status='UNDECIDABLE_TARGET_A', mainline='状态相依持有期（proposal §1.3 #15；plan §0.1）')

CARDS = [
    ('Q01', '', '源与会计（工程/复现）', 'F1精确源绑定、新旧父读数不一', '同ID源复现，零触发新账户=同backend父；列全会计桥', '不同对象不是四舍五入；错配先修仪器，不能记经济miss', 'replication'),
    ('Q02', 'E01', '选择性长期持有（E01）', 'F1 H20/T1a同H正且低换手', 'H20/HG10/D80/T1a对同H/D80无退出父FULL net差>0', '新部署会改变风险集、年龄与费用；负值限定该预算与H，不否定旧NATIVE结果', 'prediction'),
    ('Q03', 'E02', '日水平长期持有（E02）', 'F1 LEVEL H20强但40%随机短配', 'H20/HG10/D80/LEVEL对同H/D80无退出父FULL net差>0', '旧优势可能主要来自资金再用或特征层；结合联合金额控制，不能靠短配真值位次下结论', 'prediction'),
    ('Q04', 'E03', 'H与退出互补（E03）', 'F1有/无退出曲线形状相反', 'D80/HG10下，T1a与LEVEL的H20−H5退出边际之差，二者等权平均>0', '父随H变弱并不代表子改善；并报H20子−H5子及H5父，禁止只用较弱参照', 'prediction'),
    ('Q05', '', '直接推进H5（开放）', '正确主目标是完整升级', '同H父、H5同部署父、H5当前NATIVE父、H5同触发四差全部报告', '只赢同H父而输H5子，继续保留结果但不称升级', 'question'),
    ('Q06', 'E04', '低换手代价（E04）', 'F1 T1a与LEVEL随A排序变化', 'H20/HG10/D80、A5亿κ.5δ.5，T1a−LEVEL的成本后差大于二者未加冲击的差', '两条订单/流动性结构可能反转；失败改成本动机，不直接停较强net成员', 'prediction'),
    ('Q07', 'E05', '联合触发（E05）', 'T3b与T1a有不同信息来源', '在H20/HG10/NATIVE的共同风险快照，T3b-only触发的下一VWAP后5日超额低于同金额/年龄/行业size非触发匹配组', '非触发组不可比、成交时机改变；联合账户对单项仍开放，不由事件差强推UNION≥max', 'prediction'),
    ('Q08', 'E06', '陈旧持有（E06，新）', '未触坏不等于原自然门仍认可；H5旧证据弱', 'H40/HG10/D80/LEVEL＋RENEW5对无RENEW5同对象FULL net差>0', '最容易miss处是自然门短期噪声及额外交易；对照renew-only/随机检查点/成本，允许无新增方向', 'prediction'),
    ('Q09', 'E07', '涨停退出（E07，新）', 'W5/W6＋F6事件型注意力；角色未测', 'H20/HG10/D80/T8对同H/D80父FULL net差>0', '次日延续、队列及T+1时钟可能使次日VWAP退出错失收益；分制度/板型但不后选有利子规则', 'prediction'),
    ('Q10', 'E08', '同层同金额信息（E08）', 'COUNT_ISK与AMOUNT不等价', 'H20/HG10/D80的T1a、LEVEL真实−AMOUNT_ISK_V2 FULL差的等权平均>0', '未匹配及层宽使对照不公；用局部共同预算说明、不能更换机制挑显著', 'prediction'),
    ('Q11', '', '存活剖面（开放）', 'F2 S0-4要识别长期漂移', 'landmark无未来分组；10–20日区间的当前状态条件收益、资本贡献及风险暴露', '未来一直存活组正不作为支持；仅已知状态条件也不证明因果', 'question'),
    ('Q12', '', '部署（开放）', '平均43%现金是线索', 'D80/D95对NATIVE、容量/风险定义桥、MIRROR误差、H×部署×退出', '不能将比例换算当上界；达到目标并不保证净改善', 'question'),
    ('Q13', '', 'UNION/LEVEL与简化（开放）', '参数简化有维护价值', '同剂量H/资本/规模逐对差；点差±.3仅实用显示带，CI并列', '点近不能证等价；不因“0参数”自动选T1a，也不因为LEVEL_WORST近就宣布纯信息已分离', 'question'),
    ('Q14', '', '成本与容量（开放）', 'c5是旧主要瓶颈', '每种父/绝对组合的曲线、上下交叉、场景反馈84路径', '相对D_imp正≠绝对赚钱；同κ改δ尺度必须对齐', 'question'),
    ('Q15', '', '长期与时代（开放）', '多年暴露、长H连续持仓', '年度/四段/H/可成交/截尾/连续股票年龄、依政策字段解释', '单年度反号不自动关闭；不把后段重复历史再称OOS', 'question'),
    ('Q16', '', '循环与外部性（记录/工程）', '用户两账本与跨轮保护', '完整G→E→反思→派生图、park恢复、原父永留、日序列/源合同可取', '不能用工程PASS提高经济命中率；没有新方向明确保留NO_NEW_DIRECTION_YET', 'engineering'),
    ('Q17', 'E09', '有限再投（E09，v1.1新）', 'F7：NATIVE多得净收益也多付模型冲击；CASH端点有用', 'H5/HG10/LEVEL，RECYCLE_HALF−NATIVE，固定路径A5亿/κ.5/δ.5的FULL净差>0', '半释放可能削掉高收益再投资而未降低关键订单；与CASH/NATIVE完整差、同资本与日级费用分解，负值限定该资金时钟与规模', 'prediction'),
    ('Q18', 'E10', '净成本路由（E10，v1.1新）', 'F7：利用待执行净单与流动性，避免假定已持有即便宜', 'H20/HG10/LEVEL，RECYCLE_COSTNET−NATIVE，固定路径A1亿/κ.5/δ.5的FULL净差>0', '低成本路由可能集中/买入边际质量较差者；COST0及同快照native、固定预算/支持/风险、反馈账户并列，不将优化器成本下降当经济HIT', 'prediction'),
]

GP = [
    ('G-P-01', 'H20子账户无日序列，无法做完整β/同敞口分析', '所有经济账户、镜像、确定性控制、随机配对均导出日级状态/PnL及可重放订单；H5/20旧表重新绑定确切父', '最大效应不能因被叫“读法”而丢失底层证据'),
    ('G-P-02', '所有可见政策项为1仍不可判', '导出每项值、计算域、来源、NA原因、依赖ID；无枚举外原因；旧表不追判PASS', '技术缺项、H域限制、目标A未定与经济失败分开'),
    ('G-P-03', '“单位敞口净值”只提供粗读', '真正独立D80/D95＋有滞后且可行的MIRROR；不称比例差为上下界', '对照本身携带的信息、交易路径和风险约束同样要建模'),
    ('G-P-04', 'H20随机40%金额短配', '预定两级金额匹配、同金额ISK、局部对称预算诊断；短配及跨层回填全部报告', '匹配改善不是把父未来股票拿来补集，也不是强行凑100%'),
    ('G-P-05', 'T1a与LEVEL随规模相对优势翻转', '所有直接比较各自成本曲线与交叉点，目标A保留待定', '“过政策”与“存在可研究的资本规模”不同'),
    ('G-P-06', '原CC-09细粒度必更强不支持', '这是E6o的第二道原预测；其失败启发E6p不提名分钟触发，记E→G派生而非又算一次G实测失败', '同一失败按来源只计一次，派生设计仍可创造新价值'),
    ('G-P-07', '敞口/H/β/三个记忆的汇总关系', '核源权重与自融资状态、每日暴露协变、存活/新买/内部转移分解', '平均敞口相同不证明资本渠道为零；β匹配不是纯期限识别'),
    ('G-P-08', '成本后CASH接近零', '费用增量与净收益不能混读→三臂再投', 'CASH 的净增量约 −.02 不是卖出冲击成本约 0；卖与再投分开研究'),
    ('G-P-09', '水平≥EDGE', '保留简单水平对照→不重复提名已测尾盘', '已被 F1 明确支持的 E02 仍记支持，不因启发新思路再算一次 miss'),
    ('G-P-10', '层内增量可能增加', '同金额分层及PIT密度诊断→将来研究角色映射', '格子层与格内信息分开；不默认某类应剔除'),
    ('G-P-11', '总体“无实质改进”过强', '分开预测、账户增量、实施与政策、覆盖四层', 'E6o 已获得账户级正向增量与可迁移的研究资产；部分方向未改善相应基准'),
]

CC = [
    ('CC-E6p-01', '§3.4 C-A′ 预测', '相对**同 H FIXED 父**：D 随 H 增（H5 → H20），H30 / H40 继续增或平', '可比：VS_SAME_H_PARENT 在 H5…H40（NATIVE 对应 proposal 的 FIXED）', 'yes'),
    ('CC-E6p-01L', '附录 A（从业者口径，文献来源的方向句）', 'H40 ≤ H20 或平', '与 CC-E6p-01 方向不同：两句都携带，分别评，不在执行后选中一句（附录 E 末段）', 'yes'),
    ('CC-E6p-02', '§3.4', '相对 **DEPLOY_MATCH 父**：D > 0 但小于相对 FIXED 父的 D（部署份额 > 0）', '对象已改：DEPLOY_MATCH 父在 plan 中降为 MIRROR 诊断；按 OWNER_VS_EXPOSURE_FOLLOWER 评分并注明对象差（NOT_TESTED_AS_WRITTEN 亦可）', 'partial'),
    ('CC-E6p-03', '§3.4', '相对 **LEVEL_WORST**：T1a / LEVEL 版 ≈ 对照（信息 = 水平）；换手随 H 单调降；冲击曲线盈亏平衡 A* 随 H 增；**可证伪点**：若相对 DEPLOY_MATCH 父 ≤ 0，长 H 的增量就只是部署，退出线不固化、部署线升级',
     '前三句可比（LEVEL_WORST_1D、turnover_ann、breakeven）；可证伪点随 CC-E6p-02 对象差评', 'partial'),
    ('CC-E6p-04', '§5.2 H 网格读法', '预测 D_M 随 H 增后变平；若 H40 < H20 → 上限在 20–30', '可比（HORIZON_WITHIN_TRIGGER）；"上限在 20–30"是读法不是预测，不评分', 'yes'),
    ('CC-E6p-05', '§4.1 读法列 1', '预测 k = 1 ≥ 3 ≥ 5 的触发账户 D（信息衰减快）；只分列读、不选 k', '本轮 cvr_k 只作 D7 测量列、无触发账户 → NOT_TESTED_AS_WRITTEN；D7 只报秩相关与重叠', 'no'),
    ('CC-E6p-06', '§4.2 部署规则族', 'DEPLOY_95 父相对 FIXED 父 D > 0 且 ≈ 单位敞口净值 × 敞口差（线性假设）；D3 下在用户目标规模内仍正；DEPLOY_95 + 退出 相对 DEPLOY_95 父 的 D 与 FIXED + 退出 相对 FIXED 父 的 D 同号、量级相近（信息不依赖部署）',
     '对象改为 D95（独立目标账户，非敞口匹配）：前半句按 DEPLOY_OPERATOR_CHANGE（D95 父 − NATIVE 父）评；"≈ 单位敞口净值 × 敞口差"是 plan §2.2 明确否定的线性换算，记 REPLACED_BEFORE_RUN；后半句按 DEPLOY_X_EXIT 复合评（同号 + 量级）', 'partial'),
    ('CC-E6p-07', '§4.1 T1b_LEVEL 行', '毛 D 最高；D3 下在小规模（≤ 2 亿）优于 T1a、大规模劣于 T1a；相对 LEVEL_WORST ≈ 0', '可比：主展示 FULL D 排序、成本曲线 `T1A_VS_LEVEL` 交叉点（breakeven）、`LEVEL_WORST_1D` 对照', 'yes'),
    ('CC-E6p-08', '§4.1 T3b15 行', 'D > 0（H5 已 1.42）；随 H 增', '可比：VS_SAME_H_PARENT（H5 … H40）与 HORIZON_WITHIN_TRIGGER', 'yes'),
    ('CC-E6p-09', '§4.1 UNION 行', 'D(UNION) ≥ max(T1a, T3b15) 且换手 ≤ 两者之和；若 D < max → 两者信息重叠', '可比：UNION_COMPONENT、UNION_NONADDITIVITY、`turnover_ann`；plan §2.4 不预设 ≥ max，原句照评，"信息重叠"只是读法', 'yes'),
    ('CC-E6p-10', '§4.1 T8 行', '先数事件（S0-5）；D ≥ 0 两域登记：若赢家日携带延续信息，门内方向可能反号', '可比：VS_SAME_H_PARENT；事件不足 → NO_ACTION_OPPORTUNITY / 未覆盖，不按零效应判', 'yes'),
    ('CC-E6p-11', '§4.2 FIXED 行（结构断言）', '敞口 = 日均 ΣW，与 H 无关（S0-0 验证）', '可比：恒等行 `SOURCE_EXPOSURE_EQ_MEAN_SUMW`（P_SOURCE；INFO）与 P_SOURCE / NATIVE 父三个 H 的 `exposure_mean`；plan §1.2(8) 的反对意见一并携带', 'yes'),
]

F7 = [
    ('F7-01', 'LEVEL CASH +.12（水平 CASH）', 'H5 LEVEL × CASH 的 D（来源 query 未取得）', '.12', 'USER_RELAYED_UNVERIFIED_QUERY'),
    ('F7-02', '按单位资本 1.7–1.9', '主对象同资本 / 单位资本口径 D（D_sc 1.73–1.88；来源 query 未取得）', '1.7–1.9', 'USER_RELAYED_UNVERIFIED_QUERY'),
    ('F7-03', '近段格内 1.19', '2024–26 段 real − COUNT_ISK（格内）', '1.19', 'USER_RELAYED_UNVERIFIED_QUERY'),
    ('F7-04', '全程 .79、2019–23 .73', 'real − COUNT_ISK 全程与 2019–23 段', '.79 / .73', 'USER_RELAYED_UNVERIFIED_QUERY'),
    ('F7-05', '2.4% ADV', '参与率读数（D3）', '2.4%', 'USER_RELAYED_UNVERIFIED_QUERY'),
    ('F7-06', 'NATIVE 净 D 1.980', 'H5 主对象 FULL D（同引擎无退出父）', '1.980', 'SOURCE_REVIEW_MATCHED'),
    ('F7-07', 'CASH 净 D .869', 'H5 主对象 CASH 变体 FULL D', '.869', 'SOURCE_REVIEW_MATCHED'),
    ('F7-08', '冲击后 D −1.111', 'H5 主对象 5 亿 κ .5 冲击后 D', '−1.111', 'SOURCE_REVIEW_MATCHED'),
    ('F7-09', 'CASH 冲击后约 −.02', 'H5 主对象 CASH 变体冲击后 D', '约 −.02', 'SOURCE_REVIEW_MATCHED'),
]

PARK = [
    ('P63', '分钟尾盘退出触发 T4b / T5（E6o：D .02 / .18；公共窗口 .03 / .24 vs T1b 2.12）', 'L2 成交方向或日内更早时点的测量；T4a 不 park（carried 弱）', 'PARKED'),
    ('P64', '放量下跌退出 T3a（含 X1 / XR / 量比 2.0）（D .01 ~ .29）', '信息型卖出代理（大单净卖 / 撤单）或行业条件重定义；T3b 不 park', 'PARKED'),
    ('P65', '相对变化触发 T2 / T2′ / OWNCHANGE（.44 / −.02 / .15）', '不同基线（入场后最高 CVR）或长窗', 'PARKED'),
    ('P66', '价格止损 T6a / T6b（−.38 / −.36；对照臂）', '本轮不提名；未来需新角色 / 新风险状态 / 新实施合同另行登记（plan §14：不预先承诺复活）', 'PARKED'),
    ('P67', '行业豁免 X1_RANK / XR（账户层 ≈ 0 ~ −.05）', '行业 × size 层级退出研究（COUNT_ISK 线索）', 'PARKED'),
    ('P68', '重入 BLOCK / RECONFIRM（−.52 / −.14 对 ALLOW）', '冲击约束下重入换手成为瓶颈；本轮不重开', 'PARKED'),
    ('P69', '资金去向 CASH / ORIGINAL_DUE（−1.02 / −.71 对 NATIVE RESET_H）', '再投资冲击主导时作低换手形态——本轮按已满足的恢复条件有限重开 CASH_REMAIN 九行（plan §6.4）', 'REOPENED_BOUNDED_E6P'),
    ('P70', '持仓自身分位高换手版 T1c（2.13 但换手 30.8、冲击 −5.3）', '冲击校准后或 H20 口径；本轮不提名', 'PARKED'),
]


def appendix_b_sha():
    t = open(O.P('inputs', 'E6p_brief_appendix_schema_probes.md'), encoding='utf-8').read().replace('\r\n', '\n')
    a = t.index('## B. SCHEMA')
    b = t.index('## C. ')
    return O.sha_bytes(t[a:b].encode('utf-8'))


def policy_profile():
    src = O.E6O('registration', 'policy_profile_E6o.json')
    legacy = json.load(open(src, encoding='utf-8'))
    prof = dict(
        LEGACY_E6O_A5=dict(source_file='E6o registration/policy_profile_E6o.json', source_sha256=O.sha_file(src), fields=legacy['mapping'], verdict_rule=legacy['verdict_rule'],
                           research_status=legacy['research_status'], frozen_cost_stress=legacy['frozen_cost_stress'], delta_main=legacy['delta_main'],
                           domain='E6o 适用域：H ∈ {5, 10, 20}、NATIVE（ENGINE_NATIVE lag1 RESET_H ALLOW）、FEASIBLE / IDEAL；域外（H ∈ {15, 30, 40}、D80 / D95 / CASH_REMAIN / RECYCLE、RENEW5、ABS01）→ 不可判（H_DOMAIN_NOT_IN_LEGACY / MAPPING_UNRESOLVED）',
                           approval_status='APPROVED_E6O'),
        E6P_CURVE_RESEARCH=dict(fields=dict(c1=legacy['mapping']['c1_segment_tolerance_ok'], c2=legacy['mapping']['c2_year_positive_share'], positive=legacy['mapping']['positive'],
                                            c3=legacy['mapping']['c3_full_sc_same_sign'], c4=legacy['mapping']['c4_random_post_ok'] + '（E6p 主匹配机制 = AMOUNT_MATCH_V2；其余机制并排、不替代）',
                                            c5='成本曲线 profile：target_A_cny 未指定 → c5 = NA、undecidable_reason = UNDECIDABLE_TARGET_A；曲线全报（A ∈ {.5, 1, 2, 5, 10} 亿 × κ ∈ {.5, 1} × δ ∈ {.5, .7}），1 亿与 5 亿作显示锚；规模条件不自动 PASS',
                                            c6=legacy['mapping']['c6_declared_ok'], port3t=legacy['mapping']['port3t_ok']),
                                h_domain_authorized='research_long_H_authorized = true → H ∈ {5, 10, 15, 20, 30, 40} 均在研究域（生产口径另定）',
                                verdict_rule='plan 附录 C policy_verdict：任一 false → 不通过；无 false 有 NA → 不可判；全 true → 通过；known_failure 优先记录真实不通过',
                                research_status=legacy['research_status'], approval_status='PROPOSED_E6P', no_new_gates='记录用通过（≥ 3/4 段正、赢两种随机、LEVEL 差 ≥ −.3）不构成新资格门；±.3 只作显示带'),
        undecidable_reasons=['UNDECIDABLE_TARGET_A', 'H_DOMAIN_NOT_IN_LEGACY', 'RANDOM_NOT_COVERED', 'CONTROL_NOT_COMPARABLE', 'SOURCE_BINDING_PENDING', 'PARTIAL_YEAR_ONLY', 'MAPPING_UNRESOLVED'],
        control_not_comparable_rule='FULL unmatched_cny / requested_cny > %.2f' % O.NOT_COMPARABLE_UNMATCHED,
        deployment_authorized=False)
    return prof


def main():
    t0 = time.time()
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    reg = O.P('registration')
    if not os.path.exists(os.path.join(reg, 'registry_E6p.csv')):
        raise RuntimeError('registry 未编译')
    if not os.path.exists(O.P('diagnostics', 'stage0_E6p_part1.csv')):
        raise RuntimeError('Stage 0 未完成')
    perm = [dict(key=k, value=('' if v is None else (str(v).lower() if isinstance(v, bool) else v)), authorized_by=AUTH_BY, authorized_at=AUTH_AT) for k, v in AUTH.items()]
    perm += [dict(key='protocol', value='v1.6', authorized_by=AUTH_BY, authorized_at=AUTH_AT), dict(key='mode', value='B', authorized_by=AUTH_BY, authorized_at=AUTH_AT),
             dict(key='deployment_authorized', value='false', authorized_by='brief §0 / R8（不变）', authorized_at=AUTH_AT),
             dict(key='E7', value='HOLD', authorized_by='brief R8（不变）', authorized_at=AUTH_AT)]
    O.atomic_write_csv(os.path.join(reg, 'permissions_E6p.csv'), pd.DataFrame(perm))
    prof = policy_profile()
    O.atomic_write_json(os.path.join(reg, 'policy_profile_E6p.json'), prof)
    O.atomic_write_csv(os.path.join(reg, 'cards_E6p.csv'), pd.DataFrame([dict(card_id=c[0], e_id=c[1], title=c[2], motivation=c[3], estimand_direction=c[4], strongest_counter_and_update=c[5], kind=c[6])
                                                                      for c in CARDS]))
    G = [dict(g_id=g[0], original_author='F2 E6p proposal v1.0 第一道反思（CC；§2.3 / §3.7）' if int(g[0][-2:]) <= 7 else 'F7（用户转交的执行端"三条折扣"讨论；plan §3.4）',
              verbatim_expectation=g[1], expected_at='AUTHOR_REPORTED/PENDING_ARTIFACT' if int(g[0][-2:]) <= 7 else 'REPORTED_POST_E6O_DISCUSSION',
              measurement_at='' if int(g[0][-2:]) <= 7 else 'MEASUREMENT_NOT_YET_BOUND', observed_result='', source_query='', source_data_hash='',
              probe_window='E6o 交付已曝光四段（第一道 = 已暴露账户再查询，保留 G 地位）' if int(g[0][-2:]) <= 7 else 'E6o 执行后讨论',
              prior_exposure='E6o 全样本已曝光', interpretation=g[2], competing_roots='', root_status='AUTHOR_REPORTED/PENDING_ARTIFACT' if int(g[0][-2:]) <= 7 else 'REPORTED_POST_E6O_DISCUSSION',
              derived_from='plan §3.1' if int(g[0][-2:]) <= 7 else 'plan §3.4', derived_idea=g[3], new_prediction_at=now, nominated_or_parked='NOMINATED_E6P_DESIGN') for g in GP]
    O.atomic_write_csv(os.path.join(reg, 'ledger_G_E6p.csv'), pd.DataFrame(G))
    gmap = {'E01': 'G-P-01;G-P-03', 'E02': 'G-P-01;G-P-04;G-P-09', 'E03': 'G-P-07', 'E04': 'G-P-05', 'E05': 'G-P-06', 'E06': 'G-P-07', 'E07': 'G-P-06', 'E08': 'G-P-04;G-P-10',
            'E09': 'G-P-08', 'E10': 'G-P-08;G-P-11'}
    E_ = []
    for c in CARDS:
        eid = c[1] or c[0]
        E_.append(dict(e_id=eid, g_ids=gmap.get(eid, ''), author='plan v1.1 §12（E01–E08 v1.0 携带；E09 / E10 v1.1 新）' if c[1] else 'plan v1.1 §12 卡', exact_statement=c[4],
                       object_id='', comparator_id='', support_id=O.SUPPORT, unit='ann_pp', outcome_window='FULL（2010-01-04 … 2026-03-27，连续全历史）+ 四段 + G4',
                       prior_exposure='同一历史已曝光；首次新算子运行仍非 OOS（plan §13.1）', kind=c[6],
                       statistic_and_interval_function='FULL D = Σ n_s D_s / Σ n_s；区间 = stationary bootstrap 2,000 次（块 40；同函数、同样本）', query_id='QRY-%s' % eid,
                       result='', direction='+' if c[6] == 'prediction' else '', precision='', heterogeneity='', mechanism_status='', next_action=''))
    O.atomic_write_csv(os.path.join(reg, 'ledger_E_E6p.csv'), pd.DataFrame(E_))
    O.atomic_write_csv(os.path.join(reg, 'cc_statement_carry.csv'), pd.DataFrame([dict(carry_id=c[0], source_doc='E6p_proposal.md v1.0（2652d4c891c803fa）', source_section=c[1],
                                                                                    verbatim_statement=c[2], estimand_note=c[3], comparable=c[4], claim_status='开放') for c in CC]))
    O.atomic_write_csv(os.path.join(reg, 'reported_claims_E6p.csv'), pd.DataFrame([dict(claim_id=f[0], relayed_text_verbatim=f[1], quantity=f[2], value_as_relayed=f[3], binding_status=f[4],
                                                                                       query_id='QRY-%s' % f[0]) for f in F7]))
    O.atomic_write_csv(os.path.join(reg, 'park_E6p.csv'), pd.DataFrame([dict(park_id=p[0], domain=p[1], condition=p[2], status=p[3]) for p in PARK]))
    sh = json.load(open(O.P('diagnostics', 'source_fn_sha256_E6p.json')))
    files = ['registry_E6p.csv', 'comparisons_E6p.csv', 'compound_contrasts_E6p.csv', 'random_control_refs_E6p.csv', 'cost_feedback_refs_E6p.csv', 'recycle_diagnostic_refs_E6p.csv',
             'exposure_E6p.csv', 'sources_E6p.csv', 'permissions_E6p.csv', 'policy_profile_E6p.json', 'cards_E6p.csv', 'ledger_G_E6p.csv', 'ledger_E_E6p.csv', 'cc_statement_carry.csv',
             'reported_claims_E6p.csv', 'park_E6p.csv']
    fz = dict(plan_sha256=O.PLAN_SHA256, spec_sha256=O.SPEC_SHA256, brief_sha256=O.BRIEF_SHA256, appendix_sha256=O.APPENDIX_SHA256, d_script_sha256=O.D_SCRIPT_SHA256,
              schema_contract_sha256=appendix_b_sha(), policy_file_sha256=O.sha_file(os.path.join(reg, 'policy_profile_E6p.json')),
              source_fn_sha256={k: sh[k] for k in ('engine', 'b2_trigger', 'veto_t1a', 'volume_baseline', 'limit_fields', 'natural_gate', 'deploy_eligible_set', 'deploy_prior_weight',
                                                   'relative_benchmark', 'fee', 'vwap', 'cost_adv', 'cost_sigma')},
              data_cutoff=O.CUTOFF, protocol='v1.6', mode='B', authorizations=AUTH, authorized_by=AUTH_BY, authorized_at=AUTH_AT, written_at=now, cache_tag=O.CACHE_TAG,
              cache_dir=os.path.basename(O.cache_dir()), deployment_authorized=False, e7='HOLD', support=O.SUPPORT, start_state_main='CASH_V0', start_state_sensitivity='WARM（主对象对与其父的四段重置；不进 registry）',
              segment_init_deviation='连续全历史为主、四段重置作敏感性（brief §0.1 #18，用户 10-19 裁定；对 plan §4.4 的有意偏离）',
              random_budget=dict(base_paths=128, main_owner_target_mcse=0.01, max_paths=1024, batch=128, ideal_scope='18 主对象 owner × AMOUNT_MATCH_V2 × 128', seed='stable_u64(E6p, owner 逻辑 ID, 机制, 路径序号)'),
              control_not_comparable_rule=prof['control_not_comparable_rule'], parameters=dict(renew_step=5, eta=O.ETA_HALF, route_A_ref=O.ROUTE_A_REF, route_kappa=O.ROUTE_KAPPA,
                                                                                               route_delta=O.ROUTE_DELTA, p0=O.P0_PIVOT, fee_rate=O.FEE_RATE, deploy_targets=O.TARGETS),
              registration_sha256={f: O.sha_file(os.path.join(reg, f)) for f in files}, spec_json_sha256={f: O.sha_file(os.path.join(reg, 'spec', f)) for f in sorted(os.listdir(os.path.join(reg, 'spec')))},
              stage0_sha256=O.sha_file(O.P('diagnostics', 'stage0_E6p_part1.csv')), code_sha256={f: O.sha_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), f))
                                                                                                  for f in sorted(os.listdir(os.path.dirname(os.path.abspath(__file__)))) if f.startswith('e6p_') and f.endswith('.py')})
    p = os.path.join(reg, 'freeze_E6p.json')
    if os.path.exists(p):
        raise RuntimeError('freeze_E6p.json 已存在：A1 只冻结一次（变动走 amendment）')
    O.atomic_write_json(p, fz)
    O.write_receipt('E6p_A1_freeze', [p] + [os.path.join(reg, f) for f in files], code=[__file__], wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(written_at=now, files=len(files), schema_contract_sha256=fz['schema_contract_sha256'][:16]), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
