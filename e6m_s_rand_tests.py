# -*- coding: utf-8 -*-
"""E6m 随机层（e6m_s_rand）在 mock 上的名单层测试：真实内容恒等、各机制守恒量、路径确定性。不读任何收益。
输出 stageS_dev/rand_tests_<段>.csv 与回执。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_ops as O
import e6m_s_ops as S
import e6m_s_rand as RN
import e6m_s_mock as MK
import e6m_s_meas as ME
import e6m_b3_tools as BT

ROWS = []


def put(seg, form, test, ok, **kw):
    ROWS.append(dict(segment=seg, form=form, test=test, status='PASS' if ok else 'FAIL', **{k: str(v) for k, v in kw.items()}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', default='2024-2026')
    ap.add_argument('--paths', type=int, default=4)
    a = ap.parse_args()
    t0 = time.time()
    seg = MK.MockSeg(a.seg)
    me = ME.load(a.seg)
    cal = np.load(M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), allow_pickle=False)['dates']
    paths = list(range(a.paths))
    ind = seg.ctx['industry'].reindex_like(seg.pool0).to_numpy(float)[:, seg.ccols]
    ind_c = np.where(np.isfinite(ind), ind, -1).astype(np.int64)
    k0_c = MK.dict_dense(seg.ctx['pcond'], seg.pool0)[:, seg.ccols]
    for form in ('M_union3_v2', 'M_mean3_v2'):
        st = seg.struct(form)
        ctx = S.Ctx(st, me['kQ0'])
        ctx._cal = cal
        owner = 'TEST|%s' % form
        day = seg.ci.t[ctx.ids]
        real = np.repeat(ctx.kq[None, :], len(paths), axis=0)
        # 1 替身内容：当日多重集守恒、缺失不动、确定性、路径不同
        KQ = RN.standin_content(ctx, paths, 'LEGACY_POLICY_RANDOM', owner, form)
        ms_ok = all(np.array_equal(np.sort(KQ[i, day == d][np.isfinite(KQ[i, day == d])]), np.sort(ctx.kq[day == d][np.isfinite(ctx.kq[day == d])]))
                    for i in range(len(paths)) for d in np.unique(day)[:50])
        miss_ok = bool((np.isfinite(KQ) == np.isfinite(ctx.kq)[None, :]).all())
        det_ok = np.array_equal(KQ, RN.standin_content(ctx, paths, 'LEGACY_POLICY_RANDOM', owner, form))
        put(a.seg, form, 'standin_content_invariants', ms_ok and miss_ok and det_ok and not np.array_equal(KQ[0], KQ[1]))
        # 2 真实内容恒等：逐路径 BAND / PRIORITY / HARD / SOURCE = 逐日版
        for w in (0.1, 0.2):
            gn, gm = RN.band_paths(ctx, real, w, memory='PROTECTED_LAG10')
            rn, rm, _ = S.band_gates(ctx, w, None, 'PROTECTED_LAG10')
            put(a.seg, form, 'band_paths_real_identity_w%.1f' % w, bool((gn == rn).all() and (gm == rm).all()))
            gn, gm = RN.band_paths(ctx, real, w, alpha=0.25, memory='PROTECTED_LAG10')
            rn, rm, _ = S.band_gates(ctx, w, 0.25, 'PROTECTED_LAG10')
            put(a.seg, form, 'band_blend_paths_real_identity_w%.1f' % w, bool((gn == rn).all() and (gm == rm).all()))
        gp = RN.priority_paths(ctx, real[:2], 0.8, 'RULE_LAG10')
        rp = S.priority_gates(ctx, 0.8, 'RULE_LAG10')[1]
        put(a.seg, form, 'priority_paths_real_identity', bool((gp == rp).all()))
        gh = RN.hard_paths(ctx, real, 0.5, 'RULE_LAG10')
        rh = S.hard_gates(ctx, 0.5, 'RULE_LAG10')[0]
        put(a.seg, form, 'hard_paths_real_identity', bool((gh == rh).all()))
        gs = RN.source_paths(ctx, real[:2], 0.25, 'HG10')
        rs = S.source_gate(ctx, 0.25, 'HG10')[0]
        put(a.seg, form, 'source_paths_real_identity', bool((gs == rs).all()))
        # 3 R-BAND：B 外不动、B 内多重集守恒、门人数 = K
        KB = RN.r_band_content(ctx, paths, owner, form, 0.1)
        okB = True
        for d, s_, e, K in ctx.days[:200]:
            o = ctx.orders[d]
            A, B, C, j = O.band_parts(o, K, 0.1)
            outB = np.setdiff1d(np.arange(e - s_), B)
            for i in range(len(paths)):
                okB &= np.array_equal(KB[i, s_ + outB], ctx.kq[s_ + outB], equal_nan=True)
                x, y = KB[i, s_ + B], ctx.kq[s_ + B]
                okB &= np.array_equal(np.sort(x[np.isfinite(x)]), np.sort(y[np.isfinite(y)]))
        Gb = RN.band_paths(ctx, KB, 0.1)[0]
        cnt_ok = all(int(Gb[i, s_:e].sum()) == K for i in range(len(paths)) for d, s_, e, K in ctx.days)
        put(a.seg, form, 'r_band_invariants', bool(okB and cnt_ok))
        # 4 R-FILTER：PASS 数守恒、缺失不动
        KF = RN.r_filter_content(ctx, paths, owner, form)
        ok4 = all(int(np.sum(KF[i, s_:e][np.isfinite(KF[i, s_:e])] <= 0.8)) == int(np.sum(ctx.kq[s_:e][np.isfinite(ctx.kq[s_:e])] <= 0.8))
                  for i in range(len(paths)) for d, s_, e, K in ctx.days)
        put(a.seg, form, 'r_filter_pass_count', bool(ok4 and (np.isfinite(KF) == np.isfinite(ctx.kq)[None, :]).all()))
        # 5 删除预算（HARD c .5）：同层同数、只删候选
        G_h, f = S.hard_gates(ctx, 0.5)
        pre = np.zeros(seg.n, bool)
        pre[ctx.ids] = ctx.U0
        dele = np.zeros(seg.n, bool)
        dele[ctx.ids] = ctx.U0 & ~G_h
        fin = np.zeros(seg.n, bool)
        fin[ctx.ids] = np.isfinite(ctx.kq)
        sz = BT.activity_terciles(seg.cells(seg.ctx['log_mcap'].reindex_like(seg.pool0).to_numpy(float)), np.ones(seg.n, bool))
        szc = np.array([{'LOW': 0, 'MID': 1, 'HIGH': 2}.get(s, 3) for s in sz], np.int64)
        grp = (ind_c[seg.ci.t, seg.ci.c] + 1) * 4 + szc                                  # 确定性分层键（不用内置 hash）
        K_ = RN.Keys(seg, cal)
        Dg = RN.delete_budget(seg, K_, pre, dele, grp, fin, owner, form, paths)
        ok5 = True
        for i in range(len(paths)):
            rd = pre & ~Dg[i]
            ok5 &= bool((rd & ~(pre & fin)).sum() == 0)
            for d in range(0, seg.T, 7):
                a0, a1 = int(seg.off[d]), int(seg.off[d + 1])
                x = pd.Series(grp[a0:a1][rd[a0:a1]]).value_counts().sort_index()
                y = pd.Series(grp[a0:a1][dele[a0:a1]]).value_counts().sort_index()
                ok5 &= x.equals(y)
        put(a.seg, form, 'delete_budget_same_layer_counts', ok5)
        # 6 R-EDIT：换出 / 换入对数 = 真实 J*（无 shortfall 时）；FIXED_OUT 保留真实换出
        for which in ('LOCAL', 'GLOBAL'):
            for mode in ('FIXED_OUT', 'BOTH_RANDOM'):
                Ge, fe = RN.r_edit(ctx, paths[:2], owner, form, 0.25, 0.1, which, mode, ind_c, k0_c)
                r_, _ = S.edit_gates(ctx, 0.25, 0.1)
                real_g = r_[which]
                ok6 = True
                for i in range(2):
                    ok6 &= int((Ge[i] & ~ctx.U0).sum()) == int((real_g & ~ctx.U0).sum())
                    ok6 &= int((ctx.U0 & ~Ge[i]).sum()) == int((ctx.U0 & ~real_g).sum())
                    if mode == 'FIXED_OUT':
                        ok6 &= bool(((ctx.U0 & ~real_g) == (ctx.U0 & ~Ge[i])).all())
                put(a.seg, form, 'r_edit_%s_%s' % (which, mode), ok6 or fe['shortfall'] > 0, J_star=fe['J_star'], shortfall=fe['shortfall'])
        # 7 R-MEMORY-HG（SOURCE Q0 HG10）：每日标记数 = 本路径昨日实际 G 在门域的格数；与真实 HG 不同
        sc = st.gate_scores(S.native_q(ctx.q0, me['kQ0'], 0.25)[None, :])[0]
        U = st.gate_keep(sc[None, :])[0]
        be = 10.0 * st.bunit

        def sel(d, s_, e, K, o, mark):
            return S.select_rows((sc[s_:e] - be * mark)[None, :], K)[0]
        Gm = RN.r_memory(ctx, paths[:2], owner, form, 'HG', lambda d, s_, e, K, o: U[s_:e], sel, lambda d, s_, e, K, o: np.zeros(e - s_, np.int64))
        cnt7 = all(int(Gm[i, s_:e].sum()) == K for i in range(2) for d, s_, e, K in ctx.days)
        hg = S.source_gate(ctx, 0.25, 'HG10')[0]
        put(a.seg, form, 'r_memory_hg_counts', bool(cnt7 and not (Gm[0] == hg).all()))
    df = pd.DataFrame(ROWS)
    p = M.P('stageS_dev', 'rand_tests_%s.csv' % a.seg)
    M.atomic_write_csv(p, df)
    ok = bool((df.status == 'PASS').all())
    M.write_receipt(os.environ.get('E6M_TASK', 'S_dev_rand_tests_%s' % a.seg), [p], status='SUCCEEDED' if ok else 'FAILED',
                    code=[__file__, RN.__file__, M.__file__], wall_s=round(time.time() - t0, 1), note='B2：随机层名单测试（不读收益）')
    print(df.drop(columns=['segment']).to_string(index=False), flush=True)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
