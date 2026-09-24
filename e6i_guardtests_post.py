#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 记录 B 之后的守卫测试 (Stage 3 技术修复的验收; 与 Stage 0 的 e6i_guardtests.py 并列, 后者写死"开工时无记录 B")。
must_pass = 批准清单内对象在两后段放行 + 推导段行为不变; must_block = 清单外对象 / 伪造 / 夹带 / 错包 / 模拟 B 前 /
E6h 授权 / 缺规则对象的授权 全部被拒。输出 checks/guard_attack_tests_post.json; 任一不符 exit 1。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import json
import tempfile

import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6i_stage2 as S2
import e6h_core as H
from e6i_guardtests import expect_block, expect_pass


def rule_of(r):
    if r['route_id'] in ('M1', 'M2'):
        return r['route_id']
    return S2.ROLE_RULE.get(r['role'], r['role'])


def mems_of(r):
    return [x for x in str(r['member_id']).replace('+', '|').split('|') if x in FE.CATALOG_IDS]


def main():
    FE.build_catalog()
    FE.CATALOG_IDS = {m['member_id'] for m in FE.CATALOG}
    I.set_protected_members(FE.protected_ids())
    ap = I.load_approval_i()
    assert ap['loaded'] and str(ap['approval_id']).startswith('E6I-B-'), '应已载入 E6i 记录 B'
    appr = json.load(open(I.APPROVAL_FILE))
    notap = appr['protected_members_not_approved']
    a0 = pd.read_csv(os.path.join(I.RES, 'registry', 'descriptors_A0.csv'), low_memory=False)
    res = []
    # ---------------- 必须放行 ----------------
    samples = [g.iloc[0].to_dict() for _, g in a0.groupby('route_id')]
    for r in samples:
        for seg in I.POST_SEGS:
            res.append(expect_pass('P_%s_%s' % (r['route_id'], seg), (lambda r=r, seg=seg: I.guard_i(
                mems_of(r), [rule_of(r)], segment=seg, label_end='2026-03-27', use='trade',
                where=r['descriptor_id'])), '批准清单内描述符在后段放行'))
        if r['route_id'] not in ('M1', 'M2'):
            res.append(expect_pass('P_zmap_%s' % r['route_id'], (lambda r=r: I.guard_i(
                mems_of(r), [rule_of(r)], segment='2019-2023', label_end='2023-12-29', use='trade',
                where='zmap:' + r['descriptor_id'])), 'Z-MAP 前缀的批准描述符放行'))
    okm = sorted(set(appr['approved_members']))[:3]
    res.append(expect_pass('P_measure_compute_read', lambda: [I.guard_i([m], segment='2024-2026', use=u, where='t')
                                                              for m in okm for u in ('compute', 'read')],
                           '批准成员的纯测量算 / 读'))
    res.append(expect_pass('P_carried_sealed_read', lambda: I.guard_i(
        [], ['C1_POST'], segment='2019-2023', use='read', package_id='E6I-B-CARRIED-C1C2', where='t'),
        'B 后以技术包读取旧输入 C1/C2 封存产物'))

    def deriv_unchanged():
        ok, why = I.guard_i(okm[:1], ['SLOT'], segment='2015-2018', label_end='2018-12-28', where='d')
        assert ok and why == 'derivation', why
        assert I.post_allowed('2019-2023') and I.post_allowed('2024-2026')
        assert not I.post_allowed('2015-2018') and not I.post_allowed('2010-2014')
    res.append(expect_pass('P_derivation_unchanged_and_post_allowed', deriv_unchanged, '推导段语义不变; 段闸只对后段'))
    # ---------------- 必须被拒 ----------------
    r0 = [r for r in samples if r['route_id'] == 'RT'][0]
    res.append(expect_block('B1_unapproved_member_measure', lambda: I.guard_i(
        [notap[0]], segment='2019-2023', use='compute', where='t'), '未进任何包的成员在后段算'))
    res.append(expect_block('B2_fake_descriptor', lambda: I.guard_i(
        mems_of(r0), [rule_of(r0)], segment='2019-2023', use='trade', where='RT|FAKE|NOT_REGISTERED|H5'),
        '伪造 / 未登记描述符'))
    res.append(expect_block('B3_smuggled_member', lambda: I.guard_i(
        mems_of(r0) + [notap[0]], [rule_of(r0)], segment='2019-2023', use='trade', where=r0['descriptor_id']),
        '批准描述符夹带未批成员'))
    res.append(expect_block('B4_explicit_wrong_package', lambda: I.guard_i(
        mems_of(r0), [rule_of(r0)], segment='2019-2023', use='trade', where=r0['descriptor_id'],
        package_id='E6I-B-NOPE'), '显式给出不在授权里的包名'))
    res.append(expect_block('B5_zmap_fake', lambda: I.guard_i(
        mems_of(r0), [rule_of(r0)], segment='2024-2026', use='trade', where='zmap:RT|FAKE|H5'), 'Z-MAP 前缀伪造'))

    def before_B():
        I.load_approval_i(os.path.join(tempfile.mkdtemp(), 'absent.json'))
        try:
            if I._APPROVAL_I['loaded']:
                return  # 模拟失败 (仍处于已批准状态) -> 不抛错 -> 记为漏网, 不会被当作"被拒"
            I.guard_i(mems_of(r0), [rule_of(r0)], segment='2019-2023', use='trade', where=r0['descriptor_id'])
        finally:
            I.load_approval_i()
    res.append(expect_block('B6_simulated_before_B', before_B, '模拟无记录 B: 同一批准描述符必须被拒'))

    def e6h_only():
        I.load_approval_i(os.path.join(tempfile.mkdtemp(), 'absent.json'))
        try:
            H.load_approval()
            I.guard_i(mems_of(r0), [rule_of(r0)], segment='2019-2023', use='trade', where=r0['descriptor_id'])
        finally:
            I.load_approval_i()
    res.append(expect_block('B7_e6h_approval_does_not_unlock', e6h_only, 'E6h 授权不能放行 E6i 对象'))

    def missing_rule():
        d = tempfile.mkdtemp()
        p = os.path.join(d, 'r.json')
        a2 = dict(appr)
        a2['approved_rule_objects'] = [x for x in appr['approved_rule_objects'] if x != rule_of(r0)]
        json.dump(a2, open(p, 'w'), ensure_ascii=False)
        I.load_approval_i(p)
        try:
            I.guard_i(mems_of(r0), [rule_of(r0)], segment='2019-2023', use='trade', where=r0['descriptor_id'])
        finally:
            I.load_approval_i()
    res.append(expect_block('B8_rule_object_not_approved', missing_rule, '授权缺该规则对象'))
    assert I._APPROVAL_I['loaded'] and I._APPROVAL_I['approval_id'] == appr['approval_id']
    d = pd.DataFrame(res)
    I.atomic_write_json(os.path.join(I.RES, 'checks', 'guard_attack_tests_post.json'), dict(
        approval_id=appr['approval_id'], n=len(d), n_ok=int(d.ok.sum()), tests=res))
    print(d[['test', 'kind', 'ok', 'msg']].to_string(index=False, max_colwidth=90))
    print('post 守卫测试: %d / %d 符合' % (int(d.ok.sum()), len(d)))
    sys.exit(0 if d.ok.all() else 1)


if __name__ == '__main__':
    main()
