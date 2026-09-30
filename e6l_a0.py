# -*- coding: utf-8 -*-
"""E6l A0 编译器（brief §3 / §4 ⑧–⑪ / §9；plan §9 / §9.3 / §9.3a / §12 / §13.2 / §13.4 / §16.3；附录 A6-5 / E）。不读任何收益。
独立枚举（e6l_registry）→ 与 stage0/plan_tests/out 的 spec 清单逐元组 / 块集合对账：design 34,120（含块集合）/ policy_content 9,720 /
memory_random 180 / support 432 / comparison 172,440 / audit_control 2,160。
输出 registry/：
  descriptors_E6l.csv          34,120 行：块 / 族 / 目标 / 任务 / 主展示 72 / 剂量 72 / 邻域 72 / 各比较端 ID / E6k 同构 ID（真实清单交集）/
                               暴露 / 随机登记 / 核合同（⑩）/ 记忆合同（⑨ INV 的 H 状态键）/ 状态合同（⑧）/ R-MARK 分区合同（⑪）/ 模板 v4 ⑮–⑱
  accessory_E6l.csv            审计任务 2,160（KERNEL_DOSE 432 / INV_CAP_LOOP_PAIR 1,560 / STRICT250_STATE 96 / BOUNDARY_CONT_PARENT_PAIR 72）
                               + 支持桥 432 × 3 账户（COMMON_SUPPORT 子 / 父、Q0 遮罩复制）
  comparison_manifest_E6l.csv  172,440 基础配对（SOURCE_RAW；系数 / 左右 ID / 视图 / 共同日 / 聚合 / 单位 / 源费用 / query）+ 扩展视图
                               （四账户信息 × 规则、平滑 × 规则、KERNEL_DOSE、支持桥、INV 闭环、STRICT250、连续边界）
  randoms_E6l.csv              LEGACY_POLICY_RANDOM / CONTENT_COND_ISK_P5 各 9,720；RMARK 三机制各 180
  bootstrap_comparisons_E6l.csv  CP / CN / CC1 / CB / CH / CM / CQ
  cards_E6l.csv / query_registry_E6l.csv / question_to_objects_E6l.csv / task_to_objects_E6l.csv / fixed_outputs_E6l.csv
  selection_exposure_ledger_E6l.csv（逐描述符暴露 + 已见选择史）
results/skeleton/：固定输出二十张 + 每个 query 一张空骨架（表头）；registration/a0_manifest_E6l.json。"""
import e6l_boot  # noqa: F401
import os
import sys
import json
import math

import numpy as np
import pandas as pd

import e6l_core as L
import e6l_registry as RG

SPEC_OUT = ('stage0', 'plan_tests', 'out')
KERNEL = {  # 测量 → (核 ID, 名义窗 k, 最少有效数, λ)
    'Q0': ('SOURCE_J_B1_qCC=1/(d+1e-4)', 1, 1, 1.0),
    'Q_D3': ('INV_MEAN_VALID(d,3)', 3, 2, None), 'Q_D5': ('INV_MEAN_VALID(d,5)', 5, 3, None), 'Q_D10': ('INV_MEAN_VALID(d,10)', 10, 6, None),
    'Q_QMEAN5': ('MEAN_VALID(1/(d+eps),5)', 5, 3, None), 'Q_DMED5': ('INV_MEDIAN_VALID(d,5)', 5, 3, None),
    'Q_DEW3': ('INV_EW_NORM(d,lambda=.5)', 3, 2, 0.5), 'Q_DEW5': ('INV_EW_NORM(d,lambda=1/3)', 5, 3, 1.0 / 3.0),
    'Q_RANK3': ('MEAN(SOURCE_RANK_EXTENDED,3)->RERANK', 3, 2, None), 'Q_RANK5': ('MEAN(SOURCE_RANK_EXTENDED,5)->RERANK', 5, 3, None),
    'Q_RANK10': ('MEAN(SOURCE_RANK_EXTENDED,10)->RERANK', 10, 6, None),
    'Q_RANKOBS5': ('MEAN(SOURCE_RANK_POOL0_ONLY,5)->RERANK', 5, 3, None), 'Q_RANKSCORE5': ('MEAN(SOURCE_RANK_EXTENDED,5) NO_RERANK', 5, 3, None),
    'C1': ('SOURCE_E6I_K_MA3_E6F', 3, None, None), 'S': ('SOURCE_E6I_K_rar20', 20, None, None), 'M': ('SOURCE_E6I_K_slope20', 20, None, None),
    'K0': ('SOURCE_MOTHER_K', None, None, None)}
RULES_OLD = RG.OPS[1:] + RG.MEM + RG.STATE + ('HG20', 'HG30')
CM_PAIRS = (('LAG1_10', 'HG10'), ('DECAY2_10', 'HG10'), ('DECAY5_10', 'HG10'), ('INV10', 'HG10'), ('INV10', 'LAG1_10'),
            ('DECAY2_10', 'DECAY5_10'), ('VOL_HI15', 'HG10'), ('VOL_HI5', 'HG10'), ('VOL_MEAN15', 'HG10'), ('VOL_MEAN5', 'HG10'),
            ('VOL_HI15', 'VOL_HI5'), ('VOL_MEAN15', 'VOL_MEAN5'), ('HG20', 'HG15'), ('HG30', 'HG15'), ('HG10', 'HG5'), ('HG15', 'HG10'))
KERNEL_PAIRS = (('MA_VS_EW', 'Q_D3', 'Q_DEW3', 'E6L-Q04-a'), ('MA_VS_EW', 'Q_D5', 'Q_DEW5', 'E6L-Q04-a'),
                ('MEAN_KERNEL_PAIR', 'Q_D5', 'Q_QMEAN5', 'E6L-Q03-a'), ('MEAN_KERNEL_PAIR', 'Q_D5', 'Q_DMED5', 'E6L-Q03-a'),
                ('MEAN_KERNEL_PAIR', 'Q_QMEAN5', 'Q_DMED5', 'E6L-Q03-a'),
                ('RANK_BRIDGE_PAIR', 'Q_RANK5', 'Q_RANKOBS5', 'E6L-Q05-a'), ('RANK_BRIDGE_PAIR', 'Q_RANK5', 'Q_RANKSCORE5', 'E6L-Q05-a'),
                ('WINDOW_PAIR', 'Q_D5', 'Q_D3', 'E6L-Q04-a'), ('WINDOW_PAIR', 'Q_D10', 'Q_D5', 'E6L-Q04-a'),
                ('WINDOW_PAIR', 'Q_RANK5', 'Q_RANK3', 'E6L-Q05-a'), ('WINDOW_PAIR', 'Q_RANK10', 'Q_RANK5', 'E6L-Q05-a'),
                ('SMN_PAIR', 'S', 'M', 'E6L-Q15-a'))
FIXED_TABLES = ('source_lineage', 'kernel_contracts', 'memory_contracts', 'hypothesis_lineage', 'candidate72', 'dose72', 'comparison_manifest',
                'policy_profiles', 'memory_age_daily', 'state_clock_ledger', 'turn_cost_frontier', 'risk_tight_bounds', 'random_refs',
                'mc_precision', 'completion_coverage',
                'paired_mde80_deriv', 'state_unknown_days', 'inventory_saturation', 'membership_age_ledger', 'frontier_dose_tilt')


def T(k):
    """spec 元组 → 规范元组（α float、H int）。"""
    f, p, a, h, op = k
    return (f, p, float(a), int(h), op)


def spec_sets():
    d = os.path.join(L.P(*SPEC_OUT))
    des = {T(r['id']): sorted(r['blocks']) for r in json.load(open(os.path.join(d, 'design_manifest.json')))}
    pol = sorted(T(x) for x in json.load(open(os.path.join(d, 'policy_content_manifest.json'))))
    mem = sorted(T(x) for x in json.load(open(os.path.join(d, 'memory_random_manifest.json'))))
    sup = sorted(T(x) for x in json.load(open(os.path.join(d, 'support_manifest.json'))))
    cmp_ = sorted((r['kind'], T(r['left']), T(r['right'])) for r in json.load(open(os.path.join(d, 'comparison_manifest.json'))))
    aud = sorted((r['kind'], T(r['base'])) for r in json.load(open(os.path.join(d, 'audit_control_manifest.json'))))
    return des, pol, mem, sup, cmp_, aud


def rule_text(op):
    r = __import__('e6l_ops').parse_op(op)
    if r['kind'] == 'NATIVE':
        return 'NATIVE（无记忆；源门）', 'none', 'NOT_APPLICABLE'
    if r['kind'] == 'HG':
        return 'HG b=%g：s − b·1(本账户 G_{t−1})（递归选择记忆）' % r['b'], 'recursive_gate_membership', '%g' % r['b']
    if r['kind'] == 'LAG1':
        return 'LAG1 b=%g：s − b·1(同测量同 α 无带门 U_{t−1})（非递归）' % r['b'], 'yesterday_natural_U', '%g' % r['b']
    if r['kind'] == 'DECAY':
        return 'DECAY L=%g b=%g：s − b·1(G_{t−1})·max(0, 1 − max(age−1,0)/L)，age = t − last_confirmed(U)' % (r['L'], r['b']), \
            'confirmed_decay_L%g' % r['L'], '%g' % r['b']
    if r['kind'] == 'INV':
        return 'INV b=%g：s − b·1(形成日 [T−H, T−1] 本账户最终名单批次 > 0)（按 H 独立递推）' % r['b'], 'inventory_H', '%g' % r['b']
    if r['kind'] == 'STATE':
        return 'STATE %s：HG 递归 + 逐日 b 调度（Vol3 PIT；UNKNOWN → b10）' % r['schedule'], 'recursive_gate_membership', 'SCHEDULE'
    raise ValueError(op)


def main():
    trial = '--trial' in sys.argv
    tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else ''      # 冻结前重编（旧版移入 _superseded，回执名加后缀）
    out_reg = os.path.join(L.TRIAL, 'a0', 'registry') if trial else L.P('registry')
    out_man = os.path.join(L.TRIAL, 'a0', 'a0_manifest_E6l.json') if trial else L.P('registration', 'a0_manifest_E6l.json')
    out_skel = os.path.join(L.TRIAL, 'a0', 'skeleton') if trial else L.P('results', 'skeleton')
    for d in (out_reg, os.path.dirname(out_man), out_skel):
        os.makedirs(d, exist_ok=True)
    plan_sha = L.sha_file(L.P('PLAN_COPY.md'))
    state_sha = L.sha_file(os.path.join(L.CODE, 'e6l_state.py'))
    # ================================================================ 对账
    mine = RG.compile_design()
    keys = sorted(mine)
    kset = set(keys)
    des, pol, mem, sup, cmp_spec, aud_spec = spec_sets()
    cmp_mine = RG.comparison_base(keys)
    aud_mine = sorted(RG.audit_controls(keys))
    compare = dict(
        design_only_mine=len(kset - set(des)), design_only_spec=len(set(des) - kset),
        design_block_diffs=int(sum(1 for k in keys if k in des and sorted(mine[k]) != des[k])),
        policy_content_equal=sorted(RG.random_content_ids(keys)) == pol, memory_random_equal=sorted(RG.random_memory_ids(keys)) == mem,
        support_equal=sorted(RG.kernel_support_ids(keys)) == sup, comparison_equal=cmp_mine == cmp_spec,
        audit_control_equal=aud_mine == aud_spec)
    counts_expected = dict(design=34120, policy_content=9720, memory_random=180, support=432, comparison=172440, audit=2160)
    counts_mine = dict(design=len(keys), policy_content=len(pol), memory_random=len(mem), support=len(sup), comparison=len(cmp_mine), audit=len(aud_mine))
    cmp_ok = (compare['design_only_mine'] == 0 and compare['design_only_spec'] == 0 and compare['design_block_diffs'] == 0
              and all(compare[k] for k in ('policy_content_equal', 'memory_random_equal', 'support_equal', 'comparison_equal', 'audit_control_equal'))
              and counts_mine == counts_expected)
    # ================================================================ 描述符表
    e6k = set(pd.read_csv(L.K6('registry', 'descriptors_E6k.csv'), usecols=['desc_id']).desc_id)
    prim = set(RG.primary_ids(0.25))
    dose = set(RG.primary_ids(0.5))
    nbhd = set(RG.primary_ids(0.125))
    rset = set(RG.random_content_ids(keys))
    mset = set(RG.random_memory_ids(keys))
    sset = set(RG.kernel_support_ids(keys))
    s250 = set(k for kind, k in aud_mine if kind == 'STRICT250_STATE')
    recipe_of = {(f, op): '%s:%s' % (f, op) for f, op in RG.RECIPES}
    rows = []
    for k in keys:
        f, p, a, h, op = k
        did = RG.desc_id(k)
        fam = RG.family_of(k)
        eq = RG.e6k_equiv(k)
        eq = eq if (eq is not None and eq in e6k) else ''
        if fam == 'PARENT':
            expo = 'SOURCE_PARENT'
        elif eq:
            expo = L.LABEL_SECOND
        else:
            expo = L.LABEL_FIRST_LOOK
        new_op = expo == L.LABEL_FIRST_LOOK

        def ref(kk):
            return RG.desc_id(kk) if (kk in kset and kk != k) else ''
        par = RG.desc_id(('K0', p, 0.0, h, 'NATIVE'))
        native = ref((f, p, a, h, 'NATIVE')) if (f != 'K0' and op != 'NATIVE') else ''
        c1 = ref(('C1', p, a, h, op)) if f not in ('K0', 'C1') else ''
        q0 = ref(('Q0', p, a, h, op)) if f not in ('K0', 'Q0') else ''
        qhg = ref(('Q0', p, a, h, 'HG10')) if f != 'K0' else ''
        only = ref(('K0', p, 0.0, h, op)) if (f != 'K0' and op != 'NATIVE') else ''
        kid, kw, kmin, lam = KERNEL['K0' if f == 'K0' else f]
        rtext, mem_kind, bpts = rule_text(op)
        is_state = op in RG.STATE
        rnd = 'LEGACY+COND' if k in rset else ('NO_NEW_CONTENT_TO_PERMUTE' if f == 'K0' else 'RANDOM_NOT_SCHEDULED')
        acct15 = ('Y00=parent|Y10=%s NATIVE|Y01=K0 %s|Y11=self（gross / 线性费用 / 冲击 / 资本 / 换手分列）' % (f, op)) if (f != 'K0' and op != 'NATIVE') \
            else ('child−parent（gross / 线性费用 / 冲击 / 资本 / 换手分列）' if f != 'K0' or op != 'NATIVE' else 'SOURCE_PARENT')
        meas_win = ('%dd' % kw) if kw else 'source'
        dec_win = {'none': 'same_day', 'recursive_gate_membership': 'recursive(unbounded)', 'yesterday_natural_U': '1d_nonrecursive',
                   'inventory_H': 'H=%d_inventory' % h}.get(mem_kind, mem_kind)
        rows.append(dict(
            desc_id=did, meas=f, mother=p, alpha=a, H=h, op=op, blocks='|'.join(mine[k]), family=fam, target_id=RG.target_of(k), task=RG.task_of(k),
            primary72=k in prim, dose72=k in dose, nbhd72=k in nbhd, recipe=recipe_of.get((f, op), 'NOT_APPLICABLE') if (k in prim or k in dose or k in nbhd) else 'NOT_APPLICABLE',
            parent_desc=par if fam != 'PARENT' else 'NOT_APPLICABLE', native_desc=native or 'NOT_APPLICABLE', c1_desc=c1 or 'NOT_APPLICABLE',
            q0_desc=q0 or 'NOT_APPLICABLE', qhg10_desc=qhg or 'NOT_APPLICABLE', rule_only_desc=only or 'NOT_APPLICABLE',
            e6k_equiv=eq or 'NOT_APPLICABLE', evidence_exposure=expo, new_operator=new_op,
            replacement_preference_status='NOT_AUTHORIZED' if new_op else 'NOT_APPLICABLE', deployment_authorized=False, policy_provisional=False,
            random_content=rnd, rmark=k in mset, kernel_support=k in sset, strict250=k in s250, inv_loop=op == 'INV10', boundary_cont=k in prim,
            kernel_id=kid, kernel_window=kw if kw else 'NOT_APPLICABLE', kernel_min_valid=kmin if kmin else 'NOT_APPLICABLE',
            kernel_lambda=('%.12g' % lam) if lam is not None else 'NOT_APPLICABLE',
            memory_rule=rtext, memory_kind=mem_kind, b_points=bpts, inv_state_key=('H%d' % h) if op == 'INV10' else 'NOT_APPLICABLE',
            state_var='Vol3' if is_state else 'NOT_APPLICABLE', state_def_sha256=state_sha if is_state else 'NOT_APPLICABLE',
            unknown_fallback='b10' if is_state else 'NOT_APPLICABLE',
            rmark_partition=('UNIFORM_IID(全门域一组；逐日 u)|UNIFORM_P5(全门域一组；绝对日 // 5 块 u)|ISK_P5(行业 > 旧K3 > size3 回退树叶；块 5)')
            if k in mset else 'NOT_APPLICABLE',
            t15_account=acct15, t16_timescale='meas=%s|decision=%s|H=%d' % (meas_win, dec_win, h),
            t17_random='LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5' + ('+RMARK×3' if k in mset else '') if k in rset
            else ('RMARK×3' if k in mset else rnd),
            t18_state=('Vol3 四调度（UNKNOWN→b10；STRICT250 对照）' if is_state else ('三时钟账本（形成 / 日历 / 交易）' if k in prim else 'NOT_APPLICABLE')),
            fixed_weights=bool(k in prim or k in dose or (f == 'K0' and h == 5) or (f == 'C1' and a == 0.25 and h == 5 and op in ('NATIVE', 'HG10'))),
            shadow=bool(k in prim or k in dose or (f == 'K0' and h == 5 and op != 'NATIVE') or (f in ('Q0', 'C1') and a == 0.25 and h == 5 and op in ('NATIVE', 'HG10')))))
    D = pd.DataFrame(rows)
    # ================================================================ 附属
    acc = []
    for kind, k in aud_mine:
        f, p, a, h, op = k
        did = RG.desc_id(k)
        tag = {'KERNEL_DOSE': 'KD', 'INV_CAP_LOOP_PAIR': 'ICL', 'STRICT250_STATE': 'S250', 'BOUNDARY_CONT_PARENT_PAIR': 'BCP'}[kind]
        task = RG.task_of(k) if kind != 'BOUNDARY_CONT_PARENT_PAIR' else 'CONT|%s' % p
        cmpto = {'KERNEL_DOSE': did, 'INV_CAP_LOOP_PAIR': 'ICLPAR|' + did, 'STRICT250_STATE': did,
                 'BOUNDARY_CONT_PARENT_PAIR': 'BCPPAR|' + did}[kind]
        acc.append(dict(acc_id='%s|%s' % (tag, did), kind=kind, base_desc=did, meas=f, mother=p, alpha=a, H=h, op=op, task=task, compare_to=cmpto,
                        view={'KERNEL_DOSE': 'DOSE_MATCHED_MEAN_RMS', 'INV_CAP_LOOP_PAIR': 'MATCH_CAP_INV_LOOP', 'STRICT250_STATE': 'STRICT250',
                              'BOUNDARY_CONT_PARENT_PAIR': 'CONTINUOUS'}[kind]))
        if kind == 'INV_CAP_LOOP_PAIR':
            acc.append(dict(acc_id='ICLPAR|%s' % did, kind='INV_CAP_LOOP_PARENT', base_desc=did, meas='K0', mother=p, alpha=0.0, H=h, op='NATIVE',
                            task=task, compare_to=RG.desc_id(('K0', p, 0.0, h, 'NATIVE')), view='MATCH_CAP_INV_LOOP'))
        if kind == 'BOUNDARY_CONT_PARENT_PAIR':
            acc.append(dict(acc_id='BCPPAR|%s' % did, kind='BOUNDARY_CONT_PARENT', base_desc=did, meas='K0', mother=p, alpha=0.0, H=h, op='NATIVE',
                            task=task, compare_to=RG.desc_id(('K0', p, 0.0, h, 'NATIVE')), view='CONTINUOUS'))
    for k in sorted(sset):
        f, p, a, h, op = k
        did = RG.desc_id(k)
        q0 = RG.desc_id(('Q0', p, a, h, op))
        for tag, kind, cmpto in (('CSC', 'SUPPORT_CS_CHILD', 'CSP|' + did), ('CSP', 'SUPPORT_CS_PARENT', q0), ('MQ0', 'SUPPORT_MASKQ0', q0)):
            acc.append(dict(acc_id='%s|%s' % (tag, did), kind=kind, base_desc=did, meas=f, mother=p, alpha=a, H=h, op=op, task=RG.task_of(k),
                            compare_to=cmpto, view={'SUPPORT_CS_CHILD': 'COMMON_SUPPORT', 'SUPPORT_CS_PARENT': 'COMMON_SUPPORT',
                                                    'SUPPORT_MASKQ0': 'Q0_MASKED_TO_CHILD_SUPPORT'}[kind]))
    A = pd.DataFrame(acc)
    # ================================================================ 比较清单
    card_of_kind = {'PARENT': 'E6L-Q01-b', 'SAME_MEAS_NATIVE': 'E6L-Q02-a', 'SAME_OPERATOR_C1': 'E6L-Q15-a', 'SAME_OPERATOR_Q0': 'E6L-Q03-a',
                    'KNOWN_QHG10': 'E6L-Q09-a', 'RULE_ONLY': 'E6L-Q02-a'}
    cm = []
    for i, (kind, left, right) in enumerate(cmp_mine):
        cm.append(dict(cmp_id='B%06d' % i, kind=kind, view='SOURCE_RAW', left_id=RG.desc_id(left), right_id=RG.desc_id(right), coef='+1|-1',
                       terms='%s|%s' % (RG.desc_id(left), RG.desc_id(right)), time_support='COMMON_PAIRED_DATES',
                       aggregation='segment_D=252·100·mean_common(left−right); FULL=n-weighted mean of segment D; G4=median of 4 segment D',
                       unit='ann_pp_net8', cost='source_8bp_charged_turn', query_id=card_of_kind[kind]))
    ext = []
    n = 0

    def add(kind, view, terms, coefs, q):
        nonlocal n
        ext.append(dict(cmp_id='X%06d' % n, kind=kind, view=view, left_id=terms[0], right_id=terms[1] if len(terms) > 1 else 'NOT_APPLICABLE',
                        coef='|'.join('%+d' % c for c in coefs), terms='|'.join(terms), time_support='COMMON_PAIRED_DATES',
                        aggregation='daily closure first; then segment_D / FULL(n-weighted) / G4(median)', unit='ann_pp_net8',
                        cost='source_8bp_charged_turn', query_id=q))
        n += 1
    for k in keys:
        f, p, a, h, op = k
        if f == 'K0' or op == 'NATIVE':
            continue
        y00 = RG.desc_id(('K0', p, 0.0, h, 'NATIVE'))
        y10 = RG.desc_id((f, p, a, h, 'NATIVE'))
        y01k = ('K0', p, 0.0, h, op)
        if y01k in kset:
            add('FOUR_ACCOUNT_INFO_RULE', 'SOURCE_RAW', [RG.desc_id(k), y10, RG.desc_id(y01k), y00], [1, -1, -1, 1], 'E6L-Q02-a')
        if f != 'Q0' and f.startswith('Q') and ('Q0', p, a, h, op) in kset:
            add('FOUR_ACCOUNT_SMOOTH_RULE', 'SOURCE_RAW', [RG.desc_id(k), y10, RG.desc_id(('Q0', p, a, h, op)), RG.desc_id(('Q0', p, a, h, 'NATIVE'))],
                [1, -1, -1, 1], 'E6L-Q09-a')
    for k in keys:
        f, p, a, h, op = k
        for x, y in CM_PAIRS:
            if op == x and (f, p, a, h, y) in kset:
                add('MECHANISM_PAIR', 'SOURCE_RAW', [RG.desc_id(k), RG.desc_id((f, p, a, h, y))], [1, -1],
                    {'LAG1_10': 'E6L-Q06-a', 'DECAY2_10': 'E6L-Q07-a', 'DECAY5_10': 'E6L-Q07-a', 'INV10': 'E6L-Q08-a'}.get(x, 'E6L-Q12-a' if x.startswith('VOL') else 'E6L-Q11-a'))
        for kind, x, y, q in KERNEL_PAIRS:                    # 同 α / H / 算子的测量核配对（卡 Q03 / Q04 / Q05 绑定；A1-auto 首跑拦下 Q04 无绑定）
            if f == x and (y, p, a, h, op) in kset:
                add(kind, 'SOURCE_RAW', [RG.desc_id(k), RG.desc_id((y, p, a, h, op))], [1, -1], q)
    for r in A.itertuples():
        if r.kind == 'KERNEL_DOSE':
            add('KERNEL_DOSE', 'DOSE_MATCHED_MEAN_RMS', [r.base_desc, r.acc_id], [1, -1], 'E6L-Q03-b')
        elif r.kind == 'SUPPORT_CS_CHILD':
            q0 = RG.desc_id(('Q0', r.mother, r.alpha, r.H, r.op))
            add('SUPPORT_BRIDGE_CONTENT', 'COMMON_SUPPORT', [r.acc_id, 'CSP|' + r.base_desc], [1, -1], 'E6L-Q05-b')
            add('SUPPORT_BRIDGE_PARENT_SUPPORT', 'COMMON_SUPPORT', ['CSP|' + r.base_desc, q0], [1, -1], 'E6L-Q05-b')
            add('SUPPORT_BRIDGE_CHILD_SUPPORT', 'COMMON_SUPPORT', [r.base_desc, r.acc_id], [1, -1], 'E6L-Q05-b')
            add('MASKQ0_SUPPORT_ONLY', 'Q0_MASKED_TO_CHILD_SUPPORT', ['MQ0|' + r.base_desc, q0], [1, -1], 'E6L-Q05-b')
            add('MASKQ0_CONTENT', 'Q0_MASKED_TO_CHILD_SUPPORT', [r.base_desc, 'MQ0|' + r.base_desc], [1, -1], 'E6L-Q05-b')
        elif r.kind == 'INV_CAP_LOOP_PAIR':
            add('INV_CAP_LOOP', 'MATCH_CAP_INV_LOOP', [r.acc_id, 'ICLPAR|' + r.base_desc], [1, -1], 'E6L-Q08-b')
        elif r.kind == 'STRICT250_STATE':
            add('STRICT250_VS_MAIN', 'STRICT250', [r.acc_id, r.base_desc], [1, -1], 'E6L-Q13-a')
        elif r.kind == 'BOUNDARY_CONT_PARENT_PAIR':
            add('CONTINUOUS_CHILD_PARENT', 'CONTINUOUS', [r.acc_id, 'BCPPAR|' + r.base_desc], [1, -1], 'E6L-Q13-b')
    for k in sorted(rset):                                    # 真实 − 随机参照（路径均值；随机登记同 ID；A1-auto 首跑拦下 Q10 无绑定）
        add('REAL_MINUS_LEGACY', 'RANDOM_PATH_MEAN', [RG.desc_id(k), 'LEGACY_POLICY_RANDOM|' + RG.desc_id(k)], [1, -1], 'E6L-Q01-b')
        add('REAL_MINUS_COND', 'RANDOM_PATH_MEAN', [RG.desc_id(k), 'CONTENT_COND_ISK_P5|' + RG.desc_id(k)], [1, -1], 'E6L-Q10-a')
    for k in sorted(mset):
        for mech in RG.RMARK:
            add('REAL_MINUS_RMARK', 'RANDOM_PATH_MEAN', [RG.desc_id(k), '%s|%s' % (mech, RG.desc_id(k))], [1, -1], 'E6L-Q10-a')
    for k in keys:                                            # 同资本（源政策 FULL_sc）视图：全部子 − 父
        f, p, a, h, op = k
        if RG.family_of(k) != 'PARENT':
            add('MATCH_CAP_FIXED_PATH', 'MATCH_CAP_FIXED_PATH', [RG.desc_id(k), RG.desc_id(('K0', p, 0.0, h, 'NATIVE'))], [1, -1], 'E6L-Q14-a')
    CM = pd.DataFrame(cm + ext)
    # ================================================================ 随机登记
    R = []
    for k in sorted(rset):
        f, p, a, h, op = k
        for mech in RG.POLICY_MECHS:
            R.append(dict(random_id='%s|%s' % (mech, RG.desc_id(k)), mechanism=mech, desc_id=RG.desc_id(k), meas=f, mother=p, alpha=a, H=h, op=op,
                          target_id=RG.target_of(k), rtask='%s|%s' % (mech, f), n_paths_initial=1024, topup=512, cap=8192,
                          injection='after smoothing / neutralization / direction; before rule (LEGACY: E6k Legacy key; new measures mid = E6l.<meas>)'
                          if mech == 'LEGACY_POLICY_RANDOM' else 'ISK tree (industry > old K3 > size3), P5 absolute-date blocks; key E6k.NEW namespace'))
    for k in sorted(mset):
        f, p, a, h, op = k
        for mech in RG.RMARK:
            R.append(dict(random_id='%s|%s' % (mech, RG.desc_id(k)), mechanism=mech, desc_id=RG.desc_id(k), meas=f, mother=p, alpha=a, H=h, op=op,
                          target_id=RG.target_of(k), rtask='%s|%s' % (mech, f), n_paths_initial=1024, topup=512, cap=8192,
                          injection='own-path G_{t−1} marks permuted within partition (count-preserving); real content'))
    RR = pd.DataFrame(R)
    # ================================================================ bootstrap 比较族
    B = []
    for r in D.itertuples():
        if r.family == 'PARENT':
            continue
        B.append(dict(comparison_id='CP|' + r.desc_id, family='child_minus_parent', a=r.desc_id, b=r.parent_desc))
        for pre, fam, other in (('CN', 'minus_same_meas_native', r.native_desc), ('CC1', 'minus_same_op_C1', r.c1_desc),
                                ('CB', 'minus_same_op_Q0', r.q0_desc), ('CH', 'minus_rule_only', r.rule_only_desc), ('CQ', 'minus_Q0_HG10', r.qhg10_desc)):
            if other != 'NOT_APPLICABLE':
                B.append(dict(comparison_id='%s|%s' % (pre, r.desc_id), family=fam, a=r.desc_id, b=other))
    for e in ext:
        if e['kind'] in ('MECHANISM_PAIR', 'MA_VS_EW', 'MEAN_KERNEL_PAIR', 'RANK_BRIDGE_PAIR', 'WINDOW_PAIR', 'SMN_PAIR'):
            B.append(dict(comparison_id='CM|%s|%s' % (e['left_id'], e['right_id']), family='mechanism_pair' if e['kind'] == 'MECHANISM_PAIR'
                          else 'kernel_pair_' + e['kind'].lower(), a=e['left_id'], b=e['right_id']))
    BB = pd.DataFrame(B)
    # ================================================================ 16 卡 + query
    plan = open(L.P('PLAN_COPY.md'), encoding='utf-8').read().split('\n')
    card_line = {}
    for i, ln in enumerate(plan):
        if ln.startswith('### E6L-Q'):
            card_line[ln[len('### E6L-'):len('### E6L-') + 3]] = i + 1
    CARD_Q = {
        'Q01': [('a', 'E6k 同构对象逐值复现（D 段 / n / D_sc / FULL / G4 vs policy_E6k）', "e6k_equiv != 'NOT_APPLICABLE'"),
                ('b', 'Q0 × NATIVE / HG5 / HG10 / HG15 各 α / H 的正式尺子（PORT3_T 主列）与四段 lo / hi', "meas=='Q0' & op.isin(['NATIVE','HG5','HG10','HG15'])"),
                ('c', 'W09：Q0|A4b_CVRv5|a0.5|H5|HG10 四段组合层 lo_T / hi_T 追查', "desc_id=='Q0|A4b_CVRv5|a0.5|H5|HG10'")],
        'Q02': [('a', '信息 × 规则四账户（Y00 / Y10 / Y01 / Y11）gross / 线性费用 / 冲击 / 资本 / 换手分列', "family.isin(['HG','MEMORY','STATE']) & meas!='K0'"),
                ('b', '零费敏感（gross 差）与规则 ONLY（旧 K）账户', "meas=='K0' & family=='OLD_RULE'")],
        'Q03': [('a', 'Q_D5 / Q_QMEAN5 / Q_DMED5 / Q0 同 α / H / 算子；ε 主导份额；名单差', "meas.isin(['Q0','Q_D5','Q_QMEAN5','Q_DMED5'])"),
                ('b', 'KERNEL_DOSE（同均值 / RMS 控制）vs 平滑账户（432 支持格）', 'kernel_support')],
        'Q04': [('a', 'D3 vs DEW3、D5 vs DEW5（同 α / H / 算子）', "meas.isin(['Q_D3','Q_DEW3','Q_D5','Q_DEW5'])"),
                ('b', 'EW 有效权重 / 平均年龄与有效数份额（测量事实）', "meas.isin(['Q_DEW3','Q_DEW5'])")],
        'Q05': [('a', 'RANK5 vs RANKOBS5 vs RANKSCORE5', "meas.isin(['Q_RANK5','Q_RANKOBS5','Q_RANKSCORE5'])"),
                ('b', '支持桥（COMMON_SUPPORT 子 / 父、Q0 遮罩）与延伸覆盖', 'kernel_support')],
        'Q06': [('a', 'HG10 vs LAG1_10 vs NATIVE（Q0 / Q_D5 / Q_RANK5 / C1）', "op.isin(['HG10','LAG1_10','NATIVE']) & meas.isin(['Q0','Q_D5','Q_RANK5','C1'])"),
                ('b', '记忆年龄分布（membership_age_ledger）', "op.isin(['HG10','LAG1_10'])")],
        'Q07': [('a', 'DECAY2 / DECAY5 vs HG10 vs NATIVE', "op.isin(['DECAY2_10','DECAY5_10','HG10','NATIVE']) & meas.isin(['Q0','Q_D5','Q_RANK5','C1','K0'])"),
                ('b', '纯 bonus 连续依靠日数 / 重确认年龄', "op.isin(['DECAY2_10','DECAY5_10','HG10'])")],
        'Q08': [('a', 'INV10 vs HG10 vs LAG1 与 INV_ONLY（H 剖面）', "op.isin(['INV10','HG10','LAG1_10'])"),
                ('b', '库存覆盖 / 饱和、INV_CAP_LOOP_PAIR vs FIXED_PATH', "op=='INV10'")],
        'Q09': [('a', '平滑 × 规则四账户（Q0 NATIVE / Qs NATIVE / Q0 HG / Qs HG）', "meas.str.startswith('Q_') & family=='HG'")],
        'Q10': [('a', '真实 HG10 − R-MARK 三机制（gross / 费用分列）', 'rmark'),
                ('b', '标记保持率 / 可移动资本 / 熵', 'rmark')],
        'Q11': [('a', '剂量面板 α .125 / .25 / .5 × b 5 / 10 / 15 / 20 / 30 与正式紧区间；frontier_dose_tilt', "op.isin(['HG5','HG10','HG15','HG20','HG30','NATIVE']) & H==5")],
        'Q12': [('a', '四调度 vs 固定 HG5 / 10 / 15（同测量 / α / H）', "family=='STATE' | op.isin(['HG5','HG10','HG15'])"),
                ('b', 'H_noise / H_change 切片（形成状态 gross；state_clock_ledger）', "family=='STATE'")],
        'Q13': [('a', '三时钟、UNKNOWN、状态贡献加回 FULL、对称分解、STRICT250 对照', "family=='STATE' | primary72"),
                ('b', '两压力窗口（2015-06-15 / 2024-09-24 起 40 交易日）与连续边界', 'primary72')],
        'Q14': [('a', 'Munion FULL vs FULL_sc（FIXED_PATH）+ INV_LOOP 诊断 + CAP 同单位', "mother.str.startswith('M_union')")],
        'Q15': [('a', 'S / M / C1 × NATIVE / HG10 同 α / H；rank ACF 与门重叠', "meas.isin(['S','M','C1']) & op.isin(['NATIVE','HG10'])")],
        'Q16': [('a', 'hypothesis_lineage 完整性与固定输出清单逐项', 'ALL')],
    }
    cards, queries, q2o = [], [], []
    for q, qs in CARD_Q.items():
        ln = card_line[q]
        head = plan[ln - 1]
        body = plan[ln]
        qids = []
        for suf, subj, filt in qs:
            qid = 'E6L-%s-%s' % (q, suf)
            qids.append(qid)
            queries.append(dict(query_id=qid, card=q, subject=subj, object_filter=filt,
                                unit='ann_pp（日配对均值 × 252 × 100）；size 为 pct_pt；费用 decimal 另列',
                                dates='推导段 2010-01-04..2018-12-28；后段 2019-01-02..2026-03-27（授权后）；四段分列 + FULL / G4',
                                table='results/full/%s.csv' % qid.replace('-', '_')))
            ids = ['ALL_DESCRIPTORS'] if filt == 'ALL' else D.query(filt, engine='python').desc_id.tolist()
            q2o += [dict(query_id=qid, desc_id=x) for x in ids]
        cards.append(dict(card=q, plan_line=ln, title=head.replace('### ', ''), text=body, queries='|'.join(qids), plan_sha256=plan_sha))
    C = pd.DataFrame(cards)
    Qy = pd.DataFrame(queries)
    Q2O = pd.DataFrame(q2o)
    T2O = pd.concat([D[['task', 'desc_id']], A[['task', 'acc_id']].rename(columns={'acc_id': 'desc_id'})], ignore_index=True)
    # ================================================================ 暴露台账（已见选择史）
    X = D[['desc_id', 'evidence_exposure', 'e6k_equiv']].copy()
    X['seen_history'] = np.where(X.e6k_equiv != 'NOT_APPLICABLE', 'E6k policy_E6k.csv 同 desc_id（四段 D / FULL / G4 已读）', 'NOT_APPLICABLE')
    notes = {'Q0|A4b_CVRv5|a0.5|H5|HG10': 'W09 已见：四段组合层 lo_T / hi_T −4.018 / −5.176 / −2.806…−2.804 / −5.676（E6k；PORT3_T FAIL）',
             'Q0|A4b_CVRv5|a0.5|H5|NATIVE': 'W09 已见：四段 lo_T / hi_T −0.913 / −1.669 / +0.286 / −2.485（E6k）',
             'Q0|A4b_CVRv5|a0.25|H5|HG10': 'W08 / W09 已见：D 四段 .406365 / .780853 / .362650 / .644916；FULL .517601；FULL_sc .485757',
             'Q0|A4b_CVRv5|a0.25|H5|NATIVE': 'W08 已见：D 四段 .329105 / .735040 / .152763 / .245640；FULL .363769；FULL_sc .345993',
             'K0|A4b_CVRv5|a0|H5|HG10': 'W08 已见：HG_ONLY10 D 四段 .189921 / .322932 / −.066850 / .015769；FULL .119983',
             'Q0|M_union3_v2_CVRv5|a0.25|H5|HG10': 'W08 已见：D 四段 .237350 / .667346 / .643610 / .730216；FULL .535706；FULL_sc .205062'}
    X['selection_note'] = X.desc_id.map(notes).fillna('NOT_APPLICABLE')
    X.loc[X.desc_id.str.startswith('Q0|') & X.desc_id.str.contains(r'\|H(?:1|5|20)\|(?:NATIVE|HG10)$'), 'selection_note'] = X.selection_note.where(
        X.selection_note != 'NOT_APPLICABLE', 'E6k 事后已见 Q 的 H 剖面（NATIVE H1 .89 / H5 .36 / H20 .25；HG10 1.51 / .52 / .32）')
    # ================================================================ 固定输出骨架
    fx = []
    heads = {
        'source_lineage': 'object_id|source_function|source_file|source_sha256|call_site|default|evidence',
        'kernel_contracts': 'meas|kernel_id|window|min_valid|lambda|valid_share_pool0|kf_finite_share|segment|query_id',
        'memory_contracts': 'op|rule|memory_kind|b_points|state_key|checkpoint_fields|query_id',
        'hypothesis_lineage': 'claim_id|author_role|exact_text|source_sha|source_section|status|brief_id|executed_test_id|outcome_query|exposure',
        'candidate72': 'desc_id|recipe|mother|FULL_ann_pp|G4_ann_pp|FULL_sc_ann_pp|policy_PORT3_T|query_id',
        'dose72': 'desc_id|recipe|mother|alpha|FULL_ann_pp|G4_ann_pp|policy_PORT3_T|query_id',
        'comparison_manifest': 'cmp_id|kind|view|left_id|right_id|coef|terms|time_support|aggregation|unit|cost|query_id',
        'policy_profiles': 'desc_id|profile|aggregation|verdict|query_id',
        'memory_age_daily': 'segment|target_id|date|reliant_share|reliant_run_p50|confirm_age_p50|query_id',
        'state_clock_ledger': 'segment|desc_id|clock|state|days|contribution_ann_pp|conditional_mean_ann_pp|query_id',
        'turn_cost_frontier': 'segment|desc_id|gross_ann_pp|charged_turn_decimal|net8_ann_pp|c_star_bp|query_id',
        'risk_tight_bounds': 'segment|desc_id|port_size_lo_T_pct_pt|port_size_hi_T_pct_pt|status|query_id',
        'random_refs': 'segment|desc_id|H|mechanism|n_paths|rand_mean_ann_pp|rand_sd_ann_pp|mcse_ann_pp|real_minus_rand_ann_pp|query_id',
        'mc_precision': 'segment|rtask|mechanism|n_paths|worst_mcse_ann_pp|target_mcse_ann_pp|status|query_id',
        'completion_coverage': 'block|registered|computed|status|query_id',
        'paired_mde80_deriv': 'cmp_id|left_id|right_id|segment|se_H_ann_pp|mde80_ann_pp|n_days|query_id',
        'state_unknown_days': 'segment|variable|definition|unknown_days|defined_days|query_id',
        'inventory_saturation': 'segment|target_id|H|mark_coverage|saturated_day_share|query_id',
        'membership_age_ledger': 'segment|target_id|age_bucket|cells|share|query_id',
        'frontier_dose_tilt': 'segment|recipe|mother|alpha|b|FULL_ann_pp|port_size_mid_T_pct_pt|query_id'}
    for nm in FIXED_TABLES:
        p = os.path.join(out_skel, '%s.csv' % nm)
        L.atomic_write_text(p, heads[nm].replace('|', ',') + '\n')
        fx.append(dict(table=nm, skeleton=L.rel(p) if not trial else p, final='results/full/%s.csv' % nm, status='SKELETON',
                       source='plan §13.4' if FIXED_TABLES.index(nm) < 15 else 'brief §9 追加'))
    for r in Qy.itertuples():
        p = os.path.join(out_skel, '%s.csv' % r.query_id.replace('-', '_'))
        L.atomic_write_text(p, 'query_id,desc_id,segment,metric,value,unit,aggregation,support\n')
    FX = pd.DataFrame(fx)
    # ================================================================ 写出
    paths = {}
    for nm, df in (('descriptors_E6l.csv', D), ('accessory_E6l.csv', A), ('comparison_manifest_E6l.csv', CM), ('randoms_E6l.csv', RR),
                   ('bootstrap_comparisons_E6l.csv', BB), ('cards_E6l.csv', C), ('query_registry_E6l.csv', Qy),
                   ('question_to_objects_E6l.csv', Q2O), ('task_to_objects_E6l.csv', T2O), ('fixed_outputs_E6l.csv', FX),
                   ('selection_exposure_ledger_E6l.csv', X)):
        p = os.path.join(out_reg, nm)
        L.atomic_write_csv(p, df)
        paths[nm] = L.sha_file(p)
    blocks = {}
    for b in ('CORE', 'CONTROL', 'MEMORY', 'STATE', 'OLD_RULE', 'BRIDGE', 'EDGE', 'EDGE_OLD', 'PARENT'):
        blocks[b] = int(sum(1 for k in keys if b in mine[k]))
    counts = dict(raw_id_count=len(D), block_counts=blocks, primary72=int(D.primary72.sum()), dose72=int(D.dose72.sum()), nbhd72=int(D.nbhd72.sum()),
                  targets=int(D.target_id.nunique()), tasks=int(D.task.nunique()),
                  accessory=A.kind.value_counts().to_dict(), audit_tasks=len(aud_mine), support_ids=len(sset),
                  comparisons_base=len(cm), comparisons_extended=len(ext), comparison_kinds=CM.kind.value_counts().to_dict(),
                  randoms=RR.mechanism.value_counts().to_dict(), bootstrap=BB.family.value_counts().to_dict(),
                  exposure=D.evidence_exposure.value_counts().to_dict(), e6k_isomorphic=int((D.e6k_equiv != 'NOT_APPLICABLE').sum()),
                  cards=len(C), queries=len(Qy), fixed_tables=len(FX), measurements=sorted(D.meas.unique()), operators=sorted(D.op.unique()))
    man = dict(written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), version=L.VERSION, plan_sha256=plan_sha,
               spec_script_sha256=L.sha_file(L.P('stage0', 'plan_tests', 'e6l_spec_tests.py')), state_def_sha256=state_sha,
               compare=dict(ok=bool(cmp_ok), **compare, counts=counts_mine, expected=counts_expected), counts=counts, registry_sha256=paths)
    L.atomic_write_json(out_man, man)
    print(json.dumps(man['compare'], ensure_ascii=False), flush=True)
    print(json.dumps({k: v for k, v in counts.items() if k not in ('measurements', 'operators')}, ensure_ascii=False), flush=True)
    if not trial:
        L.write_receipt('a0_compile' + ('_' + tag if tag else ''), [out_man] + [os.path.join(out_reg, n) for n in paths], 'SUCCEEDED' if cmp_ok else 'FAILED',
                        compare_ok=bool(cmp_ok), raw_id_count=len(D))
    return 0 if cmp_ok else 2


if __name__ == '__main__':
    sys.exit(main())
