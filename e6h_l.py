#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h carried L 主网格 (brief §8, plan §8.1): 期限 x 续选缓冲 x 预算。

  8 账户 (R1/A03/R2/A06/A07/A08/T25/Blend3) x H{1,2,3,5,10,15,20,30}
  x b{0,5,10,15,20,30} x {matchN, loose} = **768 个原始描述符**

只用【旧输入与旧规则】, 所以按 brief §6 末条可以先算四段并封存 (L-Q 另有 NEW40
血缘, 登记前只跑推导段, 不在本脚本)。

效率关键: 续选缓冲的【目标掩码与 H 无关】(H 只进引擎的 rolling), 所以
96 个 (账户 x b x 预算) 掩码各算一次, 每个跑 8 个 H = 768。

阻断锚: b=0 必须【精确复现源账本】(relaxed_domain 在 b=0 走源 SRC 核心域);
两种预算在 b=0 都应回到源目标。
Blend3: 先对【成员各自】做缓冲, 再合并目标权重 (换手合并后重算, 不取成员平均)。

用法: python3 e6h_l.py --segment 2019-2023
"""
from __future__ import annotations
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6g_core as G
import e6g_desc as GD
import e6g_l as L6
import e6g_c as CC
import e6f_core as F
import e6e_core as K

RES = H.RES
ATOMS = dict(L6.ATOMS)
H_GRID = [1, 2, 3, 5, 10, 15, 20, 30]
B_GRID = [0, 5, 10, 15, 20, 30]
BUDGETS = ['matchN', 'loose']
BLEND_MEMBERS = ('A03', 'A06', 'A08')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    t0 = time.time()
    S = H.seg(a.segment, verbose=False)
    ctx = GD.GCtx(S)
    M = CC.MarketCtx(S)
    od = os.path.join(RES, 'L')
    os.makedirs(od, exist_ok=True)
    print('  段就绪 %.0fs' % (time.time() - t0), flush=True)

    # ---- 1. 逐原子账户: 源目标 + 各 (b, budget) 的缓冲目标 ----
    src_mask, tmask, diags = {}, {}, {}
    for nm, cid in ATOMS.items():
        cfg = GD.parse_cfg(cid)
        Nmask, score, cand, core_mask = ctx.full_mask_g(cfg)
        Tdrop = L6.veto_drop(ctx, cfg)
        src_mask[nm] = Nmask
        for b in B_GRID:
            Bmask, _, _ = L6.relaxed_domain(ctx, cfg['core'], b)
            for bud in BUDGETS:
                tg, dg = L6.buffered_targets(S, Nmask, Bmask, Tdrop, score, bud)
                tmask[(nm, b, bud)] = tg
                diags[(nm, b, bud)] = dg
        print('    %s 掩码完成 %.0fs' % (nm, time.time() - t0), flush=True)

    # ---- 2. 阻断锚: b=0 必须精确复现源目标 ----
    anch = []
    for nm in ATOMS:
        for bud in BUDGETS:
            nd = int((tmask[(nm, 0, bud)] != src_mask[nm]).sum())
            anch.append(dict(account=nm, budget=bud, n_cells_diff=nd, ok=(nd == 0)))
    bad = [x for x in anch if not x['ok']]
    if bad:
        raise SystemExit('b=0 锚不过 (brief §8 要求精确复现源账本): %s' % bad[:3])
    print('  b=0 锚: %d 个 (账户 x 预算) 全部逐格复现源目标' % len(anch), flush=True)

    # ---- 3. Blend3: 成员各自缓冲后合并目标权重 ----
    def blend_iv(b, bud):
        ivs = [F.dev_from_dense(S, tmask[(m, b, bud)]) for m in BLEND_MEMBERS]
        return G.blend3_weights(ivs)

    # ---- 4. 跑 768 格 ----
    rows = []
    for b in B_GRID:
        for bud in BUDGETS:
            for nm in list(ATOMS) + ['Blend3']:
                if nm == 'Blend3':
                    idx, val = blend_iv(b, bud)
                    tn = float(np.mean([len(x) for x in idx]))
                else:
                    idx, val = F.dev_from_dense(S, tmask[(nm, b, bud)])
                    tn = float(tmask[(nm, b, bud)].sum(axis=1).mean())
                for Hh in H_GRID:
                    g_, p_, tu, n8 = F.sparse_pnl_H(S, idx, val, Hh, F.COST)
                    br = CC.profile_and_impact(M, idx, val, Hh, full_profile=False)[0]
                    d = diags.get((nm, b, bud), {})
                    rows.append(dict(
                        segment=a.segment, account=nm, b=b, budget=bud, H=Hh,
                        descriptor_id='L|%s|b=%s|%s|H=%d' % (nm, b, bud, Hh),
                        gross_ann=G.ann(g_), net8_ann=G.ann(n8),
                        net12_ann=G.ann(g_ - tu * 12e-4),
                        turn_mean=float(np.nanmean(tu)), pos_mean=float(np.nanmean(p_)),
                        target_n=tn,
                        bracket_sqrt_mean=float(np.nanmean(br['sqrt'])),
                        bracket_lin_mean=float(np.nanmean(br['lin'])),
                        n_new_mean=(float(d['n_new'].mean()) if d else np.nan),
                        n_carried_mean=(float(d['n_carried'].mean()) if d else np.nan),
                        max_consecutive_days=(int(d['max_streak']) if d else -1)))
        print('    b=%s 完成 %.0fs (%d 行)' % (b, time.time() - t0, len(rows)), flush=True)

    df = pd.DataFrame(rows)
    assert len(df) == len(H_GRID) * len(B_GRID) * len(BUDGETS) * 8, \
        '行数 %d != 768' % len(df)
    df.to_csv(os.path.join(od, 'L_main_%s.csv' % a.segment), index=False)
    with open(os.path.join(od, 'L_b0_anchor_%s.json' % a.segment), 'w') as fh:
        json.dump(dict(segment=a.segment, n_checked=len(anch), n_pass=len(anch),
                       results=anch,
                       note='b=0 必须精确复现源账本 (brief §8); 两种预算都测'), fh,
                  indent=1, ensure_ascii=False)
    print('  [%s] L 主网格 %d 行, %.0fs' % (a.segment, len(df), time.time() - t0))


if __name__ == '__main__':
    main()
