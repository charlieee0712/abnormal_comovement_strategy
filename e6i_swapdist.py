#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i SWAP 换入 / 换出全分布 (plan §5.4 末段: "报告换入全分布与换出全分布, 不只报告救回的赢家")。推导段。
每个 SWAP 配置 (RR / RA / RS; 含 buffer 桥) 用 Stage 2 同一函数重建名单: A = 子 \\ 母 (换入), D = 母 \\ 子 (换出);
对每个 H 用 entry-fixed H 日超额 (bp) 统计 A 与 D 的形成日分布: 均值 / 中位 / P(y<0) / p10 / p90 / 格数,
以及按日配对的 (A 日均 − D 日均) 的均值。输出 statistics/swap_in_out_<seg>_<NN>.csv。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import time
import argparse
import collections
import traceback

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6i_s1base as SB
import e6i_stage2 as S2

ROUTES = ('RR', 'RA', 'RS')


def dstats(y, m):
    v = y[m]
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return dict(n=0, mean=np.nan, median=np.nan, p_neg=np.nan, p10=np.nan, p90=np.nan)
    return dict(n=int(len(v)), mean=float(v.mean()), median=float(np.median(v)), p_neg=float((v < 0).mean()),
                p10=float(np.percentile(v, 10)), p90=float(np.percentile(v, 90)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshard', type=int, default=1)
    a = ap.parse_args()
    assert a.segment in I.DERIV_SEGS or I.post_allowed(a.segment)   # Stage 3 技术修复: 后段需 E6i 记录 B
    t0 = time.time()
    FE.build_catalog()
    FE.CATALOG_IDS = {m['member_id'] for m in FE.CATALOG}
    I.set_protected_members(FE.protected_ids())
    dd = pd.read_csv(os.path.join(I.RES, 'registry', 'descriptors_A0.csv'), low_memory=False)
    dd = dd[dd.route_id.isin(ROUTES) & (dd.role == 'SWAP')]
    groups = collections.OrderedDict()
    for r in dd.to_dict('records'):
        groups.setdefault(S2.config_key(r), []).append(r)
    keys = list(groups)[a.shard::a.nshard]
    S = I.seg_i(a.segment, warm=False)
    RN = S2.Runner(S)
    lab = SB.labels(S)
    print('段就绪 %.0fs; SWAP 配置 %d' % (time.time() - t0, len(keys)), flush=True)
    rows = []
    for gi, k in enumerate(keys):
        rs = groups[k]
        r0 = rs[0]
        members = [x for x in str(r0['member_id']).replace('+', '|').split('|') if x in FE.CATALOG_IDS]
        try:
            I.guard_i(members, ['SWAP'], segment=a.segment, label_end=str(S.dates[-1].date()), use='label',
                      where='swapdist:' + r0['descriptor_id'])
            child, _, _ = RN.build(r0)
            M = RN.mother(r0['mother_id'])
            A_ = child & ~M.B
            D_ = M.B & ~child
            for r in rs:
                H = int(r['H'])
                y = lab['entry_%d' % H]
                sa, sd = dstats(y, A_), dstats(y, D_)
                with np.errstate(all='ignore'):
                    na, nd = A_.sum(1), D_.sum(1)
                    ma = np.where(na > 0, np.nansum(np.where(A_, y, 0.0), 1) / na, np.nan)
                    mdd = np.where(nd > 0, np.nansum(np.where(D_, y, 0.0), 1) / nd, np.nan)
                pair = ma - mdd
                rec = dict(descriptor_id=r['descriptor_id'], route_id=r['route_id'], mother_id=r['mother_id'],
                           member_id=r['member_id'], strength=r['strength'], policy=r.get('policy'),
                           direction=r['direction'], direction_role=r.get('direction_role'), H=H,
                           days_swapped=int(np.isfinite(pair).sum()), in_minus_out_daymean=float(np.nanmean(pair)))
                rec.update({'in_' + k2: v for k2, v in sa.items()})
                rec.update({'out_' + k2: v for k2, v in sd.items()})
                rows.append(rec)
        except Exception as e:
            traceback.print_exc()
            for r in rs:
                rows.append(dict(descriptor_id=r['descriptor_id'], status='FAILED_TECH', note=str(e)[:150]))
        if (gi + 1) % 50 == 0:
            print('  %d/%d %.0fs' % (gi + 1, len(keys), time.time() - t0), flush=True)
    od = os.path.join(I.RES, 'statistics')
    I.atomic_write_csv(os.path.join(od, 'swap_in_out_%s_%02d.csv' % (a.segment, a.shard)), pd.DataFrame(rows))
    print('[%s swapdist %02d] %d 行; %.0fs' % (a.segment, a.shard, len(rows), time.time() - t0))


if __name__ == '__main__':
    main()
