# -*- coding: utf-8 -*-
"""E6n B4：全 A 域与 I11 条件性（plan §9.2；brief §1.3-13；卡 H14）。读收益（标签）：推导段 deriv_ready、后段 post_gate。
五个源量 cond / tvol / CVR20 / cr20（源 C.get_default_factor_specs 原日线定义，全部股票）与 Q0（1/(|log(C/lclose)| + 1e−4)，源有效性）在
clean、pool0、clean∖pool0 三域：逐日 Spearman IC、五分组低 − 高（同域当日超额）、H1 / 3 / 5 / 10 / 20（E6m B3 CLEAN 事件 FWD_SOURCE / ENDPOINT / LINEAR）。
  桥 A：在 clean 上做源 size 中性化（precompute_neutralized_factor，池 = clean）后取子域；桥 B：各域独立中性化（池 = 该域）。两种坐标的 IC 不相除。
  非 I11 匹配对照：同日同一级行业内，pool0 格与 clean∖pool0 格按 (log 市值, log 过去 20 日成交额) L1 标准化距离无放回配对（linear_sum_assignment），
  比较匹配非 I11 样本与其配对 pool0 样本的同一统计；报告重叠支持份额。不用未来入池状态配对；不把 pool0 叫 clean。
输出 results/<phase>/b4/b4_bridges_<段>.csv、b4_matched_non_i11_<段>.csv。"""
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6n_core as N

E6M_W = N.E6M_WORK
FACTORS = ('conditional_turnover', 'turnover_volatility_60d', 'CVR_20d', 'cum_return_20d', 'Q0')


def run(seg_name):
    import e6l_env as V
    import comprehensive_factor_diagnosis as C
    import e6n_b1_0 as B10
    from scipy.optimize import linear_sum_assignment
    t0 = time.time()
    seg = V.SegL(seg_name, state=False)
    ctx = seg.ctx
    data, feats, ind = ctx['data'], ctx['feats'], ctx['industry']
    pool0 = ctx['pool0']
    idx, cols = pool0.index, pool0.columns
    clean = ctx['clean'].reindex(index=idx, columns=cols).fillna(0.0) == 1
    p0 = pd.DataFrame(ctx['p0'], index=idx, columns=cols)
    lmc = ctx['log_mcap'].reindex(index=idx, columns=cols)
    specs = ctx['specs']
    raws = {}
    for f in FACTORS[:4]:
        raws[f] = specs[f]['func'](data, feats, ind).reindex(index=idx, columns=cols).astype(float)
    g = lambda k: data[k].reindex(index=idx, columns=cols).astype(float)
    is_open = data['is_open'].reindex(index=idx, columns=cols) == 1
    o_, h_, l_, c_, lc_ = g('open'), g('high'), g('low'), g('close'), g('lclose')
    with np.errstate(all='ignore'):
        valid = is_open & (o_ > 0) & (h_ > 0) & (l_ > 0) & (c_ > 0) & (lc_ > 0)
        valid &= (l_ <= np.minimum(o_, c_) + 1e-9) & (h_ >= np.maximum(o_, c_) - 1e-9)
        dq = np.abs(np.log(c_ / lc_)).where(valid)
    raws['Q0'] = 1.0 / (dq + 1e-4)
    amt = data['amount'].reindex(index=idx, columns=cols).astype(float)
    am20 = np.log(amt.where(amt > 0).rolling(20, min_periods=1).mean())
    indv = ind.reindex(index=idx, columns=cols).to_numpy(float) if ind is not None else np.full(clean.shape, np.nan)
    # 标签：E6m CLEAN 事件（clean 基准；域内差 / IC 与基准无关）
    ev = np.load(os.path.join(E6M_W, 'stageN', 'B3_prelim', 'work', 'events_%s__CLEAN.npz' % seg_name), allow_pickle=False)
    ed = [str(x) for x in ev['dates']]
    dpos = {pd.Timestamp(d).strftime('%Y-%m-%d'): i for i, d in enumerate(idx)}
    cpos = {int(str(c).split('.')[0]): j for j, c in enumerate(cols)}
    T, Nn = clean.shape
    ycols = [str(x) for x in ev['ycols']]
    Y = np.full((len(ycols), T, Nn), np.nan)
    ti = np.array([dpos.get(ed[t], -1) for t in ev['t']])
    cj = np.array([cpos.get(int(k), -1) for k in ev['tick']])
    ok = (ti >= 0) & (cj >= 0)
    for j in range(len(ycols)):
        Y[j, ti[ok], cj[ok]] = ev['Y'][ok, j]
    doms = {'CLEAN': clean.to_numpy(), 'POOL0': p0.to_numpy() & clean.to_numpy(), 'CLEAN_MINUS_POOL0': clean.to_numpy() & ~p0.to_numpy()}
    rows = []

    def stats(x, dom, tag_bridge, fname):
        tt, cc = np.nonzero(dom & np.isfinite(x))
        for j, col in enumerate(ycols):
            lab, hh = col.rsplit('_h', 1)
            y = Y[j, tt, cc]
            fin = np.isfinite(y)
            ics = B10.daily_spearman(tt[fin], x[tt[fin], cc[fin]], y[fin])
            q = B10.terc_mid_groups(x[tt, cc], tt)                      # 三分（中分布）
            days, M, Nm, dm = B10.day_stats(tt, q, y)
            dd = M[:, 0] - M[:, 2]
            okd = np.isfinite(dd)
            rows.append(dict(segment=seg_name, factor=fname, bridge=tag_bridge, label=lab, H=int(hh), stat='rank_ic_mean', value=float(np.mean(ics)) if len(ics) else np.nan,
                             unit='decimal', n_days=int(len(ics)), status='COMPUTED' if len(ics) else 'NOT_COMPUTABLE'))
            rows.append(dict(segment=seg_name, factor=fname, bridge=tag_bridge, label=lab, H=int(hh), stat='tercile_low_minus_high_bp',
                             value=float(dd[okd].mean()) if okd.any() else np.nan, unit='bp', n_days=int(okd.sum()), status='COMPUTED' if okd.any() else 'NOT_COMPUTABLE'))
    for fname in FACTORS:
        F = raws[fname]
        # 桥 A：clean 上中性化后取子域
        neuA = C.precompute_neutralized_factor(F, clean.astype(float), lmc)
        XA = np.full((T, Nn), np.nan)
        for d, s in neuA.items():
            XA[dpos[pd.Timestamp(d).strftime('%Y-%m-%d')], [cols.get_loc(c) for c in s.index]] = s.to_numpy(float)
        for dn, dm_ in doms.items():
            stats(XA, dm_, 'A_CLEAN_ESTIMATED|' + dn, fname)
            # 桥 B：各域独立中性化
            neuB = C.precompute_neutralized_factor(F, pd.DataFrame(dm_.astype(float), index=idx, columns=cols), lmc)
            XB = np.full((T, Nn), np.nan)
            for d, s in neuB.items():
                XB[dpos[pd.Timestamp(d).strftime('%Y-%m-%d')], [cols.get_loc(c) for c in s.index]] = s.to_numpy(float)
            stats(XB, dm_, 'B_DOMAIN_ESTIMATED|' + dn, fname)
        N.log('B4 %s %s（%.0f s）' % (seg_name, fname, time.time() - t0))
    # 非 I11 匹配对照
    lm = lmc.to_numpy(float)
    am = am20.to_numpy(float)
    pairs_p, pairs_n = [], []
    cov_n, cov_d = 0, 0
    for t in range(T):
        P_ = np.flatnonzero(doms['POOL0'][t] & np.isfinite(lm[t]) & np.isfinite(am[t]))
        Q_ = np.flatnonzero(doms['CLEAN_MINUS_POOL0'][t] & np.isfinite(lm[t]) & np.isfinite(am[t]))
        cov_d += len(P_)
        if not len(P_) or not len(Q_):
            continue
        X = np.column_stack([lm[t], am[t]])
        sc = np.array([np.subtract(*np.percentile(X[np.r_[P_, Q_], k], [75, 25])) for k in range(2)])
        sc = np.where(sc > 0, sc, 1.0)
        for iv in np.unique(indv[t, P_][np.isfinite(indv[t, P_])]):
            a = P_[indv[t, P_] == iv]
            b = Q_[indv[t, Q_] == iv]
            if not len(a) or not len(b):
                continue
            Dm = (np.abs(X[a][:, None, :] - X[b][None, :, :]) / sc[None, None, :]).sum(-1)
            r, c = linear_sum_assignment(Dm)
            pairs_p += [(t, x) for x in a[r]]
            pairs_n += [(t, x) for x in b[c]]
            cov_n += len(r)
    mrows = []
    if pairs_p:
        pp = np.array(pairs_p)
        pn = np.array(pairs_n)
        mp = np.zeros((T, Nn), bool)
        mn = np.zeros((T, Nn), bool)
        mp[pp[:, 0], pp[:, 1]] = True
        mn[pn[:, 0], pn[:, 1]] = True
        for fname in FACTORS:
            F = raws[fname]
            neuA = C.precompute_neutralized_factor(F, clean.astype(float), lmc)
            XA = np.full((T, Nn), np.nan)
            for d, s in neuA.items():
                XA[dpos[pd.Timestamp(d).strftime('%Y-%m-%d')], [cols.get_loc(c) for c in s.index]] = s.to_numpy(float)
            for nm, msk in (('POOL0_MATCHED', mp), ('NON_I11_MATCHED', mn)):
                j = ycols.index('FWD_SOURCE_h5')
                tt, cc = np.nonzero(msk & np.isfinite(XA))
                y = Y[j, tt, cc]
                fin = np.isfinite(y)
                ics = B10.daily_spearman(tt[fin], XA[tt[fin], cc[fin]], y[fin])
                mrows.append(dict(segment=seg_name, factor=fname, sample=nm, label='FWD_SOURCE', H=5, stat='rank_ic_mean', value=float(np.mean(ics)) if len(ics) else np.nan,
                                  unit='decimal', n_days=int(len(ics)), n_pairs=int(len(pp)), overlap_support_share_decimal=cov_n / max(1, cov_d),
                                  status='COMPUTED' if len(ics) else 'NOT_COMPUTABLE'))
    od = N.P('results', 'deriv' if seg_name in N.DERIV_SEGS else 'full', 'b4')
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, 'b4_bridges_%s.csv' % seg_name)
    p2 = os.path.join(od, 'b4_matched_non_i11_%s.csv' % seg_name)
    N.atomic_write_csv(p1, N.to_status(pd.DataFrame(rows)))
    N.atomic_write_csv(p2, N.to_status(pd.DataFrame(mrows)) if mrows else pd.DataFrame([dict(segment=seg_name, status='NOT_COMPUTABLE')]))
    return [p1, p2], time.time() - t0


def main():
    import e6n_gate as GT
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    a = ap.parse_args()
    GT.deriv_ready(a.seg, 'B4 %s' % a.seg)
    outs, wall = run(a.seg)
    N.write_receipt('E6n_b4_%s' % a.seg, outs, code=[__file__], wall_s=round(wall, 1))
    print(json.dumps(dict(seg=a.seg, wall_s=round(wall, 1)), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
