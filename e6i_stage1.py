#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 1 测量级诊断 (brief §4 / plan §6.1-6.2)。只在推导段; 新对象不进 2019+。
不是 IC 排行榜: 同一成员在六集合 x 四层上逐项报告, 均值与中位并报, 每个量标算子与 n。
**无任何准入门** —— 这里算出的 ρ / 单调 / 收益一律不删成员、不改方向 (brief §0.2 / §16)。

部件 (--part):
  first   首表 (W01): pool0 内真实 cr5 (源 / 复权)、o / c / (h-l)、近 5 日触板天数、事件日龄 —— 全分布与逐年
  diag    六集合 x 四层: 测量层 (覆盖 / 平局 / 排名稳定 / 中性化前后形态) + 预测层 (形成日 Spearman,
          3/5 分组均值, 尾部, P(y<0)) x 标签 {src5, entry_1/3/5/10/20} + 决策层 (同预算换入 - 换出)
          + 事件层 (日龄 1-5 分层)
  t0      T0 画像 (Q18): 主体 = 被错剔赢家 (econ_reject ∩ src5>0), 参照 = 被剔输家 (econ_reject ∩ src5<0);
          pct 差 + 标签随机置换对照 + 按真实漂移 / 触板分层
  margin  C3 signal_margin_profile: 固定 pool0 内按触发日三分位距边界的距离、事件日龄 -> 后续收益分布

用法: python3 e6i_stage1.py --part diag --segment 2015-2018 --axes T
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
from pool_screening_v2 import define_i11_signal
from event_study import get_base_pool

OUTD = os.path.join(I.RES, 'measurements')
LABS = ('src5', 'entry_1', 'entry_3', 'entry_5', 'entry_10', 'entry_20')
LAG_OF = {'src5': 5, 'entry_1': 1, 'entry_3': 3, 'entry_5': 5, 'entry_10': 10, 'entry_20': 20}


def qd(x, ps=(0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if not len(x):
        return {}
    d = {'p%02d' % int(p * 100): float(np.quantile(x, p)) for p in ps}
    d.update(mean=float(x.mean()), frac_pos=float((x > 0).mean()), n=int(len(x)))
    return d


def trigger_age(S):
    """pool0 各格的触发日龄 (= t - 最近一次 <= t-1 的源触发), 近 5 日触发次数, 入池 spell 日龄。"""
    sig = define_i11_signal(S.feats, get_base_pool(S.data))
    tr = sig.reindex(index=S.pool0.index, columns=S.pool0.columns).fillna(0).values[:, S.ccols] == 1
    T, N = tr.shape
    last = np.full(N, -10 ** 6)
    age = np.full((T, N), np.nan)
    ntr5 = np.zeros((T, N))
    for t in range(T):
        age[t] = np.where(last >= 0, t - last, np.nan)
        lo = max(0, t - 5)
        ntr5[t] = tr[lo:t].sum(0)
        last = np.where(tr[t], t, last)
    spell = np.zeros((T, N))
    p0 = S.p0c
    for t in range(T):
        spell[t] = np.where(p0[t], (spell[t - 1] + 1) if t else 1, 0)
    return tr, age, ntr5, spell


# ------------------------------------------------------------------ first
def part_first(S):
    d = S.data
    idx, cols = S.pool0.index, S.pool0.columns
    g = lambda k: d[k].reindex(index=idx, columns=cols).astype(float).values[:, S.ccols]
    O, Hh, L, Cc, LC = g('open'), g('high'), g('low'), g('close'), g('lclose')
    with np.errstate(all='ignore'):
        o, c, hl = np.log(O / LC), np.log(Cc / O), np.log(Hh / L)
    cr5_src = I.to_grid(S, S.feats['cum_return_5d'])
    cr5_adj, _ = I.load_member(S.name, 'R_5_s0', 'OBS', where='first_table')
    lu = d['limit_up'].reindex(index=idx, columns=cols).astype(float).values[:, S.ccols]
    ld = d['limit_down'].reindex(index=idx, columns=cols).astype(float).values[:, S.ccols]
    touch = (np.isfinite(lu) & np.isfinite(ld) & ((Hh >= lu - 0.005) | (L <= ld + 0.005)))
    t5 = pd.DataFrame(touch.astype(float)).rolling(5, min_periods=1).sum().values
    tr, age, ntr5, spell = trigger_age(S)
    p0 = S.p0c
    yrs = pd.DatetimeIndex(S.dates).year.values
    rows = []
    items = [('cr5_source_unadjusted_simple', cr5_src), ('cr5_adjusted_log', cr5_adj),
             ('overnight_o', o), ('intraday_c', c), ('range_log_h_minus_l', hl),
             ('limit_touch_days_last5', t5), ('trigger_age', age),
             ('triggers_in_prev5', ntr5), ('pool_spell_age', spell)]
    for name, A in items:
        for yr in ['all'] + sorted(set(yrs.tolist())):
            m = p0 if yr == 'all' else (p0 & (yrs == yr)[:, None])
            rows.append(dict(segment=S.name, quantity=name, year=yr, **qd(A[m])))
    df = pd.DataFrame(rows)
    I.atomic_write_csv(os.path.join(OUTD, 'first_table_%s.csv' % S.name), df)
    a = df[df.year == 'all'].set_index('quantity')
    print(a[['p05', 'p25', 'p50', 'p75', 'p95', 'mean', 'frac_pos', 'n']].round(4).to_string())


# ------------------------------------------------------------------ diag
def part_diag(S, axes):
    FE.build_catalog()
    mems = [m for m in FE.CATALOG if m['axis_id'] in axes]
    I.guard_i([m['member_id'] for m in mems], segment=S.name, use='label',
              label_end=str(S.dates[-1].date()), where='stage1_diag')
    L = SB.labels(S)
    Ps = {mn: RR.ParentCtx(S, mn) for mn in I.MOTHERS}
    sets = {'pool0': {'__all__': S.p0c}}
    for mn, P in Ps.items():
        sets[mn] = SB.sets_for_mother(S, P)
    # 标签在每个集合内的秩 (所有成员共用)
    ylab = {}
    for mn, ss in sets.items():
        for sn, mask in ss.items():
            for lb in LABS:
                ylab[(mn, sn, lb)] = SB.row_rank(L[lb], mask)
    tr, age, ntr5, spell = trigger_age(S)
    rows, mrows = [], []
    t0 = time.time()
    for i, m in enumerate(mems):
        mid = m['member_id']
        raw = SB.raw_member(S, mid)
        pct = SB.pct_member(S, mid, direction='hi')
        p0 = S.p0c
        # ---- 测量层 ----
        fin = np.isfinite(raw) & p0
        tie = []
        for t in range(0, S.T, 5):
            v = raw[t][fin[t]]
            if len(v) > 5:
                tie.append(1.0 - len(np.unique(v)) / len(v))
        pr = SB.row_rank(raw, p0)
        ac1 = np.nanmean(SB.row_spearman(pr[1:], pr[:-1], 20))
        ac5 = np.nanmean(SB.row_spearman(pr[5:], pr[:-5], 20))
        neu = np.nanmean(SB.row_spearman(pr, SB.row_rank(pct, p0), 20))
        mrows.append(dict(segment=S.name, member_id=mid, axis=m['axis_id'],
                          family=m['family_id'], source_class=m['source_class'],
                          cov_pool0=float(fin[p0].mean()) if p0.any() else np.nan,
                          tie_frac=float(np.mean(tie)) if tie else np.nan,
                          rank_autocorr_lag1=float(ac1), rank_autocorr_lag5=float(ac5),
                          raw_vs_ns_spearman=float(neu),
                          raw_p01=float(np.nanquantile(raw[fin], 0.01)) if fin.any() else np.nan,
                          raw_p50=float(np.nanquantile(raw[fin], 0.5)) if fin.any() else np.nan,
                          raw_p99=float(np.nanquantile(raw[fin], 0.99)) if fin.any() else np.nan))
        # ---- 预测层 / 事件层 ----
        for mn, ss in sets.items():
            for sn, mask in ss.items():
                xr = SB.row_rank(pct, mask)
                nday = np.isfinite(xr).sum(1)
                for lb in LABS:
                    yr_ = ylab[(mn, sn, lb)]
                    ic = SB.row_spearman(xr, yr_)
                    y = np.where(mask, L[lb], np.nan)
                    g5 = SB.group_means(xr, y, 5)
                    g3 = SB.group_means(xr, y, 3)
                    g10 = SB.group_means(xr, y, 10)
                    neg5 = SB.group_means(xr, np.where(np.isfinite(y), (y < 0).astype(float),
                                                       np.nan), 5)
                    with np.errstate(all='ignore'):
                        rec = dict(segment=S.name, member_id=mid, axis=m['axis_id'],
                                   mother=mn, set=sn, label=lb,
                                   n_days=int(np.isfinite(ic).sum()),
                                   n_per_day_mean=float(np.nanmean(np.where(nday > 0, nday,
                                                                            np.nan))),
                                   ic_mean=float(np.nanmean(ic)), ic_median=float(np.nanmedian(ic)),
                                   ic_nw_t=SB.nw_t(ic, LAG_OF[lb]),
                                   ic_pos_frac=float(np.nanmean(ic > 0)) if np.isfinite(ic).any()
                                   else np.nan,
                                   **{'g5_%d' % (k + 1): float(np.nanmean(g5[:, k])) for k in range(5)},
                                   **{'g3_%d' % (k + 1): float(np.nanmean(g3[:, k])) for k in range(3)},
                                   tail_top10_minus_bottom10=float(np.nanmean(g10[:, 9] - g10[:, 0])),
                                   p_neg_g1=float(np.nanmean(neg5[:, 0])),
                                   p_neg_g5=float(np.nanmean(neg5[:, 4])),
                                   g5_spread_5m1_median_day=float(np.nanmedian(g5[:, 4] - g5[:, 0])))
                    rec['u_shape_index'] = (rec['g5_1'] + rec['g5_5']) / 2 - rec['g5_3']
                    rows.append(rec)
                # 事件层: pool0 按日龄
                if mn == 'pool0':
                    for a_ in (1, 2, 3, 4, 5):
                        am = mask & (age == a_)
                        xa = SB.row_rank(pct, am)
                        ya = SB.row_rank(L['src5'], am)
                        ic = SB.row_spearman(xa, ya)
                        rows.append(dict(segment=S.name, member_id=mid, axis=m['axis_id'],
                                         mother='pool0', set='age%d' % a_, label='src5',
                                         n_days=int(np.isfinite(ic).sum()),
                                         ic_mean=float(np.nanmean(ic)),
                                         ic_nw_t=SB.nw_t(ic, 5)))
        # ---- 决策层: 同预算换入 (econ_reject 中按成员两端各取 m) - 换出 (final 中母体核分最差 m) ----
        for mn, P in Ps.items():
            ss = sets[mn]
            dlt_lo, dlt_hi = [], []
            for t in range(S.T):
                b = np.where(ss['final'][t] & np.isfinite(P.score[t]))[0]
                e = np.where(ss['econ_reject'][t] & np.isfinite(pct[t]) &
                             np.isfinite(L['src5'][t]))[0]
                if len(b) < 5 or len(e) < 5:
                    continue
                mm = max(1, int(np.floor(0.1 * len(b))))
                out_ = b[np.argsort(-P.score[t][b], kind='stable')[:mm]]
                yo = np.nanmean(L['src5'][t][out_])
                srt = e[np.argsort(pct[t][e], kind='stable')]
                dlt_lo.append(np.nanmean(L['src5'][t][srt[:mm]]) - yo)     # 成员低值端换入
                dlt_hi.append(np.nanmean(L['src5'][t][srt[-mm:]]) - yo)    # 成员高值端换入
            for side, v in (('member_low_in', dlt_lo), ('member_high_in', dlt_hi)):
                v = np.asarray(v, float)
                rows.append(dict(segment=S.name, member_id=mid, axis=m['axis_id'], mother=mn,
                                 set='decision_swap10pct', label='src5_bp', side=side,
                                 n_days=int(np.isfinite(v).sum()),
                                 swap_in_minus_out_mean=float(np.nanmean(v)),
                                 swap_in_minus_out_median=float(np.nanmedian(v)),
                                 swap_nw_t=SB.nw_t(v, 5)))
        if (i + 1) % 5 == 0:
            print('  %d/%d  %.0fs' % (i + 1, len(mems), time.time() - t0), flush=True)
    tag = ''.join(sorted(axes))
    I.atomic_write_csv(os.path.join(OUTD, 'diag_%s_%s.csv' % (S.name, tag)), pd.DataFrame(rows))
    I.atomic_write_csv(os.path.join(OUTD, 'measure_layer_%s_%s.csv' % (S.name, tag)),
                       pd.DataFrame(mrows))
    print('[%s %s] diag %d 行, 测量层 %d 行, %.0fs' % (S.name, tag, len(rows), len(mrows),
                                                   time.time() - t0))


# ------------------------------------------------------------------ t0
def part_t0(S, axes, n_perm=50):
    FE.build_catalog()
    mems = [m for m in FE.CATALOG if m['axis_id'] in axes]
    I.guard_i([m['member_id'] for m in mems], segment=S.name, use='label',
              label_end=str(S.dates[-1].date()), where='stage1_t0')
    L = SB.labels(S)
    y = L['src5']
    Ps = {mn: RR.ParentCtx(S, mn) for mn in I.MOTHERS}
    cr5 = I.to_grid(S, S.feats['cum_return_5d'])
    d = S.data
    idx, cols = S.pool0.index, S.pool0.columns
    g = lambda k: d[k].reindex(index=idx, columns=cols).astype(float).values[:, S.ccols]
    Hh, Lw = g('high'), g('low')
    lu, ld = g('limit_up'), g('limit_down')
    touch = np.isfinite(lu) & np.isfinite(ld) & ((Hh >= lu - 0.005) | (Lw <= ld + 0.005))
    t5 = pd.DataFrame(touch.astype(float)).rolling(5, min_periods=1).sum().values
    rng = np.random.default_rng(20260923)
    rows = []

    def wl_diff(win, los, pct):
        with np.errstate(all='ignore'):
            nw, nl = win.sum(1), los.sum(1)
            dw = np.where(nw >= 3, np.where(win, pct, 0.0).sum(1) / nw, np.nan)
            dl = np.where(nl >= 3, np.where(los, pct, 0.0).sum(1) / nl, np.nan)
        return dw - dl

    for mn, P in Ps.items():
        D = P.D.astype(bool) & S.p0c & np.isfinite(y)
        # 真实漂移分层: 当日 D 内 cr5 三分位
        crk = SB.row_rank(cr5, D)
        strata = {'all': D, 'drift_low': D & (crk <= 1 / 3), 'drift_mid': D & (crk > 1 / 3) & (crk <= 2 / 3),
                  'drift_high': D & (crk > 2 / 3), 'touch0': D & (t5 == 0), 'touch1p': D & (t5 >= 1)}
        # 置换对照: 当日 D 内打乱标签, 每个置换一次生成、全部成员共用 (plan §6.3 局部随机)
        perms = []
        for _ in range(n_perm):
            ys = np.where(D, y, np.nan)
            for t in range(S.T):
                v = np.where(D[t])[0]
                if len(v) > 1:
                    ys[t, v] = ys[t, v][rng.permutation(len(v))]
            perms.append((ys > 0, ys < 0))
        for m in mems:
            pct = SB.pct_member(S, m['member_id'], direction='hi')
            fp = np.isfinite(pct)
            for sname, sm in strata.items():
                diff = wl_diff(sm & (y > 0) & fp, sm & (y < 0) & fp, pct)
                perm = []
                if sname == 'all':
                    for pw, pl in perms:
                        perm.append(np.nanmean(wl_diff(D & pw & fp, D & pl & fp, pct)))
                rows.append(dict(segment=S.name, mother=mn, member_id=m['member_id'],
                                 axis=m['axis_id'], stratum=sname,
                                 subject_set='econ_reject ∩ src5>0 (被错剔赢家)',
                                 reference_set='econ_reject ∩ src5<0 (被剔输家)',
                                 label_definition='src5 = compute_forward_5d_excess (日龄线性, bp)',
                                 weights='形成日内等权, 日期等权', dates='%s..%s' % (
                                     S.dates[0].date(), S.dates[-1].date()),
                                 pct_diff_winner_minus_loser=float(np.nanmean(diff)),
                                 pct_diff_nw_t=SB.nw_t(diff, 5),
                                 n_days=int(np.isfinite(diff).sum()),
                                 perm_mean=float(np.mean(perm)) if perm else np.nan,
                                 perm_sd=float(np.std(perm, ddof=1)) if len(perm) > 1 else np.nan))
        print('  t0 %s done' % mn, flush=True)
    tag = ''.join(sorted(axes))
    I.atomic_write_csv(os.path.join(OUTD, 't0_portrait_%s_%s.csv' % (S.name, tag)),
                       pd.DataFrame(rows))


# ------------------------------------------------------------------ margin (C3)
def part_margin(S):
    feats = S.feats
    bp = get_base_pool(S.data).reindex(index=S.pool0.index, columns=S.pool0.columns).fillna(0)
    mask = bp == 1

    def pip(name):
        f = feats[name].reindex_like(bp).where(mask)
        return f.rank(axis=1, pct=True).values[:, S.ccols]
    cmf, cr5p, irp = pip('CMF_20d'), pip('cum_return_5d'), pip('intraday_ret')
    tr, age, ntr5, spell = trigger_age(S)
    T, N = tr.shape
    # pool0 格的最近一次触发日行号
    last = np.full(N, -1)
    tau = np.full((T, N), -1)
    for t in range(T):
        tau[t] = last
        last = np.where(tr[t], t, last)
    L = SB.labels(S)
    y = L['src5']
    cr5 = I.to_grid(S, feats['cum_return_5d'])
    p0 = S.p0c & (tau >= 0)
    cols = np.arange(N)[None, :].repeat(T, 0)
    ti = np.where(tau >= 0, tau, 0)
    m_cmf = cmf[ti, cols] - 0.80
    m_cr5 = np.minimum(cr5p[ti, cols] - 0.25, 0.55 - cr5p[ti, cols])
    m_ir = 0.70 - irp[ti, cols]
    rows = []
    for name, M in (('cmf_margin', m_cmf), ('cr5_band_margin', m_cr5), ('intraday_margin', m_ir)):
        v = M[p0]
        yy = y[p0]
        ok = np.isfinite(v) & np.isfinite(yy)
        if ok.sum() < 100:
            continue
        q = pd.qcut(pd.Series(v[ok]).rank(method='first'), 5, labels=False)
        for k in range(5):
            s = yy[ok][q.values == k]
            vv = v[ok][q.values == k]
            rows.append(dict(segment=S.name, margin=name, quintile=k + 1,
                             margin_lo=float(vv.min()), margin_hi=float(vv.max()),
                             n=int(len(s)), src5_mean_bp=float(s.mean()),
                             src5_median_bp=float(np.median(s)), p_neg=float((s < 0).mean()),
                             p10=float(np.quantile(s, 0.1)), p90=float(np.quantile(s, 0.9))))
    for a_ in (1, 2, 3, 4, 5):
        s = y[p0 & (age == a_)]
        s = s[np.isfinite(s)]
        rows.append(dict(segment=S.name, margin='trigger_age', quintile=a_, n=int(len(s)),
                         src5_mean_bp=float(s.mean()), src5_median_bp=float(np.median(s)),
                         p_neg=float((s < 0).mean())))
    rv = cr5[p0]
    yy = y[p0]
    ok = np.isfinite(rv) & np.isfinite(yy)
    q = pd.qcut(pd.Series(rv[ok]).rank(method='first'), 5, labels=False)
    for k in range(5):
        s = yy[ok][q.values == k]
        vv = rv[ok][q.values == k]
        rows.append(dict(segment=S.name, margin='realized_cr5_at_t', quintile=k + 1,
                         margin_lo=float(vv.min()), margin_hi=float(vv.max()), n=int(len(s)),
                         src5_mean_bp=float(s.mean()), src5_median_bp=float(np.median(s)),
                         p_neg=float((s < 0).mean())))
    I.atomic_write_csv(os.path.join(OUTD, 'signal_margin_profile_%s.csv' % S.name),
                       pd.DataFrame(rows))
    print(pd.DataFrame(rows)[['margin', 'quintile', 'n', 'src5_mean_bp', 'p_neg']].round(3)
          .to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--part', required=True, choices=['first', 'diag', 't0', 'margin'])
    ap.add_argument('--segment', required=True)
    ap.add_argument('--axes', default='T,K,V,R,O,C,A,S')
    a = ap.parse_args()
    assert a.segment in I.DERIV_SEGS
    FE.build_catalog()
    I.set_protected_members(FE.protected_ids())
    os.makedirs(OUTD, exist_ok=True)
    S = I.seg_i(a.segment, warm=False)
    axes = set(a.axes.split(','))
    if a.part == 'first':
        part_first(S)
    elif a.part == 'diag':
        part_diag(S, axes)
    elif a.part == 't0':
        part_t0(S, axes)
    else:
        part_margin(S)


if __name__ == '__main__':
    main()
