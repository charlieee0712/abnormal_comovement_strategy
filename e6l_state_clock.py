# -*- coding: utf-8 -*-
"""E6l 状态三时钟（plan §6.3 / §6.4 / §11.2a；brief §1.3 第 7 条）。seal 之后运行；一段一个进程（--segment），全部段完成后 --combine 做跨段对称分解。
对象：主展示 72 + α .5 剂量 72 + STATE 调度 α .25 × H5（Q0 / Q_D5 / C1）+ 其 ONLY（旧 K 调度，α0）+ 固定 HG 参照（Q0 / Q_D5 / C1 × HG5 / 10 / 15 α .25 H5；
旧 K HG5 / 10 / 15）；每对象对同 H 原父。目标权重由 masks 位图 + DEV 确定性重算（与账户同一 SE）。
  时钟 1 形成状态 gross：批次在形成日 τ 冻结状态，T+1 VWAP 后逐日累计其实际权重 × 收益，并同时分配 −benchmark × position（超额可闭合）：
     gross_j(u) = Σ_{L=2..H+1, state(u−L)=j} (W_{u−L}·r0_u − bench_u·sw_{u−L}) / den(u−2)；Σ_j gross_j = gross（逐日恒等，核验）。
     状态：Vol3（市场，形成日）；Trend3（个股，形成日）；Q12 切片 H_noise = 高 Vol ∧ 个股 Trend 与前一交易日相同 ∧ 非 DOWN、
     H_change = 高 Vol ∧（Trend 改变 ∨ DOWN）、OTHER = 其余（事前诊断切片，不生成新策略）
  时钟 2 日历市场状态净收益：Δnet_u = net_child − net_parent，以 u 日可见 Vol3 状态（用 v_{u−1}）分组：contribution_j = mean(Δnet·1(state=j))、
     conditional_mean_j = mean(Δnet | state=j)（缺日 HAC：m_t = 1(state=j ∧ 有限)，其余状态日不当 0 样本）；Σ contribution = FULL 日均（核验）
  时钟 3 交易状态费用：Δfee_u = −8e−4·(turn_child − turn_parent) 按执行日 u 的状态分组（净额合并后的实际交易，不按形成状态倒分）
  压力窗口：2015-06-15 / 2024-09-24 起 40 个交易日：累计 Σ(net_child − net_parent)、其最大回撤；子 / 父原始组合（port = gross + bench·pos）NAV 最大回撤
  STRICT250 对照：主定义 vs STRICT250 的状态日差异（改变高低状态的日数）
  --combine：对称分解 ΔFULL = Σ .5(p_new+p_old)(μ_new−μ_old) + Σ .5(μ_new+μ_old)(p_new−p_old)（共同有支持状态）；只在一侧出现的状态记
     UNMATCHED_STATE_SUPPORT 并给剩余项。段对：相邻段与推导 → 后段。
输出 results/full/state_clock/<段>_*.csv 与 state_clock_ledger.csv（固定表）/ state_symmetric_decomposition.csv。"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import argparse

import numpy as np
import pandas as pd

import e6l_core as L
import e6l_mde80 as MD
import e6l_registry as RG

STRESS = ('2015-06-15', '2024-09-24')
VOL_LAB = {-1: 'UNKNOWN', 0: 'LOW', 1: 'MID', 2: 'HIGH'}
TR_LAB = {-1: 'UNKNOWN', 0: 'DOWN', 1: 'MIXED', 2: 'UP'}


def objects(D):
    m = (D.primary72.astype(str) == 'True') | (D.dose72.astype(str) == 'True')
    a25h5 = (D.alpha.astype(float) == 0.25) & (D.H.astype(int) == 5)
    m |= a25h5 & D.op.isin(RG.STATE) & D.meas.isin(['Q0', 'Q_D5', 'C1'])
    m |= (D.meas == 'K0') & (D.H.astype(int) == 5) & D.op.isin(RG.STATE + ('HG5', 'HG10', 'HG15'))
    m |= a25h5 & D.meas.isin(['Q0', 'Q_D5', 'C1']) & D.op.isin(['HG5', 'HG10', 'HG15'])
    return D[m]


def decompose(SE, t, c, w, H, labels_tc):
    """gross 按形成状态分解：labels_tc = (T,) 形成日标签或 (len(t),) 每单元标签（整数 0..G−1）。返回 (G, T) gross_j 与 (T,) 总 gross。"""
    T = SE.T
    r0T, bench = SE.r0T, SE.bench
    lab = labels_tc if len(labels_tc) == len(t) else labels_tc[t]
    G = int(lab.max()) + 1 if len(lab) else 1
    port = np.zeros((G, T))
    pos = np.zeros((G, T))
    den = np.minimum(np.arange(1, T + 1), H).astype(float)
    for Lg in range(2, H + 2):
        u = t + Lg
        ok = u < T
        np.add.at(port, (lab[ok], u[ok]), w[ok] * r0T[c[ok] * T + u[ok]])
        np.add.at(pos, (lab[ok], u[ok]), w[ok])
    with np.errstate(divide='ignore', invalid='ignore'):
        dd = np.r_[np.full(2, np.inf), den[:-2]]
        g = (port - bench[None, :] * pos) / dd[None, :]
    g[:, :2] = 0.0
    return g, g.sum(0)


def seg_run(pname):
    import e6l_env as V
    seg = V.SegL(pname)
    SE = seg.SE
    ci = seg.ci
    T, n = seg.T, seg.n
    D = L.read_csv_keep(L.P('registry', 'descriptors_E6l.csv'))
    O = objects(D)
    bits, arr = {}, {}
    for f in sorted(glob.glob(L.P('accounts', pname, '*.npz'))):
        if os.path.basename(f).startswith('weights_'):
            continue
        z = L.npz(f, keys=['targets', 'bits', 'desc', 'd_net8', 'd_turn', 'd_gross', 'd_pos'])
        for j, tid in enumerate(map(str, z['targets'])):
            bits[tid] = z['bits'][j]
        for i, did in enumerate(map(str, z['desc'])):
            arr[did] = dict(net8=z['d_net8'][i], turn=z['d_turn'][i], gross=z['d_gross'][i], pos=z['d_pos'][i])
    vol = np.asarray(seg.st['vol_state'], np.int64)
    vols = np.asarray(seg.st['vol_state_strict'], np.int64)
    trend = seg.trend_cells.astype(np.int64)
    trc = np.full((T, seg.Nc), -1, np.int64)
    trc[ci.t, ci.c] = trend
    prev = np.full((T, seg.Nc), -9, np.int64)
    prev[1:] = trc[:-1]
    slice_ = np.where(vol[ci.t] == 2, np.where((trend == prev[ci.t, ci.c]) & (trend != 0) & (trend >= 0), 0, 1), 2)   # 0 H_noise / 1 H_change / 2 OTHER
    dates = [str(x)[:10] for x in seg.dates]
    rows1, rows2, rows3, rows_s = [], [], [], []

    def weights(tid):
        kept = np.unpackbits(bits[tid])[:n].astype(bool)
        ids = np.flatnonzero(kept)
        t, c = ci.t[ids], ci.c[ids]
        return t, c, SE.dev(t, c), ids
    wc = {}
    for r in O.itertuples():
        H = int(r.H)
        par_t = 'K0|%s|a0|NATIVE' % r.mother
        par_d = 'K0|%s|a0|H%d|NATIVE' % (r.mother, H)
        if r.target_id not in bits or par_t not in bits or r.desc_id not in arr:
            continue
        for tid in (r.target_id, par_t):
            if tid not in wc:
                wc[tid] = weights(tid)
        tc_, cc_, wch, idc = wc[r.target_id]
        tp_, cp_, wpa, idp = wc[par_t]
        # 时钟 1
        for kind, labc, labp, names in (('VOL3_FORMATION', vol + 1, vol + 1, {k + 1: v for k, v in VOL_LAB.items()}),
                                        ('TREND3_FORMATION', trend[idc] + 1, trend[idp] + 1, {k + 1: v for k, v in TR_LAB.items()}),
                                        ('Q12_SLICE', slice_[idc], slice_[idp], {0: 'H_noise', 1: 'H_change', 2: 'OTHER'})):
            gch, tot_c = decompose(SE, tc_, cc_, wch, H, labc)
            gpa, tot_p = decompose(SE, tp_, cp_, wpa, H, labp)
            Gn = max(gch.shape[0], gpa.shape[0])
            gch = np.vstack([gch, np.zeros((Gn - gch.shape[0], T))])
            gpa = np.vstack([gpa, np.zeros((Gn - gpa.shape[0], T))])
            clos = float(np.nanmax(np.abs(tot_c - arr[r.desc_id]['gross']))) if np.isfinite(arr[r.desc_id]['gross']).any() else np.nan
            for j in range(Gn):
                rows1.append(dict(segment=pname, desc_id=r.desc_id, clock='FORMATION', state_var=kind, state=names.get(j, str(j)),
                                  gross_contrib_child_ann_pp=float(np.nanmean(gch[j])) * L.ANN, gross_contrib_parent_ann_pp=float(np.nanmean(gpa[j])) * L.ANN,
                                  gross_contrib_diff_ann_pp=float(np.nanmean(gch[j] - gpa[j])) * L.ANN, closure_max_abs_decimal=clos))
        # 时钟 2 / 3
        dn = arr[r.desc_id]['net8'] - arr[par_d]['net8']
        df_ = -8e-4 * (arr[r.desc_id]['turn'] - arr[par_d]['turn'])
        fin = np.isfinite(dn)
        tot = float(np.mean(dn[fin])) * L.ANN if fin.any() else np.nan
        for clock, x in (('CALENDAR_NET', dn), ('TRADING_FEE', df_)):
            fx = np.isfinite(x)
            Nall = int(fx.sum())
            ssum = 0.0
            for code, nm in VOL_LAB.items():
                m = fx & (vol == code)
                contrib = float(np.sum(x[m]) / Nall) * L.ANN if Nall else np.nan
                ssum += contrib if np.isfinite(contrib) else 0.0
                cm = float(np.mean(x[m])) * L.ANN if m.any() else np.nan
                se, nn = MD.hac_batch(np.where(m, x, np.nan)[None, :], H)
                rows2.append(dict(segment=pname, desc_id=r.desc_id, clock=clock, state_var='VOL3_CALENDAR', state=nm, days=int(m.sum()),
                                  share=float(m.sum() / Nall) if Nall else np.nan, contribution_ann_pp=contrib, conditional_mean_ann_pp=cm,
                                  conditional_se_H_ann_pp=float(se[0]) * L.ANN if np.isfinite(se[0]) else np.nan,
                                  status='UNDEFINED' if not m.any() else 'DEFINED'))
            rows2.append(dict(segment=pname, desc_id=r.desc_id, clock=clock, state_var='VOL3_CALENDAR', state='SUM_CHECK', days=Nall, share=1.0,
                              contribution_ann_pp=ssum, conditional_mean_ann_pp=float(np.mean(x[fx])) * L.ANN if Nall else np.nan,
                              conditional_se_H_ann_pp=np.nan, status='closure_vs_FULL_daily_mean'))
        # 压力窗口
        for s0 in STRESS:
            ix = int(np.searchsorted(np.array(dates), s0))
            if ix >= T or dates[ix] < s0:
                continue
            w_ = slice(ix, min(T, ix + 40))
            x = np.nan_to_num(dn[w_])
            cum = np.cumsum(x)
            mdd = float(np.max(np.maximum.accumulate(np.r_[0.0, cum])[1:] - cum)) if len(cum) else np.nan
            nav = {}
            for lab, did in (('child', r.desc_id), ('parent', par_d)):
                port = arr[did]['gross'] + SE.bench * arr[did]['pos']
                pth = np.cumprod(1.0 + np.nan_to_num(port[w_]))
                nav[lab] = float(np.max(1.0 - pth / np.maximum.accumulate(pth))) if len(pth) else np.nan
            rows3.append(dict(segment=pname, desc_id=r.desc_id, window_start=dates[ix], window_end=dates[min(T, ix + 40) - 1], days=len(cum),
                              cum_rel_net_pct=float(cum[-1]) * 100.0 if len(cum) else np.nan, max_drawdown_rel_ledger_pct=mdd * 100.0,
                              nav_max_drawdown_child_pct=nav['child'] * 100.0, nav_max_drawdown_parent_pct=nav['parent'] * 100.0))
    for code, nm in VOL_LAB.items():
        rows_s.append(dict(segment=pname, state=nm, main_days=int((vol == code).sum()), strict250_days=int((vols == code).sum())))
    rows_s.append(dict(segment=pname, state='LABEL_DIFFERS_DAYS', main_days=int((vol != vols).sum()), strict250_days=int(((vol >= 0) & (vols >= 0) & (vol != vols)).sum())))
    od = L.P('results', 'full', 'state_clock')
    os.makedirs(od, exist_ok=True)
    outs = []
    stress_cols = ['segment', 'desc_id', 'window_start', 'window_end', 'days', 'cum_rel_net_pct', 'max_drawdown_rel_ledger_pct', 'nav_max_drawdown_child_pct',
                   'nav_max_drawdown_parent_pct']
    for nm, rows in (('formation', rows1), ('calendar_trading', rows2), ('stress', rows3), ('strict250', rows_s)):
        p = os.path.join(od, '%s_%s.csv' % (pname, nm))
        L.atomic_write_csv(p, pd.DataFrame(rows) if rows else pd.DataFrame(columns=stress_cols if nm == 'stress' else ['segment']))
        outs.append(p)
    L.write_receipt(L.next_rerun('state_clock_%s' % pname), outs, 'SUCCEEDED', objects=int(len(O)))
    print('%s state clock：形成 %d / 日历交易 %d / 压力 %d 行' % (pname, len(rows1), len(rows2), len(rows3)), flush=True)
    return 0


def combine():
    od = L.P('results', 'full', 'state_clock')
    C = pd.concat([pd.read_csv(f, keep_default_na=False, na_values=['']) for f in glob.glob(os.path.join(od, '*_calendar_trading.csv'))], ignore_index=True)
    C = C[(C.clock == 'CALENDAR_NET') & (C.state != 'SUM_CHECK')]
    groups = {'2010-2014': ['2010-2014'], '2015-2018': ['2015-2018'], '2019-2023': ['2019-2023'], '2024-2026': ['2024-2026'],
              'DERIV': list(L.DERIV_SEGS), 'POST': list(L.POST_SEGS)}
    pairs = [('2010-2014', '2015-2018'), ('2015-2018', '2019-2023'), ('2019-2023', '2024-2026'), ('DERIV', 'POST')]
    out = []
    for did, g in C.groupby('desc_id'):
        stat = {}
        for gn, segs in groups.items():
            x = g[g.segment.isin(segs)]
            if not len(x):
                continue
            days = x.groupby('state').days.sum()
            N = days.sum()
            mu = x.assign(w=x.days * x.conditional_mean_ann_pp.fillna(0.0)).groupby('state').w.sum() / days.replace(0, np.nan)
            stat[gn] = (days / N if N else days * np.nan, mu)
        for old, new in pairs:
            if old not in stat or new not in stat:
                continue
            p0, m0 = stat[old]
            p1, m1 = stat[new]
            common = [s for s in p0.index if s in p1.index and np.isfinite(m0.get(s, np.nan)) and np.isfinite(m1.get(s, np.nan)) and p0[s] > 0 and p1[s] > 0]
            within = sum(0.5 * (p1[s] + p0[s]) * (m1[s] - m0[s]) for s in common)
            freq = sum(0.5 * (m1[s] + m0[s]) * (p1[s] - p0[s]) for s in common)
            unmatched = [s for s in set(p0.index) | set(p1.index) if s not in common]
            full0 = float(np.nansum(p0 * m0))
            full1 = float(np.nansum(p1 * m1))
            out.append(dict(desc_id=did, old=old, new=new, delta_FULL_ann_pp=full1 - full0, within_state_ann_pp=within, state_frequency_ann_pp=freq,
                            residual_ann_pp=(full1 - full0) - within - freq, common_states='|'.join(sorted(common)),
                            unmatched_state_support='|'.join(sorted(unmatched)) if unmatched else 'NONE'))
    S = pd.DataFrame(out)
    p = L.P('results', 'full', 'state_symmetric_decomposition.csv')
    L.atomic_write_csv(p, S)
    led = pd.concat([pd.read_csv(f, keep_default_na=False, na_values=['']) for f in glob.glob(os.path.join(od, '*_calendar_trading.csv'))] +
                    [pd.read_csv(f, keep_default_na=False, na_values=['']).rename(columns={'gross_contrib_diff_ann_pp': 'contribution_ann_pp'})
                     for f in glob.glob(os.path.join(od, '*_formation.csv'))], ignore_index=True)
    led['query_id'] = 'E6L-Q13-a'
    p2 = L.P('results', 'full', 'state_clock_ledger.csv')
    L.atomic_write_csv(p2, led)
    L.write_receipt(L.next_rerun('state_clock_combine'), [p, p2], 'SUCCEEDED', rows=len(S))
    print('对称分解 %d 行；账本 %d 行' % (len(S), len(led)), flush=True)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', default=None)
    ap.add_argument('--combine', action='store_true')
    a = ap.parse_args()
    import e6l_seal as SEAL
    for pkg in ('deriv', 'post'):
        ok, bad = SEAL.verify(pkg)
        if not ok:
            raise RuntimeError('seal_%s 核对失败：%s' % (pkg, bad[:5]))
    if a.combine:
        return combine()
    if a.segment in L.POST_SEGS:
        L.post_gate(a.segment, 'state clock')
    return seg_run(a.segment)


if __name__ == '__main__':
    sys.exit(main())
