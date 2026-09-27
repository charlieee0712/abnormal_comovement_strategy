# -*- coding: utf-8 -*-
"""e6j_random._pick_levels 向量化版 vs 原逐需求循环版（参考实现）在合成数据上的逐位对照（选中集合与 shortfall）。"""
import e6j_boot  # noqa: F401
import sys
import numpy as np
import e6j_core as J
import e6j_random as R


def ref_pick(cand_rows, cand_cols, cand_keys, need_rows, need_keys, u_c):
    taken = np.zeros(len(cand_rows), bool)
    need_left = np.ones(len(need_rows), bool)
    for L in range(len(cand_keys)):
        if not need_left.any():
            break
        nk = need_keys[L][need_left]
        qk, qcnt = np.unique(nk, axis=0, return_counts=True)
        quota_map = {tuple(k): int(c) for k, c in zip(qk, qcnt)}
        avail = np.flatnonzero(~taken)
        byk = {}
        for i in avail:
            byk.setdefault(tuple(cand_keys[L][i]), []).append(i)
        got = {}
        for k, lst in byk.items():
            q = quota_map.get(k, 0)
            lst = sorted(lst, key=lambda i: (-u_c[i], i))
            take = lst[:q]
            taken[take] = True
            got[k] = len(take)
        for j in np.flatnonzero(need_left):
            k = tuple(need_keys[L][j])
            if got.get(k, 0) > 0:
                got[k] -= 1; need_left[j] = False
    short = np.bincount(need_rows[need_left]) if need_left.any() else np.zeros(0, dtype=np.int64)
    return np.flatnonzero(taken), short


def main():
    g = J.rng_for('E6j', 'test_pick')
    bad = 0
    for trial in range(200):
        T = int(g.integers(3, 12)); nc = int(g.integers(20, 200)); nn = int(g.integers(0, 60))
        cr = g.integers(0, T, nc); cc = g.integers(0, 50, nc)
        ind_c = g.integers(-1, 5, nc); k_c = g.integers(0, 3, nc)
        nr = g.integers(0, T, nn); ind_n = g.integers(-1, 5, nn); k_n = g.integers(0, 3, nn)
        ck = [np.stack([cr, ind_c, k_c], 1), np.stack([cr, k_c], 1), np.stack([cr, ind_c], 1), cr[:, None]]
        nk = [np.stack([nr, ind_n, k_n], 1), np.stack([nr, k_n], 1), np.stack([nr, ind_n], 1), nr[:, None]]
        u = g.random(nc)
        a1, s1 = R._pick_levels(cr, cc, ck, nr, nk, u)
        a2, s2 = ref_pick(cr, cc, ck, nr, nk, u)
        n = max(len(s1), len(s2))
        s1p = np.pad(s1, (0, n - len(s1))); s2p = np.pad(s2, (0, n - len(s2)))
        if not (np.array_equal(np.sort(a1), np.sort(a2)) and np.array_equal(s1p, s2p)):
            bad += 1
    print('trials 200, mismatches', bad)
    return 0 if bad == 0 else 2


if __name__ == '__main__':
    sys.exit(main())
