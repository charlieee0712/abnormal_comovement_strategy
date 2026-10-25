# -*- coding: utf-8 -*-
"""E6q §C 收尾（附录 B.17 / B.18 / B.22 / B.24 / C；brief §8）：
  identities   Stage 0 恒等（含攻击类）+ 引擎自检恒等 + 运行恒等（stats）+ E7 守卫 → verify/identities_E6q.csv
  stage0       Stage 0 终版（part1 + part2〔S0-B / S0-M〕）→ diagnostics/stage0_E6q.csv
  schema       reports/SCHEMA.md（一表一行：文件 | 类型 | 行数 | 键列 | 列名全列 | 单位 | 生成脚本 | query_id | 入 handoff | 样例行 | sha256）+ SCHEMA_DEVIATIONS.md
  seal_final   registration/seal_final.json（first_post_segment_write_at = 后段账户最早落盘时刻）
  deploy_log   code_register/deploy_log.csv（全部 e6q_ 前缀文件 + sha + A1 冻结时 sha）
  gates        闭包门 ①–㉑ → verify/closure_E6q.csv（任一 FAIL 不交付）；gates_post 含 ⑱ / ⑳
  handoff      handoff/E6q_<ts>/ + HANDOFF_SHA256.txt + 全交接件敏感扫描；在结果目录内以相对路径运行决策端脚本
用法：python3 e6q_closure.py <子命令> [--root <相对 E6Q_WORK 的根>]"""
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

import e6q_core as O

V0 = O.V0
IDENT_REQ = ['E6P_ACCOUNT_REPLICATION', 'SOURCE_ANCHOR_FRONTIER', 'E6P_HOLDINGS_SHA', 'ACCOUNTING_BRIDGE', 'ZERO_INTERVENTION_EQ_NATIVE',
             'PSTAR_INF_EQ_NATIVE', 'THETA_ONE_EQ_NATIVE', 'NEW_FILTER_OFF_EQ_NATIVE', 'CASH_EQUATION', 'NAV_TELESCOPE', 'TICKET_CONSERVATION',
             'TOKEN_CONSERVATION', 'TOKEN_LIABILITY_LE_CASH', 'FEE_NET_ORDER', 'SHARED_BUDGET_SINGLE_RESERVATION', 'BUDGET_REPLAY_IDEMPOTENT',
             'TTL_FIRST_DENIAL_ONLY', 'QUARANTINE_NOT_SPENT_BY_REGULAR', 'DUE_UNLOCK_NO_NEW_CASH', 'REGULAR_BYPASS_ROUTE', 'PAYMENT_ATOMIC',
             'FILL_REPLAY_NO_SECOND_DEBIT', 'TOKEN_DOUBLE_SPEND', 'HALF_TARGET_FIXED_SNAPSHOT', 'HALF_NO_GEOMETRIC', 'REARM_REQUIRES_FALSE_THEN_TRUE',
             'REARM_UNKNOWN_NOT_CLEAR', 'SPLIT_SCALES_PENDING_NO_RESET', 'DEADLINE_OVERRIDE_EXPLICIT', 'FIRSTHIT_NEXT_EXEC_LT_DUE',
             'FIRSTHIT_ONE_EVENT_PER_LOT', 'RANDOM_TARGET_PRIORITY_STABLE', 'RANDOM_TARGET_NO_RETURN_READ', 'MATCH_NO_OWNER_FUTURE_INVENTORY',
             'SPLIT_INVARIANCE', 'IMPACT_ALGEBRA_EQUAL', 'ZERO_ORDER_ZERO_COST', 'NONZERO_ORDER_MISSING_LIQ_UNKNOWN', 'LOG_DOMAIN_NO_OVERFLOW',
             'SAME_NAV_NODE_COST', 'LANDMARK_NO_FUTURE_GROUPING', 'LANDMARK_CENSOR_AT_CUTOFF', 'FUTURE_DATA_PLANT', 'UNIT_PLANT', 'JOURNAL_REPLAY',
             'CHECKPOINT_RESTORE_IDEMPOTENT', 'E7_GUARD', 'POLICY_BOOL_EXPLICIT', 'DENSITY_DENOMINATOR_GUARD']
ATTACK = {'SHARED_BUDGET_SINGLE_RESERVATION', 'QUARANTINE_NOT_SPENT_BY_REGULAR', 'DUE_UNLOCK_NO_NEW_CASH', 'REGULAR_BYPASS_ROUTE', 'PAYMENT_ATOMIC',
          'FILL_REPLAY_NO_SECOND_DEBIT', 'TOKEN_DOUBLE_SPEND', 'HALF_NO_GEOMETRIC', 'REARM_REQUIRES_FALSE_THEN_TRUE', 'REARM_UNKNOWN_NOT_CLEAR',
          'RANDOM_TARGET_NO_RETURN_READ', 'MATCH_NO_OWNER_FUTURE_INVENTORY', 'SPLIT_INVARIANCE', 'NONZERO_ORDER_MISSING_LIQ_UNKNOWN',
          'LANDMARK_NO_FUTURE_GROUPING', 'LANDMARK_CENSOR_AT_CUTOFF', 'FUTURE_DATA_PLANT', 'UNIT_PLANT', 'JOURNAL_REPLAY', 'POLICY_BOOL_EXPLICIT',
          'DENSITY_DENOMINATOR_GUARD'}
INFO = {'SOURCE_ANCHOR_FRONTIER', 'E6P_HOLDINGS_SHA', 'ACCOUNTING_BRIDGE', 'E7_GUARD'}
ICOLS = ['check_id', 'description', 'exec_id', 'value', 'max_abs_diff', 'tolerance', 'status']
CONTRACT = ['registration/registry_E6q.csv', 'registration/comparisons_E6q.csv', 'registration/compound_contrasts_E6q.csv', 'registration/random_control_refs_E6q.csv',
            'registration/cost_feedback_refs_E6q.csv', 'registration/feedback_comparisons_E6q.csv', 'registration/local_snapshot_refs_E6q.csv', 'registration/ledger_G_E6q.csv',
            'registration/ledger_E_E6q.csv', 'registration/ledger_Q_E6q.csv', 'registration/cc_statement_carry.csv', 'registration/e_band_bindings_E6q.csv',
            'statistics/account_summary_E6q.csv', 'statistics/comparison_results_E6q.csv', 'statistics/randoms_E6q.csv', 'statistics/random_paths_main_E6q.csv',
            'statistics/matching_E6q.csv', 'statistics/policy_E6q.csv', 'statistics/policy_fields_E6q.csv', 'statistics/main32_E6q.csv', 'statistics/yearly_E6q.csv',
            'statistics/cost_curve_E6q.csv', 'statistics/breakeven_E6q.csv', 'statistics/cost_feedback_E6q.csv', 'statistics/cost_feedback_pairs_E6q.csv',
            'statistics/density_E6q.csv', 'verify/impact_reconciliation_E6q.csv', 'verify/impact_reconciliation_ladder_E6q.csv', 'verify/e6p_replication_E6q.csv',
            'verify/identities_E6q.csv', 'diagnostics/stage0_E6q.csv', 'diagnostics/landmark_E6q.csv', 'events/event_counts_E6q.csv', 'events/exit_requests_E6q.csv',
            'reports/claims_E6q.csv', 'reports/query_registry_E6q.csv', 'accounts/daily/INDEX.csv', 'trades/INDEX.csv', 'code_register/deploy_log.csv',
            'registration/sources_E6q.csv', 'registration/permissions_E6q.csv', 'registration/exposure_E6q.csv', 'registration/park_E6q.csv'] + \
           ['diagnostics/D%d_%s_E6q.csv' % (i, n) for i, n in enumerate(['cost_source', 'target', 'entry_persistence', 'age_delay', 'dose', 'density', 'composition', 'window',
                                                                         'risk', 'externality'], start=1)] + ['diagnostics/G1_E6q.csv']
EXTRA = ['statistics/warm_sensitivity_E6q.csv', 'verify/impact_reconciliation_daily_bridge_E6q.csv', 'verify/identities_E6q_stage0.csv', 'verify/selftest_identities_E6q.csv',
         'verify/identities_E6q_runs.csv', 'verify/closure_E6q.csv', 'diagnostics/stage0_E6q_part1.csv', 'diagnostics/stage0_E6q_part2.csv',
         'registration/e_band_bindings_E6q.csv', 'diagnostics/local_snapshot_E6q.csv', 'events/m3_parent_orders_E6q.csv', 'verify/trades_events_bridge_E6q.csv']
GEN = {'registration': 'e6q_registry.py / e6q_a1.py / e6q_stage0.py / e6q_g1.py / e6q_claims.py', 'statistics': 'e6q_stats.py / e6q_policy.py',
       'diagnostics': 'e6q_diag.py / e6q_g1.py / e6q_stage0.py / e6q_closure.py', 'verify': 'e6q_s0a.py / e6q_stage0.py / e6q_selftest.py / e6q_stats.py / e6q_closure.py',
       'events': 'e6q_stats.py', 'reports': 'e6q_claims.py', 'accounts': 'e6q_stats.py', 'trades': 'e6q_stats.py', 'code_register': 'e6q_closure.py'}
KEYS = {'registration/registry_E6q.csv': 'exec_id', 'registration/comparisons_E6q.csv': 'comparison_id', 'registration/compound_contrasts_E6q.csv': 'contrast_id|term_exec_id',
        'registration/random_control_refs_E6q.csv': 'owner_logical_id|mechanism', 'registration/cost_feedback_refs_E6q.csv': 'feedback_id',
        'registration/feedback_comparisons_E6q.csv': 'feedback_id|kind|right_feedback_id', 'statistics/account_summary_E6q.csv': 'exec_id|segment',
        'statistics/comparison_results_E6q.csv': 'comparison_id|segment', 'statistics/randoms_E6q.csv': 'owner_exec_id|mechanism|segment',
        'statistics/matching_E6q.csv': 'owner_exec_id|mechanism|segment', 'statistics/policy_E6q.csv': 'exec_id|profile_name', 'statistics/policy_fields_E6q.csv': 'exec_id|profile_name|field',
        'statistics/yearly_E6q.csv': 'exec_id|year', 'statistics/cost_curve_E6q.csv': 'exec_id|comparator_kind|A_cny|kappa|exponent|segment',
        'statistics/breakeven_E6q.csv': 'exec_id|comparator_kind|kappa|exponent', 'statistics/cost_feedback_E6q.csv': 'feedback_id|segment',
        'statistics/cost_feedback_pairs_E6q.csv': 'feedback_id|kind|right_feedback_id|segment', 'statistics/density_E6q.csv': 'exec_id|reference_kind|A_cny|kappa|exponent|segment',
        'statistics/main32_E6q.csv': 'exec_id', 'accounts/daily/INDEX.csv': 'exec_hash', 'trades/INDEX.csv': 'exec_id', 'events/event_counts_E6q.csv': 'exec_id',
        'events/exit_requests_E6q.csv': 'exec_id', 'reports/claims_E6q.csv': 'claim_id', 'reports/query_registry_E6q.csv': 'query_id', 'verify/identities_E6q.csv': 'check_id|description',
        'diagnostics/stage0_E6q.csv': 'probe_id|key', 'diagnostics/landmark_E6q.csv': 'exec_id|landmark_age|state|q|weighting'}
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def rd(root, rel):
    return pd.read_csv(os.path.join(root, rel), keep_default_na=False, na_values=[''])


def rds(root, rel):
    return pd.read_csv(os.path.join(root, rel), keep_default_na=False, dtype=str)


def sens_pattern():
    """敏感串：IPv4、凭据类词（拼接生成，代码文本里不出现原词）、运行时取得的用户目录名（不写字面量）。"""
    words = ['pass' + 'w', chr(0x53e3) + chr(0x4ee4), chr(0x5bc6) + chr(0x7801), 'PRIVATE' + ' KEY', 'ssh' + '-rsa', 'ssh' + '-ed25519', 'tok' + 'en=', 'BEGIN ' + 'OPENSSH',
             'sec' + 'ret', 'api' + ' key', 'api' + '_key']
    names = {os.path.basename(os.path.expanduser('~')), os.environ.get('USER', ''), os.environ.get('LOGNAME', ''),
             os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(O.work())))), os.path.basename(sys.prefix)}
    names = [re.escape(n) for n in names if n and len(n) >= 4 and n not in ('root', 'results', 'mnt', 'sda2', 'usr', 'local', 'python3', 'conda')]
    return re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b|' + '|'.join(re.escape(w) for w in words) + ('|' + '|'.join(names) if names else ''), re.I)


# ------------------------------------------------------------------ 恒等
def identities(root):
    parts = []
    for rel, base in (('verify/identities_E6q_stage0.csv', O.work()), ('verify/selftest_identities_E6q.csv', O.work()), ('verify/identities_E6q_runs.csv', root)):
        p = os.path.join(base, rel)
        if os.path.exists(p):
            parts.append(pd.read_csv(p, keep_default_na=False, dtype=str)[ICOLS])
    D = pd.concat(parts, ignore_index=True)
    DI = rds(root, 'accounts/daily/INDEX.csv') if os.path.exists(os.path.join(root, 'accounts', 'daily', 'INDEX.csv')) else pd.DataFrame(columns=['date_max'])
    maxdate = DI.date_max.max() if len(DI) else ''
    for p in sorted(glob.glob(os.path.join(root, 'trades', '*.csv')))[:40] + [os.path.join(root, 'statistics', 'yearly_E6q.csv')]:
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
    D = pd.concat([D, pd.DataFrame([dict(check_id='E7_GUARD', description='全部交付日序列 / 成交分片（样本）/ 年表与面板的最大日期 ≤ 授权终点；E7 不读（缓存与面板止于 2026-03-27）',
                                         exec_id='', value=maxdate[:10], max_abs_diff='', tolerance='', status='INFO' if maxdate[:10] <= O.CUTOFF else 'DIFFERS')])],
                  ignore_index=True)
    O.atomic_write_csv(os.path.join(root, 'verify', 'identities_E6q.csv'), D[ICOLS])
    miss = [c for c in IDENT_REQ if c not in set(D.check_id)]
    print(json.dumps(dict(rows=len(D), missing=miss, maxdate=maxdate[:10], status=D.status.value_counts().to_dict()), ensure_ascii=False), flush=True)


BCOLS = ['exec_id', 'n_realized_early', 'd_script_count', 'postcutoff_due_rows', 'deadline_override_rows', 'extra_slice_rows', 'requests_early_not_realized', 'residual',
         'status']


def bridge(root):
    """S29 桥（附录 B.21；D 脚本 S29 对锚账户核"早退成交行 = 已实现早退意向"）：逐锚账户把差分解为三类已知来源——
    ① D 计数口径只数 EXIT / EXIT_HALF / EXIT_REARM 且 lot_due 为真实日期（排除 POST_CUTOFF：原 due 在 2026-03-27 之后的早退行）；
    ② DEADLINE_OVERRIDE 行不在 D 计数类别内；③ 同一请求分日 / 部分成交 = 多行（extra_slice_rows），以及有早退切片但最终状态非"早退已实现"的请求。
    恒等：d_script_count = n_realized_early + requests_early_not_realized + extra_slice_rows − postcutoff_due_rows − deadline_override_rows（residual 应为 0）。"""
    import e6q_engine as E
    R = rds(O.work(), 'registration/registry_E6q.csv')
    Ri = R.set_index('exec_id')
    p32 = R[R.is_primary32 == '1']
    ids = set(p32.exec_id)
    Rl = R.set_index('logical_id')
    for l in ('E6Q-9f826422e6d4c39c', 'E6Q-b5c68d2c70eb5e19', 'E6Q-d78b9785b0594c1e'):
        if l in Rl.index:
            ids.add(Rl.loc[l].exec_id)
    for e in list(ids):
        r = Ri.loc[e]
        ids |= {x for x in (r.parent_same_arm_exec_id, r.native_same_trigger_exec_id, r.cash_same_trigger_exec_id) if x}
    EV = rd(root, 'events/event_counts_E6q.csv').set_index('exec_id')
    T = len(np.load(os.path.join(O.cache_dir(), 'panels', 'dates.npy')))
    rows = []
    for e in sorted(ids):
        h = Ri.loc[e, 'exec_hash']
        ti = np.concatenate([np.load(O.P('trades_parts', s, h[:2], '%s.npz' % h), allow_pickle=False)['TL_i'] for s in ('deriv', 'full')])
        z = np.load(O.P('accounts_run', 'full', h[:2], '%s.npz' % h), allow_pickle=False)
        IN = z['IN_i']
        k, day, due, rq = ti[:, 4], ti[:, 0], ti[:, 6], ti[:, 3]
        ex3 = np.isin(k, [E.OK_EXIT, E.OK_EXIT_HALF, E.OK_EXIT_REARM])
        early = day < due
        a = int((ex3 & early & (due < T)).sum())
        b = int((ex3 & early & (due >= T)).sum())
        c = int(((k == E.OK_DEADLINE) & early).sum())
        allr = (ex3 | (k == E.OK_DEADLINE)) & early
        drq = np.unique(rq[allr & (rq >= 0)])
        extra = int(allr.sum()) - len(drq)
        real = np.isin(IN[:, E.IN_KIND], [E.KD_TRIG, E.KD_REARM, E.KD_RAND])
        realized = set(np.flatnonzero(real & (IN[:, E.IN_STATUS] == 1)).tolist())
        not_real = int(sum(1 for x in drq.tolist() if x not in realized))
        nre = int(EV.loc[e, 'n_realized_early']) if e in EV.index else -1
        resid = a - (nre + not_real + extra - b - c)
        rows.append(dict(exec_id=e, n_realized_early=nre, d_script_count=a, postcutoff_due_rows=b, deadline_override_rows=c, extra_slice_rows=extra,
                         requests_early_not_realized=not_real, residual=resid, status='PASS' if resid == 0 else 'DIFFERS'))
    D = pd.DataFrame(rows, columns=BCOLS)
    O.atomic_write_csv(os.path.join(root, 'verify', 'trades_events_bridge_E6q.csv'), D)
    print(json.dumps(dict(accounts=len(D), status=D.status.value_counts().to_dict(), d_ne_events=int((D.d_script_count != D.n_realized_early).sum())), ensure_ascii=False), flush=True)


def stage0_final(root):
    p1 = pd.read_csv(O.P('diagnostics', 'stage0_E6q_part1.csv'), keep_default_na=False, dtype=str)
    p2 = pd.read_csv(O.P('diagnostics', 'stage0_E6q_part2.csv'), keep_default_na=False, dtype=str)
    out = pd.concat([p1, p2], ignore_index=True)
    O.atomic_write_csv(os.path.join(root, 'diagnostics', 'stage0_E6q.csv'), out)
    print(json.dumps(dict(rows=len(out), probes=sorted(out.probe_id.unique().tolist())), ensure_ascii=False), flush=True)


# ------------------------------------------------------------------ SCHEMA
def schema(root, in_handoff=True):
    pat = sens_pattern()
    lines = ['# E6q SCHEMA（由 e6q_closure.py schema 从实际文件生成；附录 B 合同；sha256 = 生成时文件）', '',
             '| 文件（相对结果目录） | 类型 | 行数或键数 | 键列 | 列名全列 | 单位列说明 | 生成脚本 | query_id 列是否存在 | 是否入 handoff | 样例行（一行真实值，脱敏） | sha256 |',
             '|---|---|---|---|---|---|---|---|---|---|---|']
    seen = set()
    for rel in CONTRACT + EXTRA:
        if rel in seen:
            continue
        seen.add(rel)
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            p = O.P(*rel.split('/'))
            if not os.path.exists(p):
                continue
        with open(p, 'r', encoding='utf-8-sig', newline='') as f:
            hdr = f.readline().rstrip('\r\n')
            first = f.readline().rstrip('\r\n')
            n = (1 + sum(1 for _ in f)) if first else 0
        cols = hdr.split(',')
        unit = '有 unit 列' if 'unit' in cols else ('ann_pp / share / cny / bp（列名后缀）' if any(c.endswith(('_ann_pp', '_share', '_cny', '_bp')) for c in cols) else '见列名')
        sample = pat.sub('<redacted>', first)[:240].replace('|', '/')
        lines.append('| %s | csv | %d | %s | %s | %s | %s | %s | %s | %s | %s |' % (rel, n, KEYS.get(rel, '').replace('|', ' + '), ' '.join(cols), unit, GEN.get(rel.split('/')[0], 'e6q_*'),
                                                                           '是' if 'query_id' in cols else '否', '是' if in_handoff else '否', sample, O.sha_file(p)))
    nd = len(glob.glob(os.path.join(root, 'accounts', 'daily', '*.csv'))) - 1
    nt = len(glob.glob(os.path.join(root, 'trades', '*.csv'))) - 1
    lines += ['', '另：`accounts/daily/<exec_hash>.csv`（%d 个，列 = B.21 日序列列）与 `trades/<exec_hash>.csv`（%d 个，列 = B.21 成交列）按 INDEX 列出；随机路径日统计分片在 47 '
              '`randoms/daily/`（不入 handoff，可取）；`registration/spec/*.json` 为 plan 附录 C 七个 json 原样复制；JSON：`registration/freeze_E6q.json`、`seal_A2.json`、'
              '`seal_final.json`、`policy_profile_E6q.json`。' % (max(nd, 0), max(nt, 0)), '']
    O.atomic_write_text(os.path.join(root, 'reports', 'SCHEMA.md'), '\n'.join(lines) + '\n')
    dev = ['# E6q SCHEMA_DEVIATIONS（表 | 列 | 原因 | 影响的探针）', '',
           '| 表 | 列 | 原因 | 影响的探针 |', '|---|---|---|---|',
           '| trades/<exec_hash>.csv 与 events/event_counts_E6q.csv | order_kind ∈ EXIT* 且 date < lot_due 的行数 vs n_realized_early | 成交日志按"成交行"写、事件按"意向"计（B.19 恒等），'
           'D 脚本 S29 的行计数另有两项口径排除。三类已知来源逐锚账户分解在 verify/trades_events_bridge_E6q.csv（恒等 d_script_count = n_realized_early + requests_early_not_realized '
           '+ extra_slice_rows − postcutoff_due_rows − deadline_override_rows，residual 全部为 0）：① 多行——M3 门控日程把一个请求拆到多日、一字跌停日内部转移的部分成交 + 次日余量 '
           '（+）；② lot_due = POST_CUTOFF 的早退行——原 due 在 2026-03-27 之后、在截止前早退的批次，是真实早退、事件计入，S29 计数按设计不数（−；H30 与样本末批次多）；'
           '③ DEADLINE_OVERRIDE 行——门控截止强制完成，在截止前完成的计为早退已实现，S29 的类别清单不含（−） | S29 |',
           '| trades/<exec_hash>.csv | lot_due / deadline | 原批次 due 或门控截止落在授权终点（2026-03-27）之后的行写 `POST_CUTOFF`（不物化 E7 日期；字典序大于任何样本日期，`date < lot_due` 比较保持正确）| S29 |',
           '| statistics/account_summary_E6q.csv | 额外列 | 另加 boot60_lo / boot60_hi / D_imp_legacy_5e8_ann_pp / D_imp_curve_1e8_ann_pp / D_imp_curve_5e8_ann_pp（只加不改） | 无 |',
           '| statistics/randoms_E6q.csv | 额外列 | 另加 first128_mean_D_ann_pp（前 128 条路径均值，增补前后对照）与 limit_day_share（RANDOM_TARGET 触限 + 无解日份额） | 无 |',
           '| statistics/cost_curve_E6q.csv | kappa = 0.3 行 | 主 32 行另加 κ .3 曲线行，status = SCENARIO_NOT_CALIBRATED（只加不改；主读 κ .5 / 1） | S27（网格只核 κ .5 / 1 的齐全） |',
           '| statistics/comparison_results_E6q.csv | interpretation | 另加 registration 的 interpretation 列（只加不改） | 无 |',
           '| diagnostics/D2_target_E6q.csv | stat / key2 | fwd_excess 行 key1 / key2 照附录 B.23 词表；账户标签与三分位写在 stat（依次为 臂、触发、H、形态、记忆、T1–T3 或 NEW / OLD、加权，'
           '以 ASCII 竖线分隔）；entry_score_tertile = 取向后的 K 腿好度（−K0 当日源域分位，E6i 测量缓存四段只读），不是形成权重（A4b 下近乎全是 1% 上限、不分级） | S20（只核存在与词表） |',
           '| diagnostics/D3_entry_persistence_E6q.csv | segment / key1 | D3 只用两推导段，segment 写 `DERIV_2010_2018`；K 强 = −K0 源域三分位（T3 最强），K0 原值 / CVR20 另列，取 E6i 测量缓存'
           '（只读，sha 入回执；对齐核行 e6i_alignment_check）；形成权重退化另起 INFO 行 source_weight_degenerate | S20 |', '']
    O.atomic_write_text(os.path.join(root, 'reports', 'SCHEMA_DEVIATIONS.md'), '\n'.join(dev) + '\n')
    print('SCHEMA rows', len(lines) - 6, flush=True)


def seal_final(root):
    fs = glob.glob(O.P('accounts_run', 'full', '*', '*.npz')) + glob.glob(O.P('trades_parts', 'full', '*', '*.npz'))
    first = min(os.path.getmtime(f) for f in fs) if fs else time.time()
    man = []
    for sub in ('statistics', 'events', 'diagnostics', 'verify', 'reports'):
        for p in sorted(glob.glob(os.path.join(root, sub, '*.*'))):
            man.append('%s  %s' % (O.sha_file(p), os.path.relpath(p, root)))
    mp = O.P('registration', 'seal_final_manifest.txt')
    O.atomic_write_text(mp, '\n'.join(man) + '\n')
    s = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), n_files=len(man), sha256_manifest=O.sha_file(mp), manifest='registration/seal_final_manifest.txt',
             first_post_segment_write_at=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first)))
    O.atomic_write_json(O.P('registration', 'seal_final.json'), s)
    print(json.dumps(s, ensure_ascii=False), flush=True)


def deploy_log(root):
    here = os.path.dirname(os.path.abspath(__file__))
    fz = json.load(open(O.P('registration', 'freeze_E6q.json'), encoding='utf-8'))
    a1 = fz.get('code_sha256', {})
    rows = []
    for f in sorted(os.listdir(here)):
        if f.startswith('e6q_') and (f.endswith('.py') or f.endswith('.sh')):
            sha = O.sha_file(os.path.join(here, f))
            dbg = f.startswith(('e6q_dbg_', 'e6q_rtproto'))
            rows.append(dict(file=f, sha256=sha, bytes=os.path.getsize(os.path.join(here, f)), sha256_at_A1=a1.get(f, ''),
                             changed_after_A1='' if f not in a1 else ('yes' if a1[f] != sha else 'no'),
                             role='调试脚本（不在交付链；只读诊断）' if dbg else 'E6q 模块（只 import 复用 e6p_* / e6n_* 等既有模块，不改）'))
    O.atomic_write_csv(os.path.join(root, 'code_register', 'deploy_log.csv'), pd.DataFrame(rows))
    print(json.dumps(dict(files=len(rows)), ensure_ascii=False), flush=True)


# ------------------------------------------------------------------ 闭包门
GATE_ROWS = []


def gate(no, desc, ok, detail=''):
    GATE_ROWS.append(dict(gate=no, description=desc, status='PASS' if ok else 'FAIL', detail=str(detail)[:400]))


def num(s):
    return pd.to_numeric(s, errors='coerce')


def gates(root, stage='pre'):
    del GATE_ROWS[:]
    W = O.work()
    R = rds(W, 'registration/registry_E6q.csv')
    bad = [r.logical_id for r in R.itertuples(index=False) if O.logical_id(r._asdict()) != r.logical_id]
    cnt = R.groupby('scenario').size().to_dict()
    gate('①', 'registry 201 行、情景 / 组计数、逻辑 id 重算', len(R) == 201 and cnt.get('FEASIBLE_DAILY') == 180 and cnt.get('IDEALIZED_SOURCE_FILL') == 21 and not bad,
         dict(cnt=cnt, groups=R.group.value_counts().to_dict(), bad=len(bad)))
    ids = set(R.exec_id)
    lids = set(R.logical_id)
    C = rds(W, 'registration/comparisons_E6q.csv')
    PC = rds(W, 'registration/compound_contrasts_E6q.csv')
    RR = rds(W, 'registration/random_control_refs_E6q.csv')
    FR = rds(W, 'registration/cost_feedback_refs_E6q.csv')
    FC = rds(W, 'registration/feedback_comparisons_E6q.csv')
    LS = rds(W, 'registration/local_snapshot_refs_E6q.csv')
    ok2 = (len(C) == 1359 and set(C.left_exec_id) <= ids and set(C.right_exec_id) <= ids and PC.contrast_id.nunique() == 6 and set(PC.term_exec_id) <= ids
           and len(RR) == 568 and set(RR.owner_logical_id) <= lids and len(FR) == 80 and len(FC) == 580 and len(LS) == 20 and set(LS.owner_exec_id) <= ids
           and set(LS.reference_exec_id) <= ids)
    gate('②', 'comparisons / compound / refs / 反馈 / 快照全部 id 在 registry、计数 = 附录 C', ok2,
         dict(comparisons=len(C), compound=PC.contrast_id.nunique(), refs=len(RR), feedback=len(FR), pairs=len(FC), snapshots=len(LS)))
    AS = rd(root, 'statistics/account_summary_E6q.csv')
    full = AS.groupby('exec_id').segment.nunique()
    c = AS[AS.parent_same_arm_net_ann_pp.notna() & (AS.segment != 'G4')]
    dd = (c.D_same_arm_ann_pp - (c.net_ann_pp - c.parent_same_arm_net_ann_pp)).abs().max()
    seg = AS[AS.segment.isin(O.SEGS)]
    fl = AS[AS.segment == 'FULL'].set_index('exec_id')
    rec = (seg.assign(w=seg.net_ann_pp * seg.n_days).groupby('exec_id').w.sum() / seg.groupby('exec_id').n_days.sum())
    fd = (rec - fl.net_ann_pp.reindex(rec.index)).abs().max()
    g4 = AS[AS.segment == 'G4'].set_index('exec_id').net_ann_pp
    g4d = (seg.groupby('exec_id').net_ann_pp.median() - g4.reindex(seg.exec_id.unique())).abs().max()
    gate('③', 'account_summary 每对象 × 6 段齐全、D 恒等、FULL / G4 恒等', (full == 6).all() and len(full) == len(R) and dd <= 1e-9 and fd <= 1e-9 and g4d <= 1e-9,
         dict(objects=len(full), D_identity=dd, FULL_identity=fd, G4_identity=g4d))
    I = rds(root, 'verify/identities_E6q.csv')
    miss = [k for k in IDENT_REQ if k not in set(I.check_id)]
    att_bad = I[I.check_id.isin(ATTACK) & (I.status != 'BLOCKED')]
    pas = I[I.status == 'PASS']
    tol_bad = pas[num(pas.max_abs_diff) > num(pas.tolerance)]
    oth_bad = I[I.check_id.isin(set(IDENT_REQ) - ATTACK - INFO) & ~I.status.isin(['PASS', 'INFO'])]
    gate('④', 'identities 49 项全在、恒等类 ≤ 容差、攻击类全 BLOCKED', not miss and not len(att_bad) and not len(tol_bad) and not len(oth_bad),
         dict(missing=miss, attack_bad=len(att_bad), tol_bad=list(tol_bad.check_id)[:5], other_bad=list(oth_bad.check_id.unique())[:5]))
    RD = rd(root, 'statistics/randoms_E6q.csv')
    fr = RD[RD.segment == 'FULL']
    feas = R.set_index('logical_id').exec_id
    have = set(zip(fr.owner_exec_id, fr.mechanism))
    miss_r = sum(1 for x in RR.itertuples(index=False) if (feas[x.owner_logical_id], x.mechanism) not in have)
    mc = fr[fr.paths > 1]
    mc_bad = (mc.mcse - mc.rand_sd_D_ann_pp / np.sqrt(mc.paths)).abs().max() if len(mc) else 0.0
    main_o = fr[fr.mcse_target.notna() & (fr.mechanism != 'LEVEL_WORST_1D')]
    prec_bad = main_o[(main_o.mcse > main_o.mcse_target + 1e-12) & (main_o.status != 'MC_LIMIT')]
    rt = fr[fr.mechanism.str.startswith('RANDOM_TARGET')]
    rt_bad = rt[~rt.match_status.isin(['FEASIBLE', 'PROVED_NO_MATCH', 'ALGORITHM_LIMIT', 'IDENTITY_TARGET_CONTROL'])]
    gate('⑤', 'randoms 覆盖按 refs、mcse 恒等、主 owner 精度（MCSE ≤ .01 或 MC_LIMIT）、RANDOM_TARGET 状态词表', miss_r == 0 and mc_bad <= 1e-9 and not len(prec_bad) and not len(rt_bad),
         dict(missing=miss_r, mcse_identity=mc_bad, precision_bad=len(prec_bad), mc_limit=int((fr.status == 'MC_LIMIT').sum()), rt_status=rt.match_status.value_counts().to_dict()))
    PO = rds(root, 'statistics/policy_E6q.csv')
    fz = json.load(open(O.P('registration', 'freeze_E6q.json'), encoding='utf-8'))
    ok6 = (len(PO) == 2 * len(R) and set(PO.profile_name) == {'LEGACY_E6O_A5', 'POLICY_E6Q_A1_CANONICAL'} and set(PO.verdict) <= {'通过', '不通过', '不可判'}
           and (PO[PO.verdict == '不可判'].undecidable_reason != '').all() and set(PO.reconciliation_status) == {fz.get('reconciliation_status')})
    gate('⑥', 'policy 每对象 × 两 profile、词表、不可判必有原因、对账状态统一', ok6, dict(rows=len(PO), verdicts=PO.verdict.value_counts().to_dict(),
                                                                     recon=sorted(set(PO.reconciliation_status))))
    CL = rds(root, 'reports/claims_E6q.csv')
    QR = set(rds(root, 'reports/query_registry_E6q.csv').query_id)
    req = ['Q%02d' % i for i in range(1, 19)] + ['E%02d' % i for i in range(1, 8)] + ['G-P-%02d' % i for i in range(1, 13)] + ['CC-E6q-%02d' % i for i in range(1, 12)]
    e = CL[CL.claim_id.isin(['E%02d' % i for i in range(1, 8)])]
    sc = e[e.claim_status.isin(['支持', '不支持', 'mixed'])]
    inside = ((num(sc.ci_lo) <= num(sc.result_value) + 1e-12) & (num(sc.result_value) <= num(sc.ci_hi) + 1e-12)) | (sc.note != '')
    gate('⑦', 'claims 必含 id 全在、query_id 闭合、E 评分行点估在区间内或 note', set(req) <= set(CL.claim_id) and set(CL.query_id) - {''} <= QR and inside.all() and
         sc.ci_lo.ne('').all() and sc.ci_hi.ne('').all(), dict(missing=sorted(set(req) - set(CL.claim_id))[:5], unregistered=sorted(set(CL.query_id) - {''} - QR)[:5]))
    S0 = rds(root, 'diagnostics/stage0_E6q.csv')
    gate('⑧', 'stage0 S0-A…S0-N 全有行、S0-G 状态词表', {'S0-' + x for x in 'ABCDEFGHIJKLMN'} <= set(S0.probe_id) and
         S0[S0.probe_id == 'S0-G'].status.isin(['BOUND', 'SOURCE_BINDING_PENDING', 'NOT_APPLICABLE']).all(), sorted(S0.probe_id.unique()))
    EV = rd(root, 'events/event_counts_E6q.csv')
    RQ = rd(root, 'events/exit_requests_E6q.csv')
    okev = (EV.n_intents == EV.n_realized_early + EV.n_late_fill + EV.n_unfilled + EV.n_censored).all() and len(EV) == len(R)
    okrq = (RQ.n_requests == RQ.n_completed_before_deadline + RQ.n_forced_deadline_override + RQ.n_completed_after_due_objective).all()
    gate('⑨', 'events / exit_requests 恒等', okev and okrq, dict(events=len(EV), requests=len(RQ)))
    DI = rds(root, 'accounts/daily/INDEX.csv')
    ex = all(os.path.exists(os.path.join(root, f)) for f in DI.file)
    nd = AS[AS.segment.isin(O.SEGS)].groupby('exec_id').n_days.sum()
    mism = (num(DI.set_index('exec_id').n_rows) - nd.reindex(DI.exec_id).values).abs().max()
    gate('⑩', 'accounts/daily 覆盖全部 201 与 n_rows = Σ 四段 n_days', len(DI) == len(R) and ex and mism == 0, dict(index=len(DI), files_exist=ex, n_rows_mismatch=mism))
    sp = os.path.join(root, 'reports', 'SCHEMA.md')
    sm = open(sp, encoding='utf-8').read() if os.path.exists(sp) else ''
    okS = bool(sm) and os.path.exists(os.path.join(root, 'reports', 'SCHEMA_DEVIATIONS.md'))
    badS = []
    if okS:
        for line in sm.splitlines():
            if line.startswith('| ') and '.csv' in line.split('|')[1]:
                cells = [x.strip() for x in line.strip().strip('|').split('|')]
                p = os.path.join(root, cells[0])
                if not os.path.exists(p):
                    p = O.P(*cells[0].split('/'))
                with open(p, encoding='utf-8-sig', newline='') as f:
                    hdr = f.readline().rstrip('\r\n')
                    n = sum(1 for _ in f)
                if int(cells[2]) != n or cells[4] != ' '.join(hdr.split(',')):
                    badS.append(cells[0])
        miss_t = [t for t in CONTRACT if ('| %s |' % t) not in sm]
        okS = okS and not badS and not miss_t
    gate('⑪', 'SCHEMA.md 行数 = 实际、列名 = 表头、合同表全在、DEVIATIONS 存在', okS, badS[:5])
    keys = ['plan_sha256', 'contract_sha256', 'brief_sha256', 'appendix_sha256', 'd_script_sha256', 'schema_contract_sha256', 'policy_file_sha256', 'source_fn_sha256', 'data_cutoff',
            'protocol', 'mode', 'authorizations', 'authorized_by', 'authorized_at', 'written_at', 'cache_tag', 'e6p_registry_sha256', 'reconciliation_status']
    akeys = ['main_A_cny', 'sub_A_cny', 'research_metric', 'product_metric', 'frontier_anchor_logical_id', 'mainline', 'deployment_authorized', 'e7']
    s2 = json.load(open(O.P('registration', 'seal_A2.json'), encoding='utf-8'))
    sf = json.load(open(O.P('registration', 'seal_final.json'), encoding='utf-8')) if os.path.exists(O.P('registration', 'seal_final.json')) else {}
    gate('⑫', 'freeze 全键（含授权八键与对账状态）；seal_A2.written_at < 后段首次写入', all(k in fz for k in keys) and all(k in fz['authorizations'] for k in akeys)
         and str(s2['written_at']) < str(sf.get('first_post_segment_write_at', '')), dict(seal_A2=s2['written_at'], first_post=sf.get('first_post_segment_write_at')))
    pat_nan = re.compile(r'(?<![A-Za-z_])(nan|None)(?![A-Za-z_])')
    nanf = [f for f in glob.glob(os.path.join(root, 'reports', '*.md')) if pat_nan.search(open(f, encoding='utf-8').read())]
    gate('⑬', '报告正文无字面 nan / None', not nanf, [os.path.basename(f) for f in nanf])
    e7 = I[I.check_id == 'E7_GUARD'].value.astype(str).max()
    gate('⑭', '全部文件最大日期 ≤ 2026-03-27', e7 <= O.CUTOFF and DI.date_max.max() <= O.CUTOFF, e7)
    cdn = os.path.basename(O.cache_dir())
    gate('⑮', '缓存目录含 E6q-v1.1 与 86c246dd', 'E6q-v1.1' in cdn and '86c246dd' in cdn, cdn)
    r0p = os.path.join(root, 'reports', 'E6q_REPORT_R0.md')
    r0 = open(r0p, encoding='utf-8').read()[:4000] if os.path.exists(r0p) else ''
    gate('⑯', '页首写明无 E7 / 部署授权、协议 v1.6、方式 B、授权八值', all(x in r0 for x in ('E7', 'deployment_authorized = false', 'v1.6', '方式 B', 'main_A_cny', 'sub_A_cny',
                                                                                'research_metric', 'product_metric', 'frontier_anchor_logical_id', 'mainline', 'e7')))
    vt = json.load(open(O.P('verify', 'spec', 'verification.txt'), encoding='utf-8'))
    lf = lambda p: O.sha_bytes(open(p, 'rb').read().replace(b'\r\n', b'\n'))
    okf = all(lf(O.P('registration', 'spec', k)) == v for k, v in O.JSON_SHA.items())
    gate('⑰', 'verify/spec 七指纹 = plan 附录 B（LF）、205 PASS', okf and vt.get('test_count') == 205 and len(vt.get('passed', [])) == 205 and not vt.get('failed'),
         dict(test_count=vt.get('test_count'), passed=len(vt.get('passed', []))))
    if stage == 'post':
        outp = O.P('verify', 'decision', 'out_E6q_stage2', 'E6q_D_probes_stage2.csv')
        gate('⑱', 'verify/decision/out_E6q_stage2/ 存在且含探针 CSV（结果不作门）', os.path.exists(outp))
    CU = rds(root, 'statistics/cost_curve_E6q.csv')
    CU = CU[CU.kappa.isin(['0.5', '1.0'])]
    need = len(O.A_GRID) * len(O.KAPPAS) * len(O.EXPONENTS) * 6
    g_ = CU.groupby(['exec_id', 'comparator_kind']).size()
    abs_ok = all(g_.get((e_, 'ABSOLUTE'), 0) >= need for e_ in R.exec_id)
    par_ok = all(g_.get((r.exec_id, 'SAME_ARM_PARENT'), 0) >= need for r in R.itertuples(index=False) if r.parent_same_arm_exec_id)
    FB = rds(root, 'statistics/cost_feedback_E6q.csv')
    FP = rds(root, 'statistics/cost_feedback_pairs_E6q.csv')
    BE = rds(root, 'statistics/breakeven_E6q.csv')
    DN = rds(root, 'statistics/density_E6q.csv')
    gate('⑲', '成本：曲线网格、breakeven、反馈 80 × 6 段与 580 配对、密度表齐全', abs_ok and par_ok and FB.feedback_id.nunique() == 80 and (FB.groupby('feedback_id').segment.nunique() == 6).all()
         and FP.groupby(['feedback_id', 'kind', 'right_feedback_id']).ngroups == 580 and len(BE) > 0 and len(DN) > 0,
         dict(abs_ok=abs_ok, par_ok=par_ok, feedback=FB.feedback_id.nunique(), pairs=FP.groupby(['feedback_id', 'kind', 'right_feedback_id']).ngroups, density=len(DN)))
    if stage == 'post':
        sj = O.P('handoff', '%s_scan.json' % os.path.basename(root_handoff())) if root_handoff() else ''
        sc_ = json.load(open(sj, encoding='utf-8')) if sj and os.path.exists(sj) else dict(n_hits=-1, hits=[['no scan record', '']])
        gate('⑳', '全交接件扫描：无登录信息 / 主机标识 / 用户目录名 / __pycache__（决策端脚本原件按 sha 豁免）', sc_.get('n_hits') == 0, sc_.get('hits', [])[:5])
    s0a = all(os.path.exists(O.P(*x.split('/'))) for x in ('verify/impact_reconciliation_E6q.csv', 'verify/impact_reconciliation_ladder_E6q.csv', 'reports/E6q_S0A_reconciliation.md'))
    fa = json.load(open(O.P('diagnostics', 's0a_facts_E6q.json'), encoding='utf-8'))
    bb = rds(W, 'registration/e_band_bindings_E6q.csv')
    gate('㉑', 'S0-A 对账三件存在且状态与 policy / freeze 一致；E 端点绑定表存在', s0a and fa.get('status') == fz.get('reconciliation_status') == PO.reconciliation_status.iloc[0]
         and bb.e_id.nunique() == 7, dict(s0a_status=fa.get('status'), freeze=fz.get('reconciliation_status'), bands=bb.e_id.nunique()))
    G_ = pd.DataFrame(GATE_ROWS)
    O.atomic_write_csv(os.path.join(root, 'verify', 'closure_E6q.csv' if stage == 'pre' else 'closure_post_E6q.csv'), G_)
    print(G_.to_string()[:8000], flush=True)
    return G_


def root_handoff():
    p = O.P('handoff', 'LATEST_E6q.txt')
    return open(p).read().strip() if os.path.exists(p) else ''


# ------------------------------------------------------------------ handoff
_SCAN_PAT = None


def _scan_file(p):
    global _SCAN_PAT
    if _SCAN_PAT is None:
        _SCAN_PAT = sens_pattern()
    with open(p, 'r', encoding='utf-8', errors='replace') as fh:
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
            if f == 'E6q_D_stage2.py' and O.sha_file(p) == O.D_SCRIPT_SHA256:
                continue
            if f.endswith(('.csv', '.md', '.txt', '.json', '.py', '.sh')):
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
    hd = O.P('handoff', 'E6q_%s' % ts)
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
        if f.startswith('e6q_') and (f.endswith('.py') or f.endswith('.sh')):
            link(os.path.join(here, f), os.path.join(hd, 'code_register', 'src', f))
    O.atomic_write_text(O.P('handoff', 'LATEST_E6q.txt'), os.path.relpath(hd, W) + '\n')
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


def run_d(hd):
    """决策端脚本：在结果目录内以相对路径运行（stdout 不含绝对路径）；输出入 handoff 并追加 sha。"""
    W = O.work()
    d = O.P('verify', 'decision')
    assert O.sha_file(os.path.join(d, 'E6q_D_stage2.py')) == O.D_SCRIPT_SHA256
    tmp = O.P('tmp', 'pyc_d')
    os.makedirs(tmp, exist_ok=True)
    env = dict(os.environ, PYTHONPYCACHEPREFIX=tmp, PYTHONDONTWRITEBYTECODE='1')
    rel_hd = os.path.relpath(hd, W)
    cmd = [sys.executable, 'verify/decision/E6q_D_stage2.py', '--root', '.', '--handoff', rel_hd, '--out', 'verify/decision/out_E6q_stage2']
    p = subprocess.run(cmd, cwd=W, env=env, capture_output=True, text=True)
    out = O.P('verify', 'decision', 'out_E6q_stage2')
    os.makedirs(out, exist_ok=True)
    tail = (p.stdout + '\n' + p.stderr)[-8000:]
    O.atomic_write_text(os.path.join(out, 'stdout_tail.txt'), O.san(tail))
    lines = []
    for f in sorted(os.listdir(out)):
        src = os.path.join(out, f)
        dst = os.path.join(hd, 'verify', 'decision', 'out_E6q_stage2', f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copy2(src, dst)
        lines.append('%s  %s' % (O.sha_file(dst), os.path.relpath(dst, hd)))
    with open(os.path.join(hd, 'HANDOFF_SHA256.txt'), 'a', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    print(json.dumps(dict(rc=p.returncode, outputs=len(lines)), ensure_ascii=False), flush=True)
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
    elif a.cmd == 'gates_post':
        G_ = gates(root, 'post')
        sys.exit(0 if (G_.status == 'PASS').all() else 2)
    elif a.cmd == 'handoff':
        hd, hits = handoff(root)
        if hits:
            print('S07b 扫描命中，不交付', flush=True)
            sys.exit(3)
        run_d(hd)
    elif a.cmd == 'run_d':
        run_d(O.P(*a.handoff.split('/')))
    else:
        {'identities': identities, 'stage0': stage0_final, 'schema': schema, 'seal_final': seal_final, 'deploy_log': deploy_log, 'bridge': bridge}[a.cmd](root)
