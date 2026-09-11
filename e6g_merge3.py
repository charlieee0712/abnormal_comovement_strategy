#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 全窗口视图 (brief §10): 四段按【有效日】拼接 + 去 2015+2016 + 逐年 + 最近段。

同日做差再汇总; 不 dropna 压缩交易日轴; 空仓日是经济上的 0, 保留。
全窗口同时带仍用共 draw stationary bootstrap 的 max-|t| (块长 20, 2000 次)。
"""
import os, sys, json, glob, time, argparse
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6g_core as G
import e6g_desc as GD

BLOCK_DIR = {'H0': 'H0', 'H1': 'H1', 'H2': 'H2', 'H4a': 'H4', 'H4b': 'H4',
             'H5': 'H5', 'B2': 'B2'}


def load_seg(seg):
    n8 = {}
    for b, d in BLOCK_DIR.items():
        for fg in sorted(glob.glob(os.path.join(G.RES, d,
                                                'daily_gross_%s_%s_s*.parquet' % (b, seg)))):
            ft = fg.replace('daily_gross_', 'daily_turn_')
            if not os.path.exists(ft):
                continue
            gg = pd.read_parquet(fg); tt = pd.read_parquet(ft)
            v = gg.values - tt.values * F.COST / 1e4
            for i, c in enumerate(gg.columns):
                n8[c] = pd.Series(v[:, i], index=gg.index)
    return n8


def main():
    t0 = time.time()
    out = os.path.join(G.RES, 'D')
    MS = pd.read_csv(os.path.join(out, 'master_summary.csv'), low_memory=False)
    econ = set(MS[MS.role == 'economic'].config_id)
    fam = MS[MS.role == 'economic'].drop_duplicates('config_id').set_index(
        'config_id')['family'].to_dict()

    parts, refparts = [], []
    for seg in G.SEGMENTS:
        S = G.seg(seg, verbose=False)
        ctx = GD.GCtx(S)
        ivs, rr = {}, {}
        for lab, cid, _ in G.DISPLAY:
            pnl, iv, _ = ctx.run(GD.parse_cfg(cid))
            ivs[lab] = iv
            rr[lab] = pd.Series(pnl[0] - pnl[2] * F.COST / 1e4, index=pd.DatetimeIndex(S.dates))
        bi, bv = G.blend3_weights([ivs[m] for m in G.BLEND3_MEMBERS])
        bp = F.sparse_pnl_H(S, bi, bv, K.HOLD, F.COST)
        rr['Blend3'] = pd.Series(bp[0] - bp[2] * F.COST / 1e4,
                                 index=pd.DatetimeIndex(S.dates))
        refparts.append(pd.DataFrame(rr))
        n8 = load_seg(seg)
        n8 = {c: v for c, v in n8.items() if c in econ}
        parts.append(pd.DataFrame(n8))
        print('  %s: %d 列, %.0fs' % (seg, len(n8), time.time() - t0), flush=True)

    X = pd.concat(parts, axis=0).sort_index()
    RF = pd.concat(refparts, axis=0).sort_index()
    RF = RF.reindex(X.index)
    print('全窗口 %d 日 x %d 配置, %.0fs' % (X.shape[0], X.shape[1], time.time() - t0), flush=True)

    yrs = X.index.year.to_numpy()
    views = {'full': np.ones(len(X), bool),
             'ex_2015_2016': ~np.isin(yrs, [2015, 2016]),
             'last_segment': yrs >= 2024}
    rows = []
    rng_seed = 4242
    for vname, mask in views.items():
        Xv = X.values[mask]
        T = Xv.shape[0]
        Wm = None
        for rn in ('R1', 'R2', 'Blend3'):
            ref = RF[rn].values[mask]
            D = Xv - ref[:, None]
            mu = np.nanmean(D, axis=0) * 252 * 100
            if Wm is None:
                rng = np.random.default_rng(rng_seed)
                Wm = np.zeros((2000, T))
                for b in range(2000):
                    idx = []
                    while len(idx) < T:
                        s0 = int(rng.integers(0, T)); L = int(rng.geometric(1 / 20.0))
                        idx.extend(range(s0, min(T, s0 + L)))
                    np.add.at(Wm[b], np.asarray(idx[:T]), 1.0)
                Wm /= T
            V = np.isfinite(D).astype(float)
            Dz = np.where(np.isfinite(D), D, 0.0)
            with np.errstate(invalid='ignore', divide='ignore'):
                BM = np.where((Wm @ V) > 0, (Wm @ Dz) / np.maximum(Wm @ V, 1e-12), np.nan) \
                    * 252 * 100
            se = np.nanstd(BM, axis=0, ddof=1)
            fc = np.array([fam.get(c, 'F-other') for c in X.columns])
            with np.errstate(invalid='ignore', divide='ignore'):
                Z = (BM - mu[None, :]) / np.where(se > 0, se, np.nan)[None, :]
            simlo = np.full(len(mu), np.nan); simhi = np.full(len(mu), np.nan)
            crit = {}
            for f in np.unique(fc):
                jj = np.flatnonzero(fc == f)
                mx = np.where(np.isfinite(Z[:, jj]), np.abs(Z[:, jj]), 0.0).max(axis=1)
                cc = float(np.percentile(mx[np.isfinite(mx)], 95)) if np.isfinite(mx).any() \
                    else np.nan
                crit[f] = cc
                simlo[jj] = mu[jj] - cc * se[jj]; simhi[jj] = mu[jj] + cc * se[jj]
            rows.append(pd.DataFrame(dict(view=vname, ref=rn, config_id=list(X.columns),
                                          family=fc, delta_net8_ann=mu, boot_se=se,
                                          sim_crit=[crit[f] for f in fc],
                                          sim_lo=simlo, sim_hi=simhi)))
            print('  %s vs %s 完成 %.0fs' % (vname, rn, time.time() - t0), flush=True)
    R = pd.concat(rows, ignore_index=True)
    R.to_csv(os.path.join(out, 'fullwindow_vs_refs.csv'), index=False)

    # 逐年
    yr_rows = []
    for y in sorted(set(yrs)):
        m2 = yrs == y
        if m2.sum() < 60:
            continue
        for rn in ('R1', 'R2'):
            D = X.values[m2] - RF[rn].values[m2][:, None]
            mu = np.nanmean(D, axis=0) * 252 * 100
            yr_rows.append(pd.DataFrame(dict(year=y, ref=rn, config_id=list(X.columns),
                                             family=[fam.get(c, 'F-other') for c in X.columns],
                                             delta_net8_ann=mu)))
    pd.concat(yr_rows, ignore_index=True).to_csv(os.path.join(out, 'yearly_vs_refs.csv'),
                                                 index=False)

    s = R[R.ref == 'R2']
    print()
    print('== 全窗口拼接 vs R2 (只经济格) ==')
    for v in ('full', 'ex_2015_2016', 'last_segment'):
        g = s[s.view == v]
        print(' %-13s n=%d  点估为正 %d  同时带为正 %d  同时带为负 %d  中位 %.2f  最大 %.2f'
              % (v, len(g), int((g.delta_net8_ann > 0).sum()), int((g.sim_lo > 0).sum()),
                 int((g.sim_hi < 0).sum()), g.delta_net8_ann.median(),
                 g.delta_net8_ann.max()))
    print()
    print('== 全窗口 vs R2, 按族 ==')
    g = s[s.view == 'full']
    print(g.groupby('family').apply(
        lambda d: pd.Series({'n': len(d), '点估正': int((d.delta_net8_ann > 0).sum()),
                             '同时带正': int((d.sim_lo > 0).sum()),
                             '同时带负': int((d.sim_hi < 0).sum()),
                             '中位': round(d.delta_net8_ann.median(), 2),
                             '最大': round(d.delta_net8_ann.max(), 2)})).to_string())
    print('DONE %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
