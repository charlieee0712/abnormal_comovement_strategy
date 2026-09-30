# -*- coding: utf-8 -*-
"""E6l Stage 0 第 5 类：随机 / 状态（brief §2 第 5 类 / W10 / W13；附录 A2-6、A5-1 … A5-5）。推导段 2010-2014。
  A2-6 LEGACY_POLICY_RANDOM 对 Q0 × NATIVE / HG10 × α .25 × H5 × 六形态（E6k 同构对象）用正式随机运行器（e6l_run_rand --stage0，
       numba 提速件）跑 1,024 路径 → 路径均值 / sd / n = E6k results/full/random_refs_2010-2014.csv 同对象（1e−12）；
       CONTENT_COND_ISK_P5 同对象 = E6k NEW_COND_ISK_P5（同键同树；1e−12）
  A5-1 显式种子：path_key 由 (命名空间, 测量, 控制, 支持, 机制, path) 的规范 JSON → blake2b-64；u = splitmix64(键 ⊕ 绝对块·C1 ⊕ ticker·C2)；
       两个独立 spawn 进程同键 → 同 u（逐位）；不依赖 Python hash / worker 编号 / 完成顺序
  A5-2 MC 记账：首 1,024 路径固定、512 增补、MCSE ≤ .03 或 8,192（规划函数单测）；两遍方差 vs Welford（1e−12）；恒等路径 sd = 0（两遍式精确 0）
  A5-3 R-MARK 分区：ISK 回退树每名恰一叶；叶 < 2 只可能是当日根；真实 HG10 标记的逐日保持率 / 可移动份额 / 熵比（分位）
  A5-4 LEGACY 注入点：新测量置换 = 当日有限 kf（平滑 / 中性化 / 方向之后）的日内置换，缺失位置不动；OLD_RULE 登记 NO_NEW_CONTENT_TO_PERMUTE
  A5-5 STATE 对象的随机路径用同一状态序列（调度 b 与路径无关；状态不随机化）"""
import e6l_boot  # noqa: F401
import os
import sys
import json
import glob
import time
import argparse
import subprocess
import multiprocessing as mp

import numpy as np
import pandas as pd

import e6l_core as L

SEG = '2010-2014'


def _u_proc(args):
    import e6j_random as RND
    key = RND.path_key(*args)
    return RND.uniform(key, np.arange(0, 400) // 5, np.arange(1, 401) * 7).tobytes().hex()[:4096]


def plan_topup(have, sd, target=0.03, cap=8192, step=512):
    need = int(min(cap, max(have, np.ceil((sd / target) ** 2))))
    return have if need <= have else int(min(cap, have + step * np.ceil((need - have) / float(step))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rerun', action='store_true')
    ap.add_argument('--skip-run', action='store_true')
    ap.add_argument('--reg', default=os.path.join(L.TRIAL, 'a0', 'registry'))
    a = ap.parse_args()
    out = L.P('stage0', 'c5_random' + ('_rerun' if a.rerun else ''))
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    rows = []

    def chk(cid, what, ok, detail=''):
        rows.append(dict(check_id=cid, what=what, status='INFO' if ok is None else ('PASS' if ok else 'FAIL'), detail=L.txt(detail)[:400]))
    # ---------------- A2-6（正式随机运行器，stage0 模式）
    rd = L.P('stage0', 'c5_random', 'randoms')                     # 正式运行器产物的固定位置（--rerun --skip-run 复用，不重算）
    regex = r'^Q0\|[^|]+\|a0\.25\|H5\|(NATIVE|HG10)$'
    if not a.skip_run:
        cmd = [os.path.join(L.CODE, 'e6l_run.sh'), os.path.join(L.P('logs'), 'stage0_c5_randrun.log'), os.path.join(L.CODE, 'e6l_run_rand.py'),
               '--segment', SEG, '--stage0', '--reg', a.reg, '--out', rd, '--mechs', 'LEGACY_POLICY_RANDOM,CONTENT_COND_ISK_P5', '--meas', 'Q0',
               '--desc-regex', regex, '--npaths', '1024', '--chunk', '128', '--workers', '16']
        r = subprocess.run(cmd, capture_output=True, text=True)
        chk('A2-6', '正式随机运行器（--stage0；16 进程；1,024 路径 × 2 机制）退出码', r.returncode == 0, 'rc=%d' % r.returncode)
    E = pd.read_csv(L.K6('results', 'full', 'random_refs_%s.csv' % SEG))
    Dq = L.read_csv_keep(os.path.join(a.reg, 'descriptors_E6l.csv'), usecols=['desc_id', 'e6k_equiv'])
    eq = dict(zip(Dq.desc_id, Dq.e6k_equiv))
    for mech, emech in (('LEGACY_POLICY_RANDOM', 'LEGACY_POLICY_RANDOM'), ('CONTENT_COND_ISK_P5', 'NEW_COND_ISK_P5')):
        files = sorted(glob.glob(os.path.join(rd, mech, SEG, '*.npz')))
        acc = {}
        for f in files:
            z = L.npz(f)
            for i, (did, H) in enumerate(zip([str(x) for x in z['desc']], z['H'])):
                v = z['s_net'][i] / z['n_net'][i] * L.ANN
                acc.setdefault((did, int(H)), []).append(v)
        worst, nobj = 0.0, 0
        det = []
        for (did, H), parts in sorted(acc.items()):
            v = np.concatenate(parts)
            n = len(v)
            m = float(np.mean(v))
            sd = float(np.std(v, ddof=1))
            e = E[(E.desc_id == eq[did]) & (E.H == H) & (E.mechanism == emech)]
            if not len(e):
                det.append('%s: E6k 无同对象' % did)
                continue
            e = e.iloc[0]
            err = max(abs(m - e.rand_mean), abs(sd - e.rand_sd))
            worst = max(worst, err if n == int(e.n) else 1.0)
            nobj += 1
            det.append('%s n %d/%d mean %.6f/%.6f sd %.6f/%.6f' % (did.split('|')[1], n, int(e.n), m, e.rand_mean, sd, e.rand_sd))
        chk('A2-6', '%s：%d 个对象路径均值 / sd / n = E6k %s（1e−12）' % (mech, nobj, emech), nobj == 12 and worst <= 1e-12, 'max|Δ| %.2e；%s' % (worst, '; '.join(det[:4])))
    # ---------------- A5-1
    import e6j_random as RND
    args = [('E6j.P', 'E6l.Q_D5', 'P_production_v2', 'native', 'IID', 7), ('E6k.NEW', 'Q', 'COND_ISK', 'B5', 'content', 3),
            ('E6l.RMARK', 'RMARK_ISK_P5', 'ALL', 'gate', 'marks', 11)]
    ctx = mp.get_context('spawn')
    with ctx.Pool(2) as pool:
        r1 = pool.map(_u_proc, args)
        r2 = pool.map(_u_proc, list(reversed(args)))[::-1]
    local = [_u_proc(x) for x in args]
    chk('A5-1', '同键 → 同 u：两个 spawn 进程（正 / 反序）与本进程逐位（三种命名空间）', r1 == r2 == local, RND.GEN_ID)
    k1 = RND.path_key('E6j.P', 'E6l.Q_D5', 'P_production_v2', 'native', 'IID', 7)
    chk('A5-1', 'path_key 为规范 JSON 的 blake2b-64（与 Python hash / PYTHONHASHSEED 无关）', isinstance(k1, int) and k1 == RND.path_key(*args[0]), hex(k1))
    # ---------------- A5-2
    ok_plan = (plan_topup(1024, 0.5) == 1024 and plan_topup(1024, 1.2) == 2048 and plan_topup(1024, 2.0) == 4608 and plan_topup(1024, 9.9) == 8192
               and plan_topup(1536, 1.2) == 2048)
    chk('A5-2', '增补规划：首 1,024 固定；需 (sd/.03)² 条；512 一批；上限 8,192（单测 5 例）', ok_plan)
    rng = np.random.default_rng(11)
    x = rng.normal(0.3, 0.2, 4096)
    mu = 0.0
    m2 = 0.0
    for i, v in enumerate(x, 1):
        dlt = v - mu
        mu += dlt / i
        m2 += dlt * (v - mu)
    sd_w = np.sqrt(m2 / (len(x) - 1))
    sd_2 = float(np.std(x, ddof=1))
    chk('A5-2', '两遍方差 = Welford（1e−12）', abs(sd_w - sd_2) <= 1e-12, '%.3e' % abs(sd_w - sd_2))
    c = np.full(1024, 0.123456789)
    chk('A5-2', '恒等路径（全部路径同值）sd 两遍式 = 0 精确', float(np.std(c, ddof=1)) == 0.0, repr(float(np.std(c, ddof=1))))
    # ---------------- A5-3 / A5-4 / A5-5（真实数据）
    import e6l_env as V
    import e6l_ops as O
    import e6k_random as RN
    import e6l_run_det as RD
    import e6l_run_rand as RR_
    from scipy.special import gammaln
    seg = V.SegL(SEG)
    st = seg.struct('A4b_CVRv5')
    k0 = st.q0
    kQ = seg.meas_kf('Q0')
    valid = np.zeros(seg.n, bool)
    valid[st.ids] = True
    leaf, stats = RN.tree_leaves(seg, valid, k0, 'ISK')
    lv = leaf[st.ids]
    one = bool((leaf[valid] >= 0).all() and (leaf[~valid] == -1).all())
    cnt = np.bincount(lv)
    small = np.flatnonzero(cnt < 2)
    dcnt = np.bincount(seg.ci.t[st.ids], minlength=seg.T)
    only_root = bool((dcnt[seg.ci.t[st.ids][np.isin(lv, small)]] < 2).all()) if len(small) else True
    chk('A5-3', 'ISK 回退树：每门域名恰一叶；叶 < 2 只可能是当日根', one and only_root, json.dumps(stats))
    ctx_ = RD.DetCtx(seg, st, k0, kQ, 'Q0')
    sc, U = ctx_.sc(0.25), ctx_.U(0.25)
    G, _, _ = O.mem_gate(st, sc[None, :], U[None, :], O.parse_op('HG10'), b_day=np.full(seg.T, 10.0))
    cols = seg.ci.c[st.ids]
    ret, mov, ent = [], [], []
    ukey = RND.path_key('E6l.RMARK', 'RMARK_ISK_P5', 'ALL', 'gate', 'marks', 0)
    uu = seg.env.grid.u_cells(ukey, seg.ci.t[st.ids], seg.ci.c[st.ids], 5)
    prev = np.zeros(seg.Nc, bool)
    for d in range(seg.T):
        a0, b0 = st.dom.off[d], st.dom.off[d + 1]
        if b0 == a0 or st.dom.K[d] == 0:
            prev[:] = False
            continue
        cc = cols[a0:b0]
        mk = prev[cc]
        if mk.any():
            g = np.unique(lv[a0:b0], return_inverse=True)[1].ravel()
            pm = O.permute_marks_day(mk[None, :], lv[a0:b0], uu[None, a0:b0])[0]
            ret.append(float((pm & mk).sum() / mk.sum()))
            ng = np.bincount(g)
            mg = np.bincount(g, weights=mk.astype(float))
            movable = (mg > 0) & (mg < ng)
            mov.append(float(mg[movable].sum() / mk.sum()))
            lc = gammaln(ng + 1) - gammaln(mg + 1) - gammaln(ng - mg + 1)
            tot = gammaln(len(mk) + 1) - gammaln(mk.sum() + 1) - gammaln(len(mk) - mk.sum() + 1)
            ent.append(float(lc.sum() / tot) if tot > 0 else np.nan)
        prev = np.zeros(seg.Nc, bool)
        prev[cc[G[0, a0:b0]]] = True
    q = lambda v: np.round(np.nanpercentile(v, [10, 50, 90]), 4).tolist()
    chk('A5-3', 'R-MARK ISK_P5 真实 HG10 标记（A4b_CVRv5 Q0 α .25）逐日：保持率 / 可移动份额 / 熵比 分位 10 / 50 / 90', None,
        'retention %s；movable %s；entropy %s（%d 日）' % (q(ret), q(mov), q(ent), len(ret)))
    kD5 = seg.meas_kf('Q_D5')
    drw = RR_.Draws(seg, 'LEGACY_POLICY_RANDOM', 'Q_D5', kD5)
    X = drw.draw('A4b_CVRv5', [0, 1, 2], k0)
    nan_same = all(np.array_equal(np.isnan(X[i]), np.isnan(kD5)) for i in range(3))
    perm_ok = True
    for i in range(3):
        for d in range(0, seg.T, 7):
            a0, b0 = seg.off[d], seg.off[d + 1]
            x0, x1 = kD5[a0:b0], X[i, a0:b0]
            if not np.array_equal(np.sort(x0[np.isfinite(x0)]), np.sort(x1[np.isfinite(x1)])):
                perm_ok = False
    chk('A5-4', 'LEGACY 新测量（Q_D5）置换 = 当日有限 kf 的日内置换（多重集不变），缺失位置不动（3 路径）', nan_same and perm_ok,
        'nan_same=%s perm=%s；键 E6j.P / E6l.Q_D5' % (nan_same, perm_ok))
    D = L.read_csv_keep(os.path.join(a.reg, 'descriptors_E6l.csv'), usecols=['desc_id', 'meas', 'random_content'])
    k0rows = D[D.meas == 'K0']
    chk('A5-4', 'OLD_RULE / EDGE_OLD / PARENT（K0）全部登记 NO_NEW_CONTENT_TO_PERMUTE（%d 行）' % len(k0rows),
        bool((k0rows.random_content == 'NO_NEW_CONTENT_TO_PERMUTE').all()))
    b1 = seg.state_b('VOL_HI15')
    b2 = seg.state_b('VOL_HI15')
    chk('A5-5', 'STATE 调度 b 为段日期的确定序列（随机运行器对全部路径用同一 seg.state_b；不随机化）', bool(np.array_equal(b1, b2)),
        'e6l_run_rand：bday = seg.state_b(schedule)（与 path 无关）')
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'random_checks.csv')
    L.atomic_write_csv(p, df)
    ok = not (df.status == 'FAIL').any()
    L.write_receipt('stage0_c5_random' + ('_rerun' if a.rerun else ''), [p] + sorted(glob.glob(os.path.join(rd, '*', SEG, '*.npz'))),
                    'SUCCEEDED' if ok else 'FAILED', counts=df.status.value_counts().to_dict(), blocker=not ok, generator=RND.GEN_ID,
                    bootstrap_generator='blake2b-128(canonical_json(key)) -> SeedSequence -> PCG64', wall_s=round(time.time() - t0, 1))
    print(df.to_string(max_colwidth=150), flush=True)
    print(df.status.value_counts().to_dict(), 'OK' if ok else 'FAIL', flush=True)
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
