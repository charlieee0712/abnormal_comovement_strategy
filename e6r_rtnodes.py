# -*- coding: utf-8 -*-
"""E6r 入场票据求解器节点分布（开发期；定节点上限用）：v1（rt_match）20 万上限下真实 TICKETS / JOINT 路径全历史，
按日统计可行日节点数分布与触限日数、单路径耗时。输出 $W/tmp/rtcheck/rtnodes.csv。用法：python3 e6r_rtnodes.py [--refs N] [--paths P] [--workers W]"""
import os
import json
import time
import argparse
import multiprocessing as mp

import numpy as np
import pandas as pd

import e6r_core as O
import e6r_engine as E
import e6r_acct as A

G = {}
EDGES = (0, 1000, 5000, 20000, 50000, 100000, 200000, 10 ** 12)


def init():
    mk = G['mk'] = A.Market()
    G['R'] = O.read_csv(O.P('registration', 'registry_E6r.csv'))
    for f in O.FORMS:
        for m in O.MEMS:
            mk.formation(f, m)
            mk.overlay(f, m)
    mk.formation(O.MAIN_FORM, 'HG10', w15=True)


def job(args):
    lid, mech, path = args
    mk = G['mk']
    row = G['R'][G['R'].logical_id == lid].iloc[0].to_dict()
    ernd = E.ER_TICKETS if mech == 'RANDOM_TILT_TICKETS' else E.ER_JOINT
    ip, fp, trig = A.spec_params(row, seed=O.path_seed(lid, mech, path), ernd=ernd, rtv=0)
    acc = A.Account(mk, ip, fp, trig, mk.formation(row['form'], row['memory'], w15=row['weight_scheme'] == 'UNIFORM_CAP15'), ov=A.overlay_arrays(mk, row))
    t0 = time.time()
    acc.run(0, mk.T)
    st = acc.DY[:, E.DY_ERST].astype(int)
    nd = acc.DY[:, E.DY_ERNODES]
    out = dict(lid=lid, scheme=row['weight_scheme'], mech=mech, path=path, wall_s=round(time.time() - t0, 2), n_draw=int((st > 0).sum()), n_lim=int((st == 3).sum()),
               n_feas=int((st == 1).sum()), n_id=int((st == 4).sum()), nodes_lim=float(nd[st == 3].sum()), nodes_all=float(nd.sum()))
    f = (st == 1) | (st == 4)
    for a, b in zip(EDGES[:-1], EDGES[1:]):
        out['feas_nodes_%d_%d' % (a, b)] = int((f & (nd > a) & (nd <= b)).sum())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--refs', type=int, default=24)
    ap.add_argument('--paths', type=int, default=2)
    ap.add_argument('--workers', type=int, default=64)
    a = ap.parse_args()
    init()
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6r.csv'))
    tk = RR[RR.mechanism == 'RANDOM_TILT_TICKETS'].sort_values('owner_logical_id')
    pick = list(tk.owner_logical_id.iloc[np.linspace(0, len(tk) - 1, min(a.refs, len(tk))).astype(int)])
    jobs = [(l, 'RANDOM_TILT_TICKETS', p) for l in pick for p in range(a.paths)]
    jobs += [(l, 'RANDOM_GATE_TILT_JOINT', p) for l in RR[RR.mechanism == 'RANDOM_GATE_TILT_JOINT'].owner_logical_id for p in range(a.paths)]
    job(jobs[0])
    t0 = time.time()
    with mp.get_context('fork').Pool(min(a.workers, len(jobs))) as pool:
        rows = pool.map(job, jobs, chunksize=1)
    D = pd.DataFrame(rows)
    d = O.P('tmp', 'rtcheck')
    os.makedirs(d, exist_ok=True)
    D.to_csv(os.path.join(d, 'rtnodes.csv'), index=False)
    s = D.drop(columns=['lid', 'scheme', 'mech', 'path']).sum(numeric_only=True).to_dict()
    s.update(paths=len(D), wall_mean=round(float(D.wall_s.mean()), 2), wall_max=float(D.wall_s.max()), total_s=round(time.time() - t0, 1))
    print(json.dumps(s), flush=True)
    print(D.groupby('scheme')[['wall_s', 'n_draw', 'n_lim']].mean().to_string(), flush=True)


if __name__ == '__main__':
    main()
