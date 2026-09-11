#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 块 T0: 输家解剖 (brief §4 / plan §2T0) —— 回答 Q1 / Q2。

只用 2010-2014、2015-2018。主标签严格复用 E3 的 compute_forward_5d_excess (日超额【累加】,
基准 = 传入的 base_pool 等权), 另报端点复利版, 命名不混。
三层对象: pool0 全体 / R1·R2·A06·A08 保留集中的输家 / 这些策略剔除的赢家。
事件计数三账 (形成机会 / spell 首次进入 / age=1..5)。128 条伪输家路径。
T0-35 只用 U35 三十五键; T0-74 加 NEW40 (守卫: 只在推导段, label_end <= 2018-12-31)。
"""
import os, sys, json, time, argparse
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6g_core as G
import e6g_desc as GD
import comprehensive_factor_diagnosis as C
from event_study import get_base_pool
from pool_screening_v2 import define_i11_signal

STRATS = {'R1': 'KT_dep(50,50)|C:k5', 'R2': 'KT_mean@30|C:k5+cr5:k10',
          'A06': 'KTC_mean@25|cvr_1d:k10+cr5:k10', 'A08': 'T@30|C:k5+cr5:k10'}
CORE_ONLY = {'R1': 'KT_dep(50,50)', 'R2': 'KT_mean@30',
             'A06': 'KTC_mean@25', 'A08': 'T@30'}


def labels(S):
    """源版 (日超额累加) + 端点复利版。两者都只用本段数据, 段尾自然 NaN。"""
    bp = get_base_pool(S.data)
    src = C.compute_forward_5d_excess(S.data, bp, hold_days=K.HOLD, adjust=True)
    dr = C.vwap_daily_return(S.data, K.ADJUST)
    bm = dr.where(bp == 1).mean(axis=1)
    gp = (1.0 + dr)
    gb = (1.0 + bm)
    pr = np.ones(gp.shape)
    pb = np.ones(len(gb))
    for k in range(2, 2 + K.HOLD):
        pr = pr * gp.shift(-k).values      # 任一日缺失 -> NaN (只允许区间内完整端点)
        pb = pb * gb.shift(-k).values
    comp = (pd.DataFrame(pr, index=gp.index, columns=gp.columns).sub(pd.Series(pb, index=gp.index),
                                                                     axis=0)) * 1e4
    return src, comp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--keyset', default='U35', choices=['U35', 'U74'])
    ap.add_argument('--npath', type=int, default=128)
    A = ap.parse_args()
    assert A.segment in G.DERIV_SEGS, 'T0 只跑推导段'
    t0 = time.time()
    S = G.seg(A.segment, verbose=False)
    ctx = GD.GCtx(S)
    out = os.path.join(G.RES, 'T0_35' if A.keyset == 'U35' else 'T0_74_discovery')
    os.makedirs(out, exist_ok=True)
    print('段就绪 %.0fs T=%d Nc=%d keyset=%s' % (time.time() - t0, S.T, S.Nc, A.keyset),
          flush=True)

    keys = list(G.U35) if A.keyset == 'U35' else sorted(set(G.U35) | set(G.NEW40))
    keys = [k for k in keys if k not in G.DIAGNOSTIC_ONLY]
    lin = G.Lin(keys)
    G.guard(lin, 'label', segment=A.segment, label_end=str(S.dates[-1].date()), where='T0')

    fsrc, fcomp = labels(S)
    Y = fsrc.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]
    Yc = fcomp.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]
    p0 = S.p0c
    have = p0 & np.isfinite(Y)
    print('形成格 %d, 标签有值 %d (%.4f)' % (p0.sum(), have.sum(), have.sum() / p0.sum()),
          flush=True)

    # ---- 分位标签: 形成日 pool0 内最差 / 最好 20% (10% 敏感性) ----
    flags = {}
    for q in (0.10, 0.20):
        lo = np.zeros(Y.shape, bool); hi = np.zeros(Y.shape, bool)
        for t in range(S.T):
            v = np.flatnonzero(have[t])
            if len(v) < 10:
                continue
            r = pd.Series(Y[t, v]).rank(pct=True).to_numpy()
            lo[t, v] = r <= q
            hi[t, v] = r >= 1 - q
        flags['loser_q%d' % int(q * 100)] = lo
        flags['winner_q%d' % int(q * 100)] = hi
    flags['neg_abs'] = have & (Y < 0)

    # ---- 策略覆盖: 核保留 / 否决剔除 / 最终保留 ----
    cov = {}
    for nm, cid in STRATS.items():
        m_final, score, cand, m_core = ctx.full_mask_g(GD.parse_cfg(cid))
        cov[nm] = dict(final=m_final, core=m_core,
                       vetoed=(m_core & ~m_final), dropped=(p0 & ~m_final))
    print('策略覆盖就绪 %.0fs' % (time.time() - t0), flush=True)

    # ---- 事件计数三账 ----
    sg = define_i11_signal(S.feats, get_base_pool(S.data)).reindex(
        index=S.pool0.index, columns=S.pool0.columns).fillna(0).values[:, S.ccols]
    age = np.zeros(sg.shape, np.int8)
    for lag in range(5, 0, -1):
        sh = np.zeros_like(sg); sh[lag:] = sg[:-lag]
        age = np.where(sh > 0, lag, age)
    spell_first = p0 & (age == 1) & ~np.vstack([np.zeros((1, S.Nc), bool), p0[:-1]])
    counts = dict(formation_cells=int(p0.sum()), spell_first_entries=int(spell_first.sum()),
                  by_age={int(a): int((p0 & (age == a)).sum()) for a in range(1, 6)})

    # ---- 画像: 每个键在各组的池内 NS pct 均值 (+ 日期块 bootstrap 区间) ----
    P = {}
    for kk in keys:
        try:
            P[kk] = ctx.leg_pct(GD.spec_of_key(kk))
        except Exception as e:
            print('  !! 键 %s 跳过: %s' % (kk, str(e)[:80]), flush=True)
    print('%d 个键的 pct 就绪 %.0fs' % (len(P), time.time() - t0), flush=True)

    groups = {'pool_all': have}
    for g_ in ('loser_q20', 'winner_q20', 'loser_q10', 'winner_q10', 'neg_abs'):
        groups[g_] = have & flags[g_]
    for nm in STRATS:
        groups['%s_kept_loser' % nm] = have & flags['loser_q20'] & cov[nm]['final']
        groups['%s_dropped_winner' % nm] = have & flags['winner_q20'] & cov[nm]['dropped']
        groups['%s_kept_all' % nm] = have & cov[nm]['final']

    dts = pd.DatetimeIndex(S.dates)
    yrs = dts.year.to_numpy()
    prof_rows = []
    rng = np.random.default_rng(20260911)
    nblk = max(1, S.T // 20)
    for gname, gm in groups.items():
        n = int(gm.sum())
        r = dict(segment=A.segment, keyset=A.keyset, group=gname, n_cells=n,
                 n_days=int(gm.any(axis=1).sum()),
                 fwd5_src_mean=float(np.nanmean(Y[gm])) if n else np.nan,
                 fwd5_compound_mean=float(np.nanmean(Yc[gm])) if n else np.nan)
        for kk, Pk in P.items():
            m2 = gm & np.isfinite(Pk)
            r['pct_' + kk] = float(np.nanmean(Pk[m2])) if m2.any() else np.nan
        # 日期块 bootstrap (块长 20) 的区间, 只对主标签与前 8 个键
        if n:
            bs = []
            for _ in range(200):
                st_ = rng.integers(0, max(1, S.T - 20), size=nblk)
                sel = np.zeros(S.T, bool)
                for s_ in st_:
                    sel[s_:s_ + 20] = True
                mm = gm & sel[:, None]
                bs.append(float(np.nanmean(Y[mm])) if mm.any() else np.nan)
            bs = np.array(bs, float)
            r['fwd5_src_lo'] = float(np.nanpercentile(bs, 2.5))
            r['fwd5_src_hi'] = float(np.nanpercentile(bs, 97.5))
        prof_rows.append(r)
    pd.DataFrame(prof_rows).to_csv(
        os.path.join(out, 'T0_profiles_%s_%s.csv' % (A.keyset, A.segment)), index=False)
    print('画像 %d 组 %.0fs' % (len(prof_rows), time.time() - t0), flush=True)

    # ---- 覆盖矩阵: 原规则是否剔除 x 输家/赢家 x 损失/机会 ----
    covrows = []
    for nm in STRATS:
        for lab, lm in (('loser_q20', flags['loser_q20']), ('winner_q20', flags['winner_q20']),
                        ('neg_abs', flags['neg_abs'])):
            for state, sm in (('dropped', cov[nm]['dropped']), ('kept', cov[nm]['final']),
                              ('vetoed', cov[nm]['vetoed']), ('core_kept', cov[nm]['core'])):
                m2 = have & lm & sm
                den = int((have & lm).sum())
                covrows.append(dict(segment=A.segment, strategy=nm, label=lab, state=state,
                                    n=int(m2.sum()), denom_label=den,
                                    denom_state=int((have & sm).sum()),
                                    share_of_label=(m2.sum() / den if den else np.nan),
                                    mean_fwd5=float(np.nanmean(Y[m2])) if m2.any() else np.nan,
                                    sum_fwd5_bp=float(np.nansum(Y[m2])) if m2.any() else np.nan,
                                    n_days=int(m2.any(axis=1).sum())))
    pd.DataFrame(covrows).to_csv(
        os.path.join(out, 'T0_coverage_%s_%s.csv' % (A.keyset, A.segment)), index=False)

    # ---- 逐年 / 逐行业 / 逐 age 的剩余损失 ----
    byrows = []
    for nm in STRATS:
        kept_loser = have & flags['loser_q20'] & cov[nm]['final']
        for y in sorted(set(yrs)):
            mm = kept_loser & (yrs == y)[:, None]
            byrows.append(dict(segment=A.segment, strategy=nm, dim='year', key=int(y),
                               n=int(mm.sum()),
                               sum_fwd5_bp=float(np.nansum(Y[mm])) if mm.any() else 0.0))
        for a in range(1, 6):
            mm = kept_loser & (age == a)
            byrows.append(dict(segment=A.segment, strategy=nm, dim='age', key=a,
                               n=int(mm.sum()),
                               sum_fwd5_bp=float(np.nansum(Y[mm])) if mm.any() else 0.0))
        ind = S.icodes
        for gcode in range(S.G):
            mm = kept_loser & (ind == gcode)
            if mm.any():
                byrows.append(dict(segment=A.segment, strategy=nm, dim='industry', key=int(gcode),
                                   n=int(mm.sum()), sum_fwd5_bp=float(np.nansum(Y[mm]))))
    pd.DataFrame(byrows).to_csv(
        os.path.join(out, 'T0_remaining_loss_%s_%s.csv' % (A.keyset, A.segment)), index=False)

    # ---- 128 条伪输家路径 ----
    real = have & flags['loser_q20']
    nper = real.sum(axis=1).astype(int)
    pathrows = []
    for mode in ('same_count', 'industry_matched'):
        stat = []
        for b in range(A.npath):
            fake = np.zeros_like(real)
            rr = np.random.default_rng(7000 + b)
            for t in range(S.T):
                v = np.flatnonzero(have[t])
                if len(v) == 0 or nper[t] == 0:
                    continue
                if mode == 'same_count':
                    fake[t, rr.choice(v, size=min(nper[t], len(v)), replace=False)] = True
                else:
                    ic = S.icodes[t, v]
                    rv = np.flatnonzero(real[t])
                    rc = S.icodes[t, rv] if len(rv) else np.empty(0, int)
                    rc = rc[rc >= 0]            # icodes = -1 是"行业未知", 不能进 bincount
                    want = (np.bincount(rc, minlength=S.G) if len(rc)
                            else np.zeros(S.G, int))
                    for gc in np.flatnonzero(want):
                        pool = v[ic == gc]
                        if len(pool):
                            fake[t, rr.choice(pool, size=min(int(want[gc]), len(pool)),
                                              replace=False)] = True
            row = dict(mean_fwd5=float(np.nanmean(Y[fake])) if fake.any() else np.nan)
            for kk in list(P)[:12]:
                m2 = fake & np.isfinite(P[kk])
                row['pct_' + kk] = float(np.nanmean(P[kk][m2])) if m2.any() else np.nan
            stat.append(row)
        arr = {k2: np.array([x[k2] for x in stat], float) for k2 in stat[0]}
        r = dict(segment=A.segment, keyset=A.keyset, mode=mode, n_path=A.npath)
        for k2, v in arr.items():
            r[k2 + '_mean'] = float(np.nanmean(v))
            r[k2 + '_sd'] = float(np.nanstd(v, ddof=1))
            r[k2 + '_mcse'] = float(np.nanstd(v, ddof=1) / np.sqrt(len(v)))
        # 真实输家的同名统计, 便于并排
        r['real_mean_fwd5'] = float(np.nanmean(Y[real]))
        for kk in list(P)[:12]:
            m2 = real & np.isfinite(P[kk])
            r['real_pct_' + kk] = float(np.nanmean(P[kk][m2])) if m2.any() else np.nan
        pathrows.append(r)
        print('  伪路径 %s 完成 %.0fs' % (mode, time.time() - t0), flush=True)
    pd.DataFrame(pathrows).to_csv(
        os.path.join(out, 'T0_pseudo_%s_%s.csv' % (A.keyset, A.segment)), index=False)

    json.dump(dict(counts=counts, n_keys=len(P), keyset=A.keyset, segment=A.segment,
                   label_note='主标签 = 源版日超额累加; fwd5_compound 为端点复利对照',
                   label_bench='base_pool 等权 (不是 pool0, 也不是引擎的 clean)',
                   elapsed_s=round(time.time() - t0, 1)),
              open(os.path.join(out, 'T0_counts_%s_%s.json' % (A.keyset, A.segment)), 'w'),
              indent=1, ensure_ascii=False)
    json.dump(dict(block='T0', keyset=A.keyset, segment=A.segment,
                   elapsed_s=round(time.time() - t0, 1)),
              open(os.path.join(G.RES, 'task_status',
                                'DONE_T0_%s_%s.json' % (A.keyset, A.segment)), 'w'), indent=1)
    print('DONE T0 %s %s  %.0fs' % (A.keyset, A.segment, time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
