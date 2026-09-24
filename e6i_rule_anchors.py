#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 2 算子恒等锚 (阻断; brief §2 "SLOT α=0 = 源父逐位 …… 同 m 核心对照精确复现原名单")。

每个推导段 x 母体 (R1/R2/A06/A08), 全部要求【逐位】等于 E6h ParentCtx:
  R0  rebuild() == P.B; veto_drop() == P.dr; (DEP) s1 == P.cand
  R1  SLOT α=0 短路 —— 传入一个"一调用就抛错"的新成员加载器, 证明不读新有效域
  R2  SLOT FULL_REPLACE α=1 且 z_new = 该腿自身 pct -> B (真恒等, 不涉浮点混合)
  R3  ADD_SCORE γ=0 / SWAP q=0 / SOFT λ=0 (乘性权重全 1) / RL keep_frac=1 -> B
  R4  FOCAL 每条否决腿: 'old' -> B; real_state(状态全真) -> B; real_state(全假) == 'none'
  R5  core_matchN(n = 当日 |B|) -> B (continuation ordering 与源 keep 同一并列规则)
  R6  DEP T 槽位 α=0 短路 (R1)
任一不过 -> 退出码 1 (MODULE STOP 级: 算子会凭空改动母体)。
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import time
import argparse

import numpy as np

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6i_ops as OP


def eq(a, b):
    return bool(np.array_equal(np.asarray(a, bool), np.asarray(b, bool)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    assert a.segment in I.DERIV_SEGS
    t0 = time.time()
    FE.build_catalog()
    I.set_protected_members(FE.protected_ids())
    S = I.seg_i(a.segment, warm=False)
    res = []

    def R(name, ok, **kw):
        res.append(dict(segment=a.segment, test=name, ok=bool(ok), **kw))

    def boom():
        raise AssertionError('α=0 却读取了新成员 (违反短路)')

    for mn in I.MOTHERS:
        M = OP.Mother(S, mn)
        B = M.B
        R('%s_R0_rebuild_B' % mn, eq(M.rebuild(), B), n_B=int(B.sum()))
        R('%s_R0_veto_drop' % mn, eq(M.veto_drop(), M.dr))
        if M.kind == 'dep':
            cand = np.asarray(M.P.cand, bool)
            R('%s_R0_dep_s1' % mn, eq(M.s1, cand))
        for leg in M.leg_roles:
            if M.kind == 'dep' and leg == 'T':
                B2, _ = M.slot_dep_T(None, 'high_bad', 0.0, 'FALLBACK')
                R('%s_R6_depT_alpha0' % mn, eq(B2, B))
                continue
            try:
                B2, info = M.slot(leg, boom, 0.0, 'FALLBACK')
                R('%s_R1_slot_%s_alpha0' % (mn, leg), eq(B2, B), note=info['note'])
            except AssertionError as e:
                R('%s_R1_slot_%s_alpha0' % (mn, leg), False, note=str(e))
            own = (M.legs[M.leg_roles.index(leg)] if M.kind != 'dep' else M.Px)
            B3, _ = M.slot(leg, lambda o=own: o, 1.0, 'FULL_REPLACE')
            R('%s_R2_slot_%s_fullreplace_self' % (mn, leg), eq(B3, B))
        z = M.score
        R('%s_R3_add_gamma0' % mn, eq(M.add_score(z, 0.0)[0], B))
        R('%s_R3_swap_q0' % mn, eq(M.swap(z, 0.0)[0], B))
        Bs, info = M.soft(z, 0.0)
        R('%s_R3_soft_lam0' % mn, eq(Bs, B) and bool(np.all(info['wmul'] == 1.0)))
        R('%s_R3_rl_off' % mn, eq(M.edge_replace(z, keep_frac=1.0)[0], B))
        for v in M.veto_legs:
            R('%s_R4_focal_%s_old' % (mn, v['name']), eq(M.focal(v['name'], 'old')[0], B))
            allT = np.ones_like(B)
            R('%s_R4_focal_%s_state_allTrue' % (mn, v['name']),
              eq(M.focal(v['name'], 'real_state', state=allT)[0], B))
            R('%s_R4_focal_%s_state_allFalse_eq_none' % (mn, v['name']),
              eq(M.focal(v['name'], 'real_state', state=~allT)[0], M.focal(v['name'], 'none')[0]))
        cm, restricted = M.core_matchN(B.sum(1))
        R('%s_R5_core_matchN_eq_B' % mn, eq(cm, B) and not restricted, restricted=restricted)
        print('  %s: %d/%d 过 (%.0fs)' % (mn, sum(r['ok'] for r in res if r['test'].startswith(mn)),
                                        sum(1 for r in res if r['test'].startswith(mn)),
                                        time.time() - t0), flush=True)
    out = dict(segment=a.segment, n=len(res), n_pass=sum(r['ok'] for r in res), results=res)
    I.atomic_write_json(os.path.join(I.RES, 'checks', 'rule_anchors_%s.json' % a.segment), out)
    bad = [r for r in res if not r['ok']]
    for r in bad:
        print('!!', r)
    print('算子锚 %d/%d (%.0fs)' % (out['n_pass'], out['n'], time.time() - t0))
    sys.exit(0 if not bad else 1)


if __name__ == '__main__':
    main()
