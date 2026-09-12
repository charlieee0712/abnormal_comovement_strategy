#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 守卫攻击测试 (brief §1.3 末条 + §0.2 硬约束②)。

沿 E6g 的四条 + 本轮新增四条:
  A5 重命名规则对象 (换个名字叫 ADD)
  A6 已知键条件化绕过 (用 U35 老键做条件, 但规则对象是新的)
  A7 TCV / JUMP / IND_* 未登记即用于 2019+
  A8 DEP 例外绕过另一关 (由集合契约层断言, 这里测守卫不被 route_id 欺骗)

每条测试都必须【被拒】才算通过; 另有三条"正常路径必须放行"的反向测试,
防止守卫过严把合法的 L/T 旧输入格也挡掉。
"""
from __future__ import annotations
import os
import sys
import json
import time

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6g_core as G

RES = H.RES
OUT = os.path.join(RES, 'checks')


def expect_block(name, fn, note=''):
    """fn 必须抛 GuardViolationH 才算通过。"""
    try:
        fn()
    except H.GuardViolationH as e:
        return dict(test=name, kind='must_block', ok=True, note=note, msg=str(e)[:180])
    except Exception as e:
        return dict(test=name, kind='must_block', ok=False, note=note,
                    msg='抛了别的异常: %s: %s' % (type(e).__name__, str(e)[:140]))
    return dict(test=name, kind='must_block', ok=False, note=note, msg='没有被拒 (漏网)')


def expect_pass(name, fn, note=''):
    """fn 必须不抛才算通过 (防守卫过严)。"""
    try:
        fn()
    except Exception as e:
        return dict(test=name, kind='must_pass', ok=False, note=note,
                    msg='被误拒: %s: %s' % (type(e).__name__, str(e)[:140]))
    return dict(test=name, kind='must_pass', ok=True, note=note, msg='')


def main():
    os.makedirs(OUT, exist_ok=True)
    H.load_approval()                       # 确保是"记录 B 未批准"状态
    assert not H._APPROVAL['loaded'], '开工时不应已有记录 B 批准文件'
    r = []

    # ---------- 必须被拒 ----------
    r.append(expect_block(
        'A1_new40_key_post2018',
        lambda: H.guard_h(['amihud_daily'], 'trade', segment='2019-2023',
                          where='A1'),
        'NEW40 键直接用于 2019+'))

    r.append(expect_block(
        'A2_new40_label_end_past_2018',
        lambda: H.guard_h(['volume_ratio_3d'], 'label', segment='2015-2018',
                          label_end='2019-06-30', where='A2'),
        'NEW40 键的 label_end 越过 2018-12-31'))

    r.append(expect_block(
        'A3_alias_of_new40_post2018',
        lambda: H.guard_h([G.resolve_key('CVR')], 'trade', segment='2024-2026',
                          where='A3'),
        '用别名指向 NEW40 键再进 2019+'))

    r.append(expect_block(
        'A4_learned_product_post2018',
        lambda: H.guard_h(['mcap_rank', 'conditional_turnover'], 'selection',
                          segment='2019-2023', where='A4'),
        '学习产物混入一个 NEW40 坐标就整体受保护'))

    r.append(expect_block(
        'A5_renamed_rule_object_post2018',
        lambda: H.guard_h(['conditional_turnover'], 'trade', segment='2019-2023',
                          rule_objects=['ADD'], where='A5'),
        '规则对象是新的 -> 即使键全是老键也受保护'))

    r.append(expect_block(
        'A6_known_key_conditionalised_post2018',
        lambda: H.guard_h(['cum_return_5d'], 'holding', segment='2024-2026',
                          rule_objects=['FOCAL_CONDITION'], where='A6'),
        '已知键条件化 (新规则对象) 不能绕过守卫'))

    for dk in ('TCV_20', 'JUMP_5', 'IND_CUR_20', 'REL_IND_5'):
        r.append(expect_block(
            'A7_derived_%s_post2018' % dk,
            (lambda k=dk: H.guard_h([k], 'trade', segment='2019-2023', where='A7')),
            '新派生键 %s 未经记录 B 即进 2019+' % dk))

    r.append(expect_block(
        'A8_unregistered_key_spec',
        lambda: H.specH('my_secret_new_factor'),
        '自造新键名绕过注册表'))

    r.append(expect_block(
        'A9_derived_label_end_past_2018',
        lambda: H.guard_h(['TCV_60'], 'label', segment='2010-2014',
                          label_end='2019-01-15', where='A9'),
        '派生键在推导段但标签结束日越界'))

    r.append(expect_block(
        'A10_route_id_not_in_manifest',
        lambda: H.guard_h(['JUMP_20'], 'trade', segment='2019-2023',
                          route_id='R-O-fabricated', where='A10'),
        '编一个 route_id 也不行 (记录 B 未批准)'))

    # ---------- 必须放行 (防过严) ----------
    r.append(expect_pass(
        'P1_old_keys_post2018_ok',
        lambda: H.guard_h(['conditional_turnover', 'turnover_volatility_60d', 'CVR_20d'],
                          'trade', segment='2019-2023', where='P1'),
        'L/T 的旧输入旧规则格必须能先跑后段并封存 (brief §6 末条)'))

    r.append(expect_pass(
        'P2_new40_in_derivation_ok',
        lambda: H.guard_h(['amihud_daily'], 'trade', segment='2015-2018',
                          label_end='2018-12-31', where='P2'),
        'NEW40 键在推导段、label_end 到 2018-12-31 是允许的'))

    r.append(expect_pass(
        'P3_derived_in_derivation_ok',
        lambda: H.guard_h(['TCV_20', 'JUMP_5', 'IND_CUR_20'], 'shape',
                          segment='2010-2014', label_end='2018-12-31', where='P3'),
        '新派生键在推导段可用'))

    r.append(expect_pass(
        'P4_rule_object_in_derivation_ok',
        lambda: H.guard_h(['conditional_turnover'], 'trade', segment='2010-2014',
                          rule_objects=['ADD', 'SWAP'], where='P4'),
        '新规则对象在推导段可用'))

    r.append(expect_pass(
        'P5_registered_derived_spec_ok',
        lambda: [H.specH(k) for k in sorted(H.DERIVED)],
        '12 个派生键都能过注册闸'))

    r.append(expect_pass(
        'P6_registered_u74_spec_ok',
        lambda: [H.specH(k) for k in sorted(H.U74)],
        '75 个 U74 键都能过注册闸'))

    # ---------- 祖父豁免仍然成立 ----------
    r.append(expect_pass(
        'P7_grandfathered_intraday_cvr_1d',
        lambda: H.guard_h(['intraday_cvr_1d'], 'trade', segment='2019-2023', where='P7'),
        'E6e 已登记的 intraday_cvr_1d 保留祖父豁免'))

    n_ok = sum(1 for x in r if x['ok'])
    out = dict(round='E6h', version=H.VERSION,
               written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
               approval_loaded=H._APPROVAL['loaded'],
               n_total=len(r), n_pass=n_ok, results=r,
               note=('must_block = 攻击必须被拒; must_pass = 合法路径必须放行。'
                     '两类都过才算守卫既严又不过严。'))
    with open(os.path.join(OUT, 'guard_attack_tests.json'), 'w') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)

    print('E6h 守卫攻击测试: %d/%d 通过' % (n_ok, len(r)))
    for x in r:
        flag = 'OK ' if x['ok'] else '!! '
        print('  %s%-38s [%s] %s' % (flag, x['test'], x['kind'], x['note']))
        if not x['ok']:
            print('      -> %s' % x['msg'])
    if n_ok != len(r):
        raise SystemExit('守卫测试未全过')


if __name__ == '__main__':
    main()
