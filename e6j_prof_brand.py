# -*- coding: utf-8 -*-
"""B 随机单路径各环节耗时剖析（只测时，不写结果）：置换 / 混合 / kept / DEV / pnl(7H) / 逐年汇总。用 2010-2014 R2 × B3A 的一个测量组、8 条路径。"""
import e6j_boot  # noqa: F401
import time
import numpy as np
import pandas as pd
import e6j_core as J
import e6j_engine as EN
import e6j_random as RND
import e6j_run_b as RB
import e6j_run_brand as BR

env = EN.Env('2010-2014', with_prod=False)
ci, SE = env.ci, env.SE
rows = pd.read_csv(J.RES + '/registry/rows_B.csv')
g = rows[(rows.block == 'B3A') & (rows.measurement_id == 'J_B3A_COVP_CC_W20')]
st = EN.research_structure(env, 'R2', 'K')
raw = RB.raw_cells(env, '2010-2014', 'J_B3A_COVP_CC_W20', 'J')
cache = RB.ns_cache(env, raw)
zc = {d: RB.pct_of(env, cache, d) for d in g.direction}
zhi = zc['high_bad']; V = np.isfinite(zhi); vt, vc = ci.t[V], ci.c[V]
T = {'perm': 0, 'blend': 0, 'kept': 0, 'dev': 0, 'pnl': 0, 'yr': 0}
years = pd.to_datetime(pd.Index(env.S.dates).astype(str)).year.values
for p in range(8):
    t0 = time.time()
    key = RND.path_key('E6j.B.prof', 'x', 'R2', 'native', 'IID', p)
    u = env.grid.u_cells(key, vt, vc, 1)
    don = BR.donor_map(zhi[V], vt.astype(np.int64), u)
    zp = np.full(ci.n, np.nan); zp[V] = zc['high_bad'][V][don]
    t1 = time.time(); T['perm'] += t1 - t0
    Q = np.vstack([EN.blend(st.q0, [(1.0, zp[None, :])], a) for a in (0.125, 0.25, 0.5)])
    t2 = time.time(); T['blend'] += t2 - t1
    K = st.kept(Q)
    t3 = time.time(); T['kept'] += t3 - t2
    for j in range(3):
        tt, cc = ci.t[K[j]], ci.c[K[j]]
        a0 = time.time(); w = SE.dev(tt, cc); a1 = time.time(); T['dev'] += a1 - a0
        led = SE.pnl(tt, cc, w, EN.HS_B, 8.0); a2 = time.time(); T['pnl'] += a2 - a1
        for H in EN.HS_B:
            n = led[H][3]
            for y in sorted(set(years)):
                m = (years == y) & np.isfinite(n)
                _ = np.mean(n[m])
        T['yr'] += time.time() - a2
print({k: round(v / 24, 4) for k, v in T.items()}, '秒 / 掩码')
