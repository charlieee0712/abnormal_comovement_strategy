"""
I11池内因子IC诊断 (保守版参数扫描)
===================================
目标: 在我们真实的"I11池+5日持有"场景下, 找到每个因子的最优参数.
避免P0覆辙: 不照搬研报全A月频最优, 用我们自己的数据说话.

诊断对象:
    - 反转 (skip-1day, 行业中性化 vs 不做): 窗口[5,10,20]
    - Parkinson波动率: 窗口[10,20,30]
    - Close-to-close波动率: 窗口[10,20,30]
    - 异常换手率: 长短比[5/60, 10/60, 20/120, 60/250]
    - 均值换手率: 窗口[5,20,60]
    - ΔCMF (基础版): [5日变化]
    共 19 参数 × 4 段

收益对齐方式B (calendar-time):
    对每只触发股票, 计算其"未来5日持有期内每天的VWAP超额收益"
    和策略Sharpe的来源完全一致

用法:
    python factor_ic_diagnosis.py --period all 2>&1 | tee factor_ic_all.txt
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
    compute_log_mcap,
)


# ============================================================
# 因子计算: 参数化版本, 供扫描
# ============================================================

def compute_reversal(close, industry, window, do_industry_neu=True):
    """Skip-1day反转. do_industry_neu控制是否做行业中性化."""
    ret_adj = close.shift(1) / close.shift(window + 1) - 1
    
    if not do_industry_neu or industry is None:
        return -ret_adj  # 负向
    
    ret_neutral = ret_adj.copy()
    for date_idx in ret_adj.index:
        ret_today = ret_adj.loc[date_idx]
        ind_today = industry.loc[date_idx] if date_idx in industry.index else None
        if ind_today is None:
            continue
        df_tmp = pd.DataFrame({'ret': ret_today, 'ind': ind_today}).dropna()
        if len(df_tmp) == 0:
            continue
        ind_mean = df_tmp.groupby('ind')['ret'].transform('mean')
        ret_neutral.loc[date_idx, df_tmp.index] = (df_tmp['ret'] - ind_mean).values
    return -ret_neutral


def compute_parkinson(high, low, window):
    """Parkinson波动率. 只过滤一字板."""
    hl_ratio = np.log(high / low)
    parkinson_var = (1.0 / (4.0 * np.log(2))) * (hl_ratio ** 2)
    parkinson_var = parkinson_var.where(high > low)
    vol = parkinson_var.rolling(window, min_periods=int(window * 0.7)).mean()
    return -np.sqrt(vol)


def compute_cc_vol(close, window):
    """Close-to-close波动率 (对数收益率std)."""
    log_ret = np.log(close / close.shift(1))
    vol = log_ret.rolling(window, min_periods=int(window * 0.7)).std()
    return -vol


def compute_abn_turnover(turnover, short_win, long_win):
    """异常换手率 = 短窗均值 / 长窗均值."""
    avg_short = turnover.rolling(short_win, min_periods=max(3, short_win // 2)).mean()
    avg_long = turnover.rolling(long_win, min_periods=max(10, long_win // 3)).mean()
    return -(avg_short / (avg_long + 1e-10))


def compute_mean_turnover(turnover, window):
    """均值换手率 (水平值)."""
    return -turnover.rolling(window, min_periods=max(3, window // 2)).mean()


def compute_cmf_change(features, shift_days=5):
    """ΔCMF: CMF_20d的5日变化."""
    cmf = features.get('CMF_20d')
    return cmf - cmf.shift(shift_days)


# ============================================================
# 市值中性化 (所有因子都做, 与回测一致)
# ============================================================

def neutralize_by_mcap(factor_today, log_mcap_today):
    """截面市值OLS中性化, 返回残差."""
    df = pd.DataFrame({'f': factor_today, 'm': log_mcap_today}).dropna()
    if len(df) < 10:
        return factor_today
    x = df['m'].values
    y = df['f'].values
    var_x = np.var(x)
    if var_x < 1e-10:
        return factor_today
    beta = np.cov(x, y, bias=True)[0, 1] / var_x
    alpha = y.mean() - beta * x.mean()
    residual = y - (alpha + beta * x)
    
    out = pd.Series(np.nan, index=factor_today.index)
    out.loc[df.index] = residual
    return out


# ============================================================
# 方式B: Calendar-time forward return 计算
# ============================================================

def compute_forward_5d_excess(data, base_pool, hold_days=5):
    """
    对每只股票每天, 计算"如果从T+1日VWAP买入, 到T+hold_days+1日VWAP卖出"的超额收益.
    基准: 同期base_pool内所有股票VWAP收益的等权均值.
    
    Returns: DataFrame, [日期 × 股票], 值为T日的"未来5日持有期累积超额收益" (bp).
    """
    vwap = data['vwap']
    ref_idx = vwap.index
    ref_col = vwap.columns
    
    bp = base_pool.reindex(index=ref_idx, columns=ref_col).fillna(0)
    vwap_daily_ret = (vwap / vwap.shift(1) - 1).replace([np.inf, -np.inf], np.nan)
    
    # 基准: base_pool内等权日收益
    bm_daily = vwap_daily_ret.where(bp == 1).mean(axis=1)
    
    # 个股超额日收益
    excess_daily = vwap_daily_ret.sub(bm_daily, axis=0)
    
    # 对每只股票, "T日的forward" = [T+2日收益 + T+3日收益 + ... + T+hold_days+1日收益]
    # (T+1买入, T+hold_days+1卖出, 持有期内的收益是从T+2起算)
    forward_list = []
    for k in range(2, 2 + hold_days):
        forward_list.append(excess_daily.shift(-k))
    forward_cum = sum(forward_list)  # 累积超额收益
    
    return forward_cum * 1e4  # 转bp


# ============================================================
# IC计算
# ============================================================

def compute_rank_ic_in_pool(factor, forward_ret, pool_mask, log_mcap, 
                              neutralize=True):
    """
    在pool_mask为1的股票上, 逐日计算factor和forward_ret的RankIC.
    factor: 已是截面因子值 (可以是正向或负向, IC方向会自动对应)
    
    Returns: 日度IC序列 (pd.Series, index=日期)
    """
    ref_idx = factor.index
    ic_list = []
    
    for date_idx in ref_idx:
        in_pool = pool_mask.loc[date_idx] == 1
        stocks_today = pool_mask.columns[in_pool].tolist()
        if len(stocks_today) < 10:
            continue
        
        f_today = factor.loc[date_idx, stocks_today]
        fw_today = forward_ret.loc[date_idx, stocks_today] if date_idx in forward_ret.index else None
        mc_today = log_mcap.loc[date_idx, stocks_today]
        
        if fw_today is None or fw_today.notna().sum() < 10:
            continue
        
        # 市值中性化
        if neutralize:
            f_neu = neutralize_by_mcap(f_today, mc_today)
        else:
            f_neu = f_today
        
        df = pd.DataFrame({'f': f_neu, 'fw': fw_today}).dropna()
        if len(df) < 10:
            continue
        
        ic = df['f'].rank().corr(df['fw'].rank())
        if pd.notna(ic):
            ic_list.append((date_idx, ic))
    
    if not ic_list:
        return pd.Series(dtype=float)
    
    return pd.Series([v for _, v in ic_list], 
                     index=pd.DatetimeIndex([d for d, _ in ic_list]))


def summarize_ic(ic_series, name):
    """IC序列汇总统计."""
    if len(ic_series) == 0:
        return {'name': name, 'n': 0}
    
    n = len(ic_series)
    ic_mean = ic_series.mean()
    ic_std = ic_series.std()
    ic_icir = ic_mean / ic_std * np.sqrt(252) if ic_std > 0 else 0
    ic_win = (ic_series > 0).mean() if ic_mean > 0 else (ic_series < 0).mean()
    ic_t = ic_mean / (ic_std / np.sqrt(n)) if ic_std > 0 else 0
    
    return {
        'name': name,
        'n': n,
        'ic_mean': ic_mean,
        'ic_std': ic_std,
        'icir': ic_icir,
        'abs_ic': abs(ic_mean),
        'win_rate': ic_win,
        't_stat': ic_t,
    }


# ============================================================
# 参数扫描
# ============================================================

def run_diagnosis_on_period(period_name, start, end):
    print(f"\n{'#'*90}")
    print(f"  因子IC诊断 (方式B: calendar-time forward return): {period_name}")
    print(f"{'#'*90}")
    
    # ---- 加载数据和构建池 ----
    data = load_all_daily_data(start_date=start, end_date=end)
    features = calc_all_daily_features(data)
    bp = get_base_pool(data)
    signal = define_i11_signal(features, bp)
    industry = data.get('industry_zx1', data.get('industry', None))
    
    # 观察池 (obs_window=5, 匹配最优配置)
    obs_pool = build_observation_pool(signal, obs_window=5)
    # 硬约束
    filtered_pool = apply_hard_constraints(obs_pool, data, features, min_mcap=5e9)
    
    print(f"\n  池内股票数: 均值{filtered_pool.sum(axis=1).mean():.1f} 只/天")
    
    # ---- 计算forward 5-day excess return ----
    print(f"  计算T+5 VWAP 持有期超额收益...")
    forward_ret = compute_forward_5d_excess(data, bp, hold_days=5)
    
    # ---- 对齐 ----
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
    log_mcap = compute_log_mcap(mcap)
    if industry is not None:
        industry = industry.reindex(index=ref_idx, columns=ref_col)
    
    # ---- 扫描参数 ----
    all_results = []
    
    # 反转: [5, 10, 20] × [do_ind, no_ind]
    for win in [5, 10, 20]:
        for do_ind in [True, False]:
            tag = f"reversal_w{win}_{'indneu' if do_ind else 'noind'}"
            print(f"  [{tag}]", end=' ')
            f = compute_reversal(close, industry, window=win, do_industry_neu=do_ind)
            ic = compute_rank_ic_in_pool(f, forward_ret, filtered_pool, log_mcap)
            result = summarize_ic(ic, tag)
            all_results.append(result)
            if result['n'] > 0:
                print(f"IC={result['ic_mean']:+.4f} ICIR={result['icir']:+.2f} "
                      f"胜率={result['win_rate']*100:.1f}% t={result['t_stat']:+.2f}")
            else:
                print("N=0")
    
    # Parkinson: [10, 20, 30]
    for win in [10, 20, 30]:
        tag = f"parkinson_w{win}"
        print(f"  [{tag}]", end=' ')
        f = compute_parkinson(high, low, window=win)
        ic = compute_rank_ic_in_pool(f, forward_ret, filtered_pool, log_mcap)
        result = summarize_ic(ic, tag)
        all_results.append(result)
        if result['n'] > 0:
            print(f"IC={result['ic_mean']:+.4f} ICIR={result['icir']:+.2f} "
                  f"胜率={result['win_rate']*100:.1f}% t={result['t_stat']:+.2f}")
        else:
            print("N=0")
    
    # Close-to-close vol: [10, 20, 30]
    for win in [10, 20, 30]:
        tag = f"ccvol_w{win}"
        print(f"  [{tag}]", end=' ')
        f = compute_cc_vol(close, window=win)
        ic = compute_rank_ic_in_pool(f, forward_ret, filtered_pool, log_mcap)
        result = summarize_ic(ic, tag)
        all_results.append(result)
        if result['n'] > 0:
            print(f"IC={result['ic_mean']:+.4f} ICIR={result['icir']:+.2f} "
                  f"胜率={result['win_rate']*100:.1f}% t={result['t_stat']:+.2f}")
        else:
            print("N=0")
    
    # 异常换手率: [5/60, 10/60, 20/120, 60/250]
    for short, long in [(5, 60), (10, 60), (20, 120), (60, 250)]:
        tag = f"abn_turn_{short}_{long}"
        print(f"  [{tag}]", end=' ')
        f = compute_abn_turnover(turnover, short_win=short, long_win=long)
        ic = compute_rank_ic_in_pool(f, forward_ret, filtered_pool, log_mcap)
        result = summarize_ic(ic, tag)
        all_results.append(result)
        if result['n'] > 0:
            print(f"IC={result['ic_mean']:+.4f} ICIR={result['icir']:+.2f} "
                  f"胜率={result['win_rate']*100:.1f}% t={result['t_stat']:+.2f}")
        else:
            print("N=0")
    
    # 均值换手率: [5, 20, 60]
    for win in [5, 20, 60]:
        tag = f"mean_turn_w{win}"
        print(f"  [{tag}]", end=' ')
        f = compute_mean_turnover(turnover, window=win)
        ic = compute_rank_ic_in_pool(f, forward_ret, filtered_pool, log_mcap)
        result = summarize_ic(ic, tag)
        all_results.append(result)
        if result['n'] > 0:
            print(f"IC={result['ic_mean']:+.4f} ICIR={result['icir']:+.2f} "
                  f"胜率={result['win_rate']*100:.1f}% t={result['t_stat']:+.2f}")
        else:
            print("N=0")
    
    # ΔCMF (基础版)
    tag = "cmf_change_5d"
    print(f"  [{tag}]", end=' ')
    f = compute_cmf_change(features, shift_days=5)
    ic = compute_rank_ic_in_pool(f, forward_ret, filtered_pool, log_mcap)
    result = summarize_ic(ic, tag)
    all_results.append(result)
    if result['n'] > 0:
        print(f"IC={result['ic_mean']:+.4f} ICIR={result['icir']:+.2f} "
              f"胜率={result['win_rate']*100:.1f}% t={result['t_stat']:+.2f}")
    else:
        print("N=0")
    
    # ---- 汇总排序 ----
    print(f"\n{'='*80}")
    print(f"  {period_name} 汇总 (按|IC|降序)")
    print(f"{'='*80}")
    df_summary = pd.DataFrame(all_results)
    if len(df_summary) > 0 and 'abs_ic' in df_summary.columns:
        df_summary = df_summary.sort_values('abs_ic', ascending=False)
        print(f"  {'因子':28s}  {'IC':>8s}  {'ICIR':>8s}  {'胜率':>8s}  {'t值':>8s}  {'N':>6s}")
        for _, row in df_summary.iterrows():
            if row.get('n', 0) > 0:
                print(f"  {row['name']:28s}  {row['ic_mean']:>+8.4f}  "
                      f"{row['icir']:>+8.2f}  {row['win_rate']*100:>7.1f}%  "
                      f"{row['t_stat']:>+8.2f}  {int(row['n']):>6d}")
    
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
                all_period_results[p] = run_diagnosis_on_period(p, s, e)
            except Exception as exc:
                print(f"[ERROR] {p}: {exc}")
                import traceback; traceback.print_exc()
    else:
        s, e = PERIODS[args.period]
        all_period_results[args.period] = run_diagnosis_on_period(args.period, s, e)
    
    # ---- 跨段汇总 ----
    if len(all_period_results) > 1:
        print(f"\n{'#'*90}")
        print(f"  跨段IC汇总 (判断因子稳定性)")
        print(f"{'#'*90}")
        
        factor_names = set()
        for results in all_period_results.values():
            for r in results:
                if r.get('n', 0) > 0:
                    factor_names.add(r['name'])
        
        periods = list(all_period_results.keys())
        header = f"  {'因子':28s}  " + "  ".join(f"{p:>10s}" for p in periods) + f"  {'均值':>8s}  {'符号一致':>8s}"
        print(header)
        
        # 按均值|IC|排序
        factor_avg_abs = {}
        for name in factor_names:
            ics = []
            for p in periods:
                for r in all_period_results[p]:
                    if r.get('name') == name and r.get('n', 0) > 0:
                        ics.append(r['ic_mean'])
                        break
            if ics:
                factor_avg_abs[name] = abs(np.mean(ics))
        
        for name in sorted(factor_names, key=lambda n: factor_avg_abs.get(n, 0), reverse=True):
            ics_by_period = {}
            for p in periods:
                ics_by_period[p] = None
                for r in all_period_results[p]:
                    if r.get('name') == name and r.get('n', 0) > 0:
                        ics_by_period[p] = r['ic_mean']
                        break
            
            values = [v for v in ics_by_period.values() if v is not None]
            if not values:
                continue
            ic_avg = np.mean(values)
            sign_consistent = all(v > 0 for v in values) or all(v < 0 for v in values)
            sign_str = "✓" if sign_consistent else "✗"
            
            cells = []
            for p in periods:
                v = ics_by_period[p]
                cells.append(f"{v:>+10.4f}" if v is not None else f"{'N/A':>10s}")
            print(f"  {name:28s}  " + "  ".join(cells) + f"  {ic_avg:>+8.4f}  {sign_str:>8s}")
    
    print("\n[done]")


if __name__ == '__main__':
    main()
