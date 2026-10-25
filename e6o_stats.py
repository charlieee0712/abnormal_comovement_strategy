# -*- coding: utf-8 -*-
"""E6o 统计（附录 B.6 / B.7 / B.9 / B.10 / B.12 / B.14 合同；plan §11）。
  python3 e6o_stats.py --phase B            正式：accounts_run/full + randoms/random_paths_B*.csv → statistics/ events/ accounts/daily/
  python3 e6o_stats.py --phase A2 --dryrun  封存后空跑：只用推导段产物，输出写 tmp/dryrun/（检查合并 / 表 / 报告链，不读后段）
口径：日差 = 子 − 父的逐日净超额（同日；POST_VWAP_EQUITY_V11）；段年化 = 均值 × 252 × 100；FULL = Σ n_s D_s / Σ n_s；G4 = 四段 D 中位（G4 行 status = INFO：
  其 net / parent_net 各为四段中位，不满足 D = net − parent_net，故不标 COMPUTED）；HAC（Newey–West）lag = H / 2H / max(H, 20)；
  stationary bootstrap 2,000 次（几何块长均值 20，敏感 60），相关账户共同抽日期；D_sc = 两边逐日净超额按 min(x_c, x_p) / x 缩放（交易后敞口共同下缩）；
  D_imp = 固定路径再扣冲击 κ √A Σ|Δw|^1.5 σ / √ADV（A = 5 亿、κ = .5；压力 A = 10 亿、κ = 1）；PORT3_T = 全组合目标 size 均值差 ×100 的段均值。"""
import os
import sys
import json
import time
import argparse
import resource

import numpy as np
import pandas as pd

import e6o_core as O
import e6o_engine as E

SEG4 = list(O.SEGS)
MSEG = ['2013-2014', '2015-2018', '2019-2023', '2024-2026']
A_MAIN, K_MAIN, A_STR, K_STR = 5e8, 0.5, 1e9, 1.0
V0 = 1e8


def load_accounts(phase, R):
    sub = 'full' if phase == 'B' else 'deriv'
    out = {}
    for r in R[R.series != 'P_SOURCE'].itertuples():
        p = O.P('accounts_run', sub, r.exec_hash[:2], '%s.npz' % r.exec_hash)
        z = np.load(p, allow_pickle=False)
        out[r.exec_id] = dict(DY=z['DY'], IN_i=z['IN_i'], IN_f=z['IN_f'], S_i=z['S_i'], HOLDH=z['HOLDH'])
    return out


def source_daily(mk_dates, R, segs=O.SEGS):
    """P_SOURCE 逐日（各段源账本拼接；段外 / 预热 = NaN）。A2 空跑只读推导两段。"""
    cd = O.cache_dir()
    di = {d: i for i, d in enumerate(mk_dates)}
    T = len(mk_dates)
    out = {}
    cache = {s: np.load(os.path.join(cd, 'source', '%s.npz' % s), allow_pickle=False) for s in segs}
    for r in R[R.series == 'P_SOURCE'].itertuples():
        H = int(r.H[1:])
        arr = {k: np.full(T, np.nan) for k in ('net8', 'gross', 'pos', 'turn')}
        for s in segs:
            z = cache[s]
            idx = np.array([di[d] for d in z['dates']])
            for k in arr:
                arr[k][idx] = z['src_%s|%s|%s|H%d' % (k, r.form, r.memory, H)]
        out[r.exec_id] = arr
    return out


def nw_se(D, L):
    """D：(n, A) 去均值前的日差（缺测日 NaN）；返回每列"有限日均值"的 Newey–West 标准误。
    每列按自身有限日数 n_f 归一（缺测日去均值后记 0、不贡献自协方差）；部分支持（MINUTE_2013 在 2010-2014 段、P_SOURCE 段首预热）不再被全段日数压小。"""
    nf = np.isfinite(D).sum(0).astype(float)
    with np.errstate(all='ignore'):
        X = D - np.nanmean(D, axis=0)
    X = np.where(np.isfinite(X), X, 0.0)
    v = (X * X).sum(0)
    n = D.shape[0]
    for l in range(1, L + 1):
        if l >= n:
            break
        g = (X[l:] * X[:-l]).sum(0)
        v += 2.0 * (1.0 - l / (L + 1.0)) * g
    with np.errstate(all='ignore'):
        return np.where(nf > L + 2, np.sqrt(np.maximum(v / nf, 0.0) / nf), np.nan)


def boot_matrix(n, reps, block, seed):
    """stationary bootstrap 计数矩阵 W (reps, n)：每行 n 个抽样日的出现次数（几何块长均值 block）。"""
    rng = np.random.default_rng(seed)
    W = np.zeros((reps, n), np.float32)
    p = 1.0 / block
    for r in range(reps):
        i = rng.integers(n)
        for k in range(n):
            if k > 0:
                if rng.random() < p:
                    i = rng.integers(n)
                else:
                    i = (i + 1) % n
            W[r, i] += 1.0
    return W


def boot_matrix_fast(n, reps, block, seed):
    rng = np.random.default_rng(seed)
    p = 1.0 / block
    starts = rng.integers(0, n, size=(reps, n))
    newb = rng.random((reps, n)) < p
    newb[:, 0] = True
    idx = np.empty((reps, n), np.int64)
    cur = starts[:, 0].copy()
    idx[:, 0] = cur
    for k in range(1, n):
        cur = np.where(newb[:, k], starts[:, k], (cur + 1) % n)
        idx[:, k] = cur
    W = np.zeros((reps, n), np.float32)
    rows = np.repeat(np.arange(reps), n)
    np.add.at(W, (rows, idx.ravel()), 1.0)
    return W


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=['A2', 'B'], required=True)
    ap.add_argument('--dryrun', action='store_true')
    ap.add_argument('--reps', type=int, default=2000)
    ap.add_argument('--fake_post', action='store_true', help='空跑专用：后段日行用推导段日行循环复制（假数据；账户与源账本只读推导段），使 FULL / G4 / 政策 / 报告全路径被执行')
    a = ap.parse_args()
    if a.fake_post and not (a.dryrun and a.phase == 'A2'):
        raise RuntimeError('--fake_post 只用于 --phase A2 --dryrun')
    t0 = time.time()
    outroot = O.P('tmp', 'dryrun') if a.dryrun else O.work()
    if a.phase == 'B' and not os.path.exists(O.P('registration', 'seal_A2.json')):
        raise RuntimeError('seal_A2 不在：拒绝后段统计')
    cd = O.cache_dir()
    dates = np.load(os.path.join(cd, 'panels', 'dates.npy'))
    T = len(dates)
    d_end = T if a.phase == 'B' else int(np.searchsorted(dates, '2019-01-01'))
    bench = np.load(os.path.join(cd, 'panels', 'bench.npy'))
    R = pd.read_csv(O.P('registration', 'registry_E6o.csv'), keep_default_na=False, na_values=[''])
    PL = pd.read_csv(O.P('registration', 'run_plan_E6o.csv'), keep_default_na=False, na_values=[''])
    acc = load_accounts(a.phase, R)
    src = source_daily(dates, R, O.SEGS if a.phase == 'B' else O.DERIV_SEGS)
    if a.fake_post:
        d19_ = d_end
        fk = np.arange(T - d19_) % d19_                       # 后段第 i 日 ← 推导段第 i mod d19 日
        for e in acc:
            DY = acc[e]['DY'].copy()
            DY[d19_:] = DY[fk]
            acc[e]['DY'] = DY
        for e in src:
            for k in src[e]:
                v = src[e][k].copy()
                v[d19_:] = v[fk]
                src[e][k] = v
        bench = bench.copy()
        bench[d19_:] = bench[fk]
        d_end = T
        O.log('fake_post：后段 %d 日用推导段日行循环复制（假数据）' % (T - d19_))
    segi = np.array([O.seg_of_date(d) for d in dates])
    years = np.array([int(d[:4]) for d in dates])
    masks = {s: (segi == s) & (np.arange(T) < d_end) for s in SEG4}
    masks['2013-2014'] = (dates >= O.MINUTE_START) & (segi == '2010-2014') & (np.arange(T) < d_end)
    ids = list(R.exec_id)
    reg = R.set_index('exec_id')
    # ---------------- 逐日序列矩阵
    ne = np.full((T, len(ids)), np.nan)
    feefr = np.full((T, len(ids)), np.nan)
    rnet = np.full((T, len(ids)), np.nan)
    xprev = np.full((T, len(ids)), np.nan)
    expo = np.full((T, len(ids)), np.nan)
    cash = np.full((T, len(ids)), np.nan)
    turn = np.full((T, len(ids)), np.nan)
    impb = np.full((T, len(ids)), np.nan)
    szk = np.full((T, len(ids)), np.nan)
    szu = np.full((T, len(ids)), np.nan)
    col = {e: j for j, e in enumerate(ids)}
    for e, j in col.items():
        if e in acc:
            DY = acc[e]['DY']
            nav = DY[:, E.DYI['nav_post']]
            vprev = np.r_[V0, nav[:-1]]
            ne[:d_end, j] = DY[:d_end, E.DYI['net_excess']]
            feefr[:d_end, j] = (DY[:, E.DYI['fee']] / vprev)[:d_end]
            rnet[:d_end, j] = DY[:d_end, E.DYI['r_net']]
            xprev[:d_end, j] = DY[:d_end, E.DYI['x_prev']]
            expo[:d_end, j] = DY[:d_end, E.DYI['exposure']]
            cash[:d_end, j] = DY[:d_end, E.DYI['cash_share']]
            with np.errstate(all='ignore'):
                turn[:d_end, j] = (0.5 * DY[:, E.DYI['traded']] / nav)[:d_end]
                szk[:d_end, j] = (DY[:, E.DYI['sz_num']] / DY[:, E.DYI['sz_den']])[:d_end]
                szu[:d_end, j] = (DY[:, E.DYI['sz_unk']] / (DY[:, E.DYI['sz_den']] + DY[:, E.DYI['sz_unk']]))[:d_end]
            impb[:d_end, j] = DY[:d_end, E.DYI['impact_br']]
        else:
            s = src[e]
            ne[:d_end, j] = s['net8'][:d_end]
            feefr[:d_end, j] = (s['turn'] * 8e-4)[:d_end]
            rnet[:d_end, j] = (s['net8'] + bench * s['pos'])[:d_end]
            xprev[:d_end, j] = s['pos'][:d_end]
            expo[:d_end, j] = s['pos'][:d_end]
            cash[:d_end, j] = (1.0 - s['pos'])[:d_end]
            turn[:d_end, j] = s['turn'][:d_end]
    par = np.array([col[reg.loc[e, 'parent_exec_id']] for e in ids])
    spar = np.array([col[reg.loc[e, 'source_parent_exec_id']] for e in ids])
    Hh = np.array([int(reg.loc[e, 'H'][1:]) for e in ids])
    diff = ne - ne[:, par]
    dsrc = ne - ne[:, spar]
    # 同资本视图
    xm = np.minimum(xprev, xprev[:, par])
    with np.errstate(all='ignore'):
        scc = np.where(xprev > 0, ne * xm / xprev, 0.0)
        scp = np.where(xprev[:, par] > 0, ne[:, par] * xm / xprev[:, par], 0.0)
    dsc = scc - scp
    imp_m = K_MAIN * np.sqrt(A_MAIN) * np.nan_to_num(impb)
    imp_s = K_STR * np.sqrt(A_STR) * np.nan_to_num(impb)
    dimp = (ne - imp_m) - (ne[:, par] - imp_m[:, par])
    dimps = (ne - imp_s) - (ne[:, par] - imp_s[:, par])
    dsz = (szk - szk[:, par]) * 100.0
    # 事件（按段）
    ev = {}
    for e in ids:
        if e not in acc:
            continue
        IN_i = acc[e]['IN_i']
        real = IN_i[:, E.IN_STATUS] != 9
        ev[e] = IN_i[real]
    sellok = (np.load(os.path.join(cd, 'panels', 'sellable.npy'), mmap_mode='r'), np.load(os.path.join(cd, 'panels', 'is_open.npy'), mmap_mode='r'))
    # ---------------- bootstrap 计数矩阵（相关账户共同抽日期；每段一个种子）
    rows = []
    BOOT = {}
    for s in SEG4 + ['2013-2014', 'FULL']:
        m = masks[s] if s != 'FULL' else (np.arange(T) < d_end)
        n = int(m.sum())
        if n < 30:
            continue
        BOOT[(s, 20)] = boot_matrix_fast(n, a.reps, 20, O.stable_u64('E6o', 'BOOT', s, 20) % (2 ** 32))
        BOOT[(s, 60)] = boot_matrix_fast(n, a.reps, 60, O.stable_u64('E6o', 'BOOT', s, 60) % (2 ** 32))

    def seg_stats(s, m):
        n_days = int(m.sum())
        Dm = diff[m]
        res = {}
        res['n'] = np.isfinite(Dm).sum(0)
        common = np.isfinite(Dm)                              # 子与父都有限的共同日（net / parent_net / D 同一日集）
        with np.errstate(all='ignore'):
            res['net'] = np.nanmean(np.where(common, ne[m], np.nan), 0) * O.ANN_PP
            res['pnet'] = np.nanmean(np.where(common, ne[m][:, par], np.nan), 0) * O.ANN_PP
            res['abs'] = np.nanmean(rnet[m], 0) * O.ANN_PP
            res['gross'] = np.nanmean(ne[m] + feefr[m], 0) * O.ANN_PP
            res['fee'] = np.nanmean(feefr[m], 0) * O.ANN_PP
            res['Dsrc'] = np.nanmean(dsrc[m], 0) * O.ANN_PP
            res['Dsc'] = np.nanmean(dsc[m], 0) * O.ANN_PP
            res['Dimp'] = np.nanmean(dimp[m], 0) * O.ANN_PP
            res['Dimps'] = np.nanmean(dimps[m], 0) * O.ANN_PP
            res['dsz'] = np.nanmean(dsz[m], 0)
            res['szu'] = np.nanmean(szu[m], 0)
            res['expo'] = np.nanmean(expo[m], 0)
            res['cash'] = np.nanmean(cash[m], 0)
            res['turn'] = np.nanmean(turn[m], 0) * 252.0
        for lagname in ('H', '2H', 'MAX'):
            se = np.full(len(ids), np.nan)
            for hv in np.unique(Hh):
                L = hv if lagname == 'H' else (2 * hv if lagname == '2H' else max(hv, 20))
                cols = Hh == hv
                if n_days > L + 2:
                    se[cols] = nw_se(Dm[:, cols], L) * O.ANN_PP
            res['se_' + lagname] = se
        for blk in (20, 60):
            W = BOOT.get((s, blk))
            if W is not None and W.shape[1] == n_days:
                X = np.where(np.isfinite(Dm), Dm, 0.0).astype(np.float32)
                Fm = np.isfinite(Dm).astype(np.float32)
                with np.errstate(all='ignore'):
                    bm = (W @ X) / (W @ Fm) * O.ANN_PP           # 重抽样日中的有限日均值（比率估计；与点估计同口径）
                with np.errstate(all='ignore'):
                    res['blo%d' % blk] = np.nanpercentile(bm, 2.5, axis=0)
                    res['bhi%d' % blk] = np.nanpercentile(bm, 97.5, axis=0)
            else:
                res['blo%d' % blk] = np.full(len(ids), np.nan)
                res['bhi%d' % blk] = np.full(len(ids), np.nan)
        return res

    SS = {}
    for s in SEG4 + ['2013-2014']:
        if masks[s].sum() >= 1:
            SS[s] = seg_stats(s, masks[s])
    SS['FULL_ALL'] = seg_stats('FULL', np.arange(T) < d_end)
    mfull13 = (dates >= O.MINUTE_START) & (np.arange(T) < d_end)
    SS['FULL13_ALL'] = seg_stats('FULL13', mfull13)
    # ---------------- account_summary
    for j, e in enumerate(ids):
        r = reg.loc[e]
        sup = r.support
        segs_here = SEG4 + (['2013-2014'] if sup == 'MINUTE_2013' else [])
        evv = ev.get(e)

        def cnt(s):
            if evv is None:
                return dict(n_exit_intents=0, n_realized_early=0, n_late_fill=0, n_unfilled=0, n_censored=0)
            m = masks[s]
            dd = evv[:, E.IN_DAY]
            ex = evv[:, E.IN_EXEC]
            st = evv[:, E.IN_STATUS]
            in_s = m[np.clip(dd, 0, T - 1)]
            ex_s = (ex >= 0) & m[np.clip(ex, 0, T - 1)]
            pend = (st == 0) & in_s
            out = dict(n_exit_intents=int(in_s.sum()), n_realized_early=int(((st == 1) & ex_s).sum()), n_late_fill=int(((st == 2) & ex_s).sum()))
            # 末尾待成交：意向后再无可卖开盘日 → 未成交；否则右删失
            unf = 0
            for i in np.flatnonzero(pend):
                d0 = int(dd[i]) + 1
                sec = int(evv[i, E.IN_SEC])
                if d0 < d_end and (np.asarray(sellok[0][d0:d_end, sec]) & np.asarray(sellok[1][d0:d_end, sec])).any():
                    continue
                unf += 1
            out['n_unfilled'] = unf
            out['n_censored'] = int(pend.sum()) - unf
            return out

        DYe = acc[e]['DY'] if e in acc else None
        segvals = {}
        for s in segs_here:
            if s not in SS:
                continue
            X = SS[s]
            m = masks[s]
            c = cnt(s) if r.series == 'C_ACCOUNT' else dict(n_exit_intents=0, n_realized_early=0, n_late_fill=0, n_unfilled=0, n_censored=0)
            n_days = int(X['n'][j])
            net, pnet = X['net'][j], X['pnet'][j]
            st = 'COMPUTED' if n_days > 0 and np.isfinite(net) and np.isfinite(pnet) else 'UNKNOWN'
            row = dict(exec_id=e, execution_profile=r.execution_profile, segment=s, support=sup, n_days=n_days, net_ann_pp=net, abs_net_ann_pp=X['abs'][j],
                       gross_ann_pp=X['gross'][j], fee_ann_pp=X['fee'][j], parent_exec_id=r.parent_exec_id, parent_net_ann_pp=pnet,
                       D_ann_pp=(net - pnet) if st == 'COMPUTED' else np.nan, source_parent_exec_id=r.source_parent_exec_id, D_source_ann_pp=X['Dsrc'][j],
                       D_sc_ann_pp=X['Dsc'][j], hac_se_H=X['se_H'][j], hac_se_2H=X['se_2H'][j], hac_se_max=X['se_MAX'][j], boot_lo=X['blo20'][j], boot_hi=X['bhi20'][j],
                       exposure_mean=X['expo'][j], cash_share_mean=X['cash'][j], turnover_ann=X['turn'][j], **c,
                       n_reentries=int(DYe[m, E.DYI['n_reentry']].sum()) if DYe is not None else 0,
                       n_internal_transfers=int(DYe[m, E.DYI['n_internal']].sum()) if DYe is not None else 0,
                       cash_lock_cny_days=float((DYe[m, E.DYI['tag_amt']] + DYe[m, E.DYI['lock_amt']]).sum()) if DYe is not None else 0.0,
                       status=st, D_imp_ann_pp=X['Dimp'][j], D_imp_stress_ann_pp=X['Dimps'][j], size_dev_pp=X['dsz'][j], size_unknown_share=X['szu'][j],
                       boot60_lo=X['blo60'][j], boot60_hi=X['bhi60'][j])
            rows.append(row)
            segvals[s] = row
        for tag, ss_ in (('', SEG4), ('_2013', MSEG)):
            if tag == '_2013' and sup != 'MINUTE_2013':
                continue
            have = [segvals[s] for s in ss_ if s in segvals and segvals[s]['status'] == 'COMPUTED']
            Xf = SS['FULL_ALL' if tag == '' else 'FULL13_ALL']
            if len(have) == 4:
                w = np.array([h['n_days'] for h in have], float)
                net_f = float(np.sum(w * np.array([h['net_ann_pp'] for h in have])) / w.sum())
                pnet_f = float(np.sum(w * np.array([h['parent_net_ann_pp'] for h in have])) / w.sum())
                Dl = np.array([h['D_ann_pp'] for h in have])
                D_f = float(np.sum(w * Dl) / w.sum())
                full = dict(have[0])
                full.update(segment='FULL' + tag, n_days=int(w.sum()), net_ann_pp=net_f, parent_net_ann_pp=pnet_f, D_ann_pp=net_f - pnet_f, status='COMPUTED')
                for k_ in ('abs_net_ann_pp', 'gross_ann_pp', 'fee_ann_pp', 'D_source_ann_pp', 'D_sc_ann_pp', 'exposure_mean', 'cash_share_mean', 'turnover_ann',
                           'D_imp_ann_pp', 'D_imp_stress_ann_pp', 'size_dev_pp', 'size_unknown_share'):
                    vv = np.array([h[k_] for h in have], float)
                    full[k_] = float(np.nansum(w * vv) / w[np.isfinite(vv)].sum()) if np.isfinite(vv).any() else np.nan
                for k_ in ('n_exit_intents', 'n_realized_early', 'n_late_fill', 'n_unfilled', 'n_censored', 'n_reentries', 'n_internal_transfers', 'cash_lock_cny_days'):
                    full[k_] = sum(h[k_] for h in have)
                full.update(hac_se_H=Xf['se_H'][j], hac_se_2H=Xf['se_2H'][j], hac_se_max=Xf['se_MAX'][j], boot_lo=Xf['blo20'][j], boot_hi=Xf['bhi20'][j],
                            boot60_lo=Xf['blo60'][j], boot60_hi=Xf['bhi60'][j])
                g4 = dict(full)
                g4.update(segment='G4' + tag, net_ann_pp=float(np.median([h['net_ann_pp'] for h in have])), parent_net_ann_pp=float(np.median([h['parent_net_ann_pp'] for h in have])),
                          D_ann_pp=float(np.median(Dl)), D_source_ann_pp=float(np.median([h['D_source_ann_pp'] for h in have])),
                          D_sc_ann_pp=float(np.median([h['D_sc_ann_pp'] for h in have])), status='INFO',
                          hac_se_H=np.nan, hac_se_2H=np.nan, hac_se_max=np.nan, boot_lo=np.nan, boot_hi=np.nan, boot60_lo=np.nan, boot60_hi=np.nan)
            else:
                base = dict(exec_id=e, execution_profile=r.execution_profile, support=sup, parent_exec_id=r.parent_exec_id, source_parent_exec_id=r.source_parent_exec_id,
                            n_days=0, status='UNKNOWN')
                full = dict(base, segment='FULL' + tag)
                g4 = dict(base, segment='G4' + tag)
            rows.append(full)
            rows.append(g4)
    AS = pd.DataFrame(rows)
    cols = ['exec_id', 'execution_profile', 'segment', 'support', 'n_days', 'net_ann_pp', 'abs_net_ann_pp', 'gross_ann_pp', 'fee_ann_pp', 'parent_exec_id', 'parent_net_ann_pp',
            'D_ann_pp', 'source_parent_exec_id', 'D_source_ann_pp', 'D_sc_ann_pp', 'hac_se_H', 'hac_se_2H', 'hac_se_max', 'boot_lo', 'boot_hi', 'exposure_mean', 'cash_share_mean',
            'turnover_ann', 'n_exit_intents', 'n_realized_early', 'n_late_fill', 'n_unfilled', 'n_censored', 'n_reentries', 'n_internal_transfers', 'cash_lock_cny_days', 'status',
            'D_imp_ann_pp', 'D_imp_stress_ann_pp', 'size_dev_pp', 'size_unknown_share', 'boot60_lo', 'boot60_hi']
    AS = AS[cols]
    od = os.path.join(outroot, 'statistics')
    os.makedirs(od, exist_ok=True)
    O.atomic_write_csv(os.path.join(od, 'account_summary_E6o.csv'), AS)
    # 逐年 D（政策 c2）
    yr_rows = []
    for j, e in enumerate(ids):
        if reg.loc[e, 'series'] != 'C_ACCOUNT':
            continue
        for y in sorted(set(years[:d_end])):
            m = (years == y) & (np.arange(T) < d_end)
            x = diff[m, j]
            ok = np.isfinite(x)
            yr_rows.append(dict(exec_id=e, year=int(y), n_days=int(ok.sum()), D_ann_pp=float(np.mean(x[ok]) * O.ANN_PP) if ok.any() else np.nan))
    O.atomic_write_csv(os.path.join(od, 'yearly_D_E6o.csv'), pd.DataFrame(yr_rows))
    # 事件计数（B.12）
    er = []
    for e in ids:
        if reg.loc[e, 'series'] != 'C_ACCOUNT':
            continue
        A_ = acc[e]
        evv = ev[e]
        st = evv[:, E.IN_STATUS]
        full = AS[(AS.exec_id == e) & (AS.segment == 'FULL')].iloc[0]
        hh = A_['HOLDH']
        tot = hh.sum()
        if tot > 0:
            mean_h = float((hh * np.arange(len(hh))).sum() / tot)
            cum = np.cumsum(hh)
            med_h = float(np.searchsorted(cum, (tot + 1) / 2.0))
        else:
            mean_h = med_h = np.nan
        S_i = A_['S_i']
        er.append(dict(exec_id=e, trigger=reg.loc[e, 'trigger'], n_intents=int(len(evv)), n_realized_early=int((st == 1).sum()), n_late_fill=int((st == 2).sum()),
                       n_unfilled=int(full.n_unfilled) if np.isfinite(full.n_unfilled) else 0, n_censored=int(full.n_censored) if np.isfinite(full.n_censored) else 0,
                       n_unknown_state_days=int(S_i[E.SI_UNKDAYS]), n_reentry_blocked=int(S_i[E.SI_REBLK]), n_reentry_reconfirmed=int(S_i[E.SI_RECONF]),
                       n_internal_transfers=int(S_i[E.SI_INTERNAL]), mean_realized_hold_days=mean_h, median_realized_hold_days=med_h, status='COMPUTED'))
    EV = pd.DataFrame(er)
    bad = EV.n_intents - (EV.n_realized_early + EV.n_late_fill + EV.n_unfilled + EV.n_censored)
    if (bad != 0).any():
        raise RuntimeError('事件恒等不成立：%d 行' % int((bad != 0).sum()))
    oe = os.path.join(outroot, 'events')
    os.makedirs(oe, exist_ok=True)
    O.atomic_write_csv(os.path.join(oe, 'event_counts_E6o.csv'), EV)
    # 日序列导出（B.14）
    dd_dir = os.path.join(outroot, 'accounts', 'daily')
    os.makedirs(dd_dir, exist_ok=True)
    c_rows = R[R.series == 'C_ACCOUNT']
    main = c_rows[c_rows.is_main_object == 1].exec_id.iloc[0].split('|')
    sel = set(c_rows[c_rows.is_primary72 == 1].exec_id)
    for e in c_rows.exec_id:
        p_ = e.split('|')
        if p_[0] == main[0] and p_[2] == main[2] and p_[3] == main[3] and p_[4] == main[4]:
            sel.add(e)
    sel |= set(R[R.series.isin(['P_ACCOUNT', 'P_SOURCE'])].exec_id)
    idx_rows = []
    for e in sorted(sel):
        j = col[e]
        h = reg.loc[e, 'exec_hash']
        if e in acc:
            DY = acc[e]['DY'][:d_end]
            df = pd.DataFrame(dict(date=dates[:d_end], nav_pre=DY[:, E.DYI['nav_pre']], nav_post=DY[:, E.DYI['nav_post']], fee=DY[:, E.DYI['fee']],
                                   exposure=DY[:, E.DYI['exposure']], bench_ret=bench[:d_end], net_excess_ret=DY[:, E.DYI['net_excess']],
                                   cash_share=DY[:, E.DYI['cash_share']], n_holdings=DY[:, E.DYI['n_hold']].astype(int), n_exits_today=DY[:, E.DYI['n_exits']].astype(int)))
        else:
            s = src[e]
            gross = s['gross'] + bench * s['pos']
            navp = np.empty(T)
            navq = np.empty(T)
            fee = np.empty(T)
            v = V0
            for d in range(T):
                g = gross[d] if np.isfinite(gross[d]) else 0.0
                f = (s['turn'][d] * 8e-4 if np.isfinite(s['turn'][d]) else 0.0) * v
                navq[d] = v * (1.0 + g)
                fee[d] = f
                navp[d] = navq[d] - f
                v = navp[d]
            df = pd.DataFrame(dict(date=dates, nav_pre=navq, nav_post=navp, fee=fee, exposure=s['pos'], bench_ret=bench, net_excess_ret=s['net8'],
                                   cash_share=1.0 - s['pos'], n_holdings=0, n_exits_today=0))[:d_end]
        fn = '%s.csv' % h
        O.atomic_write_csv(os.path.join(dd_dir, fn), df)
        idx_rows.append(dict(exec_hash=h, exec_id=e, file=fn, n_rows=len(df), date_min=str(df.date.min()), date_max=str(df.date.max())))
    O.atomic_write_csv(os.path.join(dd_dir, 'INDEX.csv'), pd.DataFrame(idx_rows))
    facts = dict(phase=a.phase, dryrun=a.dryrun, fake_post=a.fake_post, rows=len(AS), events=len(EV), daily=len(idx_rows), wall_s=round(time.time() - t0, 1),
                 rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.atomic_write_json(os.path.join(od, 'stats_facts_E6o.json'), facts)
    print(json.dumps(facts, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
