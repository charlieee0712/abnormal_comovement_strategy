"""
I11 交叉验证
============
基于敏感性测试的发现, 测试3个最有潜力的组合:
  v2a: CMF P90 + CLV P80 + cr5 [P25-P55] + ir<P70 (B3思路+A2区间)
  v2b: CMF P90 + cr5 [P25-P55] + ir<P70 (极简版, 去CVR和CLV)
  v2c: CMF P85 + CLV P80 + cr5 [P25-P55] + ir<P70 (CMF放松+A2区间)
  
对比基准: baseline I11 (P30-P60)
"""

import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import (
    get_base_pool, calc_forward_returns, calc_benchmark_returns, PERIODS,
)


def define_v2_variants(features, base_pool):
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
    
    # ============================================================
    # baseline (对比基准)
    # ============================================================
    signals['I11_baseline_P30_P60_withCVR'] = (
        (cmf_pct >= 0.90) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.30) & (cr5_pct <= 0.60) &
        (cvr20_pct >= 0.70) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # ============================================================
    # v2系列: 去CVR + cr5前移
    # ============================================================
    
    # v2a: 标配 (CMF P90 + CLV P80 + cr5 P25-P55 + ir<P70)
    signals['I11_v2a_core'] = (
        (cmf_pct >= 0.90) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.25) & (cr5_pct <= 0.55) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # v2b: 极简版 (去CLV)
    signals['I11_v2b_minimal'] = (
        (cmf_pct >= 0.90) &
        (cr5_pct >= 0.25) & (cr5_pct <= 0.55) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # v2c: CMF放松到P85
    signals['I11_v2c_cmf85'] = (
        (cmf_pct >= 0.85) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.25) & (cr5_pct <= 0.55) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # ============================================================
    # 加几个补充组合 (既然要跑就把可能的最优都覆盖)
    # ============================================================
    
    # v2d: cr5更前移到P20-P50 (A1思路)
    signals['I11_v2d_cr5_20_50'] = (
        (cmf_pct >= 0.90) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.20) & (cr5_pct <= 0.50) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # v2e: v2a + ir收紧到P60 (进一步减少VWAP成本)
    signals['I11_v2e_ir_p60'] = (
        (cmf_pct >= 0.90) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.25) & (cr5_pct <= 0.55) &
        (ir_pct < 0.60) &
        mask
    ).astype(float)
    
    # v2f: v2a + ir放松到P80
    signals['I11_v2f_ir_p80'] = (
        (cmf_pct >= 0.90) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.25) & (cr5_pct <= 0.55) &
        (ir_pct < 0.80) &
        mask
    ).astype(float)
    
    return signals


def eval_variant(sig, fwd, bm, bp):
    bp_mask = bp == 1
    sig = sig.where(bp_mask, 0)
    daily_count = sig.sum(axis=1)
    total = int(daily_count.sum())
    avg = daily_count.mean()
    if total == 0:
        return None
    
    sig_mask = sig == 1
    
    def excess(horizon):
        trig = fwd[horizon].where(sig_mask).mean(axis=1)
        b = bm[horizon]
        return ((trig - b) * 1e4).mean()
    
    return {
        'avg_daily': avg,
        'vwap_t3': excess('vwap_3d'),
        'vwap_t5': excess('vwap_5d'),
        'vwap_t10': excess('vwap_10d'),
    }


def analyze_period(period_name, start, end):
    print(f"\n{'#'*80}")
    print(f"  I11 交叉验证: {period_name}")
    print(f"{'#'*80}")
    
    data = load_all_daily_data(start_date=start, end_date=end)
    features = calc_all_daily_features(data)
    bp = get_base_pool(data)
    
    variants = define_v2_variants(features, bp)
    fwd = calc_forward_returns(data, max_horizon=10)
    bm = calc_benchmark_returns(data, bp, max_horizon=10)
    
    results = {}
    for name, sig in variants.items():
        r = eval_variant(sig, fwd, bm, bp)
        if r:
            results[name] = r
    
    # 打印
    print(f"\n  {'变种':35s}  {'日均':>6s}  {'VWAP T+3':>10s}  {'VWAP T+5':>10s}  {'VWAP T+10':>10s}")
    print(f"  {'-'*82}")
    for name, r in results.items():
        marker = " ← base" if name == 'I11_baseline_P30_P60_withCVR' else ""
        print(f"  {name:35s}  {r['avg_daily']:>6.1f}  "
              f"{r['vwap_t3']:>10.1f}  {r['vwap_t5']:>10.1f}  {r['vwap_t10']:>10.1f}{marker}")
    
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
                all_results[p] = analyze_period(p, s, e)
            except Exception as exc:
                print(f"[ERROR] {p}: {exc}")
                import traceback; traceback.print_exc()
    else:
        s, e = PERIODS[args.period]
        all_results[args.period] = analyze_period(args.period, s, e)
    
    # 最终汇总
    if len(all_results) > 1:
        print(f"\n\n{'#'*95}")
        print(f"  最终汇总: 跨4段对比")
        print(f"{'#'*95}")
        
        all_variants = set()
        for r in all_results.values():
            all_variants.update(r.keys())
        # 保持固定顺序
        variant_order = [
            'I11_baseline_P30_P60_withCVR',
            'I11_v2a_core',
            'I11_v2b_minimal',
            'I11_v2c_cmf85',
            'I11_v2d_cr5_20_50',
            'I11_v2e_ir_p60',
            'I11_v2f_ir_p80',
        ]
        all_variants = [v for v in variant_order if v in all_variants]
        
        periods = list(all_results.keys())
        
        for metric, title in [('vwap_t3', 'VWAP T+3'), ('vwap_t5', 'VWAP T+5'), ('vwap_t10', 'VWAP T+10')]:
            print(f"\n  【{title} 超额收益 (bp)】")
            print(f"  {'变种':35s}  " + " ".join(f"{p:>9s}" for p in periods) + 
                  f"  {'平均':>9s}  {'正段数':>6s}")
            print(f"  {'-'*105}")
            for v in all_variants:
                vals = []
                for p in periods:
                    if v in all_results[p]:
                        vals.append(all_results[p][v][metric])
                    else:
                        vals.append(None)
                valid = [x for x in vals if x is not None]
                if not valid:
                    continue
                avg = sum(valid) / len(valid)
                pos = sum(1 for x in valid if x > 0)
                marker = " ← base" if v == 'I11_baseline_P30_P60_withCVR' else ""
                print(f"  {v:35s}  " + " ".join(
                    f"{x:>9.1f}" if x is not None else f"{'N/A':>9s}" for x in vals
                ) + f"  {avg:>9.1f}  {pos}/{len(valid)}{marker}")
        
        # 触发数
        print(f"\n  【日均触发数】")
        print(f"  {'变种':35s}  " + " ".join(f"{p:>9s}" for p in periods))
        print(f"  {'-'*95}")
        for v in all_variants:
            vals = []
            for p in periods:
                if v in all_results[p]:
                    vals.append(all_results[p][v]['avg_daily'])
                else:
                    vals.append(None)
            marker = " ← base" if v == 'I11_baseline_P30_P60_withCVR' else ""
            print(f"  {v:35s}  " + " ".join(
                f"{x:>9.1f}" if x is not None else f"{'N/A':>9s}" for x in vals
            ) + marker)
    
    print("\n[done]")


if __name__ == '__main__':
    main()
