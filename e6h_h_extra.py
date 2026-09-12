#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 推导段的 H 补格 + 加回/移出集合的事件剖面 (brief §4 末条, plan §3.4)。

  "全部基本格做 H5; 相同主格固定补 H={3,10,20} 及加回/移出集合 1-20 日事件剖面;
   **原父同 H 一起跑**, 分清'结构增量'与'完整策略相对生产 H5 增量'。"

效率: 路线操作的【掩码与 H 无关】(H 只进引擎 rolling), 所以掩码只建一次,
补三个 H 各跑一次引擎即可。

事件剖面: 对加回集 A 与移出集 R, 在形成日按固定权重算 1/3/5/10/20 日前向超额
(与 E3 标签同口径: 日超额算术和, 基准 = 该账户的 clean 基准; 只允许区间内完整端点)。
plan §10.1: fwd cohort 表固定形成日与成员, 支持缺失与可观测分母另报,
不通过未来可用性挑更好的股票。

用法: python3 e6h_h_extra.py --segment 2010-2014 --parent A06
"""
from __future__ import annotations
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_rules as RU
import e6h_run_routes as RR
import e6h_expand as EX
import e6f_core as F
import e6e_core as K

RES = H.RES
H_EXTRA = [3, 10, 20]
HORIZONS = [1, 3, 5, 10, 20]


def fwd_excess(S, h):
    """(T, Nc) 形成日 t 起 h 日的前向超额 (日超额算术和 x 1e4, 同 E3 口径)。
       任一日缺失 -> NaN (只允许区间内完整端点)。"""
    r = S.r0.copy()
    fin = np.isfinite(S.dr.values[:, S.ccols])
    r = np.where(fin, r, np.nan)
    b = np.asarray(S.bench, float)
    T = S.T
    out = np.full((T, S.Nc), np.nan)
    for t in range(T):
        hi = t + 1 + h
        if hi >= T:
            continue
        seg = r[t + 2:hi + 1] - b[t + 2:hi + 1, None]
        if seg.shape[0] < h:
            continue
        out[t] = seg.sum(axis=0) * 1e4
        out[t][~np.isfinite(seg).all(axis=0)] = np.nan
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--parent', required=True)
    a = ap.parse_args()
    assert a.segment in H.DERIV_SEGS
    t0 = time.time()
    rows = [r for r in EX.all_descriptors() if r['parent'] == a.parent]
    if not rows:
        print('本片无描述符'); return
    S = H.seg(a.segment, verbose=False)
    P = RR.ParentCtx(S, a.parent)
    print('  段+母体就绪 %.0fs, %d 个描述符' % (time.time() - t0, len(rows)), flush=True)

    fwd = {h: fwd_excess(S, h) for h in HORIZONS}
    par_h = {}
    pidx, pval = F.dev_from_dense(S, P.B)
    for Hh in H_EXTRA + [K.HOLD]:
        par_h[Hh] = F.sparse_pnl_H(S, pidx, pval, Hh, F.COST)
    print('  事件剖面与母体 H 曲线就绪 %.0fs' % (time.time() - t0), flush=True)

    out, prof = [], []
    for i, r in enumerate(rows):
        try:
            mask, wmul, ex = RR.build_mask(P, r)
        except Exception as e:
            continue
        idx, val = F.dev_from_dense(S, mask)
        if wmul is not None:
            val = [v * wmul[t, idx[t]] if len(idx[t]) else v for t, v in enumerate(val)]
        for Hh in H_EXTRA:
            g_, pp, tu, n8 = F.sparse_pnl_H(S, idx, val, Hh, F.COST)
            g0, p0_, t0_, n0 = par_h[Hh]
            both = np.isfinite(g_) & np.isfinite(g0)
            out.append(dict(
                segment=a.segment, descriptor_id=r['descriptor_id'],
                route_id=r['route_id'], parent=a.parent, role=r['role'], H=Hh,
                is_identity=bool(r.get('is_identity')),
                net8_ann=H.ann(n8), gross_ann=H.ann(g_),
                turn_mean=float(np.nanmean(tu)),
                parent_net8_ann=H.ann(n0),
                d_net8_vs_parent_sameH=H.ann(np.where(both, n8 - n0, np.nan)),
                d_net8_vs_parent_H5=H.ann(np.where(
                    both & np.isfinite(par_h[K.HOLD][3]), n8 - par_h[K.HOLD][3], np.nan))))
        # 事件剖面: 只对真正改了名单的格
        added = mask & ~P.B
        removed = P.B & ~mask
        if added.any() or removed.any():
            rec = dict(segment=a.segment, descriptor_id=r['descriptor_id'],
                       route_id=r['route_id'], parent=a.parent, role=r['role'],
                       n_added=int(added.sum()), n_removed=int(removed.sum()))
            for h in HORIZONS:
                f = fwd[h]
                for nm, M in (('added', added), ('removed', removed)):
                    v = f[M]
                    ok = np.isfinite(v)
                    rec['%s_fwd%d_mean' % (nm, h)] = (float(v[ok].mean())
                                                      if ok.any() else np.nan)
                    rec['%s_fwd%d_n' % (nm, h)] = int(ok.sum())
                    rec['%s_fwd%d_obs_frac' % (nm, h)] = (float(ok.mean())
                                                         if v.size else np.nan)
            prof.append(rec)
        if (i + 1) % 300 == 0:
            print('    %d/%d  %.0fs' % (i + 1, len(rows), time.time() - t0), flush=True)

    od = os.path.join(RES, 'route_results')
    tag = '%s_%s' % (a.segment, a.parent)
    pd.DataFrame(out).to_csv(os.path.join(od, 'hextra_%s.csv' % tag), index=False)
    pd.DataFrame(prof).to_csv(os.path.join(od, 'event_profile_%s.csv' % tag), index=False)
    print('  [%s] H 补格 %d 行 / 事件剖面 %d 行, %.0fs'
          % (tag, len(out), len(prof), time.time() - t0))


if __name__ == '__main__':
    main()
