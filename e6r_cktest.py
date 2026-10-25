# -*- coding: utf-8 -*-
"""E6r 随机路径 A2 末 checkpoint 续跑等价核验（开发期；结果进 notes §8）：若干真实随机引用的路径，(1) 0 → T 一次跑完；(2) 0 → d19、压缩 checkpoint（不存 DY）、
新账户恢复、d19 → T 续跑；逐位比对 DY[d19:T] 与 S_i，记 checkpoint 字节数与耗时。不写任何结果目录（输出 $W/tmp/cktest/）。不读收益做任何选择。"""
import os
import json
import time
import multiprocessing as mp

import numpy as np
import pandas as pd

import e6r_core as O
import e6r_engine as E
import e6r_acct as A
import e6r_run as RN

MECHS = ('RANDOM_TILT_TICKETS', 'RANDOM_TILT_LABEL_PROJECT', 'RANDOM_GATE_COUNT', 'RANDOM_GATE_AMOUNT', 'RANDOM_GATE_TILT_JOINT', 'RANDOM_TENOR_LABEL')


def job(args):
    lid, mech, path = args
    mk = RN.G['mk']
    row = RN.G['R'][RN.G['R'].logical_id == lid].iloc[0].to_dict()
    ernd = RN.ENTRY_MECH[mech]
    seed = O.path_seed(lid, mech, path)
    dA, T = RN.d19(), mk.T
    t0 = time.time()
    a = RN.build(row, seed=seed, ernd=ernd)
    a.run(0, T)
    t1 = time.time()
    b = RN.build(row, seed=seed, ernd=ernd)
    b.run(0, dA)
    d = O.P('tmp', 'cktest', 'ck')
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, '%s_%s_%d.npz' % (row['exec_hash'], mech, path))
    b.checkpoint_compact(p, dict(test=1))
    c = RN.build(row, seed=seed, ernd=ernd)
    c.restore(p)
    c.run(dA, T)
    t2 = time.time()
    neq = int((np.abs(np.nan_to_num(a.DY[dA:T]) - np.nan_to_num(c.DY[dA:T])) > 0).any(axis=0).sum())
    eq = bool(np.array_equal(a.DY[dA:T], c.DY[dA:T], equal_nan=True) and np.array_equal(np.delete(a.S_i, E.SI_NL), np.delete(c.S_i, E.SI_NL)) and np.array_equal(a.HOLDH, c.HOLDH))
    return dict(lid=lid, mech=mech, path=path, scheme=row['weight_scheme'], equal=eq, n_cols_diff=neq, ck_bytes=os.path.getsize(p), t_full=round(t1 - t0, 2), t_split=round(t2 - t1, 2))


def main():
    RN.setup()
    R = RN.G['R'] = RN.registry()
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6r.csv'))
    jobs = []
    for m in MECHS:
        x = RR[RR.mechanism == m].sort_values('owner_logical_id')
        for lid in x.owner_logical_id.iloc[np.linspace(0, len(x) - 1, min(4, len(x))).astype(int)]:
            jobs += [(lid, m, 0), (lid, m, 7)]
    with mp.get_context('fork').Pool(min(64, len(jobs))) as pool:
        rows = pool.map(job, jobs, chunksize=1)
    D = pd.DataFrame(rows)
    os.makedirs(O.P('tmp', 'cktest'), exist_ok=True)
    D.to_csv(O.P('tmp', 'cktest', 'cktest.csv'), index=False)
    print(json.dumps(dict(n=len(D), all_equal=bool(D.equal.all()), ck_mb_mean=round(D.ck_bytes.mean() / 1e6, 3), ck_mb_max=round(D.ck_bytes.max() / 1e6, 3),
                          t_full_mean=round(D.t_full.mean(), 2), t_split_mean=round(D.t_split.mean(), 2))), flush=True)
    print(D.groupby('mech')[['equal', 'ck_bytes', 't_full']].mean().to_string(), flush=True)


if __name__ == '__main__':
    main()
