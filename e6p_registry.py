# -*- coding: utf-8 -*-
"""E6p A1 登记编译（brief §3；附录 B.1 / B.2 / B.21）：plan 附录 C 七个 json（registration/spec/，S0-13 原样复制，计数与身份的事实来源）→
registry / comparisons / compound / random_control_refs / cost_feedback_refs / recycle_diagnostic_refs / exposure。
- logical_id 逐行由 Spec 11 字段重算（e6p_core.spec_logical_id）并与 json id 比对；exec_id 六段；exec_hash = sha256(exec_id + trigger_formula_hash + source_ref_contract + source_hash)[:16]。
- trigger_formula_hash = 触发定义句 + 触发面板文件 sha 的 digest；source_ref_contract = 形成名单合同名；source_hash = (form, memory) 四段源形成名单数组 sha
  （RENEW5 另含 NONE 记忆自然名单 sha）。均由缓存实物算出，换面板 / 换名单即换 hash。
- 父列（B.1）：ACCOUNT 且 trigger ≠ NONE → 同 form / memory / H / deploy / cap / renew、trigger = NONE 的行；renew-only（trigger = NONE、renew = 5）→ 同坐标 renew = 0 的父
  （= plan 附录 C 的 VS_SAME_H_PARENT 右侧）；H5 同部署父 / H5 NATIVE 父 / P_SOURCE 父沿 D 脚本夹具同式。
用法：python3 e6p_registry.py"""
import os
import json
import time
import hashlib

import numpy as np
import pandas as pd

import e6p_core as O

PROFILES = ('FEASIBLE_DAILY', 'IDEALIZED_SOURCE_FILL')
PSHORT = {'FEASIBLE_DAILY': 'FD', 'IDEALIZED_SOURCE_FILL': 'IS'}
BLOCK_N = {'PARENT': 144, 'MAIN': 324, 'TRANSFER': 180, 'RENEW5': 36, 'CAP_BRIDGE': 36, 'CASH_BRIDGE': 9, 'RECYCLE_EXTENSION': 27, 'MIRROR': 308}
KIND_N = {'VS_SAME_H_PARENT': 588, 'VS_H5_SAME_DEPLOY': 588, 'VS_H5_CURRENT_NATIVE': 588, 'DEPLOY_OPERATOR_CHANGE': 450, 'HORIZON_WITHIN_TRIGGER': 448,
          'OWNER_VS_EXPOSURE_FOLLOWER': 308, 'EXPOSURE_FOLLOWER_VS_FIXED': 308, 'UNION_COMPONENT': 108, 'LEVEL_VS_EDGE': 54, 'RENEW_VS_NO_RENEW': 36,
          'CAP_DEFINITION_BRIDGE': 36, 'RECYCLE_VS_NATIVE': 27, 'RECYCLE_VS_CASH': 27, 'EXIT_WITHIN_RENEW': 24, 'CASH_VS_NATIVE': 9,
          'NET_AWARE_VS_STANDALONE_COST': 9}
COMPOUND_N = {'H_X_EXIT': 448, 'DEPLOY_X_EXIT': 348, 'UNION_NONADDITIVITY': 54, 'RENEW_X_EXIT': 24}
TRIG_DEF = {
    'NONE': 'no exit trigger (parent / control)',
    'T1a': 'CVR_20d OLS residual on log mcap, pool0 top quintile; held domain uses same-day coefficients and cut (E6o T1a panel, production cut, 0 new parameters)',
    'T1b_LEVEL': 'daily CVR position in clean empirical distribution >= .90; persistent state (E6o T1b_LEVEL panel)',
    'T1b_EDGE': 'today >= .90 and yesterday known < .90; yesterday unknown -> UNKNOWN (E6o T1b_EDGE panel; hit cells identical to SOURCE_T1b)',
    'T3b15': 'volume ratio >= 1.5 vs 20-day mean baseline and adjusted return > 0 (E6o T3b15 panel)',
    'UNION': 'three-valued OR of T1a and T3b15 (any true -> true; both false -> false; else UNKNOWN)',
    'T8_LIMIT_CLOSE': 'raw close within half tick of raw effective limit-up price; no-limit day -> 0; unknown limit -> UNKNOWN',
}
TRIG_FILE = {'NONE': 'NONE', 'T1a': 'T1a', 'T1b_LEVEL': 'T1b_LEVEL', 'T1b_EDGE': 'T1b_EDGE', 'T3b15': 'T3b15', 'UNION': 'UNION', 'T8_LIMIT_CLOSE': 'T8_LIMIT_CLOSE'}
REG_COLS = ['exec_id', 'exec_hash', 'logical_id', 'series', 'block', 'role', 'form', 'Qalpha', 'memory', 'H', 'deploy', 'cap', 'trigger', 'renew',
            'owner_logical_id', 'mirror_H', 'version', 'execution_profile', 'accounting_backend', 'support', 'start_state', 'cost_profile', 'policy_version',
            'trigger_formula_hash', 'source_ref_contract', 'source_hash', 'parent_same_h_exec_id', 'parent_h5_same_deploy_exec_id', 'parent_h5_native_exec_id',
            'source_parent_exec_id', 'is_primary72', 'is_main_object', 'status']


def spec_dir():
    return O.P('registration', 'spec')


def load_spec(name):
    with open(os.path.join(spec_dir(), name + '.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def formation_sha(cd, form, mem):
    h = hashlib.sha256()
    for s in O.SEGS:
        z = np.load(os.path.join(cd, 'source', '%s.npz' % s), allow_pickle=False)
        for k in ('fm_t', 'fm_c', 'fm_w'):
            h.update(np.ascontiguousarray(z['%s|%s|%s' % (k, form, mem)]).tobytes())
    return h.hexdigest()


def main_object_ids(reg):
    out = set()
    for s in reg:
        if (s['form'] == O.MAIN_FORM and s['memory'] == 'HG10' and int(s['H']) == 20 and s['deploy'] == 'NATIVE' and s['trigger'] in ('T1a', 'T1b_LEVEL')
                and int(s['renew']) == 0 and s['cap'] == 'SOURCE' and s['role'] == 'ACCOUNT'):
            out.add(s['id'])
    return out


def build(cd=None):
    t0 = time.time()
    cd = cd or O.cache_dir()
    reg = load_spec('registry')
    p72 = set(load_spec('primary72'))
    comps = load_spec('comparisons')
    comp = load_spec('compound_contrasts')
    rcr = load_spec('random_control_refs')
    aux = load_spec('auxiliary_refs')
    rdr = load_spec('recycle_diagnostic_refs')
    bad = []
    for s in reg:
        if O.spec_logical_id(s) != s['id']:
            bad.append('logical_id 重算不符 %s' % s['id'])
    if bad:
        raise RuntimeError('; '.join(bad[:5]))
    by = {s['id']: s for s in reg}
    trig_sha = {t: O.sha_file(os.path.join(cd, 'triggers', TRIG_FILE[t] + '.npy')) for t in TRIG_DEF}
    tfh = {t: O.digest(dict(trigger=t, definition=TRIG_DEF[t], panel_sha256=trig_sha[t]))[:16] for t in TRIG_DEF}
    fsha = {}
    for form in O.FORMS:
        for mem in O.MEMS:
            try:
                fsha[(form, mem)] = formation_sha(cd, form, mem)
            except KeyError:
                pass
    main_ids = main_object_ids(reg)

    def find(form, memory, H, deploy, cap, renew, trigger='NONE'):
        for s in reg:
            if (s['role'] == 'ACCOUNT' and s['form'] == form and s['memory'] == memory and int(s['H']) == int(H) and s['deploy'] == deploy
                    and s['cap'] == cap and int(s['renew']) == int(renew) and s['trigger'] == trigger):
                return s['id']
        return ''

    tail = '|'.join([O.SUPPORT, 'CASH_V0', O.COST_PROFILE, O.POLICY_VERSION])

    def eid(lid, prof):
        return '%s|%s|%s' % (lid, prof, tail)
    srcset = sorted({(s['form'], s['memory'], int(s['H'])) for s in reg if s['role'] == 'ACCOUNT' and s['block'] == 'PARENT' and s['deploy'] == 'NATIVE'})
    rows = []
    for prof in PROFILES:
        for s in reg:
            lid = s['id']
            same_h = h5_dep = h5_nat = ''
            if s['role'] == 'ACCOUNT' and s['trigger'] != 'NONE':
                x = find(s['form'], s['memory'], s['H'], s['deploy'], s['cap'], s['renew'])
                same_h = eid(x, prof) if x else ''
            elif s['role'] == 'ACCOUNT' and int(s['renew']) != 0:
                x = find(s['form'], s['memory'], s['H'], s['deploy'], s['cap'], 0)
                same_h = eid(x, prof) if x else ''
            if s['role'] == 'ACCOUNT':
                x = find(s['form'], s['memory'], 5, s['deploy'], s['cap'], 0)
                h5_dep = eid(x, prof) if x else ''
                y = find(s['form'], s['memory'], 5, 'NATIVE', 'SOURCE', 0)
                h5_nat = eid(y, prof) if y else ''
            srcp = ''
            if s['role'] == 'ACCOUNT' and s['deploy'] == 'NATIVE' and (s['form'], s['memory'], int(s['H'])) in srcset:
                srcp = 'E6P-SRC-%s-%s-H%d|SOURCE|%s' % (s['form'], s['memory'], int(s['H']), tail)
            series = 'M_ACCOUNT' if s['role'] == 'MIRROR' else ('P_ACCOUNT' if s['block'] == 'PARENT' else 'C_ACCOUNT')
            src_c = 'E6O_FORMATION_V1:%s:%s:a0.25' % (s['form'], s['memory'])
            sh = fsha[(s['form'], s['memory'])]
            if int(s['renew']) != 0:
                src_c += ':RENEW_NATURAL_NONE_MEMORY'
                sh = O.digest(dict(main=sh, natural=fsha[(s['form'], 'NONE')]))
            if s['role'] == 'MIRROR':
                src_c += ':MIRROR_OWNER_CLOSE_EXPOSURE_LAG1'
            e = eid(lid, prof)
            th = tfh[s['trigger']]
            rows.append(dict(exec_id=e, exec_hash=O.exec_hash(e, th, src_c, sh[:16]), logical_id=lid, series=series, block=s['block'], role=s['role'],
                             form=s['form'], Qalpha='a0.25', memory=s['memory'], H=int(s['H']), deploy=s['deploy'], cap=s['cap'], trigger=s['trigger'],
                             renew=int(s['renew']), owner_logical_id=s['owner'], mirror_H=int(s['mirror_H']), version=s['version'], execution_profile=prof,
                             accounting_backend='ACCOUNT', support=O.SUPPORT, start_state='CASH_V0', cost_profile=O.COST_PROFILE, policy_version=O.POLICY_VERSION,
                             trigger_formula_hash=th, source_ref_contract=src_c, source_hash=sh[:16], parent_same_h_exec_id=same_h, parent_h5_same_deploy_exec_id=h5_dep,
                             parent_h5_native_exec_id=h5_nat, source_parent_exec_id=srcp, is_primary72=1 if lid in p72 else 0, is_main_object=1 if lid in main_ids else 0,
                             status='COMPUTED'))
    for (form, mem, H) in srcset:
        lid = 'E6P-SRC-%s-%s-H%d' % (form, mem, H)
        e = '%s|SOURCE|%s' % (lid, tail)
        src_c = 'E6I_SOURCE_ENGINE_FIXED_ROLLING:%s:%s:a0.25' % (form, mem)
        sh = fsha[(form, mem)][:16]
        rows.append(dict(exec_id=e, exec_hash=O.exec_hash(e, 'na', src_c, sh), logical_id=lid, series='P_SOURCE', block='SOURCE', role='SOURCE', form=form,
                         Qalpha='a0.25', memory=mem, H=H, deploy='SOURCE_ROLLING', cap='SOURCE', trigger='NONE', renew=0, owner_logical_id='', mirror_H=0,
                         version=O.VERSION, execution_profile='SOURCE', accounting_backend='SOURCE', support=O.SUPPORT, start_state='CASH_V0',
                         cost_profile=O.COST_PROFILE, policy_version=O.POLICY_VERSION, trigger_formula_hash='na', source_ref_contract=src_c, source_hash=sh,
                         parent_same_h_exec_id='', parent_h5_same_deploy_exec_id='', parent_h5_native_exec_id='', source_parent_exec_id='', is_primary72=0,
                         is_main_object=0, status='COMPUTED'))
    R = pd.DataFrame(rows, columns=REG_COLS)
    # ---- 自检（S04 / S05 同式）
    for prof in PROFILES:
        pr = R[R.execution_profile == prof]
        if len(pr) != 1064:
            bad.append('%s 行数 %d' % (prof, len(pr)))
        for b, n in BLOCK_N.items():
            if int((pr.block == b).sum()) != n:
                bad.append('%s 块 %s %d≠%d' % (prof, b, int((pr.block == b).sum()), n))
        if int((pr.role == 'ACCOUNT').sum()) != 756 or int((pr.role == 'MIRROR').sum()) != 308:
            bad.append('%s 角色计数' % prof)
        if set(pr.logical_id[pr.is_primary72 == 1]) != p72:
            bad.append('%s primary72' % prof)
        if set(pr.logical_id[pr.is_main_object == 1]) != main_ids or len(main_ids) != 2:
            bad.append('%s 主对象' % prof)
        ids = set(pr.exec_id)
        byid = pr.set_index('exec_id')
        for r in pr.itertuples(index=False):
            if r.role == 'ACCOUNT' and r.trigger != 'NONE':
                if r.parent_same_h_exec_id not in ids:
                    bad.append('父缺 %s' % r.logical_id)
                    continue
                p = byid.loc[r.parent_same_h_exec_id]
                if any(str(p[k]) != str(getattr(r, k)) for k in ('form', 'memory', 'H', 'deploy', 'cap', 'renew')) or p['trigger'] != 'NONE':
                    bad.append('父字段 %s' % r.logical_id)
            if r.role == 'MIRROR':
                o = pr[pr.logical_id == r.owner_logical_id]
                if len(o) != 1 or o.iloc[0].role != 'ACCOUNT' or o.iloc[0].deploy != 'NATIVE' or int(o.iloc[0].renew) != 0 or o.iloc[0].trigger == 'NONE':
                    bad.append('镜像 owner %s' % r.logical_id)
    if R.exec_hash.duplicated().any() or R.exec_id.duplicated().any():
        bad.append('exec_hash / exec_id 重复')
    if bad:
        raise RuntimeError('registry 自检失败：' + '; '.join(bad[:8]))
    # ---- comparisons（每情景 3,608）与 compound（874，长格式）
    lid2 = {(r.logical_id, r.execution_profile): r.exec_id for r in R.itertuples(index=False)}
    crow = []
    for prof in PROFILES:
        for i, c in enumerate(comps):
            crow.append(dict(comparison_id='CMP-%s-%04d' % (PSHORT[prof], i + 1), kind=c['kind'], left_exec_id=lid2[(c['left'], prof)],
                             right_exec_id=lid2[(c['right'], prof)], left_logical_id=c['left'], right_logical_id=c['right'], execution_profile=prof, note=''))
    C = pd.DataFrame(crow)
    for prof in PROFILES:
        kc = C[C.execution_profile == prof].kind.value_counts().to_dict()
        if kc != KIND_N:
            raise RuntimeError('comparisons 计数 %s' % kc)
    prow = []
    for prof in PROFILES:
        for i, c in enumerate(comp):
            if abs(sum(c['terms'].values())) != 0:
                raise RuntimeError('复合系数和非零')
            for lid, coef in sorted(c['terms'].items()):
                prow.append(dict(contrast_id='CPD-%s-%04d' % (PSHORT[prof], i + 1), kind=c['kind'], owner_logical_id=c['owner'], execution_profile=prof,
                                 term_exec_id=lid2[(lid, prof)], coefficient=int(coef)))
    PC = pd.DataFrame(prow)
    for prof in PROFILES:
        g = PC[PC.execution_profile == prof].drop_duplicates('contrast_id').kind.value_counts().to_dict()
        if g != COMPOUND_N:
            raise RuntimeError('compound 计数 %s' % g)
    RR = pd.DataFrame([dict(owner_logical_id=x['owner'], mechanism=x['mechanism'], minimum_paths=int(x['minimum_paths'])) for x in rcr]
                      + [dict(owner_logical_id=x['owner'], mechanism=x['mechanism'], minimum_paths=int(x['minimum_paths'])) for x in aux['renewal_only_controls']])
    if len(RR) != 2484 + 12:
        raise RuntimeError('random refs %d' % len(RR))
    FB = pd.DataFrame([dict(owner_logical_id=x['owner'], A_cny=int(round(x['A'])), kappa=x['kappa'], exponent=x['exponent']) for x in aux['cost_feedback']])
    if len(FB) != 84:
        raise RuntimeError('feedback refs %d' % len(FB))
    RD = pd.DataFrame([dict(owner_logical_id=x['owner'], kind=x['kind'], routing_reference_A=int(round(x['routing_reference_A'])), routing_kappa=x['routing_kappa'],
                            routing_exponent=x['routing_exponent'], priority_future_returns=str(bool(x['priority_future_returns'])).lower()) for x in rdr])
    if len(RD) != 18:
        raise RuntimeError('recycle refs %d' % len(RD))
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    EX = pd.DataFrame([dict(logical_id=s['id'], first_seen_at=now, selection_history='REGISTERED_AT_A1_FROM_PLAN_APPENDIX_C_JSON;NO_OUTCOME_SELECTION') for s in reg])
    out = {}
    for name, df in (('registry_E6p.csv', R), ('comparisons_E6p.csv', C), ('compound_contrasts_E6p.csv', PC), ('random_control_refs_E6p.csv', RR),
                     ('cost_feedback_refs_E6p.csv', FB), ('recycle_diagnostic_refs_E6p.csv', RD), ('exposure_E6p.csv', EX)):
        p = O.P('registration', name)
        O.atomic_write_csv(p, df)
        out[name] = p
    facts = dict(registry_rows=len(R), p_source=int((R.series == 'P_SOURCE').sum()), comparisons=len(C), compound_rows=len(PC), random_refs=len(RR),
                 feedback_refs=len(FB), recycle_refs=len(RD), exposure=len(EX), trigger_formula_hash=tfh, trigger_panel_sha256=trig_sha,
                 main_object_logical_ids=sorted(main_ids), wall_s=round(time.time() - t0, 1))
    O.atomic_write_json(O.P('registration', 'registry_facts_E6p.json'), facts)
    O.write_receipt('E6p_registry', list(out.values()), code=[__file__, O.__file__], **{k: v for k, v in facts.items() if k not in ('trigger_formula_hash', 'trigger_panel_sha256')})
    return R, facts


if __name__ == '__main__':
    R, f = build()
    print(json.dumps({k: v for k, v in f.items() if k not in ('trigger_formula_hash', 'trigger_panel_sha256')}, ensure_ascii=False), flush=True)
