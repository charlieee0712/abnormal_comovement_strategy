# -*- coding: utf-8 -*-
"""E6m 报告（plan §13.4 最少交付；brief §5 S4"七份 REPORT + cards + E7 准备页"）。part1 与记录 B 草稿在 e6m_s_part1。
全部机械生成：只给数与状态，每张表带读法表头，不写判词；新算子一律 NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY、deployment_authorized = false、
replacement NOT_AUTHORIZED；SECOND_EVALUATION_SAME_HISTORY 不进"本轮新证据"栏。读真实结果目录前过后段守卫与两道封存门；全部输入都在 stageS_dev
（合成开发测试）时跳过守卫并在每份报告顶部标"SYNTHETIC，非收益"。
  r0 | part2 | part3 | mechanisms | b3 | carried | cards | e7 | all"""
import e6j_boot  # noqa: F401
import os
import sys
import glob
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
from e6m_s_part1 import Report

SEGS = tuple(M.SEGMENTS)
SYN = '**开发测试版：本文件全部数字来自 SYNTHETIC 合成账本 / 合成统计，不是收益，不得引用。**'


def head(subject, op, sub, unit='年化百分点（ann_pp）', base='同 H 实际父（8bp）', H='见 H 列', dates='2010-01-04 … 2026-03-27（四段）'):
    return {'主体': subject, '算子': op, '分母': '各段有效配对日', '基准': base, '子集': sub, '单位': unit, '日期': dates, 'H': H,
            '成本': '源 8bp', 'exposure': '见 exposure 列（首评 / 二次评估）'}


def jload(p):
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


def csv(p, **kw):
    return pd.read_csv(p, keep_default_na=False, na_values=[''], low_memory=False, **kw) if os.path.exists(p) else None


def cat(pattern, segs=SEGS):
    parts = [csv(pattern % s).assign(segment=s) for s in segs if os.path.exists(pattern % s)]
    return pd.concat(parts, ignore_index=True) if parts else None


def dev_mode(paths):
    paths = [p for p in paths if p]
    return bool(paths) and all('stageS_dev' in os.path.realpath(p) for p in paths)


def gate(a, paths):
    if dev_mode(paths):
        return True
    import e6m_s_gate as GT
    import e6m_s_seal as SEAL
    GT.post_gate(M.POST_SEGS[0], 'reports')
    SEAL.require('deriv')
    SEAL.require('post')
    return False


def start(name, a, title, dev):
    rp = Report(name, a.out)
    rp.h(1, title)
    if dev:
        rp.p(SYN)
    return rp


# ====================================================================== R0
def r0(a, dev):
    rp = start('R0', a, 'E6m REPORT R0 —— 运行总览、授权、Stage 0、封存、覆盖、限制与待决策端事项', dev)
    rp.p('用途：plan §13.4 R0。只列状态与计数（来自机器表）；研究读数见 part1 / part2 / part3 / mechanisms / B3 / cards。')
    rp.h(2, '1. 授权与冻结')
    rp.p('⑬b 八张卡的反解释与 §5 第 1–25 项、B4 签名 1–3 的定义由用户授权执行端代拟、advisor 复核（不冒称决策端；L-S8），见下列两份 registration 文件与 '
         '`exec_briefs/E6m_stageS_decisions_delegated.md`；两份 JSON 进 Stage B 冻结清单。')
    for nm, p in (('W11 方式（阶段 N）', M.P('registration', 'authorization_status_E6m.json')),
                  ('W11 方式（阶段 S 决定，照录用户原话）', M.P('registration', 'authorization_status_E6m_S.json')),
                  ('冻结清单', M.P('registration', 'stageB_freeze_E6m.json')),
                  ('方式 A 批准（用户原话）', M.P('registration', 'record_B_approved_E6m.json')),
                  ('方式 B 事前授权（用户原话）', M.P('registration', 'record_B_preauthorized_E6m.json')),
                  ('生效条件回执', M.P('registration', 'record_B_conditions_receipt_E6m.json')),
                  ('⑬b 反解释（用户授权代拟）', M.P('registration', 'counter_explanations_decision_E6m.json')),
                  ('§5 / 签名 1–3 决定（用户授权代拟）', M.P('registration', 'delegated_decisions_E6m_S.json'))):
        j = jload(p)
        if j is None:
            rp.p('- %s：文件缺（`%s`）' % (nm, M.rel(p)))
        else:
            keep = {k: j[k] for k in ('w11_mode', 'mode', 'user_quote', 'user_quote_date', 'all_pass', 'frozen_manifest_sha256', 'freeze_sha256', 'written_at')
                    if k in j}
            if 'basis' in j:
                keep['basis_user_quote'] = j['basis'].get('user_quote')
            rp.p('- %s：`%s`，sha256 前 16 = %s；%s' % (nm, M.rel(p), M.sha_file(p)[:16], M.san(json.dumps(keep, ensure_ascii=False))[:600]))
    rp.h(2, '2. Stage 0 S 与 A1-auto（阶段 S）')
    rp.p('数据口径：X01 文本重建只用于 import 诊断与随机层 import 测试，不进任何账户 / 特征计算（L-S9）；Stage A 四段掩码层事实在 Stage B 冻结前计算、'
         '不读收益、不经后段守卫（L-S10，第 12 项决定确认）。')
    for nm, p in (('Stage 0 S 门', M.P('stage0_S', 'stage0_S_gate.json')), ('A1-auto（S）', M.P('registration', 'a1_auto_E6m_S.json'))):
        j = jload(p)
        rp.p('- %s：%s' % (nm, '文件缺' if j is None else M.san(json.dumps({k: j[k] for k in ('counts', 'all_pass', 'fail_items', 'source_wait_items',
                                                                                       'not_run_items', 'not_pass') if k in j}, ensure_ascii=False))[:900]))
    S = csv(M.P('stage0_S', 'stage0_S_summary.csv'))
    if S is not None:
        rp.table(S, {'主体': 'Stage 0 S 检查表', '单位': '行数', '子集': '附录 A 标 S 的项'}, 'E6M-R0-S0')
    rp.h(2, '3. 封存')
    for ph in ('deriv', 'post'):
        j = jload(M.P('seal_%s.json' % ph))
        rp.p('- seal_%s：%s' % (ph, '文件缺' if j is None else json.dumps({k: (len(j[k]) if isinstance(j[k], list) else j[k]) for k in
                                                                         ('written_at', 'n_files', 'tasks_expected', 'queue_missing', 'failed_unresolved', 'mc_done',
                                                                          'all_ok') if k in j}, ensure_ascii=False)))
    rp.h(2, '4. 覆盖（登记 = 已算）')
    X = csv(os.path.join(a.aux or '', 'aux_status_summary_full.csv')) if a.aux else None
    if X is not None:
        rp.table(X, {'主体': '附属清单 66,698 行', '单位': '行数', '子集': 'item × 类 × 状态'}, 'E6M-R0-AUX')
    else:
        rp.p('附属覆盖汇总缺（e6m_s_aux_status 未跑）。')
    rp.p('状态读法：第 7 项两条撮合链（FULL_FILL_SAME_MODEL / SOURCE_LIMIT_SHADOW）552 行为 LIMIT（源模型不具备撮合细节，L-S1）；'
         '第 7 项源理论连续链 138 行由连续面板逐 aux_id 判定（L-S2）；主 72 记忆配方 2、3 的 H1 / 3 / 10 / 20 对应桥 192 行为 DEFINITION_PENDING（L-S7）。')
    rp.h(2, '5. 标签与读法')
    A = csv(M.P('stage0_S', 'c2_c4', 'anchor_map_E6m.csv'), dtype=str)
    if A is not None:
        rp.table(A.groupby(['anchor_candidate', 'exposure_S1']).size().reset_index(name='objects'), {'主体': '描述符', '单位': '个数',
                 '子集': '锚候选 × S1 暴露标签'}, 'E6M-R0-EXPO')
    rp.p('全部对象 deployment_authorized = false；新路线 replacement_preference_status = NOT_AUTHORIZED；`%s` 不进"本轮新证据"栏。' % M.LABEL_SECOND)
    rp.h(2, '6. 限制登记与待决策端事项')
    p = M.P('reports', 'E6m_limit_register.md')
    p = p if os.path.exists(p) else M.P('stageN', 'limit_register_stageS_draft.md')
    if os.path.exists(p):
        rp.p('限制登记（`%s`，sha256 前 16 = %s）全文表：' % (M.rel(p), M.sha_file(p)[:16]))
        rp.p('\n'.join(l for l in open(p, encoding='utf-8').read().split('\n') if l.startswith('|')))
    else:
        rp.p('限制登记缺（SOURCE_WAIT）。')
    rp.p('- 执行端释义与决策端一次性裁定块：`stageN/STAGE_S_IMPL_PLAN.md` §5 / §6。')
    return rp.write('E6m_REPORT_R0.md'), rp.tables


# ====================================================================== part2
def part2(a, dev):
    rp = start('part2', a, 'E6m REPORT part2 —— 两后段与四段：作用量、比较视图、暴露标签与随机参照', dev)
    S = cat(os.path.join(a.stats, 'descriptor_stats_%s.csv'))
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    if S is None:
        rp.p('描述符统计缺（SOURCE_WAIT）。')
        return rp.write('E6m_REPORT_part2.md'), rp.tables
    S = S[S.status == 'COMPUTED'].merge(D[['desc_id', 'block', 'operator', 'memory', 'param', 'alpha', 'parent', 'H', 'is_primary72', 'primary_recipe', 'exposure']],
                                        on='desc_id', how='left', suffixes=('', '_reg'))
    W = S.pivot_table(index='desc_id', columns='segment', values='D', aggfunc='first')
    W.columns = ['D_%s' % c for c in W.columns]
    pol = csv(a.policy) if a.policy else None
    if pol is not None:
        W = W.join(pol.set_index('desc_id')[['FULL', 'G4', 'FULL_sc']], how='left')
    W = W.join(D.set_index('desc_id')[['parent', 'H', 'is_primary72', 'primary_recipe', 'exposure']], how='left')
    rp.h(2, '1. 主展示 72（四段 D、FULL / G4、资本视图 FULL_sc）')
    P72 = W[W.is_primary72 == 'True'].reset_index().sort_values(['primary_recipe', 'parent'])
    rp.table(P72, head('主展示 72', '12 配方', 'primary72'), 'E6M-P2-72', maxrows=72)
    rp.h(2, '2. 全部登记描述符四段分布（块 × 算子 × 记忆 × 参数）')
    g = S.groupby(['block', 'operator', 'memory', 'param', 'segment']).D.agg(cells='count', median='median', share_pos=lambda x: float((x > 0).mean()),
                                                                          q10=lambda x: float(x.quantile(.1)), q90=lambda x: float(x.quantile(.9))).reset_index()
    rp.table(g, head('全部登记描述符（不含 PARENT）', '各算子', '块 × 算子 × 记忆 × 参数 × 段', H='1…20'), 'E6M-P2-GRID', maxrows=80)
    C = cat(os.path.join(a.stats, 'comparison_stats_%s.csv'))
    if C is not None:
        rp.h(2, '3. 登记比较视图（四段）')
        cv = C[C.status == 'COMPUTED'].groupby(['view', 'segment']).agg(comparisons=('comparison_id', 'count'), median_D_ann_pp=('D_ann_pp', 'median'),
                                                                       share_pos=('D_ann_pp', lambda x: float((x > 0).mean())),
                                                                       median_mde80_ann_pp=('mde80_ann_pp', 'median')).reset_index()
        rp.table(cv, head('全部登记比较', '左 − 右', '视图 × 段', base='比较右端'), 'E6M-P2-VIEWS', maxrows=100)
    R = cat(os.path.join(a.stats, 'random_refs_%s.csv'))
    if R is not None:
        rp.h(2, '4. 随机参照（四段；e_random 只看两后段）')
        R2 = R.assign(hi=R.real_minus_rand >= 2 * R.mcse)
        rp.table(R2.groupby(['mechanism', 'segment']).agg(objects=('desc_id', 'count'), share_rmr_ge_2mcse=('hi', 'mean'), median_mcse=('mcse', 'median'),
                                                          paths_min=('n', 'min')).reset_index(), head('登记随机行', '各机制', '机制 × 段', base='同对象随机路径均值'),
                 'E6M-P2-RANDOM')
    rp.h(2, '5. 暴露标签')
    rp.table(W.groupby('exposure').size().reset_index(name='objects'), {'主体': '登记描述符', '单位': '个数', '子集': 'exposure'}, 'E6M-P2-EXPO')
    return rp.write('E6m_REPORT_part2.md'), rp.tables


# ====================================================================== part3
def part3(a, dev):
    rp = start('part3', a, 'E6m REPORT part3 —— 政策（四个 profile × FULL / G4）、生产变更候选清单、三句加法与同时带', dev)
    P = csv(a.policy) if a.policy else None
    if P is None:
        rp.p('政策表缺（SOURCE_WAIT）。')
        return rp.write('E6m_REPORT_part3.md'), rp.tables
    prof = sorted(c[len('policy_'):-len('_FULL')] for c in P.columns if c.startswith('policy_') and c.endswith('_FULL'))
    rows = []
    for pf in prof:
        for agg in ('FULL', 'G4'):
            vc = P['policy_%s_%s' % (pf, agg)].astype(str).str[:3].value_counts()
            for k, v in vc.items():
                rows.append(dict(profile=pf, aggregation=agg, verdict_head=k, objects=int(v)))
    rp.h(2, '1. 政策判定串计数（判定串顺序 c、d、f、正向门槛、e资本、e随机、size(profile)）')
    rp.table(pd.DataFrame(rows), {'主体': '政策表全部对象', '单位': '个数', '子集': 'profile × 聚合 × 判定串前缀'}, 'E6M-P3-COUNTS')
    rp.h(2, '2. 生产变更候选清单（只列，不授权：deployment_authorized = false；新路线 replacement NOT_AUTHORIZED）')
    col = 'policy_PROPOSED_PORT3_T_FULL' if 'policy_PROPOSED_PORT3_T_FULL' in P.columns else 'policy_result'
    passed = P[P[col].astype(str).str.startswith('通过')]
    keep = [c for c in ('desc_id', 'block', 'operator', 'param', 'alpha', 'memory', 'parent', 'H', 'FULL', 'G4', 'FULL_sc', 'years_pos', 'e_rand',
                        'size_PROPOSED_PORT3_T', 'evidence_exposure', 'historical_exposure', 'replacement_status', 'deployment_authorized') if c in P.columns]
    rp.table(passed[keep], {'主体': '正式尺子通过对象', '单位': '年化百分点', '子集': col, '资本视图': 'FULL_sc 并列'}, 'E6M-P3-CANDIDATES', maxrows=60)
    rp.h(2, '3. 边缘清单（全部条件距离）')
    edge = [c for c in P.columns if c.startswith('edge_')]
    if edge:
        E = P[['desc_id'] + edge].copy()
        E['min_margin'] = E[edge].min(axis=1)
        rp.table(E.sort_values('min_margin').head(60), {'主体': '最靠近政策边界的 60 个对象', '单位': '各条件距离（年化百分点 / 年数 / 百分点）'}, 'E6M-P3-EDGES', maxrows=60)
    A = csv(os.path.join(os.path.dirname(a.policy), 'policy_additions_E6m.csv'))
    if A is not None:
        rp.h(2, '4. 三句加法（只对原生四测量 + SM）')
        rp.table(A, {'主体': '六形态', '子集': 'profile × 聚合'}, 'E6M-P3-ADDITIONS')
    B = csv(os.path.join(os.path.dirname(a.policy), 'bootstrap', 'simultaneous_band_q95.csv'))
    if B is not None:
        rp.h(2, '5. 同时带（共享 draw；JOINT_BAND / JOINT_BAND_NOT_ESTIMABLE / COMMON_ESTIMABLE_SUBFAMILY）')
        rp.table(B, {'主体': '登记比较', '单位': 'SE 单位（q95_maxabs_t）'}, 'E6M-P3-BAND')
    return rp.write('E6m_REPORT_part3.md'), rp.tables


# ====================================================================== mechanisms
def mechanisms(a, dev):
    rp = start('mechanisms', a, 'E6m REPORT mechanisms —— 四账户、MATCH_CAP、Δgross 三项、T 桥与 B4–B6 读法', dev)
    F = cat(os.path.join(a.decomp or '', 'four_account_%s.csv')) if a.decomp else None
    if F is not None and 'I_ann_pp' in F.columns:
        rp.h(2, '1. 四账户（逐日闭合后段均；中位数只描述，不相加）')
        G = F[F.status == 'COMPUTED'].groupby(['route', 'metric', 'segment']).agg(objects=('object', 'count'), I_median=('I_ann_pp', 'median'),
                                                                                R_median=('R_ann_pp', 'median'), X_median=('X_ann_pp', 'median'),
                                                                                total_median=('total_ann_pp', 'median'), closure_max=('closure_maxabs', 'max'),
                                                                                y00_minus_parent_median=('y00_minus_parent_ann_pp', 'median')).reset_index()
        rp.table(G, head('四账户', 'I / R / X', '路线 × 口径 × 段'), 'E6M-MECH-4ACC')
    K = cat(os.path.join(a.decomp or '', 'cap_decomp_%s.csv')) if a.decomp else None
    if K is not None:
        rp.h(2, '2. MATCH_CAP 对称分解（两边有仓：单位资本效果 + 资本变化；单边 / 真空 / 无编辑 / 缺失分开）')
        cols = [c for c in K.columns if c.endswith('_segavg')] + ['closure_maxabs']
        rp.table(K.groupby('segment')[cols].median().reset_index(), head('全部非父对象（中位）', 'CAP 分解', '段'), 'E6M-MECH-CAP')
    Wc = cat(os.path.join(a.decomp or '', 'weight_change_%s.csv')) if a.decomp else None
    if Wc is not None:
        rp.h(2, '3. Δgross 三项（新增 / 消失 / 共同重定权；主 72）')
        rp.table(Wc, head('主 72', '三项', '对象 × 段'), 'E6M-MECH-WCHG', maxrows=80)
    Tb = cat(os.path.join(a.decomp or '', 'trefit_%s.csv')) if a.decomp else None
    if Tb is not None:
        rp.h(2, '4. T 重估桥（冻结源 T 系数 − 完整重估）')
        rp.table(Tb, head('T 桥对象', '冻结 − 重估', '对象 × 段'), 'E6M-MECH-TREFIT', maxrows=80)
    for nm, fn, qid, sub in (('5. B4 事件窗贡献（W1 / W2）', 'b4_event_contrib_detail.csv', 'E6M-MECH-B4EV', 'B4 对象 × 窗口'),
                             ('6. B4 SYMDEC（频率 / 状态内 / 单边，严格加回段间差）', 'symdec_detail.csv', 'E6M-MECH-SYMDEC', 'B4 对象 × 段对 × 状态变量'),
                             ('7. B4 签名 4（月度净超额 ACF1 与波动；逐年只作低精度附列）', 'b4_sig4_detail.csv', 'E6M-MECH-SIG4', 'B4 对象')):
        X = csv(os.path.join(a.b4 or '', fn)) if a.b4 else None
        if X is not None:
            rp.h(2, nm)
            rp.table(X, head(sub, 'B4', sub), qid, maxrows=40)
    for nm, pat, qid, sub in (('7a. B4 签名 1（入场后 j 日累计超额：子 / 父 / 差，按形成年；第一天份额；账户锚；定义用户授权代拟，L-S3）', 'b4_sig1_%s.csv',
                               'E6M-MECH-SIG1', 'B4 对象 × 年 × j'),
                              ('7b. B4 签名 2（持仓 60 日平均两两相关 raw / 剔市场与同业；对同日 pool0 分层匹配随机 1,024 条；真实 − 随机不是资金流入的观测；'
                               'formation_days_in_year 与 days 之差 = 段首历史不足的日；L-S3）', 'b4_sig2_%s.csv', 'E6M-MECH-SIG2', 'B4 对象 × 年'),
                              ('7c. B4 签名 3（保留 / 剔除 / 新增的 Q / K / size 价差与其后 H 日收益价差，按形成年；价差变窄不等于被套利推平；L-S3）',
                               'b4_sig3_%s.csv', 'E6M-MECH-SIG3', 'B4 对象 × 年')):
        X = cat(os.path.join(a.b4 or '', pat)) if a.b4 else None                   # 定义 = registration/delegated_decisions_E6m_S.json（用户授权代拟）
        rp.h(2, nm)                                                                # 标题总写（限制编号的引用不随输入缺失消失；S11）
        if X is None:
            rp.p('缺（e6m_b4_sig 未跑；SOURCE_WAIT）。')
        else:
            rp.table(X, head(sub, 'B4', sub), qid, maxrows=60)
    for nm, pat, qid in (('8. B5b 删除预算', 'b5_delete_budget_%s.csv', 'E6M-MECH-B5B'), ('9. B5 形成日状态账本', 'b5_state_ledger_%s.csv', 'E6M-MECH-B5L')):
        X = cat(os.path.join(a.b5 or '', pat)) if a.b5 else None
        if X is not None:
            rp.h(2, nm)
            rp.table(X, head(nm[3:], 'B5', '对象 × H × 段'), qid, maxrows=40)
    X = cat(os.path.join(a.b6 or '', 'b6_trigger_ledger_%s.csv')) if a.b6 else None
    rp.h(2, '10. B6 退出潜力（只做已声明的反事实读法；费用为上界代理，L-S6；骨架无段列的汇总约定见 L-S11）')
    if X is None:
        rp.p('缺（e6m_b6_accounts 未跑；SOURCE_WAIT）。')
    else:
        rp.table(X, head('B6 对象', '触发 × 早退', '对象 × 触发 × 段'), 'E6M-MECH-B6', maxrows=40)
    X = cat(os.path.join(a.b5 or '', 'b5_state_clock_%s.csv')) if a.b5 else None
    rp.h(2, '11. 状态时钟账本（state_clock_ledger：形成状态 gross / 日历 Vol3 净差 / 执行日 Vol3 费用差 + STRICT250；E6l 三时钟移植，L-S5）')
    if X is None:
        rp.p('缺（e6m_b5 clock 未跑；SOURCE_WAIT）。')
    else:
        rp.table(X.groupby(['clock', 'status']).size().reset_index(name='rows'), {'主体': 'B4 的 78 个对象 + 段级 STRICT250', '单位': '行数',
                                                                                   '子集': '时钟 × 状态'}, 'E6M-MECH-CLOCK-STATUS')
        cl = X[pd.to_numeric(X.get('closure_max_abs_decimal'), errors='coerce').notna()] if 'closure_max_abs_decimal' in X.columns else X.iloc[:0]
        if len(cl):
            rp.table(cl.groupby(['segment', 'clock']).closure_max_abs_decimal.max().reset_index(), {'主体': '闭合（FORMATION：Σ 状态 = 账户 gross；'
                     'SUM_CHECK：Σ 贡献 = FULL 日均）', '单位': '小数（日）', '子集': '段 × 时钟'}, 'E6M-MECH-CLOCK-CLOSURE')
        cn = X[(X.clock == 'CALENDAR_NET') & (X.state != 'SUM_CHECK')]
        if len(cn):
            rp.table(cn.groupby(['segment', 'state'])[['share', 'contribution_ann_pp', 'conditional_mean_ann_pp']].median().reset_index(),
                     head('B4 对象（中位，只描述不相加）', 'Δnet8 按 u 日 Vol3', '段 × 状态'), 'E6M-MECH-CLOCK-NET', maxrows=40)
    rp.h(2, '12. 附属第 7 项源理论连续链（carry = 段首接续上一段记忆状态，reset = 各段冷启动；子 / 父 / C1 / HG / LAG 参照同样连续；L-S2）')
    P = csv(os.path.join(a.cont, 'continuous_panel_E6m.csv')) if a.cont else None
    if P is None:
        rp.p('缺（e6m_s_continuous 未跑；SOURCE_WAIT）。')
    else:
        for nm_, fn_ in (('锚 i（reset 门 / 名单 = 名单阶段位图）', 'anchor_masks_E6m.csv'), ('锚 ii（原父单段 pnl_nb = 主账户 net8）', 'anchor_ledger_E6m.csv')):
            A_ = csv(os.path.join(a.cont, fn_))
            if A_ is not None:
                rp.table(A_.groupby('status').size().reset_index(name='rows'), {'主体': nm_, '单位': '行数'}, 'E6M-MECH-CONT-%s' % fn_.split('_')[1].upper())
        cols = [c for c in ('carry_minus_reset_ann_pp', 'D_cont_carry_minus_cont_parent_ann_pp', 'D_seg_main_ann_pp', 'cont_carry_minus_seg_self_ann_pp',
                            'boundary40_carry_minus_reset_ann_pp') if c in P.columns]
        rp.table(P.groupby(['path', 'segment'])[cols].median().reset_index().assign(owners=P.groupby(['path', 'segment']).size().values),
                 head('138 个 owner（中位，只描述不相加）', 'carry / reset / 连续父 / 分段主账户', '记忆通道 × 段', base='连续父（同样拼接）'), 'E6M-MECH-CONT',
                 maxrows=40)
        B_ = csv(os.path.join(a.cont, 'boundary_facts_E6m.csv'))
        if B_ is not None and 'init' in B_.columns:
            bc = [c for c in ('carried_U', 'lost_U', 'new_cols_without_state', 'final_carry_minus_reset_cells', 'days_with_final_diff') if c in B_.columns]
            rp.table(B_[B_.init == 'CARRY'].groupby('segment')[bc].median().reset_index(), {'主体': '段首接续（CARRY 行，中位）', '单位': '名 / 列 / 格 / 日'},
                     'E6M-MECH-CONT-BOUNDARY')
    return rp.write('E6m_REPORT_mechanisms.md'), rp.tables


# ====================================================================== b3 / carried / cards / e7
def b3(a, dev):
    rp = start('B3', a, 'E6m REPORT B3 —— 条件信息（N8 先行结果，锚过后并入）', dev)
    st = jload(M.P('stageN', 'B3_anchor_status_S.json'))
    rp.p('锚判定：%s' % ('未判定' if st is None else json.dumps({k: st[k] for k in ('verdict', 'evidence', 'labels', 'written_at')}, ensure_ascii=False)))
    if not st or st.get('verdict') != 'ANCHOR_PASSED':
        rp.p('锚未通过：B3 数值不读、不并入（ANCHOR_PENDING / ANCHOR_FAILED 见上）。')
        return rp.write('E6m_REPORT_B3.md'), rp.tables
    for nm in ('b3_cells', 'b3_mirror_cvr', 'b3_mirror_gap', 'b3_pairs', 'b3_random'):
        X = csv(os.path.join(a.b3 or '', '%s.csv' % nm)) if a.b3 else None
        if X is not None:
            rp.h(2, nm)
            rp.table(X, {'主体': nm, '单位': '每 h 基点（bp_per_h）', '标签': 'COMPUTED_BEFORE_ANCHOR, ANCHOR_PASSED'}, 'E6M-B3-%s' % nm.upper(), maxrows=60)
    return rp.write('E6m_REPORT_B3.md'), rp.tables


def carried(a, dev):
    rp = start('carried', a, 'E6m REPORT carried —— 承接锚（E6k / E6l 同构对象）、P44 核与 HG / LAG 身份', dev)
    for nm, pat in (('A2-4 / A2-2 / A2-3 / A2-5 源锚', M.P('stage0_S', 'c2_c4', 'checks_engine_*.csv')), ('A3 真实结构 = mock', M.P('stage0_S', 'c3', 'checks_structid_*.csv'))):
        fs = sorted(glob.glob(pat))
        if fs:
            X = pd.concat([csv(f, dtype=str) for f in fs], ignore_index=True)
            rp.h(2, nm)
            rp.table(X.groupby(['item', 'status']).size().reset_index(name='rows'), {'主体': nm, '单位': '行数'}, 'E6M-CAR-%s' % nm[:4].replace(' ', ''))
        else:
            rp.h(2, nm)
            rp.p('检查表缺（SOURCE_WAIT）。')
    for nm, p in (('P44（mock）', M.P('stage0_S', 'mock', 'p44_grid.csv')), ('P44（真实结构）', M.P('stage0_S', 'c3', 'p44_grid.csv'))):
        X = csv(p)
        rp.h(2, nm)
        if X is None:
            rp.p('缺（SOURCE_WAIT）。')
        else:
            rp.table(X, {'主体': 'SA 网格 vs BAND_Q', '单位': '名单格差'}, 'E6M-CAR-P44%s' % ('M' if 'mock' in p else 'R'), maxrows=40)
    Q = csv(os.path.join(a.queries or '', 'E6M-Q01-a.csv')) if a.queries else None
    if Q is not None and 'D_ann_pp' in Q.columns:
        rp.h(2, 'HG10 与 LAG1_10 各自身份（W09：撤回"LAG1_10 作记忆族代表、HG10 别名"）')
        rp.table(Q.groupby('segment').agg(comparisons=('comparison_id', 'count'), median_D_ann_pp=('D_ann_pp', 'median'),
                                          share_pos=('D_ann_pp', lambda x: float((pd.to_numeric(x, errors='coerce') > 0).mean()))).reset_index(),
                 head('Q01 HG10 − LAG1_10', '配对差', '段', base='同 α / H 的 LAG1_10'), 'E6M-CAR-Q01')
    rp.h(2, '沿用的 E6l 固定表：memory_age_daily（逐日门层记忆事实，L-S4）与 state_clock_ledger（三时钟，L-S5）')
    for nm in ('memory_age_daily', 'state_clock_ledger'):
        X = csv(os.path.join(a.fixed, '%s.csv' % nm)) if a.fixed else None
        if X is None:
            rp.p('- %s：缺（固定表未生成；SOURCE_WAIT）。' % nm)
        else:
            rp.table(X.groupby('status').size().reset_index(name='rows'), {'主体': nm, '单位': '行数', '子集': '状态'}, 'E6M-CAR-%s' % nm.upper())
    return rp.write('E6m_REPORT_carried.md'), rp.tables


def cards(a, dev):
    rp = start('cards', a, 'E6m cards —— 18 张卡的绑定、预测、判别、反解释、更新规则与 query 读数（不写判词）', dev)
    K = csv(M.P('registry', 'cards_stageB_E6m.csv')) if os.path.exists(M.P('registry', 'cards_stageB_E6m.csv')) else csv(M.P('stageS_dev', 'registry_b', 'cards_stageB_E6m.csv'))
    Qr = M.read_csv_keep(M.P('registry', 'query_registry_E6m.csv'), dtype=str)
    t13 = csv(os.path.join(a.stats or '', 'cards_t13_deriv_E6m.csv')) if a.stats else None
    for r in K.itertuples():
        rp.h(2, '%s %s' % (r.card, r.title))
        rp.p('- 预测：%s\n- 判别：%s\n- 反解释：%s\n- 更新：%s\n- 绑定视图：%s；query：%s' % (r.t02_prediction, r.t04_discriminator, r.t09_counter, r.t10_update,
                                                                           r.contrast_views, r.query_ids))
        if t13 is not None:
            x = t13[t13.card == r.card]
            if len(x):
                rp.p('- ⑬ MDE80（推导段，只是列、不作门）：%s' % '；'.join('%s：%s（中位 %.3f 年化百分点）' % (s, l, float(m))
                                                                   for s, l, m in zip(x.segment, x.t13_label, x.mde80_median_ann_pp)))
        rows = []
        for q in Qr[Qr.card == r.card].itertuples():
            X = csv(os.path.join(a.queries or '', '%s.csv' % q.query_id)) if a.queries else None
            if X is None:
                rows.append(dict(query_id=q.query_id, schema=q.schema, rows=0, status='SOURCE_WAIT'))
                continue
            d = dict(query_id=q.query_id, schema=q.schema, rows=len(X), status=json.dumps(X.status.value_counts().to_dict(), ensure_ascii=False))
            if 'D_ann_pp' in X.columns:
                v = pd.to_numeric(X.D_ann_pp, errors='coerce')
                d.update(median_D_ann_pp=float(v.median()), share_pos=float((v > 0).mean()))
            rows.append(d)
        rp.table(pd.DataFrame(rows), {'主体': '%s 的 query' % r.card, '单位': '年化百分点（COMPARISON）'}, 'E6M-CARD-%s' % r.card)
    return rp.write('E6m_cards.md'), rp.tables


def e7(a, dev):
    rp = start('E7', a, 'E6m E7 准备页（E7 HOLD：不读 2026-03-27 之后任何行情）', dev)
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    rp.p('用途：plan §11.3。只列 E7 若开启时要读的对象与统计；本轮不做任何 E7 读法、不设"E7 ≥ 推导 × .5"之类门槛（brief A1-8 已撤销）。数据截止 %s。' % M.MARKET_DATA_END_MAX)
    rp.table(D.groupby(['block', 'exposure']).size().reset_index(name='objects'), {'主体': '登记描述符', '单位': '个数', '子集': '块 × 暴露'}, 'E6M-E7-OBJ')
    rp.p('E7 开启需要：用户授权 + 新数据截止日登记 + E7 守卫改版（e6j_core.MARKET_DATA_END_MAX）+ 同一冻结清单 sha。')
    return rp.write('E6m_E7_prep.md'), rp.tables


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['r0', 'part2', 'part3', 'mechanisms', 'b3', 'carried', 'cards', 'e7', 'all'])
    ap.add_argument('--stats', default='')
    ap.add_argument('--policy', default='')
    ap.add_argument('--decomp', default='')
    ap.add_argument('--b4', default='')
    ap.add_argument('--b5', default='')
    ap.add_argument('--b6', default='')
    ap.add_argument('--b3', default='')
    ap.add_argument('--aux', default='')
    ap.add_argument('--queries', default='')
    ap.add_argument('--cont', default='', help='附属第 7 项连续链目录（results/full/continuous）')
    ap.add_argument('--fixed', default='', help='固定表目录（reports/fixed_full）')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    t0 = time.time()
    a.out = a.out or M.P('reports')
    dev = gate(a, [a.stats, a.policy, a.decomp, a.b4, a.b5, a.b6, a.queries, a.cont, a.fixed])
    fns = dict(r0=r0, part2=part2, part3=part3, mechanisms=mechanisms, b3=b3, carried=carried, cards=cards, e7=e7)
    todo = list(fns) if a.task == 'all' else [a.task]
    outs = []
    for t in todo:
        p, tabs = fns[t](a, dev)
        outs += [p] + tabs
        print('%s → %s（%d 表）' % (t, M.san(M.rel(p)), len(tabs)), flush=True)
    M.write_receipt(os.environ.get('E6M_TASK', 'S_reports_%s' % a.task), outs, status='SUCCEEDED', code=[__file__, M.__file__], dev_synthetic=dev,
                    wall_s=round(time.time() - t0, 1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
