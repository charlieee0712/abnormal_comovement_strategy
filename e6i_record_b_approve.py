#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 记录 B 批准落盘 (brief §7)。在任何 Stage 3 技术改动之前运行:
  1. 逐项核对 registry/record_B_candidate_manifest.json (描述符 / M2 规格 / 预登记 / 48 个 e6i 源文件 SHA) —— 不符即停;
  2. 写 registration/record_B_approved_E6i.json (E6i 自己的命名空间; e6i_core.load_approval_i 读取)
     + registration/record_B_approved_E6i.md (人读版) + receipt。
批准范围 = 候选 manifest 的全部 43 个需求域包 (整表), 另加一个技术包 E6I-B-CARRIED-C1C2 (brief §7 末条:
旧输入 C1 / C2 后段格 B 前封存、B 后读取), 不含任何未登记对象。
approved_members = 这些包的 A0 描述符在任何列里引用到的受保护成员 (含状态成员) + M2 程序固定引用的 u / z 成员;
Stage 1 只测未路由的成员不在内 (后段仍不可算)。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import re
import sys
import json
import time
import hashlib

import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE

CODE = '/mnt/sda2/lichenchen/code/project_core'
USER_REPLY = 'ultrathink 继续跑完'
APPROVAL_ID = 'E6I-B-20260924-FULL'
M2_FIXED_MEMBERS = ('S_peerR20', 'R_peer20', 'K_res_log', 'T_evlevel')
CARRIED_PKG = 'E6I-B-CARRIED-C1C2'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main():
    rg = os.path.join(I.RES, 'registry')
    man_p = os.path.join(rg, 'record_B_candidate_manifest.json')
    man = json.load(open(man_p))
    man_sha = sha(man_p)
    checks = []
    for name, path, want in (('descriptors_A0', os.path.join(rg, 'descriptors_A0.csv'), man['descriptors_sha256']),
                             ('M2_program_spec', os.path.join(rg, 'M2_program_spec.md'), man['m2_spec_sha256']),
                             ('preregistration', os.path.join(I.RES, 'preregistration.md'),
                              man['preregistration_sha256'])):
        got = sha(path)
        checks.append(dict(object=name, want=want, got=got, ok=(got == want)))
    for f, want in man['code_sha256'].items():
        p = os.path.join(CODE, f)
        got = sha(p) if os.path.exists(p) else None
        checks.append(dict(object='code:' + f, want=want, got=got, ok=(got == want)))
    bad = [c for c in checks if not c['ok']]
    if bad:
        raise SystemExit('manifest 核对失败 (%d 项): %s' % (len(bad), [c['object'] for c in bad][:10]))
    FE.build_catalog()
    prot = set(FE.protected_ids())
    a0 = pd.read_csv(os.path.join(rg, 'descriptors_A0.csv'), low_memory=False)
    pk = set(man['packages'])
    a0['package'] = 'E6I-B-' + a0.route_id.astype(str) + '-' + a0.mother_id.astype(str)
    sel = a0[a0.package.isin(pk)]
    if len(sel) != int(man['n_descriptors']) or set(sel.package) != pk:
        raise SystemExit('包 -> 描述符映射与 manifest 不符: %d 行 vs %d' % (len(sel), man['n_descriptors']))
    toks = set()
    for c in sel.columns:
        if sel[c].dtype == object:
            for v in sel[c].dropna().astype(str).unique():
                toks.update(t for t in re.split(r'[|+:=@,; ]', v) if t)
    members = sorted((toks | set(M2_FIXED_MEMBERS)) & prot)
    not_in = sorted(prot - set(members))
    rules = sorted(I.RULE_OBJECTS_I)
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    appr = dict(
        status='APPROVED', approval_id=APPROVAL_ID, round='E6i', approved_at=now,
        approved_by='user', user_reply_verbatim=USER_REPLY,
        user_reply_context=('执行端 2026-09-23 23:55 前后交付 E6i_record_B_draft.md (manifest sha 前缀 %s) 并在消息中请用户'
                            '在"批整表 / 按包批子集 / 不批"中选择、建议批整表, 同时询问是否先做 A1; 用户回复"%s"。'
                            '执行端据此按【整表批准】执行 (43 个需求域包); A1 路由复核未做, 按用户指示不等待。'
                            % (man_sha[:12], USER_REPLY)),
        manifest_path='registry/record_B_candidate_manifest.json', manifest_sha256=man_sha,
        descriptors_sha256=man['descriptors_sha256'], m2_spec_sha256=man['m2_spec_sha256'],
        preregistration_sha256=man['preregistration_sha256'],
        manifest_check=dict(n_objects=len(checks), n_ok=sum(c['ok'] for c in checks)),
        post_segments=man['post_segments'], end_date=man['end_date'], rules=man['rules'],
        approved_packages=sorted(pk) + [CARRIED_PKG],
        approved_descriptors=sorted(sel.descriptor_id.astype(str)),
        approved_members=members, approved_rule_objects=rules,
        carried_package_note=('%s 是技术包: brief §7 末条 "C1 / C2 只用旧输入的格可先算后段并封存 (B 前不读)", '
                              'B 后读取这些封存产物用此包名过守卫; 不解封任何新测量对象。' % CARRIED_PKG),
        protected_members_not_approved=not_in,
        draft_corrections=[
            'B 草稿 §3 注释写"Z-MAP (局部无信息映射) 只在推导段跑, 后段不复跑", §2 理由 (2) 写"随机对照不必复跑" —— '
            '与 brief §8 不符 (后段机制主读数 = 同人数核心 / 同资本 / 随机机制; P21 原登记主读数 = 匹配随机)。'
            'Stage 3 按 brief §8 在后段运行 Z-MAP; 冻结对象 (描述符 / 成员 / 规则 / M2 规格) 不变。'],
        stage3_technical_changes_policy=('Stage 3 需要的代码改动只做技术修复、保持经济定义 (brief §7 "后段技术修复保持经济定义并记 hash"): '
                                         '逐文件记改前 / 改后 SHA 与 diff 于 registry/stage3_code_changes/。'),
    )
    od = os.path.join(I.RES, 'registration')
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, 'record_B_approved_E6i.json')
    if os.path.exists(p):
        raise SystemExit('批准文件已存在, 不覆盖: %s' % p)
    I.atomic_write_json(p, appr)
    md = ['# E6i 记录 B 批准（%s）\n' % APPROVAL_ID,
          '- 批准时间（47）：%s；批准方：用户；用户原话：「%s」' % (now, USER_REPLY),
          '- 上下文：%s' % appr['user_reply_context'],
          '- 冻结 manifest：`registry/record_B_candidate_manifest.json`，sha `%s`；核对 %d / %d 项一致（描述符、M2 规格、预登记、%d 个 e6i 源文件）。'
          % (man_sha, appr['manifest_check']['n_ok'], appr['manifest_check']['n_objects'], len(man['code_sha256'])),
          '- 批准范围：%d 个需求域包（整表）+ 技术包 `%s`；描述符 %d 个；受保护成员 %d 个（另有 %d 个只在 Stage 1 测量、未进任何包的成员仍不可在后段计算）；规则对象 %d 个。'
          % (len(pk), CARRIED_PKG, len(sel), len(members), len(not_in), len(rules)),
          '- 后段：%s；数据止于 %s；规则：%s。' % (' / '.join(man['post_segments']), man['end_date'], '；'.join(man['rules'])),
          '- 草稿更正：%s' % appr['draft_corrections'][0],
          '- Stage 3 技术改动：%s' % appr['stage3_technical_changes_policy'],
          '- A1 路由复核：未做（规划 session 义务）；用户指示继续，不等待。\n']
    open(os.path.join(od, 'record_B_approved_E6i.md'), 'w', encoding='utf-8').write('\n'.join(md))
    I.write_receipt(os.path.join(I.RES, 'task_status', 'record_B_approved.receipt.json'), 'record_B:approve',
                    [p, os.path.join(od, 'record_B_approved_E6i.md')], approval_id=APPROVAL_ID,
                    manifest_sha256=man_sha)
    print('批准落盘: %s; 包 %d (+%s); 描述符 %d; 成员 %d (未批 %d); manifest 核对 %d/%d' % (
        p, len(pk), CARRIED_PKG, len(sel), len(members), len(not_in), appr['manifest_check']['n_ok'], len(checks)))


if __name__ == '__main__':
    main()
