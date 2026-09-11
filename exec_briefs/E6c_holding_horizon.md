# E6c —— 最终 brief（v2，2026-09-04）：持有期 1～20 日 × 16 个既有配置 + 事件时间剖面 + 日龄桥 + 统计诊断

> **版本与来源**：本 brief 由规划 session 审 Claude web 的 plan 后写成，是 E6c 唯一有效执行文件。web plan = `exec_briefs/plans/E6c_plan_web_final_20260904.md`（v1.1，SHA256 `f5f401763b4fe89406af5e249ce09891bc09eebefb3bb9c9efca3c115eb0c32e`）；原 proposal 已移至 `plans/E6c_proposal_v1_superseded_20260904.md`，**不再有效**。执行端以本 brief 为准；本 brief 未写到的细节按 web plan 对应小节执行；两者冲突以本 brief 为准。先读 `00_协议.md`；末尾有自审记录。

## 0. 一句话问题与设计结论

**在既定 I11 池、既定选股规则、DEV 目标权重与 T+1 VWAP 执行下，资金在一批候选股票上停留几天，才能更好地平衡收益释放、信号老化、资金占用与交易成本？** 事件时间剖面、否决增量随期限变化、触发日龄、成本分解，都是这一问题的解释层。

核心读法：不是找累计收益最大的终点。持有期拉长时，早期日龄的资本权重被稀释、晚期日龄贡献加入、成本减少，三项之和才是 Δnet。本轮把这三项在同一日账本上精确拆开（§2F），并给对照与不确定性。**本轮只出表，不定持有期、不定稿 v3、不淘汰任何配置。**

### 0.1 相对 web plan 的采纳与调整（规划 session 决定）

| web plan 内容 | 处置 |
|---|---|
| 16 个 canonical 配置、H = 1…20 全整数轴、主文展示 {3,5,10,15,20} | **采纳** |
| 配置去重（`A4b\|CVR_20d:k5` ≡ `A4b_CVRv5`）、补 `M_mean2` 与两底座的 C/B 单否决父 | **采纳** |
| 生产构造：`M_mean2`、`M_mean3_v2` 用二分组剔高半；keep30/20 用十分位 | **采纳**；另报二分组与十分位留 50% 的成员差异（E6b 实测四段逐位相同，本步只记录） |
| 日账本、全部 full 指标从逐日数据重算、不平均 t、12bp 从日序列重算 | **采纳**（修正原 proposal 的错误） |
| `legacy_all` 与 `common_mature` 两套评价范围，B = 60 | **采纳**；B=60 已按源码核实（最长回看 = turnover_volatility_60d 的 60 日；信号 CMF 20 日；观察窗 5 日；次新 20 日） |
| 相对自身 H5 与相对固定生产参照 `A4b_CVRv5@h5` 的配对 Δ；相邻期限差；成本临界点 c* | **采纳** |
| 否决 × 持有期：固定父子边，不选"最佳单父" | **采纳** |
| 事件剖面：固定形成日成员、固定 cohort 日历、E/M/A 三视图、父子/剔除配对剖面、混合恒等式校验 | **采纳**；视图 M 按 §2E 的简化定义实现（前向携带的复权 VWAP 标记 + 入场掩码 + 固定股数终点） |
| 日龄桥 K_{t,j} 与三项分解；估值 delta | **采纳**；K 的定义已按引擎源码核实（§1.3） |
| 触发日龄与新事件起点 | **采纳**；**日龄取值为 1…5**（观察池由 signal.shift(1..5) 构成，形成日 T 的池不含 T 当日触发），web 写的 0…4 不对 |
| HAC：主列 L=H / max(H,5)；敏感性 L=5/20/40；带缺口序列的 score-HAC；full 的 fixedmix 与 legacy 拼接两列 | **采纳** |
| 共同时间块 bootstrap：2000 次、L=60（敏感性 20）、按段 stationary、配置/H/父子共用 draw、逐点区间 + 两族联合带、固定 seed | **采纳**（只在聚合向量上抽，不重跑选股） |
| 逐年 Δ 与留一年 | **采纳** |
| 可成交性暴露审计 | **采纳但缩范围**：只用语义已核的字段——`is_open`、涨跌停价、`flag_buy/flag_sell`（缓存里取值 1/0/NaN；2024 样本 flag_buy=0 约 3%、flag_sell=0 约 0.5%；按 1=可、0=不可解读，报告标"疑似不可成交"）；只做暴露计数，不改收益 |
| 价格漂移费用代理 | **采纳为诊断**（无费用近似下的漂移再平衡需求），不进正式成本 |
| 每分区 hash 键缓存、`.partial` 标记、原子落盘 | **简化**：按段落盘 + `_DONE_<seg>` 标记 + `run_manifest.json` 记录代码/plan/输入 hash；某段失败整段重跑，不做配置级缓存 |
| 图表 | **可选**；文本表必需 |
| "一口气完成不设中途批准" | **采纳，改为四阶段自动推进**（§4）：阶段间不等用户，但阶段 2 的锚点 FAIL 会停 |

## 1. 起点确认与引擎 contract

### 1.1 起点
1. 47 `git log -1 --oneline` = `93b0d4e`（HEAD 若前进，核 `93b0d4e` 为祖先且 `comprehensive_factor_diagnosis.py`、四地基、`e6_wide_scan.py`、`e6b_stack_sleeves.py`、`export_delivery_pools_v2.py` 的 blob 未变；纯文档提交不是 BLOCKER）；`git status -sb` 首行 `## main...origin/main`；untracked 仍只有那 3 个历史脚本。
2. 引擎默认值 `(5, 8, 1, True)`；`C.COST_BP_BILATERAL == 8.0`。
3. 输入存在：`results/20260904_1051_E6_wide_scan/{scan_all.csv,daily_all.parquet}`、`results/20260904_1202_E6b_stack_sleeves/{scan_all.csv,daily_all.parquet}`、`results/20260903_0935_E2_decomposition/decomp.csv`；四个分段缓存。
4. 记录 Python / numpy / pandas 版本、`PERIODS`、上述文件与五个 py 文件的 SHA256 到 `run_manifest.json`。
5. `ps` 无本项目残留；按实际 RSS 与负载决定并发（默认 4 段并行），不因资源少跑网格。

### 1.2 数据边界
四段独立加载（`load_all_daily_data(ps, pe)`），收益信息不超过 2026-03-27；不重建延长缓存、不读 E7 相关目录。段内 cohort 不跨段末补齐。

### 1.3 引擎 contract（规划 session 已核的事实；执行端开工前整段读函数体复核，写进 `engine_contract.md`）
- `compute_calendar_pnl(W, data, base_pool, hold_days, cost_bp_bilateral, exec_lag=1, adjust=True)`：
  - `actual = W.reindex(...).fillna(0).rolling(hold_days, min_periods=1).mean()`；`ah = actual.shift(exec_lag+1)`。→ 稳态（t ≥ hold_days+1）`ah_t = (1/H) Σ_{j=1..H} W_{t−j−1}`；**段首前 H 天分母是可用行数（<H），不是 H**。
  - `daily_ret = vwap_daily_return(data, adjust)` = 后复权 `vwap_t/vwap_{t−1} − 1`，停牌日与复牌日为 NaN。
  - `port_t = (ah × daily_ret).sum(axis=1)`：**NaN 收益按 0 贡献**（pandas sum 跳过 NaN）；`position_t = ah.sum(axis=1)`：**权重照算**，含无收益的票。
  - `bench_t = daily_ret.where(base_pool==1).mean(axis=1)`（clean 等权，同一 H 下不随配置变；跨 H 也相同）。
  - `gross_t = port_t − bench_t × position_t`；`turnover_t = 0.5 Σ_i |ah_{t,i} − ah_{t−1,i}|`（首日 fillna 0）；`cost_t = turnover_t × bp/1e4`；`net_t = gross_t − cost_t`。成本记在收益归属日 t（= 执行日 t 当天的 vwap 成交），执行日与形成日的映射：形成日 T → 执行日 T+1 → 首个收益结束日 T+2。
  - `turnover_annual = Σ turnover_t / (len/252)`，分母为段内全部日期。
  - 返回键：`gross_excess_daily / net_excess_daily / daily_position / daily_turnover / port_daily / bench_daily / turnover_annual / exec_lag / adjust`。
- 由上可证：稳态下 `gross_{H,t} = (1/H) Σ_{j=1..H} K_{t,j}`，`K_{t,j} = Σ_i W_{t−j−1,i} · r̃_{i,t} − bench_t · Σ_i W_{t−j−1,i}`，其中 `r̃` = 收益 NaN 置 0（与引擎同构）。`ah_t − ah_{t−1} = (W_{t−2} − W_{t−H−2})/H`。
- `build_factor_strategy_holdings_cached(neu, pool, k, drop)`：当日有效中性化值 <3k 只则该日无持仓；qcut 按 rank(method='first') 分组，组 1 最低；奇数日中位那一只落组 1。
- `combine(caches, 'mean')`：只对各因子缓存都有的日期取交集；成员缺任一因子值则该票不进均值（dropna 在 `precompute_neutralized_factor` 内）。
- 观察池：`build_observation_pool(signal, obs_window=5)` = `Σ_{lag=1..5} signal.shift(lag) > 0`，**形成日 T 的池只含 T−1…T−5 触发过的票**；触发日龄 age ∈ {1,…,5}。
- 硬约束：`is_open==1`、非涨跌停（用 limit 价）、上市 ≥20 日、20 日均成交额 ≥2000 万、`min_mcap=0`。
- 若复核发现与上述不符，先写进 contract 并定位到新增 helper；确属引擎问题则停受影响输出并报告，不改引擎。

## 2. 做什么

### 2A. 冻结配置（每段每配置只生成一次 mask 与 W，所有 H 共用）

| # | canonical | 构造 | 角色 |
|---|---|---|---|
| 1 | `A4b` | cond 二分组剔高半 → 保留集内重中性化 tvol → 二分组剔高半 | 生产底座 |
| 2 | `M_mean3_v2` | cond/tvol/cr20 pct 均值，二分组剔高半 | 生产 |
| 3 | `M_union3_v2` | 三因子各二分组剔高半，并集之外 | 生产 |
| 4 | `A4b_CVRv5` | #1 ∧ ¬(CVR_20d 池内最高 1/5) | 生产；别名 `A4b\|CVR_20d:k5` |
| 5 | `M_mean3_v2_CVRv5` | #2 ∧ ¬tox_CVR5 | 生产 |
| 6 | `M_union3_v2_CVRv5` | #3 ∧ ¬tox_CVR5 | 生产 |
| 7 | `M_mean2` | cond/tvol pct 均值，二分组剔高半 | 宽底座对照 |
| 8 | `M_mean2@keep30` | 同 #7 均值，十分位保留最低 3 档 | E6b 底座 |
| 9 | `M_mean2@keep20` | 十分位保留最低 2 档 | E6b 底座 |
| 10 | `A4b\|CVR_20d:k10` | #1 ∧ ¬(CVR 最高 1/10) | C 单父 |
| 11 | `A4b\|cum_return_5d:k10` | #1 ∧ ¬(cr5 最高 1/10) | B 单父 |
| 12 | `A4b\|CVR_20d:k10+cum_return_5d:k10` | #1 ∧ ¬tox_CVR10 ∧ ¬tox_cr5_10 | 双否决 |
| 13 | `M_mean2@keep30\|CVR_20d:k10` | #8 ∧ ¬tox_CVR10 | C 单父 |
| 14 | `M_mean2@keep30\|cum_return_5d:k10` | #8 ∧ ¬tox_cr5_10 | B 单父 |
| 15 | `M_mean2@keep30\|CVR_20d:k10+cum_return_5d:k10` | 双否决 | E6b 全表最高（样本内） |
| 16 | `A4b\|intraday_cvr_1d:k10` | #1 ∧ ¬(cvr_1d 最高 1/10) | 探索性（H1） |
| 基准 | `pool0_DEV` | pool0 全体按同一 DEV 权重 | 副基准，每个 H 各跑一次 |

所有否决的分位域是当日 pool0；方向、k、符号不变；DEV helper 与 E6b 逐字相同（从 `_remote_tmp/e6b_stack_sleeves.py` 复制 helper 与 pipeline 段）。保存每个 mask/W 的 SHA256；统计各配置每日 `n_target = (W>0).sum(axis=1)`。

**hold=5 锚点（`legacy_all` 范围）**：#1–7 对 E6 `scan_all.csv` 的 `net_<yr>`（8bp），#8–16 对 E6b `scan_all.csv`；共 64 格，`TOL=0.02`；另对 E6b `daily_all.parquet` 中同名配置的 h5 日净序列逐日比（max|diff|，NaN 位置一致）。任一格 FAIL → 阶段 2 停、写 BLOCKERS。`pool0_DEV@h5` 对 E2 `decomp.csv` 的 `pool0_DEV` L1A（6bp）按 `−turn×2/100` 换算作软对照，只报告。

### 2B. Calendar 持有期曲线

- 对每配置与 `pool0_DEV`，H = 1…20 各调一次引擎（显式传 `hold_days=H, cost_bp_bilateral=8.0, exec_lag=1, adjust=True`）。
- **日账本**（每配置 × H × 日）：`period, date, cfg, hold, port, bench, position, turnover, cost8, gross, net8, net12 (= net8 − turnover×4/1e4), n_target, n_actual (= (ah>0).sum), hhi_actual (= Σ(ah_i/position)^2), effective_n (= 1/hhi), pu_gross (= gross/position, position>1e-12), pu_net (= net8/position)`。`ah` 从 W 用与引擎相同的 rolling/shift 重构并与引擎 `daily_position` 逐日核对（atol 1e-12）。
- **两套评价范围**：`legacy_all` = 段内全部日期（锚点用）；`common_mature` = 段内索引 `t ≥ B + HMAX + 1 = 81` 的日期，所有配置与 H 共用（主比较用）。两套都输出。无持仓日（position=0）保留在均值里；p=0 但有退出成本的日子单列 `zero_position_cost`。
- **指标**（每范围 × 四段 × full；full 从四段日序列拼接后重算）：`ann = 252×100×mean`；gross / net8 / net12 / cost；`turn_eval = 252×mean(turnover)`（`turn_legacy` 另存）；NW t（L = H）；`nw5`（L=5）；`capital_day_net = 25200×Σnet8/Σposition`；仓位均值（全日历 / 活跃日）、仓位分位数、零仓位天数；`n_target`、`n_actual`、`effective_n` 均值；日收益波动；excess MDD；组合自身 `port − cost8` 的路径 MDD 另报（不叫资金净值回撤）。
- **副基准**：`b_pool,H,t = port_pool,H,t / position_pool,H,t`（p_pool>0）；`g2 = port_cfg − position_cfg × b_pool`；`n2 = g2 − cost8_cfg`；配对有效日期掩码与天数同存；另给固定 `pool0_DEV@h5` 参照列。

### 2C. 配对、成本与资金占用
- `Δnet(H,5) = net8_H − net8_5`（同日）；同报 Δgross、Δcost、Δturn、Δposition、Δn_actual；恒等式 `Δnet = Δgross + (cost_5 − cost_H)` 逐日核。四段、full、逐年。H5 自比记 Δ=0、t=NA。
- `Δservice = net_cfg,H − net_{A4b_CVRv5,5}`（固定生产参照，8bp 与 12bp 各一套）。
- 相邻期限差 `net_H − net_{H−1}`。
- 换手诊断：`turn_H/turn_5`、`H×turn_H`、目标权重跨 H 日重合 `Σ min(W_t, W_{t−H})/Σ W_t`。
- 漂移代理（诊断）：`q_pre,u = q_{u−1}(1+r_u)/(1+Σ q_{u−1} r_u)`，`tau_drift_proxy,u = 0.5 Σ|q_u − q_pre,u|`，与 `0.5Σ|q_u − q_{u−1}|` 并列；r 用后复权 vwap 日收益，NaN 处 q_pre 取 q_{u−1}（不重归一），报覆盖率；不进 net。
- 成本临界点：`c*_bp = 1e4×(G_H − G_5)/(U_H − U_5)`（G 为小数年化 gross，U 为年化换手），|U_H − U_5| < 0.5 时记"无清晰交叉点"。

### 2D. 否决 × 持有期（固定父子边）
边：`A4b→A4b_CVRv5`、`M_mean3_v2→M_mean3_v2_CVRv5`、`M_union3_v2→M_union3_v2_CVRv5`、`A4b→#16`；对 A4b 与 keep30 各自：`Base→C10`、`Base→B10`、`Base→C10+B10`、`C10→C10+B10`、`B10→C10+B10`。每 H：`D_H = net_child,H − net_parent,H`，`I_H = D_H − D_5`；gross 与成本分别分解；NW t（L=H）。

### 2E. 事件时间剖面（冻结形成日成员与 cohort 日历）
- 收益：`r_{i,T}(j) = adj_vwap_{i,T+1+j}/adj_vwap_{i,T+j} − 1`，j=1…20（j=1 即 T+1→T+2 VWAP）。
- cohort 日历：形成日 `T ≥ B=60` 且 `T+21 ≤ 段末索引`；所有集合、所有 j 共用；集合当日为空 → 结构性 NA。
- 集合注册表 `set_registry.csv`（`set_id, formation_mask 来源, reference_mask, parent, child, reason`）：16 个配置（参照 = 同日 pool0）；`pool0`（参照 = 同日 clean）；§2D 每条边的 `removed = parent ∧ ¬child`（参照 pool0）；`pool0 ∧ tox_CVR5`、`pool0 ∧ tox_cr5_10`（参照 pool0）。逐日逐股核 `parent = child ∪ removed`、`child ∩ removed = ∅`。
- **三视图**：
  - **E（引擎同构，主）**：形成日等权 `a = 1/n_T`，`Σ_i a_i r̃_{i,T}(j)`（NaN 收益记 0，分母不变）；参照同法。
  - **M（估值敏感性）**：`mark_{i,t}` = 后复权 vwap 前向携带（停牌期间保持上次标记，复牌日补上跨停牌价格变化）；`r_mark` = mark 的日变化；入场掩码 `e_{T,i} = 1{T+1 日 is_open==1 且 vwap 有效}`；线性日剖面 `Σ_i a_i e_i r_mark,i,T(j)`（e=0 的名额全程现金、分母不变）；固定股数终点 `Σ_i a_i e_i (mark_{T+1+H}/mark_{T+1} − 1)`，H ∈ {3,5,10,15,20}；另报陈旧标记权重（最后有效价距当日 >20 日）与无法入场权重。
  - **A（available-case，兼容附表）**：原 `nanmean` 口径 + 逐 j 有效数；累计只在全部 j 都可定义的形成日上算（`A_complete_observable_cohort`），不 skipna 求和。
- 统计对象：先在每个形成日内聚合，再对形成日求均值（另给按 n_T 加权的描述列）；配对剖面（child−parent、removed−parent、child−removed）先逐形成日求差再汇总；混合恒等式 `r_parent = (1−q_T) r_child + q_T r_removed`（固定等权、E 视图）逐 T 核。
- 输出：日剖面 j=1…20、`CAR(H)` H=1…20、区间贡献 `[1,3]/[4,5]/[6,10]/[11,15]/[16,20]`、`CAR(H)/H`；不按 `CAR3/CAR20` 排序（比例可展示但带分子分母与不稳定标志）。

### 2F. 日龄桥（关键桥梁）
- 对每配置、每 H、common_mature 日期：`K_{t,j}` 如 §1.3；核 `gross_{H,t} == (1/H)Σ_{j≤H} K_{t,j}`（atol 1e-10）。
- 分解 `Δgross(H,5) = (1/H − 1/5)Σ_{j≤5}K_{t,j} + (1/H)Σ_{6≤j≤H}K_{t,j}`（H<5 同理拆保留早期与去掉晚期）；三项：早期稀释、晚期贡献、成本节省 `cost_5 − cost_H`，之和 = Δnet（逐日核）。四段与 full 汇总。
- 估值 delta：`valuation_delta_{H,t} = Σ_i ah_{H,t,i}(r_mark − r̃)_{i,t}`，报 H−H5 差与缺失权重；不替换 net。

### 2G. 触发日龄与新事件
- 每票每日 `age ∈ {1..5}` = 距最近一次 `signal==1` 的天数（只用 ≤T 信息）。对重点集合（16 配置 + removed）按 age 分组给 E 视图区间贡献与数量/权重；参照同日龄 pool0 与全部 pool0 两列。
- 新事件起点：`signal_T=1` 且 T−1…T−5 无触发的票，形成 T+1 日进入池的"首次事件"子集（只报剖面，不成配置）。
- 同票在 `ah` 中连续非零持有的存续长度分布（段首末删失标注）与多批次重选比例。

### 2H. 不确定性（只作列）
- **HAC**：主列 L=H（配对 max(H,5)；父子 H）；敏感性 L=5/20/40；剖面序列在形成日日历上 L=20（另 40）。带内部缺口的序列用 score-HAC：`m_t` 有效指示，`mu=Σm x/Σm`，`u_t = m_t(x_t−mu)`（缺失处显式 0），`Var = [Σu² + 2Σ_{l≤L}(1−l/(L+1))Σu_t u_{t−l}]/(Σm)²`；零方差记 SE=0、t=NA。
- **full 两列**：`nw_full_concat`（拼接后直接 NW，与 E6/E6b 同）与 `nw_full_fixedmix`（每段 `z_t = m_t(x_t − mu_full)`，缺失 0，`e_t = z_t − mean_seg(z)`，各段 Bartlett 二次型之和 / n_obs²；滞后乘积不跨段）。
- **bootstrap**：stationary bootstrap，期望块长 L=60（敏感性 20），每段独立、保持段长；2000 次；一个 draw 内所有配置/H/父子/基准共用日期索引；cohort 按形成日整行抽 20 日向量；每 replicate 重算分子/有效分母（资本日比率 = Σnet/Σposition）；full 由四段合计分子/分母；配对差先构差序列再抽。seed 根 `20260904`，子 seed = SHA256("20260904/" + 命名空间) 取前 8 字节（不用 Python `hash()`）。输出：逐点 95% percentile 区间、`B_valid`；每条"Δ vs H5 全期限曲线"与重点剖面的同时带 `theta ± q95·s`（`q95 = quantile_0.95(max_h |θ*_b,h − θ̂_h|/s_h)`）；两族联合带：① 所有 cfg×H≠5 的自身 H5 差，② 所有 cfg×H 的固定生产参照差，8/12bp 各一，family 点集事前冻结、只计全可估 draw。
- **逐年与留一年**：由冻结日序列重算逐年 Δ（2026 标不完整年）；去掉任一年后的 H5 配对差摘要。

### 2I. 可成交性暴露（只计数）
执行日 u = 形成日+1。买入需求 `max(ah_u − ah_{u−1}, 0)` 权重中落在 `is_open_u==0` 或 `close_u ≥ limit_up_u` 或 `flag_buy_u==0` 的份额；卖出需求同理用 `limit_down` / `flag_sell==0`。按 H 报份额、天数占比与对应日收益贡献；字段覆盖率（NaN 占比）并列。标"疑似不可成交"，不改收益。

## 3. 自测与验收

### 3.1 玩具测试（正式跑前，`e6c_selftests.py`，合成面板，全部必须 PASS）
1. 单次信号脉冲、收益只在 T+1→T+2：首个收益落 T+2；H∈{1,3,5,20} 的 ah 与机械枚举一致。
2. 收益只在第 10 日：H<10 不得获得；H≥10 获得 1/H。
3. 同票连续多日信号：批次叠加，不重置旧批次；换手按 `(W_{t−2} − W_{t−H−2})/H` 核。
4. 恒定目标与交替目标：换手不强制 1/H；漂移代理在常数目标、两票相反收益下非零。
5. 奇/偶截面、并列值、<3k 只、缺失因子：二分组与十分位留 50% 的差异可见并被记录。
6. 两段不等长：full 指标从日序列重算；"平均 t / 混用平均 turn"的旧算法被测试标为错误。
7. 8→12bp：日差恒等 `turnover×4/1e4`。
8. 空池 / 零仓位 / 只有退出成本：主 net 保留成本；pu 不除零。
9. 停牌→复牌→永久无价：E 记 0 贡献分母不变；M 复牌日补跨停牌变化、终值未知单列；A 有效数变化。
10. 最后一笔 cohort：T+21 越界不进入。
11. 父子分割与固定权重混合恒等式。
12. 带缺口 score-HAC：无缺失时等于 `nw_stats`；有缺口时 NaN 不进 score 乘积。
13. bootstrap：同 seed 复现；共用 draw；带缺口每 draw 重算分母；联合族只接受全可估 draw。
14. 四段各为常数：fixedmix 方差数值零、concat 版非零。
15. 前视：合成"改未来值、过去输出不变"。
16. merge 与格式串：manifest 哑元全流程；`%` 字面量全扫。

### 3.2 实数验收（齐不齐与会计恒等，无效果门槛）
- 64 个 h5 锚点全 OK（TOL 0.02）+ E6b 日序列逐日 max|diff| < 1e-9；`pool0_DEV@h5` 软对照报出。
- 完整性：16 配置 × 20 H × 4 段 + pool0_DEV × 20 × 4 全有状态；剖面集合 × 20 j × 4 段全有状态或结构性 NA 带原因。
- 会计：逐日 `gross = port − bench×position`、`net = gross − cost`、`net12 = net8 − turn×4/1e4`、`ann_g − ann_n = ann_cost`；桥 `gross_H = (1/H)ΣK`、三项分解之和 = Δnet（atol 1e-10）。
- 日期：所有输出日期 ≤ 段末；common_mature 起点 = 81；cohort 日历各 j 相同。
- 只读：五个 py、四地基、上游结果 hash 前后相同。
- 二分组 vs 十分位留 50% 的成员差异格数（`M_mean2`、`M_mean3_v2`）报出。

## 4. 执行组织（四阶段自动推进，阶段间不等用户）
1. **阶段 1**：读函数体写 `engine_contract.md`（对照 §1.3 逐条确认/更正）；`run_manifest.json`；`e6c_selftests.py` 16 项 PASS。
2. **阶段 2**：只跑 2024-2026 段全流程（W → 20 H 账本 → 剖面 E/M/A → 桥 → 日龄 → 暴露审计），核该段 16 个 h5 锚点与日序列；**FAIL → 停，写 BLOCKERS**；PASS 自动进阶段 3。同时记录该段耗时并在日志首行给出全任务预计时长（>30 分钟只是告知）。
3. **阶段 3**：其余三段并行（`taskset -c 96-191,288-383`，BLAS 线程 16/进程）；每段落 `sf_<seg>.csv / daily_<seg>.parquet / profile_<seg>.csv / cohort_<seg>.parquet / bridge_<seg>.csv / exposure_<seg>.csv / _DONE_<seg>`。某段失败整段重跑，不覆盖旧 results 目录里其他段。
4. **阶段 4**：merge（四段齐后）：full 指标、配对表、fixedmix、bootstrap、逐年/留一年、summary、REPORT。

产物（`results/<ts>_E6c_holding_horizon/`）：`run_manifest.json`、`engine_contract.md`、`config_registry.csv`、`aliases.csv`、`set_registry.csv`、`check.csv`、`selftest_results.json`、`daily_all.parquet`（日账本）、`sf_all.csv`、`full_summary.csv`、`horizon_deltas.csv`、`service_deltas.csv`、`veto_horizon_deltas.csv`、`cost_frontier.csv`、`capital_age_decomposition.csv`、`cohort_daily.parquet`、`profile_all.csv`、`event_age_profiles.csv`、`event_coverage.csv`、`bootstrap_summary.csv`、`bootstrap_manifest.json`、`yearly_deltas.csv`、`leave_one_year.csv`、`execution_exposure_audit.csv`、`valuation_horizon_sensitivity.csv`、`drift_cost_audit.csv`、`limit_register.md`、`summary.txt`、各段日志。图可选。

`summary.txt` 主表顺序：(A) 16 配置主读五档 net8/net12/gross/cost/turn/pos/n_actual/NW(L=H)（common_mature 与 legacy_all 各一）；(B) Δ vs 自身 H5 与 Δservice（四段/full/2024-26，含 bootstrap 区间）；(C) 三项分解；(D) 否决 × H 的 D_H / I_H；(E) 剖面（E 视图为主，M/A 差异列）；(F) 日龄与新事件；(G) 暴露审计与估值 delta；(H) 逐年/留一年；(I) 范围边界与 `RIGHT_BOUNDARY_OPEN` 标记（20 日仍未见平台时）。

## 5. 交回
- 47：`git add e6c_holding_horizon.py e6c_selftests.py [e6c_statistics.py]`（只加新增脚本）→ commit `E6c 持有期 1-20 日 × 16 配置 + 事件剖面 E/M/A + 日龄桥 + HAC/bootstrap 诊断 (results/<ts>_E6c_holding_horizon)` → `git push origin main`；`scp` 回本地 `_remote_tmp/`。
- `exec_briefs/E6c_REPORT.md`（协议结构）：起点与 contract 复核结论（与 §1.3 不符处单列）；16 项玩具测试；64 锚点 + 日序列对账；完整性/会计/日期/只读验收；每段耗时与总耗时；`summary.txt` (A)(B)(C)(D) 原样、(E)–(I) 摘要 + 指向文件；纯文本摘要 ≤15 行（只答 web plan §4.4 的五个问题的"数字与方向"，**不写"该用几日 / v3 定稿 / 饱和"**）；BLOCKERS。
- WORKLOG 一条（远端 + 本地镜像同文）。

## 6. 禁区
不改四地基、引擎、I11/obs_window/DEV/中性化；不新增行业中性化；不重扫 34 因子；不做深度×否决优化、软否决、placebo（留 E6e）；不看 E7、不重建延长缓存；不改生产持有期或交付池；不删 results；不用 `git add .`；REPORT 不下持有期结论；结果数字不外发；文档与日志不出现登录信息与主机地址。凡遇"必须改上述任何一项才能继续" → 停，写 BLOCKERS。

## 7. 自审记录（规划 session 2026-09-04；执行端见此段方可开工）
| 类 | 不利因素 | 处置 |
|---|---|---|
| 版本 | 三份 E6c 文件并存会让执行端混用 | 原 proposal 移入 `plans/…_superseded`；本 brief 唯一有效；记录 web plan SHA256 |
| 事实 | web plan 写触发日龄 0…4 | 源码核实观察池 = `signal.shift(1..5)`，日龄 1…5，已改 |
| 事实 | web plan 要求现场核 B、rolling 分母、NaN 收益处理、成本记账日 | 规划 session 已按源码核出并写进 §1.3；执行端复核即可，减少猜测 |
| 事实 | flag_buy/flag_sell 语义未知 | 缓存取值 1/0/NaN，2024 样本 0 占比 3%/0.5%，按 1=可 解读并标"疑似"；只计数 |
| 代码 | 原 proposal 12 名有 1 对重复；full 指标平均 t、混用平均 turn | 采纳 web 修正：去重、全部 full 从日序列重算 |
| 代码 | `M_mean2/M_mean3_v2` 构造在 E6b 用了十分位 | 回到生产二分组；差异格数报出（E6b 实测四段逐位相同） |
| 代码 | 引擎段首 rolling 分母 <H，桥恒等式在段首不成立 | 桥只在 common_mature（t ≥ 81）核；legacy_all 只用于锚 |
| 代码 | NaN 收益的票权重计入 position 但收益记 0；K 若用原始 NaN 会与引擎不等 | K 用 r̃（NaN→0），与引擎同构；M 视图另算 |
| 代码 | 大张量：16 配置 × 20 H × T × N | 只存日标量账本；K 逐 j 流式；bootstrap 只抽聚合向量 |
| 代码 | `%` 格式串、merge 末尾崩 | 玩具测试 16 含 manifest 哑元全流程与 `%` 全扫 |
| 统计 | 320 个配置×期限仍是样本内、彼此不独立 | 逐点区间 + 两族联合带 + 逐年/留一年；无盈利门槛；REPORT 标 `RIGHT_BOUNDARY_OPEN` |
| 统计 | 5 日重叠使 lag=H 未必充分；缺口序列 dropna 改变 lag 单位 | L 敏感性 5/20/40；score-HAC 显式 0 占位 |
| 统计 | full 拼接 NW 与固定四段 bootstrap 推断对象不一致 | 双列：`nw_full_concat`（与历史一致）与 `nw_full_fixedmix` |
| 会计 | 12bp 只改均值 | 日序列 `net12` 重算全部指标 |
| 会计 | pu 删掉零仓位日的退出成本 | 主 net 保留；`zero_position_cost` 与 `capital_day_net` 单列 |
| 解读 | 长端 CAR 仍正就"该长持" | `CAR/H`、三项分解、成本临界点、固定生产参照并排 |
| 解读 | removed 对 pool0 弱 ≠ 对父有价值 | 固定父子边的真实 Calendar D_H 与配对剖面 |
| 运行 | 复杂度高，一次跑到底若中途错要重来 | 四阶段：contract → 玩具 → 单段端到端并核锚 → 三段并行 → merge；段级落盘与 `_DONE` |
| 运行 | 耗时未知 | 阶段 2 测时后给预计（告知非批准）；算力与时长不是约束 |
| 交接 | 复杂产物执行端易在 REPORT 里下结论 | 摘要限定为 web §4.4 五问的"数字与方向"，禁写采纳/淘汰 |

方向确认：单主题（持有期）不变；只增加对照、时间轴完整性与会计/统计诊断，不增加因子、不优化否决与深度；探索从宽、无盈利闸门；OOS 仍 HOLD；结论交规划 session 与用户。
