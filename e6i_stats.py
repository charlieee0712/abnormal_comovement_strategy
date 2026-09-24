#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 推导段统计 (plan §8; brief §6 / §14)。只读 Stage 2 合并产物与 Z-MAP 产物, 不产生新账户。

主对象 = 逐日配对 child − mother 的 net8 (Stage 2 npz 的 dnet8); 机制对象 = sameN (dcore)、同资本 (dsamecap)。
  NW          主 lag = H, 另 lag = max(2H, 20) 与源 lag 5; 完整交易日网格上的有掩码估计 (缺测日不拼接)。
  bootstrap   2,000 次共同 stationary bootstrap (循环), 平均块长 20 (主) 与 60, 段内重采样;
              full = 两段按有效日合并, 每次 draw 重算分母 (两段各自一组 draw, 同一编号配对)。
  同步带      对固定家族 (need 域 = 路线 x 母体 / 轴 / 全 headline) 的有效且 SE>0 成员,
              t*_j = (mean*_j − mean_j)/SE_j, c = 95% 分位 of max_j |t*_j|; 零 SE 单列; 不用 nanmax 缩家族。
  Z-MEAN      同一组 draw 的中心化分布 = "全部已登记增量均值为零、依赖结构近似保留" 的条件情景:
              家族中位 / 最大 / 两段同号比例的零分布与观测值 (diagnostic_tail_fraction, 含原样本约定)。
  δ / MDE     δ ∈ {0.10, 0.25, 0.50, 1.00} 年化百分点的区间覆盖; 可分辨尺度 = 1.96·SE, MDE80 = (1.96+0.84)·SE。
  状态词      以 NW(lag H) 95% 区间与声明尺度 δ=0.25 定: materially_small_under_declared_delta (区间 ⊂ [−δ, δ]) /
              inconclusive (区间同时覆盖 −δ 与 +δ) / positive_estimate_uncertain / negative_estimate_uncertain;
              另列 ci_excludes_zero 作证据强度轴 —— 两条轴并列, 不合成 PASS/FAIL (plan §8.4)。
  时间        逐年年化均值与 LOYO (各段内与 full)。
输出 statistics/: descriptor_stats_<seg|full>.csv, family_bands.csv, zmean_family.csv, yearly_<seg>.csv。
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import glob
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I

B_DRAWS = 2000
BLOCKS = (20, 60)
DELTAS = (0.10, 0.25, 0.50, 1.00)
DECLARED_DELTA = 0.25
SEED = 20260923
SERIES = ('dnet8', 'dcore', 'dsamecap')


# ============================================================ 数据
def load_segment(seg):
    od = os.path.join(I.RES, 'accounts', seg)
    meta = pd.concat([pd.read_csv(f, low_memory=False) for f in sorted(glob.glob(os.path.join(od, 'merged_*.csv')))
                      if not f.endswith('merged_index.csv')], ignore_index=True)
    meta = meta[meta.status == 'SUCCEEDED'].reset_index(drop=True)
    idx = pd.read_csv(os.path.join(od, 'merged_index.csv'))
    pos = dict(zip(idx.descriptor_id, zip(idx.npz, idx.row)))
    missing = [d for d in meta.descriptor_id if d not in pos]
    if missing:
        print('  [%s] %d 个描述符无逐日序列索引 -> 不进统计 (例 %s)' % (seg, len(missing), missing[:3]))
        meta = meta[meta.descriptor_id.isin(pos)].reset_index(drop=True)
    J = len(meta)
    arrs = {k: None for k in SERIES}
    by_npz = {}
    for j, did in enumerate(meta.descriptor_id):
        f, r = pos[did]
        by_npz.setdefault(f, []).append((j, r))
    T = None
    for f, lst in by_npz.items():
        with np.load(os.path.join(od, f)) as z:
            if T is None:
                T = z['dnet8'].shape[1]
                for k in SERIES:
                    arrs[k] = np.full((T, J), np.nan)
            jj = np.array([a for a, _ in lst])
            rr = np.array([b for _, b in lst])
            for k in SERIES:
                if k in z.files:                      # M1 / M2 账户只有 dnet8 (无同人数 / 同资本对照序列)
                    arrs[k][:, jj] = z[k][rr].T
    return meta, arrs, T


def seg_dates(seg):
    S = I.seg_i(seg, warm=False)
    return pd.DatetimeIndex(S.dates)


# ============================================================ NW (有掩码, 完整日历)
def nw_se_masked(X, lag):
    """X (T, J) 含 NaN; 返回 (mean, se) 两个 (J,)。自协方差只在两端都有值的日对上累加, 分母 = 有效日数。"""
    m = np.isfinite(X)
    n = m.sum(0).astype(float)
    with np.errstate(all='ignore'):
        mu = np.where(m, X, 0.0).sum(0) / n
        e = np.where(m, X - mu, 0.0)
        s = (e * e).sum(0) / n
        for L in range(1, lag + 1):
            if L >= X.shape[0]:
                break
            g = (e[L:] * e[:-L]).sum(0) / n
            s = s + 2.0 * (1.0 - L / (lag + 1.0)) * g
        se = np.sqrt(np.maximum(s, 0.0) / n)
    return mu, se, n


# ============================================================ stationary bootstrap
def sb_weights(T, B, L, seed):
    """B 条循环 stationary bootstrap 序列的日期重数 (B, T)。"""
    rng = np.random.default_rng(seed)
    W = np.zeros((B, T))
    p = 1.0 / L
    for b in range(B):
        idx = np.empty(T, np.int64)
        cur = rng.integers(T)
        jumps = rng.random(T) < p
        starts = rng.integers(T, size=T)
        for t in range(T):
            if t == 0 or jumps[t]:
                cur = starts[t]
            else:
                cur = (cur + 1) % T
            idx[t] = cur
        W[b] = np.bincount(idx, minlength=T)
    return W


def boot_means(X, W, chunk=4000):
    """(B, J) 重采样均值 (按有效日重算分母)。"""
    m = np.isfinite(X)
    X0 = np.where(m, X, 0.0)
    M = m.astype(float)
    B, J = W.shape[0], X.shape[1]
    out_num = np.empty((B, J))
    out_den = np.empty((B, J))
    for a in range(0, J, chunk):
        out_num[:, a:a + chunk] = W @ X0[:, a:a + chunk]
        out_den[:, a:a + chunk] = W @ M[:, a:a + chunk]
    return out_num, out_den


def family_crit(tstar_abs, cols):
    """家族 max|t*| 的 95% 分位; cols = 家族内有效成员的列下标。"""
    if len(cols) == 0:
        return np.nan
    return float(np.quantile(tstar_abs[:, cols].max(1), 0.95))


def state_word(lo, hi, est, delta=DECLARED_DELTA):
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return 'inconclusive'
    if lo >= -delta and hi <= delta:
        return 'materially_small_under_declared_delta'
    if lo < -delta and hi > delta:
        return 'inconclusive'
    return 'positive_estimate_uncertain' if est > 0 else 'negative_estimate_uncertain'


# ============================================================ 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--draws', type=int, default=B_DRAWS)
    a = ap.parse_args()
    t0 = time.time()
    od = os.path.join(I.RES, 'statistics')
    os.makedirs(od, exist_ok=True)
    segs = list(I.DERIV_SEGS)
    data = {}
    for seg in segs:
        meta, arrs, T = load_segment(seg)
        dates = seg_dates(seg)
        assert len(dates) == T, (seg, len(dates), T)
        data[seg] = (meta, arrs, T, dates)
        print('[%s] 描述符 %d x 日 %d  (%.0fs)' % (seg, len(meta), T, time.time() - t0), flush=True)
    # 共同描述符集合 (两段都有)
    common = sorted(set(data[segs[0]][0].descriptor_id) & set(data[segs[1]][0].descriptor_id))
    fam_rows, zrows = [], []
    stats_by_seg = {}
    boot = {}
    for seg in segs:
        meta, arrs, T, dates = data[seg]
        order = meta.set_index('descriptor_id').index.get_indexer(common)
        meta = meta.iloc[order].reset_index(drop=True)
        arrs = {k: v[:, order] for k, v in arrs.items()}
        data[seg] = (meta, arrs, T, dates)
        Hs = meta.H.astype(int).values
        X = arrs['dnet8']
        res = pd.DataFrame({'descriptor_id': meta.descriptor_id})
        mu, _, n = nw_se_masked(X, 1)
        res['n_days'] = n
        res['d_net8_ann'] = mu * I.ANN
        for tag, lagf in (('nwH', lambda h: h), ('nw2H20', lambda h: max(2 * h, 20)), ('nw5', lambda h: 5)):
            se = np.full(len(meta), np.nan)
            for h in np.unique(Hs):
                cols = np.flatnonzero(Hs == h)
                _, s_, _ = nw_se_masked(X[:, cols], lagf(int(h)))
                se[cols] = s_
            res['se_%s' % tag] = se * I.ANN
        for k in ('dcore', 'dsamecap'):
            m_, _, _ = nw_se_masked(arrs[k], 1)
            se = np.full(len(meta), np.nan)
            for h in np.unique(Hs):
                cols = np.flatnonzero(Hs == h)
                _, s_, _ = nw_se_masked(arrs[k][:, cols], int(h))
                se[cols] = s_
            res['%s_ann' % k] = m_ * I.ANN
            res['%s_se_nwH' % k] = se * I.ANN
        # 逐年与 LOYO
        yrs = dates.year.values
        ys = sorted(set(yrs))
        m = np.isfinite(X)
        for y in ys:
            sel = yrs == y
            with np.errstate(all='ignore'):
                res['y%d' % y] = np.where(m[sel], X[sel], 0).sum(0) / m[sel].sum(0) * I.ANN
                res['loyo_ex%d' % y] = np.where(m[~sel], X[~sel], 0).sum(0) / m[~sel].sum(0) * I.ANN
        # bootstrap
        for L in BLOCKS:
            W = sb_weights(T, a.draws, L, SEED + 1000 * L + (1 if seg == segs[0] else 2))
            num, den = boot_means(X, W)
            with np.errstate(all='ignore'):
                mstar = num / den
            boot[(seg, L)] = (num, den)
            sd = np.nanstd(mstar, axis=0, ddof=1)
            res['se_boot%d' % L] = sd * I.ANN
        stats_by_seg[seg] = res
        print('[%s] NW / 逐年 / bootstrap 完成 (%.0fs)' % (seg, time.time() - t0), flush=True)
    # full (两段按有效日合并)
    meta0 = data[segs[0]][0]
    full = pd.DataFrame({'descriptor_id': meta0.descriptor_id})
    X1, X2 = data[segs[0]][1]['dnet8'], data[segs[1]][1]['dnet8']
    Xf = np.vstack([X1, X2])
    Hs = meta0.H.astype(int).values
    mu, _, n = nw_se_masked(Xf, 1)
    full['n_days'] = n
    full['d_net8_ann'] = mu * I.ANN
    se = np.full(len(meta0), np.nan)
    for h in np.unique(Hs):
        cols = np.flatnonzero(Hs == h)
        # 段间不相邻: 分段 NW 方差按有效日加权合并 (段边界不拼接)
        m1, s1, n1 = nw_se_masked(X1[:, cols], int(h))
        m2, s2, n2 = nw_se_masked(X2[:, cols], int(h))
        with np.errstate(all='ignore'):
            v = ((n1 * s1) ** 2 + (n2 * s2) ** 2) / (n1 + n2) ** 2
        se[cols] = np.sqrt(v)
    full['se_nwH'] = se * I.ANN
    for L in BLOCKS:
        n1_, d1_ = boot[(segs[0], L)]
        n2_, d2_ = boot[(segs[1], L)]
        with np.errstate(all='ignore'):
            mstar = (n1_ + n2_) / (d1_ + d2_)
        full['se_boot%d' % L] = np.nanstd(mstar, axis=0, ddof=1) * I.ANN
        boot[('full', L)] = (n1_ + n2_, d1_ + d2_)
    stats_by_seg['full'] = full
    # ---------------- 家族 / 同步带 / Z-MEAN ----------------
    meta = meta0.copy()
    meta['axis'] = meta.descriptor_id.map(lambda s: '')
    try:
        cat = pd.read_csv(os.path.join(I.RES, 'registry', 'feature_semantics_v2.csv'))
        ax = dict(zip(cat.member_id, cat.axis_id))
        meta['axis'] = [ax.get(str(m).split('|')[0].split('+')[0], '') for m in meta.member_id]
    except Exception:
        pass
    fams = {}
    for (rt, mo), g in meta.groupby(['route_id', 'mother_id']):
        fams[('domain', '%s|%s' % (rt, mo))] = g.index.values
    for axn, g in meta.groupby('axis'):
        if axn:
            fams[('axis', axn)] = g.index.values
    fams[('headline', 'all')] = meta.index.values
    for scope in (segs[0], segs[1], 'full'):
        res = stats_by_seg[scope]
        mu = res.d_net8_ann.values / I.ANN
        for L in BLOCKS:
            num, den = boot[(scope, L)]
            with np.errstate(all='ignore'):
                mstar = num / den
                sd = np.nanstd(mstar, axis=0, ddof=1)
                tabs = np.abs((mstar - mu[None, :]) / sd[None, :])
            valid = np.isfinite(sd) & (sd > 0) & np.isfinite(mu)
            for (lvl, name), cols in fams.items():
                cv = cols[valid[cols]]
                c = family_crit(np.where(np.isfinite(tabs), tabs, 0.0), cv)
                fam_rows.append(dict(scope=scope, block=L, level=lvl, family=name, n_members=len(cols),
                                     n_valid=len(cv), n_zero_se=int((~valid[cols]).sum()), crit=c))
                if L == BLOCKS[0]:
                    col = 'band_%s' % lvl
                    lo = (mu[cols] - c * sd[cols]) * I.ANN
                    hi = (mu[cols] + c * sd[cols]) * I.ANN
                    res.loc[cols, col + '_lo'] = lo
                    res.loc[cols, col + '_hi'] = hi
                    # Z-MEAN: 家族中位 / 最大 的零分布 (中心化 draw)
                    cen = (mstar[:, cv] - mu[None, cv]) * I.ANN
                    obs_med = float(np.median(mu[cv] * I.ANN)) if len(cv) else np.nan
                    obs_max = float(np.max(mu[cv] * I.ANN)) if len(cv) else np.nan
                    if len(cv):
                        nmed = np.nanmedian(cen, axis=1)
                        nmax = np.nanmax(cen, axis=1)
                        zrows.append(dict(scope=scope, level=lvl, family=name, n=len(cv), obs_median=obs_med,
                                          null_median_q025=float(np.quantile(nmed, 0.025)),
                                          null_median_q975=float(np.quantile(nmed, 0.975)),
                                          tail_median_ge=float((1 + np.sum(nmed >= obs_med)) / (1 + len(nmed))),
                                          obs_max=obs_max, null_max_q95=float(np.quantile(nmax, 0.95)),
                                          tail_max_ge=float((1 + np.sum(nmax >= obs_max)) / (1 + len(nmax))),
                                          label='diagnostic_tail_fraction'))
        # δ / MDE / 状态词
        se = res.se_nwH.values
        est = res.d_net8_ann.values
        lo, hi = est - 1.96 * se, est + 1.96 * se
        res['ci_lo_nwH'], res['ci_hi_nwH'] = lo, hi
        res['ci_excludes_zero'] = (lo > 0) | (hi < 0)
        res['discernible_scale'] = 1.96 * se
        res['mde80'] = (1.96 + 0.84) * se
        for d in DELTAS:
            res['within_pm%.2f' % d] = (lo >= -d) & (hi <= d)
        res['state_word'] = [state_word(a_, b_, e_) for a_, b_, e_ in zip(lo, hi, est)]
    # 两段同号: 观测 vs Z-MEAN 零分布 (每个家族)
    s0, s1 = stats_by_seg[segs[0]], stats_by_seg[segs[1]]
    same = np.sign(s0.d_net8_ann.values) == np.sign(s1.d_net8_ann.values)
    L = BLOCKS[0]
    c0 = boot[(segs[0], L)]
    c1 = boot[(segs[1], L)]
    with np.errstate(all='ignore'):
        m0 = c0[0] / c0[1] - (s0.d_net8_ann.values / I.ANN)[None, :]
        m1_ = c1[0] / c1[1] - (s1.d_net8_ann.values / I.ANN)[None, :]
    for (lvl, name), cols in fams.items():
        obs = float(np.mean(same[cols]))
        nul = np.mean(np.sign(m0[:, cols]) == np.sign(m1_[:, cols]), axis=1)
        zrows.append(dict(scope='both_segments', level=lvl, family=name, n=len(cols), obs_same_sign=obs,
                          null_same_sign_q975=float(np.quantile(nul, 0.975)),
                          tail_same_sign_ge=float((1 + np.sum(nul >= obs)) / (1 + len(nul))),
                          label='diagnostic_tail_fraction'))
    # 写出
    keep = ['descriptor_id', 'route_id', 'mother_id', 'member_id', 'role', 'strength', 'policy', 'direction',
            'direction_role', 'H', 'representative', 'axis']
    for scope, res in stats_by_seg.items():
        out = meta[keep].join(res.drop(columns=['descriptor_id']))
        if scope in segs:
            m_ = data[scope][0][['net8_ann', 'parent_net8_ann', 'd_gross_ann', 'd_turn', 'd_pos', 'd_vs_core_matchN',
                                 'd_vs_reverse_matchN', 'd_vs_parent_common', 'd_same_capital', 'attr_added_ann',
                                 'attr_removed_ann', 'attr_common_ann', 'n_changed_cells', 'target_n_mean',
                                 'parent_n_mean', 'core_matchN_restricted']]
            out = out.join(m_)
        I.atomic_write_csv(os.path.join(od, 'descriptor_stats_%s.csv' % scope), out)
    I.atomic_write_csv(os.path.join(od, 'family_bands.csv'), pd.DataFrame(fam_rows))
    I.atomic_write_csv(os.path.join(od, 'zmean_family.csv'), pd.DataFrame(zrows))
    # ---------------- 四臂交互 (plan §5.6; Q15): 逐日配对 Δ_AB − Δ_A − Δ_B ----------------
    fa = meta[meta.route_id == 'FOURARM'].copy()
    if len(fa):
        fa['arm'] = fa.direction_role.astype(str)
        fa['param'] = fa.strength.astype(str)
        irows = []
        for (nm, mo, pv, H), g in fa.groupby(['policy', 'mother_id', 'param', 'H']):
            arms = dict(zip(g.arm, g.index))
            if not all(k in arms for k in ('A', 'B', 'AB')):
                continue
            for scope in segs + ['full']:
                if scope == 'full':
                    Xs = [np.concatenate([data[segs[0]][1]['dnet8'][:, arms[k]], data[segs[1]][1]['dnet8'][:, arms[k]]])
                          for k in ('A', 'B', 'AB')]
                else:
                    Xs = [data[scope][1]['dnet8'][:, arms[k]] for k in ('A', 'B', 'AB')]
                inter = Xs[2] - Xs[0] - Xs[1]
                if scope == 'full':
                    n0 = data[segs[0]][2]
                    m1, s1, c1 = nw_se_masked(inter[:n0, None], int(H))
                    m2, s2, c2 = nw_se_masked(inter[n0:, None], int(H))
                    with np.errstate(all='ignore'):
                        mu_ = (c1 * m1 + c2 * m2) / (c1 + c2)
                        se_ = np.sqrt(((c1 * s1) ** 2 + (c2 * s2) ** 2) / (c1 + c2) ** 2)
                else:
                    mu_, se_, _ = nw_se_masked(inter[:, None], int(H))
                rec = dict(fourarm=nm, mother=mo, param=pv, H=int(H), scope=scope,
                           interaction_ann=float(mu_[0]) * I.ANN, interaction_se_nwH=float(se_[0]) * I.ANN)
                for k in ('A', 'B', 'AB'):
                    rec['d_%s_ann' % k] = float(np.nanmean(Xs[('A', 'B', 'AB').index(k)])) * I.ANN
                irows.append(rec)
        I.atomic_write_csv(os.path.join(od, 'fourarm_interaction.csv'), pd.DataFrame(irows))
    I.write_receipt(os.path.join(I.RES, 'task_status', 'stats_main.receipt.json'), 'stats:main',
                    [os.path.join(od, f) for f in os.listdir(od)], n_descriptors=len(meta), draws=a.draws,
                    blocks=list(BLOCKS), elapsed_s=round(time.time() - t0, 1))
    print('统计完成: 描述符 %d; 家族 %d; %.0fs' % (len(meta), len(fams), time.time() - t0))


if __name__ == '__main__':
    main()
