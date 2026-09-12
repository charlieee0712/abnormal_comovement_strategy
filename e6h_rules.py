#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 的六类新规则算子 (plan §3.2 / §4.2, brief §5)。

每个算子都必须有【真正的 identity 实现】—— 不是"用一个看起来极端的参数近似源父"
(plan §4.3)。所以每个算子的 identity 端点在【加载新因子之前就短路】, 直接返回源父,
这样"零系数仍触发缺失"这类问题从构造上不可能发生。

算子与 identity:
  SLOT_FALLBACK / SLOT_REPLACE   alpha=0 -> 源父 (短路)
  FOCAL_REPLACE / FOCAL_CONDITION 全开 -> 原焦点否决; 全关 -> 无焦点父
  ADD / SWAP                      eta=0 -> 原 B (短路)
  CONJ                            Jbad 全真 -> 原父; 无上限加回 = C ∪ (E\\C)\\Jbad 恒等
  MARGIN                          e=0 -> 原 B (短路)
  SOFT_DEWEIGHT                   lambda=0 -> 原父 (短路)

FALLBACK 与 REPLACE 【必须分名】(plan §3.2): FALLBACK 在 alpha=1 时, 新测量缺失的
票仍用旧测量, 所以它是"新测量优先的混合规则"而不是完全消融; REPLACE 在 alpha=1
时完全不访问旧焦点输入, 新测量缺失按该独立规则的合法域处理, 不退回旧腿。
"""
from __future__ import annotations
import hashlib

import numpy as np
import pandas as pd

import e6h_core as H
import e6g_core as G
import e6g_desc as GD
import e6f_core as F
import e6e_core as K


# ---------------------------------------------------------------- 小工具
def round_half_up(x):
    return int(np.floor(np.asarray(x, float) + 0.5))


_HASH_CACHE = {}


def ticker_order(cols):
    """固定 ticker 哈希序 —— 主平局用它, 不加日期随机制造换手 (plan §4.2)。"""
    key = id(cols)
    if key not in _HASH_CACHE:
        h = np.array([int(hashlib.sha256(str(c).encode()).hexdigest()[:8], 16)
                      for c in cols], dtype=np.int64)
        _HASH_CACHE[key] = h
    return _HASH_CACHE[key]


def topk_by(score, avail, k, tiebreak, largest=False):
    """逐日在 avail 内按 score 取 k 个 (默认取【小】, 与 bad_pct 约定一致)。
       平局用 tiebreak (ticker 哈希) 定序。返回 (T, Nc) bool。"""
    T, Nc = score.shape
    out = np.zeros((T, Nc), bool)
    for t in range(T):
        m = avail[t] & np.isfinite(score[t])
        n = int(m.sum())
        if n == 0 or k[t] <= 0:
            continue
        kk = min(int(k[t]), n)
        idx = np.where(m)[0]
        s = score[t][idx]
        if largest:
            s = -s
        order = np.lexsort((tiebreak[idx], s))
        out[t, idx[order[:kk]]] = True
    return out


# ---------------------------------------------------------------- SLOT
def slot_score(ctx, core, leg_idx, new_pct, alpha, policy):
    """把核心第 leg_idx 条腿的 pct 换成 (1-a)*old + a*new。
       policy='FALLBACK': new 缺失处用 old (所以 a=1 仍依赖 old)
       policy='REPLACE' : a=1 时完全不用 old; 0<a<1 按两者【共同活跃域】
       返回 (score, active_domain)。"""
    S = ctx.S
    md = core.get('neu', 'NS') or 'NS'
    dirs = core.get('dirs') or ['hi'] * len(core['comps'])
    tfs = core.get('tfs') or ['identity'] * len(core['comps'])
    Ps = [ctx.leg_pct(sp, md, dirs[i] if i < len(dirs) else 'hi',
                      tfs[i] if i < len(tfs) else 'identity')
          for i, sp in enumerate(core['comps'])]
    old = Ps[leg_idx]
    a = float(alpha)
    if policy == 'FALLBACK':
        blend = np.where(np.isfinite(new_pct), (1 - a) * old + a * new_pct, old)
        dom = np.isfinite(old)
    elif policy == 'REPLACE':
        if a >= 1.0:
            blend = new_pct
            dom = np.isfinite(new_pct)
        else:
            both = np.isfinite(old) & np.isfinite(new_pct)
            blend = np.where(both, (1 - a) * old + a * new_pct, np.nan)
            dom = both
    else:
        raise ValueError(policy)
    Ps2 = list(Ps)
    Ps2[leg_idx] = blend
    if len(Ps2) == 1:
        score = Ps2[0]
    else:
        score = F.combine_dense(Ps2, 'mean', complete=core['fam'].startswith('KTC'))
    return score, dom


def apply_slot(ctx, cfg, leg_idx, new_key, alpha, policy):
    """返回 (mask, score, cand, note)。alpha=0 在【加载新因子之前】短路回源父。"""
    core = cfg['core']
    if float(alpha) == 0.0:
        B, sc, cand, C = ctx.full_mask_g(cfg)
        return B, sc, cand, 'identity_alpha0_shortcircuit'
    sp = GD.spec_of_key(new_key) if new_key in H.U74 else H.specH(new_key)
    new_pct = H.get_pct_h(ctx.S, sp, core.get('neu', 'NS') or 'NS', 'hi')
    score, dom = slot_score(ctx, core, leg_idx, new_pct, alpha, policy)
    sel = core.get('sel', 'SRC')
    m = ctx._keep(score, ctx.S.p0c, core['s'], sel, core.get('depth'))
    dr = ctx.build_veto_drop_g(cfg.get('veto'), core, None,
                               sel=('QEDGE' if sel == 'QEDGE' else 'SRC'))
    B = (m & ~dr) if dr is not None else m
    return B, score, ctx.S.p0c, 'slot_%s_a%s' % (policy.lower(), alpha)


# ---------------------------------------------------------------- FOCAL
def apply_focal(ctx, cfg, focal_idx, state=None, mode='original', k=None):
    """焦点否决的四对照 + 条件化。
       mode: 'none'      拆掉焦点否决 (非焦点规则不动)
             'original'  原焦点否决 (= 源父)
             'replace'   用 new_key 换焦点 (由调用方把 veto legs 改好后传进来)
             'enable'    只在 state 为真处启用焦点   -> V_f ∩ S
             'exempt'    在 state 为真处豁免焦点     -> V_f \\ S
       identity: mode='original' 必须逐位 = 源父; 'enable' 且 state 全真 = original;
                 'exempt' 且 state 全假 = original。"""
    core = cfg['core']
    sel = core.get('sel', 'SRC')
    m, score, cand = ctx.build_core_g(core)
    veto = cfg.get('veto')
    if veto is None:
        return m, 'no_veto'
    legs = list(veto['legs'])
    dropf = (G.drop_SRC if sel != 'QEDGE'
             else (lambda P, pp, kk: G.drop_QEDGE(P, pp, kk, report=ctx.report)))
    md = core.get('neu_veto') or core.get('neu', 'NS') or 'NS'
    p0 = ctx.S.p0c
    dr = np.zeros_like(m)
    for i, (sp, kk) in enumerate(legs):
        P = ctx.leg_pct(sp, md, veto.get('dir', 'hi'), veto.get('tf', 'identity'))
        kuse = kk if (i != focal_idx or k is None) else k
        leg_drop = dropf(P, p0, kuse)
        if i == focal_idx:
            if mode == 'none':
                continue
            if mode == 'enable':
                leg_drop = leg_drop & state
            elif mode == 'exempt':
                leg_drop = leg_drop & (~state)
        dr |= leg_drop
    return (m & ~dr), 'focal_%s' % mode


# ---------------------------------------------------------------- ADD / SWAP
def apply_add(B, D, g_score, eta, cols, cond=None):
    """B' = B ∪ A, A = D(∩cond) 内按 g 最好的 min(m, |Q|) 只, m = round_half_up(eta*|B|)。
       eta=0 短路回 B。"""
    if float(eta) == 0.0:
        return B.copy(), np.zeros_like(B), 'identity_eta0'
    tb = ticker_order(cols)
    Q = D & (cond if cond is not None else True)
    nb = B.sum(axis=1)
    m = np.array([round_half_up(float(eta) * n) for n in nb])
    A = topk_by(g_score, Q & (~B), m, tb, largest=False)
    return (B | A), A, 'add_eta%s' % eta


def apply_swap(B, D, g_score, edge_score, eta, cols, cond=None):
    """B' = (B\\R) ∪ A*, |R| = |A*| <= |B|; R 按父的【真实边缘分数】取最差,
       A* 按 g 取最好。人数不变 (但同人数 != 同仓位 != 同风险, plan §4.2)。"""
    if float(eta) == 0.0:
        return B.copy(), np.zeros_like(B), np.zeros_like(B), 'identity_eta0'
    tb = ticker_order(cols)
    Q = D & (cond if cond is not None else True)
    nb = B.sum(axis=1)
    m = np.array([round_half_up(float(eta) * n) for n in nb])
    A = topk_by(g_score, Q & (~B), m, tb, largest=False)
    na = A.sum(axis=1)
    R = topk_by(edge_score, B, na, tb, largest=True)     # 边缘分数最【差】= 分最高
    return ((B & ~R) | A), A, R, 'swap_eta%s' % eta


# ---------------------------------------------------------------- CONJ
def apply_conj(C, D, Jbad, V):
    """E = C ∪ D; C' = E \\ ((E\\C) ∩ Jbad); 再去 V。
       Jbad 全真 -> 原父; 与【无上限加回】C ∪ (E\\C)\\Jbad 恒等 (plan §4.2)。"""
    E = C | D
    extra = E & (~C)
    Cp = E & ~(extra & Jbad)
    return (Cp & ~V), 'conj'


def conj_identity_check(C, D, Jbad, V):
    """恒等式: C' = C ∪ ((E\\C) \\ Jbad)。返回 max 差 (应为 0)。"""
    E = C | D
    extra = E & (~C)
    a = (E & ~(extra & Jbad))
    b = C | (extra & ~Jbad)
    return int((a != b).sum())


# ---------------------------------------------------------------- MARGIN
def apply_margin(B, core_score, liq_score, e, cols, legal, order='cheap_first'):
    """保护按父核排序最好的 (1-e) 份额; 候选带 = B 最差 m 只 + 外侧按父核排序最近的
       最多 m 只合法票; 按流动性改善排序从带中取 m 只, 补回父原人数。
       e=0 短路回 B。所有票仍过原 veto (由 legal 保证)。"""
    if float(e) == 0.0:
        return B.copy(), 'identity_e0'
    tb = ticker_order(cols)
    T, Nc = B.shape
    out = np.zeros((T, Nc), bool)
    for t in range(T):
        bidx = np.where(B[t])[0]
        nb = len(bidx)
        if nb == 0:
            continue
        m = round_half_up(float(e) * nb)
        if m <= 0:
            out[t] = B[t]
            continue
        s = core_score[t]
        ok = np.isfinite(s[bidx])
        if ok.sum() < nb:
            out[t] = B[t]
            continue
        order_b = bidx[np.lexsort((tb[bidx], s[bidx]))]      # 分低 = 好
        protect = order_b[:max(0, nb - m)]
        worst = order_b[max(0, nb - m):]
        outside = np.where(legal[t] & (~B[t]) & np.isfinite(s))[0]
        if len(outside):
            near = outside[np.lexsort((tb[outside], s[outside]))][:m]
        else:
            near = np.array([], int)
        band = np.concatenate([worst, near])
        if len(band) == 0:
            out[t] = B[t]
            continue
        ls = liq_score[t][band]
        good = np.isfinite(ls)
        band, ls = band[good], ls[good]
        if len(band) == 0:
            out[t] = B[t]
            continue
        if order == 'cheap_first':
            pick = band[np.lexsort((tb[band], ls))][:m]          # 流动性成本低优先
        elif order == 'expensive_first':
            pick = band[np.lexsort((tb[band], -ls))][:m]
        elif order == 'source':
            pick = band[np.lexsort((tb[band], s[band]))][:m]
        else:                                                    # random_in_band
            rs = np.random.default_rng(20260912 + t).random(len(band))
            pick = band[np.argsort(rs)][:m]
        out[t, protect] = True
        out[t, pick] = True
    return out, 'margin_e%s_%s' % (e, order)


# ---------------------------------------------------------------- 软降权
def apply_soft(B, bad, lam):
    """w_new = w_parent * (1 - lam*I_bad), 释放的资本【留现金】(不归一)。
       lam=0 -> 原父; lam=1 是冻权删票, 与"删除后重算 DEV"的硬端点【不同】,
       两者分开计 (plan §3.2)。返回 (mask, 权重乘子)。"""
    if float(lam) == 0.0:
        return B.copy(), np.ones(B.shape), 'identity_lam0'
    mul = np.where(B & bad, 1.0 - float(lam), 1.0)
    return B.copy(), mul, 'soft_lam%s' % lam


# ---------------------------------------------------------------- 账本
def run_mask(S, mask, wmul=None, H_hold=None, cost_bp=None):
    """mask -> DEV -> 引擎。wmul 是逐格权重乘子 (软降权用), 释放的资本留现金。"""
    idx, val = F.dev_from_dense(S, mask)
    if wmul is not None:
        val = [v * wmul[t, idx[t]] if len(idx[t]) else v for t, v in enumerate(val)]
    return F.sparse_pnl_H(S, idx, val,
                          H_hold if H_hold is not None else K.HOLD,
                          cost_bp if cost_bp is not None else F.COST)
