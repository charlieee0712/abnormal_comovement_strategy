# -*- coding: utf-8 -*-
"""E6m 阶段 N · N3：A0 编译（brief §3 / 附录 N3；plan §10 / §12 / §13.3）。不读任何收益，不读行情。
以 plan §16 参考脚本（stage0/plan_tests/e6m_spec_tests.py，sha 25020c82…）的 registry / primary / supplemental / comparison
为语义权威，补齐：真实源字段（门位置、下游合同、记忆引用、评分几何、条件、支持、费用、初始化）、任务键、暴露与锚候选、
政策字段、18 卡绑定（卡文本逐字取自 PLAN_COPY.md）、卡片比较视图、附属八项（plan §10.3）清单与计数、B3–B6 query 清单、
固定输出与每个 query 的带 status 行骨架、政策合同转录、A1-auto 阶段 N 可判项。
对账：语义元组集合与 semantic_id 与 spec 输出逐一相同；计数逐块相同。"""
import os
import re
import sys
import json
import hashlib
import itertools
import importlib.util

import numpy as np
import pandas as pd

import e6m_core as M

SPEC_SHA = '25020c8239adb9b7a2ee86a45aa653005689b38127d94187a1be546fe062cca9'
SEM = ('measurement', 'parent', 'operator', 'param', 'alpha', 'memory', 'H', 'adapter', 'condition')
P6 = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
LAND = (1, 3, 5, 10, 20)
NEW_BLOCKS = ('BAND_Q', 'BAND_BLEND', 'FILTER', 'TWO_DAY', 'EDIT_MATCH', 'MEAN_SLOT_BRIDGE', 'LEAK_BRIDGE', 'V_STATE')
STATUS_ROW = 'NOT_RUN_STAGE_N'


def load_spec():
    p = M.P('stage0', 'plan_tests', 'e6m_spec_tests.py')
    if M.sha_file(p) != SPEC_SHA:
        raise RuntimeError('spec sha 不符')
    sp = importlib.util.spec_from_file_location('e6m_spec_ref', p)
    mod = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    return mod


def fmt(x, pre):
    return '-' if x is None else '%s%g' % (pre, x)


def desc_id(r):
    op = r['operator']
    pre = 'c' if op in ('PRIORITY_PASS', 'HARD_CONJ') else ('d' if op.startswith('DELETE_') else 'w')
    return '|'.join([r['measurement'], r['parent'], op, fmt(r['param'], pre), fmt(r['alpha'], 'a'), r['memory'], 'H%d' % r['H'], r['adapter'],
                     r['condition'] or '-'])


def family_of(p):
    return 'A4b' if p.startswith('A4b') else ('Mmean' if p.startswith('M_mean') else ('Munion' if p.startswith('M_union') else p))


def gate_position(r):
    b, ad, p = r['block'], r['adapter'], r['parent']
    if b == 'PARENT':
        return 'SOURCE_PARENT'
    if ad == 'SOURCE':
        return 'SOURCE_K_SLOT_OLD_RULE' if b == 'OLD_RULE' else 'SOURCE_K_SLOT'
    if ad == 'K_SLOT':
        return 'MMEAN_K_SLOT_BRIDGE'
    if ad == 'POST_PARENT':
        return 'POST_PARENT_DELETE'
    return {'A4b': 'A4B_K_FIRST_GATE', 'Munion': 'MUNION_K_TAIL_GATE', 'Mmean': 'MMEAN_COMPOSITE_GATE'}[family_of(p)]


def downstream(p):
    f = family_of(p)
    cvr = '→CVR_K5_VETO' if p.endswith('CVRv5') else ''
    if f == 'A4b':
        return 'T_REFIT_IN_NEW_G→SECOND_GATE%s→DEV' % cvr
    if f == 'Munion':
        return 'AND_T_CR20_KEEP%s→DEV' % cvr
    if f == 'Mmean':
        return '%s→DEV' % (cvr[1:] if cvr else 'NO_VETO')
    return 'E6I_PARENT_CONTRACT_SOURCE_WAIT'


def memory_reference(r):
    m = r['memory']
    return {'NONE': 'NONE', 'HG10': 'ACTUAL_G_PREV_DAY_OWN_PATH', 'LAG1_10': 'NATURAL_U_PREV_DAY_SAME_SOURCE_OPERATOR_NO_BONUS',
            'PROTECTED_LAG10': 'NATURAL_U_PREV_DAY_SAME_OPERATOR_NO_BONUS', 'UNPROTECTED_LAG10': 'NATURAL_U_PREV_DAY_SAME_OPERATOR_NO_BONUS',
            'RULE_LAG10': ('NATURAL_U_PREV_DAY_OLD_CORE_SOURCE_LAG' if r['operator'] == 'HARD_CONJ'
                           else 'NATURAL_U_PREV_DAY_SAME_RULE_WITHIN_PASS_FAIL_PARTITION')}[m]


def score_geometry(r):
    if r['block'] == 'LEAK_BRIDGE':
        return 'SLOT_MAPPED_UNPROTECTED'
    if r['block'] in ('BAND_Q', 'BAND_BLEND') and r['memory'] == 'PROTECTED_LAG10':
        return 'SLOT_MAPPED'
    if r['block'] == 'MEAN_SLOT_BRIDGE':
        return 'K_SLOT_REMAP'
    return 'NOT_APPLICABLE'


def support_of(r):
    b = r['block']
    if b == 'TWO_DAY':
        return 'TWO_DAY_BOTH_VALID_ELSE_OLD_K_MARKED'
    if b in ('BAND_Q', 'BAND_BLEND', 'FILTER', 'LEAK_BRIDGE', 'MEAN_SLOT_BRIDGE', 'EDIT_MATCH'):
        return 'OWNER_MISSING_IDENTITY_FROZEN'
    if b == 'V_STATE':
        return 'V_VALID_AND_CONDITION（UNKNOWN 不删）' if r['condition'] != 'ALL' else 'V_VALID（ALL 不读 Trend）'
    return 'SOURCE_NATIVE_FALLBACK'


def anchor_candidate(r):
    b, m, mem = r['block'], r['measurement'], r['memory']
    if b == 'PARENT':
        return 'E6I_PARENT_ANCHOR' if r['parent'] in ('R2', 'A06') else 'E5A_POOL2+E6J_LEADER+E6K/E6L_PARENT'
    if b == 'OLD_RULE':
        return 'E6K_POLICY(K0×HG_ONLY10)' if mem == 'HG10' else 'E6L_POLICY_CANDIDATE(K0×LAG1_10)'
    if b == 'SOURCE':
        if m in ('Q0', 'C1') and mem in ('NONE', 'HG10'):
            return 'E6K_POLICY'
        if m == 'Q0' and mem == 'LAG1_10':
            return 'E6L_POLICY'
        return 'REGISTRY_INTERSECTION_AT_S1'
    return 'NONE_NEW_OPERATOR'


def exposure(r):
    if r['block'] in NEW_BLOCKS:
        return M.LABEL_FIRST_LOOK
    if r['block'] == 'PARENT':
        return 'SOURCE_PARENT'
    return 'SOURCE_WAIT_REGISTRY_INTERSECTION'          # 实际交集在 S1 对 E6k / E6l 登记表定（W08）


def e_random(r):
    if r['block'] == 'PARENT':
        return 'NOT_APPLICABLE'
    if r['block'] == 'OLD_RULE':
        return 'NO_NEW_CONTENT_TO_PERMUTE'
    if r['H'] not in LAND:
        return 'RANDOM_NOT_SCHEDULED'
    return 'DELETE_BUDGET_COND' if r['block'] == 'V_STATE' else 'LEGACY_POLICY_RANDOM'


def family(r):
    b = r['block']
    if b == 'SOURCE':
        return {'NONE': 'SOURCE_NATIVE', 'HG10': 'SOURCE_HG10', 'LAG1_10': 'SOURCE_LAG1_10'}[r['memory']]
    if b == 'FILTER':
        return 'FILTER_PRIORITY' if r['operator'] == 'PRIORITY_PASS' else 'FILTER_HARD'
    return b


def task_key(r, extra):
    k = {f: r[f] for f in SEM}
    k.update({f: extra[f] for f in ('domain', 'gate_position', 'support', 'cost', 'init', 'score_geometry', 'memory_reference', 'label_id', 'matching_id')})
    k['source_parent'] = r['parent']
    return hashlib.sha256(json.dumps(k, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def build_descriptors(spec):
    rows = spec.registry()
    prim_no = {t: (i % 12) + 1 for i, t in enumerate(spec.primary())}          # primary() 按母体排、每母体 12 配方同序
    prim = set(prim_no)
    out = []
    for r in rows:
        sig = spec.signature(r)
        ex = dict(domain='POOL0', gate_position=gate_position(r), support=support_of(r), cost='SOURCE_8BP_CHARGED_TURN',
                  init='SEGMENT_RESET_19D_WARMUP', score_geometry=score_geometry(r), memory_reference=memory_reference(r),
                  label_id='NOT_APPLICABLE', matching_id='NOT_APPLICABLE')
        recipe = prim_no.get(sig)
        d = dict(desc_id=desc_id(r), semantic_id=spec.semantic_id(r), block=r['block'], family=family(r), **{f: r[f] for f in SEM},
                 parent_kind='STRONG_REFERENCE' if r['parent'] in ('R2', 'A06') else 'PRODUCTION_FORM', mother_family=family_of(r['parent']),
                 downstream_contract=downstream(r['parent']), **ex, data_sha='BOUND_AT_RUN', code_sha='BOUND_AT_RUN',
                 task_key_semantic=task_key(r, ex), is_primary72=sig in prim, primary_recipe=recipe or 0,
                 in_policy_table=r['block'] != 'PARENT', exposure=exposure(r), anchor_candidate=anchor_candidate(r),
                 replacement_preference_status='NOT_AUTHORIZED' if r['block'] in NEW_BLOCKS else (
                     'NOT_APPLICABLE' if r['block'] == 'PARENT' else 'PER_SOURCE_POLICY_SOURCE_WAIT'),
                 deployment_authorized=False,
                 three_sentence_addition='NOT_ELIGIBLE_NEW_OPERATOR' if r['block'] in NEW_BLOCKS else (
                     'NOT_APPLICABLE' if r['block'] == 'PARENT' else 'PER_PX1_SOURCE_WAIT'),
                 e_random_mechanism=e_random(r), post_segment_authorization='MODE_A_PENDING_USER')
        out.append(d)
    D = pd.DataFrame(out)
    for c in ('param', 'alpha', 'condition'):
        D[c] = D[c].map(lambda v: 'NOT_APPLICABLE' if v is None or (isinstance(v, float) and np.isnan(v)) else v)
    return D, rows


def build_supplemental(spec, rows):
    extra = spec.supplemental_registry(rows)
    out = []
    for e in extra:
        r = e['semantic']
        kind = e['diagnostic']
        sem = dict({f: r[f] for f in SEM}, diagnostic=kind)
        if kind == 'V_ALL_KNOWN':
            sem['condition'] = 'ALL_KNOWN'
        sid = hashlib.sha256(json.dumps(sem, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
        geom = {'NATIVE_METRIC_LAG': 'NATIVE_METRIC', 'COPY_NATIVE_METRIC_LAG': 'COPY_NATIVE_METRIC'}.get(kind, 'NOT_APPLICABLE')
        out.append(dict(supp_id=sid, diagnostic=kind, owner_semantic_id=e['owner'], owner_desc_id=desc_id(r), **{f: r[f] for f in SEM},
                        condition_effective=sem['condition'] or 'NOT_APPLICABLE', score_geometry=geom,
                        memory_reference=('NATURAL_U_PREV_DAY_OWN_COPY_NO_BONUS' if kind == 'COPY_NATIVE_METRIC_LAG' else memory_reference(r)),
                        owner_mask='COPY_GATE_ORDER_OWNER' if kind.startswith('COPY') else 'Q_OWNER', in_policy_table=False,
                        exposure=M.LABEL_FIRST_LOOK, deployment_authorized=False, replacement_preference_status='NOT_AUTHORIZED'))
    S = pd.DataFrame(out)
    for c in ('param', 'alpha', 'condition'):
        S[c] = S[c].map(lambda v: 'NOT_APPLICABLE' if v is None or (isinstance(v, float) and np.isnan(v)) else v)
    return S


def build_comparisons(spec, rows, D, S):
    base = spec.comparison_manifest(rows)
    did = dict(zip(D.semantic_id, D.desc_id))
    C = pd.DataFrame(base)
    C['view'] = 'BASE'
    C['card'] = ''
    sig2sid = {spec.signature(r): spec.semantic_id(r) for r in rows}

    def sid(meas, p, op, x, a, m, h, ad, cond=None):
        return sig2sid.get((meas, p, op, x, a, m, h, ad, cond))

    ext = []

    def add(view, card, l, r, kind):
        if l and r and l != r:
            ext.append(dict(left=l, right=r, kind=kind, view=view, card=card))
    A_ = (.125, .25, .5)
    H_ = tuple(range(1, 21))
    # 主展示扩展视图（plan §10.1：相对源 Q-NATIVE / Q-HG / Q-LAG；R2 / A06 同 H 与 H5 分开）
    for t in spec.primary():
        l = sig2sid[t]
        p = t[1]
        for m, kind in (('NONE', 'VS_SOURCE_Q_NATIVE'), ('HG10', 'VS_SOURCE_Q_HG10'), ('LAG1_10', 'VS_SOURCE_Q_LAG1_10')):
            add('PRIMARY_EXT', 'Q16', l, sid('Q0', p, 'LINEAR', None, .25, m, 5, 'SOURCE'), kind)
        for ref in ('R2', 'A06'):
            add('PRIMARY_EXT', 'Q16', l, sid('K0', ref, 'PARENT', None, None, 'NONE', 5, 'SOURCE'), 'VS_STRONG_REF_H5')
    # Q01：HG vs LAG（源 SOURCE 与旧规则 OLD_RULE）
    for f, p, a, h in itertools.product(('Q0', 'C1', 'S', 'M'), P6, A_, H_):
        add('Q01_HG_VS_LAG', 'Q01', sid(f, p, 'LINEAR', None, a, 'HG10', h, 'SOURCE'), sid(f, p, 'LINEAR', None, a, 'LAG1_10', h, 'SOURCE'), 'HG10_MINUS_LAG1_10')
    for p, h in itertools.product(P6, H_):
        add('Q01_OLDRULE_HG_VS_LAG', 'Q01', sid('K0', p, 'OLD_RULE', None, 0., 'HG10', h, 'SOURCE'), sid('K0', p, 'OLD_RULE', None, 0., 'LAG1_10', h, 'SOURCE'),
            'HG10_MINUS_LAG1_10')
    # Q02：局部 vs 全域（BAND_Q 无记忆 − 源 NATIVE α 各档）
    for f, p, w, a, h in itertools.product(('Q0', 'C1'), P6, (.02, .05, .1, .2, .4), A_, H_):
        add('Q02_BAND_VS_NATIVE', 'Q02', sid(f, p, 'BAND_Q', w, None, 'NONE', h, 'ACTUAL_GATE'), sid(f, p, 'LINEAR', None, a, 'NONE', h, 'SOURCE'),
            'BAND_Q_MINUS_SOURCE_NATIVE_a%g' % a)
    # Q03：BAND_BLEND − BAND_Q（同 B、同名额、同记忆）
    for f, p, w, a, m, h in itertools.product(('Q0', 'C1'), P6, (.05, .1, .2, .4), A_, ('NONE', 'PROTECTED_LAG10'), H_):
        add('Q03_BLEND_VS_BANDQ', 'Q03', sid(f, p, 'BAND_BLEND', w, a, m, h, 'ACTUAL_GATE'), sid(f, p, 'BAND_Q', w, None, m, h, 'ACTUAL_GATE'), 'BLEND_MINUS_BANDQ')
    # Q04：Mmean 位置桥（K 槽位 vs 真实综合门）
    for f, p, w, h in itertools.product(('Q0', 'C1'), P6[2:4], (.1, .2), H_):
        add('Q04_SLOT_VS_ACTUAL', 'Q04', sid(f, p, 'SLOT_Q', w, None, 'NONE', h, 'K_SLOT'), sid(f, p, 'BAND_Q', w, None, 'NONE', h, 'ACTUAL_GATE'),
            'K_SLOT_MINUS_ACTUAL_GATE')
        add('Q04_SLOT_VS_ACTUAL', 'Q04', sid(f, p, 'SLOT_BLEND25', w, .25, 'NONE', h, 'K_SLOT'), sid(f, p, 'BAND_BLEND', w, .25, 'NONE', h, 'ACTUAL_GATE'),
            'K_SLOT_MINUS_ACTUAL_GATE')
    # Q05：PRIORITY − HARD（同 c、同记忆）
    for f, p, c, m, h in itertools.product(('Q0', 'C1', 'M'), P6, (.3, .5, .7, .8, .9), ('NONE', 'RULE_LAG10'), H_):
        add('Q05_PRIORITY_VS_HARD', 'Q05', sid(f, p, 'PRIORITY_PASS', c, None, m, h, 'ACTUAL_GATE'), sid(f, p, 'HARD_CONJ', c, None, m, h, 'ACTUAL_GATE'),
            'PRIORITY_MINUS_HARD')
    # Q06：记忆 × 局部规则（保护 − 无记忆；非保护桥 − 保护）
    for f, p, w, h in itertools.product(('Q0', 'C1'), P6, (.02, .05, .1, .2, .4), H_):
        add('Q06_PROTECTED_VS_NONE', 'Q06', sid(f, p, 'BAND_Q', w, None, 'PROTECTED_LAG10', h, 'ACTUAL_GATE'), sid(f, p, 'BAND_Q', w, None, 'NONE', h, 'ACTUAL_GATE'),
            'PROTECTED_MINUS_NONE')
    for f, p, w, a, h in itertools.product(('Q0', 'C1'), P6, (.05, .1, .2, .4), A_, H_):
        add('Q06_PROTECTED_VS_NONE', 'Q06', sid(f, p, 'BAND_BLEND', w, a, 'PROTECTED_LAG10', h, 'ACTUAL_GATE'), sid(f, p, 'BAND_BLEND', w, a, 'NONE', h, 'ACTUAL_GATE'),
            'PROTECTED_MINUS_NONE')
    for f, p, w, h in itertools.product(('Q0', 'C1'), P6, (.1, .2), (1, 5, 20)):
        add('Q06_UNPROTECTED_VS_PROTECTED', 'Q06', sid(f, p, 'BAND_Q', w, None, 'UNPROTECTED_LAG10', h, 'ACTUAL_GATE'),
            sid(f, p, 'BAND_Q', w, None, 'PROTECTED_LAG10', h, 'ACTUAL_GATE'), 'UNPROTECTED_MINUS_PROTECTED')
    for f, p, c, h in itertools.product(('Q0', 'C1', 'M'), P6, (.3, .5, .7, .8, .9), H_):
        for op in ('PRIORITY_PASS', 'HARD_CONJ'):
            add('Q06_RULE_LAG_VS_NONE', 'Q06', sid(f, p, op, c, None, 'RULE_LAG10', h, 'ACTUAL_GATE'), sid(f, p, op, c, None, 'NONE', h, 'ACTUAL_GATE'),
                'RULE_LAG_MINUS_NONE')
    # Q07：同编辑预算三账户
    for p, a, w, h in itertools.product(P6, A_, (.1, .2), H_):
        L_, G_, T_ = (sid('Q0', p, op, w, a, 'NONE', h, 'ACTUAL_GATE') for op in ('EDIT_LOCAL', 'EDIT_GLOBAL', 'EDIT_NATIVE_TRIM'))
        add('Q07_EDIT_PAIRS', 'Q07', L_, G_, 'LOCAL_MINUS_GLOBAL')
        add('Q07_EDIT_PAIRS', 'Q07', L_, T_, 'LOCAL_MINUS_NATIVE_TRIM')
        add('Q07_EDIT_PAIRS', 'Q07', G_, T_, 'GLOBAL_MINUS_NATIVE_TRIM')
        for x in (L_, G_, T_):
            add('Q07_EDIT_VS_NATIVE', 'Q07', x, sid('Q0', p, 'LINEAR', None, a, 'NONE', h, 'SOURCE'), 'EDIT_MINUS_SOURCE_NATIVE')
    # Q08：两日测量 vs Q0（同 α / 记忆 / H）；MAX2 − MIN2；Q0 − LAGRAW1；对 Q0 HG10
    for p, a, m, h in itertools.product(P6, A_, ('NONE', 'LAG1_10'), H_):
        q0 = sid('Q0', p, 'LINEAR', None, a, m, h, 'SOURCE')
        for f in ('Q_MAX2', 'Q_MIN2', 'Q_LAGRAW1', 'Q_MEAN2'):
            add('Q08_TWO_DAY_VS_Q0', 'Q08', sid(f, p, 'LINEAR', None, a, m, h, 'SOURCE'), q0, 'TWO_DAY_MINUS_Q0')
        add('Q08_MAX2_VS_MIN2', 'Q08', sid('Q_MAX2', p, 'LINEAR', None, a, m, h, 'SOURCE'), sid('Q_MIN2', p, 'LINEAR', None, a, m, h, 'SOURCE'), 'MAX2_MINUS_MIN2')
        add('Q08_Q0_VS_LAGRAW1', 'Q08', q0, sid('Q_LAGRAW1', p, 'LINEAR', None, a, m, h, 'SOURCE'), 'Q0_MINUS_LAGRAW1')
        if m == 'NONE':
            add('Q08_TWO_DAY_VS_HG10', 'Q08', sid('Q_MAX2', p, 'LINEAR', None, a, 'NONE', h, 'SOURCE'), sid('Q0', p, 'LINEAR', None, a, 'HG10', h, 'SOURCE'),
                'MAX2_MINUS_Q0_HG10')
    # Q13：V 条件（条件 − ALL；DOWN_MIXED − UP）
    for p, side, dose, h in itertools.product(('A4b_CVRv5', 'R2', 'A06'), ('HIGH', 'LOW'), (.1, .2), H_):
        allv = sid('PARKINSON', p, 'DELETE_' + side, dose, None, 'NONE', h, 'POST_PARENT', 'ALL')
        dm = sid('PARKINSON', p, 'DELETE_' + side, dose, None, 'NONE', h, 'POST_PARENT', 'DOWN_MIXED')
        up = sid('PARKINSON', p, 'DELETE_' + side, dose, None, 'NONE', h, 'POST_PARENT', 'UP')
        add('Q13_V_COND_VS_ALL', 'Q13', dm, allv, 'DOWN_MIXED_MINUS_ALL')
        add('Q13_V_COND_VS_ALL', 'Q13', up, allv, 'UP_MINUS_ALL')
        add('Q13_V_DOWNMIXED_VS_UP', 'Q13', dm, up, 'DOWN_MIXED_MINUS_UP')
    # 附属视图：补充 384 对其 owner（Q06 / Q13）
    for _, s in S.iterrows():
        card = 'Q13' if s.diagnostic == 'V_ALL_KNOWN' else 'Q06'
        add('SUPP_VS_OWNER', card, s.supp_id, s.owner_semantic_id, s.diagnostic + '_MINUS_OWNER')
    E = pd.DataFrame(ext)
    C = pd.concat([C, E], ignore_index=True)
    C['coefficient'] = 'left(+1) − right(−1)'
    C['estimand'] = 'D_seg = 252·100·(mean_left − mean_right)，共同有限日；FULL = Σ n_s D_s / Σ n_s；G4 = 段 D 中位；同资本另列'
    C['unit'] = 'ann_pp'
    supp_ids = set(S.supp_id)
    C['left_desc_id'] = C.left.map(lambda x: did.get(x, 'SUPP:' + x[:16] if x in supp_ids else 'MISSING'))
    C['right_desc_id'] = C.right.map(lambda x: did.get(x, 'MISSING'))
    C['comparison_id'] = ['CMP%06d' % i for i in range(1, len(C) + 1)]
    return C[['comparison_id', 'view', 'card', 'kind', 'left', 'right', 'left_desc_id', 'right_desc_id', 'coefficient', 'estimand', 'unit']]
