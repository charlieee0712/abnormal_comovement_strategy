# E6i 复核报告（VERIFY_report；执行端，2026-09-26 47 时间）

用途：按《review 分工协议 v1.0》（`exec_briefs/REVIEW_protocol_v1.md`，sha256 `1bde2758…`）与 `exec_briefs/E6i_VERIFY_brief.md`（sha256 `e63cfe64…`），报告执行端 §C 收尾与 V 探针的结果：**报告里的每个数是不是这个数**。本报告**不含推荐、不含判读**；DIFFERS 只印不修，不改 REPORT；影响与读法由决策端在 REVIEW 判断。执行端本轮唯一推荐仍是 part3 §8–§9。

- 只读程序：`verify_e6i_readonly.py`（sha256 `eb75033fcbd9e649…`，2,786 行）；结果目录副本 `verify/verify_e6i_readonly.py`，仓库副本随本报告提交。
- 运行：47，2026-09-26 03:38:59–03:48:39，闭包门 → A → B → C0 → C → D → E 顺序单进程（taskset，BLAS 4 线程）；各阶段 4 s / 6 s / 172 s / 264 s / 118 s / 8 s / 5 s。`verify/probe_results.csv` 只含这一次的结果。
- 产物（结果目录 `verify/`）：`probes.csv`（brief §5 机器转录 45 条）、`probe_results.csv`（1,443 条子检查，sha256 `ca362100…`）、`E_items.md`（`e7558ae0…`）、`closure_gate.json`、`D1_query_text.csv`、`D2_rebuild.csv`、`D5_universal_sentences.csv`、`E6_no_random_control.csv`、`work/`（从日账本重算的逐描述符统计等中间表）、`verify.log`、`run_*.log`。

---

## 风险状态判决表（协议 §7.8）

| 问题 | 结论（事实） |
|---|---|
| ① 有什么处于风险中吗（生产 / 地基 / U34 / E7 / 冻结对象） | **没有被碰**。只读程序只写 `verify/`；没有 import e6i 模块（每阶段结束自检 `sys.modules`）；没有读 `cache/`、没有读 E7（>2026-03-27）数据文件；四地基与 e6e–e6h 钉住脚本（`source_manifest.json` 的 `foundation_readonly` 等各组，共 100 个）当前 sha 与登记一致（A12），重放期间钉住引擎的影子缓存目录无新增 / 改动文件（B1）；封存的 2,865 个后段文件逐个 sha 与回执一致（A8(i)）；project_core 已跟踪文件无改动（闭包门）。生产候选库、U34 / U35、v2 / v3 展示候选所在目录不在本程序的写路径内；本程序没有对这些目录做内容核对。 |
| ② 数字是否复现（计数） | 1,443 条子检查：**REPRODUCED 1,424 / DIFFERS 13 / NOT_COMPUTABLE 6**；无 ROUNDING、无 STOCHASTIC 标记。45 个 V 探针：35 个全部复现；8 个含 DIFFERS（A8、B2、C1、C12、D1、D2、D5、E6）；2 个部分 NOT_COMPUTABLE（C13、E1）。13 条 DIFFERS 与 6 条 NOT_COMPUTABLE 逐条见 §3（E01–E12）。 |
| ③ REPORT 没展示什么 | (i) RO / RS 的 `state=random_state` 焦点臂以 Python 内置 `hash(descriptor_id)` 取随机种子、运行环境未设 `PYTHONHASHSEED`：C2 冲击表里这 240 个子账户（四段各 60）与主账本不同，主账本这些臂不能由重跑逐位重放（E04）；(ii) `query_ids_part1.csv` 的 118 条问题卡事实句不在五份 REPORT 正文（E06）；`Q13-SIGN` 一个 id 对应两句不同的话（E05）；(iii) part2 §4 表头括注"FOURARM / TPAIR 等确定性臂无随机对照"与同表 TPAIR 行有值不符（E11）；(iv) 两句全称句逐格计数不成立或依读法而定（E09、E10）。 |
| ④ 建议 | 无（VERIFY 不给建议）。 |

---

## §0 计数

**按类别（子检查粒度）**

| 类别 | 子检查 | REPRODUCED | DIFFERS | NOT_COMPUTABLE |
|---|---|---|---|---|
| V-A 闭包与指纹 | 175 | 173 | 2 | 0 |
| V-B 服役集与锚 | 291 | 289 | 2 | 0 |
| V-C 统计从账本与表重算 | 840 | 836 | 3 | 1 |
| V-D 报告 ↔ 表 | 111 | 103 | 4 | 4 |
| V-E 装配恒等式 | 26 | 23 | 2 | 1 |
| 合计 | 1,443 | 1,424 | 13 | 6 |

（V-C 含 C0 阶段写的 263 条：39,800 个描述符 x 9 个口径从日账本全量重算与 bootstrap 重放；V-E 含 C0 阶段写的 1 条 E2 逐日恒等。）

**按探针**：45 个（A 14、B 3、C 17、D 5、E 6）。判定规则：任一子检查 DIFFERS → 探针 DIFFERS；无 DIFFERS 而有 NOT_COMPUTABLE → "部分 NOT_COMPUTABLE"；其余 REPRODUCED。

**容差**：全部按 brief §2 预注册执行，没有事后放宽（计数 / sha / 时间先后 EXACT；从账本重算的值 |d| ≤ 1e−12；钉住引擎重放 ≤ 2.3e−15；印出值按印出位数；同 seed bootstrap EXACT；恒等式残差 ≤ 1e−12；D1 为"EXACT 字符串（数字部分）"）。V 程序首跑后发现自己有两处比预注册更严的实现（B1 用 EXACT、D1 用全字符串），已改回预注册口径，见 §2.2。

---

## §1 §C 收尾结果

| # | 项 | 结果 | 产物 / 位置 |
|---|---|---|---|
| C-1 | 经验增量 | 完成：仪器 8 条、口径 8 条、流程（含 part3 §5 八条）、复盘候选 4 条、执行端 E6h / E6i 写进共享 memory 的 21 条逐条列表、协议建议、已知未做项；§8 追加 VERIFY 阶段内容。**自此执行端不再写共享 memory**（本轮 VERIFY 期间未写） | `exec_briefs/E6i_lessons_delta.md`（三处镜像：本地、47 `exec_briefs/`、结果目录 `verify/`） |
| C-2 | REPORT 冻结 | 完成（2026-09-26 01:53）：五份 REPORT + 记录 B 草稿 + brief（`brief_copy.md`）三处、plan（`PLAN_COPY.md`）两处（47 仓库无 `exec_briefs/plans/`）的 md5 / sha256，三处（两处）逐字节一致；本次交付追加第二节列 VERIFY 交付物 | `exec_briefs/E6i_MIRROR.md5` + `verify/E6i_MIRROR.md5` |
| C-3 | 闭包门 | 进入 V 的闭包门 2026-09-26 01:52:14 **PASS**（§4）；VERIFY 交付后的指纹写 `verify/handoff_fingerprint_postverify.json`（原 `registry/handoff_fingerprint.json` 不改），交付后闭包门写 `verify/closure_gate_post_V.json`，都在本报告 push 之后运行，结果记 WORKLOG | `verify/closure_gate.json` 等 |
| C-4 | limit_register | L1–L17 内容与 A14 核对一致、状态不变；VERIFY 阶段新增只 append（L18 起） | `reports/limit_register.md` |
| C-5 | worklog | VERIFY 阶段操作事实（时间、程序 sha、耗时、产物）写入远端与本地 WORKLOG，同文 | 远端 + 本地 |
| C-6 | 目录 | `domains/README.md`（空目录说明：M1 / M2 实际在 `accounts/` 与 `m2/`）与 `reports/E6i_REPORT_part1_tables.README.md`（标明 part1 表集为内部全量表）各一行，01:56:24 写 | 结果目录 |
| C-7 | 已知未做项 | A1 未执行（决策端义务）、8 个只 Stage 1 成员（L6）不解封：只在 lessons_delta §7 记事实，不补做 | — |

---

## §2 探针逐条表

判定列的"部分 NC" = 部分 NOT_COMPUTABLE。逐子检查行（预期 / 重算 / 差 / 容差 / 输入文件 sha 前缀 / 函数 / 说明）在 `verify/probe_results.csv`。

| id | 探针（brief §5） | 子检查 | REP | DIF | NC | 判定 | E 项 |
|---|---|---|---|---|---|---|---|
| A1 | 三处镜像 | 24 | 24 | 0 | 0 | REPRODUCED | |
| A2 | 交接指纹 | 7 | 7 | 0 | 0 | REPRODUCED | |
| A3 | 白名单提交 | 7 | 7 | 0 | 0 | REPRODUCED | |
| A4 | A0 四版计数 | 9 | 9 | 0 | 0 | REPRODUCED | |
| A5 | 修订时间戳先于结果读出 | 4 | 4 | 0 | 0 | REPRODUCED | |
| A6 | preregistration | 4 | 4 | 0 | 0 | REPRODUCED | |
| A7 | 记录 B | 14 | 14 | 0 | 0 | REPRODUCED | |
| A8 | 首次观察封存 | 10 | 8 | 2 | 0 | DIFFERS | E01 |
| A9 | 状态表求和 | 30 | 30 | 0 | 0 | REPRODUCED | |
| A10 | 守卫与契约 | 7 | 7 | 0 | 0 | REPRODUCED | |
| A11 | Stage 3 代码改动 | 43 | 43 | 0 | 0 | REPRODUCED | |
| A12 | 源 manifest | 3 | 3 | 0 | 0 | REPRODUCED | |
| A13 | coverage 与目录对照 | 7 | 7 | 0 | 0 | REPRODUCED | |
| A14 | limit_register | 6 | 6 | 0 | 0 | REPRODUCED | |
| B1 | 母体基线 16 行 | 177 | 177 | 0 | 0 | REPRODUCED | |
| B2 | 母体重放 | 100 | 98 | 2 | 0 | DIFFERS | E02 |
| B3 | 源锚 / 算子锚 / 稀疏引擎锚 | 14 | 14 | 0 | 0 | REPRODUCED | |
| C1 | part2 §2 路线 × 母体 33 行 | 289 | 288 | 1 | 0 | DIFFERS | E03 |
| C2 | K 槽位 1,134 集合与中位 | 88 | 88 | 0 | 0 | REPRODUCED | |
| C3 | 两期为正 11 成员 | 38 | 38 | 0 | 0 | REPRODUCED | |
| C4 | P20 | 9 | 9 | 0 | 0 | REPRODUCED | |
| C5 | P21 | 20 | 20 | 0 | 0 | REPRODUCED | |
| C6 | RV 反向、RC 槽位 | 7 | 7 | 0 | 0 | REPRODUCED | |
| C7 | NW 区间计数 | 6 | 6 | 0 | 0 | REPRODUCED | |
| C8 | 同步带 | 9 | 9 | 0 | 0 | REPRODUCED | |
| C9 | Z-MAP | 54 | 54 | 0 | 0 | REPRODUCED | |
| C10 | M2 | 47 | 47 | 0 | 0 | REPRODUCED | |
| C11 | C1 | 55 | 55 | 0 | 0 | REPRODUCED | |
| C12 | C2 | 68 | 66 | 2 | 0 | DIFFERS | E04 |
| C13 | R0 | 35 | 34 | 0 | 1 | 部分 NC | E12 |
| C14 | 延续 | 13 | 13 | 0 | 0 | REPRODUCED | |
| C15 | vs H5 | 70 | 70 | 0 | 0 | REPRODUCED | |
| C16 | 逐年 | 25 | 25 | 0 | 0 | REPRODUCED | |
| C17 | 决策层与 SWAP 分布 | 7 | 7 | 0 | 0 | REPRODUCED | |
| D1 | query_id 文本 | 13 | 11 | 1 | 1 | DIFFERS | E05 / E06 |
| D2 | query_id 重算 60 条 | 65 | 62 | 1 | 2 | DIFFERS | E07 / E08 |
| D3 | 表头十项 | 10 | 10 | 0 | 0 | REPRODUCED | |
| D4 | 禁用词 | 5 | 5 | 0 | 0 | REPRODUCED | |
| D5 | 全称句 | 18 | 15 | 2 | 1 | DIFFERS | E09 / E10 / E12 |
| E1 | Δgross = 进入 + 退出 + 共同 | 2 | 1 | 0 | 1 | 部分 NC | E12 |
| E2 | net8 = gross − 8e−4·turn；Δnet8 = Δgross − 8e−4·Δturn | 5 | 5 | 0 | 0 | REPRODUCED | |
| E3 | 四臂交互 = Δ_AB − Δ_A − Δ_B | 9 | 9 | 0 | 0 | REPRODUCED | |
| E4 | C1 分解 d_deploy = cap_part + sel_part | 2 | 2 | 0 | 0 | REPRODUCED | |
| E5 | 计数闭合 | 4 | 4 | 0 | 0 | REPRODUCED | |
| E6 | Z-MAP 行闭合 | 4 | 2 | 2 | 0 | DIFFERS | E11 |

### 2.1 各类要点（事实）

- **V-A**：五份 REPORT 与 B 草稿三处逐字节一致（sha 前缀与 brief 逐字相同）；交接指纹记录的 HEAD = 当前 HEAD = `569c810`，66 个 e6i blob 逐项一致；白名单提交 f8bb4d9（72 个文件，白名单外 0）/ 0d0f5cd / 569c810 的文件集合与记录一致；A0 四版 35,104 / 35,176 / 35,656 / 37,360 行，v1.2 → v1.3 只新增 1,704（RA 1,656 + M2 48）、0 删 0 改；v1.3 登记早于 RA 补跑的首个作业与账户文件，exposure_ledger 有 v1.2 信息暴露条目；preregistration 落盘早于首个 Stage 2 作业；记录 B 的 sha、批准 id / 时间 / 用户原话、包数、描述符数、受保护成员集合一致；封存 2,865 个文件逐个 sha 一致；Z-MAP 后段首个作业晚于批准；Stage 2 / 3 状态表四段各 35,384 SUCCEEDED、FAILED_TECH 0；守卫 25 / 25、7 / 7、48 / 48，suffix_guard 1,952 项 0 失败，plan 契约 61 / 61，EDGE vendor 5 / 5；Stage 3 改动 12 个修改 + 5 个新文件的改前 / 改后 sha 与 diff 一致；source_manifest 100 个源脚本当前 sha 一致、4b1ee8e..569c810 之间无改动；coverage 与 layout_map 计数一致；limit_register L1–L17 齐全。例外见 E01。
- **V-B**：四母体 x 四段母体（pool0 人数、持仓、投入资金、gross、net8）用钉住引擎重放，与 `registry/mother_needs_*.csv` 与 part3 §0 表一致（≤ 1e−12）；六个 H 的重放与账本母体逐日一致、NaN 位置相同，96 个 (段, 母体, H) 中 95 个 ≤ 2.3e−15（E02）；特征锚 19 / 19、算子锚 65 / 65、标签锚 0.0 bp、稀疏引擎锚 168 / 168（两段）；按构造等于母体的焦点臂（`state=all_on` / `old`）四段 312 / 312 逐日 dnet8 恒为 0，其余逐日恒为 0 的只有当段每年都选零修改的 M2 程序（24 / 226 / 125 / 753）。
- **V-C**：39,800 个描述符 x 9 个口径（四段、推导合并、后段合并、四段合并、去 2015+16、去 2024+）的逐描述符统计从日账本全量重算，与 statistics 表逐列一致（数值列 max|d| 7.1e−15，状态词 / 区间排除 0 逐个一致）；bootstrap 按同 seed 重放，728 个家族临界值一致（max|d| 1.3e−15）；part1 / part2 输入面板逐列一致；vs 生产 H5 七个统计表全量一致；C1–C17 所列 REPORT 印出值与表值逐格一致。例外见 E03、E04；C13 首表原值不可算（E12）。
- **V-D**：五份 REPORT 正文里的 117 + 34 条 query_id 句与存档现算文本逐字一致，正文里没有无存档的〔id〕；REVIEW_input 235 条与存档数字部分一致；D2 抽到的 63 个 id（64 句）中 62 句用本程序的重算值按生成器公式重建后逐字一致；94 张表十项表头齐全（R0 20 / part1 28 / 1b 7 / part2 22 / part3 17）；禁用词 0；全称句 108 句列出并按覆盖分类。例外见 E05–E10、E12。
- **V-E**：日账本 net8 = gross − 8e−4·turn 逐日残差 6.9e−18；四段表层 d_net8 = net8 − parent_net8 ≤ 7.1e−15；四臂交互从日账本重算，推导 216 + 后段 288 行与表一致，推导 full |t| > 2 为 12 / 72（正 8、负 4），后段合并 t > 2 为 32、t < −2 为 0；C1 资本分解恒等残差 ≤ 1e−12；A0 37,360 = 35,384 + 1,512 + 464、统计表 39,800 = 35,384 + 3,024 + 1,392、part2 §2 各路线 n、M2 modified + zero = 1,392 / 1,856 全部闭合。例外见 E11、E12。

### 2.2 V 程序的更正记录（首跑后；实现错误，未改预注册容差）

1. 闭包门：FAILED receipt 认"被同名 `_rerun` 成功覆盖"；m2boot / m2_samples 的 receipt 按 `n_programs` 计数。
2. A11：diff 文件名与 runtime 脚本位置找错（13 个假 DIFFERS）。
3. B1：首版对浮点日均值用 EXACT，改为 brief 预注册的 1e−12。
4. B3：首版方向与 brief 相反（找逐日恒为 0 的描述符），改为"恒等臂 → 逐日恒为 0"。
5. C0：集合比较改为记录对称差个数（首版把 id 列表写进结果）。
6. C12：说明文字里未转义的 `%` 让一次运行中途退出；C13：两级表头 CSV 按单级读。
7. D1：REVIEW_input 比较首版用全字符串，改为 brief 预注册的"数字部分"。D2：抽样行首版把期望写成实际值 45，改为预注册的 42（结果 DIFFERS，E07）。D5：覆盖分类改为句内〔id〕或按"报告 + 行 + 关键片段"登记。
8. `flush_results` 首版按 probe_id 替换，会删掉别的阶段写的同名 probe 行；改为按阶段替换，终版程序全链重跑一次（本报告的全部计数来自这一次）。

### 2.3 独立性范围与对 brief §1 的偏离（披露）

- 为转录汇总口径（主方向集合、伴随账户正则、各表的分组 / 过滤 / 格式串），V 阶段读了 e6i 报告生成器与统计脚本的**源码文本**（没有 import、没有执行）。brief §1 的封闭输入清单没有列这些文件。因此 V 能抓到计算与转录错误，抓不到"生成器口径本身写错"；D2 的句子是按生成器公式、用本程序的重算值重建的。
- V 的数值全部来自日账本、存档表与钉住引擎重放。D2 的 P3-CARDS / P3-DELTA 与 D1 的事实块因输入不在清单记 NOT_COMPUTABLE（E06、E08）。
- 协议 §9 写程序名 `verify_readonly_e6i.py`，brief §1 / §7 写 `verify_e6i_readonly.py`；本轮按 brief。

---

## §3 E 项（append-only；全文同 `verify/E_items.md`）

### E01　A8(ii)：m2 后段台账的写入时间早于首次观察回执

- **探针**：A8(ii)，2 个子检查 DIFFERS。
- **预期（brief §5 A8）**：`statistics/post/*`、`reports/part2_tables/*`、`m2/2019-2023/ledger_*`、`m2/2024-2026/*` 的最早 mtime 均 ≥ 回执时间 2026-09-24 14:48:50。
- **重算**：`statistics/post/*` 与 `reports/part2_tables/*` 满足（REPRODUCED）；`m2/2019-2023/ledger_*` 最早 mtime 2026-09-24 04:44:37，`m2/2024-2026/*` 最早 04:54:15，均早于回执。
- **同时核到的事实**：这两组文件全部在回执 `registry/first_look_receipts.json` 的封存清单内（2019-23 组 28 / 28；2024-26 组 58 项中 57 个是文件且都在清单内，另 1 项是 `samples/` 目录）；A8(i) 封存 2,865 个文件逐一重算 sha 0 不符；回执 `rule` 字段原文为"两后段同一 manifest 全部计算后封存; 本回执之前不读任何后段结果; 不看 2019-23 后改 2024-26"。
- **判定**：DIFFERS（相对 brief 预注册的先后关系）。

### E02　B2：2015-2018 逐日 net8 最大差 2.338e−15，超过预注册 2.3e−15

- **探针**：B2，2 个子检查 DIFFERS（`checks/engine_anchor_2015-2018.json` 的 48 行最大值；本程序重放 2015-18 A06 H1 对账本母体序列）。
- **预期（brief §2 / §5 B2）**：逐位或 ≤ 2.3e−15（REPORT R0 §1 印"1.2e−15 / 2.3e−15"）。
- **重算**：两处都是 2.338434350671048e−15；NaN 位置一致；同段其余 23 个 (母体, H) 的重放与账本逐日差都在 2.3e−15 以内。
- **判定**：DIFFERS。未放宽容差。

### E03　C1：part2 §2 路线 x 母体表是 35 行，brief 写 33 行

- **探针**：C1（1 个子检查 DIFFERS）。
- **预期（brief §5 C1）**：33 行。
- **重算**：35 行；`reports/part2_tables/T2_route_mother_post.csv` 与 REPORT part2 §2 印出表都是 35 行；35 行 x 12 列逐格与存档表、与 REPORT 印出值一致（REPRODUCED）。
- **判定**：DIFFERS（相对 brief 转录的行数）。

### E04　C12：C2 冲击表里 `state=random_state` 焦点臂的子账户与主账本不同

- **探针**：C12，2 个子检查 DIFFERS。
- **重算**：`carried/summary/C2_children_delta.csv` 的 `d_net8_ann` 与本程序从日账本重算的分段 `d_net8_ann`：
  - `state=random_state` 焦点臂以外的全部子描述符：max|d| ≤ 1e−12（REPRODUCED）。
  - `state=random_state` 焦点臂：每段 60 个（RO FOCAL_NEW gap_pos / gap_neg 36 个 + RS FOCAL_NEW weak_or_dispersed 24 个），四段 240 个**全部**不同；max|d| 2010-14 0.323 / 2015-18 0.757 / 2019-23 0.675 / 2024-26 0.889（年化百分点）；这些行的母体列 `m_net8_ann` 与母体账户一致，差全在子账户 net8。
  - `C2_T6_impact_delta.csv` 的 640 个 (段, 路线, 母体, H) 格中，用账本值替换这些子账户后 `d_net8_ann` 变化的有 18 格（2010-14 RO / RS、2019-23 RO、2024-26 RO），max|d| 0.0788。
  - REPORT part3 §3 第一表（44 行）的 `d_net8_ann` 列用账本值重算后，按印出位数不变（REPRODUCED）；该表由 C2_T6 汇总的另外三列也逐格一致（表层）。
- **同时核到的事实**：`e6i_stage2.py:152` 以 `np.random.default_rng(abs(hash(r['descriptor_id'])) % (2 ** 32))` 取 random_state 臂的随机状态；项目脚本、`runtime/` 目录与 47 登录环境中都没有设置 `PYTHONHASHSEED`。
- **判定**：DIFFERS。

### E05　D1：query_id `Q13-SIGN` 在两个存档文件里对应两句不同的话

- **探针**：D1（query_id 唯一性，1 个子检查 DIFFERS）。
- **重算**：6 个存档文件中重复的 id 1 个：`Q13-SIGN` 在 `query_ids_part1.csv` 是"两段同号 88.3%（同为正 172、同为负 2880）"，在 `query_ids_part1_text.csv` 是"K_rar SLOT 主方向两段中位 -0.084 / -0.208、竞争方向 +0.087 / +0.550"。REPORT part1 正文里的〔Q13-SIGN〕是后一句。REVIEW_input 的 235 行因此只有 234 个唯一 id。
- **判定**：DIFFERS。两句的数字各自按 D2 公式重算都一致（见 D2）。

### E06　D1：`query_ids_part1.csv` 的 118 条问题卡事实句不在五份 REPORT 正文

- **探针**：D1（1 个子检查 NOT_COMPUTABLE）。
- **事实**：这 118 条（Q1-N … Q15-STR）由 `reports/part1_facts.md` 承载（part1 REPORT 第 3 行指向该文件）；五份 REPORT 正文里只出现其中 1 个 id（`Q13-SIGN`，见 E05）。`part1_facts.md` 不在 brief §1 封闭输入清单，所以"现算文本 = 正文句"无法按 brief 口径核对。其余 5 个存档文件的 117 条 + R0 的 34 条全部逐字出现在对应 REPORT 正文（REPRODUCED）。
- **判定**：NOT_COMPUTABLE。

### E07　D2：必做条数与 brief 预注册不同

- **探针**：D2（抽样行 1 个子检查 DIFFERS）。
- **预期（brief §5 D2）**："必做 42 条：P1-S-*（10）、P2-S-*（10）、P3-S-*（7）、…"。
- **重算**：按 brief 列出的规则取到 45 条（P2-S-* 实有 12 条：RUN / ALL / K / K2 / PERS / T / P20 / P21 / RS / V / C / M2）；随机 18 条按"其余 id 排序后 `default_rng(20260925).choice(n, 18, replace=False)`"取自 189 个唯一 id（REVIEW_input 235 行、234 个唯一 id，见 E05）。抽到：P1B-FA、Q13-ZMAP-15-18、Q14-SIGN、Q2-STATE、Q7-H、Q15-BY、P3-FAM-KM、Q7-SIGN、Q13-SIGN、P2-REP、P1B-S-FA、Q15-SIGN、P3-FAM-T、Q12-ACC、Q15-H、P3-FAM-Q18、Q4-CI、Q8-M1。
- **判定**：DIFFERS（条数）。63 个 id（64 句，Q13-SIGN 两句）中 62 句按生成器公式、用本程序的重算值重建后与存档文本逐字相同（REPRODUCED），2 句见 E08。

### E08　D2：P3-CARDS、P3-DELTA 不能重算

- **探针**：D2（2 个子检查 NOT_COMPUTABLE）。
- **事实**：两句所引的 `reports/hypothesis_outcomes.json`、`reports/factor_iteration_delta.csv` 不在 brief §1 封闭输入清单。
- **判定**：NOT_COMPUTABLE。

### E09　D5：part1 Q4「真实状态并不优于随机状态」有 1 / 4 格不成立

- **探针**：D5（1 个子检查 DIFFERS）。
- **REPORT 原句（part1 Q4 读法）**："……而**真实状态并不优于随机状态**（见上表 real_state 与 random_state）"。
- **重算**：RO FOCAL_NEW 焦点臂按 (方向, 段) 的描述符中位（real_state / random_state）：gap_neg 2010-14 −0.121 / −0.107；gap_neg 2015-18 **−0.214 / −0.233**；gap_pos 2010-14 −0.235 / −0.142；gap_pos 2015-18 −0.292 / −0.191。real_state 高于 random_state 的 1 格（gap_neg 2015-18，差 0.019）。
- **相关事实**：random_state 臂的随机状态见 E04。
- **判定**：DIFFERS（全称句的逐格计数）。

### E10　D5：part1 Q3「ADD … 更大权重为负」按两段各自读有 1 档不成立

- **探针**：D5（2 个子检查：两段读法 DIFFERS；full 读法 REPRODUCED）。
- **REPORT 原句（part1 Q3 读法）**："ADD 在最小权重（γ = .0625）两段接近 0、更大权重为负"。
- **重算**（RV ADD_SCORE 主方向，与 part1 Q3 表同一分组）：γ = .0625：两段 −0.029 / +0.025，full 0.000；γ = .125：两段 −0.141 / **+0.003**，full −0.066；γ = .25：两段 −0.427 / −0.168，full −0.264。按"两段各自为负"读，2 档中 1 档成立；按 full 列读，2 档都成立。句子没有写明按哪一列，两种读法并列。
- **判定**：两段读法 DIFFERS；full 读法 REPRODUCED。

### E11　E6：无随机对照的 432 个主描述符的构成与 brief 预期不同；part2 §4 表头括注与表不符

- **探针**：E6（2 个子检查 DIFFERS）。
- **预期（brief §5 E6）**：432 = FOURARM 216 + TPAIR 160 + 56 个其他。
- **重算**：总数 432 与 104,856 = 3 x 34,952 都成立（REPRODUCED）；构成是 FOURARM 216 + RC FOCAL_NEW 36 + RO FOCAL_NEW 108 + RS FOCAL_NEW 72（逐个列表 `verify/E6_no_random_control.csv`）；TPAIR 160 个在 Z-MAP 里有 basic / industry / persist20 三类行。
- **REPORT 原句（part2 §4 表头"基准"项）**："真实−随机 = Z-MAP basic 路径均值（FOURARM / TPAIR 等确定性臂无随机对照）"；同表 TPAIR 行的"真实−随机"两后段为 0.607 / 0.779（有值），FOURARM 行为空。
- **判定**：DIFFERS（构成；表头括注 vs 表）。

### E12　其余 NOT_COMPUTABLE（输入里没有对象或不在允许输入）

| 子检查 | 事实 |
|---|---|
| C13 首表从 `measurements/` 原值重算分位 | `measurements/` 只有诊断汇总（`diag_*` / `cost_exposure_*`）；逐格原值只在 `cache/`，不在允许输入。首表 18 行按表层复核（REPRODUCED） |
| E1 逐日 Δgross = 进入 + 退出 + 共同 | 日账本 npz 只存子账户 net8 / gross / pos / turn 与 dnet8 / dcore / dsamecap，没有三项与母体 gross；年化列 `attr_*` 与 `d_gross_ann` 的日期掩码不同，年化层面不是恒等式。REPORT 印的 6.1e−18 与存档逐描述符残差列 `attr_identity_resid` 的最大值一致（表层，REPRODUCED） |
| D5 全称句清单 | 五份 REPORT 正文（表格行与表头除外）108 句，按 `verify/D5_universal_sentences.csv` 的 coverage 列：41 句的数字由 D2 / D5 / V-C 重算（句内〔id〕或按"报告 + 行 + 关键片段"登记）；7 句带〔id〕、D1 只核了"正文 = 存档文本"；48 句带数字但本程序没有逐句重算；12 句无数字（定性或范围句）。其中 48 句计入此项 |

---

## §4 闭包门

- **进入 V（2026-09-26 01:52:14，`verify.log`）：PASS**。运行中的 e6i 作业 0；`task_status/*_DONE.json` 6 个、failed_tech 0；receipt 1,691 个（SUCCEEDED 1,685；FAILED 6 个为 2015-18 RO / RR 原始分片，均被同名 `_rerun` 成功覆盖），无空 receipt；交接指纹（7 个 exec_briefs 文件 + 32 个结果文件、66 个 e6i blob）重算 0 不符；HEAD = 远端 main = `569c810`；已跟踪文件无改动；untracked 只有既知 11 项；五份 REPORT + B 草稿三处一致。
- **终版全链运行时（03:38:59）的闭包门：FAIL**，唯一不同项是 untracked 多出 `exec_briefs/E6i_MIRROR.md5`（C-2 在 01:53:19 写进 47 仓库、随本报告提交）；其余各项与 01:52:14 相同。`verify/closure_gate.json` 记录的是这一次。
- **交付后**：本报告与 lessons_delta、MIRROR、只读程序 push 之后，同一程序以 `--stage gate_post` 写 `verify/handoff_fingerprint_postverify.json`（原指纹不改）并运行交付后闭包门（`verify/closure_gate_post_V.json`）；结果记 WORKLOG（本报告不能包含自身 push 之后的检查）。

---

## §5 经验增量

见 `exec_briefs/E6i_lessons_delta.md`：§1–§7 为 C-1 收拢的内容（含执行端写进共享 memory 的 21 条逐条列表），§8 为 VERIFY 阶段追加（V 暴露的仪器 / 口径事实、brief 转录与预注册、V 程序自身的错误、独立性范围、流程层建议）。
