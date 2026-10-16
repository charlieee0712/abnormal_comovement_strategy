# -*- coding: utf-8 -*-
"""E6m 阶段 S（B2 开发）· 测量（plan §4.3 / §6.1 / §8.3）。不读任何收益。

只在全程数据上算原值，再映射到各段 pool0 单元（mock 坐标：ccols = p0.any(0)，(t, c) 字典序）。T−1 和 20 日窗口跨段首取真实前一交易日。
- Q0：J_B1_qCC raw = 1/(d + 1e−4)。经 pool0 当日 log 市值源中性化（C.precompute_neutralized_factor）→ 'lo' 方向 → rank(pct)。
  须与 N5 的 kQ（stage0/cache_cloud/kq_<段>.npz）逐位相同。
- 两日：Q_MAX2 / Q_MIN2 / Q_LAGRAW1 / Q_MEAN2（e6m_ops.two_day_raw）。要求 T 与 T−1 的 d 都有效，raw 先合成，再在 T 做一次源中性化（plan §6.1）。
  无效 → 坏度缺失，使用时回旧 K 并保留缺失标记。
- V：源 pool_screening_v2.compute_parkinson_vol 返回 −vol；经济方向 vol = −源值（≥ 0）。
- Trend：云机重建状态（state_full_E6m_cloud.npz，ANCHOR_PENDING）的个股 trend 码。
  2 = UP、0 = DOWN、1 = MIXED、−1 = UNKNOWN。
端点核验：d_{T−1} := d_T 时 Q_MAX2 raw = Q0 raw，中性化后坏度与 Q0 逐位相同。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import pickle
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_ops as O

SEGS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')
TWO = ('Q_MAX2', 'Q_MIN2', 'Q_LAGRAW1', 'Q_MEAN2')


def out_path(seg):
    return M.P('stageS_dev', 'meas', 'meas_%s.npz' % seg)


def full_arrays():
    import e6m_stage0_full as SF
    import pool_screening_v2 as PS
    data, before, cd = SF.load_full()
    close = data['close'].astype(float)
    cols = close.columns
    g = lambda k: data[k].reindex(index=close.index, columns=cols).astype(float)
    is_open = (data['is_open'].reindex(index=close.index, columns=cols) == 1).to_numpy()
    o, h, l, c, lc = (g(k).to_numpy() for k in ('open', 'high', 'low', 'close', 'lclose'))
    with np.errstate(all='ignore'):
        valid = is_open & (o > 0) & (h > 0) & (l > 0) & (c > 0) & (lc > 0)
        valid &= (l <= np.minimum(o, c) + 1e-9) & (h >= np.maximum(o, c) - 1e-9)
        r = np.where(valid, np.log(c / lc), np.nan)
    d = np.abs(r)
    vsrc = PS.compute_parkinson_vol(g('high'), g('low')).to_numpy()
    dstr = np.array([str(x)[:10] for x in close.index])
    tick = np.array([int(x) for x in cols], np.int64)
    return dict(d=d, vsrc=vsrc, dates=dstr, tick=tick, cache_unchanged=sorted(os.listdir(cd)) == before)


def seg_cells(F, ctx, A, ccols, t, c):
    """全程网格数组 → 段 pool0 网格（行 = 段日期，列 = pool0 列）→ 单元。"""
    di = {s: i for i, s in enumerate(F['dates'])}
    ci = {x: j for j, x in enumerate(F['tick'])}
    rows = np.array([di[str(x)[:10]] for x in ctx['pool0'].index])
    colsf = np.array([ci.get(int(x), -1) for x in ctx['pool0'].columns])
    if (colsf[ccols] < 0).any():
        raise RuntimeError('ccol 不在全程列中')
    return A[np.ix_(rows, colsf[ccols])][t, c], rows, colsf


def neu_kq(ctx, raw_cells, t, c, ccols):
    """单元原值 → pool0 网格 DataFrame → 源中性化 → 'lo' 秩 → 单元。"""
    import comprehensive_factor_diagnosis as C
    import e6j_slot as SL
    pool0 = ctx['pool0']
    dense = np.full(pool0.shape, np.nan)
    dense[t, ccols[c]] = raw_cells
    raw_df = pd.DataFrame(dense, index=pool0.index, columns=pool0.columns)
    neu = C.precompute_neutralized_factor(raw_df, pool0, ctx['log_mcap'])
    kq = SL.pct_dir(neu, 'lo')
    out = np.full(pool0.shape, np.nan)
    di = {x: i for i, x in enumerate(pool0.index)}
    cp = {x: j for j, x in enumerate(pool0.columns)}
    for day, s in kq.items():
        pos = np.fromiter((cp[x] for x in s.index), int, len(s))
        out[di[day], pos] = s.to_numpy(float)
    return out[:, ccols][t, c]


def task_build():
    t0 = time.time()
    F = full_arrays()
    T = dict(load_and_full_s=round(time.time() - t0, 1), cache_unchanged=F['cache_unchanged'])
    zs = np.load(M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), allow_pickle=False)
    if list(zs['dates']) != list(F['dates']):
        raise RuntimeError('状态日期轴与全程数据不一致')
    zcol = {int(x): j for j, x in enumerate(zs['columns'])}
    rows_out = []
    for seg in SEGS:
        t1 = time.time()
        with open(M.P('tmp', 'ctx_%s.pkl' % seg), 'rb') as fh:
            ctx = pickle.load(fh)
        p0 = np.asarray(ctx['p0'], bool)
        ccols = np.flatnonzero(p0.any(axis=0))
        t, c = np.nonzero(p0[:, ccols])
        d_T, rows, colsf = seg_cells(F, ctx, F['d'], ccols, t, c)
        prev = np.full_like(F['d'], np.nan)
        prev[1:] = F['d'][:-1]
        d_P = seg_cells(F, ctx, prev, ccols, t, c)[0]
        raw_q0 = np.where(np.isfinite(d_T), 1.0 / (d_T + O.EPS_Q), np.nan)
        out = dict(t=t, c=c, ccols=ccols, kQ0=neu_kq(ctx, raw_q0, t, c, ccols), raw_Q0=raw_q0)
        for key, op in O.TWO_DAY_OPS.items():
            raw = O.two_day_raw(d_T, d_P, op)
            out['raw_' + key] = raw
            out['k' + key] = neu_kq(ctx, raw, t, c, ccols)
        vs = seg_cells(F, ctx, F['vsrc'], ccols, t, c)[0]
        out['vol'] = -vs
        tc = np.array([zcol.get(int(x), -1) for x in ctx['pool0'].columns[ccols]])
        tr = np.full(len(t), -1, np.int8)
        ok = tc[c] >= 0
        tr[ok] = zs['trend'][rows[t[ok]], tc[c[ok]]]
        out['trend'] = tr
        # 核验 1：Q0 对 N5 kQ 逐位
        z = np.load(M.P('stage0', 'cache_cloud', 'kq_%s.npz' % seg), allow_pickle=False)
        cpos = {s: j for j, s in enumerate(np.array([str(x) for x in ctx['pool0'].columns[ccols]]))}
        zmap = np.array([cpos[s] for s in z['ccols']])
        n5 = np.full((p0.shape[0], len(ccols)), np.nan)
        n5[:, zmap] = z['kq']
        n5c = n5[t, c]
        q0_same = bool(np.array_equal(n5c, out['kQ0'], equal_nan=True))
        # 核验 2：端点 d_{T−1} := d_T → Q_MAX2 坏度 = Q0 坏度
        raw_end = O.two_day_raw(d_T, d_T, 'MAX')
        end_same = bool(np.array_equal(neu_kq(ctx, raw_end, t, c, ccols), out['kQ0'], equal_nan=True)) and bool(
            np.array_equal(raw_end, raw_q0, equal_nan=True))
        os.makedirs(os.path.dirname(out_path(seg)), exist_ok=True)
        M.atomic_write_npz(out_path(seg), status=np.array(['ANCHOR_PENDING']), **out)
        fin = lambda v: round(float(np.isfinite(v).mean()), 6)
        rows_out.append(dict(segment=seg, cells=len(t), kQ0_finite=fin(out['kQ0']), **{k + '_finite': fin(out['k' + k]) for k in TWO},
                             vol_finite=fin(out['vol']), vol_nonneg=bool((out['vol'][np.isfinite(out['vol'])] >= 0).all()),
                             trend_unknown_share=round(float((tr < 0).mean()), 6), q0_equals_N5_bitwise=q0_same,
                             qmax2_endpoint_equals_q0_bitwise=end_same, seconds=round(time.time() - t1, 1)))
    df = pd.DataFrame(rows_out)
    p = M.P('stageS_dev', 'meas', 'meas_facts.csv')
    M.atomic_write_csv(p, df)
    ok = bool(df.q0_equals_N5_bitwise.all() and df.qmax2_endpoint_equals_q0_bitwise.all() and df.vol_nonneg.all() and T['cache_unchanged'])
    M.write_receipt(os.environ.get('E6M_TASK', 'S_dev_meas'), [p] + [out_path(s) for s in SEGS], status='SUCCEEDED' if ok else 'FAILED',
                    code=[__file__, O.__file__, M.__file__], timing=T, note='B2 开发：测量（不读收益）')
    print(df.to_string(index=False), flush=True)
    return 0 if ok else 1


def load(seg):
    z = np.load(out_path(seg), allow_pickle=False)
    return {k: z[k] for k in z.files}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['build'])
    a = ap.parse_args()
    sys.exit(task_build())
