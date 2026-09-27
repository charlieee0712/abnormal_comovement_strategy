# -*- coding: utf-8 -*-
"""E6j B 随机分段计时（只测时，不写结果、不写回执）：复刻 e6j_run_brand 一个 (母体, 块) 的第一个 (槽位, 测量) 组，
n 条路径 × 三机制，拆 draw（u_cells / donor_map）/ blend / kept（第一关 / 第二关）/ edit_entry / dev / pnl（7 个 H）。"""
import e6j_boot  # noqa: F401
import os
import sys
import time
import json

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_engine as EN
import e6j_random as RND
import e6j_run_b as RB
import e6j_run_brand as RBR
import e6i_randoms as IR

acc = {}


def tick(k, t0):
    acc[k] = acc.get(k, 0.0) + (time.perf_counter() - t0)


_keep, _s2, _ee = IR.KeepDom.keep, IR.dep_stage2_keep, RND.edit_entry


def keep(self, *a, **k):
    t0 = time.perf_counter(); r = _keep(self, *a, **k); tick('kept.KeepDom_keep', t0); return r


def s2(*a, **k):
    t0 = time.perf_counter(); r = _s2(*a, **k); tick('kept.stage2_T', t0); return r


IR.KeepDom.keep, IR.dep_stage2_keep = keep, s2


def main():
    a = sys.argv
    pname, mother, block, n = a[a.index('--segment') + 1], a[a.index('--mother') + 1], a[a.index('--block') + 1], int(a[a.index('--paths') + 1])
    t0 = time.perf_counter()
    rows = pd.read_csv(os.path.join(J.RES, 'registry', 'rows_B.csv'))
    rows = rows[(rows.block == block) & rows.mothers.str.split('|').apply(lambda m: mother in m)]
    env = EN.Env(pname, with_prod=False)
    ci, SE = env.ci, env.SE
    ind = np.asarray(env.S.icodes)
    lm = env.S.log_mcap.reindex(index=env.S.pool0.index, columns=env.S.pool0.columns).values[:, env.S.ccols]
    (slot, mid), grp = next(iter(rows.groupby(['slot', 'measurement_id'], sort=True)))
    st = EN.research_structure(env, mother, slot)
    parent = st.kept(st.q0[None, :])[0]; legal = ~st.drop
    raw = RB.raw_cells(env, pname, mid, grp.source.iloc[0])
    cache = RB.ns_cache(env, raw)
    zc = {d: RB.pct_of(env, cache, d) for d in grp.direction.unique()}
    zhi = zc['high_bad'] if 'high_bad' in zc else RB.pct_of(env, cache, 'high_bad')
    V = np.isfinite(zhi); vt, vc = ci.t[V], ci.c[V]
    Vd = np.zeros((ci.T, ci.Nc), bool); Vd[vt, vc] = True
    oldk = np.full((ci.T, ci.Nc), np.nan); oldk[ci.t, ci.c] = st.q0
    rr_, cc_, cell, _ = RND.cond_cells(Vd, ind, lm, oldk)
    cid = np.full((ci.T, ci.Nc), -1, np.int64); cid[rr_, cc_] = cell
    cond_cell = cid[vt, vc]
    combos = [(row.direction, x) for _, row in grp.iterrows() for x in RBR.ALPHAS]
    real = {(d, x): st.kept(EN.blend(st.q0, [(1.0, zc[d][None, :])], x))[0] for d, x in combos}
    def dense(b):
        A = np.zeros((ci.T, ci.Nc), bool); A[ci.t[b], ci.c[b]] = True
        return A
    Pd, Ld = dense(parent), dense(legal)
    Cd = {k: dense(v) for k, v in real.items()}
    k3 = RND.terciles_rowwise(oldk, Ld)
    acc['setup_s'] = time.perf_counter() - t0
    info = dict(segment=pname, mother=mother, block=block, slot=slot, measurement=mid, combos=len(combos), paths=n, n_cells=int(ci.n))
    for mech in RBR.MECHS:
        tm = time.perf_counter()
        for (d, x) in combos:
            if mech == 'EDIT':
                K = []
                for p in range(n):
                    key = RND.path_key('E6j.B', 'EDIT-ENTRY', mother, 'native', 'EDIT', p)
                    t1 = time.perf_counter(); m, _ = RND.edit_entry(Pd, Cd[(d, x)], Ld, env.grid, key, ind, oldk, 5, k3=k3); tick('EDIT.edit_entry', t1)
                    K.append(m[ci.t, ci.c][None, :])
                K = np.vstack(K)
            else:
                Q = []
                for p in range(n):
                    key = RND.path_key('E6j.B', mid, mother, 'native', mech, p)
                    t1 = time.perf_counter()
                    u = env.grid.u_cells(key, vt, vc, 1 if mech == 'IID' else 5)
                    don = RBR.donor_map(zhi[V], vt.astype(np.int64) if mech == 'IID' else cond_cell, u)
                    tick('%s.draw(u+donor_map)' % mech, t1)
                    t1 = time.perf_counter()
                    zp = np.full(ci.n, np.nan); zp[V] = zc[d][V][don]
                    Q.append(EN.blend(st.q0, [(1.0, zp[None, :])], x)[0]); tick('%s.blend' % mech, t1)
                t1 = time.perf_counter(); K = st.kept(np.vstack([q[None, :] for q in Q])); tick('%s.kept_total' % mech, t1)
            for j in range(n):
                kj = K[j]; t_, c_ = ci.t[kj], ci.c[kj]
                t1 = time.perf_counter(); w = SE.dev(t_, c_); tick('%s.dev' % mech, t1)
                t1 = time.perf_counter(); SE.pnl(t_, c_, w, RBR.HS, 8.0); tick('%s.pnl7H' % mech, t1)
        acc['%s.wall' % mech] = time.perf_counter() - tm
    per = {k: (v / (n * len(combos)) if not k.endswith(('wall', 'setup_s')) else v) for k, v in acc.items()}
    print(json.dumps(dict(info=info, seconds_total=acc, seconds_per_path_combo=per), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
