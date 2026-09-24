#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 4 登记件 (plan §12.1): registry/manifest_B.json, registry/approval_provenance.json,
registry/exposure_ledger.csv, reports/limit_register.md。全部由已落盘文件现取 (sha / 计数 / 状态表), 叙述只登记事实。
在首次观察回执之后运行 (manifest_B 带回执 sha); C1 / C2 未完成时对应 LIMIT 行写 pending。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import json
import glob
import time
import hashlib

import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I

R = I.RES


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest() if os.path.exists(p) else None


def main():
    t0 = time.time()
    rg = os.path.join(R, 'registry')
    appr = json.load(open(I.APPROVAL_FILE))
    man = json.load(open(os.path.join(rg, 'record_B_candidate_manifest.json')))
    chg = json.load(open(os.path.join(rg, 'stage3_code_changes', 'changes.json')))
    flp = os.path.join(rg, 'first_look_receipts.json')
    fl = json.load(open(flp)) if os.path.exists(flp) else {}
    mb = dict(round='E6i', stage='manifest_B', written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
              approval_id=appr['approval_id'], approved_at=appr['approved_at'],
              approval_file_sha256=sha(I.APPROVAL_FILE), candidate_manifest_sha256=appr['manifest_sha256'],
              descriptors_sha256=man['descriptors_sha256'], m2_spec_sha256=man['m2_spec_sha256'],
              preregistration_sha256=man['preregistration_sha256'], code_sha256_at_approval=man['code_sha256'],
              approved_packages=appr['approved_packages'], n_descriptors=len(appr['approved_descriptors']),
              n_members=len(appr['approved_members']), rule_objects=appr['approved_rule_objects'],
              post_segments=man['post_segments'], end_date=man['end_date'], rules=man['rules'],
              stage3_technical_changes=[dict(file=c['file'], sha_before=c['sha_before'], sha_after=c['sha_after'])
                                        for c in chg['changed']],
              stage3_new_files=chg['new_files'],
              first_look_receipts=dict(status=fl.get('status'), written_at=fl.get('written_at'),
                                       n_files=fl.get('n_files'), sha256=sha(flp)))
    I.atomic_write_json(os.path.join(rg, 'manifest_B.json'), mb)
    prov = dict(approval_id=appr['approval_id'], approved_at=appr['approved_at'], approved_by=appr['approved_by'],
                user_reply_verbatim=appr['user_reply_verbatim'], user_reply_context=appr['user_reply_context'],
                interpretation='用户在执行端给出"整表 / 子集 / 不批"三选与整表建议之后回复"继续跑完"; 执行端按整表批准执行, 并在交付消息中写明此解读',
                a1_status='not performed（规划 session 义务；用户指示继续，不等待）',
                draft_corrections=appr['draft_corrections'],
                files=dict(approval=os.path.relpath(I.APPROVAL_FILE, R), approval_md='registration/record_B_approved_E6i.md',
                           candidate_manifest='registry/record_B_candidate_manifest.json',
                           b_draft='reports/E6i_record_B_draft.md'))
    I.atomic_write_json(os.path.join(rg, 'approval_provenance.json'), prov)
    ex = [
        dict(event='A0 v1.1（四臂参数补登记）', when='2026-09-23 Stage 2 之前', seen='无四臂账户; Stage 1 诊断不涉及四臂',
             changed='FOURARM 144 -> 216 行; 其余逐 id 相同', basis='plan §5.7 原文参数', ref='registry/A0_amendment_v1_1.md'),
        dict(event='A0 v1.2（RR cr5 焦点"两者"臂）', when='2026-09-23 Z-MAP selftest 期间',
             seen='RR replace_cr5（新臂）2010-14 真实账户年化水平（未与母体 / all_off / 随机比较; 无 2015-18）',
             changed='+480 行 both_cr5; 其余逐字段相同', basis='plan §5.3 原文', ref='registry/A0_amendment_v1_2.md'),
        dict(event='M2 程序规格补全（z 与接入预算）', when='2026-09-23 18:22, 任何 M2 拟合之前',
             seen='Stage 2 主账户推导段已算出（首看: 多数路线子−母中位为负, RK 例外）',
             changed='z = S_peerR20（S 轴 u = R_peer20）; 预算 = 各 home 角色已登记网格中间档',
             basis='只从已登记对象取、一次定死; plan §7.2 / §7.3', ref='registry/M2_program_spec.md'),
        dict(event='A0 v1.3（RA 最高 K 换出 SWAP; 四臂 K x A 的 M2）', when='2026-09-23 22:33',
             seen='Stage 2 全部推导段账户、Z-MAP 首轮与统计首轮（含 RA 母体最差换出与 RK / 四臂读数）',
             changed='+1,704 行（RA 1,656 + M2 48）; 旧行 gone 0 / changed 0', basis='plan §5.4.2 / brief §6 原文参数, 无按结果选择的自由度',
             ref='registry/A0_amendment_v1_3.md'),
        dict(event='record B 草稿与候选 manifest', when='2026-09-23 23:55',
             seen='推导段全部结果（设计如此）', changed='43 个需求域包; 执行端建议整表批准', basis='brief §7',
             ref='reports/E6i_record_B_draft.md; registry/record_B_candidate_manifest.json'),
        dict(event='记录 B 批准', when=appr['approved_at'], seen='无后段数值',
             changed='整表批准 + 技术包 CARRIED; 草稿"Z-MAP 后段不复跑"更正为照 brief §8 执行',
             basis='用户原话"%s"' % appr['user_reply_verbatim'], ref=os.path.relpath(I.APPROVAL_FILE, R)),
        dict(event='Stage 3 技术改动', when=chg.get('written_at', ''), seen='无后段数值（冒烟只看状态: 2019-23 RK 2 配置已算, 数值未读）',
             changed='%d 个文件（段闸 / 守卫 / M2 多段训练 / 后段参数）+ %d 个新文件' % (len(chg['changed']), len(chg['new_files'])),
             basis='brief §7 "后段技术修复保持经济定义并记 hash"', ref='registry/stage3_code_changes/'),
        dict(event='Z-MAP 后段 MCSE 加轮', when='Stage 3', seen='只看 MCSE（路径均值的蒙特卡洛误差）', changed='按阶梯 256 / 512 / 1024 加路径',
             basis='plan §6.4', ref='statistics/zmap_post_escalation_plan_r*.csv'),
        dict(event='首次观察封存回执', when=fl.get('written_at', 'pending'), seen='回执之前无后段数值读取',
             changed='两后段产物逐文件 sha 封存', basis='brief §7 / plan Stage 3', ref='registry/first_look_receipts.json'),
        dict(event='B 后事后补充（part3 §0 母体基线 / §1b 分族读数 / §2 C1 资本分解）', when='2026-09-25（47 时间）',
             seen='全部推导段与后段结果（part2 / part3 已交付之后）',
             changed='只重新汇总已封存账户：按 A0 事前定义的族汇总、按 α / H 分组、α ≤ .25 且 H ≥ 10 的事后切片、C1 部署视图资本分解；'
                     'part3 §2 读法与摘要据此修订（C1 人数效应主体是部署量）；不改任何登记读数、不新增账户',
             basis='用户要求补充报告；读法标"事后"', ref='reports/E6i_REPORT_part3.md §0 / §1b / §2；carried/summary/C1_T9_capital*.csv'),
    ]
    I.atomic_write_csv(os.path.join(rg, 'exposure_ledger.csv'), pd.DataFrame(ex))
    st3p = os.path.join(rg, 'stage3_status_table.csv')
    st3 = pd.read_csv(st3p) if os.path.exists(st3p) else pd.DataFrame()
    na = int(st3.not_applicable.sum()) if len(st3) else 0
    ft = int(st3.failed_tech.sum()) if len(st3) else 0
    c1 = sorted(glob.glob(os.path.join(R, 'task_status', 'c1_*.receipt.json')))
    c2 = sorted(glob.glob(os.path.join(R, 'task_status', 'c2_*.receipt.json')))
    lim = ['# E6i limit_register（LIMIT / 不可得 / 延后；%s）\n' % time.strftime('%Y-%m-%d %H:%M'),
           '| # | 项 | 状态 | 原因 | 影响 |', '|---|---|---|---|---|',
           '| L1 | A1 路由复核（规划 session） | deferred | 规划端未做；用户在记录 B 时指示继续、不等待 | 本轮没有 A1 增补；若事后做 A1，只能作为下一轮登记，不追认 |',
           '| L2 | EDGE 价差（Ardia–Guidotti–Kroencke） | changed | 47 上 GitHub raw 超时 → 本地工作站 clone 固定 commit、逐行审阅后 vendor（source_corrections C1；vendor check 5/5） | 实现来源不变 |',
           '| L3 | Kyle λ / tick 跳跃与已实现核 / 东财概念图 / 分钟级微观结构 / turnover_ff | unavailable | 数据不可得（逐笔签名成交、分钟或 tick、概念 PIT、自由流通股本字段）| 对应需求轴无本轮测量；见 consideration_ledger C 部分 |',
           '| L4 | Pástor–Stambaugh / DFA-Hurst | deferred | 本轮无当前母体需求（plan §4.9）| 未构造 ≠ 无效 |',
           '| L5 | RK 在 A08 | NOT_APPLICABLE | A08 核只有 T（source_corrections C2）| RK 少一个母体 |',
           '| L6 | %d 个只在 Stage 1 测量、未进任何需求域包的受保护成员（%s） | 后段未解封 | 记录 B 只解封包内对象 | 后段无读数；研究目录标"仅推导段" |' % (
               len(appr['protected_members_not_approved']), ' / '.join(appr['protected_members_not_approved'])),
           '| L7 | Z-MAP 尾部比例 | LIMIT | 无可交换性证明 → `diagnostic_tail_fraction`，不是精确 p 值（plan §6.4 / §8.3）| 只作诊断 |',
           '| L8 | M2 学习不确定性（256 次时间块重采样） | LIMIT | 条件于已拟合的程序路径，不是重新经历完整选模的无条件区间（plan §7.3）| 不当独立验证 |',
           '| L9 | 后段 | LIMIT | 冻结对象的首次观察，研究者知道 regime，历史此前参与过研究 → 不是 OOS（E7 HOLD）| 读法见 part2 |',
           '| L10 | C2 冲击成本 | LIMIT | κ 未校准；Q/ADV20 为日频压力代理、不是 POV → 不输出可部署规模 | 见 part3 |',
           '| L11 | B 草稿写法 | changed | 草稿写"Z-MAP 后段不复跑"与 brief §8 不符 → 批准文件登记更正、后段照跑 Z-MAP | 冻结对象不变 |',
           '| L12 | Stage 3 技术改动 | changed | 段闸 / 守卫 / M2 多段训练 / 后段参数（%d 个文件）| 经济定义不变；sha 与 diff 见 registry/stage3_code_changes/ |' % len(chg['changed']),
           '| L13 | Stage 3 NOT_APPLICABLE / FAILED_TECH | %s | 状态表 `registry/stage3_status_table.csv` | NOT_APPLICABLE %d、FAILED_TECH %d |' % (
               'done' if len(st3) else 'pending', na, ft),
           '| L14 | C1（N x 行业宽度） | %s | receipt %d 个 | 见 part3 |' % ('done' if len(c1) else 'pending', len(c1)),
           '| L15 | C2（冲击成本透镜） | %s | receipt %d 个 | 见 part3 |' % ('done' if len(c2) else 'pending', len(c2)),
           '| L16 | C1 资本分解 | LIMIT | 严格视图（两格同日可行日）的逐日投入资金没有保存 → 分解只能在部署视图（全日历）上做 | 两视图支持不同、差的大小不同；part3 §2 并列给出 |',
           '| L17 | part3 §0 / §1b / §2 资本分解 | changed | B 后事后补充（看过后段后做的汇总；α / H 切片事后选） | 不改登记读数；读法标"事后"；见 exposure_ledger |',
           '']
    open(os.path.join(R, 'reports', 'limit_register.md'), 'w', encoding='utf-8').write('\n'.join(lim))
    # plan §12.1: A1 没做就写明没做, 不写 "A1 reviewed; no change", 也不生成 hypotheses_A1.json
    open(os.path.join(rg, 'routing_review_A1.md'), 'w', encoding='utf-8').write(
        '# routing_review_A1（E6i）\n\n**A1 未执行。** 执行端 2026-09-23 23:55 前后交付记录 B 草稿时询问是否先做 A1；用户回复"%s"，'
        '执行端按整表批准执行、不等待 A1（`registry/approval_provenance.json`）。\n\n'
        '因此本轮没有 A1 登记版本：不存在 `hypotheses_A1.json`，也不写"A1 reviewed; no change"（plan §12.1：不伪造未发生的登记）。'
        '若规划 session 事后做路由复核，只能作为下一轮的登记输入，不追认本轮。\n' % appr['user_reply_verbatim'])
    lay = [('PLAN_COPY.md', 'PLAN_COPY.md', ''), ('brief_copy.md', 'brief_copy.md', ''),
           ('input_manifest.json', 'source_manifest.json', '改名：输入文件与源码指纹'),
           ('source_resolution.md', 'source_resolution.md', ''),
           ('registry/mothers.csv', 'registry/mothers.csv', ''),
           ('registry/feature_semantics_v2.csv', 'registry/feature_semantics_v2.csv', ''),
           ('registry/estimator_families.csv', 'registry/estimator_families.csv', ''),
           ('registry/mother_needs.csv', 'registry/mother_needs_*.csv', '按段拆成四个文件'),
           ('registry/need_estimator_role_map.csv', 'registry/need_estimator_role_map.csv', ''),
           ('registry/aliases.csv', 'registry/feature_semantics_v2.csv', '未单独成文件：源桥 / 别名 = source_class LEGACY 行 + source_ref 列'),
           ('registry/hypotheses_A0.json', 'registry/hypotheses_A0.json', ''),
           ('registry/hypotheses_A1.json', '', 'A1 未执行，不生成（见 routing_review_A1.md）'),
           ('registry/routing_review_A1.md', 'registry/routing_review_A1.md', '写明 A1 未执行'),
           ('registry/manifest_A0.json', 'registry/manifest_A0.json', ''),
           ('registry/manifest_B.json', 'registry/manifest_B.json', ''),
           ('registry/approval_provenance.json', 'registry/approval_provenance.json', ''),
           ('registry/consideration_ledger.csv', 'reports/consideration_ledger_E6i*.csv', '放在 reports/（另有 .md）'),
           ('registry/exposure_ledger.csv', 'registry/exposure_ledger.csv', ''),
           ('registry/coverage.csv', 'registry/coverage.csv', ''),
           ('checks/source_anchors.csv', 'checks/p0_source_facts_*.json', '按段 json；另有 engine / sparse_engine / feature / label / rule anchors'),
           ('checks/algebra_checks.csv', 'checks/*_anchor*_*.json', '恒等锚按段 json；plan 合同测试见 checks/plan_contract_tests/'),
           ('checks/suffix_guard.csv', 'checks/suffix_guard_*.csv', '按段 x 轴拆开'),
           ('checks/simulation_ADEMP.md', 'checks/simulation_ADEMP.md', ''),
           ('checks/simulation_results.csv', 'checks/simulation_results.csv', ''),
           ('checks/instrument_limits.csv', '', '未单独成文件：仪器偏差与排序力见 E6i_REPORT_R0 §1，限制项见 reports/limit_register.md'),
           ('measurements/', 'measurements/*', ''), ('accounts/', 'accounts/*', ''), ('statistics/', 'statistics/*', ''),
           ('domains/', 'm2/*/ledger_*.csv', 'domains/ 建了但未用（空目录）：M2 程序台账 / 系数 / 训练区间 / 学习不确定性在 m2/<段>/，'
                                               'M1 账户在 accounts/<段>/M1_*，M2 规格在 registry/M2_program_spec.md，M0 = accounts/ 主账户的固定代表'),
           ('carried/', 'carried/*', '')]
    lay += [('reports/' + f, 'reports/' + f, '') for f in (
        'E6i_REPORT_R0.md', 'E6i_REPORT_part1.md', 'E6i_REPORT_part1b.md', 'E6i_record_B_draft.md', 'E6i_REPORT_part2.md',
        'E6i_REPORT_part3.md', 'hypothesis_outcomes.md', 'factor_iteration_delta.md', 'research_catalog_v36.csv',
        'candidate_library_update_proposal.md', 'source_corrections_E6i.md', 'limit_register.md',
        'line_state_proposal.md', 'park_ledger_delta.md', 'E6i_REVIEW_input.md')]
    rows = []
    for item, actual, note in lay:
        n = len(glob.glob(os.path.join(R, actual))) if actual else 0
        rows.append(dict(plan_item=item, actual=actual or '—', n_found=n,
                         status=('present' if n else ('not_produced' if not actual else 'MISSING')), note=note))
    I.atomic_write_csv(os.path.join(rg, 'layout_map_plan12_1.csv'), pd.DataFrame(rows))
    miss = [r['plan_item'] for r in rows if r['status'] == 'MISSING']
    print('manifest_B / approval_provenance / exposure_ledger (%d) / limit_register / routing_review_A1 / layout_map (%d 项, MISSING %s) 写出; %.0fs' % (
        len(ex), len(rows), miss or 0, time.time() - t0))


if __name__ == '__main__':
    main()
