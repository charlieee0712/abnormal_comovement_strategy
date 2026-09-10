#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 块 A 描述符展开 (§4)。纯组合逻辑, 不看任何收益、不碰数据。
   被 e6f_blockA.py 与 e6f_stage0 注册表共用。
"""
import sys, itertools, json
from fractions import Fraction
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np
import e6e_core as K
import e6f_core as F

# ---- 默认规格 (= 库默认窗, E6e 用的那一组) ----
DT_ = F.spec('T', 60)
DC = F.spec('C', 20)
DK = F.spec('K', 1, est='MA', eps=1e-4)
DCF = F.spec('Cf', 1, base='ratio')          # cvr_1d
DB5 = F.spec('B', 5)                          # cr5
DB20 = F.spec('B', 20)                        # cr20
DEF = {'T': DT_, 'C': DC, 'K': DK, 'Cf': DCF, 'B': DB5}

# ---- 扫描网格 (§4.1) ----
GT = [20, 40, 60, 90, 120]
GC = [5, 10, 20, 40, 60]
GK_W = [1, 3, 5, 10, 20]
GK_EST = ['MA', 'ROS']
GCF = [1, 2, 3, 5]
GB = [3, 5, 10, 20]
GEPS = [1e-5, 1e-4, 1e-3]
DEPTHS = K.DEPTHS                              # [20,25,30,35,40,50]
KGRID = [5, 10, 15, 20]
HGRID = [1, 2, 3, 4, 5, 7, 10]
NEU = ['N0', 'NS', 'NI', 'NSI']


def _sid(sp):
    return F.fid(sp)


def core_id(c):
    """核的规范 ID。默认参数时退化成 E6e 的名字 (便于对锚)。"""
    tag = ''
    parts = []
    for sp in c.get('comps', []) + ([c['x']] if c.get('x') else []) + c.get('ys', []):
        if _sid(sp) != _sid(DEF[sp['role']]):
            parts.append(_sid(sp))
    if c.get('ws') is not None:
        parts.append('w' + '/'.join(str(x) for x in c['ws']))
    if c.get('neu', 'NS') != 'NS':
        parts.append('neu:' + c['neu'])
    if c.get('neu_veto') is not None and c['neu_veto'] != c.get('neu', 'NS'):
        parts.append('vneu:' + c['neu_veto'])
    if parts:
        tag = '{' + ','.join(parts) + '}'
    if c['kind'] in ('single', 'mean'):
        return '%s@%d%s' % (c['fam'], c['s'], tag)
    return '%s(%d,%d)%s' % (c['fam'], c['a'], c['b'], tag)


def cfg_id(core, veto, H=5, sup='legacy_all'):
    s = core_id(core)
    if veto:
        s += '|' + veto['vid']
    if H != 5:
        s += '@H%d' % H
    if sup != 'legacy_all':
        s += '#' + sup
    return s


def mk_core(fam, kind, s=None, a=None, b=None, comps=None, x=None, ys=None,
            ws=None, neu='NS', neu_core=None, neu_veto=None):
    return dict(fam=fam, kind=kind, s=s, a=a, b=b, comps=comps or [], x=x, ys=ys or [],
                ws=ws, neu=neu, neu_veto=neu_veto)


# ---- P54 核 (E6e 定义) 的分量角色 ----
SINGLE = {'T': 'T', 'K': 'K', 'C': 'C'}
MEANF = {'KT_mean': ['K', 'T'], 'TC_mean': ['T', 'C'], 'KTC_mean': ['K', 'T', 'C']}
DEPF = {'KT_dep': ('K', ['T']), 'CT_dep': ('C', ['T']), 'K_gate_TC': ('K', ['T', 'C'])}
AB54 = K.AB_P54


def default_core(fam, s=None, a=None, b=None, neu='NS'):
    if fam in SINGLE:
        return mk_core(fam, 'single', s=s, comps=[dict(DEF[SINGLE[fam]])], neu=neu)
    if fam in MEANF:
        return mk_core(fam, 'mean', s=s, comps=[dict(DEF[r]) for r in MEANF[fam]], neu=neu)
    xr, yr = DEPF[fam]
    return mk_core(fam, 'dep', a=a, b=b, x=dict(DEF[xr]), ys=[dict(DEF[r]) for r in yr], neu=neu)


def p54_cores():
    out = []
    for fam in SINGLE:
        for s in DEPTHS:
            out.append(default_core(fam, s=s))
    for fam in MEANF:
        for s in DEPTHS:
            out.append(default_core(fam, s=s))
    for fam in DEPF:
        for (a, b) in AB54:
            out.append(default_core(fam, a=a, b=b))
    return out


def role_slots(c):
    """核里可扫的分量槽: [(容器, 下标, 角色)]"""
    out = []
    for i, sp in enumerate(c['comps']):
        out.append(('comps', i, sp['role']))
    if c.get('x'):
        out.append(('x', 0, c['x']['role']))
    for i, sp in enumerate(c['ys']):
        out.append(('ys', i, sp['role']))
    return out


def role_variants(role, eps_grid=False):
    """一个角色的全部候选规格 (含默认)"""
    if role == 'T':
        return [F.spec('T', w) for w in GT]
    if role == 'C':
        return [F.spec('C', w) for w in GC]
    if role == 'K':
        v = [F.spec('K', w, est=e) for e in GK_EST for w in GK_W]
        if eps_grid:
            v += [F.spec('K', w, est=e, eps=x) for e in GK_EST for w in (1, 5)
                  for x in GEPS if x != 1e-4]
        return v
    if role == 'Cf':
        return [F.spec('Cf', w, base=('ratio' if w == 1 else 'diff')) for w in GCF]
    if role == 'B':
        return [F.spec('B', w) for w in GB] + [F.spec('B', w, adj=True) for w in GB]
    raise ValueError(role)


def set_slot(c, slot, sp):
    import copy
    d = copy.deepcopy(c)
    where, i, _ = slot
    if where == 'comps':
        d['comps'][i] = dict(sp)
    elif where == 'x':
        d['x'] = dict(sp)
    else:
        d['ys'][i] = dict(sp)
    return d


# ---- 否决配方 ----
def veto_hard(legs, vid=None):
    nm = vid or '+'.join('%s:k%d' % (VSHORT(sp), k) for sp, k in legs)
    return dict(vid=nm, kind='hard', legs=[(dict(sp), k) for sp, k in legs])


def VSHORT(sp):
    if sp['role'] == 'Cf':
        return 'cvr_1d' if (sp['w'] == 1 and sp.get('base') == 'ratio') else F.fid(sp)
    if sp['role'] == 'B':
        return {5: 'cr5', 20: 'cr20'}.get(sp['w'], F.fid(sp)) if not sp.get('adj') else F.fid(sp)
    if sp['role'] == 'C':
        return 'C' if sp['w'] == 20 else F.fid(sp)
    if sp['role'] == 'K':
        return 'K' if F.fid(sp) == F.fid(DK) else F.fid(sp)
    return F.fid(sp)


V_NONE = None
V_CVR = veto_hard([(DCF, 10)])
V_CR5 = veto_hard([(DB5, 10)])
V_BOTH = veto_hard([(DCF, 10), (DB5, 10)])
V_C5 = veto_hard([(DC, 5)])
V_C5CR5 = veto_hard([(DC, 5), (DB5, 10)])
V4 = [V_NONE, V_CVR, V_CR5, V_BOTH]

# ---- A12 展示锚 ----
A12 = [
    ('A01', default_core('KT_dep', a=50, b=50), V_C5),
    ('A02', default_core('KT_mean', s=30), V_C5CR5),
    ('A03', default_core('KT_dep', a=50, b=50), V_C5CR5),
    ('A04', default_core('KTC_mean', s=25), V_NONE),
    ('A05', default_core('KTC_mean', s=25), V_CVR),
    ('A06', default_core('KTC_mean', s=25), V_BOTH),
    ('A07', default_core('KTC_mean', s=30), V_BOTH),
    ('A08', default_core('T', s=30), V_C5CR5),
    ('A09', default_core('KTC_mean', s=25),
     dict(vid='cmp_mean(cvr_1d,cr5):k10', kind='composite', how='mean', k=10,
          legs=[(dict(DCF), 10), (dict(DB5), 10)])),
    ('A10', default_core('TC_mean', s=35), V_BOTH),
    ('A11', default_core('T', s=25), V_NONE),
    ('A12', default_core('KT_mean', s=30), V_NONE),
]


def weight_points():
    """37 个唯一有理权重点: {(a,b,c)/6 : a+b+c=6} 28 点 ∪ proposal 10 点归一"""
    pts = set()
    for a in range(7):
        for b in range(7 - a):
            c = 6 - a - b
            pts.add((Fraction(a, 6), Fraction(b, 6), Fraction(c, 6)))
    prop = [(1, 1, 1), (2, 1, 1), (1, 2, 1), (1, 1, 2), (3, 1, 1), (1, 3, 1), (1, 1, 3),
            (2, 2, 1), (2, 1, 2), (1, 2, 2)]
    for t in prop:
        s = sum(t)
        pts.add(tuple(Fraction(x, s) for x in t))
    return sorted(pts)


def gen_all():
    """返回 configs: list[dict(config_id, core, veto, H, layer, parent_id, controls)]"""
    cfgs = []
    seen = set()

    def add(core, veto, layer, parent_id=None, H=5, controls=(), extra=None):
        cid = cfg_id(core, veto, H)
        if cid in seen:
            return None
        seen.add(cid)
        d = dict(config_id=cid, core=core, veto=veto, H=H, layer=layer,
                 parent_id=parent_id if parent_id is not None else cid,
                 controls=list(controls), core_id=core_id(core),
                 veto_id=(veto['vid'] if veto else ''), family=core['fam'],
                 neu=core.get('neu', 'NS'))
        if extra:
            d.update(extra)

        cfgs.append(d)
        return d

    # ---- 0. P54 默认 (锚) ----
    P54 = p54_cores()
    for c in P54:
        add(c, None, 'P54_default')

    # ---- 1. P54 全 OAT ----
    for c in P54:
        pid = cfg_id(c, None)
        for slot in role_slots(c):
            for sp in role_variants(slot[2]):
                if F.fid(sp) == F.fid(DEF[slot[2]]):
                    continue
                add(set_slot(c, slot, sp), None, 'A_oat_P54', pid,
                    controls=['paired_common_domain', 'eqpos'])

    # ---- 2. A12 OAT + ε + B 复权 ----
    for nm, c, v in A12:
        pid = cfg_id(c, v)
        add(c, v, 'A12_anchor', extra=dict(anchor=nm))
        for slot in role_slots(c):
            for sp in role_variants(slot[2], eps_grid=True):
                if F.fid(sp) == F.fid(DEF[slot[2]]):
                    continue
                add(set_slot(c, slot, sp), v, 'A_oat_A12', pid,
                    controls=['paired_common_domain', 'eqpos'], extra=dict(anchor=nm))
        if v:
            for li, (lsp, lk) in enumerate(v['legs']):
                for sp in role_variants(lsp['role']):
                    if F.fid(sp) == F.fid(lsp):
                        continue
                    legs = [(dict(x), kk) for x, kk in v['legs']]
                    legs[li] = (dict(sp), lk)
                    nv = (veto_hard(legs) if v['kind'] == 'hard'
                          else dict(v, legs=legs,
                                    vid='cmp_%s(%s):k%d' % (v['how'],
                                                            ','.join(VSHORT(x) for x, _ in legs), v['k'])))
                    add(c, nv, 'A_veto_window', pid,
                        controls=['coretrim_matchN', 'eqpos'], extra=dict(anchor=nm))

    # ---- 3. 二元联合 ----
    for nm, c, v in A12:
        roles = [s[2] for s in role_slots(c)]
        pid = cfg_id(c, v)
        if 'T' in roles and 'C' in roles:                    # T×C 5×5
            st = [s for s in role_slots(c) if s[2] == 'T'][0]
            sc = [s for s in role_slots(c) if s[2] == 'C'][0]
            for wt in GT:
                for wc in GC:
                    c2 = set_slot(set_slot(c, st, F.spec('T', wt)), sc, F.spec('C', wc))
                    add(c2, v, 'A_TxC', pid, controls=['paired_common_domain'],
                        extra=dict(anchor=nm))
        if 'C' in roles and v and any(l[0]['role'] == 'Cf' for l in v['legs']):   # 慢C × 快C
            sc = [s for s in role_slots(c) if s[2] == 'C'][0]
            li = [i for i, l in enumerate(v['legs']) if l[0]['role'] == 'Cf'][0]
            for wc in GC:
                for wf in GCF:
                    legs = [(dict(x), kk) for x, kk in v['legs']]
                    legs[li] = (F.spec('Cf', wf, base=('ratio' if wf == 1 else 'diff')), legs[li][1])
                    nv = (veto_hard(legs) if v['kind'] == 'hard'
                          else dict(v, legs=legs,
                                    vid='cmp_%s(%s):k%d' % (v['how'],
                                                            ','.join(VSHORT(x) for x, _ in legs), v['k'])))
                    add(set_slot(c, sc, F.spec('C', wc)), nv, 'A_slowC_x_fastC', pid,
                        controls=['coretrim_matchN'],
                        extra=dict(anchor=nm, same_window=(wc == wf)))
        if v and any(l[0]['role'] == 'Cf' for l in v['legs']) and \
           any(l[0]['role'] == 'B' for l in v['legs']):                          # 快C × B
            lf = [i for i, l in enumerate(v['legs']) if l[0]['role'] == 'Cf'][0]
            lb = [i for i, l in enumerate(v['legs']) if l[0]['role'] == 'B'][0]
            for wf in GCF:
                for wb in GB:
                    legs = [(dict(x), kk) for x, kk in v['legs']]
                    legs[lf] = (F.spec('Cf', wf, base=('ratio' if wf == 1 else 'diff')), legs[lf][1])
                    legs[lb] = (F.spec('B', wb), legs[lb][1])
                    nv = (veto_hard(legs) if v['kind'] == 'hard'
                          else dict(v, legs=legs,
                                    vid='cmp_%s(%s):k%d' % (v['how'],
                                                            ','.join(VSHORT(x) for x, _ in legs), v['k'])))
                    add(c, nv, 'A_fastC_x_B', pid, controls=['coretrim_matchN'],
                        extra=dict(anchor=nm))

    # ---- 4. KTC 五维联合模板 (1,296) ----
    for wt in (40, 60, 90):
        for wc in (10, 20, 40):
            for wk in (1, 3, 5):
                for s in (25, 30, 35):
                    c = mk_core('KTC_mean', 'mean', s=s,
                                comps=[F.spec('K', wk, est='MA'), F.spec('T', wt), F.spec('C', wc)])
                    vs = [None]
                    vs += [veto_hard([(F.spec('Cf', w, base=('ratio' if w == 1 else 'diff')), 10)])
                           for w in (1, 2, 3)]
                    vs += [veto_hard([(F.spec('B', w), 10)]) for w in (3, 5, 10)]
                    vs += [veto_hard([(F.spec('Cf', a, base=('ratio' if a == 1 else 'diff')), 10),
                                      (F.spec('B', b), 10)])
                           for a in (1, 2, 3) for b in (3, 5, 10)]
                    for v in vs:
                        add(c, v, 'A_KTC_template',
                            cfg_id(mk_core('KTC_mean', 'mean', s=s,
                                           comps=[dict(DK), dict(DT_), dict(DC)]), v),
                            controls=['paired_common_domain'])

    # ---- 5. 分量权重 (888) ----
    WP = weight_points()
    for ws in WP:
        for s in DEPTHS:
            c = mk_core('KTC_mean', 'mean', s=s,
                        comps=[dict(DK), dict(DT_), dict(DC)], ws=list(ws))
            for v in V4:
                add(c, v, 'A_weights',
                    cfg_id(mk_core('KTC_mean', 'mean', s=s,
                                   comps=[dict(DK), dict(DT_), dict(DC)]), v),
                    controls=['paired_common_domain'],
                    extra=dict(n_zero_weight=sum(1 for x in ws if x == 0)))

    # ---- 6. 否决强度 k 平台 (54 × 25 = 1,350) ----
    for c in P54:
        pid = cfg_id(c, None)
        for kf in [0] + KGRID:
            for kb in [0] + KGRID:
                legs = []
                if kf:
                    legs.append((dict(DCF), kf))
                if kb:
                    legs.append((dict(DB5), kb))
                v = veto_hard(legs) if legs else None
                add(c, v, 'A_k_platform', pid,
                    controls=(['coretrim_matchN', 'eqpos'] if legs else []),
                    extra=dict(k_fastC=kf, k_B=kb))

    # ---- 7. 深度补档 15 / 60 ----
    for s in (15, 60):
        c = mk_core('KTC_mean', 'mean', s=s, comps=[dict(DK), dict(DT_), dict(DC)])
        for v in V4:
            add(c, v, 'A_depth_extra', controls=['paired_common_domain'])

    # ---- 8. 持有期 H (84) ----
    for nm, c, v in A12:
        for H in HGRID:
            add(c, v, 'A_horizon', cfg_id(c, v), H=H, extra=dict(anchor=nm, h=H))

    # ---- 9. 中性化 N0/NS/NI/NSI ----
    for nm, c, v in A12:
        pid = cfg_id(c, v)
        for md in NEU:
            if md == 'NS':
                continue
            c2 = dict(c); c2['neu'] = md; c2['neu_veto'] = None
            add(c2, v, 'A_neutralization', pid, controls=['paired_common_domain'],
                extra=dict(anchor=nm, neu_scope='all'))
    for nm in ('A05', 'A07', 'A01', 'A02'):
        ent = [x for x in A12 if x[0] == nm][0]
        _, c, v = ent
        pid = cfg_id(c, v)
        for md in NEU:
            if md == 'NS':
                continue
            c2 = dict(c); c2['neu'] = md; c2['neu_veto'] = 'NS'
            add(c2, v, 'A_neutralization_split', pid,
                extra=dict(anchor=nm, neu_scope='core_only'))
            if v:
                c3 = dict(c); c3['neu'] = 'NS'; c3['neu_veto'] = md
                add(c3, v, 'A_neutralization_split', pid,
                    extra=dict(anchor=nm, neu_scope='veto_only'))
    missing = sorted({c['parent_id'] for c in cfgs} - seen)
    if missing:
        raise RuntimeError('有 %d 个被引用的父配置未展开: %s' % (len(missing), missing[:5]))
    return cfgs


if __name__ == '__main__':
    cf = gen_all()
    import collections
    cnt = collections.Counter(c['layer'] for c in cf)
    print('总配置 (去重后) %d' % len(cf))
    for k_, v in sorted(cnt.items(), key=lambda x: -x[1]):
        print('  %-26s %5d' % (k_, v))
    ctrl = collections.Counter()
    for c in cf:
        for x in c['controls']:
            ctrl[x] += 1
    print('对照:')
    for k_, v in ctrl.items():
        print('  %-24s %5d  (eqpos 产生 2 条评估)' % (k_, v))
    ncore = len(set(c['core_id'] + '|' + str(c['core'].get('neu')) for c in cf))
    print('唯一核 %d' % ncore)
    nev = len(cf) + ctrl['coretrim_matchN'] + 2 * ctrl['eqpos'] + 2 * ctrl['paired_common_domain']
    print('总评估次数 (含对照) 约 %d /段' % nev)
    wp = weight_points()
    print('权重点 %d (前 3: %s)' % (len(wp), [tuple(str(y) for y in x) for x in wp[:3]]))
    print('格位数 vs 去重后新增: KTC模板 1296 -> %d; 权重 %d×6×4=%d -> %d; k平台 54×25=1350 -> %d; H 12×7=84 -> %d'
          % (cnt['A_KTC_template'], len(wp), len(wp)*24, cnt['A_weights'],
             cnt['A_k_platform'], cnt['A_horizon']))
