# -*- coding: utf-8 -*-
"""E6p 诊断块（plan §10；附录 B.16）：D1 持有期 / 存活、D2 部署、D3 成本 / 参与率、D4 组成（两层信息并排）、D5 再投资、D6 时代 / 状态、D7 CVR 测量、
D8 执行时窗、D9 三折扣（成本分解 / 局部四费用面板 / 日龄 × 剩余 H 机会 / 半退出剂量 / κ 就绪与 F7 对账）；landmark 存活剖面；镜像差；再投资局部同预算。
长格式：block, item, key1, key2, segment, stat, value, unit, n, status, query_id。只读账户 / 成交分片 / 意向 / 面板（截至授权终点）；读法禁令见 plan §10 表。
  python3 e6p_diag.py --phase B [--workers 48]
  python3 e6p_diag.py --phase A2 --root tmp/a2stats    推导段（G1 用）"""
import os
import sys
import json
import time
import argparse
from multiprocessing import get_context

import numpy as np
import pandas as pd

import e6p_core as O
import e6p_engine as E
import e6p_landmark as LM
import e6p_stats as ST

SEG4 = list(O.SEGS)
LCOLS = ['block', 'item', 'key1', 'key2', 'segment', 'stat', 'value', 'unit', 'n', 'status', 'query_id']
G = {}


def L(rows, block, item, key1, key2, segment, stat, value, unit, n='', status='COMPUTED', q=''):
    if isinstance(value, float) and not np.isfinite(value):
        value, status = '', 'UNKNOWN' if status == 'COMPUTED' else status
    rows.append(dict(block=block, item=item, key1=key1, key2=key2, segment=segment, stat=stat, value=value, unit=unit, n=n, status=status, query_id=q or 'QRY-%s' % block))


def short(e):
    p = e.split('|')
    return p[0][-8:] + '|' + p[1][:4]


def sel_accounts(R):
    """TL 级诊断对象（FEASIBLE；主对象两只与其变体 / 父、H5 / H40 同触发、RENEW5、CASH / RECYCLE 的 H20 主触发）。"""
    m = R[(R.role == 'ACCOUNT') & (R.form == O.MAIN_FORM) & (R.memory == 'HG10') & (R.execution_profile == 'FEASIBLE_DAILY')]
    keep = m[((m.H.isin(['5', '20', '40'])) & (m.trigger.isin(['NONE', 'T1a', 'T1b_LEVEL'])) & (m.renew == '0') & (m.cap != 'ABS01'))
             | ((m.renew == '5') & (m.trigger.isin(['NONE', 'T1a', 'T1b_LEVEL'])))
             | ((m.H == '5') & (m.trigger == 'T1b_EDGE') & (m.deploy == 'NATIVE') & (m.renew == '0'))]      # = E6o H5 主对象（F7 对账用）
    return keep


def lots_table(ti, tf, T_end):
    """成交日志 → 批次生命期：lot, sec, e0, due, principal, close_day（未清 = −1）, close_kind（EARLY_EXIT / EARLY_RENEW / DUE / OPEN）, buy_kind。"""
    b = ti[:, 5] == 0
    s = ~b
    buys = pd.DataFrame(dict(lot=ti[b, 2], sec=ti[b, 1], e0=ti[b, 0], due=ti[b, 6], principal=tf[b, 1], qty=tf[b, 0], buy_kind=ti[b, 4]))
    buys = buys.groupby('lot', as_index=False).agg(sec=('sec', 'first'), e0=('e0', 'min'), due=('due', 'first'), principal=('principal', 'sum'), qty=('qty', 'sum'),
                                                    buy_kind=('buy_kind', 'first'))
    sells = pd.DataFrame(dict(lot=ti[s, 2], day=ti[s, 0], kind=ti[s, 4], qty=tf[s, 0]))
    last = sells.groupby('lot').agg(close_day=('day', 'max'), kind=('kind', 'last'), sold=('qty', 'sum'))
    lt = buys.merge(last, left_on='lot', right_index=True, how='left')
    closed = lt.sold.fillna(0) >= lt.qty * (1 - 1e-9)
    lt['close_day'] = np.where(closed, lt.close_day.fillna(-1), -1).astype(int)
    k = lt.kind.fillna(-1).astype(int)
    early = closed & (lt.close_day < lt.due)
    lt['close_kind'] = np.where(~closed, 'OPEN', np.where(early & (k == E.OK_RENEW), 'EARLY_RENEW', np.where(early, 'EARLY_EXIT', 'DUE')))
    return lt


def job_tl(args):
    """单账户 TL 级诊断（D1 / D3 / D5 / D8 / D9-COST / D9-AGE / landmark）。"""
    e, h = args
    ctx = G['ctx']
    try:
        rows = []
        lm_rows = []
        r = ctx.reg.loc[e]
        ti, tf = ST.load_trades(ctx, h)
        z = np.load(ST.acct_file(ctx, h), allow_pickle=False)
        IN = z['IN_i']
        INf = z['IN_f']
        H = int(r.H)
        lt = lots_table(ti, tf, ctx.d_end)
        hold = np.where(lt.close_day >= 0, lt.close_day - lt.e0, ctx.d_end - 1 - lt.e0)
        lt['hold'] = hold
        tag = short(e)
        for cls in ('ALL', 'EARLY_EXIT', 'EARLY_RENEW', 'DUE', 'OPEN'):
            x = lt if cls == 'ALL' else lt[lt.close_kind == cls]
            if not len(x):
                continue
            hv = x.hold.to_numpy(float)
            w = x.principal.to_numpy(float)
            for st_, v in (('mean', hv.mean()), ('median', np.median(hv)), ('p10', np.percentile(hv, 10)), ('p90', np.percentile(hv, 90)),
                           ('mean_principal_weighted', float((hv * w).sum() / w.sum()) if w.sum() > 0 else np.nan)):
                L(rows, 'D1', 'lot_hold_days', cls, e, 'FULL', st_, float(v), 'days', len(x))
            L(rows, 'D1', 'lot_count_share', cls, e, 'FULL', 'share_of_lots', len(x) / len(lt), 'share', len(lt))
        DY = z['DY'][:ctx.d_end]
        L(rows, 'D1', 'security_continuous_age', 'ALL', e, 'FULL', 'mean', float(np.nansum(DY[:, E.DYI['sec_age_sum']]) / max(np.nansum(DY[:, E.DYI['sec_age_n']]), 1)), 'days')
        L(rows, 'D1', 'risk_set', 'R_INTENT_lots', e, 'FULL', 'mean', float(np.nanmean(DY[:, E.DYI['n_risk']])), 'count')
        L(rows, 'D1', 'risk_set', 'R_OBS_securities', e, 'FULL', 'mean', float(np.nanmean(DY[:, E.DYI['n_hold']])), 'count')
        L(rows, 'D1', 'risk_set', 'live_lots', e, 'FULL', 'mean', float(np.nanmean(DY[:, E.DYI['n_lots']])), 'count')
        # D3 参与率（ADV20 主分母；分钟全日额 / 尾盘额两列只作事后）
        if len(ti):
            sg = np.where(ti[:, 5] == 0, 1.0, -1.0)
            df = pd.DataFrame(dict(d=ti[:, 0], s=ti[:, 1], v=sg * tf[:, 1]))
            net = df.groupby(['d', 's']).v.sum().reset_index()
            net = net[net.v.abs() > 0]
            dd, ss = net.d.to_numpy(), net.s.to_numpy()
            dn = net.v.abs().to_numpy()
            navs = DY[:, E.DYI['nav_pre']]
            adv = np.asarray(G['adv20'][dd, ss])
            alla = np.asarray(G['all_amt'][dd, ss])
            tail = np.asarray(G['tail_amt'][dd, ss])
            for A in (1e8, 5e8):
                sc = A / O.V0
                for col, den in (('ADV20', adv), ('MINUTE_ALL_DAY', alla), ('MINUTE_TAIL_1430', tail)):
                    with np.errstate(all='ignore'):
                        p = dn * sc / den
                    p = p[np.isfinite(p)]
                    if len(p):
                        for st_, v in (('mean', p.mean()), ('p50', np.median(p)), ('p90', np.percentile(p, 90)), ('p99', np.percentile(p, 99))):
                            L(rows, 'D3', 'participation', col, e, 'FULL', '%s_A%dyi' % (st_, int(A / 1e8)), float(v), 'ratio', len(p),
                              status='COMPUTED' if col == 'ADV20' else 'INFO')
            # D5 订单来源与费用分摊
            kind = ti[:, 4]
            for k, nm in ST.OKN.items():
                mk_ = kind == k
                if mk_.any():
                    L(rows, 'D5', 'notional_by_order_kind', nm, e, 'FULL', 'share', float(tf[mk_, 1].sum() / tf[:, 1].sum()), 'share', int(mk_.sum()))
                    L(rows, 'D5', 'fee_by_order_kind', nm, e, 'FULL', 'share', float(tf[mk_, 3].sum() / max(tf[:, 3].sum(), 1e-300)), 'share', int(mk_.sum()))
            buys = lt.sort_values('e0')
            rep = 0
            live = {}
            for row in buys.itertuples(index=False):
                prev = live.get(row.sec)
                if prev is not None and (prev < 0 or prev > row.e0):
                    rep += 1
                live[row.sec] = row.close_day if (prev is None or row.close_day < 0 or (prev >= 0 and row.close_day > prev)) else prev
            L(rows, 'D5', 'same_security_repeat_buy', 'lots', e, 'FULL', 'share', rep / max(len(buys), 1), 'share', len(buys))
            L(rows, 'D5', 'internal_transfers', 'security_days', e, 'FULL', 'count', float(np.nansum(DY[:, E.DYI['n_internal']])), 'count')
            # D9-COST：买 / 卖侧固定路径冲击（5 亿 κ .5 δ .5）与线性费用、换手、净额抵消
            sig = np.asarray(G['sig20'][dd, ss])
            gross_b = df[df.v > 0].v.sum()
            gross_s = -df[df.v < 0].v.sum()
            vp = navs[dd]
            with np.errstate(all='ignore'):
                imp = 0.5 * sig * np.sqrt(0.01) * (dn * 5.0 / (adv * 0.01)) ** 0.5 * dn / vp
            imp = np.where(np.isfinite(imp), imp, 0.0)
            side_b = net.v.to_numpy() > 0
            ndays = ctx.d_end
            L(rows, 'D9', 'COST_buy_impact', 'A5yi_k.5_d.5', e, 'FULL', 'ann_pp', float(imp[side_b].sum() / ndays * O.ANN_PP), 'ann_pp')
            L(rows, 'D9', 'COST_sell_impact', 'A5yi_k.5_d.5', e, 'FULL', 'ann_pp', float(imp[~side_b].sum() / ndays * O.ANN_PP), 'ann_pp')
            fee_b = 4e-4 * dn[side_b] / vp[side_b]
            fee_s = 4e-4 * dn[~side_b] / vp[~side_b]
            L(rows, 'D9', 'COST_buy_fee', 'linear_4bp', e, 'FULL', 'ann_pp', float(np.nansum(fee_b) / ndays * O.ANN_PP), 'ann_pp')
            L(rows, 'D9', 'COST_sell_fee', 'linear_4bp', e, 'FULL', 'ann_pp', float(np.nansum(fee_s) / ndays * O.ANN_PP), 'ann_pp')
            L(rows, 'D9', 'COST_netting', 'gross_vs_net', e, 'FULL', 'share_netted', float(1.0 - dn.sum() / max(gross_b + gross_s, 1e-300)), 'share')
            L(rows, 'D9', 'COST_turnover', 'one_side', e, 'FULL', 'ann', float(np.nanmean(0.5 * DY[:, E.DYI['traded']] / DY[:, E.DYI['nav_post']]) * 252), 'ratio')
        # D8 执行时窗：已冻结早退卖单在次日开盘 / 全日 VWAP / 尾盘 VWAP 的同单价格机会差（raw 价，bp；卖出越高越好）
        ex = (ti[:, 4] == E.OK_EXIT) & (ti[:, 5] == 1) & (ti[:, 0] < ti[:, 6]) if len(ti) else np.zeros(0, bool)
        if ex.any():
            d_, s_ = ti[ex, 0], ti[ex, 1]
            vw = np.asarray(G['vwap_raw'][d_, s_])
            op = np.asarray(G['open_raw'][d_, s_])
            tv = np.asarray(G['tail_amt'][d_, s_]) / np.asarray(G['tail_vol'][d_, s_])
            w = tf[ex, 1]
            for nm, alt in (('OPEN_vs_VWAP', op), ('TAIL1430_vs_VWAP', tv)):
                with np.errstate(all='ignore'):
                    x = (alt / vw - 1.0) * 1e4
                ok = np.isfinite(x)
                if ok.any():
                    L(rows, 'D8', 'sell_price_opportunity', nm, e, 'FULL', 'mean_bp', float(x[ok].mean()), 'bp', int(ok.sum()), status='INFO')
                    L(rows, 'D8', 'sell_price_opportunity', nm, e, 'FULL', 'notional_weighted_bp', float((x[ok] * w[ok]).sum() / w[ok].sum()), 'bp', int(ok.sum()), status='INFO')
        # D9-AGE / DOSE：已知触发风险集——意向日龄 × 剩余 H × 至原 due 的后续超额（执行 VWAP → 原 due VWAP）；半退出 = 一半至原 due 的机会
        trig = IN[(IN[:, E.IN_KIND] == E.KD_TRIG)]
        trf = INf[(IN[:, E.IN_KIND] == E.KD_TRIG)]
        if len(trig):
            d0 = trig[:, E.IN_DAY] + 1
            due = trig[:, E.IN_DUE]
            sec = trig[:, E.IN_SEC]
            ok = (due < ctx.d_end) & (d0 < ctx.d_end)
            pv = G['pv']
            cb = G['cumbench']
            with np.errstate(all='ignore'):
                fwd = (np.asarray(pv[np.clip(due, 0, ctx.T - 1), sec]) / np.asarray(pv[np.clip(d0, 0, ctx.T - 1), sec]) - 1.0) - (cb[np.clip(due, 0, ctx.T - 1)] / cb[np.clip(d0, 0, ctx.T - 1)] - 1.0)
            age = trig[:, E.IN_AGE]
            rem = due - d0
            for b_ in range(E.NB):
                lo, hi = O.AGE_BUCKETS[b_]
                m = ok & (age >= lo) & (age <= hi) & np.isfinite(fwd)
                if m.sum():
                    L(rows, 'D9', 'AGE_fwd_excess_to_original_due', '%d-%s' % (lo, hi if hi < 10 ** 5 else '+'), e, 'FULL', 'mean_bp', float(fwd[m].mean() * 1e4), 'bp', int(m.sum()),
                      status='INFO')
                    L(rows, 'D9', 'DOSE_half_exit_keep_half', '%d-%s' % (lo, hi if hi < 10 ** 5 else '+'), e, 'FULL', 'mean_bp_per_intent', float(0.5 * fwd[m].mean() * 1e4), 'bp',
                      int(m.sum()), status='INFO')
            for rb, (lo, hi) in (('rem1-5', (1, 5)), ('rem6-10', (6, 10)), ('rem11-20', (11, 20)), ('rem21+', (21, 10 ** 6))):
                m = ok & (rem >= lo) & (rem <= hi) & np.isfinite(fwd)
                if m.sum():
                    L(rows, 'D9', 'AGE_fwd_excess_to_original_due', rb, e, 'FULL', 'mean_bp', float(fwd[m].mean() * 1e4), 'bp', int(m.sum()), status='INFO')
            cens = int((~ok).sum())
            L(rows, 'D9', 'AGE_fwd_excess_to_original_due', 'RIGHT_CENSORED', e, 'FULL', 'count', float(cens), 'count', cens, status='RIGHT_CENSORED' if cens else 'COMPUTED')
        # landmark（主对象族；年龄 a < H；只用截至 T 的意向 / 检查点记录）
        if G.get('landmark') and e in G['landmark']:
            lm_rows += landmark_rows(ctx, e, r, lt, IN)
        return dict(exec_id=e, status='OK', rows=rows, lm=lm_rows)
    except Exception as ex:
        import traceback
        return dict(exec_id=e, status='FAILED', err='%s: %s' % (type(ex).__name__, str(ex)[:300]), tb=traceback.format_exc()[-900:])


def landmark_rows(ctx, e, r, lt, IN):
    H = int(r.H)
    renew = int(r.renew)
    pv = G['pv']
    pc = G['pc']
    cb = G['cumbench']
    intent = {}
    for lid, d, k in zip(IN[:, E.IN_LID], IN[:, E.IN_DAY], IN[:, E.IN_KIND]):
        if lid not in intent:
            intent[int(lid)] = (int(d), 'RENEW' if k == E.KD_RENEW else 'TRIG')
    nptr, ncol = G['nat']
    known_day = np.diff(nptr) > 0
    isopen = G['isopen']
    lots = lt.lot.to_numpy()
    e0 = lt.e0.to_numpy()
    cl = lt.close_day.to_numpy()
    sec = lt.sec.to_numpy()
    qty = lt.qty.to_numpy()
    idd = np.array([intent.get(int(l), (-1, ''))[0] for l in lots])
    ikd = np.array([intent.get(int(l), (-1, ''))[1] for l in lots])
    out = {}
    chk = 0
    for a in LM.LANDMARK_AGES:
        if a >= H:
            continue
        T = e0 + a - 1
        v = (T < ctx.d_end - 1) & ((cl < 0) | (cl > T))
        if not v.any():
            continue
        Tv, sv, iv, kv, qv, lv = T[v], sec[v], idd[v], ikd[v], qty[v], lots[v]
        known = (iv >= 0) & (iv <= Tv)
        rc = np.full(len(Tv), '', dtype=object)
        if renew and a % renew == 0:
            ck = ~(known & (iv == Tv) & (kv == 'RENEW'))
            okn = known_day[Tv] & np.asarray(isopen[Tv, sv]).astype(bool)
            rc[ck] = np.where(okn[ck], 'CONFIRMED', 'UNKNOWN')
        st = np.where(known & (iv < Tv), 'REQUEST_PENDING',
                      np.where(known & (iv == Tv), np.where(kv == 'RENEW', 'RENEW_REJECTED', 'BAD_STATE'),
                               np.where(rc == 'CONFIRMED', 'RENEW_CONFIRMED', np.where(rc == 'UNKNOWN', 'RENEW_UNKNOWN', 'NOT_TRIGGERED'))))
        for i in range(min(200, len(Tv))):            # 向量化状态与 e6p_landmark.state_at（S0-10 的定义）逐例对照
            ref = LM.state_at(int(Tv[i]), int(iv[i]) if known[i] else None, 'RENEW' if kv[i] == 'RENEW' else 'TRIG', rc[i] or None)
            if ref != st[i]:
                raise RuntimeError('landmark 向量化状态与 state_at 不符：%s vs %s' % (st[i], ref))
            chk += 1
        val = qv * np.asarray(pc[Tv, sv])
        for q in LM.QS:
            s0, s1 = Tv + 1, Tv + 1 + q
            cens = s1 > ctx.d_end - 1
            ok = ~cens
            with np.errstate(all='ignore'):
                x = (np.asarray(pv[np.minimum(s1, ctx.T - 1), sv]) / np.asarray(pv[np.minimum(s0, ctx.T - 1), sv]) - 1.0) - (cb[np.minimum(s1, ctx.T - 1)] / cb[np.minimum(s0, ctx.T - 1)] - 1.0)
            ok = ok & np.isfinite(x)
            for s_ in np.unique(st):
                m = st == s_
                o = out.setdefault((a, s_, q), dict(x=[], w=[], d=[], cens=0))
                o['cens'] += int((m & cens).sum())
                mm = m & ok
                o['x'].append(x[mm])
                o['w'].append(val[mm])
                o['d'].append(Tv[mm])
    rows = []
    for (a, st_, q), o in sorted(out.items()):
        st = st_
        x = np.concatenate(o['x']) if o['x'] else np.zeros(0)
        w = np.concatenate(o['w']) if o['w'] else np.zeros(0)
        d = np.concatenate(o['d']) if o['d'] else np.zeros(0)
        for wt in ('EQUAL', 'CAPITAL'):
            if not len(x):
                rows.append(dict(exec_id=e, landmark_age=a, state=st, q=q, weighting=wt, n=0, status='RIGHT_CENSORED' if o['cens'] else 'UNKNOWN'))
                continue
            ww = np.ones_like(x) if wt == 'EQUAL' else np.where(np.isfinite(w) & (w > 0), w, 0.0)
            if ww.sum() <= 0:
                continue
            mean = float((x * ww).sum() / ww.sum())
            dfm = pd.DataFrame(dict(d=d, xw=x * ww, w=ww)).groupby('d').sum()
            dm = (dfm.xw / dfm.w).to_numpy()
            nd = len(dm)
            se = float(np.std(dm, ddof=1) / np.sqrt(nd)) if nd > 1 else np.nan
            rows.append(dict(exec_id=e, landmark_age=a, state=st, q=q, weighting=wt, n=len(x), mean_fwd_excess_bp=mean * 1e4,
                             lo=(mean - 1.96 * se) * 1e4 if np.isfinite(se) else np.nan, hi=(mean + 1.96 * se) * 1e4 if np.isfinite(se) else np.nan,
                             status='COMPUTED', n_days=nd, n_censored=o['cens']))
    return rows


# ------------------------------------------------------------------ 账户级块（不需 TL）
def deploy_block(ctx, S, AS, rows):
    R = ctx.R
    asi = AS.set_index(['exec_id', 'segment'])
    for r in R[(R.role == 'ACCOUNT') & (R.trigger == 'NONE') & (R.renew == '0')].itertuples(index=False):
        j = ctx.col[r.exec_id]
        for s in SEG4 + ['FULL']:
            m = ctx.masks[s]
            L(rows, 'D2', 'exposure_mean', r.deploy + '|' + r.cap, r.exec_id, s, 'mean', float(np.nanmean(S['expo'][m, j])), 'share', int(m.sum()))
            L(rows, 'D2', 'cash_share_mean', r.deploy + '|' + r.cap, r.exec_id, s, 'mean', float(np.nanmean(S['cash'][m, j])), 'share', int(m.sum()))
            buys = np.nansum(S['buyv'][m, j])
            if buys > 0:
                L(rows, 'D2', 'deploy_buy_share_of_buys', r.deploy + '|' + r.cap, r.exec_id, s, 'share', float(np.nansum(S['deploy_buy'][m, j]) / buys), 'share')
        if r.deploy in ('D80', 'D95'):
            nat = R[(R.role == 'ACCOUNT') & (R.form == r.form) & (R.memory == r.memory) & (R.H == r.H) & (R.deploy == 'NATIVE') & (R.trigger == 'NONE') & (R.renew == '0')
                    & (R.execution_profile == r.execution_profile)]
            if len(nat):
                n_ = nat.iloc[0].exec_id
                for s in SEG4 + ['FULL']:
                    a_, b_ = asi['net_ann_pp'].get((r.exec_id, s), np.nan), asi['net_ann_pp'].get((n_, s), np.nan)
                    L(rows, 'D2', 'DEPLOY_OPERATOR_CHANGE_net_diff', r.deploy + '|' + r.cap, r.exec_id, s, 'ann_pp', float(a_ - b_), 'ann_pp',
                      q='QRY-D2-DEPLOY')


def regime_block(ctx, S, rows):
    R = ctx.R
    b = np.nan_to_num(ctx.bench)
    c20 = pd.Series(b).rolling(20, min_periods=10).sum().shift(1).to_numpy()
    v20 = pd.Series(b).rolling(20, min_periods=10).std().shift(1)
    vmed = v20.rolling(250, min_periods=60).median().to_numpy()
    v20 = v20.to_numpy()
    states = {'BENCH_UP': c20 > 0, 'BENCH_DOWN': c20 <= 0, 'VOL_HIGH': v20 > vmed, 'VOL_LOW': v20 <= vmed}
    main = R[(R.is_main_object == '1')]
    for r in main.itertuples(index=False):
        j, k = ctx.col[r.exec_id], ctx.col[r.parent_same_h_exec_id]
        D = S['ne'][:, j] - S['ne'][:, k]
        for nm, msk in states.items():
            m = msk & ctx.masks['FULL'] & np.isfinite(D)
            L(rows, 'D6', 'state_conditional_D', nm, r.exec_id, 'FULL', 'ann_pp', float(np.mean(D[m]) * O.ANN_PP) if m.any() else np.nan, 'ann_pp', int(m.sum()), status='INFO')
        h5 = ctx.col[r.parent_h5_native_exec_id]
        D5 = S['ne'][:, j] - S['ne'][:, h5]
        for y in ST.YEARS:
            m = (ctx.years == y) & ctx.masks['FULL'] & np.isfinite(D5)
            if m.any():
                L(rows, 'D6', 'year_D_vs_H5_native', str(y), r.exec_id, 'FULL', 'ann_pp', float(np.mean(D5[m]) * O.ANN_PP), 'ann_pp', int(m.sum()),
                  status='INFO' if y != 2026 else 'INFO')


def cvr_block(ctx, rows):
    """D7：日 CVR、3 / 5 日成交 VWAP 相对现收、20 日比值均值（raw 价 / 额 / 量，同支持）；pool0 形成日域；秩相关与上十分位重叠；尾盘 VWAP 高于收盘份额（bar 近似）。"""
    cd = ctx.cd
    P = lambda k: np.load(os.path.join(cd, 'panels', k + '.npy'), mmap_mode='r')
    close = np.asarray(P('close_raw'))
    amt = np.asarray(P('amt'))
    vol = np.asarray(P('vol'))
    cvr1 = np.asarray(P('cvr1d'))
    pool0 = np.asarray(np.load(os.path.join(cd, 'triggers', 'pool0.npy'), mmap_mode='r')).astype(bool)
    pool0[ctx.d_end:] = False
    def kvwap(k):
        a = pd.DataFrame(amt).rolling(k, min_periods=k).sum().to_numpy()
        v = pd.DataFrame(vol).rolling(k, min_periods=k).sum().to_numpy()
        with np.errstate(all='ignore'):
            return close / (a / v) - 1.0
    c3, c5 = kvwap(3), kvwap(5)
    c20 = pd.DataFrame(cvr1).rolling(20, min_periods=20).mean().to_numpy()
    meas = {'cvr_1d': cvr1, 'cvr_3d_ratio_of_sums': c3, 'cvr_5d_ratio_of_sums': c5, 'cvr_20d_mean_of_ratios': c20}
    rng = np.random.default_rng(3)
    days = np.flatnonzero(pool0.any(1))
    for nm, X in meas.items():
        if nm == 'cvr_1d':
            continue
        cors, ovl = [], []
        for d in days[::5]:
            m = pool0[d] & np.isfinite(X[d]) & np.isfinite(cvr1[d])
            if m.sum() < 30:
                continue
            a = pd.Series(cvr1[d, m]).rank().to_numpy()
            b = pd.Series(X[d, m]).rank().to_numpy()
            cors.append(np.corrcoef(a, b)[0, 1])
            ta = a >= np.percentile(a, 90)
            tb = b >= np.percentile(b, 90)
            ovl.append((ta & tb).sum() / max(ta.sum(), 1))
        L(rows, 'D7', 'rank_corr_vs_cvr_1d', nm, 'POOL0', 'FULL', 'mean_spearman', float(np.mean(cors)) if cors else np.nan, 'ratio', len(cors), status='INFO')
        L(rows, 'D7', 'top_decile_overlap_vs_cvr_1d', nm, 'POOL0', 'FULL', 'mean_share', float(np.mean(ovl)) if ovl else np.nan, 'share', len(ovl), status='INFO')
    ta, tv = G['tail_amt'], G['tail_vol']
    with np.errstate(all='ignore'):
        tvw = np.asarray(ta) / np.asarray(tv)
    m = pool0 & np.isfinite(tvw) & np.isfinite(close)
    L(rows, 'D7', 'tail_vwap_above_close_share', 'BAR_APPROXIMATION_1430_1500', 'POOL0', 'FULL', 'share', float((tvw[m] > close[m]).mean()) if m.any() else np.nan, 'share',
      int(m.sum()), status='INFO')
    L(rows, 'D7', 'k_trigger_accounts', 'cvr_k', 'NONE', 'FULL', 'note', 'NOT_TESTED_AS_WRITTEN（本轮 cvr_k 只作测量列，无触发账户）', 'count', status='NOT_RUN')
    del rng


def composition_block(ctx, S, RD, rows):
    """D4：同金额 ISK vs 同金额全域并排（主母体 T1a / LEVEL 全部坐标；按段）；COUNT_ISK 口径复现。"""
    R = ctx.R
    ow = R[(R.role == 'ACCOUNT') & (R.form == O.MAIN_FORM) & (R.trigger.isin(['T1a', 'T1b_LEVEL'])) & (R.execution_profile == 'FEASIBLE_DAILY')]
    rmap = RD.set_index(['owner_exec_id', 'mechanism', 'segment'])
    for r in ow.itertuples(index=False):
        for s in SEG4 + ['FULL']:
            vals = {}
            for mech in ('AMOUNT_MATCH_V2', 'AMOUNT_ISK_V2', 'COUNT_ISK'):
                k = (r.exec_id, mech, s)
                if k in rmap.index:
                    x = rmap.loc[k]
                    vals[mech] = float(x.real_D_ann_pp - x.rand_mean_D_ann_pp)
                    L(rows, 'D4', 'real_minus_control', mech, r.exec_id, s, 'ann_pp', vals[mech], 'ann_pp', int(x.paths))
            if 'AMOUNT_MATCH_V2' in vals and 'AMOUNT_ISK_V2' in vals:
                L(rows, 'D4', 'cell_vs_global_same_amount', 'AMOUNT_ISK_V2_minus_AMOUNT_MATCH_V2_gap', r.exec_id, s, 'ann_pp', vals['AMOUNT_ISK_V2'] - vals['AMOUNT_MATCH_V2'],
                  'ann_pp', status='INFO')


def density_block(ctx, rows, e, h):
    """D4 两层 PIT 字段（主母体 HG10 × T1a / LEVEL × H5 / 20 / 40 NATIVE）：意向时同层（行业 × size）触发密度（剔除本股的 leave-one-security-out）、日 CVR clean 位置。"""
    ti, tf = ST.load_trades(ctx, h)
    z = np.load(ST.acct_file(ctx, h), allow_pickle=False)
    IN = z['IN_i']
    trig = IN[IN[:, E.IN_KIND] == E.KD_TRIG]
    if not len(trig):
        return
    lt = lots_table(ti, tf, ctx.d_end)
    iskid = G['iskid']
    cpct = G['cpct']
    tp = G['trig_panel'][ctx.reg.loc[e, 'trigger']]
    days = np.unique(trig[:, E.IN_DAY])
    dens_trig, dens_all, pct_trig = [], [], []
    starts = lt.e0.to_numpy()
    closes = np.where(lt.close_day.to_numpy() >= 0, lt.close_day.to_numpy(), ctx.d_end + 1)
    secs = lt.sec.to_numpy()
    for d in days[::3]:
        alive = (starts <= d) & (closes > d)
        held = np.unique(secs[alive])
        if len(held) < 5:
            continue
        cells = np.asarray(iskid[d, held])
        tr = np.asarray(tp[d, held]) == 1
        tsec = set(trig[trig[:, E.IN_DAY] == d][:, E.IN_SEC].tolist())
        for i, s in enumerate(held):
            c = cells[i]
            if c < 0:
                continue
            peers = (cells == c)
            peers[i] = False
            npeer = peers.sum()
            if npeer == 0:
                continue
            dsty = tr[peers].mean()
            if s in tsec:
                dens_trig.append(dsty)
                pct_trig.append(float(cpct[d, s]))
            dens_all.append(dsty)
    L(rows, 'D4', 'same_cell_trigger_density_LOSO', 'triggered_securities', e, 'FULL', 'mean', float(np.mean(dens_trig)) if dens_trig else np.nan, 'share', len(dens_trig),
      status='INFO')
    L(rows, 'D4', 'same_cell_trigger_density_LOSO', 'all_held_securities', e, 'FULL', 'mean', float(np.mean(dens_all)) if dens_all else np.nan, 'share', len(dens_all),
      status='INFO')
    L(rows, 'D4', 'clean_cvr_position_at_intent', 'triggered_securities', e, 'FULL', 'mean', float(np.nanmean(pct_trig)) if pct_trig else np.nan, 'share', len(pct_trig),
      status='INFO')


def mirror_table(ctx, S):
    R = ctx.R
    rows = []
    for r in R[R.role == 'MIRROR'].itertuples(index=False):
        o = R[(R.logical_id == r.owner_logical_id) & (R.execution_profile == r.execution_profile)].iloc[0]
        j, k = ctx.col[r.exec_id], ctx.col[o.exec_id]
        with np.errstate(all='ignore'):
            tgt = 1.0 - S['cash_abs'][:, k] / S['navc'][:, k]
            mir = 1.0 - S['cash_abs'][:, j] / S['navc'][:, j]
        tgt_l = np.r_[np.nan, tgt[:-1]]                 # T 收盘目标 → T+1 成交后比较
        gap = mir - tgt_l
        for s in SEG4 + ['FULL', 'G4']:
            if s == 'G4':
                continue
            m = ctx.masks[s] & np.isfinite(gap)
            n = int(m.sum())
            under = m & (gap < -0.005)
            over = m & (gap > 0.005)
            cash_short = under & (S['cash'][:, j] < 0.005)
            inv = over
            elig = under & ~cash_short
            rows.append(dict(owner_exec_id=o.exec_id, mirror_exec_id=r.exec_id, segment=s, target_exposure_mean=float(np.nanmean(tgt_l[m])) if n else np.nan,
                             mirror_exposure_mean=float(np.nanmean(mir[m])) if n else np.nan, under_share=under.sum() / n if n else np.nan, over_share=over.sum() / n if n else np.nan,
                             n_days_under=int(under.sum()), n_days_over=int(over.sum()), reason_cash=int(cash_short.sum()), reason_eligibility=int(elig.sum()),
                             reason_inventory=int(inv.sum()), status='COMPUTED', mean_abs_gap=float(np.nanmean(np.abs(gap[m]))) if n else np.nan))
        seg_rows = [x for x in rows[-5:] if x['segment'] in SEG4]
        if len(seg_rows) == 4:
            g4 = dict(seg_rows[0])
            g4['segment'] = 'G4'
            for c in ('target_exposure_mean', 'mirror_exposure_mean', 'under_share', 'over_share', 'mean_abs_gap'):
                g4[c] = float(np.median([x[c] for x in seg_rows]))
            for c in ('n_days_under', 'n_days_over', 'reason_cash', 'reason_eligibility', 'reason_inventory'):
                g4[c] = int(sum(x[c] for x in seg_rows))
            rows.append(g4)
    return pd.DataFrame(rows)


def recycle_local(ctx, acc):
    R = ctx.R
    D = pd.read_csv(O.P('registration', 'recycle_diagnostic_refs_E6p.csv'), keep_default_na=False, dtype=str)
    rows = []
    for x in D.itertuples(index=False):
        r = R[(R.logical_id == x.owner_logical_id) & (R.execution_profile == 'FEASIBLE_DAILY')].iloc[0]
        DY = acc[r.exec_id]['DY'][:ctx.d_end]
        bud = DY[:, E.DYI['rt_budget']]
        m = bud > 0
        n = int(m.sum())
        rows.append(dict(owner_exec_id=r.exec_id, date_count=n, budget_cny_mean=float(bud[m].mean()) if n else 0.0, cost_native=float(DY[m, E.DYI['rt_native']].sum()),
                         cost_cost0=float(DY[m, E.DYI['rt_cost0']].sum()), cost_costnet=float(DY[m, E.DYI['rt_costnet']].sum()),
                         unknown_share=float(DY[m, E.DYI['rt_unknown']].sum() / bud[m].sum()) if n else 0.0,
                         degenerate_share=float(DY[m, E.DYI['rt_degen']].sum() / bud[m].sum()) if n else 0.0,
                         status='COMPUTED' if n else 'NO_ACTION_OPPORTUNITY', kind=x.kind, deploy=r.deploy, trigger=r.trigger, H=int(r.H)))
    return pd.DataFrame(rows)


def local_four_fee(ctx, rows, e, h):
    """D9 局部四费用面板（T 已知快照：b = 常规净单、e = 信息早退卖、r = 额外买；同证券同日；A = 5 亿 κ .5 δ .5；φ_e + φ_r = C(b+e+r) − C(b)；LOCAL_ORDER_COST_ONLY）。"""
    ti, tf = ST.load_trades(ctx, h)
    if not len(ti):
        return
    z = np.load(ST.acct_file(ctx, h), allow_pickle=False)
    DY = z['DY'][:ctx.d_end]
    sg = np.where(ti[:, 5] == 0, 1.0, -1.0)
    k = ti[:, 4]
    comp = np.where((k == E.OK_EXIT) | (k == E.OK_RENEW), 'e', np.where(k == E.OK_EXTRA, 'r', 'b'))
    df = pd.DataFrame(dict(d=ti[:, 0], s=ti[:, 1], c=comp, v=sg * tf[:, 1]))
    pv = df.pivot_table(index=['d', 's'], columns='c', values='v', aggfunc='sum', fill_value=0.0)
    for c in ('b', 'e', 'r'):
        if c not in pv.columns:
            pv[c] = 0.0
    dd = pv.index.get_level_values(0).to_numpy()
    ss = pv.index.get_level_values(1).to_numpy()
    nav = DY[dd, E.DYI['nav_pre']]
    sig = np.asarray(G['sig20'][dd, ss])
    adv = np.asarray(G['adv20'][dd, ss])
    Ar = 5e8 * nav / O.V0
    with np.errstate(all='ignore'):
        a = 0.5 * sig * np.sqrt(0.01) / ((adv * 0.01 / Ar) ** 0.5)
    ok = np.isfinite(a) & (a > 0)
    b, e_, r_ = (pv[c].to_numpy() / nav for c in ('b', 'e', 'r'))
    C = lambda q: 4e-4 * np.abs(q) + a * np.abs(q) ** 1.5
    phi_e = 0.5 * ((C(b + e_) - C(b)) + (C(b + e_ + r_) - C(b + r_)))
    phi_r = 0.5 * ((C(b + r_) - C(b)) + (C(b + e_ + r_) - C(b + e_)))
    tot = C(b + e_ + r_) - C(b)
    nd = ctx.d_end
    L(rows, 'D9', 'LOCAL_phi_exit', 'A5yi_k.5_d.5', e, 'FULL', 'ann_pp', float(np.nansum(phi_e[ok]) / nd * O.ANN_PP), 'ann_pp', int(ok.sum()), status='LOCAL_ORDER_COST_ONLY')
    L(rows, 'D9', 'LOCAL_phi_recycle', 'A5yi_k.5_d.5', e, 'FULL', 'ann_pp', float(np.nansum(phi_r[ok]) / nd * O.ANN_PP), 'ann_pp', int(ok.sum()), status='LOCAL_ORDER_COST_ONLY')
    L(rows, 'D9', 'LOCAL_closure_maxabs', 'phi_e+phi_r-total', e, 'FULL', 'max_abs', float(np.nanmax(np.abs((phi_e + phi_r - tot)[ok]))) if ok.any() else np.nan, 'ratio',
      status='LOCAL_ORDER_COST_ONLY')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=['A2', 'B'], required=True)
    ap.add_argument('--root', default='')
    ap.add_argument('--fake_post', action='store_true')
    ap.add_argument('--workers', type=int, default=48)
    a = ap.parse_args()
    t0 = time.time()
    root = O.P(a.root) if a.root else O.work()
    if a.phase == 'B' and not os.path.exists(O.P('registration', 'seal_A2.json')):
        raise RuntimeError('seal_A2 不在：拒绝后段诊断')
    ctx = ST.Ctx(a.phase, a.fake_post, root)
    S, acc = ST.load_all(ctx)
    AS = pd.read_csv(os.path.join(root, 'statistics', 'account_summary_E6p.csv'), keep_default_na=False, na_values=[''])
    RD = pd.read_csv(os.path.join(root, 'statistics', 'randoms_E6p.csv'), keep_default_na=False, na_values=[''])
    cd = ctx.cd
    P = lambda k: np.load(os.path.join(cd, 'panels', k + '.npy'), mmap_mode='r')
    MI = lambda k: np.load(os.path.join(O.e6o_cache(), 'minute', k + '.npy'), mmap_mode='r')
    G.update(ctx=ctx, adv20=P('adv20'), sig20=P('sig20'), pv=P('pv_ff'), pc=P('pc_ff'), vwap_raw=P('vwap_raw'), open_raw=P('open_raw'), iskid=P('iskid'), cpct=P('cvr_pct'),
             isopen=P('is_open'), all_amt=MI('all_amt'), tail_amt=MI('tail_amt'), tail_vol=MI('tail_vol'))
    b = np.nan_to_num(ctx.bench)
    G['cumbench'] = np.cumprod(1.0 + b)
    import e6p_acct as A
    mk_nat = A.Market().natural(O.MAIN_FORM)
    G['nat'] = mk_nat
    G['trig_panel'] = {t: np.load(os.path.join(cd, 'triggers', t + '.npy'), mmap_mode='r') for t in ('T1a', 'T1b_LEVEL')}
    R = ctx.R
    SEL = sel_accounts(R)
    lmset = set(SEL[(SEL.H.isin(['20', '40'])) & (SEL.trigger.isin(['T1a', 'T1b_LEVEL', 'NONE']))].exec_id)
    G['landmark'] = lmset
    rows = []
    jobs = [(e, ctx.reg.loc[e, 'exec_hash']) for e in SEL.exec_id]
    lm = []
    ctxp = get_context('fork')
    with ctxp.Pool(min(a.workers, len(jobs))) as pool:
        for res in pool.imap_unordered(job_tl, jobs):
            if res['status'] != 'OK':
                print(res, flush=True)
                raise RuntimeError('TL 诊断失败 %s' % res.get('err'))
            rows += res['rows']
            lm += res['lm']
    O.log('TL 级诊断 %d 个对象（%.0f s）' % (len(jobs), time.time() - t0))
    deploy_block(ctx, S, AS, rows)
    regime_block(ctx, S, rows)
    cvr_block(ctx, rows)
    composition_block(ctx, S, RD, rows)
    for r in SEL[(SEL.trigger.isin(['T1a', 'T1b_LEVEL'])) & (SEL.deploy == 'NATIVE') & (SEL.renew == '0')].itertuples(index=False):
        density_block(ctx, rows, r.exec_id, r.exec_hash)
    main = R[(R.is_main_object == '1') & (R.execution_profile == 'FEASIBLE_DAILY')]
    h5 = R[(R.form == O.MAIN_FORM) & (R.memory == 'HG10') & (R.H == '5') & (R.trigger.isin(['T1a', 'T1b_LEVEL'])) & (R.deploy.isin(['NATIVE', 'CASH_REMAIN']))
           & (R.renew == '0') & (R.cap == 'SOURCE') & (R.execution_profile == 'FEASIBLE_DAILY')]
    for r in pd.concat([main, h5]).itertuples(index=False):
        local_four_fee(ctx, rows, r.exec_id, r.exec_hash)
    L(rows, 'D9', 'KAPPA_STATUS', 'kappa', 'ALL', 'FULL', 'status', 'SCENARIO_NOT_CALIBRATED', 'count', status='SCENARIO_NOT_CALIBRATED',
      q='QRY-D9-KAPPA')
    D = pd.DataFrame(rows, columns=LCOLS)
    names = {'D1': 'D1_holding', 'D2': 'D2_deploy', 'D3': 'D3_cost', 'D4': 'D4_composition', 'D5': 'D5_reinvest', 'D6': 'D6_regime', 'D7': 'D7_cvr', 'D8': 'D8_window',
             'D9': 'D9_discount'}
    for blk, nm in names.items():
        x = D[D.block == blk]
        if not len(x):
            x = pd.DataFrame([dict(block=blk, item='none', key1='', key2='', segment='FULL', stat='', value='', unit='count', n=0, status='NOT_APPLICABLE', query_id='')])
        ST.write(ctx, 'diagnostics/%s_E6p.csv' % nm, x[LCOLS])
    LMt = pd.DataFrame(lm)
    if not len(LMt):
        LMt = pd.DataFrame([dict(exec_id='', landmark_age=1, state='NOT_TRIGGERED', q=1, weighting='EQUAL', n=0, status='NOT_APPLICABLE')])
    for c in ('exec_id', 'landmark_age', 'state', 'q', 'weighting', 'n', 'mean_fwd_excess_bp', 'lo', 'hi', 'status'):
        if c not in LMt.columns:
            LMt[c] = np.nan
    ST.write(ctx, 'diagnostics/landmark_E6p.csv', LMt)
    ST.write(ctx, 'diagnostics/mirror_E6p.csv', mirror_table(ctx, S))
    ST.write(ctx, 'diagnostics/D9_recycle_local_E6p.csv', recycle_local(ctx, acc))
    print(json.dumps(dict(rows=len(D), landmark=len(LMt), wall_s=round(time.time() - t0, 1)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
