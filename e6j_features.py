# -*- coding: utf-8 -*-
"""E6j 研究块 B1–B7 的新测量（plan §5.2–§5.8；§3.3 价格时钟；§3.4 默认估计政策）。

输入 = E6i 同款预热网格上的 Base（`e6i_features.Base(S)`，S = `e6i_core.seg_i(pname, warm=True)`；只 import、不改）：
  x   = 换手率（开市日，x ≥ 0）          d = |r_cc| = |log(C/lclose)|（有效 OHLC 日）
  r   = log(C/lclose)   o = log(O/lclose)（隔夜 ON）   c = log(C/O)（日内 ID）   h − l = log(H/L)（极差）
  amt = 成交额（元；本模块统一换成 1e6 元，比值 / 斜率的秩与金额基数无关，登记单位）
  trig / tau() = 截至 t 已知 I11 触发（E6i 事件钟，段首前无已知触发）
  p0w = 段内 pool0 映射到预热网格（段外 0；spell_entry 时钟用）
默认估计政策（plan §3.4，新测量；既有源成员严格继承源政策、另行复用 E6i 缓存）：
  20 日窗至少 10 个有效配对、60 日至少 30、W3 至少 2、W5 至少 4；std ddof = 1；分解用总体协方差 ddof = 0；
  ε = 1e−4 只加在 |收益| 类价格响应上（换单位同改）；OLS：x 无有效变异 → NA；y 常数而 x 有变异 → β = 0 有效、ρ 未定义（NA）。
所有测量只用 ≤ t 的数据（前缀不变性由合成检验阻断）。方向不写进测量函数，在登记层给（high_bad / low_bad）。
本模块只算原值 (T_w × N_own)；取段网格用 `Base.to_seg`；中性化 / 排名在账户层按 E6i NS 源路径做。"""
import math

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

EPS = 1e-4
AMT_UNIT = 1e6


def mo_of(w):
    """plan §3.4：W3→2、W5→4（至少 2/3）；20→10、60→30（至少一半）。"""
    return {3: 2, 5: 4}.get(int(w), int(math.ceil(w / 2.0)))


# ------------------------------------------------------------------ 基础算子
def sdiv(a, b):
    with np.errstate(all='ignore'):
        out = np.asarray(a, float) / np.asarray(b, float)
    return np.where(np.isfinite(out), out, np.nan)


def lag1(A):
    out = np.full_like(A, np.nan, dtype=float)
    out[1:] = A[:-1]
    return out


def pair(a, b):
    v = np.isfinite(a) & np.isfinite(b)
    return np.where(v, a, np.nan), np.where(v, b, np.nan), v


def _roll(A, w, how, mo):
    r = pd.DataFrame(A).rolling(w, min_periods=mo)
    return getattr(r, how)().values


def rmean(A, w, mo=None):
    return _roll(A, w, 'mean', mo_of(w) if mo is None else mo)


def rsum(A, w, mo=None):
    return _roll(A, w, 'sum', mo_of(w) if mo is None else mo)


def rcount(A, w):
    return pd.DataFrame(np.isfinite(A).astype(float)).rolling(w, min_periods=1).sum().values


def rstd(A, w, mo=None):
    return pd.DataFrame(A).rolling(w, min_periods=mo_of(w) if mo is None else mo).std(ddof=1).values


def pair_moments(z, y, w, mo=None):
    """窗内有效配对的总体矩：n, mz, my, vz, vy, czy（ddof = 0）；n < mo 处全部 NaN。
       用 rolling sum 实现（与逐窗 np.mean 同值到浮点；合成检验对暴力实现核对）。"""
    mo = mo_of(w) if mo is None else mo
    zv, yv, v = pair(z, y)
    n = rcount(zv, w)
    sz, sy = rsum(zv, w, 1), rsum(yv, w, 1)
    szz, syy, szy = rsum(zv * zv, w, 1), rsum(yv * yv, w, 1), rsum(zv * yv, w, 1)
    with np.errstate(all='ignore'):
        mz, my = sz / n, sy / n
        vz = szz / n - mz * mz
        vy = syy / n - my * my
        czy = szy / n - mz * my
    ok = n >= mo
    f = lambda A: np.where(ok, A, np.nan)
    return f(n), f(mz), f(my), np.where(ok, np.maximum(vz, 0.0), np.nan), np.where(ok, np.maximum(vy, 0.0), np.nan), f(czy)


def _novar(v, scale):
    """总体方差在浮点意义上为 0（相对输入尺度 64·eps）→ 视为无有效变异。"""
    return ~(v > 64.0 * np.finfo(float).eps * np.maximum(scale * scale, 1e-300))


def ols_slope(z, y, w, mo=None):
    """y ~ 1 + z 的 OLS 斜率（窗内有效配对）；返回 (β, ρ, scale = sd(y)/sd(z), mz, my, n, 状态码)。
       状态：0 有效；1 数据不足（DATA_MISSING/WARMUP）；2 z 无变异（NO_EXCITATION → β NA）；3 y 常数（VALID_ZERO：β = 0、ρ NA）。"""
    n, mz, my, vz, vy, czy = pair_moments(z, y, w, mo)
    nov_z = _novar(vz, np.abs(mz))
    nov_y = _novar(vy, np.abs(my))
    with np.errstate(all='ignore'):
        beta = np.where(nov_z, np.nan, np.where(nov_y, 0.0, czy / vz))
        rho = np.where(nov_z | nov_y, np.nan, czy / np.sqrt(vz * vy))
        scale = np.where(nov_z, np.nan, np.sqrt(vy) / np.sqrt(vz))
    code = np.where(~np.isfinite(n), 1, np.where(nov_z, 2, np.where(nov_y, 3, 0)))
    return beta, rho, scale, mz, my, n, code


# ------------------------------------------------------------------ 价格 / 活动序列
def ys(B):
    return {'CC': B.d, 'ID': np.abs(B.c), 'RANGE': B.h - B.l, 'ON': np.abs(B.o)}


def zs(B):
    return {'TR': B.x, 'AMT': B.amt / AMT_UNIT}


def signed(B, y):
    return {'CC': B.r, 'ID': B.c}[y]


# ------------------------------------------------------------------ B1（plan §5.2）
def b1(B):
    x, d = B.x, B.d
    b20 = lag1(rmean(x, 20))
    b60 = lag1(rmean(x, 60))
    a20 = sdiv(x, b20)
    q = sdiv(1.0, d + EPS)
    s20 = a20 * q
    with np.errstate(all='ignore'):
        logk0 = np.where(x > 0, np.log(sdiv(x, d + EPS)), np.nan)
        logs20 = np.where(s20 > 0, np.log(np.where(s20 > 0, s20, 1.0)), np.nan)
    return {'J_B1_b20': b20, 'J_B1_a20': a20, 'J_B1_qCC': q, 'J_B1_S20lag': s20,
            'J_B1_S60lag': sdiv(x, b60) * q, 'J_B1_logK0': logk0, 'J_B1_logS20lag': logs20}


# ------------------------------------------------------------------ B2（plan §5.3）
def b2(B):
    out = {}
    Y, Z = ys(B), zs(B)
    for zn in ('TR', 'AMT'):
        z = Z[zn]
        for yn in ('CC', 'ID', 'RANGE'):
            y = Y[yn]
            zv, yv, v = pair(z, y)
            pt = sdiv(zv, yv + EPS)
            out['J_B2_POINT_%s_%s' % (zn, yn)] = pt
            out['J_B2_MR3_%s_%s' % (zn, yn)] = rmean(pt, 3)
            out['J_B2_MR5_%s_%s' % (zn, yn)] = rmean(pt, 5)
            n = rcount(zv, 20)
            ros = sdiv(rsum(zv, 20, 1), rsum(yv, 20, 1) + n * EPS)
            out['J_B2_ROS20_%s_%s' % (zn, yn)] = np.where(n >= mo_of(20), ros, np.nan)
            out['J_B2_SLOPE20_%s_%s' % (zn, yn)] = ols_slope(z, y, 20)[0]
        zo, yo, _ = pair(z, Y['ON'])
        out['J_B2_POINT_%s_ON' % zn] = sdiv(zo, yo + EPS)
    return out


# ------------------------------------------------------------------ B3-A（plan §5.4 A）
def b3a(B):
    out = {}
    for yn in ('CC', 'ID'):
        y = ys(B)[yn]
        inv = sdiv(1.0, y + EPS)
        for w in (3, 20):
            n, mx, minv, vx, vinv, cov = pair_moments(B.x, inv, w)
            P = mx * minv
            for lam, tag in ((0.0, '0'), (0.5, '05'), (1.0, '1')):
                out['J_B3A_Q%s_%s_W%d' % (tag, yn, w)] = P + lam * cov
            out['J_B3A_COVP_%s_W%d' % (yn, w)] = np.where(np.isfinite(P) & (P > 0), sdiv(cov, P), np.nan)
    return out


# ------------------------------------------------------------------ B3-B（plan §5.4 B）
def b3b(B):
    out = {}
    for yn in ('CC', 'ID'):
        beta, rho, scale, mx, my, n, _ = ols_slope(B.x, ys(B)[yn], 20)
        out['J_B3B_BETANORM_%s' % yn] = beta * sdiv(mx, my + EPS)
        out['J_B3B_RHO_%s' % yn] = rho
        out['J_B3B_SCALE_%s' % yn] = scale
    return out


# ------------------------------------------------------------------ B3-C（plan §5.4 C：逐日留一 β 的可靠性）
def loo_reliability(z, y, w=20, min_pairs=10, chunk=200):
    """同一 20 日窗：β = OLS(y ~ 1 + z)；β_{−j} 删一日重估。u = median|β_{−j}−β| / (|β| + median|β_{−j}−β| + scale_eps)，
       scale_eps = 32·eps·max(|β|, median|β_{−j}|)；r = (n/w)(1 − u) 截于 [0,1]；分母为 0 → r = 0；
       留一拟合也须至少 min_pairs 对（即 n − 1 ≥ min_pairs），不足 → r = 0（码 1）；任一留一因无变异不可估 → r = 0（码 2）。
       β 本身按 n ≥ min_pairs 给出（与 qM 同窗）。返回 (r, β, code)。"""
    zv, yv, v = pair(z, y)
    T, N = zv.shape
    r_out = np.zeros((T, N)); b_out = np.full((T, N), np.nan); code = np.ones((T, N), np.int8)
    if T < w:
        return r_out, b_out, code
    eps = np.finfo(float).eps
    for j0 in range(0, N, chunk):
        Zw = swv(zv[:, j0:j0 + chunk], w, axis=0)       # (T−w+1, n, w)
        Yw = swv(yv[:, j0:j0 + chunk], w, axis=0)
        V = np.isfinite(Zw)
        Z0, Y0 = np.where(V, Zw, 0.0), np.where(V, Yw, 0.0)
        n = V.sum(-1).astype(float)
        sz, sy, szz, szy = Z0.sum(-1), Y0.sum(-1), (Z0 * Z0).sum(-1), (Z0 * Y0).sum(-1)
        with np.errstate(all='ignore'):
            vz = szz - sz * sz / n
            beta = (szy - sz * sy / n) / vz
            # 留一：去掉窗内第 j 个有效配对
            n1 = n[..., None] - 1.0
            sz1, sy1 = sz[..., None] - Z0, sy[..., None] - Y0
            szz1, szy1 = szz[..., None] - Z0 * Z0, szy[..., None] - Z0 * Y0
            vz1 = szz1 - sz1 * sz1 / n1
            b1_ = (szy1 - sz1 * sy1 / n1) / vz1
        scl = np.maximum(np.abs(sz / n), 1e-300)
        ok_full = (n >= min_pairs) & (vz > 64 * eps * scl * scl * n)
        ok_loo = (vz1 > 64 * eps * (scl * scl * n)[..., None]) | ~V
        est = ok_full & ok_loo.all(-1) & ((n - 1) >= min_pairs)
        dev = np.where(V, np.abs(b1_ - beta[..., None]), np.nan)
        with np.errstate(all='ignore'):
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                med = np.nanmedian(dev, axis=-1)
                medb = np.nanmedian(np.where(V, np.abs(b1_), np.nan), axis=-1)
            seps = 32.0 * eps * np.maximum(np.abs(beta), medb)
            den = np.abs(beta) + med + seps
            u = np.where(den > 0, med / den, np.nan)
            rr = np.clip((n / w) * (1.0 - u), 0.0, 1.0)
        rr = np.where(est & (den > 0) & np.isfinite(rr), rr, 0.0)
        c = np.where((n - 1) < min_pairs, 1, np.where(~est, 2, 0)).astype(np.int8)
        r_out[w - 1:, j0:j0 + chunk] = rr
        b_out[w - 1:, j0:j0 + chunk] = np.where(ok_full, beta, np.nan)
        code[w - 1:, j0:j0 + chunk] = c
    return r_out, b_out, code


def b3c(B):
    """返回可靠性 r（CC / ID）与 ID 的 β（CC 的 qM = 源 K_slope20，ID 的 qM = J_B2_SLOPE20_TR_ID，账户层接）。"""
    out = {}
    for yn in ('CC', 'ID'):
        r, beta, code = loo_reliability(B.x, ys(B)[yn], 20, 10)
        out['J_B3C_REL_%s' % yn] = r
        out['__beta_%s' % yn] = beta
        out['__code_%s' % yn] = code
    return out


# ------------------------------------------------------------------ B4（plan §5.5）
def b4(B):
    out, diag = {}, {}
    for yn in ('CC', 'ID'):
        y = ys(B)[yn]; s = signed(B, yn)
        xv, yv, v = pair(B.x, y)
        sv = np.where(v, s, np.nan)
        n_all = rcount(xv, 20)
        ok_all = n_all >= mo_of(20)
        ks = {}
        for side, m in (('UP', sv > 0), ('DN', sv < 0)):
            xs_ = np.where(m, xv, np.nan); ys_ = np.where(m, yv, np.nan)
            ns = rcount(xs_, 20)
            ok = ok_all & (ns >= 3)
            ros = sdiv(rsum(xs_, 20, 1), rsum(ys_, 20, 1) + ns * EPS)
            mr = rsum(sdiv(xs_, ys_ + EPS), 20, 1) / ns
            out['J_B4_ROS_%s_%s' % (side, yn)] = np.where(ok, ros, np.nan)
            out['J_B4_MR_%s_%s' % (side, yn)] = np.where(ok, mr, np.nan)
            ks[side] = (out['J_B4_ROS_%s_%s' % (side, yn)], out['J_B4_MR_%s_%s' % (side, yn)])
        for k, tag in ((0, 'ROS'), (1, 'MR')):
            up, dn = ks['UP'][k], ks['DN'][k]
            with np.errstate(all='ignore'):
                out['J_B4_ASYM_%s_%s' % (tag, yn)] = np.where((up > 0) & (dn > 0), np.log(np.where(up > 0, up, 1.0)) -
                                                             np.log(np.where(dn > 0, dn, 1.0)), np.nan)
        diag[yn] = dict(n_all=n_all, n_up=rcount(np.where(sv > 0, xv, np.nan), 20),
                        n_dn=rcount(np.where(sv < 0, xv, np.nan), 20), n_zero=rcount(np.where(sv == 0, xv, np.nan), 20))
    return out, diag


# ------------------------------------------------------------------ B5（plan §5.6 事件）
def clock_last_trigger(B):
    return B.tau()


def clock_spell_entry(p0w):
    """最近一次 pool0 连续 spell 的首日行号（无 → −1）；只用 ≤ t 的 pool0。"""
    p = np.asarray(p0w, bool)
    start = p & ~np.vstack([np.zeros((1, p.shape[1]), bool), p[:-1]])
    idx = np.where(start, np.arange(p.shape[0])[:, None], -1)
    return np.maximum.accumulate(idx, axis=0)


def _at_clock(A_lagged, c):
    """A_lagged = lag1(窗统计)（第 k 行 = [k−W, k−1] 的统计）；取每格在事件钟行 c 处的值（c < 0 → NaN）。"""
    T, N = c.shape
    ci = np.where(c >= 0, c, 0)
    vals = A_lagged[ci, np.arange(N)[None, :].repeat(T, 0)]
    return np.where(c >= 0, vals, np.nan)


def _event_sum(A, c):
    """Σ_{s=c..t} A_s（NaN 当 0 计入和；配套计数另算）。c < 0 → NaN。"""
    T, N = c.shape
    cs = np.vstack([np.zeros((1, N)), np.nancumsum(np.where(np.isfinite(A), A, 0.0), axis=0)])
    ci = np.where(c >= 0, c, 0)
    cols = np.arange(N)[None, :].repeat(T, 0)
    out = cs[np.arange(1, T + 1)[:, None].repeat(N, 1), cols] - cs[ci, cols]
    return np.where(c >= 0, out, np.nan)


def rev_shrunk(sye_ev, sx_ev, myep, mxp, m):
    """R_ev(m) = [(Σ_ev d_ε + m·mean_pre d_ε)/(Σ_ev x + m·mean_pre x)] / [mean_pre d_ε / mean_pre x]；m = 0 即原始 R_ev。"""
    return sdiv(sdiv(sye_ev + m * myep, sx_ev + m * mxp), sdiv(myep, mxp))


def b5(B, p0w):
    out, diag = {}, {}
    clocks = {'LT': clock_last_trigger(B), 'SE': clock_spell_entry(p0w)}
    for yn in ('CC', 'ID'):
        y = ys(B)[yn]
        xv, yv, v = pair(B.x, y)
        ye = np.where(v, yv + EPS, np.nan)                  # d_ε：事件前后同一 ε 口径
        for W in (20, 60):
            mo = mo_of(W)
            n_pre = lag1(rcount(xv, W))
            mx_pre = lag1(rmean(xv, W, mo)); my_pre = lag1(rmean(yv, W, mo)); mye_pre = lag1(rmean(ye, W, mo))
            n_, mz, my, vz, vy, czy = pair_moments(B.x, y, W, mo)
            with np.errstate(all='ignore'):
                b_pre = lag1(np.where(_novar(vz, np.abs(mz)), np.nan, czy / vz))
            a_pre = lag1(my) - b_pre * lag1(mz)
            for ck, c in clocks.items():
                mxp, myp, myep = _at_clock(mx_pre, c), _at_clock(my_pre, c), _at_clock(mye_pre, c)
                ap, bp = _at_clock(a_pre, c), _at_clock(b_pre, c)
                sx_ev, sye_ev = _event_sum(xv, c), _event_sum(ye, c)
                n_ev = _event_sum(v.astype(float), c)
                rarpre = sdiv(sdiv(B.x, mxp), y + EPS)
                rev = rev_shrunk(sye_ev, sx_ev, myep, mxp, 0.0)
                rev5 = rev_shrunk(sye_ev, sx_ev, myep, mxp, 5.0)
                U = sdiv(yv - ap - bp * xv, myp + EPS)
                okc = (c >= 0) & np.isfinite(mxp)
                ok_ev = okc & (n_ev >= 1)
                tag = '%s_W%d_%s' % (yn, W, ck)
                out['J_B5_RARPRE_%s' % tag] = np.where(okc, rarpre, np.nan)
                out['J_B5_REV_%s' % tag] = np.where(ok_ev, rev, np.nan)
                out['J_B5_REV5_%s' % tag] = np.where(ok_ev, rev5, np.nan)
                out['J_B5_U_%s' % tag] = np.where(okc & np.isfinite(bp), U, np.nan)
                if yn == 'CC' and W == 20:
                    T = c.shape[0]
                    diag[ck] = dict(age=np.where(c >= 0, np.arange(T)[:, None] - c, np.nan), n_ev=n_ev)
    return out, diag


# ------------------------------------------------------------------ B6（plan §5.7；T 槽位）
def b6(B):
    from e6i_features import rtrend
    x = B.x
    m20 = rmean(x, 20)
    b20 = lag1(rmean(x, 20))
    rel = sdiv(x, b20)
    _, rs, _ = rtrend(x, 20, mo_of(20))
    return {'J_B6_CV20': np.where(m20 > 0, sdiv(rstd(x, 20), m20), np.nan),
            'J_B6_RELROLL20': rstd(rel, 20),
            'J_B6_DETREND20': np.where(m20 > 0, sdiv(rs, m20), np.nan)}


def all_members(B, p0w):
    """全部新原值（T_w × N_own）+ 诊断。键以 '__' 开头的是账户层辅助量，不进登记表。"""
    out = {}
    out.update(b1(B)); out.update(b2(B)); out.update(b3a(B)); out.update(b3b(B)); out.update(b3c(B))
    o4, d4 = b4(B); out.update(o4)
    o5, d5 = b5(B, p0w); out.update(o5)
    out.update(b6(B))
    return out, dict(b4=d4, b5=d5)
