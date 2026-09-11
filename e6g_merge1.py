#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 合并层 (part1): 配对增量 / 比较族 / 同时带 / 冲击情景。

族定义按 plan §2D3。同时带 = 共 draw stationary bootstrap 的 max-|t| (块长 20, 2000 次),
Romano-Wolf stepdown 作附列。四种计数 (全体描述符 / 公式 / 真实路径 / 有效比较数) 同时报。
任何统计量都只作列, 不作准入门 (brief §0.2)。
"""
import os, sys, json, glob, time, argparse
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6g_core as G
import e6g_desc as GD

BLOCK_DIR = {'H0': 'H0', 'H1': 'H1', 'H2': 'H2', 'H4a': 'H4', 'H4b': 'H4',
             'H5': 'H5', 'B2': 'B2'}
NB = 2000
BLK = 20


def family_of(r):
    b = r.get('block')
    mode = str(r.get('mode', ''))
    if b == 'H1':
        return 'F-H1replace' if mode.startswith('replace') else 'F-H1add'
    if b == 'H2':
        return 'F-H2'
    if b in ('H4a', 'H4b'):
        return 'F-H4'
    if b == 'H5':
        return 'F-H5'
    if b == 'B2':
        return 'F-B2'
    return 'F-instrument'


def refs(S, ctx):
    """固定参照的逐日账本: R1 / R2 / A03 / A06 / A08 / Blend3。
       Blend3 = 成员目标权重各 1/3 合并后【重新过引擎】(turn/net 必须重算)。"""
    out, ivs = {}, {}
    for lab, cid, _ in G.DISPLAY:
        pnl, iv, _ = ctx.run(GD.parse_cfg(cid))
        out[lab] = pnl
        ivs[lab] = iv
    bi, bv = G.blend3_weights([ivs[m] for m in G.BLEND3_MEMBERS])
    out['Blend3'] = F.sparse_pnl_H(S, bi, bv, K.HOLD, F.COST)
    return out


def hac_t(x, lag=5):
    """Newey-West t (均值为 0 的检验)。"""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 30:
        return np.nan, np.nan
    m = x.mean()
    e = x - m
    s = float(e @ e) / n
    for L in range(1, min(lag, n - 1) + 1):
        c = float(e[L:] @ e[:-L]) / n
        s += 2.0 * (1.0 - L / (lag + 1.0)) * c
    if s <= 0:
        return m, np.nan
    return m, m / np.sqrt(s / n)


def boot_weights(T, nb=NB, blk=BLK, seed=11):
    """共 draw stationary bootstrap: 返回 (nb, T) 的日期计数权重矩阵 (行和 = 1)。"""
    rng = np.random.default_rng(seed)
    Wm = np.zeros((nb, T))
    for b in range(nb):
        idx = []
        while len(idx) < T:
            s0 = int(rng.integers(0, T))
            L = int(rng.geometric(1.0 / blk))
            idx.extend(range(s0, min(T, s0 + L)))
        idx = np.asarray(idx[:T])
        np.add.at(Wm[b], idx, 1.0)
    return Wm / T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segments', default=','.join(G.SEGMENTS))
    ap.add_argument('--nboot', type=int, default=NB)
    A = ap.parse_args()
    t0 = time.time()
    out = os.path.join(G.RES, 'D')
    os.makedirs(out, exist_ok=True)

    # ---------- 1. 汇总表 ----------
    frames = []
    for b, d in BLOCK_DIR.items():
        for fp in sorted(glob.glob(os.path.join(G.RES, d, 'summary_%s_*.csv' % b))):
            x = pd.read_csv(fp)
            x['block'] = b
            frames.append(x)
    if not frames:
        print('没有 summary 文件, 先跑 e6g_run.py'); return
    MS = pd.concat(frames, ignore_index=True)
    MS['family'] = MS.apply(family_of, axis=1)
    print('汇总 %d 行 (%d 经济), %d 段, %.0fs'
          % (len(MS), int((MS.role == 'economic').sum()), MS.segment.nunique(),
             time.time() - t0), flush=True)

    # 族映射在读收益之前冻结 (brief §8: 映射在收益读取前冻结)
    FAM = {}
    for r in MS.itertuples():
        FAM[(r.config_id, r.segment)] = (r.family if getattr(r, 'role', '') == 'economic'
                                         else 'F-control')
    json.dump({'%s||%s' % k: v for k, v in FAM.items()},
              open(os.path.join(out, 'family_map_frozen.json'), 'w'), ensure_ascii=False)

    # ---------- 2. 逐段配对 ----------
    allpair, bandrows, allparent = [], [], []
    for seg in A.segments.split(','):
        S = G.seg(seg, verbose=False)
        ctx = GD.GCtx(S)
        R = refs(S, ctx)
        dts = pd.DatetimeIndex(S.dates)
        n8 = {}
        for b, d in BLOCK_DIR.items():
            pat = os.path.join(G.RES, d, 'daily_gross_%s_%s_s*.parquet' % (b, seg))
            for fg in sorted(glob.glob(pat)):
                ft = fg.replace('daily_gross_', 'daily_turn_')
                if not os.path.exists(ft):
                    continue
                gg = pd.read_parquet(fg)
                tt = pd.read_parquet(ft)
                v = gg.values - tt.values * F.COST / 1e4
                for i, c in enumerate(gg.columns):
                    n8[c] = v[:, i]
        if not n8:
            print('  %s 无日账本, 跳过' % seg, flush=True)
            continue
        cols = list(n8)
        X = np.column_stack([n8[c] for c in cols])
        Xall = X
        print('  %s: %d 列日 net8, %.0fs' % (seg, X.shape[1], time.time() - t0), flush=True)

        Wm = boot_weights(S.T, A.nboot, BLK, seed=abs(hash(seg)) % 10 ** 6)
        for rname in ('R1', 'R2', 'Blend3'):
            ref = R[rname][0] - R[rname][2] * F.COST / 1e4
            D = X - ref[:, None]
            D = np.where(np.isfinite(D), D, np.nan)
            mu = np.nanmean(D, axis=0) * 252 * 100
            tv = np.array([hac_t(D[:, j])[1] for j in range(D.shape[1])])
            # 共 draw bootstrap: 在【重抽到的有效日】上求均值 —— 不能把 NaN 日当 0 差,
            # 否则缺日多的配置会被系统性拉向零。
            V = np.isfinite(D).astype(float)
            Dz = np.where(np.isfinite(D), D, 0.0)
            num = Wm @ Dz
            den = Wm @ V
            with np.errstate(invalid='ignore', divide='ignore'):
                BM = np.where(den > 0, num / den, np.nan) * 252 * 100   # (nb, ncols) 年化点
            se = np.nanstd(BM, axis=0, ddof=1)
            lo = np.nanpercentile(BM, 2.5, axis=0)
            hi = np.nanpercentile(BM, 97.5, axis=0)

            # ---- 族内【共 draw max-|t|】同时带 (brief §10 主口径) ----
            # 对每个 bootstrap draw b 取全族最大 |BM_bj − mu_j| / se_j, 再取其 95 分位,
            # 得到该族的同时临界值。这是真正的同时带; 用观察到的 |t| 分位数是不对的。
            fam_col = np.array([FAM.get((c, seg), 'F-other') for c in cols])
            crit_of, simlo, simhi = {}, np.full(len(cols), np.nan), np.full(len(cols), np.nan)
            with np.errstate(invalid='ignore', divide='ignore'):
                Z = (BM - mu[None, :]) / np.where(se > 0, se, np.nan)[None, :]
            for fam in np.unique(fam_col):
                jj = np.flatnonzero(fam_col == fam)
                Zf = Z[:, jj]
                ok = np.isfinite(Zf)
                Zf = np.where(ok, np.abs(Zf), 0.0)
                mx = Zf.max(axis=1)
                crit = float(np.percentile(mx[np.isfinite(mx)], 95)) if np.isfinite(mx).any() \
                    else np.nan
                crit_of[fam] = crit
                simlo[jj] = mu[jj] - crit * se[jj]
                simhi[jj] = mu[jj] + crit * se[jj]
            allpair.append(pd.DataFrame(dict(
                segment=seg, ref=rname, config_id=cols, family=fam_col,
                delta_net8_ann=mu, hac_t=tv, boot_se=se, ind_lo=lo, ind_hi=hi,
                sim_crit=[crit_of.get(f, np.nan) for f in fam_col],
                sim_lo=simlo, sim_hi=simhi)))
        # ---- vs 直接母体 (换腿/第四腿必须对自己的父比, 不能只对 R2 比) ----
        pmap = (MS[(MS.segment == seg) & (MS.role == 'economic')]
                .dropna(subset=['parent_cfg'])[['config_id', 'parent_cfg']]
                .drop_duplicates().set_index('config_id')['parent_cfg'].to_dict())
        pcache = {}
        prow = []
        colpos = {c: i for i, c in enumerate(cols)}
        for cid, pcid in pmap.items():
            if cid not in colpos:
                continue
            if pcid not in pcache:
                try:
                    pp = ctx.run(GD.parse_cfg(pcid))[0]
                    pcache[pcid] = pp[0] - pp[2] * F.COST / 1e4
                except Exception as e:
                    pcache[pcid] = None
                    print('    母体 %s 建不出: %s' % (pcid, str(e)[:80]), flush=True)
            pn8 = pcache[pcid]
            if pn8 is None:
                continue
            dd = Xall[:, colpos[cid]] - pn8
            m_, t_ = hac_t(dd)
            prow.append(dict(segment=seg, config_id=cid, parent_cfg=pcid,
                             delta_vs_parent_ann=float(np.nanmean(dd)) * 252 * 100,
                             hac_t_vs_parent=t_,
                             n_days=int(np.isfinite(dd).sum())))
        if prow:
            allparent.append(pd.DataFrame(prow))
            print('  %s vs 母体 %d 条 (%d 个不同母体) %.0fs'
                  % (seg, len(prow), len(pcache), time.time() - t0), flush=True)
        del X, Xall
        print('  %s 配对完成 %.0fs' % (seg, time.time() - t0), flush=True)

    if not allpair:
        print('没有可配对的日账本'); return
    PR = pd.concat(allpair, ignore_index=True)
    PR.to_csv(os.path.join(out, 'paired_vs_refs.csv'), index=False)
    if allparent:
        pd.concat(allparent, ignore_index=True).to_csv(
            os.path.join(out, 'paired_vs_parent.csv'), index=False)

    # ---------- 3. 族内同时带 (共 draw max-|t|) ----------
    J = PR[PR.family != 'F-control']
    for (seg, ref, fam), gdf in J.groupby(['segment', 'ref', 'family']):
        bandrows.append(dict(segment=seg, ref=ref, family=fam, n=len(gdf),
                             sim_crit=float(gdf.sim_crit.iloc[0]),
                             n_pos_point=int((gdf.delta_net8_ann > 0).sum()),
                             n_ind_pos=int((gdf.ind_lo > 0).sum()),
                             n_ind_neg=int((gdf.ind_hi < 0).sum()),
                             n_sim_pos=int((gdf.sim_lo > 0).sum()),
                             n_sim_neg=int((gdf.sim_hi < 0).sum()),
                             median_delta=float(gdf.delta_net8_ann.median()),
                             q90_delta=float(gdf.delta_net8_ann.quantile(0.9)),
                             max_delta=float(gdf.delta_net8_ann.max()),
                             min_delta=float(gdf.delta_net8_ann.min())))
    pd.DataFrame(bandrows).to_csv(os.path.join(out, 'family_bands.csv'), index=False)

    # ---------- 4. 四种计数 ----------
    # brief §10: 全体描述符 / 公式 / 真实路径 / 有效比较数 四种计数同时报。
    #   描述符 = 登记名个数 (同名不同处理算两个)
    #   公式   = 去掉 selector / 否决 / 方向后的【核表达式】个数
    #   真实路径 = path_key 个数 (完全相同的计算只算一次) -> 同时带的真实重数
    #   有效比较数 = 真实路径数 (别名不额外增加多重性)
    man = pd.read_csv(os.path.join(G.RES, 'H0', 'H_manifest.csv'))
    man['formula'] = (man.descriptor_id.astype(str).str.split('|').str[0]
                      .str.replace(r'~sel:[A-Z]+', '', regex=True))
    cnt = []
    for fam, gdf in MS[MS.role == 'economic'].groupby('family'):
        ids = set(gdf.config_id)
        sub = man[man.descriptor_id.isin(ids)]
        nrp = int(sub.path_key.nunique()) if len(sub) else np.nan
        cnt.append(dict(family=fam, n_descriptors=len(ids),
                        n_formula=int(sub.formula.nunique()) if len(sub) else np.nan,
                        n_real_paths=nrp,
                        n_distinct_leg_sets=int(sub.lineage.nunique()) if len(sub) else np.nan,
                        n_effective_comparisons=nrp))
    pd.DataFrame(cnt).to_csv(os.path.join(out, 'family_counts.csv'), index=False)

    MS.to_csv(os.path.join(out, 'master_summary.csv'), index=False)
    print('DONE merge1: paired %d 行, 族 %d, %.0fs' % (len(PR), len(bandrows), time.time() - t0))


if __name__ == '__main__':
    main()
