# E6i —— 最终 brief（v1，2026-09-23）：因子端迭代 = 按母体需求重设计测量（八轴估计量族）→ 测量级诊断 → 角色账户（M0 / M1 / M2）→ 一次用户授权 → 后段首次观察；carried = C1 人数 × 行业宽度交叉、C2 成本透镜、C3 信号边界描述

用途：本文件是 E6i 唯一有效的执行文件。设计层最终版是 web plan `exec_briefs/plans/E6i_plan_web_final.md` v1.0（本地 SHA256 前缀 `cf9ce859575401dc…`，1,734 行），执行端整份读并复制进 results 作 `PLAN_COPY.md`；**本 brief 未提到的细节按 plan 执行，两者冲突以本 brief 为准**。输入指纹：`E6i_proposal.md` SHA256 `38feb8c1…`（68,130 B，与 plan 附录 C 一致；本 brief 定稿同日在 proposal 顶部加了勘误块，加后 SHA256 前缀 `f3c2fd441a301b26…`，405 行 → manifest 记两个哈希、WARN 不阻断）；`E6h_REVIEW.md` `5eb27e87…`（37,021 B，与 plan 一致）。前置：E6h 四份 REPORT、`E6h_REVIEW.md`、47 `results/20260912_1147_E6h_need_driven_routing/`（HEAD `4b1ee8e`，工作区只有旧 untracked：三个 2026-05 `.py` + 七个 `.sh`，不动、不 add）。先读 `00_协议.md`。

---

## 0. 一句话问题与设计结论

**问题**（plan §0.1）：在 I11 固定候选域与现有架构内，能否通过改进**活动水平 / 不稳定性、价格响应、风险分量、相对收益、昼夜结构、位置、量能动态、同业背景**这八轴的测量，使某个明确决策（K/T/C 槽位、否决、边缘替换、焦点条件）比当前做法更有价值；改善来自测量、角色、资本、时间还是精度。证据链 = `源字段与测量对象 → 数值 / 统计有效性 → 目标集合中的条件信息 → 明确角色 → 完整账户相对母体的改善 → 历史迁移与实施敏感性`，任一环失败都要定位，不统一归因为"因子没有信息"。

**设计结论**：按 plan §11.1 任务图执行 `P0 起点 → A0 登记 → Stage 0 仪器 → Stage 1 测量（REPORT_R0）→ A1 规划复核 → Stage 2 推导账户（REPORT_part1）→ 记录 B（用户授权）→ Stage 3 后段（REPORT_part2）→ Stage 4 合并复盘（REPORT_part3）`。八轴同一研究契约；**无 IC / 单调 / 同号 / 席位任何硬准入门**；研究目录（`research_catalog_v36`）与候选库更新提案（`candidate_library_update_proposal`）分开，后者可为空、单项或互补多项，由用户决定；地基、生产、信号、E7 全不动。

### 0.1 相对 web plan 的采纳与调整（规划 session 决定；★ = 规划 session 自身错误，已按 47 源码核实）

| web plan 内容 | 处置 |
|---|---|
| **W01** I11 的 P25–P55 是截面分位，不是 5 日涨 25–55% | ★ **核实成立**：`pool_screening_v2.define_i11_signal`（:43–61）对基础池内 `CMF_20d / cum_return_5d / intraday_ret` 取当日 `rank(pct=True)`，条件 `cmf_pct ≥ 0.80 ∧ 0.25 ≤ cr5_pct ≤ 0.55 ∧ ir_pct < 0.70`；`handoff_i11/03-已拍板口径与决策.md` 第 23 行也写的是 P25/P55。proposal §1.3 C / §4.3 / §9.1 的"本池由定义强漂移 → RS/YZ 适配"先验**删除**（proposal 顶部勘误；复盘 #43）。保留全部估计量，适配性由 Stage 1 实测的漂移 / 跳空 / 涨跌停 / 事件日龄分层决定（§4） |
| W02 std = mean × CV，水平可能有价值 | 采纳：T 族保留原 std、水平、CV、趋势与分量，`T_pair` β 网格 |
| W03 K 与 Amihud 只在同时点、同分母、无偏置时成倒数关系 | 采纳：proposal "合族"保留为**分组**，不称同一测量；分开单位、聚合顺序与方向对照 |
| W04 logK 不改原始排序、中性化后可不同 | 采纳；表示对照两条 |
| W05 无符号收益对换手斜率不叫 Kyle λ | 采纳，命名 `abs_return_activity_slope` |
| W06 小 IC 不是根因；加角色相关形状（M2） | 采纳 |
| W07 / W08 仿真按 ADEMP，不设 2% 硬锚 | 采纳；proposal 的"偏差 < 2%"改为报告项 |
| W09 事件窗掩码只用已知触发 | 采纳；proposal `T_exsig` 的对称掩码改为因果版，对称版只在 t 信息集逐次重算且不进主网格 |
| W10–W13 MAD 同窗中心、源锚原 min_periods、预估计残差、隔夜份额稳定版 | 采纳 |
| W14 涨跌停用 PIT 源标志 | 采纳且可行：`data_loader.load_limit_prices`（:276–280）已装 `limitUpPrice / limitDownPrice` 长表；触板 = `H ≥ limit_up − tol ∨ L ≤ limit_down + tol`，一字板 = `H == L ∧ 触板`，缺标志日标 UNKNOWN；不再用 |chgPct| ≥ 9.8% |
| W15 C 不是假零对照；A / S 同等契约 | 采纳：proposal §4.6 "对照族"改为真实候选（RC 路线）；假阳性检查改用合成负对照 + 精确 no-op + 局部随机化（plan §8.3） |
| W16 双主读数（策略问题 = 对真实母体；机制问题 = sameN） | 采纳；P20 / P21 按各自原登记主读数回答旧问题 |
| W17 取消"一族一支 / 两段同号 / ≤12 描述符" | 采纳（与用户"探索从宽"一致）。**用户"剩余日频键不一次全加进候选库"仍成立**：`research_catalog_v36` 是研究资产，`candidate_library_update_proposal` 是另一产物且由用户定；U34/U35 本轮不改 |
| W18–W23 | 采纳（W23：D-S 改为固定池内 `signal_margin_profile`，不重建信号） |
| W24 float64 主计算；并发按实测 | 采纳精度；**并发有硬上限**（§14）：起步 12 worker，实测总线程 / RSS 后可升，**≤ 24**；每 worker 先设 `OMP/MKL/OPENBLAS_NUM_THREADS ≤ 4`（47 `ulimit -u = 4096`，E6h 峰值 2,663 线程正是撞这个上限）；超过 24 需用户批准具体数字 |
| W25 假设分层更新 | 采纳；结果卡模板 plan §10.2 |
| §3 契约（LEGACY_EXACT vs RESEARCH_CAUSAL；单位；一字板三政策；事件钟；母体槽位；float64；同义三层） | 采纳；`turnover_rate` 在 `data_loader` 无缩放（:166 直接改名）→ P0 核数值量级（百分数 vs 比例）与分母口径后写进 `feature_semantics_v2.csv`，K 的 ε=1e−4 的相对尺度据此说明 |
| §4 八轴目录（全部成员） | 采纳。**EDGE**：47 无 `bidask` 包、可达 GitHub（raw 200）→ 不 `pip install`，从作者 repo 取固定 commit 的实现文件逐行审阅后 vendor 到 `e6i_vendor/`，记录 commit SHA 与文件 SHA；**Meilijson**：按 plan §4.3 四分量与系数实现，执行端对照 arXiv 0807.3492 式 (1)/(3) 复核系数，核不出 → `UNAVAILABLE_SOURCE` 隔离该成员，其余继续 |
| §5 路线 RT/RK/RV/RR/RO/RC/RA/RS/RL 作 A0；SLOT α{0,.125,.25,.5,1} FULL/FALLBACK；ADD_SCORE γ{.0625,.125,.25}；VETO k{5,10}；软缩减 λ{.25,.5,1}；SWAP q{.05,.10,.20}；H{3,5,10,20} + 快端 {1,2}；四臂；§5.7 生成器合同 | 采纳；H 网格比 proposal 宽，接受 |
| §6 Stage 1 六集合 / 四层；对照表；随机对照 256→512→1024；同资本；逐日归因 | 采纳口径与种类；**随机路径数量按优先级分配而不是统一 256**：§7.1 固定代表 × 主角色 × 母体 × H 先 256（MCSE > 0.05 pp 且为 B 草稿候选再 512 / 1024）；非代表成员先 64，进 B 草稿候选时补到 256。理由 = 可行性排序（E6h ~2 万次运行 ≈ 1.5 天 / 12 worker），不是收益筛选；执行端先出精确计数与计时样本，若预算允许可整体抬高 |
| §7 M0 / M1 / M2 | 采纳；M2 作 `part1b` 子交付，不阻断 M0 / M1 的 `part1a`；M2 只对 §7.1 代表运行，程序（basis / λ 网格 / 年度更新 / 回退）在 B 冻结 |
| §8 统计（NW lag=H 与 2H/20 桥；2,000 stationary 共 draw 块 20/60；三层同时带；Z-MEAN ≥ 2,000；Z-MAP；δ{0.10,0.25,0.50,1.00} 与 MDE；四种状态词；逐年 + LOYO 全路线） | 采纳 |
| §9 C1 N{100,150,250} × B{8,12,16} × q{.2,.3,.4,.5} × 64 seed × 两种分配 × R1/R2/A06；C2 成本透镜独立、Q/ADV20 日频压力代理；C3 `signal_margin_profile` | 采纳；C1 全交叉不缩（约 1.4 万配置，跑久没关系）；C1 的 2019+ 数值在 B 冻结前只算不读（封存） |
| §10 Q1–Q16 | **逐字进事前登记**（§12）；规划 session 另加 Q17–Q18 |
| §11.1 A1 规划复核 | **规划 session 的义务**：R0 交付后 ≤ 2 个工作日给 `routing_review_A1.md`（可为"reviewed; no change"）；执行端不等 A1 即跑全部 A0 账户；A1 增补单独版本、时间戳、信息暴露标注 |
| §11.5 任务状态 `PENDING/RUNNING/SUCCEEDED/FAILED_TECH/UNAVAILABLE_SOURCE/NOT_APPLICABLE` | 采纳；映射到协议：`FAILED_TECH → FAILED`，`UNAVAILABLE_SOURCE / NOT_APPLICABLE → LIMIT（带子类）`，计数之和 = 登记总数 |
| §12 交付目录 `results/<ts>_E6i_measurement_need_fit/` | 采纳；另加 `E6i_REVIEW_input.md`（数字与分母清单，供规划 session 复算） |
| 附录 B 61 项本地契约测试 | 在 47 用现有环境（Python 3.10.13 / numpy 1.26.1 / pandas 2.2.3 / scipy 1.11.3）复跑一次记录结果；不替代真实源锚与真实数据前缀测试 |

### 0.2 "设计尽量宽松，不要太严格"（用户 09-23）在本 brief 的落法

- **硬约束只六类**（违反即停并写 BLOCKERS）：① 取数 `end_date ≤ 20260327`，走 `guarded_load`，不读 E7；② **血缘守卫**：本轮所有新测量、新算子（SLOT / ADD_SCORE / VETO 新键 / 软缩减 / SWAP / FOCAL / RL 边缘替换）、M1 组合、M2 程序在 2019+ 上依赖收益、持仓、条件分布或选择结果的计算，只在记录 B 批准后按冻结清单运行；推导段 `label_end ≤ 2018-12-31`；C1 的 2019+ 产物算完封存、B 前不读；守卫覆盖缓存读取；③ 四地基、e6e / e6f / e6g / e6h 脚本不改（新代码 `e6i_*.py` + `e6i_vendor/`），`results/` 不删，不改 I11 / pool0 / clean / 生产 DEV / 生产 H5 / 8bp 主口径 / 生产 v2 / U34 / U35；④ 并发 ≤ 24 worker 且在实测线程 / 内存预算内（起步 12），父进程验收后写 DONE，状态表求和 = 登记总数；⑤ git 只 whitelist add，不 `git add .`，不混入旧 untracked；⑥ 文档不出现登录信息与主机地址。
- **plan 里其余的"不得 / 必须"一律改读为"报告并继续"**；MODULE STOP 只限符号 / 时间 / 域的逻辑错（未来函数、成本重复扣、账户资产凭空消失、有效域错、DEP 例外绕过另一关、SWAP/ADD 绕过源 veto、位置索引未按 ticker 对齐、随机对照改动了旧分量）；锚差报最大差 / 日期 / 原因记 WARN；某成员缺字段或作者算法核不清 → `UNAVAILABLE_SOURCE` 只隔离它及其依赖。
- **探索从宽的具体边界**：Stage 1 对全部数据可算、语义合格的成员跑；Stage 2 对 A0 全部路线 × 全部成员 × 全部登记参数格跑（含竞争方向、四臂、对照），**不按 Stage 1 任何 ρ / 单调 / 收益删成员**；后段只跑记录 B 冻结清单。负收益、IC 小、五分位不单调、四段不同号、C 族出现增量、同时带跨零、冲击下排名翻转、运行很长，都不是停止条件。
- **网格不缩、也不加严**：plan 打开的格全跑；执行端顺手可加的格作附加列登记，不进主表不替代主表；随机路径按 §0.1 优先级分配是**顺序**不是上限。
- **实施细节留给执行端**：模块划分、缓存、分片、并行顺序按 plan §11 建议不强制；"名称可适配，字段不可遗漏"。

---

## 1. 起点确认与契约

### 1.1 起点
- 47 HEAD `4b1ee8e`；untracked 只有三个 2026-05 `.py` 与七个 `chain*/wave*/autochain.sh`，不动、不 add。
- E6h 产出 `results/20260912_1147_E6h_need_driven_routing/`：`registry/`（`feature_semantics.csv` 87 键含 source_sign / economic_quantity / value_used_for_pct；`feature_taxonomy.csv`；`need_parent_role_map.csv` 348 对；`consideration_ledger.csv` 277；`alias_measurements.csv`；`route_manifest.json`）、`T0_full_distribution/`（三层与标签口径）、`registration/`（记录 A/B 模板与 receipt）、`checks/`、`route_results / paired_controls / random_registry / domain_selection / L / T / cost`。
- 可复用代码：`e6g_core`（guard / Lin / specF / agg_dense / keep_* / canon_veto / path_key）、`e6g_t0`（labels 源版 + 端点复利版）、`e6g_k`（iid_expect、同人数 core / 反向）、`e6g_l`（relaxed_domain）、`e6g_c`（`align_to_close`、冲击括号、`shadow_account`）、`e6h_core`（SLOT_FALLBACK / SLOT_REPLACE / FOCAL / ADD / SWAP / CONJ / MARGIN / 软降权与恒等锚）、`e6h_randoms`（U-IID / I-IID / I-P20）、`e6h_anchors`、`e6h_post_lgrid`（子对象可持有域 `Bmask(b)`）、`e6h_approve_B`（授权与封存）。
- 环境（本 brief 定稿日核）：Python 3.10.13 / numpy 1.26.1 / pandas 2.2.3 / scipy 1.11.3（`scipy.signal.savgol_coeffs(pos=, use='dot')` 可用）/ sklearn 1.3.1；`bidask` 未安装；GitHub raw 可达；384 逻辑核（taskset `96-191,288-383`）；`ulimit -u 4096`；内存充足。

### 1.2 数据与生产锁
沿 E6h brief §1.2。研究变体（全部新测量、`e6i_vendor` 实现、SLOT / ADD_SCORE / SWAP / RL / M1 / M2、H ≠ 5、b=10 桥、影子账户）一律独立命名，不进交付、不进公共库。

### 1.3 契约（规划 session 2026-09-23 已按 47 源码核；执行端整段读函数体复核并写 `engine_contract.md` + `source_resolution.md`，每条机制句三栏：定义处 / 调用处 / 默认值）
- **I11 信号**：`define_i11_signal(features, base_pool)`：三成分在基础池内当日 `rank(axis=1, pct=True)`，`cmf_pct ≥ 0.80 ∧ 0.25 ≤ cr5_pct ≤ 0.55 ∧ ir_pct < 0.70`（`pool_screening_v2.py:43–61`）；**不是收益阈值**。观察池 `build_observation_pool(signal, obs_window=5)`（调用处 `comprehensive_factor_diagnosis.py:788` 等）= `signal.shift(1..5)` → age ∈ {1,…,5}（函数默认 3 不生效）。Stage 1 首张表 = 池内真实 `cum_return_5d / o / c / (h−l)` 分布、事件日龄、触板天数（W01）。
- **三腿源定义**：K = `turnover_rate / (|log(close/lclose)| + 1e-4)`（`features_daily.py:353`）；T = `turn.rolling(60, min_periods=30).std()`（:605）；C = `((close−vwap)/vwap).rolling(20, min_periods=10).mean()`（:573）。核 = 三腿 pct-rank 等权均值或两段式 DEP（`e6e_core.py:51/357/424`）；R1 = `KT_dep(50,50)|C:k5`（R1 的 CVR 是**否决**不是 C 核心腿，plan §3.5）；R2 / A06 / A08 描述符从 E6h registry 读取。
- **自定义键符号**：`compute_parkinson_vol` = `−sqrt(rolling20 mean of (ln(H/L))²/(4 ln 2))`，`H==L → NaN`，`min_periods=14`（:190–199）= `LEGACY_PARK_NAN` 桥；`compute_abnormal_turnover` = `−(MA20/MA120)`；`compute_reversal_skip1` = `−(行业内去均值 skip-1 十日收益)`；`cmf_change_neg` = `−compute_cmf_change`。所有新测量 `source_sign = as_is`，方向在 role 层登记（plan §5.7 默认方向表），不写进测量函数。
- **数据字段**（`data_loader.py:104–168`）：open / close / high / low / lclose(=preClosePrice) / vwap / volume / amount(=turnoverValue) / turnover_rate(=turnoverRate，**无缩放，单位待 P0 核**) / mcap(=negMarketValue) / adj_factor / industry（`industry_zx1` 日频 PIT）；`load_limit_prices` 装 `limitUpPrice / limitDownPrice` 长表（:276–280）；`isOpen` 停牌。价格约定：`r = log(C/lclose)`、`o = log(O/lclose)`、`c = log(C/O)`、`h = log(H/O)`、`l = log(L/O)`，同日 `r = o + c`；同日 OHLC/VWAP 比值复权因子抵消；跨日路径用既有调整器同尺度价格；金额用原始元。
- **T0 三层画像主体**（E6h proposal 勘误；本轮每张 T0 表带 `subject_set / reference_set / label_definition / weights / dates`）：**被错剔的赢家**（核裁掉但 5 日为正）相对**被剔掉的输家**：换手水平与 T 更低、CVR 与累计收益更低、源 `abn / parkinson / reversal_skip1` 更高 = 换手相对自身更低、区间更窄、相对同业更负；不可写成"输家"画像（#42）。
- **派生量与估计量**（plan §4 逐字；此处只列锚与容易写错的）：`TCV_w = std_w/mean_w`（E6h 桥，ddof 沿源）；YZ `= var(o) + k_n var(c) + (1−k_n) RS`，`k_n = 0.34/[1.34 + (n+1)/(n−1)]`，n = 实际完整观测数，ddof=1；RS `= mean[h(h−c) + l(l−c)]`；GK-simple `= mean[½(h−l)² − (2ln2−1)c²]`；Parkinson `= mean((h−l)²)/(4 ln 2)`；Meilijson 四分量与系数按 plan §4.3；CS 两日 β/γ/α、`s = 2 tanh(α/2)`，主值 `mean(max(s,0))`、对照 `max(mean(s),0)`；AR `q_t = 4(logC_{t−1} − η_{t−1})(logC_{t−1} − η_t)`（t 收盘已知），窗口先均再开根；EDGE 用作者实现；Roll `q = −cov(ΔlogC_t, ΔlogC_{t−1})`；零收益占比不称 LOT。事件钟：`τ` = 截至 t 最近已知触发；`event_level = mean_{τ:t}(x)/mean_{preτ,20}(x)`；峰只取 `[τ,t]`。标签时钟：entry-fixed `VWAP(t+1+H)/VWAP(t+1) − 1` 与日龄线性归因 `Σ_{j=1..H}[VWAP(t+1+j)/VWAP(t+j) − 1]` 分名；E6h R0 源标签属哪种由 P0 读函数确认并保留精确旧桥。
- **账本口径**：沿 E6h `engine_contract.md`（DEV `min(1/n, 0.01)` + 行业 cap 等比缩减不归一；`gross = port − bench × position`；`turnover = 0.5Σ|Δah|`；`net8 = gross − 8e−4·turn` 单边基数；net12 另列；冲击独立扣）。
- **守卫**：`Lin` 血缘沿 DAG 最严格父；对象带 `max_feature_date / label_end_date / source_lineage / exposure_status / approval_id`；攻击测试沿 E6h 20 项 + 新增：新测量缓存绕守卫、M2 训练集含未成熟标签、C1 后段产物 B 前被读、随机对照改动旧分量、SLOT α=0 读新有效域。

### 1.4 事前登记
首次新收益评价前落盘 `preregistration.md` = 本 brief §12 全文（plan §10 Q1–Q16 逐字 + 规划补充 Q17–Q18 + 读法优先级 + 边界）+ `hypotheses_A0.json` + 实际时间 + 输入 / 代码哈希 + 源 ID 映射；修订另起 `preregistration_amend_<日期>.md`。**不改写编号与问题。**

---

## 2. P0 起点 + Stage 0 仪器（不改任何数字口径）
- 读 `PROJECT_STATUS.md`、`00_协议.md`、memory 入口、E6h 四份 REPORT + REVIEW、`E6i_proposal.md`（含勘误）、plan v1.0；冻结四地基 + e6e/e6f/e6g/e6h 脚本 SHA 与运行库版本；`source_manifest`；HEAD / dirty / untracked。
- `source_resolution.md`：I11 分位定义、`turnover_rate` 单位与分母、`amount` 单位、复权路径、`limitUp/Down` 覆盖、`isOpen`、行业 PIT、E6h R0 标签属哪种时钟、`turnover_ff` 是否可得（不可得则不造）。任何 source-only 修订写明并保留 plan 原文。
- `feature_semantics_v2.csv` / `estimator_families.csv` / `mothers.csv` / `mother_needs.csv`：plan §3.1 字段全（`axis_id … executable_status`），每成员来源标签 `[L]/[E]/[P]/[M]`，一字板政策 `OBS / LIMIT_SENS / LEGACY_PARK_NAN`，事件钟版本。
- 研究模块 `e6i_features.py`（+ `e6i_vendor/`）：全部成员在股票完整允许历史上计算再取当日 pool0；窗口按交易日网格（停牌不压缩）；前缀不变测试同时扰动未来价 / 量 / 行业 / 触发 / 缓存（每个支持日期 suffix 切断或随机扰动）。
- **恒等锚（阻断）**：`V_park_20_LEGACY` = `−compute_parkinson_vol`；`T_std60` = `turnover_volatility_60d`；`TCV_20` = E6h 值；`V_cc_20·√252` = `realized_vol_20d`（先核 simple/log、复权、ddof）；`K0` = `conditional_turnover`；`K_MA3 / K_ROS` = E6f 函数；`CVR_20` = 源；SLOT α=0 = 源父逐位（短路，不读新有效域）；ADD_SCORE γ=0 / SWAP q=0 / λ=0 / RL 全关 = 原 B；同 m 核心对照在目标人数 = 原人数时精确复现原名单；E6h 22 条源账户 + 六类算子锚 48 + `Bmask(b=0)` 62 逐位复现。容差：代数等价路径 `atol 1e−12 / rtol 1e−10`，另报 max 绝对 / 相对误差与受影响排序格数；源 brief 更严者沿用，不得事后放宽。
- **ADEMP 仿真**（plan §11.3；先写目标 / DGP / 估计对象 / 方法 / 指标再跑）：价格面板（日志漂移 {−1%,−.5%,0,.5%,1%} × 日内 σ{20%,40%,80%} × 隔夜 σ 比 {0,.5,1} × 离散 tick / 限价 / 稀疏 / 停牌；≥2,000 路径 × 250 日，日内 390 步与 1,560 步收敛诊断；MCSE 不稳升 8,000）；活动面板；价差面板（存 signed 与截零）；信息 / 策略反例面板（已知零增量、零 ρ 但 U 形有用、条件于边缘有用、只改缺失 / 仓位 / 成本）。**仿真结果是误差表不是 PASS 门**；Meilijson 非零漂移格标 mis-specification 不算 FAIL。
- 复跑 plan 附录 B 61 项契约测试并记录；守卫攻击测试；`checks/` 落证据。
- 并发：先设 BLAS/OMP 线程 ≤ 4 再实测每 worker 总线程 / RSS，起步 12，≤ 24；随机路径只存汇总 + 8 条示例日账本；父进程验收；`os._exit(0)` 只作受控恢复。

## 3. A0 登记（执行端编译；不等收益）
- `need_estimator_role_map.csv`（plan §5.1 字段）从 plan §5.1 九条路线 + §5.7 生成器合同 + §7.1 固定代表 编译为机器可枚举的 member / role / grid 列表；`hypotheses_A0.json` = §12；`manifest_A0.json` 带 SHA；计数按 **轴 / 估计对象 / 母体 / 角色 / H / 支持政策 / 方向** 列出（共享计算只减实际计算量，不减披露的已试假设）；缺槽位母体标 `NOT_APPLICABLE`（R1/R2 无 C 核心槽位；只有真含该腿的母体有 K/T 槽位）。
- 方向默认表（plan §5.7）：T 尺度 / 水平继承原 T 低值为主 + 反向对照；K 吸收延用原 K 低值方向 + 高值竞争，倒数响应反向映射；V 范围 / 尾风险低值保护 + 反方向；R 低值 / 高值按"反转 / 延续"分域；O 均值 / 份额 / 方差不共享方向，高低两角色都登记；C 高位置为坏是主假设 + 反向另域；A 高低竞争都保留；S 只按 §4.8 状态作用。**方向是描述符，不能按 Stage 1 最大 ρ 改写。**

## 4. Stage 1：测量级诊断（新对象只用 2010-14 / 2015-18；旧母体四段锚可复现）
- 首表（W01）：pool0 内 `cum_return_5d`（复权与未复权两版）、`o / c / (h−l)`、触板天数、事件 age 的全分布与逐年；这是 V / O 族"适配"读法的依据。
- 六集合 × 四层（plan §6.1）：集合 = pool0 / 进入焦点前 / 核心保留 / 最终保留 / 经济拒绝 / 决策边缘；层 = 测量（单位、覆盖、平局、极端值、前缀不变、同族相关、rank 稳定、有效窗龄、中性化前后形态）/ 预测（形成日 Spearman、3/5 分组均值与全分布、分位尾部、P(y<0)、均值效应与风险效应）/ 决策（同预算换入 − 换出、进入真实 DEV 的毛与成本）/ 事件（age0–4、首入 spell、重复触发；H1/3/5/10/20 支持曲线）。**五个分组均值的相关不作单调性检验**（[R24]）。
- T0 三层用新成员重做画像（主体逐字：被错剔赢家 − 被剔输家；同人数反向与随机对照列）；被剔输家 / 被错剔赢家的**新测量**分布按真实漂移 / 涨跌停桶分层。
- `signal_margin_profile`（C3）：固定 pool0 内按 CMF / cr5 / intraday 分位距边界的距离、真实收益、事件 age 报后续收益分布；不重建信号。
- 交付 `E6i_REPORT_R0.md`（测量 / 边缘 / 事件 / 成本暴露表 + coverage）给规划 session。

## 5. A1 规划复核（规划 session；≤ 2 个工作日；执行端不等待）
- 规划 session 读 R0 与原始动机，写 `routing_review_A1.md`：可为"A1 reviewed; no change"；有增补则单独版本 / 时间戳 / 理由 / 信息暴露标注（"推导数据启发"，不追认为 A0 预测）；**不按 Stage 1 ρ 或收益删任何 A0 路线**。执行端并行跑全部 A0 账户；A1 增补只增量补跑。

## 6. Stage 2：推导段角色账户（plan §5–§7 全文执行）
- 角色：SLOT（K/T/C 槽位；α 网格；FULL_REPLACE 与 FALLBACK_REPLACE 分名；COMMON_SUPPORT 诊断）；ADD_SCORE γ；VETO k{5,10} + 反向对照恰删同 m；软缩减 λ{.25,.5,1} 不再分配资本 + 硬删重 DEV 另列；SWAP q{.05,.10,.20}（换出 = 母体排序最差 m 个最终保留成员；K 路线另有"最高 K 的 m 个"分别登记；换入按新测量从事前状态的 E 取；m=0 返回母体；保留集内部只重排不改名单 = 精确 no-op）；FOCAL 四对照（先关原焦点）；RL 边缘替换（保留最好 80%，合并边缘域按成本测量选同人数；无 continuation ordering 标不适用）。
- 母体 R1 / R2 / A06 / A08；H{3,5,10,20}（+ 快端 {1,2} 对 RO/RC 瞬时分量与 RK 当日响应）；每 H 同时给相对同 H 母体的结构增量与相对生产 H5 的完整增量，不合并。成本 net8 主、net12 另列、冲击情景独立（§10）。
- 四臂（plan §5.6/§5.7 中心固定）：T mean20 × CV20；K log 条件活动残差 × 因果 event_level（α .25/.5；单变量 M2 与双变量 M2 含一阶交互）；R REL_IND20 × S peerR20 正 / 负状态（q=.10）；V RS20 × O ONmean5（总新分量 γ=.125，单项 .0625）；报 `Δ_AB − Δ_A − Δ_B` 逐日配对。
- **对照（每角色匹配自己的改变，plan §6.3）**：SLOT/REPLACE 只置换新分量的当日横截面归属（保留旧分量、源构造、新分量 mask；行业 / 规模层内版并列）；VETO 同日同 m 随机删 / 同 m 原核心剔深 / 同 m 反向；SWAP 固定真实 D、从相同候选域随机取 m 个 A / 同行业人数匹配 / 反向新排序；FOCAL 全开 / 全关 / 真实 / 随机状态；成本边缘替换同 m 同域相近旧分数；家族组合固定资本份额合并目标权重后重算实际交易。**不重新随机抽整个母体名单。** 同 m 核心对照用冻结 continuation ordering，目标人数 = 原人数时精确复现原名单；无延伸排序则 `restricted_comparator`。
- 随机路径：种类 = 同日基础匹配、行业匹配、股票 × 注册块稳定哈希的 20 日持续性对照；数量按 §0.1 优先级；共用配对 draw，各自过 DEV / 持仓 / 成本，**先运行再平均收益**；每日随机与持续性随机的 gross / turn / net 并列；放松匹配的顺序与剩余失配记录。
- 归因（plan §6.5）：`Δgross_t = Σ_i (w_child − w_parent)(r − b)`（用源引擎实际计收益时点的持仓）拆进入 / 退出 / 共同成员权重变化三项逐日精确相加；`Δnet8 = Δgross − 8e−4·Δturn`；同资本对照只向下缩到共同可投资本后完整重跑；未知收益不 `nanmean` 成满权重。
- M0 固定代表与完整邻域相对母体的分布；M1 同估计对象 / 同方向 / 同 role 内先估计形式等权再窗等权 + 父权重 η{.25,.5,1} + 成员账户等资本合并版；M2（`part1b`）按 plan §7.3 契约：日期等权加权平方误差 + L2，训练只用已成熟形成日，basis 冻结中心化，λ{0.1,1,10}（平均损失口径），2012 起年度向前回放、≥252 成熟日否则回退母体、purge 按标签结束时间、内层 = 外层最后两个完整年度逐年向前、λ 并列取大、零修改与修改并列取零修改；输出转 bad-score 后沿该域已登记预算接入；每次新模型只控后续新批次；M2 学习不确定性在推导段做 256 次时间块重采样（只对预登记代表）。
- 交付 `E6i_REPORT_part1.md`（1a：M0 / M1 全部账户、对照、四臂、随机、归因、coverage、`consideration_ledger`；1b：M2）+ `E6i_record_B_draft.md`。

## 7. 记录 B：用户授权（part1 之后）
- 草稿按**需求域包**组织（不是 ≤12 单格）：包内列全部成员、强度、期限、对照、M2 更新程序、方向 / 状态、读法优先级（策略问题 vs 机制问题）、Z-MEAN / Z-MAP 零期望、源 SHA；用户可批准整个清单或明确子集（不强制逐行）；允许"没有一项值得推进"的空建议；考虑过未进后段的项留理由。
- 执行端核 SHA 后打开守卫，两后段（2019-23、2024-03-27 止）同一 manifest 全部计算并封存，receipt 后共同展示；**不看 2019-23 后改 2024-26**；后段技术修复保持经济定义并记 hash；自适应程序（M2）的年度更新按 B 冻结规则用当时已成熟历史执行并留日志，不解封其他新成员。
- 闸期间执行端不空等：C1 / C2 只用旧输入的格可先算后段并封存（B 前不读）；新测量血缘的一切只跑推导段。

## 8. Stage 3：后段首次观察（记录 B 之后）
- 所有冻结路径在两后段 + 四段合并：对真实母体（策略主读数）、同人数核心 / 同资本 / 随机机制（机制主读数）、vs R1@H5 / R2@H5；M0 / M1 / M2 账户；逐年、LOYO（至少单列 2015 / 2016 / 2020 / 2024+）、去 15+16；三层同时带（need-domain / 轴 / 全 headline）；δ 尺度与 MDE；状态词四选（`positive_estimate_uncertain / negative_estimate_uncertain / materially_small_under_declared_delta / inconclusive`）。
- **P20 / P21 复核按各自原登记主读数回答旧问题**（P20 = 同人数核心；P21 = 匹配随机），再另标新问题。
- 结论格式：`在哪个母体 / 需求 / 角色 / 日期 / 支持 / 成本下，点估多少、不确定性多少、相对什么、哪部分可解释、哪些解释未排除`；不作淘汰标签。
- 交付 `E6i_REPORT_part2.md` + `first_look_receipts`。

## 9. Stage 4：合并复盘
- Q1–Q18 结果卡（plan §10.2 模板：`prediction_status ∈ {aligned, opposed, mixed, underidentified, untested}`；`root_cause_evidence` 可多选含 unknown；`what_was_not_tested / what_cannot_be_concluded / next_design_change`）→ `hypothesis_outcomes.md`。
- `factor_iteration_delta.md`：每成员一行（构造版本 / 角色证据 / 失效归因五选并给证据 / 状态），供规划 session 更新因子迭代台账。
- `research_catalog_v36.csv`（每个已考虑成员的来源 / 定义 / 有效域 / 尝试 / 未测用途；不只存通过者）与 `candidate_library_update_proposal.md`（可空；每项写改善对象 / 母体 / 角色 / H·成本 / 增益来源 / 时间与风险范围 / 剩余不确定性 / 所需后续验证；同对象多支说明为何保留与如何避免重复加权）。**U34/U35、生产 v2、v3 展示候选本轮不改；入地基由用户另定。**
- 交付 `E6i_REPORT_part3.md`（后段合并 + carried + 全轮 coverage）+ `line_state_proposal.md` / `park_ledger_delta.md`（草稿，定案权在规划 session 与用户）。

## 10. carried（plan §9 全文执行）
- **C1**：N{100,150,250} × B{8,12,16} × q{.20,.30,.40,.50} × 64 共同哈希 seed × 行业内分配 {容量受限近似等人数, 容量受限原始比例} × R1/R2/A06；行业子集先选、股票按行业内固定优先级选；跨 N 嵌套、跨深度共用可选域；桥 = 原始完整 pool0 / 按原核心分数 top-N 截断 / 随机 N 截断；评分 scope 分开（完整 pool0 冻结中性化排名 vs 采样域重做）；严格交叉主表用同日共同可行支持，另报 `min(N, N_t)` 部署视图；行业容量不足标 infeasible 不重抽；报名义 B / B_eff / HHI / size / 活动分布 / DEV 仓位 / 分箱失败 / 真实持股；计数预算用已验证研究适配器，与源分箱差异单列"仪器效应"；逐年偏相关 / 回归作附图，不点名唯一机制。2019+ 产物算完封存、B 前不读。
- **C2**：net8 主、net12 解析；含冲击用已核验源模型（sigma / ADV / 执行时钟不变；新 V / EDGE 不替换成本模型）；A{1,5,10} 亿 × κ{.25,.5,1} 平方根，线性模型单独表；`Q = A|Δw|`，ADV 只用执行日前历史成交额，`Q/ADV20` 日频压力代理（不是 POV）；组合净交易与分成员独立账户各跑；容量零点只在 `a/b > 0 ∧ b ≠ 0` 求，否则报无正根；κ 未校准不输出可部署规模。
- **C3**：`signal_margin_profile`（§4）；不做阈值敏感面，不重建信号。

## 11. 统计与账本（plan §8 全文执行）
逐日 gross / position / turn / net8 / net12 与成本列；年化 = 共同有效日均值 × 252 × 100；配置间、seed 间、日期间三种分布分标；NW 主 lag = H，另 lag = max(2H, 20) 与源 lag5 桥；缺测日用完整交易日网格的掩码估计，不拼相邻；主事件统计先聚合到形成日级；2,000 次共同 stationary bootstrap（块 20 与 60 分开；段内重采样；full 按有效日权重合并且每次 draw 重算分母）；三层同时带用中心化 `t*` 的 max-|t*| 95% 分位，零 SE 同义单列，不 `nanmax`；Z-MEAN ≥ 2,000 draw（去均值条件模型）与 Z-MAP（局部无信息映射）分名，tail fraction 含原样本计数并报 MCSE，可交换性无据时标 `diagnostic_tail_fraction`；δ{0.10,0.25,0.50,1.00} 覆盖与 MDE `(critical + 0.84)×SE`，不用事后点估反算功效；逐年 + LOYO 全部主路线；重加权诊断只在共同支持内。所有汇总量标算子与 n；均值与中位并报；全称句只来自计数。

---

## 12. 事前登记（执行端逐字落盘为 `preregistration.md`；只补时间、哈希、源 ID 映射）

**plan §10 原文（Q1–Q16；四列逐字）**

| Q | 动机、问题与竞争解释 | 预定实验／主读法 | 允许的结论与禁止的跳跃 |
|---|---|---|---|
| Q1 T | 部分混入曾正，完全替换多负；水平可能是信息而非污染。相对尺度、趋势、事件前基线是否提供不同价值？ | RT按母体；共同支持T分解→SLOT曲线→sameN与实际mother差→年份/H | 支持某个测量配比或母体用途；不由CV相关降低宣布测量更好 |
| Q2 K | 奇点、单位和聚合不同。收益来自价平、换手水平、条件吸收还是中性化表示？ | RK分量／点态倒数／ROS／残差；同slot完整账户 | 比值效果与分量效果分开；logK的raw rank不变不算新信息 |
| Q3 V | I11不保证强漂移；不同估计量目标不同。风险分离是否经共同支持和限制分层保留？ | 同一V定义下真实漂移／range／限制桶→收益与风险形状→RV | 仿真优不推出alpha优；Park画像变弱不自动等于“假象已证实” |
| Q4 O | 旧高跳空否决负可能含正gap信息，也可能是估计与角色问题 | 保留集ON方向／份额／方差分离→RO双机制→费用与期限 | 正向用途需自己验证；不能由坏否决推导“高跳空必买” |
| Q5 R | ADD负而部分random差正；问题可能在边缘替代与同业状态 | RR同人数SWAP对母体为实用主读数；matched replacement为机制主读数；H3/5/10/20 | 两个主读数不同向时保留两句结论；不随结果切基准 |
| Q6 C | 几种替代失败不能定义整个C族为零 | RC核心／焦点分开，更长／加权／持续性；mother与覆盖桥 | C为真实未知候选；有增量不触发“所有方法假阳性” |
| Q7 摩擦 | 交易代理可能主要改变成本，不改变gross；不同价差对象不可混同 | RL以独立源成本net与gross拆分；AR/CS/EDGE分开；A、κ视图 | 只成本改善可作为实施机会；不能称信息alpha或真实容量 |
| Q8 家族 | 不能靠最大格，也不能因top难分就否定域 | M0、M1、M2各自账户相对同一母体；forms/windows先分层后聚合 | 固定族整体可有价值而无需冠军；effective-rank不作检验分母 |
| Q9 后段 | 测量／母体／时间关系可能漂移，低功效不等于零 | 冻结B相同两段；actualmother、sameN、LOYO、区间与δ尺度 | 可以负、弱、异质、不可分辨；不要求两段同号才能留作研究资产 |
| Q10 C1 | 人数与行业宽度同向变，旧截断没分离 | N×B共同支持交叉、冻结score与重估score分开 | 算法域敏感性可识别；偏相关不能独立证明历史成因 |
| Q11 D-S | 先确认信号真实状态，而非假定涨幅25%–55% | 固定pool0的分位边界距离／实际收益／age描述 | 可提出新需求；不推导未运行的新信号绩效 |
| Q12 缺失/限制 | H=L零观测、NA与限价可能改变样本与排序 | OBS、LIMIT_SENS、LEGACY桥；共同支持、原生覆盖与资本变化 | 数值差可定位；不能把机械影响一概视为无用信息 |
| Q13 A | 旧量比统一条件失败，可能混合延续/反转及事件时钟 | RA因果事件基线、峰衰减、K×A四臂；同预算名单 | 仅该测量/角色/域被削弱；无预测力也是允许答案 |
| Q14 S | 同行业强弱与落后角色相关；全球同一状态不能横截面排序 | RS分同行强/弱、宽/窄和连续状态；R主效应对照 | 条件用途而非全局regime；不把行业均值当真实板块共振发现 |
| Q15 互补 | 单项弱可能组合有用，也可能只是重复资本调整 | §5.6四臂完整账户＋interaction差＋sameN | 交互只对登记对象成立；不能推广为所有同族因子有效 |
| Q16 方法复盘 | 原失误跨事实、估计对象、基准、筛法与文档 | 每Q回链motivation、actualtest、interpretation、unresolved、nextchange | 不能把失败仅写“样本噪声”或“研究饱和”；也不保证总能找到新解释 |

**规划 session 补充**
Q17 条件形状：八族成员在四母体拒绝集 / 保留集的 3/5 分组条件形状（含 U 形、单边）与单调 Spearman 是否不一致？读法 = Stage 1 分组均值与全分布 + M2 basis（u、u²、u·z）拟合的训练内形状；备择 = (i) 单调且弱 (ii) 非单调可用 (iii) 无形状；允许结论只到"该成员 × 集合 × 段"，不推及轴。
Q18 画像复核：用新测量（RS / YZ / 分量 / T 分解 / K 分量）重做"被错剔赢家 − 被剔输家"画像并按真实漂移与触板天数分层，与 Parkinson / std60 / K0 的旧画像相比是否保持、减弱或反向？读法 = 主体逐字的 pct 差 + 分层表 + 同人数反向对照；备择 = 保持 / 减弱（旧画像含机械成分）/ 反向；不由此推收益。

**读法优先级（plan §10.1）**：策略问题 = 对真实母体的同成本同 H 增量 → 实际 gross / cost / 仓位 → sameN / 同资本 / 随机机制 → 年份与区间（相对生产 H5 另列）；测量问题 = 明确 estimand 与有效支持 → 技术 / 仿真检验 → 目标集合条件形状 → 角色账户；旧 P20 / P21 按原登记主读数答旧问题；否定与 park 只对实际跑过的 成员 × 角色 × 母体 × 时期 × 口径，未测 / 不可计算 / 负点估 / 无实质差异为不同状态。

**边界全文**：所有截至 2026-03-27 的历史此前用于研究；推导段结果属研究历史不叫未污染 OOS；后段是首次观察但研究者知道 regime，不是未触碰样本；E7 是唯一 OOS。统计量、成本翻转、局部弱段、MCSE、风险画像用于读表，不作自动淘汰门；未路由 / 未测不等于无效；每句"无效果"写母体 × 需求 × 角色 × 日期 × 支持 × 成本；线状态、v3、候选库更新、入地基由用户定；E7 HOLD。

---

## 13. 自测与验收（只对正确性设硬条件）
- GLOBAL STOP：E7 数据进入计算；受保护对象（新测量 / 新算子 / M1 / M2 / C1 后段产物）越界到 2019+ 或 B 前被读；源码 / 冻结数据意外变化；进程配额不足且无法降并发；服务器安全问题。MODULE STOP：§0.2 所列逻辑错。WARN / LIMIT：锚差可解释、注册表计数不符、行业 PIT 缺口、字段缺失、SE 退化、恒等式不过的小块、作者算法核不清（`UNAVAILABLE_SOURCE`）→ 保留主结果、缺失列 NA、禁止有利插补。合法研究结果：净值下降、某段负、区间跨零、随机参照不显著、某 κ 翻转、C 族有增量、五分位不单调、四段不同号 → 全部留表。
- 真实源必核：R1/R2/A06/A08 固定目标与日账本；α0 / γ0 / q0 / λ0 / RL 全关 identity；焦点全开 / 全关；T0 原标签与两种时钟桥；同 m 核心对照精确复现原名单；PIT 行业与限价标志按列名对齐；每条账的净费用恒等式；新增反例（新测量缓存绕守卫；M2 训练含未成熟标签；C1 后段产物 B 前被读；随机对照改动旧分量；SLOT α=0 读新有效域；一字板三政策混名；事件峰用未来；SG 居中窗；AR 用 t+1 中点；`turnover_ff` 无自由流通股本却被造出）。
- 完成定义：每登记单元 ∈ {PENDING, RUNNING, SUCCEEDED, FAILED（含 FAILED_TECH）, LIMIT（子类 UNAVAILABLE_SOURCE / NOT_APPLICABLE / RESTRICTED）, SUPERSEDED}，计数之和 = 登记总数；完成 = 退出码 + schema / 行数 / 日期检查 + hash + 原子写 receipt（不只 `_DONE`）；断点恢复以内容 hash 与完整产物为准；核心模块未跑标 `COMPLETE_WITH_LIMITS`。

## 14. 运行组织（五次交付 + 两次登记 + 一次规划复核）
`P0 + Stage 0 → A0 → Stage 1 → REPORT_R0（给规划 session）→ A1（规划 ≤2 工作日，执行端并行跑 A0）→ Stage 2 → REPORT_part1（1a M0/M1；1b M2）+ B 草稿 → 记录 B（用户）→ Stage 3 → REPORT_part2 → Stage 4 → REPORT_part3 + coverage`。part1 / part2 不是等用户 GO；part1 后不得按收益改网格；用户中途改方向则保存原登记并做 amendment。
- 问题与交付映射：R0 答 Q3 首表 / Q11 / Q12 的测量部分与 Q17 / Q18 的 Stage 1 部分；part1 答 Q1–Q8、Q13–Q15 的推导段部分；part2 答 Q9 与 Q1–Q8 的后段部分；part3 答 Q10、Q7 冲击视图、Q16 与全部结果卡。
- 计时：先跑短 / 长历史段 × 便宜 / 昂贵估计量的代表任务，报每类耗时、峰值内存、输出大小、总 wall 区间，再估全部；>30 分钟阶段报预计；**慢不是问题**，分批交付不削；C1 约 1.4 万配置与随机路径按 §0.1 优先级排队。
- 并发：起步 12 worker、每 worker BLAS/OMP ≤ 4 线程，实测总线程（≤ 3,000）/ RSS / 句柄 / 磁盘后可升，**≤ 24**；绑定已批准 cpuset；给总线程 / 内存 / 磁盘留 ≥ 25% 余量；不触碰同事任务。
- 存储：日账本分块 float64 parquet；随机路径汇总 + 8 示例 + seed / 配额 / hash 可重建；特征按族缓存一次；写前估容量。

## 15. 交回
- `results/<ts>_E6i_measurement_need_fit/`：plan §12.1 目录全部 + `E6i_REVIEW_input.md`（每张主表的数字 / 算子 / 分母 / 基准 / 子集清单）+ `engine_contract.md` + `preregistration.md`。
- `exec_briefs/E6i_REPORT_R0.md`、`_part1.md`（可分 1a/1b）、`_part2.md`、`_part3.md`：协议结构；每份 ≤15 行纯文本摘要 + "没有得出的结论"节；Q1–Q18 每问：原问题 → 数字 / 分母 → 竞争解释 → 仍未知 → 下一步含义；**每张表首行四项：汇总算子 / 分母及构成 / 基准 / 子集**（另附单位、日期支持、H、成本模型、支持口径、资本口径；表头缺项 = 生成 FAIL）；正文"全部 / 没有 / 唯一 / 四段同号 / 中位 / 最好"句由表计算带 query_id；**不写"可交付 / 已确证 / 必须换核 / 饱和 / 穷尽 / 到平台"**；part3 末尾附全轮 coverage（逐条映射 proposal、plan、本 brief：`done / reused / changed / deferred / unavailable` + 理由与影响）。
- WORKLOG 远端 + 本地同文（只记操作事实；不含账号路径）；git whitelist add：`e6i_*.py`、`e6i_vendor/`（含 commit SHA 记录文件）、本 brief、`source_corrections_E6i.md`、四份 REPORT；e6e / e6f / e6g / e6h 不改不重 add；三个 2026-05 `.py` 与七个 `.sh` 不 add；`git push origin main`；交接指纹在最后一次改动后计算。

## 16. 禁区
不读 2026-03-27 之后数据、不开 E7；受保护对象不进 2019+ 直至记录 B；C1 后段产物 B 前不读；不改 I11 / pool0 / clean / 生产 DEV / 生产 H5 / 8bp / v2 / U34 / U35 / `features_daily.py`；研究变体不升格生产；不把首次观察读成 OOS；不把"无效果"写成线级"穷尽 / 到平台 / 饱和"；不把未路由 / 未测写成无效；不以卡数、描述符数或审计通过数当改善；不因慢减配置；不按 Stage 1 任何统计量删成员或改方向；不用 `pip install` 未审阅脚本；不用 `git add .`；不出现登录信息与主机地址。凡遇"必须改上述任何一项才能继续" → 停，写 BLOCKERS。

## 17. 自审记录（规划 session 2026-09-23；执行端见此段方可开工）
| 类 | 不利因素 | 处置 |
|---|---|---|
| 事实 | ★ proposal 把 I11 阈值当成 +25–55% 涨幅并据此写"强漂移 → RS/YZ 适配"先验（#43，根因 C：没重读 `define_i11_signal`，handoff 03 第 23 行早写了 P25/P55） | §0.1 承认；proposal 顶部勘误；Stage 1 首表实测漂移 / 跳空 / 触板分布；估计量全保留、不预设赢家 |
| 事实 | proposal 指纹与 plan 记录不符（勘误块加后） | WARN，两个哈希进 manifest |
| 事实 | T0 画像主体（#42） | 每张 T0 表带主体四元组；本 brief §1.3 逐字 |
| 代码 | 约 80+ 新测量、5 类新算子、M2 程序、vendor 实现 | 恒等锚逐位阻断；ADEMP 仿真误差表；61 项契约测试复跑；前缀不变多维扰动；EDGE 固定 commit 审阅后 vendor；Meilijson 系数对原文复核 |
| 代码 | 单位（换手率百分数 vs 比例、金额元、ε 相对尺度）与分母口径 | P0 `source_resolution.md` 先核后写语义表；不造 `turnover_ff` |
| 代码 | 一字板 / 限价 / 停牌 | OBS / LIMIT_SENS / LEGACY_PARK_NAN 三政策分名；PIT 限价标志；UNKNOWN 单列 |
| 代码 | 前视（事件掩码、峰、SG、AR 中点、行业、M2 标签成熟） | 因果版为主；suffix 攻击测试覆盖每个支持日期 |
| 代码 | 线程上限 4,096（E6h 峰值 2,663） | BLAS/OMP ≤ 4；起步 12、≤ 24；实测总线程 |
| 统计 | 族多重性与赢家诅咒 | 三层同时带；Z-MEAN / Z-MAP 分名；M0 全邻域分布；M1 固定预算；不选冠军 |
| 统计 | 后段功效低、2019+ regime 已知 | δ 尺度与 MDE；四种状态词；LOYO 全路线；边界全文；不用事后点估算功效 |
| 统计 | 随机对照破坏旧 alpha / 少算成本 | 只打乱新分量或改变名额；独立路径实际运行；持续性版本 |
| 统计 | sameN 更显著替代策略目标 | 双主读数按问题指定；P20/P21 按原登记 |
| 统计 | M2 训练内选择偏差 | 成熟标签、内层向前、年度批次、选择程序进评估、零修改参赛、后段真实账本 |
| 统计 | C1 抽样实验被读成历史因果 | 识别边界写明；偏相关作附图 |
| 运行 | 计算量（Stage 2 参数展开 + 随机路径 + C1 1.4 万配置 + 2,000 bootstrap） | 先精确计数与计时样本；分批交付；随机路径按优先级；慢不是问题 |
| 运行 | 存储 | 汇总 + 示例；按族缓存；写前估容量 |
| 解读 | 口径未标（#38–#40） | 表头四项硬约束；正文句带 query_id |
| 解读 | 首次观察读成 OOS；"无效果"写成线级 | 边界全文；结论模板；结果卡 |
| 解读 | 仿真 PASS 当策略证据；估计量效率当 alpha | plan W07；三层目标分开 |
| 流程 | A1 规划复核（E6h 缺） | §5 规划义务，可为"no change"；执行端不等待 |
| 流程 | 记录 B 一次性批准 | 按需求域包组织；可批整表或子集 |
| 宽松 | plan 的过程性"不得"被当阻断 | §0.2 六类硬约束外报告并继续；`UNAVAILABLE_SOURCE` 只隔离 |
| 节奏 | 有没有把跑得快当约束 | 没有：八轴全部成员 Stage 1 + A0 全路线 × 全格 Stage 2 + 四臂 + M0/M1/M2 + 随机 64/256→1024 + C1 全交叉 + bootstrap 2,000 + Z-MEAN 2,000 + ADEMP 2,000→8,000 路径；随机路径的优先级只是顺序 |

方向确认：headline = 因子端迭代（八轴估计量族按母体需求路由；测量级诊断 → 角色账户 → 一次用户授权 → 后段首次观察；研究目录与候选库更新提案分开、由用户定）；carried = C1（人数 × 行业宽度交叉）、C2（成本透镜独立）、C3（信号边界描述）；不改池、不改信号、不改地基、不改生产、不开 E7；探索从宽（八轴全跑、无统计闸、方向不按结果改）、采纳只在 E7 + 用户过目；五份 REPORT 交用户与规划 session；判读由规划 session 写 REVIEW（含因子端归因八项）、更新线状态 / park 台账 / 因子迭代台账并续写复盘台账。
