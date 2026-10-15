# -*- coding: utf-8 -*-
"""E6n B2：退出 Stage 1 —— 冻结源决策下的逐事件剩余收益与订单差分诊断（plan §8；brief A15、§1.3-12）。不生成可部署退出策略、不参与政策过门。
对象：原六形态（α = 0）+ Q0 HG10 / LAG1_10（α .25，各形态）；H 1 / 3 / 5 / 10 / 20；主触发 CVR_JUMP（cvr_1d 首次由参考 90% 坏尾外跨入），
旧控制 PRICE_BREAK（价稳破坏）、TREND_DOWN（Trend 转 DOWN）；CVR_FIRST_VISIBLE_HIGH 只作桥。触发定义 = E6m e6m_b6_triggers.build（源函数，47 全程数据重建）。
  triggers：全程数据（e6m_stage0_full.load_full，E7 截止守卫）→ b2/triggers_full.npz（int8：1 触发 / 0 / −1 UNKNOWN）+ 与 E6m 开发面板逐格对照。
  prep --seg S：批次风险集与触发率（掩码层事实，不读收益）：入场 e0 = f + 1；正常目标退出 n = f + H + 1；e0…n−1 收盘评估取首次触发 T；
        a = max(e0 + 1, T + 1)；a ≥ n → NO_EARLY_OPPORTUNITY；e_early = 首个可卖 ≥ a，e_base = 首个可卖 ≥ n；e_early < e_base 才是实现的早退；
        同日 → NO_EXECUTED_DIFFERENCE；e_base 不在数据内 → 右删失。可卖 = 当日开盘交易且非全天一字跌停（E6m B6 同式）。
  run --seg S（读收益；后段过 post_gate）：剩余收益差（CASH / NEXT_RANK）、订单差费用（SOLO / JOINT_FROZEN）、同率随机 / CVR 水平 / Bernoulli 三对照（后续实现）。"""
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6n_core as N

E6M_W = N.E6M_WORK
TRIGS = ('CVR_JUMP', 'PRICE_BREAK', 'TREND_DOWN', 'CVR_FIRST_VISIBLE_HIGH')
HOLDS = (1, 3, 5, 10, 20)
FORMS = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
OBJECTS = [(f, 'NONE|a0|NATIVE') for f in FORMS] + [(f, '%s|a0.25|Q0' % m) for f in FORMS for m in ('HG10', 'LAG1_10')]
NO_EARLY, NO_DIFF, REALIZED, CENSORED, NOT_TRIGGERED, NOT_ENTERED = 1, 2, 3, 4, 0, 5


def triggers():
    """E6m 触发函数在 47 全程数据上重建（E6M_WORK 指向 E6m 工作目录只为读其状态缓存；不写 E6m 目录）。"""
    os.environ['E6M_WORK'] = E6M_W
    import e6m_stage0_full as SF
    import e6m_b6_triggers as BT
    t0 = time.time()
    data, before, cd = SF.load_full()
    N.assert_index_ok(data['close'].index, 'B2 triggers')
    P, clean, idx, cols, info = BT.build(data)
    od = N.P('b2')
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, 'triggers_full.npz')
    g = lambda k: data[k].reindex(index=idx, columns=cols).astype(float).to_numpy()
    is_open = (data['is_open'].reindex(index=idx, columns=cols) == 1).to_numpy()
    hi, ld = g('high'), g('limit_down')
    lo, lu = g('low'), g('limit_up')
    with np.errstate(invalid='ignore'):
        sell = is_open & ~(np.isfinite(ld) & (hi <= ld + 1e-6))
        buy = is_open & ~(np.isfinite(lu) & (lo >= lu - 1e-6))
        c_, vw = g('close'), g('vwap')
        cvr = np.where(is_open & (vw > 0) & (c_ > 0), c_ / vw - 1.0, np.nan)
    cvr_pct = BT.ecdf_pct(cvr, np.where(clean, cvr, np.nan)).astype(np.float32)       # e6m_b6_triggers.build 同式（CVR 水平对照用）
    N.atomic_write_npz(p, dates=np.array([str(d)[:10] for d in idx]), columns=np.array([str(x) for x in cols]), sell=sell, buy=buy, cvr_pct=cvr_pct, **P)
    # 对 E6m 开发面板逐格
    cmp_ = {}
    pe = os.path.join(E6M_W, 'stageS_dev', 'b6', 'b6_triggers_full.npz')
    if os.path.exists(pe):
        z = np.load(pe, allow_pickle=False)
        same_axes = (list(z['dates']) == [str(d)[:10] for d in idx]) and (list(z['columns']) == [str(x) for x in cols])
        cmp_['axes_equal'] = bool(same_axes)
        if same_axes:
            for k in BT.NAMES:
                cmp_[k] = int((z[k] != P[k]).sum())
    info.update(wall_s=round(time.time() - t0, 1), cache_dir_unchanged=sorted(os.listdir(cd)) == before, vs_e6m_dev_panel=cmp_)
    N.atomic_write_json(os.path.join(od, 'triggers_facts.json'), info)
    N.write_receipt('E6n_b2_triggers', [p, os.path.join(od, 'triggers_facts.json')], code=[__file__], **{k: v for k, v in info.items() if not isinstance(v, dict)})
    N.log('B2 触发面板：%s' % json.dumps(info, ensure_ascii=False))
    return p


def load_triggers(path=None):
    """触发 / 可卖面板（B2 风险集唯一入口）：E7 截止守卫——面板日期 > 2026-03-27 即拒绝（读取接口截断，不先读后滤）。"""
    z = np.load(path or N.P('b2', 'triggers_full.npz'), allow_pickle=False)
    N.assert_index_ok(pd.DatetimeIndex(pd.to_datetime([str(x) for x in z['dates']])), 'B2 触发面板')
    return z


def _first_ge(sell_col, start, T):
    for d in range(start, T):
        if sell_col[d]:
            return d
    return -1


def risk_facts_numba():
    from numba import njit

    @njit(cache=False)
    def run(f, c, trig, sell, H, T):
        n = len(f)
        status = np.zeros(n, np.int8)
        trig_day = np.full(n, -1, np.int64)
        e_early = np.full(n, -1, np.int64)
        e_base = np.full(n, -1, np.int64)
        unknown_days = np.zeros(n, np.int64)
        for i in range(n):
            e0 = f[i] + 1
            nn = f[i] + H + 1
            if e0 >= T:
                status[i] = 5
                continue
            ci = c[i]
            tt = -1
            for d in range(e0, min(nn, T)):
                v = trig[d, ci]
                if v == 1:
                    tt = d
                    break
                if v < 0:
                    unknown_days[i] += 1
            b = -1
            for d in range(nn, T):
                if sell[d, ci]:
                    b = d
                    break
            e_base[i] = b
            if tt < 0:
                status[i] = 0
                continue
            trig_day[i] = tt
            a = max(e0 + 1, tt + 1)
            if a >= nn:
                status[i] = 1
                continue
            e = -1
            for d in range(a, T):
                if sell[d, ci]:
                    e = d
                    break
            e_early[i] = e
            if e < 0:
                status[i] = 4
            elif b >= 0 and e >= b:
                status[i] = 2
            elif b < 0:
                status[i] = 3
            else:
                status[i] = 3
        return status, trig_day, e_early, e_base, unknown_days
    return run


def prep(seg):
    import e6n_vars as VR
    t0 = time.time()
    B = VR.Base(seg)
    z = load_triggers()
    fd = {d: i for i, d in enumerate(z['dates'])}
    fc = {c: j for j, c in enumerate(z['columns'])}
    dates = [str(x)[:4] + '-' + str(x)[4:6] + '-' + str(x)[6:] for x in B.get('dates')]
    codes = [str(x) for x in B.get('codes')]
    ri = np.array([fd[d] for d in dates])
    cj = np.array([fc.get(c, -1) for c in codes])
    if (cj < 0).any():
        raise RuntimeError('触发面板缺列 %d' % int((cj < 0).sum()))
    T = len(dates)
    sell = np.ascontiguousarray(z['sell'][np.ix_(ri, cj)])
    run = risk_facts_numba()
    rows = []
    batches = {}
    for form, key in OBJECTS:
        zm = np.load(N.P('masks', seg, '%s.npz' % form), allow_pickle=False)
        keys = [str(k) for k in zm['mask_keys']]
        F = np.unpackbits(zm['final_bits'][keys.index(key)])[:B.n].astype(bool)
        ids = np.flatnonzero(F)
        f = B.t[ids].astype(np.int64)
        c = B.c[ids].astype(np.int64)
        batches[(form, key)] = (f, c)
        for tg in TRIGS:
            trig = np.ascontiguousarray(z[tg][np.ix_(ri, cj)])
            for H in HOLDS:
                st, td, ee, eb, uk = run(f, c, trig, sell, H, T)
                ent = st != NOT_ENTERED
                rows.append(dict(segment=seg, form=form, object_key=key, trigger=tg, H=H, batches=int(len(f)), entered=int(ent.sum()),
                                 triggered=int(((st != NOT_TRIGGERED) & ent).sum()), no_early_opportunity=int((st == NO_EARLY).sum()),
                                 no_executed_difference=int((st == NO_DIFF).sum()), realized_early=int((st == REALIZED).sum()),
                                 early_unsellable_censored=int((st == CENSORED).sum()), base_right_censored=int((ent & (eb < 0)).sum()),
                                 trigger_rate_decimal=float(((st != NOT_TRIGGERED) & ent).sum() / max(ent.sum(), 1)),
                                 no_early_share_decimal=float((st == NO_EARLY).sum() / max(((st != NOT_TRIGGERED) & ent).sum(), 1)),
                                 unknown_trigger_cell_days=int(uk.sum())))
    df = pd.DataFrame(rows)
    od = N.P('b2')
    p = os.path.join(od, 'b2_risk_set_facts_%s.csv' % seg)
    N.atomic_write_csv(p, df)
    N.write_receipt('E6n_b2_prep_%s' % seg, [p], code=[__file__], rows=len(df), wall_s=round(time.time() - t0, 1))
    N.log('B2 prep %s：%d 行，%.0f s' % (seg, len(df), time.time() - t0))
    return p


def selftest():
    """附录 earliest_exit 六例（plan 附录 B）在本实现上逐例复现（单批次、全可卖 / 指定可卖）。"""
    run = risk_facts_numba()

    def one(entry_f, H, trig_day, tradable, T=40):
        trig = np.zeros((T, 1), np.int8)
        if trig_day is not None:
            trig[trig_day, 0] = 1
        sell = np.zeros((T, 1), bool)
        for d in tradable:
            if d < T:
                sell[d, 0] = True
        st, td, ee, eb, uk = run(np.array([entry_f], np.int64), np.array([0], np.int64), trig, sell, H, T)
        return int(st[0]), int(ee[0]), int(eb[0])
    res = []
    # 参考：earliest_exit(entry, normal, trigger, tradable)；本实现 entry = f+1、normal = f+H+1
    res.append(('卖出最早 T+1（同日不能买卖）：entry 10、normal 15、trigger 10、可卖 {10,11,12} → 11', one(9, 5, 10, {10, 11, 12, 15}) == (3, 11, 15)))
    res.append(('触发在入场前不算退出：trigger 9 < entry 10 → 不触发', one(9, 5, 8, {10, 11, 15})[0] == 0))
    res.append(('晚触发不退回过去：trigger 16 ≥ normal 15 → 不在窗口（不触发）', one(9, 5, 16, {15, 16, 17})[0] == 0))
    res.append(('卖不掉的库存保留：entry 10、normal 15、trigger 11、可卖 {14,15} → 早退 14', one(9, 5, 11, {14, 15})[:2] == (3, 14)))
    res.append(('右删失：基线可卖日不在数据内 → 早退可实现但基线删失', one(9, 5, 11, {12}, T=16) == (3, 12, -1)))
    res.append(('触发在正常日前一日：a = normal → NO_EARLY_OPPORTUNITY', one(0, 5, 5, set(range(40)))[0] == NO_EARLY))
    res.append(('同一实际卖日：早退可卖日 ≥ 基线 → NO_EXECUTED_DIFFERENCE', one(0, 5, 3, {7, 8})[0] == NO_DIFF))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['triggers', 'prep', 'selftest'])
    ap.add_argument('--seg', default='')
    a = ap.parse_args()
    if a.step == 'triggers':
        triggers()
    elif a.step == 'prep':
        prep(a.seg)
    else:
        res = selftest()
        for nm, ok in res:
            print('%s  %s' % ('PASS' if ok else 'FAIL', nm))
        pd.DataFrame([dict(test=nm, ok=ok) for nm, ok in res]).to_csv(N.P('stage0', 'a3_11_b2_clock_selftest.csv'), index=False)
        sys.exit(0 if all(ok for _, ok in res) else 1)


if __name__ == '__main__':
    main()
