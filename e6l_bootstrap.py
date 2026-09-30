# -*- coding: utf-8 -*-
"""E6l bootstrap（plan §11.2 / §11.2a；brief §7；E6k e6k_bootstrap 同式）。seal_deriv + seal_post 之后运行。
四历史段内分层 stationary（Politis–Romano，几何块长均值 L ∈ {20, 60}，段内环绕、不跨段接缝），每 L 各 2,000 次；全部比较共享同一套段内索引
（rng_for('E6l', 'bootstrap', L, 段)）；抽已生成的逐日配对 PnL（原日历行与缺失掩码一起抽），不回喂规则 / 持仓引擎；
FULL* = Σ_s num*_s / Σ_s den*_s × 252 × 100（固定段、实际有效分母）。计数矩阵：C_s[b, t] = 第 b 次抽样段 s 第 t 日被抽中次数。
比较族（registry/bootstrap_comparisons_E6l.csv）：CP / CN / CC1 / CB（同算子 Q0）/ CH（规则 ONLY）/ CQ（Q0 HG10）/ CM（机制与核配对）；另加 CR（真实 − 随机逐日路径均值，plan §7.5）。
同时带：固定集合（主 72 的 CP / 高剂量 72 的 CP / 各族 / 全部）上中心化最大标准化偏差 max_j |(D*_bj − D̂_j)/SE_j| 的 95% 分位 = q95_maxabs_t（SE 倍数）；
逐行 halfwidth_ann_pp = q95_maxabs_t × SE_j；另列单侧带符号读法：q95_max_t = max_j (D*_bj − D̂_j)/SE_j 的 95% 分位、q05_min_t = min_j 的 5% 分位（上 / 下单侧）；
SE = 0 的恒等 / 常数比较单列（不进最大值）；某 draw 无支持（den* = 0）计 INSUFFICIENT_REPLICATE_SUPPORT 份额、
不用 nanmax 改域（该比较不进同时带并单列）。不设 FWER / 同时带准入门。"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import argparse

import numpy as np
import pandas as pd

import e6l_core as L
import e6j_stats as ST

NB = 2000
LS = (20, 60)


def seg_counts(T, Lb, seg):
    rng = L.rng_for('E6l', 'bootstrap', int(Lb), seg)
    C = np.zeros((NB, T), np.float64)
    for b in range(NB):
        idx = ST.stationary_indices(T, Lb, rng)
        C[b] = np.bincount(idx, minlength=T)
    return C


def load_net8(seg):
    out = {}
    for f in sorted(glob.glob(L.P('accounts', seg, '*.npz'))):
        if os.path.basename(f).startswith('weights_'):
            continue
        z = L.npz(f, keys=['desc', 'd_net8'])
        for did, x in zip([str(v) for v in z['desc']], z['d_net8']):
            out[did] = x
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chunk', type=int, default=8000)
    a = ap.parse_args()
    import e6l_seal as SEAL
    for pkg in ('deriv', 'post'):
        ok, bad = SEAL.verify(pkg)
        if not ok:
            raise RuntimeError('seal_%s 核对失败：%s' % (pkg, bad[:5]))
    for s in L.POST_SEGS:
        L.post_gate(s, 'bootstrap')
    BB = L.read_csv_keep(L.P('registry', 'bootstrap_comparisons_E6l.csv'))
    D = L.read_csv_keep(L.P('registry', 'descriptors_E6l.csv'))
    sets = {'primary72_CP': set('CP|' + D[D.primary72.astype(str) == 'True'].desc_id),
            'dose72_CP': set('CP|' + D[D.dose72.astype(str) == 'True'].desc_id)}
    od = L.P('results', 'full', 'bootstrap')
    os.makedirs(od, exist_ok=True)
    nets = {s: load_net8(s) for s in L.SEGMENTS}
    # CR 族（plan §7.5：真实 − 随机的跨时间均值另做共享日期 bootstrap）：右端 = 该机制逐日随机路径均值（random_daily_<段>.npz）
    RR = L.read_csv_keep(L.P('registry', 'randoms_E6l.csv'), usecols=['mechanism', 'desc_id', 'H'])
    for s in L.SEGMENTS:
        rdl = L.npz(L.P('results', 'full', 'random_daily_%s.npz' % s))
        for k, v in rdl.items():
            nets[s]['RANDMEAN~' + k] = v
    cr = pd.DataFrame(dict(comparison_id='CR|' + RR.mechanism + '|' + RR.desc_id, family='real_minus_random_' + RR.mechanism.str.lower(), a=RR.desc_id,
                           b='RANDMEAN~' + RR.desc_id.str.replace('|', '~', regex=False) + '~H' + RR.H.astype(str) + '~' + RR.mechanism))
    BB = pd.concat([BB, cr], ignore_index=True)
    Ts = {s: len(next(iter(nets[s].values()))) for s in L.SEGMENTS}
    counts = {(s, Lb): seg_counts(Ts[s], Lb, s) for s in L.SEGMENTS for Lb in LS}
    rows = []
    maxst = {Lb: {} for Lb in LS}
    for c0 in range(0, len(BB), a.chunk):
        sub = BB.iloc[c0:c0 + a.chunk]
        Dseg = {}
        est_num = np.zeros(len(sub))
        est_den = np.zeros(len(sub))
        for s in L.SEGMENTS:
            T = Ts[s]
            M = np.zeros((T, len(sub)))
            V = np.zeros((T, len(sub)))
            for j, r in enumerate(sub.itertuples()):
                x, y = nets[s].get(r.a), nets[s].get(r.b)
                if x is None or y is None:
                    continue
                dd = x - y
                v = np.isfinite(dd)
                M[v, j] = dd[v]
                V[v, j] = 1.0
            est_num += M.sum(0)
            est_den += V.sum(0)
            Dseg[s] = (M, V)
        est = np.where(est_den > 0, est_num / np.where(est_den > 0, est_den, 1) * ST.ANN, np.nan)
        for Lb in LS:
            parts = {s: (counts[(s, Lb)] @ Dseg[s][0], counts[(s, Lb)] @ Dseg[s][1]) for s in L.SEGMENTS}
            for grp, segs_ in (('DERIV', L.DERIV_SEGS), ('POST', L.POST_SEGS)):
                if not segs_:
                    continue
                gn = sum(parts[s][0] for s in segs_)
                gd = sum(parts[s][1] for s in segs_)
                with np.errstate(divide='ignore', invalid='ignore'):
                    gdr = np.where(gd > 0, gn / gd * ST.ANN, np.nan)
                en = sum(Dseg[s][0].sum(0) for s in segs_)
                ed = sum(Dseg[s][1].sum(0) for s in segs_)
                gest = np.where(ed > 0, en / np.where(ed > 0, ed, 1) * ST.ANN, np.nan)
                with np.errstate(all='ignore'):
                    gq = np.nanpercentile(gdr, [2.5, 97.5], axis=0)
                    gse = np.nanstd(gdr, axis=0, ddof=1)
                for j, r in enumerate(sub.itertuples()):
                    rows.append(dict(comparison_id=r.comparison_id, family=r.family, L=Lb, scope=grp, est_ann_pp=gest[j], q025_ann_pp=gq[0, j],
                                     q975_ann_pp=gq[1, j], se_ann_pp=float(gse[j]), no_support_draws=int((gd[:, j] <= 0).sum())))
            num = sum(parts[s][0] for s in L.SEGMENTS)
            den = sum(parts[s][1] for s in L.SEGMENTS)
            with np.errstate(divide='ignore', invalid='ignore'):
                draws = np.where(den > 0, num / den * ST.ANN, np.nan)
            nosup = (den <= 0).sum(0)
            with np.errstate(all='ignore'):
                se = np.nanstd(draws, axis=0, ddof=1)
                q = np.nanpercentile(draws, [2.5, 50, 97.5], axis=0)
            for j, r in enumerate(sub.itertuples()):
                rows.append(dict(comparison_id=r.comparison_id, family=r.family, L=Lb, scope='FULL', est_ann_pp=est[j], q025_ann_pp=q[0, j],
                                 q50_ann_pp=q[1, j], q975_ann_pp=q[2, j], se_ann_pp=float(se[j]), no_support_draws=int(nosup[j]),
                                 zero_se=bool(np.isfinite(se[j]) and se[j] == 0.0)))
            ok_ = np.isfinite(se) & (se > 0) & (nosup == 0)
            z = (draws - est[None, :]) / np.where(ok_, se, 1.0)[None, :]
            cen = np.abs(z)
            fams = sub.family.values
            ids = sub.comparison_id.values
            groups = {'all': ok_}
            for fam in np.unique(fams):
                groups['family_' + fam] = ok_ & (fams == fam)
            for nm, sset in sets.items():
                groups[nm] = ok_ & np.array([c in sset for c in ids])
            for nm, msk in groups.items():
                if msk.any():
                    maxst[Lb].setdefault(nm, []).append(np.max(cen[:, msk], axis=1))
                    maxst[Lb].setdefault(nm + '__smax', []).append(np.max(z[:, msk], axis=1))
                    maxst[Lb].setdefault(nm + '__smin', []).append(np.min(z[:, msk], axis=1))
                    maxst[Lb].setdefault(nm + '__n', []).append(int(msk.sum()))
        L.log('bootstrap chunk %d / %d' % (c0 + len(sub), len(BB)))
    R = pd.DataFrame(rows)
    band = []
    for Lb in LS:
        for nm in [k for k in maxst[Lb] if not k.endswith(('__n', '__smax', '__smin'))]:
            mx = np.max(np.vstack(maxst[Lb][nm]), axis=0)
            smx = np.max(np.vstack(maxst[Lb][nm + '__smax']), axis=0)
            smn = np.min(np.vstack(maxst[Lb][nm + '__smin']), axis=0)
            band.append(dict(L=Lb, set=nm, q95_maxabs_t=float(np.percentile(mx, 95)), q95_max_t=float(np.percentile(smx, 95)),
                             q05_min_t=float(np.percentile(smn, 5)), draws=NB, n_comparisons=int(sum(maxst[Lb][nm + '__n']))))
    B = pd.DataFrame(band)
    full = R[R.scope == 'FULL'].copy()
    qall = {Lb: float(B[(B.L == Lb) & (B.set == 'all')].q95_maxabs_t.iloc[0]) for Lb in LS}
    full['q95_maxabs_t_all'] = full.L.map(qall)
    full['q95_max_t_all'] = full.L.map({Lb: float(B[(B.L == Lb) & (B.set == 'all')].q95_max_t.iloc[0]) for Lb in LS})
    full['q05_min_t_all'] = full.L.map({Lb: float(B[(B.L == Lb) & (B.set == 'all')].q05_min_t.iloc[0]) for Lb in LS})
    full['halfwidth_ann_pp_all'] = full.q95_maxabs_t_all * full.se_ann_pp
    full['band_status'] = np.where(full.no_support_draws > 0, 'INSUFFICIENT_REPLICATE_SUPPORT', np.where(full.zero_se, 'ZERO_SE_IDENTITY', 'IN_BAND_SET'))
    p1 = os.path.join(od, 'bootstrap_comparisons.csv')
    L.atomic_write_csv(p1, pd.concat([full, R[R.scope != 'FULL']], ignore_index=True))
    p2 = os.path.join(od, 'simultaneous_band_q95.csv')
    L.atomic_write_csv(p2, B)
    L.write_receipt(L.next_rerun('bootstrap_full'), [p1, p2], 'SUCCEEDED', comparisons=len(BB), draws=NB,
                    generator='blake2b-128(canonical_json(E6l, bootstrap, L, segment)) -> SeedSequence -> PCG64; e6j_stats.stationary_indices')
    print('bootstrap：%d 比较 × %d L；同时带集合 %d' % (len(BB), len(LS), len(B)), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
