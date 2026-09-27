# -*- coding: utf-8 -*-
"""E6j P 块政策补充（plan §8.3–§8.5 / §5.1a；brief §7 统计 / 解读行）。只在 P 包最新封存核对通过、pilot_policy.csv 已生成后运行；
主配置 α .25 × H5；六形态 × 四个主臂（S / M / SM / C1）。输出 results_P/：
  robustness_main.csv / robustness_loyo.csv   17 年逐年、16 完整年、逐一留一年（FULL / G4 / c）、去 2015+2016、去 2020、最近段；
                                              日增量分位、最差年 / 日、尾部（最差 5% 日均）、集中度（近零总增量只报带符号绝对贡献）、编辑资本占比
  drawdown_pair.csv            超额路径回撤（源 net8 累计和，百分点：子 / 母 / 差路径）与账户财富回撤（自融资 shadow NAV 比率，ideal / X1，逐段）分列
  opportunity_baseline.csv     随机新增分量逐路径过 c / d / 正向门槛 的比例（各机制；主 = R-MATCH-SRC IID；路径 0–1,023 四段齐全者）；
                               e / f / 市值逐路径不可算（无逐路径同资本 / 冲击 / 市值账本），不伪造
  selection_bootstrap.csv / selection_bootstrap_centered.csv
                               "按规则挑最佳合格单臂"的整个程序：每 draw 重算 c / d / e-资本 / e-随机 / f / 正向门槛（市值静态）、FULL / G4 与三句加法选择
  simultaneous_bands.csv       每形态 7 个对比（四臂 − 母、S / M / SM − C1）：bootstrap max-t 同时带与逐点区间并列；不设新 FWER 门
  multiplicity.csv             各族账户数、问题数、随机机制与路径数、同时带分位；主对象 MDE80 与 T_required（静态尺度提示）
  member_c_status.csv          合成臂成员 c 状态并印（SM ← S / M；AMT4 ← K_samt20，其余三成员本轮无 P 账户）
  cs_frozen_score.csv          CS_FROZEN_SCORE 附表（只缩域、保留全池评分），与重估 CS 分列、不混称
不写判词；随机通过比例是固定历史与该生成机制下的机会基线，不是 p 值或实盘失败概率。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_stats as ST
import e6j_bands as BD
import e6j_policy_p as PP

SEGS = list(J.SEGMENTS)
POST = list(J.POST_SEGS)
OUT = os.path.join(J.RES, 'results_P')
RAN = os.path.join(J.RES, 'randoms', 'P')
DIAG = os.path.join(J.RES, 'diagnostics', 'P')
A_, H_ = 0.25, 5
DELTA = 0.10
POS = 0.10
N_DRAWS = 2000
ARMS = ('S', 'M', 'SM', 'C1')


def yrs_of(dates):
    return pd.to_datetime(pd.Index(dates).astype(str)).year.values


# ------------------------------------------------------------------ 稳健性
def robustness(form, arm, ch, pa, dates, edit_cap):
    d_by = {s: ST.paired(ch[s]['net8'], pa[s]['net8'])[0] for s in SEGS}
    yr = {s: yrs_of(dates[s]) for s in SEGS}

    def excl(ys):
        Ds, ns = [], []
        for s in SEGS:
            D, n = ST.seg_D(np.where(np.isin(yr[s], ys), np.nan, d_by[s])); Ds.append(D); ns.append(n)
        f, g = ST.full_g4(Ds, ns)
        return f, g, bool(all(np.isfinite(D) and D >= -DELTA for D in Ds)), Ds
    f0, g0, c0, D0 = excl([])
    row = dict(form=form, arm=arm, alpha=A_, H=H_, FULL=f0, G4=g0, c=c0)
    loyo = []
    for y in ST.YEARS:
        f, g, c, Ds = excl([y])
        loyo.append(dict(form=form, arm=arm, left_out=y, FULL=f, G4=g, c=c, **{'D_%s' % s: D for s, D in zip(SEGS, Ds)}))
    lo = pd.DataFrame(loyo)
    row.update(LOYO_FULL_min=float(lo.FULL.min()), LOYO_FULL_max=float(lo.FULL.max()), LOYO_G4_min=float(lo.G4.min()),
               LOYO_c_fail_years='|'.join(str(y) for y in lo.left_out[~lo.c]) or '无')
    for lab, ys in (('ex2015_2016', [2015, 2016]), ('ex2020', [2020])):
        f, g, c, _ = excl(ys); row.update({'%s_FULL' % lab: f, '%s_G4' % lab: g, '%s_c' % lab: c})
    row['recent_D_2024_2026'] = D0[-1]
    row['recent_se_H'] = ST.hac_se(d_by[SEGS[-1]], H_)[0] * ST.ANN
    d = np.concatenate([d_by[s] for s in SEGS]); dt = np.concatenate([dates[s] for s in SEGS])
    y = ST.yearly(d, dt)
    for k, v in y.items():
        row['Y%d' % k] = v
    vals = {k: v for k, v in y.items() if np.isfinite(v)}
    row['years_pos_17'] = int(sum(v > 0 for v in vals.values())); row['years_n'] = len(vals)
    row['years_pos_2010_2025'] = int(sum(v > 0 for k, v in vals.items() if k <= 2025))
    row['worst_year'] = min(vals, key=vals.get); row['worst_year_D'] = vals[row['worst_year']]
    f = np.isfinite(d); x = d[f] * 1e4                      # 日增量，基点
    row.update(daily_mean_bp=float(x.mean()), daily_median_bp=float(np.median(x)), daily_q05_bp=float(np.quantile(x, .05)),
               daily_q25_bp=float(np.quantile(x, .25)), daily_q75_bp=float(np.quantile(x, .75)), daily_q95_bp=float(np.quantile(x, .95)),
               worst_day_bp=float(x.min()), worst_day=str(dt[f][np.argmin(x)])[:10], tail_ES5_bp=float(np.mean(np.sort(x)[:max(1, int(len(x) * .05))])))
    # 集中度：前 1% |d| 日、最好 / 最差年对 FULL 的带符号贡献（年化百分点）；总增量近零（|FULL| < .05）时不报百分比
    n = len(x); k = max(1, int(round(n * .01))); top = np.argsort(-np.abs(x))[:k]
    contrib_top = float(np.sum(d[f][top]) / n * ST.ANN)
    yrs_all = yrs_of(dt[f])
    by = {yy: float(np.sum(d[f][yrs_all == yy]) / n * ST.ANN) for yy in sorted(set(yrs_all))}
    row.update(top1pct_days_contrib=contrib_top, best_year_contrib=max(by.values()), worst_year_contrib=min(by.values()),
               top1pct_days_share=(contrib_top / f0 if abs(f0) >= 0.05 else np.nan),
               concentration_note=('总增量近零：只报带符号绝对贡献' if abs(f0) < 0.05 else ''))
    ec = edit_cap[(edit_cap.form == form) & (edit_cap.arm == arm)]
    for s in SEGS:
        e = ec[ec.segment == s]
        if len(e):
            row['entry_weight_share_%s' % s] = float(e.entry_weight_share_mean.iloc[0])
            row['exit_weight_share_%s' % s] = float(e.exit_weight_share_mean.iloc[0])
    return row, lo


def excess_dd(x):
    """累计和路径（百分点）的最大回撤；NaN 日跳过。"""
    v = x[np.isfinite(x)] * 100.0
    if len(v) < 2:
        return np.nan
    c = np.cumsum(v); return float(np.max(np.maximum.accumulate(c) - c))


def drawdowns(form, arm, ch, pa, shadow):
    rows = []
    for s in SEGS + ['ALL']:
        segs = SEGS if s == 'ALL' else [s]
        cn = np.concatenate([ch[q]['net8'] for q in segs]); pn = np.concatenate([pa[q]['net8'] for q in segs])
        d = ST.paired(cn, pn)[0]
        r = dict(form=form, arm=arm, segment=s, H=H_, excess_dd_child_pp=excess_dd(cn), excess_dd_parent_pp=excess_dd(pn),
                 excess_dd_diffpath_pp=excess_dd(d))
        r['excess_dd_change_pp'] = r['excess_dd_child_pp'] - r['excess_dd_parent_pp']
        if s != 'ALL':
            for mode in ('ideal', 'X1'):
                sc = shadow[(shadow.segment == s) & (shadow.form == form) & (shadow.diag == 'SHADOW_SF_%s' % mode)]
                c_ = sc[sc.arm == arm]; p_ = sc[sc.arm == 'C0']
                r['wealth_dd_child_%s' % mode] = float(c_.max_dd.iloc[0]) if len(c_) else np.nan
                r['wealth_dd_parent_%s' % mode] = float(p_.max_dd.iloc[0]) if len(p_) else np.nan
        rows.append(r)
    return rows


# ------------------------------------------------------------------ 随机机会基线
def opportunity(form, arm, pa, dates):
    per = {}
    for s in SEGS:
        z = np.load(os.path.join(RAN, s, '%s__%s.npz' % (form, arm)), allow_pickle=False)
        mechs = [str(m) for m in z['mechs']]
        main = z['main']                                    # (机制, 路径, 4, T)：α .25 × H5 逐路径日账本
        pn = pa[s]['net8']; yr = yrs_of(dates[s])
        for mi, m in enumerate(mechs):
            x = main[mi, :, 0, :]
            d = np.where(np.isfinite(x) & np.isfinite(pn)[None, :], x - pn[None, :], np.nan)
            M = np.isfinite(d); d0 = np.where(M, d, 0.0)
            n = M.sum(1)
            D = np.where(n > 0, d0.sum(1) / np.maximum(n, 1), np.nan) * ST.ANN
            Y = {int(y): np.where(M[:, yr == y].sum(1) > 0, d0[:, yr == y].sum(1) / np.maximum(M[:, yr == y].sum(1), 1), np.nan)
                 for y in sorted(set(yr))}
            per.setdefault(m, {})[s] = (D, n, Y)
        del main, z
    rows = []
    for m, bys in per.items():
        if set(bys) != set(SEGS):
            continue
        npth = min(len(bys[s][0]) for s in SEGS)
        Ds = np.stack([bys[s][0][:npth] for s in SEGS], 0); ns = np.stack([bys[s][1][:npth] for s in SEGS], 0)
        full = np.where(ns.sum(0) > 0, (Ds * ns).sum(0) / np.maximum(ns.sum(0), 1), np.nan)
        g4 = np.nanmedian(Ds, 0)
        Y = {}
        for s in SEGS:
            Y.update({y: v[:npth] for y, v in bys[s][2].items()})
        ypos = np.sum(np.stack([Y[y] > 0 for y in sorted(Y)], 0), 0)
        c = np.all(Ds >= -DELTA, 0); d_ok = ypos >= 12
        for prof, val in (('FULL', full), ('G4', g4)):
            pos = val >= POS
            rows.append(dict(form=form, arm=arm, mechanism=m, profile=prof, n_paths=int(npth), frac_c=float(c.mean()), frac_d=float(d_ok.mean()),
                             frac_positive=float(pos.mean()), frac_c_d_positive=float((c & d_ok & pos).mean()),
                             random_value_q50=float(np.nanmedian(val)), random_value_q95=float(np.nanquantile(val, .95)),
                             not_computable='e-资本 / e-随机 / f / 市值（无逐路径同资本、冲击、市值账本）'))
    return rows


# ------------------------------------------------------------------ 选择程序 bootstrap 与同时带
def iid_mean_daily(seg, form, arm):
    """R-MATCH-SRC（IID）α .25 × H5 的随机路径日均值（全部分片按路径数加权）。"""
    num, den = None, 0
    files = [os.path.join(RAN, seg, '%s__%s.npz' % (form, arm))] + sorted(glob.glob(os.path.join(RAN, seg, '%s__%s_p*.npz' % (form, arm))))
    for f in [f for f in files if os.path.exists(f)]:
        z = np.load(f, allow_pickle=False)
        mechs = [str(m) for m in z['mechs']]
        if 'IID' not in mechs:
            continue
        ai = list(np.round(z['alphas'], 6)).index(A_); hi = list(z['Hs']).index(H_)
        npth = z['ann'].shape[1]
        v = z['mean_daily'][mechs.index('IID'), ai, hi] * npth
        num = v if num is None else num + v; den += npth
    return num / den if den else None


def program_bootstrap(form, A, dates, pol, cms):
    """返回 (选择程序行, 同时带行)。列：d_arm / d_sc_arm / d_imp_arm / d_rand_arm（后段）/ S−C1 / M−C1 / SM−C1 / SM−S / SM−M。"""
    get = lambda arm: A[(arm, A_, H_)]
    pa = A[('C0', 0.0, H_)]
    cols, X = [], {s: [] for s in SEGS}
    imp = lambda z: z['net8'] - ST.impact_cost(z['bracket'], PP.A_POL, PP.K_POL)
    for arm in ARMS:
        ch = get(arm)
        rmean = {s: (iid_mean_daily(s, form, arm) if s in POST else None) for s in SEGS}
        for kind in ('d', 'sc', 'imp', 'rand'):
            cols.append('%s|%s' % (kind, arm))
            for s in SEGS:
                c, p = ch[s], pa[s]
                if kind == 'd':
                    x = ST.paired(c['net8'], p['net8'])[0]
                elif kind == 'sc':
                    x = ST.paired(c['sc_child'], c['sc_parent'])[0]
                elif kind == 'imp':
                    x = ST.paired(imp(c), imp(p))[0]
                else:
                    x = ST.paired(c['net8'], rmean[s])[0] if rmean[s] is not None else np.full(len(c['net8']), np.nan)
                X[s].append(x)
    for a1, a2 in (('S', 'C1'), ('M', 'C1'), ('SM', 'C1'), ('SM', 'S'), ('SM', 'M')):
        cols.append('pair|%s-%s' % (a1, a2))
        for s in SEGS:
            X[s].append(ST.paired(get(a1)[s]['net8'], get(a2)[s]['net8'])[0])
    X = {s: np.column_stack(v) for s, v in X.items()}
    ci = {c: i for i, c in enumerate(cols)}
    polm = pol[(pol.form == form) & pol.main_config].set_index('arm')
    size_fail = {a: (polm.loc[a, 'size_status'] == 'FAIL') if a in polm.index else False for a in ARMS}
    sel_rows, band_rows = [], []
    for L, cm in cms.items():
        for centered in (False, True):
            rs = BD.resample(cm, X, centered=centered)
            Dseg = {s: BD.seg_D(rs, s) for s in SEGS}                      # (draws, K)
            FULL = BD.full(rs, SEGS); G4 = BD.g4(rs, SEGS)
            ypos, _ = BD.years_pos(rs)
            real = {'FULL': np.array([ST.full_g4([ST.seg_D(X[s][:, k])[0] for s in SEGS], [ST.seg_D(X[s][:, k])[1] for s in SEGS])[0]
                                      for k in range(len(cols))])}
            for prof in ('FULL', 'G4'):
                V = FULL if prof == 'FULL' else G4
                ok, val = {}, {}
                for arm in ARMS:
                    kd, ks, kf, kr = ci['d|%s' % arm], ci['sc|%s' % arm], ci['imp|%s' % arm], ci['rand|%s' % arm]
                    c_ = np.all(np.stack([Dseg[s][:, kd] >= -DELTA for s in SEGS], 0), 0)
                    d_ = ypos[:, kd] >= 12
                    s_n, s_c = PP.tri_sign(V[:, kd]), PP.tri_sign(V[:, ks])
                    e_cap = (s_n == s_c) & np.isfinite(s_n) & np.isfinite(s_c)
                    e_rand = np.all(np.stack([Dseg[s][:, kr] > 0 for s in POST], 0), 0)
                    f_ = np.all(np.stack([Dseg[s][:, kf] >= -DELTA for s in SEGS], 0), 0)
                    pos = V[:, kd] >= POS
                    ok[arm] = c_ & d_ & e_cap & e_rand & f_ & pos & (not size_fail[arm])
                    val[arm] = V[:, kd]
                nd = len(V)
                chosen = np.array(['无'] * nd, dtype=object); prog = np.zeros(nd)
                for b in range(nd):
                    elig = [a for a in ('C1', 'M', 'S') if ok[a][b]]
                    best = sorted(elig, key=lambda a: (-val[a][b], ('C1', 'M', 'S').index(a)))[0] if elig else None
                    ch_ = None
                    if 'C1' in elig:
                        ch_ = 'C1'; beat = []
                        for a in ('M', 'S'):
                            if a in elig:
                                k = ci['pair|%s-C1' % a]
                                dsg = np.array([Dseg[s][b, k] for s in SEGS])
                                md = (FULL if prof == 'FULL' else G4)[b, k]
                                if int(np.sum(dsg >= 0.05)) >= 3 and md >= 0.05:
                                    beat.append((md, a))
                        if beat:
                            ch_ = sorted(beat, key=lambda x: (-x[0], ('M', 'S').index(x[1])))[0][1]
                    elif elig:
                        ch_ = best
                    if ok['SM'][b]:
                        if best is None:
                            ch_ = 'SM'
                        else:
                            md = (FULL if prof == 'FULL' else G4)[b, ci['pair|SM-%s' % best]]
                            if md >= 0.10:
                                ch_ = 'SM'
                    if ch_:
                        chosen[b] = ch_; prog[b] = val[ch_][b]
                r = dict(form=form, profile=prof, L=L, centered=centered, n_draws=nd,
                         program_q025=float(np.quantile(prog, .025)), program_q50=float(np.quantile(prog, .5)), program_q975=float(np.quantile(prog, .975)))
                for a in ('C1', 'M', 'S', 'SM', '无'):
                    r['choose_%s' % a] = float(np.mean(chosen == a))
                for a in ARMS:
                    r['pass_%s' % a] = float(ok[a].mean())
                sel_rows.append(r)
            if not centered:
                ks = [ci['d|%s' % a] for a in ARMS] + [ci['pair|%s-C1' % a] for a in ('S', 'M', 'SM')]
                labs = ['%s − 母' % a for a in ARMS] + ['%s − C1' % a for a in ('S', 'M', 'SM')]
                q, sd, plo, phi, slo, shi, fam = BD.max_t_band(FULL[:, ks], real['FULL'][ks])
                for j, lab in enumerate(labs):
                    band_rows.append(dict(form=form, L=L, contrast=lab, FULL=float(real['FULL'][ks][j]), boot_sd=float(sd[j]), maxt_q95=q,
                                          point_lo=float(plo[j]), point_hi=float(phi[j]), simul_lo=float(slo[j]), simul_hi=float(shi[j]),
                                          in_family=bool(fam[j])))
    return sel_rows, band_rows


def main():
    import e6j_seal as SEAL
    ok, bad = SEAL.verify('P')
    if not ok:
        raise RuntimeError('P 包封存核对未过（%d 项）' % len(bad))
    pol = pd.read_csv(os.path.join(OUT, 'pilot_policy.csv'))
    dx = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(os.path.join(DIAG, '*', 'diag_extra_*.csv')))], ignore_index=True)
    dg = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(os.path.join(DIAG, '*', 'diagnostics_*.csv')))], ignore_index=True)
    edit_cap = dx[dx.diag == 'EDIT_CAP']; shadow = dx[dx.diag.str.startswith('SHADOW_SF')]
    rob, loyo, dd, opp, sel, bands = [], [], [], [], [], []
    cms, ndays = None, None
    for form in PP.FORMS:
        A, dates = PP.arrays_for(form)
        pa = A[('C0', 0.0, H_)]
        if cms is None:
            lens = {s: len(dates[s]) for s in SEGS}
            ndays = sum(lens.values())
            cms = {L: BD.count_mats(lens, dates, L, N_DRAWS, 'P-main') for L in (20, 60)}
        for arm in ARMS:
            ch = A[(arm, A_, H_)]
            r, lo = robustness(form, arm, ch, pa, dates, edit_cap); rob.append(r); loyo.append(lo)
            dd += drawdowns(form, arm, ch, pa, shadow)
            opp += opportunity(form, arm, pa, dates)
        s_, b_ = program_bootstrap(form, A, dates, pol, cms); sel += s_; bands += b_
        J.log('policy_extra %s done' % form, os.path.join(J.RES, 'logs', 'policy_extra.log'))
    outs = []

    def w(name, df):
        p = os.path.join(OUT, name); J.atomic_write_csv(p, df); outs.append(p)
    w('robustness_main.csv', pd.DataFrame(rob)); w('robustness_loyo.csv', pd.concat(loyo, ignore_index=True))
    w('drawdown_pair.csv', pd.DataFrame(dd)); w('opportunity_baseline.csv', pd.DataFrame(opp))
    sel = pd.DataFrame(sel)
    w('selection_bootstrap.csv', sel[~sel.centered]); w('selection_bootstrap_centered.csv', sel[sel.centered])
    w('simultaneous_bands.csv', pd.DataFrame(bands))
    # ---- 成员 c 状态
    mc = []
    key = lambda f, a, al, H: pol[(pol.form == f) & (pol.arm == a) & np.isclose(pol.alpha, al) & (pol.H == H)]
    for _, r in pol[pol.arm.isin(['SM', 'COL:AMT4'])].iterrows():
        members = [('S', 'S'), ('M', 'M')] if r.arm == 'SM' else [('K_samt20', 'COL:K_samt20'), ('K_amt5', None), ('K_samt5', None), ('K_amt20', None)]
        for lab, arm in members:
            m = key(r.form, arm, r.alpha, r.H) if arm else pd.DataFrame()
            mc.append(dict(form=r.form, composite=r.arm, alpha=r.alpha, H=r.H, composite_c=bool(r.c_FULL_d10), member=lab,
                           member_c=(bool(m.c_FULL_d10.iloc[0]) if len(m) else np.nan),
                           member_D_min=(float(min(m['D_%s' % s].iloc[0] for s in SEGS)) if len(m) else np.nan),
                           note=('' if len(m) else '本轮无该成员单独 P 账户（AMT4 为列对象、不评分）')))
    w('member_c_status.csv', pd.DataFrame(mc))
    # ---- CS_FROZEN_SCORE 附表（与重估 CS 并列）
    fz = dx[dx.diag == 'CS_FROZEN'].copy()
    cs = dg[dg.diag == 'CS'][['segment', 'form', 'arm', 'H', 'C1_minus_C0', 'C0_minus_N0', 'N1_minus_C1']].rename(
        columns={'C1_minus_C0': 'CS_reestimated_C1_minus_C0', 'C0_minus_N0': 'CS_reestimated_C0_minus_N0', 'N1_minus_C1': 'CS_reestimated_N1_minus_C1'})
    w('cs_frozen_score.csv', fz.merge(cs, on=['segment', 'form', 'arm', 'H'], how='left'))
    # ---- 多重性与 T_required
    reg = pd.read_csv(os.path.join(J.RES, 'registry', 'descriptors_P.csv'))
    exl = pd.read_csv(os.path.join(J.RES, 'registration', 'selection_exposure_ledger.csv'))
    bands = pd.DataFrame(bands)
    mains = pol[pol.main_config & pol.arm.isin(ARMS)]
    mult = [dict(family='P 冻结主试点（A4b_CVRv5 四臂 − 母 / − C1，α .25 × H5）', accounts=7, questions='Q07 / Q13 / Q15 / Q16',
                 maxt_q95_L20=float(bands[(bands.form == PP.MAIN_FORM) & (bands.L == 20)].maxt_q95.iloc[0]),
                 maxt_q95_L60=float(bands[(bands.form == PP.MAIN_FORM) & (bands.L == 60)].maxt_q95.iloc[0])),
            dict(family='P 全部登记描述符（六形态 × 臂 × α × H）', accounts=int(len(reg)), questions='—'),
            dict(family='P 主臂评分对象（六形态 × 四臂 × 12 格）', accounts=int(pol.arm.isin(ARMS).sum()), questions='政策评分'),
            dict(family='P 随机（每 (段, 形态, 臂)：7 机制 × 1,024 路径起；IID 增补另计）', accounts=int(6 * 4 * 7), questions='e-随机 / 机会基线'),
            dict(family='历史选择暴露台账（selection_exposure_ledger）', accounts=int(len(exl)), questions='全过程')]
    for _, r in mains.iterrows():
        se = float(r.FULL_se_H); mde = 2.80 * se; T_y = ndays / 252.0
        mult.append(dict(family='主对象 %s / %s' % (r.form, r.arm), accounts=1, FULL=float(r.FULL), FULL_se_H=se, MDE80=mde,
                         T_years=T_y, T_required_years=(T_y * (mde / DELTA) ** 2 if np.isfinite(mde) else np.nan),
                         note='T_required = T·(MDE80/δ)²：静态尺度提示（依赖当前方差与正态近似），不是采纳所需等待年数'))
    w('multiplicity.csv', pd.DataFrame(mult))
    J.write_receipt('policy_extra_P', outs, 'SUCCEEDED', n_files=len(outs))
    print('policy_extra', len(outs))
    return 0


if __name__ == '__main__':
    sys.exit(main())
