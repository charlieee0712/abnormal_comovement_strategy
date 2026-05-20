"""
Daily特征计算模块
==================
数据源: alpha基础数据日线 (/mnt/big/base/shibo/KLines_make/daily_temp3/)
辅助:   FundamentalTL (/mnt/big/base/public/FundamentalTL/)

字段:
    open, close, high, low, lclose, vwap
    volume, amount, turnover_rate
    mcap, is_open, adj_factor

特征分组:
    B1.2  隔夜跳空异常 (10个)
    B1.4  昼夜结构 (9个)
    B1.X  背景状态 (12个)
    B2.1  基础量能 (6个)
    B2.2  量变加速度 (3个)
    B2.3  regime变点 (4个)
    B2.8  流动性 (2个)
    B2.13 截面排名 (3个)
    B3.1  创新特征 (13个) - 基于研究报告
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional


# ============================================================
# 数据加载
# ============================================================

def load_daily_data_offline(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    离线模式: 直接传入已有的数据字典.
    用于测试或已经从别处加载了数据的场景.
    实际数据加载请使用 data_loader.py 中的 load_all_daily_data().
    """
    return data_dict


# ============================================================
# 辅助函数
# ============================================================

def _rolling_zscore(x: pd.DataFrame, window: int) -> pd.DataFrame:
    """时序滚动z-score."""
    mu = x.rolling(window, min_periods=window // 2).mean()
    sigma = x.rolling(window, min_periods=window // 2).std()
    return (x - mu) / sigma.replace(0, np.nan)


def _rolling_percentile(x: pd.DataFrame, window: int) -> pd.DataFrame:
    """时序滚动分位数."""
    return x.rolling(window, min_periods=window // 2).rank(pct=True)


# ============================================================
# B1.2 隔夜跳空异常 (10个特征)
# ============================================================

def calc_b12_gap_features(data: dict) -> Dict[str, pd.DataFrame]:
    """
    B1.2 隔夜跳空异常 — 10个特征.

    gap = (open - lclose) / lclose
    """
    open_p = data['open'].replace(0, np.nan)
    lclose = data['lclose'].replace(0, np.nan)
    close = data['close'].replace(0, np.nan)
    volume = data['volume']

    # 基础gap (lclose=0时自动变NaN)
    gap = (open_p - lclose) / lclose

    features = {}

    # 1. gap_zscore_20d: 今日gap在20日分布的z-score
    features['gap_zscore_20d'] = _rolling_zscore(gap, 20)

    # 2. gap_abs_zscore_20d: |gap|的z-score
    features['gap_abs_zscore_20d'] = _rolling_zscore(gap.abs(), 20)

    # 3. gap_percentile_60d: |gap|在60日分布的分位数
    features['gap_percentile_60d'] = _rolling_percentile(gap.abs(), 60)

    # 4. gap_vs_sector: 个股gap - 截面均值 (先用全市场均值代替, 后续接概念映射)
    gap_mean = gap.mean(axis=1)
    features['gap_vs_sector'] = gap.sub(gap_mean, axis=0)

    # 5. gap_rank_in_sector: 截面rank分位 (全市场版)
    features['gap_rank_in_sector'] = gap.rank(axis=1, pct=True)

    # 6. consecutive_gap_same_direction: 连续同向gap天数
    gap_sign = np.sign(gap)
    direction_change = (gap_sign != gap_sign.shift(1)).astype(int)
    # 对每列用cumsum分组+cumcount
    def _count_consecutive(col):
        groups = direction_change[col.name].cumsum()
        return col.groupby(groups).cumcount() + 1
    features['consecutive_gap_same_direction'] = gap_sign.apply(_count_consecutive)

    # 7. gap_direction_consistency_5d: 过去5日gap方向一致性
    gap_pos = (gap > 0).astype(float)
    features['gap_direction_consistency_5d'] = gap_pos.rolling(5, min_periods=3).mean()

    # 8. gap_trend_5d: 过去5日|gap|的线性趋势斜率
    abs_gap = gap.abs()
    # 简化: 用最后一天减第一天除以天数
    features['gap_trend_5d'] = (abs_gap - abs_gap.shift(4)) / 4

    # 9. gap_survival_ratio: (close - lclose) / (open - lclose)
    #    衡量gap是否存活到收盘
    gap_raw = open_p - lclose
    total_change = close - lclose
    features['gap_survival_ratio'] = total_change / gap_raw.replace(0, np.nan)

    # 10. gap_volume_ratio: gap方向 × (竞价量放大倍数 - 1)
    #     简化版: sign(gap) × (volume / volume_20d_mean - 1)
    vol_ratio = volume / volume.rolling(20, min_periods=10).mean()
    features['gap_volume_ratio'] = np.sign(gap) * (vol_ratio - 1)

    return features


# ============================================================
# B1.4 昼夜结构 (9个特征)
# ============================================================

def calc_b14_daynight_features(data: dict) -> Dict[str, pd.DataFrame]:
    """
    B1.4 昼夜结构 — 9个特征.

    隔夜收益 = ln(open/lclose)
    日内收益 = ln(close/open)
    """
    open_p = data['open'].replace(0, np.nan)
    close = data['close'].replace(0, np.nan)
    lclose = data['lclose'].replace(0, np.nan)

    overnight_ret = np.log(open_p / lclose)
    intraday_ret = np.log(close / open_p)

    # 清理inf (来自除零或log(0))
    overnight_ret = overnight_ret.replace([np.inf, -np.inf], np.nan)
    intraday_ret = intraday_ret.replace([np.inf, -np.inf], np.nan)

    features = {}

    # 1. overnight_ret
    features['overnight_ret'] = overnight_ret

    # 2. intraday_ret
    features['intraday_ret'] = intraday_ret

    # 3. daynight_divergence: 隔夜和日内方向背离 (1=背离)
    features['daynight_divergence'] = (np.sign(overnight_ret) != np.sign(intraday_ret)).astype(float)

    # 4. agreement_count_5d: 过去5天"高开高走"(隔夜正+日内正)天数
    agreement = ((overnight_ret > 0) & (intraday_ret > 0)).astype(float)
    features['agreement_count_5d'] = agreement.rolling(5, min_periods=3).sum()

    # 5. overnight_ret_surprise: 隔夜收益 - 20日均值 (z-score)
    features['overnight_ret_surprise'] = _rolling_zscore(overnight_ret, 20)

    # 6. overnight_ret_cross_sectional_rank: 隔夜收益全市场排名分位
    features['overnight_ret_cross_sectional_rank'] = overnight_ret.rank(axis=1, pct=True)

    # 7. overnight_ret_trend: 隔夜收益5日OLS斜率 (简化版)
    features['overnight_ret_trend'] = (overnight_ret - overnight_ret.shift(4)) / 4

    # 8. intraday_ret_consistency_5d: 过去5天日内正收益占比
    intraday_pos = (intraday_ret > 0).astype(float)
    features['intraday_ret_consistency_5d'] = intraday_pos.rolling(5, min_periods=3).mean()

    # 9. positive_day_ratio_5d: 过去5天收阳占比
    daily_ret = np.log(close / lclose).replace([np.inf, -np.inf], np.nan)
    daily_pos = (daily_ret > 0).astype(float)
    features['positive_day_ratio_5d'] = daily_pos.rolling(5, min_periods=3).mean()

    return features


# ============================================================
# B1.X 背景状态 (12个特征)
# ============================================================

def calc_b1x_background_features(data: dict) -> Dict[str, pd.DataFrame]:
    """
    B1.X 背景状态 — 12个特征.
    """
    close = data['close'].replace(0, np.nan)
    lclose = data['lclose'].replace(0, np.nan)
    high = data['high']
    low = data['low']
    volume = data['volume']

    features = {}

    # 日收益率 (直接从价格计算, 不依赖change_rate字段)
    daily_ret = np.log(close / lclose)
    daily_ret = daily_ret.replace([np.inf, -np.inf], np.nan)

    # 1. realized_vol_20d: 20日已实现波动率
    features['realized_vol_20d'] = daily_ret.rolling(20, min_periods=10).std() * np.sqrt(252)

    # 2. vol_ratio_5d_20d: 短/长波动比
    vol_5d = daily_ret.rolling(5, min_periods=3).std()
    vol_20d = daily_ret.rolling(20, min_periods=10).std()
    features['vol_ratio_5d_20d'] = vol_5d / vol_20d.replace(0, np.nan)

    # 3. realized_skewness_20d: 20日已实现偏度
    features['realized_skewness_20d'] = daily_ret.rolling(20, min_periods=10).skew()

    # 4. realized_kurtosis_20d: 20日已实现峰度
    features['realized_kurtosis_20d'] = daily_ret.rolling(20, min_periods=10).kurt()

    # 5. max_abs_return_10d: 近10日最大|单日收益|
    features['max_abs_return_10d'] = daily_ret.abs().rolling(10, min_periods=5).max()

    # 6. cum_return_5d: 5日累计收益
    features['cum_return_5d'] = close / close.shift(5) - 1

    # 7. cum_return_10d: 10日累计收益
    features['cum_return_10d'] = close / close.shift(10) - 1

    # 8. cum_return_20d: 20日累计收益
    features['cum_return_20d'] = close / close.shift(20) - 1

    # 9. recent_high_20d: 过去20日最高收盘价
    features['recent_high_20d'] = close.rolling(20, min_periods=10).max()

    # 10. distance_from_high_20d: 距20日新高的回撤幅度
    features['distance_from_high_20d'] = close / features['recent_high_20d'] - 1

    # 11. days_since_high: 距20日新高天数
    rolling_max = close.rolling(20, min_periods=10).max()
    is_at_high = (close >= rolling_max).astype(float)
    def _count_since_high(col):
        groups = is_at_high[col.name].cumsum()
        return col.groupby(groups).cumcount()
    features['days_since_high'] = close.apply(_count_since_high)

    # 12. drawdown_volume_ratio: 回撤日均量/上涨日均量
    is_down_day = (daily_ret < 0).astype(float)
    is_up_day = (daily_ret > 0).astype(float)
    down_vol = (volume * is_down_day).rolling(20, min_periods=5).sum()
    down_days = is_down_day.rolling(20, min_periods=5).sum().replace(0, np.nan)
    up_vol = (volume * is_up_day).rolling(20, min_periods=5).sum()
    up_days = is_up_day.rolling(20, min_periods=5).sum().replace(0, np.nan)
    features['drawdown_volume_ratio'] = (down_vol / down_days) / (up_vol / up_days).replace(0, np.nan)

    return features


# ============================================================
# B2.1 基础量能 (6个特征)
# ============================================================

def calc_b21_volume_features(data: dict) -> Dict[str, pd.DataFrame]:
    """
    B2.1 基础量能 — 6个特征.
    """
    volume = data['volume']
    amount = data['amount']
    turnover_rate = data['turnover_rate']

    features = {}

    # 1. volume_ratio_1d: 当日量/20日均量
    vol_ma20 = volume.rolling(20, min_periods=10).mean()
    features['volume_ratio_1d'] = volume / vol_ma20.replace(0, np.nan)

    # 2. volume_ratio_3d: 3日均量/20日均量
    vol_ma3 = volume.rolling(3, min_periods=2).mean()
    features['volume_ratio_3d'] = vol_ma3 / vol_ma20.replace(0, np.nan)

    # 3. volume_ratio_5d: 5日均量/20日均量
    vol_ma5 = volume.rolling(5, min_periods=3).mean()
    features['volume_ratio_5d'] = vol_ma5 / vol_ma20.replace(0, np.nan)

    # 4. volume_zscore_60d: 成交量在60日分布的z-score
    features['volume_zscore_60d'] = _rolling_zscore(volume, 60)

    # 5. turnover_5d: 5日平均换手率
    features['turnover_5d'] = turnover_rate.rolling(5, min_periods=3).mean()

    # 6. amount_ratio_1d: 当日成交额/20日均额
    amt_ma20 = amount.rolling(20, min_periods=10).mean()
    features['amount_ratio_1d'] = amount / amt_ma20.replace(0, np.nan)

    return features


# ============================================================
# B2.2 量变加速度 (3个特征)
# ============================================================

def calc_b22_volume_accel_features(data: dict) -> Dict[str, pd.DataFrame]:
    """
    B2.2 量变加速度 — 3个特征.
    """
    volume = data['volume']

    features = {}

    vol_ma5 = volume.rolling(5, min_periods=3).mean()
    vol_ma10 = volume.rolling(10, min_periods=5).mean()
    vol_ma20 = volume.rolling(20, min_periods=10).mean()

    # 1. volume_accel_3d: 3日成交量加速度 (二阶差分)
    features['volume_accel_3d'] = volume.diff().diff()

    # 2. volume_trend_10d: 10日量趋势 (线性斜率简化)
    features['volume_trend_10d'] = (vol_ma5 - vol_ma10) / vol_ma10.replace(0, np.nan)

    # 3. volume_momentum_divergence: 量价动量背离
    #    价格上涨但量能萎缩 = 负信号
    close = data['close']
    price_mom = close / close.shift(5) - 1
    vol_mom = vol_ma5 / vol_ma20.replace(0, np.nan) - 1
    features['volume_momentum_divergence'] = vol_mom - price_mom

    return features


# ============================================================
# B2.3 regime变点 (4个特征, 不含BOCPD需在线估计的)
# ============================================================

def calc_b23_regime_features(data: dict) -> Dict[str, pd.DataFrame]:
    """
    B2.3 regime变点 — 4个特征.
    """
    volume = data['volume']
    close = data['close'].replace(0, np.nan)
    lclose = data['lclose'].replace(0, np.nan)
    high = data['high']
    low = data['low']
    amount = data['amount']

    features = {}

    # 1. stealth_score: 隐蔽交易得分 = 量放大倍数 / 振幅放大倍数
    vol_ratio = volume / volume.rolling(20, min_periods=10).mean().replace(0, np.nan)
    range_daily = (high - low) / close
    range_ratio = range_daily / range_daily.rolling(20, min_periods=10).mean().replace(0, np.nan)
    features['stealth_score'] = vol_ratio / range_ratio.replace(0, np.nan)

    # 2. conditional_turnover: 条件换手率 = TR / (|r| + ε)
    daily_ret = np.log(close / lclose).replace([np.inf, -np.inf], np.nan)
    turnover_rate = data['turnover_rate']
    features['conditional_turnover'] = turnover_rate / (daily_ret.abs() + 0.0001)

    # 3. volume_regime_break: 成交量突破20日最高量 (0/1)
    vol_max_20d = volume.rolling(20, min_periods=10).max()
    features['volume_regime_break'] = (volume >= vol_max_20d).astype(float)

    # 4. amount_concentration_5d: 5日成交额占20日总额比例
    amt_5d = amount.rolling(5, min_periods=3).sum()
    amt_20d = amount.rolling(20, min_periods=10).sum()
    features['amount_concentration_5d'] = amt_5d / amt_20d.replace(0, np.nan)

    return features


# ============================================================
# B2.8 流动性 (2个特征)
# ============================================================

def calc_b28_liquidity_features(data: dict) -> Dict[str, pd.DataFrame]:
    """
    B2.8 流动性 — 2个特征.
    """
    close = data['close'].replace(0, np.nan)
    lclose = data['lclose'].replace(0, np.nan)
    amount = data['amount']

    daily_ret = np.log(close / lclose).replace([np.inf, -np.inf], np.nan)

    features = {}

    # 1. amihud_daily: Amihud非流动性 = |r| / (amount × 10^-6)
    features['amihud_daily'] = daily_ret.abs() / (amount * 1e-6).replace(0, np.nan)

    # 2. amihud_ratio_5d_20d: Amihud短长期比
    amihud = features['amihud_daily']
    amihud_5d = amihud.rolling(5, min_periods=3).mean()
    amihud_20d = amihud.rolling(20, min_periods=10).mean()
    features['amihud_ratio_5d_20d'] = amihud_5d / amihud_20d.replace(0, np.nan)

    return features


# ============================================================
# B2.13 截面排名 (3个特征)
# ============================================================

def calc_b213_crosssection_features(data: dict) -> Dict[str, pd.DataFrame]:
    """
    B2.13 截面排名 — 3个特征.
    """
    volume = data['volume']
    turnover_rate = data['turnover_rate']
    mcap = data['mcap']

    features = {}

    # 1. volume_rank_market: 全市场成交量排名分位
    features['volume_rank_market'] = volume.rank(axis=1, pct=True)

    # 2. turnover_rank_market: 全市场换手率排名分位
    features['turnover_rank_market'] = turnover_rate.rank(axis=1, pct=True)

    # 3. mcap_rank: 市值排名分位
    features['mcap_rank'] = mcap.rank(axis=1, pct=True)

    return features


# ============================================================
# 主函数: 计算全部49个daily特征
# ============================================================

def calc_b31_innovation_features(data: dict) -> Dict[str, pd.DataFrame]:
    """
    B3.1 创新特征 (基于研究报告)
    ============================
    新增21个特征, 重点解决VWAP执行下"高开吃alpha"问题.
    
    特征来源:
    - cum_intraday_ret_5d/10d/20d: A2 IMOM (Lou,Polk,Skouras 2019)
    - overnight_return_ratio_20d: A2/A4 隔夜收益占比
    - info_discreteness_20d: A1 FIP (Da,Gurun,Warachka 2014)
    - CLV / CLV_20d: D2 聪明钱代理 (Close Location Value)
    - CMF_20d: D4 Chaikin Money Flow
    - shadow_asymmetry / shadow_asymmetry_20d: D5 K线影线不对称
    - tug_of_war / tug_of_war_20d: B3 隔夜vs日内角力
    - amihud_asymmetry_20d: D3 非对称价格冲击
    - CVR / CVR_5d / CVR_20d: A3 尾盘强度 (机构吸筹)
    - CCV_20d: D1 价量相关性 (RPV简化版)
    - turnover_volatility_60d: B3 散户情绪波动
    - RPV_20d: D1 日内vs隔夜波动差 (东吴高子剑近似版)
    - ou_halflife_60d: B5 OU模型半衰期 (均值回归速度)
    - inside_bar_freq_20d: D5 缩量内包K线频率 (波动压缩)
    
    注: fscore需要基本面数据, 当前未实现.
    """
    features = {}
    
    open_p = data['open'].astype(float)
    close = data['close'].astype(float)
    high = data['high'].astype(float)
    low = data['low'].astype(float)
    lclose = data['lclose'].astype(float)
    volume = data['volume'].astype(float)
    amount = data['amount'].astype(float)
    
    # ---- 基础日收益分解 ----
    # 日内收益 = Close/Open - 1 (你的实际盈利段)
    intraday_ret = (close / open_p.replace(0, np.nan) - 1).replace([np.inf, -np.inf], np.nan)
    # 隔夜收益 = Open/lclose - 1
    overnight_ret = (open_p / lclose.replace(0, np.nan) - 1).replace([np.inf, -np.inf], np.nan)
    # 全天收益
    daily_ret = (close / lclose.replace(0, np.nan) - 1).replace([np.inf, -np.inf], np.nan)
    
    # ============================================================
    # A2: 日内动量 (IMOM) - 最重要的创新特征
    # ============================================================
    # 累积日内收益 (忽略隔夜跳空)
    # 用 sum(log(1+r)) 累积, 等价于 prod(1+r) - 1
    log_intra = np.log(1 + intraday_ret.fillna(0))
    features['cum_intraday_ret_5d'] = np.exp(log_intra.rolling(5, min_periods=3).sum()) - 1
    features['cum_intraday_ret_10d'] = np.exp(log_intra.rolling(10, min_periods=5).sum()) - 1
    features['cum_intraday_ret_20d'] = np.exp(log_intra.rolling(20, min_periods=10).sum()) - 1
    
    # ============================================================
    # A2/A4: 隔夜收益占比 - 越高说明动量越依赖隔夜跳空, 应惩罚
    # ============================================================
    log_over = np.log(1 + overnight_ret.fillna(0))
    cum_overnight_20d = np.exp(log_over.rolling(20, min_periods=10).sum()) - 1
    cum_total_20d = (close / close.shift(20) - 1)
    # 比例 = 隔夜累积/全天累积, 范围在(-inf,+inf), winsorize到[-2,2]
    features['overnight_return_ratio_20d'] = (
        cum_overnight_20d / cum_total_20d.replace(0, np.nan)
    ).clip(-2, 2)
    
    # ============================================================
    # A1: FIP 信息离散度 - 区分连续型 vs 跳跃型动量
    # ============================================================
    # ID = sign(cumret) * (负收益天数% - 正收益天数%)
    # 连续上涨型: cumret>0且大部分日为正, ID极负
    # 跳跃型: 由少数大涨日驱动, ID接近0或正
    pos_days = (daily_ret > 0).astype(float)
    neg_days = (daily_ret < 0).astype(float)
    pos_ratio_20d = pos_days.rolling(20, min_periods=10).mean()
    neg_ratio_20d = neg_days.rolling(20, min_periods=10).mean()
    cumret_20d = close / close.shift(20) - 1
    features['info_discreteness_20d'] = np.sign(cumret_20d) * (neg_ratio_20d - pos_ratio_20d)
    
    # ============================================================
    # D2: CLV (Close Location Value) - 聪明钱代理
    # ============================================================
    # CLV = [(Close-Low) - (High-Close)] / (High-Low)
    # = (2*Close - High - Low) / (High - Low)
    # 范围[-1, 1], +1表示收盘在最高(尾盘买压), -1表示收盘在最低(尾盘卖压)
    hl_range = (high - low).replace(0, np.nan)
    clv = (2 * close - high - low) / hl_range
    features['CLV'] = clv
    features['CLV_20d'] = clv.rolling(20, min_periods=10).mean()
    
    # ============================================================
    # D4: Chaikin Money Flow (订单流方向代理)
    # ============================================================
    # CMF = sum(CLV * Volume) / sum(Volume)
    cmf_num = (clv * volume).rolling(20, min_periods=10).sum()
    cmf_den = volume.rolling(20, min_periods=10).sum().replace(0, np.nan)
    features['CMF_20d'] = cmf_num / cmf_den
    
    # ============================================================
    # D5: K线影线不对称
    # ============================================================
    # 上影线比率 = (High - max(Open,Close)) / (High-Low)
    # 下影线比率 = (min(Open,Close) - Low) / (High-Low)
    # 影线不对称 = USR - LSR, 正值=上影长(抛压), 负值=下影长(支撑)
    body_high = pd.concat([open_p, close]).groupby(level=0).max()
    body_low = pd.concat([open_p, close]).groupby(level=0).min()
    # 用element-wise方式
    body_high = open_p.where(open_p > close, close)
    body_low = open_p.where(open_p < close, close)
    upper_shadow = (high - body_high) / hl_range
    lower_shadow = (body_low - low) / hl_range
    features['shadow_asymmetry'] = upper_shadow - lower_shadow
    features['shadow_asymmetry_20d'] = features['shadow_asymmetry'].rolling(20, min_periods=10).mean()
    
    # ============================================================
    # B3: Tug of War - 隔夜vs日内角力
    # ============================================================
    # TW = (overnight_ret/σ_over)² - (intraday_ret/σ_intra)²
    # 极负: 日内抛压远大于隔夜买盘 (反转最强)
    # 极正: 隔夜买盘远大于日内抛压 (动量延续概率高)
    sigma_over = overnight_ret.rolling(20, min_periods=10).std().replace(0, np.nan)
    sigma_intra = intraday_ret.rolling(20, min_periods=10).std().replace(0, np.nan)
    tw_over = (overnight_ret / sigma_over) ** 2
    tw_intra = (intraday_ret / sigma_intra) ** 2
    features['tug_of_war'] = tw_over - tw_intra
    features['tug_of_war_20d'] = features['tug_of_war'].rolling(20, min_periods=10).mean()
    
    # ============================================================
    # D3: 非对称Amihud流动性
    # ============================================================
    # 跌日Amihud均值 - 涨日Amihud均值
    # 正值: 跌时冲击大于涨时 (信息型卖压, 应回避)
    amihud = (daily_ret.abs() / (amount * 1e-6).replace(0, np.nan))
    amihud_down = amihud.where(daily_ret < 0)
    amihud_up = amihud.where(daily_ret > 0)
    features['amihud_asymmetry_20d'] = (
        amihud_down.rolling(20, min_periods=5).mean() -
        amihud_up.rolling(20, min_periods=5).mean()
    )
    
    # ============================================================
    # A3: CVR (Close vs VWAP Ratio) - 尾盘强度
    # ============================================================
    # CVR = (Close - VWAP) / VWAP
    # CVR>0: 收盘价高于VWAP, 尾盘买盘强 (机构吸筹信号)
    # CVR<0: 收盘价低于VWAP, 尾盘卖压强
    vwap = data['vwap'].astype(float)
    cvr = (close - vwap) / vwap.replace(0, np.nan)
    cvr = cvr.replace([np.inf, -np.inf], np.nan)
    features['CVR'] = cvr
    features['CVR_5d'] = cvr.rolling(5, min_periods=3).mean()
    features['CVR_20d'] = cvr.rolling(20, min_periods=10).mean()
    
    # ============================================================
    # D1: CCV (Close-Volume Correlation) - 价量相关性 (RPV简化版)
    # ============================================================
    # 20日滚动: Corr(Close序列, Turnover序列)
    # 正相关: 量增价涨, 健康趋势
    # 负相关: 量价背离, 警惕
    if 'turnover_rate' in data:
        turn = data['turnover_rate'].astype(float)
    else:
        turn = (volume / (data.get('mcap', volume * 0 + 1).astype(float))).replace([np.inf, -np.inf], np.nan)
    
    # 滚动Corr的高效实现: 用rolling.corr
    def _rolling_corr(x, y, window):
        # x, y are DataFrames with same index/columns
        # Compute rolling correlation column by column
        # Faster way: use rolling means and stds
        x_mean = x.rolling(window, min_periods=window//2).mean()
        y_mean = y.rolling(window, min_periods=window//2).mean()
        x_std = x.rolling(window, min_periods=window//2).std()
        y_std = y.rolling(window, min_periods=window//2).std()
        cov = (x * y).rolling(window, min_periods=window//2).mean() - x_mean * y_mean
        denom = (x_std * y_std).replace(0, np.nan)
        return cov / denom
    
    features['CCV_20d'] = _rolling_corr(close, turn, 20)
    
    # ============================================================
    # B3 (extra): 换手率波动 - 散户情绪波动代理
    # ============================================================
    # 60日换手率标准差: 高=散户情绪剧烈波动 (反转信号增强)
    features['turnover_volatility_60d'] = turn.rolling(60, min_periods=30).std()
    
    # ============================================================
    # D1 (extra): RPV - 价量相关性日频近似 (东吴高子剑)
    # ============================================================
    # 完整RPV需要分钟数据(CCOIV vs COV分量), 这里用日频近似:
    # RPV = std(intraday_ret) - std(overnight_ret), 20日滚动
    # 正值: 日内波动主导(反转特征强), 负值: 隔夜波动主导(动量特征强)
    # 与CCV互补: CCV看相关方向, RPV看波动来源
    intra_std_20d = intraday_ret.rolling(20, min_periods=10).std()
    over_std_20d = overnight_ret.rolling(20, min_periods=10).std()
    features['RPV_20d'] = intra_std_20d - over_std_20d
    
    # ============================================================
    # B5: OU模型半衰期 (均值回归速度)
    # ============================================================
    # 用log价格对其滞后值做OLS: log(P_t) = a + b * log(P_{t-1})
    # 半衰期 = -log(2) / log(b) (当b<1时)
    # b接近1: 半衰期长(趋势型, 不回归)
    # b小: 半衰期短(强均值回归)
    # 用60日滚动估计
    log_close = np.log(close.replace(0, np.nan))
    log_close_lag = log_close.shift(1)
    
    # 滚动OLS的高效实现: 用滚动协方差/方差
    # b = Cov(y, x) / Var(x) (这里 y=log_close, x=log_close_lag)
    window = 60
    minp = 30
    x_mean = log_close_lag.rolling(window, min_periods=minp).mean()
    y_mean = log_close.rolling(window, min_periods=minp).mean()
    xy_mean = (log_close_lag * log_close).rolling(window, min_periods=minp).mean()
    xx_mean = (log_close_lag * log_close_lag).rolling(window, min_periods=minp).mean()
    cov_xy = xy_mean - x_mean * y_mean
    var_x = xx_mean - x_mean * x_mean
    b = cov_xy / var_x.replace(0, np.nan)
    # 限制b到合理范围(避免log(b<=0)报错), 然后算半衰期
    b_clipped = b.where((b > 0) & (b < 1), np.nan)
    features['ou_halflife_60d'] = (-np.log(2) / np.log(b_clipped)).clip(0, 200)
    
    # ============================================================
    # D5 (extra): 内包K线频率 (Inside Bar - 波动压缩信号)
    # ============================================================
    # 内包K线: 当日最高<前日最高 AND 当日最低>前日最低
    # 表示当日波动被前日完全包含, 是波动压缩信号, 常预示突破
    # 缩量内包: 内包 + 当日量 < 5日均量 (压缩更彻底)
    high_lag = high.shift(1)
    low_lag = low.shift(1)
    is_inside = ((high < high_lag) & (low > low_lag)).astype(float)
    
    # 缩量条件
    vol_ma5 = volume.rolling(5, min_periods=3).mean()
    is_low_vol = (volume < vol_ma5).astype(float)
    is_inside_low_vol = is_inside * is_low_vol
    
    features['inside_bar_freq_20d'] = is_inside_low_vol.rolling(20, min_periods=10).sum()
    
    return features


def calc_all_daily_features(data: dict) -> Dict[str, pd.DataFrame]:
    """
    计算全部daily特征.

    Parameters
    ----------
    data : dict
        load_daily_data() 的输出

    Returns
    -------
    dict: {feature_name: DataFrame(index=date, columns=stock)}
    """
    all_features = {}

    print("[calc] B1.2 隔夜跳空异常...")
    all_features.update(calc_b12_gap_features(data))

    print("[calc] B1.4 昼夜结构...")
    all_features.update(calc_b14_daynight_features(data))

    print("[calc] B1.X 背景状态...")
    all_features.update(calc_b1x_background_features(data))

    print("[calc] B2.1 基础量能...")
    all_features.update(calc_b21_volume_features(data))

    print("[calc] B2.2 量变加速度...")
    all_features.update(calc_b22_volume_accel_features(data))

    print("[calc] B2.3 regime变点...")
    all_features.update(calc_b23_regime_features(data))

    print("[calc] B2.8 流动性...")
    all_features.update(calc_b28_liquidity_features(data))

    print("[calc] B2.13 截面排名...")
    all_features.update(calc_b213_crosssection_features(data))

    print("[calc] B3.1 创新特征 (IMOM/FIP/CLV/CMF/...)...")
    all_features.update(calc_b31_innovation_features(data))

    print(f"[calc] Done. Total {len(all_features)} features.")
    return all_features


# ============================================================
# 快速验证脚本
# ============================================================

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', help='用模拟数据测试')
    parser.add_argument('--csv', action='store_true', help='从csv文件加载 (推荐)')
    parser.add_argument('--start', default='20240101')
    parser.add_argument('--end', default='20260327')
    args = parser.parse_args()

    if args.csv:
        from data_loader import load_all_daily_data
        data = load_all_daily_data(start_date=args.start, end_date=args.end)
    else:
        # Demo: 用模拟数据
        from data_loader import generate_synthetic_data
        synth = generate_synthetic_data(n_stocks=200, n_days=500)
        data = {
            'open': synth['close'] * (1 + np.random.randn(*synth['close'].shape) * 0.005),
            'close': synth['close'],
            'high': synth['close'] * (1 + abs(np.random.randn(*synth['close'].shape) * 0.01)),
            'low': synth['close'] * (1 - abs(np.random.randn(*synth['close'].shape) * 0.01)),
            'lclose': synth['close'].shift(1),
            'vwap': synth['vwap'],
            'volume': pd.DataFrame(
                np.random.lognormal(15, 1, synth['close'].shape),
                index=synth['close'].index, columns=synth['close'].columns),
            'amount': pd.DataFrame(
                np.random.lognormal(20, 1, synth['close'].shape),
                index=synth['close'].index, columns=synth['close'].columns),
            'turnover_rate': pd.DataFrame(
                np.random.lognormal(0, 0.5, synth['close'].shape),
                index=synth['close'].index, columns=synth['close'].columns),
            'mcap': pd.DataFrame(
                np.random.lognormal(12, 1, synth['close'].shape),
                index=synth['close'].index, columns=synth['close'].columns),
        }

    features = calc_all_daily_features(data)

    # 打印摘要
    print("\n" + "=" * 70)
    print(f"  Daily Features Summary ({len(features)} features)")
    print("=" * 70)
    for name, df in sorted(features.items()):
        valid_pct = df.notna().mean().mean()
        mean_val = df.mean().mean()
        std_val = df.std().mean()
        print(f"  {name:40s}  valid={valid_pct:.1%}  mean={mean_val:>10.4f}  std={std_val:>10.4f}")
