#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h R0 第三块: 伪路径 / 匹配随机参照 (brief §3, plan §2.3 末段)。

问题: 一个集合 (真实输家 / 真实赢家 / 母体的 B / D) 的标签均值, 有多少只是
【构成】—— 行业、市值 —— 带来的? 三层匹配逐层加严:
  U_IID   : 同人数, 池内均匀抽 (不匹配任何构成)
  I_IID   : 同人数【且同行业人数】
  IxM_IID : 同人数【且同 (行业 x 当日池内市值三档) 人数】

plan §2.3 明确警告: "匹配只是条件参照, 尤其不能过度匹配掉研究中的行业或流动性信息"
—— 所以三层【并列报】, 不取最严的当唯一答案; 匹配后归零不等于无效。
伪输家与伪赢家【对称】做 (E6g 只做了输家一侧)。

只落汇总 + 8 条示例路径 (brief §0.1: E6e 183 GB 教训)。

用法: python3 e6h_r0_pseudo.py --segment 2010-2014 [--draws 128]
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
import e6g_t0 as T0

RES = H.RES
PARENTS = ['R1', 'R2', 'A06', 'A08']
SEED = 20260912


def strata_codes(S, level):
    """(T, Nc) 整数分层码。-1 = 不可用。"""
    T, Nc = S.T, S.Nc
    if level == 'U_IID':
        return np.zeros((T, Nc), dtype=np.int32)
    ind = S.icodes.astype(np.int32)            # (T, Nc) 行业码, 已是逐日 PIT
    if level == 'I_IID':
        return ind
    # 行业 x 当日池内市值三档
    lm = S.log_mcap.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]
    tier = np.full((T, Nc), -1, dtype=np.int32)
    for t in range(T):
        m = S.p0c[t] & np.isfinite(lm[t])
        if m.sum() < 3:
            continue
        v = lm[t][m]
        q1, q2 = np.percentile(v, [33.3333, 66.6667])
        tt = np.digitize(lm[t], [q1, q2]).astype(np.int32)
        tier[t] = np.where(m, tt, -1)
    out = np.where((ind >= 0) & (tier >= 0), ind * 3 + tier, -1).astype(np.int32)
    return out


def matched_draws(S, target, L, codes, n_draws, rng, keep_examples=8):
    """对 target 做同人数(+同分层人数)的随机抽取。返回 (draw 均值数组, 示例)。"""
    T, Nc = target.shape
    pool = S.p0c
    sums = np.zeros(n_draws)
    cnts = np.zeros(n_draws)
    examples = []
    for t in range(T):
        tgt = target[t]
        if not tgt.any():
            continue
        avail = pool[t] & np.isfinite(L[t]) & (codes[t] >= 0)
        if not avail.any():
            continue
        # 逐分层: target 在该层有几只, 就从池内该层抽几只
        ct = codes[t]
        for s in np.unique(ct[tgt & avail]):
            k = int((tgt & avail & (ct == s)).sum())
            if k <= 0:
                continue
            pos = np.where(avail & (ct == s))[0]
            if len(pos) == 0:
                continue
            kk = min(k, len(pos))
            r = rng.random((n_draws, len(pos)))
            take = np.argpartition(r, kk - 1, axis=1)[:, :kk] if kk < len(pos) else None
            if take is None:
                v = L[t][pos]
                sums += v.sum()
                cnts += len(pos)
            else:
                v = L[t][pos][take]            # (n_draws, kk)
                sums += v.sum(axis=1)
                cnts += kk
        if len(examples) < keep_examples and (t % max(1, T // keep_examples) == 0):
            examples.append(dict(date=str(S.dates[t])[:10], n_target=int(tgt.sum()),
                                 n_avail=int(avail.sum()),
                                 n_strata=int(len(np.unique(ct[tgt & avail])))))
    with np.errstate(invalid='ignore'):
        means = sums / np.where(cnts > 0, cnts, np.nan)
    return means, examples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--draws', type=int, default=128)
    a = ap.parse_args()
    seg = a.segment
    assert seg in H.DERIV_SEGS, 'R0 只在推导段'
    t0 = time.time()
    out = os.path.join(RES, 'T0_full_distribution')
    os.makedirs(out, exist_ok=True)

    S = H.seg(seg, verbose=False)
    lab_src, _ = T0.labels(S)
    L = lab_src.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]

    z = np.load(os.path.join(RES, 'stage_sets', 'stage_sets_%s.npz' % seg), allow_pickle=True)
    T, Nc = z['_shape']

    def unpack(nm):
        return np.unpackbits(z[nm])[:T * Nc].reshape(T, Nc).astype(bool)

    # 目标集合: 池内真实最差/最好 20% (逐日) + 四个母体的 B 与 D
    targets = {}
    worst = np.zeros((T, Nc), bool)
    best = np.zeros((T, Nc), bool)
    for t in range(T):
        m = S.p0c[t] & np.isfinite(L[t])
        n = int(m.sum())
        if n < 10:
            continue
        idx = np.where(m)[0]
        o = idx[np.argsort(L[t][idx])]
        k = max(1, int(round(0.2 * n)))
        worst[t, o[:k]] = True
        best[t, o[-k:]] = True
    targets['pool_worst20'] = worst
    targets['pool_best20'] = best
    for p in PARENTS:
        targets['%s_B' % p] = unpack('%s_B' % p)
        targets['%s_D' % p] = unpack('%s_D' % p)

    levels = ['U_IID', 'I_IID', 'IxM_IID']
    code_of = {lv: strata_codes(S, lv) for lv in levels}
    rows, ex_all = [], {}
    for tname, M in targets.items():
        real = L[M]
        real = real[np.isfinite(real)]
        rmean = float(real.mean()) if real.size else np.nan
        for lv in levels:
            rng = np.random.default_rng(SEED + abs(hash((seg, tname, lv))) % 10 ** 6)
            means, ex = matched_draws(S, M, L, code_of[lv], a.draws, rng)
            mm = float(np.nanmean(means))
            sd = float(np.nanstd(means, ddof=1))
            mcse = sd / np.sqrt(np.isfinite(means).sum())
            rows.append(dict(
                segment=seg, target=tname, match_level=lv, n_draws=a.draws,
                real_mean_bp=round(rmean, 3), pseudo_mean_bp=round(mm, 3),
                gap_real_minus_pseudo=round(rmean - mm, 3),
                explained_frac=(round(mm / rmean, 4) if rmean not in (0, np.nan)
                                and np.isfinite(rmean) and rmean != 0 else np.nan),
                pseudo_sd=round(sd, 4), mcse_bp=round(mcse, 4),
                mcse_ok_0p05pp=bool(mcse <= 5.0),   # 0.05 个年化百分点 = 5 bp
                n_cells=int(M.sum())))
            ex_all['%s|%s' % (tname, lv)] = ex
            print('  %-14s %-8s 真实 %8.2f 伪 %8.2f 差 %8.2f (解释 %5.1f%%) MCSE %.3f'
                  % (tname, lv, rmean, mm, rmean - mm,
                     100.0 * mm / rmean if rmean else float('nan'), mcse), flush=True)

    pd.DataFrame(rows).to_csv(
        os.path.join(out, 'pseudo_paths_%s.csv' % seg), index=False)
    with open(os.path.join(out, 'pseudo_examples_%s.json' % seg), 'w') as fh:
        json.dump(ex_all, fh, indent=1, ensure_ascii=False)
    print('  [%s] 合计 %.0fs' % (seg, time.time() - t0))


if __name__ == '__main__':
    main()
