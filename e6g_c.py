#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 账户 / 成本 / 容量。

`e6f_c1.py` 与 `e6f_c2.py` 在模块层跑 argparse, import 即 SystemExit, 所以这里【复制函数体】
并重新对锚 (E6f 已存的 C_impact/bracket_*.npy 逐位), 不改 E6f 文件。
"""
import os, sys, json, collections
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6g_core as G
import comprehensive_factor_diagnosis as C

P0 = 0.01                      # 线性形式的参考参与率
YI = 1e8                       # A 以亿元计 -> 元


def align_to_close(S, key):
    """FundamentalTL 的六个字段 (limit_up/limit_down/flag_buy/flag_sell/flag_st/industry_zx1)
       【列集合与列序都与 close 不同】(2010-2014: close 2,612 列 vs 这些 5,450 列)。
       必须先 reindex 再按 ccols 取位置, 否则取到的是另一批股票。

       E6f 的 e6f_c1.py:52-57 与 e6f_c2.py:52-53 直接写 `.values[:, cc]`, 落进了这个坑
       —— 见 source_corrections_E6g.md §13。本轮一律走这个函数。"""
    f = S.data.get(key)
    if f is None:
        return None
    cl = S.data['close']
    if list(f.columns) != list(cl.columns) or list(f.index) != list(cl.index):
        f = f.reindex(index=cl.index, columns=cl.columns)
    return f.values[:, S.ccols]


class MarketCtx(object):
    """段上的市场量。执行日 e 的输入截止 e-1 (全部 .shift(1))。函数体复刻 e6f_c1 第 44-66 行,
       但把三个 FundamentalTL 标志改成【先对齐再取列】(见 align_to_close)。"""

    def __init__(self, S):
        cc = S.ccols
        amt = S.data['amount'].astype(float)
        isop = (S.data.get('is_open') == 1)
        amt_open = amt.where(isop)
        self.S = S
        self.ADV20 = amt_open.rolling(20, min_periods=10).mean().shift(1).values[:, cc]
        self.ADV20c = amt.rolling(20, min_periods=10).mean().shift(1).values[:, cc]
        self.ADV60 = amt_open.rolling(60, min_periods=30).mean().shift(1).values[:, cc]
        self.SIG20 = S.dr.rolling(20, min_periods=10).std().shift(1).values[:, cc]
        self.SIG60 = S.dr.rolling(60, min_periods=30).std().shift(1).values[:, cc]
        self.MCAP = S.data.get('mcap').astype(float).values[:, cc]
        self.AMT_E = amt.values[:, cc]
        self.OPEN_E = isop.values[:, cc]
        self.FLAGB = align_to_close(S, 'flag_buy')          # 必须对齐, 不能 .values[:, cc]
        self.FLAGS_ = align_to_close(S, 'flag_sell')
        self.FLAGST = align_to_close(S, 'flag_st')
        self.LIMUP = align_to_close(S, 'limit_up')
        self.LIMDN = align_to_close(S, 'limit_down')
        self.adv_pct = pd.DataFrame(self.ADV20).rank(axis=1, pct=True).values
        self.mc_pct = pd.DataFrame(self.MCAP).rank(axis=1, pct=True).values
        self.LOWADV = self.adv_pct < 0.20
        self.IC = S.icodes


def walk_holdings(S, idx, val, H=K.HOLD, tol=1e-15):
    """增量走 ah_t 与 q_t = ah_t − ah_{t−1}; 窗口与 sparse_pnl_H 逐字相同。"""
    T, Nc = S.T, S.Nc
    den = np.minimum(np.arange(1, T + 1), H).astype(float)
    cur = np.zeros(Nc)
    prev = np.zeros(Nc)
    for t in range(2, T):
        sa, sr = t - 2, t - 2 - H
        if len(idx[sa]):
            cur[idx[sa]] += val[sa]
        if sr >= 0 and len(idx[sr]):
            cur[idx[sr]] -= val[sr]
        ah = cur / den[t - 2]
        q = ah - prev
        hz = np.flatnonzero(np.abs(ah) > tol)
        qz = np.flatnonzero(np.abs(q) > tol)
        yield t, hz, ah[hz], qz, q[qz]
        prev = ah


def profile_and_impact(M, idx, val, H=K.HOLD, full_profile=True):
    """四个 bracket 与 (A, κ) 无关:
         sqrt: Σ|q|^1.5 σ20/√ADV20  -> c = κ√A · bracket   (主口径)
         cal : 同上但 ADV 含停牌 0                            (敏感性)
         s60 : Σ|q|^1.5 σ60/√ADV60                         (窗口敏感性)
         lin : Σ q²σ20/ADV20        -> c = (κA/√p0)·bracket, p0 = 1%
       返回 (brackets, profile, 逐日 Σ|q|, 逐日缺 ADV/σ 的 Σ|q|)。"""
    S = M.S
    T = S.T
    br = np.full(T, np.nan); brc = np.full(T, np.nan)
    br60 = np.full(T, np.nan); brl = np.full(T, np.nan)
    tw = np.zeros(T); qmiss = np.zeros(T)
    nh = np.zeros(T, int); live_w = np.zeros(T)
    acc = collections.defaultdict(list)
    for t, hz, w, qz, q in walk_holdings(S, idx, val, H):
        if len(qz):
            aq = np.abs(q)
            tw[t] = aq.sum()
            s_, a_, ac_ = M.SIG20[t, qz], M.ADV20[t, qz], M.ADV20c[t, qz]
            s6_, a6_ = M.SIG60[t, qz], M.ADV60[t, qz]
            ok = ~np.isnan(s_) & ~np.isnan(a_) & (a_ > 0)
            okc = ~np.isnan(s_) & ~np.isnan(ac_) & (ac_ > 0)
            ok6 = ~np.isnan(s6_) & ~np.isnan(a6_) & (a6_ > 0)
            qmiss[t] = float(aq[~ok].sum())
            if ok.any():
                br[t] = float(np.sum(aq[ok] ** 1.5 * s_[ok] / np.sqrt(a_[ok])))
                brl[t] = float(np.sum(aq[ok] ** 2 * s_[ok] / a_[ok]))
            if okc.any():
                brc[t] = float(np.sum(aq[okc] ** 1.5 * s_[okc] / np.sqrt(ac_[okc])))
            if ok6.any():
                br60[t] = float(np.sum(aq[ok6] ** 1.5 * s6_[ok6] / np.sqrt(a6_[ok6])))
            if full_profile:
                wq = aq / aq.sum()
                acc['tw_adv_pct'].append(float(np.nansum(wq * M.adv_pct[t, qz])))
                acc['tw_mc_pct'].append(float(np.nansum(wq * M.mc_pct[t, qz])))
                acc['tw_lowadv'].append(float(wq[M.LOWADV[t, qz]].sum()))
                if M.FLAGB is not None:
                    acc['tw_nobuy'].append(float(np.nansum(wq * (M.FLAGB[t, qz] == 0))))
                if M.FLAGS_ is not None:
                    acc['tw_nosell'].append(float(np.nansum(wq * (M.FLAGS_[t, qz] == 0))))
                if M.FLAGST is not None:
                    acc['tw_st'].append(float(np.nansum(wq * (M.FLAGST[t, qz] == 1))))
        nh[t] = len(hz)                      # live_n: 5 批叠加后实际持有的不同股票数
        live_w[t] = float(w.sum()) if len(hz) else 0.0
        if full_profile and len(hz):
            tot = w.sum()
            if tot > 0:
                p_ = w / tot
                acc['hhi'].append(float((p_ ** 2).sum()))
                acc['wmax'].append(float(w.max()))
                acc['invested'].append(float(tot))
                ic = M.IC[t, hz]
                v = ic >= 0
                if v.any():
                    gs = np.bincount(ic[v], weights=w[v], minlength=S.G)
                    acc['ind_max'].append(float(gs.max() / tot))
                    acc['ind_n'].append(int((gs > 0).sum()))
    brackets = dict(sqrt=br, cal=brc, s60=br60, lin=brl)
    prof = {k: float(np.mean(v)) for k, v in acc.items() if len(v)}
    prof['live_n_calendar'] = float(nh.mean())
    prof['live_n_active'] = float(nh[nh > 0].mean()) if (nh > 0).any() else np.nan
    prof['days_live_zero'] = int((nh == 0).sum())
    return brackets, prof, tw, qmiss, nh, live_w


FORMS = {'sqrt': lambda Ay, kp: kp * np.sqrt(Ay * YI),
         'cal': lambda Ay, kp: kp * np.sqrt(Ay * YI),
         's60': lambda Ay, kp: kp * np.sqrt(Ay * YI),
         'lin': lambda Ay, kp: kp * (Ay * YI) / np.sqrt(P0)}


def impact_cost(bracket, A_yi, kappa, form='sqrt'):
    """逐日实施冲击成本 (小数收益率单位)。A_yi 以【亿元】计。"""
    return FORMS[form](A_yi, kappa) * bracket


def anchor_against_e6f(M, pname, cfg_ids, idxvals, out=None):
    """与 E6f 已存的 C_impact/bracket_<段>.npy 逐位对锚。"""
    d = os.path.join(G.E6F_DIR, 'C_impact')
    fp = os.path.join(d, 'bracket_%s.npy' % pname)
    fc = os.path.join(d, 'bracket_cols_%s.json' % pname)
    if not (os.path.exists(fp) and os.path.exists(fc)):
        return dict(status='E6f bracket 文件缺失', path=fp)
    B = np.load(fp)
    cols = json.load(open(fc))
    pos = {c: i for i, c in enumerate(cols)}
    res = []
    for cid, (idx, val) in zip(cfg_ids, idxvals):
        if cid not in pos:
            res.append(dict(config_id=cid, status='不在 E6f bracket 列里'))
            continue
        br = profile_and_impact(M, idx, val, full_profile=False)[0]['sqrt']
        ref = B[:, pos[cid]]
        a, b = np.asarray(br, float), np.asarray(ref, float)
        both = np.isfinite(a) & np.isfinite(b)
        res.append(dict(config_id=cid, n=int(both.sum()),
                        max_abs_diff=(float(np.max(np.abs(a[both] - b[both])))
                                      if both.any() else None),
                        nan_mismatch=int((np.isfinite(a) != np.isfinite(b)).sum())))
    if out:
        json.dump(res, open(out, 'w'), indent=1, ensure_ascii=False)
    return res


# ============================================================
# 影子账户 (函数体移植自 e6f_c2, 两处改动:
#   1. flag_buy / flag_sell 走 align_to_close (E6f 的列错位, 见 source_corrections_E6g §13)
#   2. 全局量收进 ShadowCtx, 不再用模块级变量
# 账户约定 (仓位按日初敞口、费用按买卖合计收 0.5bp) 与 E6f 修正后一致, 不再改。
# ============================================================
class ShadowCtx(object):
    def __init__(self, S):
        cc = S.ccols
        self.S = S
        adjf = C.adjust_factor(S.data)
        PV = (S.data['vwap'].astype(float) * adjf).values[:, cc]
        self.PV = PV
        self.OPEN = (S.data.get('is_open') == 1).values[:, cc]
        self.VALID = self.OPEN & np.isfinite(PV) & (PV > 0)
        self.FB = align_to_close(S, 'flag_buy')
        self.FS = align_to_close(S, 'flag_sell')
        self.BENCH = S.bench
        self.PV_ff = pd.DataFrame(PV).ffill().values
        self.STALE = ~np.isfinite(PV)
        PE = np.empty_like(self.PV_ff)
        p0 = np.where(np.isfinite(self.PV_ff[0]) & (self.PV_ff[0] > 0), self.PV_ff[0], 1.0)
        PE[0] = p0
        for t in range(1, S.T):
            PE[t] = PE[t - 1] * (1.0 + S.r0[t])
        self.PV_eng = np.where(np.isfinite(PE) & (PE > 0), PE, 1.0)


def target_weights(S, idx, val, H=K.HOLD):
    """引擎口径的 ah_t -> 稠密逐日目标权重 (T, Nc)。"""
    T_, Nc = S.T, S.Nc
    den = np.minimum(np.arange(1, T_ + 1), H).astype(float)
    W = np.zeros((T_, Nc))
    cur = np.zeros(Nc)
    for t in range(2, T_):
        sa, sr = t - 2, t - 2 - H
        if len(idx[sa]):
            cur[idx[sa]] += val[sa]
        if sr >= 0 and len(idx[sr]):
            cur[idx[sr]] -= val[sr]
        W[t] = cur / den[t - 2]
    return W


def shadow_account(SC, W, mode='ideal', capital='constant_notional', A_notional=5 * YI,
                   bp=F.COST, unknown_tradable=True, convention='account', price_path=None):
    T_, Nc = W.shape
    PX = SC.PV_eng if (price_path or convention) == 'engine' else SC.PV_ff
    u = np.zeros(Nc)
    cash = float(A_notional)
    out = dict(nav=np.full(T_, np.nan), pos=np.zeros(T_), fee=np.zeros(T_),
               excess=np.full(T_, np.nan), cash=np.full(T_, np.nan),
               hold=np.full(T_, np.nan), recon=np.zeros(T_),
               unfilled_buy=np.zeros(T_), unfilled_sell=np.zeros(T_),
               trapped=np.zeros(T_), stale_val=np.zeros(T_), scaled_down=np.zeros(T_),
               bad_fill=np.zeros(T_), pos_mtm=np.zeros(T_))
    prev_nav = float(A_notional)
    for t in range(2, T_):
        e = t - 1
        Pe = PX[e]
        ok_price = np.isfinite(Pe) & (Pe > 0)
        nav_pre = cash + float(np.nansum(u * np.where(ok_price, Pe, 0.0)))
        base = A_notional if capital == 'constant_notional' else nav_pre
        tgt = np.zeros(Nc)
        np.divide(W[t] * base, Pe, out=tgt, where=ok_price)
        order = tgt - u
        if mode == 'ideal':
            can_b = np.ones(Nc, bool); can_s = np.ones(Nc, bool)
        else:
            can_b = SC.VALID[e].copy(); can_s = SC.VALID[e].copy()
            if mode == 'X1':
                if SC.FB is not None:
                    fb = SC.FB[e].astype(float)
                    can_b &= np.where(np.isnan(fb), unknown_tradable, fb == 1)
                if SC.FS is not None:
                    fs = SC.FS[e].astype(float)
                    can_s &= np.where(np.isnan(fs), unknown_tradable, fs == 1)
        buy = (order > 0) & can_b
        sell = (order < 0) & can_s
        out['unfilled_buy'][t] = float(np.sum(order[(order > 0) & ~can_b] *
                                              Pe[(order > 0) & ~can_b])) if ok_price.any() else 0.0
        bs_ = (order < 0) & ~can_s
        out['unfilled_sell'][t] = float(-np.sum(order[bs_] * Pe[bs_]))
        out['trapped'][t] = float(np.sum(u[bs_] * Pe[bs_]))
        sell_amt = float(-np.sum(order[sell] * Pe[sell]))
        avail = cash + sell_amt * (1.0 - 0.5 * bp / 1e4)
        buy_amt = float(np.sum(order[buy] * Pe[buy]))
        scale = 1.0
        if buy_amt > 0 and convention != 'engine':
            need = buy_amt * (1.0 + 0.5 * bp / 1e4)
            if need > avail:
                scale = max(0.0, avail / need)
                out['scaled_down'][t] = 1.0
        du = np.zeros(Nc)
        du[sell] = order[sell]
        du[buy] = order[buy] * scale
        out['bad_fill'][t] = float(np.sum(np.abs(du[(order > 0) & ~can_b]))
                                   + np.sum(np.abs(du[(order < 0) & ~can_s])))
        traded = float(np.sum(np.abs(du) * np.where(ok_price, Pe, 0.0)))
        fee = 0.5 * traded * (bp / 1e4)
        u = u + du
        cash = cash - float(np.sum(du * np.where(ok_price, Pe, 0.0))) - fee
        held_at_exec = float(np.nansum(u * np.where(ok_price, Pe, 0.0)))
        Pt = PX[t]
        ok_t = np.isfinite(Pt) & (Pt > 0)
        hold_val = float(np.nansum(u * np.where(ok_t, Pt, 0.0)))
        pnl = hold_val - held_at_exec
        pos_t = held_at_exec / base if base > 0 else 0.0      # 日初敞口, 不是盯市
        out['pos_mtm'][t] = hold_val / base if base > 0 else 0.0
        out['stale_val'][t] = (0 if convention == 'engine'
                               else float(np.sum(np.abs(u[SC.STALE[t]]) > 0)))
        nav = cash + hold_val
        out['nav'][t] = nav; out['cash'][t] = cash; out['hold'][t] = hold_val
        out['fee'][t] = fee; out['pos'][t] = pos_t
        out['recon'][t] = nav - (nav_pre + pnl - fee)
        r_port = (nav - prev_nav) / base if base > 0 else np.nan
        out['excess'][t] = r_port - (SC.BENCH[t] * pos_t if np.isfinite(SC.BENCH[t]) else np.nan)
        prev_nav = nav
    return out
