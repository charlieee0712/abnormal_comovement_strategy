"""
数据加载模块 v2.0
==================
基于服务器已有csv文件加载, parquet缓存加速.

主数据源:
    日线行情: /mnt/big/base/shibo/KLines_make/daily_temp3/YYYYMMDD.csv
        字段: ticker, preClosePrice, openPrice, highestPrice, lowestPrice, 
              closePrice, turnoverVol, turnoverValue, turnoverRate, 
              negMarketValue, marketValue, chgPct, isOpen, vwap, 
              industryID1, adj_factor

辅助数据 (领导洗过):
    /mnt/big/base/public/FundamentalTL/base_data/base_factor/
        closePrice.csv, vwap_30m.csv, limitUpPrice.csv, limitDownPrice.csv,
        flag_buy.csv, flag_sell.csv, flag_st_new.csv, industry_zx_1_all.csv

股票池过滤:
    /mnt/big/base/zhuhuihao/alphagp_lv2_daily/isopen_gp.csv  (pivot矩阵)

缓存机制:
    首次加载csv → 存为parquet缓存 → 后续秒级加载
"""

import os
import glob
import numpy as np
import pandas as pd
from typing import Dict, Optional, List
from pathlib import Path


# ============================================================
# 路径配置
# ============================================================

PATHS = {
    # 日线行情 (每日一个csv)
    'daily_kline': '/mnt/big/base/shibo/KLines_make/daily_temp3/',
    # 备选日线
    'daily_kline_alt': '/mnt/big/base/zhuhuihao/1day/',

    # 领导洗过的基础数据 (长表)
    'fundamental': '/mnt/big/base/public/FundamentalTL/base_data/base_factor/',

    # pivot矩阵类
    'isopen': '/mnt/big/base/zhuhuihao/alphagp_lv2_daily/isopen_gp.csv',
    'st_judge': '/mnt/big/base/zhuhuihao/alphagp_lv2_daily/st_judge_uqer.csv',
    'adj': '/mnt/big/base/zhuhuihao/alphagp_lv2_daily/adj.csv',
    'ind': '/mnt/big/base/zhuhuihao/alphagp_lv2_daily/ind.csv',

    # 行业分类
    'zx_industry': '/mnt/big/base/zhouhua/POIPOI233/stock/risk_management/data/Kline/zx_industry_lv1.csv',

    # 指数权重
    'index_weight': '/mnt/big/base/zhuhuihao/host_zhu/weight/',
    'index_weight_alt': '/mnt/big/base/public/Choice/Weight/',

    # 交易日历
    'trade_dates': '/mnt/big/base/shibo/script/uqer_s/daily/trade_date.csv',

    # 默认缓存目录
    'cache_dir': '/mnt/big/base/public/FundamentalTL/cache/',
}


def _pad_ticker(ticker) -> str:
    """将股票代码统一为6位补零字符串: 1 -> '000001', '000001' -> '000001'."""
    s = str(ticker).strip()
    # 去掉可能的交易所后缀 (如 .XSHE)
    s = s.split('.')[0]
    # 只保留数字
    digits = ''.join(filter(str.isdigit, s))
    return digits.zfill(6)


# ============================================================
# 1. 日线行情加载 (daily_temp3 csv)
# ============================================================

def load_daily_kline_from_csv(
    start_date: str = '20240101',
    end_date: str = '20260327',
    kline_dir: str = None,
    cache_path: str = None,
) -> Dict[str, pd.DataFrame]:
    """
    从 daily_temp3/ 逐日csv加载行情数据, 返回pivot矩阵字典.

    Parameters
    ----------
    start_date : str
        起始日期 YYYYMMDD
    end_date : str
        结束日期 YYYYMMDD
    kline_dir : str
        日线csv目录, None则使用默认路径
    cache_path : str
        parquet缓存路径, None则使用默认路径

    Returns
    -------
    dict: 每个value是 DataFrame(index=trade_date, columns=stock_code_6digit)
        'open', 'close', 'high', 'low', 'lclose', 'vwap',
        'volume', 'amount', 'turnover_rate', 'change_pct',
        'mcap', 'is_open', 'adj_factor', 'industry'
    """
    if kline_dir is None:
        kline_dir = PATHS['daily_kline']

    if cache_path is None:
        cache_dir = PATHS['cache_dir']
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f'daily_kline_{start_date}_{end_date}.parquet')

    # ---- 尝试读缓存 ----
    if os.path.exists(cache_path):
        print(f"[load] Reading cache: {cache_path}")
        cache_df = pd.read_parquet(cache_path)
        return _unpack_cache(cache_df)

    # ---- 逐日读csv ----
    print(f"[load] Loading daily kline from {kline_dir}")
    print(f"[load] Date range: {start_date} ~ {end_date}")

    csv_files = sorted(glob.glob(os.path.join(kline_dir, '*.csv')))
    csv_files = [f for f in csv_files
                 if start_date <= os.path.basename(f).replace('.csv', '') <= end_date]

    print(f"[load] Found {len(csv_files)} csv files")

    all_dfs = []
    for i, fpath in enumerate(csv_files):
        date_str = os.path.basename(fpath).replace('.csv', '')
        try:
            df = pd.read_csv(fpath, index_col=0)
            df['date'] = date_str
            all_dfs.append(df)
        except Exception as e:
            print(f"[warn] Failed to read {fpath}: {e}")
            continue

        if (i + 1) % 100 == 0:
            print(f"[load] ... {i + 1}/{len(csv_files)} files loaded")

    if not all_dfs:
        raise ValueError(f"No valid csv files found in {kline_dir} for {start_date}~{end_date}")

    raw = pd.concat(all_dfs, ignore_index=True)
    print(f"[load] Total rows: {len(raw)}, stocks: {raw['ticker'].nunique()}")

    # ---- 统一股票代码 ----
    raw['stock_code'] = raw['ticker'].apply(_pad_ticker)
    raw['trade_date'] = pd.to_datetime(raw['date'], format='%Y%m%d')

    # ---- 字段映射 ----
    field_map = {
        'openPrice': 'open',
        'closePrice': 'close',
        'highestPrice': 'high',
        'lowestPrice': 'low',
        'preClosePrice': 'lclose',
        'vwap': 'vwap',
        'turnoverVol': 'volume',
        'turnoverValue': 'amount',
        'turnoverRate': 'turnover_rate',
        'chgPct': 'change_pct',
        'negMarketValue': 'mcap',
        'isOpen': 'is_open',
        'adj_factor': 'adj_factor',
        'industryID1': 'industry',
    }

    # ---- Pivot ----
    data = {}
    for raw_col, name in field_map.items():
        if raw_col not in raw.columns:
            print(f"[warn] Column '{raw_col}' not found in csv, skipping '{name}'")
            continue
        pivot = raw.pivot_table(
            index='trade_date', columns='stock_code', values=raw_col,
            aggfunc='first'
        )
        pivot = pivot.sort_index()
        data[name] = pivot.astype(float) if name != 'industry' else pivot

    print(f"[load] Pivoted: {data['close'].shape[0]} days x {data['close'].shape[1]} stocks")

    # ---- 存缓存 ----
    _save_cache(data, cache_path)

    return data


def _save_cache(data: dict, cache_path: str):
    """将多个DataFrame打包存为单个parquet (用MultiIndex)."""
    frames = []
    for name, df in data.items():
        df_flat = df.stack().rename(name)
        frames.append(df_flat)

    combined = pd.concat(frames, axis=1)
    combined.index.names = ['trade_date', 'stock_code']

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    combined.to_parquet(cache_path, engine='pyarrow')
    size_mb = os.path.getsize(cache_path) / 1024 / 1024
    print(f"[cache] Saved to {cache_path} ({size_mb:.1f} MB)")


def _unpack_cache(cache_df: pd.DataFrame) -> dict:
    """从parquet缓存还原为字典格式."""
    data = {}
    for col in cache_df.columns:
        pivot = cache_df[col].unstack(level='stock_code')
        data[col] = pivot
    first_key = list(data.keys())[0]
    print(f"[cache] Loaded: {data[first_key].shape[0]} days x "
          f"{data[first_key].shape[1]} stocks, "
          f"fields: {list(data.keys())}")
    return data


# ============================================================
# 2. FundamentalTL 辅助数据 (领导洗过的长表)
# ============================================================

def load_fundamental_long_table(
    name: str,
    fundamental_dir: str = None,
    cache_dir: str = None,
) -> pd.DataFrame:
    """
    读取 FundamentalTL 的长表文件, 返回 pivot 矩阵.

    长表格式: ticker, tradeDate, value_column
    返回: DataFrame(index=trade_date, columns=stock_code_6digit)
    """
    if fundamental_dir is None:
        fundamental_dir = PATHS['fundamental']
    if cache_dir is None:
        cache_dir = PATHS['cache_dir']

    cache_path = os.path.join(cache_dir, f'ftl_{name}.parquet')

    # 尝试缓存
    if os.path.exists(cache_path):
        return pd.read_parquet(cache_path)

    fpath = os.path.join(fundamental_dir, f'{name}.csv')
    print(f"[load] Reading FundamentalTL: {fpath}")

    df = pd.read_csv(fpath)

    # 字段: ticker, tradeDate, 第三列(+)是值
    value_cols = [c for c in df.columns if c not in ('ticker', 'tradeDate')]
    value_col = value_cols[0]

    df['stock_code'] = df['ticker'].apply(_pad_ticker)
    df['trade_date'] = pd.to_datetime(df['tradeDate'])

    pivot = df.pivot_table(
        index='trade_date', columns='stock_code', values=value_col,
        aggfunc='first'
    ).sort_index()

    # 缓存
    os.makedirs(cache_dir, exist_ok=True)
    pivot.to_parquet(cache_path)
    size_mb = os.path.getsize(cache_path) / 1024 / 1024
    print(f"[cache] Saved {name} -> {cache_path} ({size_mb:.1f} MB)")

    return pivot


def load_limit_prices(fundamental_dir: str = None) -> dict:
    """加载涨跌停价 + 买卖标记."""
    return {
        'limit_up': load_fundamental_long_table('limitUpPrice', fundamental_dir),
        'limit_down': load_fundamental_long_table('limitDownPrice', fundamental_dir),
        'flag_buy': load_fundamental_long_table('flag_buy', fundamental_dir),
        'flag_sell': load_fundamental_long_table('flag_sell', fundamental_dir),
        'flag_st': load_fundamental_long_table('flag_st_new', fundamental_dir),
        'industry_zx1': load_fundamental_long_table('industry_zx_1_all', fundamental_dir),
    }


# ============================================================
# 3. isopen_gp.csv (已经是pivot矩阵)
# ============================================================

def load_isopen(
    fpath: str = None,
    cache_dir: str = None,
) -> pd.DataFrame:
    """
    加载停牌状态 pivot矩阵.
    格式: index=日期(带 ' 15:00:00' 后缀), columns=6位股票代码, values=0/1
    """
    if fpath is None:
        fpath = PATHS['isopen']
    if cache_dir is None:
        cache_dir = PATHS['cache_dir']

    cache_path = os.path.join(cache_dir, 'isopen_gp.parquet')

    if os.path.exists(cache_path):
        return pd.read_parquet(cache_path)

    print(f"[load] Reading isopen: {fpath}")
    df = pd.read_csv(fpath, index_col=0)

    # index: '2017-12-01 15:00:00' -> 去掉时间后缀
    df.index = pd.to_datetime(df.index.str[:10])
    df.index.name = 'trade_date'

    # columns已经是6位补零
    df.columns = [_pad_ticker(c) for c in df.columns]

    os.makedirs(cache_dir, exist_ok=True)
    df.to_parquet(cache_path)
    print(f"[cache] Saved isopen -> {cache_path}")

    return df


# ============================================================
# 4. 复权因子 (adj.csv, pivot矩阵)
# ============================================================

def load_adj_factor(
    fpath: str = None,
    cache_dir: str = None,
) -> pd.DataFrame:
    """加载后复权因子 pivot矩阵."""
    if fpath is None:
        fpath = PATHS['adj']
    if cache_dir is None:
        cache_dir = PATHS['cache_dir']

    cache_path = os.path.join(cache_dir, 'adj_factor.parquet')

    if os.path.exists(cache_path):
        return pd.read_parquet(cache_path)

    print(f"[load] Reading adj factor: {fpath}")
    df = pd.read_csv(fpath, index_col=0)
    df.index = pd.to_datetime(df.index)
    df.index.name = 'trade_date'
    df.columns = [_pad_ticker(c) for c in df.columns]

    os.makedirs(cache_dir, exist_ok=True)
    df.to_parquet(cache_path)
    return df


# ============================================================
# 5. 一站式加载函数
# ============================================================

def load_all_daily_data(
    start_date: str = '20240101',
    end_date: str = '20260327',
    load_limits: bool = True,
    load_isopen_flag: bool = True,
    kline_dir: str = None,
    fundamental_dir: str = None,
    cache_dir: str = None,
) -> dict:
    """
    一站式加载全部日频数据.

    Returns
    -------
    dict with keys:
        行情: open, close, high, low, lclose, vwap, volume, amount,
              turnover_rate, change_pct, mcap, adj_factor, industry
        限制: is_open, limit_up, limit_down, flag_buy, flag_sell,
              flag_st, industry_zx1
    """
    print("=" * 60)
    print(f"  Loading daily data: {start_date} ~ {end_date}")
    print("=" * 60)

    # Step 1: 日线行情
    _cache_dir = cache_dir or PATHS['cache_dir']
    data = load_daily_kline_from_csv(
        start_date=start_date,
        end_date=end_date,
        kline_dir=kline_dir,
        cache_path=os.path.join(_cache_dir, f'daily_kline_{start_date}_{end_date}.parquet'),
    )

    # Step 2: 涨跌停/ST/行业
    if load_limits:
        print("\n[load] Loading FundamentalTL auxiliary data...")
        limits = load_limit_prices(fundamental_dir)
        data.update(limits)

    # Step 3: isopen pivot
    if load_isopen_flag and 'is_open' not in data:
        data['is_open'] = load_isopen(cache_dir=_cache_dir)

    # 数据范围裁剪
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    for key in data:
        if isinstance(data[key], pd.DataFrame):
            if pd.api.types.is_datetime64_any_dtype(data[key].index):
                data[key] = data[key].loc[start_dt:end_dt]

    print(f"\n[load] Done. Fields: {list(data.keys())}")
    if 'close' in data:
        print(f"[load] Shape: {data['close'].shape[0]} days x {data['close'].shape[1]} stocks")

    return data


# ============================================================
# 6. 缓存管理
# ============================================================

def clear_cache(cache_dir: str = None):
    """清除所有parquet缓存."""
    if cache_dir is None:
        cache_dir = PATHS['cache_dir']
    import shutil
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        print(f"[cache] Cleared: {cache_dir}")


def list_cache(cache_dir: str = None):
    """列出缓存文件."""
    if cache_dir is None:
        cache_dir = PATHS['cache_dir']
    if not os.path.exists(cache_dir):
        print("[cache] No cache directory")
        return
    for f in sorted(os.listdir(cache_dir)):
        size = os.path.getsize(os.path.join(cache_dir, f)) / 1024 / 1024
        print(f"  {f:50s} {size:>8.1f} MB")


# ============================================================
# 7. 模拟数据生成器 (测试用)
# ============================================================

def generate_synthetic_data(
    n_stocks: int = 200,
    n_days: int = 500,
    start_date: str = '2024-04-01',
    factor_ic: float = 0.03,
    seed: int = 42,
) -> dict:
    """生成模拟数据用于测试."""
    np.random.seed(seed)

    dates = pd.bdate_range(start=start_date, periods=n_days)
    stocks = [f'{i:06d}' for i in range(1, n_stocks + 1)]

    true_signal = np.random.randn(n_days, n_stocks) * 0.02
    noise = np.random.randn(n_days, n_stocks) * 0.02
    returns = true_signal * 0.3 + noise

    prices = 20 * np.exp(np.cumsum(returns, axis=0))
    close = pd.DataFrame(prices, index=dates, columns=stocks)

    vwap_noise = 1 + np.random.randn(n_days, n_stocks) * 0.002
    vwap = close * vwap_noise

    future_ret = np.roll(returns, -1, axis=0)
    factor_noise = np.random.randn(n_days, n_stocks)
    factor_values = factor_ic * future_ret / 0.02 + np.sqrt(1 - factor_ic**2) * factor_noise
    factor = pd.DataFrame(factor_values, index=dates, columns=stocks)

    return {'close': close, 'vwap': vwap, 'factor': factor}


# ============================================================
# CLI
# ============================================================

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Data Loader')
    parser.add_argument('--csv', action='store_true', help='Load from csv files')
    parser.add_argument('--start', default='20240101')
    parser.add_argument('--end', default='20260327')
    parser.add_argument('--clear-cache', action='store_true')
    parser.add_argument('--list-cache', action='store_true')
    args = parser.parse_args()

    if args.clear_cache:
        clear_cache()
    elif args.list_cache:
        list_cache()
    elif args.csv:
        data = load_all_daily_data(start_date=args.start, end_date=args.end)
    else:
        print("Usage: python data_loader.py --csv / --clear-cache / --list-cache")
