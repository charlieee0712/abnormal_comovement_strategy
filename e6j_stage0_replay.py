# -*- coding: utf-8 -*-
"""E6j Stage 0 第 5 项（brief v1.2 §2；plan §8.2）：显式种子与并行 / 续跑逐位重放实测 + 全样本交易日历。
只比较哈希，不打印、不读任何收益数值（登记前）。推导段 2010-2014、研究母体 R1、S 成员（K_rar20 低坏）的 IID 随机路径。
  --calendar            由锚 1 母体日账本（四段全部交易日）生成 registry/trade_calendar.csv
  --paths a,b,c --tag X 计算指定路径 → stage0/replay/<tag>.json（每路径 net8 / 目标权重 / 掩码的 sha256）
  --check               u 矩阵的切片 / 列重排不变性 + serial / parallel / resume 三组哈希逐位比对 → 回执"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import hashlib

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_random as R

TASK = 'stage0_item5_replay'
OUT = os.path.join(J.RES, 'stage0', 'replay')
CAL = os.path.join(J.RES, 'registry', 'trade_calendar.csv')
SEG = '2010-2014'


def calendar():
    led = pd.read_parquet(os.path.join(J.RES, 'anchors', 'mother_ledger_prod_v2.parquet'), columns=['period', 'date'])
    d = pd.Index(sorted(led.date.unique()))
    J.assert_index_ok(d, 'trade_calendar')
    df = pd.DataFrame({'date': d, 'day_index': np.arange(len(d)), 'block5': np.arange(len(d)) // 5})
    J.atomic_write_csv(CAL, df)
    print('calendar', len(d), d[0], d[-1], J.sha_file(CAL))


def load_cal():
    c = pd.read_csv(CAL)
    return pd.Index(pd.to_datetime(c.date))


def _h(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def research_ctx():
    import e6i_core as I
    import e6i_ops as O
    import e6j_slot as SL
    import e6f_core as F
    import e6g_core as G
    S = I.seg_i(SEG, warm=False)
    M = O.Mother(S, 'R1')
    arr, meta = SL.e6i_member_raw(SEG, 'K_rar20')
    df = pd.DataFrame(np.full((S.T, S.Nfull), np.nan), index=S.pool0.index, columns=S.pool0.columns)
    df.iloc[:, S.ccols] = arr
    cache, _ = F.neu_cache(df, S.pool0, S.log_mcap, S.icodes_neu, 'NS')
    q = G.pct_dense_dir(cache, S.dates, S.ccolpos, S.Nc, 'lo')
    return S, M, q


def run_paths(paths, tag):
    import e6i_engine as E
    S, M, q = research_ctx()
    grid = R.Grid(pd.to_datetime(pd.Index(S.dates).astype(str)), S.ccolnames, load_cal())
    valid = np.isfinite(q) & S.p0c
    rows, cols, cell = R.day_cells(valid)
    rec = {}
    for p in paths:
        key = R.path_key('E6j.stage0.replay', 'R1|K_rar20|low_bad', 'R1', 'native', 'R-SCORE-IID', p)
        u = grid.u_cells(key, rows, cols, 1)
        qr = np.full(q.shape, np.nan)
        qr[rows, cols] = R.assign_by_priority(q[rows, cols], cell, u)
        B2, _ = M.slot('K', lambda: qr, 0.25, 'FALLBACK')
        W = E.dev_weights(S, B2)
        _, _, _, n = E.pnl_W(S, W, 5, 8.0)
        rec[str(p)] = dict(mask=_h(np.asarray(B2, np.uint8)), weights=_h(W), net8=_h(np.nan_to_num(n, nan=-9e99)), key=str(key))
    os.makedirs(OUT, exist_ok=True)
    J.atomic_write_json(os.path.join(OUT, '%s.json' % tag), dict(tag=tag, pid=os.getpid(), paths=rec, generator=R.GEN_ID))
    print('done', tag, len(rec), flush=True)


def check():
    rows = []

    def chk(t, what, ok, detail=''):
        rows.append(dict(test=t, what=what, status='PASS' if ok else 'FAIL', detail=detail))

    cal = load_cal()
    dates = cal[(cal >= '2010-01-04') & (cal <= '2014-12-31')]
    import e6i_core as I
    S = I.seg_i(SEG, warm=False)
    cols = list(S.ccolnames)
    key = R.path_key('E6j.stage0.replay', 'u-matrix', 'R1', 'native', 'R-SCORE-IID', 7)
    g = R.Grid(dates, cols, cal)
    full = R.uniform(key, g.day[:, None], g.tid[None, :])
    half = len(dates) // 2
    g1, g2 = R.Grid(dates[:half], cols, cal), R.Grid(dates[half:], cols, cal)
    sl = np.vstack([R.uniform(key, g1.day[:, None], g1.tid[None, :]), R.uniform(key, g2.day[:, None], g2.tid[None, :])])
    chk('Z1', 'u 矩阵：整段 vs 日期切两半后拼接逐位相同', bool(np.array_equal(full, sl)))
    perm = np.random.default_rng(0).permutation(len(cols))
    gp = R.Grid(dates, [cols[i] for i in perm], cal)
    up = R.uniform(key, gp.day[:, None], gp.tid[None, :])
    chk('Z2', 'u 矩阵：列重排后按 ticker 对回逐位相同', bool(np.array_equal(full[:, perm], up)))
    for bd in (5,):
        u5 = R.uniform(key, (g.day // bd)[:, None], g.tid[None, :])
        same = all(np.array_equal(u5[i], u5[j]) for i in range(len(dates)) for j in (i + 1,) if j < len(dates) and g.day[i] // bd == g.day[j] // bd)
        chk('Z3', 'P5：同一绝对五日块内优先序逐位相同', bool(same))
    k1 = R.path_key('E6j', 'g', 'R1', 'native', 'R-COND', 3)
    k2 = R.path_key('E6j', 'g', 'R1', 'native', 'R-COND', 3)
    k3 = R.path_key('E6j', 'g', 'R1', 'native', 'R-COND', 4)
    chk('Z4', '路径键：同 JSON 同键、换 path_index 不同键（blake2b，与进程无关）', k1 == k2 and k1 != k3)
    # serial / parallel / resume
    def load(tag):
        return json.load(open(os.path.join(OUT, '%s.json' % tag)))
    ser = load('serial')['paths']
    par = {**load('par_a')['paths'], **load('par_b')['paths']}
    res = {**load('resume_1')['paths'], **load('resume_2')['paths']}
    pids = {load(t)['pid'] for t in ('serial', 'par_a', 'par_b', 'resume_1', 'resume_2')}
    chk('Z5', 'serial vs 两进程并行（奇偶分片）：8 条路径 掩码 / 权重 / net8 哈希逐位相同', ser == par, 'pids=%d' % len(pids))
    chk('Z6', 'serial vs 续跑（0–3 后 4–7）：8 条路径哈希逐位相同', ser == res)
    chk('Z7', '不同路径的掩码哈希互不相同（随机确有作用）', len({v['mask'] for v in ser.values()}) == len(ser))
    df = pd.DataFrame(rows)
    J.atomic_write_csv(os.path.join(OUT, 'replay_results.csv'), df)
    ok = bool((df.status == 'PASS').all())
    J.write_receipt(TASK, [os.path.join(OUT, 'replay_results.csv'), CAL] + [os.path.join(OUT, '%s.json' % t) for t in
                                                                           ('serial', 'par_a', 'par_b', 'resume_1', 'resume_2')],
                    'SUCCEEDED' if ok else 'FAILED', generator=R.GEN_ID, blocker=not ok)
    print(df.to_string(), flush=True)
    return 0 if ok else 2


if __name__ == '__main__':
    if '--calendar' in sys.argv:
        calendar(); sys.exit(0)
    if '--check' in sys.argv:
        sys.exit(check())
    ps = [int(x) for x in sys.argv[sys.argv.index('--paths') + 1].split(',')]
    run_paths(ps, sys.argv[sys.argv.index('--tag') + 1])
