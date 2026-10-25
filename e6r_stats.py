# -*- coding: utf-8 -*-
"""E6r 统计（附录 B.10–B.17、B.19、B.21；plan §7 / §9 / §13；brief §0.1 #24）：
  python3 e6r_stats.py --phase B                                   正式：statistics/ events/ verify/ accounts/daily/ trades/ 全部合同表（写 $E6R_WORK）
  python3 e6r_stats.py --phase A2 --root tmp/a2stats               推导段（G1 / 推导段读数；不读后段）
  python3 e6r_stats.py --phase A2 --fake_post --root tmp/dryrun    S0-L 空跑：后段日行 = 推导段日行循环复制，全链路被执行（--dry_extras 另跑导出 / 随机 / 复现）
口径：支持日 = 全部 350 账户净超额同时有限的交易日；段年化 = 252 × 100 × 段内日均；FULL = Σ n v / Σ n（n = 段支持日）；G4 = 四段中位（D 列 = 四段 D 的中位，
不是两个中位之差）；D_<ref> = 本账户 net − 引用账户 net（同支持日）；gross = net + 费用份额（费用 / 前一日 NAV）；HAC 主滞后 = max(20, 两账户注册 H 最大者)、
60 敏感；stationary bootstrap 2,000 次（块长 = HAC 主值；段内抽块、按段 n 合并 FULL）；D_sc = 同资本视图（逐日两边净超额按 min(x_c, x_p) / x 缩放）；
成本曲线：日冲击份额 = κ A^δ S_δ（S_δ = 引擎逐日 cost_s05 / s07 / s10，固定路径）；PORT3_T = 组合 clean 市值分位资本加权均值相对参照 × 100（正 = 偏大盘）。"""
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

import e6r_core as O
import e6r_engine as E

SEG4 = list(O.SEGS)
SEG6 = SEG4 + ['FULL', 'G4']
POST2 = ['2019-2023', '2024-2026']
YEARS = list(range(2010, 2027))
REPS = 2000
GRID = [(A_, k, x) for A_ in O.A_GRID for k in O.KAPPAS for x in O.EXPONENTS]
SCOL = {0.5: 's05', 0.7: 's07', 1.0: 's10'}
REF_D = (('flat_same_exit_exec_id', 'D_flat_same_exit_ann_pp'), ('native_same_trigger_flat_exec_id', 'D_native_same_trigger_flat_ann_pp'),
         ('noexit_same_overlay_exec_id', 'D_noexit_same_overlay_ann_pp'), ('h5_local_exec_id', 'D_h5_local_ann_pp'), ('h5_global_exec_id', 'D_h5_global_ann_pp'),
         ('frontier_exec_id', 'D_frontier_ann_pp'), ('scale_ref_gate_exec_id', 'D_scale_gate_ann_pp'), ('scale_ref_rearm_exec_id', 'D_scale_rearm_ann_pp'),
         ('policy_reference_exec_id', 'D_policy_ann_pp'))
COMP_REQ = (('FLAT_SAME_EXIT', 'flat_same_exit_exec_id'), ('NATIVE_SAME_TRIGGER_FLAT', 'native_same_trigger_flat_exec_id'),
            ('NOEXIT_SAME_OVERLAY', 'noexit_same_overlay_exec_id'), ('POLICY_REFERENCE', 'policy_reference_exec_id'))
COMP_P9 = (('FRONTIER', 'frontier_exec_id'), ('SCALE_REF_GATE_1E8', 'scale_ref_gate_exec_id'), ('SCALE_REF_REARM', 'scale_ref_rearm_exec_id'),
           ('H5_LOCAL', 'h5_local_exec_id'), ('H5_GLOBAL', 'h5_global_exec_id'))
GATE_SCHEMES = ('GATE_STATE', 'GATE_TILT', 'DROP_T3')
REARM_OPS = ('EXIT_HALF_REARM', 'GATE_REARM_1E8', 'GATE_REARM_5E8')
AREF_OPS = ('EXIT_GATE_LIQ_1E8', 'EXIT_GATE_LIQ_5E8', 'GATE_REARM_1E8', 'GATE_REARM_5E8')
ENTRY_MECHS = ('RANDOM_TILT_TICKETS', 'RANDOM_TILT_LABEL_PROJECT', 'RANDOM_GATE_COUNT', 'RANDOM_GATE_AMOUNT', 'RANDOM_GATE_TILT_JOINT', 'RANDOM_TENOR_LABEL')
MATCH_MECHS = ('AMOUNT_MATCH_V2', 'AMOUNT_ISK_V2', 'COUNT_ISK', 'LEVEL_WORST_1D')
NOT_COMPARABLE_UNMATCHED = 0.25
INTENSITY_BAND = (0.8, 1.25)
TICKET_LIMIT_SHARE = 0.25
OKN = {E.OK_REGULAR: 'REGULAR', E.OK_EXIT: 'EXIT', E.OK_EXTRA: 'EXTRA', E.OK_RENEW: 'EXIT', E.OK_DUE: 'DUE', E.OK_EXIT_HALF: 'EXIT_HALF',
       E.OK_EXIT_REARM: 'EXIT_REARM', E.OK_DEADLINE: 'DEADLINE_OVERRIDE'}
TERT = {1: 'T1', 2: 'T2', 3: 'T3', 0: 'NA'}
ST0 = {1: 'BAD', 0: 'GOOD', -1: 'UNKNOWN'}
SUM_COLS = ['exec_id', 'scenario', 'segment', 'support', 'n_days', 'net_ann_pp', 'gross_ann_pp', 'fee_ann_pp', 'abs_net_ann_pp', 'full_bench_excess_ann_pp',
            'D_flat_same_exit_ann_pp', 'D_native_same_trigger_flat_ann_pp', 'D_noexit_same_overlay_ann_pp', 'D_h5_local_ann_pp', 'D_h5_global_ann_pp',
            'D_frontier_ann_pp', 'D_scale_gate_ann_pp', 'D_scale_rearm_ann_pp', 'policy_reference_exec_id', 'D_policy_ann_pp', 'gross_D_policy_ann_pp',
            'D_sc_policy_ann_pp', 'D_sc_noexit_ann_pp', 'hac_lag_main', 'hac_se_main', 'hac_se_60', 'boot_lo', 'boot_hi', 'exposure_mean', 'cash_share_mean',
            'turnover_ann', 'max_drawdown_total', 'cagr_total', 'g_formation_mean', 'n_eff_formation_mean', 'transfer_share_mean', 'n_cohorts',
            'n_cohorts_overlay_active', 'n_gate_blocked_names', 'gate_blocked_capital_share', 'n_exit_intents', 'n_realized_early', 'n_rearm_episodes',
            'n_deadline_overrides', 'size_dev_pp', 'port3t_dev_pp', 'port3t_dev_noexit_pp', 'sector_active_max_pp', 'status']
DAILY_COLS = ['date', 'nav_pre', 'nav_post', 'fee', 'exposure', 'cash_share', 'bench_ret', 'net_excess_ret', 'gross_excess_ret', 'fee_ret', 'abs_net_ret',
              'full_bench_excess_ret', 'n_holdings', 'n_lots', 'turnover_day', 'g_formation', 'n_eff_formation', 'n_gate_blocked', 'overlay_active']
TRADE_COLS = ['date', 'security', 'lot_id', 'cohort_id', 'request_id', 'order_kind', 'side', 'qty', 'notional_cny', 'price', 'fee_cny', 'lot_due', 'assigned_H',
              'deadline', 'planned_p', 'realized_p', 'cvr_tertile_T0', 'entry_state_T0', 'planned_formation_w', 'planned_account_buy_w', 'actual_filled_w']
SER = ('ne', 'rnet', 'fullb', 'feefr', 'expo', 'cash', 'xprev', 'turn', 's05', 's07', 's10', 'szk', 'sam', 'navpost', 'nhold', 'nlots', 'bench', 'ovact',
       'ovcn', 'ovgn', 'ovgv', 'ovb', 'ovxb', 'ovtrf', 'pag', 'pah2', 'pah15', 'ahh2', 'ahh15', 'capbn', 'indbn', 'm3ovr', 'rearm', 'grprom', 'traded')


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
        self.segi = O.segs_of_dates(self.dates)
        self.years = np.array([int(d[:4]) for d in self.dates])
        self.live = np.arange(self.T) < self.d_end
        self.root = root or O.work()
        R = O.read_csv(O.P('registration', 'registry_E6r.csv'))
        self.R = R
        self.ids = list(R.exec_id)
        self.col = {e: j for j, e in enumerate(self.ids)}
        self.reg = R.set_index('exec_id', drop=False)
        self.lid2e = dict(zip(R.logical_id, R.exec_id))
        self.Hh = np.array([int(float(h)) for h in R.funding_H])

    def fake_rows(self, a):
        if self.fake:
            a = a.copy()
            a[self.d19:] = a[self.fk]
        return a

    def out(self, *parts):
        p = os.path.join(self.root, *parts)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        return p

    def refidx(self, col):
        return np.array([self.col.get(e, -1) if e else -1 for e in self.R[col]])


def acct_file(ctx, h, kind='acct'):
    sub = ctx.sub + ('_fb' if kind == 'fb' else '')
    return O.P('accounts_run', sub, h[:2], '%s.npz' % h)


def dy_series(DY):
    I = E.DYI
    nav = DY[:, I['nav_post']]
    vprev = np.r_[O.V0, nav[:-1]]
    with np.errstate(all='ignore'):
        return dict(ne=DY[:, I['net_excess']], rnet=DY[:, I['r_net']], fullb=DY[:, I['full_bench_ex']], feefr=DY[:, I['fee']] / vprev, expo=DY[:, I['exposure']],
                    cash=DY[:, I['cash_share']], xprev=DY[:, I['x_prev']], turn=0.5 * DY[:, I['traded']] / nav, s05=DY[:, I['cost_s05']],
                    s07=DY[:, I['cost_s07']], s10=DY[:, I['cost_s10']], szk=DY[:, I['sz_num']] / DY[:, I['sz_den']], sam=DY[:, I['sector_active_max']],
                    navpost=nav, nhold=DY[:, I['n_hold']], nlots=DY[:, I['n_lots']], bench=DY[:, I['bench']], ovact=DY[:, E.DY_OVACT], ovcn=DY[:, E.DY_OVCN],
                    ovgn=DY[:, E.DY_OVGN], ovgv=DY[:, E.DY_OVGV], ovb=DY[:, E.DY_OVB], ovxb=DY[:, E.DY_OVXB], ovtrf=DY[:, E.DY_OVTRF], pag=DY[:, E.DY_PAG],
                    pah2=DY[:, E.DY_PAH2], pah15=DY[:, E.DY_PAH15], ahh2=DY[:, E.DY_AHH2], ahh15=DY[:, E.DY_AHH15], capbn=DY[:, E.DY_CAPBN],
                    indbn=DY[:, E.DY_INDBN], m3ovr=DY[:, E.DY_M3OVR], rearm=DY[:, E.DY_REARM], grprom=DY[:, E.DY_GRPROM], traded=DY[:, I['traded']])


def load_all(ctx):
    T, n = ctx.T, len(ctx.ids)
    S = {k: np.full((T, n), np.nan) for k in SER}
    acc = {}
    for r in ctx.R.itertuples(index=False):
        j = ctx.col[r.exec_id]
        z = np.load(acct_file(ctx, r.exec_hash), allow_pickle=False)
        DY = z['DY']
        nd = min(len(DY), ctx.d_end)
        ser = dy_series(DY[:nd])
        for k, v in ser.items():
            col = np.full(T, np.nan)
            col[:nd] = v[:nd]
            S[k][:, j] = ctx.fake_rows(col)
        acc[r.exec_id] = dict(IN_i=z['IN_i'], IN_f=z['IN_f'], S_i=z['S_i'], HOLDH=z['HOLDH'], LOTH=z['LOTH'], DY=DY)
    ok_all = np.isfinite(S['ne']).all(axis=1) & ctx.live
    ctx.masks = {s: (ctx.segi == s) & ok_all for s in SEG4}
    ctx.masks['FULL'] = ok_all
    ctx.support_days = int(ok_all.sum())
    return S, acc


_MK = []


def market():
    import e6r_acct as A
    if not _MK:
        _MK.append(A.Market())
    return _MK[0]


def formation_layer(ctx):
    """FORMATION 层逐日统计 (T, 12)：e6r_overlay 缓存（8 个算子 'stats|<scheme>'；FLAT / TILT_H = stats_FLAT）；UNIFORM_CAP15 = DEV .015 名单现算
    （同列：g, h2, h15, N_eff = g²/h2, 1/h2, h15/g, 转移 0, 单股 .015 绑定份额, 行业绑定 NaN, 状态 0, 违约 0, 0）。返回 {exec_id: (T, 12)}。"""
    out = {}
    cache = {}
    for r in ctx.R.itertuples(index=False):
        sc = r.weight_scheme
        if sc == 'UNIFORM_CAP15':
            key = (r.form, r.memory, 'W15')
            if key not in cache:
                ptr, col, w = market().formation(r.form, r.memory, w15=True)
                st = np.full((ctx.T, 12), np.nan)
                for d in range(ctx.T):
                    a, b = ptr[d], ptr[d + 1]
                    if b == a:
                        continue
                    x = w[a:b]
                    g = x.sum()
                    h2 = (x * x).sum()
                    h15 = (x ** 1.5).sum()
                    st[d] = (g, h2, h15, g * g / h2 if h2 > 0 else np.nan, 1 / h2 if h2 > 0 else np.nan, h15 / g if g > 0 else np.nan, 0.0,
                             float(np.mean(np.isclose(x, O.RESEARCH_CAP, rtol=0, atol=1e-15))), np.nan, 0, 0.0, 0.0)
                cache[key] = st
        else:
            key = (r.form, r.memory, sc if sc not in ('FLAT', 'TILT_H') else 'FLAT')
            if key not in cache:
                z = np.load(os.path.join(ctx.cd, 'overlay', '%s|%s.npz' % (r.form, r.memory)), allow_pickle=False)
                cache[key] = z['stats_FLAT'] if key[2] == 'FLAT' else z['stats|' + sc]
        out[r.exec_id] = ctx.fake_rows(cache[key].copy())
    return out


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
    """按段、按块长缓存的 bootstrap 矩阵；FULL = 同一重抽序号下各段均值按段真实 n 合并（共同时间块：同段同块长的全部列共用一个 W）。"""

    def __init__(self, ctx):
        self.ctx = ctx
        self.W = {}

    def mat(self, s, blk):
        k = (s, blk)
        if k not in self.W:
            n = int(self.ctx.masks[s].sum())
            self.W[k] = boot_matrix(n, REPS, blk, int(O.stable_key('E6r', 'BOOT', s, blk)[:8], 16)) if n >= 30 else None
        return self.W[k]

    def reps(self, D, blk):
        """{段: (REPS, A) 重抽段均值 ann_pp 或 None}，含 FULL。"""
        out = {}
        acc, ns = [], []
        for s in SEG4:
            m = self.ctx.masks[s]
            W = self.mat(s, blk)
            if W is None:
                out[s] = None
                continue
            X = D[m]
            F = np.isfinite(X).astype(np.float32)
            X = np.where(np.isfinite(X), X, 0.0).astype(np.float32)
            with np.errstate(all='ignore'):
                bm = (W @ X) / (W @ F) * O.ANN_PP
            out[s] = bm
            n = int(m.sum())
            acc.append(bm * n)
            ns.append(n)
        out['FULL'] = (sum(acc) / sum(ns)) if acc else None
        return out

    def ci(self, D, blk):
        out = {}
        for s, v in self.reps(D, blk).items():
            if v is None:
                out[s] = (np.full(D.shape[1], np.nan), np.full(D.shape[1], np.nan))
            else:
                out[s] = (np.nanpercentile(v, 2.5, axis=0), np.nanpercentile(v, 97.5, axis=0))
        return out


def dseg(X, s, j, k):
    """差的段读数：四段与 FULL 直接相减；G4 = 四段差的中位。k = None → 绝对值。"""
    if s == 'G4':
        return float(np.median([X[t][j] - (X[t][k] if k is not None else 0.0) for t in SEG4]))
    return float(X[s][j] - (X[s][k] if k is not None else 0.0))


def ann_seg(X, ctx):
    """X：(T, A) → {段: (A,) ann_pp}；FULL = Σ n v / Σ n；G4 = 四段中位。"""
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


def mean_seg(X, ctx, scale=1.0, masks=None):
    out = {}
    for s in SEG4 + ['FULL']:
        m = ctx.masks[s]
        with np.errstate(all='ignore'):
            out[s] = np.nanmean(X[m], 0) * scale
    out['G4'] = np.median(np.vstack([out[s] for s in SEG4]), axis=0)
    return out


def sum_seg(X, ctx):
    out = {}
    for s in SEG4 + ['FULL']:
        out[s] = np.nansum(X[ctx.masks[s]], 0)
    return out


def drawdown_cagr(nav, ctx):
    out = {}
    for s in SEG4 + ['FULL']:
        x = nav[ctx.masks[s]]
        if len(x) < 2:
            out[s] = (np.nan, np.nan)
            continue
        peak = np.maximum.accumulate(x)
        out[s] = (float(np.min(x / peak - 1.0)), float((x[-1] / x[0]) ** (252.0 / (len(x) - 1)) - 1.0))
    out['G4'] = (float(np.median([out[s][0] for s in SEG4])), float(np.median([out[s][1] for s in SEG4])))
    return out


def fnum(x):
    return '' if x is None or (isinstance(x, float) and not np.isfinite(x)) else x


# ------------------------------------------------------------------ 事件计数（意向 / 成交）
def event_counts(ctx, a, s):
    """段内事件计数（意向日落在段内；段末待成交：意向日 + 1 ≥ 授权末日 → 右删失，否则未成交）；n_intents = early + late + unfilled + censored。"""
    out = dict(n_exit_intents=0, n_realized_early=0, n_late_fill=0, n_unfilled=0, n_censored=0)
    if a is None or ctx.fake:
        return out
    IN = a['IN_i']
    IN = IN[np.isin(IN[:, E.IN_KIND], [E.KD_TRIG, E.KD_REARM, E.KD_RAND])]
    dd = IN[:, E.IN_DAY]
    st = IN[:, E.IN_STATUS]
    segm = (ctx.segi == s) if s in SEG4 else np.ones(ctx.T, bool)
    in_s = segm[np.clip(dd, 0, ctx.T - 1)] & (dd < ctx.d_end)
    pend = (st == 0) & in_s
    cens = pend & (dd + 1 >= ctx.d_end)
    out.update(n_exit_intents=int(in_s.sum()), n_realized_early=int(((st == 1) & in_s).sum()), n_late_fill=int(((st == 2) & in_s).sum()),
               n_unfilled=int((pend & ~cens).sum()), n_censored=int(cens.sum()))
    return out


# ------------------------------------------------------------------ 账户汇总（B.10）
def summary(ctx, S, acc, boot, FL):
    R = ctx.R
    n = len(ctx.ids)
    ne = S['ne']
    idx = {c: ctx.refidx(c) for c, _ in REF_D}
    pol = idx['policy_reference_exec_id']
    nox = idx['noexit_same_overlay_exec_id']
    fse = idx['flat_same_exit_exec_id']
    net = ann_seg(ne, ctx)
    gross = ann_seg(ne + S['feefr'], ctx)
    fee = ann_seg(S['feefr'], ctx)
    absn = ann_seg(S['rnet'], ctx)
    fullb = ann_seg(S['fullb'], ctx)
    expo = mean_seg(S['expo'], ctx)
    cash = mean_seg(S['cash'], ctx)
    turn = mean_seg(S['turn'], ctx, 252.0)
    sam = mean_seg(S['sam'], ctx)

    def scview(ref):
        ok = ref >= 0
        xm = np.full_like(ne, np.nan)
        xm[:, ok] = np.minimum(S['xprev'][:, ok], S['xprev'][:, ref[ok]])
        with np.errstate(all='ignore'):
            scc = np.where(S['xprev'] > 0, ne * xm / S['xprev'], 0.0)
            scp = np.full_like(ne, np.nan)
            scp[:, ok] = np.where(S['xprev'][:, ref[ok]] > 0, ne[:, ref[ok]] * xm[:, ok] / S['xprev'][:, ref[ok]], 0.0)
        return ann_seg(np.where(ok[None, :], scc - scp, np.nan), ctx)

    def devview(ref, sign=1.0):
        ok = ref >= 0
        X = np.full_like(ne, np.nan)
        X[:, ok] = sign * (S['szk'][:, ok] - S['szk'][:, ref[ok]]) * 100.0
        return mean_seg(X, ctx)
    Dsc_pol, Dsc_nox = scview(pol), scview(nox)
    dev_pol, dev_nox, dev_fse = devview(pol), devview(nox), devview(fse, -1.0)       # size_dev：正 = 偏小盘（参照 − 本账户）
    okp = pol >= 0
    Dp = np.full_like(ne, np.nan)
    Dp[:, okp] = ne[:, okp] - ne[:, pol[okp]]
    lag = np.array([max(20, ctx.Hh[j], ctx.Hh[pol[j]]) if pol[j] >= 0 else 0 for j in range(n)])
    se = {'main': {}, '60': {}}
    for s in SEG4 + ['FULL']:
        Dm = Dp[ctx.masks[s]]
        v = np.full(n, np.nan)
        for L in np.unique(lag[okp]):
            cols = (lag == L) & okp
            if Dm.shape[0] > L + 2:
                v[cols] = nw_se(Dm[:, cols], int(L)) * O.ANN_PP
        se['main'][s] = v
        v60 = np.full(n, np.nan)
        if okp.any() and Dm.shape[0] > 62:
            v60[okp] = nw_se(Dm[:, okp], 60) * O.ANN_PP
        se['60'][s] = v60
    bci = {s: (np.full(n, np.nan), np.full(n, np.nan)) for s in SEG4 + ['FULL']}
    for L in np.unique(lag[okp]):
        cols = np.flatnonzero((lag == L) & okp)
        c = boot.ci(Dp[:, cols], int(L))
        for s in SEG4 + ['FULL']:
            bci[s][0][cols], bci[s][1][cols] = c[s]
    # FORMATION 层与入场计数
    fg = np.column_stack([FL[e][:, 0] for e in ctx.ids])
    fneff = np.column_stack([FL[e][:, 3] for e in ctx.ids])
    ftrf = np.column_stack([FL[e][:, 6] for e in ctx.ids])
    fco = np.isfinite(fg)
    fgm, fnm, ftm = mean_seg(fg, ctx), mean_seg(fneff, ctx), mean_seg(ftrf, ctx)
    ncoh = sum_seg(fco.astype(float), ctx)
    nact = sum_seg((S['ovact'] > 0).astype(float), ctx)
    ngb = sum_seg(S['ovgn'], ctx)
    gbv = sum_seg(S['ovgv'], ctx)
    gbb = sum_seg(S['ovb'] + np.nan_to_num(S['ovxb']), ctx)
    nrearm = sum_seg(S['rearm'], ctx)
    novr = sum_seg(S['m3ovr'], ctx)
    rows = []
    for j, e in enumerate(ctx.ids):
        r = R.iloc[j]
        ddc = drawdown_cagr(S['navpost'][:, j], ctx)
        a = acc.get(e)
        for s in SEG6:
            row = dict(exec_id=e, scenario=r.scenario, segment=s, support=r.support, n_days=int(ctx.masks[s].sum()) if s != 'G4' else '',
                       net_ann_pp=net[s][j], gross_ann_pp=gross[s][j], fee_ann_pp=fee[s][j], abs_net_ann_pp=absn[s][j], full_bench_excess_ann_pp=fullb[s][j],
                       policy_reference_exec_id=r.policy_reference_exec_id, exposure_mean=expo[s][j], cash_share_mean=cash[s][j], turnover_ann=turn[s][j],
                       max_drawdown_total=ddc[s][0], cagr_total=ddc[s][1], g_formation_mean=fgm[s][j], n_eff_formation_mean=fnm[s][j],
                       transfer_share_mean=ftm[s][j], sector_active_max_pp=sam[s][j], size_dev_pp=dev_fse[s][j] if fse[j] >= 0 else '',
                       port3t_dev_pp=dev_pol[s][j] if okp[j] else '', port3t_dev_noexit_pp=dev_nox[s][j] if nox[j] >= 0 else '', status='COMPUTED')
            for c, dcol in REF_D:
                k = idx[c][j]
                if k >= 0:
                    row[dcol] = dseg(net, s, j, k)
            if okp[j]:
                k = pol[j]
                row.update(gross_D_policy_ann_pp=dseg(gross, s, j, k), D_sc_policy_ann_pp=Dsc_pol[s][j], hac_lag_main=int(lag[j]))
                if s != 'G4':
                    row.update(hac_se_main=se['main'][s][j], hac_se_60=se['60'][s][j], boot_lo=bci[s][0][j], boot_hi=bci[s][1][j])
            if nox[j] >= 0:
                row['D_sc_noexit_ann_pp'] = Dsc_nox[s][j]
            if s != 'G4':
                ev = event_counts(ctx, a, s)
                row.update(n_cohorts=int(ncoh[s][j]), n_cohorts_overlay_active=int(nact[s][j]), n_gate_blocked_names=int(ngb[s][j]),
                           gate_blocked_capital_share=float(gbv[s][j] / gbb[s][j]) if gbb[s][j] > 0 else 0.0, n_exit_intents=ev['n_exit_intents'],
                           n_realized_early=ev['n_realized_early'], n_rearm_episodes=int(nrearm[s][j]) if (r.exit_op in REARM_OPS and r.trigger != 'NONE') else 0,
                           n_deadline_overrides=int(novr[s][j]))
            rows.append(row)
    return pd.DataFrame(rows, columns=SUM_COLS), net, gross


# ------------------------------------------------------------------ 比较 / 复合（B.11）
def comparison_results(ctx, S, net, gross, boot):
    C = O.read_csv(O.P('registration', 'comparisons_E6r.csv'))
    L = np.array([ctx.col[e] for e in C.left_exec_id])
    Rr = np.array([ctx.col[e] for e in C.right_exec_id])
    ne = S['ne']
    absn = ann_seg(S['rnet'], ctx)
    imp1 = 0.5 * (1e8 ** 0.5) * np.nan_to_num(S['s05'])
    imp5 = 0.5 * (5e8 ** 0.5) * np.nan_to_num(S['s05'])
    c1 = ann_seg((ne[:, L] - imp1[:, L]) - (ne[:, Rr] - imp1[:, Rr]), ctx)
    c5 = ann_seg((ne[:, L] - imp5[:, L]) - (ne[:, Rr] - imp5[:, Rr]), ctx)
    D = ne[:, L] - ne[:, Rr]
    blk = np.maximum(20, np.maximum(ctx.Hh[L], ctx.Hh[Rr]))
    lo = {s: np.full(len(C), np.nan) for s in SEG4 + ['FULL']}
    hi = {s: np.full(len(C), np.nan) for s in SEG4 + ['FULL']}
    for b in np.unique(blk):
        cols = np.flatnonzero(blk == b)
        ci = boot.ci(D[:, cols], int(b))
        for s in SEG4 + ['FULL']:
            lo[s][cols], hi[s][cols] = ci[s]
    rows = []
    for i, c in enumerate(C.itertuples(index=False)):
        self_edge = c.structural_identity == 'true'
        for s in SEG6:
            if self_edge:
                dn = dg = da = d1 = d5 = 0.0
            else:
                dn, dg, da = dseg(net, s, L[i], Rr[i]), dseg(gross, s, L[i], Rr[i]), dseg(absn, s, L[i], Rr[i])
                d1, d5 = float(c1[s][i]), float(c5[s][i])
            rows.append(dict(comparison_id=c.comparison_id, kind=c.kind, left_exec_id=c.left_exec_id, right_exec_id=c.right_exec_id, segment=s,
                             D_net_ann_pp=dn, D_gross_ann_pp=dg, D_abs_ann_pp=da, D_cost_1e8_ann_pp=d1, D_cost_5e8_ann_pp=d5,
                             boot_lo=(0.0 if self_edge else lo[s][i]) if s != 'G4' else '', boot_hi=(0.0 if self_edge else hi[s][i]) if s != 'G4' else '',
                             status='COMPUTED'))
    return pd.DataFrame(rows)


def compound_results(ctx, S, net, gross, boot):
    """I = Σ coef × net(term)（AB + / A − / B − / ZERO +）；M_A = AB − A；M_B = AB − B；AB − max(A, B)；bootstrap 区间在每次重复内重算（plan §7.2）。"""
    K = O.read_csv(O.P('registration', 'compound_contrasts_E6r.csv'))
    ne = S['ne']
    rows = []
    for cid, g in K.groupby('contrast_id', sort=True):
        t = {r.term_role: ctx.col[r.term_exec_id] for r in g.itertuples(index=False)}
        coef = {r.term_role: float(r.coefficient) for r in g.itertuples(index=False)}
        kind = g.kind.iloc[0]
        cols = [t['AB'], t['A'], t['B'], t['ZERO']]
        blk = int(max(20, max(ctx.Hh[c] for c in cols)))
        Di = sum(coef[k] * ne[:, t[k]] for k in ('AB', 'A', 'B', 'ZERO'))[:, None]
        rp_i = boot.reps(Di, blk)
        rp = boot.reps(ne[:, cols[:3]], blk)
        for s in SEG6:
            if s == 'G4':
                iv = float(np.median([sum(coef[k] * net[q][t[k]] for k in coef) for q in SEG4]))
                gv = float(np.median([sum(coef[k] * gross[q][t[k]] for k in coef) for q in SEG4]))
                ma = float(np.median([net[q][t['AB']] - net[q][t['A']] for q in SEG4]))
                mb = float(np.median([net[q][t['AB']] - net[q][t['B']] for q in SEG4]))
                mx = float(np.median([net[q][t['AB']] - max(net[q][t['A']], net[q][t['B']]) for q in SEG4]))
                lo_i = hi_i = lo_m = hi_m = ''
            else:
                iv = float(sum(coef[k] * net[s][t[k]] for k in coef))
                gv = float(sum(coef[k] * gross[s][t[k]] for k in coef))
                ma = float(net[s][t['AB']] - net[s][t['A']])
                mb = float(net[s][t['AB']] - net[s][t['B']])
                mx = float(net[s][t['AB']] - max(net[s][t['A']], net[s][t['B']]))
                bi, bm = rp_i[s], rp[s]
                lo_i, hi_i = (float(np.nanpercentile(bi[:, 0], 2.5)), float(np.nanpercentile(bi[:, 0], 97.5))) if bi is not None else ('', '')
                if bm is not None:
                    v = bm[:, 0] - np.maximum(bm[:, 1], bm[:, 2])
                    lo_m, hi_m = float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))
                else:
                    lo_m = hi_m = ''
            rows.append(dict(contrast_id=cid, kind=kind, segment=s, I_net_ann_pp=iv, I_gross_ann_pp=gv, M_A_net_ann_pp=ma, M_B_net_ann_pp=mb,
                             AB_minus_max_net_ann_pp=mx, boot_lo_I=lo_i, boot_hi_I=hi_i, boot_lo_AB_minus_max=lo_m, boot_hi_AB_minus_max=hi_m, status='COMPUTED'))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 逐年（B.15）
def yearly(ctx, S):
    R = ctx.R
    ne = S['ne']
    pol = ctx.refidx('policy_reference_exec_id')
    nox = ctx.refidx('noexit_same_overlay_exec_id')
    sup = ctx.masks['FULL']
    rows = []
    for j, e in enumerate(ctx.ids):
        sc = R.scenario.iloc[j]
        for y in YEARS:
            m = (ctx.years == y) & sup
            row = dict(exec_id=e, scenario=sc, year=y, n_days=int(m.sum()), partial_year_flag=1 if y == 2026 else 0)
            if not m.any():
                row['status'] = 'NOT_RUN'
                rows.append(row)
                continue
            v = float(np.mean(ne[m, j]) * O.ANN_PP)
            row.update(net_ann_pp=v, status='COMPUTED')
            if pol[j] >= 0:
                pv = float(np.mean(ne[m, pol[j]]) * O.ANN_PP)
                row.update(policy_reference_net_ann_pp=pv, D_policy_ann_pp=v - pv)
            if nox[j] >= 0:
                nv = float(np.mean(ne[m, nox[j]]) * O.ANN_PP)
                row.update(noexit_reference_net_ann_pp=nv, D_noexit_ann_pp=v - nv)
            rows.append(row)
    return pd.DataFrame(rows, columns=['exec_id', 'scenario', 'year', 'n_days', 'net_ann_pp', 'policy_reference_net_ann_pp', 'D_policy_ann_pp',
                                       'noexit_reference_net_ann_pp', 'D_noexit_ann_pp', 'partial_year_flag', 'status'])


# ------------------------------------------------------------------ 成本曲线 / 盈亏平衡（B.16）
def e_refs(ctx):
    """E 依赖（claims.json）：owner 逻辑 id → [reference exec_id]（statistic 以 EXCESS_CURVE_DIFF 开头的才进 E_REFERENCE 行）。"""
    cl = json.load(open(O.P('registration', 'spec', 'claims.json'), encoding='utf-8'))
    out = {}
    for c in cl:
        if str(c.get('statistic', '')).startswith('EXCESS_CURVE_DIFF'):
            out.setdefault(ctx.lid2e[c['owner']], []).append(ctx.lid2e[c['reference']])
    return out


def root_status(a, b, delta=0.5, A0=1e8):
    """plan §9.5：Δ(A) = a − b (A / A0)^δ 的过零点；a / b 异号或为 0 → NO_ROOT（不造正根）；负 → 正 = LOWER_CROSSING；浮点范围外 → OUT_OF_NUMERICAL_RANGE。"""
    if not (math.isfinite(a) and math.isfinite(b)):
        return None, 'COST_MISSING'
    if b == 0 or a == 0 or (a > 0) != (b > 0):
        return None, 'NO_ROOT'
    lr = math.log(A0) + (math.log(abs(a)) - math.log(abs(b))) / delta
    if lr > math.log(sys.float_info.max) or lr < math.log(sys.float_info.min):
        return None, 'OUT_OF_NUMERICAL_RANGE'
    return math.exp(lr), ('POSITIVE_ROOT' if a > 0 else 'LOWER_CROSSING')


def cost_pairs(ctx):
    """(j, comparator_kind, k) 清单：ABSOLUTE；四种必有参照（非空且非自身）；E06 / E07 owner 的 E_REFERENCE；主 9 另加 FRONTIER / SCALE / H5。"""
    R = ctx.R
    p9 = (R.is_primary9 == 'true').to_numpy()
    er = e_refs(ctx)
    out = []
    for j, e in enumerate(ctx.ids):
        out.append((j, 'ABSOLUTE', None))
        r = R.iloc[j]
        for kind, col in COMP_REQ + (COMP_P9 if p9[j] else ()):
            ref = r[col]
            if ref and ref != e:
                out.append((j, kind, ctx.col[ref]))
        for ref in er.get(e, []):
            out.append((j, 'E_REFERENCE', ctx.col[ref]))
    return out


def cost_tables(ctx, S):
    ne = S['ne']
    fee = S['feefr']
    seg_a = {x: ann_seg(np.nan_to_num(S[SCOL[x]]), ctx) for x in O.EXPONENTS}
    g_ne = ann_seg(ne + fee, ctx)
    g_fee = ann_seg(fee, ctx)
    g_net = ann_seg(ne, ctx)
    rows, brows = [], []
    for j, ck, k in cost_pairs(ctx):
        e = ctx.ids[j]
        sc = ctx.R.scenario.iloc[j]
        cid = '' if k is None else ctx.ids[k]
        for s in SEG6:
            gd = dseg(g_ne, s, j, k)
            fd = dseg(g_fee, s, j, k)
            for (A_, kp, x) in GRID:
                Sx = seg_a[x]
                imp = kp * (A_ ** x) * dseg(Sx, s, j, k)
                if s == 'G4':
                    na = float(np.median([dseg(g_ne, t, j, k) - dseg(g_fee, t, j, k) - kp * (A_ ** x) * dseg(Sx, t, j, k) for t in SEG4]))
                else:
                    na = gd - fd - imp
                okv = all(math.isfinite(v) for v in (gd, fd, imp, na))
                rows.append((e, sc, ck, cid, int(A_), kp, x, s, gd, fd, imp, na, 'COMPUTED' if okv else 'NUMERICAL_RANGE'))
        for kp in O.KAPPAS:
            for x in O.EXPONENTS:
                a_ = dseg(g_net, 'FULL', j, k)
                b_ = kp * (1e8 ** x) * dseg(seg_a[x], 'FULL', j, k)
                root, kind = root_status(float(a_), float(b_), x, 1e8)
                if kind in ('POSITIVE_ROOT', 'LOWER_CROSSING') and not (O.A_GRID[0] <= root <= O.A_GRID[-1]):
                    kind = 'OUT_OF_GRID'
                brows.append(dict(exec_id=e, scenario=sc, comparator_kind=ck, comparator_exec_id=cid, kappa=kp, exponent=x, a_coeff=a_, b_coeff=b_,
                                  root_kind=kind, breakeven_A_cny=root if (root is not None and kind != 'OUT_OF_GRID') else '', status='COMPUTED'))
    CC = pd.DataFrame(rows, columns=['exec_id', 'scenario', 'comparator_kind', 'comparator_exec_id', 'A_cny', 'kappa', 'exponent', 'segment',
                                     'gross_diff_ann_pp', 'fee_diff_ann_pp', 'impact_diff_ann_pp', 'net_after_impact_diff_ann_pp', 'status'])
    return CC, pd.DataFrame(brows)


# ------------------------------------------------------------------ 反馈（B.16）
def feedback_tables(ctx, S):
    import e6r_run as RN
    F = O.read_csv(O.P('registration', 'cost_feedback_refs_E6r.csv'))
    P = O.read_csv(O.P('registration', 'feedback_comparisons_E6r.csv'))
    T = ctx.T
    cols = []
    for f in F.itertuples(index=False):
        h = RN.fb_hash(f.owner_exec_id, int(float(f.A0_cny)))
        DY = np.load(acct_file(ctx, h, 'fb'), allow_pickle=False)['DY']
        nd = min(len(DY), ctx.d_end)
        col = np.full(T, np.nan)
        col[:nd] = DY[:nd, E.DYI['net_excess']]
        cols.append(ctx.fake_rows(col))
    fa = ann_seg(np.column_stack(cols), ctx)
    pos = {fid: k for k, fid in enumerate(F.feedback_id)}
    ne = S['ne']
    oj = np.array([ctx.col[e] for e in F.owner_exec_id])
    A0 = F.A0_cny.astype(float).to_numpy()
    imp = np.column_stack([0.5 * (A0[k] ** 0.5) * np.nan_to_num(S['s05'][:, oj[k]]) for k in range(len(F))])
    fx = ann_seg(ne[:, oj] - imp, ctx)
    rows = []
    for k, f in enumerate(F.itertuples(index=False)):
        for s in SEG6:
            rows.append(dict(feedback_id=f.feedback_id, owner_exec_id=f.owner_exec_id, A0_cny=int(float(f.A0_cny)), kappa=float(f.kappa), exponent=float(f.exponent),
                             segment=s, net_ann_pp_feedback=float(fa[s][k]), net_ann_pp_fixed_path=float(fx[s][k]), status='COMPUTED'))
    prow = []
    for p in P.itertuples(index=False):
        a, b = pos[p.left_feedback_id], pos[p.right_feedback_id]
        for s in SEG6:
            prow.append(dict(left_feedback_id=p.left_feedback_id, right_feedback_id=p.right_feedback_id, kind=p.kind, A0_cny=int(float(p.A0_cny)), segment=s,
                             D_feedback_ann_pp=dseg(fa, s, a, b), D_fixed_path_ann_pp=dseg(fx, s, a, b), status='COMPUTED'))
    return pd.DataFrame(rows), pd.DataFrame(prow)


# ------------------------------------------------------------------ 权重三层（weights_E6r；plan §6 / §10 D5）
def weights_table(ctx, S, FL):
    """FORMATION（源最终 cohort 的算子形成权重；逐形成日）、PLANNED_ACCOUNT（账户层计划买入权重 = 票据 / NAV_T；逐有计划日）、ACTUAL_HOLDING（收盘持仓 / NAV）；
    N_eff = g² / h2（不是 legacy 1 / h2）；形状代理 = h1.5 / g；现金作资产集中度 = h2 + (1 − g)²；单股 / 行业上界绑定份额（FORMATION = 形成层；PLANNED = 计划层名数份额）。"""
    rows = []
    with np.errstate(all='ignore'):
        for j, e in enumerate(ctx.ids):
            fl = FL[e]
            sc = ctx.R.weight_scheme.iloc[j]
            pg, ph2, ph15 = S['pag'][:, j], S['pah2'][:, j], S['pah15'][:, j]
            ag, ah2, ah15 = S['expo'][:, j], S['ahh2'][:, j], S['ahh15'][:, j]
            layers = {
                'FORMATION': (fl[:, 0], fl[:, 1], fl[:, 2], np.isfinite(fl[:, 0]), fl[:, 6], fl[:, 7], fl[:, 8]),
                'PLANNED_ACCOUNT': (pg, ph2, ph15, pg > 0, np.where(S['ovb'][:, j] > 0, S['ovtrf'][:, j] / S['ovb'][:, j], np.nan),
                                    np.where(S['ovcn'][:, j] > 0, S['capbn'][:, j] / S['ovcn'][:, j], np.nan),
                                    np.where(S['ovcn'][:, j] > 0, S['indbn'][:, j] / S['ovcn'][:, j], np.nan)),
                'ACTUAL_HOLDING': (ag, ah2, ah15, ag > 0, np.full(ctx.T, np.nan), np.full(ctx.T, np.nan), np.full(ctx.T, np.nan))}
            for lay, (g, h2, h15, ok, trf, cb, ib) in layers.items():
                ok = ok & np.isfinite(g) & np.isfinite(h2) & (h2 > 0)
                neff = g * g / h2
                inv = 1.0 / h2
                shp = h15 / g
                cac = h2 + (1.0 - g) ** 2
                vals = {}
                for s in SEG4 + ['FULL']:
                    m = ctx.masks[s] & ok
                    nobs = int(m.sum())
                    if nobs == 0:
                        vals[s] = None
                        continue
                    tr = 0.0 if (lay == 'FORMATION' and sc == 'FLAT') else (float(np.nanmean(trf[m])) if np.isfinite(trf[m]).any() else np.nan)
                    vals[s] = dict(n_obs=nobs, g_mean=float(np.mean(g[m])), h2_mean=float(np.mean(h2[m])), h15_mean=float(np.mean(h15[m])),
                                   n_eff_mean=float(np.mean(neff[m])), legacy_inverse_s2_mean=float(np.mean(inv[m])), shape_proxy_mean=float(np.mean(shp[m])),
                                   cash_as_asset_concentration_mean=float(np.mean(cac[m])), transfer_share_mean=tr,
                                   cap_bound_stock_share=float(np.nanmean(cb[m])) if np.isfinite(cb[m]).any() else np.nan,
                                   cap_bound_industry_share=float(np.nanmean(ib[m])) if np.isfinite(ib[m]).any() else np.nan)
                ok4 = [vals[s] for s in SEG4 if vals[s] is not None]
                vals['G4'] = ({k: (float(np.median([v[k] for v in ok4])) if all(np.isfinite(v[k]) for v in ok4) else np.nan) for k in ok4[0]}
                              if len(ok4) == 4 else None)
                for s in SEG6:
                    v = vals[s]
                    if v is None:
                        rows.append(dict(exec_id=e, layer=lay, segment=s, n_obs=0, status='NOT_APPLICABLE'))
                    else:
                        rows.append(dict(exec_id=e, layer=lay, segment=s, **{k: fnum(x) for k, x in v.items()}, status='COMPUTED'))
    cols = ['exec_id', 'layer', 'segment', 'n_obs', 'g_mean', 'h2_mean', 'h15_mean', 'n_eff_mean', 'legacy_inverse_s2_mean', 'shape_proxy_mean',
            'cash_as_asset_concentration_mean', 'transfer_share_mean', 'cap_bound_stock_share', 'cap_bound_industry_share', 'status']
    W = pd.DataFrame(rows, columns=cols)
    W['n_obs'] = W['n_obs'].map(lambda x: int(round(x)) if x != '' and pd.notna(x) else x)
    return W


# ------------------------------------------------------------------ 事件表 / 请求表（B.19）
def event_tables(ctx, S, acc, trades_meta, FLAB):
    R = ctx.R
    rows, rq = [], []
    for j, r in enumerate(R.itertuples(index=False)):
        a = acc[r.exec_id]
        Si = a['S_i']
        ev = event_counts(ctx, a, 'FULL')
        H = a['HOLDH'].astype(float)
        mle = float((np.arange(len(H)) * H).sum() / H.sum()) if H.sum() > 0 else ''
        lc, ld = int(Si[E.SI_LCLOSED]), int(Si[E.SI_LDUE])
        gate = r.weight_scheme in GATE_SCHEMES
        rearm = r.exit_op in REARM_OPS and r.trigger != 'NONE'
        nunk, ncoh, nallna = FLAB[(r.form, r.memory)]
        rows.append(dict(exec_id=r.exec_id, trigger=r.trigger, exit_op=r.exit_op, weight_scheme=r.weight_scheme, n_intents=ev['n_exit_intents'],
                         n_realized_early=ev['n_realized_early'], n_late_fill=ev['n_late_fill'], n_unfilled=ev['n_unfilled'], n_censored=ev['n_censored'],
                         n_deadline_overrides=int(Si[E.SI_OVERRIDE]), n_half_requests=int(Si[E.SI_HALF]) if r.exit_op in REARM_OPS else 0,
                         n_rearm_episodes=int(Si[E.SI_REARMN]) if rearm else 0, n_rearm_promotions=int(np.nansum(S['grprom'][:, j])) if rearm else 0,
                         n_reentries=int(Si[E.SI_REENTRY]), n_gate_blocked_names=int(np.nansum(S['ovgn'][ctx.masks['FULL'], j])) if gate else 0,
                         n_gate_unknown_kept=nunk if gate else 0, n_cohorts=ncoh, n_cohorts_all_na=nallna, mean_lot_age_realized_early=mle,
                         share_lots_reaching_due=float(ld / lc) if lc > 0 else '', status='COMPUTED'))
        if r.exit_op in AREF_OPS and r.trigger != 'NONE':
            tm = trades_meta.get(r.exec_id, {})
            IN = a['IN_i']
            m = np.isin(IN[:, E.IN_KIND], [E.KD_TRIG, E.KD_RAND])
            st = IN[m, E.IN_STATUS]
            rid = np.flatnonzero(m)
            forced = tm.get('forced_requests', set())
            fset = np.array([k in forced for k in rid], bool)
            before = int(((st == 1) & ~fset).sum())
            nf = int(fset.sum())
            ex = IN[m, E.IN_EXEC]
            dd = IN[m, E.IN_DAY]
            done = ex >= 0
            rq.append(dict(exec_id=r.exec_id, n_requests=int(len(st)), n_completed_before_deadline=before, n_forced_deadline_override=nf,
                           n_completed_after_due_objective=int(len(st) - before - nf), mean_days_to_complete=float(np.mean(ex[done] - dd[done])) if done.any() else '',
                           qty_share_delayed=tm.get('qty_share_delayed', ''), status='COMPUTED'))
    return pd.DataFrame(rows), pd.DataFrame(rq, columns=['exec_id', 'n_requests', 'n_completed_before_deadline', 'n_forced_deadline_override',
                                                         'n_completed_after_due_objective', 'mean_days_to_complete', 'qty_share_delayed', 'status'])


def formation_labels(ctx):
    """(form, memory) → (门保留的 UNKNOWN 名字数, 形成日数, 全 NA 形成日数)（FULL，授权段内）。"""
    out = {}
    for f in O.FORMS:
        for m in O.MEMS:
            z = np.load(os.path.join(ctx.cd, 'overlay', '%s|%s.npz' % (f, m)), allow_pickle=False)
            st0, lab20 = z['st0'], z['lab20']
            ptr = market().formation(f, m)[0]
            dmax = ctx.d_end
            nunk = int((st0[:ptr[dmax]] == -1).sum())
            ncoh = int((np.diff(ptr[:dmax + 1]) > 0).sum())
            nallna = 0
            for d in range(dmax):
                a, b = ptr[d], ptr[d + 1]
                if b > a and (lab20[a:b] == 0).all():
                    nallna += 1
            out[(f, m)] = (nunk, ncoh, nallna)
    return out


# ------------------------------------------------------------------ 日序列 / 成交导出（B.21）
G = {}


def _exp_init(info):
    G.update(info)


def job_export(args):
    eid, h, aref = args
    dates, codes, T, sup = G['dates'], G['codes'], G['T'], G['sup']
    z = np.load(O.P('accounts_run', G['asub'], h[:2], '%s.npz' % h), allow_pickle=False)
    DY = z['DY']
    I = E.DYI
    nd = len(DY)
    keep = np.flatnonzero(sup[:nd])
    nav = DY[:, I['nav_post']]
    vprev = np.r_[O.V0, nav[:-1]]
    fl = G['FL'][eid]
    with np.errstate(all='ignore'):
        feer = DY[:, I['fee']] / vprev
        D = pd.DataFrame(dict(date=dates[keep], nav_pre=DY[keep, I['nav_pre']], nav_post=nav[keep], fee=DY[keep, I['fee']], exposure=DY[keep, I['exposure']],
                              cash_share=DY[keep, I['cash_share']], bench_ret=DY[keep, I['bench']], net_excess_ret=DY[keep, I['net_excess']],
                              gross_excess_ret=DY[keep, I['net_excess']] + feer[keep], fee_ret=feer[keep], abs_net_ret=DY[keep, I['r_net']],
                              full_bench_excess_ret=DY[keep, I['full_bench_ex']], n_holdings=DY[keep, I['n_hold']].astype(int),
                              n_lots=DY[keep, I['n_lots']].astype(int), turnover_day=0.5 * DY[keep, I['traded']] / nav[keep], g_formation=fl[keep, 0],
                              n_eff_formation=fl[keep, 3], n_gate_blocked=DY[keep, E.DY_OVGN].astype(int), overlay_active=DY[keep, E.DY_OVACT].astype(int)),
                         columns=DAILY_COLS)
    pd_ = os.path.join(G['out_root'], 'accounts', 'daily', '%s.csv' % h)
    O.atomic_write_csv(pd_, D)
    tzs = [np.load(O.P('trades_parts', s_, h[:2], '%s.npz' % h), allow_pickle=False) for s_ in G['tsubs']]
    TLi = np.concatenate([t_['TL_i'] for t_ in tzs])
    TLf = np.concatenate([t_['TL_f'] for t_ in tzs])
    adv = G['adv20']
    day = TLi[:, 0]
    sec = TLi[:, 1]
    scale = (aref if aref > 0 else 1e8) / O.V0
    with np.errstate(all='ignore'):
        a_e = np.asarray(adv[day, sec])
        realized = TLf[:, 1] * scale / a_e
        planned = np.where(np.isfinite(TLf[:, 4]), TLf[:, 4] * scale / np.asarray(adv[np.maximum(day - 1, 0), sec]), np.nan)
        navd = nav[np.clip(day, 0, nd - 1)]
        vpd = vprev[np.clip(day, 0, nd - 1)]
        filled_w = TLf[:, 1] / vpd
    due = TLi[:, 6]
    dl = TLi[:, 7]
    kind = np.array([OKN.get(int(k), 'REGULAR') for k in TLi[:, 4]])
    side = np.where(TLi[:, 5] == 0, 'BUY', 'SELL')

    def dstr(x):
        return np.array(['POST_CUTOFF' if v >= T else (dates[int(v)] if v >= 0 else '') for v in x], dtype=object)
    lot_due = np.where(np.isin(kind, ['EXIT', 'EXIT_HALF', 'EXIT_REARM', 'DUE', 'DEADLINE_OVERRIDE']), dstr(due), '')
    asgH = np.where((side == 'BUY') & (due >= 0), due - day, -1)
    coh = TLi[:, 8]
    lab20 = TLi[:, 10]
    st = TLi[:, 11]
    Tr = pd.DataFrame(dict(date=dates[day], security=codes[sec], lot_id=TLi[:, 2], cohort_id=dstr(coh), request_id=np.where(TLi[:, 3] >= 0, TLi[:, 3].astype(str), ''),
                           order_kind=kind, side=side, qty=TLf[:, 0], notional_cny=TLf[:, 1], price=TLf[:, 2], fee_cny=TLf[:, 3], lot_due=lot_due,
                           assigned_H=np.where(asgH >= 0, asgH.astype(str), ''), deadline=np.where(dl >= 0, dstr(dl), ''), planned_p=planned, realized_p=realized,
                           cvr_tertile_T0=np.array([TERT.get(int(v), '') for v in lab20], dtype=object),
                           entry_state_T0=np.array([ST0.get(int(v), '') for v in st], dtype=object),
                           planned_formation_w=np.where(side == 'BUY', TLf[:, 6], np.nan), planned_account_buy_w=np.where(side == 'BUY', TLf[:, 7], np.nan),
                           actual_filled_w=filled_w), columns=TRADE_COLS)
    pt = os.path.join(G['out_root'], 'trades', '%s.csv.gz' % h)
    O.atomic_write_csv_gz(pt, Tr)
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


def exports(ctx, workers, FL, asub='full', tsubs=('deriv', 'full'), only=None):
    R = ctx.R
    for d in (os.path.join(ctx.root, 'accounts', 'daily'), os.path.join(ctx.root, 'trades')):
        os.makedirs(d, exist_ok=True)
    info = dict(dates=ctx.dates, codes=ctx.codes, T=ctx.T, sup=ctx.masks['FULL'], adv20=np.load(os.path.join(ctx.cd, 'panels', 'adv20.npy'), mmap_mode='r'),
                out_root=ctx.root, asub=asub, tsubs=tsubs, FL=FL)
    jobs = [(r.exec_id, r.exec_hash, float(r.A_ref) if getattr(r, 'A_ref', '') else aref_of(r.exit_op)) for r in R.itertuples(index=False)
            if only is None or r.exec_id in only]
    with get_context('fork').Pool(min(workers, len(jobs)), initializer=_exp_init, initargs=(info,)) as pool:
        out = list(pool.imap_unordered(job_export, jobs))
    di = pd.DataFrame([dict(exec_hash=x['exec_hash'], exec_id=x['exec_id'], file='accounts/daily/%s.csv' % x['exec_hash'], n_rows=x['daily_rows'],
                            date_min=x['date_min'], date_max=x['date_max']) for x in out]).sort_values('exec_id')
    ti = pd.DataFrame([dict(exec_id=x['exec_id'], file='trades/%s.csv' % x['exec_hash'], n_rows=x['trade_rows'], n_fills=x['n_fills']) for x in out]).sort_values('exec_id')
    O.atomic_write_csv(os.path.join(ctx.root, 'accounts', 'daily', 'INDEX.csv'), di)
    O.atomic_write_csv(os.path.join(ctx.root, 'trades', 'INDEX.csv'), ti)
    return {x['exec_id']: x['meta'] for x in out}


def aref_of(exit_op):
    return {'EXIT_GATE_LIQ_1E8': 1e8, 'EXIT_GATE_LIQ_5E8': 5e8, 'GATE_REARM_1E8': 1e8, 'GATE_REARM_5E8': 5e8}.get(exit_op, 0.0)


# ------------------------------------------------------------------ 随机（B.12）
def full_D(df, pre='D_'):
    num = 0.0
    den = 0
    for s in SEG4:
        v = df['%s%s' % (pre, s)].to_numpy(float)
        n = df['n_%s' % s].to_numpy(float)
        num = num + np.nan_to_num(v) * n
        den = den + n
    with np.errstate(all='ignore'):
        return num / den


def load_paths(tags):
    parts = []
    for t in tags:
        p = O.P('randoms', 'random_paths_%s.csv' % t)
        if os.path.exists(p) and os.path.getsize(p) > 5:
            parts.append(pd.read_csv(p, keep_default_na=False, na_values=['']))
    if not parts:
        return pd.DataFrame(columns=['owner_exec_id', 'mechanism', 'path_id', 'status'])
    P = pd.concat(parts, ignore_index=True)
    return P[P.status == 'OK'].drop_duplicates(['owner_exec_id', 'mechanism', 'path_id'], keep='last')


def randoms_tables(ctx, net, tags):
    """randoms_E6r（1,408 × 6）、random_paths_main（policy_primary 引用全部路径）、random_tilt_feasibility（入场层 × 6）、matching（退出层匹配机制 × 段）。"""
    R = ctx.R
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6r.csv'))
    P = load_paths(tags)
    byid = R.set_index('exec_id', drop=False)
    grp = {k: g for k, g in P.groupby(['owner_exec_id', 'mechanism'])} if len(P) else {}
    rows, prows, frows, mrows = [], [], [], []
    for ref in RR.itertuples(index=False):
        e = ref.owner_exec_id
        j = ctx.col[e]
        layer = ref.layer
        refc = 'flat_same_exit_exec_id' if layer == 'ENTRY' else 'noexit_same_overlay_exec_id'
        k = ctx.col[byid.loc[e][refc]]
        X = grp.get((e, ref.mechanism))
        X = X.sort_values('path_id') if X is not None else pd.DataFrame()
        npth = len(X)
        det = ref.draw_kind == 'DETERMINISTIC'
        mt = float(ref.mcse_target) if ref.mcse_target else None
        fd = full_D(X) if npth else np.array([])
        ent = ref.mechanism in ENTRY_MECHS
        segs_of = {s: (SEG4 if s in ('FULL', 'G4') else [s]) for s in SEG6}

        def ssum(col, s):
            return float(sum(X['%s_%s' % (col, q)].sum() for q in segs_of[s])) if npth else 0.0
        # 可比性（FULL 口径）
        comp = 'COMPARABLE'
        req_f, unm_f = ssum('req', 'FULL'), ssum('unm', 'FULL')
        ush_f = unm_f / req_f if req_f > 0 else np.nan
        if ref.mechanism in ('AMOUNT_MATCH_V2', 'COUNT_ISK', 'AMOUNT_ISK_V2') and np.isfinite(ush_f) and ush_f > NOT_COMPARABLE_UNMATCHED:
            comp = 'CONTROL_NOT_COMPARABLE'
        pint_f = ssum('pint', 'FULL')
        oint_f = float(sum(X['oint_%s' % q].iloc[0] for q in SEG4)) * npth if npth else 0.0
        if ref.mechanism == 'BERNOULLI_FIRSTHIT' and oint_f > 0 and not (INTENSITY_BAND[0] <= pint_f / oint_f <= INTENSITY_BAND[1]):
            comp = 'CONTROL_NOT_COMPARABLE'
        ndraw_f = sum(ssum(c, 'FULL') for c in ('erfeas', 'ernom', 'erlim', 'erid', 'erdeg'))
        if ref.mechanism in ('RANDOM_TILT_TICKETS', 'RANDOM_GATE_TILT_JOINT') and ndraw_f > 0 and \
                (ssum('erlim', 'FULL') + ssum('ernom', 'FULL')) / ndraw_f > TICKET_LIMIT_SHARE:
            comp = 'CONTROL_NOT_COMPARABLE'
        sdeg = bool(ent and npth and ssum('erfeas', 'FULL') == 0 and ndraw_f > 0)
        for s in SEG6:
            real = dseg(net, s, j, k)
            if s == 'FULL':
                v = fd
            elif s == 'G4':
                v = np.median(np.vstack([X['D_%s' % q].to_numpy(float) for q in SEG4]), axis=0) if npth else np.array([])
            else:
                v = X['D_%s' % s].to_numpy(float) if npth else np.array([])
            v = v[np.isfinite(v)]
            nv = len(v)
            mean = float(np.mean(v)) if nv else np.nan
            sd = float(np.std(v, ddof=1)) if nv > 1 else np.nan
            mcse = sd / math.sqrt(nv) if nv > 1 else np.nan
            rank = float((np.sum(v < real) + 0.5 * np.sum(v == real)) / nv) if nv else np.nan
            req, unm = ssum('req', s), ssum('unm', s)
            st = 'COMPUTED' if npth else 'NOT_RUN'
            if (not det) and mt is not None and s == 'FULL' and npth >= int(ref.max_paths) and np.isfinite(mcse) and mcse > mt:
                st = 'MC_LIMIT'
            if npth and comp == 'CONTROL_NOT_COMPARABLE':
                st = 'CONTROL_NOT_COMPARABLE'                  # 整个引用不可比：各段同标，c4 记 NA（CONTROL_NOT_COMPARABLE）
            elif npth and sdeg:
                st = 'STRUCTURAL_DEGENERATE'                   # 无一次非恒等抽样：控制结构性无辨别力（plan §8.1），各段同标
            pint_s = ssum('pint', s)
            oint_s = float(sum(X['oint_%s' % q].iloc[0] for q in segs_of[s])) * npth if npth else 0.0
            rows.append(dict(ref_id=ref.ref_id, owner_exec_id=e, mechanism=ref.mechanism, layer=layer, policy_primary=ref.policy_primary, segment=s,
                             paths=npth if not det else min(npth, 1), start_paths=int(ref.start_paths), max_paths=int(ref.max_paths), mcse_target=ref.mcse_target,
                             real_D_ann_pp=real, rand_mean_D_ann_pp=mean, rand_sd_D_ann_pp='' if det else fnum(sd), mcse='' if det else fnum(mcse),
                             rank_real=rank, unmatched_share=(unm / req if req > 0 else '') if ref.mechanism in MATCH_MECHS else '',
                             intensity_ratio=((pint_s / oint_s) if oint_s > 0 else (1.0 if pint_s == 0 else '')) if ref.mechanism == 'BERNOULLI_FIRSTHIT' else '',
                             control_comparability=comp, structural_degenerate='true' if sdeg else 'false', status=st))
            if ent and npth:
                nf_, nn_, nl_, ni_, ndg = (ssum(c, s) for c in ('erfeas', 'ernom', 'erlim', 'erid', 'erdeg'))
                nd_ = nf_ + nn_ + nl_ + ni_ + ndg
                dw = float(max(X['dwmax_%s' % q].max() for q in segs_of[s]))
                dw2 = float(max(X['dw2max_%s' % q].max() for q in segs_of[s]))
                coh_p, coh_o = ssum('ercoh', s), ssum('ercohown', s)
                cl = (ssum('ovb', s) - ssum('ovbown', s)) / coh_p if coh_p > 0 else np.nan
                frows.append(dict(ref_id=ref.ref_id, owner_exec_id=e, mechanism=ref.mechanism, segment=s, n_cohort_draws=int(nd_), n_feasible=int(nf_ + ni_ + ndg),
                                  n_identity_draw=int(ni_ + ndg), n_nonidentity_draw=int(nf_), n_proved_no_match=int(nn_), n_algorithm_limit=int(nl_),
                                  structural_degenerate_share=float(ndg / nd_) if nd_ > 0 else '', max_rel_sum_w_diff=dw, max_rel_sum_w2_diff=dw2,
                                  gen_layer_B_diff_mean=float(ssum('ershort', s) / nd_) if nd_ > 0 else '', closed_loop_B_diff_mean=fnum(cl), status='COMPUTED'))
            if ref.mechanism in MATCH_MECHS and s != 'G4' and npth:
                wi, cr = ssum('within', s), ssum('cross', s)
                nrq, nun = ssum('nreq', s), ssum('nunm', s)
                navm = float(np.nanmean(np.where(ctx.masks[s], 1.0, np.nan)))      # 占位（NAV 份额见下）
                kk = max(npth, 1)
                nd = int(ctx.masks[s].sum())
                mrows.append(dict(owner_exec_id=e, mechanism=ref.mechanism, segment=s, requested_cny=req / kk, matched_within_cny=wi / kk, matched_cross_cny=cr / kk,
                                  unmatched_cny=unm / kk, unmatched_nav_share=float(unm / kk / (O.V0 * nd)) if nd else '', n_requests=nrq / kk,
                                  n_unmatched_requests=nun / kk, control_comparability=comp, status='COMPUTED'))
        if ref.policy_primary == 'true' and npth:
            for r_, f_ in zip(X.itertuples(index=False), fd):
                prows.append(dict(ref_id=ref.ref_id, owner_exec_id=e, mechanism=ref.mechanism, path_id=int(r_.path_id), seed=str(r_.seed), FULL_D_ann_pp=f_,
                                  draw_interpretation=draw_interp(ref.mechanism, r_), in_first_256=1 if int(r_.path_id) < 256 else 0))
    RD = pd.DataFrame(rows)
    PM = pd.DataFrame(prows, columns=['ref_id', 'owner_exec_id', 'mechanism', 'path_id', 'seed', 'FULL_D_ann_pp', 'draw_interpretation', 'in_first_256'])
    FE = pd.DataFrame(frows)
    MT = pd.DataFrame(mrows)
    return RD, PM, FE, MT, P


def draw_interp(mech, r):
    if mech not in ('RANDOM_TILT_TICKETS', 'RANDOM_GATE_TILT_JOINT'):
        return 'NOT_APPLICABLE'
    nf = sum(getattr(r, 'erfeas_%s' % q.replace('-', '_'), 0) if False else 0 for q in SEG4)
    d = r._asdict()
    nf = sum(d.get('erfeas_%s' % q, 0) for q in SEG4)
    ni = sum(d.get('erid_%s' % q, 0) + d.get('erdeg_%s' % q, 0) for q in SEG4)
    if nf > 0:
        return 'NONIDENTITY_DRAW'
    if ni > 0:
        return 'IDENTITY_DRAW'
    return 'NO_COMPLETE_DRAW'


# ------------------------------------------------------------------ 复现 / 运行恒等（B.17）
def replication(ctx):
    """58 个 E6Q 同坐标锚（FLAT）：E6r B 结果 DY 前 102 列 vs E6q 同坐标账户 DY，四段逐日相对差。"""
    R = ctx.R
    E6 = O.read_csv(O.E6Q('registration', 'registry_E6q.csv')).set_index('exec_id')
    rows = []
    for r in R[R.replication_source == 'E6Q'].itertuples(index=False):
        h6 = r.replication_exec_hash
        a = np.load(acct_file(ctx, r.exec_hash), allow_pickle=False)['DY']
        b = np.load(O.E6Q('accounts_run', 'full', h6[:2], '%s.npz' % h6), allow_pickle=False)['DY']
        nd = min(len(a), len(b))
        for s in SEG4:
            m = (ctx.segi == s)[:nd]
            x = a[:nd][m, :102]
            y = b[:nd][m, :102]
            fa, fb = np.isfinite(x), np.isfinite(y)
            if not np.array_equal(fa, fb):
                md = float('inf')
            else:
                d = np.abs(x[fa] - y[fa])
                sc = np.maximum(np.maximum(np.abs(x[fa]), np.abs(y[fa])), 1.0)
                md = float(np.max(d / sc)) if d.size else 0.0
            rows.append(dict(e6r_exec_id=r.exec_id, source_round='E6Q', source_exec_id=r.replication_exec_id, segment=s, max_rel_diff_daily=md, tolerance=1e-9,
                             status='PASS' if md <= 1e-9 else 'DIFFERS'))
    return pd.DataFrame(rows)


def run_identities(ctx, S, acc, rep, P):
    rows = []
    c = O.FEE_RATE
    V0 = O.V0
    cash_d = tele = tok = feed = brg = 0.0
    pol = ctx.refidx('policy_reference_exec_id')
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
        if ctx.R.scenario.iloc[j] == O.FEAS:
            feed = max(feed, float(np.max(np.abs(DY[:, I['fee']] - c * DY[:, I['traded']]))) / V0)
        k = pol[j]
        if k >= 0:
            m = ctx.masks['FULL']
            b = S['bench'][m, j]
            ok = np.isfinite(b)
            pd_ = S['rnet'][m, j] - S['rnet'][m, k]
            sd_ = S['ne'][m, j] - S['ne'][m, k]
            xb = (S['xprev'][m, j] - S['xprev'][m, k]) * b
            if ok.any():
                brg = max(brg, float(np.max(np.abs(pd_[ok] - (sd_[ok] + xb[ok])))))
    rows.append(dict(check_id='CASH_EQUATION', description='全部 350 账户逐日：Δ现金 = 卖款 − 买款 − 费用（相对 V0）', exec_id='', value='', max_abs_diff=cash_d,
                     tolerance=1e-9, status='PASS' if cash_d <= 1e-9 else 'DIFFERS'))
    rows.append(dict(check_id='NAV_TELESCOPE', description='全部账户：Π(1 + r_net) = 末日 NAV / V0', exec_id='', value='', max_abs_diff=tele, tolerance=1e-8,
                     status='PASS' if tele <= 1e-8 else 'DIFFERS'))
    rows.append(dict(check_id='TOKEN_CONSERVATION', description='全部账户逐日：标签余额变动 = 新增 − 常规消费 − 额外消费 − 到期重分类（相对 V0）', exec_id='', value='',
                     max_abs_diff=tok, tolerance=1e-9, status='PASS' if tok <= 1e-9 else 'DIFFERS'))
    rows.append(dict(check_id='FEE_NET_ORDER', description='FEASIBLE 账户逐日：费用 = 4bp × Σ|证券净订单名义|（引擎 traded 列）', exec_id='', value='', max_abs_diff=feed,
                     tolerance=1e-9, status='PASS' if feed <= 1e-9 else 'DIFFERS'))
    rows.append(dict(check_id='SCALED_PRODUCT_BRIDGE', description='全部有政策参照的账户逐日：产品差 r_net 差 = 缩放超额差 + (x_prev 差) × 基准（plan audit_scaled_product_bridge）',
                     exec_id='', value='', max_abs_diff=brg, tolerance=1e-12, status='PASS' if brg <= 1e-12 else 'DIFFERS'))
    tk = P[P.mechanism.isin(['RANDOM_TILT_TICKETS', 'RANDOM_GATE_TILT_JOINT'])] if len(P) else P
    dmax = 0.0
    if len(tk):
        dmax = float(max(tk[['dwmax_%s' % q for q in SEG4]].max().max(), tk[['dw2max_%s' % q for q in SEG4]].max().max()))
    rows.append(dict(check_id='TICKET_CONSERVATION', description='入场 TICKETS / JOINT 随机路径逐抽样：随机票据与同快照 would-be 真实票据的 Σw、Σw² 相对差最大值（%d 条路径）' % len(tk),
                     exec_id='', value=len(tk), max_abs_diff=dmax, tolerance=1e-9, status='PASS' if dmax <= 1e-9 else 'DIFFERS'))
    rmax = float(rep.max_rel_diff_daily.max()) if len(rep) else 0.0
    rows.append(dict(check_id='REPLICATION_E6Q_ACCOUNTS', description='%d 个 E6Q 同坐标锚 × 四段逐日 DY 前 102 列（B 相结果；相对）' % rep.e6r_exec_id.nunique() if len(rep) else 'B 相复现',
                     exec_id='', value=int((rep.status == 'PASS').sum()) if len(rep) else 0, max_abs_diff=rmax, tolerance=1e-9, status='PASS' if rmax <= 1e-9 else 'DIFFERS'))
    ce = P['ck_equal'] if (len(P) and 'ck_equal' in P.columns) else pd.Series([], dtype=object)
    ce = pd.to_numeric(ce, errors='coerce').dropna()
    rows.append(dict(check_id='CHECKPOINT_RESTORE_IDEMPOTENT', description='随机路径：每个 (owner, 机制) 的 0 号路径整段重跑 vs A2 末紧凑 checkpoint 续跑，后段 DY 与 S_i（除批次计数）逐位相同'
                     '（%d / %d 相同）' % (int(ce.sum()), len(ce)), exec_id='', value=int(ce.sum()), max_abs_diff=float(len(ce) - ce.sum()), tolerance=0.0,
                     status='PASS' if len(ce) and ce.all() else ('DIFFERS' if len(ce) else 'NOT_RUN')))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 主流程
def write(ctx, rel, df, gz=False):
    p = ctx.out(*rel.split('/'))
    if gz:
        p = p + '.gz'
        O.atomic_write_csv_gz(p, df)
    else:
        O.atomic_write_csv(p, df)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=['A2', 'B'], required=True)
    ap.add_argument('--fake_post', action='store_true')
    ap.add_argument('--root', default='')
    ap.add_argument('--workers', type=int, default=64)
    ap.add_argument('--dry_extras', action='store_true')
    ap.add_argument('--rand_tags', default='', help='随机路径表标签（逗号分隔；空跑可用 A2.partial）')
    a = ap.parse_args()
    t0 = time.time()
    root = O.P(*a.root.split('/')) if a.root else None
    ctx = Ctx(a.phase, a.fake_post, root)
    S, acc = load_all(ctx)
    O.log('载入 %d 账户；支持日 %d' % (len(ctx.ids), ctx.support_days))
    FL = formation_layer(ctx)
    FLAB = formation_labels(ctx)
    boot = Boot(ctx)
    Sm, net, gross = summary(ctx, S, acc, boot, FL)
    outs = [write(ctx, 'statistics/account_summary_E6r.csv', Sm)]
    O.log('account_summary %d 行' % len(Sm))
    outs.append(write(ctx, 'statistics/comparison_results_E6r.csv', comparison_results(ctx, S, net, gross, boot)))
    outs.append(write(ctx, 'statistics/compound_results_E6r.csv', compound_results(ctx, S, net, gross, boot)))
    outs.append(write(ctx, 'statistics/yearly_E6r.csv', yearly(ctx, S)))
    CC, BE = cost_tables(ctx, S)
    outs.append(write(ctx, 'statistics/cost_curve_E6r.csv', CC, gz=True))
    outs.append(write(ctx, 'statistics/breakeven_E6r.csv', BE))
    O.log('cost_curve %d 行；breakeven %d 行' % (len(CC), len(BE)))
    FB, FP = feedback_tables(ctx, S)
    outs.append(write(ctx, 'statistics/cost_feedback_E6r.csv', FB))
    outs.append(write(ctx, 'statistics/cost_feedback_pairs_E6r.csv', FP))
    outs.append(write(ctx, 'statistics/weights_E6r.csv', weights_table(ctx, S, FL)))
    meta = {}
    real_b = a.phase == 'B' and not a.fake_post
    if real_b:
        meta = exports(ctx, a.workers, FL)
        O.log('日序列 / 成交导出完成')
    elif a.dry_extras:
        meta = exports(ctx, a.workers, FL, 'deriv', ('deriv',))
        O.log('空跑：推导段日序列 / 成交导出完成')
    EV, RQ = event_tables(ctx, S, acc, meta, FLAB)
    outs.append(write(ctx, 'events/event_counts_E6r.csv', EV))
    outs.append(write(ctx, 'events/exit_requests_E6r.csv', RQ))
    if real_b or a.dry_extras:
        tags = tuple(a.rand_tags.split(',')) if a.rand_tags else (('B', 'B_topup') if real_b else ('A2',))
        RD, PM, FE, MT, P = randoms_tables(ctx, net, tags)
        outs.append(write(ctx, 'statistics/randoms_E6r.csv', RD))
        outs.append(write(ctx, 'statistics/random_paths_main_E6r.csv', PM))
        outs.append(write(ctx, 'statistics/random_tilt_feasibility_E6r.csv', FE))
        outs.append(write(ctx, 'statistics/matching_E6r.csv', MT))
        REP = replication(ctx)
        outs.append(write(ctx, 'verify/replication_E6r.csv', REP))
        RI = run_identities(ctx, S, acc, REP, P)
        outs.append(write(ctx, 'verify/identities_E6r_runs.csv', RI))
        O.log('随机 / 复现 / 运行恒等：%s' % RI.status.value_counts().to_dict())
    facts = dict(phase=a.phase, fake_post=a.fake_post, support_days=ctx.support_days, n_accounts=len(ctx.ids), summary_rows=len(Sm), cost_rows=len(CC),
                 wall_s=round(time.time() - t0, 1), rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.atomic_write_json(ctx.out('statistics', 'stats_facts_E6r.json'), facts)
    O.write_receipt('E6r_stats_%s%s' % (a.phase, '_fake' if a.fake_post else ''), outs, code=[__file__, O.__file__, E.__file__], **facts)
    print(json.dumps(facts, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
