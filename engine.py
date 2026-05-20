"""
因子回测引擎 v1.0
==================
实现领导指定的因子收益率计算框架:

收益率公式 (T日):
    PnL_T = w_old × (VWAP_T / Close_{T-1} - 1)   # 旧仓位: 昨收→今VWAP
          + w_new × (Close_T / VWAP_T - 1)         # 新仓位: 今VWAP→今收

其中:
    w_old = T-2日因子生成 → T-1日交易的目标权重 (已持有)
    w_new = T-1日因子生成 → T日交易的目标权重 (今日调仓)

交易成本:
    commission = |Δw| × 0.02%  (双边万二)
    stamp_tax  = max(-Δw, 0) × 0.1%  (卖出印花税)

回测曲线:
    蓝色: 扣成本前因子收益率
    红色: 扣成本后因子收益率
    紫色: 扣成本后 - 全市场等权基准 (对市场超额)
    绿色: (后续) 个股相对中信一级行业等权基准超额
"""

import numpy as np
import pandas as pd
from typing import Optional, Literal


# ============================================================
# 1. 因子值 → 仓位权重 映射
# ============================================================

def factor_to_weight(
    factor: pd.DataFrame,
    method: Literal['rank', 'zscore', 'discrete', 'raw'] = 'rank',
    zscore_clip: float = 3.0,
) -> pd.DataFrame:
    """
    将因子值截面映射到 [-1, 1] 范围作为仓位权重。

    Parameters
    ----------
    factor : DataFrame, index=date, columns=stock_code
        原始因子值矩阵
    method : str
        'rank'     : 截面rank后线性映射到 [-1, 1] (推荐, 对异常值稳健)
        'zscore'   : 截面z-score后winsorize到 [-1, 1]
        'discrete' : 二值化, 正→+1, 负→-1, 零→0
        'raw'      : 不做处理, 假设因子值已在 [-1, 1]
    zscore_clip : float
        zscore方法的clip阈值, 默认3σ

    Returns
    -------
    DataFrame: 仓位权重矩阵, 值域 [-1, 1]
    """
    if method == 'rank':
        # 截面rank → [0, 1] → [-1, 1]
        ranked = factor.rank(axis=1, pct=True)  # [0, 1]
        weight = ranked * 2 - 1                  # [-1, 1]

    elif method == 'zscore':
        # 截面z-score → clip → 缩放到 [-1, 1]
        mean = factor.mean(axis=1)
        std = factor.std(axis=1)
        std = std.replace(0, np.nan)  # 避免除零
        z = factor.sub(mean, axis=0).div(std, axis=0)
        z = z.clip(-zscore_clip, zscore_clip)
        weight = z / zscore_clip  # [-1, 1]

    elif method == 'discrete':
        weight = np.sign(factor)

    elif method == 'raw':
        weight = factor.clip(-1, 1)

    else:
        raise ValueError(f"Unknown method: {method}")

    return weight


# ============================================================
# 2. 核心回测引擎
# ============================================================

def calc_factor_return(
    weight: pd.DataFrame,
    close: pd.DataFrame,
    vwap: pd.DataFrame,
    commission_rate: float = 0.0002,    # 万二
    stamp_tax_rate: float = 0.001,      # 千一 (卖出)
    benchmark_return: Optional[pd.Series] = None,
    mode: Literal['vwap', 'simple'] = 'vwap',
) -> pd.DataFrame:
    """
    计算因子收益率 (含/不含交易成本, 超额收益).

    两种模式:
    - 'vwap' (领导公式):
        PnL_T = w_old × (VWAP_T / Close_{T-1} - 1)    旧仓: 昨收→今VWAP
              + w_new × (Close_T / VWAP_T - 1)          新仓: 今VWAP→今收
    - 'simple' (标准close-to-close):
        PnL_T = w_new × (Close_T / Close_{T-1} - 1)    全仓: 昨收→今收

    Parameters
    ----------
    weight : DataFrame, index=date, columns=stock
        因子仓位权重矩阵, 已shift过
    close, vwap : DataFrame
    commission_rate, stamp_tax_rate : float
    benchmark_return : Series, optional
    mode : 'vwap' or 'simple'
    """
    # ---- 对齐数据 ----
    dates = weight.index.intersection(close.index).intersection(vwap.index)
    dates = dates.sort_values()
    stocks = weight.columns.intersection(close.columns).intersection(vwap.columns)

    w = weight.loc[dates, stocks]
    c = close.loc[dates, stocks]
    v = vwap.loc[dates, stocks]

    w_old = w.shift(1)
    w_new = w

    # ---- 个股PnL矩阵 ----
    if mode == 'vwap':
        ret_close_to_vwap = v / c.shift(1) - 1
        ret_vwap_to_close = c / v - 1
        stock_pnl = (w_old * ret_close_to_vwap + w_new * ret_vwap_to_close)
    else:
        # simple: close-to-close
        ret_cc = c / c.shift(1) - 1
        stock_pnl = w_new * ret_cc

    # ---- 组合收益率 ----
    w_abs_sum = w_new.abs().sum(axis=1).median()
    
    if w_abs_sum < 2.0:
        gross_return = stock_pnl.sum(axis=1)
    else:
        n_stocks = stock_pnl.notna().sum(axis=1)
        gross_return = stock_pnl.sum(axis=1) / n_stocks.replace(0, np.nan)

    # ---- 交易成本 ----
    delta_w = w_new - w_old.fillna(0)
    commission = delta_w.abs() * commission_rate
    stamp_tax = (-delta_w).clip(lower=0) * stamp_tax_rate

    if w_abs_sum < 2.0:
        total_cost = (commission + stamp_tax).sum(axis=1)
    else:
        n_stocks_cost = delta_w.notna().sum(axis=1)
        total_cost = (commission + stamp_tax).sum(axis=1) / n_stocks_cost.replace(0, np.nan)

    # ---- 净收益 ----
    net_return = gross_return - total_cost

    # ---- 构建结果DataFrame ----
    result = pd.DataFrame(index=dates)
    result['gross_return'] = gross_return
    result['cost'] = total_cost
    result['net_return'] = net_return

    # ---- 基准 & 超额 ----
    if benchmark_return is not None:
        bm = benchmark_return.reindex(dates).fillna(0)
        result['benchmark_return'] = bm
        result['excess_return'] = net_return - bm
    else:
        result['benchmark_return'] = 0.0
        result['excess_return'] = net_return

    # ---- 累积收益 ----
    result['cum_gross'] = (1 + result['gross_return'].fillna(0)).cumprod() - 1
    result['cum_net'] = (1 + result['net_return'].fillna(0)).cumprod() - 1
    result['cum_excess'] = (1 + result['excess_return'].fillna(0)).cumprod() - 1

    # 去掉首日 (shift导致NaN)
    result = result.iloc[1:]

    return result


# ============================================================
# 3. 全市场等权基准
# ============================================================

def calc_market_benchmark(
    close: pd.DataFrame,
    vwap: pd.DataFrame,
    method: Literal['vwap_to_vwap', 'close_to_close'] = 'close_to_close',
) -> pd.Series:
    """
    计算全市场等权基准收益率.

    Parameters
    ----------
    close : DataFrame
        收盘价矩阵
    vwap : DataFrame
        VWAP矩阵
    method : str
        'close_to_close' : Close_T / Close_{T-1} - 1
        'vwap_to_vwap'   : VWAP_{T+1} / VWAP_T - 1 (for excess calc)

    Returns
    -------
    Series: 日度等权基准收益率
    """
    if method == 'close_to_close':
        stock_ret = close / close.shift(1) - 1
    else:
        stock_ret = vwap.shift(-1) / vwap - 1

    # 等权平均
    benchmark = stock_ret.mean(axis=1)
    return benchmark


# ============================================================
# 4. 因子评价指标
# ============================================================

def calc_factor_metrics(result: pd.DataFrame, ann_factor: int = 252) -> dict:
    """
    计算因子回测的常用评价指标.

    Parameters
    ----------
    result : DataFrame
        calc_factor_return 的输出
    ann_factor : int
        年化因子, 日频=252

    Returns
    -------
    dict: 各项指标
    """
    metrics = {}

    for prefix, col in [('gross', 'gross_return'), ('net', 'net_return'), ('excess', 'excess_return')]:
        r = result[col].dropna()
        if len(r) == 0:
            continue

        ann_ret = r.mean() * ann_factor
        ann_vol = r.std() * np.sqrt(ann_factor)
        sharpe = ann_ret / ann_vol if ann_vol > 0 else np.nan
        max_dd = ((1 + r).cumprod().cummax() - (1 + r).cumprod()).max()
        calmar = ann_ret / max_dd if max_dd > 0 else np.nan
        win_rate = (r > 0).mean()
        avg_cost = result['cost'].mean() * ann_factor if 'cost' in result else 0

        metrics[f'{prefix}_ann_return'] = ann_ret
        metrics[f'{prefix}_ann_vol'] = ann_vol
        metrics[f'{prefix}_sharpe'] = sharpe
        metrics[f'{prefix}_max_drawdown'] = max_dd
        metrics[f'{prefix}_calmar'] = calmar
        metrics[f'{prefix}_win_rate'] = win_rate

    metrics['avg_ann_cost'] = result['cost'].mean() * ann_factor
    metrics['avg_daily_turnover'] = result['cost'].mean() / (0.0002 + 0.0005) if result['cost'].mean() > 0 else 0
    metrics['avg_ann_turnover'] = metrics['avg_daily_turnover'] * ann_factor

    return metrics


# ============================================================
# 5. 因子预测力指标 (IC替代)
# ============================================================

def calc_factor_predictiveness(
    factor: pd.DataFrame,
    forward_return: pd.DataFrame,
) -> pd.DataFrame:
    """
    计算因子预测力指标 (领导说的IC替代方案).

    因子收益率 = 因子值(压缩后) × 下一期收益率  → 替代时序IC
    预测波动率 = |因子值 × 下一期收益率|          → 类比IC绝对值

    Parameters
    ----------
    factor : DataFrame
        因子值矩阵 (已压缩到[-1,1])
    forward_return : DataFrame
        下一期收益率矩阵

    Returns
    -------
    DataFrame with columns:
        'factor_return'       : 因子值×下一期收益率的截面均值 (替代IC)
        'abs_factor_return'   : |因子值×下一期收益率|的截面均值 (替代|IC|)
        'predicted_vol'       : 预测波动率
        'cum_factor_return'   : 累积因子收益率
    """
    # 对齐
    dates = factor.index.intersection(forward_return.index)
    stocks = factor.columns.intersection(forward_return.columns)
    f = factor.loc[dates, stocks]
    r = forward_return.loc[dates, stocks]

    # 因子值 × 下一期收益率
    cross_product = f * r

    result = pd.DataFrame(index=dates)
    result['factor_return'] = cross_product.mean(axis=1)
    result['abs_factor_return'] = cross_product.abs().mean(axis=1)
    result['predicted_vol'] = cross_product.abs().mean(axis=1)
    result['cum_factor_return'] = result['factor_return'].cumsum()

    return result
