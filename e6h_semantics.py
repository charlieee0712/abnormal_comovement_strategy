#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 阶段 0: feature_semantics.csv + feature_taxonomy.csv (brief §2 第二条)。

在 E6g `registry/key_registry.csv` (75 键 x 37 列) 基础上:
  - 加 brief §1.3 要求的三列 source_sign / economic_direction / value_used_for_pct
  - 加 plan §1.3 要求的身份列 (原始字段/公式/经济量/单位/窗口/min_periods/分母/
    平滑顺序/复权/可得时点/有效条件/缺失标志/精确别名/近似同源/已有角色/previous_looks)
  - 加 12 个新派生键作为新行
  - 第一层测量目录 (plan §2.1) 多标签, **按源公式定, 不按名字**

taxonomy 的每个标签都写 basis (依据哪一条公式), 便于规划 session 复核。
"""
from __future__ import annotations
import os
import sys
import re
import json
import inspect

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6g_core as G
import features_daily as FD
import comprehensive_factor_diagnosis as C
import pool_screening_v2 as P

RES = H.RES

# ---------------------------------------------------------------- 第一层标签
FAMILIES = {
    'activity_level': '活动水平 (成交量/换手/成交额的绝对或截面水平)',
    'self_relative_anomaly': '相对自身历史的异常 (比值/z/分位, 分母是自身历史)',
    'activity_stability': '活动的持续性与稳定性 (二阶矩/趋势/加速)',
    'price_response_position': '价格响应与日内位置 (收盘在区间/相对 VWAP/距高点)',
    'overnight_shock': '隔夜冲击与昼夜结构',
    'return_path': '收益路径与分布形状 (累计/一致性/矩)',
    'flow_price_proxy': '资金流的价格加权代理',
    'liquidity_cost': '流动性成本代理 (单位成交额的价格冲击)',
    'peer_relative': '同业/截面相对信息',
    'diagnostic_scale': '诊断性规模与混杂控制',
}

# 键 -> (标签元组, 依据)  —— 依据必须引公式, 不能引名字
TAX = {
    # --- 活动水平 ---
    'turnover_5d': (('activity_level',), 'turnover_rate.rolling(5).mean(): 换手水平的短窗均值'),
    'turnover_rank_market': (('activity_level', 'peer_relative'),
                             'turnover_rate.rank(axis=1,pct=True): 当日截面换手排序'),
    'volume_rank_market': (('activity_level', 'diagnostic_scale', 'peer_relative'),
                           'volume.rank(axis=1,pct=True): 股数量截面排序, 与股本混杂'),
    'conditional_turnover': (('activity_level', 'price_response_position'),
                             'turnover_rate/(|log(close/lclose)|+1e-4): 换手÷价格响应, 两者混合; '
                             '分母近零与分子高是不同情况'),
    # --- 相对自身异常 ---
    'volume_ratio_1d': (('self_relative_anomaly',), 'volume/vol_ma20'),
    'volume_ratio_3d': (('self_relative_anomaly',), 'vol_ma3/vol_ma20'),
    'volume_ratio_5d': (('self_relative_anomaly',), 'vol_ma5/vol_ma20'),
    'volume_zscore_60d': (('self_relative_anomaly',), '_rolling_zscore(volume,60)'),
    'amount_ratio_1d': (('self_relative_anomaly', 'activity_level'),
                        'amount/amt_ma20: 金额口径(与股数口径不同经济量)'),
    'abn_turnover': (('self_relative_anomaly',),
                     '源函数 return -abn, abn=MA20(turnover)/MA120(turnover); 源值高=换手比低'),
    'volume_regime_break': (('self_relative_anomaly',),
                            '(volume >= vol_max_20d): 二元状态, 窗口是否含当日须核'),
    'amount_concentration_5d': (('self_relative_anomaly', 'activity_level'),
                                'amt_5d/amt_20d: 活动的时点分布, 不直接推拥挤'),
    'amihud_ratio_5d_20d': (('self_relative_anomaly', 'liquidity_cost'),
                            'amihud_5d/amihud_20d: 流动性代理的短/长变化, 非绝对水平'),
    # --- 活动稳定性 ---
    'turnover_volatility_60d': (('activity_stability', 'activity_level'),
                                'turn.rolling(60,min_periods=30).std(): 标准差同时含水平与不稳定性, '
                                '不能改名叫"换手水平"'),
    'TCV_20': (('activity_stability',), 'std20/mean20: 尺度不变的变异系数, 与 T 分离水平'),
    'TCV_60': (('activity_stability',), 'std60/mean60: 与源 T 同窗口, 只去掉水平'),
    'volume_trend_10d': (('activity_stability', 'self_relative_anomaly'),
                         '(vol_ma5-vol_ma10)/vol_ma10: 持续变化, 与一次脉冲分开'),
    'volume_accel_3d': (('activity_stability',),
                        'volume.diff().diff(): 源是二阶差分, 不是三日比例'),
    'CCV_20d': (('activity_stability', 'price_response_position'),
                '_rolling_corr(close,turn,20): 价与换手的相关, 量价关系'),
    'inside_bar_freq_20d': (('activity_stability', 'price_response_position'),
                            'is_inside_low_vol.rolling(20).sum(): 低量内包形态频数(压缩状态)'),
    'volume_momentum_divergence': (('activity_stability', 'return_path'),
                                   'vol_mom - price_mom: 量变化与价变化之差, 先核两项量纲'),
    # --- 价格响应/位置 ---
    'CLV': (('price_response_position',), '(2*close-high-low)/hl_range: 收盘在当日区间位置'),
    'CLV_20d': (('price_response_position',), 'clv.rolling(20).mean()'),
    'CVR': (('price_response_position',), '(close-vwap)/vwap: 收盘相对当日均价'),
    'CVR_5d': (('price_response_position',), 'cvr.rolling(5).mean()'),
    'CVR_20d': (('price_response_position',), 'cvr.rolling(20).mean() —— 核心 C 腿'),
    'intraday_cvr_1d': (('price_response_position',), 'close/vwap-1: CVR 的公式别名(E6e 研究 spec)'),
    'distance_from_high_20d': (('price_response_position', 'return_path'),
                               'close/recent_high_20d-1'),
    'recent_high_20d': (('price_response_position',), 'close.rolling(20).max()'),
    'days_since_high': (('price_response_position',), '距最近 20 日高点的天数'),
    'shadow_asymmetry': (('price_response_position',), 'upper_shadow-lower_shadow: 日内路径'),
    'shadow_asymmetry_20d': (('price_response_position',), '上式的 20 日均值'),
    'stealth_score': (('price_response_position', 'activity_level'),
                      'vol_ratio/range_ratio: 量 ÷ 幅度'),
    'gap_survival_ratio': (('price_response_position', 'overnight_shock'),
                           'total_change/gap_raw: 跳空是否被日内消化'),
    # --- 隔夜冲击 ---
    'overnight_ret': (('overnight_shock',), 'log(open/lclose): 当日隔夜收益原量, 非风险大小'),
    'gap_zscore_20d': (('overnight_shock', 'self_relative_anomaly'), '_rolling_zscore(gap,20) 有方向'),
    'gap_abs_zscore_20d': (('overnight_shock', 'self_relative_anomaly'),
                           '_rolling_zscore(|gap|,20): 绝对隔夜变化的自身异常'),
    'gap_percentile_60d': (('overnight_shock', 'self_relative_anomaly'),
                           '_rolling_percentile(|gap|,60): 时序分位'),
    'gap_trend_5d': (('overnight_shock', 'activity_stability'),
                     '(|gap|-|gap|.shift(4))/4: 绝对隔夜变化的变化率, 非价格动量'),
    'consecutive_gap_same_direction': (('overnight_shock', 'return_path'),
                                       'gap_sign 的连续同号长度'),
    'gap_direction_consistency_5d': (('overnight_shock', 'return_path'),
                                     'gap_pos.rolling(5,min_periods=3).mean(): 隔夜【正向比例】, '
                                     '不是绝对一致性 -> 阈值用比例不用计数'),
    'gap_volume_ratio': (('overnight_shock', 'self_relative_anomaly'),
                         'sign(gap)*(vol_ratio-1): 有符号 gap x 相对量变化, 不预解释为净流入'),
    'overnight_ret_trend': (('overnight_shock',), '(on-on.shift(4))/4: 有方向隔夜收益的变化'),
    'overnight_ret_cross_sectional_rank': (('overnight_shock', 'peer_relative'),
                                           'on.rank(axis=1,pct=True): 原量的截面排序表达'),
    'overnight_ret_surprise': (('overnight_shock', 'self_relative_anomaly'),
                               '_rolling_zscore(on,20)'),
    'overnight_return_ratio_20d': (('overnight_shock',), '隔夜收益占比(20 日)'),
    'daynight_divergence': (('overnight_shock', 'return_path'),
                            '(sign(on)!=sign(in)): 二元, NA 不得当作事件'),
    'agreement_count_5d': (('overnight_shock', 'return_path'),
                           'agreement.rolling(5,min_periods=3).sum(): 【计数】不是比例 -> '
                           '阈值用 <=1 / >=4, 并列有效观察数'),
    'tug_of_war': (('overnight_shock',), 'tw_over - tw_intra: 隔夜/日内相对分量'),
    'tug_of_war_20d': (('overnight_shock',), '上式 20 日均值'),
    'RPV_20d': (('overnight_shock', 'return_path'), 'intra_std_20d - over_std_20d'),
    'JUMP_5': (('overnight_shock',), 'sum(on^2)/(sum(on^2)+sum(in^2)), 5 日; 不是严格跳跃检验'),
    'JUMP_20': (('overnight_shock',), '同上, 20 日'),
    # --- 收益路径 ---
    'intraday_ret': (('return_path', 'price_response_position'),
                     'log(close/open): I11 信号成分之一(分布被截断)'),
    'intraday_ret_consistency_5d': (('return_path',),
                                    'intraday_pos.rolling(5,min_periods=3).mean(): 【比例】-> 0.2/0.8'),
    'positive_day_ratio_5d': (('return_path',),
                              'daily_pos.rolling(5,min_periods=3).mean(): 【比例】-> 0.2/0.8'),
    'cum_return_5d': (('return_path',), 'close/close.shift(5)-1: 【未复权路径】, I11 信号成分'),
    'cum_return_10d': (('return_path',), 'close/close.shift(10)-1: 未复权'),
    'cum_return_20d': (('return_path',), 'close/close.shift(20)-1: 未复权'),
    'cum_intraday_ret_5d': (('return_path',), 'exp(sum log_intra 5)-1'),
    'cum_intraday_ret_10d': (('return_path',), 'exp(sum log_intra 10)-1'),
    'cum_intraday_ret_20d': (('return_path',), 'exp(sum log_intra 20)-1'),
    'reversal_skip1': (('return_path', 'peer_relative'),
                       '源 return -ret_neutral, ret=close.shift(1)/close.shift(11)-1 行业内去均值; '
                       '源值高 = 相对同业过去十日收益低'),
    'max_abs_return_10d': (('return_path',), '|daily_ret|.rolling(10).max()'),
    'realized_vol_20d': (('return_path',), 'daily_ret.rolling(20).std()*sqrt(252): 收盘间波动'),
    'realized_skewness_20d': (('return_path',), 'daily_ret.rolling(20).skew()'),
    'realized_kurtosis_20d': (('return_path',), 'daily_ret.rolling(20).kurt()'),
    'vol_ratio_5d_20d': (('return_path', 'self_relative_anomaly'), 'vol_5d/vol_20d'),
    'parkinson_vol': (('return_path',),
                      '源 return -vol, vol=sqrt(mean (ln(H/L))^2/(4ln2)) 20 日; '
                      '源值高 = 区间波动低 (H==L 置 NaN)'),
    'ou_halflife_60d': (('return_path',), '(-log2/log(b)).clip(0,200): 均值回复半衰期'),
    'info_discreteness_20d': (('return_path',),
                              'sign(cumret20)*(neg_ratio-pos_ratio): 路径离散度'),
    # --- 资金流代理 ---
    'CMF_20d': (('flow_price_proxy',),
                'cmf_num/cmf_den: I11 已用(pct>=0.80 截断); 提新需求才另路由, 不改 I11'),
    'cmf_change_neg': (('flow_price_proxy',),
                       'spec lambda = -compute_cmf_change(window_long=10,window_short=5)'),
    'drawdown_volume_ratio': (('flow_price_proxy', 'activity_level'),
                              '(down_vol/down_days)/(up_vol/up_days)'),
    # --- 流动性成本 ---
    'amihud_daily': (('liquidity_cost',),
                     '|daily_ret|/(amount*1e-6): 分母是【百万元】口径; 停牌/一字板另核'),
    'amihud_asymmetry_20d': (('liquidity_cost',), '上下行 amihud 的不对称'),
    # --- 同业/占位 ---
    'gap_vs_sector': (('peer_relative', 'overnight_shock'),
                      'gap.sub(gap_mean,axis=0): 源实为【全市场】去均值占位, 不是行业信息'),
    'gap_rank_in_sector': (('peer_relative', 'overnight_shock'),
                           'gap.rank(axis=1,pct=True): 源实为【全市场】rank 占位, 不冒充行业内 rank'),
    'IND_CUR_5': (('peer_relative',), 'T 时可见 PIT 同业(剔自身)5 日复权端点收益等权均值'),
    'IND_CUR_20': (('peer_relative',), '同上, 20 日'),
    'IND_ROLL_5': (('peer_relative',), '逐历史日 PIT 归属聚合当日同业收益再滚动 5 日'),
    'IND_ROLL_20': (('peer_relative',), '同上, 20 日'),
    'REL_IND_5': (('peer_relative', 'return_path'), 'OWN_RET_5 - IND_CUR_5'),
    'REL_IND_20': (('peer_relative', 'return_path'), 'OWN_RET_20 - IND_CUR_20'),
    'OWN_RET_5': (('return_path',), 'close_adj[T]/close_adj[T-5]-1: 【已复权】, 与 cum_return_5d 不同'),
    'OWN_RET_20': (('return_path',), 'close_adj[T]/close_adj[T-20]-1: 【已复权】'),
    # --- 诊断规模 ---
    'mcap_rank': (('diagnostic_scale',), 'mcap.rank(axis=1,pct=True): 诊断/混杂控制, 本轮不进交易评分'),
}

# 源符号: 源函数返回值是否已取负
NEGATED = {'abn_turnover': '-(MA20/MA120)',
           'parkinson_vol': '-sqrt(mean (ln(H/L))^2/(4 ln 2))',
           'reversal_skip1': '-(行业内去均值的 skip-1 十日收益)',
           'cmf_change_neg': '-compute_cmf_change(window_long=10, window_short=5)'}

# 源值【高】在经济上意味着什么 (四个负号键必须反读; 其余按公式)
ECON_HIGH = {
    'abn_turnover': '换手相对自身 120 日历史更【低】(更安静)',
    'parkinson_vol': '日内高低区间波动更【低】(区间更窄)',
    'reversal_skip1': '相对同业的过去十日收益更【低】(相对回落)',
    'cmf_change_neg': '资金流变化更【负】',
}

UNADJUSTED_PRICE_PATH = {'cum_return_5d', 'cum_return_10d', 'cum_return_20d',
                         'recent_high_20d', 'distance_from_high_20d', 'days_since_high',
                         'volume_momentum_divergence'}


# 源里是多行表达式, 正则抽不到, 逐条手抄 (已对源码行号核过)
FORMULA_OVERRIDE = {
    'amihud_asymmetry_20d': ('amihud_down.rolling(20, min_periods=5).mean() - '
                             'amihud_up.rolling(20, min_periods=5).mean()  [源 :557]'),
    'overnight_return_ratio_20d': ('(cum_overnight_20d / cum_total_20d.replace(0, np.nan))'
                                   '.clip(-2, 2)  [源 :484] —— 【被 clip 到 ±2】, '
                                   '在两端造平局, k 分位否决时须看 tie 诊断'),
}


def source_lines():
    src = inspect.getsource(FD).split('\n')
    out = {}
    for i, l in enumerate(src):
        m = re.match(r"\s*features\[['\"]([A-Za-z0-9_]+)['\"]\]\s*=\s*(.+)$", l)
        if m and m.group(1) not in out:
            out[m.group(1)] = (i + 1, m.group(2).strip())
    return out


def win_minp(formula):
    m = re.search(r'rolling\(\s*(\d+)\s*(?:,\s*min_periods\s*=\s*(\d+))?', formula or '')
    if not m:
        m2 = re.search(r'_rolling_(?:zscore|percentile|corr)\([^,]+,\s*(\d+)', formula or '')
        return (int(m2.group(1)), None) if m2 else (None, None)
    return int(m.group(1)), (int(m.group(2)) if m.group(2) else None)


def main():
    os.makedirs(os.path.join(RES, 'registry'), exist_ok=True)
    base = pd.read_csv(os.path.join(H.E6G_DIR, 'registry', 'key_registry.csv'))
    sl = source_lines()

    rows = []
    for k in sorted(H.REGISTERED):
        is_new = k in H.DERIVED
        b = base[base['key'] == k]
        b = b.iloc[0].to_dict() if len(b) else {}
        ln, formula = sl.get(k, (None, None))
        if is_new:
            sp = H.DERIVED_SPECS[k]
            formula = sp['econ']
            ln = None
            w, mp = sp['w'], sp['minv']
            raw_fields = '|'.join(sp['src'])
            src_file = 'e6h_core.py'
        else:
            if k in FORMULA_OVERRIDE:
                formula = FORMULA_OVERRIDE[k]
            w, mp = win_minp(formula)
            raw_fields = ''
            src_file = b.get('source_file', '')
        tax, basis = TAX.get(k, ((), ''))
        rows.append(dict(
            key=k,
            key_class=('E6H_DERIVED' if is_new else b.get('key_class', '')),
            registered_in=('e6h' if is_new else 'e6g'),
            protected=H.is_protected_key(k),
            new40_blood=(False if is_new else bool(b.get('new40_blood', False))),
            source_file=src_file,
            source_func=b.get('source_func', 'e6h_core' if is_new else ''),
            source_line=(ln if ln else b.get('source_line', '')),
            formula=formula or b.get('source_snippet', '')[:160],
            raw_fields=raw_fields,
            window=w, min_periods=mp,
            source_sign=('negated' if k in NEGATED else 'as_is'),
            source_sign_detail=NEGATED.get(k, ''),
            economic_quantity=(H.DERIVED_SPECS[k]['econ'] if is_new else basis),
            economic_direction_of_high_source=ECON_HIGH.get(
                k, '按公式直读 (源值未取负)'),
            value_used_for_pct='source_value',
            pct_direction_default='hi',
            price_adjusted=('yes' if (is_new and k.startswith(('OWN_RET', 'IND_', 'REL_IND')))
                            else ('no_close_shift_path' if k in UNADJUSTED_PRICE_PATH
                                  else 'see_e6g_adj_cols')),
            measurement_families='|'.join(tax),
            taxonomy_basis=basis,
            exact_alias=b.get('formula_alias', ''),
            market_wide_placeholder=bool(b.get('market_wide_placeholder', False)),
            signal_overlap=bool(b.get('signal_overlap', False)),
            diagnostic_only=bool(b.get('diagnostic_only', False)),
            tie_frac_raw=b.get('tie_frac_raw', np.nan),
            missing_rate=b.get('missing_rate', np.nan),
            price_adj_measured_change=b.get('price_adj_measured_change', ''),
            volume_dependent_untested=b.get('volume_dependent_untested', ''),
            allowed_segments=('|'.join(H.DERIV_SEGS) if H.is_protected_key(k)
                              else b.get('allowed_segments', '|'.join(H.SEGMENTS))),
            label_end_max=(H.PROTECTED_LABEL_END if H.is_protected_key(k)
                           else b.get('label_end_max', H.MARKET_DATA_END_MAX)),
            previous_looks=b.get('access_history_label', 'none_e6h_new' if is_new else ''),
            previous_looks_evidence=b.get('access_history_evidence', ''),
        ))
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(RES, 'registry', 'feature_semantics.csv'), index=False)

    # taxonomy 长表 (多标签展开)
    tx = []
    for _, r in d.iterrows():
        fams = [f for f in str(r['measurement_families']).split('|') if f]
        for f in fams:
            tx.append(dict(key=r['key'], family=f, family_desc=FAMILIES.get(f, ''),
                           basis=r['taxonomy_basis'], protected=r['protected'],
                           key_class=r['key_class']))
    t = pd.DataFrame(tx)
    t.to_csv(os.path.join(RES, 'registry', 'feature_taxonomy.csv'), index=False)

    print('== feature_semantics / feature_taxonomy ==')
    print(' 键 %d (U74 %d + 派生 %d); 受保护 %d'
          % (len(d), len(H.U74), len(H.DERIVED), int(d['protected'].sum())))
    miss = d[d['measurement_families'] == '']
    print(' 未分类的键: %d %s' % (len(miss), list(miss['key']) if len(miss) else ''))
    nof = d[(d['formula'].astype(str).str.len() < 3)]
    print(' 无公式的键: %d %s' % (len(nof), list(nof['key']) if len(nof) else ''))
    print()
    print(' 多标签分布 (一个键可属多族):')
    vc = t['family'].value_counts()
    for f, n in vc.items():
        print('   %-26s %2d  %s' % (f, n, FAMILIES.get(f, '')))
    print(' 标签数分布: %s' % d['measurement_families'].str.count(r'\|').add(1).value_counts().to_dict())
    print()
    print(' 源符号取负的键: %s' % sorted(NEGATED))
    print(' 全市场占位 (不能当行业信息): %s' % sorted(d[d['market_wide_placeholder']]['key']))
    print(' 与 I11 信号重叠: %s' % sorted(d[d['signal_overlap']]['key']))


if __name__ == '__main__':
    main()
