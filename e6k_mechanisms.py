# -*- coding: utf-8 -*-
"""E6k 机制账户（plan §6.1 / §6.3 / §10.1 / §12.1；E6K-Q05 / Q06；两后段封存之后运行，一段一个进程 + 合并）。
  SHAPLEY   八子集条件置换（24 个 NATIVE 主配置）：v(集合) = 该条件下随机路径均值（gross / net8 年化，fee = gross − net8）；
            I / S / K 三变量六种顺序平均的 Shapley 差（只是"改变置换条件的算法效应"，不是因果份额，plan §10.1）；另报可移动份额与置换熵
  LXGROSS   LX 对象（α .25 × H5）的 gross 特征匹配账本（§6.1）：形成日 τ 冻结层 g 与合法域成员，组参考收益 r_group(g, τ, k) = 固定成员等权；
            Δgross_k = Σ_i δw_i (r_i − r_group_i) + Σ_g δW_g r_group_g（逐日闭合；成本不分摊，完整账户另收）；子 = LX / NATIVE，父 = 原父
  CAPITAL   §12.1 资本分解：两边都有仓的日子 E = P·u，ΔE = .5(Pc + Pb)(uc − ub) + .5(uc + ub)(Pc − Pb)；一边零仓日单列
写 diagnostics/mechanisms/<段>_*.csv。"""
import e6k_boot  # noqa: F401
import os
import sys
import glob
import argparse
import itertools

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_seal as SEAL

SUBS = ('EMPTY', 'I', 'S', 'K', 'IS', 'IK', 'SK', 'ISK')


def shapley(pname):
    rows = []
    vals = {}
    for sub in SUBS:
        mech = 'NEW_COND_ISK_P5' if sub == 'ISK' else 'EIGHT_SUBSET_' + sub
        for f in glob.glob(K.P('randoms', mech, pname, '*.npz')):
            z = K.npz(f)
            for i, (did, H) in enumerate(zip(map(str, z['desc']), z['H'])):
                if not did.endswith('|NATIVE') or int(H) != 5:
                    continue
                g, n = z['ann'][i, :, 1], z['ann'][i, :, 0]
                key = (did, sub)
                acc = vals.setdefault(key, [0.0, 0.0, 0])
                acc[0] += float(np.nansum(g))
                acc[1] += float(np.nansum(n))
                acc[2] += int(np.isfinite(n).sum())
    objs = sorted(set(k[0] for k in vals))
    for did in objs:
        v = {}
        for sub in SUBS:
            if (did, sub) in vals:
                s = vals[(did, sub)]
                v[sub] = (s[0] / s[2], s[1] / s[2])
        if len(v) < 8:
            continue
        key = lambda st: 'EMPTY' if not st else ''.join(x for x in 'ISK' if x in st)
        phi = {x: np.zeros(2) for x in 'ISK'}
        for order in itertools.permutations('ISK'):
            cur = set()
            for x in order:
                a, b = np.array(v[key(cur)]), np.array(v[key(cur | {x})])
                phi[x] += (b - a) / 6.0
                cur |= {x}
        r = dict(segment=pname, desc_id=did, **{'rand_net_%s' % s: v[s][1] for s in SUBS}, **{'rand_gross_%s' % s: v[s][0] for s in SUBS})
        for x in 'ISK':
            r['shapley_gross_%s' % x], r['shapley_net_%s' % x] = phi[x]
            r['shapley_fee_%s' % x] = phi[x][0] - phi[x][1]
        r['closure_net'] = sum(phi[x][1] for x in 'ISK') - (v['ISK'][1] - v['EMPTY'][1])
        rows.append(r)
    return pd.DataFrame(rows)


def lx_gross(pname):
    import e6k_env as E
    import e6k_ops as O
    seg = E.Seg(pname)
    ci, S = seg.ci, seg.S
    T = seg.T
    r0 = S.r0
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    L = D[(D.family == 'LX') & (D.alpha == 0.25) & (D.H == 5)]
    bits, n = {}, None
    for f in glob.glob(K.P('accounts', pname, '*.npz')):
        if os.path.basename(f).startswith('weights_'):
            continue
        z = K.npz(f)
        n = int(z['n_cells'][0])
        for j, tid in enumerate(map(str, z['targets'])):
            bits[tid] = z['bits'][j]
    rows = []
    H = 5
    for r in L.itertuples():
        st = seg.struct(r.mother)
        lay = 'SIZE3' if 'SIZE3' in r.op else 'ISK'
        layers = O.lx_layers(seg, st.q0, lay)
        legal = st.legal()
        for child_tid in (r.target_id, '%s|%s|a0.25|NATIVE' % (r.meas, r.mother)):
            kc = np.unpackbits(bits[child_tid])[:n].astype(bool)
            kp = np.unpackbits(bits['K0|%s|a0|PARENT' % r.mother])[:n].astype(bool)
            wc, wp = np.zeros(n), np.zeros(n)
            for k_, w_ in ((kc, wc), (kp, wp)):
                ids = np.flatnonzero(k_)
                w_[ids] = seg.SE.dev(ci.t[ids], ci.c[ids])
            dw = wc - wp
            g = layers.astype(np.int64)
            G = int(g.max()) + 1
            key = ci.t.astype(np.int64) * G + g
            within = np.zeros(T)
            alloc = np.zeros(T)
            total = np.zeros(T)
            bterm = np.zeros(T)
            bench = np.nan_to_num(np.asarray(S.bench, float))
            lm = legal
            for lag in range(2, H + 2):
                tt = ci.t + lag
                ok = tt < T
                ret = np.zeros(n)
                ret[ok] = r0[tt[ok], ci.c[ok]]
                sums = np.bincount(key[lm & ok], weights=ret[lm & ok], minlength=T * G)
                cnts = np.bincount(key[lm & ok], minlength=T * G)
                rg = np.where(cnts > 0, sums / np.maximum(cnts, 1), 0.0)[key]
                contrib_w = dw * (ret - rg) / H
                contrib_a = dw * rg / H
                idx = np.flatnonzero(ok & (dw != 0))
                np.add.at(within, tt[idx], contrib_w[idx])
                np.add.at(alloc, tt[idx], contrib_a[idx])
                np.add.at(total, tt[idx], (dw * ret / H)[idx])
                bk = np.zeros(n)
                bk[ok] = bench[tt[ok]]
                np.add.at(bterm, tt[idx], (dw * bk / H)[idx])
            rows.append(dict(segment=pname, desc_id=r.desc_id, child=child_tid, within_group_ann=float(np.mean(within)) * K.ANN,
                             allocation_ann=float(np.mean(alloc)) * K.ANN, total_ann=float(np.mean(total)) * K.ANN,
                             allocation_excess_ann=float(np.mean(alloc - bterm)) * K.ANN, total_excess_ann=float(np.mean(total - bterm)) * K.ANN,
                             closure_resid=float(np.max(np.abs(within + alloc - total)))))
    return pd.DataFrame(rows)


def capital(pname):
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    keep = set(D[D.primary144 | D.c1_hi | D.sm_anchor | ((D.alpha == 0.25) & (D.H == 5))].desc_id)
    arr = {}
    for f in glob.glob(K.P('accounts', pname, '*.npz')):
        if os.path.basename(f).startswith('weights_'):
            continue
        z = K.npz(f)
        for i, did in enumerate(map(str, z['desc'])):
            if did in keep or did.endswith('|PARENT'):
                arr[did] = (z['d_gross'][i], z['d_pos'][i])
    rows = []
    for did in sorted(keep):
        if did not in arr or did.endswith('|PARENT'):
            continue
        p = did.split('|')
        par = 'K0|%s|a0|%s|PARENT' % (p[1], p[3])
        (Ec, Pc), (Eb, Pb) = arr[did], arr[par]
        both = (Pc > 0) & (Pb > 0) & np.isfinite(Ec) & np.isfinite(Eb)
        uc = np.where(both, Ec / np.where(Pc > 0, Pc, 1), 0.0)
        ub = np.where(both, Eb / np.where(Pb > 0, Pb, 1), 0.0)
        sel = np.where(both, 0.5 * (Pc + Pb) * (uc - ub), 0.0)
        cap = np.where(both, 0.5 * (uc + ub) * (Pc - Pb), 0.0)
        one = ((Pc > 0) ^ (Pb > 0))
        rows.append(dict(segment=pname, desc_id=did, selection_ann=float(np.mean(sel)) * K.ANN, capital_ann=float(np.mean(cap)) * K.ANN,
                         both_days=int(both.sum()), one_sided_days=int(one.sum()),
                         one_sided_dE_ann=float(np.nanmean(np.where(one, np.nan_to_num(Ec) - np.nan_to_num(Eb), 0.0))) * K.ANN))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    pname = a.segment
    ok, bad = SEAL.verify('deriv' if pname in K.DERIV_SEGS else 'post')
    if not ok:
        raise RuntimeError('封存核对失败：%s' % bad[:5])
    od = K.P('diagnostics', 'mechanisms')
    os.makedirs(od, exist_ok=True)
    outs = []
    for nm, fn in (('shapley', shapley), ('capital', capital), ('lx_gross', lx_gross)):
        df = fn(pname)
        p = os.path.join(od, '%s_%s.csv' % (pname, nm))
        K.atomic_write_csv(p, df)
        outs.append(p)
        print(pname, nm, len(df), flush=True)
    K.write_receipt('mechanisms_%s' % pname, outs, 'SUCCEEDED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
