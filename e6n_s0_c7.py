# -*- coding: utf-8 -*-
"""E6n Stage 0 第 7 类：分钟数据合同与健康（brief §2 第 7 类、附录 A7-1…A7-11；plan §4.1–§4.4）。不读任何收益。
样本日（固定种子）上读分钟表与日频缓存的同日价量，逐项实测数据合同；覆盖率读全期分钟表表头（只读首行）。
输出 stage0/c7_minute/：a7_*.csv、minute_health.csv、data_contract.json、c7_summary.json（逐项 PASS / FAIL / INFO / SOURCE_WAIT）。
用法：E6N_WORK=<结果目录> python3 e6n_s0_c7.py [--ctxdir <E6m tmp 目录>]"""
import os
import sys
import json
import time
import pickle
import argparse

import numpy as np
import pandas as pd

import e6n_core as N
import e6n_minute as MN

DAILY = N.DAILY_FULL
REFORM = 20180820
OUT = None


def exch(codes):
    c = np.asarray(codes).astype(str)
    return np.where(np.char.startswith(c, '6'), 'SH', np.where(np.char.startswith(c, '0') | np.char.startswith(c, '3'), 'SZ', 'OTHER'))


def regime(codes, date_int):
    e = exch(codes)
    return np.where(e == 'SH', np.where(date_int < REFORM, 'SH_PRE', 'SH_POST'), e)


def sample_days(seed=20261015):
    days = MN.list_days(5)
    rng = np.random.default_rng(seed)
    out = set()
    by_year = {}
    for d in days:
        by_year.setdefault(d // 10000, []).append(d)
    for y, ds in sorted(by_year.items()):
        k = min(4, len(ds))
        out |= set(int(x) for x in rng.choice(ds, size=k, replace=False))
    around = [d for d in days if 20180813 <= d <= 20180824]          # 沪市改革前后各一周
    out |= set(around)
    return sorted(out)


def load_daily(days):
    import pyarrow.parquet as pq
    ts = [pd.Timestamp(str(d)) for d in days]
    t = pq.read_table(DAILY, columns=['trade_date', 'stock_code', 'open', 'close', 'high', 'low', 'lclose', 'volume', 'amount', 'is_open', 'adj_factor'],
                      filters=[('trade_date', 'in', ts)])
    df = t.to_pandas().reset_index()
    N.assert_index_ok(pd.DatetimeIndex(df['trade_date']), 'daily sample')
    return df


def bar_checks(date_int):
    """A7-2：5 分钟标签 L 的 bar = 1 分钟 (L−5, L] 的聚合（收 = 末根收；量 / 额 = 和；高 / 低 = 极值；开 = 首根开）。"""
    c5, t5 = MN.read_day(date_int, 5)
    c1, t1 = MN.read_day(date_int, 1)
    common = np.intersect1d(c5, c1)
    i5 = pd.Index(c5).get_indexer(common)
    i1 = pd.Index(c1).get_indexer(common)
    rows = []
    for k in range(1, len(MN.LAB5)):
        lab = MN.LAB5[k]
        j1 = MN.I1[lab]
        win = list(range(j1 - 4, j1 + 1))                      # 1 分钟行号：L−4…L（各自是 1 分钟终点）
        v1 = np.nan_to_num(t1['v'][win][:, i1], nan=0.0)
        a1 = np.nan_to_num(t1['a'][win][:, i1], nan=0.0)
        tr = v1 > 0
        anyt = tr.any(0)
        c5k = t5['c'][k, i5]
        v5k = np.nan_to_num(t5['v'][k, i5], nan=0.0)
        a5k = np.nan_to_num(t5['a'][k, i5], nan=0.0)
        h1 = np.where(tr, t1['h'][win][:, i1], -np.inf).max(0)
        l1 = np.where(tr, t1['l'][win][:, i1], np.inf).min(0)
        first = np.argmax(tr, axis=0)
        o1 = t1['o'][win][:, i1][first, np.arange(len(common))]
        rows.append(dict(date=date_int, label=lab, n=len(common), n_traded=int(anyt.sum()),
                         close_eq=int((np.abs(c5k - t1['c'][j1, i1]) <= 1e-9).sum()),
                         vol_eq=int((np.abs(v5k - v1.sum(0)) <= 1e-6).sum()), amt_eq=int((np.abs(a5k - a1.sum(0)) <= 1e-3 * np.maximum(1, a5k)).sum()),
                         high_eq_traded=int((np.abs(t5['h'][k, i5] - h1)[anyt] <= 1e-9).sum()),
                         low_eq_traded=int((np.abs(t5['l'][k, i5] - l1)[anyt] <= 1e-9).sum()),
                         open_eq_traded=int((np.abs(t5['o'][k, i5] - o1)[anyt] <= 1e-9).sum())))
    return rows


def representation(date_int, daily_day):
    """A7-3 / A7-4 / A7-5 / A7-11：一行一个 (日, 交易所制度)。"""
    c5, t5 = MN.read_day(date_int, 5)
    c1, t1 = MN.read_day(date_int, 1)
    codes, F = MN.day_features(date_int)
    dd = daily_day.set_index('stock_code')
    reg = regime(codes, date_int)
    out = []
    v5 = t5['v']
    v1 = t1['v']
    zero5 = np.nan_to_num(v5[1:], nan=0.0) == 0
    chg5 = np.abs(np.diff(t5['c'], axis=0)) > 1e-9
    nan1 = np.isnan(v1[1:])
    zero1 = np.nan_to_num(v1[1:], nan=0.0) == 0
    o_d = dd['open'].reindex(codes).to_numpy(float)
    c_d = dd['close'].reindex(codes).to_numpy(float)
    vol_d = dd['volume'].reindex(codes).to_numpy(float)
    amt_d = dd['amount'].reindex(codes).to_numpy(float)
    isop = dd['is_open'].reindex(codes).to_numpy(float)
    h_d = dd['high'].reindex(codes).to_numpy(float)
    l_d = dd['low'].reindex(codes).to_numpy(float)
    i1500 = MN.I1['15:00:00']
    for g in sorted(set(reg)):
        m = reg == g
        tr = (F['state'] != MN.STATE['NO_TRADE_PRESENT']) & m
        auc = (F['auction_traded'] == 1) & m & np.isfinite(o_d) & (o_d > 0)
        last_ok = tr & np.isfinite(c_d) & (c_d > 0) & np.isfinite(F['p_last'])
        with np.errstate(all='ignore'):
            vr = F['vol_min'] / vol_d
            ar = F['amt_min'] / amt_d
            hr = F['high_min'] / h_d
            lr = F['low_min'] / l_d
        okv = tr & np.isfinite(vr) & (vol_d > 0)
        oka = tr & np.isfinite(ar) & (amt_d > 0)
        out.append(dict(date=date_int, regime=g, n_codes=int(m.sum()), n_traded=int(tr.sum()),
                        rows5=len(MN.LAB5), rows1=len(MN.LAB1), lunch_rows=0,
                        nan_close5=int(np.isnan(t5['c'][:, m]).sum()), nan_close1=int(np.isnan(t1['c'][:, m]).sum()),
                        zero_vol5_bars=int(zero5[:, m].sum()), zero_vol5_price_change=int((zero5 & chg5)[:, m].sum()),
                        nan_vol1_bars=int(nan1[:, m].sum()), zero_not_nan_vol1_bars=int((zero1 & ~nan1)[:, m].sum()),
                        auction_traded=int(auc.sum()), auction_px_eq_open=int((np.abs(F['auction_px'] - o_d) <= 1e-9)[auc].sum()),
                        last_eq_close=int((np.abs(F['p_last'] - c_d) <= 1e-9)[last_ok].sum()), n_last_ok=int(last_ok.sum()),
                        v1458_59_zero=int((F['v1_1458_59'] == 0)[tr].sum()),
                        v1500_share_med=float(np.nanmedian((np.nan_to_num(v1[i1500], nan=0.0) / np.where(F['vol_min1'] > 0, F['vol_min1'], np.nan))[tr])) if tr.any() else np.nan,
                        vol_ratio_eq1=int((np.abs(vr - 1) <= 1e-9)[okv].sum()), vol_ratio_lt1=int((vr < 1 - 1e-9)[okv].sum()),
                        vol_ratio_gt1=int((vr > 1 + 1e-9)[okv].sum()), n_vol_ok=int(okv.sum()),
                        vol_ratio_p01=float(np.nanpercentile(vr[okv], 1)) if okv.any() else np.nan,
                        vol_ratio_med=float(np.nanmedian(vr[okv])) if okv.any() else np.nan,
                        amt_ratio_med=float(np.nanmedian(ar[oka])) if oka.any() else np.nan,
                        amt_ratio_within_1e4=int((np.abs(ar - 1) <= 1e-4)[oka].sum()), n_amt_ok=int(oka.sum()),
                        high_eq=int((np.abs(hr - 1) <= 1e-9)[tr & np.isfinite(hr)].sum()), low_eq=int((np.abs(lr - 1) <= 1e-9)[tr & np.isfinite(lr)].sum()),
                        n_hl=int((tr & np.isfinite(hr) & np.isfinite(lr)).sum()),
                        daily_open_absent_in_minute=0,
                        state_flat=int((F['state'] == MN.STATE['FLAT_TRADED'])[m].sum()),
                        state_notrade=int((F['state'] == MN.STATE['NO_TRADE_PRESENT'])[m].sum()),
                        state_hole=int((F['state'] == MN.STATE['HOLE'])[m].sum()),
                        isopen0_present=int((isop == 0)[m].sum())))
    # 日频 is_open = 1 但不在分钟表（缺源）与停牌（is_open = 0）计数
    d_open = dd.index[(dd['is_open'] == 1) & (dd['volume'] > 0)]
    miss = np.setdiff1d(np.asarray(d_open, dtype=str), codes)
    miss = miss[np.isin(exch(miss), ['SH', 'SZ'])]
    for g in sorted(set(regime(miss, date_int))) if len(miss) else []:
        out.append(dict(date=date_int, regime=g, daily_open_absent_in_minute=int((regime(miss, date_int) == g).sum())))
    return out, codes, F


def bridge(date_int, daily_day, codes, F):
    """A7-8：官方桥分解 log(C/O) = log(P0/O) + Σr + log(C/P_last)，只在有效路径上核；印桥项分布（按制度）。"""
    dd = daily_day.set_index('stock_code')
    o_d = dd['open'].reindex(codes).to_numpy(float)
    c_d = dd['close'].reindex(codes).to_numpy(float)
    ok = (F['state'] == MN.STATE['PATH_OK']) | (F['state'] == MN.STATE['FLAT_TRADED'])
    ok &= np.isfinite(o_d) & (o_d > 0) & np.isfinite(c_d) & (c_d > 0)
    with np.errstate(all='ignore'):
        lhs = np.log(c_d / o_d)
        b0 = np.log(F['p0'] / o_d)
        b1 = np.log(c_d / F['p_last'])
        rhs = b0 + F['net_5'] + b1
    reg = regime(codes, date_int)
    return pd.DataFrame(dict(date=date_int, code=codes, regime=reg, ok=ok, err=np.abs(lhs - rhs), open_bridge=b0, close_bridge=b1, net_path=F['net_5']))[ok]


def signature(date_int, codes, pool_codes, rng, k=60):
    """A7-7：签名图样本——pool0 内随机 k 只股票的 1 / 2 / 5 / 10 / 15 / 30 分钟 RV（同会话起止、各自网格，只向后端点）。"""
    c1, t1 = MN.read_day(date_int, 1)
    X1, s1, tr1, hole1 = MN._path_matrix(t1['c'], t1['o'], t1['v'])
    cand = np.where(np.isin(c1, pool_codes) & (s1 >= 0) & ~hole1)[0]
    if not len(cand):
        return []
    pick = rng.choice(cand, size=min(k, len(cand)), replace=False)
    out = []
    for f in (1, 2, 5, 10, 15, 30):
        rows = [i for i, lab in enumerate(MN.LAB1) if i > 0 and (int(lab[:2]) * 60 + int(lab[3:5]) - (570 if lab < '12' else 780)) % f == 0]
        Y = X1[[0] + rows][:, pick]
        r = np.diff(Y, axis=0)
        rv = (r * r).sum(0)
        pl = np.abs(r).sum(0)
        out += [dict(date=date_int, freq_min=f, code=c1[j], rv=float(rv[i]), pl=float(pl[i])) for i, j in enumerate(pick)]
    return out


def afterhours(date_int, daily_day, codes, F):
    """A7-11：科创板 / 创业板盘后固定价格成交——分钟表止于 15:00；若日频量含盘后，则分钟量 < 日频量。按板块计。"""
    dd = daily_day.set_index('stock_code')
    vol_d = dd['volume'].reindex(codes).to_numpy(float)
    c = np.asarray(codes).astype(str)
    board = np.where(np.char.startswith(c, '688') | np.char.startswith(c, '689'), 'STAR',
                     np.where(np.char.startswith(c, '300') | np.char.startswith(c, '301'), 'CHINEXT', 'MAIN'))
    ok = (F['state'] != MN.STATE['NO_TRADE_PRESENT']) & np.isfinite(vol_d) & (vol_d > 0)
    with np.errstate(all='ignore'):
        r = F['vol_min'] / vol_d
    out = []
    for b in ('STAR', 'CHINEXT', 'MAIN'):
        m = ok & (board == b)
        out.append(dict(date=date_int, board=b, n=int(m.sum()), minute_lt_daily=int((r < 1 - 1e-9)[m].sum()),
                        minute_eq_daily=int((np.abs(r - 1) <= 1e-9)[m].sum()), ratio_med=float(np.nanmedian(r[m])) if m.any() else np.nan))
    return out


def coverage(seg_pool, seg_isop):
    """A7-6：全期分钟表表头（只读首行）× 日频 is_open × pool0 → 按年 × 交易所 × pool0 的覆盖份额（股票日）。"""
    days = MN.list_days(5)
    heads = {}
    for d in days:
        with open(os.path.join(MN.root(), '5min', '%08d' % d, 'closeprice.csv'), encoding='utf-8') as fh:
            heads[d] = set(x.strip() for x in fh.readline().strip().split(',')[1:])
    rows = []
    for seg in N.SEGMENTS:
        p0 = seg_pool[seg]
        isop = seg_isop[seg]
        cols = np.array([str(c) for c in p0.columns])
        ex = exch(cols)
        P = p0.to_numpy() == 1
        O = isop.to_numpy() == 1
        for t, dt in enumerate(p0.index):
            di = int(dt.strftime('%Y%m%d'))
            h = heads.get(di)
            pres = np.isin(cols, list(h)) if h is not None else np.zeros(len(cols), bool)
            for e in ('SH', 'SZ'):
                me = ex == e
                for dom, M_ in (('pool0', P[t] & me), ('open_market', O[t] & me)):
                    rows.append(dict(segment=seg, date=di, year=di // 10000, exchange=e, domain=dom, n=int(M_.sum()), present=int((M_ & pres).sum()),
                                     minute_day=int(h is not None)))
    df = pd.DataFrame(rows)
    g = df.groupby(['segment', 'year', 'exchange', 'domain'], as_index=False)[['n', 'present', 'minute_day']].sum()
    g['days'] = df.groupby(['segment', 'year', 'exchange', 'domain']).size().to_numpy()
    with np.errstate(all='ignore'):
        g['coverage_share_decimal'] = g['present'] / g['n']
    return g


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument('--ctxdir', required=True)
    a = ap.parse_args()
    OUT = N.P('stage0', 'c7_minute')
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    days = sample_days()
    daily = load_daily(days)
    N.log('样本日 %d 个（%d–%d）；日频样本行 %d' % (len(days), days[0], days[-1], len(daily)))
    rng = np.random.default_rng(7)
    bars, reps, brs, sig, ahs = [], [], [], [], []
    seg_pool, seg_isop = {}, {}
    for seg in N.SEGMENTS:
        with open(os.path.join(a.ctxdir, 'ctx_%s.pkl' % seg), 'rb') as fh:
            ctx = pickle.load(fh)
        seg_pool[seg] = ctx['pool0']
        seg_isop[seg] = ctx['data']['is_open'].reindex(index=ctx['pool0'].index, columns=ctx['pool0'].columns)
        del ctx
    for d in days:
        dd = daily[daily['trade_date'] == pd.Timestamp(str(d))]
        bars += bar_checks(d)
        rp, codes, F = representation(d, dd)
        reps += rp
        brs.append(bridge(d, dd, codes, F))
        ahs += afterhours(d, dd, codes, F)
        ts = pd.Timestamp(str(d))
        pc = []
        for seg, p0 in seg_pool.items():
            if ts in p0.index:
                pc = [str(c) for c in p0.columns[(p0.loc[ts] == 1).to_numpy()]]
        sig += signature(d, codes, pc, rng)
    A2 = pd.DataFrame(bars)
    A3 = pd.DataFrame(reps)
    B = pd.concat(brs, ignore_index=True)
    SG = pd.DataFrame(sig)
    N.atomic_write_csv(os.path.join(OUT, 'a7_2_bar_convention.csv'), A2)
    N.atomic_write_csv(os.path.join(OUT, 'a7_3_5_11_representation_units.csv'), A3)
    bsum = B.groupby('regime').agg(n=('err', 'size'), err_max=('err', 'max'),
                                   open_bridge_p01=('open_bridge', lambda x: np.nanpercentile(x, 1)), open_bridge_med=('open_bridge', 'median'),
                                   open_bridge_p99=('open_bridge', lambda x: np.nanpercentile(x, 99)), open_bridge_nonzero=('open_bridge', lambda x: int((np.abs(x) > 1e-12).sum())),
                                   close_bridge_p01=('close_bridge', lambda x: np.nanpercentile(x, 1)), close_bridge_med=('close_bridge', 'median'),
                                   close_bridge_p99=('close_bridge', lambda x: np.nanpercentile(x, 99)),
                                   close_bridge_nonzero=('close_bridge', lambda x: int((np.abs(x) > 1e-12).sum()))).reset_index()
    N.atomic_write_csv(os.path.join(OUT, 'a7_8_official_bridge.csv'), bsum)
    SG['segment'] = [next((s for s in N.SEGMENTS if pd.Timestamp(str(x)) in seg_pool[s].index), 'NONE') for x in SG['date']]
    mh = SG.groupby(['segment', 'freq_min']).agg(n_stock_days=('rv', 'size'), rv_mean=('rv', 'mean'), rv_median=('rv', 'median'),
                                                pl_mean=('pl', 'mean'), pl_median=('pl', 'median')).reset_index()
    mh['role'] = 'HEALTH_ONLY_NOT_FREQUENCY_SELECTION'
    N.atomic_write_csv(os.path.join(OUT, 'minute_health.csv'), mh)
    cov = coverage(seg_pool, seg_isop)
    N.atomic_write_csv(os.path.join(OUT, 'a7_6_coverage_year_exchange_pool0.csv'), cov)
    AH = pd.DataFrame(ahs)
    AH['year'] = AH['date'] // 10000
    ahs_sum = AH.groupby(['board', 'year'], as_index=False)[['n', 'minute_lt_daily', 'minute_eq_daily']].sum()
    N.atomic_write_csv(os.path.join(OUT, 'a7_11_afterhours_board_year.csv'), ahs_sum)
    # ---------------- 判定（预期来源写在每项）
    S = []

    def add(item, what, status, detail):
        S.append(dict(item=item, check=what, status=status, detail=json.dumps(detail, ensure_ascii=False, default=str)))
    n_bar = int(A2['n'].sum())
    add('A7-2', '5 分钟标签 = bar 终点：bar 收 = 1 分钟同标签收；量 / 额 = 1 分钟 (L−5, L] 之和；高 / 低 / 开 = 有成交 1 分钟的极值 / 首开',
        'PASS' if (A2['close_eq'] == A2['n']).all() and (A2['vol_eq'] == A2['n']).all() else 'FAIL',
        dict(cells=n_bar, close_eq=int(A2['close_eq'].sum()), vol_eq=int(A2['vol_eq'].sum()), amt_eq=int(A2['amt_eq'].sum()),
             traded=int(A2['n_traded'].sum()), high_eq=int(A2['high_eq_traded'].sum()), low_eq=int(A2['low_eq_traded'].sum()), open_eq=int(A2['open_eq_traded'].sum())))
    R = A3[A3['n_codes'].notna()] if 'n_codes' in A3 else A3
    add('A7-3', '竞价 / 午休 / 无成交表示：09:25 竞价独立行；午休无行；1 分钟无成交 = 量 NaN 且价沿用；5 分钟无成交 = 量 0 且价沿用；停牌不在表',
        'INFO', dict(rows5=len(MN.LAB5), rows1=len(MN.LAB1), nan_close5=int(R['nan_close5'].sum()), nan_close1=int(R['nan_close1'].sum()),
                     zero_vol5_bars=int(R['zero_vol5_bars'].sum()), zero_vol5_price_change=int(R['zero_vol5_price_change'].sum()),
                     nan_vol1_bars=int(R['nan_vol1_bars'].sum()), zero_not_nan_vol1_bars=int(R['zero_not_nan_vol1_bars'].sum()),
                     present_but_isopen0=int(R['isopen0_present'].sum()), daily_open_absent_in_minute=int(A3['daily_open_absent_in_minute'].fillna(0).sum())))
    add('A7-4', '单位：分钟量合计（含开盘竞价行）/ 日频量；分钟额 / 日频额（按制度分）', 'INFO',
        {g: dict(n=int(x['n_vol_ok'].sum()), eq1=int(x['vol_ratio_eq1'].sum()), lt1=int(x['vol_ratio_lt1'].sum()), gt1=int(x['vol_ratio_gt1'].sum()),
                 amt_within_1e4=int(x['amt_ratio_within_1e4'].sum()), n_amt=int(x['n_amt_ok'].sum())) for g, x in R.groupby('regime')})
    add('A7-5', '复权：分钟价与日频同为未复权价；竞价价 = 官方开盘价；15:00 末成交价 vs 官方收盘价（按制度）', 'INFO',
        {g: dict(auction=int(x['auction_traded'].sum()), auction_eq_open=int(x['auction_px_eq_open'].sum()),
                 last_ok=int(x['n_last_ok'].sum()), last_eq_close=int(x['last_eq_close'].sum()),
                 high_eq=int(x['high_eq'].sum()), low_eq=int(x['low_eq'].sum()), n_hl=int(x['n_hl'].sum())) for g, x in R.groupby('regime')})
    add('A7-8', '官方桥分解每制度期 ≥ 1,000 股票日成立（1e−12）；桥项分布另印', 'PASS' if (bsum['n'] >= 1000).all() and (bsum['err_max'] <= 1e-12).all() else 'FAIL',
        bsum[['regime', 'n', 'err_max', 'close_bridge_nonzero', 'open_bridge_nonzero']].to_dict('records'))
    add('A7-9', '制度数据事实：14:58 / 14:59 1 分钟量为 0 的份额（收盘集合竞价期应为 0）；15:00 1 分钟量占全日的中位份额', 'INFO',
        {g: dict(traded=int(x['n_traded'].sum()), v1458_59_zero=int(x['v1458_59_zero'].sum()), v1500_share_med=float(x['v1500_share_med'].median()))
         for g, x in R.groupby('regime')})
    add('A7-7', '签名图（健康表，不选频率）', 'INFO', mh[['segment', 'freq_min', 'n_stock_days', 'rv_median']].to_dict('records'))
    add('A7-11', '盘后固定价格成交：分钟表止于 15:00；分钟量 < 日频量的股票日按板块计（科创板 / 创业板若日频含盘后则此计数 > 0）', 'INFO',
        {b: dict(n=int(x['n'].sum()), minute_lt_daily=int(x['minute_lt_daily'].sum()), minute_eq_daily=int(x['minute_eq_daily'].sum()))
         for b, x in ahs_sum.groupby('board')})
    add('A7-6', '覆盖：按年 × 交易所 × pool0 的分钟可得份额（股票日）', 'INFO',
        dict(first_minute_day=MN.list_days(5)[0], pool0_overall=float(cov[cov.domain == 'pool0']['present'].sum() / max(cov[cov.domain == 'pool0']['n'].sum(), 1))))
    pd.DataFrame(S).to_csv(os.path.join(OUT, 'c7_summary_items.csv'), index=False)
    N.atomic_write_json(os.path.join(OUT, 'c7_summary.json'), dict(items=S, sample_days=days, secs=round(time.time() - t0, 1)))
    N.log('第 7 类探针完成：%.0f s' % (time.time() - t0))
    for s in S:
        print(s['item'], s['status'], s['detail'][:400])


if __name__ == '__main__':
    main()
