#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 描述符展开 (纯组合逻辑, 不看任何收益、不碰数据) + H manifest 冻结。

brief 硬约束 ② 要求 H manifest 在读到 T0-74 结果前冻结; T0-74 与 H1–H4 并行,
所以必须在【任何东西启动之前】把 H0–H5 / B2 的完整枚举哈希进 checks/H_manifest_frozen.json。
计数与 brief 声明的 1,544 / 1,100 / 600 出 diff 即报, 不凑数、不删格。
"""
import os, sys, json, hashlib, itertools
from fractions import Fraction
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6f_desc as D
import e6g_core as G
import e6g_desc as GD

KTC = [K.FK, K.FT, K.FC]
KT = [K.FK, K.FT]
V_BOTH = 'cvr_1d:k10+cr5:k10'
V_C5CR5 = 'C:k5+cr5:k10'
DIRS = ('hi', 'lo')


def par(core_name, vname):
    """母体 config_id: 同一否决状态下的原核。"""
    return core_name + ('|' + vname if vname else '')


def _row(block, cfg_id, core, veto, note, **kw):
    d = dict(block=block, descriptor_id=cfg_id, note=note)
    d.update(kw)
    d['_core'], d['_veto'] = core, veto          # 执行器要用; 写 CSV 前丢掉
    pf = GD.path_fields(core, veto, H=kw.get('H', K.HOLD), sup=kw.get('support', 'legacy_all'),
                        sel=kw.get('sel'), buf=kw.get('buf'), tie=kw.get('tie', 'src'),
                        state=kw.get('state'), seed=kw.get('seed'))
    d['path_key'] = G.path_key(pf)
    lin = GD.core_lineage(core) | GD.veto_lineage(veto)
    d['lineage'] = lin.tag()
    d['new40_blood'] = lin.new40
    return d


def wcore(fam, depth, keys, ws, dirs=None):
    return GD.mk_core_g(fam, 'mean', s=depth, keys=keys, ws=ws, dirs=dirs)


def h0():
    """固定仪器桥: KT_dep / CT_dep 的四个 (a,b) 裸核及其 C:k5+cr5:k10, SRC / QEDGE 并排。"""
    out = []
    for fam in ('KT_dep', 'CT_dep'):
        for ab in ((45, 45), (50, 50), (55, 55), (65, 65)):
            c = D.default_core(fam, a=ab[0], b=ab[1])
            for vname in (None, V_C5CR5):
                v = GD.parse_veto(vname) if vname else None
                for sel in ('SRC', 'QEDGE'):
                    c2 = dict(c); c2['sel'] = sel; c2['dirs'] = ['hi']; c2['tfs'] = ['identity']
                    out.append(_row('H0', GD.cfg_id_g(c2, v, sel=sel), c2, v,
                                    '仪器桥 %s(%d,%d) %s %s' % (fam, ab[0], ab[1],
                                                               vname or '裸核', sel),
                                    sel=sel))
    # 固定展示组也进 H0 (作参照身份, 不是候选)
    for lab, cid, note in G.DISPLAY:
        cfg = GD.parse_cfg(cid)
        out.append(_row('H0', cid, cfg['core'], cfg['veto'], '固定展示组 %s: %s' % (lab, note),
                        display=lab))
    return out


def h1():
    """第四腿 / 换腿。brief §5: 原始描述符 1,544。"""
    out = []
    # (a) KTC 母体 A06@25 / A07@30
    for pname, dep in (('A06', 25), ('A07', 30)):
        for J in G.J_KTC:
            spJ = GD.spec_of_key(J)
            for dr in DIRS:
                # 第四腿 alpha in {1/8, 1/4}
                for al in (Fraction(1, 8), Fraction(1, 4)):
                    ws = [(1 - al) / 3] * 3 + [al]
                    c = wcore('KTC_mean', dep, KTC + [J], ws, dirs=['hi'] * 3 + [dr])
                    for vname in (V_BOTH, None):
                        v = GD.parse_veto(vname) if vname else None
                        out.append(_row('H1', GD.cfg_id_g(c, v), c, v,
                                        '%s 第四腿 %s dir=%s a=%s %s'
                                        % (pname, J, dr, al, vname or '裸核'),
                                        parent=pname, J=J, dirJ=dr, alpha=float(al),
                                        mode='add4',
                                        parent_cfg=par('KTC_mean@%d' % dep, vname)))
                # 换腿: 替 K / T / C
                for pos, slot in enumerate(('K', 'T', 'C')):
                    keys = list(KTC)
                    keys[pos] = J
                    drs = ['hi', 'hi', 'hi']
                    drs[pos] = dr
                    c = GD.mk_core_g('KTC_mean', 'mean', s=dep, keys=keys, dirs=drs)
                    for vname in (V_BOTH, None):
                        v = GD.parse_veto(vname) if vname else None
                        out.append(_row('H1', GD.cfg_id_g(c, v), c, v,
                                        '%s 换腿 %s<-%s dir=%s %s'
                                        % (pname, slot, J, dr, vname or '裸核'),
                                        parent=pname, J=J, dirJ=dr, mode='replace_' + slot,
                                        parent_cfg=par('KTC_mean@%d' % dep, vname)))
    # (b) R2 的 KT 核加第三腿, J in J_KT (33, 含 C), alpha in {1/8, 1/3}
    for J in G.J_KT:
        for dr in DIRS:
            for al in (Fraction(1, 8), Fraction(1, 3)):
                ws = [(1 - al) / 2] * 2 + [al]
                c = wcore('KT_mean', 30, KT + [J], ws, dirs=['hi', 'hi', dr])
                for vname in (V_C5CR5, None):
                    v = GD.parse_veto(vname) if vname else None
                    out.append(_row('H1', GD.cfg_id_g(c, v), c, v,
                                    'R2 第三腿 %s dir=%s a=%s %s' % (J, dr, al, vname or '裸核'),
                                    parent='R2', J=J, dirJ=dr, alpha=float(al), mode='add3_R2',
                                    parent_cfg=par('KT_mean@30', vname)))
    return out


def h2():
    """K/T/C 的时序变换。三种非 identity x 两方向 x 五种角色 x {A06, R2} x 两支持集。"""
    out = []
    TFS = ('delta5', 'delta20', 'zprior60')
    for pname, fam, dep, legs, vname in (('A06', 'KTC_mean', 25, KTC, V_BOTH),
                                         ('R2', 'KT_mean', 30, KT, V_C5CR5)):
        for comp in KTC:
            for tf in TFS:
                for dr in DIRS:
                    for role in ('replace', 'add_1_8', 'add_1_np1', 'veto_k5', 'veto_k10'):
                        if role == 'replace' and comp not in legs:
                            continue                      # R2 没有 C 腿 -> not_applicable
                        for sup in ('legacy_all', 'history_warmed'):
                            if role == 'replace':
                                keys = list(legs)
                                i = keys.index(comp)
                                drs = ['hi'] * len(keys); drs[i] = dr
                                tfs = ['identity'] * len(keys); tfs[i] = tf
                                c = GD.mk_core_g(fam, 'mean', s=dep, keys=keys,
                                                 dirs=drs, tfs=tfs)
                                v = GD.parse_veto(vname)
                            elif role.startswith('add'):
                                al = (Fraction(1, 8) if role == 'add_1_8'
                                      else Fraction(1, len(legs) + 1))
                                ws = [(1 - al) / len(legs)] * len(legs) + [al]
                                c = wcore(fam, dep, legs + [comp], ws,
                                          dirs=['hi'] * len(legs) + [dr])
                                c['tfs'] = ['identity'] * len(legs) + [tf]
                                v = GD.parse_veto(vname)
                            else:
                                kk = int(role.split('k')[1])
                                c = GD.mk_core_g(fam, 'mean', s=dep, keys=legs)
                                v = GD.parse_veto(vname)
                                # vid 必须带方向与变换, 否则 dir=hi/lo 两条会撞成同一条路径
                                v = dict(v, vid='%s+%s.%s^%s:k%d'
                                         % (v['vid'], GD.short_of_key(comp), tf, dr, kk),
                                         legs=v['legs'] + [(GD.spec_of_key(comp), kk)])
                                v['dir'], v['tf'] = dr, tf
                            out.append(_row('H2', GD.cfg_id_g(c, v, sup=sup), c, v,
                                            '%s %s %s dir=%s %s sup=%s'
                                            % (pname, comp, tf, dr, role, sup),
                                            parent=pname, comp=comp, tf=tf, dirJ=dr,
                                            role=role, support=sup,
                                            parent_cfg=par('%s@%d' % (fam, dep), vname)))
    return out


def h4a():
    """四核 x 11 深度 x 两否决各 k in {OFF,3,4,5,10}。brief §5: 1,100。"""
    out = []
    DEPTHS = [15, 20, 22.5, 25, 30, 35, 40, 42.5, 45, 47.5, 50]
    KS = ['OFF', 3, 4, 5, 10]
    CORES = [('KT_mean', KT, ('C', 'cr5')), ('KTC_mean', KTC, ('cvr_1d', 'cr5')),
             ('T', [K.FT], ('C', 'cr5')), ('KT_dep', KT, ('C', 'cr5'))]
    for fam, legs, (v1, v2) in CORES:
        for d in DEPTHS:
            for k1 in KS:
                for k2 in KS:
                    if fam == 'KT_dep':
                        c = D.default_core('KT_dep', a=50, b=2 * d)
                        c = dict(c); c['dirs'] = ['hi']; c['tfs'] = ['identity']
                    elif fam == 'T':
                        c = GD.mk_core_g('T', 'single', s=d, keys=legs)
                    else:
                        c = GD.mk_core_g(fam, 'mean', s=d, keys=legs)
                    c['sel'] = 'RANKBUDGET'
                    c['depth'] = d
                    vn = '+'.join(['%s:k%d' % (a, b) for a, b in ((v1, k1), (v2, k2))
                                   if b != 'OFF'])
                    v = GD.parse_veto(vn) if vn else None
                    out.append(_row('H4a', GD.cfg_id_g(c, v, sel='RANKBUDGET'), c, v,
                                    '%s d=%s %s:%s %s:%s' % (fam, d, v1, k1, v2, k2),
                                    core_fam=fam, depth=d, k1=str(k1), k2=str(k2),
                                    sel='RANKBUDGET'))
    return out


def h4b():
    """KTC 母体角落邻域。brief §5: 600。"""
    out = []
    for kw in (1, 2, 3, 5, 10):
        for tw in (20, 30, 40, 60, 80):
            for bw in (3, 5):
                for dep in (25, 30, 35):
                    for k1 in (5, 10):
                        for k2 in (5, 10):
                            spK = F.spec('K', kw, est='MA', eps=1e-4)
                            spT = F.spec('T', tw)
                            spB = F.spec('B', bw)
                            c = dict(fam='KTC_mean', kind='mean', s=dep,
                                     comps=[spK, spT, dict(D.DC)], x=None, ys=[],
                                     ws=None, neu='NS', neu_veto=None,
                                     dirs=['hi'] * 3, tfs=['identity'] * 3,
                                     sel='SRC', depth=None)
                            vn = 'cvr_1d:k%d+%s:k%d' % (k1, F.fid(spB), k2)
                            v = D.veto_hard([(dict(D.DCF), k1), (spB, k2)], vid=vn)
                            out.append(_row('H4b', GD.cfg_id_g(c, v), c, v,
                                            'K_MA%d T%d B%d d=%d v1k%d Bk%d'
                                            % (kw, tw, bw, dep, k1, k2),
                                            kw=kw, tw=tw, bw=bw, depth=dep, k1=k1, k2=k2))
    return out


def h5():
    """四腿聚合: H1 的全部 KTC+J 四腿集合 x 六种聚合 x {完整栈, 裸核}。"""
    out = []
    # 同人数聚合控制不是经济格, 由执行器作 control_matchN 产出, 不进冻结表
    AGG = ('mean', 'median', 'worst', 'vote2', 'vote3')
    for dep in (25, 30):
        for J in G.J_KTC:
            for dr in DIRS:
                for agg in AGG:
                    c = GD.mk_core_g('KTC4_' + agg, 'mean', s=dep, keys=KTC + [J],
                                     dirs=['hi'] * 3 + [dr])
                    for vname in (V_BOTH, None):
                        v = GD.parse_veto(vname) if vname else None
                        out.append(_row('H5', GD.cfg_id_g(c, v), c, v,
                                        '四腿 %s @%d J=%s dir=%s %s'
                                        % (agg, dep, J, dr, vname or '裸核'),
                                        agg=agg, depth=dep, J=J, dirJ=dr,
                                        parent_cfg=par('KTC_mean@%d' % dep, vname)))
    return out


def b2():
    """alpha 五点曲线 + J 分量的因果 MA3/MA5。"""
    out = []
    for dep in (25, 30):
        for J in G.J_KTC:
            for dr in DIRS:
                for al in (Fraction(0), Fraction(3, 8), Fraction(1, 2)):   # 1/8, 1/4 已在 H1
                    if al == 0:
                        c = GD.mk_core_g('KTC_mean', 'mean', s=dep, keys=KTC)
                    else:
                        ws = [(1 - al) / 3] * 3 + [al]
                        c = wcore('KTC_mean', dep, KTC + [J], ws, dirs=['hi'] * 3 + [dr])
                    for vname in (V_BOTH, None):
                        v = GD.parse_veto(vname) if vname else None
                        out.append(_row('B2', GD.cfg_id_g(c, v), c, v,
                                        'alpha 曲线 @%d J=%s dir=%s a=%s %s'
                                        % (dep, J, dr, al, vname or '裸核'),
                                        depth=dep, J=J, dirJ=dr, alpha=float(al), mode='alpha',
                                        parent_cfg=par('KTC_mean@%d' % dep, vname)))
                for maw in (3, 5):
                    al = Fraction(1, 4)
                    ws = [(1 - al) / 3] * 3 + [al]
                    keys = KTC + [J]
                    c = wcore('KTC_mean', dep, keys, ws, dirs=['hi'] * 3 + [dr])
                    c['comps'][3] = GD.spec_of_key(J)
                    c['comps'][3] = dict(c['comps'][3], w=maw) if \
                        c['comps'][3].get('role') != 'F' else G.specF(J, maw)
                    for vname in (V_BOTH, None):
                        v = GD.parse_veto(vname) if vname else None
                        out.append(_row('B2', GD.cfg_id_g(c, v), c, v,
                                        'J 因果 MA%d @%d J=%s dir=%s a=1/4 %s'
                                        % (maw, dep, J, dr, vname or '裸核'),
                                        depth=dep, J=J, dirJ=dr, alpha=0.25, mode='MA%d' % maw,
                                        parent_cfg=par('KTC_mean@%d' % dep, vname)))
    return out


BLOCKS = [('H0', h0), ('H1', h1), ('H2', h2), ('H4a', h4a), ('H4b', h4b),
          ('H5', h5), ('B2', b2)]
DECLARED = {'H1': 1544, 'H4a': 1100, 'H4b': 600}


def main():
    rows = []
    counts = {}
    for name, fn in BLOCKS:
        r = fn()
        counts[name] = len(r)
        rows.extend(r)
        print('%-5s 原始描述符 %5d  唯一 ID %5d  唯一真实路径 %5d'
              % (name, len(r), len({x['descriptor_id'] for x in r}),
                 len({x['path_key'] for x in r})), flush=True)
    df = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith('_')} for r in rows])
    out = os.path.join(G.RES, 'H0')
    os.makedirs(out, exist_ok=True)
    df.to_csv(os.path.join(out, 'H_manifest.csv'), index=False)

    diff = {b: dict(declared=DECLARED[b], actual=counts[b], delta=counts[b] - DECLARED[b])
            for b in DECLARED}
    print('\n与 brief 声明的 diff:')
    for b, v in diff.items():
        print('  %-4s 声明 %5d  实际 %5d  差 %+d  %s'
              % (b, v['declared'], v['actual'], v['delta'], 'OK' if v['delta'] == 0 else '** DIFF **'))

    # NEW40 血缘必须为空: H 块只用 U35
    nb = int(df['new40_blood'].sum())
    print('\nH 块里带 NEW40 血缘的描述符: %d (必须为 0)' % nb)
    if nb:
        print(df[df['new40_blood']].head(10)[['block', 'descriptor_id', 'lineage']].to_string())

    payload = '\n'.join(sorted(df['descriptor_id'].astype(str)))
    h = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    man = dict(version=G.VERSION, frozen_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
               counts=counts, total=int(len(df)),
               unique_descriptor_ids=int(df['descriptor_id'].nunique()),
               unique_path_keys=int(df['path_key'].nunique()),
               declared_diff=diff, new40_blood_in_H=nb,
               descriptor_id_sha256=h,
               note=('H manifest 冻结于任何 T0-74 结果产生之前; 之后 H/B 只能按本表跑, '
                     '新增格必须另起 amendment 并标明是否已看过 T0-74。'))
    with open(os.path.join(G.RES, 'checks', 'H_manifest_frozen.json'), 'w') as fh:
        json.dump(man, fh, indent=1, ensure_ascii=False)
    print('\n冻结: 总计 %d 个描述符, 唯一 ID %d, 唯一真实路径 %d, sha256 %s'
          % (man['total'], man['unique_descriptor_ids'], man['unique_path_keys'], h[:16]))
    # 去重收益
    dup = df.groupby('path_key').size()
    print('可复用计算的路径 (>1 个描述符共享): %d 条, 最多共享 %d 个描述符'
          % int((dup > 1).sum()) if False else
          '可复用计算的路径 (>1 个描述符共享): %d 条, 最多共享 %d 个描述符'
          % (int((dup > 1).sum()), int(dup.max())))


if __name__ == '__main__':
    main()
