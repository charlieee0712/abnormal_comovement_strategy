#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 0 恒等锚 (阻断; brief §2 / plan §11.4)。只在推导段跑。

A 组 —— 测量逐位复现源 (独立重写, 不是把源值抄一遍):
  A1 T_std60      = turnover_volatility_60d      (turn.rolling(60,min 30).std(), 原始换手不掩停牌)
  A2 K0           = conditional_turnover          (tr/(|log(C/LC)|+1e-4))
  A3 CVR_20       = CVR_20d                       ((C-VW)/VW rolling(20,min 10).mean())
  A4 Park20       = -compute_parkinson_vol        (where(H>L) (ln H/L)^2/(4ln2) rolling(20,min 14).mean, sqrt)
  A5 V_cc20*√252  = realized_vol_20d              (log(C/LC) rolling(20,min 10).std()*√252; 核 log/不复权/ddof=1)
  A6 TCV_20       = E6h build_raw_h(TCV_20)       (std20/mean20, minv 10, mean<=0 -> NaN)
  A7 K_MA3 / K_ROS5 / K_ROS20 = e6f build_raw     (MA: rolling mean of K0; ROS: Σtr/(Σ|r|+nε) 共同有效日)
  A8 abn          = -compute_abnormal_turnover    (MA20(min10)/(MA120(min60)+1e-10))
  判据: 源有值的格 max|差| <= atol 1e-12 且 rtol 1e-10 (代数等价路径); NaN 模式在源有值处一致。
B 组 —— 管线: 缓存里的 LEGACY 成员 (取源值) 经 save/load/to_seg 后与 S.feats 同格逐位相等。
C 组 —— pct 链: E6i 的中性化 + 分位 (neu_cache + pct_dense_dir) 对 K/T/C 源键与
  G.get_pct_g 逐位相等 —— SLOT α=0 与新分量共用同一条路径的前提。
D 组 —— 研究版 vs 源版的【桥差】(不是锚, 只报告): 掩停牌 / 0.7w 有效数 / 预热 带来的差异格数与量级。

用法: python3 e6i_anchors.py --segment 2015-2018
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import math
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6h_core as H
import e6g_core as G
import e6g_desc as GD
import e6f_core as F
import e6e_core as K
from pool_screening_v2 import compute_parkinson_vol, compute_abnormal_turnover

ATOL, RTOL = 1e-12, 1e-10


def cmp(name, mine, src, level='ANCHOR'):
    """mine, src: 同一 (T, Nc) 网格。源有值处比较。"""
    m = np.isfinite(src)
    both = m & np.isfinite(mine)
    miss = int((m & ~np.isfinite(mine)).sum())
    if both.any():
        d = np.abs(mine[both] - src[both])
        tol = ATOL + RTOL * np.abs(src[both])
        mx, rel = float(d.max()), float((d / np.maximum(np.abs(src[both]), 1e-300)).max())
        n_bad = int((d > tol).sum())
    else:
        mx = rel = 0.0
        n_bad = 0
    ok = (n_bad == 0) and (miss == 0) and bool(both.any())
    return dict(test=name, level=level, ok=bool(ok), max_abs=mx, max_rel=rel, n_cells=int(both.sum()),
                n_exceed_tol=n_bad, n_src_finite_mine_nan=miss)


def grid(S, df):
    return I.to_grid(S, df)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    assert a.segment in I.DERIV_SEGS
    t0 = time.time()
    FE.build_catalog()
    I.set_protected_members(FE.protected_ids())
    S = I.seg_i(a.segment, warm=False)          # 源锚用 legacy 段数据 (与源同输入)
    d = S.data
    res = []
    feats = S.feats
    tr = d['turnover_rate'].astype(float)
    close, lclose = d['close'].astype(float), d['lclose'].astype(float)
    # A1
    mine = tr.rolling(60, min_periods=30).std()
    res.append(cmp('A1_T_std60', grid(S, mine), grid(S, feats['turnover_volatility_60d'])))
    # A2
    lr = np.log(close / lclose).replace([np.inf, -np.inf], np.nan)
    k0 = tr / (lr.abs() + 1e-4)
    res.append(cmp('A2_K0', grid(S, k0), grid(S, feats['conditional_turnover'])))
    # A3
    vw = d['vwap'].astype(float)
    cvr = ((close - vw) / vw.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
    res.append(cmp('A3_CVR20', grid(S, cvr.rolling(20, min_periods=10).mean()),
                   grid(S, feats['CVR_20d'])))
    # A4
    hi, lo = d['high'].astype(float), d['low'].astype(float)
    pv = (np.log(hi / lo) ** 2 / (4 * math.log(2))).where(hi > lo)
    park = np.sqrt(pv.rolling(20, min_periods=14).mean())
    res.append(cmp('A4_Park20', grid(S, park), grid(S, -compute_parkinson_vol(hi, lo))))
    # A5
    rv = lr.rolling(20, min_periods=10).std() * np.sqrt(252)
    res.append(cmp('A5_realized_vol20', grid(S, rv), grid(S, feats['realized_vol_20d'])))
    # A6 TCV_20 (E6h)
    m20 = tr.rolling(20, min_periods=10).mean()
    s20 = tr.rolling(20, min_periods=10).std()
    tcv = (s20 / m20).where(m20 > 0)
    src = H.build_raw_h(S, H.specH('TCV_20')).reindex(index=S.pool0.index, columns=S.pool0.columns)
    res.append(cmp('A6_TCV20_E6H', grid(S, tcv), grid(S, src)))
    # A7 E6f K 变体
    ad = lr.abs()
    for w, est in ((3, 'MA'), (5, 'ROS'), (20, 'ROS')):
        srcv = F.build_raw(d, F.spec('K', w, est=est, eps=1e-4))
        mp = F.mp(w)
        if est == 'MA':
            mine = (tr / (ad + 1e-4)).rolling(w, min_periods=mp).mean()
        else:
            v = tr.notna() & ad.notna()
            s_tr = tr.where(v).rolling(w, min_periods=mp).sum()
            s_rr = ad.where(v).rolling(w, min_periods=mp).sum()
            nn = tr.where(v).rolling(w, min_periods=mp).count()
            mine = (s_tr / (s_rr + nn * 1e-4)).where(nn >= mp)
        res.append(cmp('A7_K_%s%d_E6F' % (est, w), grid(S, mine), grid(S, srcv)))
    # A8 abn
    a20 = tr.rolling(20, min_periods=10).mean()
    a120 = tr.rolling(120, min_periods=60).mean()
    res.append(cmp('A8_abn', grid(S, a20 / (a120 + 1e-10)), grid(S, -compute_abnormal_turnover(tr))))

    # ---- B 组: 缓存管线 (LEGACY 成员取源值; 读缓存需推导段, 守卫放行) ----
    for mid, key in (('T_std60_LEGACY', 'turnover_volatility_60d'),
                     ('K0_LEGACY', 'conditional_turnover'), ('C_CVR20_LEGACY', 'CVR_20d'),
                     ('V_cc20_LEGACY', 'realized_vol_20d'), ('R_cr5_LEGACY', 'cum_return_5d')):
        arr, meta = I.load_member(a.segment, mid, 'OBS', where='anchor_B')
        if arr is None:
            res.append(dict(test='B_%s' % mid, level='ANCHOR', ok=False, note='缓存缺失'))
            continue
        srcg = grid(S, feats[key])
        same_nan = bool(np.array_equal(np.isnan(arr), np.isnan(srcg)))
        eq = bool(np.array_equal(np.nan_to_num(arr, nan=-9.9e99), np.nan_to_num(srcg, nan=-9.9e99)))
        res.append(dict(test='B_%s' % mid, level='ANCHOR', ok=bool(eq and same_nan),
                        bit_equal=eq, nan_pattern_equal=same_nan, sha=meta.get('sha256', '')[:16]))
    arr, _ = I.load_member(a.segment, 'V_park20_LEGACY', 'LEGACY_PARK_NAN', where='anchor_B')
    if arr is not None:
        res.append(cmp('B_V_park20_LEGACY', arr, grid(S, -compute_parkinson_vol(hi, lo))))

    # ---- C 组: pct 链逐位 ----
    for key in (K.FT, K.FK, K.FC):
        sp = GD.spec_of_key(key)
        ref = G.get_pct_g(S, sp, 'NS', 'hi')
        raw = feats[key].reindex(index=S.pool0.index, columns=S.pool0.columns)
        cache, _ = F.neu_cache(raw, S.pool0, S.log_mcap, S.icodes_neu, 'NS')
        mine = G.pct_dense_dir(cache, S.dates, S.ccolpos, S.Nc, 'hi')
        eq = bool(np.array_equal(np.nan_to_num(mine, nan=-1.0), np.nan_to_num(ref, nan=-1.0)))
        res.append(dict(test='C_pct_chain_%s' % K.SHORT[key], level='ANCHOR', ok=eq, bit_equal=eq,
                        n_finite=int(np.isfinite(ref).sum())))

    # ---- D 组: 研究版 vs 源版的桥差 (报告项) ----
    for mid, key, conv in (('T_std60', 'turnover_volatility_60d', lambda x: x),
                           ('V_cc20', 'realized_vol_20d', lambda x: np.sqrt(x) * np.sqrt(252)),
                           ('V_park20_obs', '__park__', lambda x: np.sqrt(x)),
                           ('T_cv20', 'E6H:TCV_20', lambda x: x)):
        arr, _ = I.load_member(a.segment, mid, FE.member(mid)['policy'], where='anchor_D')
        if arr is None:
            continue
        if key == '__park__':
            srcg = grid(S, -compute_parkinson_vol(hi, lo))
        elif key.startswith('E6H:'):
            srcg = grid(S, src)
        else:
            srcg = grid(S, feats[key])
        mine = conv(arr)
        p0 = S.p0c
        both = p0 & np.isfinite(mine) & np.isfinite(srcg)
        diff = np.abs(mine[both] - srcg[both])
        res.append(dict(test='D_bridge_%s' % mid, level='REPORT', ok=True,
                        pool0_cells=int(p0.sum()), both_finite=int(both.sum()),
                        research_only=int((p0 & np.isfinite(mine) & ~np.isfinite(srcg)).sum()),
                        source_only=int((p0 & ~np.isfinite(mine) & np.isfinite(srcg)).sum()),
                        frac_differ_1e9=float((diff > 1e-9).mean()) if both.any() else None,
                        median_rel_diff=float(np.median(diff / np.maximum(np.abs(srcg[both]),
                                                                           1e-12)))
                        if both.any() else None,
                        spearman_pool0=float(pd.Series(mine[both]).corr(pd.Series(srcg[both]),
                                                                         method='spearman'))
                        if both.sum() > 10 else None))

    anchors = [r for r in res if r['level'] == 'ANCHOR']
    out = dict(segment=a.segment, atol=ATOL, rtol=RTOL, n_anchor=len(anchors),
               n_pass=sum(r['ok'] for r in anchors), elapsed_s=round(time.time() - t0, 1),
               results=res)
    I.atomic_write_json(os.path.join(I.RES, 'checks', 'feature_anchors_%s.json' % a.segment), out)
    for r in res:
        print('%-24s %-6s %s  %s' % (r['test'], r['level'], 'OK ' if r['ok'] else '!! ',
                                     {k: v for k, v in r.items()
                                      if k not in ('test', 'level', 'ok')}))
    print('锚 %d/%d 过 (%.0fs)' % (out['n_pass'], out['n_anchor'], time.time() - t0))
    sys.exit(0 if out['n_pass'] == out['n_anchor'] else 1)


if __name__ == '__main__':
    main()
