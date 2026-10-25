# -*- coding: utf-8 -*-
"""E6o 手工逐日账（plan §15.2 "CC 现场额外必做"；他算 = 不经引擎的独立重算）：推导段内对 5 个真实账户开逐笔成交日志重跑，
① 会计层：只用 成交日志（证券 × 日的卖量 / 买量 / 成交价）+ 后复权 VWAP 面板 + 基准，从 V0 起逐日独立重算 现金 / V⁻ / 费用 / V⁺ / R_net / 敞口 / 净超额，
   与引擎日序列逐日比（容差 1e−9 相对 V0）；
② 决策层三类真实片段：(i) 普通早退：每条早退意向在 T+1 起首个"开盘且可卖"日成交（FEASIBLE）；(ii) 卖出受限：延后天数全部落在不可卖日；
   (iii) 同证券跨批（ALLOW 重入 / 同日内部转移）：买入只来自 T 收盘已知名单（形成名单 / NEXT 序），同日同证券买卖只按净额收费；
   BLOCK：早退意向次日不得买回同证券。③ 标签 / 锁定守恒（逐日：余额 = 昨余 + 新建 − 常规耗 − 额外耗 − 到期重分类）。
④ 存档的 A2 日序列与带日志重跑逐位相同（日志开关不改计算）。输出 verify/refcheck_E6o.csv。用法：python3 e6o_refcheck.py"""
import os
import sys
import json
import time

import numpy as np
import pandas as pd

import e6o_core as O
import e6o_engine as E
import e6o_acct as A
import e6o_run as RU


def main():
    t0 = time.time()
    RU.setup()
    mk = RU.G['mk']
    T = mk.T
    d19 = RU.d19()
    P = RU.plan().set_index('exec_id', drop=False)
    main_id = P[(P.form == O.MAIN_FORM) & (P.memory == 'HG10') & (P.H == 5) & (P.trigger == 'T1b') & (P.fund == 'NATIVE') & (P.reentry == 'ALLOW')
                & (P.lag == 1) & (P.maturity == 0) & (P.family == 'CORE') & (P.ideal == 0)].exec_id.iloc[0]
    pick = {'MAIN_NATIVE_ALLOW_FEAS': main_id,
            'NATIVE_BLOCK_FEAS': main_id.replace('|ALLOW|', '|BLOCK|'),
            'CASH_ALLOW_FEAS': main_id.replace('|ENGINE_NATIVE|lag1|RESET_H|', '|CASH|NA|NA|'),
            'NEXT_ALLOW_FEAS': main_id.replace('|ENGINE_NATIVE|', '|NEXT_RANK|'),
            'MAIN_NATIVE_ALLOW_IDEAL': main_id.replace('|FEASIBLE_DAILY|', '|IDEALIZED_SOURCE_FILL|')}
    pv = np.asarray(mk.pv)
    sell_ok = np.asarray(mk.sellable) & np.asarray(mk.isopen)
    rows = []
    for tag, eid in pick.items():
        p = P.loc[eid].to_dict()
        acc = RU.make_account(p)
        acc.ip[E.IP_TLOG] = 1
        acc.TL_i = np.zeros((1 << 21, 2), np.int64)
        acc.TL_f = np.zeros((1 << 21, 4))
        acc.run(0, d19)
        n = int(acc.S_i[E.SI_NTL])
        TLi, TLf = acc.TL_i[:n], acc.TL_f[:n]
        DY = acc.DY[:d19]
        # ④ 与存档 A2 日序列
        z = np.load(RU.acct_path('A2', p['exec_hash']), allow_pickle=False)
        arch = z['DY'][:d19, :DY.shape[1]]
        d_arch = float(np.nanmax(np.abs(arch - DY)))
        # ① 独立会计重算
        q = {}
        cash = 1e8
        Vprev = 1e8
        xprev = 0.0
        by_day = {}
        for k in range(n):
            by_day.setdefault(int(TLi[k, 0]), []).append(k)
        diff = dict(nav_pre=0.0, fee=0.0, nav_post=0.0, net_excess=0.0, exposure=0.0, cash=0.0)
        for d in range(d19):
            Vpre = cash + sum(qq * pv[d, s] for s, qq in q.items() if qq != 0.0)
            fee = 0.0
            for k in by_day.get(d, []):
                s = int(TLi[k, 1])
                sq, bq, px = TLf[k, 0], TLf[k, 1], TLf[k, 2]
                if abs(px - pv[d, s]) > 1e-12 * max(1.0, px):
                    diff['price_mismatch'] = diff.get('price_mismatch', 0) + 1
                cash += sq * px - bq * px
                fee += 4e-4 * abs(bq - sq) * px
                q[s] = q.get(s, 0.0) - sq + bq
            cash -= fee
            Vpost = Vpre - fee
            r = Vpost / Vprev - 1.0
            b = mk.bench[d]
            nex = r - xprev * b if np.isfinite(b) else (r if xprev == 0.0 else np.nan)
            hv = sum(qq * pv[d, s] for s, qq in q.items() if qq > 1e-15)
            x = hv / Vpost
            for k_, v_ in (('nav_pre', Vpre), ('fee', fee), ('nav_post', Vpost), ('exposure', x)):
                ref = DY[d, E.DYI[k_]]
                diff[k_] = max(diff[k_], abs(v_ - ref) / (1e8 if k_ != 'exposure' else 1.0))
            if np.isfinite(nex):
                diff['net_excess'] = max(diff['net_excess'], abs(nex - DY[d, E.DYI['net_excess']]))
            diff['cash'] = max(diff['cash'], abs(cash - DY[d, E.DYI['cash_share']] * DY[d, E.DYI['nav_post']]) / 1e8)
            Vprev = Vpost
            xprev = x
        # ② 决策层
        IN_i = acc.IN_i[:int(acc.S_i[E.SI_NIN])]
        st = IN_i[:, E.IN_STATUS]
        exe = IN_i[:, E.IN_EXEC]
        dd = IN_i[:, E.IN_DAY]
        ss = IN_i[:, E.IN_SEC]
        viol_first = 0
        delayed = 0
        delay_days_unsellable_ok = 0
        is_ideal = int(p['ideal']) == 1
        for i in np.flatnonzero((st == 1) | (st == 2)):
            t1 = dd[i] + 1
            e = exe[i]
            if e < t1:
                viol_first += 1
                continue
            if e > t1:
                delayed += 1
                if is_ideal:
                    viol_first += 1
                elif not sell_ok[t1:e, ss[i]].any():
                    delay_days_unsellable_ok += 1
            elif not is_ideal and not sell_ok[e, ss[i]]:
                pass                                              # 当日只内部转移成交（净额为 0）亦合法
        f_ptr, f_col, _ = RU.G['f'][(p['form'], p['memory'])]
        n_ptr, n_col = RU.G['n'][p['memory']]
        bad_buy = 0
        nbuy = 0
        for k in range(n):
            if TLf[k, 1] > 0.0:
                nbuy += 1
                d, s = int(TLi[k, 0]), int(TLi[k, 1])
                okb = s in set(f_col[f_ptr[d - 1]:f_ptr[d]]) if d >= 1 else False
                if not okb and p['fund'] == 'NEXT':
                    okb = s in set(n_col[n_ptr[d - 1]:n_ptr[d]])
                if not okb:
                    bad_buy += 1
        block_viol = 0
        if p['reentry'] == 'BLOCK':
            buys = set((int(TLi[k, 0]), int(TLi[k, 1])) for k in range(n) if TLf[k, 1] > 0)
            for i in range(len(IN_i)):
                if (dd[i] + 1, ss[i]) in buys:
                    block_viol += 1
        # ③ 标签 / 锁定守恒
        tc = 0.0
        lc = 0.0
        for d in range(1, d19):
            tc = max(tc, abs(DY[d, E.DYI['tag_amt']] - (DY[d - 1, E.DYI['tag_amt']] + DY[d, E.DYI['tag_new']] - DY[d, E.DYI['tag_use_reg']] - DY[d, E.DYI['tag_use_ext']]
                                                            - DY[d, E.DYI['tag_matured']])) / 1e8)
            lc = max(lc, abs(DY[d, E.DYI['lock_amt']] - (DY[d - 1, E.DYI['lock_amt']] + DY[d, E.DYI['lock_new']] - DY[d, E.DYI['lock_matured']])) / 1e8)
        rows.append(dict(case=tag, exec_id=eid, days=d19, trades=n, buys=nbuy, early_intents=int(len(IN_i)), archived_DY_maxabs=d_arch,
                         acct_nav_pre=diff['nav_pre'], acct_fee=diff['fee'], acct_nav_post=diff['nav_post'], acct_net_excess=diff['net_excess'],
                         acct_exposure=diff['exposure'], acct_cash=diff['cash'], price_mismatch=int(diff.get('price_mismatch', 0)),
                         early_exec_before_t1=viol_first, delayed_exits=delayed, delayed_all_unsellable=delay_days_unsellable_ok,
                         buys_not_in_T_list=bad_buy, block_rebuy_next_day=block_viol, ticket_conservation=tc, lock_conservation=lc,
                         internal_days=int(DY[:, E.DYI['n_internal']].sum())))
        O.log('refcheck %s 完成' % tag)
    D = pd.DataFrame(rows)
    O.atomic_write_csv(O.P('verify', 'refcheck_E6o.csv'), D)
    print(D.T.to_string(), flush=True)
    print(json.dumps(dict(wall_s=round(time.time() - t0, 1))), flush=True)


if __name__ == '__main__':
    main()
