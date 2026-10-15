# -*- coding: utf-8 -*-
"""E6n 测量层（plan §4.4、§5.1–§5.6、§6.2、§6.4；brief §1.3-4 / -5、W07）。不读任何收益。
  full ：分钟面板 + 日频官方价（同源日频缓存，≤ 2026-03-27）→ 全日历 × 全代码的原始量、过去基线、五面、两构造分量、三 raw 控制分量、
         481 源桥列 → meas/full/<名>.npy（float64，行 = 日历，列 = codes）+ dates.npy / codes.npy。
  seg  --seg S：E6m 段上下文（pool0 单元坐标 (t, c) 字典序）→ 源 Q（J_B1_qCC 原值 → pool0 当日 log 市值 OLS → 'lo' → rank(pct)）、
         QGOOD（源 Q 坏度 ≤ 1/3）、旧 K 坏度 k0（pcond）、五面坏度（'hi' 主向 / 'lo' 反向；当日有限输入 + 源 log-size）、
         两条 OHLC 桥坏度（源登记方向 high_bad）、raw 构造坐标 kq'（plan §6.2：完整参考域初始化 Q0 原值、只对有效且资格内写新 raw、
         走源 Q 同一中性化 / 排名、再把非激活股票覆盖回源 kQ；λ = 0 或整日无激活 → 当日直接回源 kQ）、五面克隆坐标（owner 有限域内重建 Q 秩）
         → meas/<段>/*.npy（单元向量）+ manifest.json。
基线：b20 = T−20…T−1 固定交易日位置有限值中位数（≥ 10）；尾盘量份额与 8 格 profile = 逐日份额算术均值（每个历史日 8 格全有限非负、总量 > 0
才贡献；同交易所制度：沪市 2018-08-20 前 / 后分开，深市一个制度；不足 10 日 → UNKNOWN）。比率分母 ≤ 0 → UNKNOWN。"""
import os
import sys
import json
import time
import pickle
import argparse

import numpy as np
import pandas as pd

import e6n_core as N

DAILY = N.DAILY_FULL
E6M_TMP = os.path.join(N.E6M_WORK, 'tmp')
EPS = 1e-4
REFORM = 20180820
FACETS = ('PL_REL20', 'TAIL_PUSH', 'TAIL_VOL_REL20', 'JSD_PROFILE20', 'RV_REL20')
MIN_FIELDS = ('state', 'present', 'pl_5', 'rv_5', 'net_5', 'eff_5', 'up_5', 'dn_5', 'pl_1', 'rv_1', 'eff_1', 'pl_10', 'rv_10', 'eff_10',
              'p_1430', 'p_late0', 'p_late1', 'p_late2', 'p_late3', 'p_late4', 'p_late5', 'p_last', 'p0', 'auction_traded', 'auction_vol',
              'vb1', 'vb2', 'vb3', 'vb4', 'vb5', 'vb6', 'vb7', 'vb8', 'vol_min', 'v1_1500', 'v1_1458_59', 'r_lunch_5', 'r_last_5',
              't_high_5', 't_low_5', 'n_late_traded', 'maxrun_notrade_1', 'src481_path_eff_1m', 'src481_high_timing_1m', 'start5', 'hole1')


def mdir(*p):
    d = N.P('meas', *p)
    os.makedirs(d if not os.path.splitext(d)[1] else os.path.dirname(d), exist_ok=True)
    return d


def panel_root():
    d = N.P('minute_panel')
    cands = sorted([os.path.join(d, x) for x in os.listdir(d) if x.startswith('cache_') and os.path.exists(os.path.join(d, x, 'panel_manifest.json'))],
                   key=os.path.getmtime)
    if not cands:
        raise RuntimeError('分钟面板未合并完成')
    return cands[-1]


# ------------------------------------------------------------------ 全日历
def load_daily():
    import pyarrow.parquet as pq
    t = pq.read_table(DAILY, columns=['trade_date', 'stock_code', 'open', 'close', 'high', 'low', 'lclose', 'is_open', 'volume'])
    df = t.to_pandas().reset_index()
    N.assert_index_ok(pd.DatetimeIndex(df['trade_date']), 'daily full')
    df['d'] = df['trade_date'].dt.strftime('%Y%m%d').astype(np.int64)
    cal = np.sort(df['d'].unique())
    codes = np.array(sorted(c for c in df['stock_code'].astype(str).unique() if len(c) == 6 and c[0] in '036'), dtype='U6')
    ri = pd.Index(cal).get_indexer(df['d'])
    ci = pd.Index(codes).get_indexer(df['stock_code'].astype(str))
    ok = ci >= 0
    out = {}
    for k in ('open', 'close', 'high', 'low', 'lclose', 'is_open', 'volume'):
        A = np.full((len(cal), len(codes)), np.nan)
        A[ri[ok], ci[ok]] = df[k].to_numpy(float)[ok]
        out[k] = A
    return cal, codes, out


def load_minute(cal, codes, fields=MIN_FIELDS):
    root = panel_root()
    out = {k: np.full((len(cal), len(codes)), np.nan) for k in fields}
    rpos = {int(d): i for i, d in enumerate(cal)}
    for y in sorted(x for x in os.listdir(root) if x.startswith('Y')):
        yd = os.path.join(root, y)
        dates = np.load(os.path.join(yd, 'dates.npy'))
        cds = np.load(os.path.join(yd, 'codes.npy'))
        if dates.max() > N.MARKET_DATA_END_INT:
            raise RuntimeError('分钟面板含截止日之后的日期')
        r = np.array([rpos.get(int(d), -1) for d in dates])
        if (r < 0).any():
            raise RuntimeError('分钟日不在日频日历：%s' % dates[r < 0][:5])
        c = pd.Index(codes).get_indexer(cds)
        okc = c >= 0
        for k in fields:
            A = np.load(os.path.join(yd, ('present' if k == 'present' else k) + '.npy'), mmap_mode='r')
            X = np.asarray(A, dtype=float)
            if k not in ('present',) and not np.issubdtype(A.dtype, np.floating):
                X = np.where(np.asarray(A) == -9, np.nan, X)
            out[k][np.ix_(r, c[okc])] = X[:, okc]
    out['minute_day'] = np.isin(cal, np.concatenate([np.load(os.path.join(root, y, 'dates.npy')) for y in os.listdir(root) if y.startswith('Y')]))
    return out, root


def b20_median(X, w=20, mn=10, chunk=400):
    """过去 w 个固定交易日位置（不含当日）的有限值中位数，有限数 ≥ mn。"""
    from numpy.lib.stride_tricks import sliding_window_view as swv
    T, C = X.shape
    out = np.full((T, C), np.nan)
    for j0 in range(0, C, chunk):
        Xc = X[:, j0:j0 + chunk]
        P = np.vstack([np.full((w, Xc.shape[1]), np.nan), Xc])
        W = swv(P, w, axis=0)[:T]                               # 窗口 t = X[t−w … t−1]
        cnt = np.isfinite(W).sum(-1)
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            med = np.nanmedian(W, axis=-1)
        out[:, j0:j0 + chunk] = np.where(cnt >= mn, med, np.nan)
    return out


def pre20_mean(X, ok, w=20, mn=10):
    """过去 w 个位置里 ok（完整日）的算术均值，个数 ≥ mn。X 可为 (T, C) 或 (T, C, K)。"""
    T = X.shape[0]
    V = np.where(ok if X.ndim == 2 else ok[..., None], X, 0.0)
    M = ok.astype(float)
    cs = np.concatenate([np.zeros((1,) + V.shape[1:]), np.cumsum(V, axis=0)], axis=0)
    cm = np.concatenate([np.zeros((1,) + M.shape[1:]), np.cumsum(M, axis=0)], axis=0)
    t = np.arange(T)
    lo = np.maximum(t - w, 0)
    s = cs[t] - cs[lo]
    n = cm[t] - cm[lo]
    with np.errstate(all='ignore'):
        mean = s / (n if X.ndim == 2 else n[..., None])
    return np.where((n >= mn) if X.ndim == 2 else (n >= mn)[..., None], mean, np.nan)


def regime_split(cal, codes, X, ok):
    """沪市按 2018-08-20 前 / 后分制度、深市一个制度：返回同制度过去 20 日完整日均值。"""
    sh = np.char.startswith(codes.astype(str), '6')
    post = cal >= REFORM
    okp = ok & post[:, None]
    oka = ok & ~post[:, None]
    m_post = pre20_mean(X, okp)
    m_pre = pre20_mean(X, oka)
    m_all = pre20_mean(X, ok)
    shmask = sh if X.ndim == 2 else sh[:, None]
    pm = post[:, None] if X.ndim == 2 else post[:, None, None]
    out = np.where(pm, m_post, m_pre)
    return np.where(shmask[None, ...] if X.ndim == 2 else shmask[None, :, :], out, m_all)


def rel_nonneg(today, base):
    """log1p(today / base) 的无溢出版（plan 附录 relative_nonnegative）：today < 0、base ≤ 0 或非有限 → NaN；today = 0 → 0。"""
    out = np.full(today.shape, np.nan)
    ok = np.isfinite(today) & np.isfinite(base) & (today >= 0) & (base > 0)
    with np.errstate(all='ignore'):
        lt = np.where(ok & (today > 0), np.log(np.where(today > 0, today, 1.0)), -np.inf)
        lb = np.log(np.where(ok, base, 1.0))
        out[ok] = (np.logaddexp(lt, lb) - lb)[ok]
    return out


def jsd_vec(x, y):
    """附录 jsd() 的向量版（最后一维 = 8 格）：各自先按最大值缩放再归一；0 项贡献 0；任一缺失 / 负 / 全零 → NaN。"""
    okx = np.isfinite(x).all(-1) & (x >= 0).all(-1) & (np.nan_to_num(x, nan=-1).max(-1) > 0)
    oky = np.isfinite(y).all(-1) & (y >= 0).all(-1) & (np.nan_to_num(y, nan=-1).max(-1) > 0)
    ok = okx & oky
    with np.errstate(all='ignore'):
        xs = x / np.where(ok, x.max(-1), 1.0)[..., None]
        ys = y / np.where(ok, y.max(-1), 1.0)[..., None]
        p = xs / xs.sum(-1)[..., None]
        q = ys / ys.sum(-1)[..., None]
        m = (p + q) / 2
        kp = np.where(p > 0, p * np.log2(np.where(p > 0, p, 1.0) / np.where(m > 0, m, 1.0)), 0.0).sum(-1)
        kq = np.where(q > 0, q * np.log2(np.where(q > 0, q, 1.0) / np.where(m > 0, m, 1.0)), 0.0).sum(-1)
    return np.where(ok, .5 * (kp + kq), np.nan)


def daily_shares(V):
    """逐日 8 格份额（附录 prior_profile 同式：先 /max 再 /sum）。V：(T, C, 8)。"""
    with np.errstate(all='ignore'):
        mx = V.max(-1)
        A = V / np.where(mx > 0, mx, np.nan)[..., None]
        return A / A.sum(-1)[..., None]


def build_full():
    t0 = time.time()
    cal, codes, D = load_daily()
    M, root = load_minute(cal, codes)
    N.log('full：日历 %d 日（%d–%d）× %d 码；分钟面板 %s' % (len(cal), cal[0], cal[-1], len(codes), N.rel(root)))
    out = {}
    pres = M['present'] == 1
    st = M['state']
    path_ok = pres & ((st == 0) | (st == 1))                    # PATH_OK / FLAT_TRADED
    out['minute_present'] = pres.astype(float)
    out['minute_state'] = np.where(pres, st, np.nan)
    for f in ('5', '1', '10'):
        okf = path_ok if f == '5' else (path_ok & (M['hole1'] != 1))
        pl = np.where(okf, M['pl_' + f], np.nan)
        rv = np.where(okf, M['rv_' + f], np.nan)
        eff = np.where(okf, M['eff_' + f], np.nan)
        out['PL_' + f] = pl
        out['RV_' + f] = rv
        out['EFF_' + f] = eff
        out['b20_PL_' + f] = b20_median(pl)
        out['b20_RV_' + f] = b20_median(rv)
        out['PL_REL20_' + f] = rel_nonneg(pl, out['b20_PL_' + f])
        out['RV_REL20_' + f] = rel_nonneg(rv, out['b20_RV_' + f])
        with np.errstate(all='ignore'):
            out['h_path_' + f] = np.sqrt(rv) * (1.0 - eff)
            out['sqrtRV_' + f] = np.sqrt(rv)
    out['NET_5'] = np.where(path_ok, M['net_5'], np.nan)
    out['UP_5'] = np.where(path_ok, M['up_5'], np.nan)
    out['DN_5'] = np.where(path_ok, M['dn_5'], np.nan)
    C = D['close']
    O = D['open']
    H = D['high']
    L_ = D['low']
    LC = D['lclose']
    with np.errstate(all='ignore'):
        Lt = np.where(path_ok & (C > 0) & (M['p_1430'] > 0), np.log(C / M['p_1430']), np.nan)
    out['L_TAIL'] = Lt
    out['L_TAIL_TERMINAL'] = np.where(path_ok & (M['p_1430'] > 0) & (M['p_last'] > 0), np.log(M['p_last'] / M['p_1430']), np.nan)
    out['b20_absL'] = b20_median(np.abs(Lt))
    with np.errstate(all='ignore'):
        b = out['b20_absL']
        out['TAIL_PUSH'] = np.where(np.isfinite(Lt) & np.isfinite(b) & (b > 0), np.arcsinh(Lt / np.where(b > 0, b, 1.0)), np.nan)
    VB = np.stack([M['vb%d' % k] for k in range(1, 9)], axis=-1)
    tot = VB.sum(-1)
    complete = path_ok & np.isfinite(VB).all(-1) & (VB >= 0).all(-1) & (tot > 0)
    with np.errstate(all='ignore'):
        s_tail = np.where(complete, M['vb8'] / tot, np.nan)
    out['S_TAIL'] = s_tail
    out['base_S_TAIL'] = regime_split(cal, codes, np.where(complete, s_tail, 0.0), complete)
    out['TAIL_VOL_REL20'] = rel_nonneg(s_tail, out['base_S_TAIL'])
    SH = daily_shares(np.where(complete[..., None], VB, np.nan))
    base_prof = regime_split(cal, codes, np.where(complete[..., None], SH, 0.0), complete)
    out['JSD_PROFILE20'] = np.where(complete, jsd_vec(np.where(complete[..., None], VB, np.nan), base_prof), np.nan)
    for k in range(8):
        out['SHARE_%d' % (k + 1)] = SH[..., k]
        out['base_SHARE_%d' % (k + 1)] = base_prof[..., k]
    # 481 源桥（W07）：vsds K8 = 8 格份额与基线的 L1 均距；K5 = 唯一不重叠 5 时段读法；熵 / HHI / 对均匀 KL / 单格最大偏离 = identity 标签
    with np.errstate(all='ignore'):
        out['SRC481_VSDS_K8'] = np.abs(SH - base_prof).mean(-1)
        K5 = np.stack([VB[..., 0], VB[..., 1] + VB[..., 2], VB[..., 3], VB[..., 4] + VB[..., 5] + VB[..., 6], VB[..., 7]], axis=-1)
        SH5 = daily_shares(np.where(complete[..., None], K5, np.nan))
        base5 = regime_split(cal, codes, np.where(complete[..., None], SH5, 0.0), complete)
        out['SRC481_VSDS_K5'] = np.abs(SH5 - base5).mean(-1)
        out['SRC481_VOLUME_ENTROPY_1D'] = -np.where(SH > 0, SH * np.log2(np.where(SH > 0, SH, 1.0)), 0.0).sum(-1)
        hhi = (SH * SH).sum(-1)
        out['SRC481_VOLUME_HHI_1D'] = hhi
        out['SRC481_VOLUME_HHI_NORM_1D'] = (hhi - 1 / 8.0) / (1 - 1 / 8.0)
        out['SRC481_VSDS_KL_1D'] = np.where(SH > 0, SH * np.log2(np.where(SH > 0, SH, 1.0) * 8.0), 0.0).sum(-1)
        out['SRC481_SESSION_VOLUME_DEVIATION_MAX'] = np.abs(SH - base_prof).max(-1)
        out['SRC481_CLOSING_30MIN_VOLUME_RATIO'] = s_tail
    out['SRC481_PATH_EFF_1M'] = np.where(path_ok & (M['hole1'] != 1), M['src481_path_eff_1m'], np.nan)
    out['SRC481_HIGH_TIMING_1M'] = np.where(path_ok & (M['hole1'] != 1), M['src481_high_timing_1m'], np.nan)
    # Q_CLOSE_THIN 分量（附录 thin_close_penalty 同式）
    LATE = np.stack([M['p_late%d' % k] for k in range(6)], axis=-1)
    late_ok = path_ok & np.isfinite(LATE).all(-1) & (LATE > 0).all(-1)
    with np.errstate(all='ignore'):
        pmed = np.where(late_ok, np.median(np.where(late_ok[..., None], LATE, 1.0), axis=-1), np.nan)
        u = np.where(late_ok & (C > 0), np.maximum(np.log(C / pmed), 0.0), np.nan)
        base = out['base_S_TAIL']
        thin_ok = np.isfinite(s_tail) & (s_tail >= 0) & (s_tail <= 1) & np.isfinite(base) & (base > 0) & (base <= 1)
        thin = np.where(thin_ok, np.maximum(0.0, 1.0 - s_tail / np.where(base > 0, base, 1.0)), np.nan)
    out['P_LATE_MED'] = pmed
    out['U_CLOSE'] = u
    out['THIN'] = thin
    out['h_close'] = np.where(np.isfinite(u) & np.isfinite(thin), u * thin, np.nan)
    out['h_close_level'] = np.where(np.isfinite(out['h_close']), u, np.nan)          # Q_CLOSE_LEVEL 用 Q_CLOSE_THIN 的有效掩码
    with np.errstate(all='ignore'):
        rng = np.where((H > 0) & (L_ > 0) & (H >= L_), np.log(H / L_), np.nan)
        out['LOG_HL'] = rng
        out['GAP'] = np.where((O > 0) & (LC > 0), np.log(O / LC), np.nan)
        out['OC'] = np.where((O > 0) & (C > 0), np.log(C / O), np.nan)
        out['CLOSE_VS_LAST'] = np.where(path_ok & (C > 0) & (M['p_last'] > 0), np.log(C / M['p_last']), np.nan)
    for k in ('auction_traded', 'auction_vol', 'v1_1500', 'v1_1458_59', 'r_lunch_5', 'r_last_5', 't_high_5', 't_low_5', 'n_late_traded',
              'maxrun_notrade_1', 'start5', 'vol_min'):
        out['M_' + k] = np.where(pres, M[k], np.nan)
    out['MINUTE_DAY'] = np.repeat(M['minute_day'][:, None], len(codes), axis=1).astype(float)
    d = mdir('full')
    np.save(os.path.join(d, 'dates.npy'), cal)
    np.save(os.path.join(d, 'codes.npy'), codes)
    man = {}
    for k, v in out.items():
        p = os.path.join(d, k + '.npy')
        tmp = p + '.tmp'
        with open(tmp, 'wb') as fh:
            np.save(fh, np.asarray(v, dtype=np.float64))
        os.replace(tmp, p)
        man[k] = dict(finite=int(np.isfinite(v).sum()))
    N.atomic_write_json(os.path.join(d, 'manifest.json'), dict(fields=man, n_dates=len(cal), n_codes=len(codes), panel=N.rel(root),
                                                               secs=round(time.time() - t0, 1)))
    N.log('full 完成：%d 个字段，%.0f s' % (len(out), time.time() - t0))
    return d


# ------------------------------------------------------------------ 段（pool0 单元坐标）
class SegM(object):
    """一段的测量上下文：E6m 段上下文 pkl（源 build_period 落盘件）+ 全日历测量。单元 = pool0 格 (t, c) 字典序，c ∈ ccols = p0.any(0)。"""

    def __init__(self, seg):
        self.seg = seg
        with open(os.path.join(E6M_TMP, 'ctx_%s.pkl' % seg), 'rb') as fh:
            self.ctx = pickle.load(fh)
        ctx = self.ctx
        self.pool0 = ctx['pool0']
        p0 = ctx['p0']
        self.ccols = np.flatnonzero(p0.any(0))
        self.codes = np.array([str(c) for c in self.pool0.columns[self.ccols]], dtype='U6')
        self.dates = np.array([int(pd.Timestamp(x).strftime('%Y%m%d')) for x in self.pool0.index], dtype=np.int64)
        N.assert_end_ok(str(self.dates.max()), 'seg %s' % seg)
        t, c = np.nonzero(p0[:, self.ccols])
        self.t, self.c = t, c
        self.n = len(t)
        self.T, self.Nc = len(self.dates), len(self.ccols)
        fd = N.P('meas', 'full')
        fdates = np.load(os.path.join(fd, 'dates.npy'))
        fcodes = np.load(os.path.join(fd, 'codes.npy'))
        self.ri = pd.Index(fdates).get_indexer(self.dates)
        self.cj = pd.Index(fcodes).get_indexer(self.codes)
        if (self.ri < 0).any():
            raise RuntimeError('段日期不在全日历')
        self._full = fd

    def grid(self, name):
        """全日历字段 → 段网格 (T, Nc)（代码不在全日历的列 NaN）。"""
        A = np.load(os.path.join(self._full, name + '.npy'), mmap_mode='r')
        out = np.full((self.T, self.Nc), np.nan)
        ok = self.cj >= 0
        out[:, ok] = np.asarray(A[np.ix_(self.ri, self.cj[ok])])
        return out

    def cells(self, G):
        return np.asarray(G)[self.t, self.c]

    def frame(self, G):
        out = np.full(self.pool0.shape, np.nan)
        out[:, self.ccols] = G
        return pd.DataFrame(out, index=self.pool0.index, columns=self.pool0.columns)

    def pct_cells(self, G, direction, pool=None):
        """源口径：pool0（或给定池）当日 log 市值 OLS（C.precompute_neutralized_factor）→ 方向 → rank(pct) → 单元。"""
        import comprehensive_factor_diagnosis as C
        import e6j_slot as SL
        cache = C.precompute_neutralized_factor(self.frame(G), self.pool0 if pool is None else pool, self.ctx['log_mcap'])
        pc = SL.pct_dir(cache, direction)
        D = np.full((self.T, self.Nc), np.nan)
        di = {x: i for i, x in enumerate(self.pool0.index)}
        cpos = pd.Index(self.pool0.columns[self.ccols])
        for day, s in pc.items():
            j = cpos.get_indexer(s.index)
            ok = j >= 0
            D[di[day], j[ok]] = s.to_numpy(float)[ok]
        return self.cells(D)

    def pool_of_cells(self, cellmask):
        m = np.zeros(self.pool0.shape)
        m[self.t[cellmask], self.ccols[self.c[cellmask]]] = 1.0
        return pd.DataFrame(m, index=self.pool0.index, columns=self.pool0.columns)

    def dict_cells(self, cache):
        D = np.full((self.T, self.Nc), np.nan)
        di = {x: i for i, x in enumerate(self.pool0.index)}
        cpos = pd.Index(self.pool0.columns[self.ccols])
        for day, s in cache.items():
            if day not in di:
                continue
            j = cpos.get_indexer(s.index)
            ok = j >= 0
            D[di[day], j[ok]] = s.to_numpy(float)[ok]
        return self.cells(D)


def q_source(S):
    """源 Q（W04 / W05）：d = |log(C/lclose)|（E6i Base 有效性，e6m_adapter.q_source 同式），Q0 原值 = 1/(d + 1e−4)；kQ = 源中性化 'lo' 秩。"""
    data = S.ctx['data']
    close = data['close'].astype(float)
    g = lambda k: data[k].reindex(index=close.index, columns=close.columns).astype(float).to_numpy()
    is_open = (data['is_open'].reindex(index=close.index, columns=close.columns) == 1).to_numpy()
    o, h, l, c, lc = g('open'), g('high'), g('low'), g('close'), g('lclose')
    with np.errstate(all='ignore'):
        valid = is_open & (o > 0) & (h > 0) & (l > 0) & (c > 0) & (lc > 0)
        valid &= (l <= np.minimum(o, c) + 1e-9) & (h >= np.maximum(o, c) - 1e-9)
        r = np.where(valid, np.log(c / lc), np.nan)
    dfull = pd.DataFrame(np.abs(r), index=close.index, columns=close.columns).reindex_like(S.pool0)
    dG = dfull.to_numpy()[:, S.ccols]
    with np.errstate(all='ignore'):
        q = 1.0 / (dG + EPS)
    q = np.where(np.isfinite(q), q, np.nan)
    return dG, q


def build_seg(seg):
    t0 = time.time()
    S = SegM(seg)
    od = mdir(seg)
    W = {}
    facts = dict(seg=seg, n_cells=int(S.n), T=int(S.T), Nc=int(S.Nc))
    dG, q0G = q_source(S)
    # 源 Q 原值对 E6j 缓存 J_B1_qCC（逐位）
    import e6j_slot as SL
    jq, _ = SL.j_member_raw(seg, 'J_B1_qCC')
    jcells = jq[S.t, S.c] if jq.shape == (S.T, S.Nc) else None
    q0c = S.cells(q0G)
    if jcells is not None:
        both = np.isfinite(jcells) & np.isfinite(q0c)
        facts['q0raw_vs_J_B1_qCC'] = dict(shape_ok=True, finite_mismatch=int((np.isfinite(jcells) != np.isfinite(q0c)).sum()),
                                          maxabs=float(np.abs(jcells[both] - q0c[both]).max()) if both.any() else None,
                                          bitwise_equal=int((jcells[both] == q0c[both]).sum()), n_both=int(both.sum()))
        q0G_src = jq                                       # 源原值（逐位用源缓存）
    else:
        facts['q0raw_vs_J_B1_qCC'] = dict(shape_ok=False, j_shape=list(jq.shape))
        q0G_src = q0G
    kQ = S.pct_cells(q0G_src, 'lo')
    W['kQ'] = kQ
    W['QGOOD'] = (np.isfinite(kQ) & (kQ <= 1.0 / 3.0)).astype(np.int8)
    W['d'] = S.cells(dG)
    W['q0raw'] = S.cells(q0G_src)
    W['k0'] = S.dict_cells(S.ctx['pcond'])
    # 五面与频率桥：原始 / 相对列（单元）+ 坏度
    fac_grids = {}
    for f in FACETS:
        name = f if f in ('TAIL_PUSH', 'TAIL_VOL_REL20', 'JSD_PROFILE20') else f + '_5'
        fac_grids[(f, 5)] = S.grid(name)
    for f in ('PL_REL20', 'RV_REL20'):
        for fr in (1, 10):
            fac_grids[(f, fr)] = S.grid('%s_%d' % (f, fr))
    for (f, fr), G in fac_grids.items():
        tag = '%s_f%d' % (f, fr)
        W['raw_' + tag] = S.cells(G)
        W['km_%s_hi' % tag] = S.pct_cells(G, 'hi')
        if fr == 5:
            W['km_%s_lo' % tag] = S.pct_cells(G, 'lo')
    # OHLC 桥（源登记方向 high_bad）
    for nm, (src, mid) in (('K_RANGE_SOURCE', ('J', 'J_B2_POINT_TR_RANGE')), ('CLV20_SOURCE', ('E6I', 'C_clv20'))):
        arr = SL.j_member_raw(seg, mid)[0] if src == 'J' else SL.e6i_member_raw(seg, mid)[0]
        if arr.shape != (S.T, S.Nc):
            raise RuntimeError('%s 网格 %s 与段网格 %s 不一致' % (nm, arr.shape, (S.T, S.Nc)))
        W['raw_%s_f5' % nm] = S.cells(arr)
        W['km_%s_f5_hi' % nm] = S.pct_cells(arr, 'hi')
    # raw 构造分量（单元）
    comp = {}
    for fr in (5, 1, 10):
        comp[('h_path', fr)] = S.cells(S.grid('h_path_%d' % fr))
        comp[('sqrtRV', fr)] = S.cells(S.grid('sqrtRV_%d' % fr))
    comp[('h_close', 5)] = S.cells(S.grid('h_close'))
    comp[('h_close_level', 5)] = S.cells(S.grid('h_close_level'))
    comp[('log_hl', 5)] = S.cells(S.grid('LOG_HL'))
    for k, v in comp.items():
        W['comp_%s_f%d' % k] = v
    for nm in ('U_CLOSE', 'THIN', 'S_TAIL', 'base_S_TAIL', 'L_TAIL', 'L_TAIL_TERMINAL', 'b20_absL', 'PL_5', 'RV_5', 'EFF_5', 'NET_5', 'UP_5', 'DN_5',
               'GAP', 'OC', 'LOG_HL', 'CLOSE_VS_LAST', 'minute_present', 'minute_state', 'MINUTE_DAY', 'M_auction_traded', 'M_v1_1500',
               'M_v1_1458_59', 'M_n_late_traded', 'M_maxrun_notrade_1', 'M_start5', 'M_t_high_5', 'M_t_low_5', 'M_vol_min',
               'SRC481_PATH_EFF_1M', 'SRC481_HIGH_TIMING_1M', 'SRC481_VSDS_K8', 'SRC481_VSDS_K5', 'SRC481_VOLUME_ENTROPY_1D',
               'SRC481_VOLUME_HHI_1D', 'SRC481_VOLUME_HHI_NORM_1D', 'SRC481_VSDS_KL_1D', 'SRC481_SESSION_VOLUME_DEVIATION_MAX',
               'SRC481_CLOSING_30MIN_VOLUME_RATIO'):
        W['col_' + nm] = S.cells(S.grid(nm))
    for k, v in W.items():
        np.save(os.path.join(od, k + '.npy'), np.asarray(v))
    np.save(os.path.join(od, 'cells_t.npy'), S.t)
    np.save(os.path.join(od, 'cells_c.npy'), S.c)
    np.save(os.path.join(od, 'dates.npy'), S.dates)
    np.save(os.path.join(od, 'codes.npy'), S.codes)
    facts.update(kQ_finite=float(np.isfinite(kQ).mean()), qgood_share=float(W['QGOOD'].mean()),
                 secs=round(time.time() - t0, 1))
    N.atomic_write_json(os.path.join(od, 'manifest_base.json'), facts)
    N.log('seg %s 基础测量：%d 单元，%.0f s；q0raw vs J：%s' % (seg, S.n, time.time() - t0, json.dumps(facts['q0raw_vs_J_B1_qCC'])))
    return S, W


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['full', 'seg'])
    ap.add_argument('--seg')
    a = ap.parse_args()
    t0 = time.time()
    if a.step == 'full':
        d = build_full()
        N.write_receipt('E6n_meas_full', [os.path.join(d, 'manifest.json')], code=[__file__], secs=round(time.time() - t0, 1))
    else:
        build_seg(a.seg)
        N.write_receipt('E6n_meas_seg_%s' % a.seg, [N.P('meas', a.seg, 'manifest_base.json')], code=[__file__], secs=round(time.time() - t0, 1))


if __name__ == '__main__':
    main()
