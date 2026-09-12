#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h carried T3: 缩小候选域的诊断 (brief §9, plan §9.3)。答 Q11。

I11 / clean 不变; 只在【选股阶段】把 U 取 N={150,250} 的子样本, 各 32 seed,
两类抽样 (IID / 固定 ticker 哈希持续), n<N 保留全部。
八个配置 (R1/R2/A06/A08 + KTC keep{25,30,40,50}) **共享样本指纹**。

三种运行 (plan §9.3):
  run1 全域系数分位冻结, 仅限制可选票  —— 源掩码 ∩ 子样本 (人数随子样本变)
  run2 系数全域, 子域【重排】          —— 用全域分数, 但额度按子样本重算
  run3 子域【重新中性化】与重排        —— NS 回归在子样本内重跑
**DEP 第二关不重拟合** (plan §9.3), 所以 R1 的 run3 只重排不重拟合。

读法 (Q11, 事前登记): 斜率翻号弱化【只能说明在该构造中弱化】, 不能确认规模是原因。

用法: python3 e6h_t3.py --segment 2019-2023 [--seeds 32]
"""
from __future__ import annotations
import os
import sys
import json
import time
import hashlib
import argparse
import itertools

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_t2 as T2
import e6g_core as G
import e6g_desc as GD
import e6f_core as F
import e6e_core as K

RES = H.RES
NSUB = [150, 250]
KEEPS = [25, 30, 40, 50]
PARENTS = ['R1', 'R2', 'A06', 'A08']
SEED0 = 1109


def subsample_masks(S, N, seed, mode):
    """(T, Nc) bool: 当日 pool0 内抽 min(N, n) 只。
       mode='iid'      逐日独立抽
       mode='persist'  固定 ticker 哈希持续 (同一批票尽量一直在样本里)"""
    p0 = S.p0c
    T, Nc = p0.shape
    out = np.zeros((T, Nc), bool)
    if mode == 'persist':
        h = np.array([int(hashlib.sha256(('%s|%d' % (c, seed)).encode()).hexdigest()[:8], 16)
                      for c in S.ccolnames], dtype=np.int64)
        for t in range(T):
            v = np.where(p0[t])[0]
            if len(v) == 0:
                continue
            k = min(N, len(v))
            out[t, v[np.argsort(h[v])[:k]]] = True
    else:
        rng = np.random.default_rng(SEED0 + seed * 7919)
        for t in range(T):
            v = np.where(p0[t])[0]
            if len(v) == 0:
                continue
            k = min(N, len(v))
            out[t, v[rng.permutation(len(v))[:k]]] = True
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--seeds', type=int, default=32)
    a = ap.parse_args()
    t0 = time.time()
    S = H.seg(a.segment, verbose=False)
    ctx = GD.GCtx(S)
    od = os.path.join(RES, 'T')
    os.makedirs(od, exist_ok=True)
    p0 = S.p0c

    # ---- 全域: 核分数 + 源否决 ----
    scoreK = ctx.leg_pct(GD.spec_of_key(K.FK), 'NS', 'hi', 'identity')
    scoreT = ctx.leg_pct(GD.spec_of_key(K.FT), 'NS', 'hi', 'identity')
    scoreC = ctx.leg_pct(GD.spec_of_key(K.FC), 'NS', 'hi', 'identity')
    ktc_full = F.combine_dense([scoreK, scoreT, scoreC], 'mean', complete=True)
    vcfg = GD.parse_cfg('KTC_mean@25|cvr_1d:k10+cr5:k10')
    dr_full = ctx.build_veto_drop_g(vcfg['veto'], vcfg['core'], None, sel='SRC')
    dr_full = np.zeros_like(p0) if dr_full is None else dr_full
    # 全域的 keep 掩码 (run1 要用"分位冻结")
    full_keep = {d: G.keep_RANKBUDGET(ktc_full, p0 & ~dr_full, d) for d in KEEPS}
    # 母体的全域掩码
    par_full = {}
    for pn in PARENTS:
        par_full[pn] = ctx.full_mask_g(GD.parse_cfg(G.DISPLAY_ID[pn]))[0]
    print('  全域就绪 %.0fs' % (time.time() - t0), flush=True)

    # ---- 子域重新中性化用的原始帧 ----
    raws = {}
    for nm, key in (('K', K.FK), ('T', K.FT), ('C', K.FC)):
        r = H.build_raw_h(S, GD.spec_of_key(key))
        raws[nm] = r.reindex(index=S.pool0.index, columns=S.pool0.columns)

    rows = []
    n_done = 0
    for N, mode, seed in itertools.product(NSUB, ('iid', 'persist'), range(a.seeds)):
        sub = subsample_masks(S, N, seed, mode)
        subpool = p0 & sub
        # run3: 子域重新中性化 (NS 回归在子样本内重跑)
        subdf = pd.DataFrame(np.zeros(S.pool0.shape), index=S.pool0.index,
                             columns=S.pool0.columns)
        subdf.values[:, S.ccols] = subpool.astype(float)
        parts = []
        for nm in ('K', 'T', 'C'):
            cch, _ = F.neu_cache(raws[nm], subdf, S.log_mcap, S.icodes_neu, 'NS')
            parts.append(G.pct_dense_dir(cch, S.dates, S.ccolpos, S.Nc, 'hi'))
        ktc_sub = F.combine_dense(parts, 'mean', complete=True)

        for d in KEEPS:
            for run, mask in (
                    ('run1_frozen_quantile', full_keep[d] & subpool),
                    ('run2_full_score_subrank',
                     G.keep_RANKBUDGET(ktc_full, subpool & ~dr_full, d)),
                    ('run3_sub_neutralised',
                     G.keep_RANKBUDGET(ktc_sub, subpool & ~dr_full, d))):
                idx, val = F.dev_from_dense(S, mask)
                g_, pp, tu, n8 = F.sparse_pnl_H(S, idx, val, K.HOLD, F.COST)
                rows.append(dict(segment=a.segment, config='KTC_keep%d' % d, keep=d,
                                 N=N, mode=mode, seed=seed, run=run,
                                 net8_ann=G.ann(n8), gross_ann=G.ann(g_),
                                 turn_mean=float(np.nanmean(tu)),
                                 target_n=float(mask.sum(axis=1).mean())))
        for pn in PARENTS:
            m = par_full[pn] & subpool
            idx, val = F.dev_from_dense(S, m)
            g_, pp, tu, n8 = F.sparse_pnl_H(S, idx, val, K.HOLD, F.COST)
            rows.append(dict(segment=a.segment, config=pn, keep=np.nan, N=N,
                             mode=mode, seed=seed, run='run1_frozen_quantile',
                             net8_ann=G.ann(n8), gross_ann=G.ann(g_),
                             turn_mean=float(np.nanmean(tu)),
                             target_n=float(m.sum(axis=1).mean())))
        n_done += 1
        if n_done % 16 == 0:
            print('    子样本 %d/%d  %.0fs' % (n_done, len(NSUB) * 2 * a.seeds,
                                               time.time() - t0), flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(od, 'T3_subsample_%s.csv' % a.segment), index=False)
    print('  [%s] T3 %d 行, %.0fs' % (a.segment, len(df), time.time() - t0))


if __name__ == '__main__':
    main()
