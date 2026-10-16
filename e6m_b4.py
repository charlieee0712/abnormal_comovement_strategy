# -*- coding: utf-8 -*-
"""E6m B4（plan §8.1 / §8.1a；registry/b4_queries_E6m.csv 冻结的 78 个对象 × EVENT_CONTRIB / SIGNATURE / SYMDEC）。读账户（封存门）+ 云机状态缓存。
账户差：非父对象 = 对象 net8 − 同 H 实际父 net8（共同有效日）；父对象 = 父自身 net8（相对基准的超额）。年化 = 252·100·日均（ann_pp）。
  event    W1 = 2024-01-15 … 2024-02-23、W2 = 2024-09-24 前后各 20 交易日（stage0/c4_data_windows.csv，真实日历解析）：
           D_full（全段日均）；cond_mean_excl（剔窗口后的条件均值，分母变）；contrib_in / contrib_out（都用全段分母，严格加回 D_full）
  symdec   两段 a、b × 冻结状态 Vol3 / Act3（形成日市场状态码 0 / 1 / 2；−1 = UNKNOWN 单列）：p_sj = 段内已知状态日频率，μ_sj = 条件日均；
           frequency = Σ_C (p_bj − p_aj)(μ_bj + μ_aj)/2，within = Σ_C (μ_bj − μ_aj)(p_bj + p_aj)/2，one_sided = Σ_{j∉C}(p_bj μ_bj − p_aj μ_aj)；
           三项严格加回 mean_b − mean_a（已知状态日上的均值）；UNKNOWN 份额另列，不按 0 闭合（plan §8.1a）
  sig4     全窗与 36 个月滚动的月度净超额（日 net8 按月加总）ACF1 与月波动；逐年约 12 点的估计只作低精度附列（不判拥挤）
  sig1–3   需要逐批次收益（j1…j20 累计超额）、持仓 60 日收益相关矩阵、形成日保留 / 剔除特征价差与其未来收益：阶段 S 引擎层另写，现记 NOT_RUN
b4_signatures 的 A0 骨架列与 event 相同（D_full / cond_mean_excl / contrib_in / contrib_out），装不下签名输出：sig4 写到 b4_sig4_<段>.csv 详表，
骨架表只给状态行并指向详表（STAGE_S_IMPL_PLAN §5 第 22 项，待决策端定）。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_s_stats as SS

ANN = M.ANN
TOL = 1e-12


def series(d, did):
    """对象账户差（非父：对象 − 同 H 实际父；父：自身）→ 日数组（无效日 NaN）。"""
    x = np.asarray(d[did]['net8'], float)
    if did.split('|')[2] == 'PARENT':
        return x
    p = SS.parent_of(did)
    if p not in d:
        return None
    y = np.asarray(d[p]['net8'], float)
    return np.where(np.isfinite(x) & np.isfinite(y), x - y, np.nan)


def event_one(D, inwin):
    v = np.isfinite(D)
    n = int(v.sum())
    if n == 0:
        return dict(status='UNDEFINED')
    full = float(np.sum(D[v])) / n * ANN
    ii, oo = v & inwin, v & ~inwin
    cin = float(np.sum(D[ii])) / n * ANN
    cout = float(np.sum(D[oo])) / n * ANN
    excl = float(np.mean(D[oo])) * ANN if oo.any() else np.nan
    return dict(D_full_ann_pp=full, cond_mean_excl_ann_pp=excl, contrib_in_ann_pp=cin, contrib_out_ann_pp=cout,
                closure=abs(cin + cout - full), n_in=int(ii.sum()), n_all=n, status='COMPUTED' if abs(cin + cout - full) <= 1e-9 else 'CLOSURE_FAIL')


def symdec_one(Da, sa, Db, sb):
    """两段日序列 D 与状态码 s（−1 = UNKNOWN）→ 三项分解（日均单位，调用方年化）。"""
    out = {}
    stats = {}
    for tag, Dx, sx in (('a', Da, sa), ('b', Db, sb)):
        v = np.isfinite(Dx)
        kn = v & (sx >= 0)
        nk = int(kn.sum())
        stats[tag] = dict(n=nk, unknown_share=float((v & (sx < 0)).sum()) / max(int(v.sum()), 1),
                          mean=float(np.mean(Dx[kn])) if nk else np.nan,
                          p={j: float((kn & (sx == j)).sum()) / nk for j in (0, 1, 2)} if nk else {},
                          mu={j: float(np.mean(Dx[kn & (sx == j)])) for j in (0, 1, 2) if (kn & (sx == j)).any()})
    A, B = stats['a'], stats['b']
    if not (A['n'] and B['n']):
        return dict(status='UNDEFINED')
    freq = within = one = 0.0
    for j in (0, 1, 2):
        ina, inb = j in A['mu'], j in B['mu']
        if ina and inb:
            freq += (B['p'][j] - A['p'][j]) * (B['mu'][j] + A['mu'][j]) / 2.0
            within += (B['mu'][j] - A['mu'][j]) * (B['p'][j] + A['p'][j]) / 2.0
        elif inb:
            one += B['p'][j] * B['mu'][j]
        elif ina:
            one -= A['p'][j] * A['mu'][j]
    tot = B['mean'] - A['mean']
    out.update(frequency=freq, within=within, one_sided=one, total=tot, closure=abs(freq + within + one - tot),
               unknown_share_a=A['unknown_share'], unknown_share_b=B['unknown_share'])
    out['status'] = 'COMPUTED' if out['closure'] <= TOL else 'CLOSURE_FAIL'
    return out


def monthly(D, dates):
    s = pd.Series(D, index=pd.to_datetime(pd.Index(dates)))
    g = s.groupby(s.index.to_period('M'))
    m = g.sum(min_count=1)
    return m[g.count() > 0]


def acf1(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return np.nan
    x = x - x.mean()
    den = float(np.sum(x * x))
    return float(np.sum(x[1:] * x[:-1]) / den) if den > 0 else np.nan


def state_codes(dates, var):
    zs = np.load(M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), allow_pickle=False)
    di = {str(d)[:10]: i for i, d in enumerate(zs['dates'])}
    key = {'VOL3': 'vol_state', 'ACT3': 'act_state'}[var]
    ix = np.array([di.get(str(d)[:10], -1) for d in dates])
    out = np.full(len(dates), -1, int)
    ok = ix >= 0
    out[ok] = zs[key][ix[ok]]
    return out


def windows():
    W = M.read_csv_keep(M.P('stage0', 'c4_data_windows.csv'))
    return {('W1_20240115_20240223' if r.window == 'W1' else 'W2_20240924_PM20'): (str(r.first)[:10], str(r.last)[:10]) for r in W.itertuples()}


def task_event(acc, out):
    Q = M.read_csv_keep(M.P('registry', 'b4_queries_E6m.csv'), dtype=str)
    Q = Q[Q.query_kind == 'EVENT_CONTRIB']
    seg = '2024-2026'
    d, t, d2t, dH, dates = SS.load(acc, seg)
    ds = np.array([str(x)[:10] for x in dates])
    WIN = windows()
    rows = []
    for r in Q.itertuples():
        D = series(d, r.object) if r.object in d else None
        if D is None:
            rows.append(dict(query_id='E6M-Q14-a', object=r.object, window=r.window, status='UNDEFINED'))
            continue
        a, b = WIN[r.window]
        e = event_one(D, (ds >= a) & (ds <= b))
        rows.append(dict(query_id='E6M-Q14-a', object=r.object, window=r.window, **e))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'b4_event_contrib_detail.csv')
    M.atomic_write_csv(p, df)
    return p, df


def task_symdec(acc, out):
    Q = M.read_csv_keep(M.P('registry', 'b4_queries_E6m.csv'), dtype=str)
    Q = Q[Q.query_kind == 'SYMDEC']
    cache = {}

    def seg_data(s):
        if s not in cache:
            d, t, d2t, dH, dates = SS.load(acc, s)
            cache[s] = (d, dates, {v: state_codes(dates, v) for v in ('VOL3', 'ACT3')})
        return cache[s]
    rows = []
    for r in Q.itertuples():
        pair, var = r.window.split('|')
        sa, sb = pair.split('_VS_')
        (da, dta, sta), (db, dtb, stb) = seg_data(sa), seg_data(sb)
        Da = series(da, r.object) if r.object in da else None
        Db = series(db, r.object) if r.object in db else None
        if Da is None or Db is None:
            rows.append(dict(query_id='E6M-Q14-c', object=r.object, seg_a=sa, seg_b=sb, state_var=var, status='UNDEFINED'))
            continue
        x = symdec_one(Da, sta[var], Db, stb[var])
        if x.get('status') == 'UNDEFINED':
            rows.append(dict(query_id='E6M-Q14-c', object=r.object, seg_a=sa, seg_b=sb, state_var=var, status='UNDEFINED'))
            continue
        rows.append(dict(query_id='E6M-Q14-c', object=r.object, seg_a=sa, seg_b=sb, state_var=var, frequency_ann_pp=x['frequency'] * ANN,
                         within_ann_pp=x['within'] * ANN, one_sided_ann_pp=x['one_sided'] * ANN, total_ann_pp=x['total'] * ANN,
                         unknown_share_decimal=max(x['unknown_share_a'], x['unknown_share_b']), closure_daily=x['closure'], status=x['status']))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'symdec_detail.csv')
    M.atomic_write_csv(p, df)
    return p, df


def task_sig4(acc, segs, out):
    Q = M.read_csv_keep(M.P('registry', 'b4_queries_E6m.csv'), dtype=str)
    objs = sorted(set(Q[Q.query_kind == 'SIGNATURE'].object))
    per = {}
    for s in segs:
        d, t, d2t, dH, dates = SS.load(acc, s)
        for o in objs:
            D = series(d, o) if o in d else None
            if D is not None:
                per.setdefault(o, []).append(monthly(D, dates))
    rows = []
    for o in objs:
        if o not in per:
            rows.append(dict(object=o, status='UNDEFINED'))
            continue
        mser = pd.concat(per[o]).sort_index()
        roll = [acf1(mser.iloc[i - 36:i].values) for i in range(36, len(mser) + 1)]
        yr = mser.groupby(mser.index.year).apply(lambda x: acf1(x.values))
        rows.append(dict(object=o, months=int(len(mser)), acf1_full=acf1(mser.values), vol_month_full_pp=float(np.std(mser.values, ddof=1)) * 100.0,
                         acf1_roll36_median=float(np.nanmedian(roll)) if roll else np.nan, acf1_roll36_min=float(np.nanmin(roll)) if roll else np.nan,
                         acf1_roll36_max=float(np.nanmax(roll)) if roll else np.nan,
                         acf1_by_year_low_precision=json.dumps({int(k): (None if not np.isfinite(v) else round(float(v), 4)) for k, v in yr.items()}),
                         status='COMPUTED'))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'b4_sig4_detail.csv')
    M.atomic_write_csv(p, df)
    return p, df


def selftest():
    rng = np.random.default_rng(14)
    Da, Db = rng.normal(0.0002, 0.003, 800), rng.normal(-0.0001, 0.004, 600)
    sa, sb = rng.integers(-1, 3, 800), rng.integers(0, 2, 600)                    # b 段没有状态 2 → 单边项
    Da[rng.integers(0, 800, 30)] = np.nan
    x = symdec_one(Da, sa, Db, sb)
    D = rng.normal(0, 0.003, 300)
    D[5] = np.nan
    inwin = np.zeros(300, bool)
    inwin[100:141] = True
    e = event_one(D, inwin)
    ok_ev = e['status'] == 'COMPUTED' and abs(e['contrib_in_ann_pp'] + e['contrib_out_ann_pp'] - e['D_full_ann_pp']) <= 1e-9
    ac = acf1(np.r_[1.0, -1.0, 1.0, -1.0, 1.0, -1.0])
    return [('SYMDEC 三项加回 mean_b − mean_a（含单边状态与 UNKNOWN）closure %.1e' % x['closure'], x['status'] == 'COMPUTED' and abs(x['one_sided']) > 0),
            ('事件窗 contrib_in + contrib_out = D_full（全段分母）', ok_ev), ('ACF1 交替序列 < −0.8', ac < -0.8)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['event', 'symdec', 'sig4', 'selftest'])
    ap.add_argument('--acc', default='')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    t0 = time.time()
    if a.task == 'selftest':
        res = selftest()
        for nm, ok in res:
            print('%s  %s' % ('PASS' if ok else 'FAIL', nm))
        return 0 if all(ok for _, ok in res) else 1
    import e6m_s_seal as SEAL
    for s in M.SEGMENTS if a.task != 'event' else ('2024-2026',):
        SEAL.require_for(a.acc, s)                       # 真实账户：两个封存门；B4 全部涉及后段 → 合成 / 开发目录不拦
    os.makedirs(a.out, exist_ok=True)
    p, df = {'event': lambda: task_event(a.acc, a.out), 'symdec': lambda: task_symdec(a.acc, a.out),
             'sig4': lambda: task_sig4(a.acc, M.SEGMENTS, a.out)}[a.task]()
    st = df.status.value_counts().to_dict() if len(df) else {}
    M.write_receipt(os.environ.get('E6M_TASK', 'S_b4_%s' % a.task), [p], status='SUCCEEDED', code=[__file__, M.__file__], rows=len(df), status_counts=st,
                    wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(task=a.task, rows=len(df), status=st, wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
