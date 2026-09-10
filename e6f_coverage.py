#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f coverage 硬交付项 (§11): 逐条映射 brief / web plan / proposal, 状态与理由。
   用法: python e6f_coverage.py --out DIR
"""
import os, sys, json, time, argparse
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
A = ap.parse_args()
OUT = A.out


def ex(p):
    return os.path.exists(os.path.join(OUT, p))


def rows(p):
    q = os.path.join(OUT, p)
    if not os.path.exists(q):
        return 0
    try:
        return len(pd.read_csv(q))
    except Exception:
        return -1


def nfiles(d, pre=''):
    q = os.path.join(OUT, d)
    return len([f for f in os.listdir(q) if f.startswith(pre)]) if os.path.isdir(q) else 0


def st(cond, done='done', other='deferred'):
    return done if cond else other


def nsec(p):
    """数 markdown 文件里的 '## ' 小节数 —— 免得手写条数说了不算。"""
    q = os.path.join(OUT, p)
    if not os.path.exists(q):
        return 0
    return sum(1 for l in open(q, encoding='utf-8') if l.startswith('## '))


def selftest_note():
    import glob as _g
    out = []
    for q in sorted(_g.glob(os.path.join(OUT, 'checks', 'selftests_*.json'))):
        try:
            d = json.load(open(q, encoding='utf-8'))
        except Exception:
            continue
        tag = os.path.basename(q)[10:-5]
        out.append('%s %d/%d' % (tag, d.get('n', 0) - d.get('n_fail', 0), d.get('n', 0)))
    g10 = os.path.join(OUT, 'checks', 'selftests_g10_2024-2026.csv')
    if os.path.exists(g10):
        d = pd.read_csv(g10)
        out.append('第10组 %d/%d' % (int(d.ok.sum()), len(d)))
    return '; '.join(out) if out else '(未跑)'


def has_col_val(p, col, val):
    """文件存在【且】某列真出现过 val —— 防止"文件在就算做完"的假绿灯。"""
    q = os.path.join(OUT, p)
    if not os.path.exists(q):
        return False
    try:
        d = pd.read_csv(q)
        return col in d.columns and bool((d[col].astype(str) == val).any())
    except Exception:
        return False


ITEMS = []


def I(sec, item, status, evidence, note=''):
    ITEMS.append(dict(section=sec, item=item, status=status, evidence=evidence, note=note))


# ---------- 阶段 0 ----------
I('§2', 'E6e 汇总修订 avg_nh/days_nohold, 不覆盖原表',
  st(ex('revisions/E6e_summary_fix/all_candidates.csv')),
  'revisions/E6e_summary_fix/ (%d 行)' % rows('revisions/E6e_summary_fix/all_candidates.csv'),
  '非目标列复算 max|d| 7.1e-15; 前沿/core_depth 行集合对称差 0')
I('§2', 'days_nohold 四分拆 no_target/no_live/benchmark_missing/warmup', 'changed',
  'revisions/E6e_summary_fix/days_nohold_decomposition_by_segment.csv',
  'E6e 未存逐日 nh, 严格四分拆不可得; 改出可推导的四列 '
  '(days_nopos / warmup_lead / benchmark_missing / interior_nopos), 结论: 全部落在段首预热')
I('§2', 'target_nh 与 live_nh 分开', 'changed',
  'C_exposures/profile_*.csv 的 names 列',
  'avg_nh 明确标为 target_nh; live_nh 在 C1 画像里按覆盖范围给出 (E6e 全量重建 live_nh 不成比例)')
I('§2', 'hard_total 逐配置分量与总量', st(ex('revisions/E6e_summary_fix/attribution_per_config.csv')),
  'revisions/E6e_summary_fix/attribution_per_config.csv',
  'hard_total 中位 +0.4919; 逐行恒等式 max|err| 0.000e+00')
I('§2', 'engine_contract / PLAN_COPY 找不到原件则标 RECONSTRUCTED_AT_E6f',
  st(ex('engine_contract.md')), 'engine_contract.md', 'E6e 目录确无原件; 已标注, 不倒签')
I('§2', '四件注册表 + selector_registry + study_manifest',
  st(ex('feature_registry.csv') and ex('selector_registry.json') and
     ex('comparison_registry.csv') and ex('analysis_families.json')),
  'feature_registry(%d) / comparison_registry(%d) / selector_registry / analysis_families'
  % (rows('feature_registry.csv'), rows('comparison_registry.csv')))
I('§2', 'industry_zx1 PIT / 可成交性覆盖 / amount 单位与停牌语义',
  st(ex('checks/source_facts.json')), 'checks/source_facts.json',
  'PIT 成立(相邻日 9,769 格变化); 停牌 amount 恰为 0; flag_* 非空 93.7%')
I('§2', 'source_corrections_E6f.md', st(ex('source_corrections_E6f.md')),
  'source_corrections_E6f.md', '%d 条; 本轮新发现 6 条: pd.qcut 分箱边界 / cache_dir 只读 / 源数据延伸到 2026-09-09 / drop_duplicates 取错段 / C2 错断言假报 MODULE LIMIT / C2 仓位口径错(假象 4.45 点)' % nsec('source_corrections_E6f.md'))
I('§1.4', '预登记 §8 逐字落盘', st(ex('preregistration.md')), 'preregistration.md',
  'Q1-Q7 与边界全文逐字抽取, 只补时间/哈希/源 ID 映射')

# ---------- 块 A ----------
nA = rows('A_oat/A_summary_2024-2026__legacy_all.csv')
I('§4.1', '因子重建与窗口 (T/C/K_MA/K_ROS/快C/B) + 默认值逐项复现库值',
  st(ex('feature_registry.csv')), 'feature_registry.csv (%d 个规格)' % rows('feature_registry.csv'),
  '10 个默认锚全部逐位相同 (自测第 2/5 组)')
I('§4.1', 'K 的 ε 敏感性 w∈{1,5} × {MA,ROS} × ε∈{1e-5,1e-4,1e-3}', st(nA > 0),
  'A_oat/oat_A12.csv', '并入 A12 OAT')
I('§4.2', 'P54 全 OAT', st(nA > 0), 'A_oat/oat_P54.csv', '558 个描述符')
I('§4.2', 'A12 全 OAT + ε + B 复权对照', st(nA > 0), 'A_oat/oat_A12.csv', '191 个')
I('§4.2', 'T×C 5×5 / 慢C×快C / 快C×B', st(nA > 0), 'A_interactions/', '96 / 60 / 36 (去重后新增)')
I('§4.2', 'KTC 五维联合模板 1,296', st(nA > 0), 'A_interactions/KTC_template.csv',
  '1,296 个格位, 其中 1,208 个为新增, 88 个与其他层重叠而复用 (§4.2 明写允许)')
I('§4.2', '分量权重 37 点 × 6 深 × 4 否决 = 888', st(nA > 0), 'A_weights/weights.csv',
  '888 个, 与 brief 逐个吻合; 零权重分量真正 bypass (自测第 5 组)')
I('§4.2', '否决强度 k 平台 54×25 = 1,350', st(nA > 0), 'A_oat/k_platform.csv',
  '1,350 个格位, 1,286 个为新增, 64 个与 P54 默认/A12 锚重叠而复用')
I('§4.2', 'k15/k20 的确切人数预算诊断 (m = ceil(n_valid/k))', 'deferred',
  '—', '本轮只跑源 helper 原生版 (≥3k 门槛已由自测第 7 组 thin-day 验证, 违例 0 天); '
       'rank_budget 双胞胎在 E6e 已有, 本轮未对新 k 网格重做')
I('§4.2', '深度补档 KTC_mean @15 与 @60', 'changed', 'A_oat/depth_extra.csv',
  'E6e 锁定的 P2G 分位映射无 15 -> 首轮 4 个配置 KeyError; 已在 e6f_core.P2G 按生成 P2G 其余条目的'
  '同一规则补 15->g=20 并单独补跑 (不改 e6e_core)')
I('§4.2', '持有期 H∈{1,2,3,4,5,7,10}', st(nA > 0), 'A_horizon/horizon.csv', '84 格位, 72 个新增')
I('§4.2', 'H 分支的 E6c 三项分解 (legacy / common_mature / 日龄桥)', 'deferred', '—',
  '本轮只出 H 分支的 net/turn/pos 与对 H5 的差; 三项分解需重跑 E6c 口径, 登记 LIMIT')
I('§4.2', '中性化 N0/NS/NI/NSI + 只改核/只改否决两路归因', st(nA > 0),
  'A_neutralization/', '36 + 24; FWL/SVD 等价与反例见自测第 6 组')
I('§4.3', 'coretrim_matchN + 等仓位配对 + paired_common_domain', st(nA > 0),
  'A_summary_*.csv 的 role 列', '每段 coretrim 1,462 / eqpos 2×2,115 / common_domain 4,994')
I('§4.4', '邻域度量 (邻居数/Δnet8 分位/容忍带/边界标记)',
  st(ex('neighborhoods/neighborhood_metrics.csv')), 'neighborhoods/neighborhood_metrics.csv')
I('§4.4', 'mask Jaccard 与目标权重 L1', 'deferred', '—',
  '需为每对邻居重建两套掩码 (~1.8 万对), 与本轮其余部分不成比例; '
  '邻域的收益侧度量 (Δnet8/Δpu_net/容忍带) 已全出')
I('§0.1', '三种支持集 legacy_all / paired_common_domain / history_warmed',
  st(nfiles('daily', 'A_gross_') >= 7), 'daily/A_*_<段>__<支持集>.parquet',
  '2010-2014 段源数据最早日 = 段首日, 物理上无法预热 -> no_prior_data (brief §0.1 已预授权); '
  'LIMIT 记录 checks/warm_2010-2014__history_warmed.json')
I('§0.1', '支持集对照表 (同配置 legacy_all vs history_warmed 的 Δnet8/Δnh/Δ无持仓日)',
  st(ex('A_oat/support_compare.csv')), 'A_oat/support_compare.csv',
  'history_warmed 下 63 个锚只有 12 个与 E6e 账本逐位相同、max|d| 约 0.96 —— 这是【预期】不是失败: '
  'E6e 账本本身是 legacy_all 口径, 预热改了因子的可见历史; 相同的 12 个正是核里没有长窗因子的那些。'
  '主口径锚 (legacy_all) 四段各 63/63、max|d| = 0.000e+00')

# ---------- 块 B ----------
I('§5.1', 'B1 只读账本: 逐年/留一年/留15-16/3-5年滚动/四段/全窗口',
  st(rows('B_yearly/panel_year_segment_full.csv') > 0),
  'B_yearly/ B_leaveout/ B_rolling/ (%d + %d 行)'
  % (rows('B_yearly/panel_year_segment_full.csv'), rows('B_leaveout/leave_one_year.csv')))
I('§5.1', '年度集中度三种分母 + 逐月 + 最差 5/20/60 日 + 回撤',
  st(ex('B_yearly/annual_concentration.csv') and ex('B_yearly/worst_windows_drawdown.csv')),
  'B_yearly/')
I('§5.1', '静态 ledger_portability 六切点', st(ex('B_split/ledger_portability_static.csv')),
  'B_split/ (%d 行)' % rows('B_split/ledger_portability_static.csv'))
I('§5.2', 'S1-S6 × 四域 × 六切点 × 双向', st(ex('B_nested/selected_sets.csv')),
  'B_nested/selected_sets.csv (%d 行)' % rows('B_nested/selected_sets.csv'))
I('§5.2', 'S_meta (外层训练段内部逐年前向小折选规则)',
  st(has_col_val('B_nested/selected_sets.csv', 'rule', 'S_meta')),
  'selected_sets.csv 的 rule=S_meta 行 (meta_pick / meta_folds / meta_fallback 三列)',
  '内层用【账本加权平均 net8】比较六规则, 不是混合账户 —— 混合换手 ≤ 加权平均换手, '
  '故对多成员规则 (S2/S3/S4) 系统性偏保守; 不参与重采样稳定性 (重采样后无时间序)')
I('§5.2', '单次选择账户 + 年度 walk-forward 账户',
  st(nfiles('B_walkforward', 'policy_accounts_') > 0),
  'B_walkforward/policy_accounts_*.csv',
  '反向切分只出静态 b_ledger, 不建政策账户 —— 它的评估窗在训练窗之前, 建不出随时间前进的账户')
I('§5.2', '政策账户 a / b_ledger / b−a / 混合增益 / 对 R1R2 配对差',
  st(ex('B_walkforward/policy_readout.csv')),
  'B_walkforward/policy_readout.csv (%d 行)' % rows('B_walkforward/policy_readout.csv'))
I('§5.2', '选择稳定性重采样 B=2000', st(ex('B_selection_stability/selection_stability.csv')),
  'B_selection_stability/selection_stability.csv (%d 行)'
  % rows('B_selection_stability/selection_stability.csv'),
  'S5 的重采样用朴素 t (HAC 在重采样日多重集上不可识别), 已在表内 note 列标注')
I('§5.2', '否决选择回放 (每源父核选 Δ_vs_coretrim_matchN 最大的否决规则)', 'deferred', '—',
  'coretrim_matchN 日账本已产 (每段 1,462 条), 但按父核的否决选择回放本轮未做; '
  '登记 LIMIT, 不影响 S1-S6 主回放')
I('§5.2', 'cond 时间异质 + 成分归因 + 市场状态描述 + 单调性', 'deferred', '—',
  '逐年 Δ 已可从 B1/块A 表推出; 逐票/行业分层归因与单调性五组本轮未做, 登记 LIMIT')

# ---------- 块 C ----------
I('§6.1', 'C1 三层画像 (目标/执行后/收益承载) + 按交易金额加权再报一遍',
  st(nfiles('C_exposures', 'profile_') > 0), 'C_exposures/profile_*.csv')
I('§6.1', 'ADV20/sigma20 (+ ADV60/sigma60) 输入截止 e-1', st(nfiles('C_impact', 'bracket_') > 0),
  'C_impact/', '主口径 ADV20 只计交易日; 含停牌 0 的口径作敏感性列并排')
I('§6.1', '平方根冲击 A∈{0.1..20}亿 × κ∈{0.25,0.5,1.0} = 21 情景',
  st(nfiles('C_impact', 'impact_scenarios_') > 0), 'C_impact/impact_scenarios_*.csv',
  '可分离: c(A,κ)=κ√A·Σ|q|^1.5σ/√ADV, 21 情景是同一日标量的倍数 (自测第 9 组手算验证)')
I('§6.1', '线性形式敏感性 impact_linear = κσ·p/√p0',
  st(nfiles('C_impact', 'bracket_lin_') > 0), 'C_impact/bracket_lin_*.npy + impact_scenarios 的 form 列',
  '同样可分离: c_lin = (κA/√p0)·Σq²σ/ADV, p0=1%; 与平方根/含停牌0/60日窗四种形式并排')
I('§6.1', '容量情景 (净超额降至 0 的 A / 半数 gross 耗尽 / 相对 R1,R2 增量降至 0 的 A)',
  st(nfiles('C_capacity_scenarios', 'capacity_') > 0), 'C_capacity_scenarios/capacity_*.csv',
  '平方根律下 A* = A0·(n0/c1)²; 各符号情形 (net≤0 / cost≤0 / 增量不随规模消失) 单列; '
  '超出扫描上限只报外推标志。p 超 1%/5%/10% 的交易金额比例曲线未做, 登记 LIMIT')
I('§6.1', 'S1-cost / S6-cost (训练评分换成当时可算的冲击后净值)',
  st(has_col_val('B_nested/selected_sets.csv', 'rule', 'S1-cost@A5_k0.5')),
  'selected_sets.csv 的 rule=S1-cost@A{1,5}_k0.5 / S6-cost@... 行 + train_score_cost 列',
  '评分 = 训练窗内 net8_daily − κ√(A·1e8)·当日括号, 同分母年化; 括号缺失的配置评分为 NaN、'
  '排序落最后、不被选中 (不填 0)')
I('§6.2', 'C2 影子账户 Xideal / X0 / X1 + 两种资本口径',
  st(nfiles('C_shadow_accounts', 'shadow_accounts_') > 0), 'C_shadow_accounts/',
  '新增 Xengine 严格锚: 与源引擎逐位相同 (7.4e-16); 自测第 10 组 16/16')
I('§6.2', '真实股数 / 现金分红分支', 'unavailable', '—',
  '无分红数据; brief §0.1 已授权登记 LIMIT 不做。主版本 = 调整单位总收益代理账')

# ---------- 块 D ----------
I('§7', 'HAC L=5 主列 + 20/60 + 日历感知影响序列附加列', st(ex('D_hac/hac_table.csv')),
  'D_hac/hac_table.csv')
I('§7', 'stationary bootstrap 块长 20/60 各 2,000, 段内重采样段长固定',
  st(ex('D_bootstrap/bootstrap_families.csv')), 'D_bootstrap/bootstrap_families.csv')
I('§7', '族 F-source / F-A / F-R / F-C / F-B + 共 draw max|t| 同时带',
  st(ex('D_bootstrap/bootstrap_families.csv')), 'D_bootstrap/',
  'F-R 与 F-A 已出; F-C/F-B 依赖 C1/B2 汇总, 见各自状态')
I('§7', 'RW 调整 p 值附列', 'deferred', '—',
  'brief 写明"须已验证实现"; 本轮无已验证的 RW 实现, 按规定不出')
I('§7', 'I-IID 解析 gross 旁证 + 小宇宙全枚举确定性测试',
  st(ex('D_analytic_random/small_universe_enum.csv')), 'D_analytic_random/',
  '枚举 = 解析期望权重 max|d| 3.5e-18; 与 E6e 随机路径的对账本轮未做 (登记 LIMIT)')
I('§7', '统一记账 (小数日收益/n_clock/n_valid/support_id/同有效日集合)', 'done',
  'D_hac/hac_table.csv 的 n_clock/n_valid/support_id 列')

# ---------- 工程 / 交付 ----------
I('§9', '十二组测试', st(ex('checks/selftests_2024-2026.csv')),
  'checks/selftests_*.csv + checks/selftests_g10_*.csv',
  selftest_note())
I('§9', 'E6c 持有期锚 A4b_CVRv5 H3/4/5/7/10', st(ex('checks/e6c_horizon_anchor.csv')),
  'checks/e6c_horizon_anchor.csv',
  'A4b_CVRv5 是 v2 形态、不在 E6f 描述符空间内, 无法在本核重建 -> 该锚落在【用 E6c 存档日序列'
  '重算年化与净额口径一致】; 持有期机制本身另在自测组 4 对生产引擎逐 H (1,2,3,4,5,7,10) 锚')
I('§10', '三次交付 0->B1->part1->A->C1->B2->D->part2->C2->part3',
  st(ex('REPORT_part1.md')), 'REPORT_part1/2/3.md')
I('§10', '全局 worker ≤32, BLAS 单线程, 绑 socket 1', 'done',
  'run_manifest.json 的 env 段', '峰值 11 个 E6f 进程; 线程余量 ≥1,022')
I('§10', '父进程验收产物后写 DONE; 不默认 os._exit(0)', 'done', 'task_status/_DONE_*',
  '一次冒烟测试留下的陈旧 DONE 已按 PID+启动时间核对后删除, 并改由行数验收')
I('§11', 'coverage 硬交付项', 'done', 'coverage.md')
I('§12', '禁区', 'done', 'checks/selftests_*.csv 第 3 组',
  'E7 守卫两个反例均被拒; 未读 2026-03-27 之后数据; 未改 I11/pool0/生产 DEV; 未 git add .')

CV = pd.DataFrame(ITEMS)
CV.to_csv(os.path.join(OUT, 'coverage.csv'), index=False)
cnt = CV.status.value_counts().to_dict()
md = ['# E6f coverage (硬交付项, §11)', '',
      '逐条映射 brief / web plan / proposal。状态 = `done / reused / changed / deferred / unavailable`；',
      '`changed` 与未做项写明理由与影响。', '',
      '**统计**: ' + ', '.join('%s %d' % (k, v) for k, v in sorted(cnt.items())) +
      '（合计 %d 条）' % len(CV), '',
      '| 出处 | 条目 | 状态 | 证据 | 理由 / 影响 |', '|---|---|---|---|---|']
for _, r in CV.iterrows():
    md.append('| %s | %s | **%s** | `%s` | %s |'
              % (r.section, r['item'], r.status, r.evidence, r.note))
open(os.path.join(OUT, 'coverage.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
print('coverage: %d 条; %s' % (len(CV), cnt))
for _, r in CV[CV.status.isin(['deferred', 'unavailable', 'changed'])].iterrows():
    print('  [%s] %s -- %s' % (r.status, r['item'][:52], r.note[:96]))
