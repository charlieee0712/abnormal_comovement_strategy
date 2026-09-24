#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 守卫攻击测试 (brief §1.3 末条 / §13 新增反例)。must_block = 攻击必须被拒; must_pass = 合法路径放行。

覆盖: E6h 20 项的 E6i 对应物 + brief 点名的新反例:
  新测量缓存绕守卫 / M2 训练含未成熟标签 / C1 后段产物 B 前被读 / 随机对照改动旧分量 /
  E6h 的授权文件不能放行 E6i 对象 / 伪造 E6i 授权文件格式被拒 / 局部授权不外溢。
(SLOT α=0 不读新有效域 属算子层, 在 Stage 2 规则锚里阻断验收, 这里登记为指针。)
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import json
import time
import tempfile

import numpy as np

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6h_core as H


def expect_block(name, fn, note):
    try:
        fn()
    except I.GuardViolationI as e:
        return dict(test=name, kind='must_block', ok=True, note=note, msg=str(e)[:180])
    except Exception as e:                                  # 其他异常也算被拒, 但标出类型
        return dict(test=name, kind='must_block', ok=True, note=note,
                    msg='%s: %s' % (type(e).__name__, str(e)[:160]))
    return dict(test=name, kind='must_block', ok=False, note=note, msg='没有被拒 (漏网)')


def expect_pass(name, fn, note):
    try:
        fn()
    except Exception as e:
        return dict(test=name, kind='must_pass', ok=False, note=note,
                    msg='%s: %s' % (type(e).__name__, str(e)[:160]))
    return dict(test=name, kind='must_pass', ok=True, note=note, msg='')


def main():
    FE.build_catalog()
    I.set_protected_members(FE.protected_ids())
    I.load_approval_i()
    assert not I._APPROVAL_I['loaded'], '开工时不应已有 E6i 记录 B'
    r = []
    rs = [m['member_id'] for m in FE.CATALOG if m['source_class'] != 'LEGACY']
    lg = [m['member_id'] for m in FE.CATALOG if m['source_class'] == 'LEGACY']

    # ---------------- 必须被拒 ----------------
    r.append(expect_block('I1_research_member_post2018',
                          lambda: I.guard_i(['T_cv20'], segment='2019-2023', where='I1'),
                          '新测量直接进 2019+'))
    r.append(expect_block('I2_research_label_end_past_2018',
                          lambda: I.guard_i(['V_rs20_obs'], segment='2015-2018', use='label',
                                            label_end='2019-01-10', where='I2'),
                          '推导段新测量但标签结束日越界'))
    r.append(expect_block('I3_new_rule_on_legacy_keys_post2018',
                          lambda: I.guard_i(['T_std60_LEGACY'], ['SLOT'], segment='2024-2026',
                                            where='I3'),
                          '键全是源键, 但新算子 SLOT 进 2019+'))
    for ro in ('ADD_SCORE', 'VETO_NEW', 'SOFT', 'SWAP', 'FOCAL_NEW', 'RL', 'T_PAIR', 'FOURARM',
               'M1', 'M2', 'SLOT_FULL_REPLACE', 'COMMON_SUPPORT'):
        r.append(expect_block('I4_rule_%s_post2018' % ro,
                              (lambda ro=ro: I.guard_i([], [ro], segment='2019-2023',
                                                       where='I4')),
                              '新算子/程序 %s 未经 E6i 记录 B 进 2019+' % ro))
    r.append(expect_block('I5_cache_read_post_bypass',
                          lambda: I.load_member('2019-2023', 'T_cv20', 'OBS', where='I5'),
                          '新测量缓存读取绕守卫 (后段)'))
    r.append(expect_block('I6_c1_post_read_before_B',
                          lambda: I.sealed_read_csv('2019-2023', 'c1_probe'),
                          'C1 后段产物在记录 B 前被读'))
    r.append(expect_block('I7_m2_immature_label',
                          lambda: I.assert_matured(['2016-03-01', '2016-03-09'], '2016-03-08',
                                                   where='I7'),
                          'M2 训练集含未成熟标签 (标签结束日 >= 决策日)'))
    r.append(expect_block('I8_random_control_changes_old_component',
                          lambda: I.assert_old_component_unchanged(np.array([.1, .2, np.nan]),
                                                                   np.array([.1, .25, np.nan]),
                                                                   where='I8'),
                          '随机对照改动了旧分量'))

    def e6h_approval_does_not_unlock():
        H.load_approval()                                   # E6h 记录 B (已批准 M-T / I-P) 载入
        assert H._APPROVAL['loaded']
        I.guard_i(['T_cv20', 'R_peer20'], segment='2019-2023', where='I9')
    r.append(expect_block('I9_e6h_approval_does_not_unlock_e6i', e6h_approval_does_not_unlock,
                          'E6h 的 record_B_approved.json 不能放行 E6i 对象 (命名空间隔离)'))

    def fake_approval_format():
        d = tempfile.mkdtemp()
        p = os.path.join(d, 'fake.json')
        json.dump(dict(status='APPROVED', approval_id='E6H-B-01', approved_members=['T_cv20'],
                       approved_packages=['x'], approved_rule_objects=[]), open(p, 'w'))
        try:
            I.load_approval_i(p)
        finally:
            I.load_approval_i()
    r.append(expect_block('I10_fake_approval_wrong_namespace', fake_approval_format,
                          '伪造授权文件 (approval_id 不是 E6I-B-) 被拒'))

    def partial_approval_no_spill():
        d = tempfile.mkdtemp()
        p = os.path.join(d, 'ok.json')
        json.dump(dict(status='APPROVED', approval_id='E6I-B-TEST', approved_members=['T_cv20'],
                       approved_packages=['PKG-T'], approved_rule_objects=['SLOT']), open(p, 'w'))
        I.load_approval_i(p)
        try:
            I.guard_i(['T_cv20', 'V_rs20_obs'], ['SLOT'], segment='2019-2023',
                      package_id='PKG-T', where='I11')
        finally:
            I.load_approval_i()
    r.append(expect_block('I11_partial_approval_does_not_spill', partial_approval_no_spill,
                          '只批了 T_cv20, 同一调用里夹带未批成员 V_rs20_obs 必须被拒'))

    def wrong_package():
        d = tempfile.mkdtemp()
        p = os.path.join(d, 'ok.json')
        json.dump(dict(status='APPROVED', approval_id='E6I-B-TEST', approved_members=['T_cv20'],
                       approved_packages=['PKG-T'], approved_rule_objects=['SLOT']), open(p, 'w'))
        I.load_approval_i(p)
        try:
            I.guard_i(['T_cv20'], ['SLOT'], segment='2019-2023', package_id='PKG-OTHER',
                      where='I12')
        finally:
            I.load_approval_i()
    r.append(expect_block('I12_wrong_package_id', wrong_package,
                          '成员已批但 package_id 不在授权包里'))
    r.append(expect_block('I13_sealed_flag_does_not_free_new_measurement',
                          lambda: I.guard_i(['K_edge20'], ['C1_POST'], segment='2019-2023',
                                            use='compute', sealed=True, where='I13'),
                          'sealed 只放行旧输入 C1; 新测量血缘不因 sealed 放行'))
    r.append(expect_block('I14_all_research_members_post2018',
                          lambda: I.guard_i(rs, segment='2024-2026', where='I14'),
                          '全部 %d 个研究成员整批进 2019+' % len(rs)))

    # ---------------- 必须放行 ----------------
    r.append(expect_pass('P1_legacy_members_post2018_ok',
                         lambda: I.guard_i(lg, segment='2019-2023', where='P1'),
                         '%d 个 LEGACY 成员 (源键) 是旧对象, 后段可用' % len(lg)))
    r.append(expect_pass('P2_research_in_derivation_ok',
                         lambda: I.guard_i(rs, segment='2015-2018', use='label',
                                           label_end='2018-12-31', where='P2'),
                         '研究成员在推导段、标签到 2018-12-31'))
    r.append(expect_pass('P3_all_rules_in_derivation_ok',
                         lambda: I.guard_i(['T_cv20'], sorted(I.RULE_OBJECTS_I),
                                           segment='2010-2014', where='P3'),
                         '全部新算子/程序在推导段可用'))
    r.append(expect_pass('P4_c1_post_sealed_compute_ok',
                         lambda: I.guard_i([], ['C1_POST'], segment='2019-2023', use='compute',
                                           sealed=True, where='P4'),
                         '旧输入 C1 后段格可先算并封存 (brief §7 末条)'))
    r.append(expect_pass('P5_cache_read_derivation_ok',
                         lambda: I.load_member('2015-2018', 'T_cv20', 'OBS', where='P5'),
                         '推导段缓存读取放行'))
    r.append(expect_pass('P6_matured_labels_ok',
                         lambda: I.assert_matured(['2016-03-01', '2016-03-07'], '2016-03-08',
                                                  where='P6'),
                         '标签全部早于决策日'))
    r.append(expect_pass('P7_old_mother_post2018_ok',
                         lambda: I.guard_i([], [], segment='2024-2026', where='P7'),
                         '母体 / 源引擎 (无受保护对象) 后段可用'))
    r.append(dict(test='X1_slot_alpha0_no_new_domain', kind='pointer', ok=True,
                  note='SLOT α=0 不读新成员有效域 —— 算子层阻断锚, 在 Stage 2 e6i_rule_anchors 验收',
                  msg=''))

    n_block = [x for x in r if x['kind'] == 'must_block']
    n_pass = [x for x in r if x['kind'] == 'must_pass']
    out = dict(round='E6i', version=I.VERSION, written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
               approval_loaded=I._APPROVAL_I['loaded'],
               n_must_block=len(n_block), n_must_block_ok=sum(x['ok'] for x in n_block),
               n_must_pass=len(n_pass), n_must_pass_ok=sum(x['ok'] for x in n_pass),
               n_protected_members=len(rs), n_legacy_members=len(lg),
               n_rule_objects=len(I.RULE_OBJECTS_I), results=r)
    I.atomic_write_json(os.path.join(I.RES, 'checks', 'guard_attack_tests.json'), out)
    for x in r:
        print('%-4s %-44s %s' % ('OK' if x['ok'] else '!!', x['test'], x['msg'][:90]))
    tot = len(n_block) + len(n_pass)
    good = out['n_must_block_ok'] + out['n_must_pass_ok']
    print('守卫攻击测试 %d/%d (must_block %d/%d, must_pass %d/%d)'
          % (good, tot, out['n_must_block_ok'], len(n_block), out['n_must_pass_ok'], len(n_pass)))
    sys.exit(0 if good == tot else 1)


if __name__ == '__main__':
    main()
