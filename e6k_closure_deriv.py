# -*- coding: utf-8 -*-
"""E6k 推导段闭包核（seal_deriv 之后；附录 A6-3 / A3-12 足额样本 + A4-6 COMMON_SUPPORT 齐全 + 登记对象全有账户）。
  A6-3  抽 500 个描述符：逐日 net8 = gross − 8e−4·turn（机械恒等，不是收益读数）
  A3-12 抽 200 个目标：位图 → DEV → 稀疏账本重算 wsum / nnames / 首个 H 的 net8 = 已存（≤ 1e−12）
  A4-6  COMMON_SUPPORT 子 1,800 / 父 176（每段）齐全；四账户桥逐日闭合（(C1−C0)+(C0−N0)+(N1−C1) = N1−N0）
  闭包  每段 39,142 登记描述符 + 附属（72 + 288 + 1,976）全有账户行"""
import e6k_boot  # noqa: F401
import os
import sys
import glob
import json

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_seal as SEAL


def main():
    ok, bad = SEAL.verify('deriv')
    if not ok:
        raise RuntimeError('seal_deriv 核对失败：%s' % bad[:5])
    import e6k_env as E
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    A = pd.read_csv(K.P('registry', 'accessory_E6k.csv'))
    rows = []

    def chk(cid, seg, what, ok_, detail=''):
        rows.append(dict(check_id=cid, segment=seg, what=what, status='PASS' if ok_ else 'FAIL', detail=str(detail)[:300]))
    for pname in K.DERIV_SEGS:
        files = [f for f in sorted(glob.glob(K.P('accounts', pname, '*.npz'))) if not os.path.basename(f).startswith('weights_')]
        Z = {f: K.npz(f) for f in files}
        have = set()
        for z in Z.values():
            have |= set(map(str, z['desc']))
        need = set(D.desc_id) | set(A.acc_id)
        miss = sorted(need - have)
        chk('closure', pname, '登记描述符 + 附属全有账户行（%d）' % len(need), not miss, 'missing=%d %s' % (len(miss), miss[:3]))
        rng = np.random.default_rng(K.stable_seed_int('E6k.closure.deriv', pname) % (2 ** 63))
        allrows = [(f, i) for f, z in Z.items() for i in range(len(z['desc']))]
        pick = [allrows[i] for i in rng.choice(len(allrows), size=500, replace=False)]
        worst = 0.0
        for f, i in pick:
            z = Z[f]
            r = z['d_net8'][i] - (z['d_gross'][i] - 8e-4 * z['d_turn'][i])
            m = np.isfinite(r)
            worst = max(worst, float(np.max(np.abs(r[m]))) if m.any() else 0.0)
        chk('A6-3', pname, '费用恒等 net8 = gross − 8e−4·turn（抽 500 个描述符，逐日）', worst <= 1e-15, 'max|resid| = %.2e' % worst)
        seg = E.Seg(pname)
        tl = [(f, j) for f, z in Z.items() for j in range(len(z['targets']))]
        tp = [tl[i] for i in rng.choice(len(tl), size=200, replace=False)]
        worst = 0.0
        for f, j in tp:
            z = Z[f]
            n = int(z['n_cells'][0])
            kept = np.unpackbits(z['bits'][j])[:n].astype(bool)
            ids = np.flatnonzero(kept)
            t, c = seg.ci.t[ids], seg.ci.c[ids]
            w = seg.SE.dev(t, c)
            worst = max(worst, float(np.max(np.abs(np.bincount(t, weights=w, minlength=seg.T) - z['t_wsum'][j]))),
                        float(np.max(np.abs(np.bincount(t, minlength=seg.T) - z['t_nnames'][j]))))
            di = np.flatnonzero(z['desc_target'] == j)
            if len(di):
                H = int(z['desc_H'][di[0]])
                n8 = seg.SE.pnl(t, c, w, (H,), 8.0)[H][3]
                ref = z['d_net8'][di[0]]
                mm = np.isfinite(ref) & np.isfinite(n8)
                worst = max(worst, float(np.max(np.abs(n8[mm] - ref[mm]))) if mm.any() else 0.0,
                            0.0 if np.array_equal(np.isfinite(ref), np.isfinite(n8)) else 1.0)
        chk('A3-12', pname, '位图 + DEV 输入重算 wsum / nnames / 首个 H 的 net8 = 已存（抽 200 个目标）', worst <= 1e-12, 'max|Δ| = %.2e' % worst)
        cs = A[A.kind == 'COMMON_SUPPORT_CHILD']
        csp = A[A.kind == 'COMMON_SUPPORT_PARENT']
        chk('A4-6', pname, 'COMMON_SUPPORT 子 %d / 父 %d 齐全' % (len(cs), len(csp)), set(cs.acc_id) <= have and set(csp.acc_id) <= have)
        # 四账户桥逐日闭合（抽 100）
        worst = 0.0
        get = {}
        for z in Z.values():
            for i, did in enumerate(map(str, z['desc'])):
                get[did] = (z, i)
        for r in cs.sample(n=min(100, len(cs)), random_state=int(rng.integers(1 << 30))).itertuples():
            nat = r.acc_id[3:]
            par = 'K0|%s|a0|H%d|PARENT' % (r.mother, r.H)
            n1, n0 = get[nat][0]['d_net8'][get[nat][1]], get[par][0]['d_net8'][get[par][1]]
            c1, c0 = get[r.acc_id][0]['d_net8'][get[r.acc_id][1]], get[r.compare_to][0]['d_net8'][get[r.compare_to][1]]
            lhs = n1 - n0
            rhs = (c1 - c0) + (c0 - n0) + (n1 - c1)
            m = np.isfinite(lhs) & np.isfinite(rhs)
            worst = max(worst, float(np.max(np.abs(lhs[m] - rhs[m]))) if m.any() else 0.0)
        chk('A4-6', pname, '四账户桥逐日闭合（抽 100）', worst <= 1e-15, 'max|resid| = %.2e' % worst)
    df = pd.DataFrame(rows)
    p = K.P('checks', 'closure_deriv.csv')
    K.atomic_write_csv(p, df)
    ok = not (df.status == 'FAIL').any()
    K.write_receipt('closure_deriv', [p], 'SUCCEEDED' if ok else 'FAILED', counts=df.status.value_counts().to_dict())
    print(df.to_string(max_colwidth=90), flush=True)
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
