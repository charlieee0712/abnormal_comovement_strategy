# -*- coding: utf-8 -*-
"""E6n A0 登记编译（brief §3、附录 S1；plan 附录 A / B、§6.4a、§6.5、§7.1、§10、§13.1）。不读收益与行情。
以 plan 附录 B 参考编译器（结果目录 stage0/plan_tests/e6n_spec_tests.py，sha 14c3991f）为坐标真值重编：主 3,784 / 附属 6,984 / 主展示 72 /
MATCHED_COMPONENT 414 / COMPONENT_DOSE 864 / 直接比较 2,178，Spec.key() 集合与 registry_sha256 必须与参考输出相同（不等即停）；
在其上加真实源 ID、测量输入变体、政策归属、随机绑定、暴露标签与输出 schema。卡片 / 断言 / CC 携带表的文本逐字取自结果目录 PLAN_COPY.md。
输出 registry/*_E6n.csv、registration/a0_counts_E6n.json；回执 E6n_a0。"""
import os
import re
import sys
import json
import time
import hashlib
import importlib.util
from dataclasses import asdict

import pandas as pd

import e6n_core as N

FACETS = ('PL_REL20', 'TAIL_PUSH', 'TAIL_VOL_REL20', 'JSD_PROFILE20', 'RV_REL20')
ADAPTED = ('Q_PATH', 'Q_CLOSE_THIN')
RAW_CONTROLS = ('Q_RV', 'Q_RANGE', 'Q_CLOSE_LEVEL')
RAW_ALL = ADAPTED + RAW_CONTROLS + ('Q_BOTH',)
BRIDGES = ('K_RANGE_SOURCE', 'CLV20_SOURCE')
SUPPORT_OWNER = {'Q_RV': 'Q_PATH', 'Q_RANGE': 'Q_PATH', 'Q_CLOSE_LEVEL': 'Q_CLOSE_THIN'}
MAIN_PARENT = 'A4b_CVRv5'
SEGS = N.SEGMENTS


def ref():
    p = N.P('stage0', 'plan_tests', 'e6n_spec_tests.py')
    exp = [ln.split()[0] for ln in open(N.P('handoff_in', 'exec_briefs', 'E6n_HANDOFF_SHA256.txt'), encoding='utf-8')
           if ln.strip().endswith('exec_briefs/plans/e6n_spec_tests.py')]
    if len(exp) != 1 or N.sha_file(p) != exp[0]:
        raise RuntimeError('参考编译器 sha 不符（交接清单 %s）' % exp)
    spec = importlib.util.spec_from_file_location('e6n_spec_ref', p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m                          # dataclass 需要模块在 sys.modules 里
    spec.loader.exec_module(m)
    return m


def fnum(x):
    return ('%g' % float(x))


def desc_id(s):
    """可读描述符 ID：kind|feature|parent|memory|H|s<strength>|<applicability>|a<α>|f<freq>|d<dir>[|o<owner 键前 12>]。"""
    parts = [s.kind, s.feature, s.parent, s.memory, 'H%d' % s.hold, 's' + fnum(s.strength), s.applicability, 'a' + fnum(s.outer_alpha),
             'f%d' % s.frequency, 'd%+d' % s.direction]
    if s.owner and s.owner != 'Q_BOTH':
        parts.append('o' + s.owner[:12])
    elif s.owner == 'Q_BOTH':
        parts.append('oQ_BOTH')
    return '|'.join(parts)


def config_of(did):
    p = did.split('|')
    return '|'.join(p[:4] + p[5:])                      # 去掉 H


def support_sig(s, lookup):
    if s.kind in ('MASK_CLONE', 'DOSE', 'MATCHED_COMPONENT', 'COMPONENT_DOSE'):
        return support_sig(lookup[s.owner], lookup)
    fam = 'Q_BOTH' if s.kind == 'COMBO_COMPONENT' else SUPPORT_OWNER.get(s.feature, s.feature)
    return fam, s.applicability, s.frequency


def input_variant(s, lookup):
    """测量输入变体（名单层据此取 kf / K）。锚：Q0 / C1 / NATIVE；五面与桥：FACET；raw 构造：RAW；附属：CLONE / DOSE；分量：RAW / CDOSE。"""
    k = s.kind
    if k == 'STRONG_ANCHOR':
        return 'NATIVE|%s' % s.parent
    if k == 'ANCHOR':
        return 'NATIVE' if s.feature == 'ORIGINAL' else s.feature
    if k in ('MASK_CLONE', 'DOSE', 'COMPONENT_DOSE'):
        o = lookup[s.owner]
        ov = input_variant(o, lookup)
        if k == 'MASK_CLONE':
            return ('CLONE_RAW' if ov.startswith('RAW|') else 'CLONE|' + '|'.join(ov.split('|')[1:5]))
        if k == 'DOSE':
            return 'DOSE|%s' % ov
        return 'CDOSE|%s' % ov
    fam, app, fr = support_sig(s, lookup)
    if s.feature in FACETS + BRIDGES:
        return 'FACET|%s|eta%s|%s|f%d|d%+d' % (s.feature, fnum(s.strength), app, fr, s.direction)
    if s.feature in RAW_ALL:
        return 'RAW|%s|lam%s|%s|f%d|sup:%s' % (s.feature, fnum(s.strength), app, fr, fam)
    raise ValueError(s)


def exposure_of(s):
    if s.kind in ('ANCHOR', 'STRONG_ANCHOR'):
        return N.LABEL_SECOND
    return N.LABEL_FIRST_LOOK


def compile_all():
    R = ref()
    t0 = time.time()
    primary, aux = R.registry()
    extra, cdose, pairs = R.component_registry(primary)
    d72 = R.display72()
    rsha = hashlib.sha256(json.dumps([asdict(s) for s in primary], sort_keys=True).encode()).hexdigest()
    rep = json.load(open(N.P('stage0', 'plan_tests', 'report.json'), encoding='utf-8'))
    chk = dict(main=len(primary), auxiliary=len(aux), primary72=len(d72), matched=len(extra), cdose=len(cdose), comparisons=len(pairs),
               registry_sha256=rsha)
    exp = dict(main=rep['main_descriptors'], auxiliary=rep['auxiliary_descriptors'], primary72=rep['primary_display'],
               matched=rep['matched_component_controls'], cdose=rep['component_dose_controls'], comparisons=rep['component_comparisons'],
               registry_sha256=rep['registry_sha256'])
    if chk != exp:
        raise RuntimeError('A0 计数 / registry_sha256 与参考输出不符：%s vs %s' % (chk, exp))
    lookup = {s.key(): s for s in primary + aux + extra + cdose}
    keys72 = {s.key() for s in d72}
    recipe = {}
    for i, s in enumerate(d72):
        recipe[s.key()] = (i % 12) + 1
    rows = []
    for s in primary:
        did = desc_id(s)
        fam, app, fr = support_sig(s, lookup)
        in_pol = not (s.kind == 'STRONG_ANCHOR' or (s.kind == 'ANCHOR' and s.feature == 'ORIGINAL'))
        rb = s.kind not in ('ANCHOR', 'STRONG_ANCHOR')
        mech = ''
        if rb:
            mech = 'CONTENT_IID|CONTENT_ISK_P5'
            if (s.key() in keys72) or (s.feature in ADAPTED and s.kind == 'CORE'):
                mech += '|CONTENT_QRANGE_P5'
        rows.append(dict(desc_id=did, spec_key=s.key(), kind=s.kind, feature=s.feature, parent=s.parent, memory=s.memory, H=s.hold,
                         strength=s.strength, applicability=s.applicability, outer_alpha=s.outer_alpha, frequency=s.frequency,
                         direction=s.direction, owner=s.owner or 'NONE', config_id=config_of(did), support_family=fam, support_applicability=app,
                         support_frequency=fr, input_variant=input_variant(s, lookup), is_primary72=s.key() in keys72,
                         primary_recipe=recipe.get(s.key(), 0), in_policy_table=in_pol, random_bound=rb, random_mechanisms=mech or 'NOT_APPLICABLE',
                         r_memory=(s.key() in keys72 and s.memory != 'NONE' and s.feature not in ('Q0', 'C1')),
                         e_random_mechanism='LEGACY_POLICY_RANDOM' if (s.kind == 'ANCHOR' and s.feature in ('Q0', 'C1') and s.outer_alpha == .25 and s.hold == 5) else (
                             'NEW_CONTENT_RANDOM_DIAGNOSTIC' if rb else 'RANDOM_NOT_SCHEDULED'),
                         exposure=exposure_of(s), replacement_preference_status='NOT_AUTHORIZED' if rb else 'NOT_APPLICABLE',
                         deployment_authorized=False, feature_version='E6n-minute-v1' if (s.feature in FACETS + RAW_ALL) else 'SOURCE',
                         contract_version=N.CONTRACT_VERSION, plan_sha256=N.PLAN_SHA256[:16], data_sha='BOUND_AT_RUN', code_sha='BOUND_AT_RUN',
                         init='SEGMENT_RESET_19D_WARMUP', cost='SOURCE_8BP_CHARGED_TURN', domain=s.applicability if rb else 'POOL0'))
    D = pd.DataFrame(rows)
    if D.desc_id.duplicated().any():
        raise RuntimeError('desc_id 重复')
    arows = []
    for s in aux:
        o = lookup[s.owner]
        arows.append(dict(aux_id=desc_id(s), spec_key=s.key(), kind=s.kind, owner_desc_id=desc_id(o), owner_spec_key=s.owner, feature=s.feature,
                          parent=s.parent, memory=s.memory, H=s.hold, strength=s.strength, applicability=s.applicability, outer_alpha=s.outer_alpha,
                          frequency=s.frequency, direction=s.direction, config_id=config_of(desc_id(s)), input_variant=input_variant(s, lookup),
                          support_family=support_sig(s, lookup)[0], random_bound=False, in_policy_table=False, exposure=N.LABEL_FIRST_LOOK,
                          deployment_authorized=False))
    A = pd.DataFrame(arows)
    crows = []
    for s in extra + cdose:
        o = lookup[s.owner]
        crows.append(dict(comp_id=desc_id(s), spec_key=s.key(), kind=s.kind, owner_desc_id=desc_id(o), owner_spec_key=s.owner, feature=s.feature,
                          parent=s.parent, memory=s.memory, H=s.hold, strength=s.strength, applicability=s.applicability, outer_alpha=s.outer_alpha,
                          frequency=s.frequency, direction=s.direction, config_id=config_of(desc_id(s)),
                          input_variant=(input_variant(s, lookup) if s.kind == 'COMPONENT_DOSE' else
                                         'RAW|%s|lam%s|%s|f%d|sup:%s' % (s.feature, fnum(s.strength), support_sig(s, lookup)[1],
                                                                         support_sig(s, lookup)[2], support_sig(s, lookup)[0])),
                          support_family=support_sig(s, lookup)[0], random_bound=True, random_mechanisms='SHARED_WITH_OWNER_DONOR',
                          in_policy_table=False, exposure=N.LABEL_FIRST_LOOK, deployment_authorized=False))
    CC = pd.DataFrame(crows)
    # COMPONENT_DOSE 的简化分量输入 = 同坐标同支持的 MATCHED / CONTROL
    cmap = {}
    for r in pairs:
        if r['role'] == 'COMPONENT_DOSE':
            cmap[r['right']] = r['input_control']
    allkeys = {s.key(): desc_id(s) for s in primary + aux + extra + cdose}
    CC['input_control_desc_id'] = CC['spec_key'].map(lambda k: allkeys.get(cmap.get(k, ''), 'NOT_APPLICABLE'))
    return R, primary, aux, extra, cdose, pairs, d72, D, A, CC, allkeys, lookup, dict(chk=chk, secs=round(time.time() - t0, 1))


def comparisons(primary, aux, extra, cdose, pairs, allkeys, lookup):
    """plan §6.4a 的 2,178 条直接分量比较 + §6.5 每对象标准比较（子 − 原父 / 同记忆 Q0 / Q0 HG10 / Q0 LAG1_10 / 自身 NONE / MASK_CLONE / DOSE）
    + 方向 / 作用域 / 频率 / 外层剂量 / 合用四账户 / 信息 × 记忆四账户 / OHLC 桥配对。"""
    rows = []
    cid = [0]

    def add(view, card, kind, left, right, coef='left(+1) − right(−1)', est='D_seg = 252·100·(mean_left − mean_right)，共同有限日；FULL = Σ n_s D_s / Σ n_s；G4 = 段 D 中位'):
        cid[0] += 1
        rows.append(dict(comparison_id='E6N-CMP%06d' % cid[0], view=view, card=card, kind=kind, left_desc_id=left, right_desc_id=right,
                         coefficient=coef, estimand=est, unit='ann_pp'))
    for r in pairs:
        add('COMPONENT' if r['role'] == 'COMPONENT' else 'COMPONENT_DOSE', 'H04' if 'PATH' in lookup[r['left']].feature else 'H07',
            r['role'], allkeys[r['left']], allkeys[r['right']])
    idx = {}
    for s in primary:
        idx[(s.kind, s.feature, s.parent, s.memory, s.hold, s.strength, s.applicability, s.outer_alpha, s.frequency, s.direction)] = desc_id(s)

    def anchor(f, p, m, h, a=.25):
        k = ('ANCHOR', f, p, m, h, 0.0, 'ALL', a, 5, 1)
        return idx.get(k)
    auxby = {}
    for s in aux:
        auxby[(s.owner, s.kind)] = desc_id(s)
    for s in primary:
        if s.kind in ('ANCHOR', 'STRONG_ANCHOR'):
            continue
        L = desc_id(s)
        card = {'PL_REL20': 'H03', 'TAIL_PUSH': 'H05', 'TAIL_VOL_REL20': 'H06', 'JSD_PROFILE20': 'H06', 'RV_REL20': 'H08', 'Q_PATH': 'H04',
                'Q_CLOSE_THIN': 'H07', 'Q_RV': 'H04', 'Q_RANGE': 'H04', 'Q_CLOSE_LEVEL': 'H07', 'Q_BOTH': 'H11', 'K_RANGE_SOURCE': 'H08',
                'CLV20_SOURCE': 'H08'}[s.feature]
        orig = anchor('ORIGINAL', s.parent, 'NONE', s.hold, a=0.0)
        if orig:
            add('VS_ORIGINAL_PARENT', card, 'ACTUAL_PARENT', L, orig)
        for f, m, view in (('Q0', s.memory, 'VS_SAME_MEMORY_Q0'), ('Q0', 'HG10', 'VS_Q0_HG10'), ('Q0', 'LAG1_10', 'VS_Q0_LAG1_10')):
            r = anchor(f, s.parent, m, s.hold, s.outer_alpha)
            if r:
                add(view, card, 'CURRENT_FRONTIER' if view != 'VS_SAME_MEMORY_Q0' else 'SAME_MEMORY_Q0', L, r)
        if s.memory != 'NONE':
            k = (s.kind, s.feature, s.parent, 'NONE', s.hold, s.strength, s.applicability, s.outer_alpha, s.frequency, s.direction)
            if k in idx and s.kind not in ('COMBO_COMPONENT',):
                add('VS_OWN_NONE', 'H09', 'MEMORY_INCREMENT', L, idx[k])
        for kk in ('MASK_CLONE', 'DOSE'):
            if (s.key(), kk) in auxby:
                add('VS_' + kk, 'H10', kk, L, auxby[(s.key(), kk)])
        if s.kind == 'DIRECTION':
            k = ('CORE', s.feature, s.parent, s.memory, s.hold, s.strength, 'QGOOD', s.outer_alpha, s.frequency, 1)
            if k in idx:
                add('DIRECTION_REVERSED_MINUS_FORWARD', card, 'DIRECTION', L, idx[k])
        if s.kind == 'APPLICABILITY':
            kind_q = 'CORE' if s.feature in FACETS + ADAPTED else 'CONTROL'
            k = (kind_q, s.feature, s.parent, s.memory, s.hold, s.strength, 'QGOOD', s.outer_alpha, s.frequency, s.direction)
            if k in idx:
                add('ALL_MINUS_QGOOD', 'H10', 'APPLICABILITY', L, idx[k])
        if s.kind == 'FREQUENCY':
            kind_q = 'CORE' if s.feature in FACETS + ADAPTED else 'CONTROL'
            k = (kind_q, s.feature, s.parent, s.memory, s.hold, s.strength, s.applicability, s.outer_alpha, 5, s.direction)
            if k in idx:
                add('FREQ%d_MINUS_FREQ5' % s.frequency, 'H08', 'FREQUENCY', L, idx[k])
        if s.kind == 'OUTER_DOSE':
            k = ('CORE', s.feature, s.parent, s.memory, s.hold, s.strength, s.applicability, .25, s.frequency, s.direction)
            if k in idx:
                add('OUTER_ALPHA%s_MINUS_ALPHA0.25' % fnum(s.outer_alpha), card, 'OUTER_DOSE', L, idx[k])
        if s.kind == 'LEGACY_BRIDGE':
            for f in FACETS:
                k = ('CORE', f, s.parent, s.memory, s.hold, .25, 'QGOOD', .25, 5, 1)
                if k in idx:
                    add('FACET_MINUS_OHLC_BRIDGE', 'H08', 'LEGACY_BRIDGE', idx[k], L)
        if s.kind == 'CORE' and s.feature == 'Q_PATH':
            for ctl in ('Q_RV', 'Q_RANGE'):
                k = ('CONTROL', ctl, s.parent, s.memory, s.hold, s.strength, s.applicability, s.outer_alpha, s.frequency, s.direction)
                if k in idx:
                    add('PATH_MINUS_%s' % ctl, 'H04', 'MATCHED_CONTROL', L, idx[k])
        if s.kind == 'CORE' and s.feature == 'Q_CLOSE_THIN':
            k = ('CONTROL', 'Q_CLOSE_LEVEL', s.parent, s.memory, s.hold, s.strength, s.applicability, s.outer_alpha, s.frequency, s.direction)
            if k in idx:
                add('THIN_MINUS_LEVEL', 'H07', 'MATCHED_CONTROL', L, idx[k])
        if s.kind == 'COMBINATION':
            for f in ADAPTED:
                k1 = ('COMBO_COMPONENT', f, s.parent, s.memory, s.hold, .125, 'QGOOD', s.outer_alpha, 5, 1)
                k2 = ('CORE', f, s.parent, s.memory, s.hold, .25, 'QGOOD', s.outer_alpha, 5, 1)
                if k1 in idx:
                    add('BOTH_MINUS_HALF_%s_COMMON' % f, 'H11', 'COMBINATION', L, idx[k1])
                if k2 in idx:
                    add('BOTH_MINUS_FULL_%s' % f, 'H11', 'COMBINATION_VS_SINGLE', L, idx[k2])
    return pd.DataFrame(rows)


def parse_table(lines, start_pat, first_col_pat):
    out = []
    on = False
    for ln in lines:
        if re.search(start_pat, ln):
            on = True
            continue
        if on:
            if not ln.startswith('|'):
                if out:
                    break
                continue
            cells = [c.strip() for c in ln.strip().strip('|').split('|')]
            if all(re.fullmatch(r'-+', c or '-') for c in cells):
                continue
            if re.match(first_col_pat, cells[0]):
                out.append(cells)
    return out


def cards_and_claims():
    lines = open(N.P('PLAN_COPY.md'), encoding='utf-8').read().split('\n')
    H = parse_table(lines, r'^\| 卡 \| motivation', r'^H\d\d ')
    if len(H) != 16:
        raise RuntimeError('卡片表解析 %d 行（应 16）' % len(H))
    first = {'H01': 'NOT_APPLICABLE_ENGINEERING_CARD（时钟 / 身份；Stage 0 第 7 类实测 stage0/c7_minute）',
             'H02': 'FACT：E6m 主表已见（F1；policy_E6m.csv，Stage 0 A2-4 逐值复现）',
             'H12': 'FACT：E6m B6 触发账本（gross 与粗费用代理已见；E6m reports/fixed_full/b6_trigger_ledger.csv）',
             'H13': 'FACT：决策端第一道 P1 表（exec_briefs/E6n_probe_P1_cvr_tail_by_position_activity.csv，2026-10-12 19:39–19:45 本机时间）+ E6e 同数对照',
             'H14': 'FACT：E6m B3 池内 / 门内读数（F1）；分钟成员全 A 域未测',
             'H15': 'FACT：E6m 两推导段读数（F2 早段翻号）；SSE 2018-08-20 规则原文（stage0/c7_minute/rules）',
             'H16': 'NOT_APPLICABLE_RECORD_CARD（记录完整性；双账本与 query 链）'}
    rows = []
    for c in H:
        cid = c[0][:3]
        m = re.search(r'（(.+?)）', c[0])
        auth = m.group(1) if m else 'Web'
        rows.append(dict(claim_id='E6N-' + cid, card=cid, title=c[0], author=auth, version='plan v1.1（af5ff33f）', source=c[1],
                         first_stage_evidence=first.get(cid, 'INLINE_STAGE1_NOT_YET_MEASURED'), seen_facts=c[1], new_prediction=c[2],
                         estimand='见 query_registry_E6n 本卡各 query 的 object_rule', control=c[3], domain='QGOOD 主；pool0 / clean / 门内 / 拒绝集四域（plan §6.1）',
                         implementation='registry/comparison_manifest_E6n.csv + query_registry_E6n.csv（card = %s）' % cid,
                         query='E6N-%s-*' % cid, exposure=N.LABEL_FIRST_LOOK if cid not in ('H01', 'H02', 'H16') else 'NOT_APPLICABLE',
                         result='NOT_RUN', miss_reason=c[3] + '；符号判断与证据强度分开：负点估 = 方向 miss；正而区间宽 = 方向相符但证据有限；有效域 / 制度显著分歧 = mixed；未覆盖 = 未检验（plan §13.1）',
                         next_step=c[4], externality=c[4],
                         card_type={'H01': 'ENGINEERING', 'H02': 'REPLICATION', 'H16': 'RECORD'}.get(cid, 'OPEN_QUESTION' if cid in ('H08', 'H09', 'H10', 'H11', 'H14', 'H15') else 'DIRECTIONAL')))
    cards = pd.DataFrame(rows)
    P = parse_table(lines, r'^\| 预测ID \| 第一测量对象', r'^H\d\d-P')
    crow = []
    for c in P:
        ids = ['H06-P1', 'H06-P2'] if c[0].startswith('H06-P1/P2') else [c[0]]
        for i in ids:
            crow.append(dict(assertion_id=i, card=i[:3], author={'H03': 'CC+Web', 'H04': 'Web', 'H05': 'CC（Web 改估计对象）', 'H06': 'CC（Web 改估计对象）',
                                                                 'H07': 'Web', 'H12': 'CC（Web 改估计对象）', 'H13': 'CC（Web 改估计对象）'}[i[:3]],
                             first_object=c[1], frozen_direction=c[2],
                             estimand=c[1], comparator={'H03-P': 'PL_REL20 高组（同域同日）', 'H04-P1': 'Q0|A4b_CVRv5|α.25|HG10|H5', 'H04-P2': 'Q_RV 同坐标共同 Q_PATH 支持',
                                                        'H05-P': 'TAIL_PUSH 高组（同域同日）', 'H06-P1': 'TAIL_VOL_REL20 高组', 'H06-P2': 'JSD_PROFILE20 高组',
                                                        'H07-P1': 'Q0|A4b_CVRv5|α.25|HG10|H5', 'H07-P2': 'Q_CLOSE_LEVEL 同支持同坐标',
                                                        'H12-P': '同日龄随机触发（同风险集同率）', 'H13-P': '同日同父同数随机删除'}[i],
                             reading_rule='负点估 = 方向 miss；正而区间宽 = 方向相符但证据有限；域 / 制度显著分歧 = mixed（分域披露）；数据未覆盖 = 未检验（plan §13.1）',
                             counts_in_hit_rate=True, result='NOT_RUN'))
    claims = pd.DataFrame(crow)
    if len(claims) != 10:
        raise RuntimeError('方向断言 %d 条（应 10）' % len(claims))
    T = parse_table(lines, r'^\| 源定位/短原句 \| 本版处理', r'^.')
    carry = pd.DataFrame([dict(carry_id='E6N-CC%02d' % (i + 1), author='CC', version='E6n_proposal v2（82f439f2）', source_locator=c[0],
                               plan_treatment=c[1], scoring_rule=c[2], status='SUPERSEDED' if ('替代' in c[1] or '撤去' in c[1]) else 'PREDICTION',
                               supersedes_id='NOT_APPLICABLE', counts_in_web_hit_rate=False)
                          for i, c in enumerate(T)])
    return cards, claims, carry


def main():
    t0 = time.time()
    os.makedirs(N.P('registry'), exist_ok=True)
    os.makedirs(N.P('registration'), exist_ok=True)
    R, primary, aux, extra, cdose, pairs, d72, D, A, CC, allkeys, lookup, info = compile_all()
    CM = comparisons(primary, aux, extra, cdose, pairs, allkeys, lookup)
    cards, claims, carry = cards_and_claims()
    outs = []
    for nm, df in (('descriptors_E6n.csv', D), ('auxiliary_E6n.csv', A), ('component_controls_E6n.csv', CC), ('comparison_manifest_E6n.csv', CM),
                   ('cards_E6n.csv', cards), ('claims_E6n.csv', claims), ('cc_carry_E6n.csv', carry)):
        p = N.P('registry', nm)
        N.atomic_write_csv(p, N.to_status(df))
        outs.append(p)
    var = pd.concat([D[['input_variant', 'kind']], A[['input_variant', 'kind']], CC[['input_variant', 'kind']]]).drop_duplicates('input_variant')
    pv = N.P('registry', 'input_variants_E6n.csv')
    N.atomic_write_csv(pv, var.sort_values('input_variant'))
    outs.append(pv)
    counts = dict(info['chk'], by_kind=D.kind.value_counts().to_dict(), policy_rows=int(D.in_policy_table.sum()), random_bound=int(D.random_bound.sum()),
                  configs_main=int(D.config_id.nunique()), configs_aux=int(A.config_id.nunique()), configs_comp=int(CC.config_id.nunique()),
                  input_variants=int(len(var)), comparisons_total=int(len(CM)), comparisons_by_view=CM.view.value_counts().to_dict(),
                  cards=int(len(cards)), claims=int(len(claims)), cc_carry=int(len(carry)), secs=round(time.time() - t0, 1))
    pc = N.P('registration', 'a0_counts_E6n.json')
    N.atomic_write_json(pc, counts)
    outs.append(pc)
    N.write_receipt('E6n_a0', outs, code=[__file__], **{k: v for k, v in counts.items() if not isinstance(v, dict)})
    print(json.dumps({k: v for k, v in counts.items() if k != 'comparisons_by_view'}, ensure_ascii=False, default=str)[:1500])


if __name__ == '__main__':
    main()
