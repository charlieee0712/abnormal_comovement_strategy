# -*- coding: utf-8 -*-
"""E6r 报告（brief §8：R0 总览 / 主结果 / 政策 / 机制与随机 / 账本 / limit register）。
数字只从机器表取（statistics / diagnostics / events / reports / verify）；缺失写 —（不写字面 nan / None）；不写登录信息、主机标识或用户目录；
读法纪律：主对象差与族分布分列、四段符号旁印、结论带角色标签（入场 / 退出 / 参照 / 读法），不替决策端下结论。
用法：python3 e6r_reports.py [--root <相对 E6R_WORK 的根>]"""
import os
import json
import glob
import argparse

import numpy as np
import pandas as pd

import e6r_core as O

SEG4 = list(O.SEGS)
AUTH = O.AUTHORIZATIONS
HEADER = ('> **页首声明**：E6r 执行交付（协议 **v1.6**、**方式 B**；brief d6cdc0b3 / 附录 5dc01f4e / plan v1.1 c89305fb / 合同脚本 7aa0338f / D 脚本 51256b05 / proposal v1.2 e3114b07）。'
          '市场历史截止 2026-03-27；**E7 不做（e7 = HOLD，不读）**；**deployment_authorized = false**；生产配置 / I11 事件定义 / 观察窗 / K/T/C/Q 原测量 / 候选库 / 原因子缓存不动。'
          '授权九值（用户 2026-10-24 消息，决策端转交）：main_A_cny = %s；sub_A_cny = %s；research_metric = %s；product_metric = %s；frontier_anchor_logical_id = %s；'
          'mainline = %s；deployment_authorized = false；e7 = HOLD；r5_single_stock_research_parameter = %s（R5 研究单股上界 1.5%%，只在研究账户——TILT 族与 UNIFORM_CAP15——'
          '使用；其余账户与 E6q 同为 1%%）。连续全历史（CASH_V0）为主读；数字全部来自机器表；结论带角色标签，不替决策端下结论。\n'
          % (AUTH['main_A_cny'], AUTH['sub_A_cny'], AUTH['research_metric'], AUTH['product_metric'], AUTH['frontier_anchor_logical_id'], AUTH['mainline'],
             AUTH['r5_single_stock_research_parameter']))


def f2(x, d=2):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return '—' if (x is None or str(x).strip() in ('', 'nan', 'None', 'NaN')) else str(x)
    if not np.isfinite(v):
        return '—'
    return ('%+.' + str(d) + 'f') % v


def fs(x, d=2):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return '—'
    return ('%.' + str(d) + 'f') % v if np.isfinite(v) else '—'


def md_table(rows, heads):
    out = ['| ' + ' | '.join(heads) + ' |', '|' + '---|' * len(heads)]
    for r in rows:
        out.append('| ' + ' | '.join(str(x).replace('|', '/') for x in r) + ' |')
    return out


class C(object):
    pass


def load(root):
    c = C()
    rd = lambda rel: pd.read_csv(os.path.join(root, rel) if os.path.exists(os.path.join(root, rel)) else os.path.join(root, rel) + '.gz', dtype=str,
                                 keep_default_na=False) if (os.path.exists(os.path.join(root, rel)) or os.path.exists(os.path.join(root, rel) + '.gz')) else pd.DataFrame()
    c.R = O.read_csv(O.P('registration', 'registry_E6r.csv'))
    c.reg = c.R.set_index('exec_id', drop=False)
    c.AS = rd('statistics/account_summary_E6r.csv')
    c.sm = {(r.exec_id, r.segment): r for r in c.AS.itertuples(index=False)}
    c.P9 = rd('statistics/primary9_E6r.csv')
    c.PO = rd('statistics/policy_E6r.csv')
    c.RD = rd('statistics/randoms_E6r.csv')
    c.FE = rd('statistics/random_tilt_feasibility_E6r.csv')
    c.ER = rd('reports/e_results_E6r.csv')
    c.CL = rd('reports/claims_E6r.csv')
    c.KR = rd('statistics/compound_results_E6r.csv')
    c.ID = rd('verify/identities_E6r.csv')
    c.REP = rd('verify/replication_E6r.csv')
    c.G1 = rd('diagnostics/G1_E6r.csv') if len(rd('diagnostics/G1_E6r.csv')) else pd.read_csv(O.P('diagnostics', 'G1_E6r.csv'), dtype=str, keep_default_na=False)
    return c


def short(c, e):
    r = c.reg.loc[e]
    return '%s / %s / H%s / %s' % (r.weight_scheme, r.trigger, r.funding_H, r.exit_op)


def r0(c, Wt):
    hl = []
    if len(c.P9):
        n_pos = int(sum(1 for v in c.P9.FULL_D_policy_ann_pp if v not in ('', None) and float(v) > 0))
        n_obj = int(sum(1 for v in c.P9.FULL_D_policy_ann_pp if v not in ('', None)))
        hl.append('- **[读法] 主 9 对政策参照（同退出 FLAT / 无退出父）**：FULL D 为正 %d / %d 行（全表见 E6r_REPORT_main.md；四段符号旁印，不从单行下结论）。' % (n_pos, n_obj))
    if len(c.ER):
        hl.append('- **[读法] E01–E07（plan score_e）**：%s。' % '；'.join('%s %s（%s）' % (r.e_id, r.status, f2(r.value)) for r in c.ER.itertuples(index=False)))
    cc = c.CL[c.CL.kind == 'CC'] if len(c.CL) else c.CL
    if len(cc):
        hl.append('- **[读法] CC-E6r-01…09 句级**：%s（子条款见 E6r_REPORT_ledgers.md）。' % '；'.join('%s %s' % (r.claim_id[-2:], r.claim_status) for r in cc.itertuples(index=False)))
    if len(c.PO):
        m = c.PO[c.PO.mapping == 'E6R_POLICY_ESTIMAND']
        hl.append('- **[参照] 政策（主映射 E6R_POLICY_ESTIMAND，profile POLICY_E6Q_A1_CANONICAL）**：%s；研究状态 %s。' % (
            '、'.join('%s %d' % kv for kv in m.verdict.value_counts().items()), '、'.join('%s %d' % kv for kv in m.research_status.value_counts().items())))
    if len(c.ID):
        hl.append('- **[参照] 恒等**：%d 项（%s）；58 个 E6q 同坐标锚逐日复现 %s。' % (len(c.ID), '、'.join('%s %d' % kv for kv in c.ID.status.value_counts().items()),
                                                              '全部 PASS' if (len(c.REP) and (c.REP.status == 'PASS').all()) else '见 verify/replication_E6r.csv'))
    body = [HEADER, '# E6r 报告 R0：总览', ''] + hl + ['', '## 文件', '',
                                                      '- E6r_REPORT_main.md：主 9 与 E / CC 对象读数（四段、FULL、G4、成本后、产品读法）',
                                                      '- E6r_REPORT_policy.md：两映射 × 350 的政策裁定分布与不可判原因',
                                                      '- E6r_REPORT_mechanisms.md：随机控制（1,408 引用）、入场随机可行性、第二块复合',
                                                      '- E6r_REPORT_ledgers.md：G 第一道标签、Q 卡、CC 子条款、E 账',
                                                      '- E6r_limit_register.md：MC_LIMIT / 不可比 / 结构退化 / 触限份额等限制登记',
                                                      '- SCHEMA.md / SCHEMA_DEVIATIONS.md：表结构与偏离', '']
    Wt('E6r_REPORT_R0.md', '\n'.join(body) + '\n')


def main_report(c, Wt):
    parts = [HEADER, '# E6r 主结果（主 9 + E / CC 对象）', '', '## 主 9（FEASIBLE；D = 本账户 − 政策参照，ann_pp）', '']
    rows = []
    for r in c.P9.itertuples(index=False):
        rows.append([short(c, r.exec_id), f2(r.FULL_net_ann_pp), f2(r.FULL_D_policy_ann_pp), f2(r.FULL_gross_D_policy_ann_pp), f2(r.G4_D_policy_ann_pp),
                     ' / '.join(f2(c.sm[(r.exec_id, s)].D_policy_ann_pp) for s in SEG4),
                     f2(r.cost_1e8_D_policy_ann_pp), f2(r.cost_5e8_D_policy_ann_pp), f2(r.abs_net_ann_pp), fs(r.max_drawdown_total, 3), fs(r.rank_vs_c4, 3),
                     r.verdict, r.research_status])
    parts += md_table(rows, ['对象', 'FULL net', 'FULL D', 'FULL gross D', 'G4 D', '四段 D（10–14 / 15–18 / 19–23 / 24–26）', '1 亿成本后 D', '5 亿成本后 D', '绝对净值年化',
                             'MDD', 'rank vs c4', '裁定', '研究状态'])
    parts += ['', '## E01–E07（plan score_e；带上端开放）', '']
    rows = [[r.e_id, '%s vs %s' % (short(c, r.owner_exec_id), short(c, r.reference_exec_id)), r.statistic, f2(r.value, 3), '[%s, %s]' % (fs(r.lower, 3), fs(r.upper, 3)), r.status,
             r.working_range or '—'] for r in c.ER.itertuples(index=False)]
    parts += md_table(rows, ['E', '对象', '统计量', '值', '带', '状态', '工作区间'])
    parts += ['', '读法：E 状态只按登记的带与 score_e；越上端（ABOVE_WORKING_RANGE）不否认方向支持；量级不是合格门。', '']
    Wt('E6r_REPORT_main.md', '\n'.join(parts) + '\n')


def policy_report(c, Wt):
    txt = [HEADER, '# E6r 政策（两映射 × 350；POLICY_E6Q_A1_CANONICAL 阈值不改）', '']
    for m in ('E6R_POLICY_ESTIMAND', 'E6Q_ORIGINAL_AUDIT'):
        x = c.PO[c.PO.mapping == m]
        if not len(x):
            continue
        txt += ['## %s' % m, '']
        g = x.groupby(['scenario', 'policy_estimand', 'verdict']).size().reset_index(name='n')
        txt += md_table([[r.scenario, r.policy_estimand, r.verdict, r.n] for r in g.itertuples(index=False)], ['情景', '估计对象', '裁定', '数'])
        u = x[x.verdict == '不可判'].undecidable_reason.value_counts()
        txt += ['', '不可判原因：%s' % ('、'.join('%s %d' % kv for kv in u.items()) or '—'), '']
        kf = x[x.known_failure != ''].known_failure.str.split(';').explode().value_counts()
        txt += ['不通过字段（可多选）：%s' % ('、'.join('%s %d' % kv for kv in kf.items()) or '—'), '']
    Wt('E6r_REPORT_policy.md', '\n'.join(txt) + '\n')


def mech_report(c, Wt):
    mech = [HEADER, '# E6r 机制与随机', '', '## 随机控制（FULL 行；real − 随机均值，ann_pp）', '']
    if len(c.RD):
        fr = c.RD[c.RD.segment == 'FULL']
        rows = []
        for m, g in fr.groupby('mechanism'):
            d = pd.to_numeric(g.real_D_ann_pp, errors='coerce') - pd.to_numeric(g.rand_mean_D_ann_pp, errors='coerce')
            mc = pd.to_numeric(g.mcse, errors='coerce')
            rows.append([m, len(g), int((d > 0).sum()), int((d >= 2 * mc).sum()), int((g.status == 'MC_LIMIT').sum()), int((g.status == 'CONTROL_NOT_COMPARABLE').sum()),
                         int((g.status == 'STRUCTURAL_DEGENERATE').sum()), fs(np.nanmedian(pd.to_numeric(g.paths, errors='coerce')), 0)])
        mech += md_table(rows, ['机制', '引用', 'real − 均值 > 0', '≥ 2 MCSE', 'MC_LIMIT', '不可比', '结构退化', '路径数中位'])
    if len(c.FE):
        f = c.FE[c.FE.segment == 'FULL']
        mech += ['', '## 入场随机可行性（FULL；求得首个可行映射 / 无解 / 触限）', '']
        rows = []
        for m, g in f.groupby('mechanism'):
            nd = pd.to_numeric(g.n_cohort_draws, errors='coerce').sum()
            rows.append([m, len(g), int(nd), fs(pd.to_numeric(g.n_nonidentity_draw, errors='coerce').sum() / nd if nd else np.nan, 4),
                         fs(pd.to_numeric(g.n_identity_draw, errors='coerce').sum() / nd if nd else np.nan, 4),
                         fs(pd.to_numeric(g.n_algorithm_limit, errors='coerce').sum() / nd if nd else np.nan, 4)])
        mech += md_table(rows, ['机制', '引用', '抽样', '非恒等份额', '恒等份额', '触限份额'])
        mech += ['', '注：TICKETS / JOINT 的节点上限 2 万（notes §8）；触限当日该路径保留同快照 would-be 真实票据（原映射见证），按限制登记，不当经济 HIT。', '']
    if len(c.KR):
        mech += ['', '## 四账户复合（FULL；I = R_AB − R_A − R_B + R_0）', '']
        k = c.KR[c.KR.segment == 'FULL']
        mech += md_table([[r.contrast_id, r.kind, f2(r.I_net_ann_pp), f2(r.M_A_net_ann_pp), f2(r.M_B_net_ann_pp), f2(r.AB_minus_max_net_ann_pp),
                           '[%s, %s]' % (f2(r.boot_lo_AB_minus_max), f2(r.boot_hi_AB_minus_max))] for r in k.itertuples(index=False)],
                         ['复合', '种类', 'I', 'M_A', 'M_B', 'AB − max', 'AB − max 95%'])
    Wt('E6r_REPORT_mechanisms.md', '\n'.join(mech) + '\n')


def ledgers_report(c, Wt):
    led = [HEADER, '# E6r 账本（G 第一道 / Q / CC 子条款 / E）', '', '## G（第一道标签；只打标签不选支）', '']
    if len(c.CL):
        g = c.CL[c.CL.kind == 'G']
        led += md_table([[r.claim_id, r.statement[:80], r.claim_status, r.note[:60]] for r in g.itertuples(index=False)], ['G', '原句（截）', '标签', '备注'])
        led += ['', '## CC（句级 + 子条款）', '']
        for r in c.CL[c.CL.kind == 'CC'].itertuples(index=False):
            led += ['### %s：%s' % (r.claim_id, r.claim_status), '', '读法：%s' % r.note, '']
            s = c.CL[(c.CL.kind == 'CC_SUB') & (c.CL.claim_id.str.startswith(r.claim_id))]
            led += md_table([[x.claim_id[len(r.claim_id):], x.statement, f2(x.result_value, 3), x.claim_status] for x in s.itertuples(index=False)],
                            ['子条款', '内容', '值', '状态'])
            led += ['']
        led += ['## Q（开放问题卡，只报）', '']
        q = c.CL[c.CL.kind == 'Q']
        led += md_table([[r.claim_id, r.statement[:70], f2(r.result_value, 3), r.note[:50]] for r in q.itertuples(index=False)], ['Q', '问题（截）', '读数', '备注'])
    Wt('E6r_REPORT_ledgers.md', '\n'.join(led) + '\n')


def limit_register(c, Wt):
    lim = [HEADER, '# E6r limit register（限制登记）', '']
    if len(c.RD):
        fr = c.RD[c.RD.segment == 'FULL']
        for st in ('MC_LIMIT', 'CONTROL_NOT_COMPARABLE', 'STRUCTURAL_DEGENERATE', 'NOT_RUN'):
            x = fr[fr.status == st]
            lim += ['- %s：%d 条引用（%s）' % (st, len(x), '、'.join('%s %d' % kv for kv in x.mechanism.value_counts().items()) or '—')]
    lim += ['- 入场 TICKETS / JOINT 求解器：E6q rt_match，节点上限 2 万；触限份额见 E6r_REPORT_mechanisms.md 与 statistics/random_tilt_feasibility_E6r.csv。',
            '- 局部快照：RAW_TILT_WITHIN_CELL_TICKETS（122）与 GATE_TILT 两种部分随机（12）本轮不另跑（NOT_APPLICABLE + 缺因）。',
            '- GW08：混合 Q 真实分数与记忆年龄不在缓存 → NOT_COMPUTABLE（代理并报）。',
            '- D10 TAIL30：分钟依赖，只读，不入本轮门或权重。', '']
    Wt('E6r_limit_register.md', '\n'.join(lim) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    root = O.P(*a.root.split('/')) if a.root else O.work()
    rep = os.path.join(root, 'reports')
    os.makedirs(rep, exist_ok=True)

    def Wt(name, txt):
        O.atomic_write_text(os.path.join(rep, name), txt)
    c = load(root)
    r0(c, Wt)
    main_report(c, Wt)
    policy_report(c, Wt)
    mech_report(c, Wt)
    ledgers_report(c, Wt)
    limit_register(c, Wt)
    print(json.dumps(dict(reports=sorted(os.path.basename(p) for p in glob.glob(os.path.join(rep, '*.md')))), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
