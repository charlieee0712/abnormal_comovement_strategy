# -*- coding: utf-8 -*-
"""E6l 随机层（plan §7.3 / §7.4 / §7.5；brief W10 / W13；附录 A5）。一段一个父进程：段环境与全部所需测量只加载一次 → fork 进程池
（写时复制共享）→ 任务 = (机制, 测量, 路径区间)；每个任务对该测量全部母体 × α × 算子的登记行逐路径重跑（名单 / DEV / 持仓 / 费用逐路径独立）。
提速（Stage 0 在真实数据上与参照实现逐位对拍）：e6l_fast 的 numba 门递推 / 第二关 / 多 H 账本；同一形成名单跨 H 共享（INV 例外：按 H 递推）；
同测量同机制全部对象共用一次内容置换（共同随机数）；P 条路径一批。
  LEGACY_POLICY_RANDOM  E6k Legacy 同键同机制（Q0 = E6k 'Q'：A4b_CVRv5 用 E6j B 机制 donor 映射，其余 P 机制；C1 / S / M = E6k 同）；
                        新测量 P 机制，成员 id = 'E6l.<测量>'（注入点：平滑 / 中性化 / 方向之后、规则之前；缺失位置不动）
  CONTENT_COND_ISK_P5   E6k NewCond 同键（'E6k.NEW', 测量键, 'COND_ISK', 'B5', 'content', path）；Q0 的测量键 = 'Q'；树依母体旧 K
  RMARK_UNIFORM_IID / RMARK_UNIFORM_P5 / RMARK_ISK_P5  真实内容；本路径 G_{t−1} 标记在分区内按 u 置换（组内计数守恒）；
                        键 ('E6l.RMARK', 机制, 'ALL', 'gate', 'marks', path)：全测量 / 母体 / α 共用 u 流（共同随机数）
每路径统计先按该路径自己的有效日求（plan §7.5），路径间再求均值 / 方差；状态调度用同一状态序列（不随机化，附录 A5-5）。
输出 randoms/<机制>/<段>/<测量>__p<起>_<数>.npz：desc / H / target（行）；s_net / n_net / s_gross / n_gross / s_turn / s_pos（行 × 路径）；
dsum / dsq / dcnt（行 × 日，net8 跨路径）；审计路径（全局路径 0 / 1）完整日账本 samp（行 × 2 × [net8, gross, pos, turn] × 日）；
fp（行 × 路径名单指纹）；回执 task_status/run_rand_<机制>_<段>_<测量>__p<起>_<数>。登记门同 e6l_run_det；后段过 post_gate。
--profile：真实新测量换成当日内置换内容（只测时，不写回执，写 TRIAL）。"""
import e6l_boot  # noqa: F401
import os
import sys
import time
import hashlib
import argparse
import resource
import multiprocessing as mp

import numpy as np
import numba as nb
import pandas as pd

import e6l_core as L
import e6l_env as V
import e6l_ops as O
import e6l_fast as FA
import e6l_run_det as RD
import e6j_fast as FJ
import e6j_random as RND

BATCH = 32
ANN = L.ANN
POLICY = ('LEGACY_POLICY_RANDOM', 'CONTENT_COND_ISK_P5')
RMARKS = ('RMARK_UNIFORM_IID', 'RMARK_UNIFORM_P5', 'RMARK_ISK_P5')
E6K_MEAS = {'Q0': 'Q', 'C1': 'C1', 'S': 'S', 'M': 'M'}
AUDIT_PATHS = (0, 1)
CTX = {}


@nb.njit(cache=True, error_model='numpy', nogil=True)
def accum_nb(out, hrow, k, s_net, n_net, s_gross, n_gross, s_turn, s_pos, dsum, dsq, dcnt):
    """out (nH, 4, T)；hrow[h] = 行号（−1 = 该 H 未登记）；路径列 k。"""
    nH = out.shape[0]
    T = out.shape[2]
    for h in range(nH):
        r = hrow[h]
        if r < 0:
            continue
        sn = 0.0
        nn = 0
        sg = 0.0
        ng = 0
        st = 0.0
        sp = 0.0
        for j in range(T):
            x = out[h, 3, j]
            if np.isfinite(x):
                sn += x
                nn += 1
                dsum[r, j] += x
                dsq[r, j] += x * x
                dcnt[r, j] += 1
            g = out[h, 0, j]
            if np.isfinite(g):
                sg += g
                ng += 1
            st += out[h, 2, j]
            sp += out[h, 1, j]
        s_net[r, k] = sn
        n_net[r, k] = nn
        s_gross[r, k] = sg
        n_gross[r, k] = ng
        s_turn[r, k] = st
        s_pos[r, k] = sp


def meas_key(meas):
    return E6K_MEAS.get(meas, meas)


class Draws(object):
    """一个 (机制, 测量) 的内容置换器（按母体给出 P × n 置换后的坏度）。"""

    def __init__(self, seg, mech, meas, kf, profile=False):
        self.seg, self.mech, self.meas, self.kf = seg, mech, meas, kf
        self._cond = {}
        self._leg = {}
        ci = seg.ci
        V_ = np.isfinite(kf)
        self.V = V_
        self.vt, self.vc = ci.t[V_], ci.c[V_]
        if mech == 'LEGACY_POLICY_RANDOM' and meas not in E6K_MEAS:
            self.asg = FJ.Assigner(kf[V_], self.vt.astype(np.int64))

    def legacy(self, mother):
        import e6k_random as RN
        import e6k_env as E
        mk = meas_key(self.meas)
        if self.meas not in E6K_MEAS:
            return None
        if mother not in self._leg:
            kf_hi = None
            if RN.legacy_kind(mother, mk) == 'B':
                import e6j_slot as SL
                src, mid, d = E.MEAS[mk]
                if d == 'hi':
                    kf_hi = self.kf
                else:
                    neu = SL.neu_of(self.seg.ctx, SL.full_frame(self.seg.ctx, self.seg.raw(mk)))
                    kf_hi = self.seg.env._dense_cells(SL.pct_dir(neu, 'hi'))
            self._leg[mother] = RN.Legacy(self.seg, mother, mk, self.kf, kf_hi)
        return self._leg[mother]

    def kind_of(self, mother):
        """同一置换可跨母体共用的键（P 机制全部母体相同；B 机制与 COND 按母体）。"""
        if self.mech == 'LEGACY_POLICY_RANDOM':
            if self.meas in E6K_MEAS:
                import e6k_random as RN
                return RN.legacy_kind(mother, meas_key(self.meas)) + ('' if RN.legacy_kind(mother, meas_key(self.meas)) == 'P' else mother)
            return 'P'
        return 'COND|' + mother

    def draw(self, mother, paths, k0):
        seg = self.seg
        out = np.full((len(paths), seg.n), np.nan)
        if self.mech == 'LEGACY_POLICY_RANDOM':
            lg = self.legacy(mother)
            for i, p in enumerate(paths):
                if lg is not None:
                    out[i] = lg.draw(p)
                else:
                    u = seg.env.grid.u_cells(RND.path_key('E6j.P', 'E6l.' + self.meas, 'P_production_v2', 'native', 'IID', p), self.vt, self.vc, 1)
                    out[i, self.V] = self.asg(u)
            return out
        import e6k_random as RN
        if mother not in self._cond:
            self._cond[mother] = RN.NewCond(seg, meas_key(self.meas), self.kf, k0, 'ISK', 5)
        nc = self._cond[mother]
        for i, p in enumerate(paths):
            out[i] = nc.draw(p)
        return out


def rmark_groups(seg, st, k0, mech):
    """R-MARK 分区（门域位置）：UNIFORM → 全 0；ISK → E6k 条件树叶（行业 > 旧 K3 > size3；每名恰一叶）逐日重编。"""
    N = len(st.ids)
    if mech != 'RMARK_ISK_P5':
        return np.zeros(N, np.int64), None
    import e6k_random as RN
    valid = np.zeros(seg.n, bool)
    valid[st.ids] = True
    leaf, stats = RN.tree_leaves(seg, valid, k0, 'ISK')
    raw = leaf[st.ids]
    grp = np.zeros(N, np.int64)
    off = st.dom.off
    for d in range(seg.T):
        a, b = off[d], off[d + 1]
        if b > a:
            grp[a:b] = np.unique(raw[a:b], return_inverse=True)[1].ravel()
    return grp, raw


def load_ctx(pname, mechs, measures, profile):
    t0 = time.time()
    seg = V.SegL(pname)
    AF = FA.AcctFast(seg)
    kfs = {}
    for m in measures:
        if m == 'K0':
            continue
        kf = seg.meas_kf(m)
        if profile:
            rng = np.random.default_rng(L.stable_seed_int('E6l.profile.rand', pname, m) % (2 ** 63))
            kf = RD.perm_within_day(seg, kf, rng)
        kfs[m] = kf
    structs = {}
    for form in V.E.P6:
        st = seg.struct(form)
        structs[form] = (st, FA.StructFast(st))
    FA.warmup()
    CTX.update(seg=seg, AF=AF, kfs=kfs, structs=structs, pname=pname, profile=profile, t_env=time.time() - t0)
    return CTX


def run_task(args):
    """子进程：一个 (机制, 测量, 路径区间) 任务。返回 (状态, 回执路径或错误)。"""
    mech, meas, path0, npaths, rows, out_dir, write_receipt = args
    try:
        return _run_task(mech, meas, path0, npaths, rows, out_dir, write_receipt)
    except Exception as e:                                                   # noqa: BLE001
        import traceback
        return ('FAILED', '%s: %s\n%s' % (type(e).__name__, e, traceback.format_exc()[-2000:]))


def _run_task(mech, meas, path0, npaths, rows, out_dir, write_receipt):
    t0 = time.time()
    seg, AF = CTX['seg'], CTX['AF']
    T, n = seg.T, seg.n
    R = pd.DataFrame(rows)
    R = R.sort_values(['mother', 'alpha', 'op', 'H']).reset_index(drop=True)
    nr = len(R)
    row_of = {(r.mother, float(r.alpha), r.op, int(r.H)): i for i, r in enumerate(R.itertuples())}
    targets = {}
    for i, r in enumerate(R.itertuples()):
        key = (r.mother, float(r.alpha), r.op) if r.op != 'INV10' else (r.mother, float(r.alpha), r.op, int(r.H))
        targets.setdefault(key, []).append(int(r.H))
    s_net = np.zeros((nr, npaths))
    n_net = np.zeros((nr, npaths), np.int32)
    s_gross = np.zeros((nr, npaths))
    n_gross = np.zeros((nr, npaths), np.int32)
    s_turn = np.zeros((nr, npaths))
    s_pos = np.zeros((nr, npaths))
    dsum = np.zeros((nr, T))
    dsq = np.zeros((nr, T))
    dcnt = np.zeros((nr, T), np.int32)
    aud = [p for p in AUDIT_PATHS if path0 <= p < path0 + npaths]
    samp = np.full((nr, len(aud), 4, T), np.nan) if aud else np.zeros((nr, 0, 4, T))
    fp = np.zeros((nr, npaths), np.uint64)
    kf = CTX['kfs'].get(meas)
    drw = Draws(seg, mech, meas, kf) if mech in POLICY else None
    mothers = sorted(set(R.mother))
    tim = dict(draw=0.0, gate=0.0, down=0.0, acct=0.0)
    rgrp = {}
    for b0 in range(0, npaths, BATCH):
        paths = list(range(path0 + b0, path0 + min(npaths, b0 + BATCH)))
        P = len(paths)
        cache_draw = {}
        for mother in mothers:
            st, SF = CTX['structs'][mother]
            k0 = st.q0
            ta = time.time()
            if mech in POLICY:
                kk = drw.kind_of(mother)
                if kk not in cache_draw:
                    cache_draw[kk] = drw.draw(mother, paths, k0)
                KF = cache_draw[kk]
            else:
                KF = None
            tim['draw'] += time.time() - ta
            if mech in RMARKS:
                if mother not in rgrp:
                    rgrp[mother] = rmark_groups(seg, st, k0, mech)[0]
                blk = 1 if mech == 'RMARK_UNIFORM_IID' else 5
                ids_t, ids_c = seg.ci.t[st.ids], seg.ci.c[st.ids]
                UU = np.vstack([seg.env.grid.u_cells(RND.path_key('E6l.RMARK', mech, 'ALL', 'gate', 'marks', p), ids_t, ids_c, blk)[None, :]
                                for p in paths])
            for a in sorted(set(R[R.mother == mother].alpha)):
                a = float(a)
                tg = time.time()
                if meas == 'K0' or a == 0.0:
                    Q = np.broadcast_to(k0[None, :], (P, n))
                elif KF is None:
                    Q = np.broadcast_to(np.where(np.isfinite(kf), (1 - a) * k0 + a * kf, k0)[None, :], (P, n))
                else:
                    Q = np.where(np.isfinite(KF), (1 - a) * k0[None, :] + a * KF, k0[None, :])
                SC = np.ascontiguousarray(st.gate_scores(Q))
                Oo, U = FA.order_U(SC, SF.off, SF.K)
                tim['gate'] += time.time() - tg
                for key, Hs in targets.items():
                    if key[0] != mother or key[1] != a:
                        continue
                    op = key[2]
                    rule = O.parse_op(op)
                    tg = time.time()
                    F = None
                    if mech in RMARKS:
                        be_day = np.full(seg.T, float(rule['b']) * st.bunit)
                        G = FA.rec_rmark(SC, Oo, U, SF.off, SF.K, SF.cols, be_day, SF.Nc, rgrp[mother], np.ascontiguousarray(UU))
                    elif rule['kind'] == 'NATIVE':
                        G = U
                    elif rule['kind'] in ('HG', 'STATE', 'LAG1'):
                        bday = seg.state_b(rule['schedule']) if rule['kind'] == 'STATE' else np.full(seg.T, rule['b'])
                        be_day = np.array([float(x) * st.bunit for x in bday])
                        G = FA.rec_single(SC, Oo, U, SF.off, SF.K, SF.cols, be_day, SF.Nc, rule['kind'] == 'LAG1')
                    elif rule['kind'] == 'DECAY':
                        be_day = np.full(seg.T, float(rule['b']) * st.bunit)
                        Lv = float(rule['L'])
                        G = FA.rec_decay(SC, U, SF.off, SF.K, SF.cols, be_day, SF.Nc, Lv if np.isfinite(Lv) else 1.0, bool(np.isinf(Lv)))
                    elif rule['kind'] == 'INV':
                        G, F = FA.rec_inv(SC, Oo, U, SF.off, SF.K, SF.cols, SF.ids, float(rule['b']) * st.bunit, int(key[3]), SF.Nc, SF.n,
                                          SF.kind, SF.drop, SF.base, SF.logm, SF.Traw, SF.kof)
                    else:
                        raise ValueError(op)
                    tim['gate'] += time.time() - tg
                    td = time.time()
                    if F is None:
                        F = SF.down(G)
                    tim['down'] += time.time() - td
                    tc = time.time()
                    Hs_ = np.asarray(sorted(set(Hs)), np.int64)
                    hrow = np.array([row_of[(mother, a, op, int(h))] for h in Hs_], np.int64)
                    for i, p in enumerate(paths):
                        out, nn = AF.run(F[i], Hs_)
                        kcol = p - path0
                        accum_nb(out, hrow, kcol, s_net, n_net, s_gross, n_gross, s_turn, s_pos, dsum, dsq, dcnt)
                        h8 = np.frombuffer(hashlib.blake2b(np.packbits(F[i]).tobytes(), digest_size=8).digest(), np.uint64)[0]
                        fp[hrow, kcol] = h8
                        if p in aud:
                            j = aud.index(p)
                            for hi, r in enumerate(hrow):
                                samp[r, j] = (out[hi, 3], out[hi, 0], out[hi, 1], out[hi, 2])
                    tim['acct'] += time.time() - tc
    od = os.path.join(out_dir, mech, CTX['pname'])
    os.makedirs(od, exist_ok=True)
    stem = '%s__p%d_%d' % (meas, path0, npaths)
    pth = os.path.join(od, stem + '.npz')
    L.atomic_write_npz(pth, desc=R.desc_id.values.astype(str), H=R.H.values.astype(np.int64), target=R.target_id.values.astype(str),
                       mother=R.mother.values.astype(str), alpha=R.alpha.values.astype(float), op=R.op.values.astype(str),
                       path0=np.array([path0]), n_paths=np.array([npaths]), audit_paths=np.array(aud, np.int64),
                       s_net=s_net, n_net=n_net, s_gross=s_gross, n_gross=n_gross, s_turn=s_turn, s_pos=s_pos, dsum=dsum, dsq=dsq, dcnt=dcnt,
                       samp=samp, fp=fp, dates=np.array([str(d)[:10] for d in seg.dates]))
    wall = time.time() - t0
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576.0
    rec = None
    if write_receipt:
        rec = L.write_receipt('run_rand_%s_%s_%s' % (mech, CTX['pname'], stem), [pth], 'SUCCEEDED', n_rows=nr, n_paths=npaths, path0=path0,
                              wall_s=round(wall, 1), maxrss_gb=round(rss, 2), t_draw=round(tim['draw'], 1), t_gate=round(tim['gate'], 1),
                              t_down=round(tim['down'], 1), t_acct=round(tim['acct'], 1), code_sha256=code_shas())
    return ('SUCCEEDED', dict(stem=stem, mech=mech, rows=nr, paths=npaths, wall=round(wall, 1), rss=round(rss, 2), receipt=rec,
                              t=dict((k, round(v, 1)) for k, v in tim.items())))


def code_shas():
    return {f: L.sha_file(os.path.join(L.CODE, f))[:16] for f in ('e6l_run_rand.py', 'e6l_fast.py', 'e6l_ops.py', 'e6l_env.py', 'e6l_state.py', 'e6l_core.py')}


def plan_tasks(RR, mechs, measures, path0, npaths, chunk):
    tasks = []
    for mech in mechs:
        for meas in measures:
            sub = RR[(RR.mechanism == mech) & (RR.meas == meas)]
            if not len(sub):
                continue
            rows = sub[['desc_id', 'meas', 'mother', 'alpha', 'H', 'op', 'target_id']].to_dict('records')
            for q0 in range(path0, path0 + npaths, chunk):
                tasks.append((mech, meas, q0, min(chunk, path0 + npaths - q0), rows))
    return tasks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--mechs', default=','.join(POLICY))
    ap.add_argument('--meas', default='ALL')
    ap.add_argument('--path0', type=int, default=0)
    ap.add_argument('--npaths', type=int, default=1024)
    ap.add_argument('--chunk', type=int, default=256)
    ap.add_argument('--workers', type=int, default=16)
    ap.add_argument('--profile', action='store_true')
    ap.add_argument('--reg', default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--forms', default='ALL')
    ap.add_argument('--stage0', action='store_true')
    ap.add_argument('--desc-regex', default=None)
    a = ap.parse_args()
    pname = a.segment
    if a.profile:
        reg = a.reg or os.path.join(L.TRIAL, 'a0', 'registry')
        out = a.out or os.path.join(L.TRIAL, 'profile_rand')
    elif a.stage0:                                   # Stage 0 A2-6：只允许 E6k 同构对象（已算已读），真实内容，写 stage0/，任务回执由 c5 写
        reg = a.reg or os.path.join(L.TRIAL, 'a0', 'registry')
        out = a.out or L.P('stage0', 'c5_random', 'randoms')
    else:
        reg = L.P('registry')
        out = L.P('randoms')
        ok, why = RD.registration_ok(reg)
        if not ok:
            raise RuntimeError('登记门：%s' % why)
        L.post_gate(pname, 'run_rand %s' % pname)
    mechs = a.mechs.split(',')
    RR = L.read_csv_keep(os.path.join(reg, 'randoms_E6l.csv'))
    RR = RR[RR.mechanism.isin(mechs)]
    if a.forms != 'ALL':
        RR = RR[RR.mother.isin(a.forms.split(','))]
    if a.desc_regex:
        RR = RR[RR.desc_id.str.match(a.desc_regex)]
    if a.stage0:
        Dq = L.read_csv_keep(os.path.join(reg, 'descriptors_E6l.csv'), usecols=['desc_id', 'e6k_equiv'])
        eq = dict(zip(Dq.desc_id, Dq.e6k_equiv))
        if not len(RR) or any(eq.get(d, 'NOT_APPLICABLE') == 'NOT_APPLICABLE' for d in RR.desc_id):
            raise RuntimeError('--stage0 只允许 E6k 同构对象')
    measures = sorted(RR.meas.unique()) if a.meas == 'ALL' else a.meas.split(',')
    tasks = plan_tasks(RR, mechs, measures, a.path0, a.npaths, a.chunk)
    print('%s：%d 个任务（机制 %s；测量 %d；路径 %d..%d；分片 %d）' % (pname, len(tasks), mechs, len(measures), a.path0, a.path0 + a.npaths - 1, a.chunk),
          flush=True)
    load_ctx(pname, mechs, measures, a.profile)
    if a.stage0 and pname not in L.DERIV_SEGS:
        raise RuntimeError('--stage0 只在推导段')
    print('环境 %.0fs；maxrss %.1f GB' % (CTX['t_env'], resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576.0), flush=True)
    order = sorted(range(len(tasks)), key=lambda i: -len(tasks[i][4]) * tasks[i][3])      # 大任务先发
    jobs = [tasks[i][:4] + (tasks[i][4], out, not (a.profile or a.stage0)) for i in order]
    ctx = mp.get_context('fork')
    bad = 0
    t0 = time.time()
    with ctx.Pool(a.workers, maxtasksperchild=4) as pool:
        for st, info in pool.imap_unordered(run_task, jobs):
            if st != 'SUCCEEDED':
                bad += 1
                print('FAILED', info, flush=True)
            else:
                print('done %s %s rows %d paths %d wall %.0fs rss %.1fGB %s' % (info['mech'], info['stem'], info['rows'], info['paths'], info['wall'],
                                                                             info['rss'], info['t']), flush=True)
    print('ALL_DONE %s bad=%d wall %.0fs' % (pname, bad, time.time() - t0), flush=True)
    return 0 if bad == 0 else 2


if __name__ == '__main__':
    sys.exit(main())
