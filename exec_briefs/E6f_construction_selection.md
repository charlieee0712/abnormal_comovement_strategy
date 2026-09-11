# E6f —— 最终 brief（v1，2026-09-09）：v3 候选的构造改进、选择程序回放与实施后表现

> **版本与来源**：规划 session 审 Claude web 的 plan 后写成，是 E6f 唯一有效执行文件。web plan = `exec_briefs/plans/E6f_plan_web_final.md`（v1.0，SHA256 `ddf3a7d94ff9a19dcb5f61101a6b5e9c3ec171551763920c44941ec96e9289e3`）；proposal = `exec_briefs/E6f_proposal.md`（其顶部有 2026-09-09 勘误）。执行端以本 brief 为准；本 brief 未写到的实现细节按 web plan 对应小节执行（web §1.3 支持集、§2A.2 因子定义、§2A.7 中性化、§2B.4–2B.6 选择账户与读法、§2C.2–2C.4 成本与影子账户、§2D 统计、§3.2 测试清单）；冲突以本 brief 为准。先读 `00_协议.md`（第 3 条 2026-09-09 已改）；末尾有自审记录。E7 仍 HOLD。

## 0. 一句话问题与设计结论

**E6e 提出的完整候选（以 `KTC_mean` 叠 `cvr_1d`/`cr5` 否决为代表），在合理改变构造参数、用历史当时可见的信息选择配置、并计入实施限制之后，哪些仍有改善 R1/R2 的空间；改善来自什么，脆弱处能否在既有构造范围内修复？** 本轮出三张并排的地图：构造参数邻域（含新候选）、按当时信息选择的政策账户、成本与成交后的表现。**只出地图与账，不定 v3、不开 E7、不改生产。**

### 0.1 相对 web plan 的采纳与调整（规划 session 决定）

| web plan 内容 | 处置 |
|---|---|
| 三项方向改变：参数研究允许产生新候选并进入选择回放（UA → EXPANDED）；静态分割表现与真实政策账户分开；成本与成交同时作用于候选和参照 | **采纳** |
| §0.3 对 proposal 的 12 条修订 | **全部采纳**。其中属于规划 session 自身错误、已核实的：2022 年底分割后到 2026-03-27 约 39 个月而非 15；"核越浅否决增量越小"表述方向混乱，改为"保留比例更大的底座上否决增量更大"；**E6 只扫了其他因子的否决角色，没有扫第四合成因子**（E6_REPORT 只有 B/C/D 三段，规划 session 09-09 核）；新窗 `min_periods = ceil(w/2)` 而非 `w//2`；`cvr_1d` 与 `CVR` 数学恒等但浮点不必逐位相同；proposal 的决策地图与阈值不进 brief，判读由规划 session 与用户做 |
| 修 E6e 汇总不原地覆盖，输出到 `revisions/E6e_summary_fix/`；找不到原 `engine_contract/PLAN_COPY` 则标 `RECONSTRUCTED_AT_E6f` | **采纳** |
| 三种支持集 `legacy_all / paired_common_domain / history_warmed` | **采纳，且 `history_warmed` 是必要的**：规划 session 09-09 核 `e6e_core.load_segment`，四段按 `PERIODS` 起止直接加载、**不带预热**，每段头 19 天 `clean` 全零（`load_segment` 的 20 日 `mature` 成熟度过滤，账本 76 个基准 NaN 日 = 4×19）、头约 29 天无 tvol（min_periods 30）；120 日窗在 `legacy_all` 下每段再损失约 30 天。`history_warmed` 只预热因子，pool0/clean/基准沿冻结版，**故每段头 19 天仍空**，比较用同一支持集；2010 段若源数据有更早日期则用，没有则如实保留 |
| 候选域三层 U0-primary / U0-broad / UA；A12 展示锚；P54 按 E6e 定义恢复 | **采纳**（U0-primary 3,770、U0-broad 6,038 须按 E6e 注册表实查） |
| 块 A：OAT + T×C、慢C×快C、快C×B 二元 + KTC 五维联合模板 1,296 + 权重 37 点 × 6 深 × 4 否决 = 888 + k 平台 54×25 = 1,350 + 深度 15/60 + A12 的 H∈{1,2,3,4,5,7,10} + 中性化 N0/NS/NI/NSI + K 的 MA/ROS 与 ε 格 + B 复权分支 | **采纳**；否决类变体全部配 `coretrim_matchN` 与等仓位配对；所有重要比较另配 `paired_common_domain` |
| 块 B：只读账本的时间面板；六分割双向；`ledger_portability` 与 `policy_account` 分开；四个候选域；S1–S6 + S_meta；单次选择账户与年度 walk-forward 账户（vintage 由引擎 rolling 自然承接）；a/b/b−a/SE 读法、oracle 与 hindsight-rule 对照、三层推断；否决选择回放；cond 时间异质的匹配比较；成分归因；市场状态描述；单调性 | **采纳**。选择稳定性重采样 B=2000；S_meta 的稳定性同 B，若实测超过 24 小时先交 B=200 版本并继续跑满、两版都留（分批交付，不削） |
| 块 C：画像 + 平方根冲击情景 A∈{0.1,0.5,1,2,5,10,20} 亿 × κ∈{0.25,0.5,1.0} + 线性形式敏感性 + 容量情景 + S1-cost/S6-cost；影子账户 Xideal/X0/X1（自融资 NAV、受困库存、买不成留现金） | **采纳，但影子账户单列为最后一个阶段并单独交付（part3）**：它是本轮唯一新建的账户级引擎，代码风险最大；恒等式不过则该模块 LIMIT，不影响其余。会计口径由规划 session 定：**主版本 = 调整单位的总收益代理账**（用 E1 的 `adjust_factor` 与 `lclose`，分红拆并已在价格里）；真实股数与现金分红分支**无分红数据，登记 LIMIT，不做** |
| 块 D：HAC L=5 主列 + 20/60；日历感知的影响序列 HAC 作新增列；bootstrap 20/60 各 2,000；族 F-source/F-A/F-R/F-C/F-B；RW 附列可选；I-IID 解析 gross 旁证 | **采纳**（旧锚用旧实现，新推断另列，不改 E6e 已验证的 `nw_full_concat/fixedmix`） |
| 预登记 Q1–Q7 逐字落盘 | **采纳**；本 brief §8 给全文，执行端只补时间、哈希与源 ID 映射，**不改写编号与问题**（E6e 曾重写，本轮禁止） |
| 排程 `0 → B1 → part1 → A → C画像/成本 → B2 → C影子 → D → part2` | **调整为三次交付**：`0 → B1 → REPORT_part1 → A → C1（画像/成本/S-cost）→ B2 → D → REPORT_part2 → C2（影子账户）→ REPORT_part3`。part1/part2 不是等用户 GO；part1 之后不得按收益改网格 |
| 全局 worker ≤32；提升须用户批具体数字；父进程验收后写 DONE；不默认 `os._exit(0)` | **采纳**；`00_协议` 第 3 条已于 2026-09-09 改为同样表述。E6e 的 96 是当轮授权，不延续 |
| 删除 proposal 的"70% 平台 / 11/17 正年 / 收缩 0.5 / 5 亿翻转"联合准入逻辑 | **采纳**：brief 与 REPORT 无采纳逻辑；规划 session 判读时另用 |
| "3/4 段稳定才能作前提" | **澄清**：那是规划侧构思假设时对"用作前提的描述统计"的检查，不是对结果的筛法；执行端只报稳定性统计，不筛 |
| 换手缓冲带"价值有限"的推算 | **采纳 web 的保留意见**：跨批次抵消与重复选股使 `仓位×242/H` 只是上界，buffer 仍为未测方向，本轮不做 |
| 行业字段 | 规划 session 核：DEV 与中性化用 `data.get('industry_zx1', data.get('industry'))`，即 FundamentalTL 的日频长表 `industry_zx_1_all`（index=trade_date）。执行端核其历史覆盖与是否逐日更新（PIT）；缺失记 UNKNOWN，不用未来行业补 |

## 1. 起点确认与契约

### 1.1 起点
1. 47 `git status -sb` 应为 `## main...origin/main`（E6e 三个 commit `981c08d`/`7ab38f8`/`0fbd683` 已 push）；三个 5 月的 untracked `.py` 不动、不 add。四地基、`comprehensive_factor_diagnosis.py`、七个 `e6e_*.py` 的 blob 与 E6e manifest 一致。**不 reset、不强推。**
2. 引擎默认 `(5, 8, 1, True)`；`C.COST_BP_BILATERAL == 8.0`。
3. 输入：E6e 目录 `results/20260906_1300_E6e_architecture/`（四件注册表、`preregistration.md`、`limit_register.md`、`source_corrections.md`、`summary/*`、`daily/daily_{gross,pos,turn}_<段>.parquet`、`random_daily/`）；E6c/E6d 结果；E6 `roles.csv`；四段冻结加载路径。
4. `run_manifest.json`：版本、`PERIODS`、输入与脚本 SHA256、本 brief 与 web plan 的 SHA256、实际时间与时区、峰值进程/线程/RSS。
5. `ps` 无本项目残留；记录可用 RSS、socket 1 负载、`ulimit -u` 与当前用户进程/线程数。

### 1.2 数据与生产锁
读取入口日期 ≤ 2026-03-27；不读 E7 目录、不建延长缓存、不查询任何更晚收益。不改池、不加原始因子、不改 I11、不改生产 DEV、不改否决方向；研究变体（窗口、权重、中性化、复权 B、H≠5、影子账户）一律独立命名，不进交付、不进公共库。

### 1.3 契约（规划 session 已核；执行端整段读函数体复核并写 `engine_contract.md`，不符处单列）
- **引擎**：`compute_calendar_pnl`：`actual = W.rolling(5, min_periods=1).mean()`，`ah = actual.shift(2)`，`port = (ah × r̃).sum`（NaN 收益记 0，权重照算入 `position`），`bench = r.where(clean==1).mean`，**`gross = port − bench × position`（已是仓位缩放后的超额，不再扣）**，`turnover = 0.5Σ|ah_t − ah_{t−1}|`，`cost = turnover × bp/1e4`，`net = gross − cost`。停牌日与复牌当日收益 NaN。
- **E6e 日账本**：`daily_{gross,pos,turn}_<段>.parquet`，`trade_date` 为 pandas 索引（`pq.read_table(columns=['trade_date', …]).to_pandas()` 后即为索引）；20,282 列；四段合计 3,940 行，其中 76 个基准全 NaN 日；`net8 日 = gross − turn × 8/1e4`；年化 ≈ 有效日均值 × 252 × 100（规划 session 复算 R1 2015 年 14.8 vs 执行端 `yearly.csv` 14.776；**精确口径由执行端按 `e6e_merge1` 复现 `yearly.csv` 作锚**）。
- **段加载**：`load_segment` 按 `PERIODS = {2010-2014: 20100104–20141231, 2015-2018: 20150101–20181231, 2019-2023: 20190101–20231231, 2024-2026: 20240101–20260327}` 直接 `load_all_daily_data(start, end)`，**无预热**。`load_segment` 内 `mature = close.notna().rolling(20, min_periods=1).sum() >= 20` 并入 `clean`，故每段头 19 天 `clean` 全零 → 基准 NaN（账本 76 个基准全 NaN 日 = 4 × 19）、无持仓；含 tvol 的核再叠 min_periods=30 → 29 天。`days_nohold` 每段 19～29、四段合计 116 即由此来，**不是 bug**。执行端按此复核并把 76 = 4×19 写进锚点。**`history_warmed` 只预热因子（加载起点提前，`end_date` 仍是段末、永不超过 2026-03-27），`clean`/基准/pool0 冻结不重算，所以每段头 19 天仍为空**，比较时用同一支持集。
- **DEV**：`w = min(1/n, 0.01)`，行业 `cap = clean 行业占比 + 0.03` 等比缩减，无下限、不归一；`P(n) = min(1, 0.01n)` 再减削顶。行业 = `industry_zx1`（日频长表）缺则 `industry`。
- **因子**（`features_daily.py`）：`conditional_turnover = turnover_rate / (|log(close/lclose)| + 1e-4)`，1 日；`turnover_volatility_60d = turnover_rate.rolling(60, min_periods=30).std()`；`CVR = (close − vwap)/vwap`（inf→NaN），`CVR_5d/20d` 为其滚动均值（min_periods 3/10）；`intraday_cvr_1d = close/vwap − 1`（E3/E6 研究 spec，数学等于 `CVR`）；`cum_return_w = close/close.shift(w) − 1`，**未复权 close**；`cum_intraday_ret_5d = exp(Σ log 日内)−1`。
- **中性化**：`neutralize_by_mcap` 逐日 OLS 残差（log 市值），有效票 <10 返回原值；`precompute_neutralized_factor` 池 <6 跳过。分组：`build_factor_strategy_holdings_cached` 有效值 <3k 无持仓；`qcut(rank('first'), k)`。`combine(…,'mean')` skipna；`drop_mask = pool0 ∧ ¬kept` 把无值票算作剔除。
- **可成交性字段**：`flag_buy / flag_sell / is_open / limit_up / limit_down / flag_st` 来自 FundamentalTL 长表；语义沿 E6c 的解读（1/0 取值，标"疑似"）；执行端在阶段 0 核每列的历史覆盖，unknown 不等于可成交。
- **随机对照**（E6e）：`random_controls.csv` 与 `random_daily/`（183 GB）可复用；不重跑。

### 1.4 事前登记
在首次新收益评价之前落盘 `preregistration.md` = 本 brief §8 全文（Q1–Q7 表 + 边界段）+ 实际时间 + 输入/代码哈希 + 源 ID 映射；修订另起 `preregistration_amend_<日期>.md` 并标是否已看过收益。

## 2. 阶段 0：E6e 修订与注册（不改研究历史）
- `revisions/E6e_summary_fix/`：保存原文件哈希与副本引用；**七个 `e6e_*.py` 一律保持字节不变**（与 §1.1 的 manifest 核对一致），修复写成新脚本 `e6f_e6e_summary_fix.py`（从 `e6e_merge1` import 聚合 helper，重写全窗口聚合），**输出到该目录**，不覆盖 E6e 原文件：`avg_nh_full = Σ_s Σ_t nh_{s,t} / Σ_s N_s`（用各段实际分母）；`days_nohold_full = Σ_s days_nohold_s`，另拆 `no_target / no_live / benchmark_missing / warmup`；`target_nh` 与五批叠加后的 `live_nh` 分开。复算 `all_candidates / core_depth / neighborhoods_and_frontiers / coverage_and_execution`，按主键排序后断言 net8/net12/gross/pos/turn 等非目标列逐位不变；发现其他列有错另立 issue，不隐瞒。
- 校对 REVIEW 的"hard_total 中位 vs 两项中位之和"，正式归因改报逐配置分量与总量。REVIEW §3 的日均持股（如 R1 62.1、A07 79.3）只是"日均持股"旧口径下按天加权的核对值，阶段 0 的分母若不同以阶段 0 为准，不把它们当目标值。
- 找到 E6e 当时的 `engine_contract.md / PLAN_COPY.md` 则按原字节恢复到 revision 并记恢复时间；找不到写 `RECONSTRUCTED_AT_E6f`，不倒签。
- `e6e_random.py` 的退出问题只记 `limit_register`，本轮不改该脚本（保 provenance）。
- 写 `config_registry / comparison_registry / selector_registry / feature_registry / analysis_families / study_manifest`，先能不看收益展开；候选域 U0-primary / U0-broad / UA 的成员按 E6e 注册表实查后登记确切数。
- 核 `industry_zx1` 的 PIT 性质与覆盖、可成交性各列的覆盖、`amount` 单位（元）、停牌日 `amount` 的语义。
- 产出 `source_corrections_E6f.md`（含上述与 §0.1 的勘误）。

## 3. 注册表与候选域
- **A12 展示锚**（显示标签，精确源 ID 由 registry 映射）：A01/R1 `KT_dep(50,50)|C:k5`；A02/R2 `KT_mean@30|C:k5+cr5:k10`；A03 `KT_dep(50,50)|C:k5+cr5:k10`；A04 `KTC_mean@25`；A05/C1 `KTC_mean@25|cvr_1d:k10`；A06 `KTC_mean@25|cvr_1d:k10+cr5:k10`；A07/C2 `KTC_mean@30|cvr_1d:k10+cr5:k10`；A08 `T@30|C:k5+cr5:k10`；A09 `KTC_mean@25|cmp_mean(cvr_1d,cr5):k10`；A10 `TC_mean@35|cvr_1d:k10+cr5:k10`；A11 `T@25`；A12 `KT_mean@30`。R1/R2 的固定原版始终单独报告。
- **P54** 按 E6e 定义：`{T,K,C,KT_mean,TC_mean,KTC_mean} × {20,25,30,35,40,50}` + `{KT_dep,CT_dep,K_gate_TC} × (45,45)…(70,70)`。
- **候选域**：U0-primary = E6e 核/硬/复合/豁免（约 3,770）；U0-broad = + 全部软 WB/WS 变体（约 6,038，须与 F1/F2 族对账）；UA = 本轮新增 H5 构造变体（窗口、权重、中性化、复权 B）；诊断性共同域/等仓位/H≠5 分支另标，不入 UA。EXPANDED = U0-broad ∪ UA(H5)。
- 每配置主键含：源 ID、各分量窗口、K 估计器与 ε、各角色 CVR 窗、B 窗与复权模式、有理分量权重、深度或 (a,b)、中性化模式/范围、缺失规则、分位实现、否决配方与 k、H、权重模式、支持集、可作候选/诊断原因。
- 别名：公式完全相同的结构别名可合并；全历史 mask 偶然相同只用于复用计算；历史选择按训练期指纹去重。

## 4. 块 A：构造改进地图（新引擎运行，H5 主口径）

### 4.1 因子重建与窗口（默认值必须逐项复现库值：值、NaN 模式、方向、pct、mask、权重）
| 角色 | 扫描 | 定义 |
|---|---|---|
| T 波动窗 | 20/40/**60**/90/120 | `std(turnover_rate)`，默认 60/min30/ddof 沿源；新窗 `min_periods=ceil(w/2)` |
| C 核（慢）窗 | 5/10/**20**/40/60 | 日 CVR 等权滚动均值；5/min3、20/min10 逐项锚 |
| K 均值 `K_MA(w)` | **1**/3/5/10/20 | `mean[TR/(|log(close/lclose)|+ε)]`，ε=1e-4，最少 `ceil(w/2)` 个联合有效日 |
| K 比值 `K_ROS(w)` | 1/3/5/10/20 | `sum(TR)/(sum(|r|)+n_valid·ε)`，共同有效日；w=1 回到日值 |
| 快 C 否决窗 | **1**/2/3/5 | 同一日 CVR 的均值，w=1 不调 std；滚动后再中性化 |
| B 否决窗 | 3/**5**/10/20 | 未复权 `close/shift(w)−1` 为源分支；另登记**仅该 B 因子**的后复权分支（E1 `adjust_factor` 机制），并标除权附近差异及其持仓贡献 |
K 的 ε 敏感性：A12 含 K 者，在 w∈{1,5} × 估计器∈{MA,ROS} × ε∈{1e-5,1e-4,1e-3} 全格；报 `|r|≤ε` 比例、K 尾部贡献、排名变化。

### 4.2 覆盖
- 全部 P54 裸核做其**实际使用分量**的全 OAT（K 的 MA/ROS 均保留）；全部 A12 做适用角色的全 OAT、ε、B 复权对照，保留父子配置。
- 二元联合：T×C 5×5（A12 中同时含 T 与慢 C 的全部锚）；慢 C×快 C（A05/A06/A07/A09/A10，5×4 + 对角线同窗口重复处理对照）；快 C×B（A06/A07/A09/A10，4×4）。
- **KTC 五维联合模板**：T 窗 {40,60,90} × C 核窗 {10,20,40} × K_MA 窗 {1,3,5} × 深度 {25,30,35} × 否决 {无, 快C k10（窗 1/2/3）, B k10（窗 3/5/10）, 二者并集 3×3} = `27 × 3 × (1+3+3+9) = 1,296` 描述符；与其他层重叠者复用，不按结果砍格。
- **分量权重**：KTC 的 37 个唯一有理权重点（`{(a,b,c)/6 : a+b+c=6}` 28 点 ∪ proposal 10 点归一）× 深度 {20,25,30,35,40,50} × 否决 {无, cvr_1d:k10, cr5:k10, 并集} = 888。零权重分量真正 bypass（不再因其缺失剔股）；自然有效域与三分量共同域配对分别报。这是 pct 的权重，不改 DEV。
- **否决强度**：P54 全部交叉快 C 与 cr5 的 k∈{5,10,15,20}：无 1 + 单 4 + 单 4 + 双 16 = 25/核，`54 × 25 = 1,350`。k15/k20 先跑源 helper 原生版（分组 ≥3k 名门槛可能造成技术空仓，如实记），另跑确切人数预算诊断（`m = ceil(n_valid/k)`，稳定 tie 键），两者不合并。
- **深度补档**：`KTC_mean` @15 与 @60，配四类默认否决。
- **持有期**：A12 全部 H∈{1,2,3,4,5,7,10}（84 描述符，含 H5 锚），沿 E6c 的 legacy 与 `common_mature` 两口径和日龄桥三项分解；H 分支不入 H5 主选择库。
- **中性化**：A12 所有适用分量（含否决）各做 N0 不残差化 / NS 市值（源）/ NI 行业 / NSI 行业+市值联合回归；控制范围沿源（pool0 初层、DEP 第二层的 S1）。NSI 用 `[行业哑变量, log_mcap]` 的 QR/SVD 最小二乘，FWL 等价测试（y 与 log_mcap 都先去行业均值）；报设计秩、残差自由度、单票/小行业人数；size 列被行业完全解释时退化为 NI 并标记；有效残差自由度 <3 或有效票 <10 回退 NS，记 fallback 计数；UNKNOWN 行业固定类别。C 角色同时出现时先做全分量同模式主比较，再对 A05/A07/R1/R2 补"只改核 / 只改否决"两路归因；截尾后实际行业/市值暴露照实报。

### 4.3 匹配与记账（所有重要比较）
原生 net8/net12 为主；每个变体对同配方默认版、以及 A12 与全部经济配置对 R1/R2，报同日 `Δgross / Δcost / Δnet / Δpos / Δturn`。**否决类变体（k 平台、否决窗口、复权 B、复合分替换）全部配 `coretrim_matchN`（同日同父同最终人数，按父的冻结核心排序剔深后实际重建 DEV）与等仓位配对（两者同日目标仓位取小者、只向下缩、各自过 rolling 与成本）**；核窗口/权重/中性化变体虽人数不变，仍配 `paired_common_domain`（形成日双方所需分量均可得的票上重建）与等仓位诊断，不以"人数相同"当资本相同。复合/双否决的两个单父都保留。

### 4.4 邻域度量（连续量，不作筛选器）
每节点存结构邻居图（同核、同其余参数、一个有序坐标相邻；类别变换不伪造距离；单纯形边 = 1/6 权重从一分量移到另一分量）。输出：邻居数、唯一持仓路径数、mask Jaccard 与目标权重 L1、邻居 Δnet8 与 Δ`pu_net` 的中位/P10/P90/min、四段与滚动窗、相对 R1/R2 水平、容忍带 τ∈{0.1,0.3,0.5} 的邻居覆盖率（只作列）。网格边界、有效邻居少、多数邻居选同一批票的节点必须标记。

## 5. 块 B：时间地图与选择程序回放

### 5.1 B1 只读账本（阶段 B1，出 part1）
对 U0-primary / U0-broad 全部配置与固定参照（UA 在块 A 后补同表）：2010–2026 逐年（2026 标 `partial_year=True`，完整年与部分年分开计数）、留一年、留 2015–16、3/5 年滚动窗（每年 1 月起；完整窗主表、截尾窗另表）、四段与全窗口；字段含 net/gross/成本/pos/turn、对 R1/R2 的同日配对 Δ 及 SE、有效日。年度集中度三种量：带符号贡献份额（分母近零/为负时标记、不裁剪）、正贡献份额、绝对贡献份额；留年后的实际同日 Δ；总正贡献最高 1/2 年与最低年。逐月、最差 5/20/60 日窗口、主组合与配对差的回撤。旧 8 配置的 yearly 与 E6e 源表锚。分割 D∈{2012-12-31（标 short-training）, 2014-12-31, 2016-12-31, 2018-12-31, 2020-12-31, 2022-12-31} 的**静态** `ledger_portability` 面板（原配置后段截取，注明含分割前已生成持仓）。

### 5.2 B2 选择程序回放与政策账户（块 A 之后）
- **域**：`OLD_structural`（U0 中 KT_dep/KT_mean 系及其既有 C/B 否决，结构条件事先写死）、U0-primary、U0-broad、EXPANDED（U0-broad ∪ UA(H5)）；另报 KTC 子域内选择分布。全部回放标 `fixed_hindsight_library`。
- **规则**（分数 = 训练段 net8 均值，全部从训练日账本重算）：S1 最大者；S2 前 20 等资本；S3 每核族最大者（族由构造元数据固定）+ 每族等资本组合；S4 非支配集合按换手升序等距取 ≤5；S5 对基准 HAC t 最大（L=5，无有限 SE 记未定义）；S6 邻域中位数最高的中心（邻居由 §4.4 元数据预定义）。同分依次用训练均值、较低换手、cfg_id 字典序。S2/S3/S4 先平均目标权重再进引擎计实际成本，另报分账户均值。
- **S_meta**：每个外层训练区间内部用 ≥3 年起始、逐年前向的小折比较 S1–S6 的真实政策账户 net8，按内部验证有效日加权选规则再在整个外层训练段执行；无内部折回退 S1 并标 `insufficient_inner_folds`。
- **正向**：只用截至 D 已记账可知的日收益与构造信息（训练标签最后兑现日 ≤ D，按依赖图消除越界，不机械丢 120 天）。**反向**：D 后训练起点留 `max_feature_dependency + H + exec_lag + obs_window` 保护区，另报无保护区版与排除 2024–26 的版本；反向只是迁移诊断，不是可执行策略。
- **两类可执行账户**：单次选择账户（D 收盘后选，D 后首个形成日起产生目标，T+1 执行，零库存起点，报全区间与共同成熟子区间，末端未兑现比例单列）；**年度 walk-forward 账户（主要程序表现）**：2014 年末首选，2015 起每年末按全部既往数据重选（另报固定 5 年训练滚动版），新选择只控制此后形成批次，旧 vintage 持有至本来退出日——`W_T(policy) = Σ_j α_{j,D(T)} W_T(j)`，α 在前一选择日锁定，整条政策路径一次过引擎（rolling 自然承接 vintage），逐票净交易与成本按契约转换。主回放保留原四段 reset 并对所有参照一致；另给连续库存诊断。
- **读法**：报训练优势 a、评估优势 b、b−a、SE/区间、实际日期；`b/a` 仅作带符号描述，a 近零/≤0/区间跨零时标不稳定，主摘要不按它排序。oracle 分开：单策略 vs 评估段最佳同类型固定单策略；组合 vs 同规则同成员数的 hindsight-rule comparator。推断三层：固定配置配对区间；已完成政策路径的条件区间；**选择稳定性**（训练区间共同块重采样 B=2000，每次重做去重与 S1–S6/内层选择，记选中 ID/核族在原评估区间的分布；S_meta 同 B，超 24 小时分批交付）。六切点 × 两方向不当 12 次独立试验。
- **否决选择回放**：每源父核在训练段选 `Δ_vs_coretrim_matchN` 最大的否决规则，后段评同一规则；若 matchN 日账本缺失先由冻结规则补建。另做跨父核选择附表。
- **cond 时间异质**：逐年 Δ(`KT_dep(50,50)` − `KT_mean@30`)、Δ(`KTC_mean@25` − `TC_mean@25`)、Δ(R1 − `T@25`)，并补同深度/同否决/共同域/等资本比较；成分归因（逐票、行业/市值/流动性分层、前 5/10 贡献；固定权重归因不等于重建组合）；市场状态量（全市场换手、小盘−大盘、截面离散度，训练期可得口径）只作同年相关描述，**不建开关**。
- **单调性**：KTC/TC/T 的源 score 在 pool0 内 5 组前向 5 日收益，按段，均值/尾部/缺失人数/日期级 SE 并列；KT_dep 报 K 分组 × S1 内 T 条件分组；Spearman 只作列。

## 6. 块 C：可实施性

### 6.1 C1 画像与规模成本（覆盖 U0-broad ∪ UA 及 A12 的 H 分支）
- 三层保存：目标、执行后、收益承载；names、投资比例、归一化 HHI/effective_N、最大权重、行业权重与削顶、持仓中位市值/ADV 及全市场分位、低 ADV 权重、停牌持仓、ST、买/卖受限与缺值；除按持仓权重外**按交易金额加权**再报一遍。
- 执行日 e 的输入截止 e−1：`ADV20_e = mean(amount_{e−20:e−1})`（元；停牌日 amount=0 只在语义确认后计入；文件缺失不当 0）；`sigma20_e = std(后复权日收益_{e−20:e−1})`（小数，ddof=1，最少 10 个有效）；另给 ADV60/sigma60（min30）与执行日实得 amount/ADV 压力比。
- 先核 `q_ei`（执行日每票实际净交易权重，`ah_e − ah_{e−1}` 逐票，正买负卖）；`p_ei(A) = |q_ei|·A/ADV_ei`；`c_e(A,κ) = Σ_i |q_ei|·κ·σ_ei·sqrt(p_ei(A))`（当日账户收益小数）；`net_impact_daily = net8_daily − c_e`；`net_impact_ann = 252×100×mean(共同有效日)`。**先构日成本再同分母年化**；买卖各计一次，不额外乘 2。A∈{0.1,0.5,1,2,5,10,20} 亿元，κ∈{0.25,0.5,1.0}，0 冲击为锚；线性形式 `impact_linear = κσ·p/sqrt(p0)`（p0=1%）作敏感性；q/ADV 缺失与高 p 项单列，不填 0。8/12bp 线性成本并列。
- 每情景报 `Δnet_impact_vs_R1/R2`、资金使用、gross 差。容量情景：`50pct_gross_depletion_scenario`、净超额降至 0 的 A、相对 R1/R2 增量降至 0 的 A（平方根律下 `A* = A0·(d/b)²`，符号情形逐一处理）、p 超 1%/5%/10% 的交易金额比例随 A 的曲线；超扫描范围只报外推标志。
- **S1-cost / S6-cost**：对 OLD 与 EXPANDED 的年度前向账户，把训练评分替换为当时可算的冲击后净值（A∈{1,5,10} 亿、κ=0.5、ADV20/sigma20），其余规则相同；评估段同情景重算政策交易成本并与原 S1/S6 配对。

### 6.2 C2 影子账户（最后阶段，单独交付 part3；恒等式不过 → 该模块 LIMIT，其余不受影响）
- 覆盖至少 A12 与 S1–S6/S_meta 实际选中过的配置与政策路径（并集由预登记程序确定）。
- 先建 Xideal（相同账户模型、全部按 VWAP 成交），再 X0（仅无开市/无有效报价日不成交）、X1（X0 + 历史 flag 明确不可买/卖；unknown 保留计数与敏感区间）。比较 源引擎→Xideal 的账户模型差、Xideal→X0/X1 的成交约束差。
- 账户规则：冻结信号/目标/H；未成交买单留现金、当日到期不补买；卖出受限则持有并重试至首次允许或研究截止，退出后收益记至真实卖出；库存 T+1；同票多批净额；现金不足只同比缩买单，不杠杆；受困存量可致超限，披露不强减。估值用当时可得价格，停牌沿最近估值并标陈旧，复牌跳变不漏记；截止仍无终值者报未定价持仓与上下限。
- 两种资本口径并排：`constant_notional`（静态成本地图）与 `self_financing_initial_NAV`（A 为初始 NAV，此后按真实库存价值/现金/实际成交额算参与率与费用）。**会计主版本 = 调整单位总收益代理账**（价格用 E1 `adjust_factor` 机制，分红拆并在价格内，不重复加分红）；真实股数/现金分红分支 LIMIT。冲击若已进成交现金流，不在日收益末端重复扣。
- 自测：现金 + 持仓价值 + 费用逐日对账；零成本/单票/多批/停牌/复牌/研究末端/拆股分红反例；不凭最终可成交性事先选股。

## 7. 块 D：统计补全与统一读表
- HAC：`nw_full_concat` 与 `nw_full_fixedmix` 沿 E6e 实现，L=5 主列，L=20/60 敏感性；H 分支主 L=H 另报 5/20/60；新增日历感知影响序列 `z_t = I_t·(x_t − μ)/mean(I)` 在原时钟上的 HAC 作附加列（旧锚用旧实现）。
- bootstrap：stationary，平均块长 20 与 60 各 2,000，同族共用日期 draw，段内重采样、段长固定；掩码与分母随 draw 重算。
- 族：F-source（E6e F1/F2/F4 全成员复算 + L20/60 + 块长 20）、F-A（UA 变体 − 对应默认父，按窗口/权重/中性化/k/H 子族 + 合并族）、F-R（U0-broad ∪ UA(H5) 对 R1/R2，8/12bp）、F-C（冲击后差，规模×κ 为情景维度）、F-B（域×规则×正向政策账户及固定参照）。逐点区间 + 共 draw max-|t| 同时带；零 SE 保留标签；RW 调整 p 值可作附列（须已验证实现）。**主表不设任何闸。**
- I-IID 解析 gross 旁证：同日每行业父人数 n_h、保留 m_h、总人数 m 固定且 DEV 为源公式时 `u = min(1/m, 0.01)`，`E[w_i] = (m_h/n_h)·u·min(1, cap_h/(m_h·u))`；期望权重过同一线性 rolling 与收益核得期望 gross/pos 与路径均值对账（成本/换手/冲击必须逐路径）；小宇宙全部子集枚举作确定性测试；差以 MCSE 计，超出为调查线索非 FAIL。复用 E6e 随机路径，不重跑。
- 统一记账：小数日收益，显示时 ×252×100；每列带 `n_clock/n_valid/support_id`；成本/gross/net 同一有效日集合；配对差先同日相减再统计；零仓位日单位仓位列 NA。
- 最终地图每个 A12 / UA 平台代表 / 训练规则选出的配置或政策：`源构造 → 参数近邻 → 训练选择方式 → 评估账户 → 8/12bp → 冲击情景 → 成交影子账户 → 时间/风险画像 → 残余不确定性`；候选按"更高原生净值 / 较低成本 / 较少改动 / 近段与全历史取舍"分别呈现，不构造综合分。

## 8. 事前登记（执行端逐字落盘，只补时间、哈希、源 ID 映射）

| 编号 | 问题与目标量 | 竞争解释及设计对照 | 允许的结果和读法 |
|---|---|---|---|
| Q1 | 完整候选的参数变化能否改善相对 R1/R2 的 net？ | 真时间尺度变化 vs 新窗覆盖变化 vs 相邻配置重复：OAT、联合模板、共同域、权重/mask 距离 | 平台、斜坡、局部尖峰或混合均可；不由阈值自动采纳/淘汰。 |
| Q2 | 优势在时间和成分上如何分布？ | 特殊年份/行业/个股贡献 vs 持续增量：年度、滚动、留年、逐票/行业归因 | 集中是风险画像而非自动判假；部分年不作完整年。 |
| Q3 | 在冻结候选域内怎样选，之后的政策账户表现如何？ | 搜索误差、训练量、时间变化和切换成本：多切点、年度回放、嵌套选规则、固定与同训练参照 | 报 a、b、b−a 与不稳定比值；不能识别"真优势概率"或"噪声占比"。 |
| Q4 | 成本/可成交性是否改变候选相对优势？ | 规模冲击、持股价值漂移、阻断买入/被困卖出：同规模同模型、Xideal/X0/X1 | 情景翻转需点名模型与规模；不由 5 亿单格判不可兑现。 |
| Q5 | cond 的贡献是核、深度、否决还是阶段结构？ | 混合因素 vs 独立作用：同深度/同否决/共同域＋逐年成分差 | 允许近段与全窗口相反；市场状态只描述，不建开关。 |
| Q6 | 新核是否仍适配 H5？ | alpha 日龄与资本分配、成本、起止边界：A12 短端/长端及 E6c 三项分解 | 可以出现不同 H 的改善；只登记研究结果，不修改生产 H。 |
| Q7 | 是否发现此前解释依赖记账或流程错误？ | merge 分母、缺值、源定义与运行缺失：修订账本、默认锚、expected-gross、任务状态核对 | 修正测量并限制相关结论；不能为保住预期而改阈值/方向。 |

**边界全文**：所有历史窗口此前已用于策略研究；KTC、角色、方向与本轮选择空间有后见形成成分。本登记只约束 E6f 新增计算与读法，不把历史分析转成独立验证。既有年度数值为 `retrospective_descriptive`（规划 session 写 proposal 前已看过 8 个候选的逐年正号与 2015–16 份额），新的未看过输出为本次预定分析，但不是未触碰市场样本。统计量只作列，采纳/淘汰及 E7 启动由用户另行决定。研究不以性能不佳、区间跨零、单段为负或某一压力情景翻转自动中止。

## 9. 自测与验收（只对正确性设硬条件；收益/区间/某段弱不是 BLOCKER）
- **级别**：GLOBAL STOP（E7 数据进入计算、源码/冻结数据意外变化、财务或时间记账根本不明、共用机余量不足）；MODULE STOP（某新因子默认锚不符、某中性化/影子账户恒等式不符、某字段无法恢复 → 隔离该模块及后继，其余继续）；LIMIT/WARN（行业 PIT 不足、某段成本字段缺失、估值未知、SE 退化、旧文件缺失 → 保留主结果，缺失列 NA，禁止有利插补）；合法研究结果（net 下降、近段差、未超 R2、联合带跨零、低容量、邻域不平 → 全部留表）。
- **锚**：A12 全部 H5 默认格、P54 原核、U0 日 gross/pos/turn 与 E6e 源一致（主键/shape/NaN 对齐后日 atol 1e-12、rtol 1e-10，汇总 ≤1e-10 点；显示值只按其精度）；账本恒等式 76 个基准全 NaN 日 = 4 段 × 19 天（`mature` 过滤）；因子锚 T60/CVR20/CVR5/K1/`cvr_1d`/cr5/cr20（相同源实现查值，等价表达查 allclose 与下游 mask/排名差）；账本回算段 net8 = `sf_*.csv`；逐年 = E6e `yearly.csv`；`A4b_CVRv5` 的 H3/H4/H5/H7/H10 = E6c 同名数字；复权机制 = E1 `selftest_engine_fix` 同源。
- **十二组测试**（web §3.2 逐条）：源锚；因子锚；时间因果（合成前缀截断、未来扰动、入场 VWAP≠收盘、训练标签兑现日、ADV/sigma 用 e−1、selector 在 D 后不读新收益、反向路径不入正向指标）；账户恒等式（`net12−net8 = −turn×4bp`、gross/净/成本、H1 单股、年度切换旧 vintage 不消失、平均权重≠平均净值）；窗口与 K（默认锚、CVR5 min3、ROS 的 ε 乘有效天数、w1 两估计器相同、零权重分量不限制端点）；行业回归（联合 SVD = 正确 FWL、只去 y 均值反例、单票行业、共线 size、缺行业、低自由度回退、截尾后暴露）；匹配/控制（每日同人数、m=0/m=n 极值、thin-day、向下等资本端点、both 毒尾不重复计）；统计（不平均 t、不相减不同支持均值、gap-aware 时钟、分段权重、共 draw、零 SE）；冲击（单位手算、A×4 成本×2、κ 线性、买卖各计、A=0 锚、交叉点各符号、高 p 与 missing 不得零成本）；影子账户（理想账户对照、买不成留现金、卖不出继续风险、库存 T+1、不借钱、陈旧估值/复牌/末端、不凭最终可成交性选股、现金+持仓+费用逐日对账）；随机解析（小宇宙枚举）；工程（登记计数、ID 不冲突、分片幂等、写完整才 DONE、worker 回收、不越并发、记录峰值）。
- **完成定义**：每个登记单元 ∈ {PENDING, RUNNING, SUCCEEDED, FAILED, LIMIT, SUPERSEDED}，按 task_id 计数之和 = 登记总数（重试是同 task 的 attempt）；每输出带输入 hash、schema/行数、有限/NA 计数、产物 hash 与状态；核心模块未跑不得称整轮"通过"，标 `PARTIAL_WITH_LIMITS`。容差不是拟合参数。

## 10. 运行组织（三次交付）
`0（修订与注册）→ B1（只读账本）→ REPORT_part1 → A（构造网格）→ C1（画像/成本/S-cost）→ B2（选择回放与政策账户）→ D（统计）→ REPORT_part2 → C2（影子账户）→ REPORT_part3 + coverage/manifest`。可按依赖并行；part1/part2 不是等用户 GO；part1 后不得按收益改网格；用户中途改方向则保存原登记并做 amendment。
- **问题与交付的映射**：part1 答 Q7（修订与记账）、Q2（静态时间面板）、Q3 的 `ledger_portability` 部分；part2 答 Q1、Q3 的政策账户与 S_meta、Q5、Q6、Q4 的成本情景与 S-cost；part3 答 Q4 的影子账户部分。每份 REPORT 只写本次已答的问题，未答的标"待 partN"。
- **计时**：先在最长段与最短段各跑固定配方试点（特征重建、OLS 中性化、权重、引擎、控制、重采样、写盘、影子账户）报范围；不用最短段线性外推整轮；再久也不削配置、随机诊断或交易对照，只分批交付。
- **并发**：全局同时计算 worker ≤32（A/B/C/D 与子任务共享；BLAS/OpenMP 每 worker 1 线程；不嵌套起子 worker）；绑 socket 1（`taskset -c 96-191,288-383`）；启动前与运行中监控用户进程/线程总数、`ulimit -u`、内存、磁盘，预留 ≥20% 进程限额且不少于 64 任务槽；提升并发须向用户报具体数字并获批后写入 amendment。
- **完成协议**：日志直写文件；父进程 wait/reap；worker 正常 close/join/flush/fsync 后原子 rename 提交；**父进程验证产物 hash 与退出码后写 DONE**；不默认 `os._exit(0)`；清理残留只按 PID+启动时间+cwd+task_id，禁止泛化 `pkill python`。
- 存储：新增确定性配置日账本 float64 parquet 分块；影子账户逐日现金/持仓/费用账；写前估容量。

## 11. 交回
- `results/<ts>_E6f_construction_selection_implementation/`：`PLAN_COPY.md / brief_copy.md / preregistration.md`（含哈希与修订链）、`source_manifest / engine_contract.md / feature_registry`、四件注册表 + `selector_registry / study_manifest`、`revisions/E6e_summary_fix/`、`daily/`、`A_oat / A_interactions / A_weights / A_neutralization / A_horizon / neighborhoods`、`B_yearly / B_leaveout / B_rolling / B_split / B_walkforward / B_nested / B_selection_stability`、`C_exposures / C_orders / C_impact / C_capacity_scenarios / C_shadow_accounts`、`D_hac / D_bootstrap / D_analytic_random`、`checks / task_status / limit_register.md / source_corrections_E6f.md`、`REPORT_part1/2/3.md`。
- `exec_briefs/E6f_REPORT_part1.md`、`_part2.md`、`_part3.md`：协议结构；每份 ≤15 行纯文本摘要；Q1–Q7 每问：原问题 → 数字/分母 → 竞争解释 → 仍未知 → 下一步可操作含义；**不写"可交付 / 已确证 / 必须换核 / 饱和"**。
- **coverage 为硬交付项**：逐条映射 proposal、web plan、本 brief，状态 `done / reused / changed / deferred / unavailable`，改或没做写理由与影响。
- 三份 REPORT 的问题分工按 §10 映射；REPORT_part3 末尾附全轮 coverage 总表。
- WORKLOG 远端 + 本地同文；git：whitelist add `e6f_*.py`（含 `e6f_e6e_summary_fix.py`）、本 brief、`source_corrections_E6f.md`；**七个 `e6e_*.py` 不改、不重新 add**；`git push origin main`；不 `git add .`、不 force、不混入旧 untracked。

## 12. 禁区
不读 2026-03-27 之后的真实数据、不开 E7；不改 I11/pool0/clean 历史成员、生产 DEV、v2 交付；研究中性化/复权 B/H≠5/影子账户不升格生产；不把网格平坦称独立 OOS、不把被选比例/年度胜率/`b/a` 称未来成功概率、不把 0 个联合显著说成 0 个有效策略、不把局部多数说成定律、不以候选数量作独立样本量；不默认裸 KTC 不可作候选、不预设含 cond 必优、不淘汰软否决全族、不把"无新增轴"扩大为 34 因子穷尽；不因慢而减配置；不用 `git add .`；不出现登录信息与主机地址。凡遇"必须改上述任何一项才能继续" → 停，写 BLOCKERS。

## 13. 自审记录（规划 session 2026-09-09；执行端见此段方可开工）
| 类 | 不利因素 | 处置 |
|---|---|---|
| 事实 | proposal 六处错（39 个月、增量方向表述、第四合成因子未扫、min_periods、cvr_1d 浮点、决策地图） | 全部按 web 核实并在 §0.1 承认；proposal 顶部加勘误；`source_corrections_E6f` 收录 |
| 事实 | 四段无预热是本轮才核实的引擎事实，直接影响长窗变体的覆盖 | 写进 §1.3 契约；`history_warmed` 支持集与 `legacy_all` 并排；每变体每段有效票数与无持仓天数必报 |
| 代码 | 因子重建与库不一致（ceil 的 min_periods、ddof、停牌、log 与简单收益、ε 尺度） | 默认窗口逐项复现库值作阻断锚（值/NaN/方向/pct/mask/权重）；K 的 MA/ROS 分别跑；ε 格 |
| 代码 | 行业联合回归实现错（顺序去均值当联合） | QR/SVD + FWL 恒等测试；秩/自由度/回退计数 |
| 代码 | 影子账户是新引擎，现金/库存/估值/企业行动全是新账 | 单列最后阶段并单独交付；Xideal 桥接；恒等式不过 → LIMIT；会计主版本定为调整单位代理账，真实股数分支 LIMIT 不做 |
| 代码 | 政策账户的 vintage 承接与成本 | 整条政策路径一次过引擎，rolling 自然承接；`net12−net8` 与年度切换旧 vintage 不消失作恒等测试 |
| 代码 | 账本口径（索引、76 个基准全 NaN 日、年化） | §1.3 写明；账本回算 = `sf_*` 与 `yearly.csv` 作锚 |
| 统计 | 平台表诱使选最好窗口；新窗只出全样本高点 | 连续量只作列；UA 纳入 EXPANDED 回放与年度账户 |
| 统计 | 选择规则/切点事后挑 | S1–S6 与六切点事前写死、全报；S_meta 嵌套；选择稳定性重采样 |
| 统计 | `b/a` 被读成噪声比例；空间后见形成不可见 | a/b/b−a/SE 为主，比值只描述；`fixed_hindsight_library` 标签；Q3 读法明写不能识别噪声占比 |
| 统计 | 时间分割互相重叠、2026 部分年 | 不当独立试验；`partial_year` 分开计数 |
| 统计 | 多重比较再添硬门 | 族预登记 + 同时带；主表无闸 |
| 混杂 | 同人数 ≠ 同资本 ≠ 同行业；长窗改可得域 | coretrim/等仓位/共同域三种对照并排，各答各的问题 |
| 成本 | 单位错、年化减总和、κ 语义 | 日成本先构再同分母年化；手算锚；κ 为假设的平均执行成本系数，多 κ 多 A 情景 |
| 解读 | 平台 ≠ OOS；情景 ≠ 成本估计；影子账户 ≠ 实盘 | 固定 caveat 进 REPORT；Q1–Q7 读法逐字 |
| 解读 | "确认性"倒签 | `retrospective_descriptive` 标签，已看过的数字原样列出 |
| 运行 | 并发与僵尸进程（E6e 教训） | 全局 32、配额监控、父进程验收、状态表求和 = 登记总数 |
| 运行 | 模块多导致隐性缩域 | 依赖 DAG、分片复用、coverage 硬交付、三次交付 |
| 流程 | 事前登记被执行端重写（E6e 教训） | §8 逐字落盘，只补哈希与映射 |
| 流程 | 两套 final | 本 brief 唯一有效；web plan 与 proposal 的 SHA 进 manifest |
| 节奏 | 有没有把跑得快当约束 | 没有：OAT 施于全部 P54 与 A12，联合模板 1,296、权重 888、k 平台 1,350 全跑；画像与冲击对 U0-broad ∪ UA 全做；选择稳定性 B=2000；S_meta 只分批交付不削；影子账户全做只是放到最后 |

方向确认：单主题（v3 候选定稿前的构造改进、选择程序回放与实施后表现）；不加原始因子、不改池、不改持有期主口径、不改成本、不改生产、不开 E7；探索从宽、无闸门、事前登记逐字；三份 REPORT 交用户与规划 session；判读由规划 session 写 REVIEW 并续写复盘台账。
