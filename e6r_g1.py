# -*- coding: utf-8 -*-
"""E6r S0-C 第一道（brief §2 / A-C；plan §3）：只推导段收益（return_end ≤ 2018-12-31；窗尾不足完整 q → RIGHT_CENSORED，不用后段补）。
- G-P-01…04：F1 §3.5 三张表与量级原算式 = 从 E6q 交付机器表原样复刻（D3 = DERIV；landmark / D4 / 统计 = FULL_SEEN），印出值按小数位容差对照；
  G-P-04 原式照录 + plan R05 的 λ/3 修正并列。
- GW01–GW08（plan §3 原文）：在 E6r A2 产物上新测（主坐标 A4b_CVRv5 × HG10 × FEASIBLE × H20；FLAT NONE 常规批次为入场样本）。
状态只打标签（PRESPECIFIED_DISCRIMINATING_TEST / NOT_YET_SUPPORTED / SUPPORTED_DERIVATION / NOT_COMPUTABLE），不选支、不改名单、不删账户。
输出：diagnostics/G1_E6r.csv（B.23 长格式）、diagnostics/stage0_E6r_part2.csv（S0-C 行：每个 GW 的 RETURN_END_MAX、TIME_LEVEL_RANK_ALIAS、S0-B 结构基准率）、
verify/identities_E6r_g1.csv（T0_NOT_AGE1）、registration/ledger_G_E6r.csv（state / result_query / result_row 回填）。用法：python3 e6r_g1.py"""
import os
import json
import time

import numpy as np
import pandas as pd

import e6r_core as O
import e6r_engine as E
import e6r_acct as A

LCOLS = ['block', 'item', 'key1', 'key2', 'segment', 'stat', 'value', 'unit', 'n', 'status', 'query_id']
DEND = '2018-12-31'
ROWS, ST0, IDN = [], [], []
G = {}
LAB = {'SUPPORTED_DERIVATION', 'NOT_YET_SUPPORTED', 'PRESPECIFIED_DISCRIMINATING_TEST', 'NOT_COMPUTABLE'}


def L(block, item, key1, key2, segment, stat, value, unit, n='', status='COMPUTED', q=''):
    if isinstance(value, float) and not np.isfinite(value):
        value, status = '', ('UNKNOWN' if status == 'COMPUTED' else status)
    ROWS.append(dict(block=block, item=item, key1=key1, key2=key2, segment=segment, stat=stat, value=value, unit=unit, n=n, status=status,
                     query_id=q or 'QRY-G1-%s' % block))


def label(block, lab, rule):
    assert lab in LAB
    L(block, 'g_label', lab, rule, 'DERIV_2010_2018' if block.startswith('GW') or block == 'G-P-01' else 'FULL_SEEN', 'label', lab, 'none', status='INFO')
    G.setdefault('labels', {})[block] = (lab, rule)


def put(probe, item, key, value, unit='count', status='INFO', source_file='', note=''):
    if isinstance(value, float) and not np.isfinite(value):
        value, status = '', 'UNKNOWN'
    ST0.append(dict(probe_id=probe, item=item, key=key, value=value, unit=unit, status=status, source_file=source_file, note=note))


# ------------------------------------------------------------------ 公共
def setup():
    cd = O.cache_dir()
    P = lambda k: np.load(os.path.join(cd, 'panels', k + '.npy'), mmap_mode='r')
    G['cd'] = cd
    G['dates'] = np.load(os.path.join(cd, 'panels', 'dates.npy'))
    G['T'] = len(G['dates'])
    G['d19'] = int(np.searchsorted(G['dates'], '2019-01-01'))
    G['last'] = G['d19'] - 1
    G['pv'] = P('pv_ff')
    G['pc'] = P('pc_ff')
    G['zsize'] = P('zsize')
    G['iskid'] = P('iskid')
    G['ind'] = P('ind')
    G['cumbench'] = np.cumprod(1.0 + np.nan_to_num(np.load(os.path.join(cd, 'panels', 'bench.npy')).astype(float)))
    mk = A.Market()
    G['mk'] = mk
    G['cvr20'] = np.asarray(mk.cvr20)
    G['cvr5'] = np.asarray(mk.cvr5)
    G['lvl'] = np.asarray(mk.lvl)
    G['R'] = O.read_csv(O.P('registration', 'registry_E6r.csv'))
    G['f'] = mk.formation(O.MAIN_FORM, 'HG10')
    G['ov'] = np.load(os.path.join(cd, 'overlay', '%s|HG10.npz' % O.MAIN_FORM), allow_pickle=False)


def pick(trig='NONE', scheme='FLAT', H='20', exit_op='NATIVE', form=O.MAIN_FORM, mem='HG10', scen=O.FEAS):
    R = G['R']
    x = R[(R.trigger == trig) & (R.weight_scheme == scheme) & (R.funding_H == H) & (R.exit_op == exit_op) & (R.form == form) & (R.memory == mem) & (R.scenario == scen)]
    return x.iloc[0] if len(x) else None


def trades(h):
    z = np.load(O.P('trades_parts', 'deriv', h[:2], '%s.npz' % h), allow_pickle=False)
    return z['TL_i'], z['TL_f']


def acct(h):
    return np.load(O.P('accounts_run', 'deriv', h[:2], '%s.npz' % h), allow_pickle=False)


def lots_frame(ti, tf):
    """常规批次买入 → 批次（e0 = 买入日、sec、qty、due）；卖出合计 ≥ qty 的批次记关闭日 cl（未关闭 = −1）。"""
    b = (ti[:, 5] == 0) & (ti[:, 4] == E.OK_REGULAR)
    lots = pd.DataFrame(dict(lot=ti[b, 2], sec=ti[b, 1], e0=ti[b, 0], qty=tf[b, 0], due=ti[b, 6], nt=tf[b, 1])).groupby('lot', as_index=False).agg(
        sec=('sec', 'first'), e0=('e0', 'min'), qty=('qty', 'sum'), due=('due', 'max'), nt=('nt', 'sum'))
    s = ti[:, 5] == 1
    sells = pd.DataFrame(dict(lot=ti[s, 2], day=ti[s, 0], qty=tf[s, 0]))
    last = sells.groupby('lot').agg(close_day=('day', 'max'), sold=('qty', 'sum'))
    lots = lots.merge(last, left_on='lot', right_index=True, how='left')
    closed = lots.sold.fillna(0).to_numpy() >= lots.qty.to_numpy() * (1 - 1e-9)
    lots['cl'] = np.where(closed, lots.close_day.fillna(-1), -1).astype(np.int64)
    return lots


def fwd(sec, d0, q, last=None):
    """前向超额：VWAP(d0) → VWAP(d0 + q)（后复权）减同窗口 clean 等权基准；终点 > last（推导段末）→ NaN（右删失，不用后段补）。"""
    last = G['last'] if last is None else last
    pv, cb = G['pv'], G['cumbench']
    d0 = np.asarray(d0, np.int64)
    sec = np.asarray(sec, np.int64)
    d1 = d0 + np.asarray(q, np.int64)
    cens = d1 > last
    a = np.minimum(d0, last)
    b = np.minimum(d1, last)
    with np.errstate(all='ignore'):
        x = (np.asarray(pv[b, sec], float) / np.asarray(pv[a, sec], float) - 1.0) - (cb[b] / cb[a] - 1.0)
    return np.where(cens, np.nan, x), cens


def by_day(day):
    o = np.argsort(day, kind='stable')
    ds = day[o]
    cut = np.flatnonzero(np.r_[True, ds[1:] != ds[:-1], True])
    return [(int(ds[a]), o[a:b]) for a, b in zip(cut[:-1], cut[1:])]


def day_se(x, d):
    if len(x) < 2:
        return np.nan
    g = pd.DataFrame(dict(d=d, x=x)).groupby('d').x.mean().to_numpy()
    return float(np.std(g, ddof=1) / np.sqrt(len(g))) if len(g) > 1 else np.nan


def entry_index(e0, sec):
    """入场批次 (e0, sec) → 形成日 T0 = e0 − 1 的形成名单位置 k（CSR；名单外 = −1）。"""
    ptr, col, w = G['f']
    out = np.full(len(e0), -1, np.int64)
    for i, (d, s) in enumerate(zip(e0 - 1, sec)):
        if d < 0:
            continue
        a, b = ptr[d], ptr[d + 1]
        k = a + np.searchsorted(col[a:b], s)
        if k < b and col[k] == s:
            out[i] = k
    return out


def tert_domain(Xp, T0, sec, domain='cohort'):
    """形成日 T0 的三分位标签（tie-aware 中点秩：< 1/3 T1、> 2/3 T3；有限值 < 3 → NA）：domain = cohort（当日最终形成名单）/ source（当日全部有值证券 = 源域）。"""
    ptr, col, w = G['f']
    lab = np.zeros(len(T0), np.int64)
    for d, idx in by_day(T0):
        if d < 0:
            continue
        if domain == 'cohort':
            dom = np.asarray(Xp[d, col[ptr[d]:ptr[d + 1]]], float)
        else:
            dom = np.asarray(Xp[d], float)
        v = np.sort(dom[np.isfinite(dom)])
        if len(v) < 3 or v[0] == v[-1]:
            continue
        x = np.asarray(Xp[d, sec[idx]], float)
        lo = np.searchsorted(v, x, 'left')
        hi = np.searchsorted(v, x, 'right')
        p = (lo + 0.5 * (hi - lo)) / len(v)
        lab[idx] = np.where(np.isfinite(x), np.where(p < 1 / 3.0, 1, np.where(p > 2 / 3.0, 3, 2)), 0)
    return lab


def spread_rows(block, item, lab, x, d, w=None, tags=('T1', 'T2', 'T3'), seg='DERIV_2010_2018', q=''):
    """三分位均值（等权；w 给定时另报资本加权）与 T1 − T3（等权差 + 日聚类 se）。"""
    out = {}
    for k, t in enumerate(tags, start=1):
        m = (lab == k) & np.isfinite(x)
        mu = float(x[m].mean() * 1e4) if m.any() else np.nan
        out[t] = (mu, m)
        L(block, item, t, 'equal', seg, 'mean_bp', mu, 'bp', int(m.sum()), q=q)
        if w is not None and m.any():
            ww = w[m]
            L(block, item, t, 'capital', seg, 'mean_bp', float((x[m] * ww).sum() / ww.sum() * 1e4) if ww.sum() > 0 else np.nan, 'bp', int(m.sum()), q=q)
    m1, m3 = out['T1'][1], out['T3'][1]
    dif = out['T1'][0] - out['T3'][0]
    # 日聚类差的 se：逐日 T1 − T3 均值差的跨日 se
    if m1.any() and m3.any():
        a = pd.DataFrame(dict(d=d[m1], x=x[m1])).groupby('d').x.mean()
        b = pd.DataFrame(dict(d=d[m3], x=x[m3])).groupby('d').x.mean()
        j = a.index.intersection(b.index)
        dd = (a.loc[j] - b.loc[j]).to_numpy()
        se = float(np.std(dd, ddof=1) / np.sqrt(len(dd)) * 1e4) if len(dd) > 1 else np.nan
    else:
        se = np.nan
    L(block, item, 'T1_minus_T3', 'equal', seg, 'diff_bp', dif, 'bp', int(m1.sum() + m3.sum()), q=q)
    L(block, item, 'T1_minus_T3', 'equal', seg, 'day_cluster_se_bp', se, 'bp', q=q)
    return dif, se


# ------------------------------------------------------------------ G-P（E6q 交付机器表原样复刻）
PRINTED_T1 = {('CVR20_risk', 1): (40.6, 26.6, 16.9), ('CVR20_risk', 5): (19.2, 17.0, 18.1), ('CVR20_risk', 10): (17.9, 16.5, 16.6),
              ('size', 1): (37.7, 26.9, 19.7), ('size', 5): (28.0, 17.2, 9.0), ('size', 10): (25.4, 12.6, 12.7),
              ('K_strength', 1): (22.1, 33.2, 29.5), ('K_strength', 5): (16.8, 17.2, 20.4), ('K_strength', 10): (14.3, 17.7, 19.1),
              ('K0_raw', 1): (29.2, 33.0, 22.4), ('K0_raw', 5): (20.1, 17.0, 17.1), ('K0_raw', 10): (18.3, 18.6, 14.1)}
PRINTED_Q10 = {'CVR20_risk': (23.3, 2.1, 8.1), 'size': (36.2, 30.7, 28.6)}


def e6q_table(rel):
    p = O.E6Q('handoff', 'E6q_20261023_1032', rel)
    if not os.path.exists(p):
        p = os.path.join(O.E6Q_HANDOFF, rel)
    return pd.read_csv(p, dtype=str, keep_default_na=False)


def gp01():
    D = e6q_table('diagnostics/D3_entry_persistence_E6q.csv')
    tg = 'NATIVE|NONE|H20|main|HG10'
    worst = 0.0
    n = 0
    for (nm, a), pr in PRINTED_T1.items():
        for k, t in enumerate(('T1', 'T2', 'T3')):
            x = D[(D.item == 'fwd_excess_q5') & (D.key1 == nm) & (D.key2 == 'age%d' % a) & (D.stat == '%s|%s|mean_bp' % (tg, t))]
            v = float(x.value.iloc[0]) if len(x) else np.nan
            L('G-P-01', 'fwd_excess_q5', nm, 'age%d|%s' % (a, t), 'DERIV_2010_2018', 'e6q_machine_bp', v, 'bp', x.n.iloc[0] if len(x) else '',
              q='QRY-G1-GP01')
            L('G-P-01', 'fwd_excess_q5', nm, 'age%d|%s' % (a, t), 'DERIV_2010_2018', 'printed_bp', pr[k], 'bp', status='INFO', q='QRY-G1-GP01')
            if np.isfinite(v):
                worst = max(worst, abs(v - pr[k]))
                n += 1
    for nm, pr in PRINTED_Q10.items():                   # 印出的 q10 行 = T1 − T3 价差在 age1 / 5 / 10（例：56.8 − 33.5 = 23.3）
        for k, a in enumerate((1, 5, 10)):
            vv = {}
            for t in ('T1', 'T3'):
                x = D[(D.item == 'fwd_excess_q10') & (D.key1 == nm) & (D.key2 == 'age%d' % a) & (D.stat == '%s|%s|mean_bp' % (tg, t))]
                vv[t] = float(x.value.iloc[0]) if len(x) else np.nan
            v = vv['T1'] - vv['T3']
            L('G-P-01', 'fwd_excess_q10_T1_minus_T3', nm, 'age%d' % a, 'DERIV_2010_2018', 'e6q_machine_bp', v, 'bp', q='QRY-G1-GP01')
            L('G-P-01', 'fwd_excess_q10_T1_minus_T3', nm, 'age%d' % a, 'DERIV_2010_2018', 'printed_bp', pr[k], 'bp', status='INFO', q='QRY-G1-GP01')
            if np.isfinite(v):
                worst = max(worst, abs(v - pr[k]))
                n += 1
    L('G-P-01', 'print_tolerance_check', 'max_abs_diff_vs_printed_1dp', '', 'DERIV_2010_2018', 'bp', worst, 'bp', n, status='INFO', q='QRY-G1-GP01')
    label('G-P-01', 'SUPPORTED_DERIVATION' if n == 42 and worst < 0.1 else 'NOT_YET_SUPPORTED',
          '42 个印出格与 E6q D3 机器值之差都小于末位一个单位（印出 1 位小数，四舍五入或截断都覆盖） → SUPPORTED_DERIVATION（复刻成立）；否则 NOT_YET_SUPPORTED')


def gp02():
    """表 2：LEVEL / T1a / NONE H20 NATIVE（E6q 同坐标 = E6r FLAT 复现锚）的 landmark：age1 坏状态份额、坏状态 / 未触发 q5（age 1 / 5 / 10 / 15）、age2 存活。"""
    LM = e6q_table('diagnostics/landmark_E6q.csv')
    D4 = e6q_table('diagnostics/D4_age_delay_E6q.csv')
    printed = {'T1b_LEVEL': (7.9, (-21.0, -6.3, -17.5, -2.5), (33.7, 31.8, 35.1, 32.9), 92.1), 'T1a': (3.0, (-23.4, -63.5, -85.7, -126.4), (31.7, 25.4, 25.1, 25.1), 96.9),
               'NONE': (None, None, (29.6, 21.5, 19.7, 19.2), 99.9)}
    worst = 0.0
    nchk = 0
    for trig, pr in printed.items():
        r = pick(trig)
        e6 = r.replication_exec_id
        x = LM[(LM.exec_id == e6) & (LM.q == '5') & (LM.weighting == 'EQUAL')]
        n1 = x[x.landmark_age == '1']
        tot = sum(float(v) for v in n1.n) if len(n1) else np.nan
        bad = float(n1[n1.state == 'BAD_STATE'].n.iloc[0]) if (len(n1) and (n1.state == 'BAD_STATE').any()) else 0.0
        share = bad / tot * 100.0 if tot and np.isfinite(tot) else np.nan
        L('G-P-02', 'age1_bad_state_share', trig, 'H20|NATIVE', 'FULL', 'pct', share, 'pct', int(tot) if np.isfinite(tot) else '', status='COMPUTED', q='QRY-G1-GP02')
        if pr[0] is not None and np.isfinite(share):
            worst = max(worst, abs(share - pr[0]))
            nchk += 1
        for k, a in enumerate((1, 5, 10, 15)):
            for st, prv in (('BAD_STATE', pr[1]), ('NOT_TRIGGERED', pr[2])):
                y = x[(x.landmark_age == str(a)) & (x.state == st)]
                v = float(y.mean_fwd_excess_bp.iloc[0]) if (len(y) and y.mean_fwd_excess_bp.iloc[0] != '') else np.nan
                L('G-P-02', 'landmark_q5_equal', trig, 'age%d|%s' % (a, st), 'FULL', 'mean_bp', v, 'bp', y.n.iloc[0] if len(y) else '', q='QRY-G1-GP02')
                if prv is not None and np.isfinite(v):
                    worst = max(worst, abs(v - prv[k]))
                    nchk += 1
        a2 = LM[(LM.exec_id == e6) & (LM.q == '5') & (LM.weighting == 'EQUAL') & (LM.landmark_age == '2')]
        n2 = sum(float(v) for v in a2.n) if len(a2) else np.nan
        surv = n2 / tot * 100.0 if (np.isfinite(n2) and tot) else np.nan
        L('G-P-02', 'age2_survival', trig, 'H20|NATIVE', 'FULL', 'pct', surv, 'pct', q='QRY-G1-GP02')
        if np.isfinite(surv):
            worst = max(worst, abs(surv - pr[3]))
            nchk += 1
    L('G-P-02', 'print_tolerance_check', 'max_abs_diff_vs_printed_1dp', '', 'FULL', 'pct_or_bp', worst, 'mixed', nchk, status='INFO', q='QRY-G1-GP02')
    label('G-P-02', 'SUPPORTED_DERIVATION' if worst < 0.1 and nchk >= 20 else 'NOT_YET_SUPPORTED',
          'age1 坏状态份额、坏态 / 未触发 q5 与 age2 存活的印出值（1 位小数）与 E6q landmark 机器值之差都小于末位一个单位（存活印出为截断） → SUPPORTED_DERIVATION；否则 NOT_YET_SUPPORTED（份额 / 存活按 n 计数口径）')
    del D4


def gp03():
    """表 3：第二块 E6q 读数（E6q statistics 表；FULL_SEEN）：门控 1E8 LEVEL H30 曲线 1 / 5 亿、REARM H30、LEVEL_WORST vs T1a、UNION H30、H30 − H20。"""
    vals = [('GATE_1E8_LEVEL_H30_curve_1e8', 4.79), ('GATE_1E8_LEVEL_H30_curve_5e8', 0.73), ('REARM_H30_curve_1e8', 5.38), ('REARM_H30_curve_5e8', 2.58),
            ('LEVEL_WORST_vs_T1a', 3.52 - 3.24), ('UNION_H30', 4.73), ('H30_minus_H20_T1a', 0.33), ('H30_minus_H20_LEVEL', 0.68)]
    for k, v in vals:
        L('G-P-03', 'e6q_second_block', k, 'printed', 'FULL', 'ann_pp', v, 'ann_pp', status='INFO', q='QRY-G1-GP03')
    # 曲线四锚由 S0-A 在 E6r 仪器上重放（verify/curve_replication_E6r.csv）→ 这里只回链
    cr = O.read_csv(O.P('verify', 'curve_replication_E6r.csv'))
    for r in cr.itertuples(index=False):
        L('G-P-03', 'curve_anchor_replay', r.e6r_exec_id.split('|')[0], str(r.A_cny), r.segment, 'e6r_value', float(r.e6r_value), 'ann_pp', status='COMPUTED',
          q='QRY-S0A-CURVE')
    ok = len(cr) == 4 and (cr.status == 'PASS').all()
    label('G-P-03', 'SUPPORTED_DERIVATION' if ok else 'NOT_YET_SUPPORTED', 'E6q 曲线四锚在 E6r 仪器上逐点复现（S0-A）→ SUPPORTED_DERIVATION；其余印出值只回链 E6q 交付表（FULL_SEEN），不作新检验')


def gp04():
    """量级原算式（proposal §3.5）照录 + plan R05 的 λ/3 修正并列（只是带，不是门）。"""
    rows = [('GATE_LEVEL', '13 bp × 6.8% × 7.9% × 240', 13e-4 * 0.068 * 0.079 * 240 * 100, None),
            ('GATE_T1A_NONE', '3.5% × 7.9% × 45 bp × 240', 0.035 * 0.079 * 45e-4 * 240 * 100, None),
            ('TILT_LEVEL', '6.8% × 1/3 × 23.7 bp × 240（原式）', 0.068 / 3 * 23.7e-4 * 240 * 100, 0.068 * (0.5 / 3) * 23.7e-4 * 240 * 100),
            ('TILT_T1A', '3.5% × 1/3 × 23.7 bp × 240（原式）', 0.035 / 3 * 23.7e-4 * 240 * 100, 0.035 * (0.5 / 3) * 23.7e-4 * 240 * 100),
            ('TILT_H', '≈ 0（CVR 在 age5 后无分辨力）', 0.0, None), ('UNIFORM_CAP15', '绝对 +（敞口 × 单位敞口 alpha ≈ 12）；缩放超额 ± .3', np.nan, None)]
    for k, f, v, vc in rows:
        L('G-P-04', 'magnitude_formula', k, f, 'FULL', 'ann_pp_original', v, 'ann_pp', status='INFO', q='QRY-G1-GP04')
        if vc is not None:
            L('G-P-04', 'magnitude_formula', k, '捕获系数 λ/3（λ = .5 → 1/6；plan R05）', 'FULL', 'ann_pp_lambda_over_3', vc, 'ann_pp', status='INFO', q='QRY-G1-GP04')
    label('G-P-04', 'PRESPECIFIED_DISCRIMINATING_TEST', '量级只是带（不是门）；原式与 λ/3 修正并列，由 B 相账户读数对照，不在 S0 判定')


# ------------------------------------------------------------------ GW（E6r A2 新测；推导段）
def entry_sample():
    """FLAT NONE H20 NATIVE（主坐标）A2 常规批次入场：e0、sec、T0 = e0 − 1、名单位置 k、源权重 w、名义额 nt、due、关闭日。"""
    r = pick('NONE')
    ti, tf = trades(r.exec_hash)
    lots = lots_frame(ti, tf)
    lots = lots[(lots.e0 >= 1) & (lots.e0 <= G['last'])]
    e0 = lots.e0.to_numpy().astype(np.int64)
    sec = lots.sec.to_numpy().astype(np.int64)
    k = entry_index(e0, sec)
    ptr, col, w = G['f']
    ww = np.where(k >= 0, w[np.maximum(k, 0)], np.nan)
    return dict(e0=e0, sec=sec, T0=e0 - 1, k=k, w=ww, nt=lots.nt.to_numpy(), due=lots.due.to_numpy().astype(np.int64), cl=lots.cl.to_numpy(), r=r)


def gw01(S):
    """T0 状态（T1b_LEVEL 面板形成日收盘值：1 BAD / 0 GOOD / −1 UNKNOWN）对入场后可执行 q1 / q5 / q10 与至原 due 前向超额是否区分。"""
    st = np.asarray(G['lvl'][S['T0'], S['sec']], np.int64)
    rmax = ''
    res = {}
    for q in (1, 5, 10):
        x, cens = fwd(S['sec'], S['e0'], q)
        for code, nm in ((1, 'BAD'), (0, 'GOOD'), (-1, 'UNKNOWN')):
            m = (st == code) & np.isfinite(x)
            mu = float(x[m].mean() * 1e4) if m.any() else np.nan
            res[(q, nm)] = (mu, day_se(x[m], S['T0'][m]) * 1e4 if m.any() else np.nan, int(m.sum()))
            L('GW01', 'fwd_excess_after_entry', nm, 'q%d' % q, 'DERIV_2010_2018', 'mean_bp', mu, 'bp', int(m.sum()), q='QRY-G1-GW01')
            L('GW01', 'fwd_excess_after_entry', nm, 'q%d' % q, 'DERIV_2010_2018', 'day_cluster_se_bp', res[(q, nm)][1], 'bp', int(m.sum()), q='QRY-G1-GW01')
        L('GW01', 'fwd_excess_after_entry', 'censored', 'q%d' % q, 'DERIV_2010_2018', 'n_right_censored', int(cens.sum()), 'count', status='RIGHT_CENSORED' if cens.any() else 'COMPUTED',
          q='QRY-G1-GW01')
        ok_end = S['e0'][~cens] + q
        if len(ok_end):
            rmax = max(rmax, G['dates'][int(ok_end.max())])
    rem = np.maximum(S['due'] - S['e0'], 0)
    xs, dm = [], []
    for qq in np.unique(rem):
        if qq <= 0:
            continue
        mm = rem == qq
        x, cens = fwd(S['sec'][mm], S['e0'][mm], int(qq))
        xs.append((np.flatnonzero(mm), x))
        if (~cens).any():
            rmax = max(rmax, G['dates'][int((S['e0'][mm][~cens] + qq).max())])
    xd = np.full(len(S['e0']), np.nan)
    for idx, x in xs:
        xd[idx] = x
    for code, nm in ((1, 'BAD'), (0, 'GOOD'), (-1, 'UNKNOWN')):
        m = (st == code) & np.isfinite(xd)
        L('GW01', 'fwd_excess_to_original_due', nm, 'due', 'DERIV_2010_2018', 'mean_bp', float(xd[m].mean() * 1e4) if m.any() else np.nan, 'bp', int(m.sum()),
          q='QRY-G1-GW01')
    bshare = float((st == 1).mean())
    L('GW01', 'T0_state_share', 'BAD', 'entries', 'DERIV_2010_2018', 'share', bshare, 'share', len(st), q='QRY-G1-GW01')
    b, g = res[(5, 'BAD')], res[(5, 'GOOD')]
    t = (b[0] - g[0]) / np.sqrt(b[1] ** 2 + g[1] ** 2) if (np.isfinite(b[1]) and np.isfinite(g[1])) else np.nan
    L('GW01', 'BAD_minus_GOOD', 'q5', '', 'DERIV_2010_2018', 'diff_bp', b[0] - g[0], 'bp', q='QRY-G1-GW01')
    L('GW01', 'BAD_minus_GOOD', 'q5', '', 'DERIV_2010_2018', 't_approx', t, 'ratio', q='QRY-G1-GW01')
    label('GW01', 'SUPPORTED_DERIVATION' if (np.isfinite(t) and t <= -2) else 'NOT_YET_SUPPORTED', 'q5：BAD − GOOD < 0 且 |t| ≥ 2（日聚类 se，两组独立近似）→ SUPPORTED_DERIVATION；否则 NOT_YET_SUPPORTED')
    return rmax


def gw02(S):
    """CVR20 两类分位（同源域 = 当日全部有值证券；最终 cohort = 当日形成名单）× age1 q5 前向超额；等权与资本（源权重）加权；两种分位的标签重合率。"""
    x, cens = fwd(S['sec'], S['e0'], 5)
    w = np.where(np.isfinite(S['w']), S['w'], 0.0)
    lc = tert_domain(G['cvr20'], S['T0'], S['sec'], 'cohort')
    ls = tert_domain(G['cvr20'], S['T0'], S['sec'], 'source')
    d1, s1 = spread_rows('GW02', 'cvr20_cohort_tertile_q5', lc, x, S['T0'], w=w, q='QRY-G1-GW02')
    d2, s2 = spread_rows('GW02', 'cvr20_source_tertile_q5', ls, x, S['T0'], w=w, q='QRY-G1-GW02')
    ok = (lc > 0) & (ls > 0)
    L('GW02', 'label_agreement', 'cohort_vs_source', '', 'DERIV_2010_2018', 'share', float((lc[ok] == ls[ok]).mean()) if ok.any() else np.nan, 'share', int(ok.sum()),
      q='QRY-G1-GW02')
    label('GW02', 'SUPPORTED_DERIVATION' if (np.isfinite(s1) and d1 / s1 >= 2) else 'NOT_YET_SUPPORTED', '最终 cohort 分位的 age1 q5 T1 − T3 > 0 且 t ≥ 2 → SUPPORTED_DERIVATION（两类分位并报）')
    ok_end = S['e0'][~cens] + 5
    return G['dates'][int(ok_end.max())] if len(ok_end) else ''


def gw03(S):
    """CVR5 是否增加第一周分辨：CVR5 / CVR20 cohort 三分位的 age1 q1 / q5 T1 − T3；CVR20 同档内 CVR5 的 T1 − T3（条件分辨，三档等权平均）。"""
    rmax = ''
    l20 = tert_domain(G['cvr20'], S['T0'], S['sec'], 'cohort')
    l5 = tert_domain(G['cvr5'], S['T0'], S['sec'], 'cohort')
    res = {}
    for q in (1, 5):
        x, cens = fwd(S['sec'], S['e0'], q)
        res[('20', q)] = spread_rows('GW03', 'cvr20_q%d' % q, l20, x, S['T0'], q='QRY-G1-GW03')
        res[('5', q)] = spread_rows('GW03', 'cvr5_q%d' % q, l5, x, S['T0'], q='QRY-G1-GW03')
        cond = []
        for k in (1, 2, 3):
            m = l20 == k
            a = np.isfinite(x) & m & (l5 == 1)
            b = np.isfinite(x) & m & (l5 == 3)
            if a.any() and b.any():
                cond.append(float(x[a].mean() - x[b].mean()) * 1e4)
        L('GW03', 'cvr5_within_cvr20_tertile', 'T1_minus_T3_avg', 'q%d' % q, 'DERIV_2010_2018', 'diff_bp', float(np.mean(cond)) if cond else np.nan, 'bp', len(cond),
          q='QRY-G1-GW03')
        ok_end = S['e0'][~cens] + q
        if len(ok_end):
            rmax = max(rmax, G['dates'][int(ok_end.max())])
    d5, s5 = res[('5', 1)]
    label('GW03', 'SUPPORTED_DERIVATION' if (np.isfinite(s5) and d5 / s5 >= 2) else 'NOT_YET_SUPPORTED', 'CVR5 cohort 三分位 age1 q1 T1 − T3 > 0 且 t ≥ 2 → SUPPORTED_DERIVATION（条件分辨另列，不作判据）')
    return rmax


def gw04(S):
    """行业 × clean size 格内 CVR20 三分位（e6r_overlay labcell）的 age1 q5 T1 − T3（格内仍有方向？）。"""
    k = S['k']
    lab = np.where(k >= 0, np.asarray(G['ov']['labcell'])[np.maximum(k, 0)], 0).astype(np.int64)
    x, cens = fwd(S['sec'], S['e0'], 5)
    d, s = spread_rows('GW04', 'cvr20_within_cell_q5', lab, x, S['T0'], q='QRY-G1-GW04')
    label('GW04', 'SUPPORTED_DERIVATION' if (np.isfinite(s) and d / s >= 2) else 'NOT_YET_SUPPORTED', '格内 CVR20 三分位 age1 q5 T1 − T3 > 0 且 t ≥ 2 → SUPPORTED_DERIVATION')
    ok_end = S['e0'][~cens] + 5
    return G['dates'][int(ok_end.max())] if len(ok_end) else ''


def gw05():
    """允许的 1.5% 与行业预算下的实际权重转移（形成层 e6r_overlay 统计；不读收益）：各倾斜算子推导段的转移份额、单股 / 行业上界绑定份额、N_eff。"""
    ov = G['ov']
    segi = O.segs_of_dates(G['dates'])
    m = np.isin(segi, list(O.DERIV_SEGS))
    for sc in ('TILT_CVR_L050', 'TILT_CVR_L025', 'TILT_SIZE_L050', 'TILT_CVR5_L050', 'GATE_TILT', 'TILT_CVR_CELL_L050'):
        st = ov['stats|' + sc]
        ok = m & np.isfinite(st[:, 0])
        for j, nm in ((6, 'transfer_share'), (7, 'cap_bound_stock_share'), (8, 'cap_bound_industry_share'), (3, 'n_eff'), (0, 'g')):
            v = st[ok, j]
            L('GW05', 'formation_layer', sc, nm, 'DERIV_2010_2018', 'mean', float(np.nanmean(v)) if np.isfinite(v).any() else np.nan, 'share' if j in (6, 7, 8, 0) else 'count',
              int(ok.sum()), q='QRY-G1-GW05')
    st = ov['stats|TILT_CVR_L050']
    v = st[m & np.isfinite(st[:, 0]), 6]
    label('GW05', 'SUPPORTED_DERIVATION' if (np.isfinite(v).any() and np.nanmean(v) > 0.01) else 'NOT_YET_SUPPORTED',
          'TILT_CVR_L050 推导段形成层转移份额均值 > 1% → SUPPORTED_DERIVATION（预算下确有转移）；否则 NOT_YET_SUPPORTED')
    return ''


def gw06():
    """门控 × REARM（GATE_REARM_1E8 / 5E8 vs EXIT_GATE_LIQ_1E8 vs EXIT_HALF_REARM；LEVEL H30 主坐标；A2）：卖单请求额 / 分配额 / 强制额、待处理日份额、REARM 次数与升级。"""
    out = {}
    for op in ('GATE_REARM_1E8', 'GATE_REARM_5E8', 'EXIT_GATE_LIQ_1E8', 'EXIT_HALF_REARM'):
        r = pick('T1b_LEVEL', 'FLAT', '30', op)
        if r is None:
            L('GW06', 'gate_rearm', op, 'missing', 'DERIV_2010_2018', 'note', '', 'none', status='NOT_APPLICABLE', q='QRY-G1-GW06')
            continue
        DY = acct(r.exec_hash)['DY']
        Si = acct(r.exec_hash)['S_i']
        req = float(DY[:, E.DY_M3REQ].sum())
        alloc = float(DY[:, E.DY_M3ALLOC].sum())
        forced = float(DY[:, E.DY_M3FORCED].sum())
        pend = float((DY[:, E.DY_M3PEND] > 0).mean())
        out[op] = (req, alloc, forced, pend)
        for k, v, u in (('m3_request_val', req, 'CNY'), ('m3_alloc_val', alloc, 'CNY'), ('m3_forced_val', forced, 'CNY'), ('pending_day_share', pend, 'share'),
                        ('rearm_episodes', float(Si[E.SI_REARMN]), 'count'), ('rearm_promotions', float(DY[:, E.DY_GRPROM].sum()), 'count'),
                        ('deadline_overrides', float(Si[E.SI_OVERRIDE]), 'count'), ('half_requests', float(Si[E.SI_HALF]), 'count')):
            L('GW06', 'gate_rearm', op, k, 'DERIV_2010_2018', 'value', v, u, q='QRY-G1-GW06')
    g = out.get('GATE_REARM_1E8')
    label('GW06', 'SUPPORTED_DERIVATION' if (g is not None and g[3] > 0 and g[0] > 0) else 'NOT_YET_SUPPORTED',
          'GATE_REARM_1E8 推导段确有卖单请求与排队（请求额 > 0、待处理日 > 0）→ SUPPORTED_DERIVATION（机制运转，不判收益）')
    return ''


def gw07():
    """T1A_TIME_LEVEL_RANK 是否 LEVEL_WORST_1D 源别名：账户（FLAT H20 NATIVE 主坐标）推导段 D（对无退出父）vs T1a owner 的 LEVEL_WORST_1D 确定性路径推导段 D。"""
    r = pick('T1A_TIME_LEVEL_RANK')
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6r.csv'))
    o = pick('T1a')
    ref = RR[(RR.owner_exec_id == o.exec_id) & (RR.mechanism == 'LEVEL_WORST_1D')]
    p = O.P('randoms', 'random_paths_A2.csv')
    if not os.path.exists(p):
        p = O.P('randoms', 'random_paths_A2.partial.csv')
    P = pd.read_csv(p, keep_default_na=False, na_values=['']) if os.path.exists(p) else pd.DataFrame()
    x = P[(P.owner_exec_id == o.exec_id) & (P.mechanism == 'LEVEL_WORST_1D')] if len(P) else P
    a = acct(r.exec_hash)['DY'][:, E.DYI['net_excess']]
    nox = G['R'].set_index('exec_id').loc[r.exec_id].noexit_same_overlay_exec_id
    b = acct(G['R'].set_index('exec_id').loc[nox].exec_hash)['DY'][:, E.DYI['net_excess']]
    segi = O.segs_of_dates(G['dates'])[:len(a)]
    worst = np.nan
    for s in O.DERIV_SEGS:
        m = segi == s
        da = float(np.nanmean(a[m] - b[m]) * O.ANN_PP)
        L('GW07', 'time_level_rank_account', 'D_vs_noexit', s, s, 'ann_pp', da, 'ann_pp', int(m.sum()), q='QRY-G1-GW07')
        if len(x):
            dp = float(x['D_%s' % s].iloc[0])
            L('GW07', 'level_worst_1d_path_T1a_owner', 'D_vs_noexit', s, s, 'ann_pp', dp, 'ann_pp', q='QRY-G1-GW07')
            worst = np.nanmax([worst, abs(da - dp)]) if np.isfinite(worst) else abs(da - dp)
    alias = ('ALIAS_OF_SOURCE' if worst <= 1e-9 else 'NEW_COORDINATE') if np.isfinite(worst) else 'UNKNOWN'
    L('GW07', 'alias_check', 'max_abs_D_diff', '', 'DERIV_2010_2018', 'ann_pp', worst, 'ann_pp', status='COMPUTED' if np.isfinite(worst) else 'NOT_RUN', q='QRY-G1-GW07')
    put('S0-C', 'GW07', 'TIME_LEVEL_RANK_ALIAS', alias, 'none', alias if alias != 'UNKNOWN' else 'NOT_RUN', 'randoms/random_paths_A2.csv + accounts_run/deriv',
        'T1A_TIME_LEVEL_RANK 账户推导段 D 与 T1a owner 的 LEVEL_WORST_1D 确定性路径推导段 D 逐段比较（≤ 1e−9 → 别名）；账户照跑')
    label('GW07', 'SUPPORTED_DERIVATION' if alias == 'NEW_COORDINATE' else 'NOT_YET_SUPPORTED',
          'NEW_COORDINATE（与源确定性对照不同路径）→ SUPPORTED_DERIVATION（有独立坐标）；ALIAS_OF_SOURCE → NOT_YET_SUPPORTED（CC-E6r-09 注"无新独立检验"）')
    G['gw07_alias'] = alias
    return ''


def gw08():
    """混合 Q 真实分数、记忆年龄等代理的离散度与时间剖面：A4b 合成只存形成权重（每日 1–3 个不同值）、混合 Q 评分无独立列 → NOT_COMPUTABLE；
    能算的代理：形成权重离散度（每日不同值个数）与 HG10 名单逐日变动率（时间剖面，推导段）。"""
    ptr, col, w = G['f']
    segi = O.segs_of_dates(G['dates'])
    nu, chg = [], []
    prev = None
    for d in range(G['last'] + 1):
        a, b = ptr[d], ptr[d + 1]
        if b == a:
            continue
        nu.append(len(np.unique(np.round(w[a:b], 10))))
        cur = set(col[a:b].tolist())
        if prev is not None and len(prev):
            chg.append(len(cur - prev) / max(len(cur), 1))
        prev = cur
    L('GW08', 'mixed_Q_score', 'NOT_IN_CACHE', 'A4b 合成只存形成权重；混合 Q 评分无独立列', 'DERIV_2010_2018', 'note', '', 'none', status='NOT_APPLICABLE', q='QRY-G1-GW08')
    L('GW08', 'formation_weight_distinct_values', 'per_day', '', 'DERIV_2010_2018', 'median', float(np.median(nu)) if nu else np.nan, 'count', len(nu), q='QRY-G1-GW08')
    L('GW08', 'formation_list_turnover', 'new_share_per_day', '', 'DERIV_2010_2018', 'mean', float(np.mean(chg)) if chg else np.nan, 'share', len(chg), q='QRY-G1-GW08')
    label('GW08', 'NOT_COMPUTABLE', '混合 Q 真实分数与记忆年龄不在缓存（A4b 只存形成权重）→ NOT_COMPUTABLE；可算代理（权重离散度、名单变动率）并报')
    return ''


# ------------------------------------------------------------------ S0-B 结构基准率与 T0 ≠ age1
def s0b_transitions(S):
    """T0 状态（形成日收盘）→ age1 状态（入场日收盘）转移计数（FLAT NONE H20；推导段入场）；T0_NOT_AGE1 = 两个方向的跨态转移都存在（合同 gate_transition_counts 夹具同式）。"""
    st0 = np.asarray(G['lvl'][S['T0'], S['sec']], np.int64)
    st1 = np.asarray(G['lvl'][S['e0'], S['sec']], np.int64)
    nm = {1: 'BAD', 0: 'GOOD', -1: 'UNKNOWN'}
    cnt = {}
    for a, b in zip(st0, st1):
        k = '%s__%s' % (nm.get(int(a), 'UNKNOWN'), nm.get(int(b), 'UNKNOWN'))
        cnt[k] = cnt.get(k, 0) + 1
    for k, v in sorted(cnt.items()):
        put('S0-B', 'T0 → age1 状态转移（FLAT NONE H20 主坐标；推导段入场批次）', 'TRANSITION_%s' % k, v, 'count', 'INFO', 'trades_parts/deriv + T1b_LEVEL 面板')
    bg, gb = cnt.get('BAD__GOOD', 0), cnt.get('GOOD__BAD', 0)
    ok = bg > 0 and gb > 0
    IDN.append(dict(check_id='T0_NOT_AGE1', description='T0（形成日收盘）与 age1（入场日收盘）是两个时钟：真实入场批次中 BAD → GOOD 与 GOOD → BAD 转移都存在（%d / %d），不把 age1 份额当 T0 份额' % (bg, gb),
                    exec_id=S['r'].exec_id, value='%d|%d' % (bg, gb), max_abs_diff=0.0, tolerance=0.0, status='PASS' if ok else 'DIFFERS'))
    put('S0-B', 'T0 BAD 份额（入场批次）', 'BASE_RATE_T0_BAD_SHARE', float((st0 == 1).mean()), 'share', 'INFO', 'trades_parts/deriv', '与 age1 坏份额分开（brief §0.1 #12）')
    put('S0-B', 'age1 BAD 份额（入场批次）', 'BASE_RATE_AGE1_BAD_SHARE', float((st1 == 1).mean()), 'share', 'INFO', 'trades_parts/deriv', '')


def main():
    t0 = time.time()
    setup()
    gp01()
    gp02()
    gp03()
    gp04()
    S = entry_sample()
    rm = {}
    rm['GW01'] = gw01(S)
    rm['GW02'] = gw02(S)
    rm['GW03'] = gw03(S)
    rm['GW04'] = gw04(S)
    rm['GW05'] = gw05()
    rm['GW06'] = gw06()
    rm['GW07'] = gw07()
    rm['GW08'] = gw08()
    for k, v in rm.items():
        if v and v > DEND:
            raise RuntimeError('%s 收益窗越过推导段末 %s' % (k, v))
        put('S0-C', k, 'RETURN_END_MAX', v, 'date', 'COMPUTED' if v else 'NOT_APPLICABLE', 'diagnostics/G1_E6r.csv',
            '所用收益窗最大终点（≤ 2018-12-31；无收益读数的 GW 留空）')
    s0b_transitions(S)
    D = pd.DataFrame(ROWS, columns=LCOLS)
    O.atomic_write_csv(O.P('diagnostics', 'G1_E6r.csv'), D)
    O.atomic_write_csv(O.P('diagnostics', 'stage0_E6r_part2.csv'), pd.DataFrame(ST0))
    O.atomic_write_csv(O.P('verify', 'identities_E6r_g1.csv'), pd.DataFrame(IDN))
    Lg = O.read_csv(O.P('registration', 'ledger_G_E6r.csv'))
    for i, r in Lg.iterrows():
        lab, rule = G['labels'].get(r.g_id, ('NOT_COMPUTABLE', ''))
        Lg.at[i, 'state'] = lab
        Lg.at[i, 'result_query'] = 'QRY-G1-%s' % r.g_id.replace('-', '')
        Lg.at[i, 'result_row'] = 'diagnostics/G1_E6r.csv|block=%s|item=g_label' % r.g_id
        if not Lg.at[i, 'explanation_scope']:
            Lg.at[i, 'explanation_scope'] = rule
    O.atomic_write_csv(O.P('registration', 'ledger_G_E6r.csv'), Lg)
    facts = dict(g1_rows=len(D), labels={k: v[0] for k, v in G['labels'].items()}, gw07_alias=G.get('gw07_alias'), return_end_max=rm, wall_s=round(time.time() - t0, 1))
    O.atomic_write_json(O.P('diagnostics', 'g1_facts_E6r.json'), facts)
    O.write_receipt('E6r_g1', [O.P('diagnostics', 'G1_E6r.csv'), O.P('diagnostics', 'stage0_E6r_part2.csv'), O.P('verify', 'identities_E6r_g1.csv'),
                               O.P('registration', 'ledger_G_E6r.csv')], code=[__file__, O.__file__], g1_rows=len(D))
    print(json.dumps(facts, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
