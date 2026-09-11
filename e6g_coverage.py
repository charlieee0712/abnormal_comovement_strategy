#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g coverage: 逐条映射 proposal / web plan / brief -> 状态 + 证据文件 + 理由。
状态 ∈ {done, reused, changed, deferred, unavailable}。改或没做必须写理由与影响。
每条的 `evidence` 会现场核实文件是否存在, 存在才算 done —— 防止假"完成"标记。
"""
import os, sys, glob, json
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6g_core as G

R = G.RES
ITEMS = [
    # (brief 节, 条目, 状态, 证据 glob, 理由/影响)
    ('§2', '读 PROJECT_STATUS / 协议 / memory / E6f 全套前置', 'done', 'brief_copy.md', ''),
    ('§2', '冻结四地基 + 七 e6e + 十九 e6f 的 SHA 与运行库版本', 'done', 'source_manifest.json', ''),
    ('§2', 'registry/: U34/U35/NEW40 逐键 ~15 字段', 'done', 'registry/key_registry.csv', ''),
    ('§2', 'registry/: 剩余 8 键索引', 'changed', 'source_corrections_E6g.md',
     '实测日频键是干净的 30⊎40 划分, 无余项; proposal 所指来源是外部 99 篇研报库, 另一个宇宙。按 plan §2K1「不另发明清单」只索引来源'),
    ('§2', '涨跌停计数列 (逐段逐年)', 'done', 'H0/limit_hits_*.csv', ''),
    ('§2', '去重元数据 descriptor -> path 映射', 'done', 'registry/descriptor_path_map.csv', ''),
    ('§2', '方向统一 bad_pct + 反向真实反序 + 两个方向都报', 'done', 'checks/selftests_*.json', ''),
    ('§2', '固定展示组 R1/R2/A03-A10/T25/Blend3', 'done', 'H0/summary_H0_*.csv', ''),
    ('§2', '40 键守卫 DAG + 四条攻击测试', 'done', 'checks/guard_attack_tests.json', ''),
    ('§2', '锚: E6f 63 源锚 / E6e 逐日 / interior_nopos / 76=4x19', 'done', 'checks/selftests_*.json', ''),
    ('§2', '锚: E3 6bp -> 8bp 对账', 'deferred', '',
     '未单独复现 E3 单因子表; T0 与 K2 都直接用 compute_forward_5d_excess 源函数, 成本口径不进标签。影响: E3 表的 6->8bp 转换未独立验证'),
    ('§1.1', 'E6f 段内零仓位勘误写进 revisions/', 'done', 'revisions/E6f_interior_nopos/README.md', ''),
    ('§14', 'revisions/ 计数分母 (12.5%/41.7% 的分母是 264 不是 352)', 'done',
     'revisions/E6f_count_denominator/README.md', ''),
    ('§14', 'revisions/ R2 身份 (E6b 样本内研究参照, 非 v2 交付)', 'done',
     'revisions/E6f_R2_identity/README.md', ''),
    ('§14', 'revisions/ Blend 估算撤回 (换成真实账户值)', 'done',
     'revisions/E6f_blend_estimate_withdrawn/README.md',
     '全窗口 net8 7.230 / net12 6.357 / 换手x252 21.40; proposal 的账本平均估 7.2/6.3/22 差 <=0.06 点, '
     '方向全对但仍作废换成账户值。新结论: 混合增益全部来自换手对冲 (gross 恒等于成员平均)'),
    ('§14', 'revisions/ 数据 / 位级差', 'done', 'revisions/E6f_bitlevel_and_data/README.md',
     '四项位级对锚全过, 无需撤回的位级问题; 真实存在的位级差已登记为仪器事实 I1/I2/I6'),
    ('§14', 'revisions/ E6f flag 列错位 (本轮新查出, 不在 brief 原列表)', 'done',
     'revisions/E6f_flag_alignment/README.md', ''),
    ('§14', 'revisions/ 索引', 'done', 'revisions/README.md', ''),
    ('§1.4', 'preregistration.md 落盘于首次新收益评价之前', 'done', 'preregistration.md', ''),
    ('§3', '三个具名 selector + 逐开关账', 'done', 'H0/selector_switch_*.csv', ''),
    ('§3', '平局 WHOLE_TIE / RANDOM_TIE 64 seed', 'done', 'H0/tie_runs_*.csv', ''),
    ('§3', 'NEW40 输入变换 RAW vs pool_rank 并排', 'done', 'H0/new40_input_variant_*.csv', ''),
    ('§3', '复权三分类 (逐式)', 'changed', 'registry/key_registry.csv',
     '改为两个独立标志 (price_adj_measured_change / volume_dependent_untested) + 并列驱动标志; 互斥三分类会把「实测会变」与「未测」混同'),
    ('§4', 'T0-35 输家解剖 (画像/覆盖/剩余损失/伪路径)', 'done', 'T0_35/T0_profiles_U35_*.csv', ''),
    ('§4', 'T0 主标签用 E3 源版 + 端点复利版另报', 'done', 'T0_35/T0_counts_U35_*.json', ''),
    ('§4', 'T0-74', 'done', 'T0_74_discovery/T0_profiles_U74_*.csv', ''),
    ('§4', 'T0 聚类 (层次 / k-means / 深度<=3 树)', 'deferred', '',
     '画像/覆盖/剩余损失/伪路径已出; 聚类与树未做。影响: Q1 的「模式」分层用的是逐键 pct 偏移而不是聚类标签'),
    ('§5', 'H1 第四腿/换腿 1,544 格', 'done', 'H1/summary_H1_*.csv', ''),
    ('§5', 'H2 时序变换 (两支持集)', 'done', 'H2/summary_H2_*.csv', ''),
    ('§5', 'H3 条件否决 + 三对照 + 256 随机路径', 'done', 'H3/H3_random_*.csv', ''),
    ('§5', 'H4-a 1,100 + H4-b 600', 'done', 'H4/summary_H4a_*.csv', ''),
    ('§5', 'H5 四腿聚合', 'done', 'H5/summary_H5_*.csv', ''),
    ('§5', 'B2 alpha 五点 + J 的 MA3/MA5', 'done', 'B2/summary_B2_*.csv', ''),
    ('§5', '新选入/被替出集合的形成日 fwd 剖面', 'deferred', '',
     '日账本已存可事后算; 本轮未出表。影响: Q3 只有净效应没有分解到「换进来的票表现如何」'),
    ('§6', 'L1 续选缓冲 (b 四点 + relative1.5, 两预算)', 'done', 'L/L_*.csv', ''),
    ('§6', 'L2 持有期 H 八点', 'done', 'L/L_*.csv', ''),
    ('§6', 'L1-2 低频刷新参照', 'done', 'L/L_*.csv', ''),
    ('§6', 'L-X 提前退出小块', 'deferred', '',
     '需影子账户改造 + 恒等式检验 (b0+不提前退出 = 同影子模型的源 H5)。brief §6 允许该小块 LIMIT。影响: Q8 缺「提前退出」这一支'),
    ('§6', 'L1-3 Blend3 成员级缓冲', 'done', 'L/L_*.csv', ''),
    ('§6', 'actual_incumbent 对照', 'deferred', '',
     '需从源账户取执行时钟。影响: 缺「昨天被选 vs 今天真实仍持有」的差'),
    ('§7', 'K1 40 键访问史七标签', 'done', 'registry/key_registry.csv', ''),
    ('§7', 'K2 单因子 + 叠父否决 + 三对照 + I-IID', 'done', 'K_discovery/K2_2*.csv', ''),
    ('§7', 'K2 随机路径 128+128', 'changed', 'K_discovery/K2_random_*.csv',
     '主切片 (k=5 x A06 x RAW, 80 格) 跑满 128+128; 其余 960 个否决格给 I-IID 解析期望 + 同人数 core + 同人数反向三个确定性对照。理由: 全上 256 条单段约 13.6 小时。影响: 非主切片没有随机参照的 MCSE'),
    ('§7', 'K3 park 相关小块', 'changed', 'K_discovery/K2_2*.csv',
     'K2 已覆盖全部 40 键 x 双方向 x k x 三母体, K3 点名的键 (CMF/volume_ratio/amihud/turnover_5d 等) 都在其中; 未另起 K3 的专门分组表。影响: park 台账要自己从 K2 表里取对应键'),
    ('§7', 'K4 E6h 登记草稿', 'done', 'E6h_registration_draft.md', ''),
    ('§8', 'B1 扩展域 + S1/S3/S4 + S1-cost', 'done', 'B/B1_selection_EXPANDED.csv', ''),
    ('§8', 'B1 真实政策账户 (重走批次)', 'done', 'B/B1_policy_accounts_EXPANDED.csv', ''),
    ('§8', 'B1 可分辨度 spread_to_pairSE', 'done', 'B/B1_discernibility_EXPANDED.csv', ''),
    ('§8', 'B1 反向切割迁移诊断', 'deferred', '',
     '未做。影响: 缺「训练窗在评估窗之后」的迁移对照'),
    ('§9', '三层账 G / N8 / N12 / NI 与逐日恒等', 'done', 'C/impact_scenarios.csv', ''),
    ('§9', '冲击 A x kappa 九格 x 两模型', 'done', 'C/impact_scenarios.csv', ''),
    ('§9', '影子账户 ideal/X0/X1 + Xengine 锚', 'done', 'C/shadow_*.csv', ''),
    ('§9', '容量 A* 与优势交点 A_delta* 求根', 'deferred', '',
     '情景表已全出 (A x kappa x 两模型), 未做求根。影响: 没有单一「容量数字」, 只有网格'),
    ('§9', 'Blend 与随机路径的非线性 / I-IID 解析期望', 'done', 'K_discovery/K2_2*.csv', ''),
    ('§10', 'HAC lag 5 + bootstrap 2000 stationary 块长 20', 'done', 'D/paired_vs_refs.csv', ''),
    ('§10', '共 draw max-|t| 同时带', 'done', 'D/family_bands.csv', ''),
    ('§10', 'Romano-Wolf stepdown 附列', 'deferred', '',
     '同时带已用共 draw max-|t| 主口径; RW 附列未做。影响: 缺一个更保守的逐步调整 p 值'),
    ('§10', '全窗口拼接 / 去 15+16 / 最近段 / 逐年', 'done', 'D/fullwindow_vs_refs.csv', ''),
    ('§10', '四种计数 (描述符/公式/真实路径/有效比较数)', 'done', 'D/family_counts.csv', ''),
    ('§12', '自测与锚 43/43 x 4 段', 'done', 'checks/selftests_*.json', ''),
    ('§12', 'plan §3.2 八组最小测试矩阵', 'changed', 'checks/selftests_*.json',
     '按功能等价接到真实 builder 与引擎 (时间/权限、因子/单位、分箱、DEV、结构、路径、会计、统计), 未按 plan 的八组编号逐组列表。影响: 对照 plan 时要自己映射'),
    ('§13', '计时试点 (最长段 + 最短段)', 'done', 'H0/pilot_*.json', ''),
    ('§13', '并发 <=32 / BLAS 单线程 / 绑 socket 1 / 父进程验收', 'done', 'task_status/', ''),
    ('§14', 'REPORT part1 / part2 / part3', 'done', 'REPORT_part1.md', ''),
    ('§14', 'line_state_proposal / park_ledger_delta 草稿', 'done', 'line_state_proposal.md', ''),
    ('§14', 'limit_register / source_corrections_E6g', 'done', 'limit_register.md', ''),
]


def main():
    rows = []
    for sec, item, st, ev, why in ITEMS:
        hit = sorted(glob.glob(os.path.join(R, ev))) if ev else []
        ok = bool(hit)
        # 防假 done: 声称 done 但证据文件不在, 降级
        final = st
        note = why
        if st in ('done', 'reused') and ev and not ok:
            final = 'unavailable'
            note = (why + ' | ' if why else '') + '声称 %s 但证据文件不存在: %s' % (st, ev)
        rows.append(dict(brief_section=sec, item=item, status=final,
                         evidence=ev, n_evidence_files=len(hit), reason_or_impact=note))
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(R, 'coverage.csv'), index=False)
    print(d.status.value_counts().to_string())
    print()
    bad = d[d.status.isin(['unavailable'])]
    if len(bad):
        print('!! 证据缺失:')
        print(bad[['brief_section', 'item', 'evidence']].to_string(index=False))
    print()
    print('deferred / changed 明细:')
    print(d[d.status.isin(['deferred', 'changed'])][['brief_section', 'item', 'status']]
          .to_string(index=False))


if __name__ == '__main__':
    main()
