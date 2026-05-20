"""
Phase 1 v2: 事件收益评估 (修复版)
================================
修复:
    1. VWAP时序错误: T日收盘触发 → T+1日VWAP买入 → T+k+1日VWAP卖出
       (之前错误地用T日VWAP做买入价, 产生未来函数)
    2. 基准改为"基础池等权" (近似CSI 3800, 剔除ST/停牌/新股)
    3. 加入多空结构评估: 触发股票 vs 未触发股票
    4. 信号条件收紧, 控制每天触发数量在20-60只
    5. 三根收益线都能看 (绝对/超额/多空差)

数据源: (确认不是朝阳永续)
    - 行情: /mnt/big/base/shibo/KLines_make/daily_temp3/ (shibo从Uqer合成)
    - 辅助: /mnt/big/base/public/FundamentalTL/ (领导洗过)

用法:
    python event_study.py --csv --period 2024-2026
"""

import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features

PERIODS = {
    '2010-2014': ('20100104', '20141231'),
    '2015-2018': ('20150101', '20181231'),
    '2019-2023': ('20190101', '20231231'),
    '2024-2026': ('20240101', '20260327'),
}


def get_base_pool(data):
    pool = pd.DataFrame(True, index=data['close'].index, columns=data['close'].columns)
    if 'is_open' in data:
        pool = pool & (data['is_open'] == 1).reindex_like(pool).fillna(False)
    if 'flag_st' in data:
        pool = pool & (data['flag_st'] != 1).reindex_like(pool).fillna(True)
    pool = pool & (data['volume'] > 0) & (data['close'] > 0) & (data['lclose'] > 0)
    return pool.astype(float)


# ============================================================
# 入场信号 (收紧版, 只在基础池内排名)
# ============================================================

def define_entry_signals(features, base_pool):
    """
    入场信号定义.
    
    A-E: 原baseline (动量/筛选), 用于对比
    I1-I10: 第一批创新逻辑 (基于研究报告, 大部分失败)
        I1: IMOM日内动量替代全天动量 (A2)
        I2: FIP连续型动量过滤 (A1)
        I3: 聪明钱共振CLV (D2 + 趋势)
        I4: 隔夜惩罚动量 (A4)
        I5: 健康反转 (B1精神 + B4)
        I6: Tug-of-War反转 (B3)
        I7: 资金流CMF共振 (D4) ← 唯一跨段稳定非负
        I8: 影线+CLV尾盘强势 (D5 + D2)
        I9: CVR尾盘强势动量 (A3)
        I10: 价量正相关共振 (D1 RPV简化版)
    
    I11-I13: 第二批创新 (基于I7洞察反向推导, 非翻译研报)
        I11: 隐藏建仓 (资金流领先于价格的极端版)
        I12: 三重资金流共振 (CMF+CVR+CLV叠加)
        I13: 低换手隐藏建仓 (低换手+资金流)
    """
    bp = base_pool.reindex_like(features['intraday_ret']).fillna(0)
    mask = bp == 1
    
    def pct_in_pool(feat_name):
        f = features[feat_name].reindex_like(bp).where(mask)
        return f.rank(axis=1, pct=True)
    
    # ---- baseline特征 ----
    ir_pct = pct_in_pool('intraday_ret')
    cr5_pct = pct_in_pool('cum_return_5d')
    cr20_pct = pct_in_pool('cum_return_20d')
    dfh_pct = pct_in_pool('distance_from_high_20d')
    ag = features['agreement_count_5d'].reindex_like(bp)
    vrb = features['volume_regime_break'].reindex_like(bp)
    ct_pct = pct_in_pool('conditional_turnover')
    vmd_pct = pct_in_pool('volume_momentum_divergence')
    dvr_pct = pct_in_pool('drawdown_volume_ratio')
    rv_pct = pct_in_pool('realized_vol_20d')
    
    # ---- 创新特征 (B3.1) ----
    imom20_pct = pct_in_pool('cum_intraday_ret_20d')
    imom5_pct = pct_in_pool('cum_intraday_ret_5d')
    fip = features['info_discreteness_20d'].reindex_like(bp).where(mask)
    fip_pct = fip.rank(axis=1, pct=True)  # 越小=越连续
    overshare_pct = pct_in_pool('overnight_return_ratio_20d')  # 越小=越不依赖隔夜
    clv = features['CLV'].reindex_like(bp).where(mask)
    clv20_pct = pct_in_pool('CLV_20d')
    cmf_pct = pct_in_pool('CMF_20d')
    sa_pct = pct_in_pool('shadow_asymmetry_20d')  # 越小=下影线越长(支撑强)
    tw_pct = pct_in_pool('tug_of_war_20d')  # 越小=日内抛压大(反转强)
    aa_pct = pct_in_pool('amihud_asymmetry_20d')  # 越小=跌时冲击小
    
    # ---- 新增特征: CVR / CCV / 换手波动 ----
    cvr_today = features['CVR'].reindex_like(bp).where(mask)
    cvr20_pct = pct_in_pool('CVR_20d')
    ccv20_pct = pct_in_pool('CCV_20d')
    tv60_pct = pct_in_pool('turnover_volatility_60d')
    
    signals = {}
    
    # ============================================================
    # baseline 5个 (用于对比)
    # ============================================================
    signals['A_ultra_momentum'] = (
        (ir_pct >= 0.99) & (cr5_pct >= 0.90) & (ag >= 3) & mask
    ).astype(float)
    
    signals['B_momentum_vol_break'] = (
        (ir_pct >= 0.95) & (vrb == 1) & (cr5_pct >= 0.70) & mask
    ).astype(float)
    
    signals['C_momentum_trend'] = (
        (ir_pct >= 0.97) & (dfh_pct >= 0.90) & (ag >= 2) & mask
    ).astype(float)
    
    bad = (ct_pct >= 0.80) | (vmd_pct <= 0.20) | (dvr_pct <= 0.20)
    signals['D_A_filtered'] = (
        (signals['A_ultra_momentum'] == 1) & (~bad)
    ).astype(float)
    
    signals['E_pure_momentum'] = (
        (ir_pct >= 0.99) & mask
    ).astype(float)
    
    # ============================================================
    # 创新逻辑 8个 (基于研究报告)
    # ============================================================
    
    # I1: IMOM日内动量 (A2 - 最重要)
    # 用cum_intraday_ret_20d代替cum_return_5d, 直接对齐VWAP执行段
    # 选: 20日累积日内涨幅Top5% + 当天日内不疯狂
    signals['I1_IMOM_momentum'] = (
        (imom20_pct >= 0.95) &
        (ir_pct < 0.95) &  # 关键: 当天不能是最强的(否则次日高开)
        (ir_pct >= 0.50) &  # 但当天也不能跌
        mask
    ).astype(float)
    
    # I2: FIP连续型动量 (A1)
    # 选: 20日有正动量 + FIP极负(信息连续, 多天小涨, 散户没察觉)
    signals['I2_FIP_continuous'] = (
        (cr20_pct >= 0.85) &
        (fip_pct <= 0.15) &  # FIP最负的15% (最连续)
        (ir_pct < 0.90) &  # 当天不极端
        mask
    ).astype(float)
    
    # I3: 聪明钱共振 (D2 + 趋势)
    # 选: CLV_20d高(尾盘持续买压) + 20日动量正 + 当天CLV>0(尾盘买入)
    signals['I3_smart_money'] = (
        (clv20_pct >= 0.85) &
        (cr20_pct >= 0.70) &
        (clv > 0) &
        (ir_pct < 0.90) &  # 当天非疯狂
        mask
    ).astype(float)
    
    # I4: 隔夜惩罚动量 (A4)
    # 选: 5日有动量 + 隔夜占比低(不依赖跳空) + 当天日内涨
    signals['I4_overnight_penalized'] = (
        (cr5_pct >= 0.80) &
        (overshare_pct <= 0.30) &  # 隔夜收益占比最低30%
        (imom5_pct >= 0.70) &  # 5日日内动量也要正
        mask
    ).astype(float)
    
    # I5: 健康反转 (B1+B4精神, 无FSCORE的简化版)
    # 选: 5日大跌 + 离前高不远(健康) + 量没崩(支撑强) + 流动性正常
    signals['I5_healthy_reversal'] = (
        (cr5_pct <= 0.10) &  # 5日跌幅Top10%
        (dfh_pct >= 0.30) &  # 离前高不至于太远(>P30, 不是趋势崩溃)
        (sa_pct <= 0.30) &  # 影线: 下影长(P30以下=支撑强)
        (aa_pct <= 0.50) &  # 跌时冲击不夸张(不是恐慌盘)
        mask
    ).astype(float)
    
    # I6: Tug-of-War反转 (B3)
    # 选: 隔夜vs日内角力极负(日内抛压远大于隔夜买盘) + 趋势仍在
    signals['I6_tug_of_war'] = (
        (tw_pct <= 0.10) &  # TW极负
        (cr20_pct >= 0.40) &  # 20日没崩
        (rv_pct >= 0.50) &  # 有波动空间
        mask
    ).astype(float)
    
    # I7: 资金流共振 (D4)
    # 选: CMF高(订单流持续买入) + 价格温和上涨 + 当天不追高
    signals['I7_money_flow'] = (
        (cmf_pct >= 0.90) &
        (cr5_pct >= 0.50) & (cr5_pct <= 0.85) &  # 温和涨, 不在最强
        (ir_pct < 0.85) &
        mask
    ).astype(float)
    
    # I8: 影线+CLV尾盘强势 (D5 + D2)
    # 选: 影线非对称负(下影长) + CLV高(尾盘买) + 5日有动量
    signals['I8_tail_strength'] = (
        (sa_pct <= 0.20) &  # 下影线长(支撑强)
        (clv20_pct >= 0.80) &  # 尾盘持续偏强
        (cr5_pct >= 0.50) &
        (ir_pct < 0.95) &
        mask
    ).astype(float)
    
    # I9: CVR尾盘强势动量 (A3)
    # 选: 持续尾盘强势(CVR_20d高) + 5日趋势 + 当天尾盘也强 + 离前高近
    # 逻辑: 机构持续在尾盘吸筹, 这类股票次日高开概率低, 且趋势会延续
    signals['I9_CVR_tail_close'] = (
        (cvr20_pct >= 0.85) &  # 持续尾盘强势
        (cvr_today > 0) &  # 今天也是尾盘强势
        (cr5_pct >= 0.50) &  # 有动量
        (dfh_pct >= 0.60) &  # 离前高不远
        (ir_pct < 0.90) &  # 当天非疯狂
        mask
    ).astype(float)
    
    # I10: 价量正相关共振 (D1 RPV简化版)
    # 选: 价量正相关高(健康量价配合) + 中等动量 + 量能加速
    # 逻辑: CCV高=量增价涨健康, 不在最强(P50-P85)避免高开
    signals['I10_price_volume_sync'] = (
        (ccv20_pct >= 0.85) &  # 20日价量正相关Top15%
        (cr5_pct >= 0.50) & (cr5_pct <= 0.85) &  # 中等动量
        (vrb == 1) &  # 量能确认
        (ir_pct < 0.90) &
        mask
    ).astype(float)
    
    # ============================================================
    # I11-I13: 基于I7洞察的真正创新 (非翻译研报)
    # ============================================================
    # 核心观察: I7 (CMF高 + 温和动量 + 不追高) 是唯一跨段稳定非负的信号.
    # 这3个信号围绕I7的核心机制做不同方向的探索.
    
    # I11: 隐藏建仓 (stealth accumulation)
    # 假设: alpha来自"资金流领先于价格". 如果CMF+CLV高但价格还没涨, 
    #       说明主力在吸筹但还没拉抬, VWAP执行下最理想.
    # 与I7区别: 不要求动量, 反而要求"价格没涨"
    signals['I11_stealth_accumulation'] = (
        (cmf_pct >= 0.90) &           # 订单流极强
        (clv20_pct >= 0.80) &          # 持续尾盘吸筹  
        (cr5_pct >= 0.30) & (cr5_pct <= 0.60) &  # 价格还没明显涨!
        (cvr20_pct >= 0.70) &          # 持续尾盘强于VWAP
        (ir_pct < 0.70) &              # 今天也不涨
        mask
    ).astype(float)
    
    # I12: 三重资金流共振 (triple smart money)
    # 假设: CMF/CVR/CLV是3个独立的资金流代理, 同时满足=强共振.
    # 与I7区别: 放宽动量要求(只要不是弱势), 用3个资金流叠加替代动量过滤
    signals['I12_triple_smart_money'] = (
        (cmf_pct >= 0.85) &            # CMF: 订单流
        (cvr20_pct >= 0.85) &          # CVR: 20日持续尾盘强于VWAP
        (clv20_pct >= 0.80) &          # CLV: 20日持续尾盘收高
        (cr5_pct >= 0.40) &            # 弱趋势(不要求强)
        (ir_pct < 0.80) &              # 当天非疯狂
        mask
    ).astype(float)
    
    # I13: 低换手隐藏建仓 (low turnover accumulation)
    # 假设: 低换手+资金流 = 主力低调建仓, 散户没发现, VWAP成本低.
    # 与I7区别: I7不控制换手率, I13明确要求低换手
    signals['I13_low_turnover_accumulation'] = (
        (cmf_pct >= 0.85) &            # 订单流持续流入
        (ct_pct <= 0.40) &             # 换手率低 (不是散户炒作)
        (tv60_pct <= 0.40) &           # 换手波动低 (稳定低换手, 不是突发躁动)
        (dfh_pct >= 0.50) &            # 离前高不远
        (cr5_pct >= 0.40) &            # 有弱动量
        (ir_pct < 0.80) &
        mask
    ).astype(float)
    
    return signals


def define_negative_signals(features, base_pool):
    bp = base_pool.reindex_like(features['intraday_ret']).fillna(0)
    mask = bp == 1
    
    def pct_in_pool(feat_name):
        f = features[feat_name].reindex_like(bp).where(mask)
        return f.rank(axis=1, pct=True)
    
    ir_pct = pct_in_pool('intraday_ret')
    cr5_pct = pct_in_pool('cum_return_5d')
    dvr_pct = pct_in_pool('drawdown_volume_ratio')
    
    signals = {}
    signals['NEG_intraday_crash'] = ((ir_pct <= 0.01) & mask).astype(float)
    signals['NEG_dump'] = ((cr5_pct <= 0.05) & (dvr_pct <= 0.10) & mask).astype(float)
    
    return signals


# ============================================================
# 前瞻收益 (修复VWAP时序 + 延迟入场)
# ============================================================

def calc_forward_returns(data, max_horizon=20):
    """
    CC: T日close买入, T+k日close卖出.
    
    VWAP (默认): T+1 VWAP买入, T+k+1 VWAP卖出
        vwap_k[T] = VWAP_{T+k+1} / VWAP_{T+1} - 1
    
    VWAP延迟入场 (新增): 跳过信号后几天再买, 避开高开冲击
        vwap_d3_k[T] = VWAP_{T+k+3} / VWAP_{T+3} - 1  (T+3 VWAP买入)
        vwap_d5_k[T] = VWAP_{T+k+5} / VWAP_{T+5} - 1  (T+5 VWAP买入)
    """
    close = data['close']
    vwap = data['vwap']
    
    fwd = {}
    for k in range(1, max_horizon + 1):
        fwd[f'cc_{k}d'] = close.shift(-k) / close - 1
        fwd[f'vwap_{k}d'] = vwap.shift(-k - 1) / vwap.shift(-1) - 1
        # 延迟入场 (T+3/T+5 买入)
        fwd[f'vwap_d3_{k}d'] = vwap.shift(-k - 3) / vwap.shift(-3) - 1
        fwd[f'vwap_d5_{k}d'] = vwap.shift(-k - 5) / vwap.shift(-5) - 1
    
    return fwd


def calc_benchmark_returns(data, base_pool, max_horizon=20):
    """基础池等权日度基准. 包含延迟入场的基准."""
    close = data['close']
    vwap = data['vwap']
    bp = base_pool.reindex_like(close).fillna(0)
    mask = bp == 1
    
    cc_daily = (close / close.shift(1) - 1).where(mask)
    cc_bm = cc_daily.mean(axis=1)
    
    vwap_daily = (vwap / vwap.shift(1) - 1).where(mask)
    vwap_bm = vwap_daily.mean(axis=1)
    
    bm = {}
    for k in range(1, max_horizon + 1):
        # CC: T+1到T+k累积
        cc_c = pd.Series(0.0, index=cc_bm.index)
        for j in range(1, k + 1):
            cc_c = cc_c + cc_bm.shift(-j).fillna(0)
        bm[f'cc_{k}d'] = cc_c
        
        # VWAP (T+1买): T+2到T+k+1累积
        vwap_c = pd.Series(0.0, index=vwap_bm.index)
        for j in range(2, k + 2):
            vwap_c = vwap_c + vwap_bm.shift(-j).fillna(0)
        bm[f'vwap_{k}d'] = vwap_c
        
        # VWAP延迟3天入场: T+4到T+k+3累积
        vwap_d3 = pd.Series(0.0, index=vwap_bm.index)
        for j in range(4, k + 4):
            vwap_d3 = vwap_d3 + vwap_bm.shift(-j).fillna(0)
        bm[f'vwap_d3_{k}d'] = vwap_d3
        
        # VWAP延迟5天入场: T+6到T+k+5累积
        vwap_d5 = pd.Series(0.0, index=vwap_bm.index)
        for j in range(6, k + 6):
            vwap_d5 = vwap_d5 + vwap_bm.shift(-j).fillna(0)
        bm[f'vwap_d5_{k}d'] = vwap_d5
    
    return bm


# ============================================================
# 事件研究
# ============================================================

def event_study(signal, fwd, bm, base_pool, signal_name,
                horizons=[1, 2, 3, 5, 10, 20]):
    bp = base_pool.reindex_like(signal).fillna(0)
    mask = bp == 1
    sig = signal.where(mask, 0)
    neg_sig = ((sig == 0) & mask).astype(float)
    
    daily_count = sig.sum(axis=1)
    total = int(daily_count.sum())
    avg = daily_count.mean()
    trig_days = (daily_count > 0).sum()
    total_days = len(daily_count)
    
    print(f"\n  {'─'*65}")
    print(f"  信号: {signal_name}")
    print(f"  触发: 总{total}次, 日均{avg:.1f}只, 触发天数{trig_days}/{total_days} ({trig_days/total_days:.1%})")
    
    if total == 0:
        return None
    
    results = {'signal': signal_name, 'total': total, 'avg_daily': avg}
    
    print(f"\n  CC模式 (T日close买, T+k日close卖):")
    print(f"  {'期':>5s} {'触发均值':>10s} {'基准均值':>10s} {'超额':>10s} {'多空差':>10s} {'超额胜率':>9s}")
    print(f"  {'─'*5} {'─'*10} {'─'*10} {'─'*10} {'─'*10} {'─'*9}")
    
    for h in horizons:
        cc_ret = fwd[f'cc_{h}d'].reindex_like(sig)
        cc_bm = bm[f'cc_{h}d'].reindex(sig.index)
        
        trig_ret = cc_ret.where(sig == 1).stack().dropna()
        if len(trig_ret) == 0: continue
        neg_ret = cc_ret.where(neg_sig == 1).stack().dropna()
        
        bm_vals = []
        for date in sig.index:
            n = int(sig.loc[date].sum())
            if n > 0 and date in cc_bm.index:
                bm_vals.extend([cc_bm.loc[date]] * n)
        bm_arr = np.array(bm_vals) if bm_vals else np.array([0])
        bm_arr = bm_arr[:len(trig_ret)]
        
        trig_mean = trig_ret.mean() * 10000
        bm_mean = bm_arr.mean() * 10000
        excess = trig_mean - bm_mean
        ls = (trig_ret.mean() - neg_ret.mean()) * 10000 if len(neg_ret) > 0 else 0
        wr = ((trig_ret.values - bm_arr) > 0).mean()
        
        print(f"  T+{h:<3d} {trig_mean:>10.2f} {bm_mean:>10.2f} {excess:>10.2f} "
              f"{ls:>10.2f} {wr:>9.1%}")
        
        results[f'cc_{h}d_trig'] = trig_mean
        results[f'cc_{h}d_bm'] = bm_mean
        results[f'cc_{h}d_excess'] = excess
        results[f'cc_{h}d_ls'] = ls
        results[f'cc_{h}d_wr'] = wr
    
    def _eval_mode(mode_key, mode_label, horizons_to_use):
        """计算某个模式(vwap/vwap_d3/vwap_d5)下的触发收益."""
        print(f"\n  {mode_label}:")
        print(f"  {'期':>5s} {'触发均值':>10s} {'基准均值':>10s} {'超额':>10s} {'多空差':>10s} {'超额胜率':>9s}")
        print(f"  {'─'*5} {'─'*10} {'─'*10} {'─'*10} {'─'*10} {'─'*9}")
        
        for h in horizons_to_use:
            ret = fwd[f'{mode_key}_{h}d'].reindex_like(sig)
            bm_s = bm[f'{mode_key}_{h}d'].reindex(sig.index)
            
            trig_ret = ret.where(sig == 1).stack().dropna()
            if len(trig_ret) == 0: continue
            neg_ret = ret.where(neg_sig == 1).stack().dropna()
            
            bm_vals = []
            for date in sig.index:
                n = int(sig.loc[date].sum())
                if n > 0 and date in bm_s.index:
                    bm_vals.extend([bm_s.loc[date]] * n)
            bm_arr = np.array(bm_vals) if bm_vals else np.array([0])
            bm_arr = bm_arr[:len(trig_ret)]
            
            trig_mean = trig_ret.mean() * 10000
            bm_mean = bm_arr.mean() * 10000
            excess = trig_mean - bm_mean
            ls = (trig_ret.mean() - neg_ret.mean()) * 10000 if len(neg_ret) > 0 else 0
            wr = ((trig_ret.values - bm_arr) > 0).mean()
            
            print(f"  T+{h:<3d} {trig_mean:>10.2f} {bm_mean:>10.2f} {excess:>10.2f} "
                  f"{ls:>10.2f} {wr:>9.1%}")
            
            results[f'{mode_key}_{h}d_trig'] = trig_mean
            results[f'{mode_key}_{h}d_bm'] = bm_mean
            results[f'{mode_key}_{h}d_excess'] = excess
            results[f'{mode_key}_{h}d_ls'] = ls
            results[f'{mode_key}_{h}d_wr'] = wr
    
    # VWAP标准: T+1 买入, 持有k天
    _eval_mode('vwap', 'VWAP标准 (T+1 VWAP买入, 持有k天)', [h for h in horizons if h >= 2])
    
    # VWAP延迟3天入场: T+3 买入, 持有k天
    _eval_mode('vwap_d3', 'VWAP延迟3天 (T+3 VWAP买入, 避开高开冲击)', [h for h in horizons if h >= 2])
    
    # VWAP延迟5天入场: T+5 买入, 持有k天
    _eval_mode('vwap_d5', 'VWAP延迟5天 (T+5 VWAP买入, 更保守)', [h for h in horizons if h >= 2])
    
    print(f"\n  日均衰减 (累积/天数, bp):")
    print(f"  {'期':>5s} {'CC超额日均':>12s} {'VWAP超额日均':>14s} {'CC多空日均':>12s}")
    for h in horizons:
        cc_ex = results.get(f'cc_{h}d_excess', 0)
        vwap_ex = results.get(f'vwap_{h}d_excess', None)
        cc_ls = results.get(f'cc_{h}d_ls', 0)
        vwap_str = f"{vwap_ex/h:>14.2f}" if vwap_ex is not None else f"{'-':>14s}"
        print(f"  T+{h:<3d} {cc_ex/h:>12.2f} {vwap_str} {cc_ls/h:>12.2f}")
    
    return results


def plot_decay(all_results, output_dir, period_name):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    horizons = [1, 2, 3, 5, 10, 20]
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    
    for name, r in all_results.items():
        if r is None: continue
        cc_ex = [r.get(f'cc_{h}d_excess', 0) for h in horizons]
        cc_ls = [r.get(f'cc_{h}d_ls', 0) for h in horizons]
        vwap_pairs = [(h, r.get(f'vwap_{h}d_excess')) for h in horizons]
        vwap_pairs = [(h, v) for h, v in vwap_pairs if v is not None]
        
        axes[0,0].plot(horizons, cc_ex, 'o-', label=name, markersize=4)
        axes[0,1].plot(horizons, cc_ls, 'o-', label=name, markersize=4)
        if vwap_pairs:
            hx, vy = zip(*vwap_pairs)
            axes[1,0].plot(hx, vy, 's--', label=name, markersize=4, alpha=0.8)
        cc_daily = [x/h for x, h in zip(cc_ex, horizons)]
        axes[1,1].plot(horizons, cc_daily, 'o-', label=name, markersize=4)
    
    titles = [
        f'{period_name} - CC Cumulative Excess (bp)',
        f'{period_name} - CC Long-Short Spread (bp)',
        f'{period_name} - VWAP Cumulative Excess (bp)',
        f'{period_name} - CC Daily Avg Excess (bp/day)',
    ]
    for ax, t in zip(axes.flatten(), titles):
        ax.set_title(t, fontsize=10)
        ax.set_xlabel('Holding Days')
        ax.axhline(y=0, color='black', linewidth=0.5)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
    
    fig.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    save_path = f'{output_dir}/{period_name}_decay.png'
    fig.savefig(save_path, dpi=150)
    plt.close('all')
    print(f"\n  [plot] {save_path}")


def run_period(period_name, start, end, output_dir):
    print(f"\n\n{'#'*80}")
    print(f"  Phase 1 v2: {period_name} ({start}~{end})")
    print(f"{'#'*80}")
    
    data = load_all_daily_data(start, end)
    features = calc_all_daily_features(data)
    bp = get_base_pool(data)
    
    print(f"\n  数据: {data['close'].shape[0]}天 × {data['close'].shape[1]}只, "
          f"基础池avg={bp.sum(axis=1).mean():.0f}只")
    
    fwd = calc_forward_returns(data, max_horizon=20)
    bm = calc_benchmark_returns(data, bp, max_horizon=20)
    
    entry_sigs = define_entry_signals(features, bp)
    neg_sigs = define_negative_signals(features, bp)
    
    print(f"\n\n{'='*60}\n  入场信号评估\n{'='*60}")
    all_results = {}
    for name, sig in entry_sigs.items():
        all_results[name] = event_study(sig, fwd, bm, bp, name)
    
    print(f"\n\n{'='*60}\n  负向信号评估\n{'='*60}")
    for name, sig in neg_sigs.items():
        all_results[name] = event_study(sig, fwd, bm, bp, name)
    
    entry_r = {k: v for k, v in all_results.items() 
               if not k.startswith('NEG') and v is not None}
    plot_decay(entry_r, output_dir, period_name)
    
    # 汇总表
    print(f"\n\n{'='*80}\n  {period_name} 汇总: CC 超额收益 (bp)\n{'='*80}")
    print(f"  {'信号':30s} {'日均':>6s} {'T+1':>7s} {'T+3':>7s} {'T+5':>7s} "
          f"{'T+10':>7s} {'T+20':>7s} {'T+5胜率':>8s}")
    for name, r in all_results.items():
        if r is None: continue
        print(f"  {name:30s} {r['avg_daily']:>6.1f} "
              f"{r.get('cc_1d_excess', 0):>7.1f} {r.get('cc_3d_excess', 0):>7.1f} "
              f"{r.get('cc_5d_excess', 0):>7.1f} {r.get('cc_10d_excess', 0):>7.1f} "
              f"{r.get('cc_20d_excess', 0):>7.1f} {r.get('cc_5d_wr', 0):>8.1%}")
    
    print(f"\n  {period_name} 汇总: CC 多空差 (bp)")
    print(f"  {'信号':30s} {'T+1':>7s} {'T+3':>7s} {'T+5':>7s} {'T+10':>7s} {'T+20':>7s}")
    for name, r in all_results.items():
        if r is None: continue
        print(f"  {name:30s} "
              f"{r.get('cc_1d_ls', 0):>7.1f} {r.get('cc_3d_ls', 0):>7.1f} "
              f"{r.get('cc_5d_ls', 0):>7.1f} {r.get('cc_10d_ls', 0):>7.1f} "
              f"{r.get('cc_20d_ls', 0):>7.1f}")
    
    print(f"\n  {period_name} 汇总: VWAP 超额收益 (bp, T+1买入)")
    print(f"  {'信号':30s} {'T+2':>7s} {'T+3':>7s} {'T+5':>7s} {'T+10':>7s} {'T+20':>7s}")
    for name, r in all_results.items():
        if r is None: continue
        print(f"  {name:30s} "
              f"{r.get('vwap_2d_excess', 0):>7.1f} {r.get('vwap_3d_excess', 0):>7.1f} "
              f"{r.get('vwap_5d_excess', 0):>7.1f} {r.get('vwap_10d_excess', 0):>7.1f} "
              f"{r.get('vwap_20d_excess', 0):>7.1f}")
    
    print(f"\n  {period_name} 汇总: VWAP 延迟3天 超额收益 (bp, T+3 VWAP买入, 避开高开)")
    print(f"  {'信号':30s} {'T+2':>7s} {'T+3':>7s} {'T+5':>7s} {'T+10':>7s} {'T+20':>7s}")
    for name, r in all_results.items():
        if r is None: continue
        print(f"  {name:30s} "
              f"{r.get('vwap_d3_2d_excess', 0):>7.1f} {r.get('vwap_d3_3d_excess', 0):>7.1f} "
              f"{r.get('vwap_d3_5d_excess', 0):>7.1f} {r.get('vwap_d3_10d_excess', 0):>7.1f} "
              f"{r.get('vwap_d3_20d_excess', 0):>7.1f}")
    
    print(f"\n  {period_name} 汇总: VWAP 延迟5天 超额收益 (bp, T+5 VWAP买入, 更保守)")
    print(f"  {'信号':30s} {'T+2':>7s} {'T+3':>7s} {'T+5':>7s} {'T+10':>7s} {'T+20':>7s}")
    for name, r in all_results.items():
        if r is None: continue
        print(f"  {name:30s} "
              f"{r.get('vwap_d5_2d_excess', 0):>7.1f} {r.get('vwap_d5_3d_excess', 0):>7.1f} "
              f"{r.get('vwap_d5_5d_excess', 0):>7.1f} {r.get('vwap_d5_10d_excess', 0):>7.1f} "
              f"{r.get('vwap_d5_20d_excess', 0):>7.1f}")
    
    # 延迟入场效果对比 (T+5持有期)
    print(f"\n  {period_name} 延迟入场效果对比 (T+5持有期超额收益, bp)")
    print(f"  {'信号':30s} {'T+1买':>8s} {'T+3买':>8s} {'T+5买':>8s} {'delta_d3':>10s} {'delta_d5':>10s}")
    for name, r in all_results.items():
        if r is None: continue
        v0 = r.get('vwap_5d_excess', 0)
        v3 = r.get('vwap_d3_5d_excess', 0)
        v5 = r.get('vwap_d5_5d_excess', 0)
        print(f"  {name:30s} {v0:>8.1f} {v3:>8.1f} {v5:>8.1f} "
              f"{v3-v0:>10.1f} {v5-v0:>10.1f}")
    
    os.makedirs(output_dir, exist_ok=True)
    df = pd.DataFrame([r for r in all_results.values() if r is not None])
    df.to_csv(f'{output_dir}/{period_name}_event_study.csv', index=False)
    
    return all_results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', action='store_true')
    parser.add_argument('--period', default='2024-2026')
    parser.add_argument('--output', default='./output_phase1_v2')
    args = parser.parse_args()
    
    if not args.csv:
        print("Usage: python event_study.py --csv [--period 2024-2026/all]")
        sys.exit(0)
    
    if args.period == 'all':
        periods = PERIODS
    elif args.period in PERIODS:
        periods = {args.period: PERIODS[args.period]}
    else:
        print(f"Available: {list(PERIODS.keys())} or 'all'")
        sys.exit(1)
    
    for pname, (start, end) in periods.items():
        run_period(pname, start, end, args.output)
    
    print(f"\n[done] → {args.output}/")
