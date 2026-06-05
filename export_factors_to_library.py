"""
导出因子到公共因子库
====================
按领导要求格式导出我们项目用的5个因子:
  1. clc_ts_all_i11_signal_daily      (I11入场信号 0/1)
  2. clc_ts_all_cmf_change_daily      (ΔCMF_10d, 5日变化)
  3. clc_ts_all_reversal_skip1_daily  (Skip-1日 10日反转)
  4. clc_ts_all_parkinson_vol_daily   (Parkinson 20日波动率)
  5. clc_ts_all_abn_turnover_daily    (20/120异常换手率)

输出格式 (每个文件):
  3 列: ticker(int), tradeDate, <因子名>
  第三列列名 = 文件名
  
输出路径:
  /mnt/big/base/public/FundamentalTL/量价因子/

注意:
  - reversal_skip1 不做行业中性化 (导出原始因子值, 给他人自由用)
    本项目策略里在score_pool阶段才做中性化
  - I11入场信号是合成结果 (3个条件的AND)
  - 全A股 + 全时间范围 (2010-至今)

用法:
    python export_factors_to_library.py
"""

import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 关键: 把data_loader的缓存目录改成用户有权限的位置
# (公共目录 /mnt/big/base/public/FundamentalTL/cache/ 可能没写权限)
import data_loader
USER_CACHE_DIR = '/mnt/sda2/lichenchen/data/cache/'
os.makedirs(USER_CACHE_DIR, exist_ok=True)
data_loader.PATHS['cache_dir'] = USER_CACHE_DIR
print(f"[setup] cache_dir overridden to: {USER_CACHE_DIR}")

from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import get_base_pool, PERIODS
from pool_screening_v2 import (
    define_i11_signal,
    compute_reversal_skip1,
    compute_parkinson_vol,
    compute_abnormal_turnover,
    compute_cmf_change,
)


OUTPUT_DIR = '/mnt/big/base/public/FundamentalTL/量价因子'


def factor_matrix_to_long(factor_df, factor_name):
    """
    把宽表(日期x股票)转成长表(ticker, tradeDate, 因子值).
    
    Args:
        factor_df: DataFrame, index=日期, columns=股票代码(如 '600000.SH')
        factor_name: 字符串, 用作第三列的列名
    
    Returns:
        DataFrame, 3列: ticker(int), tradeDate, factor_name
    """
    # 转长表 (兼容新旧pandas)
    long = factor_df.stack().dropna().reset_index()
    long.columns = ['tradeDate', 'ticker_str', factor_name]
    
    # ticker转整数 (去掉.SH/.SZ等后缀)
    # A股代码格式: '600000.SH' / '000001.SZ' / '300001.SZ' 等
    long['ticker'] = long['ticker_str'].str.split('.').str[0].astype(int)
    
    # 排列列顺序: ticker, tradeDate, 因子值
    result = long[['ticker', 'tradeDate', factor_name]].copy()
    
    # 按 tradeDate + ticker 排序 (人类阅读友好)
    result = result.sort_values(['tradeDate', 'ticker']).reset_index(drop=True)
    
    return result


def export_one_factor(factor_df, file_name, output_dir):
    """导出单个因子到csv."""
    factor_name_col = file_name  # 列名=文件名
    long_df = factor_matrix_to_long(factor_df, factor_name_col)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f'{file_name}.csv')
    long_df.to_csv(output_path, index=False)
    
    n_rows = len(long_df)
    n_dates = long_df['tradeDate'].nunique()
    n_tickers = long_df['ticker'].nunique()
    
    print(f"  [export] {file_name}")
    print(f"    {n_rows:,} rows, {n_dates} dates, {n_tickers} tickers")
    print(f"    saved to: {output_path}")
    
    return output_path


def compute_and_export_all_factors(start_date='20100101', end_date='20260327',
                                     output_dir=OUTPUT_DIR):
    """
    主流程: 加载全时间数据, 计算5个因子, 导出.
    """
    print(f"\n{'#'*80}")
    print(f"  导出因子到公共因子库")
    print(f"  时间范围: {start_date} ~ {end_date}")
    print(f"  输出目录: {output_dir}")
    print(f"{'#'*80}")
    
    # ---- Step 1: 加载数据 ----
    print(f"\n[1/3] 加载日频数据...")
    data = load_all_daily_data(start_date=start_date, end_date=end_date)
    
    # ---- Step 2: 计算因子 ----
    print(f"\n[2/3] 计算因子...")
    
    close = data['close']
    high = data['high']
    low = data['low']
    turnover = data.get('turnover_rate')
    industry = data.get('industry_zx1', data.get('industry'))
    
    # 计算70个特征 (因为I11和cmf_change都需要CMF_20d)
    features = calc_all_daily_features(data)
    
    # 因子1: I11入场信号 (3个条件合成)
    print("  计算因子1: I11_signal (3条件: CMF_20d>=P80 & cum_ret_5d in [P25,P55] & intraday_ret<P70)")
    bp = get_base_pool(data)
    i11_signal = define_i11_signal(features, bp)
    
    # 因子2: ΔCMF (5日变化)
    print("  计算因子2: cmf_change (CMF_20d的5日变化)")
    cmf_change = compute_cmf_change(features, window_long=10, window_short=5)
    
    # 因子3: 反转 (导原始值, 不做行业中性化)
    # 注意: 项目策略里score_pool做行业中性化, 但导出公共因子保持原料状态
    print("  计算因子3: reversal_skip1 (Skip-1日 10日反转, 原始值不做中性化)")
    reversal_raw = -close.shift(1) / close.shift(11) + 1  # = -(close.shift(1)/close.shift(11) - 1) = 负向
    # 上面公式等价于: -(过去10日skip-1反转)
    # 但更清晰: 直接计算
    raw_reversal = close.shift(1) / close.shift(11) - 1   # 10日skip-1涨幅
    reversal_skip1 = -raw_reversal  # 反转因子=负的涨幅 (低涨幅=高分)
    
    # 因子4: Parkinson波动率
    print("  计算因子4: parkinson_vol (20日Parkinson)")
    parkinson_vol = compute_parkinson_vol(high, low, window=20)
    
    # 因子5: 异常换手率
    print("  计算因子5: abn_turnover (20/120)")
    abn_turnover = compute_abnormal_turnover(turnover, window_short=20, window_long=120)
    
    # ---- Step 3: 导出 ----
    print(f"\n[3/3] 导出因子到 {output_dir} ...")
    
    exports = [
        (i11_signal,      'clc_ts_all_i11_signal_daily'),
        (cmf_change,      'clc_ts_all_cmf_change_daily'),
        (reversal_skip1,  'clc_ts_all_reversal_skip1_daily'),
        (parkinson_vol,   'clc_ts_all_parkinson_vol_daily'),
        (abn_turnover,    'clc_ts_all_abn_turnover_daily'),
    ]
    
    paths = []
    for factor_df, file_name in exports:
        path = export_one_factor(factor_df, file_name, output_dir)
        paths.append(path)
    
    # ---- 总结 ----
    print(f"\n{'='*80}")
    print(f"  导出完成! 共 {len(paths)} 个因子文件")
    print(f"{'='*80}")
    for path in paths:
        size_mb = os.path.getsize(path) / 1024 / 1024
        print(f"  {os.path.basename(path):>50s}  {size_mb:>8.1f} MB")
    
    return paths


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', default='20100101', help='起始日期')
    parser.add_argument('--end',   default='20260327', help='结束日期')
    parser.add_argument('--output_dir', default=OUTPUT_DIR, help='输出目录')
    args = parser.parse_args()
    
    compute_and_export_all_factors(args.start, args.end, args.output_dir)
    
    print("\n[done]")


if __name__ == '__main__':
    main()
