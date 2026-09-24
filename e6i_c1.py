#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i carried C1: 人数 N x 行业宽度 B 交叉 (plan §9.1; brief §10)。旧测量 + 固定 R1/R2/A06, 不依赖本轮赢家。

采样域 Ω (N, B, 分配, seed):
  行业先选: 当日 pool0 出现的行业按 hash(seed, 行业码) 优先级取前 B 个 (不足 B -> 当日 infeasible);
  行业内按 hash(seed, ticker) 固定优先级取票 (跨日持续; 跨 N 嵌套);
  分配: equal = 容量受限近似等人数 (水位填充) / prop = 容量受限原始行业比例 (最大余数取整);
  所选 B 个行业的总容量 < N -> 当日 infeasible (严格交叉视图剔除; 部署视图取 min(N, 容量))。
核与预算 (研究适配器 = 计数预算, 同 E6h T2/T3 的 keep_RANKBUDGET; 源分箱差异另列"仪器效应"):
  R2 = KT_mean, A06 = KTC_mean: 在 Ω ∩ ¬否决 内按核分数取 floor(q·n);
  R1 = KT_dep: 第一阶段 K 取 50% (计数), 第二阶段 T 在 S1' 内取 2q (计数) -> 总深度 q;
  评分 scope: frozen = 完整 pool0 上的 NS pct (冻结); resample = 各腿在 Ω 内按源口径重新中性化后排名
  (R1 第二阶段在 S1' 内重中性化);
  否决 = 母体完整 pool0 的源否决 (冻结), 先从 Ω 剔除 (同 E6h T3 run2)。
桥: full_pool0 (Ω = pool0 的同一计数预算) / topN_core (按冻结核分数 top-N 截断) / randomN (逐日 IID 随机 N, 64 seed)。
仪器效应: frozen scope 的 R2/A06 另跑源分箱 keep_SRC(q) 与计数预算之差。
后段 (2019-23 / 2024-26): 旧输入格按守卫 sealed 规则只算不读 -> sealed/<seg>/ (B 前不读; 日志不打印任何后段数字)。
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import io
import sys
import time
import hashlib
import argparse
import itertools

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_ops as OP
import e6i_engine as E
import e6g_core as G
import e6f_core as F

NS = (100, 150, 250)
BS = (8, 12, 16)
QS = (0.20, 0.30, 0.40, 0.50)
ALLOCS = ('equal', 'prop')
MOTHERS = ('R1', 'R2', 'A06')
N_SEEDS = 64
POST = ('2019-2023', '2024-2026')


def h32(s):
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16)


def allocate(caps, N, how):
    """caps: 各行业容量 (int array); 返回各行业人数 (sum = min(N, sum caps))。"""
    caps = np.asarray(caps, np.int64)
    tot = int(caps.sum())
    if tot <= N:
        return caps.copy()
    if how == 'prop':
        raw = N * caps / tot
        base = np.floor(raw).astype(np.int64)
        rem = N - int(base.sum())
        order = np.lexsort((np.arange(len(caps)), -(raw - base)))
        base[order[:rem]] += 1
        return np.minimum(base, caps)
    # equal: 水位填充
    out = np.zeros(len(caps), np.int64)
    left = N
    active = np.ones(len(caps), bool)
    while left > 0 and active.any():
        k = int(active.sum())
        share = left // k
        if share == 0:
            idx = np.flatnonzero(active)[:left]
            out[idx] += 1
            break
        add = np.minimum(caps - out, share)
        add = np.where(active, add, 0)
        out += add
        left -= int(add.sum())
        active = active & (out < caps)
    return out


class Sampler(object):
    def __init__(self, S):
        self.S = S
        self.p0 = S.p0c
        self.ic = np.asarray(S.icodes)
        self.names = list(S.ccolnames)

    def omega(self, N, B, how, seed):
        """(Ω (T, Nc) bool, feasible (T,), B_eff (T,), HHI (T,))。"""
        S, p0, ic = self.S, self.p0, self.ic
        T, Nc = p0.shape
        tick_pri = np.array([h32('stk|%d|%s' % (seed, c)) for c in self.names], np.int64)
        out = np.zeros((T, Nc), bool)
        feas = np.zeros(T, bool)
        beff = np.full(T, np.nan)
        hhi = np.full(T, np.nan)
        ind_pri = {}
        for t in range(T):
            v = np.flatnonzero(p0[t])
            if len(v) == 0:
                continue
            g = ic[t, v]
            inds = np.unique(g[g >= 0])
            if len(inds) < B:
                continue
            pri = np.array([ind_pri.setdefault(x, h32('ind|%d|%d' % (seed, x))) for x in inds])
            chosen = inds[np.argsort(pri, kind='stable')[:B]]
            caps = np.array([int((g == x).sum()) for x in chosen])
            feas[t] = caps.sum() >= N
            alloc = allocate(caps, N, how)
            sel = []
            for x, k in zip(chosen, alloc):
                if k <= 0:
                    continue
                vv = v[g == x]
                sel.append(vv[np.argsort(tick_pri[vv], kind='stable')[:k]])
            if sel:
                ss = np.concatenate(sel)
                out[t, ss] = True
                sh = alloc[alloc > 0] / alloc.sum()
                hhi[t] = float((sh ** 2).sum())
                beff[t] = 1.0 / hhi[t]
        return out, feas, beff, hhi

    def random_n(self, N, seed):
        p0 = self.p0
        T, Nc = p0.shape
        out = np.zeros((T, Nc), bool)
        rng = np.random.default_rng([20260923, 9, seed])
        for t in range(T):
            v = np.flatnonzero(p0[t])
            if len(v):
                out[t, v[rng.permutation(len(v))[:min(N, len(v))]]] = True
        return out


class Core(object):
    """母体核 (冻结分数 + 重排所需的原始腿)。"""

    def __init__(self, S, mn):
        self.S, self.mn = S, mn
        M = self.M = OP.Mother(S, mn)
        self.kind = M.kind
        self.dr = M.dr & S.p0c
        if M.kind == 'dep':
            self.K_full = M.Px
            self.T_spec = M.core['ys'][0]
            self.K_spec = M.core['x']
            self.T_raw = OP._raw_c(S, self.T_spec)
            self.K_raw = OP._raw_c(S, self.K_spec)
            self.T_full = M.ctx.leg_pct(self.T_spec, 'NS', 'hi', 'identity')
        else:
            self.specs = list(M.core['comps'])
            self.legs_full = list(M.legs)
            self.raws = [OP._raw_c(S, sp) for sp in self.specs]
            self.complete = M.core['fam'].startswith('KTC')
            self.score_full = M.score

    def combine(self, legs):
        if len(legs) == 1:
            return legs[0]
        return F.combine_dense(legs, 'mean', complete=self.complete)

    def prepare(self, dom):
        """resample scope 的重排只依赖域 (不依赖 q): 每个域算一次。"""
        S = self.S
        self._dom = dom
        if self.kind == 'dep':
            Kp = OP._ns_pct_within(S, self.K_raw, dom, 'hi')
            self._s1r = G.keep_RANKBUDGET(Kp, dom, 50)
            self._Tp = OP._ns_pct_within(S, self.T_raw, self._s1r, 'hi')
            self._s1f = G.keep_RANKBUDGET(self.K_full, dom, 50)
        else:
            self._scr = self.combine([OP._ns_pct_within(S, r, dom, 'hi') for r in self.raws])

    def select(self, dom, q, scope, bins=False):
        """在 dom (已剔否决; 必须先 prepare(dom)) 内按核取深度 q; 返回最终名单 (T, Nc) bool。"""
        assert dom is self._dom
        if self.kind == 'dep':
            if scope == 'frozen':
                return G.keep_RANKBUDGET(self.T_full, self._s1f, 100 * min(1.0, 2 * q))
            return G.keep_RANKBUDGET(self._Tp, self._s1r, 100 * min(1.0, 2 * q))
        sc = self.score_full if scope == 'frozen' else self._scr
        if bins:
            return G.keep_SRC(sc, dom, int(round(100 * q))).astype(bool)
        return G.keep_RANKBUDGET(sc, dom, 100 * q)


_SE = {}


def run_account(S, mask, H=5):
    """稀疏引擎 (DEV 逐位、账本 <=1e-14 对已锚稠密引擎; checks/sparse_engine_anchor_*.json)。"""
    import e6i_sparse as SP
    se = _SE.get(id(S))
    if se is None:
        se = _SE[id(S)] = SP.SparseEngine(S)
    t, c = np.nonzero(mask)
    w = se.dev(t, c)
    return se.pnl(t, c, w, (H,), I.COST)[H]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--seeds', default='0-63')
    ap.add_argument('--part', default='cross', choices=('cross', 'bridges'))
    a = ap.parse_args()
    seg = a.segment
    post = seg in POST
    assert seg in I.DERIV_SEGS or post
    s0, s1_ = [int(x) for x in a.seeds.split('-')]
    seeds = list(range(s0, s1_ + 1))
    t0 = time.time()
    I.guard_i([], ['C1_POST'] if post else [], segment=seg, use='compute', sealed=post, where='c1:%s' % seg)
    S = I.seg_i(seg, warm=False)
    cores = {mn: Core(S, mn) for mn in MOTHERS}
    smp = Sampler(S)
    logm = S.log_mcap.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]
    trn = S.data['turnover_rate'].reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]
    print('段就绪 %.0fs; C1 %s part=%s seeds %s' % (time.time() - t0, seg, a.part, a.seeds), flush=True)
    rows, series, feas_rows = [], {}, []

    def record(tag, dom_desc, mn, q, scope, mask, extra):
        g, p, u, n = run_account(S, mask)
        key = '|'.join(str(x) for x in (tag, dom_desc, mn, q, scope))
        series[key] = n
        held = mask.sum(1)
        rows.append(dict(key=key, part=tag, domain=dom_desc, mother=mn, q=q, scope=scope,
                         net8_ann=I.ann(n), gross_ann=I.ann(g), turn_mean=float(np.nanmean(u)),
                         pos_mean=float(np.nanmean(p)), held_mean=float(held.mean()),
                         empty_days=int((held == 0).sum()), **extra))

    if a.part == 'cross':
        for seed, N, B, how in itertools.product(seeds, NS, BS, ALLOCS):
            om, feas, beff, hhi = smp.omega(N, B, how, seed)
            dd = '%d|%d|%s|s%02d' % (N, B, how, seed)
            with np.errstate(all='ignore'):
                extra = dict(N=N, B=B, alloc=how, seed=seed, feasible_frac=float(feas.mean()),
                             B_eff_mean=float(np.nanmean(beff)), HHI_mean=float(np.nanmean(hhi)),
                             omega_n_mean=float(om.sum(1).mean()),
                             logmcap_mean=float(np.nanmean(np.where(om, logm, np.nan))),
                             turnover_mean=float(np.nanmean(np.where(om, trn, np.nan))))
            feas_rows.append(dict(domain=dd, **{'f%d' % t: bool(x) for t, x in enumerate(feas)}))
            for mn, C in cores.items():
                dom = om & ~C.dr
                C.prepare(dom)
                for q in QS:
                    for scope in ('frozen', 'resample'):
                        record('cross', dd, mn, q, scope, C.select(dom, q, scope), extra)
                    if mn != 'R1':
                        record('instrument_bins', dd, mn, q, 'frozen', C.select(dom, q, 'frozen', bins=True), extra)
            if not post:
                print('  seed %d N %d B %d %s  %.0fs' % (seed, N, B, how, time.time() - t0), flush=True)
    else:
        p0 = S.p0c
        for mn, C in cores.items():
            full = p0 & ~C.dr
            C.prepare(full)
            for q in QS:
                record('bridge_full', 'pool0', mn, q, 'frozen', C.select(full, q, 'frozen'), {})
            base = C.score_full if C.kind != 'dep' else C.K_full
            rk = pd.DataFrame(np.where(full, base, np.nan)).rank(axis=1, method='first').values
            for N in NS:
                top = full & np.isfinite(rk) & (rk <= N)
                C.prepare(top)
                for q in QS:
                    record('bridge_topN', 'top%d' % N, mn, q, 'frozen', C.select(top, q, 'frozen'), dict(N=N))
        if seeds[0] == 0:
            # 源母体本身 (完整 pool0、源分箱、源否决) = 桥的零点
            for mn, C in cores.items():
                record('mother_source', 'pool0', mn, np.nan, 'source', C.M.B, {})
        for seed, N in itertools.product(seeds, NS):
            rn = smp.random_n(N, seed)
            for mn, C in cores.items():
                dom = rn & ~C.dr
                C.prepare(dom)
                for q in QS:
                    for scope in ('frozen', 'resample'):
                        record('bridge_randomN', '%d|s%02d' % (N, seed), mn, q, scope,
                               C.select(dom, q, scope), dict(N=N, seed=seed))
    d = pd.DataFrame(rows)
    buf = io.BytesIO()
    ks = sorted(series)
    np.savez(buf, keys=np.asarray(ks), net8=np.vstack([series[k] for k in ks]) if ks else np.zeros((0, S.T)))
    tag = 'c1_%s_%s' % (a.part, a.seeds)
    if post:
        I.sealed_write_csv(seg, tag, d, meta=dict(part=a.part, seeds=a.seeds))
        I.guard_i([], ['C1_POST'], segment=seg, use='compute', sealed=True, where='sealed_write_npz')
        p = os.path.join(I.SEALED, seg, tag + '.npz')
        I.atomic_write_bytes(p, buf.getvalue())
        if feas_rows:
            I.sealed_write_csv(seg, tag + '_feasible', pd.DataFrame(feas_rows))
        print('[%s] C1 %s 封存 %d 行 (不打印数值); %.0fs' % (seg, tag, len(d), time.time() - t0))
    else:
        od = os.path.join(I.RES, 'carried', 'C1', seg)
        os.makedirs(od, exist_ok=True)
        I.atomic_write_csv(os.path.join(od, tag + '.csv'), d)
        I.atomic_write_bytes(os.path.join(od, tag + '.npz'), buf.getvalue())
        if feas_rows:
            I.atomic_write_csv(os.path.join(od, tag + '_feasible.csv'), pd.DataFrame(feas_rows))
        print('[%s] C1 %s %d 行; %.0fs' % (seg, tag, len(d), time.time() - t0))
    I.write_receipt(os.path.join(I.RES, 'task_status', 'c1_%s_%s.receipt.json' % (seg, tag)),
                    'c1:%s:%s' % (seg, tag), [], status='SUCCEEDED', rows=len(d), sealed=post,
                    elapsed_s=round(time.time() - t0, 1))


if __name__ == '__main__':
    main()
