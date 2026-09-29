# -*- coding: utf-8 -*-
"""E6k 随机层（plan §10.1 / §10.2；brief W13；执行端补充 X14 / X15）。一个任务 = (段, 母体, 测量, 机制, 路径区间)。
每条路径：置换新测量内容一次（同测量全部算子 / α / H 共用，共同随机数）→ 逐对象重跑完整算子（DEV / 持仓 / 费用逐路径独立）→ 逐路径统计。
批量：每批 BATCH 条路径；q 层算子（NATIVE / SZL / OWN / INC / SA / SM）与 HG 在 (P, n) 上一次过门（逐日 2D 稳定排序）；
A4b 第二关用 e6j_fast.stage2_fast（与 IR.dep_stage2_keep 逐位，E6j 已测）；PM / RP / LX / TREFIT / POST2 逐路径。
HG 每条路径从自身段首空状态递推（不借真实状态）；HG_ONLY 不在随机清单（NO_NEW_CONTENT_TO_PERMUTE）。
存储 randoms/<机制>/<段>/<母体>__<测量>__p<起>_<数>.npz：ann（行 × 路径 × [net8, gross, turn, pos] 年化 / 均值）、yr（逐年 net8 年化）、
dsum / dsq / dcnt（跨路径日和，供随机均值时间序列与 MC）、samp（分片前 2 条路径完整日账本）、fp（逐路径掩码指纹）。
登记门同 e6k_run_det；后段过 post_gate。--profile：真实新测量换成当日内置换后的内容再随机（只测时），写临时目录。"""
import e6k_boot  # noqa: F401
import os
import sys
import time
import hashlib
import argparse
import resource

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_env as E
import e6k_ops as O
import e6k_random as RN
import e6k_run_det as RD
import e6j_fast as FAST

BATCH = 32
QOPS = ('NATIVE', 'SZL3', 'SZL5', 'SZL3_OWN', 'SZL5_OWN', 'INC05', 'INC1')


def q_of(ctx, op, a):
    """q 层算子的 q（单路径）；SA 也在此（不属于门层）。"""
    k0, kf, seg = ctx.k0, ctx.kf, ctx.seg
    if op == 'NATIVE':
        return ctx.q_native(a)
    if op in ('SZL3', 'SZL5'):
        return O.szl_q(seg, k0, kf, a, int(op[3]))
    if op in ('SZL3_OWN', 'SZL5_OWN'):
        return O.szl_own_q(seg, k0, kf, a, int(op[3]))
    if op in ('INC05', 'INC1'):
        return O.inc_q(k0, ctx.d_inc(0.5 if op == 'INC05' else 1.0), a)
    base, rest = op.split('_', 1)
    b = int(rest[2:])
    if rest.startswith('SA'):
        return O.sa_q_native(k0, kf, a, b) if base == 'NATIVE' else O.sa_q_inc(k0, ctx.d_inc(1.0), a, b)
    raise ValueError(op)


def is_q_op(op):
    return op in QOPS or ('_SA' in op and not op.startswith('DOSE'))


def is_hg(op):
    return '_HG' in op and not op.startswith('HG_ONLY')


def run(pname, task, mech, path0, npaths, reg_dir, out_dir, profile=False):
    t0 = time.time()
    mother, meas = task.split('|')
    if not profile:
        ok, why = RD.registration_ok(reg_dir)
        if not ok:
            raise RuntimeError('登记门：%s' % why)
        K.post_gate(pname, 'run_rand %s %s' % (task, mech))
    RR = pd.read_csv(os.path.join(reg_dir, 'randoms_E6k.csv'))
    RR = RR[(RR.task == task) & (RR.mechanism == mech) & RR.alias_of.isna()]
    if not len(RR):
        return 0
    seg = E.Seg(pname)
    st = seg.struct(mother)
    st.stage2 = FAST.stage2_fast
    k0 = st.q0
    T = seg.T
    kf = kf2 = None
    if meas == 'SM':
        kf, kf2 = seg.kf('S'), seg.kf('M')
    else:
        kf = seg.kf(meas)
    if profile:
        rng = np.random.default_rng(K.stable_seed_int('E6k.profile.rand', pname, task) % (2 ** 63))
        kf = RD._perm_within_day(seg, kf, rng)
        if kf2 is not None:
            kf2 = RD._perm_within_day(seg, kf2, rng)
    # ---- 置换器
    if mech == 'LEGACY_POLICY_RANDOM':
        kf_hi = None
        if RN.legacy_kind(mother, meas) == 'B' and kf2 is None:
            import e6j_slot as SL
            src, mid, d = E.MEAS[meas]
            if d == 'hi':
                kf_hi = kf
            else:
                neu = SL.neu_of(seg.ctx, SL.full_frame(seg.ctx, seg.raw(meas)))
                kf_hi = seg.env._dense_cells(SL.pct_dir(neu, 'hi'))
        perm = RN.Legacy(seg, mother, meas, kf, kf_hi, kf2)
        gen = 'E6j R-MATCH-SRC replica (%s)' % RN.legacy_kind(mother, meas)
    else:
        if mech.startswith('NEW_COND_ISK'):
            subset, block = 'ISK', (1 if mech.endswith('IID') else 5)
        else:
            subset, block = mech.replace('EIGHT_SUBSET_', ''), 5
        perm = RN.NewCond(seg, meas, kf, k0, subset, block, kf2)
        gen = 'E6k.NEW subset=%s block=%d' % (subset, block)
    base = RD.Ctx(seg, st, k0, kf, kf2)
    SE = seg.SE
    # ---- 行 = (对象, H)
    rows = []
    for r in RR.itertuples():
        for H in str(r.Hs).split('|'):
            rows.append((r.desc_id, r.op, float(r.alpha), int(H)))
    nr = len(rows)
    years = pd.to_datetime(pd.Index(seg.dates).astype(str)).year.values
    yl = sorted(set(years))
    ann = np.full((nr, npaths, 4), np.nan)
    yr = np.full((nr, npaths, len(yl)), np.nan)
    dsum = np.zeros((nr, T))
    dsq = np.zeros((nr, T))
    dcnt = np.zeros((nr, T), np.int32)
    nsamp = min(2, npaths)
    samp = np.full((nr, nsamp, 4, T), np.nan)
    fp = np.zeros((nr, npaths), np.uint64)
    objs = sorted(set((op, a) for _, op, a, _ in rows))
    t_perm = t_op = t_acc = 0.0
    for b0 in range(0, npaths, BATCH):
        ps = list(range(path0 + b0, path0 + min(npaths, b0 + BATCH)))
        tp = time.time()
        draws = [perm.draw(p) for p in ps]
        t_perm += time.time() - tp
        to = time.time()
        ctxs = []
        for dr in draws:
            c = RD.Ctx.__new__(RD.Ctx)
            c.__dict__.update(base.__dict__)
            c._c = {k: v for k, v in base._c.items() if k in ('legal', 'key0', 's1_old') or (isinstance(k, tuple) and k[0] == 'lay')}
            c.facts = {}
            if kf2 is None:
                c.kf = dr
            else:
                c.kf, c.kf2 = dr
            ctxs.append(c)
        kept = {}
        # q 层：批量过门
        for op, a in objs:
            if is_q_op(op):
                Q = np.vstack([q_of(c, op, a)[None, :] for c in ctxs])
                kept[(op, a)] = st.kept(Q)
            elif is_hg(op):
                bse, rest = op.split('_', 1)
                bb = int(rest[2:])
                SC = np.vstack([st.gate_scores(c.q_base(bse, a)[None, :]) for c in ctxs])
                G = O.hg_gate(st, SC, bb * st.bunit, base.tid_ids)
                kept[(op, a)] = st.down(G)
        for (op, a), Kk in list(kept.items()):                        # 原生子名单给 RP / LX / PM 复用（避免逐路径重算）
            if op == 'NATIVE':
                for i, c in enumerate(ctxs):
                    c._c[('child', a)] = Kk[i]
        for (op, a) in objs:
            if (op, a) in kept:
                continue
            kept[(op, a)] = np.vstack([c.kept(op, a)[None, :] for c in ctxs])
        t_op += time.time() - to
        ta = time.time()
        for j, (did, op, a, H) in enumerate(rows):
            Kk = kept[(op, a)]
            for i, p in enumerate(ps):
                ids = np.flatnonzero(Kk[i])
                t, c_ = seg.ci.t[ids], seg.ci.c[ids]
                led = SE.pnl(t, c_, SE.dev(t, c_), (H,), 8.0)[H]
                g, pos, tu, n8 = led
                k = p - path0
                ann[j, k] = (np.nanmean(n8) * K.ANN, np.nanmean(g) * K.ANN, np.mean(tu), np.mean(pos))
                for yi, y in enumerate(yl):
                    m = years == y
                    yr[j, k, yi] = np.nanmean(n8[m]) * K.ANN if np.isfinite(n8[m]).any() else np.nan
                f = np.isfinite(n8)
                dsum[j, f] += n8[f]
                dsq[j, f] += n8[f] ** 2
                dcnt[j, f] += 1
                if k < nsamp:
                    samp[j, k] = (n8, g, pos, tu)
                fp[j, k] = np.frombuffer(hashlib.blake2b(np.packbits(Kk[i]).tobytes(), digest_size=8).digest(), np.uint64)[0]
        t_acc += time.time() - ta
    od = os.path.join(out_dir, mech, pname)
    os.makedirs(od, exist_ok=True)
    stem = '%s__%s__p%d_%d' % (mother, meas, path0, npaths)
    pth = os.path.join(od, stem + '.npz')
    K.atomic_write_npz(pth, desc=np.array([r[0] for r in rows]), op=np.array([r[1] for r in rows]), alpha=np.array([r[2] for r in rows]),
                       H=np.array([r[3] for r in rows]), path0=np.array([path0]), n_paths=np.array([npaths]), years=np.array(yl),
                       ann=ann, yr=yr, dsum=dsum, dsq=dsq, dcnt=dcnt, samp=samp, fp=fp,
                       dates=np.array([str(d)[:10] for d in seg.dates]), generator=np.array([gen]))
    wall = time.time() - t0
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576.0
    if not profile:
        K.write_receipt('run_rand_%s_%s_%s' % (mech, pname, stem), [pth], 'SUCCEEDED', n_rows=nr, n_paths=npaths, wall_s=round(wall, 1),
                        maxrss_gb=round(rss, 2), generator=gen, t_perm=round(t_perm, 1), t_op=round(t_op, 1), t_acct=round(t_acc, 1))
    print('%s %s %s p%d+%d: %d 行；wall %.0fs（置换 %.0f / 算子 %.0f / 账户 %.0f）；maxrss %.1f GB' % (
        pname, task, mech, path0, npaths, nr, wall, t_perm, t_op, t_acc, rss), flush=True)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--task', required=True)
    ap.add_argument('--mech', required=True)
    ap.add_argument('--path0', type=int, default=0)
    ap.add_argument('--npaths', type=int, default=1024)
    ap.add_argument('--profile', action='store_true')
    ap.add_argument('--reg', default=None)
    a = ap.parse_args()
    if a.profile:
        reg = a.reg or os.path.join(K.TRIAL, 'a0', 'registry')
        out = os.path.join(K.TRIAL, 'profile_rand')
    else:
        reg = K.P('registry')
        out = K.P('randoms')
    return run(a.segment, a.task, a.mech, a.path0, a.npaths, reg, out, profile=a.profile)


if __name__ == '__main__':
    sys.exit(main())
