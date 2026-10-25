# -*- coding: utf-8 -*-
"""E6p 统计（附录 B.6 / B.7 / B.12 / B.14 / B.17 / B.18 / B.19 合同；plan §7 / §9 / §13）：
  python3 e6p_stats.py --phase B                       正式：statistics/ events/ accounts/daily/ trades/ verify/ 全部合同表
  python3 e6p_stats.py --phase A2 --root tmp/a2stats    推导段（G1 用；不读后段）
  python3 e6p_stats.py --phase A2 --fake_post --root tmp/dryrun   假数据空跑：后段日行 = 推导段日行循环复制（账户 / 源 / 基准 / 随机），全链路被执行
口径：日差 = 子 − 父逐日净超额（同日；交易后 VWAP NAV 时钟）；段年化 = 252 × 100 × 日均；FULL = Σ n_s v_s / Σ n_s；G4 = 四段中位；
HAC lag = max(两 H)（同 H 父 = H）/ 20 / 60；stationary bootstrap 2,000 次（块 40 主 / 20、80 敏感；相关账户共同抽日期；每段一个种子）；
D_sc = 同资本视图（逐日两边净超额按 min(x_c, x_p) / x 缩放，E6o 同式）；D_imp = 旧审计冲击（κ √A Σ|Δw|^1.5 σ / √ADV；5 亿 κ .5；压力 10 亿 κ 1）；
成本曲线：冲击份额 = κ A^δ S_δ（S_δ = 引擎逐日系数，p0 = .01 锚，A = 起始资本）；盈亏平衡 Δ(A) = a − b (A / 1 亿)^δ（plan §9.3 / 附录 C crossing）。"""
import os
import sys
import json
import time
import math
import argparse
import resource
from multiprocessing import get_context

import numpy as np
import pandas as pd

import e6p_core as O
import e6p_engine as E

SEG4 = list(O.SEGS)
SEG6 = SEG4 + ['FULL', 'G4']
YEARS = list(range(2010, 2027))
A_MAIN, K_MAIN, A_STR, K_STR = 5e8, 0.5, 1e9, 1.0
REPS = 2000
BLOCKS = (40, 20, 80)
A0 = 1e8
A_GRID = list(O.A_GRID)
GRID = [(A, k, x) for A in A_GRID for k in O.KAPPAS for x in O.EXPONENTS]
OKN = {E.OK_REGULAR: 'REGULAR', E.OK_EXIT: 'EXIT', E.OK_EXTRA: 'EXTRA', E.OK_RENEW: 'RENEW', E.OK_DUE: 'DUE'}
SUM_COLS = ['exec_id', 'execution_profile', 'segment', 'support', 'n_days', 'net_ann_pp', 'abs_net_ann_pp', 'full_bench_excess_ann_pp', 'gross_ann_pp', 'fee_ann_pp',
            'parent_same_h_exec_id', 'parent_same_h_net_ann_pp', 'D_same_h_ann_pp', 'parent_h5_same_deploy_exec_id', 'D_h5_same_deploy_ann_pp', 'parent_h5_native_exec_id',
            'D_h5_native_ann_pp', 'source_parent_exec_id', 'D_source_ann_pp', 'D_sc_ann_pp', 'hac_se_H', 'hac_se_20', 'hac_se_60', 'boot_lo', 'boot_hi', 'exposure_mean',
            'cash_share_mean', 'turnover_ann', 'n_exit_intents', 'n_realized_early', 'n_late_fill', 'n_unfilled', 'n_censored', 'n_renew_exits', 'n_reentries',
            'n_internal_transfers', 'exposure_diff_vs_parent', 'cash_share_diff_vs_parent', 'size_dev_pp', 'sector_active_max_pp', 'status',
            'D_imp_ann_pp', 'D_imp_stress_ann_pp', 'boot20_lo', 'boot20_hi', 'boot80_lo', 'boot80_hi', 'size_unknown_share', 'sector_active_max_peak_pp',
            'D_h5_same_trigger_ann_pp', 'parent_h5_same_trigger_exec_id', 'start_state', 'cost_profile']
DAILY_COLS = ['date', 'nav_pre', 'nav_post', 'fee', 'exposure', 'cash_share', 'bench_ret', 'net_excess_ret', 'abs_net_ret', 'full_bench_excess_ret', 'n_holdings', 'n_lots',
              'n_exits_today', 'n_renew_exits_today', 'extra_batch_share', 'turnover_day']
TRADE_COLS = ['date', 'security', 'lot_id', 'request_id', 'order_kind', 'side', 'qty', 'notional_cny', 'price', 'fee_cny', 'lot_due']
G = {}


# ------------------------------------------------------------------ 载入
class Ctx(object):
    def __init__(self, phase, fake_post=False, root=None):
        self.phase = phase
        self.fake = fake_post
        cd = O.cache_dir()
        self.cd = cd
        self.dates = np.load(os.path.join(cd, 'panels', 'dates.npy'))
        self.codes = np.load(os.path.join(cd, 'panels', 'codes.npy'))
        self.T = len(self.dates)
        self.d19 = int(np.searchsorted(self.dates, '2019-01-01'))
        self.d_end = self.T if (phase == 'B' or fake_post) else self.d19
        self.sub = 'full' if phase == 'B' else 'deriv'
        self.fk = (np.arange(self.T - self.d19) % self.d19) if fake_post else None
        b = np.load(os.path.join(cd, 'panels', 'bench.npy')).astype(float)
        if fake_post:
            b = b.copy()
            b[self.d19:] = b[self.fk]
        self.bench = b
        self.segi = np.array([O.seg_of_date(d) for d in self.dates])
        self.years = np.array([int(d[:4]) for d in self.dates])
        live = np.arange(self.T) < self.d_end
        self.masks = {s: (self.segi == s) & live for s in SEG4}
        self.masks['FULL'] = live
        self.root = root or O.work()
        R = pd.read_csv(O.P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
        self.R = R
        self.ids = list(R.exec_id)
        self.col = {e: j for j, e in enumerate(self.ids)}
        self.reg = R.set_index('exec_id', drop=False)

    def fake_rows(self, a):
        if self.fake:
            a = a.copy()
            a[self.d19:] = a[self.fk]
        return a

    def out(self, *parts):
        p = os.path.join(self.root, *parts)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        return p


def acct_file(ctx, h, kind='acct'):
    sub = ctx.sub + ('_fb' if kind == 'fb' else '')
    return O.P('accounts_run', sub, h[:2], '%s.npz' % h)


SER = ('ne', 'rnet', 'fullb', 'feefr', 'expo', 'cash', 'xprev', 'turn', 's05', 's07', 'impb', 'szk', 'szu', 'sam', 'navpre', 'navpost', 'fee', 'nhold', 'nlots', 'nexit',
       'nrenew', 'xshare', 'traded', 'n_reentry', 'n_internal', 'buyv', 'sellv', 'deploy_buy', 'cash_abs', 'renew_n', 'navc')


def dy_series(DY, V0=O.V0):
    nav = DY[:, E.DYI['nav_post']]
    vprev = np.r_[V0, nav[:-1]]
    with np.errstate(all='ignore'):
        out = dict(ne=DY[:, E.DYI['net_excess']], rnet=DY[:, E.DYI['r_net']], fullb=DY[:, E.DYI['full_bench_ex']], feefr=DY[:, E.DYI['fee']] / vprev,
                   expo=DY[:, E.DYI['exposure']], cash=DY[:, E.DYI['cash_share']], xprev=DY[:, E.DYI['x_prev']], turn=0.5 * DY[:, E.DYI['traded']] / nav,
                   s05=DY[:, E.DYI['cost_s05']], s07=DY[:, E.DYI['cost_s07']], impb=DY[:, E.DYI['impact_br']],
                   szk=DY[:, E.DYI['sz_num']] / DY[:, E.DYI['sz_den']], szu=DY[:, E.DYI['sz_unk']] / (DY[:, E.DYI['sz_den']] + DY[:, E.DYI['sz_unk']]),
                   sam=DY[:, E.DYI['sector_active_max']], navpre=DY[:, E.DYI['nav_pre']], navpost=nav, fee=DY[:, E.DYI['fee']], nhold=DY[:, E.DYI['n_hold']],
                   nlots=DY[:, E.DYI['n_lots']], nexit=DY[:, E.DYI['n_exits']], nrenew=DY[:, E.DYI['renew_exec']], xshare=DY[:, E.DYI['extra_val']],
                   traded=DY[:, E.DYI['traded']], n_reentry=DY[:, E.DYI['n_reentry']], n_internal=DY[:, E.DYI['n_internal']], buyv=DY[:, E.DYI['buy_val']],
                   sellv=DY[:, E.DYI['sell_val']], deploy_buy=DY[:, E.DYI['deploy_buy']], cash_abs=DY[:, E.DYI['cash_share']] * nav, renew_n=DY[:, E.DYI['renew_n']],
                   navc=DY[:, E.DYI['nav_close']])
    return out


def load_all(ctx):
    T, n = ctx.T, len(ctx.ids)
    S = {k: np.full((T, n), np.nan) for k in SER}
    acc = {}
    src_cache = {s: np.load(os.path.join(ctx.cd, 'source_e6p', '%s.npz' % s), allow_pickle=False) for s in SEG4}
    di = {d: i for i, d in enumerate(ctx.dates)}
    src_idx = {s: np.array([di[d] for d in src_cache[s]['dates']]) for s in SEG4}
    for r in ctx.R.itertuples(index=False):
        j = ctx.col[r.exec_id]
        if r.series == 'P_SOURCE':
            H = int(r.H)
            arr = {k: np.full(T, np.nan) for k in ('net8', 'gross', 'pos', 'turn')}
            for s in SEG4:
                for k in arr:
                    arr[k][src_idx[s]] = src_cache[s]['src_%s|%s|%s|H%d' % (k, r.form, r.memory, H)]
            for k in arr:
                arr[k] = ctx.fake_rows(arr[k])
                arr[k][ctx.d_end:] = np.nan
            S['ne'][:, j] = arr['net8']
            S['feefr'][:, j] = arr['turn'] * 8e-4
            S['rnet'][:, j] = arr['net8'] + ctx.bench * arr['pos']
            S['fullb'][:, j] = S['rnet'][:, j] - ctx.bench
            S['expo'][:, j] = arr['pos']
            S['xprev'][:, j] = arr['pos']
            S['cash'][:, j] = 1.0 - arr['pos']
            S['turn'][:, j] = arr['turn']
            acc[r.exec_id] = dict(src=arr)
            continue
        z = np.load(acct_file(ctx, r.exec_hash), allow_pickle=False)
        DY = z['DY']
        nd = min(len(DY), ctx.d_end)
        ser = dy_series(DY[:nd])
        for k, v in ser.items():
            col = np.full(T, np.nan)
            col[:nd] = v
            S[k][:, j] = ctx.fake_rows(col)
        acc[r.exec_id] = dict(IN_i=z['IN_i'], IN_f=z['IN_f'], S_i=z['S_i'], HOLDH=z['HOLDH'], LOTH=z['LOTH'], DY=DY)
    return S, acc


# ------------------------------------------------------------------ 统计工具
def nw_se(D, L):
    """D：(n, A) 日差（缺测 NaN）；返回各列有限日均值的 Newey–West 标准误（Bartlett，lag L；每列按自身有限日数归一）。"""
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


def boot_ci(W, D):
    X = np.where(np.isfinite(D), D, 0.0).astype(np.float32)
    F = np.isfinite(D).astype(np.float32)
    with np.errstate(all='ignore'):
        bm = (W @ X) / (W @ F) * O.ANN_PP
        return np.nanpercentile(bm, 2.5, axis=0), np.nanpercentile(bm, 97.5, axis=0)


def ann(x, m):
    v = x[m]
    v = v[np.isfinite(v)]
    return float(np.mean(v) * O.ANN_PP) if len(v) else np.nan


# ------------------------------------------------------------------ 账户汇总（B.6）
def summary(ctx, S, acc):
    R = ctx.R
    n = len(ctx.ids)
    par = np.array([ctx.col.get(e, -1) if e else -1 for e in R.parent_same_h_exec_id])
    p5d = np.array([ctx.col.get(e, -1) if e else -1 for e in R.parent_h5_same_deploy_exec_id])
    p5n = np.array([ctx.col.get(e, -1) if e else -1 for e in R.parent_h5_native_exec_id])
    psr = np.array([ctx.col.get(e, -1) if e else -1 for e in R.source_parent_exec_id])
    # H5 同触发父（Q05 第四差）：同 form / memory / deploy / cap / renew / trigger 的 H5 行
    key = {(r.form, r.memory, r.H, r.deploy, r.cap, r.renew, r.trigger, r.execution_profile, r.role): r.exec_id for r in R.itertuples(index=False)}
    p5t = np.array([ctx.col.get(key.get((r.form, r.memory, '5', r.deploy, r.cap, r.renew, r.trigger, r.execution_profile, r.role), ''), -1)
                    if (r.role == 'ACCOUNT' and r.trigger != 'NONE' and r.H != '5') else -1 for r in R.itertuples(index=False)])
    Hh = np.array([int(h) for h in R.H])
    ne = S['ne']

    def dmat(pidx):
        D = np.full_like(ne, np.nan)
        ok = pidx >= 0
        D[:, ok] = ne[:, ok] - ne[:, pidx[ok]]
        return D
    Dp, D5d, D5n, Dsr, D5t = dmat(par), dmat(p5d), dmat(p5n), dmat(psr), dmat(p5t)
    xm = np.full_like(ne, np.nan)
    okp = par >= 0
    xm[:, okp] = np.minimum(S['xprev'][:, okp], S['xprev'][:, par[okp]])
    with np.errstate(all='ignore'):
        scc = np.where(S['xprev'] > 0, ne * xm / S['xprev'], 0.0)
        scp = np.full_like(ne, np.nan)
        scp[:, okp] = np.where(S['xprev'][:, par[okp]] > 0, ne[:, par[okp]] * xm[:, okp] / S['xprev'][:, par[okp]], 0.0)
    Dsc = np.where(okp[None, :], scc - scp, np.nan)
    imp_m = K_MAIN * np.sqrt(A_MAIN) * np.nan_to_num(S['impb'])
    imp_s = K_STR * np.sqrt(A_STR) * np.nan_to_num(S['impb'])
    Dimp = np.full_like(ne, np.nan)
    Dimps = np.full_like(ne, np.nan)
    Dimp[:, okp] = (ne[:, okp] - imp_m[:, okp]) - (ne[:, par[okp]] - imp_m[:, par[okp]])
    Dimps[:, okp] = (ne[:, okp] - imp_s[:, okp]) - (ne[:, par[okp]] - imp_s[:, par[okp]])
    dsz = np.full_like(ne, np.nan)
    dsz[:, okp] = (S['szk'][:, okp] - S['szk'][:, par[okp]]) * 100.0
    BOOT = {}
    for s in SEG4 + ['FULL']:
        m = ctx.masks[s]
        nn = int(m.sum())
        if nn < 30:
            continue
        for blk in BLOCKS:
            BOOT[(s, blk)] = boot_matrix(nn, REPS, blk, O.stable_u64('E6p', 'BOOT', s, blk) % (2 ** 32))
    seg = {}
    for s in SEG4 + ['FULL']:
        m = ctx.masks[s]
        if not m.any():
            continue
        Dm = Dp[m]
        common = np.where(okp[None, :], np.isfinite(Dm), np.isfinite(ne[m]))
        res = {}
        with np.errstate(all='ignore'):
            res['n'] = common.sum(0)
            res['net'] = np.nanmean(np.where(common, ne[m], np.nan), 0) * O.ANN_PP
            pn = np.full(n, np.nan)
            pn[okp] = np.nanmean(np.where(common[:, okp], ne[m][:, par[okp]], np.nan), 0) * O.ANN_PP
            res['pnet'] = pn
            res['D'] = np.where(okp, res['net'] - pn, np.nan)
            for k, X in (('abs', S['rnet']), ('fullb', S['fullb']), ('fee', S['feefr']), ('expo', S['expo']), ('cash', S['cash']), ('turn', S['turn']),
                         ('szu', S['szu']), ('sam', S['sam'])):
                res[k] = np.nanmean(np.where(common, X[m], np.nan), 0) * (O.ANN_PP if k in ('abs', 'fullb', 'fee') else (252.0 if k == 'turn' else 1.0))
            res['sam_peak'] = np.nanmax(np.where(common, S['sam'][m], np.nan), 0)
            res['gross'] = np.nanmean(np.where(common, ne[m] + S['feefr'][m], np.nan), 0) * O.ANN_PP
            for k, X in (('D5d', D5d), ('D5n', D5n), ('Dsr', Dsr), ('Dsc', Dsc), ('Dimp', Dimp), ('Dimps', Dimps), ('D5t', D5t)):
                res[k] = np.nanmean(X[m], 0) * O.ANN_PP
            res['dsz'] = np.nanmean(dsz[m], 0)
        for lag_name in ('H', '20', '60'):
            se = np.full(n, np.nan)
            for hv in np.unique(Hh):
                L = hv if lag_name == 'H' else int(lag_name)
                cols = (Hh == hv) & okp
                if cols.any() and Dm.shape[0] > L + 2:
                    se[cols] = nw_se(Dm[:, cols], L) * O.ANN_PP
            res['se_' + lag_name] = se
        for blk in BLOCKS:
            W = BOOT.get((s, blk))
            lo = np.full(n, np.nan)
            hi = np.full(n, np.nan)
            if W is not None and okp.any():
                l_, h_ = boot_ci(W, Dm[:, okp])
                lo[okp], hi[okp] = l_, h_
            res['blo%d' % blk], res['bhi%d' % blk] = lo, hi
        seg[s] = res
    rows = []
    for j, e in enumerate(ctx.ids):
        r = R.iloc[j]
        segvals = {}
        base = dict(exec_id=e, execution_profile=r.execution_profile, support=r.support, start_state=r.start_state, cost_profile=r.cost_profile,
                    parent_same_h_exec_id=r.parent_same_h_exec_id, parent_h5_same_deploy_exec_id=r.parent_h5_same_deploy_exec_id,
                    parent_h5_native_exec_id=r.parent_h5_native_exec_id, source_parent_exec_id=r.source_parent_exec_id,
                    parent_h5_same_trigger_exec_id=ctx.ids[p5t[j]] if p5t[j] >= 0 else '')
        for s in SEG4 + ['FULL']:
            if s not in seg:
                row = dict(base, segment=s, n_days=0, status='NOT_RUN')
                rows.append(row)
                segvals[s] = row
                continue
            X = seg[s]
            nd = int(X['n'][j])
            row = dict(base, segment=s, n_days=nd)
            if nd == 0 or not np.isfinite(X['net'][j]):
                row.update(status='UNKNOWN')
                rows.append(row)
                segvals[s] = row
                continue
            row.update(net_ann_pp=X['net'][j], abs_net_ann_pp=X['abs'][j], full_bench_excess_ann_pp=X['fullb'][j], gross_ann_pp=X['gross'][j], fee_ann_pp=X['fee'][j],
                       exposure_mean=X['expo'][j], cash_share_mean=X['cash'][j], turnover_ann=X['turn'][j], size_unknown_share=X['szu'][j],
                       sector_active_max_pp=X['sam'][j], sector_active_max_peak_pp=X['sam_peak'][j], status='COMPUTED')
            if okp[j]:
                row.update(parent_same_h_net_ann_pp=X['pnet'][j], D_same_h_ann_pp=X['D'][j], D_sc_ann_pp=X['Dsc'][j], hac_se_H=X['se_H'][j], hac_se_20=X['se_20'][j],
                           hac_se_60=X['se_60'][j], boot_lo=X['blo40'][j], boot_hi=X['bhi40'][j], boot20_lo=X['blo20'][j], boot20_hi=X['bhi20'][j],
                           boot80_lo=X['blo80'][j], boot80_hi=X['bhi80'][j], D_imp_ann_pp=X['Dimp'][j], D_imp_stress_ann_pp=X['Dimps'][j], size_dev_pp=X['dsz'][j])
            if p5d[j] >= 0:
                row['D_h5_same_deploy_ann_pp'] = X['D5d'][j]
            if p5n[j] >= 0:
                row['D_h5_native_ann_pp'] = X['D5n'][j]
            if psr[j] >= 0:
                row['D_source_ann_pp'] = X['Dsr'][j]
            if p5t[j] >= 0:
                row['D_h5_same_trigger_ann_pp'] = X['D5t'][j]
            row.update(event_counts(ctx, acc.get(e), s, S, j))
            rows.append(row)
            segvals[s] = row
        # FULL：n_days 加权（net / parent / D 与各差同权）；G4：四段中位
        have = [segvals[s] for s in SEG4 if segvals[s].get('status') == 'COMPUTED']
        full = segvals['FULL']
        if len(have) == 4 and full.get('status') == 'COMPUTED':
            w = np.array([h['n_days'] for h in have], float)
            wm = lambda k: float(np.sum(w * np.array([h.get(k, np.nan) for h in have], float)) / w.sum()) if all(np.isfinite(h.get(k, np.nan)) for h in have) else full.get(k, np.nan)
            for k in ('net_ann_pp', 'abs_net_ann_pp', 'full_bench_excess_ann_pp', 'gross_ann_pp', 'fee_ann_pp', 'exposure_mean', 'cash_share_mean', 'turnover_ann',
                      'sector_active_max_pp', 'size_unknown_share'):
                full[k] = wm(k)
            if okp[j]:
                for k in ('parent_same_h_net_ann_pp', 'D_sc_ann_pp', 'D_imp_ann_pp', 'D_imp_stress_ann_pp', 'size_dev_pp'):
                    full[k] = wm(k)
                full['D_same_h_ann_pp'] = full['net_ann_pp'] - full['parent_same_h_net_ann_pp']
            for k in ('D_h5_same_deploy_ann_pp', 'D_h5_native_ann_pp', 'D_h5_same_trigger_ann_pp'):
                if k in full:
                    full[k] = wm(k)
            g4 = dict(base, segment='G4', n_days=int(w.sum()), status='COMPUTED')
            for k in ('net_ann_pp', 'abs_net_ann_pp', 'full_bench_excess_ann_pp', 'gross_ann_pp', 'fee_ann_pp', 'exposure_mean', 'cash_share_mean', 'turnover_ann',
                      'sector_active_max_pp', 'parent_same_h_net_ann_pp', 'D_same_h_ann_pp', 'D_h5_same_deploy_ann_pp', 'D_h5_native_ann_pp', 'D_source_ann_pp', 'D_sc_ann_pp',
                      'D_imp_ann_pp', 'D_imp_stress_ann_pp', 'size_dev_pp', 'D_h5_same_trigger_ann_pp'):
                vals = [h.get(k, np.nan) for h in have]
                if all(isinstance(v, float) and np.isfinite(v) for v in vals):
                    g4[k] = float(np.median(vals))
            for k in ('n_exit_intents', 'n_realized_early', 'n_late_fill', 'n_unfilled', 'n_censored', 'n_renew_exits', 'n_reentries', 'n_internal_transfers'):
                g4[k] = full.get(k, '')
        else:
            g4 = dict(base, segment='G4', n_days=0, status='UNKNOWN')
        rows.append(g4)
    AS = pd.DataFrame(rows)
    # 敞口 / 现金差 = 本行 − 父行（同段；两行都 COMPUTED）
    idx = AS.set_index(['exec_id', 'segment'])
    pe = AS.parent_same_h_exec_id.fillna('')
    for own, dcol in (('exposure_mean', 'exposure_diff_vs_parent'), ('cash_share_mean', 'cash_share_diff_vs_parent')):
        pv = [idx[own].get((p, s), np.nan) if p else np.nan for p, s in zip(pe, AS.segment)]
        AS[dcol] = np.where(pe != '', AS[own].astype(float) - np.array(pv, float), np.nan)
    for c in SUM_COLS:
        if c not in AS.columns:
            AS[c] = np.nan
    return AS[SUM_COLS]


def event_counts(ctx, a, s, S, j):
    """段内事件计数（意向日 / 成交日落在段内；段末待成交：意向日 + 1 ≥ 授权末日 → 右删失，否则未成交）。"""
    out = dict(n_exit_intents=0, n_realized_early=0, n_late_fill=0, n_unfilled=0, n_censored=0, n_renew_exits=0)
    m = ctx.masks[s]
    out['n_reentries'] = int(np.nansum(S['n_reentry'][m, j]))
    out['n_internal_transfers'] = int(np.nansum(S['n_internal'][m, j]))
    if a is None or 'IN_i' not in a:
        return out
    IN = a['IN_i']
    if ctx.fake and len(IN):
        return out
    real = IN[:, E.IN_KIND] != E.KD_RAND
    IN = IN[real]
    dd = IN[:, E.IN_DAY]
    ex = IN[:, E.IN_EXEC]
    st = IN[:, E.IN_STATUS]
    in_s = m[np.clip(dd, 0, ctx.T - 1)] & (dd < ctx.d_end)
    ex_s = (ex >= 0) & m[np.clip(ex, 0, ctx.T - 1)]
    pend = (st == 0) & in_s
    cens = pend & (dd + 1 >= ctx.d_end)
    out.update(n_exit_intents=int(in_s.sum()), n_realized_early=int(((st == 1) & ex_s).sum()), n_late_fill=int(((st == 2) & ex_s).sum()),
               n_unfilled=int((pend & ~cens).sum()), n_censored=int(cens.sum()), n_renew_exits=int(((IN[:, E.IN_KIND] == E.KD_RENEW) & in_s).sum()))
    return out


# ------------------------------------------------------------------ 逐年（B.19）
def yearly(ctx, S):
    R = ctx.R
    rows = []
    ne = S['ne']
    for j, e in enumerate(ctx.ids):
        r = R.iloc[j]
        if r.role != 'ACCOUNT':
            continue
        p = ctx.col.get(r.parent_same_h_exec_id, -1) if r.parent_same_h_exec_id else -1
        for y in YEARS:
            m = (ctx.years == y) & (np.arange(ctx.T) < ctx.d_end)
            if not m.any():
                rows.append(dict(exec_id=e, execution_profile=r.execution_profile, year=y, n_days=0, partial_year_flag=1 if y == 2026 else 0, status='NOT_RUN'))
                continue
            x = ne[m, j]
            if p >= 0:
                ok = np.isfinite(x) & np.isfinite(ne[m, p])
                net = float(np.mean(x[ok]) * O.ANN_PP)
                pn = float(np.mean(ne[m, p][ok]) * O.ANN_PP)
                rows.append(dict(exec_id=e, execution_profile=r.execution_profile, year=y, n_days=int(ok.sum()), net_ann_pp=net, parent_same_h_net_ann_pp=pn,
                                 D_same_h_ann_pp=net - pn, partial_year_flag=1 if y == 2026 else 0, status='COMPUTED'))
            else:
                ok = np.isfinite(x)
                rows.append(dict(exec_id=e, execution_profile=r.execution_profile, year=y, n_days=int(ok.sum()), net_ann_pp=float(np.mean(x[ok]) * O.ANN_PP),
                                 partial_year_flag=1 if y == 2026 else 0, status='COMPUTED'))
    cols = ['exec_id', 'execution_profile', 'year', 'n_days', 'net_ann_pp', 'parent_same_h_net_ann_pp', 'D_same_h_ann_pp', 'partial_year_flag', 'status']
    Y = pd.DataFrame(rows)
    for c in cols:
        if c not in Y.columns:
            Y[c] = np.nan
    return Y[cols]


# ------------------------------------------------------------------ 随机 / 匹配（B.7）
def random_tables(ctx, AS, S):
    R = ctx.R
    tag = 'B' if ctx.phase == 'B' else 'A2'
    parts = [pd.read_csv(O.P('randoms', 'random_paths_%s.csv' % tag), keep_default_na=False, na_values=[''])]
    pt = O.P('randoms', 'random_paths_B_topup.csv')
    if ctx.phase == 'B' and os.path.exists(pt) and os.path.getsize(pt) > 10:
        parts.append(pd.read_csv(pt, keep_default_na=False, na_values=['']))
    P = pd.concat(parts, ignore_index=True)
    P = P[P.status == 'OK']
    if P.duplicated(['owner_exec_id', 'mechanism', 'path_id']).any():
        raise RuntimeError('随机路径重复（owner × 机制 × 路径）')
    if ctx.fake:
        for s in ('2019-2023', '2024-2026'):
            src = '2010-2014' if s == '2019-2023' else '2015-2018'
            for k in ('D', 'n', 'req', 'within', 'cross', 'unm', 'nreq', 'nunm'):
                P['%s_%s' % (k, s)] = P['%s_%s' % (k, src)]
    refs = pd.read_csv(O.P('registration', 'random_control_refs_E6p.csv'), keep_default_na=False, dtype=str)
    feas = R[R.execution_profile == 'FEASIBLE_DAILY'].set_index('logical_id')
    main_l = set(R[(R.role == 'ACCOUNT') & (R.form == O.MAIN_FORM) & (R.H == '20') & (R.trigger.isin(['T1a', 'T1b_LEVEL'])) & (R.renew == '0') & (R.block == 'MAIN')].logical_id)
    scope = [(feas.loc[x.owner_logical_id].exec_id, x.mechanism, int(x.minimum_paths)) for x in refs.itertuples(index=False)]
    ideal = R[(R.execution_profile == 'IDEALIZED_SOURCE_FILL') & R.logical_id.isin(main_l)]
    scope += [(e, 'AMOUNT_MATCH_V2', 128) for e in ideal.exec_id]
    ASi = AS.set_index(['exec_id', 'segment'])
    navsum = {s: np.nansum(S['navpost'][ctx.masks[s]], 0) for s in SEG4 + ['FULL']}
    mains = set(R[(R.execution_profile == 'FEASIBLE_DAILY') & R.logical_id.isin(main_l)].exec_id)
    rows, mrows = [], []
    nd = {s: P['n_%s' % s].to_numpy(float) for s in SEG4}
    for s in SEG4:
        P['D_%s' % s] = P['D_%s' % s].astype(float)
    num = sum(np.nan_to_num(P['D_%s' % s].to_numpy(float)) * nd[s] for s in SEG4)
    den = sum(nd[s] for s in SEG4)
    with np.errstate(all='ignore'):
        P['D_FULL'] = num / den
    for k in ('req', 'within', 'cross', 'unm', 'nreq', 'nunm'):
        P['%s_FULL' % k] = sum(P['%s_%s' % (k, s)].astype(float) for s in SEG4)
    grp = {k: g for k, g in P.groupby(['owner_exec_id', 'mechanism'])}
    for e, mech, mp in scope:
        g = grp.get((e, mech))
        j = ctx.col[e]
        if g is None or len(g) == 0:
            for s in SEG4 + ['FULL']:
                rows.append(dict(owner_exec_id=e, mechanism=mech, segment=s, paths=0, minimum_paths=mp, status='NOT_RUN'))
            continue
        full_unm = g['unm_FULL'].sum() / max(g['req_FULL'].sum(), 1e-300) if g['req_FULL'].sum() > 0 else 0.0
        comp = 'CONTROL_NOT_COMPARABLE' if full_unm > O.NOT_COMPARABLE_UNMATCHED else 'COMPARABLE'
        segs = SEG4 + ['FULL'] if ctx.phase == 'B' or ctx.fake else list(O.DERIV_SEGS)
        for s in segs:
            v = g['D_%s' % s].to_numpy(float)
            v = v[np.isfinite(v)]
            npth = len(v)
            real = ASi['D_same_h_ann_pp'].get((e, s), np.nan)
            mean = float(np.mean(v)) if npth else np.nan
            sd = float(np.std(v, ddof=1)) if npth > 1 else np.nan
            mcse = sd / math.sqrt(npth) if npth > 1 else np.nan
            rank = float((np.sum(v < real) + 0.5 * np.sum(v == real)) / npth) if (npth and np.isfinite(real)) else np.nan
            unm_share = float(g['unm_%s' % s].sum() / g['req_%s' % s].sum()) if g['req_%s' % s].sum() > 0 else 0.0
            st = 'COMPUTED'
            if s == 'FULL' and e in mains and mech in ('AMOUNT_MATCH_V2', 'COUNT_ISK', 'BERNOULLI_LAG60') and npth >= 1024 and not (mcse <= 0.01):
                st = 'MC_LIMIT'
            rows.append(dict(owner_exec_id=e, mechanism=mech, segment=s, paths=npth, minimum_paths=mp, real_D_ann_pp=real, rand_mean_D_ann_pp=mean,
                             rand_sd_D_ann_pp=sd, mcse=mcse, rank_real=rank, unmatched_share=unm_share, control_comparability=comp, status=st,
                             rand_mean_n_intents=float(g.n_intents.mean())))
            isk = mech == 'COUNT_ISK'
            req, wi, cr, un = (float(g['%s_%s' % (k, s)].mean()) for k in ('req', 'within', 'cross', 'unm'))
            navs = float(navsum[s][j]) if s in navsum else np.nan
            mrows.append(dict(owner_exec_id=e, mechanism=mech, segment=s, requested_cny='' if isk else req, matched_within_cny='' if isk else wi,
                              matched_cross_cny='' if isk else cr, unmatched_cny='' if isk else un,
                              unmatched_nav_share='' if isk else (un / navs if navs > 0 else np.nan),
                              n_requests=req if isk else float(g['nreq_%s' % s].mean()), n_unmatched_requests=un if isk else float(g['nunm_%s' % s].mean()),
                              matched_within_n=wi if isk else '', matched_cross_n=cr if isk else '', control_comparability=comp, status='COMPUTED', paths=npth))
    RD = pd.DataFrame(rows)
    MT = pd.DataFrame(mrows)
    RP = P[P.owner_exec_id.isin(mains)][['owner_exec_id', 'mechanism', 'path_id', 'seed', 'D_FULL', 'n_unmatched_days']].rename(columns={'D_FULL': 'FULL_D_ann_pp'})
    return RD, MT, RP.sort_values(['owner_exec_id', 'mechanism', 'path_id'])


# ------------------------------------------------------------------ 成本曲线 / 盈亏平衡 / 反馈（B.17）
def comparator_map(ctx):
    R = ctx.R
    key = {(r.form, r.memory, r.H, r.deploy, r.cap, r.renew, r.trigger, r.execution_profile): r.exec_id for r in R.itertuples(index=False) if r.role == 'ACCOUNT'}
    out = {}
    for r in R.itertuples(index=False):
        if r.role != 'ACCOUNT':
            continue
        c = [('ABSOLUTE', '')]
        if r.parent_same_h_exec_id:
            c.append(('VS_SAME_H_PARENT', r.parent_same_h_exec_id))
        if r.parent_h5_same_deploy_exec_id and r.parent_h5_same_deploy_exec_id != r.exec_id:
            c.append(('VS_H5_SAME_DEPLOY', r.parent_h5_same_deploy_exec_id))
        if r.parent_h5_native_exec_id and r.parent_h5_native_exec_id != r.exec_id:
            c.append(('VS_H5_CURRENT_NATIVE', r.parent_h5_native_exec_id))
        if r.trigger == 'T1a':
            lv = key.get((r.form, r.memory, r.H, r.deploy, r.cap, r.renew, 'T1b_LEVEL', r.execution_profile))
            if lv:
                c.append(('T1A_VS_LEVEL', lv))
        out[r.exec_id] = c
    return out


def crossing(a, b, d, A0_=A0):
    """Δ(A) = a − b (A / A0)^δ 的根（plan 附录 C crossing 同式；log 尺度）。"""
    if not (np.isfinite(a) and np.isfinite(b)):
        return 'COST_MISSING', np.nan
    if b == 0:
        return 'NO_ROOT', np.nan
    if a == 0 or (a > 0) != (b > 0):
        return 'NO_ROOT', np.nan
    lr = math.log(A0_) + (math.log(abs(a)) - math.log(abs(b))) / d
    if not math.isfinite(lr) or not (math.log(sys.float_info.min) <= lr <= math.log(sys.float_info.max)):
        return 'OUT_OF_NUMERICAL_RANGE', np.nan
    root = math.exp(lr)
    kind = 'POSITIVE_ROOT' if b > 0 else 'LOWER_CROSSING'
    if root < min(A_GRID) or root > max(A_GRID):
        kind = 'OUT_OF_GRID'
    return kind, root


def cost_tables(ctx, S):
    cm = comparator_map(ctx)
    ne, fr = S['ne'], S['feefr']
    rows, brows = [], []
    for e, comps in cm.items():
        j = ctx.col[e]
        for ck, ce in comps:
            k = ctx.col[ce] if ce else -1
            for s in SEG4 + ['FULL']:
                m = ctx.masks[s]
                x = ne[m, j]
                f = fr[m, j]
                ok = np.isfinite(x)
                if k >= 0:
                    ok = ok & np.isfinite(ne[m, k])
                if not ok.any():
                    continue
                g0 = np.mean((x + f)[ok]) - (np.mean((ne[m, k] + fr[m, k])[ok]) if k >= 0 else 0.0)
                f0 = np.mean(f[ok]) - (np.mean(fr[m, k][ok]) if k >= 0 else 0.0)
                n0 = np.mean(x[ok]) - (np.mean(ne[m, k][ok]) if k >= 0 else 0.0)
                ms = {}
                for dl, key in ((0.5, 's05'), (0.7, 's07')):
                    sj = np.nan_to_num(S[key][m, j][ok])
                    ms[dl] = np.mean(sj) - (np.mean(np.nan_to_num(S[key][m, k][ok])) if k >= 0 else 0.0)
                for (A, kap, dl) in GRID:
                    di = kap * A ** dl * ms[dl]
                    rows.append((e, ce, ck, A, kap, dl, s, g0 * O.ANN_PP, f0 * O.ANN_PP, di * O.ANN_PP, (n0 - di) * O.ANN_PP))
                if s == 'FULL':
                    for kap in O.KAPPAS:
                        for dl in O.EXPONENTS:
                            b = kap * A0 ** dl * ms[dl] * O.ANN_PP
                            a = n0 * O.ANN_PP
                            kind, root = crossing(a, b, dl)
                            brows.append(dict(exec_id=e, execution_profile=ctx.reg.loc[e, 'execution_profile'], comparator_kind=ck, comparator_exec_id=ce, kappa=kap,
                                              exponent=dl, a_coeff=a, b_coeff=b, root_kind=kind, breakeven_A_cny=root, status='COMPUTED'))
    C = pd.DataFrame(rows, columns=['exec_id', 'comparator_exec_id', 'comparator_kind', 'A_cny', 'kappa', 'exponent', 'segment', 'gross_diff_ann_pp', 'fee_diff_ann_pp',
                                    'impact_diff_ann_pp', 'net_after_impact_diff_ann_pp'])
    # G4 = 四段中位
    q = C[C.segment.isin(SEG4)]
    g4 = q.groupby(['exec_id', 'comparator_exec_id', 'comparator_kind', 'A_cny', 'kappa', 'exponent'], sort=False)[
        ['gross_diff_ann_pp', 'fee_diff_ann_pp', 'impact_diff_ann_pp', 'net_after_impact_diff_ann_pp']].median().reset_index()
    cnt = q.groupby(['exec_id', 'comparator_kind', 'A_cny', 'kappa', 'exponent'], sort=False).size().reset_index(name='k')
    g4 = g4.merge(cnt, on=['exec_id', 'comparator_kind', 'A_cny', 'kappa', 'exponent'])
    g4 = g4[g4.k == 4].drop(columns=['k'])
    g4['segment'] = 'G4'
    C = pd.concat([C, g4], ignore_index=True)
    C['execution_profile'] = C.exec_id.map(ctx.reg.execution_profile)
    C['status'] = 'COMPUTED'
    C = C[['exec_id', 'execution_profile', 'comparator_kind', 'comparator_exec_id', 'A_cny', 'kappa', 'exponent', 'segment', 'gross_diff_ann_pp', 'fee_diff_ann_pp',
           'impact_diff_ann_pp', 'net_after_impact_diff_ann_pp', 'status']]
    return C, pd.DataFrame(brows)


def feedback_table(ctx, S):
    import e6p_run as RN
    F = pd.read_csv(O.P('registration', 'cost_feedback_refs_E6p.csv'), keep_default_na=False, dtype=str)
    R = ctx.R
    feas = R[R.execution_profile == 'FEASIBLE_DAILY'].set_index('logical_id', drop=False)
    fbne = {}
    for f in F.itertuples(index=False):
        row = feas.loc[f.owner_logical_id]
        h = RN.fb_hash(row.exec_id, int(f.A_cny))
        z = np.load(acct_file(ctx, h, 'fb'), allow_pickle=False)
        DY = z['DY']
        col = np.full(ctx.T, np.nan)
        nd = min(len(DY), ctx.d_end)
        col[:nd] = DY[:nd, E.DYI['net_excess']]
        fbne[(row.exec_id, int(f.A_cny))] = ctx.fake_rows(col)
    rows = []
    for (e, A), x in fbne.items():
        p = ctx.reg.loc[e, 'parent_same_h_exec_id']
        px = fbne.get((p, A)) if p else None
        j = ctx.col[e]
        k = ctx.col[p] if p else -1
        imp = 0.5 * A ** 0.5 * S['s05'][:, j]
        vals = {}
        for s in SEG4 + ['FULL']:
            m = ctx.masks[s]
            row = dict(owner_exec_id=e, parent_feedback_exec_id=p, A_cny=A, kappa=0.5, exponent=0.5, segment=s, net_ann_pp_feedback=ann(x, m), status='COMPUTED')
            if px is not None:
                ok = m & np.isfinite(x) & np.isfinite(px)
                row['parent_net_ann_pp_feedback'] = float(np.mean(px[ok]) * O.ANN_PP)
                row['net_ann_pp_feedback'] = float(np.mean(x[ok]) * O.ANN_PP)
                row['D_feedback_ann_pp'] = row['net_ann_pp_feedback'] - row['parent_net_ann_pp_feedback']
                impp = 0.5 * A ** 0.5 * S['s05'][:, k]
                row['D_fixed_path_ann_pp'] = float(np.mean(((S['ne'][:, j] - imp) - (S['ne'][:, k] - impp))[ok]) * O.ANN_PP)
            rows.append(row)
            vals[s] = row
        g = dict(owner_exec_id=e, parent_feedback_exec_id=p, A_cny=A, kappa=0.5, exponent=0.5, segment='G4', status='COMPUTED')
        for c in ('net_ann_pp_feedback', 'parent_net_ann_pp_feedback', 'D_feedback_ann_pp', 'D_fixed_path_ann_pp'):
            v = [vals[s].get(c) for s in SEG4]
            if all(isinstance(t, float) and np.isfinite(t) for t in v):
                g[c] = float(np.median(v))
        rows.append(g)
    cols = ['owner_exec_id', 'parent_feedback_exec_id', 'A_cny', 'kappa', 'exponent', 'segment', 'net_ann_pp_feedback', 'parent_net_ann_pp_feedback', 'D_feedback_ann_pp',
            'D_fixed_path_ann_pp', 'status']
    D = pd.DataFrame(rows)
    for c in cols:
        if c not in D.columns:
            D[c] = np.nan
    return D[cols]


# ------------------------------------------------------------------ 事件 / 续期（B.12）
def events_tables(ctx, acc, S):
    R = ctx.R
    er, rr = [], []
    for j, e in enumerate(ctx.ids):
        r = R.iloc[j]
        if r.role != 'ACCOUNT':
            continue
        a = acc[e]
        IN = a['IN_i']
        IN = IN[IN[:, E.IN_KIND] != E.KD_RAND]
        st = IN[:, E.IN_STATUS]
        dd = IN[:, E.IN_DAY]
        pend = st == 0
        cens = pend & (dd + 1 >= ctx.d_end)
        hh = a['HOLDH']
        lh = a['LOTH']
        tot_h, tot_l = hh.sum(), lh.sum()
        mean_h = float((hh * np.arange(len(hh))).sum() / tot_h) if tot_h else np.nan
        mean_l = float((lh * np.arange(len(lh))).sum() / tot_l) if tot_l else np.nan
        med_l = float(np.searchsorted(np.cumsum(lh), (tot_l + 1) / 2.0)) if tot_l else np.nan
        Si = a['S_i']
        m = np.arange(ctx.T) < ctx.d_end
        sec_age = float(np.nansum(a['DY'][:ctx.d_end, E.DYI['sec_age_sum']]) / max(np.nansum(a['DY'][:ctx.d_end, E.DYI['sec_age_n']]), 1.0))
        er.append(dict(exec_id=e, trigger=r.trigger, renew=int(r.renew), n_intents=int(len(IN)), n_realized_early=int((st == 1).sum()), n_late_fill=int((st == 2).sum()),
                       n_unfilled=int((pend & ~cens).sum()), n_censored=int(cens.sum()), n_no_action_opportunity=int(Si[E.SI_NOACT]),
                       n_renew_exit_orders=int((IN[:, E.IN_KIND] == E.KD_RENEW).sum()), n_reentries=int(np.nansum(S['n_reentry'][m, j])),
                       n_internal_transfers=int(Si[E.SI_INTERNAL]), mean_lot_age_realized_early=mean_h, mean_lot_age_all_lots=mean_l, median_lot_age_all_lots=med_l,
                       mean_security_age=sec_age, share_lots_reaching_due=float(Si[E.SI_LDUE] / Si[E.SI_LCLOSED]) if Si[E.SI_LCLOSED] else np.nan,
                       n_rounding_fix_days=int(Si[E.SI_RNDFIX]), status='COMPUTED'))
        if int(r.renew) == 5:
            rr.append(dict(exec_id=e, n_checkpoints=int(Si[E.SI_RCHK]), n_confirmed=int(Si[E.SI_RCONF2]), n_rejected=int(Si[E.SI_RREJ]), n_unknown=int(Si[E.SI_RUNK]),
                           n_exit_orders=int((IN[:, E.IN_KIND] == E.KD_RENEW).sum()), share_new_lot_same_security=np.nan, status='COMPUTED'))
    EV = pd.DataFrame(er)
    bad = EV.n_intents - (EV.n_realized_early + EV.n_late_fill + EV.n_unfilled + EV.n_censored)
    if (bad != 0).any():
        raise RuntimeError('事件恒等不成立：%d 行' % int((bad != 0).sum()))
    return EV, pd.DataFrame(rr)


# ------------------------------------------------------------------ 成交分片（B.18）与续期同证券份额
def load_trades(ctx, h):
    parts = []
    for sub in (['deriv'] if ctx.phase == 'A2' else ['deriv', 'full']):
        p = O.P('trades_parts', sub, h[:2], '%s.npz' % h)
        if os.path.exists(p):
            z = np.load(p, allow_pickle=False)
            parts.append((z['TL_i'], z['TL_f']))
    if not parts:
        return np.zeros((0, 7), np.int64), np.zeros((0, 4))
    ti = np.concatenate([p[0] for p in parts])
    tf = np.concatenate([p[1] for p in parts])
    keep = ti[:, 0] < ctx.d_end
    return ti[keep], tf[keep]


def job_trades(args):
    e, h, root = args
    ctx = G['ctx']
    try:
        ti, tf = load_trades(ctx, h)
        dates = ctx.dates
        due = ti[:, 6]
        kind = ti[:, 4]
        showdue = (kind == E.OK_EXIT) | (kind == E.OK_RENEW) | (kind == E.OK_DUE)
        lot_due = np.where(showdue, np.where(due < ctx.d_end, dates[np.clip(due, 0, ctx.T - 1)], 'POST_CUTOFF'), '')
        df = pd.DataFrame(dict(date=dates[ti[:, 0]], security=ctx.codes[ti[:, 1]], lot_id=ti[:, 2], request_id=ti[:, 3], order_kind=[OKN[int(k)] for k in kind],
                               side=np.where(ti[:, 5] == 0, 'BUY', 'SELL'), qty=tf[:, 0], notional_cny=tf[:, 1], price=tf[:, 2], fee_cny=tf[:, 3], lot_due=lot_due))
        fn = '%s.csv' % h
        p = os.path.join(root, 'trades', fn)
        tmp = p + '.tmp%d' % os.getpid()
        df.to_csv(tmp, index=False, float_format='%.10g', lineterminator='\n')
        os.replace(tmp, p)
        early_exit_rows = int(((kind == E.OK_EXIT) & (ti[:, 0] < due)).sum())
        early_renew_rows = int(((kind == E.OK_RENEW) & (ti[:, 0] < due)).sum())
        # 续期退出时同证券是否仍有更新的批次（成交日志重建活批次）
        same = np.nan
        return dict(exec_id=e, file='trades/' + fn, n_rows=len(df), n_fills=int((tf[:, 0] > 0).sum()), early_exit_rows=early_exit_rows, early_renew_rows=early_renew_rows,
                    status='OK', share_new_lot_same_security=same)
    except Exception as ex:
        return dict(exec_id=e, status='FAILED', err='%s: %s' % (type(ex).__name__, str(ex)[:200]))


def renew_same_security(ctx, acc, e, h):
    """RENEW 退出意向日 T：同证券是否另有 e0 更晚、在 T 仍持有的批次（成交日志重建批次生命期；意向带批次 ID）。"""
    ti, tf = load_trades(ctx, h)
    IN = acc[e]['IN_i']
    ren = IN[(IN[:, E.IN_KIND] == E.KD_RENEW)]
    if not len(ren):
        return np.nan
    buys = ti[ti[:, 5] == 0]
    sells = ti[ti[:, 5] == 1]
    life = pd.DataFrame(dict(lot=buys[:, 2], sec=buys[:, 1], e0=buys[:, 0])).drop_duplicates('lot')
    close = pd.Series(sells[:, 0], index=sells[:, 2]).groupby(level=0).max()
    life['close'] = life.lot.map(close).fillna(ctx.T + 10).astype(int)
    bysec = {s: g[['e0', 'close', 'lot']].to_numpy() for s, g in life.groupby('sec')}
    hit = 0
    for d, s, lid in zip(ren[:, E.IN_DAY], ren[:, E.IN_SEC], ren[:, E.IN_LID]):
        arr = bysec.get(int(s))
        if arr is None:
            continue
        own = arr[arr[:, 2] == lid]
        e0 = own[0, 0] if len(own) else -1
        if np.any((arr[:, 0] > e0) & (arr[:, 0] <= d) & (arr[:, 1] > d) & (arr[:, 2] != lid)):
            hit += 1
    return hit / len(ren)


# ------------------------------------------------------------------ 日序列（B.14）
def job_daily(args):
    e, h = args
    ctx = G['ctx']
    S = G['S']
    j = ctx.col[e]
    root = G['root']
    try:
        r = ctx.reg.loc[e]
        if r.series == 'P_SOURCE':
            src = G['acc'][e]['src']
            ok = np.isfinite(src['net8'])
            gross = src['gross'] + ctx.bench * src['pos']
            v = O.V0
            navq, navp, fee, absr = [], [], [], []
            for d in range(ctx.T):
                if not ok[d]:
                    continue
                g_ = gross[d] if np.isfinite(gross[d]) else 0.0
                f_ = (src['turn'][d] * 8e-4 if np.isfinite(src['turn'][d]) else 0.0) * v
                q = v * (1.0 + g_)
                p = q - f_
                navq.append(q)
                fee.append(f_)
                navp.append(p)
                absr.append(p / v - 1.0)
                v = p
            idx = np.flatnonzero(ok)
            df = pd.DataFrame(dict(date=ctx.dates[idx], nav_pre=navq, nav_post=navp, fee=fee, exposure=src['pos'][idx], cash_share=1.0 - src['pos'][idx], bench_ret=ctx.bench[idx],
                                   net_excess_ret=src['net8'][idx], abs_net_ret=absr, full_bench_excess_ret=np.array(absr) - ctx.bench[idx], n_holdings='', n_lots='',
                                   n_exits_today='', n_renew_exits_today='', extra_batch_share='', turnover_day=src['turn'][idx]))
        else:
            n = ctx.d_end
            df = pd.DataFrame(dict(date=ctx.dates[:n], nav_pre=S['navpre'][:n, j], nav_post=S['navpost'][:n, j], fee=S['fee'][:n, j], exposure=S['expo'][:n, j],
                                   cash_share=S['cash'][:n, j], bench_ret=ctx.bench[:n], net_excess_ret=S['ne'][:n, j], abs_net_ret=S['rnet'][:n, j],
                                   full_bench_excess_ret=S['fullb'][:n, j], n_holdings=S['nhold'][:n, j].astype(int), n_lots=S['nlots'][:n, j].astype(int),
                                   n_exits_today=S['nexit'][:n, j].astype(int), n_renew_exits_today=S['nrenew'][:n, j].astype(int), extra_batch_share=S['xshare'][:n, j],
                                   turnover_day=S['turn'][:n, j]))
            if not np.isfinite(df.net_excess_ret.to_numpy(float)).all():
                raise RuntimeError('账户日净超额含缺失')
        fn = '%s.csv' % h
        p = os.path.join(root, 'accounts', 'daily', fn)
        tmp = p + '.tmp%d' % os.getpid()
        df.to_csv(tmp, index=False, float_format='%.15g', lineterminator='\n', na_rep='')
        os.replace(tmp, p)
        return dict(exec_hash=h, exec_id=e, file='accounts/daily/' + fn, n_rows=len(df), date_min=str(df.date.iloc[0]), date_max=str(df.date.iloc[-1]), status='OK')
    except Exception as ex:
        return dict(exec_hash=h, exec_id=e, status='FAILED', err='%s: %s' % (type(ex).__name__, str(ex)[:200]))


# ------------------------------------------------------------------ WARM 敏感性
def warm_table(ctx, S):
    R = ctx.R
    import e6p_run as RN
    acc = R[(R.role == 'ACCOUNT')]
    main = acc[acc.is_main_object == '1']
    keep = list(main.exec_id) + list(main.parent_same_h_exec_id) + list(main.parent_h5_native_exec_id)
    keep = list(dict.fromkeys(keep))
    rows = []
    wne = {}
    segs = SEG4 if (ctx.phase == 'B' and not ctx.fake) else list(O.DERIV_SEGS)
    for e in keep:
        for s in segs:
            h = O.sha_bytes(('%s|WARM|%s' % (e, s)).encode())[:16]
            p = RN.res_path('A2' if s in O.DERIV_SEGS else 'B', h, 'warm')
            if not os.path.exists(p):
                continue
            z = np.load(p, allow_pickle=False)
            wne[(e, s)] = z['DY'][:, E.DYI['net_excess']]
    for e in [x for x in keep if ctx.reg.loc[x, 'is_main_object'] == '1']:
        p = ctx.reg.loc[e, 'parent_same_h_exec_id']
        for s in segs:
            if (e, s) not in wne or (p, s) not in wne:
                continue
            m = ctx.masks[s]
            x, y = wne[(e, s)], wne[(p, s)]
            ok = np.isfinite(x) & np.isfinite(y)
            Dw = float(np.mean(x[ok] - y[ok]) * O.ANN_PP)
            j, k = ctx.col[e], ctx.col[p]
            Dc = float(np.nanmean((S['ne'][m, j] - S['ne'][m, k])) * O.ANN_PP)
            rows.append(dict(exec_id=e, parent_exec_id=p, execution_profile=ctx.reg.loc[e, 'execution_profile'], segment=s, start_state='WARM', n_days=int(ok.sum()),
                             net_ann_pp=float(np.mean(x[ok]) * O.ANN_PP), parent_net_ann_pp=float(np.mean(y[ok]) * O.ANN_PP), D_ann_pp=Dw, D_cash_v0_ann_pp=Dc,
                             D_warm_minus_cont=Dw - Dc, status='COMPUTED'))
    return pd.DataFrame(rows)


def write(ctx, rel, df):
    p = ctx.out(rel)
    tmp = p + '.tmp%d' % os.getpid()
    df.to_csv(tmp, index=False, lineterminator='\n', na_rep='', float_format='%.15g')
    os.replace(tmp, p)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=['A2', 'B'], required=True)
    ap.add_argument('--fake_post', action='store_true')
    ap.add_argument('--root', default='')
    ap.add_argument('--workers', type=int, default=64)
    ap.add_argument('--skip_exports', action='store_true')
    ap.add_argument('--skip_randoms', action='store_true', help='工程测试用：随机表留空')
    a = ap.parse_args()
    if a.fake_post and a.phase != 'A2':
        raise RuntimeError('--fake_post 只用于 --phase A2')
    import warnings
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    if a.phase == 'B' and not os.path.exists(O.P('registration', 'seal_A2.json')):
        raise RuntimeError('seal_A2 不在：拒绝后段统计')
    t0 = time.time()
    root = O.P(a.root) if a.root else O.work()
    if a.phase == 'A2' and not a.root:
        raise RuntimeError('A2 统计必须写到 --root（tmp 下），不覆盖正式表')
    ctx = Ctx(a.phase, a.fake_post, root)
    S, acc = load_all(ctx)
    O.log('载入 %d 个执行对象（%.0f s）' % (len(ctx.ids), time.time() - t0))
    AS = summary(ctx, S, acc)
    write(ctx, 'statistics/account_summary_E6p.csv', AS)
    O.log('account_summary %d 行（%.0f s）' % (len(AS), time.time() - t0))
    write(ctx, 'statistics/yearly_E6p.csv', yearly(ctx, S))
    if a.skip_randoms:
        RD = pd.DataFrame(columns=['owner_exec_id', 'mechanism', 'segment', 'paths', 'minimum_paths', 'real_D_ann_pp', 'rand_mean_D_ann_pp', 'rand_sd_D_ann_pp', 'mcse',
                                   'rank_real', 'unmatched_share', 'control_comparability', 'status'])
        MT = pd.DataFrame(columns=['owner_exec_id', 'mechanism', 'segment', 'requested_cny', 'matched_within_cny', 'matched_cross_cny', 'unmatched_cny',
                                   'unmatched_nav_share', 'n_requests', 'n_unmatched_requests', 'control_comparability', 'status'])
        RP = pd.DataFrame(columns=['owner_exec_id', 'mechanism', 'path_id', 'seed', 'FULL_D_ann_pp', 'n_unmatched_days'])
    else:
        RD, MT, RP = random_tables(ctx, AS, S)
    write(ctx, 'statistics/randoms_E6p.csv', RD)
    write(ctx, 'statistics/matching_E6p.csv', MT)
    write(ctx, 'statistics/random_paths_main_E6p.csv', RP)
    O.log('randoms %d / matching %d / main paths %d（%.0f s）' % (len(RD), len(MT), len(RP), time.time() - t0))
    C, BE = cost_tables(ctx, S)
    write(ctx, 'statistics/cost_curve_E6p.csv', C)
    write(ctx, 'statistics/breakeven_E6p.csv', BE)
    write(ctx, 'statistics/cost_feedback_E6p.csv', feedback_table(ctx, S))
    O.log('cost curve %d / breakeven %d（%.0f s）' % (len(C), len(BE), time.time() - t0))
    EV, RW = events_tables(ctx, acc, S)
    write(ctx, 'statistics/warm_sensitivity_E6p.csv', warm_table(ctx, S))
    G['ctx'], G['S'], G['acc'], G['root'] = ctx, S, acc, root
    if not a.skip_exports:
        os.makedirs(os.path.join(root, 'accounts', 'daily'), exist_ok=True)
        os.makedirs(os.path.join(root, 'trades'), exist_ok=True)
        jobs = [(e, ctx.reg.loc[e, 'exec_hash']) for e in ctx.ids]
        ctxp = get_context('fork')
        with ctxp.Pool(a.workers) as pool:
            DI = pd.DataFrame(list(pool.imap_unordered(job_daily, jobs, chunksize=4)))
        if (DI.status != 'OK').any():
            print(DI[DI.status != 'OK'].head().to_string(), flush=True)
            raise RuntimeError('日序列导出失败')
        write(ctx, 'accounts/daily/INDEX.csv', DI[['exec_hash', 'exec_id', 'file', 'n_rows', 'date_min', 'date_max']].sort_values('exec_id'))
        tj = [(e, ctx.reg.loc[e, 'exec_hash'], root) for e in ctx.ids if ctx.reg.loc[e, 'role'] == 'ACCOUNT']
        with ctxp.Pool(a.workers) as pool:
            TI = pd.DataFrame(list(pool.imap_unordered(job_trades, tj, chunksize=2)))
        if (TI.status != 'OK').any():
            print(TI[TI.status != 'OK'].head().to_string(), flush=True)
            raise RuntimeError('成交分片导出失败')
        write(ctx, 'trades/INDEX.csv', TI[['exec_id', 'file', 'n_rows', 'n_fills']].sort_values('exec_id'))
        br = TI[['exec_id', 'early_exit_rows', 'early_renew_rows']].merge(EV[['exec_id', 'n_realized_early', 'n_late_fill', 'n_renew_exit_orders']], on='exec_id')
        br['partial_fill_extra_rows'] = br.early_exit_rows + br.early_renew_rows - br.n_realized_early
        write(ctx, 'verify/trades_events_bridge_E6p.csv', br)
        O.log('daily %d / trades %d（%.0f s）' % (len(DI), len(TI), time.time() - t0))
    if len(RW):
        RW['share_new_lot_same_security'] = [renew_same_security(ctx, acc, e, ctx.reg.loc[e, 'exec_hash']) for e in RW.exec_id]
    write(ctx, 'events/event_counts_E6p.csv', EV)
    write(ctx, 'events/renew_E6p.csv', RW)
    facts = dict(phase=a.phase, fake_post=a.fake_post, rows=len(AS), randoms=len(RD), cost_rows=len(C), events=len(EV), renew=len(RW), wall_s=round(time.time() - t0, 1),
                 rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.atomic_write_json(os.path.join(root, 'statistics', 'stats_facts_E6p.json'), facts)
    print(json.dumps(facts, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
