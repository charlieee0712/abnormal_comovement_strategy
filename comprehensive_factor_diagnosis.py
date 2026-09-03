"""
综合单因子诊断 (Event Study + Calendar PnL)
============================================

升级版的 single_factor_groups, 同时输出:
  视图 A: Event Study (2/3/5 分组 mean 超额, 多空 Sharpe)
  视图 B: Calendar PnL (基于规则的单因子组合, daily PnL + Sharpe/Calmar/MDD/月度统计)

跨 4 段独立跑, 重点看 2024-26 段表现.

输入:
  - 因子定义列表 (因子名 + 计算函数 + 规则)
  - 默认池: I11 + 硬约束 (不卡市值)
  - 基准: I11 池等权 (同 single_factor_groups 口径)
  - 成本: 6bp 双边 (同 factor_marginal_v3 口径)

输出 (带时间戳子文件夹):
  - log.txt
  - event_study_<period>_<ngrp>.png × 多张
  - calendar_pnl_<period>_<factor>.png (每个因子一张, 含累积/回撤/月度)
  - factor_metrics.csv (所有因子的关键指标汇总)
  - summary.txt (跨段汇总表)

用法:
  python comprehensive_factor_diagnosis.py --period all --factors all
"""

import sys, os, numpy as np, pandas as pd
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data_loader
USER_CACHE_DIR = '/mnt/sda2/lichenchen/data/cache/'

# 双边成本 (bp), 可被 --cost_bp 覆盖. 默认6 (与历史口径一致).
COST_BP_BILATERAL = 6.0
os.makedirs(USER_CACHE_DIR, exist_ok=True)
data_loader.PATHS['cache_dir'] = USER_CACHE_DIR

from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import (
    define_i11_signal,
    build_observation_pool,
    apply_hard_constraints,
    compute_reversal_skip1,
    compute_parkinson_vol,
    compute_abnormal_turnover,
    compute_cmf_change,
    compute_log_mcap,
    neutralize_by_mcap,
)


# ============================================================
# 输出目录 + 日志
# ============================================================

def make_output_dir(suffix='comprehensive_diag'):
    base_dir = '/mnt/sda2/lichenchen/results'
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    out_dir = os.path.join(base_dir, f'{ts}_{suffix}')
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj); f.flush()
    def flush(self):
        for f in self.files:
            f.flush()


def setup_dual_logging(output_dir, log_name='log.txt'):
    log_path = os.path.join(output_dir, log_name)
    log_file = open(log_path, 'w', encoding='utf-8')
    sys.stdout = Tee(sys.__stdout__, log_file)
    return log_path


# ============================================================
# 因子注册表 (扩展时只需在这里加)
# ============================================================

CONFIRMED_FEATURE_NAMES = [
    # 原14 (微观结构等)
    'CCV_20d', 'info_discreteness_20d', 'CLV_20d', 'CVR_20d', 'drawdown_volume_ratio',
    'tug_of_war_20d', 'shadow_asymmetry_20d', 'conditional_turnover', 'RPV_20d', 'ou_halflife_60d',
    'stealth_score', 'amihud_asymmetry_20d', 'realized_skewness_20d', 'gap_survival_ratio',
    # vol类5
    'realized_vol_20d', 'vol_ratio_5d_20d', 'realized_kurtosis_20d', 'turnover_volatility_60d',
    'max_abs_return_10d',
    # 反转/动量11
    'cum_return_5d', 'cum_return_10d', 'cum_return_20d', 'distance_from_high_20d', 'days_since_high',
    'recent_high_20d', 'cum_intraday_ret_5d', 'cum_intraday_ret_10d', 'cum_intraday_ret_20d',
    'overnight_return_ratio_20d', 'overnight_ret_surprise',
]  # 30个, 已核对 features_daily.keys() 30/30 精确匹配 (2026-06-04)


def make_feature_func(feat_name):
    """features_daily 里已算好的因子, 直接从 features dict 取值.
    不预设方向 -- 双向剔尾 + 2/3/5 扫描让数据决定 (PROJECT_STATUS §4.4)."""
    def _f(data, features, industry):
        return features[feat_name]
    return _f


def get_default_factor_specs():
    """
    返回 4 个原有因子的 spec.
    spec 字段:
      name: 因子名 (输出文件用)
      func: 计算函数 (输入 data/features/industry → DataFrame)
      n_groups: 分组数 (Calendar PnL 用)
      drop_groups: 剔除的组号列表 (G1=1, G_max=n_groups)
      direction: 'positive' (因子大=好) / 'negative' (因子大=差, 已乘负号)
      neutralize_industry: 是否需要行业中性 (reversal 已在 compute 内做)
    """
    specs = [
        {
            'name': 'reversal_skip1',
            'func': lambda data, features, industry: compute_reversal_skip1(data['close'], industry, window=10),
            'n_groups': 3,
            'drop_groups': [1],
            'direction': 'positive',
        },
        {
            'name': 'parkinson_vol',
            'func': lambda data, features, industry: compute_parkinson_vol(data['high'], data['low'], window=20),
            'n_groups': 5,
            'drop_groups': [1],
            'direction': 'positive',
        },
        {
            'name': 'abn_turnover',
            'func': lambda data, features, industry: compute_abnormal_turnover(
                data.get('turnover_rate'), window_short=20, window_long=120),
            'n_groups': 5,
            'drop_groups': [1],
            'direction': 'positive',
        },
        {
            'name': 'cmf_change_neg',
            'func': lambda data, features, industry: -compute_cmf_change(features, window_long=10, window_short=5),
            # 直接乘负号, 统一为"越大越好"
            'n_groups': 3,
            'drop_groups': [1],
            'direction': 'positive',  # 已经乘了负号, 现在是正向
        },
    ]

    # 追加 30 个 features_daily 候选 (拼写已核对 30/30, 2026-06-04).
    # 双向剔尾 + 2/3/5 分组扫描自动定方向与分组, n_groups/drop_groups 仅占位.
    for feat_name in CONFIRMED_FEATURE_NAMES:
        specs.append({
            'name': feat_name,
            'func': make_feature_func(feat_name),
            'n_groups': 5,        # 占位, 2/3/5 扫描覆盖
            'drop_groups': [1],   # 占位, 双向剔尾覆盖
            'direction': 'unknown',
        })
    return specs


# ============================================================
# 后复权 + VWAP 日收益 (2026-09 E1 引擎修正; 参照 factor_library forward_returns.adjust_factor, commit a654a12)
# ============================================================

def adjust_factor(data):
    """后复权累计因子 A_t = Pi_{s<=t} prev_s / lclose_s, prev_s = s 日之前最近一个有效收盘价.
    lclose 是交易所口径的前收盘价(已含除权除息调整, 与 change_pct 逐格一致), 不用 adj_factor 列(首次除权前 NaN, 约 3.5% 格子).
    只在交易日(is_open==1)算比值, 停牌行记 1: 数据源在停牌行把 close/lclose 填成搬运值(正数, 非 NaN), 不能当真实成交价用;
    prev 取上一交易日收盘(ffill 跨停牌), 因此停牌期间发生的除权在复牌日被一次性捕捉、不重复计.
    只用于算收益(跨日比价); 复权价 = 原始价 x A_t. 同一日截面内的因子值不受影响.
    与 factor_library 版本的差别: 加 is_open 掩码 + prev 用 ffill 跨停牌(那边 prev=close.shift(1) 且不掩停牌行, 依赖数据源对停牌行的填法).
    """
    is_open = data['is_open'] == 1
    close = data['close'].where(is_open & (data['close'] > 0))
    lclose = data['lclose'].where(is_open & (data['lclose'] > 0))
    prev = close.ffill().shift(1)
    ok = close.notna() & prev.notna() & lclose.notna()
    ratio = (prev / lclose).where(ok).fillna(1.0)
    return ratio.cumprod()


def adjusted_prices(data, keys=('close', 'vwap')):
    """{key: 后复权价}, 见 adjust_factor."""
    a = adjust_factor(data)
    return {k: data[k] * a for k in keys}


def vwap_daily_return(data, adjust=True):
    """VWAP 回看日收益 vwap_t / vwap_{t-1} - 1.
    adjust=True: 后复权 vwap (正式口径). adjust=False: 原始 vwap = 2026-09 之前的旧写法, 仅供自测/分解对照, 禁止用于正式输出.
    """
    vwap = adjusted_prices(data, ('vwap',))['vwap'] if adjust else data['vwap']
    return (vwap / vwap.shift(1) - 1).replace([np.inf, -np.inf], np.nan)


# ============================================================
# Forward return 计算 (Event Study 用)
# ============================================================

def compute_forward_5d_excess(data, base_pool, hold_days=5, adjust=True):
    """5 日累积超额 (bp), 基准=base_pool 等权.
    时点: k=2..1+hold_days -> vwap_{T+1} 买入、vwap_{T+1+hold_days} 卖出 (与 Calendar exec_lag=1 同起点).
    adjust=True 用后复权 vwap (2026-09 E1 起); adjust=False 仅供对照.
    """
    vwap = data['vwap']
    ref_idx = vwap.index
    ref_col = vwap.columns
    bp = base_pool.reindex(index=ref_idx, columns=ref_col).fillna(0)
    
    vwap_daily_ret = vwap_daily_return(data, adjust)
    bm_daily = vwap_daily_ret.where(bp == 1).mean(axis=1)
    excess_daily = vwap_daily_ret.sub(bm_daily, axis=0)
    
    forward_list = []
    for k in range(2, 2 + hold_days):
        forward_list.append(excess_daily.shift(-k))
    return sum(forward_list) * 1e4


# ============================================================
# 视图 A: Event Study (2/3/5 分组)
# ============================================================

def event_study_analysis(factor, forward_ret, filtered_pool, log_mcap, n_groups,
                          factor_name, neutralize=True):
    """单因子分组多空 Sharpe (5 日 forward, 年化用 sqrt(252/5))."""
    daily_group_returns = {g: [] for g in range(1, n_groups + 1)}
    n_dates_used = 0
    
    for date_idx in filtered_pool.index:
        in_pool = filtered_pool.loc[date_idx] == 1
        stocks = filtered_pool.columns[in_pool].tolist()
        if len(stocks) < n_groups * 3:
            continue
        
        f_today = factor.loc[date_idx, stocks]
        fw_today = forward_ret.loc[date_idx, stocks] if date_idx in forward_ret.index else None
        if fw_today is None or fw_today.notna().sum() < n_groups * 3:
            continue
        
        if neutralize:
            mc_today = log_mcap.loc[date_idx, stocks]
            f_neu = neutralize_by_mcap(f_today, mc_today)
        else:
            f_neu = f_today
        
        df = pd.DataFrame({'f': f_neu, 'fw': fw_today}).dropna()
        if len(df) < n_groups * 3:
            continue
        
        try:
            df['group'] = pd.qcut(df['f'].rank(method='first'), n_groups,
                                  labels=range(1, n_groups + 1))
        except ValueError:
            continue
        
        for g in range(1, n_groups + 1):
            grp = df[df['group'] == g]
            if len(grp) > 0:
                daily_group_returns[g].append(grp['fw'].mean())
        n_dates_used += 1
    
    if n_dates_used < 10:
        return None
    
    # 各组统计
    group_means = {}
    for g in range(1, n_groups + 1):
        rets = pd.Series(daily_group_returns[g])
        if len(rets) >= 10:
            group_means[g] = rets.mean()
        else:
            group_means[g] = np.nan
    
    # 多空 (G_max - G_1)
    head_rets = pd.Series(daily_group_returns[n_groups])
    tail_rets = pd.Series(daily_group_returns[1])
    n = min(len(head_rets), len(tail_rets))
    if n < 10:
        return None
    ls_rets = head_rets.iloc[:n].values - tail_rets.iloc[:n].values
    
    ls_mean = ls_rets.mean()
    ls_std = ls_rets.std()
    ls_sharpe = ls_mean / ls_std * np.sqrt(252 / 5) if ls_std > 0 else 0
    
    # Net (扣 12bp 多空总成本 = 双边 6bp × 2)
    cost_bp = 12
    net_rets = ls_rets - cost_bp
    net_sharpe = net_rets.mean() / net_rets.std() * np.sqrt(252 / 5) if net_rets.std() > 0 else 0
    
    return {
        'n_groups': n_groups,
        'group_means_bp': group_means,
        'long_short_gross_sharpe': ls_sharpe,
        'long_short_net_sharpe': net_sharpe,
        'long_short_mean_bp': ls_mean,
        'n_dates': n_dates_used,
    }


# ============================================================
# 视图 B: Calendar PnL (规则筛选后的单因子组合)
# ============================================================

def precompute_neutralized_factor(factor, filtered_pool, log_mcap):
    """
    每日中性化因子值 + 排序信息, 一次算好供多个 n_groups 复用.
    
    返回: dict[date_idx] = pd.Series (中性化后的因子值, index=stocks)
    """
    cache = {}
    for date_idx in filtered_pool.index:
        in_pool = filtered_pool.loc[date_idx] == 1
        stocks = filtered_pool.columns[in_pool].tolist()
        if len(stocks) < 6:  # 太少不算
            continue
        f_today = factor.loc[date_idx, stocks]
        mc_today = log_mcap.loc[date_idx, stocks]
        f_neu = neutralize_by_mcap(f_today, mc_today)
        df = pd.DataFrame({'f': f_neu}).dropna()
        if len(df) < 6:
            continue
        cache[date_idx] = df['f']
    return cache


def event_study_analysis_cached(neu_cache, forward_ret, filtered_pool, n_groups, factor_name):
    """单因子分组多空 Sharpe, 用预算好的中性化因子."""
    daily_group_returns = {g: [] for g in range(1, n_groups + 1)}
    n_dates_used = 0
    
    for date_idx, f_neu in neu_cache.items():
        if len(f_neu) < n_groups * 3:
            continue
        
        if date_idx not in forward_ret.index:
            continue
        fw_today = forward_ret.loc[date_idx, f_neu.index]
        
        df = pd.DataFrame({'f': f_neu, 'fw': fw_today}).dropna()
        if len(df) < n_groups * 3:
            continue
        
        try:
            df['group'] = pd.qcut(df['f'].rank(method='first'), n_groups,
                                  labels=range(1, n_groups + 1))
        except ValueError:
            continue
        
        for g in range(1, n_groups + 1):
            grp = df[df['group'] == g]
            if len(grp) > 0:
                daily_group_returns[g].append(grp['fw'].mean())
        n_dates_used += 1
    
    if n_dates_used < 10:
        return None
    
    group_means = {}
    for g in range(1, n_groups + 1):
        rets = pd.Series(daily_group_returns[g])
        group_means[g] = rets.mean() if len(rets) >= 10 else np.nan
    
    head_rets = pd.Series(daily_group_returns[n_groups])
    tail_rets = pd.Series(daily_group_returns[1])
    n = min(len(head_rets), len(tail_rets))
    if n < 10:
        return None
    ls_rets = head_rets.iloc[:n].values - tail_rets.iloc[:n].values
    
    ls_mean = ls_rets.mean()
    ls_std = ls_rets.std()
    ls_sharpe = ls_mean / ls_std * np.sqrt(252 / 5) if ls_std > 0 else 0
    
    cost_bp = 12
    net_rets = ls_rets - cost_bp
    net_sharpe = net_rets.mean() / net_rets.std() * np.sqrt(252 / 5) if net_rets.std() > 0 else 0
    
    return {
        'n_groups': n_groups,
        'group_means_bp': group_means,
        'long_short_gross_sharpe': ls_sharpe,
        'long_short_net_sharpe': net_sharpe,
        'long_short_mean_bp': ls_mean,
        'n_dates': n_dates_used,
    }


def build_factor_strategy_holdings_cached(neu_cache, filtered_pool, n_groups, drop_groups):
    """用缓存的中性化因子建 holdings."""
    T = len(filtered_pool.index)
    N = len(filtered_pool.columns)
    holdings_arr = np.zeros((T, N), dtype=np.float32)
    col_idx_map = {col: i for i, col in enumerate(filtered_pool.columns)}
    date_idx_map = {d: i for i, d in enumerate(filtered_pool.index)}
    
    for date_idx, f_neu in neu_cache.items():
        if len(f_neu) < n_groups * 3:
            continue
        if date_idx not in date_idx_map:
            continue
        
        df = pd.DataFrame({'f': f_neu}).dropna()
        if len(df) < n_groups * 3:
            continue
        
        try:
            df['group'] = pd.qcut(df['f'].rank(method='first'), n_groups,
                                  labels=range(1, n_groups + 1))
        except ValueError:
            continue
        
        selected = df[~df['group'].isin(drop_groups)].index.tolist()
        if selected:
            t_idx = date_idx_map[date_idx]
            sel_col_idxs = [col_idx_map[s] for s in selected if s in col_idx_map]
            holdings_arr[t_idx, sel_col_idxs] = 1.0
    
    return pd.DataFrame(holdings_arr, index=filtered_pool.index, columns=filtered_pool.columns)


def assign_weights(holdings, industry, max_stock=0.01, max_industry=0.03, max_total=1.00):
    """
    按领导 Q1 公式分配权重:
      weight = min(max_stock, max_industry/N_行业内, max_total/N_总)
    
    返回 weights DataFrame (每日和=总仓位, 不一定满仓).
    
    性能优化: 用 numpy 向量化, 避免 pandas 逐 cell 写入.
    """
    weights = pd.DataFrame(0.0, index=holdings.index, columns=holdings.columns)
    holdings_arr = holdings.values  # (T, N) 0/1 矩阵
    
    if industry is not None:
        industry_aligned = industry.reindex(index=holdings.index, columns=holdings.columns)
        industry_arr = industry_aligned.values  # (T, N) object dtype, 行业代码或 NaN
    else:
        industry_arr = None
    
    T, N = holdings_arr.shape
    out = np.zeros((T, N), dtype=np.float64)
    
    for t in range(T):
        row_h = holdings_arr[t]
        sel_idx = np.where(row_h == 1)[0]
        if len(sel_idx) == 0:
            continue
        
        n_total = len(sel_idx)
        
        # 计算行业内股数
        if industry_arr is not None:
            row_i = industry_arr[t, sel_idx]
            # 用 pandas Series 算 value_counts (容忍 NaN)
            ind_series = pd.Series(row_i)
            ind_count = ind_series.value_counts(dropna=True).to_dict()
        else:
            ind_count = {}
            row_i = np.array([None] * n_total)
        
        # 每只股票算 weight (向量化)
        w_per_stock = np.zeros(n_total)
        for i in range(n_total):
            ind = row_i[i] if industry_arr is not None else None
            if ind is None or (isinstance(ind, float) and pd.isna(ind)):
                n_ind = 1  # 无行业信息, 不受行业约束
            else:
                n_ind = ind_count.get(ind, 1)
            
            w_per_stock[i] = min(max_stock, max_industry / max(n_ind, 1), max_total / max(n_total, 1))
        
        out[t, sel_idx] = w_per_stock
    
    weights = pd.DataFrame(out, index=holdings.index, columns=holdings.columns)
    return weights


def compute_calendar_pnl(weights, data, base_pool, hold_days=5, cost_bp_bilateral=6, exec_lag=1, adjust=True):
    """
    Calendar PnL: hold_days 日持有期, 持仓累积 (每天换 1/hold_days).
    口径 (2026-09 E1 定稿):
      - weights 一律按【信号日 T】索引, 调用方不预先 shift.
      - exec_lag=1: T 收盘出信号, T+1 vwap 成交. daily_ret 是回看日收益 (vwap_t/vwap_{t-1}-1),
        故持仓 shift(exec_lag+1)=2. 每笔 T+1 vwap 进、T+1+hold_days vwap 出,
        与 compute_forward_5d_excess (k=2..1+hold_days) 逐笔同起点 (selftest_engine_fix T4 恒等式保证).
      - adjust=True: 收益用后复权 vwap (adjust_factor), 除权除息日不再记假跌.
      - exec_lag=0 / adjust=False = 2026-09 之前的旧写法 (T 日 vwap 起记 + 未复权),
        仅供自测复现与 E2 分解对照, 禁止用于任何正式输出.
    
    每日 PnL = sum(实际持仓权重 × 当日 daily return) - 当日基准 daily return × 总仓位.
    """
    vwap = data['vwap']
    ref_idx = vwap.index
    ref_col = vwap.columns
    
    weights_aligned = weights.reindex(index=ref_idx, columns=ref_col).fillna(0)
    bp = base_pool.reindex(index=ref_idx, columns=ref_col).fillna(0)
    
    # 实际持仓 = 过去 5 天 weights 的均值 (每天换 1/hold_days)
    actual_holding = weights_aligned.rolling(hold_days, min_periods=1).mean()
    
    # 每日 daily return (VWAP-to-VWAP)
    daily_ret = vwap_daily_return(data, adjust)
    
    # 基准 daily ret = I11 池等权
    bm_daily = daily_ret.where(bp == 1).mean(axis=1)
    
    # 持仓按信号日 T 索引; exec_lag=1 = T+1 vwap 成交; daily_ret 是回看日收益, 故 shift(exec_lag+1)=2
    actual_holding_t1 = actual_holding.shift(exec_lag + 1)
    portfolio_daily_ret = (actual_holding_t1 * daily_ret).sum(axis=1)
    daily_position = actual_holding_t1.sum(axis=1).fillna(0)
    excess_daily = portfolio_daily_ret - bm_daily * daily_position
    
    # ★ 精确换手: 持仓 diff 的绝对值 / 2 (买入和卖出, 除2避免重复)
    holding_diff = actual_holding_t1.diff().abs().sum(axis=1) / 2.0
    holding_diff = holding_diff.fillna(0)
    
    # 扣成本: 每天的实际换手率 × 双边成本 (可配置, 默认6bp)
    daily_cost = holding_diff * (cost_bp_bilateral / 1e4)
    excess_daily_net = excess_daily - daily_cost
    
    return {
        'gross_excess_daily': excess_daily,
        'net_excess_daily': excess_daily_net,
        'daily_position': daily_position,
        'daily_turnover': holding_diff,
        'turnover_per_day': holding_diff.mean(),
        'turnover_annual': holding_diff.sum() / (len(holding_diff) / 252) if len(holding_diff) > 0 else 0,
        'port_daily': portfolio_daily_ret,   # 组合自身日收益(未减基准), 自测恒等式用
        'bench_daily': bm_daily,             # 基准日收益
        'exec_lag': exec_lag, 'adjust': adjust,
    }


def calendar_pnl_metrics(daily_ret_series):
    """
    给定每日收益序列, 算 Sharpe (三口径) / Calmar / MDD / 月度统计.

    三个 Sharpe (均已验证, 见 test_sharpe_estimators.py):
      sharpe_naive:  std 假设 iid, 年化 sqrt(252)        -- 乐观, 持仓重叠时高估
      sharpe_nw:     Newey-West (lag=5) 调整 std         -- 保守, 全样本, lag 与持仓周期对齐
      sharpe_weekly: 非重叠 5 日收益, 年化 sqrt(252/5)   -- 保守, 从根上消除重叠自相关
    """
    rets = daily_ret_series.dropna()
    if len(rets) < 30:
        return None
    
    # Sharpe (年化) - naive 口径
    mean_ret = rets.mean()
    std_ret = rets.std()
    sharpe = mean_ret / std_ret * np.sqrt(252) if std_ret > 0 else 0
    sharpe_naive = sharpe
    
    # Sharpe - Newey-West (lag=5)
    sharpe_nw = _sharpe_newey_west(rets.values, lag=5)
    
    # Sharpe - 非重叠周收益
    sharpe_weekly = _sharpe_weekly(rets, block=5)
    
    # 累积收益曲线
    cum_ret = (1 + rets).cumprod() - 1
    
    # MDD
    running_max = (1 + rets).cumprod().cummax()
    drawdown = (1 + rets).cumprod() / running_max - 1
    mdd = drawdown.min()
    
    # Calmar
    annual_ret = (1 + mean_ret) ** 252 - 1
    calmar = annual_ret / abs(mdd) if mdd < 0 else 0
    
    # 月度收益
    # 月度收益 (兼容新老 pandas: 老版用 'M', 新版用 'ME')
    try:
        monthly = rets.resample('ME').apply(lambda x: (1 + x).prod() - 1)
    except ValueError:
        monthly = rets.resample('M').apply(lambda x: (1 + x).prod() - 1)
    monthly_win_rate = (monthly > 0).mean()
    
    # 最坏 5 日
    worst_days = rets.nsmallest(5)
    best_days = rets.nlargest(5)
    
    return {
        'sharpe': sharpe,
        'sharpe_naive': sharpe_naive,
        'sharpe_nw': sharpe_nw,
        'sharpe_weekly': sharpe_weekly,
        'annual_ret': annual_ret,
        'mdd': mdd,
        'calmar': calmar,
        'monthly_win_rate': monthly_win_rate,
        'monthly_pnl_series': monthly,
        'cum_ret_series': cum_ret,
        'drawdown_series': drawdown,
        'worst_days': worst_days,
        'best_days': best_days,
        'n_days': len(rets),
    }


def _sharpe_newey_west(ret_array, lag=5):
    """Newey-West 调整的 Sharpe (年化 sqrt(252)). lag 与持仓周期对齐."""
    r = ret_array[~np.isnan(ret_array)]
    n = len(r)
    if n < 30:
        return np.nan
    mean = r.mean()
    dev = r - mean
    gamma0 = np.dot(dev, dev) / n
    if gamma0 == 0:
        return np.nan
    nw_var = gamma0
    for k in range(1, lag + 1):
        if k >= n:
            break
        gamma_k = np.dot(dev[k:], dev[:-k]) / n
        weight = 1.0 - k / (lag + 1.0)
        nw_var += 2.0 * weight * gamma_k
    if nw_var <= 0:
        return np.nan
    return mean / np.sqrt(nw_var) * np.sqrt(252)


def _sharpe_weekly(ret_series, block=5):
    """非重叠 block 日收益聚合的 Sharpe (年化 sqrt(252/block))."""
    r = ret_series.dropna()
    if len(r) < block * 10:
        return np.nan
    n_blocks = len(r) // block
    r_trim = r.iloc[:n_blocks * block]
    blocks = r_trim.values.reshape(n_blocks, block)
    block_ret = (1 + blocks).prod(axis=1) - 1
    if block_ret.std() == 0:
        return np.nan
    return block_ret.mean() / block_ret.std() * np.sqrt(252 / block)


# ============================================================
# 绘图
# ============================================================

def plot_calendar_pnl(metrics_gross, metrics_net, factor_name, period_name, output_dir):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import warnings; warnings.filterwarnings('ignore', category=UserWarning)
    except ImportError:
        return None
    
    if metrics_gross is None or metrics_net is None:
        return None
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 11))
    
    # 子图 1: 累积超额曲线 (gross + net)
    ax = axes[0]
    metrics_gross['cum_ret_series'].plot(ax=ax, label=f"Gross (Sh={metrics_gross['sharpe']:.2f})", color='#2ca02c', linewidth=1.5)
    metrics_net['cum_ret_series'].plot(ax=ax, label=f"Net (Sh={metrics_net['sharpe']:.2f})", color='#d62728', linewidth=1.5)
    ax.axhline(0, color='k', linewidth=0.5)
    ax.set_title(f'{factor_name} | {period_name} | 累积超额收益')
    ax.set_ylabel('累积超额')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # 子图 2: 回撤曲线 (net)
    ax = axes[1]
    metrics_net['drawdown_series'].plot(ax=ax, color='#d62728', linewidth=1.0)
    ax.fill_between(metrics_net['drawdown_series'].index,
                     metrics_net['drawdown_series'].values, 0, color='#d62728', alpha=0.3)
    ax.set_title(f"Net 回撤 | MDD={metrics_net['mdd']*100:.1f}%, Calmar={metrics_net['calmar']:.2f}")
    ax.set_ylabel('Drawdown')
    ax.grid(True, alpha=0.3)
    
    # 子图 3: 月度 PnL 柱状图 (net)
    ax = axes[2]
    monthly = metrics_net['monthly_pnl_series']
    colors = ['#2ca02c' if x > 0 else '#d62728' for x in monthly]
    ax.bar(range(len(monthly)), monthly.values * 100, color=colors, alpha=0.85)
    ax.axhline(0, color='k', linewidth=0.5)
    ax.set_title(f"Net 月度 PnL (%) | 月胜率={metrics_net['monthly_win_rate']*100:.1f}%")
    ax.set_ylabel('Monthly Return (%)')
    ax.set_xticks(range(0, len(monthly), max(1, len(monthly)//12)))
    ax.set_xticklabels([str(d)[:7] for d in monthly.index[::max(1, len(monthly)//12)]], rotation=45)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_path = os.path.join(output_dir, f'calendar_pnl_{period_name.replace("-","_")}_{factor_name}.png')
    plt.savefig(save_path, dpi=110, bbox_inches='tight')
    plt.close()
    return save_path


# ============================================================
# 单段全因子诊断
# ============================================================

def compute_factor_correlation_matrix(all_neu_caches, filtered_pool, factor_names):
    """
    NxN 因子相关性矩阵: 每个交易日在 I11 池内算一次截面 Spearman 相关
    (= 中性化值 rank 后 Pearson), 再对所有交易日取均值.
    输入用各因子中性化后的值 (precompute_neutralized_factor 输出).

    向量化: 每天把所有因子的池内值拼成一个 DataFrame, df.rank().corr() 一次出当日全矩阵,
    绝不因子两两逐日循环.
    """
    mat_sum = None
    cnt_mat = None
    all_dates = set()
    for fac in factor_names:
        all_dates.update(all_neu_caches.get(fac, {}).keys())
    all_dates = sorted(all_dates)

    for date_idx in all_dates:
        cols = {}
        for fac in factor_names:
            s = all_neu_caches.get(fac, {}).get(date_idx)
            if s is not None:
                cols[fac] = s
        if len(cols) < 2:
            continue
        df = pd.DataFrame(cols)                       # index=池内股票(并集), columns=因子
        r = df.rank().corr().reindex(index=factor_names, columns=factor_names)
        if mat_sum is None:
            mat_sum = r.fillna(0).values.copy()
            cnt_mat = (~r.isna()).astype(int).values.copy()
        else:
            mat_sum = mat_sum + r.fillna(0).values
            cnt_mat = cnt_mat + (~r.isna()).astype(int).values

    if mat_sum is None:
        return pd.DataFrame(np.nan, index=factor_names, columns=factor_names)

    # ★ 必须用 out= 给可写数组, 否则 np.divide(where=) 返回只读数组会报错
    corr_mean = np.full_like(mat_sum, np.nan, dtype=float)
    np.divide(mat_sum, cnt_mat, out=corr_mean, where=cnt_mat > 0)
    return pd.DataFrame(corr_mean, index=factor_names, columns=factor_names)


def plot_correlation_heatmap(corr_mat, period_name, output_dir):
    """相关性矩阵热力图 (可选, 失败不影响主流程)."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import warnings; warnings.filterwarnings('ignore')
    except ImportError:
        return None
    n = corr_mat.shape[0]
    if n == 0:
        return None
    fig, ax = plt.subplots(figsize=(max(8, n * 0.45), max(7, n * 0.42)))
    im = ax.imshow(corr_mat.values.astype(float), vmin=-1, vmax=1, cmap='RdBu_r', aspect='auto')
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels(list(corr_mat.columns), rotation=90, fontsize=6)
    ax.set_yticklabels(list(corr_mat.index), fontsize=6)
    ax.set_title('Factor cross-sectional rank corr (time-avg) | %s' % period_name)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    save_path = os.path.join(output_dir, 'correlation_matrix_%s.png' % period_name.replace('-', '_'))
    plt.savefig(save_path, dpi=110, bbox_inches='tight')
    plt.close()
    return save_path


def analyze_period(period_name, start, end, factor_specs, output_dir):
    print(f"\n{'#'*90}")
    print(f"  综合诊断: {period_name}")
    print(f"{'#'*90}")
    
    print(f"\n[1/5] 加载数据 + 计算特征 + 构造池子...")
    data = load_all_daily_data(start_date=start, end_date=end)
    features = calc_all_daily_features(data)
    
    base_pool = get_base_pool(data)
    signal = define_i11_signal(features, base_pool)
    obs_pool = build_observation_pool(signal, obs_window=5)
    filtered = apply_hard_constraints(obs_pool, data, features, min_mcap=0)
    
    avg_pool_size = filtered.sum(axis=1).mean()
    print(f"  I11池 + 硬约束 池规模: {avg_pool_size:.0f} 只/天")
    
    print(f"\n[2/5] 计算 forward return...")
    forward_ret = compute_forward_5d_excess(data, filtered, hold_days=5)
    
    log_mcap = compute_log_mcap(data.get('mcap'))
    industry = data.get('industry_zx1', data.get('industry'))
    if industry is not None:
        industry = industry.reindex(index=data['close'].index, columns=data['close'].columns)
    
    period_results = {}
    all_neu_caches = {}   # 收集各因子中性化 neu_cache, 供相关性矩阵
    for fac_spec in factor_specs:
        fac_name = fac_spec['name']
        print(f"\n  --- {fac_name} (n_groups={fac_spec['n_groups']}, drop={fac_spec['drop_groups']}) ---")
        
        # 计算因子
        try:
            factor_df = fac_spec['func'](data, features, industry)
        except Exception as e:
            print(f"    [ERROR] 因子计算失败: {e}")
            continue
        
        # ★ 一次中性化, 多次复用 (省 70% 时间)
        print(f"    [precompute] 中性化 + 缓存...")
        neu_cache = precompute_neutralized_factor(factor_df, filtered, log_mcap)
        print(f"    [precompute] 缓存了 {len(neu_cache)} 个交易日的中性化因子值")
        all_neu_caches[fac_name] = neu_cache   # ★ 存下来供相关性矩阵
        
        # 视图 A: Event Study (跑 2/3/5 分组, 复用 cache)
        event_results = {}
        for ng in [2, 3, 5]:
            r = event_study_analysis_cached(neu_cache, forward_ret, filtered,
                                              n_groups=ng, factor_name=fac_name)
            if r:
                event_results[ng] = r
                print(f"    Event Study {ng}grp: gross_LS_Sharpe={r['long_short_gross_sharpe']:+.2f}, "
                      f"net_LS_Sharpe={r['long_short_net_sharpe']:+.2f}")
        
        # 视图 B: Calendar PnL (复用 cache)
        # ★ 双向剔尾 + 2/3/5 分组扫描: 数据定方向, 不靠预设
        #   对每个 (n_groups, 剔最低组 or 剔最高组) 组合算"剔尾超额", 选最优
        print(f"    [Calendar PnL] 双向剔尾 + 2/3/5 分组扫描...")
        try:
            best = None  # (mean_excess, config, pnl_result, metrics_6bp)
            sweep_log = []
            for ng in [2, 3, 5]:
                for drop_side, drop_groups in [('low', [1]), ('high', [ng])]:
                    holdings = build_factor_strategy_holdings_cached(
                        neu_cache, filtered, n_groups=ng, drop_groups=drop_groups)
                    weights = assign_weights(holdings, industry)
                    pr = compute_calendar_pnl(weights, data, filtered,
                                               hold_days=5, cost_bp_bilateral=COST_BP_BILATERAL)
                    m6 = calendar_pnl_metrics(pr['net_excess_daily'])
                    if m6 is None:
                        continue
                    mean_excess = pr['net_excess_daily'].mean()
                    sweep_log.append((ng, drop_side, m6['sharpe_nw'], mean_excess))
                    # 选择标准: NW Sharpe 最大 (保守口径下的最优, 避免被 naive 高估误导)
                    score = m6['sharpe_nw'] if not np.isnan(m6['sharpe_nw']) else -99
                    if best is None or score > best[0]:
                        best = (score, (ng, drop_side, drop_groups), pr, m6)

            # 打印扫描结果
            for ng, side, nw, exc in sweep_log:
                print(f"      {ng}grp 剔{side:>4s}: NW_Sharpe={nw:+.2f}, 日均剔尾超额={exc*1e4:+.2f}bp")

            if best is None:
                print(f"    [WARN] 所有分组组合都无有效结果")
                period_results[fac_name] = {'event_study': event_results}
                continue

            _, best_cfg, pnl_result, metrics_net = best
            best_ng, best_side, best_drop = best_cfg
            print(f"    [Calendar PnL] ★最优: {best_ng}分组 剔{best_side} (方向={'正向' if best_side=='low' else '反向'})")

            # 用最优配置算三个 Sharpe
            metrics_gross = calendar_pnl_metrics(pnl_result['gross_excess_daily'])

            if metrics_net:
                print(f"    [{COST_BP_BILATERAL:.0f}bp] naive={metrics_net['sharpe_naive']:+.2f}  "
                      f"NW={metrics_net['sharpe_nw']:+.2f}  weekly={metrics_net['sharpe_weekly']:+.2f}")
                print(f"    [{COST_BP_BILATERAL:.0f}bp] Calmar={metrics_net['calmar']:.2f}  MDD={metrics_net['mdd']*100:.1f}%  "
                      f"月胜率={metrics_net['monthly_win_rate']*100:.0f}%")
                print(f"    [仓位] 平均={pnl_result['daily_position'].mean()*100:.1f}%  "
                      f"年化换手={pnl_result['turnover_annual']:.1f}x")

                plot_path = plot_calendar_pnl(metrics_gross, metrics_net, fac_name, period_name, output_dir)
                if plot_path:
                    print(f"    [plot] {plot_path}")

            period_results[fac_name] = {
                'event_study': event_results,
                'calendar_gross': metrics_gross,
                'calendar_net': metrics_net,
                'best_config': {'n_groups': best_ng, 'drop_side': best_side,
                                'direction': 'positive' if best_side == 'low' else 'negative'},
                'avg_position': pnl_result['daily_position'].mean(),
                'avg_turnover_annual': pnl_result['turnover_annual'],
            }
        except Exception as e:
            print(f"    [ERROR] Calendar PnL 失败: {e}")
            import traceback; traceback.print_exc()
            period_results[fac_name] = {'event_study': event_results}
    
    # ============================================================
    # 因子相关性矩阵: 本段所有因子中性化值的截面 rank 相关 (时序均值)
    # ============================================================
    fac_names_corr = [s['name'] for s in factor_specs if s['name'] in all_neu_caches]
    print(f"\n[相关性矩阵] {len(fac_names_corr)} 因子, 计算截面 rank 相关 (时序均值)...")
    try:
        corr_mat = compute_factor_correlation_matrix(all_neu_caches, filtered, fac_names_corr)
        corr_csv = os.path.join(output_dir, 'correlation_matrix_%s.csv' % period_name.replace('-', '_'))
        corr_mat.to_csv(corr_csv, encoding='utf-8-sig')
        print(f"  [csv] {corr_csv}  ({corr_mat.shape[0]}x{corr_mat.shape[1]})")
        hp = plot_correlation_heatmap(corr_mat, period_name, output_dir)
        if hp:
            print(f"  [plot] {hp}")
    except Exception as e:
        print(f"  [ERROR] 相关性矩阵失败: {e}")
        import traceback; traceback.print_exc()

    return period_results


# ============================================================
# 跨段汇总
# ============================================================

def cross_period_summary(all_results, output_dir, factor_specs):
    print(f"\n\n{'#'*90}")
    print(f"  跨段汇总")
    print(f"{'#'*90}")
    
    fac_names = [s['name'] for s in factor_specs]
    periods = list(all_results.keys())
    
    # Event Study 多空 Sharpe (3 分组)
    print(f"\n--- Event Study 多空 Sharpe (3分组, Net) ---")
    print(f"  {'因子':<22s} " + "  ".join(f"{p:>10s}" for p in periods) + f"  {'均值':>8s}")
    for fac in fac_names:
        vals = []; cells = []
        for p in periods:
            r = all_results.get(p, {}).get(fac, {}).get('event_study', {}).get(3)
            if r:
                vals.append(r['long_short_net_sharpe'])
                cells.append(f"{r['long_short_net_sharpe']:>+10.2f}")
            else:
                cells.append(f"{'N/A':>10s}")
        avg = np.mean(vals) if vals else 0
        print(f"  {fac:<22s} " + "  ".join(cells) + f"  {avg:>+8.2f}")
    
    # Calendar PnL Sharpe
    print(f"\n--- Calendar PnL Sharpe (规则筛选后, NW 保守口径) ---")
    print(f"  {'因子':<22s} " + "  ".join(f"{p:>10s}" for p in periods) + f"  {'均值':>8s}")
    for fac in fac_names:
        vals = []; cells = []
        for p in periods:
            m = all_results.get(p, {}).get(fac, {}).get('calendar_net')
            if m:
                vals.append(m['sharpe_nw'])
                cells.append(f"{m['sharpe_nw']:>+10.2f}")
            else:
                cells.append(f"{'N/A':>10s}")
        avg = np.mean(vals) if vals else 0
        print(f"  {fac:<22s} " + "  ".join(cells) + f"  {avg:>+8.2f}")
    
    # Calendar PnL Calmar
    print(f"\n--- Calendar PnL Calmar (Net) ---")
    print(f"  {'因子':<22s} " + "  ".join(f"{p:>10s}" for p in periods) + f"  {'均值':>8s}")
    for fac in fac_names:
        vals = []; cells = []
        for p in periods:
            m = all_results.get(p, {}).get(fac, {}).get('calendar_net')
            if m:
                vals.append(m['calmar'])
                cells.append(f"{m['calmar']:>+10.2f}")
            else:
                cells.append(f"{'N/A':>10s}")
        avg = np.mean(vals) if vals else 0
        print(f"  {fac:<22s} " + "  ".join(cells) + f"  {avg:>+8.2f}")
    
    # MDD
    print(f"\n--- Calendar PnL MDD (Net, %) ---")
    print(f"  {'因子':<22s} " + "  ".join(f"{p:>10s}" for p in periods) + f"  {'均值':>8s}")
    for fac in fac_names:
        vals = []; cells = []
        for p in periods:
            m = all_results.get(p, {}).get(fac, {}).get('calendar_net')
            if m:
                vals.append(m['mdd'] * 100)
                cells.append(f"{m['mdd']*100:>10.1f}")
            else:
                cells.append(f"{'N/A':>10s}")
        avg = np.mean(vals) if vals else 0
        print(f"  {fac:<22s} " + "  ".join(cells) + f"  {avg:>+8.1f}")
    
    # 保存 csv
    rows = []
    for fac in fac_names:
        for p in periods:
            event = all_results.get(p, {}).get(fac, {}).get('event_study', {}).get(3, {})
            cal_net = all_results.get(p, {}).get(fac, {}).get('calendar_net', {})
            cal_gross = all_results.get(p, {}).get(fac, {}).get('calendar_gross', {})
            best_cfg = all_results.get(p, {}).get(fac, {}).get('best_config', {})
            rows.append({
                'factor': fac,
                'period': p,
                # 最优配置 (双向剔尾扫描结果)
                'best_n_groups':      best_cfg.get('n_groups', np.nan),
                'best_drop_side':     best_cfg.get('drop_side', ''),
                'direction':          best_cfg.get('direction', ''),
                # Event Study (多空, 仅供参考 - 不是我们策略口径)
                'event_LS_gross_sharpe': event.get('long_short_gross_sharpe', np.nan),
                'event_LS_net_sharpe':   event.get('long_short_net_sharpe', np.nan),
                # Calendar PnL 三口径 (★主要看这些)
                'cal_sharpe_naive':  cal_net.get('sharpe_naive', np.nan) if cal_net else np.nan,
                'cal_sharpe_nw':     cal_net.get('sharpe_nw', np.nan) if cal_net else np.nan,
                'cal_sharpe_weekly': cal_net.get('sharpe_weekly', np.nan) if cal_net else np.nan,
                # 回撤指标 (不受自相关影响, 稳)
                'cal_calmar':            cal_net.get('calmar', np.nan) if cal_net else np.nan,
                'cal_mdd':               cal_net.get('mdd', np.nan) if cal_net else np.nan,
                'cal_monthly_winrate':   cal_net.get('monthly_win_rate', np.nan) if cal_net else np.nan,
                # gross 参考
                'cal_gross_sharpe_naive': cal_gross.get('sharpe_naive', np.nan) if cal_gross else np.nan,
                'avg_position':          all_results.get(p, {}).get(fac, {}).get('avg_position', np.nan),
                'avg_turnover_annual':   all_results.get(p, {}).get(fac, {}).get('avg_turnover_annual', np.nan),
            })
    df = pd.DataFrame(rows)
    csv_path = os.path.join(output_dir, 'factor_metrics.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\n[csv] 保存到 {csv_path}")


# ============================================================
# 主流程
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--period', default='all', help='all 或具体段名')
    parser.add_argument('--factors', default='all',
                        help="all 或逗号分隔因子名 (子集验证, 如 'reversal_skip1,cum_return_20d')")
    parser.add_argument('--cost_bp', type=float, default=6.0,
                        help='双边成本 bp (默认6, 可调; 实盘中低频参考10-15)')
    args = parser.parse_args()
    
    global COST_BP_BILATERAL
    COST_BP_BILATERAL = args.cost_bp
    
    output_dir = make_output_dir('comprehensive_diag')
    log_path = setup_dual_logging(output_dir)
    print(f"\n{'★'*90}")
    print(f"  综合单因子诊断 (Event Study + Calendar PnL)")
    print(f"  输出: {output_dir}")
    print(f"{'★'*90}")
    
    factor_specs = get_default_factor_specs()
    if args.factors != 'all':
        want = [x.strip() for x in args.factors.split(',') if x.strip()]
        known = {s['name'] for s in factor_specs}
        missing = [w for w in want if w not in known]
        if missing:
            print(f"[WARN] --factors 里这些名字不在 specs, 忽略: {missing}")
        factor_specs = [s for s in factor_specs if s['name'] in want]
        if not factor_specs:
            print("[ERROR] --factors 过滤后无因子可跑"); return
    print(f"\n因子数: {len(factor_specs)}")
    for s in factor_specs:
        print(f"  - {s['name']} (n_groups={s['n_groups']}, drop={s['drop_groups']})")
    
    all_results = {}
    if args.period == 'all':
        for p, (s, e) in PERIODS.items():
            try:
                all_results[p] = analyze_period(p, s, e, factor_specs, output_dir)
            except Exception as exc:
                print(f"\n[ERROR] {p}: {exc}")
                import traceback; traceback.print_exc()
    else:
        s, e = PERIODS[args.period]
        all_results[args.period] = analyze_period(args.period, s, e, factor_specs, output_dir)
    
    if len(all_results) >= 1:
        cross_period_summary(all_results, output_dir, factor_specs)
    
    print(f"\n{'★'*90}")
    print(f"  完成. 输出: {output_dir}")
    print(f"{'★'*90}")
    print("[done]")


if __name__ == '__main__':
    main()
