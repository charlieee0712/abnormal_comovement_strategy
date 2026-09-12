#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h carried T2: 绝对人数 vs 百分比深度 (brief §9, plan §9.2)。答 Q12。

  核 {KTC_mean, T, KT_mean} x 否决栈 {C:k5+cr5:k10, cvr_1d:k10+cr5:k10, 无}
  x 预算 {N=30..200 绝对 (9) + keep=15..50 百分比 (7)} x {PRE_VETO, POST_VETO}
  = 3 x 3 x 16 x 2 = **288 个原始描述符** x 四段

口径要点 (plan §9.2):
  - PRE_VETO 先取额度再否决 (最终人数 < 额度); POST_VETO 先否决再取额度。
  - **POST 的比例分母仍是冻结 pool0**, 不悄悄换成幸存域。
  - 人数不足取全部合法票, **不绕 veto**。
  - RANKBUDGET 主研究; keep 越大表示保留更多 (不用"更深"表达相反含义)。

阻断锚: 否决栈 = 无 时, PRE_VETO 与 POST_VETO 必须【逐格恒等】(48 对)。

用法: python3 e6h_t2.py --segment 2019-2023
"""
from __future__ import annotations
import os
import sys
import json
import time
import math
import argparse
import itertools

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6g_core as G
import e6g_desc as GD
import e6f_core as F
import e6e_core as K

RES = H.RES
NS_ABS = [30, 40, 50, 60, 80, 100, 120, 150, 200]
KEEPS = [15, 20, 25, 30, 35, 40, 50]
CORES = ['KTC_mean', 'T', 'KT_mean']
VETOS = {'C:k5+cr5:k10': 'C:k5+cr5:k10',
         'cvr_1d:k10+cr5:k10': 'cvr_1d:k10+cr5:k10',
         'none': None}


def keep_absN(P, poolmask, N):
    """逐日在 poolmask 内按 P 升序取 min(N, n) 只。稳定排序同 RANKBUDGET。"""
    T, Nc = P.shape
    out = np.zeros((T, Nc), bool)
    for t in range(T):
        v = np.where(poolmask[t] & ~np.isnan(P[t]))[0]
        n = len(v)
        if n == 0:
            continue
        r = min(int(N), n)
        order = np.lexsort((v, P[t, v]))
        out[t, v[order[:r]]] = True
    return out


def keep_pct_denom(P, poolmask, d, denom_mask):
    """按【denom_mask 的人数】定额度, 从 poolmask 里取。POST_VETO 的比例分母用
       冻结 pool0 (plan §9.2), 所以 denom_mask 与 poolmask 可以不同。"""
    T, Nc = P.shape
    out = np.zeros((T, Nc), bool)
    for t in range(T):
        nd = int((denom_mask[t] & ~np.isnan(P[t])).sum())
        r = int(math.floor(nd * float(d) / 100.0))
        if r < 1:
            continue
        v = np.where(poolmask[t] & ~np.isnan(P[t]))[0]
        if len(v) == 0:
            continue
        r = min(r, len(v))
        order = np.lexsort((v, P[t, v]))
        out[t, v[order[:r]]] = True
    return out


def build_core_score(ctx, name):
    """三个核的分数 (走 E6g 的 leg_pct + combine, 口径与源一致)。"""
    S = ctx.S
    md = 'NS'
    spK = GD.spec_of_key(K.FK)
    spT = GD.spec_of_key(K.FT)
    spC = GD.spec_of_key(K.FC)
    if name == 'T':
        return ctx.leg_pct(spT, md, 'hi', 'identity')
    legs = [spK, spT] + ([spC] if name == 'KTC_mean' else [])
    Ps = [ctx.leg_pct(sp, md, 'hi', 'identity') for sp in legs]
    return F.combine_dense(Ps, 'mean', complete=(name == 'KTC_mean'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    t0 = time.time()
    S = H.seg(a.segment, verbose=False)
    ctx = GD.GCtx(S)
    od = os.path.join(RES, 'T')
    os.makedirs(od, exist_ok=True)

    scores = {c: build_core_score(ctx, c) for c in CORES}
    p0 = S.p0c
    drops = {}
    for vn, vid in VETOS.items():
        if vid is None:
            drops[vn] = np.zeros_like(p0)
        else:
            cfg = GD.parse_cfg('KTC_mean@25|%s' % vid)
            dr = ctx.build_veto_drop_g(cfg['veto'], cfg['core'], None, sel='SRC')
            drops[vn] = np.zeros_like(p0) if dr is None else dr
    print('  核与否决就绪 %.0fs' % (time.time() - t0), flush=True)

    rows, masks = [], {}
    for cn, vn, order in itertools.product(CORES, VETOS, ('PRE_VETO', 'POST_VETO')):
        P = scores[cn]
        dr = drops[vn]
        surv = p0 & ~dr
        for bud in [('N', n) for n in NS_ABS] + [('keep', k) for k in KEEPS]:
            kind, val = bud
            if order == 'PRE_VETO':
                sel = (keep_absN(P, p0, val) if kind == 'N'
                       else keep_pct_denom(P, p0, val, p0))
                final = sel & ~dr
            else:
                final = (keep_absN(P, surv, val) if kind == 'N'
                         else keep_pct_denom(P, surv, val, p0))
            did = 'T2|%s|%s|%s=%s|%s' % (cn, vn, kind, val, order)
            masks[(cn, vn, kind, val, order)] = final
            idx, v_ = F.dev_from_dense(S, final)
            g_, pp, tu, n8 = F.sparse_pnl_H(S, idx, v_, K.HOLD, F.COST)
            rows.append(dict(segment=a.segment, descriptor_id=did, core=cn, veto=vn,
                             budget_kind=kind, budget=val, order=order,
                             gross_ann=G.ann(g_), net8_ann=G.ann(n8),
                             turn_mean=float(np.nanmean(tu)),
                             pos_mean=float(np.nanmean(pp)),
                             target_n=float(final.sum(axis=1).mean()),
                             days_empty=int((final.sum(axis=1) == 0).sum())))
        print('    %s / %s / %s 完成 %.0fs' % (cn, vn, order, time.time() - t0),
              flush=True)

    # 阻断锚: 无否决时 PRE 与 POST 必须逐格恒等
    anch = []
    for cn in CORES:
        for bud in [('N', n) for n in NS_ABS] + [('keep', k) for k in KEEPS]:
            a1 = masks[(cn, 'none', bud[0], bud[1], 'PRE_VETO')]
            a2 = masks[(cn, 'none', bud[0], bud[1], 'POST_VETO')]
            nd = int((a1 != a2).sum())
            anch.append(dict(core=cn, budget='%s=%s' % bud, n_diff=nd, ok=(nd == 0)))
    bad = [x for x in anch if not x['ok']]
    if bad:
        raise SystemExit('无否决时 PRE/POST 必须恒等, 但有 %d 对不同: %s' % (len(bad), bad[:3]))

    df = pd.DataFrame(rows)
    assert len(df) == 288, '行数 %d != 288' % len(df)
    df.to_csv(os.path.join(od, 'T2_budget_%s.csv' % a.segment), index=False)
    with open(os.path.join(od, 'T2_anchor_%s.json' % a.segment), 'w') as fh:
        json.dump(dict(segment=a.segment, n_pairs=len(anch), n_pass=len(anch),
                       note='否决栈=无 时 PRE_VETO 与 POST_VETO 必须逐格恒等'),
                  fh, indent=1, ensure_ascii=False)
    print('  [%s] T2 %d 行; PRE/POST 恒等锚 %d/%d; %.0fs'
          % (a.segment, len(df), len(anch), len(anch), time.time() - t0))


if __name__ == '__main__':
    main()
