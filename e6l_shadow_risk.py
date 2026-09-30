# -*- coding: utf-8 -*-
"""E6l 影子与风险透镜（plan §8.3 / §8.4 / §10.2；E6k e6k_shadow / e6k_risk 同式，只 import e6g_c / e6j_supp1_seg 不改）。seal 之后，一段一个进程。
  影子（shadow = True 的登记对象：主展示 72、α .5 剂量 72、旧 K 规则控制 H5、Q0 / C1 × NATIVE / HG10 α .25 H5）：
     三视图 = 源引擎（账户本身）/ 同库存模型全可成交（ideal）/ 源限制影子（X1：买不到留现金、卖不掉继续持仓；H 到期不代表库存消失）；
     目标权重由 masks 位图 + DEV 确定性重算；子 − 同视图同 H 原父另列 → diagnostics/shadow/<段>.csv
  风险（主展示 72 + 剂量 72）：SMB 回归（universe clean / pool0；α ×252×100、β、HAC L5、R²）；size 分桶（小盘 ≤ .3 / 中 / 大 > .7 / 未知）
     滚动持仓资本份额与 gross 贡献（子、父、差）；日差最差 1% 日期 → diagnostics/risk/<段>_{smb,tails}.csv；另写 risk_tight_bounds 段行
     （组合层 PORT3_T 紧区间段均 lo / hi 与状态，固定表）"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import argparse

import numpy as np
import pandas as pd

import e6l_core as L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    pname = a.segment
    import e6l_seal as SEAL
    ok, bad = SEAL.verify('deriv' if pname in L.DERIV_SEGS else 'post')
    if not ok:
        raise RuntimeError('封存核对失败：%s' % bad[:5])
    if pname in L.POST_SEGS:
        L.post_gate(pname, 'shadow / risk')
    import e6l_env as V
    import e6g_c as GC
    import e6j_supp1_seg as SUP
    D = L.read_csv_keep(L.P('registry', 'descriptors_E6l.csv'))
    seg = V.SegL(pname, state=False)
    S, ci, T = seg.S, seg.ci, seg.T
    bits, arr, n = {}, {}, None
    for f in sorted(glob.glob(L.P('accounts', pname, '*.npz'))):
        if os.path.basename(f).startswith('weights_'):
            continue
        z = L.npz(f, keys=['targets', 'bits', 'n_cells', 'desc', 'd_net8'])
        n = int(z['n_cells'][0])
        for j, tid in enumerate(map(str, z['targets'])):
            bits[tid] = z['bits'][j]
        for i, did in enumerate(map(str, z['desc'])):
            arr[did] = z['d_net8'][i]
    SC = GC.ShadowCtx(S)
    cache = {}

    def lists(tid):
        kept = np.unpackbits(bits[tid])[:n].astype(bool)
        ids = np.flatnonzero(kept)
        t, c = ci.t[ids], ci.c[ids]
        return t, c, seg.SE.dev(t, c)

    def shadow(tid, H):
        if (tid, H) in cache:
            return cache[(tid, H)]
        t, c, w = lists(tid)
        order = np.argsort(t, kind='stable')
        ts = t[order]
        bnd = np.searchsorted(ts, np.arange(T + 1))
        idx = [c[order[bnd[d]:bnd[d + 1]]] for d in range(T)]
        val = [w[order[bnd[d]:bnd[d + 1]]] for d in range(T)]
        W = GC.target_weights(S, idx, val, H)
        res = {mode: GC.shadow_account(SC, W, mode=mode) for mode in ('ideal', 'X1')}
        cache[(tid, H)] = res
        return res
    rows = []
    for r in D[D.shadow.astype(str) == 'True'].itertuples():
        H = int(r.H)
        par = 'K0|%s|a0|NATIVE' % r.mother
        if r.target_id not in bits or par not in bits:
            continue
        res = shadow(r.target_id, H)
        pres = shadow(par, H)
        for mode, sh in res.items():
            ex = sh['excess']
            pe = pres[mode]['excess']
            m = np.isfinite(ex) & np.isfinite(pe)
            rows.append(dict(segment=pname, desc_id=r.desc_id, view=mode, excess_ann_pp=float(np.nanmean(ex)) * L.ANN,
                             unfilled_buy_notional=float(np.nansum(sh['unfilled_buy'])), unfilled_sell_notional=float(np.nansum(sh['unfilled_sell'])),
                             trapped_mean_notional=float(np.nanmean(sh['trapped'])),
                             child_minus_parent_ann_pp=float(np.mean(ex[m] - pe[m])) * L.ANN if m.any() else np.nan,
                             capital_basis='constant_notional', corporate_action='源复权价路径（E6g）'))
    od = L.P('diagnostics', 'shadow')
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, '%s.csv' % pname)
    L.atomic_write_csv(p1, pd.DataFrame(rows))
    # 风险
    cl = S.clean.reindex(index=S.pool0.index, columns=S.pool0.columns).fillna(0).values == 1
    smb_all, _ = SUP.smb_series(S, cl)
    smb_p0, _ = SUP.smb_series(S, S.pool0.values == 1)
    zb = np.full(seg.zc.shape, 3, np.int64)
    zb[np.isfinite(seg.zc) & (seg.zc <= 0.3)] = 0
    zb[np.isfinite(seg.zc) & (seg.zc > 0.3) & (seg.zc <= 0.7)] = 1
    zb[np.isfinite(seg.zc) & (seg.zc > 0.7)] = 2
    r0 = S.r0
    dates = np.array([str(x)[:10] for x in seg.dates])

    def bucket_ledger(tid, H):
        t, c, w = lists(tid)
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
    rs, rt = [], []
    Dr = D[(D.primary72.astype(str) == 'True') | (D.dose72.astype(str) == 'True')]
    for r in Dr.itertuples():
        H = int(r.H)
        par_d = 'K0|%s|a0|H%d|NATIVE' % (r.mother, H)
        if r.desc_id not in arr or par_d not in arr:
            continue
        d = arr[r.desc_id] - arr[par_d]
        for uni, smb in (('clean_full', smb_all), ('pool0', smb_p0)):
            rr = SUP.hac_ols(d, smb)
            f = np.isfinite(d)
            Dm = float(np.mean(d[f])) * L.ANN if f.any() else np.nan
            rs.append(dict(segment=pname, desc_id=r.desc_id, universe=uni, alpha_ann_pp=rr['alpha'] * L.ANN, beta=rr['beta'], se_alpha_ann_pp=rr['se_alpha'] * L.ANN,
                           se_beta=rr['se_beta'], r2=rr['r2'], n=rr['n'], D_ann_pp=Dm))
        cc_, gc_ = bucket_ledger(r.target_id, H)
        cp_, gp_ = bucket_ledger('K0|%s|a0|NATIVE' % r.mother, H)
        tot_c, tot_p = cc_.sum(0), cp_.sum(0)
        for bi, bn in enumerate(('small30', 'mid', 'large30', 'unknown')):
            with np.errstate(divide='ignore', invalid='ignore'):
                sc = np.where(tot_c > 0, cc_[bi] / tot_c, np.nan)
                sp = np.where(tot_p > 0, cp_[bi] / tot_p, np.nan)
            m = np.isfinite(sc) & np.isfinite(sp)
            rt.append(dict(segment=pname, desc_id=r.desc_id, bucket=bn, capital_share_child=float(np.nanmean(sc)), capital_share_parent=float(np.nanmean(sp)),
                           capital_share_delta=float(np.mean(sc[m] - sp[m])) if m.any() else np.nan, gross_contrib_child_ann_pp=float(np.mean(gc_[bi])) * L.ANN,
                           gross_contrib_parent_ann_pp=float(np.mean(gp_[bi])) * L.ANN, gross_contrib_delta_ann_pp=float(np.mean(gc_[bi] - gp_[bi])) * L.ANN))
        f = np.isfinite(d)
        if f.sum() > 100:
            k = max(1, int(round(0.01 * f.sum())))
            worst = np.argsort(np.where(f, d, np.inf))[:k]
            rt.append(dict(segment=pname, desc_id=r.desc_id, bucket='worst1pct_days', tail_dates='|'.join(dates[worst]), tail_mean_d_bp=float(np.mean(d[worst])) * 1e4))
    od2 = L.P('diagnostics', 'risk')
    os.makedirs(od2, exist_ok=True)
    p2 = os.path.join(od2, '%s_smb.csv' % pname)
    p3 = os.path.join(od2, '%s_tails.csv' % pname)
    L.atomic_write_csv(p2, pd.DataFrame(rs))
    L.atomic_write_csv(p3, pd.DataFrame(rt))
    L.write_receipt(L.next_rerun('shadow_risk_%s' % pname), [p1, p2, p3], 'SUCCEEDED', shadow=len(rows), smb=len(rs), tails=len(rt))
    print('%s shadow %d / smb %d / tails %d' % (pname, len(rows), len(rs), len(rt)), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
