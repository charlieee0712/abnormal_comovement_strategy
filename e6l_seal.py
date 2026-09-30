# -*- coding: utf-8 -*-
"""E6l 封存（附录 D-2；brief §5 / §8）：seal_deriv.json / seal_post.json = 该包全部产物文件 sha + 队列逐行回执核对（E6k lessons 20）。
队列 = 登记表推出的计划任务：确定性 masks / accounts（每段 104 任务）；随机首 1,024 路径分片（每 (机制, 测量) 按 --chunk 256）+ MC 增补计划
（results/<阶段>/mc_plan_<段>_*.csv 的 topup 行，按 e6l_topup.TOPUP_CHUNK = 64 一片；17:0x 前为 512，推导段无增补不受影响）。
任何计划任务缺成功回执（链上最后一个）→ 不封存。
  --pkg deriv|post [--chunk 256]     写 registration/seal_<pkg>.json（已存在则写 _v2 …，只增不删）
  verify(pkg)                        读数前核对：封存文件 sha 与磁盘一致（供 stats / policy 调用）"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import json
import argparse

import pandas as pd

import e6l_core as L
from e6l_topup import TOPUP_CHUNK


def planned(pkg, chunk=256):
    segs = L.DERIV_SEGS if pkg == 'deriv' else L.POST_SEGS
    D = L.read_csv_keep(L.P('registry', 'descriptors_E6l.csv'), usecols=['task'])
    tasks = sorted(D.task.unique())
    RR = L.read_csv_keep(L.P('registry', 'randoms_E6l.csv'), usecols=['mechanism', 'meas'])
    pairs = sorted(set(zip(RR.mechanism, RR.meas)))
    q = []
    for s in segs:
        for t in tasks:
            stem = t.replace('|', '__')
            q.append('run_det_masks_%s_%s' % (s, stem))
            q.append('run_det_accounts_%s_%s' % (s, stem))
        for mech, meas in pairs:
            for p0 in range(0, 1024, chunk):
                q.append('run_rand_%s_%s_%s__p%d_%d' % (mech, s, meas, p0, chunk))
        for f in sorted(glob.glob(L.P('results', pkg, 'mc_plan_%s_*.csv' % s))):
            P = pd.read_csv(f)
            for r in P[P.topup > 0].itertuples():
                mech, meas = r.rtask.split('|')
                for p0 in range(int(r.have), int(r.target), TOPUP_CHUNK):
                    q.append('run_rand_%s_%s_%s__p%d_%d' % (mech, s, meas, p0, min(TOPUP_CHUNK, int(r.target) - p0)))
    return q


def receipt_status(name):
    ch = L.rerun_chain(name)
    if not ch:
        return 'MISSING', None
    r = json.load(open(L._receipt_path(ch[-1]), encoding='utf-8'))
    return r['status'], r


def files_of(pkg):
    segs = L.DERIV_SEGS if pkg == 'deriv' else L.POST_SEGS
    fs = []
    for s in segs:
        fs += glob.glob(L.P('masks', s, '*'))
        fs += glob.glob(L.P('accounts', s, '*'))
        fs += glob.glob(L.P('randoms', '*', s, '*.npz'))
    if pkg == 'deriv':
        fs += glob.glob(L.P('results', 'stage_a', '*.csv'))
    fs += [L.P('registration', x) for x in (L.MANIFEST_P, L.MANIFEST_B, L.AUTH_PRE, L.AUTH_COND)]
    return sorted(f for f in fs if os.path.isfile(f))


def seal(pkg, chunk):
    q = planned(pkg, chunk)
    miss, bad = [], []
    for nm in q:
        st, _ = receipt_status(nm)
        if st == 'MISSING':
            miss.append(nm)
        elif st != 'SUCCEEDED':
            bad.append(nm)
    if miss or bad:
        raise RuntimeError('队列未全部成功：缺 %d（例 %s）；失败 %d（例 %s）' % (len(miss), miss[:3], len(bad), bad[:3]))
    fs = files_of(pkg)
    sha = {L.rel(f): L.sha_file(f) for f in fs}
    base = L.P('registration', 'seal_%s.json' % pkg)
    p = base
    k = 2
    while os.path.exists(p):
        p = L.P('registration', 'seal_%s_v%d.json' % (pkg, k))
        k += 1
    rec = dict(pkg=pkg, written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), n_files=len(sha), queue_rows=len(q), queue_missing=0,
               queue_failed=0, files_sha256=sha, frozen_manifest_sha256=L.sha_file(L.P('registration', L.MANIFEST_B)))
    L.atomic_write_json(p, rec)
    L.write_receipt(L.next_rerun('seal_%s' % pkg), [p], 'SUCCEEDED', n_files=len(sha), queue_rows=len(q))
    print('seal_%s：%d 文件；队列 %d 行全部成功（%s）' % (pkg, len(sha), len(q), os.path.basename(p)), flush=True)
    return 0


def latest_seal(pkg):
    fs = sorted(glob.glob(L.P('registration', 'seal_%s*.json' % pkg)), key=os.path.getmtime)
    return fs[-1] if fs else None


def verify(pkg):
    p = latest_seal(pkg)
    if p is None:
        return False, ['seal_%s 不存在' % pkg]
    rec = json.load(open(p, encoding='utf-8'))
    bad = []
    for rel_, s in rec['files_sha256'].items():
        f = L.P(rel_)
        if not os.path.exists(f) or L.sha_file(f) != s:
            bad.append(rel_)
    return not bad, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pkg', required=True, choices=('deriv', 'post'))
    ap.add_argument('--chunk', type=int, default=256)
    a = ap.parse_args()
    if a.pkg == 'post':
        for s in L.POST_SEGS:
            L.post_gate(s, 'seal_post')
    return seal(a.pkg, a.chunk)


if __name__ == '__main__':
    sys.exit(main())
