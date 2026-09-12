#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 推导段实验的描述符枚举 + 冻结 (brief §5, plan §3.2/§4)。

**只从 route_manifest.json 的 routed 行编译** (plan §2.1 末段)。不遍历 U74。

方向的坑 (复盘 #33 的直接后果): 卡上写的是【经济方向】(quiet / surge / up / down),
但每个键的源符号不同 —— abn_turnover / parkinson_vol / reversal_skip1 / cmf_change_neg
四个键源函数已取负, 其余没有。所以
    want_source_high = (econ_dir 是"高经济量") XOR (该键源符号是 negated)
这条必须显式算, 不能按名字或凭印象填。见 want_high() 与 e6h_expand_anchors。

描述符 ID 必须【单射】(E6g 的 F3 教训: core_id_g 对换腿位置不敏感, 1,544 个塌成 992)。
这里用 `parent|route|role|k1=v1,k2=v2,...` 有序键值串, 构造上单射, 并在冻结时断言。
"""
from __future__ import annotations
import os
import sys
import json
import hashlib
import itertools

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H

RES = H.RES

# 每个母体的核心腿顺序 (用于 SLOT 的 leg_idx), 与 e6e/e6f 的 comps 顺序一致
LEGS_OF = {'R1': ['K', 'T'],            # 两段式: K 第一关, T 第二关
           'R2': ['K', 'T'],
           'A06': ['K', 'T', 'C'],
           'A08': ['T'],
           'T25': ['T'],
           'A07': ['K', 'T', 'C'],
           'A03': ['K', 'T']}
# 焦点否决腿的位置 (veto legs 的下标)
FOCAL_OF = {'R2': dict(C=0, cr5=1), 'A06': dict(cvr_1d=0, cr5=1),
            'A08': dict(C=0, cr5=1), 'R1': dict(C=0)}

_SEM = None


def sem():
    global _SEM
    if _SEM is None:
        _SEM = pd.read_csv(os.path.join(RES, 'registry', 'feature_semantics.csv')
                           ).set_index('key')
    return _SEM


def is_negated(key):
    return str(sem().loc[key, 'source_sign']) == 'negated'


def want_high(key, econ_high):
    """该键的【源值】是否应取高端。econ_high=True 表示要"经济量高"的那一端。
       源符号取负的键要翻过来。"""
    return bool(econ_high) != bool(is_negated(key))


def did(parent, route, role, **params):
    ps = ','.join('%s=%s' % (k, params[k]) for k in sorted(params))
    return '%s|%s|%s|%s' % (parent, route, role, ps)


# ---------------------------------------------------------------- 逐卡展开
def exp_MT(rt):
    out = []
    news = [m for m in rt['measurements'] if m != 'turnover_volatility_60d']
    parents = rt['parents'] + rt.get('migrate_parents', [])
    for p in parents:
        if 'T' not in LEGS_OF.get(p, []):
            continue
        li = LEGS_OF[p].index('T')
        out.append(dict(descriptor_id=did(p, rt['route_id'], 'SLOT_FALLBACK',
                                          new='src', alpha=0),
                        route_id=rt['route_id'], parent=p, role='SLOT_FALLBACK',
                        op='slot', leg_idx=li, new_key=None, alpha=0.0,
                        policy='FALLBACK', is_identity=True))
        for m, pol, al in itertools.product(news, ('FALLBACK', 'REPLACE'),
                                            (0.25, 0.5, 1.0)):
            out.append(dict(descriptor_id=did(p, rt['route_id'], 'SLOT_' + pol,
                                              new=m, alpha=al),
                            route_id=rt['route_id'], parent=p, role='SLOT_' + pol,
                            op='slot', leg_idx=li, new_key=m, alpha=al,
                            policy=pol, is_identity=False))
    return out


def exp_MC(rt):
    out = []
    news = [m for m in rt['measurements'] if m != 'CVR_20d']
    # A06: 换核心 C 位
    p = 'A06'
    li = LEGS_OF[p].index('C')
    out.append(dict(descriptor_id=did(p, rt['route_id'], 'SLOT_FALLBACK',
                                      new='src', alpha=0),
                    route_id=rt['route_id'], parent=p, role='SLOT_FALLBACK',
                    op='slot', leg_idx=li, new_key=None, alpha=0.0,
                    policy='FALLBACK', is_identity=True))
    for m, pol, al in itertools.product(news, ('FALLBACK', 'REPLACE'), (0.25, 0.5, 1.0)):
        out.append(dict(descriptor_id=did(p, rt['route_id'], 'SLOT_' + pol,
                                          new=m, alpha=al),
                        route_id=rt['route_id'], parent=p, role='SLOT_' + pol,
                        op='slot', leg_idx=li, new_key=m, alpha=al, policy=pol,
                        is_identity=False))
    # R2: 换 C 否决位 (四对照: none / original / new / both)
    p, fi = 'R2', FOCAL_OF['R2']['C']
    for mode in ('none', 'original'):
        out.append(dict(descriptor_id=did(p, rt['route_id'], 'FOCAL_' + mode.upper(),
                                          focal='C'),
                        route_id=rt['route_id'], parent=p, role='FOCAL_' + mode.upper(),
                        op='focal', focal_idx=fi, mode=mode, new_key=None, k=None,
                        is_identity=(mode == 'original')))
    for m, k, both in itertools.product(news, (5, 10), (False, True)):
        out.append(dict(descriptor_id=did(p, rt['route_id'], 'FOCAL_REPLACE',
                                          new=m, k=k, both=int(both)),
                        route_id=rt['route_id'], parent=p, role='FOCAL_REPLACE',
                        op='focal_replace', focal_idx=fi, mode='replace', new_key=m,
                        k=k, keep_original=both, is_identity=False))
    return out


def exp_EV(rt):
    out = []
    # surge = 经济量(换手相对自身历史的比值)【高】; quiet = 低。
    # 注意 route_id 是 'E-V-surge-price' / 'E-V-quiet-price', 结尾是 '-price',
    # 所以不能用 endswith('surge') —— 那样两张卡会拿到同一个方向 (本行曾经就是这个 bug,
    # 由 main() 末尾的方向自检打印抓出)。
    rid = rt['route_id']
    assert ('surge' in rid) ^ ('quiet' in rid), 'E-V 卡必须且只能标一个方向: %s' % rid
    econ_high = ('surge' in rid)
    vols = [m for m in rt['measurements'] if m not in ('cum_return_20d',)]
    prices = rt['grids']['price_cond']
    parents = rt['parents'] + rt.get('migrate_parents', [])
    roles = [('ADD', e) for e in (0.10, 0.25, 0.50)] + \
            [('SWAP', e) for e in (0.10, 0.25, 0.50)] + [('CONJ', None)]
    conds = []
    for pc in prices:
        for v in vols:
            conds.append(dict(cond_mode='price_only', price=pc, vol=v, q=None))
    for v in vols:
        for q in (0.2, 0.3):
            conds.append(dict(cond_mode='volume_only', price=None, vol=v, q=q))
    for pc in prices:
        for v in vols:
            for q in (0.2, 0.3):
                conds.append(dict(cond_mode='joint', price=pc, vol=v, q=q))
    for p in parents:
        out.append(dict(descriptor_id=did(p, rt['route_id'], 'ADD', eta=0),
                        route_id=rt['route_id'], parent=p, role='ADD', op='add',
                        eta=0.0, is_identity=True, cond_mode='none',
                        vol_key=None, price_cond=None, q=None,
                        want_source_high=None))
        for c, (role, eta) in itertools.product(conds, roles):
            out.append(dict(
                descriptor_id=did(p, rt['route_id'], role,
                                  cm=c['cond_mode'], pc=c['price'] or '-',
                                  v=c['vol'], q=c['q'] if c['q'] is not None else '-',
                                  eta=eta if eta is not None else '-'),
                route_id=rt['route_id'], parent=p, role=role,
                op=role.lower(), eta=eta, is_identity=False,
                cond_mode=c['cond_mode'], vol_key=c['vol'], price_cond=c['price'],
                q=c['q'], want_source_high=want_high(c['vol'], econ_high)))
    return out


def exp_EP(rt):
    out = []
    states = [('intraday_ret_consistency_5d', 'le', 0.2),
              ('intraday_ret_consistency_5d', 'ge', 0.8),
              ('positive_day_ratio_5d', 'le', 0.2),
              ('positive_day_ratio_5d', 'ge', 0.8),
              ('agreement_count_5d', 'le', 1),
              ('agreement_count_5d', 'ge', 4),
              ('daynight_divergence', 'eq', 0),
              ('daynight_divergence', 'eq', 1)]
    for p in rt['parents']:
        fi = FOCAL_OF[p]['cr5']
        out.append(dict(descriptor_id=did(p, rt['route_id'], 'FOCAL_ORIGINAL', focal='cr5'),
                        route_id=rt['route_id'], parent=p, role='FOCAL_ORIGINAL',
                        op='focal', focal_idx=fi, mode='original', state=None,
                        k=None, is_identity=True))
        out.append(dict(descriptor_id=did(p, rt['route_id'], 'FOCAL_NONE', focal='cr5'),
                        route_id=rt['route_id'], parent=p, role='FOCAL_NONE',
                        op='focal', focal_idx=fi, mode='none', state=None,
                        k=None, is_identity=False))
        for (sk, cmp_, th), mode, k in itertools.product(states, ('enable', 'exempt'),
                                                         (5, 10)):
            out.append(dict(
                descriptor_id=did(p, rt['route_id'], 'FOCAL_' + mode.upper(),
                                  s=sk, c=cmp_, th=th, k=k),
                route_id=rt['route_id'], parent=p, role='FOCAL_' + mode.upper(),
                op='focal_cond', focal_idx=fi, mode=mode, state_key=sk,
                state_cmp=cmp_, state_th=th, k=k, is_identity=False))
    return out


def exp_RO(rt):
    out = []
    meas = rt['measurements']
    for p in rt['parents']:
        out.append(dict(descriptor_id=did(p, rt['route_id'], 'SOFT_DEWEIGHT', lam=0),
                        route_id=rt['route_id'], parent=p, role='SOFT_DEWEIGHT',
                        op='soft', lam=0.0, is_identity=True, risk_key=None,
                        k=None, want_source_high=None))
        for m, k, hi in itertools.product(meas, (5, 10), (True, False)):
            out.append(dict(
                descriptor_id=did(p, rt['route_id'], 'VETO_IN_B',
                                  m=m, k=k, hi=int(hi)),
                route_id=rt['route_id'], parent=p, role='VETO_IN_B',
                op='veto_in_b', risk_key=m, k=k, want_source_high=hi,
                is_identity=False))
            for lam in (0.5, 1.0):
                out.append(dict(
                    descriptor_id=did(p, rt['route_id'], 'SOFT_DEWEIGHT',
                                      m=m, k=k, hi=int(hi), lam=lam),
                    route_id=rt['route_id'], parent=p, role='SOFT_DEWEIGHT',
                    op='soft', risk_key=m, k=k, want_source_high=hi, lam=lam,
                    is_identity=False))
    return out


def exp_IPup(rt):
    out = []
    for p in rt['parents']:
        out.append(dict(descriptor_id=did(p, rt['route_id'], 'ADD', eta=0),
                        route_id=rt['route_id'], parent=p, role='ADD', op='add',
                        eta=0.0, is_identity=True, w=None, q=None))
        for w, q, eta, role in itertools.product((5, 20), (0.2, 0.3),
                                                 (0.10, 0.25, 0.50), ('ADD', 'SWAP')):
            out.append(dict(
                descriptor_id=did(p, rt['route_id'], role, w=w, q=q, eta=eta),
                route_id=rt['route_id'], parent=p, role=role, op=role.lower(),
                eta=eta, w=w, q=q, is_identity=False, ip_dir='up'))
    return out


def exp_IPdown(rt):
    out = []
    for p in rt['parents']:
        for w, k in itertools.product((5, 20), (5, 10)):
            out.append(dict(
                descriptor_id=did(p, rt['route_id'], 'VETO_IN_B', w=w, k=k),
                route_id=rt['route_id'], parent=p, role='VETO_IN_B',
                op='ip_down_veto', w=w, k=k, is_identity=False))
    return out


def exp_LQ(rt):
    out = []
    for p in rt['parents']:
        out.append(dict(descriptor_id=did(p, rt['route_id'], 'MARGIN', e=0),
                        route_id=rt['route_id'], parent=p, role='MARGIN', op='margin',
                        e=0.0, is_identity=True, liq_key=None, order=None))
        for m, e, od in itertools.product(rt['measurements'], (0.10, 0.25, 0.50),
                                          rt['grids']['order']):
            out.append(dict(
                descriptor_id=did(p, rt['route_id'], 'MARGIN', m=m, e=e, o=od),
                route_id=rt['route_id'], parent=p, role='MARGIN', op='margin',
                liq_key=m, e=e, order=od, is_identity=False))
    return out


EXPANDERS = {
    'M-T-tcv-vs-t60': exp_MT, 'M-C-position-window': exp_MC,
    'E-V-quiet-price': exp_EV, 'E-V-surge-price': exp_EV,
    'E-P-path-conditional-focal': exp_EP, 'R-O-overnight-risk': exp_RO,
    'I-P-peer-up-laggard': exp_IPup, 'I-P-peer-down-risk': exp_IPdown,
    'L-Q-margin-liquidity': exp_LQ,
}


def all_descriptors():
    rm = json.load(open(os.path.join(RES, 'registry', 'route_manifest.json')))
    rows = []
    for rt in rm['routes']:
        fn = EXPANDERS.get(rt['route_id'])
        if fn is None:
            raise KeyError('路线 %s 没有展开函数' % rt['route_id'])
        rows.extend(fn(rt))
    return rows


def main():
    rows = all_descriptors()
    d = pd.DataFrame(rows)
    ids = list(d['descriptor_id'])
    assert len(ids) == len(set(ids)), \
        '描述符 ID 不单射: %d 个 -> %d 个唯一 (E6g F3 同类错)' % (len(ids), len(set(ids)))
    h = hashlib.sha256('\n'.join(sorted(ids)).encode('utf-8')).hexdigest()
    by_route = d.groupby('route_id').size().to_dict()
    by_role = d.groupby('role').size().to_dict()
    man = dict(round='E6h', kind='derivation_descriptors',
               total=len(d), unique_ids=len(set(ids)),
               n_identity=int(d['is_identity'].sum()),
               by_route=by_route, by_role=by_role,
               sha256=h,
               segments=list(H.DERIV_SEGS),
               total_config_segments=len(d) * len(H.DERIV_SEGS),
               note=('只从 route_manifest 的 routed 行编译; 不遍历 U74。'
                     'ID 用有序键值串, 构造上单射, 已断言。'))
    os.makedirs(os.path.join(RES, 'checks'), exist_ok=True)
    with open(os.path.join(RES, 'checks', 'derivation_manifest_frozen.json'), 'w') as fh:
        json.dump(man, fh, indent=1, ensure_ascii=False)
    d.to_csv(os.path.join(RES, 'checks', 'derivation_descriptors.csv'), index=False)

    print('== E6h 推导段描述符冻结 ==')
    print(' 总数 %d (唯一 %d), 其中 identity 端点 %d' % (len(d), len(set(ids)),
                                                         man['n_identity']))
    print(' 两段合计 config-segment: %d' % man['total_config_segments'])
    print(' sha256 %s' % h[:16])
    print()
    print(' 逐路线:')
    for k in sorted(by_route, key=lambda x: -by_route[x]):
        print('   %-28s %5d' % (k, by_route[k]))
    print()
    print(' 逐角色:')
    for k in sorted(by_role, key=lambda x: -by_role[x]):
        print('   %-20s %5d' % (k, by_role[k]))
    print()
    # 方向自检: 把 want_source_high 的推导打印出来给人复核
    ev = d[d.route_id.str.startswith('E-V') & d.want_source_high.notna()]
    if len(ev):
        chk = ev.groupby(['route_id', 'vol_key']).want_source_high.agg(
            lambda x: sorted(set(x))).reset_index()
        print(' E-V 的源方向推导 (econ 方向 XOR 源符号):')
        for _, r in chk.iterrows():
            neg = is_negated(r['vol_key'])
            print('   %-18s %-20s 源符号=%-8s -> 取源值高端 %s'
                  % (r['route_id'].replace('E-V-', ''), r['vol_key'],
                     'negated' if neg else 'as_is', r['want_source_high']))
        # 阻断断言: 同一个键在 quiet 与 surge 两张卡上【必须】方向相反
        piv = chk.pivot_table(index='vol_key', columns='route_id',
                              values='want_source_high',
                              aggfunc=lambda x: list(x)[0][0])
        bad = [k for k, r in piv.iterrows()
               if r['E-V-quiet-price'] == r['E-V-surge-price']]
        assert not bad, ('quiet 与 surge 是相反的经济方向, 但这些键拿到了相同的源方向: %s'
                         % bad)
        # 且源符号取负的键与不取负的键, 在同一张卡上方向必须相反
        for rid in ('E-V-quiet-price', 'E-V-surge-price'):
            negd = {k: piv.loc[k, rid] for k in piv.index if is_negated(k)}
            asis = {k: piv.loc[k, rid] for k in piv.index if not is_negated(k)}
            if negd and asis:
                assert set(negd.values()) != set(asis.values()), \
                    ('%s: 取负键与不取负键的源方向必须相反 (negated=%s, as_is=%s)'
                     % (rid, negd, asis))
        print('   方向断言通过: quiet/surge 相反, 且 negated/as_is 在同一卡内相反')


if __name__ == '__main__':
    main()
