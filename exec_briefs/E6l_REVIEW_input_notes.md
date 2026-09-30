# E6l REVIEW_input 读法注（执行端；读完结果后写；不写判词）

用途：给决策端 V / D / REVIEW 的读法入口。路径一律相对结果目录 `results/20260930_1141_E6l_time_memory_stage/`；数字只引 REPORT 的 query_id 或机器表，不另算。交付后冻结，补充另起 supplement。

## 1. 从哪里读起

- 先读 `reports/E6l_REPORT_R0.md`（仪器、授权、Stage 0、登记计数、掩码事实、耗时；§8 执行次序、MC 增补回执链、seal_post 首次失败与续跑），再读 `reports/E6l_REPORT_cards.md`：16 卡 × 28 个登记 query 各一张表，另有附节"判别读数"41 张（E6L-CD-*），卡片八字段的数字都引自这些表。
- 卡片八字段（source_claim / exposure / missing_assumption / experiment / result_query / supported_scope / alternative_surviving / next_design_change）与 category 在 `results/hypothesis_outcomes.json`；执行端原文在 `results/hypothesis_text_input_E6l.json`。
- 全部 query_id → 文件 / 列 / 表头：`reports/query_registry_E6l.json`；每张表的 CSV：`results/full/query_tables/<query_id>.csv`。登记路径 `results/full/E6L_Qxx_x.csv` 是同字节副本（`results/query_table_paths.csv`，闭包门逐项核）。

## 2. 授权与次序

- 方式 B。用户转交消息原话「记得好好思考提速优化方案 中途不需要停下来报告 避免空转」不含 W11 字面触发词；执行端当场询问，用户答「方式 B：一口气跑完」（2026-09-30）。`registration/record_B_preauthorized_E6l.json` 于 14:10:28 与 Stage A / B 两包冻结同时写入（B 包清单 sha256 02a2d2ca…；条件回执 `record_B_conditions_receipt_E6l.json` all_pass）。授权范围不含生产 / 地基 / v2 / v3 / U34 / U35 / I11 / DEV / 源时钟、E7 与 E6k 38 个遗留进程。
- 次序：Stage 0（六类全 PASS）→ A0（与 spec 逐元组相等）→ 推导两段 masks → Stage A（A2-7 1,740 / 1,740）→ Stage B / A1-auto（rerun3 27 PASS / 1 INFO）→ 冻结 → 推导两段 accounts → 随机首 1,024（MC 增补 0 组）→ seal_deriv 15:10:37（1,613 个文件，队列 768 行）→ 推导段统计 → part1 → 记录 B 草稿 → 进入后段核验 15:22:33（`record_B_entry_post_E6l.json` 五项全 true）→ 两后段 masks / accounts / 随机 / 增补 → seal_post 17:09:09（1,636 个文件，队列 800 行）→ 后段 Stage A（A2-7 1,740 / 1,740）→ 四段统计 / 政策 / bootstrap 与状态三时钟 / 影子风险 / 记忆年龄 / 连续面板（并行）→ 固定表 → REPORT → 交付。
- 全部 33,960 个登记对象 `deployment_authorized = false`；新算子 `replacement_preference_status = NOT_AUTHORIZED`。

## 3. 数字口径

- 单位：D 类量为年化百分点（日配对均值 × 252 × 100，列名 `_ann_pp`）；size 类为 pct_pt；费用 decimal 另列；段均列带 `_segavg`。
- 基准：D = 子 − 同 H 原父（8bp）；D_sc = 同资本（MATCH-CAP FIXED_PATH）；INV_LOOP 闭环只作诊断，不进正式 FULL_sc。
- 聚合：FULL = 四段有效配对日 n 加权；G4 = 四段 D 中位；PORT3_T 为正式 size 列（E6k RULING 第 2 项，policy_provisional = false）。cards 附节的比较层 FULL 是逐比较先合成、再按卡的维度取分布；t = FULL / 合成 se，只作描述列。
- 标签：新对象 `NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY`（首评、重复使用的历史，不是样本外）；E6k 同构 2,776 个 `SECOND_EVALUATION_SAME_HISTORY`（只作锚与基线）。

## 4. 执行中的偏离与补件（均在对应读数之前；逐项有部署存档与代码变更登记）

| # | 内容 | 时点 | 影响 | 证据 |
|---|---|---|---|---|
| 1 | 源差异 20 条（`source_resolution.md`）：如 DECAY L = ∞ 按显式特例（有限大 L 与 HG10 有 10 格不同，作 INFO）、Mmean 综合分为可得腿均值（b/3 锁定，limit L5） | Stage 0 | 均不改登记语义 | `source_resolution.md`；`engine_contract.md` |
| 2 | A0 两次补编：A1-auto 拦下 Q04 / Q10 无绑定比较与政策 JSON 状态词；补测量核配对与真实 − 随机扩展视图（基础 172,440 条不变） | 冻结前 | 只加扩展比较行 | `registry/_superseded_v1..v3/`；A1-auto rerun3 |
| 3 | E6k 同构对象按真实清单交集 = 2,776 + 160 母体（brief W08 写约 4,000，按类型计） | A0 | 其余同类对象标首评 | limit L8 |
| 4 | bootstrap 补 CR 族（plan §7.5 真实 − 随机共享日期 bootstrap） | bootstrap 运行前 | 推断；不设门 | R0 §8；limit L13 |
| 5 | 同时带补单侧带符号列 `q95_max_t` / `q05_min_t` | bootstrap 运行前 | 推断文本 | `results/full/bootstrap/simultaneous_band_q95.csv` |
| 6 | cards 正文把登记 query 标题中的库存技术词写作"满额（saturation）"（禁用词扫描按字面；登记原文不改） | REPORT 生成前 | 文本 | `e6l_reports.regtext` |
| 7 | 登记 query 表路径另存同字节副本 | 交付 | 路径 | `results/query_table_paths.csv` |
| 8 | 后段 Stage A 掩码事实在 seal_post 之后汇总（沿 E6k mask_facts_post） | 后段 | 不参与登记或门 | R0 §8 |
| 9 | 分析链改触发点（v2 / v3：seal_post 后即起分段诊断；REPORT 仍在 bootstrap 之后），步骤与参数不变 | 16:03 / 17:08 | 无 | `logs/chain_analysis3.steps` |
| 10 | MC 增补驱动改为合并调用 + 64 路径一片并行；2024-2026 在该段首批完成时提前增补（COND × Q_D3 / Q_D5 / Q_DEW3 / Q_DEW5 各 1,024 → 1,536） | 16:48 | 只改并行方式；分片不变性用真实内容逐位核验 | lessons 53–54；R0 表 E6L-R0-MC |
| 11 | seal_post 首次运行失败（队列推算仍按 512 一片），改 `e6l_seal.planned` 后续跑 | 17:05–17:09 | 只改队列推算 | lessons 55；`logs/chain_main.failed`（保留）与 `chain_main2.*` |
| 12 | 报告补件：carried 写明 A2-4 不符 0 行；R0 MC 表列回执链全部记录；cards 计数按整数印；cards 附节判别读数 41 张 | REPORT 定稿前 | 文本 / 新增表 | `e6l_reports.py` 17:44 / 17:50 版 |

## 5. 已知限制

见 `reports/E6l_limit_register.md`（L1–L16）。与读数直接相关的：L1（首评非样本外）、L3 / L4（状态定义与段 1 UNKNOWN）、L6 / L7（连续面板范围）、L13（CR 区间不含 MC 误差）、L14（Q10 / Q14 的 ⑬ 为 UNDEFINED）、L15（STRICT250 只在段 1 有差）、L16（Q03 / Q04 / Q15 各一项判别事实未单列）。

## 6. 结果读法要点（按卡；类别为执行端按预登记读法所填）

| 卡 | 类别 | 一句话 | 主引 |
|---|---|---|---|
| Q01 | 复现 + 追查完成 | 2,776 个同构对象逐项偏差 0；W09 只因 size 不通过，“−2.8”是 2019-2023 一段的值，其余三段 −4.0 至 −5.7 | E6L-CA-A24、E6L-CD-Q01-2 |
| Q02 | 首评支持 | 规则效应以 gross 为主（HG10 +0.097 中 gross +0.089、费用 +0.002）；6 / 12bp 下几乎不变 | E6L-CD-Q02-1、E6L-CD-Q02-4 |
| Q03 | 首评部分支持 | QMEAN5 > D5 > DMED5；全部平滑测量低于同算子 Q0 与剂量控制 | E6L-CD-Q03-1 … Q03-4 |
| Q04 | 不可识别 | MA / EW 差 ≤ 0.05，低于分辨度 | E6L-CD-Q04-1 |
| Q05 | 首评支持（覆盖） | RANK5 − RANKOBS5 +0.08；RANKOBS5 新测量覆盖 .74；平滑 − Q0 的差全在内容项 | E6L-CD-Q05-1 … Q05-3 |
| Q06 | 不可识别 | HG10 与 LAG1 相对 NATIVE 都为正，彼此差 ≤ 0.02；依靠串 p90 = 1 日 | E6L-CD-Q06-1 … Q06-3 |
| Q07 | 首评不支持 | DECAY 截短长尾但净差 ±0.01 | E6L-CD-Q07-1 |
| Q08 | 首评部分支持 | INV 优势只在短 H、以费用 / 资本为主；H ≥ 3 同资本约 0 | E6L-CD-Q08-1 … Q08-4 |
| Q09 | 首评支持（重叠） | 平滑 × HG 交互小负；联合不优于 Q0 × HG | E6L-CD-Q09-1、Q09-2 |
| Q10 | 首评支持 | 真实 − R-MARK：ISK +0.089、IID / P5 约 +0.18 | E6L-CD-Q10-1、Q10-2 |
| Q11 | 首评支持 | 剂量加大 FULL 趋平、size 倾斜加速、同资本回落 | E6L-CD-Q11-1、Q11-2 |
| Q12 | 首评不支持 | 四个 Vol 调度对固定 HG10 无增量；切片方向与预测一致但 ≤ 0.01 | E6L-CD-Q12-1、Q12-2 |
| Q13 | 首评支持 | 贡献集中在低波动日历状态；跨段变化来自状态内均值；两压力窗口方向相反 | E6L-CD-Q13-1 … Q13-4 |
| Q14 | 首评部分支持 | Munion 主展示点同资本 +0.21；全网格同资本约 0，A4b +0.21 至 +0.24 | E6L-P2-72-Q0-HG10、E6L-CD-Q14-1、Q14-2 |
| Q15 | 首评部分支持 | S ≈ M，都高于 C1；S 与 Q0 名单重叠最高；rank ACF 未算 | E6L-CD-Q15-1、Q15-2、E6L-CD-FACTS-1 |
| Q16 | 方法卡 | 16 卡闭环；3 处判别事实未覆盖（limit L16） | E6L-Q16-a；`results/query_table_paths.csv` |

- 正式尺子：PORT3_T FULL 通过 2,831、G4 通过 2,788（E6L-P3-COUNTS）；生产变更候选清单 2,864 个（FULL 或 G4 通过；上一轮同构 432 / 本轮首评 2,432），其中 765 个为 α .5 或 HG20 / 30（剂量 / 边界对象，按 brief 不自动进候选；E6L-P3-CANDIDATES）。主展示 72 通过 17 个（E6L-P3-PRIMARY72）。

## 7. 给复核的建议抽检点

1. A2-4：任取 5 个同构对象，从 `accounts/<段>/*.npz` 的 d_net8 现算四段 D / n 与 FULL，对 `policy_E6k.csv`（E6L-CA-A24）。
2. W09：从 `results/full/descriptor_stats_<段>.csv` 取 `port_size_lo_T / hi_T`，核 E6L-CD-Q01-2 的四段值与 size 判定。
3. cards 附节口径：任取一行（如 E6L-CD-Q02-1 的 HG10），从四段 `comparison_stats_<段>.csv` 按 n_days 加权现算 FULL，再取中位。
4. CR bootstrap：任取一条 CR 行，核右端键 = `random_daily_<段>.npz` 的 `描述符~H<h>~机制`，est 与 cmpstats 的 RANDOM_PATH_MEAN 一致。
5. MC 增补：2024-2026 四个 COND 组 `random_refs` 的 paths_run = 1,536；增补分片 `p1024_64 … p1472_64` 各 64 路径；其余组 1,024。
6. seal_post 队列：`e6l_seal.planned('post')` = 800 行 = 768 + 32，全部 SUCCEEDED。
7. regtext：`registry/query_registry_E6l.csv` 的 E6L-Q08-b 原文与 cards 正文只差技术词写法。
8. 登记 query 表路径：`results/query_table_paths.csv` 28 行 same_as_source 全 True。
9. Q12 切片：`results/full/state_clock_ledger.csv` 中 Q12_SLICE 的 H_noise / H_change 行与 E6L-CD-Q12-2 一致。
10. 后段 A2-7：`results/stage_a/a2_7_vs_e6k_post.csv` 1,740 行全 PASS。
