# -*- coding: utf-8 -*-
"""E6p 重放核验（brief §4 断点恢复；附录 B.11 JOURNAL_REPLAY）：
  journal   主对象两只 × 两情景与其同 H 父 / H5 NATIVE 父：新建账户从 0 日一次跑完 vs 正式链（A2 checkpoint → B 续跑）的全部 DY 逐位比较 → verify/journal_replay_E6p.csv
  randoms   随机路径：B（从 0 日整段重放）的推导两段 D 与 A2 逐路径逐位比较（owner × 机制汇总）→ verify/random_replay_E6p.csv
用法：python3 e6p_replay.py journal|randoms"""
import os
import sys
import json

import numpy as np
import pandas as pd

import e6p_core as O
import e6p_run as RN


def journal():
    RN.setup()
    R = RN.G['R'] = RN.registry()
    A = R[R.role == 'ACCOUNT']
    main = A[A.is_main_object == '1']
    keep = list(dict.fromkeys(list(main.exec_id) + list(main.parent_same_h_exec_id) + list(main.parent_h5_native_exec_id)))
    rows = []
    T = RN.G['mk'].T
    for e in keep:
        row = R[R.exec_id == e].iloc[0].to_dict()
        acc = RN.build(row, 'B', tlog=False)
        acc.run(0, T)
        z = np.load(RN.res_path('B', row['exec_hash']), allow_pickle=False)
        ref = z['DY']
        a, b = acc.DY[:T], ref[:T]
        fa, fb = np.isfinite(a), np.isfinite(b)
        same_nan = bool(np.array_equal(fa, fb))
        mx = float(np.max(np.abs(a[fa & fb] - b[fa & fb]))) if (fa & fb).any() else 0.0
        rows.append(dict(exec_id=e, n_days=T, nan_pattern_same=same_nan, max_abs_diff=mx if same_nan else float('inf'), intents_same=int(acc.S_i[RN.E.SI_NIN]) == len(z['IN_i']),
                         status='PASS' if (same_nan and mx == 0.0) else 'DIFFERS'))
    D = pd.DataFrame(rows)
    O.atomic_write_csv(O.P('verify', 'journal_replay_E6p.csv'), D)
    print(json.dumps(dict(n=len(D), bad=int((D.status != 'PASS').sum()), max_abs=float(D.max_abs_diff.max())), ensure_ascii=False), flush=True)


def randoms():
    a2 = pd.read_csv(O.P('randoms', 'random_paths_A2.csv'), keep_default_na=False, na_values=[''])
    b = pd.read_csv(O.P('randoms', 'random_paths_B.csv'), keep_default_na=False, na_values=[''])
    k = ['owner_exec_id', 'mechanism', 'path_id']
    m = a2.merge(b, on=k, suffixes=('_a2', '_b'))
    out = []
    for (o, mech), g in m.groupby(['owner_exec_id', 'mechanism']):
        d = 0.0
        for s in O.DERIV_SEGS:
            x, y = g['D_%s_a2' % s].to_numpy(float), g['D_%s_b' % s].to_numpy(float)
            fx, fy = np.isfinite(x), np.isfinite(y)
            if not np.array_equal(fx, fy):
                d = float('inf')
                break
            if fx.any():
                d = max(d, float(np.max(np.abs(x[fx] - y[fy]))))
        out.append(dict(owner_exec_id=o, mechanism=mech, n_paths=len(g), seeds_same=bool((g.seed_a2 == g.seed_b).all()), max_abs_diff=d,
                        status='PASS' if (d == 0.0 and (g.seed_a2 == g.seed_b).all()) else 'DIFFERS'))
    D = pd.DataFrame(out)
    D.loc[len(D)] = dict(owner_exec_id='ALL', mechanism='ALL', n_paths=int(D.n_paths.sum()), seeds_same=bool(D.seeds_same.all()), max_abs_diff=float(D.max_abs_diff.max()),
                         status='PASS' if (D.status == 'PASS').all() else 'DIFFERS')
    missing = len(a2) - len(m)
    O.atomic_write_csv(O.P('verify', 'random_replay_E6p.csv'), D)
    print(json.dumps(dict(groups=len(D) - 1, paths=len(m), unmatched_a2_rows=missing, bad=int((D.status != 'PASS').sum())), ensure_ascii=False), flush=True)


def hand():
    """手工逐日账（brief §8.1 verify/）：主对象两只（FEASIBLE）各抽 5 个交易日，只用成交日志 + 面板逐笔重算：
    当日买 / 卖名义、费用 = 4bp × Σ_证券 |净成交名义|、现金变动 = 卖 − 买 − 费、交易前 NAV = 昨收现金 + Σ 批次股数 × 当日 VWAP（后复权）；与引擎日序列比。"""
    import e6p_stats as ST
    import e6p_engine as E
    ctx = ST.Ctx('B', False, O.work())
    R = ctx.R
    pv = np.load(os.path.join(O.cache_dir(), 'panels', 'pv_ff.npy'), mmap_mode='r')
    rows = []
    for e in R[(R.is_main_object == '1') & (R.execution_profile == 'FEASIBLE_DAILY')].exec_id:
        h = ctx.reg.loc[e, 'exec_hash']
        ti, tf = ST.load_trades(ctx, h)
        DY = np.load(RN.res_path('B', h), allow_pickle=False)['DY']
        rng = np.random.default_rng(O.stable_u64('E6p', 'HAND', e) % (2 ** 32))
        days = sorted(rng.choice(np.arange(100, ctx.T - 1), 5, replace=False).tolist())
        sg = np.where(ti[:, 5] == 0, 1.0, -1.0)
        for d in days:
            m = ti[:, 0] == d
            buy = float(tf[m & (ti[:, 5] == 0), 1].sum())
            sell = float(tf[m & (ti[:, 5] == 1), 1].sum())
            net = pd.Series(sg[m] * tf[m, 1]).groupby(ti[m, 1]).sum().abs().sum() if m.any() else 0.0
            fee = O.FEE_RATE * float(net)
            prior = ti[:, 0] < d
            q = pd.Series(sg[prior] * tf[prior, 0]).groupby(ti[prior, 1]).sum()
            q = q[q.abs() > 1e-9]
            hold = float((q.to_numpy() * np.asarray(pv[d, q.index.to_numpy()])).sum())
            cash_prev = DY[d - 1, E.DYI['cash_share']] * DY[d - 1, E.DYI['nav_post']]
            nav_pre = cash_prev + hold
            rows.append(dict(exec_id=e, date=str(ctx.dates[d]), buy_hand=buy, buy_engine=DY[d, E.DYI['buy_val']], sell_hand=sell, sell_engine=DY[d, E.DYI['sell_val']],
                             fee_hand=fee, fee_engine=DY[d, E.DYI['fee']], nav_pre_hand=nav_pre, nav_pre_engine=DY[d, E.DYI['nav_pre']],
                             cash_change_hand=sell - buy - fee, cash_change_engine=DY[d, E.DYI['cash_share']] * DY[d, E.DYI['nav_post']] - cash_prev))
    D = pd.DataFrame(rows)
    rel = lambda a, b: (D[a] - D[b]).abs() / np.maximum(1.0, D[b].abs())
    D['max_rel_diff'] = np.maximum.reduce([rel('buy_hand', 'buy_engine'), rel('sell_hand', 'sell_engine'), rel('fee_hand', 'fee_engine'), rel('nav_pre_hand', 'nav_pre_engine'),
                                           (D.cash_change_hand - D.cash_change_engine).abs() / 1e8])
    D['status'] = np.where(D.max_rel_diff <= 1e-9, 'PASS', 'DIFFERS')
    O.atomic_write_csv(O.P('verify', 'hand_ledger_E6p.csv'), D)
    print(json.dumps(dict(n=len(D), bad=int((D.status != 'PASS').sum()), max_rel=float(D.max_rel_diff.max())), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    {'journal': journal, 'randoms': randoms, 'hand': hand}[sys.argv[1]]()
