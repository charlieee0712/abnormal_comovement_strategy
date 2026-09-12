#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 新算子的恒等锚 (brief §2「新算子恒等锚(阻断)」+ plan §12.1 新增反例)。

每条都是【阻断】: 不过就不许用该算子跑经济格。
用法: python3 e6h_rule_anchors.py --segment 2010-2014
"""
from __future__ import annotations
import os
import sys
import json
import time
import argparse

import numpy as np

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_rules as RU
import e6g_core as G
import e6g_desc as GD
import e6f_core as F

RES = H.RES


def eq(a, b):
    return int((np.asarray(a, bool) != np.asarray(b, bool)).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', default='2010-2014')
    a = ap.parse_args()
    t0 = time.time()
    S = H.seg(a.segment, verbose=False)
    ctx = GD.GCtx(S)
    cols = S.ccolnames
    res = []

    def add(name, ok, note, **kw):
        res.append(dict(test=name, ok=bool(ok), level='ANCHOR', note=note, **kw))

    # ---- 取两个代表母体: A06 (三腿均值核) 与 R2 (两腿均值核 + 双否决) ----
    for pname in ('A06', 'R2'):
        cfg = GD.parse_cfg(G.DISPLAY_ID[pname])
        B0, sc0, cand0, C0 = ctx.full_mask_g(cfg)
        dr0 = ctx.build_veto_drop_g(cfg.get('veto'), cfg['core'], None, sel='SRC')
        V0 = C0 & (dr0 if dr0 is not None else np.zeros_like(C0))

        # --- SLOT identity ---
        for pol in ('FALLBACK', 'REPLACE'):
            m, _, _, note = RU.apply_slot(ctx, cfg, 1, 'TCV_20', 0.0, pol)
            add('SLOT_%s_alpha0_is_parent[%s]' % (pol, pname), eq(m, B0) == 0,
                'alpha=0 必须【短路】回源父, 不是近似', n_diff=eq(m, B0), shortcut=note)
        # alpha=1 两种政策必须【不同】(否则 FALLBACK 白分了)
        m1, _, _, _ = RU.apply_slot(ctx, cfg, 1, 'TCV_20', 1.0, 'FALLBACK')
        m2, _, _, _ = RU.apply_slot(ctx, cfg, 1, 'TCV_20', 1.0, 'REPLACE')
        add('SLOT_fallback_vs_replace_differ[%s]' % pname, eq(m1, m2) > 0,
            'alpha=1 时 FALLBACK 仍用旧测量补缺, REPLACE 不用 -> 必须不同',
            n_diff=eq(m1, m2))

        # --- FOCAL identity ---
        mo, _ = RU.apply_focal(ctx, cfg, 0, mode='original')
        add('FOCAL_original_is_parent[%s]' % pname, eq(mo, B0) == 0,
            'mode=original 必须逐位 = 源父', n_diff=eq(mo, B0))
        allT = np.ones_like(B0)
        me, _ = RU.apply_focal(ctx, cfg, 0, state=allT, mode='enable')
        add('FOCAL_enable_all_true_is_original[%s]' % pname, eq(me, mo) == 0,
            'state 全真的 enable = 原焦点否决', n_diff=eq(me, mo))
        allF = np.zeros_like(B0)
        mx, _ = RU.apply_focal(ctx, cfg, 0, state=allF, mode='exempt')
        add('FOCAL_exempt_all_false_is_original[%s]' % pname, eq(mx, mo) == 0,
            'state 全假的 exempt = 原焦点否决', n_diff=eq(mx, mo))
        mn, _ = RU.apply_focal(ctx, cfg, 0, mode='none')
        add('FOCAL_none_differs_and_is_superset[%s]' % pname,
            (eq(mn, mo) > 0) and bool((mo & ~mn).sum() == 0),
            '拆掉焦点否决后必须是原父的【超集】(少删一条腿只会多留票)',
            n_diff=eq(mn, mo), n_lost=int((mo & ~mn).sum()))
        # 伪 no-op 陷阱: 在原已全部否决的父上叠 state 不能得到假 no-op
        add('FOCAL_enable_is_subset_of_original_drop[%s]' % pname,
            bool((mo & ~me).sum() == 0),
            'enable 只会【少删】, 所以结果必须 ⊇ 原父', n=int((mo & ~me).sum()))

        # --- ADD / SWAP ---
        D0 = cand0 & np.isfinite(sc0) & (~C0)
        gs = H.get_pct_h(S, GD.spec_of_key('volume_ratio_3d'), 'NS', 'hi')
        m, A, note = RU.apply_add(B0, D0, gs, 0.0, cols)
        add('ADD_eta0_is_parent[%s]' % pname, eq(m, B0) == 0, 'eta=0 短路回 B',
            n_diff=eq(m, B0), shortcut=note)
        m, A, note = RU.apply_add(B0, D0, gs, 0.25, cols)
        add('ADD_keeps_parent[%s]' % pname, bool((B0 & ~m).sum() == 0),
            'ADD 只加不减: B ⊆ B\'', n_lost=int((B0 & ~m).sum()))
        add('ADD_does_not_bypass_veto[%s]' % pname, bool((A & V0).sum() == 0),
            '加回的票不得是源 veto 删掉的 (plan §12.1 反例)', n_bad=int((A & V0).sum()))
        add('ADD_budget_respected[%s]' % pname,
            bool(np.all(A.sum(axis=1) <= np.array(
                [RU.round_half_up(0.25 * n) for n in B0.sum(axis=1)]))),
            'A 的人数不得超过 m_cap = round_half_up(eta*|B|)')
        ms, A2, R2_, note = RU.apply_swap(B0, D0, gs, sc0, 0.0, cols)
        add('SWAP_eta0_is_parent[%s]' % pname, eq(ms, B0) == 0, 'eta=0 短路回 B',
            n_diff=eq(ms, B0), shortcut=note)
        ms, A2, R2_, note = RU.apply_swap(B0, D0, gs, sc0, 0.25, cols)
        add('SWAP_preserves_headcount[%s]' % pname,
            bool(np.array_equal(ms.sum(axis=1), B0.sum(axis=1))),
            'SWAP 必须人数不变 (但同人数 != 同仓位 != 同风险)',
            max_diff=int(np.abs(ms.sum(axis=1) - B0.sum(axis=1)).max()))
        add('SWAP_does_not_bypass_veto[%s]' % pname, bool((A2 & V0).sum() == 0),
            '换进来的票不得绕过源 veto', n_bad=int((A2 & V0).sum()))
        add('SWAP_removed_from_parent[%s]' % pname, bool((R2_ & ~B0).sum() == 0),
            '被换出的票必须来自 B', n_bad=int((R2_ & ~B0).sum()))

        # --- CONJ ---
        Jb = np.ones_like(C0)
        mc, _ = RU.apply_conj(C0, D0, Jb, V0)
        add('CONJ_all_bad_is_parent[%s]' % pname, eq(mc, B0) == 0,
            'Jbad 全真 -> 一个都不加回 -> 原父', n_diff=eq(mc, B0))
        Jb2 = (gs > 0.5)
        nid = RU.conj_identity_check(C0, D0, Jb2, V0)
        add('CONJ_unbounded_identity[%s]' % pname, nid == 0,
            "C' = C ∪ ((E\\C)\\Jbad) 恒等 (plan §4.2)", n_diff=nid)
        mc2, _ = RU.apply_conj(C0, D0, np.zeros_like(C0), V0)
        add('CONJ_none_bad_adds_all_D[%s]' % pname,
            bool(((D0 & ~V0) & ~mc2).sum() == 0),
            'Jbad 全假 -> 全部合法经济拒绝票加回 (但仍过 V)',
            n_missing=int(((D0 & ~V0) & ~mc2).sum()))

        # --- MARGIN ---
        liq = H.get_pct_h(S, GD.spec_of_key('amihud_daily'), 'NS', 'hi')
        legal = S.p0c & (~(dr0 if dr0 is not None else np.zeros_like(C0)))
        mm, note = RU.apply_margin(B0, sc0, liq, 0.0, cols, legal)
        add('MARGIN_e0_is_parent[%s]' % pname, eq(mm, B0) == 0, 'e=0 短路回 B',
            n_diff=eq(mm, B0), shortcut=note)
        mm, note = RU.apply_margin(B0, sc0, liq, 0.25, cols, legal)
        dd = int(np.abs(mm.sum(axis=1) - B0.sum(axis=1)).max())
        add('MARGIN_preserves_headcount[%s]' % pname, dd == 0,
            'MARGIN 补回父原人数', max_diff=dd)
        add('MARGIN_all_legal[%s]' % pname, bool((mm & ~legal).sum() == 0),
            'MARGIN 换进来的票必须仍过原 veto', n_bad=int((mm & ~legal).sum()))

        # --- 软降权 ---
        bad = (liq > 0.9)
        m0, w0, note = RU.apply_soft(B0, bad, 0.0)
        add('SOFT_lam0_is_parent[%s]' % pname,
            (eq(m0, B0) == 0) and bool(np.all(w0 == 1.0)), 'lambda=0 -> 原父',
            n_diff=eq(m0, B0), shortcut=note)
        m1_, w1, _ = RU.apply_soft(B0, bad, 1.0)
        pnl_soft = RU.run_mask(S, m1_, w1)
        pnl_del = RU.run_mask(S, B0 & ~bad)
        d = float(np.nanmax(np.abs(np.asarray(pnl_soft[0]) - np.asarray(pnl_del[0]))))
        add('SOFT_lam1_differs_from_delete_and_redev[%s]' % pname, d > 1e-12,
            'lambda=1 是冻权删票(释放资本留现金), 与删除后重算 DEV 的硬端点【不同】',
            max_gross_diff=d)

    n_ok = sum(1 for x in res if x['ok'])
    out = dict(round='E6h', segment=a.segment, kind='rule_operator_identity',
               written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
               n_total=len(res), n_pass=n_ok, elapsed_s=round(time.time() - t0, 1),
               results=res)
    os.makedirs(os.path.join(RES, 'checks'), exist_ok=True)
    with open(os.path.join(RES, 'checks', 'rule_anchors_%s.json' % a.segment), 'w') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False, default=str)
    print('== E6h 新算子恒等锚 @ %s ==  %d/%d' % (a.segment, n_ok, len(res)))
    for x in res:
        print('  %s%-48s %s' % ('OK  ' if x['ok'] else '!!  ', x['test'],
                                '' if x['ok'] else x['note']))
        if not x['ok']:
            print('       %s' % {k: v for k, v in x.items()
                                 if k not in ('test', 'ok', 'level', 'note')})
    if n_ok != len(res):
        raise SystemExit('算子恒等锚未全过 —— 按 brief §2 这是阻断项')


if __name__ == '__main__':
    main()
