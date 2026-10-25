# -*- coding: utf-8 -*-
"""E6q 诊断块（plan §10；附录 B.23；brief §5 映射）：长格式 block, item, key1, key2, segment, stat, value, unit, n, status, query_id。
D1 成本来源（订单类别 × 参与率五分位〔切点 = 同触发 NATIVE 的净单参与率〕的 curve 冲击；臂 − 同触发 NATIVE、臂 − 同臂父）/ D2 资金目标（key1 ∈ EXTRA / REGULAR /
RANDOM_TARGET_WITHIN_ARM / RANDOM_TARGET_SOURCE_DOMAIN，key2 ∈ 六维；q5 / q20 前向超额，等证券 / 等批次 / 预算加权；重复率、new 合法数、预算短缺、队列过期）/
D3 入场信息 × 持久性（只两推导段；源域〔当日形成名单〕内三分位；K 强 = 源好度，K0 原值另列，CVR20 风险，size，行业作类别）/ D4 日龄与延期（landmark 汇总、存活组成、
至原 due；M3 延期）/ D5 剂量与对冲（参与率 ADV20 / 尾盘 30 分钟两分母 × 订单类别；M4 半量完成、残仓、重复信号、REARM；卖半 × 再投半四账户交互）/ D6 价值 / 成本密度 /
D7 层组成（同数 vs 同额 ISK；LOSO 触发密度；并集交集与两边独有）/ D8 执行窗 / D9 完整风险 / D10 跨轮外部性；landmark_E6q.csv。
只读账户 / 成交分片 / 意向 / 面板（截至授权终点）；前向窗口超出终点 → RIGHT_CENSORED（不取 E7）；按未来事件分组一律拒绝（e6q_landmark.group_by_outcome）。
  python3 e6q_diag.py --phase B [--workers 96]        （--phase A2 --root tmp/a2stats：只用推导段的空跑检查）"""
import os
import sys
import json
import time
import argparse
from multiprocessing import get_context

import numpy as np
import pandas as pd

import e6q_core as O
import e6q_engine as E
import e6q_landmark as LM
import e6q_stats as ST
import e6q_cost as CO
import e6q_acct as A

SEG4 = list(O.SEGS)
DSEGS = list(O.DERIV_SEGS)
LCOLS = ['block', 'item', 'key1', 'key2', 'segment', 'stat', 'value', 'unit', 'n', 'status', 'query_id']
LMCOLS = ['exec_id', 'landmark_age', 'state', 'q', 'weighting', 'n', 'mean_fwd_excess_bp', 'lo', 'hi', 'status']
QB = ('Q1', 'Q2', 'Q3', 'Q4', 'Q5')
D2_DIMS = ('entry_score_tertile', 'size_tertile', 'amihud_tertile', 'loso_density_tertile', 'edge_spread_tertile', 'new_vs_old')
EXITK = ('EXIT', 'EXIT_HALF', 'EXIT_REARM', 'DEADLINE_OVERRIDE')
E6I_DIR = '20260923_0254_E6i_measurement_need_fit'
A_D1 = (1e8, 5e8)
G = {}


def L(rows, block, item, key1, key2, segment, stat, value, unit, n='', status='COMPUTED', q=''):
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        value, status = '', ('UNKNOWN' if status == 'COMPUTED' else status)
    rows.append(dict(block=block, item=item, key1=key1, key2=key2, segment=segment, stat=stat, value=value, unit=unit, n=n, status=status, query_id=q or 'QRY-%s' % block))


def tag(r):
    return '%s|%s|H%s|%s|%s' % (r.arm, r.trigger, r.H, 'main' if r.form == O.MAIN_FORM else r.form, r.memory)


def load_trades(h):
    ctx = G['ctx']
    a = np.load(O.P('trades_parts', 'deriv', h[:2], '%s.npz' % h), allow_pickle=False)
    if ctx.phase == 'A2':
        return a['TL_i'], a['TL_f']
    b = np.load(O.P('trades_parts', 'full', h[:2], '%s.npz' % h), allow_pickle=False)
    return np.concatenate([a['TL_i'], b['TL_i']]), np.concatenate([a['TL_f'], b['TL_f']])


def trig_panel(name):
    p = A.TRIG_PANEL.get(name if name != 'NONE' else 'T1a')
    return G['mk'].trig(p)


def setup(ctx):
    cd = ctx.cd
    P = lambda k: np.load(os.path.join(cd, 'panels', k + '.npy'), mmap_mode='r')
    M = lambda k: np.load(os.path.join(cd, 'minute', k + '.npy'), mmap_mode='r')
    mk = A.Market()
    G.update(ctx=ctx, mk=mk, pv=P('pv_ff'), pc=P('pc_ff'), adv20=P('adv20'), sig20=P('sig20'), zsize=P('zsize'), amihud=P('amihud20'), edge=P('edge21'),
             iskid=P('iskid'), ind=P('ind'), vwap_raw=P('vwap_raw'), open_raw=P('open_raw'), amt=P('amt'), close_adj=P('close_adj'), tail_amt=M('tail_amt'),
             tail_vol=M('tail_vol'))
    G['cumbench'] = np.cumprod(1.0 + np.nan_to_num(ctx.bench))
    G['f'] = {(f, m): mk.formation(f, m) for f in O.FORMS for m in O.MEMS if (f == O.MAIN_FORM or m == 'HG10')}
    G['last'] = ctx.d_end - 1
    G['N'] = len(ctx.codes)
    # 取向后的 K 腿好度 = −K0（E6i K0_LEGACY = 条件换手，高 = 坏），四段全读（测量面板，非收益；E6i 各段形状与本轮源段一致、止于 2026-03-27）
    K0, sh = e6i_panel('K0_LEGACY', segs=list(O.SEGS))
    G['negK0'] = -K0
    G['k0_sha_all'] = sh


def k_pct(form, mem, fday, sec):
    """形成日 fday 的源域（当日形成名单）内 −K0 的分位（0–1；平局取中点）：D2 入场好度、D4 存活组成与 D3 的 K 强都用它
    （形成权重在 A4b 下几乎全是 1% 上限，不分级，不能当好度分数）。名单外名字按其 −K0 在当日源域分布里的位置给分位。"""
    ptr, col, w = G['f'][(form, mem)]
    X = G['negK0']
    fday = np.asarray(fday, np.int64)
    sec = np.asarray(sec, np.int64)
    out = np.full(len(fday), np.nan)
    for d, idx in by_day(fday):
        if d < 0:
            continue
        v = np.asarray(X[d, col[ptr[d]:ptr[d + 1]]], float)
        v = np.sort(v[np.isfinite(v)])
        if len(v) < 3:
            continue
        x = np.asarray(X[d, sec[idx]], float)
        lo = np.searchsorted(v, x, 'left')
        hi = np.searchsorted(v, x, 'right')
        out[idx] = np.where(np.isfinite(x), (lo + 0.5 * (hi - lo)) / len(v), np.nan)
    return out


# ------------------------------------------------------------------ 公共测量
def fwd(sec, d0, q, last=None):
    """前向超额：VWAP(d0) → VWAP(d0 + q)（后复权）减同窗口 clean 等权基准；终点超出 last（默认授权终点 / 推导段终点）→ NaN + 右删失标记。"""
    last = G['last'] if last is None else last
    pv, cb = G['pv'], G['cumbench']
    d0 = np.asarray(d0, np.int64)
    d1 = d0 + q
    cens = d1 > last
    a = np.minimum(d0, last)
    b = np.minimum(d1, last)
    with np.errstate(all='ignore'):
        x = (np.asarray(pv[b, sec], float) / np.asarray(pv[a, sec], float) - 1.0) - (cb[b] / cb[a] - 1.0)
    return np.where(cens, np.nan, x), cens


def entry_weight(form, mem, fday, sec):
    """形成日 fday 的源权重（取向后的源好度；名单外 → NaN）。"""
    ptr, col, w = G['f'][(form, mem)]
    out = np.full(len(fday), np.nan)
    for i, (f, s) in enumerate(zip(np.asarray(fday, np.int64), np.asarray(sec, np.int64))):
        if f < 0:
            continue
        a, b = ptr[f], ptr[f + 1]
        k = a + np.searchsorted(col[a:b], s)
        if k < b and col[k] == s:
            out[i] = w[k]
    return out


def by_day(day):
    o = np.argsort(day, kind='stable')
    ds = day[o]
    cut = np.flatnonzero(np.r_[True, ds[1:] != ds[:-1], True])
    return [(int(ds[a]), o[a:b]) for a, b in zip(cut[:-1], cut[1:])]


def loso_density(trig, day, sec):
    """LOSO 层密度：日 T 同 iskid 层内、除本股外处于坏状态（触发面板 = 1）的份额（本股触发不机械计入）；NONE 账户用 T1a 面板。"""
    P = trig_panel(trig)
    iskid = G['iskid']
    day = np.asarray(day, np.int64)
    sec = np.asarray(sec, np.int64)
    out = np.full(len(day), np.nan)
    for d, idx in by_day(day):
        k = np.asarray(iskid[d], float)
        ok = np.isfinite(k) & (k >= 0)
        ki = np.where(ok, k, -1).astype(np.int64)
        bad = (np.asarray(P[d]) == 1) & ok
        m = int(ki.max()) + 1 if ok.any() else 1
        nk = np.bincount(ki[ok], minlength=m)
        bk = np.bincount(ki[ok], weights=bad[ok].astype(float), minlength=m)
        s = sec[idx]
        ks = ki[s]
        v = ks >= 0
        n = nk[ks[v]]
        b = bk[ks[v]] - bad[s[v]]
        with np.errstate(all='ignore'):
            out[idx[v]] = np.where(n > 1, b / (n - 1), np.nan)
    return out


def cuts3(x):
    x = np.asarray(x, float)
    ok = np.isfinite(x)
    if ok.sum() < 30:
        return None
    return tuple(np.percentile(x[ok], [100 / 3.0, 200 / 3.0]))


def lab3(x, c):
    x = np.asarray(x, float)
    out = np.full(len(x), '', dtype=object)
    if c is None:
        return out
    ok = np.isfinite(x)
    out[ok] = np.where(x[ok] <= c[0], 'T1', np.where(x[ok] <= c[1], 'T2', 'T3'))
    return out


def held_before(ti, tf):
    """成交行所在日之前（不含当日）该证券是否已有库存：区分 new / old 名字（重复率）。"""
    if not len(ti):
        return np.zeros(0, bool)
    df = pd.DataFrame(dict(d=ti[:, 0], s=ti[:, 1], q=np.where(ti[:, 5] == 0, tf[:, 0], -tf[:, 0])))
    g = df.groupby(['s', 'd']).q.sum().reset_index().sort_values(['s', 'd'])
    g['inv_before'] = g.groupby('s').q.cumsum() - g.q
    key = dict(zip(zip(g.s.to_numpy(), g.d.to_numpy()), g.inv_before.to_numpy()))
    return np.array([key[(s, d)] > 1e-9 for s, d in zip(ti[:, 1], ti[:, 0])])


def day_se(x, d):
    """交易日聚类：日内均值 → 跨日标准误。"""
    if len(x) < 2:
        return np.nan
    g = pd.DataFrame(dict(d=d, x=x)).groupby('d').x.mean().to_numpy()
    return float(np.std(g, ddof=1) / np.sqrt(len(g))) if len(g) > 1 else np.nan


# ------------------------------------------------------------------ D1：净单 curve 冲击 → 成交行
def net_orders(ti, tf, DY):
    """证券日净单（与 S0-A / 引擎 cost_s05 同节点）：dn = |B − S|，V⁺_{e−1} = 前日 nav_post（首日 V0），σ / ADV 取执行日面板；返回逐成交行的净单索引与在净方向一侧的名义份额。"""
    N = G['N']
    key = ti[:, 0].astype(np.int64) * N + ti[:, 1].astype(np.int64)
    uk, inv = np.unique(key, return_inverse=True)
    buy = ti[:, 5] == 0
    B = np.bincount(inv, weights=np.where(buy, tf[:, 1], 0.0), minlength=len(uk))
    S = np.bincount(inv, weights=np.where(~buy, tf[:, 1], 0.0), minlength=len(uk))
    dd, ss = uk // N, uk % N
    dn = np.abs(B - S)
    vprev = np.where(dd >= 1, DY[np.maximum(dd - 1, 0), E.DYI['nav_post']], O.V0)
    sig = np.asarray(G['sig20'][dd, ss], float)
    adv = np.asarray(G['adv20'][dd, ss], float)
    onside = np.where((B > S)[inv], buy, ~buy) & (dn[inv] > 0)
    w = np.where(onside, tf[:, 1], 0.0)
    tot = np.bincount(inv, weights=w, minlength=len(uk))
    with np.errstate(all='ignore'):
        share = np.where(onside & (tot[inv] > 0), w / tot[inv], 0.0)
        p1 = 1e8 * dn / (O.V0 * adv)
    return dict(inv=inv, share=share, dn=dn, vprev=vprev, sig=sig, adv=adv, p1=p1, dd=dd)


def qcuts(no):
    p = no['p1'][(no['dn'] > 0) & np.isfinite(no['p1'])]
    return tuple(np.percentile(p, [20, 40, 60, 80])) if len(p) >= 50 else None


def qlab(p, c):
    out = np.full(len(p), '', dtype=object)
    if c is None:
        return out
    ok = np.isfinite(p)
    out[ok] = np.array(QB, dtype=object)[np.searchsorted(np.asarray(c), p[ok], side='left')]
    return out


def d1_account(ti, tf, DY, kinds, cuts, T):
    """逐 (订单类别, 参与率五分位, A) 与逐 (买卖方向, A) 的 curve 冲击 ann_pp（κ .5、δ .5；全部交易日为分母）；缺 σ / ADV 的非零净单计数另列。"""
    no = net_orders(ti, tf, DY)
    q_of_order = qlab(no['p1'], cuts)
    out, side, miss = {}, {}, {}
    for A_ in A_D1:
        c = CO.curve_share_vec(no['dn'], no['vprev'], no['sig'], no['adv'], A_, O.V0, kappa=0.5, delta=0.5)
        cm = ~np.isfinite(c) & (no['dn'] > 0)
        miss[A_] = int(cm.sum())
        row_imp = np.where(np.isfinite(c), c, 0.0)[no['inv']] * no['share']
        qb = q_of_order[no['inv']]
        df = pd.DataFrame(dict(k=kinds, q=qb, v=row_imp, side=np.where(ti[:, 5] == 0, 'BUY', 'SELL'), on=no['share'] > 0))
        for (k, q), g in df[df.on & (df.q != '')].groupby(['k', 'q']):
            out[(k, q, A_)] = (float(g.v.sum() / T * O.ANN_PP), int(len(g)))
        for sd, g in df[df.on].groupby('side'):
            side[(sd, A_)] = (float(g.v.sum() / T * O.ANN_PP), int(len(g)))
    return out, side, miss


M3COLS = ['exec_id', 'request_id', 'security', 'intent_date', 'first_fill_date', 'last_fill_date', 'n_slices', 'target_value_V0', 'filled_value_V0', 'completed_share',
          'forced_deadline', 'participation_A1e8', 'deferred_value_V0', 'deferral_pnl_V0', 'unreleased_cash_opp_V0', 'cost_daily_independent_A1e8_V0',
          'cost_linked_meta_A1e8_V0', 'status']


def m3_meta(r, ti, tf, IN, INf, DY, rows, tg, e, T):
    """plan §9.3：M3 门控的元订单（同请求 = parent order 的分日切片）。逐请求：总目标（意向时整批价值）、已成交、完成份额、强制截止、参与率（A = 1 亿，切片名义 / 当日成交额）、
    推迟部分（首个可执行日 e = 意向日 + 1 之后的切片）与延期损益（e → 实际卖出日超额）、未释放现金机会（同名义 × 形成名单篮子同窗口超额）；
    成本敏感性："日独立"= 每个切片按当日 σ / ADV / V⁺ 单独计 curve 冲击，"关联元订单不重置"= 用首个切片日已知 σ / ADV 对全 episode 成交名义计同式（按完成份额分配，合计不变）。
    只是模型边界读法，不进 c5。D4 行写账户汇总，返回逐请求行（主形态 HG10 FEASIBLE 账户才写表）。"""
    ctx = G['ctx']
    m = IN[:, E.IN_KIND] == E.KD_TRIG
    rid = np.flatnonzero(m)
    sl = (ti[:, 5] == 1) & (ti[:, 3] >= 0)
    F = pd.DataFrame(dict(rq=ti[sl, 3].astype(np.int64), day=ti[sl, 0].astype(np.int64), s=ti[sl, 1].astype(np.int64), v=tf[sl, 1], q=tf[sl, 0], k=ti[sl, 4]))
    F = F[F.rq.isin(rid)]
    if not len(F):
        return []
    req = pd.DataFrame(dict(rq=rid, d=IN[m, E.IN_DAY].astype(np.int64), s=IN[m, E.IN_SEC].astype(np.int64), target=INf[m, 0], tq=INf[m, 1]))
    F = F.merge(req[['rq', 'd']], on='rq', how='inner')
    nav = DY[:, E.DYI['nav_post']]
    vpv = lambda dd: np.where(dd >= 1, nav[np.maximum(dd - 1, 0)], O.V0)
    sig = np.asarray(G['sig20'][F.day.to_numpy(), F.s.to_numpy()], float)
    adv = np.asarray(G['adv20'][F.day.to_numpy(), F.s.to_numpy()], float)
    amt = np.asarray(G['amt'][F.day.to_numpy(), F.s.to_numpy()], float)
    F['c_ind'] = np.nan_to_num(CO.curve_share_vec(F.v.to_numpy(), vpv(F.day.to_numpy()), sig, adv, 1e8, O.V0, kappa=0.5, delta=0.5)) * vpv(F.day.to_numpy())
    F['amt'] = amt
    pv, cb = G['pv'], G['cumbench']
    ptr, col, w = G['f'][(r.form, r.memory)]
    out = []
    tot_ind, tot_meta = {}, {}
    for A_ in A_D1:
        tot_ind[A_] = 0.0
        tot_meta[A_] = 0.0
    rq_d = dict(zip(req.rq.to_numpy(), req.d.to_numpy()))
    rq_s = dict(zip(req.rq.to_numpy(), req.s.to_numpy()))
    rq_t = dict(zip(req.rq.to_numpy(), req.target.to_numpy()))
    rq_q = dict(zip(req.rq.to_numpy(), req.tq.to_numpy()))
    for rq, g in F.groupby('rq'):
        d0, s0, tgt, tq = int(rq_d[rq]), int(rq_s[rq]), float(rq_t[rq]), float(rq_q[rq])
        ee = d0 + 1
        g = g.sort_values('day')
        f0 = int(g.day.iloc[0])
        Q = float(g.v.sum())
        gd, gs = g.day.to_numpy(), g.s.to_numpy()
        meta1 = np.nan
        for A_ in A_D1:
            ci = CO.curve_share_vec(g.v.to_numpy(), vpv(gd), np.asarray(G['sig20'][gd, gs], float), np.asarray(G['adv20'][gd, gs], float), A_, O.V0, kappa=0.5, delta=0.5)
            cm = CO.curve_share_vec(np.array([Q]), vpv(np.array([f0])), np.array([float(G['sig20'][f0, s0])]), np.array([float(G['adv20'][f0, s0])]), A_, O.V0,
                                    kappa=0.5, delta=0.5)
            tot_ind[A_] += float(np.nansum(ci * vpv(gd)))
            mv = float(np.nansum(cm * vpv(np.array([f0]))))
            tot_meta[A_] += mv
            if A_ == 1e8:
                meta1 = mv
        later = g[g.day > ee]
        dp, op = 0.0, 0.0
        if len(later) and ee <= G['last']:
            dd, ss, vv = later.day.to_numpy(), later.s.to_numpy(), later.v.to_numpy()
            with np.errstate(all='ignore'):
                xx = (np.asarray(pv[dd, ss], float) / np.asarray(pv[np.full(len(dd), ee), ss], float) - 1.0) - (cb[dd] / cb[ee] - 1.0)
            dp = float(np.nansum(xx * vv))
            a_, b_ = ptr[d0], ptr[d0 + 1]
            cs, ws = col[a_:b_].astype(np.int64), w[a_:b_]
            mk = ws > 0
            cs, ws = cs[mk], ws[mk]
            if len(cs):
                p0 = np.asarray(pv[ee, cs], float)
                for day_, v_ in zip(dd, vv):
                    with np.errstate(all='ignore'):
                        xb = np.asarray(pv[day_, cs], float) / p0 - 1.0
                    okb = np.isfinite(xb)
                    if okb.any():
                        op += float(v_ * ((xb[okb] * ws[okb]).sum() / ws[okb].sum() - (cb[day_] / cb[ee] - 1.0)))
        sa = float(g.amt.sum())
        out.append(dict(exec_id=e, request_id=int(rq), security=str(ctx.codes[s0]), intent_date=str(ctx.dates[d0]), first_fill_date=str(ctx.dates[f0]),
                        last_fill_date=str(ctx.dates[int(g.day.iloc[-1])]), n_slices=int(g.day.nunique()), target_value_V0=tgt / O.V0, filled_value_V0=Q / O.V0,
                        completed_share=float(g.q.sum()) / tq if tq > 0 else np.nan, forced_deadline=int((g.k == E.OK_DEADLINE).any()),
                        participation_A1e8=(Q * 1e8 / O.V0) / sa if sa > 0 else np.nan, deferred_value_V0=float(later.v.sum()) / O.V0, deferral_pnl_V0=dp / O.V0,
                        unreleased_cash_opp_V0=op / O.V0, cost_daily_independent_A1e8_V0=float(g.c_ind.sum()) / O.V0, cost_linked_meta_A1e8_V0=meta1 / O.V0,
                        status='COMPUTED'))
    Dq = pd.DataFrame(out)
    for A_ in A_D1:
        L(rows, 'D4', 'm3_meta_order_cost', tg, 'A%.0e' % A_, 'FULL', 'daily_independent_ann_pp', tot_ind[A_] / O.V0 / T * O.ANN_PP, 'ann_pp', len(Dq), status='MODEL_BOUNDARY',
          q='QRY-D4-M3META')
        L(rows, 'D4', 'm3_meta_order_cost', tg, 'A%.0e' % A_, 'FULL', 'linked_meta_no_reset_ann_pp', tot_meta[A_] / O.V0 / T * O.ANN_PP, 'ann_pp', len(Dq),
          status='MODEL_BOUNDARY', q='QRY-D4-M3META')
    if len(Dq):
        for st_, v, u in (('mean_completed_share', float(Dq.completed_share.mean()), 'share'), ('share_multi_slice', float((Dq.n_slices > 1).mean()), 'share'),
                          ('deferral_pnl_ann_pp', float(Dq.deferral_pnl_V0.sum()) / T * O.ANN_PP, 'ann_pp'),
                          ('unreleased_cash_opp_ann_pp', float(Dq.unreleased_cash_opp_V0.sum()) / T * O.ANN_PP, 'ann_pp'),
                          ('median_participation_A1e8', float(Dq.participation_A1e8.median()), 'ratio')):
            L(rows, 'D4', 'm3_parent_orders', tg, e, 'FULL', st_, v, u, len(Dq), q='QRY-D4-M3META')
    keep = r.scenario == 'FEASIBLE_DAILY' and r.form == O.MAIN_FORM and r.memory == 'HG10'
    return Dq.to_dict('records') if (keep and len(Dq)) else []


FA_ORIG = ('REGULAR', 'DUE')
FA_SELL = ('EXIT', 'EXIT_HALF', 'EXIT_REARM', 'DEADLINE_OVERRIDE')


def fee_algebra(ti, tf, DY, kinds, T):
    """plan §7.2 第 3 层"费用代数"：以已成交的证券日订单为固定状态，C00 = 原订单（REGULAR / DUE）净单冲击；C10 = 原订单 + 额外卖单（EXIT 类）；
    C01 = 原订单 + 额外再买（EXTRA）；C11 = 三者合并（= 实际净单）。交互 = C11 − C10 − C01 + C00；分摊约定 = 对称平均两条边际（不作经济因果）。
    curve κ .5 δ .5、同节点 V⁺_{e−1}；ann_pp（全部交易日为分母）。"""
    N = G['N']
    key = ti[:, 0].astype(np.int64) * N + ti[:, 1].astype(np.int64)
    uk, inv = np.unique(key, return_inverse=True)
    sgn = np.where(ti[:, 5] == 0, 1.0, -1.0) * tf[:, 1]
    cls = {'o': np.isin(kinds, FA_ORIG), 's': np.isin(kinds, FA_SELL) & (ti[:, 5] == 1), 'b': (kinds == 'EXTRA') & (ti[:, 5] == 0)}
    part = {c: np.bincount(inv, weights=np.where(m, sgn, 0.0), minlength=len(uk)) for c, m in cls.items()}
    dd, ss = uk // N, uk % N
    vprev = np.where(dd >= 1, DY[np.maximum(dd - 1, 0), E.DYI['nav_post']], O.V0)
    sig = np.asarray(G['sig20'][dd, ss], float)
    adv = np.asarray(G['adv20'][dd, ss], float)
    out = {}
    for A_ in A_D1:
        C = {}
        for nm, comb in (('C00', ('o',)), ('C10', ('o', 's')), ('C01', ('o', 'b')), ('C11', ('o', 's', 'b'))):
            net = sum(part[c] for c in comb)
            v = CO.curve_share_vec(np.abs(net), vprev, sig, adv, A_, O.V0, kappa=0.5, delta=0.5)
            C[nm] = float(np.nansum(v) / T * O.ANN_PP)
        C['interaction'] = C['C11'] - C['C10'] - C['C01'] + C['C00']
        C['sym_extra_sell'] = 0.5 * ((C['C10'] - C['C00']) + (C['C11'] - C['C01']))
        C['sym_extra_buy'] = 0.5 * ((C['C01'] - C['C00']) + (C['C11'] - C['C10']))
        out[A_] = C
    n = {c: int(m.sum()) for c, m in cls.items()}
    return out, n


# ------------------------------------------------------------------ D2：资金目标
def d2_feats(form, mem, trig, d, s):
    t = np.maximum(np.asarray(d, np.int64) - 1, 0)
    s = np.asarray(s, np.int64)
    return {'entry_score_tertile': k_pct(form, mem, t, s), 'size_tertile': np.asarray(G['zsize'][t, s], float),
            'amihud_tertile': np.asarray(G['amihud'][t, s], float), 'loso_density_tertile': loso_density(trig, t, s),
            'edge_spread_tertile': np.asarray(G['edge'][t, s], float)}


def d2_owner_cuts(r, ti, tf, kinds):
    """六维三分位切点：owner 自己全部 REGULAR + EXTRA 买入行合并（同一 owner 下各组 T1/T2/T3 含义相同；平局不按 ID 拆）。"""
    m = np.isin(kinds, ['REGULAR', 'EXTRA']) & (ti[:, 5] == 0)
    f = d2_feats(r.form, r.memory, r.trigger, ti[m, 0], ti[m, 1])
    return {k: cuts3(v) for k, v in f.items()}


def d2_emit(rows, group, tg, feats, cuts, isnew, d, notional, s):
    for q in (5, 20):
        x, cens = fwd(s, d, q)
        ok = np.isfinite(x)
        labs = {k: lab3(feats[k], cuts.get(k)) for k in feats}
        labs['new_vs_old'] = np.where(isnew, 'NEW', 'OLD').astype(object)
        for dim in D2_DIMS:
            lab = labs[dim]
            for t in (('NEW', 'OLD') if dim == 'new_vs_old' else ('T1', 'T2', 'T3')):
                m = ok & (lab == t)
                if not m.any():
                    continue
                xm, wm, dm = x[m], notional[m], d[m]
                bm = pd.DataFrame(dict(d=dm, x=xm)).groupby('d').x.mean().mean()
                L(rows, 'D2', 'fwd_excess_q%d' % q, group, dim, 'FULL', '%s|%s|equal_security_bp' % (tg, t), float(xm.mean() * 1e4), 'bp', int(m.sum()), q='QRY-D2-FWD')
                L(rows, 'D2', 'fwd_excess_q%d' % q, group, dim, 'FULL', '%s|%s|equal_batch_bp' % (tg, t), float(bm * 1e4), 'bp', int(len(np.unique(dm))), q='QRY-D2-FWD')
                L(rows, 'D2', 'fwd_excess_q%d' % q, group, dim, 'FULL', '%s|%s|budget_weighted_bp' % (tg, t),
                  float((xm * wm).sum() / wm.sum() * 1e4) if wm.sum() > 0 else np.nan, 'bp', int(m.sum()), q='QRY-D2-FWD')
        if ok.any():
            L(rows, 'D2', 'fwd_excess_q%d_pooled' % q, group, tg, 'FULL', 'equal_security_bp', float(x[ok].mean() * 1e4), 'bp', int(ok.sum()), q='QRY-D2-FWD')
            L(rows, 'D2', 'fwd_excess_q%d_pooled' % q, group, tg, 'FULL', 'budget_weighted_bp', float((x[ok] * notional[ok]).sum() / notional[ok].sum() * 1e4)
              if notional[ok].sum() > 0 else np.nan, 'bp', int(ok.sum()), q='QRY-D2-FWD')
        L(rows, 'D2', 'right_censored_q%d' % q, group, tg, 'FULL', 'count', float(cens.sum()), 'count', int(len(x)),
          status='RIGHT_CENSORED' if cens.any() else 'COMPUTED', q='QRY-D2-FWD')


def d2_supply(rows, tg, e, DY, ti, kinds, hb):
    """重复率（全账户买入 vs EXTRA 分开）、new 合法数、名单空日、预算短缺、队列过期（TTL 隔离）。"""
    b = ti[:, 5] == 0
    for nm, m in (('ALL_BUYS', b), ('EXTRA', b & (kinds == 'EXTRA')), ('REGULAR', b & (kinds == 'REGULAR'))):
        if m.any():
            L(rows, 'D2', 'repeat_rate', nm, tg, 'FULL', 'share_already_held', float(hb[m].mean()), 'share', int(m.sum()), q='QRY-D2-SUPPLY')
    xp = DY[:, E.DYI['extra_plan']] > 0
    I = E.DYI
    for nm, v, u in (('new_legal_n_mean_on_plan_days', float(DY[xp, I['new_n']].mean()) if xp.any() else np.nan, 'count'),
                     ('list_n_mean_on_plan_days', float(DY[xp, I['list_n']].mean()) if xp.any() else np.nan, 'count'),
                     ('new_empty_days', float((DY[:, I['new_empty']] > 0).sum()), 'days'),
                     ('route_need_elig_sum', float(np.nansum(DY[:, I['route_need_elig']])), 'value_V0'),
                     ('budget_shortfall_rt_short_sum', float(np.nansum(DY[:, I['rt_short']])), 'value_V0'),
                     ('queue_expired_quarantined_amt', float(np.nansum(DY[:, I['tk_quar']])), 'value_V0'),
                     ('queue_expired_quarantined_n', float(np.nansum(DY[:, I['n_tk_quar']])), 'count'),
                     ('tag_new_amt', float(np.nansum(DY[:, I['tag_new']])), 'value_V0'),
                     ('deny_amt', float(np.nansum(DY[:, I['deny_amt']])), 'value_V0'), ('deny_n', float(np.nansum(DY[:, I['deny_n']])), 'count'),
                     ('plan_days', float(xp.sum()), 'days')):
        L(rows, 'D2', 'supply', nm, tg, 'FULL', 'value', v, u, q='QRY-D2-SUPPLY')


# ------------------------------------------------------------------ landmark（D4）
def lots_frame(ti, tf):
    b = ti[:, 5] == 0
    lots = pd.DataFrame(dict(lot=ti[b, 2], sec=ti[b, 1], e0=ti[b, 0], qty=tf[b, 0], due=ti[b, 6])).groupby('lot', as_index=False).agg(
        sec=('sec', 'first'), e0=('e0', 'min'), qty=('qty', 'sum'), due=('due', 'max'))
    s = ti[:, 5] == 1
    sells = pd.DataFrame(dict(lot=ti[s, 2], day=ti[s, 0], kind=ti[s, 4], qty=tf[s, 0]))
    last = sells.groupby('lot').agg(close_day=('day', 'max'), sold=('qty', 'sum'))
    lots = lots.merge(last, left_on='lot', right_index=True, how='left')
    closed = lots.sold.fillna(0).to_numpy() >= lots.qty.to_numpy() * (1 - 1e-9)
    lots['cl'] = np.where(closed, lots.close_day.fillna(-1), -1).astype(np.int64)
    return lots, sells


def states_vec(T, iv, known, hs, hd, fo):
    """e6q_landmark.state_at 的向量版（QUARANTINED_CASH 不适用于批次）；main 内对样本逐行与 state_at 对照。"""
    st = np.full(len(T), 'NOT_TRIGGERED', dtype=object)
    k = known
    st[k & (iv == T)] = 'BAD_STATE'
    st[k & (iv < T)] = 'REQUEST_PENDING'
    st[k & (hs == 1) & ~hd] = 'HALF_PENDING'
    st[k & (hs == 1) & hd] = 'HALF_DONE_RESIDUAL'
    st[k & (hs == 2)] = 'REARMED'
    st[k & fo] = 'DEADLINE_OVERRIDDEN'
    return st


def landmark_rows(e, r, ti, tf, IN, rows):
    ctx = G['ctx']
    H = int(r.H)
    lots, sells = lots_frame(ti, tf)
    half_done = sells[sells.kind == E.OK_EXIT_HALF].groupby('lot').day.max()
    forced = sells[sells.kind == E.OK_DEADLINE].groupby('lot').day.min()
    first_int, rearm_day = {}, {}
    for lid, d, k in zip(IN[:, E.IN_LID].tolist(), IN[:, E.IN_DAY].tolist(), IN[:, E.IN_KIND].tolist()):
        if k == E.KD_TRIG and lid not in first_int:
            first_int[lid] = d
        if k == E.KD_REARM and lid not in rearm_day:
            rearm_day[lid] = d
    lid = lots.lot.to_numpy()
    e0, sec, qty, cl, due = lots.e0.to_numpy(), lots.sec.to_numpy(), lots.qty.to_numpy(), lots.cl.to_numpy(), lots.due.to_numpy()
    idd = np.array([first_int.get(int(l), -1) for l in lid], np.int64)
    hdd = np.array([int(half_done.get(int(l), -1)) for l in lid], np.int64)
    fdd = np.array([int(forced.get(int(l), -1)) for l in lid], np.int64)
    rdd = np.array([rearm_day.get(int(l), -1) for l in lid], np.int64)
    ew = k_pct(r.form, r.memory, e0 - 1, sec)
    half_arm = r.arm.startswith('EXIT_HALF')
    acc = {}
    chk = []
    tg = tag(r)
    for a in LM.LANDMARK_AGES:
        if a >= H:
            continue
        T = e0 + a - 1
        v = (T < G['last']) & ((cl < 0) | (cl > T))
        if not v.any():
            continue
        Tv, sv, iv, qv = T[v], sec[v], idd[v], qty[v]
        known = (iv >= 0) & (iv <= Tv)
        hs = np.where(half_arm & known, np.where((rdd[v] >= 0) & (rdd[v] <= Tv), 2, 1), 0)
        hd = (hdd[v] >= 0) & (hdd[v] <= Tv)
        fo = (fdd[v] >= 0) & (fdd[v] <= Tv)
        st = states_vec(Tv, iv, known, hs, hd, fo)
        if len(chk) < 400:
            for i in range(0, len(Tv), max(1, len(Tv) // 50)):
                chk.append((st[i], LM.state_at(int(Tv[i]), int(iv[i]) if known[i] else None, half_state=int(hs[i]), half_done=bool(hd[i]), forced=bool(fo[i]))))
        L(rows, 'D4', 'alive_composition', tg, 'age%d' % a, 'FULL', 'n_alive_lots', float(v.sum()), 'count', int(len(v)), q='QRY-D4-LM')
        L(rows, 'D4', 'alive_composition', tg, 'age%d' % a, 'FULL', 'mean_entry_weight_alive_over_all', float(np.nanmean(ew[v]) / np.nanmean(ew))
          if np.isfinite(ew).any() else np.nan, 'ratio', int(v.sum()), q='QRY-D4-LM')
        val = qv * np.asarray(G['pc'][Tv, sv], float)
        for q in LM.QS:
            x, cens = fwd(sv, Tv + 1, q)
            ok = ~cens & np.isfinite(x)
            for s_ in np.unique(st):
                m = st == s_
                o = acc.setdefault((a, s_, q), dict(x=[], w=[], d=[], cens=0))
                o['cens'] += int((m & cens).sum())
                o['x'].append(x[m & ok])
                o['w'].append(val[m & ok])
                o['d'].append(Tv[m & ok])
        # 至原 due 的前向超额（剩余 H − a 个间隔；同状态）
        rem = np.maximum(due[v] - (Tv + 1), 0)
        for s_ in np.unique(st):
            m = st == s_
            xs = []
            for qq in np.unique(rem[m]):
                mm = m & (rem == qq)
                if qq <= 0:
                    continue
                x, cens = fwd(sv[mm], Tv[mm] + 1, int(qq))
                xs.append(x[np.isfinite(x)])
            xx = np.concatenate(xs) if xs else np.zeros(0)
            L(rows, 'D4', 'fwd_to_original_due', tg, 'age%d|%s' % (a, s_), 'FULL', 'mean_bp', float(xx.mean() * 1e4) if len(xx) else np.nan, 'bp', int(len(xx)), q='QRY-D4-LM')
    bad = [x for x in chk if x[0] != x[1]]
    if bad:
        raise RuntimeError('landmark 向量状态与 state_at 不一致：%s' % (bad[:3],))
    out = []
    for (a, st_, q), o in sorted(acc.items()):
        x = np.concatenate(o['x'])
        w = np.concatenate(o['w'])
        d = np.concatenate(o['d'])
        for wt in ('EQUAL', 'CAPITAL'):
            if not len(x):
                out.append(dict(exec_id=e, landmark_age=a, state=st_, q=q, weighting=wt, n=0, mean_fwd_excess_bp='', lo='', hi='',
                                status='RIGHT_CENSORED' if o['cens'] else 'EMPTY'))
                continue
            ww = np.ones_like(x) if wt == 'EQUAL' else np.where(np.isfinite(w) & (w > 0), w, 0.0)
            if ww.sum() <= 0:
                out.append(dict(exec_id=e, landmark_age=a, state=st_, q=q, weighting=wt, n=int(len(x)), mean_fwd_excess_bp='', lo='', hi='', status='ZERO_WEIGHT'))
                continue
            mean = float((x * ww).sum() / ww.sum())
            dfm = pd.DataFrame(dict(d=d, xw=x * ww, w=ww)).groupby('d').sum()
            dfm = dfm[dfm.w > 0]
            dm = (dfm.xw / dfm.w).to_numpy()
            se = float(np.std(dm, ddof=1) / np.sqrt(len(dm))) if len(dm) > 1 else np.nan
            out.append(dict(exec_id=e, landmark_age=a, state=st_, q=q, weighting=wt, n=int(len(x)), mean_fwd_excess_bp=mean * 1e4,
                            lo=(mean - 1.96 * se) * 1e4 if np.isfinite(se) else '', hi=(mean + 1.96 * se) * 1e4 if np.isfinite(se) else '',
                            status='COMPUTED' if np.isfinite(se) else 'SINGLE_DAY'))
    return out


# ------------------------------------------------------------------ 每账户作业
def job_acct(args):
    e = args
    ctx = G['ctx']
    try:
        rows = []
        r = ctx.reg.loc[e]
        h = r.exec_hash
        tg = tag(r)
        ti, tf = load_trades(h)
        z = np.load(ST.acct_file(ctx, h), allow_pickle=False)
        IN, DY, Si = z['IN_i'], z['DY'], z['S_i']
        T = ctx.d_end
        DY = DY[:T]
        kinds = np.array([ST.OKN.get(int(k), 'REGULAR') for k in ti[:, 4]], dtype=object) if len(ti) else np.zeros(0, dtype=object)
        out = dict(exec_id=e, status='OK', rows=rows, lm=[], d1=None)
        if len(ti):
            # D1
            nat = r.native_same_trigger_exec_id or (e if r.arm == 'NATIVE' else '')
            cuts = G['qcut'].get(nat)
            d1, side, miss = d1_account(ti, tf, DY, kinds, cuts, T)
            out['d1'] = dict(levels=d1, side=side)
            for (k, q, A_), (v, n) in sorted(d1.items()):
                L(rows, 'D1', 'impact_by_order_kind', k, q, 'FULL', '%s|A%.0e|level' % (tg, A_), v, 'ann_pp', n,
                  status='COMPUTED' if cuts is not None else 'NO_NATIVE_CUTS', q='QRY-D1-IMPACT')
            for (sd, A_), (v, n) in sorted(side.items()):
                L(rows, 'D1', 'impact_by_side', sd, tg, 'FULL', 'A%.0e|level' % A_, v, 'ann_pp', n, q='QRY-D1-IMPACT')
            for A_, n in miss.items():
                L(rows, 'D1', 'cost_missing_orders', tg, 'A%.0e' % A_, 'FULL', 'count', float(n), 'count', status='COMPUTED', q='QRY-D1-IMPACT')
            fa, fan = fee_algebra(ti, tf, DY, kinds, T)
            for A_, Cd in fa.items():
                for nm, v in Cd.items():
                    L(rows, 'D1', 'fee_algebra', nm, tg, 'FULL', 'A%.0e' % A_, v, 'ann_pp', fan['s'] if 'sell' in nm else (fan['b'] if 'buy' in nm else fan['o']),
                      status='COMPUTED' if not nm.startswith('sym_') else 'ALLOCATION_CONVENTION', q='QRY-D1-FEEALG')
            # D5 参与率两分母（A = 1 亿主读；参与率随 A 线性）
            dd, ss = ti[:, 0].astype(np.int64), ti[:, 1].astype(np.int64)
            adv = np.asarray(G['adv20'][dd, ss], float)
            tail = np.asarray(G['tail_amt'][dd, ss], float)
            for den_nm, den in (('ADV20', adv), ('TAIL30MIN', tail)):
                with np.errstate(all='ignore'):
                    pl = tf[:, 1] * (1e8 / O.V0) / den
                for kk in sorted(set(kinds.tolist())):
                    m = (kinds == kk) & np.isfinite(pl)
                    if m.sum() >= 5:
                        for st_, v in (('p50', np.median(pl[m])), ('p90', np.percentile(pl[m], 90)), ('p99', np.percentile(pl[m], 99)), ('mean', np.mean(pl[m]))):
                            L(rows, 'D5', 'participation_%s' % den_nm, tg, kk, 'FULL', 'A1e+08|%s' % st_, float(v), 'ratio', int(m.sum()),
                              status='COMPUTED' if den_nm == 'ADV20' else 'INFO', q='QRY-D5-PART')
            # D8 执行窗：早退卖单（日 < 原 due）
            ex = np.isin(kinds, EXITK) & (ti[:, 5] == 1) & (ti[:, 0] < ti[:, 6])
            if ex.any():
                d_, s_ = dd[ex], ss[ex]
                vw = np.asarray(G['vwap_raw'][d_, s_], float)
                op = np.asarray(G['open_raw'][d_, s_], float)
                with np.errstate(all='ignore'):
                    tv = np.asarray(G['tail_amt'][d_, s_], float) / np.asarray(G['tail_vol'][d_, s_], float)
                    pa = tf[ex, 1] * (1e8 / O.V0) / np.asarray(G['amt'][d_, s_], float)
                w = tf[ex, 1]
                for nm, alt in (('OPEN_vs_VWAP', op), ('TAIL1430_vs_VWAP', tv)):
                    with np.errstate(all='ignore'):
                        x = (alt / vw - 1.0) * 1e4
                    ok = np.isfinite(x)
                    if ok.any():
                        L(rows, 'D8', 'sell_price_opportunity', nm, tg, 'FULL', 'mean_bp', float(x[ok].mean()), 'bp', int(ok.sum()), status='INFO', q='QRY-D8')
                        L(rows, 'D8', 'sell_price_opportunity', nm, tg, 'FULL', 'notional_weighted_bp', float((x[ok] * w[ok]).sum() / w[ok].sum()), 'bp', int(ok.sum()),
                          status='INFO', q='QRY-D8')
                ok = np.isfinite(pa)
                if ok.any():
                    L(rows, 'D8', 'volume_support', 'early_sell_share_of_day_amount', tg, 'FULL', 'A1e+08|mean', float(pa[ok].mean()), 'ratio', int(ok.sum()), status='INFO',
                      q='QRY-D8')
                    L(rows, 'D8', 'volume_support', 'early_sell_share_of_day_amount', tg, 'FULL', 'A1e+08|share_gt_10pct', float((pa[ok] > 0.1).mean()), 'share',
                      int(ok.sum()), status='INFO', q='QRY-D8')
            # D2（主形态 HG10 FEASIBLE 的 H20 / H30）
            if r.H in ('20', '30'):
                hb = held_before(ti, tf)
                d2_supply(rows, tg, e, DY, ti, kinds, hb)
                cuts2 = d2_owner_cuts(r, ti, tf, kinds)
                for grp in ('EXTRA', 'REGULAR'):
                    m = (kinds == grp) & (ti[:, 5] == 0)
                    if m.any():
                        f = d2_feats(r.form, r.memory, r.trigger, ti[m, 0], ti[m, 1])
                        d2_emit(rows, grp, tg, f, cuts2, ~hb[m], ti[m, 0].astype(np.int64), tf[m, 1], ti[m, 1].astype(np.int64))
        # D4：M3 延期
        if r.arm.startswith('EXIT_GATE') and r.trigger != 'NONE' and len(ti):
            m = (ti[:, 3] >= 0) & (ti[:, 5] == 1)
            if m.any():
                g = pd.DataFrame(dict(rq=ti[m, 3], d=ti[m, 0], k=ti[m, 4])).groupby('rq').agg(first=('d', 'min'), last=('d', 'max'), n=('d', 'nunique'),
                                                                                            forced=('k', lambda x: int((x == E.OK_DEADLINE).any())))
                idd = IN[g.index.to_numpy().astype(np.int64), E.IN_DAY]
                for st_, v, u in (('mean_days_intent_to_last_fill', float(np.mean(g['last'].to_numpy() - idd)), 'days'),
                                  ('mean_days_intent_to_first_fill', float(np.mean(g['first'].to_numpy() - idd)), 'days'),
                                  ('share_multi_day_requests', float((g.n > 1).mean()), 'share'), ('share_forced', float(g.forced.mean()), 'share')):
                    L(rows, 'D4', 'exit_gate_delay', tg, e, 'FULL', st_, v, u, len(g), q='QRY-D4-M3')
                out['m3req'] = m3_meta(r, ti, tf, IN, z['IN_f'], DY, rows, tg, e, T)
        # D5：M4 半量
        if r.arm.startswith('EXIT_HALF') and r.trigger != 'NONE':
            hs_, hd_ = float(np.nansum(DY[:, E.DY_HALFST])), float(np.nansum(DY[:, E.DY_HALFDN]))
            for nm, v, u in (('half_requests', float(Si[E.SI_HALF]), 'count'), ('half_started', hs_, 'count'), ('half_completed', hd_, 'count'),
                             ('half_completion_rate', hd_ / hs_ if hs_ > 0 else np.nan, 'share'), ('rearm_episodes', float(Si[E.SI_REARMN]), 'count'),
                             ('rearm_days', float(np.nansum(DY[:, E.DY_REARM])), 'count')):
                L(rows, 'D5', 'half_exit', tg, e, 'FULL', nm, v, u, q='QRY-D5-M4')
            if len(ti):
                lots, sells = lots_frame(ti, tf)
                hl = set(sells[sells.kind == E.OK_EXIT_HALF].lot.tolist())
                hh = lots[lots.lot.isin(hl)]
                if len(hh):
                    fin = sells[sells.lot.isin(hl)].sort_values('day').groupby('lot').kind.last()
                    endk = fin.reindex(hh.lot).to_numpy()
                    open_end = (hh.cl.to_numpy() < 0)
                    for nm, v in (('residual_closed_by_REARM', float(np.mean((endk == E.OK_EXIT_REARM) & ~open_end))),
                                  ('residual_closed_by_DUE', float(np.mean((endk == E.OK_DUE) & ~open_end))),
                                  ('residual_closed_by_DEADLINE', float(np.mean((endk == E.OK_DEADLINE) & ~open_end))),
                                  ('residual_open_at_end', float(np.mean(open_end)))):
                        L(rows, 'D5', 'half_residual', tg, e, 'FULL', nm, v, 'share', int(len(hh)), q='QRY-D5-M4')
                    first_half = sells[sells.kind == E.OK_EXIT_HALF].groupby('lot').day.min()
                    lidv = IN[:, E.IN_LID]
                    mrow = np.isin(lidv, np.array(sorted(hl), dtype=lidv.dtype))
                    fh = first_half.reindex(lidv[mrow]).to_numpy()
                    rep = int((IN[mrow, E.IN_DAY] > fh).sum())
                    L(rows, 'D5', 'half_repeat_signal', tg, e, 'FULL', 'intent_rows_after_first_half', float(rep), 'count', int(len(hh)), q='QRY-D5-M4')
        # D9：受限库存与连续证券持有期（全账户）
        nav = DY[:, E.DYI['nav_post']]
        with np.errstate(all='ignore'):
            for nm, num in (('lock_amt_share_mean', DY[:, E.DYI['lock_amt']]), ('stale_val_share_mean', DY[:, E.DYI['stale_val']]),
                            ('cancel_val_share_mean', DY[:, E.DYI['cancel_val']]), ('unmatched_val_share_mean', DY[:, E.DYI['unmatched_val']])):
                L(rows, 'D9', 'restricted_inventory', nm, tg, 'FULL', 'mean', float(np.nanmean(num / nav)), 'share', int(T), q='QRY-D9')
            sa, sn = float(np.nansum(DY[:, E.DYI['sec_age_sum']])), float(np.nansum(DY[:, E.DYI['sec_age_n']]))
        L(rows, 'D9', 'continuous_security_holding', 'mean_security_age_days', tg, 'FULL', 'mean', sa / sn if sn > 0 else np.nan, 'days', int(sn), q='QRY-D9')
        if e in G['landmark'] and len(ti):
            out['lm'] = landmark_rows(e, r, ti, tf, IN, rows)
        return out
    except Exception as ex:
        import traceback
        return dict(exec_id=e, status='FAILED', err='%s: %s' % (type(ex).__name__, str(ex)[:300]), tb=traceback.format_exc()[-1200:])


def job_rt(args):
    """RANDOM_TARGET 路径重放（带成交日志；种子与 e6q_run.job_random 同式 → 与随机层同一路径）：随机目标买入行的 D2 前向超额，切点用 owner 自己的买入行。"""
    e, mech, paths = args
    ctx = G['ctx']
    try:
        import e6q_run as RN
        RN.G.update(mk=G['mk'], f=G['f'], segi=ctx.segi)
        r = ctx.reg.loc[e]
        row = r.to_dict()
        rows = []
        ti0, tf0 = load_trades(r.exec_hash)
        k0 = np.array([ST.OKN.get(int(k), 'REGULAR') for k in ti0[:, 4]], dtype=object)
        cuts = d2_owner_cuts(r, ti0, tf0, k0)
        rt = E.RT_WITHIN if mech == 'RANDOM_TARGET_WITHIN_ARM' else E.RT_SOURCE
        D, S, N_, NEW, rep = [], [], [], [], []
        T = ctx.d_end
        for p in paths:
            seed = O.stable_u64('E6q', r.logical_id, mech, p) & ((1 << 62) - 1)
            acc = RN.build(row, seed=seed, rt=rt, tlog=True)
            sink = []
            RN.run_flush(acc, 0, T, sink)
            ti = np.concatenate([s[0] for s in sink]) if sink else np.zeros((0, E.NTLI), np.int64)
            tf = np.concatenate([s[1] for s in sink]) if sink else np.zeros((0, E.NTLF))
            hb = held_before(ti, tf)
            m = (ti[:, 4] == E.OK_EXTRA) & (ti[:, 5] == 0)
            D.append(ti[m, 0])
            S.append(ti[m, 1])
            N_.append(tf[m, 1])
            NEW.append(~hb[m])
            if ctx.phase == 'B':
                fp = O.P('randoms', 'daily', r.exec_hash[:2], '%s_%s_%04d.npz' % (r.exec_hash, mech, 0))
                if os.path.exists(fp):
                    zz = np.load(fp, allow_pickle=False)
                    j = np.flatnonzero(zz['path_id'] == p)
                    if len(j):
                        rep.append(float(np.nanmax(np.abs(zz['ne'][j[0]].astype(float) - acc.DY[:T, E.DYI['net_excess']].astype(np.float32).astype(float)))))
        d, s, nv, nw = (np.concatenate(D).astype(np.int64), np.concatenate(S).astype(np.int64), np.concatenate(N_), np.concatenate(NEW))
        tg = tag(r)
        f = d2_feats(r.form, r.memory, r.trigger, d, s)
        d2_emit(rows, mech, tg, f, cuts, nw, d, nv, s)
        L(rows, 'D2', 'random_target_paths', mech, tg, 'FULL', 'paths_replayed', float(len(paths)), 'count', int(len(d)), q='QRY-D2-FWD')
        if rep:
            L(rows, 'D2', 'random_target_paths', mech, tg, 'FULL', 'max_abs_diff_vs_random_layer_daily_ne', float(max(rep)), 'ratio', len(rep),
              status='COMPUTED' if max(rep) <= 1e-6 else 'DIFFERS', q='QRY-D2-FWD')
        return dict(exec_id=e, status='OK', rows=rows, lm=[], d1=None)
    except Exception as ex:
        import traceback
        return dict(exec_id=e, status='FAILED', err='%s: %s' % (type(ex).__name__, str(ex)[:300]), tb=traceback.format_exc()[-1200:])


# ------------------------------------------------------------------ 主进程块
def d1_diffs(ctx, res, rows):
    lv = {x['exec_id']: x['d1'] for x in res if x.get('d1')}
    for e, cur in lv.items():
        r = ctx.reg.loc[e]
        for kind, ref in (('arm_minus_native', r.native_same_trigger_exec_id), ('arm_minus_parent', r.parent_same_arm_exec_id)):
            if not ref or ref == e or ref not in lv:
                continue
            o = lv[ref]
            for k in sorted(set(cur['levels']) | set(o['levels'])):
                a_ = cur['levels'].get(k, (0.0, 0))
                b_ = o['levels'].get(k, (0.0, 0))
                L(rows, 'D1', 'impact_by_order_kind', k[0], k[1], 'FULL', '%s|A%.0e|%s' % (tag(r), k[2], kind), a_[0] - b_[0], 'ann_pp', a_[1], q='QRY-D1-IMPACT')
            for k in sorted(set(cur['side']) | set(o['side'])):
                a_ = cur['side'].get(k, (0.0, 0))
                b_ = o['side'].get(k, (0.0, 0))
                L(rows, 'D1', 'impact_by_side', k[0], tag(r), 'FULL', 'A%.0e|%s' % (k[1], kind), a_[0] - b_[0], 'ann_pp', a_[1], q='QRY-D1-IMPACT')


def e6i_panel(name, segs=None):
    """E6i 测量缓存（只读；只取两推导段）→ 全程网格；返回 (面板, {段: sha256})。"""
    ctx = G['ctx']
    base = os.path.join(os.path.dirname(O.work()), E6I_DIR, 'cache')
    X = np.full((ctx.T, len(ctx.codes)), np.nan)
    cj = {c: j for j, c in enumerate(ctx.codes)}
    shas = {}
    for s in (segs or DSEGS):
        p = os.path.join(base, s, name + '__OBS.npy')
        a = np.load(p)
        z = G['mk'].source(s)
        di = np.searchsorted(ctx.dates, z['dates'])
        cc = np.array([cj[c] for c in z['codes']])
        if a.shape != (len(di), len(cc)):
            raise RuntimeError('E6i %s %s 形状 %s ≠ 源 %s' % (name, s, a.shape, (len(di), len(cc))))
        X[np.ix_(di, cc)] = a
        shas[s] = O.sha_file(p)
    return X, shas


def e6i_alignment(ctx, rows):
    """对齐核：E6i R_cr20_LEGACY 与本缓存 close_adj 20 日收益的截面秩相关（每段 6 日）；< .8（错位时≈0）→ D3 的 K0 / CVR20 列标 ALIGNMENT_FAILED。"""
    X, sh = e6i_panel('R_cr20_LEGACY')
    ca = G['close_adj']
    cors = []
    for s in DSEGS:
        idx = np.flatnonzero(ctx.segi == s)
        for d in idx[np.linspace(40, len(idx) - 1, 6).astype(int)]:
            a = X[d]
            with np.errstate(all='ignore'):
                b = np.asarray(ca[d], float) / np.asarray(ca[d - 20], float) - 1.0
            m = np.isfinite(a) & np.isfinite(b)
            if m.sum() > 100:
                cors.append(float(pd.Series(a[m]).rank().corr(pd.Series(b[m]).rank())))
    med = float(np.median(cors)) if cors else np.nan
    ok = bool(np.isfinite(med) and med >= 0.8)
    L(rows, 'D3', 'e6i_alignment_check', 'R_cr20_LEGACY_vs_close_adj_20d', 'rank_corr', 'DERIV', 'median', med, 'ratio', len(cors),
      status='COMPUTED' if ok else 'ALIGNMENT_FAILED', q='QRY-D3')
    return ok, sh


def d3_block(ctx, rows, facts):
    """D3：只两推导段；H20 / H30 NATIVE NONE（主形态 HG10 FEASIBLE）常规批次；变量在形成日 T 冻结，按当日源域（形成名单）三分位；年龄 a ∈ {1, 5, 10} 的 q5 / q10 前向超额，
    窗口终点 < 2019-01-01；行业作类别。K 强 = 取向后的 K 腿好度（−K0 在当日源域内的三分位，T3 = 最强）；K0 原值另列（E6i K0_LEGACY）；CVR20 风险（E6i C_CVR20_LEGACY）；
    形成权重在 A4b 下几乎全是 1% 上限（每日只有 1–3 个不同值），不作好度分数，只写一行 INFO；混合 Q 评分不在本轮缓存 → 标缺。"""
    ok_align, sh_r = e6i_alignment(ctx, rows)
    K0, sh_k = e6i_panel('K0_LEGACY')
    CV, sh_c = e6i_panel('C_CVR20_LEGACY')
    facts['d3_e6i'] = dict(aligned=ok_align, sha_R_cr20=sh_r, sha_K0=sh_k, sha_CVR20=sh_c, sha_K0_all_segments=G.get('k0_sha_all'), source=E6I_DIR)
    R = ctx.R
    lastd = ctx.d19 - 1
    L(rows, 'D3', 'mixed_Q_score', 'NOT_IN_CACHE', 'A4b 合成只存形成权重；混合 Q 评分无独立列', 'DERIV', 'note', '', 'none', status='NOT_AVAILABLE', q='QRY-D3')
    ptr_, col_, w_ = G['f'][(O.MAIN_FORM, 'HG10')]
    nu = [len(np.unique(np.round(w_[ptr_[d]:ptr_[d + 1]], 10))) for d in range(0, ctx.T - 1, 20) if ptr_[d + 1] > ptr_[d]]
    L(rows, 'D3', 'source_weight_degenerate', 'distinct_weights_per_day', 'formation A4b_CVRv5|HG10（每 20 日抽一日）', 'FULL', 'median', float(np.median(nu)) if nu else np.nan,
      'count', len(nu), status='INFO', q='QRY-D3')
    for H in ('20', '30'):
        rr = R[(R.arm == 'NATIVE') & (R.trigger == 'NONE') & (R.H == H) & (R.form == O.MAIN_FORM) & (R.memory == 'HG10') & (R.scenario == 'FEASIBLE_DAILY')]
        if not len(rr):
            continue
        r = rr.iloc[0]
        ti, tf = load_trades(r.exec_hash)
        lots, _ = lots_frame(ti, tf)
        lots = lots[(lots.e0 >= 1) & (lots.e0 < ctx.d19)]
        e0 = lots.e0.to_numpy().astype(np.int64)
        sec = lots.sec.to_numpy().astype(np.int64)
        cl = lots.cl.to_numpy()
        T0 = e0 - 1
        ptr, col, w = G['f'][(r.form, r.memory)]
        var = {'K_strength': ('panel', G['negK0']), 'K0_raw': ('panel', K0), 'CVR20_risk': ('panel', CV), 'size': ('panel', G['zsize'])}
        labs = {}
        for nm, (kind, Xp) in var.items():
            lab = np.full(len(e0), '', dtype=object)
            if kind == 'panel' and nm in ('K_strength', 'K0_raw', 'CVR20_risk') and not ok_align:
                labs[nm] = lab
                continue
            for d, idx in by_day(T0):
                a, b = ptr[d], ptr[d + 1]
                dom = col[a:b]
                if kind == 'source_weight':
                    vals_dom = w[a:b]
                    pos = np.searchsorted(dom, sec[idx])
                    hit = (pos < len(dom))
                    own = np.full(len(idx), np.nan)
                    own[hit] = np.where(dom[np.minimum(pos[hit], len(dom) - 1)] == sec[idx][hit], vals_dom[np.minimum(pos[hit], len(dom) - 1)], np.nan)
                else:
                    vals_dom = np.asarray(Xp[d, dom], float)
                    own = np.asarray(Xp[d, sec[idx]], float)
                fin = vals_dom[np.isfinite(vals_dom)]
                if len(fin) < 9:
                    continue
                c = np.percentile(fin, [100 / 3.0, 200 / 3.0])
                lab[idx] = lab3(own, tuple(c))
            labs[nm] = lab
        indl = np.asarray(G['ind'][T0, sec])
        labs['industry'] = np.array(['IND%02d' % int(x) if np.isfinite(x) and x >= 0 else '' for x in indl.astype(float)], dtype=object)
        tg = 'NATIVE|NONE|H%s|main|HG10' % H
        means = {}
        for a in (1, 5, 10):
            Ta = e0 + a - 1
            alive = (cl < 0) | (cl > Ta)
            for q in (5, 10):
                x, cens = fwd(sec, Ta + 1, q, last=lastd)
                ok = alive & np.isfinite(x)
                for nm, lab in labs.items():
                    cats = ('T1', 'T2', 'T3') if nm != 'industry' else sorted(set(lab.tolist()) - {''})
                    for t in cats:
                        m = ok & (lab == t)
                        if not m.any():
                            continue
                        mu = float(x[m].mean() * 1e4)
                        means[(nm, t, a, q)] = mu
                        L(rows, 'D3', 'fwd_excess_q%d' % q, nm, 'age%d' % a, 'DERIV_2010_2018', '%s|%s|mean_bp' % (tg, t), mu, 'bp', int(m.sum()),
                          status='INFO' if nm == 'industry' else 'COMPUTED', q='QRY-D3')
                        if nm != 'industry':
                            L(rows, 'D3', 'fwd_excess_q%d' % q, nm, 'age%d' % a, 'DERIV_2010_2018', '%s|%s|day_cluster_se_bp' % (tg, t), day_se(x[m], Ta[m]) * 1e4, 'bp',
                              int(m.sum()), q='QRY-D3')
        xs = {}
        for a in (1, 10):
            Ta = e0 + a - 1
            x, _ = fwd(sec, Ta + 1, 5, last=lastd)
            xs[a] = np.where((cl < 0) | (cl > Ta), x, np.nan)
        for zt in ('T1', 'T2', 'T3'):
            dk = {}
            for kt in ('T1', 'T3'):
                v = {}
                for a in (1, 10):
                    m = np.isfinite(xs[a]) & (labs['K_strength'] == kt) & (labs['size'] == zt)
                    v[a] = float(xs[a][m].mean() * 1e4) if m.any() else np.nan
                dk[kt] = v[1] - v[10]
            L(rows, 'D3', 'decline_age1_to_10_q5_within_size', 'K_strength', 'size_%s|T3_minus_T1' % zt, 'DERIV_2010_2018', '%s|bp' % tg, dk['T3'] - dk['T1'], 'bp',
              q='QRY-D3')
        for nm in ('K_strength', 'K0_raw', 'CVR20_risk', 'size'):
            for q in (5, 10):
                v = {t: means.get((nm, t, 1, q), np.nan) - means.get((nm, t, 10, q), np.nan) for t in ('T1', 'T3')}
                L(rows, 'D3', 'decline_age1_to_10_q%d' % q, nm, 'T3_minus_T1', 'DERIV_2010_2018', '%s|bp' % tg, v['T3'] - v['T1'], 'bp',
                  q='QRY-D3-CC09' if (nm == 'K_strength' and q == 5 and H == '20') else 'QRY-D3')


SNAPCOLS = ['owner_exec_id', 'reference_exec_id', 'owner_arm', 'trigger', 'H', 'side', 'segment', 'n_days', 'native_full_V0', 'new_budget_V0', 'common_V0',
            'uncovered_native_V0', 'uncovered_new_V0', 'r_new_q5_bp', 'r_native_q5_bp', 'to_whom_q5_bp', 'to_whom_pnl_V0', 'trading_less_pnl_V0', 'deferral_pnl_V0',
            'to_whom_ann_pp', 'trading_less_ann_pp', 'deferral_ann_pp', 'unreleased_cash_opp_pnl_V0', 'unreleased_cash_opp_ann_pp', 'deferral_net_of_opp_ann_pp',
            'n_new_rows', 'status', 'note']


def _wavg(x, w):
    ok = np.isfinite(x) & np.isfinite(w) & (w > 0)
    return float((x[ok] * w[ok]).sum() / w[ok].sum()) if ok.any() else np.nan


def snap_buy(r, ti, tf, DY):
    """M1 / M2（买方）：快照 T = 计划日 d（收盘），执行 e = d + 1。原生完整预算 = 引擎同快照记录的 NATIVE 可用额（DY extra_native_plan），新动作预算 = 本臂票据总额（DY rt_arm_use）；
    共同预算 = 两者较小者。新动作篮子 = e 日 EXTRA 买入（实际成交名义）；原生篮子 = 形成日 d 名单按源权重 f_w 的比例（缩到共同预算；单股 / 行业截断不重算 → 比例为未截断近似）。"""
    xn, au = DY[:, E.DY_XNAT], DY[:, E.DY_ARMUSE]
    nav = DY[:, E.DYI['nav_post']]
    ptr, col, w = G['f'][(r.form, r.memory)]
    ex = (ti[:, 4] == E.OK_EXTRA) & (ti[:, 5] == 0)
    by = {}
    if ex.any():
        g = pd.DataFrame(dict(d=ti[ex, 0], s=ti[ex, 1], v=tf[ex, 1])).groupby(['d', 's']).v.sum().reset_index()
        for d, x in g.groupby('d'):
            by[int(d)] = (x.s.to_numpy().astype(np.int64), x.v.to_numpy())
    out = []
    for d in np.flatnonzero((xn > 1e-12) | (au > 1e-12)):
        e = int(d) + 1
        if e > G['last']:
            continue
        nf, nb = float(xn[d]), float(au[d])
        com = min(nf, nb)
        a, b = ptr[d], ptr[d + 1]
        cs, ws = col[a:b], w[a:b]
        m = ws > 0
        cs, ws = cs[m].astype(np.int64), ws[m]
        x_nat, _ = fwd(cs, np.full(len(cs), e), 5)
        sn, vn = by.get(e, (np.zeros(0, np.int64), np.zeros(0)))
        x_new, _ = fwd(sn, np.full(len(sn), e), 5) if len(sn) else (np.zeros(0), None)
        out.append(dict(d=int(d), e=e, nf=nf, nb=nb, com=com, unn=nf - com, unw=nb - com, r_new=_wavg(x_new, vn), r_nat=_wavg(x_nat, ws), n_new=len(sn), nav=float(nav[d])))
    return pd.DataFrame(out)


def snap_sell(r, ti, tf, IN, INf, DY):
    """M3（卖方）：快照 T = 意向日 d；原生 = e = d + 1 全部卖出当日意向批次（价值 = 意向时整批价值）；新动作 = 门控在 e 日实际分配的卖出（同请求成交名义）；
    共同预算 = 两者较小者；"交给谁"= 同额下新动作所卖批次 vs 全部意向批次按价值比例缩量的前向超额差（卖出：所卖名字之后越差越好）；延期 = 推迟部分从 e 到实际卖出日的超额 × 名义。"""
    nav = DY[:, E.DYI['nav_post']]
    ptr, col, w = G['f'][(r.form, r.memory)]
    m = IN[:, E.IN_KIND] == E.KD_TRIG
    rid = np.flatnonzero(m)
    req = pd.DataFrame(dict(rq=rid, d=IN[m, E.IN_DAY].astype(np.int64), s=IN[m, E.IN_SEC].astype(np.int64), v=INf[m, 0]))
    sl = (ti[:, 5] == 1) & (ti[:, 3] >= 0)
    fills = pd.DataFrame(dict(rq=ti[sl, 3].astype(np.int64), day=ti[sl, 0].astype(np.int64), s=ti[sl, 1].astype(np.int64), v=tf[sl, 1])).merge(req[['rq', 'd']], on='rq', how='inner')
    first = fills[fills.day == fills.d + 1]
    later = fills[fills.day > fills.d + 1]
    f1 = {int(d): x for d, x in first.groupby('d')}
    lt = {int(d): x for d, x in later.groupby('d')}
    pv, cb = G['pv'], G['cumbench']
    out = []
    for d, g in req.groupby('d'):
        d = int(d)
        e = d + 1
        if e > G['last']:
            continue
        nf = float(g.v.sum())
        x1 = f1.get(d)
        nb = float(x1.v.sum()) if x1 is not None else 0.0
        com = min(nf, nb)
        x_nat, _ = fwd(g.s.to_numpy(), np.full(len(g), e), 5)
        if x1 is not None:
            x_new, _ = fwd(x1.s.to_numpy(), np.full(len(x1), e), 5)
            r_new = _wavg(x_new, x1.v.to_numpy())
        else:
            r_new = np.nan
        dp, op = 0.0, 0.0
        y = lt.get(d)
        if y is not None:
            dd, ss = y.day.to_numpy(), y.s.to_numpy()
            with np.errstate(all='ignore'):
                xx = (np.asarray(pv[dd, ss], float) / np.asarray(pv[np.full(len(dd), e), ss], float) - 1.0) - (cb[dd] / cb[e] - 1.0)
            dp = float(np.nansum(xx * y.v.to_numpy()))
            # 未释放现金的机会收益：原生在 e 日释放现金并按形成日 d 名单源权重再投；推迟名义 × 该篮子 e → 实际卖出日的超额
            a, b = ptr[d], ptr[d + 1]
            cs, ws = col[a:b].astype(np.int64), w[a:b]
            mk = ws > 0
            cs, ws = cs[mk], ws[mk]
            if len(cs):
                p0 = np.asarray(pv[e, cs], float)
                for day_, v_ in zip(dd, y.v.to_numpy()):
                    with np.errstate(all='ignore'):
                        xb = np.asarray(pv[day_, cs], float) / p0 - 1.0
                    okb = np.isfinite(xb)
                    if okb.any():
                        op += float(v_ * ((xb[okb] * ws[okb]).sum() / ws[okb].sum() - (cb[day_] / cb[e] - 1.0)))
        out.append(dict(d=d, e=e, nf=nf, nb=nb, com=com, unn=nf - com, unw=nb - com, r_new=r_new, r_nat=_wavg(x_nat, g.v.to_numpy()), n_new=0 if x1 is None else len(x1),
                        nav=float(nav[d]), defer=dp, opp=op))
    return pd.DataFrame(out)


def snapshot_block(ctx, facts):
    """plan §7.4：20 项固定快照金额控制（不是账户、不进政策；只读表）。原生完整预算 / 新动作预算 / 共同预算 / 未覆盖部分 + 同额"交给谁"差 + 买方"少交易"机会 + 卖方延期损益；
    按执行日 e 所在段汇总（FULL = 全部）；*_ann_pp = Σ(效应 / 当日 NAV) / 支持日数 × 252 × 100（局部读数，不拼成策略净值）。"""
    LS = O.read_csv(O.P('registration', 'local_snapshot_refs_E6q.csv'), dtype=str).fillna('')
    rows = []
    nd_all = {s: int((ctx.segi[:ctx.d_end] == s).sum()) for s in SEG4}
    nd_all['FULL'] = int(ctx.d_end)
    for x in LS.itertuples(index=False):
        r = ctx.reg.loc[x.owner_exec_id]
        ti, tf = load_trades(r.exec_hash)
        z = np.load(ST.acct_file(ctx, r.exec_hash), allow_pickle=False)
        DY = z['DY'][:ctx.d_end]
        buy = r.arm.startswith('REINVEST')
        D = snap_buy(r, ti, tf, DY) if buy else snap_sell(r, ti, tf, z['IN_i'], z['IN_f'], DY)
        if not len(D):
            rows.append(dict(owner_exec_id=x.owner_exec_id, reference_exec_id=x.reference_exec_id, owner_arm=r.arm, trigger=r.trigger, H=r.H, side='BUY' if buy else 'SELL',
                             segment='FULL', n_days=0, status='NO_INTERVENTION_DAYS', note=''))
            continue
        D['seg'] = ctx.segi[D.e.to_numpy()]
        sgn = 1.0 if buy else -1.0
        D['tw'] = D.com * (D.r_new - D.r_nat) * sgn
        D['tl'] = D.unn * D.r_nat if buy else 0.0
        if 'defer' not in D.columns:
            D['defer'] = 0.0
        if 'opp' not in D.columns:
            D['opp'] = 0.0
        for s in SEG4 + ['FULL']:
            g = D if s == 'FULL' else D[D.seg == s]
            if not len(g):
                continue
            nv = g.nav.to_numpy()
            ok = np.isfinite(g.tw.to_numpy())
            rows.append(dict(owner_exec_id=x.owner_exec_id, reference_exec_id=x.reference_exec_id, owner_arm=r.arm, trigger=r.trigger, H=r.H, side='BUY' if buy else 'SELL',
                             segment=s, n_days=len(g), native_full_V0=g.nf.sum() / O.V0, new_budget_V0=g.nb.sum() / O.V0, common_V0=g.com.sum() / O.V0,
                             uncovered_native_V0=g.unn.sum() / O.V0, uncovered_new_V0=g.unw.sum() / O.V0, r_new_q5_bp=_wavg(g.r_new.to_numpy(), g.com.to_numpy()) * 1e4,
                             r_native_q5_bp=_wavg(g.r_nat.to_numpy(), g.com.to_numpy()) * 1e4,
                             to_whom_q5_bp=sgn * (_wavg(g.r_new.to_numpy(), g.com.to_numpy()) - _wavg(g.r_nat.to_numpy(), g.com.to_numpy())) * 1e4,
                             to_whom_pnl_V0=float(np.nansum(g.tw)) / O.V0, trading_less_pnl_V0=float(np.nansum(g.tl)) / O.V0, deferral_pnl_V0=float(np.nansum(g.defer)) / O.V0,
                             to_whom_ann_pp=float(np.nansum(np.where(ok, g.tw.to_numpy(), 0.0) / nv)) / nd_all[s] * O.ANN_PP,
                             trading_less_ann_pp=float(np.nansum(np.asarray(g.tl, float) / nv)) / nd_all[s] * O.ANN_PP,
                             deferral_ann_pp=float(np.nansum(g.defer.to_numpy() / nv)) / nd_all[s] * O.ANN_PP, unreleased_cash_opp_pnl_V0=float(np.nansum(g.opp)) / O.V0,
                             unreleased_cash_opp_ann_pp=float(np.nansum(g.opp.to_numpy() / nv)) / nd_all[s] * O.ANN_PP,
                             deferral_net_of_opp_ann_pp=float(np.nansum((g.defer.to_numpy() - g.opp.to_numpy()) / nv)) / nd_all[s] * O.ANN_PP, n_new_rows=int(g.n_new.sum()), status='COMPUTED',
                             note='买方原生比例 = 形成名单源权重（未截断近似）；q5 前向超额（e 日 VWAP 起，clean 等权基准）' if buy else
                             '卖方：同额按全部意向批次价值比例缩量；延期 = 推迟部分 e → 实际卖出日超额 × 名义；未释放现金机会 = 同名义按形成名单源权重篮子同窗口超额（原生在 e 日释放再投的近似）'))
    S_ = pd.DataFrame(rows, columns=SNAPCOLS)
    p = ctx.out('diagnostics', 'local_snapshot_E6q.csv')
    O.atomic_write_csv(p, S_)
    facts['local_snapshot_rows'] = len(S_)
    return p


def feedback_components(ctx, rows):
    """plan §9.4：费用反馈路径 vs 同对象固定路径的分项（描述性，不作可加分解）：数量 / NAV（期末 NAV 比、反馈实收冲击）、触发风险集（意向数差）、
    资金时钟（现金份额均值差）、未成交（未匹配 / 撤单名义差）。逐反馈路径写 D10（INFO）。"""
    import e6q_run as RN
    F = O.read_csv(O.P('registration', 'cost_feedback_refs_E6q.csv'), dtype=str).fillna('')
    I = E.DYI
    for f in F.itertuples(index=False):
        r = ctx.reg.loc[f.owner_exec_id]
        hf = RN.fb_hash(f.owner_exec_id, int(float(f.A0_cny)))
        pf, pa = ST.acct_file(ctx, hf, 'fb'), ST.acct_file(ctx, r.exec_hash)
        if not (os.path.exists(pf) and os.path.exists(pa)):
            L(rows, 'D10', 'feedback_vs_fixed_components', f.feedback_id, tag(r), 'FULL', 'missing', '', 'none', status='NOT_AVAILABLE', q='QRY-D10-FB')
            continue
        zf = np.load(pf, allow_pickle=False)['DY'][:ctx.d_end]
        za = np.load(pa, allow_pickle=False)['DY'][:ctx.d_end]
        navf, nava = zf[:, I['nav_post']], za[:, I['nav_post']]
        vprev = np.r_[O.V0, navf[:-1]]
        with np.errstate(all='ignore'):
            comps = (('nav_end_ratio_fb_over_fixed', float(navf[-1] / nava[-1]), 'ratio'),
                     ('feedback_impact_charged_ann_pp', float(np.nanmean(zf[:, I['fb_impact']] / vprev) * O.ANN_PP), 'ann_pp'),
                     ('intents_diff', float(np.nansum(zf[:, I['n_intents']]) - np.nansum(za[:, I['n_intents']])), 'count'),
                     ('cash_share_mean_diff', float(np.nanmean(zf[:, I['cash_share']]) - np.nanmean(za[:, I['cash_share']])), 'share'),
                     ('unmatched_val_diff_V0', float(np.nansum(zf[:, I['unmatched_val']]) - np.nansum(za[:, I['unmatched_val']])) / O.V0, 'V0'),
                     ('cancel_val_diff_V0', float(np.nansum(zf[:, I['cancel_val']]) - np.nansum(za[:, I['cancel_val']])) / O.V0, 'V0'),
                     ('turnover_ann_diff', float(np.nanmean(0.5 * zf[:, I['traded']] / navf) - np.nanmean(0.5 * za[:, I['traded']] / nava)) * 252.0, 'ratio'))
        for k, v, u in comps:
            L(rows, 'D10', 'feedback_vs_fixed_components', f.feedback_id, tag(r), 'FULL', k, v, u, status='INFO', q='QRY-D10-FB')


def d5_interaction(ctx, AS, rows):
    """卖半 × 再投半四账户：交互 = N(EXIT_HALF_RECYCLE_HALF) − N(EXIT_HALF) − N(RECYCLE_HALF) + N(NATIVE)（同 H、同触发、主形态 HG10 FEASIBLE；net_ann_pp）。"""
    R = ctx.R
    asi = AS.set_index(['exec_id', 'segment'])
    base = R[(R.form == O.MAIN_FORM) & (R.memory == 'HG10') & (R.scenario == 'FEASIBLE_DAILY')]
    for (H, tr), g in base.groupby(['H', 'trigger']):
        ids = {a: g[g.arm == a].exec_id.iloc[0] for a in ('NATIVE', 'EXIT_HALF', 'RECYCLE_HALF', 'EXIT_HALF_RECYCLE_HALF') if (g.arm == a).any()}
        if len(ids) < 4:
            continue
        for s in SEG4 + ['FULL']:
            try:
                v = {a: float(asi.loc[(e, s)].net_ann_pp) for a, e in ids.items()}
            except KeyError:
                continue
            ia = v['EXIT_HALF_RECYCLE_HALF'] - v['EXIT_HALF'] - v['RECYCLE_HALF'] + v['NATIVE']
            for a, x in v.items():
                L(rows, 'D5', 'half_x_recycle_four_accounts', 'H%s|%s' % (H, tr), a, s, 'net_ann_pp', x, 'ann_pp', q='QRY-D5-INT')
            L(rows, 'D5', 'half_x_recycle_four_accounts', 'H%s|%s' % (H, tr), 'INTERACTION', s, 'net_ann_pp', ia, 'ann_pp', q='QRY-D5-INT')


def d7_block(ctx, rows):
    root = ctx.root
    prd = os.path.join(root, 'statistics', 'randoms_E6q.csv')
    if not os.path.exists(prd):
        L(rows, 'D7', 'count_vs_amount_isk', 'randoms table absent', '', 'FULL', 'note', '', 'none', status='NOT_APPLICABLE', q='QRY-D7')
        piv = pd.DataFrame()
    else:
        RD = pd.read_csv(prd, keep_default_na=False, na_values=[''])
        full = RD[RD.segment == 'FULL']
        piv = full.pivot_table(index='owner_exec_id', columns='mechanism', values='rand_mean_D_ann_pp')
    if 'COUNT_ISK' in piv.columns and 'AMOUNT_ISK_V2' in piv.columns:
        for e, x in piv.iterrows():
            L(rows, 'D7', 'count_vs_amount_isk', tag(ctx.reg.loc[e]), e, 'FULL', 'rand_mean_D_count_minus_amount', float(x.COUNT_ISK - x.AMOUNT_ISK_V2), 'ann_pp', q='QRY-D7')
    R = ctx.R
    base = R[(R.form == O.MAIN_FORM) & (R.memory == 'HG10') & (R.scenario == 'FEASIBLE_DAILY') & (R.arm == 'NATIVE')]
    # LOSO 触发密度（意向日；本股不计）× 卖出后 q5 前向超额
    for r in base[base.trigger.isin(['T1a', 'T1b_LEVEL']) & base.H.isin(['20', '30'])].itertuples(index=False):
        IN = np.load(ST.acct_file(ctx, r.exec_hash), allow_pickle=False)['IN_i']
        m = IN[:, E.IN_KIND] == E.KD_TRIG
        d, s = IN[m, E.IN_DAY].astype(np.int64), IN[m, E.IN_SEC].astype(np.int64)
        ld = loso_density(r.trigger, d, s)
        lab = lab3(ld, cuts3(ld))
        x, cens = fwd(s, d + 1, 5)
        for t in ('T1', 'T2', 'T3'):
            mm = (lab == t) & np.isfinite(x)
            L(rows, 'D7', 'loso_trigger_density_fwd_q5_after_intent', tag(r), t, 'FULL', 'mean_bp', float(x[mm].mean() * 1e4) if mm.any() else np.nan, 'bp', int(mm.sum()),
              q='QRY-D7-LOSO')
        L(rows, 'D7', 'loso_trigger_density', tag(r), 'all_intents', 'FULL', 'mean', float(np.nanmean(ld)), 'share', int(np.isfinite(ld).sum()), q='QRY-D7-LOSO')
    # 并集交集 / 两边独有：次数、金额、q5、费用
    t1a, t8 = trig_panel('T1a'), trig_panel('T8_LIMIT_CLOSE')
    for r in R[(R.trigger == 'UNION_T1a_T8') & (R.scenario == 'FEASIBLE_DAILY')].itertuples(index=False):
        z = np.load(ST.acct_file(ctx, r.exec_hash), allow_pickle=False)
        IN, INf = z['IN_i'], z['IN_f']
        m = IN[:, E.IN_KIND] == E.KD_TRIG
        rid = np.flatnonzero(m)
        d, s = IN[m, E.IN_DAY].astype(np.int64), IN[m, E.IN_SEC].astype(np.int64)
        a = np.asarray(t1a[d, s]) == 1
        b = np.asarray(t8[d, s]) == 1
        grp = np.where(a & b, 'both', np.where(a, 'T1a_only', np.where(b, 'T8_only', 'neither')))
        val = INf[m, 0]
        x, cens = fwd(s, d + 1, 5)
        ti, tf = load_trades(r.exec_hash)
        fee = pd.Series(tf[:, 3]).groupby(ti[:, 3]).sum() if len(ti) else pd.Series(dtype=float)
        fr = fee.reindex(rid).fillna(0.0).to_numpy()
        n = len(d)
        for nm in ('T1a_only', 'T8_only', 'both', 'neither'):
            mm = grp == nm
            L(rows, 'D7', 'union_composition', tag(r), nm, 'FULL', 'count_share', float(mm.mean()) if n else np.nan, 'share', int(mm.sum()), q='QRY-D7-UNION')
            L(rows, 'D7', 'union_composition', tag(r), nm, 'FULL', 'amount_share', float(val[mm].sum() / val.sum()) if val.sum() > 0 else np.nan, 'share', int(mm.sum()),
              q='QRY-D7-UNION')
            ok = mm & np.isfinite(x)
            L(rows, 'D7', 'union_composition', tag(r), nm, 'FULL', 'fwd_q5_after_intent_mean_bp', float(x[ok].mean() * 1e4) if ok.any() else np.nan, 'bp', int(ok.sum()),
              q='QRY-D7-UNION')
            L(rows, 'D7', 'union_composition', tag(r), nm, 'FULL', 'exit_fee_sum_V0', float(fr[mm].sum()), 'value_V0', int(mm.sum()), q='QRY-D7-UNION')


def table_blocks(ctx, AS, rows):
    R = ctx.R
    asi = AS.set_index(['exec_id', 'segment'])
    root = ctx.root
    dn = pd.read_csv(os.path.join(root, 'statistics', 'density_E6q.csv'), keep_default_na=False, na_values=[''])
    for x in dn[dn.exponent == 0.5].itertuples(index=False):
        k = '%s|%s|A%.0e|k%.1f' % (tag(ctx.reg.loc[x.exec_id]), x.reference_kind, float(x.A_cny), float(x.kappa))
        st = 'COMPUTED' if x.denominator_status == 'OK' else str(x.denominator_status)
        for nm, v in (('value_density', x.value_density), ('cost_density', x.cost_density)):
            L(rows, 'D6', nm, k, x.exec_id, x.segment, 'ann_pp_per_turn', float(v) if pd.notna(v) else np.nan, 'ratio', status=st, q='QRY-D6')
        L(rows, 'D6', 'numerators', k, x.exec_id, x.segment, 'd_net8|d_impact|d_turn|d_exposure',
          '|'.join('%.6g' % float(v) if pd.notna(v) else 'NA' for v in (x.d_net8_ann_pp, x.d_impact_ann_pp, x.d_turn, x.d_exposure)), 'mixed', status='INFO', q='QRY-D6')
    for r in R.itertuples(index=False):
        if r.is_primary32 != '1' and not (r.trigger == 'NONE' and r.form == O.MAIN_FORM and r.memory == 'HG10'):
            continue
        for s in SEG4 + ['FULL']:
            if (r.exec_id, s) not in asi.index:
                continue
            x = asi.loc[(r.exec_id, s)]
            for c, u in (('net_ann_pp', 'ann_pp'), ('abs_net_ann_pp', 'ann_pp'), ('full_bench_excess_ann_pp', 'ann_pp'), ('max_drawdown_total', 'ratio'),
                         ('cagr_total', 'ratio'), ('exposure_mean', 'share'), ('cash_share_mean', 'share'), ('turnover_ann', 'ratio'), ('size_dev_pp', 'pp'),
                         ('sector_active_max_pp', 'pp')):
                v = x.get(c, np.nan)
                L(rows, 'D9', c, tag(r), r.exec_id, s, 'value', float(v) if pd.notna(v) and v != '' else np.nan, u, q='QRY-D9')
    Y = pd.read_csv(os.path.join(root, 'statistics', 'yearly_E6q.csv'), keep_default_na=False, na_values=[''])
    for e, g in Y[Y.D_same_arm_ann_pp.notna()].groupby('exec_id'):
        r = ctx.reg.loc[e]
        if r.is_primary32 != '1':
            continue
        L(rows, 'D9', 'positive_years', tag(r), e, 'FULL', 'count', float((g.D_same_arm_ann_pp > 0).sum()), 'count', len(g), q='QRY-D9')
        L(rows, 'D9', 'worst_year_D', tag(r), e, 'FULL', 'min', float(g.D_same_arm_ann_pp.min()), 'ann_pp', len(g), q='QRY-D9')
    CC = pd.read_csv(os.path.join(root, 'statistics', 'cost_curve_E6q.csv'), keep_default_na=False, na_values=[''])
    cc = CC[(CC.comparator_kind == 'SAME_ARM_PARENT') & (CC.segment == 'FULL') & (CC.exponent == 0.5)]
    piv = cc[cc.A_cny.astype(float) == 1e8].pivot_table(index='exec_id', columns='kappa', values='net_after_impact_diff_ann_pp')
    if 0.5 in piv.columns and 1.0 in piv.columns:
        L(rows, 'D10', 'kappa_sign_flips', 'A1e8|delta.5|k.5_vs_k1', 'all_accounts', 'FULL', 'count', float((np.sign(piv[0.5]) != np.sign(piv[1.0])).sum()), 'count', len(piv),
          q='QRY-D10')
    for r in R[(R.A_ref != '') & (R.is_primary32 == '1')].itertuples(index=False):
        for A_ in (1e8, 5e8):
            v = cc[(cc.exec_id == r.exec_id) & (cc.kappa.astype(float) == 0.5) & (cc.A_cny.astype(float) == A_)]
            L(rows, 'D10', 'A_ref_vs_A_eval', '%s|A_ref=%s' % (tag(r), r.A_ref), r.exec_id, 'FULL', 'net_after_impact_A%.0e' % A_,
              float(v.net_after_impact_diff_ann_pp.iloc[0]) if len(v) else np.nan, 'ann_pp', q='QRY-D10')
    ev = pd.read_csv(os.path.join(root, 'events', 'event_counts_E6q.csv'), keep_default_na=False, na_values=[''])
    for c in ('n_quarantined_tokens', 'n_new_name_empty_days', 'n_deadline_overrides', 'n_no_action_opportunity'):
        L(rows, 'D10', 'coverage_and_fallback', c, 'all_accounts', 'FULL', 'sum', float(pd.to_numeric(ev[c], errors='coerce').sum()), 'count', len(ev), q='QRY-D10')
    for r in R[R.is_primary32 == '1'].itertuples(index=False):
        if (r.exec_id, 'FULL') in asi.index:
            x = asi.loc[(r.exec_id, 'FULL')]
            L(rows, 'D10', 'benchmark_double_report', tag(r), r.exec_id, 'FULL', 'net_minus_full_bench_excess', float(x.net_ann_pp - x.full_bench_excess_ann_pp), 'ann_pp',
              q='QRY-D10')
    pk = O.read_csv(O.P('registration', 'park_E6q.csv'), dtype=str).fillna('')
    for p in pk.itertuples(index=False):
        L(rows, 'D10', 'park_status', p.park_id, p.status, 'FULL', 'domain', str(p.domain)[:200], 'text', status='INFO', q='QRY-D10')
    for nm, v in (('new_daily_state_columns', float(E.NDY - 76)), ('new_order_kinds', 3.0), ('new_intent_kinds', 1.0)):
        L(rows, 'D10', 'complexity', nm, 'engine', 'FULL', 'count', v, 'count', status='INFO', q='QRY-D10')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=['A2', 'B'], default='B')
    ap.add_argument('--root', default='')
    ap.add_argument('--workers', type=int, default=96)
    ap.add_argument('--rt_paths', type=int, default=4)
    a = ap.parse_args()
    t0 = time.time()
    root = O.P(*a.root.split('/')) if a.root else None
    ctx = ST.Ctx(a.phase, False, root)
    AS = pd.read_csv(os.path.join(ctx.root, 'statistics', 'account_summary_E6q.csv'), keep_default_na=False, na_values=[''])
    setup(ctx)
    R = ctx.R
    sel = R[(R.scenario == 'FEASIBLE_DAILY') & (R.form == O.MAIN_FORM) & (R.memory == 'HG10')]
    p32 = R[R.is_primary32 == '1']
    G['landmark'] = set(p32.exec_id) | set(x for x in p32.parent_same_arm_exec_id if x)
    # D1 切点：同触发 NATIVE 的净单参与率五分位（A = 1 亿；参与率随 A 线性 → 各 A 分组相同）
    G['qcut'] = {}
    for e in sorted(set(sel[sel.arm == 'NATIVE'].exec_id) | set(x for x in sel.native_same_trigger_exec_id if x)):
        r = ctx.reg.loc[e]
        ti, tf = load_trades(r.exec_hash)
        DY = np.load(ST.acct_file(ctx, r.exec_hash), allow_pickle=False)['DY'][:ctx.d_end]
        G['qcut'][e] = qcuts(net_orders(ti, tf, DY)) if len(ti) else None
    rows, lm, facts = [], [], dict(phase=a.phase)
    jobs = list(sel.exec_id)
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6q.csv'), dtype=str).fillna('')
    Rl = R.set_index('logical_id', drop=False)
    rtj = []
    for x in RR[RR.mechanism.str.startswith('RANDOM_TARGET')].itertuples(index=False):
        rr = Rl.loc[x.owner_logical_id]
        if rr.form == O.MAIN_FORM and rr.memory == 'HG10' and rr.H == '20' and rr.scenario == 'FEASIBLE_DAILY':
            rtj.append((rr.exec_id, x.mechanism, list(range(a.rt_paths))))
    facts.update(n_account_jobs=len(jobs), n_rt_jobs=len(rtj), qcut_natives=len(G['qcut']))
    with get_context('fork').Pool(max(1, min(a.workers, len(jobs) + len(rtj)))) as pool:
        res = list(pool.imap_unordered(job_rt, rtj)) + list(pool.imap_unordered(job_acct, jobs))
    bad = [x for x in res if x['status'] != 'OK']
    for x in res:
        if x['status'] == 'OK':
            rows += x['rows']
            lm += x['lm']
    d1_diffs(ctx, [x for x in res if x['status'] == 'OK'], rows)
    table_blocks(ctx, AS, rows)
    d3_block(ctx, rows, facts)
    d5_interaction(ctx, AS, rows)
    d7_block(ctx, rows)
    feedback_components(ctx, rows)
    snap_p = snapshot_block(ctx, facts)
    D = pd.DataFrame(rows, columns=LCOLS)
    names = {'D1': 'cost_source', 'D2': 'target', 'D3': 'entry_persistence', 'D4': 'age_delay', 'D5': 'dose', 'D6': 'density', 'D7': 'composition', 'D8': 'window',
             'D9': 'risk', 'D10': 'externality'}
    outs = []
    for blk, nm in names.items():
        x = D[D.block == blk]
        if not len(x):
            x = pd.DataFrame([dict(block=blk, item='no_rows', key1='', key2='', segment='FULL', stat='count', value=0, unit='count', n=0, status='NOT_APPLICABLE',
                                   query_id='QRY-%s' % blk)], columns=LCOLS)
        p = ctx.out('diagnostics', '%s_%s_E6q.csv' % (blk, nm))
        O.atomic_write_csv(p, x)
        outs.append(p)
    LMD = pd.DataFrame(lm, columns=LMCOLS)
    p = ctx.out('diagnostics', 'landmark_E6q.csv')
    O.atomic_write_csv(p, LMD)
    outs.append(p)
    outs.append(snap_p)
    M3 = pd.DataFrame([row for x in res if x['status'] == 'OK' for row in (x.get('m3req') or [])], columns=M3COLS)
    p = ctx.out('events', 'm3_parent_orders_E6q.csv')
    O.atomic_write_csv(p, M3)
    outs.append(p)
    facts['m3_parent_order_rows'] = len(M3)
    facts.update(rows=len(D), by_block=D.block.value_counts().to_dict(), landmark_rows=len(LMD), failed=len(bad), wall_s=round(time.time() - t0, 1))
    O.write_receipt('E6q_diag_%s' % a.phase, outs, code=[__file__, O.__file__, ST.__file__, CO.__file__, LM.__file__], **facts)
    print(json.dumps(facts, ensure_ascii=False, default=str), flush=True)
    if bad:
        for x in bad[:5]:
            print(x['exec_id'], x['err'], x.get('tb', '')[-800:], flush=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
