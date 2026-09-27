# -*- coding: utf-8 -*-
"""E6j Stage 1 测量诊断（brief v1.2 §4；plan §10.3）：推导段、不作准入门、不读任何收益。
逐成员（110 个 J + 源成员）在 pool0 单元上：覆盖、符号（零 / 负占比）、分位、单位、OLS / 留一状态码、
与旧 K（pcond）及 S / M / C1 的逐日秩相关（中位）、旧 K 三档 × size 三档条件中位（3×3）、价格限制日占比、事件日龄分布（B5）。
T0 类画像不做（㊱：若做须带 pool0 同人数对照）。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import glob
import time

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_slot as SL
import e6j_engine as EN
import e6j_run_b as RB

OUT = os.path.join(J.RES, 'stage1')
SRC = ['K_rar20', 'K_slope20', 'K_MA3_E6F', 'K_rarpre', 'K_samt20', 'K_amt5', 'K_samt5', 'K_amt20', 'T_ewcv20', 'R_peer20']


def daily_spearman(a, b, t, T):
    """逐日 Spearman（两者都有限的单元；≥ 20 只）；返回中位与有效日数。"""
    ok = np.isfinite(a) & np.isfinite(b)
    rs = []
    order = np.argsort(t, kind='stable'); ts = t[order]
    bnd = np.searchsorted(ts, np.arange(T + 1))
    for d in range(T):
        ii = order[bnd[d]:bnd[d + 1]]
        ii = ii[ok[ii]]
        if len(ii) >= 20:
            ra = pd.Series(a[ii]).rank().values; rb = pd.Series(b[ii]).rank().values
            rs.append(np.corrcoef(ra, rb)[0, 1])
    return (float(np.nanmedian(rs)) if rs else np.nan), len(rs)


def terciles(x, t, T):
    q = np.full(len(x), -1)
    order = np.argsort(t, kind='stable'); ts = t[order]
    bnd = np.searchsorted(ts, np.arange(T + 1))
    for d in range(T):
        ii = order[bnd[d]:bnd[d + 1]]
        ii = ii[np.isfinite(x[ii])]
        if len(ii) >= 3:
            r = pd.Series(x[ii]).rank(method='first').values
            q[ii] = np.minimum((3 * (r - 1) // len(ii)).astype(int), 2)
    return q


def run(pname):
    t0 = time.time()
    if pname not in J.DERIV_SEGS:
        raise RuntimeError('Stage 1 只在推导段')
    env = EN.Env(pname, with_prod=True)
    ci, S, T = env.ci, env.S, env.S.T
    q0 = env.pK
    lm = S.log_mcap.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols][ci.t, ci.c]
    k3 = terciles(q0, ci.t, T); s3 = terciles(lm, ci.t, T)
    refs = {'S': env._dense_cells(SL.member_pct(env.ctx, 'K_rar20', 'lo')[0]),
            'M': env._dense_cells(SL.member_pct(env.ctx, 'K_slope20', 'lo')[0]),
            'C1': env._dense_cells(SL.member_pct(env.ctx, 'K_MA3_E6F', 'hi')[0])}
    rows = []
    mids = [(os.path.basename(p)[:-4], 'J') for p in sorted(glob.glob(os.path.join(J.RES, 'cache', pname, 'J_*.npy')))] + [(m, 'E6I') for m in SRC]
    for mid, src in mids:
        raw = RB.raw_cells(env, pname, mid, src)
        v = env.cells_of_dense(raw)
        fin = np.isfinite(v)
        pct = RB.ns_pct(env, raw, 'high_bad')
        rho_k, nd = daily_spearman(pct, q0, ci.t, T)
        r = dict(segment=pname, member_id=mid, source=src, coverage=float(fin.mean()), zero_frac=float((v[fin] == 0).mean()) if fin.any() else np.nan,
                 neg_frac=float((v[fin] < 0).mean()) if fin.any() else np.nan,
                 **{('p%02d' % q): (float(np.nanpercentile(v[fin], q)) if fin.any() else np.nan) for q in (1, 10, 50, 90, 99)},
                 rho_oldK_median=rho_k, rho_days=nd)
        for k, ref in refs.items():
            r['rho_%s_median' % k] = daily_spearman(pct, ref, ci.t, T)[0]
        for kk in range(3):
            for ss in range(3):
                m = fin & (k3 == kk) & (s3 == ss)
                r['med_K%d_S%d' % (kk, ss)] = float(np.median(v[m])) if m.any() else np.nan
        rows.append(r)
    df = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, 'measurement_diagnostics_%s.csv' % pname); J.atomic_write_csv(p, df)
    J.write_receipt('stage1_%s' % pname, [p], 'SUCCEEDED', n_members=len(df), wall_s=round(time.time() - t0, 1))
    J.log('stage1 %s: %d members %.0fs' % (pname, len(df), time.time() - t0), os.path.join(J.RES, 'logs', 'stage1_%s.log' % pname))
    return 0


if __name__ == '__main__':
    sys.exit(run(sys.argv[sys.argv.index('--segment') + 1]))
