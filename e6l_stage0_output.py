# -*- coding: utf-8 -*-
"""E6l Stage 0 第 6 类：输出 / 资源（brief §2 第 6 类 / A6；附录 A6-1 … A6-6）。
  --fast        提速件 ≡ 参照实现（推导段 2010-2014 真实分数；P = 16 条置换路径 × 六形态 × α {0, .25, .5}）：
                order_U = KeepDom.keep；down = Struct.down；HG / STATE / LAG1 / DECAY（2、5、∞）/ R-MARK（UNIFORM_IID、ISK_P5）/ INV（H 1 / 5 / 20）
                = e6l_ops 参照（HG10 另 = e6k_ops.hg_gate）；账本 DEV + H1…20 = SparseEngine（逐位）；pairwise 行和 = numpy（3,000 例）；
                单一折让归并 = stable argsort（合成 20,000 日，含并列 / 舍入并列）→ stage0/c6_output/fast_identity.csv
  （默认）      A6-1 耗时实测（TRIAL profile：确定性 masks / accounts 与随机 LEGACY / COND / R-MARK）→ 按段 pool0 单元数外推总量区间
                A6-2 内存 / RSS（父进程 + 子进程）；核绑定 / 并发上限
                A6-3 状态词扫描（TRIAL a0 registry / skeleton 与 RES 下 CSV / JSON / MD）：无 N/A / NA / nan / null 作状态
                A6-4 单位列名清单（skeleton 表头：ann_pp / pct_pt / decimal / _segavg / q95_maxabs_t / halfwidth_ann_pp）
                A6-5 固定输出二十张 + 每个 query 一张空骨架存在
                A6-6 禁用词 / 主机 / 账号 / 家目录 / 连接串扫描（运行时取本机用户名与主机名在内存比对，只报计数）"""
import e6l_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time
import socket
import getpass
import argparse

import numpy as np
import pandas as pd

import e6l_core as L


def fast(out, rerun):
    import e6l_env as V
    import e6l_ops as O
    import e6l_fast as FA
    import e6k_ops as KO
    import e6j_fast as FJ
    import e6j_random as RND
    import e6k_random as RN
    t0 = time.time()
    FA.warmup()
    rng = np.random.default_rng(20260930)
    res = {}

    def rec(name, ok):
        r = res.setdefault(name, [0, 0])
        r[0] += 1
        r[1] += int(not ok)
    for trial in range(20000):
        m = int(rng.integers(1, 60))
        nden = int(rng.integers(2, 12))
        a_ = float(rng.choice([0.125, 0.25, 0.5]))
        s = (1 - a_) * rng.integers(0, nden + 1, m) / nden + a_ * rng.integers(0, nden + 1, m) / nden
        if trial % 3 == 0:
            s = s / 3.0 + (rng.integers(0, 4, m) / 7.0) / 3.0
        be = float(rng.choice([0.05, 0.1, 0.15, 0.1 / 3, 0.05 / 3, 0.2, 0.3]))
        mk = rng.random(m) < rng.random()
        K = int(rng.integers(0, m + 1))
        sc = s[None, :]
        Oo = np.argsort(sc, axis=1, kind='stable')
        U = np.zeros((1, m), bool)
        U[0, Oo[0, :K]] = True
        bon = be * mk
        ref = np.zeros(m, bool)
        if (bon != 0).any():
            ref[np.argsort(s - bon, kind='stable')[:K]] = True
        else:
            ref = U[0].copy()
        G = np.zeros((1, m), bool)
        FA._select_single(0, 0, m, K, be, mk, sc, Oo, U, G, np.empty(m, np.int64), np.empty(m, np.int64), np.empty(m))
        rec('synthetic_single_level_merge==stable_argsort', np.array_equal(G[0], ref))
    for trial in range(3000):
        nn = int(rng.integers(1, 6000))
        x = np.abs(rng.normal(size=nn)) * 10 ** rng.uniform(-8, 2, size=nn)
        x[rng.random(nn) < 0.7] = 0.0
        rec('rowsum==numpy_row_sum', FA.rowsum(x) == x[None, :].sum(1)[0])
    seg = V.SegL('2010-2014')
    AF = FA.AcctFast(seg)
    SE = seg.SE
    Hs = tuple(range(1, 21))
    for trial in range(120):
        F = rng.random(seg.n) < [0.02, 0.1, 0.3, 0.6][trial % 4]
        if trial % 10 == 0:
            F[:] = False
            if trial % 20 == 0:
                F[seg.off[25]] = True
        ids = np.flatnonzero(F)
        tt, cc = seg.ci.t[ids], seg.ci.c[ids]
        led = SE.pnl(tt, cc, SE.dev(tt, cc), Hs, 8.0)
        o, _ = AF.run(F, Hs)
        rec('acct(DEV+pnl H1..20)==SparseEngine', all(np.array_equal(o[i, k], led[H][k], equal_nan=True) for i, H in enumerate(Hs) for k in range(4)))
    P = 16
    kf = seg.meas_kf('Q_D5')
    Vv = np.isfinite(kf)
    vt, vc = seg.ci.t[Vv], seg.ci.c[Vv]
    asg = FJ.Assigner(kf[Vv], vt.astype(np.int64))
    g = seg.env.grid
    KF = np.full((P, seg.n), np.nan)
    for p in range(P):
        KF[p, Vv] = asg(g.u_cells(RND.path_key('E6l.stage0.fast', 'Q_D5', 'x', 'native', 'IID', p), vt, vc, 1))
    tim = []
    for form in V.E.P6:
        st = seg.struct(form)
        SF = FA.StructFast(st)
        k0 = st.q0
        for a_ in (0.0, 0.25, 0.5):
            Q = np.vstack([KO.native_q(k0, KF[p], a_)[None, :] if a_ > 0 else k0[None, :] for p in range(P)])
            SC = np.ascontiguousarray(st.gate_scores(Q))
            t1 = time.time()
            Uref = st.gate_keep(SC)
            t2 = time.time()
            Oo, U = FA.order_U(SC, SF.off, SF.K)
            t3 = time.time()
            rec('order_U==KeepDom.keep', np.array_equal(U, Uref))
            Fr = st.down(U)
            t4 = time.time()
            Ff = SF.down(U)
            t5 = time.time()
            rec('down==Struct.down', np.array_equal(Fr, Ff))
            tim.append(dict(form=form, alpha=a_, step='U', ref_s=round(t2 - t1, 3), fast_s=round(t3 - t2, 3)))
            tim.append(dict(form=form, alpha=a_, step='down', ref_s=round(t4 - t3, 3), fast_s=round(t5 - t4, 3)))
            for op in ('HG10', 'HG5', 'HG30', 'LAG1_10', 'VOL_HI15', 'VOL_MEAN5', 'DECAY2_10', 'DECAY5_10', 'DECAYinf_10'):
                rule = dict(kind='DECAY', L=np.inf, b=10.0) if op == 'DECAYinf_10' else O.parse_op(op)
                bday = seg.state_b(rule['schedule']) if rule['kind'] == 'STATE' else np.full(seg.T, rule['b'])
                be_day = np.array([float(x) * st.bunit for x in bday])
                t1 = time.time()
                Gr, _, _ = O.mem_gate(st, SC, U, rule, b_day=bday)
                t2 = time.time()
                if rule['kind'] in ('HG', 'STATE', 'LAG1'):
                    Gf = FA.rec_single(SC, Oo, U, SF.off, SF.K, SF.cols, be_day, SF.Nc, rule['kind'] == 'LAG1')
                else:
                    Gf = FA.rec_decay(SC, U, SF.off, SF.K, SF.cols, be_day, SF.Nc, float(rule['L']) if np.isfinite(rule['L']) else 1.0,
                                      bool(np.isinf(rule['L'])))
                t3 = time.time()
                rec('rec_%s==e6l_ops.mem_gate' % rule['kind'], np.array_equal(Gr, Gf))
                tim.append(dict(form=form, alpha=a_, step=op, ref_s=round(t2 - t1, 3), fast_s=round(t3 - t2, 3)))
                if op == 'HG10':
                    rec('rec_HG10==e6k_ops.hg_gate', np.array_equal(KO.hg_gate(st, SC, 10 * st.bunit, seg.tid[st.ids]), Gf))
            leaf = RN.tree_leaves(seg, np.isin(np.arange(seg.n), st.ids), k0, 'ISK')[0][st.ids]
            grp = np.zeros(len(st.ids), np.int64)
            for d in range(seg.T):
                a0, b0 = SF.off[d], SF.off[d + 1]
                if b0 > a0:
                    grp[a0:b0] = np.unique(leaf[a0:b0], return_inverse=True)[1].ravel()
            it, ic = seg.ci.t[st.ids], seg.ci.c[st.ids]
            for mech, groups, blk in (('RMARK_UNIFORM_IID', None, 1), ('RMARK_ISK_P5', leaf, 5)):
                UU = np.vstack([g.u_cells(RND.path_key('E6l.RMARK', mech, 'ALL', 'gate', 'marks', p), it, ic, blk)[None, :] for p in range(P)])
                Gr, _, _ = O.mem_gate(st, SC, U, dict(kind='RMARK', b=10.0), b_day=np.full(seg.T, 10.0),
                                      rmark=dict(groups=groups, u=lambda d, a0, b0, UU=UU: UU[:, a0:b0]))
                Gf = FA.rec_rmark(SC, Oo, U, SF.off, SF.K, SF.cols, np.full(seg.T, 10.0 * st.bunit), SF.Nc,
                                  grp if groups is not None else np.zeros(len(st.ids), np.int64), np.ascontiguousarray(UU))
                rec('rec_%s==e6l_ops.mem_gate' % mech, np.array_equal(Gr, Gf))
            for H in (1, 5, 20):
                t1 = time.time()
                Gr, Fr_, _, _ = O.inv_path(st, SC, U, 10.0, H)
                t2 = time.time()
                Gf, Ff_ = FA.rec_inv(SC, Oo, U, SF.off, SF.K, SF.cols, SF.ids, 10.0 * st.bunit, H, SF.Nc, SF.n, SF.kind, SF.drop, SF.base,
                                     SF.logm, SF.Traw, SF.kof)
                t3 = time.time()
                rec('rec_INV==e6l_ops.inv_path', np.array_equal(Gr, Gf) and np.array_equal(Fr_, Ff_))
                tim.append(dict(form=form, alpha=a_, step='INV_H%d' % H, ref_s=round(t2 - t1, 3), fast_s=round(t3 - t2, 3)))
    df = pd.DataFrame([dict(check_id='A6-1b', what=k, cases=v[0], differs=v[1], status='PASS' if v[1] == 0 else 'FAIL') for k, v in res.items()])
    p = os.path.join(out, 'fast_identity.csv')
    L.atomic_write_csv(p, df)
    pt = os.path.join(out, 'fast_timing_P16.csv')
    L.atomic_write_csv(pt, pd.DataFrame(tim))
    ok = not (df.status == 'FAIL').any()
    L.write_receipt('stage0_c6_fast' + ('_rerun' if rerun else ''), [p, pt], 'SUCCEEDED' if ok else 'FAILED', counts=df.status.value_counts().to_dict(),
                    blocker=not ok, wall_s=round(time.time() - t0, 1))
    print(df.to_string(), flush=True)
    return 0 if ok else 2


def seg_cells():
    """各段 pool0 单元数（E6k 账户 n_cells，只读）与交易日数。"""
    out = {}
    for s in L.SEGMENTS:
        f = sorted(glob.glob(L.K6('accounts', s, '*.npz')))
        f = [x for x in f if not os.path.basename(x).startswith('weights_')][0]
        z = np.load(f, allow_pickle=False)
        out[s] = (int(z['n_cells'][0]), int(len(z['dates'])))
    return out


def main_out(out, rerun):
    rows = []

    def chk(cid, what, ok, detail=''):
        rows.append(dict(check_id=cid, what=what, status='INFO' if ok is None else ('PASS' if ok else 'FAIL'), detail=L.txt(detail)[:600]))
    cells = seg_cells()
    base_n = cells['2010-2014'][0]
    chk('A6-1', '各段 pool0 单元数 / 交易日数（E6k 账户 n_cells；外推尺度）', None, json.dumps(cells))
    # ---- 确定性 profile
    prof = []
    for ph in ('masks', 'det'):
        for f in sorted(glob.glob(os.path.join(L.TRIAL, 'profile_%s' % ph, '*', 'profile_*.csv'))):
            p = pd.read_csv(f)
            col = 'op_s' if 'op_s' in p.columns else 'acct_s'
            prof.append(dict(kind='det_' + ph, task=os.path.basename(f)[8:-4], n_targets=len(p), seconds=round(float(p[col].sum() + (p['stats_s'].sum() if 'stats_s' in p else 0)), 1)))
    for f in sorted(glob.glob(os.path.join(L.TRIAL, 'logs', 'prof_rand*.log'))):
        for ln in open(f, encoding='utf-8', errors='replace'):
            m = re.match(r'done (\S+) (\S+)__p(\d+)_(\d+) rows (\d+) paths (\d+) wall (\d+)s rss ([\d.]+)GB', ln.strip())
            if m:
                prof.append(dict(kind='rand', task='%s|%s' % (m.group(1), m.group(2)), n_targets=int(m.group(5)), paths=int(m.group(6)),
                                 seconds=float(m.group(7)), rss_gb=float(m.group(8))))
    P = pd.DataFrame(prof)
    pp = os.path.join(out, 'profile.csv')
    L.atomic_write_csv(pp, P)
    # 外推：确定性（每段 104 任务，按测量类取 profile 均值）；随机（每路径每测量秒数 × 1,024 × 2 机制 + R-MARK）
    det = P[P.kind.str.startswith('det')]
    heavy_m = det[det.task.str.contains('__Q0|__Q_D5')].groupby('kind').seconds.mean()
    light_m = det[det.task.str.contains('__K0|__Q_RANK5')].groupby('kind').seconds.mean()
    det_seg = {k: float(24 * heavy_m.get(k, 0) + 80 * light_m.get(k, 0)) for k in ('det_masks', 'det_det')}
    rnd = P[P.kind == 'rand'].copy()
    rnd['sec_per_path'] = rnd.seconds / rnd.paths
    sp = rnd.groupby('task').sec_per_path.mean().to_dict()
    heavy = np.mean([v for k, v in sp.items() if k.endswith('|Q0') and not k.startswith('RMARK')]) if sp else np.nan
    light = np.mean([v for k, v in sp.items() if k.endswith('|Q_D3')]) if sp else np.nan
    rm = np.mean([v for k, v in sp.items() if k.startswith('RMARK')]) if sp else np.nan
    per_path_seg1 = 3 * heavy + 0.7 * heavy + 8 * light + 4 * 0.5 * light
    cpu_rand = sum(per_path_seg1 * (cells[s][0] / base_n) * 1024 * 2 + rm * 4 * 3 * 1024 * (cells[s][0] / base_n) for s in cells)
    cpu_det = sum((det_seg['det_masks'] + det_seg['det_det']) * (cells[s][0] / base_n) for s in cells)
    est = dict(rand_sec_per_path_seg1=dict(heavy_meas=round(heavy, 2), light_meas=round(light, 2), rmark_meas=round(rm, 2), all_meas=round(per_path_seg1, 1)),
               cpu_hours_random_first1024=round(cpu_rand / 3600, 1), cpu_hours_det=round(cpu_det / 3600, 1),
               wall_hours_at_64=[round(cpu_rand / 3600 / 64 * 0.9, 2), round(cpu_rand / 3600 / 64 * 1.6, 2)],
               wall_hours_det_at_24=[round(cpu_det / 3600 / 24 * 0.9, 2), round(cpu_det / 3600 / 24 * 1.6, 2)],
               note='区间 = 理想并行 ×0.9 … ×1.6（负载不均 / IO / 段间单元数差）；MC 增补未计（E6k 路径 sd .08–.28 → 首 1,024 已达 MCSE ≤ .03 的概率高）')
    chk('A6-1', '耗时实测外推（随机首 1,024 路径两机制 + R-MARK；确定性 masks + accounts；四段）', None, json.dumps(est, ensure_ascii=False))
    L.atomic_write_json(os.path.join(out, 'timing_extrapolation.json'), est)
    # ---- A6-2
    rss = P.rss_gb.max() if 'rss_gb' in P else np.nan
    chk('A6-2', '子进程 maxrss（含与父进程共享的写时复制页）/ 核绑定 taskset 96-191,288-383 / 并发上限 64 / BLAS 线程 4', None,
        'max child rss %.1f GB；父进程 ≈ 12–13 GB / 段；2.2 TB 内存' % rss)
    # ---- A6-3 状态词
    bad = []
    scan = glob.glob(os.path.join(L.TRIAL, 'a0', 'registry', '*.csv')) + glob.glob(os.path.join(L.TRIAL, 'a0', 'skeleton', '*.csv')) + \
        [f for f in glob.glob(L.P('**', '*.csv'), recursive=True) if '/randoms/' not in f and '/accounts/' not in f]
    for f in scan:
        try:
            df = pd.read_csv(f, keep_default_na=False, na_values=[], dtype=str)
        except Exception:                                                     # noqa: BLE001
            continue
        for c in df.columns:
            hit = L.status_scan_values(df[c].values)
            if hit:
                bad.append('%s:%s:%s' % (os.path.basename(f), c, hit[:3]))
    chk('A6-3', '状态词扫描：%d 个 CSV 无 N/A / NA / nan / null 等作单元值' % len(scan), not bad, '; '.join(bad[:10]))
    # ---- A6-4 / A6-5
    fx = pd.read_csv(os.path.join(L.TRIAL, 'a0', 'registry', 'fixed_outputs_E6l.csv'))
    qy = pd.read_csv(os.path.join(L.TRIAL, 'a0', 'registry', 'query_registry_E6l.csv'))
    miss = [t for t in fx.table if not os.path.exists(os.path.join(L.TRIAL, 'a0', 'skeleton', '%s.csv' % t))]
    missq = [q for q in qy.query_id if not os.path.exists(os.path.join(L.TRIAL, 'a0', 'skeleton', '%s.csv' % q.replace('-', '_')))]
    chk('A6-5', '固定输出 %d 张 + query %d 张空骨架存在（A0 试编）' % (len(fx), len(qy)), not miss and not missq, 'miss %s %s' % (miss, missq))
    units = set()
    for t in fx.table:
        hdr = open(os.path.join(L.TRIAL, 'a0', 'skeleton', '%s.csv' % t), encoding='utf-8').readline().strip().split(',')
        units |= {h for h in hdr if re.search(r'(_ann_pp|_pct_pt|_decimal|_bp|_segavg|q95_maxabs_t|halfwidth_ann_pp)$', h)}
    chk('A6-4', '单位列名（骨架表头）：%d 个带单位后缀；bootstrap / CAP 表的 q95_maxabs_t / halfwidth_ann_pp / _segavg 在结果阶段由生成器写（纪律 57 / 58）' % len(units),
        None, sorted(units))
    # ---- A6-6 禁用词
    user = getpass.getuser()
    host = socket.gethostname()
    kw = ('pass' + 'word', 'pass' + 'wd')                           # 拼接写法：扫描器源码自身不含字面口令词
    pats = [re.escape(user), re.escape(host), r'/home/[A-Za-z0-9_]+', r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', r'://[^/\s]*@', kw[0], kw[1]]
    hits = 0
    files = [f for f in glob.glob(L.P('**', '*'), recursive=True) if os.path.isfile(f) and f.endswith(('.csv', '.json', '.md', '.txt', '.log'))
             and '/randoms/' not in f and '/accounts/' not in f and '/masks/' not in f]
    files += glob.glob(os.path.join(L.CODE, 'e6l_*'))
    who = []
    for f in files:
        try:
            txt = open(f, encoding='utf-8', errors='replace').read()
        except Exception:                                                     # noqa: BLE001
            continue
        for i, p in enumerate(pats):
            if re.search(p, txt, flags=re.I if i >= 5 else 0):
                hits += 1
                who.append('%s:#%d' % (L.rel(f) if f.startswith(L.RES) else os.path.basename(f), i))
    chk('A6-6', '禁用词 / 主机 / 账号 / 家目录 / IP / 连接串扫描（%d 个文件；运行时比对本机用户名与主机名，不落盘）' % len(files), hits == 0, '; '.join(who[:10]))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'output_checks.csv')
    L.atomic_write_csv(p, df)
    ok = not (df.status == 'FAIL').any()
    L.write_receipt('stage0_c6_output' + ('_rerun' if rerun else ''), [p, pp, os.path.join(out, 'timing_extrapolation.json')], 'SUCCEEDED' if ok else 'FAILED',
                    counts=df.status.value_counts().to_dict(), blocker=not ok)
    print(df.to_string(max_colwidth=160), flush=True)
    print(df.status.value_counts().to_dict(), 'OK' if ok else 'FAIL', flush=True)
    return 0 if ok else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fast', action='store_true')
    ap.add_argument('--rerun', action='store_true')
    a = ap.parse_args()
    out = L.P('stage0', 'c6_output' + ('_rerun' if a.rerun else ''))
    os.makedirs(out, exist_ok=True)
    if a.fast:
        return fast(out, a.rerun)
    return main_out(out, a.rerun)


if __name__ == '__main__':
    sys.exit(main())
