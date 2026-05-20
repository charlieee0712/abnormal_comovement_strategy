"""
I11 Calendar Time PnL (工作2)
============================
目的: 从事件时间(event time)转到日历时间(calendar time),
     看I11在真实时间线上的每日组合收益曲线.

回应领导反馈2: "还要拉平到时间轴上看某个时间点具体走势,
             比如2024年二月1号小票崩盘, 我们可以看到小票暴露"

方法:
    每一天, 找出"当前在池里"的所有股票 (过去5天内触发的),
    计算它们的等权组合当日收益, 减去基准收益, 得到每日excess.
    然后画累积PnL曲线.

    这不是完整的Phase 2回测 (不考虑换手/交易成本/仓位调整),
    但能看到时间维度的风险暴露和集中风险.

用法:
    python i11_calendar_pnl.py --period all 2>&1 | tee i11_calendar_output.txt
"""

import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import get_base_pool, PERIODS


def define_i11_final(features, base_pool):
    """I11最终定稿 (P80版本, 风险调整后最优)."""
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


def compute_calendar_pnl(signal, data, base_pool, hold_days=5):
    """
    计算日历时间的每日组合PnL.
    
    逻辑:
        - T日收盘后信号触发 → T+1日以VWAP买入 → 持有hold_days天
        - 所以T日触发的股票, 在T+1到T+hold_days这些日历日里都"在池中"
        - 每个日历日D, 找出所有"在池中"的股票, 算等权VWAP日收益
        - 减去基准(基础池等权VWAP日收益), 得到当日excess
    
    Returns
    -------
    result: DataFrame with columns:
        date, n_stocks, portfolio_ret, benchmark_ret, excess_ret, cum_excess
    """
    close = data['close']
    vwap = data['vwap']
    bp = base_pool.reindex_like(close).fillna(0)
    mask = bp == 1
    
    dates = close.index
    
    # VWAP日收益 = VWAP_t / VWAP_{t-1} - 1
    vwap_daily_ret = (vwap / vwap.shift(1) - 1).replace([np.inf, -np.inf], np.nan)
    
    # 基准: 基础池等权VWAP日收益
    bm_daily = vwap_daily_ret.where(mask).mean(axis=1)
    
    # 对每个日历日, 找"在池中"的股票
    # 股票在池中 = 过去hold_days天内任何一天触发过
    # signal[t] = 1 表示T日收盘触发, T+1日买入
    # 所以signal[t]=1 → 股票在 t+1, t+2, ..., t+hold_days 这些日子里"在池中"
    
    # 构建 "在池中" 的矩阵: in_pool[d, s] = 1 if stock s is in pool on day d
    in_pool = pd.DataFrame(0.0, index=dates, columns=close.columns)
    for lag in range(1, hold_days + 1):
        # signal.shift(lag) 把T日的信号shift到T+lag日
        in_pool += signal.shift(lag).fillna(0)
    
    # in_pool > 0 表示在池中 (可能被多次触发, 但权重相同)
    in_pool = (in_pool > 0).astype(float)
    
    # 每日组合收益 = 在池股票的等权VWAP日收益
    portfolio_ret = vwap_daily_ret.where(in_pool == 1).mean(axis=1)
    
    # 每日在池股票数
    n_stocks = in_pool.sum(axis=1)
    
    # 只看有持仓的日子
    has_position = n_stocks > 0
    
    # 每日excess = portfolio_ret - benchmark_ret
    excess_ret = (portfolio_ret - bm_daily).where(has_position) * 1e4  # bp
    
    # 累积excess
    cum_excess = excess_ret.fillna(0).cumsum()
    
    result = pd.DataFrame({
        'n_stocks': n_stocks,
        'portfolio_ret_bp': portfolio_ret * 1e4,
        'benchmark_ret_bp': bm_daily * 1e4,
        'excess_ret_bp': excess_ret,
        'cum_excess_bp': cum_excess,
    }, index=dates)
    
    return result


def compute_drawdown(cum_series):
    """计算回撤序列."""
    running_max = cum_series.expanding().max()
    dd = cum_series - running_max
    return dd


def analyze_period(period_name, start, end):
    print(f"\n{'#'*90}")
    print(f"  Calendar Time PnL: {period_name}")
    print(f"{'#'*90}")
    
    data = load_all_daily_data(start_date=start, end_date=end)
    features = calc_all_daily_features(data)
    bp = get_base_pool(data)
    signal = define_i11_final(features, bp)
    
    # 计算不同持有期的calendar PnL
    for hold in [5, 10]:
        print(f"\n{'='*80}")
        print(f"  持有期: {hold}天")
        print(f"{'='*80}")
        
        result = compute_calendar_pnl(signal, data, bp, hold_days=hold)
        
        # 基本统计
        valid = result['excess_ret_bp'].dropna()
        n_total = len(result)
        n_active = len(valid)
        
        mean_excess = valid.mean()
        std_excess = valid.std()
        sharpe = mean_excess / std_excess * np.sqrt(252) if std_excess > 0 else 0
        win_rate = (valid > 0).mean()
        
        cum_final = result['cum_excess_bp'].iloc[-1]
        dd = compute_drawdown(result['cum_excess_bp'])
        max_dd = dd.min()
        calmar = (mean_excess * 252) / abs(max_dd) if max_dd < 0 else 99.9
        
        # 在池股票数
        active_days = result[result['n_stocks'] > 0]
        avg_stocks = active_days['n_stocks'].mean()
        max_stocks = active_days['n_stocks'].max()
        min_stocks = active_days['n_stocks'].min()
        
        print(f"\n  日历时间统计:")
        print(f"    总交易日: {n_total}")
        print(f"    有持仓天数: {n_active} ({n_active/n_total*100:.1f}%)")
        print(f"    在池股票数: 均值{avg_stocks:.1f}, 范围[{min_stocks:.0f}, {max_stocks:.0f}]")
        print(f"\n  收益指标:")
        print(f"    日均excess: {mean_excess:.2f} bp")
        print(f"    日度std: {std_excess:.2f} bp")
        print(f"    年化Sharpe: {sharpe:.2f}")
        print(f"    胜率: {win_rate*100:.1f}%")
        print(f"    累积excess: {cum_final:.1f} bp")
        print(f"    最大回撤: {max_dd:.1f} bp")
        print(f"    Calmar: {calmar:.2f}")
        
        # 最大单日亏损 top5
        print(f"\n  最大单日亏损 (excess, bp):")
        worst_days = valid.nsmallest(5)
        for dt, val in worst_days.items():
            n_stk = result.loc[dt, 'n_stocks']
            bm = result.loc[dt, 'benchmark_ret_bp']
            print(f"    {dt.strftime('%Y-%m-%d')}: {val:>8.1f} bp  "
                  f"(在池{n_stk:.0f}只, 基准{bm:.1f}bp)")
        
        # 最大单日盈利 top5
        print(f"\n  最大单日盈利 (excess, bp):")
        best_days = valid.nlargest(5)
        for dt, val in best_days.items():
            n_stk = result.loc[dt, 'n_stocks']
            bm = result.loc[dt, 'benchmark_ret_bp']
            print(f"    {dt.strftime('%Y-%m-%d')}: {val:>8.1f} bp  "
                  f"(在池{n_stk:.0f}只, 基准{bm:.1f}bp)")
        
        # 最大回撤期间
        dd_end_idx = dd.idxmin()
        # 找回撤起点 (从peak到trough)
        cum_up_to_trough = result['cum_excess_bp'].loc[:dd_end_idx]
        dd_start_idx = cum_up_to_trough.idxmax()
        dd_duration = (dd_end_idx - dd_start_idx).days
        print(f"\n  最大回撤期间: {dd_start_idx.strftime('%Y-%m-%d')} → "
              f"{dd_end_idx.strftime('%Y-%m-%d')} ({dd_duration}天)")
        print(f"    回撤幅度: {max_dd:.1f} bp")
        
        # 按年分组看年度表现
        print(f"\n  年度表现:")
        print(f"    {'年份':>6s}  {'日均excess':>12s}  {'年化Sharpe':>12s}  {'年度累积':>12s}  {'最大回撤':>12s}")
        result['year'] = result.index.year
        for yr, grp in result.groupby('year'):
            yr_excess = grp['excess_ret_bp'].dropna()
            if len(yr_excess) < 20:
                continue
            yr_mean = yr_excess.mean()
            yr_std = yr_excess.std()
            yr_sharpe = yr_mean / yr_std * np.sqrt(252) if yr_std > 0 else 0
            yr_cum = yr_excess.sum()
            yr_dd = compute_drawdown(grp['cum_excess_bp'] - grp['cum_excess_bp'].iloc[0])
            yr_max_dd = yr_dd.min()
            print(f"    {yr:>6d}  {yr_mean:>12.2f}  {yr_sharpe:>12.2f}  {yr_cum:>12.1f}  {yr_max_dd:>12.1f}")
    
    return result


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
