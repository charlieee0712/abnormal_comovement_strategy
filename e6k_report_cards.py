# -*- coding: utf-8 -*-
"""E6k_REPORT_cards（18 张卡 × 登记 query）：registry/query_registry_E6k.csv 的每个 query_id 一张表（同 id 登记进 reports/query_registry_E6k.json），
供 hypothesis_outcomes 的 result_query 与 Q18 血缘直接引用（原句 → brief 采纳句 → 实现 → query → 允许结论）。
数据全部来自已封存的四段统计 / 政策 / 诊断 / 掩码事实 / 账户目标级数组，不另算收益；未计算的量写原因行，不补数。
差值约定：同原父基准的两个对象，"A − B" = FULL(A) − FULL(B)（逐对象 FULL 相减；FULL = 四段 n 加权）；登记了逐日配对比较的（D_vs_*）用配对版本。"""
import e6k_boot  # noqa: F401
import os
import sys
import glob
import json
import traceback

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_report as RP
import e6k_seal as SEAL

OUT = K.P('reports', 'E6k_REPORT_cards.md')
SEGS = K.SEGMENTS
DER, POS = K.DERIV_SEGS, K.POST_SEGS
PROFILES = ('LEGACY_EDIT5', 'PROPOSED_PORT3_T', 'PROPOSED_PORT3_LAG1', 'EXEC_DISCLOSE_ONLY', 'EXEC_LEADER_VS_PARENT')
DATES = '2010-01-04..2026-03-27（四段；FULL = 四段 n 加权；2026 partial）'
P6 = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')


class Ctx(object):
    pass


def load():
    c = Ctx()
    c.Q = pd.read_csv(K.P('registry', 'query_registry_E6k.csv')).set_index('query_id')
    c.D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    c.A = pd.read_csv(K.P('registry', 'accessory_E6k.csv'))
    c.P = pd.read_csv(K.P('results', 'full', 'policy_E6k.csv'))
    for b in ('primary144', 'c1_hi'):
        c.P[b] = c.P[b].astype(bool)
    c.Pi = c.P.set_index('desc_id')
    c.S = {s: pd.read_csv(K.P('results', 'full', 'descriptor_stats_%s.csv' % s)).drop_duplicates('desc_id').set_index('desc_id') for s in SEGS}
    c.R = pd.concat([pd.read_csv(K.P('results', 'full', 'random_refs_%s.csv' % s)).assign(segment=s) for s in SEGS], ignore_index=True)
    mf = [pd.read_csv(f) for f in sorted(glob.glob(K.P('registry', 'mask_facts_*_E6k.csv')))]
    c.MF = pd.concat(mf, ignore_index=True) if mf else pd.DataFrame()
    fa = []
    for s in SEGS:
        for f in sorted(glob.glob(K.P('accounts', s, 'facts_*.csv'))):
            fa.append(pd.read_csv(f).assign(segment=s))
    c.FA = pd.concat(fa, ignore_index=True) if fa else pd.DataFrame()
    return c


def fullv(c, col, ids, segs=SEGS):
    """四段 n 加权合并某统计列（每 id；缺段不计）。"""
    ids = list(ids)
    num = np.zeros(len(ids))
    den = np.zeros(len(ids))
    for s in segs:
        x = c.S[s].reindex(ids)
        if col not in x.columns:
            continue
        v, n = x[col].values.astype(float), x['n'].values.astype(float)
        m = np.isfinite(v) & np.isfinite(n) & (n > 0)
        num[m] += v[m] * n[m]
        den[m] += n[m]
    return pd.Series(np.where(den > 0, num / np.where(den > 0, den, 1), np.nan), index=ids)


def pfull(c, ids, col='FULL'):
    return c.Pi[col].reindex(list(ids))


def summ(df, by, val):
    g = df.dropna(subset=[val]).groupby(by)[val]
    out = g.agg(cells='count', median='median', q10=lambda x: x.quantile(.1), q90=lambda x: x.quantile(.9)).reset_index()
    out['share_pos'] = g.apply(lambda x: float((x > 0).mean())).values
    return out


def head(c, qid, H='5', op='见列', base='同 H 原父（8bp）', unit=None, support=None, cost='源 8bp', cap='实际源 DEV', expo='见 evidence_exposure / 首看标签',
         dates=DATES):
    q = c.Q.loc[qid]
    return {'主体': q.subject, '算子': op, '分母': '四段有效配对日（FULL = n 加权）', '基准': base, '子集': q.object_filter,
            '单位': unit or q.unit, '日期': dates, 'H': H, '成本模型': cost, '支持': support or q.support, '资本视图': cap, 'exposure': expo}


def did(f, p, a, h, op):
    return '%s|%s|a%s|H%d|%s' % (f, p, ('%g' % a), int(h), op)


# ============================================================================ 各 query
def q01a(c, rp, qid):
    t = c.P[c.P.primary144 & (c.P.op == 'NATIVE')].sort_values(['meas', 'mother'])
    cols = ['meas', 'mother', 'FULL', 'G4'] + ['D_%s' % s for s in SEGS] + ['policy_%s_FULL' % p for p in PROFILES] + ['policy_%s_G4' % p for p in PROFILES]
    rp.table(t[cols], head(c, qid, op='NATIVE', expo='原生：暴露台账'), qid)


def q01b(c, rp, qid):
    t = c.P[c.P.primary144 & (c.P.op == 'NATIVE')].sort_values(['meas', 'mother']).copy()
    for z in ('T', 'L'):
        for side in ('lo', 'hi'):
            t['port_size_%s_%s_full' % (side, z)] = fullv(c, 'port_size_%s_%s' % (side, z), t.desc_id).values
    for s in SEGS:
        t['edit_gap_mean_T_%s' % s] = t['edit_gap_mean_T_%s' % s]
        t['edit_gap_absmean_T_%s' % s] = t['edit_gap_absmean_T_%s' % s]
    tails = sorted(glob.glob(K.P('diagnostics', 'risk', '*_tails.csv')))
    if tails:
        tl = pd.concat([pd.read_csv(f) for f in tails], ignore_index=True)
        for b in ('small30', 'large30', 'unknown'):
            m = tl[tl.bucket == b].groupby('desc_id').capital_share_delta.mean()
            t['tail_capital_share_delta_%s_segavg' % b] = t.desc_id.map(m).values
        w = tl[tl.bucket == 'worst1pct_days'].groupby('desc_id').tail_mean_d_bp.mean()
        t['worst1pct_days_mean_d_bp_segavg'] = t.desc_id.map(w).values
    cols = (['meas', 'mother'] + ['port_size_%s_%s_full' % (sd, z) for z in ('T', 'L') for sd in ('lo', 'hi')] +
            ['port_size_lo_T_%s' % s for s in SEGS] + ['port_size_hi_T_%s' % s for s in SEGS] +
            ['edit_gap_mean_T_%s' % s for s in SEGS] + ['edit_gap_absmean_T_%s' % s for s in SEGS] + ['small30_delta_%s' % s for s in SEGS] +
            [x for x in t.columns if x.startswith(('tail_capital', 'worst1pct'))])
    rp.table(t[[x for x in cols if x in t.columns]], head(c, qid, op='NATIVE', unit='百分位点（size）/ 份额 / bp', expo='原生：暴露台账'), qid)


def q01c(c, rp, qid):
    t = c.P[c.P.primary144 & (c.P.op == 'NATIVE')].sort_values(['meas', 'mother']).copy()
    t['FULL_str'] = fullv(c, 'D_str', t.desc_id).values
    t['FULL_6bp'] = fullv(c, 'D_6bp', t.desc_id).values
    t['FULL_12bp'] = fullv(c, 'D_12bp', t.desc_id).values
    rp.table(t[['meas', 'mother', 'FULL', 'FULL_sc', 'G4', 'G4_sc', 'e_cap_FULL', 'FULL_imp', 'G4_imp', 'FULL_str', 'FULL_6bp', 'FULL_12bp']],
             head(c, qid, op='NATIVE', cost='源 8bp；imp = A 5 亿 κ .5；str = A 10 亿 κ 1；6 / 12bp 线性', cap='实际源 DEV 与 MATCH-CAP 并列',
                  expo='原生：暴露台账'), qid)


def q02a(c, rp, qid):
    t = c.P[c.P.family == 'SZL']
    o = summ(t, ['op', 'alpha', 'H'], 'FULL_vs_native')
    o = o.merge(t.groupby(['op', 'alpha', 'H']).FULL.median().rename('median_FULL').reset_index(), on=['op', 'alpha', 'H'])
    rp.table(o, head(c, qid, H='1…20', op='SZL3 / SZL5', base='同测量 NATIVE（逐日配对 D_vs_native）', unit='年化百分点（跨四测量 × 八母体的分布）'), qid)
    rp.p('主解释格（α .25 × H5）逐对象行见 `E6K-P2-144-*` / `E6K-P3-POL-*`。')


def q02b(c, rp, qid):
    t = c.P[c.P.family == 'SZL'].copy()
    own = t.desc_id + '_OWN'
    t['SZL_minus_OWN_FULL'] = t.FULL.values - pfull(c, own).values
    t['SZL_minus_OWN_G4'] = t.G4.values - pfull(c, own, 'G4').values
    o = summ(t, ['meas', 'op', 'alpha'], 'SZL_minus_OWN_FULL')
    o = o.merge(t.groupby(['meas', 'op', 'alpha']).SZL_minus_OWN_G4.median().rename('median_G4_diff').reset_index(), on=['meas', 'op', 'alpha'])
    rp.table(o, head(c, qid, H='1…20', op='SZL − SZL_OWN', base='同原父（逐对象 FULL 相减）', unit='年化百分点（跨 H × 八母体的分布）'), qid)


def q02c(c, rp, qid):
    t = c.P[c.P.family == 'SZL'].copy()
    nat = t.desc_id.str.rsplit('|', n=1).str[0] + '|NATIVE'
    mid = lambda ids: 0.5 * (fullv(c, 'port_size_lo_T', ids).values + fullv(c, 'port_size_hi_T', ids).values)
    t['port_size_mid_T_delta_vs_native'] = mid(t.desc_id) - mid(nat)
    o = summ(t, ['op', 'alpha'], 'port_size_mid_T_delta_vs_native')
    if len(c.MF):
        mf = c.MF[c.MF.op.isin(['SZL3', 'SZL5'])].copy()
        mf['alpha'] = mf.alpha.astype(str).str.lstrip('a').astype(float)
        mf['phase'] = np.where(mf.segment.isin(DER), 'deriv', 'post')
        ov = mf.groupby(['op', 'alpha', 'phase']).same_ticker_overlap_with_native.median().unstack('phase').add_prefix('overlap_with_native_median_').reset_index()
        o = o.merge(ov, on=['op', 'alpha'], how='left')
    rp.table(o, head(c, qid, H='1…20', op='SZL3 / SZL5', base='同测量 NATIVE', unit='百分位点（size 中点，带符号）/ 份额（换入重叠）'), qid)


def _acc(c, kind):
    return c.A[c.A.kind == kind].copy()


def q03a(c, rp, qid):
    a = _acc(c, 'INC_SUPPORT_ACCESSORY')
    a = a[a.op.str.startswith('INC_DOSE')]
    a['INC_minus_DOSE_FULL'] = -fullv(c, 'D_vs_compare', a.acc_id).values
    a['DOSE_FULL'] = fullv(c, 'D', a.acc_id).values
    a['INC_FULL'] = pfull(c, a.compare_to).values
    rp.table(a[['meas', 'mother', 'op', 'compare_to', 'INC_FULL', 'DOSE_FULL', 'INC_minus_DOSE_FULL']].sort_values(['meas', 'mother', 'op']),
             head(c, qid, op='INC − INC_DOSE（同均值 / 同 RMS）', base='逐日配对（D_vs_compare 取负）', support='INC：C = k0 ∧ kf ∧ z_T 有效'), qid)


def q03b(c, rp, qid):
    a = _acc(c, 'INC_SUPPORT_ACCESSORY')
    a['F'] = fullv(c, 'D', a.acc_id).values
    key = ['meas', 'mother', 'alpha', 'H']
    s0 = a[a.op == 'INC_SUPPORT0'].set_index(key).F.rename('SUPPORT0')
    d05 = a[a.op == 'INC_DOSE05'].set_index(key).F.rename('DOSE05')
    d1 = a[a.op == 'INC_DOSE1'].set_index(key).F.rename('DOSE1')
    t = pd.concat([s0, d05, d1], axis=1).reset_index()
    t['NATIVE'] = pfull(c, [did(r.meas, r.mother, r.alpha, r.H, 'NATIVE') for r in t.itertuples()]).values
    t['INC05'] = pfull(c, [did(r.meas, r.mother, r.alpha, r.H, 'INC05') for r in t.itertuples()]).values
    t['INC1'] = pfull(c, [did(r.meas, r.mother, r.alpha, r.H, 'INC1') for r in t.itertuples()]).values
    t['SUPPORT0_minus_NATIVE'] = t.SUPPORT0 - t.NATIVE
    t['DOSE05_minus_SUPPORT0'] = t.DOSE05 - t.SUPPORT0
    t['DOSE1_minus_SUPPORT0'] = t.DOSE1 - t.SUPPORT0
    t['INC05_minus_DOSE05'] = t.INC05 - t.DOSE05
    t['INC1_minus_DOSE1'] = t.INC1 - t.DOSE1
    rp.table(t.sort_values(['meas', 'mother']), head(c, qid, op='NATIVE → INC_SUPPORT0 → INC_DOSE → INC', base='同原父（逐对象 FULL 相减）',
                                                      support='INC：C = k0 ∧ kf ∧ z_T 有效'), qid)


def q03c(c, rp, qid):
    if not len(c.MF):
        raise RuntimeError('%s：掩码事实缺' % qid)
        return
    mf = c.MF[c.MF.op.isin(['INC05', 'INC1', 'SZL3', 'SZL5'])].copy()
    mf['alpha'] = mf.alpha.astype(str).str.lstrip('a').astype(float)
    mf['phase'] = np.where(mf.segment.isin(DER), 'deriv', 'post')
    o = mf.groupby(['op', 'alpha', 'phase']).agg(targets=('target_id', 'count'), overlap_with_native_median=('same_ticker_overlap_with_native', 'median'),
                                                  n_edits_in_median=('n_edits_in', 'median'), edit_weight_share_median=('edit_weight_share', 'median')).reset_index()
    rp.table(o, head(c, qid, H='—（目标级）', op='INC / SZL', base='同测量 NATIVE 的换入集合', unit='份额 / 名数', expo='掩码事实（不读收益）'), qid)
    rp.p('重叠率只描述编辑是否与 NATIVE 同名，不作收益证据（卡 Q03 反例条）。')


def q04a(c, rp, qid):
    t = c.P[(c.P.op == 'RPINF') & (c.P.alpha == 0.25) & (c.P.H == 5)].sort_values(['meas', 'mother']).copy()
    t['D_deriv'] = fullv(c, 'D', t.desc_id, DER).values
    t['D_post'] = fullv(c, 'D', t.desc_id, POS).values
    rp.table(t[['meas', 'mother', 'FULL', 'G4', 'FULL_vs_native', 'G4_vs_native', 'D_deriv', 'D_post']],
             head(c, qid, op='RPINF（= PAIR_ALL）', base='原父（FULL）与同测量 NATIVE（逐日配对 FULL_vs_native）'), qid)


def q04b(c, rp, qid):
    t = c.P[(c.P.op == 'RPINF') & (c.P.alpha == 0.25) & (c.P.H == 5)].sort_values(['meas', 'mother'])[['meas', 'mother', 'desc_id', 'FULL']].copy()
    for tau in ('0p5', '1', '3'):
        ids = t.desc_id.str.replace('|RPINF', '|RP%s' % tau, regex=False)
        t['RP%s_FULL' % tau] = pfull(c, ids).values
        t['RP%s_minus_PAIR_ALL' % tau] = t['RP%s_FULL' % tau] - t.FULL
    rp.table(t.drop(columns=['desc_id']).rename(columns={'FULL': 'PAIR_ALL_FULL'}),
             head(c, qid, op='RP τ{.5, 1, 3} − PAIR_ALL', base='同原父（逐对象 FULL 相减）'), qid)


def q04c(c, rp, qid):
    fa = c.FA[c.FA.op.astype(str).str.startswith('RP')].copy() if len(c.FA) else pd.DataFrame()
    if not len(fa):
        raise RuntimeError('%s：facts 缺' % qid)
        return
    for k in ('rp_recovered_days', 'solver_limit_days'):
        if k not in fa.columns:
            fa[k] = np.nan
    fa['rp_recovered_days'] = fa.rp_recovered_days.fillna(0)          # 恢复路径部署前完成的任务没有该列：它们没有复核失败日（失败即崩溃）
    o = fa.groupby(['segment', 'op']).agg(targets=('target_id', 'count'), days_with_edits=('rp_days_with_edits', 'sum'), pairs=('rp_pairs', 'sum'),
                                          kept=('rp_kept_pairs', 'sum'), unknown=('rp_unknown_edits', 'sum'),
                                          unpaired_structural=('rp_unpaired_structural', 'sum'), solver_limit_days=('solver_limit_days', 'sum'),
                                          recovered_days=('rp_recovered_days', 'sum')).reset_index()
    o['kept_share'] = o.kept / o.pairs.where(o.pairs > 0)
    rp.table(o, head(c, qid, H='—（目标级）', op='RP τ', unit='计数（目标 × 日求和）', expo='名单层事实（不读收益）', dates='四段分列'), qid)


def q05a(c, rp, qid):
    ids = c.P[c.P.primary144 & (c.P.op == 'NATIVE')].desc_id.tolist()
    R = c.R[(c.R.H == 5) & c.R.desc_id.isin(ids)]
    rows = []
    for d in ids:
        r = dict(desc_id=d)
        w = {s: c.Pi.at[d, 'n_%s' % s] for s in SEGS}
        for sub in ('EMPTY', 'I', 'S', 'K', 'IS', 'IK', 'SK', 'ISK'):
            mech = 'NEW_COND_ISK_P5' if sub == 'ISK' else 'EIGHT_SUBSET_' + sub
            x = R[(R.desc_id == d) & (R.mechanism == mech)]
            if len(x):
                ww = np.array([w.get(s, 0) for s in x.segment], float)
                r['rand_%s' % sub] = float(np.average(x.rand_mean, weights=ww)) if ww.sum() > 0 else np.nan
                if sub == 'ISK':
                    r['real_net8_ann'] = float(np.average(x.real_net8_ann, weights=ww)) if ww.sum() > 0 else np.nan
        rows.append(r)
    t = pd.DataFrame(rows)
    rp.table(t, head(c, qid, op='八子集条件置换（NEW 机制；ISK = NEW_COND_ISK_P5 别名）', base='随机路径均值（子账户 8bp 净值水平，不是相对原父）',
                     unit='年化百分点（四段按真实对象有效日加权）', expo='随机路径（无登记读数）'), qid)


def q05b(c, rp, qid):
    fs = sorted(glob.glob(K.P('diagnostics', 'mechanisms', '*_shapley.csv')))
    if not fs:
        raise RuntimeError('%s：Shapley 诊断缺' % qid)
        return
    sh = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    sh['w'] = [c.Pi.at[d, 'n_%s' % s] if d in c.Pi.index else np.nan for d, s in zip(sh.desc_id, sh.segment)]
    cols = [x for x in sh.columns if x.startswith('shapley_')] + ['closure_net']
    t = sh.groupby('desc_id').apply(lambda g: pd.Series({k: float(np.average(g[k], weights=g.w)) if g.w.sum() > 0 else np.nan for k in cols})).reset_index()
    rp.table(t, head(c, qid, op='I / S / K 六顺序平均 Shapley（gross / net / 费用分列）', base='八子集随机均值之差（算法效应，不是因果份额）',
                     unit='年化百分点（四段按有效日加权）', expo='随机路径（无登记读数）'), qid)


def q05c(c, rp, qid):
    fs = sorted(glob.glob(K.P('diagnostics', 'mechanisms', '*_leafdiag.csv')))
    if not fs:
        raise RuntimeError('%s：可移动份额 / 置换熵诊断缺' % qid)
        return
    ld = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    o = ld.groupby(['segment', 'subset']).agg(objects=('desc_id', 'nunique'), movable_share_median=('movable_share', 'median'),
                                              movable_share_min=('movable_share', 'min'), entropy_ratio_median=('entropy_ratio', 'median'),
                                              entropy_ratio_min=('entropy_ratio', 'min'), n_leaves_median=('n_leaves', 'median')).reset_index()
    rp.table(o, head(c, qid, H='—（分区）', op='八子集分层树（I > K > S）', base='当日单叶（EMPTY）', unit='份额 / 比例 / 叶数',
                     expo='分区结构（不读收益）', dates='四段分列'), qid)


def q06a(c, rp, qid):
    m5 = c.P[(c.P.alpha == 0.25) & (c.P.H == 5)].set_index(['meas', 'mother', 'op'])
    rows = []
    for (f, p), _ in c.P[(c.P.family == 'LX') & (c.P.alpha == 0.25) & (c.P.H == 5)].groupby(['meas', 'mother']):
        for lay in ('SIZE3', 'ISK'):
            v10 = m5.FULL.get((f, p, 'LX_%s_10' % lay), np.nan)
            v01 = m5.FULL.get((f, p, 'LX_%s_01' % lay), np.nan)
            v11 = m5.FULL.get((f, p, 'NATIVE'), np.nan)
            rows.append(dict(meas=f, mother=p, layer=lay, V10_minus_V00=v10, V01_minus_V00=v01, V11_minus_V00=v11, interaction=v11 - v10 - v01,
                             order_avg_allocation=0.5 * (v10 + v11 - v01), order_avg_within=0.5 * (v01 + v11 - v10)))
    rp.table(pd.DataFrame(rows), head(c, qid, op='LX 四账户', base='V00 = 原父', support='合法域先锁（X07-rev）'), qid)


def q06b(c, rp, qid):
    t = c.P[(c.P.family == 'LX') & (c.P.alpha == 0.25) & (c.P.H == 5)].sort_values(['meas', 'mother', 'op']).copy()
    t['capital_view_diff'] = t.FULL_sc - t.FULL
    t['impact_diff'] = t.FULL_imp - t.FULL
    t['turn_rel_full'] = fullv(c, 'turn_rel', t.desc_id).values
    t['nnames_delta_full'] = fullv(c, 'nnames_mean', t.desc_id).values - fullv(c, 'parent_nnames_mean', t.desc_id).values
    t['wsum_delta_full'] = fullv(c, 'wsum_mean', t.desc_id).values - fullv(c, 'parent_wsum_mean', t.desc_id).values
    rp.table(t[['meas', 'mother', 'op', 'FULL', 'FULL_sc', 'capital_view_diff', 'FULL_imp', 'impact_diff', 'turn_rel_full', 'nnames_delta_full', 'wsum_delta_full']],
             head(c, qid, op='LX', cost='源 8bp；imp = A 5 亿 κ .5', cap='实际源 DEV 与 MATCH-CAP 并列', support='合法域先锁（X07-rev）',
                  unit='年化百分点 / 相对换手 / 名数 / 资本份额'), qid)


def q06c(c, rp, qid):
    fs = sorted(glob.glob(K.P('diagnostics', 'mechanisms', '*_lx_gross.csv')))
    if not fs:
        raise RuntimeError('%s：gross 账本缺' % qid)
        return
    lg = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    t = lg.groupby(['desc_id', 'child']).agg(segments=('segment', 'nunique'), within_group=('within_group_ann', 'mean'), allocation=('allocation_ann', 'mean'),
                                             allocation_excess=('allocation_excess_ann', 'mean'), total=('total_ann', 'mean'),
                                             closure_resid_max=('closure_resid', 'max')).reset_index()
    rp.table(t, head(c, qid, op='LX 与对应 NATIVE', base='特征匹配基准（组内差 + 组配置；成本不分摊）', unit='年化百分点（四段简单平均）'), qid)


def q07a(c, rp, qid):
    t = c.P[((c.P.family == 'TREFIT') | (c.P.op == 'NATIVE')) & c.P.mother.isin(['A4b', 'A4b_CVRv5']) & (c.P.alpha == 0.25) & (c.P.H == 5) &
            c.P.meas.isin(['S', 'M', 'Q', 'C1'])].sort_values(['meas', 'mother', 'op']).copy()
    t['D_deriv'] = fullv(c, 'D', t.desc_id, DER).values
    t['D_post'] = fullv(c, 'D', t.desc_id, POS).values
    rp.table(t[['meas', 'mother', 'op', 'FULL', 'G4', 'D_deriv', 'D_post', 'FULL_vs_native']],
             head(c, qid, op='TREFIT g0 / g.5 / NATIVE（= g1）', base='原父（FULL）；FULL_vs_native = 逐日配对'), qid)


def q07b(c, rp, qid):
    t = c.P[(c.P.family == 'TREFIT') & (c.P.alpha == 0.25) & (c.P.H == 5)].sort_values(['meas', 'mother', 'op']).copy()
    t['port_size_mid_T_full'] = 0.5 * (fullv(c, 'port_size_lo_T', t.desc_id).values + fullv(c, 'port_size_hi_T', t.desc_id).values)
    t['edit_gap_mean_T_full'] = fullv(c, 'edit_gap_mean_T', t.desc_id).values
    if len(c.FA) and 'coef_interp_unavailable_days' in c.FA.columns:
        fa = c.FA[c.FA.op.astype(str).str.startswith('TREFIT')]
        cu = fa.groupby('target_id').coef_interp_unavailable_days.sum()
        t['coef_interp_unavailable_days_4seg'] = t.desc_id.map(lambda d: cu.get(c.D.set_index('desc_id').target_id.get(d, ''), np.nan)).values
    rp.table(t[[x for x in ['meas', 'mother', 'op', 'coef_interp_unavailable_days_4seg', 'port_size_mid_T_full', 'edit_gap_mean_T_full'] if x in t.columns]],
             head(c, qid, op='TREFIT', unit='日数 / 百分位点（带符号）', base='原父'), qid)
    rp.p('第二关有效数（逐日第二关实际参与回归的有效样本数）本轮未落盘：覆盖不足，记入 lessons 与下一轮设计。')


def q08a(c, rp, qid):
    t = c.P[c.P.family == 'POST2'].sort_values(['meas', 'mother', 'alpha', 'H']).copy()
    t = t[(t.alpha == 0.25) & (t.H == 5)]
    t['D_deriv'] = fullv(c, 'D', t.desc_id, DER).values
    t['D_post'] = fullv(c, 'D', t.desc_id, POS).values
    rp.table(t[['meas', 'mother', 'op', 'FULL', 'G4', 'FULL_vs_native', 'FULL_vs_C1', 'D_deriv', 'D_post']],
             head(c, qid, op='POST2_INCREMENT（C1 行 = 同算子主动控制）', base='原父；同测量 NATIVE 与同算子 C1（逐日配对）'), qid)


def q08b(c, rp, qid):
    t = c.P[(c.P.family == 'POST2') & (c.P.alpha == 0.25) & (c.P.H == 5)].sort_values(['meas', 'mother']).copy()
    t['capital_view_diff'] = t.FULL_sc - t.FULL
    if len(c.MF):
        mf = c.MF[c.MF.op == 'POST2_INCREMENT'].copy()
        mf['phase'] = np.where(mf.segment.isin(DER), 'deriv', 'post')
        mf['key'] = mf.meas + '|' + mf.mother + '|' + mf.alpha.astype(str)
        for ph in ('deriv', 'post'):
            g = mf[mf.phase == ph].groupby('key')
            t['n_edits_in_%s' % ph] = (t.meas + '|' + t.mother + '|a0.25').map(g.n_edits_in.mean()).values
            t['edit_weight_share_%s' % ph] = (t.meas + '|' + t.mother + '|a0.25').map(g.edit_weight_share.mean()).values
    rp.table(t[[x for x in ['meas', 'mother', 'FULL', 'FULL_sc', 'capital_view_diff', 'n_edits_in_deriv', 'n_edits_in_post', 'edit_weight_share_deriv',
                            'edit_weight_share_post'] if x in t.columns]],
             head(c, qid, op='POST2_INCREMENT', cap='实际源 DEV 与 MATCH-CAP 并列', unit='年化百分点 / 名数（最终名单相对原父的日均换入）/ 份额'), qid)
    rp.p('编辑数取最终名单相对原父的日均换入；"第二关前"的编辑数本轮未单独落盘（覆盖不足）。')


def _band(c, kind):
    t = c.P[(c.P.family == 'BAND') & c.P.op.str.contains('_%s' % kind) & (c.P.alpha == 0.25) & c.P.H.isin([3, 5, 10, 20])].copy()
    t['FULL_vs_base'] = fullv(c, 'D_vs_base', t.desc_id).values
    t['FULLg_vs_base'] = fullv(c, 'Dg_vs_base', t.desc_id).values
    t['turn_rel_full'] = fullv(c, 'turn_rel', t.desc_id).values
    return t


def _dose(c, kind):
    a = _acc(c, 'BAND_DOSE_CONTROL')
    a = a[a.op.str.contains('_%s' % kind)].copy()
    a['BAND_minus_DOSE_FULL'] = -fullv(c, 'D_vs_compare', a.acc_id).values
    a['band_op'] = a.op.str.replace('DOSE_', '', regex=False)
    return a


def qband_base(c, rp, qid, kind):
    t = _band(c, kind)
    o = summ(t, ['op', 'H'], 'FULL_vs_base')
    rp.table(o, head(c, qid, H='3 | 5 | 10 | 20', op='%s（NATIVE / INC1 两个基础）' % kind, base='无带基础（逐日配对 D_vs_base）',
                     unit='年化百分点（跨四测量 × 六形态的分布；α .25）'), qid)


def qband_dose(c, rp, qid, kind):
    a = _dose(c, kind)
    o = summ(a, ['band_op', 'H'], 'BAND_minus_DOSE_FULL')
    rp.table(o, head(c, qid, H='3 | 5 | 10 | 20', op='%s − 同日共同剂量控制' % kind, base='DOSE（逐日配对 D_vs_compare 取负）',
                     unit='年化百分点（四 owner 对象的分布）'), qid)


def na(c, rp, qid, reason, pointer=''):
    """登记了但本轮未计算的 query：一行表（同 query_id 登记），写原因与可用的替代读数位置，不补数。"""
    rp.table(pd.DataFrame([dict(query_id=qid, status='未计算（覆盖不足）', reason=reason, pointer=pointer)]),
             head(c, qid, H='—', op='—', base='—', unit='—', expo='—', dates='—', cost='—', cap='—'), qid)


def q10c(c, rp, qid):
    na(c, rp, qid, 'PM 只落盘了门内名单与目标级统计，逐日固定配对交换数的嵌套与结构单边编辑未单独记账；不另补算',
       'PM 的编辑事实见 registry/mask_facts_*_E6k.csv（n_edits_in / edit_weight_share；R0 §5 与 E6K-R0-MASK / E6K-R0-MASK-POST）')


def q11a(c, rp, qid):
    m5 = c.P[(c.P.alpha == 0.25) & (c.P.H == 5)].set_index(['meas', 'mother', 'op'])
    rows = []
    for r in c.P[(c.P.family == 'BAND') & c.P.op.str.contains('_HG') & (c.P.alpha == 0.25) & (c.P.H == 5)].itertuples():
        base = r.op.split('_')[0]
        v10 = m5.FULL.get((r.meas, r.mother, base), np.nan)
        b = r.op.split('HG')[-1]
        v01 = c.Pi.FULL.get('K0|%s|a0|H5|HG_ONLY%s' % (r.mother, b), np.nan)
        rows.append(dict(meas=r.meas, mother=r.mother, op=r.op, V11_minus_V00=r.FULL, V10_minus_V00=v10, V01_minus_V00=v01,
                         HG_minus_base=r.FULL - v10, info_margin_V11_minus_V01=r.FULL - v01, interaction=r.FULL - v10 - v01))
    rp.table(pd.DataFrame(rows).sort_values(['meas', 'mother', 'op']), head(c, qid, op='HG × 续选规则四账户（V01 = HG_ONLY，α0 不读新测量）', base='V00 = 原父'), qid)


def q11b(c, rp, qid):
    a = _dose(c, 'HG')
    o = summ(a, ['band_op', 'H'], 'BAND_minus_DOSE_FULL').rename(columns={'band_op': 'op'})
    t = c.P[(c.P.family == 'BAND') & c.P.op.str.contains('_HG') & (c.P.alpha == 0.25) & (c.P.H == 5) & c.P.primary144]
    R = c.R[(c.R.mechanism == 'NEW_COND_ISK_P5')]
    rows = []
    for d in t.desc_id:
        for H in (3, 5, 10, 20):                                         # 随机参照按登记单元（H5 描述符）存，持续性控制行的 H 列 = 3 / 10 / 20
            x = R[(R.desc_id == d) & (R.H == H)]
            if len(x):
                w = np.array([c.Pi.at[d, 'n_%s' % s] for s in x.segment], float)
                rows.append(dict(op=d.split('|')[-1], H=H, desc_id=d, real_minus_rand=float(np.average(x.real_minus_rand, weights=w)) if w.sum() > 0 else np.nan,
                                 mcse_max=float(x.mcse.max()), paths_min=int(x.n.min())))
    pr = pd.DataFrame(rows)
    if len(pr):
        ps = pr.groupby(['op', 'H']).agg(persistence_objects=('desc_id', 'count'), real_minus_rand_median=('real_minus_rand', 'median'),
                                          mcse_max=('mcse_max', 'max'), paths_min=('paths_min', 'min')).reset_index()
        o = o.merge(ps, on=['op', 'H'], how='outer')
    rp.table(o, head(c, qid, H='3 | 5 | 10 | 20', op='HG − DOSE；HG − 随机新内容续选（NEW_COND_ISK_P5 持续性控制）',
                     base='DOSE（逐日配对）；随机路径均值（real − rand，子账户净值水平）', unit='年化百分点', expo='主对象 + 随机路径'), qid)


def q11c(c, rp, qid):
    t = _band(c, 'HG')
    g = t.groupby(['op', 'H'])
    o = g.agg(cells=('desc_id', 'count'), turn_rel_median=('turn_rel_full', 'median'), gross_vs_base_median=('FULLg_vs_base', 'median'),
              net_vs_base_median=('FULL_vs_base', 'median')).reset_index()
    rp.table(o, head(c, qid, H='3 | 5 | 10 | 20', op='HG', base='无带基础（逐日配对：gross 与 8bp 净分列）', unit='相对换手 / 年化百分点（α .25）'), qid)


def _sq(c):
    s = c.P[c.P.meas == 'S'].copy()
    s['qid'] = 'Q|' + s.desc_id.str.split('|', n=1).str[1]
    s['Q_FULL'] = pfull(c, s.qid).values
    s['S_minus_Q_FULL'] = s.FULL - s.Q_FULL
    s['Q_G4'] = pfull(c, s.qid, 'G4').values
    s['S_minus_Q_G4'] = s.G4 - s.Q_G4
    return s


def q12a(c, rp, qid):
    s = _sq(c)
    o = summ(s, ['family', 'op', 'alpha'], 'S_minus_Q_FULL')
    rp.table(o, head(c, qid, H='1…20', op='S − Q（同槽位 / 同处理）', base='同原父（逐对象 FULL 相减）', unit='年化百分点（跨 H × 母体的分布）'), qid)
    rp.p('"同支持"只在原生 FALLBACK 口径下成立（两测量各自有效域）；S / Q 的 COMMON_SUPPORT 桥见 E6K-P1-CS / E6K-MX-CS。')


def q12b(c, rp, qid):
    s = _sq(c)
    s = s[(s.alpha == 0.25) & (s.H == 5) & s.op.isin(['NATIVE', 'SZL5', 'INC1', 'RP3', 'NATIVE_HG10', 'INC1_HG10'])]
    rp.table(s[['mother', 'op', 'FULL', 'Q_FULL', 'S_minus_Q_FULL', 'S_minus_Q_G4']].sort_values(['mother', 'op']),
             head(c, qid, op='S − Q（六接入 × 八母体）', base='同原父（逐对象 FULL 相减）'), qid)


def q13a(c, rp, qid):
    t = c.P[c.P.meas.str.startswith('RARPRE') & (c.P.op == 'NATIVE') & (c.P.alpha == 0.25) & (c.P.H == 5)].sort_values(['meas', 'mother'])
    rp.table(t[['meas', 'mother', 'FULL', 'G4'] + ['D_%s' % s for s in SEGS]], head(c, qid, op='NATIVE（RARPRE W20 / W60 × LT / SE）', expo='原生：暴露台账'), qid)


def q13b(c, rp, qid):
    a = _acc(c, 'COMMON_SUPPORT_CHILD')
    a = a[a.meas.astype(str).str.startswith('RARPRE')].copy()
    for k in ('N1_minus_N0', 'C1_minus_C0', 'C0_minus_N0', 'N1_minus_C1'):
        a[k] = fullv(c, k, a.acc_id).values
    rp.table(a[['meas', 'mother', 'H', 'op', 'N1_minus_N0', 'C1_minus_C0', 'C0_minus_N0', 'N1_minus_C1']].sort_values(['meas', 'mother', 'H']),
             head(c, qid, H='3 | 5 | 10 | 20', op='NATIVE（RARPRE）', base='N0 原父 / C0 共同支持父', support='J = k0 ∧ kf 有效（X16）'), qid)


def q13c(c, rp, qid):
    t = c.P[c.P.meas.str.startswith('RARPRE') & (c.P.op == 'NATIVE')]
    o = t.groupby(['meas', 'mother', 'alpha']).agg(H_cells=('H', 'count'), median_vs_native_S=('FULL_vs_native', 'median'),
                                                   share_pos=('FULL_vs_native', lambda x: float((x > 0).mean()))).reset_index()
    h5 = t[t.H == 5].set_index(['meas', 'mother', 'alpha']).FULL_vs_native.rename('H5_vs_native_S')
    o = o.merge(h5.reset_index(), on=['meas', 'mother', 'alpha'], how='left')
    rp.table(o, head(c, qid, H='1…20（中位）与 H5', op='RARPRE − NATIVE_S', base='同 α / H 的 S NATIVE（逐日配对）', expo='原生：暴露台账'), qid)


def _m5(c):
    return c.P[(c.P.alpha == 0.25) & (c.P.H == 5) & c.P.mother.isin(P6) & c.P.meas.isin(['S', 'M', 'Q', 'C1'])]


def q14a(c, rp, qid):
    t = _m5(c)
    pv = t.pivot_table(index=['meas', 'op'], columns='mother', values='FULL_vs_native', aggfunc='first')
    pv = pv[[m for m in P6 if m in pv.columns]].add_suffix('_vs_native').reset_index()
    rp.table(pv, head(c, qid, op='同算子跨六形态', base='同测量 NATIVE（逐日配对）'), qid)


def q14b(c, rp, qid):
    t = _m5(c).set_index(['meas', 'op', 'mother']).FULL.unstack('mother')
    o = pd.DataFrame(index=t.index)
    for x in ('A4b', 'M_mean3_v2', 'M_union3_v2'):
        if x in t.columns and x + '_CVRv5' in t.columns:
            o['%s_CVR_margin' % x] = t[x + '_CVRv5'] - t[x]
    rp.table(o.reset_index(), head(c, qid, op='同算子 CVR ± 边际', base='同原父（逐对象 FULL 相减；+CVRv5 − 纯净）'), qid)


def q14c(c, rp, qid):
    t = c.P[(c.P.alpha == 0.25) & (c.P.H == 5) & c.P.mother.isin(['A4b', 'A4b_CVRv5']) & c.P.meas.isin(['S', 'M', 'Q', 'C1']) &
            c.P.op.isin(['NATIVE', 'SZL5', 'INC1', 'RP3', 'NATIVE_HG10', 'INC1_HG10', 'TREFIT0', 'TREFIT0p5', 'POST2_INCREMENT'])].copy()
    t['capital_view_diff'] = t.FULL_sc - t.FULL
    if len(c.MF):
        mf = c.MF[c.MF.mother.isin(['A4b', 'A4b_CVRv5'])].copy()
        mf = mf[mf.alpha.astype(str) == 'a0.25']
        g = mf.groupby(['meas', 'mother', 'op'])
        for k in ('n_edits_in', 'edit_weight_share', 'edit_persistence_5d_reversal_share'):
            if k in mf.columns:
                t[k + '_segavg'] = [g[k].mean().get((r.meas, r.mother, r.op), np.nan) for r in t.itertuples()]
    cols = ['meas', 'mother', 'op', 'FULL', 'FULL_sc', 'capital_view_diff'] + [x for x in t.columns if x.endswith('_segavg')]
    rp.table(t[cols].sort_values(['meas', 'mother', 'op']), head(c, qid, op='A4b 两形态主接入 + TREFIT / POST2', cap='实际源 DEV 与 MATCH-CAP 并列',
                                                                  unit='年化百分点 / 名数 / 份额'), qid)


def q15a(c, rp, qid):
    t = c.P[~c.P.family.isin(['NATIVE', 'PARENT'])].copy()
    t['D_deriv'] = fullv(c, 'D', t.desc_id, DER).values
    t['D_post'] = fullv(c, 'D', t.desc_id, POS).values
    t['post_minus_deriv'] = t.D_post - t.D_deriv
    o = t.groupby(['family', 'op']).agg(cells=('desc_id', 'count'), FULL_median=('FULL', 'median'), D_deriv_median=('D_deriv', 'median'),
                                        D_post_median=('D_post', 'median'), share_post_pos=('D_post', lambda x: float((x > 0).mean())),
                                        post_minus_deriv_median=('post_minus_deriv', 'median'),
                                        label=('first_look_label', lambda x: '|'.join(sorted(set(map(str, x.dropna())))))).reset_index()
    rp.table(o, head(c, qid, H='1…20', op='全部新算子', unit='年化百分点（跨对象分布）', expo=K.LABEL_FIRST_LOOK), qid)


def q15b(c, rp, qid):
    am = K.P('results', 'account_manifest.csv')
    sha = pd.read_csv(am).set_index('file').sha256 if os.path.exists(am) else pd.Series(dtype=str)
    rows = []
    for s in SEGS:
        for f in sorted(glob.glob(K.P('accounts', s, '*.npz'))):
            b = os.path.basename(f)
            if b.startswith('weights_'):
                continue
            z = np.load(f, allow_pickle=False)                               # 只读两个键（不整读账户数组）
            w = K.P('accounts', s, 'weights_' + b)
            hs = lambda p: str(sha.get(K.rel(p), K.sha_file(p) if os.path.exists(p) else ''))[:16]
            rows.append(dict(segment=s, task=b[:-4].replace('__', '|'), n_targets=len(z['targets']), n_desc=len(z['desc']),
                             account_sha16=hs(f), weights_sha16=hs(w)))
    rp.table(pd.DataFrame(rows), head(c, qid, H='—', op='源对象（母体 | 测量）× 段', unit='计数 / sha256 前 16 位', expo='账户文件指纹（不读收益）',
                                      dates='四段分列'), qid)
    rp.p('目标 / 持仓指纹以任务 × 段的账户文件与权重文件 sha 表示（每个文件含该任务全部目标的位图与实际权重）；逐文件全长 sha 见 `results/account_manifest.csv`。')


def q16a(c, rp, qid):
    p = K.P('diagnostics', 'decay', 'decay_scenarios_v2.csv')
    if not os.path.exists(p):
        raise RuntimeError('%s：衰减场景缺' % qid)
        return
    d = pd.read_csv(p)
    rp.table(d[d.kind == 'reproduction'].dropna(axis=1, how='all'), head(c, qid, H='5', op='E6j 638 个 B 主配置对象', unit='计数 / 份额',
                                                                        expo='E6j 已暴露对象', dates='E6j 四段账本'), qid)


def q16b(c, rp, qid):
    p = K.P('diagnostics', 'decay', 'decay_scenarios_v2.csv')
    if not os.path.exists(p):
        raise RuntimeError('%s：衰减场景缺' % qid)
        return
    d = pd.read_csv(p)
    rp.table(d[d.kind == 'scenario'].dropna(axis=1, how='all'), head(c, qid, H='5', op='回顾性条件场景（θ × 漂移 × 波动来源 × L）', unit='份额（推导正中后段非正的比例）',
                                                                    expo='E6j 已暴露对象', dates='E6j 四段账本'), qid)
    rp.p('只读"与哪些场景相容 / 不相容"（观测值是否落在 [q05, q95]）；不输出选择效应 / 噪声 / 市场变化的份额（plan §10.5）。')


def _main148(c):
    return c.P[c.P.primary144 | c.P.c1_hi].sort_values(['meas', 'mother', 'op', 'H'])


def q17a(c, rp, qid):
    t = _main148(c)
    cols = ['meas', 'mother', 'op', 'alpha', 'H', 'FULL', 'G4'] + ['size_%s' % p for p in PROFILES] + ['policy_%s_FULL' % p for p in PROFILES]
    rp.table(t[cols], head(c, qid, H='见列', op='144 主展示 + 四条 C1_hi', unit='年化百分点 / 判词'), qid)


def _daily_mid(c, ids):
    """主对象目标级逐日 size 中点（T）：带符号 p05 / p95、|mid| 的 p95 与最大（最大处的带符号值）。只读目标级数组，不读收益。"""
    tmap = c.D.set_index('desc_id').target_id
    want = {tmap[d]: d for d in ids if d in tmap.index}
    acc = {}
    for s in SEGS:
        for f in sorted(glob.glob(K.P('accounts', s, '*.npz'))):
            if os.path.basename(f).startswith('weights_'):
                continue
            z = np.load(f, allow_pickle=False)                               # 懒读：先看 targets，命中才各读一次两个数组
            tg = list(map(str, z['targets']))
            hit = [j for j, tid in enumerate(tg) if tid in want]
            if not hit:
                continue
            LO, HI = z['t_szT_lo'], z['t_szT_hi']
            for j in hit:
                m = 0.5 * (LO[j] + HI[j])
                acc.setdefault(want[tg[j]], []).append(m[np.isfinite(m)])
    out = {}
    for d, parts in acc.items():
        m = np.concatenate(parts) if parts else np.array([])
        if not len(m):
            continue
        k = int(np.argmax(np.abs(m)))
        out[d] = dict(port_size_mid_T_p05=float(np.percentile(m, 5)), port_size_mid_T_p95=float(np.percentile(m, 95)),
                      port_size_mid_T_abs_p95=float(np.percentile(np.abs(m), 95)), port_size_mid_T_max=float(m[k]), port_size_mid_T_abs_max=float(abs(m[k])))
    return out


def q17b(c, rp, qid):
    t = _main148(c).copy()
    ids = t.desc_id.tolist()
    t['port_size_mid_T_mean'] = 0.5 * (fullv(c, 'port_size_lo_T', ids).values + fullv(c, 'port_size_hi_T', ids).values)
    t['port_size_mid_T_absmean'] = fullv(c, 'port_size_absmean_mid_T', ids).values
    dm = _daily_mid(c, ids)
    for k in ('port_size_mid_T_p05', 'port_size_mid_T_p95', 'port_size_mid_T_abs_p95', 'port_size_mid_T_max', 'port_size_mid_T_abs_max'):
        t[k] = [dm.get(d, {}).get(k, np.nan) for d in ids]
    t['lv5_child_full'] = fullv(c, 'lv5_mean', ids).values
    t['lv5_parent_full'] = fullv(c, 'parent_lv5_mean', ids).values
    t['small30_delta_full'] = fullv(c, 'small30_delta', ids).values
    t['unknown_size_capital_full'] = fullv(c, 'unkT_mean', ids).values
    t['roll_size_delta_T_full'] = fullv(c, 'roll_size_delta_T', ids).values
    t['edit_gap_mean_T_full'] = fullv(c, 'edit_gap_mean_T', ids).values
    t['edit_gap_absmean_T_full'] = fullv(c, 'edit_gap_absmean_T', ids).values
    t['edit_capital_share_full'] = fullv(c, 'edit_w_in_mean', ids).values
    t['n_edits_full'] = fullv(c, 'n_edits_mean', ids).values
    cols = ['meas', 'mother', 'op', 'alpha', 'H', 'port_size_mid_T_mean', 'port_size_mid_T_absmean', 'port_size_mid_T_p05', 'port_size_mid_T_p95',
            'port_size_mid_T_abs_p95', 'port_size_mid_T_max', 'port_size_mid_T_abs_max', 'lv5_child_full', 'lv5_parent_full', 'small30_delta_full',
            'unknown_size_capital_full', 'roll_size_delta_T_full', 'edit_gap_mean_T_full', 'edit_gap_absmean_T_full', 'edit_capital_share_full', 'n_edits_full']
    rp.table(t[cols], head(c, qid, H='见列', op='144 主展示 + 四条 C1_hi', unit='百分位点（size，带符号与绝对并印）/ 份额 / 名数',
                           support='原生（FALLBACK）；size 紧区间取中点'), qid)
    rp.p('`_mean` 为四段 n 加权的日均带符号值；`_absmean` 为逐段 |日均| 的 n 加权；p05 / p95 / max 为四段全部日的带符号分位与 |·| 最大处的带符号值（E6j #70 / #74 同印）。')


def q17c(c, rp, qid):
    t = _main148(c).copy()
    ids = t.desc_id.tolist()
    for m, tag in (('LEGACY_POLICY_RANDOM', 'LEGACY'), ('NEW_COND_ISK_P5', 'NEW')):
        R = c.R[c.R.mechanism == m]
        v, e = [], []
        for d, h in zip(ids, t.H):
            x = R[(R.desc_id == d) & (R.H == h)]
            w = np.array([c.Pi.at[d, 'n_%s' % s] for s in x.segment], float) if len(x) else np.array([])
            v.append(float(np.average(x.real_minus_rand, weights=w)) if len(x) and w.sum() > 0 else np.nan)
            e.append(float(x.mcse.max()) if len(x) else np.nan)
        t['real_minus_rand_%s_full' % tag] = v
        t['mcse_max_%s' % tag] = e
    rp.table(t[['meas', 'mother', 'op', 'alpha', 'H', 'FULL', 'FULL_vs_C1', 'FULL_vs_nativeC1', 'real_minus_rand_LEGACY_full', 'mcse_max_LEGACY',
                'real_minus_rand_NEW_full', 'mcse_max_NEW']],
             head(c, qid, H='见列', op='144 主展示 + 四条 C1_hi', base='原父；同算子 C1 与 NATIVE_C1（逐日配对）；随机路径均值（子账户净值水平）'), qid)


def q18a(c, rp, qid):
    L = pd.read_csv(K.P('registry', 'hypothesis_lineage_E6k.csv'))
    rp.table(L, head(c, qid, H='—', op='—', base='—', unit='文本 / 链接', expo='登记（读数前）', dates='—', cost='—', cap='—'), qid)


def q18b(c, rp, qid):
    import e6k_deliver as DL
    rows = []
    for r in DL.REPORTS:
        rows.append(dict(item='reports/' + r, exists_at_generation=os.path.exists(K.P('reports', r)),
                         note='本报告之后生成' if r in ('E6k_REVIEW_input.md', 'E6k_lessons_delta.md', 'E6k_REPORT_cards.md') else ''))
    for t in DL.TABLES:
        rows.append(dict(item=t, exists_at_generation=os.path.exists(K.P(t)),
                         note='本报告之后生成' if t in ('results/hypothesis_outcomes.json', 'results/completion_receipt.json') else ''))
    rp.table(pd.DataFrame(rows), head(c, qid, H='—', op='—', base='—', unit='存在性', expo='—', dates='—', cost='—', cap='—'), qid)
    rp.p('最终逐项存在性以 `results/completion_receipt.json`（闭包门）为准。')


BUILD = {
    'E6K-Q01-a': q01a, 'E6K-Q01-b': q01b, 'E6K-Q01-c': q01c,
    'E6K-Q02-a': q02a, 'E6K-Q02-b': q02b, 'E6K-Q02-c': q02c,
    'E6K-Q03-a': q03a, 'E6K-Q03-b': q03b, 'E6K-Q03-c': q03c,
    'E6K-Q04-a': q04a, 'E6K-Q04-b': q04b, 'E6K-Q04-c': q04c,
    'E6K-Q05-a': q05a, 'E6K-Q05-b': q05b, 'E6K-Q05-c': q05c,
    'E6K-Q06-a': q06a, 'E6K-Q06-b': q06b, 'E6K-Q06-c': q06c,
    'E6K-Q07-a': q07a, 'E6K-Q07-b': q07b,
    'E6K-Q08-a': q08a, 'E6K-Q08-b': q08b,
    'E6K-Q09-a': lambda c, rp, q: qband_base(c, rp, q, 'SA'), 'E6K-Q09-b': lambda c, rp, q: qband_dose(c, rp, q, 'SA'),
    'E6K-Q10-a': lambda c, rp, q: qband_base(c, rp, q, 'PM'), 'E6K-Q10-b': lambda c, rp, q: qband_dose(c, rp, q, 'PM'), 'E6K-Q10-c': q10c,
    'E6K-Q11-a': q11a, 'E6K-Q11-b': q11b, 'E6K-Q11-c': q11c,
    'E6K-Q12-a': q12a, 'E6K-Q12-b': q12b,
    'E6K-Q13-a': q13a, 'E6K-Q13-b': q13b, 'E6K-Q13-c': q13c,
    'E6K-Q14-a': q14a, 'E6K-Q14-b': q14b, 'E6K-Q14-c': q14c,
    'E6K-Q15-a': q15a, 'E6K-Q15-b': q15b,
    'E6K-Q16-a': q16a, 'E6K-Q16-b': q16b,
    'E6K-Q17-a': q17a, 'E6K-Q17-b': q17b, 'E6K-Q17-c': q17c,
    'E6K-Q18-a': q18a, 'E6K-Q18-b': q18b,
}


def main():
    for pkg in ('deriv', 'post'):
        ok, bad = SEAL.verify(pkg)
        if not ok:
            raise RuntimeError('seal_%s 核对失败：%s' % (pkg, bad[:5]))
    c = load()
    cards = pd.read_csv(K.P('registry', 'cards_E6k.csv'))
    rp = RP.Report('cards')
    rp.h(1, 'E6k REPORT cards —— 18 张卡的登记 query（每个 query_id 一张表）')
    rp.p('用途：把 `registry/query_registry_E6k.csv` 的 47 个登记 query 逐个落成表（同 id），供 `results/hypothesis_outcomes.json` 的 result_query 与 Q18 血缘直接引用。'
         '数字全部来自已封存的四段统计 / 政策 / 诊断 / 掩码事实 / 账户目标级数组；不设显著性门、不写判词；新算子行首看标签 `%s`；'
         '`policy_provisional = true`；`deployment_authorized = false`。未计算的量写原因，不补数。' % K.LABEL_FIRST_LOOK)
    fails = []
    for cd in cards.itertuples():
        rp.h(2, '%s（plan 第 %d 行）%s' % (cd.card, int(cd.plan_line), cd.title.split('｜', 1)[-1]))
        for qid in cd.queries.split('|'):
            rp.h(3, qid)
            try:
                BUILD[qid](c, rp, qid)
            except Exception as e:                                      # noqa: BLE001
                fails.append((qid, repr(e)))
                traceback.print_exc()
    missing = sorted(set(c.Q.index) - set(BUILD))
    if fails or missing:
        raise RuntimeError('cards 生成失败：%s；未实现 %s' % (fails[:5], missing))
    rp.write(OUT)
    K.write_receipt('report_cards', [OUT], 'SUCCEEDED', queries=len(rp.qids))
    print('cards 写出：%d 个 query' % len(rp.qids), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
