# -*- coding: utf-8 -*-
"""E6n 交付（brief §5 S8、§9、A7 / A9；附录 F / G）。
  schema   reports/SCHEMA.md：每张交付 CSV / JSON / npz（文件、类型、行数或键数、键列、列名全列、单位说明、生成脚本、query_id 列）——按文件实测
  register reports/E6n_code_change_register.md：deploy_log 逐行（文件、动作、sha、行数、时间）+ 每个 e6n 模块的来源 / 语义改动说明
  replica  replica/：P0_REVIEW（plan / brief / 授权 / 源合同 / 注册与比较清单 / policy 与 query / 主 72 + 父 + 关键对照逐日 / B1-0 / 随机汇总与种子 /
           回执 / 限制 / SCHEMA）、P1_LEDGER（账户 npz）、P2_RANDOM（随机 npz 汇总表 + 种子 / 路径键说明）、P3_DATA_REF（分钟分区清单 + 数据指纹 + 外部输入）；
           复制后逐文件 sha 复核
  copy     handoff/E6n_<ts>/：reports + registry + registration + results/full 摘要表 + SCHEMA.md + HANDOFF_SHA256.txt
collect_files() 供闭包门扫描（交付集）。"""
import os
import re
import sys
import glob
import json
import time
import shutil
import argparse

import numpy as np
import pandas as pd

import e6n_core as N

DELIVER_DIRS = ('reports', 'registry', 'registration', 'results/full', 'results/deriv', 'results/b1_0', 'stage0', 'replica')
SKIP_EXT = ('.npz', '.npy', '.pkl', '.parquet')
SCRIPT_OF = [('penalty_change', 'e6n_fixed.py'), ('measurement_raw_ledger', 'e6n_fixed.py'), ('card_query_map', 'e6n_fixed.py'), ('park_reentry', 'e6n_fixed.py'),
             ('externality_register', 'e6n_fixed.py'), ('authorization_receipt', 'e6n_fixed.py'), ('_final.csv', 'e6n_fixed.py'),
             ('registration/policy_profiles', 'e6n_stage_b.py'), ('results/b1_0/', 'e6n_b1_0.py'), ('results/full/b2/', 'e6n_b2_run.py'), ('results/deriv/b2/', 'e6n_b2_run.py'), ('/b3/', 'e6n_b3.py'), ('/b4/', 'e6n_b4.py'),
             ('/b5/', 'e6n_b56.py'), ('/b6/', 'e6n_b56.py'), ('/decomp/', 'e6n_decomp.py'), ('/bootstrap/', 'e6n_bootstrap.py'), ('policy_', 'e6n_policy.py'),
             ('frontier_', 'e6n_policy.py'), ('improvement_', 'e6n_policy.py'), ('primary72_', 'e6n_policy.py'), ('descriptor_stats', 'e6n_stats.py'),
             ('comparison_', 'e6n_stats.py'), ('random_refs', 'e6n_stats.py'), ('mc_plan', 'e6n_stats.py'), ('registry/random_manifest', 'e6n_rand.py'),
             ('registry/b1_0_manifest', 'e6n_b1_0.py'), ('registry/query_registry', 'e6n_stage_b.py'), ('registry/b2_manifest', 'e6n_stage_b.py'),
             ('registry/b3_manifest', 'e6n_stage_b.py'), ('registry/external_inputs', 'e6n_s0_rest.py'), ('registry/import_closure', 'e6n_s0_rest.py'),
             ('registry/e_random_contract', 'e6n_s0_rest.py'), ('registry/', 'e6n_a0.py'), ('registration/probe_ledger', 'e6n_b1_0.py'), ('registration/seal_B1_0', 'e6n_b1_0.py'),
             ('registration/seal_', 'e6n_seal.py'), ('registration/a1_auto', 'e6n_stage_b.py'), ('registration/record_B', 'e6n_stage_b.py'),
             ('registration/stageB_freeze', 'e6n_stage_b.py'), ('registration/mask_facts', 'e6n_stage_a.py'), ('registration/stage_a', 'e6n_stage_a.py'),
             ('registration/a0_counts', 'e6n_a0.py'), ('registration/', 'e6n_stage_b.py'), ('stage0/c7_minute/', 'e6n_s0_c7.py'), ('stage0/plan_tests/', 'e6n_spec_tests.py（plan 附录 B）'),
             ('stage0/c2_mask', 'e6n_s0_mask_anchor.py'), ('stage0/c2_anchor', 'e6n_s0_anchor_acct.py'), ('stage0/c5_random', 'e6n_rand.py selftest'),
             ('stage0/', 'e6n_s0_rest.py'), ('results/coverage_by', 'e6n_stage_a.py'), ('reports/queries_', 'e6n_queries.py'), ('reports/', 'e6n_reports.py')]
UNIT_RULE = 'ann_pp = 252 × 100 × 日均；bp = 持有期累计基点；bp_per_h = bp / H；decimal = 小数；pct_pt = 百分点；count = 计数；log_return = 对数收益'


def collect_files():
    out = []
    for d in DELIVER_DIRS:
        for f in glob.glob(N.P(d, '**', '*'), recursive=True):
            if os.path.isfile(f) and not f.endswith(SKIP_EXT) and '/tmp/' not in f and os.path.getsize(f) < 300e6:
                out.append(f)
    return sorted(set(out))


def script_of(rel):
    for k, v in SCRIPT_OF:
        if k in rel:
            return v
    return 'e6n_*（见 code_change_register）'


def schema():
    rows = []
    files = [f for f in collect_files() if f.endswith(('.csv', '.json')) and '/replica/' not in f]
    files += sorted(glob.glob(N.P('accounts', '*', '*.npz')))[:4] + sorted(glob.glob(N.P('randoms', '*', '*', '*.npz')))[:3] + sorted(glob.glob(N.P('accounts_support', '*', '*.npz')))[:2]
    L = ['# E6n SCHEMA.md（交付时按文件实测生成；闭包门 N05 核"行数 = 文件实际行数"）', '', '单位：' + UNIT_RULE, '',
         '| 文件（相对结果目录） | 类型 | 行数或键数 | 键列 | 列名全列（npz 为键名） | 单位列说明 | 生成脚本 | query_id 列 |', '|---|---|---|---|---|---|---|---|']
    for f in files:
        rel = N.rel(f)
        if f.endswith('.csv'):
            try:
                df = pd.read_csv(f, nrows=0)
                n = sum(1 for _ in open(f, encoding='utf-8')) - 1
            except Exception:                                                    # noqa: BLE001
                continue
            cols = list(df.columns)
            key = next((c for c in ('desc_id', 'comparison_id', 'query_id', 'comp_id', 'aux_id', 'obj', 'member', 'item', 'id') if c in cols), cols[0] if cols else '')
            units = ', '.join(c for c in cols if re.search(r'_(ann_pp|bp|bp_per_h|decimal|pct_pt|count)$', c))[:300]
            L.append('| `%s` | csv | %d | %s | %s | %s | %s | %s |' % (rel, n, key, ', '.join(cols)[:1500].replace('|', '¦'), units or '见列名后缀', script_of(rel),
                                                                     '有' if 'query_id' in cols else '无'))
        elif f.endswith('.json'):
            try:
                j = json.load(open(f, encoding='utf-8'))
            except Exception:                                                    # noqa: BLE001
                continue
            keys = list(j.keys()) if isinstance(j, dict) else ['(list %d)' % len(j)]
            L.append('| `%s` | json | %d | — | %s | — | %s | 无 |' % (rel, len(keys), ', '.join(keys)[:800].replace('|', '¦'), script_of(rel)))
        else:
            with np.load(f, allow_pickle=False) as z:
                keys = list(z.files)
                n = len(z[keys[0]]) if keys else 0
            L.append('| `%s`（同目录同构文件同 schema） | npz | %d | desc / desc_H | %s | d_* 为逐日（小数日收益 / 权重） | %s | 无 |' % (
                rel, n, ', '.join(keys)[:800], script_of(rel) if 'accounts' not in rel else ('e6n_accounts.py' if 'support' not in rel else 'e6n_support.py')))
    n_rows = len(L) - 6
    L += ['', '## plan §12.4 / brief §5 S8 必交产物 → 文件（按文件实测；"缺" = 未生成）', '', '| 必交项 | 文件（相对结果目录） | 状态 |', '|---|---|---|']
    for item, fs in REQUIRED_MAP:
        st = []
        for f in fs:
            p_ = N.P(f)
            if not os.path.exists(p_):
                st.append('缺')
            elif f.endswith('.csv'):
                st.append('%d 行' % (sum(1 for _ in open(p_, encoding='utf-8')) - 1))
            else:
                st.append('在')
        L.append('| %s | %s | %s |' % (item, '<br>'.join('`%s`' % f for f in fs), ' / '.join(st)))
    p = N.P('reports', 'SCHEMA.md')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    N.atomic_write_text(p, '\n'.join(L) + '\n')
    return p, n_rows


REQUIRED_MAP = [
    ('source_manifest', ['registry/external_inputs_E6n.csv', 'registry/import_closure_E6n.csv']),
    ('data_contract', ['stage0/data_contract.json', 'stage0/data_request_E6n.md']),
    ('coverage_by_feature_year_exchange', ['results/coverage_by_feature_year_exchange.csv']),
    ('minute_health', ['stage0/c7_minute/minute_health.csv']),
    ('source_claim_reconciliation', ['registration/source_claim_reconciliation.csv']),
    ('idea_ledger_G（冻结件 / 结果版）', ['registration/idea_ledger_G.csv', 'results/full/idea_ledger_G_final.csv']),
    ('probe_ledger', ['registration/probe_ledger.csv']),
    ('execution_ledger_E（冻结件 / 结果版）', ['registration/execution_ledger_E.csv', 'results/full/execution_ledger_E_final.csv']),
    ('exposure_ledger（冻结件 / 结果版）', ['registration/exposure_ledger.csv', 'results/full/exposure_ledger_final.csv']),
    ('registry', ['registry/descriptors_E6n.csv', 'registry/auxiliary_E6n.csv', 'registry/component_controls_E6n.csv']),
    ('comparison_manifest', ['registry/comparison_manifest_E6n.csv']),
    ('random_manifest（含路径键 / 种子合同）', ['registry/random_manifest_E6n.csv', 'registry/e_random_contract_E6n.json']),
    ('policy_profile_copy', ['registration/policy_profiles_E6n.json']),
    ('authorization_receipt', ['registration/authorization_receipt_E6n.json', 'registration/record_B_preauthorized_E6n.json',
                               'registration/record_B_conditions_receipt_E6n.json']),
    ('card_query_map', ['registration/card_query_map_E6n.csv']),
    ('park_reentry', ['registration/park_reentry_E6n.csv']),
    ('externality_register', ['registration/externality_register_E6n.csv']),
    ('code_change_register', ['reports/E6n_code_change_register.md']),
    ('runbook（脚本在仓库：e6n_runbook.sh / e6n_chain.sh / e6n_pipeline.sh）', ['reports/E6n_REVIEW_input_notes.md']),
    ('limits', ['reports/E6n_limit_register.md']),
    ('closure', ['closure_E6n.json', 'closure_E6n.csv']),
    ('数据指纹 / 重放', ['results/full/measurement_raw_ledger.csv', 'replica/replica_manifest_P3_DATA_REF.json']),
    ('measurement_raw_ledger', ['results/full/measurement_raw_ledger.csv']),
    ('penalty_change_ledger（四项变化 + 边界间距）', ['results/full/penalty_change_ledger.csv']),
    ('b1_0_cells / pairs / matched / moderators / bridges', ['results/b1_0/b1_0_cells.csv', 'results/b1_0/b1_0_pairs.csv', 'results/b1_0/b1_0_matched.csv',
                                                            'results/b1_0/b1_0_moderators.csv', 'results/b1_0/b1_0_bridges.csv']),
    ('component_dose_ledger', ['results/full/component_dose_ledger.csv']),
    ('support_four_accounts', ['results/full/support_four_accounts.csv']),
    ('match_cap_holdings_min', ['results/full/match_cap_holdings_min.csv']),
    ('b2_risk_set / order_overlay / mirrors / controls', ['results/full/b2/b2_risk_set.csv', 'results/full/b2/b2_order_overlay.csv', 'results/full/b2/b2_mirrors.csv',
                                                         'results/full/b2/b2_controls.csv']),
    ('b3_same_count', ['results/full/b3/b3_same_count.csv']),
    ('b4_bridges', ['results/full/b4/b4_bridges.csv']),
    ('b5_dedupe', ['results/full/b5/b5_dedupe.csv']),
    ('b6_event_contrib', ['results/full/b6/b6_event_contrib.csv'])]


def register():
    lg = pd.read_csv(N.P('code_register', 'deploy_log.csv'), keep_default_na=False)
    desc = {
        'e6n_core.py': '工程常量 / 路径 / 回执 / 原子写（沿 e6m_core，只 import 不改）', 'e6n_minute.py': '分钟读取器（读取接口截断 ≤ 2026-03-27；起点 = 竞价价或 1 分钟第一笔成交）',
        'e6n_etl.py': '分钟 ETL（按日分区缓存 + 分区清单 sha）', 'e6n_meas.py': '测量层（全日历 + 段单元；源 Q 逐位；五面 / 两构造 / 控制 / 桥 / 481 源桥）',
        'e6n_a0.py': 'A0 登记编译（以 plan 附录 B 参考编译器为坐标真值重编）', 'e6n_vars.py': '测量输入变体（生成语法 / CLONE / DOSE / CDOSE）',
        'e6n_masks.py': '名单层（源 Struct 门 / 源 mem_gate / 源下游）', 'e6n_accounts.py': '确定性账户（e6k_acct 同式）', 'e6n_gate.py': '后段守卫 / 推导段守卫 / 授权文件',
        'e6n_rand.py': '随机层（新增内容置换 → 源中性化排名逐位 → e6l_fast 门 / 记忆 / 下游 / 账本；LEGACY / R_MEMORY；任务认领）',
        'e6n_b1_0.py': 'B1-0 第一道（四域 × 成员 × 三分 / 匹配 / 调节 / 桥 / A2 标签 / 封存）', 'e6n_b2.py': 'B2 触发面板 / 风险集时钟', 'e6n_b2_run.py': 'B2 账本诊断',
        'e6n_b3.py': 'B3 同数对照', 'e6n_b4.py': 'B4 全 A 域桥', 'e6n_b56.py': 'B5 去重 / LEAK 复现 / E7 页；B6 窗口贡献 / 年度状态', 'e6n_support.py': '四账户支持桥（S_T 上重跑）',
        'e6n_decomp.py': '四账户 / 合用 / 支持闭合 / COMPONENT_DOSE / MATCH_CAP_HOLDINGS_MIN', 'e6n_stats.py': '描述符 / 比较 / 随机统计（e6m_s_stats 同式）',
        'e6n_policy.py': '政策（e6l_policy 判定函数）/ 可用期 / 实质改善 / 前沿', 'e6n_bootstrap.py': 'bootstrap（e6m_s_bootstrap 同式）', 'e6n_seal.py': '封存',
        'e6n_stage_a.py': 'Stage A 掩码层事实', 'e6n_stage_b.py': 'Stage B / A1-auto / 冻结 / 记录 B / 条件回执', 'e6n_queries.py': 'query 表生成（缺列 / 0 行报错）',
        'e6n_reports.py': '七份 REPORT（机器表生成；E02 扫描）', 'e6n_closure.py': '闭包门', 'e6n_deliver.py': 'SCHEMA / 代码登记 / 副本包 / 交接',
        'e6n_s0_c7.py': 'Stage 0 第 7 类（分钟数据合同实测）', 'e6n_s0_mask_anchor.py': 'Stage 0 名单层锚', 'e6n_s0_anchor_acct.py': 'Stage 0 账户层锚',
        'e6n_s0_rest.py': 'Stage 0 其余各类 + 收尾', 'e6n_runbook.sh': '运行手册',
        'e6n_chain.sh': '推导段收尾链（等随机 → 统计 → MC 增补 → seal deriv → 条件回执 → part1）',
        'e6n_pipeline.sh': '自动接力（后段启动 / 均衡 / 收尾 / 交付前全套；每步失败即停）',
        'e6n_fixed.py': '补齐必交表（penalty_change / measurement_raw / card_query_map / park_reentry / externality / authorization_receipt / 账本结果版）',
        'e6n_notes.py': '执行端交付说明（REVIEW_input_notes；数字取机器表）'}
    L = ['# E6n 代码变更登记（code_register/deploy_log.csv 逐行；新代码全部 e6n_ 前缀；四地基与 e6e–e6m 只读未改）', '',
         '说明：随机推导段（2010-2014 / 2015-2018 首 1,024 路径）由 e6n_rand.py 版本 d64c295d 执行（进程启动时载入）；其回执 code 字段在写回执时取文件当前 sha'
         '（3900360a 之后版本只新增任务认领逻辑，计算路径逐行相同）。', '', '| 时间 | 文件 | 动作 | 新 sha16 | 旧 sha16 | 字节 | 行 | 模块说明 |', '|---|---|---|---|---|---|---|---|']
    for r in lg.itertuples():
        L.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (r.time, r.file, r.action, str(r.new_sha256)[:16], str(r.old_sha256)[:16], r.bytes, r.lines,
                                                            desc.get(r.file, '—')))
    p = N.P('reports', 'E6n_code_change_register.md')
    N.atomic_write_text(p, '\n'.join(L) + '\n')
    return p


def replica():
    od = N.P('replica')
    os.makedirs(od, exist_ok=True)
    sets = {
        'P0_REVIEW': [N.P('PLAN_COPY.md')] + glob.glob(N.P('handoff_in', '**', '*'), recursive=True) + glob.glob(N.P('registry', '*')) + glob.glob(N.P('registration', '*'))
        + glob.glob(N.P('reports', '**', '*'), recursive=True) + glob.glob(N.P('results', 'b1_0', '*')) + glob.glob(N.P('results', 'full', '*.csv'))
        + glob.glob(N.P('task_status', '*')),
        'P1_LEDGER': glob.glob(N.P('accounts', '*', '*.npz')) + glob.glob(N.P('accounts_support', '*', '*')),
        'P2_RANDOM': glob.glob(N.P('results', '*', 'random_refs*.csv')) + glob.glob(N.P('results', '*', 'mc_plan_*.csv')) + [N.P('registry', 'random_manifest_E6n.csv'),
                                                                                                                     N.P('registry', 'e_random_contract_E6n.json')],
        'P3_DATA_REF': [N.P('registry', 'external_inputs_E6n.csv'), N.P('stage0', 'data_contract.json'), N.P('stage0', 'data_request_E6n.md')]
        + glob.glob(N.P('minute_panel', 'cache_*', 'partition_manifest.csv')) + glob.glob(N.P('minute_panel', 'cache_*', 'panel_manifest.json'))
        + glob.glob(N.P('minute_panel', 'cache_*', 'namespace.json'))}
    outs = []
    for nm, fs in sets.items():
        fs = sorted(set(f for f in fs if os.path.isfile(f)))
        dest = os.path.join(od, nm)
        rows, bad = [], []
        for f in fs:
            rel = N.rel(f)
            tgt = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(tgt), exist_ok=True)
            if not os.path.exists(tgt) or N.sha_file(tgt) != N.sha_file(f):
                shutil.copy2(f, tgt)
            s1, s2 = N.sha_file(f), N.sha_file(tgt)
            rows.append(dict(path=rel, sha256=s1, bytes=os.path.getsize(f)))
            if s1 != s2:
                bad.append(rel)
        man = dict(tier=nm, created_at=time.strftime('%Y-%m-%d %H:%M:%S'), machine=N.MACHINE, file_count=len(rows), total_bytes=int(sum(r['bytes'] for r in rows)),
                   files=rows, verified=dict(mismatched=bad, checked=len(rows)))
        p = os.path.join(od, 'replica_manifest_%s.json' % nm)
        N.atomic_write_json(p, man)
        outs.append(p)
    return outs


def copy(ts):
    hd = N.P('handoff', 'E6n_%s' % ts)
    os.makedirs(hd, exist_ok=True)
    picks = (glob.glob(N.P('reports', '*.md')) + glob.glob(N.P('reports', 'queries_full', '*.csv')) + glob.glob(N.P('registry', '*')) + glob.glob(N.P('registration', '*'))
             + glob.glob(N.P('results', 'full', '*.csv')) + glob.glob(N.P('results', 'full', '*', '*.csv')) + glob.glob(N.P('results', 'b1_0', '*'))
             + glob.glob(N.P('results', 'deriv', '*', '*.csv')) + glob.glob(N.P('results', 'checks', '*.csv')) + [N.P('stage0', 'data_contract.json'),
                                                                                                                 N.P('stage0', 'data_request_E6n.md'), N.P('closure_E6n.json'), N.P('closure_E6n.csv')]
             + glob.glob(N.P('replica', 'replica_manifest_*.json')) + glob.glob(N.P('stage0', 'c7_minute', '*.csv')) + glob.glob(N.P('stage0', 'checks', '*.csv')))
    lines = []
    for f in sorted(set(x for x in picks if os.path.isfile(x) and os.path.getsize(x) < 200e6)):
        rel = N.rel(f)
        tgt = os.path.join(hd, rel)
        os.makedirs(os.path.dirname(tgt), exist_ok=True)
        shutil.copy2(f, tgt)
        lines.append('%s  %s' % (N.sha_file(tgt), rel))
    N.atomic_write_text(os.path.join(hd, 'HANDOFF_SHA256.txt'), '\n'.join(lines) + '\n')
    return hd, len(lines)


CONSOLIDATE = [('decomp/four_account_ledger_%s.csv', 'four_account_ledger.csv'), ('decomp/support_four_accounts_%s.csv', 'support_four_accounts.csv'),
               ('decomp/component_dose_ledger_%s.csv', 'component_dose_ledger.csv'), ('decomp/match_cap_holdings_min_%s.csv', 'match_cap_holdings_min.csv'),
               ('b2/b2_risk_set_%s*.csv', 'b2/b2_risk_set.csv'), ('b2/b2_order_overlay_%s*.csv', 'b2/b2_order_overlay.csv'), ('b2/b2_mirrors_%s*.csv', 'b2/b2_mirrors.csv'),
               ('b2/b2_controls_%s*.csv', 'b2/b2_controls.csv'), ('b3/b3_same_count_%s.csv', 'b3/b3_same_count.csv'), ('b3/b3_same_count_split_%s.csv', 'b3/b3_same_count_split.csv'),
               ('b4/b4_bridges_%s.csv', 'b4/b4_bridges.csv'), ('b4/b4_matched_non_i11_%s.csv', 'b4/b4_matched_non_i11.csv')]


def consolidate():
    """逐段表（推导段 results/deriv/…、后段 results/full/…）→ results/full/<名>.csv（四段合表；segment 列）。"""
    outs = []
    for pat, dst in CONSOLIDATE:
        parts = []
        for s in N.SEGMENTS:
            ph = 'deriv' if s in N.DERIV_SEGS else 'full'
            for f in sorted(glob.glob(N.P('results', ph, pat % s))):
                x = pd.read_csv(f, keep_default_na=False, low_memory=False)
                if 'segment' not in x.columns:
                    x['segment'] = s
                parts.append(x)
        if not parts:
            continue
        D = pd.concat(parts, ignore_index=True)
        # 真实计算状态（plan §12.3）：B2 逐段原表把 0 事件配置也记 COMPUTED（值为空）→ 合表时改标 NOT_COMPUTABLE（逐段原表不动）
        nev = next((c for c in ('n_events', 'n_events_real') if c in D.columns), None)
        if dst.startswith('b2/') and nev and 'status' in D.columns:
            z = (pd.to_numeric(D[nev], errors='coerce') == 0) & (D.status.astype(str) == 'COMPUTED')
            D.loc[z, 'status'] = 'NOT_COMPUTABLE（0 事件）'
        p = N.P('results', 'full', dst)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        N.atomic_write_csv(p, D)
        outs.append(p)
    return outs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['schema', 'register', 'replica', 'copy', 'consolidate'])
    ap.add_argument('--ts', default=time.strftime('%Y%m%d_%H%M'))
    a = ap.parse_args()
    if a.step == 'schema':
        p, n = schema()
        N.write_receipt('E6n_deliver_schema', [p], code=[__file__], rows=n)
        print(json.dumps(dict(schema=N.rel(p), rows=n), ensure_ascii=False))
    elif a.step == 'register':
        p = register()
        N.write_receipt('E6n_deliver_register', [p], code=[__file__])
        print(N.rel(p))
    elif a.step == 'consolidate':
        outs = consolidate()
        N.write_receipt('E6n_deliver_consolidate', outs, code=[__file__])
        print(json.dumps([N.rel(p) for p in outs], ensure_ascii=False))
    elif a.step == 'replica':
        outs = replica()
        N.write_receipt('E6n_deliver_replica', outs, code=[__file__])
        print(json.dumps([N.rel(p) for p in outs], ensure_ascii=False))
    else:
        hd, n = copy(a.ts)
        N.write_receipt('E6n_deliver_copy', [os.path.join(hd, 'HANDOFF_SHA256.txt')], code=[__file__], files=n)
        print(json.dumps(dict(handoff=N.rel(hd), files=n), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
