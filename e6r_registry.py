# -*- coding: utf-8 -*-
"""E6r A1 注册（brief §3 / 附录 B.1–B.7、B.13、B.24；plan §11.0）：合同脚本 11 件产物（registration/spec，sha = plan 附录 B）→ 机器表。
- registry_E6r.csv（350）：logical_id 从 spec 逐行重算（plan canon）；exec_id 六段；exec_hash = sha256(exec_id | source_fingerprint)[:16]
  （source_fingerprint = 源数据 / 缓存 / 限制价 / 行业 / 费用 / 初始状态指纹的 sha16，代码版本另在结果 meta 与 deploy_log）；八种基础引用列与 H30→H20、H40→H30
  同规则列 = comparisons.json 边（存 exec_id）；政策两映射列（brief §0.1 #6 / #7）；复现绑定（附录 G.1 的 58 个 = E6Q；H40 与 E6p 同坐标唯一匹配 = E6P；其余 NEW_COORDINATE）。
- comparisons / compound / random_control_refs / cost_feedback_refs / feedback_comparisons / local_snapshot_refs：逐项 = spec，id 公式 = 附录 F。
- 账本：ledger_G（G-P-01…04 = brief §0.1 #21；GW01–GW08 = plan §3 原文）、ledger_E（claims.json 原值，created_before = 2026-10-23T23:38:25+00:00）、
  ledger_Q（Q01–Q18 = plan §12.1）、cc_statement_carry（合同 CSV 原样 + 五列，claims 阶段填）、G_E_CC_dependency_ledger（E 依赖 = 附录 G.2 机器表行）。
- permissions（九授权 + protocol / mode）、exposure、park（P62 / P69 / P74–P79 + P80–P83 RESERVED）、statistics/policy_mapping_E6r.csv。
用法：python3 e6r_registry.py"""
import os
import re
import json
import time
import hashlib

import numpy as np
import pandas as pd

import e6r_core as O

BASE_KIND_COL = {'ENTRY_OVERLAY_VS_SAME_EXIT_FLAT': 'flat_same_exit_exec_id', 'SAME_TRIGGER_NATIVE_FLAT': 'native_same_trigger_flat_exec_id',
                 'EXIT_VS_SAME_OVERLAY_NO_EXIT': 'noexit_same_overlay_exec_id', 'H5_LOCAL_PARENT': 'h5_local_exec_id', 'H5_GLOBAL_PARENT': 'h5_global_exec_id',
                 'FRONTIER_E6P_T1A_H20': 'frontier_exec_id', 'SCALE_REFERENCE_EXIT_GATE_LIQ_1E8': 'scale_ref_gate_exec_id',
                 'SCALE_REFERENCE_EXIT_HALF_REARM': 'scale_ref_rearm_exec_id'}
NOT_CANDIDATE = ('UNIFORM_CAP15', 'TILT_SIZE_L050')
G_P = [('G-P-01', 'CC', 'F1 §3.5 表 1：CVR20 / size / K 强 / K0 × age1 / 5 / 10 + q10 行（D3 = DERIV）', 'DERIV_2010_2018'),
       ('G-P-02', 'CC', 'F1 §3.5 表 2：LEVEL / T1a / NONE 三账户坏状态与存活（landmark / D4 透视 = FULL）', 'FULL_SEEN'),
       ('G-P-03', 'CC', 'F1 §3.5 表 3：第二块 E6q 读数（门控 / REARM / 并集 / H30）', 'FULL_SEEN'),
       ('G-P-04', 'CC', 'F1 §3.5 量级原算式：GATE / TILT / TILT_H / UNIFORM 四条，原式照录 + plan 的 λ/3 修正并列', 'FULL_SEEN')]
GW = [('GW01', 'T0状态对源下一次买入后的可执行q1/q5/q10及原due收益是否区分'),
      ('GW02', 'CVR20同源域、最终cohort两类分位及资本加权差'),
      ('GW03', 'CVR5是否增加第一周分辨而非只加噪'),
      ('GW04', 'industry×size格内CVR是否仍有方向'),
      ('GW05', '允许的1.5%与行业预算下实际权重转移'),
      ('GW06', '门控×REARM的卖单预算/持续坏态/排队重合'),
      ('GW07', '时点×排名是否源别名'),
      ('GW08', '混合Q真实分数、记忆年龄等代理离散度及时间剖面')]
Q_CARDS = [('Q01', 'T0坏态是否预示入场后短期损害？未来age1坏态未必能预判', '转移矩阵、T0组q1/q5及可执行窗口；重叠低则时钟限制'),
           ('Q02', 'Gate能否省掉有害往返？净额抵消可能使删买单增加净卖费', '三退出Gate−Flat及count/amount随机；gross、fee分别报'),
           ('Q03', 'CVR20倾斜能否变成账户改善？size/约束/后续资本可抵消', '同名单/目标资本、随机、日龄贡献、E01–03'),
           ('Q04', '.25是否更稳？较小改动可能少赚也少费', '两λ同坐标直接差，不规定单调或挑最佳'),
           ('Q05', 'DROP与软倾斜：坏组收益为正也可能值得保留', 'Drop−Flat、Drop−random、资本与产品差'),
           ('Q06', 'TILT_H是否与快信息错配？长期共同alpha可能仍值得拿', '真实H映射−固定H与随机H；不把正结果自动称原时间读法错'),
           ('Q07', 'Uniform提高的是已有alpha规模还是beta/风格？', '三收益口径/同资本/费用；不写“超额>.5就是新信息”'),
           ('Q08', 'CVR vs SIZE差能否由粗风格解释？', '3×3、CELL−raw、real−random；不是只比较两政策符号'),
           ('Q09', 'CVR5更贴近新状态还是更嘈杂？', '固定CVR5−20，S0方向先记，无E前测不编造'),
           ('Q10', 'GATE×TILT是否互补？资格减少可能削弱tilt机会', '四账户交互与共同支持；新组别不二次改标签'),
           ('Q11', '新entry overlay是否提高门控前沿？', '门控入口桥及相应四账户，不借旧LEVEL退出增量'),
           ('Q12', 'REARM×门控互补还是重复延迟？', '分量、deadline、余量风险及E06/07'),
           ('Q13', 'LEVEL∨T8是否增量？重叠时点可能已吸收', '同LEVEL差、同T8差、交集及净单，E04/05'),
           ('Q14', 'T1a时点×LEVEL排名是新对象还是旧控制？', '源码/意向/目标/交易/日收益指纹同构；相同归R'),
           ('Q15', 'H40是否推进H30？低成本与共同收益而非新增状态信息', '恒定规则/产品回撤/截尾，不选最大H'),
           ('Q16', '所有权重/成本差来自哪里？', '形成→买入→净单→库存→收益的金额桥与CAP视图'),
           ('Q17', '第一道与正式域不一致造成多少偏差？', '源分位→cohort分位、事件/资本权重、DERIV/FULL身份并列'),
           ('Q18', '本轮是否留下跨轮锁定？', '全部原父可回退、每个新测量只带准确适用域与恢复理由')]
PARK = [('P62', '分钟级 Q 补充族（入场 / 交易角色）× 六形态 × η/λ ≤ .5', '本轮只许 TAIL30 只读诊断（D10），不恢复分钟交易', 'PARKED'),
        ('P69', 'CASH_REMAIN 资金去向（参照臂 η = 0，不作候选）', '恢复 = A ≥ 2–3 亿且 LEVEL 冲击后为正；T1a 不恢复', 'PARKED'),
        ('P74', 'RENEW5 五日完整自然门重新确认 × {H20, H40} × {NATIVE, D80} × {NONE, T1a, LEVEL} × 三记忆', '恢复 = 自然门以非换手代价改善', 'PARKED'),
        ('P75', '固定预算成本路由 RECYCLE_COST0 / COSTNET × A ≤ 1 亿', '恢复 = 用户定规模 ≥ 5 亿或路由加质量项', 'PARKED'),
        ('P76', 'M1 REINVEST_NEW 新名字再投 × LEVEL / T1a × H20 / 30 × A ≤ 5 亿（A4b_CVRv5 × HG10 × FEASIBLE）', '恢复 = 目标选择含信息（RANDOM_TARGET − 真实 ≥ .5）；本轮不改名解封', 'PARKED'),
        ('P77', 'M2 REINVEST_LIQ 流动性再投 × A_ref（同域）', '恢复 = 买方成为约束侧（买方 > 2% 参与份额 > .5）；本轮不改名解封', 'PARKED'),
        ('P78', '主 M4 EXIT_HALF 到期半量（同域）', '恢复 = 有理由认为退出信息集中在部分剂量；本轮不改名解封', 'PARKED'),
        ('P79', '入场 × 持有桥（D3 −K0 代理；A4b 形成权重退化）', '恢复 = 真实入场评分且推导段三分位单调（基准 CVR20 风险三分位）；本轮新测量不自动解封', 'PARKED'),
        ('P80', '预留槽位（E6r REVIEW 登记）', '—', 'RESERVED'), ('P81', '预留槽位（E6r REVIEW 登记）', '—', 'RESERVED'),
        ('P82', '预留槽位（E6r REVIEW 登记）', '—', 'RESERVED'), ('P83', '预留槽位（E6r REVIEW 登记）', '—', 'RESERVED')]
G2_EXACT = {  # 附录 G.2：E 依赖 → E6q 机器表行（S0-I 在 47 上按 exec_id 重读，写 exact_value；带不改）
    ('E01', 'review A.1 primary32'): ('statistics/account_summary_E6q.csv', 'E6Q-d78b9785b0594c1e', 'turnover_ann'),
    ('E02', 'review A.1 primary32'): ('statistics/account_summary_E6q.csv', 'E6Q-9f826422e6d4c39c', 'turnover_ann'),
    ('E03', 'review A.1 primary32'): ('statistics/account_summary_E6q.csv', 'E6Q-d78b9785b0594c1e', 'turnover_ann'),
}


def jl(n):
    with open(O.P('registration', 'spec', n), 'r', encoding='utf-8') as f:
        return json.load(f)


def payload_cell(k, v):
    if v is None:
        return ''
    if k == 'H_by_tertile':
        return json.dumps(v, sort_keys=True, separators=(',', ':'))
    if isinstance(v, bool):
        return 'true' if v else 'false'
    return str(v)


def e6q_replication_map():
    """附录 G.1：D 脚本常量 E6Q_REPLICATION（e6r lid → e6q lid）。"""
    txt = open(O.P('verify', 'decision', 'E6r_D_stage2.py'), encoding='utf-8').read()
    blk = txt[txt.index('E6Q_REPLICATION = {'):]
    blk = blk[:blk.index('\n}') + 2]
    return dict(re.findall(r"'(E6R-[0-9a-f]{16})': \('(E6Q-[0-9a-f]{16})'", blk))


def source_fingerprint(cd):
    det = dict(cache_reuse_manifest=O.sha_file(os.path.join(cd, 'cache_reuse_manifest.json')),
               cache_facts=O.sha_file(os.path.join(cd, 'cache_facts.json')),
               e6q_registry=O.sha_file(O.E6Q('registration', 'registry_E6q.csv')),
               e6q_engine=O.sha_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'e6q_engine.py')),
               cutoff=O.CUTOFF, fee=O.FEE_RATE, V0=O.V0, scap=O.STOCK_CAP, rcap=O.RESEARCH_CAP, idev=O.IND_DEV, start_state='CASH_V0')
    return hashlib.sha256(json.dumps(det, sort_keys=True).encode()).hexdigest()[:16], det


def main():
    t0 = time.time()
    for n, s in O.SPEC_SHA.items():
        got = O.sha_file(O.P('registration', 'spec', n))
        if got != s:
            raise RuntimeError('spec %s sha 不符：%s' % (n, got[:16]))
    reg = jl('registry.json')
    comps = jl('comparisons.json')
    compound = jl('compound.json')
    rrefs = jl('random_refs.json')
    frefs = jl('feedback_refs.json')
    primary = jl('primary.json')
    claims = jl('claims.json')
    cc = O.read_csv(O.P('registration', 'spec', 'cc_statement_carry.csv'))
    by = {}
    for r in reg:
        lid = 'E6R-' + O.digest(r['spec'])[:16]
        if lid != r['logical_id']:
            raise RuntimeError('logical_id 重算不符 %s' % r['logical_id'])
        by[lid] = r
    if len(by) != O.COUNTS['accounts']:
        raise RuntimeError('registry 行数 %d' % len(by))
    E = {lid: O.exec_id(lid, r['spec']['scenario']) for lid, r in by.items()}
    cd = O.cache_dir()
    fp, fp_det = source_fingerprint(cd)
    H = {lid: O.exec_hash(E[lid], fp) for lid in by}
    if len(set(H.values())) != len(H):
        raise RuntimeError('exec_hash 冲突')
    base = {lid: {} for lid in by}
    h20, h30 = {}, {}
    for c in comps:
        k = c['kind']
        if k in BASE_KIND_COL:
            base[c['left']][BASE_KIND_COL[k]] = c['right']
        elif k == 'H30_MINUS_H20_SAME_RULE':
            h20[c['left']] = c['right']
        elif k == 'H40_MINUS_H30_SAME_RULE':
            h30[c['left']] = c['right']
    for lid in by:
        miss = [col for col in BASE_KIND_COL.values() if col not in base[lid]]
        if miss:
            raise RuntimeError('%s 缺基础引用 %s' % (lid, miss))
    pp = {r['owner']: r for r in rrefs if r['policy_primary']}
    am = {r['owner']: r for r in rrefs if r['mechanism'] == 'AMOUNT_MATCH_V2'}
    e_owner = {c['owner'] for c in claims}
    e_ref = {c['reference'] for c in claims}
    p9 = list(primary['primary9'])
    # ---- 复现绑定
    rep = e6q_replication_map()
    if len(rep) != 58:
        raise RuntimeError('E6Q_REPLICATION 应为 58 项：%d' % len(rep))
    Q = O.read_csv(O.E6Q('registration', 'registry_E6q.csv'))
    qby = Q.set_index('logical_id')
    P6 = O.read_csv(os.path.join(O.E6P_DIR, 'registration', 'registry_E6p.csv'))
    e6p_trig = {'NONE': 'NONE', 'T1a': 'T1a', 'T1b_LEVEL': 'T1b_LEVEL', 'T8': 'T8_LIMIT_CLOSE'}

    def e6p_twin(sp):
        if sp['funding_H'] != 40 or sp['weight_scheme'] != 'FLAT' or sp['exit_op'] != 'NATIVE' or sp['trigger'] not in e6p_trig:
            return None
        m = P6[(P6.form == sp['form']) & (P6.memory == sp['memory']) & (P6.H == '40') & (P6.trigger == e6p_trig[sp['trigger']]) &
               (P6.execution_profile == sp['scenario']) & (P6.deploy.isin(['NONE', 'NATIVE', ''])) & (P6.cap.isin(['SOURCE', ''])) &
               (P6.renew.isin(['NONE', '0', '', 'OFF']))]
        return m.iloc[0] if len(m) == 1 else None
    rows = []
    for lid, r in by.items():
        sp = r['spec']
        b = base[lid]
        if sp['weight_scheme'] != 'FLAT':
            est, pref = 'ENTRY_OVERLAY', b['flat_same_exit_exec_id']
        elif sp['trigger'] != 'NONE':
            est, pref = 'EXIT_RULE', b['noexit_same_overlay_exec_id']
        else:
            est, pref = 'PARENT_NO_MECHANISM', ''
        cand = not (sp['weight_scheme'] in NOT_CANDIDATE or sp['scenario'] == O.IDEAL or est == 'PARENT_NO_MECHANISM')
        if lid in rep:
            q = qby.loc[rep[lid]]
            if q.execution_profile != sp['scenario']:
                raise RuntimeError('复现锚情景不符 %s' % lid)
            rsrc, rexe, rhash = 'E6Q', q.exec_id, q.exec_hash
        else:
            tw = e6p_twin(sp)
            if tw is not None:
                rsrc, rexe, rhash = 'E6P', tw.exec_id, tw.exec_hash
            else:
                rsrc, rexe, rhash = 'NEW_COORDINATE', '', ''
        row = dict(exec_id=E[lid], exec_hash=H[lid], logical_id=lid, groups='|'.join(sorted(r['groups'])), role='ACCOUNT')
        for k in O.PAYLOAD_KEYS:
            row[k] = payload_cell(k, sp[k])
        row.update(execution_profile=sp['scenario'], accounting_backend='ACCOUNT', support='FULLHIST', accounting_mode='FIXED_PATH_V1',
                   policy_version='E6R_V11', source_fingerprint=fp)
        for col in BASE_KIND_COL.values():
            row[col] = E[b[col]]
        row.update(h20_same_rule_exec_id=E.get(h20.get(lid), ''), h30_same_rule_exec_id=E.get(h30.get(lid), ''), policy_estimand=est,
                   policy_reference_exec_id=E[pref] if pref else '', candidate_eligible='true' if cand else 'false', replication_source=rsrc,
                   replication_exec_id=rexe, is_primary9=1 if lid in p9 else 0, is_e_owner=1 if lid in e_owner else 0, is_e_reference=1 if lid in e_ref else 0,
                   status='COMPUTED', replication_exec_hash=rhash)
        rows.append(row)
    R = pd.DataFrame(rows).sort_values('logical_id')
    est_n = R.policy_estimand.value_counts().to_dict()
    if est_n != {'ENTRY_OVERLAY': 231, 'EXIT_RULE': 70, 'PARENT_NO_MECHANISM': 49}:
        raise RuntimeError('estimand 计数 %s' % est_n)
    O.atomic_write_csv(O.P('registration', 'registry_E6r.csv'), R)
    # ---- comparisons / compound
    crow = []
    for c in comps:
        crow.append(dict(comparison_id='CMP-' + O.stable_key(c['left'], c['right'], c['kind'])[:16], kind=c['kind'], left_exec_id=E[c['left']],
                         right_exec_id=E[c['right']], left_logical_id=c['left'], right_logical_id=c['right'], metric=c['metric'],
                         scenario_relation=c['scenario_relation'], structural_identity='true' if c['structural_identity'] else 'false'))
    C = pd.DataFrame(crow)
    if len(C) != O.COUNTS['comparisons'] or C.comparison_id.nunique() != len(C):
        raise RuntimeError('comparisons 计数 / id 唯一不符')
    O.atomic_write_csv(O.P('registration', 'comparisons_E6r.csv'), C)
    corow = []
    for i, c in enumerate(compound, start=1):
        for role, t in zip(('AB', 'A', 'B', 'ZERO'), c['terms']):
            corow.append(dict(contrast_id='CPD-%02d' % i, kind=c['kind'], term_role=role, term_exec_id=E[t['id']], term_logical_id=t['id'], coefficient=t['coefficient']))
    O.atomic_write_csv(O.P('registration', 'compound_contrasts_E6r.csv'), pd.DataFrame(corow))
    # ---- random refs
    rr = []
    for c in rrefs:
        o = c['owner']
        rr.append(dict(ref_id='RND-' + O.stable_key(o, c['mechanism'])[:16], owner_logical_id=o, owner_exec_id=E[o], mechanism=c['mechanism'], layer=c['layer'],
                       policy_primary='true' if c['policy_primary'] else 'false', start_paths=c['paths'], max_paths=c['max_paths'],
                       mcse_target='' if c['mcse_target_ann_pp'] is None else c['mcse_target_ann_pp'], draw_kind=c['draw_kind'], seed_protocol=c['seed_protocol'],
                       owner_exec_hash=H[o]))
    RR = pd.DataFrame(rr)
    if len(RR) != O.COUNTS['random_refs'] or RR.ref_id.nunique() != len(RR):
        raise RuntimeError('random refs 计数 / id 不符')
    O.atomic_write_csv(O.P('registration', 'random_control_refs_E6r.csv'), RR)
    # ---- feedback
    fr = [dict(feedback_id=x['id'], owner_logical_id=x['owner'], owner_exec_id=E[x['owner']], A0_cny=x['A0'], kappa=x['kappa'], exponent=x['exponent'],
               mode='OWN_NAV_COST_CASH', owner_exec_hash=H[x['owner']]) for x in frefs['paths']]
    O.atomic_write_csv(O.P('registration', 'cost_feedback_refs_E6r.csv'), pd.DataFrame(fr))
    fc = [dict(left_feedback_id=c['left'], right_feedback_id=c['right'], kind=c['kind'], A0_cny=c['A0']) for c in frefs['comparisons']]
    O.atomic_write_csv(O.P('registration', 'feedback_comparisons_E6r.csv'), pd.DataFrame(fc))
    # ---- snapshots（computed_rows / status 在 diag 阶段回填）
    sn = [dict(snapshot_id='SNP-' + O.stable_key(x['owner'], x['kind'])[:16], owner_logical_id=x['owner'], owner_exec_id=E[x['owner']], kind=x['kind'],
               role=x['role'], policy_gate='false', computed_rows='', table='diagnostics/entry_target_snapshot_E6r.csv', status='NOT_RUN')
          for x in primary['snapshot_refs']]
    O.atomic_write_csv(O.P('registration', 'local_snapshot_refs_E6r.csv'), pd.DataFrame(sn))
    # ---- 账本
    gl = [dict(g_id=g, author=a, created_before=O.E_DECLARED_AT, dependency_file_sha=O.PROPOSAL_SHA256[:16], source_query='S0-C/' + g, exposed_window=w,
               derived_from='F1 §3.5', motivation=t, statement_verbatim=t, tested_estimand=t, comparison_ids='', unit='bp', state='PRESPECIFIED_DISCRIMINATING_TEST',
               result_query='QRY-' + g, result_row='', explanation_scope='', next_design_change='') for g, a, t, w in G_P]
    gl += [dict(g_id=g, author='PLAN', created_before='2026-10-24T00:20:01+00:00', dependency_file_sha=O.PLAN_SHA256[:16], source_query='S0-C/' + g,
                exposed_window='DERIV_2010_2018', derived_from='plan §3', motivation=t, statement_verbatim=t, tested_estimand=t, comparison_ids='', unit='bp',
                state='PRESPECIFIED_DISCRIMINATING_TEST', result_query='QRY-' + g, result_row='', explanation_scope='', next_design_change='') for g, t in GW]
    O.atomic_write_csv(O.P('registration', 'ledger_G_E6r.csv'), pd.DataFrame(gl))
    el = []
    for c in claims:
        el.append(dict(e_id=c['id'], author=c['author'], created_before=c['dependency_declared_at'], owner_exec_id=E[c['owner']], reference_exec_id=E[c['reference']],
                       statistic=c['statistic'], segment=c['segment'], unit=c['unit'], lower=repr(c['lower']), upper=repr(c['upper']),
                       upper_open_for_support='true' if c['upper_open_for_support'] else 'false',
                       dependency_keys=';'.join(str(d.get('keys', d.get('key'))) for d in c['dependencies']), exact_reference='', state='REGISTERED',
                       result_query='QRY-' + c['id'], result_row='', explanation_scope='', next_design_change=''))
    O.atomic_write_csv(O.P('registration', 'ledger_E_E6r.csv'), pd.DataFrame(el))
    ql = [dict(q_id=q, author='PLAN', created_before='2026-10-24T00:20:01+00:00', statement_verbatim=t, tested_estimand=e, comparison_ids='', result_query='QRY-' + q,
               result_row='', explanation_scope='', state='开放') for q, t, e in Q_CARDS]
    if [x['q_id'] for x in ql] != list(primary['q_cards']):
        raise RuntimeError('Q 卡与 primary.json 不符')
    O.atomic_write_csv(O.P('registration', 'ledger_Q_E6r.csv'), pd.DataFrame(ql))
    ccr = cc.copy()
    for col in ('plan_reading', 'estimand_note', 'comparable', 'claim_status', 'sub_claims'):
        ccr[col] = ''
    O.atomic_write_csv(O.P('registration', 'cc_statement_carry.csv'), ccr)
    # ---- 授权 / 暴露 / park / 政策映射
    at = O.AUTHORIZED_AT
    perm = [dict(key=k, value=(json.dumps(v) if not isinstance(v, str) else v), authorized_by=O.AUTHORIZED_BY, authorized_at=at) for k, v in O.AUTHORIZATIONS.items()]
    perm += [dict(key='protocol', value='v1.6', authorized_by=O.AUTHORIZED_BY, authorized_at=at), dict(key='mode', value='B', authorized_by=O.AUTHORIZED_BY, authorized_at=at)]
    O.atomic_write_csv(O.P('registration', 'permissions_E6r.csv'), pd.DataFrame(perm))
    today = time.strftime('%Y-%m-%d')
    O.atomic_write_csv(O.P('registration', 'exposure_E6r.csv'),
                       pd.DataFrame([dict(logical_id=lid, first_seen_at=today, selection_history='REGISTERED_A1') for lid in sorted(by)]))
    O.atomic_write_csv(O.P('registration', 'park_E6r.csv'), pd.DataFrame([dict(park_id=p, domain=d, condition=c, status=s) for p, d, c, s in PARK]))
    pm = []
    for _, r in R.iterrows():
        lid = r.logical_id
        sp = by[lid]['spec']
        c4p = pp.get(lid) if (sp['scenario'] == O.FEAS and r.policy_estimand != 'PARENT_NO_MECHANISM') else None
        c4a = am.get(lid) if (sp['scenario'] == O.FEAS and sp['trigger'] != 'NONE') else None
        pm.append(dict(exec_id=r.exec_id, policy_estimand=r.policy_estimand, reference_exec_id=r.policy_reference_exec_id,
                       c4_ref_id=('RND-' + O.stable_key(lid, c4p['mechanism'])[:16]) if c4p else '', c4_mechanism=c4p['mechanism'] if c4p else '',
                       candidate_eligible=r.candidate_eligible, audit_reference_exec_id=r.noexit_same_overlay_exec_id if sp['trigger'] != 'NONE' else '',
                       audit_c4_ref_id=('RND-' + O.stable_key(lid, 'AMOUNT_MATCH_V2')[:16]) if c4a else '', c6_basis='A1_FREEZE_REGISTRY_AND_POLICY_MAPPING',
                       note='UNIFORM_CAP15 无入场随机 → c4 NA' if sp['weight_scheme'] == 'UNIFORM_CAP15' else ''))
    O.atomic_write_csv(O.P('statistics', 'policy_mapping_E6r.csv'), pd.DataFrame(pm))
    facts = dict(accounts=len(R), feasible=int((R.scenario == O.FEAS).sum()), ideal=int((R.scenario == O.IDEAL).sum()), estimand=est_n,
                 replication=R.replication_source.value_counts().to_dict(), comparisons=len(C), compound=len(compound), random_refs=len(RR),
                 feedback_paths=len(fr), feedback_comparisons=len(fc), snapshots=len(sn), source_fingerprint=fp, source_fingerprint_inputs=fp_det,
                 wall_s=round(time.time() - t0, 1))
    O.atomic_write_json(O.P('registration', 'registry_facts_E6r.json'), facts)
    outs = [O.P('registration', n) for n in ('registry_E6r.csv', 'comparisons_E6r.csv', 'compound_contrasts_E6r.csv', 'random_control_refs_E6r.csv',
                                             'cost_feedback_refs_E6r.csv', 'feedback_comparisons_E6r.csv', 'local_snapshot_refs_E6r.csv', 'ledger_G_E6r.csv',
                                             'ledger_E_E6r.csv', 'ledger_Q_E6r.csv', 'cc_statement_carry.csv', 'permissions_E6r.csv', 'exposure_E6r.csv',
                                             'park_E6r.csv', 'registry_facts_E6r.json')] + [O.P('statistics', 'policy_mapping_E6r.csv')]
    O.write_receipt('E6r_registry', outs, code=[__file__, O.__file__], **{k: v for k, v in facts.items() if k != 'source_fingerprint_inputs'})
    print(json.dumps({k: v for k, v in facts.items() if k != 'source_fingerprint_inputs'}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
