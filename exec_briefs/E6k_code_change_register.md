# E6k 代码变更登记（VERIFY §C-7；执行端；只登记，不复跑）

用途：按 VERIFY brief 规则 9 / C-7，把 Stage 0 收尾（`source_manifest.json` written_at 2026-09-29 00:42:32；`e6k_code_sha256_at_stage0` 16 个文件）之后改动过的 e6k 代码与新增的 e6k 代码逐文件登记：before / after sha、改动时间、改动范围、触发原因（lessons_delta 条号）、影响面（哪些任务在改动前 / 后跑）、等价证据。交付版 = REVIEW_input 所列 sha = 提交 `03e1015`。时间均为 47 时间。

## 0. 还原检验（本登记的主证据）

- 做法：把交付版按执行端编辑记录逐条反向撤回（`verify/code_register/reverse_edits.py`，只读交付版、只写临时目录；还原件与 unified diff 复制在 `verify/code_register/`）。
- 结果：四个改动文件全部**逐字节**回到 Stage 0 sha——`e6k_core.py` 723300bb4297f8bc、`e6k_ops.py` be2e3076bf3a5138、`e6k_run_det.py` 2e82a5e8cda9faa6、`e6k_stage0_ops.py` 26505f03b5002a2e；中间版本也逐字节对上：`e6k_ops.py` 只撤 hold_init 一步 = 07:51 部署版 d4bfe7bd6d65f32e（WORKLOG 记录）；`e6k_core.py` 只撤清单文件名一步 = 中间版 d2bdf96bd2e13aac。
- 含义：Stage 0 之后对这四个文件的改动 = 下表所列各项，**别无其他**。
- 其余 12 个 Stage 0 文件交付 sha 与 Stage 0 相同：`e6k_a0.py`、`e6k_acct.py`、`e6k_boot.py`、`e6k_env.py`、`e6k_random.py`、`e6k_run_rand.py`、`e6k_stage0_close.py`、`e6k_stage0_data.py`、`e6k_stage0_identity.py`、`e6k_stage0_output.py`、`e6k_stage0_random.py`、`e6k_stage0_source.py`。

## 1. 四个改动文件

| 文件 | 版本链（sha 前缀 @ 时间） | 改动范围 | 触发 | 影响面 | 等价证据 |
|---|---|---|---|---|---|
| `e6k_core.py` | 723300bb @ Stage 0 → d2bdf96b @ 约 01:3x（统计试跑发现 NpzFile 重复读盘之后、首次真实读数 02:40:25 之前）→ fd3a0379 @ 07:31:00 | ① 文件末尾新增 `NpzDict` 类与 `npz()`（+15 行，`diff_core_s0_to_0130.txt`）；② `post_gate` 内冻结清单文件名 `B_package_manifest.json` → `B_package_manifest_E6k.json`（1 行，`diff_core_0130_to_final.txt`） | ① lessons 9；② lessons 17 | ① `npz()` 只被 11 个统计 / 诊断 / 报告脚本调用（a1_auto、bootstrap、closure_deriv、decay、deliver、hg_continuous、mechanisms、report_carried、risk、shadow、stats）；账户 / 随机 worker 链（run_det、run_rand、env、acct、ops、random）不调用。② 推导段 `post_gate` 在查文件之前直接放行；后段首次启动（07:28:58）1,132 个任务在守卫处退出、未读后段数据、无产物；07:31:27 重启后全部后段任务用 fd3a0379 | 还原检验逐字节；推导段封存 1,480 文件 sha 在全部改动之后未变（V 探针 VA05）；后段账户 / 随机 / 回执最早时间晚于 07:31:27（VA06） |
| `e6k_ops.py` | be2e3076 @ Stage 0 → d4bfe7bd @ 07:51:31 → 4835c41e @ 12:20:57 | ① 新增 `choose_pairs_milp_checked`、`choose_pairs_dfs_signed`、`recover_lex`（插在 `rp_day` 之前）；`rp_day` 里原 `sel = choose_pairs_milp(...)` 包进 try，复核失败时走两条独立精确路径，都不成或不一致则当日隔离回父、标 SOLVER_LIMIT；`choose_pairs_dfs` / `choose_pairs_milp` 本体未改（`diff_ops_s0_to_0751.txt`）；② `hg_gate` 加参数 `hold_init=False`（默认关）与 `started` 标记（`diff_ops_0751_to_final.txt`） | ① lessons 18（X08 / plan §5.4 第 6 条）；② lessons 24（X09 诊断 v2） | ① 推导两段全部任务、后段首轮 116 个确定性任务（07:34:02–07:51:06 全部结束）用 be2e3076，其中 10 个在复核失败处退出、无产物；后段随机分片跨两个版本启动，无一进入恢复分支（RP_RECOVERY 只出现在 10 个补跑确定性任务日志）；10 个补跑（10:26–10:52）用 d4bfe7bd：恢复 17 日（16 两路一致、1 只 MILP 路径），SOLVER_LIMIT 0。② 全部登记账户在 12:20:57 之前算完（后段队列 10:52 结束）；只有 `e6k_hg_continuous.py --hold-init`（v2 诊断）传 True | 还原检验逐字节（两步分别回到 d4bfe7bd、be2e3076）；成功日代码路径逐字相同（diff 只有新增函数与 try 包裹）；推导段 MILP 9 日、复核失败 0 日（R0 E6K-R0-RPSOLVER）；400 个随机小实例四条路径与穷举逐解一致（07:4x 临时目录，WORKLOG）；后段第 3 类恒等锚（含 A3-4 RP 端点与重解相同）在改动后同代码 PASS |
| `e6k_run_det.py` | 2e82a5e8 @ Stage 0 → 4221626b @ 07:56:35 | RP facts 字典：`solver_limit_days` 由常数 0 改为按逐日求解路径计数；新增 `rp_recovered_days`（`diff_run_det_s0_to_final.txt`，3 行） | lessons 18（facts 记恢复 / SOLVER_LIMIT） | 只改 `accounts/<段>/facts_*.csv` 两列，不在 target / ledgers 路径上；推导段与后段首轮确定性任务用 2e82a5e8（这些任务没有复核失败日，常数 0 正确；缺 `rp_recovered_days` 列 = 0）；10 个补跑用 4221626b | 还原检验逐字节；账户 npz 不受影响（改动只在 facts 字典） |
| `e6k_stage0_ops.py` | 26505f03 @ Stage 0 → 59fee076 @ 07:56:35 | `main()` 开头：后段过 `post_gate`（X04），推导段仍 `deriv_only`（`diff_stage0_ops_s0_to_final.txt`，5 行） | 执行端补充 X04（后段授权后同代码补算） | 推导段第 3 类（Stage 0 时跑）不受影响；后段第 3 类 07:57:16 起用 59fee076，两段各 891 PASS / 168 INFO / 0 FAIL | 还原检验逐字节 |

## 2. Stage 0 之后新增的 32 个文件

"首次运行"取首个回执或日志；回执同名重跑会覆盖 written_at，报告类首跑时间取 `logs/chain_analysis_full.log`。"触及"：账户 = `accounts/`，随机 = `randoms/`，政策 = `results/full/policy_*`。

| 文件 | 用途 | 首次运行 | 触及 | 首跑后改动 |
|---|---|---|---|---|
| `e6k_prereg.py` | P / B 登记包、暴露台账、hypothesis_lineage | 回执 prereg_packages 00:46:10 | 登记（读数前）；不触账户 / 随机 / 政策 | 无 |
| `e6k_a1_auto.py` | A1-auto 读数前 22 项 / 掩码事实 / 草稿第 7 项 | 回执 a1_auto_pre 00:47:40 | 读目标级位图与统计（不读收益）；写 registry / registration | `--masks-finish`（01:1x，lessons 8）；`--masks-post`（07:56:35，X04，另写 `_post` 文件） |
| `e6k_worker.sh` | 队列工作者 | worker_done 首行 00:54:12 | 间接写账户 / 随机（调用 Stage 0 登记的 run_det / run_rand） | 无 |
| `e6k_queue.py` | 首轮队列（确定性 + 随机分片） | `logs/queue_deriv.txt` 00:50:09 | 只写队列文本 | 无 |
| `e6k_queue_topup.py` | MC 增补队列 | `logs/queue_topup_deriv_1.txt` 02:35:50 | 只写队列文本 | 无 |
| `e6k_chain_mc.sh` | 推导段 MC 增补链 | MC_DONE_deriv 02:35:50 | 编排 | 无 |
| `e6k_seal.py` | 封存与核对 | 回执 seal_deriv_v1 02:37:51 | 读账户 / 随机算 sha；写 registration/seal_* | 07:56:35：`check()` 加队列逐行回执核对（lessons 20）；`verify()` 未改；seal_deriv 于改动前写成 |
| `e6k_stats.py` | 逐描述符统计 / 随机参照 / MC 规划 | 回执 stats_deriv 02:40:25 | 读账户 / 随机（封存后）；写 results/<阶段>/ | 真实读数前改整读 `npz()`；07:56:35：`--mc-plan` 前核队列完整（lessons 20），统计口径未改 |
| `e6k_risk.py` | SMB 回归与尾部账本 | 回执 risk 02:40:51 | 读账户（封存后）；写 diagnostics/risk | 无 |
| `e6k_mechanisms.py` | Shapley / LX gross / 资本分解 | 回执 mechanisms 02:41:14 | 读账户 / 随机（封存后）；写 diagnostics/mechanisms | 无 |
| `e6k_shadow.py` | 实施影子账户 | 回执 shadow 02:42:01 | 读账户（封存后）；写 diagnostics/shadow | 无 |
| `e6k_hg_continuous.py` | X09 HG 跨段连续诊断 | 回执 hg_continuous_2010-2014_2015-2018 02:42:27 | 重算 48 个 HG 目标（诊断，不写登记账户）；写 diagnostics/hg_continuous | 12:21:22：`--tag v2 --hold-init`（lessons 24），v1 文件保留 |
| `e6k_closure_deriv.py` | 推导段闭包核对 | 回执 closure_deriv 02:43:00 | 读账户（封存后）；写 checks/ | 无 |
| `e6k_report.py` | 报告公共件（表头、禁用词与泄露扫描、query 登记） | 随 part1 02:52:35 首用 | 只写报告 | 无 |
| `e6k_report_part1.py` | part1 | 回执 report_part1 02:52:35 | 读统计表 | 无 |
| `e6k_record_b.py` | 记录 B 草稿 / 批准 / 条件回执 | 回执 record_b_draft 02:53:06 | 写 registration/record_B_* | 07:27:45：`--approve` 加 `--note`（context_note） |
| `e6k_control_dist.py` | 附录 C 对照分布 | 回执 control_dist 03:20:07 | 按原键重算前 256 条随机路径的目标（诊断，不写 randoms/）；写 diagnostics/control_distributions | 无 |
| `e6k_chain_post.sh` | 后段链首版 | `logs/chain_post.log` 07:28:58 起 | 编排；07:52 停链脚本（保留其 xargs） | 无 |
| `e6k_chain_post2.sh` | 后段续链（补跑 / MC / 封存 / 分析） | `logs/chain_post2.log` 07:57:15 | 编排 | 无 |
| `e6k_queue_failed.py` | 按回执名生成补跑队列 | `logs/queue_rerun_post_1.txt` 10:26:17 | 只写队列文本 | 无 |
| `e6k_leafdiag.py` | Q05-c 可移动份额 / 置换熵 | 回执 leafdiag 08:07–08:08（四段） | 只用分区结构与有效掩码（不读收益）；写 diagnostics/mechanisms/*_leafdiag | 无 |
| `e6k_chain_analysis.sh` | 封存后分析链 | `logs/chain_analysis_deriv.log` 02:39:39 | 编排 | 08:11:43：full 链加卡表一步 |
| `e6k_policy.py` | 政策五列评分 / 三句加法 | 回执 policy_E6k 11:00:53 | 读 results/full 统计（封存后）；写 results/full/policy_* | 首跑前（07:56:35）：首看标签 / NOT_AUTHORIZED 改按新算子族（lessons 25） |
| `e6k_bootstrap.py` | 段内分层 stationary bootstrap | 回执 bootstrap_full 11:04:06 | 读账户（封存后）；写 results/full/bootstrap | 无 |
| `e6k_decay.py` | Q16 衰减场景 | 回执 decay_scenarios 11:01:01 | 只读 E6j 已暴露账本；写 diagnostics/decay | 12:13:27：前瞻版改独立 draw（lessons 23），另写 `_v2` 文件，v1 保留 |
| `e6k_report_r0.py` | R0 | 12:05:33（链内） | 读登记 / Stage 0 / 掩码事实 / facts | 首跑前（07:56:35）：授权原话、后段表、RP 求解计数、L13 / L14；12:29:25：L15 / L16（重生成 12:29:26） |
| `e6k_report_part2.py` | part2 | 12:05:33–12:06:00（链内） | 读 policy / bootstrap / random_refs | 首跑前（07:56:35）标签修正；12:13:27：改读衰减 v2 并加注（重生成 12:14:02） |
| `e6k_report_part3.py` | part3 | 12:06:00–12:06:21（链内） | 读 policy；写 results/full/production_change_candidates_E6k.csv | 首跑前（07:56:35）：候选 / 边缘清单改为主对象全列 + 计数 |
| `e6k_report_mechanisms.py` | mechanisms | 12:06:21–12:06:43（链内） | 读诊断 | 首跑前（08:1x）：CS / CAP / TAILS 表；12:22:40：HGCONT 表（重生成 12:29:48） |
| `e6k_report_carried.py` | carried | 12:06:43 首跑 rc=1（glob 匹配到权重文件，lessons 26）→ 12:09:12 | 读 PARENT 目标统计 / 回执 / worker_done | 首跑前（08:1x）运行卫生文字；12:0x glob 修正；12:29:25 代码改动清单（重生成 12:29:48） |
| `e6k_report_cards.py` | 47 个卡 query 同 id 落表 | 12:07:35–12:08:14（链内） | 读 policy / 统计 / 诊断 / 掩码 / 目标级数组 | 12:13:27：改读衰减 v2（重生成 12:14:41） |
| `e6k_deliver.py` | 机器表 / 假设卡 / REVIEW_input / 闭包门 / 镜像 | 12:06:43–12:07:35（链内 `--tables`），终版 12:32:38 | 写 results/ 机器表与 reports/REVIEW_input | 首跑前：REVIEW_input 读法注（07:4x）、REPORTS 加 cards（08:2x）；12:29:25：REVIEW_input 对自身 / 闭包门之后写入项注明 |

## 3. 等价证据汇总

1. 还原检验：四个改动文件逐字节回到 Stage 0 sha，中间版本逐字节回到部署记录（§0）。
2. 推导段：封存 `seal_deriv`（02:37:51）登记的 1,480 个文件 sha 在全部改动之后未变——由 V 探针 VA05 现算（VERIFY_report §2）。
3. 后段：第 3 类新算子恒等锚（`stage0/c3_ops/ops_identity_2019-2023.csv` / `_2024-2026.csv`）在全部账户相关改动之后同代码运行，两段各 891 PASS / 168 INFO / 0 FAIL。
4. RP 成功日路径：`diff_ops_s0_to_0751.txt` 只含新增函数与 try 包裹，`choose_pairs_dfs` / `choose_pairs_milp` / `canonical_matching` 逐字未改；推导两段 MILP 9 日、复核失败 0 日；后段恢复 17 日全部在 10 个补跑确定性任务里，随机分片无一进入恢复分支。
5. `hold_init` 默认关，全部登记账户在该改动之前算完。
6. 本登记不复跑任何计算；V 程序只转录本表并与 `source_manifest` / REVIEW_input 的 sha 逐条对（VA07）。
