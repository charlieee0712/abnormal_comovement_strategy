#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest_engine_fix.py — E1 引擎修正自测 (真数据, import-only, 只读地基 4 文件)
T1 复权因子对账: 后复权 close 日收益 == change_pct (交易日, 含复牌日), max|diff| < 1e-4
T2 除权事件计数: 事件数 > 20000; 报告中位假跌 / <-20% 占比 / 最小值
T3 旧口径回归: (exec_lag=0, adjust=False) 与 5623e59 版函数逐格相等 (calendar 4 序列 x 2 组权重 + forward), |d| <= 1e-15 且 NaN 位置相同
T4 两视角焊死: hold=1 池等权无成本, Calendar 有效仓位口径超额 .shift(-2) == compute_forward_5d_excess(hold=1) 池内均值/1e4, max|diff| < 1e-10, n > 3000
T5 前视探测器: S = close/vwap-1 (只含 T 日盘中信息), 池内 keep-HIGH 上半区等权, hold=5 无成本:
   旧口径 (exec_lag=0) NW > 5 且 年化 > +10%; 新口径年化比旧口径低 >= 5pp. 软检查 |新口径年化| < 2% (WARN 不算失败)
附: 池等权 vs 同池基准 在 exec_lag=0/1 下的年化与 NW, 只报告
"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import comprehensive_factor_diagnosis as C
from data_loader import load_all_daily_data
from event_study import get_base_pool

OUT = C.make_output_dir('engine_fix_selftest'); C.setup_dual_logging(OUT); print('[out]', OUT, flush=True)
results = []
def check(name, ok, detail):
    results.append((name, bool(ok))); print('[%s %s] %s' % (name, 'PASS' if ok else 'FAIL', detail), flush=True)

# ---------- legacy copies: 从 /tmp/cfd_5623e59.py 逐字粘贴, 只改函数名 ----------
def _legacy_forward(data, base_pool, hold_days=5):
    """5 日累积超额 (bp), 基准=base_pool 等权."""
    vwap = data['vwap']
    ref_idx = vwap.index
    ref_col = vwap.columns
    bp = base_pool.reindex(index=ref_idx, columns=ref_col).fillna(0)
    
    vwap_daily_ret = (vwap / vwap.shift(1) - 1).replace([np.inf, -np.inf], np.nan)
    bm_daily = vwap_daily_ret.where(bp == 1).mean(axis=1)
    excess_daily = vwap_daily_ret.sub(bm_daily, axis=0)
    
    forward_list = []
    for k in range(2, 2 + hold_days):
        forward_list.append(excess_daily.shift(-k))
    return sum(forward_list) * 1e4


def _legacy_calendar(weights, data, base_pool, hold_days=5, cost_bp_bilateral=6):
    """
    Calendar PnL: 5 日持有期, 持仓累积.
    
    实际持仓 = 过去 5 天选股的加权平均 (每天 1/5 仓位换一次)
    每日 PnL = sum(实际持仓权重 × 当日 daily return) - 当日基准 daily return × 总仓位
    """
    vwap = data['vwap']
    ref_idx = vwap.index
    ref_col = vwap.columns
    
    weights_aligned = weights.reindex(index=ref_idx, columns=ref_col).fillna(0)
    bp = base_pool.reindex(index=ref_idx, columns=ref_col).fillna(0)
    
    # 实际持仓 = 过去 5 天 weights 的均值 (每天换 1/hold_days)
    actual_holding = weights_aligned.rolling(hold_days, min_periods=1).mean()
    
    # 每日 daily return (VWAP-to-VWAP)
    daily_ret = (vwap / vwap.shift(1) - 1).replace([np.inf, -np.inf], np.nan)
    
    # 基准 daily ret = I11 池等权
    bm_daily = daily_ret.where(bp == 1).mean(axis=1)
    
    # 组合 daily PnL (gross): shift(1) 把 T 日的持仓信号对应 T+1 的收益
    actual_holding_t1 = actual_holding.shift(1)
    portfolio_daily_ret = (actual_holding_t1 * daily_ret).sum(axis=1)
    daily_position = actual_holding_t1.sum(axis=1).fillna(0)
    excess_daily = portfolio_daily_ret - bm_daily * daily_position
    
    # ★ 精确换手: 持仓 diff 的绝对值 / 2 (买入和卖出, 除2避免重复)
    holding_diff = actual_holding_t1.diff().abs().sum(axis=1) / 2.0
    holding_diff = holding_diff.fillna(0)
    
    # 扣成本: 每天的实际换手率 × 双边成本 (可配置, 默认6bp)
    daily_cost = holding_diff * (cost_bp_bilateral / 1e4)
    excess_daily_net = excess_daily - daily_cost
    
    return {
        'gross_excess_daily': excess_daily,
        'net_excess_daily': excess_daily_net,
        'daily_position': daily_position,
        'daily_turnover': holding_diff,
        'turnover_per_day': holding_diff.mean(),
        'turnover_annual': holding_diff.sum() / (len(holding_diff) / 252) if len(holding_diff) > 0 else 0,
    }
# ------------------------------------------------------------------------------

data = load_all_daily_data(start_date='20100101', end_date='20260327')
for k in ('close', 'lclose', 'vwap', 'is_open', 'change_pct'):
    assert k in data, 'data 缺字段 %s -> BLOCKER' % k
close, lclose, vwap = data['close'], data['lclose'], data['vwap']
pool = get_base_pool(data).reindex(index=vwap.index, columns=vwap.columns).fillna(0.0)
print('days', len(vwap.index), 'stocks', vwap.shape[1], 'range', vwap.index[0].date(), vwap.index[-1].date(), flush=True)

# ---------- T1 ----------
is_open = data['is_open'] == 1
close_v = close.where(is_open & (close > 0))          # 交易日收盘价; 停牌行(数据源填搬运值)置 NaN
lclose_v = lclose.where(is_open & (lclose > 0))
A = C.adjust_factor(data)
adj_close = close_v * A
ret_adj = adj_close / adj_close.ffill().shift(1) - 1   # 跨停牌: 复牌日对上一交易日
m = is_open & close_v.notna() & data['change_pct'].notna() & ret_adj.notna() & np.isfinite(ret_adj)
diff = (ret_adj - data['change_pct']).where(m)
mx = float(np.nanmax(np.abs(diff.values))); nbad = int((diff.abs() > 1e-4).sum().sum()); ncell = int(m.sum().sum())
check('T1', mx < 1e-4, '后复权 close 日收益 vs change_pct: cells=%d max|diff|=%.2e n(|diff|>1e-4)=%d' % (ncell, mx, nbad))

# ---------- T2 ----------
prev = close_v.ffill().shift(1)
ok = close_v.notna() & prev.notna() & lclose_v.notna()
ratio = (prev / lclose_v).where(ok)
ev = ratio.notna() & ((ratio - 1).abs() > 1e-6)
drop = (lclose_v / prev - 1).where(ev).stack()
n_ev = int(ev.sum().sum())
check('T2', n_ev > 20000, '除权事件 n=%d 中位假跌=%.2f%% 占比<-20%%=%.1f%% 最小=%.1f%%'
      % (n_ev, drop.median() * 100, (drop < -0.2).mean() * 100, drop.min() * 100))

# ---------- T3 ----------
def _same(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    if not np.array_equal(np.isnan(a), np.isnan(b)):
        return False, np.inf
    d = float(np.nanmax(np.abs(a - b))) if a.size else 0.0
    return d <= 1e-15, d
w_ew = pool.div(pool.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
rng = np.random.RandomState(0)
w_rand = pool * rng.rand(*pool.shape)
w_rand = w_rand.div(w_rand.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
t3_ok, t3_detail = True, []
for wname, w in (('ew', w_ew), ('rand', w_rand)):
    new = C.compute_calendar_pnl(w, data, pool, hold_days=5, cost_bp_bilateral=6, exec_lag=0, adjust=False)
    old = _legacy_calendar(w, data, pool, hold_days=5, cost_bp_bilateral=6)
    for key in ('gross_excess_daily', 'net_excess_daily', 'daily_position', 'daily_turnover'):
        okk, d = _same(new[key].values, old[key].values)
        t3_ok &= okk; t3_detail.append('%s/%s d=%.1e' % (wname, key, d))
okk, d = _same(C.compute_forward_5d_excess(data, pool, hold_days=5, adjust=False).values,
               _legacy_forward(data, pool, hold_days=5).values)
t3_ok &= okk; t3_detail.append('forward d=%.1e' % d)
check('T3', t3_ok, '旧口径逐格回归: ' + '; '.join(t3_detail))
del new, old

# ---------- T4 ----------
r = C.vwap_daily_return(data, adjust=True)
pr = C.compute_calendar_pnl(w_ew, data, pool, hold_days=1, cost_bp_bilateral=0)   # 默认 exec_lag=1, adjust=True
ah = w_ew.shift(2)
pos_eff = ah.where(r.notna()).sum(axis=1)
lhs = (pr['port_daily'] / pos_eff.replace(0, np.nan) - pr['bench_daily']).shift(-2)
fwd1 = C.compute_forward_5d_excess(data, pool, hold_days=1)                       # 默认 adjust=True, 单位 bp
rhs = fwd1.where(pool == 1).mean(axis=1) / 1e4
both = pd.concat([lhs.rename('lhs'), rhs.rename('rhs')], axis=1).dropna()
err = float((both.lhs - both.rhs).abs().max())
check('T4', (len(both) > 3000) and (err < 1e-10), '两视角焊死: n=%d max|diff|=%.1e' % (len(both), err))
del fwd1, pr

# ---------- T5 ----------
S = (close / vwap - 1).where(pool == 1)
keep = ((S.rank(axis=1, pct=True) > 0.5) & (pool == 1)).astype(float)
w_S = keep.div(keep.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
m_old = C.calendar_pnl_metrics(C.compute_calendar_pnl(w_S, data, pool, hold_days=5, cost_bp_bilateral=0, exec_lag=0, adjust=True)['gross_excess_daily'])
m_new = C.calendar_pnl_metrics(C.compute_calendar_pnl(w_S, data, pool, hold_days=5, cost_bp_bilateral=0)['gross_excess_daily'])
ao, nwo, an, nwn = m_old['annual_ret'], m_old['sharpe_nw'], m_new['annual_ret'], m_new['sharpe_nw']
hard = (nwo > 5) and (ao > 0.10) and ((ao - an) > 0.05)
check('T5', hard, '前视探测器 S=close/vwap-1 keep-HIGH: 旧口径 ann=%+.1f%% NW=%+.2f | 新口径 ann=%+.1f%% NW=%+.2f | 软检查 |新口径ann|<2%%: %s'
      % (ao * 100, nwo, an * 100, nwn, 'PASS' if abs(an) < 0.02 else 'WARN'))

# ---------- 附: 池等权自比 (只报告) ----------
for lag in (0, 1):
    mm = C.calendar_pnl_metrics(C.compute_calendar_pnl(w_ew, data, pool, hold_days=5, cost_bp_bilateral=0, exec_lag=lag, adjust=True)['gross_excess_daily'])
    print('[INFO] 池等权 vs 同池基准 exec_lag=%d: ann=%+.2f%% NW=%+.2f' % (lag, mm['annual_ret'] * 100, mm['sharpe_nw']), flush=True)

npass = sum(ok for _, ok in results)
print('[SELFTEST] %d/%d PASS' % (npass, len(results)), flush=True)
sys.exit(0 if npass == len(results) else 1)
