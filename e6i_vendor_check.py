#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e6i_vendor 自检: 用同 commit 的本地测试数据复现作者 tests/test_edge.py 的已知值,
并核 edge_rolling 与逐窗 edge() 的一致性 (无缺失数据时应一致)。结果写 checks/vendor_check.json。"""
from __future__ import annotations
import e6i_boot  # noqa: F401  (必须最先: 关掉 pyarrow S3 的 192 个 AwsEventLoop 线程)
import os
import sys
import json

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
from e6i_vendor.bidask import edge, edge_rolling
import e6i_core as I

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'e6i_vendor', 'bidask_testdata')


def main():
    df = pd.read_csv(os.path.join(D, 'ohlc.csv'))
    dm = pd.read_csv(os.path.join(D, 'ohlc-miss.csv'))
    res = []

    def chk(name, got, want, tol=1e-12):
        ok = (np.isnan(want) and np.isnan(got)) or abs(got - want) <= tol * max(1.0, abs(want))
        res.append(dict(test=name, got=float(got), want=float(want), ok=bool(ok)))

    chk('edge_full', edge(df.Open, df.High, df.Low, df.Close), 0.0101849034905478)
    chk('edge_first10_signed', edge(df.Open[0:10], df.High[0:10], df.Low[0:10], df.Close[0:10],
                                    True), -0.016889917516422)
    chk('edge_missing', edge(dm.Open, dm.High, dm.Low, dm.Close), 0.01013284969780197)
    chk('edge_flat_nan', edge([18.21, 17.61, 17.61], [18.21, 17.61, 17.61],
                              [17.61, 17.61, 17.61], [17.61, 17.61, 17.61]), float('nan'))
    # rolling vs 逐窗 (作者 test_edge_rolling 的逻辑, 无缺失数据)
    worst = 0.0
    for w in (3, 4, 20, 42):
        for sign in (True, False):
            r = edge_rolling(df.rename(columns=str.lower), window=w, sign=sign)
            for t in range(w - 1, len(df)):
                sl = slice(t - w + 1, t + 1)
                e = edge(df.Open.values[sl], df.High.values[sl], df.Low.values[sl],
                         df.Close.values[sl], sign)
                a = r.iloc[t]
                if np.isnan(e) and np.isnan(a):
                    continue
                worst = max(worst, abs(a - e))
    res.append(dict(test='rolling_vs_windowed_max_abs', got=worst, want=0.0,
                    ok=bool(worst < 1e-9)))
    out = dict(n=len(res), n_pass=sum(r['ok'] for r in res), results=res)
    I.atomic_write_json(os.path.join(I.RES, 'checks', 'vendor_check.json'), out)
    for r in res:
        print('%-30s got=%.15g want=%.15g %s' % (r['test'], r['got'], r['want'],
                                                  'OK' if r['ok'] else '!!'))
    print('vendor check %d/%d' % (out['n_pass'], out['n']))
    sys.exit(0 if out['n_pass'] == out['n'] else 1)


if __name__ == '__main__':
    main()
