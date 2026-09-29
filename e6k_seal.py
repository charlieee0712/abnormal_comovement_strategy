# -*- coding: utf-8 -*-
"""E6k 封存回执（brief §5 / 附录 D-1；plan §13.3；E6j e6j_seal 同式）：先计算、封存内容 hash 与回执、再读取统计与报告。
  --package deriv   推导两段：accounts/<段>、randoms/*/<段>（含 MC 增补分片）→ registration/seal_deriv.json（增补后 seal_deriv_v2.json …）
  --package post    两后段：同上 → registration/seal_post.json
版本只增不删：新版本先核对此前各版登记的文件 hash 全部未变，再登记当前全部文件并列出新增文件。
回执：确定性任务数 = 登记任务数 × 段数，随机分片须全部 SUCCEEDED 且与文件一一对应（FAILED 由同名 _rerun 覆盖）。verify() 供读数程序调用。"""
import e6k_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time

import pandas as pd

import e6k_core as K

SEGS = {'deriv': K.DERIV_SEGS, 'post': K.POST_SEGS}


def seal_path(pkg, v):
    return K.P('registration', ('seal_%s.json' % pkg) if v == 1 else ('seal_%s_v%d.json' % (pkg, v)))


def versions(pkg):
    vs, v = [], 1
    while os.path.exists(seal_path(pkg, v)):
        vs.append(v)
        v += 1
    return vs


def files_of(pkg):
    out = []
    for s in SEGS[pkg]:
        out += sorted(glob.glob(K.P('accounts', s, '*')))
        out += sorted(glob.glob(K.P('randoms', '*', s, '*.npz')))
    return [p for p in out if os.path.isfile(p)]


def receipts(pkg):
    ts = K.P('task_status')
    st = {}
    for s in SEGS[pkg]:
        for p in glob.glob(os.path.join(ts, 'run_det_%s_*.receipt.json' % s)) + glob.glob(os.path.join(ts, 'run_rand_*_%s_*.receipt.json' % s)):
            n = os.path.basename(p)[:-len('.receipt.json')]
            st[n] = json.load(open(p, encoding='utf-8'))['status']
    for n in list(st):                                                   # _rerun 覆盖同名 FAILED
        if n.endswith('_rerun') and st[n] == 'SUCCEEDED':
            st[n[:-6]] = 'SUCCEEDED'
    return st


def queued_receipts(pkg):
    """队列文件（首轮 logs/queue_<pkg>.txt + 增补 logs/queue_topup_<pkg>_*.txt）里每一行对应的回执名（2026-09-29 补：随机分片失败时
    回执与文件同时缺，只比数量看不出来）。"""
    names = []
    for f in [K.P('logs', 'queue_%s.txt' % pkg)] + sorted(glob.glob(K.P('logs', 'queue_topup_%s_*.txt' % pkg))):
        if not os.path.exists(f):
            continue
        for line in open(f, encoding='utf-8'):
            w = line.split()
            if not w:
                continue
            mother, meas = w[2].split('|')
            if w[0] == 'det':
                names.append('run_det_%s_%s__%s' % (w[1], mother, meas))
            else:
                names.append('run_rand_%s_%s_%s__%s__p%d_%d' % (w[3], w[1], mother, meas, int(w[4]), int(w[5])))
    return names


def check(pkg):
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    n_tasks = D.task.nunique()
    st = receipts(pkg)
    det = {k: v for k, v in st.items() if k.startswith('run_det_') and not k.endswith('_rerun')}
    rnd = {k: v for k, v in st.items() if k.startswith('run_rand_') and not k.endswith('_rerun')}
    bad = [k for k, v in list(det.items()) + list(rnd.items()) if v != 'SUCCEEDED']
    ok = len(det) == n_tasks * len(SEGS[pkg]) and not bad
    files = files_of(pkg)
    rfiles = [f for f in files if '/randoms/' in f]
    ok &= len(rfiles) == len(rnd)
    q = queued_receipts(pkg)
    missing = [n for n in q if st.get(n) != 'SUCCEEDED']
    ok &= not missing
    return ok, dict(det=len(det), det_expected=n_tasks * len(SEGS[pkg]), rand_receipts=len(rnd), rand_files=len(rfiles), bad=bad[:20],
                    queued=len(q), queued_missing=len(missing), queued_missing_head=missing[:20])


def seal(pkg):
    ok, info = check(pkg)
    if not ok:
        raise RuntimeError('封存前核对未过：%s' % info)
    vs = versions(pkg)
    prev = {}
    for v in vs:
        m = json.load(open(seal_path(pkg, v), encoding='utf-8'))
        for f, s in m['files'].items():
            if K.sha_file(K.P(f)) != s:
                raise RuntimeError('此前封存版本 %d 的文件已变：%s' % (v, f))
            prev[f] = s
    files = {K.rel(p): K.sha_file(p) for p in files_of(pkg)}
    new = sorted(set(files) - set(prev))
    v = (vs[-1] + 1) if vs else 1
    rec = dict(package=pkg, version=v, written_at=time.strftime('%Y-%m-%d %H:%M:%S'), segments=list(SEGS[pkg]), n_files=len(files),
               new_files=new if vs else [], receipts=info, files=files)
    K.atomic_write_json(seal_path(pkg, v), rec)
    K.write_receipt('seal_%s_v%d' % (pkg, v), [seal_path(pkg, v)], 'SUCCEEDED', n_files=len(files), n_new=len(new))
    print('seal %s v%d：%d 个文件（新增 %d）' % (pkg, v, len(files), len(new) if vs else len(files)), flush=True)
    return 0


def verify(pkg):
    """读数程序调用：最新版本及此前各版登记的文件 hash 全部未变；回执齐。返回 (ok, 问题列表)。"""
    vs = versions(pkg)
    if not vs:
        return False, ['未封存']
    bad = []
    for v in vs:
        m = json.load(open(seal_path(pkg, v), encoding='utf-8'))
        for f, s in m['files'].items():
            if not os.path.exists(K.P(f)) or K.sha_file(K.P(f)) != s:
                bad.append(f)
    latest = json.load(open(seal_path(pkg, vs[-1]), encoding='utf-8'))
    cur = set(K.rel(p) for p in files_of(pkg))
    unsealed = sorted(cur - set(latest['files']))
    bad += ['<未封存> ' + f for f in unsealed]
    return (not bad), bad


if __name__ == '__main__':
    a = sys.argv
    pkg = a[a.index('--package') + 1]
    if '--verify' in a:
        ok, bad = verify(pkg)
        print('OK' if ok else 'BAD %d' % len(bad), bad[:5])
        sys.exit(0 if ok else 2)
    sys.exit(seal(pkg))
