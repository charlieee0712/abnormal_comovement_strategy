# -*- coding: utf-8 -*-
"""E6m 阶段 N · 提速原型对拍与计时：路径向量化门（e6m_ops_vec）对逐路径版（e6m_ops）在真实数据上逐位相同，并计时。
不算收益；Q 坐标按 LEGACY 口径做日内有限值置换（缺失不动）。输出 stage0/c6_vec_bench_<段>.csv。"""
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
import e6m_ops_vec as V
import e6m_adapter as AD


def run(seg, P):
    with open(M.P('tmp', 'ctx_%s.pkl' % seg), 'rb') as fh:
        ctx = pickle.load(fh)
    raw, neu, kq, _ = AD.q_source(ctx)
    rows = []
    T = ctx['pool0'].shape[0]
    for fam in ('A4b', 'Mmean'):
        G = AD.Gate(ctx, fam, kq)
        days = [G.day(t) for t in range(T)]
        tl = dict(band=0., band_mem=0., prio=0., hard=0.)
        tv = dict(band=0., band_mem=0., prio=0., hard=0.)
        diff = dict(band=0, band_mem=0, prio=0, hard=0)
        nd = 0
        for t, D in enumerate(days):
            if D is None:
                continue
            nd += 1
            rng = M.rng_for('E6m', 'vec_bench', seg, fam, t)
            fin = np.flatnonzero(np.isfinite(D['kq']))
            KQ = np.repeat(D['kq'][None, :], P, axis=0)
            for p in range(P):
                KQ[p, fin] = D['kq'][fin][rng.permutation(len(fin))]
            PREV = rng.uniform(size=KQ.shape) < .5
            ins = None
            t0 = time.time()
            a = np.array([O.band(D['order'], D['s0'], KQ[p], D['n'], .1, ids=D['ids']) for p in range(P)])
            tl['band'] += time.time() - t0
            t0 = time.time()
            b = V.band_paths(D['order'], D['s0'], KQ, D['n'], .1)
            tv['band'] += time.time() - t0
            diff['band'] += int((a != b).any())
            t0 = time.time()
            a = np.array([O.band(D['order'], D['s0'], KQ[p], D['n'], .1, prev_natural=PREV[p], b=.1, loading=D['K_loading'], ids=D['ids']) for p in range(P)])
            tl['band_mem'] += time.time() - t0
            t0 = time.time()
            b = V.band_paths(D['order'], D['s0'], KQ, D['n'], .1, PREV=PREV, b=.1, loading=D['K_loading'])
            tv['band_mem'] += time.time() - t0
            diff['band_mem'] += int((a != b).any())
            t0 = time.time()
            a = np.array([O.priority_pass(D['order'], D['s0'], KQ[p], D['n'], .8, ids=D['ids'])[0] for p in range(P)])
            tl['prio'] += time.time() - t0
            t0 = time.time()
            b = V.priority_paths(D['order'], D['s0'], KQ, D['n'], .8)
            tv['prio'] += time.time() - t0
            diff['prio'] += int((a != b).any())
            base = O.source_mask(D['order'], D['n'])
            t0 = time.time()
            a = np.array([O.hard_conj(base, KQ[p], .5) for p in range(P)])
            tl['hard'] += time.time() - t0
            t0 = time.time()
            b = V.hard_paths(D['order'], KQ, D['n'], .5)
            tv['hard'] += time.time() - t0
            diff['hard'] += int((a != b).any())
        for k in tl:
            rows.append(dict(segment=seg, family=fam, op=k, paths=P, days=nd, loop_s=round(tl[k], 3), vectorized_s=round(tv[k], 3),
                             speedup=round(tl[k] / max(tv[k], 1e-9), 1), days_with_difference=diff[k], status='PASS' if diff[k] == 0 else 'FAIL'))
    df = pd.DataFrame(rows)
    p = M.P('stage0', 'c6_vec_bench_%s.csv' % seg)
    M.atomic_write_csv(p, df)
    ok = (df.status == 'PASS').all()
    M.write_receipt(os.environ.get('E6M_TASK', 'N5_vec_bench_%s' % seg), [p], status='SUCCEEDED' if ok else 'FAILED',
                    code=[__file__, os.path.join(M.CODE, 'e6m_ops_vec.py'), M.__file__], paths=P)
    print(df.to_string(index=False), flush=True)
    return 0 if ok else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--paths', type=int, default=64)
    a = ap.parse_args()
    sys.exit(run(a.seg, a.paths))
