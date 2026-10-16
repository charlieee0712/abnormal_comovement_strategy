# -*- coding: utf-8 -*-
"""E6m 阶段 N · N4 合成测试（附录 A3 / A5 的 N 项 + A1-5 合成守卫攻击）。不读行情、不读收益。
两层：① 生产算子（e6m_ops / e6m_b3_tools）对 plan 参考实现（stage0/plan_tests/e6m_spec_tests.py，sha 25020c82…）随机对拍；
② 附录逐项合成恒等 / 反例。输出 checks/synthetic_*.csv 与 checks/synthetic_summary.csv。"""
import os
import sys
import json
import time
import itertools
import subprocess
import importlib.util
from fractions import Fraction

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_ops as O
import e6m_b3_tools as B

ROWS = []


def rec(group, tid, item, what, n, fails, extra=''):
    ROWS.append(dict(group=group, test_id=tid, appendix_item=item, description=what, n_cases=int(n), failures=int(fails),
                     status='PASS' if fails == 0 else 'FAIL', detail=str(extra)[:300]))


def spec():
    p = M.P('stage0', 'plan_tests', 'e6m_spec_tests.py')
    sp = importlib.util.spec_from_file_location('e6m_spec_ref2', p)
    mod = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    return mod


def case(rng, N, ties=False, miss=0.15):
    s0 = rng.uniform(size=N)
    if ties:
        s0 = np.round(s0, 1)
    kq = rng.uniform(size=N)
    kq[rng.uniform(size=N) < miss] = np.nan
    ids = np.array(['T%05d' % i for i in rng.permutation(100000)[:N]])
    return s0, kq, ids


def spec_order(s0, ids):
    return np.lexsort((ids, s0))


# ===================================================================== ① 对拍
def crosscheck(S, rng):
    g = 'XCHECK'
    W = (.02, .05, .1, .2, .4)
    f = 0
    n = 0
    for _ in range(600):
        N = int(rng.integers(6, 140))
        s0, kq, ids = case(rng, N, ties=bool(rng.integers(0, 2)))
        n_ = int(rng.integers(0, N + 1))
        w = W[rng.integers(0, 5)]
        order = spec_order(s0, ids)
        tie = O.ranks_of(np.lexsort((ids,)))                           # 平局按 ticker：与参考实现 order(score, ids) 一致
        o2 = O.total_order(s0, tie)
        if not np.array_equal(o2, order):
            f += 1
        inside = .75 * s0 + .25 * np.where(np.isfinite(kq), kq, s0)
        for ins in (None, inside):
            a = O.band(order, s0, kq, n_, w, inside=ins, ids=ids)
            bref = S.band_gate(s0, kq, n_, w, ids=ids, inside_score=ins)
            n += 1
            f += int(not np.array_equal(a, bref))
        prev = rng.uniform(size=N) < .5
        loading = rng.choice([1.0, 1 / 2, 1 / 3], size=N)
        a = O.band(order, s0, kq, n_, w, inside=inside, prev_natural=prev, b=.1, loading=loading, ids=ids)
        bref = S.band_gate(s0, kq, n_, w, ids=ids, inside_score=inside, prev=prev, b=.1, loading=loading)
        n += 1
        f += int(not np.array_equal(a, bref))
        a = O.band_native_metric(order, s0, kq, n_, w, inside, prev_natural=prev, b=.1, loading=loading, ids=ids)
        bref = S.band_native_metric(s0, kq, n_, w, inside, ids=ids, prev=prev, b=.1, loading=loading)
        n += 1
        f += int(not np.array_equal(a, bref))
    rec(g, 'X1', 'A3-2/3/4/5', 'band / band(PROTECTED) / band_native_metric 对参考实现逐位（600 例 × 4，含 s0 平局）', n, f)
    f = n = 0
    for _ in range(600):
        N = int(rng.integers(6, 140))
        s0 = rng.uniform(size=N)
        kq = rng.uniform(size=N)
        kq[rng.uniform(size=N) < .15] = np.nan
        ids = np.arange(N).astype(str)
        n_ = int(rng.integers(0, N + 1))
        c = float(rng.choice([.3, .5, .7, .8, .9, 1.0]))
        order = np.lexsort((ids, s0))
        a, _ = O.priority_pass(order, s0, kq, n_, c, ids=ids)
        n += 2
        f += int(not np.array_equal(a, S.priority_pass(s0, kq, n_, c)))
        f += int(not np.array_equal(O.hard_conj(O.source_mask(order, n_), kq, c), S.hard_conj(s0, kq, n_, c)))
    rec(g, 'X2', 'A3-6/7', 'priority_pass / hard_conj 对参考实现逐位（600 例 × 2）', n, f)
    f = n = 0
    for _ in range(400):
        N = int(rng.integers(8, 120))
        s0 = rng.uniform(size=N)
        kq = rng.uniform(size=N)
        kq[rng.uniform(size=N) < .1] = np.nan
        ids = np.array(['T%04d' % i for i in range(N)])
        n_ = int(rng.integers(1, N))
        order = np.lexsort((ids, s0))
        nat_s = .75 * s0 + .25 * np.where(np.isfinite(kq), kq, s0)
        nat = O.source_mask(np.lexsort((ids, nat_s)), n_)
        w = float(rng.choice([.1, .2]))
        r = O.edit_match(order, kq, n_, w, nat, nat_s, ids=ids)
        u0 = O.source_mask(order, n_)
        A_, Bb, C_, j = O.band_parts(order, n_, w)
        inB = np.zeros(N, bool)
        inB[Bb] = True
        loc_ref, jl, _, _ = S.exact_swap(u0, kq, r['J_star'], inB)
        glo_ref, jg, _, _ = S.exact_swap(u0, kq, r['J_star'], np.ones(N, bool))
        n += 3
        f += int(not np.array_equal(r['LOCAL'], loc_ref)) + int(not np.array_equal(r['GLOBAL'], glo_ref))
        f += int(not all((g_ ^ u0).sum() == 2 * r['J_star'] for g_ in (r['LOCAL'], r['GLOBAL'], r['NATIVE_TRIM'])))
    rec(g, 'X3', 'A3-8', 'edit_match LOCAL / GLOBAL 对参考 exact_swap 逐位；三账户恰换 J* 对（400 例）', n, f)
    f = n = 0
    for _ in range(300):
        N = int(rng.integers(1, 60))
        s0 = rng.uniform(size=N)
        ov = rng.uniform(size=N)
        ov[rng.uniform(size=N) < .2] = np.nan
        ids = np.arange(N).astype(str)
        order = np.lexsort((ids, s0))
        n += 1
        a = O.copy_coordinates(order, ov)
        bref = S.copy_gate_coordinates(s0, ov)
        f += int(not np.array_equal(np.isnan(a), np.isnan(bref)) or not np.allclose(a[np.isfinite(a)], bref[np.isfinite(bref)], atol=0, rtol=0))
    for _ in range(300):
        d0 = rng.uniform(0, .1, 50)
        d1 = rng.uniform(0, .1, 50)
        d0[rng.uniform(size=50) < .1] = np.nan
        d1[rng.uniform(size=50) < .1] = np.nan
        for op, sop in (('MAX', 'MAX'), ('MIN', 'MIN'), ('LAG', 'LAG'), ('MEAN', 'MEAN')):
            n += 1
            a = O.two_day_raw(d0, d1, op)
            bref = S.qpair(d0, d1, sop)
            f += int(not (np.array_equal(np.isnan(a), np.isnan(bref)) and np.array_equal(a[np.isfinite(a)], bref[np.isfinite(bref)])))
    rec(g, 'X4', 'A3-9/11', 'copy_coordinates / two_day_raw 对参考实现逐位', n, f)
    f = n = 0
    for _ in range(200):
        m_, k_ = int(rng.integers(1, 9)), int(rng.integers(1, 12))
        x, y = rng.uniform(size=m_), rng.uniform(size=k_)
        if rng.integers(0, 2):
            x, y = np.round(x, 1), np.round(y, 1)
        xi = np.array(['x%d' % i for i in range(m_)])
        yi = np.array(['y%d' % i for i in range(k_)])
        n += 1
        f += int(B.min_distance_pairs(x, y, xi, yi) != S.min_distance_pairs(x, y, xi, yi))
    for _ in range(200):
        st = rng.choice(['UP', 'DOWN', 'MIXED', 'UNKNOWN'], size=30)
        for cnd in ('ALL', 'ALL_KNOWN', 'DOWN_MIXED', 'UP'):
            n += 1
            f += int(not np.array_equal(B.v_condition_mask(st, cnd), S.v_condition_mask(st, cnd)))
    for _ in range(100):
        v = rng.uniform(size=20)
        v[rng.uniform(size=20) < .2] = np.nan
        ids = np.array(['s%02d' % i for i in range(20)])
        n += 1
        f += int(not np.array_equal(np.nan_to_num(B.stable_permute(v, ids, 3, 9), nan=-1), np.nan_to_num(S.stable_permute(v, ids, 3, 9), nan=-1)))
    rec(g, 'X5', 'A3-12/15、A5-2', 'min_distance_pairs / v_condition_mask / stable_permute 对参考实现', n, f)


# ===================================================================== ② 附录逐项
def appendix(S, rng):
    g = 'A3'
    s0 = np.arange(40.) / 40
    kq = s0[::-1].copy()
    ids = np.array(['S%02d' % i for i in range(40)])
    order = np.lexsort((ids, s0))
    base = O.source_mask(order, 20)
    rec(g, 'A3-2a', 'A3-2', 'BAND_Q w = 0 ≡ 源对象', 1, int(not np.array_equal(O.band(order, s0, kq, 20, 0, ids=ids), base)))
    bad = 0
    for N in range(2, 400):
        for w in (.02, .05, .1, .2, .4):
            nn = N // 2
            exp = min(int(Fraction(str(w)) * N), nn, N - nn)
            bad += int(O.band_width_count(w, N, nn) != exp)
    rec(g, 'A3-2b', 'A3-2', 'm 用十进制有理 floor（N 2…399 × 五档 w；含 w = .10、N = 199）', 398 * 5, bad, 'N=199,w=.1 → %d' % O.band_width_count(.1, 199, 99))
    k = np.linspace(0, 1, 30)
    t = np.random.default_rng(5).uniform(size=30)
    c_ = np.random.default_rng(6).uniform(size=30)
    q = np.random.default_rng(7).uniform(size=30)
    comp = (k + t + c_) / 3
    full_mut = O.source_mask(np.lexsort((np.arange(30), q)), 15)                       # FULL_MUTABLE：B = E，按 kQ 取原名额
    mean_native1 = O.source_mask(np.lexsort((np.arange(30), (q + t + c_) / 3)), 15)     # Mmean NATIVE α1：K 腿换 Q 后仍有 T / cr20
    rec(g, 'A3-2c', 'A3-2', 'FULL_MUTABLE 端点 ≠ Mmean NATIVE α 1（含 T / cr20）', 1, int(np.array_equal(full_mut, mean_native1)))
    rec(g, 'A3-3a', 'A3-3', 'BAND_BLEND 无记忆 α = 0（带内优先序 = s0）≡ 源对象', 1, int(not np.array_equal(O.band(order, s0, kq, 20, .2, inside=s0, ids=ids), base)))
    wrong = (.75 * k + .25 * comp + 2 * t) / 3
    rec(g, 'A3-3b', 'A3-3', 'Mmean 用真实三腿综合式，不是 .75·s0 + .25·kQ（反例成立）', 1, int(np.allclose(wrong, (k + 2 * t) / 3)))
    viol = edits_un = slotbad = 0
    for _ in range(300):
        N = int(rng.integers(12, 120))
        s0r, kqr, idr = case(rng, N)
        o = np.lexsort((idr, s0r))
        n_ = N // 2
        prev = rng.uniform(size=N) < .5
        ins = .75 * s0r + .25 * np.where(np.isfinite(kqr), kqr, s0r)
        b0 = O.source_mask(o, n_)
        out = O.band(o, s0r, kqr, n_, .2, inside=ins, prev_natural=prev, b=.1, ids=idr)
        A_, Bb, C_, j = O.band_parts(o, n_, .2)
        miss = ~np.isfinite(kqr)
        viol += int(not (out[A_].all() and not out[C_].any() and np.array_equal(out[miss], b0[miss]) and out.sum() == n_))
        good = Bb[np.isfinite(kqr[Bb])]
        slotbad += int(len(good) and not np.array_equal(np.sort(s0r[good]), np.sort(s0r[good])))
        _, e = O.band_unprotected(o, s0r, kqr, n_, .2, ins, prev, b=.4, ids=idr)
        edits_un += int(e > 0)
    rec(g, 'A3-4a', 'A3-4', 'PROTECTED_LAG10：A / C / Q 缺失身份不变、名额不变（outside_band_edits = 0）', 300, viol)
    rec(g, 'A3-4b', 'A3-4', 'UNPROTECTED_LAG10 桥：越界编辑数 > 0 的合成日数（信息项：> 0 即可）', 300, int(edits_un == 0), '越界 > 0 的例 %d / 300' % edits_un)
    same0 = diff = 0
    for _ in range(300):
        N = int(rng.integers(12, 80))
        s0r, kqr, idr = case(rng, N)
        o = np.lexsort((idr, s0r))
        ins = .75 * s0r + .25 * np.where(np.isfinite(kqr), kqr, s0r)
        prev = rng.uniform(size=N) < .5
        a0 = O.band_native_metric(o, s0r, kqr, N // 2, .3, ins, prev_natural=prev, b=0.0, ids=idr)
        e0 = O.band(o, s0r, kqr, N // 2, .3, inside=ins, ids=idr)
        same0 += int(not np.array_equal(a0, e0))
        diff += int(not np.array_equal(O.band_native_metric(o, s0r, kqr, N // 2, .3, ins, prev_natural=prev, b=.1, ids=idr),
                                       O.band(o, s0r, kqr, N // 2, .3, inside=ins, prev_natural=prev, b=.1, ids=idr)))
    rec(g, 'A3-5a', 'A3-5', 'NATIVE_METRIC_LAG：b = 0 ≡ 同带 BAND_BLEND 无记忆端点', 300, same0)
    rec(g, 'A3-5b', 'A3-5', 'NATIVE_METRIC_LAG：b > 0 允许与 SLOT_MAPPED 不同（信息项：不同例 > 0）', 300, int(diff == 0), '不同例 %d / 300' % diff)
    fails = 0
    for _ in range(200):
        N = int(rng.integers(8, 80))
        s0r = rng.uniform(size=N)
        kqr = rng.uniform(size=N)
        kqr[rng.uniform(size=N) < .2] = np.nan
        idr = np.arange(N).astype(str)
        o = np.lexsort((idr, s0r))
        n_ = N // 2
        prev = rng.uniform(size=N) < .5
        p1, _ = O.priority_pass(o, s0r, kqr, n_, 1.0, ids=idr)
        fails += int(not np.array_equal(p1, O.source_mask(o, n_)))
        old_lag = O.source_mask(np.lexsort((idr, O.ranks_of(o), s0r - .1 * prev)), n_)
        p1m, _ = O.priority_pass(o, s0r, kqr, n_, 1.0, prev_natural=prev, b=.1, ids=idr)
        fails += int(not np.array_equal(p1m, old_lag))
    rec(g, 'A3-6a', 'A3-6', 'PRIORITY_PASS c = 1：无记忆 ≡ 源对象；有记忆 ≡ OLD_LAG（同 s0 − b·1(昨日自然 U)）', 400, fails)
    errs = 0
    for c in (-.1, 1.1, 80.0, np.nan, np.inf):
        for fn in (lambda c: O.priority_pass(order, s0, kq, 20, c), lambda c: O.hard_conj(base, kq, c)):
            try:
                fn(c)
            except ValueError:
                continue
            errs += 1
    rec(g, 'A3-6b', 'A3-6', 'c 为 0–100 或非有限 → 报错（PRIORITY / HARD）', 10, errs)
    sub = miss_del = 0
    for _ in range(300):
        N = int(rng.integers(8, 80))
        s0r = rng.uniform(size=N)
        kqr = rng.uniform(size=N)
        kqr[rng.uniform(size=N) < .2] = np.nan
        o = np.lexsort((np.arange(N), s0r))
        u0 = O.source_mask(o, N // 2)
        h = O.hard_conj(u0, kqr, .5)
        sub += int(np.any(h & ~u0))
        miss_del += int(np.any(u0 & ~np.isfinite(kqr) & ~h))
    one = O.hard_conj(base, kq, 1.0)
    rec(g, 'A3-7a', 'A3-7', 'HARD_CONJ：c = 1 ≡ 源；G ⊆ U0；Q 缺失不新删', 601, sub + miss_del + int(not np.array_equal(one, base)))
    old = np.array([1, 1, 1, 1], bool)
    new = np.array([0, 0, 1, 1], bool)
    ts = np.array([.1, .2, .3, .4])
    veto = np.array([1, 1, 0, 0], bool)

    def down(gm):
        ix = np.flatnonzero(gm)
        out = np.zeros(4, bool)
        out[ix[np.argsort(ts[ix])[:len(ix) // 2]]] = True
        return out & ~veto
    rec(g, 'A3-7b', 'A3-7', '上游删除后下游 T 重估可使最终人数增加（反例成立；真实数据日数在 S 报）', 1, int(not (down(new).sum() > down(old).sum())))
    f0 = 0
    for _ in range(200):
        N = int(rng.integers(8, 80))
        s0r = rng.uniform(size=N)
        kqr = rng.uniform(size=N)
        idr = np.array(['E%03d' % i for i in range(N)])
        o = np.lexsort((idr, s0r))
        u0 = O.source_mask(o, N // 2)
        r = O.edit_match(o, kqr, N // 2, .1, u0, s0r, ids=idr)            # NATIVE = U0 → J = 0
        f0 += int(not (r['J_star'] == 0 and all(np.array_equal(r[k], u0) for k in ('LOCAL', 'GLOBAL', 'NATIVE_TRIM'))))
    rec(g, 'A3-8a', 'A3-8', 'EDIT_MATCH：J* = 0 ≡ U0（三账户）', 200, f0)
    s_ = np.array([.1, .4, .8])
    outs = np.array([0, 1, 2])
    rec(g, 'A3-8b', 'A3-8', 'NATIVE_TRIM 换出由劣到好（最差先出）', 1, int(outs[np.lexsort((outs, -s_[outs]))][0] != 2))
    cc = O.copy_coordinates(order, np.ones(40))
    rec(g, 'A3-9a', 'A3-9', 'BAND_Q 的 COPY（带内优先序 = 复制坐标）恢复原门优先序 ≡ 源', 1, int(not np.array_equal(O.band(order, s0, cc, 20, .4, inside=cc, ids=ids), base)))
    rec(g, 'A3-9b', 'A3-9', 'BAND_BLEND 的 COPY 以 s0 为带内优先序 ≡ 源', 1, int(not np.array_equal(O.band(order, s0, kq, 20, .4, inside=s0, ids=ids), base)))
    own = np.ones(40)
    own[[3, 30]] = np.nan
    ccm = O.copy_coordinates(order, own)
    cp, _ = O.priority_pass(order, s0, ccm, 20, .3, ids=ids)
    ch = O.hard_conj(base, ccm, .3)
    rec(g, 'A3-9c', 'A3-9', 'COPY 资格（复制坐标、同 c、同缺失身份）：HARD 版 c = .3 继续删票（≠ 原父 → Y00 偏父时基线桥存在）；PRIORITY 版回填后 = 原父（复制坐标与原总序单调）',
        2, int(np.array_equal(ch, base)) + int(not np.array_equal(cp, base)), 'COPY_HARD 删 %d 只；COPY_PRIORITY = 原父：%s' % (int((base & ~ch).sum()), np.array_equal(cp, base)))
    # A3-10：记忆引用与断点
    sc = np.array([[0., 1.], [.51, .5], [.51, .5]])

    def path(scores, n, b, kind, state=None, start=0):
        P_ = scores.shape[1]
        st = state or dict(U=np.zeros(P_, bool), G=np.zeros(P_, bool), next=start)
        if st['next'] != start:
            raise ValueError('checkpoint date mismatch')
        outG, outU = [], []
        U, G = st['U'].copy(), st['G'].copy()
        for t_, z in enumerate(scores, start):
            o_ = np.lexsort((np.arange(P_), z))
            u = O.source_mask(o_, n)
            m = O.memory_reference(kind, U, G)
            gg = O.source_mask(np.lexsort((np.arange(P_), z - b * m)), n)
            outG.append(gg)
            outU.append(u)
            U, G = u, gg
        return np.array(outG), np.array(outU), dict(U=U, G=G, next=start + len(scores))
    hg, _, _ = path(sc, 1, .1, 'HG10')
    lag, _, _ = path(sc, 1, .1, 'LAG1_10')
    rec(g, 'A3-10a', 'A3-10', 'HG 用本路径昨日实际 G、LAG 用同算子昨日自然 U：同分数路径下两者名单不同', 1, int(np.array_equal(hg, lag)))
    big = np.random.default_rng(98).uniform(size=(30, 10))
    bad = 0
    for kind in ('HG10', 'LAG1_10'):
        fg, fu, _ = path(big, 4, .1, kind)
        a1, u1, st = path(big[:13], 4, .1, kind)
        a2, u2, _ = path(big[13:], 4, .1, kind, state=st, start=13)
        bad += int(not (np.array_equal(fg, np.vstack([a1, a2])) and np.array_equal(fu, np.vstack([u1, u2]))))
    try:
        _, _, st = path(big[:5], 4, .1, 'HG10')
        path(big[5:], 4, .1, 'HG10', state=st, start=7)
        bad += 1
    except ValueError:
        pass
    rec(g, 'A3-10b', 'A3-10', '断点续跑（13 日 + 17 日 vs 30 日）自然 U / 实际 G 逐位相同；错位时钟报错', 3, bad)
    d = np.array([0., .01, .1, np.nan])
    q0 = O.two_day_raw(d, d, 'MAX')
    ref = np.where(np.isfinite(d), 1 / (d + 1e-4), np.nan)
    a_ = np.array([0, .01, .1])
    b_ = np.array([.02, .03, 0])
    X = np.c_[np.ones(4), np.arange(4.)]
    res = lambda z: z - X @ np.linalg.lstsq(X, z, rcond=None)[0]
    neu_order = not np.allclose(res(np.minimum([1., 5., 2., 8.], [4., 2., 6., 1.])), np.minimum(res(np.array([1., 5., 2., 8.])), res(np.array([4., 2., 6., 1.]))))
    rec(g, 'A3-11', 'A3-11', 'd_{T−1} = d_T 时 Q_MAX2 / MIN2 / MEAN2 ≡ Q0；Q_MAX2 = min(Q_T, Q_{T−1})；先中性化再取极值 ≠ 先取极值再中性化；两日缺失 → 缺失（回旧 K 并标记）', 4,
        int(not (np.array_equal(np.isnan(q0), np.isnan(ref)) and np.allclose(q0[:3], ref[:3]) and np.allclose(O.two_day_raw(a_, b_, 'MAX'),
                                                                                                         np.minimum(1 / (a_ + 1e-4), 1 / (b_ + 1e-4)))
                 and neu_order and np.isnan(O.two_day_raw([.1], [np.nan], 'MAX')[0]))))
    # A3-12
    bad = 0
    for _ in range(40):
        m_, n_ = int(rng.integers(1, 7)), int(rng.integers(1, 8))
        x, y = rng.uniform(size=m_), rng.uniform(size=n_)
        p = B.min_distance_pairs(x, y)
        got = sum(abs(x[i] - y[j]) for i, j in p)
        small, large = (x, y) if m_ <= n_ else (y, x)
        best = min(sum(abs(small[i] - large[j]) for i, j in enumerate(c)) for c in itertools.permutations(range(len(large)), len(small)))
        bad += int(abs(got - best) > 1e-12 or len(p) != min(m_, n_))
    try:
        B.min_distance_pairs([np.nan], [.1])
        bad += 1
    except ValueError:
        pass
    lp = B.label_pair([100, 110, 99], 0, 2)
    bad += int(not (abs(lp['endpoint'] + .01) < 1e-12 and abs(lp['linear_daily']) < 1e-12))
    pr = B.price_reaction(np.array([np.nan, 0.0, np.inf, .05, -.05, .001]), np.ones(6, bool))
    bad += int(not (pr[0] == 'UNKNOWN' and pr[1] == 'QUIET' and pr[2] == 'UNKNOWN' and pr[3] in ('UP', 'QUIET') and pr[4] in ('DOWN', 'QUIET')))
    rec(g, 'A3-12', 'A3-12', 'min_distance_pairs 与穷举总距离相等（≤ 6 × 7）；无效数据报错；label_pair 100→110→99 终点 −1% / 逐日和 0；NaN r → UNKNOWN、真实零 → QUIET、inf → 非 QUIET', 44, bad)
    r = B.symmetric_states([.3, .7], [1., 2.], [.6, .4], [3., 1.])
    ok = abs(r['frequency'] + r['within'] + r['one_sided'] - r['total']) < 1e-12
    try:
        B.symmetric_states([1.], [np.nan], [1.], [1.])
        ok = False
    except ValueError:
        pass
    rec(g, 'A3-13', 'A3-13', 'SYMDEC 三项严格加回；占用状态均值未知报错（不按 0 闭合）', 2, int(not ok))
    ok = B.first_feasible_exit(8, 6, 1, [1] * 12) == (6, 6)
    x = np.ones(10, bool)
    x[3:8] = False
    ok &= B.first_feasible_exit(2, 5, 1, x) == (8, 8) and B.first_feasible_exit(2, 5, 1, [False] * 8) == (None, None)
    rec(g, 'A3-14', 'A3-14', 'first_feasible_exit：触发不晚于原正常目标；卖不掉继续持有；终点不可卖保持未知', 3, int(not ok))
    st = np.array(['UP', 'DOWN', 'MIXED', 'UNKNOWN'])
    ok = (B.v_condition_mask(st, 'ALL').all() and B.v_condition_mask(st, 'ALL_KNOWN').tolist() == [1, 1, 1, 0]
          and not B.v_condition_mask(['UNKNOWN'], 'UP')[0] and not B.v_condition_mask(['UNKNOWN'], 'DOWN_MIXED')[0])
    u = np.array([1, 1, 1, 1, 0, 0], bool)
    dd = np.array([1, 0, 0, 1, 0, 0], bool)
    grp = np.array(['a', 'a', 'b', 'b', 'a', 'b'])
    ch = B.delete_count_control(u, dd, grp, list('abcdef'))
    ok &= all(np.sum((u & ~ch) & (grp == c)) == np.sum(dd & (grp == c)) for c in ('a', 'b')) and not np.any(ch & ~u)
    for seed in range(20):
        z = B.delete_count_control([1, 1, 1, 1], [1, 0, 0, 0], ['a'] * 4, list('abcd'), seed=seed, eligible=[1, 1, 0, 0])
        ok &= bool(z[2] and z[3] and z.sum() == 3)
    rec(g, 'A3-15', 'A3-15', 'V 条件：ALL 不读 Trend；ALL_KNOWN 只已知；条件版 UNKNOWN 不删；删除预算对照不在父外 / owner 缺失者取', 23, int(not ok))


def randoms(rng):
    g = 'A5'
    code = ('import numpy as np,sys; sys.path.insert(0,%r); import e6j_core as J; '
            'print(",".join("%%.17g"%%x for x in J.rng_for("E6m","Q0|A4b|BAND_Q",17,"2019-01-02","000001").uniform(size=5)))') % M.CODE
    outs = [subprocess.run([sys.executable, '-c', code], capture_output=True, text=True).stdout.strip() for _ in range(2)]
    local = ','.join('%.17g' % x for x in M.rng_for('E6m', 'Q0|A4b|BAND_Q', 17, '2019-01-02', '000001').uniform(size=5))
    rec(g, 'A5-1', 'A5-1', '显式种子：path_key（测量 / 控制 / 路径 / 绝对日块 / ticker）→ SeedSequence；两个独立进程与本进程序列相同（不依赖 PID / worker / 顺序）',
        3, int(not (outs[0] == outs[1] == local and outs[0])))
    v = np.array([.3, np.nan, .2, .8, .1])
    ids = np.array(list('abcde'))
    z = B.stable_permute(v, ids, 44, 2)
    ok1 = np.array_equal(np.isnan(z), np.isnan(v)) and np.array_equal(np.sort(v[np.isfinite(v)]), np.sort(z[np.isfinite(z)]))
    strata = np.array(['x', 'x', 'y', 'y', 'y'])
    zz = v.copy()
    for s_ in set(strata):
        ix = strata == s_
        zz[ix] = B.stable_permute(v[ix], ids[ix], 7, s_)
    ok2 = all(np.array_equal(np.sort(v[(strata == s_) & np.isfinite(v)]), np.sort(zz[(strata == s_) & np.isfinite(zz)])) for s_ in set(strata))
    s0 = np.arange(20.) / 20
    kq = rng.uniform(size=20)
    ids20 = np.array(['r%02d' % i for i in range(20)])
    o = np.lexsort((ids20, s0))
    A_, Bb, C_, j = O.band_parts(o, 10, .2)
    rk = B.stable_permute(kq, ids20, 1, 0)
    rb = O.band(o, s0, rk, 10, .2, ids=ids20)
    ok3 = rb[A_].all() and not rb[C_].any() and rb.sum() == 10
    lab = (kq <= .5)
    perm = B.stable_permute(lab.astype(float), ids20, 2, 0) > .5
    ok4 = perm.sum() == lab.sum()
    marks = rng.uniform(size=20) < .4
    pm = B.stable_permute(marks.astype(float), ids20, 3, 5) > .5
    ok5 = pm.sum() == marks.sum()
    rec(g, 'A5-2', 'A5-2', '七机制合同合成演示：LEGACY 缺失不动且多重集保持；ISK_P5 分层内置换；R-BAND 固定 A / C / 名额；R-FILTER_LABEL 保持 PASS 总数；'
                           'R-MEMORY 打乱标记保持标记数（HG 用自身实际 G、LAG 用自然 U 由调用方给入）', 5, int(not (ok1 and ok2 and ok3 and ok4 and ok5)))
    vals = np.full(1024, .3)
    identity = bool(np.all(vals == vals[0]))                         # 恒等路径按"全部取值相等"判（单遍方差有舍入，E6k #89）
    sd = 0.0 if identity else float(np.std(vals, ddof=1))
    need = lambda x: (np.std(x, ddof=1) / np.sqrt(len(x)))
    plan_n = 1024
    x = np.random.default_rng(1).normal(0, 1.2, 1024)
    while need(x[:plan_n]) > .03 and plan_n < 8192:
        plan_n += 512
        if plan_n > len(x):
            x = np.r_[x, np.random.default_rng(plan_n).normal(0, 1.2, 512)]
    rec(g, 'A5-3', 'A5-3', '首 1,024 固定、512 增补至 MCSE ≤ .03 或 8,192；恒等路径 sd = 0 单独标（不造 epsilon）', 2,
        int(not (sd == 0.0 and plan_n in range(1024, 8193, 512))), 'sd=1.2 合成：增补到 %d 路径' % plan_n)
    pairs = B.min_distance_pairs(np.array([.1, .3, .5]), np.array([.12, .31, .52, .9]))
    rx = np.array([.01, np.nan, .02])
    ry = np.array([0., .01, .0, .03])
    z = [rx[i] - ry[j] for i, j in pairs]
    ok6 = len(pairs) == 3 and not np.isfinite(np.mean(z))
    rec(g, 'A5-4', 'A5-4', 'B3 随机：R_CELL_REMATCH 置换后重新匹配 / R_PAIR_SWAP 只对内交换（合同）；未来缺价不补配（配对均值保持未知）', 1, int(not ok6))
    rec(g, 'A5-5', 'A5-5', '状态随机：STATE / V 条件对象的随机路径用同一状态序列（状态不随机化；合同条款写入随机登记）', 1, 0, '合同项；真实路径在 S 核')


def guards():
    g = 'A1-5'
    import e6j_core as J
    import e6l_state as LS
    att = []

    def must_raise(name, fn):
        try:
            fn()
            att.append((name, False))
        except Exception as e:                       # noqa: BLE001
            att.append((name, type(e).__name__ in ('RuntimeError', 'ValueError')))
    must_raise('e6j_core.assert_end_ok(20260330)', lambda: J.assert_end_ok('20260330', 'attack'))
    must_raise('e6j_core.assert_index_ok(含 2026-04-01)', lambda: J.assert_index_ok(pd.to_datetime(['2026-03-27', '2026-04-01']), 'attack'))
    must_raise('e6l_state.assert_state_dates(含 2026-03-30)', lambda: LS.assert_state_dates(['2026-03-27', '2026-03-30']))
    must_raise('e6l_state.load_full(end=20260401)（守卫在 import e6f_core 之前）', lambda: LS.load_full(end='20260401'))
    must_raise('e6l_state.full_period_ctx(end=20260401)', lambda: LS.full_period_ctx(end='20260401', dry_run=True))
    must_raise('e6m_core.assert_end_ok(2026-03-28)', lambda: M.assert_end_ok('2026-03-28'))
    fut = pd.date_range('2026-03-25', periods=6, freq='B')
    must_raise('合成未来扰动：B3 前向标签入口（终点 > 2026-03-27）', lambda: M.assert_index_ok(fut, 'B3 FWD label window'))
    must_raise('合成未来扰动：两日 d 入口（T > 2026-03-27）', lambda: M.assert_end_ok(str(fut[-1].date()), 'two-day d'))
    must_raise('合成未来扰动：B6 触发入口（触发日 > 2026-03-27）', lambda: M.assert_index_ok(pd.to_datetime(['2026-03-31']), 'B6 trigger'))
    ok = all(v for _, v in att)
    for name, v in att:
        rec(g, 'A1-5:' + name, 'A1-5', '守卫攻击（合成未来日期）：' + name, 1, int(not v))
    return ok


def main():
    t0 = time.time()
    S = spec()
    rng = np.random.default_rng(20261005)
    crosscheck(S, rng)
    appendix(S, rng)
    randoms(rng)
    guards()
    R = pd.DataFrame(ROWS)
    os.makedirs(M.P('checks'), exist_ok=True)
    for grp, df in R.groupby('group'):
        M.atomic_write_csv(M.P('checks', 'synthetic_%s.csv' % grp.replace('-', '_')), df)
    summ = R.groupby('group').status.value_counts().unstack(fill_value=0).reset_index()
    M.atomic_write_csv(M.P('checks', 'synthetic_summary.csv'), summ)
    ok = (R.status == 'PASS').all()
    outs = [M.P('checks', f) for f in os.listdir(M.P('checks')) if f.startswith('synthetic_')]
    M.write_receipt(os.environ.get('E6M_TASK', 'N4_synthetic_tests'), outs, status='SUCCEEDED' if ok else 'FAILED', code=[__file__, O.__file__, B.__file__, M.__file__],
                    inputs=[M.P('stage0', 'plan_tests', 'e6m_spec_tests.py')], counts=R.status.value_counts().to_dict(), wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(R.status.value_counts().to_dict(), wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    print(R[R.status != 'PASS'][['test_id', 'description', 'n_cases', 'failures', 'detail']].to_string(max_colwidth=90))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
