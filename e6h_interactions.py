#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 条件交互 (plan §3.3, brief §4「交互清单(事前冻结)」)。

三组: M-T x E-V、E-V x R-O、E-V x I-P。
每组保留 **P / P+A / P+B / P+A+B 四条完整策略**; 交互差 = net_AB - net_A - net_B + net_P
(这只是组合构造上的交互, **不是经济因果分解**, plan §3.3)。

中心测量【按源清楚 / 支持范围选, 不按收益选】, 事前写死在 CENTERS 里:
  M-T -> TCV_20  (纯尺度不变的变异系数, 源定义最干净; turnover_5d 是水平不是稳定性)
  E-V -> volume_ratio_3d + 价格条件 REL_LOW_q20 (cr20 是 U34, 口径最熟)
  R-O -> JUMP_20 (min 10 个成对有效, 比 JUMP_5 支持更足)
  I-P -> w=20, q=0.2 (与 R0 里 REL_IND_20 的证据同窗口)
额度两档 eta {0.10, 0.25}。

名额冲突 (plan §3.3): E-V x I-P 两个都是 ADD, **共用一份总名额、等额切分、重复票只占
一次**, 不是把两个 ADD 简单叠加把额度翻倍。E-V x R-O 里风险否决【在机会加入后】运行,
作用于新旧名单。

用法: python3 e6h_interactions.py --segment 2010-2014
"""
from __future__ import annotations
import os
import sys
import json
import time
import argparse
import itertools

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_rules as RU
import e6h_run_routes as RR
import e6g_core as G
import e6g_desc as GD

RES = H.RES

CENTERS = dict(
    MT=dict(key='TCV_20', alphas=(0.5, 1.0), policy='FALLBACK'),
    EV=dict(key='volume_ratio_3d', price='REL_LOW_q20', q=0.2,
            etas=(0.10, 0.25), dirs=('quiet', 'surge')),
    RO=dict(key='JUMP_20', ks=(5, 10)),
    IP=dict(w=20, q=0.2, etas=(0.10, 0.25)),
)
PAIRS = [('MT', 'EV', ['R2', 'A06']),
         ('EV', 'RO', ['R1', 'R2', 'A06']),
         ('EV', 'IP', ['R1', 'R2', 'A06'])]


def ev_cond_and_g(P, direction):
    """E-V 中心卡的条件与排序分数。方向按源符号翻转 (复盘 #33)。"""
    c = CENTERS['EV']
    econ_high = (direction == 'surge')
    import e6h_expand as EX
    wh = EX.want_high(c['key'], econ_high)
    g = P.dir_score(c['key'], wh)
    cond = (RR.price_cond(P, c['price']) & np.isfinite(g) & (g <= c['q']))
    return cond, g, wh


def ip_cond_and_g(P):
    c = CENTERS['IP']
    ind = P.raw('IND_CUR_%d' % c['w'])
    rel = P.pct('REL_IND_%d' % c['w'])
    cond = np.isfinite(ind) & (ind > 0) & np.isfinite(rel) & (rel <= c['q'])
    return cond, rel


def slotted(P, alpha):
    """M-T 的中心改动: 把 T 位换成 TCV_20。返回 (mask, score, D)。"""
    import e6h_expand as EX
    li = EX.LEGS_OF[P.name].index('T')
    m, sc, cand, _ = RU.apply_slot(P.ctx, P.cfg, li, CENTERS['MT']['key'],
                                   alpha, CENTERS['MT']['policy'])
    # 新核下的经济拒绝集
    core = P.cfg['core']
    sel = core.get('sel', 'SRC')
    Cnew = P.ctx._keep(sc, P.S.p0c, core['s'], sel, core.get('depth'))
    D = P.S.p0c & np.isfinite(sc) & (~Cnew)
    return m, sc, D


def run(S, P, seg, rows):
    out = []
    cols = P.cols

    def rec(pair, parent, arm, mask, wmul=None, **kw):
        pnl = RU.run_mask(S, mask, wmul)
        g0, p0_, t0_, n0 = P.pnl
        g1, p1, t1, n1 = pnl
        both = np.isfinite(g0) & np.isfinite(g1)
        d = dict(pair=pair, parent=parent, arm=arm, segment=seg,
                 net8_ann=H.ann(n1), gross_ann=H.ann(g1),
                 turn_mean=float(np.nanmean(t1)), pos_mean=float(np.nanmean(p1)),
                 target_n_mean=float(mask.sum(axis=1).mean()),
                 d_net8_vs_parent=H.ann(np.where(both, n1 - n0, np.nan)),
                 n_mask_diff=int((mask != P.B).sum()))
        d.update(kw)
        out.append(d)
        return d['net8_ann']

    # ---------------- M-T x E-V ----------------
    if P.name in PAIRS[0][2]:
        for al, direction, eta in itertools.product(
                CENTERS['MT']['alphas'], CENTERS['EV']['dirs'], CENTERS['EV']['etas']):
            tag = dict(mt_alpha=al, ev_dir=direction, eta=eta)
            nP = rec('MT_x_EV', P.name, 'P', P.B, **tag)
            mA, scA, DA = slotted(P, al)
            nA = rec('MT_x_EV', P.name, 'P+A(MT)', mA, **tag)
            cond, g, wh = ev_cond_and_g(P, direction)
            mB, Ab, _ = RU.apply_add(P.B, P.D, g, eta, cols, cond)
            nB = rec('MT_x_EV', P.name, 'P+B(EV)', mB, n_added=int(Ab.sum()), **tag)
            # AB: 先换核 (新的 B 与新的 D), 再在新 D 上做 E-V 加回
            mAB, Aab, _ = RU.apply_add(mA, DA, g, eta, cols, cond)
            nAB = rec('MT_x_EV', P.name, 'P+A+B', mAB, n_added=int(Aab.sum()), **tag)
            out[-1]['interaction'] = nAB - nA - nB + nP

    # ---------------- E-V x R-O ----------------
    if P.name in PAIRS[1][2]:
        import e6h_expand as EX
        whr = EX.want_high(CENTERS['RO']['key'], True)   # 隔夜占比【高】= 风险高
        for direction, eta, k in itertools.product(
                CENTERS['EV']['dirs'], CENTERS['EV']['etas'], CENTERS['RO']['ks']):
            tag = dict(ev_dir=direction, eta=eta, ro_k=k)
            nP = rec('EV_x_RO', P.name, 'P', P.B, **tag)
            cond, g, wh = ev_cond_and_g(P, direction)
            mA, Aa, _ = RU.apply_add(P.B, P.D, g, eta, cols, cond)
            nA = rec('EV_x_RO', P.name, 'P+A(EV)', mA, n_added=int(Aa.sum()), **tag)
            bad = RR.risk_bad(P, CENTERS['RO']['key'], k, whr)
            mB = P.B & ~bad
            nB = rec('EV_x_RO', P.name, 'P+B(RO)', mB, **tag)
            # AB: 风险否决【在机会加入后】运行, 作用于新旧名单 (plan §3.3)
            mAB = mA & ~bad
            nAB = rec('EV_x_RO', P.name, 'P+A+B', mAB,
                      n_added=int(Aa.sum()),
                      n_new_removed_by_risk=int((Aa & bad).sum()), **tag)
            out[-1]['interaction'] = nAB - nA - nB + nP

    # ---------------- E-V x I-P ----------------
    if P.name in PAIRS[2][2]:
        for direction, eta in itertools.product(CENTERS['EV']['dirs'],
                                                CENTERS['EV']['etas']):
            tag = dict(ev_dir=direction, eta=eta)
            nP = rec('EV_x_IP', P.name, 'P', P.B, **tag)
            cev, gev, _ = ev_cond_and_g(P, direction)
            mA, Aa, _ = RU.apply_add(P.B, P.D, gev, eta, cols, cev)
            nA = rec('EV_x_IP', P.name, 'P+A(EV)', mA, n_added=int(Aa.sum()), **tag)
            cip, gip = ip_cond_and_g(P)
            mB, Ab, _ = RU.apply_add(P.B, P.D, gip, eta, cols, cip)
            nB = rec('EV_x_IP', P.name, 'P+B(IP)', mB, n_added=int(Ab.sum()), **tag)
            # AB: 共用一份总名额, 等额切分, 重复票只占一次 (plan §3.3)
            half = eta / 2.0
            _, A1, _ = RU.apply_add(P.B, P.D, gev, half, cols, cev)
            _, A2, _ = RU.apply_add(P.B, P.D, gip, half, cols, cip)
            mAB = P.B | A1 | A2
            nAB = rec('EV_x_IP', P.name, 'P+A+B', mAB,
                      n_added=int((A1 | A2).sum()),
                      n_overlap=int((A1 & A2).sum()),
                      budget_note='shared_total_eta_split_equally', **tag)
            out[-1]['interaction'] = nAB - nA - nB + nP
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    assert a.segment in H.DERIV_SEGS
    t0 = time.time()
    S = H.seg(a.segment, verbose=False)
    allout = []
    for pname in ('R1', 'R2', 'A06'):
        P = RR.ParentCtx(S, pname)
        H.guard_h(['TCV_20', 'volume_ratio_3d', 'JUMP_20', 'IND_CUR_20', 'REL_IND_20'],
                  'trade', segment=a.segment, label_end=H.PROTECTED_LABEL_END,
                  where='interactions/%s' % pname, rule_objects=['ADD', 'SLOT_FALLBACK'])
        allout.extend(run(S, P, a.segment, None))
        print('  %s 完成, 累计 %d 行, %.0fs' % (pname, len(allout), time.time() - t0),
              flush=True)
        del P
    od = os.path.join(RES, 'interaction_results')
    os.makedirs(od, exist_ok=True)
    pd.DataFrame(allout).to_csv(
        os.path.join(od, 'interactions_%s.csv' % a.segment), index=False)
    print('写出 interactions_%s.csv: %d 行, %.0fs' % (a.segment, len(allout),
                                                      time.time() - t0))


if __name__ == '__main__':
    main()
