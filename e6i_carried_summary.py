#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i carried 汇总 (plan §9.1 / §9.2; brief §10): C1 (N x 行业宽度) 与 C2 (冲击成本透镜) 的读表, 供 part3 (Q10 / Q7 冲击视图)。
后段 C1 / C2 母体格是记录 B 前封存的旧输入产物 -> 用技术包 E6I-B-CARRIED-C1C2 过守卫读取 (sealed_read)。
C1:
  T1 部署视图 (全日历 min(N, N_t)): 每 (段, 母体, q, 评分口径, 分配, N, B) 的 64 seed 均值 / 标准差 / 可行日占比 / B_eff / HHI /
     采样域人数 / 实际持股 / 空仓日;
  T2 严格交叉 (同日共同可行支持): 每个被比较的格对 (固定 N 的 B16 vs B8; 固定 B 的 N250 vs N100) 取两格同日都可行的交易日; 此表报可行 seed 数与共同日数;
  T3 固定 N 比 B (B16 − B8) 与 固定 B 比 N (N250 − N100): 严格视图下逐 seed 配对差的均值 / 标准差 / 为正占比;
  T4 桥: full_pool0 (同一计数预算) / topN_core / randomN (64 seed 均值) / 源母体;
  T5 仪器效应: frozen 口径下计数预算 − 源分箱 (R2 / A06)。
C2:
  T6 每 (段, 路线, 母体, H) 的子 − 同 H 母体 在无冲击与平方根冲击 A{1,5,10} 亿 x κ{.25,.5,1} 下的描述符中位;
  T7 Q/ADV20 日频压力代理 (A = 1 亿) 子 vs 母体; T8 容量根 (只在 a/b>0 且 b≠0 时有正根) 的计数。
输出 carried/summary/*.csv。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import glob
import time

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I

R = I.RES
PKG = 'E6I-B-CARRIED-C1C2'
OUT = os.path.join(R, 'carried', 'summary')
MIN_COMMON = 60     # 严格交叉逐 seed 的最少共同可行交易日 (约 3 个月); 不足 = 支持不足, 不进均值


def c1_files(seg):
    if seg in I.POST_SEGS:
        base = os.path.join(I.SEALED, seg)
        csvs = sorted(f for f in glob.glob(os.path.join(base, 'c1_*.csv')) if '_feasible' not in f and '_63-63' not in f)   # 冒烟 (seed 63) 与正式 seed 60-63 重复, 不计
        out = []
        for f in csvs:
            name = os.path.basename(f)[:-4]
            d = I.sealed_read_csv(seg, name, package_id=PKG)
            fe = I.sealed_read_csv(seg, name + '_feasible', package_id=PKG) \
                if os.path.exists(os.path.join(base, name + '_feasible.csv')) else None
            out.append((d, os.path.join(base, name + '.npz'), fe))
        return out
    base = os.path.join(R, 'carried', 'C1', seg)
    out = []
    for f in sorted(x for x in glob.glob(os.path.join(base, 'c1_*.csv')) if '_feasible' not in x and '_63-63' not in x):   # 排除冒烟文件
        fe = f[:-4] + '_feasible.csv'
        out.append((pd.read_csv(f), f[:-4] + '.npz', pd.read_csv(fe) if os.path.exists(fe) else None))
    return out


def c1(seg):
    parts = c1_files(seg)
    if not parts:
        return None
    rows = pd.concat([d for d, _, _ in parts], ignore_index=True)
    rows['segment'] = seg
    # 严格交叉 (plan §9.1 "同日共同可行支持"): 对每个被比较的格对 (固定 N 的 B16 vs B8; 固定 B 的 N250 vs N100)
    # 取两格同日都可行的交易日, 在这些日子上重算两格的年化 net8 并配对相减 (9 格全交集在小池段常为空, 不用)
    strict = []
    pairs = [('B16−B8', 'N=%d' % n, (n, 8), (n, 16)) for n in (100, 150, 250)] + \
            [('N250−N100', 'B=%d' % b, (100, b), (250, b)) for b in (8, 12, 16)]
    for d, npz, fe in parts:
        if fe is None or not len(d) or 'cross' not in set(d.part):
            continue
        z = np.load(npz)
        kpos = {k: i for i, k in enumerate(z['keys'])}
        net = z['net8']
        fcols = [c for c in fe.columns if c.startswith('f')]
        feas = {r_.domain: np.asarray([bool(getattr(r_, c)) for c in fcols]) for r_ in fe.itertuples()}
        cr = d[d.part == 'cross']
        for (seed, alloc, mn, qq, sc), g in cr.groupby(['seed', 'alloc', 'mother', 'q', 'scope']):
            cell = {(int(r_.N), int(r_.B)): r_ for r_ in g.itertuples()}
            for ctr, fixed, ca, cb in pairs:
                if ca not in cell or cb not in cell:
                    continue
                ra, rb = cell[ca], cell[cb]
                if ra.domain not in feas or rb.domain not in feas:
                    continue
                common = feas[ra.domain] & feas[rb.domain]
                if not common.any():
                    strict.append(dict(segment=seg, mother=mn, q=qq, scope=sc, alloc=alloc, seed=seed, contrast=ctr,
                                       fixed=fixed, d=np.nan, common_days=0))
                    continue
                with np.errstate(all='ignore'):
                    va = np.nanmean(np.where(common, net[kpos[ra.key]], np.nan)) * I.ANN
                    vb = np.nanmean(np.where(common, net[kpos[rb.key]], np.nan)) * I.ANN
                strict.append(dict(segment=seg, mother=mn, q=qq, scope=sc, alloc=alloc, seed=seed, contrast=ctr,
                                   fixed=fixed, net8_a=va, net8_b=vb, d=vb - va, common_days=int(common.sum())))
    return rows, pd.DataFrame(strict)


def c1_tables(rows, strict):
    cr = rows[rows.part == 'cross']
    t1 = cr.groupby(['segment', 'mother', 'q', 'scope', 'alloc', 'N', 'B']).agg(
        n_seed=('seed', 'nunique'), net8_mean=('net8_ann', 'mean'), net8_sd=('net8_ann', 'std'),
        feasible_frac=('feasible_frac', 'mean'), B_eff=('B_eff_mean', 'mean'), HHI=('HHI_mean', 'mean'),
        omega_n=('omega_n_mean', 'mean'), held=('held_mean', 'mean'), empty_days=('empty_days', 'mean'),
        logmcap=('logmcap_mean', 'mean'), turnover=('turnover_mean', 'mean')).reset_index()
    t2 = strict.groupby(['segment', 'contrast', 'fixed', 'alloc', 'scope']).agg(
        n=('d', 'size'), n_feasible=('d', lambda x: int(x.notna().sum())), common_days_mean=('common_days', 'mean'),
        common_days_min=('common_days', 'min')).reset_index() if len(strict) else pd.DataFrame()
    t3 = strict.dropna(subset=['d']).groupby(['segment', 'mother', 'q', 'scope', 'alloc', 'contrast', 'fixed']).agg(
        mean=('d', 'mean'), sd=('d', 'std'), share_pos=('d', lambda x: (x > 0).mean()), n_seed=('d', 'size'),
        common_days=('common_days', 'mean')).reset_index() if len(strict) else pd.DataFrame()
    # 数据充分性规则 (报告口径, 不按结果取舍): 逐 seed 的共同可行日 < MIN_COMMON 视为支持不足, 不进均值; 两种都存
    sf = strict[strict.common_days >= MIN_COMMON].dropna(subset=['d']) if len(strict) else strict
    t3f = sf.groupby(['segment', 'mother', 'q', 'scope', 'alloc', 'contrast', 'fixed']).agg(
        mean=('d', 'mean'), sd=('d', 'std'), share_pos=('d', lambda x: (x > 0).mean()), n_seed=('d', 'size'),
        common_days=('common_days', 'mean')).reset_index() if len(sf) else pd.DataFrame()
    t3 = (t3, t3f)
    br = rows[rows.part.isin(['bridge_full', 'bridge_topN', 'bridge_randomN', 'mother_source'])].copy()
    br['N'] = br.get('N')
    t4 = br.groupby(['segment', 'part', 'mother', 'q', 'scope', 'N'], dropna=False).agg(
        n=('net8_ann', 'size'), net8_mean=('net8_ann', 'mean'), net8_sd=('net8_ann', 'std'),
        held=('held_mean', 'mean'), empty_days=('empty_days', 'mean')).reset_index()
    ib = rows[rows.part == 'instrument_bins'][['segment', 'mother', 'q', 'alloc', 'N', 'B', 'seed', 'net8_ann']]
    cf = cr[cr.scope == 'frozen'][['segment', 'mother', 'q', 'alloc', 'N', 'B', 'seed', 'net8_ann']]
    m = cf.merge(ib, on=['segment', 'mother', 'q', 'alloc', 'N', 'B', 'seed'], suffixes=('_count', '_bins'))
    m['d'] = m.net8_ann_count - m.net8_ann_bins
    t5 = m.groupby(['segment', 'mother', 'q', 'N']).agg(mean=('d', 'mean'), sd=('d', 'std'),
                                                        share_pos=('d', lambda x: (x > 0).mean()), n=('d', 'size')).reset_index()
    return t1, t2, t3, t4, t5


def c2(seg):
    base = os.path.join(R, 'carried', 'C2', seg)
    kids = [pd.read_csv(f) for f in sorted(glob.glob(os.path.join(base, 'c2_*_[0-9][0-9].csv')))]
    if seg in I.POST_SEGS and os.path.exists(os.path.join(I.SEALED, seg, 'c2_mothers.csv')):
        mo = I.sealed_read_csv(seg, 'c2_mothers', package_id=PKG)
    elif os.path.exists(os.path.join(base, 'c2_mothers.csv')):
        mo = pd.read_csv(os.path.join(base, 'c2_mothers.csv'))
    else:
        mo = None
    if not kids or mo is None:
        return None
    k = pd.concat(kids, ignore_index=True)
    if 'status' in k.columns:
        k = k[k.status.isna() | (k.status == 'SUCCEEDED')]
    return k, mo


def c2_tables(k, mo, seg, panel):
    cols = [c for c in k.columns if c.startswith('net8_minus_sqrt_')]
    mm = mo[['mother_id', 'H', 'net8_ann'] + cols].rename(columns={c: 'm_' + c for c in ['net8_ann'] + cols})
    k = k.merge(mm, on=['mother_id', 'H'], how='left')
    for c in ['net8_ann'] + cols:
        k['d_' + c] = k[c] - k['m_' + c]
    k['segment'] = seg
    if panel is not None:
        k = k.merge(panel, on='descriptor_id', how='left')
    grp = ['segment', 'route_id', 'mother_id', 'H']
    t6 = k.groupby(grp)[['d_net8_ann'] + ['d_' + c for c in cols]].median().reset_index()
    t6['n'] = k.groupby(grp).size().values
    t7 = k.groupby(grp).agg(q_adv_A1_wmean=('q_adv_A1_wmean', 'median')).reset_index()
    t7 = t7.merge(mo[['mother_id', 'H', 'q_adv_A1_wmean']].rename(columns={'q_adv_A1_wmean': 'mother_q_adv_A1'}),
                  on=['mother_id', 'H'], how='left')
    t7['segment'] = seg
    rc = [c for c in k.columns if c.startswith('root_A_yi_')]
    t8 = k.groupby(grp)[rc].apply(lambda x: pd.Series({c: int(np.isfinite(pd.to_numeric(x[c], errors='coerce')).sum())
                                                       for c in rc})).reset_index() if rc else pd.DataFrame()
    return t6, t7, t8, k


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    allrows, allstrict = [], []
    for seg in I.SEGMENTS:
        r = c1(seg)
        if r is not None:
            allrows.append(r[0])
            allstrict.append(r[1])
            print('[C1 %s] 行 %d, 严格格 %d (%.0fs)' % (seg, len(r[0]), len(r[1]), time.time() - t0), flush=True)
    if allrows:
        strict_all = pd.concat(allstrict, ignore_index=True) if allstrict else pd.DataFrame()
        t1, t2, t3, t4, t5 = c1_tables(pd.concat(allrows, ignore_index=True), strict_all)
        for nm, t in (('C1_T1_deploy', t1), ('C1_T2_strict', t2), ('C1_T3_contrasts', t3[0]),
                      ('C1_T3_contrasts_min%d' % MIN_COMMON, t3[1]), ('C1_T4_bridges', t4), ('C1_T5_instrument', t5),
                      ('C1_strict_rows', strict_all)):
            I.atomic_write_csv(os.path.join(OUT, nm + '.csv'), t)
    pp = os.path.join(R, 'reports', 'part2_tables', 'descriptor_panel_post.csv')
    panel = pd.read_csv(pp, usecols=['descriptor_id', 'direction_role', 'policy', 'strength', 'role'],
                        low_memory=False) if os.path.exists(pp) else None
    t6s, t7s, t8s, ks = [], [], [], []
    for seg in I.SEGMENTS:
        r = c2(seg)
        if r is None:
            continue
        t6, t7, t8, k = c2_tables(r[0], r[1], seg, panel)
        t6s.append(t6), t7s.append(t7), t8s.append(t8), ks.append(k)
        print('[C2 %s] 子描述符 %d (%.0fs)' % (seg, len(k), time.time() - t0), flush=True)
    if t6s:
        I.atomic_write_csv(os.path.join(OUT, 'C2_T6_impact_delta.csv'), pd.concat(t6s, ignore_index=True))
        I.atomic_write_csv(os.path.join(OUT, 'C2_T7_pressure.csv'), pd.concat(t7s, ignore_index=True))
        I.atomic_write_csv(os.path.join(OUT, 'C2_T8_roots.csv'), pd.concat(t8s, ignore_index=True))
        I.atomic_write_csv(os.path.join(OUT, 'C2_children_delta.csv'), pd.concat(ks, ignore_index=True))
    I.write_receipt(os.path.join(R, 'task_status', 'carried_summary.receipt.json'), 'carried:summary',
                    [os.path.join(OUT, f) for f in sorted(os.listdir(OUT))], elapsed_s=round(time.time() - t0, 1))
    print('carried 汇总完成 %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
