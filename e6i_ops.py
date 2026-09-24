#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 2 母体上下文与角色算子 (plan §5.2-§5.7; brief §6)。

只【包】源的已锚部件, 不改口径:
  keep  = e6g_core.keep_SRC (= e6f keep_mask_dense, 源 P2G 分箱语义; 池内有值 < 3g 当日空仓)
  veto  = e6g_core.drop_SRC (= e6f drop_mask_dense; 池级毒尾 1/k, 无值票也算剔除)
  mean  = e6f_core.combine_dense (KTC 完整腿)
  pct   = F.neu_cache + G.pct_dense_dir (与 E6h 同一路径)
约定: 所有分数 "高 = 差" (bad-score), keep 保留低分端 (与源一致)。
新成员的方向在 role 层给出: direction='high_bad' -> 用 NS pct 'hi'; 'low_bad' -> 'lo' (真实反序)。

恒等 (阻断锚在 e6i_rule_anchors.py):
  SLOT α=0 / ADD_SCORE γ=0 / SWAP q=0 / SOFT λ=0 / RL 关 / FOCAL 'old' -> 逐位返回母体 B
  (α=0 在【读取新成员之前】短路, 不读新有效域 —— brief §13 反例)
  core_matchN(n = |B|) -> 逐位返回 B (continuation ordering 与源 keep 同一并列规则)
"""
from __future__ import annotations
import numpy as np
import pandas as pd

import e6i_core as I
import e6i_features as FE
import e6i_s1base as SB
import e6h_run_routes as RR
import e6g_core as G
import e6g_desc as GD
import e6f_core as F
import e6e_core as K


def _dirpct(S, mid, direction):
    """新成员的 bad-score: 'high_bad' -> NS pct hi; 'low_bad' -> NS pct lo。"""
    if direction == 'high_bad':
        return SB.pct_member(S, mid, direction='hi')
    if direction == 'low_bad':
        return SB.pct_member(S, mid, direction='lo')
    raise ValueError(direction)


def _ns_pct_within(S, raw_c, set_mask, direction='hi'):
    """把 (T, Nc) 原值在给定集合内按源口径中性化 (log 流通市值 OLS) 后排名 —— DEP 第二阶段用。"""
    df = pd.DataFrame(np.full((S.T, S.Nfull), np.nan), index=S.pool0.index, columns=S.pool0.columns)
    df.iloc[:, S.ccols] = raw_c
    sfull = np.zeros((S.T, S.Nfull))
    sfull[:, S.ccols] = set_mask.astype(float)
    sdf = pd.DataFrame(sfull, index=S.pool0.index, columns=S.pool0.columns)
    cache, _ = F.neu_cache(df, sdf, S.log_mcap, S.icodes_neu, 'NS')
    return G.pct_dense_dir(cache, S.dates, S.ccolpos, S.Nc, direction)


def _blend(old, new, a, policy):
    """plan §5.2: z_α = (1-α) z_old + α z_new。FALLBACK: 新缺用旧; FULL_REPLACE (α=1): 只用新有效域;
       COMMON_SUPPORT: 新旧共同有效域内比较 (诊断账户)。"""
    if policy in ('FALLBACK', 'FALLBACK_REPLACE'):
        return np.where(np.isfinite(new), (1 - a) * old + a * new, old)
    if policy == 'FULL_REPLACE':
        return new if a >= 1.0 else np.where(np.isfinite(old) & np.isfinite(new),
                                            (1 - a) * old + a * new, np.nan)
    if policy == 'COMMON_SUPPORT':
        return np.where(np.isfinite(old) & np.isfinite(new), (1 - a) * old + a * new, np.nan)
    raise ValueError(policy)


class Mother(object):
    """一个 (段, 母体) 的全部部件。B / score / dr 与 E6h ParentCtx 逐位相同 (锚)。"""

    def __init__(self, S, name):
        self.S, self.name = S, name
        self.P = P = RR.ParentCtx(S, name)
        self.cfg = P.cfg
        self.core = core = P.cfg['core']
        self.ctx = P.ctx
        self.p0 = S.p0c
        self.kind = core['kind']
        self.B, self.score, self.C, self.dr = P.B.astype(bool), P.score, P.C.astype(bool), \
            P.dr.astype(bool)
        # 否决逐腿 (焦点替换要能单独拆下一条)
        self.veto_legs = []
        veto = P.cfg.get('veto')
        if veto:
            for sp, k in veto['legs']:
                pct = self.ctx.leg_pct(sp, 'NS', 'hi', 'identity')
                self.veto_legs.append(dict(name='%s:k%d' % (_short(sp), k), sp=sp, k=k, pct=pct,
                                           drop=G.drop_SRC(pct, self.p0, k).astype(bool)))
        if self.kind in ('mean', 'single'):
            self.legs = [self.ctx.leg_pct(sp, 'NS', 'hi', 'identity') for sp in core['comps']]
            self.leg_roles = [sp['role'] for sp in core['comps']]
        else:                                             # DEP
            self.Px = self.ctx.leg_pct(core['x'], 'NS', 'hi', 'identity')
            self.s1 = G.keep_SRC(self.Px, self.p0, core['a']).astype(bool)
            self.T_raw = _raw_c(S, core['ys'][0])
            self.leg_roles = ['K', 'T']

    # ---------------------------------------------------------- 组装
    def veto_drop(self, exclude=()):
        dr = np.zeros_like(self.p0)
        for v in self.veto_legs:
            if v['name'] not in exclude:
                dr |= v['drop']
        return dr

    def _keep_mean(self, legs):
        core = self.core
        if len(legs) == 1:
            score = legs[0]
        else:
            score = F.combine_dense(legs, 'mean', complete=core['fam'].startswith('KTC'))
        keep = G.keep_SRC(score, self.p0, core['s']).astype(bool)
        return keep, score

    def _keep_dep(self, Px=None, stage2=None, s1=None):
        core = self.core
        if s1 is None:
            s1 = self.s1 if Px is None else G.keep_SRC(Px, self.p0, core['a']).astype(bool)
        if stage2 is None:
            stage2 = self.P.score if (Px is None) else _ns_pct_within(self.S, self.T_raw, s1, 'hi')
        keep = G.keep_SRC(stage2, s1, core['b']).astype(bool)
        return keep, stage2, s1

    def rebuild(self):
        """从部件重组 B —— 锚: 必须逐位等于 ParentCtx.B。"""
        if self.kind in ('mean', 'single'):
            keep, _ = self._keep_mean(self.legs)
        else:
            keep, _, _ = self._keep_dep()
        return keep & ~self.veto_drop()

    # ---------------------------------------------------------- SLOT (K/T/C 槽位)
    def slot(self, role_leg, znew_fn, a, policy):
        """role_leg in {'K','T','C'}; znew_fn() -> (T,Nc) bad-score (池内 NS pct, 已按方向);
           DEP T 槽位时 znew_fn 必须返回原值 (第二阶段要在 S1 内重中性化), 用 slot_dep_raw。"""
        if float(a) == 0.0:
            return self.B.copy(), dict(note='identity_alpha0_shortcircuit')
        if role_leg not in self.leg_roles:
            raise ValueError('NOT_APPLICABLE: %s 无 %s 槽位' % (self.name, role_leg))
        if self.kind in ('mean', 'single'):
            i = self.leg_roles.index(role_leg)
            legs = list(self.legs)
            legs[i] = _blend(legs[i], znew_fn(), a, policy)
            keep, score = self._keep_mean(legs)
        else:
            if role_leg == 'K':
                Px2 = _blend(self.Px, znew_fn(), a, policy)
                keep, score, _ = self._keep_dep(Px=Px2)
            else:
                raise ValueError('DEP T 槽位请用 slot_dep_T')
        return keep & ~self.veto_drop(), dict(note='slot_%s_a%s' % (policy.lower(), a))

    def slot_dep_T(self, raw_new, direction, a, policy):
        """R1 第二阶段 (T 槽位): 新成员在 S1 内按源口径中性化排名后与 T 分数混合 (plan §5.2 DEP 条)。"""
        if float(a) == 0.0:
            return self.B.copy(), dict(note='identity_alpha0_shortcircuit')
        znew = _ns_pct_within(self.S, raw_new, self.s1, 'hi' if direction == 'high_bad' else 'lo')
        st2 = _blend(self.P.score, znew, a, policy)
        keep, _, _ = self._keep_dep(stage2=st2, s1=self.s1)
        return keep & ~self.veto_drop(), dict(note='slot_depT_%s_a%s' % (policy.lower(), a))

    # ---------------------------------------------------------- ADD_SCORE
    def add_score(self, znew, g):
        """z = (1-γ) z_parent + γ z_new, 保持原预算与否决 (plan §5.2)。DEP: 作用在末级 (S1 内)。"""
        if float(g) == 0.0:
            return self.B.copy(), dict(note='identity_gamma0')
        z = np.where(np.isfinite(znew), (1 - g) * self.score + g * znew, self.score)
        if self.kind in ('mean', 'single'):
            keep = G.keep_SRC(z, self.p0, self.core['s']).astype(bool)
        else:
            keep = G.keep_SRC(z, self.s1, self.core['b']).astype(bool)
        return keep & ~self.veto_drop(), dict(note='add_score_g%s' % g)

    # ---------------------------------------------------------- VETO / SOFT
    def veto_new(self, znew, k):
        """池级毒尾 1/k (与源否决同式) 作用在最终保留集。返回 (B', 当日实删掩码)。"""
        drop = G.drop_SRC(znew, self.p0, k).astype(bool)
        B2 = self.B & ~drop
        return B2, dict(note='veto_k%d' % k, removed=self.B & drop)

    def soft(self, znew, lam, k=10):
        """w' = (1 - λ·1[toxic]) w, 不再分配资本 (plan §5.3)。返回 (B 不变, 乘性权重)。"""
        toxic = G.drop_SRC(znew, self.p0, k).astype(bool) & self.B
        wmul = np.where(toxic, 1.0 - lam, 1.0)
        return self.B.copy(), dict(note='soft_lam%s' % lam, wmul=wmul, toxic=toxic)

    # ---------------------------------------------------------- SWAP / 边缘
    def E_set(self):
        """经济核心拒绝但通过硬约束与保留否决的可用集合 (plan §5.4)。
           均值 / 单核: D (有核分未被核保留) ∩ ¬否决。
           DEP (R1): 两阶段任一阶段被核拒绝的都算经济拒绝 = pool0 ∩ 有第一阶段分 ∩ ¬C ∩ ¬否决
           (E6h 的 P.D 只含第二阶段拒绝; 缺测 / 分箱不足的不纳入)。"""
        if self.kind == 'dep':
            return self.p0 & np.isfinite(self.Px) & ~self.C & ~self.dr
        return self.P.D.astype(bool) & ~self.dr & self.p0

    def swap(self, znew_E, q, out_rule='mother_worst', out_score=None, state=None):
        """m = min(floor(q|B|), |E|, |D_elig|); D = 母体排序最差 m 个最终保留成员 (或 K 路线的最高 K);
           A = E 中按新测量取 m 个 (bad-score 低端); B' = (B \\ D) ∪ A。state: 可选 (T,Nc) bool,
           只在状态为真的 E 中换入 (条件 SWAP)。"""
        if float(q) == 0.0:
            return self.B.copy(), dict(note='identity_q0')
        S = self.S
        E = self.E_set()
        if state is not None:
            E = E & state
        B2 = self.B.copy()
        n_sw = np.zeros(S.T, int)
        osc = self.score if out_score is None else out_score
        for t in range(S.T):
            b = np.where(self.B[t] & np.isfinite(osc[t]))[0]
            e = np.where(E[t] & np.isfinite(znew_E[t]))[0]
            if len(b) == 0 or len(e) == 0:
                continue
            m = min(int(np.floor(q * self.B[t].sum())), len(e), len(b))
            if m <= 0:
                continue
            out = b[np.lexsort((b, -osc[t][b]))[:m]]          # 分高 = 差, 最差 m 个
            inn = e[np.lexsort((e, znew_E[t][e]))[:m]]         # 新测量 bad-score 最低 m 个
            B2[t, out] = False
            B2[t, inn] = True
            n_sw[t] = m
        return B2, dict(note='swap_q%s_%s' % (q, out_rule), n_swapped=n_sw)

    def core_matchN(self, n_target, largest=False):
        """同日同人数核心对照: 按母体冻结 continuation ordering (末级核分 + 列位并列, 与源 keep 同规则)
           在【可用】集合 (非否决; DEP 为 S1 内) 取 n 只。n = |B| 时逐位复现 B (锚)。
           largest=True = 同人数反向 (取最差)。返回 (mask, restricted_flag)。"""
        S = self.S
        avail = (self.p0 if self.kind != 'dep' else self.s1) & ~self.dr & np.isfinite(self.score)
        out = np.zeros_like(self.B)
        restricted = False
        for t in range(S.T):
            v = np.where(avail[t])[0]
            n = int(n_target[t])
            if n <= 0 or len(v) == 0:
                continue
            if n > len(v):
                restricted = True
                n = len(v)
            sc = self.score[t][v]
            order = np.lexsort((v, -sc)) if largest else np.lexsort((v, sc))
            out[t, v[order[:n]]] = True
        return out, restricted

    def edge_replace(self, cost_score, keep_frac=0.8):
        """RL (plan §5.7): 保留母体最好 80%; 合并边缘域 = 原后 20% ∪ continuation ordering 中紧随边界
           的同等名额 (满足原硬约束与否决); 在合并域内按成本测量 (低 = 好) 选与原后 20% 同样多只。"""
        S = self.S
        B2 = np.zeros_like(self.B)
        avail = (self.p0 if self.kind != 'dep' else self.s1) & ~self.dr & np.isfinite(self.score)
        for t in range(S.T):
            b = np.where(self.B[t] & np.isfinite(self.score[t]))[0]
            if len(b) == 0:
                continue
            ob = b[np.lexsort((b, self.score[t][b]))]         # 好 -> 差
            nk = int(np.floor(keep_frac * len(ob)))
            keep, tail = ob[:nk], ob[nk:]
            m = len(tail)
            cand = np.where(avail[t] & ~self.B[t])[0]
            nxt = cand[np.lexsort((cand, self.score[t][cand]))[:m]]
            dom = np.concatenate([tail, nxt])
            cs = cost_score[t][dom]
            ok = np.isfinite(cs)
            dom, cs = dom[ok], cs[ok]
            pick = dom[np.lexsort((dom, cs))[:m]] if len(dom) else dom
            B2[t, keep] = True
            B2[t, pick] = True
        return B2, dict(note='edge_replace_%.1f' % keep_frac)

    # ---------------------------------------------------------- FOCAL
    def focal(self, focal_name, arm, znew=None, k=None, state=None, rng=None):
        """焦点四对照 (plan §5.3): 先关原焦点, 再比较 old / new / both / none;
           状态版: all_on (= old) / all_off (= none) / real_state (焦点只在状态为真的票上执行) /
           random_state (状态在当日池内打乱)。"""
        names = [v['name'] for v in self.veto_legs]
        if focal_name not in names:
            raise ValueError('NOT_APPLICABLE: %s 无焦点 %s' % (self.name, focal_name))
        leg = self.veto_legs[names.index(focal_name)]
        if self.kind in ('mean', 'single'):
            keep, _ = self._keep_mean(self.legs)
        else:
            keep, _, _ = self._keep_dep()
        base = keep & ~self.veto_drop(exclude=(focal_name,))
        if arm in ('old', 'all_on'):
            return base & ~leg['drop'], dict(note='focal_old')
        if arm in ('none', 'all_off'):
            return base, dict(note='focal_off')
        if arm in ('new', 'both'):
            dn = G.drop_SRC(znew, self.p0, k or leg['k']).astype(bool)
            d = dn if arm == 'new' else (dn | leg['drop'])
            return base & ~d, dict(note='focal_%s' % arm)
        if arm == 'real_state':
            return base & ~(leg['drop'] & state), dict(note='focal_state')
        if arm == 'random_state':
            st = state.copy()
            for t in range(self.S.T):
                v = np.where(self.p0[t])[0]
                if len(v) > 1:
                    st[t, v] = st[t, v][rng.permutation(len(v))]
            return base & ~(leg['drop'] & st), dict(note='focal_random_state')
        raise ValueError(arm)


def _short(sp):
    r = sp['role']
    if r == 'C':
        return 'C'
    if r == 'Cf':
        return 'cvr_1d'
    if r == 'B':
        return 'cr%d' % sp['w']
    if r == 'K':
        return 'K'
    if r == 'T':
        return 'T'
    return r


def _raw_c(S, sp):
    raw = G.build_raw_g(S, sp)
    raw = raw.reindex(index=S.pool0.index, columns=S.pool0.columns)
    return raw.values[:, S.ccols].astype(np.float64)
