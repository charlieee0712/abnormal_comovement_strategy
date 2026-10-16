# -*- coding: utf-8 -*-
"""E6m B6 账户读法（plan §8.4；registry/b6_queries_E6m.csv 冻结的 78 个对象 × 5 个触发）。阶段 S 才跑（真实引擎；读账户层收益，先过封存门）。
只做已声明的反事实诊断，不生成可部署的提前退出账户、不改生产出场。
口径（与引擎同式：形成日 f 的目标权重 w 在 t = f+2 … f+H+1 计入 gross，单日贡献 w·(r0 − bench)[t] / den[t−2]，den = min(t−1, H)）：
- 入场 e0 = f + 1（T+1 VWAP）；最早可卖 e0 + 1（源 T+1 卖出约束）；正常退出 N = f + H + 1。
- 可卖 = 当日开盘交易且非全天一字跌停（high ≤ 跌停价）；停牌 / 一字跌停卖不掉 → 继续持有至可卖或研究边界（段末 / 2026-03-27），右删失计数另报。
- 基线 B = first_feasible(N)：原路径也守同一受限库存合同（卖不掉的库存不在 H 到期时消失；源理论 H 终点只是另一条命名比较）。
- 触发：e0 … N−1 收盘评估，取第一次 = 1 的日子 T（e6m_b6_triggers 面板；UNKNOWN 不算触发）；提前退出 E = first_feasible(min(N, T+1))（plan first_feasible_exit 同式；
  正常退出更早到来时触发不延后正常订单）。用 T 收盘价退出的知情价诊断不参与（NONEXECUTABLE_CLOSE_LOOKBACK 不算）。
- 潜力 = −Σ_{E < t ≤ B} w·x[t]/den[t−2]（提前停止该批未来 gross、释放资金记现金 = 零超额）；其它批次与之后本来就会形成的批次全部冻结，不补买、不再入场。
- fee_proxy = 每次提前卖出单独计 8bp × 被卖权重（上界代理，未与同日其它批次净额合并；总净成本必须先合并净订单，不得相加冒充新策略 net）。
输出 b6_trigger_ledger_<段>.csv（trigger_rate_decimal / potential_gross_ann_pp / fee_proxy_ann_pp / restricted_inventory_days / 右删失数）。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M

ANN = M.ANN
TRIG = {'PRICE_BREAK_2SIGMA20': 'PRICE_BREAK', 'CVR_JUMP_INTO_P90_BAD_TAIL': 'CVR_JUMP', 'CVR_FIRST_VISIBLE_HIGH_TAIL_BRIDGE': 'CVR_FIRST_VISIBLE_HIGH',
        'TREND_ENTERS_DOWN': 'TREND_DOWN', 'TREND_ANY_CHANGE_BRIDGE': 'TREND_ANY_CHANGE'}


def first_feasible_exit(trigger, normal, entry, sell_allowed):
    """plan 附录参考函数逐字转录（只停原批次；两条路径守同一可卖约束）。"""
    x = np.asarray(sell_allowed, bool)

    def after(day):
        a = np.flatnonzero(x[max(day, entry + 1):])
        return int(max(day, entry + 1) + a[0]) if len(a) else None
    baseline = after(normal)
    early = after(min(normal, trigger + 1)) if trigger is not None else baseline
    return early, baseline


def vintage_potential(f, c, w, H, trig_col, sell_col, x_col, T):
    """一只票的一个批次 → (是否触发, 潜力逐日 dict{t: 值}, 基线受限库存日数, 右删失?, 提前卖出日)。"""
    e0, N = f + 1, f + H + 1
    if e0 >= T:
        return False, {}, 0, True, None
    T_ = None
    for t in range(e0, min(N, T)):
        if trig_col[t] == 1:
            T_ = t
            break
    E, B = first_feasible_exit(T_, N, e0, sell_col)
    restricted = (B - N) if (B is not None and B > N) else (0 if B is not None else max(T - N, 0))
    censored = B is None
    if T_ is None or E is None:
        return T_ is not None, {}, restricted, censored, None
    end = (B if B is not None else T - 1)
    pot = {}
    for t in range(E + 1, end + 1):
        if t < f + 2 or t >= T:
            continue
        den = float(min(t - 1, H))
        pot[t] = -w * x_col[t] / den
    return True, pot, restricted, censored, E


def run_object(seg, acct, kept, H, trig, sell, x):
    T = seg.T
    tg = acct.target(kept)
    out = {}
    for name, panel in trig.items():
        n = hit = rinv = cens = 0
        pot = np.zeros(T)
        fee = np.zeros(T)
        for f, c, w in zip(tg['t'], tg['c'], tg['w']):
            n += 1
            h, p, ri, ce, E = vintage_potential(int(f), int(c), float(w), H, panel[:, c], sell[:, c], x[:, c], T)
            hit += h
            rinv += ri
            cens += ce
            for t, v in p.items():
                pot[t] += v
            if E is not None and E < int(f) + H + 1:
                fee[E] += 8e-4 * float(w) / float(min(max(E - 1, 1), H))
        out[name] = dict(trigger_rate_decimal=hit / max(n, 1), potential_gross_ann_pp=float(np.mean(pot)) * ANN, fee_proxy_ann_pp=float(np.mean(fee)) * ANN,
                         restricted_inventory_days=int(rinv), right_censored_vintages=int(cens), vintages=int(n), n_days=int(T))
    return out


def task(seg_name, out):
    import e6k_acct as AC
    import e6m_s_real as RL
    seg = RL.seg_of(seg_name, 'real')
    acct = AC.Acct(seg)
    SE = seg.SE
    x = SE.r0 - SE.bench[:, None]
    z = np.load(M.P('stageS_dev', 'b6', 'b6_triggers_full.npz') if not os.path.exists(M.P('b6', 'b6_triggers_full.npz')) else M.P('b6', 'b6_triggers_full.npz'),
                allow_pickle=False)
    di = {str(d)[:10]: i for i, d in enumerate(z['dates'])}
    ci = {str(c): j for j, c in enumerate(z['columns'])}
    ri = np.array([di[str(d)[:10]] for d in seg.dates])
    cj = np.array([ci.get(str(c), -1) for c in seg.S.ccolnames])
    if (cj < 0).any():
        raise RuntimeError('B6 触发面板缺列')
    trig = {k: z[v][np.ix_(ri, cj)] for k, v in TRIG.items()}
    data = seg.ctx['data']
    g = lambda k: data[k].reindex(index=seg.S.pool0.index, columns=seg.S.pool0.columns).astype(float).to_numpy()[:, seg.ccols]
    is_open = (data['is_open'].reindex(index=seg.S.pool0.index, columns=seg.S.pool0.columns) == 1).to_numpy()[:, seg.ccols]
    hi, ld = g('high'), g('limit_down')
    with np.errstate(invalid='ignore'):
        sell = is_open & ~(np.isfinite(ld) & (hi <= ld + 1e-6))
    Q = M.read_csv_keep(M.P('registry', 'b6_queries_E6m.csv'), dtype=str)
    rows = []
    for obj, g_ in Q.groupby('object', sort=False):
        p = obj.split('|')
        form, H = p[1], int(p[6][1:])
        zm = np.load(M.P('masks', seg_name, '%s.npz' % form), allow_pickle=False)
        n = int(zm['n_cells'][0])
        cfg = '|'.join(p[:6] + p[7:])
        ids = [str(c) for c in zm['config_ids']]
        if p[2] == 'PARENT':
            kept = np.unpackbits(zm['parent_final_bits'])[:n].astype(bool)
        elif cfg in ids:
            kept = np.unpackbits(zm['final_bits'][ids.index(cfg)])[:n].astype(bool)
        else:
            rows += [dict(query_id='E6M-Q15-a', object=obj, trigger=t_, segment=seg_name, status='UNDEFINED') for t_ in g_.trigger]
            continue
        res = run_object(seg, acct, kept, H, {t_: trig[t_] for t_ in g_.trigger}, sell, x)
        for t_ in g_.trigger:
            rows.append(dict(query_id='E6M-Q15-a', object=obj, trigger=t_, segment=seg_name, status='COMPUTED', **res[t_]))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'b6_trigger_ledger_%s.csv' % seg_name)
    M.atomic_write_csv(p, df)
    return p, df


def selftest():
    res = [('plan test_119：触发不延后原可行退出', first_feasible_exit(8, 6, 1, [1] * 12) == (6, 6)),
           ('plan test_120：卖不掉的库存跨过正常到期', first_feasible_exit(2, 5, 1, np.r_[np.ones(3, bool), np.zeros(5, bool), np.ones(2, bool)]) == (8, 8)),
           ('plan test_121：终点卖不掉 → 未知（None）', first_feasible_exit(2, 5, 1, [False] * 8) == (None, None))]
    T, H = 30, 5
    trig = np.zeros(T, int)
    trig[4] = 1
    sell = np.ones(T, bool)
    x = np.full(T, 0.01)
    h, pot, ri, ce, E = vintage_potential(2, 0, 0.1, H, trig, sell, x, T)
    exp = {t: -0.1 * 0.01 / min(t - 1, H) for t in range(E + 1, 2 + H + 2)}
    res.append(('触发日 4 → 第 5 日卖出，停掉 6…8 日贡献（f = 2, H = 5）', h and E == 5 and pot.keys() == exp.keys() and all(abs(pot[k] - exp[k]) < 1e-18 for k in exp)))
    h2, pot2, ri2, ce2, E2 = vintage_potential(2, 0, 0.1, H, np.zeros(T, int), sell, x, T)
    res.append(('无触发 → 潜力 0', (not h2) and not pot2))
    sell3 = sell.copy()
    sell3[8:12] = False
    h3, pot3, ri3, ce3, E3 = vintage_potential(2, 0, 0.1, H, trig, sell3, x, T)
    res.append(('基线到期卖不掉 → 受限库存 4 日，提前退出的潜力延续到基线实际卖出日', ri3 == 4 and max(pot3) == 12))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['run', 'selftest'])
    ap.add_argument('--seg', default='')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    t0 = time.time()
    if a.task == 'selftest':
        res = selftest()
        for nm, ok in res:
            print('%s  %s' % ('PASS' if ok else 'FAIL', nm))
        return 0 if all(ok for _, ok in res) else 1
    import e6m_s_seal as SEAL
    import e6m_s_gate as GT
    SEAL.require('deriv' if a.seg in M.DERIV_SEGS else 'post')
    GT.post_gate(a.seg, 'b6 accounts %s' % a.seg)                      # 直接读后段收益（SE）：再核授权绑定的冻结清单与生效条件
    os.makedirs(a.out, exist_ok=True)
    p, df = task(a.seg, a.out)
    M.write_receipt(os.environ.get('E6M_TASK', 'S_b6_%s' % a.seg), [p], status='SUCCEEDED', code=[__file__, M.__file__], rows=len(df),
                    wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(seg=a.seg, rows=len(df), wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
