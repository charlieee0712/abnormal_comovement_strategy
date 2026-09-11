#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T0-35 的输家画像 x H1 的换腿/第四腿结果: 覆盖矩阵预分层 (brief §5)。

把每个 J 键按"在输家画像上与全池的 pct 偏移"分层 (缺口 / 冗余 / 无关),
再看该键作第四腿或换腿时的实际 Δ。**只作读表结构, 不是准入门**;
T0-35 只改变 H1 的解释分层, 不改变执行 (brief §4)。
"""
import os, sys, glob
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6g_core as G
import e6e_core as K

T0 = os.path.join(G.RES, 'T0_35')
OUT = os.path.join(G.RES, 'D')
os.makedirs(OUT, exist_ok=True)
CORE_KEYS = {K.FK, K.FT, K.FC}
VETO_KEYS = {K.FCVR1, K.FCR5}


def portrait():
    fr = []
    for seg in G.DERIV_SEGS:
        p = os.path.join(T0, 'T0_profiles_U35_%s.csv' % seg)
        if not os.path.exists(p):
            continue
        d = pd.read_csv(p)
        ks = [c for c in d.columns if c.startswith('pct_')]
        lo = d[d.group == 'loser_q20'].iloc[0]
        wi = d[d.group == 'winner_q20'].iloc[0]
        al = d[d.group == 'pool_all'].iloc[0]
        for k in ks:
            fr.append(dict(segment=seg, key=k[4:],
                           loser_offset=lo[k] - al[k], winner_offset=wi[k] - al[k],
                           lw_gap=lo[k] - wi[k]))
    P = pd.DataFrame(fr)
    if not len(P):
        return None
    W = P.pivot_table(index='key', values=['loser_offset', 'winner_offset', 'lw_gap'],
                      columns='segment')
    W.columns = ['%s_%s' % (a, b.split('-')[0]) for a, b in W.columns]
    W['loser_same_sign'] = (np.sign(W['loser_offset_2010'])
                            == np.sign(W['loser_offset_2015']))
    W['loser_abs_min'] = W[['loser_offset_2010', 'loser_offset_2015']].abs().min(axis=1)
    W['lw_abs_min'] = W[['lw_gap_2010', 'lw_gap_2015']].abs().min(axis=1)
    return W.reset_index()


def main():
    W = portrait()
    if W is None:
        print('T0 画像还没落地'); return
    # 分层: 两段同号且共同幅度进前 1/3 = 强分离; 同号但幅度小 = 弱; 不同号 = 无关
    q = W.loser_abs_min.quantile([1 / 3, 2 / 3]).values
    def lay(r):
        if not r.loser_same_sign:
            return 'unrelated_sign_flip'
        return ('strong_separation' if r.loser_abs_min >= q[1]
                else ('weak_separation' if r.loser_abs_min >= q[0] else 'flat'))
    W['t0_layer'] = W.apply(lay, axis=1)
    W['already_in_core'] = W.key.isin(CORE_KEYS)
    W['already_in_veto'] = W.key.isin(VETO_KEYS)

    # H1 结果
    fr = []
    for fp in sorted(glob.glob(os.path.join(G.RES, 'H1', 'summary_H1_*.csv'))):
        fr.append(pd.read_csv(fp))
    if not fr:
        print('H1 还没落地'); W.to_csv(os.path.join(OUT, 't0_layers.csv'), index=False); return
    H = pd.concat(fr, ignore_index=True)
    H = H[H.role == 'economic']
    PA = os.path.join(OUT, 'paired_vs_refs.csv')
    if os.path.exists(PA):
        PR = pd.read_csv(PA)
        PR = PR[PR.ref == 'R2'][['config_id', 'segment', 'delta_net8_ann', 'sim_lo', 'sim_hi']]
        H = H.merge(PR, on=['config_id', 'segment'], how='left')

    agg = {'net8_ann': ['median', 'max', 'count']}
    if 'delta_net8_ann' in H.columns:
        agg['delta_net8_ann'] = ['median', 'max']
    Hs = H.groupby(['J', 'mode']).agg(agg)
    Hs.columns = ['_'.join(c) for c in Hs.columns]
    Hs = Hs.reset_index().rename(columns={'J': 'key'})
    M = Hs.merge(W[['key', 't0_layer', 'loser_abs_min', 'loser_same_sign',
                    'loser_offset_2010', 'loser_offset_2015', 'already_in_core']],
                 on='key', how='left')
    M.to_csv(os.path.join(OUT, 't0_layer_x_H1.csv'), index=False)
    W.to_csv(os.path.join(OUT, 't0_layers.csv'), index=False)

    print('== T0 分层 x H1 模式: net8 中位 (全段合并) ==')
    print(M.pivot_table(index='t0_layer', columns='mode', values='net8_ann_median',
                        aggfunc='median').round(3).to_string())
    print()
    if 'delta_net8_ann_median' in M.columns:
        print('== 同一分层的 Δ vs R2 中位 ==')
        print(M.pivot_table(index='t0_layer', columns='mode',
                            values='delta_net8_ann_median', aggfunc='median').round(3).to_string())
        print()
        print('== 各分层里 Δ vs R2 的最大值 ==')
        print(M.pivot_table(index='t0_layer', columns='mode',
                            values='delta_net8_ann_max', aggfunc='max').round(3).to_string())
    print()
    print('== 输家画像分离最强的 8 个键, 作第四腿 (add4) 的表现 ==')
    top = M[(M['mode'] == 'add4')].nlargest(8, 'loser_abs_min')
    cols = ['key', 't0_layer', 'loser_offset_2010', 'loser_offset_2015', 'net8_ann_median']
    if 'delta_net8_ann_median' in M.columns:
        cols += ['delta_net8_ann_median', 'delta_net8_ann_max']
    print(top[cols].round(4).to_string(index=False))


if __name__ == '__main__':
    main()
