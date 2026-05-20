"""
I11 最终确认
============
基于交叉验证的发现, 测试真正的最优组合:
  final_min: CMF P85 + 去CLV + cr5[P25,P55] + ir<P70 (3条件极简版)

对比:
  v2c (当前最佳): CMF P85 + CLV P80 + cr5[P25,P55] + ir<P70
  v2b (已知): CMF P90 + 去CLV + cr5[P25,P55] + ir<P70
  final_min: CMF P85 + 去CLV + cr5[P25,P55] + ir<P70  ← 新测

额外加几个探索:
  final_v1: final_min + 去ir_pct条件 (看ir是否真必要)
  final_v2: CMF P80 + 去CLV + cr5[P25,P55] + ir<P70 (CMF继续放松)
  final_v3: CMF P85 + 去CLV + cr5[P30,P60] + ir<P70 (cr5回到baseline区间)
"""

import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import (
    get_base_pool, calc_forward_returns, calc_benchmark_returns, PERIODS,
)


def define_final_variants(features, base_pool):
    bp = base_pool.reindex_like(features['intraday_ret']).fillna(0)
    mask = bp == 1
    
    def pct_in_pool(feat_name):
        f = features[feat_name].reindex_like(bp).where(mask)
        return f.rank(axis=1, pct=True)
    
    cmf_pct = pct_in_pool('CMF_20d')
    clv20_pct = pct_in_pool('CLV_20d')
    cr5_pct = pct_in_pool('cum_return_5d')
    ir_pct = pct_in_pool('intraday_ret')
    
    signals = {}
    
    # 参考版本 v2c (当前最佳, 用于对比)
    signals['v2c_reference'] = (
        (cmf_pct >= 0.85) &
        (clv20_pct >= 0.80) &
        (cr5_pct >= 0.25) & (cr5_pct <= 0.55) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # 主角: 最简最优 (CMF P85 + 去CLV + cr5 + ir)
    signals['final_min'] = (
        (cmf_pct >= 0.85) &
        (cr5_pct >= 0.25) & (cr5_pct <= 0.55) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # 探索1: 去ir_pct看看 (ir在敏感性测试里很重要, 这里再验证)
    signals['final_v1_no_ir'] = (
        (cmf_pct >= 0.85) &
        (cr5_pct >= 0.25) & (cr5_pct <= 0.55) &
        mask
    ).astype(float)
    
    # 探索2: CMF继续放松到P80 (看是不是放得越松越好)
    signals['final_v2_cmf80'] = (
        (cmf_pct >= 0.80) &
        (cr5_pct >= 0.25) & (cr5_pct <= 0.55) &
        (ir_pct < 0.70) &
        mask
    ).astype(float)
    
    # 探索3: cr5回到baseline区间[P30,P60] (看cr5前移是必要的吗)
    signals['final_v3_cr5_30_60'] = (
        (cmf_pct >= 0.85) &
        (cr5_pct >= 0.30) & (cr5_pct <= 0.60) &
        (ir_pct < 0.70) &
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
        'vwap_t20': excess('vwap_20d') if 'vwap_20d' in fwd else None,
    }


def analyze_period(period_name, start, end):
    print(f"\n{'#'*80}")
    print(f"  I11 最终确认: {period_name}")
    print(f"{'#'*80}")
    
    data = load_all_daily_data(start_date=start, end_date=end)
    features = calc_all_daily_features(data)
    bp = get_base_pool(data)
    
    variants = define_final_variants(features, bp)
    fwd = calc_forward_returns(data, max_horizon=20)
    bm = calc_benchmark_returns(data, bp, max_horizon=20)
    
    results = {}
    for name, sig in variants.items():
        r = eval_variant(sig, fwd, bm, bp)
        if r:
            results[name] = r
    
    print(f"\n  {'变种':25s}  {'日均':>6s}  {'T+3':>8s}  {'T+5':>8s}  {'T+10':>8s}  {'T+20':>8s}")
    print(f"  {'-'*72}")
    for name, r in results.items():
        t20 = f"{r['vwap_t20']:>8.1f}" if r['vwap_t20'] is not None else f"{'--':>8s}"
        marker = " ← 当前最佳" if name == 'v2c_reference' else ""
        marker_fin = " ← 新" if name == 'final_min' else ""
        print(f"  {name:25s}  {r['avg_daily']:>6.1f}  "
              f"{r['vwap_t3']:>8.1f}  {r['vwap_t5']:>8.1f}  "
              f"{r['vwap_t10']:>8.1f}  {t20}{marker}{marker_fin}")
    
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
        print(f"  最终汇总: 跨4段")
        print(f"{'#'*95}")
        
        variant_order = [
            'v2c_reference',
            'final_min',
            'final_v1_no_ir',
            'final_v2_cmf80',
            'final_v3_cr5_30_60',
        ]
        
        periods = list(all_results.keys())
        
        for metric, title in [
            ('vwap_t3', 'VWAP T+3'),
            ('vwap_t5', 'VWAP T+5'),
            ('vwap_t10', 'VWAP T+10'),
            ('vwap_t20', 'VWAP T+20'),
        ]:
            print(f"\n  【{title} 超额收益 (bp)】")
            print(f"  {'变种':25s}  " + " ".join(f"{p:>10s}" for p in periods) + 
                  f"  {'平均':>9s}  {'正段数':>6s}")
            print(f"  {'-'*100}")
            for v in variant_order:
                vals = []
                for p in periods:
                    if v in all_results[p]:
                        x = all_results[p][v].get(metric)
                        vals.append(x)
                    else:
                        vals.append(None)
                valid = [x for x in vals if x is not None]
                if not valid:
                    continue
                avg = sum(valid) / len(valid)
                pos = sum(1 for x in valid if x > 0)
                marker = " ← v2c" if v == 'v2c_reference' else (" ← final" if v == 'final_min' else "")
                print(f"  {v:25s}  " + " ".join(
                    f"{x:>10.1f}" if x is not None else f"{'N/A':>10s}" for x in vals
                ) + f"  {avg:>9.1f}  {pos}/{len(valid)}{marker}")
        
        # 触发数
        print(f"\n  【日均触发数】")
        print(f"  {'变种':25s}  " + " ".join(f"{p:>10s}" for p in periods))
        print(f"  {'-'*90}")
        for v in variant_order:
            vals = []
            for p in periods:
                if v in all_results[p]:
                    vals.append(all_results[p][v]['avg_daily'])
                else:
                    vals.append(None)
            marker = " ← v2c" if v == 'v2c_reference' else (" ← final" if v == 'final_min' else "")
            print(f"  {v:25s}  " + " ".join(
                f"{x:>10.1f}" if x is not None else f"{'N/A':>10s}" for x in vals
            ) + marker)
    
    print("\n[done]")


if __name__ == '__main__':
    main()
