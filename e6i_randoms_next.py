#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Z-MAP 随机对照 (plan §6.3 / §6.4 / §8.3; brief §6)。推导段专用, 不产生任何 2019+ 数值。

每个"非同义配置"(A0 描述符去掉 H) 在三类随机机制下各跑 random_priority 条路径 (代表 256 / 其余 64,
首轮; MCSE 触发加到 512 / 1024 由 --paths-mult 另跑), 每条路径各自过 DEV / 持仓 / 成本 (先跑再平均收益):
  basic      同日同集合均匀随机
  industry   同日同行业人数匹配 (S.icodes 行业; 无行业码归一组)
  persist20  股票 x 注册 20 日块的稳定优先级 (块内同一股票的随机名次不变)
三类共用配对 draw (同一 b 的底层均匀数跨配置相同 = common random numbers)。

角色 -> 随机机制 (plan §6.3 表, 逐字对应):
  SLOT / COMMON_SUPPORT / T_PAIR / ADD_SCORE   只置换【新分量】的当日横截面归属, 保留其有效 mask 与旧分量 /
                                               源构造 (DEP 两阶段完整重算, 第二阶段在新 S1 内按源口径重中性化)
  VETO_NEW / SOFT_HARD                          同母体同日同 m 随机删除 (m = 真实当日实删数); 另: 同 m 反方向删除
  SOFT                                          同日同 m 随机选票做同一 λ 缩减 (不再分配)
  SWAP                                          固定真实 D, 从相同候选域随机取 m 个 A; 另: 反向新排序
  FOCAL (new / both / replace)                  焦点关闭的母体上, 新增删除名额随机化
  FOCAL (real_state)                            状态在当日 pool0 内随机 (同状态人数)
  RL                                            同 m、同边缘域 (有成本值) 随机选
  FOURARM / 焦点 old/none/all_on/all_off/random_state   不跑 (确定性臂 / 自身即随机)
每个配置先用同一稀疏引擎重算真实账户, 与 Stage 2 主账户逐描述符对账 (锚)。
SLOT 类的"恒等置换"路径必须逐格复现真实子名单 (no-op 锚, plan §8.3 负对照之一)。

输出 randoms/<seg>/<route>_<shard>.csv (配置 x 类 x H 汇总) + .npz (逐路径年化 net8 / gross 与
路径均值逐日 net8 序列)。用法:
  python3 e6i_randoms.py --segment 2015-2018 --route RT --shard 0 --nshard 4
  python3 e6i_randoms.py --segment 2015-2018 --route RT --selftest 6    (每角色取样做 no-op / 对账锚)
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import io
import sys
import time
import json
import argparse
import collections
import traceback

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6i_s1base as SB
import e6i_ops as OP
import e6i_sparse as SP
import e6i_stage2 as S2
import e6f_core as F

KINDS = ('basic', 'industry', 'persist20')
SEED = 20260923
SEGCODE = {'2010-2014': 1, '2015-2018': 2}
BATCH = 64
DET_ARMS = ('old', 'none', 'all_on', 'all_off', 'random_state')


# ============================================================ pool0 单元与随机库
class Cells(object):
    """pool0 单元编号: id 递增 = (t, c) 字典序。所有随机对象都在 pool0 内。"""

    def __init__(self, S):
        self.T, self.Nc = S.T, S.Nc
        self.t, self.c = np.nonzero(S.p0c)
        self.n = len(self.t)
        self.id = np.full((S.T, S.Nc), -1, np.int64)
        self.id[self.t, self.c] = np.arange(self.n)
        ic = np.asarray(S.icodes)[self.t, self.c]
        self.GG = int(S.G) + 1
        self.g = np.where(ic >= 0, ic, S.G).astype(np.int64)
        self.tg = self.t * self.GG + self.g
        self.blk = self.t // 20

    def of(self, mask):
        """(T, Nc) bool -> pool0 单元 bool (断言不越出 pool0)。"""
        m = np.asarray(mask, bool)
        out = m[self.t, self.c]
        if int(m.sum()) != int(out.sum()):
            raise ValueError('名单越出 pool0: %d 格' % (int(m.sum()) - int(out.sum())))
        return out

    def full(self, x_cells):
        out = np.zeros((self.T, self.Nc), bool)
        out[self.t[x_cells], self.c[x_cells]] = True
        return out


class Bank(object):
    """配对 draw: 路径 b 的底层均匀数只依赖 (段, b), 跨配置 / 跨角色相同。"""

    def __init__(self, S, cells, seg):
        self.S, self.ci, self.seg = S, cells, seg
        self._o = {}

    def order(self, kind, b):
        k = (kind, b)
        o = self._o.get(k)
        if o is None:
            ci = self.ci
            if kind in ('basic', 'industry'):
                U = np.random.default_rng([SEED, SEGCODE[self.seg], 0, int(b)]).random(ci.n)
                o = np.lexsort((U, ci.t)) if kind == 'basic' else np.lexsort((U, ci.g, ci.t))
            elif kind == 'persist20':
                nb = int(ci.blk.max()) + 1
                R = np.random.default_rng([SEED, SEGCODE[self.seg], 1, int(b)]).random((nb, ci.Nc))
                o = np.lexsort((R[ci.blk, ci.c], ci.t))
            else:
                raise ValueError(kind)
            o = o.astype(np.int64)
            self._o[k] = o
        return o

    def grp(self, kind):
        return self.ci.tg if kind == 'industry' else self.ci.t

    def ngrp(self, kind):
        return self.ci.T * self.ci.GG if kind == 'industry' else self.ci.T

    def pick(self, kind, b, X, quota):
        """在 X (单元 bool) 里按路径 b 的随机次序, 每组取 quota[组] 个; 返回 (单元 id, 缺口数)。"""
        o = self.order(kind, b)
        cand = o[X[o]]
        if len(cand) == 0:
            return cand, int(quota.sum())
        g = self.grp(kind)[cand]
        brk = np.flatnonzero(g[1:] != g[:-1]) + 1
        starts = np.r_[0, brk]
        lens = np.diff(np.r_[starts, len(cand)])
        pos = np.arange(len(cand)) - np.repeat(starts, lens)
        sel = cand[pos < quota[g]]
        return sel, int(quota.sum() - len(sel))

    def quota_of(self, kind, x_cells_bool):
        """真实被选集合在每组的人数 (basic/persist: 每日; industry: 每日 x 行业)。"""
        return np.bincount(self.grp(kind)[x_cells_bool], minlength=self.ngrp(kind))

    def shuffled(self, kind, b, V, vals_sorted):
        """V 单元上的值在组内随机重排: 第 k 个随机次序的单元拿组内第 k 小的值。"""
        o = self.order(kind, b)
        cand = o[V[o]]
        z = np.full(self.ci.n, np.nan)
        z[cand] = vals_sorted
        return z


# ============================================================ 保留 (源 keep_mask_dense 的批量版)
_KT = {}


def k_of(n, pctkeep):
    """源 keep_mask_dense: n < 3g 当日空; 否则保留 qcut 组号 <= keep_g 的前缀。"""
    g = F.P2G[int(pctkeep)]
    if n < 3 * g:
        return 0
    keep_g = int(round(g * pctkeep / 100.0))
    key = (int(n), g, keep_g)
    r = _KT.get(key)
    if r is None:
        r = _KT[key] = int((F.qcut_group(int(n), g) <= keep_g).sum())
    return r


class KeepDom(object):
    """一个保留域 (有效单元不随置换改变): 逐日 argsort(stable) 取前 K —— 与 lexsort((列, 分)) 同序。"""

    def __init__(self, ci, valid_cells_bool, pctkeep):
        if pctkeep >= 100:
            raise ValueError('pctkeep >= 100 未实现 (本轮母体无此情形)')
        self.ids = np.flatnonzero(valid_cells_bool)          # 递增 = (t, c) 序
        cnt = np.bincount(ci.t[self.ids], minlength=ci.T)
        self.off = np.r_[0, np.cumsum(cnt)]
        self.K = np.array([k_of(int(n), pctkeep) if n else 0 for n in cnt])
        self.days = np.flatnonzero(self.K > 0)

    def keep(self, sc):
        """sc: (P, len(ids)) -> kept (P, len(ids)) bool。"""
        kept = np.zeros(sc.shape, bool)
        for d in self.days:
            a, b = self.off[d], self.off[d + 1]
            idx = np.argsort(sc[:, a:b], axis=1, kind='stable')[:, :self.K[d]]
            np.put_along_axis(kept[:, a:b], idx, True, axis=1)
        return kept


def dep_stage2_keep(R, M, s1b, pctkeep_b):
    """R1 第二阶段的批量版: 每条路径的新 S1 内按源 pool_screening_v2.neutralize_by_mcap 口径
       (有效 < 10 用原值; 否则 OLS 残差) -> pct(average) -> 源 keep (有效 < 3g 空; qcut 前缀)。
       s1b: (P, n) bool over pool0 单元。返回 kept (P, n) bool。"""
    ci = R.ci
    P, n = s1b.shape
    T = ci.T
    pi, cid = np.nonzero(s1b)
    t = ci.t[cid]
    key = pi * T + t
    nk = P * T
    npool = np.bincount(key, minlength=nk)
    x = R.logm_c[cid]
    y = M.T_raw_c[cid]
    fy = np.isfinite(y)
    valid = fy & np.isfinite(x)
    nv = np.bincount(key, weights=valid.astype(float), minlength=nk)
    kv, xv, yv = key[valid], x[valid], y[valid]
    with np.errstate(all='ignore'):
        xm = np.bincount(kv, weights=xv, minlength=nk) / nv
        ym = np.bincount(kv, weights=yv, minlength=nk) / nv
        dx = xv - xm[kv]
        dy = yv - ym[kv]
        var = np.bincount(kv, weights=dx * dx, minlength=nk) / nv
        cov = np.bincount(kv, weights=dx * dy, minlength=nk) / nv
        beta = cov / var
        alpha = ym - beta * xm
    use_raw = nv[key] < 10
    val = np.full(len(cid), np.nan)
    a_ = use_raw & fy
    val[a_] = y[a_]
    r_ = (~use_raw) & valid
    with np.errstate(all='ignore'):
        val[r_] = y[r_] - (alpha[key[r_]] + beta[key[r_]] * x[r_])
    fv = np.isfinite(val)
    nfin = np.bincount(key[fv], minlength=nk)
    ok = fv & (npool[key] >= 6) & (nfin[key] >= 6)
    kk, vv, cc, pp = key[ok], val[ok], cid[ok], pi[ok]
    if len(kk) == 0:
        return np.zeros((P, n), bool)
    o = np.lexsort((vv, kk))
    ks, vs = kk[o], vv[o]
    newg = np.r_[True, ks[1:] != ks[:-1]]
    gstart = np.maximum.accumulate(np.where(newg, np.arange(len(ks)), 0))
    pos = np.arange(len(ks)) - gstart
    newr = newg | np.r_[True, vs[1:] != vs[:-1]]
    rid = np.cumsum(newr) - 1
    rfirst = pos[newr]
    rlast = np.r_[pos[np.flatnonzero(newr)[1:] - 1], pos[-1]]
    rank = (rfirst[rid] + rlast[rid]) / 2.0 + 1.0
    ng = np.bincount(kk, minlength=nk)
    pct = np.empty(len(kk))
    pct[o] = rank / ng[ks]
    # 源 keep: 有效 (= ok) 按 (pct, 列) 升序取前 K(n)
    o2 = np.lexsort((ci.c[cc], pct, kk))
    ks2 = kk[o2]
    newg2 = np.r_[True, ks2[1:] != ks2[:-1]]
    gst2 = np.maximum.accumulate(np.where(newg2, np.arange(len(ks2)), 0))
    pos2 = np.arange(len(ks2)) - gst2
    Kg = np.zeros(nk, np.int64)
    for gkey in np.flatnonzero(ng):
        Kg[gkey] = k_of(int(ng[gkey]), pctkeep_b)
    sel = pos2 < Kg[ks2]
    kept = np.zeros((P, n), bool)
    kept[pp[o2][sel], cc[o2][sel]] = True
    return kept


# ============================================================ 共享上下文
class RCtx(object):
    def __init__(self, S, seg):
        self.S, self.seg = S, seg
        self.ci = Cells(S)
        self.bank = Bank(S, self.ci, seg)
        self.RN = S2.Runner(S)
        self.SE = SP.SparseEngine(S)
        lm = S.log_mcap.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]
        self.logm_c = lm[self.ci.t, self.ci.c].astype(np.float64)
        self._mc = {}

    def mother(self, mn):
        M = self.RN.mother(mn)
        if mn not in self._mc:
            ci = self.ci
            M.dr_c = ci.of(M.dr & M.p0) if M.dr.any() else np.zeros(ci.n, bool)
            M.B_c = ci.of(M.B)
            M.score_c = M.score[ci.t, ci.c]
            if M.kind in ('mean', 'single'):
                M.legs_c = [L[ci.t, ci.c] for L in M.legs]
            else:
                M.Px_c = M.Px[ci.t, ci.c]
                M.s1_c = ci.of(M.s1)
                M.T_raw_c = M.T_raw[ci.t, ci.c]
            self._mc[mn] = True
        return M

    def cells_tc(self, ids):
        return self.ci.t[ids], self.ci.c[ids]


# ============================================================ 角色规格
class Spec(object):
    """real: (单元 id, wmul) 真实子账户; draw(kind, bs) -> [(单元 id, wmul)]; extras: 确定性附加对照。"""
    wmul_factor = None

    def extras(self):
        return {}


class ShuffleSpec(Spec):
    """SLOT / COMMON_SUPPORT / T_PAIR / ADD_SCORE: 置换新分量。score_fn(zp (P,n)) -> (P,n) 末级分数;
       dom: KeepDom; 或 dep_k=True 走 DEP 两阶段。"""

    def __init__(self, R, M, z_full, score_fn, dom=None, dep_k=None, real_mask=None):
        self.R, self.M = R, M
        ci = R.ci
        self.zc = z_full[ci.t, ci.c]
        self.V = np.isfinite(self.zc)
        self.vals = {}
        vid = np.flatnonzero(self.V)
        for kind in ('basic', 'industry'):
            g = R.bank.grp(kind)[vid]
            o = np.lexsort((self.zc[vid], g))
            self.vals[kind] = self.zc[vid][o]
        self.vals['persist20'] = self.vals['basic']
        self.score_fn, self.dom, self.dep_k = score_fn, dom, dep_k
        self.real_mask = real_mask

    def _child(self, zp):
        R, M = self.R, self.M
        if self.dep_k is None:
            sc = self.score_fn(zp)[:, self.dom.ids]
            kept = self.dom.keep(sc)
            out = []
            for p in range(zp.shape[0]):
                ids = self.dom.ids[kept[p]]
                out.append((ids[~M.dr_c[ids]], None))
            return out
        a_, b_ = self.dep_k                                  # (pct a, pct b)
        Px2 = self.score_fn(zp)
        s1 = np.zeros(zp.shape, bool)
        s1[:, self.dom.ids] = self.dom.keep(Px2[:, self.dom.ids])
        kept = dep_stage2_keep(R, M, s1, b_)
        out = []
        for p in range(zp.shape[0]):
            ids = np.flatnonzero(kept[p])
            out.append((ids[~M.dr_c[ids]], None))
        return out

    def identity(self):
        return self._child(self.zc[None, :])[0]

    def draw(self, kind, bs):
        out = []
        for i in range(0, len(bs), BATCH):
            zp = np.stack([self.R.bank.shuffled(kind, b, self.V, self.vals[kind]) for b in bs[i:i + BATCH]])
            out.extend(self._child(zp))
        return out


class DeleteSpec(Spec):
    """VETO_NEW / SOFT_HARD / SOFT / FOCAL new|both: 在 base 上删 (或缩) 与真实同 m 的随机票。"""

    def __init__(self, R, base_c, removed_c, fixed_drop_c=None, wmul=None, reverse_z=None):
        self.R, self.base, self.rem = R, base_c, removed_c
        self.fixed = fixed_drop_c if fixed_drop_c is not None else np.zeros_like(base_c)
        self.X = self.base & ~self.fixed
        self.wmul = wmul
        self.reverse_z = reverse_z

    def _mk(self, picked):
        if self.wmul is None:
            keep = self.X.copy()
            keep[picked] = False
            ids = np.flatnonzero(keep)
            return ids, None
        ids = np.flatnonzero(self.base)
        wm = np.ones(len(ids))
        pos = np.searchsorted(ids, picked)
        wm[pos] = 1.0 - self.wmul
        return ids, wm

    def draw(self, kind, bs):
        q = self.R.bank.quota_of(kind, self.rem)
        out = []
        for b in bs:
            sel, short = self.R.bank.pick(kind, b, self.X, q)
            out.append(self._mk(sel))
            self.short = max(getattr(self, 'short', 0), short)
        return out

    def extras(self):
        if self.reverse_z is None:
            return {}
        # 同 m 反方向: 在 X 里删新测量 bad-score 最低 (= 新测量最好) 的 m_t 只
        ci = self.R.ci
        z = self.reverse_z
        m_t = np.bincount(ci.t[self.rem], minlength=ci.T)
        ids = np.flatnonzero(self.X & np.isfinite(z))
        o = np.lexsort((ci.c[ids], z[ids], ci.t[ids]))
        ids = ids[o]
        tt = ci.t[ids]
        brk = np.flatnonzero(tt[1:] != tt[:-1]) + 1
        starts = np.r_[0, brk]
        lens = np.diff(np.r_[starts, len(ids)])
        pos = np.arange(len(ids)) - np.repeat(starts, lens)
        picked = ids[pos < m_t[tt]]
        restricted = int(m_t.sum() - len(picked))
        return {'reverse_sameM': (self._mk(picked), restricted)}


class SwapSpec(Spec):
    """固定真实 D, 从候选域 E' 随机取 m 个 A (industry: 按真实 A 的行业人数)。"""

    def __init__(self, R, M, B_c, D_c, A_c, Edom_c, zE, buffer_b=0):
        self.R, self.M = R, M
        self.keep = B_c & ~D_c
        self.A, self.E = A_c, Edom_c
        self.zE = zE
        self.buffer_b = int(buffer_b or 0)

    def _mk(self, a_ids):
        k = self.keep.copy()
        k[a_ids] = True
        if self.buffer_b > 0:
            R = self.R
            child = R.ci.full(np.flatnonzero(k))
            child = buffered_child_cached(R.S, self.M, child, self.buffer_b)
            return np.flatnonzero(R.ci.of(child)), None
        return np.flatnonzero(k), None

    def draw(self, kind, bs):
        q = self.R.bank.quota_of(kind, self.A)
        out = []
        for b in bs:
            sel, short = self.R.bank.pick(kind, b, self.E, q)
            out.append(self._mk(sel))
            self.short = max(getattr(self, 'short', 0), short)
        return out

    def extras(self):
        ci = self.R.ci
        m_t = np.bincount(ci.t[self.A], minlength=ci.T)
        ids = np.flatnonzero(self.E & np.isfinite(self.zE))
        o = np.lexsort((ci.c[ids], -self.zE[ids], ci.t[ids]))      # 新测量最差 (bad-score 最高) 在前
        ids = ids[o]
        tt = ci.t[ids]
        brk = np.flatnonzero(tt[1:] != tt[:-1]) + 1
        starts = np.r_[0, brk]
        lens = np.diff(np.r_[starts, len(ids)])
        pos = np.arange(len(ids)) - np.repeat(starts, lens)
        picked = ids[pos < m_t[tt]]
        return {'reverse_new_order': (self._mk(picked), int(m_t.sum() - len(picked)))}


class StateSpec(Spec):
    """FOCAL real_state: base & ~(leg_drop & state); 随机 = 状态在当日 pool0 内同人数随机。"""

    def __init__(self, R, base_c, legdrop_c, state_c):
        self.R, self.base, self.ld, self.st = R, base_c, legdrop_c, state_c
        self.X = np.ones(R.ci.n, bool)

    def draw(self, kind, bs):
        q = self.R.bank.quota_of(kind, self.st)
        out = []
        for b in bs:
            sel, short = self.R.bank.pick(kind, b, self.X, q)
            st = np.zeros(self.R.ci.n, bool)
            st[sel] = True
            out.append((np.flatnonzero(self.base & ~(self.ld & st)), None))
        return out


class EdgeSpec(Spec):
    """RL: 保留母体最好 80% 不动; 合并边缘域 (有成本值) 内随机取与真实同样多只。"""

    def __init__(self, R, keep_c, dom_c, pick_c):
        self.R, self.keep, self.dom, self.pk = R, keep_c, dom_c, pick_c

    def draw(self, kind, bs):
        q = self.R.bank.quota_of(kind, self.pk)
        out = []
        for b in bs:
            sel, short = self.R.bank.pick(kind, b, self.dom, q)
            k = self.keep.copy()
            k[sel] = True
            out.append((np.flatnonzero(k), None))
        return out


# ============================================================ 由描述符构造规格 (镜像 e6i_stage2.Runner.build)
def _blend(old, new, a, policy):
    return OP._blend(old, new, a, policy)


def buffered_child_cached(S, M, child, b):
    """与 e6i_stage2.buffered_child 同式; 放宽圈 ring 与 Tdrop 只依赖 (母体, b), 缓存在母体上。
       逐位等价由 build_spec 对真实子名单断言 (与 Stage 2 的非缓存版比)。"""
    import e6g_l as L6
    cache = M.__dict__.setdefault('_bufcache', {})
    if b not in cache:
        ctx, cfg = M.ctx, M.cfg
        ring = (L6.relaxed_domain(ctx, cfg['core'], b)[0] & ~L6.relaxed_domain(ctx, cfg['core'], 0)[0])
        cache[b] = (ring, L6.veto_drop(ctx, cfg))
    ring, Tdrop = cache[b]
    tg, _ = L6.buffered_targets(S, child, child | ring, Tdrop, M.score, 'matchN')
    return tg.astype(bool)


def build_spec(R, r):
    S, ci = R.S, R.ci
    M = R.mother(r['mother_id'])
    route, role, mid = r['route_id'], r['role'], r['member_id']
    s, pol, dirn = r['strength'], str(r.get('policy') or ''), r['direction']
    if pol == 'nan':
        pol = ''
    real_mask, wmul, info = R.RN.build(r)                    # 真实子名单 (与 Stage 2 同一函数)

    def mean_slot_fn(i, a, policy, make_new=lambda zp: zp):
        legs = M.legs_c
        k = len(legs)
        comp = M.core['fam'].startswith('KTC')
        # _day_ok 与恒等置换同 (有效集不随置换变) -> 用真实新腿算一次
        def fn(zp):
            nl = _blend(legs[i][None, :], make_new(zp), a, policy)
            if k == 1:
                return nl
            A = [np.broadcast_to(L[None, :], nl.shape) if j != i else nl for j, L in enumerate(legs)]
            tot = None
            cnt = None
            for Aj in A:
                v = np.where(np.isnan(Aj), 0.0, Aj)
                tot = v.copy() if tot is None else tot + v
                cj = (~np.isnan(Aj)).astype(np.intp)
                cnt = cj if cnt is None else cnt + cj
            with np.errstate(invalid='ignore', divide='ignore'):
                out = tot / cnt
            out = np.where(fn.dayok[ci.t][None, :], out, np.nan)
            if comp:
                anyn = np.zeros(nl.shape, bool)
                for Aj in A:
                    anyn |= np.isnan(Aj)
                out = np.where(anyn, np.nan, out)
            return out
        fn.dayok = None
        return fn

    def dayok_of(fn, zc):
        nl = _blend(M.legs_c[fn.i][None, :], fn.make_new(zc[None, :]), fn.a, fn.policy)[0]
        ok = np.ones(ci.T, bool)
        for j, L in enumerate(M.legs_c):
            x = nl if j == fn.i else L
            ok &= np.bincount(ci.t[np.isfinite(x)], minlength=ci.T) > 0
        return ok

    def slot_mean(leg, z_full, a, policy, make_new=lambda zp: zp):
        i = M.leg_roles.index(leg)
        fn = mean_slot_fn(i, a, policy, make_new)
        fn.i, fn.a, fn.policy, fn.make_new = i, a, policy, make_new
        zc = z_full[ci.t, ci.c]
        fn.dayok = dayok_of(fn, zc)
        sc0 = fn(zc[None, :])[0]
        dom = KeepDom(ci, np.isfinite(sc0), M.core['s'])
        return ShuffleSpec(R, M, z_full, fn, dom=dom, real_mask=real_mask)

    if role in ('SLOT', 'COMMON_SUPPORT'):
        leg = S2.SLOT_LEG[route]
        a = float(s)
        policy = 'COMMON_SUPPORT' if role == 'COMMON_SUPPORT' else pol
        if a == 0.0:
            return None, real_mask, wmul, 'alpha0_identity'
        if M.kind == 'dep' and leg == 'T':
            znew = OP._ns_pct_within(S, SB.raw_member(S, mid), M.s1, 'hi' if dirn == 'high_bad' else 'lo')
            fn = lambda zp: _blend(M.score_c[None, :], zp, a, policy)
            sc0 = fn(znew[ci.t, ci.c][None, :])[0]
            dom = KeepDom(ci, np.isfinite(sc0) & M.s1_c, M.core['b'])
            return ShuffleSpec(R, M, znew, fn, dom=dom, real_mask=real_mask), real_mask, wmul, ''
        z = OP._dirpct(S, mid, dirn)
        if M.kind == 'dep':                                   # R1 K 槽位: 两阶段完整重算
            fn = lambda zp: _blend(M.Px_c[None, :], zp, a, policy)
            sc0 = fn(z[ci.t, ci.c][None, :])[0]
            dom = KeepDom(ci, np.isfinite(sc0), M.core['a'])
            return ShuffleSpec(R, M, z, fn, dom=dom, dep_k=(M.core['a'], M.core['b']),
                               real_mask=real_mask), real_mask, wmul, ''
        return slot_mean(leg, z, a, policy), real_mask, wmul, ''
    if role == 'T_PAIR':
        lv, cv = mid.split('+')
        b = float(s)
        if M.kind == 'dep':
            zl = OP._ns_pct_within(S, SB.raw_member(S, lv), M.s1, 'hi')[ci.t, ci.c]
            zc_full = OP._ns_pct_within(S, SB.raw_member(S, cv), M.s1, 'hi')
            fn = lambda zp: np.where(np.isfinite(zl)[None, :] & np.isfinite(zp), (1 - b) * zl[None, :] + b * zp,
                                     np.nan)
            sc0 = fn(zc_full[ci.t, ci.c][None, :])[0]
            dom = KeepDom(ci, np.isfinite(sc0) & M.s1_c, M.core['b'])
            return ShuffleSpec(R, M, zc_full, fn, dom=dom, real_mask=real_mask), real_mask, wmul, ''
        zl = OP._dirpct(S, lv, 'high_bad')[ci.t, ci.c]
        zc_full = OP._dirpct(S, cv, 'high_bad')
        mk = lambda zp: np.where(np.isfinite(zl)[None, :] & np.isfinite(zp), (1 - b) * zl[None, :] + b * zp,
                                 np.nan)
        return slot_mean('T', zc_full, 1.0, 'FULL_REPLACE', make_new=mk), real_mask, wmul, ''
    if role == 'ADD_SCORE':
        g = float(s)
        if g == 0.0:
            return None, real_mask, wmul, 'gamma0_identity'
        if M.kind == 'dep':
            z = OP._ns_pct_within(S, SB.raw_member(S, mid), M.s1, 'hi' if dirn == 'high_bad' else 'lo')
            dom_mask = M.s1_c
            pk = M.core['b']
        else:
            z = OP._dirpct(S, mid, dirn)
            dom_mask = np.ones(ci.n, bool)
            pk = M.core['s']
        fn = lambda zp: np.where(np.isfinite(zp), (1 - g) * M.score_c[None, :] + g * zp, M.score_c[None, :])
        sc0 = fn(z[ci.t, ci.c][None, :])[0]
        dom = KeepDom(ci, np.isfinite(sc0) & dom_mask, pk)
        return ShuffleSpec(R, M, z, fn, dom=dom, real_mask=real_mask), real_mask, wmul, ''
    z = OP._dirpct(S, mid, dirn) if (mid in FE.CATALOG_IDS and dirn in ('high_bad', 'low_bad')) else None
    if role in ('VETO_NEW', 'SOFT_HARD'):
        rem = ci.of(info['removed'])
        return DeleteSpec(R, M.B_c, rem, reverse_z=z[ci.t, ci.c]), real_mask, wmul, ''
    if role == 'SOFT':
        tox = ci.of(info['toxic'])
        return DeleteSpec(R, M.B_c, tox, wmul=float(s)), real_mask, wmul, ''
    if role == 'SWAP':
        state = None
        if r.get('state_member') and str(r.get('state_member')) != 'nan':
            state = S2.state_mask(S, str(r['state_member']), str(r['state']))
        out_score = None
        if 'out=max_K' in pol:
            out_score = M.legs[M.leg_roles.index('K')] if M.kind != 'dep' else M.Px
        B2, inf2 = M.swap(z, float(s), out_score=out_score, state=state)
        E = M.E_set()
        if state is not None:
            E = E & state
        Ed = ci.of(E & np.isfinite(z))
        D = ci.of(M.B & ~B2)
        A = ci.of(B2 & ~M.B)
        bb = r.get('buffer_b')
        bb = int(float(bb)) if (bb is not None and str(bb) != 'nan') else 0
        if bb > 0:                                             # 缓存版缓冲必须逐格复现 Stage 2 真实子名单
            chk = buffered_child_cached(S, M, B2, bb)
            if not np.array_equal(chk, np.asarray(real_mask, bool)):
                raise ValueError('buffered_child_cached 与 Stage 2 不一致: %d 格' % int((chk != real_mask).sum()))
        return SwapSpec(R, M, M.B_c, D, A, Ed, z[ci.t, ci.c], buffer_b=bb), real_mask, wmul, ''
    if role == 'RL':
        cost = OP._dirpct(S, mid, 'high_bad')
        keep_c, dom_c, pick_c = rl_parts(R, M, cost)
        return EdgeSpec(R, keep_c, dom_c, pick_c), real_mask, wmul, ''
    if role == 'FOCAL_NEW':
        focal = pol.split('@')[0]
        arm = str(s)
        if arm.startswith('replace_'):
            arm = 'new'
        elif arm.startswith('both_'):
            arm = 'both'
        if arm in DET_ARMS:
            return None, real_mask, wmul, 'deterministic_arm'
        names = [v['name'] for v in M.veto_legs]
        leg = M.veto_legs[names.index(focal)]
        if M.kind in ('mean', 'single'):
            keep, _ = M._keep_mean(M.legs)
        else:
            keep, _, _ = M._keep_dep()
        base = keep & ~M.veto_drop(exclude=(focal,))
        base_c = ci.of(base)
        if arm in ('new', 'both'):
            child_c = ci.of(real_mask)
            fixed = ci.of(leg['drop'] & base) if arm == 'both' else None
            X = (base_c & ~fixed) if fixed is not None else base_c.copy()
            rem = X & ~child_c
            assert rem.dtype == bool and X.dtype == bool
            return DeleteSpec(R, base_c, rem, fixed_drop_c=fixed), real_mask, wmul, ''
        if arm == 'real_state':
            st_name = pol.split('@')[1] if '@' in pol else r.get('direction_role')
            state = S2.focal_state(S, mid, st_name)
            st_c = (np.asarray(state, bool) & S.p0c)[ci.t, ci.c]
            return StateSpec(R, base_c, ci.of(leg['drop'] & S.p0c), st_c), real_mask, wmul, ''
        raise ValueError('未知焦点臂 %s' % arm)
    if role == 'FOURARM':
        return None, real_mask, wmul, 'fourarm_no_zmap'
    raise ValueError('role 未实现: %s' % role)


def rl_parts(R, M, cost_score, keep_frac=0.8):
    """镜像 Mother.edge_replace: 返回 (保留最好 80%, 有成本值的合并边缘域, 真实所选)。"""
    S, ci = R.S, R.ci
    keep = np.zeros_like(M.B)
    domm = np.zeros_like(M.B)
    pick = np.zeros_like(M.B)
    avail = (M.p0 if M.kind != 'dep' else M.s1) & ~M.dr & np.isfinite(M.score)
    for t in range(S.T):
        b = np.where(M.B[t] & np.isfinite(M.score[t]))[0]
        if len(b) == 0:
            continue
        ob = b[np.lexsort((b, M.score[t][b]))]
        nk = int(np.floor(keep_frac * len(ob)))
        kp, tail = ob[:nk], ob[nk:]
        m = len(tail)
        cand = np.where(avail[t] & ~M.B[t])[0]
        nxt = cand[np.lexsort((cand, M.score[t][cand]))[:m]]
        dom = np.concatenate([tail, nxt])
        cs = cost_score[t][dom]
        ok = np.isfinite(cs)
        dom, cs = dom[ok], cs[ok]
        pk = dom[np.lexsort((dom, cs))[:m]] if len(dom) else dom
        keep[t, kp] = True
        domm[t, dom] = True
        pick[t, pk] = True
    return ci.of(keep), ci.of(domm), ci.of(pick)


# ============================================================ 运行
def acct(R, ids, wm, Hs):
    t, c = R.cells_tc(ids)
    w = R.SE.dev(t, c)
    if wm is not None:
        w = w * wm
    return R.SE.pnl(t, c, w, Hs, I.COST)


def run_config(R, rs, npaths, kinds, stage2_rows=None, path_start=0):
    """一个配置 (共享掩码的 H 组) -> 汇总行 + 逐路径数组 + 路径均值逐日序列。"""
    r0 = rs[0]
    Hs = sorted(int(r['H']) for r in rs)
    spec, real_mask, wmul, why = build_spec(R, r0)
    ci = R.ci
    real_ids = np.flatnonzero(ci.of(real_mask))
    real_w = None
    if wmul is not None:
        real_w = np.asarray(wmul, np.float64)[ci.t[real_ids], ci.c[real_ids]]
    real = acct(R, real_ids, real_w, Hs)
    rows, arrays = [], {}
    anchor = {}
    for r in rs:
        H = int(r['H'])
        a = I.ann(real[H][3])
        anchor[H] = a
        if stage2_rows is not None and r['descriptor_id'] in stage2_rows:
            s2 = stage2_rows[r['descriptor_id']]
            anchor[H] = (a, s2, abs(a - s2))
    if spec is None:
        for r in rs:
            rows.append(dict(descriptor_id=r['descriptor_id'], status='NO_ZMAP', note=why))
        return rows, arrays, anchor, None
    noop = None
    if isinstance(spec, ShuffleSpec):
        ids0, _ = spec.identity()
        noop = int(np.sum(ci.of(real_mask)) != len(ids0)) or \
            int(not np.array_equal(np.sort(ids0), real_ids))
    for kind in kinds:
        bs = list(range(path_start, path_start + npaths))
        draws = spec.draw(kind, bs)
        per = {H: dict(net=np.empty(len(bs)), gross=np.empty(len(bs)), turn=np.empty(len(bs)),
                       pos=np.empty(len(bs)), net12=np.empty(len(bs))) for H in Hs}
        dsum = {H: np.zeros(R.S.T) for H in Hs}
        for j, (ids, wm) in enumerate(draws):
            res = acct(R, ids, wm, Hs)
            for H in Hs:
                g, p, u, n = res[H]
                per[H]['net'][j] = I.ann(n)
                per[H]['gross'][j] = I.ann(g)
                per[H]['turn'][j] = float(np.nanmean(u))
                per[H]['pos'][j] = float(np.nanmean(p))
                per[H]['net12'][j] = I.ann(g - u * I.COST_HI / 1e4)
                dsum[H] += n
        for r in rs:
            H = int(r['H'])
            x = per[H]['net']
            real_n = I.ann(real[H][3])
            k = len(x)
            rows.append(dict(descriptor_id=r['descriptor_id'], status='SUCCEEDED', kind=kind, n_paths=k,
                             route_id=r0['route_id'], mother_id=r0['mother_id'], member_id=r0['member_id'],
                             role=r0['role'], H=H, representative=bool(r0.get('representative')),
                             real_net8_ann=real_n, real_gross_ann=I.ann(real[H][0]),
                             real_turn=float(np.nanmean(real[H][2])), real_pos=float(np.nanmean(real[H][1])),
                             rand_net8_mean=float(np.mean(x)), rand_net8_sd=float(np.std(x, ddof=1)),
                             rand_net8_mcse=float(np.std(x, ddof=1) / np.sqrt(k)),
                             rand_gross_mean=float(np.mean(per[H]['gross'])),
                             rand_net12_mean=float(np.mean(per[H]['net12'])),
                             rand_turn_mean=float(np.mean(per[H]['turn'])),
                             rand_pos_mean=float(np.mean(per[H]['pos'])),
                             d_real_minus_rand=real_n - float(np.mean(x)),
                             diagnostic_tail_fraction=float((1 + np.sum(x >= real_n)) / (1 + k)),
                             pick_shortfall=int(getattr(spec, 'short', 0)), noop_mismatch=noop))
            key = '%s||%s' % (r['descriptor_id'], kind)
            arrays[key + '||net'] = per[H]['net']
            arrays[key + '||gross'] = per[H]['gross']
            arrays[key + '||dmean'] = dsum[H] / k
    ex = spec.extras() if path_start == 0 else {}
    for nm, ((ids, wm), restricted) in ex.items():
        res = acct(R, ids, wm, Hs)
        for r in rs:
            H = int(r['H'])
            g, p, u, n = res[H]
            rows.append(dict(descriptor_id=r['descriptor_id'], status='SUCCEEDED', kind=nm, n_paths=1,
                             route_id=r0['route_id'], mother_id=r0['mother_id'], member_id=r0['member_id'],
                             role=r0['role'], H=H, representative=bool(r0.get('representative')),
                             real_net8_ann=I.ann(real[H][3]), rand_net8_mean=I.ann(n),
                             rand_gross_mean=I.ann(g), rand_turn_mean=float(np.nanmean(u)),
                             rand_pos_mean=float(np.nanmean(p)),
                             d_real_minus_rand=I.ann(real[H][3]) - I.ann(n), restricted_shortfall=restricted))
            arrays['%s||%s||daily' % (r['descriptor_id'], nm)] = n
    return rows, arrays, anchor, noop


def need_random(r):
    if r['route_id'] in ('M1', 'M2', 'FOURARM'):
        return False
    if r['role'] == 'FOCAL_NEW' and str(r['strength']) in DET_ARMS:
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--route', required=True)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshard', type=int, default=1)
    ap.add_argument('--kinds', default=','.join(KINDS))
    ap.add_argument('--paths-mult', type=int, default=1, help='首轮 1; MCSE 触发的加轮另写标签')
    ap.add_argument('--selftest', type=int, default=0, help='每 (角色, 母体) 取 n 个配置, 每类 8 条路径')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--path-start', type=int, default=0, help='加轮: 路径编号起点 (新 draw, 不重复首轮)')
    ap.add_argument('--only-list', default='', help='加轮: 只跑该 csv (descriptor_id 列) 里出现的配置')
    a = ap.parse_args()
    assert a.segment in I.DERIV_SEGS
    t0 = time.time()
    FE.build_catalog()
    FE.CATALOG_IDS = {m['member_id'] for m in FE.CATALOG}
    I.set_protected_members(FE.protected_ids())
    dd = pd.read_csv(os.path.join(I.RES, 'registry', 'descriptors_A0.csv'), low_memory=False)
    dd = dd[dd.route_id == a.route]
    groups = collections.OrderedDict()
    for r in dd.to_dict('records'):
        if need_random(r):
            groups.setdefault(S2.config_key(r), []).append(r)
    keys = list(groups)
    if a.selftest:
        seen = collections.Counter()
        sk = []
        for k in keys:
            r0 = groups[k][0]
            tag = (r0['role'], r0['mother_id'], str(r0.get('policy')))
            if seen[tag] < a.selftest:
                seen[tag] += 1
                sk.append(k)
        keys = sk
    else:
        if a.only_list:
            want = set(pd.read_csv(a.only_list).descriptor_id)
            keys = [k for k in keys if any(r['descriptor_id'] in want for r in groups[k])]
        keys = keys[a.shard::a.nshard]
    if a.limit:
        keys = keys[:a.limit]
    kinds = [k for k in a.kinds.split(',') if k]
    S = I.seg_i(a.segment, warm=False)
    R = RCtx(S, a.segment)
    # Stage 2 真实账户 (对账锚)
    s2 = {}
    import glob
    for f in glob.glob(os.path.join(I.RES, 'accounts', a.segment, '%s_*.csv' % a.route)):
        if '_timing' in f:
            continue
        d = pd.read_csv(f, low_memory=False)
        if 'net8_ann' in d:
            d = d[d.status == 'SUCCEEDED']
            s2.update(dict(zip(d.descriptor_id, d.net8_ann)))
    print('段就绪 %.0fs; %s shard %d/%d: %d 配置%s; Stage 2 对账行 %d'
          % (time.time() - t0, a.route, a.shard, a.nshard, len(keys),
             ' (selftest)' if a.selftest else '', len(s2)), flush=True)
    rows, arrays = [], {}
    n_fail = 0
    anc_rows = []
    for gi, k in enumerate(keys):
        rs = groups[k]
        r0 = rs[0]
        mid = r0['member_id']
        members = [x for x in str(mid).replace('+', '|').split('|') if x in FE.CATALOG_IDS]
        ts = time.time()
        np_ = 8 if a.selftest else int(r0['random_priority']) * a.paths_mult
        try:
            I.guard_i(members, [S2.ROLE_RULE.get(r0['role'], r0['role'])], segment=a.segment,
                      label_end=str(S.dates[-1].date()), use='trade', where='zmap:' + r0['descriptor_id'])
            rw, ar, anc, noop = run_config(R, rs, np_, kinds, s2, path_start=a.path_start)
            rows.extend(rw)
            arrays.update(ar)
            for H, v in anc.items():
                if isinstance(v, tuple):
                    anc_rows.append(dict(config=r0['descriptor_id'], H=H, sparse=v[0], stage2=v[1],
                                         abs_diff=v[2], noop_mismatch=noop))
                else:
                    anc_rows.append(dict(config=r0['descriptor_id'], H=H, sparse=v, stage2=np.nan,
                                         abs_diff=np.nan, noop_mismatch=noop))
        except Exception as e:
            n_fail += 1
            traceback.print_exc()
            for r in rs:
                rows.append(dict(descriptor_id=r['descriptor_id'], status='FAILED_TECH',
                                 note='%s: %s' % (type(e).__name__, str(e)[:150])))
        if (gi + 1) % 10 == 0 or a.selftest:
            print('  %d/%d 配置 %.0fs (末个 %.1fs, %d 路径 x %d 类)'
                  % (gi + 1, len(keys), time.time() - t0, time.time() - ts, np_, len(kinds)), flush=True)
    od = os.path.join(I.RES, 'randoms', a.segment)
    os.makedirs(od, exist_ok=True)
    tag = ('selftest_%s' % a.route) if a.selftest else ('%s_%02d' % (a.route, a.shard) + ('_timing' if a.limit else '') +
                                                       ('_x%d' % a.paths_mult if a.paths_mult > 1 else '') + ('_p%d' % a.path_start if a.path_start else ''))
    d = pd.DataFrame(rows)
    p_csv = os.path.join(od, tag + '.csv')
    I.atomic_write_csv(p_csv, d)
    p_anc = os.path.join(od, tag + '_anchor.csv')
    an = pd.DataFrame(anc_rows)
    I.atomic_write_csv(p_anc, an)
    outs = [p_csv, p_anc]
    if arrays:
        buf = io.BytesIO()
        ks = sorted(arrays)
        np.savez(buf, keys=np.asarray(ks), **{'a%d' % i: arrays[k] for i, k in enumerate(ks)})
        p_npz = os.path.join(od, tag + '.npz')
        I.atomic_write_bytes(p_npz, buf.getvalue())
        outs.append(p_npz)
    mx = float(an.abs_diff.max()) if len(an) and an.abs_diff.notna().any() else float('nan')
    nm = int((an.noop_mismatch.fillna(0) > 0).sum()) if len(an) else 0
    I.write_receipt(os.path.join(I.RES, 'task_status', 'zmap_%s_%s.receipt.json' % (a.segment, tag)),
                    'zmap:%s:%s' % (a.segment, tag), outs, status='SUCCEEDED' if n_fail == 0 else 'FAILED',
                    n_fail=n_fail, n_configs=len(keys), stage2_anchor_max_abs=mx, noop_mismatch_rows=nm,
                    elapsed_s=round(time.time() - t0, 1))
    print('[%s %s] 配置 %d / 失败 %d; 对 Stage 2 真实账户最大差 %.2e (年化百分点); no-op 不符 %d 行; %.0fs'
          % (a.segment, tag, len(keys), n_fail, mx, nm, time.time() - t0))
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == '__main__':
    main()
