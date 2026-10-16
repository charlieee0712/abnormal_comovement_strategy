# -*- coding: utf-8 -*-
"""E6m 真实门适配器（plan §4.2；brief §1.3-2）——数据侧实现（只 import 数据侧闭包：e6j_prod / e6j_slot / e6j_features /
comprehensive_factor_diagnosis；不经 e6e_core，brief W15）。阶段 S 再对 e6k_env.Struct.legal() / dom.K[d] 逐日核（A3-1）。
每母体每日返回：E_t（源门的有限评分集合，源 Series 顺序）、original_gate_order（(s0, 源位次) 升序 = rank(method='first')）、
source_U_t = order[:n_t]、n_t = ceil(N/2)（源 qcut 两组的第一组）、s0、k0（源 K 坏度 pct）、kQ、native_s(α)、source_tie_key、
K_loading（Mmean = 1 / 当日可得腿数，K 腿缺失为 0）、downstream_contract。不读任何收益。"""
import math

import numpy as np
import pandas as pd

import e6j_prod as PR
import e6j_slot as SL
import e6j_features as EF
import comprehensive_factor_diagnosis as C

FAMILY = {'A4b': 'A4b', 'A4b_CVRv5': 'A4b', 'M_mean3_v2': 'Mmean', 'M_mean3_v2_CVRv5': 'Mmean', 'M_union3_v2': 'Munion', 'M_union3_v2_CVRv5': 'Munion'}
DOWNSTREAM = {'A4b': 'T_REFIT_IN_NEW_G→SECOND_GATE→(CVR)→DEV', 'Munion': 'AND_T_CR20_KEEP→(CVR)→DEV', 'Mmean': '(CVR)→DEV'}


def q_source(ctx):
    """Q0 源坐标（plan §4.3 / W02）：e6j_features.b1 的 J_B1_qCC（x / d 有效日 = e6i_features.Base :269–306 原式）→ pool0 网格 →
    C.precompute_neutralized_factor → 'lo' 方向秩（e6j_slot.pct_dir）。返回 (raw_df, neu_cache, kq_cache)。"""
    from types import SimpleNamespace
    data = ctx['data']
    close = data['close'].astype(float)
    g = lambda k: data[k].reindex(index=close.index, columns=close.columns).astype(float).to_numpy()
    is_open = (data['is_open'].reindex(index=close.index, columns=close.columns) == 1).to_numpy()
    o, h, l, c, lc = g('open'), g('high'), g('low'), g('close'), g('lclose')
    with np.errstate(all='ignore'):
        valid = is_open & (o > 0) & (h > 0) & (l > 0) & (c > 0) & (lc > 0)
        valid &= (l <= np.minimum(o, c) + 1e-9) & (h >= np.maximum(o, c) - 1e-9)
        r = np.where(valid, np.log(c / lc), np.nan)
    x = g('turnover_rate')
    x = np.where(is_open & np.isfinite(x) & (x >= 0), x, np.nan)
    qcc = EF.b1(SimpleNamespace(x=x, d=np.abs(r)))['J_B1_qCC']
    raw = pd.DataFrame(qcc, index=close.index, columns=close.columns).reindex_like(ctx['pool0'])
    neu = C.precompute_neutralized_factor(raw, ctx['pool0'], ctx['log_mcap'])
    return raw, neu, SL.pct_dir(neu, 'lo'), pd.DataFrame(np.abs(r), index=close.index, columns=close.columns)


def blend(k0, kq, a):
    """FALLBACK 混合（e6j_slot.blend_q 单臂同式）：kQ 缺失处 = k0。"""
    k0 = np.asarray(k0, float)
    kq = np.asarray(kq, float)
    return np.where(np.isfinite(kq), (1 - a) * k0 + a * kq, k0)


class Gate(object):
    """一母体族（A4b / Munion / Mmean）在一段上的源门（数据侧）。"""

    def __init__(self, ctx, family, kq_cache=None):
        self.ctx, self.family = ctx, family
        self.pool0 = ctx['pool0']
        self.dates = list(self.pool0.index)
        self.cols = np.array([str(c) for c in self.pool0.columns])
        self.colpos = {c: i for i, c in enumerate(self.cols)}
        if family in ('A4b', 'Munion'):
            self.src = ctx['neu_cond']
        elif family == 'Mmean':
            self.src = PR.combine([ctx['pcond'], ctx['ptvol'], ctx['pcr20']], 'mean')
        else:
            raise ValueError(family)
        self.kq_cache = kq_cache or {}

    def day(self, t):
        d = self.dates[t]
        s = self.src.get(d)
        if s is None:
            return None
        f = s.dropna()
        if len(f) < 6:                                       # 源 build_factor_strategy_holdings_cached：n_groups·3 = 6
            return None
        ids = np.array([str(x) for x in f.index])
        s0 = f.to_numpy(float)
        tie = np.arange(len(f))
        order = np.lexsort((tie, s0))
        n = int(math.ceil(len(f) / 2.0))
        k0 = self.ctx['pcond'].get(d)
        k0 = k0.reindex(f.index).to_numpy(float) if k0 is not None else np.full(len(f), np.nan)
        kqs = self.kq_cache.get(d)
        kq = kqs.reindex(f.index).to_numpy(float) if kqs is not None else np.full(len(f), np.nan)
        if self.family == 'Mmean':
            legs = [self.ctx[k].get(d) for k in ('pcond', 'ptvol', 'pcr20')]
            L = np.vstack([(lg.reindex(f.index).to_numpy(float) if lg is not None else np.full(len(f), np.nan)) for lg in legs])
            nlegs = np.isfinite(L).sum(0)
            loading = np.where(np.isfinite(L[0]) & (nlegs > 0), 1.0 / np.maximum(nlegs, 1), 0.0)
        else:
            L = None
            loading = np.ones(len(f))
        return dict(date=d, ids=ids, s0=s0, tie=tie, order=order, n=n, k0=k0, kq=kq, legs=L, K_loading=loading,
                    cols=np.array([self.colpos[i] for i in ids]))

    def native_s(self, D, a):
        """native_s(α)：A4b / Munion = K 混合门分；Mmean = 真实三腿综合式（K 腿换混合值，按当日可得腿数平均）。"""
        kb = blend(D['k0'], D['kq'], a)
        if self.family != 'Mmean':
            return kb
        L = D['legs'].copy()
        L[0] = np.where(np.isfinite(D['k0']), kb, np.nan)
        with np.errstate(all='ignore'):
            return np.nanmean(L, axis=0)

    def source_kept(self):
        """源门（逐字源函数）：A4b / Munion = K 第一关 kept；Mmean = 综合门 kept。T×N bool。"""
        return C.build_factor_strategy_holdings_cached(self.src, self.pool0, 2, [2]).to_numpy() == 1


def to_frame(ctx, mask):
    return pd.DataFrame(mask.astype(np.float32), index=ctx['pool0'].index, columns=ctx['pool0'].columns)


class Downstream(object):
    """下游合同（plan §4.2；源函数逐字调用）。gate：T×N bool（新门内成员）→ 六形态最终名单 dict。"""

    def __init__(self, ctx):
        self.ctx = ctx
        self.p0 = ctx['p0']
        self.tox_cvr = PR.drop_mask(ctx['neu_cvr'], ctx['pool0'], 5)
        self.dt = PR.drop_mask(ctx['neu_tvol'], ctx['pool0'])
        self.dr = PR.drop_mask(ctx['neu_cr20'], ctx['pool0'])

    def a4b(self, gate):
        hc = to_frame(self.ctx, gate)
        m = C.build_factor_strategy_holdings_cached(C.precompute_neutralized_factor(self.ctx['fac_tvol'], hc, self.ctx['log_mcap']), hc, 2, [2]).to_numpy() == 1
        return {'A4b': m, 'A4b_CVRv5': m & ~self.tox_cvr}

    def munion(self, gate):
        m = self.p0 & gate & ~self.dt & ~self.dr
        return {'M_union3_v2': m, 'M_union3_v2_CVRv5': m & ~self.tox_cvr}

    def mmean(self, gate):
        m = gate.copy()
        return {'M_mean3_v2': m, 'M_mean3_v2_CVRv5': m & ~self.tox_cvr}

    def forms(self, family, gate):
        return {'A4b': self.a4b, 'Munion': self.munion, 'Mmean': self.mmean}[family](gate)


def scatter(G, T, N, picks):
    """picks：list of (t, cols_array, bool_mask_over_E)。返回 T×N bool。"""
    out = np.zeros((T, N), bool)
    for t, cols, m in picks:
        out[t, cols[m]] = True
    return out
