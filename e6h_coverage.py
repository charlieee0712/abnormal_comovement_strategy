#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h coverage: 逐条映射 proposal / plan / brief -> 状态 + 证据 + 理由。
状态 ∈ {done, reused, changed, deferred, unavailable, blocked_by_gate}。
每条的 evidence 会【现场核实文件是否存在】, 存在才算 done —— 防假完成标记 (E6g 做法)。
"""
from __future__ import annotations
import os
import sys
import glob

import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H

R = H.RES
ITEMS = [
    # ---------------- §2 阶段 0 ----------------
    ('§2', '读前置 + 冻结四地基/e6e/e6f/e6g SHA + 运行库版本 + HEAD/dirty/untracked',
     'done', 'source_manifest.json', ''),
    ('§2', 'feature_semantics.csv (含 source_sign / economic_direction / value_used_for_pct)',
     'done', 'registry/feature_semantics.csv', ''),
    ('§2', 'feature_taxonomy.csv 第一层测量目录, 多标签, 按源公式定',
     'done', 'registry/feature_taxonomy.csv', ''),
    ('§2', '固定展示组从 E6g 注册表导入, 不自行拼默认参数', 'done',
     'checks/anchors_2010-2014.json', '11 个源锚重建 vs E6g 已存 summary 逐位 (~1e-16)'),
    ('§2', '新算子恒等锚 (阻断): SLOT/FOCAL/ADD/SWAP/CONJ/MARGIN/软降权', 'done',
     'checks/rule_anchors_2010-2014.json', '48/48'),
    ('§2', '守卫扩展 + 攻击测试 (含重命名规则对象/已知键条件化/派生键进 2019+)',
     'done', 'checks/guard_attack_tests.json', '13 条攻击全拒 + 7 条合法路径全放行'),
    ('§2', '并发: 先实测每 worker 线程与内存再定 worker 数', 'done',
     'runtime/concurrency_pilot.json', '实测 200 线程 / 3.3GB per worker, 复现 E6g I7'),
    # ---------------- §3 R0 ----------------
    ('§3', '母体复原 U/C/V/B/D + DEP 分关 + 原因码', 'done',
     'T0_full_distribution/stage_daily_2010-2014.csv',
     '按 plan §4.1 补了 DEP 第一关拒绝集 (build_core_g 的 cand 是第一关幸存者)'),
    ('§3', 'T0 全分布 (源标签 + 端点复利版另名) + 资本加权', 'done',
     'T0_full_distribution/stage_distributions_2010-2014.csv', ''),
    ('§3', '伪路径 U-IID / 行业 I-IID / 行业×市值三档, 各 128 起, 输家赢家对称', 'done',
     'T0_full_distribution/pseudo_paths_2010-2014.csv',
     'E6g 只做输家一侧且只匹配到行业; 本轮两侧对称 + 加市值三档'),
    ('§3', '三层分类: factor_parent_relation / need_parent_role_map / taxonomy', 'done',
     'registry/need_parent_role_map.csv', ''),
    ('§3', '相关与聚类 (average/complete linkage on 1-|rho|, 不用 Ward)', 'done',
     'clustering/factor_clusters_2010-2014.json',
     '结论: 两段同簇关系仅 0.65-0.72 一致, 聚类支持不了轴定义 (按 plan 只作校验)'),
    ('§3', '主体聚类 (股票-日画像 KMeans k{3,4,5} seed 1109)', 'deferred', '',
     '因子聚类已做完且结论是"支持不了轴定义"; 主体聚类对需求卡无增量, '
     '按 plan §2.2 留 deferred 并写理由。影响: R0 少一张描述性分层图'),
    ('§3', 'R0 交付包给规划 session', 'done', 'REPORT_R0.md', ''),
    # ---------------- §4 记录 A ----------------
    ('§4', '记录 A v0 物化为可编译清单 (只从 routed 行编译)', 'done',
     'registry/route_manifest.json', '九张卡; 71 routed / 37 candidate / 28 diag / 212 unassigned'),
    ('§4', '记录 A v1 (规划 session 在 R0 后补)', 'deferred', '',
     '规划 session 的工作, 不是执行端。执行端已按 brief §4 先跑 v0 已激活路线'),
    ('§4', '模板参数逐字 (SLOT α / FOCAL 四对照 / ADD-SWAP η / CONJ / R-O / I-P / L-Q)',
     'done', 'checks/derivation_descriptors.csv', '2,844 个描述符, ID 单射已断言'),
    ('§4', '交互清单事前冻结 (M-T×E-V / E-V×R-O / E-V×I-P, 每对四条完整策略)', 'done',
     'interaction_results/interactions_2010-2014.csv', ''),
    ('§4', '迁移: 每卡 >=1 原生母体 + >=1 结构不同的迁移母体', 'done',
     'registry/route_manifest.json', ''),
    ('§4', '全部基本格 H5 + 同格补 H{3,10,20} + 原父同 H 一起跑', 'done',
     'route_results/hextra_2010-2014_A06.csv', ''),
    ('§4', '加回/移出集合 1-20 日事件剖面', 'done',
     'route_results/event_profile_2010-2014_A06.csv', ''),
    # ---------------- §5 R1-R3 ----------------
    ('§5', '集合契约 U/C/V/B/D + ADD/SWAP/CONJ 的 identity 与预算', 'done',
     'checks/rule_anchors_2010-2014.json', ''),
    ('§5', '每条主路径的确定性对照 (同人数核心 / 同人数反向 / 共同可得域父)', 'done',
     'route_results/summary_2010-2014_A06.csv', ''),
    ('§5', '同仓位对照 (逐形成日缩到两者较小仓位)', 'changed',
     'paired_controls/samepos_M-T-tcv-vs-t60_2010-2014.csv',
     '主运行里漏了这一个, 事后补跑; 本轮只对 M-T (唯一为正的路线) 补。'
     '影响: 其余八条路线没有同仓位列 —— 但它们对母体已为负, 同仓位只会更负或持平'),
    ('§5', '随机参照 U-IID / 行业 I-IID / 持续 I-P20, 256 起 + MCSE 补样', 'changed',
     'random_registry/random_refs_2010-2014_s0.csv',
     '只对九张卡的【中心代表】跑满 256 (+3 格按 MCSE 规则补到 512), 不是每个网格格。'
     '理由: 2,844 格 x 3 机制 x 256 = 218 万次引擎调用。'
     '其余格给三个确定性对照。沿 E6g L5 的做法, 范围已登记'),
    ('§5', 'Δgross 按新增/移出/幸存者重定权三集合分解 + 逐日先恒等再汇总', 'done',
     'route_results/attrib_2010-2014_A06.csv', ''),
    ('§5', '域 + S0 固定代表 / S1 层级等权组合 / S2 局部收缩', 'done',
     'domain_selection/domain_selection.csv', '155 个域; 组合合并目标权重后跑真实账户'),
    ('§5', 'REPORT_part1', 'done', 'REPORT_part1.md', ''),
    # ---------------- §6 / §7 闸 ----------------
    ('§6', '记录 B: 用户 + 规划 session 冻结后段清单', 'blocked_by_gate', '',
     '**这是用户的闸**。守卫以代码强制 (registration/record_B_approved.json 不存在时'
     '受保护对象一律拒进 2019+, 13 条攻击测试已验)'),
    ('§7', '后段首次观察 (2019-2023 / 2024-2026)', 'blocked_by_gate', '',
     '记录 B 之后才能跑。本轮结果目录里【没有任何】2019+ 的受保护对象结果'),
    ('§7', 'REPORT_part2', 'blocked_by_gate', '', '同上'),
    # ---------------- §8 carried L ----------------
    ('§8', 'L 主网格 8 账户 x H{1,2,3,5,10,15,20,30} x b{0,5,10,15,20,30} x 两预算 = 768',
     'done', 'L/L_main_2019-2023.csv', '四段各 768 行; b=0 阻断锚每段 14/14'),
    ('§8', 'actual_incumbent 八账户 x H{3,5,15,20} x b{0,10,20} x 两预算 = 192, 与 target 并排',
     'done', 'L/L_incumbent_lx_2019-2023.csv', '336 行/段 (两种 incumbent 各 168)'),
    ('§8', 'L-X 提前退出 R1/R2/A06/A08 x H x b x 两开关四组合 = 192', 'done',
     'L/L_exit_engine_anchor_2010-2014.json',
     '自写带提前退出的持仓引擎; 阻断锚: 退出全假时复现 sparse_pnl_H (~1e-14)'),
    ('§8', '新主路线在记录 B 指定的中心代表与 S1 组合上补 b{0,10} x H{3,5,15,20}',
     'blocked_by_gate', '', '名单要等记录 B 冻结; 按 brief §8 "名单后段前冻结"'),
    ('§8', 'L-Q 边缘替代域进同成本完整策略比较 (NEW40 血缘, 登记前只推导段)', 'done',
     'route_results/summary_2010-2014_A06.csv', ''),
    ('§8', '库存三层比较 (全可成交 / 受限 / 提前退出) + 影子账户逐日现金持仓',
     'changed', 'L/L_incumbent_lx_2010-2014.csv',
     '做了"提前退出 vs 全关"这一层与 actual/target incumbent 这一层; '
     '**受限账户 (买不到/卖不掉) 那一层没做** —— 需带成交约束的影子账户改造。'
     '影响: 缺"可成交性"对 L 结论的影响量'),
    ('§8', '成本 A{1,5,10,20}亿 x κ{0.25,0.5,1,2} x 两模型 + 12bp 情景', 'done',
     'cost/impact_scenarios.csv', '101,376 行'),
    ('§8', '求根: 容量 A* 与优势交点 A_delta*', 'done', 'cost/capacity_A_star.csv',
     'A* 24,576/24,576 有正根, 回代残差 3.55e-15; 交点 49% 存在, '
     '其余因 Δn/(κΔC)<=0 记 no_crossing 而非平方成伪容量'),
    ('§8', '5%/10%/20% ADV 参与率压力列', 'unavailable',
     'cost/participation_notional.csv',
     '需逐票 ADV20 明细, 本轮 L 只存了冲击括号的逐日均值。'
     '已给日均名义成交额作替代。影响: 没有参与率口径的压力列'),
    ('§8', '领导表草稿 (H x A x κ 净值), 经用户, 不选生产 H', 'done',
     'cost/leader_table_draft_H_x_A.csv', ''),
    # ---------------- §9 carried T ----------------
    ('§9', 'T1 归因 + 逐日恒等式 excess_clean - excess_pool = position x (pool - clean)',
     'done', 'T/T1_identity_2019-2023.json', '每段 11 个账户全过, max|d| ~1e-17'),
    ('§9', 'T2 绝对人数 N{30..200} 与 keep{15..50} x PRE/POST x 三核 x 三否决栈 = 288',
     'done', 'T/T2_budget_2019-2023.csv', '阻断锚: 无否决时 PRE/POST 恒等, 每段 48/48'),
    ('§9', 'T3 子样本 N{150,250} x 32 seed x {IID, 持续} x 三种运行', 'done',
     'T/T3_subsample_2019-2023.csv', '每段 2,048 行'),
    ('§9', 'T4 P16 加密 560 + 与 E6g 重叠路径逐日锚', 'done',
     'T/T4_e6g_overlap_anchor_2019-2023.json', '重叠 192 格逐位相符 (~1e-15)'),
    ('§9', 'T5 状态量 (只作描述, 不建开关)', 'done', 'T/T5_state_2019-2023.csv', ''),
    # ---------------- §10 统计 ----------------
    ('§10', 'NW lag max(5,H) + 20/60 敏感性', 'done', 'stats/pointwise_nw.csv', ''),
    ('§10', 'stationary bootstrap 2,000 x 块长 20/60 x 段内 x 共 draw', 'done',
     'stats/family_bands.csv', ''),
    ('§10', 'F-route / F-headline 同时带', 'done', 'stats/family_bands.csv', ''),
    ('§10', 'F-L / F-T 家族带', 'deferred', '',
     'L 与 T 的逐日 Δ 序列本轮没有按描述符落盘 (只落了汇总), 所以算不了共 draw 同时带。'
     '影响: L/T 的结论只有点估与网格一致性, 没有家族带'),
    ('§10', 'Romano-Wolf stepdown 附列', 'deferred', '',
     '同时带已用共 draw max-|t| 主口径; RW stepdown 附列未做。'
     '影响: 缺一个更保守的逐步调整 p 值'),
    # ---------------- §11-§14 ----------------
    ('§11', '事前登记落盘于首次新收益评价之前', 'done', 'preregistration.md',
     '12:08:45 落盘'),
    ('§12', '真实源必核 + 新增反例', 'done', 'checks/rule_anchors_2010-2014.json', ''),
    ('§13', '三次交付 + 两次记录的运行组织', 'changed', 'REPORT_part1.md',
     'part1 已交; part2/part3 等记录 B'),
    ('§14', 'coverage / limit_register / source_corrections / 线状态与 park 草稿',
     'done', 'limit_register.md', 'coverage.csv 本身由本脚本生成, 证据指向同批交付的 limit_register'),
]


def main():
    rows = []
    for sec, item, st, ev, why in ITEMS:
        hit = sorted(glob.glob(os.path.join(R, ev))) if ev else []
        final, note = st, why
        if st in ('done', 'reused') and ev and not hit:
            final = 'unavailable'
            note = (why + ' | ' if why else '') + '声称 %s 但证据文件不存在: %s' % (st, ev)
        rows.append(dict(brief_section=sec, item=item, status=final, evidence=ev,
                         n_evidence_files=len(hit), reason_or_impact=note))
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(R, 'coverage.csv'), index=False)
    print(d.status.value_counts().to_string())
    bad = d[d.status == 'unavailable']
    if len(bad):
        print('\n!! 证据缺失或不可用:')
        print(bad[['brief_section', 'item', 'evidence']].to_string(index=False))
    print('\ndeferred / changed / blocked 明细:')
    print(d[d.status.isin(['deferred', 'changed', 'blocked_by_gate'])]
          [['brief_section', 'item', 'status']].to_string(index=False))


if __name__ == '__main__':
    main()
