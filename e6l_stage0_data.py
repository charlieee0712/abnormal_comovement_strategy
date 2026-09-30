# -*- coding: utf-8 -*-
"""E6l Stage 0 第 4 类：数据 / 时钟（brief §2 第 4 类 / W07 / A1；附录 A4-1 … A4-6）。不读收益。
  --state        A4-1 状态序列 PIT：在截断到三个日期（每个推导 / 后段各取一个段中日期）的数据上重算 Vol3 / Act3 / Trend3 / 调度 b =
                      全程算出的同日值（前缀逐位）
                 A4-2 允许历史：各段各变量 STATE_UNKNOWN 日数（主定义 ≥ 150 参照 与 STRICT250 并印）→ stage0/c4_data/state_unknown_days.csv
                 A4-5 市场收益代理与 Act3 的逐日可得股票数（最小 / 分位；< 100 的日数）；"总换手"桥（全市场 turnover_rate 截面中位）另印
                 A4-6 2015-06-15 / 2024-09-24 起 40 交易日窗口的实际起止日
  --segment S    A4-3 复权 / 前收同源：Base.d = |log(close / lclose)| 与数据字段独立重算（1e−12）；零 d 份额；ε 主导（d < 1e−4）份额（pool0 单元）
                 A4-4 Q_MA 有效数（≥ ceil(.6k) 且当前 d 有效）份额（k = 3 / 5 / 10）；EW 归一化质量 B 分布（λ = .5 / 1/3）
                 T+1 VWAP 时钟（单格目标：首个非零收益在形成日 + 2 行）；段末 ≤ 2026-03-27"""
import e6l_boot  # noqa: F401
import os
import sys
import time
import argparse

import numpy as np
import pandas as pd

import e6l_core as L

CUTS = ('2012-06-29', '2016-06-30', '2021-06-30')
STRESS = ('2015-06-15', '2024-09-24')


def state(out, rerun):
    import e6l_state as S
    rows = []

    def chk(cid, obj, metric, expected, got, ok, note=''):
        rows.append(dict(check_id=cid, object=obj, metric=metric, expected=L.txt(expected), got=L.txt(got)[:300],
                         status='INFO' if ok is None else ('PASS' if ok else 'FAIL'), note=note))
    t0 = time.time()
    data = S.load_full()
    full = S.compute(data)
    fd = pd.Index(full['dates'])
    keys = ('r_m', 'n_ret', 'vol_v', 'vol_pct', 'vol_pct_strict', 'act_med', 'n_act', 'act_20', 'act_pct', 'act_pct_strict', 'trend')
    for cut in CUTS:
        ct = pd.Timestamp(cut)
        part = S.compute(data, cut=ct if ct in fd else fd[fd <= ct][-1])
        m = len(part['dates'])
        bad = []
        for k in keys:
            a_, b_ = np.asarray(full[k])[:m], np.asarray(part[k])
            if not np.array_equal(a_, b_, equal_nan=True) if a_.dtype.kind == 'f' else not np.array_equal(a_, b_):
                bad.append(k)
        code_f, code_p = S.tercile(full['vol_pct'])[:m], S.tercile(part['vol_pct'])
        pf, pp_ = S.high_freq(S.tercile(full['vol_pct']))[:m], S.high_freq(code_p)
        for nm in S.SCHEDULES:
            if not np.array_equal(S.schedule_b(nm, code_f, pf), S.schedule_b(nm, code_p, pp_)):
                bad.append('b_' + nm)
        chk('A4-1', 'cut %s（前缀 %d 日）' % (cut, m), 'Vol3 / Act3 / Trend3 / 调度 b 截断重算 = 全程同日值（逐位）', '0 列不同', bad, not bad)
    C = S.load_cache()
    cd = pd.Index(C['dates'])
    same_cache = all(np.array_equal(np.asarray(C[k]), np.asarray(full[k]), equal_nan=True) if np.asarray(full[k]).dtype.kind == 'f'
                     else np.array_equal(np.asarray(C[k]), np.asarray(full[k])) for k in keys)
    chk('A4-1', 'cache/state/state_full_E6l.npz', '缓存 = 本次现算（逐位）', True, same_cache, same_cache)
    # A4-2
    ud = []
    segs = {'2010-2014': ('2010-01-04', '2014-12-31'), '2015-2018': ('2015-01-05', '2018-12-28'), '2019-2023': ('2019-01-02', '2023-12-29'),
            '2024-2026': ('2024-01-02', '2026-03-27')}
    for sname, (s0, s1) in segs.items():
        m = (cd >= s0) & (cd <= s1)
        for var, main, strict in (('Vol3', 'vol_state', 'vol_state_strict'), ('Act3', 'act_state', 'act_state_strict')):
            ud.append(dict(segment=sname, variable=var, definition='MAIN_GE150', unknown_days=int((np.asarray(C[main])[m] < 0).sum()),
                           defined_days=int((np.asarray(C[main])[m] >= 0).sum()), query_id='E6L-Q13-a'))
            ud.append(dict(segment=sname, variable=var, definition='STRICT250', unknown_days=int((np.asarray(C[strict])[m] < 0).sum()),
                           defined_days=int((np.asarray(C[strict])[m] >= 0).sum()), query_id='E6L-Q13-a'))
        tr = np.asarray(C['trend'])[m]
        ud.append(dict(segment=sname, variable='Trend3', definition='ENDPOINT_MA20_GE16', unknown_days=int((tr < 0).all(axis=1).sum()),
                       defined_days=int((tr >= 0).any(axis=1).sum()), query_id='E6L-Q13-a'))
    U = pd.DataFrame(ud)
    pu = os.path.join(out, 'state_unknown_days.csv')
    L.atomic_write_csv(pu, U)
    s1u = U[(U.segment == '2010-2014') & (U.definition == 'MAIN_GE150')]
    chk('A4-2', '段 1 前段', 'Vol3 / Act3 UNKNOWN 日数（主定义；段 1 无 2010 前数据 → 照跑 b10）', 'Vol ≈ 250 / Act ≈ 330', dict(zip(s1u.variable, s1u.unknown_days)), None)
    chk('A4-2', '段 2–4', '段 2–4 的 Vol3 主定义 UNKNOWN 日数（允许历史取自前段）', '0 或少量', dict(zip(U[(U.definition == 'MAIN_GE150') & (U.variable == 'Vol3')].segment,
                                                                                     U[(U.definition == 'MAIN_GE150') & (U.variable == 'Vol3')].unknown_days)), None)
    # A4-5
    nret, nact = np.asarray(C['n_ret']), np.asarray(C['n_act'])
    live = nret > 0
    chk('A4-5', 'r_m', '市场收益代理逐日可得股票数（最小 / p5 / 中位；< 100 的日数）', '',
        '%d / %d / %d；%d' % (nret[live].min(), np.percentile(nret[live], 5), np.median(nret[live]), int((nret[live] < 100).sum())), None)
    chk('A4-5', 'act', 'Act3 逐日可得比值数（最小 / p5 / 中位；< 100 的日数）', '',
        '%d / %d / %d；%d' % (nact[nact > 0].min(), np.percentile(nact[nact > 0], 5), np.median(nact[nact > 0]), int(((nact > 0) & (nact < 100)).sum())), None)
    xto = data['turnover_rate'].astype(float)
    tot = xto.median(axis=1)
    chk('A4-5', 'turnover_rate', '"总换手"桥：全市场 turnover_rate 截面中位（分位 5 / 50 / 95）', '', np.round(np.nanpercentile(tot.values, [5, 50, 95]), 4).tolist(), None)
    # A4-6
    for s in STRESS:
        ix = int(np.searchsorted(cd.values, s))
        chk('A4-6', 'stress %s' % s, '起点后首个交易日 / 第 40 个交易日', '', '%s / %s' % (cd[ix], cd[min(ix + 39, len(cd) - 1)]), True,
            'window = [%s, %s]' % (cd[ix], cd[min(ix + 39, len(cd) - 1)]))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'state_checks.csv')
    L.atomic_write_csv(p, df)
    ok = not (df.status == 'FAIL').any()
    L.write_receipt('stage0_c4_state' + ('_rerun' if rerun else ''), [p, pu], 'SUCCEEDED' if ok else 'FAILED', counts=df.status.value_counts().to_dict(),
                    blocker=not ok, wall_s=round(time.time() - t0, 1))
    print(df.to_string(max_colwidth=90), flush=True)
    print(df.status.value_counts().to_dict(), 'OK' if ok else 'FAIL', flush=True)
    return 0 if ok else 2


def segment(pname, out, rerun):
    import e6l_env as V
    rows = []

    def chk(cid, obj, metric, expected, got, ok, note=''):
        rows.append(dict(check_id=cid, segment=pname, object=obj, metric=metric, expected=L.txt(expected), got=L.txt(got)[:300],
                         status='INFO' if ok is None else ('PASS' if ok else 'FAIL'), note=note))
    t0 = time.time()
    seg = V.SegL(pname, state=False)
    ci, S = seg.ci, seg.S
    B = seg.base()
    import e6i_core as I
    SW = I.seg_i(pname, warm=True)
    wd = SW.wdata_i
    cl = wd['close'].astype(float).reindex(index=B.dates_w, columns=B.own_cols).values
    lc = wd['lclose'].astype(float).reindex(index=B.dates_w, columns=B.own_cols).values
    with np.errstate(all='ignore'):
        dd = np.abs(np.log(cl / lc))
    bd = np.asarray(B.d, float)
    mm = np.isfinite(bd)
    err = float(np.max(np.abs(dd[mm] - bd[mm]))) if mm.any() else 0.0
    chk('A4-3', 'd', 'Base.d = |log(close / lclose)| 数据字段独立重算（有限格 %d）' % int(mm.sum()), '≤ 1e−12', '%.2e' % err, err <= 1e-12)
    chk('A4-3', 'd', 'Base.d 有限而独立式非有限（前填 / 补零）格数', 0, int((mm & ~np.isfinite(dd)).sum()), int((mm & ~np.isfinite(dd)).sum()) == 0)
    dseg = B.to_seg(bd)
    dc = dseg[ci.t, ci.c]
    fin = np.isfinite(dc)
    chk('A4-3', 'd（pool0 单元）', '有效份额 / 零 d 份额 / ε 主导（d < 1e−4）份额', '',
        '%.6f / %.6f / %.6f' % (fin.mean(), float((dc[fin] == 0).mean()), float((dc[fin] < 1e-4).mean())), None)
    for k in (3, 5, 10):
        cnt = pd.DataFrame(np.isfinite(bd).astype(float)).rolling(k, min_periods=1).sum().to_numpy()
        valid = np.isfinite(bd) & (cnt >= V.mo(k))
        vs = B.to_seg(valid.astype(float))
        v = vs[ci.t, ci.c]
        chk('A4-4', 'Q_MA k=%d' % k, '有效（≥ ceil(.6k) 且当前 d 有效）份额（pool0 单元）', '', '%.6f' % float(np.nanmean(v == 1)), None)
    for lam in (0.5, 1.0 / 3.0):
        _, mass = V.ew_norm(bd, lam)
        ms = B.to_seg(mass)[ci.t, ci.c]
        chk('A4-4', 'EW λ=%.4g' % lam, '归一化质量 B 分位（5 / 50 / 95；pool0 单元）', '', np.round(np.nanpercentile(ms, [5, 50, 95]), 6).tolist(), None)
    SE = seg.SE
    T = seg.T
    t_form = min(40, T - 5)
    c_ = int(ci.c[seg.off[t_form]])
    led = SE.pnl(np.array([t_form]), np.array([c_]), np.array([0.01]), (5,), 8.0)[5]
    nz = np.flatnonzero(np.abs(led[0]) > 0)
    pos = np.flatnonzero(led[1] > 0)
    chk('A4-5c', 'T+1 VWAP', '单格目标（形成日 t，H5）：首个非零收益行 = t + 2；持仓行 = t + 2 … t + 6（T+1 进、T+1+H 出）', '%d / %d..%d' % (t_form + 2, t_form + 2, t_form + 6),
        '%s / %s..%s' % (nz[0] if len(nz) else None, pos.min() if len(pos) else None, pos.max() if len(pos) else None),
        len(nz) > 0 and nz[0] == t_form + 2 and len(pos) and pos.min() == t_form + 2 and pos.max() == t_form + 6)
    last = str(seg.dates[-1])[:10]
    chk('A4-5c', '段末', '段末交易日 ≤ 2026-03-27（右删失；不读 E7）', L.MARKET_DATA_END_MAX, last, last <= L.MARKET_DATA_END_MAX)
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'data_checks_%s.csv' % pname)
    L.atomic_write_csv(p, df)
    ok = not (df.status == 'FAIL').any()
    L.write_receipt('stage0_c4_data_%s%s' % (pname, '_rerun' if rerun else ''), [p], 'SUCCEEDED' if ok else 'FAILED',
                    counts=df.status.value_counts().to_dict(), blocker=not ok, wall_s=round(time.time() - t0, 1))
    print(df.to_string(max_colwidth=90), flush=True)
    print(df.status.value_counts().to_dict(), 'OK' if ok else 'FAIL', flush=True)
    return 0 if ok else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--state', action='store_true')
    ap.add_argument('--segment', default=None)
    ap.add_argument('--rerun', action='store_true')
    a = ap.parse_args()
    out = L.P('stage0', 'c4_data' + ('_rerun' if a.rerun else ''))
    os.makedirs(out, exist_ok=True)
    if a.state:
        return state(out, a.rerun)
    return segment(a.segment, out, a.rerun)


if __name__ == '__main__':
    sys.exit(main())
