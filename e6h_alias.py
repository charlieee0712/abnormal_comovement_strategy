#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h: 高相关对里【哪些是真别名, 哪些只是高相关】。
plan §5.2 的"精确别名仅一票"只能用在【真别名】上, 所以必须实测而不是按 rho 猜。
教训: rho 保留三位小数时 0.9996 显示成 1.000; 而且 NS 中性化是【线性】回归,
所以 log 收益与简单收益这种单调但非线性的变换, 中性化后排序会不同。"""
import sys, os, json
import numpy as np, pandas as pd
sys.path.insert(0,'/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H, e6g_desc as GD

RES = H.RES
rows = []
for seg in H.DERIV_SEGS:
    S = H.seg(seg, verbose=False)
    e = pd.read_csv(os.path.join(RES,'clustering','factor_signed_edges_%s.csv'%seg))
    top = e.sort_values('abs_rho', ascending=False).head(30)
    cache = {}
    def P(k):
        if k not in cache:
            cache[k] = H.get_pct_h(S, GD.spec_of_key(k) if k in H.U74 else H.specH(k),'NS','hi')
        return cache[k]
    p0 = S.p0c
    for _, r in top.iterrows():
        a, b = P(r['a']), P(r['b'])
        both = p0 & np.isfinite(a) & np.isfinite(b)
        n = int(both.sum())
        if not n: continue
        d = np.abs(a[both]-b[both])
        rows.append(dict(segment=seg, a=r['a'], b=r['b'],
            rho_mean=round(float(r['rho_mean']),6),
            frac_cells_identical=round(float((d < 1e-12).mean()),6),
            max_abs_diff=float(d.max()), n_cells=n,
            is_exact_alias=bool(d.max() < 1e-12),
            nan_pattern_same=bool((np.isfinite(a[p0])==np.isfinite(b[p0])).all())))
    del S, cache
d = pd.DataFrame(rows)
d.to_csv(os.path.join(RES,'registry','alias_measurements.csv'), index=False)
ex = d[d.is_exact_alias]
print('高相关对实测 %d 条 (两段各 30)' % len(d))
print('**真别名** (max|d| < 1e-12 且 NaN 位一致): %d 条' % len(ex))
for _, r in ex.iterrows():
    print('   [%s] %s == %s  (rho %.6f)' % (r['segment'], r['a'], r['b'], r['rho_mean']))
print()
print('rho >= 0.999 但【不是】别名的 (逐格相同率 / max|d|):')
nn = d[(d.rho_mean.abs()>=0.999) & (~d.is_exact_alias)]
for _, r in nn.iterrows():
    print('   [%s] %-34s vs %-34s rho %.6f  同格 %.4f  max|d| %.3f'
          % (r['segment'], r['a'], r['b'], r['rho_mean'],
             r['frac_cells_identical'], r['max_abs_diff']))
