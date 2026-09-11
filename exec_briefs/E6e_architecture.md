# E6e —— 最终 brief（v1，2026-09-06）：底座 × 深度 × 否决的联合架构地图，带匹配对照、随机对照与两层不确定性

> **版本与来源**：规划 session 审 Claude web 的 plan 后写成，是 E6e 唯一有效执行文件。web plan = `exec_briefs/plans/E6e_plan_web_final.md`（v1.0，SHA256 `8c052ec1ee95c1d2fc483732dff2272e733b16a0ca52563c4520d7b10149b760`）；proposal = `exec_briefs/E6e_proposal.md`（初版，其 §1.2 的 DEV 仓位机制写反，见本文 §0.1，已在原文加勘误）。执行端以本 brief 为准；本 brief 未写到的实现细节按 web plan 对应小节执行；冲突以本 brief 为准。先读 `00_协议.md`；末尾有自审记录。

## 0. 一句话问题与设计结论

**在既有 I11 候选域与 DEV 资金约束下，底座怎样筛、否决怎样用，才能改善当前完整策略的净表现；观察到的改善，分别来自股票成分、资本使用、行业结构还是交易成本？** 本轮同时做两件事：画出"核族 × 深度 × 否决方式"的完整地图，并用三类对照（同人数剔深、反向、随机）把每个增量拆成可复核的账。**只出地图与账，不定 v3、不开 E7、不改生产。**

### 0.1 相对 web plan 的采纳与调整（规划 session 决定）

| web plan 内容 | 处置 |
|---|---|
| **DEV 仓位机制更正**：`u(n)=min(1/n, 1%)`，`P(n)=min(1, 0.01n)`；n<100 时 1% 上限绑定，剔票**降仓位**（80→60 只 = 0.80→0.60）；n>100 时 1/n，剔票不降仓位；含行业削顶时剔票甚至可能升仓位 | **采纳**。规划 session 已按 `assign_weights_dev` 源码复核：`w = np.full(n, min(1.0/n, max_stock))` 后行业 `cap = share+0.03` 按比例缩减。**我们的核多在 40–95 只，处于 1% 上限绑定区**：否决剔 15% 名额即降仓位 15%，绝对超额按仓位缩水，因此 E6b 观察到的净增益 +1.2～2.0 是在"仓位先降"之上实现的，随机对照会给出它的基线 |
| 核族 P54（9 族 × 6 档）+ 阶段分配 48 + 结构守卫 12 = **P114** | **采纳** |
| 基础硬否决 19 种 × P114 = 2,280 经济配置 | **采纳** |
| P54 上复合毒性 18、条件豁免 8、软否决 6 起点 × 7 权重 = 1,404 + 2,268 | **采纳**（软否决输出为 `research_overlay`，不改生产权重函数） |
| 缺失三值逻辑、`known_only` 双胞胎、两层随机对照（全操作 / 有效毒性） | **采纳**；规划 session 已核 `drop_mask = pool0 & ~kept` 确实把无因子值的票也算作剔除 |
| 匹配对照：同人数剔深 `coretrim_matchN`、阶段分配同预算、相对/池级拆分、反向否决（同 m）、等仓位双边向下缩减 | **采纳，全部子配置都做**（硬、复合、豁免、软覆盖层）；不按核族缩范围（初稿曾限 P54 系，已撤回） |
| 随机对照三种 profile（U-IID / I-IID / I-P5），软起点另 I-P20；**128 路径**；MCSE>0.10 追加至 256/512 | **采纳，全部按 web 的统一口径**：3,570 条规则（P114 × 19 硬 + P54 × 26 复合/豁免）三种 profile 各 **128 路径**；软否决 6 起点 × 7 权重复用同一随机剔除集合、每个 λ 各自构造权重并算自身成本，I-IID 与 I-P20 各 128；P54 六个软起点另做 `industry×core_quality_tercile` 与 `industry×liquidity_tercile` 两种分层的 gross 诊断与 128 路径成本对照。追加只由 MCSE 触发。（初稿曾按核族分层削减路径数，用户 2026-09-06 指出过严，已撤回：算力不是约束，不能因"扩展核不那么重要"的先验给它更弱的对照） |
| I-IID 的解析期望 gross | **采纳为对账与 gross 的主估计**（成本仍由路径模拟） |
| 分位映射 p→g、`rank_budget_diagnostic` 双胞胎、历史构造原样保留 | **采纳**；`DEP(50,50)` 与 A4b 的 mask 相等作**软锚**（E6d 已证十分位 (50,50) 与二分组 DEP 逐位相等；不等则报告不中止） |
| 不设 v3 硬筛法；四种视图 + 非支配集合 + 近邻平台 | **采纳** |
| 统计：HAC L=5 主列 + 20/60 敏感性、fixedmix、bootstrap B=2000 块长 60（20 敏感）、F1–F5 族、两层（日期+MC）敏感性 | **采纳**（bootstrap 只对确定性配置与随机均值序列做，不对每条随机路径） |
| 一次完整排程 A→G，不按中途效果申请 | **采纳，但加一次中间交付**：确定性阶段（A–D）完成即出 `REPORT_part1`（地图 + 匹配/反向对照），随机阶段（E）与两层统计（F）完成后出 `REPORT_part2`。两份都不含采纳判断 |
| 耗时诚实：先在 2010-2014 与 2024-2026 各做固定配方计时再报总预计 | **采纳**；并**要求向量化 DEV 权重与批量引擎**（见 §5），批量内核须对每种 profile ≥8 条路径全日期与参考引擎逐日核对（atol 1e-12） |
| 分区 hash 键、DONE 绑定 plan/源码/数据/registry/随机版本 | **采纳**（按 shard 落盘，临时文件校验后原子改名） |
| 图表 | 可选；文本表与 CSV 必需 |

## 1. 起点确认与引擎 contract

### 1.1 起点
1. 47 `git status -sb` 应为 `## main...origin/main [ahead 2]`（E6d 的 `c3002b8`、`e957f2e` 未推）；核 `93b0d4e` 为祖先；`comprehensive_factor_diagnosis.py`、四地基、`e6_wide_scan.py`、`e6b_stack_sleeves.py`、`export_delivery_pools_v2.py`、`e6d_*.py` 的 blob 与上一轮 manifest 一致。**不 reset、不强推。**
2. 引擎默认值 `(5, 8, 1, True)`；`C.COST_BP_BILATERAL == 8.0`。
3. 输入存在：E6b `scan_all.csv` + `daily_all.parquet`；E6d `full_summary.csv`、`preregistration.md`、`limit_register.md`、各段 `sf_*` 与 `daily_*`；E6 `roles.csv`；四段冻结缓存。
4. `run_manifest.json`：Python/numpy/pandas 版本、`PERIODS`、上述文件与脚本 SHA256、本 brief 与 web plan 的 SHA256、实际时间与时区。
5. `ps` 无本项目残留；记录 available RSS 与 socket 1 负载；并发上限按实测定（初始 ≤32 进程，BLAS 线程 1）。

### 1.2 数据与生产锁
四段独立加载，`legacy_all` 口径；信息 ≤2026-03-27；不读 E7 目录、不重建延长缓存。每次引擎调用显式 `hold_days=5, cost_bp_bilateral=8.0, exec_lag=1, adjust=True`。不改池、不加因子、不改 I11、不改生产 DEV 函数；软否决只写研究覆盖层。

### 1.3 引擎 contract（规划 session 已核；执行端整段读函数体复核并写 `engine_contract.md`，不符处单列）
- `compute_calendar_pnl`：`actual = W.rolling(5, min_periods=1).mean()`；`ah = actual.shift(2)`；`port = (ah × r̃).sum(axis=1)`（收益 NaN 记 0）；`position = ah.sum(axis=1)`（权重照算）；`bench = r.where(clean==1).mean(axis=1)`；`gross = port − bench × position`；`turnover = 0.5Σ|ah_t − ah_{t−1}|`（首日 0）；`cost = turnover × 8/1e4`；`net = gross − cost`。停牌日与复牌当日收益均 NaN。
- `assign_weights_dev(hold, industry, shares)`：`w = min(1/n, 0.01)` 对当日全部保留股；对每个**已知**行业 `cap = clean 行业占比 + 0.03`，若该行业权重和 > cap 则组内等比缩减；行业为 NaN 的票不受行业约束；无下限、不归一。→ `P(n) = min(1, 0.01n)` 再减行业削顶。
- `precompute_neutralized_factor(raw, S, log_mcap)`：逐日在 S 内取因子与 log 市值同时有效的票，`neutralize_by_mcap` 截面 OLS 残差；**有效票 <10 只时返回原始因子值**（不中性化）；<6 只该日无缓存。
- `build_factor_strategy_holdings_cached(neu, S, k, drop)`：有效值 <3k 只该日无持仓；`qcut(rank(method='first'), k)` 组 1 最低；`ValueError` 跳过。
- `combine([pct…], 'mean')`：日期取交集；`DataFrame.mean(axis=1)` **skipna**——成员缺某因子时按其余因子均值。
- `drop_mask(neu_f, pool0, k) = pool0 ∧ ¬kept`：**未分组/无值的票也被算作剔除**（§3.5 的三值逻辑据此设计）。
- 观察池 = `Σ_{lag=1..5} signal.shift(lag) > 0`，触发日龄 1…5；硬约束 `is_open==1`、非涨跌停、上市 ≥20 日、20 日均成交额 ≥2000 万、`min_mcap=0`。
- 若复核与上述不符：先写进 contract 并定位到新增包装层；确属引擎问题则冻结受影响输出并报告，不改引擎。

### 1.4 事前登记
在**首次收益评价之前**落盘 `preregistration.md`（沿 E6d 格式）：六个开放式问题（web §2K 的 H1–H6）、对照定义、随机 profile 与路径数政策、比较族 F1–F5、两个固定参照 R1/R2、注册表四件（`config_registry.csv / comparison_registry.csv / randomization_registry.json / analysis_families.json`）的 SHA。登记后任何修订另起 `preregistration_amend_<日期>.md`。

## 2. 注册表：核与否决（按 web §2B–2D，数字为事前描述符数）

### 2.1 因子与方向
K = conditional_turnover、T = turnover_volatility_60d、C = CVR_20d，均高 = 坏；否决族另含 cr5 = cum_return_5d、cr20 = cum_return_20d、cvr_1d = intraday_cvr_1d、ci5 = cum_intraday_ret_5d（均高 = 坏）。方向从 E6 `roles.csv` 读。

### 2.2 核（P114）
- **P54**：`{T, K, C, KT_mean, TC_mean, KTC_mean} × s∈{20,25,30,35,40,50}%`（36）+ `{KT_dep, CT_dep, K_gate_TC} × (a,b)∈{(45,45),(50,50),(55,55),(60,60),(65,65),(70,70)}`（18；名义最终比例 20.25/25/30.25/36/42.25/49%，登记 `a×b` 原值）。
- **阶段分配 48**：三种两阶段族 × 16 对 `(40,50),(50,40),(40,60),(60,40),(50,60),(60,50),(70,35),(35,70),(80,30),(30,80),(90,30),(30,90),(80,50),(50,80),(90,50),(50,90)`。100% 端点由单因子 / `TC_mean` 真正 bypass 未用因子，映射写入 registry，不另造同名配置。
- **结构守卫 12**：反序 `T→K`、`T→C` 各 `(50,50),(70,35),(60,50)`；`KT_dep / CT_dep / K_gate_TC` 的 **nr 版**（第二阶段沿 pool0 中性化值、只换排序范围）各 `(50,50),(70,35)`。
- 公式：`KTC_mean` = 三因子分别在 pool0 中性化、各自 pct、等权均值，**新三因子主版本要求当日三分量均有限**；`K_gate_TC` = 先按 K 留 a%，在 S1 内分别重中性化 T 与 C、分别重算 pct、取均值留 b%；nr 版沿 pool0 中性化值但在 S1 内重算 pct。既有 `KT_mean/TC_mean` 保留源 skipna 行为以保锚，并对 P54 含复合配置另生成 `complete_components` 双胞胎（权重相同则别名复用）。
- 分位实现：历史构造原样（A4b 两次二分、keep30/20 十分位、E6d SF25/CMEAN25 四分位）；新分支按固定映射 `p→g = {20:10, 25:4, 30:10, 35:20, 40:10, 45:20, 50:2, 55:20, 60:10, 65:20, 70:10, 75:4, 80:10, 90:10}`，保留最低 `g·p/100` 组；100% bypass。首次收益调用前锁定。另生成 `rank_budget_diagnostic` 双胞胎（同分数排序、稳定 tie 键、恰好保留 `ceil(s·n_valid)` 只），只作诊断。

### 2.3 基础硬否决（19 种 × P114 = 2,280）
单否决 12：`{K, C, cr5, cr20, cvr_1d, ci5} × {k5, k10}`；C×cr5 四种：`C{k5,k10} × cr5{k5,k10}`；其他双否决 3：`cvr_1d:k10+cr5:k10`、`ci5:k10+cr5:k10`、`C:k10+cr20:k10`。全部池级（pool0 分位、生产坏方向、原 helper）。双否决必报 `CB−C`、`CB−B`、`CB−core` 与对称分摊 `phi_C = 0.5[(Y_C−Y_0)+(Y_CB−Y_B)]`、`phi_B` 同理；被剔集拆 `C_only / B_only / both`。

### 2.4 否决方式扩展（只在 P54 上；不看结果选父）
- **复合毒性 18**：`{(C,cr5),(cvr_1d,cr5),(C,cr20)} × {mean,max,min} × 剔最高 {1/5,1/10}`；复合分要求分量共同有限；与原 OR（并集）在 §3.1 同 m 对照下比。
- **条件豁免 8**：起点 `{C:k5, cr5:k10, C:k10+cr5:k10, C:k5+cr5:k10}` × 豁免父核核心质量最好 `{10%, 25%}`；质量分 = 该核实际末级排序分（DEP 取固定第一阶段后的末级分）；任一否决分量在 pool0 坏向 pct ≥0.95 不豁免；另出"同剔除人数的更窄原否决"与"同一可豁免毒尾中随机救回同样只数"两条对照。
- **软否决 6 起点 × 7 权重 = 2,268**：起点 `{C:k5, cr5:k10, K:k10, C:k10+cr5:k10, C:k5+cr5:k10, C:k10+cr20:k10}`；`W0 = DEV(core)`，`WH = DEV(core∖D)`，`WZ = W0·1{未被剔}`；**冻结父权重降权** `WSλ = W0·(1 − λ·1_D)`，λ∈{0.25,0.5,0.75,1}（λ=1 即 WZ，释放资本留现金）；**父—硬插值** `WBλ = (1−λ)W0 + λWH`，λ∈{0.25,0.5,0.75}。输出到 `research_overlay`，与原生 DEV 分栏。

### 2.5 参照
R1 = `A4b_CVRv5@H5`（生产终形态）；R2 = `M_mean2@keep30|CVR_20d:k5+cum_return_5d:k10@H5`（E6b 样本内最强，非生产）；两者数字从 E6b `scan_all.csv` 与 `daily_all.parquet` 读，不抄摘要。

## 3. 对照

### 3.1 同人数剔深 `coretrim_matchN`
对每个真实子配置，逐日在同一父核内按该核已冻结的末级质量分保留恰好 `r_t` 只（= 子配置当日实际保留数），过 DEV 与引擎。DEP 第一阶段不动。P114 × 19 硬 + P54 × 26 → ≈3.7k 配置。
### 3.2 阶段分配同预算 `allocation_matchN`
三种两阶段结构 × q∈{20,25,30,40,50}% × a∈{q,40,50,60,70,80,90,100}%（a≥q），共同可观察域 U_t 上 `r_t = ceil(q·|U_t|)`；作诊断，不升格为候选。
### 3.3 相对 / 池级拆分
在 P54 对 `{C, cr5, cr20}`：① pool0 k5/k10（既有）；② 同 pool0 中性化值、父内固定剔 10%/20%；③ 同分数、父内剔与①同 m_t；④ 父内重中性化、共同域剔同 m_t。报 ②−①、③−①（应≈0，结构自测）、④−③（重排差）。
### 3.4 反向否决
P114 × 12 单否决：主对照 = 同父同有效域**剔最好 m_t 只**（m_t = 正向实际已知毒尾数）；同 k 自然反向另附。双否决不做反向。
### 3.5 缺失与"假毒尾"
逐日逐规则记 `known_toxic / known_non_toxic / unscorable / technical_failure / removed_legacy`；联合规则三值逻辑。历史硬配置沿原处理复现；新增复合/豁免规则 `known_only`（不可判断者留在父中）；旧规则另出 `known_only` 双胞胎。随机对照两层：全操作对照（同父随机剔同总数）与有效毒性对照（固定未知/技术剔除位置，只在可判断域内随机置换真实毒尾名额）。
### 3.6 等仓位配对（全部子配置，含软覆盖层）
`W0_down = W0·min(1, P1/P0)`，`W1_down = W1·min(1, P0/P1)`，只向下缩，两边各跑引擎；报 `原子−原父` 与 `down子−down父`。零仓位日两边同为 0，不做 0/0。软覆盖层以 `WSλ / WBλ` 为子权重同法处理。
### 3.7 随机对照（web §2G，全部规则统一 128 路径 × 3 profile）
- profile：**U-IID**（同父、同有效域、同剔除总数，每日独立随机优先级）、**I-IID**（再匹配每行业剔除人数，未知行业为一类）、**I-P5**（I 匹配 + 股票随机优先级为 AR(1)，`z_t = ρ z_{t−1} + sqrt(1−ρ²) ε_t`，ρ = exp(−1/5)）；软起点另 **I-P20**（ρ = exp(−1/20)）。
- 覆盖与路径数（统一，不按核族分层）：全部 3,570 条剔除规则三种 profile 各 **128 路径**，从 seed 0 起；软否决复用同一随机剔除集合，每个 λ 各自构造 `WSλ / WBλ` 并算自身成本，I-IID 与 I-P20 各 128；P54 六个软起点另做 `industry×core_quality_tercile` 与 `industry×liquidity_tercile` 两种分层（流动性 = 形成日可得的 20 日成交额均值，至少 10 个有效日；三分位在当日父核可观察成员内定）的 gross 诊断与 128 路径成本对照，分层分别做、不联合匹配。名义路径约 200 万条/段、四段约 800 万（同权重 hash 可复用）。
- 随机键：`SHA256("E6e-v1", profile, seed, date, ticker)` 派生优先级；同父不同 m 共用优先级（嵌套集合）；AR 状态按 ticker 全路径确定性重建，与 shard/并发顺序无关；禁用 Python `hash()`。
- 每条路径独立：名单 → DEV/覆盖层 → H5 → 逐日 gross/成本/net；**严禁先平均权重再跑一次引擎**。
- 输出：`increment_vs_random = Y_child − mean_b(Y_random,b)`（gross / cost / net / 两基准分别）；路径均值、sd、分位、`MCSE = sd/√R`、32/64/128 前缀稳定性、`z_distance`（sd=0 记 NA）、`random_design_tail_fraction = (1+#random≥real)/(R+1)`（**不是 p 值**）。
- I-IID 解析期望 gross：幸存者权重 `v_h = min(u(r), cap_h/r_h)`，父股票期望目标权重 `(r_h/n_h)·v_h`，用于 gross 对账与主估计；成本只用路径。
- 追加规则：128 路径后若预登记规则的年化 gross 或 net 随机均值 MCSE > 0.10 点，按同规则追加至 256、再 512；只由 MCSE 触发；到 512 仍不足标 LIMIT。
- 保留逐 seed 日序列（parquet 分块）供两层推断。

## 4. 账与统计
- 日账本每配置：`port, bench_clean, position, turnover, cost8, gross, net8, net12 (= net8 − turnover×4/1e4), n_target, n_live, hhi_live, effective_n, max_weight, sector_weights, binding_cap_count`；比例分三列 `core_keep/pool0`、`final_keep/pool0`、`final_keep/core`。
- 分解四组：硬否决原增量 `Y(WH)−Y(W0)`；冻权删票 vs 幸存者再配置 `[Y(WZ)−Y(W0)] + [Y(WH)−Y(WZ)]`（gross 与成本分别）；相对随机基线；同人数剔深与等仓位实跑对照。
- 单位资金两口径 `mean(Y/position)`（仓位>0 且收益已知日）与 `ΣY/Σposition`（共同支持）分别报；零仓位日费用单列。
- 成本情景 8 主 / 12 解析；相对参照的 `c* = Δgross/Δturn`（Δturn≈0 与负值单列）。
- HAC：主列 L=5，敏感性 L=20/60；缺口用 score-HAC（缺失处 u=0）；`nw_full_concat` 与 `nw_full_fixedmix` 两列。
- bootstrap：stationary、块长 60（敏感 20）、B=2000、按段、所有序列共用日期 draw；族 F1（全部经济配置 vs R1，8/12bp）、F2（vs R2）、F3（真实规则 vs 对应随机均值，按 profile）、F4（真实 vs `coretrim_matchN`）、F5（软 vs 自身硬与无否决端点）；逐点区间 + 各族同时带 + F1+F2 联合带；恒等/零方差记 0 与原因。
- 两层（日期 + MC）敏感性：对 F3 与软起点，先有放回抽 seed 编号再抽日期。
- 逐年、留一年、最差段、超额回撤（注明是超额记账）、行业/市值/成交额分位、可成交性疑似暴露（按执行日与买卖方向）。

## 5. 运行组织（A→G 一次排程，两次交付）
- **A** 起点、contract、manifest、注册表四件、事前登记、玩具测试（§6.1）。
- **B** 历史锚（§6.2）与 P114 核（含深度梯子、守卫、双胞胎）。
- **C** 基础硬否决全网格 2,280 + 反向 + 同人数剔深 + 等仓位（P54 系）。
- **D** P54 复合 / 豁免 / 软 + 其对照 + 相对/池级拆分 + 阶段分配诊断。→ **出 `REPORT_part1`**（地图 + 确定性对照，无采纳判断）。
- **E** 随机路径（U/I/P5 全规则 128；软 I-IID/I-P20 128；分层诊断）、MCSE 追加、解析 gross 对账。
- **F** 配对统计、bootstrap、两层敏感性、年度/留一年、风险与可成交性。→ **出 `REPORT_part2`**。
- **G** WORKLOG、whitelist add（新脚本、brief、必要文档）、`git push origin main`（含 E6d 两个 commit）。

**计时与实现要求**
- 在 2010-2014 与 2024-2026 各跑一组固定配方计时（名单构造、DEV、引擎、随机批、落盘、bootstrap），据实际日期数/资产数/唯一权重数给各阶段与总 wall 预计；>30 分钟只是告知，不缩范围。量级参考：随机路径约 800 万条，向量化后单路径约 0.05 s 量级 → 数小时到十几小时；未向量化则一两天。**都可接受**（用户：算力与时长不是约束），但必须先计时再报，且随机阶段（E）在确定性交付（part1）之后跑。
- **必须向量化**：DEV 权重按日 numpy（`min(1/n,0.01)` + 行业 bincount 缩减）替代逐日 groupby；批量引擎把多条权重矩阵堆叠（rolling 用 cumsum 差分）一次算；批量内核对每种 profile ≥8 条路径全日期、每个确定性阶段 ≥50 个配置与参考引擎逐日核对（gross/position/turnover atol 1e-12）通过后才可用于正式输出；未通过不许降精度或删退化日期换速度。
- 分片：按（段 × 核族 × 规则块 × profile）shard；每 shard 临时文件 → 校验主键/行数/hash → 原子改名 → `DONE` 文件绑定 plan/源码/数据/registry/随机版本 hash；续跑不重复累加、不丢 seed=0。
- 并发：初始 ≤32 进程，BLAS 线程 1；按 RSS 与负载调；不嵌套 joblib。
- 存储：随机稠密权重不永久保存；保存可重建 seed/状态、集合 hash、逐 seed 日账本（float64，parquet 分块）；写前估磁盘。

## 6. 自测与验收（只对正确性设硬条件；收益/z/区间/某段弱不是 BLOCKER）

### 6.1 玩具测试（正式收益评价前）
1. DEV：80→60、150→120、跨 100、行业削顶、删票后总仓位上升的反例。
2. 同人数不同仓位；同行业人数匹配后目标行业权重/仓位/HHI 一致，live HHI 不必一致。
3. 分数方向、闸端点 bypass、quantile ties、小样本与原始/残差回退、三因子共同有效。
4. 正向/反向/同人数剔深的数量与域；双否决并集/交集恒等式；`phi_C+phi_B = Y_CB−Y_0`。
5. 缺失不是坏尾：三值逻辑、legacy/known_only 分支可区分。
6. 随机：每日每行业计数；zero/all/one-name 层；seed、ticker 重排、任务乱序、续跑/分片不改结果；AR 前缀因果。
7. 软：WS/WB 端点与可行性；WZ≠WH 反例；成本不等于端点线性混合。
8. 真实 − 随机均值两种差法一致；I-IID 解析期望 gross 与小宇宙完全枚举一致。
9. 日频/年化 8/12bp 恒等式；共同有效分母；零仓位/全 NaN 不误作 0。
10. 同 m 原分数重排恒等；(65,65)=42.25% 标签；核末级分冻结。
11. bootstrap 共同日期与 seed、缺口/段界、零方差、联合族不 nanmax 漂移。
12. dummy 全流程：格式串、配置键、merge、空表、恢复标记、重复主键、CSV/parquet round-trip。

### 6.2 锚点
- 外部源锚（TOL 0.02，同时报所有非零差；有同源日序列时 `max|diff| ≤ 1e−10`）：E6b `A4b / M_mean2@keep30 / M_mean2@keep20 / A4b|CVR_20d:k5 / A4b|CVR_20d:k10+cum_return_5d:k10 / M_mean2@keep30|CVR_20d:k10+cum_return_5d:k10 / M_mean2@keep30|CVR_20d:k5+cum_return_5d:k10 / A4b_var_c60_t50 / c50_t60 / c40_t50`；E6d `SF25:T / SF25:K / SF25:C / CMEAN25(K,T) / CMEAN25(T,C) / DEP(C→T) / DEPnr(K→T)` 与深度网格 `(60,40)(70,35)` 行。不存在的行不捏造。
- 内部锚：`KT_dep(50,50)` mask 与 A4b 逐票相同（软锚，E6d 已证；不等则报告）；`KT_mean@50` = `M_mean2`；无否决 = 父；软 λ=0 = 父、桥 λ=1 = 硬；同 m 同排序身份；`coretrim_matchN` 人数恒等式。
- 会计：`gross = port − bench×position`、`net = gross − cost`、`net12 = net8 − turnover×4/1e4`、同表同掩码年化；批量内核 vs 参考引擎逐日 atol 1e-12。
### 6.3 完成定义
每个 registry 描述符状态 ∈ {DONE, ALIAS, NOT_ESTIMABLE(reason), BLOCKED(reason)}，不得静默 SKIP；全部经济格与既定对照状态齐、日账本与汇总一致、hash 齐。**不要求产生改进配置。**

## 7. 交回
- `results/<ts>_E6e_architecture/`：`PLAN_COPY.md`、`preregistration.md`、`engine_contract.md`、`run_manifest.json`、四件注册表、`alias_map.csv`、`run_state.json`、`checks/{toy,anchors,daily_identities,batch_vs_reference}.csv`、`daily/<seg>/<shard>.parquet`、`random_daily/<seg>/<shard>.parquet`、`summary/{all_candidates, core_depth, veto_marginals, random_controls, matched_count, relative_rerank, soft_and_reallocation, conditional_exemption, attribution, paired_vs_references, yearly, leave_one_year, neighborhoods_and_frontiers, coverage_and_execution}.csv`、`bootstrap/<family>.parquet`、`limit_register.md`、`source_corrections.md`、`summary.txt`、`logs/`。
- `exec_briefs/E6e_REPORT_part1.md`（阶段 D 后）与 `E6e_REPORT_part2.md`（阶段 F 后），协议结构；摘要各 ≤15 行，回答 web §4.5 的问题，**不写"该换核 / 最终架构已定 / 34 因子饱和 / 可交付"**。`source_corrections.md` 记本轮对既往说法的收窄（含 proposal 的 DEV 机制勘误）。
- WORKLOG 远端 + 本地镜像同文。
- git：whitelist add `e6e_*.py`、本 brief、`source_corrections.md`；`git push origin main`（连带 E6d 两个 commit）；不 `git add .`、不 force。

## 8. 禁区
不碰 E7、不延长、不用未来数据选股；不改四地基、引擎、I11/pool0、原始因子、生产 DEV；研究覆盖层不写交付或公共库；不按中途 net/z/t 淘汰；不把随机对照当随机实验、不把日期 bootstrap 当搜索校正；不对插值收益或平均权重的随机净值作结论；不承诺改进幅度；不用 `git add .`；REPORT 不下采纳结论；不出现登录信息与主机地址。凡遇"必须改上述任何一项才能继续" → 停，写 BLOCKERS。

## 9. 自审记录（规划 session 2026-09-06；执行端见此段方可开工）
| 类 | 不利因素 | 处置 |
|---|---|---|
| 事实 | proposal 把 DEV 仓位机制写反（n<100 才是 1% 上限绑定、剔票降仓位） | 按源码复核 web 的更正，写进 §1.3；proposal 原文加勘误；随机对照与等仓位配对因此更重要 |
| 事实 | `drop_mask` 把无值票算作剔除；`combine` skipna | 已核并写进 contract；三值逻辑与 `known_only` 双胞胎覆盖 |
| 规模 | 随机路径约 800 万条（含软与分层诊断），单路径逐日跑要数天 | **不削路径数、不按核族分层**；时间靠向量化 DEV 与批量引擎（与参考引擎逐日对账）、分片与 DONE、两次交付来管；先计时再报预计 |
| 节奏 | 一次排程到底会让确定性地图等随机阶段几小时到几天 | 阶段 D 后出 `REPORT_part1`，随机与两层统计后出 `part2`；两份都不含采纳判断 |
| 统计 | 数千配置里挑最大值乐观 | 无硬筛法；四视图 + 非支配集合 + 近邻平台；F1–F5 预登记族与联合带；`random_design_tail_fraction` 明示非 p 值 |
| 统计 | 随机对照的 MCSE 被当市场不确定性 | MCSE 与 HAC/bootstrap 分开；两层敏感性 |
| 统计 | I-P5 的 AR 尺度只是设定 | 报真实与随机的成员变更率、连续被剔长度、live 重叠、换手，剩余差异明示 |
| 混杂 | 同人数 ≠ 同仓位 ≠ 同行业；n<100 区剔票必降仓位 | I-IID 行业匹配、等仓位双边缩减、live 账本；分解四组 |
| 混杂 | 软否决 λ=1 被当硬 DEV | WZ 与 WH 分列；冻权删票与再配置精确拆分 |
| 混杂 | 随机权重先平均再算成本 | 每路径独立成本；解析只用于 gross |
| 数值 | 20 分位薄日空仓、并列值 | 历史构造原样保锚；固定 p→g 映射；`rank_budget_diagnostic` 双胞胎；报差异日贡献 |
| 数值 | 二阶段 universe <10 只中性化退化 | 报每核每段中位与 <10 只天数（E6d 契约） |
| 数值 | 年化分母/掩码不一致（E6d 教训）；宽表 index 丢行（E6c 教训）；`%` 串（E5a） | 同表同掩码；统一主索引；哑元全流程 |
| 运行 | 长跑中断、shard 重启改随机性 | 无状态 hash 键 + AR 全路径重建 + 前缀测试；DONE 绑定 hash；续跑不累加 |
| 运行 | 磁盘与 RSS | 随机稠密权重不落盘；逐 seed 日账本 float64 分块；写前估容量；并发 ≤32 起 |
| 运行 | 两个 final 混用 | 本 brief 唯一有效；web plan 与 proposal 的 SHA 进 manifest |
| 解读 | 强于裸 A4b 误称改善生产；随机差为正误称纯 alpha；反向也好误称浓度 | 固定 R1/R2；`increment_vs_random` 命名；反向同 m + 形状 + 成本并排 |
| 解读 | 未测格被判死 | `limit_register` 登记 `not_tested`；本轮不是策略空间终点 |
| 节奏 | 有没有把跑得快当约束 | 初稿有两处（按核族分层路径数、等仓位只做 P54 系），用户 09-06 指出过严后撤回；现全部规则 128 路径 × 3 profile、软全 λ × 2 profile、等仓位全覆盖、B=2000；时间只靠向量化、分片与两次交付管理 |

方向确认：单主题（否决层真实价值与架构地图）；不加因子、不改池、不改持有期、不改成本、不改生产；探索从宽、无闸门、事前登记；两份 REPORT 交用户与规划 session；OOS 仍 HOLD。
