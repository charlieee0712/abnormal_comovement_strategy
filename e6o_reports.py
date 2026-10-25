# -*- coding: utf-8 -*-
"""E6o 报告（brief §8 第 1 条；附录 B.15）。数字只从机器表取（statistics / diagnostics / verify / registration / events），报告正文不出现字面 nan / None。
每张表首行写 主体 / 算子 / 分母 / 基准 / 子集 / 单位（纪律 ㉚）。每页页首：协议 v1.6、方式 B、无 E7 读取、deployment_authorized = false。
用法：python3 e6o_reports.py [--root <目录>]（默认结果目录；空跑时 --root tmp/dryrun）"""
import os
import re
import sys
import json
import glob
import math
import argparse

import numpy as np
import pandas as pd

import e6o_core as O

HDR = ('> 协议 v1.6 · 方式 B（用户转交 brief = 开工与方式 B 授权）· 未读 E7（> 2026-03-27）· deployment_authorized = false · 生产配置 / I11 / U34 / U35 / 候选库未动 · '
       'plan v1.1（ce9e98c2）· 数据 2010-01-04 … 2026-03-27\n')
SEG4 = list(O.SEGS)


def f(x, nd=3):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return str(x) if str(x) not in ('nan', 'None', '') else '—'
    if not np.isfinite(x):
        return '—'
    return ('%.' + str(nd) + 'f') % x


def md(df, cols=None, nd=3, maxrows=None):
    cols = cols or list(df.columns)
    d = df[cols] if maxrows is None else df[cols].head(maxrows)
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '|'.join(['---'] * len(cols)) + '|']
    for _, r in d.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append(f(v, nd))
            else:
                s = str(v)
                cells.append('—' if s in ('nan', 'None', '') else s.replace('|', '/').replace('\n', ' '))
        out.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(out)


def thead(name, body, unit, op, den, base, sub, src):
    return '**%s**　主体：%s；算子：%s；分母：%s；基准：%s；子集：%s；单位：%s　（机器表 `%s`）\n\n' % (name, body, op, den, base, sub, unit, src)


def short(e):
    p = e.split('|')
    if len(p) != 16:
        return e
    return '%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s' % (p[0], p[2], p[3], p[4], p[5], p[6], p[7], p[8], 'G' + p[9] + 'X' + p[10], p[11][:5], p[13][:4])


def write(root, name, text):
    p = os.path.join(root, 'reports', name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    hits = re.findall(r'.{0,30}(?<![A-Za-z_])(?:nan|None)(?![A-Za-z_]).{0,30}', text)        # 与 D 脚本 S22 同正则
    if hits:
        raise RuntimeError('报告 %s 含字面 nan / None：%s' % (name, hits[:3]))
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        fh.write(text)
    os.replace(tmp, p)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    root = a.root or O.work()
    rd = lambda rel: pd.read_csv(os.path.join(root, rel), keep_default_na=False, na_values=[''])
    rdw = lambda rel: pd.read_csv(O.P(rel), keep_default_na=False, na_values=[''])
    R = rdw('registration/registry_E6o.csv')
    reg = R.set_index('exec_id')
    AS = rd('statistics/account_summary_E6o.csv')
    asi = AS.set_index(['exec_id', 'segment'])
    RT = rd('statistics/randoms_E6o.csv')
    PO = rd('statistics/policy_E6o.csv')
    M72 = rd('statistics/main72_E6o.csv')
    EV = rd('events/event_counts_E6o.csv')
    S0 = rdw('diagnostics/stage0_E6o.csv')
    IDN = rdw('verify/identities_E6o.csv') if os.path.exists(O.P('verify', 'identities_E6o.csv')) else rdw('verify/identities_E6o_stage0.csv')
    G1 = rdw('diagnostics/G1_E6o.csv')
    CL = rd('reports/claims_E6o.csv') if os.path.exists(os.path.join(root, 'reports', 'claims_E6o.csv')) else pd.DataFrame()
    facts = json.load(open(O.P('registration', 'registry_facts_E6o.json')))
    main_f = R[(R.series == 'C_ACCOUNT') & (R.is_main_object == 1) & (R.execution_profile == 'FEASIBLE_DAILY')].exec_id.iloc[0]
    main_i = main_f.replace('|FEASIBLE_DAILY|', '|IDEALIZED_SOURCE_FILL|')

    def D(e, s='FULL', c='D_ann_pp'):
        try:
            return float(asi.loc[(e, s), c])
        except (KeyError, ValueError, TypeError):
            return np.nan

    out = []
    # ======================= R0
    t = ['# E6o 报告 R0：Stage 0 与 A1（源合同、数据、两层父、恒等、攻击样例、资源）\n', HDR]
    s00 = S0[S0.probe_id == 'S0-0'][['key', 'value', 'note']]
    t.append('## 1. S0-0 源合同绑定\n')
    t.append(thead('E6O-R0-S00', 'S0-0 键', 'count', '读函数体登记', '—', '源代码（只 import）', 'probe_id = S0-0', 'diagnostics/stage0_E6o.csv'))
    t.append(md(s00, ['key', 'value', 'note']) + '\n')
    t.append('\n## 2. S0-2 两层无退出父、源锚与会计桥\n')
    idn0 = IDN[IDN.check_id.isin(['SOURCE_REPLICATION', 'SOURCE_ANCHOR_FRONTIER', 'NOEXIT_EQ_PARENT', 'ACCOUNTING_BRIDGE', 'CASH_EQUATION', 'NAV_TELESCOPE'])]
    t.append(thead('E6O-R0-S02', '恒等与锚', '见列', '逐日 / 段', '各行描述', 'P_SOURCE / P_ACCOUNT', 'check_id ∈ 源与会计类', 'verify/identities_E6o.csv'))
    t.append(md(idn0, ['check_id', 'description', 'value', 'max_abs_diff', 'tolerance', 'status'], nd=6) + '\n')
    br = rdw('diagnostics/stage0_accounting_bridge_E6o.csv')
    t.append('\n' + thead('E6O-R0-BRIDGE', '会计桥（全部 24 坐标 × 四段）', 'ann_pp', 'P_ACCOUNT − P_SOURCE（IDEAL 桥）；FEASIBLE − IDEAL（成交约束）', '各段日均 × 252 × 100',
                          'P_SOURCE（固定滚动权重源账本）', '主母体 H5 三记忆（全部见机器表）', 'diagnostics/stage0_accounting_bridge_E6o.csv'))
    t.append(md(br[(br.form == O.MAIN_FORM) & (br.H == 5)], ['memory', 'segment', 'P_SOURCE', 'P_ACCOUNT_IDEAL', 'P_ACCOUNT_FEASIBLE', 'BRIDGE_IDEAL', 'BRIDGE_FEASIBLE']) + '\n')
    t.append('\n会计桥不是退出增量：P_SOURCE 是固定滚动目标权重乘收益、按权重差收费；P_ACCOUNT 是自融资现金账户（持仓随价格漂移、复牌跳价计入、费用记在成交日、从 CASH_V0 连续建仓、段首不重置）。'
             '本轮所有退出比较的主差都是 C_ACCOUNT − 同引擎同情景同支持的 P_ACCOUNT（MAIN_EXIT）。\n')
    t.append('\n## 3. S0-3 / S0-4 / S0-6 数据与触发事实\n')
    s03 = S0[S0.probe_id.isin(['S0-3'])][['key', 'value', 'note']]
    t.append(thead('E6O-R0-S03', 'VWAP 恒等与触发重叠', 'ratio', '份额', '股票日', '日频 vwap / 分钟额量', '按年 × 交易所', 'diagnostics/stage0_E6o.csv'))
    t.append(md(s03, ['key', 'value', 'note']) + '\n')
    s04 = S0[S0.probe_id.isin(['S0-4', 'S0-5', 'S0-9', 'S0-10', 'S0-11', 'S0-12', 'S0-13'])][['probe_id', 'key', 'value', 'note']]
    t.append('\n' + thead('E6O-R0-S04-13', 'S0-4…S0-13 键', '见键', '见注', '见注', '见注', 'probe_id ∈ S0-4…S0-13', 'diagnostics/stage0_E6o.csv'))
    t.append(md(s04, ['probe_id', 'key', 'value', 'note']) + '\n')
    t.append('\n## 4. S0-7 / S0-8 攻击样例\n')
    att = IDN[IDN.check_id.isin(['REENTRY_EPISODE_CASES', 'TICKET_DOUBLE_SPEND', 'TICKET_MATURITY_REUSE', 'JOURNAL_REPLAY', 'WRONG_MOTHER_MERGE', 'FUTURE_DATA_PLANT', 'UNIT_PLANT'])]
    t.append(thead('E6O-R0-ATTACK', '攻击样例', 'count', '植入 → 是否被拦', '—', '—', '七类', 'verify/identities_E6o.csv'))
    t.append(md(att, ['check_id', 'description', 'value', 'status']) + '\n')
    t.append('\n## 5. A1 冻结与执行展开\n')
    fz = json.load(open(O.P('registration', 'freeze_E6o.json')))
    t.append('- 冻结件 `registration/freeze_E6o.json`（%s）：协议 %s、方式 %s；SOURCE_T1B = %s；源现金模型 = %s。\n' % (fz['written_at'], fz['protocol'], fz['mode'], fz['source_t1b_binding'], fz['source_cash_model']))
    t.append('- 执行展开：C_ACCOUNT %d（逻辑 %d × 2 情景）；P_ACCOUNT %d（24 坐标 × 2 情景 × 2 支持）；P_SOURCE %d（24 坐标 × 2 支持）；72 主展示；主对象每情景 1 行。\n' % (
        facts['C_ACCOUNT'], facts['logical'], facts['P_ACCOUNT'], facts['P_SOURCE']))
    t.append('- 家族计数（FEASIBLE）：%s。\n' % '、'.join('%s %d' % (k, v) for k, v in sorted(facts['families_feasible'].items())))
    t.append('- 比较图 %d 条（MAIN_EXIT %d）；spec 比较边 %d 条全部映射（B.2 词表之外的 %d 条在 `registration/comparisons_extra_E6o.csv`）。\n' % (
        facts['comparisons'], facts['comparisons_by_kind']['MAIN_EXIT'], facts['spec_edges'], facts['comparisons_extra']))
    t.append('- A1 之后的技术缺陷修复（无经济规则变动）见 `E6o_code_change_register.md` §2；全部 A2 账户 / 随机在最终引擎上重跑后才封存。\n')
    out.append(write(root, 'E6o_REPORT_R0.md', ''.join(t)))
    # ======================= part1：A2 推导段与 G1
    t = ['# E6o 报告 part1：A2 推导段（G1 第一道 probe 与推导段账户）\n', HDR]
    sa = json.load(open(O.P('registration', 'seal_A2.json'))) if os.path.exists(O.P('registration', 'seal_A2.json')) else {}
    t.append('封存：`registration/seal_A2.json` written_at = %s，%s 个文件；推导段 = 2010-01-04 … 2018-12-31。G1 只用批次原 due 早于 2019-01-01 的影子批次，前向窗口不跨入后段。\n\n' % (
        sa.get('written_at', '—'), sa.get('n_files', '—')))
    gg = G1[(G1.key1 == 'ALL') & G1['item'].str.endswith('|HG10')]
    piv = gg.pivot_table(index=['item', 'segment'], columns='stat', values='value', aggfunc='first').reset_index()
    cols = [c for c in ('item', 'segment', 'n_events', 'mean_rem_due_bp', 'diff_vs_sameday_bp', 'diff_vs_levelworst_bp', 'h1_diff_bp', 'h3_diff_bp', 'h5_diff_bp', 'contrib_diff_ann_pp') if c in piv.columns]
    t.append(thead('E6O-P1-G1', '主母体 HG10 H5 父影子批次的首触发事件', 'bp（每事件）/ ann_pp（贡献）', '剩余超额至原 due；同日同日龄对照差；同组按日 CVR 最差同数对照差；独立 H1 / H3 / H5 窗',
                   '事件数 / 段日数', '同日同日龄全部风险集批次', '推导段两段；三记忆与分层见机器表', 'diagnostics/G1_E6o.csv'))
    t.append(md(piv, cols, nd=2) + '\n')
    d72 = AS[AS.exec_id.isin(M72.exec_id) & AS.segment.isin(['2010-2014', '2015-2018'])]
    p72 = d72.pivot_table(index='exec_id', columns='segment', values='D_ann_pp').reset_index()
    p72['对象'] = p72.exec_id.map(short)
    t.append('\n' + thead('E6O-P1-DERIV72', '72 主展示（FEASIBLE）推导段 D', 'ann_pp', 'C_ACCOUNT − P_ACCOUNT 日差均值 × 252 × 100', '各段共同日', '同引擎同情景无退出父',
                          'is_primary72', 'statistics/account_summary_E6o.csv'))
    t.append(md(p72, ['对象', '2010-2014', '2015-2018']) + '\n')
    out.append(write(root, 'E6o_REPORT_part1.md', ''.join(t)))
    # ======================= part2：主结果
    t = ['# E6o 报告 part2：主对象、72 主展示与各家族（全程，两后段在 seal_A2 之后计算）\n', HDR]
    rows = []
    for e in (main_f, main_i):
        for s in SEG4 + ['FULL', 'G4']:
            if (e, s) in asi.index:
                r = asi.loc[(e, s)]
                rows.append(dict(情景=reg.loc[e, 'execution_profile'][:8], 段=s, n=r.n_days, net=r.net_ann_pp, 父net=r.parent_net_ann_pp, D=r.D_ann_pp, boot_lo=r.boot_lo,
                                 boot_hi=r.boot_hi, se_H=r.hac_se_H, D_源=r.D_source_ann_pp, D_sc=r.D_sc_ann_pp, D_冲击=r.D_imp_ann_pp, 敞口=r.exposure_mean,
                                 换手=r.turnover_ann, 意向=r.n_exit_intents))
    t.append(thead('E6O-P2-MAIN', '主对象 A4b_CVRv5 / Q0 α .25 / HG10 / H5 / T1b / ENGINE_NATIVE / ALLOW', 'ann_pp', '逐日差均值 × 252 × 100；FULL = n 加权；G4 = 四段中位',
                   '共同日', '同引擎同情景无退出 P_ACCOUNT（D_源：P_SOURCE）', '两情景', 'statistics/account_summary_E6o.csv'))
    t.append(md(pd.DataFrame(rows), nd=3) + '\n')
    rm = RT[(RT.owner_exec_id == main_f) & (RT.segment == 'FULL')]
    t.append('\n' + thead('E6O-P2-MAIN-RAND', '主对象随机与水平控制', 'ann_pp', '路径 D 均值 / 标准差 / MCSE / 真值在路径中的位次', '路径数', '同父', 'FULL', 'statistics/randoms_E6o.csv'))
    t.append(md(rm, ['mechanism', 'paths', 'real_D_ann_pp', 'rand_mean_D_ann_pp', 'rand_sd_D_ann_pp', 'mcse', 'rank_real', 'unmatched_share', 'status'], nd=4) + '\n')
    m72 = M72.copy()
    m72['对象'] = m72.exec_id.map(short)
    t.append('\n' + thead('E6O-P2-72', '72 主展示（4 主触发 × 6 形态 × 3 记忆；H5 / NATIVE / ALLOW / FEASIBLE）', 'ann_pp', 'C − P_ACCOUNT', '共同日', '同引擎无退出父', 'is_primary72',
                          'statistics/main72_E6o.csv'))
    t.append(md(m72, ['对象', 'FULL_D_ann_pp', 'G4_D_ann_pp', 'D_2010-2014', 'D_2015-2018', 'D_2019-2023', 'D_2024-2026', 'rank_vs_random', 'verdict', 'research_status']) + '\n')
    core = R[(R.series == 'C_ACCOUNT') & (R.family == 'CORE') & (R.form == O.MAIN_FORM) & (R.H == 'H5') & (R.execution_profile == 'FEASIBLE_DAILY')]
    rows = []
    for tr, g in core.groupby('trigger'):
        row = dict(触发=tr)
        for fd in ('ENGINE_NATIVE', 'CASH'):
            for re_ in ('ALLOW', 'BLOCK'):
                x = g[(g.funding == fd) & (g.reentry == re_) & (g.memory == 'HG10')]
                row['%s/%s' % (fd[:6], re_)] = D(x.exec_id.iloc[0]) if len(x) else np.nan
        x = g[(g.funding == 'ENGINE_NATIVE') & (g.reentry == 'ALLOW')]
        row['三记忆中位 NATIVE/ALLOW'] = float(np.nanmedian([D(e) for e in x.exec_id])) if len(x) else np.nan
        rows.append(row)
    t.append('\n' + thead('E6O-P2-CORE17', '主母体 H5 CORE 17 支（HG10；资金 × 重入）', 'ann_pp', 'FULL D', '共同日', '同引擎无退出父', 'FEASIBLE', 'statistics/account_summary_E6o.csv'))
    t.append(md(pd.DataFrame(rows), nd=3) + '\n')
    fam_rows = []
    for fam, g in R[(R.series == 'C_ACCOUNT') & (R.execution_profile == 'FEASIBLE_DAILY')].groupby('family'):
        v = np.array([D(e) for e in g.exec_id])
        ok = np.isfinite(v)
        fam_rows.append(dict(家族=fam, 行数=len(g), FULL_D中位=float(np.median(v[ok])) if ok.any() else np.nan, FULL_D最小=float(v[ok].min()) if ok.any() else np.nan,
                             FULL_D最大=float(v[ok].max()) if ok.any() else np.nan, 为正份额=float((v[ok] > 0).mean()) if ok.any() else np.nan))
    t.append('\n' + thead('E6O-P2-FAMILY', '各家族 FEASIBLE FULL D 分布', 'ann_pp', '中位 / 最小 / 最大 / 为正份额（族中位与主对象分列）', '家族内对象', '各自同引擎无退出父', 'FEASIBLE',
                          'statistics/account_summary_E6o.csv'))
    t.append(md(pd.DataFrame(fam_rows)) + '\n')
    out.append(write(root, 'E6o_REPORT_part2.md', ''.join(t)))
    # ======================= part3：政策与研究状态
    t = ['# E6o 报告 part3：POLICY_E6O_PARENT_Q、E6O_RESEARCH_STATUS 与 PARTIAL_HISTORY_RESEARCH_V1\n', HDR]
    pp = json.load(open(O.P('registration', 'policy_profile_E6o.json')))
    t.append('规则（A1 冻结，`registration/policy_profile_E6o.json`）：%s。研究状态不是资格门。\n\n' % pp['verdict_rule'])
    cnt = PO.groupby(['profile_name', 'execution_profile', 'verdict']).size().reset_index(name='n')
    t.append(thead('E6O-P3-COUNT', '政策判定计数', 'count', '计数', 'C_ACCOUNT × 情景', '—', 'profile × 情景', 'statistics/policy_E6o.csv'))
    t.append(md(cnt) + '\n')
    rs = PO.groupby(['profile_name', 'execution_profile', 'research_status']).size().reset_index(name='n')
    t.append('\n' + thead('E6O-P3-RS', '研究状态计数', 'count', '计数', 'C_ACCOUNT × 情景', '—', 'profile × 情景', 'statistics/policy_E6o.csv'))
    t.append(md(rs) + '\n')
    passers = PO[(PO.verdict == '通过')].copy()
    passers['对象'] = passers.exec_id.map(short)
    passers['FULL_D'] = [D(e) for e in passers.exec_id]
    t.append('\n' + thead('E6O-P3-PASS', '判"通过"的对象', 'ann_pp / flag', '六条 + PORT3_T 全过', '—', '同引擎无退出父', 'verdict = 通过', 'statistics/policy_E6o.csv'))
    t.append(md(passers.sort_values('FULL_D', ascending=False), ['对象', 'profile_name', 'FULL_D', 'c2_year_positive_share', 'port3t_dev_pp', 'research_status'], maxrows=80) + '\n')
    pm = PO[PO.exec_id.isin([main_f, main_i])]
    t.append('\n' + thead('E6O-P3-MAIN', '主对象政策行', 'flag', '逐条', '—', '同引擎无退出父', '主对象', 'statistics/policy_E6o.csv'))
    t.append(md(pm, ['execution_profile', 'profile_name', 'c1_segment_tolerance_ok', 'c2_year_positive_share', 'c2_ok', 'c3_full_sc_same_sign', 'c4_random_post_ok', 'c5_impact_ok',
                     'port3t_dev_pp', 'port3t_ok', 'positive_ok', 'verdict', 'research_status']) + '\n')
    out.append(write(root, 'E6o_REPORT_part3.md', ''.join(t)))
    # ======================= mechanisms
    t = ['# E6o 报告 mechanisms：会计桥、情景桥、资金去向、重入、入场 × 退出、事件与诊断块\n', HDR]
    pairs = [('FUNDING：CASH − NATIVE', '|CASH|NA|NA|', '|ENGINE_NATIVE|lag1|RESET_H|'), ('FUNDING：NEXT − NATIVE', '|NEXT_RANK|lag1|RESET_H|', '|ENGINE_NATIVE|lag1|RESET_H|'),
             ('FUNDING：lag0 − lag1', '|ENGINE_NATIVE|lag0|RESET_H|', '|ENGINE_NATIVE|lag1|RESET_H|'), ('FUNDING：ORIGINAL_DUE − RESET_H', '|ENGINE_NATIVE|lag1|ORIGINAL_DUE|', '|ENGINE_NATIVE|lag1|RESET_H|')]
    rows = []
    fe = R[(R.series == 'C_ACCOUNT') & (R.execution_profile == 'FEASIBLE_DAILY')]
    ids = set(fe.exec_id)
    for name, a_, b_ in pairs:
        diffs = []
        for e in fe.exec_id:
            if a_ in e:
                e2 = e.replace(a_, b_)
                if e2 in ids:
                    diffs.append(D(e) - D(e2))
        v = np.array(diffs)
        ok = np.isfinite(v)
        rows.append(dict(比较=name, 对数=int(ok.sum()), 中位=float(np.median(v[ok])) if ok.any() else np.nan, 为正份额=float((v[ok] > 0).mean()) if ok.any() else np.nan))
    for name, a_, b_ in (('REENTRY：BLOCK − ALLOW', '|BLOCK|', '|ALLOW|'), ('REENTRY：RECONFIRM − BLOCK', '|RECONFIRM|', '|BLOCK|'), ('REENTRY：RECONFIRM − ALLOW', '|RECONFIRM|', '|ALLOW|'),
                         ('情景：FEASIBLE − IDEALIZED', '|FEASIBLE_DAILY|', '|IDEALIZED_SOURCE_FILL|')):
        diffs = []
        pool = R[R.series == 'C_ACCOUNT'].exec_id
        for e in pool:
            if a_ in e:
                e2 = e.replace(a_, b_)
                if e2 in reg.index:
                    diffs.append(D(e) - D(e2))
        v = np.array(diffs)
        ok = np.isfinite(v)
        rows.append(dict(比较=name, 对数=int(ok.sum()), 中位=float(np.median(v[ok])) if ok.any() else np.nan, 为正份额=float((v[ok] > 0).mean()) if ok.any() else np.nan))
    t.append(thead('E6O-MECH-PAIRS', '配对比较（同其余字段）', 'ann_pp', 'FULL D 之差', '配对数', '各自同引擎无退出父', 'FEASIBLE（情景桥：全部）', 'statistics/account_summary_E6o.csv'))
    t.append(md(pd.DataFrame(rows), nd=4) + '\n')
    ee = EV.copy()
    ee['对象'] = ee.exec_id.map(short)
    t.append('\n' + thead('E6O-MECH-EVENTS', '事件计数（主对象坐标族）', 'count', '计数；均持 = 早退实现批次持有交易日', '—', '—', '主对象 form / 记忆 / H / T1b', 'events/event_counts_E6o.csv'))
    sel = ee[ee.exec_id.str.startswith('%s|a0.25|HG10|H5|T1b|' % O.MAIN_FORM)]
    t.append(md(sel, ['对象', 'n_intents', 'n_realized_early', 'n_late_fill', 'n_unfilled', 'n_censored', 'n_reentry_blocked', 'n_reentry_reconfirmed', 'n_internal_transfers',
                      'mean_realized_hold_days', 'median_realized_hold_days']) + '\n')
    for blk, nm, title in (('D1', 'D1_size_dose_E6o', 'D-1 剂量 × size'), ('D2', 'D2_age_weight_E6o', 'D-2 日龄 / 权重'), ('D3', 'D3_capacity_E6o', 'D-3 成本 / 容量'),
                           ('D4', 'D4_regime_E6o', 'D-4 近段读法'), ('D5', 'D5_veto_exit_E6o', 'D-5 入场否决 × 退出'), ('D6', 'D6_minute_kleg_E6o', 'D-6 分钟 K 活动分布')):
        p = O.P('diagnostics', nm + '.csv')
        if not os.path.exists(p):
            continue
        dfb = pd.read_csv(p, keep_default_na=False, na_values=[''])
        t.append('\n## %s\n\n' % title)
        t.append(thead('E6O-MECH-%s' % blk, title, '见 unit 列', '见 stat 列', '见 n 列', '见 item', '全表前 40 行（全表见机器表）', 'diagnostics/%s.csv' % nm))
        t.append(md(dfb, ['item', 'key1', 'key2', 'segment', 'stat', 'value', 'unit', 'n', 'status'], nd=4, maxrows=40) + '\n')
    out.append(write(root, 'E6o_REPORT_mechanisms.md', ''.join(t)))
    # ======================= carried / cards
    if len(CL):
        t = ['# E6o 报告 carried：CC 原预测携带（原句逐字）与 G-F2 三条形成链\n', HDR]
        cc = CL[CL.kind.isin(['CC_CARRIED', 'G_CHAIN'])]
        t.append(thead('E6O-CAR-CC', 'CC-01…12 与 G-F2-01…03', '见 note', '照原句评分；不可比者 NOT_TESTED_AS_WRITTEN / REPLACED_BEFORE_RUN', '—', '—', 'kind ∈ {CC_CARRIED, G_CHAIN}', 'reports/claims_E6o.csv'))
        t.append(md(cc, ['claim_id', 'statement', 'claim_status', 'result_value', 'note'], nd=4) + '\n')
        out.append(write(root, 'E6o_REPORT_carried.md', ''.join(t)))
        t = ['# E6o 问题卡 Q01–Q18 与经济预测 E01–E07（每条绑定机器 query）\n', HDR]
        qq = CL[CL.kind.isin(['QUESTION', 'PREDICTION'])]
        t.append('只有 E01–E07 是本版明确的经济方向预测（进经济命中率分母）；Q 卡是问题 / 技术核验（plan §12）。区间 = 配对日差 stationary bootstrap（2,000 次、块长 20）。\n\n')
        t.append(thead('E6O-CARDS', 'Q01–Q18、E01–E07', '见 note', '见各自 query', '—', '—', 'kind ∈ {QUESTION, PREDICTION}', 'reports/claims_E6o.csv'))
        t.append(md(qq, ['claim_id', 'query_id', 'claim_status', 'result_value', 'result_sign', 'ci_lo', 'ci_hi', 'note'], nd=4) + '\n')
        out.append(write(root, 'E6o_cards.md', ''.join(t)))
    print(json.dumps(dict(reports=[os.path.basename(p) for p in out]), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
