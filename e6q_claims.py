# -*- coding: utf-8 -*-
"""E6q claims（附录 B.20；plan §12–§13.1）：每个数字落到交付表实际一行（query_id → reports/query_registry_E6q.csv）。
- Q01…Q18：QUESTION，开放、不评分（只给答题用的关键读数与出处）。
- E01…E07：PREDICTION；对象 / 对照 / A_eval / κ / δ 取 ledger_E；点估与区间同一估计量（日差 x = Δne − κA^δ·ΔS_δ，FULL = Σn·v / Σn，
  段内 stationary bootstrap 2,000 次、块长 max(20, 2H)、按段 n 合并）；带内 = 支持、带外 = 不支持（端点不交换）；区间另列不决定 HIT。
- G-P-01…12：G_CHAIN；状态取 ledger_G（第一道标签，推导段），读数指向 G1_E6q.csv。
- CC-E6q-01…11：CC_CARRIED；句级行 + 子条款行（CC-E6q-01a…）；带内 = 支持、带外 = 不支持，note 写可证伪门是否触发；句级 = 子条款全支持 → 支持、全不支持 → 不支持、
  其余 mixed；plan §12.3 指定的原句对象不一致 → 句级 NOT_TESTED_AS_WRITTEN、子条款照评。
- ENG：工程恒等（技术PASS / 技术FAIL）。
同时回填 cc_statement_carry 的 estimand_note / comparable / claim_status 与 ledger E / Q 的结果栏。
  python3 e6q_claims.py --phase B        （--phase A2 --root tmp/a2stats：空跑）"""
import os
import sys
import json
import math
import time
import argparse

import numpy as np
import pandas as pd

import e6q_core as O
import e6q_stats as ST

CCOLS = ['claim_id', 'kind', 'author', 'statement', 'query_id', 'table', 'exec_ids', 'result_value', 'result_sign', 'ci_lo', 'ci_hi', 'claim_status', 'note']
NANW = __import__('re').compile(r'(?<![A-Za-z_])(nan|None|NaN|inf)(?![A-Za-z_])')
QCOLS = ['query_id', 'table', 'filter', 'n_rows', 'generator']
OWN = ('registration/', 'verify/impact_reconciliation', 'diagnostics/G1_E6q.csv', 'diagnostics/stage0')


class Q(object):
    """查询登记：table 相对路径 + 等值过滤；n_rows = 实际命中行数。"""

    def __init__(self, ctx):
        self.ctx = ctx
        self.reg = {}
        self.tabs = {}

    def path(self, rel):
        base = O.work() if rel.startswith(OWN) else self.ctx.root
        return os.path.join(base, *rel.split('/'))

    def tab(self, rel):
        if rel not in self.tabs:
            p = self.path(rel)
            self.tabs[rel] = pd.read_csv(p, dtype=str, keep_default_na=False) if os.path.exists(p) else None
        return self.tabs[rel]

    def q(self, qid, rel, filt=None, note=''):
        df = self.tab(rel)
        filt = filt or {}
        if df is None:
            sub = pd.DataFrame()
        else:
            m = np.ones(len(df), bool)
            for k, v in filt.items():
                m &= df[k].astype(str).to_numpy() == str(v)
            sub = df[m]
        ftxt = ' & '.join('%s=%s' % (k, v) for k, v in filt.items()) or 'ALL'
        if note:
            ftxt += ' ; ' + note
        self.reg[qid] = dict(query_id=qid, table=rel, filter=ftxt, n_rows=int(len(sub)), generator='e6q_claims.py')
        return sub


def f(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else np.nan
    except (TypeError, ValueError):
        return np.nan


def sgn(v):
    if not np.isfinite(v):
        return ''
    return '+' if v > 0 else ('-' if v < 0 else '0')


def band(v, lo=None, hi=None, lo_open=False, hi_open=False):
    if not np.isfinite(v):
        return 'NOT_EVALUABLE'
    ok = True
    if lo is not None:
        ok &= (v > lo) if lo_open else (v >= lo)
    if hi is not None:
        ok &= (v < hi) if hi_open else (v <= hi)
    return '支持' if ok else '不支持'


def agg(stats):
    s = [x for x in stats if x in ('支持', '不支持', 'mixed')]
    if not s:
        return 'NOT_EVALUABLE'
    if all(x == '支持' for x in s):
        return '支持'
    if all(x == '不支持' for x in s):
        return '不支持'
    return 'mixed'


def fmt(v):
    return '' if (v is None or (isinstance(v, float) and not np.isfinite(v))) else v


class Claims(object):
    def __init__(self, ctx, q):
        self.ctx = ctx
        self.Q = q
        self.rows = []
        R = ctx.R
        self.R = R
        self.main = R[(R.form == O.MAIN_FORM) & (R.memory == 'HG10') & (R.scenario == 'FEASIBLE_DAILY')]

    def pick(self, arm, trig, H='20'):
        x = self.main[(self.main.arm == arm) & (self.main.trigger == trig) & (self.main.H == H)]
        return x.exec_id.iloc[0] if len(x) else ''

    def add(self, cid, kind, author, statement, qid, table, exec_ids, value, status, ci=(np.nan, np.nan), note=''):
        v = f(value)
        clean = lambda s: NANW.sub('—', str(s)).replace('\n', ' ')
        self.rows.append(dict(claim_id=cid, kind=kind, author=author, statement=clean(statement), query_id=qid, table=table, exec_ids=';'.join(x for x in exec_ids if x),
                              result_value=fmt(v), result_sign=sgn(v), ci_lo=fmt(f(ci[0])), ci_hi=fmt(f(ci[1])), claim_status=status, note=clean(note)))

    # ---- 取值助手
    def cc(self, qid, e, ck, A, col, kappa='0.5', exponent='0.5', seg='FULL'):
        sub = self.Q.q(qid, 'statistics/cost_curve_E6q.csv', dict(exec_id=e, comparator_kind=ck, A_cny=int(A), kappa=kappa, exponent=exponent, segment=seg))
        return f(sub[col].iloc[0]) if len(sub) else np.nan

    def asum(self, qid, e, col, seg='FULL'):
        sub = self.Q.q(qid, 'statistics/account_summary_E6q.csv', dict(exec_id=e, segment=seg))
        return f(sub[col].iloc[0]) if len(sub) else np.nan

    def diag(self, qid, blk, nm, filt):
        sub = self.Q.q(qid, 'diagnostics/%s_%s_E6q.csv' % (blk, nm), filt)
        return f(sub['value'].iloc[0]) if len(sub) else np.nan


# ------------------------------------------------------------------ E
def e_claims(C, S, boot):
    ctx = C.ctx
    LE = O.read_csv(O.P('registration', 'ledger_E_E6q.csv'), dtype=str).fillna('')
    upd = []
    for r in LE.itertuples(index=False):
        o, c = r.object_exec_id, r.comparator_exec_id
        j, k = ctx.col[o], ctx.col[c]
        A = f(r.A_eval_cny)
        kp, x = f(r.kappa), f(r.exponent)
        ne = S['ne']
        d = ne[:, j] - ne[:, k]
        if np.isfinite(A):
            s = np.nan_to_num(S[ST.SCOL[x]])
            d = d - kp * (A ** x) * (s[:, j] - s[:, k])
        D = d[:, None]
        v = float(ST.ann_seg(D, ctx)['FULL'][0])
        H = int(ctx.reg.loc[o].H)
        ci = boot.ci(D, max(20, 2 * H))['FULL']
        lo, hi = f(r.band_lo_canonical), f(r.band_hi_canonical)
        qid = r.result_query or 'QRY-E-%s' % r.e_id
        if np.isfinite(A):
            rel = 'statistics/cost_curve_E6q.csv'
            sub = C.Q.q(qid, rel, dict(exec_id=o, comparator_exec_id=c, A_cny=int(A), kappa=r.kappa, exponent=r.exponent, segment='FULL'))
            col = 'net_after_impact_diff_ann_pp'
        else:
            rel = 'statistics/comparison_results_E6q.csv'
            sub = C.Q.q(qid, rel, dict(left_exec_id=o, right_exec_id=c, segment='FULL'))
            col = 'D_ann_pp'
            if not len(sub) and c == ctx.reg.loc[o].parent_same_arm_exec_id:
                rel = 'statistics/account_summary_E6q.csv'
                sub = C.Q.q(qid, rel, dict(exec_id=o, segment='FULL'))
                col = 'D_same_arm_ann_pp'
        tv = f(sub[col].iloc[0]) if len(sub) else np.nan
        if lo > hi:
            st, extra = '不支持', '；改正仪器后下端 > 上端：参照顺序假设不支持（端点不交换）'
        else:
            st, extra = band(v, lo, hi), ''
        chk = ('表行 %s = %.6f（与本估计量差 %.2e）' % (col, tv, abs(tv - v))) if np.isfinite(tv) else '表行未命中（%s）' % rel
        note = '带 [%.4f, %.4f]（canonical；显示 [%s, %s]）；%s；区间 = 段内 stationary bootstrap 2000 次、块长 %d，FULL 按段 n 合并；区间另列不决定 HIT%s' % (
            lo, hi, r.band_lo_display, r.band_hi_display, chk, max(20, 2 * H), extra)
        C.add(r.e_id, 'PREDICTION', 'plan v1.1 §12.2', r.statement_verbatim, qid, rel, [o, c], v, st, ci, note)
        upd.append((r.e_id, st, '%s %s' % (rel, C.Q.reg[qid]['filter'])))
    for eid, st, rr in upd:
        i = LE.index[LE.e_id == eid][0]
        LE.loc[i, 'state'] = st
        LE.loc[i, 'result_row'] = rr
    return LE


# ------------------------------------------------------------------ CC
def cc_claims(C, carry):
    pk = C.pick
    out = {}

    def sub(cid, txt, qid, table, ids, v, st, note, ci=(np.nan, np.nan)):
        C.add(cid, 'CC_CARRIED', 'proposal v1.3 §5.2（逐字见 cc_statement_carry）', txt, qid, table, ids, v, st, ci, note)
        return st

    vb = dict(zip(carry.id, carry.verbatim))
    # ---- 01：M1 REINVEST_NEW LEVEL H20
    m1, nat = pk('REINVEST_NEW', 'T1b_LEVEL'), pk('NATIVE', 'T1b_LEVEL')
    a = C.cc('QRY-CC01a', m1, 'SAME_TRIGGER_NATIVE', 5e8, 'impact_diff_ann_pp')
    b = C.cc('QRY-CC01b', m1, 'SAME_ARM_PARENT', 1e8, 'gross_diff_ann_pp')
    c = C.cc('QRY-CC01c', m1, 'SAME_ARM_PARENT', 5e8, 'net_after_impact_diff_ann_pp')
    d1 = C.cc('QRY-CC01d', m1, 'SAME_ARM_PARENT', 1e8, 'net_after_impact_diff_ann_pp')
    d0 = C.cc('QRY-CC01d_nat', nat, 'SAME_ARM_PARENT', 1e8, 'net_after_impact_diff_ann_pp')
    ex = C.asum('QRY-CC01_comp', m1, 'exposure_diff_vs_parent')
    dsc = f(C.Q.tab('statistics/account_summary_E6q.csv').set_index(['exec_id', 'segment']).loc[(m1, 'FULL'), 'D_sc_ann_pp']) if m1 else np.nan
    s = [sub('CC-E6q-01a', '对同触发 NATIVE 的 5 亿 κ.5 δ.5 增量冲击 ≤ 9.0', 'QRY-CC01a', 'statistics/cost_curve_E6q.csv', [m1, nat], a, band(a, hi=9.0),
             '可证伪门 > 10.5：%s' % ('触发' if a > 10.5 else '未触发')),
         sub('CC-E6q-01b', 'gross D 对同 H 父 ∈ [6.4, 8.4]', 'QRY-CC01b', 'statistics/cost_curve_E6q.csv', [m1], b, band(b, 6.4, 8.4),
             '可证伪门 gross D < 6.0：%s' % ('触发' if b < 6.0 else '未触发')),
         sub('CC-E6q-01c', '净差（5 亿）对同 H 父 > −2.0', 'QRY-CC01c', 'statistics/cost_curve_E6q.csv', [m1], c, band(c, lo=-2.0, lo_open=True), ''),
         sub('CC-E6q-01d', '补集：1 亿净差与 NATIVE 之差 ∈ [−.5, +.5]', 'QRY-CC01d', 'statistics/cost_curve_E6q.csv', [m1, nat], d1 - d0, band(d1 - d0, -0.5, 0.5),
             'M1 1 亿净差 %.4f − NATIVE 1 亿净差 %.4f（QRY-CC01d_nat）' % (d1, d0))]
    sub('CC-E6q-01', vb.get('CC-E6q-01', ''), 'QRY-CC01a', 'statistics/cost_curve_E6q.csv', [m1, nat], a, 'NOT_TESTED_AS_WRITTEN',
        'plan §12.3：原句"对同触发 NATIVE"的冲击与 11.19（对子同 H 父）不是同一个差 → 句级 NOT_TESTED_AS_WRITTEN；子条款 a–d 分别评（%s）；竞争解释：敞口差 %.4f、D_sc %.4f' % (
            '/'.join(s), ex, dsc))
    out['CC-E6q-01'] = ('NOT_TESTED_AS_WRITTEN', 'partial')
    # ---- 02：M2
    m25, m21, cash = pk('REINVEST_LIQ_5E8', 'T1b_LEVEL'), pk('REINVEST_LIQ_1E8', 'T1b_LEVEL'), pk('CASH_REMAIN', 'T1b_LEVEL')
    a = C.cc('QRY-CC02a', m25, 'SAME_ARM_PARENT', 5e8, 'net_after_impact_diff_ann_pp')
    an = C.cc('QRY-CC02a_nat', nat, 'SAME_ARM_PARENT', 5e8, 'net_after_impact_diff_ann_pp')
    ac = C.cc('QRY-CC02a_cash', cash, 'SAME_ARM_PARENT', 5e8, 'net_after_impact_diff_ann_pp')
    g = C.cc('QRY-CC02b', m25, 'SAME_ARM_PARENT', 1e8, 'gross_diff_ann_pp')
    gn = C.cc('QRY-CC02b_nat', nat, 'SAME_ARM_PARENT', 1e8, 'gross_diff_ann_pp')
    gc = C.cc('QRY-CC02b_cash', cash, 'SAME_ARM_PARENT', 1e8, 'gross_diff_ann_pp')
    nn = C.asum('QRY-CC02b_net', m25, 'D_same_arm_ann_pp')
    nnat = C.asum('QRY-CC02b_net_nat', nat, 'D_same_arm_ann_pp')
    c1 = C.cc('QRY-CC02c', m21, 'SAME_ARM_PARENT', 1e8, 'net_after_impact_diff_ann_pp')
    lo_g, hi_g = min(gc, gn), max(gc, gn)
    s = [sub('CC-E6q-02a', 'M2(5 亿) 5 亿净差（曲线）> max(NATIVE −3.33, CASH −.46) + .3 = −.16', 'QRY-CC02a', 'statistics/cost_curve_E6q.csv', [m25], a,
             band(a, lo=-0.16, lo_open=True), '原句数字为 E6p 读数；本轮同口径 NATIVE %.4f、CASH %.4f（QRY-CC02a_nat / _cash），max + .3 = %.4f 仅作读法' % (an, ac, max(an, ac) + 0.3)),
         sub('CC-E6q-02b', 'gross D ∈ [CASH, NATIVE]（本轮 gross）', 'QRY-CC02b', 'statistics/cost_curve_E6q.csv', [m25, cash, nat], g, band(g, lo_g, hi_g),
             'CASH gross %.4f、NATIVE gross %.4f（plan §12.3：CASH .19 是 net，不自动成为 gross 下界）' % (gc, gn)),
         sub('CC-E6q-02bN', 'net D ∈ [CASH .19（E6p net）, NATIVE（本轮 net）]', 'QRY-CC02b_net', 'statistics/account_summary_E6q.csv', [m25, nat], nn, band(nn, 0.19, nnat),
             'gross 与 net 并报；NATIVE 本轮 net D %.4f' % nnat),
         sub('CC-E6q-02c', 'M2(1 亿) 1 亿净差与 NATIVE 之差 ∈ [−.3, +.8]', 'QRY-CC02c', 'statistics/cost_curve_E6q.csv', [m21, nat], c1 - d0, band(c1 - d0, -0.3, 0.8),
             'M2_1E8 1 亿净差 %.4f − NATIVE %.4f' % (c1, d0))]
    st = agg(s)
    sub('CC-E6q-02', vb.get('CC-E6q-02', ''), 'QRY-CC02a', 'statistics/cost_curve_E6q.csv', [m25, m21], a, st, '子条款 %s；可证伪门 5 亿净差 ≤ −.16：%s' % (
        '/'.join(s), '触发' if a <= -0.16 else '未触发'))
    out['CC-E6q-02'] = (st, 'yes')
    # ---- 03：M3
    m3, m3t = pk('EXIT_GATE_LIQ_5E8', 'T1b_LEVEL'), pk('EXIT_GATE_LIQ_5E8', 'T1a')
    tg3 = 'EXIT_GATE_LIQ_5E8|T1b_LEVEL|H20|main|HG10'
    si = C.diag('QRY-CC03a', 'D1', 'cost_source', dict(item='impact_by_side', key1='SELL', key2=tg3, stat='A5e+08|arm_minus_parent'))
    sin = C.diag('QRY-CC03a_nat', 'D1', 'cost_source', dict(item='impact_by_side', key1='SELL', key2='NATIVE|T1b_LEVEL|H20|main|HG10', stat='A5e+08|arm_minus_parent'))
    g3 = C.cc('QRY-CC03b', m3, 'SAME_ARM_PARENT', 1e8, 'gross_diff_ann_pp')
    n3 = C.cc('QRY-CC03c', m3, 'SAME_ARM_PARENT', 5e8, 'net_after_impact_diff_ann_pp')
    g3t = C.cc('QRY-CC03d', m3t, 'SAME_ARM_PARENT', 1e8, 'gross_diff_ann_pp')
    s = [sub('CC-E6q-03a', '增量卖出冲击 ≤ 4.4（= 7.38 × .6）', 'QRY-CC03a', 'diagnostics/D1_cost_source_E6q.csv', [m3], si, band(si, hi=4.4),
             'D1 curve κ.5 δ.5 5 亿，卖方净单冲击（臂 − 同臂父）；本轮同仪器 NATIVE LEVEL H20 卖方增量 %.4f（QRY-CC03a_nat；原句 7.38 来自 E6p 读数）' % sin),
         sub('CC-E6q-03b', 'gross D ≥ 5.9（= 7.86 × .75）', 'QRY-CC03b', 'statistics/cost_curve_E6q.csv', [m3], g3, band(g3, lo=5.9),
             'plan §12.3：7.86 / 3.24 是 net，原 gross 下界照原句评；可证伪门 LEVEL gross D < 5.0：%s' % ('触发' if g3 < 5.0 else '未触发')),
         sub('CC-E6q-03c', '5 亿净差对同 H 父 > −3.33', 'QRY-CC03c', 'statistics/cost_curve_E6q.csv', [m3], n3, band(n3, lo=-3.33, lo_open=True), ''),
         sub('CC-E6q-03d', 'T1a 基座 |gross D − 3.24| ≤ .3', 'QRY-CC03d', 'statistics/cost_curve_E6q.csv', [m3t], g3t - 3.24, band(abs(g3t - 3.24), hi=0.3),
             'T1a gross D %.4f' % g3t)]
    st = agg(s)
    sub('CC-E6q-03', vb.get('CC-E6q-03', ''), 'QRY-CC03b', 'statistics/cost_curve_E6q.csv', [m3, m3t], g3, st, '子条款 %s' % '/'.join(s))
    out['CC-E6q-03'] = (st, 'yes')
    # ---- 04：M4 EXIT_HALF（主 M4 = 余半到期；REARM 另列不入评）
    hL, hT, natT = pk('EXIT_HALF', 'T1b_LEVEL'), pk('EXIT_HALF', 'T1a'), pk('NATIVE', 'T1a')
    gL = C.cc('QRY-CC04a', hL, 'SAME_ARM_PARENT', 1e8, 'gross_diff_ann_pp')
    gT = C.cc('QRY-CC04b', hT, 'SAME_ARM_PARENT', 1e8, 'gross_diff_ann_pp')
    iL = C.cc('QRY-CC04c', hL, 'SAME_ARM_PARENT', 5e8, 'impact_diff_ann_pp')
    iN = C.cc('QRY-CC04c_nat', nat, 'SAME_ARM_PARENT', 5e8, 'impact_diff_ann_pp')
    iT = C.cc('QRY-CC04cT', hT, 'SAME_ARM_PARENT', 5e8, 'impact_diff_ann_pp')
    iNT = C.cc('QRY-CC04cT_nat', natT, 'SAME_ARM_PARENT', 5e8, 'impact_diff_ann_pp')
    h5 = C.cc('QRY-CC04d', hL, 'SAME_TRIGGER_NATIVE', 5e8, 'net_after_impact_diff_ann_pp')
    h1 = C.cc('QRY-CC04e', hL, 'SAME_TRIGGER_NATIVE', 1e8, 'net_after_impact_diff_ann_pp')
    rL = iL / iN if (np.isfinite(iN) and iN != 0) else np.nan
    rT = iT / iNT if (np.isfinite(iNT) and iNT != 0) else np.nan
    s = [sub('CC-E6q-04a', 'LEVEL H20 gross D ∈ [3.5, 5.5]', 'QRY-CC04a', 'statistics/cost_curve_E6q.csv', [hL], gL, band(gL, 3.5, 5.5), ''),
         sub('CC-E6q-04b', 'T1a H20 gross D ∈ [1.5, 2.3]', 'QRY-CC04b', 'statistics/cost_curve_E6q.csv', [hT], gT, band(gT, 1.5, 2.3), ''),
         sub('CC-E6q-04c', 'LEVEL：增量冲击 ≤ 50% 全量', 'QRY-CC04c', 'statistics/cost_curve_E6q.csv', [hL, nat], rL, band(rL, hi=0.5),
             '半 %.4f / 全 %.4f（δ = .5 时比值与 A 无关）' % (iL, iN)),
         sub('CC-E6q-04cT', 'T1a：增量冲击 ≤ 50% 全量', 'QRY-CC04cT', 'statistics/cost_curve_E6q.csv', [hT, natT], rT, band(rT, hi=0.5), '半 %.4f / 全 %.4f' % (iT, iNT)),
         sub('CC-E6q-04d', '5 亿 LEVEL 半 > 全（净差）', 'QRY-CC04d', 'statistics/cost_curve_E6q.csv', [hL, nat], h5, band(h5, lo=0.0, lo_open=True), ''),
         sub('CC-E6q-04e', '1 亿 全 > 半', 'QRY-CC04e', 'statistics/cost_curve_E6q.csv', [hL, nat], h1, band(h1, hi=0.0, hi_open=True), '值 = 半 − 全；< 0 即全 > 半')]
    st = agg(s)
    sub('CC-E6q-04', vb.get('CC-E6q-04', ''), 'QRY-CC04a', 'statistics/cost_curve_E6q.csv', [hL, hT], gL, st, '子条款 %s；两锚分别评、不以平均通过；可证伪门两锚同向：%s' % (
        '/'.join(s), '触发' if (np.isfinite(h5) and np.isfinite(h1) and np.sign(h5) == np.sign(h1)) else '未触发'))
    out['CC-E6q-04'] = (st, 'yes')
    # ---- 05：T1a ∨ T8 H20 NATIVE
    un = pk('NATIVE', 'UNION_T1a_T8')
    gU = C.cc('QRY-CC05a', un, 'SAME_ARM_PARENT', 1e8, 'gross_diff_ann_pp')
    nU = C.asum('QRY-CC05aN', un, 'D_same_arm_ann_pp')
    tU = C.asum('QRY-CC05b', un, 'turnover_ann')
    cU = C.cc('QRY-CC05c', un, 'SAME_ARM_PARENT', 5e8, 'net_after_impact_diff_ann_pp')
    s = [sub('CC-E6q-05a', 'gross D ∈ [3.54, 5.96]（原作者 gross 带）', 'QRY-CC05a', 'statistics/cost_curve_E6q.csv', [un], gU, band(gU, 3.54, 5.96),
             '可证伪门 D < 3.54：%s' % ('触发' if gU < 3.54 else '未触发')),
         sub('CC-E6q-05aN', 'net D ∈ [3.54, 5.96]（plan 读法：3.24 / 2.72 为 net）', 'QRY-CC05aN', 'statistics/account_summary_E6q.csv', [un], nU, band(nU, 3.54, 5.96), ''),
         sub('CC-E6q-05b', '年换手 ≤ 9.6', 'QRY-CC05b', 'statistics/account_summary_E6q.csv', [un], tU, band(tU, hi=9.6), ''),
         sub('CC-E6q-05c', '5 亿对同 H 父净差 ≥ 1.78', 'QRY-CC05c', 'statistics/cost_curve_E6q.csv', [un], cU, band(cU, lo=1.78), '')]
    st = agg(s)
    sub('CC-E6q-05', vb.get('CC-E6q-05', ''), 'QRY-CC05a', 'statistics/cost_curve_E6q.csv', [un], gU, st, '子条款 %s（原 gross 带与 plan net 带分作者评）' % '/'.join(s))
    out['CC-E6q-05'] = (st, 'yes')
    # ---- 06：价值密度（CASH 参照；A 1 亿 κ.5 δ.5；FULL 与两推导段）
    dn = C.Q.tab('statistics/density_E6q.csv')
    s = []
    if dn is not None:
        dsub = dn[(dn.reference_kind == 'CASH_SAME_TRIGGER') & (dn.A_cny == '100000000') & (dn.kappa == '0.5') & (dn.exponent == '0.5')]
        reg = C.ctx.reg
        dsub = dsub.assign(arm=[reg.loc[e].arm for e in dsub.exec_id], trig=[reg.loc[e].trigger for e in dsub.exec_id], H=[reg.loc[e].H for e in dsub.exec_id])
        for (arm, H), g in dsub.groupby(['arm', 'H']):
            for seg in ['FULL'] + list(O.DERIV_SEGS):
                L_ = g[(g.trig == 'T1b_LEVEL') & (g.segment == seg)]
                T_ = g[(g.trig == 'T1a') & (g.segment == seg)]
                if not len(L_) or not len(T_):
                    continue
                cid = 'CC-E6q-06.%s.H%s.%s' % (arm, H, seg)
                qid = 'QRY-CC06.%s.H%s.%s' % (arm, H, seg)
                C.Q.q(qid, 'statistics/density_E6q.csv', dict(reference_kind='CASH_SAME_TRIGGER', A_cny=100000000, kappa='0.5', exponent='0.5', segment=seg),
                      note='LEVEL %s vs T1a %s' % (L_.exec_id.iloc[0][:20], T_.exec_id.iloc[0][:20]))
                if L_.denominator_status.iloc[0] != 'OK' or T_.denominator_status.iloc[0] != 'OK':
                    s.append(sub(cid, '价值密度：LEVEL 臂 ≤ T1a 同臂（%s H%s %s）' % (arm, H, seg), qid, 'statistics/density_E6q.csv', [L_.exec_id.iloc[0], T_.exec_id.iloc[0]],
                                 np.nan, 'NOT_EVALUABLE', '分母退化：%s / %s' % (L_.denominator_status.iloc[0], T_.denominator_status.iloc[0])))
                    continue
                vl, vt = f(L_.value_density.iloc[0]), f(T_.value_density.iloc[0])
                stx = '支持' if vl <= vt else ('不支持' if vl > vt + 0.1 else 'mixed')
                s.append(sub(cid, '价值密度：LEVEL 臂 ≤ T1a 同臂（%s H%s %s）' % (arm, H, seg), qid, 'statistics/density_E6q.csv', [L_.exec_id.iloc[0], T_.exec_id.iloc[0]],
                             vl - vt, stx, 'LEVEL %.4f、T1a %.4f；可证伪门 > T1a + .1；(T1a, T1a + .1] 记 mixed' % (vl, vt)))
    st = agg(s)
    C.Q.q('QRY-CC06', 'statistics/density_E6q.csv', dict(reference_kind='CASH_SAME_TRIGGER', A_cny=100000000, kappa='0.5', exponent='0.5'))
    sub('CC-E6q-06', vb.get('CC-E6q-06', ''), 'QRY-CC06', 'statistics/density_E6q.csv', [], np.nan, st, '子条款 %d 行：支持 %d / 不支持 %d / mixed %d / 不可判 %d；排序不当因果识别' % (
        len(s), s.count('支持'), s.count('不支持'), s.count('mixed'), s.count('NOT_EVALUABLE')))
    out['CC-E6q-06'] = (st, 'yes')
    # ---- 07：RANDOM_TARGET（LEVEL H20 NATIVE owner；gross 与 net）
    s = []
    for mech, suf in (('RANDOM_TARGET_WITHIN_ARM', 'a'), ('RANDOM_TARGET_SOURCE_DOMAIN', 'b')):
        qid = 'QRY-CC07%s' % suf
        r_ = C.Q.q(qid, 'statistics/randoms_E6q.csv', dict(owner_exec_id=nat, mechanism=mech, segment='FULL'))
        if not len(r_):
            s.append(sub('CC-E6q-07%s' % suf, 'NATIVE − %s（LEVEL H20，FULL gross D）∈ [−.3, +1.0]' % mech, qid, 'statistics/randoms_E6q.csv', [nat], np.nan, 'NOT_EVALUABLE',
                         '随机层表不在（空跑或未覆盖）'))
            continue
        x = r_.iloc[0]
        dnet = f(x.real_D_ann_pp) - f(x.rand_mean_D_ann_pp)
        gfee = rt_gross_fee_gap(C.ctx, nat, mech)
        dg = dnet + gfee if np.isfinite(gfee) else np.nan
        if x.match_status == 'IDENTITY_TARGET_CONTROL':
            stx, nt = 'NOT_EVALUABLE', 'IDENTITY_TARGET_CONTROL：不记 HIT'
        else:
            stx, nt = band(dg, -0.3, 1.0), ''
        s.append(sub('CC-E6q-07%s' % suf, 'NATIVE − %s（LEVEL H20，FULL gross D）∈ [−.3, +1.0]' % mech, qid, 'statistics/randoms_E6q.csv', [nat], dg, stx,
                     '%s net 差 %.4f；gross = net + 费用差 %.4f（随机路径日费用均值，randoms/daily）；match_status %s；comparability %s；可证伪门 > 1.5 或 < −.5：%s' % (
                         nt, dnet, gfee if np.isfinite(gfee) else float('nan'), x.match_status, x.control_comparability,
                         '触发' if (np.isfinite(dg) and (dg > 1.5 or dg < -0.5)) else '未触发')))
    st = agg(s)
    sub('CC-E6q-07', vb.get('CC-E6q-07', ''), 'QRY-CC07a', 'statistics/randoms_E6q.csv', [nat], np.nan, st, '子条款 %s' % '/'.join(s))
    out['CC-E6q-07'] = (st, 'yes')
    # ---- 08：H30 − H20（对 H5 NATIVE 父）
    s = []
    CR = C.Q.tab('statistics/comparison_results_E6q.csv')
    if CR is not None:
        hh = CR[(CR.kind == 'H30_MINUS_H20_SAME_RULE') & (CR.segment == 'FULL')]
        for x in hh.itertuples(index=False):
            rl = C.ctx.reg.loc[x.left_exec_id]
            if rl.form != O.MAIN_FORM or rl.memory != 'HG10' or rl.scenario != 'FEASIBLE_DAILY' or rl.trigger not in ('T1a', 'T1b_LEVEL'):
                continue
            v = f(x.D_ann_pp)
            qid = 'QRY-CC08.%s.%s' % (rl.arm, rl.trigger)
            C.Q.q(qid, 'statistics/comparison_results_E6q.csv', dict(comparison_id=x.comparison_id, segment='FULL'))
            if rl.trigger == 'T1a':
                stx, fz = band(v, -0.3, 0.6), (v > 1.0)
                txt = 'T1a 臂 %s：H30 − H20 ∈ [−.3, +.6]' % rl.arm
            else:
                stx, fz = band(v, lo=0.3), (v < 0)
                txt = 'LEVEL 臂 %s：H30 − H20 ≥ +.3' % rl.arm
            s.append(sub('CC-E6q-08.%s.%s' % (rl.arm, rl.trigger), txt, qid, 'statistics/comparison_results_E6q.csv', [x.left_exec_id, x.right_exec_id], v, stx,
                         '对固定 H5 父的差 = 同规则 H30 − H20 直接差（两者 H5 父相同）；可证伪门：%s' % ('触发' if fz else '未触发'), ci=(x.boot_lo, x.boot_hi)))
    st = agg(s)
    C.Q.q('QRY-CC08', 'statistics/comparison_results_E6q.csv', dict(kind='H30_MINUS_H20_SAME_RULE', segment='FULL'))
    sub('CC-E6q-08', vb.get('CC-E6q-08', ''), 'QRY-CC08', 'statistics/comparison_results_E6q.csv', [], np.nan, st,
        '子条款 %d 行：支持 %d / 不支持 %d；族中位不遮翻号' % (len(s), s.count('支持'), s.count('不支持')))
    out['CC-E6q-08'] = (st, 'yes')
    # ---- 09：D3
    v = C.diag('QRY-CC09', 'D3', 'entry_persistence', dict(item='decline_age1_to_10_q5', key1='K_strength', key2='T3_minus_T1', stat='NATIVE|NONE|H20|main|HG10|bp'))
    vs = C.diag('QRY-CC09_size', 'D3', 'entry_persistence', dict(item='decline_age1_to_10_q5', key1='size', key2='T3_minus_T1', stat='NATIVE|NONE|H20|main|HG10|bp'))
    stx = '支持' if v >= 5 else ('不支持' if v <= 2 else 'mixed') if np.isfinite(v) else 'NOT_EVALUABLE'
    sub('CC-E6q-09', vb.get('CC-E6q-09', ''), 'QRY-CC09', 'diagnostics/D3_entry_persistence_E6q.csv', [], v, stx,
        '只推导段；K 强 = 取向后的 K 腿好度（−K0 当日源域三分位，T3 最强；形成权重近乎常数不分级）；上三分位下降 − 下三分位下降；≥ 5 bp 支持、≤ 2 bp 不支持（可证伪门）、其间 mixed；size 层同式 %.2f bp（QRY-CC09_size；分层见 D3）' % vs)
    out['CC-E6q-09'] = (stx, 'yes')
    # ---- 10：两实现比值
    I = C.Q.q('QRY-CC10', 'verify/impact_reconciliation_E6q.csv', dict(order_kind='ALL'))
    s = []
    if len(I):
        I4 = I[I.segment.isin(list(O.SEGS))]
        r_ = I4.ratio.astype(float).to_numpy()
        inv = 1.0 / r_
        var = float(r_.max() / r_.min() - 1.0)
        share = float(np.mean((inv >= 1.7) & (inv <= 2.1)))
        stx = '不支持' if var > 0.3 else ('支持' if share == 1.0 else 'mixed')
        sub('CC-E6q-10', vb.get('CC-E6q-10', ''), 'QRY-CC10', 'verify/impact_reconciliation_E6q.csv', [], share, stx,
            '7 对象 × 4 段 = %d 格：legacy / curve ∈ [%.3f, %.3f]（curve / legacy ∈ [%.3f, %.3f]）；落入 [1.7, 2.1]（curve / legacy 向）份额 %.3f；跨对象 / 段变动 %.0f%%（可证伪门 > ±30%%：%s）；'
            '经验读法，真 ENG = IMPACT_ALGEBRA_EQUAL 见 ENG-01' % (len(r_), r_.min(), r_.max(), inv.min(), inv.max(), share, var * 100, '触发' if var > 0.3 else '未触发'))
        out['CC-E6q-10'] = (stx, 'yes')
    else:
        sub('CC-E6q-10', vb.get('CC-E6q-10', ''), 'QRY-CC10', 'verify/impact_reconciliation_E6q.csv', [], np.nan, 'NOT_EVALUABLE', 'S0-A 表未命中')
        out['CC-E6q-10'] = ('NOT_EVALUABLE', 'yes')
    # ---- 11：BERNOULLI 首达
    RD = C.Q.q('QRY-CC11a', 'statistics/randoms_E6q.csv', dict(mechanism='BERNOULLI_FIRSTHIT', segment='FULL'))
    s = []
    if len(RD):
        ir = RD.intensity_ratio.apply(f).to_numpy()
        ok = np.isfinite(ir)
        sh = float(np.mean((ir[ok] >= 0.9) & (ir[ok] <= 1.1))) if ok.any() else np.nan
        s.append(sub('CC-E6q-11a', '强度 ∈ [.9, 1.1]（全部 BERNOULLI owner，FULL）', 'QRY-CC11a', 'statistics/randoms_E6q.csv', [], sh, '支持' if sh == 1.0 else ('不支持' if np.isfinite(sh) else 'NOT_EVALUABLE'),
                     '%d 个 owner：强度 ∈ [%.3f, %.3f]，带内份额 %.3f' % (int(ok.sum()), np.nanmin(ir) if ok.any() else np.nan, np.nanmax(ir) if ok.any() else np.nan, sh)))
        natT = pk('NATIVE', 'T1a')
        x = C.Q.q('QRY-CC11b', 'statistics/randoms_E6q.csv', dict(owner_exec_id=natT, mechanism='BERNOULLI_FIRSTHIT', segment='FULL'))
        mv = f(x.rand_mean_D_ann_pp.iloc[0]) if len(x) else np.nan
        s.append(sub('CC-E6q-11b', 'T1a H20 的 BERNOULLI 均值 D < 1.71', 'QRY-CC11b', 'statistics/randoms_E6q.csv', [natT], mv, band(mv, hi=1.71, hi_open=True),
                     '强度 %s；comparability %s' % (x.intensity_ratio.iloc[0] if len(x) else '', x.control_comparability.iloc[0] if len(x) else '')))
    else:
        C.Q.q('QRY-CC11b', 'statistics/randoms_E6q.csv', dict(mechanism='BERNOULLI_FIRSTHIT'))
        s = [sub('CC-E6q-11a', '强度 ∈ [.9, 1.1]', 'QRY-CC11a', 'statistics/randoms_E6q.csv', [], np.nan, 'NOT_EVALUABLE', '随机层表不在（空跑）'),
             sub('CC-E6q-11b', 'T1a H20 均值 D < 1.71', 'QRY-CC11b', 'statistics/randoms_E6q.csv', [], np.nan, 'NOT_EVALUABLE', '随机层表不在（空跑）')]
    st = agg(s)
    sub('CC-E6q-11', vb.get('CC-E6q-11', ''), 'QRY-CC11a', 'statistics/randoms_E6q.csv', [], np.nan, st, '两条件分开评：%s' % '/'.join(s))
    out['CC-E6q-11'] = (st, 'yes')
    return out


def rt_gross_fee_gap(ctx, owner, mech):
    """FULL 年化（owner 日费用率 − 随机路径日费用率均值）：gross 差 = net 差 + 本项。只在 B 相（randoms/daily 存在）可算。"""
    r = ctx.reg.loc[owner]
    d = O.P('randoms', 'daily', r.exec_hash[:2])
    if not os.path.isdir(d):
        return np.nan
    fs = [fn for fn in os.listdir(d) if fn.startswith('%s_%s_' % (r.exec_hash, mech))]
    if not fs:
        return np.nan
    F = np.vstack([np.load(os.path.join(d, fn), allow_pickle=False)['feefr'].astype(float) for fn in sorted(fs)])
    sup = ctx.masks['FULL'][:F.shape[1]]
    z = np.load(ST.acct_file(ctx, r.exec_hash), allow_pickle=False)['DY']
    nav = z[:, ST.E.DYI['nav_post']]
    vprev = np.r_[O.V0, nav[:-1]]
    own = z[:, ST.E.DYI['fee']] / vprev
    n = min(len(own), F.shape[1])
    return float((np.nanmean(own[:n][sup[:n]]) - np.nanmean(F[:, :n][:, sup[:n]])) * O.ANN_PP)


# ------------------------------------------------------------------ Q / G / ENG
def q_claims(C):
    LQ = O.read_csv(O.P('registration', 'ledger_Q_E6q.csv'), dtype=str).fillna('')
    pk = C.pick
    m1, m25, m3, hL, nat, un = (pk('REINVEST_NEW', 'T1b_LEVEL'), pk('REINVEST_LIQ_5E8', 'T1b_LEVEL'), pk('EXIT_GATE_LIQ_5E8', 'T1b_LEVEL'), pk('EXIT_HALF', 'T1b_LEVEL'),
                                pk('NATIVE', 'T1b_LEVEL'), pk('NATIVE', 'UNION_T1a_T8'))
    natT = pk('NATIVE', 'T1a')
    spec = {
        'Q01': ('verify/impact_reconciliation_ladder_E6q.csv', dict(step='L02_NAV_NODE_WEIGHT'), 'residual_ratio', [],
                'S0-A：7 对象在 L02（权重节点替换）后的残差比均值（1 = 共同输入下两式代数相同；L00 基础比值 legacy / curve 见 S0-A 报告）'),
        'Q02': ('diagnostics/D2_target_E6q.csv', dict(item='supply', key1='new_legal_n_mean_on_plan_days', key2='REINVEST_NEW|T1b_LEVEL|H20|main|HG10'), 'value', [m1],
                'M1 LEVEL H20：有再投计划日的合法 new 名字数均值；重复率、空名单日、预算短缺、队列过期见 D2 supply'),
        'Q03': ('statistics/account_summary_E6q.csv', dict(exec_id=m1, segment='FULL'), 'D_cash_same_trigger_ann_pp', [m1], 'M1 LEVEL H20 对同触发 CASH 的 FULL 差；D_sc 与敞口差并列'),
        'Q04': ('diagnostics/D1_cost_source_E6q.csv', dict(item='impact_by_side', key1='BUY', key2='REINVEST_LIQ_5E8|T1b_LEVEL|H20|main|HG10', stat='A5e+08|arm_minus_native'),
                'value', [m25], 'M2_5E8 LEVEL H20：买方 curve 冲击（臂 − 同触发 NATIVE，5 亿）；按订单类别 × 参与率五分位见 D1'),
        'Q05': ('statistics/account_summary_E6q.csv', dict(exec_id=m3, segment='FULL'), 'D_native_same_trigger_ann_pp', [m3], 'M3_5E8 LEVEL H20 对同触发 NATIVE 的 FULL 差；延期与强制见 D4'),
        'Q06': ('statistics/account_summary_E6q.csv', dict(exec_id=hL, segment='FULL'), 'D_native_same_trigger_ann_pp', [hL], '主 M4（余半到期）LEVEL H20 对全量 NATIVE；REARM 与残仓见 D5'),
        'Q07': ('diagnostics/D5_dose_E6q.csv', dict(item='half_x_recycle_four_accounts', key1='H20|T1b_LEVEL', key2='INTERACTION', segment='FULL'), 'value', [],
                '卖半 × 再投半四账户交互（LEVEL H20，net_ann_pp）'),
        'Q08': ('diagnostics/D7_composition_E6q.csv', dict(item='union_composition', key1='NATIVE|UNION_T1a_T8|H20|main|HG10', key2='T8_only', stat='count_share'), 'value', [un],
                '并集 H20 意向中 T8 独有份额；交集 / 金额 / q5 / 费用见 D7'),
        'Q09': ('statistics/randoms_E6q.csv', dict(owner_exec_id=natT, mechanism='BERNOULLI_FIRSTHIT', segment='FULL'), 'intensity_ratio', [natT], 'T1a H20 首达强度比'),
        'Q10': ('statistics/randoms_E6q.csv', dict(owner_exec_id=nat, mechanism='RANDOM_TARGET_WITHIN_ARM', segment='FULL'), 'limit_day_share', [nat],
                'LEVEL H20 NATIVE 的 RANDOM_TARGET（臂内）触限 / 无解日份额；match_status 与 target_set_size 同行'),
        'Q11': ('statistics/cost_curve_E6q.csv', dict(exec_id=m25, comparator_kind='SAME_ARM_PARENT', A_cny=100000000, kappa='0.5', exponent='0.5', segment='FULL'),
                'net_after_impact_diff_ann_pp', [m25], 'A_ref = 5 亿的 M2 在 A_eval = 1 亿的成本后差；反馈见 cost_feedback'),
        'Q12': ('diagnostics/D3_entry_persistence_E6q.csv', dict(item='decline_age1_to_10_q5', key1='K_strength', key2='T3_minus_T1', stat='NATIVE|NONE|H20|main|HG10|bp'), 'value', [],
                'D3（只推导段）K 强上 − 下三分位的 q5 前向超额日龄 1→10 下降差（bp）'),
        'Q13': ('diagnostics/landmark_E6q.csv', dict(exec_id=nat, landmark_age=10, state='NOT_TRIGGERED', q=5, weighting='EQUAL'), 'mean_fwd_excess_bp', [nat],
                'LEVEL H20 NATIVE 日龄 10、截至 T 未触发批次的 q5 前向超额（等权）；各年龄 / 状态 / q1·q10 与至原 due 分开见 landmark 与 D4 fwd_to_original_due'),
        'Q14': ('diagnostics/D1_cost_source_E6q.csv', dict(item='impact_by_side', key1='SELL', key2='NATIVE|T1b_LEVEL|H20|main|HG10', stat='A5e+08|arm_minus_parent'), 'value', [nat],
                'LEVEL H20 NATIVE 卖方 curve 冲击（臂 − 同臂父，5 亿）；按订单类别见 D1'),
        'Q15': ('statistics/main32_E6q.csv', {}, 'FULL_D_frontier_ann_pp', [], '主 32 行对前沿锚（H20 T1a NATIVE）FULL 差为正的行数（同 H 父 / H5 / LEVEL H20 / TOTAL / MDD 见主表与 D9）'),
        'Q16': ('reports/claims_E6q.csv', dict(kind='PREDICTION', claim_status='不支持'), 'claim_status', [], 'E01–E07 中带外（不支持）条数（本表 PREDICTION 行）；归因到假设层见 notes'),
        'Q17': ('statistics/warm_sensitivity_E6q.csv', {}, 'D_warm_minus_cont', [], 'WARM（各段重置）− 连续状态 的最大绝对差（主 32 同父）'),
        'Q18': ('registration/park_E6q.csv', {}, 'status', [], 'park 台账条数（P63–P75 中本轮登记）；未测域与恢复条件见 park 表'),
    }
    for r in LQ.itertuples(index=False):
        rel, filt, col, ids, note = spec[r.q_id]
        qid = 'QRY-%s' % r.q_id
        if r.q_id == 'Q16':
            n16 = sum(1 for x in C.rows if x['kind'] == 'PREDICTION' and x['claim_status'] == '不支持')
            C.Q.reg[qid] = dict(query_id=qid, table=rel, filter='kind=PREDICTION & claim_status=不支持', n_rows=n16, generator='e6q_claims.py')
            sub = pd.DataFrame({col: ['不支持'] * n16})
        else:
            sub = C.Q.q(qid, rel, filt)
        if r.q_id == 'Q01':
            v = float(sub[col].apply(f).mean()) if len(sub) else np.nan
        elif r.q_id == 'Q15':
            x = sub[col].apply(f) if len(sub) else pd.Series(dtype=float)
            v = float((x > 0).sum()) if len(x) else np.nan
        elif r.q_id == 'Q16':
            v = float((sub[col] == '不支持').sum()) if len(sub) else np.nan
        elif r.q_id == 'Q17':
            x = sub[col].apply(f) if len(sub) else pd.Series(dtype=float)
            v = float(x.abs().max()) if len(x) else np.nan
        elif r.q_id == 'Q18':
            v = float(len(sub))
        else:
            v = f(sub[col].iloc[0]) if len(sub) else np.nan
        C.add(r.q_id, 'QUESTION', r.author or 'plan v1.1 §12.1', r.statement_verbatim, qid, rel, ids, v, '开放', note=note)
        i = LQ.index[LQ.q_id == r.q_id][0]
        LQ.loc[i, 'result_query'] = qid
        LQ.loc[i, 'result_row'] = '%s %s' % (rel, C.Q.reg[qid]['filter'])
        LQ.loc[i, 'state'] = '开放'
    return LQ


def g_claims(C):
    LG = O.read_csv(O.P('registration', 'ledger_G_E6q.csv'), dtype=str).fillna('')
    for r in LG.itertuples(index=False):
        qid = 'QRY-%s' % r.g_id
        sub = C.Q.q(qid, 'diagnostics/G1_E6q.csv', dict(block=r.g_id))
        v = float(len(sub))
        C.add(r.g_id, 'G_CHAIN', r.author or 'plan v1.1 §3.2', r.statement_verbatim, qid, 'diagnostics/G1_E6q.csv', [], v, r.state or 'PRESPECIFIED_DISCRIMINATING_TEST',
              note='第一道标签（推导段）；result_value = G1 行数；%s' % (r.result_row or ''))


def eng_claims(C):
    lad = C.Q.q('QRY-ENG01', 'verify/impact_reconciliation_ladder_E6q.csv', dict(step='L02_NAV_NODE_WEIGHT'))
    rr = lad.residual_ratio.apply(f).to_numpy() if len(lad) else np.zeros(0)
    v = float(np.max(np.abs(rr - 1.0))) if len(rr) and np.isfinite(rr).all() else np.nan
    C.add('ENG-01', 'ENGINEERING', 'plan §12.3 #10', 'IMPACT_ALGEBRA_EQUAL：共同输入下 δ = .5 两实现代数相同（S0-A L02 权重节点替换后残差比 = 1；%d 个对象）' % len(rr), 'QRY-ENG01',
          'verify/impact_reconciliation_ladder_E6q.csv', [], v, '技术PASS' if (np.isfinite(v) and v <= 1e-9) else '技术FAIL', note='result_value = max |残差比 − 1|（全部对象）')
    ids = C.Q.tab('verify/identities_E6q_runs.csv') if os.path.exists(os.path.join(C.ctx.root, 'verify', 'identities_E6q_runs.csv')) else None
    k = 2
    for chk in ('E6P_ACCOUNT_REPLICATION', 'ZERO_INTERVENTION_EQ_NATIVE', 'CASH_EQUATION', 'TOKEN_CONSERVATION', 'TICKET_CONSERVATION', 'CHECKPOINT_RESTORE_IDEMPOTENT'):
        qid = 'QRY-ENG%02d' % k
        sub = C.Q.q(qid, 'verify/identities_E6q_runs.csv', dict(check_id=chk))
        if len(sub):
            ok = bool((sub.status == 'PASS').all())
            C.add('ENG-%02d' % k, 'ENGINEERING', 'brief §4 / plan §6', '%s（%d 行）' % (chk, len(sub)), qid, 'verify/identities_E6q_runs.csv', [], f(sub.max_abs_diff.astype(float).max()),
                  '技术PASS' if ok else '技术FAIL')
        else:
            C.add('ENG-%02d' % k, 'ENGINEERING', 'brief §4 / plan §6', chk, qid, 'verify/identities_E6q_runs.csv', [], np.nan, 'NOT_EVALUABLE', note='运行恒等表不在（空跑）')
        k += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=['A2', 'B'], default='B')
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    t0 = time.time()
    root = O.P(*a.root.split('/')) if a.root else None
    ctx = ST.Ctx(a.phase, False, root)
    S, acc = ST.load_all(ctx)
    boot = ST.Boot(ctx)
    q = Q(ctx)
    C = Claims(ctx, q)
    LE = e_claims(C, S, boot)
    LQ = q_claims(C)
    g_claims(C)
    carry = O.read_csv(O.P('registration', 'cc_statement_carry.csv'), dtype=str).fillna('')
    out = cc_claims(C, carry)
    eng_claims(C)
    for i, r in carry.iterrows():
        st, cmpb = out.get(r.id, ('NOT_EVALUABLE', 'no'))
        carry.loc[i, 'claim_status'] = st
        carry.loc[i, 'comparable'] = cmpb
        if '｜执行端' not in r.estimand_note:
            carry.loc[i, 'estimand_note'] = r.estimand_note + '｜执行端：句级 + 子条款见 reports/claims_E6q.csv（%s*）' % r.id
    CL = pd.DataFrame(C.rows, columns=CCOLS)
    QR = pd.DataFrame(list(q.reg.values()), columns=QCOLS).sort_values('query_id')
    miss = [x for x in CL.query_id if x and x not in set(QR.query_id)]
    if miss:
        raise RuntimeError('query 未登记：%s' % miss[:5])
    outs = []
    for rel, df in (('reports/claims_E6q.csv', CL), ('reports/query_registry_E6q.csv', QR)):
        p = ctx.out(*rel.split('/'))
        O.atomic_write_csv(p, df)
        outs.append(p)
    if ctx.root == O.work():
        for rel, df in (('registration/cc_statement_carry.csv', carry), ('registration/ledger_E_E6q.csv', LE), ('registration/ledger_Q_E6q.csv', LQ)):
            p = O.P(*rel.split('/'))
            O.atomic_write_csv(p, df)
            outs.append(p)
    else:
        for rel, df in (('registration/cc_statement_carry.csv', carry), ('registration/ledger_E_E6q.csv', LE), ('registration/ledger_Q_E6q.csv', LQ)):
            p = ctx.out(*rel.split('/'))
            O.atomic_write_csv(p, df)
            outs.append(p)
    facts = dict(phase=a.phase, claims=len(CL), queries=len(QR), by_kind=CL.kind.value_counts().to_dict(), by_status=CL.claim_status.value_counts().to_dict(),
                 zero_row_queries=int((QR.n_rows == 0).sum()), wall_s=round(time.time() - t0, 1))
    O.write_receipt('E6q_claims_%s' % a.phase, outs, code=[__file__, O.__file__, ST.__file__], **facts)
    print(json.dumps(facts, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
