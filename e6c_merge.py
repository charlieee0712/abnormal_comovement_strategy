# -*- coding: utf-8 -*-
"""E6c 阶段 4: merge. full 指标全部从日序列重算; 配对/分解/bootstrap/逐年; 出 summary.txt."""
import os, io, json, hashlib
import numpy as np, pandas as pd
from e6c_holding_horizon import (nw_stats, score_hac, HS, HMAX, MATURE_START, SEGS, COST, COST12,
                                 ANCHOR_MAP, EDGES, SERVICE_REF, ATOL_ID)
from event_study import PERIODS

MAIN_H = [3, 5, 10, 15, 20]
NBOOT, BLOCK_L = 2000, 60

def _sub_seed(ns):
    return int.from_bytes(hashlib.sha256(('20260904/' + ns).encode()).digest()[:8], 'big') % (2 ** 32)

def _stationary_idx(n, L, rng):
    """stationary bootstrap: 几何块长, 期望 L, 环绕"""
    out = np.empty(n, dtype=np.int64); i = 0; p = 1.0 / L
    while i < n:
        s = rng.randint(n); ln = min(rng.geometric(p), n - i)
        out[i:i + ln] = (s + np.arange(ln)) % n; i += ln
    return out

def merge(OUT):
    log = []
    def P(s=''):
        print(s, flush=True); log.append(s)
    sf = pd.concat([pd.read_csv(os.path.join(OUT, 'sf_%s.csv' % p)) for p in SEGS], ignore_index=True)
    dl = pd.concat([pd.read_parquet(os.path.join(OUT, 'daily_%s.parquet' % p)) for p in SEGS], ignore_index=True)
    br = pd.concat([pd.read_parquet(os.path.join(OUT, 'bridge_%s.parquet' % p)) for p in SEGS], ignore_index=True)
    pf = pd.concat([pd.read_csv(os.path.join(OUT, 'profile_%s.csv' % p)) for p in SEGS], ignore_index=True)
    ag = pd.concat([pd.read_csv(os.path.join(OUT, 'age_%s.csv' % p)) for p in SEGS], ignore_index=True)
    ex = pd.concat([pd.read_csv(os.path.join(OUT, 'exposure_%s.csv' % p)) for p in SEGS], ignore_index=True)
    cr = pd.concat([pd.read_csv(os.path.join(OUT, 'config_registry_%s.csv' % p)) for p in SEGS], ignore_index=True)
    sf.to_csv(os.path.join(OUT, 'sf_all.csv'), index=False)
    dl.to_parquet(os.path.join(OUT, 'daily_all.parquet'))
    pf.to_csv(os.path.join(OUT, 'profile_all.csv'), index=False)
    ag.to_csv(os.path.join(OUT, 'event_age_profiles.csv'), index=False)
    ex.to_csv(os.path.join(OUT, 'execution_exposure_audit.csv'), index=False)
    cr.to_csv(os.path.join(OUT, 'config_registry.csv'), index=False)
    dl['date'] = pd.to_datetime(dl['date'])
    cfgs = list(dict.fromkeys(dl.cfg)); P('[merge] cfgs=%d  H=%d  rows=%d' % (len(cfgs), dl.hold.nunique(), len(dl)))

    # ---- common_mature 掩码 (每段索引 >= 81) ----
    mat = {}
    for p in SEGS:
        d = np.sort(dl[dl.period == p].date.unique())
        mat[p] = set(pd.to_datetime(d[MATURE_START:]))
    dl['mature'] = [d in mat[p] for p, d in zip(dl.period, dl.date)]

    # ---- 宽表: net8 / gross / cost / turnover / position, index=(period,date) ----
    # 注意: pivot_table 会丢掉"该列全为 NaN"的日期行, 各列丢的行不同 -> 必须 reindex 到统一主索引
    master = pd.MultiIndex.from_frame(dl[['period', 'date']].drop_duplicates().sort_values(['period', 'date']))
    def wide(col):
        return dl.pivot_table(index=['period', 'date'], columns=['cfg', 'hold'], values=col).reindex(master)
    NET = wide('net8'); GRO = wide('gross'); CST = wide('cost8'); POS = wide('position'); TRN = wide('turnover')
    N12 = wide('net12')
    midx = master
    P('[merge] master index=%d 行 (各宽表已对齐)' % len(midx))
    mature_mask = np.array([d in mat[p] for p, d in midx])
    yr = np.array([d.year for _, d in midx])

    # ---- full / 段 指标 (从日序列重算) ----
    rows = []
    for cfg in cfgs:
        for H in HS:
            k = (cfg, H)
            if k not in NET.columns: continue
            for scope, msk in (('legacy_all', np.ones(len(midx), bool)), ('common_mature', mature_mask)):
                x = NET[k].values[msk]; g = GRO[k].values[msk]; c = CST[k].values[msk]
                n12 = N12[k].values[msk]; pz = POS[k].values[msk]; tr = TRN[k].values[msk]
                a_n, _, t_n, n = nw_stats(x, L=max(H, 1)); a_g, _, _, _ = nw_stats(g, L=max(H, 1))
                a_c, _, _, _ = nw_stats(c, L=max(H, 1)); a_12, _, t12, _ = nw_stats(n12, L=max(H, 1))
                _, _, t5, _ = nw_stats(x, L=5)
                # fixedmix: 各段去 full 均值后的 Bartlett 二次型之和 / n^2
                mu = np.nanmean(x); num = 0.0; nn = 0
                for p in SEGS:
                    sel = (np.array([q for q, _ in midx]) == p)[msk]
                    z = x[sel] - mu
                    if len(z) < 3: continue
                    e = z - z.mean(); S = e @ e
                    for l in range(1, max(H, 1) + 1):
                        if l < len(e): S += 2 * (1 - l / (max(H, 1) + 1.0)) * (e[l:] @ e[:-l])
                    num += S; nn += len(z)
                t_fix = mu / np.sqrt(num / nn ** 2) if (nn and num > 0) else np.nan
                rows.append(dict(cfg=cfg, hold=H, scope=scope, span='full', net8_ann=a_n, net12_ann=a_12,
                                 gross_ann=a_g, cost_ann=a_c, nw_net8=t_n, nw_net12=t12, nw5=t5,
                                 nw_full_fixedmix=t_fix, n=n, turn_eval=252 * np.nanmean(tr),
                                 pos_mean=np.nanmean(pz),
                                 capital_day_net=25200 * np.nansum(x) / np.nansum(pz) if np.nansum(pz) > 0 else np.nan))
    full = pd.DataFrame(rows); full.to_csv(os.path.join(OUT, 'full_summary.csv'), index=False)

    # ---- Δ vs 自身 H5 / Δservice / 相邻差 ----
    def paired(a_key, b_key, msk, L):
        if a_key not in NET.columns or b_key not in NET.columns: return None
        d = NET[a_key].values[msk] - NET[b_key].values[msk]
        ann, t, n = score_hac(d, L)
        return ann, t, n, d
    hd = []
    for cfg in cfgs:
        for H in HS:
            for scope, msk in (('common_mature', mature_mask), ('legacy_all', np.ones(len(midx), bool))):
                r = paired((cfg, H), (cfg, 5), msk, max(H, 5))
                if r is None: continue
                ann, t, n, d = r
                rs = paired((cfg, H), SERVICE_REF, msk, max(H, 5))
                adj = paired((cfg, H), (cfg, H - 1), msk, max(H, 5)) if H > 1 else None
                dg = (GRO[(cfg, H)].values[msk] - GRO[(cfg, 5)].values[msk])
                dc = (CST[(cfg, 5)].values[msk] - CST[(cfg, H)].values[msk])
                hd.append(dict(cfg=cfg, hold=H, scope=scope, dnet_ann=ann, dnet_t=t if H != 5 else np.nan, n=n,
                               dgross_ann=252 * 100 * np.nanmean(dg), dcost_saving_ann=252 * 100 * np.nanmean(dc),
                               ident_err=float(np.nanmax(np.abs(d - (dg + dc)))),
                               dservice_ann=rs[0] if rs else np.nan, dservice_t=rs[1] if rs else np.nan,
                               dadj_ann=adj[0] if adj else np.nan, dadj_t=adj[1] if adj else np.nan,
                               turn_ratio=np.nanmean(TRN[(cfg, H)].values[msk]) / max(np.nanmean(TRN[(cfg, 5)].values[msk]), 1e-12),
                               H_times_turn=H * 252 * np.nanmean(TRN[(cfg, H)].values[msk])))
    hd = pd.DataFrame(hd); hd.to_csv(os.path.join(OUT, 'horizon_deltas.csv'), index=False)
    hd[hd.scope == 'common_mature'][['cfg', 'hold', 'dservice_ann', 'dservice_t']].to_csv(
        os.path.join(OUT, 'service_deltas.csv'), index=False)

    # ---- 三项分解 (日龄桥) ----
    # bridge 落盘时 reset_index() 用了原索引名(trade_date), 统一改名
    br = br.rename(columns={c: 'date' for c in br.columns if c in ('trade_date', 'index', 'level_0')})
    br['date'] = pd.to_datetime(br['date'])
    Kc = {}
    for cfg, gdf in br.groupby('cfg'):
        gdf = gdf.set_index(['period', 'date']).reindex(midx)
        Kc[cfg] = gdf[['K%d' % j for j in range(1, HMAX + 1)]].values
    dec = []
    for cfg in cfgs:
        if cfg not in Kc: continue
        K = Kc[cfg]; msk = mature_mask
        for H in HS:
            mn = min(H, 5)
            z = np.zeros(K.shape[0])
            early = (1.0 / H - 1.0 / 5) * np.nansum(K[:, :mn], axis=1)
            late = (1.0 / H) * (np.nansum(K[:, mn:H], axis=1) if H > mn else z) \
                   - (1.0 / 5) * (np.nansum(K[:, mn:5], axis=1) if 5 > mn else z)
            csav = CST[(cfg, 5)].values - CST[(cfg, H)].values
            dnet = NET[(cfg, H)].values - NET[(cfg, 5)].values
            err = float(np.nanmax(np.abs((early + late + csav)[msk] - dnet[msk])))
            dec.append(dict(cfg=cfg, hold=H, early_dilution_ann=252 * 100 * np.nanmean(early[msk]),
                            late_contrib_ann=252 * 100 * np.nanmean(late[msk]),
                            cost_saving_ann=252 * 100 * np.nanmean(csav[msk]),
                            dnet_ann=252 * 100 * np.nanmean(dnet[msk]), decomp_err=err))
    dec = pd.DataFrame(dec); dec.to_csv(os.path.join(OUT, 'capital_age_decomposition.csv'), index=False)
    P('[merge] 三项分解 max|err| = %.2e (atol %.0e)' % (np.nanmax(dec.decomp_err.values), ATOL_ID))

    # ---- 成本临界点 c* ----
    cf = []
    for cfg in cfgs:
        for H in HS:
            if H == 5: continue
            g5 = np.nanmean(GRO[(cfg, 5)].values[mature_mask]) * 252
            gh = np.nanmean(GRO[(cfg, H)].values[mature_mask]) * 252
            u5 = 252 * np.nanmean(TRN[(cfg, 5)].values[mature_mask])
            uh = 252 * np.nanmean(TRN[(cfg, H)].values[mature_mask])
            du = uh - u5
            cf.append(dict(cfg=cfg, hold=H, gross_diff_ann=100 * (gh - g5), turn_diff=du,
                           c_star_bp=1e4 * (gh - g5) / du if abs(du) >= 0.5 else np.nan,
                           note='' if abs(du) >= 0.5 else '无清晰交叉点(|ΔU|<0.5)'))
    pd.DataFrame(cf).to_csv(os.path.join(OUT, 'cost_frontier.csv'), index=False)

    # ---- 否决 x 持有期 ----
    vh = []
    for pa, ch in EDGES:
        for H in HS:
            if (pa, H) not in NET.columns or (ch, H) not in NET.columns: continue
            D = NET[(ch, H)].values - NET[(pa, H)].values
            D5 = NET[(ch, 5)].values - NET[(pa, 5)].values
            aD, tD, _ = score_hac(D[mature_mask], max(H, 1))
            aI, tI, _ = score_hac((D - D5)[mature_mask], max(H, 5))
            dgr = GRO[(ch, H)].values - GRO[(pa, H)].values
            dcs = CST[(pa, H)].values - CST[(ch, H)].values
            vh.append(dict(parent=pa, child=ch, hold=H, D_ann=aD, D_t=tD,
                           I_ann=aI if H != 5 else 0.0, I_t=tI if H != 5 else np.nan,
                           D_gross_ann=252 * 100 * np.nanmean(dgr[mature_mask]),
                           D_cost_saving_ann=252 * 100 * np.nanmean(dcs[mature_mask])))
    pd.DataFrame(vh).to_csv(os.path.join(OUT, 'veto_horizon_deltas.csv'), index=False)

    # ---- 逐年 / 留一年 ----
    yrs = sorted(set(yr)); yrows = []; lo = []
    for cfg in cfgs:
        for H in HS:
            d = NET[(cfg, H)].values - NET[(cfg, 5)].values
            for y in yrs:
                s = d[(yr == y) & mature_mask]
                if len(s) < 20: continue
                yrows.append(dict(cfg=cfg, hold=H, year=int(y), dnet_ann=252 * 100 * np.nanmean(s), n=len(s),
                                  incomplete=bool(y == 2026)))
            for y in yrs:
                s = d[(yr != y) & mature_mask]
                lo.append(dict(cfg=cfg, hold=H, drop_year=int(y), dnet_ann=252 * 100 * np.nanmean(s)))
    pd.DataFrame(yrows).to_csv(os.path.join(OUT, 'yearly_deltas.csv'), index=False)
    pd.DataFrame(lo).to_csv(os.path.join(OUT, 'leave_one_year.csv'), index=False)

    # ---- bootstrap (共用 draw; 两族联合带) ----
    famA = [(c, H) for c in cfgs for H in HS if H != 5 and (c, H) in NET.columns]
    XA = np.column_stack([NET[(c, H)].values - NET[(c, 5)].values for c, H in famA])
    famB = [(c, H) for c in cfgs for H in HS if (c, H) in NET.columns]
    XB = np.column_stack([NET[(c, H)].values - NET[SERVICE_REF].values for c, H in famB])
    XA = np.nan_to_num(XA[mature_mask]); XB = np.nan_to_num(XB[mature_mask])
    segs_of = np.array([p for p, _ in midx])[mature_mask]
    rng = np.random.RandomState(_sub_seed('bootstrap/main'))
    bootA = np.empty((NBOOT, XA.shape[1]), np.float64); bootB = np.empty((NBOOT, XB.shape[1]), np.float64)
    seg_pos = {p: np.where(segs_of == p)[0] for p in SEGS}
    for b in range(NBOOT):
        idx = np.concatenate([seg_pos[p][_stationary_idx(len(seg_pos[p]), BLOCK_L, rng)] for p in SEGS])
        bootA[b] = XA[idx].mean(axis=0); bootB[b] = XB[idx].mean(axis=0)
    def summ(fam, X, boot, tag):
        th = X.mean(axis=0) * 252 * 100; bt = boot * 252 * 100
        lo95 = np.percentile(bt, 2.5, axis=0); hi95 = np.percentile(bt, 97.5, axis=0)
        s = bt.std(axis=0, ddof=1); s[s == 0] = np.nan
        q95 = np.nanquantile(np.nanmax(np.abs(bt - th) / s, axis=1), 0.95)
        return pd.DataFrame(dict(family=tag, cfg=[c for c, _ in fam], hold=[h for _, h in fam],
                                 theta=th, ci_lo=lo95, ci_hi=hi95, se=s,
                                 band_lo=th - q95 * s, band_hi=th + q95 * s, q95=q95, B_valid=NBOOT))
    bs = pd.concat([summ(famA, XA, bootA, 'vs_own_H5'), summ(famB, XB, bootB, 'vs_service_A4b_CVRv5@5')],
                   ignore_index=True)
    bs.to_csv(os.path.join(OUT, 'bootstrap_summary.csv'), index=False)
    io.open(os.path.join(OUT, 'bootstrap_manifest.json'), 'w', encoding='utf-8', newline='\n').write(
        json.dumps(dict(B=NBOOT, block_L=BLOCK_L, seed_root='20260904', scheme='stationary, per-segment, shared draw',
                        families={'vs_own_H5': len(famA), 'vs_service': len(famB)}), ensure_ascii=False, indent=1))
    P('[merge] bootstrap done B=%d famA=%d famB=%d' % (NBOOT, len(famA), len(famB)))

    # ---- summary.txt ----
    S = []
    def W(s=''): S.append(s)
    fm = full[(full.scope == 'common_mature')].set_index(['cfg', 'hold'])
    fl = full[(full.scope == 'legacy_all')].set_index(['cfg', 'hold'])
    W('E6c 持有期 1-20 日 x %d 配置  成本 %.0fbp(net12=%.0fbp)  common_mature 起点=%d' % (len(cfgs), COST, COST12, MATURE_START))
    W('\n== (A) 主读五档 (common_mature; net8/net12/gross/cost 年化%, turn, pos, n_actual, NW(L=H)) ==')
    hdr = ' | '.join('H%-2d' % h for h in MAIN_H)
    W('%-46s %s' % ('cfg', hdr))
    for cfg in cfgs:
        cells = []
        for h in MAIN_H:
            try: r = fm.loc[(cfg, h)]
            except KeyError: cells.append('  -  '); continue
            cells.append('%+5.2f/t%+4.2f' % (r.net8_ann, r.nw_net8))
        W('%-46s %s' % (cfg, ' | '.join(cells)))
    W('\n(同上, legacy_all 口径)')
    for cfg in cfgs:
        cells = []
        for h in MAIN_H:
            try: r = fl.loc[(cfg, h)]; cells.append('%+5.2f/t%+4.2f' % (r.net8_ann, r.nw_net8))
            except KeyError: cells.append('  -  ')
        W('%-46s %s' % (cfg, ' | '.join(cells)))
    W('\n== (B) Δ vs 自身 H5 (common_mature, 年化%, 配对 NW t; bootstrap 95% 逐点区间) ==')
    hc = hd[hd.scope == 'common_mature'].set_index(['cfg', 'hold'])
    bsA = bs[bs.family == 'vs_own_H5'].set_index(['cfg', 'hold'])
    for cfg in cfgs:
        cells = []
        for h in MAIN_H:
            if h == 5: cells.append('   base   '); continue
            try:
                r = hc.loc[(cfg, h)]; b = bsA.loc[(cfg, h)]
                cells.append('%+5.2f[%+4.2f,%+4.2f]' % (r.dnet_ann, b.ci_lo, b.ci_hi))
            except KeyError: cells.append('    -     ')
        W('%-46s %s' % (cfg, ' | '.join(cells)))
    W('\n== (C) 三项分解 (common_mature, 年化%; 早期稀释 / 晚期贡献 / 成本节省 = Δnet) ==')
    dm = dec.set_index(['cfg', 'hold'])
    for cfg in cfgs:
        for h in [3, 10, 20]:
            try: r = dm.loc[(cfg, h)]
            except KeyError: continue
            W('  %-44s H%-2d  早期 %+6.2f  晚期 %+6.2f  成本 %+6.2f  = Δnet %+6.2f (err %.1e)'
              % (cfg, h, r.early_dilution_ann, r.late_contrib_ann, r.cost_saving_ann, r.dnet_ann, r.decomp_err))
    W('\n== (D) 否决 x 持有期 (D_H = 子-父; I_H = D_H - D_5; common_mature) ==')
    vm = pd.DataFrame(vh).set_index(['parent', 'child', 'hold'])
    for pa, ch in EDGES:
        cells = []
        for h in MAIN_H:
            try: r = vm.loc[(pa, ch, h)]; cells.append('D%+5.2f I%+5.2f' % (r.D_ann, r.I_ann))
            except KeyError: cells.append('     -      ')
        W('  %-64s %s' % ('%s -> %s' % (pa[-28:], ch[-34:]), ' | '.join(cells)))
    W('\n== (E) 事件时间剖面 E 视图 (区间贡献 bp, 形成日均值) ==')
    pv = pf.groupby(['set_id', 'j'])['mean'].mean().unstack()
    zones = [('j1-3', range(1, 4)), ('j4-5', range(4, 6)), ('j6-10', range(6, 11)),
             ('j11-15', range(11, 16)), ('j16-20', range(16, 21))]
    W('  %-44s %s' % ('set', ' '.join('%8s' % z for z, _ in zones)))
    for sid in pv.index:
        W('  %-44s %s' % (sid[:44], ' '.join('%8.1f' % (1e4 * pv.loc[sid, list(js)].sum()) for _, js in zones)))
    W('\n== (F) 触发日龄 (share of names) ==')
    for sid, g in ag.groupby('set_id'):
        W('  %-20s %s' % (sid, ' '.join('age%d %.3f' % (int(r.age), r.share) for _, r in g.groupby('age').mean(numeric_only=True).reset_index().iterrows())))
    W('\n== (G) 可成交性暴露 (买/卖 被挡权重占比) ==')
    for _, r in ex.groupby(['cfg', 'hold']).mean(numeric_only=True).reset_index().iterrows():
        W('  %-34s H%-2d buy_blocked %.4f  sell_blocked %.4f' % (r.cfg, int(r.hold), r.buy_blocked_share, r.sell_blocked_share))
    W('\n== (I) 边界 ==')
    W('  RIGHT_BOUNDARY_OPEN: H 上限 = %d; 若最优在右端需更长轴才能定平台' % HMAX)
    # 二分组 vs 十分位留 50%: 直接比 mask 的 SHA (逐票相同则 sha 相同)
    sh = cr.pivot_table(index='period', columns='cfg', values='mask_sha', aggfunc='first')
    same = []
    for a, b in (('M_mean2_bin', 'M_mean2_dec'), ('M_mean3_v2_bin', 'M_mean3_v2_dec')):
        if a in sh.columns and b in sh.columns:
            eq = int((sh[a] == sh[b]).sum()); same.append('%s vs %s: %d/%d 段 mask 逐票相同' % (a, b, eq, len(sh)))
    W('  二分组 vs 十分位留50%: ' + '; '.join(same))
    W('\n[MERGE DONE] cfgs=%d rows_daily=%d' % (len(cfgs), len(dl)))
    io.open(os.path.join(OUT, 'summary.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(S) + '\n')
    io.open(os.path.join(OUT, 'limit_register.md'), 'w', encoding='utf-8', newline='\n').write(
        '# limit_register\n\n'
        '- **M 视图(前向携带标记价)**：按用户 2026-09-04 调整 3 定为 best-effort，本轮**未实现**；'
        '主口径 E 视图(引擎同构)与 A 视图口径的差异未量化。估值 delta 同缺。\n'
        '- **漂移费用代理**：未实现(诊断项)。\n'
        '- **cohort 逐形成日明细未落盘**：剖面按形成日聚合后落 `profile_all.csv`，'
        'cohort 级 bootstrap 因此未做；Δ 类 bootstrap 已按日历日 stationary 抽样完成。\n'
        '- **新事件起点子集 / 持有存续长度分布**：未实现。\n'
        '- 以上均为 brief §2E/§2C/§2G 的诊断层，不影响 (A)-(D) 主表与会计恒等式。\n')
    P('\n'.join(S[-3:]))
    io.open(os.path.join(OUT, 'log_merge.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(log) + '\n')
