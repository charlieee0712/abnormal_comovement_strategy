# -*- coding: utf-8 -*-
"""E6k bootstrap（plan §10.4；brief §7；A15 / A16）。seal_deriv + seal_post 之后运行。
  四历史段内分层 stationary（Politis–Romano，几何块长均值 L ∈ {20, 60}，段内环绕、不跨段接缝），每 L 各 2,000 次；
  全部对象共享同一套段内索引（stable seed：rng_for('E6k', 'bootstrap', L, 段)）；抽的是已生成的逐日配对 PnL 向量（原日历行与缺失掩码一起抽），
  不回喂 HG / 持仓引擎；FULL* = Σ_s num*_s / Σ_s den*_s × 252 × 100（固定段、实际有效分母）。
  计数矩阵法：C_s[b, t] = 第 b 次抽样中段 s 第 t 日被抽中的次数；num* = C_s @ d_s（缺失置 0），den* = C_s @ 1(有效)。
  输出（results/full/bootstrap/）：逐比较 comparison_id 的点估、q2.5 / q50 / q97.5、draw SE（L 20 / 60 各列）；
  固定比较集合（主 144 / 预定机制块 / 全部）的中心化最大标准化偏差 max_j |(D*_bj − D̂_j)/SE_j| 的 95% 分位（同时带半宽 = q95·SE_j）；
  SE = 0 的真恒等对象单列（不进最大值）；某 draw 无支持（den* = 0）按"无支持"计数、不用 nanmax 改域。无 FWER / 同时带准入门。"""
import e6k_boot  # noqa: F401
import os
import sys
import glob
import argparse

import numpy as np
import pandas as pd

import e6k_core as K
import e6j_stats as ST
import e6k_seal as SEAL

NB = 2000
LS = (20, 60)


def seg_counts(T, L, seg):
    rng = K.rng_for('E6k', 'bootstrap', int(L), seg)
    C = np.zeros((NB, T), np.float64)
    for b in range(NB):
        idx = ST.stationary_indices(T, L, rng)
        C[b] = np.bincount(idx, minlength=T)
    return C


def load_net8(seg):
    out = {}
    for f in sorted(glob.glob(K.P('accounts', seg, '*.npz'))):
        if os.path.basename(f).startswith('weights_'):
            continue
        z = K.npz(f)
        for i, did in enumerate(map(str, z['desc'])):
            out[did] = z['d_net8'][i]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chunk', type=int, default=8000)
    a = ap.parse_args()
    for pkg in ('deriv', 'post'):
        ok, bad = SEAL.verify(pkg)
        if not ok:
            raise RuntimeError('seal_%s 核对失败：%s' % (pkg, bad[:5]))
    BB = pd.read_csv(K.P('registry', 'bootstrap_comparisons_E6k.csv'))
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    prim = set('CP|' + D[D.primary144].desc_id)
    od = K.P('results', 'full', 'bootstrap')
    os.makedirs(od, exist_ok=True)
    nets = {s: load_net8(s) for s in K.SEGMENTS}
    counts = {(s, L): seg_counts(len(next(iter(nets[s].values()))), L, s) for s in K.SEGMENTS for L in LS}
    rows = []
    maxstats = {L: {'primary144': [], 'all': []} for L in LS}
    ids = BB.comparison_id.values
    for c0 in range(0, len(BB), a.chunk):
        sub = BB.iloc[c0:c0 + a.chunk]
        est_num = np.zeros(len(sub))
        est_den = np.zeros(len(sub))
        Dseg = {}
        for s in K.SEGMENTS:
            T = len(next(iter(nets[s].values())))
            M = np.zeros((T, len(sub)))
            V = np.zeros((T, len(sub)))
            for j, r in enumerate(sub.itertuples()):
                x, y = nets[s].get(r.a), nets[s].get(r.b)
                if x is None or y is None:
                    continue
                d = x - y
                v = np.isfinite(d)
                M[v, j] = d[v]
                V[v, j] = 1.0
            est_num += M.sum(0)
            est_den += V.sum(0)
            Dseg[s] = (M, V)
        est = np.where(est_den > 0, est_num / np.where(est_den > 0, est_den, 1) * ST.ANN, np.nan)
        for L in LS:
            parts = {s: (counts[(s, L)] @ Dseg[s][0], counts[(s, L)] @ Dseg[s][1]) for s in K.SEGMENTS}
            for grp, segs_ in (('DERIV', K.DERIV_SEGS), ('POST', K.POST_SEGS)):
                gn = sum(parts[s][0] for s in segs_)
                gd = sum(parts[s][1] for s in segs_)
                with np.errstate(divide='ignore', invalid='ignore'):
                    gdr = np.where(gd > 0, gn / gd * ST.ANN, np.nan)
                en = sum(Dseg[s][0].sum(0) for s in segs_)
                ed = sum(Dseg[s][1].sum(0) for s in segs_)
                gest = np.where(ed > 0, en / np.where(ed > 0, ed, 1) * ST.ANN, np.nan)
                gq = np.nanpercentile(gdr, [2.5, 97.5], axis=0)
                for j, cid in enumerate(sub.comparison_id.values):
                    rows.append(dict(comparison_id=cid, L=L, scope=grp, est=gest[j], q025=gq[0, j], q975=gq[1, j], se=float(np.nanstd(gdr[:, j], ddof=1))))
            num = sum(parts[s][0] for s in K.SEGMENTS)
            den = sum(parts[s][1] for s in K.SEGMENTS)
            with np.errstate(divide='ignore', invalid='ignore'):
                draws = np.where(den > 0, num / den * ST.ANN, np.nan)
            nosup = (den <= 0).sum(0)
            se = np.nanstd(draws, axis=0, ddof=1)
            q = np.nanpercentile(draws, [2.5, 50, 97.5], axis=0)
            for j, cid in enumerate(sub.comparison_id.values):
                rows.append(dict(comparison_id=cid, L=L, scope='FULL', est=est[j], q025=q[0, j], q50=q[1, j], q975=q[2, j], se=se[j], no_support_draws=int(nosup[j])))
            ok_ = np.isfinite(se) & (se > 0) & (nosup == 0)
            cen = (draws[:, ok_] - est[ok_][None, :]) / se[ok_][None, :]
            maxstats[L]['all'].append(np.max(np.abs(cen), axis=1) if cen.shape[1] else np.zeros(NB))
            pm = np.array([c in prim for c in sub.comparison_id.values]) & ok_
            if pm.any():
                cp = (draws[:, pm] - est[pm][None, :]) / se[pm][None, :]
                maxstats[L]['primary144'].append(np.max(np.abs(cp), axis=1))
        K.log('bootstrap chunk %d / %d' % (c0 + len(sub), len(BB)))
    R = pd.DataFrame(rows)
    p1 = os.path.join(od, 'bootstrap_comparisons.csv')
    K.atomic_write_csv(p1, R)
    band = []
    for L in LS:
        for setname, parts in maxstats[L].items():
            if not parts:
                continue
            mx = np.max(np.vstack(parts), axis=0)
            band.append(dict(L=L, set=setname, q95_maxabs_centered=float(np.percentile(mx, 95)), draws=NB))
    p2 = os.path.join(od, 'simultaneous_band_q95.csv')
    K.atomic_write_csv(p2, pd.DataFrame(band))
    K.write_receipt('bootstrap_full', [p1, p2], 'SUCCEEDED', comparisons=len(BB), draws=NB,
                    generator='blake2b-128(canonical_json(E6k, bootstrap, L, segment)) -> SeedSequence -> PCG64; e6j_stats.stationary_indices')
    print('bootstrap：%d 比较 × %d L' % (len(BB), len(LS)), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
