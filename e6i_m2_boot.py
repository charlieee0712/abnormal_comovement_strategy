#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i M2 学习不确定性 (plan §8.2 末段; brief §5): 推导段 256 次时间块重采样, 每次重跑内层拟合 / λ 选择与外层账户。
只对 A0 的 M2 程序 (§7.1 代表) 与对应零修改; primary 变体 (net8 目标)。

重采样: 移动块 bootstrap (块长 20 个交易日, 循环), 对合并交易日历的日期给出重数 m_b(d); 训练权重 = (1/当日样本数) x m_b(d)。
同一个 b 用于该程序的全部 fold 与外层拟合 (两段共用同一日历 draw -> 2015-18 复用 2010-14 fold 分数时 b 对齐)。
账户走快速路径 (与 e6i_m2.Program.mask_with 在同一 z 上逐格相同, 每程序先锚; 不同则该程序回退慢路径):
  SLOT / ADD  -> e6i_randoms 的 ShuffleSpec 打分 / 保留管线 (z = M2 预测的 bad-score)
  SWAP        -> 固定真实 D (母体最差 m, 与 z 无关), 在候选域按 z 取最好 m_t
  VETO        -> 源 drop_SRC 的向量化 (有效 < 3k 当日全池剔; 否则保留 qcut 前缀)
稀疏引擎记账 (已锚)。输出 m2/<seg>/boot_<NN>.csv (程序 x b: 外层 Δnet8 与逐年动作) 与 bootfolds_<NN>.csv。
这张表是"固定历史上的程序学习不确定性"附表, 不产生新的市场历史, 不能当独立验证 (plan §8.2)。
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import time
import argparse
import traceback

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6i_ops as OP
import e6i_m2 as M2
import e6i_randoms as RD
import e6i_stage2 as S2
import e6f_core as F

N_BOOT = 256
BLOCK = 20
SEED = 20260923 + 256


def block_multiplicity(ncal, B, L, seed):
    """(B, ncal) 循环移动块 bootstrap 的日期重数。"""
    rng = np.random.default_rng(seed)
    out = np.zeros((B, ncal))
    nb = int(np.ceil(ncal / L))
    for b in range(B):
        st = rng.integers(ncal, size=nb)
        idx = (st[:, None] + np.arange(L)[None, :]).ravel()[:ncal] % ncal
        out[b] = np.bincount(idx, minlength=ncal)
    return out


class Fast(object):
    """一个 M2 程序的快速接入: accept(zM2 (T,Nc) 含 NaN) -> 单元 id (pool0 单元编号)。"""

    def __init__(self, R, P):
        self.R, self.P = R, P
        M, S, ci = P.M, P.S, R.ci
        self.M = R.mother(P.mn)
        role = P.role
        b = M2.HOME_BUDGET[P.role] if getattr(P, 'budget', None) is None else P.budget
        if role in ('SLOT', 'ADD_SCORE'):
            r = dict(route_id=P.route if role == 'SLOT' else 'RV', mother_id=P.mn, member_id=P.u_mid, role=role,
                     strength=b, policy='FALLBACK' if role == 'SLOT' else '', direction='high_bad',
                     direction_role='primary', descriptor_id='M2FAST|%s' % P.mn, H=5)
            spec, _, _, _ = RD.build_spec(R, r)
            self.spec = spec
        elif role == 'SWAP':
            zmem = np.where(P.dom, P.u + 0.5, np.nan)
            B2, _ = M.swap(zmem, b)
            D = ci.of(M.B & ~B2)
            self.keepB = ci.of(M.B) & ~D
            self.m_t = np.bincount(ci.t[D], minlength=ci.T)
            self.E = ci.of(P.dom)
        elif role == 'VETO_NEW':
            self.k = int(b)
            self.p0c = np.ones(ci.n, bool)
            self.B = ci.of(M.B)
        self.role = role

    def accept(self, zM2):
        R, ci = self.R, self.R.ci
        zc = zM2[ci.t, ci.c]
        if self.role in ('SLOT', 'ADD_SCORE'):
            return self.spec._child(zc[None, :])[0][0]
        if self.role == 'SWAP':
            ids = np.flatnonzero(self.E & np.isfinite(zc))
            o = np.lexsort((ci.c[ids], zc[ids], ci.t[ids]))
            ids = ids[o]
            tt = ci.t[ids]
            brk = np.flatnonzero(tt[1:] != tt[:-1]) + 1
            starts = np.r_[0, brk]
            lens = np.diff(np.r_[starts, len(ids)])
            pos = np.arange(len(ids)) - np.repeat(starts, lens)
            pick = ids[pos < self.m_t[tt]]
            # 当日无候选 (m_t 由真实 D 定, 真实当日若换了则候选必然有) -> 与 M.swap 同: 不换
            day_has = np.bincount(ci.t[pick], minlength=ci.T) > 0
            keep = self.keepB.copy()
            # 真实换了但 z 当日全缺的日子: M.swap 在 e 为空时不换 -> 该日保留原 B
            lost = ~day_has & (self.m_t > 0)
            if lost.any():
                keep |= self._orig_B_days(lost)
            out = np.zeros(ci.n, bool)
            out[np.flatnonzero(keep)] = True
            out[pick] = True
            return np.flatnonzero(out)
        if self.role == 'VETO_NEW':
            k = self.k
            days = np.isfinite(zc)
            dmask = np.bincount(ci.t[days], minlength=ci.T) > 0
            ids = np.flatnonzero(days)
            o = np.lexsort((ci.c[ids], zc[ids], ci.t[ids]))
            ids = ids[o]
            tt = ci.t[ids]
            n_t = np.bincount(tt, minlength=ci.T)
            Kt = np.array([int((F.qcut_group(int(n), k) <= k - 1).sum()) if n >= 3 * k else 0 for n in n_t])
            brk = np.flatnonzero(tt[1:] != tt[:-1]) + 1
            starts = np.r_[0, brk]
            lens = np.diff(np.r_[starts, len(ids)])
            pos = np.arange(len(ids)) - np.repeat(starts, lens)
            kept = np.zeros(ci.n, bool)
            kept[ids[pos < Kt[tt]]] = True
            drop = dmask[ci.t] & ~kept                     # 被改日: pool0 中未保留的全部剔 (含无值票)
            return np.flatnonzero(self.B & ~drop)
        raise ValueError(self.role)

    def _orig_B_days(self, days_bool):
        ci = self.R.ci
        return ci.of(self.M.B) & days_bool[ci.t]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshard', type=int, default=1)
    ap.add_argument('--boot', type=int, default=N_BOOT)
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    seg = a.segment
    t0 = time.time()
    FE.build_catalog()
    FE.CATALOG_IDS = {m['member_id'] for m in FE.CATALOG}
    I.set_protected_members(FE.protected_ids())
    dd = pd.read_csv(os.path.join(I.RES, 'registry', 'descriptors_A0.csv'), low_memory=False)
    progs = dd[dd.route_id == 'M2'].to_dict('records')[a.shard::a.nshard]
    if a.limit:
        progs = progs[:a.limit]
    S = I.seg_i(seg, warm=False)
    R = RD.RCtx(S, seg)
    RN = R.RN
    md = os.path.join(I.RES, 'm2', seg)
    seg_dates = np.asarray([int(x) for x in pd.DatetimeIndex(S.dates).strftime('%Y%m%d')])
    # 全局日历 = 两推导段日历之并 (M2 主程序各段落盘); 同一 b 在两段给同一日期同一重数
    cal = np.asarray(sorted(set(int(x) for s_ in I.DERIV_SEGS
                                for x in np.load(os.path.join(I.RES, 'm2', s_, 'calendar.npy')))))
    MULT = block_multiplicity(len(cal), a.boot, BLOCK, SEED)
    prev = None
    if seg == '2015-2018':
        pf = [os.path.join(I.RES, 'm2', '2010-2014', f) for f in os.listdir(os.path.join(I.RES, 'm2', '2010-2014'))
              if f.startswith('bootfolds_') and f.endswith('.csv')]
        prev = pd.concat([pd.read_csv(f) for f in pf], ignore_index=True) if pf else pd.DataFrame()
    print('段就绪 %.0fs; M2 boot %s shard %d/%d: %d 程序 x %d 次' % (time.time() - t0, seg, a.shard, a.nshard,
                                                                len(progs), a.boot), flush=True)
    rows, frows, anchors = [], [], []
    for gi, r in enumerate(progs):
        ts = time.time()
        key = M2.prog_key(r)
        try:
            P = M2.Program(S, RN, r)
            FA = Fast(R, P)
            pn = RN.ppnl(P.mn, P.H)
            parent_net8 = I.ann(pn[3])
            # 锚: 快速路径与慢路径在同一 z 上逐格相同
            smp = P.samples()
            if seg == '2010-2014':
                train_all = smp
            else:
                with np.load(os.path.join(I.RES, 'm2', '2010-2014', 'samples',
                                          key.replace('|', '__') + '.npz')) as z1:
                    train_all = {k: np.concatenate([z1[k], smp[k]]) for k in ('date', 'u', 'z', 'y')}
            years = sorted(set(P.years))
            last = years[-1]
            mdl = M2.fit_on(train_all, 1.0, False, P.basis_kind)
            zt = M2.predict_z(P, mdl, P.years == last)
            slow = R.ci.of(P.mask_with(zt))
            fast = np.zeros(R.ci.n, bool)
            fast[FA.accept(zt)] = True
            same = bool(np.array_equal(slow, fast))
            anchors.append(dict(program=key, fast_equals_slow=same, n_diff=int((slow != fast).sum())))
            if not same:
                FA = None
            year_first = {y: seg_dates[P.years == y][0] for y in years}
            cal_pos = {d: i for i, d in enumerate(cal)}
            tr_pos = np.array([cal_pos[d] for d in train_all['date']])
            _, inv, cnt = np.unique(train_all['date'], return_inverse=True, return_counts=True)
            base_w = 1.0 / cnt[inv]

            def account(zM2):
                if FA is not None:
                    ids = FA.accept(zM2)
                else:
                    ids = np.flatnonzero(R.ci.of(P.mask_with(zM2)))
                t, c = R.cells_tc(ids)
                w = R.SE.dev(t, c)
                g, p, u, n = R.SE.pnl(t, c, w, (P.H,), I.COST)[P.H]
                return I.ann(n) - parent_net8

            def fit_w(mask_rows, lam, mult):
                X = M2.basis(train_all['u'][mask_rows], train_all['z'][mask_rows], P.basis_kind)
                y = train_all['y'][mask_rows]
                wv = base_w[mask_rows] * mult[tr_pos[mask_rows]]
                keep = wv > 0
                return M2.standardize_fit(X[keep], y[keep], wv[keep], lam)

            for b in range(a.boot):
                mult = MULT[b]
                fold = {}
                for F_ in years:
                    mrow = M2.matured(train_all, year_first[F_], P.H, cal)
                    nd = len(np.unique(train_all['date'][mrow])) if mrow.any() else 0
                    if nd < M2.MIN_DATES:
                        continue
                    days = P.years == F_
                    scale = float(P.T) / max(int(days.sum()), 1)
                    for lam in M2.LAMS:
                        d8 = account(M2.predict_z(P, fit_w(mrow, lam, mult), days)) * scale
                        fold[(F_, lam)] = d8
                        frows.append(dict(program=key, b=b, fold_year=F_, lam=lam, d_net8_vs_parent=d8))
                if prev is not None and len(prev):
                    pp = prev[(prev.program == key) & (prev.b == b)]
                    for x in pp.itertuples():
                        fold[(int(x.fold_year), float(x.lam))] = x.d_net8_vs_parent
                zfull = np.full(P.u.shape, np.nan)
                acts = []
                for Y in [y for y in years if y >= M2.FIRST_YEAR]:
                    mrow = M2.matured(train_all, year_first[Y], P.H, cal)
                    nd = len(np.unique(train_all['date'][mrow])) if mrow.any() else 0
                    if nd < M2.MIN_DATES:
                        acts.append('%d:fallback' % Y)
                        continue
                    fy = [Y - 2, Y - 1]
                    if all((f_, 1.0) in fold for f_ in fy):
                        sc = {l_: float(np.mean([fold[(f_, l_)] for f_ in fy])) for l_ in M2.LAMS}
                        best = max(M2.LAMS, key=lambda l_: (round(sc[l_], 12), l_))
                        if sc[best] <= M2.TOL:
                            acts.append('%d:zero' % Y)
                            continue
                        lam = best
                    else:
                        lam = 1.0
                    days = P.years == Y
                    zfull = np.where(days[:, None], M2.predict_z(P, fit_w(mrow, lam, mult), days), zfull)
                    acts.append('%d:lam%g' % (Y, lam))
                rows.append(dict(program=key, segment=seg, b=b, d_net8_outer=account(zfull), actions='|'.join(acts),
                                 fast_path=FA is not None))
        except Exception as e:
            traceback.print_exc()
            rows.append(dict(program=key, segment=seg, b=-1, status='FAILED_TECH', note=str(e)[:150]))
        print('  %d/%d %s %.0fs (末个 %.0fs)' % (gi + 1, len(progs), key, time.time() - t0, time.time() - ts), flush=True)
    tag = '%02d' % a.shard + ('_timing' if a.limit else '')
    I.atomic_write_csv(os.path.join(md, 'boot_%s.csv' % tag), pd.DataFrame(rows))
    I.atomic_write_csv(os.path.join(md, 'bootfolds_%s.csv' % tag), pd.DataFrame(frows))
    I.atomic_write_csv(os.path.join(md, 'boot_anchor_%s.csv' % tag), pd.DataFrame(anchors))
    I.write_receipt(os.path.join(I.RES, 'task_status', 'm2boot_%s_%s.receipt.json' % (seg, tag)),
                    'm2boot:%s:%s' % (seg, tag), [], n_programs=len(progs), boot=a.boot,
                    elapsed_s=round(time.time() - t0, 1))
    print('[%s m2boot %s] 完成 %.0fs' % (seg, tag, time.time() - t0))


if __name__ == '__main__':
    main()
