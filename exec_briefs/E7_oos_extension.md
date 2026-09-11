# E7 —— 延长样本（2026-03-28 → 2026-09-02）：辅助数据刷新与对账 + OOS 符号检查 + 逐年 Δ 表

> **入库副本脱敏说明（2026-09-11）**：本仓库为 PUBLIC。按 `00_协议.md` §7「不写用户名；旧文档里的登录信息也不得转抄」，入库副本把同事账号名替换成了占位符（`ACCT0` / `ACCT_A`…`ACCT_H` / `ACCT_LIB`）。**除这些标识符外一字未改**；真实映射见用户本地原件，不入库。

> **⏸ HOLD（2026-09-04 规划 session）：本 brief 暂不执行。** 原因：延长样本只能"看一次"，看过之后它对任何后续再设计都不再是 OOS。用户 09-04 对样本内分析提出了四项复核（深度只测三点、否决层过简、pool 与主题划分、结论粗糙），需先做 E6c 把样本内设计定稿，再开 E7。执行端见到本行即不开工；解除 HOLD 由规划 session 删除本段并更新自审记录。

用途：样本内探索到 E6b 已饱和（三否决无增量、sleeve 与 1/N 全劣于 A4b）。E7 把候选拿到**从未触碰的五个月**上看，并用逐年拆分把样本内证据从 4 段细化到 17 年。**先说清能得到什么**：约 105 个交易日的年化超额标准误约 10 个点、配对 Δ 的标准误约 2～3 个点，这段数据只能做**符号检查、失败探测和 z 分数**，不能"确证"。本步仍只出表，不淘汰。前置：`E6b_REPORT.md`（commit `93b0d4e`）。先读 `00_协议.md`。

## 0. 背景（读懂再动手）
- **数据现状（2026-09-04 核）**：日线 `daily_temp3/` 到 2026-09-02；FundamentalTL 源表（`limitUpPrice / limitDownPrice / flag_buy / flag_sell / flag_st_new / industry_zx_1_all .csv`）9 月 3 日刚刷新；但我们的辅助缓存 `…/data/cache/ftl_*.parquet` 止于 **2026-05-20**，且加载器是缓存优先、按文件名命中。所以延长窗口必须换一个**新缓存目录**重建辅助表，旧缓存一个不删、一个不改。
- **7a 一致性对账**：用新缓存跑 E6b 的 2024-2026 段（20240101–20260327），比四个配置的 net 与 E6b `scan_all.csv` 的 `net_2024`。源表可能被修订（ST 标记、行业映射），差异**报告不中止**；|d|>0.5 时额外报告 pool0 日均规模与 ST 标记数的变化。
- **7b OOS**：加载 20250401–20260902（前 12 个月是特征暖机），全窗口算持仓与引擎，**只取 2026-03-30 起的日序列**作 OOS。每配置报：天数、累计净超额 %、年化、NW t、日命中率、MDD、对底座的 Δ（年化与 t）、对样本内分布的 z 分数（用 E6/E6b `daily_all.parquet` 的样本内日均值与日标准差）。
- **逐年 Δ 表**：不跑新数据，从 E6b/E6 的 `daily_all.parquet` 把 shortlist 配置对其底座的 Δ 按年拆（2010–2026 共 17 年），计正年数；v2 六形态按年报净值。
- 配置约 84 个：v1 六形态（reversal_skip1 取负 + cmf 否决，E2 构造）、v2 六形态、4 个底座、单否决 6 因子 × k{5,10} × 3 底座、双否决 5 对 × 2 档 × 3 底座、`P_AC@30 / P_ABC@30` 参照。名字与 E6b 一致，方便对表。
- 单进程顺序：辅助表重建约 5～10 分钟（读 5 个 300～500 MB CSV 并 pivot）+ 两次日线加载 + 两条 pipeline + 88 次引擎 ≈ **20～30 分钟**（用户已知悉）；超过 60 分钟报告。

## 1. 起点确认（任一不符 → 停，写 BLOCKERS）
1. 47 上 `git log -1 --oneline` = `93b0d4e`；`git status -sb` 首行 `## main...origin/main`；untracked 仍只有那 3 个。
2. `ls /mnt/big/base/ACCT_E/KLines_make/daily_temp3/ | tail -1` = `20260902.csv`；`ls -la /mnt/big/base/public/FundamentalTL/base_data/base_factor/flag_st_new.csv` 的 mtime 为 2026-09-03 或更新。
3. `results/20260904_1202_E6b_stack_sleeves/{scan_all.csv,daily_all.parquet}` 与 `results/20260904_1051_E6_wide_scan/daily_all.parquet` 在。
4. 新缓存目录 `/mnt/sda2/lichenchen/data/cache_ext20260902/` **不存在**（脚本创建）；`df -h /mnt/sda2 | tail -1` 可用 >50 GB；`ps` 无本项目残留；负载 <5。

## 2. 新建 `e7_oos_extension.py`（project_core 根目录，import-only，只读地基；只写新缓存目录与 results）

完整脚本如下。**pipeline 与 helper 逐字取自 E6b/E2；允许修语法类小错；不得改配置清单、窗口、缓存目录逻辑、成本。**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# E7 OOS EXTENSION (2026-09) -- 延长样本 2026-03-28..2026-09-02 (约 105 交易日): 只做符号检查 / 失败探测 / z 分数, 不确证, 不淘汰.
# 7a: 新缓存目录重建 FundamentalTL 辅助表 (旧缓存止于 2026-05-20, 缓存优先按名命中) + 用新缓存复跑 2024-2026 段 4 配置对账 E6b (报告不中止)
# 7b: 加载 20250401-20260902 (前 12 月暖机), 全窗口算持仓与引擎, 只取 >=2026-03-30 的日序列; ~84 配置
# 逐年 Δ 表: 从 E6b/E6 daily_all.parquet 把 shortlist 对底座的 Δ 按年拆 (2010-2026), 不跑新数据
import sys, os, time
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import comprehensive_factor_diagnosis as C           # 它会把 data_loader.PATHS['cache_dir'] 设成旧目录; 下面覆盖
import data_loader
from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import define_i11_signal, build_observation_pool, apply_hard_constraints

EXT_CACHE = '/mnt/sda2/lichenchen/data/cache_ext20260902/'
os.makedirs(EXT_CACHE, exist_ok=True)
data_loader.PATHS['cache_dir'] = EXT_CACHE          # 辅助表 (ftl_*.parquet) 将在此目录按源 CSV 重建; 旧目录不动
OUT = C.make_output_dir('E7_oos_extension'); C.setup_dual_logging(OUT); print('[out]', OUT, '| cache', EXT_CACHE, flush=True)

COST = 8.0
OOS_START = pd.Timestamp('2026-03-30'); LOAD_START, LOAD_END = '20250401', '20260902'
E6B = '/mnt/sda2/lichenchen/results/20260904_1202_E6b_stack_sleeves/'; E6 = '/mnt/sda2/lichenchen/results/20260904_1051_E6_wide_scan/'
F_COND, F_TVOL, F_REV, F_CMF, F_CR20, F_CR5, F_CR10, F_CVR, F_CVR1, F_CI5 = ('conditional_turnover', 'turnover_volatility_60d', 'reversal_skip1',
    'cmf_change_neg', 'cum_return_20d', 'cum_return_5d', 'cum_return_10d', 'CVR_20d', 'intraday_cvr_1d', 'cum_intraday_ret_5d')
SINGLES = [F_CVR1, F_CI5, F_CVR, F_CR5, F_CR10, F_CR20]                      # 全部剔高
PAIRS = [(F_CVR, F_CR5), (F_CVR, F_CR10), (F_CVR, F_CR20), (F_CVR1, F_CR5), (F_CVR1, F_CR20)]
BASES = ['A4b', 'M_mean2@keep30', 'M_mean2@keep20']
CONSIST = ['A4b', 'M_mean2@keep30', 'A4b|CVR_20d:k5', 'M_mean2@keep30|CVR_20d:k10+cum_return_5d:k10']
SHORTLIST_YEARLY = ['A4b', 'M_mean2@keep30', 'M_mean2@keep20', 'M_mean3_v2', 'M_union3_v2', 'A4b_CVRv5', 'M_mean3_v2_CVRv5', 'M_union3_v2_CVRv5',
                    'M_mean2@keep30|CVR_20d:k10+cum_return_5d:k10', 'M_mean2@keep30|CVR_20d:k5+cum_return_5d:k10', 'A4b|CVR_20d:k10+cum_return_5d:k10',
                    'A4b|intraday_cvr_1d:k10', 'M_mean2@keep30|intraday_cvr_1d:k10', 'M_mean2@keep30|CVR_20d:k5', 'M_mean2@keep20|CVR_20d:k5+cum_return_5d:k10']

# ---------- verbatim helpers (E6b / E2) ----------
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
# -------------------------------------------------

def st(x): return nw_stats(np.asarray(x, float))
def lrvar(x, L=5):
    """NW 长期方差 (与 nw_stats 同核), 供 z 分数用: 5 日重叠持有使日收益正自相关, iid 标准误会低估约 1.4 倍"""
    x = np.asarray(x, float); x = x[~np.isnan(x)]; e = x - x.mean(); S = (e @ e) / len(x)
    for l in range(1, L + 1):
        w = 1.0 - l / (L + 1.0); S += 2.0 * w * (e[l:] @ e[:-l]) / len(x)
    return S
def keep_mask(comp, pool0, keep):
    m = keep // 10
    return (C.build_factor_strategy_holdings_cached(comp, pool0, 10, list(range(m + 1, 11))).values == 1)

def build_all(start, end):
    """加载 + pipeline + 全部配置的 mask/权重. 返回 dict(name -> W) 与上下文."""
    t0 = time.time()
    data = load_all_daily_data(start_date=start, end_date=end, cache_dir=EXT_CACHE)
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
    specs['intraday_cvr_1d'] = {'name': 'intraday_cvr_1d', 'func': lambda d, f, i: d['close'] / d['vwap'] - 1}
    p0 = (pool0.values == 1)
    need = sorted(set([F_COND, F_TVOL, F_REV, F_CMF, F_CR20, F_CR5, F_CR10, F_CVR, F_CVR1, F_CI5]))
    raw = {n: specs[n]['func'](data, feats, industry) for n in need}
    neu = {n: C.precompute_neutralized_factor(raw[n], pool0, log_mcap) for n in need}
    neu_rev = {d: -s for d, s in neu[F_REV].items()}                    # v1: reversal 取负 (E2 verbatim)
    pct = {n: pct_cache(neu[n]) for n in need}; prev = pct_cache(neu_rev)
    ind_nan = float(pd.isna(industry.values[p0]).mean()) if (industry is not None and p0.any()) else -1.0   # 池内格子里行业为空的占比
    print('  [pipeline] %s..%s days=%d pool0 avg=%.1f  ST flags in window=%d  industry NaN frac(pool0)=%.3f  %.0fs' % (
        start, end, len(close.index), float(p0.sum(axis=1).mean()), int((data['flag_st'] == 1).sum().sum()) if 'flag_st' in data else -1, ind_nan, time.time() - t0), flush=True)
    # ---- masks ----
    hc = C.build_factor_strategy_holdings_cached(neu[F_COND], pool0, 2, [2])
    m_a4b = (C.build_factor_strategy_holdings_cached(C.precompute_neutralized_factor(raw[F_TVOL], hc, log_mcap), hc, 2, [2]).values == 1)
    comp2 = combine([pct[F_COND], pct[F_TVOL]], 'mean'); comp3 = combine([pct[F_COND], pct[F_TVOL], pct[F_CR20]], 'mean')
    comp3_v1 = combine([pct[F_COND], pct[F_TVOL], prev], 'mean')
    masks = {'A4b': m_a4b, 'M_mean2': keep_mask(comp2, pool0, 50), 'M_mean2@keep30': keep_mask(comp2, pool0, 30), 'M_mean2@keep20': keep_mask(comp2, pool0, 20),
             'M_mean3_v2': keep_mask(comp3, pool0, 50)}
    dc, dt, dr20, drv1 = drop_mask(neu[F_COND], pool0), drop_mask(neu[F_TVOL], pool0), drop_mask(neu[F_CR20], pool0), drop_mask(neu_rev, pool0)
    masks['M_union3_v2'] = p0 & ((dc.astype(int) + dt.astype(int) + dr20.astype(int)) == 0)
    masks['M_mean3_v1'] = (C.build_factor_strategy_holdings_cached(comp3_v1, pool0, 2, [2]).values == 1)
    masks['M_union3_v1'] = p0 & ((dc.astype(int) + dt.astype(int) + drv1.astype(int)) == 0)
    tox_cvr5 = drop_mask(neu[F_CVR], pool0, 5); tox_cmf5 = drop_mask(neu[F_CMF], pool0, 5)
    for b in ('A4b', 'M_mean3_v2', 'M_union3_v2'): masks[b + '_CVRv5'] = masks[b] & ~tox_cvr5
    for b, src in (('A4b', 'A4b'), ('M_mean3_v1', 'M_mean3_v1'), ('M_union3_v1', 'M_union3_v1')): masks[b + '_CMFv5'] = masks[src] & ~tox_cmf5
    tox = {(f, k): drop_mask(neu[f], pool0, k) for f in SINGLES for k in (5, 10)}
    for b in BASES:
        for f in SINGLES:
            for k in (5, 10): masks['%s|%s:k%d' % (b, f, k)] = masks[b] & ~tox[(f, k)]
        for fc, fb in PAIRS:
            for kc in (5, 10): masks['%s|%s:k%d+%s:k%d' % (b, fc, kc, fb, 10)] = masks[b] & ~tox[(fc, kc)] & ~tox[(fb, 10)]
    W = {n: assign_weights_dev(pd.DataFrame(m.astype(float), index=pool0.index, columns=pool0.columns), industry, shares) for n, m in masks.items()}
    # 1/N 参照 (E6b 定义): S_A@30 = M_mean2@keep30; S_B(cr20)@30; S_C(CVR20)@30
    W_SB = assign_weights_dev(pd.DataFrame(keep_mask(pct[F_CR20], pool0, 30).astype(float), index=pool0.index, columns=pool0.columns), industry, shares)
    W_SC = assign_weights_dev(pd.DataFrame(keep_mask(pct[F_CVR], pool0, 30).astype(float), index=pool0.index, columns=pool0.columns), industry, shares)
    W['P_AC@30'] = (W['M_mean2@keep30'] + W_SC) / 2; W['P_ABC@30'] = (W['M_mean2@keep30'] + W_SB + W_SC) / 3
    print('  [masks] %d configs %.0fs' % (len(W), time.time() - t0), flush=True)
    return W, data, clean

def engine(Wm, data, clean, cost=COST):
    pr = C.compute_calendar_pnl(Wm, data, clean, hold_days=5, cost_bp_bilateral=cost)
    return pr['net_excess_daily'], pr

# ================= 7a: 一致性对账 (新缓存, 2024-2026 段) =================
print('\n' + '#' * 70 + '\n7a consistency: rebuild aux caches in EXT_CACHE + rerun 2024-2026 segment', flush=True)
ps, pe = PERIODS['2024-2026']
W_c, data_c, clean_c = build_all(ps, pe)
e6b = pd.read_csv(E6B + 'scan_all.csv').set_index('cfg')
crows = []
for cfg in CONSIST:
    net, pr = engine(W_c[cfg], data_c, clean_c)
    got, _, _, _ = st(net); anc = float(e6b.loc[cfg, 'net_2024']); d = abs(got - anc)
    crows.append(dict(cfg=cfg, got=round(got, 4), e6b=anc, dabs=round(d, 4), flag=('OK' if d < 0.05 else ('SMALL' if d < 0.5 else 'LARGE'))))
    print('  [CONSIST 2024-2026] %-52s new-cache %+8.4f  E6b %+8.4f  |d|%.4f  %s' % (cfg, got, anc, d, crows[-1]['flag']), flush=True)
pd.DataFrame(crows).to_csv(os.path.join(OUT, 'consistency.csv'), index=False)
try:   # 旧 vs 新辅助表在重叠窗口的差异 (解释用)
    old = pd.read_parquet('/mnt/sda2/lichenchen/data/cache/ftl_flag_st_new.parquet'); new = pd.read_parquet(EXT_CACHE + 'ftl_flag_st_new.parquet')
    idx = old.index.intersection(new.index); idx = idx[(idx >= pd.Timestamp('2024-01-01')) & (idx <= pd.Timestamp('2026-03-27'))]
    cols = old.columns.intersection(new.columns)
    o, n = old.loc[idx, cols].fillna(0), new.loc[idx, cols].fillna(0)
    print('  [aux diff] flag_st_new 2024-01..2026-03: old ST cells=%d new ST cells=%d differing cells=%d ; new cache index max=%s' % (
        int((o == 1).sum().sum()), int((n == 1).sum().sum()), int((o != n).sum().sum()), new.index.max().date()), flush=True)
except Exception as e:
    print('  [aux diff] skipped:', repr(e)[:120], flush=True)
del W_c, data_c, clean_c

# ================= 7b: OOS =================
print('\n' + '#' * 70 + '\n7b OOS: load %s..%s, evaluate on >= %s' % (LOAD_START, LOAD_END, OOS_START.date()), flush=True)
W, data, clean = build_all(LOAD_START, LOAD_END)
daily_is = pd.concat([pd.read_parquet(E6B + 'daily_all.parquet'), pd.read_parquet(E6 + 'daily_all.parquet')], axis=1)
daily_is = daily_is.loc[:, ~daily_is.columns.duplicated()]
base_of = {}
for n in W:
    if '|' in n: base_of[n] = n.split('|')[0]
    elif n.endswith('_CVRv5') or n.endswith('_CMFv5'): base_of[n] = n[:-6]
    elif n in ('P_AC@30', 'P_ABC@30', 'M_mean2@keep30', 'M_mean2@keep20', 'M_mean2', 'M_mean3_v2', 'M_union3_v2', 'M_mean3_v1', 'M_union3_v1'): base_of[n] = 'A4b'
    else: base_of[n] = None
rows = []; oos_daily = {}
for n in W:
    net, pr = engine(W[n], data, clean)
    o = net.loc[net.index >= OOS_START].dropna(); oos_daily[n] = o
    ann, _, t, k = st(o); cum = float((1 + o).prod() - 1) * 100; hit = float((o > 0).mean()) * 100
    mm = C.calendar_pnl_metrics(o); mdd = mm['mdd'] * 100 if mm else np.nan
    pos = pr['daily_position'].loc[o.index].mean(); nh = (W[n].loc[o.index] > 0).sum(axis=1).mean(); turn = pr['daily_turnover'].loc[o.index].sum() / (len(o) / 252)
    r = dict(cfg=n, base=base_of[n], oos_days=k, oos_cum_pct=cum, oos_ann=ann, oos_t=t, oos_hit_pct=hit, oos_mdd_pct=mdd, oos_nh=nh, oos_pos=pos, oos_turn=turn)
    if n in daily_is.columns:                 # 样本内参照与 z 分数
        s = daily_is[n].dropna(); r['is_full_ann'] = s.mean() * 252 * 100; r['is_daily_sd'] = s.std()
        v = lrvar(s); r['z_oos_vs_is'] = (o.mean() - s.mean()) / np.sqrt(v / len(o)) if v > 0 else np.nan     # NW 标准误
    rows.append(r)
df = pd.DataFrame(rows).set_index('cfg')
for n in df.index:                            # Δ vs base (OOS)
    b = df.loc[n, 'base']
    if isinstance(b, str) and b in oos_daily:
        d = (oos_daily[n] - oos_daily[b]).dropna(); da, _, dt_, _ = st(d)
        df.loc[n, 'oos_dnet'] = da; df.loc[n, 'oos_dt'] = dt_; df.loc[n, 'oos_dhit_pct'] = float((d > 0).mean()) * 100
        if n in daily_is.columns and b in daily_is.columns:
            di = (daily_is[n] - daily_is[b]).dropna(); df.loc[n, 'is_dnet_full'] = di.mean() * 252 * 100
            v = lrvar(di); df.loc[n, 'z_d_oos_vs_is'] = (d.mean() - di.mean()) / np.sqrt(v / len(d)) if v > 0 else np.nan
df.to_csv(os.path.join(OUT, 'oos.csv')); pd.DataFrame(oos_daily).to_parquet(os.path.join(OUT, 'oos_daily.parquet'))

# ================= 逐年 Δ 表 (样本内, 不跑新数据) =================
yr_rows = []
for n in SHORTLIST_YEARLY:
    if n not in daily_is.columns: continue
    s = daily_is[n].dropna(); b = base_of.get(n)
    byy = s.groupby(s.index.year).mean() * 252 * 100
    r = dict(cfg=n, kind='net', base='', pos_years=int((byy > 0).sum()), n_years=len(byy), **{str(y): round(v, 2) for y, v in byy.items()})
    yr_rows.append(r)
    if isinstance(b, str) and b in daily_is.columns and b != n:
        d = (s - daily_is[b]).dropna(); byd = d.groupby(d.index.year).mean() * 252 * 100
        yr_rows.append(dict(cfg=n, kind='dnet_vs_' + b, base=b, pos_years=int((byd > 0).sum()), n_years=len(byd), **{str(y): round(v, 2) for y, v in byd.items()}))
yr = pd.DataFrame(yr_rows); yr.to_csv(os.path.join(OUT, 'yearly.csv'), index=False)

# ================= summary =================
f = open(os.path.join(OUT, 'summary.txt'), 'w', encoding='utf-8')
def P(s=''): print(s, flush=True); f.write(s + '\n')
P('E7  OOS %s..%s  (%d 交易日; 年化数字标准误约 10 点、Δ 约 2-3 点 —— 只看符号 / 失败探测 / z)' % (OOS_START.date(), LOAD_END, int(df.oos_days.max())))
P('\n== 7a 一致性 (新缓存重跑 2024-2026 段 vs E6b)'); P(pd.DataFrame(crows).to_string(index=False))
def fmt(v, w='%+6.2f'): return (w % v) if pd.notna(v) else '   nan'
def line(n):
    r = df.loc[n]
    s = '  %-52s cum %s%% ann %s t %s hit %s%% mdd %s%% | nh %5.1f pos %.2f turn %4.1f' % (n, fmt(r.oos_cum_pct, '%+5.2f'), fmt(r.oos_ann), fmt(r.oos_t, '%+4.2f'), fmt(r.oos_hit_pct, '%4.1f'), fmt(r.oos_mdd_pct, '%5.2f'), r.oos_nh, r.oos_pos, r.oos_turn)
    if pd.notna(r.get('is_full_ann', np.nan)): s += ' | IS full %s z %s' % (fmt(r.is_full_ann), fmt(r.z_oos_vs_is, '%+4.2f'))
    if pd.notna(r.get('oos_dnet', np.nan)): s += ' | Δ vs %s: %s (t %s, hit %s%%; IS %s, z %s)' % (r.base, fmt(r.oos_dnet), fmt(r.oos_dt, '%+4.2f'), fmt(r.oos_dhit_pct, '%4.1f'), fmt(r.get('is_dnet_full', np.nan)), fmt(r.get('z_d_oos_vs_is', np.nan), '%+4.2f'))
    return s
P('\n== v1 六形态 (7/8 交付; reversal_skip1 + cmf 否决)'); [P(line(n)) for n in ['M_mean3_v1', 'A4b', 'M_union3_v1', 'M_mean3_v1_CMFv5', 'A4b_CMFv5', 'M_union3_v1_CMFv5']]
P('\n== v2 六形态 (9/3 交付; cum_return_20d + CVR 否决)'); [P(line(n)) for n in ['A4b', 'M_mean3_v2', 'M_union3_v2', 'A4b_CVRv5', 'M_mean3_v2_CVRv5', 'M_union3_v2_CVRv5']]
P('\n== 底座 + 1/N 参照'); [P(line(n)) for n in ['A4b', 'M_mean2', 'M_mean2@keep30', 'M_mean2@keep20', 'P_AC@30', 'P_ABC@30']]
for b in BASES:
    P('\n== 单否决 on %s (按 OOS Δ 降序)' % b); [P(line(n)) for n in df[(df.base == b) & df.index.str.contains(r'\|') & ~df.index.str.contains(r'\+')].sort_values('oos_dnet', ascending=False).index]
    P('\n== 双否决 on %s (按 OOS Δ 降序)' % b); [P(line(n)) for n in df[(df.base == b) & df.index.str.contains(r'\+')].sort_values('oos_dnet', ascending=False).index]
P('\n== 符号汇总: 单否决 OOS Δ>0 占比 %.0f%% (n=%d); 双否决 %.0f%% (n=%d); v2 六形态 OOS 累计超额 >0 的 %d/6; v1 %d/6' % (
    100 * (df[df.index.str.contains(r'\|') & ~df.index.str.contains(r'\+')].oos_dnet > 0).mean(), int((df.index.str.contains(r'\|') & ~df.index.str.contains(r'\+')).sum()),
    100 * (df[df.index.str.contains(r'\+')].oos_dnet > 0).mean(), int(df.index.str.contains(r'\+').sum()),
    int((df.loc[['A4b', 'M_mean3_v2', 'M_union3_v2', 'A4b_CVRv5', 'M_mean3_v2_CVRv5', 'M_union3_v2_CVRv5']].oos_cum_pct > 0).sum()),
    int((df.loc[['M_mean3_v1', 'A4b', 'M_union3_v1', 'M_mean3_v1_CMFv5', 'A4b_CMFv5', 'M_union3_v1_CMFv5']].oos_cum_pct > 0).sum())))
P('\n== 逐年表 (样本内 2010-2026; net 与 Δ 年化 %; pos_years/n_years)')
pd.set_option('display.width', 400); P(yr.to_string(index=False))
P('\n[ALLDONE] %s  configs=%d' % (OUT, len(df))); f.close()
```

跑法：
```bash
cd /mnt/sda2/lichenchen/code/project_core
python -c "import ast; ast.parse(open('e7_oos_extension.py').read()); print('syntax OK')"
# 预检: %-格式串全扫 (哑元); build_all 里 print 的 industry NaN 表达式用一个 3×3 假 DataFrame 单测一次
setsid nohup taskset -c 96-191,288-383 python -u e7_oos_extension.py > /tmp/E7_oos.log 2>&1 &
# 轮询 tail -3 /tmp/E7_oos.log, 间隔 ≥120 s; 关注 '[cache] Saved' 行 (辅助表重建) 与 '[pipeline]' 行
```
预计 20–30 分钟；超过 60 分钟报告。

## 3. 验收（齐不齐 + 数据是否就位；没有采纳判断）
- **G7-1 缓存**：`ls /mnt/sda2/lichenchen/data/cache_ext20260902/` 含 6 个 `ftl_*.parquet` 与 2 个 `daily_kline_*.parquet`；用一行 python 打印 6 个 `ftl_*` 的 `index.max()`，都应 ≥ 2026-09-01。旧目录 `…/data/cache/` 文件数与 mtime **不变**（`ls -la` 前后各存一份对比）。
- **G7-2 一致性**：`consistency.csv` 4 行，flag 与 |d| 原样进 REPORT；`[aux diff]` 行原样进 REPORT。任何 `LARGE` 都不是 BLOCKER，只报告。
- **G7-3 OOS**：`oos.csv` 行数 = 配置数（约 84～88）；`oos_days` 全部相同且在 100～110 之间；`oos_daily.parquet` 列数同；无 `nan` 的 `oos_cum_pct`。
- **G7-4 逐年**：`yearly.csv` 行数 = shortlist 可得配置数 × 2 − 1（`A4b` 无 Δ 行），年份列 2010…2026。
- **G7-5 暖机**：`[pipeline] 20250401..20260902` 行的 `pool0 avg` 与 2024-2026 段（E6b 约 483）同量级；`industry NaN frac(pool0)` 写进 REPORT。

## 4. 交回
- `git add e7_oos_extension.py && git commit -m "E7 延长样本: 新缓存目录重建 FundamentalTL 辅助表 + 2024-26 段一致性对账 + OOS 2026-03-30..09-02 (~84 配置: v1/v2 六形态、3 底座、单/双否决、1/N 参照) + 逐年 Δ 表 (results/<ts>_E7_oos_extension)" && git push origin main`；`scp` 回本地 `_remote_tmp/`。
- `exec_briefs/E7_REPORT.md`：起点确认；G7-1～5；`summary.txt` **全文原样**（它不长）；缓存重建耗时与总耗时；results 目录、日志、commit、push；纯文本摘要 ≤15 行（只写规模、一致性结果、符号汇总那一行、v2 六形态 OOS 累计超额、逐年表的 pos_years，**不写任何"确证 / 该进 / 该退"**）；BLOCKERS。
- WORKLOG 一条（远端 + 本地 `_tmp_WORKLOG.md` 同文）。

## 5. 禁区
四个地基文件不动；不改引擎；不改配置清单 / 窗口 / 成本；**旧缓存目录 `…/data/cache/` 一个文件不删不改**；不重出交付；不碰公共库；不删 results；REPORT 不下确证 / 采纳 / 淘汰判断；结果数字不外发；文档与日志不出现登录信息与主机地址。凡遇"必须改上述任何一项才能继续" → 停，写 BLOCKERS，交回。

## 6. 自审记录（规划 session 2026-09-04；执行端见此段方可开工）
| 类 | 不利因素 | 处置 |
|---|---|---|
| 数据 | 辅助缓存止于 2026-05-20，加载器缓存优先按名命中；直接跑延长窗口会拿到过期的 ST / 涨跌停 / 行业 | 新缓存目录 + 覆盖 `data_loader.PATHS['cache_dir']`，辅助表按 9 月 3 日源 CSV 重建；G7-1 核 `index.max()` |
| 数据 | 源 CSV 刷新可能修订了历史（ST 标记、行业映射），使新缓存下的 2024-26 段与 E6b 不一致 | 7a 对账 4 配置，报告不中止；`[aux diff]` 行量化重叠窗口 ST 标记差异 |
| 数据 | 特征需暖机（tvol 60 日、CVR 20 日、次新 20 日、信号窗口 5 日） | 从 2025-04-01 加载，OOS 起点 2026-03-30 有 12 个月暖机；G7-5 核 pool0 规模 |
| 数据 | 新上市股票在行业表里可能为 NaN → DEV 视为不受行业约束 | `[pipeline]` 行打印池内行业 NaN 占比，写进 REPORT |
| 统计 | 105 个交易日的年化超额标准误约 10 点、Δ 约 2～3 点，无法"确证" | 报累计超额、命中率、z 分数与 Δ 符号；summary 首行写明；REPORT 与后续解读都不说"确证" |
| 统计 | v1 / v2 / 单 / 双否决 80 多个配置在 OOS 上"挑最好"仍是挑最大值 | 加"符号汇总"行（各类 OOS Δ>0 占比），并以 4 段 + 逐年表（17 年正年数）作主要稳健性证据 |
| 统计 | 样本内 `daily_is` 来自 E6b 与 E6 两个目录，同名配置以 E6b 为准 | 合并后去重列，E6b 在前 |
| 代码 | `data_loader.PATHS['cache_dir']` 在 `import comprehensive_factor_diagnosis` 时被设成旧目录 | 覆盖放在 import 之后、任何加载之前；`load_all_daily_data(cache_dir=EXT_CACHE)` 再显式传一次 |
| 代码 | `[pipeline]` 行里行业 NaN 占比初稿用 `to_numeric(stack())`，对 object 列可能全 NaN 或抛错 | 已改成 `pd.isna(industry.values[p0]).mean()`（布尔掩码直接取池内格子），无类型转换 |
| 统计 | z 分数若用 iid 日标准差，5 日重叠持有的正自相关会让标准误低估约 1.4 倍、z 虚高 | z 的标准误改用 NW 长期方差（`lrvar`，与 `nw_stats` 同核） |
| 代码 | `%` 格式串（E5a / E6 教训）；`summary` 里含 `%%` 的行都带 `%` 运算符 | 逐条核过；跑前哑元全扫 |
| 代码 | v1 形态的 reversal 取负与 cmf k5 否决必须与 E2 构造逐字一致，否则 v1 的 OOS 数字不可比 | 从 E2 逐字搬（`neu_rev = -neu`、`drop_mask(neu_cmf, pool0, 5)`） |
| 运行 | 单进程 20～30 分钟，辅助表重建读 5 个 300～500 MB CSV | 只重建一次落盘到新目录；若中途失败重跑时缓存已在，第二次快得多 |
| 运行 | 磁盘：新缓存目录约 2～3 GB | 起点确认核 >50 GB 可用 |
| 解读 | OOS 上 v1（旧口径下选出的形态）与 v2 都会被拿来比，容易读成"哪个更好" | 两组并排只作记录；判读时以符号与 z 为主，规划 session 负责措辞 |

方向确认：目标是"把样本内已饱和的候选拿到未触碰样本上看符号与失败探测，并把稳健性证据细化到年"，与"探索从宽、采纳只在 OOS 与用户过目"一致；本步仍不淘汰。OOS 之后的采纳决定由用户在看完 E7 表后做。
