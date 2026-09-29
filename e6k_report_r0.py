# -*- coding: utf-8 -*-
"""E6k_REPORT_R0（plan §13.5：输入身份、授权、源锚、新算子、mask / 风险事实与全部 LIMIT；brief W18：R0 环境节按随机量逐类写生成器）。
输入：source_manifest.json、stage0/*、registration/*、registry/*、diagnostics/control_distributions/*、limit_register（L 条目由本脚本列出）。
不含任何登记对象的收益读数（掩码事实与对照分布只作描述，注明未用于门值）。"""
import e6k_boot  # noqa: F401
import os
import sys
import glob
import json

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_report as RP

OUT = K.P('reports', 'E6k_REPORT_R0.md')


def head(subject, sub, unit='计数', dates='四段（Stage 0）或推导两段（掩码事实）', H='—', support='—', expo='不适用（无收益读数）'):
    return {'主体': subject, '算子': '—', '分母': '见表', '基准': '—', '子集': sub, '单位': unit, '日期': dates, 'H': H, '成本模型': '—',
            '支持': support, '资本视图': '—', 'exposure': expo}


def main():
    sm = json.load(open(K.P('source_manifest.json'), encoding='utf-8'))
    a0 = json.load(open(K.P('registration', 'a0_manifest_E6k.json'), encoding='utf-8'))
    rp = RP.Report('R0')
    rp.h(1, 'E6k REPORT R0 —— 输入身份、授权、源锚、新算子恒等、掩码 / 风险事实与限制')
    rp.p('用途：plan §13.5 R0。全部数字来自 `source_manifest.json`、`stage0/`、`registration/`、`registry/` 与 `diagnostics/control_distributions/`；'
         '本文件不含任何登记对象的收益读数。')
    # 1 身份
    rp.h(2, '1. 输入身份（三处镜像；全长 sha 见 source_manifest.docs_sha256 与 stage0/local_exec_briefs_hashes.json）')
    docs = pd.DataFrame([dict(file=k, sha256_16=v[:16]) for k, v in sm['docs_sha256'].items()])
    rp.table(docs, head('本轮输入与结果目录副本', 'docs_sha256'), 'E6K-R0-DOCS')
    env = sm['env']
    envt = pd.DataFrame([dict(item=k, value=str(v)) for k, v in env.items()] + [dict(item='git_head', value=sm['git_head'][:12])])
    rp.table(envt, head('47 环境与生成器', 'source_manifest.env'), 'E6K-R0-ENV')
    gens = pd.DataFrame([
        dict(random_quantity='LEGACY_POLICY_RANDOM（E6j R-MATCH-SRC 复现）', generator='splitmix64 计数器 u(键, 绝对交易日, ticker)；键 = blake2b-64(canonical_json)：E6j.P / E6j.B 命名空间（E6j 原键）',
             receipt_field='run_rand_* generator'),
        dict(random_quantity='NEW_COND_ISK_P5 / NEW_COND_ISK_IID / EIGHT_SUBSET_*', generator='同一 splitmix64 计数器；键 = blake2b-64(canonical_json(E6k.NEW, 测量, 分区, 块长, path))；块 = 绝对交易日 // 块长',
             receipt_field='run_rand_* generator'),
        dict(random_quantity='bootstrap（段内分层 stationary）', generator='blake2b-128(canonical_json(E6k, bootstrap, L, 段)) → SeedSequence → PCG64；e6j_stats.stationary_indices',
             receipt_field='bootstrap_full generator'),
        dict(random_quantity='衰减场景时间块', generator='blake2b-128(canonical_json(E6k, decay, L, 段)) → SeedSequence → PCG64', receipt_field='decay_scenarios'),
        dict(random_quantity='profile 置换（只测时，临时目录，不入结果）', generator='default_rng(blake2b(E6k.profile, 段, 任务))', receipt_field='—'),
    ])
    rp.table(gens, head('随机量 → 生成器 → 回执字段（W18；E6j E05 改法）', '全部随机量'), 'E6K-R0-GEN')
    # 2 授权
    rp.h(2, '2. 授权与读数前登记')
    au = []
    for f in ('record_B_mode_A.json', 'record_B_approved_E6k.json', 'record_B_preauthorized_E6k.json', 'record_B_conditions_receipt_E6k.json',
              'executor_supplements_E6k.json', 'executor_supplements_E6k_amend_1.json', 'policy_profiles_E6k.json', 'policy_profiles_E6k_amend_1.json',
              'policy_profiles_E6k_amend_2.json', 'preregistration_amend_20260929.md', 'P_package_manifest_E6k.json', 'B_package_manifest_E6k.json',
              'a1_auto_E6k.json', 'a1_auto_masks_E6k.json', 'a1_auto_masks_post_E6k.json', 'a1_auto_draft_E6k.json', 'seal_deriv.json'):
        p = K.P('registration', f)
        au.append(dict(file='registration/' + f, present=os.path.exists(p), sha256_16=K.sha_file(p)[:16] if os.path.exists(p) else ''))
    for f in sorted(glob.glob(K.P('registration', 'seal_post*.json'))):
        au.append(dict(file=K.rel(f), present=True, sha256_16=K.sha_file(f)[:16]))
    rp.table(pd.DataFrame(au), head('授权 / 登记 / 封存文件', 'registration/'), 'E6K-R0-AUTH')
    ap_ = K.P('registration', 'record_B_approved_E6k.json')
    if os.path.exists(ap_):
        ap = json.load(open(ap_, encoding='utf-8'))
        rp.p('- 授权方式：用户转交消息不含"B" → 方式 A；推导两段封存后用户一句话：「%s」（%s；`record_B_approved_E6k.json` 写于 %s，'
             '记录背景见其 context_note）→ 条件回执 all_pass → 两后段同版本计算。E6j REVIEW §11 经济裁定未给 → `policy_provisional = true`。'
             % (ap['user_quote'], ap['user_quote_date'], ap['written_at']))
    else:
        rp.p('- 授权方式：用户转交消息不含"B" → 方式 A（推导两段封存后停等用户一句话）；E6j REVIEW §11 经济裁定未给 → `policy_provisional = true`。')
    # 3 Stage 0
    rp.h(2, '3. Stage 0 六类（source_manifest.stage0；FAILED 由同名 _rerun 覆盖）')
    s0 = pd.DataFrame([dict(category=k, ok=v['ok'], receipts='；'.join('%s=%s' % (r['task'], r['status']) for r in v['receipts'])) for k, v in sm['stage0'].items()])
    rp.table(s0, head('Stage 0 六类回执', 'source_manifest.stage0'), 'E6K-R0-STAGE0')
    for cat, pat in (('c2_source', 'stage0/c2_source/*.csv'), ('c3_ops', 'stage0/c3_ops/ops_identity_*.csv'), ('c4_data', 'stage0/c4_data/*.csv'),
                     ('c5_random', 'stage0/c5_random/random_checks.csv'), ('c6_output', 'stage0/c6_output/output_checks.csv'),
                     ('c1_identity', 'stage0/c1_identity_rerun/identity_checks.csv')):
        fs = glob.glob(K.P(*pat.split('/')))
        if not fs:
            continue
        df = pd.concat([pd.read_csv(f).assign(file_segment=os.path.basename(f)[:-4].split('_')[-1]) for f in fs], ignore_index=True)
        key = 'check_id' if 'check_id' in df.columns else 'item'
        gk = [key, 'status'] if cat != 'c3_ops' else ['file_segment', key, 'status']      # X04：第 3 类按段分列（后段为授权后补算）
        t = df.groupby(gk).size().unstack(fill_value=0).reset_index()
        rp.table(t, head('Stage 0 %s 逐项状态计数' % cat, pat), 'E6K-R0-S0-%s' % cat.upper().replace('_', ''))
    # 4 A0 / A1-auto
    rp.h(2, '4. A0 与 A1-auto')
    c = a0['counts']
    t = pd.DataFrame([dict(item=k, value=json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in c.items()
                      if k not in ('structural_alias',)])
    rp.table(t, head('A0 计数（每段）', 'a0_manifest_E6k.json'), 'E6K-R0-A0')
    a1 = json.load(open(K.P('registration', 'a1_auto_E6k.json'), encoding='utf-8'))
    rp.table(pd.DataFrame(a1['items'])[['item', 'sub', 'what', 'status']], head('A1-auto（读数前）', 'a1_auto_E6k.json'), 'E6K-R0-A1PRE')
    # 5 掩码事实
    rp.h(2, '5. 掩码事实（附录 B；推导段；只作描述与预冻结回退 / 不适用标注，不生成阈值、不挑臂）')
    mf = pd.read_csv(K.P('registry', 'mask_facts_deriv_E6k.csv'))
    mf = mf[mf.op != 'FALLBACK_DOMAIN']
    mf['family'] = mf.op.str.replace(r'\d+$', '', regex=True).str.replace(r'_(SA|PM|HG)$', r'_\1', regex=True)
    agg = mf.groupby('family').agg(targets=('target_id', 'count'), n_edits_in=('n_edits_in', 'median'), edit_weight_share=('edit_weight_share', 'median'),
                                   size_edit_gap_T_signed=('size_edit_gap_T', 'median'), size_port_delta_T_signed=('size_port_delta_T', 'median'),
                                   small30_share_delta=('small30_share_delta', 'median'), size_unknown_weight=('size_unknown_weight', 'median'),
                                   overlap_with_native=('same_ticker_overlap_with_native', 'median')).reset_index()
    rp.table(agg, head('掩码事实中位（按算子族；目标 × 段）', 'mask_facts_deriv_E6k.csv', unit='名数 / 份额 / 百分位点', dates='推导两段'), 'E6K-R0-MASK')
    fl = mf['flags'].dropna().str.split('|').explode()
    fl = fl[fl != ''].value_counts().rename_axis('flag').reset_index(name='targets')
    rp.table(fl, head('预冻结回退 / 不适用标注触发计数', 'mask_facts_deriv_E6k.csv', dates='推导两段'), 'E6K-R0-FLAGS')
    fd = pd.read_csv(K.P('registry', 'mask_facts_deriv_E6k.csv'))
    fd = fd[fd.op == 'FALLBACK_DOMAIN'][['segment', 'meas', 'mother', 'fallback_native_kf_missing', 'fallback_szl_inc_z_missing']]
    rp.table(fd, head('回退域（K 腿有效域内：新测量缺 / size 缺份额）', 'FALLBACK_DOMAIN', unit='份额', dates='推导两段'), 'E6K-R0-FBDOM')
    mpp = K.P('registry', 'mask_facts_post_E6k.csv')
    if os.path.exists(mpp):                                             # X04：后段授权后同代码补算
        mp = pd.read_csv(mpp)
        fdp = mp[mp.op == 'FALLBACK_DOMAIN'][['segment', 'meas', 'mother', 'fallback_native_kf_missing', 'fallback_szl_inc_z_missing']]
        mp = mp[mp.op != 'FALLBACK_DOMAIN'].copy()
        mp['family'] = mp.op.str.replace(r'\d+$', '', regex=True).str.replace(r'_(SA|PM|HG)$', r'_\1', regex=True)
        aggp = mp.groupby('family').agg(targets=('target_id', 'count'), n_edits_in=('n_edits_in', 'median'), edit_weight_share=('edit_weight_share', 'median'),
                                        size_edit_gap_T_signed=('size_edit_gap_T', 'median'), size_port_delta_T_signed=('size_port_delta_T', 'median'),
                                        small30_share_delta=('small30_share_delta', 'median'), size_unknown_weight=('size_unknown_weight', 'median'),
                                        overlap_with_native=('same_ticker_overlap_with_native', 'median')).reset_index()
        dp = '2019-01-02..2026-03-27（两后段；X04 授权后补算）'
        rp.table(aggp, head('掩码事实中位（按算子族；目标 × 段）', 'mask_facts_post_E6k.csv', unit='名数 / 份额 / 百分位点', dates=dp), 'E6K-R0-MASK-POST')
        flp = mp['flags'].dropna().str.split('|').explode()
        flp = flp[flp != ''].value_counts().rename_axis('flag').reset_index(name='targets')
        rp.table(flp, head('预冻结回退 / 不适用标注触发计数', 'mask_facts_post_E6k.csv', dates=dp), 'E6K-R0-FLAGS-POST')
        rp.table(fdp, head('回退域（K 腿有效域内：新测量缺 / size 缺份额）', 'FALLBACK_DOMAIN', unit='份额', dates=dp), 'E6K-R0-FBDOM-POST')
    # RP 求解路径（X08；facts_*.csv 的 rp_solver 计数；名单层事实，不读收益）
    rs = []
    for s in K.SEGMENTS:
        for f in sorted(glob.glob(K.P('accounts', s, 'facts_*.csv'))):
            fa = pd.read_csv(f)
            if 'rp_solver' not in fa.columns:
                continue
            fa = fa[fa.rp_solver.notna() & fa.op.astype(str).str.startswith('RP')] if 'op' in fa.columns else fa[fa.rp_solver.notna()]
            for v in fa.rp_solver:
                for k, n in json.loads(v).items():
                    rs.append(dict(segment=s, solver=k, days=int(n)))
    if rs:
        rsd = pd.DataFrame(rs).groupby(['segment', 'solver']).days.sum().unstack(fill_value=0).reset_index()
        rp.table(rsd, head('RP 逐日求解路径计数（全部 RP 目标 × 日 × τ 求和；recovered_* = 主路径复核失败后由独立精确路径恢复；SOLVER_LIMIT* = 隔离回父）',
                           'accounts/<段>/facts_*.csv 的 rp_solver', unit='目标 × 日 × τ', dates='四段'), 'E6K-R0-RPSOLVER')
    # 6 对照分布
    cds = sorted(glob.glob(K.P('diagnostics', 'control_distributions', '*.csv')))
    if cds:
        rp.h(2, '6. 对照分布（附录 C；诊断，未用于任何门值）')
        cd = pd.concat([pd.read_csv(f).assign(segment=os.path.basename(f)[:-4]) for f in cds], ignore_index=True)
        t = cd.groupby(['kind', 'metric']).agg(objects=('desc_id', 'nunique'), q10=('q10', 'median'), q50=('q50', 'median'), q90=('q90', 'median'),
                                               p95=('p95', 'median')).reset_index()
        rp.table(t, head('C0 / C1 / LEGACY / IID 对照分布（跨对象中位的分位）', 'diagnostics/control_distributions', unit='百分位点 / 份额 / 年化百分点',
                         expo='对照（C1 为已暴露原生对象；随机路径无登记读数）'), 'E6K-R0-CTRL')
    # 7 LIMIT
    rp.h(2, '7. 限制（全部；limit_register_E6k.md 同步）')
    lim = [
        ('L01', '同一历史反复研究：后段是新算子首次评价（NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY），不是样本外'),
        ('L02', 'RP 最优性只在固定规范配对集内（plan §5.4 更正）；未配对结构性编辑不执行'),
        ('L03', 'LX 为本项目的配额 / 优先序移植（E6j matched_n 同 N 合同键），不是 DGTW AS 公式；A4b 的 T 重估不是固定共同门'),
        ('L04', 'HG 主历史四段段首空状态（对齐旧引擎 reset）；跨段连续状态只在 48 个 HG 主展示对象作诊断'),
        ('L05', 'z_LAG1 段首日无 T−1（未知 size 处理）；size 紧区间对共同未知只算一次'),
        ('L06', 'Stage 0 第 3 类新算子恒等锚只在推导两段（后段在授权后同代码补算）'),
        ('L07', 'A6-3 / A3-12 在 profile 产物上抽样 455 / 154（附录 500 / 200）；推导段真实账户落盘后足额复核（checks/closure_deriv.csv）'),
        ('L08', '随机均值是条件于历史的机会基线，不是精确 p 值；MC 误差另报（plan §10.2 / W15）'),
        ('L09', 'descriptors_E6k.csv 的 evidence_exposure 列为编译器粗分类；逐账户暴露以 selection_exposure_ledger_E6k.csv 为准'),
        ('L10', '对照分布的随机路径只取前 256 条（诊断）'),
        ('L11', '冲击括号（A 5 亿 κ .5 / A 10 亿 κ 1）为未校准情景，不是实际成交成本'),
        ('L12', 'SMB 暴露回归与尾部账本只作描述；截距占比不等于"不是 size"（plan §10.3）'),
    ]
    if rs:
        R_ = pd.DataFrame(rs)
        rec = R_[R_.solver.str.startswith('recovered')].groupby('segment').days.sum().to_dict()
        lim_ = R_[R_.solver.str.startswith('SOLVER_LIMIT')].groupby('segment').days.sum().to_dict()
        lim.append(('L13', 'RP 主路径（DFS 节点上限 → 逐级 MILP）在部分日复核失败（HiGHS presolve 下见证解越出预算，2026-09-29 后段首跑发现）：按 X08 / plan §5.4 '
                           '第 6 条由两条独立精确路径恢复（关闭 presolve、逐级见证复核的 MILP；带符号可达界剪枝的精确深搜；两者一致才采用），恢复日计数 %s；'
                           '未恢复日隔离回父并标 SOLVER_LIMIT，计数 %s（含此类日的 RP 账户是混合路径，不称完整 RP 经济结果）；推导两段无失败日（主路径结果与恢复代码无关）'
                           % (json.dumps(rec, ensure_ascii=False) if rec else '{}', json.dumps(lim_, ensure_ascii=False) if lim_ else '{}')))
    lim.append(('L14', '执行端补充 X04：Stage 0 第 3 类新算子恒等锚与 A1-auto 掩码事实在两后段于授权后同代码补算（R0 第 3 / 5 节按段分列）；'
                       '后段第 3 类结果不回写 Stage 0 manifest（source_manifest 保持开工时状态）'))
    lim.append(('L15', '两个诊断的首版退化、由 v2 替代（v1 文件保留不删、不作读数）：衰减场景前瞻版误用同一 draw（`diagnostics/decay/decay_scenarios.csv` → '
                       '`decay_scenarios_v2.csv`）；HG 跨段连续状态（X09）的上段末状态在段首预热日（门域 K = 0）被清空（`hg_continuous_<段>_<段>.csv` → '
                       '`hg_continuous_v2_*.csv`，hold_init 只用于该诊断，登记账户不变）'))
    lim.append(('L16', '覆盖不足（登记 query 有、本轮未记账）：PM 固定配对交换数的嵌套与结构单边编辑（E6K-Q10-c）；TREFIT 第二关逐日有效样本数（E6K-Q07-b）；'
                       'POST2 第二关前编辑数只以最终名单相对原父的换入近似（E6K-Q08-b）'))
    rp.table(pd.DataFrame(lim, columns=['id', 'limit']), head('限制登记（L01 起）', 'limit_register_E6k.md'), 'E6K-R0-LIMITS')
    K.atomic_write_text(K.P('reports', 'E6k_limit_register.md'), '# E6k limit_register（L01 起；执行端）\n\n' + '\n'.join('- **%s** %s' % x for x in lim) + '\n')
    rp.write(OUT)
    K.write_receipt('report_r0', [OUT, K.P('reports', 'E6k_limit_register.md')], 'SUCCEEDED', queries=len(rp.qids))
    print('R0 写出：%d 个 query' % len(rp.qids), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
