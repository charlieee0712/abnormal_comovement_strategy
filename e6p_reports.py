# -*- coding: utf-8 -*-
"""E6p 报告（brief §8.1：R0 / 主结果 / 政策 / 机制 / 两账本复盘 / 限制 / REVIEW 输入注记 / limit register / lessons delta / 执行端复盘 / 代码变更登记 / 白名单）。
数字只从机器表取（statistics / diagnostics / events / reports/claims / verify）；不写字面 nan / None（缺失写 —）；不写登录信息、主机标识或用户目录。
用法：python3 e6p_reports.py [--root <根>]"""
import os
import json
import glob
import argparse

import numpy as np
import pandas as pd

import e6p_core as O
import e6p_g1 as G1

SEG4 = list(O.SEGS)


def f2(x, d=2):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return '—' if (x is None or str(x).strip() in ('', 'nan', 'None')) else str(x)
    if not np.isfinite(v):
        return '—'
    return ('%.' + str(d) + 'f') % v


def fsign(x, d=2):
    s = f2(x, d)
    return s if s == '—' or s.startswith('-') else '+' + s


def md_table(df, cols, heads=None):
    heads = heads or cols
    out = ['| ' + ' | '.join(heads) + ' |', '|' + '---|' * len(heads)]
    for r in df[cols].itertuples(index=False):
        out.append('| ' + ' | '.join(f2(v) if isinstance(v, float) else ('—' if str(v) in ('', 'nan', 'None') else str(v)) for v in r) + ' |')
    return '\n'.join(out)


HEADER = ('> **页首声明**：E6p 执行交付（协议 **v1.6**、**方式 B**；brief b1b78440 / 附录 7e7277c9 / plan v1.1 efd382ee / spec 5c7742ad / D 脚本 4274d7fe）。'
          '市场历史截止 2026-03-27；**E7 HOLD（不读）**；**deployment_authorized = false**；生产配置 / I11 事件定义 / 观察窗 / K/T/C/Q 原测量 / 候选库不动。'
          '授权行（用户 2026-10-19 明示）：① research_long_H_authorized = true ② aggregate_deploy_authorized = true ③ recycle_arms_authorized = true '
          '④ target_A_cny = null → target_A_status = UNDECIDABLE_TARGET_A ⑤ 主线 = 状态相依持有期。段初始化：连续全历史为主（CASH_V0）、四段重置（WARM）只作主对象敏感性（brief §0.1 #18 有意偏离 plan §4.4）。'
          '数字全部来自机器表；读法纪律：主对象差与族中位分列、两推导段符号旁印、结论带角色标签。\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    root = O.P(a.root) if a.root else O.work()
    rd = lambda rel: pd.read_csv(os.path.join(root, rel), keep_default_na=False, na_values=[''])
    R = pd.read_csv(O.P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
    AS = rd('statistics/account_summary_E6p.csv')
    ASi = AS.set_index(['exec_id', 'segment'])
    RD = rd('statistics/randoms_E6p.csv')
    RDi = RD.set_index(['owner_exec_id', 'mechanism', 'segment'])
    PO = rd('statistics/policy_E6p.csv')
    M72 = rd('statistics/main72_E6p.csv')
    BE = rd('statistics/breakeven_E6p.csv')
    CU = rd('statistics/cost_curve_E6p.csv')
    FB = rd('statistics/cost_feedback_E6p.csv')
    CL = rd('reports/claims_E6p.csv')
    EV = rd('events/event_counts_E6p.csv')
    RW = rd('events/renew_E6p.csv')
    MT = rd('statistics/matching_E6p.csv')
    WS = rd('statistics/warm_sensitivity_E6p.csv') if os.path.exists(os.path.join(root, 'statistics', 'warm_sensitivity_E6p.csv')) else pd.DataFrame()
    I = rd('verify/identities_E6p.csv')
    ids = G1.main_ids(R)
    get = lambda e, s='FULL', c='D_same_h_ann_pp': ASi[c].get((e, s), np.nan)
    rep = os.path.join(root, 'reports')
    os.makedirs(rep, exist_ok=True)
    W = lambda name, txt: O.atomic_write_text(os.path.join(rep, name), txt)
    # ---------------- 主对象读数
    mainrows = []
    for t in ('T1a', 'T1b_LEVEL'):
        for d in ('NATIVE', 'D80', 'D95'):
            e = ids[(d, '20', t, '0')]
            rr = lambda mech: RDi['rank_real'].get((e, mech, 'FULL'), np.nan)
            rm = lambda mech: RDi['rand_mean_D_ann_pp'].get((e, mech, 'FULL'), np.nan)
            mainrows.append(dict(obj='H20 %s %s' % (t, d), net=get(e, 'FULL', 'net_ann_pp'), D=get(e), lo=get(e, 'FULL', 'boot_lo'), hi=get(e, 'FULL', 'boot_hi'),
                                 segs=' / '.join(fsign(get(e, s)) for s in SEG4), G4=get(e, 'G4'), Dsc=get(e, 'FULL', 'D_sc_ann_pp'), D5d=get(e, 'FULL', 'D_h5_same_deploy_ann_pp'),
                                 D5n=get(e, 'FULL', 'D_h5_native_ann_pp'), D5t=get(e, 'FULL', 'D_h5_same_trigger_ann_pp'), Dimp=get(e, 'FULL', 'D_imp_ann_pp'),
                                 amt=rm('AMOUNT_MATCH_V2'), isk=rm('COUNT_ISK'), bern=rm('BERNOULLI_LAG60'), lvw=rm('LEVEL_WORST_1D'), aisk=rm('AMOUNT_ISK_V2'),
                                 rk=rr('AMOUNT_MATCH_V2'), expo=get(e, 'FULL', 'exposure_mean'), turn=get(e, 'FULL', 'turnover_ann')))
    MR = pd.DataFrame(mainrows)
    E_ = CL[CL.claim_id.isin(['E%02d' % i for i in range(1, 11)])]
    pol = PO.groupby(['profile_name', 'execution_profile', 'verdict']).size().reset_index(name='n')
    # ---------------- 执行端读数要点（机器表取数；角色标签：退出 / 持有期 / 部署 / 再投资 / 读法）
    def be(e, ck, k=0.5, x=0.5):
        b = BE[(BE.exec_id == e) & (BE.comparator_kind == ck) & (BE.kappa == k) & (BE.exponent == x)]
        return ('%s %s' % (b.root_kind.iloc[0], f2(b.breakeven_A_cny.iloc[0] / 1e8, 2) + ' 亿' if np.isfinite(b.breakeven_A_cny.iloc[0]) else '')) if len(b) else '—'

    def cc(e, ck, A, k=0.5, x=0.5):
        c = CU[(CU.exec_id == e) & (CU.comparator_kind == ck) & (CU.A_cny == A) & (CU.kappa == k) & (CU.exponent == x) & (CU.segment == 'FULL')]
        return float(c.net_after_impact_diff_ann_pp.iloc[0]) if len(c) else np.nan
    hl = ['## 0. 执行端读数要点（数字取自机器表；不替决策端下结论）', '']
    for t, nm in (('T1a', 'T1a'), ('T1b_LEVEL', 'LEVEL')):
        e = ids[('NATIVE', '20', t, '0')]
        hl.append('- **[退出 × 持有期] H20 %s NATIVE**：对同 H 父 FULL D %s [%s, %s]，四段 %s，G4 %s；对 H5 NATIVE 父 %s、对 H5 同触发 %s；D_sc %s。'
                  '固定路径冲击后（κ .5 δ .5）对同 H 父：1 亿 %s / 5 亿 %s；对 H5 NATIVE 父：1 亿 %s / 5 亿 %s；盈亏平衡（对同 H 父）%s、（对 H5 NATIVE）%s。' % (
                      nm, fsign(get(e)), f2(get(e, 'FULL', 'boot_lo')), f2(get(e, 'FULL', 'boot_hi')), ' / '.join(fsign(get(e, s)) for s in SEG4), fsign(get(e, 'G4')),
                      fsign(get(e, 'FULL', 'D_h5_native_ann_pp')), fsign(get(e, 'FULL', 'D_h5_same_trigger_ann_pp')), fsign(get(e, 'FULL', 'D_sc_ann_pp')),
                      fsign(cc(e, 'VS_SAME_H_PARENT', 100000000)), fsign(cc(e, 'VS_SAME_H_PARENT', 500000000)), fsign(cc(e, 'VS_H5_CURRENT_NATIVE', 100000000)),
                      fsign(cc(e, 'VS_H5_CURRENT_NATIVE', 500000000)), be(e, 'VS_SAME_H_PARENT'), be(e, 'VS_H5_CURRENT_NATIVE')))
        rm = lambda mech: RDi['rand_mean_D_ann_pp'].get((e, mech, 'FULL'), np.nan)
        hl.append('  随机对照（FULL 路径均值）：AMOUNT_MATCH_V2 %s、COUNT_ISK %s、BERNOULLI_LAG60 %s、AMOUNT_ISK_V2 %s、LEVEL_WORST_1D %s；真值位次（AMT_V2）%s；未匹配份额 %s。' % (
            fsign(rm('AMOUNT_MATCH_V2')), fsign(rm('COUNT_ISK')), fsign(rm('BERNOULLI_LAG60')), fsign(rm('AMOUNT_ISK_V2')), fsign(rm('LEVEL_WORST_1D')),
            f2(RDi['rank_real'].get((e, 'AMOUNT_MATCH_V2', 'FULL'), np.nan), 3), f2(RDi['unmatched_share'].get((e, 'AMOUNT_MATCH_V2', 'FULL'), np.nan), 3)))
    for d in ('D80', 'D95'):
        hl.append('- **[部署] %s 父 − NATIVE 父（H20 HG10）**：FULL net %s（敞口 %s vs %s）；H5：%s。' % (
            d, fsign(get(ids[(d, '20', 'NONE', '0')], 'FULL', 'net_ann_pp') - get(ids[('NATIVE', '20', 'NONE', '0')], 'FULL', 'net_ann_pp')),
            f2(get(ids[(d, '20', 'NONE', '0')], 'FULL', 'exposure_mean'), 3), f2(get(ids[('NATIVE', '20', 'NONE', '0')], 'FULL', 'exposure_mean'), 3),
            fsign(get(ids[(d, '5', 'NONE', '0')], 'FULL', 'net_ann_pp') - get(ids[('NATIVE', '5', 'NONE', '0')], 'FULL', 'net_ann_pp'))))
    for t in ('T1a', 'T1b_LEVEL'):
        hl.append('- **[持有期] 同 H 父差随 H（NATIVE，%s）**：%s；对 H5 NATIVE：%s。' % (
            t, ' / '.join('H%s %s' % (H, fsign(get(ids[('NATIVE', H, t, '0')]))) for H in ('5', '10', '15', '20', '30', '40')),
            ' / '.join('H%s %s' % (H, fsign(get(ids[('NATIVE', H, t, '0')], 'FULL', 'D_h5_native_ann_pp'))) for H in ('5', '10', '15', '20', '30', '40'))))
    hl.append('- **[退出] RENEW5（HG10 × D80 × LEVEL）**：H20 %s、H40 %s（RENEW5 − 无 RENEW5 同对象 FULL net 差）；renew-only H20 NATIVE 对无 renew 父 %s。' % (
        fsign(get(ids[('D80', '20', 'T1b_LEVEL', '5')], 'FULL', 'net_ann_pp') - get(ids[('D80', '20', 'T1b_LEVEL', '0')], 'FULL', 'net_ann_pp')),
        fsign(get(ids[('D80', '40', 'T1b_LEVEL', '5')], 'FULL', 'net_ann_pp') - get(ids[('D80', '40', 'T1b_LEVEL', '0')], 'FULL', 'net_ann_pp')),
        fsign(get(ids[('NATIVE', '20', 'NONE', '5')]))))
    for arm in ('CASH_REMAIN', 'RECYCLE_HALF', 'RECYCLE_COST0', 'RECYCLE_COSTNET'):
        hl.append('- **[再投资] %s − NATIVE（HG10 × LEVEL）**：H5 %s、H20 %s、H40 %s（FULL net；5 亿 κ .5 冲击后 H5 %s / H20 %s）。' % (
            arm, *(fsign(get(ids[(arm, H, 'T1b_LEVEL', '0')], 'FULL', 'net_ann_pp') - get(ids[('NATIVE', H, 'T1b_LEVEL', '0')], 'FULL', 'net_ann_pp')) for H in ('5', '20', '40')),
            *(fsign(cc(ids[(arm, H, 'T1b_LEVEL', '0')], 'ABSOLUTE', 500000000) - cc(ids[('NATIVE', H, 'T1b_LEVEL', '0')], 'ABSOLUTE', 500000000)) for H in ('5', '20'))))
    hl.append('- **[退出] T8 / UNION（H20 NATIVE）**：T8 %s；UNION %s vs T1a %s / T3b15 %s。' % (
        fsign(get(ids[('NATIVE', '20', 'T8_LIMIT_CLOSE', '0')])), fsign(get(ids[('NATIVE', '20', 'UNION', '0')])), fsign(get(ids[('NATIVE', '20', 'T1a', '0')])),
        fsign(get(ids[('NATIVE', '20', 'T3b15', '0')]))))
    if len(WS):
        Ri = R.set_index('exec_id')
        wf = WS[WS.execution_profile == 'FEASIBLE_DAILY']
        hl.append('- **[读法] WARM 四段重置敏感性（主对象，FEASIBLE）**：D 差（WARM − 连续）%s。' % '；'.join(
            'H%s %s %s：%s' % (Ri.loc[e, 'H'], Ri.loc[e, 'trigger'], Ri.loc[e, 'deploy'], ' / '.join('%s %s' % (r.segment, fsign(r.D_warm_minus_cont)) for r in g.itertuples(index=False)))
            for e, g in wf.groupby('exec_id', sort=False)))
    hl += ['- **[读法] E01–E10**：%s。' % '；'.join('%s %s' % (r.claim_id, r.claim_status) for r in E_.itertuples(index=False)), '']
    r0 = [HEADER, '# E6p 报告 R0：总览', ''] + hl + [
          '## 1. 主对象两只（HG10 × H20；先 NATIVE 复现，再 D80 / D95 同部署差、H5 两种父差、随机、成本）', '',
          md_table(MR, ['obj', 'net', 'D', 'lo', 'hi', 'segs', 'G4', 'Dsc', 'D5d', 'D5n', 'D5t', 'Dimp'],
                   ['对象', 'FULL net', 'D 同 H 父', 'boot 下', 'boot 上', '四段 D', 'G4', 'D_sc', 'D vs H5 同部署', 'D vs H5 NATIVE', 'D vs H5 同触发', 'D_imp（5 亿 κ .5 旧审计）']), '',
          '随机对照（FULL；真实 D 减各机制路径均值见 statistics/randoms_E6p.csv）：', '',
          md_table(MR, ['obj', 'D', 'amt', 'isk', 'bern', 'lvw', 'aisk', 'rk', 'expo', 'turn'],
                   ['对象', '真实 D', 'AMOUNT_MATCH_V2 均值', 'COUNT_ISK 均值', 'BERNOULLI_LAG60 均值', 'LEVEL_WORST_1D', 'AMOUNT_ISK_V2 均值', '真值位次（AMT_V2）', '敞口均值', '年换手']), '',
          '## 2. 经济方向预测 E01–E10（10 条进本轮分母；工程恒等不进）', '',
          md_table(E_, ['claim_id', 'statement', 'result_value', 'ci_lo', 'ci_hi', 'claim_status', 'note'], ['id', '原句（plan §12）', '点估', '区间下', '区间上', '状态', '注']), '',
          '## 3. 政策（LEGACY_E6O_A5 只在 E6o 已批准域可判；E6P_CURVE_RESEARCH 的规模条件 = UNDECIDABLE_TARGET_A）', '',
          md_table(pol, ['profile_name', 'execution_profile', 'verdict', 'n'], ['profile', '情景', 'verdict', '对象数']), '',
          '## 4. 读法提示', '',
          '- 主差 = 同 H 同部署无退出父（VS_SAME_H_PARENT）；H5 两种父并报；"记录用通过"不构成新资格门（plan §13.2）；±.3 只作显示带。',
          '- MIRROR_LAG1 不是无信息父，只作诊断；D80 / D95 的增量是部署（DEPLOY_OPERATOR_CHANGE），退出效应看同部署差与 DEPLOY_X_EXIT。',
          '- 成本曲线 A ∈ {.5, 1, 2, 5, 10} 亿 × κ ∈ {.5, 1} × δ ∈ {.5, .7}，p₀ = .01 锚；κ 未校准（SCENARIO_NOT_CALIBRATED）；A* 只是场景交叉点。',
          '- CASH 成本后接近零不等于卖出免费；1.98 − 1.19 类差不是因果份额（plan §9.5 / §10.2 读法禁令）。',
          '- LEVEL 对象的 LEVEL_WORST_1D 对照与真实按同一水平排序选股，近同构（H20 NATIVE 真实 − 对照 = %s）：≈0 不读成"纯信息已分离"（卡 Q13）；该对照对 T1a 才有辨别力。' % fsign(
              MR.loc[MR.obj == 'H20 T1b_LEVEL NATIVE', 'D'].iloc[0] - MR.loc[MR.obj == 'H20 T1b_LEVEL NATIVE', 'lvw'].iloc[0]), '']
    W('E6p_REPORT_R0.md', '\n'.join(r0) + '\n')
    # ---------------- 主结果（primary72）
    m = M72.copy()
    m['segs'] = [' / '.join(fsign(r['D_%s' % s]) for s in SEG4) for _, r in m.iterrows()]
    parts = [HEADER, '# E6p 主结果：主展示 72 行（HG10 × 六 H × 六触发 × {NATIVE, D80}；FEASIBLE）', '',
             '72 行是阅读布局，不是候选域；族中位与主对象分列。', '']
    for d in ('NATIVE', 'D80'):
        x = m[m.deploy == d].sort_values(['trigger', 'H'])
        parts += ['## %s' % d, '', md_table(x, ['trigger', 'H', 'FULL_net_ann_pp', 'FULL_D_same_h_ann_pp', 'segs', 'G4_D_same_h_ann_pp', 'FULL_D_h5_same_deploy_ann_pp',
                                                'FULL_D_h5_native_ann_pp', 'rank_vs_amount_match_v2', 'level_worst_D_ann_pp', 'FULL_D_imp_ann_pp', 'verdict_legacy', 'verdict_curve'],
                                               ['触发', 'H', 'FULL net', 'D 同 H 父', '四段 D', 'G4', 'D vs H5 同部署', 'D vs H5 NATIVE', '位次 AMT_V2', 'LEVEL_WORST 均值', 'D_imp', 'LEGACY', 'CURVE']), '']
        med = x.groupby('H').FULL_D_same_h_ann_pp.median()
        parts += ['族中位（六触发，按 H）：' + '；'.join('H%d %s' % (h, fsign(v)) for h, v in med.items()), '']
    W('E6p_REPORT_main.md', '\n'.join(parts) + '\n')
    # ---------------- 政策
    pf = rd('statistics/policy_fields_E6p.csv')
    vc = pf.groupby(['profile_name', 'field', 'value']).size().reset_index(name='n')
    und = PO[PO.verdict == '不可判'].groupby(['profile_name', 'undecidable_reason']).size().reset_index(name='n')
    kf = PO[PO.known_failure.fillna('') != ''].groupby(['profile_name', 'known_failure']).size().reset_index(name='n').sort_values('n', ascending=False).head(20)
    passed = PO[PO.verdict == '通过']
    txt = [HEADER, '# E6p 政策', '', 'verdict 只由 policy_fields 按 plan 附录 C policy_verdict 重算（显式 bool；任一 false → 不通过；无 false 有 NA → 不可判；全 true → 通过）。', '',
           '## 字段取值分布', '', md_table(vc, ['profile_name', 'field', 'value', 'n']), '', '## 不可判原因', '', md_table(und, ['profile_name', 'undecidable_reason', 'n']), '',
           '## 已知失败（前 20 种组合）', '', md_table(kf, ['profile_name', 'known_failure', 'n']), '',
           '## LEGACY_E6O_A5 通过的对象（%d 行）' % len(passed), '', md_table(passed.merge(R[['exec_id', 'logical_id', 'block', 'memory', 'H', 'trigger', 'deploy', 'cap', 'renew']], on='exec_id')
                                                                          .sort_values(['execution_profile', 'block', 'memory', 'H', 'trigger']),
                                                                          ['profile_name', 'execution_profile', 'block', 'memory', 'H', 'trigger', 'deploy', 'cap', 'renew', 'research_status'])
           if len(passed) else '无。', '']
    W('E6p_REPORT_policy.md', '\n'.join(txt) + '\n')
    # ---------------- 机制（诊断）
    mech = [HEADER, '# E6p 机制与诊断（D1–D9、landmark、镜像、再投资局部、RENEW5、WARM）', '']
    for blk, nm in (('D1', 'D1_holding'), ('D2', 'D2_deploy'), ('D3', 'D3_cost'), ('D4', 'D4_composition'), ('D5', 'D5_reinvest'), ('D6', 'D6_regime'), ('D7', 'D7_cvr'),
                    ('D8', 'D8_window'), ('D9', 'D9_discount')):
        p = os.path.join(root, 'diagnostics', '%s_E6p.csv' % nm)
        if not os.path.exists(p):
            continue
        d = pd.read_csv(p, keep_default_na=False, na_values=[''])
        main_e = set(R[R.is_main_object == '1'].exec_id)
        dm = d[d.key2.isin(main_e) | ~d.key2.str.contains('\\|', na=False)]
        mech += ['## %s（主对象与全局行；全表见 diagnostics/%s_E6p.csv，%d 行）' % (blk, nm, len(d)), '',
                 md_table(dm.head(40), ['item', 'key1', 'segment', 'stat', 'value', 'unit', 'n', 'status']), '']
    rw = RW.copy()
    mech += ['## RENEW5（36 × 2 执行对象）', '', md_table(rw.merge(R[['exec_id', 'H', 'trigger', 'deploy', 'execution_profile', 'memory']], on='exec_id').head(36),
                                                         ['memory', 'H', 'deploy', 'trigger', 'execution_profile', 'n_checkpoints', 'n_confirmed', 'n_rejected', 'n_unknown',
                                                          'n_exit_orders', 'share_new_lot_same_security']), '']
    if len(WS):
        mech += ['## WARM 四段重置敏感性（主对象对；连续全历史为主）', '', md_table(WS, ['exec_id', 'execution_profile', 'segment', 'D_ann_pp', 'D_cash_v0_ann_pp', 'D_warm_minus_cont']), '']
    fbm = FB[FB.segment == 'FULL']
    mech += ['## 成本反馈 84 路径（FULL）', '', md_table(fbm.head(84), ['owner_exec_id', 'A_cny', 'net_ann_pp_feedback', 'D_feedback_ann_pp', 'D_fixed_path_ann_pp']), '']
    W('E6p_REPORT_mechanisms.md', '\n'.join(mech) + '\n')
    # ---------------- 两账本复盘
    Gl = pd.read_csv(O.P('registration', 'ledger_G_E6p.csv'), keep_default_na=False)
    El = pd.read_csv(O.P('registration', 'ledger_E_E6p.csv'), keep_default_na=False)
    CC = pd.read_csv(O.P('registration', 'cc_statement_carry.csv'), keep_default_na=False)
    led = [HEADER, '# E6p 两账本复盘（G / E；plan §3）', '', '构思数 / 实测方向数 / 可评分经济预测数 / 工程测试数 / 策略路径数分开；工程恒等不进经济命中率；E6o E01–E07 的 7 / 7 支持不回改。', '',
           '## G 账本（G-P-01…11）', '', md_table(Gl, ['g_id', 'verbatim_expectation', 'root_status', 'observed_result']), '',
           '## E 账本（E01–E10 + 卡）', '', md_table(El, ['e_id', 'kind', 'exact_statement', 'result', 'direction', 'precision', 'heterogeneity']), '',
           '## proposal 原句携带（CC-E6p-01…11 + 文献方向句）', '', md_table(CC, ['carry_id', 'verbatim_statement', 'claim_status', 'e6p_reading'] if 'e6p_reading' in CC.columns else
                                                                ['carry_id', 'verbatim_statement', 'claim_status']), '',
           '计数：经济方向预测 10（E01–E10）；状态分布 %s。' % E_.claim_status.value_counts().to_dict(), '']
    W('E6p_REPORT_ledgers.md', '\n'.join(led) + '\n')
    # ---------------- 限制 / limit register
    lim = [HEADER, '# E6p limit register', '',
           '- 同一历史已曝光；"首次新算子运行"仍非 OOS（plan §13.1）。主对象与 72 行事前定死，不按收益选。',
           '- κ 未校准（SCENARIO_NOT_CALIBRATED）；成本曲线是固定路径情景，反馈 84 路径只是"费用入现金"的闭环，不模拟自身订单的市场影响。',
           '- BERNOULLI_LAG60 沿 E6o 定义：影子按"状态日"计触发率，对持续状态触发（T1a / LEVEL）随机路径意向数约为 owner 的 2 倍（notes §8）。',
           '- 部分成交（一字跌停日内部转移 + 次日余量）使"早退成交行数"与"已实现早退意向数"不一致（SCHEMA_DEVIATIONS；verify/trades_events_bridge_E6p.csv）。',
           '- H30 / H40 的尾端（2026 年 1–3 月）右截尾；landmark 前向窗口超授权终点记 RIGHT_CENSORED。',
           '- 2026 为部分年（至 03-27）；年表 partial_year_flag = 1。',
           '- E7 HOLD；deployment_authorized = false；本轮任何"通过"不构成上线或候选升级。', '']
    W('E6p_limit_register.md', '\n'.join(lim) + '\n')
    print(json.dumps(dict(reports=sorted(os.path.basename(p) for p in glob.glob(os.path.join(rep, '*.md')))), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
