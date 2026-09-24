#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i carried C2: 成本透镜 (plan §9.2; brief §10)。成本模型独立于待检验测量:
  σ20 / ADV20 (执行日前历史, e6g_c.MarketCtx 全部 shift(1)) + 已锚的 sqrt 冲击 bracket (e6g_c.profile_and_impact:
  Σ|q|^1.5 σ20/√ADV20; 线性形式 Σq²σ/ADV 单独列) —— 新 V / EDGE 不替换成本模型。
情景 A ∈ {1, 5, 10} 亿元 x κ ∈ {0.25, 0.5, 1} (sqrt); 逐情景子 − 同规模母体; 净值归零规模按 e6h_cost.root_A
(须 a/b > 0 且 b ≠ 0, 否则 no_root; κ 未校准 -> 不输出可部署规模, 只作情景)。
日频压力代理 Q/ADV20 = A·|Δw| / ADV20 (执行日前可知), 报成交额加权均值与 p95 —— 不是实际 POV。
范围: 推导两段的全部 Stage 2 主描述符 (不挑); 后段只算旧输入母体并封存 (B 前不读)。
用法: python3 e6i_c2.py --segment 2010-2014 --route RT --shard 0 --nshard 4
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import time
import argparse
import collections
import traceback

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6i_engine as E
import e6i_stage2 as S2
import e6g_c as GC
import e6h_cost as HC
import e6e_core as K

AS = (1.0, 5.0, 10.0)
KAPPAS = (0.25, 0.5, 1.0)
POST = ('2019-2023', '2024-2026')


def idxval(W):
    idx, val = [], []
    for t in range(W.shape[0]):
        h = np.flatnonzero(W[t] > 0)
        idx.append(h)
        val.append(W[t, h])
    return idx, val


def lens(S, MC, W, H, net8_series):
    idx, val = idxval(W)
    br, prof, tw, qmiss, nh, live = GC.profile_and_impact(MC, idx, val, H, full_profile=False)
    out = dict(bracket_sqrt_mean=float(np.nanmean(br['sqrt'])), bracket_lin_mean=float(np.nanmean(br['lin'])),
               qmiss_frac=float(np.nansum(qmiss) / max(np.nansum(tw), 1e-12)))
    n8 = I.ann(net8_series)
    for A in AS:
        for kp in KAPPAS:
            c = GC.impact_cost(np.nan_to_num(br['sqrt']), A, kp, 'sqrt')
            out['net8_minus_sqrt_A%g_k%g' % (A, kp)] = n8 - float(np.mean(c)) * I.ANN
        cl = GC.impact_cost(np.nan_to_num(br['lin']), A, 1.0, 'lin')
        out['lin_cost_ann_A%g_k1' % A] = float(np.mean(cl)) * I.ANN
    Cm = float(np.nanmean(br['sqrt']))
    for kp in KAPPAS:
        r, why = HC.root_A(n8, Cm, kp, 'sqrt')
        out['root_A_yi_k%g' % kp] = r
        out['root_note_k%g' % kp] = why
    # Q/ADV20 日频压力代理 (A = 1 亿; 其他 A 线性放大)
    pres = []
    wts = []
    for t, hz, w, qz, q in GC.walk_holdings(S, idx, val, H):
        if len(qz):
            adv = MC.ADV20[t, qz]
            ok = np.isfinite(adv) & (adv > 0)
            if ok.any():
                pres.append(1e8 * np.abs(q[ok]) / adv[ok])
                wts.append(np.abs(q[ok]))
    if pres:
        p = np.concatenate(pres)
        wv = np.concatenate(wts)
        out['q_adv_A1_wmean'] = float((p * wv).sum() / wv.sum())
        out['q_adv_A1_p95'] = float(np.percentile(p, 95))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--route', default='mothers')
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshard', type=int, default=1)
    a = ap.parse_args()
    seg = a.segment
    post = seg in POST
    t0 = time.time()
    FE.build_catalog()
    FE.CATALOG_IDS = {m['member_id'] for m in FE.CATALOG}
    I.set_protected_members(FE.protected_ids())
    if post:
        # Stage 3 技术修复: 记录 B 前后段只算旧输入母体 (封存); B 后批准清单内的路线也可算 (逐描述符过守卫)
        assert a.route == 'mothers' or I.post_allowed(seg), '后段只算旧输入母体 (记录 B 前)'
        if a.route == 'mothers':
            I.guard_i([], ['C1_POST'], segment=seg, use='compute', sealed=True, where='c2:%s' % seg)
    S = I.seg_i(seg, warm=False)
    MC = GC.MarketCtx(S)
    RN = S2.Runner(S)
    rows = []
    if a.route == 'mothers':
        for mn in I.MOTHERS:
            M = RN.mother(mn)
            W = RN.parent_W[mn]
            for H in (1, 2, 3, 5, 10, 20):
                g, p, u, n = E.pnl_W(S, W, H, I.COST)
                rec = dict(segment=seg, kind='mother', descriptor_id='MOTHER|%s|H%d' % (mn, H), mother_id=mn, H=H,
                           net8_ann=I.ann(n))
                rec.update(lens(S, MC, W, H, n))
                rows.append(rec)
        d = pd.DataFrame(rows)
        if post:
            I.sealed_write_csv(seg, 'c2_mothers', d)
            print('[%s] C2 母体 封存 %d 行; %.0fs' % (seg, len(d), time.time() - t0))
            return
        od = os.path.join(I.RES, 'carried', 'C2', seg)
        os.makedirs(od, exist_ok=True)
        I.atomic_write_csv(os.path.join(od, 'c2_mothers.csv'), d)
        print('[%s] C2 母体 %d 行; %.0fs' % (seg, len(d), time.time() - t0))
        return
    assert seg in I.DERIV_SEGS or I.post_allowed(seg)
    dd = pd.read_csv(os.path.join(I.RES, 'registry', 'descriptors_A0.csv'), low_memory=False)
    dd = dd[dd.route_id == a.route]
    groups = collections.OrderedDict()
    for r in dd.to_dict('records'):
        groups.setdefault(S2.config_key(r), []).append(r)
    keys = list(groups)[a.shard::a.nshard]
    n_fail = 0
    for gi, k in enumerate(keys):
        rs = groups[k]
        r0 = rs[0]
        members = [x for x in str(r0['member_id']).replace('+', '|').split('|') if x in FE.CATALOG_IDS]
        try:
            I.guard_i(members, [S2.ROLE_RULE.get(r0['role'], r0['role'])], segment=seg,
                      label_end=str(S.dates[-1].date()), use='trade', where='c2:' + r0['descriptor_id'])
            mask, wmul, info = RN.build(r0)
            W = E.dev_weights(S, mask)
            if wmul is not None:
                W = W * wmul
            for r in rs:
                H = int(r['H'])
                g, p, u, n = E.pnl_W(S, W, H, I.COST)
                rec = dict(segment=seg, kind='child', descriptor_id=r['descriptor_id'], route_id=r['route_id'],
                           mother_id=r['mother_id'], H=H, net8_ann=I.ann(n))
                rec.update(lens(S, MC, W, H, n))
                rows.append(rec)
        except Exception as e:
            n_fail += 1
            traceback.print_exc()
            for r in rs:
                rows.append(dict(segment=seg, kind='child', descriptor_id=r['descriptor_id'], status='FAILED_TECH',
                                 note='%s: %s' % (type(e).__name__, str(e)[:150])))
        if (gi + 1) % 25 == 0:
            print('  %d/%d 配置 %.0fs' % (gi + 1, len(keys), time.time() - t0), flush=True)
    od = os.path.join(I.RES, 'carried', 'C2', seg)
    os.makedirs(od, exist_ok=True)
    tag = 'c2_%s_%02d' % (a.route, a.shard)
    I.atomic_write_csv(os.path.join(od, tag + '.csv'), pd.DataFrame(rows))
    I.write_receipt(os.path.join(I.RES, 'task_status', 'c2_%s_%s.receipt.json' % (seg, tag)), 'c2:%s:%s' % (seg, tag),
                    [os.path.join(od, tag + '.csv')], status='SUCCEEDED' if n_fail == 0 else 'FAILED',
                    n_fail=n_fail, n_configs=len(keys), elapsed_s=round(time.time() - t0, 1))
    print('[%s %s] 配置 %d / 失败 %d; %.0fs' % (seg, tag, len(keys), n_fail, time.time() - t0))


if __name__ == '__main__':
    main()
