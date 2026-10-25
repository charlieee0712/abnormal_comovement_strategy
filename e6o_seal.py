# -*- coding: utf-8 -*-
"""E6o 封存（附录 B.5）：
  python3 e6o_seal.py A2     → registration/seal_A2.json（推导段全部产物 sha 清单；任何后段写入之前）
  python3 e6o_seal.py final  → registration/seal_final.json（first_post_segment_write_at = B 阶段首个后段账户文件写入时刻）"""
import os
import sys
import json
import glob
import time

import numpy as np

import e6o_core as O


def manifest(paths):
    out = {}
    for p in sorted(paths):
        if os.path.isfile(p):
            out[O.rel(p)] = O.sha_file(p)
    return out


def main():
    which = sys.argv[1]
    if which == 'A2':
        if os.path.exists(O.P('registration', 'seal_A2.json')):
            raise RuntimeError('seal_A2 已存在（不重写）')
        if glob.glob(O.P('accounts_run', 'full', '*', '*.npz')):
            raise RuntimeError('已有后段账户文件：封存顺序被破坏')
        ps = (glob.glob(O.P('accounts_run', 'deriv', '*', '*.npz')) + glob.glob(O.P('accounts_run', 'shadow_deriv', '*.npz')) +
              glob.glob(O.P('checkpoints', 'A2_end', '*', '*.npz')) + glob.glob(O.P('randoms', 'random_paths_A2*.csv')) +
              [O.P('diagnostics', 'G1_E6o.csv'), O.P('verify', 'refcheck_E6o.csv'), O.P('registration', 'freeze_E6o.json'),
               O.P('task_status', 'accounts_A2.csv')])
        man = manifest(ps)
        j = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), n_files=len(man), sha256_manifest=man,
                 note='推导段（2010-01-04 … 2018-12-31）全部预登记分支（账户 / 影子 / 随机 / G1 / 手工逐日账）封存；B 阶段只在本文件存在后写后段')
        O.atomic_write_json(O.P('registration', 'seal_A2.json'), j)
        print(json.dumps(dict(n_files=len(man), written_at=j['written_at']), ensure_ascii=False))
    else:
        a2 = json.load(open(O.P('registration', 'seal_A2.json')))
        full = glob.glob(O.P('accounts_run', 'full', '*', '*.npz'))
        first = min(os.path.getmtime(p) for p in full)
        fts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first))
        ps = []
        for d in ('statistics', 'events', 'diagnostics', 'verify', 'registration', 'reports', 'accounts/daily', 'randoms'):
            ps += [p for p in glob.glob(O.P(d, '**', '*'), recursive=True) if os.path.isfile(p) and not p.endswith('seal_final.json')]
        man = manifest(ps)
        j = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), n_files=len(man), sha256_manifest=man, first_post_segment_write_at=fts,
                 seal_A2_written_at=a2['written_at'], order_ok=a2['written_at'] < fts)
        O.atomic_write_json(O.P('registration', 'seal_final.json'), j)
        print(json.dumps(dict(n_files=len(man), first_post=fts, seal_A2=a2['written_at'], order_ok=j['order_ok']), ensure_ascii=False))


if __name__ == '__main__':
    main()
