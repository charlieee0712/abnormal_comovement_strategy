# -*- coding: utf-8 -*-
"""E6r 预测与报告表（附录 B.20 / E；plan §12；brief §5）：
- e_results_E6r.csv（E01–E07；plan score_e：support = value ≥ lower，上端开放、越上端另记 ABOVE_WORKING_RANGE；gross / net8 取 account_summary FULL 印出值之差，
  曲线取 cost_curve E_REFERENCE 行 κ .5 δ .5 FULL）与 e_summary_E6r.csv；
- claims_E6r.csv：Q01–Q18（开放，只报）、E01–E07（= e_results.status）、G-P-01…04 / GW01…08（第一道标签）、CC-E6r-01…09（句级 + 子条款 CC-E6r-0xa…；
  按原句评：落空的可证伪条件 → 不支持；全部子条款成立 → 支持；其余 → mixed；缺表 → NOT_EVALUABLE）；
- query_registry_E6r.csv（claims / 政策字段 / G1 / D 表里出现的全部 query_id）；reflection_E6r.csv（E 7 + G 12 + CC 9；plan §12.4 十栏 + 版本 / 来源 / 首测 / plan sha）；
- 回填 ledger_E（state / result_query / result_row）、ledger_Q（state / result_row）、cc_statement_carry 的五列（plan_reading / estimand_note / comparable / claim_status / sub_claims）。
原句中的"同臂父"在入场算子语境 = 政策参照（同退出 FLAT）。用法：python3 e6r_claims.py [--root <输出根>]（与 e6r_stats.py 同根）"""
import os
import glob
import json
import argparse

import numpy as np
import pandas as pd

import e6r_core as O

SEG4 = list(O.SEGS)
G = {}
WR = {'BELOW_WORKING_RANGE', 'WITHIN_WORKING_RANGE', 'ABOVE_WORKING_RANGE'}


def rd(rel):
    p = os.path.join(G['root'], rel)
    if not os.path.exists(p) and os.path.exists(p + '.gz'):
        p = p + '.gz'
    return pd.read_csv(p, dtype=str, keep_default_na=False) if os.path.exists(p) else pd.DataFrame()


def f(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if np.isfinite(v) else None


def score_e(value, lower, upper, upper_open, status_ok=True, identity=False):
    """plan 附录 C score_e（D 脚本同式）。"""
    if not status_ok or value is None:
        return 'NOT_EVALUABLE', None, None
    if identity:
        return 'IDENTITY_NO_NEW_TEST', value > 0, None
    good = value >= lower if upper_open else (lower <= value <= upper)
    wr = 'BELOW_WORKING_RANGE' if value < lower else ('ABOVE_WORKING_RANGE' if value > upper else 'WITHIN_WORKING_RANGE')
    return ('支持' if good else '不支持'), value > 0, wr


def tf(v):
    return '' if v is None else ('true' if v else 'false')


# ------------------------------------------------------------------ 取数
def pick(trig, scheme='FLAT', H='20', exit_op='NATIVE'):
    R = G['R']
    x = R[(R.trigger == trig) & (R.weight_scheme == scheme) & (R.funding_H == H) & (R.exit_op == exit_op) & (R.form == O.MAIN_FORM) & (R.memory == 'HG10') &
          (R.scenario == O.FEAS)]
    return x.iloc[0] if len(x) else None


def sv(e, col, seg='FULL'):
    r = G['sm'].get((e, seg))
    return f(getattr(r, col)) if (r is not None and r.status == 'COMPUTED') else None


def dpol(e, col):
    """col（gross_ann_pp / net_ann_pp / abs_net_ann_pp / turnover_ann / exposure_mean / max_drawdown_total）的 FULL 本账户 − 政策参照。"""
    ref = G['reg'].loc[e].policy_reference_exec_id
    a, b = sv(e, col), sv(ref, col) if ref else None
    return (a - b) if (a is not None and b is not None) else None


def ratio(e, col, ref):
    a, b = sv(e, col), sv(ref, col)
    return (a / b) if (a is not None and b not in (None, 0.0)) else None


def curve(e, kind, ref, A_, kappa=0.5, x=0.5, seg='FULL'):
    v = G['cc'].get((e, kind, ref, int(A_), kappa, x, seg))
    return v


def rnd(e, mech, seg='FULL'):
    rid = G['rref'].get((e, mech))
    r = G['rd'].get((rid, seg)) if rid else None
    return r


def comp_D(kind, left, col='D_net_ann_pp', seg='FULL'):
    C = G['cmp']
    x = C[(C.kind == kind) & (C.left_exec_id == left)]
    if not len(x):
        return None
    r = G['cr'].get((x.comparison_id.iloc[0], seg))
    return f(getattr(r, col)) if r is not None else None


# ------------------------------------------------------------------ E
def e_block():
    cl = json.load(open(O.P('registration', 'spec', 'claims.json'), encoding='utf-8'))
    rows = []
    for c in cl:
        o, rf = G['lid2e'][c['owner']], G['lid2e'][c['reference']]
        st_ = c['statistic']
        ov = refv = None
        if st_ in ('EXCESS_GROSS_DIFF', 'EXCESS_NET8_DIFF'):
            col = 'gross_ann_pp' if st_ == 'EXCESS_GROSS_DIFF' else 'net_ann_pp'
            ov, refv = sv(o, col), sv(rf, col)
            okst = ov is not None and refv is not None
            v = (ov - refv) if okst else None
        else:
            A_ = int(st_.replace('EXCESS_CURVE_DIFF_A', ''))
            v = curve(o, 'E_REFERENCE', rf, A_)
            okst = v is not None
        ident = o == rf
        st, ep, wr = score_e(v, float(c['lower']), float(c['upper']), bool(c['upper_open_for_support']), okst, ident)
        rows.append(dict(e_id=c['id'], owner_exec_id=o, reference_exec_id=rf, statistic=st_, segment='FULL', owner_value=ov if ov is not None else '',
                         reference_value=refv if refv is not None else '', value=v if v is not None else '', lower=c['lower'], upper=c['upper'],
                         upper_open_for_support=tf(bool(c['upper_open_for_support'])), identity_flag=tf(ident), status=st, economic_positive=tf(ep),
                         working_range=wr or '', exact_reference='', query_id='QRY-%s' % c['id']))
    E_ = pd.DataFrame(rows)
    n_sup = int((E_.status == '支持').sum())
    n_ne = int((E_.status == 'NOT_EVALUABLE').sum())
    n_id = int((E_.status == 'IDENTITY_NO_NEW_TEST').sum())
    n_ev = 7 - n_ne - n_id
    S = pd.DataFrame([dict(n_registered=7, n_evaluable=n_ev, n_supported=n_sup, n_not_evaluable=n_ne, n_identity_no_new_test=n_id,
                           share_supported_registered=n_sup / 7.0, share_supported_evaluable=(n_sup / n_ev) if n_ev else '')])
    return E_, S


# ------------------------------------------------------------------ CC（按原句 + 子条款）
def sub(lst, sid, text, value, ok):
    lst.append(dict(id=sid, text=text, value='' if value is None else round(float(value), 6), result='NA' if ok is None else ('PASS' if ok else 'FAIL')))


def judge(subs, falsified):
    if any(s['result'] == 'NA' for s in subs) and all(s['result'] != 'FAIL' for s in subs) and not falsified:
        return 'NOT_EVALUABLE' if all(s['result'] == 'NA' for s in subs) else 'mixed'
    if falsified:
        return '不支持'
    if all(s['result'] == 'PASS' for s in subs):
        return '支持'
    return 'mixed'


def inband(v, lo, hi):
    return None if v is None else (lo <= v <= hi)


def ge(v, x):
    return None if v is None else v >= x


def cc_block():
    out = {}
    bases = (('T1b_LEVEL', 'LEVEL'), ('T1a', 'T1a'), ('NONE', 'NONE'))
    # CC-01 GATE_STATE
    subs, fal = [], False
    band = {'T1b_LEVEL': (0.05, 0.40), 'T1a': (0.10, 0.60), 'NONE': (0.10, 0.60)}
    for trig, nm in bases:
        r = pick(trig, 'GATE_STATE')
        e = r.exec_id
        ref = r.policy_reference_exec_id
        gd = dpol(e, 'gross_ann_pp')
        sub(subs, 'a_%s' % nm, '%s H20 gross D ∈ [%.2f, %.2f]' % (nm, *band[trig]), gd, inband(gd, *band[trig]))
        tr = ratio(e, 'turnover_ann', ref)
        sub(subs, 'b_%s' % nm, '%s 年换手 ≤ NATIVE（同退出 FLAT）× .95' % nm, tr, None if tr is None else tr <= 0.95)
        for A_ in (1e8, 5e8):
            c = curve(e, 'POLICY_REFERENCE', ref, A_)
            sub(subs, 'c_%s_%d' % (nm, int(A_ / 1e8)), '%s %d 亿 curve 净差 ≥ gross D − .1' % (nm, int(A_ / 1e8)), c, None if (c is None or gd is None) else c >= gd - 0.1)
        x = rnd(e, 'RANDOM_GATE_COUNT')
        rr = (f(x.real_D_ann_pp) - f(x.rand_mean_D_ann_pp)) if (x is not None and f(x.rand_mean_D_ann_pp) is not None) else None
        sub(subs, 'd_%s' % nm, '%s 真实 − RANDOM_GATE_COUNT 均值 > 0' % nm, rr, None if rr is None else rr > 0)
        fal |= (gd is not None and gd <= 0) or (tr is not None and tr >= 1.0) or (rr is not None and rr <= 0)
    out['CC-E6r-01'] = (judge(subs, fal), subs, 'gross_D_policy（FULL）+ turnover_ann 对同退出 FLAT + cost_curve POLICY_REFERENCE 1 / 5 亿 + RANDOM_GATE_COUNT real − mean',
                        '带的推导用了 age1 份额（决策端 #168），按原句评；"换手不降" = 比值 ≥ 1')
    # CC-02 TILT_CVR λ .5
    subs, fal = [], False
    band = {'T1b_LEVEL': (0.30, 1.30), 'T1a': (0.20, 0.70), 'NONE': (0.20, 0.70)}
    a5 = {'T1b_LEVEL': 1.0, 'T1a': 0.4}
    for trig, nm in bases:
        r = pick(trig, 'TILT_CVR_L050')
        e, ref = r.exec_id, r.policy_reference_exec_id
        gd = dpol(e, 'gross_ann_pp')
        sub(subs, 'a_%s' % nm, '%s H20 gross D ∈ [%.2f, %.2f]' % (nm, *band[trig]), gd, inband(gd, *band[trig]))
        x = rnd(e, 'RANDOM_TILT_TICKETS')
        okr = x is not None and f(x.mcse) is not None and f(x.rand_mean_D_ann_pp) is not None
        rr = (f(x.real_D_ann_pp) - f(x.rand_mean_D_ann_pp)) if okr else None
        sub(subs, 'b_%s' % nm, '%s 真实 − RANDOM_TILT 均值 ≥ 2·MCSE' % nm, rr, None if not okr else rr >= 2 * f(x.mcse))
        c1 = curve(e, 'POLICY_REFERENCE', ref, 1e8)
        sub(subs, 'c_%s_1' % nm, '%s 1 亿净差 ≥ gross D − .3' % nm, c1, None if (c1 is None or gd is None) else c1 >= gd - 0.3)
        if trig in a5:
            c5 = curve(e, 'POLICY_REFERENCE', ref, 5e8)
            sub(subs, 'c_%s_5' % nm, '%s 5 亿净差 ≥ gross D − %.1f' % (nm, a5[trig]), c5, None if (c5 is None or gd is None) else c5 >= gd - a5[trig])
        fal |= (gd is not None and gd <= 0) or (rr is not None and rr <= 0)
    out['CC-E6r-02'] = (judge(subs, fal), subs, 'gross_D_policy + randoms RANDOM_TILT_TICKETS（FULL）+ cost_curve POLICY_REFERENCE',
                        '带按 1/3 推导、约为 λ/3 的两倍（决策端 #169），按原句评；E01 / E02 是修正后的同对象预测')
    # CC-03 TILT_SIZE 竞争解释
    subs, fal = [], False
    D3 = rd('diagnostics/D3_cvr_size_E6r.csv')
    resid = None
    if len(D3):
        x = D3[(D3.item == 'cvr20_x_size_q5_age1') & (D3.stat == 'cohort_domain|mean_bp')]
        v = {(r.key1, r.key2): f(r.value) for r in x.itertuples(index=False)}
        diffs = [v.get(('CVR20_T1', 'SIZE_T%d' % k)) - v.get(('CVR20_T3', 'SIZE_T%d' % k)) for k in (1, 2, 3)
                 if v.get(('CVR20_T1', 'SIZE_T%d' % k)) is not None and v.get(('CVR20_T3', 'SIZE_T%d' % k)) is not None]
        resid = float(np.mean(diffs)) if diffs else None
    for trig, nm in bases:
        rs = pick(trig, 'TILT_SIZE_L050')
        rc = pick(trig, 'TILT_CVR_L050')
        gs = dpol(rs.exec_id, 'gross_ann_pp')
        sub(subs, 'a_%s' % nm, '%s TILT_SIZE gross D > 0' % nm, gs, None if gs is None else gs > 0)
        gc = sv(rc.exec_id, 'gross_ann_pp')
        gz = sv(rs.exec_id, 'gross_ann_pp')
        dcs = (gc - gz) if (gc is not None and gz is not None) else None
        sub(subs, 'b_%s' % nm, '%s sign(TILT_CVR − TILT_SIZE) = 交叉表 CVR 残余符号（D3 cohort 域三 size 档平均 T1 − T3）' % nm, dcs,
            None if (dcs is None or resid is None) else bool(np.sign(dcs) == np.sign(resid)))
        fal |= (resid is not None and dcs is not None and resid > 10 and dcs < 0)
        sz = [sv(rs.exec_id, 'size_dev_pp', q) for q in SEG4]
        cz = [sv(rc.exec_id, 'size_dev_pp', q) for q in SEG4]
        ms = float(np.mean(sz)) if all(x is not None for x in sz) else None
        mc = float(np.mean(cz)) if all(x is not None for x in cz) else None
        sub(subs, 'c_%s' % nm, '%s TILT_SIZE size_dev 四段均值 > 1.5' % nm, ms, None if ms is None else ms > 1.5)
        sub(subs, 'd_%s' % nm, '%s TILT_CVR size_dev 四段均值 < 1.0' % nm, mc, None if mc is None else mc < 1.0)
    out['CC-E6r-03'] = (judge(subs, fal), subs, 'gross_D_policy（SIZE 与 CVR）+ D3 交叉表 + size_dev_pp',
                        'size_dev_pp 符号约定：正 = 偏小盘（参照的 clean 市值分位资本加权均值 − 本账户，× 100）；两政策差的符号不等于交叉表残余符号（plan 读法）')
    # CC-04 DROP_T3 LEVEL H20
    subs = []
    r = pick('T1b_LEVEL', 'DROP_T3')
    d = sv(r.exec_id, 'D_policy_ann_pp')
    ad = dpol(r.exec_id, 'abs_net_ann_pp')
    sub(subs, 'a', 'LEVEL H20 缩放超额 D ∈ [.1, .8]', d, inband(d, 0.1, 0.8))
    sub(subs, 'b', 'LEVEL H20 绝对净值 D < 0', ad, None if ad is None else ad < 0)
    out['CC-E6r-04'] = (judge(subs, d is not None and d <= 0), subs, 'D_policy_ann_pp 与 abs_net_ann_pp 差', '绝对净值下降并非必然（plan 读法），按原句评')
    # CC-05 TILT_H
    subs, fal = [], False
    for trig, nm in bases[:2]:
        r = pick(trig, 'TILT_H')
        d = sv(r.exec_id, 'D_policy_ann_pp')
        sub(subs, 'a_%s' % nm, '%s H20 TILT_H 对 NATIVE H20 平权 net D ∈ [−.4, +.4]' % nm, d, inband(d, -0.4, 0.4))
        fal |= d is not None and d > 0.6
        x = rnd(r.exec_id, 'RANDOM_TENOR_LABEL')
        rr = (f(x.real_D_ann_pp) - f(x.rand_mean_D_ann_pp)) if (x is not None and f(x.rand_mean_D_ann_pp) is not None) else None
        sub(subs, 'r_%s' % nm, '%s 真实 − RANDOM_TENOR_LABEL 均值（并报，不作判据）' % nm, rr, None)
    subs = [s_ if not s_['id'].startswith('r_') else dict(s_, result='NA') for s_ in subs]
    out['CC-E6r-05'] = (judge([s_ for s_ in subs if not s_['id'].startswith('r_')], fal), subs, 'D_policy_ann_pp（对同退出 FLAT H20）+ RANDOM_TENOR_LABEL 并报',
                        '未正式测试前不能写已否；D > .6 不唯一识别 size / K 机制（plan 读法）')
    # CC-06 UNIFORM_CAP15
    subs, fal = [], False
    for trig, nm in bases:
        r = pick(trig, 'UNIFORM_CAP15')
        e, ref = r.exec_id, r.policy_reference_exec_id
        ad = dpol(e, 'abs_net_ann_pp')
        d = sv(e, 'D_policy_ann_pp')
        md = dpol(e, 'max_drawdown_total')
        ex = ratio(e, 'exposure_mean', ref)
        sub(subs, 'a_%s' % nm, '%s 绝对净值 D > 0' % nm, ad, None if ad is None else ad > 0)
        sub(subs, 'b_%s' % nm, '%s 缩放超额 D ∈ [−.3, +.3]' % nm, d, inband(d, -0.3, 0.3))
        sub(subs, 'c_%s' % nm, '%s MDD 更深 ≥ .02（本账户 − 参照 ≤ −.02）' % nm, md, None if md is None else md <= -0.02)
        sub(subs, 'd_%s' % nm, '%s 敞口 ≥ 父 × 1.25' % nm, ex, None if ex is None else ex >= 1.25)
        fal |= d is not None and d > 0.5
    out['CC-E6r-06'] = (judge(subs, fal), subs, 'abs_net_ann_pp 差、D_policy_ann_pp、max_drawdown_total 差、exposure_mean 比',
                        '增加已有 alpha 资本也会增加 scaled excess（plan 读法）；不是"只 beta"或"隐藏加码信息"二分')
    # CC-07 GATE_1E8 × REARM LEVEL H30
    subs = []
    r = pick('T1b_LEVEL', 'FLAT', '30', 'GATE_REARM_1E8')
    e = r.exec_id
    nox = r.noexit_same_overlay_exec_id
    c5, c1 = curve(e, 'NOEXIT_SAME_OVERLAY', nox, 5e8), curve(e, 'NOEXIT_SAME_OVERLAY', nox, 1e8)
    nat = r.native_same_trigger_flat_exec_id
    ga, gb = sv(e, 'gross_ann_pp'), sv(nat, 'gross_ann_pp')
    gd = (ga - gb) if (ga is not None and gb is not None) else None
    sub(subs, 'a', '5 亿 curve 对同臂父（无退出父）净差 ≥ 2.28', c5, ge(c5, 2.28))
    sub(subs, 'b', '1 亿 ≥ 4.5', c1, ge(c1, 4.5))
    sub(subs, 'c', 'gross D 对 NATIVE ≥ −2.0', gd, ge(gd, -2.0))
    out['CC-E6r-07'] = (judge(subs, (c5 is not None and c5 < 2.0) or (gd is not None and gd < -3.0)), subs,
                        'cost_curve NOEXIT_SAME_OVERLAY 5 / 1 亿；gross 对 NATIVE_SAME_TRIGGER_FLAT；compound GATE_X_REARM_1E8', '与 E06 / E07 同对象不同带，分别评')
    # CC-08 LEVEL ∨ T8
    subs, fal = [], False
    t8 = G.get('t8_share')
    up = 0.4 if (t8 is not None and t8 > 0.5) else 0.8
    for H in ('20', '30'):
        r = pick('UNION_LEVEL_T8', 'FLAT', H)
        lv = pick('T1b_LEVEL', 'FLAT', H)
        a, b = sv(r.exec_id, 'net_ann_pp'), sv(lv.exec_id, 'net_ann_pp')
        d = (a - b) if (a is not None and b is not None) else None
        tr = ratio(r.exec_id, 'turnover_ann', lv.exec_id)
        sub(subs, 'a_H%s' % H, 'H%s 对 LEVEL 同 H NATIVE net D ∈ [0, %.1f]（T8 在 LEVEL 坏态份额 %s → 上端）' % (H, up, 'NA' if t8 is None else '%.3f' % t8), d, inband(d, 0.0, up))
        sub(subs, 'b_H%s' % H, 'H%s 年换手 ≤ LEVEL × 1.1' % H, tr, None if tr is None else tr <= 1.1)
        fal |= d is not None and d < -0.2
    out['CC-E6r-08'] = (judge(subs, fal), subs, 'E04 / E05 同对象 net D + BASE_RATE_T8_IN_LEVEL_BAD_SHARE（S0-B）+ turnover_ann 比',
                        'S0 overlap 条件化上端保持原 if 函数（> .5 → +.4）；T1a 的 22.6% 重叠不借给 LEVEL')
    # CC-09 T1a 时点 × LEVEL 排名
    subs = []
    r = pick('T1A_TIME_LEVEL_RANK')
    gd = comp_D('TIME_LEVEL_RANK_VS_T1A', r.exec_id, 'D_gross_ann_pp')
    c5 = comp_D('TIME_LEVEL_RANK_VS_T1A', r.exec_id, 'D_cost_5e8_ann_pp')
    sub(subs, 'a', '对 T1a NATIVE FULL gross D ∈ [0, +.5]', gd, inband(gd, 0.0, 0.5))
    sub(subs, 'b', '5 亿净差 ≥ 0', c5, ge(c5, 0.0))
    alias = G.get('alias')
    out['CC-E6r-09'] = (judge(subs, gd is not None and gd < -0.2), subs, 'comparison TIME_LEVEL_RANK_VS_T1A 的 D_gross 与 D_cost_5e8；S0-C GW07',
                        '时点 × 排名别名核：%s%s' % (alias or 'UNKNOWN', '（无新独立检验）' if alias == 'ALIAS_OF_SOURCE' else ''))
    return out


# ------------------------------------------------------------------ Q
QDEF = {
    'Q01': ('diagnostics/G1_E6r.csv', 'block=GW01|item=BAD_minus_GOOD|stat=diff_bp', lambda: g1v('GW01', 'BAD_minus_GOOD', 'diff_bp')),
    'Q02': ('statistics/account_summary_E6r.csv', 'GATE_STATE LEVEL H20 FULL gross_D_policy', lambda: dpol(pick('T1b_LEVEL', 'GATE_STATE').exec_id, 'gross_ann_pp')),
    'Q03': ('statistics/account_summary_E6r.csv', 'TILT_CVR_L050 LEVEL H20 FULL D_policy', lambda: sv(pick('T1b_LEVEL', 'TILT_CVR_L050').exec_id, 'D_policy_ann_pp')),
    'Q04': ('statistics/comparison_results_E6r.csv', 'DOSE_L050_MINUS_L025 LEVEL H20 FULL D_net', lambda: comp_D('DOSE_L050_MINUS_L025', pick('T1b_LEVEL', 'TILT_CVR_L050').exec_id)),
    'Q05': ('statistics/account_summary_E6r.csv', 'DROP_T3 LEVEL H20 FULL D_policy', lambda: sv(pick('T1b_LEVEL', 'DROP_T3').exec_id, 'D_policy_ann_pp')),
    'Q06': ('statistics/account_summary_E6r.csv', 'TILT_H LEVEL H20 FULL D_policy', lambda: sv(pick('T1b_LEVEL', 'TILT_H').exec_id, 'D_policy_ann_pp')),
    'Q07': ('statistics/account_summary_E6r.csv', 'UNIFORM_CAP15 LEVEL H20 FULL abs D', lambda: dpol(pick('T1b_LEVEL', 'UNIFORM_CAP15').exec_id, 'abs_net_ann_pp')),
    'Q08': ('statistics/account_summary_E6r.csv', 'TILT_CVR_L050 − TILT_SIZE_L050 LEVEL H20 FULL gross', lambda: diff2(pick('T1b_LEVEL', 'TILT_CVR_L050').exec_id,
                                                                                                                      pick('T1b_LEVEL', 'TILT_SIZE_L050').exec_id, 'gross_ann_pp')),
    'Q09': ('statistics/comparison_results_E6r.csv', 'ADAPTATION_VS_RAW20_TILT（CVR5）LEVEL H20 FULL D_net', lambda: comp_D('ADAPTATION_VS_RAW20_TILT', pick('T1b_LEVEL', 'TILT_CVR5_L050').exec_id)),
    'Q10': ('statistics/compound_results_E6r.csv', 'GATE_X_TILT 首个 contrast FULL I_net', lambda: cpd('GATE_X_TILT')),
    'Q11': ('statistics/compound_results_E6r.csv', 'ENTRY_X_EXIT_GATE 首个 contrast FULL I_net', lambda: cpd('ENTRY_X_EXIT_GATE')),
    'Q12': ('statistics/compound_results_E6r.csv', 'GATE_X_REARM_1E8 首个 contrast FULL I_net', lambda: cpd('GATE_X_REARM_1E8')),
    'Q13': ('reports/e_results_E6r.csv', 'E04 value', lambda: G.get('E04')),
    'Q14': ('diagnostics/stage0_E6r.csv', 'S0-C TIME_LEVEL_RANK_ALIAS', lambda: None),
    'Q15': ('statistics/comparison_results_E6r.csv', 'H40_MINUS_H30_SAME_RULE 首条 FULL D_net', lambda: comp_first('H40_MINUS_H30_SAME_RULE')),
    'Q16': ('statistics/weights_E6r.csv', 'TILT_CVR_L050 LEVEL H20 FORMATION FULL transfer_share_mean', lambda: wv(pick('T1b_LEVEL', 'TILT_CVR_L050').exec_id)),
    'Q17': ('diagnostics/G1_E6r.csv', 'block=GW02|item=label_agreement', lambda: g1v('GW02', 'label_agreement', 'share')),
    'Q18': ('registration/park_E6r.csv', 'park 台账（P62 / P69 / P74–P83）', lambda: None)}


def g1v(block, item, stat):
    D = G['g1']
    x = D[(D.block == block) & (D.item == item) & (D.stat == stat)] if len(D) else D
    return f(x.value.iloc[0]) if len(x) else None


def diff2(a, b, col):
    x, y = sv(a, col), sv(b, col)
    return (x - y) if (x is not None and y is not None) else None


def cpd(kind):
    K = G['cpd']
    x = K[(K.kind == kind) & (K.segment == 'FULL')] if len(K) else K
    return f(x.I_net_ann_pp.iloc[0]) if len(x) else None


def comp_first(kind):
    C = G['cmp']
    x = C[C.kind == kind]
    if not len(x):
        return None
    r = G['cr'].get((x.comparison_id.iloc[0], 'FULL'))
    return f(r.D_net_ann_pp) if r is not None else None


def wv(e):
    W = G['w']
    x = W[(W.exec_id == e) & (W.layer == 'FORMATION') & (W.segment == 'FULL')] if len(W) else W
    return f(x.transfer_share_mean.iloc[0]) if len(x) else None


# ------------------------------------------------------------------ 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    G['root'] = O.P(*a.root.split('/')) if a.root else O.work()
    R = O.read_csv(O.P('registration', 'registry_E6r.csv'))
    G['R'] = R
    G['reg'] = R.set_index('exec_id', drop=False)
    G['lid2e'] = dict(zip(R.logical_id, R.exec_id))
    AS = rd('statistics/account_summary_E6r.csv')
    G['sm'] = {(r.exec_id, r.segment): r for r in AS.itertuples(index=False)}
    CC = rd('statistics/cost_curve_E6r.csv')
    G['cc'] = {(r.exec_id, r.comparator_kind, r.comparator_exec_id, int(float(r.A_cny)), f(r.kappa), f(r.exponent), r.segment): f(r.net_after_impact_diff_ann_pp)
               for r in CC.itertuples(index=False) if r.status == 'COMPUTED' and f(r.kappa) == 0.5 and f(r.exponent) == 0.5}
    RD = rd('statistics/randoms_E6r.csv')
    G['rd'] = {(r.ref_id, r.segment): r for r in RD.itertuples(index=False)} if len(RD) else {}
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6r.csv'))
    G['rref'] = {(r.owner_exec_id, r.mechanism): r.ref_id for r in RR.itertuples(index=False)}
    G['cmp'] = O.read_csv(O.P('registration', 'comparisons_E6r.csv'))
    CR = rd('statistics/comparison_results_E6r.csv')
    G['cr'] = {(r.comparison_id, r.segment): r for r in CR.itertuples(index=False)}
    G['cpd'] = rd('statistics/compound_results_E6r.csv')
    G['w'] = rd('statistics/weights_E6r.csv')
    G['g1'] = rd('diagnostics/G1_E6r.csv') if os.path.exists(os.path.join(G['root'], 'diagnostics', 'G1_E6r.csv')) else \
        pd.read_csv(O.P('diagnostics', 'G1_E6r.csv'), dtype=str, keep_default_na=False)
    st0 = pd.concat([pd.read_csv(p, dtype=str, keep_default_na=False) for p in (O.P('diagnostics', 'stage0_E6r_part1.csv'), O.P('diagnostics', 'stage0_E6r_part2.csv'))
                     if os.path.exists(p)], ignore_index=True)
    t8 = st0[st0.key == 'BASE_RATE_T8_IN_LEVEL_BAD_SHARE']
    G['t8_share'] = f(t8.value.iloc[0]) if len(t8) else None
    al = st0[st0.key == 'TIME_LEVEL_RANK_ALIAS']
    G['alias'] = al.value.iloc[0] if len(al) else None
    E_, ES = e_block()
    G['E04'] = f(E_[E_.e_id == 'E04'].value.iloc[0]) if (E_.e_id == 'E04').any() else None
    CCR = cc_block()
    rows, qreg = [], {}

    def reg(qid, table, filt, n=''):
        qreg.setdefault(qid, dict(query_id=qid, table=table, filter=filt, n_rows=n, generator='e6r_claims.py'))
    # Q
    LQ = O.read_csv(O.P('registration', 'ledger_Q_E6r.csv'))
    for r in LQ.itertuples(index=False):
        table, filt, fn = QDEF[r.q_id]
        v = fn()
        if r.q_id == 'Q14':
            v = None
            note = 'TIME_LEVEL_RANK_ALIAS = %s' % (G['alias'] or 'UNKNOWN')
        else:
            note = ''
        rows.append(dict(claim_id=r.q_id, kind='Q', author=r.author, statement=r.statement_verbatim, query_id='QRY-%s' % r.q_id, table=table, exec_ids='',
                         result_value='' if v is None else v, result_sign='' if v is None else ('+' if v > 0 else ('−' if v < 0 else '0')), ci_lo='', ci_hi='',
                         claim_status='开放', working_range='', note=note or '开放问题卡：全部计算、只报，不打经济 HIT'))
        reg('QRY-%s' % r.q_id, table, filt)
    # E
    for r in E_.itertuples(index=False):
        rows.append(dict(claim_id=r.e_id, kind='E', author='PLAN', statement='%s：owner − reference（%s，FULL）；带 [%s, %s]（上端开放）' % (r.e_id, r.statistic, r.lower, r.upper),
                         query_id=r.query_id, table='reports/e_results_E6r.csv', exec_ids='%s;%s' % (r.owner_exec_id, r.reference_exec_id), result_value=r.value,
                         result_sign='' if r.value == '' else ('+' if float(r.value) > 0 else '−'), ci_lo='', ci_hi='', claim_status=r.status, working_range=r.working_range,
                         note='plan score_e；越上端另记 ABOVE_WORKING_RANGE，不否认方向支持'))
        reg(r.query_id, 'reports/e_results_E6r.csv', 'e_id=%s' % r.e_id, 1)
    # G
    LG = O.read_csv(O.P('registration', 'ledger_G_E6r.csv'))
    for r in LG.itertuples(index=False):
        stt = r.state if r.state in ('PRESPECIFIED_DISCRIMINATING_TEST', 'SUPPORTED_DERIVATION', 'NOT_YET_SUPPORTED') else 'NOT_EVALUABLE'
        qid = 'QRY-G1-%s' % r.g_id.replace('-', '')
        rows.append(dict(claim_id=r.g_id, kind='G', author=r.author, statement=r.statement_verbatim, query_id=qid, table='diagnostics/G1_E6r.csv', exec_ids='',
                         result_value='', result_sign='', ci_lo='', ci_hi='', claim_status=stt, working_range='',
                         note='第一道标签（%s）；exposed_window = %s；不进 E 命中率' % (r.state, r.exposed_window)))
        reg(qid, 'diagnostics/G1_E6r.csv', 'block=%s' % r.g_id)
    # CC
    CCC = O.read_csv(O.P('registration', 'cc_statement_carry.csv'))
    for i, r in CCC.iterrows():
        st, subs, comp, note = CCR[r.statement_id]
        CCC.at[i, 'plan_reading'] = note
        CCC.at[i, 'estimand_note'] = comp
        CCC.at[i, 'comparable'] = 'true' if st != 'NOT_EVALUABLE' else 'false'
        CCC.at[i, 'claim_status'] = st
        CCC.at[i, 'sub_claims'] = json.dumps(subs, ensure_ascii=False, sort_keys=True)
        qid = 'QRY-%s' % r.statement_id
        rows.append(dict(claim_id=r.statement_id, kind='CC', author='DECISION', statement=r.verbatim.strip()[:400], query_id=qid, table='statistics/account_summary_E6r.csv',
                         exec_ids='', result_value='', result_sign='', ci_lo='', ci_hi='', claim_status=st, working_range='', note=note))
        reg(qid, 'statistics/*', comp)
        for s_ in subs:
            sid = '%s%s' % (r.statement_id, s_['id'])
            rows.append(dict(claim_id=sid, kind='CC_SUB', author='DECISION', statement=s_['text'], query_id=qid, table='statistics/*', exec_ids='',
                             result_value=s_['value'], result_sign='' if s_['value'] == '' else ('+' if float(s_['value']) > 0 else '−'), ci_lo='', ci_hi='',
                             claim_status={'PASS': '支持', 'FAIL': '不支持', 'NA': 'NOT_EVALUABLE'}[s_['result']], working_range='', note='子条款（句级状态另见 %s）' % r.statement_id))
    CL = pd.DataFrame(rows, columns=['claim_id', 'kind', 'author', 'statement', 'query_id', 'table', 'exec_ids', 'result_value', 'result_sign', 'ci_lo', 'ci_hi',
                                     'claim_status', 'working_range', 'note'])
    # 其余表里出现的 query_id（政策字段 / G1 / D 表 / 依赖账）一并登记
    for rel in ['statistics/policy_fields_E6r.csv', 'diagnostics/G1_E6r.csv'] + ['diagnostics/%s' % os.path.basename(p) for p in
                                                                                 glob.glob(os.path.join(G['root'], 'diagnostics', 'D*_E6r.csv'))]:
        T_ = rd(rel) if os.path.exists(os.path.join(G['root'], rel)) else (pd.read_csv(O.P(*rel.split('/')), dtype=str, keep_default_na=False)
                                                                           if os.path.exists(O.P(*rel.split('/'))) else pd.DataFrame())
        if len(T_) and 'query_id' in T_.columns:
            for qid, g in T_.groupby('query_id'):
                if qid:
                    reg(qid, rel, 'query_id=%s' % qid, len(g))
    QR = pd.DataFrame(list(qreg.values()), columns=['query_id', 'table', 'filter', 'n_rows', 'generator'])
    # 反思记录（E 7 + G 12 + CC 9）
    fz = json.load(open(O.P('registration', 'freeze_E6r.json'), encoding='utf-8'))
    ref_rows = []
    for r in E_.itertuples(index=False):
        ref_rows.append(dict(item_id=r.e_id, author='PLAN', statement='%s %s 带 [%s, %s]' % (r.e_id, r.statistic, r.lower, r.upper), visible_at_time='2026-10-23T23:38:25+00:00 登记；A1 冻结',
                             decision_to_change='无（方式 B 中途不改）', registered_object='%s vs %s' % (r.owner_exec_id.split('|')[0], r.reference_exec_id.split('|')[0]),
                             executed_object='同登记对象', query_and_estimator='%s；plan score_e' % r.query_id, support_points='value = %s；%s；%s' % (r.value, r.status, r.working_range),
                             strongest_unexcluded_explanation='见 REVIEW（执行端只报读数，不作解释性结论）', next_round_change='由决策端 REVIEW 定',
                             park_or_restore='', prediction_version='claims.json（plan v1.1）', derived_from='E6q REVIEW v1.1 依赖（G.2）', first_measurement_at=fz['written_at'],
                             plan_sha256=O.PLAN_SHA256))
    for r in LG.itertuples(index=False):
        ref_rows.append(dict(item_id=r.g_id, author=r.author, statement=r.statement_verbatim, visible_at_time=r.exposed_window, decision_to_change='无（只打标签）',
                             registered_object=r.tested_estimand, executed_object='同登记', query_and_estimator='QRY-G1-%s' % r.g_id.replace('-', ''),
                             support_points=r.state, strongest_unexcluded_explanation=r.explanation_scope[:300], next_round_change='由决策端 REVIEW 定', park_or_restore='',
                             prediction_version='ledger_G（A1 冻结）', derived_from=r.derived_from, first_measurement_at='A2 推导段（S0-C）', plan_sha256=O.PLAN_SHA256))
    for i, r in CCC.iterrows():
        ref_rows.append(dict(item_id=r.statement_id, author='DECISION', statement=r.verbatim.strip()[:300], visible_at_time='proposal v1.2（%s）' % r.source_sha256[:16],
                             decision_to_change='无（原句不改）', registered_object=r.estimand_note, executed_object='同 plan 读法', query_and_estimator='QRY-%s' % r.statement_id,
                             support_points=r.claim_status, strongest_unexcluded_explanation='见 REVIEW', next_round_change='由决策端 REVIEW 定', park_or_restore='',
                             prediction_version='proposal v1.2 L%s' % r.source_line, derived_from='CC 模板 v10', first_measurement_at='B 相（%s）' % fz['written_at'][:10],
                             plan_sha256=O.PLAN_SHA256))
    RF = pd.DataFrame(ref_rows)
    # 账本回填
    LE = O.read_csv(O.P('registration', 'ledger_E_E6r.csv'))
    em = E_.set_index('e_id')
    for i, r in LE.iterrows():
        LE.at[i, 'state'] = em.loc[r.e_id, 'status']
        LE.at[i, 'result_query'] = 'QRY-%s' % r.e_id
        LE.at[i, 'result_row'] = 'reports/e_results_E6r.csv|e_id=%s' % r.e_id
    for i, r in LQ.iterrows():
        LQ.at[i, 'state'] = '开放'
        LQ.at[i, 'result_row'] = 'reports/claims_E6r.csv|claim_id=%s' % r.q_id
    root = G['root']
    outs = {'reports/e_results_E6r.csv': E_, 'reports/e_summary_E6r.csv': ES, 'reports/claims_E6r.csv': CL, 'reports/query_registry_E6r.csv': QR,
            'reports/reflection_E6r.csv': RF}
    paths = []
    for rel, df in outs.items():
        p = os.path.join(root, *rel.split('/'))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        O.atomic_write_csv(p, df)
        paths.append(p)
    if root == O.work():
        for rel, df in (('registration/ledger_E_E6r.csv', LE), ('registration/ledger_Q_E6r.csv', LQ), ('registration/cc_statement_carry.csv', CCC)):
            O.atomic_write_csv(O.P(*rel.split('/')), df)
            paths.append(O.P(*rel.split('/')))
    else:
        for rel, df in (('registration/ledger_E_E6r.csv', LE), ('registration/ledger_Q_E6r.csv', LQ), ('registration/cc_statement_carry.csv', CCC)):
            p = os.path.join(root, *rel.split('/'))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            O.atomic_write_csv(p, df)
            paths.append(p)
    facts = dict(e=E_.status.value_counts().to_dict(), cc={k: v[0] for k, v in CCR.items()}, claims=len(CL), queries=len(QR), reflection=len(RF))
    O.atomic_write_json(os.path.join(root, 'reports', 'claims_facts_E6r.json'), facts)
    O.write_receipt('E6r_claims', paths, code=[__file__, O.__file__], claims=len(CL), queries=len(QR))
    print(json.dumps(facts, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
