# -*- coding: utf-8 -*-
"""E6q A1 冻结（brief §3；附录 B.7 / B.8 / B.24）：账本 G（G-P-01…12，plan §3.2）/ E（E01–E07，claims.json + plan §12.2 原句）/ Q（Q01–Q18，plan §12.1 原表）、
CC 携带（合同脚本 CSV 原样 + 执行端三列初值）、授权八值（permissions）、park（P63–P70 沿 E6p、P74 / P75 沿 E6p REVIEW）、政策 profile（LEGACY_E6O_A5 审计 +
POLICY_E6Q_A1_CANONICAL）、冻结件 freeze_E6q.json（含 S0-A 对账状态、源函数 sha、缓存标签、授权）。条款原文在运行时从 plan / 合同 json 解析，保证逐字。
用法：python3 e6q_a1.py"""
import os
import re
import json
import time

import pandas as pd

import e6q_core as O

PLAN_REG_UTC = '2026-10-22T15:00:31+00:00'
AUTHORIZED_AT = '2026-10-23T00:36:00+08:00（决策端转交消息到达执行端）'
G_COLS = ['g_id', 'author', 'created_before', 'dependency_file_sha', 'source_query', 'exposed_window', 'derived_from', 'motivation', 'statement_verbatim', 'tested_estimand',
          'comparison_ids', 'unit', 'state', 'result_query', 'result_row', 'explanation_scope', 'next_design_change']
E_EXTRA = ['object_exec_id', 'comparator_exec_id', 'A_eval_cny', 'kappa', 'exponent', 'band_lo_display', 'band_hi_display', 'band_lo_canonical', 'band_hi_canonical']
Q_COLS = ['q_id', 'author', 'created_before', 'statement_verbatim', 'tested_estimand', 'comparison_ids', 'result_query', 'result_row', 'explanation_scope', 'state']
G_ESTIMAND = {
    'G-P-01': ('S0-A 对账表（7 对象 × 6 段 × 7 类）与 ladder', 'impact_reconciliation'),
    'G-P-02': ('D1 冲击按订单类别 × 方向（推导段；臂 − 同触发 NATIVE）', 'D1'),
    'G-P-03': ('EXTRA 内重复买入份额三口径与当日合法 new 集合容量（推导段）', 'S0-B'),
    'G-P-04': ('参与率 p = 名义 / ADV20 的分布；p > 2% 的数 / 额 / 费 / 资本四种加权超限率 × 买卖 × 两 A（推导段）', 'S0-B'),
    'G-P-05': ('M4 半量后余半到期前再触发份额与余半剩余前向超额（推导段）', 'S0-B / D5'),
    'G-P-06': ('首达影子风险集分母与状态日计数之比（推导段）', 'BERNOULLI_FIRSTHIT 影子'),
    'G-P-07': ('RANDOM_TARGET 可替换性：IDENTITY 份额、match_status 分布（推导段）', 'randoms RANDOM_TARGET_*'),
    'G-P-08': ('T1a ∩ T8 证券日重叠、T8 落在 T1a 坏状态的份额（推导段）', 'S0-B'),
    'G-P-09': ('固定期限 q1 / q5 / q10 与原 due 窗口的日龄剖面（推导段 landmark）', 'D4 / landmark'),
    'G-P-10': ('两个密度（对 CASH / 同臂父）的分子分母符号（推导段）', 'D6'),
    'G-P-11': ('卖半 × 再投半四账户的推导段第一道快照（差中差）', 'compound EXIT_X_RECYCLE_HALF'),
    'G-P-12': ('D3 入场信息（K 强 / size）在存活域的 landmark 分辨（推导段）', 'D3'),
}


def plan_text():
    return open(O.P('inputs', 'E6q_plan_web_final.md'), encoding='utf-8').read()


def parse_gp(txt):
    m = re.search(r'### 3\.2 G-P清单\s*\n\s*\n(.+?)\n\s*\n', txt, re.S)
    body = m.group(1)
    parts = re.split(r'G-P(\d{2})', body)
    out = {}
    for k in range(1, len(parts), 2):
        out['G-P-%s' % parts[k]] = ('G-P%s' % parts[k] + parts[k + 1]).strip().rstrip('；。')
    if len(out) != 12:
        raise RuntimeError('G-P 解析 %d 条' % len(out))
    return out


def table_rows(txt, head, prefix):
    i = txt.index(head)
    rows = {}
    for line in txt[i:].splitlines()[1:]:
        if line.startswith('| %s' % prefix):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            rows[cells[0]] = cells
        elif line.startswith('#'):
            break
    return rows


def appendix_e():
    txt = open(O.P('inputs', 'E6q_brief_appendix_schema_probes.md'), encoding='utf-8').read()
    return table_rows(txt, '## E. 原预测携带', 'CC-E6q-')


def main():
    t0 = time.time()
    txt = plan_text()
    gp = parse_gp(txt)
    qrows = table_rows(txt, '### 12.1 Q卡', 'Q')
    erows = table_rows(txt, '### 12.2 E条款', 'E0')
    if len(qrows) != 18 or len(erows) != 7:
        raise RuntimeError('Q / E 表解析 %d / %d' % (len(qrows), len(erows)))
    claims = json.load(open(O.P('registration', 'spec', 'claims.json'), encoding='utf-8'))
    comps = json.load(open(O.P('registration', 'spec', 'comparisons.json'), encoding='utf-8'))
    bands = json.load(open(O.P('diagnostics', 'e_band_values_E6q.json'), encoding='utf-8'))
    R = O.read_csv(O.P('registration', 'registry_E6q.csv'), dtype=str)
    eid = {r.logical_id: r.exec_id for r in R.itertuples(index=False)}
    # ---- G
    G = []
    for gid in sorted(gp):
        est, blk = G_ESTIMAND[gid]
        G.append(dict(g_id=gid, author='plan v1.1 §3.2（决策端第一道 / plan 新增测量前问题；执行端复刻 G1）', created_before=PLAN_REG_UTC, dependency_file_sha=O.PLAN_SHA256,
                      source_query='diagnostics/G1_E6q.csv block=%s' % gid, exposed_window='E6p FULL 已暴露（2010-01-04…2026-03-27）；G1 只读两推导段（2010-2014、2015-2018）',
                      derived_from='F（E6p REVIEW / numbers）' if gid in ('G-P-01', 'G-P-02') else 'plan v1.1 §2–§3（新测量）',
                      motivation='plan §2.2 / §2.3：三条折扣之后新增的可辨别问题；不按 G 收益筛分支', statement_verbatim=gp[gid], tested_estimand=est, comparison_ids='',
                      unit='mixed（见 G1 行 unit）', state='PRESPECIFIED_DISCRIMINATING_TEST', result_query='QRY-G1-%s' % gid, result_row='', explanation_scope=blk,
                      next_design_change='下一轮依 G1 / 全史结果登记新 E；本轮不中途补写'))
    O.atomic_write_csv(O.P('registration', 'ledger_G_E6q.csv'), pd.DataFrame(G, columns=G_COLS))
    # ---- E
    E = []
    for e in claims['e']:
        obj, cmpid = e['object_id'], e['comparator_id']
        cid = [c['id'] for c in comps if c['left'] == obj and c['right'] == cmpid]
        b = bands[e['id']]
        row = erows[e['id']]
        E.append(dict(e_id=e['id'], author='plan v1.1 §12.2（plan 作者正式经济预测；claims.json）', created_before=e['first_registered_utc'], dependency_file_sha=e['dependency_sha256'],
                      source_query='; '.join(e['dependencies']), exposed_window='E6p FULL 已暴露；首测新算子，同历史复用，不称独立验证', derived_from='E6p REVIEW numbers（%s）' % e['scope'],
                      motivation=e['motivation'], statement_verbatim='%s：%s（原数字带 %s；端点 %s）' % (e['id'], row[1], row[2], row[3]),
                      tested_estimand='%s；FULL 共同支持；%s；A_eval %s；κ %s δ %s；带内 = 支持、带外 = 不支持（端点不交换）' % (e['scope'], e['cost_mode'], e.get('A_eval'), e['kappa'], e['delta']),
                      comparison_ids=';'.join(cid), unit='ann_pp', state='OPEN', result_query='QRY-E-%s' % e['id'], result_row='', explanation_scope=e['band_semantics'],
                      next_design_change=e['upper_failure'], object_exec_id=eid[obj], comparator_exec_id=eid[cmpid],
                      A_eval_cny='' if e.get('A_eval') is None else int(e['A_eval']), kappa=e['kappa'], exponent=e['delta'],
                      band_lo_display=b['band_lo_display'], band_hi_display=b['band_hi_display'], band_lo_canonical=b['band_lo_canonical'], band_hi_canonical=b['band_hi_canonical']))
    O.atomic_write_csv(O.P('registration', 'ledger_E_E6q.csv'), pd.DataFrame(E, columns=['e_id'] + G_COLS[1:] + E_EXTRA))
    # ---- Q
    Q = []
    for qid in sorted(qrows):
        c = qrows[qid]
        Q.append(dict(q_id=qid, author='plan v1.1 §12.1（开放问题，完整运行，不评分）', created_before=PLAN_REG_UTC, statement_verbatim='%s：%s' % (qid, c[1]), tested_estimand=c[2],
                      comparison_ids='', result_query='QRY-Q-%s' % qid, result_row='', explanation_scope=c[3], state='OPEN'))
    O.atomic_write_csv(O.P('registration', 'ledger_Q_E6q.csv'), pd.DataFrame(Q, columns=Q_COLS))
    # ---- CC 携带（合同脚本 CSV 原样 + 三列初值；最终值在 claims 阶段写）
    cc = pd.read_csv(O.P('registration', 'spec', 'cc_statement_carry.csv'), keep_default_na=False, dtype=str)
    ae = appendix_e()
    cc['estimand_note'] = [('%s｜%s' % (ae[i][1], ae[i][2])) if i in ae else '' for i in cc['id']]
    cc['comparable'] = '待评'
    cc['claim_status'] = '开放'
    vb = {x['id']: x['verbatim'] for x in claims['cc']}
    if any(vb[r.id] != r.verbatim for r in cc.itertuples(index=False)) or len(cc) != 11:
        raise RuntimeError('CC 携带原句与 claims.json 不一致')
    O.atomic_write_csv(O.P('registration', 'cc_statement_carry.csv'), cc)
    # ---- 授权（八值 + 协议 / 方式）
    au = O.AUTHORIZATIONS
    perm = [dict(key=k, value=json.dumps(au[k]) if isinstance(au[k], (list, bool)) else str(au[k]), authorized_by=O.AUTHORIZED_BY, authorized_at=AUTHORIZED_AT) for k in au]
    perm += [dict(key='protocol', value='v1.6', authorized_by=O.AUTHORIZED_BY, authorized_at=AUTHORIZED_AT), dict(key='mode', value='B', authorized_by=O.AUTHORIZED_BY, authorized_at=AUTHORIZED_AT)]
    O.atomic_write_csv(O.P('registration', 'permissions_E6q.csv'), pd.DataFrame(perm))
    # ---- park
    pk = O.read_csv(O.E6P('registration', 'park_E6p.csv'), dtype=str)
    pk = pk[pk.park_id.isin(['P63', 'P64', 'P65', 'P66', 'P67', 'P68', 'P70'])].copy()
    pk['status'] = 'PARKED'
    add = [dict(park_id='P69', domain='资金去向 CASH_REMAIN / ORIGINAL_DUE（E6o −1.02 / −.71；E6p 有限重开九行：LEVEL 未加冲击 −1.20 / −7.67 / −10.66，5 亿后 +3.34 / +2.87 / +1.62）',
                condition='E6q 只作参照臂（η = 0）不作候选；恢复 = A ≥ 2–3 亿（T1a 不恢复）', status='PARKED_REFERENCE_ARM'),
           dict(park_id='P74', domain='RENEW5 五日完整自然门重新确认 × {H20, H40} × {NATIVE, D80} × {NONE, T1a, LEVEL} × 三记忆（对无 RENEW5 −3.55…−4.88 LEVEL / +.30…−1.62 T1a）',
                condition='恢复 = 换时钟（只在原到期日确认）或换门（第一关 / 成本感知 / 持有资格自己的测量族）', status='PARKED'),
           dict(park_id='P75', domain='固定预算成本路由 RECYCLE_COST0 / COSTNET × {H5, H20, H40} × {T1a, LEVEL} × A ≤ 1 亿（κ .5 δ .5）',
                condition='恢复 = 用户 A ≥ 3 亿或 κ 校准后曲线仍正；若 M2 / M3 成立改写为"路由加质量项"另登记', status='PARKED')]
    pk = pd.concat([pk, pd.DataFrame(add)], ignore_index=True).sort_values('park_id')
    O.atomic_write_csv(O.P('registration', 'park_E6q.csv'), pk)
    # ---- 政策 profile
    e6p_pp = json.load(open(O.E6P('registration', 'policy_profile_E6p.json'), encoding='utf-8'))
    leg = dict(e6p_pp['LEGACY_E6O_A5'])
    leg['e6q_domain'] = 'H ∈ {5, 20} 可判（E6o 适用域内的 H）；H30 → 不可判（H_DOMAIN_NOT_IN_LEGACY）；c5 照原式（legacy D_imp，A = 5 亿、κ .5），只审计'
    canon = dict(fields={
        'c1': '四段 D_same_arm ≥ −.10（D = 账户 − 同臂无退出父；net8）',
        'c2': '17 年（2026 部分年）D > 0 的年份 ≥ 12；c2_year_positive_share 并印',
        'c3': 'sign(FULL D) = sign(FULL D_sc)（同资本视图）',
        'c4': '主金额随机 AMOUNT_MATCH_V2：两后段 real − rand_mean ≥ 2·MCSE（IDEAL 无随机 → 不可判 RANDOM_NOT_COVERED）',
        'c5': '主成本档：CANONICAL 仪器（S0-A 选定；curve，A_e = A·n_e）A = 1 亿、κ .5、δ .5 后四段 D ≥ −.10；副读 .5 / 5 亿各一列；S0-A 未闭合 → NA（UNDECIDABLE_RECONCILIATION）',
        'c6': '机制 / 配置事前声明（A1 冻结件内）',
        'port3t': 'PORT3_T：全组合目标 clean 市值分位加权均值相对父 ×100，四段段均值 ∈ [−3, +3]',
        'positive': 'FULL D ≥ +.10'},
        verdict_rule='任一字段 false → 不通过；无 false 有 NA → 不可判（附 undecidable_reason）；全 true → 通过（字段显式 Python bool）',
        kappa_consistent='κ .5 与 κ 1 下主成本档 FULL D 同号；只作采纳候选列，不作门',
        research_status={'未覆盖': 'status ≠ COMPUTED 或 FULL 无实际退出意向', '方向不支持': 'FULL D ≤ 0 且 G4 ≤ 0', '有改善点估': 'FULL D ≥ +.10 且 G4 > 0',
                         '结构依赖': 'FULL D > 0 且（G4 ≤ 0 或四段中 ≥ 2 段 < 0）', '证据有限': '其余', 'note': '研究状态不是资格门；E6q 无源父，不用 D_source 条件'},
        A_main_cny=100000000, A_sub_cny=[50000000, 500000000], kappa_main=0.5, kappa_sens=1.0, delta_main=0.5, delta_curve=[0.7, 1.0],
        qualification_reference='同臂无退出父（parent_same_arm）；推进同触发 NATIVE 与新前沿锚是另一列经济升级', approval_status='PROPOSED_E6Q')
    pp = dict(LEGACY_E6O_A5=leg, POLICY_E6Q_A1_CANONICAL=canon)
    O.atomic_write_json(O.P('registration', 'policy_profile_E6q.json'), pp)
    # ---- 冻结件
    fsh = json.load(open(O.P('diagnostics', 'source_fn_sha256_E6q.json'), encoding='utf-8'))
    s0a = json.load(open(O.P('diagnostics', 's0a_facts_E6q.json'), encoding='utf-8'))
    apx = open(O.P('inputs', 'E6q_brief_appendix_schema_probes.md'), encoding='utf-8').read()
    schema_txt = apx[apx.index('## B. SCHEMA'):apx.index('## C. 闭包门')]
    fz = dict(plan_sha256=O.PLAN_SHA256, contract_sha256=O.CONTRACT_SHA256, brief_sha256=O.BRIEF_SHA256, appendix_sha256=O.APPENDIX_SHA256, d_script_sha256=O.D_SCRIPT_SHA256,
              schema_contract_sha256=O.sha_bytes(schema_txt.encode()), policy_file_sha256=O.sha_file(O.P('registration', 'policy_profile_E6q.json')),
              source_fn_sha256={k: fsh[k] for k in ('engine', 'b2_trigger', 'veto_t1a', 'limit_fields', 'fee', 'vwap', 'cost_adv', 'cost_sigma', 'token_ledger', 'net_order',
                                                   'payment_route', 'industry', 'edge_spread', 'amihud', 'legacy_impact', 'curve_impact')},
              data_cutoff=O.CUTOFF, protocol='v1.6', mode='B', authorizations=dict(O.AUTHORIZATIONS), authorized_by=O.AUTHORIZED_BY, authorized_at=AUTHORIZED_AT,
              written_at=time.strftime('%Y-%m-%d %H:%M:%S'), cache_tag=O.CACHE_TAG, cache_dir=os.path.basename(O.cache_dir()),
              e6p_registry_sha256=O.sha_file(O.E6P('registration', 'registry_E6p.csv')), reconciliation_status=s0a['status'],
              registry_sha256=O.sha_file(O.P('registration', 'registry_E6q.csv')), json_sha256=dict(O.JSON_SHA), proposal_sha16=O.PROPOSAL_SHA256,
              engine_selftest=dict(e6p_replication='132/132 PASS', identities_bad=0), code_sha256={f: O.sha_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), f))
                                                                                               for f in ('e6q_engine.py', 'e6q_acct.py', 'e6q_core.py', 'e6q_cost.py', 'e6q_rules.py')})
    O.atomic_write_json(O.P('registration', 'freeze_E6q.json'), fz)
    outs = [O.P('registration', x) for x in ('ledger_G_E6q.csv', 'ledger_E_E6q.csv', 'ledger_Q_E6q.csv', 'cc_statement_carry.csv', 'permissions_E6q.csv', 'park_E6q.csv',
                                             'policy_profile_E6q.json', 'freeze_E6q.json')]
    O.write_receipt('E6q_a1', outs, code=[__file__, O.__file__], reconciliation_status=s0a['status'], wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(G=len(G), E=len(E), Q=len(Q), CC=len(cc), perm=len(perm), park=len(pk), reconciliation=s0a['status']), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
