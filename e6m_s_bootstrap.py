# -*- coding: utf-8 -*-
"""E6m bootstrap（plan §9.5；e6l_bootstrap 同式，比较集 = registry/comparison_manifest_E6m.csv，另加 plan §9.5 的联合可估性规则）。
- 抽样：四历史段内分层 stationary（Politis–Romano，几何块长均值 L ∈ {20, 60}，段内环绕，不跨段接缝），每 L 各 NB 次。
  全部比较共享同一套段内索引（rng_for('E6m', 'bootstrap', L, 段)）；抽已生成的逐日配对 PnL，原日历行与缺失掩码一起抽，不回喂引擎。
  FULL* = Σ_s num*_s / Σ_s den*_s × 252 × 100。
- 同时带：集合 = all / 每个视图族 / 主 72（左端为主 72 描述符）。q95_maxabs_t = 中心化最大标准化偏差 max_j |(D*_bj − D̂_j)/SE_j| 的 95% 分位；
  每行半宽 = q × SE_j。另印单侧 q95_max_t / q05_min_t。
- plan §9.5：集合内任一比较在某 draw 无支持（den* = 0）→ 该集合标 JOINT_BAND_NOT_ESTIMABLE（不用 nanmax 改域）；
  另在"全部 draw 都可估"的交集上印 COMMON_ESTIMABLE_SUBFAMILY 敏感行（不替原族）。SE = 0 的恒等比较单列 ZERO_SE_IDENTITY。
用法：--acc <账户目录> --out <输出目录> [--nb 2000]（B2 开发期在合成账本上跑通）。不设 FWER / 同时带准入门。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
import e6j_stats as ST

LS = (20, 60)
SEGS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')
DERIV, POST = SEGS[:2], SEGS[2:]


def seg_counts(T, Lb, seg, NB):
    rng = M.rng_for('E6m', 'bootstrap', int(Lb), seg)
    C = np.zeros((NB, T), np.float64)
    for b in range(NB):
        C[b] = np.bincount(ST.stationary_indices(T, Lb, rng), minlength=T)
    return C


def load_net8(acc, seg):
    import e6m_s_stats as SS                                        # 真实账户连同 accounts_aux 一起读（同 e6m_s_stats.load）
    out = {}
    for ad in SS.acc_dirs(acc):
        for f in sorted(glob.glob(os.path.join(ad, seg, '*.npz'))):
            if os.path.basename(f).startswith('weights_'):
                continue
            z = np.load(f, allow_pickle=False)
            for did, x in zip([str(v) for v in z['desc']], z['d_net8']):
                out[did] = x
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--acc', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--nb', type=int, default=2000)
    ap.add_argument('--chunk', type=int, default=8000)
    a = ap.parse_args()
    t0 = time.time()
    import e6m_s_seal as SEAL                                       # 四段都读：两个封存门各核一次（合成 / 开发目录不拦）
    for s in (M.DERIV_SEGS[0], M.POST_SEGS[0]):
        SEAL.require_for(a.acc, s)
    NB = a.nb
    CM = M.read_csv_keep(M.P('registry', 'comparison_manifest_E6m.csv'), dtype=str)
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    p72 = set(D[D.is_primary72 == 'True'].desc_id)
    BB = pd.DataFrame(dict(comparison_id=CM.comparison_id, family=CM.view, a=CM.left_desc_id, b=CM.right_desc_id,
                           primary72=CM.left_desc_id.isin(p72)))
    nets = {s: load_net8(a.acc, s) for s in SEGS}
    Ts = {s: len(next(iter(nets[s].values()))) for s in SEGS}
    counts = {(s, Lb): seg_counts(Ts[s], Lb, s, NB) for s in SEGS for Lb in LS}
    rows = []
    agg = {Lb: {} for Lb in LS}
    for c0 in range(0, len(BB), a.chunk):
        sub = BB.iloc[c0:c0 + a.chunk]
        Dseg = {}
        en = np.zeros(len(sub))
        ed = np.zeros(len(sub))
        for s in SEGS:
            Mx = np.zeros((Ts[s], len(sub)))
            V = np.zeros((Ts[s], len(sub)))
            for j, r in enumerate(sub.itertuples()):
                x, y = nets[s].get(r.a), nets[s].get(r.b)
                if x is None or y is None:
                    continue
                dd = x - y
                v = np.isfinite(dd)
                Mx[v, j] = dd[v]
                V[v, j] = 1.0
            en += Mx.sum(0)
            ed += V.sum(0)
            Dseg[s] = (Mx, V)
        est = np.where(ed > 0, en / np.where(ed > 0, ed, 1) * ST.ANN, np.nan)
        for Lb in LS:
            parts = {s: (counts[(s, Lb)] @ Dseg[s][0], counts[(s, Lb)] @ Dseg[s][1]) for s in SEGS}
            for grp, segs_ in (('DERIV', DERIV), ('POST', POST)):
                gn = sum(parts[s][0] for s in segs_)
                gd = sum(parts[s][1] for s in segs_)
                with np.errstate(divide='ignore', invalid='ignore'):
                    gdr = np.where(gd > 0, gn / gd * ST.ANN, np.nan)
                gen = sum(Dseg[s][0].sum(0) for s in segs_)
                ged = sum(Dseg[s][1].sum(0) for s in segs_)
                gest = np.where(ged > 0, gen / np.where(ged > 0, ged, 1) * ST.ANN, np.nan)
                with np.errstate(all='ignore'):
                    gq = np.nanpercentile(gdr, [2.5, 97.5], axis=0)
                    gse = np.nanstd(gdr, axis=0, ddof=1)
                for j, r in enumerate(sub.itertuples()):
                    rows.append(dict(comparison_id=r.comparison_id, family=r.family, L=Lb, scope=grp, est_ann_pp=gest[j], q025_ann_pp=gq[0, j],
                                     q975_ann_pp=gq[1, j], se_ann_pp=float(gse[j]), no_support_draws=int((gd[:, j] <= 0).sum())))
            num = sum(parts[s][0] for s in SEGS)
            den = sum(parts[s][1] for s in SEGS)
            with np.errstate(divide='ignore', invalid='ignore'):
                draws = np.where(den > 0, num / den * ST.ANN, np.nan)
            nosup = (den <= 0).sum(0)
            with np.errstate(all='ignore'):
                se = np.nanstd(draws, axis=0, ddof=1)
                q = np.nanpercentile(draws, [2.5, 50, 97.5], axis=0)
            zero = np.isfinite(se) & (se == 0.0)
            for j, r in enumerate(sub.itertuples()):
                rows.append(dict(comparison_id=r.comparison_id, family=r.family, L=Lb, scope='FULL', est_ann_pp=est[j], q025_ann_pp=q[0, j],
                                 q50_ann_pp=q[1, j], q975_ann_pp=q[2, j], se_ann_pp=float(se[j]), no_support_draws=int(nosup[j]), zero_se=bool(zero[j])))
            ok_ = np.isfinite(se) & (se > 0) & (nosup == 0)
            z = (draws - est[None, :]) / np.where(ok_, se, 1.0)[None, :]
            groups = {'all': np.ones(len(sub), bool), 'primary72': sub.primary72.values}
            for fam in np.unique(sub.family.values):
                groups['family_' + fam] = sub.family.values == fam
            for nm, msk in groups.items():
                if not msk.any():
                    continue
                g = agg[Lb].setdefault(nm, dict(mx=[], smx=[], smn=[], n=0, n_est=0, n_zero=0, n_noest=0))
                g['n'] += int(msk.sum())
                g['n_zero'] += int((msk & zero).sum())
                g['n_noest'] += int((msk & ~ok_ & ~zero).sum())
                m2 = msk & ok_
                g['n_est'] += int(m2.sum())
                if m2.any():
                    g['mx'].append(np.max(np.abs(z[:, m2]), axis=1))
                    g['smx'].append(np.max(z[:, m2], axis=1))
                    g['smn'].append(np.min(z[:, m2], axis=1))
        M.log('bootstrap chunk %d / %d' % (c0 + len(sub), len(BB)))
    R = pd.DataFrame(rows)
    band = []
    for Lb in LS:
        for nm, g in agg[Lb].items():
            if not g['mx']:
                band.append(dict(L=Lb, set=nm, status='JOINT_BAND_NOT_ESTIMABLE', draws=NB, n_comparisons=g['n'], n_estimable=0, n_zero_se=g['n_zero']))
                continue
            mx = np.max(np.vstack(g['mx']), axis=0)
            smx = np.max(np.vstack(g['smx']), axis=0)
            smn = np.min(np.vstack(g['smn']), axis=0)
            q = dict(q95_maxabs_t=float(np.percentile(mx, 95)), q95_max_t=float(np.percentile(smx, 95)), q05_min_t=float(np.percentile(smn, 5)))
            if g['n_noest'] > 0:
                band.append(dict(L=Lb, set=nm, status='JOINT_BAND_NOT_ESTIMABLE', draws=NB, n_comparisons=g['n'], n_estimable=g['n_est'],
                                 n_zero_se=g['n_zero']))
                band.append(dict(L=Lb, set=nm, status='COMMON_ESTIMABLE_SUBFAMILY', draws=NB, n_comparisons=g['n'], n_estimable=g['n_est'],
                                 n_zero_se=g['n_zero'], **q))
            else:
                band.append(dict(L=Lb, set=nm, status='JOINT_BAND', draws=NB, n_comparisons=g['n'], n_estimable=g['n_est'], n_zero_se=g['n_zero'], **q))
    B = pd.DataFrame(band)
    full = R[R.scope == 'FULL'].copy()
    qall = B[(B.set == 'all') & B.status.isin(['JOINT_BAND', 'COMMON_ESTIMABLE_SUBFAMILY'])].set_index('L')
    full['q95_maxabs_t_all'] = full.L.map(qall.q95_maxabs_t)
    full['halfwidth_ann_pp_all'] = full.q95_maxabs_t_all * full.se_ann_pp
    full['band_status'] = np.where(full.no_support_draws > 0, 'INSUFFICIENT_REPLICATE_SUPPORT', np.where(full.zero_se, 'ZERO_SE_IDENTITY', 'IN_BAND_SET'))
    od = os.path.join(a.out, 'bootstrap')
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, 'bootstrap_comparisons.csv')
    M.atomic_write_csv(p1, pd.concat([full, R[R.scope != 'FULL']], ignore_index=True))
    p2 = os.path.join(od, 'simultaneous_band_q95.csv')
    M.atomic_write_csv(p2, B)
    M.write_receipt(os.environ.get('E6M_TASK', 'S_bootstrap'), [p1, p2], status='SUCCEEDED', code=[__file__, M.__file__], comparisons=len(BB), draws=NB,
                    generator='blake2b-128(canonical_json(E6m, bootstrap, L, segment)) -> SeedSequence -> PCG64; e6j_stats.stationary_indices',
                    wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(comparisons=len(BB), draws=NB, band_rows=len(B), statuses=B.status.value_counts().to_dict(), wall_s=round(time.time() - t0, 1)),
                     ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
