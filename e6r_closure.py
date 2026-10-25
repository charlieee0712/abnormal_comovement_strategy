# -*- coding: utf-8 -*-
"""E6r §C 收尾（附录 B.17 / B.18 / B.22 / B.24 / C；brief §8）：
  identities   stage0 恒等（含攻击）+ 第一道（T0_NOT_AGE1）+ 运行恒等（stats B）+ E7 守卫 → verify/identities_E6r.csv（56 必含）
  stage0       stage0 终版（part1 + part2〔S0-C / S0-B〕+ part3〔S0-L 空跑〕）→ diagnostics/stage0_E6r.csv
  schema       reports/SCHEMA.md（一表一行：文件 | 类型 | 行数或键数 | 键列 | 列名全列 | 单位列说明 | 生成脚本 | query_id 列是否存在 | 是否入 handoff | 样例行 | sha256）
               + reports/SCHEMA_DEVIATIONS.md
  seal_A2      registration/seal_A2.json（A2 产物清单 sha；之后才允许写后段）
  seal_final   registration/seal_final.json（first_post_segment_write_at = 后段账户最早落盘时刻）
  deploy_log   code_register/deploy_log.csv（全部 e6r_ 前缀文件 + sha + A1 冻结时 sha）
  gates        闭包门 ①–㉒ → verify/closure_E6r.csv；gates_post 另含 ㉓ / ㉔
  handoff      handoff/E6r_<ts>/ + HANDOFF_SHA256.txt + 全交接件敏感扫描；在结果目录内以相对路径运行决策端脚本
用法：python3 e6r_closure.py <子命令> [--root <相对 E6R_WORK 的根>]"""
import os
import re
import sys
import glob
import json
import time
import shutil
import argparse
import subprocess
from multiprocessing import get_context

import numpy as np
import pandas as pd

import e6r_core as O

IDENT_REQ = ['REPLICATION_E6Q_ACCOUNTS', 'SOURCE_ANCHOR_FRONTIER', 'ACCOUNTING_BRIDGE', 'CASH_EQUATION', 'NAV_TELESCOPE', 'FEE_NET_ORDER',
             'TICKET_CONSERVATION', 'TOKEN_CONSERVATION', 'LAMBDA0_EQ_FLAT', 'NO_BAD_GATE_EQ_FLAT', 'TILT_H_ALL_SAME_H_EQ_FLAT',
             'UNIFORM_CAP_010_EQ_FLAT', 'EXITOP_NONE_TRIGGER_EQ_NATIVE', 'CELL_ALL_UNKNOWN_EQ_FLAT', 'CELL_BUDGET_ACCOUNT_LAYER',
             'NA_PINNED_TO_X0', 'OVERLAY_APPLIED_ONCE', 'SAME_B_PLANNED', 'JOINT_FEASIBLE_PROJECTION', 'KL_SCALE_INVARIANT',
             'SOURCE_HG_FROM_PRE_OVERLAY_LIST', 'T0_NOT_AGE1', 'TIE_MIDRANK_NO_ID_SPLIT', 'NA_NEUTRAL_NOT_BAD', 'TICKETS_MULTISET_EXACT',
             'IDENTITY_DRAW_RETAINED', 'DETERMINISTIC_ONE_PATH', 'SEED_PROTOCOL_STABLE', 'SEED_NO_ROW_ORDER', 'GATE_COUNT_UNKNOWN_PROTECTED',
             'REARM_PENDING_PROMOTES_NOT_DUPLICATES', 'REARM_NO_DEADLINE_EXTENSION', 'SCALED_PRODUCT_BRIDGE', 'IMPACT_LOG_DOMAIN',
             'E_SCORE_RULES', 'CHECKPOINT_RESTORE_IDEMPOTENT', 'E7_GUARD',
             'SHARED_RESIDUAL_REGULAR_EXTRA', 'NO_NEW_NAME_THROUGH_PROJECTION', 'CAP_THEN_NORMALIZE_REJECTED', 'RANDOM_NO_RETURN_READ',
             'RANDOM_NO_OWNER_FUTURE', 'REARM_STATE_STRICT_RESTORE', 'REARM_UNKNOWN_NOT_CLEAR', 'SPLIT_ATOMIC', 'OVERSELL_REJECTED',
             'STRICT_ENUMS', 'S0_DERIV_WINDOW_END', 'LANDMARK_NO_FUTURE_GROUPING', 'LANDMARK_CENSOR_AT_CUTOFF', 'FUTURE_DATA_PLANT',
             'UNIT_PLANT', 'JOURNAL_REPLAY', 'POLICY_BOOL_EXPLICIT', 'OUTPUT_FRESH_DIR', 'LABEL_T0_ONLY']
ATTACK = set(IDENT_REQ[IDENT_REQ.index('SHARED_RESIDUAL_REGULAR_EXTRA'):])
INFO = {'SOURCE_ANCHOR_FRONTIER', 'ACCOUNTING_BRIDGE', 'E7_GUARD'}
ICOLS = ['check_id', 'description', 'exec_id', 'value', 'max_abs_diff', 'tolerance', 'status']
DIAG = ['diagnostics/D%d_%s_E6r.csv' % (i, n) for i, n in enumerate(['entry_age', 'transition', 'cvr_size', 'tilt_exit', 'concentration', 'risk', 'state_coverage',
                                                                     'second_block', 'h40', 'tail30', 'adaptation_bridge', 'closure'], start=1)] + ['diagnostics/G1_E6r.csv']
CONTRACT = ['registration/registry_E6r.csv', 'registration/comparisons_E6r.csv', 'registration/compound_contrasts_E6r.csv', 'registration/random_control_refs_E6r.csv',
            'registration/cost_feedback_refs_E6r.csv', 'registration/feedback_comparisons_E6r.csv', 'registration/local_snapshot_refs_E6r.csv',
            'registration/ledger_G_E6r.csv', 'registration/ledger_E_E6r.csv', 'registration/ledger_Q_E6r.csv', 'registration/cc_statement_carry.csv',
            'registration/G_E_CC_dependency_ledger_E6r.csv', 'registration/sources_E6r.csv', 'registration/permissions_E6r.csv', 'registration/exposure_E6r.csv',
            'registration/park_E6r.csv', 'statistics/account_summary_E6r.csv', 'statistics/comparison_results_E6r.csv', 'statistics/compound_results_E6r.csv',
            'statistics/randoms_E6r.csv', 'statistics/random_paths_main_E6r.csv', 'statistics/random_tilt_feasibility_E6r.csv', 'statistics/matching_E6r.csv',
            'statistics/policy_E6r.csv', 'statistics/policy_fields_E6r.csv', 'statistics/policy_mapping_E6r.csv', 'statistics/primary9_E6r.csv',
            'statistics/yearly_E6r.csv', 'statistics/cost_curve_E6r.csv', 'statistics/breakeven_E6r.csv', 'statistics/cost_feedback_E6r.csv',
            'statistics/cost_feedback_pairs_E6r.csv', 'statistics/weights_E6r.csv', 'verify/replication_E6r.csv', 'verify/curve_replication_E6r.csv',
            'verify/identities_E6r.csv', 'diagnostics/stage0_E6r.csv', 'diagnostics/landmark_E6r.csv', 'diagnostics/entry_tertiles_E6r.csv',
            'diagnostics/entry_transition_T0_age1_E6r.csv', 'diagnostics/entry_target_snapshot_E6r.csv', 'diagnostics/allocation_projection_E6r.csv',
            'events/event_counts_E6r.csv', 'events/exit_requests_E6r.csv', 'events/entry_gate_counterfactual_E6r.csv', 'reports/claims_E6r.csv',
            'reports/query_registry_E6r.csv', 'reports/e_results_E6r.csv', 'reports/e_summary_E6r.csv', 'reports/reflection_E6r.csv', 'accounts/daily/INDEX.csv',
            'trades/INDEX.csv', 'code_register/deploy_log.csv'] + DIAG
EXTRA = ['verify/identities_E6r_stage0.csv', 'verify/identities_E6r_g1.csv', 'verify/identities_E6r_runs.csv',
         'diagnostics/stage0_E6r_part1.csv', 'diagnostics/stage0_E6r_part2.csv', 'diagnostics/stage0_E6r_part3.csv']
GEN = {'registration': 'e6r_registry.py / e6r_a1.py / e6r_stage0.py / e6r_g1.py / e6r_claims.py / e6r_closure.py', 'statistics': 'e6r_stats.py / e6r_policy.py / e6r_registry.py',
       'diagnostics': 'e6r_diag.py / e6r_g1.py / e6r_stage0.py / e6r_closure.py', 'verify': 'e6r_stage0.py / e6r_g1.py / e6r_stats.py / e6r_closure.py',
       'events': 'e6r_stats.py / e6r_diag.py', 'reports': 'e6r_claims.py / e6r_reports.py / e6r_closure.py', 'accounts': 'e6r_stats.py', 'trades': 'e6r_stats.py',
       'code_register': 'e6r_closure.py'}
KEYS = {'registration/registry_E6r.csv': 'exec_id', 'registration/comparisons_E6r.csv': 'comparison_id', 'registration/compound_contrasts_E6r.csv': 'contrast_id|term_role',
        'registration/random_control_refs_E6r.csv': 'ref_id', 'registration/cost_feedback_refs_E6r.csv': 'feedback_id',
        'registration/feedback_comparisons_E6r.csv': 'left_feedback_id|right_feedback_id|kind', 'registration/local_snapshot_refs_E6r.csv': 'snapshot_id',
        'statistics/account_summary_E6r.csv': 'exec_id|segment', 'statistics/comparison_results_E6r.csv': 'comparison_id|segment',
        'statistics/compound_results_E6r.csv': 'contrast_id|segment', 'statistics/randoms_E6r.csv': 'ref_id|segment', 'statistics/policy_E6r.csv': 'exec_id|mapping',
        'statistics/policy_fields_E6r.csv': 'exec_id|mapping|field', 'statistics/yearly_E6r.csv': 'exec_id|year',
        'statistics/cost_curve_E6r.csv': 'exec_id|comparator_kind|comparator_exec_id|A_cny|kappa|exponent|segment', 'statistics/weights_E6r.csv': 'exec_id|layer|segment',
        'reports/claims_E6r.csv': 'claim_id', 'reports/query_registry_E6r.csv': 'query_id', 'verify/identities_E6r.csv': 'check_id',
        'diagnostics/stage0_E6r.csv': 'probe_id|key', 'diagnostics/landmark_E6r.csv': 'exec_id|landmark_age|state|q|weighting'}


def rds(root, rel):
    p = os.path.join(root, rel)
    if not os.path.exists(p) and os.path.exists(p + '.gz'):
        p = p + '.gz'
    if not os.path.exists(p):
        p2 = O.P(*rel.split('/'))
        p = p2 if os.path.exists(p2) else (p2 + '.gz')
    return pd.read_csv(p, keep_default_na=False, dtype=str)


def fpath(root, rel):
    for p in (os.path.join(root, rel), os.path.join(root, rel) + '.gz', O.P(*rel.split('/')), O.P(*rel.split('/')) + '.gz'):
        if os.path.exists(p):
            return p
    return ''


def sens_pattern():
    """敏感串：IPv4、凭据类词（拼接生成，代码文本里不出现原词）、运行时取得的用户目录名（不写字面量）、家目录前缀。"""
    words = ['pass' + 'w', chr(0x53e3) + chr(0x4ee4), chr(0x5bc6) + chr(0x7801), 'PRIVATE' + ' KEY', 'ssh' + '-rsa', 'ssh' + '-ed25519', 'tok' + 'en=', 'BEGIN ' + 'OPENSSH',
             'sec' + 'ret', 'api' + ' key', 'api' + '_key', '/ho' + 'me/']
    names = {os.path.basename(os.path.expanduser('~')), os.environ.get('USER', ''), os.environ.get('LOGNAME', ''),
             os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(O.work())))), os.path.basename(sys.prefix)}
    names = [re.escape(n) for n in names if n and len(n) >= 4 and n not in ('root', 'results', 'mnt', 'sda2', 'usr', 'local', 'python3', 'conda')]
    return re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b|' + '|'.join(re.escape(w) for w in words) + ('|' + '|'.join(names) if names else ''), re.I)


# ------------------------------------------------------------------ 恒等 / stage0
def identities(root):
    parts = []
    for rel, base in (('verify/identities_E6r_stage0.csv', O.work()), ('verify/identities_E6r_g1.csv', O.work()), ('verify/identities_E6r_runs.csv', root)):
        p = os.path.join(base, rel)
        if os.path.exists(p):
            parts.append(pd.read_csv(p, keep_default_na=False, dtype=str)[ICOLS])
    D = pd.concat(parts, ignore_index=True)
    # 同 check_id 以后写为准（运行恒等的 REPLICATION_E6Q_ACCOUNTS 覆盖 S0 的同名行：B 相实际结果）
    D = D.drop_duplicates('check_id', keep='last')
    maxdate = ''
    for rel in ('accounts/daily/INDEX.csv',):
        p = os.path.join(root, rel)
        if os.path.exists(p):
            DI = pd.read_csv(p, dtype=str, keep_default_na=False)
            maxdate = max(maxdate, DI.date_max.max() if len(DI) else '')
    for p in sorted(glob.glob(os.path.join(root, 'trades', '*.csv*')))[:40] + [os.path.join(root, 'statistics', 'yearly_E6r.csv')]:
        try:
            d = pd.read_csv(p, usecols=lambda c: c in ('date', 'lot_due', 'deadline'), dtype=str)
        except Exception:
            continue
        for c in d.columns:
            v = d[c][d[c].str.match(r'^\d{4}-\d{2}-\d{2}$', na=False)]
            if len(v) and v.max() > maxdate:
                maxdate = v.max()
    dates = np.load(os.path.join(O.cache_dir(), 'panels', 'dates.npy'))
    maxdate = max(maxdate, str(max(dates.tolist())))
    D = pd.concat([D, pd.DataFrame([dict(check_id='E7_GUARD', description='交付日序列 / 成交（样本）/ 年表与面板的最大日期 ≤ 授权终点 2026-03-27；E7 不读',
                                         exec_id='', value=maxdate[:10], max_abs_diff='', tolerance='', status='INFO' if maxdate[:10] <= O.CUTOFF else 'DIFFERS')])],
                  ignore_index=True)
    O.atomic_write_csv(os.path.join(root, 'verify', 'identities_E6r.csv'), D[ICOLS])
    miss = [c for c in IDENT_REQ if c not in set(D.check_id)]
    print(json.dumps(dict(rows=len(D), missing=miss, maxdate=maxdate[:10], status=D.status.value_counts().to_dict()), ensure_ascii=False), flush=True)


def stage0_final(root):
    ps = [O.P('diagnostics', 'stage0_E6r_part%d.csv' % i) for i in (1, 2, 3)]
    out = pd.concat([pd.read_csv(p, keep_default_na=False, dtype=str) for p in ps if os.path.exists(p)], ignore_index=True)
    O.atomic_write_csv(os.path.join(root, 'diagnostics', 'stage0_E6r.csv'), out)
    print(json.dumps(dict(rows=len(out), probes=sorted(out.probe_id.unique().tolist())), ensure_ascii=False), flush=True)


# ------------------------------------------------------------------ SCHEMA
def head_count(p):
    import gzip
    op = gzip.open if p.endswith('.gz') else open
    with op(p, 'rt', encoding='utf-8-sig', newline='') as f:
        hdr = f.readline().rstrip('\r\n')
        first = f.readline().rstrip('\r\n')
        n = (1 + sum(1 for _ in f)) if first else 0
    return hdr, first, n


def schema(root, in_handoff=True):
    pat = sens_pattern()
    lines = ['# E6r SCHEMA（由 e6r_closure.py schema 从实际文件生成；附录 B 合同 66 张；sha256 = 生成时文件）', '',
             '| 文件（相对结果目录） | 类型 | 行数或键数 | 键列 | 列名全列 | 单位列说明 | 生成脚本 | query_id 列是否存在 | 是否入 handoff | 样例行（一行真实值，脱敏） | sha256 |',
             '|---|---|---|---|---|---|---|---|---|---|---|']
    seen = set()
    for rel in CONTRACT + EXTRA:
        if rel in seen:
            continue
        seen.add(rel)
        p = fpath(root, rel)
        if not p:
            continue
        hdr, first, n = head_count(p)
        cols = hdr.split(',')
        unit = '有 unit 列' if 'unit' in cols else ('ann_pp / share / cny / bp（列名后缀）' if any(c.endswith(('_ann_pp', '_share', '_cny', '_bp')) for c in cols) else '见列名')
        sample = pat.sub('<redacted>', first)[:240].replace('|', '/')
        kind = 'csv.gz' if p.endswith('.gz') else 'csv'
        lines.append('| %s | %s | %d | %s | %s | %s | %s | %s | %s | %s | %s |' % (rel, kind, n, KEYS.get(rel, '').replace('|', ' + '), ' '.join(cols), unit,
                                                                              GEN.get(rel.split('/')[0], 'e6r_*'), '是' if 'query_id' in cols else '否',
                                                                              '是' if in_handoff else '否', sample, O.sha_file(p)))
    nd = len(glob.glob(os.path.join(root, 'accounts', 'daily', '*.csv'))) - 1
    nt = len(glob.glob(os.path.join(root, 'trades', '*.csv.gz')))
    lines += ['', '单位与口径说明：', '',
              '- `accounts/daily/<exec_hash>.csv`（%d 个，列 = 附录 B.21 日序列 19 列；`nav_post = nav_pre − fee`，`fee_ret = fee / nav_post_{t−1}`，`gross_excess_ret = net_excess_ret + fee_ret`）；'
              '`trades/<exec_hash>.csv.gz`（%d 个，列 = B.21 成交 21 列；INDEX 列出的 `.csv` 名按 D 脚本规则自动读 `.gz`）。' % (max(nd, 0), nt),
              '- `diagnostics/entry_target_snapshot_E6r.csv` 预算桥采用**不含费**口径：`planned_gross_budget_cny = paid_notional_cny + unspent_cny`（计划总预算 = 常规 ov_B + 额外 ov_xB；'
              '`actual_fee_cny` = 当日费用按买入名义份额分摊，另列不入桥）。',
              '- `statistics/account_summary_E6r.csv` 的 `size_dev_pp` 符号：正 = 偏小盘（同退出 FLAT 参照的 clean 市值分位资本加权均值 − 本账户，× 100）；'
              '`port3t_dev_pp` / `port3t_dev_noexit_pp` = PORT3_T（本账户 − 参照，× 100；政策只用四段 |·| 最大 ≤ 3）。',
              '- 随机路径日统计只存每个 (owner, 机制) 的 0 号路径（47 `randoms/daily/`，不入 handoff）；A2 末紧凑 checkpoint 在 47 `checkpoints/A2_rand/`（可删临时件）。',
              '- JSON：`registration/freeze_E6r.json`、`seal_A2.json`、`seal_final.json`；`registration/spec/*.json` 为合同脚本 11 件产物原样。', '']
    O.atomic_write_text(os.path.join(root, 'reports', 'SCHEMA.md'), '\n'.join(lines) + '\n')
    dev = ['# E6r SCHEMA_DEVIATIONS（表 | 列 | 原因 | 影响的探针）', '',
           '| 表 | 列 | 原因 | 影响的探针 |', '|---|---|---|---|',
           '| diagnostics/entry_tertiles_E6r.csv | G4 行数值列 | 计数与资本份额是可加会计量，逐列四段中位后 n_names = Σ 五类与份额和 = 1 不再成立 → G4 行 status = NOT_APPLICABLE、数值留空（FULL 与四段已全给） | S34（只核 COMPUTED 行） |',
           '| trades/<exec_hash>.csv | 文件 | 以 `.csv.gz` 无损压缩存放（INDEX 写 `.csv` 名；D 脚本 read_csv_any 两种都读） | S32 |',
           '| statistics/cost_curve_E6r.csv | 文件 | 以 `.csv.gz` 存放 | S27 / S22 |',
           '| statistics/randoms_E6r.csv | status | 引用整体 CONTROL_NOT_COMPARABLE 或 STRUCTURAL_DEGENERATE 时各段同标（c4 记 NA 并写原因），不只标 FULL 行 | S15（FULL 非 COMPUTED / MC_LIMIT 时跳过该引用） |',
           '| diagnostics/entry_target_snapshot_E6r.csv | RAW_TILT_WITHIN_CELL_TICKETS / REAL_GATE_RANDOM_TILT / RANDOM_GATE_REAL_TILT 行 | 本轮不另跑（brief：局部快照只读、不跑），status = NOT_APPLICABLE 并写缺因 | S34（只核存在与 COMPUTED 行的桥） |',
           '| verify/identities_E6r.csv | REPLICATION_E6Q_ACCOUNTS | S0 首测（S0 账户全历史）后由 B 相实际结果重算覆盖（同 check_id 取后写） | S12 / S13 |', '']
    O.atomic_write_text(os.path.join(root, 'reports', 'SCHEMA_DEVIATIONS.md'), '\n'.join(dev) + '\n')
    print('SCHEMA rows', len([l for l in lines if l.startswith('| ') and '.csv' in l]), flush=True)


# ------------------------------------------------------------------ seal / deploy_log
def manifest(globs, mp):
    man = []
    for g in globs:
        for p in sorted(glob.glob(g, recursive=True)):
            if os.path.isfile(p) and '.tmp' not in os.path.basename(p):
                man.append('%s  %s' % (O.sha_file(p), os.path.relpath(p, O.work())))
    O.atomic_write_text(mp, '\n'.join(man) + '\n')
    return len(man)


def seal_A2(root):
    p = O.P('registration', 'seal_A2.json')
    if os.path.exists(p):
        raise SystemExit('seal_A2.json 已存在（只写一次）')
    if glob.glob(O.P('accounts_run', 'full', '*', '*.npz')):
        raise SystemExit('已有后段账户结果，不能再 seal_A2')
    mp = O.P('registration', 'seal_A2_manifest.txt')
    n = manifest([O.P('accounts_run', 'deriv', '**', '*.npz'), O.P('accounts_run', 'deriv_fb', '**', '*.npz'), O.P('accounts_run', 'shadow_deriv', '**', '*.npz'),
                  O.P('trades_parts', 'deriv', '**', '*.npz'), O.P('randoms', 'random_paths_A2.csv'), O.P('diagnostics', 'G1_E6r.csv'),
                  O.P('diagnostics', 'stage0_E6r_part*.csv'), O.P('verify', 'identities_E6r_*.csv'), O.P('registration', '*.csv'), O.P('registration', 'freeze_E6r.json')], mp)
    s = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), n_files=n, sha256_manifest=O.sha_file(mp), manifest='registration/seal_A2_manifest.txt')
    O.atomic_write_json(p, s)
    print(json.dumps(s, ensure_ascii=False), flush=True)


def seal_final(root):
    fs = glob.glob(O.P('accounts_run', 'full', '*', '*.npz')) + glob.glob(O.P('trades_parts', 'full', '*', '*.npz'))
    first = min(os.path.getmtime(f) for f in fs) if fs else time.time()
    mp = O.P('registration', 'seal_final_manifest.txt')
    n = manifest([os.path.join(root, s, '*.*') for s in ('statistics', 'events', 'diagnostics', 'verify', 'reports')], mp)
    s = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), n_files=n, sha256_manifest=O.sha_file(mp), manifest='registration/seal_final_manifest.txt',
             first_post_segment_write_at=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first)))
    O.atomic_write_json(O.P('registration', 'seal_final.json'), s)
    print(json.dumps(s, ensure_ascii=False), flush=True)


DEV_SCRIPTS = ('e6r_smoke.py', 'e6r_rtcheck.py', 'e6r_rtnodes.py', 'e6r_cktest.py')
SCHED_ROLES = {'e6r_membind.py': '调度辅助：设内存策略（MPOL_BIND）后 exec 目标命令，只影响内存放置、不改计算',
               'e6r_chain.sh': '调度辅助：串行链（步骤日志与 done / failed 标记）', 'e6r_bg.sh': '调度辅助：后台启动器',
               'e6r_after_a2.sh': '调度辅助：A2 → B 衔接', 'e6r_after_b.sh': '调度辅助：B → 交付衔接', 'e6r_wait.sh': '调度辅助：等待条件（只读）'}


def deploy_log(root):
    here = os.path.dirname(os.path.abspath(__file__))
    fz = json.load(open(O.P('registration', 'freeze_E6r.json'), encoding='utf-8'))
    a1 = fz.get('code_sha256', {})
    rows = []
    for f in sorted(os.listdir(here)):
        if f.startswith('e6r_') and (f.endswith('.py') or f.endswith('.sh')):
            sha = O.sha_file(os.path.join(here, f))
            rows.append(dict(file=f, sha256=sha, bytes=os.path.getsize(os.path.join(here, f)), sha256_at_A1=a1.get(f, ''),
                             changed_after_A1='' if f not in a1 else ('yes' if a1[f] != sha else 'no'),
                             role=SCHED_ROLES.get(f) or ('开发期核验脚本（不在交付链）' if f in DEV_SCRIPTS else 'E6r 模块（只 import 复用 e6q_* / e6p_* 等既有模块，不改）')))
    os.makedirs(os.path.join(root, 'code_register'), exist_ok=True)
    O.atomic_write_csv(os.path.join(root, 'code_register', 'deploy_log.csv'), pd.DataFrame(rows))
    print(json.dumps(dict(files=len(rows), changed_after_A1=int(sum(r['changed_after_A1'] == 'yes' for r in rows))), ensure_ascii=False), flush=True)


# ------------------------------------------------------------------ 闭包门
GATE_ROWS = []


def gate(no, desc, ok, detail=''):
    GATE_ROWS.append(dict(gate=no, description=desc, status='PASS' if ok else 'FAIL', detail=str(detail)[:400]))


def numv(s):
    return pd.to_numeric(s, errors='coerce')


def gates(root, stage='pre'):
    del GATE_ROWS[:]
    W = O.work()
    R = rds(W, 'registration/registry_E6r.csv')
    spec = json.load(open(O.P('registration', 'spec', 'registry.json'), encoding='utf-8'))
    bad = [r['logical_id'] for r in spec if O.logical_id_of(r['spec']) != r['logical_id']]
    cnt = R.groupby('scenario').size().to_dict()
    gate('①', 'registry 350 行、payload / groups = spec、情景 341 / 9、逻辑 id 重算', len(R) == 350 and cnt.get(O.FEAS) == 341 and cnt.get(O.IDEAL) == 9 and not bad
         and set(R.logical_id) == {r['logical_id'] for r in spec}, dict(cnt=cnt, bad=len(bad)))
    ids, lids = set(R.exec_id), set(R.logical_id)
    C = rds(W, 'registration/comparisons_E6r.csv')
    PC = rds(W, 'registration/compound_contrasts_E6r.csv')
    RR = rds(W, 'registration/random_control_refs_E6r.csv')
    FR = rds(W, 'registration/cost_feedback_refs_E6r.csv')
    FC = rds(W, 'registration/feedback_comparisons_E6r.csv')
    LS = rds(W, 'registration/local_snapshot_refs_E6r.csv')
    ok2 = (len(C) == 2988 and set(C.left_exec_id) <= ids and set(C.right_exec_id) <= ids and PC.contrast_id.nunique() == 20 and set(PC.term_exec_id) <= ids
           and len(RR) == 1408 and set(RR.owner_logical_id) <= lids and len(FR) == 202 and len(FC) == 1822 and len(LS) == 359 and set(LS.owner_exec_id) <= ids)
    gate('②', 'comparisons / compound / refs / 反馈 / 快照全部 id 在 registry、计数 = F 节', ok2,
         dict(comparisons=len(C), compound=PC.contrast_id.nunique(), refs=len(RR), feedback=len(FR), pairs=len(FC), snapshots=len(LS)))
    AS = rds(root, 'statistics/account_summary_E6r.csv')
    full = AS.groupby('exec_id').segment.nunique()
    c = AS[AS.segment != 'G4']
    gfn = (numv(c.gross_ann_pp) - numv(c.fee_ann_pp) - numv(c.net_ann_pp)).abs().max()
    seg = AS[AS.segment.isin(O.SEGS)]
    fl = AS[AS.segment == 'FULL'].set_index('exec_id')
    rec = (seg.assign(w=numv(seg.net_ann_pp) * numv(seg.n_days)).groupby('exec_id').w.sum() / numv(seg.n_days).groupby(seg.exec_id).sum())
    fd = (rec - numv(fl.net_ann_pp).reindex(rec.index)).abs().max()
    gate('③', 'account_summary 350 × 6、gross − fee = net、FULL n_days 加权', (full == 6).all() and len(full) == 350 and gfn <= 1e-8 and fd <= 1e-8,
         dict(objects=len(full), gross_fee_net=gfn, FULL_identity=fd))
    CR = rds(root, 'statistics/comparison_results_E6r.csv')
    KR = rds(root, 'statistics/compound_results_E6r.csv')
    gate('④', 'comparison_results 2,988 × 6、compound_results 20 × 6', CR.comparison_id.nunique() == 2988 and len(CR) == 2988 * 6 and KR.contrast_id.nunique() == 20 and len(KR) == 120,
         dict(cr=len(CR), kr=len(KR)))
    I = rds(root, 'verify/identities_E6r.csv')
    miss = [k for k in IDENT_REQ if k not in set(I.check_id)]
    att_bad = I[I.check_id.isin(ATTACK) & (I.status != 'BLOCKED')]
    pas = I[I.status == 'PASS']
    tol_bad = pas[numv(pas.max_abs_diff) > numv(pas.tolerance)]
    oth_bad = I[I.check_id.isin(set(IDENT_REQ) - ATTACK - INFO) & ~I.status.isin(['PASS', 'SOURCE_BINDING_PENDING'])]
    gate('⑤', 'identities 56 项全在、恒等类 ≤ 容差、攻击类全 BLOCKED', not miss and not len(att_bad) and not len(tol_bad) and not len(oth_bad),
         dict(missing=miss, attack_bad=len(att_bad), tol_bad=list(tol_bad.check_id)[:5], other_bad=list(oth_bad.check_id.unique())[:5]))
    REP = rds(root, 'verify/replication_E6r.csv')
    CRV = rds(root, 'verify/curve_replication_E6r.csv')
    gate('⑥', '58 个复现锚 × 四段 PASS、4 个曲线锚 PASS', REP.e6r_exec_id.nunique() == 58 and len(REP) == 232 and (REP.status == 'PASS').all() and len(CRV) == 4 and
         (CRV.status == 'PASS').all(), dict(rep=len(REP), rep_pass=int((REP.status == 'PASS').sum()), curve=len(CRV)))
    RD = rds(root, 'statistics/randoms_E6r.csv')
    fr = RD[RD.segment == 'FULL']
    sto = fr[fr.mcse != '']
    mcb = (numv(sto.mcse) - numv(sto.rand_sd_D_ann_pp) / np.sqrt(numv(sto.paths))).abs().max() if len(sto) else 0.0
    det = fr[fr.mechanism == 'LEVEL_WORST_1D']
    tgt = fr[(fr.mcse_target != '') & (fr.mcse != '')]
    pb = tgt[(numv(tgt.mcse) > numv(tgt.mcse_target) + 1e-12) & (tgt.status == 'COMPUTED')]      # 同 D 脚本 S15：只核 COMPUTED；MC_LIMIT 已达上限，不可比 / 结构退化整条跳过
    gate('⑦', 'randoms 覆盖 1,408、MCSE 恒等 / 精度或 MC_LIMIT、确定性 1 路', fr.ref_id.nunique() == 1408 and mcb <= 1e-6 and (numv(det.paths) == 1).all() and not len(pb),
         dict(refs=fr.ref_id.nunique(), mcse_identity=mcb, precision_bad=len(pb), mc_limit=int((fr.status == 'MC_LIMIT').sum())))
    FE = rds(root, 'statistics/random_tilt_feasibility_E6r.csv')
    fe = FE[FE.status == 'COMPUTED']
    acct_ok = ((numv(fe.n_cohort_draws) == numv(fe.n_feasible) + numv(fe.n_proved_no_match) + numv(fe.n_algorithm_limit)) &
               (numv(fe.n_feasible) == numv(fe.n_identity_draw) + numv(fe.n_nonidentity_draw))).all()
    tk = fe[fe.mechanism.isin(['RANDOM_TILT_TICKETS', 'RANDOM_GATE_TILT_JOINT'])]
    gate('⑧', '随机路径表与可行性表恒等（抽样计数；TICKETS / JOINT Σw / Σw² ≤ 1e−9）', acct_ok and (numv(tk.max_rel_sum_w_diff).fillna(0) <= 1e-9).all() and
         (numv(tk.max_rel_sum_w2_diff).fillna(0) <= 1e-9).all(), dict(rows=len(fe)))
    PO = rds(root, 'statistics/policy_E6r.csv')
    PF = rds(root, 'statistics/policy_fields_E6r.csv')
    ok9 = (len(PO) == 700 and len(PF) == 5600 and set(PO.mapping) == {'E6R_POLICY_ESTIMAND', 'E6Q_ORIGINAL_AUDIT'} and set(PO.verdict) <= {'通过', '不通过', '不可判'}
           and (PO[PO.verdict == '不可判'].undecidable_reason != '').all() and set(PO.reconciliation_status) == {'RECONCILED'})
    gate('⑨', 'policy 700 行与 8 字段、两映射、词表、不可判必有原因、RECONCILED', ok9, dict(rows=len(PO), fields=len(PF), verdicts=PO.verdict.value_counts().to_dict()))
    CL = rds(root, 'reports/claims_E6r.csv')
    QR = set(rds(root, 'reports/query_registry_E6r.csv').query_id)
    req = ['Q%02d' % i for i in range(1, 19)] + ['E%02d' % i for i in range(1, 8)] + ['G-P-%02d' % i for i in range(1, 5)] + ['GW%02d' % i for i in range(1, 9)] + \
        ['CC-E6r-%02d' % i for i in range(1, 10)]
    ER = rds(root, 'reports/e_results_E6r.csv')
    ES = rds(root, 'reports/e_summary_E6r.csv')
    okes = len(ES) == 1 and int(ES.n_registered.iloc[0]) == 7 and int(ES.n_supported.iloc[0]) == int((ER.status == '支持').sum())
    gate('⑩', 'claims 必含 id、query 闭合、E 状态 = e_results、e_summary 计数', set(req) <= set(CL.claim_id) and set(CL.query_id) - {''} <= QR and okes and
         all(CL.set_index('claim_id').loc[e, 'claim_status'] == s for e, s in zip(ER.e_id, ER.status)), dict(missing=sorted(set(req) - set(CL.claim_id))[:5]))
    LG, LE, LQ = rds(W, 'registration/ledger_G_E6r.csv'), rds(W, 'registration/ledger_E_E6r.csv'), rds(W, 'registration/ledger_Q_E6r.csv')
    CC = rds(W, 'registration/cc_statement_carry.csv')
    spcc = pd.read_csv(O.P('registration', 'spec', 'cc_statement_carry.csv'), dtype=str, keep_default_na=False).set_index('statement_id')
    okcc = len(CC) == 9 and all(CC.set_index('statement_id').loc[i, k] == spcc.loc[i, k] for i in spcc.index for k in ('verbatim', 'source_sha256', 'source_line'))
    DL = rds(W, 'registration/G_E_CC_dependency_ledger_E6r.csv')
    gate('⑪', '账本 G 12 / E 7 / Q 18、CC 原句逐字、依赖账覆盖 E01–E07', len(LG) == 12 and len(LE) == 7 and len(LQ) == 18 and okcc and
         {'E%02d' % i for i in range(1, 8)} <= set(DL[DL.kind == 'E'].item_id), dict(G=len(LG), E=len(LE), Q=len(LQ), cc=okcc))
    S0 = rds(root, 'diagnostics/stage0_E6r.csv')
    gw = S0[(S0.probe_id == 'S0-C') & (S0.key == 'RETURN_END_MAX')]
    gate('⑫', 'stage0 S0-A…S0-L 全有行、S0-G 键、GW 收益窗 ≤ 2018-12-31', {'S0-' + x for x in 'ABCDEFGHIJKL'} <= set(S0.probe_id) and len(S0[S0.probe_id == 'S0-G']) >= 44
         and {'GW%02d' % i for i in range(1, 9)} <= set(gw.item) and (gw.value <= '2018-12-31').all(), dict(probes=sorted(S0.probe_id.unique())))
    EV = rds(root, 'events/event_counts_E6r.csv')
    RQ = rds(root, 'events/exit_requests_E6r.csv')
    GC = rds(root, 'events/entry_gate_counterfactual_E6r.csv')
    okev = (numv(EV.n_intents) == numv(EV.n_realized_early) + numv(EV.n_late_fill) + numv(EV.n_unfilled) + numv(EV.n_censored)).all() and len(EV) == 350
    okrq = (numv(RQ.n_requests) == numv(RQ.n_completed_before_deadline) + numv(RQ.n_forced_deadline_override) + numv(RQ.n_completed_after_due_objective)).all()
    gate('⑬', 'events / requests 恒等、门反事实覆盖', okev and okrq and GC.exec_id.nunique() == int(R.weight_scheme.isin(['GATE_STATE', 'GATE_TILT', 'DROP_T3']).sum()),
         dict(events=len(EV), requests=len(RQ), gate_cf=GC.exec_id.nunique()))
    CU = rds(root, 'statistics/cost_curve_E6r.csv')
    BE = rds(root, 'statistics/breakeven_E6r.csv')
    FB = rds(root, 'statistics/cost_feedback_E6r.csv')
    FP = rds(root, 'statistics/cost_feedback_pairs_E6r.csv')
    g_ = CU.groupby(['exec_id', 'comparator_kind']).size()
    abs_ok = all(g_.get((e_, 'ABSOLUTE'), 0) >= 180 for e_ in R.exec_id)
    gate('⑭', '成本曲线网格（ABSOLUTE 每账户 30 × 6）、breakeven 词表、反馈 202 × 6 与 1,822 × 6', abs_ok and set(BE.root_kind) <= {'POSITIVE_ROOT', 'LOWER_CROSSING', 'NO_ROOT',
         'OUT_OF_GRID', 'OUT_OF_NUMERICAL_RANGE', 'COST_MISSING', 'NOT_APPLICABLE'} and len(FB) == 202 * 6 and len(FP) == 1822 * 6, dict(fb=len(FB), fp=len(FP)))
    DI = rds(root, 'accounts/daily/INDEX.csv')
    ex = all(fpath(root, f) for f in DI.file)
    nd = numv(AS[AS.segment == 'FULL'].set_index('exec_id').n_days)
    mism = (numv(DI.set_index('exec_id').n_rows) - nd.reindex(DI.exec_id).values).abs().max() if len(DI) else 1
    TI = rds(root, 'trades/INDEX.csv')
    gate('⑮', 'accounts/daily 覆盖全部 350 与 n_rows 恒等；成交 INDEX 覆盖', len(DI) == 350 and ex and mism == 0 and len(TI) == 350, dict(index=len(DI), mismatch=mism))
    WT = rds(root, 'statistics/weights_E6r.csv')
    AP = rds(root, 'diagnostics/allocation_projection_E6r.csv')
    apc = AP[AP.status == 'COMPUTED']
    viol = max(numv(apc.max_rel_total_diff).max(), numv(apc.max_cap_violation).max(), numv(apc.max_industry_violation).max()) if len(apc) else 0.0
    SN = rds(root, 'diagnostics/entry_target_snapshot_E6r.csv')
    gate('⑯', 'weights 三层、投影违约 ≤ 1e−9、三分位 / 转移 / 359 快照表', WT.groupby('exec_id').size().min() == 18 and viol <= 1e-9 and SN.snapshot_id.nunique() == 359,
         dict(viol=viol, snapshots=SN.snapshot_id.nunique()))
    sp = os.path.join(root, 'reports', 'SCHEMA.md')
    sm = open(sp, encoding='utf-8').read() if os.path.exists(sp) else ''
    badS = []
    for line in sm.splitlines():
        if line.startswith('| ') and '.csv' in line.split('|')[1]:
            cells = [x.strip() for x in line.strip().strip('|').split('|')]
            p = fpath(root, cells[0])
            if not p:
                badS.append(cells[0])
                continue
            hdr, first, n = head_count(p)
            if int(cells[2]) != n or cells[4] != ' '.join(hdr.split(',')):
                badS.append(cells[0])
    miss_t = [t for t in CONTRACT if ('| %s |' % t) not in sm]
    gate('⑰', 'SCHEMA.md 行数 = 实际、列名 = 表头、合同表全在、DEVIATIONS 存在', bool(sm) and not badS and not miss_t and
         os.path.exists(os.path.join(root, 'reports', 'SCHEMA_DEVIATIONS.md')), dict(bad=badS[:5], missing=miss_t[:5]))
    fz = json.load(open(O.P('registration', 'freeze_E6r.json'), encoding='utf-8'))
    keys = ['plan_sha256', 'plan_body_sha256', 'contract_sha256', 'contract_artifact_sha256', 'brief_sha256', 'appendix_sha256', 'd_script_sha256', 'schema_contract_sha256',
            'policy_file_sha256', 'source_fn_sha256', 'data_cutoff', 'protocol', 'mode', 'authorizations', 'authorized_by', 'authorized_at', 'written_at', 'cache_tag',
            'e6q_registry_sha256', 'reconciliation_status']
    s2 = json.load(open(O.P('registration', 'seal_A2.json'), encoding='utf-8')) if os.path.exists(O.P('registration', 'seal_A2.json')) else {}
    sf = json.load(open(O.P('registration', 'seal_final.json'), encoding='utf-8')) if os.path.exists(O.P('registration', 'seal_final.json')) else {}
    gate('⑱', 'freeze 全键（九授权、11 件产物 sha、RECONCILED）；seal_A2.written_at < 后段首次写入', all(k in fz for k in keys) and len(fz['authorizations']) == 9 and
         len(fz['contract_artifact_sha256']) == 11 and fz['reconciliation_status'] == 'RECONCILED' and str(s2.get('written_at', '9')) < str(sf.get('first_post_segment_write_at', '')),
         dict(seal_A2=s2.get('written_at'), first_post=sf.get('first_post_segment_write_at')))
    pat_nan = re.compile(r'(?<![A-Za-z_])(nan|None)(?![A-Za-z_])')
    nanf = [f for f in glob.glob(os.path.join(root, 'reports', '*.md')) + glob.glob(os.path.join(root, 'reports', '*.csv')) if pat_nan.search(open(f, encoding='utf-8').read())]
    gate('⑲', '报告（md / csv）无字面 nan / None', not nanf, [os.path.basename(f) for f in nanf])
    e7 = I[I.check_id == 'E7_GUARD'].value.astype(str).max()
    gate('⑳', '全部文件最大日期 ≤ 2026-03-27', e7 <= O.CUTOFF and (DI.date_max.max() <= O.CUTOFF if len(DI) else True), e7)
    cdn = os.path.basename(O.cache_dir())
    gate('㉑', '缓存目录含 E6r-v1.1 与 c89305fb', 'E6r-v1.1' in cdn and 'c89305fb' in cdn, cdn)
    r0p = os.path.join(root, 'reports', 'E6r_REPORT_R0.md')
    r0 = open(r0p, encoding='utf-8').read()[:6000] if os.path.exists(r0p) else ''
    gate('㉒', 'R0 页首写明无 E7 / 无部署授权、协议 v1.6、方式 B、授权九值、R5 研究 1.5% 只在研究账户', all(x in r0 for x in (
        'E7', 'deployment_authorized = false', 'v1.6', '方式 B', 'main_A_cny', 'sub_A_cny', 'research_metric', 'product_metric', 'frontier_anchor_logical_id', 'mainline',
        'r5_single_stock_research_parameter', '1.5%')))
    vt = open(O.P('verify', 'spec', 'spec_run.txt'), encoding='utf-8').read()
    okf = all(O.sha_file(O.P('verify', 'spec', k)) == v for k, v in O.SPEC_SHA.items())
    gate('㉓', 'verify/spec 11 指纹 = plan 附录 B、234 PASS' + ('；verify/decision/out_E6r_stage2/ 含探针 CSV' if stage == 'post' else ''),
         okf and '234' in vt and (stage != 'post' or os.path.exists(O.P('verify', 'decision', 'out_E6r_stage2', 'E6r_D_probes_stage2.csv'))), dict(fingerprints=okf))
    if stage == 'post':
        sj = O.P('handoff', '%s_scan.json' % os.path.basename(root_handoff())) if root_handoff() else ''
        sc_ = json.load(open(sj, encoding='utf-8')) if sj and os.path.exists(sj) else dict(n_hits=-1, hits=[['no scan record', '']])
        gate('㉔', '全交接件扫描：无登录信息 / 主机标识 / 用户目录名 / __pycache__（决策端脚本原件按 sha 豁免）', sc_.get('n_hits') == 0, sc_.get('hits', [])[:5])
    G_ = pd.DataFrame(GATE_ROWS)
    O.atomic_write_csv(os.path.join(root, 'verify', 'closure_E6r.csv' if stage == 'pre' else 'closure_post_E6r.csv'), G_)
    print(G_.to_string()[:8000], flush=True)
    return G_


def root_handoff():
    p = O.P('handoff', 'LATEST_E6r.txt')
    return open(p).read().strip() if os.path.exists(p) else ''


# ------------------------------------------------------------------ handoff
_SCAN_PAT = None


def _scan_file(p):
    global _SCAN_PAT
    if _SCAN_PAT is None:
        _SCAN_PAT = sens_pattern()
    import gzip
    op = gzip.open if p.endswith('.gz') else open
    with op(p, 'rt', encoding='utf-8', errors='replace') as fh:
        while True:
            chunk = fh.read(1 << 24)
            if not chunk:
                return None
            if _SCAN_PAT.search(chunk):
                return os.path.relpath(p, O.work())


def handoff_scan(hd):
    hits, todo = [], []
    for dp, dn, fn in os.walk(hd):
        if '__pycache__' in dp or any(d == '__pycache__' for d in dn):
            hits.append(('__pycache__', os.path.relpath(dp, O.work())))
        for f in fn:
            p = os.path.join(dp, f)
            if f.endswith('.pyc'):
                hits.append(('pyc', f))
                continue
            if f == 'E6r_D_stage2.py' and O.sha_file(p) == O.D_SCRIPT_SHA256:
                continue
            if f.endswith(('.csv', '.md', '.txt', '.json', '.py', '.sh', '.gz')):
                todo.append(p)
    todo.sort(key=lambda x: -os.path.getsize(x))
    with get_context('fork').Pool(96) as pool:
        for r in pool.imap_unordered(_scan_file, todo, chunksize=1):
            if r:
                hits.append(('pattern', r))
    return hits


def _sha_rel(args):
    p, base = args
    return O.sha_file(p), os.path.relpath(p, base)


def handoff(root):
    ts = time.strftime('%Y%m%d_%H%M')
    hd = O.P('handoff', 'E6r_%s' % ts)
    os.makedirs(hd, exist_ok=True)
    W = O.work()

    def link(src, dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            return
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)
    for sub in ('registration', 'accounts/daily', 'trades', 'statistics', 'diagnostics', 'events', 'reports', 'verify', 'code_register'):
        sd = os.path.join(root, sub)
        for dp, dn, fn in os.walk(sd):
            dn[:] = [d for d in dn if d not in ('__pycache__', 'decision_tmp')]
            for f in fn:
                if '.tmp' in f or f.endswith('.pyc'):
                    continue
                link(os.path.join(dp, f), os.path.join(hd, os.path.relpath(os.path.join(dp, f), root)))
    here = os.path.dirname(os.path.abspath(__file__))
    for f in sorted(os.listdir(here)):
        if f.startswith('e6r_') and (f.endswith('.py') or f.endswith('.sh')):
            link(os.path.join(here, f), os.path.join(hd, 'code_register', 'src', f))
    O.atomic_write_text(O.P('handoff', 'LATEST_E6r.txt'), os.path.relpath(hd, W) + '\n')
    hits = handoff_scan(hd)
    O.atomic_write_json(O.P('handoff', '%s_scan.json' % os.path.basename(hd)), dict(n_hits=len(hits), hits=[list(h) for h in hits[:50]],
                                                                                  scanned_at=time.strftime('%Y-%m-%d %H:%M:%S')))
    files = []
    for dp, dn, fn in os.walk(hd):
        for f in fn:
            if f != 'HANDOFF_SHA256.txt':
                files.append((os.path.join(dp, f), hd))
    with get_context('fork').Pool(64) as pool:
        shas = pool.map(_sha_rel, files, chunksize=16)
    O.atomic_write_text(os.path.join(hd, 'HANDOFF_SHA256.txt'), '\n'.join('%s  %s' % (s, r) for s, r in sorted(shas, key=lambda x: x[1])) + '\n')
    print(json.dumps(dict(handoff=os.path.relpath(hd, W), files=len(files), scan_hits=hits[:10], n_hits=len(hits)), ensure_ascii=False), flush=True)
    return hd, hits


def run_d(hd, root_rel='.'):
    """决策端脚本：在结果目录内以相对路径运行（stdout 不含绝对路径）；输出入 handoff，清单同路径以本次为准（E6q 交付后修正）。"""
    W = O.work()
    d = O.P('verify', 'decision')
    assert O.sha_file(os.path.join(d, 'E6r_D_stage2.py')) == O.D_SCRIPT_SHA256
    tmp = O.P('tmp', 'pyc_d')
    os.makedirs(tmp, exist_ok=True)
    env = dict(os.environ, PYTHONPYCACHEPREFIX=tmp, PYTHONDONTWRITEBYTECODE='1')
    rel_hd = os.path.relpath(hd, W)
    out_rel = 'verify/decision/out_E6r_stage2' if root_rel == '.' else os.path.join(root_rel, 'verify', 'decision', 'out_E6r_stage2')
    cmd = [sys.executable, 'verify/decision/E6r_D_stage2.py', '--root', root_rel, '--handoff', rel_hd, '--out', out_rel]
    p = subprocess.run(cmd, cwd=W, env=env, capture_output=True, text=True)
    out = os.path.join(W, out_rel)
    os.makedirs(out, exist_ok=True)
    O.atomic_write_text(os.path.join(out, 'stdout_tail.txt'), O.san((p.stdout + '\n' + p.stderr)[-8000:]))
    lines = []
    for f in sorted(os.listdir(out)):
        src = os.path.join(out, f)
        dst = os.path.join(hd, 'verify', 'decision', 'out_E6r_stage2', f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copy2(src, dst)
        lines.append('%s  %s' % (O.sha_file(dst), os.path.relpath(dst, hd)))
    mp = os.path.join(hd, 'HANDOFF_SHA256.txt')
    ent = {}
    for l in [x.rstrip('\n') for x in open(mp, encoding='utf-8') if x.strip()] + lines:
        s, r = l.split('  ', 1)
        ent[r] = s
    O.atomic_write_text(mp, '\n'.join('%s  %s' % (ent[r], r) for r in sorted(ent)) + '\n')
    summ = [l for l in p.stdout.splitlines() if l.startswith('SUMMARY')]
    print(json.dumps(dict(rc=p.returncode, outputs=len(lines), summary=summ[-1] if summ else ''), ensure_ascii=False), flush=True)
    return p.returncode


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd')
    ap.add_argument('--root', default='')
    ap.add_argument('--handoff', default='')
    a = ap.parse_args()
    root = O.P(*a.root.split('/')) if a.root else O.work()
    if a.cmd == 'gates':
        G_ = gates(root, 'pre')
        sys.exit(0 if (G_.status == 'PASS').all() else 2)
    elif a.cmd == 'gates_dry':                          # S0-L 空跑：照跑全部门，结果只记录不阻断（假后段 + 占位 seal 时序门预期不过）
        gates(root, 'pre')
    elif a.cmd == 'gates_post':
        G_ = gates(root, 'post')
        sys.exit(0 if (G_.status == 'PASS').all() else 2)
    elif a.cmd == 'handoff':
        hd, hits = handoff(root)
        if hits:
            print('交付扫描命中，不交付', flush=True)
            sys.exit(3)
        run_d(hd)
    elif a.cmd == 'run_d':
        run_d(O.P(*a.handoff.split('/')), a.root or '.')
    else:
        {'identities': identities, 'stage0': stage0_final, 'schema': schema, 'seal_A2': seal_A2, 'seal_final': seal_final, 'deploy_log': deploy_log}[a.cmd](root)
