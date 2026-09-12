#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 域与选择: S0 固定代表 / S1 层级等权组合 / S2 局部收缩 (plan §5, brief §5)。

**组合必须合并【目标权重】后跑真实账户** (plan §5.4):
"家族净值中位数不是组合, 平均成员净收益也不等于组合净收益"。
所以这里对每个域成员重建 mask -> DEV -> 逐日目标权重, 按层级权重合并, 再过一次引擎。
换手必须合并后重算, 不能取成员平均。

域 (plan §5.1) = parent x route(need) x direction x role x budget。
  成员 = 同一问题的【测量表达与合理参数】; 【不含】反向 / 随机 / 有效域对照、
  精确别名、不同信息目标。

S1 层级 (plan §5.2): 先在【同一测量】的参数路径间等权, 再在【同一机制的不同测量】间
  等权; 精确别名只一票 (本轮实测真别名只有 CVR == intraday_cvr_1d, 不在这些域里)。
S2 (plan §5.2): a_j ∝ π_j exp(μ_j/τ), π0 = 1/2 给原父, 其余 1/2 按"测量 -> 非同义参数"
  两层均分; τ ∈ {0.5, 1, 2} 个年化百分点; log-sum-exp 稳定求值; 原父始终是合法候选;
  identity (α0/η0) 只计入父, 不重复占质量。
  μ 用【2010-2014】估, 冻结后应用 2015-2018 (plan §5.3)。

用法: python3 e6h_selection.py --fit 2010-2014 --apply 2015-2018
"""
from __future__ import annotations
import os
import sys
import json
import time
import argparse
import collections

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_rules as RU
import e6h_run_routes as RR
import e6h_expand as EX
import e6f_core as F
import e6e_core as K

RES = H.RES

# 每个路线的"测量"字段名 (用于 S1 的第一层分组)
MEAS_COL = {'M-T-tcv-vs-t60': 'new_key', 'M-C-position-window': 'new_key',
            'E-V-quiet-price': 'vol_key', 'E-V-surge-price': 'vol_key',
            'E-P-path-conditional-focal': 'state_key',
            'R-O-overnight-risk': 'risk_key', 'I-P-peer-up-laggard': 'w',
            'I-P-peer-down-risk': 'w', 'L-Q-margin-liquidity': 'liq_key'}
# 中心代表 —— 按【源清楚 / 支持范围】选, 事前写死, 不按收益选 (plan §5.2)
CENTER = {'M-T-tcv-vs-t60': 'TCV_20',
          'M-C-position-window': 'CVR_5d',
          'E-V-quiet-price': 'volume_ratio_3d',
          'E-V-surge-price': 'volume_ratio_3d',
          'E-P-path-conditional-focal': 'positive_day_ratio_5d',
          'R-O-overnight-risk': 'JUMP_20',
          'I-P-peer-up-laggard': 20, 'I-P-peer-down-risk': 20,
          'L-Q-margin-liquidity': 'amihud_daily'}


def domain_key(r):
    """基本域 = parent x route x direction x role x budget。"""
    dirn = r.get('want_source_high')
    if pd.isna(dirn):
        dirn = r.get('ip_dir', r.get('mode', '-'))
    bud = r.get('eta')
    if pd.isna(bud):
        bud = r.get('alpha', r.get('e', r.get('lam', r.get('k', '-'))))
    return '%s|%s|%s|%s|budget=%s' % (r['parent'], r['route_id'], r['role'], dirn, bud)


def merge_weights(ivs, ws):
    """按权重合并【逐日目标权重】。ivs = [(idx, val)], ws = 权重列表。
       不归一 —— 权重和为 1 时自然守恒; identity 不重复占质量由调用方保证。"""
    T = len(ivs[0][0])
    oi, ov = [], []
    for t in range(T):
        acc = {}
        for (idx, val), w in zip(ivs, ws):
            if w == 0:
                continue
            for c, v in zip(idx[t], val[t]):
                acc[c] = acc.get(c, 0.0) + v * w
        cs = np.fromiter(sorted(acc), int, len(acc))
        oi.append(cs)
        ov.append(np.fromiter((acc[c] for c in cs), float, len(cs)))
    return oi, ov


def hierarchical_weights(members, meas_col):
    """S1: 先在同一测量的参数路径间等权, 再在不同测量间等权。"""
    by_m = collections.defaultdict(list)
    for i, m in enumerate(members):
        by_m[str(m.get(meas_col))].append(i)
    nm = len(by_m)
    w = np.zeros(len(members))
    for _, idxs in by_m.items():
        for i in idxs:
            w[i] = 1.0 / (nm * len(idxs))
    return w


def s2_weights(mu, meas_of, pi0=0.5, tau=1.0):
    """S2: a_j ∝ π_j exp(μ_j/τ)。父占 π0; 其余 1/2 按"测量 -> 非同义参数"两层均分。
       返回 (父权重, 子权重数组)。log-sum-exp 稳定。"""
    by_m = collections.defaultdict(list)
    for i, m in enumerate(meas_of):
        by_m[str(m)].append(i)
    nm = max(1, len(by_m))
    pi = np.zeros(len(mu))
    for _, idxs in by_m.items():
        for i in idxs:
            pi[i] = (1.0 - pi0) / (nm * len(idxs))
    lg = np.concatenate([[np.log(pi0) + 0.0],            # 父: μ0 = 0
                         np.log(np.where(pi > 0, pi, 1e-300)) + np.asarray(mu) / tau])
    lg = lg - lg.max()
    a = np.exp(lg)
    a = a / a.sum()
    return float(a[0]), a[1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fit', default='2010-2014')
    ap.add_argument('--apply', default='2015-2018')
    ap.add_argument('--min-members', type=int, default=2)
    a = ap.parse_args()
    t0 = time.time()
    od = os.path.join(RES, 'domain_selection')
    os.makedirs(od, exist_ok=True)

    import glob
    sm = pd.concat([pd.read_csv(f) for f in
                    sorted(glob.glob(os.path.join(RES, 'route_results',
                                                  'summary_*.csv')))],
                   ignore_index=True)
    sm = sm[~sm.is_identity].copy()
    sm['domain'] = sm.apply(domain_key, axis=1)
    # 只保留两段都有的域, 且成员数够
    ok = (sm.groupby(['domain', 'descriptor_id']).size().reset_index()
          .groupby('domain').size())
    doms = [d for d in sm.domain.unique()
            if sm[(sm.domain == d) & (sm.segment == a.fit)].shape[0] >= a.min_members
            and sm[(sm.domain == d) & (sm.segment == a.apply)].shape[0] >= a.min_members]
    print('域 %d 个 (成员 >= %d 且两段都有)' % (len(doms), a.min_members), flush=True)

    desc = {r['descriptor_id']: r for r in EX.all_descriptors()}
    rows = []
    for seg in (a.fit, a.apply):
        S = H.seg(seg, verbose=False)
        pctx = {}
        for d in doms:
            sub = sm[(sm.domain == d) & (sm.segment == seg)]
            if not len(sub):
                continue
            pname = sub.iloc[0]['parent']
            rid = sub.iloc[0]['route_id']
            if pname not in pctx:
                pctx[pname] = RR.ParentCtx(S, pname)
            P = pctx[pname]
            members = [desc[x] for x in sub.descriptor_id if x in desc]
            if len(members) < a.min_members:
                continue
            ivs = []
            for m in members:
                mask, wmul, _ = RR.build_mask(P, m)
                idx, val = F.dev_from_dense(S, mask)
                if wmul is not None:
                    val = [v * wmul[t, idx[t]] if len(idx[t]) else v
                           for t, v in enumerate(val)]
                ivs.append((idx, val))
            mcol = MEAS_COL.get(rid, 'descriptor_id')
            # --- S0 中心代表 ---
            cen = CENTER.get(rid)
            ci = [i for i, m in enumerate(members) if str(m.get(mcol)) == str(cen)]
            if ci:
                pnl = F.sparse_pnl_H(S, ivs[ci[0]][0], ivs[ci[0]][1], K.HOLD, F.COST)
                rows.append(dict(domain=d, segment=seg, selector='S0_fixed',
                                 parent=pname, route_id=rid, n_members=len(members),
                                 net8_ann=H.ann(pnl[3]), gross_ann=H.ann(pnl[0]),
                                 turn_mean=float(np.nanmean(pnl[2])),
                                 d_vs_parent=H.ann(np.asarray(pnl[3])
                                                   - np.asarray(P.pnl[3])),
                                 note='中心测量=%s (按源清楚选, 非收益)' % cen))
            # --- S1 层级等权 ---
            w1 = hierarchical_weights(members, mcol)
            oi, ov = merge_weights(ivs, w1)
            pnl = F.sparse_pnl_H(S, oi, ov, K.HOLD, F.COST)
            rows.append(dict(domain=d, segment=seg, selector='S1_hier_equal',
                             parent=pname, route_id=rid, n_members=len(members),
                             n_measurements=len(set(str(m.get(mcol)) for m in members)),
                             net8_ann=H.ann(pnl[3]), gross_ann=H.ann(pnl[0]),
                             turn_mean=float(np.nanmean(pnl[2])),
                             d_vs_parent=H.ann(np.asarray(pnl[3])
                                               - np.asarray(P.pnl[3])),
                             note='合并目标权重后跑真实账户, 换手合并后重算'))
            # --- S2 局部收缩 (μ 只从 fit 段取, 冻结后应用 apply 段) ---
            fitsub = sm[(sm.domain == d) & (sm.segment == a.fit)]
            mu_map = dict(zip(fitsub.descriptor_id, fitsub.d_net8_ann))
            mu = np.array([mu_map.get(m['descriptor_id'], 0.0) for m in members])
            meas_of = [str(m.get(mcol)) for m in members]
            for tau in (0.5, 1.0, 2.0):
                w0, wj = s2_weights(mu, meas_of, 0.5, tau)
                pidx, pval = F.dev_from_dense(S, P.B)
                oi, ov = merge_weights([(pidx, pval)] + ivs,
                                       [w0] + list(wj))
                pnl = F.sparse_pnl_H(S, oi, ov, K.HOLD, F.COST)
                rows.append(dict(domain=d, segment=seg,
                                 selector='S2_shrink_tau%.1f' % tau,
                                 parent=pname, route_id=rid, n_members=len(members),
                                 net8_ann=H.ann(pnl[3]), gross_ann=H.ann(pnl[0]),
                                 turn_mean=float(np.nanmean(pnl[2])),
                                 d_vs_parent=H.ann(np.asarray(pnl[3])
                                                   - np.asarray(P.pnl[3])),
                                 parent_weight=round(w0, 4),
                                 mu_source=a.fit, tau=tau,
                                 note='μ 只从 %s 估, 冻结后同应用两段' % a.fit))
        print('  [%s] 完成, 累计 %d 行, %.0fs' % (seg, len(rows), time.time() - t0),
              flush=True)
        del pctx, S

    pd.DataFrame(rows).to_csv(os.path.join(od, 'domain_selection.csv'), index=False)
    print('写出 domain_selection.csv: %d 行, %.0fs' % (len(rows), time.time() - t0))


if __name__ == '__main__':
    main()
