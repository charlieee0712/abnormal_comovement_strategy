#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h R0 第二块: 第二层分类 —— 每个测量【相对每个母体】的信息关系
(plan §2.1 第二层 / §2.2, brief §3)。产出 factor_parent_relation.csv。

对 87 个键 x 4 个母体 x 2 个推导段, 算:
  1. 与母体核心腿 (K/T/C) 与核心分数的【按日 signed Spearman】, 再跨日汇总
     —— 不把 pairwise 缺失填 0 后宣布独立 (plan §2.2 第 2 条)
  2. 在各决策集合 (B 保留 / D 经济拒绝 / V 被否决) 上的分位均值差
     —— "这个键能不能区分核留下的和核剔掉的"
  3. 【在 D 内部】对标签的排序能力 —— 这才是"可改变的拒绝机会"的证据:
     不是看被剔的赢家多高, 而是看这个键能否在拒绝集里把赢家排在前面
  4. 【在 B 内部】对标签的排序能力 —— "未覆盖风险" 的证据
  5. 池内可用率、并列占比

不给自动分类结论。输出证据列 + 一个【建议】status, 由规划 session 在记录 A 里定。

用法: python3 e6h_r0_relation.py --segment 2010-2014 [--shard i --nshard n]
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
import e6g_core as G
import e6g_desc as GD
import e6g_t0 as T0
import e6f_core as F
import e6e_core as K

RES = H.RES
PARENTS = ['R1', 'R2', 'A06', 'A08']
LEG_OF = {'K': K.FK, 'T': K.FT, 'C': K.FC}


def daily_spearman(A, B, mask, min_n=20):
    """按日 signed Spearman 再跨日汇总 (plan §2.2)。A/B = (T,Nc) 的 pct 表。
       只在当日两者都有限且在 mask 内的票上算; 有效日不足不汇总。"""
    T = A.shape[0]
    rs, ns = [], []
    for t in range(T):
        m = mask[t] & np.isfinite(A[t]) & np.isfinite(B[t])
        n = int(m.sum())
        if n < min_n:
            continue
        a, b = A[t][m], B[t][m]
        ra = pd.Series(a).rank().to_numpy()
        rb = pd.Series(b).rank().to_numpy()
        sa, sb = ra.std(), rb.std()
        if sa == 0 or sb == 0:
            continue
        rs.append(float(((ra - ra.mean()) * (rb - rb.mean())).mean() / (sa * sb)))
        ns.append(n)
    if not rs:
        return dict(rho_mean=np.nan, rho_median=np.nan, n_days=0, n_mean=0)
    return dict(rho_mean=float(np.mean(rs)), rho_median=float(np.median(rs)),
                rho_p10=float(np.percentile(rs, 10)), rho_p90=float(np.percentile(rs, 90)),
                n_days=len(rs), n_mean=float(np.mean(ns)))


def label_rank_power(P, L, mask, min_n=20):
    """在给定集合内, 该键的 pct 与标签的按日 Spearman (再跨日中位)。
       负值 = 键值高 -> 标签低 (键在该集合内"指向坏票"), 这正是 bad_pct 的方向约定。"""
    return daily_spearman(P, L, mask, min_n=min_n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshard', type=int, default=1)
    a = ap.parse_args()
    seg = a.segment
    assert seg in H.DERIV_SEGS, 'R0 只在推导段 (brief §3)'
    t0 = time.time()
    out = os.path.join(RES, 'T0_full_distribution')
    os.makedirs(out, exist_ok=True)

    S = H.seg(seg, verbose=False)
    ctx = GD.GCtx(S)
    lab_src, _ = T0.labels(S)
    L = lab_src.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]

    # 母体的集合 (从已存 npz 读, 保证与 stage 表同一套)
    z = np.load(os.path.join(RES, 'stage_sets', 'stage_sets_%s.npz' % seg), allow_pickle=True)
    T, Nc = z['_shape']
    def unpack(name):
        return np.unpackbits(z[name])[:T * Nc].reshape(T, Nc).astype(bool)
    sets = {}
    for p in PARENTS:
        sets[p] = dict(B=unpack('%s_B' % p), D=unpack('%s_D' % p),
                       V=unpack('%s_V' % p), C=unpack('%s_C' % p),
                       cand=unpack('%s_cand' % p))
    U = S.p0c

    # 母体核心分数与腿
    legp, score_of = {}, {}
    for nm, kk in LEG_OF.items():
        legp[nm] = H.get_pct_h(S, GD.spec_of_key(kk), 'NS', 'hi')
    for p in PARENTS:
        _, sc, _, _ = ctx.full_mask_g(GD.parse_cfg(G.DISPLAY_ID[p]))
        score_of[p] = sc

    keys = sorted(H.REGISTERED)
    keys = [k for i, k in enumerate(keys) if i % a.nshard == a.shard]
    rows = []
    for ki, k in enumerate(keys):
        try:
            sp = GD.spec_of_key(k) if k in H.U74 else H.specH(k)
            P = H.get_pct_h(S, sp, 'NS', 'hi')
        except Exception as e:
            rows.append(dict(key=k, segment=seg, status_suggested='unavailable',
                             reason=str(e)[:120]))
            continue
        avail = float(np.isfinite(P[U]).mean())
        # 并列: 当日 pct 的重复值占比
        tie = []
        for t in range(0, T, 25):
            v = P[t][U[t] & np.isfinite(P[t])]
            if v.size > 20:
                tie.append(1.0 - len(np.unique(v)) / v.size)
        tie_frac = float(np.mean(tie)) if tie else np.nan

        base = dict(key=k, segment=seg, protected=H.is_protected_key(k),
                    pool_availability=round(avail, 4), tie_frac_pool=round(tie_frac, 4)
                    if np.isfinite(tie_frac) else np.nan)
        # 与三条腿的相关 (池内)
        for nm in LEG_OF:
            r = daily_spearman(P, legp[nm], U)
            base['rho_vs_%s' % nm] = round(r['rho_mean'], 4) if np.isfinite(r['rho_mean']) else np.nan
            base['rho_days_vs_%s' % nm] = r['n_days']
        base['max_abs_rho_leg'] = round(
            float(np.nanmax([abs(base.get('rho_vs_%s' % n, np.nan)) for n in LEG_OF])), 4)

        for p in PARENTS:
            r = base.copy()
            r['parent'] = p
            rs = daily_spearman(P, score_of[p], U)
            r['rho_vs_core_score'] = round(rs['rho_mean'], 4) if np.isfinite(rs['rho_mean']) else np.nan
            # 集合间的 pct 均值差: 键能否区分"核留下的"与"核剔掉的"
            B, D, V = sets[p]['B'], sets[p]['D'], sets[p]['V']
            for nm, M in (('B', B), ('D', D), ('V', V)):
                v = P[M]
                v = v[np.isfinite(v)]
                r['pct_mean_%s' % nm] = round(float(v.mean()), 4) if v.size else np.nan
                r['n_%s' % nm] = int(v.size)
            r['pct_sep_D_minus_B'] = (round(r['pct_mean_D'] - r['pct_mean_B'], 4)
                                      if np.isfinite(r.get('pct_mean_D', np.nan))
                                      and np.isfinite(r.get('pct_mean_B', np.nan)) else np.nan)
            # 【在 D 内】排序标签的能力 = 可改变的拒绝机会的证据
            rd = label_rank_power(P, L, D)
            r['rho_label_in_D'] = round(rd['rho_median'], 4) if np.isfinite(rd['rho_median']) else np.nan
            r['days_label_in_D'] = rd['n_days']
            # 【在 B 内】= 未覆盖风险的证据
            rb = label_rank_power(P, L, B)
            r['rho_label_in_B'] = round(rb['rho_median'], 4) if np.isfinite(rb['rho_median']) else np.nan
            r['days_label_in_B'] = rb['n_days']
            # 池内整体 (作参照)
            ru = label_rank_power(P, L, U)
            r['rho_label_in_U'] = round(ru['rho_median'], 4) if np.isfinite(ru['rho_median']) else np.nan

            # 建议 status —— 只是建议, 规划 session 在记录 A 里定
            mx = r['max_abs_rho_leg']
            sug = 'candidate_for_routing'
            why = []
            if avail < 0.5:
                sug, why = 'unavailable', ['池内可用率 %.2f < 0.5' % avail]
            elif tie_frac > 0.9:
                sug, why = 'diagnostic_only', ['并列占比 %.2f > 0.9, k 分位否决由平局规则决定' % tie_frac]
            elif np.isfinite(mx) and mx >= 0.5:
                sug, why = 'candidate_for_routing', ['与腿相关 |rho|=%.2f >= 0.5 -> 同轴替代候选' % mx]
            elif np.isfinite(r['rho_label_in_D']) and abs(r['rho_label_in_D']) >= 0.02:
                sug, why = 'candidate_for_routing', [
                    '在 D 内对标签有排序 rho=%.3f -> 拒绝机会候选' % r['rho_label_in_D']]
            elif np.isfinite(r['rho_label_in_B']) and abs(r['rho_label_in_B']) >= 0.02:
                sug, why = 'candidate_for_routing', [
                    '在 B 内对标签有排序 rho=%.3f -> 保留集风险候选' % r['rho_label_in_B']]
            else:
                why = ['无上述任一证据; 但【未路由 != 无效】(plan §2.1)']
            r['status_suggested'] = sug
            r['status_basis'] = '; '.join(why)
            rows.append(r)
        if (ki + 1) % 10 == 0:
            print('  %d/%d 键, %.0fs' % (ki + 1, len(keys), time.time() - t0), flush=True)

    d = pd.DataFrame(rows)
    suf = '' if a.nshard == 1 else '_s%d' % a.shard
    p = os.path.join(out, 'factor_parent_relation_%s%s.csv' % (seg, suf))
    d.to_csv(p, index=False)
    print('写出 %s: %d 行, 耗时 %.0fs' % (os.path.basename(p), len(d), time.time() - t0))


if __name__ == '__main__':
    main()
