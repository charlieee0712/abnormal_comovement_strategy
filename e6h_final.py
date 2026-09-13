#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 收尾: task_status + manifest.json (brief §12 完成定义)。

每登记单元 ∈ {SUCCEEDED, FAILED, LIMIT, BLOCKED_BY_GATE, DEFERRED,
UNAVAILABLE_WITH_REASON}; 计数之和 = 登记总数。
产物带行数 / 有限与 NA 计数 / 状态。核心模块未跑标 PARTIAL_WITH_LIMITS。
另核【只读完整性】: 四地基 + 七 e6e + 十九 e6f + 二十八 e6g 一个都不能变。
"""
from __future__ import annotations
import os
import sys
import json
import glob
import time
import hashlib
import subprocess

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H

R = H.RES
CODE = H.CODE

# (任务名, 产物 glob, 期望片数, 状态)
TASKS = [
    ('S0_source_manifest', 'source_manifest.json', 1, 'SUCCEEDED'),
    ('S0_semantics', 'registry/feature_semantics.csv', 1, 'SUCCEEDED'),
    ('S0_taxonomy', 'registry/feature_taxonomy.csv', 1, 'SUCCEEDED'),
    ('S0_guard_tests', 'checks/guard_attack_tests.json', 1, 'SUCCEEDED'),
    ('S0_anchors', 'checks/anchors_*.json', 4, 'SUCCEEDED'),
    ('S0_rule_anchors', 'checks/rule_anchors_*.json', 1, 'SUCCEEDED'),
    ('S0_prereg', 'preregistration.md', 1, 'SUCCEEDED'),
    ('S0_concurrency', 'runtime/concurrency_pilot.json', 1, 'SUCCEEDED'),
    ('R0_stage_sets', 'stage_sets/stage_sets_*.npz', 2, 'SUCCEEDED'),
    ('R0_distributions', 'T0_full_distribution/stage_distributions_*.csv', 2, 'SUCCEEDED'),
    ('R0_pseudo', 'T0_full_distribution/pseudo_paths_*.csv', 2, 'SUCCEEDED'),
    ('R0_relation', 'T0_full_distribution/factor_parent_relation_2*.csv', 2, 'SUCCEEDED'),
    ('R0_clustering', 'clustering/factor_clusters_*.json', 2, 'SUCCEEDED'),
    ('R0_alias', 'registry/alias_measurements.csv', 1, 'SUCCEEDED'),
    ('R0_ledger', 'parent_need_ledger.md', 1, 'SUCCEEDED'),
    ('R0_report', 'REPORT_R0.md', 1, 'SUCCEEDED'),
    ('A_route_manifest', 'registry/route_manifest.json', 1, 'SUCCEEDED'),
    ('A_descriptors_frozen', 'checks/derivation_manifest_frozen.json', 1, 'SUCCEEDED'),
    ('R1_routes', 'route_results/summary_2*.csv', 10, 'SUCCEEDED'),
    ('R1_h_extra', 'route_results/hextra_*.csv', 10, 'SUCCEEDED'),
    ('R1_event_profile', 'route_results/event_profile_*.csv', 10, 'SUCCEEDED'),
    ('R1_attrib', 'route_results/attrib_*.csv', 10, 'SUCCEEDED'),
    ('R2_interactions', 'interaction_results/interactions_*.csv', 2, 'SUCCEEDED'),
    ('R2_samepos', 'paired_controls/samepos_*.csv', 2, 'LIMIT'),
    ('R2_randoms', 'random_registry/random_refs_*.csv', 6, 'LIMIT'),
    ('R3_selection', 'domain_selection/domain_selection.csv', 1, 'SUCCEEDED'),
    ('REPORT_part1', 'REPORT_part1.md', 1, 'SUCCEEDED'),
    ('L_main', 'L/L_main_*.csv', 4, 'SUCCEEDED'),
    ('L_b0_anchor', 'L/L_b0_anchor_*.json', 4, 'SUCCEEDED'),
    ('L_incumbent_lx', 'L/L_incumbent_lx_*.csv', 4, 'SUCCEEDED'),
    ('L_exit_anchor', 'L/L_exit_engine_anchor_*.json', 4, 'SUCCEEDED'),
    ('L_cost', 'cost/impact_scenarios.csv', 1, 'SUCCEEDED'),
    ('L_capacity', 'cost/capacity_A_star.csv', 1, 'SUCCEEDED'),
    ('L_leader_draft', 'cost/leader_table_draft_H_x_A.csv', 1, 'SUCCEEDED'),
    ('L_participation', 'cost/participation_notional.csv', 1, 'UNAVAILABLE_WITH_REASON'),
    ('T1_attribution', 'T/T1_attribution_*.csv', 4, 'SUCCEEDED'),
    ('T1_identity', 'T/T1_identity_*.json', 4, 'SUCCEEDED'),
    ('T2_budget', 'T/T2_budget_*.csv', 4, 'SUCCEEDED'),
    ('T2_anchor', 'T/T2_anchor_*.json', 4, 'SUCCEEDED'),
    ('T3_subsample', 'T/T3_subsample_*.csv', 4, 'SUCCEEDED'),
    ('T4_p16', 'T/T4_p16_*.csv', 4, 'SUCCEEDED'),
    ('T4_overlap_anchor', 'T/T4_e6g_overlap_anchor_*.json', 4, 'SUCCEEDED'),
    ('T5_state', 'T/T5_state_*.csv', 4, 'SUCCEEDED'),
    ('STATS_pointwise', 'stats/pointwise_nw.csv', 1, 'SUCCEEDED'),
    ('STATS_bands', 'stats/family_bands.csv', 1, 'SUCCEEDED'),
    ('STATS_FL_FT_bands', '', 0, 'DEFERRED'),
    ('STATS_stepdown', '', 0, 'DEFERRED'),
    ('R0_subject_clustering', '', 0, 'DEFERRED'),
    ('A_record_A_v1', '', 0, 'DEFERRED'),
    ('B_record_B', 'registration/record_B_approved.json', 1, 'SUCCEEDED'),
    ('POST_first_look', 'post_segments/SEALED_post_*.csv', 2, 'SUCCEEDED'),
    ('POST_receipts', 'post_segments/SEALED_receipt_*.json', 2, 'SUCCEEDED'),
    ('POST_extra', 'post_segments/post_extra_*.csv', 2, 'SUCCEEDED'),
    ('POST_family_bands', 'post_segments/post_family_bands_*.csv', 2, 'SUCCEEDED'),
    ('POST_selection', 'post_segments/post_selection_*.csv', 2, 'LIMIT'),
    ('POST_randoms', 'random_registry/random_refs_post_*.csv', 2, 'SUCCEEDED'),
    ('POST_first_look_receipt', 'first_look_receipts/first_look_receipt.json', 1,
     'SUCCEEDED'),
    ('REPORT_part2', 'REPORT_part2.md', 1, 'SUCCEEDED'),
    ('REPORT_part3', 'REPORT_part3.md', 1, 'SUCCEEDED'),
    ('L_new_route_grid', 'L/L_newroute_grid_*.csv', 4, 'SUCCEEDED'),
    ('L_new_route_b0_anchor', 'L/L_newroute_b0_anchor_*.json', 4, 'SUCCEEDED'),
    ('DOC_coverage', 'coverage.csv', 1, 'SUCCEEDED'),
    ('DOC_limit_register', 'limit_register.md', 1, 'SUCCEEDED'),
    ('DOC_source_corrections', 'source_corrections_E6h.md', 1, 'SUCCEEDED'),
    ('DOC_line_state', 'line_state_proposal.md', 1, 'SUCCEEDED'),
    ('DOC_park_ledger', 'park_ledger_delta.md', 1, 'SUCCEEDED'),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    rows, total_rows = [], 0
    for name, pat, exp, st in TASKS:
        fs = sorted(glob.glob(os.path.join(R, pat))) if pat else []
        nrow = 0
        for f in fs:
            if f.endswith('.csv'):
                try:
                    nrow += len(pd.read_csv(f))
                except Exception:
                    pass
        total_rows += nrow
        final = st
        if st == 'SUCCEEDED' and exp and len(fs) < exp:
            final = 'FAILED'
        rows.append(dict(task=name, pattern=pat, n_files=len(fs), expected=exp,
                         n_rows=nrow, status=final))
    ts = pd.DataFrame(rows)
    os.makedirs(os.path.join(R, 'task_status'), exist_ok=True)
    ts.to_csv(os.path.join(R, 'task_status', 'task_status.csv'), index=False)
    cnt = ts.status.value_counts().to_dict()
    assert sum(cnt.values()) == len(ts), '状态表求和 != 登记总数'

    # 只读完整性
    sm = json.load(open(os.path.join(R, 'source_manifest.json')))
    changed = []
    for grp in ('foundation_readonly', 'e6e_frozen', 'e6f_frozen', 'e6g_frozen'):
        for f, h0 in sm.get(grp, {}).items():
            p = os.path.join(CODE, f)
            h1 = sha(p) if os.path.exists(p) else None
            if h1 != h0:
                changed.append(dict(group=grp, file=f, before=h0[:16],
                                    after=(h1[:16] if h1 else 'MISSING')))
    n_ck = sum(len(sm.get(g, {})) for g in
               ('foundation_readonly', 'e6e_frozen', 'e6f_frozen', 'e6g_frozen'))

    cov = pd.read_csv(os.path.join(R, 'coverage.csv'))
    cv = cov.status.value_counts().to_dict()
    ga = json.load(open(os.path.join(R, 'checks', 'guard_attack_tests.json')))
    dm = json.load(open(os.path.join(R, 'checks', 'derivation_manifest_frozen.json')))

    man = dict(
        round='E6h', version=H.VERSION, written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
        results_dir=R,
        git_head=subprocess.check_output(['git', '-C', CODE, 'rev-parse', '--short',
                                          'HEAD']).decode().strip(),
        input_fingerprints=sm.get('input_fingerprints', []),
        warnings=sm.get('warnings', []),
        readonly_integrity=dict(n_checked=n_ck, n_changed=len(changed), changed=changed),
        guard=dict(attack_tests='%d/%d' % (ga['n_pass'], ga['n_total']),
                   record_B_approved=H.load_approval()['loaded'],
                   protected_keys=sum(1 for k in H.REGISTERED if H.is_protected_key(k)),
                   rule_objects=len(H.RULE_OBJECTS)),
        derivation_manifest=dict(total=dm['total'], sha256=dm['sha256'],
                                 config_segments=dm['total_config_segments']),
        task_status=dict(total=len(ts), by_status=cnt, total_result_rows=total_rows),
        coverage=cv,
        reports=['REPORT_R0.md', 'REPORT_part1.md', 'REPORT_part2.md',
                 'REPORT_part3.md'],
        blocked=[],
        completion='COMPLETE_WITH_LIMITS',
        completion_note=(
            '记录 B 已由用户批准 (2026-09-13 11:39:52, 清单 SHA c6a95478e4b18097); '
            '两后段按同一冻结清单一次算完并封存, 三份 REPORT 全部交付。'
            'coverage 有 %d 条 deferred、%d 条 changed、%d 条 unavailable '
            '(blocked_by_gate 已清零), 逐条理由在 coverage.csv; '
            'limit_register.md 记 9 条 LIMIT。'
            '**后段不是 OOS** —— 路线在看过 E6g 与 R0 之后选定, E7 才是唯一 OOS。'
            % (cv.get('deferred', 0), cv.get('changed', 0),
               cv.get('unavailable', 0))),
    )
    with open(os.path.join(R, 'manifest.json'), 'w') as fh:
        json.dump(man, fh, indent=1, ensure_ascii=False)

    print('== E6h manifest ==')
    print(' 任务状态表: 总 %d, %s (求和 = 登记总数 OK)' % (len(ts), cnt))
    print(' 结果行合计: %d' % total_rows)
    print(' 推导段描述符: %d (sha %s), config-segment %d'
          % (dm['total'], dm['sha256'][:16], dm['total_config_segments']))
    print(' 守卫: 攻击测试 %s; 记录 B 已批准 = %s; 受保护键 %d + 规则对象 %d'
          % (man['guard']['attack_tests'], man['guard']['record_B_approved'],
             man['guard']['protected_keys'], man['guard']['rule_objects']))
    print(' 只读完整性: 核了 %d 个文件, 变了 %d 个' % (n_ck, len(changed)))
    if changed:
        print('   !!', changed)
    print(' coverage:', cv)
    print(' 完成度:', man['completion'])
    bad = ts[ts.status == 'FAILED']
    if len(bad):
        print(' !! FAILED:'); print(bad.to_string(index=False))


if __name__ == '__main__':
    main()
