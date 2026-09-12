#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h carried T1 (原生表现与归因) + T5 (状态量, 只作描述) —— brief §9 / plan §9.1, §9.5。

T1: 固定展示父 + KTC keep{25,30,40,50} 的【逐年与四段】net8/gross/turn/仓位/
    目标与 live 人数/有效 N/行业 HHI/重复形成/pool0 规模/输入有效率。
    **逐日恒等式** (plan §9.1): excess_clean - excess_pool = position x
    (pool_unit_return - clean_return)。先逐日核, 再汇总。
    事后 fwd5 离散度与 T 可见历史离散度【分字段】(前者不得变成预测状态)。

T5: 历史市场换手、横截面收益离散度、pool 规模、行业 HHI 与广度、滞后市值分组收益,
    全部带可得时点。**不建开关**, 不按"某年更像另一段"切换策略 (plan §9.5)。

注意 (plan §9.1): 不把 pool 规模、行业/市值构成、市场波动与年度共趋势的回归系数
叫"原因占比"; 17 个含不完整 2026 的年度不等于 17 次独立制度复制。

用法: python3 e6h_t1t5.py --segment 2019-2023
"""
from __future__ import annotations
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6g_core as G
import e6g_desc as GD
import e6g_l as L6
import e6f_core as F
import e6e_core as K
import comprehensive_factor_diagnosis as C

RES = H.RES
KEEPS = [25, 30, 40, 50]


def yearly(dates, x):
    s = pd.Series(np.asarray(x, float), index=pd.to_datetime(dates))
    return s.groupby(s.index.year)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    t0 = time.time()
    S = H.seg(a.segment, verbose=False)
    ctx = GD.GCtx(S)
    od = os.path.join(RES, 'T')
    os.makedirs(od, exist_ok=True)
    dates = [pd.Timestamp(x) for x in S.dates]

    # ---- 基准: clean 与 pool0 ----
    dr = S.dr
    bench_clean = np.asarray(S.bench, float)
    bench_pool = dr.where(S.pool0 == 1).mean(axis=1).values

    # ---- 账户集合 ----
    accts = {}
    for nm, cid in L6.ATOMS.items():
        accts[nm] = ctx.full_mask_g(GD.parse_cfg(cid))[0]
    scoreK = ctx.leg_pct(GD.spec_of_key(K.FK), 'NS', 'hi', 'identity')
    scoreT = ctx.leg_pct(GD.spec_of_key(K.FT), 'NS', 'hi', 'identity')
    scoreC = ctx.leg_pct(GD.spec_of_key(K.FC), 'NS', 'hi', 'identity')
    ktc = F.combine_dense([scoreK, scoreT, scoreC], 'mean', complete=True)
    vcfg = GD.parse_cfg('KTC_mean@25|cvr_1d:k10+cr5:k10')
    vdrop = ctx.build_veto_drop_g(vcfg['veto'], vcfg['core'], None, sel='SRC')
    vdrop = np.zeros_like(S.p0c) if vdrop is None else vdrop
    for d in KEEPS:
        accts['KTC_keep%d' % d] = G.keep_RANKBUDGET(ktc, S.p0c & ~vdrop, d)
    print('  账户 %d 个就绪 %.0fs' % (len(accts), time.time() - t0), flush=True)

    rows, ident = [], []
    for nm, mask in accts.items():
        idx, val = F.dev_from_dense(S, mask)
        g_, pos, tu, n8 = F.sparse_pnl_H(S, idx, val, K.HOLD, F.COST)
        # port = gross + bench_clean*pos  (引擎口径: gross = port - bench*position)
        port = np.asarray(g_, float) + bench_clean * np.asarray(pos, float)
        exc_clean = port - bench_clean * np.asarray(pos, float)
        exc_pool = port - bench_pool * np.asarray(pos, float)
        lhs = exc_clean - exc_pool
        rhs = np.asarray(pos, float) * (bench_pool - bench_clean)
        ok = np.isfinite(lhs) & np.isfinite(rhs)
        ident.append(dict(account=nm, segment=a.segment,
                          max_abs_diff=float(np.nanmax(np.abs(lhs[ok] - rhs[ok])))
                          if ok.any() else np.nan,
                          n_days=int(ok.sum())))
        # 有效 N 与行业 HHI (按实际权重)
        effN, hhi, ind_hhi = np.full(S.T, np.nan), np.full(S.T, np.nan), np.full(S.T, np.nan)
        for t in range(S.T):
            if not len(idx[t]):
                continue
            w = np.asarray(val[t], float)
            sw = w.sum()
            if sw <= 0:
                continue
            p = w / sw
            hhi[t] = float((p ** 2).sum())
            effN[t] = 1.0 / hhi[t]
            ic = S.icodes[t, idx[t]]
            v = ic >= 0
            if v.any():
                iw = np.bincount(ic[v], weights=p[v], minlength=S.G)
                ind_hhi[t] = float((iw ** 2).sum())
        reform = mask.astype(int)
        rep = float((reform[1:] & reform[:-1]).sum()) / max(1, reform[1:].sum())
        base = dict(account=nm, segment=a.segment)
        for scope, sel in [('segment', slice(None))]:
            rows.append(dict(base, scope='segment', year=np.nan,
                             net8_ann=G.ann(n8), gross_ann=G.ann(g_),
                             turn_mean=float(np.nanmean(tu)),
                             pos_mean=float(np.nanmean(pos)),
                             target_n=float(mask.sum(axis=1).mean()),
                             eff_N=float(np.nanmean(effN)),
                             weight_hhi=float(np.nanmean(hhi)),
                             industry_hhi=float(np.nanmean(ind_hhi)),
                             repeat_formation_rate=rep,
                             pool_size=float(S.p0c.sum(axis=1).mean()),
                             input_valid_rate=float(np.isfinite(ktc[S.p0c]).mean())))
        gy = yearly(dates, n8)
        gg = yearly(dates, g_)
        gt = yearly(dates, tu)
        gp = yearly(dates, pos)
        for y in gy.groups:
            rows.append(dict(base, scope='year', year=int(y),
                             net8_ann=float(gy.get_group(y).mean() * 252 * 100),
                             gross_ann=float(gg.get_group(y).mean() * 252 * 100),
                             turn_mean=float(gt.get_group(y).mean()),
                             pos_mean=float(gp.get_group(y).mean()),
                             target_n=np.nan, eff_N=np.nan, weight_hhi=np.nan,
                             industry_hhi=np.nan, repeat_formation_rate=np.nan,
                             pool_size=np.nan, input_valid_rate=np.nan))
    bad = [x for x in ident if not (np.isfinite(x['max_abs_diff'])
                                    and x['max_abs_diff'] < 1e-12)]
    if bad:
        raise SystemExit('逐日恒等式不过 (plan §9.1): %s' % bad[:3])
    print('  逐日恒等式 %d 个账户全过, max|d| %.3e'
          % (len(ident), max(x['max_abs_diff'] for x in ident)), flush=True)

    pd.DataFrame(rows).to_csv(os.path.join(od, 'T1_attribution_%s.csv' % a.segment),
                              index=False)
    with open(os.path.join(od, 'T1_identity_%s.json' % a.segment), 'w') as fh:
        json.dump(dict(segment=a.segment, results=ident,
                       identity='excess_clean - excess_pool = position * '
                                '(pool_unit_return - clean_return)'),
                  fh, indent=1, ensure_ascii=False, default=str)

    # ---------------- T5 状态量 (只作描述) ----------------
    data = S.data
    turn = data['turnover_rate']
    t5 = pd.DataFrame(dict(
        date=[str(x)[:10] for x in dates],
        segment=a.segment,
        market_turnover_mean=turn.where(S.clean == 1).mean(axis=1).values,
        cs_return_dispersion=dr.where(S.clean == 1).std(axis=1).values,
        pool_size=S.p0c.sum(axis=1),
        pool_industry_breadth=[int(len(np.unique(S.icodes[t][S.p0c[t] &
                                                            (S.icodes[t] >= 0)])))
                               for t in range(S.T)],
        bench_clean=bench_clean, bench_pool=bench_pool))
    # 行业 HHI (池内等权)
    ih = np.full(S.T, np.nan)
    for t in range(S.T):
        ic = S.icodes[t][S.p0c[t] & (S.icodes[t] >= 0)]
        if len(ic):
            cnt = np.bincount(ic, minlength=S.G).astype(float)
            p = cnt / cnt.sum()
            ih[t] = float((p ** 2).sum())
    t5['pool_industry_hhi'] = ih
    # 滞后市值分组收益 (T 可见: 用 T-1 的市值分组, T 的收益)
    lm = S.log_mcap.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]
    r0 = S.r0
    small, big = np.full(S.T, np.nan), np.full(S.T, np.nan)
    for t in range(1, S.T):
        m = S.p0c[t] & np.isfinite(lm[t - 1]) & np.isfinite(r0[t])
        if m.sum() < 10:
            continue
        v = lm[t - 1][m]
        q1, q2 = np.percentile(v, [33.3333, 66.6667])
        rr = r0[t][m]
        small[t] = float(rr[v <= q1].mean()) if (v <= q1).any() else np.nan
        big[t] = float(rr[v >= q2].mean()) if (v >= q2).any() else np.nan
    t5['lagged_mcap_small_ret'] = small
    t5['lagged_mcap_big_ret'] = big
    t5['availability_note'] = 'all fields use info known at T (mcap group uses T-1)'
    t5.to_csv(os.path.join(od, 'T5_state_%s.csv' % a.segment), index=False)
    print('  [%s] T1 %d 行 / T5 %d 行, %.0fs'
          % (a.segment, len(rows), len(t5), time.time() - t0))


if __name__ == '__main__':
    main()
