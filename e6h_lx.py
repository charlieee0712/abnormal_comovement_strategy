#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h carried L 的两个小块 (brief §8; E6g 曾 deferred 这两块)。

A. actual_incumbent: 续选缓冲的"在册"集合改成【T 时实际有库存】的票, 而不是
   "上一次的目标"。所以目标掩码变成【H 相关】。
   八账户 x H{3,5,15,20} x b{0,10,20} x 两预算 = 192。与 target_incumbent 并排。

B. L-X 提前退出: R1/R2/A06/A08 x H{3,5,15,20} x b{0,10,20} x 两开关四组合
   (源否决触发 / 跌出核心放宽边界), matchN 主版 = 192。**全关 = 同账户参照**。

为此要自己写一个带提前退出的持仓引擎 `pnl_exit`。
**阻断锚**: 退出条件全假时, `pnl_exit` 必须复现 `F.sparse_pnl_H`
(浮点求和顺序不同, 所以按 max|d| < 1e-12 判, 并把实测值记下来)。

口径 (plan §8.2): 续选缓冲只决定【未来新批次】; 既有批次不隐含提前退出。
`actual_incumbent(T)` 是 T 时已成交且有库存的票, 不是 T+1 成交后倒填。

用法: python3 e6h_lx.py --segment 2019-2023
"""
from __future__ import annotations
import os
import sys
import json
import time
import argparse
import itertools

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6g_core as G
import e6g_desc as GD
import e6g_l as L6
import e6f_core as F
import e6e_core as K

RES = H.RES
HS = [3, 5, 15, 20]
BS = [0, 10, 20]
BUDGETS = ['matchN', 'loose']
LX_ACCOUNTS = ['R1', 'R2', 'A06', 'A08']


def held_weights(S, idx, val, Hh, alive_lt=None):
    """逐日【实际持有权重】(T, Nc)。alive_lt = (T,Nc) 的"最近一次触发日"数组;
       None = 不提前退出。与 F.sparse_pnl_H 同一时点约定:
       day t 持有的是批次 s ∈ [t-1-H, t-2], 除以 den[t-2]。"""
    T, Nc = S.T, S.Nc
    den = np.minimum(np.arange(1, T + 1), Hh).astype(float)
    W = np.zeros((T, Nc))
    for t in range(2, T):
        acc = W[t]
        for s in range(max(0, t - 1 - Hh), t - 1):
            ii = idx[s]
            if not len(ii):
                continue
            vv = val[s]
            if alive_lt is not None:
                # 批次 s 的票 i 在 t 仍活着 <=> [s, t-2] 内没触发过
                keep = alive_lt[t - 2, ii] < s
                if not keep.any():
                    continue
                np.add.at(acc, ii[keep], vv[keep])
            else:
                np.add.at(acc, ii, vv)
        acc /= den[t - 2]
    return W


def pnl_exit(S, idx, val, Hh, cost_bp, alive_lt=None):
    """带提前退出的账本。alive_lt=None 时应复现 F.sparse_pnl_H。"""
    W = held_weights(S, idx, val, Hh, alive_lt)
    port = (W * S.r0).sum(axis=1)
    pos = W.sum(axis=1)
    gross = port - S.bench * pos
    turn = np.zeros(S.T)
    turn[1:] = 0.5 * np.abs(W[1:] - W[:-1]).sum(axis=1)
    net = gross - turn * cost_bp / 1e4
    return gross, pos, turn, net


def last_trigger(cond):
    """(T,Nc) bool -> (T,Nc) int: 每格上"最近一次为真的日子", 没有则 -1。"""
    T, Nc = cond.shape
    lt = np.full((T, Nc), -1, dtype=np.int32)
    cur = np.full(Nc, -1, dtype=np.int32)
    for t in range(T):
        cur = np.where(cond[t], t, cur)
        lt[t] = cur
    return lt


def buffered_targets_actual(S, Nmask, Bmask, Tdrop, score, budget, Hh):
    """把"在册"改成【T 时实际有库存】。actual = 最近 H 个批次的并集。
       所以目标掩码变成 H 相关 (target_incumbent 版不是)。"""
    T, Nc = Nmask.shape
    out = np.zeros((T, Nc), bool)
    batches = []                      # 最近 H 个已发目标批次
    for t in range(T):
        I = np.zeros(Nc, bool)
        for b in batches[-Hh:]:
            I |= b
        p0 = S.p0c[t]
        elig = I & Bmask[t] & p0 & ~(Tdrop[t] if Tdrop is not None else False)
        if budget == 'matchN':
            m = int(Nmask[t].sum())
            sel = np.zeros(Nc, bool)
            if m > 0:
                old = np.flatnonzero(elig)
                if len(old) > m:
                    o = old[np.argsort(np.where(np.isfinite(score[t, old]),
                                                score[t, old], np.inf))][:m]
                    sel[o] = True
                else:
                    sel[old] = True
                    need = m - len(old)
                    fresh = np.flatnonzero(Nmask[t] & ~sel)
                    if need > 0 and len(fresh):
                        f = fresh[np.argsort(np.where(np.isfinite(score[t, fresh]),
                                                      score[t, fresh], np.inf))][:need]
                        sel[f] = True
        else:
            sel = Nmask[t] | elig
        out[t] = sel
        batches.append(sel)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    t0 = time.time()
    S = H.seg(a.segment, verbose=False)
    ctx = GD.GCtx(S)
    od = os.path.join(RES, 'L')
    os.makedirs(od, exist_ok=True)

    base = {}
    for nm, cid in L6.ATOMS.items():
        cfg = GD.parse_cfg(cid)
        Nmask, score, cand, cm = ctx.full_mask_g(cfg)
        base[nm] = dict(cfg=cfg, N=Nmask, score=score,
                        Tdrop=L6.veto_drop(ctx, cfg))
    print('  母体就绪 %.0fs' % (time.time() - t0), flush=True)

    # ---- 阻断锚: 退出条件全假 -> 复现 sparse_pnl_H ----
    anch = []
    for nm in ('R2', 'A06'):
        idx, val = F.dev_from_dense(S, base[nm]['N'])
        for Hh in (5, 20):
            ref = F.sparse_pnl_H(S, idx, val, Hh, F.COST)
            got = pnl_exit(S, idx, val, Hh, F.COST, None)
            md = max(float(np.nanmax(np.abs(np.asarray(ref[i]) - np.asarray(got[i]))))
                     for i in range(4))
            anch.append(dict(account=nm, H=Hh, max_abs_diff=md, ok=bool(md < 1e-12)))
    bad = [x for x in anch if not x['ok']]
    if bad:
        raise SystemExit('pnl_exit 在无退出时必须复现 sparse_pnl_H: %s' % bad)
    print('  引擎锚: %d 个全过, max|d| %.3e'
          % (len(anch), max(x['max_abs_diff'] for x in anch)), flush=True)

    rows = []
    # ================= A. actual_incumbent =================
    for nm, Hh, b, bud in itertools.product(list(L6.ATOMS), HS, BS, BUDGETS):
        d = base[nm]
        Bmask, _, _ = L6.relaxed_domain(ctx, d['cfg']['core'], b)
        tg_t, _ = L6.buffered_targets(S, d['N'], Bmask, d['Tdrop'], d['score'], bud)
        tg_a = buffered_targets_actual(S, d['N'], Bmask, d['Tdrop'], d['score'], bud, Hh)
        for kind, tg in (('target_incumbent', tg_t), ('actual_incumbent', tg_a)):
            idx, val = F.dev_from_dense(S, tg)
            g_, p_, tu, n8 = F.sparse_pnl_H(S, idx, val, Hh, F.COST)
            rows.append(dict(segment=a.segment, block='incumbent', account=nm,
                             H=Hh, b=b, budget=bud, incumbent_kind=kind,
                             descriptor_id='LI|%s|H=%d|b=%d|%s|%s' % (nm, Hh, b, bud, kind),
                             gross_ann=G.ann(g_), net8_ann=G.ann(n8),
                             turn_mean=float(np.nanmean(tu)),
                             pos_mean=float(np.nanmean(p_)),
                             target_n=float(tg.sum(axis=1).mean()),
                             cells_vs_target=int((tg != tg_t).sum())))
    print('  A. actual_incumbent 完成 %.0fs (%d 行)' % (time.time() - t0, len(rows)),
          flush=True)

    # ================= B. L-X 提前退出 =================
    for nm in LX_ACCOUNTS:
        d = base[nm]
        drop = d['Tdrop'] if d['Tdrop'] is not None else np.zeros_like(S.p0c)
        for Hh, b in itertools.product(HS, BS):
            Bmask, _, _ = L6.relaxed_domain(ctx, d['cfg']['core'], b)
            tg, _ = L6.buffered_targets(S, d['N'], Bmask, d['Tdrop'], d['score'],
                                        'matchN')
            idx, val = F.dev_from_dense(S, tg)
            conds = dict(veto=drop, out_of_band=(S.p0c & ~Bmask))
            for sw_v, sw_b in itertools.product((False, True), (False, True)):
                c = np.zeros_like(S.p0c)
                if sw_v:
                    c = c | conds['veto']
                if sw_b:
                    c = c | conds['out_of_band']
                lt = last_trigger(c) if (sw_v or sw_b) else None
                g_, p_, tu, n8 = pnl_exit(S, idx, val, Hh, F.COST, lt)
                rows.append(dict(
                    segment=a.segment, block='LX', account=nm, H=Hh, b=b,
                    budget='matchN', exit_veto=sw_v, exit_out_of_band=sw_b,
                    descriptor_id='LX|%s|H=%d|b=%d|v%d|o%d' % (nm, Hh, b,
                                                               int(sw_v), int(sw_b)),
                    gross_ann=G.ann(g_), net8_ann=G.ann(n8),
                    turn_mean=float(np.nanmean(tu)), pos_mean=float(np.nanmean(p_)),
                    target_n=float(tg.sum(axis=1).mean()),
                    trigger_frac=float(c[S.p0c].mean())))
        print('    LX %s 完成 %.0fs' % (nm, time.time() - t0), flush=True)

    df = pd.DataFrame(rows)
    n_inc = int((df.block == 'incumbent').sum())
    n_lx = int((df.block == 'LX').sum())
    df.to_csv(os.path.join(od, 'L_incumbent_lx_%s.csv' % a.segment), index=False)
    with open(os.path.join(od, 'L_exit_engine_anchor_%s.json' % a.segment), 'w') as fh:
        json.dump(dict(segment=a.segment, results=anch,
                       note='退出条件全假时 pnl_exit 必须复现 F.sparse_pnl_H '
                            '(浮点求和顺序不同, 按 1e-12 判)'), fh, indent=1,
                  ensure_ascii=False, default=str)
    print('  [%s] incumbent %d 行 (期望 %d) + LX %d 行 (期望 192), %.0fs'
          % (a.segment, n_inc, 7 * len(HS) * len(BS) * len(BUDGETS) * 2, n_lx,
             time.time() - t0))


if __name__ == '__main__':
    main()
