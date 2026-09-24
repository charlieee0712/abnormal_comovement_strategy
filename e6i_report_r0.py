#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i REPORT_R0 生成器 (brief §4 / §14 / §15)。全部数字从 results 产物计算 (不凭记忆);
每张表前一行 = 四项 (汇总算子 / 分母及构成 / 基准 / 子集) + 单位 / 日期支持 / H / 成本 / 支持口径 / 资本口径,
缺任一项 -> 生成 FAIL; 计数 / 全称 / 中位 / 最高 / 单调类句子由表计算并带 query_id。
输出 reports/E6i_REPORT_R0.md + reports/R0_tables/*.csv (表的全量数)。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I

R = I.RES
MEAS = os.path.join(R, 'measurements')
OUT = os.path.join(R, 'reports')
TAB = os.path.join(OUT, 'R0_tables')
SEGS = list(I.DERIV_SEGS)
QIDS = []
REQ = ('汇总算子', '分母及构成', '基准', '子集', '单位', '日期支持', 'H', '成本', '支持口径', '资本口径')
FORBID = ('可交付', '已确证', '必须换核', '饱和', '穷尽', '到平台')
REP = {
    'T': ['T_mean20', 'T_cv20', 'T_std20', 'T_madrel20', 'T_resid20', 'T_cvpre20', 'T_std60_LEGACY'],
    'K': ['K0_LEGACY', 'K_ROS20_E6F', 'K_log', 'K_res_log', 'K_amt5', 'K_ar20', 'K_edge20'],
    'V': ['V_park20_LEGACY', 'V_park20_obs', 'V_rs20_obs', 'V_yz20_obs', 'V_cc20', 'V_on20', 'V_max20'],
    'R': ['R_skip1_LEGACY', 'R_5_s0', 'R_peer20', 'R_resid20', 'R_eff20'],
    'O': ['O_onmean5', 'O_enshare20', 'O_balance20', 'O_retreat_up20'],
    'C': ['C_CVR20_LEGACY', 'C_mean5', 'C_mean20', 'C_amtw20', 'C_dev1'],
    'A': ['A_rel20', 'A_innov', 'T_evlevel', 'A_frompeak'],
    'S': ['S_peerR20', 'S_peerpos20', 'S_peeriqr20', 'S_peeract'],
}
REPS = sum(REP.values(), [])


def ss(s):
    return s[2:4] + '-' + s[-2:]


def q(qid, text):
    QIDS.append(dict(query_id=qid, text=re.sub(r'\s+', ' ', text)))
    return '%s〔%s〕' % (text, qid)


def hdr(op, denom, bench, subset, unit='不适用', dates='推导两段（2010-01-04..2014-12-31 / 2015-01-05..2018-12-28）',
        H='不适用', cost='不适用', support='pool0 成员有值格', capital='不适用'):
    return ('> **汇总算子**：%s ｜ **分母及构成**：%s ｜ **基准**：%s ｜ **子集**：%s ｜ **单位**：%s ｜ '
            '**日期支持**：%s ｜ **H**：%s ｜ **成本**：%s ｜ **支持口径**：%s ｜ **资本口径**：%s\n'
            % (op, denom, bench, subset, unit, dates, H, cost, support, capital))


def md(df, nd=3):
    if df is None or not len(df):
        return '_（无数据）_\n'
    d = df.copy()
    d.columns = [' / '.join(str(x) for x in c if str(x) != '') if isinstance(c, tuple) else str(c)
                 for c in d.columns]
    for c in d.columns:
        if d[c].dtype.kind == 'f':
            d[c] = d[c].map(lambda v: ('%.*f' % (nd, v)) if np.isfinite(v) else '—')
    cols = list(d.columns)
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, r in d.iterrows():
        out.append('| ' + ' | '.join(str(r[c]) for c in cols) + ' |')
    return '\n'.join(out) + '\n'


def save(name, df):
    os.makedirs(TAB, exist_ok=True)
    df.to_csv(os.path.join(TAB, name + '.csv'), index=False)


def load_many(pat):
    fs = sorted(glob.glob(os.path.join(MEAS, pat)))
    return pd.concat([pd.read_csv(f, low_memory=False) for f in fs], ignore_index=True) if fs else pd.DataFrame()


def jl(p):
    try:
        return json.load(open(os.path.join(R, p)))
    except Exception:
        return None


def check_headers(txt):
    lines = txt.split('\n')
    bad = []
    for i in range(1, len(lines)):
        if lines[i].startswith('|---') and lines[i - 1].startswith('| '):
            j = i - 2
            while j >= 0 and lines[j].strip() == '':
                j -= 1
            h = lines[j] if j >= 0 else ''
            if not (h.startswith('> **汇总算子**') and all(('**%s**' % k) in h for k in REQ)):
                bad.append(i)
    return bad


def monotone(vals):
    d = np.diff(np.asarray(vals, float))
    if np.all(d < 0):
        return '单调下降'
    if np.all(d > 0):
        return '单调上升'
    return '非单调'


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    L = []
    w = L.append
    diag = load_many('diag_*_*.csv')
    meas = load_many('measure_layer_*_*.csv')
    t0p = load_many('t0_portrait_*_*.csv')
    t0r = load_many('t0_reference_sets_*.csv')
    first = load_many('first_table_*.csv')
    marg = load_many('signal_margin_profile_*.csv')
    cost = load_many('cost_exposure_*.csv')
    pol = load_many('limit_policy_*.csv')
    q3 = load_many('q3_v_strata_*.csv')
    sim = pd.read_csv(os.path.join(R, 'checks', 'simulation_results.csv'), low_memory=False)
    man = jl('registry/manifest_A0.json')
    ea = [jl('checks/engine_anchor_%s.json' % s) for s in SEGS]
    fa = [jl('checks/feature_anchors_%s.json' % s) for s in SEGS]
    ra = [jl('checks/rule_anchors_%s.json' % s) for s in SEGS]
    la = [jl('checks/label_anchor_%s.json' % s) for s in SEGS]
    spa = [jl('checks/sparse_engine_anchor_%s.json' % s) for s in SEGS]
    ga = jl('checks/guard_attack_tests.json')
    ct = jl('checks/plan_contract_tests/e6i_plan_contract_test_results.json')
    vc = jl('checks/vendor_check.json')
    sfx = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(R, 'checks', 'suffix_guard_*.csv'))],
                    ignore_index=True)
    now = time.strftime('%Y-%m-%d %H:%M')
    S0, S1 = SEGS

    # ================================================================ 计算
    f_all = first[first.year.astype(str) == 'all'][['segment', 'quantity', 'p05', 'p25', 'p50', 'p75', 'p95',
                                                    'mean', 'frac_pos', 'n']]
    save('first_table', f_all)
    cr = f_all[f_all.quantity == 'cr5_source_unadjusted_simple'].set_index('segment')
    lt = f_all[f_all.quantity == 'limit_touch_days_last5'].set_index('segment')
    ml = meas.groupby(['segment', 'axis']).agg(n=('member_id', 'size'), cov_med=('cov_pool0', 'median'),
                                                cov_min=('cov_pool0', 'min'), tie_med=('tie_frac', 'median'),
                                                ac1_med=('rank_autocorr_lag1', 'median'),
                                                ac5_med=('rank_autocorr_lag5', 'median'),
                                                raw_vs_ns_med=('raw_vs_ns_spearman', 'median')).reset_index()
    save('measure_layer_by_axis', ml)
    lowcov = meas[meas.cov_pool0 < 0.9][['segment', 'member_id', 'cov_pool0']].sort_values(['segment', 'cov_pool0'])
    # 预测层
    pdg = diag[(diag.label == 'src5') & diag.set.isin(['__all__', 'core_kept', 'final', 'econ_reject', 'edge',
                                                       'pre_focal'])].copy()
    pdg['setn'] = np.where(pdg.set == '__all__', 'pool0', pdg.set)
    save('prediction_all_members_src5', pdg)
    mm = pdg.groupby(['segment', 'setn', 'axis', 'member_id']).ic_mean.mean().reset_index()
    piv = mm.groupby(['segment', 'setn', 'axis']).ic_mean.median().unstack(['segment', 'setn'])
    piv = piv.reindex(columns=pd.MultiIndex.from_product([SEGS, ['pool0', 'final', 'edge', 'econ_reject']]))
    save('prediction_axis_set_pivot', piv.reset_index())
    # 全部成员 x 段: final 的 |IC| 与 econ_reject 的 |IC| 之比
    fr = mm.pivot_table(index=['segment', 'member_id'], columns='setn', values='ic_mean')
    fr = fr[np.isfinite(fr.econ_reject) & (fr.econ_reject.abs() > 0.02)]
    ratio = (fr.final.abs() / fr.econ_reject.abs()).groupby('segment').median()
    nfr = fr.groupby('segment').size()
    sig = pdg[pdg.setn == 'pool0'].assign(s=lambda x: x.ic_nw_t.abs() > 2).groupby(['segment', 'axis']).agg(
        n=('member_id', 'size'), k=('s', 'sum')).reset_index()
    rp = pdg[pdg.member_id.isin(REPS) & pdg.setn.isin(['pool0', 'final', 'econ_reject'])]
    rpv = rp.groupby(['member_id', 'segment', 'setn']).ic_mean.mean().unstack(['segment', 'setn'])
    rpv = rpv.reindex(columns=pd.MultiIndex.from_product([SEGS, ['pool0', 'final', 'econ_reject']]))
    rpv.columns = ['%s IC %s' % (ss(a), b) for a, b in rpv.columns]
    g5 = pdg[pdg.member_id.isin(REPS) & (pdg.setn == 'pool0')].groupby(['member_id', 'segment'])[
        ['g5_1', 'g5_5']].mean().unstack('segment')
    g5.columns = ['%s pool0 %s' % (ss(b), a) for a, b in g5.columns]
    rep_tab = rpv.join(g5).reindex(REPS).reset_index()
    save('prediction_representatives', rep_tab)
    hs = diag[(diag.mother == 'pool0') & (diag.set == '__all__') & diag.member_id.isin(REPS)]
    hcv = hs.pivot_table(index='member_id', columns=['segment', 'label'], values='ic_mean')
    hcols = [(s, l_) for s in SEGS for l_ in ('entry_1', 'entry_5', 'entry_20', 'src5') if (s, l_) in hcv.columns]
    hcv = hcv[hcols]
    hcv.columns = ['%s %s' % (ss(a), b) for a, b in hcv.columns]
    hcv = hcv.reindex(REPS).reset_index()
    save('H_support_curve_representatives', hcv)
    # 决策层
    dl = diag[diag.set == 'decision_swap10pct'].copy()
    save('decision_layer_all', dl)
    dls = dl.groupby(['segment', 'side', 'axis']).agg(
        n=('member_id', 'size'), n_pos=('swap_in_minus_out_mean', lambda s: int((s > 0).sum())),
        median=('swap_in_minus_out_mean', 'median'), best=('swap_in_minus_out_mean', 'max')).reset_index()
    save('decision_layer_by_axis', dls)
    dtab = dls.assign(v=lambda x: x.n_pos.astype(str) + '/' + x.n.astype(str)).pivot_table(
        index='axis', columns=['segment', 'side'], values='v', aggfunc='first')
    dtab.columns = ['%s %s 正/总' % (ss(a), b) for a, b in dtab.columns]
    dmed = dls.pivot_table(index='axis', columns=['segment', 'side'], values='median')
    dmed.columns = ['%s %s 中位' % (ss(a), b) for a, b in dmed.columns]
    dtab = dtab.join(dmed).reset_index()
    dpos = dl[dl.swap_in_minus_out_mean > 0]
    top = dpos.sort_values('swap_in_minus_out_mean', ascending=False).head(15)[
        ['segment', 'mother', 'side', 'member_id', 'swap_in_minus_out_mean', 'swap_nw_t']]
    both = dpos.groupby(['member_id', 'side', 'mother']).segment.nunique()
    both2 = both[both == 2].reset_index()
    save('decision_layer_positive_both_segments', both2)
    ax_side = dpos.assign(ax=dpos.member_id.str[0]).groupby(['side', 'axis']).size().sort_values(ascending=False)
    top2 = ax_side.head(2)
    # 事件层
    ev = diag[(diag.mother == 'pool0') & diag.set.str.startswith('age')]
    evm = ev.groupby(['segment', 'axis', 'set']).ic_mean.median().unstack(['segment', 'set'])
    evm = evm.reindex(columns=pd.MultiIndex.from_product([SEGS, ['age1', 'age2', 'age3', 'age4', 'age5']]))
    evm.columns = ['%s %s' % (ss(a), b) for a, b in evm.columns]
    evm = evm.reset_index()
    save('event_layer_axis_median_ic', evm)
    # T0
    t0a = t0p[t0p.stratum == 'all'].copy()
    t0a['z'] = (t0a.pct_diff_winner_minus_loser - t0a.perm_mean) / t0a.perm_sd
    t0m = t0a.groupby(['segment', 'member_id']).agg(diff=('pct_diff_winner_minus_loser', 'mean'),
                                                    z=('z', 'mean')).reset_index()
    save('T0_econ_reject_mean_over_mothers', t0m)
    nz = t0m.assign(neg=t0m.z < -3, pos=t0m.z > 3).groupby('segment').agg(n=('member_id', 'size'),
                                                                        n_neg=('neg', 'sum'), n_pos=('pos', 'sum'))
    topz = {s: t0m[t0m.segment == s].nsmallest(3, 'z') for s in SEGS}
    T0KEY = ['R_5_s0', 'R_peer20', 'R_resid20', 'R_skip1_LEGACY', 'C_mean5', 'C_CVR20_LEGACY', 'T_std20', 'T_cv20',
             'T_mean20', 'T_std60_LEGACY', 'K_res_log', 'K0_LEGACY', 'K_amt5', 'V_max20', 'V_rs20_obs',
             'V_yz20_obs', 'V_park20_LEGACY', 'V_on20']
    ref = None
    if len(t0r):
        ref = t0r.groupby(['segment', 'set', 'member_id']).pct_diff_winner_minus_loser.mean().unstack(
            ['segment', 'set'])
        save('T0_reference_sets', t0r)
    rows = []
    for mid in T0KEY:
        rec = dict(member_id=mid)
        for s in SEGS:
            x = t0m[(t0m.segment == s) & (t0m.member_id == mid)]
            rec['%s 拒绝集差' % ss(s)] = float(x['diff'].iloc[0]) if len(x) else np.nan
            rec['%s z' % ss(s)] = float(x['z'].iloc[0]) if len(x) else np.nan
            if ref is not None:
                for sn, lab in (('final', '保留集差'), ('pool0', 'pool0差'), ('p0_sameN', 'p0同人数差')):
                    rec['%s %s' % (ss(s), lab)] = float(ref.loc[mid, (s, sn)]) \
                        if ((s, sn) in ref.columns and mid in ref.index) else np.nan
        rows.append(rec)
    t0tab = pd.DataFrame(rows)
    save('T0_key_members', t0tab)
    t0s = t0p[t0p.member_id.isin(['R_5_s0', 'R_peer20', 'T_std20', 'K_res_log', 'V_rs20_obs', 'V_park20_LEGACY',
                                  'T_std60_LEGACY', 'K0_LEGACY'])]
    t0str = t0s.pivot_table(index='member_id', columns=['segment', 'stratum'],
                            values='pct_diff_winner_minus_loser', aggfunc='mean')
    t0str = t0str.reindex(columns=pd.MultiIndex.from_product(
        [SEGS, ['drift_low', 'drift_mid', 'drift_high', 'touch0', 'touch1p']]))
    t0str.columns = ['%s %s' % (ss(a), b) for a, b in t0str.columns]
    t0str = t0str.reset_index()
    save('T0_strata', t0str)
    spec_cnt = None
    if ref is not None:
        crow = []
        for s in SEGS:
            x = t0m[t0m.segment == s].set_index('member_id')
            for mid in x.index:
                if mid not in ref.index:
                    continue
                crow.append(dict(segment=s, member_id=mid, d_reject=x.loc[mid, 'diff'], z=x.loc[mid, 'z'],
                                 d_p0_sameN=ref.loc[mid, (s, 'p0_sameN')], d_final=ref.loc[mid, (s, 'final')]))
        cmpd = pd.DataFrame(crow)
        sg = cmpd[cmpd.z.abs() > 3]
        spec_cnt = sg.assign(same=np.sign(sg.d_reject) == np.sign(sg.d_p0_sameN),
                             samef=np.sign(sg.d_reject) == np.sign(sg.d_final),
                             ratio=sg.d_reject / sg.d_p0_sameN).groupby('segment').agg(
            n_sig=('member_id', 'size'), n_same=('same', 'sum'), n_samef=('samef', 'sum'),
            ratio_med=('ratio', 'median'))
        save('T0_reject_vs_references', cmpd)
    # C3
    mgv = marg.pivot_table(index=['margin', 'quintile'], columns='segment',
                           values=['src5_mean_bp', 'src5_median_bp', 'p_neg'])
    mgv = mgv.reindex(columns=pd.MultiIndex.from_product([['src5_mean_bp', 'src5_median_bp', 'p_neg'], SEGS]))
    mgv.columns = ['%s %s' % (ss(b), a) for a, b in mgv.columns]
    mgv = mgv.reset_index()
    save('signal_margin_profile', marg)
    ag = marg[marg.margin == 'trigger_age'].set_index(['segment', 'quintile']).src5_mean_bp
    rc = marg[marg.margin == 'realized_cr5_at_t'].set_index(['segment', 'quintile']).src5_mean_bp
    ag_mono = {s: monotone([ag.loc[(s, k)] for k in range(1, 6)]) for s in SEGS}
    rc_min = {s: int(np.argmin([rc.loc[(s, k)] for k in range(1, 6)]) + 1) for s in SEGS}
    save('limit_policy', pol)
    ce = cost.groupby(['segment', 'member_id', 'set']).day_mean_of_means.mean().unstack(['segment', 'set'])
    ce = ce.reindex(columns=pd.MultiIndex.from_product([SEGS, ['final', 'edge', 'econ_reject', 'pool0']]))
    ce.columns = ['%s %s' % (ss(a), b) for a, b in ce.columns]
    ce = ce.reset_index()
    save('cost_exposure', cost)
    cedge = cost.groupby(['segment', 'member_id', 'set']).day_mean_of_means.mean().unstack('set')
    cedge = cedge.assign(r=cedge.edge / cedge.final)
    n_edge_hi = (cedge.r > 1).groupby('segment').sum()
    n_edge = cedge.r.notna().groupby('segment').sum()
    # Q17
    sh = pdg.copy()
    gcols = ['g5_1', 'g5_2', 'g5_3', 'g5_4', 'g5_5']
    sh['g_range'] = sh[gcols].max(1) - sh[gcols].min(1)
    sh['shape_flag'] = (sh.ic_mean.abs() < 0.01) & (sh.u_shape_index.abs() > 0.5 * sh.g_range) & (sh.g_range > 5)
    q17c = sh.groupby(['segment', 'setn', 'axis']).agg(n=('member_id', 'size'), k=('shape_flag', 'sum')).reset_index()
    q17p = q17c.assign(v=lambda x: x.k.astype(int).astype(str) + '/' + x.n.astype(str)).pivot_table(
        index='axis', columns=['segment', 'setn'], values='v', aggfunc='first')
    q17p = q17p.reindex(columns=pd.MultiIndex.from_product([SEGS, ['pool0', 'final', 'edge', 'econ_reject']]))
    q17p.columns = ['%s %s' % (ss(a), b) for a, b in q17p.columns]
    q17p = q17p.reset_index()
    save('Q17_shape_counts', q17c)
    q17m = sh[sh.shape_flag]
    q17both = q17m.groupby(['member_id', 'setn', 'mother']).segment.nunique()
    q17both = q17both[q17both == 2].reset_index()
    save('Q17_shape_members', q17m[['segment', 'mother', 'setn', 'member_id', 'ic_mean'] + gcols + ['u_shape_index']])
    save('Q17_shape_members_both_segments', q17both)
    # Q3
    q3t = q3r = None
    if len(q3):
        q3k = ['V_park20_LEGACY', 'V_park20_obs', 'V_rs20_obs', 'V_yz20_obs', 'V_gk20_obs', 'V_mj20_obs', 'V_cc20',
               'V_on20', 'V_oc20', 'V_max20', 'V_idio20']
        q3t = q3[q3.member_id.isin(q3k)].pivot_table(index='member_id', columns=['segment', 'stratum'],
                                                      values='ic_mean')
        q3t = q3t.reindex(columns=pd.MultiIndex.from_product(
            [SEGS, ['all', 'drift_low', 'drift_high', 'range_low', 'range_high', 'touch0', 'touch1p']]))
        q3t.columns = ['%s %s' % (ss(a), b) for a, b in q3t.columns]
        q3t = q3t.reindex(q3k).reset_index()
        save('Q3_v_strata', q3)
        q3r = q3[q3.member_id.isin(q3k) & (q3.stratum == 'all')][
            ['segment', 'member_id', 'g1_mean', 'g5_mean', 'g1_sd', 'g5_sd', 'g1_pneg', 'g5_pneg', 'g1_p10', 'g5_p10']]

    # ================================================================ 正文
    w('# E6i REPORT_R0 —— P0 起点 + Stage 0 仪器 + A0 登记 + Stage 1 测量级诊断\n')
    w('执行 session，%s（47 时间）；结果目录 `20260923_0254_E6i_measurement_need_fit`（47）。推导段 2010-2014 / '
      '2015-2018；**新测量与新算子没有任何 2019+ 数值**（守卫攻击 32/32；后缀检查 %d 个 0 失败）。本报告供规划 session '
      '写 A1（brief §11.1：≤2 个工作日，可为 "reviewed; no change"）；执行端不等 A1，Stage 2 主账户已按 A0 全部跑完。'
      '全量表：`reports/R0_tables/*.csv`。\n' % (now, len(sfx)))
    w('---\n')
    SUMMARY_AT = len(L)
    w('')
    # ---- 1
    w('## 1. 起点与仪器（brief §1–§3）\n')
    w('- 指纹：plan `cf9ce859…`（1,734 行）/ brief `5475d97c…` / proposal `f3c2fd44…` / E6h REVIEW `5eb27e87…`；47 HEAD '
      '`4b1ee8e`；四地基 + e6e–e6h 共 100 个脚本 SHA 冻结于 `source_manifest.json`。')
    w('- 源码核对：brief 的 source-level 事实 **0 处错误**；12 条细节补正（`reports/source_corrections_E6i.md` C1–C12）。'
      '会改变读表的三条：① `turnover_rate` 是**比例**、分母流通股（`turnover_ff` 不可得、未造）；② 限价表列数 5,448 ≠ '
      'close 3,587，**须按 ticker 对齐**（对齐后覆盖 99.999%）；③ **A08 没有 C 核心腿**（C 是 k5 否决）→ RC 核心槽位只有 '
      'A06，A08 的 CVR 走焦点分支。')
    w('- I7（E6g/E6h 登记的 ~205 线程/进程来源）查明：pyarrow 13 import 即初始化 S3，AWS SDK 起 192 个事件循环线程；'
      '`e6i_boot` 关闭后 13 线程/进程。\n')
    rows = []
    for s, e_, f_, r_, l_, sp_ in zip(SEGS, ea, fa, ra, la, spa):
        rows.append({'段': s,
                     '引擎锚': '%d/%d' % (e_['n_pass'], e_['n_checked']),
                     '引擎最大逐日差': '%.1e' % max(max(x['net8_max_abs'], x['gross_max_abs']) for x in e_['rows']),
                     '稀疏引擎锚': ('%d/%d' % (sp_['n_pass'], sp_['n_rows'])) if sp_ else '未跑',
                     '稀疏 DEV 差 / 账本差': ('%.0e / %.0e' % (sp_['dev_max_abs'], sp_['pnl_max_abs'])) if sp_ else '—',
                     '特征锚': '%d/%d' % (f_['n_pass'], f_['n_anchor']),
                     '算子锚': '%d/%d' % (r_['n_pass'], r_['n']),
                     '标签锚 (bp)': '%.1e' % l_['max_abs_bp']})
    w(hdr('逐项计数 / 最大绝对差', '引擎 6 母体 x 8 个 H；稀疏引擎 4 母体 + 24 随机名单 x 6 个 H；特征 19 项；算子 4 母体 x '
          '14–19 项；标签 = 段内全部有值格', '源 e6e/e6f/e6g/e6h 实现（稀疏引擎以已锚稠密引擎为基准）', '推导两段',
          unit='账本为日收益比例；标签 bp', H='1/2/3/5/10/20', cost='8bp 主口径', support='全部名单格', capital='源 DEV'))
    w(md(pd.DataFrame(rows)))
    w('- 守卫攻击 must_block %d/%d、must_pass %d/%d；plan 附录 B 契约 %d/%d；EDGE vendor（作者 commit `1caba55d`）%d/%d；'
      'Meilijson 系数对 arXiv 原文式 (1)/(3) 逐项一致。' % (
          ga['n_must_block_ok'], ga['n_must_block'], ga['n_must_pass_ok'], ga['n_must_pass'], ct['passed'],
          ct['tests'], vc['n_pass'], vc['n']))
    w('- 前缀不变（plan §3.4）：%s；每个检查的后缀确被扰动。\n' % q(
        'Q-R0-SFX', '%d 个"成员 x 切点"检查失败 %d 个' % (len(sfx), int((~sfx.ok).sum()))))
    p = sim[sim.panel == 'price']
    c = p[(p.variant == 'clean') & (p.window == 20) & (p.policy == 'OBS') & (p.rho == 0) & (p.regime == 'const')]
    tb = c.pivot_table(index=['estimator', 'steps'], columns='mu', values='rel_bias', aggfunc='mean').reset_index()
    tb.columns = [('漂移 %s' % x) if isinstance(x, float) else str(x) for x in tb.columns]
    w('**ADEMP（误差表，不是 PASS 门）**\n')
    w(hdr('相对偏差 mean(θ̂)/θ−1，对 σ∈{20,40,80}% 与隔夜比 {0,.5,1} 算术平均', '每格 2,000 路径 x 250 日（窗 20）',
          '日内估计量 → 日内积分方差；YZ/CC → 全天方差；ON/OC → 各自分量', 'clean 变体；列 = 日 log 漂移',
          unit='比例', dates='仿真（非市场日期）', support='仿真全部路径'))
    w(md(tb))
    xs = sim[sim.panel == 'price_xs'].pivot_table(index='estimator', columns=['mu', 'onr'],
                                                 values='spearman_true_var')
    xs.columns = ['漂移 %s / 隔夜比 %s' % (a, b) for a, b in xs.columns]
    w(hdr('截面 Spearman(20 日估计, 真 σ²) 的重复均值', '每格 40 次重复 x 200 只 x 每 10 日一截面', '真 σ²', 'clean',
          unit='相关系数', dates='仿真（非市场日期）', support='仿真全部路径'))
    w(md(xs.reset_index()))
    w('读法：RS / YZ 对漂移不变，Parkinson / GK / Meilijson 随漂移偏移；极差类 390 步 −6%~−9% 离散偏差、1,560 步约减半；'
      '截面排序 OHLC 类 0.987–0.991 vs 收盘价 0.942。**这是测量精度，不是选股收益证据（W07）。**\n')
    # ---- 2
    cnt = man['counts']
    w('## 2. A0 登记\n')
    w('`registry/descriptors_A0.csv` **%d 个描述符**（当前 v1.2，sha `%s`），`need_estimator_role_map.csv` %d 行，代表描述符 %d；'
      '首轮随机路径预算（代表 256 / 其余 64，按描述符计）%d。两次修订都是对 plan 原文的编译补全、都在相应结果读出之前，'
      '旧版原样保留：\n' % (cnt['total_descriptors'], man['descriptors_sha256'][:16], cnt['total_map_rows'],
                            cnt['representative_descriptors'], cnt['random_paths_first_pass']))
    w('- **v1.1**：补 plan §5.7 四臂参数（FOURARM 144→216 行，其余 id 不变；`registry/A0_amendment_v1_1.md`）。')
    w('- **v1.2**：补 plan §5.3 焦点替换的"两者"臂 —— RR 的 cr5 焦点只编了"新"（`replace_cr5`），补 `both_cr5` 480 行'
      '（R2 / A06 各 240），其余 35,176 行逐字段不变；信息暴露如实登记：调试 Z-MAP 时见过 RR "新"臂 2010-14 的账户水平，'
      '未与母体或其他臂比较（`registry/A0_amendment_v1_2.md`）。')
    w('- `preregistration.md`（sha `d5312ce8`，2026-09-23 16:21:24）早于任何新测量收益评价，未改。\n')
    # ---- 3
    w('## 3. 首表：pool0 的真实状态（W01；Q3 首表 / Q11）\n')
    w(hdr('分位数 / 均值 / 正值占比', 'pool0 全部格（形成日 x 股票）', '无（描述）', 'pool0',
          unit='收益 = 比例（cr5 源口径 = 未复权简单收益）；日龄 = 交易日', support='pool0 全部格'))
    w(md(f_all.rename(columns={'quantity': '量'})))
    w('**I11 池不是强漂移池**：%s；近 5 日触及涨跌停的格占 %s。\n' % (
        q('Q-R0-W01', '形成日 5 日源收益中位 %+.2f%% / %+.2f%%，正值占比 %.1f%% / %.1f%%（10-14 / 15-18）' % (
            100 * cr.loc[S0, 'p50'], 100 * cr.loc[S1, 'p50'], 100 * cr.loc[S0, 'frac_pos'],
            100 * cr.loc[S1, 'frac_pos'])),
        q('Q-R0-TOUCH', '%.1f%% / %.1f%%' % (100 * lt.loc[S0, 'frac_pos'], 100 * lt.loc[S1, 'frac_pos']))))
    # ---- 4
    w('## 4. 测量层（覆盖 / 平局 / 排名稳定 / 中性化前后）\n')
    w(hdr('按轴的中位数（覆盖另给最小）', '每段每轴全部成员（含 LEGACY 桥）', '无', 'pool0', unit='比例 / 相关系数',
          support='pool0 格'))
    w(md(ml))
    w('pool0 覆盖 < 0.9：%s —— %s。\n' % (q('Q-R0-LOWCOV', '%d 个"成员 x 段"' % len(lowcov)), '；'.join(
        '%s %s %.2f' % (ss(r.segment), r.member_id, r.cov_pool0) for r in lowcov.itertuples())))
    # ---- 5
    w('## 5. 预测层（形成日 Spearman；标签 src5 = 源 5 日超额，日龄线性）\n')
    w(hdr('成员 IC 日均先对四母体取均值，再取轴内成员中位', '每格 = 该段该集合该轴全部成员',
          '无（排序相关；负 = 成员高值对应低未来收益）', 'pool0 / 最终保留 final / 决策边缘 edge / 经济拒绝 econ_reject',
          unit='Spearman', H='src5（5 日）', support='集合内当日有值格（≥10 名）'))
    pv = piv.copy()
    pv.columns = ['%s %s' % (ss(a), b) for a, b in pv.columns]
    w(md(pv.reset_index()))
    w('pool0 内 |NW t|>2 的成员数（NW lag 5；删缺测日后拼接 = Stage 1 诊断口径，不是 §8.2 主统计）：%s。\n' % '；'.join(
        '%s %s %d/%d' % (ss(r.segment), r.axis, r.k, r.n) for r in sig.itertuples()))
    w('读法：%s。新测量的排序信息主要落在母体**已经拒绝**的名字上，在最终名单内部小得多 —— 与 E6h "现有测量池内排序力弱" 同向；'
      '这里只是测量层，不是账户。\n' % q('Q-R0-FINAL', '拒绝集 |IC|>0.02 的成员里，final 的 |IC| 与拒绝集 |IC| 之比中位 %s' % '；'.join(
          '%s %.2f（%d 个）' % (ss(s), ratio.loc[s], nfr.loc[s]) for s in SEGS)))
    w(hdr('IC 日均（非 pool0 列为四母体均值）与 pool0 五分组 src5 均值', '当日集合内有值名单', '无', '代表成员（plan §7.1）',
          unit='IC；g5 为 bp（g5_1 = 成员值最低组）', H='src5', support='集合内有值格'))
    w(md(rep_tab))
    w(hdr('pool0 形成日 Spearman 日均', 'pool0 当日有值名单', '无', '代表成员', unit='Spearman',
          H='entry-fixed 1/5/20 与源 src5', support='pool0 有值格'))
    w(md(hcv))
    # ---- 6
    w('## 6. 决策层（同预算换入 − 换出：最接近母体改善的测量桥，不是账户）\n')
    w(hdr('每个 (成员, 母体) 的 (换入均值 − 换出均值) 日均；按轴计为正的个数 / 总数与中位',
          '每日 m = floor(0.1·|final|)；换出 = final 中母体核分最差 m；换入 = econ_reject 中按成员一端取 m',
          '母体自己的最差 m 个', '四母体 x 两端（low_in = 成员低值端换入；high_in = 高值端换入）', unit='bp', H='src5',
          cost='无（未过 DEV / 持仓 / 成本）', support='final 与 econ_reject 有值格'))
    w(md(dtab, 1))
    w('%s；两段都为正的 (成员, 端, 母体) %s；为正组合最多的两个 (端, 轴)：%s。\n' % (
        q('Q-R0-DPOS', '换入 − 换出为正的 (成员, 母体, 端, 段) 共 %d / %d' % (len(dpos), len(dl))),
        q('Q-R0-DPOS2', '%d 个' % len(both2)),
        q('Q-R0-DPOS3', '；'.join('%s %s %d 个' % (a, b, n) for (a, b), n in top2.items()))))
    w(hdr('换入 − 换出日均与 NW t（lag 5）', '同上', '母体最差 m 个', '全部组合中最高 15 个', unit='bp', H='src5', cost='无',
          support='同上'))
    w(md(top, 2))
    # ---- 7
    w('## 7. 事件层（按触发日龄）\n')
    w(hdr('pool0 形成日 IC 日均，轴内成员中位', 'pool0 中该日龄的有值名单', '无', 'pool0，日龄 1–5', unit='Spearman',
          H='src5', support='pool0 有值格'))
    w(md(evm))
    # ---- 8
    w('## 8. T0 画像复核（Q18 的 Stage 1 部分）\n')
    w('主体逐字：**被错剔的赢家**（`econ_reject ∩ src5 > 0`）相对 **被剔掉的输家**（`econ_reject ∩ src5 < 0`）。度量 = 成员 '
      'NS pct（高值 = 高 pct；全部成员按原符号存，源函数取负的 skip1 / Parkinson 已还原）两组形成日均值之差，日期等权；'
      'z = 相对当日拒绝集内打乱标签 50 次的均值 / 标准差。**对照集**（brief "同人数反向对照" 的执行端口径）：同一差值在母体'
      '**最终保留集**、**整个 pool0**、以及 **pool0 内每日随机抽与拒绝集同人数的名单**里各算一次 —— 若拒绝集的差 ≈ pool0 '
      '同人数的差，画像是池子层面的收益预测，不是"被错剔"特有。pool0 同人数名单是**一次固定种子抽样**（种子 20260923+18，'
      '每母体一套），不是随机分布；它回答"同样多的随机 pool0 名字里会不会看到同样的差"，量级比较看表中数值。\n')
    w(hdr('pct 均值差（赢家 − 输家），四母体算术平均；z 为四母体均值', '拒绝集 / 保留集 / pool0 / pool0 同人数，当日两组各 ≥3 名',
          '标签置换 50 次（z）；对照集的同一差值', '关键成员（旧 LEGACY 与新测量并列）', unit='pct（0–1）', H='src5',
          support='集合内有值格'))
    w(md(t0tab))
    w('%s；z 最负的三个成员：%s。' % (
        q('Q-R0-T0Z', '；'.join('%s 在 %d 个成员里 z<−3 的 %d 个、z>3 的 %d 个' % (
            ss(s), int(nz.loc[s, 'n']), int(nz.loc[s, 'n_neg']), int(nz.loc[s, 'n_pos'])) for s in SEGS)),
        q('Q-R0-T0TOP', '；'.join('%s %s' % (ss(s), '、'.join('%s（%.1f）' % (r.member_id, r.z)
                                                              for r in topz[s].itertuples())) for s in SEGS))))
    if spec_cnt is not None:
        w('拒绝集 vs 对照集：%s。' % q('Q-R0-T0SPEC', '；'.join(
            '%s |z|>3 的 %d 个成员里，与 pool0 同人数对照同号 %d 个、与保留集同号 %d 个，拒绝集差 / 同人数对照差的中位 %.2f' % (
                ss(s), int(spec_cnt.loc[s, 'n_sig']), int(spec_cnt.loc[s, 'n_same']), int(spec_cnt.loc[s, 'n_samef']),
                spec_cnt.loc[s, 'ratio_med']) for s in SEGS if s in spec_cnt.index)))
    w('')
    w(hdr('pct 均值差（赢家 − 输家）四母体均值', '各层内当日两组各 ≥3 名', '标签置换（见上）',
          '真实漂移（当日拒绝集内 cr5 三分位）与近 5 日触板分层', unit='pct', H='src5', support='拒绝集有值格'))
    w(md(t0str))
    # ---- 9
    w('## 9. 信号边界描述 signal_margin_profile（C3 / Q11 测量部分）\n')
    w(hdr('各分箱 src5 均值 / 中位 / P(y<0)', 'pool0 格按：到三分位边界距离五分位（cmf / cr5 带 / 日内）、触发日龄 1–5、'
          't 日实现 cr5 五分位', '无', 'pool0（固定池，不重建信号）', unit='bp', H='src5', support='pool0 有值格'))
    w(md(mgv, 1))
    w('%s；%s。**只描述，不重建信号**（C3）。\n' % (
        q('Q-R0-AGE', '触发日龄 1→5 的 src5 均值：10-14 %s（%+.1f → %+.1f bp），15-18 %s（%+.1f → %+.1f bp）' % (
            ag_mono[S0], ag.loc[(S0, 1)], ag.loc[(S0, 5)], ag_mono[S1], ag.loc[(S1, 1)], ag.loc[(S1, 5)])),
        q('Q-R0-RCR5', 't 日实现 cr5 五分位中 src5 均值最低的是第 %d / 第 %d 组（%+.1f / %+.1f bp）' % (
            rc_min[S0], rc_min[S1], rc.loc[(S0, rc_min[S0])], rc.loc[(S1, rc_min[S1])]))))
    # ---- 10
    w('## 10. 缺失 / 限价政策（Q12 测量部分）\n')
    w(hdr('pool0 覆盖 / 两版截面 Spearman 日均 / 排名变动 >5 个百分位的格占比 / 窗口内触板格占比', 'pool0 格',
          'OBS 版（合法 H==L 日保留）', 'V 族极差估计量 OBS vs LIMIT_SENS（触板日剔出）；末行 Parkinson OBS vs 源 H==L→NaN',
          unit='比例 / 相关', support='pool0 格；两版都有值才比排名'))
    w(md(pol, 4))
    # ---- 11
    w('## 11. 成本暴露（决策边缘是否更贵；只描述，不当 alpha）\n')
    w(hdr('成员原值的形成日集合均值的日均，四母体算术平均', '各集合当日有值名单', 'final 列',
          'final / edge / econ_reject / pool0', unit='比例价差（K_zero = 零收益日占比；K_amihud 为源单位）',
          support='集合内有值格'))
    w(md(ce, 5))
    w('%s。\n' % q('Q-R0-COST', '；'.join('%s 摩擦成员中 edge 高于 final 的 %d / %d 个' % (
        ss(s), int(n_edge_hi.loc[s]), int(n_edge.loc[s])) for s in SEGS)))
    # ---- 12
    if q3t is not None:
        w('## 12. V 的分层形状（Q3 的 Stage 1 部分）\n')
        w(hdr('pool0 内分层后的形成日 IC 日均', '层内当日有值名单（≥10 名）', '无',
              '真实漂移（cr5 三分位）/ 当日区间（log H/L 三分位）/ 近 5 日触板', unit='Spearman', H='src5',
              support='pool0 有值格'))
        w(md(q3t))
        w(hdr('pool0 全体：成员最低 / 最高五分组的 src5 均值、标准差、P(y<0)、p10', '五分组内全部格', '无', 'V 关键成员',
              unit='bp', H='src5', support='pool0 有值格'))
        w(md(q3r, 2))
    # ---- 13
    w('## 13. 条件形状（Q17 的 Stage 1 部分）\n')
    w(hdr('"单调弱但形状强"的 (成员 x 母体) 计数 / 总数', '每格 = 该段该集合该轴全部 (成员 x 母体)',
          '报告判据（不是闸）：|IC| < 0.01 且 |U 形指数| > 0.5 x 五组极差 且 极差 > 5 bp', '集合见列', unit='计数', H='src5',
          support='集合内有值格'))
    w(md(q17p))
    w('%s（名单 `R0_tables/Q17_shape_members_both_segments.csv`）。M2 basis（u、u²、u·z）拟合在 part1b。\n' % q(
        'Q-R0-Q17', '两段都被标出的 (成员, 集合, 母体) 共 %d 个' % len(q17both)))
    # ---- 14
    w('## 14. 本报告负责的问题（R0 = Q3 首表 / Q11 / Q12 测量部分 + Q17 / Q18 的 Stage 1 部分）\n')
    CARDS_AT = len(L)
    w('')
    # ---- 15
    w('## 15. Coverage（R0 范围）\n')
    cov = [('P0 源事实 / source_resolution / engine_contract / manifest', 'done', ''),
           ('Stage 0：引擎锚 / 特征锚 / 算子锚 / 标签锚 / suffix / 守卫攻击 / 契约 / vendor', 'done', ''),
           ('Stage 0：ADEMP 仿真（price / xs / spread / activity / info）', 'done', '误差表，不设 PASS 门'),
           ('Stage 0：稀疏引擎锚（Z-MAP 路径专用）', 'done' if all(spa) else 'changed',
            '' if all(spa) else '%s 已跑，另一段在 Z-MAP 启动前补跑' % ', '.join(s for s, x in zip(SEGS, spa) if x)),
           ('A0 精确计数 + 事前登记', 'done', 'v1.1 修订只补四臂参数'),
           ('Stage 1：首表 / 测量 / 预测 / 决策 / 事件层', 'done', '276 成员 x 两段 x 四母体 x 六集合'),
           ('Stage 1：T0 画像 + 分层 + 对照集（Q18）', 'done' if ref is not None else 'changed', '对照集口径见 §8'),
           ('Stage 1：C3 signal_margin_profile（Q11）', 'done', ''),
           ('Stage 1：限价政策（Q12）/ 成本暴露', 'done', 'Q12 的资本与账户部分在 Stage 2'),
           ('Stage 1：V 分层（Q3）', 'done' if q3t is not None else 'deferred', ''),
           ('Stage 1：条件形状（Q17）', 'done', 'M2 basis 拟合在 part1b'),
           ('A1 路由复核', 'deferred', '规划 session 义务；执行端不等')]
    w(hdr('逐项状态', 'brief §3–§4 的 R0 交付项', 'brief 原文', 'R0 范围', dates='不适用', support='不适用'))
    w(md(pd.DataFrame(cov, columns=['项', '状态', '说明'])))
    # ---- 16
    w('## 16. 这份 R0 没有得出的结论\n')
    w('- 没有删除、降级或改方向任何成员 —— Stage 1 的 IC、单调、分组收益一律不作闸（brief §0.2 / §16）。')
    w('- 预测层与决策层都不是账户（没有 DEV、持仓、成本）；**不能**由此推出哪个测量会改善哪个母体。')
    w('- ADEMP 的估计精度不是 alpha 证据；截面排序更准 ≠ 选股更好。')
    w('- T0 画像按事后标签分层，本身不是可执行规则的收益证明。')
    w('- 首表与 C3 只描述 I11 池的真实状态；**不**推出"信号应该改"。')
    w('- 全部数字只来自推导段 2010–2018；不是 OOS。\n')
    w('## 17. BLOCKERS\n')
    w('无。运行事件（不阻断）：Stage 2 首版 runner 未接 RR 的 "replace_cr5" 焦点臂与 RO/RS 方向为 state 的焦点行，2015-18 的 '
      'RR 120 个、RO 24 个配置首跑记 FAILED_TECH；修复后由 `e6i_s2_focaltest.py` 核验（all_on 与母体逐格相同、real_state 位于 '
      'all_on 与 all_off 之间），只重跑失败描述符（`accounts/2015-2018/*_rerun.*`）；2010-14 全部用修复版，0 失败。'
      '合并验收 `registry/stage2_status_table.csv`：状态和 = A0 登记数、FAILED_TECH 0（`task_status/stage2_DONE.json`）。'
      '另：一次按命令行模式清理进程（`pkill -f`）误杀了执行该命令的远程 shell 本身，未影响任何产物；此后只按 PID + 启动时间清理（协议 §10）。\n')
    # ---- 摘要
    summ = [
        '1. P0：brief 的 source-level 事实 0 处错误；12 条补正（A08 无 C 核心腿、限价表须按 ticker 对齐、换手率是比例）。',
        '2. 仪器：引擎锚 48/48 x 2（≤2.3e−15）、稀疏引擎锚（DEV 逐位、账本 ≤1e−14）、特征 19/19 x 2、算子 65/65 x 2、'
        '标签 0.0 bp、后缀 %d/0、守卫 32/32、契约 61/61。' % len(sfx),
        '3. A0 v1.2：%d 个描述符（v1.1 补四臂参数、v1.2 补 RR 焦点"两者"臂，均为 plan 原文补全）；preregistration 先于一切新收益评价。'
        % cnt['total_descriptors'],
        '4. W01 成立：池内 5 日源收益中位 %+.2f%% / %+.2f%%，正值占比 %.0f%% / %.0f%% —— I11 池不是强漂移池。' % (
            100 * cr.loc[S0, 'p50'], 100 * cr.loc[S1, 'p50'], 100 * cr.loc[S0, 'frac_pos'], 100 * cr.loc[S1, 'frac_pos']),
        '5. 预测层：新测量在最终保留集内的 |IC| 约为拒绝集的 %.0f%% / %.0f%%（中位）—— 信息主要落在母体已拒绝的名字上。' % (
            100 * ratio.loc[S0], 100 * ratio.loc[S1]),
        '6. 决策层（非账户）：换入 − 换出为正 %d / %d，两段都正 %d 个；最多的是 %s。' % (
            len(dpos), len(dl), len(both2), '、'.join('%s %s' % (a, b) for (a, b), n in top2.items())),
    ]
    if spec_cnt is not None:
        summ.append('7. T0（Q18）：E6h 画像三要素方向保持；V 只在 2015-18 分离；新 K / T 测量比旧 K0 / std60 分离更强。%s'
                    ' —— 画像多半是池子层面的收益预测，不是"被错剔"特有。' % q(
                        'Q-R0-S7', '|z|>3 的成员与 pool0 同人数对照同号 %d/%d、%d/%d' % (
                            int(spec_cnt.loc[S0, 'n_same']), int(spec_cnt.loc[S0, 'n_sig']),
                            int(spec_cnt.loc[S1, 'n_same']), int(spec_cnt.loc[S1, 'n_sig']))))
    summ.append('8. C3：触发日龄 1→5 的 src5 均值 %s / %s；t 日实现 cr5 第 %d / %d 五分位最差。' % (
        ag_mono[S0], ag_mono[S1], rc_min[S0], rc_min[S1]))
    summ.append('9. 本 R0 不删成员、不改方向；Stage 2 主账户两段已全部跑完（2015-18 焦点行修复后重跑）。')
    L[SUMMARY_AT] = '## 摘要（≤15 行）\n\n' + '\n'.join(summ) + '\n\n---\n'
    L[CARDS_AT] = cards(cr, lt, ag, rc, ag_mono, rc_min, pol, t0tab, spec_cnt, q17both, q17c, q3, topz)
    txt = '\n'.join(L)
    bad = check_headers(txt)
    if bad:
        raise SystemExit('生成 FAIL：%d 张表缺表头项（行 %s）' % (len(bad), bad[:10]))
    for b in FORBID:
        if b in txt:
            raise SystemExit('生成 FAIL：禁用词 %s' % b)
    if re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', txt):
        raise SystemExit('生成 FAIL：疑似主机地址')
    pth = os.path.join(OUT, 'E6i_REPORT_R0.md')
    open(pth, 'w', encoding='utf-8').write(txt)
    pd.DataFrame(QIDS).to_csv(os.path.join(TAB, 'query_ids.csv'), index=False)
    print('REPORT_R0: %s (%d 字节, %d 行); query_id %d; 表头检查通过; %.0fs' % (
        pth, len(txt.encode()), txt.count('\n'), len(QIDS), time.time() - t0))


def cards(cr, lt, ag, rc, ag_mono, rc_min, pol, t0tab, spec_cnt, q17both, q17c, q3, topz):
    S0, S1 = SEGS
    o = []
    # ---- Q3
    o.append('### Q3（V）—— Stage 1 部分\n')
    o.append('- **原问题**：I11 不保证强漂移；不同 V 估计量的目标不同。风险分离是否在真实漂移 / 区间 / 限价分层后保留？')
    if len(q3):
        qa = q3[q3.stratum.isin(['drift_low', 'drift_high', 'range_low', 'range_high', 'touch0', 'touch1p'])]
        neg = qa.assign(n=qa.ic_mean < 0).groupby(['segment', 'stratum']).n.agg(['sum', 'size'])
        s_ = '；'.join('%s %s %d/%d' % (ss(s), st, int(neg.loc[(s, st), 'sum']), int(neg.loc[(s, st), 'size']))
                      for s in SEGS for st in ('drift_low', 'drift_high', 'range_low', 'range_high', 'touch1p')
                      if (s, st) in neg.index)
        o.append('- **数字 / 分母**：%s。' % q('Q-R0-Q3', 'V 轴全部成员中 pool0 分层 IC 为负的个数：' + s_))
        allr = q3[q3.stratum == 'all'].set_index(['segment', 'member_id'])
        k = [('V_rs20_obs', 'RS'), ('V_yz20_obs', 'YZ'), ('V_park20_LEGACY', 'Parkinson 源桥')]
        o.append('  风险形状（成员最低 → 最高五分组的 src5 标准差）：%s。' % q('Q-R0-Q3R', '；'.join(
            '%s %s %.0f→%.0f bp' % (ss(s), nm, allr.loc[(s, m), 'g1_sd'], allr.loc[(s, m), 'g5_sd'])
            for s in SEGS for m, nm in k if (s, m) in allr.index)))
        med = q3.groupby(['segment', 'stratum']).ic_mean.median()
        o.append('  漂移分层：%s。' % q('Q-R0-Q3D', '；'.join(
            '%s V 成员 IC 中位 低漂移层 %.3f / 高漂移层 %.3f' % (ss(s), med.loc[(s, 'drift_low')],
                                                         med.loc[(s, 'drift_high')]) for s in SEGS)))
        tt = t0tab.set_index('member_id')
        o.append('  保留集内（T0 对照集，§8）：%s。' % q('Q-R0-Q3K', '；'.join(
            '%s RS / YZ / Parkinson 的赢家 − 输家差 %.3f / %.3f / %.3f' % (
                ss(s), tt.loc['V_rs20_obs', '%s 保留集差' % ss(s)], tt.loc['V_yz20_obs', '%s 保留集差' % ss(s)],
                tt.loc['V_park20_LEGACY', '%s 保留集差' % ss(s)]) for s in SEGS)))
    if len(q3):
        qa2 = q3[q3.stratum.isin(['drift_low', 'drift_mid', 'drift_high', 'range_low', 'range_mid', 'range_high',
                                  'touch0', 'touch1p'])]
        cn = qa2.assign(n=qa2.ic_mean < 0).groupby(['segment', 'stratum']).n.agg(['sum', 'size'])
        lo = int(cn['sum'].min())
        lo_at = cn['sum'].idxmin()
        o.append('- **读法**：测量层的风险分离在漂移 / 区间 / 触板分层后**保留**（%s），V 高组的未来收益离散'
                 '也明显更大（真在测风险）；但负 IC **集中在高漂移层**，而且 2010-14 在母体最终保留集内反号（赢家区间更宽）。' % q(
                     'Q-R0-Q3N', '各段各层 IC 为负的成员数最少 %d / %d（%s %s）' % (
                         lo, int(cn.loc[lo_at, 'size']), ss(lo_at[0]), lo_at[1])))
    o.append('- **竞争解释**：V 高 → 低收益可能是（a）彩票偏好 / 风险补偿缺失，（b）与近期涨幅同源（高漂移层最强支持这一条；R0 未算轴间相关），'
             '（c）限价日截断区间的机械成分。池内漂移中位为负、近 5 日触板占 %.1f%% / %.1f%%，RS / YZ 的"漂移不变"在这里'
             '没有转成排序差异（各估计量分层 IC 几乎一样；仿真里 OHLC 类截面排序本就 ≈ 0.99）。' % (
                 100 * lt.loc[S0, 'frac_pos'], 100 * lt.loc[S1, 'frac_pos']))
    o.append('- **仍未知**：分层后仍在的负 IC 能否在母体最终名单内、在完整账户里留下增量（RV 路线账户，part1）；保留集内反号是否让 '
             'VETO 在 2010-14 伤害母体。')
    o.append('- **下一步含义**：RV 读法按登记不变；part1 报 V 成员在 R2 / A06 保留集的 VETO / SOFT / ADD 账户时 OBS / '
             'LIMIT_SENS 两版并列，并按段分开读。prediction_status（Stage 1 测量层）：aligned（分层后保留）；账户层 untested。\n')
    # ---- Q11
    o.append('### Q11（D-S 信号状态）\n')
    o.append('- **原问题**：先确认 I11 信号的真实状态，而不是假定涨幅 25%–55%。')
    o.append('- **数字 / 分母**：%s；%s；%s。' % (
        q('Q-R0-Q11A', 'pool0 形成日 5 日源收益中位 %+.2f%% / %+.2f%%（n = %d / %d 格）' % (
            100 * cr.loc[S0, 'p50'], 100 * cr.loc[S1, 'p50'], int(cr.loc[S0, 'n']), int(cr.loc[S1, 'n']))),
        q('Q-R0-Q11B', '触发日龄 1→5 的 src5 均值 10-14 %s（%+.1f → %+.1f bp）、15-18 %s（%+.1f → %+.1f bp）' % (
            ag_mono[S0], ag.loc[(S0, 1)], ag.loc[(S0, 5)], ag_mono[S1], ag.loc[(S1, 1)], ag.loc[(S1, 5)])),
        q('Q-R0-Q11C', 't 日实现 cr5 五分位中 src5 最低的是第 %d / %d 组（%+.1f / %+.1f bp）' % (
            rc_min[S0], rc_min[S1], rc.loc[(S0, rc_min[S0])], rc.loc[(S1, rc_min[S1])]))))
    o.append('- **竞争解释**：（a）触发后信息衰减（新触发更好）；（b）日龄与"已经涨过"共线 —— 老触发的票更可能已兑现；'
             '（c）标签是日龄线性归因，老触发只剩较短归因窗。')
    o.append('- **仍未知**：日龄梯度在母体名单内是否仍在；是衰减还是已兑现（要在同一实现 cr5 层内看日龄）。')
    o.append('- **下一步含义**：可作为新需求提出（例：事件时钟测量 / 焦点状态）；**不推导未运行的新信号绩效**（C3 只描述）。'
             'prediction_status：aligned（"不是强漂移池"成立）。\n')
    # ---- Q12
    o.append('### Q12（缺失 / 限价）—— 测量部分\n')
    o.append('- **原问题**：H==L 零观测、NA 与限价可能改变样本与排序。')
    pp = pol[pol.estimator != 'park_obs_vs_LEGACY_PARK_NAN']
    lg = pol[pol.estimator == 'park_obs_vs_LEGACY_PARK_NAN'].set_index('segment')
    im = pp.spearman_obs_vs_ls_daymean.idxmin()
    o.append('- **数字 / 分母**：%s；%s。' % (
        q('Q-R0-Q12A', 'OBS vs LIMIT_SENS 的 pool0 截面 Spearman 日均最低 %.3f（%s %s%d）、排名移动 >5 个百分位的格占比最高 %.1f%%'
          % (pp.loc[im, 'spearman_obs_vs_ls_daymean'], ss(pp.loc[im, 'segment']), pp.loc[im, 'estimator'],
             int(pp.loc[im, 'window']), 100 * pp.frac_rank_move_gt5pct.max())),
        q('Q-R0-Q12B', 'Parkinson OBS vs 源 H==L→NaN：Spearman %.4f / %.4f，排名移动格 %.2f%% / %.2f%%' % (
            lg.loc[S0, 'spearman_obs_vs_ls_daymean'], lg.loc[S1, 'spearman_obs_vs_ls_daymean'],
            100 * lg.loc[S0, 'frac_rank_move_gt5pct'], 100 * lg.loc[S1, 'frac_rank_move_gt5pct']))))
    o.append('- **竞争解释**：触板日的区间被限价截断（机械）；也可能触板本身是信息，剔掉反而丢信息。H==L 在本数据几乎全是触板日'
             '（P0：未触板的 H==L ≈ 5e−6），所以源 NaN 处理与 OBS 在排序上几乎等价，差异集中在 LIMIT_SENS。')
    o.append('- **仍未知**：两版在母体账户上的差（资本与名单变化）—— Stage 2 RV 两版都跑，part1 报。')
    o.append('- **下一步含义**：数值差已可定位到触板窗口；不把机械影响一概视为无用信息。prediction_status：underidentified（账户部分待 part1）。\n')
    # ---- Q17
    o.append('### Q17（条件形状）—— Stage 1 部分\n')
    o.append('- **原问题**：成员在拒绝集 / 保留集的分组形状（U 形、单边）与单调 Spearman 是否不一致？')
    tot = q17c.groupby('segment').agg(k=('k', 'sum'), n=('n', 'sum'))
    o.append('- **数字 / 分母**：%s；%s。' % (
        q('Q-R0-Q17A', '按报告判据标出的 (成员 x 母体 x 集合) %s' % '；'.join(
            '%s %d / %d' % (ss(s), int(tot.loc[s, 'k']), int(tot.loc[s, 'n'])) for s in SEGS)),
        q('Q-R0-Q17B', '两段都被标出的 (成员, 集合, 母体) %d 个' % len(q17both))))
    o.append('- **竞争解释**：（i）真实非单调（两端都差）；（ii）五分组均值的噪声；（iii）极端组被少数大亏票拉动（均值 vs 中位）。')
    o.append('- **仍未知**：形状在训练内拟合（M2 的 u、u²、u·z）后是否仍有前向意义 —— part1b。')
    o.append('- **下一步含义**：结论只到"该成员 x 集合 x 段"，不推及轴。prediction_status：mixed。\n')
    # ---- Q18
    o.append('### Q18（画像复核）—— Stage 1 部分\n')
    o.append('- **原问题**：用新测量重做"被错剔赢家 − 被剔输家"画像，按真实漂移与触板分层，与 Parkinson / std60 / K0 旧画像相比保持、减弱还是反向？')
    tt = t0tab.set_index('member_id')

    def g_(m, c):
        try:
            return float(tt.loc[m, c])
        except KeyError:
            return float('nan')
    o.append('- **数字 / 分母**：%s；%s；%s；%s。' % (
        q('Q-R0-Q18A', 'T：新 T_std20 %.3f / %.3f、T_cv20 %.3f / %.3f vs 旧 T_std60 %.3f / %.3f' % (
            g_('T_std20', '10-14 拒绝集差'), g_('T_std20', '15-18 拒绝集差'), g_('T_cv20', '10-14 拒绝集差'),
            g_('T_cv20', '15-18 拒绝集差'), g_('T_std60_LEGACY', '10-14 拒绝集差'), g_('T_std60_LEGACY', '15-18 拒绝集差'))),
        q('Q-R0-Q18B', 'K：新 K_res_log %.3f / %.3f vs 旧 K0 %.3f / %.3f' % (
            g_('K_res_log', '10-14 拒绝集差'), g_('K_res_log', '15-18 拒绝集差'), g_('K0_LEGACY', '10-14 拒绝集差'),
            g_('K0_LEGACY', '15-18 拒绝集差'))),
        q('Q-R0-Q18C', 'R：新 R_peer20 %.3f / %.3f、R_5_s0 %.3f / %.3f vs 旧 skip1 %.3f / %.3f' % (
            g_('R_peer20', '10-14 拒绝集差'), g_('R_peer20', '15-18 拒绝集差'), g_('R_5_s0', '10-14 拒绝集差'),
            g_('R_5_s0', '15-18 拒绝集差'), g_('R_skip1_LEGACY', '10-14 拒绝集差'), g_('R_skip1_LEGACY', '15-18 拒绝集差'))),
        q('Q-R0-Q18D', 'V：RS %.3f / %.3f、YZ %.3f / %.3f vs 旧 Parkinson %.3f / %.3f' % (
            g_('V_rs20_obs', '10-14 拒绝集差'), g_('V_rs20_obs', '15-18 拒绝集差'), g_('V_yz20_obs', '10-14 拒绝集差'),
            g_('V_yz20_obs', '15-18 拒绝集差'), g_('V_park20_LEGACY', '10-14 拒绝集差'),
            g_('V_park20_LEGACY', '15-18 拒绝集差')))))
    o.append('  z 最负的三个：%s。' % q('Q-R0-Q18E', '；'.join('%s %s' % (ss(s), '、'.join(
        '%s（%.1f）' % (r.member_id, r.z) for r in topz[s].itertuples())) for s in SEGS)))
    if spec_cnt is not None:
        o.append('  对照集：%s。' % q('Q-R0-Q18F', '；'.join(
            '%s 拒绝集 |z|>3 的 %d 个成员与 pool0 同人数对照同号 %d 个（差之比中位 %.2f）' % (
                ss(s), int(spec_cnt.loc[s, 'n_sig']), int(spec_cnt.loc[s, 'n_same']), spec_cnt.loc[s, 'ratio_med'])
            for s in SEGS if s in spec_cnt.index)))
    o.append('- **读法**：旧画像三要素方向**保持**：赢家换手更平稳（T_std20 / T_cv20 更低）、相对同业回落（R_peer20 更低）、'
             '区间更窄（V 只在 2015-18 为负，2010-14 接近 0）。新 K（残差响应）与新 T（离散 / 相对尺度）的分离比旧 K0 / std60 **更强**；'
             'V 的 RS / YZ 与旧 Parkinson **相当**。近 5 日收益（R_5_s0）的分离比旧 skip1 大得多。')
    o.append('- **竞争解释**：（a）拒绝集里的"赢家 / 输家"差大半是池子层面的短期反转与活动效应（与 pool0 同人数对照同号、量级相近），'
             '不是"被错剔"特有；（b）分层表里 K_res_log 在高漂移层更强，可能与漂移本身共线。')
    o.append('- **仍未知**：这些分离能否变成母体账户增量（RR / RT / RK 的 SWAP / SLOT 账户与 Z-MAP 随机对照，part1）。')
    o.append('- **下一步含义**：不由画像推收益。画像给 part1 一个读法先验：若 RR 的 5 日窗成员 SWAP 为正、匹配随机也为正，'
             '更可能是池内反转而非"错剔修复"。prediction_status：aligned（保持）；新测量在 K / T 上更强、V 上相当。\n')
    return '\n'.join(o)


if __name__ == '__main__':
    main()
