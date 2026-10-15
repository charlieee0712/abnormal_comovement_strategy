# -*- coding: utf-8 -*-
"""E6n 分钟全期 ETL（plan §12.3：一次拉取允许日期、按日 / 证券分区缓存原始面板与基础量，不逐形成日重读）。不读日频、不读收益。
  days  --workers K：逐日 e6n_minute.day_features → <面板>/days/<YYYYMMDD>.npz（原子写；已存在且可读则跳过 = 断点续跑）；
        同时对当日 12 个源文件逐个算 sha256，写 <面板>/days/<YYYYMMDD>.src.json（分区 manifest 的原料）。
  merge：按年合并 → <面板>/Y<年>/<字段>.npy + dates.npy + codes.npy；全期 partition_manifest.csv（日期、文件、字节、sha256）与其 sha。
  all   ：days → merge。
面板目录 = minute_panel/<缓存命名空间>（e6n_core.cache_namespace：contract_version + plan sha + 源根 + 读取器 sha + 数值环境）。
用法：E6N_WORK=<结果目录> python3 e6n_etl.py all --workers 24"""
import os
import sys
import json
import time
import hashlib
import argparse
import multiprocessing as mp

import numpy as np

import e6n_core as N
import e6n_minute as MN


def panel_dir():
    reader_sha = N.sha_file(os.path.join(os.path.dirname(os.path.abspath(MN.__file__)), 'e6n_minute.py'))[:16]
    ns, det = N.cache_namespace(source_version='MatrixDailyFix', data_version='days<=%d' % N.MARKET_DATA_END_INT,
                                adapter_version='e6n_minute@%s' % reader_sha, support='ALL_PRESENT_CODES', init='NOT_APPLICABLE')
    d = N.P('minute_panel', ns)
    os.makedirs(os.path.join(d, 'days'), exist_ok=True)
    p = os.path.join(d, 'namespace.json')
    if not os.path.exists(p):
        N.atomic_write_json(p, dict(namespace=ns, **det))
    return d


def _sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def one_day(args):
    d, out = args
    f = os.path.join(out, 'days', '%08d.npz' % d)
    s = os.path.join(out, 'days', '%08d.src.json' % d)
    if os.path.exists(f) and os.path.exists(s):
        try:
            with np.load(f, allow_pickle=False) as z:
                z['codes']
            return d, 'SKIP', 0.0
        except Exception:                                         # noqa: BLE001  读不回则重做
            pass
    t = time.time()
    try:
        codes, F = MN.day_features(d)
        N.atomic_write_npz(f, codes=codes.astype('U6'), **F)
        src = []
        for fr in (5, 1):
            for fld in MN.FIELDS:
                p = os.path.join(MN.root(), '%dmin' % fr, '%08d' % d, fld + '.csv')
                src.append(dict(date=d, file='%dmin/%08d/%s.csv' % (fr, d, fld), bytes=os.path.getsize(p), sha256=_sha(p)))
        N.atomic_write_json(s, src)
        return d, 'OK', time.time() - t
    except Exception as e:                                        # noqa: BLE001
        return d, 'FAIL %s: %s' % (type(e).__name__, str(e)[:200]), time.time() - t


def run_days(workers):
    out = panel_dir()
    days = MN.list_days(5)
    d1 = set(MN.list_days(1))
    if set(days) != d1:
        raise RuntimeError('1 / 5 分钟日期集合不同：%s' % sorted(set(days) ^ d1)[:10])
    N.log('ETL days：%d 天（%d–%d），workers=%d，面板 %s' % (len(days), days[0], days[-1], workers, N.rel(out)))
    t0 = time.time()
    fails = []
    done = 0
    with mp.get_context('fork').Pool(workers) as pool:
        for d, st, sec in pool.imap_unordered(one_day, [(x, out) for x in days], chunksize=1):
            done += 1
            if not st.startswith(('OK', 'SKIP')):
                fails.append((d, st))
            if done % 100 == 0 or done == len(days):
                N.log('  %d / %d（%.0f s）失败 %d' % (done, len(days), time.time() - t0, len(fails)))
    if fails:
        N.atomic_write_json(os.path.join(out, 'days_failed.json'), fails)
        raise RuntimeError('ETL 有 %d 天失败，见 days_failed.json' % len(fails))
    return out, days


def merge(out=None):
    out = out or panel_dir()
    days = MN.list_days(5)
    years = sorted(set(d // 10000 for d in days))
    man = []
    yrs = {}
    for y in years:
        ds = [d for d in days if d // 10000 == y]
        Z = []
        for d in ds:
            with np.load(os.path.join(out, 'days', '%08d.npz' % d), allow_pickle=False) as z:
                Z.append({k: z[k] for k in z.files})
            with open(os.path.join(out, 'days', '%08d.src.json' % d), encoding='utf-8') as fh:
                man += json.load(fh)
        codes = np.array(sorted(set().union(*[set(z['codes'].tolist()) for z in Z])), dtype='U6')
        pos = {c: i for i, c in enumerate(codes)}
        fields = [k for k in Z[0] if k != 'codes']
        yd = os.path.join(out, 'Y%d' % y)
        os.makedirs(yd, exist_ok=True)
        np.save(os.path.join(yd, 'dates.npy'), np.array(ds, dtype=np.int64))
        np.save(os.path.join(yd, 'codes.npy'), codes)
        present = np.zeros((len(ds), len(codes)), bool)
        for t, z in enumerate(Z):
            present[t, [pos[c] for c in z['codes']]] = True
        np.save(os.path.join(yd, 'present.npy'), present)
        for k in fields:
            dt = Z[0][k].dtype
            fill = np.nan if np.issubdtype(dt, np.floating) else -9
            A = np.full((len(ds), len(codes)), fill, dtype=dt)
            for t, z in enumerate(Z):
                A[t, [pos[c] for c in z['codes']]] = z[k]
            tmp = os.path.join(yd, k + '.npy.tmp')
            with open(tmp, 'wb') as fh:
                np.save(fh, A)
            os.replace(tmp, os.path.join(yd, k + '.npy'))
        yrs[y] = dict(days=len(ds), codes=len(codes), fields=len(fields))
        N.log('  merge Y%d：%d 天 × %d 码 × %d 字段' % (y, len(ds), len(codes), len(fields)))
    import pandas as pd
    mf = pd.DataFrame(man).sort_values(['date', 'file']).reset_index(drop=True)
    p = os.path.join(out, 'partition_manifest.csv')
    N.atomic_write_csv(p, mf)
    N.atomic_write_json(os.path.join(out, 'panel_manifest.json'),
                        dict(years=yrs, n_days=len(days), first=days[0], last=days[-1], partition_manifest_sha256=N.sha_file(p),
                             n_source_files=len(mf), source_bytes=int(mf['bytes'].sum()), reader_sha256=N.sha_file(MN.__file__)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['days', 'merge', 'all'])
    ap.add_argument('--workers', type=int, default=24)
    a = ap.parse_args()
    t0 = time.time()
    out = None
    if a.step in ('days', 'all'):
        out, _ = run_days(a.workers)
    if a.step in ('merge', 'all'):
        out = merge(out)
    task = 'E6n_etl_%s' % a.step
    N.write_receipt(task, [os.path.join(out, 'panel_manifest.json')] if a.step != 'days' else [], code=[MN.__file__, __file__],
                    secs=round(time.time() - t0, 1), panel=N.rel(out))
    N.log('ETL %s 完成：%.0f s' % (a.step, time.time() - t0))


if __name__ == '__main__':
    main()
