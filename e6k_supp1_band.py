# -*- coding: utf-8 -*-
"""E6k supplement_1（VERIFY brief §6 背景段"统计量是别的量"分支；事后口径，不替代登记结果；REPORT 与 simultaneous_band_q95.csv 不改）。
登记的同时带（e6k_bootstrap.py）统计量是标准化的：M_b = max_j |(FULL*_bj − FULL_j) / SE_j|，q95 以 SE 为单位，逐对象半宽 = q95 · SE_j。
本脚本在同一 bootstrap 路径上（e6k_bootstrap.seg_counts / load_net8：同种子、同段内分层 stationary、同计数矩阵、同 ok 集合 = SE > 0 且无无支持 draw）给出与 FULL 同单位的两种读数：
  ① 未标准化 max-abs：U_b = max_j |FULL*_bj − FULL_j|（年化百分点），primary144 与 all、L 20 / 60、2,000 draws 的 q90 / q95 / q99；
     primary144 中 |FULL_j| 超过各分位的对象数（不设门，只给数）；
  ② 登记统计量折成同单位：q95（登记值，SE 单位）× SE_j 的逐对象半宽（primary144：中位 / 最大 / 最小），与逐对象 q025 / q975 的半宽并列。
输出 results/full/bootstrap/supplement_1/（新目录；已存在即拒绝）。"""
import e6k_boot  # noqa: F401
import os
import sys

import numpy as np
import pandas as pd

import e6k_core as K
import e6j_stats as ST
import e6k_seal as SEAL
import e6k_bootstrap as BS


def main():
    for pkg in ('deriv', 'post'):
        ok, bad = SEAL.verify(pkg)
        if not ok:
            raise RuntimeError('seal_%s 核对失败：%s' % (pkg, bad[:5]))
    od = K.P('results', 'full', 'bootstrap', 'supplement_1')
    if os.path.exists(od):
        raise RuntimeError('%s 已存在（只增不删、不覆盖）' % K.rel(od))
    BB = pd.read_csv(K.P('registry', 'bootstrap_comparisons_E6k.csv'))
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    prim = set('CP|' + D[D.primary144].desc_id)
    band0 = pd.read_csv(K.P('results', 'full', 'bootstrap', 'simultaneous_band_q95.csv'))
    nets = {s: BS.load_net8(s) for s in K.SEGMENTS}
    Ts = {s: len(next(iter(nets[s].values()))) for s in K.SEGMENTS}
    rows, objcnt, hw = [], [], []
    for L in BS.LS:
        counts = {s: BS.seg_counts(Ts[s], L, s) for s in K.SEGMENTS}
        mx = {'primary144': [], 'all': []}
        nok = {'primary144': 0, 'all': 0}
        pe, pse, pq = {}, {}, {}
        for c0 in range(0, len(BB), 8000):
            sub = BB.iloc[c0:c0 + 8000]
            num = np.zeros((BS.NB, len(sub)))
            den = np.zeros((BS.NB, len(sub)))
            en = np.zeros(len(sub))
            ed = np.zeros(len(sub))
            for s in K.SEGMENTS:
                M = np.zeros((Ts[s], len(sub)))
                V = np.zeros((Ts[s], len(sub)))
                for j, r in enumerate(sub.itertuples()):
                    x, y = nets[s].get(r.a), nets[s].get(r.b)
                    if x is None or y is None:
                        continue
                    d = x - y
                    v = np.isfinite(d)
                    M[v, j] = d[v]
                    V[v, j] = 1.0
                num += counts[s] @ M
                den += counts[s] @ V
                en += M.sum(0)
                ed += V.sum(0)
            est = np.where(ed > 0, en / np.where(ed > 0, ed, 1) * ST.ANN, np.nan)
            with np.errstate(divide='ignore', invalid='ignore'):
                draws = np.where(den > 0, num / den * ST.ANN, np.nan)
            nosup = (den <= 0).sum(0)
            se = np.nanstd(draws, axis=0, ddof=1)
            ok_ = np.isfinite(se) & (se > 0) & (nosup == 0)
            if ok_.any():
                mx['all'].append(np.max(np.abs(draws[:, ok_] - est[ok_][None, :]), axis=1))
                nok['all'] += int(ok_.sum())
            pm = np.array([c in prim for c in sub.comparison_id.values]) & ok_
            if pm.any():
                mx['primary144'].append(np.max(np.abs(draws[:, pm] - est[pm][None, :]), axis=1))
                nok['primary144'] += int(pm.sum())
                q = np.nanpercentile(draws[:, pm], [2.5, 97.5], axis=0)
                for jj, (cid, e, sj) in enumerate(zip(sub.comparison_id.values[pm], est[pm], se[pm])):
                    pe[cid], pse[cid], pq[cid] = e, sj, (q[0, jj], q[1, jj])
            K.log('supp1 band L%d chunk %d / %d' % (L, c0 + len(sub), len(BB)))
        for setname in ('primary144', 'all'):
            m = np.max(np.vstack(mx[setname]), axis=0)
            q90, q95, q99 = np.percentile(m, [90, 95, 99])
            rows.append(dict(query_id='S1-Q01', L=L, set=setname, statistic='max_j |FULL*_bj − FULL_j|（年化百分点，未标准化）', q90=float(q90), q95=float(q95),
                             q99=float(q99), draws=BS.NB, n_comparisons=nok[setname]))
        f = np.array([pe[c] for c in sorted(pe)])
        for qn, qv in zip(('q90', 'q95', 'q99'), [r['q%s' % x] for r in rows[-2:-1] for x in ('90', '95', '99')]):
            objcnt.append(dict(query_id='S1-Q02', L=L, quantile=qn, value=float(qv), n_objects=len(f), n_FULL_above=int((f > qv).sum()),
                               n_FULL_below_neg=int((f < -qv).sum())))
        q95s = float(band0[(band0.L == L) & (band0.set == 'primary144')].q95_maxabs_centered.iloc[0])
        h_band = np.array([q95s * pse[c] for c in sorted(pse)])
        h_ci = np.array([0.5 * (pq[c][1] - pq[c][0]) for c in sorted(pq)])
        hw.append(dict(query_id='S1-Q03', L=L, set='primary144', q95_registered_se_units=q95s, n_objects=len(h_band),
                       band_halfwidth_median=float(np.median(h_band)), band_halfwidth_min=float(h_band.min()), band_halfwidth_max=float(h_band.max()),
                       ci95_halfwidth_median=float(np.median(h_ci)), ci95_halfwidth_max=float(h_ci.max()), se_median=float(np.median([pse[c] for c in pse])),
                       se_max=float(max(pse.values()))))
    os.makedirs(od)
    p1 = os.path.join(od, 'simultaneous_band_q95_v2.csv')
    p2 = os.path.join(od, 'primary144_exceed_counts.csv')
    p3 = os.path.join(od, 'registered_band_halfwidths.csv')
    K.atomic_write_csv(p1, pd.DataFrame(rows))
    K.atomic_write_csv(p2, pd.DataFrame(objcnt))
    K.atomic_write_csv(p3, pd.DataFrame(hw))
    K.write_receipt('supp1_band', [p1, p2, p3], 'SUCCEEDED', draws=BS.NB, note='事后口径；同一 bootstrap 路径与 ok 集合；不替代登记结果；REPORT 不改')
    for p in (p1, p2, p3):
        print(pd.read_csv(p).to_string(), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
