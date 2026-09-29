# -*- coding: utf-8 -*-
"""E6k 风险透镜（plan §10.3；E6j supplement_1 S3 同构造，只 import e6j_supp1_seg.smb_series / hac_ols，不改）。一段一个进程，封存之后运行。
  SMB   d_t（子 − 同 H 原父 8bp 日配对）对 SMB_t 回归（SMB = 前一日流通市值五分组等权最小组 − 最大组的当日 vwap 收益；universe = 前一日 clean 域 /
        前一日 pool0）：α（×252×100）、β、Bartlett(L = 5) HAC SE、R²、n；α / D 只作描述（不把"截距占比"说成"不是 size"）
  TAILS clean 域 z_T 分桶（小盘 ≤ .3 / 中段 / 大盘 > .7 / 未知）的滚动持仓资本份额与 gross 贡献（子、父、差）；d_t 最差 1% 日期（描述性风险账本，不作门）
对象：144 主展示 + 四 C1_hi + 六 SM 锚。输出 diagnostics/risk/<段>_{smb,tails}.csv。"""
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
    import e6j_supp1_seg as SUP
    seg = E.Seg(pname)
    S, ci = seg.S, seg.ci
    T = seg.T
    cl = S.clean.reindex(index=S.pool0.index, columns=S.pool0.columns).fillna(0).values == 1
    smb_all, _ = SUP.smb_series(S, cl)
    smb_p0, _ = SUP.smb_series(S, S.pool0.values == 1)
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    D = D[D.primary144 | D.c1_hi | D.sm_anchor]
    arr, bits, n = {}, {}, None
    for f in glob.glob(K.P('accounts', pname, '*.npz')):
        if os.path.basename(f).startswith('weights_'):
            continue
        z = K.npz(f)
        n = int(z['n_cells'][0])
        for i, did in enumerate(map(str, z['desc'])):
            arr[did] = z['d_net8'][i]
        for j, tid in enumerate(map(str, z['targets'])):
            bits[tid] = z['bits'][j]
    dates = np.array([str(d)[:10] for d in seg.dates])
    rows_s, rows_t = [], []
    zb = np.full(seg.zc.shape, 3, np.int64)
    zb[np.isfinite(seg.zc) & (seg.zc <= 0.3)] = 0
    zb[np.isfinite(seg.zc) & (seg.zc > 0.3) & (seg.zc <= 0.7)] = 1
    zb[np.isfinite(seg.zc) & (seg.zc > 0.7)] = 2
    r0 = S.r0

    def bucket_ledger(tid, H):
        kept = np.unpackbits(bits[tid])[:n].astype(bool)
        ids = np.flatnonzero(kept)
        t, c = ci.t[ids], ci.c[ids]
        w = seg.SE.dev(t, c)
        cap = np.zeros((4, T))
        grs = np.zeros((4, T))
        for lag in range(H):
            tt = t + lag
            ok_ = tt < T
            b = zb[tt[ok_], c[ok_]]
            np.add.at(cap, (b, tt[ok_]), w[ok_] / H)
            tr = t + lag + 2
            ok2 = tr < T
            b2 = zb[np.minimum(t[ok2] + lag, T - 1), c[ok2]]
            np.add.at(grs, (b2, tr[ok2]), w[ok2] * r0[tr[ok2], c[ok2]] / H)
        return cap, grs
    for r in D.itertuples():
        H = int(r.H)
        par = 'K0|%s|a0|H%d|PARENT' % (r.mother, H)
        d = arr[r.desc_id] - arr[par]
        for uni, smb in (('clean_full', smb_all), ('pool0', smb_p0)):
            rr = SUP.hac_ols(d, smb)
            f = np.isfinite(d)
            Dm = float(np.mean(d[f])) * K.ANN if f.any() else np.nan
            rows_s.append(dict(segment=pname, desc_id=r.desc_id, universe=uni, alpha_ann=rr['alpha'] * K.ANN, beta=rr['beta'],
                               se_alpha_ann=rr['se_alpha'] * K.ANN, se_beta=rr['se_beta'], r2=rr['r2'], n=rr['n'], D_ann=Dm,
                               alpha_over_D=(rr['alpha'] * K.ANN / Dm) if (Dm and np.isfinite(Dm) and Dm != 0) else np.nan))
        cc_, gc_ = bucket_ledger(r.target_id, H)
        cp_, gp_ = bucket_ledger('K0|%s|a0|PARENT' % r.mother, H)
        tot_c, tot_p = cc_.sum(0), cp_.sum(0)
        for bi, bn in enumerate(('small30', 'mid', 'large30', 'unknown')):
            with np.errstate(divide='ignore', invalid='ignore'):
                sc = np.where(tot_c > 0, cc_[bi] / tot_c, np.nan)
                sp = np.where(tot_p > 0, cp_[bi] / tot_p, np.nan)
            m = np.isfinite(sc) & np.isfinite(sp)
            rows_t.append(dict(segment=pname, desc_id=r.desc_id, bucket=bn, capital_share_child=float(np.nanmean(sc)),
                               capital_share_parent=float(np.nanmean(sp)), capital_share_delta=float(np.mean(sc[m] - sp[m])) if m.any() else np.nan,
                               gross_contrib_child_ann=float(np.mean(gc_[bi])) * K.ANN, gross_contrib_parent_ann=float(np.mean(gp_[bi])) * K.ANN,
                               gross_contrib_delta_ann=float(np.mean(gc_[bi] - gp_[bi])) * K.ANN))
        f = np.isfinite(d)
        if f.sum() > 100:
            k = max(1, int(round(0.01 * f.sum())))
            worst = np.argsort(np.where(f, d, np.inf))[:k]
            rows_t.append(dict(segment=pname, desc_id=r.desc_id, bucket='worst1pct_days', tail_dates='|'.join(dates[worst]),
                               tail_mean_d_bp=float(np.mean(d[worst])) * 1e4))
    od = K.P('diagnostics', 'risk')
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, '%s_smb.csv' % pname)
    p2 = os.path.join(od, '%s_tails.csv' % pname)
    K.atomic_write_csv(p1, pd.DataFrame(rows_s))
    K.atomic_write_csv(p2, pd.DataFrame(rows_t))
    K.write_receipt('risk_%s' % pname, [p1, p2], 'SUCCEEDED', n_smb=len(rows_s), n_tails=len(rows_t))
    print(pname, 'risk', len(rows_s), len(rows_t), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
