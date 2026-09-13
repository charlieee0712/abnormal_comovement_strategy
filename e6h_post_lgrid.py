#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h brief §8 末条: 新主路线在记录 B 指定的中心代表与 S1 组合上补 b{0,10} x H{3,5,15,20}。

名单在后段之前已冻结 (记录 B, 清单 SHA 复核), 所以这里只跑已批准的两条路线。
缓冲沿用 e6g_l.buffered_targets 的同一套推进规则, 但**可持有域按子名单定义**:

  Bmask_child(b) = 子名单 ∪ (母体核放宽到 b 档新开出来的那一圈)
                 = Nmask | (relaxed_domain(b) & ~relaxed_domain(0))

为什么不能直接用母体的 relaxed_domain(b): 子名单**不是**母体核的前 m 名
(M-T 的 SLOT 就是拿 T 的排序替掉一部分名额), 所以 `I ∩ 母体核` 里会有子名单外的票,
matchN 会让它们顶掉当日的子名单成员 —— b=0 也复现不了子名单 (实测差 4,536 格)。
按上式定义后 b=0 时新开的那一圈为空, Bmask = Nmask, 恒等严格成立;
b=10 的语义是"跌出子名单、但仍在母体核放宽 10 档以内, 就继续持有"。

Tdrop / score 取母体的 (否决与排序都在母体口径下)。
S1 组合按 Blend3 的做法: **成员各自缓冲后再合并目标权重**。

阻断锚: b=0 时缓冲目标必须逐格复现子名单本身。

用法: python3 e6h_post_lgrid.py --segment 2019-2023
"""
from __future__ import annotations
import os
import sys
import json
import time
import hashlib
import argparse
import collections

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_run_routes as RR
import e6h_expand as EX
import e6h_selection as SEL
import e6h_randoms as RD
import e6g_core as G
import e6g_desc as GD
import e6g_l as L6
import e6f_core as F

RES = H.RES
H_GRID = [3, 5, 15, 20]
B_GRID = [0, 10]
BUDGET = 'matchN'


def approved_ids():
    p = os.path.join(RES, 'registration', 'record_B_approved.json')
    d = json.load(open(p))
    assert d.get('status') == 'APPROVED'
    chk = dict(d)
    chk.pop('list_sha256', None)
    sha = hashlib.sha256(json.dumps(chk, indent=1, ensure_ascii=False,
                                    sort_keys=True).encode()).hexdigest()
    assert sha == d['list_sha256'], '清单 SHA 与批准时不符'
    ids = set()
    for e in d['entries']:
        ids |= set(e.get('descriptor_ids') or [])
    return d, ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    t0 = time.time()
    appr, ids = approved_ids()
    H.load_approval()
    ok_rids = set(appr['approved_route_ids'])
    rows_all = EX.all_descriptors()
    rows = [r for r in rows_all if r['descriptor_id'] in ids and not r.get('is_identity')]
    S = H.seg(a.segment, verbose=False)
    ctx = GD.GCtx(S)
    print('  清单 SHA OK; 已批准 route %s; 非 identity 描述符 %d'
          % (sorted(ok_rids), len(rows)), flush=True)

    # 账户清单: 每条路线的中心代表 + 每个 (路线, 母体) 的 S1 组合
    centers = {rid: RD.pick(rows_all, rid, pa, fl)
               for rid, pa, fl in RD.CENTERS if rid in ok_rids}
    by_rp = collections.defaultdict(list)
    for r in rows:
        by_rp[(r['route_id'], r['parent'])].append(r)

    # <=2018 冻结估计 (S1 只用等权, 不需要 mu; 这里只为记录成员数)
    pctx, out, anch = {}, [], []
    for name, rid, parent, members, kind in (
            [('CENTER|%s' % rid, rid, centers[rid]['parent'], [centers[rid]], 'center')
             for rid in sorted(centers) if centers[rid] is not None] +
            [('S1|%s|%s' % (rid, pa), rid, pa, ms, 's1')
             for (rid, pa), ms in sorted(by_rp.items())]):
        if parent not in pctx:
            pctx[parent] = RR.ParentCtx(S, parent)
        P = pctx[parent]
        cfg = P.cfg
        Tdrop = L6.veto_drop(ctx, cfg)
        # 成员子名单
        masks = []
        for r in members:
            keys = [k for k in (r.get('new_key'), r.get('vol_key'), r.get('risk_key'),
                                r.get('liq_key'), r.get('state_key')) if k]
            if rid == 'I-P-peer-up-laggard':
                keys += ['IND_CUR_20', 'REL_IND_20']
            H.guard_h(keys, 'trade', segment=a.segment, where='lgrid|' + r['descriptor_id'],
                      route_id=rid, rule_objects=[r['role']])
            m, wmul, _ = RR.build_mask(P, r)
            masks.append((r, m, wmul))
        if kind == 's1':
            w = SEL.hierarchical_weights([m[0] for m in masks], 'new_key')
        else:
            w = np.array([1.0])
        base0 = L6.relaxed_domain(ctx, cfg['core'], 0)[0]
        for b in B_GRID:
            ring = (L6.relaxed_domain(ctx, cfg['core'], b)[0] & ~base0) if b else None
            ivs, tns = [], []
            for (r, m, wmul) in masks:
                Bmask = m if ring is None else (m | ring)
                tg, _ = L6.buffered_targets(S, m, Bmask, Tdrop, P.score, BUDGET)
                if b == 0:
                    nd = int((tg != m).sum())
                    anch.append(dict(account=name, descriptor_id=r['descriptor_id'],
                                     n_cells_diff=nd, ok=(nd == 0)))
                idx, val = F.dev_from_dense(S, tg)
                if wmul is not None:
                    val = [v * wmul[t, idx[t]] if len(idx[t]) else v
                           for t, v in enumerate(val)]
                ivs.append((idx, val))
                tns.append(float(tg.sum(axis=1).mean()))
            if len(ivs) == 1:
                idx, val = ivs[0]
            else:
                idx, val = SEL.merge_weights(ivs, list(w))
            pidx, pval = F.dev_from_dense(S, P.B)
            for Hh in H_GRID:
                g_, p_, tu, n8 = F.sparse_pnl_H(S, idx, val, Hh, F.COST)
                g0, p0_, t0_, n0 = F.sparse_pnl_H(S, pidx, pval, Hh, F.COST)
                both = np.isfinite(np.asarray(g_)) & np.isfinite(np.asarray(g0))
                out.append(dict(
                    segment=a.segment, account=name, kind=kind, route_id=rid,
                    parent=parent, n_members=len(masks), b=b, budget=BUDGET, H=Hh,
                    gross_ann=H.ann(g_), net8_ann=H.ann(n8),
                    turn_mean=float(np.nanmean(tu)), pos_mean=float(np.nanmean(p_)),
                    target_n=float(np.mean(tns)),
                    parent_net8_ann=H.ann(n0),
                    d_net8_ann=H.ann(np.where(both, np.asarray(n8) - np.asarray(n0),
                                              np.nan))))
        print('    %-34s 完成 %.0fs' % (name, time.time() - t0), flush=True)

    bad = [x for x in anch if not x['ok']]
    if bad:
        raise SystemExit('b=0 锚不过 (缓冲目标必须复现子名单): %s' % bad[:3])
    od = os.path.join(RES, 'L')
    d = pd.DataFrame(out)
    d.to_csv(os.path.join(od, 'L_newroute_grid_%s.csv' % a.segment), index=False)
    with open(os.path.join(od, 'L_newroute_b0_anchor_%s.json' % a.segment), 'w') as fh:
        json.dump(dict(segment=a.segment, n_checked=len(anch), n_pass=len(anch),
                       list_sha256=appr['list_sha256'],
                       note='b=0 时缓冲目标须逐格复现子名单', results=anch[:40]),
                  fh, indent=1, ensure_ascii=False)
    print('  [%s] 新主路线补格 %d 行; b=0 锚 %d/%d; %.0fs'
          % (a.segment, len(d), len(anch), len(anch), time.time() - t0))
    print(d.pivot_table(index=['account', 'b'], columns='H', values='d_net8_ann')
          .round(3).to_string())


if __name__ == '__main__':
    main()
