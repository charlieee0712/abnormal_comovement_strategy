#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h REPORT_R0: 交给规划 session 的 R0 包索引 + 读数 + 待定项 (brief §3 末条 / §13)。"""
from __future__ import annotations
import os
import sys
import json
import time

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H

RES = H.RES
SEGS = list(H.DERIV_SEGS)


def main():
    rm = json.load(open(os.path.join(RES, 'registry', 'route_manifest.json')))
    al = pd.read_csv(os.path.join(RES, 'registry', 'alias_measurements.csv'))
    rel = pd.concat([pd.read_csv(os.path.join(
        RES, 'T0_full_distribution', 'factor_parent_relation_%s.csv' % s)) for s in SEGS])
    cl = {s: json.load(open(os.path.join(RES, 'clustering',
                                         'factor_clusters_%s.json' % s))) for s in SEGS}
    sem = pd.read_csv(os.path.join(RES, 'registry', 'feature_semantics.csv'))

    L = []
    A = L.append
    A('# E6h REPORT_R0 —— 需求诊断与三层分类（交规划 session）')
    A('')
    A('执行 session，%s。结果目录 `%s`（47）。'
      % (time.strftime('%Y-%m-%d'), os.path.basename(RES)))
    A('推导段 `%s` / `%s`，全部 `exploratory`。事前登记已落盘于任何新收益评价之前。'
      % (SEGS[0], SEGS[1]))
    A('')
    A('---')
    A('')
    A('## 摘要（12 行）')
    A('')
    A('1. 阶段 0 交付齐：源清单、守卫（**攻击 13 条全拒 + 合法 7 条全放行**）、'
      '四段锚 **22/22**（11 个源锚重建 vs E6g 逐位，max|d| ~1e-16）、'
      '`feature_semantics.csv`（87 键 × 32 列）、`feature_taxonomy.csv`（10 族多标签）、'
      '`preregistration.md`。')
    A('2. brief 的源码级断言**逐条成立**（三个自定义键的负号、K/T/C 身份与公式、'
      'pct 对源值取、E-P 比例 vs 计数、NEW40 名单 40/40）。两处输入指纹与 plan 不符，'
      '已定位为负号勘误的同源补写，记 WARN。')
    A('3. **池子右偏**：pool0 均值 −7.4 / +0.5 bp，但中位 **−54.3 / −37.9 bp**，'
      '负票占比 55–56%。"剔输家"主要是推中位数，均值由正尾主导。')
    A('4. **构成解释近一半**：真实输家 −566 / −590 bp，同人数随机只解释 1.3% / −0.1%，'
      '＋行业到 25.9% / 18.0%，**＋行业×市值三档到 47.3% / 37.3%**；'
      '赢家一侧**对称**（44.5% / 36.6%）。MCSE ≤ 0.21 bp。')
    A('5. E6g 只做输家一侧、只匹配到行业（报 ~26%），本轮两侧对称 + 加市值后近一半。'
      '**不能**由此说行业/市值信息无用——过度匹配会把研究中的信息一起匹配掉，三层并列报。')
    A('6. **R1 两关的分离力在两段之间翻转**：2010-14 第一关（K）29.2 bp / 第二关（T）'
      '17.6 bp；2015-18 第一关 11.3 bp / 第二关 28.0 bp。')
    A('7. R1 的第二关拒绝集 vs 行业×市值匹配随机：2010-14 **+2.18 bp（剔错票）**、'
      '2015-18 **−6.06 bp（真剔坏票）**——**只在一段成立，是翻转不是失效**。'
      'R2/A06/A08 的拒绝集在两段都比匹配随机差（真在剔坏票）。')
    A('8. **没有任何单一测量能在拒绝集里强力排序收益**：`rho_label_in_D` 全域中位 %.4f、'
      '最大 |%.4f|。可回收的拒绝机会不在单键里，只能靠条件结构。'
      % (rel['rho_label_in_D'].median(), rel['rho_label_in_D'].abs().max()))
    A('9. 排序前列是 `turnover_rank_market` / `turnover_5d` / `CVR_20d`，'
      '**本轮新造的 `REL_IND_20` 与它们同档**（两段同号、三母体一致）——I-P 路线的直接证据。')
    A('10. **统计聚类给不出稳定分区**：average linkage 退化成链（k=5 簇大小 82/2/1/1/1），'
      'complete 分得开（k=3 为 40/30/17）但两段同簇关系只 **0.65–0.72** 一致。'
      '按 plan §2.1 聚类只作校验——校验结果是它支持不了任何轴定义。')
    A('11. **60 对高相关里只有 2 条真别名**（`CVR ≡ intraday_cvr_1d`，两段各一）。'
      '`gap_rank_in_sector` vs `overnight_ret_cross_sectional_rank` 的 ρ = **1.000000**'
      '（六位小数）但同格率只有 99.7%、max|d| 0.018——**ρ=1 不等于别名**。')
    A('12. 记录 A v0 已物化为可编译清单：**%d 张卡**，（键×母体）对 routed %d / '
      'candidate %d / diagnostic_only %d / unassigned %d。未路由全留考虑台账。'
      % (rm['counts']['n_routes'], rm['counts']['n_routed_pairs'],
         rm['counts']['n_candidate'], rm['counts']['n_diagnostic_only'],
         rm['counts']['n_unassigned']))
    A('')
    A('---')
    A('')
    A('## R0 交付包清单（brief §3 末条）')
    A('')
    A('| 产物 | 内容 |')
    A('|---|---|')
    A('| `parent_need_ledger.md` | 池子画像 + 三层构成归因 + 四母体逐个的集合分布、'
      'D-vs-匹配随机判据、D 内最能排序标签的键 |')
    A('| `registry/feature_semantics.csv` | 87 键身份：源公式/源符号/经济量/窗口/'
      '`value_used_for_pct`/复权/别名/历史观察段 |')
    A('| `registry/feature_taxonomy.csv` | 第一层测量目录，10 族多标签，每标签带 basis |')
    A('| `T0_full_distribution/factor_parent_relation_*.csv` | 第二层：87 键 × 4 母体 × 2 段，'
      '与三腿/核分数的相关、在 B/D/U 内对标签的排序能力 |')
    A('| `registry/need_parent_role_map.csv` | 第三层用途路由，含 status 与证据标志 |')
    A('| `registry/route_manifest.json` | **记录 A v0**，研究程序只从这里编译 |')
    A('| `registry/consideration_ledger.csv` | 未路由项 + 理由 |')
    A('| `registry/alias_measurements.csv` | 高相关对的真别名实测 |')
    A('| `T0_full_distribution/stage_*.csv`、`pseudo_paths_*.csv` | 全分布、逐日集合、伪路径 |')
    A('| `stage_sets/stage_sets_*.npz` | U/C/V/B/D（R1 另含 S1 与分关拒绝）位打包 |')
    A('| `clustering/` | 87×87 相关（均值/中位/有效日）、signed 边表、两种 linkage |')
    A('| `checks/`、`runtime/` | 守卫攻击测试、四段锚、并发实测 |')
    A('')
    A('---')
    A('')
    A('## 规划 session 在记录 A v1 里要定的事')
    A('')
    A('1. **R1 两关翻转怎么归属**：是 T 的测量问题（M-T 的假设），还是段特性？'
      'R0 只给出翻转事实，归属要靠 M-T 的 SLOT 实验 + carried T 的时间异质块。')
    A('2. **构成占近一半之后，行业轴还怎么问**：I-P 的两张卡（向上机会 / 向下风险）'
      '目前都建在 `IND_CUR_*` / `REL_IND_*` 上。若规划 session 认为应先做'
      '"行业匹配后仍剩什么"的分解，需在 v1 里加卡。')
    A('3. **37 个 candidate_for_routing 是否升为 routed**：它们有证据标志但 v0 未路由。'
      '证据在 `need_parent_role_map.csv` 的三个 flag 列。')
    A('4. **聚类既然不稳，是否还要主体聚类（股票-日画像）**：因子聚类已做完且结论是'
      '"支持不了轴定义"；plan §2.2 的 KMeans 主体聚类尚未跑，'
      '若规划 session 认为它对需求卡无增量，可标 deferred 并写理由。')
    A('5. **`gap_vs_sector` / `gap_rank_in_sector` 的处置**：已实测**不是**'
      '`overnight_ret` 的别名（同格率 93% / 28%），但源定义确是全市场占位。'
      'v0 把它们标 `diagnostic_only`，是否维持。')
    A('')
    A('---')
    A('')
    A('## 执行端接着做什么（不等 v1）')
    A('')
    A('按 brief §4："执行端在 v1 前先跑 v0 已激活路线，v1 只增量补跑。"')
    A('下一步是推导段的路线实验（R1–R3）：九张卡的预设格、必要交互、对照、'
      '固定代表 / 层级等权组合 / 局部收缩选择，产出 `REPORT_part1`。')
    A('')
    A('**记录 B 之前不会有任何 2019+ 的受保护对象结果**——由 `e6h_core.guard_h` 代码强制，'
      '不依赖执行端自觉（攻击测试 13 条全部被拒）。')
    A('')

    p = os.path.join(RES, 'REPORT_R0.md')
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(L) + '\n')
    print('REPORT_R0.md: %d 行' % len(L))


if __name__ == '__main__':
    main()
