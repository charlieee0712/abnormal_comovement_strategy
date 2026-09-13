#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 后段的匹配随机参照 —— **只跑记录 B 已批准路线的中心代表**。

为什么需要它: B-02-IPUP 的事前读法写死为
  「后段读法: 先看相对匹配随机, 再看相对母体; 两者不一致时以匹配随机为准并写明」
而 e6h_post.py 封存的对照只有 母体 / 同人数核心 / 同人数反向 / 共同域父 / 同仓位,
没有匹配随机那道。这里按 e6h_randoms.py 的同一套机制补上, 参数、种子、MCSE 规则
全部沿用, 不改 e6h_randoms.py (推导段产物保持可复现)。

中心代表取自 e6h_randoms.CENTERS, 但只保留 route_id 在已批准清单内的两条。
守卫照常生效: 未批准的 route_id 进后段会被 guard_h 拒绝。

用法: python3 e6h_post_randoms.py --segment 2019-2023 [--draws 256]
"""
from __future__ import annotations
import os
import sys
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_rules as RU
import e6h_run_routes as RR
import e6h_expand as EX
import e6h_randoms as RD

RES = H.RES


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--draws', type=int, default=256)
    a = ap.parse_args()
    assert a.segment in H.POST_SEGS, '本脚本只跑后段'
    t0 = time.time()
    appr = H.load_approval()
    ok_rids = set(appr.get('routes') or ())
    centers = [c for c in RD.CENTERS if c[0] in ok_rids]
    print('  记录 B 已批准 route: %s' % sorted(ok_rids), flush=True)
    print('  本段跑 %d 条中心代表 (全库 %d 条里已批准的)' % (len(centers), len(RD.CENTERS)), flush=True)

    rows_all = EX.all_descriptors()
    S = H.seg(a.segment, verbose=False)
    od = os.path.join(RES, 'random_registry')
    os.makedirs(od, exist_ok=True)

    out, pctx = [], {}
    for rid, parent, filt in centers:
        r = RD.pick(rows_all, rid, parent, filt)
        if r is None:
            print('  !! %s 中心代表没找到' % rid, flush=True)
            continue
        keys = [k for k in (r.get('new_key'), r.get('vol_key'), r.get('risk_key'),
                            r.get('liq_key'), r.get('state_key')) if k]
        if rid == 'I-P-peer-up-laggard':
            keys += ['IND_CUR_20', 'REL_IND_20']
        H.guard_h(keys, 'trade', segment=a.segment, where='post_random|' + rid,
                  route_id=rid, rule_objects=[r['role']])
        if parent not in pctx:
            pctx[parent] = RR.ParentCtx(S, parent)
        P = pctx[parent]
        mask, wmul, _ = RR.build_mask(P, r)
        real = RU.run_mask(S, mask, wmul)
        added = mask & ~P.B
        removed = P.B & ~mask
        if added.sum() > 0 and removed.sum() == 0:
            kind, domain, changed = 'additive', P.D, added
        elif removed.sum() > 0 and added.sum() == 0:
            kind, domain, changed = 'subtractive', P.B, removed
        else:
            kind, domain, changed = 'mixed', P.legal, mask
        counts = changed.sum(axis=1)
        iplan = RD.industry_plan(S, domain, changed)
        for level in ('U_IID', 'I_IID', 'I_P20'):
            n_draw = a.draws
            while True:
                rng = np.random.default_rng(
                    RD.SEED0 + abs(hash((rid, parent, level))) % 10 ** 6)
                means = []
                for j in range(n_draw):
                    if level == 'I_IID':
                        rs = RD.draw_industry_fast(S, iplan, rng)
                    else:
                        rs = RD.draw_matched(S, domain, counts, level, rng, S.icodes)
                    if kind == 'additive':
                        m2 = P.B | rs
                    elif kind == 'subtractive':
                        m2 = P.B & ~rs
                    else:
                        m2 = rs
                    means.append(H.ann(RU.run_mask(S, m2)[3]))
                mm = float(np.mean(means))
                sd = float(np.std(means, ddof=1))
                mcse = sd / np.sqrt(n_draw)
                if mcse <= RD.MCSE_TARGET or n_draw >= 1024:
                    break
                n_draw = 512 if n_draw < 512 else 1024
            real8 = H.ann(real[3])
            tail = float(np.mean(np.asarray(means) >= real8))
            out.append(dict(route_id=rid, parent=parent, segment=a.segment,
                            descriptor_id=r['descriptor_id'], kind=kind,
                            match_level=level, n_draws=n_draw,
                            real_net8=real8, parent_net8=H.ann(P.pnl[3]),
                            random_mean=mm, random_sd=sd, mcse=mcse,
                            mcse_ok=bool(mcse <= RD.MCSE_TARGET),
                            real_minus_random=real8 - mm,
                            reference_tail_fraction=tail,
                            n_changed_cells=int(changed.sum()),
                            note='tail_fraction 不是 p 值 (plan 4.4 / R8)'))
            print('    %-24s %-7s n=%4d 真实 %+.3f 随机 %+.3f 差 %+.3f MCSE %.4f 尾部 %.3f'
                  % (rid, level, n_draw, real8, mm, real8 - mm, mcse, tail), flush=True)
    pd.DataFrame(out).to_csv(
        os.path.join(od, 'random_refs_post_%s.csv' % a.segment), index=False)
    print('  [%s] 后段随机参照 %d 行, %.0fs' % (a.segment, len(out), time.time() - t0))


if __name__ == '__main__':
    main()
