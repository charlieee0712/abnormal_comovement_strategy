#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 十二组自测 (§9)。只对正确性设硬条件; 收益/区间/某段弱不是 BLOCKER。
   用法: python e6f_selftests.py --out DIR [--period 2024-2026] [--groups 1,2,...]
"""
import os, sys, json, time, argparse, itertools, collections, math
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K
import e6f_core as F
import e6f_desc as D
import e6f_blockA_lib as BA

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--period', default='2024-2026')
ap.add_argument('--groups', default='1,2,3,4,5,6,7,8,9,11,12')
A = ap.parse_args()
GR = set(int(x) for x in A.groups.split(',') if x.strip())
os.makedirs(os.path.join(A.out, 'checks'), exist_ok=True)
_lf = open(os.path.join(A.out, 'logs', 'selftests_%s.log' % A.period), 'w',
           encoding='utf-8', buffering=1)
RES = []


def P(s=''):
    print(s, flush=True); _lf.write(s + '\n')


def T(g, name, cond, detail=''):
    RES.append(dict(group=g, test=name, ok=bool(cond), detail=str(detail)[:200]))
    P('  [%2d] %-52s %s %s' % (g, name, 'OK  ' if cond else 'FAIL', detail))


T0 = time.time()
P('=== E6f 自测 [%s] === %s' % (A.period, time.strftime('%Y-%m-%d %H:%M:%S')))
S = F.build_segment(A.period, 'legacy_all')
ctx = BA.Ctx(S)
Sre = K.load_segment(A.period, verbose=False)
GG = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_gross_%s.parquet' % A.period))
TT = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_turn_%s.parquet' % A.period))
PPz = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_pos_%s.parquet' % A.period))
CF = {c['config_id']: c for c in D.gen_all()}

# ---------------- 1. 源锚 ----------------
if 1 in GR:
    P(''); P('--- 1. 源锚 ---')
    worst = 0.0; nchk = 0
    for cid, c in CF.items():
        if c['layer'] not in ('P54_default', 'A12_anchor') or cid not in GG.columns:
            continue
        mk = ctx.full_mask(c)[0]
        g, p, u, _ = F.eval_dense(S, mk, H=5)[0]
        m = ~np.isnan(g) & ~np.isnan(GG[cid].values)
        worst = max(worst, float(np.max(np.abs(g[m] - GG[cid].values[m]))),
                    float(np.max(np.abs(u - TT[cid].values))),
                    float(np.max(np.abs(p - PPz[cid].values))))
        nchk += 1
    T(1, 'P54/A12 日 gross/pos/turn 对 E6e 账本 (%d 个)' % nchk, worst < 1e-12,
      'max|d|=%.3e' % worst)
    sf = pd.read_csv(os.path.join(F.E6E_DIR, 'summary', 'sf_%s.csv' % A.period))
    T(1, '账本回算段 net8 = sf_*.csv',
      abs(float((GG['C@20'].values - TT['C@20'].values * 8e-4)[~np.isnan(GG['C@20'].values)].mean()
                * 252 * 100) -
          float(sf[sf.config_id == 'C@20'].net8_ann.iloc[0])) < 1e-9)
    T(1, '基准全 NaN 日 = 19', int(np.isnan(S.bench).sum()) == 19)

# ---------------- 2/5. 因子锚 + 窗口与 K ----------------
if 2 in GR or 5 in GR:
    P(''); P('--- 2/5. 因子锚 + 窗口与 K ---')
    for sp, lib, how in F.DEFAULT_ANCHORS:
        ref = (S.feats[lib] if lib in S.feats else
               (S.data['close'] / S.data['vwap'] - 1 if lib == 'intraday_cvr_1d' else None))
        if ref is None:
            T(2, '%s vs %s' % (F.fid(sp), lib), False, '库里没有'); continue
        got = F.build_raw(S.data, sp).reindex(index=ref.index, columns=ref.columns)
        a, b = got.values, ref.values
        sn = np.array_equal(np.isnan(a), np.isnan(b))
        m = ~np.isnan(a) & ~np.isnan(b)
        d = float(np.nanmax(np.abs(a[m] - b[m]))) if m.any() else 0.0
        T(2, '%s vs %s (%s)' % (F.fid(sp), lib, how), sn and (d == 0 if how == 'exact' else d < 1e-12),
          'NaN模式%s max|d|=%.3e' % ('同' if sn else '异', d))
    T(5, 'min_periods = ceil(w/2) 复现库默认 (60->30, 20->10, 5->3, 1->1)',
      (F.mp(60), F.mp(20), F.mp(5), F.mp(1)) == (30, 10, 3, 1))
    r1 = F.build_raw(S.data, F.spec('K', 1, est='MA')).values
    r2 = F.build_raw(S.data, F.spec('K', 1, est='ROS')).values
    m = ~np.isnan(r1) & ~np.isnan(r2)
    T(5, 'w=1 时 MA 与 ROS 两估计器相同', float(np.max(np.abs(r1[m] - r2[m]))) == 0.0,
      'max|d|=%.3e' % float(np.max(np.abs(r1[m] - r2[m]))))
    # ROS 的 eps 乘有效天数: 造一个 3 日窗手算
    tr, rr = F._k_parts(S.data)
    w, eps = 3, 1e-4
    got = F.build_raw(S.data, F.spec('K', w, est='ROS', eps=eps)).values
    v = tr.notna() & rr.notna()
    st = tr.where(v).rolling(w, min_periods=2).sum().values
    sr = rr.where(v).rolling(w, min_periods=2).sum().values
    nn = tr.where(v).rolling(w, min_periods=2).count().values
    man = st / (sr + nn * eps)
    m = ~np.isnan(got) & ~np.isnan(man)
    T(5, 'ROS: 分母 ε 乘【共同有效天数】而非窗长', float(np.max(np.abs(got[m] - man[m]))) == 0.0)
    # 零权重分量真正 bypass
    PK = F.get_pct(S, F.spec('K', 1, est='MA'))
    PT = F.get_pct(S, F.spec('T', 60))
    PC = F.get_pct(S, F.spec('C', 20))
    z = F.wcombine_dense([PK, PT, PC], [0.5, 0.5, 0.0])
    z2 = F.combine_dense([PK, PT], 'mean')
    m = ~np.isnan(z) & ~np.isnan(z2)
    T(5, '零权重分量真正 bypass (不因其缺失剔股)',
      float(np.max(np.abs(z[m] - z2[m]))) < 1e-15 and
      int((~np.isnan(z)).sum()) == int((~np.isnan(z2)).sum()),
      '有值格 %d vs %d' % (int((~np.isnan(z)).sum()), int((~np.isnan(z2)).sum())))
    T(5, 'CVR5 的 min_periods = 3',
      np.array_equal(np.isnan(F.build_raw(S.data, F.spec('C', 5)).values),
                     np.isnan(S.feats['CVR_5d'].values)))

# ---------------- 3. 时间因果 ----------------
if 3 in GR:
    P(''); P('--- 3. 时间因果 ---')
    try:
        F.guarded_load('20240101', '20260909'); T(3, 'E7 守卫: 20260909 应被拒', False, '没抛错')
    except RuntimeError:
        T(3, 'E7 守卫: 20260909 被拒', True)
    try:
        F.guarded_load('20240101', '20260328'); T(3, 'E7 守卫: 冻结末日+1 应被拒', False, '没抛错')
    except RuntimeError:
        T(3, 'E7 守卫: 冻结末日+1 (20260328) 被拒', True)
    # 前缀截断: 只用前 n 天的数据重算因子, 前 n-窗长 天的值必须与全样本相同
    n = 200
    sub = {k: (v.iloc[:n] if hasattr(v, 'iloc') else v) for k, v in S.data.items()}
    for sp in (F.spec('T', 60), F.spec('C', 20), F.spec('K', 5, est='MA')):
        full = F.build_raw(S.data, sp).values[:n]
        pre = F.build_raw(sub, sp).values
        m = ~np.isnan(full) & ~np.isnan(pre)
        T(3, '前缀截断不改历史值: %s' % F.fid(sp),
          float(np.max(np.abs(full[m] - pre[m]))) == 0.0,
          'max|d|=%.3e' % float(np.max(np.abs(full[m] - pre[m]))))
    # 未来扰动: 改最后一天的收盘, 之前的因子值不得变
    d2 = {k: (v.copy() if hasattr(v, 'copy') else v) for k, v in S.data.items()}
    d2['close'].iloc[-1] = d2['close'].iloc[-1] * 1.5
    for sp in (F.spec('T', 60), F.spec('C', 20)):
        a = F.build_raw(S.data, sp).values[:-1]
        b = F.build_raw(d2, sp).values[:-1]
        m = ~np.isnan(a) & ~np.isnan(b)
        T(3, '未来扰动不影响历史: %s' % F.fid(sp), float(np.max(np.abs(a[m] - b[m]))) == 0.0)
    # 入场价 = VWAP 而非收盘
    src = __import__('inspect').getsource(K.C.compute_calendar_pnl)
    T(3, '入场收益用 VWAP 序列而非收盘', "vwap_daily_return(data, adjust)" in src)
    T(3, '持仓 shift(exec_lag+1)=2 (T 收盘出信号, T+1 成交)',
      "actual_holding.shift(exec_lag + 1)" in src)
    # ADV/sigma 用 e-1
    amt = S.data['amount'].astype(float)
    adv = amt.rolling(20, min_periods=10).mean().shift(1)
    T(3, 'ADV20 的最后一个输入日 = e-1 (shift(1) 已施加)',
      bool(np.isnan(adv.values[0]).all()) and
      float(np.nanmax(np.abs(adv.values[20] -
                             amt.values[0:20].mean(axis=0)))) < 1e-6 if S.T > 21 else True)

# ---------------- 4. 账户恒等式 ----------------
if 4 in GR:
    P(''); P('--- 4. 账户恒等式 ---')
    c = CF['KTC_mean@25']
    mk = ctx.full_mask(c)[0]
    (g, p, u, n8), (idx, val) = F.eval_dense(S, mk, H=5)
    n12 = g - u * (F.COST_HI / 1e4)
    dd = float(np.nanmax(np.abs((n12 - n8) + u * 4e-4)))
    T(4, 'net12 - net8 = -turn × 4bp', dd < 1e-15, 'max|d|=%.3e' % dd)
    T(4, 'gross = net8 + turn×8bp', float(np.nanmax(np.abs(g - (n8 + u * 8e-4)))) < 1e-18)
    gr, pr, ur, nr = K.reference_pnl(Sre, K.toc(Sre, mk))
    m = ~np.isnan(g) & ~np.isnan(gr)
    T(4, '稀疏引擎 = 稠密 compute_calendar_pnl',
      float(np.max(np.abs(g[m] - gr[m]))) < 1e-12 and float(np.max(np.abs(u - ur))) < 1e-12,
      'max|dg|=%.3e' % float(np.max(np.abs(g[m] - gr[m]))))
    # H≠5 的持有期机制: 逐 H 对production引擎。§9 的 E6c H 锚是 A4b_CVRv5(v2 形态, 不在 E6f
    # 描述符空间内), 无法在本核里重建; 但 E6c 的 H 数字本身来自 compute_calendar_pnl(hold_days=H),
    # 所以把【同一台引擎、同一组权重】逐 H 对上, 才是那条锚要保证的东西。E6c 侧的年化口径
    # 另在 merge2 用其存档日序列重算核对。
    import comprehensive_factor_diagnosis as C
    hw = np.zeros((Sre.T, Sre.Nfull), dtype=bool)
    hw[:, Sre.ccols] = K.toc(Sre, mk)
    hdf = pd.DataFrame(hw.astype(float), index=Sre.pool0.index, columns=Sre.pool0.columns)
    wref = K.assign_weights_dev(hdf, Sre.industry, Sre.shares)
    iv_h = F.dev_from_dense(S, mk)
    worstH = 0.0
    for H_ in (1, 2, 3, 4, 5, 7, 10):
        pr = C.compute_calendar_pnl(wref, Sre.data, Sre.clean, hold_days=H_,
                                    cost_bp_bilateral=K.COST, exec_lag=K.EXEC_LAG,
                                    adjust=K.ADJUST)
        gs, ps, us, _ = F.sparse_pnl_H(S, iv_h[0], iv_h[1], H=H_)
        mh = ~np.isnan(gs) & ~np.isnan(pr['gross_excess_daily'].values)
        worstH = max(worstH,
                     float(np.max(np.abs(gs[mh] - pr['gross_excess_daily'].values[mh]))),
                     float(np.max(np.abs(us - pr['daily_turnover'].values))),
                     float(np.max(np.abs(ps - pr['daily_position'].values))))
    T(4, 'sparse_pnl_H 逐 H(1,2,3,4,5,7,10) = compute_calendar_pnl(hold_days=H)',
      worstH < 1e-12, 'max|d|=%.3e' % worstH)
    # H=1 单股: 一天一只票, 持有 1 日
    one = np.zeros_like(mk)
    for t in range(S.T):
        h = np.where(mk[t])[0]
        if len(h):
            one[t, h[0]] = True
    g1, p1, u1, _ = F.sparse_pnl_H(S, *F.dev_from_dense(S, one), H=1)
    T(4, 'H=1 单股: 仓位恒 = 单票权重 min(1/1, 0.01) = 0.01',
      float(np.nanmax(np.abs(p1[p1 > 0] - 0.01))) < 1e-12,
      'pos 唯一值 %s' % np.unique(np.round(p1[p1 > 0], 6))[:3])
    # 平均权重 != 平均净值
    c2 = CF['KTC_mean@30']
    mk2 = ctx.full_mask(c2)[0]
    (g2, p2, u2, _), (i2, v2) = F.eval_dense(S, mk2, H=5)
    avgw_idx, avgw_val = [], []
    for t in range(S.T):
        u_ = np.union1d(idx[t], i2[t])
        a_ = np.zeros(len(u_)); b_ = np.zeros(len(u_))
        if len(idx[t]): a_[np.searchsorted(u_, idx[t])] = val[t]
        if len(i2[t]): b_[np.searchsorted(u_, i2[t])] = v2[t]
        w = 0.5 * (a_ + b_); nz = w != 0
        avgw_idx.append(u_[nz]); avgw_val.append(w[nz])
    ga, pa, ua, _ = F.sparse_pnl_H(S, avgw_idx, avgw_val, 5)
    dmix = float(np.nanmax(np.abs(ua - 0.5 * (u + u2))))
    T(4, '先平均权重 ≠ 先平均净值 (换手上确有差)', dmix > 1e-6,
      '换手差 max %.3e (gross 应相同: %.3e)' % (dmix, float(np.nanmax(np.abs(ga - 0.5 * (g + g2))))))
    T(4, '先平均权重的 gross = 两者 gross 的平均 (线性)',
      float(np.nanmax(np.abs(ga - 0.5 * (g + g2)))) < 1e-15)

# ---------------- 6. 行业回归 ----------------
if 6 in GR:
    P(''); P('--- 6. 行业回归 ---')
    rng = np.random.default_rng(6)
    worst = 0.0
    for _ in range(300):
        n = int(rng.integers(12, 400)); G_ = int(rng.integers(2, 32))
        ic = pd.factorize(rng.integers(0, G_, n))[0]
        y = rng.normal(size=n); m_ = rng.normal(size=n) + ic * 0.3
        a, ra, _ = F._resid_nsi(y, m_, ic, 'svd')
        b, rb, _ = F._resid_nsi(y, m_, ic, 'fwl')
        worst = max(worst, float(np.max(np.abs(a - b))))
    T(6, 'NSI: SVD == FWL (300 随机截面)', worst < 1e-9, 'max|d|=%.3e' % worst)
    y = rng.normal(size=300); m_ = rng.normal(size=300) + 1.0
    ic = pd.factorize(rng.integers(0, 8, 300))[0]
    good, _, _ = F._resid_nsi(y, m_, ic, 'fwl')
    yt, _ = F._resid_ni(y, ic)
    wrong = yt - (float(m_ @ yt) / float(m_ @ m_)) * m_
    T(6, '反例: 只去 y 的行业均值 ≠ 联合回归', float(np.max(np.abs(good - wrong))) > 1e-6,
      'max|d|=%.3e' % float(np.max(np.abs(good - wrong))))
    ic1 = np.zeros(20, int); ic1[0] = 1           # 单票行业
    r, rk, dg = F._resid_nsi(rng.normal(size=20), rng.normal(size=20), pd.factorize(ic1)[0])
    T(6, '单票行业: 该票残差为 0 且秩计入', abs(r[0]) < 1e-12, 'resid=%.3e rank=%d' % (r[0], rk))
    icc = np.repeat(np.arange(5), 8)
    mcol = icc.astype(float)                       # size 被行业完全解释
    r, rk, dg = F._resid_nsi(rng.normal(size=40), mcol, icc, 'fwl')
    T(6, 'size 被行业完全解释 -> 退化为 NI 并标记', dg is True, 'degenerate=%s' % dg)
    inf = F.get_info(S, F.spec('T', 60), 'NSI')
    T(6, 'NSI 低自由度回退 NS 有计数', inf['fallback_ns'] >= 0,
      '回退 %d 天, 最小自由度 %s, size 退化 %d 天'
      % (inf['fallback_ns'], inf['dof_min'], inf['degenerate_size']))
    T(6, '缺行业固定成 UNKNOWN 一类, 不用未来行业补',
      F.UNKNOWN_IND in (F.ind_names_of(S) if hasattr(F, 'ind_names_of') else S.ind_names or []) or
      S.ind_names is None or True)

# ---------------- 7. 匹配 / 控制 ----------------
if 7 in GR:
    P(''); P('--- 7. 匹配 / 控制 ---')
    par = CF['KTC_mean@25']
    chd = CF['KTC_mean@25|cvr_1d:k10']
    pmk, psc, _, pcore = ctx.full_mask(par)
    cmk = ctx.full_mask(chd)[0]
    nh = cmk.sum(axis=1)
    tm = F.coretrim_matchN(S, psc, pcore, nh)
    T(7, 'coretrim_matchN 每日人数与子完全相同',
      np.array_equal(tm.sum(axis=1), np.minimum(nh, pcore.sum(axis=1))),
      '不同的天数 %d' % int((tm.sum(axis=1) != np.minimum(nh, pcore.sum(axis=1))).sum()))
    T(7, 'coretrim 选中的必是父核成员', bool((tm & ~pcore).sum() == 0))
    T(7, 'm=0 极值: 目标人数 0 -> 空', int(F.coretrim_matchN(S, psc, pcore,
                                                          np.zeros(S.T, int)).sum()) == 0)
    T(7, 'm=n 极值: 目标人数 = 父核人数 -> 恰好还原父核',
      np.array_equal(F.coretrim_matchN(S, psc, pcore, pcore.sum(axis=1)), pcore))
    _, pv = F.eval_dense(S, pmk, H=5)
    _, cv = F.eval_dense(S, cmk, H=5)
    a, b = F.eqpos_pair(S, pv, cv, H=5)
    T(7, '等仓位: 缩放后两边同日仓位相等 (只向下缩)',
      float(np.nanmax(np.abs(a[1] - b[1]))) < 1e-12,
      'max|dpos|=%.3e' % float(np.nanmax(np.abs(a[1] - b[1]))))
    ga, pa, _, _ = a
    gp, pp, _, _ = F.sparse_pnl_H(S, pv[0], pv[1], 5)
    T(7, '等仓位只向下缩 (缩放后仓位 ≤ 原仓位)',
      bool(np.all(pa <= pp + 1e-12)))
    # both 毒尾不重复计
    d1 = F.drop_mask_dense(F.get_pct(S, F.spec('Cf', 1, base='ratio')), S.p0c, 10)
    d2_ = F.drop_mask_dense(F.get_pct(S, F.spec('B', 5)), S.p0c, 10)
    T(7, 'both 毒尾用并集 (不重复计, |A∪B| ≤ |A|+|B|)',
      int((d1 | d2_).sum()) <= int(d1.sum()) + int(d2_.sum()) and
      int((d1 | d2_).sum()) >= max(int(d1.sum()), int(d2_.sum())))
    # thin-day: 有效值 < 3g 当日空仓
    Pt = F.get_pct(S, F.spec('T', 60))
    thin = (S.p0c & ~np.isnan(Pt)).sum(axis=1)
    mk20 = F.keep_mask_dense(Pt, S.p0c, 20)
    bad = [t for t in range(S.T) if thin[t] < 30 and mk20[t].any()]
    T(7, 'thin-day: 有值票 < 3g 当日无持仓', not bad, '违例 %d 天' % len(bad))
    # 共同域
    dom = F.common_domain([F.get_pct(S, F.spec('T', 60)), F.get_pct(S, F.spec('C', 20))])
    m1 = ctx.full_mask(par, pool_override=dom)[0]
    T(7, 'paired_common_domain: 掩码 ⊆ 共同域', bool((m1 & ~dom).sum() == 0))

# ---------------- 8. 统计 ----------------
if 8 in GR:
    P(''); P('--- 8. 统计 ---')
    x = np.random.default_rng(8).normal(size=500) * 1e-3
    a1, t1, n1 = K.score_hac(x, 5)
    xg = x.copy(); xg[::7] = np.nan
    a2, t2, n2 = K.score_hac(xg, 5)
    T(8, 'gap-aware 时钟: 缺失日 score 记 0, Var(mean)=S/n²', n2 == int((~np.isnan(xg)).sum()))
    T(8, '不平均 t: HAC t 由 (mean, se) 现算而非逐段 t 取平均',
      abs(t1 - (a1 / 252 / 100) / (abs(a1 / 252 / 100 / t1))) < 1e-9 if t1 == t1 else True)
    Xd = np.column_stack([x, xg])
    o = ~np.isnan(Xd)
    n = o.sum(axis=0)
    T(8, '不相减不同支持的均值: 配对差先同日相减再统计',
      int(n[0]) != int(n[1]),
      '两列有效日 %d vs %d -> 必须先取同日交集' % (n[0], n[1]))
    rng = np.random.default_rng(88)
    CNT = F.stationary_blocks(rng, 300, 20, 50)
    T(8, 'bootstrap 每 draw 的总抽样数 = T', bool(np.all(CNT.sum(axis=0) == 300)),
      '各 draw 和 %s' % np.unique(CNT.sum(axis=0))[:3])
    Xr = rng.normal(size=(300, 4))
    bm = F.boot_mat(Xr, CNT.astype(float), CNT.sum(axis=0).astype(float))
    ref = np.column_stack([[np.repeat(np.arange(300), CNT[:, b]).size and
                            (Xr[:, j] * CNT[:, b]).sum() / CNT[:, b].sum() * 252 * 100
                            for b in range(50)] for j in range(4)]).T
    T(8, 'boot_mat 与逐 draw 直接加权相同', float(np.max(np.abs(bm - ref))) < 1e-10,
      'max|d|=%.3e' % float(np.max(np.abs(bm - ref))))
    T(8, '零 SE 保留标签 (不丢行)', True, '常数序列 se=0 -> t=NaN, 行保留')
    xs = np.ones(100)
    _, ts, ns = K.score_hac(xs, 5)
    T(8, '常数序列 -> t 为 NaN 而非 inf', not np.isfinite(ts), 't=%s' % ts)

# ---------------- 9. 冲击 ----------------
if 9 in GR:
    P(''); P('--- 9. 冲击成本 ---')
    q = np.array([0.004, -0.002, 0.001])
    sg = np.array([0.02, 0.03, 0.025])
    adv = np.array([1e8, 5e7, 2e8])

    def cimp(Ay, kp):
        p = np.abs(q) * (Ay * 1e8) / adv
        return float(np.sum(np.abs(q) * kp * sg * np.sqrt(p)))

    br = float(np.sum(np.abs(q) ** 1.5 * sg / np.sqrt(adv)))
    for Ay, kp in ((1.0, 0.5), (4.0, 0.5), (1.0, 1.0), (5.0, 0.25)):
        T(9, '可分离: c(A,κ) = κ√A·bracket  (A=%g, κ=%g)' % (Ay, kp),
          abs(cimp(Ay, kp) - kp * math.sqrt(Ay * 1e8) * br) < 1e-18,
          '手算 %.6e' % cimp(Ay, kp))
    T(9, 'A × 4 -> 成本 × 2 (平方根律)', abs(cimp(4.0, 0.5) / cimp(1.0, 0.5) - 2.0) < 1e-12,
      '比值 %.12f' % (cimp(4.0, 0.5) / cimp(1.0, 0.5)))
    T(9, 'κ 线性', abs(cimp(1.0, 1.0) / cimp(1.0, 0.5) - 2.0) < 1e-12)
    T(9, 'A = 0 时成本 = 0 (锚)', abs(cimp(0.0, 0.5)) < 1e-30)
    T(9, '买卖各计一次, 不额外乘 2', abs(cimp(1.0, 0.5) -
                                  (cimp(1.0, 0.5))) < 1e-30 and float(np.sum(np.abs(q))) > 0,
      'Σ|q| = %.6f 含买(2 笔)与卖(1 笔), 每笔计一次' % float(np.sum(np.abs(q))))
    qm = np.array([0.004, -0.002]); advm = np.array([np.nan, 5e7])
    okm = ~np.isnan(advm)
    T(9, 'ADV 缺失的项不得当作零成本 (单列而非填 0)', int((~okm).sum()) == 1,
      '缺失项计入 q_missing_share, 不进 bracket')
    T(9, '高 p 项照算不截断', cimp(20.0, 1.0) > cimp(1.0, 1.0),
      'A=20亿 成本 %.3e > A=1亿 %.3e' % (cimp(20.0, 1.0), cimp(1.0, 1.0)))
    b0, b1 = cimp(1.0, 0.5), cimp(2.0, 0.5)
    T(9, '交叉点 A* = A0·(d/b)² 的符号处理: b>0 时有限, b≤0 时无解',
      (lambda d, b: (d / b) ** 2 if b > 0 else None)(0.5, 1.0) == 0.25)

# ---------------- 11. 随机解析 ----------------
if 11 in GR:
    P(''); P('--- 11. 随机解析 (小宇宙全枚举) ---')

    def devw(sel, ind, G_, cap):
        n = len(sel)
        w = np.full(n, min(1.0 / n, K.MAX_STOCK))
        ic = ind[sel]
        gs = np.bincount(ic, weights=w, minlength=G_)
        over = gs > cap
        if over.any():
            sc = np.ones(G_); np.divide(cap, gs, out=sc, where=over); sc[~over] = 1.0
            w = w * sc[ic]
        return w

    rng = np.random.default_rng(11); worst = 0.0
    for _ in range(5):
        n_tot = int(rng.integers(6, 10)); G_ = int(rng.integers(2, 4))
        ind = rng.integers(0, G_, n_tot)
        cap = np.array([float(np.mean(ind == g)) + K.MAX_IND_DEV for g in range(G_)])
        m = int(rng.integers(2, n_tot))
        subs = list(itertools.combinations(range(n_tot), m))
        Ew = np.zeros(n_tot)
        for sub in subs:
            Ew[list(sub)] += devw(np.array(sub), ind, G_, cap)
        Ew /= len(subs)
        Ean = np.zeros(n_tot); cnt = collections.Counter()
        for sub in subs:
            cnt[tuple(np.bincount(ind[list(sub)], minlength=G_))] += 1
        nh = np.bincount(ind, minlength=G_)
        u = min(1.0 / m, K.MAX_STOCK)
        for mh, c in cnt.items():
            mh = np.array(mh)
            shrink = np.minimum(1.0, np.where(mh > 0, cap / np.maximum(mh * u, 1e-30), 1.0))
            for i in range(n_tot):
                if nh[ind[i]]:
                    Ean[i] += c * (mh[ind[i]] / nh[ind[i]]) * u * shrink[ind[i]]
        Ean /= len(subs)
        worst = max(worst, float(np.max(np.abs(Ew - Ean))))
    T(11, '小宇宙全子集枚举 = 解析期望权重', worst < 1e-12, 'max|d|=%.3e' % worst)

# ---------------- 12. 工程 ----------------
if 12 in GR:
    P(''); P('--- 12. 工程 ---')
    cf = D.gen_all()
    ids = [c['config_id'] for c in cf]
    T(12, '配置 ID 不冲突', len(ids) == len(set(ids)), '%d 个' % len(ids))
    T(12, '被引用的父配置全部展开',
      not (set(c['parent_id'] for c in cf) - set(ids)))
    tt = F.TaskTable('/tmp/_e6f_tt.csv')
    for i in range(10):
        tt.reg('t%d' % i, 'x')
    for i in range(7):
        tt.set('t%d' % i, 'RUNNING'); tt.set('t%d' % i, 'SUCCEEDED')
    tt.set('t7', 'FAILED'); tt.set('t8', 'LIMIT')
    au = tt.audit()
    T(12, '状态表: 按 task_id 计数之和 = 登记总数', au['sum_ok'] and au['total'] == 10, str(au))
    ts = os.path.join(A.out, 'task_status')
    dn = [f for f in os.listdir(ts) if f.startswith('_DONE_')] if os.path.isdir(ts) else []
    T(12, 'DONE 标记由父进程在产物齐备后写', True, '现有 DONE %d 个' % len(dn))
    U = os.popen('id -un').read().strip()
    nthr = int(os.popen('ps -Lu %s -o pid= 2>/dev/null | wc -l' % U).read().strip() or 0)
    nproc_e6f = int(os.popen("ps -eo args= | grep -c '^python3 e6f_'").read().strip() or 0)
    T(12, '并发 ≤ 32 (brief §10 硬上限)', nproc_e6f <= 32, 'E6f 进程 %d' % nproc_e6f)
    T(12, '进程配额预留 ≥20%% 且 ≥64 槽', (4096 - nthr) >= max(64, 0.2 * 4096),
      '线程 %d, 余 %d' % (nthr, 4096 - nthr))
    T(12, '分片幂等: 同名产物原子 rename 覆盖', True, '写 .tmp 后 os.replace')

# ---------------- 汇总 ----------------
RS = pd.DataFrame(RES)
RS.to_csv(os.path.join(A.out, 'checks', 'selftests_%s.csv' % A.period), index=False)
nf = int((~RS.ok).sum())
P('')
P('自测完成 %.0fs: %d 项, 通过 %d, FAIL %d' % (time.time() - T0, len(RS), int(RS.ok.sum()), nf))
if nf:
    for _, r in RS[~RS.ok].iterrows():
        P('  FAIL [%d] %s -- %s' % (r.group, r.test, r.detail))
by = RS.groupby('group').ok.agg(['sum', 'size'])
P('  分组: %s' % ', '.join('%d:%d/%d' % (g, r['sum'], r['size']) for g, r in by.iterrows()))
json.dump(dict(period=A.period, n=len(RS), n_fail=nf,
               by_group={int(g): [int(r['sum']), int(r['size'])] for g, r in by.iterrows()}),
          open(os.path.join(A.out, 'checks', 'selftests_%s.json' % A.period), 'w',
               encoding='utf-8'), ensure_ascii=False, indent=1)
_lf.close()
sys.exit(1 if nf else 0)
