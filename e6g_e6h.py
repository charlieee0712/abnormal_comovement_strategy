#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g K4: E6h 登记草稿 (brief §7)。

逐键给: 经济假设 / 失败模式 / 机制来源 / 推导段来源 / 表达式 / 方向 / 角色 / 合适母体 /
        可能失效原因 / 反向控制 / 数据依赖 / 历史见过结果的范围 / 下一轮允许评估域。
因果语言一律写"假设"。**新键 2019+ 的开关本轮保持关闭。**
不硬裁到 <=6 轴 x <=3 键: 40 键全部附完整角色记录与未测项。
"""
import os, sys, glob
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6g_core as G

RES = G.RES
AXES = {
    'CLV': '资金流/收盘位置', 'CVR': '资金流/收盘位置', 'CVR_5d': '资金流/收盘位置',
    'CMF_20d': '资金流/收盘位置',
    'shadow_asymmetry': '日内结构', 'tug_of_war': '日内结构', 'intraday_ret': '日内结构',
    'intraday_ret_consistency_5d': '日内结构', 'daynight_divergence': '昼夜路径',
    'overnight_ret': '昼夜路径', 'positive_day_ratio_5d': '昼夜路径',
    'agreement_count_5d': '昼夜路径', 'overnight_ret_trend': '昼夜路径',
    'overnight_ret_cross_sectional_rank': '昼夜路径',
    'gap_zscore_20d': '跳空', 'gap_abs_zscore_20d': '跳空', 'gap_percentile_60d': '跳空',
    'gap_vs_sector': '跳空', 'gap_rank_in_sector': '跳空', 'gap_trend_5d': '跳空',
    'consecutive_gap_same_direction': '跳空', 'gap_direction_consistency_5d': '跳空',
    'gap_volume_ratio': '跳空x量',
    'volume_ratio_1d': '快量能', 'volume_ratio_3d': '快量能', 'volume_ratio_5d': '快量能',
    'volume_zscore_60d': '快量能', 'volume_accel_3d': '快量能', 'volume_trend_10d': '快量能',
    'volume_regime_break': '快量能', 'volume_rank_market': '快量能',
    'turnover_5d': '换手水平', 'turnover_rank_market': '换手水平',
    'amount_ratio_1d': '成交额', 'amount_concentration_5d': '成交额',
    'amihud_daily': '流动性', 'amihud_ratio_5d_20d': '流动性',
    'inside_bar_freq_20d': 'K 线形态', 'mcap_rank': '规模(诊断)',
}


def main():
    R = pd.read_csv(os.path.join(RES, 'registry', 'key_registry.csv'))
    R = R.set_index('key')
    ks = pd.concat([pd.read_csv(x) for x in sorted(glob.glob(
        os.path.join(RES, 'K_discovery', 'K2_2*.csv')))], ignore_index=True)
    v = ks[ks.role == 'veto_on_parent']
    c = ks[ks.role == 'ctl_core_matchN'][['segment', 'key', 'input', 'direction', 'k',
                                          'parent', 'net8_ann']].rename(
        columns={'net8_ann': 'core_n8'})
    r = ks[ks.role == 'ctl_reverse_matchN'][['segment', 'key', 'input', 'direction', 'k',
                                             'parent', 'net8_ann']].rename(
        columns={'net8_ann': 'rev_n8'})
    m = (v.merge(c, on=['segment', 'key', 'input', 'direction', 'k', 'parent'], how='left')
          .merge(r, on=['segment', 'key', 'input', 'direction', 'k', 'parent'], how='left'))
    m['vs_core'] = m.net8_ann - m.core_n8
    m['vs_rev'] = m.net8_ann - m.rev_n8
    agg = m.groupby('key').agg(vs_core_med=('vs_core', 'median'), vs_core_max=('vs_core', 'max'),
                               vs_rev_med=('vs_rev', 'median'), vs_rev_max=('vs_rev', 'max'),
                               n_cell=('vs_core', 'size'))

    L = []
    L.append('# E6h 登记草稿（执行端草稿；规划 session 在 REVIEW 定稿，用户定）\n')
    L.append('由 E6g 的 `registry/key_registry.csv` 与 `K_discovery/K2_*.csv` 自动生成，'
             '2026-09-11。**因果语言一律写「假设」**。\n')
    L.append('**本轮边界**：40 键只在 2010-2014 / 2015-2018 两个推导段测过，`label_end ≤ 2018-12-31`；'
             '**新键 2019+ 的开关本轮保持关闭**；本表不构成准入，只是下一轮的登记材料。\n')
    L.append('「vs 同人数 core」= 该键作否决叠 R2/A06/A08 后，相对「在父核末级分数上剔掉同样多只」的差；'
             '「vs 同人数反向」= 相对「把该键方向反过来剔同样多只」的差。两列都是**四段合并中位 / 最大**，'
             '单位年化点。`n_cell` = 该键的否决格数（输入 × 方向 × k × 母体 × 段）。\n')
    L.append('| 键 | 轴（假设） | 角色 | 方向 | vs 同人数 core 中位/最大 | vs 同人数反向 中位/最大 | '
             '并列占比 | 复权 | 访问史 | 允许评估域 |')
    L.append('|---|---|---|---|---|---|---|---|---|---|')
    for k in G.NEW40:
        a = agg.loc[k] if k in agg.index else None
        rr = R.loc[k] if k in R.index else None
        diag = (k in G.DIAGNOSTIC_ONLY)
        role = ('诊断行（中性化目标，不作候选）' if diag
                else ('信号成分（池内分布被截断）' if k in G.SIGNAL_TRUNCATED
                      else ('全市场占位' if k in G.MARKET_WIDE_PLACEHOLDER else '候选否决/腿')))
        tie = ('%.3f' % rr['tie_frac_raw']) if rr is not None and np.isfinite(
            rr.get('tie_frac_raw', np.nan)) else 'NA'
        adj = str(rr['adj_class3']) if rr is not None else 'NA'
        adj = {'invariant_under_price_adjustment': '价格复权不变',
               'changes_under_price_adjustment': '价格复权会变',
               'unknown_share_count_not_tested': '依赖股数/额，未测',
               'changes_and_volume_untested': '会变且依赖股数'}.get(adj, adj)
        hist = str(rr['access_history_label']) if rr is not None else 'NA'
        L.append('| `%s` | %s | %s | 双向都测 | %s | %s | %s | %s | %s | 仅 2010-2018，`label_end ≤ 2018-12-31` |'
                 % (k, AXES.get(k, '未归轴'), role,
                    ('%+.3f / %+.3f' % (a.vs_core_med, a.vs_core_max)) if a is not None else 'NA',
                    ('%+.3f / %+.3f' % (a.vs_rev_med, a.vs_rev_max)) if a is not None else 'NA',
                    tie, adj, hist))
    L.append('')
    L.append('## 每轴的经济假设与失败模式（假设，未验证）\n')
    axes = {}
    for k, ax in AXES.items():
        axes.setdefault(ax, []).append(k)
    HYP = {
        '资金流/收盘位置': ('假设：收盘价在当日区间中的位置反映主动买卖压力的残余。',
                     '失败模式：与 I11 的 CMF 成分共线；`CVR` 与已在用的 `intraday_cvr_1d` 是公式别名。'),
        '日内结构': ('假设：日内价格路径的不对称性携带超出收益水平的信息。',
                 '失败模式：与波动代理高度相关；`intraday_ret` 是 I11 信号成分，池内被截断。'),
        '昼夜路径': ('假设：隔夜与日内收益的分解能区分信息驱动与流动性驱动。',
                 '失败模式：多为少数离散取值，结果被平局规则主导。'),
        '跳空': ('假设：跳空的幅度/方向/持续性反映未被价格完全吸收的消息。',
               '失败模式：`gap_vs_sector` 与 `gap_rank_in_sector` 是**全市场**占位不是行业内；零跳空并列块极大。'),
        '跳空x量': ('假设：带量的跳空比不带量的更可能延续。', '失败模式：量的口径未测复权敏感。'),
        '快量能': ('假设：短窗成交量相对基准的异常反映关注度突变。',
                '失败模式：与 `abn_turnover` 同源；`volume_accel_3d` 是未标准化的股数二阶差分，重尾极端。'),
        '换手水平': ('假设：换手水平本身是规模/流动性代理。',
                 '失败模式：与在用的 `conditional_turnover` / `turnover_volatility_60d` 共线。'),
        '成交额': ('假设：成交额的集中度反映交易的时间分布。', '失败模式：与换手同源；单位需核为元。'),
        '流动性': ('假设：Amihud 非流动性反映冲击成本的横截面差异。',
                '失败模式：与容量/冲击模型重复计价；pool0 已有 2,000 万成交额地板。'),
        'K 线形态': ('假设：内包 K 线频率反映波动压缩。', '失败模式：整数 0–20，并列占比 1.000。'),
        '规模(诊断)': ('不是候选：`mcap_rank` 是中性化的目标本身。', '——'),
    }
    for ax in sorted(axes):
        h = HYP.get(ax, ('（未写假设）', '（未写失败模式）'))
        L.append('### %s（%d 键）\n' % (ax, len(axes[ax])))
        L.append('- %s' % h[0])
        L.append('- %s' % h[1])
        sub = agg.reindex([k for k in axes[ax] if k in agg.index])
        if len(sub):
            L.append('- 本轮推导段实测：vs 同人数 core 中位 %.3f（最好的键 %s，%.3f）；'
                     'vs 同人数反向 中位 %.3f'
                     % (sub.vs_core_med.median(), sub.vs_core_med.idxmax(),
                        sub.vs_core_med.max(), sub.vs_rev_med.median()))
        L.append('')
    L.append('## 总体读法\n')
    L.append('- 40 键作否决叠父，**vs 同人数 core 的中位是 %.3f（RAW）/ %.3f（RANK）**，'
             '即在父核内按核自己的分数剔掉同样多只，通常比用新键剔更好。'
             % (m[m.input == 'RAW'].vs_core.median(), m[m.input == 'RANK'].vs_core.median()))
    L.append('- 更关键的是 **vs 同人数反向的中位 ≈ %.3f**：把方向反过来剔同样多只，'
             '平均结果没有区别——这说明这批键在这个角色上**没有可用的方向性**。'
             % m.vs_rev.median())
    L.append('- 排在前面的几个键（`%s`）多半是已在用键的公式别名或 I11 信号成分，'
             '不是新信息来源。' % '`、`'.join(agg.nlargest(5, 'vs_core_med').index.tolist()))
    L.append('- **八个键的池内并列占比 = 1.000**（离散计数/二值），在它们上面做 k 分位否决时，'
             '结果由平局处置规则决定而不是由因子决定；下一轮若测这些键必须先定平局口径。')
    L.append('- 本表**不硬裁**到少数轴少数键：40 键全部留完整记录与未测项，由用户决定下一轮取哪些。')
    p = os.path.join(RES, 'E6h_registration_draft.md')
    open(p, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('写好 %s, %d 行, %d 键' % (p, len(L), len(G.NEW40)))
    print('vs_core 中位 RAW %.3f / RANK %.3f; vs_rev 中位 %.3f'
          % (m[m.input == 'RAW'].vs_core.median(), m[m.input == 'RANK'].vs_core.median(),
             m.vs_rev.median()))


if __name__ == '__main__':
    main()
