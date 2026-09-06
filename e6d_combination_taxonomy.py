#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# E6d 合成核结构分类学 (2026-09-05)
#   四种两因子做法在等浓度下的并排: DEP(依赖排序) / DEPnr(只换排序范围不换中性化范围) /
#   IND(独立交集, 浓度浮动) / CMEAN@25 / CMAX@25 (+ CMEAN@50 历史口径)
#   + 单因子 @50/@25 基线(项目从未跑过 25%) + 三因子第三阶段 相对 vs 绝对 + 阶段深度变体
# 探索从宽: 不预筛, 不设盈利闸门, 全部报出; 统计量只作列不作闸.
# 用法:
#   python e6d_combination_taxonomy.py --prereg --out DIR
#   python e6d_combination_taxonomy.py --period <seg> --phase A --out DIR
#   python e6d_combination_taxonomy.py --select-parents --out DIR
#   python e6d_combination_taxonomy.py --period <seg> --phase C --out DIR
import sys, os, argparse, time, json, hashlib, platform
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import define_i11_signal, build_observation_pool, apply_hard_constraints
import comprehensive_factor_diagnosis as C

ap = argparse.ArgumentParser()
ap.add_argument('--period', default=None)
ap.add_argument('--phase', default='A', choices=['A', 'C'])
ap.add_argument('--out', required=True)
ap.add_argument('--prereg', action='store_true')
ap.add_argument('--select-parents', dest='select_parents', action='store_true')
if __name__ == '__main__':
    args = ap.parse_args(); OUT = args.out; os.makedirs(OUT, exist_ok=True)
else:
    args, OUT = None, None      # 供 e6d_selftests.py import 复用构造函数

COST, COST_HI = 8.0, 12.0
E6_DIR   = '/mnt/sda2/lichenchen/results/20260904_1051_E6_wide_scan'
E6B_SCAN = '/mnt/sda2/lichenchen/results/20260904_1202_E6b_stack_sleeves/scan_all.csv'
ROLES_CSV = os.path.join(E6_DIR, 'roles.csv')
TOL = 0.02
SEGS = list(PERIODS.keys())

F12 = ['conditional_turnover', 'turnover_volatility_60d', 'CVR_20d', 'intraday_cvr_1d', 'cum_intraday_ret_5d',
       'cum_return_5d', 'cum_return_20d', 'max_abs_return_10d', 'stealth_score',
       'drawdown_volume_ratio', 'reversal_skip1', 'abn_turnover']
Z6 = ['CVR_20d', 'intraday_cvr_1d', 'cum_intraday_ret_5d', 'cum_return_5d', 'cum_return_20d', 'max_abs_return_10d']
F_COND, F_TVOL, F_CVR, F_CR5 = 'conditional_turnover', 'turnover_volatility_60d', 'CVR_20d', 'cum_return_5d'
DEPTH_GRID = [(60, 50), (50, 60), (50, 40), (40, 50), (40, 40), (60, 40), (40, 60), (70, 35)]
N_TOP, N_WORST = 6, 3
ANCH_CFG = ['A4b', 'M_mean2', 'M_mean2@keep30', 'M_mean2@keep20', 'A4b|CVR_20d:k5',
            'M_mean2@keep30|CVR_20d:k10+cum_return_5d:k10']
ANCH_DEPTH = {'A4b_var_c60_t50': (60, 50), 'A4b_var_c50_t60': (50, 60), 'A4b_var_c40_t50': (40, 50)}

_roles = pd.read_csv(ROLES_CSV).set_index('factor')
for f in F12:
    assert int(_roles.loc[f, 'worst_pooled']) in (1, 5), 'worst_pooled 必须是 1 或 5: ' + f
HB = {f: (int(_roles.loc[f, 'worst_pooled']) == 5) for f in F12}   # True = 高值是坏
HINT = {f: str(_roles.loc[f, 'role_hint']) for f in F12}
RHO = {f: float(_roles.loc[f, 'rho_mean']) for f in F12}

# ---------- verbatim helpers (e6_wide_scan.py / e6b_stack_sleeves.py) ----------
def is_bse(code):
    s = str(code); return s[:1] in ('4', '8') or s[:2] == '92'

def nw_stats(x, L=5):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    if n == 0: return float('nan'), float('nan'), float('nan'), 0
    mu = x.mean(); sd = x.std(ddof=1)
    naive = mu / (sd / np.sqrt(n)) if sd > 0 else float('nan')
    e = x - mu; S = (e @ e) / n
    for l in range(1, L + 1):
        w = 1.0 - l / (L + 1.0); S += 2.0 * w * (e[l:] @ e[:-l]) / n
    se = np.sqrt(S / n) if S > 0 else float('nan')
    nw = mu / se if (se == se and se > 0) else float('nan')
    return mu * 252 * 100.0, naive, nw, n

def pct_cache(cache): return {d: s.rank(pct=True) for d, s in cache.items()}

def combine(caches, how):
    keys = set(caches[0])
    for c in caches[1:]: keys &= set(c)
    out = {}
    for d in keys:
        df = pd.concat([c[d] for c in caches], axis=1)
        out[d] = df.max(axis=1) if how == 'max' else (df.median(axis=1) if how == 'median' else df.mean(axis=1))
    return out

def bench_industry_shares(clean_df, industry_df):
    cl = clean_df.values; ind = industry_df.values if industry_df is not None else None; shares = []
    for t in range(cl.shape[0]):
        idx = np.where(cl[t] == 1)[0]; tot = len(idx)
        if tot == 0 or ind is None: shares.append({}); continue
        vc = pd.Series(ind[t, idx]).value_counts(dropna=True); shares.append((vc / tot).to_dict())
    return shares

def assign_weights_dev(holdings, industry_df, shares, max_stock=0.01, max_ind_dev=0.03):
    h = holdings.values; ind = industry_df.values if industry_df is not None else None
    T, N = h.shape; out = np.zeros((T, N))
    for t in range(T):
        sel = np.where(h[t] == 1)[0]; n = len(sel)
        if n == 0: continue
        w = np.full(n, min(1.0 / n, max_stock))
        if ind is not None and shares[t]:
            si = pd.Series(ind[t, sel])
            for indcode, grp in si.groupby(si).groups.items():
                gi = np.asarray(grp, dtype=int); cap = shares[t].get(indcode, 0.0) + max_ind_dev; ssum = w[gi].sum()
                if ssum > cap: w[gi] *= cap / ssum
        out[t, sel] = w
    return pd.DataFrame(out, index=holdings.index, columns=holdings.columns)

def st(x): return nw_stats(np.asarray(x, float))
# ------------------------------------------------------------------------------

def dgroups(high_bad, n, keep_g):
    """保留最好的 keep_g 组(共 n 组), 返回要丢的组号 (与 e6/e6b 的 [2]/[1]/[k] 约定一致)"""
    return list(range(keep_g + 1, n + 1)) if high_bad else list(range(1, n - keep_g + 1))

def holds(cache, pool, n, keep_g, high_bad=True):
    return C.build_factor_strategy_holdings_cached(cache, pool, n, dgroups(high_bad, n, keep_g))

def mk(df): return (df.values == 1)

def pct_or(cache, high_bad):
    """定向 pct: 统一成 高 = 坏"""
    p = pct_cache(cache)
    return p if high_bad else {d: 1.0 - s for d, s in p.items()}

def keep_pct(cache, pool, pctkeep, high_bad=True):
    """保留最好的 pctkeep%; 10 的倍数用十分位(与 e6b keep_mask 逐字相同), 否则用 20 分位"""
    n = 10 if pctkeep % 10 == 0 else 20
    return mk(holds(cache, pool, n, int(round(n * pctkeep / 100.0)), high_bad))

def drop_or(cache, pool, k, high_bad):
    """剔最差 1/k (与 e6 drop_mask / e6b tox 逐字相同)"""
    kept = holds(cache, pool, k, k - 1, high_bad)
    return (pool.values == 1) & ~mk(kept)

def sub_cache(neu_y, stock_map):
    """把 pool0 中性化后的 Y 限制到 S1 的成员上 (不重新中性化); 门槛镜像 precompute_neutralized_factor"""
    out = {}
    for d, stk in stock_map.items():
        if len(stk) < 6: continue
        s = neu_y.get(d)
        if s is None: continue
        v = s.reindex(stk).dropna()
        if len(v) < 6: continue
        out[d] = v
    return out

def msha(m):
    return hashlib.sha256(np.ascontiguousarray(np.asarray(m, dtype=np.uint8)).tobytes()).hexdigest()[:16]

def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''): h.update(b)
    return h.hexdigest()[:16]


# ============================== 事前登记 ==============================
PREREG = u"""# E6d 事前登记 (preregistration)

登记日期 **2026-09-05**，写于任何 E6d 回测运行之前（阶段 1，早于阶段 2 的第一次引擎调用）。
本文件一经写出即不再修改；后续如需改动，另起 `preregistration_amend_<日期>.md` 并说明理由。

## 0. 本轮问题
把两个因子合成一个选股规则，**依赖排序 DEP**（先用 X 筛一半，再在保留集内对 Y 重中性化筛一半）、
**独立交集 IND**（各自筛一半取交集）、**复合均值 CMEAN**（定向 pct 取均值后筛）、
**复合最差 CMAX**（定向 pct 取逐票最大后筛），在**相同最终浓度**下哪种更好、差多少、
差别是否随因子对的相关性变化。

## 1. 假设 H-E6d-1（可证伪）
**因果句**：闸（第一阶段）的作用是"排除注定失败者"，信息集中在坏尾的**单尾**因子适合当闸；
排序器（第二阶段）要在幸存者里继续区分，需要全分布单调，故**渐变**因子适合当排序器。

**预测**：在 132 个有序对上，把 `DEP(X→Y) − CMEAN25(X,Y)` 按 (X 的 role_hint, Y 的 role_hint) 分格，
**(单尾 → 渐变) 格的中位数最高**，(渐变 → 单尾) 格最低。

**证伪条件**：若 (单尾 → 渐变) 不是四类组合中中位数最高的一格，H-E6d-1 被否。
分格用 E6 `roles.csv` 的 `role_hint`（单尾→否决候选 / 渐变→合成候选 / 中间弱），
本轮 12 因子的分布为 8 单尾 / 3 渐变 / 1 中间弱，各格样本数在报告中列出。

**协变量的样本内性质（重要）**：`role_hint` 由 E6 在**同样的四段样本**上从形状分析得出，
不是外生标签。故 H-E6d-1 是"用同样本估出的形状协变量去预测组合结构效应"的假设，
其确证力弱于用外部信息分组；报告须原样标注这一点，不得读成独立样本验证。

## 2. 结果怎么读（三种情形，事前写死）
- **情形 A**：`DEP − CMEAN25` 的分布中位数 ≈ 0 且 cond→tvol 的名次不特殊
  → 依赖排序这个**结构**不重要；A4b 的表现等价于一个 25% 浓度的复合切；生产核可简化。
- **情形 B**：中位数显著 > 0，且差随 |ρ| 增大
  → 依赖排序是**真机制**（与 Fama-French 式经验一致）；结构可推广到新因子对。
- **情形 C**：中位数 ≈ 0 但 cond→tvol 的差排在最前
  → 优势来自**这一对因子**而非结构；A4b 不可推广，新因子进池不应默认用依赖排序。
三种情形都是合法答案；本轮不设盈利闸门，不因结果好坏改判据。

## 3. 父配置选取规则（事前写死，跑完两因子后由脚本自动执行）
以 `DEP:*` 的**全窗口 net8**（四段日净超额序列按时间拼接后 mean×252×100，成本 8bp，`legacy_all` 口径）排序：
- **生产父**：`cond→tvol`（必选，无论名次）
- **top 父**：除生产父外名次最高的 6 个
- **worst 父**：名次最低的 3 个
并列时按配置名升序。共 10 个父，用于三因子第三阶段；其中生产父 + top 6 = 7 个另用于阶段深度变体。
**top/worst 都是样本内选择**，报告须标注；但"相对 vs 绝对"是同父内对比，父的选法不影响该对比的方向。

## 4. 固定项（本轮不动）
持有期 5 日；成本 8bp（12bp 由日换手解析换算，非重跑）；DEV 权重（个股 1%、行业偏离 3%、不重新归一）；
主基准 = 干净全市场等权；副基准 = `pool0_DEV`；四段 + 全窗口；`legacy_all` 口径；
I11 信号 / obs_window=5 / 池定义 / 中性化方式 / 否决阈值 全部不动；不加新因子。

## 5. 判据（硬闸只有这些，其余全是诊断列）
- 外部锚 24 格：6 个配置 × 4 段，对 E6b `scan_all.csv` 的 8bp/H5 数值，TOL 0.02。
  **预期 `dabs` 全为 0.0**（构造与 `e6_wide_scan.py` 逐行相同）；出现"过了但不为零"按异常报告。
- 内部锚 2 条：`DEP(cond→tvol)` 的 mask SHA 必须等于 `A4b`；`CMEAN50(cond,tvol)` 必须等于 `M_mean2`。
- 阶段 C 另有 3 个深度锚：`A4b_var_c60_t50 / c50_t60 / c40_t50` 对 E6b 同名数值。
玩具测试分阻断档与软档；软档失败只记录不中止。薄日、空持仓、qcut 并列只报计数，**不加新的最少样本规则**。
"""

def write_prereg():
    p = os.path.join(OUT, 'preregistration.md')
    assert not os.path.exists(p), 'preregistration.md 已存在, 不覆盖'
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write(PREREG)
        fh.write(u'\n## 6. 12 个因子与方向（从 E6 roles.csv 读, 未手打）\n\n')
        fh.write(u'| 因子 | 轴 | worst_pooled | 方向 | role_hint | rho_mean |\n|---|---|---|---|---|---|\n')
        for f in F12:
            fh.write(u'| `%s` | %s | %d | %s | %s | %+.2f |\n' % (
                f, _roles.loc[f, 'axis'], int(_roles.loc[f, 'worst_pooled']),
                u'高=坏' if HB[f] else u'低=坏', HINT[f], RHO[f]))
    mani = dict(
        written='2026-09-05', python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
        periods={k: list(v) for k, v in PERIODS.items()}, cost_bp=COST, cost_hi_bp=COST_HI, hold_days=5,
        factors=F12, high_bad={f: bool(HB[f]) for f in F12}, role_hint=HINT, rho_mean=RHO,
        Z6=Z6, depth_grid=[list(g) for g in DEPTH_GRID], n_top=N_TOP, n_worst=N_WORST,
        anchors_external=ANCH_CFG, anchors_depth={k: list(v) for k, v in ANCH_DEPTH.items()}, tol=TOL,
        sha={os.path.basename(f): sha_file(f) for f in [
            '/mnt/sda2/lichenchen/code/project_core/e6d_combination_taxonomy.py',
            '/mnt/sda2/lichenchen/code/project_core/comprehensive_factor_diagnosis.py',
            '/mnt/sda2/lichenchen/code/project_core/data_loader.py',
            '/mnt/sda2/lichenchen/code/project_core/features_daily.py',
            '/mnt/sda2/lichenchen/code/project_core/event_study.py',
            '/mnt/sda2/lichenchen/code/project_core/pool_screening_v2.py',
            ROLES_CSV, E6B_SCAN]})
    with open(os.path.join(OUT, 'run_manifest.json'), 'w', encoding='utf-8') as fh:
        json.dump(mani, fh, ensure_ascii=False, indent=1)
    print('prereg written ->', p)


# ============================== 单段运行 ==============================
def stock_map(hdf):
    cols = np.asarray(hdf.columns); v = (hdf.values == 1)
    return {d: cols[v[i]].tolist() for i, d in enumerate(hdf.index)}

def run_period(pname, phase):
    ps, pe = PERIODS[pname]; t0 = time.time()
    log = open(os.path.join(OUT, 'log_%s_%s.txt' % (pname, phase)), 'w', encoding='utf-8')
    def P(*a):
        s = ' '.join(str(x) for x in a); print(s, flush=True); log.write(s + '\n'); log.flush()
    P('PERIOD', pname, ps, pe, 'PHASE', phase)

    # ---- pipeline (verbatim e6_wide_scan.py) ----
    data = load_all_daily_data(start_date=ps, end_date=pe)
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
    nh0s = pd.Series(p0.sum(axis=1), index=pool0.index)
    NH0 = float(nh0s[nh0s > 0].mean())
    P('pipeline %.0fs  pool0 avg=%.1f' % (time.time() - t0, NH0))

    # ---- 基础中性化 (12 因子, 两个 phase 都要) ----
    raw = {f: specs[f]['func'](data, feats, industry) for f in F12}
    neu = {f: C.precompute_neutralized_factor(raw[f], pool0, log_mcap) for f in F12}
    opct = {f: pct_or(neu[f], HB[f]) for f in F12}
    half = {f: holds(neu[f], pool0, 2, 1, HB[f]) for f in F12}
    hmask = {f: mk(half[f]) for f in F12}
    s1stk = {f: stock_map(half[f]) for f in F12}
    P('base neutralize %d factors %.0fs' % (len(F12), time.time() - t0))

    rows = []; d_net8 = {}; d_turn = {}; d_gross = {}
    def evaluate(mask, cfg, kind='', method='', X='', Y='', Z='', s1=np.nan, s2=np.nan, stage3='', k=np.nan):
        hold = pd.DataFrame(np.asarray(mask).astype(float), index=pool0.index, columns=pool0.columns)
        w = assign_weights_dev(hold, industry, shares)
        nh = (hold > 0).sum(axis=1); pos = w.sum(axis=1)
        pr = C.compute_calendar_pnl(w, data, clean, hold_days=5, cost_bp_bilateral=COST)
        net8 = pr['net_excess_daily']; turn_d = pr['daily_turnover']; gross = pr['gross_excess_daily']
        net12 = net8 - turn_d * ((COST_HI - COST) / 1e4)
        n8, _, w8, n = st(net8); n12, _, w12, _ = st(net12); g, _, _, _ = st(gross)
        mm = C.calendar_pnl_metrics(net8); mdd = mm['mdd'] if mm else np.nan
        anh = float(nh[nh > 0].mean()) if (nh > 0).any() else np.nan
        rows.append(dict(period=pname, cfg=cfg, kind=kind, method=method, X=X, Y=Y, Z=Z, s1=s1, s2=s2,
                         stage3=stage3, k=k, net8_ann=n8, nw8=w8, net12_ann=n12, nw12=w12, gross_ann=g,
                         cost_ann=g - n8, mdd_net=mdd, turn=float(pr['turnover_annual']), avg_nh=anh,
                         nh_ratio=(anh / NH0 if anh == anh else np.nan),
                         avg_pos=float(pos[pos > 0].mean()) if (pos > 0).any() else np.nan,
                         days_nohold=int((nh == 0).sum()), n=n, sha=msha(mask)))
        d_net8[cfg] = net8; d_turn[cfg] = turn_d; d_gross[cfg] = gross
        return n8

    # ---- 锚点配置 (两个 phase 都算, 保证每段独立可核) ----
    comp2 = combine([opct[F_COND], opct[F_TVOL]], 'mean')
    m_mean2 = mk(holds(comp2, pool0, 2, 1, True))
    m_k30 = keep_pct(comp2, pool0, 30); m_k20 = keep_pct(comp2, pool0, 20)
    tox_anchor = {(f, k): drop_or(neu[f], pool0, k, HB[f]) for f in (F_CVR, F_CR5) for k in (5, 10)}
    cA4b = C.precompute_neutralized_factor(raw[F_TVOL], half[F_COND], log_mcap)
    m_a4b = mk(holds(cA4b, half[F_COND], 2, 1, HB[F_TVOL]))
    anch = {'A4b': m_a4b, 'M_mean2': m_mean2, 'M_mean2@keep30': m_k30, 'M_mean2@keep20': m_k20,
            'A4b|CVR_20d:k5': m_a4b & ~tox_anchor[(F_CVR, 5)],
            'M_mean2@keep30|CVR_20d:k10+cum_return_5d:k10':
                m_k30 & ~tox_anchor[(F_CVR, 10)] & ~tox_anchor[(F_CR5, 10)]}
    for cfg in ANCH_CFG:
        evaluate(anch[cfg], cfg, kind='anchor')
    e6b = pd.read_csv(E6B_SCAN).set_index('cfg'); ycol = 'net_%s' % pname[:4]
    ok_all = True; nonzero = []
    for cfg in ANCH_CFG:
        got = [r['net8_ann'] for r in rows if r['cfg'] == cfg][0]
        ancv = float(e6b.loc[cfg, ycol]); d = abs(got - ancv); ok = d < TOL; ok_all &= ok
        if d != 0.0: nonzero.append((cfg, d))
        P('  [ANCHOR E6b@8bp] %-46s got %+9.4f anchor %+9.4f |d|%.8f %s' %
          (cfg, got, ancv, d, 'OK' if ok else 'FAIL!!'))
    if nonzero:
        P('  [!] 过闸但 dabs 非零 (按异常记录): ' + '; '.join('%s=%.2e' % (c, d) for c, d in nonzero))
    SHA_A4B, SHA_MEAN2 = msha(m_a4b), msha(m_mean2)
    P('  [SHA] A4b=%s  M_mean2=%s' % (SHA_A4B, SHA_MEAN2))
    if not ok_all:
        P('[ABORT] 外部锚点 FAIL in %s' % pname)
        pd.DataFrame(rows).to_csv(os.path.join(OUT, 'sf_%s_%s_ABORT.csv' % (pname, phase)), index=False)
        log.close(); sys.exit(1)
    evaluate(p0, 'pool0_DEV', kind='baseline')
    P('  anchors+baseline done %.0fs' % (time.time() - t0))
    return dict(P=P, log=log, t0=t0, data=data, feats=feats, clean=clean, pool0=pool0, p0=p0,
                industry=industry, shares=shares, log_mcap=log_mcap, specs=specs, raw=raw, neu=neu,
                opct=opct, half=half, hmask=hmask, s1stk=s1stk, rows=rows, evaluate=evaluate,
                d_net8=d_net8, d_turn=d_turn, d_gross=d_gross, NH0=NH0,
                SHA_A4B=SHA_A4B, SHA_MEAN2=SHA_MEAN2, pname=pname, phase=phase)

def finish(ctx):
    OUTP = os.path.join(OUT, 'sf_%s_%s.csv' % (ctx['pname'], ctx['phase']))
    pd.DataFrame(ctx['rows']).to_csv(OUTP, index=False)
    for nm, dd in (('net8', ctx['d_net8']), ('turn', ctx['d_turn']), ('gross', ctx['d_gross'])):
        pd.DataFrame(dd).to_parquet(os.path.join(OUT, 'daily_%s_%s_%s.parquet' % (nm, ctx['pname'], ctx['phase'])))
    ctx['P']('[PERIOD DONE] %s phase %s rows=%d %.0fs' % (ctx['pname'], ctx['phase'], len(ctx['rows']), time.time() - ctx['t0']))
    with open(os.path.join(OUT, '_DONE_%s_%s' % (ctx['pname'], ctx['phase'])), 'w') as fh:
        fh.write('rows=%d\n' % len(ctx['rows']))
    ctx['log'].close()


# ============================== 阶段 A: 单因子 + 两因子 ==============================
def phase_A(ctx):
    P, ev, t0 = ctx['P'], ctx['evaluate'], ctx['t0']
    neu, raw, opct = ctx['neu'], ctx['raw'], ctx['opct']
    half, hmask, s1stk = ctx['half'], ctx['hmask'], ctx['s1stk']
    pool0, log_mcap = ctx['pool0'], ctx['log_mcap']

    for f in F12:
        ev(hmask[f], 'SF50:' + f, kind='single', method='SF50', X=f)
        ev(mk(holds(neu[f], pool0, 4, 1, HB[f])), 'SF25:' + f, kind='single', method='SF25', X=f)
    P('  单因子 24 个 done %.0fs' % (time.time() - t0))

    m_prod = None; nd = 0
    for X in F12:
        for Y in F12:
            if X == Y: continue
            cY = C.precompute_neutralized_factor(raw[Y], half[X], log_mcap)
            mdep = mk(holds(cY, half[X], 2, 1, HB[Y]))
            ev(mdep, 'DEP:%s>%s' % (X, Y), kind='pair', method='DEP', X=X, Y=Y, s1=50, s2=50)
            ev(mk(holds(sub_cache(neu[Y], s1stk[X]), half[X], 2, 1, HB[Y])),
               'DEPnr:%s>%s' % (X, Y), kind='pair', method='DEPnr', X=X, Y=Y, s1=50, s2=50)
            if X == F_COND and Y == F_TVOL:
                m_prod = mdep; s = msha(mdep); same = (s == ctx['SHA_A4B'])
                P('  [内锚 1] DEP(cond>tvol) SHA %s vs A4b %s -> %s' %
                  (s, ctx['SHA_A4B'], 'SAME OK' if same else 'DIFF FAIL!!'))
                ctx['inner1'] = bool(same)
            nd += 1
            if nd % 22 == 0:
                P('    有序对 %d/132  %.0fs' % (nd, time.time() - t0))

    for i, X in enumerate(F12):
        for Y in F12[i + 1:]:
            ev(hmask[X] & hmask[Y], 'IND:%s+%s' % (X, Y), kind='pair', method='IND', X=X, Y=Y)
            cm = combine([opct[X], opct[Y]], 'mean')
            cx = combine([opct[X], opct[Y]], 'max')
            ev(mk(holds(cm, pool0, 4, 1, True)), 'CMEAN25:%s+%s' % (X, Y), kind='pair', method='CMEAN25', X=X, Y=Y)
            m50 = mk(holds(cm, pool0, 2, 1, True))
            ev(m50, 'CMEAN50:%s+%s' % (X, Y), kind='pair', method='CMEAN50', X=X, Y=Y)
            ev(mk(holds(cx, pool0, 4, 1, True)), 'CMAX25:%s+%s' % (X, Y), kind='pair', method='CMAX25', X=X, Y=Y)
            if X == F_COND and Y == F_TVOL:
                s = msha(m50); same = (s == ctx['SHA_MEAN2'])
                P('  [内锚 2] CMEAN50(cond,tvol) SHA %s vs M_mean2 %s -> %s' %
                  (s, ctx['SHA_MEAN2'], 'SAME OK' if same else 'DIFF FAIL!!'))
                ctx['inner2'] = bool(same)
    P('  无序对 66x4 done %.0fs' % (time.time() - t0))

    ind_ct = hmask[F_COND] & hmask[F_TVOL]
    if m_prod is not None:
        inter = int((ind_ct & m_prod).sum()); na = int(m_prod.sum()); ni = int(ind_ct.sum())
        P('  [诊断] IND(cond,tvol) 票数 %d, A4b 票数 %d, 交集 %d -> 占 A4b %.4f, 占 IND %.4f' %
          (ni, na, inter, inter / na if na else float('nan'), inter / ni if ni else float('nan')))

    cor = pd.DataFrame(np.nan, index=F12, columns=F12)
    for i, X in enumerate(F12):
        for Y in F12[i + 1:]:
            ks = sorted(set(opct[X]) & set(opct[Y])); vals = []
            for d in ks:
                a, b = opct[X][d], opct[Y][d]
                idx = a.index.intersection(b.index)
                if len(idx) < 6: continue
                v = a.loc[idx].corr(b.loc[idx], method='spearman')
                if v == v: vals.append(v)
            r = float(np.mean(vals)) if vals else np.nan
            cor.loc[X, Y] = r; cor.loc[Y, X] = r
    cor.to_csv(os.path.join(OUT, 'corr_%s.csv' % ctx['pname']))
    P('  相关矩阵 done %.0fs' % (time.time() - t0))
    with open(os.path.join(OUT, 'inner_anchor_%s.json' % ctx['pname']), 'w') as fh:
        json.dump({'inner1_dep_eq_a4b': ctx.get('inner1'),
                   'inner2_cmean50_eq_mmean2': ctx.get('inner2'),
                   'sha_a4b': ctx['SHA_A4B'], 'sha_mmean2': ctx['SHA_MEAN2']}, fh, indent=1)


# ============================== 阶段 C: 三因子 + 深度变体 ==============================
def phase_C(ctx):
    P, ev, t0 = ctx['P'], ctx['evaluate'], ctx['t0']
    neu, raw, opct, half = ctx['neu'], ctx['raw'], ctx['opct'], ctx['half']
    pool0, log_mcap = ctx['pool0'], ctx['log_mcap']
    with open(os.path.join(OUT, 'parents.json'), encoding='utf-8') as fh:
        parents = json.load(fh)['parents']
    tox = {(Z, k): drop_or(neu[Z], pool0, k, HB[Z]) for Z in Z6 for k in (5, 10)}
    P('  否决 mask %d 个 done %.0fs' % (len(tox), time.time() - t0))

    for pa in parents:
        X, Y, tag = pa['X'], pa['Y'], pa['tag']
        S1 = half[X]
        S2df = holds(C.precompute_neutralized_factor(raw[Y], S1, log_mcap), S1, 2, 1, HB[Y])
        S2 = mk(S2df)
        for Z in Z6:
            if Z in (X, Y): continue
            cZ = C.precompute_neutralized_factor(raw[Z], S2df, log_mcap)
            ev(mk(holds(cZ, S2df, 5, 4, HB[Z])), 'T3rel:%s>%s>%s' % (X, Y, Z), kind='triple',
               method='T3rel', X=X, Y=Y, Z=Z, stage3='relative', k=5)
            for k in (5, 10):
                ev(S2 & ~tox[(Z, k)], 'T3abs%d:%s>%s>%s' % (k, X, Y, Z), kind='triple',
                   method='T3abs', X=X, Y=Y, Z=Z, stage3='absolute', k=k)
        P('  三因子 父 %s>%s [%s] done %.0fs' % (X, Y, tag, time.time() - t0))

    for pa in parents:
        if pa['tag'] == 'worst': continue
        X, Y = pa['X'], pa['Y']; cache_h1 = {}
        for (s1, s2) in DEPTH_GRID + [(50, 50)]:
            if s1 not in cache_h1:
                h1 = pd.DataFrame(keep_pct(opct[X], pool0, s1, True).astype(float),
                                  index=pool0.index, columns=pool0.columns)
                cache_h1[s1] = (h1, pct_or(C.precompute_neutralized_factor(raw[Y], h1, log_mcap), HB[Y]))
            h1, pY = cache_h1[s1]
            ev(keep_pct(pY, h1, s2, True), 'DEPTH:%s>%s@%d_%d' % (X, Y, s1, s2),
               kind='depth', method='DEPTH', X=X, Y=Y, s1=s1, s2=s2)
        P('  深度变体 父 %s>%s done %.0fs' % (X, Y, time.time() - t0))

    e6b = pd.read_csv(E6B_SCAN).set_index('cfg'); ycol = 'net_%s' % ctx['pname'][:4]
    for aname in sorted(ANCH_DEPTH):
        s1, s2 = ANCH_DEPTH[aname]
        cfg = 'DEPTH:%s>%s@%d_%d' % (F_COND, F_TVOL, s1, s2)
        hit = [r['net8_ann'] for r in ctx['rows'] if r['cfg'] == cfg]
        if not hit:
            P('  [深度锚] %-20s 缺配置 %s' % (aname, cfg)); continue
        ancv = float(e6b.loc[aname, ycol]); d = abs(hit[0] - ancv)
        P('  [深度锚 E6b@8bp] %-20s got %+9.4f anchor %+9.4f |d|%.8f %s' %
          (aname, hit[0], ancv, d, 'OK' if d < TOL else 'FAIL(只记录, 不中止)'))


# ============================== 父配置选取 ==============================
def select_parents():
    frames = []
    for seg in SEGS:
        p = os.path.join(OUT, 'daily_net8_%s_A.parquet' % seg)
        assert os.path.exists(p), 'missing ' + p
        frames.append(pd.read_parquet(p))
    cols0 = set(frames[0].columns)
    for i, f in enumerate(frames[1:], 1):
        assert set(f.columns) == cols0, 'segment %d config columns differ from segment 1' % (i + 1)
    allnet = pd.concat(frames, axis=0).sort_index()
    dep = sorted(c for c in allnet.columns if c.startswith('DEP:'))
    assert len(dep) == 132, 'DEP count should be 132, got %d' % len(dep)
    score = {c: float(np.nanmean(allnet[c].values)) * 252 * 100.0 for c in dep}
    order = sorted(dep, key=lambda c: (-score[c], c))
    prod = 'DEP:%s>%s' % (F_COND, F_TVOL)
    rest = [c for c in order if c != prod]
    picked = [(prod, 'prod')] + [(c, 'top') for c in rest[:N_TOP]] + [(c, 'worst') for c in rest[-N_WORST:]]
    out = []
    for c, tag in picked:
        X, Y = c[len('DEP:'):].split('>')
        out.append(dict(cfg=c, X=X, Y=Y, tag=tag, rank=order.index(c) + 1, net8_full=round(score[c], 4)))
    rule = ('DEP:* full-window net8 (4 segments concatenated) desc; '
            'prod=cond>tvol always included; top=next 6; worst=last 3; ties by config name asc')
    with open(os.path.join(OUT, 'parents.json'), 'w', encoding='utf-8') as fh:
        json.dump({'rule': rule, 'selected_on': '2026-09-05', 'n_dep': len(dep), 'parents': out},
                  fh, ensure_ascii=False, indent=1)
    print('parents ->')
    for o in out:
        print('  %-6s rank %3d  net8_full %+8.4f  %s' % (o['tag'], o['rank'], o['net8_full'], o['cfg']))
    pd.DataFrame([dict(cfg=c, net8_full=score[c], rank=i + 1) for i, c in enumerate(order)]).to_csv(
        os.path.join(OUT, 'dep_ranking.csv'), index=False)


if __name__ == '__main__':
    if args.prereg:
        write_prereg()
    elif args.select_parents:
        select_parents()
    elif args.period:
        ctx = run_period(args.period, args.phase)
        (phase_A if args.phase == 'A' else phase_C)(ctx)
        finish(ctx)
    else:
        ap.error('need one of --prereg / --period / --select-parents')
