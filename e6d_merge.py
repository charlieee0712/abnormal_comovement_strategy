#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6d 阶段 D: merge。full 指标全部从日序列重算；分类学分布 / 顺序不对称 / 相关性关系 /
   等浓度分桶 / 三因子相对vs绝对 / 深度变体 / stationary bootstrap / 逐年与留一年。
   只出表, 不下结论。用法: python e6d_merge.py --out DIR
"""
import os, io, json, hashlib, argparse, itertools
import numpy as np, pandas as pd
from e6d_combination_taxonomy import (nw_stats, F12, Z6, HB, HINT, RHO, DEPTH_GRID,
                                      F_COND, F_TVOL, SEGS, COST, COST_HI, ANCH_CFG)

NBOOT, BLOCK_L, SEED_ROOT = 2000, 60, '20260905/'
PROD = 'DEP:%s>%s' % (F_COND, F_TVOL)
METHODS = ['DEP', 'DEPnr', 'IND', 'CMEAN25', 'CMEAN50', 'CMAX25']


def sub_seed(ns):
    return int.from_bytes(hashlib.sha256((SEED_ROOT + ns).encode()).digest()[:8], 'big') % (2 ** 32)


def stationary_idx(n, L, rng):
    out = np.empty(n, dtype=np.int64); i = 0; p = 1.0 / L
    while i < n:
        s = rng.randint(n); ln = min(rng.geometric(p), n - i)
        out[i:i + ln] = (s + np.arange(ln)) % n; i += ln
    return out


def score_hac(d, L=5):
    """缺口安全的 HAC: 缺失日 score 记 0, Var(mean)=S/n^2"""
    d = np.asarray(d, float); obs = ~np.isnan(d); n = int(obs.sum())
    if n < 10: return np.nan, np.nan, n
    mu = float(np.nanmean(d)); e = np.where(obs, d - mu, 0.0)
    S = float(e @ e)
    for l in range(1, L + 1):
        if l < len(e): S += 2.0 * (1 - l / (L + 1.0)) * float(e[l:] @ e[:-l])
    se = np.sqrt(S) / n if S > 0 else np.nan
    return mu * 252 * 100.0, (mu / se if (se == se and se > 0) else np.nan), n


def fixedmix_t(x, segmark, L=5):
    """段内 Bartlett 二次型求和 / n^2 (沿 E6c)"""
    obs = ~np.isnan(x)
    if obs.sum() < 12: return np.nan
    mu = float(np.nanmean(x)); num = 0.0; nn = 0
    for s in SEGS:
        z = x[(segmark == s) & obs]
        if len(z) < 3: continue
        e = z - z.mean(); S = float(e @ e)
        for l in range(1, L + 1):
            if l < len(e): S += 2.0 * (1 - l / (L + 1.0)) * float(e[l:] @ e[:-l])
        num += S; nn += len(z)
    return mu / np.sqrt(num / nn ** 2) if (nn and num > 0) else np.nan


def load(OUT):
    sf, store = [], {'net8': {}, 'turn': {}, 'gross': {}}
    for seg in SEGS:
        for ph in ('A', 'C'):
            p = os.path.join(OUT, 'sf_%s_%s.csv' % (seg, ph))
            if not os.path.exists(p): continue
            sf.append(pd.read_csv(p))
            for nm in store:
                q = os.path.join(OUT, 'daily_%s_%s_%s.parquet' % (nm, seg, ph))
                d = pd.read_parquet(q)
                if seg in store[nm]:
                    new = [c for c in d.columns if c not in store[nm][seg].columns]
                    if new: store[nm][seg] = pd.concat([store[nm][seg], d[new]], axis=1)
                else:
                    store[nm][seg] = d
    SF = pd.concat(sf, ignore_index=True).drop_duplicates(subset=['period', 'cfg'], keep='first')
    return SF, store


def stack(store_nm):
    """把各段宽表按时间拼成一张; 返回 (DataFrame, segmark)"""
    cols = sorted(set().union(*[set(store_nm[s].columns) for s in SEGS if s in store_nm]))
    parts, marks = [], []
    for s in SEGS:
        if s not in store_nm: continue
        d = store_nm[s].reindex(columns=cols)
        parts.append(d); marks.append(np.array([s] * len(d.index)))
    return pd.concat(parts, axis=0), np.concatenate(marks)


def merge(OUT):
    L = []
    def P(s=''):
        print(s, flush=True); L.append(s)

    SF, store = load(OUT)
    NET, segmark = stack(store['net8'])
    TRN, _ = stack(store['turn'])
    GRS, _ = stack(store['gross'])
    NET12 = NET - TRN * ((COST_HI - COST) / 1e4)
    cfgs = list(NET.columns)
    segs_present = [s for s in SEGS if s in store['net8']]
    P('配置 %d 个, 日序列 %d 行, 实际载入段 %s (共 %d/%d 段)'
      % (len(cfgs), len(NET.index), '/'.join(segs_present), len(segs_present), len(SEGS)))

    meta = SF.drop_duplicates(subset=['cfg'], keep='first').set_index('cfg')

    # ---------- 1. full_summary ----------
    rows = []
    yr = pd.Index(NET.index).year
    for c in cfgs:
        x = NET[c].values; x12 = NET12[c].values; g = GRS[c].values; tr = TRN[c].values
        # 统一掩码: net8 在基准全 NaN 的日子为 NaN, 而 daily_turnover 从不为 NaN。
        # 若各自用自己的非 NaN 分母, net12-net8 与 turn*4bp 会差到 1e-2 量级(分母不同), 故一律用 net8 的掩码。
        msk = ~np.isnan(x)
        a8, _, t8, n = nw_stats(x[msk], L=5)
        a12, _, t12, _ = nw_stats(x12[msk], L=5)
        ag, _, _, _ = nw_stats(g[msk], L=5)
        m = meta.loc[c] if c in meta.index else None
        segn = {}
        for s in SEGS:
            z = x[segmark == s]; z = z[~np.isnan(z)]
            segn['net8_' + s[:4]] = (float(np.mean(z)) * 252 * 100.0) if len(z) else np.nan
        rows.append(dict(cfg=c, method=(m['method'] if m is not None else ''),
                         kind=(m['kind'] if m is not None else ''),
                         X=(m['X'] if m is not None else ''), Y=(m['Y'] if m is not None else ''),
                         Z=(m['Z'] if m is not None else ''), s1=(m['s1'] if m is not None else np.nan),
                         s2=(m['s2'] if m is not None else np.nan), k=(m['k'] if m is not None else np.nan),
                         net8_full=a8, net12_full=a12, gross_full=ag, cost_full=ag - a8,
                         nw_full_concat=t8, nw12_full=t12, nw_full_fixedmix=fixedmix_t(x, segmark),
                         turn=252 * float(np.nanmean(tr[msk])), days_valid=int(msk.sum()),
                         nh=float(SF[SF.cfg == c]['avg_nh'].mean()),
                         nh_ratio=float(SF[SF.cfg == c]['nh_ratio'].mean()),
                         pos=float(SF[SF.cfg == c]['avg_pos'].mean()),
                         days_nohold=int(SF[SF.cfg == c]['days_nohold'].sum()),
                         pu_net=(a8 / float(SF[SF.cfg == c]['avg_pos'].mean())
                                 if float(SF[SF.cfg == c]['avg_pos'].mean()) > 0 else np.nan),
                         n=n, **segn))
    FULL = pd.DataFrame(rows).set_index('cfg')
    FULL.to_csv(os.path.join(OUT, 'full_summary.csv'))
    P('full_summary.csv  %d 行' % len(FULL))

    def nv(c):
        return FULL.loc[c, 'net8_full'] if c in FULL.index else np.nan

    def dpair(a, b):
        if a not in NET.columns or b not in NET.columns: return (np.nan, np.nan, 0, None)
        d = NET[a].values - NET[b].values
        ann, t, n = score_hac(d, 5)
        return ann, t, n, d

    def segpos(a, b):
        if a not in NET.columns or b not in NET.columns: return np.nan
        c = 0
        for s in SEGS:
            m = segmark == s
            z = (NET[a].values - NET[b].values)[m]; z = z[~np.isnan(z)]
            if len(z) and np.mean(z) > 0: c += 1
        return c

    # ---------- 2. 相关矩阵 (按天数加权平均各段) ----------
    cors, wts = [], []
    for s in SEGS:
        p = os.path.join(OUT, 'corr_%s.csv' % s)
        if os.path.exists(p):
            cors.append(pd.read_csv(p, index_col=0).reindex(index=F12, columns=F12))
            wts.append(float((segmark == s).sum()))
    CORR = sum(c * w for c, w in zip(cors, wts)) / sum(wts) if cors else pd.DataFrame(np.nan, index=F12, columns=F12)
    CORR.to_csv(os.path.join(OUT, 'corr_pooled.csv'))

    # ---------- 3. 成对表 (66 个无序对) ----------
    pr = []
    for i, X in enumerate(F12):
        for Y in F12[i + 1:]:
            dxy, dyx = 'DEP:%s>%s' % (X, Y), 'DEP:%s>%s' % (Y, X)
            nxy, nyx = 'DEPnr:%s>%s' % (X, Y), 'DEPnr:%s>%s' % (Y, X)
            ind, cme, cm5, cmx = ('IND:%s+%s' % (X, Y), 'CMEAN25:%s+%s' % (X, Y),
                                  'CMEAN50:%s+%s' % (X, Y), 'CMAX25:%s+%s' % (X, Y))
            best_sf = max(nv('SF25:' + X), nv('SF25:' + Y))
            d1 = dpair(dxy, cme); d2 = dpair(dyx, cme); d3 = dpair(dxy, dyx)
            d4 = dpair(ind, cme); d5 = dpair(cmx, cme); d6 = dpair(dxy, nxy)
            pr.append(dict(X=X, Y=Y, rho=CORR.loc[X, Y], absrho=abs(CORR.loc[X, Y]),
                           hintX=HINT[X], hintY=HINT[Y],
                           net_DEPxy=nv(dxy), net_DEPyx=nv(dyx), net_DEPnrxy=nv(nxy), net_DEPnryx=nv(nyx),
                           net_IND=nv(ind), net_CMEAN25=nv(cme), net_CMEAN50=nv(cm5), net_CMAX25=nv(cmx),
                           net_SF25_X=nv('SF25:' + X), net_SF25_Y=nv('SF25:' + Y), net_SF25_best=best_sf,
                           nh_IND=(FULL.loc[ind, 'nh_ratio'] if ind in FULL.index else np.nan),
                           nh_CMEAN25=(FULL.loc[cme, 'nh_ratio'] if cme in FULL.index else np.nan),
                           d_DEPxy_CMEAN=d1[0], t_DEPxy_CMEAN=d1[1], sp_DEPxy_CMEAN=segpos(dxy, cme),
                           d_DEPyx_CMEAN=d2[0], t_DEPyx_CMEAN=d2[1],
                           d_order=d3[0], t_order=d3[1],
                           d_IND_CMEAN=d4[0], t_IND_CMEAN=d4[1],
                           d_CMAX_CMEAN=d5[0], t_CMAX_CMEAN=d5[1],
                           d_DEP_DEPnr=d6[0], t_DEP_DEPnr=d6[1],
                           d_best2f_vs_SF25=max(nv(dxy), nv(dyx), nv(cme), nv(cmx)) - best_sf,
                           # 两边都不取 max, 无选择档数不对称: 复合均值 vs 两个单因子的平均
                           d_CMEAN_vs_meanSF25=nv(cme) - 0.5 * (nv('SF25:' + X) + nv('SF25:' + Y)),
                           d_DEPxy_vs_meanSF25=nv(dxy) - 0.5 * (nv('SF25:' + X) + nv('SF25:' + Y))))
    PR = pd.DataFrame(pr); PR.to_csv(os.path.join(OUT, 'pair_matrix.csv'), index=False)
    P('pair_matrix.csv  %d 对' % len(PR))

    # ---------- 4. 分类学分布 ----------
    def dist(col, tcol=None, spcol=None):
        v = PR[col].dropna().values
        r = dict(name=col, n=len(v), median=float(np.median(v)) if len(v) else np.nan,
                 mean=float(np.mean(v)) if len(v) else np.nan,
                 q25=float(np.percentile(v, 25)) if len(v) else np.nan,
                 q75=float(np.percentile(v, 75)) if len(v) else np.nan,
                 pos_share=float((v > 0).mean()) if len(v) else np.nan)
        if tcol: r['median_t'] = float(np.nanmedian(PR[tcol].values))
        if spcol: r['share_4seg_pos'] = float((PR[spcol] == 4).mean())
        return r
    DIST = pd.DataFrame([dist('d_DEPxy_CMEAN', 't_DEPxy_CMEAN', 'sp_DEPxy_CMEAN'),
                         dist('d_DEPyx_CMEAN', 't_DEPyx_CMEAN'), dist('d_order', 't_order'),
                         dist('d_IND_CMEAN', 't_IND_CMEAN'), dist('d_CMAX_CMEAN', 't_CMAX_CMEAN'),
                         dist('d_DEP_DEPnr', 't_DEP_DEPnr'), dist('d_best2f_vs_SF25'),
                         dist('d_CMEAN_vs_meanSF25'), dist('d_DEPxy_vs_meanSF25')])
    DIST.to_csv(os.path.join(OUT, 'taxonomy_distribution.csv'), index=False)

    # ---------- 5. 132 个有序对的 DEP-CMEAN25 (H-E6d-1 / 两向分解 / 留一因子) ----------
    ord_rows = []
    for X in F12:
        for Y in F12:
            if X == Y: continue
            a = 'DEP:%s>%s' % (X, Y)
            b = 'CMEAN25:%s+%s' % (X, Y) if ('CMEAN25:%s+%s' % (X, Y)) in NET.columns else 'CMEAN25:%s+%s' % (Y, X)
            dd = dpair(a, b)
            ord_rows.append(dict(X=X, Y=Y, hintX=HINT[X], hintY=HINT[Y],
                                 absrho=abs(CORR.loc[X, Y]), d=dd[0], t=dd[1],
                                 net_DEP=nv(a), net_CMEAN25=nv(b)))
    OD = pd.DataFrame(ord_rows); OD.to_csv(os.path.join(OUT, 'ordered_pairs.csv'), index=False)

    cells = OD.groupby(['hintX', 'hintY'])['d'].agg(['median', 'mean', 'count']).reset_index()
    cells.to_csv(os.path.join(OUT, 'hint_cells.csv'), index=False)
    tgt = cells[(cells.hintX.str.contains('单尾')) & (cells.hintY.str.contains('渐变'))]
    top_cell = cells.loc[cells['median'].idxmax()] if len(cells) else None
    H1_hit = bool(len(tgt) and top_cell is not None and
                  tgt.iloc[0]['hintX'] == top_cell['hintX'] and tgt.iloc[0]['hintY'] == top_cell['hintY'])

    mu = float(OD['d'].mean())
    aX = OD.groupby('X')['d'].mean() - mu
    bY = OD.groupby('Y')['d'].mean() - mu
    OD['fit'] = mu + OD['X'].map(aX).values + OD['Y'].map(bY).values
    resid = float(np.sqrt(np.nanmean((OD['d'] - OD['fit']) ** 2)))
    TW = pd.DataFrame(dict(factor=F12, gate_effect=[aX.get(f, np.nan) for f in F12],
                           ranker_effect=[bY.get(f, np.nan) for f in F12],
                           role_hint=[HINT[f] for f in F12], rho_mean=[RHO[f] for f in F12]))
    TW['mu'] = mu; TW['resid_rms'] = resid
    TW.to_csv(os.path.join(OUT, 'twoway_decomp.csv'), index=False)

    lo = [dict(dropped=f, n=int(((PR.X != f) & (PR.Y != f)).sum()),
               median_d=float(PR.loc[(PR.X != f) & (PR.Y != f), 'd_DEPxy_CMEAN'].median()),
               pos_share=float((PR.loc[(PR.X != f) & (PR.Y != f), 'd_DEPxy_CMEAN'] > 0).mean()))
          for f in F12]
    LOO = pd.DataFrame(lo); LOO.to_csv(os.path.join(OUT, 'leave_one_factor.csv'), index=False)

    # ---------- 6. 闸/排序器倾向 ----------
    gr = []
    for f in F12:
        asg = [nv('DEP:%s>%s' % (f, y)) for y in F12 if y != f]
        asr = [nv('DEP:%s>%s' % (x, f)) for x in F12 if x != f]
        gr.append(dict(factor=f, role_hint=HINT[f], rho_mean=RHO[f], high_bad=HB[f],
                       net_as_gate=float(np.nanmean(asg)), net_as_ranker=float(np.nanmean(asr)),
                       gate_minus_ranker=float(np.nanmean(asg)) - float(np.nanmean(asr)),
                       net_SF50=nv('SF50:' + f), net_SF25=nv('SF25:' + f)))
    GR = pd.DataFrame(gr).sort_values('gate_minus_ranker', ascending=False)
    GR.to_csv(os.path.join(OUT, 'gate_ranker.csv'), index=False)

    # ---------- 7. 差 vs 相关性 ----------
    v = PR.dropna(subset=['absrho', 'd_DEPxy_CMEAN'])
    rho_s = float(v['absrho'].corr(v['d_DEPxy_CMEAN'], method='spearman')) if len(v) > 3 else np.nan
    q = pd.qcut(v['absrho'], 3, labels=['low|rho|', 'mid|rho|', 'high|rho|'], duplicates='drop')
    RB = v.groupby(q, observed=False).agg(n=('d_DEPxy_CMEAN', 'size'),
                                          absrho_mean=('absrho', 'mean'),
                                          d_median=('d_DEPxy_CMEAN', 'median'),
                                          d_mean=('d_DEPxy_CMEAN', 'mean'),
                                          pos_share=('d_DEPxy_CMEAN', lambda z: float((z > 0).mean())),
                                          dIND_median=('d_IND_CMEAN', 'median')).reset_index()
    RB['spearman_absrho_vs_d'] = rho_s
    RB.to_csv(os.path.join(OUT, 'rho_relation.csv'), index=False)

    # ---------- 8. 等浓度分桶 ----------
    fb = FULL[FULL['kind'].isin(['pair', 'single'])].copy()
    fb['conc_bucket'] = pd.cut(fb['nh_ratio'], [0, 0.15, 0.22, 0.28, 0.35, 1.01],
                               labels=['<15%', '15-22%', '22-28%', '28-35%', '>35%'])
    CB = fb.groupby(['conc_bucket', 'method'], observed=True).agg(
        n=('net8_full', 'size'), net8_median=('net8_full', 'median'),
        net8_mean=('net8_full', 'mean'), net12_median=('net12_full', 'median'),
        nh_ratio_mean=('nh_ratio', 'mean'), turn_mean=('turn', 'mean')).reset_index()
    CB.to_csv(os.path.join(OUT, 'conc_buckets.csv'), index=False)

    # ---------- 9. 三因子 相对 vs 绝对 ----------
    tri = []
    pj = os.path.join(OUT, 'parents.json')
    parents = json.load(io.open(pj, encoding='utf-8'))['parents'] if os.path.exists(pj) else []
    for pa in parents:
        X, Y, tag = pa['X'], pa['Y'], pa['tag']
        base = 'DEP:%s>%s' % (X, Y)
        for Z in Z6:
            if Z in (X, Y): continue
            rel = 'T3rel:%s>%s>%s' % (X, Y, Z)
            a5, a10 = 'T3abs5:%s>%s>%s' % (X, Y, Z), 'T3abs10:%s>%s>%s' % (X, Y, Z)
            r1 = dpair(rel, a5); r2 = dpair(rel, a10); r3 = dpair(rel, base)
            r4 = dpair(a5, base); r5 = dpair(a10, base)
            tri.append(dict(parent=base, tag=tag, X=X, Y=Y, Z=Z,
                            net_parent=nv(base), net_rel=nv(rel), net_abs5=nv(a5), net_abs10=nv(a10),
                            nh_rel=(FULL.loc[rel, 'nh_ratio'] if rel in FULL.index else np.nan),
                            nh_abs5=(FULL.loc[a5, 'nh_ratio'] if a5 in FULL.index else np.nan),
                            d_rel_abs5=r1[0], t_rel_abs5=r1[1], d_rel_abs10=r2[0], t_rel_abs10=r2[1],
                            d_rel_parent=r3[0], t_rel_parent=r3[1],
                            d_abs5_parent=r4[0], t_abs5_parent=r4[1],
                            d_abs10_parent=r5[0], t_abs10_parent=r5[1]))
    TRI = pd.DataFrame(tri)
    if len(TRI): TRI.to_csv(os.path.join(OUT, 'triple_rel_vs_abs.csv'), index=False)

    # ---------- 10. 深度变体 ----------
    dep_rows = []
    for pa in parents:
        if pa['tag'] == 'worst': continue
        X, Y = pa['X'], pa['Y']
        ref = 'DEPTH:%s>%s@50_50' % (X, Y)
        for (s1, s2) in DEPTH_GRID + [(50, 50)]:
            c = 'DEPTH:%s>%s@%d_%d' % (X, Y, s1, s2)
            if c not in FULL.index: continue
            d = dpair(c, ref)
            dep_rows.append(dict(parent='%s>%s' % (X, Y), tag=pa['tag'], s1=s1, s2=s2,
                                 final_pct=s1 * s2 / 100.0, net8=nv(c), net12=FULL.loc[c, 'net12_full'],
                                 nh_ratio=FULL.loc[c, 'nh_ratio'], turn=FULL.loc[c, 'turn'],
                                 days_nohold=FULL.loc[c, 'days_nohold'],
                                 d_vs_5050=d[0], t_vs_5050=d[1],
                                 d_vs_binary_DEP=nv(c) - nv('DEP:%s>%s' % (X, Y))))
    DEPTH = pd.DataFrame(dep_rows)
    if len(DEPTH): DEPTH.to_csv(os.path.join(OUT, 'depth_grid.csv'), index=False)

    # ---------- 11. bootstrap (两族, 共用 draw) ----------
    segidx = {s: np.where(segmark == s)[0] for s in SEGS}
    famA = [c for c in cfgs if c != PROD and PROD in NET.columns]
    DA = (NET[famA].values - NET[[PROD]].values) if famA else np.zeros((len(NET), 0))
    famB = ['%s|%s' % (r.X, r.Y) for _, r in OD.iterrows()]
    DB = np.column_stack([NET['DEP:%s>%s' % (r.X, r.Y)].values -
                          NET['CMEAN25:%s+%s' % (r.X, r.Y)].values
                          if ('CMEAN25:%s+%s' % (r.X, r.Y)) in NET.columns else
                          NET['DEP:%s>%s' % (r.X, r.Y)].values -
                          NET['CMEAN25:%s+%s' % (r.Y, r.X)].values
                          for _, r in OD.iterrows()])
    rng = np.random.RandomState(sub_seed('boot'))
    bootA = np.empty((NBOOT, DA.shape[1])); bootB = np.empty((NBOOT, DB.shape[1]))
    for b in range(NBOOT):
        idx = np.concatenate([segidx[s][stationary_idx(len(segidx[s]), BLOCK_L, rng)] for s in SEGS])
        bootA[b] = np.nanmean(DA[idx], axis=0) * 252 * 100.0
        bootB[b] = np.nanmean(DB[idx], axis=0) * 252 * 100.0
    def band(boot, names, obs):
        lo = np.nanpercentile(boot, 2.5, axis=0); hi = np.nanpercentile(boot, 97.5, axis=0)
        sd = np.nanstd(boot, axis=0)
        z = np.nanmax(np.abs((boot - np.nanmean(boot, axis=0)) / np.where(sd > 0, sd, np.nan)), axis=1)
        q95 = float(np.nanpercentile(z, 95))
        return pd.DataFrame(dict(name=names, obs=obs, lo95=lo, hi95=hi, sd=sd,
                                 joint_lo=obs - q95 * sd, joint_hi=obs + q95 * sd, q95=q95))
    BA = band(bootA, famA, np.array([np.nanmean(DA[:, j]) * 252 * 100.0 for j in range(DA.shape[1])]))
    BA['family'] = 'vs_' + PROD
    BB = band(bootB, famB, np.array([np.nanmean(DB[:, j]) * 252 * 100.0 for j in range(DB.shape[1])]))
    BB['family'] = 'DEP_minus_CMEAN25'
    pd.concat([BA, BB], ignore_index=True).to_csv(os.path.join(OUT, 'bootstrap_summary.csv'), index=False)
    json.dump(dict(nboot=NBOOT, block_L=BLOCK_L, seed_root=SEED_ROOT, per_segment=True,
                   shared_draw_within_replicate=True, families=['vs_' + PROD, 'DEP_minus_CMEAN25'],
                   n_family_A=DA.shape[1], n_family_B=DB.shape[1]),
              io.open(os.path.join(OUT, 'bootstrap_manifest.json'), 'w', encoding='utf-8'), indent=1)

    # ---------- 12. 逐年 / 留一年 ----------
    watch = [PROD, 'A4b', 'M_mean2', 'pool0_DEV'] + \
            [c for c in cfgs if c.startswith(('CMEAN25:%s+%s' % (F_COND, F_TVOL),
                                              'CMAX25:%s+%s' % (F_COND, F_TVOL),
                                              'IND:%s+%s' % (F_COND, F_TVOL)))]
    yrows, lrows = [], []
    for c in [w for w in watch if w in NET.columns]:
        x = NET[c].values
        for y in sorted(set(yr)):
            z = x[yr == y]; z = z[~np.isnan(z)]
            yrows.append(dict(cfg=c, year=int(y), net8=float(np.mean(z)) * 252 * 100.0 if len(z) else np.nan,
                              days=len(z)))
        for y in sorted(set(yr)):
            z = x[yr != y]; z = z[~np.isnan(z)]
            lrows.append(dict(cfg=c, dropped_year=int(y),
                              net8=float(np.mean(z)) * 252 * 100.0 if len(z) else np.nan))
    pd.DataFrame(yrows).to_csv(os.path.join(OUT, 'yearly.csv'), index=False)
    pd.DataFrame(lrows).to_csv(os.path.join(OUT, 'leave_one_year.csv'), index=False)

    # ---------- 13. summary ----------
    P('')
    P('== (A) 分类学分布 (全窗口 net8 年化差, 单位 点) ==')
    P(DIST.to_string(index=False, float_format=lambda z: '%+.3f' % z))
    P('')
    P('== (B) H-E6d-1: DEP-CMEAN25 按 (闸 role_hint, 排序器 role_hint) 分格 ==')
    P(cells.to_string(index=False, float_format=lambda z: '%+.3f' % z))
    P('  单尾->渐变 是否为中位数最高格: %s' % ('是 (H-E6d-1 未被否)' if H1_hit else '否 (H-E6d-1 被否)'))
    P('')
    P('== (C) 两向分解 d = mu + a_X(闸) + b_Y(排序器);  mu = %+.3f, 残差 RMS = %.3f ==' % (mu, resid))
    P(TW[['factor', 'role_hint', 'gate_effect', 'ranker_effect']].to_string(
        index=False, float_format=lambda z: '%+.3f' % z))
    P('')
    P('== (D) 留一因子后 DEP-CMEAN25 的中位数 ==')
    P(LOO.to_string(index=False, float_format=lambda z: '%+.3f' % z))
    P('')
    P('== (E) 闸/排序器倾向 (跨全部搭档的平均 net8) ==')
    P(GR.to_string(index=False, float_format=lambda z: '%+.3f' % z))
    P('')
    P('== (F) 差 vs |rho| (Spearman = %+.3f) ==' % rho_s)
    P(RB.to_string(index=False, float_format=lambda z: '%+.3f' % z))
    P('')
    P('== (G) 等浓度分桶 ==')
    P(CB.to_string(index=False, float_format=lambda z: '%+.3f' % z))
    P('')
    P('== (H) 生产核 cond>tvol 的名次 ==')
    dep_only = FULL[FULL.method == 'DEP'].sort_values('net8_full', ascending=False)
    rk = list(dep_only.index).index(PROD) + 1 if PROD in dep_only.index else -1
    pr_sorted = PR.sort_values('d_DEPxy_CMEAN', ascending=False).reset_index(drop=True)
    hit = pr_sorted[(pr_sorted.X == F_COND) & (pr_sorted.Y == F_TVOL)]
    rk2 = int(hit.index[0]) + 1 if len(hit) else -1
    P('  DEP 净值名次 %d/%d;  (DEP-CMEAN25) 差的名次 %d/%d' % (rk, len(dep_only), rk2, len(pr_sorted)))
    P('  net8_full: DEP %+.3f | CMEAN25 %+.3f | CMAX25 %+.3f | IND %+.3f | SF25(cond) %+.3f | SF25(tvol) %+.3f'
      % (nv(PROD), nv('CMEAN25:%s+%s' % (F_COND, F_TVOL)), nv('CMAX25:%s+%s' % (F_COND, F_TVOL)),
         nv('IND:%s+%s' % (F_COND, F_TVOL)), nv('SF25:' + F_COND), nv('SF25:' + F_TVOL)))
    if len(TRI):
        P('')
        P('== (I) 三因子 相对 vs 绝对 (按父 tag 汇总 d_rel_abs5 / d_rel_parent) ==')
        P(TRI.groupby('tag').agg(n=('d_rel_abs5', 'size'), d_rel_abs5_median=('d_rel_abs5', 'median'),
                                 d_rel_abs10_median=('d_rel_abs10', 'median'),
                                 d_rel_parent_median=('d_rel_parent', 'median'),
                                 d_abs5_parent_median=('d_abs5_parent', 'median')).to_string(
            float_format=lambda z: '%+.3f' % z))
    if len(DEPTH):
        P('')
        P('== (J) 深度变体 (相对 (50,50) 的差, 按 (s1,s2) 汇总) ==')
        P(DEPTH.groupby(['s1', 's2']).agg(n=('net8', 'size'), final_pct=('final_pct', 'first'),
                                          net8_median=('net8', 'median'),
                                          d_vs_5050_median=('d_vs_5050', 'median'),
                                          nohold=('days_nohold', 'sum')).to_string(
            float_format=lambda z: '%+.3f' % z))
    P('')
    P('== (K) 边界与计数 ==')
    P('  配置 %d;  bootstrap 族 A %d 个 / 族 B %d 个;  B=%d, 块长 %d'
      % (len(cfgs), DA.shape[1], DB.shape[1], NBOOT, BLOCK_L))
    io.open(os.path.join(OUT, 'summary.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')

    io.open(os.path.join(OUT, 'limit_register.md'), 'w', encoding='utf-8').write(
        '# E6d 未做的诊断项 (登记, 不补做)\n\n'
        '- 交集 IND 未做浓度匹配版本(靠 CMAX25 作等浓度替身); IND 的 nh_ratio 如实报在 pair_matrix.csv\n'
        '- 三因子只在 10 个父上做(prod+top6+worst3), 未覆盖全部 132 个有序对\n'
        '- 深度变体只在 7 个父上做, 且 (70,35) 用 20 分位实现, 薄日无持仓天数见 depth_grid.csv\n'
        '- 两向分解为描述性最小二乘(行列均值), 未给 p 值(66 对不独立, 误差相关)\n'
        '- role_hint 与 rho_mean 均由 E6 在同样本上估出, 非外生标签\n'
        '- 未做 placebo / 随机因子对照(留 E6e); 未做 regime 分段; 未延长样本(E7 仍 HOLD)\n'
        '- 未改生产持有期(5 日)、否决阈值、池定义、成本口径\n')
    P('\nmerge done.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    merge(ap.parse_args().out)
