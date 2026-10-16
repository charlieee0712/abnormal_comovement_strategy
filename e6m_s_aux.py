# -*- coding: utf-8 -*-
"""E6m 阶段 S · 附属名单（registry/auxiliary_manifest_E6m.csv item 5 / 6 与 supplemental_E6m.csv 384；plan §4.3 / §5.3a / §5.5 / §8.3 / §9.1–§9.2 / §10.3）。
不读任何收益。名单层可算的附属对象在这里算；需要权重与账本的（冻结父权重删票、实施链、MATCH_CAP）留给账户阶段，随机（item 2–4）留给随机层。

执行端口径（plan 未写死处；登记在 STAGE_S_IMPL_PLAN §5，交决策端确认）：
- CORE_DEEP_SAME_DELETE_COUNT：删除前的门 = U0（无记忆）或 U_oldlag（RULE_LAG10）。每日删除与真实 HARD 同数，
  从前置门里 owner 有限的成员中按源门分 s0 自深向浅删（平局按 ticker 降序）。
- POST_PARENT_SAME_N：在父最终名单上后置删票，删到与子最终名单同人数。删除顺序：owner 有限者按 kQ 最差在先，平局按 s0 更深、再按 ticker。
  子人数 > 父人数，或有限候选不够的日子 → FINAL_N_MATCH_INFEASIBLE：当日保留父名单并计数。
- SAME_N_CORE_DEEP（V）：每日删与 V 删除同数；从父最终名单中 V 有限的成员里按父门分自深向浅删。
- FROZEN_SOURCE_T_COEFFICIENTS：e6k_ops.stage2_model 转录。fit_cells = 父第一关集合，ev_cells = 新门。
  恒等核验：fit = ev 时 ≡ 源 A4b 下游。
- COPY_OR_SUPPORT_BY_RECIPE（主 72 在 H1/3/10/20）：
  - BAND → COPY_GATE_ORDER；PRIORITY / HARD → COPY_PASS（同记忆）；
  - Q_MAX2 NATIVE / LAG1_10 → TWO_DAY_VALID_SUPPORT_CONTROL（Q0，同 α 与记忆）；
  - Q0 NATIVE → NATIVE_MASKFIX(α)；
  - Q0 HG10 / LAG1_10 → DEFINITION_PENDING（plan 只给无记忆 MASKFIX）。
- TWO_DAY 支持：Q0 / C1 坏度遮罩到"T 与 T−1 的 d 都有效"（两日 raw 有限）的单元，其余回旧 K。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import argparse
import resource

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_s_ops as S
import e6m_s_mock as MK
import e6m_s_real as RL


def parse_desc(did):
    p = did.split('|')
    if len(p) < 9:
        return None
    num = lambda s, pre: float(s[len(pre):]) if s.startswith(pre) else None
    return dict(measurement=p[0], parent=p[1], operator=p[2], param=num(p[3], 'w') if p[3].startswith('w') else (num(p[3], 'c') if p[3].startswith('c') else num(p[3], 'd')),
                alpha=num(p[4], 'a'), memory=p[5], H=int(p[6][1:]), adapter=p[7], condition=p[8])


def cells_of(seg, A):
    return np.asarray(A)[:, seg.ccols][seg.ci.t, seg.ci.c]


class Aux(object):
    def __init__(self, R):
        self.R, self.seg, self.st = R, R.seg, R.st
        seg, st = self.seg, self.st
        self.sc_cells = np.full(seg.n, np.nan)
        self.sc_cells[st.ids] = R.ctx0.sc0
        self.two_valid = np.isfinite(R.me['raw_Q_MAX2'])

    # ------------------------------------------------------------ 几何复制
    def copy_gate_order(self, o):
        c = self.R.ctx(o['measurement'])
        alpha = o['alpha'] if o['operator'] == 'BAND_BLEND' else None
        gn, gm, f = self.R.memo(('copyband', o['measurement'], o['param'], alpha), lambda: S.band_gates(c, o['param'], alpha, 'PROTECTED_LAG10', copy=True))
        return (gn, f['nomem']) if o['memory'] == 'NONE' else (gm, f['mem'])

    def copy_pass(self, o):
        c = self.R.ctx(o['measurement'])
        if o['operator'] == 'PRIORITY_PASS':
            gn, gm, f = self.R.memo(('copyprio', o['measurement'], o['param']), lambda: S.priority_gates(c, o['param'], 'RULE_LAG10', copy=True))
            return (gn, f['nomem']) if o['memory'] == 'NONE' else (gm, f['mem'])
        return self.R.memo(('copyhard', o['measurement'], o['param'], o['memory']), lambda: S.hard_gates(c, o['param'], o['memory'], copy=True))

    # ------------------------------------------------------------ 支持桥
    def native_maskfix(self, meas, a):
        c = self.R.ctx(meas)
        return self.R.memo(('maskfix', meas, a), lambda: S.maskfix_gate(c, a)), {}

    def two_day_support(self, meas, a, mem):
        def f():
            kf = np.where(self.two_valid, self.R.kf[meas], np.nan)
            return S.source_gate(S.Ctx(self.st, kf, mem_gate=self.R.mem_gate), a, mem)
        g, fa = self.R.memo(('twosupp', meas, a, mem), f)
        return g, dict(fa, support_cells_dom=int(self.two_valid[self.st.ids].sum()))

    # ------------------------------------------------------------ HARD 对照
    def _hard(self, o):
        c = self.R.ctx(o['measurement'])
        G, f = self.R.memo(('hard', o['measurement'], o['param'], o['memory']), lambda: S.hard_gates(c, o['param'], o['memory']))
        pre = c.U0 if o['memory'] == 'NONE' else S.source_gate(S._OldCtx(c), 0.0, 'LAG1_10')[0]
        return c, G, pre

    def hard_core_deep(self, o):
        c, G, pre = self._hard(o)
        out = pre.copy()
        short = 0
        for d, a, e, K in c.days:
            nd = int((pre[a:e] & ~G[a:e]).sum())
            if nd == 0:
                continue
            cand = np.flatnonzero(pre[a:e] & np.isfinite(c.kq[a:e]))
            o_ = cand[np.lexsort((-np.arange(len(cand)), -c.sc0[a:e][cand]))]          # s0 自深向浅，平局 ticker 降序
            if len(o_) < nd:
                short += 1
            out[a + o_[:nd]] = False
        return out, dict(days_short_candidates=short, deleted=int((pre & ~out).sum()))

    def post_parent_same_n(self, o):
        c, G, pre = self._hard(o)
        seg = self.seg
        Fc = self.R.down(G)
        F0 = self.R.F0
        kqc = np.full(seg.n, np.nan)
        kqc[self.st.ids] = c.kq
        out = F0.copy()
        infeas = 0
        for d in range(seg.T):
            a, e = int(seg.off[d]), int(seg.off[d + 1])
            npar, nch = int(F0[a:e].sum()), int(Fc[a:e].sum())
            if nch >= npar:
                infeas += int(nch > npar)
                continue
            need = npar - nch
            cand = np.flatnonzero(F0[a:e] & np.isfinite(kqc[a:e]))
            if len(cand) < need:
                infeas += 1
                continue
            o_ = cand[np.lexsort((-np.arange(len(cand)), -self.sc_cells[a:e][cand], -kqc[a:e][cand]))]
            out[a + o_[:need]] = False
        return out, dict(final_n_match_infeasible_days=infeas)

    # ------------------------------------------------------------ T 重估桥（A4b）
    def stage2(self, ev_cells, fit_cells):
        """e6k_ops.stage2_model 转录（g = 1 / 无插值）：fit_cells 上源 neutralize_by_mcap 系数（有效 < 10 → 原值）→ ev_cells 残差 → pct → 前 K。"""
        seg = self.seg
        ctx = seg.ctx
        if not hasattr(self, '_xy'):
            self._xy = (cells_of(seg, ctx['log_mcap'].reindex_like(seg.pool0).to_numpy(float)),
                        cells_of(seg, ctx['fac_tvol'].reindex_like(seg.pool0).to_numpy(float)))
        x, y = self._xy
        out = np.zeros(seg.n, bool)
        for d in range(seg.T):
            a0, a1 = int(seg.off[d]), int(seg.off[d + 1])
            sl = np.arange(a0, a1)
            ev = sl[ev_cells[sl]]
            if len(ev) < 6:
                continue
            fc = sl[fit_cells[sl]]
            fv = fc[np.isfinite(x[fc]) & np.isfinite(y[fc])]
            if len(fv) >= 10:
                xm, ym = x[fv].mean(), y[fv].mean()
                b = np.mean((x[fv] - xm) * (y[fv] - ym)) / np.var(x[fv])
                val = y[ev] - (ym - b * xm + b * x[ev])
            else:
                val = y[ev].copy()
            ok = np.isfinite(val)
            if ok.sum() < 6:
                continue
            evv, vv = ev[ok], val[ok]
            pct = pd.Series(vv).rank(pct=True).to_numpy()
            Kk = MK.k_of(len(evv))
            order = np.lexsort((seg.ci.c[evv], pct))
            out[evv[order[:Kk]]] = True
        return out & ~RL.struct_attr(self.st, 'drop')

    def t_refit_frozen(self, cfg):
        G, f = self.R.gate(cfg)
        g = np.zeros(self.seg.n, bool)
        g[self.st.ids] = G
        p = np.zeros(self.seg.n, bool)
        p[self.st.ids] = self.R.ctx0.U0
        return self.stage2(g, p), dict(f)

    # ------------------------------------------------------------ V 同人数剔深
    def v_same_n_core_deep(self, cfg):
        Fv, f = self.R.v_state(cfg)
        seg = self.seg
        F0 = self.R.F0
        vfin = np.isfinite(self.R.me['vol'])
        out = F0.copy()
        short = 0
        for d in range(seg.T):
            a, e = int(seg.off[d]), int(seg.off[d + 1])
            nd = int((F0[a:e] & ~Fv[a:e]).sum())
            if nd == 0:
                continue
            cand = np.flatnonzero(F0[a:e] & vfin[a:e])
            o_ = cand[np.lexsort((-np.arange(len(cand)), -self.sc_cells[a:e][cand]))]
            if len(o_) < nd:
                short += 1
            out[a + o_[:nd]] = False
        return out, dict(days_short_candidates=short, deleted=int((F0 & ~out).sum()))


def recipe_bridge(A, o):
    op = o['operator']
    if op in ('BAND_Q', 'BAND_BLEND'):
        return 'COPY_GATE_ORDER', A.copy_gate_order(o)
    if op in ('PRIORITY_PASS', 'HARD_CONJ'):
        return 'COPY_PASS', A.copy_pass(o)
    if op == 'LINEAR' and o['measurement'] == 'Q_MAX2':
        return 'TWO_DAY_VALID_SUPPORT_CONTROL', A.two_day_support('Q0', o['alpha'], o['memory'])
    if op == 'LINEAR' and o['measurement'] == 'Q0' and o['memory'] == 'NONE':
        return 'NATIVE_MASKFIX', A.native_maskfix('Q0', o['alpha'])
    return 'DEFINITION_PENDING', None


def main():
    import e6m_s_run_masks as RM
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--form', required=True)
    ap.add_argument('--struct', default='mock', choices=['mock', 'real'])
    a = ap.parse_args()
    t0 = time.time()
    AUXM = M.read_csv_keep(M.P('registry', 'auxiliary_manifest_E6m.csv'), dtype=str)
    SUP = M.read_csv_keep(M.P('registry', 'supplemental_E6m.csv'), dtype=str)
    mine = lambda own: (own.split('|')[1] == a.form) if '|' in own else (                                    # 补丁十九：SUPP: 补充 owner 按 supplemental 的 parent 归形态
        own.startswith('SUPP:') and bool(SUP[SUP.supp_id.str.startswith(own.split('@')[0][5:])].parent.eq(a.form).any()))   # （原写法全漏、SUPP 分支成死代码；只影响以后的重跑，本轮由补充件 S1 补算）
    AX = AUXM[AUXM.item.isin(['5', '6']) & AUXM.owner_id.map(mine)].copy()
    SP = SUP[SUP.parent == a.form].copy()
    if a.form in RL.out_parents(a.struct):
        R = A = None
    else:
        R = RM.Runner(a.seg, a.form, a.struct)
        A = Aux(R)
    rows, ids, finals = [], [], []
    done = {}

    def emit(key, kind, F, f, status='COMPUTED'):
        rows.append(dict(aux_key=key, kind=kind, status=status, final_members=int(F.sum()) if F is not None else '',
                         final_vs_parent=int((F != R.F0).sum()) if F is not None else '', **{('f_' + k): v for k, v in (f or {}).items()}))
        if F is not None:
            ids.append(key)
            finals.append(np.packbits(F))
    for r in AX.itertuples():
        mech = r.mechanism
        own = r.owner_id.split('@')[0]
        o = parse_desc(own)
        key = '%s|%s' % (r.aux_id, mech)
        if A is None:
            emit(key, mech, None, None, 'OUT_OF_SCOPE_MOCK')
            continue
        meas = (o or {}).get('measurement') or own.split('|')[0]
        if meas in RL.wait_meas(a.struct):
            emit(key, mech, None, None, 'SOURCE_WAIT')
            continue
        if mech in ('FROZEN_PARENT_WEIGHT_DELETE',):
            emit(key, mech, None, None, 'ACCOUNT_STAGE')
            continue
        sig = (mech, own.replace('|H%d|' % o['H'], '|H*|') if o else own)
        if sig in done:
            F, f, kind = done[sig]
            emit(key, kind, F, f)
            continue
        if mech == 'COPY_GATE_ORDER':
            G, f = A.copy_gate_order(o)
            F, kind = R.down(G), mech
        elif mech == 'COPY_PASS':
            G, f = A.copy_pass(o)
            F, kind = R.down(G), mech
        elif mech == 'NATIVE_MASKFIX':
            p = own.split('|')
            G, f = A.native_maskfix(p[0], float(p[3][1:]))
            F, kind = R.down(G), mech
        elif mech == 'TWO_DAY_VALID_SUPPORT_CONTROL':
            p = own.split('|')
            G, f = A.two_day_support(p[0], float(p[3][1:]), p[4])
            F, kind = R.down(G), mech
        elif mech == 'COPY_OR_SUPPORT_BY_RECIPE':
            kind, res = recipe_bridge(A, o)
            if res is None:
                emit(key, kind, None, None, 'DEFINITION_PENDING')
                continue
            G, f = res
            F = R.down(G)
        elif mech == 'CORE_DEEP_SAME_DELETE_COUNT':
            G, f = A.hard_core_deep(o)
            F, kind = R.down(G), mech
        elif mech == 'POST_PARENT_SAME_N':
            F, f = A.post_parent_same_n(o)
            kind = mech
        elif mech == 'FROZEN_SOURCE_T_COEFFICIENTS':
            cfg = dict(config_id=own, block=o['operator'] if o['operator'] in ('BAND_Q', 'BAND_BLEND') else 'FILTER', operator=o['operator'],
                       measurement=o['measurement'], memory=o['memory'], param=str(o['param']), alpha=str(o['alpha']) if o['alpha'] is not None else 'NOT_APPLICABLE')
            F, f = A.t_refit_frozen(cfg)
            kind = mech
        elif mech == 'SAME_N_CORE_DEEP':
            if own.startswith('SUPP:'):
                s = SUP[SUP.supp_id.str.startswith(own[5:])].iloc[0]
                cfg = dict(operator=s.operator, param=s.param, condition='ALL_KNOWN')
            else:
                cfg = dict(operator=o['operator'], param=str(o['param']), condition=o['condition'])
            F, f = A.v_same_n_core_deep(cfg)
            kind = mech
        else:
            emit(key, mech, None, None, 'NOT_MASK_LEVEL')
            continue
        done[sig] = (F, f, kind)
        emit(key, kind, F, f)
    for s in SP.itertuples():
        key = 'SUPP|%s|%s' % (s.supp_id[:16], s.diagnostic)
        if A is None:
            emit(key, s.diagnostic, None, None, 'OUT_OF_SCOPE_MOCK')
            continue
        if s.measurement in RL.wait_meas(a.struct):
            emit(key, s.diagnostic, None, None, 'SOURCE_WAIT')
            continue
        sig = (s.diagnostic, s.measurement, s.param, s.alpha, s.condition, s.operator)
        if sig in done:
            F, f, kind = done[sig]
            emit(key, kind, F, f)
            continue
        if s.diagnostic in ('NATIVE_METRIC_LAG', 'COPY_NATIVE_METRIC_LAG'):
            c = R.ctx(s.measurement)
            gn, gm, f = R.memo(('metric', s.measurement, s.param, s.alpha, s.diagnostic),
                               lambda: S.band_gates(c, float(s.param), float(s.alpha), 'PROTECTED_LAG10', copy=s.diagnostic.startswith('COPY'), metric=True))
            F, f = R.down(gm), f['mem']
        elif s.diagnostic == 'V_ALL_KNOWN':
            F, f = R.v_state(dict(operator=s.operator, param=s.param, condition='ALL_KNOWN'))
        else:
            emit(key, s.diagnostic, None, None, 'NOT_MASK_LEVEL')
            continue
        done[sig] = (F, f, s.diagnostic)
        emit(key, s.diagnostic, F, f)
    # 恒等：T 桥 fit = ev ≡ 源 A4b 下游（父门与一个 BAND 门）
    checks = []
    if A is not None and R.st.kind == 'A4b':
        for nm, G in (('U0', R.ctx0.U0), ('BAND_Q_w0.1', S.band_gates(R.ctx0, 0.1)[0])):
            g = np.zeros(R.seg.n, bool)
            g[R.st.ids] = G
            checks.append(dict(check='T_BRIDGE_FIT_EQ_EV_vs_SOURCE_%s' % nm, diff_cells=int((A.stage2(g, g) != R.down(G)).sum())))
    od = RL.root(a.struct, 'masks_aux', a.seg)
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, 'facts_aux_%s.csv' % a.form)
    p2 = os.path.join(od, '%s.npz' % a.form)
    p3 = os.path.join(od, 'checks_aux_%s.csv' % a.form)
    df = pd.DataFrame(rows)
    M.atomic_write_csv(p1, df)
    M.atomic_write_csv(p3, pd.DataFrame(checks if checks else [dict(check='NONE', diff_cells=0)]))
    if ids:
        M.atomic_write_npz(p2, aux_keys=np.array(ids), final_bits=np.array(finals), n_cells=np.array([R.seg.n]), status=np.array(['ANCHOR_PENDING']))
    ok = all(c['diff_cells'] == 0 for c in checks)
    T = dict(rows=len(df), status_counts=df.status.value_counts().to_dict() if len(df) else {}, checks=checks, wall_s=round(time.time() - t0, 1),
             rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    M.write_receipt(os.environ.get('E6M_TASK', ('S_dev_aux_%s_%s' if a.struct == 'mock' else 'S_aux_%s_%s') % (a.seg, a.form)), [p1, p3] + ([p2] if ids else []), status='SUCCEEDED' if ok else 'FAILED',
                    code=[__file__, S.__file__, M.__file__], note='附属名单（不读收益）：%s' % ('B2 开发 mock' if a.struct == 'mock' else '阶段 S 真实结构'), **T)
    print(json.dumps(dict(seg=a.seg, form=a.form, **T), ensure_ascii=False, default=str), flush=True)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
