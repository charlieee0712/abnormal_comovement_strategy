# -*- coding: utf-8 -*-
"""E6j Stage 0 收口（brief v1.2 §2 第 6 项；plan §10.1）：生成 source_manifest.json、anchor_results.csv、feature_contracts.csv、
permission_ledger.json；汇总 Stage 0 六项锚的 PASS 状态（A1-auto 第 6 项与记录 B 生效条件 ① 的机器依据）。不读任何收益。"""
import e6j_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import subprocess

import pandas as pd

import e6j_core as J

RES = J.RES
DOCS = ['brief_copy.md', 'PLAN_COPY.md', 'E6j_proposal_copy.md', 'E6i_RULING_copy.md', 'E6j_RULING_copy.md', 'E6i_REVIEW_copy.md',
        'E6i_REVIEW_supplement_1_copy.md', 'E6i_REVIEW_supplement_2_copy.md', 'REVIEW_protocol_copy.md', '00_协议_copy.md',
        'source_resolution.md', 'engine_contract.md']
CODE_FILES = ['data_loader.py', 'features_daily.py', 'event_study.py', 'pool_screening_v2.py', 'comprehensive_factor_diagnosis.py',
              'export_delivery_pools_v2.py', 'e6e_core.py', 'e6f_core.py', 'e6g_core.py', 'e6g_desc.py', 'e6h_core.py', 'e6h_rules.py',
              'e6h_run_routes.py', 'e6i_core.py', 'e6i_ops.py', 'e6i_engine.py', 'e6i_features.py', 'e6i_s1base.py', 'e6i_randoms.py',
              'e6i_stage2.py']
RECEIPTS = {  # Stage 0 六项 → 回执（FAILED 须有同名 _rerun 成功覆盖）
    '1_prod_path_anchor': ['stage0_anchor1_prod_path_rerun'],
    '2_parent_identity': ['stage0_anchor2_parent_identity', 'stage0_anchor2_parent_identity_rerun'],
    '3_slot_identity': ['stage0_anchor3_slot_identity'],
    '4_features_synthetic_real': ['stage0_item4_features'],
    '5_seed_replay_guard_a0': ['stage0_item5_replay', 'stage0_item5_guard'],
}


def receipt(tid):
    p = os.path.join(RES, 'task_status', '%s.receipt.json' % tid)
    return json.load(open(p)) if os.path.exists(p) else None


def anchor_results():
    parts = []

    def add(item, path, idcol, objcol, metcol, statcol='status', seg=None):
        df = pd.read_csv(path)
        parts.append(pd.DataFrame({'stage0_item': item, 'check_id': df[idcol], 'segment': df[seg] if seg else '',
                                   'object': df[objcol] if objcol else '', 'metric': df[metcol], 'status': df[statcol],
                                   'source_file': os.path.relpath(path, RES)}))
    add('1', os.path.join(RES, 'stage0/anchor1_rerun/anchor1_results.csv'), 'check_id', 'object', 'metric')
    add('2', os.path.join(RES, 'stage0/anchor2_rerun/anchor2_results.csv'), 'check_id', 'object', 'metric', seg='segment')
    add('3', os.path.join(RES, 'stage0/anchor3/anchor3_results.csv'), 'test', 'object', 'metric', seg='segment')
    add('4', os.path.join(RES, 'stage0/features/synthetic.csv'), 'test', None, 'what')
    for p in sorted(glob.glob(os.path.join(RES, 'stage0/features/real_*.csv'))):
        add('4', p, 'test', None, 'what', seg='segment')
    add('4', os.path.join(RES, 'stage0/plan_tests/plan_tests_flat.csv'), 'name', None, 'name')
    add('5', os.path.join(RES, 'stage0/replay/replay_results.csv'), 'test', None, 'what')
    add('5', os.path.join(RES, 'stage0/guard_attack/guard_attack_results.csv'), 'entry_id', 'entry', 'attack')
    a0 = json.load(open(os.path.join(RES, 'registry/a0_manifest.json')))
    parts.append(pd.DataFrame([dict(stage0_item='5', check_id='A0-%s' % k, segment='', object='registry', metric=k,
                                    status='PASS' if v else 'FAIL', source_file='registry/a0_manifest.json') for k, v in a0['checks'].items()]))
    return pd.concat(parts, ignore_index=True)


def plan_tests_flat():
    d = json.load(open(os.path.join(RES, 'stage0/plan_tests/test_results.json')))
    df = pd.DataFrame(d['results'])
    J.atomic_write_csv(os.path.join(RES, 'stage0/plan_tests/plan_tests_flat.csv'), df)
    return d


FORMULA = [
    (r'^J_B1_b20$', 'b20_lag = mean(x[t−20..t−1])（x = 换手率）', 20, 10),
    (r'^J_B1_a20$', 'a20 = x_t / b20_lag', 20, 10),
    (r'^J_B1_qCC$', 'q = 1 / (|r_cc| + ε)', 1, 1),
    (r'^J_B1_S20lag$', 'S20_lag = a20 × q', 20, 10),
    (r'^J_B1_S60lag$', 'x_t / mean(x[t−60..t−1]) × q', 60, 30),
    (r'^J_B1_logK0$', 'log(x / (|r_cc| + ε))，x > 0', 1, 1),
    (r'^J_B1_logS20lag$', 'log(S20_lag)，S20_lag > 0', 20, 10),
    (r'^J_B2_POINT_(\w+)_(\w+)$', 'POINT = z_t / (y_t + ε)', 1, 1),
    (r'^J_B2_MR3_', 'MR3 = mean₃(z / (y + ε))', 3, 2),
    (r'^J_B2_MR5_', 'MR5 = mean₅(z / (y + ε))', 5, 4),
    (r'^J_B2_ROS20_', 'ROS20 = Σ₂₀ z / Σ₂₀ (y + ε)（有效配对）', 20, 10),
    (r'^J_B2_SLOPE20_', 'SLOPE20 = OLS(y ~ 1 + z) 斜率（有效配对）', 20, 10),
    (r'^J_B3A_Q(\w+)_(\w+)_W(\d+)$', 'Q_λ = mean(x)·mean(1/d) + λ·cov_pop(x, 1/d)，d = y + ε', None, None),
    (r'^J_B3A_COVP_', 'COV / P（P ≤ 0 或非有限 → NA）', None, None),
    (r'^J_B3B_BETANORM_', 'β · mean(x) / (mean(y) + ε)', 20, 10),
    (r'^J_B3B_RHO_', 'corr(x, y)（y 常数 → NA）', 20, 10),
    (r'^J_B3B_SCALE_', 'sd(y) / sd(x)', 20, 10),
    (r'^J_B3C_REL_', '留一可靠性 r = (n/20)(1 − u)，u = median|β_{−j}−β| / (|β| + median|β_{−j}−β| + 32·eps·max(|β|, median|β_{−j}|))；留一需 ≥ 10 对', 20, 11),
    (r'^J_B4_ROS_', 'K_s^ROS = Σ_s x / Σ_s (|r| + ε)，s ∈ {up, down}；侧别 ≥ 3 日且全窗 ≥ 10 对', 20, 10),
    (r'^J_B4_MR_', 'K_s^MR = mean_s[x / (|r| + ε)]', 20, 10),
    (r'^J_B4_ASYM_', 'log K_up − log K_down（两边正且有效）', 20, 10),
    (r'^J_B5_RARPRE_', 'x_t / mean_pre(x) / (y_t + ε)，pre = [c−W, c−1] 冻结', None, None),
    (r'^J_B5_REV_', 'R_ev = (Σ_[c,t] d_ε / Σ_[c,t] x) / (mean_pre d_ε / mean_pre x)', None, None),
    (r'^J_B5_REV5_', 'R_ev5：m = 5 先验日收缩', None, None),
    (r'^J_B5_U_', 'U = [y_t − a_pre − β_pre·x_t] / (mean_pre y + ε)（事件前 OLS 冻结）', None, None),
    (r'^J_B6_CV20$', 'sd₂₀(x) / mean₂₀(x)', 20, 10),
    (r'^J_B6_RELROLL20$', 'sd_{s=t−19..t}(x_s / b20_lag(s))', 20, 10),
    (r'^J_B6_DETREND20$', 'sd(OLS(x_s ~ 1 + s) 残差) / mean₂₀(x)（e6i_features.rtrend）', 20, 10),
]


def feature_contracts():
    J_cov = pd.read_csv(os.path.join(RES, 'feature_contracts_J.csv'))
    rows = []
    for _, r in J_cov.iterrows():
        mid = r.member_id
        f, w, mo = next(((f, w, mo) for pat, f, w, mo in FORMULA if re.search(pat, mid)), ('?', None, None))
        m = re.search(r'_W(\d+)', mid)
        if w is None and m:
            w = int(m.group(1)); mo = {3: 2, 20: 10, 60: 30}.get(w)
        rows.append(dict(member_id=mid, source='E6j J（e6j_features）', block=mid.split('_')[1], formula=f, window=w, min_obs=mo,
                         epsilon='1e-4（仅 |收益|）', ddof='std 1 / 分解 0', valid_mask='E6i Base valid（is_open & OHLC>0 & L≤min(O,C) & H≥max(O,C)）',
                         missing_policy='NaN（不补 0）→ 账户层 FALLBACK', event_clock=('last_trigger' if mid.endswith('_LT') else 'spell_entry' if mid.endswith('_SE') else 'none'),
                         warm='E6i 同款预热（段首前 260 自然日；2010-2014 无更早数据）', neutralize='pool0 当日 log 市值 OLS（NS）',
                         rank='hi: s.rank(pct) / lo: (−s).rank(pct)',
                         **{'cov_pool0_%s' % s: r.get(s) for s in J.SEGMENTS}))
    sem = pd.read_csv(os.path.join(J.E6I_RES, 'registry', 'feature_semantics_v2.csv'))
    used = ['K0_LEGACY', 'K_rar20', 'K_slope20', 'K_MA3_E6F', 'K_rarpre', 'K_samt20', 'K_amt5', 'K_samt5', 'K_amt20', 'T_ewcv20', 'R_peer20']
    for _, s in sem[sem.member_id.isin(used)].iterrows():
        rows.append(dict(member_id=s.member_id, source='E6i 缓存（严格继承源政策）', block='SRC', formula=s.estimand_id, window=s.window,
                         min_obs=s.min_obs, epsilon='1e-4', ddof=s.ddof, valid_mask=s.valid_mask, missing_policy=s.missing_policy,
                         event_clock=s.event_clock, warm='E6i 预热', neutralize=s.neutralize_scope, rank='E6i NS 表 hi / lo',
                         direction_primary=s.direction_primary, direction_competing=s.direction_competing))
    return pd.DataFrame(rows)


def permission_ledger():
    return dict(version=J.VERSION, entries=[
        dict(id='PERM-01', what='开工执行 brief v1.2（Stage 0 → 4，按 §14 节奏）', source='用户 2026-09-27 本会话消息',
             quote='仔细阅读并理解 如果有需要补充和调整的地方 补充和调整好之后 确认方向 内容和细节都没问题以及参考的相关文献和资料都完整后 可以开工',
             status='granted（执行端确认后开工；W12 proceed 依据之一）', excludes='生产改动 / 对外数字 / E7 读取'),
        dict(id='PERM-02', what='记录 B：B 包后段事前整表授权', source='E6j_RULING_20260926.md（用户 2026-09-26 回复 "B"）',
             conditions=['Stage 0 六项锚全 PASS', 'routing_review_A1_auto.md 七项全 PASS', '进入 Stage 3 时冻结清单 sha 与授权时相同'],
             status='pending_conditions（Stage A 写 record_B_preauthorized_E6j.json；条件核验写 record_B_conditions_receipt.json）'),
        dict(id='PERM-03', what='policy_confirmation_status', value='confirmed_by_proceeding', source='E6i_RULING 第 15 项 + brief W12'),
        dict(id='PERM-04', what='E7', value='HOLD：不读 2026-03-27 之后任何真实行情'),
        dict(id='PERM-05', what='deployment_authorized', value=False, note='永远由用户改'),
        dict(id='PERM-06', what='生产 v2 / v3 展示候选 / U34 / U35 / I11 / DEV 改动', value='未授权'),
        dict(id='PERM-07', what='对外 / 领导数字', value='须用户过目'),
        dict(id='PERM-08', what='git', value='白名单提交 + push main；不 git add .；提交前扫描登录 / 主机 / 账号信息'),
        dict(id='PERM-09', what='H 网格', value='brief W10：{1,2,3,5,10,15,20}；用户若改全整数须在 A0 冻结前，冻结后改 = amendment（记录 B 授权失效）')])


def main():
    d = plan_tests_flat()
    ar = anchor_results()
    ar_path = os.path.join(RES, 'anchor_results.csv'); J.atomic_write_csv(ar_path, ar)
    fc = feature_contracts(); fc_path = os.path.join(RES, 'feature_contracts.csv'); J.atomic_write_csv(fc_path, fc)
    pl_path = os.path.join(RES, 'permission_ledger.json'); J.atomic_write_json(pl_path, permission_ledger())
    rec = {}
    for item, tids in RECEIPTS.items():
        rs = [receipt(t) for t in tids]
        rec[item] = dict(receipts=tids, status=[(r or {}).get('status') for r in rs],
                         ok=all(r is not None and r.get('status') == 'SUCCEEDED' for r in rs))
    head = subprocess.run(['git', '-C', J.CODE, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    man = dict(version=J.VERSION, written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), git_head=head, env=J.env_versions(),
               docs_sha256={f: J.sha_file(os.path.join(RES, f)) for f in DOCS if os.path.exists(os.path.join(RES, f))},
               code_sha256={f: J.sha_file(os.path.join(J.CODE, f)) for f in CODE_FILES},
               e6j_code_sha256={os.path.basename(p): J.sha_file(p) for p in sorted(glob.glob(os.path.join(J.CODE, 'e6j_*.py')))},
               e5a_sha256={os.path.basename(p): J.sha_file(p) for p in sorted(glob.glob(os.path.join(J.E5A_RES, '*.csv')))},
               e6i_registry_sha256={f: J.sha_file(os.path.join(J.E6I_RES, 'registry', f)) for f in ('mothers.csv', 'feature_semantics_v2.csv')},
               plan_tests=dict(total=d['total'], passed=d['passed'], python=d['python'], numpy=d['numpy'], pandas=d['pandas']),
               stage0=rec, stage0_all_pass=all(v['ok'] for v in rec.values()),
               anchor_results=dict(n=len(ar), status=ar.status.value_counts().to_dict()),
               discrepancies='source_resolution.md §2（17 条）', market_data_end_max=J.MARKET_DATA_END_MAX)
    man_path = os.path.join(RES, 'source_manifest.json'); J.atomic_write_json(man_path, man)
    deliv = ('source_manifest.json', 'parent_identity_map.csv', 'anchor_results.csv', 'feature_contracts.csv', 'permission_ledger.json')
    rec['6_deliverables'] = dict(files=list(deliv), ok=all(os.path.exists(os.path.join(RES, f)) for f in deliv))
    ok = man['stage0_all_pass'] and rec['6_deliverables']['ok'] and int((ar.status == 'FAIL').sum()) == 0
    J.write_receipt('stage0_close', [ar_path, fc_path, pl_path, man_path], 'SUCCEEDED' if ok else 'FAILED', stage0_all_pass=ok)
    print(json.dumps(dict(stage0=rec, anchor_status=man['anchor_results'], head=head, ok=ok), ensure_ascii=False, indent=1, default=str))
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
