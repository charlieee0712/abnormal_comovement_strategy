"""
I11 参数敏感性 & 消融分析
============================
目的:
    1. 验证I11不是过拟合 (参数扰动后仍然稳定)
    2. 理解I11每个条件的边际贡献

测试组:
    A类: cr5区间扫描 (核心假设测试)
    B类: 其他参数扰动 + 消融
"""

import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import (
    get_base_pool, calc_forward_returns, calc_benchmark_returns,
    event_study, PERIODS,
)


def define_i11_variants(features, base_pool):
    """I11的12个变种 (含baseline)."""
    bp = base_pool.reindex_like(features['intraday_ret']).fillna(0)
    mask = bp == 1
    
    def pct_in_pool(feat_name):
        f = features[feat_name].reindex_like(bp).where(mask)
        return f.rank(axis=1, pct=True)
    
    # 所有需要的pct特征
    cmf_pct = pct_in_pool('CMF_20d')
    clv20_pct = pct_in_pool('CLV_20d')
    cr5_pct = pct_in_pool('cum_return_5d')
    cvr20_pct = pct_in_pool('CVR_20d')
    ir_pct = pct_in_pool('intraday_ret')
    
    signals = {}
    
    # ============================================================
    # Baseline (用于对比)
    # ============================================================
    signals['I11_baseline'] = (
        (cmf_pct >= 0.90) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.30) & (cr5_pct <= 0.60) &
        (cvr20_pct >= 0.70) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # ============================================================
    # A类: cr5区间扫描 (最核心的参数, 测试假设的连续性)
    # ============================================================
    cr5_ranges = [
        ('A1_cr5_20_50', 0.20, 0.50),
        ('A2_cr5_25_55', 0.25, 0.55),
        # baseline = A_cr5_30_60
        ('A3_cr5_35_65', 0.35, 0.65),
        ('A4_cr5_40_70', 0.40, 0.70),
        ('A5_cr5_50_80', 0.50, 0.80),  # 接近I7区间
    ]
    for name, lo, hi in cr5_ranges:
        signals[f'I11_{name}'] = (
            (cmf_pct >= 0.90) &
            (clv20_pct >= 0.80) &
            (cr5_pct >= lo) & (cr5_pct <= hi) &
            (cvr20_pct >= 0.70) &
            (ir_pct < 0.70) &
            mask
        ).astype(float)
    
    # ============================================================
    # B类: 其他参数扰动 + 消融
    # ============================================================
    
    # B1: CMF放松到P85
    signals['I11_B1_cmf85'] = (
        (cmf_pct >= 0.85) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.30) & (cr5_pct <= 0.60) &
        (cvr20_pct >= 0.70) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # B2: CMF收紧到P95
    signals['I11_B2_cmf95'] = (
        (cmf_pct >= 0.95) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.30) & (cr5_pct <= 0.60) &
        (cvr20_pct >= 0.70) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # B3: 去掉CVR条件 (消融)
    signals['I11_B3_no_cvr'] = (
        (cmf_pct >= 0.90) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.30) & (cr5_pct <= 0.60) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # B4: 去掉CLV条件 (消融)
    signals['I11_B4_no_clv'] = (
        (cmf_pct >= 0.90) &
        (cr5_pct >= 0.30) & (cr5_pct <= 0.60) &
        (cvr20_pct >= 0.70) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # B5: 去掉ir_pct条件 (不限制今天涨跌)
    signals['I11_B5_no_ir'] = (
        (cmf_pct >= 0.90) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.30) & (cr5_pct <= 0.60) &
        (cvr20_pct >= 0.70) &
        mask
    ).astype(float)
    
    # B6: 最小化 - 只保留CMF + cr5 (看核心alpha)
    signals['I11_B6_minimal'] = (
        (cmf_pct >= 0.90) &
        (cr5_pct >= 0.30) & (cr5_pct <= 0.60) &
        mask
    ).astype(float)
    
    return signals


def evaluate_variants_per_period(period_name, start, end):
    print(f"\n{'#'*80}")
    print(f"  I11 敏感性测试: {period_name}")
    print(f"{'#'*80}")
    
    data = load_all_daily_data(start_date=start, end_date=end)
    features = calc_all_daily_features(data)
    bp = get_base_pool(data)
    
    variants = define_i11_variants(features, bp)
    
    fwd = calc_forward_returns(data, max_horizon=10)
    bm = calc_benchmark_returns(data, bp, max_horizon=10)
    
    # 只要 vwap_5d 和 vwap_10d 结果
    results = {}
    for name, sig in variants.items():
        bp_mask = bp == 1
        sig = sig.where(bp_mask, 0)
        daily_count = sig.sum(axis=1)
        total = int(daily_count.sum())
        avg = daily_count.mean()
        if total == 0:
            continue
        
        # VWAP T+5 excess
        sig_mask = sig == 1
        trig_ret_5d = fwd['vwap_5d'].where(sig_mask).mean(axis=1)
        bm_5d = bm['vwap_5d']
        excess_5d = ((trig_ret_5d - bm_5d) * 1e4).mean()
        
        # VWAP T+10 excess
        trig_ret_10d = fwd['vwap_10d'].where(sig_mask).mean(axis=1)
        bm_10d = bm['vwap_10d']
        excess_10d = ((trig_ret_10d - bm_10d) * 1e4).mean()
        
        results[name] = {
            'avg_daily': avg,
            'total_trig': total,
            'vwap_t5': excess_5d,
            'vwap_t10': excess_10d,
        }
    
    # 打印
    print(f"\n  {'变种':25s}  {'日均触发':>8s}  {'VWAP T+5':>10s}  {'VWAP T+10':>10s}")
    print(f"  {'-'*65}")
    for name, r in results.items():
        marker = " ← baseline" if name == 'I11_baseline' else ""
        print(f"  {name:25s}  {r['avg_daily']:>8.1f}  "
              f"{r['vwap_t5']:>10.1f}  {r['vwap_t10']:>10.1f}{marker}")
    
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--period', default='all')
    args = parser.parse_args()
    
    all_results = {}
    
    if args.period == 'all':
        for p, (s, e) in PERIODS.items():
            try:
                all_results[p] = evaluate_variants_per_period(p, s, e)
            except Exception as exc:
                print(f"[ERROR] {p}: {exc}")
                import traceback; traceback.print_exc()
    else:
        s, e = PERIODS[args.period]
        all_results[args.period] = evaluate_variants_per_period(args.period, s, e)
    
    # ============================================================
    # 最终汇总表
    # ============================================================
    if len(all_results) > 1:
        print(f"\n\n{'#'*90}")
        print(f"  最终汇总: 跨4段 VWAP T+5 超额收益 (bp)")
        print(f"{'#'*90}\n")
        
        # 收集所有变种名
        all_variants = set()
        for r in all_results.values():
            all_variants.update(r.keys())
        all_variants = sorted(all_variants)
        
        periods = list(all_results.keys())
        
        print(f"  {'变种':25s}  " + " ".join(f"{p:>9s}" for p in periods) + 
              f"  {'平均':>9s}  {'正段数':>6s}")
        print(f"  {'-'*95}")
        for v in all_variants:
            vals = []
            for p in periods:
                if v in all_results[p]:
                    vals.append(all_results[p][v]['vwap_t5'])
                else:
                    vals.append(None)
            valid = [x for x in vals if x is not None]
            if not valid:
                continue
            avg = sum(valid) / len(valid)
            pos = sum(1 for x in valid if x > 0)
            marker = " ←" if v == 'I11_baseline' else ""
            print(f"  {v:25s}  " + " ".join(
                f"{x:>9.1f}" if x is not None else f"{'N/A':>9s}" for x in vals
            ) + f"  {avg:>9.1f}  {pos}/{len(valid)}{marker}")
        
        # T+10 汇总
        print(f"\n\n  跨4段 VWAP T+10 超额收益 (bp)")
        print(f"  {'-'*95}")
        print(f"  {'变种':25s}  " + " ".join(f"{p:>9s}" for p in periods) + 
              f"  {'平均':>9s}  {'正段数':>6s}")
        print(f"  {'-'*95}")
        for v in all_variants:
            vals = []
            for p in periods:
                if v in all_results[p]:
                    vals.append(all_results[p][v]['vwap_t10'])
                else:
                    vals.append(None)
            valid = [x for x in vals if x is not None]
            if not valid:
                continue
            avg = sum(valid) / len(valid)
            pos = sum(1 for x in valid if x > 0)
            marker = " ←" if v == 'I11_baseline' else ""
            print(f"  {v:25s}  " + " ".join(
                f"{x:>9.1f}" if x is not None else f"{'N/A':>9s}" for x in vals
            ) + f"  {avg:>9.1f}  {pos}/{len(valid)}{marker}")
        
        # 触发数汇总
        print(f"\n\n  跨4段 日均触发数")
        print(f"  {'-'*95}")
        print(f"  {'变种':25s}  " + " ".join(f"{p:>9s}" for p in periods))
        print(f"  {'-'*95}")
        for v in all_variants:
            vals = []
            for p in periods:
                if v in all_results[p]:
                    vals.append(all_results[p][v]['avg_daily'])
                else:
                    vals.append(None)
            if not any(x is not None for x in vals):
                continue
            marker = " ←" if v == 'I11_baseline' else ""
            print(f"  {v:25s}  " + " ".join(
                f"{x:>9.1f}" if x is not None else f"{'N/A':>9s}" for x in vals
            ) + marker)
    
    print("\n[done]")


if __name__ == '__main__':
    main()
