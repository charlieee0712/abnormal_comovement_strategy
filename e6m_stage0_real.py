# -*- coding: utf-8 -*-
"""E6m 阶段 N · N4 / N5：真实数据上的门层核验（名单层，不算任何收益）。每段一进程，复用 N5 落盘的源上下文。
  A3-1  适配器 source_U_t = 冻结总序前 n_t 对源门（build_factor_strategy_holdings_cached）逐日；CONTRACT_ERROR 计数
  A3-2/3/6/7/9  端点在真实数据上逐日 ≡ 源门，并经下游合同逐字源函数后 ≡ 源六形态（form_masks）
  A3-2  FULL_MUTABLE ≠ Mmean NATIVE α1（最终名单不同的日数）
  A3-7  HARD c.5：G ⊆ U0；A4b 下游后最终人数增 / 减 / 平日数
  A3-8  EDIT_MATCH α.25 w.1：|G △ U0| = 2·J* 逐日；J* = 0 日 ≡ U0
  A3-4 / A3-10  记忆路径：HG（昨日实际 G）与 LAG（昨日自然 U）在真实数据上分开的日数；断点续跑逐位；PROTECTED 带外不动；UNPROTECTED 越界日数
  A3-11  两日：Q_MAX2 raw = min(Q_T, Q_{T−1}) 逐位；两日都有效份额
  A2-5  kQ 重算与 N5 落盘逐位（确定性）
  A2-8  V 源 Parkinson20 raw 符号（源函数返回 −vol）
  A6-1  逐配置耗时（门 / 下游）→ 阶段 S 外推输入"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import pickle
import argparse
import resource

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_ops as O
import e6m_adapter as AD

ROWS = []
TIM = []


def rec(seg, fam, item, what, n, fails, extra=''):
    ROWS.append(dict(segment=seg, family=fam, appendix_item=item, check=what, n=int(n), failures=int(fails), status='PASS' if fails == 0 else 'FAIL',
                     detail=str(extra)[:400]))


def info(seg, fam, item, what, value):
    ROWS.append(dict(segment=seg, family=fam, appendix_item=item, check=what, n=0, failures=0, status='INFO', detail=str(value)[:400]))


def gate_mask(days, T, N, fn):
    out = np.zeros((T, N), bool)
    for t, D in enumerate(days):
        if D is not None:
            out[t, D['cols'][fn(D)]] = True
    return out


def run(seg, attempt):
    import e6j_prod as PR
    import pool_screening_v2 as PS
    t00 = time.time()
    with open(M.P('tmp', 'ctx_%s.pkl' % seg), 'rb') as fh:
        ctx = pickle.load(fh)
    t0 = time.time()
    raw, neu, kq, dabs = AD.q_source(ctx)
    TIM.append(dict(segment=seg, item='q_source_s', value=time.time() - t0))
    z = np.load(M.P('stage0', 'cache_cloud', 'kq_%s.npz' % seg), allow_pickle=False)
    import e6j_slot as SL
    same = np.array_equal(SL.dense(ctx, kq), z['kq'], equal_nan=True)
    rec(seg, 'Q0', 'A2-5', 'kQ 重算与 N5 落盘逐位相同（确定性；对 E6j J_B1_qCC 的锚 = ANCHOR_PENDING）', 1, int(not same))
    forms_src = PR.form_masks(ctx)
    DS = AD.Downstream(ctx)
    T, N = ctx['pool0'].shape
    for fam in ('A4b', 'Munion', 'Mmean'):
        t0 = time.time()
        G = AD.Gate(ctx, fam, kq)
        days = [G.day(t) for t in range(T)]
        TIM.append(dict(segment=seg, item='%s_gate_days_build_s' % fam, value=time.time() - t0))
        t0 = time.time()
        src = G.source_kept()
        TIM.append(dict(segment=seg, item='%s_source_gate_s' % fam, value=time.time() - t0))
        bad = 0
        for t, D in enumerate(days):
            if D is None:
                bad += int(src[t].any())
                continue
            u = O.source_mask(D['order'], D['n'])
            bad += int(not (np.array_equal(u, src[t, D['cols']]) and src[t].sum() == u.sum()))
        rec(seg, fam, 'A3-1', '适配器 source_U = 冻结总序前 n_t（n_t = ceil(N/2)）与源门逐日相同（CONTRACT_ERROR 日数）', T, bad,
            '有门日 %d' % sum(D is not None for D in days))
        famforms = [f for f in AD.FAMILY if AD.FAMILY[f] == fam]
        endpoints = {
            'BAND_Q_w0': lambda D: O.band(D['order'], D['s0'], D['kq'], D['n'], 0, ids=D['ids']),
            'BAND_BLEND_a0_w.10': lambda D: O.band(D['order'], D['s0'], D['kq'], D['n'], .1, inside=G.native_s(D, 0.0), ids=D['ids']),
            'BAND_BLEND_a0_w.40': lambda D: O.band(D['order'], D['s0'], D['kq'], D['n'], .4, inside=G.native_s(D, 0.0), ids=D['ids']),
            'COPY_BAND_Q_w.40': lambda D: O.band(D['order'], D['s0'], D['kq'], D['n'], .4, inside=O.copy_coordinates(D['order'], D['kq']), ids=D['ids']),
            'PRIORITY_c1': lambda D: O.priority_pass(D['order'], D['s0'], D['kq'], D['n'], 1.0, ids=D['ids'])[0],
            'HARD_c1': lambda D: O.hard_conj(O.source_mask(D['order'], D['n']), D['kq'], 1.0),
        }
        for nm, fn in endpoints.items():
            t0 = time.time()
            gm = gate_mask(days, T, N, fn)
            tg = time.time() - t0
            t0 = time.time()
            fin = DS.forms(fam, gm)
            td = time.time() - t0
            TIM.append(dict(segment=seg, item='%s_%s_gate_s' % (fam, nm), value=tg))
            TIM.append(dict(segment=seg, item='%s_%s_downstream_s' % (fam, nm), value=td))
            gd = int((gm != src).any(axis=1).sum())
            fd = sum(int((fin[f] != forms_src[f]).any(axis=1).sum()) for f in famforms)
            rec(seg, fam, {'BAND_Q_w0': 'A3-2', 'BAND_BLEND_a0_w.10': 'A3-3', 'BAND_BLEND_a0_w.40': 'A3-3', 'COPY_BAND_Q_w.40': 'A3-9',
                           'PRIORITY_c1': 'A3-6', 'HARD_c1': 'A3-7'}[nm],
                '端点 %s：门层逐日 ≡ 源门；经下游源函数后两形态逐日 ≡ form_masks（不同日数：门 + 最终）' % nm, T * (1 + len(famforms)), gd + fd,
                '门不同 %d 日；最终不同 %d 日' % (gd, fd))
        if fam == 'Mmean':
            def full_mut(D):
                kqv = D['kq']
                fin_ = np.isfinite(kqv)
                base = O.source_mask(D['order'], D['n'])
                out = base & ~fin_
                k = D['n'] - int(out.sum())
                F = np.flatnonzero(fin_)
                out[F[np.lexsort((O.ranks_of(D['order'])[F], kqv[F]))][:k]] = True
                return out
            fm = DS.forms(fam, gate_mask(days, T, N, full_mut))['M_mean3_v2']
            na1 = DS.forms(fam, gate_mask(days, T, N, lambda D: O.source_mask(np.lexsort((D['tie'], G.native_s(D, 1.0))), D['n'])))['M_mean3_v2']
            dd = int((fm != na1).any(axis=1).sum())
            rec(seg, fam, 'A3-2', 'FULL_MUTABLE 端点 ≠ Mmean NATIVE α1（最终名单不同的日数 > 0）', 1, int(dd == 0), '不同 %d 日' % dd)
        hard = gate_mask(days, T, N, lambda D: O.hard_conj(O.source_mask(D['order'], D['n']), D['kq'], .5))
        sub = int((hard & ~src).any(axis=1).sum())
        rec(seg, fam, 'A3-7', 'HARD c.5：G ⊆ U0 逐日（越出日数）', T, sub)
        if fam == 'A4b':
            fin = DS.a4b(hard)['A4b']
            dn = fin.sum(1).astype(int) - forms_src['A4b'].sum(1).astype(int)
            info(seg, fam, 'A3-7', 'HARD c.5 经 T 重估后最终人数相对父：增 / 减 / 平日数', '增 %d / 减 %d / 平 %d' % ((dn > 0).sum(), (dn < 0).sum(), (dn == 0).sum()))
        bad = jz = jtot = 0
        jlist = []
        for t, D in enumerate(days):
            if D is None:
                continue
            ns = G.native_s(D, .25)
            fin_ = np.isfinite(D['kq'])
            u0 = O.source_mask(D['order'], D['n'])
            nat = u0 & ~fin_
            k = D['n'] - int(nat.sum())
            F = np.flatnonzero(fin_)
            nat[F[np.lexsort((O.ranks_of(D['order'])[F], ns[F]))][:k]] = True          # NATIVE_MASKFIX(α.25)
            r = O.edit_match(D['order'], D['kq'], D['n'], .1, nat, ns, ids=D['ids'])
            jlist.append((r['J'], r['J_star']))
            for kk in ('LOCAL', 'GLOBAL', 'NATIVE_TRIM'):
                bad += int((r[kk] ^ u0).sum() != 2 * r['J_star'])
            if r['J_star'] == 0:
                jz += 1
                bad += int(not all(np.array_equal(r[kk], u0) for kk in ('LOCAL', 'GLOBAL', 'NATIVE_TRIM')))
            jtot += 1
        J = np.array(jlist)
        rec(seg, fam, 'A3-8', 'EDIT_MATCH α.25 w.1：三账户恰换 J* 对；J* = 0 日 ≡ U0', jtot * 3, bad,
            'J 中位 %.0f / J* 中位 %.0f / J* = 0 日 %d / 被截份额 %.3f' % (np.median(J[:, 0]), np.median(J[:, 1]), jz, 1 - J[:, 1].sum() / max(J[:, 0].sum(), 1)))
        # 记忆：HG（昨日实际 G）vs LAG（昨日自然 U）；b_eff = .10·K_loading（A4b / union 1；Mmean 1/腿数，源 bunit 同式）
        def mem_path(lo, hi, state=None):
            pu, pg, pl = state if state else (set(), set(), set())
            res, ndiff = [], 0
            for t in range(lo, hi):
                D = days[t]
                if D is None:
                    pu, pg, pl = set(), set(), set()
                    res.append(None)
                    continue
                s = G.native_s(D, .25)
                o_ = np.lexsort((D['tie'], s))
                U = O.source_mask(o_, D['n'])
                ndiff += int(pu != pg)
                mG = np.array([i in pg for i in D['ids']])
                mU = np.array([i in pl for i in D['ids']])
                ghg = O.source_mask(np.lexsort((D['tie'], s - .10 * D['K_loading'] * mG)), D['n'])
                glag = O.source_mask(np.lexsort((D['tie'], s - .10 * D['K_loading'] * mU)), D['n'])
                res.append((frozenset(D['ids'][U]), frozenset(D['ids'][ghg]), frozenset(D['ids'][glag])))
                pu, pg, pl = set(D['ids'][U]), set(D['ids'][ghg]), set(D['ids'][U])
            return res, (pu, pg, pl), ndiff
        t0 = time.time()
        full, _, nd = mem_path(0, T)
        TIM.append(dict(segment=seg, item='%s_memory_path_s' % fam, value=time.time() - t0))
        a, st, _ = mem_path(0, min(300, T))
        b, _, _ = mem_path(min(300, T), T, st)
        hg_ne_lag = sum(int(x is not None and x[1] != x[2]) for x in full)
        rec(seg, fam, 'A3-10', '记忆：HG 与 LAG 在真实数据上分开（昨日 U ≠ 昨日 G 的日数 > 0；HG / LAG 名单不同日数 > 0）', 1, int(nd == 0 or hg_ne_lag == 0),
            '昨日 U≠G %d 日；HG≠LAG %d 日' % (nd, hg_ne_lag))
        rec(seg, fam, 'A3-10', '断点续跑（前 300 日 + 其余）自然 U / 实际 G（HG / LAG）逐日相同', T, sum(int(x != y) for x, y in zip(full, a + b)))
        bad = ue = 0
        pnat = set()
        for t, D in enumerate(days):
            if D is None:
                pnat = set()
                continue
            nat = O.band(D['order'], D['s0'], D['kq'], D['n'], .1, ids=D['ids'])
            prev = np.array([i in pnat for i in D['ids']])
            act = O.band(D['order'], D['s0'], D['kq'], D['n'], .1, prev_natural=prev, b=.10, loading=D['K_loading'], ids=D['ids'])
            A_, B_, C_, j = O.band_parts(D['order'], D['n'], .1)
            base = O.source_mask(D['order'], D['n'])
            miss = ~np.isfinite(D['kq'])
            bad += int(not (act[A_].all() and not act[C_].any() and np.array_equal(act[miss], base[miss]) and act.sum() == D['n']))
            _, e = O.band_unprotected(D['order'], D['s0'], D['kq'], D['n'], .1, D['kq'], prev, b=.10, loading=D['K_loading'], ids=D['ids'])
            ue += int(e > 0)
            pnat = set(D['ids'][nat])
        rec(seg, fam, 'A3-4', 'PROTECTED_LAG10（BAND_Q w.1）：A / C / Q 缺失身份与名额逐日不变（带外编辑 0）', T, bad)
        info(seg, fam, 'A3-4', 'UNPROTECTED_LAG10 桥（BAND_Q w.1）：带外编辑 > 0 的日数', ue)
    # 两日（A3-11）与 V 符号（A2-8）
    q = np.asarray(raw.to_numpy(float))
    d = dabs.reindex_like(ctx['pool0']).to_numpy()
    p0 = ctx['p0']
    mx = O.two_day_raw(d[1:], d[:-1], 'MAX')
    with np.errstate(all='ignore'):
        q1 = 1.0 / (d + 1e-4)
        mn = np.minimum(q1[1:], q1[:-1])
    ok = np.isfinite(mx)
    rec(seg, 'Q_MAX2', 'A3-11', 'Q_MAX2 raw = min(Q_T, Q_{T−1}) 逐位（两日都有效格）', int(ok.sum()), int((mx[ok] != mn[ok]).sum()))
    info(seg, 'Q_MAX2', 'A3-11', '两日都有效份额（pool0 格）', round(float(ok[p0[1:]].mean()), 6))
    pk = PS.compute_parkinson_vol(ctx['data']['high'], ctx['data']['low']).reindex_like(ctx['pool0']).to_numpy()
    v = pk[p0]
    v = v[np.isfinite(v)]
    info(seg, 'PARKINSON20', 'A2-8', 'V 源 raw（compute_parkinson_vol 返回 −vol）在 pool0 有限格：份额 < 0 / = 0 / > 0；分位 p01 / p50 / p99',
         '%.6f / %.6f / %.6f；%.5f / %.5f / %.5f' % ((v < 0).mean(), (v == 0).mean(), (v > 0).mean(), *np.percentile(v, [1, 50, 99])))
    TIM.append(dict(segment=seg, item='total_s', value=time.time() - t00))
    TIM.append(dict(segment=seg, item='rss_peak_gb', value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2))
    TIM.append(dict(segment=seg, item='T_days', value=T))
    TIM.append(dict(segment=seg, item='N_columns', value=N))
    R = pd.DataFrame(ROWS)
    TT = pd.DataFrame(TIM)
    M.atomic_write_csv(M.P('checks', 'real_gate_%s.csv' % seg), R)
    M.atomic_write_csv(M.P('stage0', 'c6_timing_gate_%s.csv' % seg), TT)
    ok = not (R.status == 'FAIL').any()
    M.write_receipt(os.environ.get('E6M_TASK', 'N4_real_gate_%s_%s' % (seg, attempt)), [M.P('checks', 'real_gate_%s.csv' % seg), M.P('stage0', 'c6_timing_gate_%s.csv' % seg)],
                    status='SUCCEEDED' if ok else 'FAILED', code=[__file__, AD.__file__, O.__file__, M.__file__], counts=R.status.value_counts().to_dict())
    print(json.dumps(dict(seg=seg, counts=R.status.value_counts().to_dict(), total_s=round(time.time() - t00, 1)), ensure_ascii=False), flush=True)
    return 0 if ok else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--attempt', default='a1')
    a = ap.parse_args()
    sys.exit(run(a.seg, a.attempt))
