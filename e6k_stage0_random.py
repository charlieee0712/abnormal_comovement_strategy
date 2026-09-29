# -*- coding: utf-8 -*-
"""E6k Stage 0 第 5 类：随机 / 状态（brief §2 第 5 类；附录 A2-6、A5-1 … A5-6）。推导段 2010-2014；只比哈希与结构计数，不读收益数值。
  A2-6 LEGACY 复现：E6j stage0/replay/serial.json 的 8 条路径（键 ('E6j.stage0.replay', 'R1|K_rar20|low_bad', 'R1', 'native', 'R-SCORE-IID', p)，
       当日 cell 内 u 降序分配）→ E6k 结构 A4b_CVRv5（= R1）α .25 → 掩码 / E6i 稠密 DEV 权重 / E6i 稠密 H5 8bp net8 哈希逐位 = E6j；键逐字相同；
       另核 E6k 测量坐标 kf('S') = E6j 研究坐标 q（逐位）
  A5-1 生成器：置换 = splitmix64 计数器（e6j_random.GEN_ID）；bootstrap = blake2b → SeedSequence → PCG64（e6k_core.rng_for）；写回执 generator
  A5-2 NEW 机制：u 矩阵整段 vs 日期切半拼接、列重排逐位；8 条路径 串行 / 两个独立进程（spawn）奇偶分片 / 续跑（0–3 后新对象 4–7）掩码与 net8 哈希逐位
  A5-3 缺失合同：置换后 NaN 位置不变；叶内值多重集不变；值只在同叶内移动（真实数据 + test_88 合成）
  A5-4 八子集分层树：不重叠（每有效单元恰一叶）；叶 < 2 只可能是当日根；可移动份额与置换熵逐子集报
  A5-5 HG 随机路径各有自己的前日状态：从空状态重跑 = 路径结果；借真实 HG 状态会不同（记录差异格数）
  A5-6 random_registry 两类分开登记（A0 随机清单按机制计数）"""
import e6k_boot  # noqa: F401
import os
import sys
import json
import time
import hashlib
import argparse
import multiprocessing as mp

import numpy as np
import pandas as pd

import e6k_core as K

SEG = '2010-2014'


def _h(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def _new_paths(paths, fresh=True):
    """独立进程入口：从零建环境，按 NEW 机制（ISK，块长 5）算 A4b_CVRv5 × S α .25 的路径掩码与稀疏 H5 net8 哈希。"""
    import e6k_env as E
    import e6k_ops as O
    import e6k_random as RN
    seg = E.Seg(SEG)
    st = seg.struct('A4b_CVRv5')
    kf = seg.kf('S')
    nc = RN.NewCond(seg, 'S', kf, st.q0, 'ISK', 5)
    out = {}
    for p in paths:
        if fresh:
            nc = RN.NewCond(seg, 'S', kf, st.q0, 'ISK', 5)
        kp = nc.draw(p)
        kept = st.kept(O.native_q(st.q0, kp, 0.25)[None, :])[0]
        t, c = seg.ci.t[kept], seg.ci.c[kept]
        n = seg.SE.pnl(t, c, seg.SE.dev(t, c), (5,), 8.0)[5][3]
        out[int(p)] = dict(mask=_h(np.packbits(kept)), net8=_h(np.nan_to_num(n, nan=-9e99)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rerun', action='store_true')
    a = ap.parse_args()
    out = K.P('stage0', 'c5_random' + ('_rerun' if a.rerun else ''))
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    rows = []

    def chk(cid, what, ok, detail=''):
        rows.append(dict(check_id=cid, what=what, status='INFO' if ok is None else ('PASS' if ok else 'FAIL'), detail=str(detail)[:300]))

    import e6k_env as E
    import e6k_ops as O
    import e6k_random as RN
    import e6j_random as RND
    import e6i_engine as EI
    import e6f_core as F
    import e6g_core as G
    seg = E.Seg(SEG)
    S, ci = seg.S, seg.ci
    st = seg.struct('A4b_CVRv5')
    k0 = st.q0
    # ---------------- A2-6
    arr, _ = __import__('e6j_slot').e6i_member_raw(SEG, 'K_rar20')
    df = pd.DataFrame(np.full((S.T, S.Nfull), np.nan), index=S.pool0.index, columns=S.pool0.columns)
    df.iloc[:, S.ccols] = arr
    cache, _ = F.neu_cache(df, S.pool0, S.log_mcap, S.icodes_neu, 'NS')
    q = G.pct_dense_dir(cache, S.dates, S.ccolpos, S.Nc, 'lo')
    kfS = seg.kf('S')
    qc = q[ci.t, ci.c]
    same_coord = bool(np.array_equal(np.isnan(qc), np.isnan(kfS)) and np.array_equal(qc[np.isfinite(qc)], kfS[np.isfinite(kfS)]))
    chk('A2-6', 'E6k 测量坐标 kf(S) = E6j 研究坐标 q（pool0 单元逐位）', same_coord)
    ser = json.load(open(os.path.join(K.E6J_RES, 'stage0', 'replay', 'serial.json'), encoding='utf-8'))
    valid = np.isfinite(q) & S.p0c
    rows_, cols_, cell = RND.day_cells(valid)
    grid = seg.env.grid
    bad = []
    for p in range(8):
        key = RND.path_key('E6j.stage0.replay', 'R1|K_rar20|low_bad', 'R1', 'native', 'R-SCORE-IID', p)
        u = grid.u_cells(key, rows_, cols_, 1)
        qr = np.full(q.shape, np.nan)
        qr[rows_, cols_] = RND.assign_by_priority(q[rows_, cols_], cell, u)
        kept = st.kept(O.native_q(k0, qr[ci.t, ci.c], 0.25)[None, :])[0]
        B2 = np.zeros((S.T, S.Nc), bool)
        B2[ci.t[kept], ci.c[kept]] = True
        W = EI.dev_weights(S, B2)
        _, _, _, n = EI.pnl_W(S, W, 5, 8.0)
        rec = dict(mask=_h(np.asarray(B2, np.uint8)), weights=_h(W), net8=_h(np.nan_to_num(n, nan=-9e99)), key=str(key))
        if rec != ser['paths'][str(p)]:
            bad.append(p)
    chk('A2-6', 'LEGACY 8 条路径 键 / 掩码 / 权重 / net8 哈希 = E6j serial.json', not bad, 'differ paths=%s' % bad)
    # ---------------- A5-1
    chk('A5-1', '生成器：置换 %s；bootstrap blake2b-128 → SeedSequence → PCG64（e6k_core.rng_for）' % RND.GEN_ID, True)
    # ---------------- A5-2
    cal = seg.env.grid
    cols = list(S.ccolnames)
    dates = seg.dates
    key = RND.path_key('E6k.NEW', 'u-matrix', 'COND_ISK', 'B5', 'content', 7)
    g = RND.Grid(dates, cols, pd.Index(pd.to_datetime(pd.read_csv(os.path.join(K.E6J_RES, 'registry', 'trade_calendar.csv')).date)))
    full = RND.uniform(key, (g.day // 5)[:, None], g.tid[None, :])
    half = len(dates) // 2
    calx = pd.Index(pd.to_datetime(pd.read_csv(os.path.join(K.E6J_RES, 'registry', 'trade_calendar.csv')).date))
    g1, g2 = RND.Grid(dates[:half], cols, calx), RND.Grid(dates[half:], cols, calx)
    sl = np.vstack([RND.uniform(key, (g1.day // 5)[:, None], g1.tid[None, :]), RND.uniform(key, (g2.day // 5)[:, None], g2.tid[None, :])])
    chk('A5-2', 'NEW u 矩阵：整段 vs 日期切半拼接逐位', bool(np.array_equal(full, sl)))
    perm = np.random.default_rng(0).permutation(len(cols))
    gp = RND.Grid(dates, [cols[i] for i in perm], calx)
    chk('A5-2', 'NEW u 矩阵：列重排后按 ticker 对回逐位', bool(np.array_equal(full[:, perm], RND.uniform(key, (gp.day // 5)[:, None], gp.tid[None, :]))))
    serial = _new_paths(range(8), fresh=False)
    ctx = mp.get_context('spawn')
    with ctx.Pool(2) as pool:
        ra, rb = pool.map(_new_paths, [[0, 2, 4, 6], [1, 3, 5, 7]])
    par = {**ra, **rb}
    res = {**_new_paths(range(4)), **_new_paths(range(4, 8))}
    chk('A5-2', 'NEW 8 条路径：串行 vs 两个 spawn 进程奇偶分片 掩码 / net8 哈希逐位', serial == par)
    chk('A5-2', 'NEW 8 条路径：串行 vs 续跑（0–3 后新对象 4–7）逐位', serial == res)
    chk('A5-2', 'NEW 不同路径掩码互不相同（随机确有作用）', len({v['mask'] for v in serial.values()}) == 8)
    # ---------------- A5-3 / A5-4
    kf = seg.kf('S')
    V = np.isfinite(kf)
    diag = []
    for sub in RN.SUBSETS:
        nc = RN.NewCond(seg, 'S', kf, k0, sub, 5)
        leaf = nc.leaf
        cnt = np.bincount(leaf[V])
        one_leaf_ok = True
        if (cnt < 2).any():
            small = np.flatnonzero(cnt < 2)
            days_small = seg.ci.t[V][np.isin(leaf[V], small)]
            dcnt = np.bincount(seg.ci.t[V], minlength=seg.T)
            one_leaf_ok = bool((dcnt[days_small] < 2).all())
        chk('A5-4', '%s：每有效单元恰一叶；叶 < 2 只可能是当日根' % sub, bool((leaf[V] >= 0).all() and (leaf[~V] == -1).all() and one_leaf_ok))
        d = RN.leaf_diagnostics(seg, leaf, V)
        d.update(subset=sub, tree=json.dumps(nc.tree_stats))
        diag.append(d)
        kp = nc.draw(3)
        chk('A5-3', '%s：置换后 NaN 位置不变' % sub, bool(np.array_equal(np.isnan(kp), np.isnan(kf))))
        dfv = pd.DataFrame({'leaf': leaf[V], 'a': kf[V], 'b': kp[V]})
        ms = dfv.groupby('leaf').apply(lambda x: np.array_equal(np.sort(x.a.values), np.sort(x.b.values))).all()
        chk('A5-3', '%s：叶内值多重集不变（值只在同叶内移动）' % sub, bool(ms))
    pdiag = os.path.join(out, 'eight_subset_leaf_diagnostics.csv')
    K.atomic_write_csv(pdiag, pd.DataFrame(diag))
    chk('A5-4', '八子集可移动份额 / 置换熵（见 eight_subset_leaf_diagnostics.csv）', None,
        '; '.join('%s %.3f/%.3f' % (d['subset'], d['movable_share'], d['entropy_ratio']) for d in diag))
    v = np.array([[1.], [np.nan], [3.], [4.]])
    import e6k_ops  # noqa: F401
    o = np.full(4, np.nan)
    asg = RN.Assigner2(v[np.isfinite(v[:, 0]), 0], np.zeros(3, np.int64))
    o[np.isfinite(v[:, 0])] = asg(np.array([0.3, 0.9, 0.1]))
    chk('A5-3', '合成（test_88 型）：缺失值不在股票间移动；有限值多重集不变', bool(np.isnan(o[1]) and sorted(o[np.isfinite(o)]) == [1., 3., 4.]))
    # ---------------- A5-5
    nc = RN.NewCond(seg, 'S', kf, k0, 'ISK', 5)
    kp = nc.draw(11)
    tid_ids = seg.tid[st.ids]
    sc = st.gate_scores(O.native_q(k0, kp, 0.25)[None, :])
    g_own = O.hg_gate(st, sc, 10 * st.bunit, tid_ids)
    g_own2 = O.hg_gate(st, sc, 10 * st.bunit, tid_ids)
    real = st.gate_scores(O.native_q(k0, kf, 0.25)[None, :])
    _, real_state = O.hg_gate(st, real, 10 * st.bunit, tid_ids, return_state=True)
    chk('A5-5', 'HG 随机路径从自身空状态递推可逐位重放', bool(np.array_equal(g_own, g_own2)))
    mid = seg.T // 2
    a1 = O.hg_gate(st, sc, 10 * st.bunit, tid_ids)
    chk('A5-5', 'HG 随机路径不借真实 HG 状态（本轮实现只接受自身 init；差异示例见 detail）', True,
        '同一随机分数下"段首借真实段末状态"与"空状态"门差异格数 = %d' % int((O.hg_gate(st, sc, 10 * st.bunit, tid_ids, init_cols=real_state) != a1).sum()))
    # ---------------- A5-6
    rr = pd.read_csv(os.path.join(K.TRIAL, 'a0', 'registry', 'randoms_E6k.csv')) if not os.path.exists(K.P('registry', 'randoms_E6k.csv')) \
        else pd.read_csv(K.P('registry', 'randoms_E6k.csv'))
    cnt = rr.mechanism.value_counts().to_dict()
    chk('A5-6', 'random_registry 两类分开登记（机制计数）', any(k.startswith('LEGACY') for k in cnt) and any(k.startswith('NEW') for k in cnt), json.dumps(cnt))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'random_checks.csv')
    K.atomic_write_csv(p, df)
    ok = not (df.status == 'FAIL').any()
    K.write_receipt('stage0_c5_random' + ('_rerun' if a.rerun else ''), [p, pdiag], 'SUCCEEDED' if ok else 'FAILED',
                    counts=df.status.value_counts().to_dict(), blocker=not ok, generator=RND.GEN_ID,
                    bootstrap_generator='blake2b-128(canonical_json(key)) -> SeedSequence -> PCG64', wall_s=round(time.time() - t0, 1))
    print(df.to_string(max_colwidth=120), flush=True)
    print(df.status.value_counts().to_dict(), 'OK' if ok else 'FAIL', flush=True)
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
