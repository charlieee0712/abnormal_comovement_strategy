# -*- coding: utf-8 -*-
"""E6n 分钟读取器与逐日原始量（plan §4.1–§4.4、§5.1–§5.2；brief §1.3-3、W06、W07）。不读日频、不读收益、不做跨日基线。

源：47 只读公共分钟 K 线目录（环境变量 E6N_MINUTE_ROOT；缺省为登记路径）。按日目录，六张宽表（开 / 高 / 低 / 收 / 量 / 额），
行 = bar 终点标签（09:25 开盘竞价行 + 上午 + 下午），列 = 6 位代码；停牌股当日不出现。数据合同的每条约定由 Stage 0 第 7 类实测
（e6n_s0_c7.py），本模块只按合同取数：
- **读取接口截断**：日期 > 2026-03-27 的目录一律拒绝（抛错），不先读后滤；只列目录名的元数据函数另列（list_days）。
- **端点只向后看**：标签 L 的端点价 = L 及之前最后一根「有成交」bar 的收盘价（零量 bar 的沿用价不当成交）；本日第一笔成交之前无端点。
- **路径起点**：开盘竞价有量 → 竞价价；否则第一根有量 bar 的开盘价（第一笔连续成交）。不接昨收。
- **主网格 5 分钟**：起点 + 09:35…11:30、13:05…15:00 共 48 个端点；午间 11:30 → 13:05 一次收益（含 13:00–13:05）；
  15:00 端点含真实收盘撮合（官方收盘价不覆盖它）；14:57 只作诊断端点（1 分钟表取）。
- **1 / 10 分钟桥**：1 分钟 240 个端点；10 分钟 = 1 分钟收盘价在 09:40…11:30、13:10…15:00 的 24 个端点。各自同会话起止。
- **量 8 格**：右闭；09:25 开盘竞价量归第 1 格；15:00 bar（含收盘撮合）归第 8 格；只计一次；不含盘后（源分钟表不含盘后行）。
- **五种状态**：PATH_OK / FLAT_TRADED（全日有成交价不变）/ NO_TRADE_PRESENT（在表内全日无成交）/ HOLE（有成交 bar 价缺失，未知洞）；
  不在表内者由日频 is_open 再分 SUSPENDED / SOURCE_MISSING（e6n_etl）。"""
import os

import numpy as np
import pandas as pd

import e6n_core as N

ROOT_DEFAULT = '/mnt/big/origin/public/MatrixDailyFix'
FIELDS = ('openprice', 'highprice', 'lowprice', 'closeprice', 'turnoverVol', 'turnoverValue')
SHORT = dict(openprice='o', highprice='h', lowprice='l', closeprice='c', turnoverVol='v', turnoverValue='a')
TOL_E = 64 * np.finfo(float).eps


def root():
    return os.environ.get('E6N_MINUTE_ROOT', ROOT_DEFAULT)


def _hm(t):
    return '%02d:%02d:00' % (t // 60, t % 60)


def labels(freq):
    """源表行标签（时刻；标签 = bar 终点）：09:25 竞价行 + 上午 09:30+freq…11:30 + 下午 13:00+freq…15:00。"""
    out = ['09:25:00']
    t = 9 * 60 + 30 + freq
    while t <= 11 * 60 + 30:
        out.append(_hm(t))
        t += freq
    t = 13 * 60 + freq
    while t <= 15 * 60:
        out.append(_hm(t))
        t += freq
    return out


LAB5 = labels(5)                                              # 49 行
LAB1 = labels(1)                                              # 241 行
I5 = {s: i for i, s in enumerate(LAB5)}
I1 = {s: i for i, s in enumerate(LAB1)}
GRID10 = [I1[_hm(t)] for t in list(range(9 * 60 + 40, 11 * 60 + 31, 10)) + list(range(13 * 60 + 10, 15 * 60 + 1, 10))]   # 24 个 1 分钟行号
LATE6 = [I5[s] for s in ('14:30:00', '14:35:00', '14:40:00', '14:45:00', '14:50:00', '14:55:00')]
BUCKET8 = [(1, 6), (7, 12), (13, 18), (19, 24), (25, 30), (31, 36), (37, 42), (43, 48)]     # 5 分钟连续 bar 行号闭区间；第 1 格另加 09:25 竞价行
STATE = dict(PATH_OK=0, FLAT_TRADED=1, NO_TRADE_PRESENT=2, HOLE=3)


def list_days(freq=5, end=None):
    """元数据：只列目录名（YYYYMMDD），不读内容；end 缺省 = 截止日。"""
    end = N.MARKET_DATA_END_INT if end is None else int(end)
    d = os.path.join(root(), '%dmin' % freq)
    out = sorted(int(x) for x in os.listdir(d) if len(x) == 8 and x.isdigit())
    return [x for x in out if x <= end]


def read_day(date_int, freq):
    """读一天一种频率的六张表 → (codes, dict 简名 → (行, 股) float64)。截断在接口：date_int > 截止日即拒绝。"""
    date_int = int(date_int)
    if date_int > N.MARKET_DATA_END_INT:
        raise RuntimeError('E7 守卫：分钟读取日期 %d 晚于 %s' % (date_int, N.MARKET_DATA_END_MAX))
    d = os.path.join(root(), '%dmin' % freq, '%08d' % date_int)
    exp = LAB5 if freq == 5 else LAB1
    out, codes = {}, None
    for f in FIELDS:
        df = pd.read_csv(os.path.join(d, f + '.csv'), index_col=0)
        idx = [str(s) for s in df.index]
        day = '%04d-%02d-%02d' % (date_int // 10000, date_int // 100 % 100, date_int % 100)
        if [s[:10] for s in idx] != [day] * len(idx) or [s[-8:] for s in idx] != exp:
            raise RuntimeError('分钟表行标签与合同不符：%s %s' % (d, f))
        cols = np.array([str(c) for c in df.columns])
        if codes is None:
            codes = cols
            if len(set(codes)) != len(codes):
                raise RuntimeError('分钟表列代码重复：%s' % d)
        elif not np.array_equal(cols, codes):
            df = df.reindex(columns=codes)
        out[SHORT[f]] = df.to_numpy(dtype=float)
    return codes, out


def _path_matrix(c, o, v, p0_late=None, h=None, l=None):
    """端点矩阵（只向后、只用有成交 bar）：返回 (X, start, traded, hole)。
    X：(R, n) 对数价，X[0] = 起点 log P0，X[k] = 标签 k 的端点（k ≥ 1）；起点之前的标签用 log P0 填（零收益、不计观测）。
    start：起点所在行（0 = 竞价有量；否则第一根有量 bar 行号）；全日无成交 = −1。
    起点 P0：竞价有量 → 竞价价；否则 = 第一笔连续成交价。1 分钟表取第一根有量分钟的开盘价，并核它落在该分钟高低价之间（不在 → 起点未知 = HOLE）；
    5 分钟表的 bar 开盘价在部分年份是上一根收盘的沿用价（Stage 0 第 7 类实测），所以 5 分钟路径的 P0 由调用方从 1 分钟表传入（p0_late）。"""
    R, n = c.shape
    vol = np.nan_to_num(v, nan=0.0)
    traded = vol > 0
    pos = np.isfinite(c) & (c > 0)
    hole = (traded & ~pos).any(0)
    any_tr = traded.any(0)
    start = np.where(any_tr, np.argmax(traded, axis=0), -1)
    p0 = np.full(n, np.nan)
    ix = np.arange(n)
    auc = start == 0
    p0[auc] = c[0, auc]
    late = start > 0
    if p0_late is None:
        p0[late] = o[start[late], ix[late]]
        if h is not None and l is not None:
            tol = 1e-9 * np.maximum(1.0, np.abs(p0[late]))
            inside = (p0[late] >= l[start[late], ix[late]] - tol) & (p0[late] <= h[start[late], ix[late]] + tol)
            bad = np.zeros(n, bool)
            bad[ix[late][~inside]] = True
            hole |= bad
    else:
        p0[late] = np.asarray(p0_late, float)[late]
    hole |= any_tr & ~(np.isfinite(p0) & (p0 > 0))
    tc = np.where(traded & pos, c, np.nan)                  # 只取有成交 bar 的收盘价
    ff = pd.DataFrame(tc).ffill().to_numpy()                # 向后填：标签 k = k 及之前最后成交价
    with np.errstate(all='ignore'):
        lp0 = np.log(p0)
        X = np.log(ff)
    X[0] = lp0
    pre = np.isnan(X)                                        # 起点之前（或全日无成交）
    X = np.where(pre, lp0[None, :], X)
    return X, start, traded, hole


def _path_stats(X, start, traded, rows=None):
    """X 的行子集（rows 缺省 = 全部）上的路径量：PL / RV / R / E / 上下半方差。"""
    Y = X if rows is None else X[[0] + list(rows)]
    r = np.diff(Y, axis=0)
    pl = np.abs(r).sum(0)
    rv = (r * r).sum(0)
    net = r.sum(0)
    up = np.where(r > 0, r * r, 0.0).sum(0)
    dn = np.where(r < 0, r * r, 0.0).sum(0)
    with np.errstate(all='ignore'):
        e = np.where(pl > 0, np.abs(net) / pl, 0.0)
    bad = np.isfinite(e) & (e > 1 + TOL_E)
    if bad.any():
        raise ValueError('路径效率越过三角不等式：%d 个' % int(bad.sum()))
    e = np.clip(e, 0.0, 1.0)
    ok = start >= 0
    for a in (pl, rv, net, up, dn, e):
        a[~ok] = np.nan
    return dict(pl=pl, rv=rv, net=net, up=up, dn=dn, eff=e)


def _longest_false_run(tr, start):
    """起点之后最长连续无成交 bar 数（tr：(R, n) bool）。"""
    R, n = tr.shape
    out = np.zeros(n, np.int32)
    cur = np.zeros(n, np.int32)
    for k in range(1, R):
        live = k > start
        cur = np.where(live & ~tr[k], cur + 1, 0)
        out = np.maximum(out, cur)
    out[start < 0] = -1
    return out


def day_features(date_int):
    """一天的逐股原始量（plan §5.1–§5.2 的全部原始 / 同源诊断列与 W07 源桥列）。返回 (codes, dict 名 → (n,) 数组)。"""
    codes, t5 = read_day(date_int, 5)
    codes1, t1 = read_day(date_int, 1)
    if not np.array_equal(codes1, codes):                     # 两表列集合不同：按 5 分钟表对齐，1 分钟缺列记 NaN
        m = {cd: i for i, cd in enumerate(codes1)}
        sel = np.array([m.get(cd, -1) for cd in codes])
        for k in list(t1):
            a = np.full((t1[k].shape[0], len(codes)), np.nan)
            ok = sel >= 0
            a[:, ok] = t1[k][:, sel[ok]]
            t1[k] = a
    n = len(codes)
    F = {}
    # ---- 1 分钟路径先算：它给出无竞价日的第一笔连续成交价（5 分钟路径的起点）
    X1, s1, tr1, hole1 = _path_matrix(t1['c'], t1['o'], t1['v'], h=t1['h'], l=t1['l'])
    with np.errstate(all='ignore'):
        p0_first = np.where(s1 > 0, np.exp(X1[0]), np.nan)
    # ---- 5 分钟主网格
    X5, s5, tr5, hole5 = _path_matrix(t5['c'], t5['o'], t5['v'], p0_late=p0_first)
    st = _path_stats(X5, s5, tr5)
    for k, v in st.items():
        F[k + '_5'] = v
    v5 = np.nan_to_num(t5['v'], nan=0.0)
    a5 = np.nan_to_num(t5['a'], nan=0.0)
    F['start5'] = s5.astype(np.int16)
    F['auction_traded'] = (v5[0] > 0).astype(np.int8)
    F['auction_vol'] = v5[0]
    F['auction_px'] = np.where(v5[0] > 0, t5['c'][0], np.nan)
    with np.errstate(all='ignore'):
        F['p0'] = np.exp(X5[0])
        F['p_last'] = np.exp(X5[-1])
        # 端点只在本日第一笔成交之后才有价：起点行 ≤ 标签行
        F['p_1430'] = np.where((s5 >= 0) & (s5 <= I5['14:30:00']), np.exp(X5[I5['14:30:00']]), np.nan)
        for j, k in enumerate(LATE6):
            F['p_late%d' % j] = np.where((s5 >= 0) & (s5 <= k), np.exp(X5[k]), np.nan)
        F['r_lunch_5'] = np.where((s5 >= 0) & (s5 <= I5['11:30:00']), X5[I5['13:05:00']] - X5[I5['11:30:00']], np.nan)
        F['r_last_5'] = np.where((s5 >= 0) & (s5 <= I5['14:55:00']), X5[-1] - X5[-2], np.nan)
    pre = np.arange(len(LAB5))[:, None] < np.maximum(s5, 0)[None, :]
    Xs = np.where(pre, np.nan, X5)
    Xs[0] = np.where(s5 >= 0, X5[0], np.nan)                   # 起点本身参与高低
    with np.errstate(all='ignore'):
        F['t_high_5'] = np.where(s5 >= 0, np.nanargmax(np.where(np.isfinite(Xs), Xs, -np.inf), axis=0), -1).astype(np.int16)
        F['t_low_5'] = np.where(s5 >= 0, np.nanargmin(np.where(np.isfinite(Xs), Xs, np.inf), axis=0), -1).astype(np.int16)
    F['n_late_traded'] = tr5[LATE6].sum(0).astype(np.int8)
    for b, (i0, i1) in enumerate(BUCKET8):
        F['vb%d' % (b + 1)] = v5[i0:i1 + 1].sum(0) + (v5[0] if b == 0 else 0.0)
    F['vol_min'] = v5.sum(0)
    F['amt_min'] = a5.sum(0)
    trh = tr5 & np.isfinite(t5['h'])
    trl = tr5 & np.isfinite(t5['l'])
    F['high_min'] = np.where(trh.any(0), np.where(trh, t5['h'], -np.inf).max(0), np.nan)
    F['low_min'] = np.where(trl.any(0), np.where(trl, t5['l'], np.inf).min(0), np.nan)
    F['n_tr_5'] = tr5[1:].sum(0).astype(np.int16)
    F['maxrun_notrade_5'] = _longest_false_run(tr5, s5)
    # ---- 1 分钟（桥、竞价分离、源桥）
    st1 = _path_stats(X1, s1, tr1)
    for k, v in st1.items():
        F[k + '_1'] = v
    F['start1'] = s1.astype(np.int16)
    v1 = np.nan_to_num(t1['v'], nan=0.0)
    F['vol_min1'] = v1.sum(0)
    F['v1_1500'] = v1[I1['15:00:00']]
    F['v1_1458_59'] = v1[I1['14:58:00']] + v1[I1['14:59:00']]
    with np.errstate(all='ignore'):
        F['p_1457'] = np.where((s1 >= 0) & (s1 <= I1['14:57:00']), np.exp(X1[I1['14:57:00']]), np.nan)
    F['n_tr_1'] = tr1[1:].sum(0).astype(np.int16)
    F['maxrun_notrade_1'] = _longest_false_run(tr1, s1)
    # 10 分钟：1 分钟收盘端点在固定 24 个标签
    s10 = np.where(s1 < 0, -1, s1)
    st10 = _path_stats(X1, s10, tr1, rows=GRID10)
    for k, v in st10.items():
        F[k + '_10'] = v
    # W07 源桥（1 分钟；价格差口径）：路径效率 |P_end − P_0| / Σ|ΔP|；最高价时点 argmax_k P_k / N_bars
    with np.errstate(all='ignore'):
        P1 = np.exp(X1)
        dp = np.abs(np.diff(P1, axis=0)).sum(0)
        F['src481_path_eff_1m'] = np.where(s1 >= 0, np.where(dp > 0, np.abs(P1[-1] - P1[0]) / dp, 0.0), np.nan)
        pre1 = np.arange(len(LAB1))[:, None] < np.maximum(s1, 0)[None, :]
        P1m = np.where(pre1, -np.inf, P1)[1:]
        F['src481_high_timing_1m'] = np.where(s1 >= 0, (np.argmax(P1m, axis=0) + 1) / float(len(LAB1) - 1), np.nan)
    # ---- 5 / 1 一致性（健康）
    with np.errstate(all='ignore'):
        both = (s5 >= 0) & (s1 >= 0)
        lab5_in1 = np.array([I1[s] for s in LAB5[1:]])
        row5 = np.arange(1, len(LAB5))[:, None]
        live = (row5 >= s5[None, :]) & (lab5_in1[:, None] >= s1[None, :])      # 两边都已过本日第一笔成交
        d51 = np.where(live, np.abs(X5[1:] - X1[lab5_in1]), 0.0)
        d51 = np.where(np.isfinite(d51), d51, np.inf)
        F['h51_endpoint_maxabs'] = np.where(both, d51.max(0), np.nan)
    F['h51_vol_diff'] = F['vol_min'] - F['vol_min1']
    # ---- 状态
    traded_any = s5 >= 0
    stt = np.full(n, STATE['PATH_OK'], np.int8)
    stt[traded_any & (F['pl_5'] == 0)] = STATE['FLAT_TRADED']
    stt[~traded_any] = STATE['NO_TRADE_PRESENT']
    stt[hole5] = STATE['HOLE']
    F['state'] = stt
    F['hole1'] = hole1.astype(np.int8)
    for k in list(F):
        if k.endswith('_5') and k[:-2] in ('pl', 'rv', 'net', 'up', 'dn', 'eff'):
            F[k] = np.where(hole5, np.nan, F[k])
        if k.endswith('_1') or k.endswith('_10'):
            if k.split('_')[0] in ('pl', 'rv', 'net', 'up', 'dn', 'eff'):
                F[k] = np.where(hole1, np.nan, F[k])
    return codes, F
