# E6l brief 附录：执行端自检探针（Stage 0 / Stage A / A1-auto / 运行期 / 闭包；规划端 2026-09-30）

用途：把 plan v1.1 §13.1 六类核验、§16.3 的 129 项合成检查、E6k 复核（VERIFY E01–E09、lessons 27–37、纪律 56–63）里发现的口径问题，落成执行端**开工期与运行期**自己跑的探针清单（不是交付后的 V；V 由决策端另写 `E6l_VERIFY_brief.md`，预期值由脚本从产物现算）。每条探针写：预期值来源 / 容差 / 产物路径；结果进 `stage0/*.csv`、`registration/a1_auto_E6l.json`、`checks/`；任一 FAIL 阻断依赖包。**预期值不由本文手抄**：凡数字均指向 E6k / E6j / E6i / E5a 已存文件或 plan 脚本输出，执行端现算比对。W★ 事实见 brief `E6l_time_memory_stage.md` §0.1。

## A. Stage 0 六类（plan §13.1）

### A1 身份 / 权限
| # | 探针 | 预期来源 | 容差 |
|---|---|---|---|
| A1-1 | 三处输入 sha256 全长：brief、附录、`E6l_proposal.md`（`f79c523a`）、`E6k_REVIEW.md`（`8ef42f86`）、`E6k_RULING_20260930.md`（`b0a87798`）、`E6k_VERIFY_report.md`（`7281cd63`）、`E6k_REPORT_supplement_1.md`（`8b6dedc9`）、`E6k_code_change_register.md`（`fd822bcb`）、协议两件；`PLAN_COPY.md` = plan 全长 sha（前缀 `e7385cb7`，152,579 字节）；`stage0/plan_tests/e6l_spec_tests.py` sha 前缀 `fb9908d6` | 本地镜像 md5 / sha 由决策端随交接给出（`verify/local_exec_briefs_hashes.json` 沿 E6k） | EXACT |
| A1-2 | E6k 原件可读：`results/full/policy_E6k.csv`（`3ab02a59`）、`registry/descriptors_E6k.csv`、`registration/policy_profiles_E6k*.json`、`accounts/<段>/*.npz`、`randoms/`、`verify/probe_results.csv`；E6j `results_P/pilot_policy.csv`、`results_B/part2_main_config_all_objects.csv`、`stage0/anchor2_rerun/e6i_parent_anchor.csv`；三本内部手册 `NOT_REQUIRED`（无可执行定义依赖，brief A8） | 存在性 + sha = E6k `REVIEW_input` / MIRROR | EXACT |
| A1-3 | 授权文件：`record_B_preauthorized_E6l.json`（用户转交消息含 "B" / "事前整表授权" / "按这个完整方案一口气执行" 含两后段）或 `record_B_mode_A.json`（停等）；引用用户原话与日期；`post_gate` 核 `B_package_manifest_E6l.json` **两向实测**（有批准放行 / 暂移拒绝，E6k lessons 17） | brief W11 | 存在 + 两向日志 |
| A1-4 | 四地基 + e6e–e6k + `export_delivery_pools_v2.py` sha = E6k `source_manifest.readonly_code_sha256`（217 文件） | E6k source_manifest | EXACT |
| A1-5 | 数据截止 `market_data_end_max = 2026-03-27`；E7 守卫攻击矩阵 ≥ E6k 入口数（含全程缓存入口、状态序列入口、连续面板入口） | E6k `stage0/c1_identity*/guard_attack.csv` | 全拦截 |
| A1-6 | HEAD `ec91def`；`git status` 只有既知 untracked（7 + 3 + 11 + 2） | E6k `verify/closure_gate_postverify.json` | EXACT |
| A1-7 | 环境锁：Python 3.10.13 / NumPy 1.26.1 / pandas 2.2.3 / SciPy 1.11.3 / statsmodels 0.14.0 / numba 0.58.1；polars 若用写版本与回退；BLAS 线程 ≤ 4 | brief W14 | EXACT |

### A2 源账户与跨轮锚
| # | 探针 | 预期来源 | 容差 |
|---|---|---|---|
| A2-1 | 六形态 α = 0 重现六个 `pool2_*.csv` 逐字节（可引用 E6k c2 A2-1 的 sha 记录并现算一次） | E5a 交付目录 | EXACT |
| A2-2 | 8bp 日账本恒等 net8 = gross − 8e−4·turn（全部 PARENT 与 Q0 NATIVE 账户）；年化 = 252·100·mean | E6k VE01 口径 | 1e−12 |
| A2-3 | R2 / A06 母体四段 net8 = E6i 母体锚；六形态 = E6j 领导表 | E6j `stage0/anchor2_rerun/e6i_parent_anchor.csv`、`carried/leader_six_forms_capital.csv` | 1e−9 |
| A2-4 | **E6k 同构对象逐值锚**：Q / C1 × {NATIVE, HG5, HG10, HG15}、S / M × {NATIVE, HG10}、K0 × HG_ONLY{5,10,15}、PARENT，六形态 × α × H 全部 → D_seg / n_seg / D_sc / FULL / G4 = `policy_E6k.csv` 同 desc_id（举例见 brief W08） | E6k policy | 1e−9 |
| A2-5 | Q（`J_B1_qCC`）与 RARPRE 在 A4b_CVRv5(=R1) / R2 / A06 α .25 H5 = E6j B 块（沿 E6k A2-5） | E6j accounts/B | 1e−12 |
| A2-6 | LEGACY_POLICY_RANDOM 对 Q0 × NATIVE / HG10 × α .25 × H5 的路径结果 = E6k `random_refs_<段>.csv` 同对象（同 path_key → 同 rand_mean / sd / n） | E6k random_refs | 1e−12 |
| A2-7 | E6k `mask_facts_*` 的 HG 目标（n_edits_in / edit_weight_share / 5d reversal / size_edit_gap_T / size_port_delta_T）= 本轮 Stage A 同目标事实 | E6k registry | 1e−9 |

### A3 新算子恒等（每项写 `which_switch_is_off / comparator_id`；真实数据上做，不只合成）
| # | 探针 | 预期 |
|---|---|---|
| A3-1 | `Q_MA1 ≡ Q0`；`Q_DEW(λ=1) ≡ Q0`（短路，无预热要求）；`Q_RANK1` 与 Q0 同支持源秩（报 ties / 覆盖差，不改 Q0 锚） | 逐位 |
| A3-2 | 每种规则 `b = 0 ≡ 同测量 NATIVE`（HG / LAG1 / DECAY / INV / 四调度）；零 bonus 直返 `source_U` 含源 ties（R06） | 逐位 |
| A3-3 | 每种规则 α = 0 = 自己的 ONLY（HG_ONLY / LAG1_ONLY / DECAY_ONLY / INV_ONLY / STATE_ONLY），且 ≠ 原母体（除非 bonus 全 0） | 逐位；报差异日数 |
| A3-4 | `DECAY(L → ∞) ≡ HG10`（用 L = 10⁶ 跑一遍） | 逐位 |
| A3-5 | LAG1 与 HG10 在真实账户上不同：报 `U_{t−1} ≠ G_{t−1}` 的日数与份额（> 0 才说明递归与非递归确被分开） | 计数 > 0 |
| A3-6 | INV 标记排除当日未成交批次：A_i,T 由 τ ∈ [T−H, T−1] 的 W 决定；与 E6k 账户 `d_pos` / `t_wsum` 的持仓时钟一致（T+1 进、T+1+H 出）；H 不同 → 形成名单不同（报差异日数） | 逐位 / 计数 |
| A3-7 | 四调度在 `b_high = b_low` 时 ≡ 固定 HG；UNKNOWN 日 → b10；p_t 只用过去 250 交易日位置的已定义值（不补更早日期） | 逐位 |
| A3-8 | KERNEL_DOSE：C 内均值与 RMS 匹配（`MATCHED_MEAN_RMS`），退化标记 `RMS_UNMATCHED / MATCHED_CONSTANT` 计数；不放大舍入（plan §4.4a tol） | 1e−12；计数 |
| A3-9 | checkpoint 拆分一致性（真实账户各 1 个：HG10 / LAG1 / DECAY5 / INV10 / VOL_HI15 / Q_DEW5）：前 300 日一次跑 = 两段续跑逐位；错股票顺序 / 不连续日期被拒 | 逐位；异常抛出 |
| A3-10 | R-MARK：每条路径分区内标记数守恒；全 0 / 全 1 组计数披露；`折让 0 ≡ NATIVE` | EXACT |
| A3-11 | RANK 延伸源锚：按 `pool_screening_v2.neutralize_by_mcap` 函数体在 u 日 pool0 成员重算 (α, β) 与残差、含 < 10 回退与 precompute 的 < 6 跳过 → 成员残差秩 = 源缓存 `J_B1_qCC` 中性化后逐位；回退日集合一致；池外延伸只在参考 ≥ 2 个不同节点时定义 | 逐位；集合 EXACT |
| A3-12 | 五形态门合同：`E_t = Struct.legal()`；名额 = `dom.K[d]`；Mmean b/3；名额不可行 → 报错不缩（真实数据上 0 次或逐次登记） | EXACT |

### A4 数据 / 时钟
| # | 探针 | 预期 |
|---|---|---|
| A4-1 | 状态序列 PIT：Vol3 / Act3 / Trend3 在截断到 3 个日期（各段各一）的数据上重算 = 全程算出的同日值（前缀不变） | 逐位 |
| A4-2 | 允许历史：段 2–4 的 250 日参考取自全程缓存前段；段 1 STATE_UNKNOWN 日数（Vol3 / Act3 / Trend3 各自）逐段印；`STRICT250` 与 `≥150` 两版 UNKNOWN 日数并印 | 计数 |
| A4-3 | 复权同源：`lclose / close` 与 Q 源 `d` 一致（E6j b1 同字段）；停牌 / 缺报价不前填、真实零 d 保留；零 d 份额、ε 主导份额（d < 1e−4 的比例）逐段印 | 逐位；计数 |
| A4-4 | Q_MA 有效数：`≥ ceil(.6k)` 且当前 d 有效的形成日份额（k = 3 / 5 / 10）逐段印；EW 归一化质量 B 分布 | 计数 |
| A4-5 | 市场收益代理与 Act3 的可得股票数逐日 ≥ 阈值；原"总换手"桥另印 | 计数 |
| A4-6 | 2015-06-15 / 2024-09-24 起 40 交易日窗口的实际起止日 | EXACT |

### A5 随机 / 状态
| # | 探针 | 预期 |
|---|---|---|
| A5-1 | 显式种子：`path_key` 由 measurement / control / path / absolute_date_block / ticker 构成；同 key 两进程同 u 序列 | EXACT |
| A5-2 | 首 1,024 路径固定；增补 512；MCSE ≤ .03 或 8,192；恒等路径 sd = 0（两遍 / Welford） | EXACT |
| A5-3 | R-MARK 分区：ISK 回退树每名恰一叶、叶 ≥ 2；标记保持率、可移动资本、熵逐日 | EXACT / 计数 |
| A5-4 | LEGACY 注入点 = 平滑 / 中性化 / 方向之后、HG 之前；缺失位置不动；OLD_RULE 标 `NO_NEW_CONTENT_TO_PERMUTE` | EXACT |
| A5-5 | 状态调度随机：STATE 对象的随机路径用同一状态序列（状态不随机化） | EXACT |

### A6 输出 / 资源
| # | 探针 | 预期 |
|---|---|---|
| A6-1 | **耗时实测**：合成 + 源锚任务上每条路径的排序 / 递推 / DEV / 账本 / IO 耗时，按段长与池规模外推总量区间，写 R0 与 WORKLOG（plan §9.4） | 报告 |
| A6-2 | 内存 / 线程 / RSS 预算实测；核绑定；并发 ≤ 64 | 报告 |
| A6-3 | 状态词扫描：全部 CSV / JSON / MD 无 `N/A / NA / nan / null` 作状态；`UNDEFINED / NOT_APPLICABLE / NOT_AUTHORIZED / NOT_REQUIRED` | 0 命中 |
| A6-4 | 列名带单位：`_segavg`、`q95_maxabs_t`、`halfwidth_ann_pp`、`ann_pp`、`pct_pt`、`decimal` | 清单 |
| A6-5 | 固定输出十五张表 + brief §9 追加五张的空骨架在 A0 后存在；每个 query_id 一张真实表 | 存在性 |
| A6-6 | 禁用词 / 主机 / 账号 / 家目录 / 连接串扫描 0 命中（沿 E6k 闭包门） | 0 命中 |

## B. Stage A 掩码层事实字段（机械填写，不读收益；每对象 × 母体 × α × 段；INV 与 STATE 按 H）
相对母体换入 / 换出数；自身编辑数（相对昨日）；编辑权重份额；**成员留存率**（K 门成员日到日保留份额）；靠 bonus 续选份额与连续依靠 bonus 日数分布；自然重确认年龄分布；pool spell 年龄；I11 最近触发日龄；真实批次年龄（INV）；INV 标记覆盖率与饱和标志（全域标记日份额）；待到期重合比例；T / CVR 后存活；编辑 5 日撤回份额（只用成熟事件，未成熟另计）；组合层 size 差与紧区间（T / L）；编辑层 gap（带符号 + abs）；后 30% 份额差；未知 size 权重；与 NATIVE / Q0 / QHG10 的编辑重叠；Q_MA 有效数份额；RANK 延伸覆盖（池外有定义份额）；R-MARK 分区叶数与可移动份额；STATE_UNKNOWN 日数；Trend3 三态与 Vol3 / Act3 三分位日数；配对 MDE80（推导段账户后）。

## C. 校准与对照分布（诊断，不作门；plan §10.3 明令不据此改门）
PORT3 ±3 紧区间在 C1 / Q_MA 族 / 随机编辑上的四段分布（分位 50 / 90 / 95）；LEADER lv5 在母体与子上的分布；HG_ONLY 随 H 的曲线（E6k 已见，复现）；Q0 的 H 剖面 H1 / H5 / H20 比（E6k 已见）；对照分布只进 R0 §6。

## D. 运行期与闭包
| # | 项 |
|---|---|
| D-1 | 回执：每任务 `task_status/<task>.receipt.json`（参数 / 输入 / 输出 sha、行数、状态、代码、对照 ID、query 闭包）；FAILED 由同名 `_rerun` 覆盖；队列逐行核对（lessons 20） |
| D-2 | 封存：`seal_deriv.json` / `seal_post.json`（文件 sha、回执计数、队列缺失 0）；封存后读 |
| D-3 | 代码变更登记：Stage 0 之后任何 `e6l_*` 改动逐文件 before / after sha、时间、范围、触发、影响面、等价证据（反向撤回逐字节还原）；语义改动使后代授权失效并重登记 |
| D-4 | WORKLOG 只记操作事实；lessons_delta 六类；不写共享 memory |
| D-5 | 闭包门：无本轮运行中作业（按 PID + 启动时间 + 命令行）；38 遗留进程不动；回执全 SUCCEEDED；禁用词扫描；query_id 唯一；coverage registered == computed；固定输出全在；HEAD 不变直到白名单提交 |
| D-6 | 三处镜像 MIRROR（结果目录 / 47 exec_briefs / 本地 md5 由决策端提供） |

## E. 为交付后 V 预留的产物（V 只读复现要用到；缺一则 V 记 NOT_COMPUTABLE）
`registry/descriptors_E6l.csv`（34,120 + 附属）、`comparison_manifest`（172,440 + 附属视图，含系数 / view / 单位）、`audit_control_manifest`（2,160）、`results/full/policy_E6l.csv`（五列 profile + PORT3_T 正式 + 七列证据状态）、`descriptor_stats_<段>.csv`、`random_refs_<段>.csv`（每路径 FULL / 四段量 / 有效分母 / 逐日均值 / 配对 MC 协方差矩；固定审计路径完整账本）、`random_registry.csv`、`accounts/<段>/*.npz`（子账户逐日 d_* 量 + 目标层 t_* 量 + INV 库存批次 + 记忆状态 checkpoint 哈希）、`memory_age_daily`、`state_clock_ledger`、`state_unknown_days`、`inventory_saturation`、`paired_mde80_deriv`、`turn_cost_frontier`、`frontier_dose_tilt`、`risk_tight_bounds`、`kernel_contracts`、`memory_contracts`、`source_lineage`、`hypothesis_lineage.csv`、`mc_precision`、`completion_coverage`、bootstrap（CP / CN / CC1 / CB / CH / CM / CQ；两单位带列）、`engine_contract.md`、`source_resolution.md`、`code_change_register.md`、`query_registry_E6l.json`、七份 REPORT + REVIEW_input + lessons_delta + limit_register。
