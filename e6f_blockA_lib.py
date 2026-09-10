#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 块 A 掩码构造的可复用形式 (与 e6f_blockA.py 里的同一套逻辑, 供 C1/B2/自测调用)。
   e6f_blockA.py 在跑, 不动它; 本文件是同一逻辑的库版本, 由自测第 7 组对其逐配置比对。
"""
import sys
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K
import e6f_core as F
import e6f_desc as D

CORE_LRU = 8


class Ctx(object):
    """绑定一个段上下文, 提供 core / veto / full_mask。"""

    def __init__(self, S, lru=CORE_LRU):
        self.S = S
        self.lru = lru
        self._cc = {}

    # ---- 核 ----
    def build_core(self, core, pool_override=None):
        S = self.S
        key = D.core_id(core)
        if pool_override is None and key in self._cc:
            self._cc[key] = self._cc.pop(key)
            return self._cc[key]
        md = core.get('neu', 'NS') or 'NS'
        p0 = S.p0c if pool_override is None else (S.p0c & pool_override)
        if core['kind'] in ('single', 'mean'):
            Ps = [F.get_pct(S, sp, md) for sp in core['comps']]
            ws = core.get('ws')
            if ws is not None:
                wf = [float(x) for x in ws]
                score = F.wcombine_dense(Ps, wf)
                used = [Pi for Pi, w in zip(Ps, wf) if w > 0]
                if core['fam'] == 'KTC_mean' and len(used) > 1:
                    score = np.where(F.common_domain(used), score, np.nan)
            elif len(Ps) == 1:
                score = Ps[0]
            else:
                score = F.combine_dense(Ps, 'mean', complete=(core['fam'] == 'KTC_mean'))
            m = F.keep_mask_dense(score, p0, core['s'])
            out = (m, score, p0)
        else:
            Px = F.get_pct(S, core['x'], md)
            s1 = F.keep_mask_dense(Px, p0, core['a'])
            S1full = np.zeros((S.T, S.Nfull))
            S1full[:, S.ccols] = s1.astype(float)
            S1df = pd.DataFrame(S1full, index=S.pool0.index, columns=S.pool0.columns)
            parts = []
            for y in core['ys']:
                raw = F.build_raw(S.wdata, y)
                if raw.shape != S.pool0.shape or not raw.index.equals(S.pool0.index):
                    raw = raw.reindex(index=S.pool0.index, columns=S.pool0.columns)
                cch, _ = F.neu_cache(raw, S1df, S.log_mcap, S.icodes_neu, md)
                parts.append(F.pct_dense(cch, S.dates, S.ccolpos, S.Nc, None, hb=F.high_bad(y)))
            score = parts[0] if len(parts) == 1 else F.combine_dense(parts, 'mean')
            m = F.keep_mask_dense(score, s1, core['b'])
            out = (m, score, s1)
        if pool_override is None:
            self._cc[key] = out
            while len(self._cc) > self.lru:
                self._cc.pop(next(iter(self._cc)))
        return out

    # ---- 否决 ----
    def build_veto_drop(self, veto, core, pool_override=None):
        S = self.S
        if not veto:
            return None
        md = core.get('neu_veto') or core.get('neu', 'NS') or 'NS'
        p0 = S.p0c if pool_override is None else (S.p0c & pool_override)
        if veto['kind'] == 'composite':
            Ps = [F.get_pct(S, sp, md) for sp, _ in veto['legs']]
            comp = F.combine_dense(Ps, veto['how'], complete=True)
            return F.drop_mask_dense(comp, p0, veto['k'])
        dr = np.zeros_like(p0)
        for sp, k in veto['legs']:
            dr |= F.drop_mask_dense(F.get_pct(S, sp, md), p0, k)
        return dr

    def full_mask(self, cfg, pool_override=None):
        """-> (最终掩码, 末级分, 候选池, 核掩码)"""
        m, sc, cand = self.build_core(cfg['core'], pool_override)
        dr = self.build_veto_drop(cfg['veto'], cfg['core'], pool_override)
        return ((m & ~dr) if dr is not None else m), sc, cand, m

    def weights(self, cfg, pool_override=None):
        mk = self.full_mask(cfg, pool_override)[0]
        return F.dev_from_dense(self.S, mk)
