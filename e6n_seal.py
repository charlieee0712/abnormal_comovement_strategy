# -*- coding: utf-8 -*-
"""E6n 封存（brief §5 S5 / S6、W14；附录 D 固定键）：seal deriv / seal post → registration/seal_<phase>.json，固定键
written_at / n_files / queued_missing / n_receipts / sha256_manifest（+ all_ok / segments / expected / mc_plan）。
清单 = 账户 npz（accounts/<段>/*.npz）+ 随机 npz（randoms/<机制>/<段>/*.npz，含 donor 日志）+ 对应回执；
queued_missing = 首 1,024 计划分片（random_manifest × CHUNK）中没有 SUCCEEDED 回执者 + 最近 MC 计划中 topup > 0 的组数。"""
import os
import sys
import glob
import json
import time
import argparse

import pandas as pd

import e6n_core as N


def expected_tasks(segs):
    import e6n_rand as RN
    M = pd.read_csv(N.P('registry', 'random_manifest_E6n.csv'), keep_default_na=False)
    exp = []
    for seg in segs:
        for (mech, grp), g in M.groupby(['mechanism', 'group']):
            for q0 in range(0, RN.FIRST, RN.CHUNK):
                exp.append((mech, seg, grp, q0, RN.CHUNK))
    return exp


def missing_tasks(segs):
    """首 1,024 计划分片中没有 SUCCEEDED 回执者（'机制|段|分片'）。"""
    miss = []
    for mech, seg, grp, q0, n in expected_tasks(segs):
        stem = '%s__p%d_%d' % (grp.replace('|', '_'), q0, n)
        rp = N.P('task_status', 'E6n_rand_%s_%s_%s.receipt.json' % (mech, seg, stem))
        if not (os.path.exists(rp) and json.load(open(rp, encoding='utf-8')).get('status') == 'SUCCEEDED'):
            miss.append('%s|%s|%s' % (mech, seg, stem))
    return miss


def seal(phase):
    import e6n_gate as GT
    segs = N.DERIV_SEGS if phase == 'deriv' else N.POST_SEGS
    files, rec = [], []
    for seg in segs:
        files += sorted(glob.glob(N.P('accounts', seg, '*.npz')))
        files += sorted(glob.glob(N.P('randoms', '*', seg, '*.npz')))
        rec += sorted(glob.glob(N.P('task_status', 'E6n_accounts_%s_*.receipt.json' % seg)))
        rec += sorted(glob.glob(N.P('task_status', 'E6n_rand_*_%s_*.receipt.json' % seg)))
    miss = missing_tasks(segs)
    acc_missing = [(seg, f) for seg in segs for f in ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5', 'R2', 'A06')
                   if not os.path.exists(N.P('accounts', seg, '%s.npz' % f))]
    topup = 0
    plans = {}
    for seg in segs:
        p = N.P('results', phase if phase == 'deriv' else 'full', 'mc_plan_%s.csv' % seg)
        if os.path.exists(p):
            P = pd.read_csv(p, keep_default_na=False)
            if 'topup' in P.columns:
                topup += int((pd.to_numeric(P.topup, errors='coerce') > 0).sum())
                plans[seg] = dict(groups=len(P), topup_groups=int((pd.to_numeric(P.topup, errors='coerce') > 0).sum()),
                                  mc_limit=int(P.get('mc_limit', pd.Series(dtype=str)).astype(str).eq('True').sum()))
    man = {N.rel(f): N.sha_file(f) for f in files}
    s = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), phase=phase, segments=list(segs), n_files=len(files), queued_missing=len(miss) + topup + len(acc_missing),
             n_receipts=len(rec), sha256_manifest=man, missing_tasks=miss[:50], missing_accounts=acc_missing, mc_plan=plans,
             all_ok=bool(not miss and not acc_missing and topup == 0), freeze_sha256=N.sha_file(N.P('registration', GT.FREEZE)))
    p = N.P('registration', 'seal_%s.json' % phase)
    if os.path.exists(p):
        old = json.load(open(p, encoding='utf-8'))
        os.replace(p, p.replace('.json', '_superseded_%s.json' % old.get('written_at', 'x').replace(' ', '_').replace(':', '')))
    N.atomic_write_json(p, s)
    N.write_receipt('E6n_seal_%s' % phase, [p], code=[__file__], n_files=len(files), queued_missing=s['queued_missing'], all_ok=s['all_ok'])
    print(json.dumps({k: v for k, v in s.items() if k != 'sha256_manifest'}, ensure_ascii=False)[:2000])
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['seal', 'missing'])
    ap.add_argument('arg', help='seal：deriv / post；missing：段名（只打印首 1,024 缺回执分片数，供编排补跑）')
    a = ap.parse_args()
    if a.step == 'missing':
        if a.arg not in N.SEGMENTS:
            raise SystemExit('未知段 %s' % a.arg)
        print(len(missing_tasks([a.arg])))
        return 0
    if a.arg not in ('deriv', 'post'):
        raise SystemExit('seal 只接受 deriv / post')
    seal(a.arg)
    return 0


if __name__ == '__main__':
    sys.exit(main())
