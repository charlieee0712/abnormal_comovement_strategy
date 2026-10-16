# -*- coding: utf-8 -*-
"""E6m 阶段 N · A6-1 / A6-2：云机逐件耗时实测（阶段 S 外推输入）。不读真实收益：账本一步用与真实网格同形状的**合成价格**计时
（真实名单 / DEV 权重 + 合成 VWAP 随机游走），P&L 数值丢弃不存。随机层每路径耗时 = Q 坐标日内置换 → 门 → 下游 → DEV → 账本。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import pickle
import argparse
import resource

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_ops as O
import e6m_adapter as AD
import e6m_b3_tools as B


def run(seg, paths):
    import e6j_prod as PR
    import comprehensive_factor_diagnosis as C
    with open(M.P('tmp', 'ctx_%s.pkl' % seg), 'rb') as fh:
        ctx = pickle.load(fh)
    rows = []
    T, N = ctx['pool0'].shape
    raw, neu, kq, _ = AD.q_source(ctx)
    masks = PR.form_masks(ctx)
    t0 = time.time()
    hold, w = PR.weights_of(ctx, masks['A4b_CVRv5'])
    rows.append(dict(item='dev_weights_one_form_s', value=time.time() - t0))
    close = ctx['data']['close']
    rng = np.random.default_rng(7)
    px = 10 * np.exp(np.cumsum(rng.normal(0, .02, size=close.shape), axis=0))
    syn = dict(vwap=pd.DataFrame(px, index=close.index, columns=close.columns), close=pd.DataFrame(px, index=close.index, columns=close.columns),
               lclose=pd.DataFrame(np.vstack([px[:1], px[:-1]]), index=close.index, columns=close.columns), is_open=ctx['data']['is_open'])
    for h in (1, 5, 20):
        t0 = time.time()
        C.compute_calendar_pnl(w, syn, ctx['clean'], hold_days=h, cost_bp_bilateral=8)
        rows.append(dict(item='ledger_calendar_pnl_H%d_s（合成价格）' % h, value=time.time() - t0))
    DS = AD.Downstream(ctx)
    for fam in ('A4b', 'Munion', 'Mmean'):
        G = AD.Gate(ctx, fam, kq)
        days = [G.day(t) for t in range(T)]
        cost = dict(permute=0., gate=0., downstream=0., dev=0., ledger=0.)
        for p in range(paths):
            t0 = time.time()
            perm = []
            for t, D in enumerate(days):
                perm.append(None if D is None else B.stable_permute(D['kq'], D['ids'], 'LEGACY|%s|%d' % (fam, p), t))
            cost['permute'] += time.time() - t0
            t0 = time.time()
            gm = np.zeros((T, N), bool)
            for t, D in enumerate(days):
                if D is not None:
                    gm[t, D['cols'][O.band(D['order'], D['s0'], perm[t], D['n'], .1, ids=D['ids'])]] = True
            cost['gate'] += time.time() - t0
            t0 = time.time()
            fin = DS.forms(fam, gm)
            cost['downstream'] += time.time() - t0
            f0 = list(fin)[1]
            t0 = time.time()
            _, wp = PR.weights_of(ctx, fin[f0])
            cost['dev'] += time.time() - t0
            t0 = time.time()
            C.compute_calendar_pnl(wp, syn, ctx['clean'], hold_days=5, cost_bp_bilateral=8)
            cost['ledger'] += time.time() - t0
        for k, v in cost.items():
            rows.append(dict(item='%s_random_path_%s_s_per_path' % (fam, k), value=v / paths))
        rows.append(dict(item='%s_random_path_total_s_per_path' % fam, value=sum(cost.values()) / paths))
    rows.append(dict(item='T_days', value=T))
    rows.append(dict(item='N_columns', value=N))
    rows.append(dict(item='pool0_cells', value=int(ctx['p0'].sum())))
    rows.append(dict(item='rss_peak_gb', value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2))
    rows.append(dict(item='paths_timed_per_family', value=paths))
    df = pd.DataFrame(rows)
    df.insert(0, 'segment', seg)
    p = M.P('stage0', 'c6_timing_cloud_paths_%s.csv' % seg)
    M.atomic_write_csv(p, df)
    M.write_receipt(os.environ.get('E6M_TASK', 'N5_timing_%s' % seg), [p], code=[__file__, M.__file__, AD.__file__, O.__file__], paths=paths)
    print(json.dumps({r['item']: round(r['value'], 3) for r in rows if 'total' in r['item'] or 'ledger' in r['item']}, ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--paths', type=int, default=8)
    a = ap.parse_args()
    sys.exit(run(a.seg, a.paths))
