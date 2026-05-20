"""
因子边际贡献诊断
================
两个诊断合并:
  Part 1: 4因子在I11池内的截面Rank相关性矩阵 (快, 2-3分钟)
          → 判断因子是否正交, 相关性高则边际贡献低
  Part 2: Leave-one-out边际贡献回测 (慢, ~40分钟, 只跑2024-2026段)
          → 每次删一个因子, 看Sharpe变化
          → 这是判断"每个因子真实价值"的黄金标准

设计教训 (P0失败 + 3因子删CMF暴跌4.77 Sharpe):
  - 独立IC高≠Sharpe贡献高
  - 独立IC低≠组合中无用 (ΔCMF的例子)
  - 唯一真正可信的判断方式: leave-one-out回测

用法:
    python factor_marginal_diagnosis.py --period 2024-2026 2>&1 | tee factor_marginal_2426.txt
"""

import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import get_base_pool, PERIODS
from pool_screening_v2 import (
    define_i11_signal,
    build_observation_pool,
    apply_hard_constraints,
    score_pool,
    select_top_n,
    compute_calendar_pnl,
    print_stats,
    compute_reversal_skip1,
    compute_parkinson_vol,
    compute_abnormal_turnover,
    compute_cmf_change,
    compute_log_mcap,
    neutralize_by_mcap,
    rank_pct_in_pool,
)


# ============================================================
# Part 1: 截面相关性矩阵
# ============================================================

def compute_factor_correlation_matrix(filtered_pool, data, features,
                                       sample_size=100):
    """
    在I11池内, 每日计算4因子之间的Rank截面相关性, 再跨时间取均值.
    sample_size: 采样多少个交易日来算 (加速, 不影响统计结果)
    """
    close = data['close']
    ref_idx = close.index
    ref_col = close.columns
    
    def align(df, fill=np.nan):
        if df is None: return None
        return df.reindex(index=ref_idx, columns=ref_col).fillna(fill)
    
    high = align(data['high'])
    low = align(data['low'])
    turnover = align(data.get('turnover_rate'), fill=1)
    mcap = align(data.get('mcap'), fill=1e10)
    industry = data.get('industry_zx1', data.get('industry'))
    if industry is not None:
        industry = industry.reindex(index=ref_idx, columns=ref_col)
    log_mcap = compute_log_mcap(mcap)
    
    print("\n[corr] 计算4因子...")
    reversal = compute_reversal_skip1(close, industry, window=10)
    vol = compute_parkinson_vol(high, low, window=20)
    abn_to = compute_abnormal_turnover(turnover, window_short=20, window_long=120)
    cmf_chg = compute_cmf_change(features, window_long=10, window_short=5)
    
    # 采样交易日 (有触发股票的)
    active_dates = filtered_pool.index[filtered_pool.sum(axis=1) >= 20]
    if len(active_dates) > sample_size:
        sampled_dates = active_dates[::len(active_dates)//sample_size][:sample_size]
    else:
        sampled_dates = active_dates
    
    print(f"[corr] 采样{len(sampled_dates)}个交易日计算相关性...")
    
    # 逐日计算相关性, 然后跨时间均值
    corr_list = []  # list of 4x4 DataFrames
    
    for date_idx in sampled_dates:
        pool_stocks = filtered_pool.columns[filtered_pool.loc[date_idx] == 1].tolist()
        if len(pool_stocks) < 20:
            continue
        
        log_mcap_d = log_mcap.loc[date_idx, pool_stocks]
        
        # 4因子值 (已做市值中性化 + Rank百分位, 与score_pool一致)
        factor_dict = {}
        for name, raw in [
            ('reversal', reversal.loc[date_idx, pool_stocks]),
            ('vol', vol.loc[date_idx, pool_stocks]),
            ('abn_to', abn_to.loc[date_idx, pool_stocks]),
            ('cmf_chg', cmf_chg.loc[date_idx, pool_stocks]),
        ]:
            neutral = neutralize_by_mcap(raw, log_mcap_d)
            factor_dict[name] = rank_pct_in_pool(neutral)
        
        df = pd.DataFrame(factor_dict).dropna()
        if len(df) < 10:
            continue
        
        corr = df.corr(method='spearman')
        corr_list.append(corr)
    
    if not corr_list:
        print("[corr] 无可用数据")
        return None
    
    # 跨时间均值
    avg_corr = pd.concat(corr_list).groupby(level=0).mean()
    avg_corr = avg_corr.reindex(index=['reversal', 'vol', 'abn_to', 'cmf_chg'],
                                 columns=['reversal', 'vol', 'abn_to', 'cmf_chg'])
    
    return avg_corr, len(corr_list)


def print_corr_matrix(corr, n_days):
    """漂亮打印相关性矩阵."""
    print(f"\n{'='*70}")
    print(f"  4因子截面Rank相关性矩阵 (基于{n_days}个交易日平均)")
    print(f"{'='*70}")
    
    print(f"  {'因子':>10s}  " + "  ".join(f"{c:>10s}" for c in corr.columns))
    for idx in corr.index:
        cells = []
        for c in corr.columns:
            v = corr.loc[idx, c]
            if idx == c:
                cells.append(f"{'1.00':>10s}")
            elif abs(v) > 0.5:
                cells.append(f"{v:>+10.3f}*")  # 高相关标星
            else:
                cells.append(f"{v:>+10.3f} ")
        print(f"  {idx:>10s}  " + " ".join(cells))
    
    print(f"\n  (带*表示相关系数|ρ|>0.5, 需警惕因子冗余)")
    
    # 找出最相关的对
    pairs = []
    factors = list(corr.index)
    for i, a in enumerate(factors):
        for b in factors[i+1:]:
            pairs.append((a, b, corr.loc[a, b]))
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    
    print(f"\n  按|ρ|排序:")
    for a, b, rho in pairs:
        flag = " ⚠️ 高相关" if abs(rho) > 0.5 else (" (弱相关)" if abs(rho) < 0.2 else "")
        print(f"    {a:>10s} <-> {b:>10s}: {rho:>+.3f}{flag}")


# ============================================================
# Part 2: Leave-One-Out边际贡献回测
# ============================================================

def run_leave_one_out(period_name, start, end):
    print(f"\n{'#'*90}")
    print(f"  Leave-One-Out 边际贡献诊断: {period_name}")
    print(f"{'#'*90}")
    
    # ---- 加载数据 ----
    data = load_all_daily_data(start_date=start, end_date=end)
    features = calc_all_daily_features(data)
    bp = get_base_pool(data)
    signal = define_i11_signal(features, bp)
    industry = data.get('industry_zx1', data.get('industry'))
    if industry is not None:
        industry = industry.reindex(index=data['close'].index, 
                                     columns=data['close'].columns)
    
    # 观察池 + 硬约束 (统一, 不重复算)
    obs_pool = build_observation_pool(signal, obs_window=5)
    filtered = apply_hard_constraints(obs_pool, data, features, min_mcap=5e9)
    
    print(f"\n  观察池规模: 均值{filtered.sum(axis=1).mean():.1f} 只/天")
    
    # ============================================================
    # Part 1: 相关性矩阵 (基础信息, 快)
    # ============================================================
    corr_result = compute_factor_correlation_matrix(filtered, data, features)
    if corr_result is not None:
        avg_corr, n_days = corr_result
        print_corr_matrix(avg_corr, n_days)
    
    # ============================================================
    # Part 2: Leave-one-out回测
    # ============================================================
    print(f"\n{'#'*90}")
    print(f"  Leave-One-Out 回测开始 (5个配置)")
    print(f"{'#'*90}")
    
    configs = [
        # (name, include_reversal, include_vol, include_abn_to, include_cmf_change)
        ('base_4factors',   True,  True,  True,  True),   # 基准: 4因子
        ('drop_reversal',   False, True,  True,  True),   # 删反转
        ('drop_vol',        True,  False, True,  True),   # 删波动率
        ('drop_abn_to',     True,  True,  False, True),   # 删换手率
        ('drop_cmf_chg',    True,  True,  True,  False),  # 删ΔCMF (已知暴跌)
    ]
    
    results = {}
    selected_dict = {}  # 保存selected DataFrame, 用于持仓重叠率分析
    
    for cfg in configs:
        name, inc_rev, inc_vol, inc_abn, inc_cmf = cfg
        n_factors = sum([inc_rev, inc_vol, inc_abn, inc_cmf])
        label = ",".join([f for f, inc in [
            ('rev', inc_rev), ('vol', inc_vol), ('abn', inc_abn), ('cmf', inc_cmf)
        ] if inc])
        
        print(f"\n{'='*70}")
        print(f"  配置: {name} ({n_factors}因子: {label})")
        print(f"{'='*70}")
        
        scores = score_pool(
            filtered, data, features,
            use_lag_factor=False,
            include_reversal=inc_rev,
            include_vol=inc_vol,
            include_abn_to=inc_abn,
            include_cmf_change=inc_cmf,
        )
        selected = select_top_n(scores, industry, filtered, 
                                 n_select=15, max_per_industry=3)
        result = compute_calendar_pnl(selected, data, bp)
        print_stats(result, name)
        
        # 计算Sharpe
        valid = result['excess_ret_bp'].dropna()
        mean_bp = valid.mean() if len(valid) > 0 else 0
        std_bp = valid.std() if len(valid) > 0 else 1
        sharpe = mean_bp / std_bp * np.sqrt(252) if std_bp > 0 else 0
        results[name] = {'sharpe': sharpe, 'mean_bp': mean_bp, 'result_df': result,
                          'selected': selected}
        selected_dict[name] = selected
    
    # ============================================================
    # P0诊断: 5个增强诊断
    # ============================================================
    from pool_screening_v2 import (
        plot_pnl_curves, plot_rolling_sharpe,
        compute_extended_stats, print_extended_stats,
        compute_holding_overlap, print_overlap_matrix,
        compute_random_baseline, print_random_baseline_stats,
        compute_turnover_and_costs, evaluate_with_costs,
        print_turnover_and_costs,
    )
    
    print(f"\n{'#'*90}")
    print(f"  P0诊断 (1/5): 累积PnL+回撤曲线图")
    print(f"{'#'*90}")
    plot_dict = {name: r['result_df'] for name, r in results.items()}
    try:
        plot_pnl_curves(plot_dict, f"leave_one_out_{period_name}")
    except Exception as e:
        print(f"[plot] 跳过: {e}")
    
    print(f"\n{'#'*90}")
    print(f"  P0诊断 (2/5): 滚动60日Sharpe图 (识别稳定盈利vs集中盈利)")
    print(f"{'#'*90}")
    try:
        plot_rolling_sharpe(plot_dict, f"leave_one_out_{period_name}", window=60)
    except Exception as e:
        print(f"[plot] 跳过: {e}")
    
    print(f"\n{'#'*90}")
    print(f"  P0诊断 (3/5): 扩展统计指标 (Sortino/VaR/CVaR/回撤天数/恢复天数等)")
    print(f"{'#'*90}")
    try:
        stats_list = [compute_extended_stats(r['result_df'], name) 
                      for name, r in results.items()]
        print_extended_stats(stats_list)
    except Exception as e:
        print(f"[ext_stats] 跳过: {e}")
        import traceback; traceback.print_exc()
    
    print(f"\n{'#'*90}")
    print(f"  P0诊断 (4/5): 持仓重叠率矩阵 (回答: 删因子后是否还是同一策略?)")
    print(f"{'#'*90}")
    try:
        overlap_df = compute_holding_overlap(selected_dict)
        print_overlap_matrix(overlap_df)
    except Exception as e:
        print(f"[overlap] 跳过: {e}")
        import traceback; traceback.print_exc()
    
    print(f"\n{'#'*90}")
    print(f"  P0诊断 (5/5): 换手率 + 扣交易成本Sharpe (实盘可行性检验)")
    print(f"{'#'*90}")
    try:
        for name, r in results.items():
            turnover_info = compute_turnover_and_costs(r['selected'], data)
            cost_results = evaluate_with_costs(r['result_df'], 
                                                 turnover_info['turnover_pct'])
            print_turnover_and_costs(turnover_info, cost_results, name)
    except Exception as e:
        print(f"[costs] 跳过: {e}")
        import traceback; traceback.print_exc()
    
    print(f"\n{'#'*90}")
    print(f"  P0诊断额外: 池内随机基准 (回答: alpha来自池子还是因子?)")
    print(f"{'#'*90}")
    try:
        random_sharpes = compute_random_baseline(filtered, data, bp, 
                                                   n_select=15, n_trials=100)
        strategy_sharpes = {name: r['sharpe'] for name, r in results.items()}
        print_random_baseline_stats(random_sharpes, strategy_sharpes)
    except Exception as e:
        print(f"[random] 跳过: {e}")
        import traceback; traceback.print_exc()
    
    # ---- 汇总边际贡献 ----
    print(f"\n{'='*90}")
    print(f"  边际贡献汇总 (单位: 年化Sharpe)")
    print(f"{'='*90}")
    
    base_sharpe = results['base_4factors']['sharpe']
    print(f"  基准 (4因子全开): Sharpe = {base_sharpe:+.2f}")
    print()
    print(f"  {'删除因子':>15s}  {'剩余Sharpe':>12s}  {'边际贡献':>12s}  {'评价':>20s}")
    print(f"  {'-'*75}")
    
    for factor_key, display_name in [
        ('drop_reversal', 'Reversal'),
        ('drop_vol',      'Parkinson Vol'),
        ('drop_abn_to',   'Abn Turnover'),
        ('drop_cmf_chg',  'ΔCMF'),
    ]:
        drop_sharpe = results[factor_key]['sharpe']
        marginal = base_sharpe - drop_sharpe  # 该因子的边际贡献
        
        if marginal > 1.0:
            verdict = "🔥 关键因子"
        elif marginal > 0.3:
            verdict = "✅ 有贡献"
        elif marginal > -0.1:
            verdict = "🟡 接近零"
        else:
            verdict = "❌ 实际有害"
        
        print(f"  {display_name:>15s}  {drop_sharpe:>+12.2f}  {marginal:>+12.2f}  {verdict:>20s}")
    
    print()
    print(f"  (边际贡献 = 基准Sharpe - 删除后Sharpe)")
    print(f"  (值越大越重要)")
    
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--period', default='2024-2026',
                        help="段名 (e.g. 2024-2026) 或 'all' 跑全4段")
    args = parser.parse_args()
    
    if args.period == 'all':
        all_period_results = {}
        for p, (s, e) in PERIODS.items():
            try:
                print(f"\n\n{'★'*90}")
                print(f"  开始处理: {p}")
                print(f"{'★'*90}")
                all_period_results[p] = run_leave_one_out(p, s, e)
            except Exception as exc:
                print(f"[ERROR] {p}: {exc}")
                import traceback; traceback.print_exc()
        
        # ---- 跨段汇总边际贡献 ----
        if len(all_period_results) >= 2:
            print(f"\n\n{'#'*90}")
            print(f"  跨段边际贡献汇总 (单位: 年化Sharpe)")
            print(f"{'#'*90}")
            
            periods_list = list(all_period_results.keys())
            
            # Baseline跨段
            print(f"\n  Baseline (4因子全开) 跨段Sharpe:")
            for p in periods_list:
                bs = all_period_results[p].get('base_4factors', {}).get('sharpe', 0)
                print(f"    {p}: {bs:>+6.2f}")
            
            # 每个因子边际贡献跨段
            print(f"\n  {'删除因子':>15s}  " + "  ".join(f"{p:>11s}" for p in periods_list) + f"  {'均值':>8s}  {'符号一致':>8s}")
            print(f"  {'-'*88}")
            
            for factor_key, display_name in [
                ('drop_reversal', 'Reversal'),
                ('drop_vol',      'Parkinson Vol'),
                ('drop_abn_to',   'Abn Turnover'),
                ('drop_cmf_chg',  'ΔCMF'),
            ]:
                marginal_by_period = {}
                for p in periods_list:
                    res = all_period_results[p]
                    base_sh = res.get('base_4factors', {}).get('sharpe', 0)
                    drop_sh = res.get(factor_key, {}).get('sharpe', 0)
                    marginal_by_period[p] = base_sh - drop_sh
                
                vals = list(marginal_by_period.values())
                avg = sum(vals) / len(vals) if vals else 0
                sign_consistent = "✓" if (all(v > 0 for v in vals) or all(v < 0 for v in vals)) else "✗"
                
                cells = "  ".join(f"{v:>+11.2f}" for v in vals)
                print(f"  {display_name:>15s}  {cells}  {avg:>+8.2f}  {sign_consistent:>8s}")
            
            print(f"\n  (边际贡献 = baseline Sharpe - 删除该因子后Sharpe)")
            print(f"  (符号一致表示因子在所有段都有相同的贡献方向)")
    else:
        s, e = PERIODS[args.period]
        run_leave_one_out(args.period, s, e)
    
    print("\n[done]")


if __name__ == '__main__':
    main()
