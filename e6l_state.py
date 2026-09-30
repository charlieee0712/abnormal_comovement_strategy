# -*- coding: utf-8 -*-
"""E6l 状态变量（plan §6.1 / §6.2；brief W07 / A1；附录 A4-1 / A4-2 / A4-5）。全程日历 PIT 计算后按日期并入各段。
允许历史：全程缓存 daily_kline_20100101_20260327（load_all_daily_data 同源加载）；行情最早 2010-01-04，没有更早数据。
clean（全程）：与源 export_delivery_pools_v2 :96–119 同式——base_pool = event_study.get_base_pool(data)；
  mature = close 非缺的 20 日滚动计数 ≥ 20；clean = base_pool ∧ mature；北交所列清零。只在全程数据上算一次（不按段预热清零）。
Vol3：r_u = close_u / lclose_u − 1（复权 / 前收同源；close、lclose > 0 且有限）；r_m,u = clean(u−1) 成员有限 r_u 的等权均值
  （全无 → 未定义；可得数 n_ret 逐日存）；v_u = r_m 20 日样本标准差（ddof = 1，窗内 ≥ 16 有效）。
Act3：ratio_i,u = x_u / mean(x[u−60 … u−1])（turnover_rate；60 日窗 ≥ 36 有效且均值 > 0，x_u 有限）；
  med_u = clean(u−1) 成员可得 ratio 的中位（可得数 n_act 逐日存）；a_u = med 20 日均值（≥ 16 有效）。
百分位（两变量同式；plan §6.1）：T 日查询 x_{T−1}，参照 x_{T−251} … x_{T−2}（最多 250 个交易日位置，不补更早日期）；
  主定义 = 参照有限数 ≥ 150 且查询有限 → (#ref < q + .5 #ref == q) / n_ref；STRICT250 = 250 个位置全有限 → 同式 / 250；
  否则 STATE_UNKNOWN（编码 −1）。三分位：low ≤ 1/3（0）、mid ≤ 2/3（1）、high > 2/3（2）。
Trend3（个股）：adj = close × adj_factor（后复权）；r20 = adj_{T−1} / adj_{T−21} − 1（两端点有限且 > 0）；MA20 = adj[T−20 … T−1]
  有限值均值（≥ 16 个）；UP（2）= r20 > 0 ∧ adj_{T−1} > MA20；DOWN（0）= r20 < 0 ∧ adj_{T−1} < MA20；其余 MIXED（1）；缺 → UNKNOWN（−1）。
调度（plan §6.2）：p_t = 操作 Vol 状态在 T−250 … T−1 这 250 个交易日位置中已定义值的 high 比例（当前 T 不进；无定义 → .5）；
  VOL_HI15：high → 15、非 high → 5；VOL_HI5：high → 5、非 high → 15；VOL_MEAN15 = 5 + 10·p_t；VOL_MEAN5 = 15 − 10·p_t；
  当前状态未知一律 10。b 单位 = K 坏度百分位点（brief W03：0–1 评分上 5 点 = .05；Mmean b/3 由 Struct.bunit 换算）。"""
import e6l_boot  # noqa: F401
import os

import numpy as np
import pandas as pd

import e6l_core as L

FULL_START, FULL_END = '20100101', '20260327'
FULL_CACHE_DIR = '/mnt/sda2/lichenchen/data/cache'        # 已有 daily_kline_20100101_20260327.parquet（brief W07 全程缓存）
SCHEDULES = ('VOL_HI15', 'VOL_HI5', 'VOL_MEAN15', 'VOL_MEAN5')
LOOKBACK, MIN_REF = 250, 150
CACHE = None


def assert_state_dates(dates):
    """状态序列入口的 E7 守卫：任何日期 > 2026-03-27 → 抛错。"""
    d = pd.to_datetime(pd.Index(dates))
    if len(d) and d.max() > pd.Timestamp(L.MARKET_DATA_END_MAX):
        raise RuntimeError('状态序列含 %s（> %s，E7 守卫）' % (d.max().date(), L.MARKET_DATA_END_MAX))
    return True


def load_full(start=FULL_START, end=FULL_END):
    """全程缓存入口（E7 守卫在加载之前）。"""
    if str(end).replace('-', '') > L.MARKET_DATA_END_MAX.replace('-', ''):
        raise RuntimeError('load_full end=%s 越过 %s（E7 守卫）' % (end, L.MARKET_DATA_END_MAX))
    import e6f_core as F                                  # 项目唯一取数入口（E7 守卫 + 可写影子缓存；公共目录不写）
    data = F.guarded_load(str(start).replace('-', ''), str(end).replace('-', ''), cache_dir=FULL_CACHE_DIR)
    L.assert_index_ok(data['close'].index, 'full data[close]')
    return data


def full_period_ctx(end=FULL_END, dry_run=False):
    """连续面板的源上下文入口（plan §5.6）：源脚本 :96–119 的逐段准备在全程区间上跑一次（e6j_prod.build_period 原函数；
    只在内存里给 event_study.PERIODS 加一个 'FULL' 键，不改任何文件）。E7 守卫在加载之前。"""
    if str(end).replace('-', '') > L.MARKET_DATA_END_MAX.replace('-', ''):
        raise RuntimeError('full_period_ctx end=%s 越过 %s（E7 守卫）' % (end, L.MARKET_DATA_END_MAX))
    if dry_run:
        return None
    import event_study as ES
    import e6j_prod as PR
    ES.PERIODS['FULL'] = ('20100104', str(end).replace('-', ''))
    try:
        return PR.build_period('FULL')
    finally:
        del ES.PERIODS['FULL']


def clean_full(data):
    """源 build_period 的 clean 同式，在全程数据上算（不按段预热清零）。"""
    from event_study import get_base_pool
    close = data['close']
    base_pool = get_base_pool(data)
    mature = close.notna().astype(float).rolling(20, min_periods=1).sum() >= 20
    clean = ((base_pool == 1) & mature).astype(float)
    bse = [c for c in close.columns if str(c)[:1] in ('4', '8') or str(c)[:2] == '92']
    if bse:
        clean[bse] = 0.0
    return clean


def lag_pct(x, lookback=LOOKBACK, min_ref=MIN_REF):
    """(主, STRICT250, 参照有限数)。T 日查询 x[T−1]，参照 x[T−lookback−1 : T−1]（位置），不补更早日期。"""
    x = np.asarray(x, float)
    n = len(x)
    out = np.full(n, np.nan)
    strict = np.full(n, np.nan)
    nref = np.zeros(n, np.int64)
    fin = np.isfinite(x)
    for t in range(1, n):
        a = max(0, t - lookback - 1)
        h = x[a:t - 1]
        hf = h[np.isfinite(h)]
        nref[t] = len(hf)
        q = x[t - 1]
        if not fin[t - 1]:
            continue
        if len(hf) >= min_ref:
            out[t] = (np.sum(hf < q) + 0.5 * np.sum(hf == q)) / len(hf)
        if t - lookback - 1 >= 0 and len(h) == lookback and np.isfinite(h).all():
            strict[t] = (np.sum(h < q) + 0.5 * np.sum(h == q)) / lookback
    return out, strict, nref


def tercile(p):
    p = np.asarray(p, float)
    return np.where(~np.isfinite(p), -1, np.where(p <= 1.0 / 3.0, 0, np.where(p <= 2.0 / 3.0, 1, 2))).astype(np.int8)


def rolling_valid(x, w, mo, how='mean'):
    s = pd.Series(np.asarray(x, float))
    r = s.rolling(w, min_periods=mo)
    return (r.std(ddof=1) if how == 'std' else r.mean()).to_numpy()


def compute(data=None, cut=None):
    """全程状态序列。cut：先把全部输入表截断到 ≤ cut 再从头计算（含 clean；A4-1 截断重算恒等 = 真 PIT）。返回 dict（日期轴 = 数据交易日）。"""
    data = load_full() if data is None else data
    if cut is not None:
        idx = pd.to_datetime(pd.Index(data['close'].index).astype(str))
        keep = np.asarray(idx <= pd.Timestamp(cut))
        n0 = len(keep)
        data = {k: (v.loc[keep] if isinstance(v, pd.DataFrame) and len(v) == n0 else v) for k, v in data.items()}
    close = data['close'].astype(float)
    lclose = data['lclose'].astype(float).reindex_like(close)
    xto = data['turnover_rate'].astype(float).reindex_like(close)
    adjf = data['adj_factor'].astype(float).reindex_like(close)
    clean = clean_full(data).reindex_like(close).fillna(0.0)
    dates = pd.to_datetime(pd.Index(close.index).astype(str))
    assert_state_dates(dates)
    C = close.to_numpy()
    LC = lclose.to_numpy()
    with np.errstate(all='ignore'):
        r = np.where((C > 0) & (LC > 0) & np.isfinite(C) & np.isfinite(LC), C / LC - 1.0, np.nan)
    cl = clean.to_numpy() == 1
    prev = np.zeros_like(cl)
    prev[1:] = cl[:-1]
    ok = prev & np.isfinite(r)
    n_ret = ok.sum(1)
    with np.errstate(all='ignore'):
        rm = np.where(n_ret > 0, np.where(ok, r, 0.0).sum(1) / np.maximum(n_ret, 1), np.nan)
    v = rolling_valid(rm, 20, 16, 'std')
    X = xto.to_numpy()
    base = pd.DataFrame(X).shift(1).rolling(60, min_periods=36).mean().to_numpy()
    with np.errstate(all='ignore'):
        ratio = np.where(np.isfinite(X) & np.isfinite(base) & (base > 0), X / base, np.nan)
    rr = np.where(prev, ratio, np.nan)
    n_act = np.isfinite(rr).sum(1)
    with np.errstate(all='ignore'):
        med = np.where(n_act > 0, np.nanmedian(np.where(n_act[:, None] > 0, rr, 0.0), axis=1), np.nan)
    med = np.where(n_act > 0, med, np.nan)
    a20 = rolling_valid(med, 20, 16, 'mean')
    vp, vs, vn = lag_pct(v)
    ap, as_, an = lag_pct(a20)
    adj = C * adjf.to_numpy()
    adj = np.where(np.isfinite(adj) & (adj > 0), adj, np.nan)
    T, N = adj.shape
    ma = pd.DataFrame(adj).rolling(20, min_periods=16).mean().to_numpy()      # 窗 [u−19 … u]
    trend = np.full((T, N), -1, np.int8)
    if T > 21:
        e = adj[20:T - 1]                     # adj_{T−1}，T = 21 … T−1
        s0 = adj[0:T - 21]                    # adj_{T−21}
        m = ma[20:T - 1]                      # MA20 截至 T−1
        with np.errstate(all='ignore'):
            r20 = e / s0 - 1.0
        dfn = np.isfinite(r20) & np.isfinite(m) & np.isfinite(e)
        up = dfn & (r20 > 0) & (e > m)
        dn = dfn & (r20 < 0) & (e < m)
        code = np.where(up, 2, np.where(dn, 0, np.where(dfn, 1, -1))).astype(np.int8)
        trend[21:T] = code
    return dict(dates=dates, columns=np.array([str(c) for c in close.columns]), r_m=rm, n_ret=n_ret, vol_v=v, vol_pct=vp, vol_pct_strict=vs,
                vol_nref=vn, act_med=med, n_act=n_act, act_20=a20, act_pct=ap, act_pct_strict=as_, act_nref=an, trend=trend)


def high_freq(state_code):
    """p_t（plan §6.2）：T−250 … T−1 位置已定义状态中 high 的比例；当前不进；无 → .5。"""
    s = np.asarray(state_code)
    n = len(s)
    out = np.full(n, 0.5)
    defined = s >= 0
    hi = (s == 2).astype(np.int64)
    cd = np.r_[0, np.cumsum(defined.astype(np.int64))]
    ch = np.r_[0, np.cumsum(hi)]
    for t in range(n):
        a = max(0, t - LOOKBACK)
        nd = cd[t] - cd[a]
        if nd > 0:
            out[t] = (ch[t] - ch[a]) / nd
    return out


def schedule_b(name, state_code, p):
    """逐日 b（K 坏度百分位点）；state_code −1 = 未知 → 10。"""
    s = np.asarray(state_code)
    hi = s == 2
    unk = s < 0
    if name == 'VOL_HI15':
        b = np.where(hi, 15.0, 5.0)
    elif name == 'VOL_HI5':
        b = np.where(hi, 5.0, 15.0)
    elif name == 'VOL_MEAN15':
        b = 5.0 + 10.0 * np.asarray(p, float)
    elif name == 'VOL_MEAN5':
        b = 15.0 - 10.0 * np.asarray(p, float)
    else:
        raise ValueError(name)
    return np.where(unk, 10.0, b)


def cache_path():
    # 首版 state_full.npz 的 columns 存成 object 数组（allow_pickle=False 读不回，从未被使用）；只增不删：换新名
    return L.P('cache', 'state', 'state_full_E6l.npz')


def build_cache():
    st = compute()
    code = tercile(st['vol_pct'])
    code_s = tercile(st['vol_pct_strict'])
    p = high_freq(code)
    p_s = high_freq(code_s)
    out = dict(st)
    out['dates'] = np.array([d.strftime('%Y-%m-%d') for d in st['dates']])
    out.update(vol_state=code, vol_state_strict=code_s, act_state=tercile(st['act_pct']), act_state_strict=tercile(st['act_pct_strict']),
               p_high=p, p_high_strict=p_s)
    for nm in SCHEDULES:
        out['b_' + nm] = schedule_b(nm, code, p)
        out['bS_' + nm] = schedule_b(nm, code_s, p_s)
    os.makedirs(os.path.dirname(cache_path()), exist_ok=True)
    L.atomic_write_npz(cache_path(), **out)
    return out


def load_cache():
    global CACHE
    if CACHE is None:
        CACHE = L.npz(cache_path())
    return CACHE


def seg_view(seg_dates, seg_cols=None):
    """全程缓存 → 段日期（逐日对齐；段日期必须都在全程日历里）。seg_cols（ticker 列表）给则另返回 trend 子表。"""
    C = load_cache()
    fd = pd.Index(C['dates'])
    sd = pd.Index([pd.Timestamp(str(d)).strftime('%Y-%m-%d') for d in seg_dates])
    ix = fd.get_indexer(sd)
    if (ix < 0).any():
        raise RuntimeError('段日期不在全程状态日历里：%s' % list(sd[ix < 0][:3]))
    out = {k: np.asarray(C[k])[ix] for k in C if k not in ('dates', 'columns', 'trend')}
    out['dates'] = sd
    if seg_cols is not None:
        cix = pd.Index(C['columns']).get_indexer(pd.Index([str(c) for c in seg_cols]))
        tr = np.full((len(ix), len(cix)), -1, np.int8)
        okc = cix >= 0
        tr[:, okc] = C['trend'][ix][:, cix[okc]]
        out['trend'] = tr
    return out
