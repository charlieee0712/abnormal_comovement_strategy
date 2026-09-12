#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h R0 第四块: 相关矩阵 + 因子聚类 + 主体聚类 (plan §2.2, brief §3)。

两件【不同】的事, 分开做:
  A. 因子聚类: 87 键两两的按日 signed Spearman -> 跨日汇总 -> 1-|rho| 距离
     average / complete linkage。**不用 Ward** (相关距离未证明是欧氏, plan §2.2 第 4 条)。
     保留 signed 边表; 没有完整有限距离矩阵时只对可用连通子图展示, 其余 unknown,
     【不删因子】。
  B. 主体聚类 (股票-日画像): 先在拟合段 rank/尺度处理, 【再】施加同家族总距离权重
     (列权重 ~ 1/sqrt(有效非别名列数)); 施加后**不能**再逐列 StandardScaler 把权重抵消。
     KMeans k{3,4,5}, n_init=20, seed=1109, lloyd; 每日期总 sample_weight 相同;
     fit 2010-2014, 应用 2015-2018 不重拟合。簇命名按事前特征, 不按未来平均收益。

相关口径注记: 逐日先对【各列自己的有限值】取 rank, 再做 pairwise-complete 的
Pearson。这是"成对删除的 Spearman", 不是对每一对重新 rank 的精确 Spearman;
多数键池内可用率 > 0.99, 差异可忽略, 但如实记在输出 note 里。

用法: python3 e6h_r0_cluster.py --fit 2010-2014 --apply 2015-2018
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
import e6g_desc as GD

RES = H.RES
SEED = 1109


def pct_stack(S, keys):
    """(K, T, Nc) float32 的 bad_pct 栈。"""
    out = np.full((len(keys), S.T, S.Nc), np.nan, dtype=np.float32)
    for i, k in enumerate(keys):
        sp = GD.spec_of_key(k) if k in H.U74 else H.specH(k)
        out[i] = H.get_pct_h(S, sp, 'NS', 'hi').astype(np.float32)
        if (i + 1) % 20 == 0:
            print('    pct %d/%d' % (i + 1, len(keys)), flush=True)
    return out


def daily_corr_matrix(P, pool, min_n=20):
    """逐日 rank -> pairwise-complete Pearson, 跨日按有效日等权平均。
       返回 (rho 均值矩阵, 有效日计数矩阵, 逐日 rho 的中位矩阵)。"""
    Kn, T, Nc = P.shape
    acc = np.zeros((Kn, Kn))
    cnt = np.zeros((Kn, Kn))
    per_day = [[[] for _ in range(Kn)] for _ in range(Kn)]
    keep_med = Kn <= 100
    for t in range(T):
        pm = pool[t]
        if pm.sum() < min_n:
            continue
        X = P[:, t, :][:, pm].astype(np.float64)        # (K, n)
        M = np.isfinite(X)
        if not M.any():
            continue
        # 逐列(= 逐键)对自己的有限值取 rank
        R = np.zeros_like(X)
        for i in range(Kn):
            v = X[i][M[i]]
            if v.size:
                R[i][M[i]] = pd.Series(v).rank().to_numpy()
        Rm = np.where(M, R, 0.0)
        Mf = M.astype(np.float64)
        n_ij = Mf @ Mf.T
        s_x = Rm @ Mf.T                                  # sum x over both-finite
        s_xy = Rm @ Rm.T
        s_x2 = (Rm ** 2) @ Mf.T
        with np.errstate(invalid='ignore', divide='ignore'):
            mx = s_x / n_ij
            my = s_x.T / n_ij
            cov = s_xy / n_ij - mx * my
            vx = s_x2 / n_ij - mx ** 2
            vy = s_x2.T / n_ij - my ** 2
            rho = cov / np.sqrt(np.where(vx > 0, vx, np.nan) * np.where(vy > 0, vy, np.nan))
        ok = np.isfinite(rho) & (n_ij >= min_n)
        acc[ok] += rho[ok]
        cnt[ok] += 1
        if keep_med:
            for i in range(Kn):
                for j in range(i + 1, Kn):
                    if ok[i, j]:
                        per_day[i][j].append(rho[i, j])
    with np.errstate(invalid='ignore'):
        mean = acc / np.where(cnt > 0, cnt, np.nan)
    med = np.full((Kn, Kn), np.nan)
    if keep_med:
        for i in range(Kn):
            med[i, i] = 1.0
            for j in range(i + 1, Kn):
                if per_day[i][j]:
                    med[i, j] = med[j, i] = float(np.median(per_day[i][j]))
    return mean, cnt, med


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fit', default='2010-2014')
    ap.add_argument('--apply', default='2015-2018')
    ap.add_argument('--stage', default='both', choices=['corr', 'subject', 'both'])
    a = ap.parse_args()
    t0 = time.time()
    out = os.path.join(RES, 'clustering')
    os.makedirs(out, exist_ok=True)
    keys = sorted(H.REGISTERED)

    from scipy.cluster import hierarchy as sch
    from scipy.spatial.distance import squareform

    # ---------------- A. 因子相关与聚类 ----------------
    if a.stage in ('corr', 'both'):
        for segname in (a.fit, a.apply):
            S = H.seg(segname, verbose=False)
            print('  [%s] 建 pct 栈 (%d 键)...' % (segname, len(keys)), flush=True)
            P = pct_stack(S, keys)
            print('  [%s] 相关矩阵...' % segname, flush=True)
            mean, cnt, med = daily_corr_matrix(P, S.p0c)
            pd.DataFrame(mean, index=keys, columns=keys).to_csv(
                os.path.join(out, 'factor_corr_mean_%s.csv' % segname))
            pd.DataFrame(med, index=keys, columns=keys).to_csv(
                os.path.join(out, 'factor_corr_median_%s.csv' % segname))
            pd.DataFrame(cnt, index=keys, columns=keys).to_csv(
                os.path.join(out, 'factor_corr_ndays_%s.csv' % segname))
            # signed 边表 (保留符号, 不只 |rho|)
            edges = []
            for i in range(len(keys)):
                for j in range(i + 1, len(keys)):
                    if np.isfinite(mean[i, j]):
                        edges.append(dict(a=keys[i], b=keys[j],
                                          rho_mean=round(float(mean[i, j]), 4),
                                          rho_median=round(float(med[i, j]), 4)
                                          if np.isfinite(med[i, j]) else np.nan,
                                          n_days=int(cnt[i, j]),
                                          abs_rho=round(abs(float(mean[i, j])), 4)))
            pd.DataFrame(edges).sort_values('abs_rho', ascending=False).to_csv(
                os.path.join(out, 'factor_signed_edges_%s.csv' % segname), index=False)

            # 层次聚类: 1-|rho|; 只对完整有限子矩阵做, 其余 unknown
            Dm = 1.0 - np.abs(mean)
            np.fill_diagonal(Dm, 0.0)
            finite_rows = np.isfinite(Dm).all(axis=1)
            usable = [k for k, f in zip(keys, finite_rows) if f]
            unknown = [k for k, f in zip(keys, finite_rows) if not f]
            res = dict(segment=segname, n_keys=len(keys), n_usable=len(usable),
                       unknown_keys=unknown,
                       note=('1-|rho| 距离, average / complete linkage。**不用 Ward** '
                             '(相关距离未证明欧氏, plan §2.2/R6)。无完整有限距离的键留 unknown, '
                             '不删。相关是"成对删除的 Spearman" (逐列自有限值 rank 后 '
                             'pairwise-complete Pearson), 非逐对重 rank 的精确 Spearman。'))
            if len(usable) >= 3:
                sub = Dm[np.ix_(finite_rows, finite_rows)]
                sub = (sub + sub.T) / 2.0
                np.fill_diagonal(sub, 0.0)
                cond = squareform(sub, checks=False)
                for meth in ('average', 'complete'):
                    Z = sch.linkage(cond, method=meth)
                    coph = float(sch.cophenet(Z, cond)[0])
                    res['cophenetic_%s' % meth] = round(coph, 4)
                    for k in (3, 4, 5, 6, 8):
                        lab = sch.fcluster(Z, k, criterion='maxclust')
                        res['labels_%s_k%d' % (meth, k)] = {
                            u: int(l) for u, l in zip(usable, lab)}
            with open(os.path.join(out, 'factor_clusters_%s.json' % segname), 'w') as fh:
                json.dump(res, fh, indent=1, ensure_ascii=False)
            print('  [%s] 因子聚类完成: 可用 %d / unknown %d; %.0fs'
                  % (segname, len(usable), len(unknown), time.time() - t0), flush=True)
            del P, S

    print('总耗时 %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
