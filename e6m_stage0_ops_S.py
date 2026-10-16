# -*- coding: utf-8 -*-
"""E6m Stage 0 第 3 类：新算子在真实数据上的恒等端点（brief §2 第 3 类；附录 A3）。只比较门 / 名单，不读任何收益。
B2 开发期在 e6m_s_mock 上跑（--struct mock）；阶段 S 原样换成真实 e6k_env.Struct（--struct real，届时接入）再跑一次。
每条写 which_switch_is_off / comparator，差异计数为格数（门域坐标）。"""
import e6j_boot  # noqa: F401
import os
import sys
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_s_ops as S
import e6m_s_meas as ME

FORMS = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
ROWS = []


def put(seg, form, item, switch, comparator, diff, n_days=None, note='', expect_zero=True):
    ROWS.append(dict(segment=seg, form=form, item=item, which_switch_is_off=switch, comparator=comparator, diff_cells=int(diff),
                     diff_days=n_days if n_days is not None else '', status=('PASS' if diff == 0 else 'FAIL') if expect_zero else 'INFO', note=note))


def diff_days(ctx, A, B):
    return int(sum(int((A[a:e] != B[a:e]).any()) for d, a, e, K in ctx.days))


def counts_ok(ctx, G, rule):
    bad = 0
    for d, a, e, K in ctx.days:
        k = int(G[a:e].sum())
        bad += int(k != K) if rule == 'eq' else int(k > K)
    return bad


def run(seg_name, struct_kind):
    if struct_kind != 'mock':
        raise NotImplementedError('真实 Struct 在阶段 S 接入')
    import e6m_s_mock as MK
    seg = MK.MockSeg(seg_name)
    me = ME.load(seg_name)
    if not (np.array_equal(me['t'], seg.ci.t) and np.array_equal(me['c'], seg.ci.c)):
        raise RuntimeError('测量单元坐标与 mock 不一致')
    kq0 = me['kQ0']
    for form in FORMS:
        st = seg.struct(form)
        ctx = S.Ctx(st, kq0)
        U0 = ctx.U0
        # 1 BAND_Q w = 0 ≡ U0；BAND_BLEND α = 0 ≡ U0（各 w）
        g = S.band_gates(ctx, 0.0)[0]
        put(seg_name, form, 'BAND_Q_w0', 'w = 0', 'U0', (g != U0).sum(), diff_days(ctx, g, U0))
        for w in (0.10, 0.20):
            g = S.band_gates(ctx, w, alpha=0.0)[0]
            put(seg_name, form, 'BAND_BLEND_a0_w%.2f' % w, 'α = 0', 'U0', (g != U0).sum(), diff_days(ctx, g, U0))
        # 2 b = 0：PROTECTED / NATIVE_METRIC / UNPROTECTED 记忆版 ≡ 各自无记忆
        old = S.B_MEM
        S.B_MEM = 0.0
        try:
            for w in (0.10, 0.20):
                gn, gm, _ = S.band_gates(ctx, w, memory='PROTECTED_LAG10')
                put(seg_name, form, 'BAND_Q_PROTECTED_b0_w%.2f' % w, 'b = 0', 'BAND_Q 无记忆', (gn != gm).sum(), diff_days(ctx, gn, gm))
                gn, gm, _ = S.band_gates(ctx, w, alpha=0.25, memory='PROTECTED_LAG10', metric=True)
                put(seg_name, form, 'NATIVE_METRIC_b0_w%.2f' % w, 'b = 0', 'BAND_BLEND α.25 无记忆', (gn != gm).sum(), diff_days(ctx, gn, gm))
                gn, gm, f = S.band_gates(ctx, w, memory='UNPROTECTED_LAG10')
                put(seg_name, form, 'UNPROTECTED_b0_w%.2f' % w, 'b = 0', 'BAND_Q 无记忆', (gn != gm).sum(), diff_days(ctx, gn, gm),
                    note='outside_band_edits=%d' % f['mem'].get('outside_band_edits', 0))
            gn, gm, _ = S.priority_gates(ctx, 0.8, memory='RULE_LAG10')
            put(seg_name, form, 'PRIORITY_RULE_LAG_b0_c0.8', 'b = 0', 'PRIORITY 无记忆', (gn != gm).sum(), diff_days(ctx, gn, gm))
        finally:
            S.B_MEM = old
        # 3 PRIORITY c = 1 ≡ U0；RULE_LAG10 c = 1 ≡ OLD_LAG（附录 A3-6）
        gn, gm, _ = S.priority_gates(ctx, 1.0, memory='RULE_LAG10')
        put(seg_name, form, 'PRIORITY_c1', 'c = 1', 'U0', (gn != U0).sum(), diff_days(ctx, gn, U0))
        old_lag = S.source_gate(S._OldCtx(ctx), 0.0, 'LAG1_10')[0]
        if st.kind != 'mean':
            put(seg_name, form, 'PRIORITY_RULE_LAG_c1', 'c = 1', 'OLD_LAG（源 LAG1_10 旧核心）', (gm != old_lag).sum(), diff_days(ctx, gm, old_lag))
        else:
            third = np.zeros(len(ctx.ids), bool)                # 当日门域全部 K_loading = 1/3 的日子
            for d, a, e, K in ctx.days:
                third[a:e] = bool(np.all(np.abs(ctx.load[a:e] - 1.0 / 3.0) <= 1e-12))
            dd = (gm != old_lag)
            put(seg_name, form, 'PRIORITY_RULE_LAG_c1_kload_third_days', 'c = 1（只看全门域 K_loading = 1/3 的日子）', 'OLD_LAG',
                (dd & third).sum(), diff_days(ctx, np.where(third, gm, False), np.where(third, old_lag, False)))
            put(seg_name, form, 'PRIORITY_RULE_LAG_c1_other_days', 'c = 1（含 K_loading ≠ 1/3 的日子）', 'OLD_LAG', (dd & ~third).sum(),
                note='plan §5.3a / §5.4：新算子 bonus = .10·K_loading_i，源 = b·bunit（1/300）；口径差异，见 STAGE_S_IMPL_PLAN §2',
                expect_zero=False)
        # 4 HARD c = 1 ≡ U0 / ≡ OLD_LAG
        g = S.hard_gates(ctx, 1.0)[0]
        put(seg_name, form, 'HARD_c1', 'c = 1', 'U0', (g != U0).sum(), diff_days(ctx, g, U0))
        g = S.hard_gates(ctx, 1.0, memory='RULE_LAG10')[0]
        put(seg_name, form, 'HARD_RULE_LAG_c1', 'c = 1', 'OLD_LAG', (g != old_lag).sum(), diff_days(ctx, g, old_lag))
        # 5 EDIT：w = 0 → J* = 0 → 三式 ≡ U0
        r, f = S.edit_gates(ctx, 0.25, 0.0)
        for k, g in r.items():
            put(seg_name, form, 'EDIT_%s_w0' % k, 'w = 0（J* = 0）', 'U0', (g != U0).sum(), diff_days(ctx, g, U0), note='J*=%d' % f['J_star'])
        # 6 COPY 端点
        for w in (0.10, 0.20):
            g = S.band_gates(ctx, w, copy=True)[0]
            put(seg_name, form, 'COPY_BAND_Q_w%.2f' % w, 'COPY 坐标', 'U0', (g != U0).sum(), diff_days(ctx, g, U0))
            g = S.band_gates(ctx, w, alpha=0.25, copy=True)[0]
            put(seg_name, form, 'COPY_BAND_BLEND_w%.2f' % w, 'COPY = s0', 'U0', (g != U0).sum(), diff_days(ctx, g, U0))
        g = S.priority_gates(ctx, 0.8, copy=True)[0]
        put(seg_name, form, 'COPY_PASS_c0.8', 'COPY 坐标', 'U0', (g != U0).sum(), diff_days(ctx, g, U0))
        g = S.hard_gates(ctx, 1.0, copy=True)[0]
        put(seg_name, form, 'COPY_HARD_c1', 'c = 1', 'U0', (g != U0).sum(), diff_days(ctx, g, U0))
        # 7 SOURCE α = 0 ≡ U0
        g = S.source_gate(ctx, 0.0)[0]
        put(seg_name, form, 'SOURCE_NATIVE_a0', 'α = 0', 'U0', (g != U0).sum(), diff_days(ctx, g, U0))
        # 8 名额守恒（真实参数）
        for w in (0.10, 0.20):
            g = S.band_gates(ctx, w, alpha=0.25, memory='PROTECTED_LAG10')
            put(seg_name, form, 'BAND_BLEND_count_w%.2f' % w, '—', '每日人数 = K', counts_ok(ctx, g[0], 'eq') + counts_ok(ctx, g[1], 'eq'))
        g = S.priority_gates(ctx, 0.5, memory='RULE_LAG10')
        put(seg_name, form, 'PRIORITY_count_c0.5', '—', '每日人数 = K', counts_ok(ctx, g[0], 'eq') + counts_ok(ctx, g[1], 'eq'))
        g = S.hard_gates(ctx, 0.5)[0]
        put(seg_name, form, 'HARD_count_c0.5', '—', '每日人数 ≤ K', counts_ok(ctx, g, 'le'))
        r, f = S.edit_gates(ctx, 0.25, 0.10)
        put(seg_name, form, 'EDIT_count_w0.10', '—', '每日人数 = K', sum(counts_ok(ctx, g, 'eq') for g in r.values()), note='J=%d J*=%d' % (f['J'], f['J_star']))
        # 9 K 槽位桥 w = 0 ≡ U0（只 Mmean）
        if st.kind == 'mean':
            g = S.slot_bridge_gate(ctx, 0.0, 'SLOT_Q')[0]
            put(seg_name, form, 'K_SLOT_w0', 'w = 0', 'U0', (g != U0).sum(), diff_days(ctx, g, U0))
        # 10 最终名单：down(U0) = kept(q0)
        if form in ('A4b_CVRv5', 'M_union3_v2', 'M_mean3_v2'):
            f1 = st.down(U0[None, :])[0]
            f0 = st.kept(st.q0[None, :])[0]
            put(seg_name, form, 'DOWN_U0_equals_parent', '—', 'kept(q0)', (f1 != f0).sum())
    df = pd.DataFrame(ROWS)
    p = M.P('stageS_dev', 'stage0_ops_mock_%s.csv' % seg_name)
    M.atomic_write_csv(p, df)
    ok = bool((df.status != 'FAIL').all())
    M.write_receipt(os.environ.get('E6M_TASK', 'S_dev_stage0_ops_%s' % seg_name), [p], status='SUCCEEDED' if ok else 'FAILED',
                    code=[__file__, S.__file__, M.__file__], note='B2 开发：mock 上的真实数据恒等端点（不读收益）')
    print(df.groupby(['item', 'status']).size().unstack(fill_value=0).to_string(), flush=True)
    bad = df[df.status != 'PASS']
    if len(bad):
        print(bad.drop(columns=['segment']).to_string(index=False), flush=True)
    return 0 if ok else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--struct', default='mock', choices=['mock', 'real'])
    a = ap.parse_args()
    sys.exit(run(a.seg, a.struct))
