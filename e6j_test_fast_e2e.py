# -*- coding: utf-8 -*-
"""E6j 提速端到端核对：新代码 --test 重跑的前 n 条路径（randoms/P_test）vs 原代码已落盘的同任务文件（randoms/P）逐位比对 ann / main。
用法：--segment S --form F --arm A（先跑 e6j_run_prand.py ... --paths n --test）。写 checks/fast_e2e_<段>_<形态>_<臂>.csv 与回执。"""
import e6j_boot  # noqa: F401
import os
import sys

import numpy as np
import pandas as pd

import e6j_core as J


def main():
    a = sys.argv
    seg, form, arm = a[a.index('--segment') + 1], a[a.index('--form') + 1], a[a.index('--arm') + 1]
    new = np.load(os.path.join(J.RES, 'randoms', 'P_test', seg, '%s__%s.npz' % (form, arm)), allow_pickle=False)
    old = np.load(os.path.join(J.RES, 'randoms', 'P', seg, '%s__%s.npz' % (form, arm)), allow_pickle=False)
    n = new['ann'].shape[1]
    rows = []
    for k in ('mechs', 'alphas', 'Hs', 'anchors'):
        rows.append(dict(item=k, status='PASS' if np.array_equal(new[k], old[k]) else 'FAIL', detail=''))
    for k in ('ann', 'main'):
        x, y = new[k], old[k][:, :n]
        same_nan = bool(np.array_equal(np.isnan(x), np.isnan(y)))
        mx = float(np.nanmax(np.abs(x - y))) if x.shape == y.shape else np.inf
        rows.append(dict(item=k, status='PASS' if (x.shape == y.shape and same_nan and mx == 0.0) else 'FAIL',
                         detail='前 %d 条路径；shape %s；NaN 位置相同 %s；最大绝对差 %.3g' % (n, x.shape, same_nan, mx)))
    df = pd.DataFrame(rows)
    p = os.path.join(J.RES, 'checks', 'fast_e2e_%s_%s_%s.csv' % (seg, form, arm)); J.atomic_write_csv(p, df)
    ok = bool((df.status == 'PASS').all())
    J.write_receipt('fast_e2e_%s_%s_%s' % (seg, form, arm), [p], 'SUCCEEDED' if ok else 'FAILED', all_pass=ok)
    print(df.to_string())
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
