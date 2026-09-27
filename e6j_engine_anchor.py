# -*- coding: utf-8 -*-
"""E6j 批量引擎的阻断锚（e6j_engine 头注）：锚不过，引擎不许用于任何账户。逐段一个进程（--segment），--merge 汇总。
四段：母体恒等（掩码 / DEV / 8bp H5 账本对生产）+ 研究母体恒等；推导段另加：S / M / C1 × α 与生产 arm_masks、SM 与生产 blend_q、
研究母体 K 槽位与 E6i Mother.slot、R1 T 槽位与 E6i slot_dep_T 的逐格比对，以及非 H5 母体账本对生产。只比掩码 / 权重 / 母体账本。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob
import time

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_prod as P
import e6j_slot as SL
import e6j_engine as EN
import comprehensive_factor_diagnosis as C

RERUN = '--rerun' in sys.argv
TASK = 'engine_anchor' + ('_rerun' if RERUN else '')
OUT = os.path.join(J.RES, 'checks', 'engine_anchor_rerun' if RERUN else 'engine_anchor')
ARMS = {'S': ('K_rar20', 'lo'), 'M': ('K_slope20', 'lo'), 'C1': ('K_MA3_E6F', 'hi')}


def run(pname):
    t0 = time.time()
    rows = []

    def chk(cid, obj, metric, got, ok, note=''):
        rows.append(dict(segment=pname, check_id=cid, object=obj, metric=metric, got=got, status='PASS' if ok else 'FAIL', note=note))

    env = EN.Env(pname, with_prod=True)
    ctx, ci = env.ctx, env.ci
    mothers = P.form_masks(ctx)
    led = pd.read_parquet(os.path.join(J.RES, 'anchors', 'mother_ledger_prod_v2.parquet'))
    deriv = pname in J.DERIV_SEGS
    for form in P.DELIV:
        st = EN.prod_structure(env, form)
        k = st.kept(st.q0[None, :])[0]
        ref = ci.of(mothers[form][:, env.S.ccols])
        chk('E1', form, '结构 kept(q0) vs 生产母体掩码（不同格数）', int((k != ref).sum()), bool((k == ref).all()))
        t, c = ci.t[k], ci.c[k]
        w = env.SE.dev(t, c)
        _, Wp = P.weights_of(ctx, mothers[form])
        wref = Wp.values[:, env.S.ccols][t, c]
        tot_ref = float(Wp.values.sum())
        dmax = float(np.max(np.abs(w - wref))) if len(w) else 0.0
        chk('E2', form, 'DEV 权重 vs 生产 assign_weights_dev（最大差；浮点求和序容差 1e−15，锚 2 L2 同）', dmax,
            dmax <= 1e-15 and abs(float(w.sum()) - tot_ref) <= 1e-9, '逐位相同占比 %.6f' % (float((w == wref).mean()) if len(w) else 1.0))
        g, pos, turn, net = env.SE.pnl(t, c, w, (5,), 8.0)[5]
        L = led[(led.period == pname) & (led.cfg == form)]
        for lab, a, b in (('gross', g, L.gross_excess.values), ('pos', pos, L.daily_position.values), ('turn', turn, L.daily_turnover.values),
                          ('net8', net, L.net8.values)):
            f = np.isfinite(a) & np.isfinite(b)
            d = float(np.max(np.abs(a[f] - b[f]))) if f.any() else 0.0
            chk('E3', form, 'H5 8bp 日账本 %s vs 生产（最大差）' % lab, d, d <= 1e-12 and bool((np.isfinite(a) == np.isfinite(b)).all()))
        if deriv and form == 'A4b_CVRv5':
            for H in (3, 10, 20):
                pr = C.compute_calendar_pnl(Wp, ctx['data'], ctx['clean'], hold_days=H, cost_bp_bilateral=8.0)
                n2 = env.SE.pnl(t, c, w, (H,), 8.0)[H][3]
                b = pr['net_excess_daily'].values
                f = np.isfinite(n2) & np.isfinite(b)
                d = float(np.max(np.abs(n2[f] - b[f])))
                chk('E3H', form, 'H%d 8bp net 日账本 vs 生产 compute_calendar_pnl' % H, d, d <= 1e-12)
    # 研究母体恒等
    for mn in ('R1', 'R2', 'A06'):
        M = env.R.mother(mn)
        for slot in ('K', 'T'):
            st = EN.research_structure(env, mn, slot)
            k = st.kept(st.q0[None, :])[0]
            chk('E6', '%s:%s' % (mn, slot), '研究结构 kept(q0) vs E6i 母体 B（不同格数）', int((k != M.B_c).sum()), bool((k == M.B_c).all()))
    M8 = env.R.mother('A08')
    st = EN.research_structure(env, 'A08', 'T')
    k = st.kept(st.q0[None, :])[0]
    chk('E6', 'A08:T', '研究结构 kept(q0) vs E6i 母体 B（不同格数）', int((k != M8.B_c).sum()), bool((k == M8.B_c).all()))
    if deriv:
        mem = {arm: SL.member_pct(ctx, mid, d)[0] for arm, (mid, d) in ARMS.items()}
        memc = {arm: env._dense_cells(pc) for arm, pc in mem.items()}
        for form in P.DELIV:
            st = EN.prod_structure(env, form)
            for arm in ('S', 'M', 'C1'):
                for a in (0.125, 0.25, 0.5):
                    k = st.kept(EN.blend(st.q0, [(1.0, memc[arm][None, :])], a))[0]
                    ref = ci.of(SL.arm_masks(ctx, arm, a, mem)[form][:, env.S.ccols])
                    chk('E4', '%s|%s|a=%s' % (form, arm, a), '引擎 vs 生产 arm_masks（不同格数）', int((k != ref).sum()), bool((k == ref).all()))
            k = st.kept(EN.blend(st.q0, [(0.5, memc['S'][None, :]), (0.5, memc['M'][None, :])], 0.25))[0]
            ref = ci.of(SL.arm_masks(ctx, 'SM', 0.25, mem)[form][:, env.S.ccols])
            chk('E5', '%s|SM|a=0.25' % form, '引擎 SM vs 生产 blend_q（不同格数）', int((k != ref).sum()), bool((k == ref).all()))
            kk = st.kept(np.repeat(EN.blend(st.q0, [(1.0, memc['S'][None, :])], 0.25), 4, axis=0))
            chk('E9', form, '批内 4 条相同 q → 4 行 kept 相同', bool((kk == kk[0]).all()), bool((kk == kk[0]).all()))
        import e6i_ops as O
        S = env.S
        for mn in ('R2', 'A06'):
            M = env.R.mother(mn)
            st = EN.research_structure(env, mn, 'K')
            z = O._dirpct(S, 'K_rar20', 'low_bad')
            k = st.kept(EN.blend(st.q0, [(1.0, env.cells_of_dense(z)[None, :])], 0.25))[0]
            B2, _ = M.slot('K', lambda: z, 0.25, 'FALLBACK')
            ref = ci.of(B2)
            chk('E7', '%s:K|K_rar20|low_bad|a=0.25' % mn, '引擎 vs E6i Mother.slot（不同格数）', int((k != ref).sum()), bool((k == ref).all()))
        M1 = env.R.mother('R1')
        import e6i_s1base as SB
        raw = SB.raw_member(S, 'T_ewcv20')
        znew = O._ns_pct_within(S, raw, M1.s1, 'hi')
        st = EN.research_structure(env, 'R1', 'T')
        k = st.kept(EN.blend(st.q0, [(1.0, env.cells_of_dense(znew)[None, :])], 0.25))[0]
        B2, _ = M1.slot_dep_T(raw, 'high_bad', 0.25, 'FALLBACK')
        ref = ci.of(B2)
        chk('E8', 'R1:T|T_ewcv20|high_bad|a=0.25', '引擎 vs E6i slot_dep_T（不同格数）', int((k != ref).sum()), bool((k == ref).all()))
    res = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    J.atomic_write_csv(os.path.join(OUT, 'part_%s.csv' % pname), res)
    J.log('%s engine anchor %d checks FAIL=%d %.0fs' % (pname, len(res), int((res.status == 'FAIL').sum()), time.time() - t0),
          os.path.join(J.RES, 'logs', 'engine_anchor_%s.log' % pname))
    return 0


def merge():
    parts = sorted(glob.glob(os.path.join(OUT, 'part_*.csv')))
    res = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)
    p = os.path.join(OUT, 'engine_anchor_results.csv'); J.atomic_write_csv(p, res)
    ok = bool((res.status == 'PASS').all()) and res.segment.nunique() == 4
    J.write_receipt(TASK, [p], 'SUCCEEDED' if ok else 'FAILED', n_checks=len(res), n_fail=int((res.status == 'FAIL').sum()),
                    src_sha256={f: J.sha_file(os.path.join(J.CODE, f)) for f in ('e6j_engine.py', 'e6j_engine_anchor.py')}, blocker=not ok)
    print(res.groupby(['check_id', 'status']).size(), flush=True)
    print(res[res.status == 'FAIL'].to_string()[:3000], flush=True)
    return 0 if ok else 2


if __name__ == '__main__':
    if '--merge' in sys.argv:
        sys.exit(merge())
    sys.exit(run(sys.argv[sys.argv.index('--segment') + 1]))
