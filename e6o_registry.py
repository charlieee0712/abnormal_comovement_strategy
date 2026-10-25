# -*- coding: utf-8 -*-
"""E6o A1 编译（brief §3；附录 B.1 / B.2 / B.3 合同）。输入 = plan 附录 B spec 重跑产物 verify/spec/e6o_spec_checks/registry.json（966 逻辑配置，
逻辑 ID = spec identity）与 level_worst_refs.json（72 owner）。输出：
  registration/registry_E6o.csv（C_ACCOUNT 966 × 2 情景 = 1,932 + P_ACCOUNT（坐标 × 情景 × 支持）+ P_SOURCE（坐标 × 支持））
  registration/comparisons_E6o.csv（B.2 词表）+ comparisons_extra_E6o.csv（spec 比较边原样，kind 不在 B.2 词表者）
  registration/run_plan_E6o.csv（每执行对象的引擎参数）、level_worst_refs_E6o.csv、random_scope_E6o.csv（brief §6 覆盖表）
  registration/ledger_G_E6o.csv / ledger_E_E6o.csv（事前登记行；结果栏 PENDING）、policy_profile_E6o.json
用法：python3 e6o_registry.py"""
import os
import sys
import json
import hashlib

import numpy as np
import pandas as pd

import e6o_core as O

POLICY = 'POLICY_E6O_PARENT_Q'
PRIMARY = ('T1a', 'T1b', 'T3c15_X', 'T4a')
MINUTE = ('T4a', 'T4b', 'T5')
TRIG_DEF = {
    'T1a': 'SOURCE_CVR20 bad state: CVR_20d raw -> pool0 same-day OLS on log mcap (source neutralize_by_mcap) -> qcut(rank first,5) group5 (= source drop_mask k5 on valued pool0 cells); off-pool holdings: resid with same (a_T,b_T) >= cut_T (min resid of group5); no value / no cut -> UNKNOWN; persistent state',
    'T1b': 'SOURCE_B2_TRIGGER bound from e6n_b2 / e6m_b6_triggers.cvr_triggers: cvr_1d=close/vwap-1; pct=#{same-day clean cvr<=v}/n; hi=pct>=.90; EDGE: today hi & yesterday known & not hi; yesterday unknown -> 0 (CVR_FIRST_VISIBLE_HIGH separate)',
    'T1b_LEVEL': 'same bound day-CVR contract; state: pct>=.90 (known), persistent',
    'T1b_EDGE': 'same bound day-CVR contract; explicit EDGE: today pct>=.90 & yesterday known pct<.90; yesterday unknown -> UNKNOWN',
    'T1b_OWNCHANGE': 'yesterday clean reference frozen: today cvr and yesterday cvr both located in yesterday reference; yesterday <.90 -> today >=.90',
    'T1c': 'holding domain (unique R_OBS securities with valid same-day cvr_1d): mid-distribution rank (N_<+.5N_=)/N >= .80',
    'T1d': 'holding domain mid-distribution rank >= .90',
    'T2': 'lot: cvr1d(T) - cvr1d(entry close e0) >= .01 (both finite)',
    'T2prime': 'T2 and T1a state known FALSE (T1a UNKNOWN -> UNKNOWN)',
    'T6a': 'lot: adjusted close / entry adjusted VWAP - 1 <= -.05 (close observed on open day)',
    'T6b': 'lot: adjusted close / entry adjusted VWAP - 1 <= -2 sigma_ENTRY20 (sigma = std of 20 pre-entry daily returns, >=10 finite, frozen at entry; sigma<=0 or missing -> UNKNOWN)',
    'T4a': 'tail CVR = C_official / (amount/volume of 5-min bars 14:35..15:00) - 1; pct vs same-day pool0 tail CVR; explicit EDGE at .90 (yesterday unknown -> UNKNOWN); minute from 2013-08-01',
    'T4b': 'jump = log(C_official / last continuous trade price at or before 14:57); TRUE if jump>0 and pct vs same-day same-exchange pool0 >= .90; persistent; SH before 2018-08-20 -> UNKNOWN',
    'T5': 'tail amount share (14:30-15:00 amount / day amount) - mean of previous 20 trading days same regime (>=10 complete days) >= .05',
}
for th, tag in ((1.5, '15'), (2.0, '20')):
    TRIG_DEF['T3a' + tag] = 'vr=V_T/mean(V_{T-20..T-1}) (>=10 finite, suspended=unknown, base>0) >= %.1f and r_day<0' % th
    TRIG_DEF['T3b' + tag] = 'vr >= %.1f and r_day>0' % th
    TRIG_DEF['T3c' + tag] = 'vr >= %.1f (any return sign)' % th
    for s, ex in (('a', 'industry rank (T-1 L1, clean EW same-day r_day, pct among industries) <=.2 exempt'),
                  ('b', 'industry rank >=.8 exempt'), ('c', 'either tail exempt')):
        TRIG_DEF['T3%s%s_X' % (s, tag)] = TRIG_DEF['T3%s%s' % (s, tag)] + '; X1_RANK: ' + ex
for s, ex in (('a', 'XR_DOWN exempt: rank<=.2 & peer<0 & own<peer'), ('b', 'XR_UP exempt: rank>=.8 & peer>0 & own>=peer'), ('c', 'XR_DOWN or XR_UP exempt')):
    TRIG_DEF['T3%s15_XR' % s] = TRIG_DEF['T3%s15' % s] + '; ' + ex + ' (peer = EW other clean same-industry r_day, >=2)'
REF = {'T1a': 'POOL0_CVR20_MCAPRESID_Q5_EXT', 'T1b': 'CLEAN_ECDF_CVR1D_P90_SOURCE', 'T1b_LEVEL': 'CLEAN_ECDF_CVR1D_P90', 'T1b_EDGE': 'CLEAN_ECDF_CVR1D_P90',
       'T1b_OWNCHANGE': 'CLEAN_ECDF_CVR1D_P90_YDAYREF', 'T1c': 'HOLDING_MIDRANK', 'T1d': 'HOLDING_MIDRANK', 'T2': 'ENTRY_CLOSE_CVR1D', 'T2prime': 'ENTRY_CLOSE_CVR1D_T1A',
       'T6a': 'ENTRY_VWAP_COST', 'T6b': 'ENTRY_VWAP_COST_SIG20', 'T4a': 'POOL0_ECDF_TAILCVR_P90', 'T4b': 'POOL0_EXCH_ECDF_JUMP_P90', 'T5': 'TAILSHARE_PRE20_SAMEREGIME',
       'NONE': 'NONE'}
ENGINE_TRIG = {'T1c': 'T1C', 'T1d': 'T1D', 'T2': 'T2', 'T2prime': 'T2P', 'T6a': 'T6A', 'T6b': 'T6B', 'NONE': 'NONE'}


def ref_of(t):
    if t in REF:
        return REF[t]
    return 'VR20_PRE20' + ('_X1RANK' if t.endswith('_X') else ('_XR' if t.endswith('_XR') else ''))


def h16(s):
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def main():
    spec = json.load(open(O.P('verify', 'spec', 'e6o_spec_checks', 'registry.json')))
    lwr = json.load(open(O.P('verify', 'spec', 'e6o_spec_checks', 'level_worst_refs.json')))
    if len(spec) != 966:
        raise RuntimeError('spec 注册表行数 %d != 966' % len(spec))
    src_hash = {}
    for f in O.FORMS:
        hs = []
        for s in O.SEGS:
            hs.append(O.sha_file(O.E6N('masks', s, '%s.npz' % f)))
        for m in O.MEMS:
            src_hash[(f, m)] = h16('|'.join(hs) + '|' + O.MEMKEY[m] + '|' + O.sha_file(os.path.join(os.path.dirname(O.__file__), 'e6o_source.py')))
    rows = []
    plan = []

    def eid(form, mem, H, trig, fund, lag, mat, re_, eg, ex, prof, back, sup):
        return '|'.join([form, 'a0.25', mem, 'H%d' % H, trig, fund, lag, mat, re_, eg, ex, prof, back, sup, 'CASH_V0', POLICY])

    parents = {}

    def parent(form, mem, H, sup, prof):
        if prof == 'SOURCE':
            e = eid(form, mem, H, 'NONE', 'NA', 'NA', 'NA', 'NA', 'OFF', 'OFF', 'SOURCE', 'SOURCE', sup)
            series = 'P_SOURCE'
        else:
            e = eid(form, mem, H, 'NONE', 'NA', 'NA', 'NA', 'NA', 'OFF', 'OFF', prof, 'ACCOUNT', sup)
            series = 'P_ACCOUNT'
        if e not in parents:
            parents[e] = dict(series=series, form=form, memory=mem, H=H, support=sup, profile=prof)
        return e

    spec_id_to_exec = {}
    for s in spec:
        form, mem, H, trig = s['form'], s['memory'], int(s['H']), s['trigger']
        fund = s['funding']
        if fund == 'CASH':
            lag, mat = 'NA', 'NA'
        else:
            lag, mat = 'lag%d' % int(s['recycle_lag']), s['recycle_maturity']
        re_ = s['reentry']
        eg = 'ON' if s['entry_guard'] != 'NONE' else 'OFF'
        ex = 'ON' if s['exit_enabled'] else 'OFF'
        sup = 'MINUTE_2013' if trig in MINUTE else 'FULLHIST'
        for prof in ('FEASIBLE_DAILY', 'IDEALIZED_SOURCE_FILL'):
            e = eid(form, mem, H, trig, fund, lag, mat, re_, eg, ex, prof, 'ACCOUNT', sup)
            pa = parent(form, mem, H, sup, prof)
            ps = parent(form, mem, H, sup, 'SOURCE')
            tfh = h16(TRIG_DEF[trig])
            rc = ref_of(trig)
            sh = src_hash[(form, mem)]
            is_p72 = int(s['family'] == 'CORE' and H == 5 and trig in PRIMARY and fund == 'ENGINE_NATIVE' and re_ == 'ALLOW' and prof == 'FEASIBLE_DAILY')
            is_main = int(form == O.MAIN_FORM and mem == 'HG10' and H == 5 and trig == 'T1b' and fund == 'ENGINE_NATIVE' and lag == 'lag1'
                          and mat == 'RESET_H' and re_ == 'ALLOW' and eg == 'OFF' and ex == 'ON' and s['family'] == 'CORE')
            rows.append(dict(exec_id=e, exec_hash=h16(e + tfh + rc + sh), logical_id=s['id'], family=s['family'], series='C_ACCOUNT', form=form,
                             Qalpha='a0.25', memory=mem, H='H%d' % H, trigger=trig, trigger_formula_hash=tfh, source_ref_contract=rc, funding=fund,
                             recycle_lag=lag, recycle_maturity=mat, reentry=re_, entry_guard=eg, exit_enabled=ex, execution_profile=prof,
                             accounting_backend='ACCOUNT', support=sup, start_state='CASH_V0', policy_version=POLICY, source_hash=sh,
                             parent_exec_id=pa, source_parent_exec_id=ps, is_primary72=is_p72, is_main_object=is_main, status='NOT_RUN'))
            guard = 'NONE'
            if eg == 'ON':
                guard = 'T1A' if trig == 'T1a' else 'LVL'
            recon = 'NONE'
            if re_ == 'RECONFIRM':
                recon = 'T1A' if trig == 'T1a' else 'LVL'
            plan.append(dict(exec_id=e, H=H, form=form, memory=mem, trig_panel=(trig if trig not in ENGINE_TRIG else ''), trig_mode=ENGINE_TRIG.get(trig, 'PANEL'),
                             fund={'ENGINE_NATIVE': 'NATIVE', 'CASH': 'CASH', 'NEXT_RANK': 'NEXT'}[fund], lag=int(s['recycle_lag']),
                             maturity=1 if s['recycle_maturity'] == 'ORIGINAL_DUE' else 0, reentry=re_, guard=guard, exit_on=int(ex == 'ON'),
                             ideal=int(prof != 'FEASIBLE_DAILY'), recon=recon, series='C_ACCOUNT', support=sup))
            spec_id_to_exec[(s['id'], prof)] = e
    for e, p in parents.items():
        tfh = h16('NONE')
        sh = src_hash[(p['form'], p['memory'])]
        rows.append(dict(exec_id=e, exec_hash=h16(e + tfh + 'NONE' + sh), logical_id='PARENT::%s::%s::%s::H%d' % (p['series'], p['form'], p['memory'], p['H']),
                         family='PARENT', series=p['series'], form=p['form'], Qalpha='a0.25', memory=p['memory'], H='H%d' % p['H'], trigger='NONE',
                         trigger_formula_hash=tfh, source_ref_contract='NONE', funding='NA', recycle_lag='NA', recycle_maturity='NA', reentry='NA',
                         entry_guard='OFF', exit_enabled='OFF', execution_profile=p['profile'], accounting_backend='SOURCE' if p['series'] == 'P_SOURCE' else 'ACCOUNT',
                         support=p['support'], start_state='CASH_V0', policy_version=POLICY, source_hash=sh,
                         parent_exec_id=(e if p['series'] == 'P_SOURCE' else parent(p['form'], p['memory'], p['H'], p['support'], 'SOURCE')),
                         source_parent_exec_id=parent(p['form'], p['memory'], p['H'], p['support'], 'SOURCE'), is_primary72=0, is_main_object=0, status='NOT_RUN'))
        if p['series'] == 'P_ACCOUNT':
            plan.append(dict(exec_id=e, H=p['H'], form=p['form'], memory=p['memory'], trig_panel='', trig_mode='NONE', fund='NONE', lag=1, maturity=0,
                             reentry='ALLOW', guard='NONE', exit_on=0, ideal=int(p['profile'] != 'FEASIBLE_DAILY'), recon='NONE', series='P_ACCOUNT',
                             support=p['support']))
    R = pd.DataFrame(rows)
    if R.exec_id.duplicated().any():
        raise RuntimeError('exec_id 重复 %d' % int(R.exec_id.duplicated().sum()))
    c = R[R.series == 'C_ACCOUNT']
    fam = c[c.execution_profile == 'FEASIBLE_DAILY'].family.value_counts().to_dict()
    # 比较图（B.2 词表）
    reg = R.set_index('exec_id')
    cmp_rows = []
    extra_rows = []

    def addc(kind, ch, pa, prof, note=''):
        cmp_rows.append(dict(comparison_id='C%06d' % (len(cmp_rows) + 1), kind=kind, child_exec_id=ch, parent_exec_id=pa, execution_profile=prof, note=note))

    for r in c.itertuples():
        addc('MAIN_EXIT', r.exec_id, r.parent_exec_id, r.execution_profile, 'C_ACCOUNT − 同引擎同情景同支持无退出 P_ACCOUNT')
        addc('MIGRATION', r.exec_id, r.source_parent_exec_id, r.execution_profile, 'C_ACCOUNT − P_SOURCE（完整迁移差）')
    for e, p in parents.items():
        if p['series'] == 'P_ACCOUNT' and p['profile'] == 'IDEALIZED_SOURCE_FILL':
            addc('BRIDGE_IDEAL', e, parent(p['form'], p['memory'], p['H'], p['support'], 'SOURCE'), 'IDEALIZED_SOURCE_FILL', 'P_ACCOUNT_IDEAL − P_SOURCE（现金 / 估值 / 费用时钟）')
        if p['series'] == 'P_ACCOUNT' and p['profile'] == 'FEASIBLE_DAILY':
            addc('BRIDGE_FEASIBLE', e, parent(p['form'], p['memory'], p['H'], p['support'], 'IDEALIZED_SOURCE_FILL'), 'FEASIBLE_DAILY',
                 'P_ACCOUNT_FEASIBLE − P_ACCOUNT_IDEAL（成交约束）')
    feas = c[c.execution_profile == 'FEASIBLE_DAILY']
    for r in feas.itertuples():
        e_ideal = r.exec_id.replace('|FEASIBLE_DAILY|', '|IDEALIZED_SOURCE_FILL|')
        if r.is_primary72 == 1 or r.is_main_object == 1:
            addc('PROFILE_BRIDGE', r.exec_id, e_ideal, 'FEASIBLE_DAILY', 'FEASIBLE − IDEALIZED（同配置情景桥）')
    # spec 比较边 → B.2 词表映射；其余原样进 extra
    edges = json.load(open(O.P('verify', 'spec', 'e6o_spec_checks', 'comparisons.json')))
    KMAP = {'CASH_VS_NATIVE': 'FUNDING_PAIR', 'NEXT_VS_NATIVE': 'FUNDING_PAIR', 'LAG0_VS_LAG1': 'FUNDING_PAIR', 'REMAIN_VS_RESET': 'FUNDING_PAIR',
            'CONFIRM_VS_ALLOW': 'REENTRY_PAIR', 'CONFIRM_VS_BLOCK': 'REENTRY_PAIR', 'XR_VS_X': 'SECTOR_PAIR', 'ENTRY_VETO_CONTEXT': 'ENTRY_VETO_CONTEXT',
            'ADD_EXIT_AFTER_ENTRY_GUARD': 'ENTRY_EXIT_INTERACTION', 'ADD_ENTRY_GUARD_AFTER_EXIT': 'ENTRY_EXIT_INTERACTION'}
    for ed in edges:
        k = ed['kind']
        if k in ('VS_SAME_ACCOUNT_PARENT', 'VS_HISTORICAL_SOURCE'):
            continue
        for prof in ('FEASIBLE_DAILY', 'IDEALIZED_SOURCE_FILL'):
            ch = spec_id_to_exec.get((ed['left'], prof))
            pa = spec_id_to_exec.get((ed['right'], prof))
            if ch is None or pa is None:
                raise RuntimeError('spec 比较边找不到执行对象：%s' % k)
            if k in KMAP:
                addc(KMAP[k], ch, pa, prof, 'spec:%s' % k)
            else:
                extra_rows.append(dict(spec_kind=k, child_exec_id=ch, parent_exec_id=pa, execution_profile=prof))
    # ENTRY × EXIT 四账户：I = Y10 − Y00、X = Y01 − Y00
    for r in c[(c.family == 'ENTRY_EXIT')].itertuples():
        y00 = r.parent_exec_id
        if r.exit_enabled == 'OFF':
            addc('ENTRY_EXIT_I', r.exec_id, y00, r.execution_profile, 'Y10 − Y00（只停新买）')
        else:
            y01 = r.exec_id.replace('|ON|ON|', '|OFF|ON|')
            if y01 in reg.index:
                addc('ENTRY_EXIT_X', y01, y00, r.execution_profile, 'Y01 − Y00（只卖已有）')
    # 日水平控制 owner（72）
    lw = []
    for x in lwr:
        for prof in ('FEASIBLE_DAILY',):
            e = spec_id_to_exec[(x['owner'], prof)]
            lw.append(dict(owner_exec_id=e, kind='LEVEL_WORST_1D', risk_contract=x['risk_contract'], measurement_contract=x['measurement_contract']))
            addc('LEVEL_WORST_1D', e, reg.loc[e, 'parent_exec_id'], prof, '控制在 statistics/randoms_E6o.csv mechanism = LEVEL_WORST_1D')
    LW = pd.DataFrame(lw)
    if LW.owner_exec_id.nunique() != 72:
        raise RuntimeError('LEVEL_WORST owner 去重 %d != 72' % LW.owner_exec_id.nunique())
    CMP = pd.DataFrame(cmp_rows)
    ids = set(R.exec_id)
    if not (CMP.child_exec_id.isin(ids).all() and CMP.parent_exec_id.isin(ids).all()):
        raise RuntimeError('比较图有 id 不在注册表')
    # 随机覆盖（brief §6）
    def main_coord(r):
        return r.form == O.MAIN_FORM and r.H == 'H5' and r.trigger in PRIMARY and r.funding == 'ENGINE_NATIVE' and r.reentry == 'ALLOW' and r.recycle_lag == 'lag1' \
            and r.recycle_maturity == 'RESET_H' and r.family == 'CORE'
    rs = []
    for r in c.itertuples():
        mc = main_coord(r)
        if r.execution_profile == 'FEASIBLE_DAILY':
            if r.exit_enabled == 'ON':
                rs.append(dict(owner_exec_id=r.exec_id, mechanism='AMOUNT_MATCH', paths=128, topup_to=1024 if mc else 128, scope='FEASIBLE_ALL_WITH_EXITS'))
            if mc:
                for m in ('COUNT_IID', 'COUNT_ISK', 'BERNOULLI_LAG60'):
                    rs.append(dict(owner_exec_id=r.exec_id, mechanism=m, paths=128, topup_to=128, scope='MAIN_MOTHER_3MEM_4PRIMARY'))
            if r.family == 'RECONFIRM':
                rs.append(dict(owner_exec_id=r.exec_id, mechanism='RECONFIRM_RANDOM', paths=128, topup_to=128, scope='RECONFIRM_18'))
                rs.append(dict(owner_exec_id=r.exec_id, mechanism='RE_ELIGIBILITY_MATCH', paths=128, topup_to=128, scope='RECONFIRM_18'))
            if r.family == 'ENTRY_EXIT' and r.trigger == 'T1b_LEVEL':
                rs.append(dict(owner_exec_id=r.exec_id, mechanism='ENTRY_RANDOM', paths=128, topup_to=128, scope='ENTRY_T1B_LEVEL_3MEM'))
        else:
            if r.is_primary72 == 0 and (r.exec_id.replace('|IDEALIZED_SOURCE_FILL|', '|FEASIBLE_DAILY|') in set(c[c.is_primary72 == 1].exec_id) or mc):
                rs.append(dict(owner_exec_id=r.exec_id, mechanism='AMOUNT_MATCH', paths=128, topup_to=128, scope='IDEAL_PRIMARY72_AND_MAIN'))
    for x in lw:
        rs.append(dict(owner_exec_id=x['owner_exec_id'], mechanism='LEVEL_WORST_1D', paths=1, topup_to=1, scope='LEVEL_WORST_72'))
    RS = pd.DataFrame(rs).drop_duplicates(['owner_exec_id', 'mechanism'])
    od = O.P('registration')
    os.makedirs(od, exist_ok=True)
    O.atomic_write_csv(os.path.join(od, 'registry_E6o.csv'), R)
    O.atomic_write_csv(os.path.join(od, 'comparisons_E6o.csv'), CMP)
    O.atomic_write_csv(os.path.join(od, 'comparisons_extra_E6o.csv'), pd.DataFrame(extra_rows))
    O.atomic_write_csv(os.path.join(od, 'run_plan_E6o.csv'), pd.DataFrame(plan))
    O.atomic_write_csv(os.path.join(od, 'level_worst_refs_E6o.csv'), LW)
    O.atomic_write_csv(os.path.join(od, 'random_scope_E6o.csv'), RS)
    pd.DataFrame([dict(trigger=k, trigger_formula_hash=h16(v), source_ref_contract=ref_of(k), definition=v) for k, v in sorted(TRIG_DEF.items())]).pipe(
        lambda d: O.atomic_write_csv(os.path.join(od, 'trigger_definitions_E6o.csv'), d))
    facts = dict(C_ACCOUNT=int(len(c)), logical=int(c.logical_id.nunique()), P_ACCOUNT=int((R.series == 'P_ACCOUNT').sum()),
                 P_SOURCE=int((R.series == 'P_SOURCE').sum()), primary72=int(c.is_primary72.sum()), main=int(c.is_main_object.sum()),
                 families_feasible=fam, comparisons=int(len(CMP)), comparisons_by_kind=CMP.kind.value_counts().to_dict(),
                 comparisons_extra=int(len(extra_rows)), spec_edges=int(len(edges)), level_worst_owners=int(LW.owner_exec_id.nunique()),
                 random_scope=RS.groupby('mechanism').size().to_dict())
    O.atomic_write_json(os.path.join(od, 'registry_facts_E6o.json'), facts)
    print(json.dumps(facts, ensure_ascii=False, default=str), flush=True)


if __name__ == '__main__':
    main()
