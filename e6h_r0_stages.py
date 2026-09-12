#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h R0 第一块: 母体复原 + 集合契约 + T0 全分布 (brief §3, plan §2.3 / §4.1)。

对 R1 / R2 / A06 / A08 逐段复原五个集合:
  U = 冻结 pool0
  C = 真实源核心 (源 combine 允许部分因子有效时按真实源复现)
  V = 源否决实际删掉的票 (只在 C 内才算"被否决")
  B = C \\ V = 最终名单
  D = 该次【真实经济筛选拒绝】= cand ∩ {score 有限} \\ C
      —— 预热 / 3g 分箱失败 / 缺原核心分数【不算】D (plan §4.1)

T0 全分布 (plan §2.3): 不只比赢家均值。每个集合都报完整分布、负/正/中段贡献、
按实际权重的资本损益、以及"当前被留下的损失"。

用法: python3 e6h_r0_stages.py --segment 2010-2014
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
import e6g_core as G
import e6g_desc as GD
import e6g_t0 as T0
import e6f_core as F
import e6e_core as K

RES = H.RES
PARENTS = ['R1', 'R2', 'A06', 'A08']
QS = [1, 5, 10, 25, 50, 75, 90, 95, 99]


def dist_stats(x, w=None):
    """一个集合的【完整分布】统计, 不只均值。x = 标签值 (bp)。"""
    x = np.asarray(x, float)
    ok = np.isfinite(x)
    x = x[ok]
    d = dict(n=int(x.size))
    if x.size == 0:
        return d
    d['mean'] = float(x.mean())
    d['median'] = float(np.median(x))
    d['std'] = float(x.std(ddof=1)) if x.size > 1 else np.nan
    for q in QS:
        d['q%02d' % q] = float(np.percentile(x, q))
    neg, pos = x[x < 0], x[x > 0]
    d['frac_neg'] = float((x < 0).mean())
    d['frac_zero'] = float((x == 0).mean())
    # 负 / 正 / 中段(20-80 分位内) 对总和的贡献
    d['sum_all'] = float(x.sum())
    d['sum_neg'] = float(neg.sum())
    d['sum_pos'] = float(pos.sum())
    lo, hi = np.percentile(x, 20), np.percentile(x, 80)
    mid = x[(x >= lo) & (x <= hi)]
    d['sum_mid_20_80'] = float(mid.sum())
    d['n_mid_20_80'] = int(mid.size)
    d['mean_neg'] = float(neg.mean()) if neg.size else np.nan
    d['mean_pos'] = float(pos.mean()) if pos.size else np.nan
    if w is not None:
        w = np.asarray(w, float)[ok]
        sw = w.sum()
        if sw > 0:
            d['wmean'] = float((x * w).sum() / sw)
            d['w_sum_contrib'] = float((x * w).sum())
            d['w_sum_neg_contrib'] = float((x[x < 0] * w[x < 0]).sum())
            d['w_sum_pos_contrib'] = float((x[x > 0] * w[x > 0]).sum())
    return d


def veto_drop(ctx, cfg):
    """源否决实际删掉哪些 (与 full_mask_g 内部同一调用)。"""
    core = cfg['core']
    sel = core.get('sel', 'SRC')
    return ctx.build_veto_drop_g(cfg.get('veto'), core, None,
                                 sel=('QEDGE' if sel == 'QEDGE' else 'SRC'))


def pack(a):
    return np.packbits(np.asarray(a, bool), axis=None)


def dep_stages(ctx, cfg):
    """两段式核 (R1 = KT_dep(50,50)) 的分关拆解。plan §4.1 要求第一关 / 第二关 /
       双关例外【各自成卡】, 所以两关的拒绝集必须分开记 —— `build_core_g` 返回的
       cand 是第一关幸存者 s1, 只用它会把"第一关拒绝"整块漏掉。

       返回 dict(s1, Px, cut1, cut2) 或 None (非两段式核)。
       复刻 build_core_g 的两段式分支前半段, 参数逐个对齐。"""
    core = cfg['core']
    if core.get('kind') != 'dep':
        return None
    S = ctx.S
    md = core.get('neu', 'NS') or 'NS'
    dirs = core.get('dirs') or ['hi']
    tfs = core.get('tfs') or ['identity']
    Px = ctx.leg_pct(core['x'], md, dirs[0] if dirs else 'hi',
                     tfs[0] if tfs else 'identity')
    s1 = ctx._keep(Px, S.p0c, core['a'], 'SRC')
    # 逐日切点 (供第一关例外"只用原切点外推", 不重拟合)
    def cut_of(score, sel_mask):
        out = np.full(S.T, np.nan)
        for t in range(S.T):
            v = score[t][sel_mask[t]]
            v = v[np.isfinite(v)]
            if v.size:
                out[t] = float(v.max())        # 保留的是低分端, 切点 = 被留下的最大分
        return out
    return dict(s1=s1, Px=Px, cut1=cut_of(Px, s1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    seg = a.segment
    assert seg in H.DERIV_SEGS, ('R0 只在推导段跑 (brief §3); 收到 %r' % seg)
    t0 = time.time()
    out_dir = os.path.join(RES, 'T0_full_distribution')
    set_dir = os.path.join(RES, 'stage_sets')
    for d in (out_dir, set_dir):
        os.makedirs(d, exist_ok=True)

    S = H.seg(seg, verbose=False)
    ctx = GD.GCtx(S)
    tb = time.time() - t0

    # ---- 标签: 源版 + 端点复利版 ----
    lab_src, lab_comp = T0.labels(S)
    lab_src = lab_src.reindex(index=S.pool0.index, columns=S.pool0.columns)
    lab_comp = lab_comp.reindex(index=S.pool0.index, columns=S.pool0.columns)
    Lsrc = lab_src.values[:, S.ccols]
    Lcmp = lab_comp.values[:, S.ccols]
    tl = time.time() - t0

    rows, day_rows, packs = [], [], {}
    for lab in PARENTS:
        cid = G.DISPLAY_ID[lab]
        cfg = GD.parse_cfg(cid)
        Bm, score, cand, Cm = ctx.full_mask_g(cfg)
        dr = veto_drop(ctx, cfg)
        dr = np.zeros_like(Cm) if dr is None else dr
        fin = np.isfinite(score)
        U = S.p0c
        V = Cm & dr                      # 只有进了核才谈"被否决"
        D = cand & fin & (~Cm)           # 真实经济筛选拒绝 (均值/单因子核 = 全池; DEP = 第二关)
        # 预热/缺分数/3g 导致的排除, 单独记, 不算 D
        no_score = cand & (~fin)
        # DEP 分关 (plan §4.1): 第一关拒绝集必须单独有身份, 否则"第一关例外"无从建卡
        dep = dep_stages(ctx, cfg)
        if dep is not None:
            fin1 = np.isfinite(dep['Px'])
            D1 = U & fin1 & (~dep['s1'])          # 第一关拒绝 (还没进第二关)
            D2 = D                                 # 第二关拒绝 (= 上面的 D)
            packs['%s_S1' % lab] = pack(dep['s1'])
            packs['%s_D1_stage1' % lab] = pack(D1)
            packs['%s_D2_stage2' % lab] = pack(D2)
            packs['%s_cut1' % lab] = dep['cut1']
            for lname, L in (('src', Lsrc), ('comp', Lcmp)):
                for nm, M in (('S1_stage1_kept', dep['s1']),
                              ('D1_stage1_rejected', D1),
                              ('D2_stage2_rejected', D2)):
                    st = dist_stats(L[M])
                    st.update(parent=lab, segment=seg, stage_set=nm, label=lname,
                              n_cells=int(M.sum()),
                              days_nonempty=int((M.sum(axis=1) > 0).sum()))
                    rows.append(st)
            print('       DEP 分关: S1 %d / 第一关拒绝 %d / 第二关拒绝 %d'
                  % (dep['s1'].sum(), D1.sum(), D2.sum()), flush=True)
        g = None
        if cfg['core']['kind'] in ('single', 'mean'):
            try:
                g = F.P2G[int(cfg['core']['s'])]
            except (KeyError, TypeError, ValueError):
                g = None
        codes, cnt = __import__('e6g_run').reason_codes(S, score, cand, Cm, Bm, g)

        # 实际 DEV 权重 (资本口径)
        idx, val = F.dev_from_dense(S, Bm)
        W = np.zeros_like(Lsrc)
        for t in range(S.T):
            if len(idx[t]):
                W[t, idx[t]] = val[t]

        for setname, M, wts in (('U_pool0', U, None), ('C_core', Cm, None),
                                ('V_vetoed', V, None), ('B_final', Bm, W),
                                ('D_econ_rejected', D, None),
                                ('no_score_excluded', no_score, None)):
            for lname, L in (('src', Lsrc), ('comp', Lcmp)):
                st = dist_stats(L[M], (wts[M] if wts is not None else None))
                st.update(parent=lab, segment=seg, stage_set=setname, label=lname,
                          n_cells=int(M.sum()),
                          days_nonempty=int((M.sum(axis=1) > 0).sum()))
                rows.append(st)
        # 逐日
        dd = pd.DataFrame(dict(
            date=S.dates, parent=lab, segment=seg,
            n_U=U.sum(axis=1), n_cand=cand.sum(axis=1), n_score_finite=(cand & fin).sum(axis=1),
            n_C=Cm.sum(axis=1), n_V=V.sum(axis=1), n_B=Bm.sum(axis=1), n_D=D.sum(axis=1),
            n_no_score=no_score.sum(axis=1), reason=codes,
            w_sum=W.sum(axis=1)))
        day_rows.append(dd)
        packs['%s_C' % lab] = pack(Cm)
        packs['%s_V' % lab] = pack(V)
        packs['%s_B' % lab] = pack(Bm)
        packs['%s_D' % lab] = pack(D)
        packs['%s_cand' % lab] = pack(cand)
        print('  %-4s C %6d / V %5d / B %6d / D %7d / 无分数 %6d ; 原因码 %s'
              % (lab, Cm.sum(), V.sum(), Bm.sum(), D.sum(), no_score.sum(), dict(cnt)),
              flush=True)

    pd.DataFrame(rows).to_csv(
        os.path.join(out_dir, 'stage_distributions_%s.csv' % seg), index=False)
    pd.concat(day_rows, ignore_index=True).to_csv(
        os.path.join(out_dir, 'stage_daily_%s.csv' % seg), index=False)
    packs['_shape'] = np.array([S.T, S.Nc])
    packs['_cols'] = np.asarray(S.ccolnames, dtype=object)
    packs['_dates'] = np.asarray([str(x)[:10] for x in S.dates], dtype=object)
    np.savez_compressed(os.path.join(set_dir, 'stage_sets_%s.npz' % seg), **packs)

    meta = dict(segment=seg, parents=PARENTS, build_s=round(tb, 1),
                labels_s=round(tl - tb, 1), total_s=round(time.time() - t0, 1),
                T=int(S.T), Nc=int(S.Nc),
                label_src='compute_forward_5d_excess(data, base_pool, hold_days=5, adjust=True)',
                label_comp='端点复利版 (e6g_t0.labels 第二个返回值)',
                note=('D 只含真实经济筛选拒绝 (cand ∩ 有限分数 \\ C); '
                      '预热/缺分数/3g 失败另记 no_score_excluded 与原因码'))
    with open(os.path.join(out_dir, 'meta_%s.json' % seg), 'w') as fh:
        json.dump(meta, fh, indent=1, ensure_ascii=False)
    print('  [%s] 建段 %.0fs 标签 %.0fs 合计 %.0fs'
          % (seg, tb, tl - tb, time.time() - t0))


if __name__ == '__main__':
    main()
