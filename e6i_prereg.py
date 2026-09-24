#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 事前登记 (brief §1.4 / §12): 首次新收益评价前落盘。
preregistration.md = brief §12 全文逐字 (Q1-Q16 四列 + 规划补充 Q17-Q18 + 读法优先级 + 边界)
                     + 实际时间 + 输入 / 代码哈希 + 源 ID 映射。不改写编号与问题。
hypotheses_A0.json = 同一内容的机器可读版 (Q 表逐行解析) + plan §2.3 八字段框架。
已存在则拒绝覆盖 (修订另起 preregistration_amend_<日期>.md)。
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I


def main():
    out_md = os.path.join(I.RES, 'preregistration.md')
    out_js = os.path.join(I.RES, 'registry', 'hypotheses_A0.json')
    if os.path.exists(out_md):
        raise SystemExit('preregistration.md 已存在, 不覆盖 (修订另起 amendment)')
    # 守卫: 此刻不得已有任何新测量的收益产物
    acc = glob.glob(os.path.join(I.RES, 'accounts', '**', '*'), recursive=True)
    meas = [p for p in glob.glob(os.path.join(I.RES, 'measurements', '**', '*'), recursive=True)
            if os.path.isfile(p)]
    if [p for p in acc if os.path.isfile(p)] or meas:
        raise SystemExit('已有收益 / 测量诊断产物, 事前登记时序被破坏: %s' % (acc[:3] + meas[:3]))
    brief = open(os.path.join(I.RES, 'brief_copy.md'), encoding='utf-8').read()
    m = re.search(r'(## 12\. 事前登记.*?)\n---\n', brief, re.S)
    assert m, 'brief §12 没找到'
    sec12 = m.group(1)
    # Q 表逐行解析
    qs = []
    for line in sec12.splitlines():
        mm = re.match(r'\|\s*(Q\d+)\s+([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|\s*$', line)
        if mm:
            qs.append(dict(q=mm.group(1), label=mm.group(2).strip(),
                           motivation_question_competing=mm.group(3).strip(),
                           experiment_primary_reading=mm.group(4).strip(),
                           allowed_and_forbidden=mm.group(5).strip()))
    for qn in ('Q17', 'Q18'):
        mm = re.search(r'^%s (.*)$' % qn, sec12, re.M)
        assert mm, qn
        qs.append(dict(q=qn, label=mm.group(1).split('：')[0].strip(), text=mm.group(1).strip(),
                       source='规划 session 补充'))
    assert [q['q'] for q in qs] == ['Q%d' % i for i in range(1, 19)], [q['q'] for q in qs]
    code = {os.path.basename(p): I.sha_file(p) for p in
            sorted(glob.glob(os.path.join(I.CODE, 'e6i_*.py')))}
    docs = {f: I.sha_file(os.path.join(I.RES, f)) for f in
            ('PLAN_COPY.md', 'brief_copy.md', 'E6i_proposal_copy.md', 'E6h_REVIEW_copy.md',
             'source_resolution.md', 'engine_contract.md')}
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    head = ('# E6i preregistration（事前登记；brief §12 逐字；首次新收益评价前落盘）\n\n'
            '- 落盘时间：%s（47 本地时间）\n'
            '- 此刻状态：Stage 0 仪器完成（特征锚 19/19 x 2、引擎锚 48/48 x 2、suffix 1,952/1,952、'
            '守卫攻击 32/32、契约 61/61）；**尚无任何新测量的收益 / 条件分布 / 角色账户产物**\n'
            '  （本脚本启动时核验 accounts/ 与 measurements/ 为空）\n'
            '- 输入文档 SHA256：%s\n'
            '- 代码 SHA256（e6i_*.py，本刻）：见 hypotheses_A0.json\n'
            '- 源 ID 映射：成员 id ↔ 公式见 registry/feature_semantics_v2.csv；源键桥见 '
            'source_resolution.md §6；母体槽位见 registry/mothers.csv\n'
            '- 修订规则：本文件不改写；修订另起 `preregistration_amend_<日期>.md`，编号与问题不改。\n\n'
            '---\n\n' % (now, json.dumps({k: v[:16] for k, v in docs.items()}, ensure_ascii=False)))
    with open(out_md, 'w', encoding='utf-8') as fh:
        fh.write(head + sec12 + '\n')
    hyp = dict(round='E6i', stage='A0', registered_at=now, source='brief §12 (逐字) + plan §10',
               eight_fields=['observation_and_exposure', 'decision_need', 'estimand',
                             'competing_mechanisms', 'operation_and_key_contrast',
                             'expected_form', 'reading_boundary', 'update_rule'],
               result_card_template=('hypothesis_id / motive_id / preregistration_hash / '
                                     'exposure_class / source_fact / competing_mechanisms / '
                                     'chosen_contrast / expected_pattern / actual_members / '
                                     'actual_dates / mother / operator / costs / support / '
                                     'primary_estimate / uncertainty / practical_scale / '
                                     'decomposition / prediction_status / root_cause_evidence / '
                                     'what_was_not_tested / what_cannot_be_concluded / '
                                     'next_design_change / why_it_addresses_the_failure / '
                                     'new_information_needed'),
               questions=qs, input_sha256=docs, code_sha256=code,
               preregistration_md_sha256=I.sha_file(out_md))
    I.atomic_write_json(out_js, hyp)
    print('preregistration.md 落盘 %s; Q 解析 %d 条 (Q1-Q18); sha %s'
          % (now, len(qs), hyp['preregistration_md_sha256'][:16]))


if __name__ == '__main__':
    main()
