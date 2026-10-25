# -*- coding: utf-8 -*-
"""E6o 读法注 / 限制登记 / 复盘 / 经验 / 代码登记 / 提交白名单（brief §8 第 1、5、7 条）。数字由机器表刷新。用法：python3 e6o_notes.py"""
import os
import sys
import json
import glob
import time

import numpy as np
import pandas as pd

import e6o_core as O
import e6o_reports as RP

HDR = RP.HDR
PURPOSE = {
    'e6o_core.py': '公共常量、路径、原子写（只写本轮结果目录）、缓存命名空间',
    'e6o_source.py': '源层抽取：E6n 名单 → 源 DEV → P_SOURCE 逐位复现；T1a 生产否决合同面板；自然门 U；NEXT 候选序',
    'e6o_panels.py': '全程日频面板（后复权 VWAP / 收盘、基准、可卖 / 可买、日 CVR、量额、行业、size）',
    'e6o_minute.py': '分钟尾盘量（14:30–15:00 额 / 量）与 E6n 分钟面板字段对齐',
    'e6o_triggers.py': '证券级触发面板（T1a / T1b 族 / T3 族 / T4a / T4b / T5）与 pool0 全程掩码',
    'e6o_engine.py': '账户引擎（numba；现金 / 批次 / 净订单 / 标签 / 重入 / 随机选择；POST_VWAP_EQUITY_V11）',
    'e6o_acct.py': '引擎的 Python 端：市场输入 mmap、形成名单 CSR、状态分配、checkpoint',
    'e6o_run.py': '运行编排：账户 A2 / B、影子风险集、随机与水平控制',
    'e6o_registry.py': 'A1 编译：966 逻辑 → 1,932 执行 + 父；比较图；随机覆盖；触发定义',
    'e6o_a1.py': 'A1 冻结：G / E 账本、问题卡、CC 携带、政策 profile、freeze_E6o.json',
    'e6o_stage0.py': 'Stage 0 第一部分（S0-0…S0-4、S0-6…S0-9、攻击样例、S0-12 / S0-13 登记）',
    'e6o_stage0b.py': 'Stage 0 第二部分（S0-5、S0-10、S0-11）',
    'e6o_selftest.py': '引擎工程自测（零触发恒等、NAV、checkpoint）',
    'e6o_refcheck.py': '手工逐日账（独立会计重算 + 三类真实片段）',
    'e6o_g1.py': 'G1 第一道 probe（推导段）',
    'e6o_seal.py': 'seal_A2 / seal_final',
    'e6o_stats.py': '账户汇总 / 逐年 / 事件 / 日序列导出（HAC、bootstrap、同资本、冲击、PORT3_T）',
    'e6o_policy.py': '随机汇总、政策、主展示 72',
    'e6o_claims.py': '声明与查询登记（Q / E / CC / G），E01–E07 区间',
    'e6o_diag.py': 'D-1…D-6 有界诊断',
    'e6o_reports.py': '报告生成',
    'e6o_notes.py': '读法注 / 限制登记 / 复盘 / 经验 / 代码登记 / 白名单',
    'e6o_closure.py': '恒等合并、SCHEMA、闭包门、副本包、交付目录',
    'e6o_topup.py': '主母体随机精度增补（精度集按 FULL mcse 两档增补：384 → 1,024）',
    'e6o_replaycheck.py': 'B 后推导段重放核对（随机路径 / 账户 / 影子与 A2 逐位相同）',
    'e6o_stage0_final.py': 'Stage 0 终版引擎刷新（A2 前表快照、S0-11 实测墙钟）',
    'e6o_merge.py': '全局键唯一合并',
    'e6o_s0_fixture.py': 'S0-12 决策端脚本合同夹具',
    'e6o_s0_12_13.sh': 'S0-12 / S0-13 运行脚本',
    'e6o_bg.sh': '后台启动器（核心绑定、线程限制）',
    'e6o_kill.sh': '停止本轮进程（脚本自身命令行不含匹配串）',
    'e6o_chain_s0.sh': 'Stage 0 链', 'e6o_chain_a2.sh': 'A2 链', 'e6o_chain_b.sh': 'B 链', 'e6o_chain_dry.sh': 'seal_A2 后假数据空跑链（只写 tmp/dryrun）',
    'e6o_dbg1.py': '调试：早退推迟成交核查（定位浮点残量缺陷）',
}
FIXES = [
    ('2026-10-17 22:45', 'e6o_engine.py', '现金约束求解把"已过原 due 才成交的早退意向"计入早退款（迟到成交不生标签）→ lag0 账户标签不足报错（FEASIBLE 6 个）；改为只计 d < 原 due 的早退',
     'A2 全部账户重跑（未封存前）'),
    ('2026-10-17 22:52', 'e6o_engine.py / e6o_acct.py', '新增可选逐笔成交日志（手工逐日账用）与日序列"再次入场"列；计算不变', 'A2 全部重跑'),
    ('2026-10-17 22:57', 'e6o_engine.py', '批次卖出分摊的浮点残量（约 1e−12 股）使已全额成交的早退批次晚一日才判"卖完"（3,003 / 3,377 推迟事件为此类）；改为整笔可执行时请求批次整批卖出、部分时按相对容差判卖完',
     'A2 全部账户 / 影子 / 随机 / G1 重跑后封存'),
    ('2026-10-17 23:40', 'e6o_notes.py', '经验列表结尾括号不配对（语法错误，静态检查发现）；L08 缺值改用统一格式化', '无（未运行过）'),
    ('2026-10-17 23:45', 'e6o_stats.py', 'HAC 标准误与 bootstrap 区间按"段内全部日"归一，部分支持列（MINUTE_2013 在 2010-2014 段、P_SOURCE 段首预热）区间偏窄；改为按各列有限日归一（bootstrap 用比率估计）',
     'account_summary 的 hac_se_* / boot_*（B 统计步之前改）'),
    ('2026-10-17 23:50', 'e6o_bg.sh / e6o_chain_*.sh', '结果目录改为相对代码目录解析（脚本里不写含用户目录的绝对路径）', '无'),
    ('2026-10-17 23:55', 'e6o_claims.py', '变体缺失时取 [0] 会崩 → 缺失记 mixed / 空区间；CC-11 文本里日龄剩余超额是写死的旧数 → 改为从 S0-10 现读；缺值在 %.4f 下印成字面 NaN → 文字栏统一换"—"',
     'claims_E6o.csv（B 统计步之前改）'),
    ('2026-10-17 23:58', 'e6o_diag.py', 'D-6 分钟面板日期 / 代码映射加格式归一与 6 位码回退（另记映射率行）；D-4 状态分解加 VOL_NA_WARMUP 档使分量和 = FULL', 'D4 / D6（B 统计步之前改）'),
    ('2026-10-18 00:27', 'e6o_policy.py', '收尾打印以 tuple 作 JSON 键而崩（表已写出；空跑发现）', '无'),
    ('2026-10-18 00:30', 'e6o_closure.py', '推导段恒等预测对字符串日期数组取 max 而崩；敏感串扫描名单改为运行时取（代码里不写名字），凭据词用 chr() 拼接；状态词扫描排除代码登记表；query 表名去括注（空跑 / 门测试发现）',
     'verify/identities_E6o.csv、closure_E6o.*'),
    ('2026-10-18 00:35', 'e6o_topup.py', '精度增补由"一次补到 1,024"改为 brief 原文"按 MCSE ≤ .01 增补"：按 FULL mcse 两档（384 → 1,024；档位事前固定、只看 mcse）', 'random_paths_B_topup*（增补开跑前改）'),
    ('2026-10-18 00:40', 'e6o_diag.py / e6o_claims.py / e6o_notes.py', '加测试参数（--stats_root / --out、--test_root、--root）：在 tmp/ 下用 B 账户文件 + 空跑统计试跑以查崩溃（只核跑通、行数与词表，未读数值）；diag 新参数变量名与 D-1 循环变量冲突（输出前崩）已改',
     '无（正式运行不带测试参数）'),
    ('2026-10-18（B 后）', 'e6o_claims.py', 'E02 / E07 区间与点估不是同一估计量（E07 区间 [1.27, 1.48] 不含其点估 .936）→ 改为同一估计量（E02：原生配对差区间按随机均值差平移；E07：各对共同抽日期 bootstrap 后对对取均值）；判定规则不用区间，状态不变',
     'claims_E6o.csv / contrasts / 账本结果栏 / 报告 cards；其后 seal_final、交接目录、决策端脚本与闭包门重跑（前一版交接目录移入 tmp/superseded_*）'),
    ('2026-10-18（B 后）', 'e6o_closure.py', '本地同步后的措辞核查发现交接目录混入 py_compile 生成的 __pycache__（字节码内嵌源文件绝对路径）与决策端脚本 stdout 印出的绝对输出路径（含用户目录名）→ 编译检查改写到 tmp、交接复制排除 __pycache__、决策端脚本在结果目录内以相对路径参数运行（脚本本身未改）；闭包门加 S07b（交接目录全部文件含二进制扫描；决策端脚本原件按固定 sha 豁免——其 S22 扫描正则本身含凭据类词，是模式不是信息）',
     '交接目录 / verify/decision/out_E6o_stage2；尾段从 notes 重跑（前一版交接目录移入 tmp/superseded_*）'),
]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='', help='测试用：statistics / reports 从该目录读，产出写该目录')
    ROOT = ap.parse_args().root or O.work()
    RD = lambda *x: os.path.join(ROOT, *x)
    R = pd.read_csv(O.P('registration', 'registry_E6o.csv'), keep_default_na=False, na_values=[''])
    AS = pd.read_csv(RD('statistics', 'account_summary_E6o.csv'), keep_default_na=False, na_values=[''])
    RT = pd.read_csv(RD('statistics', 'randoms_E6o.csv'), keep_default_na=False, na_values=[''])
    S0 = pd.read_csv(O.P('diagnostics', 'stage0_E6o.csv'), keep_default_na=False, na_values=[''])
    s0 = S0.set_index('key')['value'].to_dict()
    main_f = R[(R.series == 'C_ACCOUNT') & (R.is_main_object == 1) & (R.execution_profile == 'FEASIBLE_DAILY')].exec_id.iloc[0]
    h = R.set_index('exec_id').loc[main_f, 'exec_hash']
    DY = np.load(O.P('accounts_run', 'full', h[:2], '%s.npz' % h), allow_pickle=False)['DY']
    import e6o_engine as E
    stale = float(DY[:, E.DYI['stale_val']].sum() / max(DY[:, E.DYI['nav_post']].sum(), 1e-12))
    am = RT[(RT.mechanism == 'AMOUNT_MATCH') & (RT.segment == 'FULL') & (RT.paths > 0)]
    um_med = float(am.unmatched_share.median()) if len(am) else float('nan')
    um_max = float(am.unmatched_share.max()) if len(am) else float('nan')
    tf = json.load(open(os.path.join(O.cache_dir(), 'triggers', 'trigger_facts.json')))
    # ---------------- 限制登记
    L = [
        ('L01', 'FEASIBLE_DAILY 是日频执行模型（开盘 / 全天一字板按 side），不是已校准冲击模型；无队列 / L2，不称确定成交率', '全部', '—'),
        ('L02', 'IDEALIZED_SOURCE_FILL 继承源"意向日 VWAP 成交"（停牌按最近价）', 'IDEALIZED 全部', '—'),
        ('L03', 'P_ACCOUNT − P_SOURCE 是会计桥（源 = 固定滚动权重；账户 = 自融资、漂移、复牌跳价、成交日记费、CASH_V0 连续建仓），不是退出增量', 'BRIDGE_*', '主父 IDEAL 桥见 R0'),
        ('L04', '源形成名单每段首约 19 个交易日为空（源 clean 成熟期）：连续账户在段首不新建批次、旧仓按期退出', '全部账户', '段首日数 19 × 3'),
        ('L05', 'T1a：池内有值 = 源分组；池外持仓用同日 (α, β, cut) 延伸；池内无值 / 当日无切点 = UNKNOWN（源在入场把无值票剔除，退出层不把"无值"当坏）', 'T1a / T2prime / RECONFIRM(T1a)', s0.get('T1A_DAYS_CUT_SKIP', '—')),
        ('L06', '分钟触发 2013-08-01 起（MINUTE_2013 支持）；沪市收盘集合竞价 2018-08-20 起，之前 T4b = UNKNOWN（对象不存在，不当 0）', 'T4a / T4b / T5', '—'),
        ('L07', 'T3 量比为原始量比（不做送转换算）；窗口内复权因子跳升 ≥ 1.15 的格只标记、不改量', 'T3 族', '受影响格 %s' % s0.get('T3_CORP_ACTION_AFFECTED', '—')),
        ('L08', 'AMOUNT_MATCH 随机：风险集不足时金额未匹配（UNMATCHED 份额并印），不从未来或他路径补足', '随机层', '未匹配份额中位 %s、最大 %s' % (RP.f(um_med, 4), RP.f(um_max, 4))),
        ('L09', '随机种子 = stable(E6o, 机制, 路径序号)：同路径序号在不同 owner 间共用基础随机数（方差减少，plan §8.3）；各路径库存 / 现金独立递推', '随机层', '—'),
        ('L10', 'D_sc 是逐日交易后敞口共同下缩的视图，不是闭环同资本重跑', 'c3 / D_sc 列', '—'),
        ('L11', 'FROZEN_COST_STRESS：固定路径再扣冲击（κ √A Σ|Δw|^1.5 σ / √ADV），κ 未用本账户成交校准；不是带冲击自融资账户', 'c5 / D-3', '—'),
        ('L12', 'PORT3_T_EXIT_MAPPING 用 T 收盘全组合目标（幸存旧仓 + 意向买）的 clean 市值分位；成交后敞口另在日序列', '政策 port3t', '—'),
        ('L13', '1,932 个干预账户与随机构成大挑选空间；本轮不做 PBO / DSR 自动修正（plan §11.5）；主展示与主对象事前固定', '全部读数', '—'),
        ('L14', '全部结果复用 2010-01-04 … 2026-03-27 历史（不是独立 OOS）；E7 未读', '全部', '—'),
        ('L15', '停牌持仓按最近价估值并标陈旧（复牌跳价计入收益）；主对象陈旧估值市值占 NAV 的日均份额', '账户层', '%.6f' % stale),
        ('L16', 'G1 用源形成名单的无退出影子批次（不是实际账户持仓）；只看推导段', 'G1', '—'),
        ('L17', 'D-1 不插值造收益；D-2 FROZEN_TARGET_DIAGNOSTIC 是冻结目标诊断，不是可部署账户', 'D-1 / D-2', '—'),
        ('L18', 'NEXT_RANK 候选序 = 源 Struct.order_keys（A4b 末级 T 延伸优先序），排除最终名单与非法域；行业 / 1% 余量逐名给款', 'FUNDING_NEXT', '—'),
        ('L19', 'ENTRY_RANDOM：Y11（入场暂停 + 退出）的随机路径保留真实退出、只随机取消新买', 'ENTRY_EXIT 随机', '—'),
        ('L20', '账户允许分数股（源级连续权重近似）；整手与最小申报量未建模', '全部账户', '—'),
        ('L21', 'T1b_EDGE 与 SOURCE_T1B 触发格完全相同（%d 格）→ 两族账户数值相同（别名）；随机路径因机制种子相同亦相同' % tf['edge_vs_source']['trig_cells_source'], 'EDGE_BRIDGE', '差异格 %d' % tf['edge_vs_source']['trig_diff_cells']),
        ('L22', 'G4 行 status = INFO：其 net / parent_net 各为四段中位，不满足 D = net − parent_net（D 本身 = 四段 D 中位）', 'account_summary G4 / G4_2013', '—'),
    ]
    LR = ['# E6o 限制登记\n', HDR, '每条：编号 | 限制 | 影响范围 | 机器计数（闭包时刷新）。各条在 `E6o_REVIEW_input_notes.md` §6 引用。\n\n', '| 编号 | 限制 | 影响范围 | 机器计数 |\n|---|---|---|---|\n']
    for l in L:
        LR.append('| %s | %s | %s | %s |\n' % l)
    RP.write(ROOT, 'E6o_limit_register.md', ''.join(LR))
    # ---------------- 读法注
    c = pd.read_csv(RD('reports', 'claims_E6o.csv'), keep_default_na=False, na_values=[''])
    e01 = c[c.claim_id == 'E01'].iloc[0]
    N = ['# E6o REVIEW 读法注（执行端；给决策端 REVIEW v1.0）\n', HDR]
    N.append('\n## 1. 先读\n\n1. `E6o_REPORT_part2.md`：主对象（两情景）、72 主展示、CORE 17 支、各家族分布。\n2. `E6o_cards.md`：E01–E07 的符号与区间、Q01–Q18 的绑定与结果。\n'
             '3. `E6o_REPORT_mechanisms.md`：资金 / 重入 / 情景配对、事件、D-1…D-6。\n4. `E6o_REPORT_R0.md`：源合同绑定（S0-0）、会计桥、攻击样例。\n'
             '5. `E6o_REPORT_part3.md`：POLICY_E6O_PARENT_Q 与研究状态。\n6. `E6o_REPORT_carried.md`：CC 原句评分与 G-F2 三条链。\n')
    N.append('\n## 2. 主对象一句话事实（机器表现算）\n\n主对象 FEASIBLE FULL D（相对同引擎无退出父）= %s，bootstrap 区间 [%s, %s]；E01 判为 %s（%s）。\n' % (
        RP.f(e01.result_value, 4), RP.f(e01.ci_lo, 4), RP.f(e01.ci_hi, 4), e01.claim_status, str(e01.note)[:300]))
    N.append('\n## 3. 口径提醒\n\n- 主差 = C_ACCOUNT − 同引擎、同情景、同支持的无退出 P_ACCOUNT（MAIN_EXIT）；完整迁移差 = C − P_SOURCE（D_source 列）；两者之差是会计桥（L03）。\n'
             '- 年化 = 日差均值 × 252 × 100；FULL = 四段有效日 n 加权；G4 = 四段中位（G4 行 status = INFO，L22）。\n'
             '- 区间：HAC（lag H / 2H / max(H, 20)）与 stationary bootstrap（2,000 次、块 20；块 60 敏感列 boot60_*）。\n'
             '- 同资本视图 D_sc 是交易后敞口共同下缩（L10）；冲击 D_imp 是固定路径扣费（L11）。\n')
    N.append('\n## 4. 执行中的技术修复（无经济规则变动；引擎修复均在 seal_A2 之前，统计 / 报告 / 闭包链修复均在 B 统计步之前）\n\n')
    for fx in FIXES:
        N.append('- %s · `%s`：%s（影响：%s）。\n' % fx)
    N.append('\n## 5. 分钟数据可用之处观察（只记事实与指针；不实现、不计数、不影响主程序；brief §0.3 A11）\n\n'
             '1. 分钟重建全日 VWAP 与日频 vwap 在 2019 年后几乎逐格恒等（S0-3：深市 1.0、沪市 ≥ .9999）→ 可做"日内 VWAP 执行计划"模拟（成交时窗读法 E 的上游）。\n'
             '2. 14:57 前最后连续成交价与官方收盘的跳空（T4b 量）在深市全期、沪市 2018-08-20 起可得 → 持有期风险监控的一个现成量（本轮只作退出触发）。\n'
             '3. 分钟实际成交额可替代日线 ADV 估参与率（D-3 两列分开报）→ 容量 / 冲击校准的输入。\n'
             '4. 分钟最低价（low_min）可检验"日内触价止损"语义（本轮 T6 明确不是日内触价）。\n'
             '5. 时段量份额（vb1 / vb8）在 pool0 与持仓域的前向超额分位见 D-6；可作 K 腿活动分布下一轮的第一道。\n')
    N.append('\n## 6. 限制（全文 `E6o_limit_register.md`）\n\n' + '；'.join('%s %s' % (l[0], l[1][:30]) for l in L) + '。\n')
    N.append('\n## 7. 交付内容\n\n见 `E6o_REVIEW_input.md`（全部文件与 sha）与 `SCHEMA.md`（合同表行数 / 列）；决策端脚本结果在 `verify/decision/out_E6o_stage2/`。\n')
    N.append('\n## 8. 请决策端处理的事项（跑批中代拟、继续跑；用户 10-11 定）\n\n'
             '| # | 类 | 事项 | 执行端处理 |\n|---|---|---|---|\n'
             '| 1 | 知会 | SOURCE_T1B 参考域按源码绑定为当日 clean 截面（proposal 文字为"池内最差 10%"） | 按 plan §4.1 源码兼容绑定；EDGE 显式支与源触发格完全相同（L21） |\n'
             '| 2 | 知会 | T4a / T4b 参考域按 plan 原文取 pool0（日 CVR 源为 clean） | 照 plan 文本；不改阈值 |\n'
             '| 3 | 追认 | 随机种子不含 owner（同路径序号跨 owner 共用基础随机数），种子 = stable(E6o, 机制, 路径序号) | brief §7"对象语义 ID"按"随机对象 = 机制 × 路径"理解；L09 |\n'
             '| 4 | 追认 | 父对象按支持展开（FULLHIST / MINUTE_2013 各一套：P_ACCOUNT 96、P_SOURCE 48，合同下限 48 / 24） | plan §7"父须同 support" |\n'
             '| 5 | 追认 | account_summary 的 G4 行 status = INFO（L22） | 使 COMPUTED 行恒等 D = net − parent_net 严格成立 |\n'
             '| 6 | 追认 | D_sc 定义（交易后敞口共同下缩；源 MATCH-CAP 是形成日目标层定义） | L10 |\n'
             '| 7 | 追认 | 研究状态五档的判定规则（A1 冻结于 policy_profile_E6o.json） | 按规则机器现算 |\n'
             '| 8 | 知会 | A1 后三处技术修复（§4），A2 全部在最终引擎上重跑后封存 | code_change_register §2 |\n'
             '| 9 | 知会 | proposal §3.9 称发散 12 个候选，§3.4 原文 11 个（C-D 缺） | G 账本 G-CC-C-D 记 NO_NEW_DIRECTION_YET |\n'
             '| 10 | 知会 | P_SOURCE 的 start_state 按附录 F 写 CASH_V0，源本身是分段重置（段首约 19 日预热） | L04 |\n'
             '| 11 | 追认 | 入场暂停账户（exit OFF）的政策 c4 用 ENTRY_RANDOM；分钟触发在 17 年政策下一律"不可判"、研究列另给 | plan §11.3 |\n'
             '| 12 | 知会 | S15 判据第 4 项（审计钩子）：本轮仍无生产审计钩子；E7 守卫以读取接口截断 + FUTURE_DATA_PLANT 攻击替代 | 同 E6m 替代口径 |\n'
             '| 13 | 知会 | 主母体随机精度集：D 脚本 S11 的规则（form / H / 触发 / 资金 / 重入五段，不过滤 lag / maturity / guard）比 brief §6 的 12 个 owner 宽 | 两者并集按 FULL mcse 两档增补（384 → 1,024；档位事前固定、只看 mcse）；清单与逐档 mcse 见回执 E6o_randoms_B_topup |\n'
             '| 14 | 知会 | Stage 0 的恒等、攻击样例与 S0-5 计数在 A1 时由引擎 v1 产出；B 后用终版引擎 v3 重算 | A2 前原表另存 *_preA2.csv；S0-11 行 note 记 A2 前估计并加实测墙钟 |\n'
             '| 15 | 知会 | 假数据空跑（后段日行 = 推导段日行循环复制）在 seal_A2 之后、与 B 的账户 / 随机层并行跑（只读 A2 产物、只写 tmp/dryrun）；空跑发现的报告链问题在 B 统计步之前修完 | 未读任何后段读数；logs/chain_dry.log 与 chain_b.log 时间戳可核 |\n'
             '| 16 | 知会 | 47 连接中转 10-17 23:37 起中断约 40 分钟，期间只做本地脚本复核（47 上无运行任务），恢复后先写 seal_A2 再开 B | 不影响任何产物 |\n'
             '| 17 | 知会 | 决策端脚本 S11 = DIFFERS：其主母体精度规则不按 exit_enabled 过滤，命中 3 个 ENTRY_EXIT Y10 账户（T1a × 三记忆，入场暂停、退出关）；它们无退出意向，按 brief §6 不在 AMOUNT_MATCH 范围（ENTRY_RANDOM 范围是 T1b_LEVEL 入场四账户），randoms 表记 paths = 0 / NOT_APPLICABLE | 不改 D 脚本、不为无退出账户造随机路径；其余 39 个精度 owner FULL mcse 全 ≤ .01（最大 .0099） |\n'
             '| 18 | 知会 | E02 / E07 的区间与点估原为不同估计量（E02 区间是原生配对差；E07 点估是 24 对均值、区间是 1 对）→ B 后改为同一估计量（E02 = 原生区间按随机均值差平移；E07 = 各对共同抽日期 bootstrap 后对对取均值） | 判定规则不用区间，状态不变；见代码登记 §2 |\n'
             '| 19 | 知会 | 决策端脚本的运行方式：以结果目录为工作目录、相对路径参数（--root . / --handoff handoff/… / --out verify/decision/out_E6o_stage2）运行，使其 stdout 不印含用户目录的绝对路径；脚本本身未改（sha 0988d2e5…），探针逻辑不受影响 | 交接目录全部文件另经闭包门 S07b 扫描 |\n')
    RP.write(ROOT, 'E6o_REVIEW_input_notes.md', ''.join(N))
    # ---------------- 复盘 / 经验
    rec = {}
    for p in glob.glob(O.P('task_status', '*.receipt.json')):
        j = json.load(open(p))
        rec[j['task_id']] = j
    wt = {k: v.get('wall_s') for k, v in rec.items()}
    rand_s = sum(v for k, v in wt.items() if k.startswith('E6o_randoms') and v)
    acc_s = sum(v for k, v in wt.items() if k.startswith('E6o_accounts') and v)
    RS = ['# E6o 执行端复盘\n', HDR, '\n## 1. 资源实耗（回执墙钟秒）\n\n| 任务 | 墙钟 s |\n|---|---|\n']
    for k in sorted(wt):
        RS.append('| %s | %s |\n' % (k, RP.f(wt[k], 1)))
    RS.append('\n随机层墙钟合计 %s s，账户层 %s s；随机层占两者之和 %s。主母体精度集（random_scope topup_to = 1,024 ∪ D 脚本 S11 规则命中）AMOUNT_MATCH 按 FULL mcse 分两档增补（事前固定档位：全部补到 384；仍 > .01 的再补到 1,024）；到 1,024 仍 > .01 记 MC_LIMIT（randoms_E6o.csv status / paths；逐档 mcse 见回执 E6o_randoms_B_topup）。\n' % (
        RP.f(rand_s, 0), RP.f(acc_s, 0), RP.f(rand_s / max(rand_s + acc_s, 1), 3)))
    RS.append('\n## 2. 做得对的\n\n- Stage 0 先绑源：B2 触发是 EDGE、参考域 clean、水平对照是日 CVR——都从函数体读出，没有按文字猜。\n'
              '- 引擎在推导段封存前就过了三道独立核：零触发 ≡ 父（逐位 0）、手工逐日账（会计层独立重算 0 差）、checkpoint 续跑逐位一致。\n'
              '- 手工逐日账抓到了一个引擎缺陷（浮点残量使早退判晚一日），在封存前修掉。\n'
              '\n## 3. 读法建议\n\n- 先看主对象 FULL 与四段的符号与区间，再看同金额随机（AMOUNT_MATCH）与日水平控制（LEVEL_WORST_1D）；族中位与主对象分列。\n'
              '- 资金去向的差（CASH / NATIVE / NEXT）同时含选人、资本与反馈，固定机会表与闭环表不混读（plan §8.5）。\n')
    RP.write(ROOT, 'E6o_executor_retrospective.md', ''.join(RS))
    LS = ['# E6o 经验增量（执行端）\n', HDR,
          '\n- O01 经包装脚本的打包上传（本地 tar 管道 → 远端解包）：命令末尾不能再加 `< /dev/null`（会覆盖管道输入，远端收到空包）。\n'
          '- O02 `pkill -f` / `pgrep -f` 的匹配串若出现在发起命令自身的命令行里，会杀掉自己的会话（返回 255）。停进程用独立脚本、单独一次调用。\n'
          '- O03 批次卖出的逐批浮点相减会留 1e−12 股残量，使"已全额成交"的批次晚一日判卖完；整笔可执行时应整批卖出，事件分类才对。核法：推迟成交天数必须全部落在不可卖日。\n'
          '- O04 现金约束求解里"早退款"必须只算仍早于原 due 的早退；迟到成交不生标签，混进去会让 lag0 账户在执行时标签不足。\n'
          '- O05 新引擎在封存前过三道独立核（零触发恒等、手工逐日账、checkpoint 续跑），各自能抓不同类的错；本轮第二道抓到了 O03。\n'
          '- O06 随机层耗时由选择逻辑的 O(候选 × 批次) 扫描主导；下一轮可在每日建证券 → 批次链表（同执行端卖出），预计提速 2–3 倍。\n']
    RP.write(ROOT, 'E6o_lessons_delta.md', ''.join(LS))
    # ---------------- 代码登记 / 白名单
    code_dir = os.path.dirname(O.__file__)
    files = sorted(os.path.basename(p) for p in glob.glob(os.path.join(code_dir, 'e6o_*')))
    rows = [dict(file=fn, sha256=O.sha_file(os.path.join(code_dir, fn)), status='NEW', written_at=time.strftime('%Y-%m-%d %H:%M:%S'), purpose=PURPOSE.get(fn, '—')) for fn in files]
    os.makedirs(RD('code_register'), exist_ok=True)
    O.atomic_write_csv(RD('code_register', 'deploy_log.csv'), pd.DataFrame(rows))
    CC = ['# E6o 代码变更登记\n', HDR, '\n## 1. 本轮新文件（全部 NEW，前缀 e6o_；源与 E6n 及更早代码只 import 不改）\n\n| 文件 | sha256 前 16 | 用途 |\n|---|---|---|\n']
    for r in rows:
        CC.append('| %s | %s | %s |\n' % (r['file'], r['sha256'][:16], r['purpose']))
    CC.append('\n## 2. 运行中的技术修复（版本 + 受影响依赖）\n\n| 时间（47） | 文件 | 修复 | 受影响依赖 |\n|---|---|---|---|\n')
    for fx in FIXES:
        CC.append('| %s | %s | %s | %s |\n' % fx)
    RP.write(ROOT, 'E6o_code_change_register.md', ''.join(CC))
    WL = ['# E6o 提交白名单（只在用户指示后提交；不 `git add .`）\n', HDR, '\n仓库：47 code/project_core。只提交下列 %d 个文件（sha 与 code_register/deploy_log.csv 一致）：\n\n' % len(rows)]
    for r in rows:
        WL.append('- `%s`（%s）\n' % (r['file'], r['sha256'][:16]))
    RP.write(ROOT, 'E6o_commit_whitelist.md', ''.join(WL))
    print(json.dumps(dict(limits=len(L), code_files=len(rows)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
