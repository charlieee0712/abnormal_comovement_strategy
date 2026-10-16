# -*- coding: utf-8 -*-
"""E6m 阶段 S（B2 开发）· 引擎接口一致性 mock。
不是第二个引擎：只实现 E6m 算子会用到的 Seg / Dom / Struct 字段与方法（见 stageN/STAGE_S_IMPL_PLAN.md §1）。
- 由数据侧源上下文（tmp/ctx_<段>.pkl）与 e6m_adapter.Downstream 搭建；只覆盖六个生产形态，R2 / A06 = OUT_OF_SCOPE_MOCK。
- 语义读源转录自 e6j_engine.DepK / MeanSlot / UnionK 与 e6i_randoms.KeepDom（云机账户侧 import 不起来）：
  - 单元 = pool0 格，(t, c) 字典序，c ∈ ccols = p0.any(0)；
  - dom.ids = 门分有限的单元（递增即 (t, c) 序，也就是日内 ticker 升序）；
  - K[d] = 源 qcut(rank first, 2) 第 1 组人数（n < 6 → 0）；keep = 逐日 argsort(stable) 取前 K；
  - A4b：门分 = q（生产 pcond 单元）；下游 = 源 precompute_neutralized_factor(fac_tvol, 新 G) → 源两组第一组 → CVR k5 否决（按形态）；
  - union：门分 = q；下游 = ∧ ~T 剔尾 ∧ ~cr20 剔尾 ∧ ~CVR（按形态）；
  - mean：门分 = 可得腿均值（K 腿换 q；当日某腿整日无值 → 当日无分）；下游 = ∧ ~CVR（按形态）。
- K_loading（plan §4.2 / §5.3）：A4b / union = 1；mean = 1 / 当日可得腿数，K 腿缺失时 = 0。
Gate 0（任何算子上 mock 之前必须过）：kept(q0) = form_masks(ctx) 逐格；dom.ids 日内 ticker 升序；K = ceil(N/2)。不读任何收益。"""
import e6j_boot  # noqa: F401
import os
import sys
import math
import json
import time
import pickle
import argparse
from types import SimpleNamespace

import numpy as np
import pandas as pd

import e6m_core as M

FORMS = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
OUT_OF_SCOPE = ('R2', 'A06')
_QC = {}


def k_of(n):
    """源两组 qcut（rank method='first'）的第 1 组人数；n < 6（= 3·g）当日空（e6i_randoms.k_of、e6f_core.qcut_group 同式）。"""
    n = int(n)
    if n < 6:
        return 0
    r = _QC.get(n)
    if r is None:
        s = pd.Series(np.arange(1, n + 1, dtype=float))
        g = pd.qcut(s.rank(method='first'), 2, labels=[1, 2]).to_numpy().astype(int)
        r = _QC[n] = int((g <= 1).sum())
    return r


def dict_dense(cache, pool0):
    out = np.full(pool0.shape, np.nan)
    di = {d: i for i, d in enumerate(pool0.index)}
    cp = {c: j for j, c in enumerate(pool0.columns)}
    for d, s in cache.items():
        if d not in di:
            continue
        pos = np.fromiter((cp.get(x, -1) for x in s.index), int, len(s))
        ok = pos >= 0
        out[di[d], pos[ok]] = s.to_numpy(float)[ok]
    return out


class Dom(object):
    """一个保留域（e6i_randoms.KeepDom 同语义）。"""

    def __init__(self, seg, valid_cells):
        self.ids = np.flatnonzero(valid_cells)
        cnt = np.bincount(seg.ci.t[self.ids], minlength=seg.T)
        self.off = np.r_[0, np.cumsum(cnt)]
        self.N = cnt
        self.K = np.array([k_of(n) if n else 0 for n in cnt])
        self.days = np.flatnonzero(self.K > 0)

    def keep(self, sc):
        """sc (P, len(ids)) → (P, len(ids)) bool。"""
        kept = np.zeros(sc.shape, bool)
        for d in self.days:
            a, b = self.off[d], self.off[d + 1]
            idx = np.argsort(sc[:, a:b], axis=1, kind='stable')[:, :self.K[d]]
            np.put_along_axis(kept[:, a:b], idx, True, axis=1)
        return kept


class MockSeg(object):
    def __init__(self, pname):
        import e6j_prod as PR
        import e6m_adapter as AD
        with open(M.P('tmp', 'ctx_%s.pkl' % pname), 'rb') as fh:
            ctx = pickle.load(fh)
        self.pname, self.ctx = pname, ctx
        pool0 = ctx['pool0']
        p0 = np.asarray(ctx['p0'], bool)
        self.pool0 = pool0
        self.ccols = np.flatnonzero(p0.any(axis=0))
        self.ccolnames = np.array([str(x) for x in pool0.columns[self.ccols]])
        self.T, self.Nc = p0.shape[0], len(self.ccols)
        t, c = np.nonzero(p0[:, self.ccols])                  # 行主序 = (t, c) 字典序
        self.ci = SimpleNamespace(t=t, c=c, T=self.T, n=len(t), Nc=self.Nc)
        self.n = len(t)
        self.off = np.r_[0, np.cumsum(np.bincount(t, minlength=self.T))]
        self.tid_c = np.array([int(x) for x in self.ccolnames], np.int64)
        if not (np.diff(self.tid_c) > 0).all():
            raise RuntimeError('ccol 次序与 ticker 整数升序不一致')
        self.tid = self.tid_c[c]
        self.dates = pool0.index
        self.cell_of = np.full((self.T, self.Nc), -1, np.int64)
        self.cell_of[t, c] = np.arange(self.n)
        cells = lambda A: np.asarray(A)[:, self.ccols][t, c]
        self.cells = cells
        self.pK = cells(dict_dense(ctx['pcond'], pool0))
        self.pT = cells(dict_dense(ctx['ptvol'], pool0))
        self.pR = cells(dict_dense(ctx['pcr20'], pool0))
        self.dT = cells(PR.drop_mask(ctx['neu_tvol'], pool0))
        self.dR = cells(PR.drop_mask(ctx['neu_cr20'], pool0))
        self.cvr = cells(PR.drop_mask(ctx['neu_cvr'], pool0, 5))
        self.DS = AD.Downstream(ctx)
        self._st = {}

    def to_tn(self, G_cells):
        """单元 bool (n,) → pool0 网格 (T, N) bool。"""
        out = np.zeros(self.pool0.shape, bool)
        ix = np.flatnonzero(G_cells)
        out[self.ci.t[ix], self.ccols[self.ci.c[ix]]] = True
        return out

    def struct(self, form):
        if form in OUT_OF_SCOPE:
            raise ValueError('OUT_OF_SCOPE_MOCK：%s' % form)
        if form not in self._st:
            self._st[form] = MockStruct(self, form)
        return self._st[form]

    def day_slices(self):
        return [(d, self.off[d], self.off[d + 1]) for d in range(self.T)]


class MockStruct(object):
    def __init__(self, seg, form):
        self.seg, self.form = seg, form
        self.veto = form.endswith('_CVRv5')
        n = seg.n
        if form.startswith('A4b'):
            self.kind = 'A4b'
            self.q0 = seg.pK
            self.drop = seg.cvr if self.veto else np.zeros(n, bool)
            self.dom = Dom(seg, np.isfinite(self.q0))
        elif form.startswith('M_union3'):
            self.kind = 'union'
            self.q0 = seg.pK
            self.base = ~seg.dT & ~seg.dR & (~seg.cvr if self.veto else np.ones(n, bool))
            self.dom = Dom(seg, np.isfinite(self.q0))
        elif form.startswith('M_mean3'):
            self.kind = 'mean'
            self.q0 = seg.pK
            self.legs = [seg.pK, seg.pT, seg.pR]
            ok = np.ones(seg.T, bool)
            for L in self.legs:
                ok &= np.bincount(seg.ci.t[np.isfinite(L)], minlength=seg.T) > 0
            self.dayok = ok
            self.drop = seg.cvr if self.veto else np.zeros(n, bool)
            self.dom = Dom(seg, np.isfinite(self.score(self.q0[None, :])[0]))
        else:
            raise ValueError(form)
        self.ids = self.dom.ids
        self.nlegs = 3 if self.kind == 'mean' else 1
        self.bunit = 1.0 / (100.0 * self.nlegs)
        if self.kind == 'mean':
            avail = np.isfinite(seg.pT).astype(int) + np.isfinite(seg.pR).astype(int) + np.isfinite(seg.pK).astype(int)
            self.K_loading_cells = np.where(np.isfinite(seg.pK) & (avail > 0), 1.0 / np.maximum(avail, 1), 0.0)
        else:
            self.K_loading_cells = np.ones(n)
        self.K_loading = self.K_loading_cells[self.ids]

    def score(self, q):
        """mean 门分（e6j_engine.MeanSlot.score 同式：可得腿和 / 可得腿数；当日某腿整日无值 → NaN）。"""
        q = np.atleast_2d(q)
        A = [q] + [np.broadcast_to(L[None, :], q.shape) for L in self.legs[1:]]
        tot = np.zeros(q.shape)
        cnt = np.zeros(q.shape, np.intp)
        for Aj in A:
            tot = tot + np.where(np.isnan(Aj), 0.0, Aj)
            cnt = cnt + (~np.isnan(Aj)).astype(np.intp)
        with np.errstate(invalid='ignore', divide='ignore'):
            out = tot / cnt
        return np.where(self.dayok[self.seg.ci.t][None, :], out, np.nan)

    def gate_scores(self, q):
        q = np.atleast_2d(q)
        if self.kind == 'mean':
            return self.score(q)[:, self.ids]
        return q[:, self.ids]

    def gate_keep(self, sc):
        return self.dom.keep(sc)

    def down(self, G):
        """G (P, len(ids)) 门内成员 → (P, n) 最终名单（源下游函数）。"""
        G = np.atleast_2d(G)
        P = G.shape[0]
        seg = self.seg
        g = np.zeros((P, seg.n), bool)
        g[:, self.ids] = G
        if self.kind == 'union':
            return g & self.base[None, :]
        if self.kind == 'mean':
            return g & ~self.drop[None, :]
        out = np.zeros((P, seg.n), bool)
        for p in range(P):
            m = seg.DS.a4b(seg.to_tn(g[p]))[self.form]
            out[p] = seg.cells(m)
        return out

    def kept(self, q):
        return self.down(self.gate_keep(self.gate_scores(q)))


def task_gate0(pname):
    import e6j_prod as PR
    import e6m_adapter as AD
    t0 = time.time()
    seg = MockSeg(pname)
    masks = PR.form_masks(seg.ctx)
    rows = []
    fam = {'A4b': 'A4b', 'A4b_CVRv5': 'A4b', 'M_mean3_v2': 'Mmean', 'M_mean3_v2_CVRv5': 'Mmean', 'M_union3_v2': 'Munion', 'M_union3_v2_CVRv5': 'Munion'}
    gates = {}
    for form in FORMS:
        t1 = time.time()
        st = seg.struct(form)
        mk = st.kept(st.q0[None, :])[0]
        src = np.asarray(masks[form], bool)
        outside = int((src & ~np.asarray(seg.ctx['p0'], bool)).sum())
        srcc = seg.cells(src)
        mism = int((mk != srcc).sum())
        dom = st.dom
        order_ok = all((np.diff(seg.ci.c[dom.ids[dom.off[d]:dom.off[d + 1]]]) > 0).all() for d in range(seg.T) if dom.off[d + 1] - dom.off[d] > 1)
        k_ok = bool(all(dom.K[d] == (int(math.ceil(dom.N[d] / 2.0)) if dom.N[d] >= 6 else 0) for d in range(seg.T)))
        f = fam[form]
        if f not in gates:
            gates[f] = AD.Gate(seg.ctx, f)
        G = gates[f]
        n_dom_diff = k_diff = 0
        for d in range(seg.T):
            D = G.day(d)
            nd, kd = (0, 0) if D is None else (len(D['ids']), int(D['n']))
            n_dom_diff += int(nd != (dom.N[d] if dom.K[d] > 0 else 0))
            k_diff += int(kd != dom.K[d])
        rows.append(dict(segment=pname, form=form, kind=st.kind, cells=seg.n, final_mock=int(mk.sum()), final_source=int(srcc.sum()),
                         source_outside_pool0=outside, mismatch_cells=mism, ids_ticker_ascending=bool(order_ok), K_is_ceil_half=k_ok,
                         days_domain_size_vs_adapter_diff=n_dom_diff, days_K_vs_adapter_diff=k_diff,
                         kload_ne_third_share=float(np.mean(np.abs(st.K_loading - 1 / 3.0) > 1e-12)) if st.kind == 'mean' else np.nan,
                         kload_zero_share=float(np.mean(st.K_loading == 0)) if st.kind == 'mean' else np.nan,
                         status='PASS' if (mism == 0 and outside == 0 and order_ok and k_ok and n_dom_diff == 0 and k_diff == 0) else 'FAIL',
                         seconds=round(time.time() - t1, 1)))
    df = pd.DataFrame(rows)
    p = M.P('stageS_dev', 'gate0_mock_%s.csv' % pname)
    M.atomic_write_csv(p, df)
    ok = bool((df.status == 'PASS').all())
    M.write_receipt(os.environ.get('E6M_TASK', 'S_dev_gate0_%s' % pname), [p], status='SUCCEEDED' if ok else 'FAILED',
                    code=[__file__, M.__file__], wall_s=round(time.time() - t0, 1), note='B2 开发：mock 名单层，不读收益')
    print(df.drop(columns=['segment']).to_string(index=False), flush=True)
    return 0 if ok else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['gate0'])
    ap.add_argument('--seg', required=True)
    a = ap.parse_args()
    sys.exit(task_gate0(a.seg))
