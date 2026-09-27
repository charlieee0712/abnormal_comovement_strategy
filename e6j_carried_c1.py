# -*- coding: utf-8 -*-
"""E6j carried C1（brief v1.2 §10；plan §7.7）：只在 E6i 已冻结的 N × 行业宽度 B 设计上重报 NATIVE / MATCH-CAP / ATTRIBUTION；
不另选 N 或 B 赢家。配置用 E6i 原函数重建（`e6i_c1.Sampler / Core / run_account` 同式；hashlib 优先级可重放），
先与 E6i 已存 net8 日序列逐位核对（NATIVE 锚），再对 E6i 主表的配对（固定 N 的 B16−B8、固定 B 的 N250−N100）做：
  MATCH-CAP：逐形成日两边目标权重都向下缩到共同资本后完整重跑（只缩不放）；
  ATTRIBUTION：E_c − E_b = ((P_c+P_b)/2)(u_c−u_b) + ((u_c+u_b)/2)(P_c−P_b)（两边都有仓位的日子；只一边有仓位的日子单列）。
部署视图 = 全日历；严格视图 = 两配置共同可行日（E6i feasible 表）。一个进程 = (段, seed 区间)。写 carried/C1/<段>/。"""
import e6j_boot  # noqa: F401
import os
import sys
import time
import itertools

import numpy as np
import pandas as pd

import e6j_core as J

OUT = os.path.join(J.RES, 'carried', 'C1')
COMBOS = [(100, 8), (100, 12), (100, 16), (150, 8), (150, 16), (250, 8), (250, 12), (250, 16)]
PAIRS = [('B16−B8', 'N=%d' % n, (n, 8), (n, 16)) for n in (100, 150, 250)] + [('N250−N100', 'B=%d' % b, (100, b), (250, b)) for b in (8, 12, 16)]


def run(seg, s0, s1):
    import e6i_core as I
    import e6i_c1 as C1
    import e6i_sparse as SP
    t0 = time.time()
    S = I.seg_i(seg, warm=False)
    cores = {mn: C1.Core(S, mn) for mn in C1.MOTHERS}
    smp = C1.Sampler(S)
    SE = SP.SparseEngine(S)
    E6 = {}
    base = os.path.join(J.E6I_RES, 'carried', 'C1', seg) if seg in J.DERIV_SEGS else os.path.join(J.E6I_RES, 'sealed', seg)
    rows, anchors = [], []
    T = S.T
    for seed in range(s0, s1 + 1):
        shard = [f for f in os.listdir(base) if f.startswith('c1_cross_') and f.endswith('.npz')]
        for f in shard:
            a, b = [int(x) for x in f[len('c1_cross_'):-4].split('-')]
            if a <= seed <= b and f not in E6:
                z = np.load(os.path.join(base, f), allow_pickle=False)
                E6[f] = dict(zip([str(k) for k in z['keys']], z['net8']))
                fz = pd.read_csv(os.path.join(base, f.replace('.npz', '_feasible.csv'))).set_index('domain')
                E6[f + ':feas'] = fz
        e6 = {}; feas = {}
        for f, v in E6.items():
            if f.endswith(':feas'):
                feas.update({d: v.loc[d].values.astype(bool) for d in v.index}); continue
            e6.update(v)
        for how in C1.ALLOCS:
            acc = {}
            for (N, B) in COMBOS:
                om, fe, _, _ = smp.omega(N, B, how, seed)
                dd = '%d|%d|%s|s%02d' % (N, B, how, seed)
                for mn, Cc in cores.items():
                    dom = om & ~Cc.dr
                    Cc.prepare(dom)
                    for q in C1.QS:
                        for scope in ('frozen', 'resample'):
                            m = Cc.select(dom, q, scope)
                            t, c = np.nonzero(m); w = SE.dev(t, c)
                            g, p, u, n = SE.pnl(t, c, w, (5,), 8.0)[5]
                            key = 'cross|%s|%s|%s|%s' % (dd, mn, q, scope)
                            ref = e6.get(key)
                            anchors.append(dict(key=key, max_abs=float(np.nanmax(np.abs(n - ref))) if ref is not None else np.nan))
                            acc[(N, B, mn, q, scope)] = dict(t=t, c=c, w=w, g=g, p=p, n=n, fe=fe)
            for (contrast, fixed, ka, kb) in PAIRS:
                for mn in C1.MOTHERS:
                    for q in C1.QS:
                        for scope in ('frozen', 'resample'):
                            A_ = acc[ka + (mn, q, scope)]; B_ = acc[kb + (mn, q, scope)]
                            pa = np.bincount(A_['t'], weights=A_['w'], minlength=T); pb = np.bincount(B_['t'], weights=B_['w'], minlength=T)
                            ps = np.minimum(pa, pb)
                            with np.errstate(divide='ignore', invalid='ignore'):
                                fa = np.where(pa > 0, ps / pa, 0.0); fb = np.where(pb > 0, ps / pb, 0.0)
                            na = SE.pnl(A_['t'], A_['c'], A_['w'] * fa[A_['t']], (5,), 8.0)[5][3]
                            nb = SE.pnl(B_['t'], B_['c'], B_['w'] * fb[B_['t']], (5,), 8.0)[5][3]
                            Ea, Eb, Pa, Pb = A_['g'], B_['g'], A_['p'], B_['p']
                            both = (Pa > 0) & (Pb > 0) & np.isfinite(Ea) & np.isfinite(Eb)
                            one = ((Pa > 0) ^ (Pb > 0)) & np.isfinite(Ea) & np.isfinite(Eb)
                            ua = np.where(both, Ea / np.where(Pa > 0, Pa, 1), 0.0); ub = np.where(both, Eb / np.where(Pb > 0, Pb, 1), 0.0)
                            unit = np.where(both, 0.5 * (Pa + Pb) * (ub - ua), 0.0); dep = np.where(both, 0.5 * (ua + ub) * (Pb - Pa), 0.0)
                            ones = np.where(one, Eb - Ea, 0.0)
                            strict = A_['fe'] & B_['fe']
                            d_native = B_['n'] - A_['n']; d_sc = nb - na
                            rows.append(dict(segment=seg, mother=mn, q=q, scope=scope, alloc=how, seed=seed, contrast=contrast, fixed=fixed,
                                             native_d_ann=float(np.nanmean(d_native)) * J.ANN, samecap_d_ann=float(np.nanmean(d_sc)) * J.ANN,
                                             attr_unit_ann=float(np.nanmean(np.where(np.isfinite(Ea) & np.isfinite(Eb), unit, np.nan))) * J.ANN,
                                             attr_deploy_ann=float(np.nanmean(np.where(np.isfinite(Ea) & np.isfinite(Eb), dep, np.nan))) * J.ANN,
                                             attr_onesided_ann=float(np.nanmean(np.where(np.isfinite(Ea) & np.isfinite(Eb), ones, np.nan))) * J.ANN,
                                             gross_d_ann=float(np.nanmean(Eb - Ea)) * J.ANN,
                                             strict_days=int(strict.sum()),
                                             strict_native_d_ann=(float(np.nanmean(d_native[strict])) * J.ANN if strict.any() else np.nan),
                                             strict_samecap_d_ann=(float(np.nanmean(d_sc[strict])) * J.ANN if strict.any() else np.nan),
                                             pos_a=float(Pa.mean()), pos_b=float(Pb.mean()), matched_capital_share=float(ps.sum() / max(pb.sum(), 1e-300))))
        J.log('C1 %s seed %d done %.0fs' % (seg, seed, time.time() - t0), os.path.join(J.RES, 'logs', 'carried_c1_%s.log' % seg))
    od = os.path.join(OUT, seg); os.makedirs(od, exist_ok=True)
    p = os.path.join(od, 'c1_capital_views_s%02d-%02d.csv' % (s0, s1)); J.atomic_write_csv(p, pd.DataFrame(rows))
    pa = os.path.join(od, 'c1_native_anchor_s%02d-%02d.csv' % (s0, s1)); J.atomic_write_csv(pa, pd.DataFrame(anchors))
    an = pd.DataFrame(anchors)
    J.write_receipt('carried_c1_%s_s%02d-%02d' % (seg, s0, s1), [p, pa], 'SUCCEEDED', n_pairs=len(rows),
                    native_anchor_max=float(an.max_abs.max()) if len(an) else np.nan, native_anchor_missing=int(an.max_abs.isna().sum()))
    return 0


if __name__ == '__main__':
    a = sys.argv
    s = a[a.index('--seeds') + 1].split('-')
    sys.exit(run(a[a.index('--segment') + 1], int(s[0]), int(s[1])))
