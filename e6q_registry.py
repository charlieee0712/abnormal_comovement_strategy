# -*- coding: utf-8 -*-
"""E6q A1 登记编译（brief §3；附录 B.1–B.6 / B.24）：plan 附录 C 七个 json（registration/spec/，S0-J 原样复制，计数与身份的事实来源）→
registry（201）/ comparisons（1,359）/ compound（6 × 4）/ random_control_refs（568）/ cost_feedback_refs（80）+ feedback_comparisons（580）/
local_snapshot_refs（20）/ exposure（201）。
- logical_id 逐行由 25 字段 payload 重算（e6q_core.logical_id = plan 附录 C canonical / digest）并与 json id 比对；exec_id 六段；
  exec_hash = sha256(exec_id + trigger_formula_hash + source_ref_contract + source_hash)[:16]。
- trigger_formula_hash = 触发定义句 + 触发面板文件 sha 的 digest；source_ref_contract = 形成名单合同名；source_hash = (form, memory) 四段源形成名单数组 sha。
  均由缓存实物算出，换面板 / 换名单即换 hash。
- 引用八列（B.1）：父 = 同 form / memory / H / arm / scenario、trigger = NONE（NONE 行空）；同触发 NATIVE（非 NATIVE 臂且 trigger ≠ NONE）；H5 本地父（FEASIBLE；
  同 form / memory 的 H5 NONE NATIVE，自身为空）；H5 全局父 / 前沿 / LEVEL H20 参照 = primary.json（自身为空）；H30 → 同规则 H20；同触发 CASH（trigger ∈ {T1a, LEVEL}、
  FEASIBLE、H > 5、非 CASH 臂）；E6p 复现（NATIVE、FEASIBLE、trigger ∈ {NONE, T1a, LEVEL, T8} → E6p 同坐标 exec_id，T8 ↔ T8_LIMIT_CLOSE）。
用法：python3 e6q_registry.py"""
import os
import json
import time
import hashlib

import numpy as np
import pandas as pd

import e6q_core as O

GROUP_N = {'MAIN': 54, 'UNION': 4, 'ANCHOR_OR_H5_BRIDGE': 5, 'HALF_INTERACTION': 6, 'HALF_STATE_BRIDGE': 6, 'ROBUSTNESS': 84, 'ROBUSTNESS_H5': 21, 'IDEAL': 21}
SCEN_N = {'FEASIBLE_DAILY': 180, 'IDEALIZED_SOURCE_FILL': 21}
KIND_N = {'LEVEL_H20_REFERENCE': 200, 'H5_GLOBAL_PARENT': 200, 'FRONTIER_T1A_H20': 200, 'H5_LOCAL_PARENT': 172, 'SAME_H_PARENT': 136, 'SAME_TRIGGER_H5': 104,
          'SAME_TRIGGER_NATIVE': 94, 'CASH_SAME_TRIGGER': 82, 'ZERO_INTERVENTION': 47, 'RECYCLE_HALF_SAME_TRIGGER': 40, 'H30_MINUS_H20_SAME_RULE': 35,
          'IDEAL_MINUS_FEASIBLE': 21, 'A_REF_DESIGN_PAIR': 18, 'HALF_REARM_VS_DUE': 4, 'UNION_VS_T8': 3, 'UNION_VS_T1A': 3}
COMPOUND_N = {'EXIT_X_RECYCLE_HALF': 4, 'UNION_NONADDITIVITY': 2}
MECH_N = {'AMOUNT_MATCH_V2': 105, 'COUNT_ISK': 105, 'AMOUNT_ISK_V2': 105, 'BERNOULLI_FIRSTHIT': 105, 'LEVEL_WORST_1D': 50,
          'RANDOM_TARGET_WITHIN_ARM': 49, 'RANDOM_TARGET_SOURCE_DOMAIN': 49}
TRIG_DEF = {
    'NONE': 'no exit trigger (parent / zero-intervention endpoint)',
    'T1a': 'CVR_20d OLS residual on log mcap, pool0 top quintile; held domain uses same-day coefficients and cut (E6o T1a panel, production cut, 0 new parameters)',
    'T1b_LEVEL': 'daily CVR position in clean empirical distribution >= .90; persistent state (E6o T1b_LEVEL panel); missing measurement day UNKNOWN',
    'T8': 'raw close within half tick of raw effective limit-up price; no-limit day -> 0; unknown limit -> UNKNOWN (E6p T8_LIMIT_CLOSE panel)',
    'UNION_T1a_T8': 'three-valued OR of T1a and T8 (any known true -> true; both known false -> false; else UNKNOWN); intersection is one intent per day',
}
TRIG_FILE = {'NONE': 'NONE', 'T1a': 'T1a', 'T1b_LEVEL': 'T1b_LEVEL', 'T8': 'T8_LIMIT_CLOSE', 'UNION_T1a_T8': 'UNION_T1a_T8'}
TRIG_E6P = {'NONE': 'NONE', 'T1a': 'T1a', 'T1b_LEVEL': 'T1b_LEVEL', 'T8': 'T8_LIMIT_CLOSE'}
REG_COLS = ['exec_id', 'exec_hash', 'logical_id', 'group', 'role', 'form', 'Qalpha', 'memory', 'H', 'arm', 'trigger', 'A_ref', 'scenario', 'alpha', 'initial_state', 'cutoff',
            'cap_profile', 'funding_lag', 'maturity', 'reentry', 'execution', 'support', 'p_star', 'fraction', 'queue_days', 'exit_fraction', 'reinvest_eta', 'cap_kind',
            'firsthit_clock', 'cash_contract', 'version', 'execution_profile', 'accounting_backend', 'start_state', 'cost_profile', 'policy_version', 'trigger_formula_hash',
            'source_ref_contract', 'source_hash', 'parent_same_arm_exec_id', 'native_same_trigger_exec_id', 'parent_h5_local_exec_id', 'parent_h5_global_exec_id',
            'frontier_exec_id', 'level_h20_ref_exec_id', 'h20_same_rule_exec_id', 'cash_same_trigger_exec_id', 'e6p_replication_exec_id', 'is_primary32', 'is_e_object', 'status']
REF_COLS = ('parent_same_arm_exec_id', 'native_same_trigger_exec_id', 'parent_h5_local_exec_id', 'parent_h5_global_exec_id', 'frontier_exec_id',
            'level_h20_ref_exec_id', 'h20_same_rule_exec_id', 'cash_same_trigger_exec_id')
REF_N = {'parent_same_arm_exec_id': 136, 'native_same_trigger_exec_id': 94, 'parent_h5_local_exec_id': 172, 'parent_h5_global_exec_id': 200,
         'frontier_exec_id': 200, 'level_h20_ref_exec_id': 200, 'h20_same_rule_exec_id': 35, 'cash_same_trigger_exec_id': 82}


def load_spec(name):
    with open(O.P('registration', 'spec', name + '.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def sval(v):
    return '' if v is None else str(v)


def formation_sha(cd, form, mem):
    h = hashlib.sha256()
    for s in O.SEGS:
        z = np.load(os.path.join(cd, 'source', '%s.npz' % s), allow_pickle=False)
        for k in ('fm_t', 'fm_c', 'fm_w'):
            h.update(np.ascontiguousarray(z['%s|%s|%s' % (k, form, mem)]).tobytes())
    return h.hexdigest()


def build(cd=None):
    t0 = time.time()
    cd = cd or O.cache_dir()
    for nm, sha in O.JSON_SHA.items():
        p = O.P('registration', 'spec', nm)
        with open(p, 'rb') as f:
            if hashlib.sha256(f.read().replace(b'\r\n', b'\n')).hexdigest() != sha:
                raise RuntimeError('spec 指纹不符：%s' % nm)
    reg = load_spec('registry')
    comps = load_spec('comparisons')
    comp = load_spec('compound')
    rrefs = load_spec('random_refs')
    frefs = load_spec('feedback_refs')
    prim = load_spec('primary')
    claims = load_spec('claims')
    bad = []
    for s in reg:
        if O.logical_id(s) != s['id']:
            bad.append('logical_id 重算不符 %s' % s['id'])
        if len(s['groups']) != 1:
            bad.append('组不唯一 %s' % s['id'])
    if bad:
        raise RuntimeError('; '.join(bad[:5]))
    by = {s['id']: s for s in reg}
    p32 = set(prim['primary'])
    eobj = {e['object_id'] for e in claims['e']}
    trig_sha = {t: O.sha_file(os.path.join(cd, 'triggers', TRIG_FILE[t] + '.npy')) for t in TRIG_DEF}
    tfh = {t: O.digest(dict(trigger=t, definition=TRIG_DEF[t], panel_sha256=trig_sha[t]))[:16] for t in TRIG_DEF}
    fsha = {}
    for s in reg:
        k = (s['form'], s['memory'])
        if k not in fsha:
            fsha[k] = formation_sha(cd, *k)
    E6 = pd.read_csv(O.E6P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
    E6 = E6[(E6.role == 'ACCOUNT') & (E6.cap == 'SOURCE') & (E6.renew == '0')]

    def find(**kw):
        hits = [s['id'] for s in reg if all(s.get(k) == v for k, v in kw.items())]
        if len(hits) > 1:
            raise RuntimeError('引用不唯一 %s' % kw)
        return hits[0] if hits else ''

    def eid(lid):
        return O.exec_id(lid, by[lid]['scenario']) if lid else ''
    main_h5 = prim['h5']
    frontier = prim['frontier']
    level = prim['level_h20']
    if frontier != O.FRONTIER_LID:
        raise RuntimeError('前沿锚 %s ≠ 授权值 %s' % (frontier, O.FRONTIER_LID))
    rows = []
    for s in reg:
        lid = s['id']
        sc = s['scenario']
        base = dict(form=s['form'], memory=s['memory'], H=s['H'], scenario=sc)
        parent = find(**base, arm=s['arm'], trigger='NONE') if s['trigger'] != 'NONE' else ''
        native = find(**base, arm='NATIVE', trigger=s['trigger']) if (s['trigger'] != 'NONE' and s['arm'] != 'NATIVE') else ''
        h5l = find(form=s['form'], memory=s['memory'], H=5, trigger='NONE', arm='NATIVE', scenario='FEASIBLE_DAILY') if sc == 'FEASIBLE_DAILY' else ''
        if h5l == lid:
            h5l = ''
        h20 = find(form=s['form'], memory=s['memory'], H=20, trigger=s['trigger'], arm=s['arm'], scenario=sc) if s['H'] == 30 else ''
        cash = ''
        if s['trigger'] in ('T1a', 'T1b_LEVEL') and sc == 'FEASIBLE_DAILY' and s['H'] > 5 and s['arm'] != 'CASH_REMAIN':
            cash = find(**base, arm='CASH_REMAIN', trigger=s['trigger'])
        e6p = ''
        if s['arm'] == 'NATIVE' and sc == 'FEASIBLE_DAILY' and s['trigger'] in TRIG_E6P:
            m = E6[(E6.form == s['form']) & (E6.memory == s['memory']) & (E6.H == str(s['H'])) & (E6.deploy == 'NATIVE') & (E6.trigger == TRIG_E6P[s['trigger']])
                   & (E6.execution_profile == 'FEASIBLE_DAILY')]
            if len(m) != 1:
                raise RuntimeError('E6p 复现坐标不唯一 / 缺：%s' % lid)
            e6p = m.iloc[0].exec_id
        e = eid(lid)
        src_c = 'E6O_FORMATION_V1:%s:%s:a0.25' % (s['form'], s['memory'])
        sh = fsha[(s['form'], s['memory'])][:16]
        th = tfh[s['trigger']]
        r = dict(exec_id=e, exec_hash=O.exec_hash(e, th, src_c, sh), logical_id=lid, group=s['groups'][0], role='ACCOUNT', Qalpha='a0.25',
                 execution_profile=sc, accounting_backend='ACCOUNT', start_state=O.START_STATE, cost_profile=O.COST_PROFILE, policy_version=O.POLICY_VERSION,
                 trigger_formula_hash=th, source_ref_contract=src_c, source_hash=sh, parent_same_arm_exec_id=eid(parent), native_same_trigger_exec_id=eid(native),
                 parent_h5_local_exec_id=eid(h5l), parent_h5_global_exec_id=eid(main_h5) if lid != main_h5 else '', frontier_exec_id=eid(frontier) if lid != frontier else '',
                 level_h20_ref_exec_id=eid(level) if lid != level else '', h20_same_rule_exec_id=eid(h20), cash_same_trigger_exec_id=eid(cash),
                 e6p_replication_exec_id=e6p, is_primary32=1 if lid in p32 else 0, is_e_object=1 if lid in eobj else 0, status='COMPUTED')
        for k in O.PAYLOAD_KEYS:
            r[k] = sval(s.get(k))
        rows.append(r)
    R = pd.DataFrame(rows, columns=REG_COLS)
    # ---- 自检（S04 / S05 同式）
    if len(R) != 201 or R.logical_id.nunique() != 201:
        bad.append('行数 %d' % len(R))
    for g, n in GROUP_N.items():
        if int((R.group == g).sum()) != n:
            bad.append('组 %s %d≠%d' % (g, int((R.group == g).sum()), n))
    for sc, n in SCEN_N.items():
        if int((R.scenario == sc).sum()) != n:
            bad.append('情景 %s' % sc)
    for c, n in REF_N.items():
        if int((R[c] != '').sum()) != n:
            bad.append('引用 %s %d≠%d' % (c, int((R[c] != '').sum()), n))
    if set(R.logical_id[R.is_primary32 == 1]) != p32 or len(p32) != 32:
        bad.append('primary32')
    if set(R.logical_id[R.is_e_object == 1]) != eobj:
        bad.append('E 对象')
    ids = set(R.exec_id)
    for c in REF_COLS:
        if not set(R[c][R[c] != '']) <= ids:
            bad.append('引用未闭合 %s' % c)
    nrep = int((R.e6p_replication_exec_id != '').sum())
    if R.exec_hash.duplicated().any() or R.exec_id.duplicated().any():
        bad.append('exec_hash / exec_id 重复')
    if bad:
        raise RuntimeError('registry 自检失败：' + '; '.join(bad[:8]))
    # ---- comparisons（1,359）
    crow = []
    for c in comps:
        crow.append(dict(comparison_id=c['id'], kind=c['kind'], left_exec_id=eid(c['left']), right_exec_id=eid(c['right']), left_logical_id=c['left'],
                         right_logical_id=c['right'], metric=c['metric'], same_scenario='true' if c['same_scenario'] else 'false',
                         interpretation=c['interpretation'], note=''))
    C = pd.DataFrame(crow)
    if len(C) != 1359 or C.kind.value_counts().to_dict() != KIND_N:
        raise RuntimeError('comparisons 计数 %d %s' % (len(C), C.kind.value_counts().to_dict()))
    # ---- compound（6 × 4，长格式）
    prow = []
    for c in comp:
        if abs(sum(t[1] for t in c['terms'])) != 0:
            raise RuntimeError('复合系数和非零')
        for lid, coef in c['terms']:
            prow.append(dict(contrast_id=c['id'], kind=c['kind'], term_exec_id=eid(lid), term_logical_id=lid, coefficient=int(coef)))
    PC = pd.DataFrame(prow)
    if PC.drop_duplicates('contrast_id').kind.value_counts().to_dict() != COMPOUND_N or len(PC) != 24:
        raise RuntimeError('compound 计数')
    # ---- random refs（568）
    RR = pd.DataFrame([dict(owner_logical_id=x['owner'], owner_exec_id=eid(x['owner']), mechanism=x['mechanism'], start_paths=int(x['start_paths']),
                            max_paths=int(x['max_paths']), mcse_target=sval(x.get('mcse_target')), budget_unit=sval(x.get('budget_unit')), state=sval(x.get('state')))
                       for x in rrefs])
    if len(RR) != 568 or RR.mechanism.value_counts().to_dict() != MECH_N:
        raise RuntimeError('random refs %d' % len(RR))
    # ---- feedback（80 + 580）
    FB = pd.DataFrame([dict(feedback_id=x['id'], owner_logical_id=x['owner'], owner_exec_id=eid(x['owner']), A0_cny=int(x['A0']), kappa=x['kappa'],
                            exponent=x['delta'], mode=x['mode'], role=x['role'], parent_feedback_id=x['parent_feedback_id'],
                            same_rule_A_ref=sval(x.get('same_rule_A_ref'))) for x in frefs])
    FP = pd.DataFrame([dict(feedback_id=x['id'], kind=c['kind'], right_feedback_id=c['right_feedback_id'], right_owner_logical_id=c['right_owner'])
                       for x in frefs for c in x['comparisons']])
    if len(FB) != 80 or len(FP) != 580:
        raise RuntimeError('feedback %d / %d' % (len(FB), len(FP)))
    fids = set(FB.feedback_id)
    if not (set(FB.parent_feedback_id) <= fids and set(FP.right_feedback_id) <= fids):
        raise RuntimeError('feedback 父 / 配对未闭合')
    # ---- 本地快照（20）
    LS = pd.DataFrame([dict(owner_logical_id=x['owner'], owner_exec_id=eid(x['owner']), reference_logical_id=x['reference'], reference_exec_id=eid(x['reference']),
                            kind=x['kind'], unit=x['unit']) for x in prim['local_snapshot_refs']])
    if len(LS) != 20:
        raise RuntimeError('local snapshot refs %d' % len(LS))
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    EX = pd.DataFrame([dict(logical_id=s['id'], first_seen_at=now, selection_history='REGISTERED_AT_A1_FROM_PLAN_APPENDIX_C_JSON;NO_OUTCOME_SELECTION') for s in reg])
    out = {}
    for name, df in (('registry_E6q.csv', R), ('comparisons_E6q.csv', C), ('compound_contrasts_E6q.csv', PC), ('random_control_refs_E6q.csv', RR),
                     ('cost_feedback_refs_E6q.csv', FB), ('feedback_comparisons_E6q.csv', FP), ('local_snapshot_refs_E6q.csv', LS), ('exposure_E6q.csv', EX)):
        p = O.P('registration', name)
        O.atomic_write_csv(p, df)
        out[name] = p
    facts = dict(registry_rows=len(R), groups=R.group.value_counts().to_dict(), scenarios=R.scenario.value_counts().to_dict(),
                 ref_counts={c: int((R[c] != '').sum()) for c in REF_COLS}, e6p_replication_rows=nrep, comparisons=len(C), compound_rows=len(PC),
                 random_refs=len(RR), feedback_refs=len(FB), feedback_pairs=len(FP), local_snapshot_refs=len(LS), exposure=len(EX),
                 trigger_formula_hash=tfh, trigger_panel_sha256=trig_sha, primary32=sorted(p32), e_objects=sorted(eobj), wall_s=round(time.time() - t0, 1))
    O.atomic_write_json(O.P('registration', 'registry_facts_E6q.json'), facts)
    O.write_receipt('E6q_registry', list(out.values()), code=[__file__, O.__file__],
                    **{k: v for k, v in facts.items() if k not in ('trigger_formula_hash', 'trigger_panel_sha256', 'primary32', 'e_objects')})
    return R, facts


if __name__ == '__main__':
    R, f = build()
    print(json.dumps({k: v for k, v in f.items() if k not in ('trigger_formula_hash', 'trigger_panel_sha256', 'primary32', 'e_objects')}, ensure_ascii=False), flush=True)
