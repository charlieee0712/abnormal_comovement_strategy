#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 推导段路线实验的运行器 (brief §5, plan §3-§4)。

只跑 checks/derivation_manifest_frozen.json 冻结的描述符; 跑前断言重生成的计数
与冻结表一致 (E6g 的做法)。

按 (段 x 母体) 分片: 母体的 B/C/D/V/score 每片只建一次, pct 帧走 S._g 的 LRU。

对照 (plan §4.4, 每条路径都带):
  原父; 同日同人数的核心放宽 / 剔深; 同日同人数反向; 共同可得域父; 只向下缩的同仓位
随机参照 (U-IID / I-IID / 持续 I-P20, 256 起) 只对每卡的【中心代表】跑, 其余给
三个确定性对照 —— 理由与范围登记进 limit_register (沿 E6g L5 的做法)。

用法: python3 e6h_run_routes.py --segment 2010-2014 --parent A06 [--route ...]
                                [--limit N] [--pilot]
"""
from __future__ import annotations
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_rules as RU
import e6h_expand as EX
import e6g_core as G
import e6g_desc as GD
import e6f_core as F
import e6e_core as K

RES = H.RES


# ---------------------------------------------------------------- 母体上下文
class ParentCtx(object):
    """一个 (段, 母体) 的全部共享物件, 每片建一次。"""

    def __init__(self, S, pname):
        self.S = S
        self.name = pname
        self.ctx = GD.GCtx(S)
        self.cfg = GD.parse_cfg(G.DISPLAY_ID[pname])
        self.B, self.score, self.cand, self.C = self.ctx.full_mask_g(self.cfg)
        dr = self.ctx.build_veto_drop_g(self.cfg.get('veto'), self.cfg['core'], None,
                                        sel='SRC')
        self.dr = np.zeros_like(self.C) if dr is None else dr
        self.V = self.C & self.dr
        self.fin = np.isfinite(self.score)
        self.D = self.cand & self.fin & (~self.C)
        self.legal = S.p0c & (~self.dr)
        self.cols = S.ccolnames
        self.pnl = RU.run_mask(S, self.B)
        self.nb = self.B.sum(axis=1)
        self._raw = {}
        self._pct = {}

    def pct(self, key):
        if key not in self._pct:
            sp = GD.spec_of_key(key) if key in H.U74 else H.specH(key)
            self._pct[key] = H.get_pct_h(self.S, sp, 'NS', 'hi')
        return self._pct[key]

    def raw(self, key):
        """原始值 (二元 / 计数状态要用真实阈值, 不切分位; plan §3.2)。"""
        if key not in self._raw:
            sp = GD.spec_of_key(key) if key in H.U74 else H.specH(key)
            r = H.build_raw_h(self.S, sp)
            r = r.reindex(index=self.S.pool0.index, columns=self.S.pool0.columns)
            self._raw[key] = r.values[:, self.S.ccols]
        return self._raw[key]

    def dir_score(self, key, want_high):
        """方向化分数: 越小 = 越接近想要的那一端。"""
        p = self.pct(key)
        return (1.0 - p) if want_high else p


# ---------------------------------------------------------------- 条件
def price_cond(P, name):
    if name in (None, '-', 'nan'):
        return np.ones_like(P.B)
    if name.startswith('REL_LOW_q'):
        q = float(name.split('q')[1]) / 100.0
        return P.pct('cum_return_20d') <= q
    if name == 'NEAR_ZERO_20d_10pct':
        return np.abs(P.raw('OWN_RET_20')) <= 0.10
    if name == 'NEAR_ZERO_5d_5pct':
        return np.abs(P.raw('OWN_RET_5')) <= 0.05
    raise ValueError(name)


def state_cond(P, key, cmp_, th):
    v = P.raw(key)
    if cmp_ == 'le':
        return np.isfinite(v) & (v <= th)
    if cmp_ == 'ge':
        return np.isfinite(v) & (v >= th)
    if cmp_ == 'eq':
        return np.isfinite(v) & (v == th)
    raise ValueError(cmp_)


def risk_bad(P, key, k, want_high):
    """当日 pool0 内风险最高的 1/k (plan §3.2: 经济原量在当日 pool0 的分位)。"""
    g = P.dir_score(key, want_high)       # 越小 = 风险越高那一端
    return np.isfinite(g) & (g <= 1.0 / float(k))


# ---------------------------------------------------------------- 单描述符
def build_mask(P, r):
    """返回 (mask, wmul, extra) —— extra 记加/减集合等。"""
    op = r['op']
    S = P.S
    ex = {}
    if op == 'slot':
        if r.get('is_identity') or not r.get('new_key') or float(r['alpha']) == 0:
            return P.B.copy(), None, dict(note='identity')
        m, _, _, note = RU.apply_slot(P.ctx, P.cfg, int(r['leg_idx']), r['new_key'],
                                      float(r['alpha']), r['policy'])
        return m, None, dict(note=note)
    if op == 'focal':
        m, note = RU.apply_focal(P.ctx, P.cfg, int(r['focal_idx']), mode=r['mode'])
        return m, None, dict(note=note)
    if op == 'focal_cond':
        st = state_cond(P, r['state_key'], r['state_cmp'], r['state_th'])
        m, note = RU.apply_focal(P.ctx, P.cfg, int(r['focal_idx']), state=st,
                                 mode=r['mode'], k=int(r['k']))
        ex['state_frac'] = float(st[S.p0c].mean())
        return m, None, dict(note=note, **ex)
    if op == 'focal_replace':
        sp = (GD.spec_of_key(r['new_key']) if r['new_key'] in H.U74
              else H.specH(r['new_key']))
        cfg2 = dict(P.cfg)
        v = dict(P.cfg['veto'])
        legs = list(v['legs'])
        if r.get('keep_original'):
            legs = legs + [(sp, int(r['k']))]
        else:
            legs[int(r['focal_idx'])] = (sp, int(r['k']))
        v['legs'] = legs
        cfg2['veto'] = v
        m, _, _, _ = P.ctx.full_mask_g(cfg2)
        return m, None, dict(note='focal_replace')
    if op in ('add', 'swap', 'conj'):
        if r.get('is_identity'):
            return P.B.copy(), None, dict(note='identity')
        if r['route_id'].startswith('E-V'):
            wh = bool(r['want_source_high'])
            g = P.dir_score(r['vol_key'], wh)
            cm = r['cond_mode']
            cond = np.ones_like(P.B)
            if cm in ('price_only', 'joint'):
                cond = cond & price_cond(P, r.get('price_cond'))
            if cm in ('volume_only', 'joint'):
                cond = cond & np.isfinite(g) & (g <= float(r['q']))
        else:                                   # I-P up
            w = int(r['w'])
            ind = P.raw('IND_CUR_%d' % w)
            rel = P.pct('REL_IND_%d' % w)
            g = rel                              # 相对同业越落后 -> pct 越低 -> 越优先
            cond = np.isfinite(ind) & (ind > 0) & np.isfinite(rel) & (rel <= float(r['q']))
        if op == 'add':
            m, A, note = RU.apply_add(P.B, P.D, g, float(r['eta']), P.cols, cond)
            ex['n_added'] = int(A.sum())
        elif op == 'swap':
            m, A, R_, note = RU.apply_swap(P.B, P.D, g, P.score, float(r['eta']),
                                           P.cols, cond)
            ex['n_added'] = int(A.sum())
            ex['n_removed'] = int(R_.sum())
        else:                                    # CONJ: Jbad = 不满足机会条件
            Jbad = ~cond
            m, note = RU.apply_conj(P.C, P.D, Jbad, P.V)
            ex['n_added'] = int((m & ~P.B).sum())
        ex['cond_frac_in_D'] = float(cond[P.D].mean()) if P.D.any() else np.nan
        return m, None, dict(note=note, **ex)
    if op in ('soft', 'veto_in_b'):
        if r.get('is_identity'):
            return P.B.copy(), None, dict(note='identity')
        bad = risk_bad(P, r['risk_key'], int(r['k']), bool(r['want_source_high']))
        ex['bad_frac_in_B'] = float(bad[P.B].mean()) if P.B.any() else np.nan
        if op == 'veto_in_b':
            return (P.B & ~bad), None, dict(note='veto_in_b', **ex)
        m, wm, note = RU.apply_soft(P.B, bad, float(r['lam']))
        return m, wm, dict(note=note, **ex)
    if op == 'ip_down_veto':
        w, k = int(r['w']), int(r['k'])
        ind = P.raw('IND_CUR_%d' % w)
        indp = P.pct('IND_CUR_%d' % w)
        bad = np.isfinite(ind) & (ind < 0) & np.isfinite(indp) & (indp <= 1.0 / k)
        ex['bad_frac_in_B'] = float(bad[P.B].mean()) if P.B.any() else np.nan
        return (P.B & ~bad), None, dict(note='ip_down_veto', **ex)
    if op == 'margin':
        if r.get('is_identity'):
            return P.B.copy(), None, dict(note='identity')
        liq = P.dir_score(r['liq_key'], want_high=False)   # amihud 高 = 成本高 = 差
        m, note = RU.apply_margin(P.B, P.score, liq, float(r['e']), P.cols,
                                  P.legal, r['order'])
        ex['n_changed'] = int((m != P.B).sum())
        return m, None, dict(note=note, **ex)
    raise ValueError('未知 op %r' % op)


def controls(P, mask):
    """plan §4.4 的确定性对照。返回 dict(名 -> pnl)。"""
    S, out = P.S, {}
    n_new = mask.sum(axis=1)
    tb = RU.ticker_order(P.cols)
    # 同日同人数的核心放宽 / 剔深: 按父的核分数取同样多只
    ctl = RU.topk_by(P.score, P.legal, n_new, tb, largest=False)
    out['ctl_core_matchN'] = RU.run_mask(S, ctl)
    # 同日同人数反向: 按父的核分数取【最差】的同样多只
    rev = RU.topk_by(P.score, P.legal, n_new, tb, largest=True)
    out['ctl_reverse_matchN'] = RU.run_mask(S, rev)
    # 共同可得域父: 父 ∩ 子的共同有效日
    ok = (mask.sum(axis=1) > 0) & (P.B.sum(axis=1) > 0)
    out['ctl_parent_common'] = RU.run_mask(S, P.B & ok[:, None])
    return out


def summarize(P, r, mask, wmul, extra, pnl, ctl):
    g0, p0_, t0_, n0 = P.pnl
    g1, p1, t1, n1 = pnl
    both = np.isfinite(g0) & np.isfinite(g1)
    d = dict(r)
    for kk in ('_core', '_veto'):
        d.pop(kk, None)
    d.update(segment=P.S.name,
             gross_ann=H.ann(g1), net8_ann=H.ann(n1),
             net12_ann=H.ann(g1 - t1 * 12.0 / 1e4),
             turn_mean=float(np.nanmean(t1)), pos_mean=float(np.nanmean(p1)),
             target_n_mean=float(mask.sum(axis=1).mean()),
             parent_gross_ann=H.ann(g0), parent_net8_ann=H.ann(n0),
             d_gross_ann=H.ann(np.where(both, g1 - g0, np.nan)),
             d_net8_ann=H.ann(np.where(both, n1 - n0, np.nan)),
             d_turn=float(np.nanmean(t1) - np.nanmean(t0_)),
             d_pos=float(np.nanmean(p1) - np.nanmean(p0_)),
             n_common_days=int(both.sum()),
             n_mask_diff=int((mask != P.B).sum()))
    for cn, cp in ctl.items():
        d['%s_net8_ann' % cn] = H.ann(cp[3])
        d['d_vs_%s' % cn] = H.ann(np.where(both & np.isfinite(cp[0]),
                                           n1 - cp[3], np.nan))
    d.update({k: v for k, v in extra.items()})
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--parent', required=True)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--pilot', action='store_true')
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshard', type=int, default=1)
    a = ap.parse_args()
    assert a.segment in H.DERIV_SEGS, '推导段实验只在 2010-2014 / 2015-2018'
    t0 = time.time()

    man = json.load(open(os.path.join(RES, 'checks',
                                      'derivation_manifest_frozen.json')))
    rows = EX.all_descriptors()
    assert len(rows) == man['total'], \
        '重生成 %d 个描述符, 冻结表记 %d 个' % (len(rows), man['total'])
    rows = [r for r in rows if r['parent'] == a.parent]
    rows = [r for i, r in enumerate(rows) if i % a.nshard == a.shard]
    if a.limit:
        rows = rows[:a.limit]
    if not rows:
        print('本片无描述符'); return

    S = H.seg(a.segment, verbose=False)
    tb = time.time() - t0
    P = ParentCtx(S, a.parent)
    tp = time.time() - t0
    print('  建段 %.0fs, 建母体 %.0fs, 本片 %d 个描述符' % (tb, tp - tb, len(rows)),
          flush=True)

    out, daily, fails = [], {}, []
    tick = time.time()
    for i, r in enumerate(rows):
        try:
            H.guard_h([k for k in (r.get('new_key'), r.get('vol_key'), r.get('risk_key'),
                                   r.get('liq_key'), r.get('state_key')) if k],
                      'trade', segment=a.segment, label_end=H.PROTECTED_LABEL_END,
                      where=r['descriptor_id'], route_id=r['route_id'],
                      rule_objects=[r['role']])
            mask, wmul, ex = build_mask(P, r)
            pnl = RU.run_mask(S, mask, wmul)
            ctl = controls(P, mask)
            out.append(summarize(P, r, mask, wmul, ex, pnl, ctl))
            daily[r['descriptor_id']] = (np.asarray(pnl[3], np.float32)
                                         - np.asarray(P.pnl[3], np.float32))
        except Exception as e:
            fails.append(dict(descriptor_id=r['descriptor_id'],
                              err='%s: %s' % (type(e).__name__, str(e)[:200])))
        if a.pilot and (i + 1) % 5 == 0:
            el = time.time() - tick
            print('    %d/%d  %.2f s/描述符' % (i + 1, len(rows), el / (i + 1)),
                  flush=True)

    od = os.path.join(RES, 'route_results')
    os.makedirs(od, exist_ok=True)
    tag = '%s_%s%s' % (a.segment, a.parent, '' if a.nshard == 1 else '_s%d' % a.shard)
    if a.pilot:
        tag = 'PILOT_' + tag
    pd.DataFrame(out).to_csv(os.path.join(od, 'summary_%s.csv' % tag), index=False)
    if daily:
        pd.DataFrame(daily, index=[str(x)[:10] for x in S.dates]).astype(
            np.float32).to_parquet(os.path.join(od, 'dnet8_%s.parquet' % tag))
    if fails:
        with open(os.path.join(od, 'FAILED_%s.json' % tag), 'w') as fh:
            json.dump(fails, fh, indent=1, ensure_ascii=False)
    el = time.time() - t0
    print('  [%s] %d 成功 / %d 失败, 总 %.0fs, %.2f s/描述符'
          % (tag, len(out), len(fails), el, (el - tp) / max(1, len(rows))))
    if fails:
        print('  失败样例: %s' % fails[0]['err'])


if __name__ == '__main__':
    main()
