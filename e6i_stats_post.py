#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 3 后段统计 (brief §8 / §11; plan §8) —— 只在首次观察封存回执 (registry/first_look_receipts.json,
status=SEALED) 之后运行; 只读合并产物, 不产生新账户。与推导段统计 (e6i_stats.py) 同一套函数、同一种子规则
(块长 L 的 draw 种子 = SEED + 1000·L + 段码; 推导两段段码 1 / 2 与推导统计逐位相同, 后段 3 / 4)。

口径 (scope):
  2019-2023 / 2024-2026   各后段 (段内 NW 与 bootstrap)
  post                    两后段按有效日合并 (段间不拼接: NW 方差按有效日加权合并; bootstrap 各段 draw 同编号相加)
  all4                    四段合并 (同上)
  all4_ex1516             四段合并去 2015、2016 两个日历年 (掩码, 不拼接; 只报点估与 NW)
  all4_ex2024p            四段去 2024-2026 段 (= 2010-2023; 只报点估与 NW)
每个 scope: d_net8_ann / se_nwH (+ lag max(2H,20)、lag 5 仅分段) / 机制读数 dcore (同人数核心) 与 dsamecap (同资本) 的点估
与 NW(lag H) / 三层同时带 (need 域 = 路线 x 母体 / 轴 / 全 headline; 块 20; 仅分段、post、all4) / Z-MEAN /
δ ∈ {.10,.25,.50,1.00} 覆盖 / 可分辨尺度 / MDE80 / 状态词; 另: 逐年 (y2010..y2026) 与去一年 (LOYO, post 与 all4) /
两后段同号的 Z-MEAN / 四臂交互 (分段、post、all4)。
输出 statistics/post/: descriptor_stats_<scope>.csv, family_bands_post.csv, zmean_family_post.csv,
fourarm_interaction_post.csv; receipt。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_stats as ST

SEGS4 = list(I.SEGMENTS)
BOOT_CODE = {'2010-2014': 1, '2015-2018': 2, '2019-2023': 3, '2024-2026': 4}
MERGED = {'post': list(I.POST_SEGS), 'all4': SEGS4}


def seg_dates(seg):
    p = os.path.join(I.RES, 'm2', seg, 'calendar.npy')
    if os.path.exists(p):
        return pd.to_datetime(pd.Series(np.load(p)).astype(str), format='%Y%m%d').values
    return np.asarray(ST.seg_dates(seg))


def merged_mean_se(parts, Hs):
    """parts = [(X_seg, mask_rows or None)], 段间不拼接: 各段 NW(lag H) 按有效日加权合并。返回 (mu, se, n)。"""
    J = parts[0][0].shape[1]
    num = np.zeros(J)
    cnt = np.zeros(J)
    var = np.zeros(J)
    for X, _ in parts:
        m = np.isfinite(X)
        num += np.where(m, X, 0.0).sum(0)
        cnt += m.sum(0)
    se = np.full(J, np.nan)
    for h in np.unique(Hs):
        cols = np.flatnonzero(Hs == h)
        vv = np.zeros(len(cols))
        for X, _ in parts:
            _, s_, n_ = ST.nw_se_masked(X[:, cols], int(h))
            vv += np.where(n_ > 0, (n_ * s_) ** 2, 0.0)
        with np.errstate(all='ignore'):
            se[cols] = np.sqrt(vv) / cnt[cols]
    with np.errstate(all='ignore'):
        mu = num / cnt
    return mu, se, cnt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--draws', type=int, default=ST.B_DRAWS)
    a = ap.parse_args()
    t0 = time.time()
    fl = json.load(open(os.path.join(I.RES, 'registry', 'first_look_receipts.json')))
    if fl.get('status') != 'SEALED':
        raise SystemExit('首次观察回执不是 SEALED -> 不读后段结果')
    od = os.path.join(I.RES, 'statistics', 'post')
    os.makedirs(od, exist_ok=True)
    data = {}
    for seg in SEGS4:
        meta, arrs, T = ST.load_segment(seg)
        dates = pd.DatetimeIndex(seg_dates(seg))
        assert len(dates) == T, (seg, len(dates), T)
        data[seg] = [meta, arrs, T, dates]
        print('[%s] 描述符 %d x 日 %d (%.0fs)' % (seg, len(meta), T, time.time() - t0), flush=True)
    common = sorted(set.intersection(*[set(data[s][0].descriptor_id) for s in SEGS4]))
    for seg in SEGS4:
        meta, arrs, T, dates = data[seg]
        order = meta.set_index('descriptor_id').index.get_indexer(common)
        data[seg] = [meta.iloc[order].reset_index(drop=True), {k: v[:, order] for k, v in arrs.items()}, T, dates]
    meta0 = data[SEGS4[0]][0]
    Hs = meta0.H.astype(int).values
    J = len(common)
    stats, boot = {}, {}
    # ---------------- 分段 (后段两段 + 推导两段的 bootstrap draw 供合并) ----------------
    ysum, ycnt = {}, {}
    for seg in SEGS4:
        meta, arrs, T, dates = data[seg]
        X = arrs['dnet8']
        yrs = dates.year.values
        m = np.isfinite(X)
        for y in sorted(set(yrs)):
            sel = yrs == y
            ysum[y] = np.where(m[sel], X[sel], 0.0).sum(0)
            ycnt[y] = m[sel].sum(0).astype(float)
        for L in ST.BLOCKS:
            W = ST.sb_weights(T, a.draws, L, ST.SEED + 1000 * L + BOOT_CODE[seg])
            boot[(seg, L)] = ST.boot_means(X, W)
        if seg not in I.POST_SEGS:
            continue
        res = pd.DataFrame({'descriptor_id': meta.descriptor_id})
        mu, _, n = ST.nw_se_masked(X, 1)
        res['n_days'] = n
        res['d_net8_ann'] = mu * I.ANN
        for tag, lagf in (('nwH', lambda h: h), ('nw2H20', lambda h: max(2 * h, 20)), ('nw5', lambda h: 5)):
            se = np.full(J, np.nan)
            for h in np.unique(Hs):
                cols = np.flatnonzero(Hs == h)
                _, s_, _ = ST.nw_se_masked(X[:, cols], lagf(int(h)))
                se[cols] = s_
            res['se_%s' % tag] = se * I.ANN
        for k in ('dcore', 'dsamecap'):
            mk, sk, _ = merged_mean_se([(arrs[k], None)], Hs)
            res['%s_ann' % k] = mk * I.ANN
            res['%s_se_nwH' % k] = sk * I.ANN
        for L in ST.BLOCKS:
            num, den = boot[(seg, L)]
            with np.errstate(all='ignore'):
                res['se_boot%d' % L] = np.nanstd(num / den, axis=0, ddof=1) * I.ANN
        stats[seg] = res
        print('[%s] 分段统计 (%.0fs)' % (seg, time.time() - t0), flush=True)
    # ---------------- 合并口径 ----------------
    for scope, segs in MERGED.items():
        res = pd.DataFrame({'descriptor_id': meta0.descriptor_id})
        mu, se, n = merged_mean_se([(data[s][1]['dnet8'], None) for s in segs], Hs)
        res['n_days'], res['d_net8_ann'], res['se_nwH'] = n, mu * I.ANN, se * I.ANN
        for k in ('dcore', 'dsamecap'):
            mk, sk, _ = merged_mean_se([(data[s][1][k], None) for s in segs], Hs)
            res['%s_ann' % k] = mk * I.ANN
            res['%s_se_nwH' % k] = sk * I.ANN
        for L in ST.BLOCKS:
            nn = sum(boot[(s, L)][0] for s in segs)
            dd = sum(boot[(s, L)][1] for s in segs)
            boot[(scope, L)] = (nn, dd)
            with np.errstate(all='ignore'):
                res['se_boot%d' % L] = np.nanstd(nn / dd, axis=0, ddof=1) * I.ANN
        ys = sorted(y for y in ysum if any(y in set(data[s][3].year) for s in segs))
        tot_s = sum(ysum[y] for y in ys)
        tot_c = sum(ycnt[y] for y in ys)
        with np.errstate(all='ignore'):
            for y in ys:
                res['y%d' % y] = ysum[y] / ycnt[y] * I.ANN
                res['loyo_ex%d' % y] = (tot_s - ysum[y]) / (tot_c - ycnt[y]) * I.ANN
        stats[scope] = res
        print('[%s] 合并统计 (%.0fs)' % (scope, time.time() - t0), flush=True)
    # 去 2015+16 与 去 2024+ (四段; 只点估 + NW, 段间不拼接)
    for scope, rule in (('all4_ex1516', lambda s, d: ~np.isin(d.year, [2015, 2016])),
                        ('all4_ex2024p', lambda s, d: np.full(len(d), s != '2024-2026'))):
        parts = []
        for s in SEGS4:
            keep = rule(s, data[s][3])
            X = np.where(keep[:, None], data[s][1]['dnet8'], np.nan)
            parts.append((X, None))
        mu, se, n = merged_mean_se(parts, Hs)
        res = pd.DataFrame({'descriptor_id': meta0.descriptor_id, 'n_days': n, 'd_net8_ann': mu * I.ANN,
                            'se_nwH': se * I.ANN})
        for k in ('dcore', 'dsamecap'):
            pk = [(np.where(rule(s, data[s][3])[:, None], data[s][1][k], np.nan), None) for s in SEGS4]
            mk, sk, _ = merged_mean_se(pk, Hs)
            res['%s_ann' % k], res['%s_se_nwH' % k] = mk * I.ANN, sk * I.ANN
        stats[scope] = res
    # ---------------- 家族 / 同时带 / Z-MEAN / δ / 状态词 ----------------
    meta = meta0.copy()
    try:
        cat = pd.read_csv(os.path.join(I.RES, 'registry', 'feature_semantics_v2.csv'))
        ax = dict(zip(cat.member_id, cat.axis_id))
        meta['axis'] = [ax.get(str(m_).split('|')[0].split('+')[0], '') for m_ in meta.member_id]
    except Exception:
        meta['axis'] = ''
    fams = {}
    for (rt, mo), g in meta.groupby(['route_id', 'mother_id']):
        fams[('domain', '%s|%s' % (rt, mo))] = g.index.values
    for axn, g in meta.groupby('axis'):
        if axn:
            fams[('axis', axn)] = g.index.values
    fams[('headline', 'all')] = meta.index.values
    fam_rows, zrows = [], []
    for scope in list(I.POST_SEGS) + ['post', 'all4']:
        res = stats[scope]
        mu = res.d_net8_ann.values / I.ANN
        for L in ST.BLOCKS:
            num, den = boot[(scope, L)]
            with np.errstate(all='ignore'):
                mstar = num / den
                sd = np.nanstd(mstar, axis=0, ddof=1)
                tabs = np.abs((mstar - mu[None, :]) / sd[None, :])
            valid = np.isfinite(sd) & (sd > 0) & np.isfinite(mu)
            for (lvl, name), cols in fams.items():
                cv = cols[valid[cols]]
                c = ST.family_crit(np.where(np.isfinite(tabs), tabs, 0.0), cv)
                fam_rows.append(dict(scope=scope, block=L, level=lvl, family=name, n_members=len(cols),
                                     n_valid=len(cv), n_zero_se=int((~valid[cols]).sum()), crit=c))
                if L == ST.BLOCKS[0]:
                    res.loc[cols, 'band_%s_lo' % lvl] = (mu[cols] - c * sd[cols]) * I.ANN
                    res.loc[cols, 'band_%s_hi' % lvl] = (mu[cols] + c * sd[cols]) * I.ANN
                    if len(cv):
                        cen = (mstar[:, cv] - mu[None, cv]) * I.ANN
                        nmed, nmax = np.nanmedian(cen, axis=1), np.nanmax(cen, axis=1)
                        obs_med, obs_max = float(np.median(mu[cv] * I.ANN)), float(np.max(mu[cv] * I.ANN))
                        zrows.append(dict(scope=scope, level=lvl, family=name, n=len(cv), obs_median=obs_med,
                                          null_median_q025=float(np.quantile(nmed, 0.025)),
                                          null_median_q975=float(np.quantile(nmed, 0.975)),
                                          tail_median_ge=float((1 + np.sum(nmed >= obs_med)) / (1 + len(nmed))),
                                          obs_max=obs_max, null_max_q95=float(np.quantile(nmax, 0.95)),
                                          tail_max_ge=float((1 + np.sum(nmax >= obs_max)) / (1 + len(nmax))),
                                          label='diagnostic_tail_fraction'))
    for scope, res in stats.items():
        se = res.se_nwH.values
        est = res.d_net8_ann.values
        lo, hi = est - 1.96 * se, est + 1.96 * se
        res['ci_lo_nwH'], res['ci_hi_nwH'] = lo, hi
        res['ci_excludes_zero'] = (lo > 0) | (hi < 0)
        res['discernible_scale'] = 1.96 * se
        res['mde80'] = (1.96 + 0.84) * se
        for d_ in ST.DELTAS:
            res['within_pm%.2f' % d_] = (lo >= -d_) & (hi <= d_)
        res['state_word'] = [ST.state_word(a_, b_, e_) for a_, b_, e_ in zip(lo, hi, est)]
    # 两后段同号: 观测 vs Z-MEAN 零分布
    s0, s1 = stats[I.POST_SEGS[0]], stats[I.POST_SEGS[1]]
    same = np.sign(s0.d_net8_ann.values) == np.sign(s1.d_net8_ann.values)
    L = ST.BLOCKS[0]
    c0, c1 = boot[(I.POST_SEGS[0], L)], boot[(I.POST_SEGS[1], L)]
    with np.errstate(all='ignore'):
        m0 = c0[0] / c0[1] - (s0.d_net8_ann.values / I.ANN)[None, :]
        m1_ = c1[0] / c1[1] - (s1.d_net8_ann.values / I.ANN)[None, :]
    for (lvl, name), cols in fams.items():
        obs = float(np.mean(same[cols]))
        nul = np.mean(np.sign(m0[:, cols]) == np.sign(m1_[:, cols]), axis=1)
        zrows.append(dict(scope='both_post_segments', level=lvl, family=name, n=len(cols), obs_same_sign=obs,
                          null_same_sign_q975=float(np.quantile(nul, 0.975)),
                          tail_same_sign_ge=float((1 + np.sum(nul >= obs)) / (1 + len(nul))),
                          label='diagnostic_tail_fraction'))
    keep = ['descriptor_id', 'route_id', 'mother_id', 'member_id', 'role', 'strength', 'policy', 'direction',
            'direction_role', 'H', 'representative', 'axis']
    for scope, res in stats.items():
        out = meta[[c for c in keep if c in meta.columns]].join(res.drop(columns=['descriptor_id']))
        if scope in I.POST_SEGS:
            cols = [c for c in ('net8_ann', 'parent_net8_ann', 'd_gross_ann', 'd_turn', 'd_pos', 'd_vs_core_matchN',
                                'd_vs_reverse_matchN', 'd_vs_parent_common', 'd_same_capital', 'attr_added_ann',
                                'attr_removed_ann', 'attr_common_ann', 'n_changed_cells', 'target_n_mean',
                                'parent_n_mean', 'core_matchN_restricted', 'companion')
                    if c in data[scope][0].columns]
            out = out.join(data[scope][0][cols])
        I.atomic_write_csv(os.path.join(od, 'descriptor_stats_%s.csv' % scope), out)
    I.atomic_write_csv(os.path.join(od, 'family_bands_post.csv'), pd.DataFrame(fam_rows))
    I.atomic_write_csv(os.path.join(od, 'zmean_family_post.csv'), pd.DataFrame(zrows))
    # ---------------- 四臂交互 (分段 / post / all4) ----------------
    fa = meta[meta.route_id == 'FOURARM'].copy()
    irows = []
    if len(fa):
        fa['arm'], fa['param'] = fa.direction_role.astype(str), fa.strength.astype(str)
        for (nm, mo, pv, H), g in fa.groupby(['policy', 'mother_id', 'param', 'H']):
            arms = dict(zip(g.arm, g.index))
            if not all(k in arms for k in ('A', 'B', 'AB')):
                continue
            for scope in list(I.POST_SEGS) + ['post', 'all4']:
                segs = MERGED.get(scope, [scope])
                parts = []
                for s in segs:
                    X_ = data[s][1]['dnet8']
                    parts.append((X_[:, [arms['AB']]] - X_[:, [arms['A']]] - X_[:, [arms['B']]], None))
                mu_, se_, _ = merged_mean_se(parts, np.array([int(H)]))
                rec = dict(fourarm=nm, mother=mo, param=pv, H=int(H), scope=scope,
                           interaction_ann=float(mu_[0]) * I.ANN, interaction_se_nwH=float(se_[0]) * I.ANN)
                for k in ('A', 'B', 'AB'):
                    mk, _, _ = merged_mean_se([(data[s][1]['dnet8'][:, [arms[k]]], None) for s in segs],
                                              np.array([int(H)]))
                    rec['d_%s_ann' % k] = float(mk[0]) * I.ANN
                irows.append(rec)
    I.atomic_write_csv(os.path.join(od, 'fourarm_interaction_post.csv'), pd.DataFrame(irows))
    I.write_receipt(os.path.join(I.RES, 'task_status', 'stats_post.receipt.json'), 'stats:post',
                    [os.path.join(od, f) for f in sorted(os.listdir(od))], n_descriptors=J, draws=a.draws,
                    blocks=list(ST.BLOCKS), first_look_written_at=fl['written_at'],
                    elapsed_s=round(time.time() - t0, 1))
    print('后段统计完成: 描述符 %d; 家族 %d; %.0fs' % (J, len(fams), time.time() - t0))


if __name__ == '__main__':
    main()
