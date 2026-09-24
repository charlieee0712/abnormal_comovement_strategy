#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 1 补充: 成本暴露表 (brief §4 "测量 / 边缘 / 事件 / 成本暴露表") 与 Q12 限价政策对照。

cost    每母体 x 集合 (final / edge / econ_reject / pool0): 摩擦成员原值 (比例价差等) 的形成日等权均值与中位;
        edge 相对 final 的差 —— 回答"决策边缘的名字是不是更贵" (只描述, 不当 alpha)。
policy  V 族同一估计量 OBS vs LIMIT_SENS vs LEGACY_PARK_NAN: pool0 覆盖、两版截面 Spearman、
        触板格占比, 以及按政策换版后 pool0 内排名变动的格占比 (Q12 的测量部分)。
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6i_s1base as SB
import e6h_run_routes as RR

FRICTION = ['K_ar20', 'K_edge20', 'K_cs20', 'K_csm20', 'K_rollsp20', 'K_zero20', 'K_amihud_LEGACY',
            'K_ar60', 'K_edge60']


def part_cost(S):
    rows = []
    sets_all = {mn: SB.sets_for_mother(S, RR.ParentCtx(S, mn)) for mn in I.MOTHERS}
    for mid in FRICTION:
        raw = SB.raw_member(S, mid)
        for mn, ss in sets_all.items():
            for sn in ('pool0', 'final', 'edge', 'econ_reject'):
                m = ss[sn] & np.isfinite(raw)
                with np.errstate(all='ignore'):
                    dm = np.where(m.sum(1) > 0, np.where(m, raw, 0).sum(1) / m.sum(1), np.nan)
                rows.append(dict(segment=S.name, member_id=mid, mother=mn, set=sn,
                                 day_mean_of_means=float(np.nanmean(dm)),
                                 cell_median=float(np.nanmedian(raw[m])) if m.any() else np.nan,
                                 n_cells=int(m.sum())))
    I.atomic_write_csv(os.path.join(I.RES, 'measurements', 'cost_exposure_%s.csv' % S.name),
                       pd.DataFrame(rows))


def part_policy(S):
    rows = []
    p0 = S.p0c
    d = S.data
    idx, cols = S.pool0.index, S.pool0.columns
    g = lambda k: d[k].reindex(index=idx, columns=cols).astype(float).values[:, S.ccols]
    Hh, L, lu, ld = g('high'), g('low'), g('limit_up'), g('limit_down')
    touch = np.isfinite(lu) & np.isfinite(ld) & ((Hh >= lu - 0.005) | (L <= ld + 0.005))
    t20 = pd.DataFrame(touch.astype(float)).rolling(20, min_periods=1).sum().values > 0
    for est in ('park', 'gk', 'rs', 'yz', 'mj'):
        for w in (10, 20):
            a = SB.raw_member(S, 'V_%s%d_obs' % (est, w))
            b = SB.raw_member(S, 'V_%s%d_ls' % (est, w))
            ra, rb = SB.row_rank(a, p0), SB.row_rank(b, p0)
            both = p0 & np.isfinite(a) & np.isfinite(b)
            sp = SB.row_spearman(ra, rb)
            moved = both & (np.abs(ra - rb) > 0.05)
            rows.append(dict(segment=S.name, estimator=est, window=w,
                             cov_obs=float(np.isfinite(a)[p0].mean()),
                             cov_ls=float(np.isfinite(b)[p0].mean()),
                             spearman_obs_vs_ls_daymean=float(np.nanmean(sp)),
                             frac_rank_move_gt5pct=float(moved.sum() / max(both.sum(), 1)),
                             frac_pool0_touch_in_window=float(t20[p0].mean())))
    a = SB.raw_member(S, 'V_park20_obs')
    c = SB.raw_member(S, 'V_park20_LEGACY')
    ra, rc = SB.row_rank(a, p0), SB.row_rank(c, p0)
    both = p0 & np.isfinite(a) & np.isfinite(c)
    rows.append(dict(segment=S.name, estimator='park_obs_vs_LEGACY_PARK_NAN', window=20,
                     cov_obs=float(np.isfinite(a)[p0].mean()), cov_ls=float(np.isfinite(c)[p0].mean()),
                     spearman_obs_vs_ls_daymean=float(np.nanmean(SB.row_spearman(ra, rc))),
                     frac_rank_move_gt5pct=float((both & (np.abs(ra - rc) > 0.05)).sum() /
                                                 max(both.sum(), 1)),
                     frac_pool0_touch_in_window=float(t20[p0].mean())))
    I.atomic_write_csv(os.path.join(I.RES, 'measurements', 'limit_policy_%s.csv' % S.name),
                       pd.DataFrame(rows))
    print(pd.DataFrame(rows).round(4).to_string(index=False))


def _wl(win, los, pct):
    with np.errstate(all='ignore'):
        nw, nl = win.sum(1), los.sum(1)
        dw = np.where(nw >= 3, np.where(win, pct, 0.0).sum(1) / nw, np.nan)
        dl = np.where(nl >= 3, np.where(los, pct, 0.0).sum(1) / nl, np.nan)
    return dw - dl


def part_t0ref(S):
    """Q18 对照集 (brief §12 "同人数反向对照" 的执行端实现, 报告里写明口径):
       同一"赢家 − 输家" pct 差 (形成日等权, 日期等权), 分别在
         final   母体最终保留集 (被【保留】的名单里赢家 − 输家)
         pool0   整个 pool0
         p0_sameN  pool0 内每日随机抽与 econ_reject 同人数的名单 (一次抽样, 种子固定)
       若 econ_reject 的画像 ≈ 这些对照集, 画像是池子层面的收益预测, 不是"被错剔"特有。"""
    FE.build_catalog()
    mems = [m['member_id'] for m in FE.CATALOG]
    I.guard_i(mems, segment=S.name, use='label', label_end=str(S.dates[-1].date()), where='stage1_t0ref')
    y = SB.labels(S)['src5']
    fy = np.isfinite(y)
    rng = np.random.default_rng(20260923 + 18)
    sets = {}
    p0 = S.p0c & fy
    sets[('pool0', 'pool0')] = p0
    for mn in I.MOTHERS:
        P = RR.ParentCtx(S, mn)
        D = P.D.astype(bool) & S.p0c & fy
        sets[(mn, 'econ_reject')] = D
        sets[(mn, 'final')] = P.B.astype(bool) & S.p0c & fy
        U = np.where(p0, rng.random(p0.shape), np.inf)
        nD = D.sum(1)
        rk = np.argsort(np.argsort(U, axis=1), axis=1)
        sets[(mn, 'p0_sameN')] = p0 & (rk < nD[:, None])
    rows = []
    for mid in mems:
        pct = SB.pct_member(S, mid, direction='hi')
        fp = np.isfinite(pct)
        for (mn, sn), sm in sets.items():
            diff = _wl(sm & (y > 0) & fp, sm & (y < 0) & fp, pct)
            rows.append(dict(segment=S.name, mother=mn, set=sn, member_id=mid,
                             pct_diff_winner_minus_loser=float(np.nanmean(diff)),
                             nw_t=SB.nw_t(diff, 5), n_days=int(np.isfinite(diff).sum()),
                             n_per_day=float(np.nanmean(np.where(sm.sum(1) > 0, sm.sum(1), np.nan)))))
    I.atomic_write_csv(os.path.join(I.RES, 'measurements', 't0_reference_sets_%s.csv' % S.name),
                       pd.DataFrame(rows))


def part_q3(S):
    """Q3 的 Stage 1 部分: 同一 V 定义在 pool0 内按 真实漂移 (当日 cr5 三分位) / 当日区间 (h-l 三分位) /
       近 5 日触板 (0 vs >=1) 分层, 报预测形状 (IC 与五分组 src5 均值) 与风险形状 (各组 src5 标准差、
       P(y<0)、p10)。V 成员全部 49 个 + 源 Parkinson 桥。"""
    FE.build_catalog()
    mems = [m['member_id'] for m in FE.CATALOG if m['axis_id'] == 'V']
    I.guard_i(mems, segment=S.name, use='label', label_end=str(S.dates[-1].date()), where='stage1_q3')
    y = SB.labels(S)['src5']
    p0 = S.p0c & np.isfinite(y)
    d = S.data
    idx, cols = S.pool0.index, S.pool0.columns
    g = lambda k: d[k].reindex(index=idx, columns=cols).astype(float).values[:, S.ccols]
    Hh, Lw, lu, ld = g('high'), g('low'), g('limit_up'), g('limit_down')
    touch = np.isfinite(lu) & np.isfinite(ld) & ((Hh >= lu - 0.005) | (Lw <= ld + 0.005))
    t5 = pd.DataFrame(touch.astype(float)).rolling(5, min_periods=1).sum().values
    cr5 = I.to_grid(S, S.feats['cum_return_5d'])
    with np.errstate(all='ignore'):
        rng_ = np.log(Hh / Lw)
    ck, rk = SB.row_rank(cr5, p0), SB.row_rank(rng_, p0)
    strata = {'all': p0,
              'drift_low': p0 & (ck <= 1 / 3), 'drift_mid': p0 & (ck > 1 / 3) & (ck <= 2 / 3),
              'drift_high': p0 & (ck > 2 / 3),
              'range_low': p0 & (rk <= 1 / 3), 'range_mid': p0 & (rk > 1 / 3) & (rk <= 2 / 3),
              'range_high': p0 & (rk > 2 / 3),
              'touch0': p0 & (t5 == 0), 'touch1p': p0 & (t5 >= 1)}
    rows = []
    for mid in mems:
        pct = SB.pct_member(S, mid, direction='hi')
        for sn, sm in strata.items():
            xr = SB.row_rank(pct, sm)
            yr = SB.row_rank(y, sm & np.isfinite(pct))
            ic = SB.row_spearman(xr, yr)
            gm = SB.group_means(xr, np.where(sm, y, np.nan), 5)
            rec = dict(segment=S.name, member_id=mid, stratum=sn, ic_mean=float(np.nanmean(ic)),
                       ic_nw_t=SB.nw_t(ic, 5), n_days=int(np.isfinite(ic).sum()),
                       n_per_day=float(np.nanmean(np.where((sm & np.isfinite(pct)).sum(1) > 0,
                                                           (sm & np.isfinite(pct)).sum(1), np.nan))))
            m = np.isfinite(xr) & sm
            gi = np.clip(np.ceil(np.where(m, xr, 0.0) * 5).astype(int), 1, 5)
            for k in range(1, 6):
                rec['g%d_mean' % k] = float(np.nanmean(gm[:, k - 1]))
                yy = y[m & (gi == k)]
                rec['g%d_sd' % k] = float(np.std(yy)) if len(yy) > 1 else np.nan
                rec['g%d_pneg' % k] = float(np.mean(yy < 0)) if len(yy) else np.nan
                rec['g%d_p10' % k] = float(np.percentile(yy, 10)) if len(yy) else np.nan
            rows.append(rec)
    I.atomic_write_csv(os.path.join(I.RES, 'measurements', 'q3_v_strata_%s.csv' % S.name), pd.DataFrame(rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--parts', default='policy,cost')
    a = ap.parse_args()
    assert a.segment in I.DERIV_SEGS
    FE.build_catalog()
    I.set_protected_members(FE.protected_ids())
    S = I.seg_i(a.segment, warm=False)
    t0 = time.time()
    parts = a.parts.split(',')
    if 'policy' in parts:
        part_policy(S)
    if 'cost' in parts:
        part_cost(S)
    if 't0ref' in parts:
        part_t0ref(S)
    if 'q3' in parts:
        part_q3(S)
    print('[%s] %s 完成 %.0fs' % (a.segment, a.parts, time.time() - t0))


if __name__ == '__main__':
    main()
