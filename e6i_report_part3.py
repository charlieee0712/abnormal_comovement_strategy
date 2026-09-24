#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i REPORT_part3 (Stage 4 合并复盘; brief §9 / §14 / §15) 生成器。
读: part2 面板 (reports/part2_tables/descriptor_panel_post.csv)、carried/summary/ (C1 / C2)、reports/hypothesis_outcomes.json、
research_catalog_v36.csv、factor_iteration_delta.csv、R0 query_ids、e6i_part3_static (Q16 条目 / 全轮 coverage)。
全部数字现算带 query_id; 每张表十项表头; 禁用词 / 主机地址扫描。另写 registry/coverage.csv。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_report_part1_text as TX
import e6i_part3_static as PS

R = I.RES
CS = os.path.join(R, 'carried', 'summary')
TAB = os.path.join(R, 'reports', 'part3_tables')
PRIM = TX.PRIM
q, f, pc, md, sgn = TX.q, TX.f, TX.pc, TX.md, TX.sgn_word
ALLD = '四段（2010-01-04..2026-03-27；推导两段 + 后段两段，段间不拼接）'


def hdr(op, denom, bench, subset, **kw):
    kw.setdefault('dates', ALLD)
    return TX.hdr(op, denom, bench, subset, **kw)


def rd(p, **kw):
    return pd.read_csv(p, low_memory=False, **kw)


def c1_section(w):
    t3p, t4p, t5p, t2p = (os.path.join(CS, x) for x in ('C1_T3_contrasts.csv', 'C1_T4_bridges.csv', 'C1_T5_instrument.csv',
                                                          'C1_T2_strict.csv'))
    w('## 2. Q10 C1：人数 N x 行业宽度 B（plan §9.1）\n')
    if not os.path.exists(t3p):
        w('_（C1 汇总缺失）_\n')
        return {}
    t3a = rd(t3p)
    t3m = rd(os.path.join(CS, 'C1_T3_contrasts_min60.csv'))
    t3a.to_csv(os.path.join(TAB, 'C1_contrasts_all.csv'), index=False)
    t3m.to_csv(os.path.join(TAB, 'C1_contrasts_min60.csv'), index=False)
    t2 = rd(t2p)
    fz = t2[(t2.scope == 'frozen') & (t2.alloc == 'equal')]
    w('**支持**：严格交叉对每个被比较的格对取两格同日都可行的交易日（plan §9.1）；推导段 pool0 较小，N ≥ 150 或 B = 8 的格多数日子行业容量不足。'
      '报告口径（不按结果取舍）：逐 seed 共同可行日 < 60（约 3 个月）视为支持不足、不进均值；全量口径另存 `part3_tables/C1_contrasts_all.csv`。%s。\n' % q(
          'Q10-SUPPORT', '各 (段, 对比, 固定维) 的共同可行日均值：' + '；'.join('%s %s %s %.0f 天' % (
              r_.segment, r_.contrast, r_.fixed, r_.common_days_mean) for r_ in fz.itertuples())))
    main_ = t3m[(t3m.scope == 'frozen') & (t3m.alloc == 'equal')]
    g = main_.groupby(['segment', 'contrast', 'fixed']).agg(n_cells=('mean', 'size'), mean_of_means=('mean', 'mean'),
                                                            cells_pos=('mean', lambda x: int((x > 0).sum())),
                                                            seeds=('n_seed', 'sum'), common_days=('common_days', 'mean')).reset_index()
    w(hdr('格内逐 seed 配对差（后一端 − 前一端）的均值，再在格间汇总（格 = 母体 x 深度 q）', 'C1 严格交叉中共同可行日 ≥ 60 的 seed x 格',
          '同一 seed、同一分配、同一母体与深度下对比的另一端', '评分口径 frozen（完整 pool0 冻结中性化排名）x 分配 equal（容量受限近似等人数）',
          dates='四段各自', H='源持有（母体原生）', support='两格同日都可行的交易日（逐 seed ≥ 60 天）'))
    w(md(g))
    out = {}
    for ctr in ('B16−B8', 'N250−N100'):
        x = main_[main_.contrast == ctr]
        out[ctr] = x.groupby('segment')['mean'].apply(lambda s: (s > 0).mean())
    w('%s。\n' % q('Q10-SIGN', '；'.join('%s：各段"格均值 > 0"的占比 %s' % (
        ctr, '，'.join('%s %s' % (s_, pc(v_)) for s_, v_ in sp.items()) or '无支持') for ctr, sp in out.items())))
    nm = main_[main_.contrast == 'N250−N100'].groupby('segment')['mean'].mean()
    bm = main_[main_.contrast == 'B16−B8'].groupby('segment')['mean'].mean()
    if len(nm):
        w('- **读法**：在有充分支持的段，固定行业宽度时人数从 100 到 250 的差（%s）在方向与幅度上都大于固定人数时行业从 8 到 16 的差（%s）——'
          '在这套抽样与评分机制下，可选池变大带来的账户改善主要来自"人数多"，行业宽度的作用小且不稳定。推导段支持不足（尤其 2010-14），'
          '这一分离主要来自 2019–2026。只识别"改变 N / B 的账户差异"，不识别历史真实扩容的原因。\n' % (
              '，'.join('%s %s' % (s_, f(v_)) for s_, v_ in nm.items()), '，'.join('%s %s' % (s_, f(v_)) for s_, v_ in bm.items())))
    if os.path.exists(t4p):
        t4 = rd(t4p)
        t4.to_csv(os.path.join(TAB, 'C1_bridges.csv'), index=False)
        t4['N'] = t4['N'].astype('Int64')
        b = t4[t4.scope.isin(['frozen', 'source'])].groupby(['segment', 'part', 'N'], dropna=False).net8_mean.median().unstack(
            'part').reset_index()
        w(hdr('桥：各 (段, N) 下三母体 x 四深度的 net8 年化中位（randomN 先对 64 seed 取均值）', 'C1 桥全部格',
              'bridge_full = 完整 pool0 同一计数预算；mother_source = 源母体', 'frozen 口径',
              dates='四段各自', H='源持有（母体原生）'))
        w(md(b))
    if os.path.exists(t5p):
        t5 = rd(t5p)
        t5.to_csv(os.path.join(TAB, 'C1_instrument.csv'), index=False)
        w('%s——计数预算与源分箱的差单列为"仪器效应"，不计入 N / B 的经济解释。\n' % q(
            'Q10-INSTR', '仪器效应（计数预算 − 源分箱，frozen，R2 / A06）各段中位：' + '，'.join(
                '%s %s' % (s_, f(v_)) for s_, v_ in t5.groupby('segment')['mean'].median().items())))
    return out


def c2_section(w, P):
    t6p = os.path.join(CS, 'C2_T6_impact_delta.csv')
    kp = os.path.join(CS, 'C2_children_delta.csv')
    w('## 3. Q7 冲击视图（C2；plan §9.2）\n')
    if not os.path.exists(t6p):
        w('_（C2 汇总缺失）_\n')
        return None
    t6 = rd(t6p)
    t6.to_csv(os.path.join(TAB, 'C2_impact_delta.csv'), index=False)
    cols = [c for c in t6.columns if c.startswith('d_net8_minus_sqrt_A5')]
    show = ['segment', 'route_id', 'd_net8_ann'] + cols
    g = t6.groupby(['segment', 'route_id'])[['d_net8_ann'] + cols].median().reset_index()
    w(hdr('路线内 (母体, H) 格的描述符中位，再对格取中位', 'C2 全部子描述符（推导两段 + 后段两段）', '同 H 真实母体（同一冲击情景下的母体）',
          '无冲击 vs 平方根冲击 A = 5 亿元、κ ∈ {.25, .5, 1}', dates='四段各自', H='各描述符自身 H',
          cost='8bp + 平方根冲击 MI = κ·σ·(Q/ADV)^0.5（源模型；κ 未校准）'))
    w(md(g[[c for c in show if c in g.columns]]))
    res = None
    if os.path.exists(kp):
        K = rd(kp)
        k = K[(K.route_id == 'RK') & K.direction_role.isin(PRIM) & (K.policy == 'FALLBACK')]
        c5 = 'd_net8_minus_sqrt_A5_k0.5'
        c10 = 'd_net8_minus_sqrt_A10_k1'
        kk = k.groupby('segment')[['d_net8_ann'] + [c for c in (c5, c10) if c in k.columns]].median()
        res = kk
        w('%s。' % q('Q7-KIMPACT', 'K 主方向（FALLBACK）子 − 母体（全部 H 的中位）：' + '；'.join('%s 无冲击 %s、A5 亿 κ.5 %s、A10 亿 κ1 %s' % (
            s_, f(r_.d_net8_ann), f(r_.get(c5, np.nan)), f(r_.get(c10, np.nan))) for s_, r_ in kk.iterrows())))
        kh = k.groupby(['segment', 'H'])[['d_net8_ann', c10]].median().unstack('segment')
        kh.columns = ['%s %s' % (a_.replace('d_net8_minus_sqrt_A10_k1', 'A10κ1').replace('d_net8_ann', '无冲击'), b_)
                      for a_, b_ in kh.columns]
        kh = kh.reset_index()
        kh.to_csv(os.path.join(TAB, 'C2_K_by_H.csv'), index=False)
        w(hdr('描述符中位', 'K 主方向 x SLOT FALLBACK（α .125 / .25 / .5）x 三母体', '同 H 真实母体（同一冲击情景）',
              '按 H：无冲击 vs 平方根冲击 A = 10 亿元、κ = 1', dates='四段各自', H='见行',
              cost='8bp + 平方根冲击（源模型；κ 未校准）'))
        w(md(kh))
        mo = rd(kp)[['segment', 'mother_id', 'H', 'm_net8_minus_sqrt_A10_k1']].drop_duplicates()
        short = k[k.H <= 3].groupby('segment')[c10].median()
        long_ = k[k.H >= 10].groupby('segment')[[c10, 'd_net8_ann']].median()
        mshort = mo[mo.H <= 3].groupby('segment').m_net8_minus_sqrt_A10_k1.median()
        w('- **读法**：%s。K 在冲击下的"更好"几乎全部集中在短 H——那里母体本身在大资金下已严重为负（不是可部署区域）；'
          '在母体仍可能为正的长 H，K 的增量与无冲击时接近。冲击透镜说明 K 会把持仓推向单位成交冲击较小的票，但 κ 未校准，不输出可部署规模。\n' % q(
              'Q7-KH', 'A10 亿 κ1 下：K 短 H（≤3）增量 %s，同口径母体短 H 净值 %s；长 H（≥10）增量 %s（无冲击 %s）' % (
                  ' / '.join(f(v_) for v_ in short), ' / '.join(f(v_, 1) for v_ in mshort),
                  ' / '.join(f(v_) for v_ in long_[c10]), ' / '.join(f(v_) for v_ in long_.d_net8_ann))))
        rl = K[K.route_id == 'RL']
        if len(rl) and c5 in rl.columns:
            rr = rl.groupby('segment')[['d_net8_ann', c5, c10]].median()
            w('%s。按价差代理替换边缘名单：中等冲击（A5 亿 κ.5）下 %d / %d 段为正，最重冲击（A10 亿 κ1）下 %d / %d 段为正——'
              '它省下的主要是冲击成本（减少交易 / 偏向低冲击票），不是信息 alpha（plan Q7 允许的结论只到"实施机会"）。'
              '删除类路线（RO / RV）在重冲击下转正也是同一个资本 / 交易量效应。\n' % (
                  q('Q7-RL', 'RL 子 − 母体：' + '；'.join('%s 无冲击 %s、A5 亿 κ.5 %s、A10 亿 κ1 %s' % (
                      s_, f(r_.d_net8_ann), f(r_[c5]), f(r_[c10])) for s_, r_ in rr.iterrows())),
                  int((rr[c5] > 0).sum()), len(rr), int((rr[c10] > 0).sum()), len(rr)))
    return res


def main():
    t0 = time.time()
    os.makedirs(TAB, exist_ok=True)
    TX.QIDS.clear()
    P = rd(os.path.join(R, 'reports', 'part2_tables', 'descriptor_panel_post.csv'))
    M = P[~P.companion.astype(bool) & P.route_id.isin(['RT', 'RK', 'RV', 'RR', 'RO', 'RC', 'RA', 'RS', 'RL', 'TPAIR', 'FOURARM'])]
    cards = json.load(open(os.path.join(R, 'reports', 'hypothesis_outcomes.json')))
    D = rd(os.path.join(R, 'reports', 'factor_iteration_delta.csv'))
    cat = rd(os.path.join(R, 'reports', 'research_catalog_v36.csv'))
    appr = json.load(open(I.APPROVAL_FILE))
    L = []
    w = L.append
    w('# E6i REPORT_part3（Stage 4：合并复盘 + carried + 全轮 coverage）\n')
    w('执行 session，%s（47 时间）；结果目录 `20260923_0254_E6i_measurement_need_fit`（47）。本报告合并推导段（part1a / 1b）与后段首次观察（part2），'
      '加 carried C1（人数 x 行业宽度）/ C2（冲击成本透镜）/ C3（信号边界描述，R0），给出 Q1–Q18 结果卡汇总、研究目录 v36、因子迭代增量、'
      '候选库更新提案、线状态与 park 草稿，以及全轮 coverage。记录 B：`%s`。**全部是研究历史上的读数，E7 是唯一 OOS（HOLD）**；'
      '采纳、线状态、入地基由规划 session 与用户定。\n' % (time.strftime('%Y-%m-%d %H:%M'), appr['approval_id']))
    w('---\n')
    SUM_AT = len(L)
    w('')
    # ============================ 1 四段合并
    w('## 1. 四段合并要点\n')
    g1 = M.groupby('route_id').agg(n=('descriptor_id', 'size'), deriv=('deriv', 'median'), post=('post', 'median'),
                                   all4=('all4', 'median'), ex1516=('ex1516', 'median'), ex2024p=('ex2024p', 'median'),
                                   all4_ci_pos=('ci_all4', lambda x: int((x.astype(bool) & (M.loc[x.index, 'all4'] > 0)).sum())),
                                   all4_ci_neg=('ci_all4', lambda x: int((x.astype(bool) & (M.loc[x.index, 'all4'] < 0)).sum()))).reset_index()
    g1.to_csv(os.path.join(TAB, 'T1_all4_route.csv'), index=False)
    w(hdr('路线内描述符中位 / 计数', '该路线全部主描述符', '同 H 真实母体', '主路线；deriv / post / all4 = 推导合并 / 后段合并 / 四段合并；ex1516 / ex2024p = 四段去 2015+16 / 去 2024+',
          H='全部登记 H'))
    w(md(g1))
    both = cat[(cat.deriv_median > 0.05) & (cat.post_median > 0.05)].sort_values('all4_median', ascending=False)
    both[['member_id', 'axis', 'family', 'n_primary_single', 'deriv_median', 'post_median', 'all4_median', 'post_ci_pos',
          'post_ci_neg', 'zmap_post_median', 'best_role_post']].to_csv(os.path.join(TAB, 'T1b_members_both_periods.csv'), index=False)
    w(hdr('成员层：主方向、单成员描述符的中位（与 factor_iteration_delta 同一规则）', '推导合并与后段合并中位都 > +0.05 的目录成员',
          '同 H 真实母体', '276 个目录成员中按两期结果筛出（**有成员层选择偏差**，只作描述，不作准入）', H='各描述符自身 H'))
    both = both.assign(**{c_: both[c_].astype('Int64') for c_ in ('n_primary_single', 'post_ci_pos', 'post_ci_neg')})
    w(md(both[['member_id', 'axis', 'family', 'n_primary_single', 'deriv_median', 'post_median', 'all4_median', 'post_ci_pos',
               'post_ci_neg', 'zmap_post_median', 'best_role_post']]))
    w('%s。这张表是从 %d 个成员里按两期结果筛出的，期望值会被高估（E6f 已示范按结果挑选的赢家诅咒）；它只用于决定"哪些对象值得在 E7 前事前登记"，'
      '不是"哪些对象已经有效"。\n' % (q('P3-BOTH', '两期都为正的成员 %d 个：%s' % (len(both), '、'.join(both.member_id))), len(cat[cat.ledger_status != 'considered_not_built'])))
    # ============================ 2 / 3 carried
    c1 = c1_section(w)
    c2 = c2_section(w, P)
    # ============================ 4 Stage 1 测量层
    w('## 4. Stage 1 测量层回顾（Q11 / Q12 / Q17 / Q18；R0）\n')
    rq = rd(os.path.join(R, 'reports', 'R0_tables', 'query_ids.csv')).set_index('query_id').text
    for qid, lab in (('Q-R0-Q11A', 'Q11 池子真实状态'), ('Q-R0-Q11B', 'Q11 触发日龄'), ('Q-R0-Q11C', 'Q11 实现 cr5'),
                     ('Q-R0-Q12A', 'Q12 限价政策（V）'), ('Q-R0-Q17B', 'Q17 条件形状'), ('Q-R0-Q18F', 'Q18 画像 vs 同人数对照'),
                     ('Q-R0-Q18A', 'Q18 T 新旧分离'), ('Q-R0-Q18B', 'Q18 K 新旧分离')):
        if qid in rq.index:
            w('- %s：%s〔%s〕' % (lab, rq[qid], qid))
    w('')
    # ============================ 5 Q16
    w('## 5. Q16 方法复盘（本轮实际发生的方法层问题）\n')
    t5 = pd.DataFrame(PS.Q16_ITEMS)
    w(hdr('逐条登记（事实 / 发现途径 / 影响 / 根因 / 下一步改法）', '本轮方法层问题', '无', '全轮', unit='不适用', dates='全轮',
          H='不适用', cost='不适用', support='不适用', capital='不适用'))
    w(md(t5))
    # ============================ 6 结果卡
    w('## 6. Q1–Q18 结果卡汇总（全文见 `reports/hypothesis_outcomes.md`）\n')
    ct = pd.DataFrame([dict(Q=c['hypothesis_id'], prediction_status=c.get('prediction_status'),
                            root_cause_evidence=c.get('root_cause_evidence')) for c in cards])
    w(hdr('逐卡', 'Q1–Q18', 'plan §10.2 模板', '全轮', unit='不适用', dates='全轮', H='不适用', cost='不适用', support='不适用',
          capital='不适用'))
    w(md(ct))
    w('%s。\n' % q('P3-CARDS', '结果卡状态计数：' + '，'.join('%s %d' % (k_, v_) for k_, v_ in ct.prediction_status.value_counts().items())))
    # ============================ 7 研究目录 / 因子迭代增量
    w('## 7. 研究目录 v36 与因子迭代增量\n')
    w('%s；每成员一行的构造版本 / 角色证据 / 失效归因（执行端规则化初判）见 `reports/factor_iteration_delta.md`，'
      '来源 / 定义 / 有效域 / 尝试 / 未测用途见 `reports/research_catalog_v36.csv`（%d 行，含考虑过未构造的项）。\n' % (
          q('P3-DELTA', '因子迭代增量状态计数：' + '，'.join('%s %d' % (k_, v_) for k_, v_ in D.status.value_counts().items())), len(cat)))
    # ============================ 8 / 9 提案与线状态
    w('## 8. 候选库更新提案（草案；全文 `reports/candidate_library_update_proposal.md`）\n')
    w('执行端的提案是**不向生产候选库加任何对象**；只提出一个"E7 事前登记短名单"（研究候选），每项写明改善对象、母体、角色、H / 成本、增益来源、'
      '时间与风险范围、剩余不确定性与所需验证。U34 / U35、生产 v2、v3 展示候选本轮不改。\n')
    w('## 9. 线状态与 park 台账（草稿；`reports/line_state_proposal.md` / `reports/park_ledger_delta.md`）\n')
    w('草稿只写"子杠杆 x 适用域"的否定，不写线级结论；定案权在规划 session 与用户。\n')
    # ============================ 10 / 11
    w('## 10. 这份 part3 没有得出的结论\n')
    w('- 不是 OOS：四段都是研究历史；E7 是唯一 OOS。')
    w('- 两期都为正的成员表有成员层选择偏差，不是"已有效"的名单。')
    w('- C1 的 N / B 对比只识别"在此抽样与评分机制下改变 N / B 的账户差异"，不识别历史真实扩容的原因；偏相关不作唯一机制。')
    w('- C2 的 κ 未校准，不输出可部署规模。')
    w('- "无效果"只对 母体 x 需求 x 角色 x 日期 x 支持 x 成本 的格成立。\n')
    w('## 11. 运行事件与 BLOCKERS\n')
    w('BLOCKERS：无。本轮运行事件与方法层问题见 §5 与 WORKLOG。\n')
    # ============================ 12 coverage
    w('## 12. 全轮 coverage（proposal / plan / brief 逐条）\n')
    c1_done = len(glob.glob(os.path.join(R, 'task_status', 'c1_*.receipt.json'))) > 0
    c2_done = len(glob.glob(os.path.join(R, 'task_status', 'c2_*.receipt.json'))) > 0
    cov = []
    for src, item, st_, why, imp in PS.COVERAGE:
        if 'C1：' in item and not c1_done:
            st_ = 'deferred'
        if 'C2：' in item and not c2_done:
            st_ = 'deferred'
        cov.append(dict(source=src, item=item, status=st_, reason=why, impact=imp))
    cv = pd.DataFrame(cov)
    I.atomic_write_csv(os.path.join(R, 'registry', 'coverage.csv'), cv)
    w(hdr('逐条状态', 'proposal / plan / brief 的交付与设计条目', '各自原文', '全轮', unit='不适用', dates='全轮', H='不适用',
          cost='不适用', support='不适用', capital='不适用'))
    w(md(cv))
    w('%s。\n' % q('P3-COV', 'coverage 状态计数：' + '，'.join('%s %d' % (k_, v_) for k_, v_ in cv.status.value_counts().items())))
    # ============================ 摘要
    k = M[(M.route_id == 'RK') & M.direction_role.isin(PRIM) & (M.policy == 'FALLBACK')]
    summ = [
        '1. 本轮（E6i：因子端迭代 · 估计量族 x 策略适配）完整跑完：推导段 → 记录 B（整表）→ 后段首次观察 → carried → 复盘。',
        '2. %s。' % q('P3-S-K', 'K 槽位（响应族部分混入）：推导合并 %s → 后段 %s / %s → 四段合并 %s' % (
            f(k.deriv.median()), f(k.p1.median()), f(k.p2.median()), f(k.all4.median()))),
        '3. %s。' % q('P3-S-NEG', '推导合并与后段合并中位都为负的路线：%s；后段合并中位低于推导合并的路线 %d / %d（%s），高于的：%s' % (
            '、'.join(r_.route_id for r_ in g1.itertuples() if r_.deriv < 0 and r_.post < 0),
            int((g1.post < g1.deriv).sum()), len(g1),
            '、'.join(r_.route_id for r_ in g1.itertuples() if r_.post < r_.deriv),
            '、'.join(r_.route_id for r_ in g1.itertuples() if r_.post > r_.deriv) or '无')),
        '4. %s——有成员层选择偏差，只用于 E7 事前登记的候选范围。' % q('P3-S-BOTH', '两期都为正的成员 %d 个（K 响应族 / 源桥与 T 20 日绝对尺度为主）' % len(both)),
        '5. 执行端提案：生产候选库不加对象；E7 事前登记短名单见 candidate_library_update_proposal.md。',
        '6. 结果卡：%s。' % '，'.join('%s %d' % (k_, v_) for k_, v_ in ct.prediction_status.value_counts().items()),
    ]
    if c1:
        summ.append('7. C1：%s（固定行业宽度时"人数多"的作用一致为正、行业宽度的作用小且不稳定；推导段支持不足；见 §2）。' % '；'.join('%s 格均值>0 占比 %s' % (ctr, '，'.join('%s %s' % (s_, pc(v_)) for s_, v_ in sp.items())) for ctr, sp in c1.items()))
    kp_ = os.path.join(CS, 'C2_children_delta.csv')
    if c2 is not None and os.path.exists(kp_):
        K_ = rd(kp_)
        kk_ = K_[(K_.route_id == 'RK') & K_.direction_role.isin(PRIM) & (K_.policy == 'FALLBACK') & (K_.H >= 10)]
        lg = kk_.groupby('segment')[['d_net8_ann', 'd_net8_minus_sqrt_A10_k1']].median()
        summ.append('8. C2：K 在重冲击下的增量集中在短 H（母体在大资金下已严重为负的区域）；%s（§3）。' % q(
            'P3-S-C2', '长 H（≥10）K 增量 A10 亿 κ1 下各段 %s，无冲击 %s' % (
                ' / '.join(f(v_) for v_ in lg.d_net8_minus_sqrt_A10_k1), ' / '.join(f(v_) for v_ in lg.d_net8_ann))))
    summ.append('%d. 不是 OOS；采纳、线状态、入地基由规划 session 与用户定；E7 HOLD。' % (len(summ) + 1))
    L[SUM_AT] = '## 摘要（≤15 行）\n\n' + '\n'.join(summ) + '\n\n---\n'
    txt = '\n'.join(L)
    bad = TX.check_headers(txt)
    if bad:
        raise SystemExit('生成 FAIL：%d 张表缺表头项（行 %s）' % (len(bad), bad[:10]))
    for b in TX.FORBID:
        if b in txt:
            raise SystemExit('生成 FAIL：禁用词 %s' % b)
    if re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', txt):
        raise SystemExit('生成 FAIL：疑似主机地址')
    p = os.path.join(R, 'reports', 'E6i_REPORT_part3.md')
    open(p, 'w', encoding='utf-8').write(txt)
    pd.DataFrame(TX.QIDS).to_csv(os.path.join(TAB, 'query_ids_part3.csv'), index=False)
    print('part3: %s (%d 字节, %d 行); query_id %d; %.0fs' % (p, len(txt.encode()), txt.count('\n'), len(TX.QIDS),
                                                              time.time() - t0))


if __name__ == '__main__':
    main()
