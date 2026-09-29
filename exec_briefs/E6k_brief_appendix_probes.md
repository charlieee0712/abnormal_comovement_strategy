# E6k brief 附录：执行端自检探针（Stage 0 / A1-auto / 闭包；规划端 2026-09-28）

用途：把 plan v1.1 §13.1 六类核验、§16.3 103 项合成检查与 E6j 复核里发现的口径问题，落成执行端**开工期与运行期**自己跑的探针清单（不是交付后的 V；V 由决策端另写 `E6k_VERIFY_brief.md`）。每条探针写：预期值来源 / 容差 / 产物路径；结果进 `stage0/*.csv` 与 `registration/a1_auto.json`；任一 FAIL 阻断依赖包。**预期值不由本文手抄**：凡引用数字均指向 E6j / E5a / E6i 已存文件，执行端现算比对。

## A. Stage 0 六类（plan §13.1）

### A1 身份 / 权限
| # | 探针 | 预期来源 | 容差 |
|---|---|---|---|
| A1-1 | 三处输入 sha256 全长：brief、附录、proposal、E6j REVIEW / RULING / VERIFY / supplement_1 / addendum_1、协议两件；`PLAN_COPY.md` = plan 全长 sha（前缀 `1f9e949c`） | 本地镜像 md5 / sha 由决策端随交接给出 | EXACT |
| A1-2 | E6j 原件可读：`policy_P_operational_addendum.json`、P / B manifest、`parent_identity_map_rerun.csv`、`results_P/supplement_1/*`、`verify/probe_results.csv`、`E6j_D_probes.csv`（本地镜像 47 exec_briefs） | 存在性 + sha 与 E6j `REVIEW_input` / MIRROR 相同 | EXACT |
| A1-3 | 预授权文件：`record_B_preauthorized_E6k.json`（若用户给 B）或 `record_B_mode_A.json`（停等）；引用用户原话与日期 | — | 存在 |
| A1-4 | 四地基 + e6e–e6j + `export_delivery_pools_v2.py` sha = E6j `source_manifest.json` 所记 | E6j source_manifest | EXACT |
| A1-5 | 数据截止：`market_data_end_max = 2026-03-27`；E7 守卫攻击（合成未来行情 / 伪造 sidecar）全部拦截，覆盖矩阵 ≥ E6j 十入口 | E6j `stage0/guard_attack` | 全拦截 |
| A1-6 | HEAD `82b6cf3`；`git status` 只有既知 untracked | — | EXACT |

### A2 源账户
| # | 探针 | 预期来源 | 容差 |
|---|---|---|---|
| A2-1 | 六形态 α = 0 重现六个 `pool2_*.csv` 逐字节；行数 279,649 / 557,683 / 196,546 / 237,213 / 485,751 / 178,572 | E5a 交付目录（sha 见 E6j `anchor1_manifest.e5a_sha256`） | EXACT |
| A2-2 | 6bp `summary.csv` 全列；8bp 日账本恒等 net8 − net6 = −2e−4·turn；年化精确式 net8 = net6 − 0.02·turn·L/n | E5a summary；E6j R0-Q04 | 逐日 1e−12；年化 1e−9 |
| A2-3 | R2 / A06 母体重算 = E6i 已存母体日账本（`stage0/anchor2_rerun/e6i_parent_anchor.csv` 口径） | E6i accounts | ≤ 2.2e−19 |
| A2-4 | 原生 S / M / C1 / SM 主配置（六形态 × α .25 × H5）日账本 = E6j `accounts/P/<seg>/<form>.npz` 同描述符 net8 / gross / pos / turn 逐日 | E6j accounts/P | 1e−12 |
| A2-5 | Q（`J_B1_qCC` low_bad）与四个 RARPRE 源对象在 R1(=A4b_CVRv5) / R2 / A06 上 α .25 × H5 的日账本 = E6j `accounts/B` 同 ID | E6j accounts/B | 1e−12 |
| A2-6 | `LEGACY_POLICY_RANDOM` 8 条路径（主母体 S α .25 H5 2010-2014）u 矩阵 / 掩码 / net8 哈希 = E6j `stage0/replay/serial.json` | E6j replay | EXACT |
| A2-7 | 母体 8bp 四段年化 = E6j carried 领导表 `total_net8_ann`（24 行） | E6j carried | 1e−9 |

### A3 新算子恒等（每项写 `which_switch_is_off / comparator_id`）
| # | 探针 | 预期 |
|---|---|---|
| A3-1 | SZL5 / SZL3 在单一 size 组（强制全池一组）≡ NATIVE 同 α / H | 掩码逐格相等 |
| A3-2 | SZL_OWN：把 SZL 的分组 / 缺失掩码 / 中点秩施于旧 K 后再混入旧 K；G = 1 且同支持时 ≡ 母体 | 掩码逐格 |
| A3-3 | INC γ = 1：d_γ 与 [z − mean, z² − mean] 在集合 C 上正交（内积 ≤ 1e−10）且 mean_C(d_γ) = mean_C(d)；γ0 = `INC_SUPPORT0`；全支持日 γ0 ≡ NATIVE；INC_DOSE 的 mean 与 RMS = INC（1e−12） | 逐日 |
| A3-4 | RP：父名单恒可行；`PAIR_ALL` 与父同 N、同行业人数、同 DEV 每行业单股权重与总资本；τ = ∞ ≡ PAIR_ALL；同一输入两次求解与股票 ID 重排后解相同（词典序唯一） | EXACT |
| A3-5 | LX：合法域锁定后 V00 ≡ B、V11 ≡ C（掩码逐格）；V11 − V00 = (V10 − V00) + (V01 − V00) + 交互，对 gross / net8 / 冲击 net / capital / turn 逐日闭合 | ≤ 1e−12 |
| A3-6 | SA b = 0 ≡ 对应无门账户；PM b = 0 ≡ 无带新门；HG b = 0 ≡ 无带门（含源平局端点） | 掩码逐格 |
| A3-7 | HG 状态：同一路径从不同起点（段首 vs 数据内连续）状态不同则名单可不同（记录差异）；分片重启恢复自身状态后与不分片逐位相同 | EXACT |
| A3-8 | HG_ONLY(α0, b > 0) ≠ 父（编辑数 > 0）；α0 不加载新测量（读取审计） | 计数 |
| A3-9 | TREFIT g = 1 ≡ NATIVE；`COEF_INTERP_UNAVAILABLE` 计数报 | 掩码逐格 |
| A3-10 | POST2 α0 ≡ 父；α > 0 时第二关前实际编辑数 > 0（非 no-op） | 计数 |
| A3-11 | Mmean 的 b 换算：K 腿 b 分位点 ↔ 综合分 b/3，在源 combine 上恒等 | 1e−12 |
| A3-12 | 权重可确定性重算：随机抽 200 个未持久化权重的账户，由掩码 + DEV 输入重算目标权重与日账本 = 已存日聚合 | 1e−12 |

### A4 数据 / 时钟
| # | 探针 | 预期 |
|---|---|---|
| A4-1 | z_T：`negMarketValue` 当日 clean 域 `rank(pct=True)`；与 E6j `e6j_run_p.size_pct_cells` 在 pool0 单元逐位相同（E6j supplement selftest 同法） | 0 差 |
| A4-2 | z_LAG1 = 前一交易日 z_T 按股票对齐（停牌日沿最近可用并标 `size_stale_days`）；无 T−1 者不删 | 计数 |
| A4-3 | 行业长表 `industry_zx_1_all` 日期语义（生效日 / 快照日）写 `engine_contract.md`；形成日 T 使用 ≤ T 的最近记录 | 文字 + 抽样 |
| A4-4 | 日夜 / 涨跌恒等（沿 E6j F01–F12）；`lclose` = 交易所前收 | PASS |
| A4-5 | T+1 VWAP 执行、后复权、右删失标签 ≤ 2026-03-27 | PASS |
| A4-6 | COMMON_SUPPORT 四账户桥（原生父 / 子、共同支持父 / 子）在 CORE / REPAIR / LAYER / TREFIT / POST2 / RAR α .25 × H {3,5,10,20} 齐全 | 计数 = 登记 |

### A5 随机 / 状态
| # | 探针 | 预期 |
|---|---|---|
| A5-1 | 种子 = blake2b(canonical key) → SeedSequence；回执 `generator` 字段按随机量逐类（置换 / bootstrap / IID 复现）写 | 文字 |
| A5-2 | 股票 ID 重排 / 日期切半拼接 / 串并行 / 续跑：8 条路径掩码与 net8 哈希逐位（沿 E6j Z1–Z6） | EXACT |
| A5-3 | 缺失合同：只在同组有限 kf 间双射置换，缺失位置不移动（`test_88` 类） | PASS |
| A5-4 | 八子集分层树：不重叠分区、叶 < 2 不细分；报可移动权重与置换熵 | 计数 |
| A5-5 | HG 随机路径各有自己前日状态（不借真实 HG 状态） | 审计 |
| A5-6 | `LEGACY_POLICY_RANDOM` 与新机制置换分开登记（random_registry 两类） | 计数 |

### A6 输出 / 资源
| # | 探针 | 预期 |
|---|---|---|
| A6-1 | profile：RP / HG / LX / CORE / 随机各一代表任务的 wall、RSS、线程；写 `stage0/profile.csv`；> 30 分钟队列先报用户 | 文字 + 数 |
| A6-2 | 日账本 schema（W10 字段）齐；bit-packed 掩码 n 位 = pool0 单元数 | 计数 |
| A6-3 | 费用恒等两条（A2-2）对全部账户抽样 500 | 1e−12 |
| A6-4 | plan §16.3 脚本提取 sha = plan 所记 `ebc9d4eb…`；在 47 环境 103 / 103（环境差只改 harness） | EXACT |
| A6-5 | A0 编译 39,142 / 段 + 72 附属 + 144 主展示唯一存在；与 §16.3 `compile_design` 元组逐一比对 | EXACT |
| A6-6 | query_id 跨文件唯一；每张卡 `queries` 非空；固定输出清单（plan §13.5 表）逐项打勾 | 计数 |

## B. A1-auto 掩码事实字段（机械填写，不读收益；每对象 × 母体 × α × 段）
`n_edits_in / n_edits_out`、`edit_weight_share`（换入者目标权重份额）、`same_ticker_overlap_with_native`（新算子与同测量 NATIVE 的换入重叠比例）、`layer_shift_ISK`（行业 × size3 × 旧 K3 配额差向量）、`size_edit_gap_T / _LAG1`（带符号）、`size_port_delta_T / _LAG1`（组合层带符号）、`small30_share_delta`、`size_unknown_weight`、`fallback_reason / fallback_weight`（按算子）、`arm_overlap_S_M`（两臂改同一批票的比例）、`second_stage_survivors`（A4b：第一关新候选穿过第二关数）、`cvr_blocked`（被 CVR 挡回数）、`edit_persistence_5d`（编辑 5 日内被撤销比例）。**用途只有两个**：触发预冻结的数学回退 / 不适用标注；作 REPORT R0 的描述表。不生成阈值、不挑臂。

## C. 对照分布（诊断，不作门；plan §9.3 明令不据此改门）
在 C0（恒等）、C1（NATIVE_C1 主配置）、`LEGACY_POLICY_RANDOM` 与新机制 IID 路径上算：组合层 size 差（T / LAG1）、编辑层 gap、Δturn、冲击 net 差、小盘 30% 份额差的分布（q10 / q50 / q90 / p95）；写 `stage0/control_distributions.csv`；REPORT R0 印表并注明"未用于任何门值"。

## D. 运行期与闭包
| # | 探针 | 预期 |
|---|---|---|
| D-1 | 封存：`seal_deriv.json`（推导段）与 `seal_post.json`（后段）列全部文件 sha；读数文件 mtime 晚于对应封存；后段回执晚于授权核验回执 | 时序 |
| D-2 | 回执：FAILED 由同名 `_rerun` 成功覆盖；计数行写"截至哪个回执之前" | 计数 |
| D-3 | 政策 / MC 口径若有执行端声明，落 `policy_operational_addendum.json` 于**读数前**（E6j 先例）；dryrun 只用合成数据 | 时序 |
| D-4 | 中间文件带 attempt 后缀不覆盖；试跑写临时目录 | 审计 |
| D-5 | 进程：只管理自身进程组；`pgrep -f` 自匹配循环禁用（用 PID `kill -0`）；遗留 38 个不动并再列一次 | 清单 |
| D-6 | 闭包门：无运行中 E6k 作业；回执状态计数；query_id 唯一；报告扫描（禁用词 / 主机 / 账号 / 家目录 / 连接串）；登记对象全有账户（每段 39,142 + 72 + P） | PASS |
| D-7 | MIRROR 三处 md5 / sha；REVIEW_input 列全部路径与 sha；`limit_register.md` L01 起 | 文字 |

## E. 为交付后 V 预留的产物（V 只读复现要用到；缺一则 V 记 NOT_COMPUTABLE）
掩码（全部）；日聚合账本（全部，含 size 两坐标列）；固定清单的日目标权重与滚动持仓；随机每路径 / 每段统计 + 预指定样本路径完整日账本；bootstrap 段内索引种子；`hypothesis_lineage.csv`、`hypothesis_outcomes.json`（八字段卡）；两套 profile 的逐对象政策表与 `policy_profiles` 机器表；`mask_edit_ledger`、`risk_exposure_daily`、`layer_transplants`、`random_registry`；A0 两张对账表；`control_distributions.csv`；全部回执。
