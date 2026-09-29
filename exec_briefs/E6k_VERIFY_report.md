# E6k VERIFY 复核报告（执行端；协议 v1.1；2026-09-30）

用途：按 `E6k_VERIFY_brief.md`（sha256 903aa8fc）对 E6k 整轮交付（提交 `03e1015`）做只读复核，给出：
- §C 收尾十项结果；
- V 探针逐条结果；
- E 项与口径说明；
- 复核后闭包门。

本文只回答"是不是这个数"和"口径是什么"。无推荐、无判读；判读属 REVIEW，裁定属用户。时间均为 47 时间。

- 程序：`verify/verify_e6k_readonly.py`，sha256 3bbcf75ed0369db755119367e1a93ce85ca82c6580ea3982d1c355c8caa24931，同文件入库研究目录。不 import 任何 e6k / e6j 模块，只读 brief §1 允许的输入。
- 输出：结果目录 `verify/`，包括：
  - `probes.csv`、`probe_results.csv`、`results_<类>.csv`、`verify.log`；
  - 逐条附表 `vc13_sample.csv`、`vc16_legacy_degenerate.csv`、`vd04_prose_binding.csv`、`vd06_universal.csv`、`vd07_cards.csv`、`vd07_cards_sample5.csv`、`vd07_supported_scope*.csv`；
  - `E_items.md`、`closure_gate_postverify.json`。

## §0 计数

| 项 | 值 |
|---|---|
| 本轮身份（brief §0 逐项） | 全部相符：十二份 reports/ 文件 sha 前缀、source_manifest bdf4db8a（git_head 82b6cf3）、PLAN_COPY 1f9e949c、brief 8be4df3d、附录 2258b2c6、两个封存、回执 2,334、授权链、HEAD = origin/main = 03e1015 |
| 探针 | brief §5 表列出 48 个 probe_id（VA 8 / VB 7 / VC 17 / VD 7 / VE 9），全部执行；转交说明写"40 条"，以 §5 表为准。决策端预期表覆盖其中 29 个，其余现算 |
| 子检查 | 490 行：REPRODUCED 486、DIFFERS 4、NOT_COMPUTABLE 0 |
| 标记 | ROUNDING 0、STOCHASTIC 5、INFO 74 |
| 按类 | A 249 行全 REPRODUCED；B 58 全 REPRODUCED；C 38（DIFFERS 2：VC16）；D 136（DIFFERS 2：VD06、VD07/supported_scope）；E 9 全 REPRODUCED |
| 运行 | 正式运行 2026-09-30 03:04:52–03:11:04，16 进程；此前在临时目录试跑（仅临时目录，未写 verify/） |
| E 项 | 9 条：机器表数值 M 1 条（E01）；交付文字表述 R 6 条（E02–E06、E09）；决策端预期 P 2 条（E07、E08）。DIFFERS 与 E 项对应：VC16 → E01；VD06 → E02–E05；VD07/supported_scope → E05（另 E09 为回链口径） |
| S1 | 按 brief §6 背景段"统计量是别的量"分支做同单位读数（事后口径），见 §6 |

## §1 §C 收尾十项

| # | 结果 | 产物 |
|---|---|---|
| C-1 | `E6k_lessons_delta.md` 在交付版末尾追加"§ 交付后"节（27–37 条，A–F 标注），不改交付版正文；不写共享 memory | 结果目录 reports/ 与两处 exec_briefs |
| C-2 | 十二份 reports/ 文件在三处（结果目录 / 47 exec_briefs / 本地）的 sha256 与 md5 重算 36 行，与 `E6k_MIRROR.md5` 逐行相同。原 MIRROR 只有一节，即交付节 = 第一 / 二节合并。此后新增与追加的文件只进第三节 | `E6k_MIRROR.md5` 第三节 |
| C-3 | 复核后闭包门，见 §4 | `verify/closure_gate_postverify.json` |
| C-4 | `E6k_limit_register.md` 在 L01–L16 之后追加 L17（同时带口径）、L18（LEGACY_EDIT5 未定义段为实现口径）、L19（段均类表与 n 加权政策表分母不同；CAP 定义）、L20（random_refs 退化对象的舍入 sd） | reports/ 与两处 exec_briefs |
| C-5 | WORKLOG 记 VERIFY / S1 阶段操作事实（时间、脚本 sha、耗时、并发），远端与本地同文 | worklog |
| C-6 | 遗留进程 38 个，列在 §1.2，未动，交用户决定 | `verify/legacy_processes.csv` |
| C-7 | 代码变更登记（新文件），摘要见 §1.3 | `reports/E6k_code_change_register.md`（sha256 fd822bcb） |
| C-8 | 决策端五件复制到 `verify/decision/`，sha 与 exec_briefs 相同（`verify/decision_sha256.txt`） | `verify/decision/` |
| C-9 | 事后标注缺失：part2 衰减表注、mechanisms HGCONT 表头 / 表注、L15 都写了 v1 退化与 v2 替代，但无"事后"字样 → E06；标注补在 supplement_1 §0.2 | E 项、supplement |
| C-10 | lessons 16 的占位对象 / PARENT 源锚说明在 `E6k_REVIEW_input.md` 读法注。L16 三处覆盖不足在 limit_register L16，以及卡表 E6K-Q07-b 表注、E6K-Q08-b 表注、E6K-Q10-c 原因行。未补做 | — |

### 1.1 记录 B 批准依据（D09；原文引用，不作解释）

`registration/record_B_approved_E6k.json`（written_at 2026-09-29 07:28:09）：

- `user_quote`：「stop point不用特意停下来汇报了 继续推进就好」（`user_quote_date` 2026-09-29）
- `mode`：「A：推导段封存后用户一句话批准」
- `context_note`：「日期按 47 时间（本地日期 2026-09-28）。用户在推导段收尾后发出此句：part1、记录 B 草稿与 routing_review_A1_auto 已于 07:2x 镜像到 exec_briefs，执行端尚未单独汇报停点；原话明确停点不必停下汇报、继续推进。执行端据此按方式 A 的“一句话批准”处理（授权对象 = 冻结清单全部描述符 × 两后段及闭包；不是事前整表授权 B）。E6j REVIEW §11 经济裁定未给，policy_provisional = true 不变；deployment_authorized = false；新算子不 chosen。」

解释权在用户（REVIEW §11 裁定项）。

### 1.2 遗留进程（C-6；未动）

按 PID + 启动时间 + 命令行列出，本轮 E6k 进程 0 个。命令行已脱敏，全文见 `verify/legacy_processes.csv`。

| 类 | 个数 | 启动时间 | PID | 命令（脱敏） |
|---|---|---|---|---|
| joblib / loky 工作进程（更早轮次） | 28 | 2026-09-01 22:17:09–22:17:10 | 204181、204183、204184、204187–204189、204191、204192、204197、204201–204203、204205、204207、204209–204211、204214–204216、204227–204232、204234、204236 | `python3 -m joblib.externals.loky.backend.popen_loky_posix --process-name LokyProcess-N …` 与两个 resource_tracker |
| `pgrep -f` 自匹配等待循环（更早轮次） | 10 | 06-05 02:40:22；09-12 12:22:21 / 12:24:23 / 12:25:55 / 12:35:42；09-13 07:24:24 / 07:36:29 / 11:44:12 / 11:46:51 / 14:32:14 | 332422；311130、311414、312058、313610；433259、437646、462829、463149、487830 | `bash -c while pgrep -f <E6h 或诊断脚本名> …; do sleep N; done …` |

### 1.3 代码变更登记摘要（C-7；V 只转录、不复跑）

- **范围**：Stage 0 登记的 16 个 e6k 文件中改动 4 个、不变 12 个；Stage 0 之后新增 32 个。VA07 与登记逐条相同。
- **还原检验**（主证据）：按编辑记录把交付版逐条反向撤回（`verify/code_register/reverse_edits.py`，只读交付版）。结果：
  - 四个改动文件逐字节回到 Stage 0 sha：e6k_core 723300bb、e6k_ops be2e3076、e6k_run_det 2e82a5e8、e6k_stage0_ops 26505f03；
  - 中间版本逐字节回到部署记录：e6k_ops 07:51 版 d4bfe7bd、e6k_core 中间版 d2bdf96b。
- **四个改动**（触发 = lessons_delta 条号）：
  - e6k_core：① 新增 `npz()` 整读（lessons 9），只被统计 / 诊断 / 报告脚本调用，账户与随机 worker 不调用；② `post_gate` 冻结清单文件名修正（lessons 17），修正前后段任务在守卫处退出、无产物。
  - e6k_ops：① RP 复核失败日的恢复路径（lessons 18），`choose_pairs_dfs` / `choose_pairs_milp` / `canonical_matching` 逐字未改，只加新函数与 try 包裹；② `hg_gate(hold_init)`，默认关（lessons 24）。
  - e6k_run_det：facts 记 `solver_limit_days` / `rp_recovered_days`，不在账户路径上。
  - e6k_stage0_ops：后段过 `post_gate`（X04）。
- **影响面**：
  - 后段首轮 116 个确定性任务在 07:34:02–07:51:06 全部结束，早于 ops（07:51:31）与 run_det（07:56:35）的改动；其中 10 个在复核失败处退出、无产物，补跑用新版本。
  - 后段恢复 17 日全部在这 10 个补跑里；随机分片无一进入恢复分支。
- **等价证据**：
  - seal_deriv 的 1,480 个文件 sha 在全部改动之后未变（VA05 全量现算 0 不符）；
  - 后段 Stage 0 第 3 类恒等锚同代码两段各 891 PASS / 168 INFO / 0 FAIL；
  - 推导两段 MILP 9 日、复核失败 0 日。

## §2 探针逐条（逐行数值见 `verify/probe_results.csv`；预期值取 `E6k_VERIFY_expected.csv` 同 probe_id）

| probe | 内容 | 子检查 | 判定 | 要点 |
|---|---|---|---|---|
| VA01 | 十二份 reports/ sha256 / md5 × 三处 × MIRROR | 12 | REPRODUCED | 三处一致，与 MIRROR 逐条相同 |
| VA02 | REVIEW_input 的 sha 前缀 | 210 | REPRODUCED | 209 条全部现算相符（结果目录 161 + 代码 48；brief 写 177 + 32，E08）；8 条路径重复出现，按行计 |
| VA03 | query_id | 9 | REPRODUCED | 119 个：R0 22 / part1 17 / part2 7 / part3 10 / mechanisms 14 / carried 2 / cards 47，登记数 = 正文集合，跨文件唯一；卡 query 47 = 登记表 |
| VA04 | 回执 | 2 | REPRODUCED | 2,334 = SUCCEEDED 2,333 + FAILED 1（stage0_c1_identity，_rerun 覆盖）；completion_receipt 记 2,334 |
| VA05 | 封存 | 5 | REPRODUCED | seal_deriv 02:37:51、seal_post 10:53:21，各 1,480 文件；全部 2,960 个文件 sha256 现算 0 不符；det 116 / rand 1,016；post 队列 1,132、缺 0；时序链与预期逐键相同 |
| VA06 | 时序与追记 | 9 | REPRODUCED | 政策 / 补充 / 预登记追记（00:42:14–02:14:34）全部早于首次读数 02:40:25；批准 07:28:09 < 条件回执 07:31:28 < 首个后段账户 07:33:55 / 首个后段随机 08:05:18；B / P 清单现 sha = 批准时冻结 sha |
| VA07 | 代码变更 | 1 | REPRODUCED | 4 改动 / 12 不变 / 32 新增，与 C-7 登记逐条相同 |
| VA08 | 交付时状态 | 1 | REPRODUCED | verify/ 开工时为空；supplement_1 目录不存在；code_change_register 不存在（开工现场记录 `verify/identity_at_start.json`） |
| VB01 | Stage 0 | 18 | REPRODUCED | 六类 CSV 状态计数；c1 首跑 268 行中 FAIL 2 由 rerun 覆盖（rerun PASS 76 / INFO 192）；stage0_all_pass、plan tests 103 / 103、git_head 82b6cf3、行情终点 2026-03-27 |
| VB02 | 登记计数 | 8 | REPRODUCED | 描述符 39,142（12 块）；primary144 144 / c1_hi 4 / SM 6 / PARENT 160；coverage 64 行 registered == computed（每段 39,142 + 附属 2,336 = 41,478）；policy 38,982 × 186；descriptor_stats 各段 41,142 |
| VB03 | E6j 复现 | 2 | REPRODUCED | NATIVE 216 + SM 6 对象的 D_seg / D_sc_seg / FULL / G4 = E6j pilot_policy，max 1.67e−16；Q 3 母体、RARPRE 12 对象 Δ 0 |
| VB04 | carried 32 行 | 1 | REPRODUCED | 六形态四段 net8 / invested / position / names = E6j 领导表；R2 / A06 = E6i 锚；0 不符 |
| VB05 | E5a 证据行 | 1 | REPRODUCED | 8 行 sha = E5a 实物现算 |
| VB06 | α = 0 母体成员 | 24 | REPRODUCED | 六形态 × 四段：K0 位图的持有格 = E5a pool2 同段集合（判据：出现日集合多重集相等） |
| VB07 | 种子重放 | 4 | REPRODUCED（STOCHASTIC） | 每段 8 条路径的 u 序列哈希 = 分片元数据 |
| VC01 | 合并恒等 | 1 | REPRODUCED | FULL / G4 / FULL_sc / G4_sc / FULL_imp max ≤ 3.6e−15；years / d_ok / c / f / positive / e_cap 0 不符 |
| VC02 | e_rand | 1 | REPRODUCED | 0 不符（RANDOM_NOT_SCHEDULED 33,890 / NO_NEW_CONTENT_TO_PERMUTE 4,200 / PASS 515 / FAIL 330 / MC_UNRESOLVED 47） |
| VC03 | 政策判定串 | 1 | REPRODUCED | 38,982 × 10 判定串 + 5 列 PENDING 0 不符（V 独立实现） |
| VC04 | 相对列 | 1 | REPRODUCED | max ≤ 2.9e−15；NaN 模式一致 |
| VC05 | 三句加法 | 1 | REPRODUCED | 80 行 0 不符 |
| VC06 | 候选清单 | 2 | REPRODUCED | 820 = 66 / 233 / 233 / 233 / 55；primary144 通过 8 / 40 / 40 / 40 / 9；主对象 154 口径 12 / 47 / 47 / 47 / 13；CAND-COUNT 相符 |
| VC07 | question_to_objects | 1 | REPRODUCED | 300,466 行 / 47 query；不在描述符表的 2 个为卡级占位对象（E08） |
| VC08 | 随机 | 6 | REPRODUCED | random_refs 恒等；policy rmr / mcse = LEGACY 行；random_registry 2,252；MC 加密未触发（§3.7） |
| VC09 | bootstrap | 3 | REPRODUCED | 677,556 = 112,926 比较 × 2 L × 3 scope（CP 233,892 / CN 220,176 / CC1 161,280 / CB 46,656 / CH 15,552 行）；CP FULL est = policy FULL，max 3.1e−15；q025 ≤ q975 违反 0；part3 ci_L20 1,540 格 0 不符 |
| VC10 | 掩码台账 / 风险日表 | 2 | REPRODUCED | 9,592 = 2,398 × 4（含 FALLBACK_DOMAIN 128 行）；目标层列 = policy 段列，max 1.8e−14；parquet 630,400 × 21 = 160 目标 × 3,940 日（E08） |
| VC11 | 假设卡 / 血缘 | 2 | REPRODUCED | 18 卡十三字段齐；lineage 32 = adopted 18（plan 1f9e949c）+ superseded 14（proposal 65d2b010）（E08） |
| VC12 | 同时带 / size | 2 | REPRODUCED | size_profiles 0 不符（预期表标签，E07）；band 统计量为标准化 max-t，单位不同 → 不判 DIFFERS（§3.1；S1） |
| VC13 | 账本重算 | 2 | REPRODUCED | 154 主对象 + 抽 300（seed 20260929）：D / n / D_sc / Y / FULL / G4 / FULL_sc / se_H max ≤ 8.9e−16；bootstrap 重放 20 条 9.7e−17（STOCHASTIC） |
| VC14 | 目标层暴露列 | 1 | REPRODUCED | max ≤ 7.1e−15；口径见 §3.8 |
| VC15 | 冲击 / 线性费 | 1 | REPRODUCED | D_imp / D_str / D_6bp / D_12bp max ≤ 2.2e−16；口径见 §3.9 |
| VC16 | 随机路径值 | 11 | 9 REPRODUCED / 2 DIFFERS | 非退化对象 ≤ 2.5e−13；退化对象 rand_sd 为舍入值 ≤ 2.7e−07（E01）；按精确 sd 重判 e_rand 变化 0 |
| VC17 | part1 表 | 2 | REPRODUCED | 144 表 432 格、GRID 333 格 0 不符 |
| VD01 | 表结构 | 119 | REPRODUCED | rows / cols = 登记 |
| VD02 | part2 144 表 | 1 | REPRODUCED | 1,728 格 0 不符（V 逐列全计；part1 部分见 VC17） |
| VD03 | part2 GRID | 1 | REPRODUCED | 555 格 0 不符 |
| VD04 | 正文数字 | 8 | REPRODUCED | 167 行 708 个数字记号全部绑定、0 不符（用 REPORT 原行；清单 text 列 92 行为截断预览）；重点项 7 行（授权链、Stage 0、段边界、候选计数、RP 恢复日 6 / 11、carried 运行事实、领导表句位置）全部相符或已注明位置（E08） |
| VD05 | part3 五表 | 1 | REPRODUCED | 10,010 项 0 不符 |
| VD06 | 全称句 | 1 | DIFFERS | 52 句：可计数绑定 40（其中不成立 5 → E02–E05），指针 / 运行叙述 12，未绑定 0 |
| VD07 | 卡表 / supported_scope | 3 | 2 REPRODUCED / 1 DIFFERS | 47 表全格 18,695：OK 18,683、生成时刻存在性近似 12、不符 0；抽 5 格 233 / 0；supported_scope 160 条检查 1 条不符（E05），177 个记号全部绑定（回链口径 E09） |
| VE01 | 账本恒等（全量） | 1 | REPRODUCED | 232 个账户文件：净费恒等残差 0、NaN 模式 0、D max 8.9e−16、n 0、net8_ann 1.8e−15（164,568 行对） |
| VE02 | LX | 1 | REPRODUCED | 印出表 0 不符；顺序平均和 − V11 5.6e−17；within + allocation − total 1.8e−15；closure_resid max 1.9e−17 |
| VE03 | HG 四账户 | 1 | REPRODUCED | 144 行 0 不符；HG_ONLY α0 证据 96 PASS |
| VE04 | Shapley | 1 | REPRODUCED | Σ net − (ISK − EMPTY) 1.7e−15；gross − net − fee 1.1e−16；rand_net = random_refs 1.8e−15；印出表为段均（§3.3） |
| VE05 | RP | 1 | REPRODUCED | 印出表 0 不符；恢复日 {2019-2023: 6, 2024-2026: 11} |
| VE06 | CS 桥 | 1 | REPRODUCED | 四账户闭合 6.7e−16；MX-CS = 段均后按块平均；INC_SUPPORT0 − NATIVE 中位 −.0028 |
| VE07 | CAP | 1 | REPRODUCED | 三列从 `<段>_capital.csv` 重算 ≤ 5.4e−13；定义见 §3.3 |
| VE08 | TREFIT / POST2 / TAILS / SHADOW | 1 | REPRODUCED | 印出表 0 不符；桶份额和 2e−16；SHADOW 口径见 §3.10 |
| VE09 | 计数恒等 | 1 | REPRODUCED | 见下 |

VE09 各项构成：

- 39,142 = CORE 9,600 + LAYER 7,680 + REPAIR 7,680 + BAND 5,760 + OWN 3,840 + BAND_COMPARATOR 2,016 + TREFIT 960 + RAR 720 + POST2 360 + HG_ONLY 360 + PARENT 160 + SM 6。
- 38,982 = 39,142 − 160。
- 41,142 = 38,982 + 1,800 + 288 + 72。
- 附属 2,336 = CS 子 1,800 + DOSE 288 + CS 父 176 + INC 72。
- 144 = 6 × 4 × 6。
- LEGACY 956 = BAND 432 + LX 128 + RP 128 + INC 64 + OWN 64 + SZL 64 + NATIVE 54 + TREFIT 16 + POST2 6。
- 每段 232 个账户文件 = 116 个 npz + 116 个权重文件。
- 回执 2,334 = run_det 232 + run_rand 2,032 + 其他 70（逐项见 probe_results）。

## §3 E 项与口径说明

### 3.0 E 项（全文 `verify/E_items.md`；append-only；REPORT 均不改）

| E | 类 | 来源探针 | 现象（摘要） |
|---|---|---|---|
| E01 | M | VC16 | random_refs 中路径间方差为 0 的对象（LEGACY 128 个对象 × 段，全部 OWN；P5 抽样 27 个），rand_sd / mcse 是单遍方差式的舍入值（≤ 2.7e−07），不是 0。不影响 e_rand（PX6）与 MC 增补 |
| E02 | R | VD06 | R0 用途句"全部数字来自 …"未列 `accounts/<段>/facts_*.csv`（E6K-R0-RPSOLVER 的来源） |
| E03 | R | VD06 | part1 用途句"本文件所有数字来自 results/deriv/*.csv"：生成器另读 registry 与 facts（计数 / 台账表） |
| E04 | R | VD06 | cards Q15 表注"每个文件含该任务全部目标的位图与实际权重"：位图覆盖全部目标，但权重文件 200 / 232 只含子集（主要是 α .25 目标） |
| E05 | R | VD06 / VD07 | "α .125 × b 15 上 PM 从不触发交换"（Q10 supported_scope、lessons 12）过宽：NATIVE_PM15 20 / 24、INC1_PM15 14 / 24 个目标 × 段无换入；四段全无换入的 7 个目标 = LEGACY N/A 的 140 行 |
| E06 | R | C-9 | decay v2 / HG 跨段连续 v2 是事后补做，三处标注没写"事后"（补在 supplement_1 §0.2） |
| E07 | P | VC12 | 预期表 VC12 行的内容是 size 状态，与 brief §5 VC12（同时带）不一致 |
| E08 | P | 多条 | brief 正文与产物不一致：parquet 21 列 / REVIEW_input 161 + 48 / q2o 占位 2 个 / lineage superseded 行 source_sha = proposal / VB02 预期列名截断 / VD04"重点"所指正文不存在 / C-3 既知 untracked 计数（7 与 11，brief 写 5 与 9） |
| E09 | R | VD07 | 若干 supported_scope 数字按查询对象全集计算（如 Q04 −.173 为 RPINF 全网格），引用的卡表只印 α .25 × H5 子集（其中位 −.236），按 query_id 回链找不到 |

### 3.1 同时带（D17 / VC12）

- 统计量 = max_j |(FULL*_bj − FULL_j) / SE_j|，为标准化 max-t。
  - FULL* 为段内分层 stationary draw 的四段 n 加权年化百分点；SE_j 为 draw 的 sd（ddof 1）。
  - 集合：SE > 0 且无无支持 draw 的比较（primary144 为 144 个，all 为 111,766 个）。
- q95 以 SE 为单位；逐对象半宽 = q95·SE_j。primary144 L20：q95 3.379，半宽中位 .360 / 最大 .524（年化百分点）；同集合逐对象 CI 半宽中位 .209 / 最大 .298。
- 不同单位 → 按 brief §5 不判 DIFFERS。同单位读数见 supplement_1（S1-Q01–Q03，事后口径）。
- 限制登记 L17。

### 3.2 LEGACY_EDIT5 未定义段（D12）

- 实现：只在有编辑日的段上判 |edit_gap_absmean_T| ≤ 5；四段都未定义时 CSV 存字面 `N/A`，判定串里既不计失败、也不计待定；共 140 行（E05 的 7 个目标 × H 1…20）。
- 决策端 D12 所见 `size(LEGACY_EDIT5):nan` 是用 pandas 默认 NA 解析读字面 `N/A` 的产物。交付件（policy CSV、七份 REPORT、REVIEW_input）中 `:nan` 出现 0 次。
- PX5 未写此处理，属实现口径（L18）。

### 3.3 CAP / SMB / Shapley / CS 的"段均"（D15 / VE07 / VE04 / VE06）

- CAP：
  - 两边有仓日（Pc > 0 且 Pb > 0）：sel = ½(Pc + Pb)(uc − ub)，cap = ½(uc + ub)(Pc − Pb)，其中 u = E / P。
  - 只一边有仓日：one_sided = Ec − Eb。
  - 三列都按全段交易日取均值后 × 25,200。
  - sel + cap + one_sided = gross 配对差（不含费用），与 FULL（8bp 净）或 FULL_sc 无恒等关系；决策端候选的五个恒等式不成立是定义所致。
- 四张段均类印出表：
  - E6K-MX-CAP 为四段等权段均；
  - SMB 的 `D_ann` 为四段 D 等权均值，`alpha_over_D` 为逐段比值的均值；
  - Shapley 表为段均；
  - MX-CS 为逐描述符四段等权均值后按块平均。
- 政策表 FULL 为 n 加权（L19）。

### 3.4 part2 144 表 `label` 列（D23）

一列两义：新算子行 = 首看标签 `NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY`，原生行 = 暴露类型；表头已写。V 按两义逐格复算，0 不符（VD02）。

### 3.5 记录 B（D09）

原文引用见 §1.1，不作解释。

### 3.6 事后标注（D09 / C-9）

见 E06 与 supplement_1 §0.2。

### 3.7 MC 加密未触发（D14 / VC08）

- 增补条件：某比较组所需路径 (sd / .03)² 大于已有路径才增补；n = 1,024 时等价于 mcse > .03。
- LEGACY 两后段 1,912 个对象 × 段的 mcse 全部 ≤ .0105，满足"|rmr| ≥ 2·mcse 或 mcse ≤ .03"的有 1,912 / 1,912。
- 因此 956 个对象两后段均停在 1,024 条；MC 增补第 1 轮 0 个分片（WORKLOG 10:52:32）。

### 3.8 目标层暴露列（VC14）

- `edit_gap_mean_T` = 有编辑日（t_gapT 有限）的均值 × 100，与 `edit_gap_days_T` 对应。
- `port_size_lo / hi` = lo、hi 都有限的"共同可定义日"均值。
- lv5 / small30 / unkT = 有限且 wsum > 0 日的均值；`small30_delta` = 子 − 父。
- `turn_rel` = mean(子 d_turn) / mean(父 d_turn) − 1，为全段日均之比，不是 Σ 之比。

### 3.9 冲击（VC15）

- `d_bracket` 是逐日平方根冲击括号项。冲击成本 = κ·sqrt(A·1e8)·bracket（A 单位亿元，NaN → 0）；两档 (A, κ) = (5, .5) / (10, 1) 用同一数组。
- D_6bp / D_12bp = gross − turn × 6e−4 / 12e−4 的配对差。

### 3.10 SHADOW（VE08）

E6g 库存模型下的逐日超额（gross、constant notional；ideal 与 X1 两个视图）。`child_minus_parent_ann` = 同视图同 H 配对日均 × 25,200，与 policy D（源引擎 8bp 净）无恒等关系。

### 3.11 V 计数口径说明

- VD02 为 part2 逐列全计 1,728 格，part1 的 432 格在 VC17；与预期表"2,016 项"的计格法不同，内容覆盖更多。
- VD07 的 12 个"生成时刻存在性"格：V 以文件修改时间早于卡表回执近似，不作不符。
- VD06 的"均值 / 日均 / 平均"是词法命中，不是全称量词。

## §4 复核后闭包门（C-3；`verify/closure_gate_postverify.json`，以 JSON 为准）

脚本 `verify/closure_gate_postverify.py` 只读、不 import 本轮模块，结果 all_pass = True，共 24 项：

| 项 | 结果 |
|---|---|
| 本轮运行中作业 | 0 个（按 PID + 启动时间 + 命令行，关键词 e6k / verify_e6k）；§1.2 的 38 个遗留进程仍在，未动 |
| 回执 | 2,335 = 交付时 2,334（SUCCEEDED 2,333 + FAILED 1 由 _rerun 覆盖）+ VERIFY 阶段新增 1（`supp1_band` 2026-09-30 03:14:13 SUCCEEDED）；未覆盖 0 |
| completion_receipt 十九项复核 | 本轮作业 0；回执覆盖；seal_deriv / seal_post 各 1,480 个文件全量 sha256 0 不符；十二份文档扫描（禁用词 / 主机 / 账号 / 家目录 / 连接串）0 命中，追加后的 lessons_delta 与 limit_register 含在内；query_id 119 唯一；coverage 64 行 registered == computed；plan §13.5 固定输出清单全部存在 |
| VERIFY 新文档扫描 | E6k_VERIFY_report、E6k_REPORT_supplement_1、E6k_code_change_register、verify/E_items 共 4 件，0 命中 |
| git（白名单提交前） | HEAD = origin/main = 03e1015 |

git 未跟踪文件：

- 既有：
  - chain / wave 脚本 7 个：autochain、chain、chain2–4、wave2、wave3（brief 写"五个"，E08）；
  - 单因子脚本 3 个；
  - exec_briefs 下更早的决策端 / 裁定文件 11 个（brief 写"九个"，E08）；
  - 本轮决策端 VERIFY 输入 2 个：E6k_VERIFY_brief.md、E6k_VERIFY_expected_script.py。决策端 CSV 三件不在 git status 列表中。
- VERIFY 新增、待白名单提交 5 个：verify_e6k_readonly.py、e6k_supp1_band.py、exec_briefs/E6k_VERIFY_report.md、E6k_REPORT_supplement_1.md、E6k_code_change_register.md。

已改动：exec_briefs/E6k_lessons_delta.md、E6k_limit_register.md（追加），以及 E6k_MIRROR.md5（第三节）。

## §5 经验增量

见 `E6k_lessons_delta.md`"§ 交付后"节（27–37 条）。

## §6 补充计算

见 `E6k_REPORT_supplement_1.md`：
- §0 同时带统计量定义、单位与事后标注；
- §1 S1-Q01–Q03 同单位读数；
- 产物在 `results/full/bootstrap/supplement_1/`，回执 `supp1_band`。
