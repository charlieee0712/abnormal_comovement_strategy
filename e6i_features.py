#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 八轴估计量目录 (plan §4 逐字落实; brief §1.3 契约)。

两套实现身份 (plan §3.1):
  LEGACY  —— 源键的精确复现 (原输入/公式/窗口/min_periods/ddof/符号/缺失行为); 负责锚。
             值直接取段内 S.feats (就是源函数的输出) 或按源表达式在同一数据上重算。
  RESEARCH —— 本轮新测量: 截至 t 已知的有效日频历史; 窗口按市场交易日网格 (停牌行留空不压缩);
             有效观测 >= max(3, ceil(0.7w)); 在允许历史 (S.wdata_i, 段首前 260 自然日) 上算,
             再取 pool0 网格; 方向不写进测量函数 (source_sign = as_is), 在 role 层登记。

价格约定 (plan §3.2): r = log(C/lclose), o = log(O/lclose), c = log(C/O), h = log(H/O),
  l = log(L/O); 同日比值复权因子抵消; 跨日路径 (R / AR / CS / Roll / EDGE / 残差) 用
  comprehensive_factor_diagnosis.adjust_factor (引擎同一个调整器) 得到的后复权价;
  金额用原始元; 换手率是【比例】、分母 = 流通股 (P0 实测, checks/p0_source_facts_*.json)。
一字板三政策 (plan §3.3): OBS (合法 H==L 保留零极差) / LIMIT_SENS (已知触板日整日剔出
  基于极差的估计量) / LEGACY_PARK_NAN (源: H==L 一律 NaN)。触板 = H>=涨停价-0.005 或
  L<=跌停价+0.005, 限价表按 ticker 标签对齐 (E6g 列错位教训)。
事件钟 (plan §3.4): τ = 截至 t 最近一次已知 I11 触发 (段内源信号, 与 pool0 同源);
  主剔事件版只剔已知触发日 s 与已发生的 s+1、s+2; 事件前基线固定用 τ 之前 w 个交易日。
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

import comprehensive_factor_diagnosis as C
from pool_screening_v2 import define_i11_signal, compute_parkinson_vol, \
    compute_abnormal_turnover, compute_reversal_skip1
from event_study import get_base_pool
import e6f_core as F
import e6h_core as H

EPS = 1e-4
TOL_LIMIT = 0.005
LN2 = math.log(2.0)
MJ = (0.273520, 0.160358, 0.365212, 0.200910)     # Meilijson 四分量权重 (plan §4.3; 待与原文复核)
MJ_Q4DEN = 2 * LN2 - 5.0 / 4.0


def minobs(w):
    return max(3, int(math.ceil(0.7 * w)))


# ============================================================
# 0. 滚动工具 (numpy (T, N) 数组, 时间在第 0 轴; NaN = 无效观测)
# ============================================================
def _df(A):
    return pd.DataFrame(A)


def rmean(A, w, mo=None):
    return _df(A).rolling(w, min_periods=mo or minobs(w)).mean().values


def rsum(A, w, mo=None):
    return _df(A).rolling(w, min_periods=mo or minobs(w)).sum().values


def rcount(A, w):
    return _df(np.isfinite(A).astype(float)).rolling(w, min_periods=1).sum().values


def rstd(A, w, mo=None, ddof=1):
    return _df(A).rolling(w, min_periods=mo or minobs(w)).std(ddof=ddof).values


def rvar(A, w, mo=None, ddof=1):
    return _df(A).rolling(w, min_periods=mo or minobs(w)).var(ddof=ddof).values


def rmed(A, w, mo=None):
    return _df(A).rolling(w, min_periods=mo or minobs(w)).median().values


def rquant(A, w, q, mo=None):
    return _df(A).rolling(w, min_periods=mo or minobs(w)).quantile(q).values


def rmax(A, w, mo=None):
    return _df(A).rolling(w, min_periods=mo or minobs(w)).max().values


def rmin(A, w, mo=None):
    return _df(A).rolling(w, min_periods=mo or minobs(w)).min().values


def rcorr(A, B, w, mo=None):
    return _df(A).rolling(w, min_periods=mo or minobs(w)).corr(_df(B)).values


def rcov(A, B, w, mo=None):
    return _df(A).rolling(w, min_periods=mo or minobs(w)).cov(_df(B)).values


def lag(A, k=1):
    out = np.full_like(A, np.nan)
    if k < A.shape[0]:
        out[k:] = A[:-k]
    return out


def _chunked_windows(A, w, fn, chunk=400):
    """对 (T, N) 按列分块取滑窗 (T-w+1, n, w), 调 fn(sw)->(T-w+1, n), 前 w-1 行补 NaN。"""
    T, N = A.shape
    out = np.full((T, N), np.nan)
    if T < w:
        return out
    for j in range(0, N, chunk):
        sw = swv(A[:, j:j + chunk], w, axis=0)          # (T-w+1, n, w)
        out[w - 1:, j:j + chunk] = fn(sw)
    return out


def rmad_same_center(A, w, mo=None):
    """median(|x - m|), m = 同一窗口的中位数 (plan W10: 不能嵌套 rolling 拼)。"""
    mo = mo or minobs(w)

    def fn(sw):
        with np.errstate(all='ignore'):
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                m = np.nanmedian(sw, axis=-1)
                d = np.nanmedian(np.abs(sw - m[..., None]), axis=-1)
        n = np.isfinite(sw).sum(-1)
        return np.where(n >= mo, d, np.nan)
    return _chunked_windows(A, w, fn)


def rtrend(A, w, mo=None):
    """同一窗口 OLS: x_s = a + b (s - mean s) + e (只用有效点)。返回 (b, sqrt(SSE/(n-2)), mean)。"""
    mo = mo or minobs(w)
    tloc = np.arange(w, dtype=float)
    outs = [np.full(A.shape, np.nan) for _ in range(3)]
    T, N = A.shape
    if T < w:
        return outs
    for j in range(0, N, 400):
        sw = swv(A[:, j:j + 400], w, axis=0)
        v = np.isfinite(sw)
        x = np.where(v, sw, 0.0)
        n = v.sum(-1).astype(float)
        st = (v * tloc).sum(-1)
        stt = (v * tloc ** 2).sum(-1)
        sx = x.sum(-1)
        stx = (x * tloc).sum(-1)
        sxx = (x * x).sum(-1)
        with np.errstate(all='ignore'):
            den = n * stt - st ** 2
            b = (n * stx - st * sx) / den
            a = (sx - b * st) / n
            sse = sxx - a * sx - b * stx
            sse = np.maximum(sse, 0.0)
            rs = np.sqrt(sse / (n - 2))
            mu = sx / n
        ok = (n >= max(mo, 3)) & (den > 0)
        outs[0][w - 1:, j:j + 400] = np.where(ok, b, np.nan)
        outs[1][w - 1:, j:j + 400] = np.where(ok, rs, np.nan)
        outs[2][w - 1:, j:j + 400] = np.where(ok, mu, np.nan)
    return outs


def rewcv(A, w, mo=None):
    """有限窗指数权重: p_s ∝ 2^{-age/(w/4)}, age=0 为 t。返回 (mean_p, sd_p/mean_p)。
       sd_p = sqrt(Σp(x-mean_p)^2 / (1-Σp^2)), 权重只在有效点上归一 (plan §4.1)。"""
    mo = mo or minobs(w)
    age = np.arange(w - 1, -1, -1, dtype=float)          # 窗内第 0 个元素最老
    base = 2.0 ** (-age / (w / 4.0))
    m_out = np.full(A.shape, np.nan)
    c_out = np.full(A.shape, np.nan)
    T, N = A.shape
    if T < w:
        return m_out, c_out
    for j in range(0, N, 400):
        sw = swv(A[:, j:j + 400], w, axis=0)
        v = np.isfinite(sw)
        p = v * base
        ps = p.sum(-1)
        with np.errstate(all='ignore'):
            p = p / ps[..., None]
            x = np.where(v, sw, 0.0)
            mp = (p * x).sum(-1)
            s2 = (p * (x - mp[..., None]) ** 2 * v).sum(-1) / (1.0 - (p ** 2).sum(-1))
            cv = np.sqrt(s2) / mp
        n = v.sum(-1)
        ok = n >= mo
        m_out[w - 1:, j:j + 400] = np.where(ok, mp, np.nan)
        c_out[w - 1:, j:j + 400] = np.where(ok & (mp > 0), cv, np.nan)
    return m_out, c_out


def rpct_own_history(V, n=60, mo=None):
    """当前值在自身前 n 个可用历史值内的百分位 (严格小于 + 一半平局)/有效数; 当前值缺失 -> NaN。"""
    mo = mo or minobs(n)
    T, N = V.shape
    out = np.full((T, N), np.nan)
    if T < n + 1:
        return out
    for j in range(0, N, 400):
        sw = swv(V[:, j:j + 400], n + 1, axis=0)           # 最后一个是当前
        cur = sw[..., -1]
        hist = sw[..., :-1]
        v = np.isfinite(hist)
        lt = (hist < cur[..., None]) & v
        eq = (hist == cur[..., None]) & v
        cnt = v.sum(-1)
        with np.errstate(all='ignore'):
            p = (lt.sum(-1) + 0.5 * eq.sum(-1)) / cnt
        out[n:, j:j + 400] = np.where((cnt >= mo) & np.isfinite(cur), p, np.nan)
    return out


def rtop3pos(R, w, mo=None):
    """前 3 大正收益均值: mean(top3 of max(r,0)) —— 正收益不足 3 个时以 0 补 (plan §4.3 Tail)。"""
    mo = mo or minobs(w)

    def fn(sw):
        v = np.isfinite(sw)
        z = np.where(v, np.maximum(sw, 0.0), -np.inf)
        k = min(3, sw.shape[-1])
        top = -np.sort(-z, axis=-1)[..., :k]
        top = np.where(np.isfinite(top), top, 0.0)
        return np.where(v.sum(-1) >= mo, top.mean(-1), np.nan)
    return _chunked_windows(R, w, fn)


def ols_resid_xs(Y, Xs, rows_ok):
    """逐日截面 OLS 残差 (只在 rows_ok[t] 的格上拟合)。Y (T,N), Xs list of (T,N)。"""
    T, N = Y.shape
    out = np.full((T, N), np.nan)
    info = []
    for t in range(T):
        m = rows_ok[t] & np.isfinite(Y[t])
        for Xk in Xs:
            m &= np.isfinite(Xk[t])
        n = int(m.sum())
        k = 1 + len(Xs)
        if n < max(10, k + 3):
            continue
        X = np.column_stack([np.ones(n)] + [Xk[t][m] for Xk in Xs])
        beta, *_ = np.linalg.lstsq(X, Y[t][m], rcond=None)
        out[t, m] = Y[t][m] - X @ beta
        info.append(n)
    return out, info


# ============================================================
# 1. 基础面板 (每段一次; 在 S.wdata_i 上)
# ============================================================
class Base(object):
    """own = S.ccolnames 列 (pool0 出现过的票, 自身时序量); mkt = 全市场列 (同业 / 市场基准)。"""

    def __init__(self, S):
        d = S.wdata_i
        self.S = S
        self.dates_w = d['close'].index
        self.cols_mkt = d['close'].columns
        self.own_cols = pd.Index(S.ccolnames)
        # 段内日期在预热网格上的行号
        pos = self.dates_w.get_indexer(pd.Index(S.dates))
        assert (pos >= 0).all(), '段日期不在预热数据里'
        self.seg_rows = pos

        def g(key, cols):
            return d[key].reindex(index=self.dates_w, columns=cols).astype(float).values

        is_open = d['is_open'].reindex(index=self.dates_w, columns=self.cols_mkt) == 1
        self.open_mkt = is_open.values
        adj = C.adjust_factor(d).reindex(index=self.dates_w, columns=self.cols_mkt).values
        self.adj_mkt = adj
        o, h, l, c, lc = (g(k, self.cols_mkt) for k in ('open', 'high', 'low', 'close', 'lclose'))
        vw = g('vwap', self.cols_mkt)
        valid = self.open_mkt & (o > 0) & (h > 0) & (l > 0) & (c > 0) & (lc > 0)
        valid &= (l <= np.minimum(o, c) + 1e-9) & (h >= np.maximum(o, c) - 1e-9)
        self.valid_mkt = valid
        with np.errstate(all='ignore'):
            self.r_mkt = np.where(valid, np.log(c / lc), np.nan)
        x = g('turnover_rate', self.cols_mkt)
        self.x_mkt = np.where(self.open_mkt & np.isfinite(x) & (x >= 0), x, np.nan)
        ind = d.get('industry_zx1', d.get('industry'))
        ind = ind.reindex(index=self.dates_w, columns=self.cols_mkt)
        codes, self.ind_names = pd.factorize(pd.Series(ind.values.ravel()))
        self.ind_mkt = codes.reshape(ind.shape)            # -1 = 未知
        # own 子集
        oc = self.cols_mkt.get_indexer(self.own_cols)
        assert (oc >= 0).all()
        self.oc = oc
        sel = (slice(None), oc)
        self.O, self.Hh, self.L, self.Cc, self.LC, self.VW = (a[sel] for a in (o, h, l, c, lc, vw))
        self.valid = valid[sel]
        self.open = self.open_mkt[sel]
        self.adj = adj[sel]
        self.x = self.x_mkt[sel]
        self.amt = np.where(self.open, g('amount', self.own_cols), np.nan)
        self.vol = np.where(self.open, g('volume', self.own_cols), np.nan)
        self.ind = self.ind_mkt[sel]
        v = self.valid
        with np.errstate(all='ignore'):
            self.r = np.where(v, np.log(self.Cc / self.LC), np.nan)
            self.o = np.where(v, np.log(self.O / self.LC), np.nan)
            self.c = np.where(v, np.log(self.Cc / self.O), np.nan)
            self.h = np.where(v, np.log(self.Hh / self.O), np.nan)
            self.l = np.where(v, np.log(self.L / self.O), np.nan)
            self.d = np.abs(self.r)
            # 复权价 (跨日路径)
            self.Ca = np.where(v, self.Cc * self.adj, np.nan)
            self.Ha = np.where(v, self.Hh * self.adj, np.nan)
            self.La = np.where(v, self.L * self.adj, np.nan)
            self.Oa = np.where(v, self.O * self.adj, np.nan)
            self.p = np.where(v & (self.VW > 0), self.Cc / self.VW - 1.0, np.nan)
        # 限价 (按 ticker 标签对齐) -> 触板 / 一字板 / 未知
        lu = d.get('limit_up')
        ld = d.get('limit_down')
        if lu is not None and ld is not None:
            LU = lu.reindex(index=self.dates_w, columns=self.own_cols).astype(float).values
            LD = ld.reindex(index=self.dates_w, columns=self.own_cols).astype(float).values
            known = np.isfinite(LU) & np.isfinite(LD)
            touch = known & ((self.Hh >= LU - TOL_LIMIT) | (self.L <= LD + TOL_LIMIT))
            self.limit_known = known
            self.touch = touch & self.valid
        else:
            self.limit_known = np.zeros_like(self.valid)
            self.touch = np.zeros_like(self.valid)
        self.one_word = self.touch & (self.Hh == self.L)
        # 市场 clean 等权日 log 收益 (R_mkt 用) —— clean 只在段内定义; 预热期用全市场有效票等权
        clean = S.clean.reindex(index=self.dates_w, columns=self.cols_mkt).fillna(0).values == 1
        in_seg = np.zeros(len(self.dates_w), bool)
        in_seg[self.seg_rows] = True
        use = np.where(in_seg[:, None], clean, self.valid_mkt)
        radj_mkt = self._adj_logret(c, adj, valid)
        with np.errstate(all='ignore'):
            self.rm = np.nanmean(np.where(use & np.isfinite(radj_mkt), radj_mkt, np.nan), axis=1)
        self.radj_mkt = radj_mkt
        self.radj = radj_mkt[sel]
        # 事件钟: 段内源信号 (与 pool0 同源); 预热期无已知触发
        feats = S.feats
        sig = define_i11_signal(feats, get_base_pool(S.data))
        sig = sig.reindex(index=self.dates_w, columns=self.own_cols).fillna(0).values == 1
        self.trig = sig
        self._tau = None

    @staticmethod
    def _adj_logret(c, adj, valid):
        """复权日 log 收益 log(Ca_t / Ca_prev), prev = 上一个有效日 (跨停牌)。"""
        ca = np.where(valid, c * adj, np.nan)
        prev = pd.DataFrame(ca).ffill().shift(1).values
        with np.errstate(all='ignore'):
            return np.where(valid & np.isfinite(prev) & (prev > 0), np.log(ca / prev), np.nan)

    # ---- 事件钟 ----
    def tau(self):
        """(T_w, N) 截至 t 最近已知触发的行号 (无 -> -1)。"""
        if self._tau is None:
            T, N = self.trig.shape
            idx = np.where(self.trig, np.arange(T)[:, None], -1)
            self._tau = np.maximum.accumulate(idx, axis=0)
        return self._tau

    def to_seg(self, A):
        """(T_w, N_own) -> (T, Nc) 段网格 (own 列就是 ccolnames 顺序)。"""
        return np.ascontiguousarray(A[self.seg_rows], dtype=np.float64)


# ============================================================
# 2. 事件工具
# ============================================================
def causal_mask_nontrigger(B):
    """已知触发日 s 与已发生的 s+1、s+2 置 False (因果: 只用 <= t 的触发)。"""
    tr = B.trig
    m = tr.copy()
    m[1:] |= tr[:-1]
    m[2:] |= tr[:-2]
    return ~m


def pre_event_stat(B, A, w, stat='mean', mo=None):
    """τ 之前 w 个交易日 [τ-w, τ-1] 上的统计量, 在 τ 更新时重置, 无触发 -> NaN。"""
    mo = mo or minobs(w)
    T, N = A.shape
    if stat == 'mean':
        pre = rmean(A, w, mo)
    elif stat == 'cv':
        mu = rmean(A, w, mo)
        sd = rstd(A, w, mo)
        with np.errstate(all='ignore'):
            pre = np.where(mu > 0, sd / mu, np.nan)
    else:
        raise ValueError(stat)
    pre = lag(pre, 1)                                      # 截至 τ-1
    tau = B.tau()
    out = np.full((T, N), np.nan)
    ok = tau >= 0
    ti = np.where(ok, tau, 0)
    vals = pre[ti, np.arange(N)[None, :].repeat(T, 0)]
    out[ok] = vals[ok]
    return out


def since_tau_mean(B, A):
    """mean_{τ..t}(A), 只在 τ 已知时。"""
    T, N = A.shape
    tau = B.tau()
    cs = np.nancumsum(np.where(np.isfinite(A), A, 0.0), axis=0)
    cn = np.cumsum(np.isfinite(A), axis=0).astype(float)
    ti = np.where(tau >= 0, tau, 0)
    cols = np.arange(N)[None, :].repeat(T, 0)
    s_prev = np.where(ti > 0, cs[np.maximum(ti - 1, 0), cols], 0.0)
    n_prev = np.where(ti > 0, cn[np.maximum(ti - 1, 0), cols], 0.0)
    with np.errstate(all='ignore'):
        m = (cs - s_prev) / (cn - n_prev)
    return np.where((tau >= 0) & ((cn - n_prev) > 0), m, np.nan)


def _peak_x(B):
    if '_peakx' not in B.__dict__:
        B.__dict__['_peakx'] = since_tau_max_and_age(B, B.x)
    return B.__dict__['_peakx']


def since_tau_max_and_age(B, A):
    """[τ, t] 内已观察到的峰值与峰距今天数 (峰取最近一次达到)。逐列循环 (T_w x N 小)。"""
    T, N = A.shape
    tau = B.tau()
    peak = np.full((T, N), np.nan)
    age = np.full((T, N), np.nan)
    for j in range(N):
        cur_tau, pk, pk_t = -1, np.nan, -1
        a = A[:, j]
        tj = tau[:, j]
        for t in range(T):
            if tj[t] < 0:
                continue
            if tj[t] != cur_tau:
                cur_tau, pk, pk_t = tj[t], np.nan, -1
                for s in range(cur_tau, t):                 # 新 τ 到 t 之间补扫
                    if np.isfinite(a[s]) and (not np.isfinite(pk) or a[s] >= pk):
                        pk, pk_t = a[s], s
            if np.isfinite(a[t]) and (not np.isfinite(pk) or a[t] >= pk):
                pk, pk_t = a[t], t
            if np.isfinite(pk):
                peak[t, j] = pk
                age[t, j] = t - pk_t
    return peak, age


# ============================================================
# 3. 同业 (LOO) 工具 —— 全市场列, 形成日 PIT 行业
# ============================================================
def peer_loo_mean(B, V_mkt, min_peers=3):
    """每日每行业: (组和 - 自身)/(组有效数 - 1), 组内其余有效数 < min_peers -> NaN。返回全市场 (T_w, Nm)。"""
    T, Nm = V_mkt.shape
    out = np.full((T, Nm), np.nan)
    cnt = np.full((T, Nm), np.nan)
    ind = B.ind_mkt
    for t in range(T):
        ic = ind[t]
        v = np.isfinite(V_mkt[t]) & (ic >= 0)
        if v.sum() < min_peers + 1:
            continue
        G = ic.max() + 1
        s = np.bincount(ic[v], weights=V_mkt[t][v], minlength=G)
        n = np.bincount(ic[v], minlength=G).astype(float)
        known = ic >= 0
        own = np.where(v, V_mkt[t], 0.0)
        gs = np.where(known, s[np.where(known, ic, 0)], np.nan)
        gn = np.where(known, n[np.where(known, ic, 0)], np.nan)
        loo_n = gn - v.astype(float)
        with np.errstate(all='ignore'):
            out[t] = np.where(loo_n >= min_peers, (gs - own) / loo_n, np.nan)
        cnt[t] = loo_n
    return out, cnt


def _loo_q_sorted(y, rank_i, q):
    """y: 升序 n 个值; 对每个被剔位置 rank_i (int 数组, -1 = 自身不在 y 中) 求剩余值的
       线性插值分位 (numpy 默认 'linear')。向量化: 剩余序列下标 k -> 原下标 k + (k >= rank_i)。"""
    n = len(y)
    m = np.where(rank_i >= 0, n - 1, n).astype(float)
    pos = q * (m - 1)
    lo = np.floor(pos).astype(int)
    hi = np.ceil(pos).astype(int)
    fr = pos - lo
    lo2 = lo + ((rank_i >= 0) & (lo >= rank_i))
    hi2 = hi + ((rank_i >= 0) & (hi >= rank_i))
    return y[lo2] * (1 - fr) + y[hi2] * fr


def peer_loo_quantiles(B, V_mkt, qs=(0.25, 0.5, 0.75), min_peers=3, pos_frac=False):
    """LOO 分位 (逐日逐行业排序后剔自身, 线性插值同 np.quantile)。返回 dict q -> (T_w, Nm),
       另可返回 LOO 正值占比。组内剩余有效数 < min_peers -> NaN。"""
    T, Nm = V_mkt.shape
    outs = {q: np.full((T, Nm), np.nan) for q in qs}
    pf = np.full((T, Nm), np.nan) if pos_frac else None
    ind = B.ind_mkt
    for t in range(T):
        ic = ind[t]
        vt = V_mkt[t]
        known = ic >= 0
        v = np.isfinite(vt) & known
        if v.sum() < min_peers + 1:
            continue
        order = np.argsort(ic[known], kind='stable')
        kidx = np.where(known)[0][order]
        kcodes = ic[kidx]
        bounds = np.flatnonzero(np.diff(kcodes)) + 1
        for grp in np.split(kidx, bounds):
            gv = grp[np.isfinite(vt[grp])]
            if len(gv) < min_peers:
                continue
            o2 = np.argsort(vt[gv], kind='stable')
            ys = vt[gv][o2]
            rank_of = {int(i): r for r, i in enumerate(gv[o2])}
            rank_i = np.array([rank_of.get(int(i), -1) for i in grp])
            remain = np.where(rank_i >= 0, len(ys) - 1, len(ys))
            okm = remain >= min_peers
            if not okm.any():
                continue
            for q in qs:
                val = _loo_q_sorted(ys, np.where(okm, rank_i, -1), q)
                outs[q][t, grp[okm]] = val[okm]
            if pos_frac:
                npos = float((ys > 0).sum())
                own_pos = np.where(rank_i >= 0, (vt[grp] > 0).astype(float), 0.0)
                with np.errstate(all='ignore'):
                    f = (npos - own_pos) / remain
                pf[t, grp[okm]] = f[okm]
    return outs, pf


# ============================================================
# 4. 目录 —— 每成员一条元数据 + 计算函数
# ============================================================
CATALOG = []


def reg(member_id, axis, family, estimand, fn, w=None, policy='OBS', source_class='RESEARCH',
        unit='', source_ref='', raw_fields=(), event_clock='none', direction='high_bad',
        rep=False, note='', legacy_key=None, legacy_tol=None, **kw):
    CATALOG.append(dict(member_id=member_id, axis_id=axis, family_id=family,
                        estimand_id=estimand, fn=fn, window=w,
                        min_obs=(minobs(w) if w else None), policy=policy,
                        source_class=source_class, unit=unit, source_ref=source_ref,
                        raw_fields='/'.join(raw_fields), event_clock=event_clock,
                        direction_default=direction, representative=rep, note=note,
                        legacy_key=legacy_key, legacy_tol=legacy_tol, **kw))


def catalog_df():
    rows = [{k: v for k, v in m.items() if k != 'fn'} for m in CATALOG]
    return pd.DataFrame(rows)


def protected_ids():
    return [m['member_id'] for m in CATALOG if m['source_class'] != 'LEGACY']


# ---------------------------------------------------------------- 计算函数工厂
def _cv(A, w):
    mu = rmean(A, w)
    sd = rstd(A, w)
    with np.errstate(all='ignore'):
        return np.where(mu > 0, sd / mu, np.nan)


def _feat(key):
    """LEGACY: 直接取段内源特征 (源函数原样输出), 映射到预热网格的段内行。"""
    def f(B):
        v = B.S.feats[key].reindex(index=B.dates_w, columns=B.own_cols).astype(float).values
        return v
    return f


def _var_window(Z, w):
    """样本方差 (ddof=1) 在有效点上。"""
    return rvar(Z, w)


def _range_policy(B, A, policy):
    """把基于极差的逐日量按一字板政策处理。"""
    if policy == 'OBS':
        return A
    if policy == 'LIMIT_SENS':
        return np.where(B.touch, np.nan, A)
    if policy == 'LEGACY_PARK_NAN':
        return np.where(B.Hh > B.L, A, np.nan)
    raise ValueError(policy)


def _daily_park(B):
    return (B.h - B.l) ** 2 / (4 * LN2)


def _daily_gk(B):
    return 0.5 * (B.h - B.l) ** 2 - (2 * LN2 - 1) * B.c ** 2


def _daily_rs(B):
    return B.h * (B.h - B.c) + B.l * (B.l - B.c)


def _daily_mj(B):
    c = B.c
    cs = np.abs(c)
    hs = np.where(c >= 0, B.h, -B.l)
    ls = np.where(c >= 0, B.l, -B.h)
    q1 = 2 * ((hs - cs) ** 2 + ls ** 2)
    q2 = cs ** 2
    q3 = 2 * (hs - cs - ls) * cs
    q4 = -(hs - cs) * ls / MJ_Q4DEN
    return MJ[0] * q1 + MJ[1] * q2 + MJ[2] * q3 + MJ[3] * q4


def _yz(B, w, policy):
    """YZ = var(o) + k var(c) + (1-k) RS, 同一完整观测集 (政策剔除的日子整日剔), n = 实际完整数。"""
    ok = np.isfinite(B.o) & np.isfinite(B.c) & np.isfinite(B.h) & np.isfinite(B.l)
    if policy == 'LIMIT_SENS':
        ok &= ~B.touch
    o = np.where(ok, B.o, np.nan)
    c = np.where(ok, B.c, np.nan)
    rs = np.where(ok, _daily_rs(B), np.nan)
    n = rcount(o, w)
    vo = rvar(o, w)
    vc = rvar(c, w)
    mrs = rmean(rs, w)
    with np.errstate(all='ignore'):
        k = 0.34 / (1.34 + (n + 1) / (n - 1))
        y = vo + k * vc + (1 - k) * mrs
    return np.where(n > 1, y, np.nan)


def _event_level(B, A, pre_w=20):
    num = since_tau_mean(B, A)
    den = pre_event_stat(B, A, pre_w, 'mean')
    with np.errstate(all='ignore'):
        return np.where(den > 0, num / den, np.nan)


# ============================================================
# T 轴 (x = 换手率比例)
# ============================================================
def _build_T():
    X = lambda B: B.x
    reg('T_mean5', 'T', 'level', 'activity_level', lambda B: rmean(B.x, 5), 5, unit='ratio',
        raw_fields=('turnover_rate',))
    reg('T_mean20', 'T', 'level', 'activity_level', lambda B: rmean(B.x, 20), 20, unit='ratio',
        raw_fields=('turnover_rate',), rep=True)
    reg('T_mean60', 'T', 'level', 'activity_level', lambda B: rmean(B.x, 60), 60, unit='ratio',
        raw_fields=('turnover_rate',), note='std60 = mean60 x CV60 的水平分量')
    reg('T_med5', 'T', 'level', 'activity_level', lambda B: rmed(B.x, 5), 5, unit='ratio')
    reg('T_med20', 'T', 'level', 'activity_level', lambda B: rmed(B.x, 20), 20, unit='ratio')

    def r_5_20(B):
        with np.errstate(all='ignore'):
            return rmean(B.x, 5) / rmean(B.x, 20)

    def r_20_120(B):
        with np.errstate(all='ignore'):
            return rmean(B.x, 20) / rmean(B.x, 120)
    reg('T_r5_20', 'T', 'level', 'activity_level_ratio', r_5_20, 20, unit='ratio_of_means')
    reg('T_r20_120', 'T', 'level', 'activity_level_ratio', r_20_120, 120,
        unit='ratio_of_means', note='源 abn 的研究版 (有效日掩码, 0.7w 规则)')
    reg('T_abn_LEGACY', 'T', 'level', 'activity_level_ratio',
        lambda B: -(_feat_abn(B)), 120, source_class='LEGACY', unit='ratio_of_means',
        source_ref='pool_screening_v2.compute_abnormal_turnover (源返回 -abn; 此处取负还原)',
        legacy_key='__abn__')
    for w in (20, 60):
        reg('T_cv%d' % w, 'T', 'relative_scale', 'activity_instability',
            (lambda w: lambda B: _cv(B.x, w))(w), w, unit='dimensionless', rep=(w == 20))

        def logstd(B, w=w):
            lx = np.where(B.x > 0, np.log(np.where(B.x > 0, B.x, 1.0)), np.nan)
            return rstd(lx, w)
        reg('T_logstd%d' % w, 'T', 'relative_scale', 'activity_instability', logstd, w,
            unit='log', note='x>0 才进窗')

        def madrel(B, w=w):
            m = rmed(B.x, w)
            with np.errstate(all='ignore'):
                return np.where(m > 0, rmad_same_center(B.x, w) / m, np.nan)
        reg('T_madrel%d' % w, 'T', 'relative_scale', 'activity_instability', madrel, w,
            unit='dimensionless', rep=(w == 20), note='MAD 中心 = 同一窗口中位数 (W10)')

        def iqrrel(B, w=w):
            m = rmed(B.x, w)
            with np.errstate(all='ignore'):
                return np.where(m > 0, (rquant(B.x, w, 0.75) - rquant(B.x, w, 0.25)) / m, np.nan)
        reg('T_iqrrel%d' % w, 'T', 'relative_scale', 'activity_instability', iqrrel, w,
            unit='dimensionless')
        reg('T_std%d' % w, 'T', 'absolute_scale', 'activity_dispersion',
            (lambda w: lambda B: rstd(B.x, w))(w), w, unit='ratio')
        reg('T_mad%d' % w, 'T', 'absolute_scale', 'activity_dispersion',
            (lambda w: lambda B: rmad_same_center(B.x, w))(w), w, unit='ratio')
        reg('T_iqr%d' % w, 'T', 'absolute_scale', 'activity_dispersion',
            (lambda w: lambda B: rquant(B.x, w, 0.75) - rquant(B.x, w, 0.25))(w), w, unit='ratio')

        def trend(B, w=w):
            b, rs, mu = rtrend(B.x, w)
            with np.errstate(all='ignore'):
                return np.where(mu > 0, b / mu, np.nan)

        def resid(B, w=w):
            b, rs, mu = rtrend(B.x, w)
            with np.errstate(all='ignore'):
                return np.where(mu > 0, rs / mu, np.nan)
        reg('T_trend%d' % w, 'T', 'trend', 'activity_trend', trend, w, unit='per_day_rel')
        reg('T_resid%d' % w, 'T', 'trend', 'activity_instability_detrended', resid, w,
            unit='dimensionless', rep=(w == 20), note='同一窗口一次回归 (W10)')
        reg('T_ewcv%d' % w, 'T', 'weighted_scale', 'activity_instability',
            (lambda w: lambda B: rewcv(B.x, w)[1])(w), w, unit='dimensionless',
            note='有限窗 p∝2^{-age/(w/4)}')
        reg('T_ewmean%d' % w, 'T', 'weighted_scale', 'activity_level',
            (lambda w: lambda B: rewcv(B.x, w)[0])(w), w, unit='ratio')

        def cvmask(B, w=w):
            xm = np.where(causal_mask_nontrigger(B), B.x, np.nan)
            return _cv(xm, w)
        reg('T_cvmask%d' % w, 'T', 'event_strip', 'activity_instability_ex_event', cvmask, w,
            unit='dimensionless', event_clock='causal_trigger_s_s1_s2')
        reg('T_cvpre%d' % w, 'T', 'event_strip', 'activity_instability_pre_event',
            (lambda w: lambda B: pre_event_stat(B, B.x, w, 'cv'))(w), w, unit='dimensionless',
            event_clock='pre_tau_frozen', rep=(w == 20))
        reg('T_meanpre%d' % w, 'T', 'event_strip', 'activity_level_pre_event',
            (lambda w: lambda B: pre_event_stat(B, B.x, w, 'mean'))(w), w, unit='ratio',
            event_clock='pre_tau_frozen')

        def logrange(B, w=w):
            mx = rmax(B.x, w)
            mn = rmin(np.where(B.x > 0, B.x, np.nan), w, mo=1)
            with np.errstate(all='ignore'):
                return np.where((mx > 0) & (mn > 0), np.log(mx / mn), np.nan)
        reg('T_logrange%d' % w, 'T', 'extreme', 'activity_range', logrange, w, unit='log')

        def zero(B, w=w):
            z = np.where(B.open & np.isfinite(B.x), (B.x == 0).astype(float), np.nan)
            return rsum(z, w)
        reg('T_zero%d' % w, 'T', 'extreme', 'zero_activity_count', zero, w, unit='count',
            note='诊断: 零换手开市日数, 不偷偷抬分母')
    reg('T_evlevel', 'T', 'event_strip', 'event_activity_level',
        lambda B: _event_level(B, B.x, 20), 20, unit='ratio', event_clock='tau_to_t_over_pre20',
        note='也作 A 轴事件恢复成员 (同一测量两种用途身份)')

    def slope5(B):
        b, _, _ = rtrend(B.x, 5, mo=4)
        with np.errstate(all='ignore'):
            return b / rmean(B.x, 20)
    reg('T_slope5', 'T', 'extreme', 'activity_trend_short', slope5, 5, unit='per_day_rel')
    reg('T_std60_LEGACY', 'T', 'absolute_scale', 'activity_dispersion',
        _feat('turnover_volatility_60d'), 60, source_class='LEGACY', unit='ratio',
        source_ref='features_daily.py:605 turn.rolling(60, min_periods=30).std()',
        legacy_key='turnover_volatility_60d')
    reg('T_mean5_LEGACY', 'T', 'level', 'activity_level', _feat('turnover_5d'), 5,
        source_class='LEGACY', unit='ratio', legacy_key='turnover_5d',
        source_ref='features_daily turnover_5d')
    reg('T_TCV20_E6H', 'T', 'relative_scale', 'activity_instability',
        lambda B: _e6h_derived(B, 'TCV_20'), 20, source_class='LEGACY', unit='dimensionless',
        legacy_key='E6H:TCV_20', source_ref='e6h_core.tcv (E6h 研究键桥)')


def _feat_abn(B):
    v = compute_abnormal_turnover(
        B.S.data['turnover_rate'].reindex(index=B.S.pool0.index, columns=B.own_cols))
    return v.reindex(index=B.dates_w).values


def _e6h_derived(B, key):
    sp = H.specH(key)
    v = H.build_raw_h(B.S, sp)
    return v.reindex(index=B.dates_w, columns=B.own_cols).astype(float).values


# ============================================================
# K 轴
# ============================================================
def _build_K():
    reg('K0_LEGACY', 'K', 'source_bridge', 'price_response_ratio', _feat('conditional_turnover'),
        1, source_class='LEGACY', unit='ratio/abs_logret', legacy_key='conditional_turnover',
        source_ref='features_daily.py:353', rep=True)
    for w, est in ((3, 'MA'), (5, 'MA'), (5, 'ROS'), (20, 'ROS')):
        mid = 'K_%s%d_E6F' % (est, w)
        reg(mid, 'K', 'source_bridge', 'price_response_ratio',
            (lambda w, est: lambda B: _e6f_raw(B, F.spec('K', w, est=est, eps=EPS)))(w, est), w,
            source_class='LEGACY', unit='ratio/abs_logret', legacy_key='E6F:K_%s%d' % (est, w),
            source_ref='e6f_core.build_raw spec(K,%d,%s)' % (w, est), rep=(w == 20))
    for w in (5, 20):
        reg('K_agg%d' % w, 'K', 'aggregation_bridge', 'price_response_ratio',
            (lambda w: lambda B: _div(rmean(B.x, w), rmean(B.d, w) + EPS))(w), w,
            unit='ratio/abs_logret', note='先均再比 (W03 聚合顺序)')
    reg('K_log', 'K', 'log_repr', 'price_response_ratio',
        lambda B: np.where(B.x > 0, np.log(np.where(B.x > 0, B.x, 1.0) / (B.d + EPS)), np.nan),
        1, unit='log', rep=True, note='原排序与 K0 同; 中性化后可不同 (W04)')
    reg('K_floor', 'K', 'denominator_guard', 'price_response_ratio',
        lambda B: _div(B.x, np.maximum(B.d, EPS)), 1, unit='ratio/abs_logret')

    def vfloor(B):
        ls = lag(rstd(B.r, 20), 1)
        return np.where(np.isfinite(ls), _div(B.x, np.maximum(B.d, 0.1 * ls)), np.nan)
    reg('K_vfloor', 'K', 'denominator_guard', 'price_response_ratio', vfloor, 20,
        unit='ratio/abs_logret', note='分母下限 = 0.1 x 滞后 20 日收益 std; 缺则 NaN')
    reg('K_comp_x', 'K', 'component', 'activity_numerator', lambda B: B.x, 1, unit='ratio')
    reg('K_comp_d', 'K', 'component', 'abs_return_denominator', lambda B: B.d, 1, unit='abs_logret')
    reg('K_comp_sign', 'K', 'component', 'return_sign', lambda B: np.sign(B.r), 1, unit='sign')
    reg('K_comp_dz', 'K', 'component', 'abs_return_standardized',
        lambda B: _div(B.d, lag(rstd(B.r, 20), 1)), 20, unit='z')
    reg('K_res_lin', 'K', 'cross_sectional_residual', 'conditional_activity',
        lambda B: _xs_resid(B, 'lin'), 1, unit='ratio_resid',
        note='当日 pool0 内 x ~ 1 + d + logmcap 残差')
    reg('K_res_log', 'K', 'cross_sectional_residual', 'conditional_activity',
        lambda B: _xs_resid(B, 'log'), 1, unit='log_resid', rep=True,
        note='log x ~ 1 + log(d+eps) + logmcap 残差')
    reg('K_res_base', 'K', 'cross_sectional_residual', 'size_adjusted_activity',
        lambda B: _xs_resid(B, 'base'), 1, unit='ratio_resid', note='基准: x ~ 1 + logmcap')
    for w in (5, 20):
        reg('K_dxr%d' % w, 'K', 'turnover_response', 'abs_return_per_activity',
            (lambda w: lambda B: rmean(_div(B.d, np.where(B.x > 0, B.x, np.nan)), w))(w), w,
            unit='abs_logret/ratio')
        reg('K_sdsx%d' % w, 'K', 'turnover_response', 'abs_return_per_activity',
            (lambda w: lambda B: _div(rsum(B.d, w), rsum(np.where(np.isfinite(B.d), B.x, np.nan),
                                                        w)))(w), w, unit='abs_logret/ratio')
        reg('K_amt%d' % w, 'K', 'amount_response', 'abs_return_per_money',
            (lambda w: lambda B: rmean(_div(B.d, np.where(B.amt > 0, B.amt / 1e6, np.nan)),
                                       w))(w), w, unit='abs_logret_per_1e6_yuan')
        reg('K_samt%d' % w, 'K', 'amount_response', 'abs_return_per_money',
            (lambda w: lambda B: _div(rsum(B.d, w),
                                      rsum(np.where(np.isfinite(B.d), B.amt / 1e6, np.nan),
                                           w)))(w), w, unit='abs_logret_per_1e6_yuan')
    for w in (20, 60):
        reg('K_slope%d' % w, 'K', 'turnover_response', 'abs_return_activity_slope',
            (lambda w: lambda B: _div(rcov(B.d, B.x, w), rvar(np.where(np.isfinite(B.d), B.x,
                                                                         np.nan), w)))(w), w,
            unit='abs_logret/ratio', note='OLS 斜率 d~x; 不叫 Kyle λ (W05)')
    reg('K_inv', 'K', 'pointwise_inverse_bridge', 'price_response_inverse',
        lambda B: _div(B.d + EPS, np.where(B.x > 0, B.x, np.nan)), 1, unit='abs_logret/ratio',
        note='正值上与 K0 严格反序; 只作身份/方向测试')
    # ---- 摩擦子族 ----
    for w in (20, 60):
        def roll_q(B, w=w):
            la = np.where(np.isfinite(B.Ca) & (B.Ca > 0), np.log(np.where(B.Ca > 0, B.Ca, 1.0)),
                          np.nan)
            dl = la - lag(la, 1)
            return -rcov(dl, lag(dl, 1), w)
        reg('K_roll%d' % w, 'K', 'friction_roll', 'spread_proxy_roll_q', roll_q, w,
            unit='logret^2', note='q = -cov(ΔlogC_t, ΔlogC_{t-1}), 复权 log 价')
        reg('K_rollsp%d' % w, 'K', 'friction_roll', 'spread_proxy_roll',
            (lambda f: lambda B: 2 * np.sqrt(np.maximum(f(B), 0.0)))(roll_q), w,
            unit='proportional_spread')

        def cs_daily(B):
            h1, l1 = lag(B.Ha, 1), lag(B.La, 1)
            with np.errstate(all='ignore'):
                beta = np.log(h1 / l1) ** 2 + np.log(B.Ha / B.La) ** 2
                gam = np.log(np.maximum(h1, B.Ha) / np.minimum(l1, B.La)) ** 2
                k = 3 - 2 * math.sqrt(2)
                alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / k - np.sqrt(gam / k)
                return 2 * np.tanh(alpha / 2)
        reg('K_cs%d' % w, 'K', 'friction_cs', 'spread_cs_clip_then_mean',
            (lambda w: lambda B: rmean(np.maximum(cs_daily(B), 0.0), w))(w), w,
            unit='proportional_spread', note='主值 mean(max(s,0)); 未做开盘缺口修正版')
        reg('K_csm%d' % w, 'K', 'friction_cs', 'spread_cs_mean_then_clip',
            (lambda w: lambda B: np.maximum(rmean(cs_daily(B), w), 0.0))(w), w,
            unit='proportional_spread')
        reg('K_css%d' % w, 'K', 'friction_cs', 'spread_cs_signed_mean',
            (lambda w: lambda B: rmean(cs_daily(B), w))(w), w, unit='proportional_spread',
            note='signed 诊断量')

        def ar(B, w=w):
            lc = np.log(np.where(B.Ca > 0, B.Ca, np.nan))
            eta = (np.log(np.where(B.Ha > 0, B.Ha, np.nan)) +
                   np.log(np.where(B.La > 0, B.La, np.nan))) / 2
            lc1, eta1 = lag(lc, 1), lag(eta, 1)
            q = 4 * (lc1 - eta1) * (lc1 - eta)            # t 收盘已知
            return np.sqrt(np.maximum(rmean(q, w), 0.0))
        reg('K_ar%d' % w, 'K', 'friction_ar', 'spread_ar', ar, w, unit='proportional_spread',
            rep=(w == 20), note='q_t 在 t 收盘已知; 先均再开根 (W 系)')
        reg('K_edge%d' % w, 'K', 'friction_edge', 'spread_edge_rms',
            (lambda w: lambda B: _edge(B, w, sign=False))(w), w, unit='proportional_spread',
            rep=(w == 20), source_ref='e6i_vendor.bidask.edge_rolling @1caba55d')
        reg('K_edges%d' % w, 'K', 'friction_edge', 'spread_edge_signed',
            (lambda w: lambda B: _edge(B, w, sign=True))(w), w, unit='proportional_spread',
            note='signed 内部量')

        def zret(B, w=w):
            z = np.where(np.isfinite(B.r), (B.r == 0).astype(float), np.nan)
            return rmean(z, w)
        reg('K_zero%d' % w, 'K', 'friction_zero', 'zero_return_fraction', zret, w,
            unit='fraction', note='不称 LOT')

        def notrade(B, w=w):
            z = (~B.open).astype(float)
            return rmean(z, w, mo=1)
        reg('K_notrade%d' % w, 'K', 'friction_zero', 'no_trade_fraction', notrade, w,
            unit='fraction', note='诊断: 停牌/无交易占比')
    reg('K_amihud_LEGACY', 'K', 'source_bridge', 'illiquidity', _feat('amihud_daily'), 1,
        source_class='LEGACY', legacy_key='amihud_daily', source_ref='features_daily amihud_daily')

    def rar(B):
        base = lag(rmean(B.x, 20), 1)
        return _div(_div(B.x, base), B.d + EPS)

    def rarpre(B):
        base = pre_event_stat(B, B.x, 20, 'mean')
        return _div(_div(B.x, base), B.d + EPS)
    reg('K_rar20', 'K', 'ra_derived', 'relative_activity_response', rar, 20,
        unit='rel_activity/abs_logret', note='plan §5.7 RA 派生, 属 K 决策')
    reg('K_rarpre', 'K', 'ra_derived', 'relative_activity_response', rarpre, 20,
        unit='rel_activity/abs_logret', event_clock='pre_tau_frozen')


def _div(a, b):
    with np.errstate(all='ignore'):
        out = a / b
    return np.where(np.isfinite(out), out, np.nan)


def _e6f_raw(B, sp):
    v = F.build_raw(B.S.wdata_i, sp)
    return v.reindex(index=B.dates_w, columns=B.own_cols).astype(float).values


def _xs_resid(B, kind):
    """当日 pool0 内截面残差 (段内行; 预热行 NaN —— 截面量不需要历史)。"""
    S = B.S
    T_w, N = B.x.shape
    out = np.full((T_w, N), np.nan)
    lm = S.log_mcap.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]
    rows = B.seg_rows
    xs = B.x[rows]
    ds = B.d[rows]
    if kind == 'lin':
        y, X = xs, [ds, lm]
    elif kind == 'log':
        y = np.where(xs > 0, np.log(np.where(xs > 0, xs, 1.0)), np.nan)
        X = [np.log(ds + EPS), lm]
    else:
        y, X = xs, [lm]
    res, _ = ols_resid_xs(y, X, S.p0c)
    out[rows] = res
    return out


def _edge(B, w, sign):
    """作者 edge_rolling (vendor @1caba55d) 逐股, 复权 OHLC。作者式: 非负值 = |signed|,
       所以 signed 只算一次, 非负版取绝对值 (与 sign=False 调用逐位相同)。"""
    key = '_edge%d' % w
    if key not in B.__dict__:
        from e6i_vendor.bidask import edge_rolling
        import warnings
        T_w, N = B.Oa.shape
        out = np.full((T_w, N), np.nan)
        mo = minobs(w)
        for j in range(N):
            df = pd.DataFrame({'open': B.Oa[:, j], 'high': B.Ha[:, j], 'low': B.La[:, j],
                               'close': B.Ca[:, j]})
            if df['close'].notna().sum() < mo:
                continue
            with np.errstate(all='ignore'), warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                s = edge_rolling(df, window=w, sign=True, min_periods=mo)
            out[:, j] = s.values
        B.__dict__[key] = out
    sg = B.__dict__[key]
    return sg if sign else np.abs(sg)


# ============================================================
# V 轴 (方差尺度; sqrt 版只作表示对照, 不另立经济描述符)
# ============================================================
def _build_V():
    for w in (10, 20):
        reg('V_cc%d' % w, 'V', 'close_close', 'total_variance_cc',
            (lambda w: lambda B: rvar(B.r, w))(w), w, unit='logret^2')
        for pol in ('OBS', 'LIMIT_SENS'):
            tg = 'obs' if pol == 'OBS' else 'ls'
            reg('V_park%d_%s' % (w, tg), 'V', 'range', 'intraday_range_variance',
                (lambda w, pol: lambda B: rmean(_range_policy(B, _daily_park(B), pol), w))(w, pol),
                w, policy=pol, unit='logret^2', rep=(w == 20 and pol == 'OBS'))
            reg('V_gk%d_%s' % (w, tg), 'V', 'ohlc', 'intraday_variance_gk_simple',
                (lambda w, pol: lambda B: rmean(_range_policy(B, _daily_gk(B), pol), w))(w, pol),
                w, policy=pol, unit='logret^2')
            reg('V_rs%d_%s' % (w, tg), 'V', 'ohlc', 'intraday_variance_drift_robust',
                (lambda w, pol: lambda B: rmean(_range_policy(B, _daily_rs(B), pol), w))(w, pol),
                w, policy=pol, unit='logret^2', rep=(w == 20 and pol == 'OBS'))
            reg('V_yz%d_%s' % (w, tg), 'V', 'ohlc', 'total_variance_yz',
                (lambda w, pol: lambda B: _yz(B, w, pol))(w, pol), w, policy=pol,
                unit='logret^2', rep=(w == 20 and pol == 'OBS'))
            reg('V_mj%d_%s' % (w, tg), 'V', 'ohlc', 'intraday_variance_meilijson',
                (lambda w, pol: lambda B: rmean(_range_policy(B, _daily_mj(B), pol), w))(w, pol),
                w, policy=pol, unit='logret^2', note='零漂移基准; 系数待与 arXiv 0807.3492 复核')
        reg('V_on%d' % w, 'V', 'overnight', 'overnight_variance',
            (lambda w: lambda B: rvar(B.o, w))(w), w, unit='logret^2', rep=(w == 20))
        reg('V_oc%d' % w, 'V', 'open_close', 'intraday_oc_variance',
            (lambda w: lambda B: rvar(B.c, w))(w), w, unit='logret^2')
        reg('V_semid%d' % w, 'V', 'semivariance', 'downside_second_moment',
            (lambda w: lambda B: rmean(np.minimum(B.r, 0.0) ** 2, w))(w), w, unit='logret^2',
            rep=(w == 20))
        reg('V_semiu%d' % w, 'V', 'semivariance', 'upside_second_moment',
            (lambda w: lambda B: rmean(np.maximum(B.r, 0.0) ** 2, w))(w), w, unit='logret^2')
        reg('V_max%d' % w, 'V', 'tail', 'max_positive_return',
            (lambda w: lambda B: rmax(B.r, w))(w), w, unit='logret')
        reg('V_mmin%d' % w, 'V', 'tail', 'max_negative_return',
            (lambda w: lambda B: -rmin(B.r, w))(w), w, unit='logret')
        reg('V_maxabs%d' % w, 'V', 'tail', 'max_abs_return',
            (lambda w: lambda B: rmax(np.abs(B.r), w))(w), w, unit='logret',
            note='不能冒名 MAX (R25)')
        reg('V_top3pos%d' % w, 'V', 'tail', 'top3_positive_mean',
            (lambda w: lambda B: rtop3pos(B.r, w))(w), w, unit='logret',
            note='mean(top3 of max(r,0)); 正收益不足 3 个以 0 补')
        reg('V_idio%d' % w, 'V', 'idiosyncratic', 'residual_variance',
            (lambda w: lambda B: rvar(_innovations(B), w))(w), w, unit='logret^2',
            note='§4.4 逐日滞后预测残差的样本方差')
    for base_id, fn in (('cc20', lambda B: rvar(B.r, 20)),
                        ('rs20', lambda B: rmean(_daily_rs(B), 20)),
                        ('yz20', lambda B: _yz(B, 20, 'OBS')),
                        ('park20', lambda B: rmean(_daily_park(B), 20))):
        reg('V_relrisk_%s' % base_id, 'V', 'relative_risk', 'risk_vs_own_history',
            (lambda fn: lambda B: rpct_own_history(fn(B), 60))(fn), 60, unit='percentile',
            note='先算原测量再逐股历史排名')
    reg('V_ratio_cc', 'V', 'relative_risk', 'risk_short_vs_long',
        lambda B: _div(rvar(B.r, 10), rvar(B.r, 20)), 20, unit='ratio')
    reg('V_ratio_rs', 'V', 'relative_risk', 'risk_short_vs_long',
        lambda B: _div(rmean(_daily_rs(B), 10), rmean(_daily_rs(B), 20)), 20, unit='ratio')
    reg('V_cc20_LEGACY', 'V', 'source_bridge', 'total_vol_cc_annualized',
        _feat('realized_vol_20d'), 20, source_class='LEGACY', legacy_key='realized_vol_20d',
        source_ref='features_daily.py:205 log(C/LC).rolling(20,min 10).std()*sqrt(252) (不掩停牌)')
    reg('V_park20_LEGACY', 'V', 'source_bridge', 'intraday_range_vol', _park_legacy, 20,
        source_class='LEGACY', policy='LEGACY_PARK_NAN', legacy_key='__park__',
        source_ref='pool_screening_v2.compute_parkinson_vol (源返回 -vol; 取负还原)')
    reg('V_maxabs10_LEGACY', 'V', 'source_bridge', 'max_abs_return', _feat('max_abs_return_10d'),
        10, source_class='LEGACY', legacy_key='max_abs_return_10d')


def _park_legacy(B):
    S = B.S
    v = compute_parkinson_vol(S.data['high'], S.data['low'])
    return (-v).reindex(index=B.dates_w, columns=B.own_cols).astype(float).values


# ============================================================
# R 轴 (复权 log 价; 同业 LOO 用全市场)
# ============================================================
def _logP_own(B):
    return np.log(np.where(B.Ca > 0, B.Ca, np.nan))


def _Rw(B, w, s=0, mkt=False):
    """R(w,s)_t = log(P_{t-s}/P_{t-s-w}) = sum_{u=t-s-w+1..t-s} radj_u。
       radj 是相对上一个有效收盘的复权 log 收益, 所以停牌期间的价格变化在复牌日一次计入,
       行不压缩; 窗内有效日 < 0.7w -> NaN。"""
    rr = B.radj_mkt if mkt else B.radj
    z = np.where(np.isfinite(rr), rr, 0.0)
    cs = np.vstack([np.zeros((1, rr.shape[1])), np.cumsum(z, axis=0)])     # cs[k] = sum_{u<k}
    cn = np.vstack([np.zeros((1, rr.shape[1])), np.cumsum(np.isfinite(rr), axis=0)])
    T = rr.shape[0]
    out = np.full(rr.shape, np.nan)
    if T >= s + w:
        t = np.arange(s + w - 1, T)                  # 窗 [t-s-w+1, t-s] 全在网格内
        hi, lo = t - s + 1, t - s - w + 1
        tot = cs[hi] - cs[lo]
        na = cn[hi] - cn[lo]
        out[t] = np.where(na >= minobs(w), tot, np.nan)
    return out


def _innovations(B):
    """逐日滞后预测残差 (plan §4.4 残差时间合同):
       r_i,s = a + b_m r_m,s + b_g (r_g,s - r_m,s) + e; 系数用 [s-120, s-1] 拟合 (>=60 完整日),
       r_g = 同业 LOO 等权 (按每个历史日 s 的 PIT 行业), 当日 innovation 用前一日系数与当日实现值。"""
    key = '_innov'
    if key in B.__dict__:
        return B.__dict__[key]
    rg_mkt, _ = peer_loo_mean(B, B.radj_mkt)
    rg = rg_mkt[:, B.oc]
    rm = B.rm[:, None] * np.ones((1, rg.shape[1]))
    y = B.radj
    x1 = rm
    x2 = rg - rm
    ok = np.isfinite(y) & np.isfinite(x1) & np.isfinite(x2)
    Y, X1, X2 = (np.where(ok, v, 0.0) for v in (y, x1, x2))
    one = ok.astype(float)
    W = 120

    def rs(A):
        return lag(pd.DataFrame(A).rolling(W, min_periods=1).sum().values, 1)
    n, s1, s2, sy = rs(one), rs(X1), rs(X2), rs(Y)
    s11, s22, s12 = rs(X1 * X1), rs(X2 * X2), rs(X1 * X2)
    s1y, s2y = rs(X1 * Y), rs(X2 * Y)
    T, N = y.shape
    M = np.stack([np.stack([n, s1, s2], -1), np.stack([s1, s11, s12], -1),
                  np.stack([s2, s12, s22], -1)], -2)        # (T,N,3,3)
    v = np.stack([sy, s1y, s2y], -1)                        # (T,N,3)
    good = (n >= 60) & np.isfinite(M).all((-1, -2))
    coef = np.full((T, N, 3), np.nan)
    Mg = M[good]
    det = np.linalg.det(Mg)
    okd = np.abs(det) > 1e-18
    sol = np.full((len(Mg), 3), np.nan)
    if okd.any():
        sol[okd] = np.linalg.solve(Mg[okd], v[good][okd][..., None])[..., 0]
    coef[good] = sol
    pred = coef[..., 0] + coef[..., 1] * x1 + coef[..., 2] * x2
    inn = np.where(ok, y - pred, np.nan)
    B.__dict__[key] = inn
    return inn


def _build_R():
    for w in (5, 10, 20):
        for s in (0, 1):
            reg('R_%d_s%d' % (w, s), 'R', 'absolute', 'past_return',
                (lambda w, s: lambda B: _Rw(B, w, s))(w, s), w, unit='logret',
                rep=(w == 5 and s == 0))
    reg('R_skip3_10', 'R', 'absolute', 'past_return_skip3',
        lambda B: _Rw(B, 10, 3), 10, unit='logret', note='诊断端点 (proposal 提出, 单列)')
    reg('R_skip1_LEGACY', 'R', 'source_bridge', 'industry_relative_skip1',
        _skip1_legacy, 10, source_class='LEGACY', legacy_key='__skip1__',
        source_ref='pool_screening_v2.compute_reversal_skip1 (源返回 -x; 取负还原; 未复权简单收益)')
    reg('R_cr5_LEGACY', 'R', 'source_bridge', 'past_return', _feat('cum_return_5d'), 5,
        source_class='LEGACY', legacy_key='cum_return_5d')
    reg('R_cr20_LEGACY', 'R', 'source_bridge', 'past_return', _feat('cum_return_20d'), 20,
        source_class='LEGACY', legacy_key='cum_return_20d')
    for w in (5, 10, 20):
        reg('R_peer%d' % w, 'R', 'peer_relative', 'return_vs_industry_loo',
            (lambda w: lambda B: _peer_rel(B, w))(w), w, unit='logret', rep=(w == 20),
            note='同业 = 形成日 PIT 行业剔自身; 有效同行 <3 NaN')
        reg('R_prank%d' % w, 'R', 'peer_relative', 'return_rank_in_industry',
            (lambda w: lambda B: _peer_rank(B, w))(w), w, unit='percentile')
        reg('R_mkt%d' % w, 'R', 'market_relative', 'return_vs_clean_ew',
            (lambda w: lambda B: _Rw(B, w) - _mkt_cum(B, w))(w), w, unit='logret')
        reg('R_resid%d' % w, 'R', 'residual', 'residual_return_lagged_beta',
            (lambda w: lambda B: rsum(_innovations(B), w))(w), w, unit='logret', rep=(w == 20),
            note='预估计残差 (非同窗含截距残差和, W12)')
    for w in (5, 20):
        reg('R_peervol%d' % w, 'R', 'relative_scale', 'return_vs_industry_per_vol',
            (lambda w: lambda B: _div(_peer_rel(B, w), lag(rstd(B.radj, 20), 1)))(w), w,
            unit='z')
    reg('R_pos20', 'R', 'position', 'distance_to_high',
        lambda B: _logP_own(B) - rmax(_logP_own(B), 20), 20, unit='logret')
    reg('R_dhigh20', 'R', 'position', 'days_since_high', lambda B: _days_since_high(B, 20), 20,
        unit='days')
    reg('R_pos252', 'R', 'position', 'distance_to_long_high',
        lambda B: _logP_own(B) - rmax(_logP_own(B), 252, mo=120), 252, unit='logret',
        note='52 周高语义桥, 不是 George-Hwang 复现')
    for w in (5, 20):
        reg('R_posfrac%d' % w, 'R', 'path', 'positive_day_fraction',
            (lambda w: lambda B: rmean(np.where(np.isfinite(B.radj), (B.radj > 0).astype(float),
                                                np.nan), w))(w), w, unit='fraction')
        reg('R_eff%d' % w, 'R', 'path', 'path_efficiency',
            (lambda w: lambda B: _div(rsum(B.radj, w), rsum(np.abs(B.radj), w)))(w), w,
            unit='ratio', rep=(w == 20))
        reg('R_signdir%d' % w, 'R', 'path', 'sign_ratio_x_direction',
            (lambda w: lambda B: _signdir(B, w))(w), w, unit='fraction')
    reg('R_infodisc_LEGACY', 'R', 'source_bridge', 'information_discreteness',
        _feat('info_discreteness_20d'), 20, source_class='LEGACY',
        legacy_key='info_discreteness_20d')
    reg('R_dist20_LEGACY', 'R', 'source_bridge', 'distance_to_high',
        _feat('distance_from_high_20d'), 20, source_class='LEGACY',
        legacy_key='distance_from_high_20d')


def _skip1_legacy(B):
    S = B.S
    ind = S.data.get('industry_zx1', S.data.get('industry'))
    v = compute_reversal_skip1(S.data['close'], ind)
    return (-v).reindex(index=B.dates_w, columns=B.own_cols).astype(float).values


def _Rw_mkt(B, w):
    k = '_Rwm%d' % w
    if k not in B.__dict__:
        B.__dict__[k] = _Rw(B, w, 0, mkt=True)
    return B.__dict__[k]


def _peer_rel(B, w):
    Rm = _Rw_mkt(B, w)
    loo, _ = peer_loo_mean(B, Rm)
    return Rm[:, B.oc] - loo[:, B.oc]


def _peer_rank(B, w):
    Rm = _Rw_mkt(B, w)
    T, Nm = Rm.shape
    out = np.full((T, Nm), np.nan)
    ind = B.ind_mkt
    for t in range(T):
        v = np.isfinite(Rm[t]) & (ind[t] >= 0)
        if v.sum() < 4:
            continue
        s = pd.Series(Rm[t][v])
        g = pd.Series(ind[t][v])
        cnt = g.map(g.value_counts())
        rk = s.groupby(g.values).rank(pct=True)
        out[t, np.where(v)[0]] = np.where(cnt.values >= 4, rk.values, np.nan)
    return out[:, B.oc]


def _mkt_cum(B, w):
    rm = np.where(np.isfinite(B.rm), B.rm, 0.0)
    cs = np.cumsum(rm)
    out = np.full(len(rm), np.nan)
    out[w:] = cs[w:] - cs[:-w]
    return out[:, None] * np.ones((1, B.radj.shape[1]))


def _days_since_high(B, w):
    lp = _logP_own(B)

    def fn(sw):
        v = np.isfinite(sw)
        z = np.where(v, sw, -np.inf)
        # 最近一次达到最高: 反转窗口后 argmax
        rev = z[..., ::-1]
        am = np.argmax(rev, axis=-1)
        return np.where(v.sum(-1) >= minobs(w), am.astype(float), np.nan)
    return _chunked_windows(lp, w, fn)


def _signdir(B, w):
    rr = B.radj
    pos = rmean(np.where(np.isfinite(rr), (rr > 0).astype(float), np.nan), w)
    neg = rmean(np.where(np.isfinite(rr), (rr < 0).astype(float), np.nan), w)
    return (pos - neg) * np.sign(_Rw(B, w))


# ============================================================
# O 轴
# ============================================================
def _build_O():
    for w in (5, 20):
        reg('O_onmean%d' % w, 'O', 'direction', 'overnight_mean',
            (lambda w: lambda B: rmean(B.o, w))(w), w, unit='logret', rep=(w == 5))
        reg('O_ocmean%d' % w, 'O', 'direction', 'intraday_mean',
            (lambda w: lambda B: rmean(B.c, w))(w), w, unit='logret')
        reg('O_onpos%d' % w, 'O', 'direction', 'overnight_positive_fraction',
            (lambda w: lambda B: rmean(np.where(np.isfinite(B.o), (B.o > 0).astype(float),
                                                np.nan), w))(w), w, unit='fraction')
        if w == 5:
            reg('O_onvar5', 'O', 'energy', 'overnight_variance',
                lambda B: rvar(B.o, 5), 5, unit='logret^2')
            reg('O_ocvar5', 'O', 'energy', 'intraday_oc_variance',
                lambda B: rvar(B.c, 5), 5, unit='logret^2')
        reg('O_absshare%d' % w, 'O', 'share', 'overnight_abs_share',
            (lambda w: lambda B: _div(rsum(np.abs(B.o), w),
                                      rsum(np.abs(B.o), w) + rsum(np.abs(B.c), w)))(w), w,
            unit='fraction')
        reg('O_enshare%d' % w, 'O', 'share', 'overnight_energy_share',
            (lambda w: lambda B: _div(rsum(B.o ** 2, w), rsum(B.o ** 2, w) + rsum(B.c ** 2, w)))(w),
            w, unit='fraction', rep=(w == 20))
        reg('O_balance%d' % w, 'O', 'share', 'overnight_signed_balance',
            (lambda w: lambda B: _div(rsum(B.o, w), rsum(np.abs(B.o) + np.abs(B.c), w)))(w), w,
            unit='[-1,1]', rep=(w == 20))
        reg('O_follow%d' % w, 'O', 'path', 'overnight_intraday_comovement',
            (lambda w: lambda B: rmean(B.o * B.c, w))(w), w, unit='logret^2')
        reg('O_retreat%d' % w, 'O', 'path', 'intraday_retreat',
            (lambda w: lambda B: rmean(np.where(np.isfinite(B.o * B.c),
                                                (B.o * B.c < 0) * np.abs(B.c), np.nan), w))(w),
            w, unit='logret')
        reg('O_retreat_up%d' % w, 'O', 'path', 'intraday_retreat_after_up_gap',
            (lambda w: lambda B: rmean(np.where(np.isfinite(B.c) & (B.o > 0),
                                                (B.c < 0) * np.abs(B.c), np.nan), w, mo=1))(w),
            w, unit='logret', rep=(w == 20), note='只在 o>0 日取值, 窗内至少 1 个')
        reg('O_retreat_dn%d' % w, 'O', 'path', 'intraday_retreat_after_down_gap',
            (lambda w: lambda B: rmean(np.where(np.isfinite(B.c) & (B.o < 0),
                                                (B.c > 0) * np.abs(B.c), np.nan), w, mo=1))(w),
            w, unit='logret', note='只在 o<0 日取值')
    reg('O_o1', 'O', 'current', 'overnight_today', lambda B: B.o, 1, unit='logret')
    reg('O_c1', 'O', 'current', 'intraday_today', lambda B: B.c, 1, unit='logret')
    reg('O_o_pct60', 'O', 'current', 'overnight_today_vs_own_history',
        lambda B: rpct_own_history(B.o, 60), 60, unit='percentile')
    reg('O_c_pct60', 'O', 'current', 'intraday_today_vs_own_history',
        lambda B: rpct_own_history(B.c, 60), 60, unit='percentile')
    reg('O_jump5_E6H', 'O', 'source_bridge', 'overnight_energy_share', lambda B: _e6h_derived(B, 'JUMP_5'),
        5, source_class='LEGACY', legacy_key='E6H:JUMP_5')
    reg('O_jump20_E6H', 'O', 'source_bridge', 'overnight_energy_share',
        lambda B: _e6h_derived(B, 'JUMP_20'), 20, source_class='LEGACY', legacy_key='E6H:JUMP_20')
    reg('O_gapsurv_LEGACY', 'O', 'source_bridge', 'gap_survival', _feat('gap_survival_ratio'), 1,
        source_class='LEGACY', legacy_key='gap_survival_ratio')
    reg('O_tug20_LEGACY', 'O', 'source_bridge', 'overnight_vs_intraday', _feat('tug_of_war_20d'),
        20, source_class='LEGACY', legacy_key='tug_of_war_20d')
    reg('O_onratio20_LEGACY', 'O', 'source_bridge', 'overnight_share_ratio',
        _feat('overnight_return_ratio_20d'), 20, source_class='LEGACY',
        legacy_key='overnight_return_ratio_20d', note='源 clip(-2,2); 只作对照')


# ============================================================
# C 轴 (p = C/VWAP - 1)
# ============================================================
def _build_C():
    reg('C_p1', 'C', 'position', 'close_vs_vwap_today', lambda B: B.p, 1, unit='ratio')
    for w in (5, 20, 40, 60):
        reg('C_mean%d' % w, 'C', 'position', 'close_vs_vwap_mean',
            (lambda w: lambda B: rmean(B.p, w))(w), w, unit='ratio', rep=(w in (20, 40)))
    for w in (20, 40):
        reg('C_amtw%d' % w, 'C', 'weighted', 'close_vs_vwap_amount_weighted',
            (lambda w: lambda B: _div(rsum(np.where(np.isfinite(B.p), B.amt * B.p, np.nan), w),
                                      rsum(np.where(np.isfinite(B.p), B.amt, np.nan), w)))(w),
            w, unit='ratio', rep=(w == 20), note='活动权重, 不是投资者身份')
        reg('C_trw%d' % w, 'C', 'weighted', 'close_vs_vwap_turnover_weighted',
            (lambda w: lambda B: _div(rsum(np.where(np.isfinite(B.p), B.x * B.p, np.nan), w),
                                      rsum(np.where(np.isfinite(B.p), B.x, np.nan), w)))(w),
            w, unit='ratio')
        reg('C_med%d' % w, 'C', 'robust', 'close_vs_vwap_median',
            (lambda w: lambda B: rmed(B.p, w))(w), w, unit='ratio')
        reg('C_posf%d' % w, 'C', 'robust', 'close_above_vwap_fraction',
            (lambda w: lambda B: rmean(np.where(np.isfinite(B.p), (B.p > 0).astype(float),
                                                np.nan), w))(w), w, unit='fraction')
    reg('C_dev1', 'C', 'instant', 'close_vs_vwap_shock',
        lambda B: B.p - lag(rmean(B.p, 20), 1), 20, unit='ratio', rep=True,
        note='instant-minus-lagmean20')
    reg('C_m5m20', 'C', 'instant', 'close_vs_vwap_short_minus_long',
        lambda B: rmean(B.p, 5) - rmean(B.p, 20), 20, unit='ratio')
    reg('C_scaled', 'C', 'scaled', 'close_vs_vwap_per_vol',
        lambda B: _div(B.p, lag(rstd(B.r, 20), 1)), 20, unit='z')

    def clv(B):
        with np.errstate(all='ignore'):
            v = np.where(B.Hh > B.L, (2 * B.Cc - B.Hh - B.L) / (B.Hh - B.L), np.nan)
        return rmean(np.where(B.valid, v, np.nan), 20)
    reg('C_clv20', 'C', 'scaled', 'close_location_value', clv, 20, unit='[-1,1]',
        note='H==L 无定义')
    reg('C_CVR20_LEGACY', 'C', 'source_bridge', 'close_vs_vwap_mean', _feat('CVR_20d'), 20,
        source_class='LEGACY', legacy_key='CVR_20d', source_ref='features_daily.py:573')
    reg('C_CVR5_LEGACY', 'C', 'source_bridge', 'close_vs_vwap_mean', _feat('CVR_5d'), 5,
        source_class='LEGACY', legacy_key='CVR_5d')
    reg('C_cvr1_LEGACY', 'C', 'source_bridge', 'close_vs_vwap_today', _feat('CVR'), 1,
        source_class='LEGACY', legacy_key='CVR')
    reg('C_shadow20_LEGACY', 'C', 'source_bridge', 'shadow_asymmetry',
        _feat('shadow_asymmetry_20d'), 20, source_class='LEGACY', legacy_key='shadow_asymmetry_20d')
    reg('C_ci5_LEGACY', 'C', 'source_bridge', 'cum_intraday_return',
        _feat('cum_intraday_ret_5d'), 5, source_class='LEGACY', legacy_key='cum_intraday_ret_5d')


# ============================================================
# A 轴 (量能动态; 基线一律不含当日)
# ============================================================
def _build_A():
    reg('A_rel20', 'A', 'self_baseline', 'activity_vs_prior_mean',
        lambda B: _div(B.x, lag(rmean(B.x, 20), 1)), 20, unit='ratio', rep=True)
    reg('A_rel60', 'A', 'self_baseline', 'activity_vs_prior_mean',
        lambda B: _div(B.x, lag(rmean(B.x, 60), 1)), 60, unit='ratio')

    def logdev(B):
        lx = np.where(B.x > 0, np.log(np.where(B.x > 0, B.x, 1.0)), np.nan)
        return lx - lag(rmean(lx, 20), 1)
    reg('A_logdev20', 'A', 'self_baseline', 'log_activity_innovation', logdev, 20, unit='log')
    reg('A_amtrel20', 'A', 'self_baseline', 'amount_vs_prior_mean',
        lambda B: _div(B.amt, lag(rmean(B.amt, 20), 1)), 20, unit='ratio')
    reg('A_volrel20', 'A', 'self_baseline', 'volume_vs_prior_mean',
        lambda B: _div(B.vol, lag(rmean(B.vol, 20), 1)), 20, unit='ratio')

    def innov(B):
        m = lag(rmed(B.x, 20), 1)
        mad = lag(rmad_same_center(B.x, 20), 1)
        return np.where(mad > 0, _div(B.x - m, mad), np.nan)
    reg('A_innov', 'A', 'robust_innovation', 'activity_robust_z', innov, 20, unit='z', rep=True,
        note='分母 0 标 NaN')
    for w in (5, 20):
        def pers(B, w=w):
            base = lag(rmean(B.x, 20), 1)
            above = np.where(np.isfinite(B.x) & np.isfinite(base), (B.x > base).astype(float),
                             np.nan)
            return rmean(above, w)
        reg('A_pers%d' % w, 'A', 'persistence', 'activity_above_own_baseline_fraction', pers, w,
            unit='fraction', note='每个历史日的基线只用此前信息')

        def slope(B, w=w):
            b, _, _ = rtrend(B.x, w)
            return _div(b, rstd(B.x, w))
        reg('A_slope%d' % w, 'A', 'trend', 'activity_standardized_slope', slope, w,
            unit='per_day_z')
    reg('A_ac20', 'A', 'persistence', 'activity_lag1_autocorr',
        lambda B: rcorr(B.x, lag(B.x, 1), 20), 20, unit='corr')

    def sgacc(B):
        from scipy.signal import savgol_coeffs
        cf = savgol_coeffs(11, 2, deriv=2, pos=10, use='dot')      # 单侧, 末端评价
        rel = _div(B.x, lag(rmean(B.x, 20), 1))

        def fn(sw):
            v = np.isfinite(sw).all(-1)
            return np.where(v, np.einsum('tnw,w->tn', np.where(np.isfinite(sw), sw, 0.0), cf),
                            np.nan)
        return _chunked_windows(rel, 11, fn)
    reg('A_sgacc', 'A', 'trend', 'activity_acceleration_one_sided', sgacc, 11, unit='per_day2',
        note='SG 11 点二次, pos=10 末端二阶导 (不用居中窗, R30); 输入 = 相对前 20 日均值')
    reg('A_frompeak', 'A', 'event_recovery', 'activity_vs_observed_event_peak',
        lambda B: _div(B.x, _peak_x(B)[0]), 20, unit='ratio',
        event_clock='tau_to_t_peak', rep=True)
    reg('A_dpeak', 'A', 'event_recovery', 'days_since_observed_event_peak',
        lambda B: _peak_x(B)[1], 20, unit='days', event_clock='tau_to_t_peak')
    for w in (20, 60):
        reg('A_corr_xr%d' % w, 'A', 'volume_price', 'activity_return_corr',
            (lambda w: lambda B: rcorr(B.x, B.r, w))(w), w, unit='corr')
        reg('A_corr_xabs%d' % w, 'A', 'volume_price', 'activity_absreturn_corr',
            (lambda w: lambda B: rcorr(B.x, B.d, w))(w), w, unit='corr')

    def hilo(B, hi):
        base = lag(rmean(B.x, 20), 1)
        st = (B.x > base) if hi else (B.x < base)
        v = np.isfinite(B.x) & np.isfinite(base) & np.isfinite(B.r)
        return rmean(np.where(v, st * B.r, np.nan), 20)
    reg('A_hi_r20', 'A', 'volume_price', 'return_on_high_activity_days',
        lambda B: hilo(B, True), 20, unit='logret')
    reg('A_lo_r20', 'A', 'volume_price', 'return_on_low_activity_days',
        lambda B: hilo(B, False), 20, unit='logret')
    reg('A_hhi20', 'A', 'concentration', 'activity_concentration',
        lambda B: _div(rsum(B.x ** 2, 20), rsum(B.x, 20) ** 2), 20, unit='hhi')
    reg('A_dnshare20', 'A', 'asymmetry', 'down_day_activity_share',
        lambda B: _div(rsum(np.where(np.isfinite(B.r), (B.r < 0) * B.x, np.nan), 20),
                       rsum(np.where(np.isfinite(B.r), B.x, np.nan), 20)), 20, unit='fraction')
    reg('A_vr1_LEGACY', 'A', 'source_bridge', 'volume_vs_mean_incl_today',
        _feat('volume_ratio_1d'), 1, source_class='LEGACY', legacy_key='volume_ratio_1d')
    reg('A_vr3_LEGACY', 'A', 'source_bridge', 'volume_vs_mean_incl_today',
        _feat('volume_ratio_3d'), 3, source_class='LEGACY', legacy_key='volume_ratio_3d')
    reg('A_ar1_LEGACY', 'A', 'source_bridge', 'amount_vs_mean_incl_today',
        _feat('amount_ratio_1d'), 1, source_class='LEGACY', legacy_key='amount_ratio_1d')
    reg('A_ddvol_LEGACY', 'A', 'source_bridge', 'drawdown_volume_ratio',
        _feat('drawdown_volume_ratio'), 20, source_class='LEGACY', legacy_key='drawdown_volume_ratio')


# ============================================================
# S 轴 (同业状态; 全市场 PIT 行业, 剔自身)
# ============================================================
def _build_S():
    for w in (5, 20):
        reg('S_peerR%d' % w, 'S', 'peer_return', 'industry_loo_mean_return',
            (lambda w: lambda B: peer_loo_mean(B, _Rw_mkt(B, w))[0][:, B.oc])(w), w,
            unit='logret', rep=(w == 20), note='asof_T_peer_feature')
        reg('S_peermedR%d' % w, 'S', 'peer_return', 'industry_loo_median_return',
            (lambda w: lambda B: _peer_q(B, w)[0.5])(w), w, unit='logret')
        reg('S_peerpos%d' % w, 'S', 'peer_breadth', 'industry_loo_positive_fraction',
            (lambda w: lambda B: _peer_q(B, w, pos=True)['pos'])(w), w, unit='fraction',
            rep=(w == 20))
    reg('S_npeers', 'S', 'peer_breadth', 'industry_valid_peer_count',
        lambda B: peer_loo_mean(B, _Rw_mkt(B, 20))[1][:, B.oc], 20, unit='count')
    reg('S_peeriqr20', 'S', 'peer_dispersion', 'industry_loo_return_iqr',
        lambda B: _peer_q(B, 20)[0.75] - _peer_q(B, 20)[0.25], 20, unit='logret', rep=True)
    reg('S_peerstd20', 'S', 'peer_dispersion', 'industry_loo_return_std',
        lambda B: _peer_std(B, 20), 20, unit='logret')

    def peeract(B):
        ra = _div(rmean(B.x_mkt, 5), rmean(B.x_mkt, 20))
        return peer_loo_mean(B, ra)[0][:, B.oc]

    def peerhi(B):
        base = lag(rmean(B.x_mkt, 20), 1)
        hi = np.where(np.isfinite(B.x_mkt) & np.isfinite(base), (B.x_mkt > base).astype(float),
                      np.nan)
        return peer_loo_mean(B, hi)[0][:, B.oc]

    def indtrank(B):
        T, Nm = B.x_mkt.shape
        out = np.full((T, Nm), np.nan)
        m20 = rmean(B.x_mkt, 20)
        for t in range(T):
            v = np.isfinite(m20[t]) & (B.ind_mkt[t] >= 0)
            if v.sum() < 4:
                continue
            s = pd.Series(m20[t][v])
            g = B.ind_mkt[t][v]
            out[t, np.where(v)[0]] = s.groupby(g).rank(pct=True).values
        return out[:, B.oc]
    reg('S_peeract', 'S', 'peer_activity', 'industry_loo_relative_activity', peeract, 20,
        unit='ratio', rep=True)
    reg('S_peerhiact', 'S', 'peer_activity', 'industry_loo_high_activity_fraction', peerhi, 20,
        unit='fraction')
    reg('S_indtrank', 'S', 'peer_activity', 'turnover_rank_in_industry', indtrank, 20,
        unit='percentile')
    for w in (5, 20):
        reg('S_relmed%d' % w, 'S', 'peer_relative', 'return_vs_peer_median_per_iqr',
            (lambda w: lambda B: _div(_Rw_mkt(B, w)[:, B.oc] - _peer_q(B, w)[0.5],
                                      np.where(_peer_q(B, w)[0.75] - _peer_q(B, w)[0.25] > 0,
                                               _peer_q(B, w)[0.75] - _peer_q(B, w)[0.25],
                                               np.nan)))(w), w, unit='iqr_units')
    for k in (0, 1, 2):
        reg('S_comove%d' % k, 'S', 'peer_linkage', 'lagged_comovement_with_industry',
            (lambda k: lambda B: _comove(B, k))(k), 120, unit='corr',
            note='截至 t-1 的 120 日 corr(r_i, r_peer 滞后 %d); 描述性' % k)


def _peer_q(B, w, pos=False):
    k = '_pq%d_%d' % (w, int(pos))
    if k not in B.__dict__:
        qs, pf = peer_loo_quantiles(B, _Rw_mkt(B, w), pos_frac=pos)
        d = {q: v[:, B.oc] for q, v in qs.items()}
        if pos:
            d['pos'] = pf[:, B.oc]
        B.__dict__[k] = d
    return B.__dict__[k]


def _peer_std(B, w):
    Rm = _Rw_mkt(B, w)
    m1, _ = peer_loo_mean(B, Rm)
    m2, n = peer_loo_mean(B, Rm ** 2)
    with np.errstate(all='ignore'):
        var = (m2 - m1 ** 2) * n / (n - 1)
    return np.sqrt(np.maximum(var, 0.0))[:, B.oc]


def _comove(B, k):
    rp, _ = peer_loo_mean(B, B.radj_mkt)
    rp = rp[:, B.oc]
    rpk = lag(rp, k) if k else rp
    c = rcorr(B.radj, rpk, 120, mo=84)
    return lag(c, 1)


# ============================================================
# 5. 注册全部目录
# ============================================================
_built = [False]


def build_catalog():
    if _built[0]:
        return CATALOG
    for f in (_build_T, _build_K, _build_V, _build_R, _build_O, _build_C, _build_A, _build_S):
        f()
    ids = [m['member_id'] for m in CATALOG]
    assert len(ids) == len(set(ids)), '成员 id 重复'
    _built[0] = True
    return CATALOG


def member(mid):
    build_catalog()
    for m in CATALOG:
        if m['member_id'] == mid:
            return m
    raise KeyError(mid)
