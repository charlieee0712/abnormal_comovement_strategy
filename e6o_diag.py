# -*- coding: utf-8 -*-
"""E6o D-1…D-6 有界诊断（plan §10；附录 B.16 长格式：block, item, key1, key2, segment, stat, value, unit, n, status, query_id）。只读已生成账户 / 源 / 面板；不新增经济账户。
  D-1 剂量 × size：E6n 已暴露 α .125 / .25 / .5 源账户（主母体三记忆 H5）的段 net 与目标 size；α .5 / .125 相对 α .25 的 增 / 减 / 共同 名单 size 与 5 日前向超额（不插值、不分摊）
  D-2 日龄 / 权重：主对象早退事件日龄（资本加权）、证券连续持有日龄、批次日龄；FROZEN_TARGET_DIAGNOSTIC（源目标按批次年龄倾斜 δ = .25 / .5，成本按换手重算）
  D-3 成本 / 容量：κ = .5 / 1 × A = 1 / 5 / 10 / 20 / 50 亿元 的冻结路径冲击后 D；净订单 / ADV 参与率分位（日线预测）与 净订单 / 当日实际成交额（实际）分开
  D-4 近段读法：固定窗口 W1 = 2024、W2 = 2025-01…2026-03；逐年 D；市场状态（基准日收益符号 / 前 20 日基准波动三分位，PIT）分解（固定总体日数，分量和 = FULL）
  D-5 入场否决 × 退出四账户：Y00 / Y01 / Y10 / Y11 = (A4b, A4b_CVRv5) × (无退出, 有退出)；Δ_no_veto、Δ_veto、交互；R_both / R_only_bare / R_only_veto 名单份额
  D-6 分钟 K 活动分布：E6n 分钟面板已注册数组（时段量份额 vb1 / vb8）在 pool0 与持仓风险集的分布与 H5 / H20 前向超额（2013-08 起）；不新增入场账户
用法：python3 e6o_diag.py"""
import os
import sys
import json
import time

import numpy as np
import pandas as pd

import e6o_core as O
import e6o_engine as E
import e6o_acct as A

ROWS = {}


def put(block, item, key1, key2, segment, stat, value, unit, n, status='COMPUTED', q=''):
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        value, status = np.nan, 'UNKNOWN' if status == 'COMPUTED' else status
    ROWS.setdefault(block, []).append(dict(block=block, item=item, key1=key1, key2=key2, segment=segment, stat=stat, value=value, unit=unit, n=n,
                                           status=status, query_id=q or ('%s-%s' % (block, item))))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--stats_root', default='', help='测试用：从该目录读 statistics/（默认结果目录）')
    ap.add_argument('--out', default='', help='测试用：输出目录（默认 diagnostics/）')
    cli = ap.parse_args()
    sroot = cli.stats_root or O.work()
    t0 = time.time()
    mk = A.Market()
    T = mk.T
    cd = mk.cd
    dates = mk.dates
    segi = np.array([O.seg_of_date(d) for d in dates])
    L = lambda k: np.load(os.path.join(cd, 'panels', k + '.npy'), mmap_mode='r')
    R = pd.read_csv(O.P('registration', 'registry_E6o.csv'), keep_default_na=False, na_values=[''])
    reg = R.set_index('exec_id')
    AS = pd.read_csv(os.path.join(sroot, 'statistics', 'account_summary_E6o.csv'), keep_default_na=False, na_values=[''])
    asi = AS.set_index(['exec_id', 'segment'])
    YR = pd.read_csv(os.path.join(sroot, 'statistics', 'yearly_D_E6o.csv'), keep_default_na=False, na_values=[''])
    rv = np.asarray(L('r_vwap'))
    bench = mk.bench
    ex = np.where(np.isfinite(rv), rv - bench[:, None], 0.0)
    ex = np.where(np.isfinite(ex), ex, 0.0)
    cs = np.vstack([np.zeros((1, ex.shape[1])), np.cumsum(ex, axis=0)])
    fwd = lambda d, c, k: np.where(d + 2 + k <= T, cs[np.minimum(d + 2 + k, T), c] - cs[np.minimum(d + 2, T), c], np.nan)
    z = np.asarray(L('zsize'))
    main_id = R[(R.series == 'C_ACCOUNT') & (R.is_main_object == 1) & (R.execution_profile == 'FEASIBLE_DAILY')].exec_id.iloc[0]

    def acct(e):
        h = reg.loc[e, 'exec_hash']
        return np.load(O.P('accounts_run', 'full', h[:2], '%s.npz' % h), allow_pickle=False)

    # ---------------- D-1
    for mem in O.MEMS:
        for s in O.SEGS:
            a = np.load(O.E6N('accounts', s, '%s.npz' % O.MAIN_FORM), allow_pickle=False)
            desc = [str(x) for x in a['desc']]
            tg = a['desc_target']
            for al in ('0.125', '0.25', '0.5'):
                did = 'ANCHOR|Q0|%s|%s|H5|s0|ALL|a%s|f5|d+1' % (O.MAIN_FORM, mem, al)
                if did not in desc:
                    put('D1', 'alpha%s|%s' % (al, mem), 'SOURCE_ACCOUNT', 'net8', s, 'net_ann_pp', np.nan, 'ann_pp', 0, 'NOT_APPLICABLE')
                    continue
                i = desc.index(did)
                put('D1', 'alpha%s|%s' % (al, mem), 'SOURCE_ACCOUNT', 'net8', s, 'net_ann_pp', float(np.nanmean(a['d_net8'][i]) * O.ANN_PP), 'ann_pp',
                    int(np.isfinite(a['d_net8'][i]).sum()))
                zt = a['t_zT_mean'][tg[i]]
                put('D1', 'alpha%s|%s' % (al, mem), 'SOURCE_TARGET', 'zT_mean', s, 'mean', float(np.nanmean(zt)), 'ratio', int(np.isfinite(zt).sum()))
                put('D1', 'alpha%s|%s' % (al, mem), 'SOURCE_TARGET', 'small30', s, 'mean', float(np.nanmean(a['t_small30'][tg[i]])), 'ratio', int(np.isfinite(zt).sum()))
        # 增 / 减 / 共同（名单层，等权；α .25 为基准）
        for s in O.SEGS:
            zm = np.load(O.E6N('masks', s, '%s.npz' % O.MAIN_FORM), allow_pickle=False)
            keys = [str(k) for k in zm['mask_keys']]
            src = mk.source(s)
            ct, cc = src['cell_t'], src['cell_c']
            dd = np.array([mk.di[d] for d in src['dates']])
            cols = np.array([mk.cj[c] for c in src['codes']])
            n = int(zm['n_cells'][0])
            base = np.unpackbits(zm['final_bits'][keys.index('%s|a0.25|Q0' % mem)])[:n].astype(bool)
            for al in ('0.125', '0.5'):
                k = '%s|a%s|Q0' % (mem, al)
                if k not in keys:
                    continue
                F = np.unpackbits(zm['final_bits'][keys.index(k)])[:n].astype(bool)
                for grp, m in (('ADDED', F & ~base), ('DROPPED', base & ~F), ('COMMON', F & base)):
                    t_, c_ = dd[ct[m]], cols[cc[m]]
                    r5 = fwd(t_, c_, 5)
                    ok = np.isfinite(r5)
                    put('D1', 'alpha%s_vs_0.25|%s' % (al, mem), grp, 'fwd5', s, 'mean_bp', float(np.mean(r5[ok]) * 1e4) if ok.any() else np.nan, 'bp', int(ok.sum()))
                    zz = z[t_, c_]
                    put('D1', 'alpha%s_vs_0.25|%s' % (al, mem), grp, 'zsize', s, 'mean', float(np.nanmean(zz)) if np.isfinite(zz).any() else np.nan, 'ratio', int(np.isfinite(zz).sum()))
    put('D1', 'idempotence', 'NOTE', 'Q0_size_neutralized', 'FULL', 'flag', 1.0, 'count', 0, 'INFO')
    # ---------------- D-2
    am = acct(main_id)
    IN_i, IN_f = am['IN_i'], am['IN_f']
    real = IN_i[:, E.IN_STATUS] != 9
    for a_ in range(5):
        m = real & (IN_i[:, E.IN_LAYER] == a_)
        for s in O.SEGS:
            ms = m & (segi[np.clip(IN_i[:, E.IN_DAY], 0, T - 1)] == s)
            put('D2', 'event_age|main', 'LOT_AGE', str(a_), s, 'capital_share', float(IN_f[ms, 0].sum() / max(IN_f[real & (segi[np.clip(IN_i[:, E.IN_DAY], 0, T - 1)] == s), 0].sum(), 1e-12)),
                'ratio', int(ms.sum()))
    hh = am['HOLDH']
    for k in range(len(hh)):
        if hh[k] > 0:
            put('D2', 'realized_hold_days|main', 'HOLD_DAYS', str(k), 'FULL', 'count', float(hh[k]), 'count', int(hh[k]))
    # 证券连续持有日龄（主对象带成交日志重跑）
    import e6o_run as RU
    RU.setup()
    P = RU.plan().set_index('exec_id', drop=False)
    acc = RU.make_account(P.loc[main_id].to_dict())
    acc.ip[E.IP_TLOG] = 1
    acc.TL_i = np.zeros((1 << 22, 2), np.int64)
    acc.TL_f = np.zeros((1 << 22, 4))
    acc.run(0, T)
    n = int(acc.S_i[E.SI_NTL])
    TLi, TLf = acc.TL_i[:n], acc.TL_f[:n]
    qpos = {}
    since = {}
    cont_age = []
    held_since = np.full(mk.N, -1, np.int64)
    by_day = {}
    for k in range(n):
        by_day.setdefault(int(TLi[k, 0]), []).append(k)
    intents_by_day = {}
    for i in np.flatnonzero(real):
        intents_by_day.setdefault(int(IN_i[i, E.IN_DAY]), []).append(i)
    for d in range(T):
        for k in by_day.get(d, []):
            s = int(TLi[k, 1])
            q0 = qpos.get(s, 0.0)
            q1 = q0 - TLf[k, 0] + TLf[k, 1]
            if q0 <= 1e-12 < q1:
                held_since[s] = d
            if q1 <= 1e-12:
                held_since[s] = -1
            qpos[s] = q1
        for i in intents_by_day.get(d, []):
            s = int(IN_i[i, E.IN_SEC])
            if held_since[s] >= 0:
                cont_age.append((d, d - held_since[s], float(IN_f[i, 0])))
    CA = pd.DataFrame(cont_age, columns=['d', 'age', 'val'])
    if len(CA):
        CA['seg'] = segi[CA.d.to_numpy()]
        CA['bucket'] = pd.cut(CA.age, [-1, 4, 9, 19, 59, 10 ** 6], labels=['0-4', '5-9', '10-19', '20-59', '60+']).astype(str)
        for (s, b), g in CA.groupby(['seg', 'bucket']):
            put('D2', 'security_continuous_age|main', 'AGE_BUCKET', b, s, 'capital_share', float(g.val.sum() / CA[CA.seg == s].val.sum()), 'ratio', len(g))
    # FROZEN_TARGET_DIAGNOSTIC：源目标按批次年龄倾斜
    ptr, colf, w = mk.formation(O.MAIN_FORM, 'HG10')
    H = 5
    f_day = np.repeat(np.arange(T), np.diff(ptr))
    r0 = np.where(np.isfinite(rv), rv, 0.0)
    for delta in (0.0, 0.25, 0.5):
        mfac = 1.0 + delta * ((H - 1) / 2.0 - np.arange(H)) / ((H - 1) / 2.0)
        port = np.zeros(T)
        pos = np.zeros(T)
        act_prev = {}
        turn = np.zeros(T)
        acts = [dict() for _ in range(T)]
        for k_ in range(H):
            tt = f_day + 2 + k_
            okk = tt < T
            np.add.at(port, tt[okk], w[okk] * mfac[k_] / H * r0[tt[okk], colf[okk]])
            np.add.at(pos, tt[okk], w[okk] * mfac[k_] / H)
        # 换手：act_t(i) = Σ_k m_k w_{t−2−k}(i) / H；½Σ|Δact|
        W = pd.DataFrame(dict(t=f_day, c=colf, w=w))
        frames = []
        for k_ in range(H):
            frames.append(pd.DataFrame(dict(t=W.t + 2 + k_, c=W.c, a=W.w * mfac[k_] / H)))
        AC = pd.concat(frames).groupby(['t', 'c']).a.sum()
        ACu = AC.unstack(fill_value=0.0)
        ACu = ACu.reindex(range(T + 7), fill_value=0.0)
        dif = ACu.diff().abs().sum(axis=1).to_numpy()[:T]
        turn[:] = 0.5 * dif
        gross = port - bench * pos
        net = np.where(np.isfinite(gross), gross - turn * 8e-4, np.nan)
        for s in O.SEGS:
            m = segi == s
            put('D2', 'FROZEN_TARGET_DIAGNOSTIC|delta%.2f' % delta, 'AGE_TILT', 'young_up', s, 'net_ann_pp', float(np.nanmean(net[m]) * O.ANN_PP), 'ann_pp', int(m.sum()), 'INFO')
            put('D2', 'FROZEN_TARGET_DIAGNOSTIC|delta%.2f' % delta, 'AGE_TILT', 'young_up', s, 'turnover_ann', float(np.nanmean(turn[m]) * 252), 'ratio', int(m.sum()), 'INFO')
    # ---------------- D-3
    targets = list(R[(R.series == 'C_ACCOUNT') & (R.is_primary72 == 1)].exec_id) + [reg.loc[main_id, 'parent_exec_id']]
    for e in targets:
        DY = acct(e)['DY']
        br = DY[:, E.DYI['impact_br']]
        ne = DY[:, E.DYI['net_excess']]
        for kappa in (0.5, 1.0):
            for Acny in (1e8, 5e8, 1e9, 2e9, 5e9):
                cost = kappa * np.sqrt(Acny) * br
                for s in O.SEGS:
                    m = segi == s
                    put('D3', 'impact|%s' % reg.loc[e, 'exec_hash'], 'kappa%.1f' % kappa, 'A%.0e' % Acny, s, 'cost_ann_pp', float(np.nanmean(cost[m]) * O.ANN_PP), 'ann_pp', int(m.sum()),
                        q='D3-impact')
    # 参与率（主对象；A = 5 亿）
    navp = acc.DY[:, E.DYI['nav_post']]
    adv = np.asarray(L('adv20'))
    amt = np.asarray(L('amt'))
    netv = np.abs(TLf[:, 1] - TLf[:, 0]) * TLf[:, 2]
    dd_ = TLi[:, 0]
    ss_ = TLi[:, 1]
    frac = netv / navp[dd_]
    for Acny in (5e8, 1e9, 5e9):
        part_pred = frac * Acny / adv[dd_, ss_]
        part_act = frac * Acny / amt[dd_, ss_]
        for nm, x in (('net_order_over_ADV20', part_pred), ('net_order_over_day_amount', part_act)):
            ok = np.isfinite(x) & (frac > 0)
            for qq in (0.5, 0.9, 0.99):
                put('D3', 'participation|main', nm, 'A%.0e' % Acny, 'FULL', 'q%02d' % int(qq * 100), float(np.quantile(x[ok], qq)) if ok.any() else np.nan, 'ratio', int(ok.sum()),
                    q='D3-participation')
    # ---------------- D-4
    w1 = (dates >= '2024-01-01') & (dates <= '2024-12-31')
    w2 = dates >= '2025-01-01'
    br20 = pd.Series(bench).shift(1).rolling(20, min_periods=10).std().to_numpy()
    terc = pd.qcut(pd.Series(br20).rank(method='first'), 3, labels=False).to_numpy()
    up = np.where(np.isfinite(bench), bench > 0, False)
    for e in R[(R.series == 'C_ACCOUNT') & (R.is_primary72 == 1) & (R.form == O.MAIN_FORM)].exec_id:
        DY = acct(e)['DY']
        pa = acct(reg.loc[e, 'parent_exec_id'])['DY']
        dfz = DY[:, E.DYI['net_excess']] - pa[:, E.DYI['net_excess']]
        h = reg.loc[e, 'exec_hash']
        for wn, wm in (('W1_2024', w1), ('W2_2025_2026Q1', w2)):
            put('D4', 'window|%s' % h, 'WINDOW', wn, 'FULL', 'D_ann_pp', float(np.nanmean(dfz[wm]) * O.ANN_PP), 'ann_pp', int(wm.sum()), q='D4-window')
        tot = np.isfinite(dfz)
        for st_name, st_mask in (('BENCH_UP', up), ('BENCH_DOWN', ~up), ('VOL_T1', terc == 0), ('VOL_T2', terc == 1), ('VOL_T3', terc == 2),
                                 ('VOL_NA_WARMUP', ~np.isin(terc, [0, 1, 2]))):
            m = tot & st_mask
            put('D4', 'state|%s' % h, 'STATE', st_name, 'FULL', 'contrib_ann_pp', float(np.nansum(dfz[m]) / tot.sum() * O.ANN_PP), 'ann_pp', int(m.sum()), q='D4-state')
        y = YR[YR.exec_id == e]
        for r in y.itertuples():
            put('D4', 'yearly|%s' % h, 'YEAR', str(r.year), 'FULL', 'D_ann_pp', r.D_ann_pp, 'ann_pp', r.n_days, q='D4-yearly')
    # ---------------- D-5
    def find(form, mem, trig, fund='ENGINE_NATIVE', re_='ALLOW', prof='FEASIBLE_DAILY'):
        m = R[(R.series == 'C_ACCOUNT') & (R.form == form) & (R.memory == mem) & (R.H == 'H5') & (R.trigger == trig) & (R.funding == fund) & (R.reentry == re_)
              & (R.execution_profile == prof) & (R.family == 'CORE')]
        return m.exec_id.iloc[0] if len(m) else None
    for mem in O.MEMS:
        for trig in ('T1a', 'T1b', 'T3c15_X', 'T4a'):
            y01 = find('A4b', mem, trig)
            y11 = find(O.MAIN_FORM, mem, trig)
            if not (y01 and y11):
                continue
            for s in O.SEGS + ('FULL',):
                try:
                    d_nv = float(asi.loc[(y01, s), 'D_ann_pp'])
                    d_v = float(asi.loc[(y11, s), 'D_ann_pp'])
                except KeyError:
                    continue
                put('D5', 'veto_x_exit|%s|%s' % (trig, mem), 'DELTA', 'no_veto', s, 'D_ann_pp', d_nv, 'ann_pp', 0, q='D5-veto')
                put('D5', 'veto_x_exit|%s|%s' % (trig, mem), 'DELTA', 'veto', s, 'D_ann_pp', d_v, 'ann_pp', 0, q='D5-veto')
                put('D5', 'veto_x_exit|%s|%s' % (trig, mem), 'DELTA', 'interaction', s, 'D_ann_pp', d_v - d_nv, 'ann_pp', 0, q='D5-veto')
    for mem in O.MEMS:
        pa, ca, wa = mk.formation('A4b', mem)
        pv_, cv_, wv_ = mk.formation(O.MAIN_FORM, mem)
        for s in O.SEGS:
            nb = nvv = nboth = 0
            for d in np.flatnonzero(segi == s):
                A_ = set(ca[pa[d]:pa[d + 1]])
                V_ = set(cv_[pv_[d]:pv_[d + 1]])
                nboth += len(A_ & V_)
                nb += len(A_ - V_)
                nvv += len(V_ - A_)
            tot = max(nboth + nb + nvv, 1)
            for nm, v in (('R_both', nboth), ('R_only_bare', nb), ('R_only_veto', nvv)):
                put('D5', 'riskset|%s' % mem, 'FORMATION_NAMES', nm, s, 'share', v / tot, 'ratio', tot, q='D5-riskset')
    # ---------------- D-6
    md = O.E6N('minute_panel')
    pdir = os.path.join(md, sorted(x for x in os.listdir(md) if x.startswith('cache_'))[0])
    pool0 = np.asarray(np.load(os.path.join(cd, 'triggers', 'pool0.npy'), mmap_mode='r'))
    tail_share = np.full((T, mk.N), np.nan)
    morn_share = np.full((T, mk.N), np.nan)
    c6 = {}
    for j_, c_ in enumerate(mk.codes):
        k6 = ''.join(ch for ch in str(c_) if ch.isdigit())[:6]
        c6[k6] = -2 if k6 in c6 else j_                                     # 6 位数字码重名 → 不用
    def day_ix(x):
        s_ = str(x).replace('-', '')[:8]
        return mk.di.get('%s-%s-%s' % (s_[:4], s_[4:6], s_[6:8]), -1)
    def code_ix(c):
        j_ = mk.cj.get(str(c), -1)
        if j_ < 0:
            j_ = c6.get(''.join(ch for ch in str(c) if ch.isdigit())[:6], -1)
        return j_ if j_ >= 0 else -1
    map_facts = []
    for yd in sorted(x for x in os.listdir(pdir) if x.startswith('Y')):
        pdts = np.load(os.path.join(pdir, yd, 'dates.npy'))
        pcs = np.load(os.path.join(pdir, yd, 'codes.npy'))
        rr = np.array([day_ix(x) for x in pdts])
        jj = np.array([code_ix(c) for c in pcs])
        map_facts.append((yd, float((rr >= 0).mean()), float((jj >= 0).mean())))
        okr, okc = rr >= 0, jj >= 0
        vm = np.load(os.path.join(pdir, yd, 'vol_min.npy'))
        with np.errstate(all='ignore'):
            v8 = np.load(os.path.join(pdir, yd, 'vb8.npy')) / vm
            v1 = np.load(os.path.join(pdir, yd, 'vb1.npy')) / vm
        tail_share[np.ix_(rr[okr], jj[okc])] = v8[np.ix_(okr, okc)]
        morn_share[np.ix_(rr[okr], jj[okc])] = v1[np.ix_(okr, okc)]
    for yd, fr_d, fr_c in map_facts:
        put('D6', 'mapping|%s' % yd, 'MINUTE_PANEL', 'date_code_match', 'FULL', 'share_dates', fr_d, 'ratio', 0, 'INFO', q='D6-mapping')
        put('D6', 'mapping|%s' % yd, 'MINUTE_PANEL', 'date_code_match', 'FULL', 'share_codes', fr_c, 'ratio', 0, 'INFO', q='D6-mapping')
    hold = np.zeros((T, mk.N), bool)
    for k_ in range(5):
        tt = f_day + 1 + k_
        okk = tt < T
        hold[tt[okk], colf[okk]] = True
    for dom, M in (('POOL0', pool0), ('HOLDING_MAIN_PARENT', hold)):
        dd2, cc2 = np.nonzero(M & np.isfinite(tail_share))
        for nm, X in (('tail_vol_share', tail_share), ('morning_vol_share', morn_share)):
            x = X[dd2, cc2]
            for kk, lab in ((5, 'H5'), (20, 'H20')):
                f_ = fwd(dd2, cc2, kk)
                ok = np.isfinite(x) & np.isfinite(f_)
                if ok.sum() < 100:
                    continue
                q = pd.qcut(pd.Series(x[ok]).rank(method='first'), 5, labels=False).to_numpy()
                sg = segi[dd2[ok]]
                for s in ('2010-2014', '2015-2018', '2019-2023', '2024-2026'):
                    for qi in range(5):
                        m = (q == qi) & (sg == s)
                        if m.sum() < 30:
                            continue
                        put('D6', '%s|%s' % (nm, dom), 'QUINTILE', 'q%d' % (qi + 1), s, 'fwd_%s_mean_bp' % lab, float(np.mean(f_[ok][m]) * 1e4), 'bp', int(m.sum()), q='D6-%s' % nm)
    od = cli.out or O.P('diagnostics')
    names = {'D1': 'D1_size_dose_E6o', 'D2': 'D2_age_weight_E6o', 'D3': 'D3_capacity_E6o', 'D4': 'D4_regime_E6o', 'D5': 'D5_veto_exit_E6o', 'D6': 'D6_minute_kleg_E6o'}
    for b, nm in names.items():
        df = pd.DataFrame(ROWS.get(b, []), columns=['block', 'item', 'key1', 'key2', 'segment', 'stat', 'value', 'unit', 'n', 'status', 'query_id'])
        if not len(df):
            df = pd.DataFrame([dict(block=b, item='none', key1='', key2='', segment='FULL', stat='n', value=0.0, unit='count', n=0, status='NOT_APPLICABLE', query_id=b)])
        O.atomic_write_csv(os.path.join(od, nm + '.csv'), df)
    print(json.dumps({b: len(v) for b, v in ROWS.items()}, ensure_ascii=False), 'wall %.0f s' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
