# -*- coding: utf-8 -*-
"""E6o 分钟尾盘量（plan §4.2 T4a / T4b / T5、§4.3；brief §1.3 C6）。只读 47 公共分钟目录（e6n_minute.root()，E7 截止守卫：读取接口按日期拒绝）。
逐日读 5 分钟 turnoverVol / turnoverValue 两表（行 = bar 终点标签，与 e6n_minute 合同同一校验），算：
  tail_amt / tail_vol = 标签 14:35…15:00 六根 bar（= 14:30–15:00 窗；15:00 bar 含收盘撮合：深市全期、沪市 2018-08-20 起）之和；
  all_amt / all_vol = 09:25 竞价行 + 全部 bar 之和（与 E6n 面板 amt_min / vol_min 同式，作逐格对照）。
另从 E6n 分钟面板（只读）取 p_1457（14:57 及之前最后一笔真实成交价，T4b 的"最后连续成交价"）、p_last、state、amt_min、vol_min。
输出 <cache>/minute/*.npy（全程交易日 × 全部列；无分钟 = NaN）+ minute_facts.json。用法：python3 e6o_minute.py [--workers 48]"""
import os
import sys
import json
import time
import argparse
import resource
from multiprocessing import Pool

import numpy as np
import pandas as pd

import e6o_core as O

TAIL_LABELS = ('14:35:00', '14:40:00', '14:45:00', '14:50:00', '14:55:00', '15:00:00')
PANEL = None


def read_va(date_int):
    import e6n_minute as M
    date_int = int(date_int)
    if date_int > int(O.CUTOFF.replace('-', '')):
        raise RuntimeError('E7 守卫：分钟读取日期 %d 晚于 %s' % (date_int, O.CUTOFF))
    d = os.path.join(M.root(), '5min', '%08d' % date_int)
    out, codes = {}, None
    day = '%04d-%02d-%02d' % (date_int // 10000, date_int // 100 % 100, date_int % 100)
    for f, k in (('turnoverVol', 'v'), ('turnoverValue', 'a')):
        df = pd.read_csv(os.path.join(d, f + '.csv'), index_col=0)
        idx = [str(s) for s in df.index]
        if [s[:10] for s in idx] != [day] * len(idx) or [s[-8:] for s in idx] != list(M.LAB5):
            raise RuntimeError('分钟表行标签与合同不符：%s %s' % (d, f))
        cols = np.array([str(c) for c in df.columns])
        if codes is None:
            codes = cols
        elif not np.array_equal(cols, codes):
            df = df.reindex(columns=codes)
        out[k] = df.to_numpy(dtype=float)
    rows = [list(M.LAB5).index(s) for s in TAIL_LABELS]
    v = np.nan_to_num(out['v'], nan=0.0)
    a = np.nan_to_num(out['a'], nan=0.0)
    return date_int, codes, dict(tail_amt=a[rows].sum(0), tail_vol=v[rows].sum(0), all_amt=a.sum(0), all_vol=v.sum(0))


def main():
    import e6n_minute as M
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=48)
    a = ap.parse_args()
    t0 = time.time()
    pd_dir = os.path.join(O.cache_dir(), 'panels')
    dates = np.load(os.path.join(pd_dir, 'dates.npy'))
    codes = np.load(os.path.join(pd_dir, 'codes.npy'))
    T, N = len(dates), len(codes)
    di = {d.replace('-', ''): i for i, d in enumerate(dates)}
    cj = {str(int(c)).zfill(6) if str(c).isdigit() else str(c): j for j, c in enumerate(codes)}
    ys = sorted(d for d in os.listdir(O.E6N('minute_panel')) if d.startswith('cache_'))
    pdir = O.E6N('minute_panel', ys[0])
    days = sorted(int(x) for x in M.list_days() if int(x) <= int(O.CUTOFF.replace('-', ''))) if hasattr(M, 'list_days') else None
    if not days:
        days = []
        for y in sorted(x for x in os.listdir(pdir) if x.startswith('Y')):
            days += [int(v) for v in np.load(os.path.join(pdir, y, 'dates.npy'))]
    out = {k: np.full((T, N), np.nan) for k in ('tail_amt', 'tail_vol', 'all_amt', 'all_vol', 'p1457', 'p_last', 'amt_min', 'vol_min')}
    state = np.full((T, N), -1, np.int8)
    miss_day, miss_col = 0, set()
    with Pool(a.workers) as pool:
        for date_int, mc, F in pool.imap_unordered(read_va, days, chunksize=4):
            t = di.get(str(date_int))
            if t is None:
                miss_day += 1
                continue
            jj = np.array([cj.get(c, -1) for c in mc])
            ok = jj >= 0
            miss_col.update(mc[~ok].tolist())
            for k, v in F.items():
                out[k][t, jj[ok]] = v[ok]
    # E6n 面板（只读）
    for y in sorted(x for x in os.listdir(pdir) if x.startswith('Y')):
        yd = os.path.join(pdir, y)
        pdates = np.load(os.path.join(yd, 'dates.npy'))
        pcodes = np.load(os.path.join(yd, 'codes.npy'))
        rr = np.array([di.get(str(int(x)), -1) for x in pdates])
        jj = np.array([cj.get(str(c), -1) for c in pcodes])
        okr, okc = rr >= 0, jj >= 0
        for k, src in (('p1457', 'p_1457'), ('p_last', 'p_last'), ('amt_min', 'amt_min'), ('vol_min', 'vol_min')):
            arr = np.load(os.path.join(yd, src + '.npy'), mmap_mode='r')
            out[k][np.ix_(rr[okr], jj[okc])] = np.asarray(arr)[np.ix_(okr, okc)]
        st = np.load(os.path.join(yd, 'state.npy'), mmap_mode='r')
        state[np.ix_(rr[okr], jj[okc])] = np.asarray(st)[np.ix_(okr, okc)]
    od = os.path.join(O.cache_dir(), 'minute')
    os.makedirs(od, exist_ok=True)
    for k, v in out.items():
        np.save(os.path.join(od, k + '.npy'), v)
    np.save(os.path.join(od, 'state.npy'), state)
    both = np.isfinite(out['all_amt']) & np.isfinite(out['amt_min'])
    facts = dict(days=len(days), first=int(min(days)), last=int(max(days)), miss_day=miss_day, miss_cols=len(miss_col),
                 all_amt_vs_panel_maxabs=float(np.nanmax(np.abs(out['all_amt'][both] - out['amt_min'][both]))) if both.any() else None,
                 all_vol_vs_panel_maxabs=float(np.nanmax(np.abs(out['all_vol'][both] - out['vol_min'][both]))) if both.any() else None,
                 cells_tail=int(np.isfinite(out['tail_amt']).sum()), wall_s=round(time.time() - t0, 1),
                 rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2), tail_labels=list(TAIL_LABELS))
    O.atomic_write_json(os.path.join(od, 'minute_facts.json'), facts)
    O.write_receipt('E6o_minute', [os.path.join(od, 'minute_facts.json')], code=[__file__, O.__file__], **{k: v for k, v in facts.items() if not isinstance(v, list)})
    print(json.dumps(facts, ensure_ascii=False, default=str), flush=True)


if __name__ == '__main__':
    main()
