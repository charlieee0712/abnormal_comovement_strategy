# -*- coding: utf-8 -*-
"""E6o 推导段重放核对（B 之后；附录 B.5 封存的旁证）：
  ① 随机 / 水平控制：B 阶段从 0 日重跑的每条路径，其推导段（2010-2014 / 2015-2018）D 与有效日数 = A2 同 (owner, 机制, path_id) 的值（逐位）；
  ② 账户：B 文件的推导段日序列 = A2 文件（B 由 A2_end checkpoint 续跑，应逐位相同）；
  ③ 影子风险集：B 影子在推导段的命中 = A2 影子。
输出 verify/replay_A2_vs_B_E6o.csv；任何不等 → 退出码 1。"""
import os
import sys
import glob
import json

import numpy as np
import pandas as pd

import e6o_core as O
import e6o_engine as E


def main():
    rows = []
    # ① 随机
    a2 = pd.concat([pd.read_csv(f, keep_default_na=False, na_values=['']) for f in sorted(glob.glob(O.P('randoms', 'random_paths_A2*.csv')))], ignore_index=True)
    b = pd.concat([pd.read_csv(f, keep_default_na=False, na_values=['']) for f in sorted(glob.glob(O.P('randoms', 'random_paths_B*.csv')))], ignore_index=True)
    k = ['owner_exec_id', 'mechanism', 'path_id']
    m = a2.merge(b, on=k, suffixes=('_a', '_b'), how='left')
    miss = int(m['seed_b'].isna().sum())
    for c in ('D_2010-2014', 'D_2015-2018', 'n_2010-2014', 'n_2015-2018'):
        x, y = m[c + '_a'].to_numpy(float), m[c + '_b'].to_numpy(float)
        both_nan = np.isnan(x) & np.isnan(y)
        diff = np.where(both_nan, 0.0, np.abs(x - y))
        nbad = int((~np.isfinite(diff) | (diff > 0)).sum())
        rows.append(dict(check='RANDOM_DERIV_REPLAY', column=c, n=len(m), n_missing_in_B=miss, n_diff=nbad, max_abs_diff=float(np.nanmax(diff)) if len(diff) else 0.0,
                         status='PASS' if (nbad == 0 and miss == 0) else 'DIFFERS'))
    # ② 账户
    R = pd.read_csv(O.P('registration', 'registry_E6o.csv'), keep_default_na=False, na_values=[''])
    dates = np.load(os.path.join(O.cache_dir(), 'panels', 'dates.npy'))
    d19 = int(np.searchsorted(dates, '2019-01-01'))
    nb = 0
    mx = 0.0
    n = 0
    for r in R[R.series != 'P_SOURCE'].itertuples():
        za = np.load(O.P('accounts_run', 'deriv', r.exec_hash[:2], '%s.npz' % r.exec_hash), allow_pickle=False)['DY'][:d19]
        zb = np.load(O.P('accounts_run', 'full', r.exec_hash[:2], '%s.npz' % r.exec_hash), allow_pickle=False)['DY'][:d19]
        d = np.where(np.isnan(za) & np.isnan(zb), 0.0, np.abs(za - zb))
        n += 1
        if not np.all(d == 0):
            nb += 1
            mx = max(mx, float(np.nanmax(d)))
    rows.append(dict(check='ACCOUNT_DERIV_ROWS_EQUAL', column='DY[:d19] 全列', n=n, n_missing_in_B=0, n_diff=nb, max_abs_diff=mx, status='PASS' if nb == 0 else 'DIFFERS'))
    # ③ 影子
    nb = 0
    n = 0
    for p in sorted(glob.glob(O.P('accounts_run', 'shadow_deriv', '*.npz'))):
        za = np.load(p, allow_pickle=False)
        zb = np.load(O.P('accounts_run', 'shadow_full', os.path.basename(p)), allow_pickle=False)
        ia, ib = za['IN_i'], zb['IN_i']
        fixed = [E.IN_DAY, E.IN_SEC, E.IN_LAYER, E.IN_ISK, E.IN_RE, E.IN_LOT]   # 建档时即定的列（IN_EXEC / IN_STATUS 可在 d19 后更新，只比是否影子命中）
        sa = np.c_[ia[ia[:, E.IN_DAY] < d19][:, fixed], ia[ia[:, E.IN_DAY] < d19][:, E.IN_STATUS] == 9]
        sb = np.c_[ib[ib[:, E.IN_DAY] < d19][:, fixed], ib[ib[:, E.IN_DAY] < d19][:, E.IN_STATUS] == 9]
        ra, rb = za['RISK'][:d19], zb['RISK'][:d19]
        n += 1
        if not (sa.shape == sb.shape and np.array_equal(sa, sb) and np.array_equal(ra, rb)):
            nb += 1
    rows.append(dict(check='SHADOW_DERIV_EQUAL', column='IN_i（推导段日）+ RISK[:d19]', n=n, n_missing_in_B=0, n_diff=nb, max_abs_diff=float(nb), status='PASS' if nb == 0 else 'DIFFERS'))
    D = pd.DataFrame(rows)
    O.atomic_write_csv(O.P('verify', 'replay_A2_vs_B_E6o.csv'), D)
    print(D.to_string(), flush=True)
    sys.exit(0 if (D.status == 'PASS').all() else 1)


if __name__ == '__main__':
    main()
