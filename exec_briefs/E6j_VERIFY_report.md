# E6j 复核报告（执行端 V + §C；VERIFY_brief v1，sha256 前缀 61c130e9；2026-09-28）

用途：按《review 分工协议》v1.1 对 E6j 整轮交付做只读复现（V）与收尾（§C）。**只回答"是不是这个数"，不写判读、不写推荐**；判读在决策端 `E6j_REVIEW.md`。S1–S5 事后口径补充另见 `E6j_REPORT_supplement_1.md`（§6）。所有产物在结果目录 `verify/`（V）与 `results_P/supplement_1/`（S）；已交付的六份 REPORT 未改。

## 0. 计数

- 本轮身份核对：六份 REPORT、REVIEW_input、addendum_1、lessons_delta、记录 B 草稿、A1-auto、brief_copy、PLAN_COPY 的 sha256 前缀、HEAD `3a4377e`（= 远端 main）、两次封存（`seal_P` 08:08:16 / 160 文件 / 120 回执；`seal_B_post` 20:10:01 / 548 / 426）、回执 1,081 —— 与 brief §0 全部相同；开工时 `verify/` 为空、`results_P/supplement_1/` 不存在。
- 只读程序 `verify_e6j_readonly.py`（sha256 前缀 65060f7002c3f84a；不 import 任何 e6j 模块、不读 cache、不读 E7 行情）+ VD 分支 `vd_prose_readonly.py`（38e5a2afb8f65ede）。
- `verify/probe_results.csv`：**462 行：REPRODUCED 459 / NOT_COMPUTABLE 2 / DIFFERS 1**；ROUNDING 4、INFO / STOCHASTIC / ADDED 22。决策端 394 行预期值全部有对应结果行（执行端另加 68 行现算）。
- 两个 NOT_COMPUTABLE 都是决策端预期值的格式问题（E02 截断、E03 文件未随附），均已用替代路径核对并一致；唯一 DIFFERS 是执行端接线问题（E01，Q17 未绑定查询），不涉及任何 REPORT 数字。
- VD 分支：`vd04_prose_binding.csv` 118 行（REPRODUCED 52 / EXEMPT 66 / DIFFERS 0）；`vd05_universal_claims.csv` 27 句（REPRODUCED 14 / EXEMPT 13 / DIFFERS 0）；EXEMPT = § 号、plan 行号、日期时间、成本标签等不计数引用，或"均值"类非全称用词。

## 1. §C 收尾

| # | 结果 |
|---|---|
| C-1 | `E6j_lessons_delta.md` 追加"§ 交付后（VERIFY）"节，第 19–27 条（见 §5） |
| C-2 | 十一份 reports/ 文件的 sha256 / md5 与 47 exec_briefs 镜像、`E6j_MIRROR.md5` 第一 / 二节逐条相同（VA01 的 11 行 ADDED 核对）；新文件进第三节 |
| C-3 | `verify/closure_gate_postverify.json`：无本轮运行中作业（0）；回执 1,081（SUCCEEDED 1,080 + FAILED 1，已由 `_rerun` 覆盖，未覆盖 FAILED 0）；`checks/closure_gate.csv` 五项仍 PASS；HEAD `3a4377e`；`git status` 只有既知 untracked 与本次新增（`verify_e6j_readonly.py`、`e6j_supp1_*.py`、决策端 VERIFY 文件） |
| C-4 | `reports/limit_register.md`（L01–L18；L01–L17 合并自 R0 §7、part1 §6、part3 §20、carried §5、addendum_1；L18 = E05，VERIFY 阶段追加） |
| C-5 | WORKLOG 两份同文（VERIFY 开工行 + 本阶段操作事实） |
| C-6 | 更早轮次遗留进程 38 个（`verify/legacy_processes.csv`，命令行已脱敏，**未动**）：28 个为 2026-09-01 起的 joblib / loky 进程池工作进程与资源跟踪进程；10 个为 2026-06-05、09-12、09-13 的 `while pgrep -f …; do sleep …` 自匹配等待循环（E6h 等轮次）。交用户决定是否清理 |
| C-7 | lessons_delta 第 16 条的 B 测时分片重算：`checks/b_test_shard_validation.csv` 5 PASS + 1 INFO（ann / yearly 与原分片逐值 0 差）—— 已完成；A1 人工判断按协议在 REVIEW 做，不补做 |
| C-8 | 决策端三件复制到 `verify/decision/`：expected.csv 17479e530414233a、prose_numbers.csv 085c0d8bb16a0588、expected_script.py 1577ec054e362bc0（与 exec_briefs 同 sha） |

## 2. 探针逐条（计数；逐行见 `verify/probe_results.csv`，探针清单 `verify/probes.csv`）

| 类 | 探针 | 行 | 复现 | DIFFERS | NOT_COMPUTABLE | 要点 |
|---|---|---|---|---|---|---|
| V-A | VA01–VA10 | 203 | 203 | 0 | 0 | 十一份报告 sha / md5 与镜像；REVIEW_input 91 个 sha 前缀（37 结果目录 + 54 源代码实物现算）；87 个 query_id 与每份报告正文集合相等；回执与两条晚写回执；两个封存 708 个文件 sha 现算 0 不符；读数文件时序 21 条"须晚于封存"全部满足（只含推导段的 5 个文件记 INFO）；政策追记 05:23:31 早于封存与首个 run_prand 回执；记录 B 条件回执早于首个后段账户回执；代码修订前后 8 个文件 sha；dryrun 三文件与追记一致、e_rand 504 个 False |
| V-B | VB01–VB08 | 60 | 60 | 0 | 0 | 锚结果 904 / 794 / 108 / 2；锚 1 重跑 220 项与 E5a 十个文件 sha、六个 pool2 行数；**6bp 锚**领导表 vs E5a 最大差 4.5e−14，**8bp 锚** 2.7988 / 6.5754 / 7.8739 / 9.6647；身份图 exact_alias；**VB07：六形态 × 四段 α = 0 母体掩码逐格解包 = E5a pool2 成员（24 / 24，仅一方有的格 0）**（格坐标 = E5a pool1 按日期 × 代码排序，每段行数 = 掩码格数）；VB06 锚账本 parquet = npz C0 四个日序列（最大差 1.9e−16）；VB08 独立重算 8 条路径的 blake2b-64 规范键 = serial.json（STOCHASTIC；掩码 / net8 哈希不重放） |
| V-C | VC01–VC21 | 80 | 77 | 1 | 2 | 政策表计数与恒等；**政策判定串独立重实现，504 行 FULL / G4 与全部子布尔列 0 不符**；三句加法 0 不符；**VC15 从账本重算 242 个对象（42 主 + 200 抽）四段 D / n / 逐年 / FULL / G4，最大差 4.4e−16**；同资本、HAC(H、20)、MDE80、turn / pos / qmiss、IID 与七机制随机列（96 组，9.97e−17）全部从账本 / 路径重算一致；B 块 200 描述符抽样、parquet 53,592 行与统计表 500 行逐列一致；领导表换手年化口径写出（E09）。DIFFERS = E01；NOT_COMPUTABLE = E02、E03 |
| V-D | VD01–VD07 | 101 | 101 | 0 | 0 | 87 张表的行列数；part3 §1–§6 576 格与 pilot_policy；part1 §0 168 格；正文数字 79 行 / 118 个数字；全称句 27 句；§7 why 逐字、§19 候选 = 通过者且 deployment_authorized 全 False、§13 网格 288 格；§15–§18、§11b、§11c 各抽 30 行；§14 别名表最大差 ≤ 1.6e−14 |
| V-E | VE01–VE09 | 18 | 18 | 0 | 0 | 领导表 fee8 = 0.08 × turnover；C0 账本 net8 = gross − 8e−4 × turn 残差 0；SM 交互 90 项；同时带端点 = FULL ± z × sd（CSV 舍入 4.8e−6）；P 诊断 CS 闭合 ≤ 2.5e−17、N1 − N0 = D_seg；CS_FROZEN 与 B 诊断闭合；B 三种合并恒等、part1 = part2 推导段；C1 归因恒等 2.7e−15（73,728 行）、NATIVE 锚 98,304 个配置日账本最大差 0、CAR-Q01 48 组中位与报告一致；资本与 6 / 12bp；计数恒等 |

## 3. E 项（全文 `verify/E_items.md`，append-only）

| E | 类型 | 一句话 |
|---|---|---|
| E01 | DIFFERS（执行端接线） | `hypothesis_outcomes.json` 的 Q17 `queries` 为空（`Q_QUERIES['Q17'] = []`），其卡片 result_query 引了 5 个查询；不涉及 REPORT |
| E02 | 决策端预期值截断 | VC11 预期串在 8,000 字符处截断；替代核对：重算表 vs 报告 P1B-Q01 逐格 0 不符 |
| E03 | 决策端预期值未随附 | VC06 random_refs_main24 指向的文件不在 verify/decision/；VC19 从路径重算 96 组一致 |
| **E04** | **读法事实，交决策端核对** | **市值 gap 方向：原生账本 `size_gap_mean`（换入 − 换出，升序秩）在 A4b 两形态四臂与并集核 S / SM / C1 上四段全部为负 = 换入更小市值（买小卖大），与"全为正、买大卖小"的说法相反**；part3 表只印绝对值，看不到方向 |
| E05 | INFO | R0 §1 的随机种子描述只写了 bootstrap 的 SeedSequence，未写置换层的 blake2b-64 + splitmix64（限制登记册 L18） |
| E06 | INFO（D09） | 回执 1,079 / 1,080 / 1,081 的来由 |
| E07 | INFO（D24） | historical_exposed 三口径：登记语义 = exposure_ledger（140 行 / 128 个描述符）；pilot_policy 60 = alias_of；Q01 文字 36 = 主母体三个评分臂 |
| E08 | INFO（D19） | `both_registered` 100 行是对称双向登记设计；A1-auto 词表缺该项；多重性按 2 |
| E09 | INFO（D08 / VC21） | turnover_ann = 252·Σturn / L；与 C0 账本 252·Σturn / n 差 L/n 因子；net6 − net8 = 0.02·turnover_ann·L/n |
| E10 | INFO（D26） | R-COND 分层按源码：行业 × size3 × 旧 K3 → 行业 × 旧 K3 → 行业 → 全池，格内 ≥ 2，不重叠，与 plan 一致 |
| E11 | INFO（执行端自身操作） | 删除了本次 verify/ 下的分组试跑输出（违反只增不删，非交付 / 封存文件）；VD04 汇总行首次读错列后改正 |

## 4. 闭包门（复核后）

`verify/closure_gate_postverify.json`：运行中 E6j 作业 0；回执 1,081、未覆盖 FAILED 0；closure_gate 五项 PASS；两个封存 0 不符（VA05）；HEAD `3a4377e` 至本次白名单提交前未变；`task_status/` 与 `reports/query_registry.json` 未被 VERIFY / S 改动（S 的回执写 `results_P/supplement_1/receipts/`，query_id 写 `query_registry_supplement_1.json`）。

## 5. lessons_delta 追加（`E6j_lessons_delta.md` "§ 交付后（VERIFY）"节，第 19–27 条）

19 市值通道只实现编辑层、漏了 plan L567 的四层输出与 L311 的实际权重暴露差；20 `both_registered` 未进 A1-auto 词表；21 historical_exposed 三口径并存；22 回执计数三个数；23 方法卡 Q17 未绑定查询；24 part3 只印 |gap| 看不到方向；25 R0 随机种子描述不完整；26 复核中删除了自己的试跑输出；27 S 分支的两处口径披露（中间文件覆盖一次、S3 回归压缩缺失日）。

## 6. S1–S5 补充（指向）

`E6j_REPORT_supplement_1.md`（结果目录 `results_P/supplement_1/`，sha256 前缀 727f4892944e7116；13 个 query_id S1-Q01…S1-Q13，登记在 `query_registry_supplement_1.json`），全部为**事后口径**，不替代登记结果。S 分支自测 13 / 13 PASS（C0 子 − 母四层为 0；编辑层 gap 逐日重算与 summary.csv 最大差 1.07e−14；size 百分位与生产函数逐位同；登记口径下 S2 复现 pilot_policy 288 行 0 不符）。S 分支披露、需决策端定口径的四处：① 领导词表门 A（每日）/ B（段均值）在母体上也不满足、C（不劣于母体）为执行端事后定义的变体，三者都待决策端与用户定；② 组合层门与领导门对 288 网格对象用目标权重（H5 滚动持仓只算 24 主对象）；③ S3 回归为做 HAC 把缺失日压缩为相邻样本，与 plan §8.5a 的均值 SE 口径不同；④ S4 偏离只核形成日目标权重。
