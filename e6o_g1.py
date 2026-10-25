# -*- coding: utf-8 -*-
"""E6o G1 第一道 probe（plan §9 下半；brief §4 A2）：只在推导段（2010-2014、2015-2018；批次原 due < 2019-01-01，前向窗口不跨入后段）。
风险集 = 主母体（A4b_CVRv5 / Q0 α .25 / H5）三记忆的无退出影子批次（源形成名单：入场执行 e0 = f + 1、原 due = e0 + 5）；
每批次每个收盘决策日 d ∈ [e0, due − 2]（R_INTENT），记各触发的首次触发事件（批次级去重，同 B2）。
前向：卖在 VWAP_{d+1} → 剩余超额 rem_due = Σ_{t=d+2}^{due}(r_vwap − bench)；独立窗口 H1 / H3 / H5 = t ∈ [d+2, d+2+k−1]。
比较：同日同日龄全部风险集批次均值（同日对照）、同日同日龄按当日日 CVR 位置最差取同数（水平对照）。
单位：资产 bp（每事件）；组合资本贡献 ann_pp = Σ(w/H · rem) / 段日数 × 252 × 100（固定名义、等价 CASH 去持有的符号相反）。
分层：日龄 / 池内外（d 日是否在 pool0）/ 入场日 CVR 三分 / 当日日 CVR 位置三分 / 行业状态（X1 名次 ≤ .2 / ≥ .8 / 中间）。
输出 diagnostics/G1_E6o.csv（附录 B.16 长格式）。看过 G1 想到的新解释只写 G 账本新行，不改主程序（plan §9）。"""
import os
import sys
import json
import time

import numpy as np
import pandas as pd

import e6o_core as O
import e6o_acct as A

TRIGS_PANEL = ('T1a', 'T1b', 'T1b_LEVEL', 'T1b_EDGE', 'T1b_OWNCHANGE', 'T3a15', 'T3b15', 'T3c15', 'T3a15_X', 'T3b15_X', 'T3c15_X', 'T3a15_XR', 'T3b15_XR',
               'T3c15_XR', 'T3a20', 'T3b20', 'T3c20', 'T3a20_X', 'T3b20_X', 'T3c20_X', 'T4a', 'T4b', 'T5')
TRIGS_LOT = ('T2', 'T2prime', 'T6a', 'T6b', 'T1c', 'T1d')


def main():
    t0 = time.time()
    mk = A.Market()
    T = mk.T
    d19 = int(np.searchsorted(mk.dates, '2019-01-01'))
    cd = mk.cd
    L = lambda k: np.load(os.path.join(cd, 'panels', k + '.npy'), mmap_mode='r')
    rv = np.asarray(L('r_vwap'))[:d19]
    bench = mk.bench[:d19]
    ex = np.where(np.isfinite(rv), rv - bench[:, None], 0.0)
    ex = np.where(np.isfinite(ex), ex, 0.0)
    cs = np.vstack([np.zeros((1, ex.shape[1])), np.cumsum(ex, axis=0)])        # cs[k] = Σ_{t<k}
    cvr = np.asarray(L('cvr1d'))[:d19]
    cpct = np.asarray(L('cvr_pct'))[:d19]
    pcobs = np.asarray(L('pc'))[:d19]
    pv = np.asarray(L('pv'))[:d19]
    sig = np.asarray(L('sig20'))[:d19]
    rank = np.asarray(L('ind_rank'))[:d19]
    pool0 = np.asarray(np.load(os.path.join(cd, 'triggers', 'pool0.npy'), mmap_mode='r'))[:d19]
    t1a = np.asarray(mk.t1a)[:d19]
    segi = np.array([O.seg_of_date(d) for d in mk.dates[:d19]])
    ndays = {s: int((segi == s).sum()) for s in O.DERIV_SEGS}
    rows = []
    H = 5
    for mem in O.MEMS:
        ptr, col, w = mk.formation(O.MAIN_FORM, mem)
        f = np.repeat(np.arange(T), np.diff(ptr))
        e0 = f + 1
        due = e0 + H
        ok = due < d19
        f, col, w, e0, due = f[ok], col[ok], w[ok], e0[ok], due[ok]
        nlot = len(f)
        # 批次 × 决策日
        ages = np.arange(H - 1)
        li = np.repeat(np.arange(nlot), len(ages))
        ag = np.tile(ages, nlot)
        d = e0[li] + ag
        keep = d + 1 < due[li]
        li, ag, d = li[keep], ag[keep], d[keep]
        c = col[li]
        rem = cs[due[li] + 1, c] - cs[d + 2, c]
        h = {}
        for k in (1, 3, 5):
            end = np.minimum(d + 2 + k, d19)
            v = cs[end, c] - cs[d + 2, c]
            h[k] = np.where(d + 2 + k <= d19, v, np.nan)
        key = d * 8 + ag                                   # 同日同日龄组
        grp = pd.DataFrame(dict(key=key, rem=rem, h1=h[1], h3=h[3], h5=h[5]))
        gm = grp.groupby('key').mean()
        base = gm.reindex(key).to_numpy()
        # 触发状态
        state = {}
        for tg in TRIGS_PANEL:
            P = np.asarray(mk.trig(tg))[:d19]
            state[tg] = P[d, c] == 1
        a0 = cvr[e0[li], c]
        b0 = cvr[d, c]
        with np.errstate(invalid='ignore'):
            t2 = np.isfinite(a0) & np.isfinite(b0) & ((b0 - a0) >= 0.01)
        state['T2'] = t2
        state['T2prime'] = t2 & (t1a[d, c] == 0)
        with np.errstate(invalid='ignore', divide='ignore'):
            loss = pcobs[d, c] / pv[e0[li], c] - 1.0
            sg = sig[e0[li], c]
        state['T6a'] = np.isfinite(loss) & (loss <= -0.05)
        state['T6b'] = np.isfinite(loss) & np.isfinite(sg) & (sg > 0) & (loss <= -2.0 * sg)
        # 持仓域分位（影子：d 收盘仍持有的唯一证券）
        held_rows = []
        for k in range(H):
            held_rows.append(np.stack([e0 + k, col], 1))
        hr = np.unique(np.vstack(held_rows), axis=0)
        hr = hr[hr[:, 0] < d19]
        hv = cvr[hr[:, 0], hr[:, 1]]
        okh = np.isfinite(hv)
        hdf = pd.DataFrame(dict(d=hr[okh, 0], c=hr[okh, 1], v=hv[okh]))
        hdf['r'] = hdf.groupby('d')['v'].rank(method='average', pct=False)
        hdf['n'] = hdf.groupby('d')['v'].transform('size')
        hdf['eq'] = hdf.groupby(['d', 'v'])['v'].transform('size')
        hdf['mid'] = (hdf['r'] - 0.5 * (hdf['eq'] + 1) + 0.5 * hdf['eq']) / hdf['n']   # (N_< + .5 N_=)/N
        mid = pd.Series(hdf['mid'].to_numpy(), index=hdf['d'].to_numpy() * 100000 + hdf['c'].to_numpy())
        mm = mid.reindex(d * 100000 + c).to_numpy()
        state['T1c'] = np.isfinite(mm) & (mm >= 0.8)
        state['T1d'] = np.isfinite(mm) & (mm >= 0.9)
        # 分层键
        inpool = pool0[d, c]
        q_e = pd.qcut(pd.Series(a0).rank(method='first'), 3, labels=False).to_numpy() if np.isfinite(a0).sum() > 3 else np.zeros(len(a0))
        q_e = np.where(np.isfinite(a0), q_e, -1)
        cp = cpct[d, c]
        q_c = np.where(np.isfinite(cp), np.minimum((cp * 3).astype(int), 2), -1)
        rk = rank[d, c]
        ind_st = np.where(~np.isfinite(rk), 'UNKNOWN', np.where(rk <= 0.2, 'LOW', np.where(rk >= 0.8, 'HIGH', 'MID')))
        seg = segi[d]
        wl = w[li] / H
        for tg, st in state.items():
            # 批次级首次触发
            idx = np.flatnonzero(st)
            if len(idx):
                first = pd.Series(idx).groupby(li[idx]).min().to_numpy()
            else:
                first = np.zeros(0, np.int64)
            ev = np.zeros(len(li), bool)
            ev[first] = True
            # 水平对照：同组按当日日 CVR 位置最差取同数
            lw = np.zeros(len(li), bool)
            if len(first):
                kk = pd.DataFrame(dict(key=key[first])).value_counts().reset_index()
                kk.columns = ['key', 'k']
                g2 = pd.DataFrame(dict(key=key, cp=np.where(np.isfinite(cp), cp, -1.0), i=np.arange(len(li))))
                g2 = g2[g2.key.isin(kk.key)].merge(kk, on='key')
                g2 = g2.sort_values(['key', 'cp'], ascending=[True, False])
                g2['r'] = g2.groupby('key').cumcount()
                lw[g2[g2.r < g2.k].i.to_numpy()] = True
            for s in O.DERIV_SEGS:
                for ktype, kval_arr in (('ALL', np.full(len(li), 'ALL')), ('AGE', ag.astype(str)), ('DOMAIN', np.where(inpool, 'IN_POOL0', 'OFF_POOL0')),
                                        ('ENTRY_CVR_T3', q_e.astype(str)), ('CUR_CVR_T3', q_c.astype(str)), ('IND_STATE', ind_st)):
                    for kv in np.unique(kval_arr):
                        m = ev & (seg == s) & (kval_arr == kv)
                        n = int(m.sum())
                        if ktype != 'ALL' and n < 30:
                            continue
                        mlw = lw & (seg == s) & (kval_arr == kv)
                        stats = dict(n_events=(n, 'count'))
                        if n:
                            stats['mean_rem_due_bp'] = (float(np.nanmean(rem[m]) * 1e4), 'bp')
                            stats['diff_vs_sameday_bp'] = (float(np.nanmean(rem[m] - base[m, 0]) * 1e4), 'bp')
                            stats['diff_vs_levelworst_bp'] = (float(np.nanmean(rem[m]) * 1e4 - np.nanmean(rem[mlw]) * 1e4) if mlw.any() else np.nan, 'bp')
                            for k_, col_ in ((1, 1), (3, 2), (5, 3)):
                                stats['h%d_diff_bp' % k_] = (float(np.nanmean(h[k_][m] - base[m, col_]) * 1e4), 'bp')
                            stats['contrib_ann_pp'] = (float(np.nansum(wl[m] * rem[m]) / ndays[s] * O.ANN_PP), 'ann_pp')
                            stats['contrib_diff_ann_pp'] = (float(np.nansum(wl[m] * (rem[m] - base[m, 0])) / ndays[s] * O.ANN_PP), 'ann_pp')
                        for stt, (v, unit) in stats.items():
                            rows.append(dict(block='G1', item='%s|%s' % (tg, mem), key1=ktype, key2=str(kv), segment=s, stat=stt, value=v, unit=unit, n=n,
                                             status='COMPUTED' if np.isfinite(v) else 'UNKNOWN', query_id='G1-%s' % tg))
        O.log('G1 %s 完成（%.0f s）' % (mem, time.time() - t0))
    D = pd.DataFrame(rows)
    D['value'] = D['value'].astype(float)
    O.atomic_write_csv(O.P('diagnostics', 'G1_E6o.csv'), D)
    O.write_receipt('E6o_G1', [O.P('diagnostics', 'G1_E6o.csv')], code=[__file__], rows=len(D), wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(rows=len(D), wall_s=round(time.time() - t0, 1)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
