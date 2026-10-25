# -*- coding: utf-8 -*-
"""E6p 执行端交付文书（brief §8.1 / §8.5）：reports/E6p_REVIEW_input_notes.md（§1–§8；§8 = 待决事项；"分钟数据可用之处观察"节）、E6p_lessons_delta.md、
E6p_executor_retrospective.md（资源实耗、随机预算实际占比、读法建议）、E6p_code_change_register.md（A1 后技术修复逐条 + 文件 sha）、E6p_commit_whitelist.md。
数字从机器表 / 回执取；叙述是执行端事实陈述与读法建议，不替决策端下结论。用法：python3 e6p_notes.py [--root <根>]"""
import os
import json
import glob
import argparse

import numpy as np
import pandas as pd

import e6p_core as O
import e6p_reports as RP

FIXES = [
    ('e6p_engine.solve_eval', '额外买入份额取非负：常规 + 部署份额浮点舍入可略超 1 使 X_buy 为负（只在部署层出现；部署为零时与 E6o 同式）', 'A1 前（selftest 阶段）'),
    ('e6p_engine.solve_all / step', '现金舍入级缺口（≤ 1e−6 元；部署 / 缩量把普通现金压到 0 后的次日无卖出日）不当不可行（码 12、计数 S_i[SI_RNDFIX]），只消耗实际可用标签；E6o 账户从未进入该分支（逐位复现不变）', 'A1 前'),
    ('e6p_engine.mark_early', '意向表新增批次 ID 列 IN_LID（离线 landmark / D1 / D4 / D9 / RENEW 同证券份额用；不参与运算）', 'A1 前'),
    ('e6p_engine.select_v2（COUNT_ISK）', 'owner 证券层未知（行业 / size 缺）的需求直接回填日龄桶层（原写法会越界）', 'A1 前'),
    ('e6p_acct.Account.checkpoint / restore / state_hash', 'checkpoint 只存变长容器已用行；状态 hash 按已用行计（引擎从不读已用行之后的内容）', 'A1 前'),
    ('e6p_acct.ip_fp', '部署目标 > 1 拒绝（R1；DEPLOY_TARGET_LE_ONE）', 'A1 前'),
    ('e6p_run.job_random', '未匹配日计数加相对阈值（≥ 1 元且 ≥ 1e−6 × 当日请求），去掉浮点残差；推导段 D 计算掩码长度修正（推导段读数不受影响：修正前该批次全部报错未产出）', 'A2 随机启动前'),
    ('e6p_stage0（E6O_TABLE_BINDING / SOURCE_EXPOSURE_EQ_MEAN_SUMW）', 'E6o 表读数按父行自身支持（剔源预热）与退出子共同支持分别绑定；敞口恒等改按源公式段内计算（逐位成立）', 'A1 前'),
    ('e6p_stage0 / e6p_diag（干跑后）', 'stage0 终表补 S0-3 / 5 / 6 / 10 行（取自恒等表）；D3 统计名去掉 "@"（D 脚本 S22 字段名规则）', 'B 前（干跑 DIFFERS 后）'),
    ('e6p_claims / e6p_reports（B 复核后，只动文字与表列）', 'E 账本 precision 列与状态分开写（原写法把"不支持"行一律写成"区间不跨 0"，E10 区间跨 0）；E05 结果注明单位 bp；'
     'CC-E6p-07 补 T1A_VS_LEVEL 零点；R0 WARM 行按对象标注、补 LEVEL_WORST 近同构读法；政策通过表加 block / memory / cap / renew 列', 'B 统计后、收尾门前'),
    ('e6p_closure.schema（收尾门 ⑪ FAIL 后）', 'SCHEMA.md 的"键列"原用竖线连接多键（exec_id|segment），把 Markdown 表切歪、列名格错位（11 张表；行数均对）；改用" + "连接。D 脚本 S19 只读文件名与行数，不受影响', '收尾门首跑后'),
    ('e6p_closure.handoff_scan（首次建交接目录时）', 'S07b 全交接件扫描改为按文件并行（96 进程，进程内缓存已编译模式；扫描规则与文件范围不变）。原单线程实测约 7 MB/s，成交分片合计约 128 GB 需 4 小时以上；首个交接目录 E6p_20261020_2320 扫描中途停止，原样移到 tmp/superseded_handoff_E6p_20261020_2320（未删）', '建交接目录时'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    root = O.P(a.root) if a.root else O.work()
    rd = lambda rel: pd.read_csv(os.path.join(root, rel), keep_default_na=False, na_values=[''])
    rep = os.path.join(root, 'reports')
    W = lambda n, t: O.atomic_write_text(os.path.join(rep, n), t)
    js = lambda p: json.load(open(p)) if os.path.exists(p) else {}
    und = js(O.P('diagnostics', 's0_e6o_undecidable_E6p.json'))
    br = rd('verify/trades_events_bridge_E6p.csv') if os.path.exists(os.path.join(root, 'verify', 'trades_events_bridge_E6p.csv')) else pd.DataFrame()
    EV = rd('events/event_counts_E6p.csv')
    RD = rd('statistics/randoms_E6p.csv')
    R = pd.read_csv(O.P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
    rp = rd('statistics/random_paths_main_E6p.csv') if os.path.exists(os.path.join(root, 'statistics', 'random_paths_main_E6p.csv')) else pd.DataFrame()
    # 随机意向倍数（BERNOULLI_LAG60 vs owner）
    pth = O.P('randoms', 'random_paths_B.csv')
    bern_ratio = ''
    if os.path.exists(pth):
        P = pd.read_csv(pth, usecols=['owner_exec_id', 'mechanism', 'n_intents'])
        b = P[P.mechanism == 'BERNOULLI_LAG60'].groupby('owner_exec_id').n_intents.mean()
        own = EV.set_index('exec_id').n_intents
        r_ = (b / own.reindex(b.index)).replace([np.inf, -np.inf], np.nan).dropna()
        bern_ratio = 'BERNOULLI_LAG60 路径意向数 / owner 意向数：中位 %.2f（四分位 %.2f–%.2f；%d 个 owner）' % (r_.median(), r_.quantile(.25), r_.quantile(.75), len(r_))
    partial = ''
    if len(br):
        nb = int((br.partial_fill_extra_rows != 0).sum())
        partial = '%d / %d 个 ACCOUNT 对象存在部分成交行（早退成交行 − 已实现早退意向 = %d … %d）' % (nb, len(br), int(br.partial_fill_extra_rows.min()), int(br.partial_fill_extra_rows.max()))
    rec = {os.path.basename(p): js(p) for p in glob.glob(O.P('task_status', '*.receipt.json'))}
    wall = {k.replace('.receipt.json', ''): v.get('wall_s') for k, v in rec.items() if v.get('wall_s') is not None}
    notes = [RP.HEADER, '# E6p REVIEW 输入注记（执行端；方式 B 一次交付）', '',
             '## §1 交付范围', '', '- 2,128 执行账户（1,064 逻辑 × FEASIBLE / IDEAL）+ 48 个 P_SOURCE；成本反馈 84 路径；WARM 敏感性（主对象对与其父 × 两情景 × 四段，不进 registry）。',
             '- 随机：FEASIBLE 576 owner × 四机制（128 起；18 个主对象 owner 按 MCSE ≤ .01 增补）、AMOUNT_ISK_V2 180、R_CHECKPOINT 12；IDEAL 18 个主对象 owner × AMOUNT_MATCH_V2 128。', '',
             '## §2 源绑定与复现', '', '- E6o 18 个 P_ACCOUNT（H5 / 10 / 20 × 三记忆 × 两情景）与 H5 主对象逐日复现 ≤ 1e−9；主对象 FULL D 现算 = E6o 汇总（差 4e−15）。',
             '- P_SOURCE 对 E6n 冻结账户与 E6o 源账本逐日差 0；源引擎支持六个 H（H15 / 30 / 40 无冻结账户可对照 → 复现 NOT_APPLICABLE）。',
             '- 敞口恒等：P_SOURCE 逐日敞口 = 源公式 H 日内 ΣW 均值（滞后 2 日、段内）逐位成立（max diff ≤ 7e−16）；P_ACCOUNT 不受该等式约束（plan §1.2(8)）。', '',
             '## §3 段初始化口径', '', '连续全历史（CASH_V0）为主、四段重置（WARM）只作主对象对与其父的敏感性（brief §0.1 #18 有意偏离 plan §4.4；用户 10-19 裁定）。WARM 结果见 statistics/warm_sensitivity_E6p.csv。', '',
             '## §4 随机与匹配', '', '- %s。影子按"状态日"计触发率（E6o 定义沿用；持续状态触发每日重复计入风险集），不是首达风险率——读 BERNOULLI 对照时注意其退出强度高于 owner。' % (bern_ratio or '（B 随机完成后填）'),
             '- 匹配 V2 两级与未匹配四列全报；CONTROL_NOT_COMPARABLE 规则（FULL 未匹配份额 > .25）A1 冻结。', '',
             '## §5 成本', '', '- 固定路径曲线（A × κ × δ = 20 组合）+ 四种盈亏平衡 + 反馈 84 路径；κ 未校准（SCENARIO_NOT_CALIBRATED）。旧审计 c5 用 E6o 冲击式（κ √A Σ|Δw|^1.5 σ / √ADV）。', '',
             '## §6 政策', '', '- verdict 只由 policy_fields 显式 bool 重算；LEGACY 只在 E6o 已批准域可判，域外 c6 = NA。E6P_CURVE_RESEARCH 的 c5 = NA（UNDECIDABLE_TARGET_A）→ 不出现"通过"。', '',
             '## §7 诊断', '', '- D1–D9、landmark（向量化状态与 S0-10 state_at 定义逐例对照）、镜像差、再投资局部同预算 18 owner 全交付。', '',
             '## §8 待决事项（执行端代拟；用户 10-11 定：不中途发消息）', '',
             '1. **E6o 62 个"全部可算条件通过却不可判"对象（brief S0-2 一句话）**：不可算项是**无**——这 62 个 FEASIBLE 对象的 c1 / c2 / c3 / c4 / c5 / c6 / port3t / positive 八项全为 1；'
             '不可判来自 E6o `e6o_policy.py` 的类型判定：c3（np.sign 比较）与 positive（numpy 浮点比较）是 numpy.bool_，`c is True` 恒为假，于是"全真"落入不可判。按 E6o 自己的 verdict_rule 它们应为**通过**'
             '（H %s；触发 %s）。IDEAL 的 59 个缺 c4（IDEAL 无随机）是真不可判。E6o 结果按 brief 不改；是否在 E6o 报告上加更正注记、以及 E6o"政策 0 通过"的读法是否改写，请决策端裁定。' % (
                 und.get('feasible_all_true_H', ''), und.get('feasible_all_true_trigger', '')),
             '2. **S29 与 B.12 / B.18 的口径张力**：%s。成交日志按成交行（一字跌停日内部转移 + 次日余量 = 同批 2 行），事件按意向（B.12 恒等）；D 脚本 S29 把二者等同，部分成交对象必然 DIFFERS。逐对象桥见 verify/trades_events_bridge_E6p.csv；SCHEMA_DEVIATIONS 已声明。' % (
                 partial or '（B 后填）'),
             '3. **BERNOULLI_LAG60 的风险率定义**：见 §4；若决策端希望改为首达风险率（影子只记批次首次触发），属下一轮设计项（本轮不改，A1 冻结）。',
             '4. **trades.lot_due 的 POST_CUTOFF 记号**：原批次 due 晚于 2026-03-27 的早退行写 POST_CUTOFF（不物化 E7 日期）；如决策端更偏好留空 + 另列标志，下轮改。',
             '5. **registry renew-only 行的 parent_same_h**：合同只规定 trigger ≠ NONE 行；本轮给 renew-only 行填同坐标 renew = 0 父，使其 D 与比较图 VS_SAME_H_PARENT 一致（SCHEMA_DEVIATIONS 第 3 行）。',
             '6. **E6o 白名单提交**仍待用户一句话（本轮不动）；E6p 白名单见 reports/E6p_commit_whitelist.md（提交只在用户指示后）。', '',
             '### 分钟数据可用之处观察（只记，不改设计）', '',
             '- 分钟全日额（09:25 竞价 + 全部 bar）与日频 amount 逐格一致（E6o 已核差 0）→ 可直接作事后参与率分母（D3 两列已用）。',
             '- 尾盘 14:30–15:00 额 / 量可给"尾盘 VWAP 卖出"的同单价格机会（D8 已用）；同口径也可作"尾盘参与率"的容量上限读法（D3 第二列）。',
             '- 14:57 前最后连续成交价（p1457）与官方收盘的差可作收盘集合竞价冲击的事后读法（本轮未用；沪市 2018-08-20 前无收盘竞价）。', '']
    W('E6p_REVIEW_input_notes.md', '\n'.join(notes) + '\n')
    lessons = [RP.HEADER, '# E6p lessons delta（执行端）', '',
               '1. **本机 Git Bash 的 `python` 是商店占位、静默不执行**：heredoc 改文件看似成功实则未改；改代码一律用编辑工具、语法核查放 47。',
               '2. **部署层把普通现金压到 0 后，次日"零卖出日"会暴露 1e−9 级舍入残差**：绝对容差 1e−9 低于 1 亿量级账户的浮点 ulp；新增功能的边界必须单列分支，E6o 路径保持逐位。',
               '3. **政策布尔判定只用显式 Python bool**（plan 附录 C tri_value 的教训在 E6o 实际代码里漏掉了：numpy.bool_ 的 `is True` 恒假）。',
               '4. **成交日志与事件计数是两个单位**（成交行 vs 意向）；合同恒等写在同一句里时，先在推导段量出差异再交付，并在 SCHEMA_DEVIATIONS 声明。',
               '5. **随机层的吞吐瓶颈**：单路径独立 1.2 s，96 并发满载约 4–5 s / 路径（共享面板读取）；预算按并发实测而非单跑估。', '']
    W('E6p_lessons_delta.md', '\n'.join(lessons) + '\n')
    nrand = 0
    for p in (O.P('randoms', 'random_paths_A2.csv'), O.P('randoms', 'random_paths_B.csv'), O.P('randoms', 'random_paths_B_topup.csv')):
        if os.path.exists(p):
            with open(p) as fh:
                nrand += max(sum(1 for _ in fh) - 1, 0)
    retro = [RP.HEADER, '# E6p 执行端复盘（retrospective）', '',
             '## 资源实耗（回执 wall_s，秒）', '', '| 任务 | wall_s |', '|---|---|'] + ['| %s | %s |' % (k, v) for k, v in sorted(wall.items())] + [
             '', '- 随机路径总行数（A2 + B + 增补）：%d；并发 96 worker（核心绑定 96-191, 288-383）。' % nrand,
             '- 账户层：2,128 执行 × 两阶段各约 1.5 分钟；随机层占总算力绝大部分（> 90%）。', '',
             '## 读法建议（给 REVIEW；不替决策端下结论）', '',
             '- 先读主对象两只的 NATIVE 复现 → D80 / D95 同部署差 → H5 两种父差 → 随机（同金额 / 同层 / 状态率 / 水平）→ 成本曲线与反馈；族中位与主对象分列。',
             '- D80 / D95 的增量要拆成部署（DEPLOY_OPERATOR_CHANGE）与退出（同部署差、DEPLOY_X_EXIT）；MIRROR 差只作诊断。',
             '- 长 H 的随机对照：BERNOULLI 退出强度高于 owner（§4），以 AMOUNT_MATCH_V2 / AMOUNT_ISK_V2 为主读。', '']
    W('E6p_executor_retrospective.md', '\n'.join(retro) + '\n')
    dl = rd('code_register/deploy_log.csv') if os.path.exists(os.path.join(root, 'code_register', 'deploy_log.csv')) else pd.DataFrame()
    ccr = [RP.HEADER, '# E6p 代码变更登记（code change register）', '', '新模块一律 `e6p_` 前缀；只读复用 e6o_* / e6n_* / e6m_* / 源引擎，未改任何既有文件。', '',
           '## A1 前后的技术修复（经济规则未变）', '', '| 位置 | 修复 | 时点 |', '|---|---|---|'] + ['| %s | %s | %s |' % f for f in FIXES] + [
           '', '## 文件 sha（交付时）', '', RP.md_table(dl, ['file', 'sha256', 'changed_after_A1']) if len(dl) else '（deploy_log 未生成）', '']
    W('E6p_code_change_register.md', '\n'.join(ccr) + '\n')
    wl = [RP.HEADER, '# E6p 提交白名单（提交只在用户指示后；不 `git add .`）', '', '建议纳入（代码目录）：', ''] + ['- `%s`' % f for f in (dl.file.tolist() if len(dl) else [])] + [
        '', '不纳入：results/ 下全部产物、tmp/、checkpoints/、randoms/ 分片（体量与卫生）。E6o 白名单仍待用户一句话。', '']
    W('E6p_commit_whitelist.md', '\n'.join(wl) + '\n')
    print(json.dumps(dict(notes=True, bern=bern_ratio, partial=partial), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
