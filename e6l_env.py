# -*- coding: utf-8 -*-
"""E6l 段环境（plan §4；brief W02 / W04 / W07 / A7）。在 e6k_env.Seg（E6k 已锚：pool0 单元坐标、size、行业、门结构）之上加：
测量（统一为大值不利的坏度 kf，pool0 单元；源 J_B1_qCC 同路径：原值 → pool0 当日 log 市值 OLS → 方向 'lo' → rank(pct)）：
  Q0            = E6k 'Q'（J_B1_qCC；W02）
  Q_D3/5/10     = 1 / (mean_valid(d, k) + ε)          Q_QMEAN5 = mean_valid(1 / (d + ε), 5)
  Q_DMED5       = 1 / (median_valid(d, 5) + ε)        Q_DEW3 / Q_DEW5 = 1 / (EW_λ(d) + ε)，λ = .5 / 1/3（绝对日期归一化递推）
  （d = |log(C / lclose)|，e6i_features.Base 同一预热网格与有效性；窗口按完整交易日历；有效数 ≥ ceil(.6k) 且当前 d 有效；
   EW：A_t = (1−λ)A_{t−1} + λ·m_t·d_t，B_t = (1−λ)B_{t−1} + λ·m_t，EW = A / B，网格首日 A = B = 0；λ = 1 短路回 Q0（本轮登记无 λ = 1 成员））
  Q_RANK3/5/10  = 过去 k 个交易日"源秩延伸"坏度的均值（≥ ceil(.6k) 有效且当前源 kQ 有限）→ 当前支持集内再 rank(pct)（不再 OLS）
  Q_RANKOBS5    = 只平均当日真在 pool0 的源 kQ（不延伸）→ 再 rank
  Q_RANKSCORE5  = RANK5 的时间均值直接作坏度（不再 rank）
  源秩延伸（A7）：u 日 pool0 成员按源 pool_screening_v2.neutralize_by_mcap 函数体重算 (α_u, β_u)（有效 < 10 → 原值直返；
  precompute_neutralized_factor 的 pool0 < 6 / 有效残差 < 6 → 当日无源秩）；成员保留源 kQ；当日 clean ∧ 池外 ∧ q 与 log 市值有限者
  用同一变换得残差、方向后按成员（坏度 → 源 kQ）结点单调插值（同值结点取源秩均值；范围外 0 / 1；< 2 个不同结点 → 无定义）。
  C1 / S / M    = E6k（E6i 成员）
状态（plan §6.1）：e6l_state 全程缓存按段日期取视图（Vol / Act 百分位与三分位、调度 b、p_t；Trend 个股三态）。"""
import math

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

import e6l_core as L
import e6k_env as E
import e6j_slot as SL

EPS = 1e-4
QNEW = ('Q_D3', 'Q_D5', 'Q_D10', 'Q_QMEAN5', 'Q_DMED5', 'Q_DEW3', 'Q_DEW5')
QRANK = ('Q_RANK3', 'Q_RANK5', 'Q_RANK10', 'Q_RANKOBS5', 'Q_RANKSCORE5')
QALL = ('Q0',) + QNEW + QRANK
MEAS_ALL = QALL + ('C1', 'S', 'M')
E6K_KEY = {'Q0': 'Q', 'C1': 'C1', 'S': 'S', 'M': 'M'}          # E6k 已有测量（逐值锚）
WIN = {'Q_D3': 3, 'Q_D5': 5, 'Q_D10': 10, 'Q_QMEAN5': 5, 'Q_DMED5': 5, 'Q_DEW3': 3, 'Q_DEW5': 5,
       'Q_RANK3': 3, 'Q_RANK5': 5, 'Q_RANK10': 10, 'Q_RANKOBS5': 5, 'Q_RANKSCORE5': 5}
LAMBDA = {'Q_DEW3': 0.5, 'Q_DEW5': 1.0 / 3.0}


def mo(k):
    return int(math.ceil(0.6 * k))


def sdiv(a, b):
    with np.errstate(all='ignore'):
        out = np.asarray(a, float) / np.asarray(b, float)
    return np.where(np.isfinite(out), out, np.nan)


def win_stat(x, k, how):
    """逐列因果窗口（含当日）：有效值的 mean / median；返回 (值, 有效数)。行 < k 时窗口自然截短（网格首部）。"""
    T, N = x.shape
    pad = np.full((k - 1, N), np.nan)
    xp = np.vstack([pad, x])
    W = swv(xp, k, axis=0)                               # (T, N, k)
    cnt = np.isfinite(W).sum(-1)
    with np.errstate(all='ignore'):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            v = np.nanmean(W, axis=-1) if how == 'mean' else np.nanmedian(W, axis=-1)
    return v, cnt


def ew_norm(x, lam, state=None, t0=0, ids_hash=None):
    """绝对日期归一化 EW（plan §4.2）：缺日两者衰减、不跳过；当前无效 → NaN。返回 (EW, 质量 B)。
    state（checkpoint 恢复，plan §5.6）：dict(next_row, ids, A, B)；next_row 必须 = t0、股票身份哈希必须一致，否则拒绝。"""
    T, N = x.shape
    if state is None:
        A = np.zeros(N)
        B = np.zeros(N)
    else:
        if state['next_row'] != t0 or (ids_hash is not None and state['ids'] != ids_hash):
            raise ValueError('EW checkpoint 身份不符：next_row %s vs %s；ids %s vs %s' % (state['next_row'], t0, state['ids'], ids_hash))
        A, B = state['A'].copy(), state['B'].copy()
    out = np.full((T, N), np.nan)
    mass = np.zeros((T, N))
    for t in range(T):
        ok = np.isfinite(x[t])
        A = (1.0 - lam) * A + np.where(ok, lam * np.where(ok, x[t], 0.0), 0.0)
        B = (1.0 - lam) * B + np.where(ok, lam, 0.0)
        mass[t] = B
        with np.errstate(all='ignore'):
            out[t] = np.where(ok & (B > 0), A / B, np.nan)
    ew_norm.last_state = dict(next_row=t0 + T, ids=ids_hash, A=A, B=B)
    return out, mass


def q_smooth_raw(d, key):
    """预热网格上的原值（T_w × N_own），与有效性事实。"""
    k = WIN[key]
    cnt = pd.DataFrame(np.isfinite(d).astype(float)).rolling(k, min_periods=1).sum().to_numpy()
    valid = np.isfinite(d) & (cnt >= mo(k))
    if key in ('Q_D3', 'Q_D5', 'Q_D10'):
        m, _ = win_stat(d, k, 'mean')
        raw = sdiv(1.0, m + EPS)
    elif key == 'Q_QMEAN5':
        m, _ = win_stat(sdiv(1.0, d + EPS), k, 'mean')
        raw = m
    elif key == 'Q_DMED5':
        m, _ = win_stat(d, k, 'median')
        raw = sdiv(1.0, m + EPS)
    elif key in LAMBDA:
        m, _ = ew_norm(d, LAMBDA[key])
        raw = sdiv(1.0, m + EPS)
    else:
        raise ValueError(key)
    raw = np.where(valid, raw, np.nan)
    return raw, valid


class SegL(E.Seg):
    """一段的只读上下文（E6k Seg + 本轮测量 + 状态视图）。"""

    def __init__(self, pname, state=True):
        E.Seg.__init__(self, pname)
        self._B = None
        self._rank = None
        self._rawnew = {}
        self._rankavg = {}
        self._cs = {}
        self.mfacts = {}
        self.st = None
        if state:
            import e6l_state as ST
            self.st = ST.seg_view(self.dates, self.S.ccolnames)
            self.trend_cells = self.st['trend'][self.ci.t, self.ci.c]

    # ------------------------------------------------------------ 预热网格
    def base(self):
        if self._B is None:
            import e6i_core as I
            import e6i_features as FE
            S = I.seg_i(self.pname, warm=True)
            L.assert_index_ok(S.wdata_i['close'].index, 'wdata_i %s' % self.pname)
            B = FE.Base(S)
            if list(B.own_cols) != list(self.S.ccolnames):
                raise RuntimeError('预热网格 own 列与段 ccols 不一致')
            self._B = B
        return self._B

    # ------------------------------------------------------------ 测量
    def meas_kf(self, key):
        """统一方向后的坏度（pool0 单元，缺失 NaN）。"""
        if key in E6K_KEY:
            return self.kf(E6K_KEY[key])
        if key in self._kf:
            return self._kf[key]
        if key in QNEW:
            B = self.base()
            raw_w, valid_w = q_smooth_raw(B.d, key)
            raw = B.to_seg(raw_w)
            self._rawnew[key] = raw
            neu = SL.neu_of(self.ctx, SL.full_frame(self.ctx, raw))
            self._kf[key] = self.env._dense_cells(SL.pct_dir(neu, 'lo'))
            p0c = self.S.p0c
            self.mfacts[key] = dict(window=WIN[key], min_valid=mo(WIN[key]), valid_share_pool0=float(np.isfinite(raw[p0c]).mean()),
                                    kf_finite_share=float(np.isfinite(self._kf[key]).mean()))
            return self._kf[key]
        if key in QRANK:
            self._kf[key] = self.rank_measure(key)
            return self._kf[key]
        raise ValueError(key)

    def raw_q(self):
        """J_B1_qCC 原值 (T, Nc)。"""
        return self.raw('Q')

    # ------------------------------------------------------------ 源秩延伸（A7）
    def rank_ext(self):
        """(T, Nc) 延伸坏度（成员 = 源 kQ；池外 clean = 插值；其余 NaN）+ 逐日事实。"""
        if self._rank is not None:
            return self._rank
        ctx = self.ctx
        S = self.S
        cc = np.asarray(S.ccols)
        T, Nc = self.T, self.Nc
        q = self.raw_q()
        logm = ctx['log_mcap'].reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, cc].astype(float)
        clean = ctx['clean'].reindex(index=S.pool0.index, columns=S.pool0.columns).fillna(0).values[:, cc] == 1
        p0 = ctx['pool0'].reindex(index=S.pool0.index, columns=S.pool0.columns).fillna(0).values[:, cc] == 1
        ext = np.full((T, Nc), np.nan)
        facts = []
        for u in range(T):
            m = np.flatnonzero(p0[u])
            f = dict(u=u, n_pool0=len(m), mode='SKIP', n_ref=0, n_knots=0, n_off=0, n_off_ext=0)
            if len(m) < 6:
                facts.append(f)
                continue
            y = q[u, m]
            x = logm[u, m]
            ok = np.isfinite(y) & np.isfinite(x)
            if ok.sum() < 10:
                res_m = y.copy()
                alpha = beta = None
                f['mode'] = 'RAW'
            else:
                xv, yv = x[ok], y[ok]
                beta = np.cov(xv, yv, bias=True)[0, 1] / np.var(xv)
                alpha = yv.mean() - beta * xv.mean()
                res_m = np.full(len(m), np.nan)
                res_m[ok] = yv - (alpha + beta * xv)
                f['mode'] = 'OLS'
            fin = np.isfinite(res_m)
            if fin.sum() < 6:
                f['mode'] = 'SKIP'
                facts.append(f)
                continue
            s = pd.Series(-res_m[fin])
            kq = s.rank(pct=True).to_numpy()
            ext[u, m[fin]] = kq
            f['n_ref'] = int(fin.sum())
            bad = -res_m[fin]
            vals = np.unique(bad)
            f['n_knots'] = int(len(vals))
            cand = clean[u] & ~p0[u] & np.isfinite(q[u])
            if f['mode'] == 'OLS':                                # 原值直返模式不需要市值
                cand &= np.isfinite(logm[u])
            off = np.flatnonzero(cand)
            f['n_off'] = int(len(off))
            if len(vals) >= 2 and len(off):
                o = np.argsort(bad, kind='stable')
                bs, ks = bad[o], kq[o]
                mids = np.array([ks[bs == v].mean() for v in vals])
                if np.any(np.diff(mids) < -1e-12):
                    raise RuntimeError('源秩结点非单调（%s u=%d）' % (self.pname, u))
                if f['mode'] == 'RAW':
                    r_off = q[u, off]
                else:
                    r_off = q[u, off] - (alpha + beta * logm[u, off])
                ext[u, off] = np.interp(-r_off, vals, mids, left=0.0, right=1.0)
                f['n_off_ext'] = int(len(off))
            facts.append(f)
        self._rank = (ext, pd.DataFrame(facts))
        return self._rank

    def rank_measure(self, key):
        """RANK 族（plan §4.3 / §4.4）→ pool0 单元坏度。"""
        k = WIN[key]
        ci = self.ci
        ext, facts = self.rank_ext()
        kq_now = self.kf('Q')                                    # 源 kQ（pool0 单元）
        kq_dense = np.full((self.T, self.Nc), np.nan)
        kq_dense[ci.t, ci.c] = kq_now
        src = kq_dense if key == 'Q_RANKOBS5' else ext
        m, cnt = win_stat(src, k, 'mean')
        cur_ok = np.isfinite(kq_dense)
        avg = np.where(cur_ok & (cnt >= mo(k)), m, np.nan)
        self._rankavg[key] = avg
        cells = avg[ci.t, ci.c]
        if key == 'Q_RANKSCORE5':
            out = cells
        else:
            out = np.full(self.n, np.nan)
            ok = np.isfinite(cells)
            ix = np.flatnonzero(ok)
            df = pd.DataFrame({'t': ci.t[ix], 'v': cells[ix]})
            out[ix] = df.groupby('t')['v'].rank(pct=True).to_numpy()
        ext_share = float(np.mean(np.isfinite(ext[ci.t, ci.c]))) if len(ci.t) else float('nan')
        self.mfacts[key] = dict(window=k, min_valid=mo(k), kf_finite_share=float(np.isfinite(out).mean()),
                                ext_days_skip=int((facts['mode'] == 'SKIP').sum()), ext_days_raw=int((facts['mode'] == 'RAW').sum()),
                                ext_off_pool_defined=int(facts['n_off_ext'].sum()), ext_cell_share=ext_share)
        return out

    # ------------------------------------------------------------ 支持桥（plan §4.4 / §9.3）
    def common_support(self, key):
        """(kX_cs, kQ0_cs, C)：C = X 与 Q0 原值（形成日 T 的 raw，中性化前）都有限的 pool0 单元；
        Q 平滑族 / Q0 在 C 上按源口径重做 log 市值 OLS + 方向 'lo' + rank（E6k Seg.pct_on 同函数）；
        RANK 族（RANK3/5/10、RANKOBS5）的时间均值在 C 上逐日 rank(pct)（不 OLS，与主定义同）；RANKSCORE5 不再 rank（C 外 NaN）。"""
        if key in self._cs:
            return self._cs[key]
        self.meas_kf(key)
        ci = self.ci
        rawX = self._rawnew[key] if key in QNEW else self._rankavg[key]
        rawQ = self.raw('Q')
        C = np.isfinite(rawX[ci.t, ci.c]) & np.isfinite(rawQ[ci.t, ci.c])        # (ci.t, ci.c) 即 pool0 单元
        cells = np.flatnonzero(C)
        kQ = self.pct_on(rawQ, cells, 'lo')
        if key in QNEW:
            kX = self.pct_on(rawX, cells, 'lo')
        elif key == 'Q_RANKSCORE5':
            kX = np.where(C, rawX[ci.t, ci.c], np.nan)
        else:
            v = np.where(C, rawX[ci.t, ci.c], np.nan)
            kX = np.full(self.n, np.nan)
            ix = np.flatnonzero(np.isfinite(v))
            kX[ix] = pd.DataFrame({'t': ci.t[ix], 'v': v[ix]}).groupby('t')['v'].rank(pct=True).to_numpy()
        self._cs[key] = (kX, kQ, C)
        self.mfacts.setdefault(key, {}).update(cs_share=float(C.mean()), cs_kX_finite=float(np.isfinite(kX).mean()),
                                               cs_kQ_finite=float(np.isfinite(kQ).mean()))
        return self._cs[key]

    # ------------------------------------------------------------ 状态视图
    def state_b(self, schedule, strict=False):
        """逐日 b（段日期；K 坏度百分位点）。"""
        return np.asarray(self.st[('bS_' if strict else 'b_') + schedule], float)
