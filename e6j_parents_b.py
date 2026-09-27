# -*- coding: utf-8 -*-
"""E6j B 块研究母体（R1 / R2 / A06 / A08）的原生 8bp 日账本与冲击括号，H ∈ {1,2,3,5,10,15,20}（母体 = E6i 已跑对象，非 B 新对象）。
写 accounts/B/<段>/parents.npz；锚：H5 与 E6i 已存母体账本逐位（锚 2 L4b 同式）。"""
import e6j_boot  # noqa: F401
import os
import sys
import numpy as np

import e6j_core as J
import e6j_engine as EN

OUT = os.path.join(J.RES, 'accounts', 'B')


def run(pname):
    env = EN.Env(pname, with_prod=False)
    import e6g_c as GC
    mkt = GC.MarketCtx(env.S)
    ci, SE, T = env.ci, env.SE, env.S.T
    keys, arrs = [], {k: [] for k in ('gross', 'pos', 'turn', 'net8', 'bracket', 'qmiss', 'wsum')}
    for mn in ('R1', 'R2', 'A06', 'A08'):
        M = env.R.mother(mn)
        k = M.B_c
        t, c = ci.t[k], ci.c[k]; w = SE.dev(t, c)
        led = SE.pnl(t, c, w, EN.HS_B, 8.0)
        order = np.argsort(t, kind='stable'); ts = t[order]; bnd = np.searchsorted(ts, np.arange(T + 1))
        idx = [c[order[bnd[d]:bnd[d + 1]]] for d in range(T)]; val = [w[order[bnd[d]:bnd[d + 1]]] for d in range(T)]
        for H in EN.HS_B:
            g, pos, tu, n = led[H]
            br = GC.profile_and_impact(mkt, idx, val, H, full_profile=False)
            keys.append('%s|H%d' % (mn, H))
            for kk, v in (('gross', g), ('pos', pos), ('turn', tu), ('net8', n), ('bracket', br[0]['sqrt']), ('qmiss', br[3]),
                          ('wsum', np.bincount(t, weights=w, minlength=T))):
                arrs[kk].append(v)
    od = os.path.join(OUT, pname); os.makedirs(od, exist_ok=True)
    p = os.path.join(od, 'parents.npz')
    J.atomic_write_npz(p, keys=np.array(keys), dates=np.array([str(d)[:10] for d in env.dates]), **{k: np.vstack(v) for k, v in arrs.items()})
    J.write_receipt('parents_b_%s' % pname, [p], 'SUCCEEDED', n=len(keys))
    return 0


if __name__ == '__main__':
    sys.exit(run(sys.argv[sys.argv.index('--segment') + 1]))
