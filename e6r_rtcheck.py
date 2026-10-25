# -*- coding: utf-8 -*-
"""E6r 入场票据求解器 v2 核验（开发期；结果进 notes §8 与代码变更登记）：真实 TICKETS / JOINT 随机路径全历史，
rtv = 2（v1 回溯与 v2 字典序贪心逐实例同跑：v1 可行时 v2 须逐位同解）；另计时 rtv = 1 / 0。输出 $W/tmp/rtcheck/rtcheck.csv。
用法：python3 e6r_rtcheck.py [--refs N] [--paths P] [--workers W]"""
import os
import sys
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
KEYS = ('RTCMP', 'RTMIS', 'RTV1LIM', 'RTV1OK', 'RTV2LIM', 'RTEXACT', 'RTBFD', 'RTSWAP', 'RTN1', 'RTN2', 'ERFEAS', 'ERNOM', 'ERLIM', 'ERID')


def init():
    mk = G['mk'] = A.Market()
    G['R'] = O.read_csv(O.P('registration', 'registry_E6r.csv'))
    for f in O.FORMS:                                   # 父进程先全部载入（fork 后不再懒读共享的 npz 句柄）
        for m in O.MEMS:
            mk.formation(f, m)
            mk.overlay(f, m)
    mk.formation(O.MAIN_FORM, 'HG10', w15=True)


def job(args):
    lid, mech, path, rtv = args
    mk = G['mk']
    R = G['R']
    row = R[R.logical_id == lid].iloc[0].to_dict()
    ernd = E.ER_TICKETS if mech == 'RANDOM_TILT_TICKETS' else E.ER_JOINT
    seed = O.path_seed(lid, mech, path)
    ip, fp, trig = A.spec_params(row, seed=seed, ernd=ernd, rtv=rtv)
    f = mk.formation(row['form'], row['memory'], w15=row['weight_scheme'] == 'UNIFORM_CAP15')
    acc = A.Account(mk, ip, fp, trig, f, ov=A.overlay_arrays(mk, row))
    t0 = time.time()
    acc.run(0, mk.T)
    out = dict(lid=lid, scheme=row['weight_scheme'], trigger=row['trigger'], H=row['funding_H'], exit_op=row['exit_op'], mech=mech, path=path, rtv=rtv,
               wall_s=round(time.time() - t0, 2), nav_end=float(acc.DY[mk.T - 1, E.DYI['nav_post']]), nodes_day_max=float(acc.DY[:, E.DY_ERNODES].max()))
    for k in KEYS:
        out[k] = int(acc.S_i[getattr(E, 'SI_' + k)])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--refs', type=int, default=24)
    ap.add_argument('--paths', type=int, default=2)
    ap.add_argument('--workers', type=int, default=64)
    a = ap.parse_args()
    init()
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6r.csv'))
    tk = RR[RR.mechanism == 'RANDOM_TILT_TICKETS']
    jt = RR[RR.mechanism == 'RANDOM_GATE_TILT_JOINT']
    # 分散抽 owner：按 owner 逻辑 id 排序后等距取
    pick = list(tk.sort_values('owner_logical_id').owner_logical_id.iloc[np.linspace(0, len(tk) - 1, min(a.refs, len(tk))).astype(int)])
    jobs = [(l, 'RANDOM_TILT_TICKETS', p, 2) for l in pick for p in range(a.paths)]
    jobs += [(l, 'RANDOM_GATE_TILT_JOINT', p, 2) for l in jt.owner_logical_id for p in range(a.paths)]
    jobs += [(l, 'RANDOM_TILT_TICKETS', 0, v) for l in pick[:4] for v in (1, 0)]
    # 预编译
    job((pick[0], 'RANDOM_TILT_TICKETS', 0, 1))
    t0 = time.time()
    ctx = mp.get_context('fork')
    with ctx.Pool(min(a.workers, len(jobs))) as pool:
        rows = pool.map(job, jobs, chunksize=1)
    D = pd.DataFrame(rows)
    d = O.P('tmp', 'rtcheck')
    os.makedirs(d, exist_ok=True)
    D.to_csv(os.path.join(d, 'rtcheck.csv'), index=False)
    v = D[D.rtv == 2]
    summ = dict(paths=len(v), instances=int(v.RTCMP.sum()), mismatches=int(v.RTMIS.sum()), v1_limit=int(v.RTV1LIM.sum()), v1_limit_v2_solved=int(v.RTV1OK.sum()),
                v2_limit=int(v.RTV2LIM.sum()), exact_calls=int(v.RTEXACT.sum()), bfd_certs=int(v.RTBFD.sum()), swap_certs=int(v.RTSWAP.sum()),
                nodes_v1=int(v.RTN1.sum()), nodes_v2=int(v.RTN2.sum()), wall_s=round(time.time() - t0, 1))
    for vv in (1, 0):
        x = D[D.rtv == vv]
        summ['wall_rtv%d_mean' % vv] = round(float(x.wall_s.mean()), 2)
    print(json.dumps(summ), flush=True)
    print(D[D.rtv != 2][['lid', 'scheme', 'rtv', 'wall_s', 'ERLIM', 'RTV2LIM', 'nav_end']].to_string(), flush=True)


if __name__ == '__main__':
    main()
