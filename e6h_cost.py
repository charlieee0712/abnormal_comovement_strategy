#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 成本、规模与求根 (brief §8 末两条, plan §8.3)。答 Q9 的成本一半。

情景: A ∈ {1,5,10,20} 亿 x κ ∈ {0.25,0.5,1,2} + 无冲击; 8bp 主口径 + 12bp 另一情景。
冲击括号沿 E6g 契约:
  sqrt: c = κ·√A·bracket_sqrt      (A 单位: 元)
  lin : c = (κ·A/√p0)·bracket_lin  (p0 = 1%)
年化 = 逐日均值 × 252 × 100。

求根 (plan §8.3):
  容量 A*  : net8 − κ·√A·C·252·100 = 0 → A* = (net8/(κ·C·252·100))²
             **须 net8 > 0 且 C > 0 才有正根**; 否则记 no_root 并写原因。
  优势交点 A_delta*: Δnet8 − κ·√A·ΔC·252·100 = 0
             **须 Δnet8/(κ·ΔC) > 0**; 负比值【不平方成伪容量】(plan §8.3)。
  所有根回代并标外推范围 (A* 超出 {1..20} 亿网格的标 extrapolated)。

限制 (如实写进输出): 本轮的冲击是【事后加性成本】, 不改变持仓, 所以解析求根成立;
一旦整数股 / 参与率 / 拒单改变库存, 就必须实跑账户扫符号变化区间, 那不在本轮。
5% / 10% / 20% ADV 参与率只作【压力列】, 不是已确认的可交易上限。

用法: python3 e6h_cost.py
"""
from __future__ import annotations
import os
import sys
import json
import time
import glob
import itertools

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H

RES = H.RES
AS = [1.0, 5.0, 10.0, 20.0]          # 亿元
KAPPAS = [0.25, 0.5, 1.0, 2.0]
ANN = 252 * 100.0
P0 = 0.01


def impact_ann(bracket, A_yi, kappa, form):
    A = A_yi * 1e8
    if form == 'sqrt':
        return kappa * np.sqrt(A) * bracket * ANN
    return kappa * (A / np.sqrt(P0)) * bracket * ANN


def root_A(net8, C, kappa, form):
    """净值归零的 A (亿元)。net8>0 且 C>0 才有正根。"""
    if not (np.isfinite(net8) and np.isfinite(C)) or net8 <= 0 or C <= 0:
        return np.nan, 'no_root: net8<=0 或 bracket<=0'
    if form == 'sqrt':
        s = net8 / (kappa * C * ANN)
        return (s ** 2) / 1e8, 'ok'
    return net8 / (kappa * C * ANN / np.sqrt(P0)) / 1e8, 'ok'


def main():
    t0 = time.time()
    od = os.path.join(RES, 'cost')
    os.makedirs(od, exist_ok=True)
    L = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(
        os.path.join(RES, 'L', 'L_main_*.csv')))], ignore_index=True)
    print('L 主网格 %d 行' % len(L))

    # ---------------- 情景表 ----------------
    rows = []
    for _, r in L.iterrows():
        base = dict(segment=r.segment, account=r.account, H=int(r.H), b=r.b,
                    budget=r.budget, net8_ann=r.net8_ann, gross_ann=r.gross_ann,
                    turn_mean=r.turn_mean,
                    net12_ann=r.gross_ann - r.turn_mean * 12e-4 * ANN,
                    bracket_sqrt=r.bracket_sqrt_mean, bracket_lin=r.bracket_lin_mean)
        rows.append(dict(base, A_yi=0.0, kappa=0.0, form='none',
                         impact_ann=0.0, net_impact_ann=r.net8_ann))
        for A, k, form in itertools.product(AS, KAPPAS, ('sqrt', 'lin')):
            C = r.bracket_sqrt_mean if form == 'sqrt' else r.bracket_lin_mean
            imp = impact_ann(C, A, k, form)
            rows.append(dict(base, A_yi=A, kappa=k, form=form,
                             impact_ann=imp, net_impact_ann=r.net8_ann - imp))
    sc = pd.DataFrame(rows)
    sc.to_csv(os.path.join(od, 'impact_scenarios.csv'), index=False)
    print('  情景表 %d 行 (%.0fs)' % (len(sc), time.time() - t0))

    # ---------------- 容量 A* ----------------
    cap = []
    for _, r in L.iterrows():
        for k, form in itertools.product(KAPPAS, ('sqrt', 'lin')):
            C = r.bracket_sqrt_mean if form == 'sqrt' else r.bracket_lin_mean
            A_, why = root_A(r.net8_ann, C, k, form)
            cap.append(dict(segment=r.segment, account=r.account, H=int(r.H), b=r.b,
                            budget=r.budget, kappa=k, form=form,
                            net8_ann=r.net8_ann, bracket=C,
                            A_star_yi=A_, status=why,
                            extrapolated=bool(np.isfinite(A_) and
                                              (A_ > max(AS) or A_ < min(AS))),
                            check_net_at_Astar=(r.net8_ann - impact_ann(C, A_, k, form)
                                                if np.isfinite(A_) else np.nan)))
    capd = pd.DataFrame(cap)
    capd.to_csv(os.path.join(od, 'capacity_A_star.csv'), index=False)
    ok = capd[capd.status == 'ok']
    print('  容量 A*: %d/%d 有正根; 回代残差 max %.3e'
          % (len(ok), len(capd), float(np.nanmax(np.abs(ok.check_net_at_Astar)))
             if len(ok) else np.nan))

    # ---------------- 优势交点 A_delta* ----------------
    # 每段内, 每个 (H,b,budget) 上, 各账户 vs R1 的交点
    dl = []
    for (seg, Hh, b, bud), g in L.groupby(['segment', 'H', 'b', 'budget']):
        ref = g[g.account == 'R1']
        if not len(ref):
            continue
        ref = ref.iloc[0]
        for _, r in g.iterrows():
            if r.account == 'R1':
                continue
            for k, form in itertools.product(KAPPAS, ('sqrt', 'lin')):
                Cr = ref.bracket_sqrt_mean if form == 'sqrt' else ref.bracket_lin_mean
                Cc = r.bracket_sqrt_mean if form == 'sqrt' else r.bracket_lin_mean
                dn, dC = r.net8_ann - ref.net8_ann, Cc - Cr
                ratio = dn / (k * dC) if (dC != 0) else np.nan
                if not np.isfinite(ratio) or ratio <= 0:
                    A_, why = np.nan, ('no_crossing: Δn/(κΔC)=%.3g <= 0 '
                                       '(负比值不平方成伪容量)' % ratio
                                       if np.isfinite(ratio) else 'no_crossing: ΔC=0')
                else:
                    if form == 'sqrt':
                        A_ = ((dn / (k * dC * ANN)) ** 2) / 1e8
                    else:
                        A_ = (dn / (k * dC * ANN / np.sqrt(P0))) / 1e8
                    why = 'ok'
                dl.append(dict(segment=seg, H=int(Hh), b=b, budget=bud,
                               account=r.account, vs='R1', kappa=k, form=form,
                               d_net8=dn, d_bracket=dC, A_delta_star_yi=A_,
                               status=why,
                               extrapolated=bool(np.isfinite(A_) and A_ > max(AS))))
    dld = pd.DataFrame(dl)
    dld.to_csv(os.path.join(od, 'advantage_crossing.csv'), index=False)
    print('  优势交点: %d 行, 有交点 %d (%.0f%%)'
          % (len(dld), (dld.status == 'ok').sum(), 100 * (dld.status == 'ok').mean()))

    # ---------------- 参与率压力列 ----------------
    # turn_mean 是【单边换手占组合】的日均; 名义成交额 = turn * A
    part = []
    for _, r in L[(L.b == 0) & (L.budget == 'matchN')].iterrows():
        for A in AS:
            notional = r.turn_mean * A * 1e8
            part.append(dict(segment=r.segment, account=r.account, H=int(r.H),
                             A_yi=A, daily_notional_yuan=notional,
                             note='参与率需逐票 ADV20 才能算; 此列只给日均名义成交额, '
                                  '5%/10%/20% ADV 的压力列留 UNAVAILABLE_WITH_REASON '
                                  '(需逐票 ADV 明细, 本轮 L 只存了括号均值)'))
    pd.DataFrame(part).to_csv(os.path.join(od, 'participation_notional.csv'), index=False)

    # ---------------- 领导表草稿 (H x A x κ) ----------------
    lead = sc[(sc.b == 0) & (sc.budget == 'matchN') & (sc.form == 'sqrt') &
              (sc.kappa == 0.5)]
    piv = lead.pivot_table(index=['segment', 'H'], columns='A_yi',
                           values='net_impact_ann', aggfunc='median')
    piv.to_csv(os.path.join(od, 'leader_table_draft_H_x_A.csv'))
    print('  领导表草稿 (H x A, κ=0.5, sqrt, 中位 over 账户):')
    print(piv.round(2).to_string())
    print('  —— 草稿, 经用户; **不选生产 H** (brief §8 末条)')
    print('总 %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
