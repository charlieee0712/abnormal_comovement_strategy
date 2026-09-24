#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 测量计算驱动: 一个段 x 若干轴 (或成员) -> 缓存 (带血缘 sidecar) + 逐成员计时/覆盖。

守卫: 新测量只许推导段 (记录 B 前); LEGACY 成员 (源键) 不受限。
输出: cache/<seg>/<member>__<policy>.npy/.json; runtime/compute_<seg>_<axes>.csv; receipt。

用法: python3 e6i_compute.py --segment 2015-2018 --axes T,K [--members a,b] [--force]
"""
from __future__ import annotations
import e6i_boot  # noqa: F401  (必须最先: 关掉 pyarrow S3 的 192 个 AwsEventLoop 线程)
import os
import sys
import time
import argparse
import resource
import traceback

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--axes', default='T,K,V,R,O,C,A,S')
    ap.add_argument('--members', default='')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    t0 = time.time()
    FE.build_catalog()
    I.set_protected_members(FE.protected_ids())
    axes = set(a.axes.split(','))
    want = set(x for x in a.members.split(',') if x)
    todo = [m for m in FE.CATALOG if m['axis_id'] in axes and (not want or m['member_id'] in want)]
    if a.segment in I.POST_SEGS:
        # Stage 3 技术修复: 后段只算 E6i 记录 B 批准的成员 (+ 不受保护的源键); 未批成员不算、不读
        assert I.post_allowed(a.segment), '后段需要 E6i 记录 B'
        todo = [m for m in todo if (not I.is_protected_member(m['member_id']))
                or m['member_id'] in I._APPROVAL_I['members']]
    # 守卫: 一次性对整批新测量做段检查 (推导段才放行)
    I.guard_i([m['member_id'] for m in todo], segment=a.segment, use='compute',
              where='e6i_compute:%s' % a.axes)
    S = I.seg_i(a.segment, verbose=False)
    t_seg = time.time() - t0
    B = FE.Base(S)
    t_base = time.time() - t0 - t_seg
    print('段 %s T=%d Nc=%d 预热=%s(%s 起, %d 行) 段就绪 %.0fs Base %.0fs; 本批 %d 成员'
          % (a.segment, S.T, S.Nc, S.warm_tag_i, S.warm_start_i, len(B.dates_w), t_seg, t_base,
             len(todo)), flush=True)
    rows, n_fail = [], 0
    for i, m in enumerate(todo):
        mid, pol = m['member_id'], m['policy']
        if (not a.force) and I.has_member(a.segment, mid, pol):
            rows.append(dict(member_id=mid, status='CACHED'))
            continue
        ts = time.time()
        try:
            A = m['fn'](B)
            A = np.asarray(A, dtype=np.float64)
            assert A.shape == B.x.shape, ('形状不符', A.shape, B.x.shape)
            G = B.to_seg(A)
            G = np.where(np.isfinite(G), G, np.nan)
            meta = {k: v for k, v in m.items() if k != 'fn'}
            meta.update(source_lineage='e6i_features:%s' % mid, formula_version=I.VERSION,
                        warm_tag=S.warm_tag_i, warm_start=S.warm_start_i)
            I.save_member(S, mid, pol, G, meta)
            fin = np.isfinite(G)
            p0 = S.p0c
            rows.append(dict(member_id=mid, axis=m['axis_id'], family=m['family_id'],
                             source_class=m['source_class'], policy=pol, status='SUCCEEDED',
                             sec=round(time.time() - ts, 2),
                             cov_pool0=float(fin[p0].mean()) if p0.any() else np.nan,
                             cov_all=float(fin.mean()),
                             n_unique_pool0=int(len(np.unique(G[p0 & fin]))) if (p0 & fin).any()
                             else 0,
                             p01=float(np.nanquantile(G[p0 & fin], 0.01)) if (p0 & fin).any()
                             else np.nan,
                             p50=float(np.nanquantile(G[p0 & fin], 0.5)) if (p0 & fin).any()
                             else np.nan,
                             p99=float(np.nanquantile(G[p0 & fin], 0.99)) if (p0 & fin).any()
                             else np.nan))
        except Exception as e:
            n_fail += 1
            rows.append(dict(member_id=mid, axis=m['axis_id'], status='FAILED_TECH',
                             error='%s: %s' % (type(e).__name__, str(e)[:200]),
                             sec=round(time.time() - ts, 2)))
            traceback.print_exc()
        if (i + 1) % 10 == 0:
            print('  %d/%d  %.0fs  rss %.1f GB' % (i + 1, len(todo), time.time() - t0,
                                                  resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                                                  / 1e6), flush=True)
    d = pd.DataFrame(rows)
    tag = a.axes.replace(',', '') if not want else 'custom'
    p = os.path.join(I.RES, 'runtime', 'compute_%s_%s.csv' % (a.segment, tag))
    I.atomic_write_csv(p, d)
    I.write_receipt(os.path.join(I.RES, 'task_status', 'compute_%s_%s.receipt.json'
                                 % (a.segment, tag)), 'compute:%s:%s' % (a.segment, tag), [p],
                    status='SUCCEEDED' if n_fail == 0 else 'FAILED', n_fail=n_fail,
                    n_members=len(todo), elapsed_s=round(time.time() - t0, 1),
                    peak_rss_gb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6)
    ok = d[d.status == 'SUCCEEDED']
    print('[%s %s] 成功 %d / 失败 %d / 缓存 %d; 耗时 %.0fs; 峰值 RSS %.1f GB'
          % (a.segment, a.axes, len(ok), n_fail, int((d.status == 'CACHED').sum()),
             time.time() - t0, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6))
    if len(ok):
        print(ok.sort_values('sec', ascending=False)[['member_id', 'sec', 'cov_pool0',
                                                      'p50']].head(8).to_string(index=False))
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == '__main__':
    main()
