# -*- coding: utf-8 -*-
"""E6o S0-12：按 brief 附录 B 的 SCHEMA 合同生成决策端脚本的夹具目录（每张合同表一行示例、列名全列；
accounts/daily/ 一个 10 行文件；HANDOFF_SHA256.txt 覆盖夹具文件）。夹具只用于检验脚本能编译、能跑完、每个探针都有状态行；
夹具上的 DIFFERS / NOT_COMPUTABLE 是预期结果。不含任何真实数据。
用法：python3 e6o_s0_fixture.py --out <夹具目录>"""
import argparse
import csv
import hashlib
import json
import os

MAIN = 'A4b_CVRv5|a0.25|HG10|H5|T1b|ENGINE_NATIVE|lag1|RESET_H|ALLOW|OFF|ON|FEASIBLE_DAILY|ACCOUNT|FULLHIST|CASH_V0|POLICY_E6O_PARENT_Q'
PA = 'A4b_CVRv5|a0.25|HG10|H5|NONE|NA|NA|NA|NA|OFF|OFF|FEASIBLE_DAILY|ACCOUNT|FULLHIST|CASH_V0|POLICY_E6O_PARENT_Q'
PS = 'A4b_CVRv5|a0.25|HG10|H5|NONE|NA|NA|NA|NA|OFF|OFF|SOURCE|SOURCE|FULLHIST|CASH_V0|POLICY_E6O_PARENT_Q'

TABLES = {
    'registration/registry_E6o.csv': (
        ['exec_id', 'exec_hash', 'logical_id', 'family', 'series', 'form', 'Qalpha', 'memory', 'H', 'trigger', 'trigger_formula_hash',
         'source_ref_contract', 'funding', 'recycle_lag', 'recycle_maturity', 'reentry', 'entry_guard', 'exit_enabled', 'execution_profile',
         'accounting_backend', 'support', 'start_state', 'policy_version', 'source_hash', 'parent_exec_id', 'source_parent_exec_id',
         'is_primary72', 'is_main_object', 'status'],
        [[MAIN, '0' * 16, 'L0', 'CORE', 'C_ACCOUNT', 'A4b_CVRv5', 'a0.25', 'HG10', 'H5', 'T1b', 'h', 'c', 'ENGINE_NATIVE', 'lag1', 'RESET_H',
          'ALLOW', 'OFF', 'ON', 'FEASIBLE_DAILY', 'ACCOUNT', 'FULLHIST', 'CASH_V0', 'POLICY_E6O_PARENT_Q', 's', PA, PS, '1', '1', 'COMPUTED'],
         [PA, '1' * 16, 'P0', 'PARENT', 'P_ACCOUNT', 'A4b_CVRv5', 'a0.25', 'HG10', 'H5', 'NONE', 'h', 'c', 'NA', 'NA', 'NA', 'NA', 'OFF', 'OFF',
          'FEASIBLE_DAILY', 'ACCOUNT', 'FULLHIST', 'CASH_V0', 'POLICY_E6O_PARENT_Q', 's', '', '', '0', '0', 'COMPUTED'],
         [PS, '2' * 16, 'P1', 'PARENT', 'P_SOURCE', 'A4b_CVRv5', 'a0.25', 'HG10', 'H5', 'NONE', 'h', 'c', 'NA', 'NA', 'NA', 'NA', 'OFF', 'OFF',
          'SOURCE', 'SOURCE', 'FULLHIST', 'CASH_V0', 'POLICY_E6O_PARENT_Q', 's', '', '', '0', '0', 'COMPUTED']]),
    'registration/comparisons_E6o.csv': (
        ['comparison_id', 'kind', 'child_exec_id', 'parent_exec_id', 'execution_profile', 'note'],
        [['C0', 'MAIN_EXIT', MAIN, PA, 'FEASIBLE_DAILY', 'fixture']]),
    'registration/ledger_G_E6o.csv': (
        ['g_id', 'author', 'exact_statement', 'created_at', 'created_before_measurement', 'source_facts', 'motivation', 'competing_explanation',
         'proposed_estimand', 'probe_code_hash', 'probe_window', 'probe_result', 'status', 'root_cause_evidence', 'derived_from', 'new_direction',
         'next_test', 'operation_type', 'data_exposure', 'registration_provenance', 'timestamp_artifact', 'expectation_before_probe_verbatim',
         'expected_statement_provenance', 'measurement_at', 'result_at', 'interpretation_at', 'derived_hypothesis_at', 'original_g_id',
         'linked_e_ids', 'tested_or_unmeasured', 'pre_or_post_exposure', 'evidence_vs_candidate_explanation'],
        [['G-F2-01'] + ['x'] * 31]),
    'registration/ledger_E_E6o.csv': (
        ['e_id', 'g_ids', 'author', 'original_version', 'exact_prediction', 'prediction_or_question', 'selected_before_outcome', 'prior_exposure',
         'first_stage_evidence', 'formal_contrast', 'target_population', 'unit', 'comparison_ids', 'support_ids', 'query_id', 'result',
         'evidence_strength', 'miss_root', 'next_change'],
        [['E01'] + ['x'] * 18]),
    'statistics/account_summary_E6o.csv': (
        ['exec_id', 'execution_profile', 'segment', 'support', 'n_days', 'net_ann_pp', 'abs_net_ann_pp', 'gross_ann_pp', 'fee_ann_pp',
         'parent_exec_id', 'parent_net_ann_pp', 'D_ann_pp', 'source_parent_exec_id', 'D_source_ann_pp', 'D_sc_ann_pp', 'hac_se_H', 'hac_se_2H',
         'hac_se_max', 'boot_lo', 'boot_hi', 'exposure_mean', 'cash_share_mean', 'turnover_ann', 'n_exit_intents', 'n_realized_early',
         'n_late_fill', 'n_unfilled', 'n_censored', 'n_reentries', 'n_internal_transfers', 'cash_lock_cny_days', 'status'],
        [[MAIN, 'FEASIBLE_DAILY', 'FULL', 'FULLHIST', '10', '1.0', '1.0', '1.0', '0.1', PA, '0.5', '0.5', PS, '0.4', '0.3', '0.1', '0.1', '0.1',
          '0.1', '0.9', '0.5', '0.5', '20', '3', '2', '1', '0', '0', '0', '0', '100', 'COMPUTED']]),
    'statistics/randoms_E6o.csv': (
        ['owner_exec_id', 'mechanism', 'segment', 'paths', 'real_D_ann_pp', 'rand_mean_D_ann_pp', 'rand_sd_D_ann_pp', 'mcse', 'rank_real',
         'unmatched_share', 'status'],
        [[MAIN, 'AMOUNT_MATCH', 'FULL', '128', '0.5', '0.1', '0.08', '0.007071067811865475', '0.9', '0', 'COMPUTED']]),
    'statistics/random_paths_main_E6o.csv': (
        ['owner_exec_id', 'mechanism', 'path_id', 'seed', 'FULL_D_ann_pp', 'n_unmatched_days'],
        [[MAIN, 'AMOUNT_MATCH', '0', '1', '0.1', '0']]),
    'diagnostics/stage0_E6o.csv': (
        ['probe_id', 'item', 'key', 'value', 'unit', 'status', 'source_file', 'note'],
        [['S0-0', 'fixture', 'B2_TRIGGER_KIND', 'EDGE', 'count', 'INFO', 'f', 'fixture']]),
    'statistics/policy_E6o.csv': (
        ['exec_id', 'execution_profile', 'profile_name', 'policy_version', 'c1_segment_tolerance_ok', 'c2_year_positive_share', 'c2_ok',
         'c3_full_sc_same_sign', 'c4_random_post_ok', 'c5_impact_ok', 'c6_declared_ok', 'port3t_dev_pp', 'port3t_ok', 'verdict',
         'research_status', 'partial_history_years', 'mapping_unresolved_fields', 'status'],
        [[MAIN, 'FEASIBLE_DAILY', 'POLICY_E6O_PARENT_Q', 'v', '1', '0.7', '1', '1', '1', '1', '1', '0.1', '1', '不可判', '证据有限', '', '',
          'COMPUTED']]),
    'statistics/main72_E6o.csv': (
        ['exec_id', 'trigger', 'form', 'memory', 'FULL_D_ann_pp', 'G4_D_ann_pp', 'D_2010-2014', 'D_2015-2018', 'D_2019-2023', 'D_2024-2026',
         'rank_vs_random', 'verdict', 'research_status'],
        [[MAIN, 'T1b', 'A4b_CVRv5', 'HG10', '0.5', '0.4', '0.1', '0.2', '0.3', '0.4', '0.9', '不可判', '证据有限']]),
    'verify/identities_E6o.csv': (
        ['check_id', 'description', 'exec_id', 'value', 'max_abs_diff', 'tolerance', 'status'],
        [['E7_GUARD', 'fixture', '', '2026-03-27', '0', '0', 'PASS']]),
    'events/event_counts_E6o.csv': (
        ['exec_id', 'trigger', 'n_intents', 'n_realized_early', 'n_late_fill', 'n_unfilled', 'n_censored', 'n_unknown_state_days',
         'n_reentry_blocked', 'n_reentry_reconfirmed', 'n_internal_transfers', 'mean_realized_hold_days', 'median_realized_hold_days', 'status'],
        [[MAIN, 'T1b', '3', '2', '1', '0', '0', '0', '0', '0', '0', '2.5', '2', 'COMPUTED']]),
    'reports/claims_E6o.csv': (
        ['claim_id', 'kind', 'author', 'statement', 'query_id', 'table', 'exec_ids', 'result_value', 'result_sign', 'ci_lo', 'ci_hi',
         'claim_status', 'note'],
        [['Q01', 'QUESTION', 'fixture', 'fixture', 'QF', 't', MAIN, '0', '+', '-1', '1', '开放', '']]),
    'reports/query_registry_E6o.csv': (
        ['query_id', 'table', 'filter', 'n_rows', 'generator'],
        [['QF', 't', 'f', '1', 'g']]),
    'code_register/deploy_log.csv': (
        ['file', 'sha256', 'status', 'written_at'],
        [['e6o_s0_fixture.py', '0' * 64, 'NEW', '2026-10-17 00:00:00']]),
}
DIAGS = ['D1_size_dose_E6o', 'D2_age_weight_E6o', 'D3_capacity_E6o', 'D4_regime_E6o', 'D5_veto_exit_E6o', 'D6_minute_kleg_E6o', 'G1_E6o']
DIAG_COLS = ['block', 'item', 'key1', 'key2', 'segment', 'stat', 'value', 'unit', 'n', 'status', 'query_id']


def wcsv(path, cols, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(cols)
        for r in rows:
            if len(r) != len(cols):
                raise ValueError('fixture row width %s' % path)
            w.writerow(r)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    R = a.out
    for rel, (cols, rows) in TABLES.items():
        wcsv(os.path.join(R, rel), cols, rows)
    for d in DIAGS:
        wcsv(os.path.join(R, 'diagnostics', d + '.csv'), DIAG_COLS, [[d, 'fixture', '', '', 'FULL', 'n', '0', 'count', '0', 'NOT_APPLICABLE', 'QF']])
    dcols = ['date', 'nav_pre', 'nav_post', 'fee', 'exposure', 'bench_ret', 'net_excess_ret', 'cash_share', 'n_holdings', 'n_exits_today']
    rows = [['2020-01-%02d' % (i + 2), '1.0', '1.0', '0', '0.5', '0.001', '0.0001', '0.5', '10', '0'] for i in range(10)]
    wcsv(os.path.join(R, 'accounts', 'daily', '0' * 16 + '.csv'), dcols, rows)
    wcsv(os.path.join(R, 'accounts', 'daily', '1' * 16 + '.csv'), dcols, rows)
    wcsv(os.path.join(R, 'accounts', 'daily', 'INDEX.csv'), ['exec_hash', 'exec_id', 'file', 'n_rows', 'date_min', 'date_max'],
         [['0' * 16, MAIN, '0' * 16 + '.csv', '10', '2020-01-02', '2020-01-11'], ['1' * 16, PA, '1' * 16 + '.csv', '10', '2020-01-02', '2020-01-11']])
    os.makedirs(os.path.join(R, 'registration'), exist_ok=True)
    with open(os.path.join(R, 'registration', 'freeze_E6o.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(plan_sha256='fixture', data_cutoff='2026-03-27', protocol='v1.6', mode='B'), f)
    with open(os.path.join(R, 'registration', 'seal_A2.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(written_at='2026-10-17 00:00:00', n_files=0, sha256_manifest={}), f)
    with open(os.path.join(R, 'registration', 'seal_final.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(written_at='2026-10-18 00:00:00', n_files=0, sha256_manifest={}, first_post_segment_write_at='2026-10-17 00:00:01'), f)
    os.makedirs(os.path.join(R, 'verify', 'spec'), exist_ok=True)
    with open(os.path.join(R, 'verify', 'spec', 'SHA256.txt'), 'w', encoding='utf-8') as f:
        f.write('%s  registry.json\n' % ('0' * 64))
    with open(os.path.join(R, 'verify', 'spec', 'spec_run.txt'), 'w', encoding='utf-8') as f:
        f.write('fixture\n')
    os.makedirs(os.path.join(R, 'reports'), exist_ok=True)
    with open(os.path.join(R, 'reports', 'SCHEMA.md'), 'w', encoding='utf-8') as f:
        f.write('| 文件 | 类型 | 行数或键数 |\n|---|---|---|\n| registration/registry_E6o.csv | csv | 3 |\n')
    with open(os.path.join(R, 'reports', 'SCHEMA_DEVIATIONS.md'), 'w', encoding='utf-8') as f:
        f.write('无\n')
    with open(os.path.join(R, 'reports', 'E6o_REPORT_fixture.md'), 'w', encoding='utf-8') as f:
        f.write('fixture report\n')
    hd = os.path.join(R, 'handoff')
    os.makedirs(hd, exist_ok=True)
    lines = []
    for root, _dirs, files in os.walk(R):
        if os.path.abspath(root).startswith(os.path.abspath(hd)) or '/out' in root:
            continue
        for fn in sorted(files):
            p = os.path.join(root, fn)
            lines.append('%s  %s' % (sha(p), os.path.relpath(p, hd)))
    with open(os.path.join(hd, 'HANDOFF_SHA256.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(lines)) + '\n')
    print('fixture written: %d contract tables, %d diag tables, handoff lines %d' % (len(TABLES), len(DIAGS), len(lines)))


if __name__ == '__main__':
    main()
