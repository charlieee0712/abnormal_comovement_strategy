"""
观察池内截面筛选框架 v2 (Sharpe 2.45定稿版)
=========================================
当前默认配置 = 上一轮 pool_v2_all.txt 对应的最优 (4段平均Sharpe 2.45)

核心配置:
  硬约束   : 3项精简 (停牌涨跌停/次新/低成交) + 50亿市值阈值
  标准化   : Rank百分位 (小样本鲁棒)
  反转     : Skip-1day 10日涨幅 + 行业中性化 (Da et al. 2014)
  波动率   : Parkinson 20日 (仅过滤一字板, P0改动失败)
  换手率   : 异常换手率 = 20日/120日 (LSY 2019)
  CMF      : ΔCMF_10d (5日变化, 删除会导致Sharpe暴跌)
  中性化   : 反转做行业减均值+市值OLS, 其他3因子只做市值OLS
  合成     : 等权法
  顺序     : 评分后取Top15 -> 单行业≤3

实验开关 (用于factor_marginal_diagnosis 诊断, 默认关闭):
  include_reversal=True   include_vol=True
  include_abn_to=True     include_cmf_change=True
  → 把任一设为False做leave-one-out边际贡献测试

历史教训 (项目重要发现):
  ❌ P0改动 (窗口10/掩码/STR/全因子行业中性化): Sharpe从2.51崩到0.27
  ❌ 删ΔCMF: Sharpe从+2.48崩到-2.29 (即使ΔCMF独立IC≈0)
  → IC高 ≠ Sharpe贡献高, 必须用回测验证

用法:
    python pool_screening_v2.py --period all 2>&1 | tee pool_v2_all.txt
"""

import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import get_base_pool, PERIODS


# ============================================================
# I11 入场信号 (P80定稿版, 保持不变)
# ============================================================

def define_i11_signal(features, base_pool):
    bp = base_pool.reindex_like(features['intraday_ret']).fillna(0)
    mask = bp == 1
    
    def pct_in_pool(feat_name):
        f = features[feat_name].reindex_like(bp).where(mask)
        return f.rank(axis=1, pct=True)
    
    cmf_pct = pct_in_pool('CMF_20d')
    cr5_pct = pct_in_pool('cum_return_5d')
    ir_pct = pct_in_pool('intraday_ret')
    
    signal = (
        (cmf_pct >= 0.80) &
        (cr5_pct >= 0.25) & (cr5_pct <= 0.55) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    return signal


# ============================================================
# 观察池构建
# ============================================================

def build_observation_pool(signal, obs_window=3):
    """最近obs_window天内触发过的股票."""
    pool = pd.DataFrame(0.0, index=signal.index, columns=signal.columns)
    for lag in range(1, obs_window + 1):
        pool += signal.shift(lag).fillna(0)
    return (pool > 0).astype(float)


# ============================================================
# 第一层: 硬约束 (精简到3项 + 绝对市值阈值)
# ============================================================

def apply_hard_constraints(obs_pool, data, features,
                           min_mcap=5e9,           # 50亿RMB绝对阈值 (2024年后共识)
                           min_amount=2e7,         # 2000万日均成交额 (海通研报)
                           min_list_days=20,       # 上市<20日剔除
                           ):
    """
    3项硬约束:
      1. 停牌/当日涨跌停 (无法VWAP执行) - 通过is_open判断
      2. 次新股 (上市<20个交易日, 量价数据不足)
      3. 流动性不足 (20日日均成交额 < 2000万)
      PLUS: 流通市值 < 50亿 (2024年2月崩盘后行业共识)
    """
    close = data['close']
    ref_idx = close.index
    ref_col = close.columns
    
    # 统一对齐所有字段到close的shape, 避免DataFrame对齐错误
    def align(df, fill=0):
        if df is None:
            return None
        return df.reindex(index=ref_idx, columns=ref_col).fillna(fill)
    
    amount = align(data.get('amount', None), fill=1e10)
    if amount is None:
        amount = close * 0 + 1e10
    mcap = align(data.get('mcap', None), fill=0)
    if mcap is None:
        mcap = close * 0 + 1e10
    is_open = align(data.get('is_open', None), fill=0)
    if is_open is None:
        is_open = close * 0 + 1
    limit_up = align(data.get('limit_up', None))
    limit_down = align(data.get('limit_down', None))
    
    filtered = obs_pool.reindex(index=ref_idx, columns=ref_col).fillna(0)
    
    # 预计算:
    # 1. 当日是否可交易 (非停牌)
    tradable = (is_open == 1)
    
    # 2. 当日是否涨跌停 (无法以VWAP买入)
    if limit_up is not None and limit_down is not None:
        not_limit = (close < limit_up - 0.01) | (close > limit_down + 0.01)
        # 如果limit_up/down全是0或NaN (说明数据缺失), fallback到收益率判断
        has_limit_data = (limit_up > 0).any().any()
        if not has_limit_data:
            daily_ret = close / close.shift(1) - 1
            not_limit = (daily_ret < 0.098) & (daily_ret > -0.098)
    else:
        daily_ret = close / close.shift(1) - 1
        not_limit = (daily_ret < 0.098) & (daily_ret > -0.098)
    
    # 3. 20日日均成交额
    amount_20d = amount.rolling(20, min_periods=10).mean()
    liquid = (amount_20d > min_amount)
    
    # 4. 上市天数 (用close non-null计数)
    list_days = close.notna().astype(float).rolling(window=min_list_days, min_periods=1).sum()
    mature = (list_days >= min_list_days)
    
    # 5. 市值阈值
    if min_mcap > 0:
        big_enough = (mcap > min_mcap)
    else:
        big_enough = pd.DataFrame(True, index=ref_idx, columns=ref_col)
    
    # 组合所有约束 (全部已对齐到相同shape)
    passes_all = (
        tradable & not_limit & liquid & mature & big_enough
    ).astype(float)
    
    # 应用到observation pool
    filtered = filtered * passes_all
    
    return filtered


# ============================================================
# 第二层: 因子计算 (5个优化因子)
# ============================================================

def compute_reversal_skip1(close, industry, window=10):
    """
    Skip-1day反转因子 + 行业中性化.
    
    Skip最近1天避免bid-ask bounce (Jegadeesh-Titman 1993).
    行业中性化 (Da et al. 2014 NY Fed): 减去同行业均值, IC提升2.5x.
    方向: 负向 (越低越好, 即反转)
    """
    ret_adj = close.shift(1) / close.shift(window + 1) - 1
    
    # 行业中性化: 减去同行业均值
    if industry is not None:
        ret_neutral = ret_adj.copy()
        for date_idx in ret_adj.index:
            ret_today = ret_adj.loc[date_idx]
            ind_today = industry.loc[date_idx] if date_idx in industry.index else None
            if ind_today is None:
                continue
            # 计算每个行业的均值
            df_tmp = pd.DataFrame({'ret': ret_today, 'ind': ind_today}).dropna()
            if len(df_tmp) == 0:
                continue
            ind_mean = df_tmp.groupby('ind')['ret'].transform('mean')
            ret_neutral.loc[date_idx, df_tmp.index] = (df_tmp['ret'] - ind_mean).values
        return -ret_neutral  # 反转方向
    else:
        return -ret_adj


def compute_parkinson_vol(high, low, window=20):
    """
    Parkinson 20日波动率 (1980).
    效率约为close-to-close的5倍, 利用日内高低价信息.
    方向: 负向 (低波动有alpha)
    """
    hl_ratio = np.log(high / low)
    parkinson_var = (1.0 / (4.0 * np.log(2))) * (hl_ratio ** 2)
    # 一字板处理: H==L时方差=0会扭曲rolling mean, 设为NaN
    parkinson_var = parkinson_var.where(high > low)
    vol = parkinson_var.rolling(window, min_periods=int(window * 0.7)).mean()
    vol = np.sqrt(vol)
    return -vol  # 负向


def compute_abnormal_turnover(turnover, window_short=20, window_long=120):
    """
    异常换手率 = 20日均/120日均 (Liu-Stambaugh-Yuan 2019).
    
    通过长期均值内生标准化, 大幅降低与市值的相关性.
    方向: 负向 (低异常换手=散户未发现)
    """
    avg_short = turnover.rolling(window_short, min_periods=10).mean()
    avg_long = turnover.rolling(window_long, min_periods=60).mean()
    abn = avg_short / (avg_long + 1e-10)
    return -abn


def compute_cmf_change(features, window_long=10, window_short=5):
    """
    ΔCMF_10d: CMF(10)的5日变化率.
    
    避免与入场信号I11 (CMF_20d绝对值) 直接重复.
    方向: 正向 (CMF改善中)
    """
    cmf10 = features.get('CMF_20d')  # fallback
    # 用ΔCMF: 当前CMF - 5日前CMF
    cmf_change = cmf10 - cmf10.shift(window_short)
    return cmf_change


def compute_industry_lag(close, mcap, industry, window=20, top_n=3,
                        only_when_leader_up=True):
    """
    行业内相对落后度 (基于Hou 2007).
    
    龙头 = 全市场行业内市值前top_n, 等权平均近window日涨幅.
    补涨信号 = 龙头涨幅 - 个股涨幅.
    仅当R_leader > 0 时激活 (龙头下跌时补涨逻辑不成立).
    方向: 正向 (越落后补涨空间越大)
    """
    stock_ret = close / close.shift(window) - 1
    
    # 初始化
    lag = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    
    for date_idx in close.index:
        if date_idx not in industry.index:
            continue
        
        ind_today = industry.loc[date_idx].dropna()
        mcap_today = mcap.loc[date_idx]
        ret_today = stock_ret.loc[date_idx]
        
        # 每个行业找龙头
        for ind_name, group in ind_today.groupby(ind_today):
            all_ind_stocks = group.index
            # 按市值取前top_n
            ind_mcap = mcap_today.reindex(all_ind_stocks).dropna()
            if len(ind_mcap) < top_n:
                continue
            leaders = ind_mcap.nlargest(top_n).index
            # 龙头等权涨幅
            leader_ret = ret_today.reindex(leaders).mean()
            
            if pd.isna(leader_ret):
                continue
            # 仅龙头上涨时激活
            if only_when_leader_up and leader_ret <= 0:
                continue
            
            # 计算该行业每只股票的落后度
            for stk in all_ind_stocks:
                if stk in leaders:
                    lag.loc[date_idx, stk] = 0  # 龙头本身不参与补涨
                    continue
                stk_ret = ret_today.get(stk, np.nan)
                if pd.notna(stk_ret):
                    lag.loc[date_idx, stk] = leader_ret - stk_ret
    
    return lag


def compute_log_mcap(mcap):
    """log(市值) - 仅作为中性化变量, 不直接评分."""
    return np.log(mcap.replace(0, np.nan))


# ============================================================
# 第三层: 市值中性化 + Rank评分 + 等权合成
# ============================================================

def neutralize_by_mcap(factor_vals, log_mcap):
    """
    截面OLS: factor ~ β·log_mcap, 取残差.
    仅做市值中性化 (不做行业中性化, 保留自由度).
    """
    df = pd.DataFrame({'factor': factor_vals, 'mcap': log_mcap}).dropna()
    if len(df) < 10:
        return factor_vals
    
    x = df['mcap'].values
    y = df['factor'].values
    beta = np.cov(x, y, bias=True)[0, 1] / np.var(x)
    alpha = y.mean() - beta * x.mean()
    residual = y - (alpha + beta * x)
    
    out = pd.Series(np.nan, index=factor_vals.index)
    out.loc[df.index] = residual
    return out


def rank_pct_in_pool(factor_vals):
    """池内百分位排名 (0-100)."""
    return factor_vals.rank(pct=True) * 100


def score_pool(filtered_pool, data, features, 
               use_lag_factor=True,
               factor_weights=None,
               include_reversal=True,
               include_vol=True,
               include_abn_to=True,
               include_cmf_change=True):
    """
    对通过硬约束的候选池做多因子评分 (等权合成).
    
    因子 (全部已做市值中性化, 用Rank百分位):
      1. reversal_skip1   (-10日涨幅, 行业中性化)          [include_reversal]
      2. parkinson_vol    (-20日Parkinson波动率)           [include_vol]
      3. abn_turnover     (-20/120日异常换手率)            [include_abn_to]
      4. cmf_change       (+10日CMF的5日变化)              [include_cmf_change]
      5. industry_lag     (+20日行业内相对落后度)           [use_lag_factor]
    
    Leave-one-out支持: 把任一include_*设为False即可测试该因子的边际贡献.
    
    Returns: DataFrame, 每日每股的composite score
    """
    close = data['close']
    ref_idx = close.index
    ref_col = close.columns
    
    def align(df, fill=np.nan):
        if df is None: return None
        return df.reindex(index=ref_idx, columns=ref_col).fillna(fill)
    
    high = align(data.get('high', close), fill=np.nan)
    low = align(data.get('low', close), fill=np.nan)
    turnover = align(data.get('turnover_rate', None), fill=1)
    if turnover is None: turnover = close * 0 + 1
    mcap = align(data.get('mcap', None), fill=1e10)
    if mcap is None: mcap = close * 0 + 1e10
    industry = data.get('industry_zx1', data.get('industry', None))
    if industry is not None:
        industry = industry.reindex(index=ref_idx, columns=ref_col)
    
    log_mcap = compute_log_mcap(mcap)
    
    # 预计算因子 (仅计算需要的)
    if include_reversal:
        print("    [score] 计算因子1: Skip-1day反转...")
        reversal = compute_reversal_skip1(close, industry, window=10)
    else:
        print("    [score] 跳过因子1 (reversal)...")
    
    if include_vol:
        print("    [score] 计算因子2: Parkinson波动率...")
        vol = compute_parkinson_vol(high, low, window=20)
    else:
        print("    [score] 跳过因子2 (vol)...")
    
    if include_abn_to:
        print("    [score] 计算因子3: 异常换手率...")
        abn_to = compute_abnormal_turnover(turnover, window_short=20, window_long=120)
    else:
        print("    [score] 跳过因子3 (abn_to)...")
    
    if include_cmf_change:
        print("    [score] 计算因子4: ΔCMF...")
        cmf_chg = compute_cmf_change(features, window_long=10, window_short=5)
    else:
        print("    [score] 跳过因子4 (cmf_chg)...")
    
    if use_lag_factor:
        print("    [score] 计算因子5: 行业内相对落后度...")
        lag = compute_industry_lag(close, mcap, industry, window=20, top_n=3)
    
    # 逐日评分
    scores = pd.DataFrame(np.nan, index=filtered_pool.index, columns=filtered_pool.columns)
    n_dates = len(filtered_pool.index)
    print("    [score] 开始逐日评分...")
    
    for i, date_idx in enumerate(filtered_pool.index):
        if i % 200 == 0 and i > 0:
            print(f"      ... {i}/{n_dates} dates")
        
        pool_stocks = filtered_pool.columns[filtered_pool.loc[date_idx] == 1].tolist()
        if len(pool_stocks) < 5:
            continue
        
        # 截面上的原始因子值
        log_mcap_d = log_mcap.loc[date_idx, pool_stocks]
        
        # 对每个因子: 市值中性化 -> Rank百分位
        factor_ranks = {}
        
        factor_list = []
        if include_reversal:
            factor_list.append(('reversal', reversal.loc[date_idx, pool_stocks]))
        if include_vol:
            factor_list.append(('vol', vol.loc[date_idx, pool_stocks]))
        if include_abn_to:
            factor_list.append(('abn_to', abn_to.loc[date_idx, pool_stocks]))
        if include_cmf_change:
            factor_list.append(('cmf_chg', cmf_chg.loc[date_idx, pool_stocks]))
        
        if len(factor_list) == 0:
            continue
        
        for name, factor in factor_list:
            # 市值中性化
            neutral = neutralize_by_mcap(factor, log_mcap_d)
            # Rank百分位
            factor_ranks[name] = rank_pct_in_pool(neutral)
        
        # 补涨因子 (不做中性化, 本身已经是相对值)
        if use_lag_factor:
            lag_val = lag.loc[date_idx, pool_stocks]
            factor_ranks['lag'] = rank_pct_in_pool(lag_val)
        
        # 等权合成
        if factor_weights is None:
            # 等权
            composite = pd.DataFrame(factor_ranks).mean(axis=1)
        else:
            # 自定义权重
            weighted = pd.DataFrame({k: v * factor_weights.get(k, 1.0) 
                                     for k, v in factor_ranks.items()})
            total_w = sum(factor_weights.get(k, 1.0) for k in factor_ranks)
            composite = weighted.sum(axis=1) / total_w
        
        scores.loc[date_idx, composite.index] = composite.values
    
    return scores


# ============================================================
# 第四层: 行业约束 + 选Top N
# ============================================================

def select_top_n(scores, industry, filtered_pool, n_select=15, max_per_industry=3):
    """
    选Top N, 同时限制单行业数量.
    
    做法: 按score降序, 贪心选择, 每行业最多max_per_industry只.
    """
    selected = pd.DataFrame(0.0, index=scores.index, columns=scores.columns)
    n_dates = len(scores.index)
    
    print("    [select] 选Top N with 行业约束...")
    for i, date_idx in enumerate(scores.index):
        if i % 200 == 0 and i > 0:
            print(f"      ... {i}/{n_dates} dates")
        
        # 候选: 通过硬约束且有score
        pool_mask = filtered_pool.loc[date_idx] == 1
        candidates = scores.loc[date_idx][pool_mask].dropna().sort_values(ascending=False)
        
        if len(candidates) == 0:
            continue
        
        if industry is None or max_per_industry is None:
            # 直接选Top N
            top_stocks = candidates.index[:n_select].tolist()
        else:
            # 行业约束贪心选择
            ind_today = industry.loc[date_idx] if date_idx in industry.index else None
            ind_count = {}
            top_stocks = []
            
            for stk in candidates.index:
                if len(top_stocks) >= n_select:
                    break
                if ind_today is None:
                    top_stocks.append(stk)
                    continue
                ind = ind_today.get(stk, None)
                if pd.isna(ind):
                    top_stocks.append(stk)
                    continue
                if ind_count.get(ind, 0) >= max_per_industry:
                    continue
                top_stocks.append(stk)
                ind_count[ind] = ind_count.get(ind, 0) + 1
        
        for stk in top_stocks:
            selected.loc[date_idx, stk] = 1
    
    return selected


# ============================================================
# Calendar Time PnL 评估
# ============================================================

def compute_calendar_pnl(holding, data, base_pool):
    close = data['close']
    vwap = data['vwap']
    ref_idx = close.index
    ref_col = close.columns
    
    bp = base_pool.reindex(index=ref_idx, columns=ref_col).fillna(0)
    holding_aligned = holding.reindex(index=ref_idx, columns=ref_col).fillna(0)
    vwap_aligned = vwap.reindex(index=ref_idx, columns=ref_col)
    
    mask = bp == 1
    vwap_daily_ret = (vwap_aligned / vwap_aligned.shift(1) - 1).replace([np.inf, -np.inf], np.nan)
    bm_daily = vwap_daily_ret.where(mask).mean(axis=1)
    
    n_stocks = holding_aligned.sum(axis=1)
    portfolio_ret = vwap_daily_ret.where(holding_aligned == 1).mean(axis=1)
    has_position = n_stocks > 0
    excess_ret = (portfolio_ret - bm_daily).where(has_position) * 1e4
    cum_excess = excess_ret.fillna(0).cumsum()
    
    return pd.DataFrame({
        'n_stocks': n_stocks,
        'excess_ret_bp': excess_ret,
        'cum_excess_bp': cum_excess,
    }, index=ref_idx)


def compute_drawdown(cum_series):
    running_max = cum_series.expanding().max()
    return cum_series - running_max


def print_stats(result, label):
    valid = result['excess_ret_bp'].dropna()
    n_total = len(result)
    n_active = len(valid)
    
    if n_active < 10:
        print(f"  [{label}] 有效天数不足 ({n_active}), 跳过")
        return
    
    mean_bp = valid.mean()
    std_bp = valid.std()
    sharpe = mean_bp / std_bp * np.sqrt(252) if std_bp > 0 else 0
    win_rate = (valid > 0).mean()
    cum_final = result['cum_excess_bp'].iloc[-1]
    dd = compute_drawdown(result['cum_excess_bp'])
    max_dd = dd.min()
    calmar = (mean_bp * 252) / abs(max_dd) if max_dd < 0 else 99.9
    
    active_days = result[result['n_stocks'] > 0]
    avg_stocks = active_days['n_stocks'].mean() if len(active_days) > 0 else 0
    
    print(f"  [{label}]")
    print(f"    有持仓天数: {n_active}/{n_total} ({n_active/n_total*100:.1f}%)")
    print(f"    在池股票数: 均值{avg_stocks:.1f}")
    print(f"    日均excess: {mean_bp:.2f} bp")
    print(f"    日度std: {std_bp:.2f} bp")
    print(f"    年化Sharpe: {sharpe:.2f}")
    print(f"    胜率: {win_rate*100:.1f}%")
    print(f"    累积excess: {cum_final:.1f} bp")
    print(f"    最大回撤: {max_dd:.1f} bp")
    print(f"    Calmar: {calmar:.2f}")
    
    # 最大单日亏损
    worst = valid.nsmallest(3)
    print(f"    最大单日亏损Top3:")
    for dt, val in worst.items():
        print(f"      {dt.strftime('%Y-%m-%d')}: {val:.1f} bp (在池{result.loc[dt,'n_stocks']:.0f}只)")
    
    # 年度
    print(f"    年度表现:")
    print(f"      {'年份':>6s}  {'日均excess':>10s}  {'Sharpe':>8s}  {'累积':>8s}")
    result_yr = result.copy()
    result_yr['year'] = result_yr.index.year
    for yr, grp in result_yr.groupby('year'):
        yr_exc = grp['excess_ret_bp'].dropna()
        if len(yr_exc) < 20:
            continue
        yr_mean = yr_exc.mean()
        yr_std = yr_exc.std()
        yr_sharpe = yr_mean / yr_std * np.sqrt(252) if yr_std > 0 else 0
        yr_cum = yr_exc.sum()
        print(f"      {yr:>6d}  {yr_mean:>10.2f}  {yr_sharpe:>8.2f}  {yr_cum:>8.1f}")


def plot_pnl_curves(results_dict, period_name, output_dir='/mnt/sda2/lichenchen/results', filename=None):
    """
    画多个配置的累积excess + 回撤双面板对比图.
    
    results_dict: {config_name: result_df}, 每个result_df含 cum_excess_bp 和 excess_ret_bp
    period_name : 段名 (用于图标题和文件名)
    output_dir  : 保存目录
    filename    : 文件名 (默认 pnl_{period_name}.png)
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # 无显示器环境
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("[plot] matplotlib未安装, 跳过画图")
        return None
    
    # 用默认英文字体, 抑制font警告 (所有label已是英文, 不需要中文字体)
    import warnings, logging
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
    logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
    matplotlib.rcParams['axes.unicode_minus'] = False
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True,
                                     gridspec_kw={'height_ratios': [3, 1]})
    
    # 颜色: baseline用灰色, 其他用鲜艳颜色
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    # 上面板: 累积excess
    for i, (name, result) in enumerate(results_dict.items()):
        cum = result['cum_excess_bp']
        if 'baseline' in name.lower() or 'i11_raw' in name.lower():
            color, lw, alpha = 'gray', 1.5, 0.6
        else:
            color = colors[i % len(colors)]
            lw, alpha = 2.0, 0.85
        
        # 计算Sharpe放到label里
        valid = result['excess_ret_bp'].dropna()
        if len(valid) > 0 and valid.std() > 0:
            sharpe = valid.mean() / valid.std() * np.sqrt(252)
            label = f"{name} (Sharpe={sharpe:+.2f})"
        else:
            label = name
        
        ax1.plot(cum.index, cum.values, label=label, color=color, 
                  linewidth=lw, alpha=alpha)
    
    ax1.set_ylabel('Cumulative Excess (bp)', fontsize=11)
    ax1.set_title(f'Calendar Time PnL: {period_name}', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best', fontsize=10, framealpha=0.9)
    ax1.axhline(0, color='k', linewidth=0.5, alpha=0.5)
    
    # 下面板: 回撤
    for i, (name, result) in enumerate(results_dict.items()):
        cum = result['cum_excess_bp']
        dd = compute_drawdown(cum)
        if 'baseline' in name.lower() or 'i11_raw' in name.lower():
            color, lw, alpha = 'gray', 1.0, 0.5
        else:
            color = colors[i % len(colors)]
            lw, alpha = 1.5, 0.7
        ax2.fill_between(dd.index, dd.values, 0, color=color, alpha=alpha*0.3)
        ax2.plot(dd.index, dd.values, color=color, linewidth=lw, alpha=alpha)
    
    ax2.set_ylabel('Drawdown (bp)', fontsize=11)
    ax2.set_xlabel('Date', fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(0, color='k', linewidth=0.5)
    
    # x轴日期格式
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=0)
    
    plt.tight_layout()
    
    # 保存
    if filename is None:
        filename = f"pnl_{period_name.replace('-', '_')}.png"
    import os
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"[plot] 已保存到 {save_path}")
    return save_path


# ============================================================
# P0诊断: 5个增强诊断函数
# ============================================================

def compute_extended_stats(result, label=""):
    """
    扩展统计指标 (除Sharpe外).
    返回: dict, 含Sortino, VaR, CVaR, 最长回撤天数, 恢复天数等.
    """
    valid = result['excess_ret_bp'].dropna()
    if len(valid) < 20:
        return {'label': label, 'n': 0}
    
    mean_bp = valid.mean()
    std_bp = valid.std()
    sharpe = mean_bp / std_bp * np.sqrt(252) if std_bp > 0 else 0
    
    # Sortino: 只用负收益的std
    neg_ret = valid[valid < 0]
    downside_std = neg_ret.std() if len(neg_ret) > 0 else std_bp
    sortino = mean_bp / downside_std * np.sqrt(252) if downside_std > 0 else 0
    
    # VaR/CVaR
    var_5 = valid.quantile(0.05)
    cvar_5 = valid[valid <= var_5].mean() if len(valid[valid <= var_5]) > 0 else var_5
    
    # 回撤分析
    cum = result['cum_excess_bp']
    dd = cum - cum.expanding().max()
    max_dd = dd.min()
    
    # 找到最大回撤的起止日期 + 恢复天数
    max_dd_end = dd.idxmin()
    pre_dd_cum = cum.loc[:max_dd_end]
    max_dd_start = pre_dd_cum.idxmax()  # 回撤前的最高点
    recovery_target = cum.loc[max_dd_start]
    post_dd = cum.loc[max_dd_end:]
    recovered = post_dd[post_dd >= recovery_target]
    if len(recovered) > 0:
        recovery_date = recovered.index[0]
        recovery_days = (recovery_date - max_dd_end).days
    else:
        recovery_days = -1  # 未恢复
    
    dd_duration = (max_dd_end - max_dd_start).days
    
    # 连续亏损天数 (最长连续负excess)
    losing_streak = 0
    max_losing_streak = 0
    for v in valid.values:
        if v < 0:
            losing_streak += 1
            max_losing_streak = max(max_losing_streak, losing_streak)
        else:
            losing_streak = 0
    
    # 偏度峰度
    from scipy.stats import skew, kurtosis
    skewness = skew(valid)
    kurt = kurtosis(valid)
    
    return {
        'label': label,
        'n': len(valid),
        'sharpe': sharpe,
        'sortino': sortino,
        'var_5_bp': var_5,
        'cvar_5_bp': cvar_5,
        'skew': skewness,
        'kurtosis': kurt,
        'max_dd_bp': max_dd,
        'dd_duration_days': dd_duration,
        'recovery_days': recovery_days,
        'max_losing_streak': max_losing_streak,
    }


def print_extended_stats(stats_list):
    """打印多个配置的扩展统计对比表."""
    print(f"\n{'='*100}")
    print(f"  扩展统计指标对比")
    print(f"{'='*100}")
    print(f"  {'配置':>22s}  {'Sharpe':>7s}  {'Sortino':>8s}  {'VaR5%':>8s}  {'CVaR5%':>8s}  "
          f"{'Skew':>6s}  {'Kurt':>6s}  {'最大回撤':>9s}  {'回撤天数':>8s}  {'恢复天数':>8s}  {'连续亏':>6s}")
    print(f"  {'-'*98}")
    for s in stats_list:
        if s.get('n', 0) < 20:
            print(f"  {s['label']:>22s}  数据不足")
            continue
        rec = f"{s['recovery_days']:>8d}" if s['recovery_days'] >= 0 else f"{'未恢复':>8s}"
        print(f"  {s['label']:>22s}  {s['sharpe']:>+7.2f}  {s['sortino']:>+8.2f}  "
              f"{s['var_5_bp']:>+8.1f}  {s['cvar_5_bp']:>+8.1f}  "
              f"{s['skew']:>+6.2f}  {s['kurtosis']:>+6.2f}  "
              f"{s['max_dd_bp']:>+9.1f}  {s['dd_duration_days']:>8d}  {rec}  "
              f"{s['max_losing_streak']:>6d}")


def plot_rolling_sharpe(results_dict, period_name, output_dir='/mnt/sda2/lichenchen/results', window=60):
    """画滚动N日Sharpe对比图. 解决"集中盈利还是稳定盈利"的盲区."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        return None
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 6))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    for i, (name, result) in enumerate(results_dict.items()):
        if 'baseline' in name.lower() or 'i11_raw' in name.lower():
            color, lw, alpha = 'gray', 1.5, 0.5
        else:
            color = colors[i % len(colors)]
            lw, alpha = 1.8, 0.85
        
        exc = result['excess_ret_bp']
        roll_mean = exc.rolling(window, min_periods=int(window*0.7)).mean()
        roll_std = exc.rolling(window, min_periods=int(window*0.7)).std()
        roll_sharpe = (roll_mean / roll_std * np.sqrt(252)).where(roll_std > 0)
        
        ax.plot(roll_sharpe.index, roll_sharpe.values, label=name,
                 color=color, linewidth=lw, alpha=alpha)
    
    ax.set_ylabel(f'Rolling {window}-day Sharpe', fontsize=11)
    ax.set_title(f'Rolling {window}-day Sharpe: {period_name}', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=10)
    ax.axhline(0, color='k', linewidth=0.5)
    ax.axhline(2, color='g', linewidth=0.5, linestyle='--', alpha=0.5, label='Sharpe=2')
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    plt.tight_layout()
    import os
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"rolling_sharpe_{period_name.replace('-', '_')}.png")
    plt.savefig(save_path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"[plot] 滚动Sharpe保存到 {save_path}")
    return save_path


def compute_holding_overlap(selected_dict):
    """
    计算各配置间的持仓重叠率.
    selected_dict: {config_name: selected_DataFrame}
    
    Returns: pd.DataFrame, 重叠率矩阵 (对称矩阵, 对角线=1)
    """
    config_names = list(selected_dict.keys())
    n_cfg = len(config_names)
    overlap_matrix = np.zeros((n_cfg, n_cfg))
    
    for i, name_a in enumerate(config_names):
        sel_a = selected_dict[name_a]
        for j, name_b in enumerate(config_names):
            sel_b = selected_dict[name_b]
            
            # 每天的重叠数 / 总持仓数
            common_idx = sel_a.index.intersection(sel_b.index)
            if len(common_idx) == 0:
                overlap_matrix[i, j] = 0
                continue
            
            sa = sel_a.loc[common_idx]
            sb = sel_b.loc[common_idx]
            
            # 重叠的股票 = 两边都=1
            overlap = ((sa == 1) & (sb == 1)).sum(axis=1)
            # 总持仓 = 取两边最小持仓数 (假定双边都选满)
            total = np.minimum(sa.sum(axis=1), sb.sum(axis=1))
            
            # 平均重叠率
            ratio = (overlap / total.replace(0, np.nan)).dropna()
            overlap_matrix[i, j] = ratio.mean() if len(ratio) > 0 else 0
    
    return pd.DataFrame(overlap_matrix, index=config_names, columns=config_names)


def print_overlap_matrix(overlap_df):
    """打印持仓重叠率矩阵."""
    print(f"\n{'='*80}")
    print(f"  持仓重叠率矩阵 (每日两策略持仓的重叠比例)")
    print(f"{'='*80}")
    print(f"  {'':>22s}  " + "  ".join(f"{c:>16s}" for c in overlap_df.columns))
    for idx in overlap_df.index:
        cells = []
        for c in overlap_df.columns:
            v = overlap_df.loc[idx, c]
            if idx == c:
                cells.append(f"{'1.00':>16s}")
            else:
                flag = " 🔄高重叠" if v > 0.7 else (" ⚠️低重叠" if v < 0.3 else "")
                cells.append(f"{v:>10.3f}{flag:>6s}")
        print(f"  {idx:>22s}  " + " ".join(cells))
    
    print(f"\n  解读:")
    print(f"    >0.7: 两策略选股几乎一致, Sharpe差异来自小幅不同")
    print(f"    0.3-0.7: 两策略部分重叠, 差异有实质意义")
    print(f"    <0.3: 两策略基本是不同的策略, 不能简单对比")


def compute_random_baseline(filtered_pool, data, bp, n_select=15, n_trials=100, seed=42):
    """
    池内随机选股的基准 (关键诊断).
    每天在filtered_pool里随机选n_select只跑n_trials次, 看Sharpe分布.
    用于回答: alpha到底来自池子还是因子?
    """
    print(f"\n[random_baseline] 跑{n_trials}次池内随机选股...")
    np.random.seed(seed)
    
    sharpes = []
    for trial in range(n_trials):
        random_selected = pd.DataFrame(0.0, index=filtered_pool.index, 
                                        columns=filtered_pool.columns)
        for date_idx in filtered_pool.index:
            pool_stocks = filtered_pool.columns[filtered_pool.loc[date_idx] == 1].tolist()
            if len(pool_stocks) < n_select:
                continue
            chosen = np.random.choice(pool_stocks, size=n_select, replace=False)
            random_selected.loc[date_idx, chosen] = 1
        
        result = compute_calendar_pnl(random_selected, data, bp)
        valid = result['excess_ret_bp'].dropna()
        if len(valid) > 20 and valid.std() > 0:
            sh = valid.mean() / valid.std() * np.sqrt(252)
            sharpes.append(sh)
        
        if (trial + 1) % 20 == 0:
            print(f"  ... {trial+1}/{n_trials} trials, 当前Sharpe均值={np.mean(sharpes):.2f}")
    
    return pd.Series(sharpes)


def print_random_baseline_stats(random_sharpes, strategy_sharpes_dict):
    """对比策略Sharpe vs 池内随机基准分布."""
    print(f"\n{'='*80}")
    print(f"  池内随机基准 vs 策略Sharpe (回答: alpha来自池子还是因子?)")
    print(f"{'='*80}")
    print(f"  随机选股基准 (N={len(random_sharpes)}次):")
    print(f"    均值: {random_sharpes.mean():+.2f}")
    print(f"    标准差: {random_sharpes.std():.2f}")
    print(f"    5%分位: {random_sharpes.quantile(0.05):+.2f}")
    print(f"    95%分位: {random_sharpes.quantile(0.95):+.2f}")
    print(f"    最大: {random_sharpes.max():+.2f}")
    print(f"    最小: {random_sharpes.min():+.2f}")
    
    print(f"\n  策略Sharpe对比 (高于95%分位 = 显著好于随机选):")
    p95 = random_sharpes.quantile(0.95)
    for name, sh in strategy_sharpes_dict.items():
        flag = " ✅ 显著超过随机" if sh > p95 else (" ⚠️ 不超过随机" if sh < p95 else "")
        excess = sh - random_sharpes.mean()
        print(f"    {name:>25s}: Sharpe={sh:+.2f}  超过池子均值={excess:+.2f}{flag}")


def compute_turnover_and_costs(selected, data, costs_bps=[0, 20, 30, 50]):
    """
    计算持仓换手率 + 扣交易成本后的Sharpe.
    costs_bps: 双边交易成本(bp), 0=无成本, 20=双边千二, 30=千三, 50=千五
    """
    # 持仓变化 (T-1日持有vs T日持有, 不一样就是换手)
    selected_prev = selected.shift(1).fillna(0)
    changes = (selected != selected_prev).astype(float)
    daily_turnover = changes.sum(axis=1)  # 每天换的股票数
    n_held = selected.sum(axis=1)
    
    # 换手率 = 当日变化股票数 / (2 * 当日持仓数)
    # 比如15只里换5只, 换手率 = 5/(2*15) = 16.7%
    turnover_pct = (daily_turnover / (2 * n_held.replace(0, np.nan))).fillna(0)
    
    return {
        'daily_turnover_count': daily_turnover.mean(),
        'turnover_pct': turnover_pct.mean(),
        'max_turnover_count': daily_turnover.max(),
    }


def evaluate_with_costs(result, daily_turnover_pct, costs_bps_list=[0, 6]):
    """
    扣交易成本后的Sharpe.
    
    注: 回测已用VWAP执行, 已隐含价格平均效应, 此处只扣"VWAP外的硬成本".
    
    costs_bps_list: 双边交易成本(bp), 直接传双边总成本
      0 = 纯VWAP理论值 (回测原始Sharpe)
      6 = 佣金+印花税 (双边佣金1bp + 印花税5bp, 无额外滑点)
    
    每日成本 = 双边成本 × 当日换手率(%)
    """
    valid = result['excess_ret_bp'].dropna()
    if len(valid) < 20:
        return {}
    
    results_by_cost = {}
    for cost_bps_bilateral in costs_bps_list:
        # 每日成本 = 双边成本 × 当日换手率%
        daily_cost_bp = cost_bps_bilateral * daily_turnover_pct  # bp
        net_excess = valid - daily_cost_bp
        
        mean_bp = net_excess.mean()
        std_bp = net_excess.std()
        sharpe = mean_bp / std_bp * np.sqrt(252) if std_bp > 0 else 0
        results_by_cost[cost_bps_bilateral] = {
            'sharpe': sharpe,
            'mean_bp': mean_bp,
            'daily_cost_bp': daily_cost_bp,
        }
    
    return results_by_cost


def print_turnover_and_costs(turnover_info, cost_results, label):
    """打印换手率和扣成本Sharpe."""
    print(f"\n  [{label}]")
    print(f"    平均每日换手: {turnover_info['daily_turnover_count']:.1f} 只 "
          f"(换手率 {turnover_info['turnover_pct']*100:.1f}%)")
    print(f"    扣交易成本后Sharpe:")
    print(f"      {'双边成本(bp)':>12s}  {'每日成本(bp)':>12s}  {'净Sharpe':>10s}  {'参考':>20s}")
    cost_labels = {0: '纯VWAP理论', 6: '佣金+印花税'}
    for cost_bps, info in cost_results.items():
        ref = cost_labels.get(cost_bps, '')
        print(f"      {cost_bps:>12d}  {info['daily_cost_bp']:>12.2f}  {info['sharpe']:>+10.2f}  {ref:>20s}")


# ============================================================
# 主流程
# ============================================================

def analyze_period(period_name, start, end):
    print(f"\n{'#'*90}")
    print(f"  观察池截面筛选 v2: {period_name}")
    print(f"{'#'*90}")
    
    data = load_all_daily_data(start_date=start, end_date=end)
    features = calc_all_daily_features(data)
    bp = get_base_pool(data)
    signal = define_i11_signal(features, bp)
    industry = data.get('industry_zx1', data.get('industry', None))
    
    # ---- Baseline: I11原始 (无筛选, 持有5天) ----
    in_pool_raw = pd.DataFrame(0.0, index=signal.index, columns=signal.columns)
    for lag in range(1, 6):
        in_pool_raw += signal.shift(lag).fillna(0)
    in_pool_raw = (in_pool_raw > 0).astype(float)
    raw_result = compute_calendar_pnl(in_pool_raw, data, bp)
    
    print(f"\n{'='*70}")
    print(f"  Baseline: I11原始 (无筛选, 持有5天)")
    print(f"{'='*70}")
    print_stats(raw_result, "I11_raw")
    
    # ---- 测试配置 ----
    # 默认: 只跑Sharpe 2.45 baseline (4因子)
    # 边际贡献诊断在 factor_marginal_diagnosis.py 里, 不在这里
    configs = [
        # (name, obs_window, min_mcap, n_select, use_lag, max_per_ind, include_cmf)
        ('v2_baseline_4factors', 5, 5e9, 15, False, 3, True),
    ]
    
    # 收集结果用于画图
    all_results = {'I11_raw': raw_result}
    
    for cfg in configs:
        name, obs_win, min_mcap, n_sel, use_lag, max_ind, include_cmf = cfg
        print(f"\n{'='*70}")
        print(f"  配置: {name}")
        print(f"    观察{obs_win}天 / 市值阈值{min_mcap/1e8:.0f}亿 / "
              f"选{n_sel}只 / {'含' if use_lag else '不含'}补涨因子 / "
              f"单行业≤{max_ind} / "
              f"{'含' if include_cmf else '不含'}ΔCMF")
        print(f"{'='*70}")
        
        obs_pool = build_observation_pool(signal, obs_window=obs_win)
        filtered = apply_hard_constraints(
            obs_pool, data, features, min_mcap=min_mcap,
        )
        scores = score_pool(
            filtered, data, features, 
            use_lag_factor=use_lag,
            include_cmf_change=include_cmf,
        )
        selected = select_top_n(
            scores, industry, filtered, 
            n_select=n_sel, 
            max_per_industry=max_ind if max_ind < 99 else None,
        )
        result = compute_calendar_pnl(selected, data, bp)
        print_stats(result, name)
        all_results[name] = result
    
    # ---- 画图 ----
    plot_pnl_curves(all_results, period_name)
    
    return all_results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--period', default='all')
    args = parser.parse_args()
    
    if args.period == 'all':
        for p, (s, e) in PERIODS.items():
            try:
                analyze_period(p, s, e)
            except Exception as exc:
                print(f"[ERROR] {p}: {exc}")
                import traceback; traceback.print_exc()
    else:
        s, e = PERIODS[args.period]
        analyze_period(args.period, s, e)
    
    print("\n[done]")


if __name__ == '__main__':
    main()
