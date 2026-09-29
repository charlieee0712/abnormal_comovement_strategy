# -*- coding: utf-8 -*-
"""E6k A0 编译器（brief §3 / W15 / W20；plan §8.3 / §8.4 / §11 / §13.2；附录 A6-5 / A6-6）。
独立枚举每段原始账户描述符（不调用 plan 规范脚本的 compile_design）→ 与 PLAN_COPY.md 抽出的 §16.3 脚本 compile_design 逐元组（含 block 集合）比对；
另编译附属清单（INC 72 / COMMON_SUPPORT / 剂量 / HG 持续性 / 影子 / 随机 / 八子集 / bootstrap 比较族）、18 张卡（原文行号 + queries 非空）、
query 注册表、问题 → 对象 / 任务 → 对象两张对账表、计数（measurement / operator / raw_id / 结构别名 / exposed / policy）。
不读任何收益；输出写 registry/ 与 registration/a0_manifest_E6k.json。"""
import e6k_boot  # noqa: F401
import os
import sys
import json
import itertools
import importlib.util

import numpy as np
import pandas as pd

import e6k_core as K

P6 = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
P8 = P6 + ('R2', 'A06')
SIG = ('S', 'M', 'Q', 'C1')
ALPHA = (0.125, 0.25, 0.5)
HOLDS = tuple(range(1, 21))
LANDMARK = (3, 5, 10, 20)
CORE_OPS = ('NATIVE', 'SZL3', 'SZL5', 'INC05', 'INC1')
OWN_OPS = ('SZL3_OWN', 'SZL5_OWN')
RP_OPS = ('RP0p5', 'RP1', 'RP3', 'RPINF')
LX_OPS = ('LX_SIZE3_10', 'LX_SIZE3_01', 'LX_ISK_10', 'LX_ISK_01')
BAND_OPS = tuple('%s_%s%d' % (base, kind, b) for base in ('NATIVE', 'INC1') for kind in ('SA', 'PM', 'HG') for b in (5, 10, 15))
OWNERS = (('S', 'A4b_CVRv5'), ('Q', 'A4b_CVRv5'), ('M', 'M_union3_v2_CVRv5'), ('C1', 'M_mean3_v2_CVRv5'))
RAR_MEAS = ('RARPRE20_LT', 'RARPRE60_LT', 'RARPRE20_SE', 'RARPRE60_SE')
RAR_MOTHERS = ('A4b_CVRv5', 'R2', 'A06')
PRIMARY_OPS = ('NATIVE', 'SZL5', 'INC1', 'RP3', 'NATIVE_HG10', 'INC1_HG10')
C1_HI = [('C1', p, 0.5, h, 'NATIVE') for p in ('A4b', 'A4b_CVRv5') for h in (10, 20)]
CS_BLOCKS = ('CORE', 'REPAIR', 'LAYER', 'TREFIT', 'POST2', 'RAR')
TAU = {'RP0p5': 0.5, 'RP1': 1.0, 'RP3': 3.0, 'RPINF': None}
PLAN_LINES = {'Q%02d' % i: 565 + 3 * (i - 1) for i in range(1, 19)}


def did(f, p, a, h, op):
    return '%s|%s|a%s|H%d|%s' % (f, p, ('%g' % a), int(h), op)


def tid_(f, p, a, op):
    return '%s|%s|a%s|%s' % (f, p, ('%g' % a), op)


def enumerate_blocks():
    """本编译器自己的枚举：块规则 → {元组: [块]}（元组 = (测量, 母体, α, H, 算子)，α 为 float）。"""
    blk = {}

    def put(key, b):
        blk.setdefault(key, [])
        if b not in blk[key]:
            blk[key].append(b)
    for f in SIG:
        for p in P8:
            for a in ALPHA:
                for h in HOLDS:
                    for op in CORE_OPS:
                        put((f, p, a, h, op), 'CORE')
                    for op in OWN_OPS:
                        put((f, p, a, h, op), 'OWN')
                    for op in RP_OPS:
                        put((f, p, a, h, op), 'REPAIR')
                    for op in LX_OPS:
                        put((f, p, a, h, op), 'LAYER')
    for f in SIG:
        for p in P6:
            for h in LANDMARK:
                for op in BAND_OPS:
                    put((f, p, 0.25, h, op), 'BAND')
    for f, p in OWNERS:
        for a in ALPHA:
            for h in HOLDS:
                for op in BAND_OPS:
                    put((f, p, a, h, op), 'BAND')
    band_keys = [k for k, v in blk.items() if 'BAND' in v]
    for f, p, a, h, op in band_keys:
        c1 = ('C1', p, a, h, op)
        if c1 not in blk:
            put(c1, 'BAND_COMPARATOR')
    for p in P6:
        for h in HOLDS:
            for b in (5, 10, 15):
                put(('K0', p, 0.0, h, 'HG_ONLY%d' % b), 'HG_ONLY')
    for f in SIG:
        for p in P6[:2]:
            for a in ALPHA:
                for h in HOLDS:
                    for g in ('0', '0p5'):
                        put((f, p, a, h, 'TREFIT' + g), 'TREFIT')
    for f in ('S', 'Q', 'C1'):
        for p in P6[:2]:
            for a in ALPHA:
                for h in HOLDS:
                    put((f, p, a, h, 'POST2_INCREMENT'), 'POST2')
    for f in RAR_MEAS:
        for p in RAR_MOTHERS:
            for a in ALPHA:
                for h in HOLDS:
                    put((f, p, a, h, 'NATIVE'), 'RAR')
    for p in P8:
        for h in HOLDS:
            put(('K0', p, 0.0, h, 'PARENT'), 'PARENT')
    for p in P6:
        put(('SM', p, 0.25, 5, 'NATIVE'), 'SM_ANCHOR')
    return blk


def load_spec_compile():
    path = K.P('stage0', 'plan_tests', 'e6k_spec_tests.py')
    spec = importlib.util.spec_from_file_location('e6k_spec_tests_extracted', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, K.sha_file(path)


def family(op):
    if op in ('NATIVE',):
        return 'NATIVE'
    if op.startswith('SZL') and op.endswith('_OWN'):
        return 'OWN'
    if op.startswith('SZL'):
        return 'SZL'
    if op.startswith('INC'):
        return 'INC' if '_' not in op else 'BAND'
    if op.startswith('RP'):
        return 'RP'
    if op.startswith('LX'):
        return 'LX'
    if op.startswith('HG_ONLY'):
        return 'HG_ONLY'
    if op.startswith('NATIVE_'):
        return 'BAND'
    if op.startswith('TREFIT'):
        return 'TREFIT'
    if op.startswith('POST2'):
        return 'POST2'
    return op


def band_parts(op):
    """'INC1_HG10' → ('INC1', 'HG', 10)。"""
    base, rest = op.split('_', 1)
    return base, rest[:2], int(rest[2:])


def main():
    trial = '--trial' in sys.argv                               # 试跑：写临时目录，不写回执
    out_reg = os.path.join(K.TRIAL, 'a0', 'registry') if trial else K.P('registry')
    out_man = os.path.join(K.TRIAL, 'a0', 'a0_manifest_E6k.json') if trial else K.P('registration', 'a0_manifest_E6k.json')
    os.makedirs(out_reg, exist_ok=True)
    blk = enumerate_blocks()
    # ---------------- 与 plan 规范脚本逐元组比对（A6-5）
    mod, spec_sha = load_spec_compile()
    ref = {tuple(r['id']): sorted(r['blocks']) for r in mod.compile_design()}
    mine = {(f, p, float(a), int(h), op): sorted(v) for (f, p, a, h, op), v in blk.items()}
    ref_n = {(f, p, float(a), int(h), op): v for (f, p, a, h, op), v in ref.items()}
    only_mine = sorted(set(mine) - set(ref_n))
    only_ref = sorted(set(ref_n) - set(mine))
    blk_diff = [k for k in mine if k in ref_n and mine[k] != ref_n[k]]
    acc_ref = sorted(tuple(r['id']) for r in mod.compile_support_controls())
    acc_mine = sorted((f, p, 0.25, 5, op) for f in SIG for p in P6 for op in ('INC_SUPPORT0', 'INC_DOSE05', 'INC_DOSE1'))
    acc_ok = [tuple((x[0], x[1], float(x[2]), int(x[3]), x[4])) for x in acc_ref] == acc_mine
    primary = [(f, p, 0.25, 5, op) for f in SIG for p in P6 for op in PRIMARY_OPS]
    cmp_ok = not only_mine and not only_ref and not blk_diff and acc_ok and len(mine) == 39142 and all(k in mine for k in primary) \
        and len(set(primary)) == 144
    # ---------------- 描述符表
    rows = []
    for key in sorted(mine):
        f, p, a, h, op = key
        blocks = mine[key]
        fam = family(op)
        is_primary = key in set(primary)
        is_c1hi = key in set(C1_HI)
        base = None
        if fam == 'BAND':
            base = band_parts(op)[0]
        native_cmp = did(f, p, a, h, 'NATIVE') if (fam not in ('NATIVE', 'PARENT', 'HG_ONLY') and f not in ('K0', 'SM')) else ''
        if f in RAR_MEAS:
            native_cmp = did('S', p, a, h, 'NATIVE')                  # Q13：RARPRE 相对 NATIVE_S
        c1_cmp = did('C1', p, a, h, op) if (f in SIG and f != 'C1' and ('C1', p, a, h, op) in mine) else ''
        par = did('K0', p, 0.0, h, 'PARENT')
        hg_only = ''
        if fam == 'BAND' and band_parts(op)[1] == 'HG':
            hg_only = did('K0', p, 0.0, h, 'HG_ONLY%d' % band_parts(op)[2])
        base_cmp = did(f, p, a, h, base) if base else ''
        if op == 'PARENT':
            exposure = 'SOURCE_PARENT'
        elif fam == 'HG_ONLY':
            exposure = K.LABEL_FIRST_LOOK
        elif op == 'NATIVE' and f in SIG:
            exposure = 'REUSED_E6I_E6J_SEEN' + ('|C1_HI_E6J_S13_SEEN' if is_c1hi else '')
        elif op == 'NATIVE' and f == 'SM':
            exposure = 'E6J_SEEN_SM_ANCHOR'
        elif op == 'NATIVE' and f in RAR_MEAS:
            exposure = 'E6J_SEEN_RARPRE'
        else:
            exposure = K.LABEL_FIRST_LOOK
        new_op = exposure == K.LABEL_FIRST_LOOK
        if a == 0.25 and h == 5 and op not in ('PARENT',) and fam != 'HG_ONLY':
            rnd = 'LEGACY+NEW'
        elif is_c1hi:
            rnd = 'LEGACY+NEW'
        elif fam == 'HG_ONLY':
            rnd = 'NO_NEW_CONTENT_TO_PERMUTE'
        else:
            rnd = 'RANDOM_NOT_SCHEDULED'
        cs = bool(set(blocks) & set(CS_BLOCKS)) and a == 0.25 and h in LANDMARK
        shadow = is_primary or is_c1hi or (op == 'PARENT' and h == 5 and p in P6) or (op == 'HG_ONLY10' and h == 5)
        task = '%s|%s' % (p, f)
        rows.append(dict(desc_id=did(f, p, a, h, op), meas=f, mother=p, alpha=a, H=h, op=op, blocks='|'.join(blocks), family=fam,
                         target_id=tid_(f, p, a, op), primary144=is_primary, c1_hi=is_c1hi, sm_anchor=(f == 'SM'),
                         parent_desc=par, native_desc=native_cmp, c1_desc=c1_cmp, base_desc=base_cmp, hg_only_desc=hg_only,
                         evidence_exposure=exposure, new_operator=new_op,
                         replacement_preference_status='NOT_AUTHORIZED' if new_op else '',
                         deployment_authorized=False, random=rnd, cs_bridge=cs, shadow=shadow, task=task))
    D = pd.DataFrame(rows)
    # ---------------- 附属清单
    acc = []
    for f in SIG:
        for p in P6:
            for op in ('INC_SUPPORT0', 'INC_DOSE05', 'INC_DOSE1'):
                acc.append(dict(acc_id='ACC|' + did(f, p, 0.25, 5, op), kind='INC_SUPPORT_ACCESSORY', meas=f, mother=p, alpha=0.25, H=5, op=op,
                                target_id=tid_(f, p, 0.25, op), task='%s|%s' % (p, f), compare_to=did(f, p, 0.25, 5, 'INC1' if op != 'INC_DOSE05' else 'INC05')))
    for f, p in OWNERS:
        for base in ('NATIVE', 'INC1'):
            for kind in ('SA', 'PM', 'HG'):
                for b in (5, 10, 15):
                    for h in LANDMARK:
                        op = 'DOSE_%s_%s%d' % (base, kind, b)
                        acc.append(dict(acc_id='ACC|' + did(f, p, 0.25, h, op), kind='BAND_DOSE_CONTROL', meas=f, mother=p, alpha=0.25, H=h, op=op,
                                        target_id=tid_(f, p, 0.25, op), task='%s|%s' % (p, f), compare_to=did(f, p, 0.25, h, '%s_%s%d' % (base, kind, b))))
    cs_rows = D[D.cs_bridge]
    for _, r in cs_rows.iterrows():
        acc.append(dict(acc_id='CS|' + r.desc_id, kind='COMMON_SUPPORT_CHILD', meas=r.meas, mother=r.mother, alpha=r.alpha, H=r.H, op=r.op,
                        target_id='CS|' + r.target_id, task=r.task, compare_to='CSPARENT|' + did(r.meas, r.mother, 0.0, r.H, 'PARENT')))
    for (f, p) in sorted(set(zip(cs_rows.meas, cs_rows.mother))):
        for h in LANDMARK:
            acc.append(dict(acc_id='CSPARENT|' + did(f, p, 0.0, h, 'PARENT'), kind='COMMON_SUPPORT_PARENT', meas=f, mother=p, alpha=0.0, H=h,
                            op='PARENT', target_id='CSPARENT|' + tid_(f, p, 0.0, 'PARENT'), task='%s|%s' % (p, f), compare_to=did('K0', p, 0.0, h, 'PARENT')))
    A = pd.DataFrame(acc)
    # 随机清单
    rnd_obj = D[D.random == 'LEGACY+NEW']
    R = []

    def rrow(mech, r, Hs, alias=''):
        return dict(random_id='%s|%s' % (mech, r.desc_id), mechanism=mech, desc_id=r.desc_id, meas=r.meas, mother=r.mother, alpha=r.alpha,
                    H=r.H, op=r.op, Hs=Hs, alias_of=alias, n_paths_initial=1024, topup=512, cap=8192, task='%s|%s' % (r.mother, r.meas))
    for _, r in rnd_obj.iterrows():
        hg_owner = r.family == 'BAND' and (r.meas, r.mother) in OWNERS and band_parts(r.op)[1] == 'HG'
        R.append(rrow('LEGACY_POLICY_RANDOM', r, str(r.H)))
        R.append(rrow('NEW_COND_ISK_P5', r, '3|5|10|20' if hg_owner else str(r.H)))       # X14：HG 持续性控制另算 H{3,10,20}
        if r.primary144 or r.c1_hi:
            R.append(rrow('NEW_COND_ISK_IID', r, str(r.H)))                                 # 独立配对对照（块长 1）
    for f in SIG:
        for p in P6:
            r = D[D.desc_id == did(f, p, 0.25, 5, 'NATIVE')].iloc[0]
            for sub in ('EMPTY', 'I', 'S', 'K', 'IS', 'IK', 'SK', 'ISK'):
                R.append(rrow('EIGHT_SUBSET_' + sub, r, '5', alias='NEW_COND_ISK_P5|' + r.desc_id if sub == 'ISK' else ''))
    RR = pd.DataFrame(R)
    # bootstrap 比较族（固定 comparison_id）
    B = []
    for _, r in D.iterrows():
        if r.op == 'PARENT':
            continue
        B.append(dict(comparison_id='CP|' + r.desc_id, family='child_minus_parent', a=r.desc_id, b=r.parent_desc))
        if r.native_desc and r.native_desc != r.desc_id:
            B.append(dict(comparison_id='CN|' + r.desc_id, family='op_minus_native', a=r.desc_id, b=r.native_desc))
        if r.c1_desc:
            B.append(dict(comparison_id='CC1|' + r.desc_id, family='minus_same_op_C1', a=r.desc_id, b=r.c1_desc))
        if r.base_desc:
            B.append(dict(comparison_id='CB|' + r.desc_id, family='band_minus_base', a=r.desc_id, b=r.base_desc))
        if r.hg_only_desc:
            B.append(dict(comparison_id='CH|' + r.desc_id, family='hg_minus_hg_only', a=r.desc_id, b=r.hg_only_desc))
    BB = pd.DataFrame(B)
    # ---------------- 18 张卡 + query 注册表
    plan_lines = open(K.P('PLAN_COPY.md'), encoding='utf-8').read().split('\n')
    cards, queries = [], []
    CARD_Q = {
        'Q01': [('a', '144 主展示 NATIVE 24 行 × 五列 profile 政策表（子 − 原父，FULL / G4 并印）', "primary144 & op=='NATIVE'"),
                ('b', 'NATIVE 24 行组合层 / 编辑层 size（T / LAG1，带符号 + 绝对）与尾部', "primary144 & op=='NATIVE'"),
                ('c', 'NATIVE 24 行同资本（MATCH-CAP）与冲击后净值', "primary144 & op=='NATIVE'")],
        'Q02': [('a', 'SZL3 / SZL5 − 同测量 NATIVE（CORE，α × H 曲线；主 α .25 × H5）', "family=='SZL'"),
                ('b', 'SZL − SZL_OWN（同分组同掩码的旧 K 复制控制）', "family=='SZL' | family=='OWN'"),
                ('c', 'SZL 相对 NATIVE 的组合层 size 变化与编辑重叠', "family=='SZL'")],
        'Q03': [('a', 'INC − INC_DOSE（同均值同 RMS）', "family=='INC'"),
                ('b', 'INC_DOSE − INC_SUPPORT0 与 INC_SUPPORT0 − NATIVE（附属 72）', "family=='INC'"),
                ('c', 'INC 与 SZL 的原生编辑保留率（same_ticker_overlap_with_native）', "family=='INC' | family=='SZL'")],
        'Q04': [('a', 'PAIR_ALL（RPINF）− NATIVE 与 − 原父', "op=='RPINF'"),
                ('b', 'RP τ{.5,1,3} − PAIR_ALL（预算代价）', "family=='RP'"),
                ('c', 'RP 配对 / 保留 / 抑制的结构编辑 / SOLVER_LIMIT 计数', "family=='RP'")],
        'Q05': [('a', '八子集条件置换的随机均值（24 NATIVE）', "primary144 & op=='NATIVE'"),
                ('b', '六种顺序平均 Shapley 差（gross / 费用 / net 分列）', "primary144 & op=='NATIVE'"),
                ('c', '可移动权重与置换熵', "primary144 & op=='NATIVE'")],
        'Q06': [('a', 'LX 四账户：V10 − V00、V01 − V00、交互（逐日闭合）', "family=='LX'"),
                ('b', 'LX 资本 / N / 交易 / 冲击', "family=='LX'"),
                ('c', '§6.1 gross 特征匹配账本（组内差 + 组配置）', "family=='LX'")],
        'Q07': [('a', 'TREFIT0 / 0.5 / NATIVE（= g1）− 原父', "family=='TREFIT'"),
                ('b', 'COEF_INTERP_UNAVAILABLE、第二关有效数、最终曝光', "family=='TREFIT'")],
        'Q08': [('a', 'POST2 − 原父、− 同测量 NATIVE、C1 主动控制', "family=='POST2'"),
                ('b', 'POST2 第二关前实际编辑数 / 同资本', "family=='POST2'")],
        'Q09': [('a', 'SA − 无带基础（NATIVE / INC1）', "family=='BAND' & op.str.contains('_SA')"),
                ('b', 'SA − 同日共同剂量控制（DOSE）', "family=='BAND' & op.str.contains('_SA')")],
        'Q10': [('a', 'PM − 无带基础', "family=='BAND' & op.str.contains('_PM')"),
                ('b', 'PM − 共同剂量控制', "family=='BAND' & op.str.contains('_PM')"),
                ('c', 'PM 固定配对交换数的嵌套与结构单边编辑', "family=='BAND' & op.str.contains('_PM')")],
        'Q11': [('a', 'HG − 无带基础；HG_ONLY；信息 × 规则四账户（V00 / V10 / V01 / V11）', "family=='BAND' & op.str.contains('_HG') | family=='HG_ONLY'"),
                ('b', 'HG − 共同剂量控制、− 随机新内容续选（持续性控制）', "family=='BAND' & op.str.contains('_HG')"),
                ('c', 'HG 实现换手变化与 gross 变化分列', "family=='BAND' & op.str.contains('_HG')")],
        'Q12': [('a', 'S − Q 同槽位 / 同处理 / 同支持', "meas.isin(['S','Q'])"),
                ('b', 'S − Q 分结构', "meas.isin(['S','Q'])")],
        'Q13': [('a', 'RARPRE 2×2（窗口 × 时钟）', "family=='NATIVE' & meas.str.startswith('RARPRE')"),
                ('b', 'RARPRE 共同支持四账户桥', "family=='NATIVE' & meas.str.startswith('RARPRE')"),
                ('c', 'RARPRE − NATIVE_S', "family=='NATIVE' & meas.str.startswith('RARPRE')")],
        'Q14': [('a', '同对象 / α / H / 成本跨形态比较；same operator − NATIVE', "mother.isin(%r)" % list(P6)),
                ('b', 'CVR ± 边际', "mother.isin(%r)" % list(P6)),
                ('c', '编辑存活、实际资本、T 重估（A4b）', "mother.isin(%r)" % list(P6))],
        'Q15': [('a', '新算子 full / pre / post 与首次评价标签', 'new_operator'),
                ('b', '源对象 / 算子 / 目标与持仓指纹', 'new_operator')],
        'Q16': [('a', 'E6j 638 对象原 flag 复现（推导正 / 后段正，n 加权合并）', 'E6J_638'),
                ('b', '衰减场景相容性表（θ / 漂移 / 收缩 / 选择事件重做）', 'E6J_638')],
        'Q17': [('a', '五列 profile 并排（LEGACY_EDIT5 / PORT3_LAG1 / PORT3_T / EXEC_DISCLOSE_ONLY / EXEC_LEADER_VS_PARENT）', 'primary144 | c1_hi'),
                ('b', '固定曝光列（带符号均值 / 平均绝对差 / p95 / 最大 / 五组份额 / 小盘 30% / 未知 size / 目标与滚动 / 编辑 gap / 资本与编辑比例）', 'primary144 | c1_hi'),
                ('c', 'C1 主动基线与随机机会基线', 'primary144 | c1_hi')],
        'Q18': [('a', 'hypothesis_lineage：原句 → brief 采纳句 → 实现 → query → 允许结论', 'ALL'),
                ('b', '固定输出清单逐项打勾（plan §13.5）', 'ALL')],
    }
    for q, qs in CARD_Q.items():
        ln = PLAN_LINES[q]
        head = plan_lines[ln - 1]
        body = plan_lines[ln]
        if not head.startswith('### E6K-%s' % q):
            raise RuntimeError('卡片行号漂移：%s L%d' % (q, ln))
        qids = []
        for suf, subj, filt in qs:
            qid = 'E6K-%s-%s' % (q, suf)
            qids.append(qid)
            queries.append(dict(query_id=qid, card=q, subject=subj, object_filter=filt, unit='年化百分点（日配对均值 × 252 × 100）；size 为百分位点',
                                dates='推导段 2010-01-04..2018-12-31；后段在授权后；四段分列 + FULL', support='见 object_filter；COMMON_SUPPORT 另列'))
        cards.append(dict(card=q, plan_line=ln, title=head.replace('### ', ''), text=body, queries='|'.join(qids),
                          plan_sha256=K.sha_file(K.P('PLAN_COPY.md'))))
    C = pd.DataFrame(cards)
    Qy = pd.DataFrame(queries)
    # 问题 → 对象 / 任务 → 对象
    q2o = []
    for q, qs in CARD_Q.items():
        for suf, subj, filt in qs:
            if filt in ('E6J_638', 'ALL'):
                ids = ['E6J_638_OBJECTS'] if filt == 'E6J_638' else ['ALL_DESCRIPTORS']
            else:
                ids = D.query(filt, engine='python').desc_id.tolist()
            for x in ids:
                q2o.append(dict(query_id='E6K-%s-%s' % (q, suf), desc_id=x))
    Q2O = pd.DataFrame(q2o)
    T2O = D[['task', 'desc_id']].copy()
    # ---------------- 计数
    targets = D.target_id.nunique()
    struct_alias = [
        dict(alias='TREFIT g1 ≡ NATIVE（未登记为独立描述符）', n=0),
        dict(alias='RPINF ≡ PAIR_ALL（同一描述符）', n=int((D.op == 'RPINF').sum())),
        dict(alias='HG_ONLY：NATIVE / INC1 两起点在 α0 共用（不按四测量重复）', n=int((D.family == 'HG_ONLY').sum())),
        dict(alias='A4b_CVRv5 ≡ R1（E6j exact_alias；R1 不另算）', n=int((D.mother == 'A4b_CVRv5').sum())),
    ]
    counts = dict(raw_id_count=len(D), accessory_INC=int((A.kind == 'INC_SUPPORT_ACCESSORY').sum()),
                  band_dose_controls=int((A.kind == 'BAND_DOSE_CONTROL').sum()),
                  cs_children=int((A.kind == 'COMMON_SUPPORT_CHILD').sum()), cs_parents=int((A.kind == 'COMMON_SUPPORT_PARENT').sum()),
                  block_counts={b: int(D.blocks.str.split('|').apply(lambda x: b in x).sum()) for b in
                                ('CORE', 'OWN', 'REPAIR', 'LAYER', 'BAND', 'BAND_COMPARATOR', 'HG_ONLY', 'TREFIT', 'POST2', 'RAR', 'PARENT', 'SM_ANCHOR')},
                  measurement_count=int(D.meas.nunique()), measurements=sorted(D.meas.unique()),
                  operator_count=int(D.op.nunique()), operators=sorted(D.op.unique()),
                  target_count=targets, primary144=int(D.primary144.sum()), c1_hi=int(D.c1_hi.sum()), sm_anchor=int(D.sm_anchor.sum()),
                  mothers=len(P8), exposed_count=int((~D.new_operator).sum()), new_operator_count=int(D.new_operator.sum()),
                  policy_count=int((D.random == 'LEGACY+NEW').sum()),
                  random_objects=int(len(rnd_obj)), random_units=int(len(RR)), shadow_accounts=int(D.shadow.sum()),
                  bootstrap_comparisons=int(len(BB)), structural_alias=struct_alias,
                  exact_target_alias='A1-auto 由推导段掩码 hash 现算（本表只列结构别名）',
                  account_alias='同 H / lag / 费用 / A / 基准 / 状态 / 末端才算账户别名（plan §13.4）；A0 不预设')
    # ---------------- 写出
    paths = {}
    for nm, df in (('descriptors_E6k.csv', D), ('accessory_E6k.csv', A), ('randoms_E6k.csv', RR), ('bootstrap_comparisons_E6k.csv', BB),
                   ('cards_E6k.csv', C), ('query_registry_E6k.csv', Qy), ('question_to_objects_E6k.csv', Q2O), ('task_to_objects_E6k.csv', T2O)):
        p = os.path.join(out_reg, nm)
        K.atomic_write_csv(p, df)
        paths[nm] = K.sha_file(p)
    man = dict(written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), version=K.VERSION,
               plan_sha256=K.sha_file(K.P('PLAN_COPY.md')), spec_script_sha256=spec_sha,
               compare=dict(ok=bool(cmp_ok), only_in_compiler=len(only_mine), only_in_spec=len(only_ref), block_set_diffs=len(blk_diff),
                            accessory_72_equal=bool(acc_ok), primary144_present=all(k in mine for k in primary)),
               counts=counts, registry_sha256=paths)
    K.atomic_write_json(out_man, man)
    print(json.dumps(man['compare'], ensure_ascii=False), json.dumps(counts['block_counts']), 'targets', targets, 'random_units', len(RR),
          'bootstrap', len(BB), 'cs', counts['cs_children'], counts['cs_parents'], flush=True)
    if not trial:
        K.write_receipt('a0_compile', [out_man] + [os.path.join(out_reg, n) for n in paths],
                        'SUCCEEDED' if cmp_ok else 'FAILED', compare_ok=bool(cmp_ok), raw_id_count=len(D))
    return 0 if cmp_ok else 2


if __name__ == '__main__':
    sys.exit(main())
