# -*- coding: utf-8 -*-
"""E6q 报告（brief §8.1：R0 / 主结果 / 政策 / 机制 / 两账本复盘 / limit register）。
数字只从机器表取（statistics / diagnostics / events / reports/claims / verify）；不写字面 nan / None（缺失写 —）；不写登录信息、主机标识或用户目录；
读法纪律：主对象差与族分布分列、两推导段符号旁印、结论带角色标签（卖出侧 / 再投侧 / 参照 / 读法），不替决策端下结论。
用法：python3 e6q_reports.py [--root <相对 E6Q_WORK 的根>]"""
import os
import json
import glob
import argparse

import numpy as np
import pandas as pd

import e6q_core as O

SEG4 = list(O.SEGS)
AUTH_TXT = ('main_A_cny = 100000000（1 亿主读）；sub_A_cny = [50000000, 500000000]；research_metric = EXCESS_SCALED_BENCHMARK；product_metric = TOTAL_RETURN_AND_MAX_DRAWDOWN；'
            'frontier_anchor_logical_id = E6Q-9f826422e6d4c39c（FRONTIER_E6P_T1A_H20）；mainline = sell_reinvest_split；deployment_authorized = false；e7 = HOLD')
HEADER = ('> **页首声明**：E6q 执行交付（协议 **v1.6**、**方式 B**；brief 655d9e9e / 附录 7997d462 / plan v1.1 86c246dd / 合同脚本 2ad9d86e / D 脚本 d64c1009 / proposal v1.4 ece038ea）。'
          '市场历史截止 2026-03-27；**E7 不做（e7 = HOLD，不读）**；**deployment_authorized = false**；生产配置 / I11 事件定义 / 观察窗 / K/T/C/Q 原测量 / 候选库不动。'
          '授权八值（用户 2026-10-22 消息，决策端转交）：' + AUTH_TXT + '。S0-A 两实现对账 = RECONCILED（canonical 仪器 = curve：κA^δ，同节点 V⁺_{e−1}）。'
          '连续全历史（CASH_V0）为主，四段重置（WARM）只作主对象对与父的敏感性。数字全部来自机器表；结论带角色标签，不替决策端下结论。\n')


def f2(x, d=2):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return '—' if (x is None or str(x).strip() in ('', 'nan', 'None', 'NaN')) else str(x)
    if not np.isfinite(v):
        return '—'
    return ('%.' + str(d) + 'f') % v


def fs(x, d=2):
    s = f2(x, d)
    return s if s == '—' or s.startswith('-') else '+' + s


NANW = __import__('re').compile(r'(?<![A-Za-z_])(nan|None|NaN)(?![A-Za-z_])')


def cell(v):
    if isinstance(v, (float, np.floating)):
        return f2(v)
    s = str(v)
    if s.strip() in ('', 'nan', 'None', 'NaN'):
        return '—'
    return NANW.sub('—', s.replace('|', '/').replace('\n', ' '))


def md_table(df, cols, heads=None):
    heads = heads or cols
    out = ['| ' + ' | '.join(heads) + ' |', '|' + '---|' * len(heads)]
    for r in df[cols].itertuples(index=False):
        out.append('| ' + ' | '.join(cell(v) for v in r) + ' |')
    return '\n'.join(out)


def short(e):
    return e.split('|')[0] if isinstance(e, str) else ''


class Ctx(object):
    def __init__(self, root):
        self.root = root
        rd = lambda rel: pd.read_csv(os.path.join(root, rel), keep_default_na=False, na_values=['']) if os.path.exists(os.path.join(root, rel)) else pd.DataFrame()
        self.rd = rd
        self.R = pd.read_csv(O.P('registration', 'registry_E6q.csv'), keep_default_na=False, dtype=str)
        self.Ri = self.R.set_index('exec_id')
        self.AS = rd('statistics/account_summary_E6q.csv')
        self.ASi = self.AS.set_index(['exec_id', 'segment']) if len(self.AS) else None
        self.RD = rd('statistics/randoms_E6q.csv')
        self.RDi = self.RD.set_index(['owner_exec_id', 'mechanism', 'segment']) if len(self.RD) else None
        self.CU = rd('statistics/cost_curve_E6q.csv')
        self.CL = rd('reports/claims_E6q.csv')
        self.PO = rd('statistics/policy_E6q.csv')
        self.M32 = rd('statistics/main32_E6q.csv')
        main = self.R[(self.R.form == O.MAIN_FORM) & (self.R.memory == 'HG10') & (self.R.scenario == 'FEASIBLE_DAILY')]
        self.ids = {(r.arm, r.trigger, r.H): r.exec_id for r in main.itertuples(index=False)}

    def get(self, e, s='FULL', c='D_same_arm_ann_pp'):
        if self.ASi is None or not e:
            return np.nan
        try:
            return self.ASi.loc[(e, s), c]
        except KeyError:
            return np.nan

    def cc(self, e, ck, A, k=0.5, x=0.5, col='net_after_impact_diff_ann_pp'):
        if not len(self.CU) or not e:
            return np.nan
        c = self.CU[(self.CU.exec_id == e) & (self.CU.comparator_kind == ck) & (self.CU.A_cny == A) & (self.CU.kappa == k) & (self.CU.exponent == x) & (self.CU.segment == 'FULL')]
        return float(c[col].iloc[0]) if len(c) else np.nan

    def rm(self, e, mech, col='rand_mean_D_ann_pp'):
        if self.RDi is None:
            return np.nan
        try:
            return self.RDi.loc[(e, mech, 'FULL'), col]
        except KeyError:
            return np.nan


def obj_line(C, arm, trig, H='20', role=''):
    e = C.ids.get((arm, trig, H), '')
    if not e:
        return ''
    return ('- **[%s] %s %s H%s**：FULL net %s；对同臂父 D %s [%s, %s]（四段 %s；G4 %s）；对同触发 NATIVE %s；对前沿锚 %s；对 LEVEL H20 参照 %s；D_sc %s；'
            '成本后对同臂父（curve κ .5 δ .5）1 亿 %s / 5 亿 %s；敞口 %s（父 %s）、年换手 %s。' % (
                role, arm, trig, H, fs(C.get(e, 'FULL', 'net_ann_pp')), fs(C.get(e)), f2(C.get(e, 'FULL', 'boot_lo')), f2(C.get(e, 'FULL', 'boot_hi')),
                ' / '.join(fs(C.get(e, s)) for s in SEG4), fs(C.get(e, 'G4')), fs(C.get(e, 'FULL', 'D_native_same_trigger_ann_pp')), fs(C.get(e, 'FULL', 'D_frontier_ann_pp')),
                fs(C.get(e, 'FULL', 'D_level_h20_ann_pp')), fs(C.get(e, 'FULL', 'D_sc_ann_pp')), fs(C.cc(e, 'SAME_ARM_PARENT', 100000000)), fs(C.cc(e, 'SAME_ARM_PARENT', 500000000)),
                f2(C.get(e, 'FULL', 'exposure_mean'), 3), f2(C.get(C.Ri.loc[e, 'parent_same_arm_exec_id'], 'FULL', 'exposure_mean') if C.Ri.loc[e, 'parent_same_arm_exec_id'] else np.nan, 3),
                f2(C.get(e, 'FULL', 'turnover_ann'))))


def r0(C, W):
    hl = ['## 0. 执行端读数要点（数字取自机器表；角色标签；不替决策端下结论）', '']
    s0a = json.load(open(O.P('diagnostics', 's0a_facts_E6q.json'), encoding='utf-8')) if os.path.exists(O.P('diagnostics', 's0a_facts_E6q.json')) else {}
    rr = s0a.get('ratio_range_full_all', [])
    hl.append('- **[仪器] S0-A**：状态 %s；7 对象 FULL legacy / curve 比值 %s；共同输入下 δ = .5 两式代数相同（L02 残差比 = 1）；比值非常数来自 NAV 节点（V_pre vs V⁺_{e−1}）与 √(V0 / V_pre) 因子，'
              '逐日桥保留（verify/impact_reconciliation_daily_bridge_E6q.csv）。' % (s0a.get('status', '—'), ' – '.join(f2(x, 3) for x in rr) if rr else '—'))
    for trig in ('T1b_LEVEL', 'T1a'):
        for arm, role in (('NATIVE', '退出基座'), ('EXIT_GATE_LIQ_5E8', '卖出侧 M3'), ('EXIT_GATE_LIQ_1E8', '卖出侧 M3'), ('EXIT_HALF', '卖出侧 M4'),
                          ('REINVEST_NEW', '再投侧 M1'), ('REINVEST_LIQ_1E8', '再投侧 M2'), ('REINVEST_LIQ_5E8', '再投侧 M2'), ('CASH_REMAIN', '参照'), ('RECYCLE_HALF', '参照')):
            ln = obj_line(C, arm, trig, '20', role)
            if ln:
                hl.append(ln)
    for H in ('20', '30'):
        ln = obj_line(C, 'NATIVE', 'UNION_T1a_T8', H, '退出并集')
        if ln:
            hl.append(ln)
        ln = obj_line(C, 'NATIVE', 'T8', H, '退出 T8')
        if ln:
            hl.append(ln)
    for trig in ('T1b_LEVEL', 'T1a'):
        e = C.ids.get(('NATIVE', trig, '20'), '')
        if e and C.RDi is not None:
            hl.append('  随机对照（%s H20 NATIVE；FULL 路径均值 / 真值位次）：AMOUNT_MATCH_V2 %s（%s）、COUNT_ISK %s、AMOUNT_ISK_V2 %s、BERNOULLI_FIRSTHIT %s（强度 %s）、LEVEL_WORST_1D %s、'
                      'RANDOM_TARGET 臂内 %s（%s）/ 源域 %s（%s）。' % (
                          trig, fs(C.rm(e, 'AMOUNT_MATCH_V2')), f2(C.rm(e, 'AMOUNT_MATCH_V2', 'rank_real'), 3), fs(C.rm(e, 'COUNT_ISK')), fs(C.rm(e, 'AMOUNT_ISK_V2')),
                          fs(C.rm(e, 'BERNOULLI_FIRSTHIT')), f2(C.rm(e, 'BERNOULLI_FIRSTHIT', 'intensity_ratio'), 3), fs(C.rm(e, 'LEVEL_WORST_1D')),
                          fs(C.rm(e, 'RANDOM_TARGET_WITHIN_ARM')), cell(C.rm(e, 'RANDOM_TARGET_WITHIN_ARM', 'match_status')), fs(C.rm(e, 'RANDOM_TARGET_SOURCE_DOMAIN')),
                          cell(C.rm(e, 'RANDOM_TARGET_SOURCE_DOMAIN', 'match_status'))))
    if len(C.M32):
        pos = int((pd.to_numeric(C.M32.FULL_D_frontier_ann_pp, errors='coerce') > 0).sum())
        hl.append('- **[读法] 主 32 行对前沿锚（H20 T1a NATIVE）**：FULL 差为正 %d / 32 行（全表见 E6q_REPORT_main.md；不从 201 个逻辑账户挑最大者）。' % pos)
    E_ = C.CL[C.CL.kind == 'PREDICTION'] if len(C.CL) else pd.DataFrame()
    if len(E_):
        hl.append('- **[读法] E01–E07**：%s（带内 = 支持、带外 = 不支持；区间另列不决定 HIT）。' % '；'.join('%s %s（%s）' % (r.claim_id, r.claim_status, f2(r.result_value)) for r in E_.itertuples(index=False)))
    CCs = C.CL[C.CL.claim_id.str.match(r'^CC-E6q-\d\d$')] if len(C.CL) else pd.DataFrame()
    if len(CCs):
        hl.append('- **[读法] CC-E6q-01…11 句级**：%s（子条款见 E6q_REPORT_ledgers.md）。' % '；'.join('%s %s' % (r.claim_id[-2:], r.claim_status) for r in CCs.itertuples(index=False)))
    if len(C.PO):
        pv = C.PO.groupby(['profile_name', 'verdict']).size().reset_index(name='n')
        hl.append('- **[政策]** %s。' % '；'.join('%s %s %d' % (r.profile_name, r.verdict, r.n) for r in pv.itertuples(index=False)))
    hl.append('')
    m = C.M32.copy()
    if len(m):
        m['segs'] = [' / '.join(fs(r['D_%s' % s]) for s in SEG4) for _, r in m.iterrows()]
    body = [HEADER, '# E6q 报告 R0：总览', ''] + hl + [
        '## 1. 主 32 行（两 H × 两触发 × 七核心臂 + T8 / 并集四行；FEASIBLE；对同臂父）', '',
        md_table(m.sort_values(['trigger', 'H', 'arm']), ['trigger', 'H', 'arm', 'FULL_net_ann_pp', 'FULL_D_same_arm_ann_pp', 'segs', 'G4_D_same_arm_ann_pp',
                                                         'FULL_D_native_same_trigger_ann_pp', 'FULL_D_frontier_ann_pp', 'cost_1e8_D_same_arm_ann_pp', 'cost_5e8_D_same_arm_ann_pp',
                                                         'verdict_canonical', 'research_status'],
                 ['触发', 'H', '臂', 'FULL net', 'D 同臂父', '四段 D', 'G4', 'D 同触发 NATIVE', 'D 前沿锚', '1 亿成本后', '5 亿成本后', '政策（canonical）', '研究状态']) if len(m) else '（主表未生成）', '',
        '## 2. 经济方向预测 E01–E07（plan §12.2；首测新算子，同历史，不称独立验证）', '',
        md_table(E_, ['claim_id', 'result_value', 'ci_lo', 'ci_hi', 'claim_status', 'note'], ['id', '点估', '区间下', '区间上', '状态', '注']) if len(E_) else '（未生成）', '',
        '## 3. 读法提示', '',
        '- 主差 = 同臂无退出父（SAME_ARM_PARENT）；同触发 NATIVE、H5 全局父、前沿锚、LEVEL H20 参照并报；IDEAL 只作配对诊断，不因 IDEAL 好于 FEASIBLE 调换主次。',
        '- 成本曲线 A ∈ {.5, 1, 2, 5, 10} 亿 × κ ∈ {.5, 1}（主 32 另报 κ .3 场景行）× δ ∈ {.5, .7, 1}，p₀ = .01；κ 未校准（SCENARIO_NOT_CALIBRATED）；1 亿主读、.5 / 5 亿副读。',
        '- 价值密度 / 成本密度是"每单位换手"的读法，分母退化行（NOT_POSITIVE_DENOMINATOR 等）不比；CASH 参照的密度已部分消去避损。',
        '- RANDOM_TARGET 的触限（ALGORITHM_LIMIT）日份额 > .25 → CONTROL_NOT_COMPARABLE；IDENTITY_TARGET_CONTROL 不记 HIT（plan §12.3 #7）。',
        '- 本轮任何"通过"不构成上线或候选升级（deployment_authorized = false；E7 HOLD）。', '']
    W('E6q_REPORT_R0.md', '\n'.join(body) + '\n')


def main_report(C, W):
    m = C.M32.copy()
    parts = [HEADER, '# E6q 主结果：主展示 32 行（FEASIBLE；A4b_CVRv5 × HG10）', '', '32 行是阅读布局，不是候选域；CASH / RECYCLE_HALF 在参照表（下节），不因未进 32 行而减少对照。', '']
    if len(m):
        m['segs'] = [' / '.join(fs(r['D_%s' % s]) for s in SEG4) for _, r in m.iterrows()]
        for (t, H), x in m.groupby(['trigger', 'H']):
            parts += ['## %s H%s' % (t, H), '', md_table(x.sort_values('arm'), ['arm', 'A_ref', 'FULL_net_ann_pp', 'FULL_D_same_arm_ann_pp', 'segs', 'G4_D_same_arm_ann_pp',
                                                                             'FULL_D_native_same_trigger_ann_pp', 'FULL_D_h5_global_ann_pp', 'FULL_D_frontier_ann_pp',
                                                                             'FULL_D_level_h20_ann_pp', 'cost_1e8_D_same_arm_ann_pp', 'cost_5e8_D_same_arm_ann_pp',
                                                                             'rank_vs_amount_match_v2', 'rank_vs_amount_isk_v2', 'verdict_legacy', 'verdict_canonical'],
                                                                ['臂', 'A_ref', 'FULL net', 'D 同臂父', '四段 D', 'G4', 'D 同触发 NATIVE', 'D H5 全局父', 'D 前沿锚', 'D LEVEL H20',
                                                                 '1 亿成本后', '5 亿成本后', '位次 AMT_V2', '位次 AISK_V2', 'LEGACY', 'CANONICAL']), '']
    ref = []
    for trig in ('T1a', 'T1b_LEVEL'):
        for H in ('20', '30'):
            for arm in ('CASH_REMAIN', 'RECYCLE_HALF', 'EXIT_HALF_REARM', 'EXIT_HALF_RECYCLE_HALF', 'EXIT_GATE_LIQ_1E8', 'REINVEST_LIQ_1E8'):
                e = C.ids.get((arm, trig, H), '')
                if e:
                    ref.append(dict(trigger=trig, H=H, arm=arm, net=C.get(e, 'FULL', 'net_ann_pp'), D=C.get(e), lo=C.get(e, 'FULL', 'boot_lo'), hi=C.get(e, 'FULL', 'boot_hi'),
                                    Dn=C.get(e, 'FULL', 'D_native_same_trigger_ann_pp'), Dc=C.get(e, 'FULL', 'D_cash_same_trigger_ann_pp'),
                                    c1=C.cc(e, 'SAME_ARM_PARENT', 100000000), c5=C.cc(e, 'SAME_ARM_PARENT', 500000000), expo=C.get(e, 'FULL', 'exposure_mean'),
                                    segs=' / '.join(fs(C.get(e, s)) for s in SEG4)))
    if ref:
        parts += ['## 参照臂与桥（CASH_REMAIN / RECYCLE_HALF / 半量桥 / 1 亿门控与再投）', '',
                  md_table(pd.DataFrame(ref), ['trigger', 'H', 'arm', 'net', 'D', 'lo', 'hi', 'segs', 'Dn', 'Dc', 'c1', 'c5', 'expo'],
                           ['触发', 'H', '臂', 'FULL net', 'D 同臂父', 'boot 下', 'boot 上', '四段 D', 'D 同触发 NATIVE', 'D 同触发 CASH', '1 亿成本后', '5 亿成本后', '敞口']), '']
    rob = C.R[(C.R.group.isin(['ROBUSTNESS'])) & (C.R.scenario == 'FEASIBLE_DAILY')]
    if len(rob):
        rows = [dict(form=r.form, memory=r.memory, trigger=r.trigger, arm=r.arm, D=C.get(r.exec_id), Dn=C.get(r.exec_id, 'FULL', 'D_native_same_trigger_ann_pp'),
                     segs=' / '.join(fs(C.get(r.exec_id, s)) for s in SEG4)) for r in rob.itertuples(index=False)]
        X = pd.DataFrame(rows).sort_values(['form', 'memory', 'trigger', 'arm'])
        parts += ['## 记忆 / 形态稳健性（84 行，H20；对同臂父 FULL D）', '', md_table(X, ['form', 'memory', 'trigger', 'arm', 'D', 'segs', 'Dn'],
                                                                               ['形态', '记忆', '触发', '臂', 'D 同臂父', '四段 D', 'D 同触发 NATIVE']), '']
    ide = C.R[C.R.scenario == 'IDEALIZED_SOURCE_FILL']
    if len(ide):
        rows = [dict(trigger=r.trigger, arm=r.arm, D=C.get(r.exec_id), Dn=C.get(r.exec_id, 'FULL', 'D_native_same_trigger_ann_pp'),
                     Df=C.get(C.ids.get((r.arm, r.trigger, r.H), ''))) for r in ide.itertuples(index=False)]
        parts += ['## IDEAL 配对诊断（21 行；只作诊断，不调换主次）', '', md_table(pd.DataFrame(rows).sort_values(['trigger', 'arm']), ['trigger', 'arm', 'D', 'Dn', 'Df'],
                                                                           ['触发', '臂', 'IDEAL D 同臂父', 'IDEAL D 同触发 NATIVE', 'FEASIBLE 同坐标 D']), '']
    W('E6q_REPORT_main.md', '\n'.join(parts) + '\n')


def policy_report(C, W):
    pf = C.rd('statistics/policy_fields_E6q.csv')
    txt = [HEADER, '# E6q 政策', '', 'verdict 只由 policy_fields 按 plan 附录 C policy_verdict 重算（显式 Python bool；任一 false → 不通过；无 false 有 NA → 不可判；全 true → 通过）；'
           'LEGACY_E6O_A5 只审计（H ∈ {5, 20}）；POLICY_E6Q_A1_CANONICAL 主 A = 1 亿、c5 用 curve κ .5 δ .5，.5 / 5 亿另列；kappa_consistent 只是列。', '']
    if len(pf):
        vc = pf.groupby(['profile_name', 'field', 'value']).size().reset_index(name='n')
        txt += ['## 字段取值分布', '', md_table(vc, ['profile_name', 'field', 'value', 'n']), '']
    if len(C.PO):
        und = C.PO[C.PO.verdict == '不可判'].groupby(['profile_name', 'undecidable_reason']).size().reset_index(name='n')
        kf = C.PO[C.PO.known_failure.fillna('') != ''].groupby(['profile_name', 'known_failure']).size().reset_index(name='n').sort_values('n', ascending=False).head(20)
        passed = C.PO[C.PO.verdict == '通过'].merge(C.R[['exec_id', 'group', 'form', 'memory', 'H', 'trigger', 'arm']], on='exec_id')
        txt += ['## 不可判原因', '', md_table(und, ['profile_name', 'undecidable_reason', 'n']) if len(und) else '无。', '',
                '## 已知失败（前 20 种组合）', '', md_table(kf, ['profile_name', 'known_failure', 'n']) if len(kf) else '无。', '',
                '## 通过的对象（%d 行）' % len(passed), '', md_table(passed.sort_values(['profile_name', 'scenario', 'group', 'trigger', 'H', 'arm']),
                                                                 ['profile_name', 'scenario', 'group', 'form', 'memory', 'H', 'trigger', 'arm', 'research_status']) if len(passed) else '无。', '']
    W('E6q_REPORT_policy.md', '\n'.join(txt) + '\n')


def mech_report(C, W):
    mech = [HEADER, '# E6q 机制与诊断（D1–D10、landmark、WARM、成本反馈）', '', '每块只列主读行（LEVEL / T1a H20 主形态 HG10 与全局行）；全表见 diagnostics/。', '']
    names = (('D1', 'cost_source'), ('D2', 'target'), ('D3', 'entry_persistence'), ('D4', 'age_delay'), ('D5', 'dose'), ('D6', 'density'), ('D7', 'composition'),
             ('D8', 'window'), ('D9', 'risk'), ('D10', 'externality'))
    keep = ('|T1b_LEVEL|H20|main|HG10', '|T1a|H20|main|HG10', 'H20|T1b_LEVEL', 'H20|T1a', 'NATIVE|NONE|H20|main|HG10', 'all_accounts', 'engine', 'K_strength', 'UNION_T1a_T8|H20')
    for blk, nm in names:
        d = C.rd('diagnostics/%s_%s_E6q.csv' % (blk, nm))
        if not len(d):
            continue
        k = d.key1.astype(str) + '#' + d.key2.astype(str) + '#' + d.stat.astype(str)
        dm = d[k.apply(lambda s: any(x in s for x in keep))]
        if blk == 'D1':
            dm = dm[dm.stat.astype(str).str.contains('A5e\\+08') & (dm.stat.astype(str).str.contains('arm_minus') | (dm.item == 'fee_algebra')) | (dm.item == 'impact_by_side')]
        mech += ['## %s（%s；全表 %d 行，此处 ≤ 60 行）' % (blk, nm, len(d)), '', md_table(dm.head(60), ['item', 'key1', 'key2', 'segment', 'stat', 'value', 'unit', 'n', 'status']), '']
    lm = C.rd('diagnostics/landmark_E6q.csv')
    e = C.ids.get(('NATIVE', 'T1b_LEVEL', '20'), '')
    if len(lm) and e:
        x = lm[(lm.exec_id == e) & (lm.q == 5) & (lm.weighting == 'EQUAL')]
        mech += ['## landmark（LEVEL H20 NATIVE；q5；等权；交易日聚类区间）', '', md_table(x, ['landmark_age', 'state', 'n', 'mean_fwd_excess_bp', 'lo', 'hi', 'status']), '']
    ws = C.rd('statistics/warm_sensitivity_E6q.csv')
    if len(ws):
        mech += ['## WARM 四段重置敏感性（主 32 对象对；连续全历史为主）', '', md_table(ws.head(140), ['exec_id', 'segment', 'D_ann_pp', 'D_cash_v0_ann_pp', 'D_warm_minus_cont']), '']
    fb = C.rd('statistics/cost_feedback_E6q.csv')
    if len(fb):
        fbm = fb[fb.segment == 'FULL']
        mech += ['## 成本反馈 80 路径（FULL；费用入现金的闭环，不模拟自身订单的市场影响）', '', md_table(fbm, ['feedback_id', 'owner_exec_id', 'A0_cny', 'net_ann_pp_feedback',
                                                                                             'D_feedback_ann_pp', 'D_fixed_path_ann_pp', 'status']), '']
    sn = C.rd('diagnostics/local_snapshot_E6q.csv')
    if len(sn):
        x = sn[sn.segment == 'FULL']
        mech += ['## 固定快照金额控制（plan §7.4；20 项；只读、不进政策、不拼净值）', '', md_table(x, ['owner_arm', 'trigger', 'H', 'side', 'n_days', 'native_full_V0', 'new_budget_V0', 'common_V0',
                                                                                  'uncovered_native_V0', 'to_whom_q5_bp', 'to_whom_ann_pp', 'trading_less_ann_pp', 'deferral_ann_pp']), '']
    W('E6q_REPORT_mechanisms.md', '\n'.join(mech) + '\n')


def ledgers_report(C, W):
    led = [HEADER, '# E6q 两账本复盘（G / E；plan §3 / §12）', '',
           '构思数 / 实测方向数 / 可评分经济预测数（E01–E07）/ 工程测试数 / 策略路径数分开；工程恒等不进经济命中率；7 条 E 高度相关（同历史、同对象族），不当 7 份独立证据。', '']
    Gl = pd.read_csv(O.P('registration', 'ledger_G_E6q.csv'), keep_default_na=False, dtype=str)
    led += ['## G 账本（G-P-01…12；第一道标签，推导段）', '', md_table(Gl, ['g_id', 'statement_verbatim', 'state', 'result_row']), '']
    if len(C.CL):
        for kind, title in (('PREDICTION', 'E 账本（E01–E07）'), ('QUESTION', 'Q 卡（Q01–Q18；不评分）'), ('CC_CARRIED', 'proposal 原句携带（CC-E6q-01…11；句级 + 子条款）'),
                            ('ENGINEERING', '工程恒等（不进经济分母）')):
            x = C.CL[C.CL.kind == kind]
            led += ['## %s' % title, '', md_table(x, ['claim_id', 'statement', 'result_value', 'ci_lo', 'ci_hi', 'claim_status', 'query_id', 'note'],
                                                   ['id', '原句 / 子条款', '值', '区间下', '区间上', '状态', 'query', '注']), '']
        E_ = C.CL[C.CL.kind == 'PREDICTION']
        led += ['计数：经济方向预测 7（E01–E07）；状态分布 %s；CC 句级 %s。' % (E_.claim_status.value_counts().to_dict(),
                                                                C.CL[C.CL.claim_id.str.match(r'^CC-E6q-\d\d$')].claim_status.value_counts().to_dict()), '']
    W('E6q_REPORT_ledgers.md', '\n'.join(led) + '\n')


def limit_register(C, W):
    RD = C.RD
    mcl = RD[(RD.segment == 'FULL') & (RD.status == 'MC_LIMIT')] if len(RD) else pd.DataFrame()
    rt = RD[(RD.segment == 'FULL') & RD.mechanism.astype(str).str.startswith('RANDOM_TARGET')] if len(RD) else pd.DataFrame()
    ncomp = int((rt.control_comparability == 'CONTROL_NOT_COMPARABLE').sum()) if len(rt) else 0
    ls = pd.to_numeric(rt.limit_day_share, errors='coerce') if len(rt) else pd.Series(dtype=float)
    lim = [HEADER, '# E6q limit register', '',
           '- 同一历史已曝光；"首次新算子运行"仍非 OOS（plan §13.1）。主 32 行与 E 对象事前定死，不按收益选。',
           '- κ 未校准（SCENARIO_NOT_CALIBRATED）；成本曲线是固定路径情景；反馈 80 路径只是"费用入现金"的闭环，不模拟自身订单的市场影响；A_ref 锁定规则的跨规模迁移只作读法（Q11）。',
           '- S0-A：legacy / curve 比值非常数（NAV 节点与 √(V0 / V_pre)）；canonical = curve，旧审计 profile 只在 H ∈ {5, 20} 可判。',
           '- RANDOM_TARGET 精确首可行匹配在节点上限（20 万）处可能触限：FULL 触限 / 无解日份额 %s（%d 个 owner × 机制 CONTROL_NOT_COMPARABLE）；触限日按带上限部分分配并计 ALGORITHM_LIMIT。' % (
               ('中位 %.3f，最大 %.3f' % (ls.median(), ls.max())) if ls.notna().any() else '—', ncomp),
           '- MC_LIMIT（主形态 HG10 owner 到 1,024 条路径仍 MCSE > .01）：%d 个 owner × 机制（清单见 REVIEW 注记 §8）。' % len(mcl),
           '- BERNOULLI_FIRSTHIT：影子风险集按日龄桶的首达率（60 日窗、不含 T）；桶内无风险集回退全龄池，仍无则 NaN（该日不抽）。',
           '- EDGE 价差：21 日窗止于 T−1、≥ 3 完整 OHLC；输入为 lclose 链复权价（adj_factor 在 2–11% 开盘格缺失）；相等判断在原价上（避免 SIMD 1-ulp 翻转）；只作 D2 附属列，不设过滤门。',
           '- 分钟数据 2013-08-01 起：D5 第二分母（尾盘 30 分钟额）与 D8 执行窗只在其后有值。',
           '- D3 只用两推导段；K0 / CVR20 取 E6i 测量缓存（只读，对齐核见 D3 e6i_alignment_check）；"混合 Q 评分"本轮缓存无独立列 → NOT_AVAILABLE。',
           '- 入场好度：A4b 形成权重近乎常数（1% 单股上限），不能当好度分数；D2 入场好度、D3 K 强、D4 存活组成用取向后的 K 腿好度（−K0 当日源域分位，只是 K 腿一条轴，不是 A4b 合成分）；'
           '推导段封存的 G1 · G-P-12 仍是形成权重排名（不分级），读法以 D3 为准。',
           '- 部分成交与门控多日执行使"早退成交行数"≠"已实现早退意向数"（SCHEMA_DEVIATIONS；S29）。',
           '- H30 的尾端（2026 年 1–3 月）与 landmark 前向窗口超授权终点记 RIGHT_CENSORED；2026 为部分年（至 03-27），年表 partial_year_flag = 1。',
           '- E7 HOLD；deployment_authorized = false；本轮任何"通过"不构成上线或候选升级。', '']
    W('E6q_limit_register.md', '\n'.join(lim) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    root = O.P(*a.root.split('/')) if a.root else O.work()
    C = Ctx(root)
    rep = os.path.join(root, 'reports')
    os.makedirs(rep, exist_ok=True)
    W = lambda name, txt: O.atomic_write_text(os.path.join(rep, name), txt)
    r0(C, W)
    main_report(C, W)
    policy_report(C, W)
    mech_report(C, W)
    ledgers_report(C, W)
    limit_register(C, W)
    print(json.dumps(dict(reports=sorted(os.path.basename(p) for p in glob.glob(os.path.join(rep, '*.md')))), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
