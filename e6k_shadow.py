# -*- coding: utf-8 -*-
"""E6k 实施影子账户（plan §12.3 / §8.4；E6j diag_p SHADOW 同式：e6g_c.ShadowCtx / target_weights / shadow_account，只 import 不改）。
对象（登记 shadow = True，160 个 / 段）：144 主展示、六形态原父 H5、四条 C1_hi、六形态旧 K 的 HG_ONLY10 × H5。
三视图：源引擎（账户本身，已在 accounts）/ 同一库存模型下全可成交（ideal）/ 源限制影子（X1：买卖标志，买不到留现金、卖不掉继续持仓，
H 到期不代表库存消失）。一段一个进程；两后段须 seal_post 之后（brief §5 A2 次序）。目标权重由位图 + DEV 确定性重算（A3-12 锚）。
输出 diagnostics/shadow/<段>.csv：逐对象 × 视图的超额年化、未成交买 / 卖、被困库存均值；子 − 父（同视图同 H）另列。"""
import e6k_boot  # noqa: F401
import os
import sys
import glob
import argparse

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_seal as SEAL


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    pname = a.segment
    ok, bad = SEAL.verify('deriv' if pname in K.DERIV_SEGS else 'post')
    if not ok:
        raise RuntimeError('封存核对失败：%s' % bad[:5])
    import e6k_env as E
    import e6g_c as GC
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    D = D[D.shadow]
    seg = E.Seg(pname)
    S = seg.S
    SC = GC.ShadowCtx(S)
    bits, n = {}, None
    for f in sorted(glob.glob(K.P('accounts', pname, '*.npz'))):
        if os.path.basename(f).startswith('weights_'):
            continue
        z = K.npz(f)
        n = int(z['n_cells'][0])
        for j, tid in enumerate(map(str, z['targets'])):
            bits[tid] = z['bits'][j]
    T = seg.T
    rows = []
    cache = {}

    def acct(tid, H):
        if (tid, H) in cache:
            return cache[(tid, H)]
        kept = np.unpackbits(bits[tid])[:n].astype(bool)
        ids = np.flatnonzero(kept)
        t, c = seg.ci.t[ids], seg.ci.c[ids]
        w = seg.SE.dev(t, c)
        order = np.argsort(t, kind='stable')
        ts = t[order]
        bnd = np.searchsorted(ts, np.arange(T + 1))
        idx = [c[order[bnd[d]:bnd[d + 1]]] for d in range(T)]
        val = [w[order[bnd[d]:bnd[d + 1]]] for d in range(T)]
        W = GC.target_weights(S, idx, val, H)
        res = {}
        for mode in ('ideal', 'X1'):
            sh = GC.shadow_account(SC, W, mode=mode)
            res[mode] = sh
        cache[(tid, H)] = res
        return res
    for r in D.itertuples():
        H = int(r.H)
        res = acct(r.target_id, H)
        par = 'K0|%s|a0|PARENT' % r.mother
        pres = acct(par, H) if r.op != 'PARENT' else None
        for mode, sh in res.items():
            ex = sh['excess']
            row = dict(segment=pname, desc_id=r.desc_id, view=mode, excess_ann=float(np.nanmean(ex)) * K.ANN,
                       unfilled_buy=float(np.nansum(sh['unfilled_buy'])), unfilled_sell=float(np.nansum(sh['unfilled_sell'])),
                       trapped_mean=float(np.nanmean(sh['trapped'])), capital_basis='constant_notional', corporate_action='源复权价路径（E6g）',
                       terminal_inventory=float(sh['hold'][np.isfinite(sh['hold'])][-1]) if np.isfinite(sh['hold']).any() else np.nan)
            if pres is not None:
                pe = pres[mode]['excess']
                m = np.isfinite(ex) & np.isfinite(pe)
                row['child_minus_parent_ann'] = float(np.mean(ex[m] - pe[m])) * K.ANN if m.any() else np.nan
            rows.append(row)
    od = K.P('diagnostics', 'shadow')
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, '%s.csv' % pname)
    K.atomic_write_csv(p, pd.DataFrame(rows))
    K.write_receipt('shadow_%s' % pname, [p], 'SUCCEEDED', n=len(rows))
    print('%s shadow：%d 行' % (pname, len(rows)), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
