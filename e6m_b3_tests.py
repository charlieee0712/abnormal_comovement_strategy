# -*- coding: utf-8 -*-
"""E6m N8 · B3 内核与分类函数对拍（只用合成数据，不读任何行情或收益）。
对象：e6m_b3_kernels（numba）对 e6m_b3_tools 参考实现与本文件的纯 Python 参考；e6m_b3_build 的分类码对 e6m_b3_tools 字符串版。
输出 stageN/B3_prelim/tests/b3_kernel_tests.csv 与回执。"""
import e6j_boot  # noqa: F401
import os
import sys
import time

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_b3_tools as B
import e6m_b3_kernels as K
import e6m_b3_build as BB

MASK = (1 << 64) - 1
ROWS = []


def put(test, ok, **kw):
    ROWS.append(dict(test=test, status='PASS' if ok else 'FAIL', **kw))


def sm64(x):
    z = (x + 0x9E3779B97F4A7C15) & MASK
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
    return z ^ (z >> 31)


def hkey_py(seed, path, block, ident):
    return sm64(seed ^ sm64(path ^ sm64(block ^ sm64(ident))))


def perm_py(code, tick, seed, path, block):
    """R_CELL_REMATCH 参考：已知码按 ticker 升序为接收者，供体按 (hkey, ticker) 升序。"""
    out = code.copy()
    known = sorted([i for i in range(len(code)) if code[i] >= 0], key=lambda i: tick[i])
    donors = sorted(known, key=lambda i: (hkey_py(seed, path, block, int(tick[i])), tick[i]))
    for r_, d_ in zip(known, donors):
        out[r_] = code[d_]
    return out


def ref_match(off, d, lab, tick):
    """逐层调用 e6m_b3_tools.min_distance_pairs（ticker 补零字符串作 ID；层内按 (d, ticker)）。返回 (h 下标, l 下标) 对的集合。"""
    pairs = set()
    for s in range(len(off) - 1):
        ix = np.arange(off[s], off[s + 1])
        hi = ix[lab[ix] == 1]
        lo = ix[lab[ix] == 0]
        if len(hi) == 0 or len(lo) == 0:
            continue
        pr = B.min_distance_pairs(d[hi], d[lo], ['%06d' % t for t in tick[hi]], ['%06d' % t for t in tick[lo]])
        pairs |= {(int(hi[i]), int(lo[j])) for i, j in pr}
    return pairs


def synth_day(rng, n, nstrata, tie_heavy, nan_share=0.1, C=4):
    tick = rng.choice(np.arange(1, 999999), size=n, replace=False).astype(np.int64)
    strat = rng.integers(0, nstrata, n)
    d = (rng.integers(0, 4, n) / 100.0) if tie_heavy else rng.uniform(0, .05, n)
    code = rng.integers(-1, 3, n).astype(np.int8)
    Y = rng.normal(size=(n, C))
    Y[rng.uniform(size=(n, C)) < nan_share] = np.nan
    o = np.lexsort((tick, d, strat))
    tick, strat, d, code, Y = tick[o], strat[o], d[o], code[o], Y[o]
    off = np.r_[0, np.cumsum(np.bincount(strat, minlength=nstrata))].astype(np.int64)
    return tick, d, code, Y, off


def main():
    t0 = time.time()
    rng = np.random.default_rng(20261005)
    # 1 hkey：numba 对纯 Python
    bad = 0
    for _ in range(2000):
        s, p, b, i = (int(rng.integers(0, 2 ** 63)) * 2 + int(rng.integers(0, 2)), int(rng.integers(0, 4096)), int(rng.integers(0, 1000)),
                      int(rng.integers(0, 999999)))
        bad += int(int(K.hkey(np.uint64(s), p, b, i)) != hkey_py(s, p, b, i))
    put('hkey_numba_vs_python', bad == 0, cases=2000, mismatches=bad)
    # 2 dp_pairs 对 min_distance_pairs（含大量平局）
    bad = 0
    ncase = 0
    for tie in (True, False):
        for _ in range(400):
            m = int(rng.integers(0, 12))
            n = int(rng.integers(m, 20))
            a = np.sort((rng.integers(0, 4, m) / 100.0) if tie else rng.uniform(0, .05, m))
            b = np.sort((rng.integers(0, 4, n) / 100.0) if tie else rng.uniform(0, .05, n))
            # 同值内按 ticker 序：给 ID 0..m−1 / 0..n−1（已按值排好，同值内 ID 升序）
            oi = np.empty(n + 1, np.int64)
            oj = np.empty(n + 1, np.int64)
            k = K.dp_pairs(a, b, oi, oj)
            got = {(int(oi[q]), int(oj[q])) for q in range(k)}
            ref = set(B.min_distance_pairs(a, b, ['%06d' % i for i in range(m)], ['%06d' % j for j in range(n)])) if m else set()
            bad += int(got != ref)
            ncase += 1
    put('dp_pairs_vs_reference', bad == 0, cases=ncase, mismatches=bad)
    # 3 match_day 对逐层参考（配对集合、和、计数、NaN 标记）
    bad = 0
    for tie in (True, False):
        for _ in range(200):
            tick, d, code, Y, off = synth_day(rng, int(rng.integers(5, 60)), int(rng.integers(1, 6)), tie)
            lab = K.sides_of(code, np.array([0, -1, 1], np.int8))          # HIGH(2)→1、LOW(0)→0、MID(1)→−1
            n = len(d)
            ph = np.empty(n, np.int64)
            pl = np.empty(n, np.int64)
            npair, s_sum, s_cnt, s_nan = K.match_day(off, d, lab, Y, ph, pl)
            got = {(int(ph[q]), int(pl[q])) for q in range(npair)}
            ref = ref_match(off, d, lab, tick)
            diff = np.array([Y[h, :] - Y[l_, :] for h, l_ in ref]).reshape(-1, Y.shape[1])
            rs = np.where(np.isfinite(diff), diff, 0).sum(0)
            rc = np.isfinite(diff).sum(0)
            rn = (~np.isfinite(diff)).any(0)
            bad += int(got != ref or not np.allclose(s_sum, rs, atol=1e-12) or not np.array_equal(s_cnt, rc) or not np.array_equal(s_nan, rn))
    put('match_day_vs_reference', bad == 0, cases=400, mismatches=bad)
    # 4 permute_labels：人数守恒、未知不动、确定性、行序无关、对纯 Python 参考
    bad = dict(count=0, unknown=0, determinism=0, roworder=0, python=0, identical_paths=0)
    for _ in range(200):
        n = int(rng.integers(3, 80))
        tick = rng.choice(np.arange(1, 999999), size=n, replace=False).astype(np.int64)
        code = rng.integers(-1, 3, n).astype(np.int8)
        recv = np.argsort(tick, kind='mergesort').astype(np.int64)
        seed = int(rng.integers(0, 2 ** 63)) * 2 + 1
        out = K.permute_labels(code, tick, recv, np.uint64(seed), 7, 33)
        bad['count'] += int(not all((out == c).sum() == (code == c).sum() for c in (-1, 0, 1, 2)))
        bad['unknown'] += int(not np.array_equal(out[code < 0], code[code < 0]))
        bad['determinism'] += int(not np.array_equal(out, K.permute_labels(code, tick, recv, np.uint64(seed), 7, 33)))
        sh = rng.permutation(n)
        out2 = K.permute_labels(code[sh], tick[sh], np.argsort(tick[sh], kind='mergesort').astype(np.int64), np.uint64(seed), 7, 33)
        bad['roworder'] += int(dict(zip(tick[sh], out2)) != dict(zip(tick, out)))
        bad['python'] += int(not np.array_equal(out, perm_py(code, tick, seed, 7, 33)))
        if (code >= 0).sum() >= 6 and len(set(code[code >= 0])) > 1:
            outs = [tuple(K.permute_labels(code, tick, recv, np.uint64(seed), p, 33)) for p in range(16)]
            bad['identical_paths'] += int(len(set(outs)) < 2)
    put('permute_labels_invariants', sum(bad.values()) == 0, cases=200, **{'fail_' + k: v for k, v in bad.items()})
    # 5 paths_rematch（不配对 = 均值差；配对 = 重新匹配）对纯 Python 参考
    bad = 0
    for matched in (False, True):
        for _ in range(60):
            tick, d, code, Y, off = synth_day(rng, int(rng.integers(6, 50)), int(rng.integers(1, 5)), bool(rng.integers(0, 2)))
            smap = np.array([0, -1, 1], np.int8)
            recv = np.argsort(tick, kind='mergesort').astype(np.int64)
            seed = int(rng.integers(0, 2 ** 63))
            P = 8
            est, strict = K.paths_rematch(off, d, code, smap, Y, tick, recv, np.uint64(seed), 21, P, matched)
            for p in range(P):
                cp = perm_py(code, tick, seed, p, 21)
                lab = np.where(cp >= 0, smap[np.maximum(cp, 0)], -1)
                if matched:
                    ref = ref_match(off, d, lab, tick)
                    if ref:
                        diff = np.array([Y[h] - Y[l_] for h, l_ in ref])
                        fin = np.isfinite(diff)
                        e_ref = np.where(fin.sum(0) > 0, np.where(fin, diff, 0).sum(0) / np.maximum(fin.sum(0), 1), np.nan)
                        s_ref = np.where(fin.all(0), diff.mean(0) if fin.all() else np.where(fin, diff, 0).sum(0) / len(ref), np.nan)
                    else:
                        e_ref = s_ref = np.full(Y.shape[1], np.nan)
                else:
                    e_ref = np.array([np.nanmean(Y[lab == 1, c]) - np.nanmean(Y[lab == 0, c])
                                      if (np.isfinite(Y[lab == 1, c]).any() and np.isfinite(Y[lab == 0, c]).any()) else np.nan for c in range(Y.shape[1])])
                    s_ref = e_ref
                bad += int(not (np.allclose(est[p], e_ref, equal_nan=True, atol=1e-12) and np.allclose(strict[p], s_ref, equal_nan=True, atol=1e-12)))
    put('paths_rematch_vs_python', bad == 0, cases=120 * 8, mismatches=bad)
    # 6 paths_pairswap 对纯 Python 参考
    bad = 0
    for _ in range(60):
        tick, d, code, Y, off = synth_day(rng, int(rng.integers(6, 50)), int(rng.integers(1, 4)), False)
        lab = K.sides_of(code, np.array([0, -1, 1], np.int8))
        n = len(d)
        ph = np.empty(n, np.int64)
        pl = np.empty(n, np.int64)
        npair = K.match_day(off, d, lab, Y, ph, pl)[0]
        seed = int(rng.integers(0, 2 ** 63))
        est, strict = K.paths_pairswap(ph, pl, npair, Y, tick, np.uint64(seed), 5, 8)
        for p in range(8):
            if npair == 0:
                ok = np.isnan(est[p]).all() and np.isnan(strict[p]).all()
            else:
                sg = np.array([1.0 if (hkey_py(seed, p, 5, int(tick[ph[q]]) * 1000003 + int(tick[pl[q]])) & 1) == 0 else -1.0 for q in range(npair)])
                diff = (Y[ph[:npair]] - Y[pl[:npair]]) * sg[:, None]
                fin = np.isfinite(diff)
                e_ref = np.where(fin.sum(0) > 0, np.where(fin, diff, 0).sum(0) / np.maximum(fin.sum(0), 1), np.nan)
                s_ref = np.where(fin.all(0), np.where(fin, diff, 0).sum(0) / npair, np.nan)
                ok = np.allclose(est[p], e_ref, equal_nan=True, atol=1e-12) and np.allclose(strict[p], s_ref, equal_nan=True, atol=1e-12)
            bad += int(not ok)
    put('paths_pairswap_vs_python', bad == 0, cases=480, mismatches=bad)
    # 7 分类码对 e6m_b3_tools 字符串版（平局、NaN、真实零 r、域外）
    bad = 0
    for _ in range(300):
        n = int(rng.integers(1, 60))
        v = rng.integers(0, 5, n).astype(float)
        v[rng.uniform(size=n) < .15] = np.nan
        dom = rng.uniform(size=n) < .8
        r = rng.choice([-0.02, -0.01, 0.0, 0.01, 0.02, np.nan], n)
        a_ref = B.activity_terciles(v, dom)
        a_got = BB.terc_ref(v, dom)
        mp = {'LOW': 0, 'MID': 1, 'HIGH': 2, 'UNKNOWN': -1}
        bad += int(not np.array_equal(np.array([mp[x] for x in a_ref]), a_got))
        p_ref = B.price_reaction(r, dom)
        p_got = BB.react_ref(r, dom)
        mp2 = {'QUIET': 0, 'UP': 1, 'DOWN': 2, 'UNKNOWN': -1}
        bad += int(not np.array_equal(np.array([mp2[x] for x in p_ref]), p_got))
    put('classification_codes_vs_tools', bad == 0, cases=600, mismatches=bad)
    put('nan_r_not_quiet', bool(BB.react_ref(np.array([np.nan, 0.0, 0.01]), np.ones(3, bool))[0] == -1), cases=1, mismatches=0)
    df = pd.DataFrame(ROWS)
    p = M.P('stageN', 'B3_prelim', 'tests', 'b3_kernel_tests.csv')
    M.atomic_write_csv(p, df)
    ok = bool((df.status == 'PASS').all())
    M.write_receipt(os.environ.get('E6M_TASK', 'N8_b3_kernel_tests'), [p], status='SUCCEEDED' if ok else 'FAILED',
                    code=[__file__, K.__file__, B.__file__, BB.__file__], wall_s=round(time.time() - t0, 1))
    print(df.to_string(index=False), flush=True)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
