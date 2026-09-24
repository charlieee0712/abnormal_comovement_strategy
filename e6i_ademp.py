#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 0 ADEMP 仿真 (设计见 checks/simulation_ADEMP.md; 先写后跑)。
直接调 e6i_features 的原函数 —— 同时是本轮实现的数值检验。结果是误差表, 不是 PASS 门。

用法:
  python3 e6i_ademp.py --panel price --cells 0-44 [--paths 2000] [--steps 390]
  python3 e6i_ademp.py --panel price_xs | spread | activity | info
  python3 e6i_ademp.py --merge
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import time
import glob
import math
import argparse
import itertools
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE

OUT = os.path.join(I.RES, 'checks', 'sim')
MUS = (-0.01, -0.005, 0.0, 0.005, 0.01)
SIGS = (0.20, 0.40, 0.80)
ONR = (0.0, 0.5, 1.0)
VARIANTS = ('clean', 'tick', 'limit', 'sparse', 'suspend')
DAYS = 250
WINS = (10, 20)


def price_cells():
    cells = [dict(mu=m, sig=s, onr=o, variant=v, rho=0.0, regime='const')
             for v in VARIANTS for m in MUS for s in SIGS for o in ONR]
    for s in SIGS:
        for o in (0.5, 1.0):
            cells.append(dict(mu=0.0, sig=s, onr=o, variant='clean', rho=0.5, regime='const'))
        cells.append(dict(mu=0.0, sig=s, onr=0.5, variant='clean', rho=0.0, regime='vol_double'))
    return cells


def simulate_ohlc(rng, n_paths, cell, steps):
    """返回 dict of (DAYS, n_paths) log 量: o, c, h, l, r, 以及 touch (限价) 与价格水平 (tick 用)。
       cell['sig'] / cell['mu'] 可以是标量或长度 n_paths 的数组 (截面子面板每只股票各自 σ 与漂移)。
       停牌简化: 停牌日不产生价格变化 (复牌从上一有效收盘续走), 只检验估计量的缺失处理。"""
    P, D = n_paths, DAYS
    sd = np.broadcast_to(np.asarray(cell['sig'], float) / math.sqrt(252.0), (P,)).copy()
    mu = np.broadcast_to(np.asarray(cell['mu'], float), (P,)).copy()
    fac = np.ones(D)
    if cell.get('regime') == 'vol_double':
        fac[D // 2:] = 2.0
    sd_pd = sd[:, None] * fac[None, :]                        # (P, D) 日内日 σ
    on_sd = cell['onr'] * sd                                  # (P,)
    z = rng.standard_normal((P, D, steps))
    inc = (mu[:, None, None] / steps) + (sd_pd[:, :, None] / math.sqrt(steps)) * z
    X = np.concatenate([np.zeros((P, D, 1)), np.cumsum(inc, axis=2)], axis=2)   # 开盘为 0
    z_on = rng.standard_normal((P, D))
    if cell.get('rho', 0.0) != 0.0:
        zc = (X[:, :, -1] - mu[:, None]) / (sd_pd + 1e-300)
        z_on = cell['rho'] * zc + math.sqrt(1 - cell['rho'] ** 2) * z_on
    o_true = on_sd[:, None] * z_on
    logC = np.zeros((P, D))
    logO = np.zeros((P, D))
    lc_prev = np.full(P, math.log(10.0))
    lclose = np.zeros((P, D))
    Hlog = np.zeros((P, D))
    Llog = np.zeros((P, D))
    touch = np.zeros((P, D), bool)
    valid = np.ones((P, D), bool)
    v = cell['variant']
    if v == 'suspend':
        valid = rng.random((P, D)) >= 0.05
    for d in range(D):
        lo_ = lc_prev + o_true[:, d]
        path = lo_[:, None] + X[:, d, :]
        if v == 'tick':
            path = np.log(np.maximum(np.round(np.exp(path) * 100.0) / 100.0, 0.01))
            lcp = np.log(np.round(np.exp(lc_prev) * 100.0) / 100.0)
        else:
            lcp = lc_prev
        if v == 'limit':
            ub, lb = lcp + math.log(1.1), lcp + math.log(0.9)
            hit_u = np.maximum.accumulate(path >= ub[:, None], axis=1)
            path = np.where(hit_u, ub[:, None], path)
            hit_l = np.maximum.accumulate(path <= lb[:, None], axis=1)
            path = np.where(hit_l, lb[:, None], path)
            touch[:, d] = hit_u[:, -1] | hit_l[:, -1]
        if v == 'sparse':
            tr = rng.random(path.shape) < 0.10
            tr[:, 0] |= ~tr.any(axis=1)                     # 至少 1 笔 (开盘)
            obs = np.where(tr, path, np.nan)
            first = np.argmax(tr, axis=1)
            last = path.shape[1] - 1 - np.argmax(tr[:, ::-1], axis=1)
            rows = np.arange(P)
            O_, C_ = path[rows, first], path[rows, last]
            H_, L_ = np.nanmax(obs, axis=1), np.nanmin(obs, axis=1)
        else:
            O_, C_ = path[:, 0], path[:, -1]
            H_, L_ = path.max(axis=1), path.min(axis=1)
        logO[:, d], logC[:, d], Hlog[:, d], Llog[:, d] = O_, C_, H_, L_
        lclose[:, d] = lcp
        lc_prev = np.where(valid[:, d], C_, lc_prev)        # 停牌日不更新前收
    T = lambda a: np.ascontiguousarray(a.T)
    o = logO - lclose
    c = logC - logO
    h = Hlog - logO
    l = Llog - logO
    for a in (o, c, h, l):
        a[~valid] = np.nan
    return dict(o=T(o), c=T(c), h=T(h), l=T(l), r=T(o + c), touch=T(touch & valid),
                Hh=T(np.exp(Hlog)), L=T(np.exp(Llog)), sd_day=sd_pd[0], on_sd=float(on_sd[0]))


def targets(cell, sd_day, on_sd):
    """逐日目标 (主面板各路径 σ 相同, 用第一条路径的日 σ 序列)。"""
    iv = sd_day ** 2
    tot = iv + on_sd ** 2 + 2 * cell.get('rho', 0.0) * on_sd * sd_day
    return dict(intraday=iv, total=tot, on=np.full_like(iv, on_sd ** 2), oc=iv)


EST = {
    # name: (daily fn or special, target key, policy)
    'park': ('park', 'intraday'), 'gk': ('gk', 'intraday'), 'rs': ('rs', 'intraday'),
    'mj': ('mj', 'intraday'), 'yz': ('yz', 'total'), 'cc': ('cc', 'total'),
    'on': ('on', 'on'), 'oc': ('oc', 'oc'),
}


def estimate(B, name, w, policy):
    if name == 'park':
        return FE.rmean(FE._range_policy(B, FE._daily_park(B), policy), w)
    if name == 'gk':
        return FE.rmean(FE._range_policy(B, FE._daily_gk(B), policy), w)
    if name == 'rs':
        return FE.rmean(FE._range_policy(B, FE._daily_rs(B), policy), w)
    if name == 'mj':
        return FE.rmean(FE._range_policy(B, FE._daily_mj(B), policy), w)
    if name == 'yz':
        return FE._yz(B, w, policy)
    if name == 'cc':
        return FE.rvar(B.r, w)
    if name == 'on':
        return FE.rvar(B.o, w)
    if name == 'oc':
        return FE.rvar(B.c, w)
    raise KeyError(name)


def run_price(cells_idx, n_paths, steps, chunk=100):
    cells = price_cells()
    os.makedirs(OUT, exist_ok=True)
    for ci in cells_idx:
        cell = cells[ci]
        t0 = time.time()
        rng = np.random.default_rng(20260923 + ci * 7919 + steps)
        acc = {}
        for start in range(0, n_paths, chunk):
            n = min(chunk, n_paths - start)
            sim = simulate_ohlc(rng, n, cell, steps)
            B = SimpleNamespace(o=sim['o'], c=sim['c'], h=sim['h'], l=sim['l'], r=sim['r'],
                                touch=sim['touch'], Hh=sim['Hh'], L=sim['L'])
            tg = targets(cell, sim['sd_day'], sim['on_sd'])
            pols = ('OBS', 'LIMIT_SENS') if cell['variant'] == 'limit' else ('OBS',)
            for name, (_, tkey) in EST.items():
                for pol in (pols if name in ('park', 'gk', 'rs', 'mj', 'yz') else ('OBS',)):
                    for w in WINS:
                        est = estimate(B, name, w, pol)            # (DAYS, n)
                        # 目标: 窗内日目标的均值 (分段波动时逐窗不同)
                        tt = pd.Series(tg[tkey]).rolling(w, min_periods=1).mean().values
                        rel = est / tt[:, None] - 1.0
                        rel[:w - 1] = np.nan
                        key = (name, pol, w)
                        a = acc.setdefault(key, dict(path_means=[], sq=0.0, n=0, cov=0, tot=0))
                        with np.errstate(all='ignore'):
                            pm = np.nanmean(rel, axis=0)
                        a['path_means'].append(pm)
                        f = np.isfinite(rel)
                        a['sq'] += float(np.nansum(rel ** 2))
                        a['n'] += int(f.sum())
                        a['cov'] += int(f[w - 1:].sum())
                        a['tot'] += int(rel[w - 1:].size)
        rows = []
        for (name, pol, w), a in acc.items():
            pm = np.concatenate(a['path_means'])
            pm = pm[np.isfinite(pm)]
            bias = float(pm.mean()) if len(pm) else np.nan
            mcse = float(pm.std(ddof=1) / math.sqrt(len(pm))) if len(pm) > 1 else np.nan
            mis = (name == 'mj' and cell['mu'] != 0.0) or (name in ('park', 'gk') and
                                                           cell['mu'] != 0.0)
            rows.append(dict(panel='price', cell=ci, steps=steps, n_paths=n_paths, **cell,
                             estimator=name, policy=pol, window=w, rel_bias=bias,
                             rel_rmse=math.sqrt(a['sq'] / max(a['n'], 1)), mcse=mcse,
                             mcse_ok=bool(np.isfinite(mcse) and mcse <= 0.005),
                             coverage=a['cov'] / max(a['tot'], 1),
                             misspecified=bool(mis)))
        tag = 'price_c%03d_s%d_p%d' % (ci, steps, n_paths)
        I.atomic_write_csv(os.path.join(OUT, tag + '.csv'), pd.DataFrame(rows))
        print('  cell %d %s mu=%+.3f sig=%.2f onr=%.1f rho=%.1f %s: %.0fs'
              % (ci, cell['variant'], cell['mu'], cell['sig'], cell['onr'], cell['rho'],
                 cell['regime'], time.time() - t0), flush=True)


def run_price_xs(n_rep=40, n_stock=200, steps=390):
    """截面排序: 同格 200 只, σ_i = σ·exp(0.5 z); Spearman(20 日估计, 真 σ²) 逐窗平均。"""
    rows = []
    for mu, onr in itertools.product((0.0, 0.005), (0.0, 0.5)):
        rng = np.random.default_rng(777 + int(mu * 1e4) + int(onr * 10))
        sc = {k: [] for k in EST}
        for rep in range(n_rep):
            sig_i = 0.40 * np.exp(0.5 * rng.standard_normal(n_stock))
            # 每只股票各自 σ; 漂移 = 同一日 log 漂移 (不随 σ 缩放), 截面排序对象 = 真 σ²
            cell = dict(mu=mu, sig=sig_i, onr=onr, variant='clean', rho=0.0, regime='const')
            sim = simulate_ohlc(rng, n_stock, cell, steps)
            B = SimpleNamespace(o=sim['o'], c=sim['c'], h=sim['h'], l=sim['l'], r=sim['r'],
                                touch=np.zeros_like(sim['touch']))
            true = (sig_i ** 2)
            for name in EST:
                est = estimate(B, name, 20, 'OBS')
                rhos = []
                for d in range(19, DAYS, 10):
                    e = est[d]
                    m = np.isfinite(e)
                    if m.sum() > 20:
                        rhos.append(pd.Series(e[m]).corr(pd.Series(true[m]), method='spearman'))
                sc[name].append(np.mean(rhos))
        for name, v in sc.items():
            v = np.asarray(v)
            rows.append(dict(panel='price_xs', mu=mu, onr=onr, estimator=name, window=20,
                             spearman_true_var=float(v.mean()),
                             mcse=float(v.std(ddof=1) / math.sqrt(len(v))), n_rep=len(v)))
        print('  xs mu=%.3f onr=%.1f done' % (mu, onr), flush=True)
    I.atomic_write_csv(os.path.join(OUT, 'price_xs.csv'), pd.DataFrame(rows))


def run_spread(n_paths=500, steps=390):
    rows = []
    for sig in (0.20, 0.40):
        for s in (0.0, 0.001, 0.005, 0.01, 0.02):
            t0 = time.time()
            rng = np.random.default_rng(4242 + int(s * 1e4) + int(sig * 100))
            sd = sig / math.sqrt(252.0)
            P, D = n_paths, DAYS
            z = rng.standard_normal((P, D, steps))
            mid = math.log(10.0) + np.cumsum((sd / math.sqrt(steps)) * z.reshape(P, D * steps),
                                             axis=1).reshape(P, D, steps)
            side = rng.choice((-1.0, 1.0), size=mid.shape)
            px = mid + side * (s / 2.0)
            O = np.exp(px[:, :, 0]).T
            C = np.exp(px[:, :, -1]).T
            Hh = np.exp(px.max(axis=2)).T
            L = np.exp(px.min(axis=2)).T
            res = {}
            for w in (20, 60):
                lc = np.log(C)
                eta = (np.log(Hh) + np.log(L)) / 2
                q = 4 * (FE.lag(lc, 1) - FE.lag(eta, 1)) * (FE.lag(lc, 1) - eta)
                res[('ar', w)] = np.sqrt(np.maximum(FE.rmean(q, w), 0.0))
                res[('ar_signed_meanq', w)] = FE.rmean(q, w)
                h1, l1 = FE.lag(Hh, 1), FE.lag(L, 1)
                with np.errstate(all='ignore'):
                    beta = np.log(h1 / l1) ** 2 + np.log(Hh / L) ** 2
                    gam = np.log(np.maximum(h1, Hh) / np.minimum(l1, L)) ** 2
                    k = 3 - 2 * math.sqrt(2)
                    alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / k - np.sqrt(gam / k)
                    csd = 2 * np.tanh(alpha / 2)
                res[('cs_clip_then_mean', w)] = FE.rmean(np.maximum(csd, 0.0), w)
                res[('cs_mean_then_clip', w)] = np.maximum(FE.rmean(csd, w), 0.0)
                res[('cs_signed_mean', w)] = FE.rmean(csd, w)
                dl = lc - FE.lag(lc, 1)
                rq = -FE.rcov(dl, FE.lag(dl, 1), w)
                res[('roll', w)] = 2 * np.sqrt(np.maximum(rq, 0.0))
                Bx = SimpleNamespace(Oa=O, Ca=C, Ha=Hh, La=L)
                res[('edge', w)] = FE._edge(Bx, w, sign=False)
                res[('edge_signed', w)] = FE._edge(Bx, w, sign=True)
            for (name, w), est in res.items():
                e = est[w:]
                pm = np.nanmean(e, axis=0)
                pm = pm[np.isfinite(pm)]
                rows.append(dict(panel='spread', sig=sig, spread=s, estimator=name, window=w,
                                 mean_est=float(pm.mean()),
                                 bias=float(pm.mean() - s),
                                 rel_bias=(float(pm.mean() / s - 1) if s > 0 else np.nan),
                                 mcse=float(pm.std(ddof=1) / math.sqrt(len(pm))),
                                 coverage=float(np.isfinite(e).mean())))
            print('  spread sig=%.2f s=%.3f %.0fs' % (sig, s, time.time() - t0), flush=True)
    I.atomic_write_csv(os.path.join(OUT, 'spread.csv'), pd.DataFrame(rows))


def run_activity(n=500, n_rep=100):
    """六情景, 每情景把一个参数在截面上变化; 报 T 成员与该参数的截面 Spearman (越接近 ±1 越敏感)。"""
    members = ['T_mean20', 'T_cv20', 'T_logstd20', 'T_madrel20', 'T_iqrrel20', 'T_std20',
               'T_trend20', 'T_resid20', 'T_ewcv20', 'T_r5_20', 'T_cvmask20', 'T_cvpre20',
               'T_evlevel']
    fns = {m: FE.member(m)['fn'] for m in members}
    rows = []
    D = DAYS
    for scen in ('scale', 'trend', 'pulse', 'events', 'level_constCV', 'cv_constMean'):
        acc = {m: [] for m in members}
        for rep in range(n_rep):
            rng = np.random.default_rng(99 + rep + hash(scen) % 1000)
            par = rng.uniform(0.5, 2.0, n)                    # 截面变化的情景参数
            base = 0.02 * np.exp(0.3 * rng.standard_normal((D, n)))
            trig = np.zeros((D, n), bool)
            t = np.arange(D)[:, None]
            if scen == 'scale':
                x = base * par
            elif scen == 'trend':
                x = base * (1 + (par - 1.25) * (t - D / 2) / D)
            elif scen == 'pulse':
                x = base.copy()
                x[200] *= 1 + 4 * par
            elif scen == 'events':
                x = base.copy()
                for j in range(n):
                    k = int(par[j] * 3)
                    days = rng.choice(np.arange(60, 230), size=k, replace=False)
                    trig[days, j] = True
                    for dd in days:
                        x[dd:dd + 3, j] *= 3.0
            elif scen == 'level_constCV':
                # 时间上的水平跳变 (跳变后 CV 与跳变前相同): 评估日 20 日窗跨在跳变点上,
                # 检验 std / CV 类成员会不会把"水平跳变"读成"不稳定"
                x = base.copy()
                x[D - 10:] *= par[None, :]
            else:                                               # cv 变、均值不变
                s_ln = 0.3 * par
                x = 0.02 * np.exp(rng.standard_normal((D, n)) * s_ln[None, :] - 0.5 * s_ln ** 2)
            x = np.maximum(x, 1e-6)
            B = SimpleNamespace(x=x, trig=trig, open=np.ones_like(trig), _tau=None)
            B.tau = (lambda B=B: FE.Base.tau(B))
            for m in members:
                v = fns[m](B)[D - 1]
                ok = np.isfinite(v)
                if ok.sum() > 20:
                    acc[m].append(pd.Series(v[ok]).corr(pd.Series(par[ok]), method='spearman'))
        for m, v in acc.items():
            v = np.asarray(v)
            rows.append(dict(panel='activity', scenario=scen, member=m,
                             spearman_with_param=float(np.nanmean(v)) if len(v) else np.nan,
                             mcse=float(np.nanstd(v, ddof=1) / math.sqrt(max(len(v), 1)))
                             if len(v) > 1 else np.nan, n_rep=len(v)))
        print('  activity %s done' % scen, flush=True)
    I.atomic_write_csv(os.path.join(OUT, 'activity.csv'), pd.DataFrame(rows))


def stage1_stats(x, y):
    """Stage 1 读表工具的最小版本 (与 Stage 1 模块同式): 形成日 Spearman、5 分组均值、尾部差。"""
    m = np.isfinite(x) & np.isfinite(y)
    xs, ys = x[m], y[m]
    rho = pd.Series(xs).corr(pd.Series(ys), method='spearman')
    q = pd.qcut(pd.Series(xs).rank(method='first'), 5, labels=False)
    g = pd.Series(ys).groupby(q.values).mean().values
    return rho, g


def run_info(n=200, D=500, n_rep=200):
    rows = []
    for kind in ('zero', 'ushape', 'edge_only', 'missing_only'):
        rhos, groups = [], []
        for rep in range(n_rep):
            rng = np.random.default_rng(31337 + rep + 10000 * hash(kind) % 7)
            rr, gg = [], []
            for d in range(0, D, 25):
                x = rng.standard_normal(n)
                e = rng.standard_normal(n)
                if kind == 'zero':
                    y = e
                elif kind == 'ushape':
                    y = 0.3 * (x ** 2 - 1) + e
                elif kind == 'edge_only':
                    y = 0.6 * np.where(np.abs(x) > np.quantile(np.abs(x), 0.9), np.sign(x), 0) + e
                else:
                    y = e.copy()
                    x = np.where(rng.random(n) < 0.15, np.nan, x)
                rho, g = stage1_stats(x, y)
                rr.append(rho)
                gg.append(g)
            rhos.append(np.mean(rr))
            groups.append(np.mean(gg, axis=0))
        g = np.asarray(groups)
        rows.append(dict(panel='info', kind=kind, spearman_mean=float(np.mean(rhos)),
                         spearman_mcse=float(np.std(rhos, ddof=1) / math.sqrt(len(rhos))),
                         **{'g%d_mean' % (i + 1): float(g[:, i].mean()) for i in range(5)},
                         g_mcse=float(g.std(ddof=1, axis=0).mean() / math.sqrt(len(g))),
                         n_rep=n_rep))
        print('  info %s done' % kind, flush=True)
    I.atomic_write_csv(os.path.join(OUT, 'info.csv'), pd.DataFrame(rows))


def merge():
    fs = sorted(glob.glob(os.path.join(OUT, 'price_c*.csv')))
    d = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else pd.DataFrame()
    others = [pd.read_csv(p) for p in (os.path.join(OUT, x) for x in
                                       ('price_xs.csv', 'spread.csv', 'activity.csv', 'info.csv'))
              if os.path.exists(p)]
    allr = pd.concat([d] + others, ignore_index=True, sort=False)
    I.atomic_write_csv(os.path.join(I.RES, 'checks', 'simulation_results.csv'), allr)
    print('merge: price 行 %d (%d 格文件), 合计 %d 行' % (len(d), len(fs), len(allr)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--panel', default='price')
    ap.add_argument('--cells', default='')
    ap.add_argument('--paths', type=int, default=2000)
    ap.add_argument('--steps', type=int, default=390)
    ap.add_argument('--merge', action='store_true')
    a = ap.parse_args()
    FE.build_catalog()
    if a.merge:
        return merge()
    if a.panel == 'price':
        if '-' in a.cells:
            lo, hi = map(int, a.cells.split('-'))
            idx = list(range(lo, hi + 1))
        else:
            idx = [int(x) for x in a.cells.split(',') if x]
        run_price(idx, a.paths, a.steps)
    elif a.panel == 'price_xs':
        run_price_xs()
    elif a.panel == 'spread':
        run_spread()
    elif a.panel == 'activity':
        run_activity()
    elif a.panel == 'info':
        run_info()


if __name__ == '__main__':
    main()
