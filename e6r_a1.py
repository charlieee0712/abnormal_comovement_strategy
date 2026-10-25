# -*- coding: utf-8 -*-
"""E6r A1 冻结（brief §3 / 附录 B.8；plan §11.1）：S0（A1 前卡）全部通过后写 registration/freeze_E6r.json——
plan 全长 / 正文 / 合同脚本 / 11 件产物 / brief / 附录 / D 脚本 / SCHEMA 合同（D 脚本 --print-schema 原样输出的 sha）/ policy 文件 sha、源函数 sha 字典、
数据 cutoff、协议与方式、授权九值、authorized_by / at、cache_tag、E6q registry sha、reconciliation_status = RECONCILED；另冻结本轮代码（e6r_*.py / *.sh）sha、
registry 与全部注册件 sha。冻结后经济规则变动都是 amendment；技术缺陷修复可继续，修前输出改名保留。用法：python3 e6r_a1.py"""
import os
import sys
import json
import time
import glob
import hashlib
import subprocess

import pandas as pd

import e6r_core as O


def main():
    I = O.read_csv(O.P('verify', 'identities_E6r_stage0.csv'))
    bad = I[I.status.isin(['DIFFERS', 'FAIL'])]
    if len(bad):
        raise SystemExit('S0 有 DIFFERS：%s' % bad.check_id.tolist())
    S = O.read_csv(O.P('diagnostics', 'stage0_E6r_part1.csv'))
    sbad = S[S.status.isin(['DIFFERS', 'FAIL'])]
    if len(sbad):
        raise SystemExit('stage0 有 DIFFERS：%s' % sbad.key.tolist())
    dsc = O.P('verify', 'decision', 'E6r_D_stage2.py')
    if O.sha_file(dsc) != O.D_SCRIPT_SHA256:
        raise SystemExit('D 脚本 sha 不符')
    sch = subprocess.run([sys.executable, dsc, '--print-schema'], capture_output=True, text=True, cwd=O.work())
    if sch.returncode != 0:
        raise SystemExit('print-schema 失败')
    O.atomic_write_text(O.P('verify', 'spec', 'schema_contract.md'), sch.stdout)
    contract_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contract')
    code_dir = os.path.dirname(os.path.abspath(__file__))
    code = {os.path.basename(p): O.sha_file(p) for p in sorted(glob.glob(os.path.join(code_dir, 'e6r_*.py')) + glob.glob(os.path.join(code_dir, 'e6r_*.sh')))}
    src = O.read_csv(O.P('registration', 'sources_E6r.csv'))
    fz = dict(plan_sha256=O.PLAN_SHA256, plan_body_sha256=O.PLAN_BODY_SHA256, contract_sha256=O.CONTRACT_SHA256, contract_artifact_sha256=dict(O.SPEC_SHA),
              brief_sha256=O.sha_file(os.path.join(contract_dir, 'E6r_entry_quality_roles.md')),
              appendix_sha256=O.sha_file(os.path.join(contract_dir, 'E6r_brief_appendix_schema_probes.md')), d_script_sha256=O.sha_file(dsc),
              schema_contract_sha256=hashlib.sha256(sch.stdout.encode()).hexdigest(),
              policy_file_sha256=O.sha_file(O.E6Q('registration', 'policy_profile_E6q.json')),
              source_fn_sha256=dict(zip(src.key, [v if v else s for v, s in zip(src.fn_sha256, src.value)])), data_cutoff=O.CUTOFF, protocol='v1.6', mode='B',
              authorizations=dict(O.AUTHORIZATIONS), authorized_by=O.AUTHORIZED_BY, authorized_at=O.AUTHORIZED_AT, written_at=time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
              cache_tag=O.CACHE_TAG, e6q_registry_sha256=O.sha_file(O.E6Q('registration', 'registry_E6q.csv')), reconciliation_status='RECONCILED',
              cache_dir=os.path.basename(O.cache_dir()), code_sha256=code,
              registration_sha256={os.path.basename(p): O.sha_file(p) for p in sorted(glob.glob(O.P('registration', '*.csv')))},
              policy_mapping_sha256=O.sha_file(O.P('statistics', 'policy_mapping_E6r.csv')), start_message_sha256=O.START_MSG_SHA256,
              proposal_sha256=O.PROPOSAL_SHA256, e6q_review_sha256=O.E6Q_REVIEW_SHA256, deployment_authorized=False, e7='HOLD',
              stage0_identities=dict(n=len(I), statuses=I.status.value_counts().to_dict()))
    for k in ('brief_sha256', 'appendix_sha256'):
        exp = {'brief_sha256': O.BRIEF_SHA256, 'appendix_sha256': O.APPENDIX_SHA256}[k]
        if fz[k] != exp:
            raise SystemExit('%s 不符' % k)
    p = O.P('registration', 'freeze_E6r.json')
    if os.path.exists(p):
        raise SystemExit('freeze_E6r.json 已存在（A1 只写一次；amendment 另写版本）')
    O.atomic_write_json(p, fz)
    O.write_receipt('E6r_A1_freeze', [p, O.P('verify', 'spec', 'schema_contract.md')], code=[__file__, O.__file__], n_code=len(code))
    print(json.dumps(dict(written=os.path.basename(p), code_files=len(code), schema_contract_sha256=fz['schema_contract_sha256'][:16]), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
