#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 共享内核 (2026-09-09)。
   参数化因子 + 四种中性化 + E7 守卫加载 + 段上下文持久化 + 控制组 + 账本工具。
   建在 e6e_core 之上, 不修改 e6e_* 任何文件。本模块只提供构件, 不自己跑东西。
"""
import os, sys, time, json, math, hashlib, glob, warnings
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import data_loader as DL
from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import (define_i11_signal, build_observation_pool,
                               apply_hard_constraints, neutralize_by_mcap)
import comprehensive_factor_diagnosis as C
import e6e_core as K

VERSION = 'E6f-v1'
FROZEN_END = '20260327'                       # 禁区 §12: 任何取数不得越过
PUB_CACHE = '/mnt/big/base/public/FundamentalTL/cache/'
WCACHE = '/mnt/sda2/lichenchen/data/cache_e6f'
E6E_DIR = '/mnt/sda2/lichenchen/results/20260906_1300_E6e_architecture'
E6C_DIR = '/mnt/sda2/lichenchen/results/20260905_0633_E6c_holding_horizon'
SEGS = K.SEGS
COST, COST_HI = K.COST, K.COST_HI
UNKNOWN_IND = '__UNKNOWN__'
NSI_METHOD = 'svd'                            # 'svd' = 生产路径; 'fwl' = 等价测试路径


# ============================================================
# 1. E7 守卫 + 可写缓存影子目录
# ============================================================
_shadowed = [False]


def shadow_cache():
    """把 PATHS['cache_dir'] 指到自己盘上的影子目录; 公共缓存以符号链接复用(只读),
       新日期区间(history_warmed)才落到自己盘。公共目录一个字节都不写。"""
    if _shadowed[0]:
        return WCACHE
    os.makedirs(WCACHE, exist_ok=True)
    if os.path.isdir(PUB_CACHE):
        for f in os.listdir(PUB_CACHE):
            d = os.path.join(WCACHE, f)
            if not os.path.exists(d):
                try:
                    os.symlink(os.path.join(PUB_CACHE, f), d)
                except OSError:
                    pass
    DL.PATHS['cache_dir'] = WCACHE
    _shadowed[0] = True
    return WCACHE


def guarded_load(start_date, end_date, **kw):
    """唯一允许的取数入口。end_date > 2026-03-27 直接抛错 (禁区 §12 / GLOBAL STOP)。"""
    for nm, v in (('start_date', start_date), ('end_date', end_date)):
        if not (isinstance(v, str) and len(v) == 8 and v.isdigit()):
            raise ValueError('E7 GUARD: %s 必须是 8 位日期字符串, 得到 %r' % (nm, v))
    if end_date > FROZEN_END:
        raise RuntimeError('E7 GUARD 触发 (GLOBAL STOP): end_date=%s > 冻结末日 %s。'
                           '源数据物理上有更晚日期, 但 E6f 禁区 §12 禁止读取。' % (end_date, FROZEN_END))
    if start_date > end_date:
        raise ValueError('E7 GUARD: start_date %s > end_date %s' % (start_date, end_date))
    shadow_cache()
    return load_all_daily_data(start_date=start_date, end_date=end_date, **kw)


def source_last_date():
    """源 kline 目录的最晚日期 —— 只用于在 manifest 里记录"我们冻结在更早的日子"。"""
    fs = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(DL.PATHS['daily_kline'], '*.csv')))
    return (fs[0], fs[-1]) if fs else (None, None)


def warm_start(pname, calendar_days=260):
    """history_warmed 的加载起点: 段首往前推 calendar_days 天; 源数据没有更早日期则返回段首。"""
    ps, _ = PERIODS[pname]
    first, _ = source_last_date()
    want = (pd.Timestamp(ps) - pd.Timedelta(days=calendar_days)).strftime('%Y%m%d')
    if first is None:
        return ps, 'no_source_listing'
    if want < first:
        return (first, 'clipped_to_source_start') if first < ps else (ps, 'no_prior_data')
    return want, 'warmed'


# ============================================================
# 2. 参数化因子
# ============================================================
def mp(w):
    """新窗最少观测数 = ceil(w/2); 逐项复现库默认 (T60->30, CVR20->10, CVR5->3, K1->1)"""
    return max(1, int(math.ceil(w / 2.0)))


def _eps_tag(e):
    return {1e-5: '1e-5', 1e-4: '1e-4', 1e-3: '1e-3'}.get(e, repr(e))


def fid(sp):
    """因子规格的规范 ID (进 feature_registry / 配置主键)"""
    r, w = sp['role'], int(sp['w'])
    if r == 'T':
        return 'T%d' % w
    if r == 'C':
        return 'C%d' % w
    if r == 'K':
        return 'K%s%d@%s' % (sp['est'], w, _eps_tag(sp['eps']))
    if r == 'Cf':
        return 'Cf%d%s' % (w, sp.get('base', 'diff')[0])
    if r == 'B':
        return 'B%d%s' % (w, 'a' if sp.get('adj') else 'u')
    raise ValueError(r)


def spec(role, w, est='MA', eps=1e-4, base='diff', adj=False):
    return dict(role=role, w=int(w), est=est, eps=eps, base=base, adj=bool(adj))


def _cvr_diff(data):
    """库口径 CVR = (close - vwap)/vwap"""
    close = data['close'].astype(float)
    vwap = data['vwap'].astype(float)
    return ((close - vwap) / vwap.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)


def _cvr_ratio(data):
    """E6e 研究口径 intraday_cvr_1d = close/vwap - 1 (与上式数学恒等, 浮点不必逐位相同)"""
    return (data['close'] / data['vwap']).replace([np.inf, -np.inf], np.nan) - 1


def _k_parts(data):
    tr = data['turnover_rate'].astype(float)
    rr = np.log(data['close'] / data['lclose']).replace([np.inf, -np.inf], np.nan).abs()
    return tr, rr


def build_raw(data, sp):
    """按规格重建原始因子帧。默认窗必须逐项复现库值 —— 由 e6f_selftests 第 2/5 组阻断验收。"""
    r, w = sp['role'], int(sp['w'])
    if r == 'T':
        return data['turnover_rate'].astype(float).rolling(w, min_periods=mp(w)).std()
    if r in ('C', 'Cf'):
        base = _cvr_ratio(data) if sp.get('base') == 'ratio' else _cvr_diff(data)
        return base if w == 1 else base.rolling(w, min_periods=mp(w)).mean()
    if r == 'B':
        cl = data['close'].astype(float)
        if sp.get('adj'):
            cl = cl * C.adjust_factor(data)
        return (cl / cl.shift(w) - 1).replace([np.inf, -np.inf], np.nan)
    if r == 'K':
        tr, rr = _k_parts(data)
        eps = float(sp['eps'])
        if sp['est'] == 'MA':
            x = tr / (rr + eps)                                   # 任一缺失即缺失
            return x if w == 1 else x.rolling(w, min_periods=mp(w)).mean()
        if sp['est'] == 'ROS':
            v = tr.notna() & rr.notna()                           # 共同有效日
            trv, rrv = tr.where(v), rr.where(v)
            if w == 1:
                return trv / (rrv + eps)
            m = mp(w)
            s_tr = trv.rolling(w, min_periods=m).sum()
            s_rr = rrv.rolling(w, min_periods=m).sum()
            nn = trv.rolling(w, min_periods=m).count()
            return (s_tr / (s_rr + nn * eps)).where(nn >= m)
        raise ValueError(sp['est'])
    raise ValueError(r)


# 默认锚: (规格, 库字段名) —— 相同源实现查值; 等价表达查 allclose
DEFAULT_ANCHORS = [
    (spec('T', 60), 'turnover_volatility_60d', 'exact'),
    (spec('C', 20), 'CVR_20d', 'exact'),
    (spec('C', 5), 'CVR_5d', 'exact'),
    (spec('Cf', 1, base='diff'), 'CVR', 'exact'),
    (spec('Cf', 5, base='diff'), 'CVR_5d', 'exact'),
    (spec('K', 1, est='MA', eps=1e-4), 'conditional_turnover', 'exact'),
    (spec('K', 1, est='ROS', eps=1e-4), 'conditional_turnover', 'exact'),
    (spec('B', 5), 'cum_return_5d', 'exact'),
    (spec('B', 20), 'cum_return_20d', 'exact'),
    (spec('Cf', 1, base='ratio'), 'intraday_cvr_1d', 'allclose'),
]

# 角色 -> E6e 里的经典因子名 (方向继承; roles.csv 全部 worst_pooled=5 -> high_bad=True)
ROLE_CANON = {'T': K.FT, 'C': K.FC, 'Cf': K.FCVR1, 'K': K.FK, 'B': K.FCR5}


def high_bad(sp):
    return K.HB[ROLE_CANON[sp['role']]]


# ============================================================
# 3. 四种中性化
# ============================================================
def _ind_codes(industry, dates, cols):
    """行业 -> 每日整数码; 缺失单独成一类 UNKNOWN (不用未来行业补)"""
    if industry is None:
        return None, None
    iv = industry.reindex(index=dates, columns=cols).values
    iv = np.where(pd.isna(iv), UNKNOWN_IND, iv)
    codes, uniq = pd.factorize(pd.Series(iv.ravel()))
    return codes.reshape(len(dates), len(cols)), list(uniq)


def _resid_ni(y, ic):
    """行业哑变量残差 = 逐行业去均值 (与 OLS on 满秩哑变量恒等)"""
    G = ic.max() + 1
    cnt = np.bincount(ic, minlength=G).astype(float)
    sm = np.bincount(ic, weights=y, minlength=G)
    mu = np.divide(sm, cnt, out=np.zeros(G), where=cnt > 0)
    rank = int((cnt > 0).sum())
    return y - mu[ic], rank


def _resid_nsi(y, m, ic, method=None):
    """[行业哑变量, log_mcap] 联合最小二乘残差。
       'svd' = np.linalg.lstsq (生产路径, 给出数值秩); 'fwl' = 双去均值 (等价, 供测试)。"""
    method = method or NSI_METHOD
    G = ic.max() + 1
    if method == 'fwl':
        yt, rk = _resid_ni(y, ic)
        mt, _ = _resid_ni(m, ic)
        den = float(mt @ mt)
        if den < 1e-12:
            return yt, rk, True                       # size 被行业完全解释 -> 退化为 NI
        return yt - (float(mt @ yt) / den) * mt, rk + 1, False
    D = np.zeros((len(y), G))
    D[np.arange(len(y)), ic] = 1.0
    keep = D.sum(axis=0) > 0
    X = np.column_stack([D[:, keep], m])
    beta, _, rank, _ = np.linalg.lstsq(X, y, rcond=None)
    degen = rank <= int(keep.sum())
    return y - X @ beta, int(rank), bool(degen)


def neu_cache(raw, pool, log_mcap, icodes_full, mode, dates=None, cols=None):
    """逐日中性化缓存 dict[date] = Series。守卫与 precompute_neutralized_factor 一致
       (池内 <6 跳过; dropna 后 <6 跳过)。返回 (cache, info)。"""
    info = dict(mode=mode, days=0, skipped=0, fallback_ns=0, degenerate_size=0,
                rank_sum=0, dof_min=10 ** 9)
    if mode == 'NS':
        cache = C.precompute_neutralized_factor(raw, pool, log_mcap)
        info['days'] = len(cache)
        return cache, info
    cache = {}
    pcols = pool.columns
    for di, date_idx in enumerate(pool.index):
        in_pool = pool.loc[date_idx] == 1
        stocks = pcols[in_pool]
        if len(stocks) < 6:
            info['skipped'] += 1
            continue
        f = raw.loc[date_idx, stocks]
        if mode == 'N0':
            s = f.dropna()
            if len(s) < 6:
                info['skipped'] += 1
                continue
            cache[date_idx] = s
            info['days'] += 1
            continue
        m = log_mcap.loc[date_idx, stocks]
        ok = f.notna().values & (m.notna().values if mode == 'NSI' else True)
        if icodes_full is None:
            info['fallback_ns'] += 1
            s = neutralize_by_mcap(f, m).dropna()
            if len(s) >= 6:
                cache[date_idx] = s
                info['days'] += 1
            continue
        idxpos = np.where(in_pool.values)[0]
        ic_all = icodes_full[di, idxpos]
        yv = f.values.astype(float)
        sel = ok & ~np.isnan(yv)
        n = int(sel.sum())
        if n < 10:
            info['fallback_ns'] += 1
            s = neutralize_by_mcap(f, m).dropna()
            if len(s) >= 6:
                cache[date_idx] = s
                info['days'] += 1
            continue
        y = yv[sel]
        ic = pd.factorize(ic_all[sel])[0]
        if mode == 'NI':
            res, rank = _resid_ni(y, ic)
            degen = False
        else:
            res, rank, degen = _resid_nsi(y, m.values.astype(float)[sel], ic)
        dof = n - rank
        if dof < 3:
            info['fallback_ns'] += 1
            s = neutralize_by_mcap(f, m).dropna()
            if len(s) >= 6:
                cache[date_idx] = s
                info['days'] += 1
            continue
        info['rank_sum'] += rank
        info['dof_min'] = min(info['dof_min'], dof)
        info['degenerate_size'] += int(degen)
        s = pd.Series(res, index=np.asarray(stocks)[sel]).dropna()
        if len(s) < 6:
            info['skipped'] += 1
            continue
        cache[date_idx] = s
        info['days'] += 1
    if info['dof_min'] == 10 ** 9:
        info['dof_min'] = None
    return cache, info


# ============================================================
# 4. 稠密 pct 排名表 (逐日) —— 供快速掩码
# ============================================================
def pct_dense(cache, dates, colpos, Nc, ccols_set, hb=True):
    """cache -> (T, Nc) float64 pct 排名 (NaN = 该日该票无值)。
       与 e6e pct_or 的 Series.rank(pct=True) 逐值相同 (average 并列法)。"""
    T = len(dates)
    out = np.full((T, Nc), np.nan)
    for i, d in enumerate(dates):
        s = cache.get(d)
        if s is None:
            continue
        p = s.rank(pct=True)
        if not hb:
            p = 1.0 - p
        idx = np.asarray(s.index)
        pos = np.fromiter((colpos.get(x, -1) for x in idx), int, len(idx))
        v = pos >= 0
        out[i, pos[v]] = p.values[v]
    return out


_QCUT = {}


def qcut_group(n, g):
    """pd.qcut(rank(method='first'), g, labels=1..g) 对 1..n 的整数秩给出的组号。
       直接调 pandas 本身并按 (n,g) 记忆化 —— 构造上就与源 helper 不可能不同。
       (闭式 1+k/g*(n-1) 与 np.percentile 的线性插值在末位差 1 ULP, 恰在边界上的秩会翻组,
        实测 C:k15 差 28 格; 见 source_corrections_E6f。)"""
    key = (int(n), int(g))
    r = _QCUT.get(key)
    if r is None:
        s = pd.Series(np.arange(1, n + 1, dtype=float))
        r = pd.qcut(s.rank(method='first'), g, labels=range(1, g + 1)).to_numpy().astype(np.int16)
        _QCUT[key] = r
    return r


# E6e 的 P2G 是"首次收益调用前锁定"的分位映射, 不含深度 15 (E6e 从未用过)。
# brief §4.2 要求补 KTC_mean@15。按生成 P2G 其余条目的同一规则新增: 取使
# g×pct/100 为整数的最小 g ∈ {2,4,10,20} —— 15% -> g=20 保留 3 组。
# (核验: 20->10 保留2, 25->4 保留1, 30->10 保留3, 35->20 保留7, 40->10 保留4,
#  50->2 保留1, 75->4 保留3 —— 与锁定表逐条一致。) 不改 e6e_core.P2G。
P2G = dict(K.P2G)
P2G[15] = 20


def keep_mask_dense(P, p0c, pctkeep, g=None):
    """保留最好 pctkeep% (低 pct = 好)。P=(T,Nc) pct 表, p0c=(T,Nc) 池掩码。
       完全复刻 e6e keep_pct_mask -> holds -> build_factor_strategy_holdings_cached 的语义:
       池内有值票 <3g 当日空仓; qcut(rank('first'), g); 丢弃 dgroups。"""
    T, Nc = P.shape
    if pctkeep >= 100:
        return p0c.copy()
    if g is None:
        g = P2G[int(pctkeep)]
    keep_g = int(round(g * pctkeep / 100.0))
    out = np.zeros((T, Nc), bool)
    for t in range(T):
        v = np.where(p0c[t] & ~np.isnan(P[t]))[0]
        n = len(v)
        if n < g * 3:
            continue
        order = np.lexsort((v, P[t, v]))                 # 分数升序, 并列按列位稳定 = rank('first')
        gid = qcut_group(n, g)
        out[t, v[order[gid <= keep_g]]] = True
    return out


def drop_mask_dense(P, p0c, k):
    """剔最差 1/k (毒尾) -> 返回【剔除】掩码, 复刻 e6e drop_or = pool ∧ ¬kept;
       池内无值票也算剔除; 有值票 <3k 当日 holds 空 -> 全池皆剔除。"""
    T, Nc = P.shape
    kept = np.zeros((T, Nc), bool)
    for t in range(T):
        v = np.where(p0c[t] & ~np.isnan(P[t]))[0]
        n = len(v)
        if n < k * 3:
            continue
        order = np.lexsort((v, P[t, v]))
        gid = qcut_group(n, k)
        kept[t, v[order[gid <= k - 1]]] = True
    return p0c & ~kept


def combine_dense(Ps, how='mean', complete=False):
    """多分量 pct 表合成。complete=True 时任一分量缺失即整体缺失 (对齐 e6e dropna 语义)。"""
    A = np.stack(Ps, axis=0)
    fn = {'max': np.nanmax, 'min': np.nanmin, 'median': np.nanmedian}.get(how, np.nanmean)
    with np.errstate(invalid='ignore'), warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        out = fn(A, axis=0)
    out = np.where(_day_ok(A)[:, None], out, np.nan)
    if complete:
        out = np.where(np.isnan(A).any(axis=0), np.nan, out)
    return out


def _day_ok(A):
    """e6e combine() 先取各分量【日期集合的交集】(`keys &= set(c)`): 任一分量当日整行无值,
       当日整体无值。漏掉这条会在只有部分分量可得的日子多出持仓 (实测 KT_mean/TC_mean/
       K_gate_TC 的 d_pos 差到 0.94)。"""
    return (~np.isnan(A)).any(axis=2).all(axis=0)


def wcombine_dense(Ps, ws):
    """有理权重合成 (§4.2 权重层)。零权重分量真正 bypass: 不参与均值, 也不因其缺失剔股。"""
    use = [(P, w) for P, w in zip(Ps, ws) if w > 0]
    if not use:
        raise ValueError('全零权重')
    num = np.zeros_like(use[0][0])
    den = np.zeros_like(use[0][0])
    for P, w in use:
        ok = ~np.isnan(P)
        num[ok] += w * P[ok]
        den[ok] += w
    out = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
    ok_day = _day_ok(np.stack([P for P, _ in use], axis=0))   # 日期交集只对权重>0 的分量
    return np.where(ok_day[:, None], out, np.nan)


# ============================================================
# 5. 段上下文 (可持久化 / mmap)
# ============================================================
class SegX(object):
    pass


def build_segment(pname, support='legacy_all', verbose=True):
    """支持集: legacy_all (E6e 口径, 无预热) / history_warmed (只预热因子源数据)。
       pool0 / clean / 基准 一律沿冻结版 (legacy 加载) 重算, 与支持集无关。"""
    t0 = time.time()
    ps, pe = PERIODS[pname]
    data = guarded_load(ps, pe)
    feats = calc_all_daily_features(data)
    close = data['close']
    bse = [c for c in close.columns if K.is_bse(c)]
    base_pool = get_base_pool(data)
    mature = close.notna().astype(float).rolling(20, min_periods=1).sum() >= 20
    clean = ((base_pool == 1) & mature).astype(float)
    if bse:
        clean[bse] = 0.0
    signal = define_i11_signal(feats, base_pool)
    obs = build_observation_pool(signal, obs_window=5)
    pool0 = apply_hard_constraints(obs, data, feats, min_mcap=0)
    log_mcap = C.compute_log_mcap(data.get('mcap'))
    industry = data.get('industry_zx1', data.get('industry'))
    if industry is not None:
        industry = industry.reindex(index=close.index, columns=close.columns)
    shares = K.bench_industry_shares(clean, industry)

    S = SegX()
    S.name, S.support = pname, support
    S.data, S.feats, S.clean, S.pool0 = data, feats, clean, pool0
    S.industry, S.shares, S.log_mcap = industry, shares, log_mcap
    S.T, S.Nfull = pool0.shape
    S.p0 = (pool0.values == 1)
    S.ccols = np.where(S.p0.any(axis=0))[0]
    S.Nc = len(S.ccols)
    S.dates = list(pool0.index)
    S.cols = np.asarray(pool0.columns)
    S.ccolnames = S.cols[S.ccols]
    S.colpos = {c: i for i, c in enumerate(S.cols)}
    S.ccolpos = {c: i for i, c in enumerate(S.ccolnames)}
    S.p0c = S.p0[:, S.ccols]

    ind_v = industry.values
    codes, uniq = pd.factorize(pd.Series(ind_v[:, S.ccols].ravel()))
    S.icodes = codes.reshape(S.T, S.Nc)
    S.G = int(S.icodes.max()) + 1
    code_of = {v: i for i, v in enumerate(uniq)}
    sh = np.zeros((S.T, S.G))
    for t in range(S.T):
        for kk, v in shares[t].items():
            if kk in code_of:
                sh[t, code_of[kk]] = v
    S.cap = sh + K.MAX_IND_DEV
    dr = C.vwap_daily_return(data, K.ADJUST)
    S.dr = dr
    S.bench = dr.where(clean == 1).mean(axis=1).values
    S.r0 = np.nan_to_num(dr.values[:, S.ccols], nan=0.0)
    S.den5 = np.minimum(np.arange(1, S.T + 1), K.HOLD).astype(float)
    S.icodes_neu, S.ind_names = _ind_codes(industry, pool0.index, pool0.columns)

    # history_warmed: 只把因子源数据提前, clean/pool0/基准不动
    if support == 'history_warmed':
        ws, tag = warm_start(pname)
        S.warm_tag = tag
        S.warm_start = ws
        if tag in ('warmed', 'clipped_to_source_start'):
            S.wdata = guarded_load(ws, pe)
        else:
            S.wdata = data
    else:
        S.warm_tag, S.warm_start, S.wdata = 'legacy_all', ps, data

    S._store = {}
    if verbose:
        print('  [%s/%s] pipeline %.0fs T=%d Nc=%d G=%d pool0日均%.1f warm=%s'
              % (pname, support, time.time() - t0, S.T, S.Nc, S.G,
                 S.p0.sum(1).mean(), S.warm_tag), flush=True)
    return S


def get_pct(S, sp, mode='NS'):
    """(T, Nc) pct 表, 按 (因子规格, 中性化模式) 缓存。"""
    key = (fid(sp), mode)
    if key in S._store:
        return S._store[key][0]
    raw = build_raw(S.wdata, sp)
    if raw.shape != S.pool0.shape or not raw.index.equals(S.pool0.index):
        raw = raw.reindex(index=S.pool0.index, columns=S.pool0.columns)
    cache, info = neu_cache(raw, S.pool0, S.log_mcap, S.icodes_neu, mode)
    P = pct_dense(cache, S.dates, S.ccolpos, S.Nc, None, hb=high_bad(sp))
    info.update(fid=key[0], mode=mode, support=S.support, period=S.name)
    S._store[key] = (P, info)          # 不留 Series 缓存: 41 个规格会占数 GB
    return P


def get_info(S, sp, mode='NS'):
    get_pct(S, sp, mode)
    return S._store[(fid(sp), mode)][1]


def get_cache(S, sp, mode='NS'):
    raise NotImplementedError('_store 不再保留 Series 缓存; 需要时直接调 neu_cache')


# ============================================================
# 6. 引擎 (参数化持有期)
# ============================================================
def dev_from_dense(S, mask_c):
    idx, val = [], []
    for t in range(S.T):
        h = np.where(mask_c[t])[0]
        idx.append(h)
        val.append(K.dev_day(h, S.icodes[t], S.cap[t], S.G))
    return idx, val


def sparse_pnl_H(S, idx, val, H=K.HOLD, cost_bp=COST):
    """e6e sparse_pnl 的持有期参数化版; H=5 时与之逐位相同 (自测第 4 组)。"""
    T, r0, bench = S.T, S.r0, S.bench
    den = np.minimum(np.arange(1, T + 1), H).astype(float)
    wsum = np.fromiter((v.sum() if len(v) else 0.0 for v in val), float, T)
    cs = np.concatenate([[0.0], np.cumsum(wsum)])
    lo = np.maximum(np.arange(1, T + 1) - H, 0)
    act_sum = (cs[1:] - cs[lo]) / den
    pos = np.zeros(T)
    pos[2:] = act_sum[:-2]

    port = np.zeros(T)
    for t in range(2, T):
        a = 0.0
        for s in range(max(0, t - 1 - H), t - 1):
            if len(idx[s]):
                a += float(r0[t, idx[s]] @ val[s])
        port[t] = a / den[t - 2]

    turn = np.zeros(T)

    def amap(i):
        d = {}
        for s in range(max(0, i - H + 1), i + 1):
            for c, v in zip(idx[s], val[s]):
                d[c] = d.get(c, 0.0) + v
        dn = den[i]
        return {c: v / dn for c, v in d.items()}

    hi = min(T, H + 5)
    for t in range(3, hi):
        a1, a0 = amap(t - 2), amap(t - 3)
        ks = set(a1) | set(a0)
        turn[t] = 0.5 * sum(abs(a1.get(x, 0.0) - a0.get(x, 0.0)) for x in ks)
    for t in range(hi, T):
        p, q = t - 2, t - 2 - H
        ip, iq = idx[p], idx[q]
        if len(ip) == 0 and len(iq) == 0:
            continue
        ks = np.union1d(ip, iq)
        vp = np.zeros(len(ks))
        vq = np.zeros(len(ks))
        if len(ip):
            vp[np.searchsorted(ks, ip)] = val[p]
        if len(iq):
            vq[np.searchsorted(ks, iq)] = val[q]
        turn[t] = 0.5 * float(np.abs(vp - vq).sum()) / H
    gross = port - bench * pos
    return gross, pos, turn, gross - turn * (cost_bp / 1e4)


def eval_dense(S, mask_c, H=K.HOLD, cost_bp=COST):
    idx, val = dev_from_dense(S, mask_c)
    return sparse_pnl_H(S, idx, val, H, cost_bp), (idx, val)


# ============================================================
# 7. 控制组
# ============================================================
def coretrim_matchN(S, parent_P, parent_mask, target_n):
    """同日同父同最终人数: 在父核内按父的末级分数保留恰好 target_n[t] 只 (§4.3)。"""
    out = np.zeros_like(parent_mask)
    for t in range(S.T):
        r = int(target_n[t])
        if r <= 0:
            continue
        v = np.where(parent_mask[t] & ~np.isnan(parent_P[t]))[0]
        if len(v) == 0:
            continue
        r = min(r, len(v))
        order = np.lexsort((v, parent_P[t, v]))
        out[t, v[order[:r]]] = True
    return out


def wsum_daily(val):
    return np.fromiter((v.sum() if len(v) else 0.0 for v in val), float, len(val))


def scale_weights(val, f):
    return [v * f[i] if len(v) else v for i, v in enumerate(val)]


def eqpos_pair(S, pv, cv, H=K.HOLD):
    """等仓位配对 (只向下缩, 各自过 rolling 与成本)。返回 (父缩, 子缩) 两个 pnl 元组。"""
    P0, P1 = wsum_daily(pv[1]), wsum_daily(cv[1])
    f0 = np.where(P0 > 0, np.minimum(1.0, np.divide(P1, P0, out=np.zeros_like(P0), where=P0 > 0)), 0.0)
    f1 = np.where(P1 > 0, np.minimum(1.0, np.divide(P0, P1, out=np.zeros_like(P1), where=P1 > 0)), 0.0)
    a = sparse_pnl_H(S, pv[0], scale_weights(pv[1], f0), H)
    b = sparse_pnl_H(S, cv[0], scale_weights(cv[1], f1), H)
    return a, b


def common_domain(Ps):
    """共同域: 所有涉及分量当日均有值的票 (§4.3 paired_common_domain)"""
    ok = ~np.isnan(Ps[0])
    for P in Ps[1:]:
        ok &= ~np.isnan(P)
    return ok


# ============================================================
# 8. 账本 / 统计工具
# ============================================================
def ann(x):
    """小数日收益 -> 年化点数"""
    x = np.asarray(x, float)
    m = ~np.isnan(x)
    return float(np.mean(x[m])) * 252 * 100.0 if m.any() else np.nan


def hac_t(d, L=5):
    return K.score_hac(d, L)


def hac_calendar(x, clock_len, L=5):
    """日历感知影响序列 z_t = I_t (x_t - mu)/mean(I) 在原时钟上的 HAC (§7)"""
    x = np.asarray(x, float)
    I = (~np.isnan(x)).astype(float)
    if I.sum() < 10:
        return np.nan, np.nan, int(I.sum())
    mu = float(np.nanmean(x))
    z = np.zeros(clock_len)
    n = min(clock_len, len(x))
    z[:n] = I[:n] * (np.nan_to_num(x[:n]) - mu) / I.mean()
    S = float(z @ z)
    for l in range(1, L + 1):
        if l < len(z):
            S += 2.0 * (1 - l / (L + 1.0)) * float(z[l:] @ z[:-l])
    se = np.sqrt(S) / clock_len if S > 0 else np.nan
    return mu * 252 * 100.0, (mu / se if (se == se and se > 0) else np.nan), int(I.sum())


def stationary_blocks(rng, T, mean_block, B):
    """stationary bootstrap 的采样计数矩阵 (T, B); 段内重采样由调用方按段切分。
       向量化: 每步以概率 1/mean_block 跳到新的随机起点, 否则前进一格 (环绕) ——
       与"抽几何长度的块再连续取"等价, 但只有一个长度 T 的外层循环。"""
    p = 1.0 / float(mean_block)
    starts = rng.integers(0, T, size=(T, B))
    jump = rng.random((T, B)) < p
    idx = np.empty((T, B), dtype=np.int64)
    idx[0] = starts[0]
    for t in range(1, T):
        idx[t] = np.where(jump[t], starts[t], idx[t - 1] + 1)
        np.mod(idx[t], T, out=idx[t])
    cnt = np.empty((T, B), dtype=np.int32)
    for b in range(B):
        cnt[:, b] = np.bincount(idx[:, b], minlength=T)
    return cnt


def boot_mat(X, CNT, DEN):
    """X=(T,Ncfg) 日值(NaN->0), CNT=(T,B) 采样计数, DEN=(B,) 有效日计数 -> (Ncfg,B) 年化"""
    Xf = np.nan_to_num(X, nan=0.0)
    return (Xf.T @ CNT) / DEN * 252 * 100.0


# ============================================================
# 9. 任务状态表 (协议 §3)
# ============================================================
STATES = ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'LIMIT', 'SUPERSEDED')


class TaskTable(object):
    def __init__(self, path):
        self.path = path
        self.rows = {}

    def reg(self, task_id, kind, **kw):
        self.rows[task_id] = dict(task_id=task_id, kind=kind, state='PENDING',
                                  attempt=0, note='', **kw)

    def set(self, task_id, state, **kw):
        assert state in STATES, state
        r = self.rows[task_id]
        r['state'] = state
        r.update(kw)
        if state == 'RUNNING':
            r['attempt'] += 1

    def flush(self):
        df = pd.DataFrame(list(self.rows.values()))
        tmp = self.path + '.tmp'
        df.to_csv(tmp, index=False)
        os.replace(tmp, self.path)
        return df

    def audit(self):
        df = pd.DataFrame(list(self.rows.values()))
        by = df.state.value_counts().to_dict()
        return dict(total=len(df), by_state=by,
                    sum_ok=int(sum(by.values())) == len(df))


def sha_file(p):
    return K.sha_file(p)


def sha_obj(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False,
                                     default=str).encode()).hexdigest()
