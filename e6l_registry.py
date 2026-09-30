# -*- coding: utf-8 -*-
"""E6l 登记编译（plan §9 / §16.3；brief §3 A0）：与 spec 脚本 compile_design / random_*_ids / kernel_support_ids /
comparison_manifest / audit_control_manifest 同规则（逐块计数与 ID 元组集合由 e6l_a0 对账 stage0/plan_tests/out/*.json）。
描述符 ID：'<meas>|<mother>|a<α:g>|H<h>|<op>'（spec 元组 (f, p, a, h, op)）；目标 ID：去掉 H（INV 例外：H 进目标）。
E6k 同构对象（brief W08）：Q0 ↔ E6k 'Q'；K0 NATIVE ↔ E6k PARENT；K0 HGb ↔ E6k HG_ONLYb；HGb ↔ E6k NATIVE_HGb。"""
import itertools

P6 = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
P8 = P6 + ('R2', 'A06')
ALPHAS = (.125, .25, .5)
HS = tuple(range(1, 21))
RH = (1, 2, 3, 5, 10, 20)
Q = ('Q0', 'Q_RANK3', 'Q_RANK5', 'Q_RANK10', 'Q_D3', 'Q_D5', 'Q_D10', 'Q_DEW3', 'Q_DEW5', 'Q_QMEAN5', 'Q_DMED5')
OPS = ('NATIVE', 'HG5', 'HG10', 'HG15')
MEM = ('LAG1_10', 'DECAY2_10', 'DECAY5_10', 'INV10')
STATE = ('VOL_HI15', 'VOL_HI5', 'VOL_MEAN15', 'VOL_MEAN5')
MEMQ = ('Q0', 'Q_D5', 'Q_RANK5')
RECIPES = (('Q0', 'NATIVE'), ('Q0', 'HG10'), ('Q0', 'LAG1_10'), ('Q0', 'DECAY5_10'), ('Q0', 'INV10'),
           ('Q_D3', 'NATIVE'), ('Q_D5', 'NATIVE'), ('Q_D5', 'HG10'), ('Q_RANK5', 'NATIVE'), ('Q_RANK5', 'HG10'),
           ('Q_DEW5', 'NATIVE'), ('Q_DEW5', 'HG10'))
BRIDGE = ('Q_RANKOBS5', 'Q_RANKSCORE5')
RMARK = ('RMARK_UNIFORM_IID', 'RMARK_UNIFORM_P5', 'RMARK_ISK_P5')
POLICY_MECHS = ('LEGACY_POLICY_RANDOM', 'CONTENT_COND_ISK_P5')


def compile_design():
    """spec compile_design 同规则；返回 {(f, p, a, h, op): [blocks]}（插入序 = spec 生成序）。"""
    rows = {}

    def add(block, f, p, a, h, op):
        key = (f, p, float(a), int(h), op)
        rows.setdefault(key, [])
        if block not in rows[key]:
            rows[key].append(block)
    for f, p, a, h, op in itertools.product(Q, P6, ALPHAS, HS, OPS):
        add('CORE', f, p, a, h, op)
    for p, a, h, op in itertools.product(P6, ALPHAS, HS, OPS):
        add('CONTROL', 'C1', p, a, h, op)
    for f, p, a, h, op in itertools.product(('S', 'M'), P6, ALPHAS, HS, ('NATIVE', 'HG10')):
        add('CONTROL', f, p, a, h, op)
    for f, p, a, h, op in itertools.product(MEMQ + ('C1',), P6, ALPHAS, HS, MEM):
        add('MEMORY', f, p, a, h, op)
    for f, p, a, h, op in itertools.product(('Q0', 'Q_D5', 'C1'), P6, ALPHAS, HS, STATE):
        add('STATE', f, p, a, h, op)
    for p, h, op in itertools.product(P6, HS, OPS[1:] + MEM + STATE):
        add('OLD_RULE', 'K0', p, 0, h, op)
    for f, p, a, h, op in itertools.product(BRIDGE, P6, ALPHAS, HS, ('NATIVE', 'HG10')):
        add('BRIDGE', f, p, a, h, op)
    for f, p, a, h, op in itertools.product(('Q0', 'Q_D5', 'C1'), P6, ALPHAS, HS, ('HG20', 'HG30')):
        add('EDGE', f, p, a, h, op)
    for p, h, op in itertools.product(P6, HS, ('HG20', 'HG30')):
        add('EDGE_OLD', 'K0', p, 0, h, op)
    for p, h in itertools.product(P8, HS):
        add('PARENT', 'K0', p, 0, h, 'NATIVE')
    return {k: rows[k] for k in sorted(rows)}


def primary_ids(a=.25):
    return [(f, p, float(a), 5, op) for p, (f, op) in itertools.product(P6, RECIPES)]


def random_content_ids(keys):
    return [k for k in keys if k[0] != 'K0' and k[3] in RH]


def random_memory_ids(keys):
    return [k for k in keys if k[0] in ('Q0', 'Q_D5', 'Q_RANK5', 'K0') and k[3] in (1, 5, 20) and k[4] == 'HG10']


def kernel_support_ids(keys):
    return [k for k in keys if k[0] in Q[1:] + BRIDGE and k[2] == .25 and k[3] in (1, 5, 20) and k[4] in ('NATIVE', 'HG10')]


def comparison_base(keys):
    """spec comparison_manifest 同规则：[(kind, left, right)]（按 (kind, left, right) 排序）。"""
    ids = set(keys)
    out = {}

    def add(label, left, right):
        if left == right:
            return
        if left not in ids or right not in ids:
            raise ValueError(('missing comparison', label, left, right))
        out[(label, left, right)] = 1
    for f, p, a, h, op in sorted(ids):
        if f == 'K0':
            continue
        child = (f, p, a, h, op)
        add('PARENT', child, ('K0', p, 0.0, h, 'NATIVE'))
        add('SAME_MEAS_NATIVE', child, (f, p, a, h, 'NATIVE'))
        add('SAME_OPERATOR_C1', child, ('C1', p, a, h, op))
        add('SAME_OPERATOR_Q0', child, ('Q0', p, a, h, op))
        add('KNOWN_QHG10', child, ('Q0', p, a, h, 'HG10'))
        if op != 'NATIVE':
            add('RULE_ONLY', child, ('K0', p, 0.0, h, op))
    return sorted(out)


def audit_controls(keys):
    """spec audit_control_manifest 同规则：[(kind, base)]。"""
    tasks = []
    for k in kernel_support_ids(keys):
        tasks.append(('KERNEL_DOSE', k))
    for k in keys:
        if k[4] == 'INV10':
            tasks.append(('INV_CAP_LOOP_PAIR', k))
        if k[4] in STATE and k[3] == 5 and k[2] in (0.0, .25):
            tasks.append(('STRICT250_STATE', k))
    for k in primary_ids():
        tasks.append(('BOUNDARY_CONT_PARENT_PAIR', k))
    return tasks


# ---------------------------------------------------------------- ID 与映射
def fmt_a(a):
    return '%g' % float(a)


def desc_id(k):
    f, p, a, h, op = k
    return '%s|%s|a%s|H%d|%s' % (f, p, fmt_a(a), int(h), op)


def target_of(k):
    """H 无关的形成名单共用一个目标（INV 按 H）。"""
    f, p, a, h, op = k
    if op == 'INV10':
        return '%s|%s|a%s|%s|H%d' % (f, p, fmt_a(a), op, int(h))
    return '%s|%s|a%s|%s' % (f, p, fmt_a(a), op)


def task_of(k):
    return '%s|%s' % (k[1], k[0])


def e6k_equiv(k):
    """E6k 同构描述符 ID（brief W08；E6k 结构：Q / C1 × NATIVE / NATIVE_HG5/10/15、S / M × NATIVE / NATIVE_HG10、K0 × HG_ONLY5/10/15、PARENT）。"""
    f, p, a, h, op = k
    if f == 'K0':
        if op == 'NATIVE':
            return 'K0|%s|a0|H%d|PARENT' % (p, h)
        if op in ('HG5', 'HG10', 'HG15'):
            return 'K0|%s|a0|H%d|HG_ONLY%s' % (p, h, op[2:])
        return None
    if f not in ('Q0', 'C1', 'S', 'M'):
        return None
    fk = 'Q' if f == 'Q0' else f
    if op == 'NATIVE':
        return '%s|%s|a%s|H%d|NATIVE' % (fk, p, fmt_a(a), h)
    if op in ('HG5', 'HG10', 'HG15'):
        return '%s|%s|a%s|H%d|NATIVE_%s' % (fk, p, fmt_a(a), h, op)
    return None


def family_of(k):
    f, p, a, h, op = k
    if f == 'K0':
        return 'PARENT' if op == 'NATIVE' else 'OLD_RULE'
    if op == 'NATIVE':
        return 'NATIVE' if f in ('Q0', 'C1', 'S', 'M') else 'SMOOTH'
    if op.startswith('HG'):
        return 'HG'
    if op in MEM:
        return 'MEMORY'
    if op in STATE:
        return 'STATE'
    raise ValueError(k)
