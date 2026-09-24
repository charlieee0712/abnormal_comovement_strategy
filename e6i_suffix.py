#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 前缀不变 (suffix) 测试 —— plan §3.4 / §11.3: 同时扰动未来价 / 量 / 换手 / 行业 / 限价 /
开市标志 / 触发, 重算全部 RESEARCH 成员, 截止日及以前的值必须逐位不变 (atol 1e-12)。

每个切点 t*: 预热网格上 t* 之后的所有行随机扰动 (价格同乘 U(0.5,2) 保持 OHLC 相容;
量/额/换手 x U(0,3); 行业码在 t* 后随机置换; 限价 x U(0.9,1.1); is_open 5% 翻转;
触发 5% 随机重置), 其余 (S.feats / pool0 / clean / log_mcap, 皆为段内旧对象) 不动。
LEGACY 成员取源值, 不在本测试内 (其前缀性属源)。

任何成员在 <= t* 的格上变了 -> 未来函数 -> MODULE STOP (退出码 2)。

用法: python3 e6i_suffix.py --segment 2015-2018 --axes T,K --cuts 4
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import copy
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE

PRICE = ('open', 'high', 'low', 'close', 'lclose', 'vwap')
QTY = ('volume', 'amount', 'turnover_rate')


def perturb(S, tcut, rng):
    S2 = copy.copy(S)
    d2 = {}
    fac = None
    for k, df in S.wdata_i.items():
        if not isinstance(df, pd.DataFrame):
            d2[k] = df
            continue
        df = df.copy()
        after = df.index > tcut
        if not after.any():
            d2[k] = df
            continue
        if k in PRICE:
            if fac is None or fac.shape != (int(after.sum()), df.shape[1]):
                fac = rng.uniform(0.5, 2.0, size=(int(after.sum()), df.shape[1]))
            df.loc[after] = df.loc[after].values * fac
        elif k in QTY:
            df.loc[after] = df.loc[after].values * rng.uniform(0, 3, size=(int(after.sum()),
                                                                         df.shape[1]))
        elif k in ('limit_up', 'limit_down'):
            df.loc[after] = df.loc[after].values * rng.uniform(0.9, 1.1, size=(int(after.sum()),
                                                                             df.shape[1]))
        elif k in ('industry', 'industry_zx1'):
            v = df.loc[after].values.copy()
            flat = v.ravel()
            flat[:] = rng.permutation(flat)
            df.loc[after] = flat.reshape(v.shape)
        elif k == 'is_open':
            v = df.loc[after].values.astype(float)
            flip = rng.random(v.shape) < 0.05
            v[flip] = 1.0 - v[flip]
            df.loc[after] = v
        d2[k] = df
    S2.wdata_i = d2
    S2._i = {}
    return S2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--axes', default='T,K,V,R,O,C,A,S')
    ap.add_argument('--cuts', type=int, default=4)
    ap.add_argument('--seed', type=int, default=20260923)
    a = ap.parse_args()
    assert a.segment in I.DERIV_SEGS
    t0 = time.time()
    FE.build_catalog()
    I.set_protected_members(FE.protected_ids())
    axes = set(a.axes.split(','))
    mems = [m for m in FE.CATALOG if m['axis_id'] in axes and m['source_class'] != 'LEGACY']
    I.guard_i([m['member_id'] for m in mems], segment=a.segment, use='compute', where='suffix')
    S = I.seg_i(a.segment, verbose=False)
    B0 = FE.Base(S)
    base_vals = {}
    for m in mems:
        base_vals[m['member_id']] = np.asarray(m['fn'](B0), np.float64)
    dates = B0.dates_w
    seg_pos = B0.seg_rows
    cut_rows = np.linspace(seg_pos[0] + 60, seg_pos[-1] - 20, a.cuts).astype(int)
    rng = np.random.default_rng(a.seed)
    rows, bad = [], 0
    for ci, r in enumerate(cut_rows):
        tcut = dates[r]
        S2 = perturb(S, tcut, rng)
        B2 = FE.Base(S2)
        after = np.arange(len(dates)) > r
        flip = (rng.random(B2.trig.shape) < 0.05) & after[:, None]
        B2.trig = np.where(after[:, None], flip, B2.trig)
        B2._tau = None
        for m in mems:
            try:
                v2 = np.asarray(m['fn'](B2), np.float64)
            except Exception as e:
                rows.append(dict(cut=str(tcut.date()), member_id=m['member_id'], ok=False,
                                 error='%s: %s' % (type(e).__name__, str(e)[:120])))
                bad += 1
                continue
            v1 = base_vals[m['member_id']]
            pre1, pre2 = v1[:r + 1], v2[:r + 1]
            nan_same = bool(np.array_equal(np.isnan(pre1), np.isnan(pre2)))
            both = np.isfinite(pre1) & np.isfinite(pre2)
            mx = float(np.max(np.abs(pre1[both] - pre2[both]))) if both.any() else 0.0
            # 未来部分应当确实被扰动过 (否则测试没有力度): 至少一格变化
            post_changed = bool((~np.isclose(np.nan_to_num(v1[r + 1:], nan=1e300),
                                             np.nan_to_num(v2[r + 1:], nan=1e300))).any())
            ok = nan_same and mx <= 1e-12
            bad += (not ok)
            rows.append(dict(cut=str(tcut.date()), member_id=m['member_id'], axis=m['axis_id'],
                             ok=ok, max_abs_prefix=mx, nan_pattern_same=nan_same,
                             suffix_actually_changed=post_changed))
        print('  切点 %d/%d %s: 累计失败 %d (%.0fs)' % (ci + 1, len(cut_rows), tcut.date(), bad,
                                                  time.time() - t0), flush=True)
    d = pd.DataFrame(rows)
    tag = a.axes.replace(',', '')
    p = os.path.join(I.RES, 'checks', 'suffix_guard_%s_%s.csv' % (a.segment, tag))
    I.atomic_write_csv(p, d)
    n_weak = int((~d.suffix_actually_changed.fillna(True)).sum()) if 'suffix_actually_changed' in d else 0
    print('[%s %s] 成员 %d x 切点 %d = %d 检查; 失败 %d; 后缀未被扰动到的检查 %d; %.0fs'
          % (a.segment, a.axes, len(mems), len(cut_rows), len(d), bad, n_weak, time.time() - t0))
    if bad:
        print(d[~d.ok].head(20).to_string(index=False))
    sys.exit(2 if bad else 0)


if __name__ == '__main__':
    main()
