# E6j 限制登记册（VERIFY C-4；执行端，2026-09-27）

用途：把 `E6j_REPORT_R0.md` §7、`E6j_REPORT_part1.md` §6、`E6j_REPORT_part3.md` §20、`E6j_REPORT_carried.md` §5 与 `E6j_delivery_addendum_1.md` 中的限制条目合并为一张编号表。原文逐条摘录、不改任何 REPORT；VERIFY 阶段新增条目只在表尾追加（L18 起）。状态词：**有效**（限制仍适用于所列读数）/ **已补**（后续文件已补齐，指明出处）/ **待补**（VERIFY brief §6 S 项或后续轮次）/ **待裁定**（用户裁定项）。

| 编号 | 原文出处 | 限制（原文摘录，必要处缩写） | 适用对象 | 影响的 query_id | 状态 |
|---|---|---|---|---|---|
| L01 | R0 §7 第 1 条 | Stage 0 第 4 项的真实字段检验在四段上计算了 J 原值、覆盖与别名统计（无任何收益、无账户）；B 包后段账户与收益关联统计仍按记录 B 生效条件执行 | Stage 0 第 4 项；B 包后段 | R0-Q12、R0-Q13 | 已补：记录 B 条件回执 2026-09-27 04:23:40 三条全过（`registration/record_B_conditions_receipt.json`），后段读数见 part2 |
| L02 | R0 §7 第 2 条 | W03 所引 E6i 投入资金 0.317 / 0.520 / 0.700 / 0.833 的出处表未定位；同一账本上两种定义实算见 R0-Q06 | 主母体 A4b_CVRv5（R1）投入资金展示口径 | R0-Q06 | 有效（出处表仍未定位） |
| L03 | R0 §7 第 3 条 | 段首事件钟沿 E6i：预热期无已知触发，段首 spell / 触发被截断（登记为限制，不改源） | 事件时钟类测量（B5 RARPRE / R_ev / U 的 LT / SE 时钟；spell_entry） | R0-Q11、R0-Q13；P1-Q09；P2-Q01（B5 行） | 有效 |
| L04 | R0 §7 第 4 条 | 下一步：Stage A 两个登记包同时冻结 → A0 登记 → Stage 1 推导段测量诊断 → profile 后报并发与时长 | 流程待办 | — | 已补：Stage A 2026-09-27 03:14:05；Stage 1 已跑；"profile 后报并发与时长"未按时做，记 lessons_delta 第 11、17 条 |
| L05 | part1 §6 第 1 条 | 随机参照三类（R-SCORE-IID / R-COND / EDIT-ENTRY，1,024 路径起）与 COMMON_SUPPORT 四账户、TRANSPORT、剂量控制（B3-C）在 part1b 补；本文件读数都是"子 − 母"原生增量 | part1 全部表 | P1-Q01–P1-Q14 | 已补：part1b（P1B-Q01–P1B-Q06） |
| L06 | part1 §6 第 2 条 | 一个 2010-2014 R2 × B3C 的 32 路径随机分片是测时样本，其路径作为该配置 1,024 路径中的前 32 条保留，不单独读数 | 2010-2014 R2 × B3C 随机参照 | P1B-Q01–P1B-Q03（该配置行） | 有效；该分片以最终代码重算逐值一致（`checks/b_test_shard_validation.csv` 5 PASS + 1 INFO） |
| L07 | part1 §6 第 3 条 | 两推导段已在 E6i 中暴露于同源母体的成员选择；推导段读数不是样本外证据 | B 包推导段全部对象 | P1-Q01–P1-Q14；P1B 全部；P2-Q06（推导列） | 有效 |
| L08 | part3 §20 第 1 条 | 四段非样本外；S 方向为 E6i 对照方向事后转正（direction_2of1）；S / M / C1 与两列对象在主母体上 = E6i 已见账户 | P 包全部对象；主母体 S / M / C1 / K_rarpre / K_samt20 | P3-Q01–P3-Q08、P3-Q20、P3-Q21 | 有效 |
| L09 | part3 §20 第 2 条 | 随机参照为 R-MATCH-SRC（Z-MAP basic 匹配条件，E6j 稳定哈希种子）；其余机制（P5 / COND / COND_IID / EDIT / EDIT_IID / EDITB）只作诊断 | P 包 e-随机与随机列 | P3-Q01–P3-Q06（rand_* 列）、P3-Q22、P3-Q29 | 有效 |
| L10 | part3 §20 第 3 条 | 冲击为源平方根模型的事后加性成本（不改库存）；影子库存账户只对主对象与母体做 H5 | f 条件、冲击列、影子库存 | P3-Q01–P3-Q06（FULL_imp / f）、P3-Q17、P3-Q24 | 有效（与 L11、L12 同源） |
| L11 | carried §5 第 1 条 | 影子库存账户（ideal / X1）只对 P 主对象与母体做 H5（part3 §11）；买卖标志缺失按"可成交"处理（源默认 unknown_tradable = True） | 影子库存账户 | P3-Q17、P3-Q24 | 有效 |
| L12 | carried §5 第 2 条 | 冲击为源平方根模型的事后加性成本，不改库存；κ 与 A 是情景，不是已确认的实际资金或容量 | 冲击列与 f 条件；领导表 | P3-Q01–P3-Q06（FULL_imp / f）、CAR-Q02 | 有效 |
| L13 | addendum_1 §1 | 市值通道现行口径为编辑层（换入 / 换出中位差，逐段 \|mean_t gap_t\| ≤ 5 百分位点）；plan 要求并列的"实际权重暴露差"（plan 第 311 行；第 567 行四层输出）未产出 | P 包全部主臂对象的 size_status 与政策串 | P3-Q01–P3-Q08、P3-Q21、P3-Q35 | 待补：VERIFY brief §6 S1（四层暴露）、S2（事后口径重评分）；登记结果不改 |
| L14 | addendum_1 §2 | 主母体增量与粗风格（市值 / 行业 / 旧 K 档）对齐高度重合（R-COND 参照）；放宽市值通道只改变通过与否，不改变这条读法 | 主母体四臂主配置 | P3-Q01（rand_COND / rand_IID 列）、P3-Q16 | 有效；S3（size 中性 α）并列 |
| L15 | addendum_1 §3 | 执行端自定口径（MC_Z = 2、市值聚合方式、e-资本 0 容差 1e−9）不是用户逐式批准的数值 | P 包政策判定 | P3-Q01–P3-Q08、P3-Q22 | 待裁定 |
| L16 | addendum_1 §3 | 领导确认过的 1% / 3% 相对基准偏离约束本轮没有按该口径计算任何对象 | P 包主配置对象 | — | 待补：VERIFY brief §6 S4 |
| L17 | addendum_1 §5 | 四个标签不变：mechanism_status 未分离；replication_status 主母体 S / M / C1 为复现；deployment_authorized = false；补充计算前后都不改生产、不读 E7 | 《生产变更候选清单》 | P3-Q21、P3-Q35 | 有效 |

VERIFY 阶段新增（append-only，L18 起）：

| 编号 | 出处 | 限制 | 适用对象 | 影响的 query_id | 状态 |
|---|---|---|---|---|---|
| L18 | VERIFY VD04（`verify/vd04_prose_binding.csv` R0:50） | R0 §1 环境句"随机：blake2b-128(canonical_json(key)) -> SeedSequence"只描述 `rng_for`（bootstrap 等）；P / B 随机置换层实际为 blake2b-64 路径键 + splitmix64 计数器（各随机回执 generator 字段） | R0 §1 文字 | R0-Q01 | 有效（文字口径，读数不受影响） |
