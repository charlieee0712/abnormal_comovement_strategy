# -*- coding: utf-8 -*-
"""E6k 衰减场景（plan §10.5；E6K-Q16）：只用 E6j 已暴露的日账本做回顾性条件场景，不产生新策略账户、不调本轮候选。
  1 复现 E6j 638 个 B 主配置对象（α .25 × H5）的原 flag：deriv_pos = D_FULL_deriv > 0、post_pos = D_FULL_post > 0（两段 n 加权合并，W06）
  2 误差：四段内分层 stationary 时间块（L 20 主 / 60 敏感，各 2,000 次，所有对象共享索引）→ e*_D = D*_deriv − D̂_deriv、e*_P = D*_post − D̂_post（联合）
  3 场景：θ ∈ {0, .25·D̂_deriv, .5·D̂_deriv, 1·D̂_deriv, 经验收缩（族 = E6j block × 母体；J ≥ 3 用矩估计 τ²，J < 3 不做）}
          × 均值漂移 ∈ {−.25, 0, +.25} × 波动来源 ∈ {全四段（回顾性）, 只推导段（前瞻：后段误差用推导段误差的同一抽样结构重缩放）}；
     每个 draw 重做选择事件（推导正）与后段 flag，报告"推导正中后段非正"的比例分布（均值 / q05 / q95）与原观测值的位置
  4 只写"与哪些场景相容 / 不相容"（观测值落在 [q05, q95] 内外），不输出选择效应 / 噪声 / 市场变化的因果份额（plan §10.5 禁止结论）"""
import e6k_boot  # noqa: F401
import os
import sys

import numpy as np
import pandas as pd

import e6k_core as K
import e6j_stats as ST

NB = 2000
SEGS = K.SEGMENTS


def main():
    E = K.E6J_RES
    T0 = pd.read_csv(os.path.join(E, 'results_B', 'part2_main_config_all_objects.csv'))
    rows = []
    d_by = {s: [] for s in SEGS}
    for s in SEGS:
        par = K.npz(os.path.join(E, 'accounts', 'B', s, 'parents.npz'))
        pk = [str(x) for x in par['keys']]
        cache = {}
        for r in T0.itertuples():
            f = os.path.join(E, 'accounts', 'B', s, '%s__%s.npz' % (r.mother, r.block))
            if f not in cache:
                z = K.npz(f)
                cache[f] = (z, {str(x): i for i, x in enumerate(z['desc'])})
            z, ix = cache[f]
            c = z['net8'][ix[r.descriptor_id]]
            p = par['net8'][pk.index('%s|H5' % r.mother)]
            d_by[s].append(np.where(np.isfinite(c) & np.isfinite(p), c - p, np.nan))
    Dm = {s: np.vstack(d_by[s]) for s in SEGS}                          # (对象, 日)
    obs = {}
    for s in SEGS:
        m = np.isfinite(Dm[s])
        obs['D_%s' % s] = np.where(m.any(1), np.nansum(Dm[s], 1) / np.maximum(m.sum(1), 1) * ST.ANN, np.nan)
        obs['n_%s' % s] = m.sum(1)
    Dd = (obs['D_2010-2014'] * obs['n_2010-2014'] + obs['D_2015-2018'] * obs['n_2015-2018']) / (obs['n_2010-2014'] + obs['n_2015-2018'])
    Dp = (obs['D_2019-2023'] * obs['n_2019-2023'] + obs['D_2024-2026'] * obs['n_2024-2026']) / (obs['n_2019-2023'] + obs['n_2024-2026'])
    rep_d = np.allclose(Dd, T0.D_FULL_deriv.values, atol=1e-9, equal_nan=True)
    rep_p = np.allclose(Dp, T0.D_FULL_post.values, atol=1e-9, equal_nan=True)
    sel = Dd > 0
    flip_obs = float(np.mean(~(Dp[sel] > 0)))
    rows.append(dict(kind='reproduction', note='E6j 原 flag 复现（两段 n 加权合并）', objects=len(T0), deriv_pos=int(sel.sum()),
                     post_nonpos_among_deriv_pos=int((~(Dp[sel] > 0)).sum()), flip_share=flip_obs, reproduced_deriv=bool(rep_d), reproduced_post=bool(rep_p)))
    fam = (T0.block + '|' + T0.mother).values
    for L in (20, 60):
        draws_d = np.zeros((NB, len(T0)))
        draws_p = np.zeros((NB, len(T0)))
        num = {}
        for s in SEGS:
            rng = K.rng_for('E6k', 'decay', int(L), s)
            X = Dm[s]
            V = np.isfinite(X)
            X0 = np.where(V, X, 0.0)
            C = np.zeros((NB, X.shape[1]))
            for b in range(NB):
                C[b] = np.bincount(ST.stationary_indices(X.shape[1], L, rng), minlength=X.shape[1])
            num[s] = (C @ X0.T, C @ V.T.astype(float))
        for grp, segs_, out in (('deriv', K.DERIV_SEGS, draws_d), ('post', K.POST_SEGS, draws_p)):
            nn = sum(num[s][0] for s in segs_)
            dd = sum(num[s][1] for s in segs_)
            out[:] = np.where(dd > 0, nn / np.where(dd > 0, dd, 1) * ST.ANN, np.nan)
        eD = draws_d - Dd[None, :]
        eP = draws_p - Dp[None, :]
        # 经验收缩（族内；推导段误差协方差）
        th_shr = np.full(len(T0), np.nan)
        for g in np.unique(fam):
            ix = np.flatnonzero(fam == g)
            if len(ix) < 3:
                continue
            d = Dd[ix]
            Sig = np.cov(eD[:, ix], rowvar=False)
            J = len(ix)
            m = d.mean()
            Mx = np.eye(J) - np.ones((J, J)) / J
            tau2 = max(0.0, float(((d - m) ** 2).sum() / (J - 1) - np.trace(Mx @ Sig) / (J - 1)))
            den = tau2 + np.diag(Sig)
            th_shr[ix] = np.where(den > 0, m + tau2 / den * (d - m), m)
        thetas = {'theta0': np.zeros(len(T0)), 'theta25': .25 * Dd, 'theta50': .5 * Dd, 'theta100': Dd, 'theta_shrink': th_shr}
        # v2（2026-09-29 修正）：前瞻版的后段误差取推导段误差的另一个独立 draw（同一抽样结构、按后段离散重缩放）；
        # v1 用同一 draw 的 eD 重缩放，选择事件与后段结果完全同号 → θ0 翻号率恒 0（退化），v1 文件保留不删
        perm = np.roll(np.arange(NB), NB // 2)
        for vol in ('all4_retrospective', 'deriv_only_prospective'):
            eP_use = eP if vol == 'all4_retrospective' else eD[perm] * (np.nanstd(eP, 0) / np.where(np.nanstd(eD, 0) > 0, np.nanstd(eD, 0), 1))[None, :]
            for tn, th in thetas.items():
                okt = np.isfinite(th)
                for shift in (-0.25, 0.0, 0.25):
                    sd = th[None, :] + eD
                    sp = th[None, :] + shift + eP_use
                    fl = []
                    for b in range(NB):
                        s_ = (sd[b] > 0) & okt
                        if s_.sum():
                            fl.append(float(np.mean(~(sp[b][s_] > 0))))
                    fl = np.array(fl)
                    q05, q95 = (float(np.percentile(fl, 5)), float(np.percentile(fl, 95))) if len(fl) else (np.nan, np.nan)
                    rows.append(dict(kind='scenario', L=L, volatility=vol, theta=tn, shift=shift, flip_mean=float(fl.mean()) if len(fl) else np.nan,
                                     flip_q05=q05, flip_q95=q95, observed_flip=flip_obs, objects_in_theta=int(okt.sum()),
                                     compatible=bool(q05 <= flip_obs <= q95) if len(fl) else None))
    od = K.P('diagnostics', 'decay')
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, 'decay_scenarios_v2.csv')                      # v2：前瞻版独立 draw（v1 decay_scenarios.csv 保留）
    K.atomic_write_csv(p, pd.DataFrame(rows))
    K.write_receipt('decay_scenarios_v2', [p], 'SUCCEEDED', objects=len(T0), reproduced=bool(rep_d and rep_p), note='前瞻版改为独立 draw；v1 保留')
    print('衰减场景：%d 行；原 flag 复现 %s' % (len(rows), rep_d and rep_p), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
