# E6h —— 最终 brief（v1，2026-09-11）：母体需求驱动的信息路由、推导段实验、一次用户登记、后段首次观察；carried = 期限 / 缓冲 / 实施（L）与时间异质 / 人数预算 / P16（T）

用途：本文件是 E6h 唯一有效的执行文件。设计层最终版是 web plan `exec_briefs/E6h_plan_web_final.md` v2.0（本地 SHA256 `1eff57b67965a11d876caa073fd2c6f3b968fc27d92635c15a389c55c55cb67c`，1,132 行），执行端整份读并复制进 results 作 `PLAN_COPY.md`；**本 brief 未提到的细节按 plan 执行，两者冲突以本 brief 为准**。输入指纹：`E6h_proposal.md` SHA256 `93c698ea…ded42af`（plan 附录 C 记的是加勘误块之前的版本；勘误块见 proposal 顶部，内容无丢失，记 WARN 不阻断）；`E6g_REVIEW.md` `ef36aa7f…d15dd`（与 plan 一致）。前置：E6g 三份 REPORT、`E6g_REVIEW.md`、47 `results/20260911_1140_E6g_structure_layer/`（HEAD `463575d`）。先读 `00_协议.md`。

---

## 0. 一句话问题与设计结论

**问题**：现有母体（R1 / R2 / A06 / A08）的损益与名单变化暴露了哪些决策问题；哪些测量类别对应这些问题、应进入哪个环节（核位替代、经济拒绝集的例外加回 / 换入、焦点否决的条件开关、保留集的风险否决、边缘流动性替代）；接入后完整策略相对直接母体与 R1/R2 是否更好、改善来自哪里；固定代表 / 层级等权组合 / 局部收缩选择各能保留多少。carried 两块回答期限 / 缓冲 / 受限库存 / 成本，以及时间异质、绝对人数与 P16 角落。

**设计结论**：按 plan v2.0 的任务图执行 `起点与 R0 → 路线冻结（记录 A，规划 session）→ 推导段实验 → REPORT_part1 → 一次用户登记（记录 B）→ 两后段同版本运行 → REPORT_part2 → L / T 完整覆盖 → REPORT_part3`。**取消 v1.0 的全库多角色网格与登记后自动开放全库首次观察**；只有有需求行、有角色契约的路线才生成实验，未路由对象保持"未研究"，不写"无效"。探索从宽落在：推导段允许全部 `routed` 与 `candidate_for_routing` 行、任何路线不以收益 / 相关 / 显著性设闸、卡数不设上限；采纳只在 E7 + 用户过目。

### 0.1 相对 web plan 的采纳与调整（规划 session 决定；★ = 规划 session 自身错误，已按 47 源码核实）

| web plan 内容 | 处置 |
|---|---|
| §0.1 十二项修订（撤销全库网格、三层分类、T0 全分布、按需求建域、卡数非上限、不设弱腿 / 高相关 / 分类不稳闸、DEP 分关例外、行业时钟分离、平局 / 缺失 / 缩放处理、规则级后段授权、以完整策略净增量为主） | **全部采纳** |
| §0.2「待核」：`abn_turnover`、`parkinson_vol` 源函数含负号；T0 列方向 | ★ **核实成立且影响 proposal 的读法**：`compute_abnormal_turnover` 返回 `−MA20/MA120`、`compute_parkinson_vol` 返回 `−vol`、`compute_reversal_skip1` 返回 `−(行业内去均值 skip-1 十日收益)`（`pool_screening_v2.py:205 / 190 / 161`）；E6g T0 的 `pct_*` 对源值取（`e6g_desc.spec_of_key → specF → get_pct_g(direction='hi')`）。因此 proposal §1.2"被错剔赢家换手相对自身放大、区间波动大"应反读为**更安静、区间窄、相对同业回落**；E-V 的 T0 支持分支是"量静"，"量增"为竞争分支——plan 已分卡，本 brief 只改标签。E6g REPORT"波动代理冲突"是符号伪象，已补记 |
| §0.2「待核」：K2 正反对照是否成镜像 | **采纳**：K2 的 `ctl_reverse_matchN` 是按同键反向取同人数，不是 `1−pct`；本轮对每对报人数 / 支持日 / 方向 / 权重，不从合并均值 ≈ 0 推"无方向性"，该句在 REVIEW 里限定为"否决角色 × 推导段"的合并读数 |
| §1.2 母体表与 K/T/C 身份 | **采纳**（K/T/C = `conditional_turnover / turnover_volatility_60d / CVR_20d`，E6g `engine_contract` 已核） |
| §1.3 `feature_semantics.csv`（源符号、单位、窗口、别名、可得时点） | **采纳**；在 E6g `registry/key_registry.csv` 基础上加 `source_sign / economic_direction / value_used_for_pct` 三列，四个自定义键与 `cmf_change_neg` 的负号明写 |
| §1.4 血缘与时间守卫（规则级授权、`label_end`、T0-74 不入 carried 后段） | **采纳**；沿 E6g `e6g_core.guard / Lin / learned_lineage`（16/16 攻击测试）扩 `registered_rule` 与新派生键（TCV / JUMP / IND_*）标签 |
| §2 R0 三层分类与需求卡；§2.2 聚类口径（average / complete linkage，家族权重后置，KMeans k{3,4,5} seed 1109，fit 2010-14 → 应用 2015-18） | **采纳**（sklearn 1.3.1 / scipy 1.11.3 在 47 可用，E6g 聚类只因时间 deferred） |
| §3.1 七条初始路线（M-T / M-C / E-V / E-P / R-O / I-P / L-Q）与 §3.2–3.4 模板参数 | **采纳为记录 A 的 v0**（§4）：执行端在 R0 交付后即可按七条路线的初始测量开跑推导段，不等规划 session 写完整路由表；规划 session 在 R0 后出记录 A v1（只增改、不按收益删行） |
| §3.2 E-P 阈值：比例键 ≤0.2 / ≥0.8、计数键 ≤1 / ≥4、divergence 0/1 | **采纳**（`intraday_ret_consistency_5d`、`positive_day_ratio_5d`、`gap_direction_consistency_5d` 是比例，`agreement_count_5d` 是计数，附录 A 定义已核） |
| §4 集合契约（U/C/V/B/D、DEP 分关例外、ADD/SWAP/CONJ、缺失与 identity、对照、归因恒等式） | **采纳**；identity 全部作阻断锚 |
| §5 域与选择（S0 固定代表 / S1 层级等权 / S2 局部收缩 τ{0.5,1,2}、π0=1/2；≤2018 估计一次冻结后同应用两后段） | **采纳** |
| §6 两次记录、一次用户授权；删除自动 F-explore | **采纳**；见 §0.2 对"探索从宽"的落法 |
| §7 行业时钟（`IND_FEATURE_CURRENT` vs `IND_TRADABLE` vs `IND_FEATURE_ROLLING`） | **采纳**；`industry_zx1` 日频 PIT 在 E6f 已核成立（相邻日 9,769 格变化），缺行业记 UNKNOWN |
| §8 carried L（768 + 192 + 192；κ{0.25,0.5,1,2} × A{1,5,10,20} 亿；求根；L-Q 受血缘约束） | **采纳**；b 语义沿 `e6g_l.relaxed_domain`（`d0 + b` 百分点；`relative1.5` 保留作别名桥） |
| §9 carried T（逐年归因；绝对人数 N{30,…,200} × keep{15,…,50} × PRE/POST_VETO；子样本 N{150,250} × 32 seed；P16 560 格；状态量） | **采纳** |
| §10 统计（NW lag max(5,H)；bootstrap 2,000 段内共 draw；F-route / F-headline / F-L / F-T；stepdown） | **采纳**；"分了类不等于测试数变少"进 REPORT 模板 |
| §11 工作流与 §12 验收（技术验收，不加经济门槛；68 项本地合成检查不替代 47 真接口测试） | **采纳**；三次交付见 §13 |
| §12.4 Q1–Q10 | **逐字进事前登记**（§11）；规划 session 另加 Q11–Q13（T 块读法），标"规划补充" |
| 随机路径 256 → 按 MCSE > 0.05 pp 补到 512 / 1024 | **采纳条数，改存储**：只落汇总 + 8 条示例日账本（E6e 183 GB 教训） |
| 并发 | ≤12 worker 或按实测 ~205 线程/进程的等价预算；先实测再定 |

### 0.2 "设计尽量宽松，不要太严格"（用户 09-11）在本 brief 的落法

- **硬约束只六类**（违反即停并写 BLOCKERS）：① 取数 `end_date ≤ 20260327`，走 `guarded_load`，不读 E7；② **血缘守卫**：NEW40 键、新派生键（TCV / JUMP / IND_*）、新规则对象（SLOT / FOCAL_CONDITION / ADD / SWAP / CONJ / MARGIN / 软降权）在 2019+ 上依赖收益、持仓、条件分布或选择结果的计算，只在记录 B 批准后按冻结清单运行；推导段 `label_end ≤ 2018-12-31`；T0-74 产物不进 carried 后段；③ 四地基、七 e6e、十九 e6f、二十八 e6g 脚本不改（新代码 `e6h_*.py`），`results/` 不删，不改 I11 / pool0 / clean / 生产 DEV / 生产 H5 / 8bp 主口径 / 生产 v2；④ 并发在实测线程预算内，父进程验收后写 DONE，状态表求和 = 登记总数；⑤ git 只 whitelist add，不 `git add .`，不混入旧 untracked；⑥ 文档不出现登录信息与主机地址。
- **plan 里其余的"不得 / 必须"一律改读为"报告并继续"**；MODULE STOP 只限符号 / 时间 / 域的逻辑错（未来函数、成本重复扣、账户资产凭空消失、active-leg 或有效域错、DEP 例外绕过另一关、ADD/SWAP 绕过源 veto、位置索引未按 ticker 对齐）；锚差报最大差 / 日期 / 原因记 WARN；资料缺失 → 模块 `UNAVAILABLE_WITH_REASON`，其余继续。
- **探索从宽的具体边界**：推导段（2010-2018）对 `routed` 与 `candidate_for_routing` 两类行都跑（含全部参数格、竞争方向、对照）；`unassigned` / `diagnostic_only` 行只做 R0 的基础诊断（分布、相关、可用率）不做策略；后段只跑记录 B 冻结清单。任何路线不因收益、相关、显著性、簇不稳、单项弱而停止；"约 8–12 张重点卡"只是 REPORT 组织长度。
- **网格不缩、也不加严**：plan 打开的格全跑；执行端顺手可加的格作附加列登记，不进主表不替代主表。
- **实施细节留给执行端**：模块划分、缓存、分片、并行顺序按 plan §11 建议不强制；"名称可适配，字段不可遗漏"。

---

## 1. 起点确认与契约

### 1.1 起点
- 47 HEAD `463575d`（E6g 交付 + 各轮 brief 入库）；untracked：三个 2026-05 `.py` 与七个 `chain*/wave*/autochain.sh`，不动、不 add。
- E6g 产出 `results/20260911_1140_E6g_structure_layer/`：`registry/`（75 键；`key_registry.csv` 含血缘、别名、并列、复权、访问史）、`H0/H_manifest.csv`、`D/`、`T0_35/`、`T0_74_discovery/`、`K_discovery/`、`L/`、`B/`、`C/`、`checks/`、`E6h_registration_draft.md`（40 键逐键：轴 / 角色 / 两对照 / 并列 / 复权 / 访问史）。
- 可复用代码（`e6g_core.py` 等 28 个）：`guard / Lin / learned_lineage / assert_registered_spec`、`specF / build_raw_g / tf_apply / agg_dense / get_pct_g`、`keep_SRC / keep_QEDGE / keep_RANKBUDGET / drop_*`、`canon_veto / canon_legs / path_key / cache_key`、`blend3_weights`、`eval_mask`；`e6g_h0`（tie_diag / whole_tie / random_tie）、`e6g_t0`（labels：源版 + 端点复利版）、`e6g_k`（iid_expect、同人数 core / 反向）、`e6g_l`（relaxed_domain / buffered_targets）、`e6g_c`（`align_to_close`、冲击括号、`shadow_account` 移植版）。

### 1.2 数据与生产锁
沿 E6g brief §1.2。研究变体（TCV / JUMP / IND_* 派生键、SLOT / FOCAL_CONDITION / ADD / SWAP / CONJ / MARGIN / 软降权、H≠5、缓冲、影子账户）一律独立命名，不进交付、不进公共库。

### 1.3 契约（规划 session 2026-09-11 已按 47 源码核；执行端整段读函数体复核并写 `engine_contract.md`，每条机制句三栏：定义处 / 调用处 / 默认值）
- **自定义键符号**：`compute_abnormal_turnover` = `−(MA20/MA120)`（min_periods 10/60）；`compute_parkinson_vol` = `−sqrt(rolling20 mean of (ln(H/L))²/(4 ln 2))`（H==L 置 NaN，min_periods 14）；`compute_reversal_skip1` = `−(close.shift(1)/close.shift(11) − 1，行业内去均值)`；`cmf_change_neg` = `−compute_cmf_change`。四者在 `get_default_factor_specs` 的 `direction='positive'` 指"源值大 = 好"。**K** = `turnover_rate / (|log(close/lclose)| + 1e-4)`；**T** = `turnover_rate.rolling(60, min_periods=30).std()`（水平与不稳定性混合）；**C** = `CVR_20d`。`feature_semantics.csv` 对每键写 `source_sign / economic_quantity / value_used_for_pct`，T0 与 K2 的历史列按此重述。
- **pool0 / clean / 基准 / DEV / 引擎 / 账本口径**：沿 E6g `engine_contract.md`（age ∈ {1,…,5}；I11 三成分截断；涨跌停过滤 no-op；每段头 19 天基准 NaN；DEV `min(1/n, 0.01)` + 行业 cap 等比缩减不归一；`gross = port − bench × position`；`turnover = 0.5Σ|Δah|`；8bp 单边换手基数 `net8 = gross − 8e−4·turn`，不再除 2、不买卖各扣）。
- **E3 标签**：`compute_forward_5d_excess(data, base_pool, hold_days=5, adjust=True)` = T+2…T+6 五个日超额算术和 × 1e4，基准 `base_pool`；端点复利版另名（`e6g_t0.labels`）。
- **行业**：`industry_zx1` 日频长表 pivot（`data_loader.load_fundamental_long_table`），PIT 成立；`IND_FEATURE_CURRENT(i,T,w)` = T 时可见同业（剔 i）已复权 close 端点收益等权均值，w∈{5,20}；同业 <5 标 thin；单成员 NA；`IND_TRADABLE` 另守 VWAP(s−1) 前已知；`IND_FEATURE_ROLLING` 按历史日 PIT 聚合再滚动。
- **派生量**：`TCV_w = std_w(turnover)/mean_w(turnover)`，w∈{20,60}，min 有效 {10,30}，ddof 沿源 std，mean ≤0 → NA；`JUMP_w` = 隔夜平方收益和 / (隔夜 + 日内平方收益和)，w∈{5,20}，≥3/10 成对有效，全零 NA。
- **缓冲**：`relaxed_domain` 的 b 为分位百分点（`d = min(100, d0 + b)`），DEP 只放宽第二关；`L-loose` 全体重 DEV，`L-matchN` `m_t = |N_t|`；b=0 直接返回源目标。
- **成本**：`e6g_c` 括号 sqrt `Σ|q|^1.5 σ20/√ADV20`、lin `Σq²σ20/ADV20`，`c = κ√(A·1e8)·bracket`，年化 ×252×100；ADV20 交易日口径，`ADV20c` 含停牌 0 敏感性；金额单位元。
- **守卫**：`Lin` 血缘沿 DAG 最严格父；`use_type ∈ {label, shape, holding, trade, cost, outcome_cluster, selection}`；攻击测试沿 E6g 四条 + 新增：重命名规则对象、已知键条件化绕过、TCV/JUMP/IND 未登记即用于 2019+、DEP 例外绕过另一关。
- **平局**：源 `rank('first')`；`WHOLE_TIE` 施于实际排序分；`RANDOM_TIE` 64 seed；二元 / 计数键用真实状态阈值不切分位。

### 1.4 事前登记
首次新收益评价前落盘 `preregistration.md` = 本 brief §11 全文（plan §12.4 Q1–Q10 逐字 + 规划补充 Q11–Q13 + 边界）+ 实际时间 + 输入 / 代码哈希 + 源 ID 映射；修订另起 `preregistration_amend_<日期>.md`。**不改写编号与问题。**

---

## 2. 阶段 0（不改数字口径）
- 读 `PROJECT_STATUS.md`、`00_协议.md`、memory 入口、E6g 三份 REPORT + REVIEW、`E6h_proposal.md`（含勘误）、plan v2.0；冻结四地基 + e6e + e6f + e6g 脚本 SHA 与运行库版本；写 `source_manifest`；记 HEAD / dirty / untracked。
- `feature_semantics.csv` / `feature_taxonomy.csv`：U74（34 + 40）+ `intraday_cvr_1d` 别名 + 派生量（TCV_20/60、JUMP_5/20、IND_FEATURE_CURRENT_5/20、IND_FEATURE_ROLLING、个股相对同业收益）逐键：原始字段、公式、经济量、**源符号**、单位、窗口 / min_periods、分母、平滑顺序、复权、可得时点、有效条件、缺失标志、精确别名、近似同源、已有角色、历史观察段（`previous_looks`）。
- 固定展示组从 E6g 注册表导入（R1 / R2 / A06 / A08 / A03 / T25 / A07 / Blend3 账户值），不自行拼写默认参数。
- 新算子恒等锚（阻断）：SLOT α=0 = 源父逐位；FOCAL 全开 = 原焦点否决、全关 = 无焦点父；ADD/SWAP η=0 = 原 B；CONJ Jbad 全真 = 原父、无上限加回 = `C ∪ (E\C)\Jbad` 恒等；软降权 λ=0 = 原父；MARGIN e=0 = 原 B；`depth_absN` 在 N = 当日 RANKBUDGET 人数时逐位；`pool_subsample` N ≥ n_t 时原池逐位；`IND_FEATURE_CURRENT` 单成分 = NA、两成分互为对方收益；TCV 缩放不变；标志 `align_to_close` 按 ticker 对齐（列置换、重复、缺列、前导零测试）。
- 守卫扩展与攻击测试（§1.3）；`checks/` 落证据。
- 并发：先实测每 worker 线程数与内存，再定 worker 数（≤12 或等价）；随机路径只存汇总 + 8 条示例；状态表 / 父进程验收沿 E6g。

## 3. R0：需求诊断与三层分类（推导段 2010-14 / 2015-18；全部 `exploratory`；plan §2 全文执行）
- **母体复原**（R1 / R2 / A06 / A08）：源可用域、原核 C、各经济拒绝阶段、原 veto、最终名单 B、因缺失 / 预热 / 3g 失败的名单；DEP 记 S1 与第二关系数 / 切点；源 combine 允许部分因子有效时按真实源复现，另报完整输入双胞胎。
- **T0 全分布**：源标签原样（base_pool、算术和、T+1→T+6）+ pool0 同 cohort / 绝对收益 / 复利终点另名；全分布期望、负 / 正 / 中段贡献；**当前被留下的损失按实际权重计**；**可改变的拒绝机会 = 事前条件覆盖的全部股票**（含条件内输家与中段）；决策边界（第一关 / 第二关 / 否决处）；实施损失（新增 / 移出的交易量、成本代理）。每条事前条件输出可用日期、动作频率、样本量、完整收益分布、父 / 拒绝集覆盖、每股权重、目标与 rolling 资本贡献、费用；全日期净收益列保留不动作日。
- **伪路径**：U-IID / 行业人数 I-IID / 行业×市值三档，各 128 起（MCSE > 0.05 pp 补到 256）；伪输家与伪赢家对称。
- **三层分类产物**：`feature_taxonomy.csv`（测量目录，多标签）、`factor_parent_relation.csv`（同轴更好测量 / 旧轴补充 / 局部条件状态 / 未覆盖风险 / 执行信息）、`need_parent_role_map.csv`（`status ∈ {routed, candidate_for_routing, diagnostic_only, unassigned, unavailable, exact_alias}`）。相关：按日 signed Spearman 再跨日汇总，分 clean / pool0 / 父保留 / 经济拒绝集；聚类 average / complete linkage on `1−|ρ|`，不用 Ward；主体聚类 KMeans k{3,4,5}、n_init 20、seed 1109、日期等权、家族权重（1/√非别名列数）在标准化后施加、fit 2010-14 应用 2015-18；深度 ≤3 树只作描述。
- 交付 R0 包（`parent_need_ledger.md`、三张 csv、T0 全分布表、聚类 / 树）给规划 session。

## 4. 路线冻结（记录 A；规划 session；不读受保护的 2019+ 结果）
- **记录 A v0（本 brief 即生效，执行端 R0 交付后可开跑）**：plan §3.1 七条路线按其"初始测量及源锚 / 首选母体 / 允许主操作"全部激活为 `routed`；每条路线的竞争解释各自成卡（E-V 量静 vs 量增；I-P 向上机会 vs 向下风险；R-O 高 vs 低状态）。**E-V 的 T0 支持分支为"量静"**（源值 `abn_turnover` 高 = 换手比低；`parkinson_vol` 高 = 区间窄；`reversal_skip1` 高 = 相对同业回落），"量增"为竞争分支；两者用同一价格条件（`REL_LOW` q{0.2,0.3}；`NEAR_ZERO` |20 日复权涨幅| ≤10%，另 5 日 ≤5%）。
- **记录 A v1（R0 交付后 ≤2 个工作日）**：规划 session 按需求卡增改路由（新增测量 / 母体 / 操作、改 `status`）；**不按推导段收益删 `routed` 行**；改动写理由与旧意见；`route_manifest.json` 带 SHA。执行端在 v1 前先跑 v0 已激活路线，v1 只增量补跑。
- 模板参数（plan §3.2 逐字）：SLOT α{0,1/4,1/2,1} × {FALLBACK, REPLACE}，另给共同完整域整条 α 曲线；FOCAL_REPLACE / FOCAL_CONDITION 四对照（无焦点 / 原焦点 / 新焦点 / 并用），k{5,10}，启用 `V_f ∩ S` 与豁免 `V_f \ S` 分卡；E-P 阈值比例 ≤0.2 / ≥0.8、计数 ≤1 / ≥4、divergence 0/1，初始焦点 = 母体已有 cr5 否决；ADD/SWAP 额度 `m_cap = round_half_up(η|B|)`，η{0,0.10,0.25,0.50}，旧 `x|pool0|` x{0.05,0.10} 只作桥；CONJ 按 §4.2 定义；R-O JUMP_5/20 与 `gap_abs_zscore_20d`，剔最高 1/k k{5,10}，软降权 λ{0,0.5,1} 释放资本留现金；I-P 向上卡 `IND_FEATURE_CURRENT_w > 0 ∧ 个股相对同业收益在 pool0 最低 q`（w{5,20}、q{0.2,0.3}，ADD/SWAP），向下卡 `IND_FEATURE_CURRENT_w < 0 ∧ 同行特征在 pool0 最低 1/k`（k{5,10}，在 B 内否决）；L-Q 保护最好 (1−e) 份额，e{0.10,0.25,0.50}，候选带按流动性改善排序补回原人数，全部仍过原 veto，对照源顺序 / 便宜优先 / 贵优先 / 同带随机；M-T TCV_20/60 与 `turnover_5d` 在 T 位；M-C C20 源锚 / CVR5 / CLV20 / CLV 在 A06 的 C 位与 R2 的 C 否决位分域。
- 交互清单（事前冻结）：M-T × E-V（R2 / A06）、E-V × R-O、E-V × I-P；每对 P / P+A / P+B / P+A+B 四条完整策略；中心测量按源清晰度选；ADD 共用总名额等额切分、重复票只占一次、风险否决默认在机会加入后运行。
- 迁移：每卡 ≥1 原生母体 + ≥1 结构不同的迁移母体（确无则允许一个）；缺 K 的父不接受"替换 K"；核心含 C 的父区分替代与冗余；Blend 只在原子父应用再合并账户。
- 全部基本格 H5；同格补 H{3,10,20} 与加回 / 移出集合 1–20 日事件剖面；原父同 H 一起跑。

## 5. R1–R3：推导段实验、集合契约、域与选择（plan §3–§5 全文执行）
- 集合身份：U = 冻结 pool0；C 源核；V 源否决；B = C\V；D = 该次真实经济筛选拒绝且通过非焦点约束且有本路线输入的票（预热 / 3g / 缺原核分数不算 D）；DEP 第一关 / 第二关 / 双关例外三种分卡，外推只用原 S1 系数与切点并披露范围外比例。
- ADD `B' = B ∪ A`；SWAP `B' = (B\R) ∪ A*`，`|R| = |A*| ≤ |B|`；主平局固定 ticker 哈希；CONJ `E = C ∪ D`、`C' = E \ ((E\C) ∩ Jbad)` 再去 V；identity 端点在新因子加载前短路；SLOT_FALLBACK 与 SLOT_REPLACE 分名；条件缺失 = 无动作另码。
- **每条主路径对照**：原父；同日同人数核心放宽 / 剔深；同日同人数反向；共同可得域父；原生 DEV 与只向下缩的同仓位；U-IID / 行业 I-IID / 持续 I-P20 随机 256 起、MCSE > 0.05 pp 补到 512 / 1024；每条路径独立 DEV / rolling / 净交易 / 成本；保存 seed、配额、路径 hash、分段结果、≥8 条完整示例。
- 归因：`Δgross = Σ(w_child − w_parent)(r − bench)` 按新增 / 移出 / 幸存者重定权三集合分解，再扣费用差与冲击差；逐日先恒等再汇总；报目标人数 / live 人数 / 净仓位 / HHI / 有效 N / 行业权重 / 可成交与流动性暴露。
- 域：`parent × need × mechanism_direction × decision_role × core_budget_policy × H × cost_scenario`；输出路线相对母体增量地图 + 域内 S0 固定代表 / S1 层级等权组合（测量→非别名参数两层，精确别名一票）/ S2 局部收缩（`a_j ∝ π_j exp(μ_j/τ)`，π0 = 1/2，τ{0.5,1,2}，log-sum-exp，原父始终合法，identity 只计父）的完整账户；推导内部 2010-14 估、2015-18 固定应用。
- 交付 `REPORT_part1`：全部已路由实验（含弱 / 负）、覆盖、中心代表、组合、选择规则、额外机制提案、`consideration_ledger.csv`。

## 6. 记录 B：一次用户登记（part1 之后）
- 用户 + 规划 session（web 可核对）冻结后段清单：`id / need / measurement_taxonomy / parent / source_stage / role_AST / candidate_measurements / direction_and_competitor / validity_and_fallback / grids / H / budget / controls / matched_pairs / interactions / domain_members / representative / mixture_hierarchy / selector / train_cutoff / label_end_cutoff / provenance / previous_looks / uncertainty_reading / source+code_hash / approval_receipt`（plan 附录 B 模板）。**不用收益阈值替代批准**；考虑过未进后段的路线留理由（用途 / 技术 / 延期 / 用户取舍）。
- 执行端核 SHA 后打开守卫，两后段（2019-23、2024-26）同一 manifest 全部计算并封存，receipt 后共同展示；**不看 2019-23 后改 2024-26**；后段技术修复保持经济定义并记 hash。
- 闸期间执行端不空等：块 L / T 中只用旧输入与旧规则的格可先算后段并封存；L-Q 与任何 NEW40 血缘格只跑推导段。

## 7. 后段首次观察（记录 B 之后）
- 所有冻结路径在两后段 + 四段合并：vs 直接母体 / R1@H5 / R2@H5 / 同母体同 H；同人数 / 同仓位 / 反向 / 随机对照；S0 / S1 / S2 账户（≤2018 估计冻结后同应用）；逐年、最近段、去 15+16、单年留一。
- 家族：F-route（同需求 / 母体）、F-headline（本轮全部后段注册策略 / 固定组合 / 选择规则）；卡数、描述符、唯一路径、学习步骤分别统计。
- 结论格式（plan §10.3）：`在哪个母体 / 需求 / 角色 / 日期 / 支持 / 成本下，点估多少、不确定性多少、相对什么、哪部分可解释、哪些解释未排除`；分"有改善点估且值得继续 / 改善主要来自资金成本 / 无改善点估 / 区间过宽或支持不足 / 构造不可判"五类说明，不作淘汰标签。
- 交付 `REPORT_part2` + `first_look_receipts`。

## 8. carried L：期限、缓冲与实际实施（plan §8 全文执行）
- 八账户 R1 / A03 / R2 / A06 / A07 / A08 / T25 / Blend3 × H{1,2,3,5,10,15,20,30} × b{0,5,10,15,20,30} × {matchN, loose} = 768（含 b0 别名，b0 先逐位复现 E6g）；`actual_incumbent` 八账户 × H{3,5,15,20} × b{0,10,20} × 两预算 = 192，与 target_incumbent 并排；L-X R1/R2/A06/A08 × H{3,5,15,20} × b{0,10,20} × 两开关四组合（源否决触发 / 跌出核心放宽边界），matchN 主版 = 192，全关为同账户参照。
- 新主路线在记录 B 指定的中心代表与 S1 组合上补 b{0,10} × H{3,5,15,20}（名单后段前冻结）。L-Q 边缘替代域进同成本完整策略比较；**L-Q 用 amihud 等 NEW40 血缘，登记前只跑推导段**。
- 库存：续选只决定新批次；`actual_incumbent(T)` = T 时已成交有库存；未过期 / 过期卖不掉分列；批次 ID / 形成 / 成交 / 可卖 / 到期 / 数量 / 未成交 / 现金 / 费用 / 估值 / 公司行动全记；三层比较（同账户全可成交 − 源引擎；受限 − 全可成交；提前退出 / 实际续选 − 受限全关）；固定名义与自融资 NAV 分列；标志按 ticker 对齐。
- 成本：`net8 = gross − 8e−4·turn`（单边基数不再除 2）；12bp 另情景；A{1,5,10,20} 亿 × κ{0.25,0.5,1,2} + 无冲击；`Δ实施净收益 = Δgross − Δ固定费用 − Δ冲击`；求根：平方根模型 `net(A) = n − κC√A` 须 n>0、C>0；交叉 `Δn/(κΔC) > 0`；账户路径依赖时扫符号变化区间再求根，允许多根 / 无根；5% / 10% / 20% ADV 参与率作压力列。
- 领导表草稿（H × A × κ 净值；缓冲换手 / 净值）经用户；不选生产 H。

## 9. carried T：时间异质、人数预算与 P16（plan §9 全文执行）
- **T1 归因**：固定展示父 + KTC keep{25,30,40,50} 逐年 / 四段 net8、gross、turn、仓位、目标 / live 人数、有效 N、行业、重复形成、pool0 规模、输入有效率；`excess_clean − excess_pool = position·(pool_unit_return − clean_return)` 逐日恒等；事后 fwd5 离散度与 T 可见历史离散度分字段；共趋势回归系数不称原因占比。
- **T2 绝对人数**：KTC_mean / T / KT_mean × 否决栈 {C:k5+cr5:k10, cvr_1d:k10+cr5:k10, 无}；N{30,40,50,60,80,100,120,150,200} 与 keep{15,20,25,30,35,40,50}；PRE_VETO / POST_VETO（POST 分母仍是冻结 pool0）；RANKBUDGET 主研究、SRC/QEDGE 桥；人数不足取全部合法票不绕 veto。
- **T3 子样本**：I11 / clean 不变，选股阶段 U 取 N{150,250} 子样本 × 32 seed × {IID, 固定 ticker 哈希持续}；n<N 保留全部；R1/R2/A06/A08 + KTC keep{25,30,40,50} 共享样本指纹；三种运行（全域系数分位冻结只限制可选票 / 系数全域子域重排 / 子域重新中性化重排）；DEP 第二关不重拟合。**读法**：斜率翻号弱化只说明在该构造中弱化。
- **T4 P16 加密**：`T{15,20,25,30,35,40,45} × K_MA{1,2,3,4,5} × B{3,5} × keep{30,35} × cvr_1d k{5,10} × B k{5,10}` = 560；源 ε 1e−4，B3u/B5u，与 E6g 重叠路径逐日锚；全历史 / 2019+ / 最近段 / 去 15+16 / 单年留一分报点估与区间；最大格标"样本内最大"。
- **T5 状态量**（描述）：历史市场换手、横截面离散度、pool 规模、行业 HHI / 广度、滞后市值分组收益，带可得时点；不建开关。
- 交付 `REPORT_part3`（L / T 完整覆盖 + 合并地图 + 全轮 coverage）。

## 10. 统计与账本（plan §10 全文执行）
逐日 gross / position / turn / net8 / net12 与成本列，gross 标明是否已减基准；年化 = 共同有效日均值 × 252 × 100；`legacy_all` / 共同可得域 / 共同起点稳态三支持；MDD 标绝对 NAV 或超额曲线；NW lag = max(5, H) 另 20 / 60 或 2H；bootstrap 2,000 stationary、块长 20 / 60、段内、共 draw、重做拟合时同步重估；F-route / F-headline / F-L / F-T 逐点 + 同时带 + stepdown 附列；零方差 identity 恒等 0；不用 nanmax 换比较集合。所有汇总量标算子与 n，均值与中位并报；全称句只来自计数。

---

## 11. 事前登记（执行端逐字落盘为 `preregistration.md`；只补时间、哈希、源 ID 映射）

**plan §12.4 原文（Q1–Q10）**
Q1：本轮哪些分类实际改变了母体用途/规则，哪些只是目录标签？
Q2：每个主母体的可改善损益问题是什么，新信息针对哪里？
Q3：同轴替代、独立补充和状态信息的增量是否不同？
Q4：加回的全分布与同人数SWAP是否改善，而不只是救回赢家？
Q5：条件作用是否超出单条件、人数和资本变化，哪些解释仍未排除？
Q6：哪些有道理的联合结构在单项不强时仍有价值，哪些没有？
Q7：固定代表、同机制组合、局部收缩选择各能保留多少对父优势？
Q8：需求映射在不同母体/时代是否需不同角色，哪些不能迁移？
Q9：期限、人数、受限库存与成本使哪一部分改善保留或翻转？
Q10：还有哪些测量未路由、哪些结构未测试，下一轮应追什么，而不是宣布哪一整库饱和？

**规划 session 补充（T 块读法）**
Q11 深度斜率翻号能否归到池规模 / 基准 / 离散度 / 腿本身时变？备择四个；读法 = T1 相关 + T3 子样本；无效果 = 子样本下翻号不变且相关弱 → "翻号来源不在这四个量"。
Q12 绝对人数深度是否消除翻号？读法 = 逐段 Δ vs 百分比深度，PRE/POST 分列；不选生产深度。
Q13 P16 角落峰位置是否稳定且不依赖 2015+16？读法 = 含 / 不含两套同时带 + 峰位置 + mask Jaccard；无效果 = 不含 2015+16 无同时带正 → P16 park。

**边界全文**：所有截至 2026-03-27 的历史此前用于研究；推导段结果属研究历史不叫未污染 OOS；后段是首次观察但研究者知道 regime，不是未触碰样本；E7 是唯一 OOS。统计量、成本翻转、局部弱段、MCSE、风险画像用于读表，不作自动淘汰门；未路由不等于无效；每句"无效果"写母体 × 需求 × 角色 × 日期 × 支持 × 成本；线状态与 v3 由用户定；E7 HOLD。

---

## 12. 自测与验收（只对正确性设硬条件）
- GLOBAL STOP：E7 数据进入计算；受保护对象（NEW40 / 派生键 / 规则对象 / T0-74 产物）越界到 2019+ 或流入 carried 后段；源码 / 冻结数据意外变化；进程配额不足且无法降并发。MODULE STOP：§0.2 所列逻辑错。WARN / LIMIT：锚差可解释、注册表计数不符、行业 PIT 缺口、字段缺失、SE 退化、恒等式不过的小块 → 保留主结果、缺失列 NA、禁止有利插补。合法研究结果：净值下降、某段负、区间跨零、随机参照不显著、某 κ 翻转、簇不稳、q 间不单调 → 全部留表。
- 真实源必核（plan §12.1）：R1/R2/A06/A08 固定目标与日账本；H5 / b0 / α0 / η0 / λ0 / e0 identity；焦点全开 / 全关；T0 原标签；SRC/QEDGE 共同工作日；源与研究分数有效域；PIT 行业；标志按列名对齐；每条账的 net 费用恒等式；新增反例（未路由键不得自动获角色；diagnostic_only 不入选择域；同名不同公式不去重；别名不改组合资本；置零旧腿不再要求其有效；二元 NA 不变事件；ADD/SWAP 不绕源 veto；DEP 第一关例外仍约束第二关；组合真实交易；成本与规模根；label 结束日与规则级后段访问）。
- 完成定义：每登记单元 ∈ {PENDING, RUNNING, SUCCEEDED, FAILED, LIMIT, SUPERSEDED, ROUTING_PENDING, UNAVAILABLE_WITH_REASON}，计数之和 = 登记总数；产物带输入 hash / schema / 行数 / 有限与 NA 计数 / 状态；核心模块未跑标 `PARTIAL_WITH_LIMITS`。plan 附录 D 的 68 项本地合成检查可复跑但不替代 47 真接口测试。

## 13. 运行组织（三次交付 + 两次记录）
`0 → R0 → REPORT_R0（给规划 session）→ 记录 A v0 已在本 brief 生效（v1 由规划 session 在 R0 后补，≤2 工作日）→ 推导段 R1–R3 + 块 L / T 的推导段与旧输入部分 → REPORT_part1 → 记录 B（用户）→ 两后段 → REPORT_part2 → 块 L / T 完整覆盖 → REPORT_part3 + coverage`。part1 / part2 不是等用户 GO；part1 后不得按收益改网格；用户中途改方向则保存原登记并做 amendment。
- 问题与交付映射：part1 答 Q1 / Q2 / Q3 / Q4 / Q5 / Q6 的推导段部分与 Q10 初稿；part2 答 Q3–Q8 的后段部分与 Q7；part3 答 Q9、Q11–Q13 与 Q10 定稿。
- 计时：先实测小样本每日期 × 配置耗时、内存、线程、吞吐，再估全部冻结任务；>30 分钟阶段报预计；**慢不是问题**，只分批交付不削。
- 并发：初始不高于已验证 12 worker 量级，先查真实总线程 / RSS / 句柄 / 磁盘 / 共用负荷；全任务共享配额；绑 socket 1；父进程验收；`os._exit(0)` 只作受控恢复。
- 存储：日账本分块 float64 parquet；随机路径汇总 + 8 示例；影子账户逐日现金 / 持仓 / 费用账；写前估容量。

## 14. 交回
- `results/<ts>_E6h_need_driven_routing/`：`PLAN_COPY.md / brief_copy.md / preregistration.md`、`source_manifest / engine_contract.md / anchors`、`feature_semantics.csv / feature_taxonomy.csv`、`parent_need_ledger.md / factor_parent_relation.csv`、`need_parent_role_map.csv / route_manifest.json`（v0 / v1）、`consideration_ledger.csv / coverage.csv`、`T0_full_distribution / stage_sets / profiles`、`route_results / interaction_results / paired_controls`、`random_registry / random_summaries`、`domain_manifest / fixed_mix / local_selection_accounts`、`registration / approvals / first_look_receipts`、`daily_ledger / inventory / L / T`、`checks / selftests / runtime`、`line_state_proposal.md / park_ledger_delta.md`（草稿）、`limit_register.md`、`source_corrections_E6h.md`、`REPORT_part1/2/3.md`、`E6h_REVIEW_input.md`。
- `exec_briefs/E6h_REPORT_part1.md`、`_part2.md`、`_part3.md`：协议结构；每份 ≤15 行纯文本摘要；Q1–Q13 每问：原问题 → 数字 / 分母 → 竞争解释 → 仍未知 → 下一步含义；所有统计表附总体计数与分布极值；**不写"可交付 / 已确证 / 必须换核 / 饱和 / 穷尽 / 到平台"**；part3 末尾附全轮 coverage。
- coverage 硬交付：逐条映射 proposal、plan、本 brief，状态 `done / reused / changed / deferred / unavailable`，理由与影响。
- WORKLOG 远端 + 本地同文（只记操作事实；不含账号路径）；git whitelist add `e6h_*.py`、本 brief、`source_corrections_E6h.md`；e6e / e6f / e6g 不改不重 add；三个 2026-05 与七个 `.sh` 不 add；`git push origin main`。

## 15. 禁区
不读 2026-03-27 之后数据、不开 E7；受保护对象不进 2019+ 直至记录 B；T0-74 不进 carried 后段；不改 I11 / pool0 / clean / 生产 DEV / 生产 H5 / 8bp / v2；研究变体不升格生产；不把首次观察读成 OOS；不把"无效果"写成线级"穷尽 / 到平台 / 饱和"；不把未路由写成无效；不以卡数、描述符数或审计通过数当改善；不因慢减配置；不用 `git add .`；不出现登录信息与主机地址。凡遇"必须改上述任何一项才能继续" → 停，写 BLOCKERS。

## 16. 自审记录（规划 session 2026-09-11；执行端见此段方可开工）
| 类 | 不利因素 | 处置 |
|---|---|---|
| 事实 | proposal 按名字读了三个负号因子的方向（"量增价平"、"波动代理冲突"） | §0.1 ★ 承认；proposal 顶部勘误；`feature_semantics` 加源符号三列；E-V 量静为 T0 支持分支、量增竞争 |
| 事实 | proposal 指纹与 plan 记录不符（勘误块） | WARN，两个哈希进 manifest |
| 代码 | 六类新算子 + 三类派生键 + 守卫扩展 | 恒等锚逐位阻断；攻击测试；玩具池；地基不改 |
| 代码 | DEP 分关例外实现（外推第二关系数） | 只用原 S1 系数与切点；范围外比例披露；双关例外分卡 |
| 代码 | 标志 / 行业按位置索引（E6f 教训） | `align_to_close` 一律先 reindex；列置换测试 |
| 代码 | 行业时钟（CURRENT vs TRADABLE vs ROLLING） | 三者分名；PIT 成员按 T；单成员 NA；thin 标记 |
| 统计 | 路由 = 另一种收益筛选 | 记录 A 不按收益增删；推导段跑 `routed` + `candidate_for_routing`；`consideration_ledger` 留全部考虑史 |
| 统计 | 卡数 / 参数多重性 | F-route / F-headline 全族；卡数与描述符与路径与学习步骤分别计；不设门 |
| 统计 | 后段只两段；2019+ regime 已知 | 两段分报、单年留一、去 15+16；边界全文 |
| 统计 | 随机参照被读成 p 值；匹配掉目标信息 | U / I 两层并列；`reference_tail_fraction`；退化对照标明 |
| 统计 | 均值 / 中位改号、全称句（E6g #30 / #32） | 算子与 n 必标、并报；全称句来自计数 |
| 统计 | 时间异质滑向事后编故事 | Q11 四备择事前写；T3 子样本可证伪 |
| 运行 | 两次记录拖时间线 | 记录 A v0 在 brief 即生效；闸期间跑 L / T 旧输入格与推导段 |
| 运行 | 线程配额、存储 | 先实测再定 worker；汇总 + 示例 |
| 解读 | 首次观察读成 OOS；"无效果"写成线级 | 边界全文；plan §10.3 结论模板 |
| 解读 | 路由失败被读成因子类别失败 | 迁移失败限父 × 位置 × 操作；未路由 ≠ 无效 |
| 流程 | 两套 final；plan v1.0 残留 | 本 brief + plan v2.0 唯一有效；v1.0 只归档；SHA 进 manifest |
| 宽松 | plan 的过程性"不得"被当阻断 | §0.2 六类硬约束外报告并继续；MODULE STOP 只限逻辑错 |
| 节奏 | 有没有把跑得快当约束 | 没有：七路线全参数格 + 竞争方向 + 三交互 + 全部对照 + 随机 256→1024、L 768+192+192、T 绝对人数全网格 + 32 seed × 2 N × 3 运行 + P16 560、bootstrap 2,000；时间线由两次记录决定 |

方向确认：headline = 母体需求驱动的路由（七条初始路线 + R0 增改）、推导段实验、一次用户登记后的首次观察；carried = L（期限 / 缓冲 / 实施）与 T（时间异质 / 人数 / P16）；不改池、不改生产、不开 E7；探索从宽（推导段全跑、无闸、卡数不限）、采纳只在 E7 + 用户过目；三份 REPORT 交用户与规划 session；判读由规划 session 写 REVIEW、更新线状态与 park 台账并续写复盘台账。
