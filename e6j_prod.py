# -*- coding: utf-8 -*-
"""E6j 生产路径（brief v1.2 W04 / W05）。
`export_delivery_pools_v2.py` 没有 main 保护，import 即写交付目录，故不 import；其 helper 与逐段流水线在本文件逐字复制
（`# ---- verbatim` 段；与源的差别只有：函数封装、E7 截止守卫、不写交付目录）。
α = 0 / C0 必须逐位重现 E5a 六个 pool2 与 summary.csv（Stage 0 锚 1，`e6j_stage0_prod_anchor.py`）。
K 槽位替换（SLOT，W05 / plan §4.2）只经 `form_masks(ctx, kq=...)` 进入；kq=None ≡ 源父（α = 0 短路）。"""
import e6j_boot  # noqa: F401  （必须先于 numpy / pandas）
import numpy as np
import pandas as pd

import e6j_core as J
from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import define_i11_signal, build_observation_pool, apply_hard_constraints
import comprehensive_factor_diagnosis as C

SRC_SCRIPT = J.CODE + '/export_delivery_pools_v2.py'
F_COND, F_TVOL, F_CR20, F_CVR = 'conditional_turnover', 'turnover_volatility_60d', 'cum_return_20d', 'CVR_20d'
SEGS = list(PERIODS.keys())
DELIV = ['A4b', 'M_mean3_v2', 'M_union3_v2', 'A4b_CVRv5', 'M_mean3_v2_CVRv5', 'M_union3_v2_CVRv5']
FNAME = {'A4b': 'A4b_pure', 'M_mean3_v2': 'Mmean_v2_pure', 'M_union3_v2': 'Munion_v2_pure',
         'A4b_CVRv5': 'A4b_cvrveto', 'M_mean3_v2_CVRv5': 'Mmean_v2_cvrveto', 'M_union3_v2_CVRv5': 'Munion_v2_cvrveto'}
RULE_OF = {'A4b': 'A4b', 'M_mean3_v2': 'Mmean', 'M_union3_v2': 'Munion',
           'A4b_CVRv5': 'A4b', 'M_mean3_v2_CVRv5': 'Mmean', 'M_union3_v2_CVRv5': 'Munion'}
ANCHORS_E4 = {  # 源脚本 ANCHORS（E4 summary.csv L1A）
    ('2010-2014', 'A4b'): 2.5046, ('2015-2018', 'A4b'): 5.0447, ('2019-2023', 'A4b'): 7.5665, ('2024-2026', 'A4b'): 8.9262,
    ('2010-2014', 'A4b_CVRv5'): 3.0584, ('2015-2018', 'A4b_CVRv5'): 6.9892, ('2019-2023', 'A4b_CVRv5'): 8.4299, ('2024-2026', 'A4b_CVRv5'): 10.3293,
    ('2010-2014', 'M_mean3_v2'): 3.5462, ('2015-2018', 'M_mean3_v2'): 7.0335, ('2019-2023', 'M_mean3_v2'): 5.5572, ('2024-2026', 'M_mean3_v2'): 6.3298,
}
POOL1_MD5 = '6006780eb791fe6a7f66e3829cb23763'


# ---- verbatim helpers (export_delivery_pools_v2.py :37–89) ----
def is_bse(code):
    s = str(code); return s[:1] in ('4','8') or s[:2]=='92'

def nw_stats(x, L=5):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n=len(x)
    if n==0: return float('nan'),float('nan'),float('nan'),0
    mu=x.mean(); sd=x.std(ddof=1)
    naive = mu/(sd/np.sqrt(n)) if sd>0 else float('nan')
    e=x-mu; S=(e@e)/n
    for l in range(1,L+1):
        w=1.0-l/(L+1.0); S+=2.0*w*(e[l:]@e[:-l])/n
    se=np.sqrt(S/n) if S>0 else float('nan')
    nw= mu/se if (se==se and se>0) else float('nan')
    return mu*252*100.0, naive, nw, n

def pct_cache(cache): return {d: s.rank(pct=True) for d,s in cache.items()}

def combine(caches, how):
    keys=set(caches[0])
    for c in caches[1:]: keys &= set(c)
    out={}
    for d in keys:
        df=pd.concat([c[d] for c in caches], axis=1)
        out[d]= df.max(axis=1) if how=='max' else (df.median(axis=1) if how=='median' else df.mean(axis=1))
    return out

def bench_industry_shares(clean_df, industry_df):
    cl=clean_df.values; ind=industry_df.values if industry_df is not None else None; shares=[]
    for t in range(cl.shape[0]):
        idx=np.where(cl[t]==1)[0]; tot=len(idx)
        if tot==0 or ind is None: shares.append({}); continue
        vc=pd.Series(ind[t,idx]).value_counts(dropna=True); shares.append((vc/tot).to_dict())
    return shares

def assign_weights_dev(holdings, industry_df, shares, max_stock=0.01, max_ind_dev=0.03):
    h=holdings.values; ind=industry_df.values if industry_df is not None else None
    T,N=h.shape; out=np.zeros((T,N))
    for t in range(T):
        sel=np.where(h[t]==1)[0]; n=len(sel)
        if n==0: continue
        w=np.full(n, min(1.0/n, max_stock))
        if ind is not None and shares[t]:
            si=pd.Series(ind[t,sel])
            for indcode,grp in si.groupby(si).groups.items():
                gi=np.asarray(grp,dtype=int); cap=shares[t].get(indcode,0.0)+max_ind_dev; ssum=w[gi].sum()
                if ssum>cap: w[gi]*=cap/ssum
        out[t,sel]=w
    return pd.DataFrame(out, index=holdings.index, columns=holdings.columns)

def drop_mask(neu_f, pool0, k=2):  # worst tail (top group, high=worst) flagged for drop
    kept=C.build_factor_strategy_holdings_cached(neu_f, pool0, k, [k])
    return (pool0.values==1) & ~(kept.values==1)

def st(x): return nw_stats(np.asarray(x, float))
# ---- end verbatim helpers ----


def build_period(pname):
    """源脚本 :96–119 的逐段准备（逐字），外加 E7 截止守卫。返回后续一切掩码 / 账户共用的上下文。"""
    ps, pe = PERIODS[pname]
    J.assert_end_ok(pe, 'PERIODS[%s]' % pname)
    data = load_all_daily_data(start_date=ps, end_date=pe)
    J.assert_index_ok(data['close'].index, 'data[close] %s' % pname)
    J.assert_index_ok(data['vwap'].index, 'data[vwap] %s' % pname)
    feats = calc_all_daily_features(data)
    close = data['close']; bse = [c for c in close.columns if is_bse(c)]
    base_pool = get_base_pool(data)
    mature = close.notna().astype(float).rolling(20, min_periods=1).sum() >= 20
    clean = ((base_pool == 1) & mature).astype(float)
    if bse: clean[bse] = 0.0
    signal = define_i11_signal(feats, base_pool)
    obs = build_observation_pool(signal, obs_window=5)
    pool0 = apply_hard_constraints(obs, data, feats, min_mcap=0)
    log_mcap = C.compute_log_mcap(data.get('mcap'))
    industry = data.get('industry_zx1', data.get('industry'))
    if industry is not None:
        industry = industry.reindex(index=close.index, columns=close.columns)
    shares = bench_industry_shares(clean, industry)
    specs = {s['name']: s for s in C.get_default_factor_specs()}

    def neu(fname): return C.precompute_neutralized_factor(specs[fname]['func'](data, feats, industry), pool0, log_mcap)

    fac_tvol = specs[F_TVOL]['func'](data, feats, industry)
    neu_cond = neu(F_COND); neu_tvol = neu(F_TVOL); neu_cr20 = neu(F_CR20); neu_cvr = neu(F_CVR)
    pcond, ptvol, pcr20 = pct_cache(neu_cond), pct_cache(neu_tvol), pct_cache(neu_cr20)
    p0 = (pool0.values == 1)
    col_ids = np.array([int(str(c).split('.')[0]) for c in pool0.columns], dtype=np.int64)
    date_ids = np.array([pd.Timestamp(str(d)).strftime('%Y-%m-%d') for d in pool0.index])
    return dict(pname=pname, ps=ps, pe=pe, data=data, feats=feats, clean=clean, pool0=pool0, p0=p0, log_mcap=log_mcap,
                industry=industry, shares=shares, specs=specs, fac_tvol=fac_tvol,
                neu_cond=neu_cond, neu_tvol=neu_tvol, neu_cr20=neu_cr20, neu_cvr=neu_cvr,
                pcond=pcond, ptvol=ptvol, pcr20=pcr20, col_ids=col_ids, date_ids=date_ids)


def form_masks(ctx, kq=None):
    """六形态布尔掩码（T×N）。kq=None：源父逐字（:120–128）。
    kq = K 槽位的生产坐标 pct 缓存（dict 日期 → Series，定义域 = pcond 的定义域；FALLBACK 由调用方做好）时按 W05 / plan §4.2 接入：
      A4b    —— kq 进第一关 build(...,2,[2])；第二关 tvol 沿源在幸存集内中性化；
      Mmean  —— kq 替换 combine([pcond,ptvol,pcr20],'mean') 里的 pcond；
      Munion —— kq 的剔尾集替换 cond 的剔尾集，再与 tvol / cr20 剔尾集取并集之外；
      CVRv5 否决不变。"""
    pool0, p0, log_mcap = ctx['pool0'], ctx['p0'], ctx['log_mcap']
    first = ctx['neu_cond'] if kq is None else kq
    mean_leg = ctx['pcond'] if kq is None else kq
    hc = C.build_factor_strategy_holdings_cached(first, pool0, 2, [2])
    m_a4b = (C.build_factor_strategy_holdings_cached(
        C.precompute_neutralized_factor(ctx['fac_tvol'], hc, log_mcap), hc, 2, [2]).values == 1)
    m_mean3 = (C.build_factor_strategy_holdings_cached(combine([mean_leg, ctx['ptvol'], ctx['pcr20']], 'mean'), pool0, 2, [2]).values == 1)
    dc, dt, dr = drop_mask(first, pool0), drop_mask(ctx['neu_tvol'], pool0), drop_mask(ctx['neu_cr20'], pool0)
    m_union3 = (p0 & ((dc.astype(int) + dt.astype(int) + dr.astype(int)) == 0))
    tox_cvr = drop_mask(ctx['neu_cvr'], pool0, 5)
    return {'A4b': m_a4b, 'M_mean3_v2': m_mean3, 'M_union3_v2': m_union3,
            'A4b_CVRv5': (m_a4b & ~tox_cvr), 'M_mean3_v2_CVRv5': (m_mean3 & ~tox_cvr), 'M_union3_v2_CVRv5': (m_union3 & ~tox_cvr)}


def weights_of(ctx, mask):
    hold = pd.DataFrame(mask.astype(float), index=ctx['pool0'].index, columns=ctx['pool0'].columns)
    return hold, assign_weights_dev(hold, ctx['industry'], ctx['shares'])


def pool_bench(ctx, cost_bp=6.0):
    """源 :131–133 副基准：pool0 DEV 同机制；bm2 与成本无关。"""
    p0 = ctx['p0']; pool0 = ctx['pool0']
    w_pool = assign_weights_dev(pd.DataFrame(p0.astype(float), index=pool0.index, columns=pool0.columns), ctx['industry'], ctx['shares'])
    pr_pool = C.compute_calendar_pnl(w_pool, ctx['data'], ctx['clean'], hold_days=5, cost_bp_bilateral=cost_bp)
    bm2 = pr_pool['port_daily'] / pr_pool['daily_position'].replace(0, np.nan)
    return w_pool, pr_pool, bm2


def summary_row(pname, cfg, hold, w, pr, bm2, cost_bp):
    """源 :143–148 的一行 summary（cost_bp 同时用于 net2 的成本项；源固定 6.0）。"""
    nh = (hold > 0).sum(axis=1); pos = w.sum(axis=1)
    nann, _, nnw, n = st(pr['net_excess_daily']); gann, _, _, _ = st(pr['gross_excess_daily'])
    mm = C.calendar_pnl_metrics(pr['net_excess_daily']); mdd = mm['mdd'] if mm else np.nan
    ex2 = pr['port_daily'] - bm2 * pr['daily_position']; net2 = ex2 - pr['daily_turnover'] * cost_bp / 1e4
    n2ann, _, n2nw, _ = st(net2)
    return dict(period=pname, cfg=cfg, net_ann=nann, net_nw=nnw, gross_ann=gann, mdd_net=mdd, net2_ann=n2ann, net2_nw=n2nw,
                avg_nh=float(nh[nh > 0].mean()), avg_pos=float(pos[pos > 0].mean()), turn=float(pr['turnover_annual']), n=n), net2


def pool2_part(ctx, w):
    wv = w.values; rr, cc = np.nonzero(wv)
    return pd.DataFrame({'ticker': ctx['col_ids'][cc], 'tradeDate': ctx['date_ids'][rr], 'weight': wv[rr, cc]})


def pool1_part(ctx):
    rr, cc = np.nonzero(ctx['p0'])
    return pd.DataFrame({'ticker': ctx['col_ids'][cc], 'tradeDate': ctx['date_ids'][rr], 'in_pool': np.int8(1)})


def pool2_bytes(parts):
    """源 :170–171：拼接 → 按 tradeDate, ticker 排序 → '%.8g'。返回 (bytes, DataFrame)。"""
    dfp = pd.concat(parts, ignore_index=True).sort_values(['tradeDate', 'ticker']).reset_index(drop=True)
    return dfp.to_csv(index=False, float_format='%.8g').encode('utf-8'), dfp


def pool1_bytes(parts):
    p1 = pd.concat(parts, ignore_index=True).sort_values(['tradeDate', 'ticker']).reset_index(drop=True)
    return p1.to_csv(index=False).encode('utf-8'), p1
