# E6j —— 最终 brief（v1.1，2026-09-26）：K 腿两维重构试点（生产 v2 六形态）+ K 分离设计（研究母体 R1 / R2 / A06）

**v1 → v1.1（2026-09-26，用户定"整轮执行完毕并交付后决策端再开始 review，中途决策端不动"）**：A1 规划复核改为执行端机械对账 A1-auto（§5、W13）；决策端在整轮一次性交付前不读、不写、不留言；记录 B 仍是用户的唯一中途动作，另给"事前整表授权"选项（§7）；§14 节奏相应改写。其余不变。**v1.1 → v1.2（同日）**：用户回复"B"，记录 B 定为事前整表授权（§7），整轮无人中途介入；§14 节奏改为条件核验自动进入 Stage 3。

用途：执行端开工文件。设计全文 = `exec_briefs/plans/E6j_plan_web_final.md` v1.1（1,740 行，sha256 前缀 `6dd59dbf`；执行端复制为结果目录 `PLAN_COPY.md`），**本 brief 不重写 plan，只做三件事**：① 规划端在 47 上核过的源事实与身份（§1.3）；② 规划端对 plan 的采纳与少数调整（§0.1，W 项；冲突处以本 brief 为准并已写明理由）；③ 执行组织、登记时序、交付与复核（协议 v1.1）。proposal `E6j_proposal.md`（`2bc4b346`）是参考输入，不是设计权威。用户裁定见 `E6i_RULING_20260926.md`（`9f28b132`）。

**执行端第一个动作**（协议 v1.1）：完整读经验册——`resonance-methodology-hypothesis-postmortem`（#1–#60 与纪律 ①–㊶，见 proposal 附录 C）、`00_协议.md`（已含 v1.1 修订）、`REVIEW_protocol_v1.md`（末尾 v1.1 节）、`E6i_lessons_delta.md`；然后读本 brief §0、plan §0 / §3 / §4.5 / §5.10 / §8，再编译登记清单。

**硬边界不变**：四地基（`data_loader / features_daily / event_study / pool_screening_v2`）与 e6e–e6i 脚本只读；新代码 `e6j_` 前缀放研究目录；`results/` 只增不删；白名单提交 + push main，不 `git add .`；任何文档 / 日志 / 提交不含登录信息、主机地址、账号名；不读 2026-03-27 之后任何真实行情（E7 守卫沿 E6i，攻击测试用合成未来数据）；生产 v2 / v3 展示候选 / U34 / U35 / I11 / DEV 不改——试点"通过"只产出《生产变更候选清单》，`deployment_authorized = false` 永远由用户改。

---

## 0. 一句话问题与设计结论

**问题**（plan §2.1 机制句，逐字）：在 I11 条件域内，现有 K 可能把长期活动水平、短期活动异常和价格响应混合得不合适。保持母体的成功结构，重构这些量如何进入 K 槽位，可能改善边缘股票的排序与资本配置。供给吸收是其中一个可检验的解释，而非已测得的结构参数。

**结论**：P 块 = 用户指定五臂（S = K_rar20 反向、M = K_slope20、S+M 半剂量、C1 = K_MA3、C0 恒等）在生产 v2 六形态上的冻结试点，主母体 A4b_CVRv5、主配置总混入 .25 × H5，按用户六条 + 三句加法 + 实施条件出《暂定政策评分卡》；B 块 = K 分离研究（B1–B7，plan §5）在 R1 / R2 / A06 推导段全跑 → A1 → 记录 B → 后段一次算完；carried = C1 同资本 N × B、领导六形态资本分解、E04 补记、信号面板。P 与 B 两个登记包在任何新收益读取前同时冻结（plan §10.2）。

### 0.1 相对 plan v1.1 的采纳与调整（规划端 2026-09-26 在 47 核源码 / 账本后定；★ = 规划端核出的事实；W = 规划端决定）

| # | 项 | 处置 |
|---|---|---|
| W01 | plan §0–§10、§14 | **全部采纳为执行设计**（J01–J32、A01–A17 的修正一并采纳）；本表只列源事实与少数调整 |
| ★W02 | 成本身份（plan §1.3） | 核实：E5a v2 交付 `results/20260903_1214_delivery_pools_v2/summary.csv` 为 **6bp**（`export_delivery_pools_v2.py:133,145 cost_bp_bilateral=6.0`）：A4b_CVRv5 net_ann 3.0584 / 6.9892 / 8.4299 / 10.3293，turn 12.78 / 20.28 / 27.37 / 32.06（年化换手倍数），avg_pos 0.326 / 0.537 / 0.719 / 0.883，avg_nh 32.6 / 54.1 / 77.4 / 109.0。8bp 换算 `net8 ≈ net6 − 0.02 × turn`（年化百分点）得 2.80 / 6.58 / 7.88 / 9.69。Stage 0 两条锚：先在同一冻结权重上重现 6bp，再由 turn 核 8bp；政策与全部新账户只用 8bp |
| ★W03 | R1 是否 = A4b_CVRv5（plan §1.3 / Q01） | 结构对得上（R1 = `KT_dep(50,50)\|C:k5`：K 保留好半 → 幸存集内 T 中性化保留好半 → CVR_20d k5 否决；A4b_CVRv5 = cond 剔高半 → 组内 tvol 剔高半 → CVR_20d 最高 1/5 剔除），**但账本不逐位相同**：E6i R1 8bp 净值 2.799 / 6.575 / 7.874 / 9.665 vs E5a 换算 2.80 / 6.58 / 7.88 / 9.69（差 0.003–0.023）；持仓 31.9 / 52.5 / 75.6 / 103.2 vs 32.6 / 54.1 / 77.4 / 109.0；投入资金 0.317 / 0.520 / 0.700 / 0.833 vs 0.326 / 0.537 / 0.719 / 0.883。→ 暂判"**同源不同路径**"（可能来自 pool0 口径、中性化范围 dep_nr vs 幸存集、分箱 / 平局、DEV 实现差）；Stage 0 按 plan §3.2 做 mask / 目标权重 / 持仓 / 日收益四层核对写 `parent_identity_map.csv`；主母体保持 A4b_CVRv5（RULING），S / M / C1 单臂在其上标 `historical_exposed = true`（同源对象已在 R1 见过），转移证据来自 Mmean_v2 / Munion_v2 ± CVRv5 与纯净 A4b |
| ★W04 | 试点跑在哪条代码路径 | **生产路径**，不是 E6 研究引擎：`comprehensive_factor_diagnosis.precompute_neutralized_factor`（pool0 内 log 市值 OLS 残差，:315）→ `pct = s.rank(pct=True)`（`export_delivery_pools_v2.py:52`）→ `build_factor_strategy_holdings_cached(neu, pool0, 2, [2])`（:399，剔高半）→ `combine(...,'mean')` / 交集 → `drop_mask(neu_cvr, pool0, 5)`（:86）→ `assign_weights_dev(hold, industry, shares, max_stock=0.01, max_ind_dev=0.03)`（:71）→ `compute_calendar_pnl(w, data, clean, hold_days=5, cost_bp_bilateral=…)`（:488；T+1 VWAP、后复权、exec_lag=1）。**恒等锚 = α = 0 时逐位重现六个 `pool2_*.csv`**（行数 279,649 / 557,683 / 196,546 / 237,213 / 485,751 / 178,572；3,824 天；2010-02-12–2026-03-27；wmax 0.01）与 summary.csv 全部列 |
| ★W05 | SLOT 的源语义（plan §4.1） | `e6h_rules.slot_score`（:73）：各腿 pct 先按源 `leg_pct`（中性化 → 方向 → 变换）算好，`blend = (1−a)·old + a·new`（FALLBACK：new 缺失处用 old；dom = old 有效），**不重排、不重做 OLS**，多腿再 `combine_dense(…,'mean')`，然后 `_keep` + 否决；α = 0 在加载新因子前短路回源父（:109–113）。生产三规则的接法按 plan §4.2：A4b 混合 pct 进第一关 `build_factor_strategy_holdings_cached(...,2,[2])`，第二关 tvol 沿源在幸存集内中性化；Mmean_v2 替换 `combine([pcond,ptvol,pcr20],'mean')` 里的 pcond；Munion_v2 用混合 pct 的剔尾集替换 cond 的剔尾集再与其余取交（保留源"并集剔除 / 交集保留"定义）。E6 研究 `leg_pct` 与生产 `rank(pct=True)` 的百分位 / 平局约定可能不同 → SRC 坐标 = 生产约定；plan §4.1a 的 rank_support 反例与 TRANSPORT 诊断照做 |
| ★W06 | 新测量的源事实 | `K_rar20 = x / lag(rmean(x,20),1) / (d+EPS)`（`e6i_features.py:897`，**基线不含当日**，plan §5.2 之问已答）；`K_rarpre` 基线 = `pre_event_stat(…,'mean')` = [τ−20, τ−1]（:378，τ 更新时重置、无触发 NaN）；`A_rel20 = x / lag(rmean(x,20),1)`（:1338）；`K_MA3/5` = K0 的 rolling mean（`e6f_core` build_raw :145，min_periods = mp(w)）；`K_ROS` = Σtr / (Σ\|r\| + nε)（:157–165）；数据字段 open / high / low / close / lclose / vwap / amount / volume / turnover_rate / negMarketValue / industry 均在 `data_loader.py:104–168` |
| W07 | 政策合并算子（plan §4.5 A01） | **锁定 FULL = E6i `descriptor_stats_all4` 的"四段按有效日合并"口径**（有源约定，不是新选择）；G4 = 四段增量中位作并印列；`policy_aggregation = FULL_E6I_ALL4`，登记前锁，不 PENDING |
| W08 | e-随机的主匹配机制（A02） | `R-MATCH-SRC = Z-MAP basic`（`e6i_randoms.py:53–104`：同日 pool0 内按 `default_rng([SEED, SEGCODE, 0, batch])` 置换，E6i part2 §4 的"真实 − 匹配随机"主读数），种子本就显式；R-COND / R-SCORE-P5 / EDIT-ENTRY / EDIT-BOTH 全做、作诊断 |
| W09 | e-资本的合并（A03） | 复用 E6i `same_capital`（`e6i_stage2.py:11`：逐形成日把子 / 父目标权重都向下缩到共同资本后完整重跑，只缩不放；即 plan §7.2）；符号比较用 FULL；逐段同号只作诊断 |
| W10 | 研究块 H 网格 | plan 读成 H = 1…20 全整数（38,280 / 段）。规划端定 **H ∈ {1, 2, 3, 5, 10, 15, 20}**（7 档）：RULING 第 14 项"H 1–20"是执行端对 E6i 网格 {1,2,3,5,10,20} 的范围写法；加 15 是 L 线含冲击最优 H 15–20 的旧发现。210 行 × 3 α × 7 H = 4,410 → **13,230 原始账户描述符 / 段**；用户若要全整数可直接改此项（机械扩展，登记单位不变） |
| W11 | 试点网格 | 不变：4 臂 × α{.125,.25,.5} × H{3,5,10,20} × 6 形态 = 288 + C0 24 = 312；列对象 216；共 528（plan §4.3） |
| W12 | 政策确认状态（A01 / §0.3） | `policy_confirmation_status = confirmed_by_proceeding`：用户 09-26 消息 B"其他我觉得基本都 ok"（RULING 第 15 项）+ 消息 C 指示写 brief 开工；六条原话与三句加法按 RULING 第 15 项计算；任何生产改动、对外数字、E7 读取仍须用户另行授权 |
| W13 | A1 时序（v1.1 改） | **决策端中途不动**（用户 09-26）：A1 的功能由执行端在提交记录 B 草稿前以脚本完成（§5 A1-auto 七项，任一 FAIL 不得提交 B 草稿），报告 `routing_review_A1_auto.md` 随 B 草稿附上；决策端对登记的判断移到整轮 REVIEW；RULING 第 12 项据此修订（`E6j_RULING_20260926.md`） |
| W14 | 随机与重采样规模 | 1,024 路径起、MCSE 目标 ≤ .03 年化百分点、不足按 512 增补（plan §8.1）；stationary bootstrap 块 20 / 60 各 2,000 次；显式种子按 plan §8.2；P 保留完整随机日账本，B 流式可重放（plan §10.6） |
| W15 | 协议 v1.1 | 12 条修订今日已追加到 `REVIEW_protocol_v1.md`（`dde9e255`）与 `00_协议.md`（`1dd8033a`）末尾；执行端开工前读；VERIFY brief 的预期值由规划端脚本从产物现算 |
| W16 | 文献限定（plan §12） | 采纳：Sun–Wang–Zhu 2023 与 Zhang–Chen–Yeh 2021 不合并；日频 K 的 ε、事件窗、收缩、协动 λ 是本轮适配构造；REPORT 不写"文献验证过此策略" |
| W17 | 结论用语 | 只有 通过 / 不通过 / 不可判 / 结构依赖 / UNAVAILABLE / UNDEFINED；禁用词清单沿 E6i brief §15（生成器扫描） |
| W18 | 交付物 | plan §10.7 七件 + `E6j_REVIEW_input.md`；表头十项 + 主体 + exposure + query_id；REPORT 冻结、补充另起 supplement |

### 0.2 "跑久一些、多用算力都没关系，跑得快不是红利"（用户 09-26）在本 brief 的落法
不预筛；六形态 × 全网格 × 1,024 路径 × 2,000 bootstrap；B 块 13,230 描述符 / 段（W10）；C1 同资本重报；估计 5–8 天，不以短为目标。并发与内存按 §14 实测配额，不为省时间砍范围。

---

## 1. 起点确认与契约

### 1.1 起点
- 47 HEAD = 远端 main = `052fb53d`（E6i VERIFY 交付后）；E6i 结果目录 `results/20260923_0254_E6i_measurement_need_fit/`（registry / accounts / statistics / randoms / carried / verify 只读复用）；E5a v2 交付 `results/20260903_1214_delivery_pools_v2/`（六个 pool2 权重文件 + summary.csv + _delivery_stats.csv）；生产脚本 `code/project_core/export_delivery_pools_v2.py`（形态定义 :4、:121–129、:220–223；成本 :133、:145）。
- 本地 exec_briefs 与 47 `code/project_core/exec_briefs/` 三处镜像：plan（`6dd59dbf`）、proposal（`2bc4b346`）、RULING（`9f28b132`）、REVIEW v1.0.1（`f94820c6`）、supplement 1 / 2、本 brief；执行端开工时按 sha 核对并写 `source_manifest.json`。

### 1.2 数据与生产锁
2010-01-04 .. 2026-03-27；四段 2010-14 / 2015-18 / 2019-23 / 2024-26；E7（> 2026-03-27）不读；基础池、I11 定义（`define_i11_signal`，`pool_screening_v2.py:43–61`，分位阈值）、5 日观察、DEV（个股 ≤ 1%、行业相对基准偏离 ≤ 3%、不归一）、T+1 VWAP、后复权、生产 H5、源 8bp 成本算法（`cost_bp_bilateral × daily_turnover`）不改。

### 1.3 契约（规划端已核；执行端整段读函数体复核并写 `engine_contract.md` + `source_resolution.md`，每条三栏：定义处 / 调用处 / 默认值；差异登记不改源）
1. 生产路径与六形态定义、6bp 成本、pool2 文件（W02 / W04）。
2. R1 / R2 / A06 定义（E6i `registry/mothers.csv`：R1 `KT_dep(50,50)|C:k5` dep_stage1 / dep_stage2；R2 `KT_mean@30|C:k5+cr5:k10` mean_leg0 / 1；A06 `KTC_mean@25|cvr_1d:k10+cr5:k10` mean_leg0 / 1 / 2；A08 `T@30|C:k5+cr5:k10` 仅 T，无 K 槽位 → 只参加 B6）；KT_dep 实现 `e6e_core.py:445–470`（第一关 `keep_pct_mask(S.opct[K], pool0, a)`，第二关默认在幸存集 S1 内重做 T 市值中性化 `precompute_neutralized_factor(raw[T], S1, log_mcap)`；`dep_nr` 变体沿 pool0 中性化只换排序范围）→ plan §6.2 双开关只对 A4b / R1 这类 dep 核有意义。
3. SLOT 语义（W05）；FALLBACK 与 REPLACE 分名（`e6h_rules.py` 头注）；α = 0 短路。
4. 新测量源定义（W06）；ε = 1e−4 只用于 |r|；换单位同改 ε（plan §3.4）。
5. Z-MAP basic / industry / persist20 机制与种子（`e6i_randoms.py:53–113`）；`same_capital`（`e6i_stage2.py:11`）；`dcore` 同人数核心（part2 §4 定义）。
6. 数据字段与时钟（W06；plan §3.3）：`r_cc = log(C/lclose)`、`r_on = log(O/lclose)`、`r_id = log(C/O)`，有符号相加恒等；停牌 / 0 量 / H=L / 涨跌停逐项状态码（plan §5.1a）。
7. E6i 后段封存目录、`first_look_receipts.json`、记录 B 批准格式（`registration/record_B_approved_E6i.json`）作模板。

### 1.4 事前登记
两个登记包在任何新收益读取前落盘（plan §10.2）：**P 包** `preregistration_P.md` = plan §4 全文 + §9 Q01 / Q02 / Q07 / Q13 / Q15 / Q16 + 本 brief W07 / W08 / W09 / W12 的锁定值 + 五臂对象 sha + `selection_exposure_ledger`（S 方向 = E6i 对照方向事后转正、S / M / C1 已在 R1 见过、试点母体与 R1 同源、α / H 网格、政策制定史）；**B 包** `preregistration_B.md` = plan §5–§6 + §9 全部 Q + §5.10 210 行登记表（编译器现算计数）+ W10 网格。两包都带时间戳、输入 / 代码哈希；修订另起 `preregistration_amend_<日期>.md`，不改编号与问题。plan §9 Q 卡以 `PLAN_COPY.md` 行号 687–792 逐字引用，不转录。

---

## 2. Stage 0 仪器（不改任何数字口径；任何账户之前）
1. **生产路径锚**：α = 0 重现六个 pool2 权重文件逐位（行、日期、ticker、weight）与 summary.csv 全列（6bp）；再以 `cost_bp_bilateral=8` 重算得 8bp 账本，核 `net8 ≈ net6 − 0.02 × turn` 并保存为六形态 8bp 母体日账本（后续一切"子 − 母"的母）。任一形态不一致 → BLOCKER。
2. **R1 vs A4b_CVRv5 身份**（W03）：mask / 目标权重 / 持仓 / 日收益四层比对，写 `parent_identity_map.csv`（exact_alias / same_structure_diff_impl / different；差异来源逐项：pool0、中性化范围、分箱平局、DEV、成本）。
3. **SLOT 三规则恒等锚**：α = 0 ≡ 母体；MA1 ≡ K0；FALLBACK α = 1 ≠ REPLACE（有回退）；plan §4.1a 两个无经济新增反例（复制旧坏度作 NEW；置缺失不重估）与 TRANSPORT 诊断；`operator_discrepancy_manifest`（SRC vs SPEC）。
4. **新成员合成检验**：日夜有符号恒等、涨跌零三分区与频率闭合、R_ev 常数比例过程 ≡ 1、prefix 不变（后缀扰动）、事件时钟只用 ≤ t 触发、OLS 退化状态码（x 无变异 → NA；y 常数 → β = 0 有效）；plan §13 的 90 项合成检查在 47 环境重跑并加真实字段测试。
5. **显式种子**（plan §8.2）与并行 / 续跑逐位重放实测；A0 编译对账（问题 → 对象、任务 → 对象两张表）；brief 预期值脚本；守卫攻击 ≥ 覆盖矩阵（不凑 48/48）。
6. 交付 `source_manifest.json`、`parent_identity_map.csv`、`anchor_results.csv`、`feature_contracts.csv`、`permission_ledger.json` → REPORT_R0。

## 3. A0 登记（执行端编译；不等收益）
P 包 528 描述符（W11）；B 包 210 行 × 3 α × 7 H = 13,230 / 段（W10）+ COMMON_SUPPORT 四账户（每母体—角色 α .25 × H{3,5,10,20}）+ 匹配 N / 同资本 / 随机 / TRANSPORT / T-refit / 剂量控制分表；精确别名保留 exposure 行不重复算；总数由编译器现算，两张对账表都过才开跑（plan §5.10）。

## 4. Stage 1 测量诊断（推导段；不作准入门）
新成员单位 / 符号 / 覆盖 / 价格限制 / 最小有效数 / 分量恒等 / 事件日龄 / 同 K × size × 行业条件形状；T0 类画像若做须带 pool0 同人数对照（㊱）。

## 5. A1 复核 → A1-auto（执行端机械对账；决策端中途不动，用户 2026-09-26 定）
决策端在整轮一次性交付（§14）之前不读任何中途产物、不写、不留言。A1 原来要核的内容由执行端在提交记录 B 草稿前用脚本完成，写 `routing_review_A1_auto.md`，**任一项 FAIL 不得提交 B 草稿**（修正走 `preregistration_amend_<日期>.md` 并登记暴露）：
1. 登记对账：问题 → 对象、任务 → 对象两表逐元组相等；B 包 210 行 × 3 α × 7 H = 13,230 / 段、P 包 528 由编译器现算并与登记表一致。
2. 每个对象五类身份齐全（measurement_id / orientation_id / operator_id / parent_id / account_id），orientation 带方向论证句与"是否双向登记"，hypothesis_id 回链 Q01–Q17，exposure 标记齐（historical_exposed、direction_2of1、alias_of 等）。
3. 槽位合法性：A08 无 K 槽位；B6 只在 T 位；B7 K / T 分域；每个对象都含主配置 .25 × H5；H 集合 = {1,2,3,5,10,15,20}，α = {.125,.25,.5}。
4. 锁定值非空且与本 brief 一致：`policy_aggregation = FULL_E6I_ALL4`、`random_ref = R-MATCH-SRC (Z-MAP basic)`、`capital_ref = same_capital`、δ = .10（敏感 .05 / .15）、`policy_confirmation_status = confirmed_by_proceeding`。
5. `source_resolution.md` 覆盖 §1.3 七条源事实，差异逐条登记（不改源）。
6. Stage 0 六项锚全部 PASS（pool2 逐位、身份图、SLOT 恒等、合成检验、种子重放、A0 对账）。
7. B 草稿逐对象含 source exposure / 机制重要性 / 有效支持 / 推导读数 / 未解决限制；不设"两推导段中位 ≤ 0 不进"的门。
决策端在 REVIEW 里再做人工 A1 判断；那时发现的登记错误按复盘条目处理，对应对象读数降级或标注，本轮不重跑。代价写明：语义级登记错（例如某个方向论证写反）中途无人拦，只能事后降级——E6i 的三次编译遗漏（#49）都是执行端自己对账抓到的，机械对账覆盖了主要风险。

## 6. Stage 2：推导段账户（B 包）与试点四段账户（P 包）
- B 包：R1 / R2 / A06（B6 加 A08）推导两段全网格，FALLBACK 主 + COMMON_SUPPORT 诊断，随机三类，plan §5–§8 全文；负结果照常。
- P 包：P 登记落盘 → 六形态四段一次算完（不是 OOS；登记的意义是钉判据）→ 封存回执 → 按清单读；plan §4.5 政策合同（六条、三句加法、实施条件、G4 / FULL 并印、δ 敏感、市值 gap、Δturn、MC 状态、`historical_exposed`）；同资本 / 同人数核心 / 随机 / TRANSPORT / T-refit 双开关（A4b）/ 编辑账本（plan §6.1）/ 影子库存（plan §7.6）全做。

## 7. 记录 B（B 包后段授权）—— 用户 2026-09-26 选 **方式 B：事前整表授权**，整轮无人中途介入
- **授权来源**：用户 2026-09-26 回复"B"（`E6j_RULING_20260926.md`）。授权对象 = Stage A 冻结的 B 包全部登记对象（manifest sha 在冻结时写死）。执行端在 Stage A 写 `registration/record_B_preauthorized_E6j.json`：approval_id、用户原话与时间、manifest sha、三个生效条件、对象 ID 与完整派生闭包。
- **生效条件**（三者全满足才进入 Stage 3；缺一即停、写 BLOCKER 等用户，不自行修补）：① Stage 0 六项锚全 PASS；② `routing_review_A1_auto.md` 七项全 PASS；③ 进入 Stage 3 时冻结清单 sha 与授权时相同——任何 `preregistration_amend_*` 都使授权失效，须用户重新一句话授权。
- 执行端仍在 part1 后写 B 草稿（逐对象 source exposure、机制重要性、有效支持、推导读数、未解决限制）作记录，**不等待任何人**；条件核验写 `registration/record_B_conditions_receipt.json`，然后按 §8 两后段一次算完、封存回执后读。
- **不设"两推导段中位 ≤ 0 不进"的门**；不在冻结清单内的对象不算后段账户。P 包四段在 P 登记落盘后同样自动执行（原就没有用户闸）。plan 本来就不按推导段结果删对象，所以事前授权与中途批准在信息上等价，只少一次人工确认。

## 8. Stage 3：后段一次执行（B 包）
两后段同一版本一次算完，封存回执后读；E7 守卫各层；修复走 revision 目录不覆盖原件（plan §10.4）。

## 9. Stage 4：三个结果包 + REPORT
`pilot_policy.csv`、`research_object_results.parquet`、`hypothesis_outcomes.json`（Q01–Q17 原文 + 真实 query + 效果 / 机制 / 未知 / 下一次设计改变 + `hypothesis_update_card` 八字段）；《生产变更候选清单》四标签分开（policy_score / mechanism_status / replication_status / deployment_authorized）；REPORT R0 / part1 / part2 / part3 / carried（plan §10.7）+ REVIEW_input + lessons_delta；每张表十项表头 + 主体 + exposure + query_id；数字 / 计数 / 全称句由同一结构化查询产生。

## 10. carried（plan §7.7）
C1 同一 N × B 配置重报 NATIVE / MATCH-CAP / ATTRIBUTION；领导六形态资本分解（名义投入资金、单位资金 gross / net、总 gross / net、持股数、换手、费用；措辞"投入资金上升"）；E04 补记（240 臂两次抽样中位、part1 Q4 句复核，不重跑）；信号线只复用描述面板。

## 11. 统计与账本（plan §7–§8 全文执行）
三种资本视图；逐日精确分解；成本合同 8bp 主 + 6 / 12bp 对账 + 平方根冲击 A5κ.5 / A10κ1 / κ0；随机三类 + 稳定五日映射 + 不重叠稀疏分区 + EDIT-ENTRY / EDIT-BOTH + SM 共享 donor；HAC 主滞后 H、敏感 max(2H,20)、缺失日不压缩；bootstrap 点估（未中心化）与零基线（中心化）分文件；同时带三层；MDE80 = 2.80·SE，`T_required` 只作静态尺度提示；年度 / 留一年 / 去 2015+16 / 去 2020 / 最近段；回撤定义分开。

## 12. 事前登记（`preregistration_P.md` / `preregistration_B.md`；只补时间、哈希、源 ID 映射）
plan §9 Q01–Q17 原文（`PLAN_COPY.md` 687–792 行）逐字；假设模板 v2（proposal 附录 B）十项每 Q 填齐；锁定值：W07 FULL_E6I_ALL4、W08 R-MATCH-SRC = Z-MAP basic、W09 same_capital、W10 网格、W12 政策确认状态；`selection_exposure_ledger` 逐条。

## 13. 自测与验收（只对正确性设硬条件）
Stage 0 六项全过；A0 两张对账表逐元组相等；任务状态和 = 登记数、FAILED 须被同名成功重跑覆盖（协议 v1.1 ⑤）；受控随机重放（分片 / 并发 / 续跑）逐位一致；每份 REPORT 生成器：表头缺项 FAIL、禁用词 FAIL、主机地址 / 账号扫描 FAIL、query_id 跨文件唯一。经济结果不是验收条件。

## 14. 运行组织
先 profile（代表母体、短 / 长 H、新估计、随机路径：配置数、日期数、每任务 RSS / 线程），再定并发；起步 12、上限 ≤ 24、BLAS ≤ 4、`ulimit -u 4096`、`taskset -c 96-191,288-383`；不整块加载 npz；原子写 + checksum + SUCCESS 回执；按 PID + 启动时间 + 完整命令行清理，不 `pkill -f`、不 `os._exit(0)`；存储按 plan §10.6（P 完整随机日账本；B `STREAMED_REPLAYABLE`）。交付节奏：R0 → part1 + B 草稿（附 A1-auto）→ 记录 B 事前授权条件核验（自动，§7）→ part2 → part3 + carried → REVIEW_input + lessons_delta + 闭包门 → **一次性交付**；中途的 R0 / part1 / part2 只落盘并镜像，决策端不读；交付后决策端才开始：`E6j_VERIFY_brief.md`（预期值脚本现算）→ 执行端 §C + V → 决策端 D + REVIEW → 用户裁定（协议 v1.1）。

## 15. 交回
七件 REPORT / 文档（plan §10.7）三处镜像 md5；WORKLOG 只记操作事实；`E6j_lessons_delta.md` 收拢判断与教训，**执行端不写共享 memory**；REPORT 交付即冻结；复核按协议 v1.1：规划端写 `E6j_VERIFY_brief.md`（预期值脚本现算），执行端只读程序 V + §C 收尾，决策端 D + REVIEW。

## 16. 禁区
不读 E7；不改四地基 / e6e–e6i / 生产 v2 / U34 / U35 / v3 / I11 / DEV；不按推导段收益预筛或改网格；不在出数后选 SRC / TRANSPORT、G4 / FULL、随机机制中较好的一套；不把研究块的好候选替换 P 主对象；不写"可以上线"类判词；不用 `hash()` 作随机种子；不 `git add .`；不删 results；不写登录 / 主机 / 账号信息。

## 17. 自审记录（规划端 2026-09-26；四类不利因素 + 两问；执行端见此段方可开工）

| 类 | 不利因素 | 处置 |
|---|---|---|
| 代码 | 生产路径与 E6 研究引擎不同（中性化范围、pct 约定、DEV、成本） | 试点跑生产路径；pool2 逐位锚 + 6 / 8bp 双锚；R1 身份四层核对（W02–W04） |
| 代码 | SLOT 在 Munion / Mmean 上是新实现 | α = 0 恒等、MA1 ≡ K0、rank_support 反例、SRC / TRANSPORT 双路径登记 |
| 代码 | 新成员实现错、日内 / 隔夜口径错 | 合成恒等 + 真实字段测试 + prefix 守卫 |
| 代码 | 随机种子 / 并行重放 | 稳定哈希种子、实测分片 / 并发 / 续跑逐位一致 |
| 统计 | S 方向事后选正；S / M / C1 已在 R1 见过；试点四段非 OOS | exposure 台账；`historical_exposed`；转移证据只来自其他五形态；政策标签四分 |
| 统计 | 政策合并 / 随机参照 / 资本合并三处口径若事后选 | 登记前锁 W07–W09（有源约定），两 profile 并印不交叉 |
| 统计 | 网格与多重性 | 主配置事前 .25 × H5；切片不进结论句；多重性表；随机通过率作机会基线 |
| 运行 | 存储 TB 级、耗时 | 流式可重放、profile 后定并发；不砍范围（用户 09-26） |
| 解读 | 合成臂盖成员、结构依赖读成无效、"通过"读成"证实" | 成员 c 状态并印；六形态各自计分；结论词限定；四标签分开 |
| 解读 | 对话层先报好消息 | ㊴ |
| 节奏 | 有没有把跑得快当约束 | 没有 |
| 流程 | 决策端中途不动 → 登记语义错中途无人拦 | A1-auto 七项机械对账 + 任一 FAIL 阻断 B 草稿；事后在 REVIEW 降级对应对象、记复盘，不重跑；E6i #49 的三次编译遗漏正是执行端对账抓到的 |

**两问**：① 不利因素是否已最大程度降低——剩余最大风险仍是"S 方向事后选正"与"试点对象在同源母体上已见过四段"，只能靠转移到其他五形态、分歧 / 编辑账本与登记前锁判据缓解；② 没有把跑得快当约束。

**执行端开工信号**：见到本段即可按 §14 节奏开工；开工前先完成 §0 的"第一个动作"（读经验册与协议 v1.1）并在 WORKLOG 记一行。
