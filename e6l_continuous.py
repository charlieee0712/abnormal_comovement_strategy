# -*- coding: utf-8 -*-
"""E6l 连续面板（plan §5.6 / §9.3a BOUNDARY_CONT_PARENT_PAIR 72；brief §0.2）。四段封存后运行（后段须授权条件）。
对象：主展示 72（α .25 × H5）+ 各自原父 + Q0 NATIVE / Q0 HG10 / 同算子 C1 参照（同形态 α .25 × H5）。
两层：
  ① 记忆接续（同一套分段日评分与合法域上对照 reset 与 carry）：段 k+1 的第一个形成日 d_f 以段 k 末状态起步——G / U / last_confirmed
     按 ticker 重映射（plan §5.6"按显式 ID 重映射"），跨过段首预热（hold）；last 平移使段 k 末形成日对应 d_f − 1；INV 的最近 H 个形成日批次
     放入环位 (d_f − k) mod (H+1)；resume 走 e6l_ops 的 checkpoint 身份核验（next_day = d_f、next_date、列哈希）。NATIVE 配方无记忆（carry ≡ reset）。
  ② 连续账户：四段形成权重（各段 DEV，与账户同式）按 ticker 拼到全日历（3,940 个交易日）上，用拼接的 r0 / bench 算 H5 账本
     （numba 账本同 SparseEngine 式）：连续子（reset 名单 / carry 名单）与连续父；段首预热日沿上一段批次继续持有（不清仓）。
     段间 ticker 不在下一段列集者的收益按 0 计（记数披露）。
输出 results/full/continuous/：continuous_panel.csv（每对象 × 段：连续子 − 连续父 D、分段 D（账户）、carry − reset、边界 40 日窗口差）、
boundary_facts.csv（每段首接续：carry 与 reset 门差异格数、跨段 ticker 缺列数）；回执 continuous_panel。连续源因子全程重算不在本脚本（limit_register）。"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import time

import numpy as np
import pandas as pd

import e6l_core as L
import e6l_ops as O
import e6l_fast as FA
import e6l_registry as RG

H5 = 5


def first_formation(st):
    k = np.flatnonzero(st.dom.K > 0)
    return int(k[0]) if len(k) else None


def remap(prev_cols, new_cols, arr_prev, fill):
    """(1, Nc_prev) → (1, Nc_new) 按 ticker。"""
    pi = pd.Index(prev_cols).get_indexer(new_cols)
    out = np.full((1, len(new_cols)), fill, dtype=arr_prev.dtype)
    ok = pi >= 0
    out[0, ok] = arr_prev[0, pi[ok]]
    return out, int((~ok).sum())


def main():
    t0 = time.time()
    import e6l_seal as SEAL
    for pkg in ('deriv', 'post'):
        ok, bad = SEAL.verify(pkg)
        if not ok:
            raise RuntimeError('seal_%s 核对失败：%s' % (pkg, bad[:5]))
    for s in L.POST_SEGS:
        L.post_gate(s, 'continuous panel')
    import e6l_env as V
    D = L.read_csv_keep(L.P('registry', 'descriptors_E6l.csv'))
    P72 = D[D.primary72.astype(str) == 'True']
    refs = set()
    for r in P72.itertuples():
        refs.add(('Q0', r.mother, 0.25, 'NATIVE'))
        refs.add(('Q0', r.mother, 0.25, 'HG10'))
        refs.add(('C1', r.mother, 0.25, r.op))
    objs = sorted(set((r.meas, r.mother, 0.25, r.op) for r in P72.itertuples()) | refs)
    carry_state = {}                               # (meas, mother, op) → dict(cols, stt, F_tail)
    panel_w = {}                                   # key → list of (global day, ticker, w)
    rows_b = []
    seg_meta = []
    goff = 0
    r0_parts, bench_parts, cols_parts = [], [], []
    for pname in L.SEGMENTS:
        seg = V.SegL(pname)
        ci = seg.ci
        cols = list(seg.S.ccolnames)
        T = seg.T
        seg_meta.append((pname, goff, T))
        r0_parts.append(seg.SE.r0)
        bench_parts.append(seg.SE.bench)
        cols_parts.append(cols)
        tick = O.ids_hash(cols)
        dates = [str(x)[:10] for x in seg.dates]
        for (meas, mother, a, op) in objs + [('K0', m, 0.0, 'NATIVE') for m in sorted(set(x[1] for x in objs))]:
            st = seg.struct(mother)
            k0 = st.q0
            kf = None if meas == 'K0' else seg.meas_kf(meas)
            q = k0 if kf is None else np.where(np.isfinite(kf), (1 - a) * k0 + a * kf, k0)
            sc = st.gate_scores(q[None, :])
            U = st.gate_keep(sc)
            rule = O.parse_op(op)
            df_ = first_formation(st)
            key = (meas, mother, op)
            finals = {}
            for mode in ('reset', 'carry'):
                if rule['kind'] == 'NATIVE':
                    F = st.down(U)[0]
                    stt = None
                elif rule['kind'] == 'INV':
                    if mode == 'carry' and key in carry_state and df_ is not None:
                        prev = carry_state[key]
                        cnt = np.zeros((1, seg.Nc), np.int16)
                        ring = [[] for _ in range(H5 + 1)]
                        miss = 0
                        for k_, pcols in enumerate(prev['F_tail'][::-1], start=1):     # 上一段最后 H 个形成日（最近者 k=1）
                            pi = pd.Index(cols).get_indexer(pcols)
                            okc = pi[pi >= 0]
                            miss += int((pi < 0).sum())
                            if len(okc):
                                np.add.at(cnt, (np.zeros(len(okc), np.int64), okc), 1)
                                ring[(df_ - k_) % (H5 + 1)] = (np.zeros(len(okc), np.int64), okc)
                        state = dict(next_day=df_, next_date=dates[df_], ids=tick, H=H5, cnt=cnt, ring=ring)
                        G, Fm, stt, _ = O.inv_path(st, sc, U, rule['b'], H5, state=state, d0=df_)
                        rows_b.append(dict(segment=pname, meas=meas, mother=mother, op=op, carried_inventory_names=int(cnt.sum()), tickers_missing=miss))
                    else:
                        G, Fm, stt, _ = O.inv_path(st, sc, U, rule['b'], H5)
                    F = Fm[0]
                else:
                    bday = np.full(seg.T, rule.get('b', 10.0))
                    if mode == 'carry' and key in carry_state and df_ is not None:
                        prev = carry_state[key]
                        Gc, m1 = remap(prev['cols'], cols, prev['stt']['G'], False)
                        Uc, _ = remap(prev['cols'], cols, prev['stt']['U'], False)
                        lp = prev['stt']['last'].copy()
                        shift = df_ - prev['T']                                    # 上一段末形成日 → d_f − 1
                        lp = np.where(np.isfinite(lp), lp + shift, -np.inf)
                        lc, _ = remap(prev['cols'], cols, lp, -np.inf)
                        state = dict(next_day=df_, next_date=dates[df_], ids=tick, G=Gc, U=Uc, last=lc)
                        G, stt, _ = O.mem_gate(st, sc, U, rule, b_day=bday, state=state, d0=df_)
                        rows_b.append(dict(segment=pname, meas=meas, mother=mother, op=op, carried_gate_names=int(Gc.sum()), tickers_missing=m1))
                    else:
                        G, stt, _ = O.mem_gate(st, sc, U, rule, b_day=bday)
                    F = st.down(G)[0]
                finals[mode] = F
                if mode == 'carry':
                    tail = []
                    ts = np.flatnonzero(np.bincount(ci.t[F], minlength=T) > 0)
                    for d in ts[-H5:]:
                        a0, a1 = seg.off[d], seg.off[d + 1]
                        cells = np.arange(a0, a1)[F[a0:a1]]
                        tail.append([cols[c] for c in ci.c[cells]])
                    carry_state[key] = dict(cols=cols, stt=stt if stt is not None else {}, F_tail=tail, T=T)
            if rule['kind'] != 'NATIVE':
                rows_b.append(dict(segment=pname, meas=meas, mother=mother, op=op, carry_minus_reset_cells=int((finals['carry'] != finals['reset']).sum())))
            for mode, F in finals.items():
                ids = np.flatnonzero(F)
                t, c = ci.t[ids], ci.c[ids]
                w = seg.SE.dev(t, c)
                panel_w.setdefault((meas, mother, op, mode), []).append((t + goff, np.array([cols[x] for x in c]), w))
        goff += T
        print('%s 完成（%.0fs）' % (pname, time.time() - t0), flush=True)
    # 拼接全日历
    union = sorted(set().union(*[set(c) for c in cols_parts]))
    uix = {k: i for i, k in enumerate(union)}
    Tf = goff
    r0f = np.zeros((Tf, len(union)))
    for (pname, go, T), r0, cols in zip(seg_meta, r0_parts, cols_parts):
        r0f[go:go + T, [uix[c] for c in cols]] = r0
    benchf = np.concatenate(bench_parts)
    r0T = np.ascontiguousarray(r0f.T).ravel()
    Wd = np.zeros((H5 + 2, len(union)))
    led = {}
    for key, parts in panel_w.items():
        t = np.concatenate([p[0] for p in parts]).astype(np.int64)
        c = np.array([uix[x] for p in parts for x in p[1]], np.int64)
        w = np.concatenate([p[2] for p in parts])
        o = np.lexsort((c, t))
        out = np.empty((1, 4, Tf))
        FA.pnl_nb(t[o], c[o], w[o], np.array([H5], np.int64), Tf, r0T, benchf, 8e-4, Wd, out)
        led[key] = out[0, 3]
    rows = []
    for r in P72.itertuples():
        key_c = (r.meas, r.mother, r.op)
        par = led[('K0', r.mother, 'NATIVE', 'reset')]
        for (pname, go, T) in seg_meta:
            sl = slice(go, go + T)
            dc = led[key_c + ('carry',)][sl] - par[sl]
            dr = led[key_c + ('reset',)][sl] - par[sl]
            f = np.isfinite(dc) & np.isfinite(dr)
            bw = slice(go, go + min(T, 40))
            rows.append(dict(desc_id=r.desc_id, segment=pname, D_cont_carry_minus_cont_parent_ann_pp=float(np.mean(dc[f])) * L.ANN,
                             D_cont_reset_minus_cont_parent_ann_pp=float(np.mean(dr[f])) * L.ANN,
                             carry_minus_reset_ann_pp=float(np.mean((dc - dr)[f])) * L.ANN,
                             boundary40_carry_minus_parent_ann_pp=float(np.nanmean((led[key_c + ('carry',)] - par)[bw])) * L.ANN,
                             query_id='E6L-Q13-b'))
    P = pd.DataFrame(rows)
    od = L.P('results', 'full', 'continuous')
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, 'continuous_panel.csv')
    L.atomic_write_csv(p1, P)
    p2 = os.path.join(od, 'boundary_facts.csv')
    L.atomic_write_csv(p2, pd.DataFrame(rows_b))
    L.write_receipt(L.next_rerun('continuous_panel'), [p1, p2], 'SUCCEEDED', rows=len(P), union_tickers=len(union), days=Tf,
                    wall_s=round(time.time() - t0, 1))
    print('连续面板 %d 行；全日历 %d 日 × %d 票（%.0fs）' % (len(P), Tf, len(union), time.time() - t0), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
