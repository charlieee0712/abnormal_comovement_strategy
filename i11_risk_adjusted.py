"""
I11 风险调整评估 (Phase 1.7)
============================
目的: 回应领导反馈1 - 不能只看超额绝对值, 要看Sharpe/Calmar/IR.

原因:
    CMF阈值越低 → 触发股票越多 → 分散化降低std → 平均超额自动提升.
    这是数学效应, 不是真正的alpha提升. 
    必须用risk-adjusted指标才能揭示"每单位风险下的alpha".

评估指标:
    1. 日度excess的 mean (bp)
    2. 日度excess的 std (bp) 
    3. Sharpe = mean / std × sqrt(52/hold) [年化, 假设持有期hold天]
    4. IR (信息比率) = mean / std
    5. 最大回撤 (累积excess曲线)
    6. Calmar = 年化mean / max_drawdown
    7. 胜率 (日度excess > 0 的比例)
    8. 触发股票数分布 (min/mean/max)

比较对象:
    - I11_baseline (原始: P90 + CLV + cr5[30,60] + CVR + ir)
    - v2c (4条件: P85 + CLV + cr5[25,55] + ir)
    - final_min (3条件: P85 + cr5[25,55] + ir)  ← 推荐候选1
    - final_v2_cmf80 (3条件: P80 + cr5[25,55] + ir) ← 最高绝对超额但分散化嫌疑
    - I7 (对比baseline)

用法:
    python i11_risk_adjusted.py --period all 2>&1 | tee i11_risk_output.txt
"""

import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import (
    get_base_pool, calc_forward_returns, calc_benchmark_returns, PERIODS,
)


def define_variants_for_risk_eval(features, base_pool):
    """定义要做风险评估的所有变种."""
    bp = base_pool.reindex_like(features['intraday_ret']).fillna(0)
    mask = bp == 1
    
    def pct_in_pool(feat_name):
        f = features[feat_name].reindex_like(bp).where(mask)
        return f.rank(axis=1, pct=True)
    
    cmf_pct = pct_in_pool('CMF_20d')
    clv20_pct = pct_in_pool('CLV_20d')
    cr5_pct = pct_in_pool('cum_return_5d')
    cvr20_pct = pct_in_pool('CVR_20d')
    ir_pct = pct_in_pool('intraday_ret')
    
    signals = {}
    
    # I7 作为对比 baseline
    signals['I7_money_flow'] = (
        (cmf_pct >= 0.90) &
        (cr5_pct >= 0.50) & (cr5_pct <= 0.85) &
        (ir_pct < 0.85) &
        mask
    ).astype(float)
    
    # I11 原始 baseline (P90 + CLV + cr5[30,60] + CVR + ir)
    signals['I11_original'] = (
        (cmf_pct >= 0.90) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.30) & (cr5_pct <= 0.60) &
        (cvr20_pct >= 0.70) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # v2c (4 条件: P85+CLV+cr5[25,55]+ir, 交叉验证的最优)
    signals['v2c_4cond'] = (
        (cmf_pct >= 0.85) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.25) & (cr5_pct <= 0.55) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # final_min (3 条件: P85+cr5[25,55]+ir, 最终确认定稿)
    signals['final_min_P85'] = (
        (cmf_pct >= 0.85) &
        (cr5_pct >= 0.25) & (cr5_pct <= 0.55) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # final_v2 (3 条件: P80+cr5[25,55]+ir, 最高绝对超额但疑似分散化)
    signals['final_v2_P80'] = (
        (cmf_pct >= 0.80) &
        (cr5_pct >= 0.25) & (cr5_pct <= 0.55) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    return signals


def compute_daily_excess_series(signal, fwd_ret, bm_ret, horizon='vwap_5d'):
    """
    对单个信号, 计算每一天所有触发股票的平均excess收益序列.
    
    Returns
    -------
    excess: pd.Series  日度excess (bp), NaN表示该日无触发
    daily_count: pd.Series  日度触发股票数
    """
    sig_mask = signal == 1
    trig_ret = fwd_ret[horizon].where(sig_mask).mean(axis=1)
    bm = bm_ret[horizon]
    excess = (trig_ret - bm) * 1e4  # to bp
    daily_count = sig_mask.sum(axis=1)
    excess = excess.where(daily_count > 0)
    return excess, daily_count


def compute_max_drawdown(cum_series):
    """计算累积曲线的最大回撤 (返回bp)."""
    if len(cum_series) == 0:
        return 0
    running_max = cum_series.expanding().max()
    drawdown = cum_series - running_max
    return drawdown.min()  # 最负的值


def compute_risk_metrics(excess, daily_count, hold_days=5):
    """
    对一个信号的日度excess序列, 计算所有风险调整指标.
    
    Parameters
    ----------
    excess: pd.Series  日度excess (bp), 可含NaN
    daily_count: pd.Series  日度触发数
    hold_days: int  持有期 (影响年化因子)
    
    Returns
    -------
    dict: 所有评估指标
    """
    # 只用有触发的日子 (NaN 表示当天没触发, 该日无信号)
    valid_excess = excess.dropna()
    n_days_trig = len(valid_excess)
    n_days_total = len(excess)
    
    if n_days_trig < 10:
        return None
    
    mean_bp = valid_excess.mean()
    std_bp = valid_excess.std()
    
    # 年化Sharpe (假设每日excess近似独立, 一年约 252/hold 个非重叠期, 但我们按每天算所以用252)
    # 注意: 这里是简化处理, 因为事件研究的excess不是严格日度独立
    if std_bp > 0:
        sharpe_daily = mean_bp / std_bp
        # 年化因子: 假设250个交易日
        sharpe_annual = sharpe_daily * np.sqrt(252)
        ir = sharpe_daily  # IR = mean/std (不年化)
    else:
        sharpe_annual = 0
        ir = 0
    
    # 胜率
    win_rate = (valid_excess > 0).mean()
    
    # 累积excess曲线 (用所有日期, NaN 的日子excess=0, 表示无触发日组合回到基准)
    daily_excess_filled = excess.fillna(0)
    cum_excess = daily_excess_filled.cumsum()
    
    # 最大回撤
    max_dd = compute_max_drawdown(cum_excess)
    
    # Calmar = 年化mean / |max_drawdown|
    # 年化mean: mean_bp * 252 (按日度)
    annual_mean = mean_bp * 252
    if max_dd < 0:
        calmar = annual_mean / abs(max_dd)
    else:
        calmar = float('inf')
    
    # 触发数分布
    trig_days_count = daily_count[daily_count > 0]
    
    return {
        'mean_bp': mean_bp,
        'std_bp': std_bp,
        'sharpe_annual': sharpe_annual,
        'IR': ir,
        'win_rate': win_rate,
        'annual_mean_bp': annual_mean,
        'max_drawdown_bp': max_dd,
        'calmar': calmar,
        'cum_excess_final': cum_excess.iloc[-1] if len(cum_excess) > 0 else 0,
        'trig_days': n_days_trig,
        'total_days': n_days_total,
        'trig_avg': trig_days_count.mean() if len(trig_days_count) > 0 else 0,
        'trig_min': trig_days_count.min() if len(trig_days_count) > 0 else 0,
        'trig_max': trig_days_count.max() if len(trig_days_count) > 0 else 0,
    }


def analyze_period(period_name, start, end):
    print(f"\n{'#'*90}")
    print(f"  风险调整评估: {period_name}")
    print(f"{'#'*90}")
    
    data = load_all_daily_data(start_date=start, end_date=end)
    features = calc_all_daily_features(data)
    bp = get_base_pool(data)
    
    variants = define_variants_for_risk_eval(features, bp)
    fwd = calc_forward_returns(data, max_horizon=10)
    bm = calc_benchmark_returns(data, bp, max_horizon=10)
    
    # 对每个信号在每个持有期都算 (T+3, T+5, T+10)
    all_results = {}
    for name, sig in variants.items():
        all_results[name] = {}
        for horizon in ['vwap_3d', 'vwap_5d', 'vwap_10d']:
            excess, count = compute_daily_excess_series(sig, fwd, bm, horizon)
            hold = int(horizon.split('_')[1].replace('d', ''))
            metrics = compute_risk_metrics(excess, count, hold_days=hold)
            all_results[name][horizon] = metrics
    
    # 打印: T+5 主要指标表
    print(f"\n  【T+5 风险调整指标】")
    print(f"  {'变种':20s}  {'mean':>8s}  {'std':>8s}  {'Sharpe年化':>10s}  "
          f"{'IR':>6s}  {'胜率':>6s}  {'最大回撤':>10s}  {'Calmar':>8s}  {'日均触发':>8s}")
    print(f"  {'-'*110}")
    for name, r_by_h in all_results.items():
        r = r_by_h['vwap_5d']
        if r is None:
            continue
        print(f"  {name:20s}  "
              f"{r['mean_bp']:>8.1f}  "
              f"{r['std_bp']:>8.1f}  "
              f"{r['sharpe_annual']:>10.2f}  "
              f"{r['IR']:>6.3f}  "
              f"{r['win_rate']*100:>5.1f}%  "
              f"{r['max_drawdown_bp']:>10.1f}  "
              f"{r['calmar']:>8.2f}  "
              f"{r['trig_avg']:>8.1f}")
    
    # 打印: T+3 和 T+10 对比 (只看Sharpe)
    print(f"\n  【跨持有期 Sharpe 对比】")
    print(f"  {'变种':20s}  {'T+3 Sharpe':>12s}  {'T+5 Sharpe':>12s}  {'T+10 Sharpe':>12s}")
    print(f"  {'-'*70}")
    for name, r_by_h in all_results.items():
        s3 = r_by_h['vwap_3d']['sharpe_annual'] if r_by_h['vwap_3d'] else 0
        s5 = r_by_h['vwap_5d']['sharpe_annual'] if r_by_h['vwap_5d'] else 0
        s10 = r_by_h['vwap_10d']['sharpe_annual'] if r_by_h['vwap_10d'] else 0
        print(f"  {name:20s}  {s3:>12.2f}  {s5:>12.2f}  {s10:>12.2f}")
    
    return all_results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--period', default='all')
    args = parser.parse_args()
    
    all_period_results = {}
    
    if args.period == 'all':
        for p, (s, e) in PERIODS.items():
            try:
                all_period_results[p] = analyze_period(p, s, e)
            except Exception as exc:
                print(f"[ERROR] {p}: {exc}")
                import traceback; traceback.print_exc()
    else:
        s, e = PERIODS[args.period]
        all_period_results[args.period] = analyze_period(args.period, s, e)
    
    # 最终汇总
    if len(all_period_results) > 1:
        print(f"\n\n{'#'*100}")
        print(f"  最终汇总: 跨4段风险调整对比")
        print(f"{'#'*100}")
        
        variant_order = [
            'I7_money_flow',
            'I11_original',
            'v2c_4cond',
            'final_min_P85',
            'final_v2_P80',
        ]
        periods = list(all_period_results.keys())
        
        # 汇总表1: T+5 mean_bp (之前看的)
        print(f"\n  【T+5 平均超额 (bp)】(之前用的指标)")
        print(f"  {'变种':20s}  " + " ".join(f"{p:>10s}" for p in periods) + f"  {'平均':>9s}")
        print(f"  {'-'*90}")
        for v in variant_order:
            vals = []
            for p in periods:
                if v in all_period_results[p] and all_period_results[p][v]['vwap_5d']:
                    vals.append(all_period_results[p][v]['vwap_5d']['mean_bp'])
                else:
                    vals.append(None)
            valid = [x for x in vals if x is not None]
            if not valid:
                continue
            avg = sum(valid) / len(valid)
            print(f"  {v:20s}  " + " ".join(
                f"{x:>10.1f}" if x is not None else f"{'N/A':>10s}" for x in vals
            ) + f"  {avg:>9.1f}")
        
        # 汇总表2: T+5 Sharpe (新指标! 关键对比)
        print(f"\n  【T+5 Sharpe (年化)】(领导要求的新指标)")
        print(f"  {'变种':20s}  " + " ".join(f"{p:>10s}" for p in periods) + f"  {'平均':>9s}")
        print(f"  {'-'*90}")
        for v in variant_order:
            vals = []
            for p in periods:
                if v in all_period_results[p] and all_period_results[p][v]['vwap_5d']:
                    vals.append(all_period_results[p][v]['vwap_5d']['sharpe_annual'])
                else:
                    vals.append(None)
            valid = [x for x in vals if x is not None]
            if not valid:
                continue
            avg = sum(valid) / len(valid)
            print(f"  {v:20s}  " + " ".join(
                f"{x:>10.2f}" if x is not None else f"{'N/A':>10s}" for x in vals
            ) + f"  {avg:>9.2f}")
        
        # 汇总表3: T+5 std (标准差 - 判断是不是分散化)
        print(f"\n  【T+5 标准差 (bp)】(判断分散化效应)")
        print(f"  {'变种':20s}  " + " ".join(f"{p:>10s}" for p in periods) + f"  {'平均':>9s}")
        print(f"  {'-'*90}")
        for v in variant_order:
            vals = []
            for p in periods:
                if v in all_period_results[p] and all_period_results[p][v]['vwap_5d']:
                    vals.append(all_period_results[p][v]['vwap_5d']['std_bp'])
                else:
                    vals.append(None)
            valid = [x for x in vals if x is not None]
            if not valid:
                continue
            avg = sum(valid) / len(valid)
            print(f"  {v:20s}  " + " ".join(
                f"{x:>10.1f}" if x is not None else f"{'N/A':>10s}" for x in vals
            ) + f"  {avg:>9.1f}")
        
        # 汇总表4: Calmar
        print(f"\n  【T+5 Calmar】")
        print(f"  {'变种':20s}  " + " ".join(f"{p:>10s}" for p in periods) + f"  {'平均':>9s}")
        print(f"  {'-'*90}")
        for v in variant_order:
            vals = []
            for p in periods:
                if v in all_period_results[p] and all_period_results[p][v]['vwap_5d']:
                    c = all_period_results[p][v]['vwap_5d']['calmar']
                    vals.append(c if c != float('inf') else 99.9)
                else:
                    vals.append(None)
            valid = [x for x in vals if x is not None]
            if not valid:
                continue
            avg = sum(valid) / len(valid)
            print(f"  {v:20s}  " + " ".join(
                f"{x:>10.2f}" if x is not None else f"{'N/A':>10s}" for x in vals
            ) + f"  {avg:>9.2f}")
        
        # 汇总表5: 最大回撤
        print(f"\n  【T+5 最大回撤 (bp, 负值)】")
        print(f"  {'变种':20s}  " + " ".join(f"{p:>10s}" for p in periods) + f"  {'平均':>9s}")
        print(f"  {'-'*90}")
        for v in variant_order:
            vals = []
            for p in periods:
                if v in all_period_results[p] and all_period_results[p][v]['vwap_5d']:
                    vals.append(all_period_results[p][v]['vwap_5d']['max_drawdown_bp'])
                else:
                    vals.append(None)
            valid = [x for x in vals if x is not None]
            if not valid:
                continue
            avg = sum(valid) / len(valid)
            print(f"  {v:20s}  " + " ".join(
                f"{x:>10.1f}" if x is not None else f"{'N/A':>10s}" for x in vals
            ) + f"  {avg:>9.1f}")
        
        # 汇总表6: 日均触发
        print(f"\n  【日均触发数】")
        print(f"  {'变种':20s}  " + " ".join(f"{p:>10s}" for p in periods))
        print(f"  {'-'*80}")
        for v in variant_order:
            vals = []
            for p in periods:
                if v in all_period_results[p] and all_period_results[p][v]['vwap_5d']:
                    vals.append(all_period_results[p][v]['vwap_5d']['trig_avg'])
                else:
                    vals.append(None)
            print(f"  {v:20s}  " + " ".join(
                f"{x:>10.1f}" if x is not None else f"{'N/A':>10s}" for x in vals
            ))
    
    print("\n[done]")


if __name__ == '__main__':
    main()
