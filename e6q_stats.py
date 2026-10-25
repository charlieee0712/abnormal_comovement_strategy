# -*- coding: utf-8 -*-
"""E6q 统计（附录 B.10–B.17 / B.19 / B.21 合同；plan §7 / §9 / §13）：
  python3 e6q_stats.py --phase B                     正式：statistics/ events/ verify/（复现 / 运行恒等）全部合同表
  python3 e6q_stats.py --phase A2 --root tmp/a2stats  推导段（G1 用；不读后段）
  python3 e6q_stats.py --phase A2 --fake_post --root tmp/dryrun   假数据空跑：后段日行 = 推导段日行循环复制，全链路被执行
口径：支持 = 全部 201 账户净超额同时有限的交易日（实为全部 3,940 日：基准缺失的 2010-01 前 19 日账户未持仓，净超额 = r_net 有限）；
段年化 = 252 × 100 × 段内日均；FULL = Σ n v / Σ n；G4 = 四段中位；D_<ref> = 本账户 net − 引用账户 net（同支持日，故与引用行自身 net 恒等）；
HAC lag = max(20, 2H) / 20 / 60；stationary bootstrap 2,000 次（主块长 max(20, 2H)；段内抽块、按段真实 n 合并 FULL）；
D_sc = 同资本视图（逐日两边净超额按 min(x_c, x_p) / x 缩放）；成本曲线：日冲击份额 = κ A^δ S_δ（S_δ = 引擎逐日系数 cost_s05 / s07 / s10，CANONICAL = curve）。"""
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

import e6q_core as O
import e6q_engine as E
import e6q_cost as CO
import e6q_rules as RU

SEG4 = list(O.SEGS)
SEG6 = SEG4 + ['FULL', 'G4']
YEARS = list(range(2010, 2027))
REPS = 2000
GRID = [(A, k, x) for A in O.A_GRID for k in O.KAPPAS for x in O.EXPONENTS]
SCOL = {0.5: 's05', 0.7: 's07', 1.0: 's10'}
OKN = {E.OK_REGULAR: 'REGULAR', E.OK_EXIT: 'EXIT', E.OK_EXTRA: 'EXTRA', E.OK_RENEW: 'EXIT', E.OK_DUE: 'DUE', E.OK_EXIT_HALF: 'EXIT_HALF',
       E.OK_EXIT_REARM: 'EXIT_REARM', E.OK_DEADLINE: 'DEADLINE_OVERRIDE'}
SUM_COLS = ['exec_id', 'scenario', 'segment', 'support', 'n_days', 'net_ann_pp', 'abs_net_ann_pp', 'full_bench_excess_ann_pp', 'gross_ann_pp', 'fee_ann_pp',
            'parent_same_arm_exec_id', 'parent_same_arm_net_ann_pp', 'D_same_arm_ann_pp', 'native_same_trigger_exec_id', 'native_same_trigger_net_ann_pp',
            'D_native_same_trigger_ann_pp', 'D_h5_local_ann_pp', 'D_h5_global_ann_pp', 'D_frontier_ann_pp', 'D_level_h20_ann_pp', 'D_cash_same_trigger_ann_pp',
            'D_sc_ann_pp', 'hac_se_H', 'hac_se_20', 'hac_se_60', 'boot_lo', 'boot_hi', 'exposure_mean', 'cash_share_mean', 'turnover_ann', 'max_drawdown_total',
            'cagr_total', 'n_exit_intents', 'n_realized_early', 'n_late_fill', 'n_unfilled', 'n_censored', 'n_deadline_overrides', 'n_half_requests',
            'n_rearm_episodes', 'n_reentries', 'n_internal_transfers', 'exposure_diff_vs_parent', 'cash_share_diff_vs_parent', 'size_dev_pp', 'sector_active_max_pp',
            'status', 'boot60_lo', 'boot60_hi', 'D_imp_legacy_5e8_ann_pp', 'D_imp_curve_1e8_ann_pp', 'D_imp_curve_5e8_ann_pp']
REFS = (('parent_same_arm_exec_id', 'D_same_arm_ann_pp'), ('native_same_trigger_exec_id', 'D_native_same_trigger_ann_pp'), ('parent_h5_local_exec_id', 'D_h5_local_ann_pp'),
        ('parent_h5_global_exec_id', 'D_h5_global_ann_pp'), ('frontier_exec_id', 'D_frontier_ann_pp'), ('level_h20_ref_exec_id', 'D_level_h20_ann_pp'),
        ('cash_same_trigger_exec_id', 'D_cash_same_trigger_ann_pp'))
CMP_EXTRA = (('H5_GLOBAL_PARENT', 'parent_h5_global_exec_id'), ('H5_LOCAL_PARENT', 'parent_h5_local_exec_id'), ('FRONTIER_T1A_H20', 'frontier_exec_id'),
             ('LEVEL_H20_REFERENCE', 'level_h20_ref_exec_id'), ('CASH_SAME_TRIGGER', 'cash_same_trigger_exec_id'))
SER = ('ne', 'rnet', 'fullb', 'feefr', 'expo', 'cash', 'xprev', 'turn', 's05', 's07', 's10', 'impb', 'szk', 'sam', 'navpre', 'navpost', 'fee', 'nhold', 'nlots',
       'nexit', 'xshare', 'traded', 'n_reentry', 'n_internal', 'tag', 'lock', 'cashc', 'tku', 'ntkq', 'halfdn', 'buyv', 'sellv', 'tagnew', 'tagmat', 'usereg', 'useext',
       'secage_s', 'secage_n', 'fbimp', 'bench', 'navc')


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
        self.live = np.arange(self.T) < self.d_end
        self.root = root or O.work()
        R = O.read_csv(O.P('registration', 'registry_E6q.csv'), dtype=str).fillna('')
        self.R = R
        self.ids = list(R.exec_id)
        self.col = {e: j for j, e in enumerate(self.ids)}
        self.reg = R.set_index('exec_id', drop=False)
        self.Hh = np.array([int(h) for h in R.H])

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


def dy_series(DY, bench, V0=O.V0):
    I = E.DYI
    nav = DY[:, I['nav_post']]
    vprev = np.r_[V0, nav[:-1]]
    with np.errstate(all='ignore'):
        out = dict(ne=DY[:, I['net_excess']], rnet=DY[:, I['r_net']], fullb=DY[:, I['full_bench_ex']], feefr=DY[:, I['fee']] / vprev, expo=DY[:, I['exposure']],
                   cash=DY[:, I['cash_share']], xprev=DY[:, I['x_prev']], turn=0.5 * DY[:, I['traded']] / nav, s05=DY[:, I['cost_s05']], s07=DY[:, I['cost_s07']],
                   s10=DY[:, I['cost_s10']], impb=DY[:, I['impact_br']], szk=DY[:, I['sz_num']] / DY[:, I['sz_den']], sam=DY[:, I['sector_active_max']],
                   navpre=DY[:, I['nav_pre']], navpost=nav, fee=DY[:, I['fee']], nhold=DY[:, I['n_hold']], nlots=DY[:, I['n_lots']], nexit=DY[:, I['n_exits']],
                   xshare=DY[:, I['extra_val']], traded=DY[:, I['traded']], n_reentry=DY[:, I['n_reentry']], n_internal=DY[:, I['n_internal']], tag=DY[:, I['tag_amt']],
                   lock=DY[:, I['lock_amt']], cashc=DY[:, I['cash_close']], tku=DY[:, I['tk_usable_next']], ntkq=DY[:, I['n_tk_quar']], halfdn=DY[:, I['half_done_n']],
                   buyv=DY[:, I['buy_val']], sellv=DY[:, I['sell_val']], tagnew=DY[:, I['tag_new']], tagmat=DY[:, I['tag_matured']], usereg=DY[:, I['tag_use_reg']],
                   useext=DY[:, I['tag_use_ext']], secage_s=DY[:, I['sec_age_sum']], secage_n=DY[:, I['sec_age_n']], fbimp=DY[:, I['fb_impact']], bench=DY[:, I['bench']],
                   navc=DY[:, I['nav_close']])
    return out


def load_all(ctx):
    T, n = ctx.T, len(ctx.ids)
    S = {k: np.full((T, n), np.nan) for k in SER}
    acc = {}
    for r in ctx.R.itertuples(index=False):
        j = ctx.col[r.exec_id]
        z = np.load(acct_file(ctx, r.exec_hash), allow_pickle=False)
        DY = z['DY']
        nd = min(len(DY), ctx.d_end)
        ser = dy_series(DY[:nd], ctx.bench)
        for k, v in ser.items():
            col = np.full(T, np.nan)
            col[:nd] = v[:nd]
            S[k][:, j] = ctx.fake_rows(col)
        acc[r.exec_id] = dict(IN_i=z['IN_i'], IN_f=z['IN_f'], S_i=z['S_i'], HOLDH=z['HOLDH'], LOTH=z['LOTH'], DY=DY,
                              L_i=z['L_i'] if 'L_i' in z.files else None, L_f=z['L_f'] if 'L_f' in z.files else None)
    ok_all = np.isfinite(S['ne']).all(axis=1) & ctx.live
    ctx.masks = {s: (ctx.segi == s) & ok_all for s in SEG4}
    ctx.masks['FULL'] = ok_all
    ctx.support_days = int(ok_all.sum())
    return S, acc


# ------------------------------------------------------------------ 统计工具
def nw_se(D, L):
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
    """stationary bootstrap 计数矩阵 W (reps, n)：几何续块（均值块长 block），段内循环；W[r, i] = 第 r 次重抽中日 i 的出现次数。"""
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


class Boot(object):
    """按段、按块长缓存的 bootstrap 矩阵；FULL = 同一重抽序号下各段均值按段真实 n 合并。"""

    def __init__(self, ctx):
        self.ctx = ctx
        self.W = {}

    def mat(self, s, blk):
        k = (s, blk)
        if k not in self.W:
            n = int(self.ctx.masks[s].sum())
            self.W[k] = boot_matrix(n, REPS, blk, O.stable_u64('E6q', 'BOOT', s, blk) % (2 ** 32)) if n >= 30 else None
        return self.W[k]

    def seg_means(self, D, s, blk):
        """D：(T, A) 日差；返回 (REPS, A) 段内重抽均值（ann_pp）与段 n。"""
        m = self.ctx.masks[s]
        W = self.mat(s, blk)
        if W is None:
            return None, 0
        X = D[m]
        F = np.isfinite(X).astype(np.float32)
        X = np.where(np.isfinite(X), X, 0.0).astype(np.float32)
        with np.errstate(all='ignore'):
            return (W @ X) / (W @ F) * O.ANN_PP, int(m.sum())

    def ci(self, D, blk):
        """返回 {段: (lo, hi)}，含 FULL（按段 n 加权合并同序号重抽）。"""
        out = {}
        acc, ns = [], []
        for s in SEG4:
            bm, n = self.seg_means(D, s, blk)
            if bm is None:
                out[s] = (np.full(D.shape[1], np.nan), np.full(D.shape[1], np.nan))
                continue
            out[s] = (np.nanpercentile(bm, 2.5, axis=0), np.nanpercentile(bm, 97.5, axis=0))
            acc.append(bm * n)
            ns.append(n)
        if acc:
            full = sum(acc) / sum(ns)
            out['FULL'] = (np.nanpercentile(full, 2.5, axis=0), np.nanpercentile(full, 97.5, axis=0))
        return out


def dseg(X, s, j, k):
    """差的段读数：四段与 FULL 直接相减；G4 = 四段差的中位（plan §13.1"G4 是四段点估中位"；不是两个中位之差）。k = None → 绝对值。"""
    if s == 'G4':
        return float(np.median([X[t][j] - (X[t][k] if k is not None else 0.0) for t in SEG4]))
    return X[s][j] - (X[s][k] if k is not None else 0.0)


def ann_seg(X, ctx):
    """X：(T, A) → {段: (A,) ann_pp}；FULL = Σ n v / Σ n。"""
    out = {}
    num = 0.0
    den = 0
    for s in SEG4:
        m = ctx.masks[s]
        n = int(m.sum())
        with np.errstate(all='ignore'):
            v = np.nanmean(X[m], 0) * O.ANN_PP if n else np.full(X.shape[1], np.nan)
        out[s] = v
        num = num + np.nan_to_num(v) * n
        den += n
    out['FULL'] = num / den
    out['G4'] = np.median(np.vstack([out[s] for s in SEG4]), axis=0)
    return out


def mean_seg(X, ctx, scale=1.0):
    out = {}
    for s in SEG4 + ['FULL']:
        m = ctx.masks[s]
        with np.errstate(all='ignore'):
            out[s] = np.nanmean(X[m], 0) * scale
    out['G4'] = np.median(np.vstack([out[s] for s in SEG4]), axis=0)
    return out


def drawdown_cagr(nav, ctx):
    out = {}
    for s in SEG4 + ['FULL']:
        m = ctx.masks[s]
        x = nav[m]
        if len(x) < 2:
            out[s] = (np.nan, np.nan)
            continue
        peak = np.maximum.accumulate(x)
        dd = float(np.min(x / peak - 1.0))
        cg = float((x[-1] / x[0]) ** (252.0 / (len(x) - 1)) - 1.0)
        out[s] = (dd, cg)
    out['G4'] = (float(np.median([out[s][0] for s in SEG4])), float(np.median([out[s][1] for s in SEG4])))
    return out


# ------------------------------------------------------------------ 事件
def event_counts(ctx, a, s):
    """段内事件计数（意向日 / 成交日落在段内；段末待成交：意向日 + 1 ≥ 授权末日 → 右删失，否则未成交）；n_intents = early + late + unfilled + censored（FULL 恒等）。"""
    out = dict(n_exit_intents=0, n_realized_early=0, n_late_fill=0, n_unfilled=0, n_censored=0)
    if a is None or ctx.fake:
        return out
    IN = a['IN_i']
    real = np.isin(IN[:, E.IN_KIND], [E.KD_TRIG, E.KD_REARM, E.KD_RAND])
    IN = IN[real]
    dd = IN[:, E.IN_DAY]
    ex = IN[:, E.IN_EXEC]
    st = IN[:, E.IN_STATUS]
    segm = (ctx.segi == s) if s in SEG4 else np.ones(ctx.T, bool)
    in_s = segm[np.clip(dd, 0, ctx.T - 1)] & (dd < ctx.d_end)
    pend = (st == 0) & in_s
    cens = pend & (dd + 1 >= ctx.d_end)
    out.update(n_exit_intents=int(in_s.sum()), n_realized_early=int(((st == 1) & in_s).sum()), n_late_fill=int(((st == 2) & in_s).sum()),
               n_unfilled=int((pend & ~cens).sum()), n_censored=int(cens.sum()))
    return out


# ------------------------------------------------------------------ 账户汇总（B.10）
def summary(ctx, S, acc, boot):
    R = ctx.R
    n = len(ctx.ids)
    ne = S['ne']
    idx = {c: np.array([ctx.col.get(e, -1) if e else -1 for e in R[c]]) for c, _ in REFS}
    par = idx['parent_same_arm_exec_id']
    okp = par >= 0
    net = ann_seg(ne, ctx)
    absn = ann_seg(S['rnet'], ctx)
    fullb = ann_seg(S['fullb'], ctx)
    fee = ann_seg(S['feefr'], ctx)
    gross = ann_seg(ne + S['feefr'], ctx)
    expo = mean_seg(S['expo'], ctx)
    cash = mean_seg(S['cash'], ctx)
    turn = mean_seg(S['turn'], ctx, 252.0)
    sam = mean_seg(S['sam'], ctx)
    szk = S['szk']
    dsz = np.full_like(ne, np.nan)
    dsz[:, okp] = (szk[:, okp] - szk[:, par[okp]]) * 100.0
    dszs = mean_seg(dsz, ctx)
    xm = np.full_like(ne, np.nan)
    xm[:, okp] = np.minimum(S['xprev'][:, okp], S['xprev'][:, par[okp]])
    with np.errstate(all='ignore'):
        scc = np.where(S['xprev'] > 0, ne * xm / S['xprev'], 0.0)
        scp = np.full_like(ne, np.nan)
        scp[:, okp] = np.where(S['xprev'][:, par[okp]] > 0, ne[:, par[okp]] * xm[:, okp] / S['xprev'][:, par[okp]], 0.0)
    Dsc = ann_seg(np.where(okp[None, :], scc - scp, np.nan), ctx)
    Dp = np.full_like(ne, np.nan)
    Dp[:, okp] = ne[:, okp] - ne[:, par[okp]]
    imp_leg = 0.5 * math.sqrt(5e8) * np.nan_to_num(S['impb'])
    imp_c1 = 0.5 * (1e8 ** 0.5) * np.nan_to_num(S['s05'])
    imp_c5 = 0.5 * (5e8 ** 0.5) * np.nan_to_num(S['s05'])
    Dimp = {}
    for nm, imp in (('leg', imp_leg), ('c1', imp_c1), ('c5', imp_c5)):
        X = np.full_like(ne, np.nan)
        X[:, okp] = (ne[:, okp] - imp[:, okp]) - (ne[:, par[okp]] - imp[:, par[okp]])
        Dimp[nm] = ann_seg(X, ctx)
    se = {k: {} for k in ('H', '20', '60')}
    for s in SEG4 + ['FULL']:
        m = ctx.masks[s]
        Dm = Dp[m]
        for lag in ('H', '20', '60'):
            v = np.full(n, np.nan)
            for hv in np.unique(ctx.Hh):
                L = max(20, 2 * hv) if lag == 'H' else int(lag)
                cols = (ctx.Hh == hv) & okp
                if cols.any() and Dm.shape[0] > L + 2:
                    v[cols] = nw_se(Dm[:, cols], L) * O.ANN_PP
            se[lag][s] = v
    bci = {}
    bci60 = {}
    for hv in np.unique(ctx.Hh):
        cols = np.flatnonzero((ctx.Hh == hv) & okp)
        if not len(cols):
            continue
        c1 = boot.ci(Dp[:, cols], max(20, 2 * int(hv)))
        c2 = boot.ci(Dp[:, cols], 60)
        for s in SEG4 + ['FULL']:
            bci.setdefault(s, (np.full(n, np.nan), np.full(n, np.nan)))
            bci60.setdefault(s, (np.full(n, np.nan), np.full(n, np.nan)))
            bci[s][0][cols], bci[s][1][cols] = c1[s]
            bci60[s][0][cols], bci60[s][1][cols] = c2[s]
    rows = []
    for j, e in enumerate(ctx.ids):
        r = R.iloc[j]
        nav = S['navpost'][:, j]
        ddc = drawdown_cagr(nav, ctx)
        a = acc.get(e)
        Si = a['S_i'] if a is not None else np.zeros(E.NSI, np.int64)
        for s in SEG6:
            nd = int(ctx.masks[s].sum()) if s != 'G4' else ''
            row = dict(exec_id=e, scenario=r.scenario, segment=s, support=O.SUPPORT, n_days=nd, net_ann_pp=net[s][j], abs_net_ann_pp=absn[s][j],
                       full_bench_excess_ann_pp=fullb[s][j], gross_ann_pp=gross[s][j], fee_ann_pp=fee[s][j], exposure_mean=expo[s][j], cash_share_mean=cash[s][j],
                       turnover_ann=turn[s][j], max_drawdown_total=ddc[s][0], cagr_total=ddc[s][1], sector_active_max_pp=sam[s][j], status='COMPUTED',
                       parent_same_arm_exec_id=r.parent_same_arm_exec_id, native_same_trigger_exec_id=r.native_same_trigger_exec_id)
            for c, dcol in REFS:
                k = idx[c][j]
                if k >= 0:
                    row[dcol] = dseg(net, s, j, k)
            if okp[j]:
                k = par[j]
                row.update(parent_same_arm_net_ann_pp=net[s][k], D_sc_ann_pp=Dsc[s][j], size_dev_pp=dszs[s][j], exposure_diff_vs_parent=expo[s][j] - expo[s][k],
                           cash_share_diff_vs_parent=cash[s][j] - cash[s][k], D_imp_legacy_5e8_ann_pp=Dimp['leg'][s][j], D_imp_curve_1e8_ann_pp=Dimp['c1'][s][j],
                           D_imp_curve_5e8_ann_pp=Dimp['c5'][s][j])
                if s != 'G4':
                    row.update(hac_se_H=se['H'][s][j], hac_se_20=se['20'][s][j], hac_se_60=se['60'][s][j], boot_lo=bci[s][0][j], boot_hi=bci[s][1][j],
                               boot60_lo=bci60[s][0][j], boot60_hi=bci60[s][1][j])
            k = idx['native_same_trigger_exec_id'][j]
            if k >= 0:
                row['native_same_trigger_net_ann_pp'] = net[s][k]
            if s != 'G4':
                row.update(event_counts(ctx, a, s))
                row.update(n_deadline_overrides=int(Si[E.SI_OVERRIDE]) if s == 'FULL' else '', n_half_requests=int(Si[E.SI_HALF]) if s == 'FULL' else '',
                           n_rearm_episodes=int(Si[E.SI_REARMN]) if s == 'FULL' else '')
                m = ctx.masks[s]
                row['n_reentries'] = int(np.nansum(S['n_reentry'][m, j]))
                row['n_internal_transfers'] = int(np.nansum(S['n_internal'][m, j]))
                if s != 'FULL':
                    row['n_deadline_overrides'] = int(np.nansum(acc[e]['DY'][m[:len(acc[e]['DY'])], E.DY_M3OVR])) if a is not None else ''
                    row['n_half_requests'] = int(np.nansum(acc[e]['DY'][m[:len(acc[e]['DY'])], E.DY_HALFST])) if a is not None else ''
                    row['n_rearm_episodes'] = int(np.nansum(acc[e]['DY'][m[:len(acc[e]['DY'])], E.DY_REARM])) if a is not None else ''
            rows.append(row)
    Sm = pd.DataFrame(rows, columns=SUM_COLS)
    return Sm, net


# ------------------------------------------------------------------ 比较结果（B.11）
def comparison_results(ctx, S, net, boot):
    C = O.read_csv(O.P('registration', 'comparisons_E6q.csv'), dtype=str).fillna('')
    L = np.array([ctx.col[e] for e in C.left_exec_id])
    Rr = np.array([ctx.col[e] for e in C.right_exec_id])
    ne = S['ne']
    D = ne[:, L] - ne[:, Rr]
    imp1 = 0.5 * (1e8 ** 0.5) * np.nan_to_num(S['s05'])
    imp5 = 0.5 * (5e8 ** 0.5) * np.nan_to_num(S['s05'])
    c1 = ann_seg((ne[:, L] - imp1[:, L]) - (ne[:, Rr] - imp1[:, Rr]), ctx)
    c5 = ann_seg((ne[:, L] - imp5[:, L]) - (ne[:, Rr] - imp5[:, Rr]), ctx)
    blk = np.maximum(20, 2 * np.maximum(ctx.Hh[L], ctx.Hh[Rr]))
    lo = {s: np.full(len(C), np.nan) for s in SEG4 + ['FULL']}
    hi = {s: np.full(len(C), np.nan) for s in SEG4 + ['FULL']}
    for b in np.unique(blk):
        cols = np.flatnonzero(blk == b)
        ci = boot.ci(D[:, cols], int(b))
        for s in SEG4 + ['FULL']:
            lo[s][cols], hi[s][cols] = ci[s]
    rows = []
    for i, c in enumerate(C.itertuples(index=False)):
        for s in SEG6:
            Dv = net[s][L[i]] - net[s][Rr[i]] if s != 'G4' else float(np.median([net[x][L[i]] - net[x][Rr[i]] for x in SEG4]))
            rows.append(dict(comparison_id=c.comparison_id, kind=c.kind, left_exec_id=c.left_exec_id, right_exec_id=c.right_exec_id, segment=s, D_ann_pp=Dv,
                             boot_lo=lo[s][i] if s != 'G4' else '', boot_hi=hi[s][i] if s != 'G4' else '', D_cost_1e8_ann_pp=c1[s][i], D_cost_5e8_ann_pp=c5[s][i],
                             status='COMPUTED', interpretation=c.interpretation))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 逐年（B.15）
def yearly(ctx, S):
    R = ctx.R
    rows = []
    ne = S['ne']
    sup = ctx.masks['FULL']
    for j, e in enumerate(ctx.ids):
        r = R.iloc[j]
        p = ctx.col.get(r.parent_same_arm_exec_id, -1) if r.parent_same_arm_exec_id else -1
        for y in YEARS:
            m = (ctx.years == y) & sup
            if not m.any():
                rows.append(dict(exec_id=e, scenario=r.scenario, year=y, n_days=0, partial_year_flag=1 if y == 2026 else 0, status='NOT_RUN'))
                continue
            v = float(np.mean(ne[m, j]) * O.ANN_PP)
            row = dict(exec_id=e, scenario=r.scenario, year=y, n_days=int(m.sum()), net_ann_pp=v, partial_year_flag=1 if y == 2026 else 0, status='COMPUTED')
            if p >= 0:
                pv = float(np.mean(ne[m, p]) * O.ANN_PP)
                row.update(parent_same_arm_net_ann_pp=pv, D_same_arm_ann_pp=v - pv)
            rows.append(row)
    return pd.DataFrame(rows, columns=['exec_id', 'scenario', 'year', 'n_days', 'net_ann_pp', 'parent_same_arm_net_ann_pp', 'D_same_arm_ann_pp', 'partial_year_flag', 'status'])


# ------------------------------------------------------------------ 成本曲线 / 盈亏平衡（B.16）
def cost_tables(ctx, S):
    R = ctx.R
    n = len(ctx.ids)
    ne = S['ne']
    fee = S['feefr']
    p32 = (R.is_primary32 == '1').to_numpy()
    ref = {'SAME_ARM_PARENT': np.array([ctx.col.get(e, -1) if e else -1 for e in R.parent_same_arm_exec_id]),
           'SAME_TRIGGER_NATIVE': np.array([ctx.col.get(e, -1) if e else -1 for e in R.native_same_trigger_exec_id])}
    for ck, c in CMP_EXTRA:
        ref[ck] = np.array([(ctx.col.get(e, -1) if (e and p32[j]) else -1) for j, e in enumerate(R[c])])
    seg_a = {}
    for x in O.EXPONENTS + (0.5,):
        seg_a[('S', x)] = ann_seg(np.nan_to_num(S[SCOL[x]]), ctx)
    g_ne = ann_seg(ne + fee, ctx)
    g_fee = ann_seg(fee, ctx)
    g_net = ann_seg(ne, ctx)
    rows = []
    brows = []
    kinds = [('ABSOLUTE', None)] + [(k, ref[k]) for k in ('SAME_ARM_PARENT', 'SAME_TRIGGER_NATIVE') + tuple(ck for ck, _ in CMP_EXTRA)]
    for ck, rv in kinds:
        js = np.arange(n) if rv is None else np.flatnonzero(rv >= 0)
        for j in js:
            k = None if rv is None else int(rv[j])
            e = ctx.ids[j]
            cid = '' if k is None else ctx.ids[k]
            for s in SEG6:
                gd = dseg(g_ne, s, j, k)
                fd = dseg(g_fee, s, j, k)
                for (A_, kp, x) in GRID + ([(A_, 0.3, x) for A_ in O.A_GRID for x in O.EXPONENTS] if p32[j] else []):
                    Sx = seg_a[('S', x)]
                    imp = kp * (A_ ** x) * dseg(Sx, s, j, k)
                    if s == 'G4':
                        na = float(np.median([dseg(g_ne, t, j, k) - dseg(g_fee, t, j, k) - kp * (A_ ** x) * dseg(Sx, t, j, k) for t in SEG4]))
                    else:
                        na = gd - fd - imp
                    rows.append(dict(exec_id=e, scenario=R.scenario.iloc[j], comparator_kind=ck, comparator_exec_id=cid, A_cny=int(A_), kappa=kp, exponent=x, segment=s,
                                     gross_diff_ann_pp=gd, fee_diff_ann_pp=fd, impact_diff_ann_pp=imp, net_after_impact_diff_ann_pp=na,
                                     status='SCENARIO_NOT_CALIBRATED' if kp == 0.3 else 'COMPUTED'))
            for kp in O.KAPPAS:
                for x in O.EXPONENTS:
                    a_ = g_net['FULL'][j] - (g_net['FULL'][k] if k is not None else 0.0)
                    Sx = seg_a[('S', x)]['FULL']
                    b_ = kp * (1e8 ** x) * (Sx[j] - (Sx[k] if k is not None else 0.0))
                    root, kind = CO.root_status(float(a_), float(b_), x, 1e8)
                    if kind == 'POSITIVE_ROOT' or kind == 'LOWER_CROSSING':
                        if not (O.A_GRID[0] <= root <= O.A_GRID[-1]):
                            kind = 'OUT_OF_GRID'
                    brows.append(dict(exec_id=e, scenario=R.scenario.iloc[j], comparator_kind=ck, comparator_exec_id=cid, kappa=kp, exponent=x, a_coeff=a_, b_coeff=b_,
                                      root_kind=kind, breakeven_A_cny=root if root is not None else '', status='COMPUTED'))
    return pd.DataFrame(rows), pd.DataFrame(brows)


# ------------------------------------------------------------------ 反馈（B.16）
def feedback_tables(ctx, S, net):
    import e6q_run as RN
    F = O.read_csv(O.P('registration', 'cost_feedback_refs_E6q.csv'), dtype=str).fillna('')
    P = O.read_csv(O.P('registration', 'feedback_comparisons_E6q.csv'), dtype=str).fillna('')
    T = ctx.T
    fne = {}
    for f in F.itertuples(index=False):
        h = RN.fb_hash(f.owner_exec_id, int(f.A0_cny))
        z = np.load(acct_file(ctx, h, 'fb'), allow_pickle=False)
        DY = z['DY']
        nd = min(len(DY), ctx.d_end)
        col = np.full(T, np.nan)
        col[:nd] = DY[:nd, E.DYI['net_excess']]
        fne[f.feedback_id] = ctx.fake_rows(col)
    ids = list(fne)
    M = np.column_stack([fne[i] for i in ids])
    fa = ann_seg(M, ctx)
    pos = {i: k for k, i in enumerate(ids)}
    ne = S['ne']
    rows = []
    for f in F.itertuples(index=False):
        k = pos[f.feedback_id]
        kp = pos[f.parent_feedback_id]
        oj = ctx.col[f.owner_exec_id]
        pj = ctx.col[O.exec_id(F.set_index('feedback_id').loc[f.parent_feedback_id].owner_logical_id, 'FEASIBLE_DAILY')]
        A_ = float(f.A0_cny)
        imp = 0.5 * (A_ ** 0.5) * np.nan_to_num(S['s05'])
        fx = ann_seg((ne[:, [oj]] - imp[:, [oj]]) - (ne[:, [pj]] - imp[:, [pj]]), ctx)
        for s in SEG6:
            rows.append(dict(feedback_id=f.feedback_id, owner_exec_id=f.owner_exec_id, A0_cny=int(A_), kappa=float(f.kappa), exponent=float(f.exponent), segment=s,
                             net_ann_pp_feedback=fa[s][k], parent_feedback_id=f.parent_feedback_id, parent_net_ann_pp_feedback=fa[s][kp],
                             D_feedback_ann_pp=dseg(fa, s, k, kp), D_fixed_path_ann_pp=float(fx[s][0]), status='COMPUTED'))
    prow = []
    for p in P.itertuples(index=False):
        k, k2 = pos[p.feedback_id], pos[p.right_feedback_id]
        for s in SEG6:
            prow.append(dict(feedback_id=p.feedback_id, kind=p.kind, right_feedback_id=p.right_feedback_id, segment=s, D_feedback_pair_ann_pp=dseg(fa, s, k, k2),
                             status='COMPUTED'))
    return pd.DataFrame(rows), pd.DataFrame(prow)


# ------------------------------------------------------------------ 密度（B.16）
def density_table(ctx, S):
    R = ctx.R
    ne = S['ne']
    turn = mean_seg(S['turn'], ctx, 252.0)
    expo = mean_seg(S['expo'], ctx)
    g_net = ann_seg(ne, ctx)
    sa = {x: ann_seg(np.nan_to_num(S[SCOL[x]]), ctx) for x in O.DENSITY_EXP}
    rows = []
    for j, r in enumerate(R.itertuples(index=False)):
        if r.is_primary32 != '1':
            continue
        for rk, ref in (('CASH_SAME_TRIGGER', r.cash_same_trigger_exec_id), ('SAME_ARM_PARENT', r.parent_same_arm_exec_id)):
            if not ref:
                continue
            k = ctx.col[ref]
            for A_ in O.DENSITY_A:
                for kp in O.KAPPAS:
                    for x in O.DENSITY_EXP:
                        for s in SEG6:
                            dnet = dseg(g_net, s, j, k)
                            dimp = kp * (A_ ** x) * dseg(sa[x], s, j, k)
                            dturn = dseg(turn, s, j, k)
                            dexp = dseg(expo, s, j, k)
                            v, c, st = RU.density(float(dnet), float(dimp), float(dturn), eps=1e-3)
                            rows.append(dict(exec_id=r.exec_id, reference_kind=rk, reference_exec_id=ref, A_cny=int(A_), kappa=kp, exponent=x, segment=s, d_net8_ann_pp=dnet,
                                             d_impact_ann_pp=dimp, d_turn=dturn, d_exposure=dexp, value_density=v if v is not None else '', cost_density=c if c is not None else '',
                                             denominator_status=st, status='COMPUTED'))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 事件表 / 请求表（B.19）
def event_tables(ctx, S, acc, trades_meta):
    R = ctx.R
    rows, rq = [], []
    for j, r in enumerate(R.itertuples(index=False)):
        a = acc[r.exec_id]
        Si = a['S_i']
        ev = event_counts(ctx, a, 'FULL')
        H = a['HOLDH'].astype(float)
        Lh = a['LOTH'].astype(float)
        mle = float((np.arange(len(H)) * H).sum() / H.sum()) if H.sum() > 0 else ''
        mla = float((np.arange(len(Lh)) * Lh).sum() / Lh.sum()) if Lh.sum() > 0 else ''
        cum = np.cumsum(Lh)
        med = int(np.searchsorted(cum, cum[-1] / 2.0)) if Lh.sum() > 0 else ''
        sa = np.nansum(S['secage_s'][:, j])
        sn = np.nansum(S['secage_n'][:, j])
        lc = int(Si[E.SI_LCLOSED])
        ld = int(Si[E.SI_LDUE])
        half = r.arm.startswith('EXIT_HALF')
        rows.append(dict(exec_id=r.exec_id, trigger=r.trigger, arm=r.arm, n_intents=ev['n_exit_intents'], n_realized_early=ev['n_realized_early'], n_late_fill=ev['n_late_fill'],
                         n_unfilled=ev['n_unfilled'], n_censored=ev['n_censored'], n_no_action_opportunity=int(Si[E.SI_NOACT]), n_deadline_overrides=int(Si[E.SI_OVERRIDE]),
                         n_half_requests=int(Si[E.SI_HALF]) if half else 0, n_rearm_episodes=int(Si[E.SI_REARMN]) if r.arm == 'EXIT_HALF_REARM' else 0,
                         n_reentries=int(Si[E.SI_REENTRY]), n_internal_transfers=int(Si[E.SI_INTERNAL]), n_new_name_empty_days=int(Si[E.SI_NEWEMPTY]),
                         n_quarantined_tokens=int(Si[E.SI_QUAR]), mean_lot_age_realized_early=mle, mean_lot_age_all_lots=mla, median_lot_age_all_lots=med,
                         mean_security_age=float(sa / sn) if sn > 0 else '', share_lots_reaching_due=float(ld / lc) if lc > 0 else '', status='COMPUTED'))
        if r.arm.startswith('EXIT_GATE_LIQ') and r.trigger != 'NONE':
            tm = trades_meta.get(r.exec_id, {})
            IN = a['IN_i']
            m = np.isin(IN[:, E.IN_KIND], [E.KD_TRIG])
            st = IN[m, E.IN_STATUS]
            rid = np.flatnonzero(m)
            forced = tm.get('forced_requests', set())
            fset = np.array([k in forced for k in rid], bool)
            before = int(((st == 1) & ~fset).sum())
            nf = int(fset.sum())
            after = int(len(st) - before - nf)
            ex = IN[m, E.IN_EXEC]
            dd = IN[m, E.IN_DAY]
            done = ex >= 0
            rq.append(dict(exec_id=r.exec_id, n_requests=int(len(st)), n_completed_before_deadline=before, n_forced_deadline_override=nf, n_completed_after_due_objective=after,
                           mean_days_to_complete=float(np.mean(ex[done] - dd[done])) if done.any() else '', qty_share_delayed=tm.get('qty_share_delayed', ''), status='COMPUTED'))
    return pd.DataFrame(rows), pd.DataFrame(rq, columns=['exec_id', 'n_requests', 'n_completed_before_deadline', 'n_forced_deadline_override', 'n_completed_after_due_objective',
                                                          'mean_days_to_complete', 'qty_share_delayed', 'status'])


# ------------------------------------------------------------------ 日序列 / 成交导出（B.21）
DAILY_COLS = ['date', 'nav_pre', 'nav_post', 'fee', 'exposure', 'cash_share', 'cash_untagged_share', 'cash_available_share', 'bench_ret', 'net_excess_ret', 'abs_net_ret',
              'full_bench_excess_ret', 'n_holdings', 'n_lots', 'n_exits_today', 'n_half_exits_today', 'n_quarantined_tokens', 'extra_batch_share', 'turnover_day']
TRADE_COLS = ['date', 'security', 'lot_id', 'request_id', 'order_kind', 'side', 'qty', 'notional_cny', 'price', 'fee_cny', 'lot_due', 'deadline', 'planned_p', 'realized_p']
G = {}


def _exp_init(ctx_info):
    G.update(ctx_info)


def job_export(args):
    eid, h, aref = args
    dates, codes, T, sup = G['dates'], G['codes'], G['T'], G['sup']
    z = np.load(O.P('accounts_run', G.get('asub', 'full'), h[:2], '%s.npz' % h), allow_pickle=False)
    DY = z['DY']
    s = dy_series(DY, None)
    nav = s['navpost']
    keep = np.flatnonzero(sup[:len(DY)])
    vprev_row = np.r_[O.V0, nav[keep][:-1]]
    with np.errstate(all='ignore'):
        absr = nav[keep] / vprev_row - 1.0
        untag = (s['cashc'] - s['tag'] - s['lock']) / nav
        avail = (s['cashc'] - s['tag'] - s['lock'] + s['tku']) / nav
    D = pd.DataFrame(dict(date=dates[keep], nav_pre=s['navpre'][keep], nav_post=nav[keep], fee=s['fee'][keep], exposure=s['expo'][keep], cash_share=s['cash'][keep],
                          cash_untagged_share=untag[keep], cash_available_share=avail[keep], bench_ret=DY[keep, E.DYI['bench']], net_excess_ret=s['ne'][keep],
                          abs_net_ret=absr, full_bench_excess_ret=absr - DY[keep, E.DYI['bench']], n_holdings=s['nhold'][keep].astype(int), n_lots=s['nlots'][keep].astype(int),
                          n_exits_today=s['nexit'][keep].astype(int), n_half_exits_today=s['halfdn'][keep].astype(int), n_quarantined_tokens=s['ntkq'][keep].astype(int),
                          extra_batch_share=s['xshare'][keep], turnover_day=s['turn'][keep]), columns=DAILY_COLS)
    pd_ = os.path.join(G['out_root'], 'accounts', 'daily', '%s.csv' % h)
    O.atomic_write_csv(pd_, D)
    tzs = [np.load(O.P('trades_parts', s_, h[:2], '%s.npz' % h), allow_pickle=False) for s_ in G.get('tsubs', ('deriv', 'full'))]
    TLi = np.concatenate([t_['TL_i'] for t_ in tzs])
    TLf = np.concatenate([t_['TL_f'] for t_ in tzs])
    adv = G['adv20']
    pc = G['pc']
    day = TLi[:, 0]
    sec = TLi[:, 1]
    scale = (aref if aref > 0 else 1e8) / O.V0
    with np.errstate(all='ignore'):
        a_e = np.asarray(adv[day, sec])
        realized = TLf[:, 1] * scale / a_e
        planned = np.where(np.isfinite(TLf[:, 4]), TLf[:, 4] * scale / np.asarray(adv[np.maximum(day - 1, 0), sec]), np.nan)
    due = TLi[:, 6]
    dl = TLi[:, 7]
    kind = np.array([OKN.get(int(k), 'REGULAR') for k in TLi[:, 4]])
    lot_due = np.where(np.isin(kind, ['EXIT', 'EXIT_HALF', 'EXIT_REARM', 'DUE', 'DEADLINE_OVERRIDE']),
                       np.where(due >= T, 'POST_CUTOFF', np.array([dates[min(int(x), T - 1)] if x >= 0 else '' for x in due])), '')
    dls = np.where(dl >= 0, np.where(dl >= T, 'POST_CUTOFF', np.array([dates[min(int(x), T - 1)] if x >= 0 else '' for x in dl])), '')
    Tr = pd.DataFrame(dict(date=dates[day], security=codes[sec], lot_id=TLi[:, 2], request_id=np.where(TLi[:, 3] >= 0, TLi[:, 3].astype(str), ''), order_kind=kind,
                           side=np.where(TLi[:, 5] == 0, 'BUY', 'SELL'), qty=TLf[:, 0], notional_cny=TLf[:, 1], price=TLf[:, 2], fee_cny=TLf[:, 3], lot_due=lot_due,
                           deadline=dls, planned_p=planned, realized_p=realized), columns=TRADE_COLS)
    pt = os.path.join(G['out_root'], 'trades', '%s.csv' % h)
    O.atomic_write_csv(pt, Tr)
    # 门控请求元数据：强制完成的请求、首日未卖出份额
    meta = {}
    if np.any(kind == 'DEADLINE_OVERRIDE'):
        meta['forced_requests'] = set(int(x) for x in TLi[kind == 'DEADLINE_OVERRIDE', 3] if x >= 0)
    ex = np.isin(kind, ['EXIT', 'DEADLINE_OVERRIDE']) & (TLi[:, 3] >= 0)
    if ex.any():
        df = pd.DataFrame(dict(rq=TLi[ex, 3], day=day[ex], qty=TLf[ex, 0]))
        first = df.groupby('rq').day.transform('min')
        tot = df.qty.sum()
        meta['qty_share_delayed'] = float(df.qty[df.day > first].sum() / tot) if tot > 0 else ''
    return dict(exec_id=eid, exec_hash=h, daily_rows=len(D), date_min=str(D.date.iloc[0]), date_max=str(D.date.iloc[-1]), trade_rows=len(Tr),
                n_fills=int((Tr.qty > 0).sum()), meta=meta)


def exports(ctx, workers, asub='full', tsubs=('deriv', 'full'), only=None):
    """日序列 / 成交导出（B 相：accounts_run/full + trades_parts deriv + full；空跑 --dry_extras：推导段文件，写到空跑根）。"""
    R = ctx.R
    for d in (os.path.join(ctx.root, 'accounts', 'daily'), os.path.join(ctx.root, 'trades')):
        os.makedirs(d, exist_ok=True)
    info = dict(dates=ctx.dates, codes=ctx.codes, T=ctx.T, sup=ctx.masks['FULL'], adv20=np.load(os.path.join(ctx.cd, 'panels', 'adv20.npy'), mmap_mode='r'),
                pc=np.load(os.path.join(ctx.cd, 'panels', 'pc_ff.npy'), mmap_mode='r'), out_root=ctx.root, asub=asub, tsubs=tsubs)
    jobs = [(r.exec_id, r.exec_hash, float(r.A_ref) if r.A_ref else 0.0) for r in R.itertuples(index=False) if only is None or r.exec_id in only]
    ctxm = get_context('fork')
    with ctxm.Pool(min(workers, len(jobs)), initializer=_exp_init, initargs=(info,)) as pool:
        out = list(pool.imap_unordered(job_export, jobs))
    di = pd.DataFrame([dict(exec_hash=x['exec_hash'], exec_id=x['exec_id'], file='accounts/daily/%s.csv' % x['exec_hash'], n_rows=x['daily_rows'], date_min=x['date_min'],
                            date_max=x['date_max']) for x in out]).sort_values('exec_id')
    ti = pd.DataFrame([dict(exec_id=x['exec_id'], file='trades/%s.csv' % x['exec_hash'], n_rows=x['trade_rows'], n_fills=x['n_fills']) for x in out]).sort_values('exec_id')
    O.atomic_write_csv(os.path.join(ctx.root, 'accounts', 'daily', 'INDEX.csv'), di)
    O.atomic_write_csv(os.path.join(ctx.root, 'trades', 'INDEX.csv'), ti)
    return {x['exec_id']: x['meta'] for x in out}


# ------------------------------------------------------------------ 随机 / 匹配（B.12）
def randoms_tables(ctx, S, net, tags=('B', 'B_topup')):
    R = ctx.R
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6q.csv'), dtype=str).fillna('')
    parts = [pd.read_csv(O.P('randoms', 'random_paths_%s.csv' % t), keep_default_na=False, na_values=['']) for t in tags
             if os.path.exists(O.P('randoms', 'random_paths_%s.csv' % t)) and os.path.getsize(O.P('randoms', 'random_paths_%s.csv' % t)) > 5]
    P = pd.concat(parts, ignore_index=True)
    P = P[P.status == 'OK'].drop_duplicates(['owner_exec_id', 'mechanism', 'path_id'])
    byid = R.set_index('exec_id', drop=False)
    rows, mrows, prows = [], [], []
    for ref in RR.itertuples(index=False):
        e = ref.owner_exec_id
        j = ctx.col[e]
        p = ctx.col[byid.loc[e].parent_same_arm_exec_id]
        X = P[(P.owner_exec_id == e) & (P.mechanism == ref.mechanism)].sort_values('path_id')
        npth = len(X)
        mt = float(ref.mcse_target) if ref.mcse_target else None
        fd = full_D(X) if npth else np.array([])
        for s in SEG6:
            real = net[s][j] - net[s][p]
            if s == 'FULL':
                v = fd
            elif s == 'G4':
                v = np.median(np.vstack([X['D_%s' % x].to_numpy(float) for x in SEG4]), axis=0) if npth else np.array([])
            else:
                v = X['D_%s' % s].to_numpy(float)
            v = v[np.isfinite(v)]
            mean = float(np.mean(v)) if len(v) else np.nan
            sd = float(np.std(v, ddof=1)) if len(v) > 1 else np.nan
            mcse = sd / math.sqrt(len(v)) if len(v) > 1 else np.nan
            rank = float((np.sum(v < real) + 0.5 * np.sum(v == real)) / len(v)) if len(v) else np.nan
            segs = SEG4 if s in ('FULL', 'G4') else [s]
            req = sum(X['req_%s' % x].sum() for x in segs) if npth else 0.0
            unm = sum(X['unm_%s' % x].sum() for x in segs) if npth else 0.0
            ush = float(unm / req) if req > 0 else np.nan
            pint = sum(X['pint_%s' % x].sum() for x in segs) if npth else 0
            oint = sum(X['oint_%s' % x].iloc[0] for x in segs) * npth if npth else 0
            iratio = float(pint / oint) if oint > 0 else np.nan
            rt = ref.mechanism.startswith('RANDOM_TARGET')
            if rt and npth:
                lim = sum(X['rtlim_%s' % x].sum() for x in segs)
                nom = sum(X['rtnom_%s' % x].sum() for x in segs)
                ide = sum(X['rtid_%s' % x].sum() for x in segs)
                fea = sum(X['rtfeas_%s' % x].sum() for x in segs)
                tot = lim + nom + ide + fea
                ms = 'ALGORITHM_LIMIT' if lim > 0 else ('PROVED_NO_MATCH' if nom > 0 else ('IDENTITY_TARGET_CONTROL' if (tot > 0 and ide == tot) else 'FEASIBLE'))
                tss = float(sum(X['list_%s' % x].sum() for x in segs) / max(1, sum(int(ctx.masks[x].sum()) for x in segs) * npth))
                lim_share = float((lim + nom) / tot) if tot > 0 else 0.0
            else:
                ms, tss, lim_share = 'NOT_APPLICABLE', '', 0.0
            comp = 'COMPARABLE'
            if ref.mechanism in ('AMOUNT_MATCH_V2', 'COUNT_ISK', 'AMOUNT_ISK_V2') and np.isfinite(ush) and ush > O.NOT_COMPARABLE_UNMATCHED:
                comp = 'CONTROL_NOT_COMPARABLE'
            if ref.mechanism == 'BERNOULLI_FIRSTHIT' and np.isfinite(iratio) and not (O.INTENSITY_BAND[0] <= iratio <= O.INTENSITY_BAND[1]):
                comp = 'CONTROL_NOT_COMPARABLE'
            if rt and lim_share > 0.25:
                comp = 'CONTROL_NOT_COMPARABLE'
            st = 'COMPUTED'
            if mt is not None and ref.mechanism != 'LEVEL_WORST_1D' and s == 'FULL' and npth >= int(ref.max_paths) and np.isfinite(mcse) and mcse > mt:
                st = 'MC_LIMIT'
            rows.append(dict(owner_exec_id=e, mechanism=ref.mechanism, segment=s, paths=npth, start_paths=int(ref.start_paths), max_paths=int(ref.max_paths),
                             mcse_target=ref.mcse_target, real_D_ann_pp=real, rand_mean_D_ann_pp=mean, rand_sd_D_ann_pp=sd if npth > 1 else '', mcse=mcse if npth > 1 else '',
                             rank_real=rank, unmatched_share=ush if ref.mechanism in ('AMOUNT_MATCH_V2', 'COUNT_ISK', 'AMOUNT_ISK_V2', 'LEVEL_WORST_1D') else '',
                             intensity_ratio=iratio if ref.mechanism == 'BERNOULLI_FIRSTHIT' else '', target_set_size=tss, match_status=ms, control_comparability=comp,
                             status=st, first128_mean_D_ann_pp=float(np.mean(fd[:128][np.isfinite(fd[:128])])) if (s == 'FULL' and npth) else '',
                             limit_day_share=lim_share if rt else ''))
            if ref.mechanism in ('AMOUNT_MATCH_V2', 'COUNT_ISK', 'AMOUNT_ISK_V2', 'LEVEL_WORST_1D') and s != 'G4':
                wi = sum(X['within_%s' % x].sum() for x in segs) if npth else 0.0
                cr = sum(X['cross_%s' % x].sum() for x in segs) if npth else 0.0
                nrq = sum(X['nreq_%s' % x].sum() for x in segs) if npth else 0.0
                nun = sum(X['nunm_%s' % x].sum() for x in segs) if npth else 0
                navm = float(np.nanmean(S['navpost'][ctx.masks['FULL'] if s == 'FULL' else ctx.masks[s], j]))
                nd = sum(int(ctx.masks[x].sum()) for x in segs)
                k = max(npth, 1)
                mrows.append(dict(owner_exec_id=e, mechanism=ref.mechanism, segment=s, requested_cny=req / k, matched_within_cny=wi / k, matched_cross_cny=cr / k,
                                  unmatched_cny=unm / k, unmatched_nav_share=float(unm / k / (navm * nd)) if nd and navm > 0 else '', n_requests=nrq / k,
                                  n_unmatched_requests=nun / k, control_comparability=comp, status='COMPUTED'))
        if mt is not None and npth:
            for r_, f_ in zip(X.itertuples(index=False), fd):
                prows.append(dict(owner_exec_id=e, mechanism=ref.mechanism, path_id=int(r_.path_id), seed=int(r_.seed), FULL_D_ann_pp=f_, n_unmatched_days=int(r_.n_unmatched_days)))
    return pd.DataFrame(rows), pd.DataFrame(mrows), pd.DataFrame(prows, columns=['owner_exec_id', 'mechanism', 'path_id', 'seed', 'FULL_D_ann_pp', 'n_unmatched_days'])


def full_D(df):
    num = 0.0
    den = 0
    for s in SEG4:
        v = df['D_%s' % s].to_numpy(float)
        n = df['n_%s' % s].to_numpy(float)
        num = num + np.nan_to_num(v) * n
        den = den + n
    with np.errstate(all='ignore'):
        return num / den


# ------------------------------------------------------------------ 复现 / 运行恒等 / WARM
def replication(ctx):
    R = ctx.R
    E6 = O.read_csv(O.E6P('registration', 'registry_E6p.csv'), dtype=str).fillna('').set_index('exec_id')
    rows = []
    for r in R[R.e6p_replication_exec_id != ''].itertuples(index=False):
        h6 = E6.loc[r.e6p_replication_exec_id, 'exec_hash']
        a = np.load(acct_file(ctx, r.exec_hash), allow_pickle=False)['DY']
        b = np.load(O.E6P('accounts_run', 'full', h6[:2], '%s.npz' % h6), allow_pickle=False)['DY']
        ncol = b.shape[1]
        for s in SEG4:
            m = (ctx.segi == s)[:min(len(a), len(b))]
            x = a[:len(m)][m, :ncol]
            y = b[:len(m)][m]
            fa, fb = np.isfinite(x), np.isfinite(y)
            if not np.array_equal(fa, fb):
                md = float('inf')
            else:
                d = np.abs(x[fa] - y[fa])
                sc = np.maximum(np.abs(x[fa]), np.abs(y[fa]))
                md = float(np.max(np.where(sc > 0, d / np.where(sc > 0, sc, 1.0), 0.0))) if d.size else 0.0
            rows.append(dict(e6q_exec_id=r.exec_id, e6p_exec_id=r.e6p_replication_exec_id, segment=s, max_abs_diff_daily=md, tolerance=1e-9,
                             status='PASS' if md <= 1e-9 else 'DIFFERS'))
    return pd.DataFrame(rows)


def run_identities(ctx, S, acc, net, rep):
    rows = []
    c = O.FEE_RATE
    R = ctx.R
    V0 = O.V0
    cash_d = 0.0
    tele = 0.0
    tok = 0.0
    liab = 0.0
    feed = 0.0
    for j, e in enumerate(ctx.ids):
        DY = acc[e]['DY']
        I = E.DYI
        cc = DY[:, I['cash_close']]
        d_cash = np.diff(np.r_[V0, cc]) - (DY[:, I['sell_val']] - DY[:, I['buy_val']] - DY[:, I['fee']])
        cash_d = max(cash_d, float(np.max(np.abs(d_cash))) / V0)
        tele = max(tele, abs(float(np.prod(1.0 + DY[:, I['r_net']])) - DY[-1, I['nav_post']] / V0))
        tg = DY[:, I['tag_amt']]
        resid = np.diff(np.r_[0.0, tg]) - (DY[:, I['tag_new']] - DY[:, I['tag_use_reg']] - DY[:, I['tag_use_ext']] - DY[:, I['tag_matured']])
        tok = max(tok, float(np.max(np.abs(resid))) / V0)
        liab = max(liab, float(np.max(tg + DY[:, I['lock_amt']] - cc)) / V0)
        if R.iloc[j].scenario == 'FEASIBLE_DAILY':
            feed = max(feed, float(np.max(np.abs(DY[:, I['fee']] - c * DY[:, I['traded']]))) / V0)
    rows.append(dict(check_id='CASH_EQUATION', description='全部 201 账户逐日：Δ现金 = 真实卖款 − 真实买款 − 费用（相对 V0）', exec_id='', value='', max_abs_diff=cash_d, tolerance=1e-9,
                     status='PASS' if cash_d <= 1e-9 else 'DIFFERS'))
    rows.append(dict(check_id='NAV_TELESCOPE', description='全部账户：Π(1 + r_net) = 末日 NAV / V0', exec_id='', value='', max_abs_diff=tele, tolerance=1e-8,
                     status='PASS' if tele <= 1e-8 else 'DIFFERS'))
    rows.append(dict(check_id='TOKEN_CONSERVATION', description='全部账户逐日：标签余额变动 = 新增 − 常规消费 − 额外消费 − 到期重分类（相对 V0）', exec_id='', value='', max_abs_diff=tok,
                     tolerance=1e-9, status='PASS' if tok <= 1e-9 else 'DIFFERS'))
    rows.append(dict(check_id='TOKEN_LIABILITY_LE_CASH', description='全部账户逐日：未消费标签 + 锁定额 ≤ 收盘现金（max(标签 + 锁定 − 现金) / V0）', exec_id='', value=liab,
                     max_abs_diff=max(liab, 0.0), tolerance=1e-9, status='PASS' if liab <= 1e-9 else 'DIFFERS'))
    rows.append(dict(check_id='FEE_NET_ORDER', description='FEASIBLE 账户逐日：费用 = 4bp × Σ|证券净订单名义|（引擎 traded 列）', exec_id='', value='', max_abs_diff=feed, tolerance=1e-9,
                     status='PASS' if feed <= 1e-9 else 'DIFFERS'))
    C = O.read_csv(O.P('registration', 'comparisons_E6q.csv'), dtype=str).fillna('')
    zi = C[C.kind == 'ZERO_INTERVENTION']
    zmax = 0.0
    dust, dust_n = 0.0, 0
    ledger = np.array([E.DYI[c] for c in ('tag_amt', 'tag_use_reg', 'tag_use_ext', 'tag_new', 'tag_matured', 'lock_amt', 'lock_new', 'lock_matured')])
    for z in zi.itertuples(index=False):
        a = acc[z.left_exec_id]['DY'][:, :76]
        b = acc[z.right_exec_id]['DY'][:, :76]
        fa, fb = np.isfinite(a), np.isfinite(b)
        if not np.array_equal(fa, fb):
            zmax = float('inf')
            break
        d = np.abs(np.where(fa, a - b, 0.0))
        sc = np.maximum(np.abs(np.where(fa, a, 0.0)), np.abs(np.where(fb, b, 0.0)))
        rel = np.where(sc > 0, d / np.where(sc > 0, sc, 1.0), 0.0)
        # 标签 / 锁定账本列（只作归属记账，不入现金 / NAV）：绝对差 ≤ 1e-6 元视为浮点碎屑并单独报告；其余 68 列严格相对 1e-9
        dl = d[:, ledger]
        dz = (dl <= 1e-6) & (rel[:, ledger] > 1e-9)
        if dz.any():
            dust = max(dust, float(dl[dz].max()))
            dust_n += 1
        rel[:, ledger] = np.where(dl <= 1e-6, 0.0, rel[:, ledger])
        zmax = max(zmax, float(rel.max()))
    rows.append(dict(check_id='ZERO_INTERVENTION_EQ_NATIVE', description='%d 条 ZERO_INTERVENTION 边（trigger = NONE 的非 NATIVE 臂 vs 同坐标 NATIVE）逐日 76 列：68 列严格相对差；'
                     '8 个标签 / 锁定账本列绝对差 ≤ 1e-6 元记为浮点碎屑（%d 条边有碎屑，最大 %.1e 元；现金 / NAV 列严格相等）' % (len(zi), dust_n, dust), exec_id='',
                     value=len(zi), max_abs_diff=zmax, tolerance=1e-9, status='PASS' if zmax <= 1e-9 else 'DIFFERS'))
    rmax = float(rep.max_abs_diff_daily.max()) if len(rep) else 0.0
    rows.append(dict(check_id='E6P_ACCOUNT_REPLICATION', description='%d 个 NATIVE（FEASIBLE；NONE / T1a / LEVEL / T8）账户 × 四段逐日 DY vs E6p 同坐标（E6p 全列；相对）' % rep.e6q_exec_id.nunique(),
                     exec_id='', value=int((rep.status == 'PASS').sum()), max_abs_diff=rmax, tolerance=1e-9, status='PASS' if rmax <= 1e-9 else 'DIFFERS'))
    # 票据守恒（随机目标路径日统计）
    tk = 0.0
    ntk = 0
    for p in sorted(os.listdir(O.P('randoms', 'daily'))) if os.path.exists(O.P('randoms', 'daily')) else []:
        for fn in os.listdir(O.P('randoms', 'daily', p)):
            if 'RANDOM_TARGET' not in fn:
                continue
            z = np.load(O.P('randoms', 'daily', p, fn), allow_pickle=False)
            if 'tkt' not in z.files:
                continue
            tk = max(tk, float(np.max(np.abs(z['xplan'] + z['rtshort'] - z['tkt']))) / V0)
            ntk += len(z['path_id'])
    rows.append(dict(check_id='TICKET_CONSERVATION', description='RANDOM_TARGET 路径逐日：本臂票据总额 = 已分配额 + 短配额（%d 条路径；相对 V0）' % ntk, exec_id='', value=ntk, max_abs_diff=tk,
                     tolerance=1e-6, status='PASS' if tk <= 1e-6 else 'DIFFERS'))
    return pd.DataFrame(rows)


def checkpoint_continuity(ctx, n=4):
    """A2 → checkpoint → B 续跑 vs 一次跑完（若干新机制账户）：全部 DY 逐位相同。"""
    import e6q_run as RN
    RN.setup()
    RN.G['R'] = ctx.R
    R = ctx.R
    pick = []
    for arm in ('EXIT_GATE_LIQ_5E8', 'REINVEST_LIQ_1E8', 'EXIT_HALF_REARM', 'REINVEST_NEW'):
        x = R[(R.arm == arm) & (R.trigger == 'T1b_LEVEL') & (R.H == '20') & (R.form == O.MAIN_FORM) & (R.memory == 'HG10') & (R.scenario == 'FEASIBLE_DAILY')]
        if len(x):
            pick.append(x.iloc[0])
    rows = []
    for r in pick[:n]:
        a = RN.build(r.to_dict()).run(0, ctx.T)
        b = np.load(acct_file(ctx, r.exec_hash), allow_pickle=False)['DY']
        same = np.array_equal(a.DY, b, equal_nan=True)
        rows.append(dict(check_id='CHECKPOINT_RESTORE_IDEMPOTENT', description='%s：A2 段末 checkpoint → B 续跑 vs 一次跑完，DY 全部列逐位相同 = %s' % (r.arm, same), exec_id=r.exec_id,
                         value=same, max_abs_diff=0.0 if same else float(np.nanmax(np.abs(a.DY - b))), tolerance=0.0, status='PASS' if same else 'DIFFERS'))
    return pd.DataFrame(rows)


def warm_table(ctx, S):
    import e6q_run as RN
    R = ctx.R
    p32 = R[R.is_primary32 == '1']
    rows = []
    segs = SEG4 if (ctx.phase == 'B' and not ctx.fake) else list(O.DERIV_SEGS)
    wne = {}
    keep = set(p32.exec_id) | set(x for x in p32.parent_same_arm_exec_id if x)
    for e in keep:
        for s in segs:
            h = O.sha_bytes(('%s|WARM|%s' % (e, s)).encode())[:16]
            p = RN.res_path('A2' if s in O.DERIV_SEGS else 'B', h, 'warm')
            if os.path.exists(p):
                wne[(e, s)] = np.load(p, allow_pickle=False)['DY'][:, E.DYI['net_excess']]
    for r in p32.itertuples(index=False):
        e, p = r.exec_id, r.parent_same_arm_exec_id
        if not p:
            continue
        for s in segs:
            if (e, s) not in wne or (p, s) not in wne:
                continue
            x, y = wne[(e, s)], wne[(p, s)]
            ok = np.isfinite(x) & np.isfinite(y)
            Dw = float(np.mean(x[ok] - y[ok]) * O.ANN_PP)
            m = ctx.masks[s]
            j, k = ctx.col[e], ctx.col[p]
            Dc = float(np.nanmean(S['ne'][m, j] - S['ne'][m, k]) * O.ANN_PP)
            rows.append(dict(exec_id=e, parent_exec_id=p, execution_profile=r.scenario, segment=s, start_state='WARM', n_days=int(ok.sum()), net_ann_pp=float(np.mean(x[ok]) * O.ANN_PP),
                             parent_net_ann_pp=float(np.mean(y[ok]) * O.ANN_PP), D_ann_pp=Dw, D_cash_v0_ann_pp=Dc, D_warm_minus_cont=Dw - Dc, status='COMPUTED'))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 主流程
def write(ctx, rel, df):
    p = ctx.out(*rel.split('/'))
    O.atomic_write_csv(p, df)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=['A2', 'B'], required=True)
    ap.add_argument('--fake_post', action='store_true')
    ap.add_argument('--root', default='')
    ap.add_argument('--workers', type=int, default=96)
    ap.add_argument('--dry_extras', action='store_true', help='空跑：A2 + fake_post 时另跑导出 / 随机表 / 复现 / 运行恒等（推导段文件，写到空跑根）')
    a = ap.parse_args()
    t0 = time.time()
    root = O.P(*a.root.split('/')) if a.root else None
    ctx = Ctx(a.phase, a.fake_post, root)
    S, acc = load_all(ctx)
    O.log('载入 %d 账户；支持日 %d' % (len(ctx.ids), ctx.support_days))
    boot = Boot(ctx)
    Sm, net = summary(ctx, S, acc, boot)
    outs = [write(ctx, 'statistics/account_summary_E6q.csv', Sm)]
    O.log('account_summary %d 行' % len(Sm))
    CR = comparison_results(ctx, S, net, boot)
    outs.append(write(ctx, 'statistics/comparison_results_E6q.csv', CR))
    Y = yearly(ctx, S)
    outs.append(write(ctx, 'statistics/yearly_E6q.csv', Y))
    CC, BE = cost_tables(ctx, S)
    outs.append(write(ctx, 'statistics/cost_curve_E6q.csv', CC))
    outs.append(write(ctx, 'statistics/breakeven_E6q.csv', BE))
    O.log('cost_curve %d 行；breakeven %d 行' % (len(CC), len(BE)))
    FB, FP = feedback_tables(ctx, S, net)
    outs.append(write(ctx, 'statistics/cost_feedback_E6q.csv', FB))
    outs.append(write(ctx, 'statistics/cost_feedback_pairs_E6q.csv', FP))
    DN = density_table(ctx, S)
    outs.append(write(ctx, 'statistics/density_E6q.csv', DN))
    WM = warm_table(ctx, S)
    outs.append(write(ctx, 'statistics/warm_sensitivity_E6q.csv', WM))
    meta = {}
    if a.phase == 'B' and not a.fake_post:
        meta = exports(ctx, a.workers)
        O.log('日序列 / 成交导出完成')
    elif a.dry_extras:
        p32 = ctx.R[ctx.R.is_primary32 == '1']
        fam = set(p32.exec_id) | {x for c in ('parent_same_arm_exec_id', 'native_same_trigger_exec_id', 'cash_same_trigger_exec_id', 'frontier_exec_id', 'parent_h5_global_exec_id',
                                              'level_h20_ref_exec_id') for x in p32[c] if x}
        meta = exports(ctx, a.workers, 'deriv', ('deriv',), only=fam)
        O.log('空跑：推导段日序列 / 成交导出完成')
    EV, RQ = event_tables(ctx, S, acc, meta)
    outs.append(write(ctx, 'events/event_counts_E6q.csv', EV))
    outs.append(write(ctx, 'events/exit_requests_E6q.csv', RQ))
    if a.phase == 'B' and not a.fake_post:
        RD, MT, RP = randoms_tables(ctx, S, net)
        outs.append(write(ctx, 'statistics/randoms_E6q.csv', RD))
        outs.append(write(ctx, 'statistics/matching_E6q.csv', MT))
        outs.append(write(ctx, 'statistics/random_paths_main_E6q.csv', RP))
        REP = replication(ctx)
        outs.append(write(ctx, 'verify/e6p_replication_E6q.csv', REP))
        RI = pd.concat([run_identities(ctx, S, acc, net, REP), checkpoint_continuity(ctx)], ignore_index=True)
        outs.append(write(ctx, 'verify/identities_E6q_runs.csv', RI))
        O.log('随机 / 复现 / 运行恒等完成：%s' % RI.status.value_counts().to_dict())
    elif a.dry_extras:
        RD, MT, RP = randoms_tables(ctx, S, net, tags=('A2',))
        outs.append(write(ctx, 'statistics/randoms_E6q.csv', RD))
        outs.append(write(ctx, 'statistics/matching_E6q.csv', MT))
        outs.append(write(ctx, 'statistics/random_paths_main_E6q.csv', RP))
        REP = replication(ctx)
        outs.append(write(ctx, 'verify/e6p_replication_E6q.csv', REP))
        RI = run_identities(ctx, S, acc, net, REP)
        outs.append(write(ctx, 'verify/identities_E6q_runs.csv', RI))
        O.log('空跑：随机 / 复现 / 运行恒等完成：%s' % RI.status.value_counts().to_dict())
    facts = dict(phase=a.phase, fake_post=a.fake_post, support_days=ctx.support_days, n_accounts=len(ctx.ids), summary_rows=len(Sm), comparison_rows=len(CR),
                 cost_rows=len(CC), wall_s=round(time.time() - t0, 1), rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.atomic_write_json(ctx.out('statistics', 'stats_facts_E6q.json'), facts)
    O.write_receipt('E6q_stats_%s%s' % (a.phase, '_fake' if a.fake_post else ''), outs, code=[__file__, O.__file__, E.__file__, CO.__file__, RU.__file__], **facts)
    print(json.dumps(facts, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
