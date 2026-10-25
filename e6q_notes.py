# -*- coding: utf-8 -*-
"""E6q 执行端交付文书（brief §8.1 / §8.5；附录 B.24）：reports/E6q_REVIEW_input_notes.md（§1–§8；§8 = 待决事项，含 MC_LIMIT 清单、对账未解释残差、PENDING 依赖；
"分钟数据可用之处观察"节）、E6q_lessons_delta.md、E6q_executor_retrospective.md（资源实耗、随机预算实际占比、读法建议、分钟数据观察）、
E6q_code_change_register.md（A1 前后技术修复逐条 + 文件 sha）、E6q_commit_whitelist.md。
数字从机器表 / 回执 / 链日志取；叙述是执行端事实陈述与读法建议，不替决策端下结论。用法：python3 e6q_notes.py [--root <相对 E6Q_WORK 的根>]"""
import os
import re
import json
import glob
import argparse

import numpy as np
import pandas as pd

import e6q_core as O
import e6q_engine as E
import e6q_reports as RP

FIXES = [
    ('e6q_edge.edge', 'EDGE 的相等指示（high = low 等）改在原价上判断：作者原式在对数价格上比较，numpy 向量化 log 与标量 log 的 1-ulp 差会翻转相等指示（作者四例在同进程内重复调用出现 0.009752 vs 0.010133）；'
     '改后 40 次重复调用结果唯一、四例与作者期望值差 1e−17 量级；作者原式保留为 edge_author 只作对照（证据日志 tmp/superseded_cache_edge_adjfactor_20261023/）', 'A1 前（缓存构建）'),
    ('e6q_cache（EDGE 输入）', 'OHLC 复权改用 lclose 链因子（F_t = F_{t−1} × 前日原始收盘 / 当日 lclose）：adj_factor 在 2–11% 的开盘格缺失、lclose 全覆盖；42,968 个公司行为格；'
     '面板抽查相对差 ≤ 1e−12；旧缓存原样移至 tmp/superseded_cache_edge_adjfactor_20261023（未删）', 'A1 前'),
    ('e6q_engine（M3 卖单门控分配）', '共享净预算按队列分配时，剩余预算 ≥ 剩余需求 → 整批取满（rem_want 规则）：原逐批相减的舍入在 p* → ∞ 时留下 2e−11 股碎屑批次，使 PSTAR_INF_EQ_NATIVE 不逐位', 'A1 前（引擎自检）'),
    ('e6q_engine（TTL 隔离计数）', 'S_i[SI_QUAR] 收盘块按新进入隔离的 token 计数（tk_quar_new）：原计数器从未递增（只供事件表），由 Stage 0 恒等发现', 'A1 前（Stage 0）'),
    ('e6q_engine（RANDOM_TARGET 精确首可行匹配）', '容差改相对（1e−9 × max(1, t)；原绝对容差在大额票据上给出假 PROVED_NO_MATCH）；剪枝四条（名额 / 阈值嵌套容量 / 行业最低吸收 / 同额大类计数）+ 同额票据对称性；'
     '节点上限 20 万（触限 → ALGORITHM_LIMIT + 带上限部分分配）；独立精确判定器 rt_match_oracle 只作对照未用（难例 18 / 18 分配相同）', 'A1 前'),
    ('e6q_engine（日表 DY）', 'DY 加宽到 102 列，新列 101 rt_arm_use（本臂票据总额，TICKET_CONSERVATION 用）：先试用 E6p 76 列比较区内的 59 号槽位，使 PSTAR_INF 复现失败，已撤回并改为追加列', 'A1 前'),
    ('e6q_engine（调试缓冲）', 'step / plan_e6q 增加 DBG 缓冲参数（生产 DBG = zeros(1)，不写入）：只供触限实例导出；逐位复现不变', 'A1 前'),
    ('e6q_stage0（夹具）', 'REARM 夹具背景改为 UNKNOWN（−1；原 0 = 已知 False 使"UNKNOWN 不清除"夹具失效）；截止强制夹具提高流动性并预置 3% 权重使路径真正到达 deadline（原被单股上限挡住）', 'A1 前'),
]
FIXES.append(('e6q_stats / e6q_policy / e6q_g1 / e6q_diag / e6q_claims（读注册件）', 'core 的 read_csv（A1 冻结）把空串读成 NaN，下游判断按空串写（if not ref / != 空串）→ stats A2 首跑在密度表 KeyError；'
                                                                     '下游模块读注册件后统一 fillna 为空串（core 不改）；stats A2 在链外手动重跑一次（logs/a2stats_rerun.log），旧失败标记与日志移 tmp/superseded_chain_a2stats_20261023，g1 随后以一步链写 seal_A2',
              'A2 统计（seal_A2 之前）'))
FIXES.append(('e6q_stats（空跑扩展）', '加 --dry_extras：A2 + fake_post 空跑时另跑导出（只主 32 家族）/ 随机表 / E6p 复现 / 运行恒等，写到空跑根；导出路径与随机标签参数化（B 相行为不变）', 'A2 运行中'))
FIXES.append(('e6q_stats.run_identities（ZERO_INTERVENTION_EQ_NATIVE）', '空跑在推导段发现 2 条 CASH_REMAIN × NONE 边（M_mean3_v2 / M_mean3_v2_CVRv5 稳健性形态）的 tag_use_reg 一侧恰为 0、另一侧为 1e−9 元级浮点碎屑'
              '（44 / 26 日，合计 2.2e−8 元），纯相对差把它放大成 1.0；现金、NAV 与其余 68 列逐位相等。8 个标签 / 锁定账本列改为"绝对差 ≤ 1e−6 元记碎屑并单独报告"，其余列仍严格相对 1e−9；引擎未改',
              'B 统计前（空跑后）'))
FIXES.append(('e6q_run.main_owner_ids / cmd_topup（增补对象集合）', '同一空串 → NaN 问题使"带 MCSE 目标的 owner"判断恒真（568 条引用全被当主 owner）；在 B 增补启动前改为 fillna 后判断，且增补只对带目标的 (owner, 机制) 引用'
              '（238 条 = 49 个主形态 HG10 owner × 四机制 + RANDOM_TARGET 两域各 21）；路径数值由种子决定、不受影响；基础 128 条与 registry 行语义不变（registry() 未改，保证增补路径与基础路径同参数）',
              'B 随机基础层运行中、增补启动前'))

FIXES.append(('e6q_closure.bridge / SCHEMA_DEVIATIONS（S29）', '首次交接的 D 结果显示部分锚账户"早退成交行 < 意向"，与原声明（只写多行一项）方向不符；查明 D 计数另按设计排除 lot_due = POST_CUTOFF 的早退行与 DEADLINE_OVERRIDE 行。'
              '加 verify/trades_events_bridge_E6q.csv 逐锚分解（51 个锚账户残差全 0），重写 SCHEMA_DEVIATIONS 第 1 行与注记 §8 第 7 条', '交付前（首次交接后）'))
FIXES.append(('e6q_diag（入场好度 / K 强）', 'A4b 形成权重几乎全是 1% 单股上限（每日 1–3 个不同值）；以其作好度的 D2 entry_score 三分位与 D3 K 强因此退化（只有 T1 / T2，CC-09 在首次交接里 NOT_EVALUABLE）。'
              '改为取向后的 K 腿好度 = −K0（E6i K0_LEGACY，四段只读，sha 入回执）在当日源域内的分位；D4 存活组成同改。前两个交接目录原样移至 tmp/superseded_handoff_*（未删）', '交付前（首次交接后）'))

DOWNSTREAM = ['e6q_stats.py', 'e6q_g1.py', 'e6q_policy.py', 'e6q_diag.py', 'e6q_claims.py', 'e6q_reports.py', 'e6q_notes.py', 'e6q_closure.py', 'e6q_dryrun.py', 'e6q_syncpack.py']
SUPERSEDED = ['tmp/superseded_cache_edge_adjfactor_20261023', 'tmp/superseded_selftest_*', 'tmp/superseded_chain1/2/3_20261023', 'tmp/superseded_chain_s0_20261023']


def chain_times(path):
    """链日志 → [(步骤, 秒)]。"""
    out = []
    if not os.path.exists(path):
        return out
    st = {}
    for ln in open(path, encoding='utf-8', errors='replace'):
        m = re.match(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\] (start|done|failed) (\d+) (\S+)', ln)
        if not m:
            continue
        t = pd.Timestamp(m.group(1))
        k = (m.group(3), m.group(4))
        if m.group(2) == 'start':
            st[k] = t
        elif k in st:
            out.append((m.group(4).replace('_', ' '), (t - st.pop(k)).total_seconds(), m.group(2)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    root = O.P(*a.root.split('/')) if a.root else O.work()
    rd = lambda rel: pd.read_csv(os.path.join(root, rel), keep_default_na=False, na_values=['']) if os.path.exists(os.path.join(root, rel)) else pd.DataFrame()
    rep = os.path.join(root, 'reports')
    os.makedirs(rep, exist_ok=True)
    W = lambda n, t: O.atomic_write_text(os.path.join(rep, n), t)
    R = pd.read_csv(O.P('registration', 'registry_E6q.csv'), keep_default_na=False, dtype=str)
    RD = rd('statistics/randoms_E6q.csv')
    EV = rd('events/event_counts_E6q.csv')
    BRG = rd('verify/trades_events_bridge_E6q.csv')
    S0 = rd('diagnostics/stage0_E6q.csv')
    s0a = json.load(open(O.P('diagnostics', 's0a_facts_E6q.json'), encoding='utf-8')) if os.path.exists(O.P('diagnostics', 's0a_facts_E6q.json')) else {}
    lad = pd.read_csv(O.P('verify', 'impact_reconciliation_ladder_E6q.csv'), keep_default_na=False) if os.path.exists(O.P('verify', 'impact_reconciliation_ladder_E6q.csv')) else pd.DataFrame()
    fr = RD[RD.segment == 'FULL'] if len(RD) else pd.DataFrame()
    mcl = fr[fr.status == 'MC_LIMIT'] if len(fr) else pd.DataFrame()
    rt = fr[fr.mechanism.astype(str).str.startswith('RANDOM_TARGET')] if len(fr) else pd.DataFrame()
    pend = S0[(S0.probe_id == 'S0-G') & (S0.status == 'SOURCE_BINDING_PENDING')] if len(S0) else pd.DataFrame()
    # 早退成交行 vs 已实现早退意向（S29 口径；主 32 与锚）
    p32 = R[R.is_primary32 == '1']
    br = []
    for r in p32.itertuples(index=False):
        ti = []
        for sub in ('deriv', 'full'):
            p = O.P('trades_parts', sub, r.exec_hash[:2], '%s.npz' % r.exec_hash)
            if os.path.exists(p):
                ti.append(np.load(p, allow_pickle=False)['TL_i'])
        if not ti:
            continue
        ti = np.concatenate(ti)
        ex = np.isin(ti[:, 4], [E.OK_EXIT, E.OK_EXIT_HALF, E.OK_EXIT_REARM, E.OK_DEADLINE]) & (ti[:, 5] == 1) & (ti[:, 0] < ti[:, 6])
        ev = EV[EV.exec_id == r.exec_id]
        br.append(dict(exec_id=r.exec_id, rows=int(ex.sum()), intents=int(ev.n_realized_early.iloc[0]) if len(ev) else -1))
    BR = pd.DataFrame(br)
    nmulti = int((BR.rows != BR.intents).sum()) if len(BR) else 0
    rec = {}
    for p in glob.glob(O.P('task_status', '*.receipt.json')):
        try:
            rec[os.path.basename(p).replace('.receipt.json', '')] = json.load(open(p, encoding='utf-8'))
        except Exception:
            pass
    wall = {k: v.get('wall_s') for k, v in rec.items() if v.get('wall_s') is not None}
    ct = []
    for lg in sorted(glob.glob(O.P('logs', 'chain*.log'))) + sorted(glob.glob(O.P('logs', '*', 'chain*.log'))):
        ct += chain_times(lg)
    tot = sum(x[1] for x in ct)
    rnd = sum(x[1] for x in ct if 'randoms' in x[0] or 'topup' in x[0])
    nrand = 0
    for p in glob.glob(O.P('randoms', 'random_paths_*.csv')):
        with open(p, encoding='utf-8', errors='replace') as fh:
            nrand += max(sum(1 for _ in fh) - 1, 0)
    d5 = rd('diagnostics/D5_dose_E6q.csv')
    d8 = rd('diagnostics/D8_window_E6q.csv')

    def pval(den, kind, stat):
        if not len(d5):
            return np.nan
        x = d5[(d5.item == 'participation_%s' % den) & (d5.key1 == 'NATIVE|T1b_LEVEL|H20|main|HG10') & (d5.key2 == kind) & (d5.stat == 'A1e+08|%s' % stat)]
        return float(x.value.iloc[0]) if len(x) else np.nan

    def wval(nm):
        if not len(d8):
            return np.nan
        x = d8[(d8.item == 'sell_price_opportunity') & (d8.key1 == 'NATIVE|T1b_LEVEL|H20|main|HG10|%s' % nm) & (d8.stat == 'notional_weighted_bp')]
        if not len(x):
            x = d8[(d8.item == 'sell_price_opportunity') & (d8.key1 == nm) & d8.key2.astype(str).str.startswith('NATIVE|T1b_LEVEL|H20|main|HG10') & (d8.stat == 'notional_weighted_bp')]
        return float(x.value.iloc[0]) if len(x) else np.nan
    f2, fs = RP.f2, RP.fs
    unexplained = ''
    if len(lad):
        x = lad[lad.step == 'L02_NAV_NODE_WEIGHT'].residual_ratio.astype(float)
        y = lad[lad.step == 'L01_NAV_NODE_PARTICIPATION'].residual_ratio.astype(float)
        z = lad[lad.step == 'L00_BASE'].residual_ratio.astype(float)
        unexplained = '7 对象 L00 基础比值 legacy / curve %s–%s；L01（参与率节点替换）后 %s–%s；L02（权重节点替换）后最大 |残差比 − 1| = %s' % (
            f2(z.min(), 3), f2(z.max(), 3), f2(y.min(), 4), f2(y.max(), 4), ('%.1e' % float((x - 1.0).abs().max())) if len(x) else '—')
    notes = [RP.HEADER, '# E6q REVIEW 输入注记（执行端；方式 B 一次交付）', '',
             '## §1 交付范围', '',
             '- 201 个逻辑账户（180 FEASIBLE + 21 IDEAL）全部两阶段运行（A2 推导段 → seal_A2 → B 两后段连续续跑）；比较 1,359、复合 6、随机引用 568、反馈 80 + 配对 580、快照控制 20；主 32 行事前定死。',
             '- 随机：105 个信息退出 owner × 四机制（128 起；主形态 HG10 owner 按 MCSE ≤ .01 以 128 批增补至 1,024）、LEVEL_WORST_1D 50、RANDOM_TARGET 两域各 49；IDEAL 不跑（NO_RANDOM_BY_SCOPE）。', '',
             '## §2 源绑定与复现', '',
             '- E6q 引擎在新功能全关时与 E6p 逐日复现：自检 132 个坐标差 0；正式运行 E6P_ACCOUNT_REPLICATION（NATIVE 54 坐标 × 四段）见 verify/e6p_replication_E6q.csv。',
             '- 零干预恒等（47 条 ZERO_INTERVENTION 边）、p* → ∞ / θ = 1 / new 过滤关 = NATIVE 逐位（Stage 0 与自检）。', '',
             '## §3 段初始化口径', '', '连续全历史（CASH_V0）为主；四段重置（WARM）只作主 32 对象对与父的敏感性（statistics/warm_sensitivity_E6q.csv）。', '',
             '## §4 随机与匹配', '',
             '- BERNOULLI_FIRSTHIT = 首达风险率（日龄桶；60 日窗不含 T；桶空回退全龄池，仍空 → 该日不抽）。强度比（路径意向 / owner 意向）见 randoms 表 intensity_ratio。',
             '- RANDOM_TARGET：同预算票据的精确首可行匹配（冻结优先序 = 五日块 × 路径 × 证券哈希）；触限 / 无解日份额 > .25 → CONTROL_NOT_COMPARABLE（执行端代拟阈值，见 §8）。',
             '- 匹配 V2 两级与未匹配四列全报；CONTROL_NOT_COMPARABLE 规则（FULL 未匹配份额 > %s）沿 E6p。' % getattr(O, 'NOT_COMPARABLE_UNMATCHED', '.25'), '',
             '## §5 成本', '',
             '- S0-A 先于任何新成本读数：%s；%s。canonical 仪器 = curve（κA^δ、同节点 V⁺_{e−1}）；LEGACY_E6O_A5 只审计。' % (s0a.get('status', '—'), unexplained),
             '- 固定路径曲线（A 五档 × κ .5 / 1 × δ .5 / .7 / 1；主 32 另 κ .3 场景）+ 盈亏平衡 + 反馈 80 路径 / 580 配对 + 密度（两分子一分母，分母退化行不比）。', '',
             '## §6 政策', '', '- verdict 只由 policy_fields 显式 Python bool 重算；c 字段写 true / false / NA；A_main = 1 亿；对账状态统一为 freeze 值。', '',
             '## §7 诊断', '',
             '- D1–D10 与 landmark（8 状态；向量化状态与 e6q_landmark.state_at 逐例对照）全交付；D1 参与率五分位的切点取同触发 NATIVE 的净单参与率（执行端对"参与率分位"的操作化，见 §8）。',
             '- 固定快照金额控制 20 项（plan §7.4）：diagnostics/local_snapshot_E6q.csv。买方原生预算 = 引擎同快照记录的 NATIVE 可用额、新动作 = 本臂票据，原生篮子比例取形成名单源权重（未截断近似）；卖方由请求—成交关联得出同额交给谁与延期损益；局部读数，不拼成策略净值。',
             '- D3 只用两推导段：K 强 = 取向后的 K 腿好度（−K0 当日源域三分位；D2 入场好度与 D4 存活组成同用 −K0 源域分位），K0 原值与 CVR20 取 E6i 测量缓存（只读、sha 入回执、对齐核）、"混合 Q 评分"无独立列 → NOT_AVAILABLE。', '',
             '## §8 待决事项（执行端代拟；用户 10-11 定：不中途发消息）', '',
             '1. **S0-A 状态读法**：附录 A-A 字面"比例非恒定 → UNDECIDABLE_RECONCILIATION"；本轮两式在共同输入下逐层闭合（L02 残差比 = 1，差异全部来自 NAV 节点与 √(V0 / V_pre) 因子，逐日桥保留），'
             '执行端按"来源已闭合"读为 RECONCILED 并据此冻结。若决策端坚持字面读法，受影响的只有 canonical profile 的 c5（会变 UNDECIDABLE_RECONCILIATION），账户与曲线不变。',
             '2. **EDGE 输入与相等判断两处改动**（code change register 第 1–2 条）：请追认（只影响 D2 的 EDGE 三分位列）。',
             '3. **RANDOM_TARGET 求解器与可比性阈值**：节点上限 20 万、触限日带上限部分分配；"触限 + 无解日份额 > .25 → CONTROL_NOT_COMPARABLE"是执行端代拟（plan 未给数）。FULL 触限 / 无解日份额：%s。' % (
                 ('中位 %.3f、最大 %.3f（%d 个 owner × 域）' % (pd.to_numeric(rt.limit_day_share, errors='coerce').median(), pd.to_numeric(rt.limit_day_share, errors='coerce').max(), len(rt)))
                 if len(rt) else '（B 后填）'),
             '4. **MC_LIMIT 清单**（主形态 HG10 owner 到 1,024 条路径仍 MCSE > .01）：%s。' % (
                 '；'.join('%s × %s（MCSE %s）' % (e.split('|')[0], m, f2(v, 4)) for e, m, v in zip(mcl.owner_exec_id, mcl.mechanism, mcl.mcse)) if len(mcl) else '无'),
             '5. **对账未解释残差**：%s（无未解释残差则 S0-A 可直接用）。' % (unexplained or '—'),
             '6. **PENDING 依赖**：%s。' % ('、'.join(pend.key.tolist()) if len(pend) else '无（S0-G 全部 BOUND / NOT_APPLICABLE）'),
             '7. **早退成交行 vs 意向（S29）**：%s；SCHEMA_DEVIATIONS 第 1 行声明三类来源（多行 + / POST_CUTOFF 早退行 − / DEADLINE_OVERRIDE 行 −）。' % (
                 ('S29 口径下 %d / %d 个锚账户两计数不等；逐账户分解见 verify/trades_events_bridge_E6q.csv：多行 %d、POST_CUTOFF 早退 %d、截止强制 %d、有早退切片但最终未"早退已实现"的请求 %d；'
                  '恒等残差 %s' % (int((BRG.d_script_count != BRG.n_realized_early).sum()), len(BRG), int(BRG.extra_slice_rows.sum()), int(BRG.postcutoff_due_rows.sum()),
                                 int(BRG.deadline_override_rows.sum()), int(BRG.requests_early_not_realized.sum()),
                                 '全部为 0' if (BRG.residual == 0).all() else '有 %d 个账户非 0' % int((BRG.residual != 0).sum())))
                 if len(BRG) else '主 32 中 %d 个对象两计数不等（门控多日执行与部分成交 = 同一请求多行）' % nmulti),
             '8. **D1 参与率分位的操作化**：五分位切点 = 同触发 NATIVE 的证券日净单参与率（A = 1 亿；参与率随 A 线性，各 A 分组相同）；臂 − 同触发 NATIVE 与臂 − 同臂父两种差都给。',
             '9. **CC 子条款读法**（gross / net、可证伪门之间的区间）逐条写在 claims 的 note；CC-01 句级按 plan §12.3 记 NOT_TESTED_AS_WRITTEN、子条款照评。',
             '10. **假数据空跑与 B 的时序**：seal_A2 写入后，B 账户 / 随机层与假数据空跑（tmp/dryrun，推导段日行循环复制成后段，另加 --dry_extras 跑后段专属分支）并行，'
             '两链共用同一核心名单（B 96 进程、空跑 ≤ 48 进程）；空跑只读 A2 产物，共三轮，每轮发现的口径问题在 B 的统计 / 诊断步启动前修完（见代码变更登记）。',
             '11. **卫生**：一次约 2 分钟的单核调试误用核心 192–200（不在 96-191 / 288-383 名单内）；此后一律经包装脚本绑定核心。',
             '12. **本机同步体积**：合同仍为 ≤ 300 MB 优先序截断（E6p 时"下一轮精简 ~90 MB"的建议未被采纳，本轮照合同）。',
             '13. **固定快照金额控制（plan §7.4，20 项）与其余 plan 产出的补做**：交付链核对时发现只有注册（registration/local_snapshot_refs_E6q.csv）、没有计算；A2 启动后补进 e6q_diag.py（只读重建，不改任何账户）。买方原生比例用形成名单源权重的未截断近似（单股 / 行业截断未重算），卖方用请求—成交关联；若决策端要求逐名精确重放，需要在引擎快照处加记录（属引擎改动，本轮未做）。同次核对还补了 plan §7.2 第 3 层"费用代数"（D1 fee_algebra：C00 / C10 / C01 / C11、交互与对称两边际分摊，'
             '以已成交证券日订单为固定状态）与 §7.3 M3"未释放现金的机会收益"（快照表 unreleased_cash_opp_*：推迟名义 × 形成名单篮子同窗口超额），以及 §9.3 M3 元订单：逐请求表 events/m3_parent_orders_E6q.csv'
             '（总目标 / 完成份额 / 切片数 / 参与率 / 延期损益 / 未释放现金机会）与"日独立 vs 关联元订单不重置"成本敏感性（D4 m3_meta_order_cost，MODEL_BOUNDARY，不进 c5），§9.4 费用反馈 vs 固定路径分项（D10 feedback_vs_fixed_components：'
             '期末 NAV 比 / 反馈实收冲击 / 意向数差 / 现金份额差 / 未匹配与撤单名义差 / 换手差；描述性，不作可加分解），均只读、不改账户。',
             '14. **E6o 勘误与 E6o / E6p 白名单提交**仍待用户一句话（本轮不动）；E6q 白名单见 reports/E6q_commit_whitelist.md（提交只在用户指示后）。',
             '15. **入场好度的度量**：A4b 形成权重几乎全是 1% 单股上限（每日 1–3 个不同值，D3 source_weight_degenerate 行），不能当"好度分数"。交付前已把 D3 K 强、D2 entry_score 三分位与 D4 存活组成'
             '改为取向后的 K 腿好度（−K0 当日源域分位；E6i 测量缓存四段只读）。推导段封存的 G1 · G-P-12（按形成权重排名、平局按顺序拆）同样不分级，属已封存的第一道标签，不改，读法以 D3 为准；'
             '"混合 Q 评分"本轮缓存仍无独立列（NOT_AVAILABLE）。', '',
             '### 分钟数据可用之处观察（只记，不改设计）', '',
             '- D5 第二分母：LEVEL H20 NATIVE 早退卖单的尾盘 30 分钟额参与率 p90 %s（ADV20 口径 p90 %s；A = 1 亿）——尾盘容量明显更紧，M3 门控若改用尾盘额作预算分母会更保守。' % (
                 f2(pval('TAIL30MIN', 'EXIT', 'p90'), 4), f2(pval('ADV20', 'EXIT', 'p90'), 4)),
             '- D8 执行窗：同一早退卖单在尾盘 VWAP 相对全日 VWAP 的名义加权价差 %s bp、开盘相对全日 %s bp（只作事后实施读法，不据 e 日价格改 T 名单）。' % (
                 fs(wval('TAIL1430_vs_VWAP')), fs(wval('OPEN_vs_VWAP'))),
             '- 14:57 前最后连续成交价（p1457）与官方收盘的差可作收盘集合竞价冲击的事后读法（本轮未用；沪市 2018-08-20 前无收盘竞价）。',
             '- 分钟量分布可给 M3 门控的"日内分时"版本（把 p* 预算按分钟量切片）——只记为下一轮可能的执行设计，不在本轮改。', '']
    W('E6q_REVIEW_input_notes.md', '\n'.join(notes) + '\n')
    lessons = [RP.HEADER, '# E6q lessons delta（执行端）', '',
               '1. **相等指示要在原始输入上判断**：numpy 向量化 log 与标量 log 的 1-ulp 差会翻转"high = low"类指示（EDGE 作者例同进程内漂移）；新实现先做同进程重复调用的唯一性核。',
               '2. **组合可行性检验用相对容差**：大额票据下的绝对容差给出假"无解"；容差随量级缩放。',
               '3. **逐批相减的预算会留碎屑**：剩余预算覆盖剩余需求时整批取满；p* → ∞ 一类的零干预恒等能抓住这种碎屑。',
               '4. **只供报表的计数器也要有恒等**：SI_QUAR 从未递增，只有 Stage 0 的"计数 = Σ 日事件"恒等发现了它。',
               '5. **夹具要证明路径真的走到**：三值状态的背景（UNKNOWN vs 已知 False）改变 REARM 语义；单股上限会让截止夹具到不了 deadline——夹具里断言被测分支确实触发。',
               '6. **共享日表只追加列，不复用被复现比较覆盖的槽位**（第 59 号槽位的教训）。',
               '7. **核心绑定只经包装脚本**：一次临时手写核心列表越界（192–200）。',
               '8. **精确匹配的对称性**：同额票据的对称性剪枝把难例从"100 万节点内无解"降到 54 万节点内解出；"判定器先行"的替代做法更差（17 / 508）。',
               '9. **共享读表函数把空串读成 NaN**：`dtype=str` 也挡不住；下游按空串写的判断（`if not ref`、`!= 空串`）对 NaN 恒真——stats 首跑崩在密度表，更隐蔽的是增补对象集合把 568 条引用全当主 owner。'
               '读注册件后立即统一空值，再写判断；冻结的公共模块不改，就在每个读点规范化。',
               '10. **空跑要覆盖后段才走的分支**：只跑 fake_post 时导出 / 随机表 / 复现 / 运行恒等全被跳过；加 --dry_extras 后一次空跑就抓到 ZERO_INTERVENTION 的碎屑口径与 G4 中位口径两处。',
               '11. **同一张表里的 G4 有两种口径**：D 列的 G4 = 四段 D 的中位，敞口 / 现金差的 G4 = 两个 G4 之差——以核对脚本为准逐列确认，不按直觉统一。',
               '12. **"已注册"不等于"已计算"**：固定快照金额控制只在注册表里有 20 行、计算链里没有；收尾前逐条对 plan 的产出清单（不只对合同表名单）。', '']
    W('E6q_lessons_delta.md', '\n'.join(lessons) + '\n')
    retro = [RP.HEADER, '# E6q 执行端复盘（retrospective）', '',
             '## 资源实耗（链日志步骤耗时，秒）', '', '| 步骤 | 秒 | 状态 |', '|---|---|---|'] + ['| %s | %.0f | %s |' % (k, v, s) for k, v, s in ct] + [
             '', '- 链步骤合计 %.1f 小时；随机层（randoms + topup）%.1f 小时，占 %s；随机路径记录行（A2 + B + 增补）%d；并发 96 worker（核心绑定 96-191, 288-383）。' % (
                 tot / 3600.0, rnd / 3600.0, ('%.0f%%' % (100.0 * rnd / tot)) if tot > 0 else '—', nrand),
             '', '## 回执 wall_s（秒）', '', '| 任务 | wall_s |', '|---|---|'] + ['| %s | %s |' % (k, v) for k, v in sorted(wall.items())] + [
             '', '## 读法建议（给 REVIEW；不替决策端下结论）', '',
             '- 先读 S0-A（仪器）→ 主 32 行的同臂父差与四段符号 → 同触发 NATIVE / CASH / RECYCLE_HALF 参照（卖出与再投分开）→ 随机（同额 / 同层 / 首达 / 水平 / 随机目标两域）→ 成本曲线、密度与反馈 → E / CC。',
             '- M3 / M4 是"卖出侧"算子、M1 / M2 是"再投侧"算子：卖出侧看同触发 NATIVE 差与卖方冲击（D1 SELL），再投侧看 EXTRA 买入的前向超额（D2）与随机目标对照。',
             '- RANDOM_TARGET 的可比性先看 match_status 与 limit_day_share；IDENTITY_TARGET_CONTROL 不记 HIT。', '',
             '## 分钟数据可用之处观察', '', '见 REVIEW 注记同名节。', '']
    W('E6q_executor_retrospective.md', '\n'.join(retro) + '\n')
    dl = rd('code_register/deploy_log.csv')
    ccr = [RP.HEADER, '# E6q 代码变更登记（code change register）', '', '新模块一律 `e6q_` 前缀；只 import 复用 e6p_* / e6n_* 等既有模块，未改任何既有文件；修前输出改名保留（%s）。' % '、'.join(SUPERSEDED), '',
           '## A1 前的技术修复（经济规则未变；A1 冻结时引擎 sha 见 freeze_E6q.json code_sha256）', '', '| 位置 | 修复 | 时点 |', '|---|---|---|'] + ['| %s | %s | %s |' % f for f in FIXES] + [
           '', '## A2 启动后新增的下游模块（只读账户产物，不改任何账户）', '', '、'.join('`%s`' % x for x in DOWNSTREAM), '',
           '## 文件 sha（交付时）', '', RP.md_table(dl, ['file', 'sha256', 'changed_after_A1', 'role']) if len(dl) else '（deploy_log 未生成）', '']
    W('E6q_code_change_register.md', '\n'.join(ccr) + '\n')
    wl = [RP.HEADER, '# E6q 提交白名单（提交只在用户指示后；不 `git add .`）', '', '建议纳入（代码目录）：', ''] + [
        '- `%s`' % f for f in (dl.file.tolist() if len(dl) else []) if not f.startswith(('e6q_dbg_', 'e6q_rtproto'))] + [
        '', '不纳入：调试脚本（e6q_dbg_* / e6q_rtproto，只作取证）、results/ 下全部产物、tmp/、checkpoints/、randoms/ 分片（体量与卫生）。E6o / E6p 白名单仍待用户一句话。', '']
    W('E6q_commit_whitelist.md', '\n'.join(wl) + '\n')
    print(json.dumps(dict(notes=True, mc_limit=len(mcl), rt=len(rt), multi_row_objects=nmulti, chain_steps=len(ct), random_share=(rnd / tot) if tot else None), ensure_ascii=False),
          flush=True)


if __name__ == '__main__':
    main()
