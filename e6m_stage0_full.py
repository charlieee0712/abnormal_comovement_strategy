# -*- coding: utf-8 -*-
"""E6m 阶段 N · N5 全程项（附录 A4-2 / A4-3 / A4-4 / A4-7 / A4-8；A6-1 / A6-2）。不读任何前向收益（只算形成日已知的特征与可得性）。
状态序列：e6l_state.compute(data=…) 原函数 + build_cache() 函数体（:213–228）逐行复刻，只把输出写进 E6m 工作目录；
数据经四地基 data_loader.load_all_daily_data 同参数加载（e6l_state.load_full 内部 import e6f_core，云机 import 期读 roles.csv 失败，
brief W15）。pool0 格取自 N5 分段重建的 pool1 部件（= p0 格）。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import inspect
import argparse
import resource

import numpy as np
import pandas as pd

import data_loader as DL
import e6m_core as M

FULL = ('20100101', '20260327')
SEG = {'2010-2014': ('2010-01-04', '2014-12-31'), '2015-2018': ('2015-01-01', '2018-12-31'), '2019-2023': ('2019-01-01', '2023-12-31'),
       '2024-2026': ('2024-01-01', '2026-03-27')}
FTL = ('flag_buy', 'flag_sell', 'flag_st_new', 'industry_zx_1_all', 'limitDownPrice', 'limitUpPrice')
ROWS = []


def put(table, **kw):
    ROWS.append(dict(table=table, **kw))


def cache_dir():
    return os.path.join(os.path.dirname(os.path.dirname(M.CODE.rstrip('/'))), 'data', 'cache')


def load_full():
    cd = cache_dir()
    need = ['daily_kline_%s_%s.parquet' % FULL] + ['ftl_%s.parquet' % x for x in FTL]
    miss = [f for f in need if not os.path.exists(os.path.join(cd, f))]
    if miss:
        raise RuntimeError('缓存缺件：%s' % miss)
    M.assert_end_ok(FULL[1], 'full load')
    DL.PATHS['cache_dir'] = cd
    before = sorted(os.listdir(cd))
    data = DL.load_all_daily_data(start_date=FULL[0], end_date=FULL[1], cache_dir=cd)
    M.assert_index_ok(data['close'].index, 'full close')
    return data, before, cd


def pool0_mask(close):
    """N5 pool1 部件（ticker 去零整数 / tradeDate）→ 全程网格布尔。"""
    out = np.zeros(close.shape, bool)
    di = {str(d)[:10]: i for i, d in enumerate(close.index)}
    ci = {int(c): j for j, c in enumerate(close.columns)}
    for s in SEG:
        p = pd.read_parquet(M.P('stage0', 'c2_rebuild_parts', s, 'pool1.parquet'))
        r = p.tradeDate.map(di)
        c = p.ticker.map(ci)
        ok = r.notna() & c.notna()
        out[r[ok].astype(int).to_numpy(), c[ok].astype(int).to_numpy()] = True
    return out


def seg_rows(dates, s):
    a, b = SEG[s]
    return (dates >= pd.Timestamp(a)) & (dates <= pd.Timestamp(b))


def task_state(data, dates, p0):
    import e6l_state as LS
    t0 = time.time()
    st = LS.compute(data=data)
    code = LS.tercile(st['vol_pct'])
    code_s = LS.tercile(st['vol_pct_strict'])
    p = LS.high_freq(code)
    p_s = LS.high_freq(code_s)
    out = dict(st)
    out['dates'] = np.array([d.strftime('%Y-%m-%d') for d in st['dates']])
    out['columns'] = np.array([str(c) for c in st['columns']], dtype='U12')
    out.update(vol_state=code, vol_state_strict=code_s, act_state=LS.tercile(st['act_pct']), act_state_strict=LS.tercile(st['act_pct_strict']),
               p_high=p, p_high_strict=p_s)
    for nm in LS.SCHEDULES:
        out['b_' + nm] = LS.schedule_b(nm, code, p)
        out['bS_' + nm] = LS.schedule_b(nm, code_s, p_s)
    M.atomic_write_npz(M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), status=np.array(['ANCHOR_PENDING']), **out)
    put('timing', item='state_compute_s', value=round(time.time() - t0, 1))
    # PIT 截断恒等（A4-3）：截断到 cut 后从头重算 = 全程同日值
    keys = ('r_m', 'n_ret', 'vol_v', 'vol_pct', 'vol_pct_strict', 'act_med', 'n_act', 'act_20', 'act_pct', 'act_pct_strict', 'trend')
    for cut in ('2014-12-31', '2018-12-28', '2023-12-29'):
        t0 = time.time()
        sc = LS.compute(data=data, cut=cut)
        n = len(sc['dates'])
        bad = [k for k in keys if not np.array_equal(np.asarray(sc[k]), np.asarray(st[k])[:n], equal_nan=True)]
        put('pit', cut=cut, n_dates=n, keys=len(keys), mismatched_keys=';'.join(bad) or '无', status='PASS' if not bad else 'FAIL',
            seconds=round(time.time() - t0, 1))
    # UNKNOWN 日数（逐段；主定义 ≥ 150 / STRICT250）与 STRICT 标签差日数
    for s in SEG:
        m = seg_rows(dates, s)
        vs, vss = code[m], code_s[m]
        a_, as_ = out['act_state'][m], out['act_state_strict'][m]
        tr = st['trend'][m]
        put('state_unknown', segment=s, days=int(m.sum()), vol_unknown_main=int((vs < 0).sum()), act_unknown_main=int((a_ < 0).sum()),
            vol_unknown_strict250=int((vss < 0).sum()), act_unknown_strict250=int((as_ < 0).sum()),
            vol_label_diff_main_vs_strict=int((vs != vss).sum()), trend_unknown_share_pool0=round(float((tr[p0[m]] < 0).mean()), 6),
            trend_up_down_mixed_share_pool0='%.4f / %.4f / %.4f' % tuple(float((tr[p0[m]] == k).mean()) for k in (2, 0, 1)))
    return st


def task_calendar(dates):
    cal = dates
    for s in SEG:
        m = seg_rows(cal, s)
        put('calendar', segment=s, open_days=int(m.sum()), first=str(cal[m][0].date()), last=str(cal[m][-1].date()), warmup_days=19)
    w1 = cal[(cal >= pd.Timestamp('2024-01-15')) & (cal <= pd.Timestamp('2024-02-23'))]
    put('windows', window='W1', rule='2024-01-15 → 2024-02-23 交易日', first=str(w1[0].date()), last=str(w1[-1].date()), days=len(w1))
    c = cal.get_indexer([pd.Timestamp('2024-09-24')])[0]
    w2 = cal[max(0, c - 20): c + 21]
    put('windows', window='W2', rule='2024-09-24 前后各 20 交易日（含中心，≤ 41）', first=str(w2[0].date()), last=str(w2[-1].date()), days=len(w2),
        center_is_trading_day=bool(c >= 0))
    tdf = None
    for root, _, fs in os.walk('/mnt/big/base'):
        if 'trade_date.csv' in fs and 'uqer_adj_refresh' in root:
            tdf = pd.read_csv(os.path.join(root, 'trade_date.csv'), dtype=str)
            break
    if tdf is not None:
        w = tdf[(tdf.calendarDate >= '2010-01-01') & (tdf.calendarDate <= M.MARKET_DATA_END_MAX) & (tdf.isOpen == '1')]
        for ex, g in w.groupby('exchangeCD'):
            od = pd.to_datetime(g.calendarDate)
            put('calendar_file', exchange=ex, open_days=len(od), equals_data_index=bool(len(od) == len(cal) and (od.sort_values().values == cal.values).all()))


def task_apre(data, dates, p0):
    x = data['turnover_rate'].reindex_like(data['close']).astype(float).to_numpy()
    op = (data['is_open'].reindex_like(data['close']) == 1).to_numpy()
    x = np.where(op & np.isfinite(x) & (x >= 0), x, np.nan)
    X = pd.DataFrame(x)
    res = {}
    for w, mo in ((20, 12), (5, 3), (60, 36), (19, 19)):
        prev = X.shift(1).rolling(w, min_periods=mo)
        b = prev.mean().to_numpy()
        with np.errstate(all='ignore'):
            a = np.where(np.isfinite(x) & np.isfinite(b) & (b > 0), x / b, np.nan)
        res[w] = a
    for s in SEG:
        m = seg_rows(dates, s)[:, None] & p0
        put('a_pre', segment=s, pool0_cells=int(m.sum()), a20_pre_valid_share=round(float(np.isfinite(res[20][m]).mean()), 6),
            a5_pre_valid_share=round(float(np.isfinite(res[5][m]).mean()), 6), a60_pre_valid_share=round(float(np.isfinite(res[60][m]).mean()), 6))
    inc = X.rolling(20, min_periods=20).mean().to_numpy()
    with np.errstate(all='ignore'):
        direct = np.where(np.isfinite(x) & (inc > 0), x / inc, np.nan)
        a19 = res[19]
        bridge = 20 * a19 / (19 + a19)
    ok = np.isfinite(direct) & np.isfinite(bridge) & p0
    rel = np.abs(direct[ok] - bridge[ok]) / np.maximum(np.abs(direct[ok]), 1e-300)
    put('a_inc_bridge', cells=int(ok.sum()), max_rel_diff=float(rel.max()) if ok.any() else np.nan, p99_rel_diff=float(np.percentile(rel, 99)) if ok.any() else np.nan,
        note='a_inc = n·a_pre/(n−1+a_pre)，a_pre 用前 19 日基线（全有效）对含当日 20 日窗比值；源 S 含当日基线逐位 = S（E6i 缓存）')


def task_peer(data, dates, p0):
    import comprehensive_factor_diagnosis as C
    close = data['close'].astype(float)
    A = C.adjust_factor(data).reindex(index=close.index, columns=close.columns).to_numpy()
    ca = close.to_numpy() * A
    ca = np.where(np.isfinite(ca) & (ca > 0), ca, np.nan)
    r20 = np.full(ca.shape, np.nan)
    with np.errstate(all='ignore'):
        r20[21:] = ca[20:-1] / ca[:-21] - 1.0                       # 截至 T−1：C[T−1] / C[T−21] − 1
    ind = data.get('industry_zx1', data.get('industry')).reindex(index=close.index, columns=close.columns)
    codes, _ = pd.factorize(pd.Series(ind.to_numpy().ravel()))
    codes = codes.reshape(ind.shape)
    import e6l_state as LS
    clean = LS.clean_full(data).reindex_like(close).fillna(0.0).to_numpy() == 1
    prevclean = np.zeros_like(clean)
    prevclean[1:] = clean[:-1]
    peer_unknown = np.zeros(ca.shape, bool)
    mkt = np.full(len(dates), np.nan)
    for t in range(len(dates)):
        v = r20[t]
        mem = prevclean[t] & np.isfinite(v) & (codes[t] >= 0)
        if mem.any():
            mkt[t] = np.mean(v[mem])
        cnt = np.bincount(codes[t][mem], minlength=codes.max() + 1)
        own_in = mem.astype(int)
        k = codes[t]
        n_other = np.where(k >= 0, cnt[np.maximum(k, 0)] - own_in, 0)
        peer_unknown[t] = n_other <= 0
    for s in SEG:
        m = seg_rows(dates, s)
        pm = m[:, None] & p0
        mk = mkt[m]
        put('peer', segment=s, pool0_cells=int(pm.sum()), peer_unknown_share_pool0=round(float(peer_unknown[pm].mean()), 6),
            market_proxy_pos_days=int((mk > 0).sum()), market_proxy_neg_days=int((mk < 0).sum()), market_proxy_undefined_days=int((~np.isfinite(mk)).sum()))


def task_fwd(data, dates, p0):
    import comprehensive_factor_diagnosis as C
    src = inspect.getsource(C.compute_forward_5d_excess)
    line = inspect.getsourcelines(C.compute_forward_5d_excess)[1]
    put('fwd', item='FWD_SOURCE', value='comprehensive_factor_diagnosis.compute_forward_5d_excess（:%d；hold_days = h；adjust=True）' % line,
        semantics='T+1 后复权 VWAP 买入 → T+1+h 卖出；逐日 VWAP 收益减 base_pool 等权日均（超额）后按日相加（线性），× 1e4 = bp；任一日缺失 → 缺失（pandas 相加传播 NaN）',
        source_sha16=M.sha_bytes(src.encode())[:16])
    idx = pd.date_range('2024-01-01', periods=6, freq='D')
    cols = ['a', 'b', 'c']
    v = pd.DataFrame([[10, 20, 30], [11, 20, 30], [12.1, 20, 30], [11, 20, 30], [10, 20, 30], [10, 20, 30]], index=idx, columns=cols, dtype=float)
    syn = dict(vwap=v, close=v.copy(), lclose=v.shift(1).fillna(v.iloc[0]), is_open=pd.DataFrame(1, index=idx, columns=cols))
    bp = pd.DataFrame(1.0, index=idx, columns=cols)
    f2 = C.compute_forward_5d_excess(syn, bp, hold_days=2, adjust=True)
    syn2 = {k: x.copy() for k, x in syn.items()}
    syn2['vwap'].iloc[2, 0] = np.nan
    f2n = C.compute_forward_5d_excess(syn2, bp, hold_days=2, adjust=True)
    put('fwd', item='FWD_SOURCE 合成例（三只等权基准、h = 2）', value='T0 股票 a 线性超额 = %.4f bp；第 2 日 a 缺价 → %s' % (f2.iloc[0, 0], 'NaN' if np.isnan(f2n.iloc[0, 0]) else f2n.iloc[0, 0]),
        semantics='缺失传播：任一日缺失即缺失（FWD_LINEAR 同型；与 FWD_ENDPOINT 不同）', source_sha16='')
    import e6m_b3_tools as B
    for name, path in (('100→110→99', [100, 110, 99]), ('100→NaN→99', [100, np.nan, 99]), ('100→110→NaN', [100, 110, np.nan])):
        lp = B.label_pair(path, 0, 2)
        put('fwd', item='FWD_ENDPOINT / FWD_LINEAR 合成：' + name, value='endpoint %s / linear %s' % (lp['endpoint'], lp['linear_daily']), semantics='', source_sha16='')
    vw = data['vwap'].reindex_like(data['close']).astype(float).to_numpy()
    op = (data['is_open'].reindex_like(data['close']) == 1).to_numpy()
    ok_next = np.zeros(vw.shape, bool)
    ok_next[:-1] = np.isfinite(vw[1:]) & (vw[1:] > 0) & op[1:]
    for s in SEG:
        m = seg_rows(dates, s)[:, None] & p0
        put('fwd', item='T+1 VWAP 入场不可得份额（pool0 格；留现金诊断）', value='%s：%.6f' % (s, 1 - ok_next[m].mean()), semantics='只看次日 VWAP 可得性，不算收益', source_sha16='')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--attempt', default='a1')
    a = ap.parse_args()
    t0 = time.time()
    data, before, cd = load_full()
    put('timing', item='load_full_s', value=round(time.time() - t0, 1))
    dates = pd.to_datetime(pd.Index(data['close'].index).astype(str))
    p0 = pool0_mask(data['close'])
    put('timing', item='pool0_cells_full', value=int(p0.sum()))
    for nm, fn in (('state', lambda: task_state(data, dates, p0)), ('calendar', lambda: task_calendar(dates)), ('apre', lambda: task_apre(data, dates, p0)),
                   ('peer', lambda: task_peer(data, dates, p0)), ('fwd', lambda: task_fwd(data, dates, p0))):
        t1 = time.time()
        fn()
        put('timing', item='%s_s' % nm, value=round(time.time() - t1, 1))
    put('timing', item='cache_dir_unchanged', value=sorted(os.listdir(cd)) == before)
    put('timing', item='rss_peak_gb', value=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    R = pd.DataFrame(ROWS)
    outs = []
    for tb, g in R.groupby('table'):
        p = M.P('stage0', 'c4_data_%s.csv' % tb)
        M.atomic_write_csv(p, g.dropna(axis=1, how='all'))
        outs.append(p)
    pit_ok = (R[R.table == 'pit'].status == 'PASS').all()
    ok = pit_ok and bool(R[(R.table == 'timing') & (R['item'] == 'cache_dir_unchanged')].value.iloc[0])
    M.write_receipt(os.environ.get('E6M_TASK', 'N5_full_%s' % a.attempt), outs + [M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz')],
                    status='SUCCEEDED' if ok else 'FAILED', code=[__file__, M.__file__], wall_s=round(time.time() - t0, 1))
    print(R.drop(columns=[c for c in R.columns if R[c].isna().all()]).to_string(max_colwidth=90))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
