# E6g —— 最终 brief（v1，2026-09-11）：headline = 34 键结构层（第四腿 / 换腿、腿变换、条件否决、网格边缘、四腿聚合）+ T0 输家解剖；carried = 续选缓冲与期限、40 键推导段准备；park 复核

用途：本文件是 E6g 唯一有效的执行文件。设计层最终版是 web plan `exec_briefs/plans/E6g_plan_web_final.md`（本地 SHA256 `e5402a66d0a2c41e6c87dc72876faee835b481d5a75b913b67e8a78db0f606c2`），执行端整份读，复制进 results 作 `PLAN_COPY.md`；**本 brief 未提到的细节按 plan 执行；两者冲突以本 brief 为准**。输入指纹：`E6g_proposal.md` SHA256 `79f5632dbb743d19ba894bcffb137419a18dee8fc2a6bbb205916ca3d7ea912d`；`E6f_REVIEW.md` SHA256 `1eda93b1e72fcbc85c69c8f42062bfdfed1c13aa9f598e9e5aad20885b4c3399`。前置：`E6f_REPORT_part1/2/3.md`、`E6f_REVIEW.md`、47 上 `results/20260910_0814_E6f_construction_selection_implementation/`（commit `08ded45` = 当前 HEAD）。先读 `00_协议.md`。

---

## 0. 一句话问题与设计结论

**问题**：在已经有资金流入信号的 I11 池内，当前 K/T/C 三腿核 + 否决的结构是否遗漏了 34 键信息集里能改善"谁被保留"的信息——加一条腿、换一条腿、用变化量而不是水平、只在特定个股状态下否决、把核挖深或挖浅、四腿聚合；成本线的有界问题是续选缓冲与持有期能否用较小的 gross 损失换取足够的成本节省；新键线只做推导段准备。

**设计结论**：按 plan 的任务图执行 `0 注册/源码/锚 → H0 仪器 → {T0-35, H1, H2, H3, H4, L, K/T0-74} → H5/B2 → B1 → C/D/归因/REPORT`，三次交付（part1 结构层、part2 成本/选择/账户/统计、part3 新键推导段）。探索从宽：不以单因子强弱、相关、正年数、t 值或同时带作准入门；统计量只作列；任何"无效果"只写子杠杆 × 适用域。**headline / carried / park 三态按 proposal §1.4**：headline 留 34 键结构层，40 键本轮只碰推导段，park 只收被推翻或无增量的结论。

### 0.1 相对 web plan 的采纳与调整（规划 session 决定；★ = 规划 session 自身错误，已按 47 源码核实）

| web plan 内容 | 处置 |
|---|---|
| 任务图、三态分配、H0–H5、B2、T0-35/74、L、K、B1、C、D、Q1–Q11、测试矩阵、交付结构 | **全部采纳** |
| §0.3 对 proposal 的 16 条修订 | **全部采纳**。属于规划 session 错误且已核实的：★ **K/T/C = `conditional_turnover` / `turnover_volatility_60d` / `CVR_20d`**（`e6e_core.py` 第 26 行），proposal 把 C 当成 cr20，并把 CVR_20d 列进第四腿候选；`U35 = get_default_factor_specs()` 的 34 + `intraday_cvr_1d`（E6e 研究 spec），`J_KTC = 32`，不是 31；★ **`lclose` = 数据源 `preClosePrice`（交易所前收盘价）**，E1 的 `adjust_factor` 正是由它推得（PROJECT_STATUS §4.9），故 `open/lclose`、`close/lclose` 类表达式与复权一致，proposal 把 gap 族 / `overnight_ret` / `positive_day_ratio_5d` 判为"除权污染"是错的；只有 `close/close.shift(w)` 路径（`cum_return_w`、`volume_momentum_divergence` 的价格项、`recent_high_20d` 系）未复权；★ E3 单因子表是 **6bp**（`cost_bp_bilateral=6.0`），8bp 由同日 turn 转换对账，不硬锚；★ R2 `KT_mean@30|C:k5+cr5:k10` 是 E6b 样本内研究参照，不是 v2 交付（v2 = `A4b_CVRv5` 系）；★ `Δ0 = 原腿`、`ts-z 窗→∞ = 原腿` 两个伪端点删除，按 plan §2H2 的正确自测；★ 缓冲带"已持有即保护、被否决即出"与 H5 批次不兼容，改为 plan 的"形成日续选"定义 |
| "第四腿 / 换腿从未测"的范围 | **收窄**（规划 session 09-11 核 `E6d_REPORT.md` / `E6e_architecture.md`）：E6d 已穷举 12 个候选的两因子合成（依赖 / 交集 / 均值，528 格）与 6 个单尾 Z（CVR_20d、cvr_1d、ci5、cr5、cr20、max_abs_return_10d）作**第三阶段过滤**（相对 / 绝对 k5 / k10，10 父 × 162 格）；E6e 只以 C=CVR_20d 作等权第三腿建 KTC_mean / TC_mean。**从未测的是：等权 rank-mean 三腿核内换席、第四腿、34 − 12 = 22 个从未进过任何合成的键。** H1 的换腿结果与 E6d 表 F/G 并排读，不当新发现 |
| pool0 的观察窗与 age | **修正**：`build_observation_pool(signal, obs_window=5)` 用 `signal.shift(1..5)`，形成日距最近触发的 age ∈ {1,…,5}，不是 0–4。H3 的 age 状态分 `1` 与 `2–5`；T0 的 age 轴同 |
| I11 信号成分 | **补充**：`define_i11_signal` 用 `CMF_20d`（pct ≥ 0.80）、`cum_return_5d`（0.25–0.55）、`intraday_ret`（pct < 0.70），三者在 pool0 内分布都被信号截断，不只 CMF_20d；K1 注册表对 `intraday_ret`（NEW40）与 cr5 否决同样标 `signal_component_truncated` |
| pool0 硬约束 | **补充为池事实**：`apply_hard_constraints(obs, data, feats, min_mcap=0)` 只放开市值，`is_open`、20 日均成交额 > 2,000 万、上市 ≥ 20 日仍生效；K3 的流动性否决与 ADV20 规则在这个地板之上做，REPORT 写明。**涨跌停过滤名义化**（§1.3）：pool0 可能含涨跌停日，可成交性只在影子账户与标志层处理；阶段 0 加"形成日 pool0 成员触及涨跌停"计数列 |
| 随机路径 128 + 128（H3、K2、T0 伪输家） | **采纳条数，改存储**：只落每路径的汇总统计（gross/pos/turn/net/impact 年化与逐段）与固定 8 条路径的日账本，不落全部逐路径日账本（E6e `random_daily/` 183 GB 教训）；某族 wall 时间实测超 24 小时可降到 64 条并报 MCSE，不低于 32，coverage 记录 |
| H2 `delta20` / `zprior60` 在 `legacy_all` 下每段再失 20–60 个有效日 | **补充**：H2 三种变换同时在 `history_warmed` 支持集上跑（`warm_start` 260 日历日），主读数在两支持集的共同形成日上 |
| 缓冲 L 与 L-X | **采纳**；L-X 提前退出用 E6f `e6f_c2.shadow_account` 的账户模型改造，恒等式（b0 + 不提前退出 = 同影子模型的源 H5）不过 → 该小块 LIMIT，不影响 L 主实验 |
| 计数 1,544 / 1,100 / 600 | 由真实注册表生成；**不符出 diff 继续跑**，不凑数、不删格 |
| 交付顺序与 REPORT 分工 | **采纳** plan §4.3 三份；**part1 已含 H 配置的冲击括号列**（`e6f_c1` 的 sqrt/lin 括号可直接复用），影子账户放 part2 |
| `line_state_proposal.md` / `park_ledger_delta.md` | 执行端出**草稿**（来源 / 适用域 / 已测子杠杆 / 不确定性 / 建议状态 / 恢复条件），规划 session 在 REVIEW 定稿，用户定 |
| 全局 worker ≤32、父进程验收、状态表 | **采纳**（`00_协议` 第 3 条） |

### 0.2 "设计尽量宽松，不要太严格"（用户 09-11）在本 brief 的落法

- **硬约束只保留六类**（违反即停并写 BLOCKERS）：① 取数 `end_date ≤ 20260327`（走 `e6f_core.guarded_load`），不读 E7、不建延长缓存；② **40 键守卫**：任何带 NEW40 血缘的收益 / 持仓 / 交易 / 成本 / 标签 / 学习产物只允许 2010-2014、2015-2018 两段，`label_end` 与估值端点 ≤ 2018-12-31，T0-74 的产物不进 H/B（H manifest 在读到 T0-74 结果前冻结）；③ 四个地基文件只读，七个 `e6e_*.py` 与十九个 `e6f_*.py` 不改（新代码一律 `e6g_*.py`），`results/` 不删，不改 I11 / pool0 / clean / 生产 DEV / 生产 H5 / 8bp 主口径 / 生产 v2；④ 并发 ≤32、BLAS 单线程、绑 socket 1、父进程验收后写 DONE、状态表求和 = 登记总数；⑤ git 只 whitelist add、不 `git add .`、不混入旧 untracked；⑥ 文档不出现登录信息与主机地址。
- **其余 plan 里的"不得 / 必须"一律改读为"报告并继续"**：锚点不符报最大差、日期、原因，记 WARN；注册表计数不符出 diff；MODULE STOP 只用于**符号 / 时间 / 域的逻辑错**（未来函数、成本重复扣、账户资产凭空消失、active-leg 或有效域错、把 pool 级与 Q 内排序混用）；资料缺失 → 模块 LIMIT，其余继续。
- **网格不缩、也不加严**：plan 打开的格全跑；plan 自设的边界（z 只 60 窗、五个状态变量、α 五点、b 四点 + relative1.5）保留；执行端若顺手可加的格（如 α=1/16、状态三分层）可作**附加列**登记，不进主表、不替代主表。
- **读表无闸**：任何统计量、成本翻转、单段为负、随机参照不显著，都是结果，不触发中止、不触发删格。
- **实施细节留给执行端**：模块划分、缓存设计、分片方式、并行顺序按 plan §4.1 建议但不强制；"名称可适配，字段不可遗漏"。

---

## 1. 起点确认与契约

### 1.1 起点
- 47 `project_core` HEAD = `08ded45`（E6f）；工作树有三个 2026-05 的 untracked 文件（`full_a_single_factor.py`、`sharpe_credibility_diagnosis.py`、`single_factor_groups.py`），不动、不 add。
- E6f 产出目录 `results/20260910_0814_E6f_construction_selection_implementation/`：`daily/`（U0-broad 与 UA 的日账本）、`domain_U0.csv`、`feature_registry.csv`、`selector_registry.json`、`study_manifest.json`、`comparison_registry.csv`、`B_*`、`C_impact/`、`C_shadow_accounts/`、`D_*`、`checks/`、`limit_register.md`、`source_corrections_E6f.md`、`preregistration.md`、`run_manifest.json`。E6e 目录 `results/20260906_1300_E6e_architecture/`、E6c 目录 `results/20260905_0633_E6c_holding_horizon/`（`e6f_core.E6E_DIR / E6C_DIR`）。
- 源账本口径沿 E6f brief §1.3（`compute_calendar_pnl`：`actual = W.rolling(5, min_periods=1).mean()`，`ah = actual.shift(2)`，`gross = port − bench × position`，`turnover = 0.5Σ|Δah|`，`cost = turn × bp/1e4`；停牌与复牌当日收益 NaN；`load_segment` 无预热，每段头 19 天 `clean` 全零 → 76 个基准全 NaN 日 = 4 × 19）。
- 阶段 0 先更正 E6f 遗留：`source_corrections_E6f.md` §5 与 `coverage.md` 的"段内零仓位 0 天"（E6f_REVIEW §1.3：4,446 配置 > 0 天，(45,45)/(55,55) 两段式核 2010-14 段 246 / 67 天），写进 `revisions/`，不覆盖旧文件。

### 1.2 数据与生产锁
读取入口日期 ≤ 2026-03-27（`guarded_load`）；公共缓存目录只读（沿 E6f 影子缓存 `WCACHE`）；不读 E7 目录、不建延长缓存、不查询任何更晚收益；目录元数据与 manifest 的源最新日期可以读。不改池、不加原始因子进生产、不改 I11、不改生产 DEV、不改否决方向；全部研究变体（新腿、变换、条件否决、缓冲、H≠5、selector、影子账户）独立命名，不进交付、不进公共库。

### 1.3 契约（规划 session 2026-09-11 已按 47 源码核；执行端整段读函数体复核并写 `engine_contract.md`，不符处单列）
- **键集合**：`C.get_default_factor_specs()` = 4 个自定义（`reversal_skip1`、`parkinson_vol`、`abn_turnover`、`cmf_change_neg`）+ `CONFIRMED_FEATURE_NAMES` 30 个 = **U34**；`e6e_core` 加 `intraday_cvr_1d = close/vwap − 1`（`FCVR1`）= **U35**；`FK, FT, FC = 'conditional_turnover', 'turnover_volatility_60d', 'CVR_20d'`，`FCR5/FCR20/FCI5 = cum_return_5d / cum_return_20d / cum_intraday_ret_5d`；方向 `K.HB[f]`（roles.csv `worst_pooled == 5` → 高值坏）。**NEW40** = proposal 附录 A 的 40 个名字；`CVR` 与 `intraday_cvr_1d` 公式别名（`(close−vwap)/vwap` vs `close/vwap−1`，浮点不必逐位）；`CVR_5d` E6f 已测。
- **pool0**：`base_pool = get_base_pool(data)`；`signal = define_i11_signal(feats, base_pool)`（pool 内 pct：`CMF_20d ≥ 0.80`、`cum_return_5d ∈ [0.25, 0.55]`、`intraday_ret < 0.70`）；`obs = build_observation_pool(signal, obs_window=5)`（`signal.shift(1..5)` 之和 > 0，故 **age ∈ {1,…,5}**）；`pool0 = apply_hard_constraints(obs, data, feats, min_mcap=0)`：`is_open == 1`、20 日均成交额 > 2e7、`close` 非空计数 ≥ 20 日；市值不设限。**涨跌停过滤在源码里是名义的**：`data` 含 `limit_up/limit_down` 时条件写成 OR（`close < limit_up−0.01 | close > limit_down+0.01`，涨停行或跌停行都能通过；若字段是 0/1 标志则更是恒真）；`data` 缺该字段时回退到**未复权** `close/close.shift(1)` 的 ±9.8%（会把除权日误当跌停剔除）。`data_loader` 的字段表没有 `limit_up/limit_down`，规划 session 判断实际走的是回退分支——**阶段 0 核实际分支并计数**（两分支各自剔掉多少形成日 × 票），写进 `engine_contract.md` 与 `source_corrections_E6g.md`；地基文件不改。`clean = base_pool ∧ mature(20)`，北交所列置 0。基准 = `dr.where(clean==1).mean(axis=1)`，`dr = C.vwap_daily_return(data, K.ADJUST)`。
- **因子与特征**：`feats = calc_all_daily_features(data)` 一次算全部 70 键并挂在 `S.feats`（`e6e_core.load_segment` 与 `e6f_core.build_segment` 都是）；新键进研究 = 加注册表条目，不写新计算代码；`history_warmed` 支持集下特征在 `S.wdata` 上重算。`lclose` = `preClosePrice`；`cum_return_w = close/close.shift(w) − 1` 未复权；`C.adjust_factor(data)` 是 E1 的 lclose 法复权因子。
- **分组与合成**（`e6f_core`）：`qcut_group(n, g)` 直接调 `pd.qcut(rank('first'), g)` 并记忆化；`keep_mask_dense(P, p0c, pctkeep, g=None)`：有值票 `< 3g` 当日空仓，`g = P2G[pctkeep]`，`keep_g = round(g·pct/100)`；`P2G = e6e_core.P2G ∪ {15: 20}`；`drop_mask_dense(P, p0c, k)`：有值票 `< 3k` 当日全池皆剔；`combine_dense(Ps, how)` 取各分量日期交集（`_day_ok`）；**`wcombine_dense(Ps, ws)` 有理权重合成，零权重分量真正 bypass**（H1 的 α 权重与 B2 的 α=0 端点直接用它）；`common_domain(Ps)` = `paired_common_domain`；`coretrim_matchN(S, parent_P, parent_mask, target_n)`；`eqpos_pair`。
- **中性化**：`neutralize_by_mcap` 逐日 OLS 残差（log 市值），有效票 < 10 返回原值；`precompute_neutralized_factor` 池 < 6 跳过；E6f 另有 `NI/NSI`（行业）路径与 `NSI_METHOD='svd'`。
- **DEV**：`w = min(1/n, 0.01)`，行业 `cap = clean 行业占比 + MAX_IND_DEV`，等比缩减、无下限、不归一。
- **支持集**：`legacy_all`（无预热）与 `history_warmed`（`warm_start(pname, calendar_days=260)`，只预热因子源数据，`clean/pool0/基准` 冻结，每段头 19 天仍空）。
- **成本与容量**（`e6f_c1`）：`ADV20 = amt_open.rolling(20, min_periods=10).mean().shift(1)`（交易日口径；`ADV20c` 含停牌 0 为敏感性）、`ADV60`、`SIG20/SIG60`；括号 `sqrt: Σ|q|^1.5 σ20/√ADV20 → c = κ√A·bracket`，`lin: Σq²σ20/ADV20 → c = (κA/√p0)·bracket, p0 = 1%`；`LOWADV = ADV20 全市场分位 < 0.20`；`amount` = 数据源 `turnoverValue`（元），`mcap` = `negMarketValue`（元）。
- **影子账户**（`e6f_c2.shadow_account(W, mode∈{ideal, X0, X1}, capital='constant_notional', A_notional, bp, unknown_tradable)`）：现金 / 持仓 / 费用逐日账，买不成留现金、卖不掉留库存；Xideal − Xengine = 账户模型差（报出而非错误）。
- **选择回放**（`e6f_b2_select`）：`SPLITS = 2012/2014/2016/2018/2020/2022 年末`；`RULES = S1–S6`，`S1-cost / S6-cost`（冲击后训练评分）、`S_meta`；年度 walk-forward `YEARS = 2014–2025`；全部标 `fixed_hindsight_library`。
- **E3 口径**：`compute_forward_5d_excess(data, base_pool, hold_days=5, adjust=True)` 与 `event_study_analysis_cached(neu_cache, forward_ret, filtered_pool, n_groups, name)`（`group_means_bp`）；E3 单因子表 `cost_bp_bilateral=6.0`。
- **E6d 事实**（换腿的对照读）：两因子合成 12 候选穷举 528 格；第三阶段 Z 6 个 × {相对, 绝对 k5, 绝对 k10} × 10 父 = 162 格；"相对不优于绝对"、"第三因子增量在生产父与最差父上 +0.65～+1.26，top 父上约零"。

### 1.4 事前登记
在首次新收益评价之前落盘 `preregistration.md` = 本 brief §11 全文（plan §2E 表 + 共同声明，逐字）+ §0.1 的修正附注（age 1–5、I11 三成分截断、pool 地板、E6d 对照读）+ 实际时间 + 输入 / 代码哈希 + 源 ID 映射；修订另起 `preregistration_amend_<日期>.md` 并标是否已看过收益。**不改写编号与问题**（E6e 曾重写，禁止）。

---

## 2. 阶段 0：注册、源码核、锚（plan §1.1–1.6 + §2H0 前置）
- 读 `PROJECT_STATUS.md`、`00_协议.md`、memory 入口、E6f brief 与三份 REPORT、`E6f_REVIEW.md`、`limit_register.md`、`coverage.md`、`source_corrections_E6f.md`、`preregistration.md`、`run_manifest.json`；冻结四地基、七个 e6e、十九个 e6f 的 SHA 与运行库版本；写 `source_manifest`。
- **注册表**：`registry/` 含 U34 / U35 / NEW40 / 剩余 8 键资料索引（只列清单与来源，不实现）；每键：源码定义（读函数体）、窗口 / min_periods、单位、PIT 可用性、是否全市场占位（`gap_vs_sector`、`gap_rank_in_sector`）、信号重叠（`CMF_20d`、`cum_return_5d`、`intraday_ret`）、公式别名 / 排名别名 / 真实路径别名、raw 与处理后 `nunique / tie 占比 / 最大 tie 块`、稳健重尾量（`q99(|x−median|)/MAD`、缺失 / 无穷率、最大绝对值、OLS leverage；MAD=0 写 NA）、复权敏感（按 plan §2H0-d 三类逐式）、历史是否算过收益相关量（访问史标签七种，plan §2K1）、本轮 `feature_date / label_end` 上界。`mcap_rank` 标 `diagnostic_only`。**涨跌停计数列**（必交）：形成日 pool0 成员触及涨跌停的数量与比例（FundamentalTL `limit_up / limit_down / flag_buy / flag_sell` 标志；覆盖不足记 UNKNOWN），逐段逐年，供 T0 协变量与 K3 / L-X 解读。
- **去重元数据**：`raw_name / canonical_formula_id / transform / input_scale / neutralization_domain / sign / active_legs / weights / tie_policy / selector / keep / veto / H / buffer / provenance / support`；同名不同处理 = 不同 ID；不同名同路径可复用计算但保留全部 descriptor→path 映射。
- **方向**：统一为 `bad_pct`（越高越该剔）；反向按反序构造并测奇偶 / 并列，不默认 `1−pct` 与源逆序逐位等价；所有方向都报。
- **固定展示组**（plan §1.3 表）：R1 `KT_dep(50,50)|C:k5` = `A4b_CVRv5`（生产 v2 参照）、R2、A03–A10、T25、Blend3（A03/A06/A08 目标权重各 1/3，源 DEV 各自先算，**不对合并名单再 DEV 或归一**；gross/pos 等于成员平均，turn/net/impact 合并后重算）。只是展示组，不是准入名单。
- **40 键守卫**：实现为表达式 DAG 上的血缘标签 + 段 / `label_end` / 用途检查（`use_type ∈ {label, shape, holding, trade, cost, outcome_cluster, selection}`）；自测四条（重命名新键、由新键拟合的树、2018 跨年标签、2019 只建持仓不读收益）必须被拒，`cvr_1d` 原式的历史使用不被误封；`checks/` 落证据。
- **锚**：E6f 63 源锚与 E6e R1/R2/A03/A06/A07/A08 逐日 `gross/pos/turn/net8`（同源码路径求字节一致；独立浮点实现 `atol = rtol = 1e-10`，不符报最大误差 / 日期 / 原因，WARN）；E3 单因子表用 6bp 复现后转 8bp 对账；`interior_nopos` 复现 E6f_REVIEW §1.3 的 246 / 67 / 4（先找到确切 cfg_id，不把 247 的全体最大值与某条 246 混为一行）；逐日原因码（池空 / 特征缺失 / 有效样本不足 / 3g 门槛 / 否决全剔 / 批次耗尽）；`avg_nh_calendar` 与 `avg_nh_active`、`target_n` 与 `live_n` 各算，聚合算子逐字段登记。
- 时点：T 收盘形成目标，T+1 VWAP 交易，首个完整收益日 T+2；ADV / σ 最晚用执行日前日。

---

## 3. 块 H0：分组、平局、输入与复权（plan §2H0 全文执行；本节只列本 brief 的固定项）
- **三个具名 selector**：`SRC`（源 `P2G` + 源分箱 + 3g 门槛 + fallback）、`QEDGE`（源中性化 / 有效域 / 分箱调用不变，只不把"需表达成 g 组"变成 3g 空仓；有效样本 < 6 不形成目标，6–9 沿源中性化 fallback 并标记；共同可运行日 mask 与 SRC 一致）、`RANKBUDGET`（active 有效域内稳定排序保留 `floor(n·d/100)`，d 连续；不足 1 则空）。**QEDGE 复用源 `pd.qcut` 调用与 `retbins=True` 的边界，不用 NumPy 闭式重造**（`qcut_group` 的 1 ULP 教训）。
- **固定仪器桥**：`KT_dep / CT_dep` 的 (45,45)、(50,50)、(55,55)、(65,65) 裸核及其 `C:k5+cr5:k10`，SRC / QEDGE 并排；H1–H5 中所有出现 3g-only 阻断的 descriptor 自动补 QEDGE（不按收益决定）；H4 加密格用 RANKBUDGET，原映射深度保留 SRC / QEDGE 桥；`SRC→QEDGE→RANKBUDGET` 逐开关账，影响集 = "有任一不同 vintage 仍在账内"的日期。
- **平局**：源 `rank('first')` 保留；`WHOLE_TIE` 施于**实际排序分数**（中性化残差），tie block 按平均秩整块落箱，报人数偏差，常数全 tie 标 `constant_score`；`RANDOM_TIE` 同分块内 `hash(seed, date, stock)` 64 seed，持续版 `hash(seed, block5, stock)` 64 条；只对实际影响 cutoff 的 tie 扩展；原二值 / 计数变量另展示原始类别的收益与持仓贡献。
- **输入变换**：U35 主路径不变；NEW40 非诊断键推导段并排 `RAW→NS→rank` 与 `pool_rank(raw)→NS→rank`；源 OLS 病态出 NaN 时主锚保留源语义，另给 `NS_safe` wrapper（退回原值并打标）。
- **复权**：按 plan §2H0-d 逐式分三类（应恒等 / 可能不同 / 未知）；`C = CVR_20d` 是同日比值的 20 日均值，调整抵消，**不再造"复权 C"**；`B = cum_return_w` 继承 E6f 已注册的 `ADJUST` 研究修正；量因子无可靠股本 / 企业行动资料则只披露不猜系数。

## 4. 块 T0：输家解剖（plan §2T0 全文执行）
- 只用 2010-2014、2015-2018；主标签严格复用 E3 的 `compute_forward_5d_excess`（bench = pool0 等权、已复权；plan 写的"T+1 VWAP 入、T+6 出"是假设，阶段 0 读函数体把实际入场 / 出场时钟写进 `engine_contract.md`）；若 E3 是日收益累加而非端点复利，源版保留并另报端点版，命名不混；**5 日标签完整端点不越 2018-12-31**；段尾与停牌 / 未知终值单列。
- 主分位标签 = 形成日 pool0 最差 / 最好 20%（10% 敏感性）；另报负绝对收益、负 pool 超额、对当前完整策略（R1/R2/A06/A08）的真实 gross 贡献。事件计数三账（每日形成机会 / spell 首次进入 / **age = 1…5**）；主估计按日期等权，另报 DEV 形成权重版。
- 三层对象：pool0 全体；R1/R2/A06/A08 最终保留集中的输家；这些策略剔除的赢家。覆盖 = 形成日该原始规则是否剔除 / 低排；`lift` 报分子、分母、日期支持；常数控制（ST、开市标志）列出但不计发现。补当前策略剩余损失的资本贡献（按源 rolling 权重逐票 / 行业 / 年份对 `Δgross vs R1/R2`）；oracle 只描述损失上界。
- `T0-35` 与 `T0-74` 分开运行并保存 DAG；聚类专用坐标 / 标准化 / 填充只由 2010-2014 拟合、2015-2018 固定应用；层次聚类 `1−|Spearman|` 只作同源整理；k-means k∈{3,4,5}、固定 seed、`n_init=20`、日期等权 sample_weight，再跑去掉 K/T/C/cvr_1d/cr5 直接坐标的版本；深度 ≤3 树只作描述，`min_leaf` = 总日期权重 5%；**128 条伪输家路径**（同日同人数随机、同日同行业人数匹配、行业 × 市值三档条件版），每条重跑全部预设统计；画像区间按日期 block bootstrap。
- 输出"模式 × 在用腿 / 否决 × 剩余损失 / 错失赢家"覆盖矩阵；两推导段同号、逐年符号、伪参照区间都是列，**没有"≥6/9 年即稳定"硬标签**。T0-35 只改变 H1 的解释分层，不改变执行；T0-74 只给 E6h 草稿，**H manifest 在读到 T0-74 结果前锁定**。

## 5. 块 H1–H5 与 B2：34 键结构层（plan §2H1–2H5、§2B2 全文执行）
- **H1**（plan §2H1）：母体 A06 `KTC_mean@25|cvr_1d:k10+cr5:k10`、A07 `KTC_mean@30|cvr_1d:k10+cr5:k10`；J ∈ J_KTC（32，由注册表生成）× 两方向 × {第四腿 α∈{1/8, 1/4}（`score = (1−α)·mean(K,T,C) + α·bad_pct(J)`，用 `wcombine_dense`）, 替 K, 替 T, 替 C} × {原完整否决栈, 无否决裸核}；R2 的 KT 核加第三腿桥 J ∈ J_KT（33，含 C）× 两方向 × α∈{1/8, 1/3} × 两否决状态（α=1/3 与同深度 KTC 源构造对齐）。原始描述符 1,544（去别名前、未含对照）。**同名腿 / 否决 2×2**（至少 J = cvr_1d、cr5；R2 桥中的 C）：`原核无焦点否决 / 有焦点 / 加或换 J 后无焦点 / 有焦点`，四格保留，不预判冗余。配对与归因：Δ vs 直接母体、vs 对应裸核、vs R1/R2/Blend3；共同有效域 Δ（`common_domain`）与 `refit_common` 分标；当日原父分数上同人数预算选股（真的重建 mask→DEV→引擎）；同人数反向 J；新选入 / 被替出集合的形成日固定权重 fwd 剖面（1/3/5/10/20 日，只允许区间内完整端点）；`Δgross` 按日期 / 行业 / 个股分解。候选按 T0-35 覆盖矩阵预分层（缺口 / 冗余 / 无关）与 |ρ| 标注，只作读表结构。**E6d 对照读**：换腿格与 E6d 表 F/G 的同 J 两因子 / 第三阶段结果并排列出。
- **H2**（plan §2H2）：K/T/C 原始分量在个股完整已允许历史上做 `identity / delta5 / delta20 / zprior60`（`(F_t − mean(F_{t−60..t−1}))/std(ddof=1)`，≥30 个有效点，std=0 → NaN），再取当日 pool0、NS、方向 rank；不在池内截断后 rolling。三种非 identity × 两方向 × {替对应活跃腿（R2 无 C 则 `not_applicable`）, 加腿 α=1/8 与 α=1/(原腿数+1), 作额外否决 k∈{5,10}} × A06 / R2；与已有焦点重叠时同样给无焦点父。**两支持集**：`legacy_all` 与 `history_warmed` 都跑，主读数在共同形成日。正确自测：identity = 原值；Δ0 = 0；常数 F 的非零 lag 差分 = 0；z 对正比例平移不变；历史常数 z 无定义；未来扰动不影响过去前缀。
- **H3**（plan §2H3）：母体 R2/A06/A08；焦点 z ∈ {cr5:k10, cvr_1d:k10}；先构 Q = 移除同公式同窗口焦点规则后的母体（R2 研究 cr5 时 Q 只留 C:k5；研究 cvr_1d 时 Q 不变 = R2；A06 研究 cvr_1d 时 Q 留 cr5:k10、反之留 cvr_1d:k10；A08 同 R2 逻辑）；pool0 内固定焦点毒尾 `T_z,t`，条件策略 = `Q_t \ (T_z,t ∩ S_t)`；S = 全集锚无条件、S = 空集锚 Q。状态五项：K 的 NS 分数、T 的 NS 分数、log 市值、`realized_vol_20d` 的 NS 分数（前四项 pool0 内 `rank(average, pct)` 按 ≥0.5 / <0.5 分层，边界归高侧）、**I11 age ∈ {1} vs {2–5}**；缺失状态默认保留无条件焦点规则并报回退贡献。每状态高 / 低侧启用；A06 上两焦点的四种共同开关。三种对照分名：`Tox-matchN`、`Core-matchN`（DEP 用源阶段顺序的合法条件分数）、`Random-state`（同日同行业内重排状态标签，报剔除数变化；另有匹配真实被剔行业人数的随机删除）；128 条独立日路径 + 128 条 5 日 hash 持续路径，逐路径费用 / 冲击，报 MCSE；排序恒等自测（pool 级 rank 与 Q 内 rank 的最差 m 只相同）。
- **H4**（plan §2H4）：**H4-a** 四核 `KT_mean / KTC_mean / T / KT_dep`（K 第一阶段固定 50%，第二阶段保留 2d%）× `d ∈ {15,20,22.5,25,30,35,40,42.5,45,47.5,50}` × 两否决各 `k ∈ {OFF,3,4,5,10}`（KT_mean / KT_dep / T 用 C=CVR_20d + cr5；KTC_mean 用 cvr_1d + cr5），4×11×25 = 1,100 原始描述符，RANKBUDGET 主地图 + 原深度 SRC / QEDGE 桥；DEP 第二阶段 = 100% 时去掉无效重排 / 重 NS 但保留端点对照。**H4-b** KTC 母体角落邻域：`K_MA 窗 {1,2,3,5,10}` × `T 窗 {20,30,40,60,80}` × `B 收益窗 {3,5}` × 深度 `{25,30,35}` × v1 与 B 的 k 各 `{5,10}` = 600；K 分母 ε 固定源 `1e-4`；B 主路径 raw，另 E6f 已存在的 adjusted 对照；`min_periods` 按 E6f 同一变体规则（`mp(w)`）；阶段 0 先精确找回 E6f 两个正角点的真实 cfg。**H4-c** 每节点报参数距离、mask Jaccard、目标权重 L1、实际交易距离、最终人数 / 仓位差、配对 Δgross / net8 / impact；端点只有单侧邻居，不套"≥70% 邻居"平台公式。
- **H5**（plan §2H5）：对 H1 **全部** KTC+J 四腿集合（两深度、两方向；不用 ρ 或早段收益预筛）比较 mean / median（四数中间两个均值）/ worst(max) / `2-of-4`、`3-of-4` 自然投票 / 同人数聚合控制（在四腿共同有效域选与 mean 核同 N，再上同一完整否决；同票先 mean score 再固定 hash）；完整栈与裸核控制配齐；`trimmed_mean` 四腿 = median 自动登记别名；同人数两种定义（核选名数相同为主；否决后最终数相同另列，不补回毒票；refill 策略本轮不做）。
- **B2**（plan §2B2）：H1 加第四腿集合全覆盖：α 补 `{0, 3/8, 1/2}`（与 1/8、1/4 成五点曲线；α=0 真实剔除 J 有效性要求）；J 原始分量追加因果 MA3 / MA5（min_periods 2 / 3）在 α=1/4、两深度、两方向、完整 / 裸核下运行；全部进 B1 的 EXPANDED 域。
- 全部配置带 `interior_nopos`、`avg_nh_calendar / avg_nh_active`、`target_n / live_n`、逐段、最近一段单列、8bp 与 12bp、冲击括号（§9）。

## 6. 块 L：carried —— 续选缓冲与持有期（plan §2L 全文执行）
- **L1 主实验 = 形成日续选**：七个原子配置 `{R1, R2, A03, A06, A07, A08, T25}` + Blend3 成员级缓冲。形成日目标 `N_t`、无否决核心域 `B_t`、毒尾 `T_t`；既有名单 `I_{t−1}` = 上一形成日缓冲目标名单；放宽核心域 `B^b_t`（均值 / T 核按原排序放宽 d 到 `min(100, d+b)`；DEP 核第一阶段 K 闸不变，只放宽第二阶段 T 保留比例，b 单位为第二阶段百分位点，表中与均值核区分）；`U_t = N_t ∪ [I_{t−1} ∩ B^b_t ∩ pool0_t \ T_t]`；`b ∈ {0,5,10,15}` 及 `relative1.5`。两预算：`L-loose`（U_t 全体重新 DEV）与 `L-matchN`（`m_t = |N_t|`，旧成员按当日原排序优先留到 m_t，不足以 N_t 新票补足；m_t=0 则不发新目标）。**b=0 直接返回源 N_t 与目标权重**（精确复现源账本），各 relaxed 域的 b→0 一致性仍另测。形成日目标权重送同一 H5 批次引擎：被毒尾判中的票不获新批次，已有批次照源规则到期。报每批次年龄、同一股票连续持有天数、反复续选次数。
- `actual_incumbent` 对照（R2/A06/A08、b=10）：I 由 T 收盘已实际执行的未到期批次成员定义，执行时钟从源账户取。
- **L1-2 对照**：自身 b0、同人数 L-matchN、现有深度梯子；低频刷新参照（R2/A06/A08 每 {2,3,5} 日形成一次，所有日历相位都报，间隔日检查资格不续选失格票）。**L-X 提前退出小块**：只 R2/A06/A08、b∈{0,10} 的 L-matchN，源影子账户两开关（保持原批次到期 / 焦点毒尾触发后下一可执行 VWAP 提前卖出）；b0 + 不提前退出先与同影子模型的源 H5 一致；买不到留现金、卖不掉库存继续计价；恒等式不过 → 本小块 LIMIT。
- **L1-3 Blend3 缓冲**：A03/A06/A08 分别缓冲后按 1/3 合并目标权重执行；另报三账户各 A/3 的资本一致基准。
- **L2 期限**：七原子 + Blend3 在 b0 扫 `H ∈ {3,5,7,10,12,15,20,30}`；R2/A06/A08 追加 `L-matchN, b=10 × H{5,10,20}`；主口径沿 SRC 权重与批次预算；共同形成日支持集、段首 ramp-up、段尾未完成持有、`history_warmed` 分列；端点最长 30 且 ≤ 2026-03-27，不足则截尾，**禁止读 E7 补足**。保留 E6c 的"早期日龄权重变化 + 晚期收益贡献 + 交易成本差"分解并另扣冲击差。不选生产 H。

## 7. 块 K：carried —— 40 键准备（plan §2K 全文执行；只用推导段；全部 `exploratory`；40 键守卫全程有效）
- **K1**：沿附录 A 40 个名字（不另发明"剩余 8 个"清单，只索引资料）；每键访问史标签七种（`previous_outcome_seen / newly_computed_expression / same_formula_alias / related_information / feature_only_seen / new_outcome_first_read_in_this_project / economic_role_unmeasured`）；`first_read ≠ 独立 OOS`；`gap_vs_sector / gap_rank_in_sector` 沿源全市场含义；`CMF_20d`、`intraday_ret`、`cum_return_5d` 标 `signal_component_truncated`，照测，解释注明截断。
- **K2**：40 键 × 双方向 × k{2,5} 单因子（E3 口径：5 组形状、1/3/5 日逐日 / 累计回报；未形成五个非空组时报实际类别与人数）；40 键 × 双方向 × k{5,10} 叠 R2/A06/A08 作否决；RAW / RANK 输入均跑；经济上不同的价格调整变体均跑；WHOLE_TIE / RANDOM_TIE 按 H0 触发。每否决配父、同人数 core、同人数反向、I-IID 解析期望 gross/pos；随机路径 128（含同行业人数匹配；5 日持续优先级 128）逐路径费用 / 冲击，**只存汇总与 8 条示例日账本**。`mcap_rank` 诊断行。
- **K3 park 相关小块**（推导段，状态保持 park）：资金流 `CMF_20d` 与 `cmf_change_neg` 同父双方向 + 形状；快量能 `volume_ratio_1d/3d/5d`、`amount_ratio_1d` 与 abn 同父 / 同人数；第三轴由 K2 在完整母体上覆盖（不重复计）；昼夜路径 `positive_day_ratio_5d`、`intraday_ret_consistency_5d` 与 skip1 / cr5 并排；流动性 `amihud_daily` MA{1,5,20}（min_periods 1/3/10）、`amihud_ratio_5d_20d`、`amount_ratio_1d`、`turnover_5d` 双方向 k{5,10} + 执行前 ADV20 池内低端 5%/10%/20% 剔除（容量规则，pool0 不变；**pool0 已有 20 日均成交额 > 2,000 万地板**，写明）；共同成分后相关只作早段描述；hump 只报形状与误差，不进留中段搜索。K 成本只计推导段；金额单位核为元（`amount×1e−6` = 百万元缩放须映射回元）。
- **K4 E6h 登记草稿** `E6h_registration_draft.md`：列 `经济假设 / 失败模式 / 机制来源 / 推导段来源 / 表达式 / 方向 / 角色 / 合适母体 / 可能失效原因 / 反向控制 / 数据依赖 / 历史见过结果的范围 / 下一轮允许评估域`；约十多个精简建议但不硬裁到"≤6 轴 × ≤3 键"，全部 40 键附完整角色记录与未测项；因果语言一律写"假设"；**新键 2019+ 的开关本轮保持关闭**。

## 8. 块 B1：扩展结构域内的选择复验（plan §2B1 全文执行）
- 域：`OLD = E6f 冻结 U0-broad`；`EXPANDED = OLD ∪ H0/H1/H2/H3/H4/H5/B2 全部经济配置`（只 `hold_days=5` 的合法静态结构；排除随机控制、oracle、K 与 T0 学习策略、只用于会计的 matched-domain 控制；SRC/QEDGE/RANKBUDGET 作不同 selector 登记；L 的 H 变体与 stateful 缓冲不进本次 B 域）。**新域按构造定义，不按表现定义。**
- 规则复用 E6f 实际 `S1 / S3 / S4`（源同分、权重、族定义、日期、现金处理从 E6f brief 与代码读）+ `S1-cost`（A=1/5/10 亿、κ=0.5 同模型实施净收益训练评分，后段承担同模型费用，vs 同规模 R1/R2/Blend3）；新 descriptor 的宏观族按母体源家族继承（H3/H5 继承其母体），映射在收益读取前冻结；每种规则都报。
- 切点沿 E6f `SPLITS`（六个年末）单次选择 / 之后评估 + ≥3 年初始历史后的逐年扩窗；16 个完整年与 2026 部分年分开。训练评分只用决策时已实现的收益与成本；fwd 标签按 `label_end` purge。**政策账户重新走批次**（新规则只控制其后形成的目标；旧批次延续到期；整条路径一次过引擎），两种启动支持（无历史批次 / 带库存连续账户）。反向切割只作迁移诊断。全部标 `fixed_hindsight_library`。
- 可分辨度：`spread_to_pairSE`（即 proposal 的 ρ_sel，改名；不是门）；同时报与固定 R2 的差分分布、源宏观家族内两两差与 SE、固定描述符均匀抽样配对差、近邻权重 / mask 距离、共同 block 扰动后所选配置 / 家族份额。主答案 = 评估账户相对 R1/R2/Blend3 的 `Δgross / Δnet8 / Δcost / Δimpact` 与区间；a、b、b−a 报告，`b/a` 不判噪声占比。

## 9. 块 C：账户、成本、容量与归因（plan §2C 全文执行）
- 三层账：`G_t = portfolio_gross_t − benchmark_t × position_pre_return_t`；`N8_t = G_t − 8e−4·u_t`；`N12_t = G_t − 12e−4·u_t`；`NI_t(A,κ,model) = N8_t − I_t`。`u_t` 是源引擎已核对的成本基数，不另乘 2；影子账户 position 用收益前资本敞口。分解逐日先恒等再按同一日期加权汇总；`ΔN8 = ΔG − 8e−4·Δu`；`ΔNI = ΔG − 8e−4·Δu − ΔI`；对称桥 `ΔG = 0.5(P_c+P_p)[(p_c−p_p)·(r−b)] + 0.5(P_c−P_p)[(p_c+p_p)·(r−b)]` 只作代数分配，先自测（零仓位 p=0）。
- 冲击：继承 E6f C1 平方根与线性模型并先复现其日成本；`A ∈ {1e8, 5e8, 1e9}` 元 × `κ ∈ {0.25, 0.5, 1.0}`；H/L/B 全经济路径覆盖，K 只早段；8bp 与 12bp 另列；**H 配置的括号列在 part1 交付**。模型形状对照：每个训练 / 推导窗口以固定 R2 在 A=1 亿、κ=0.5 的平均费用校准线性常数使两模型费用相同，再施于评估段（全历史直接校准版只作描述）。报 ADV、σ、参与率、低 ADV 比例、极端分位；参与率超模型可信范围只打 `extrapolation` 标签；容量 `A*` 与优势交点 `A_delta*` 分别求根，无解 / 多解如实报。
- Blend 与随机路径的非线性（plan §2C3）：gross/pos 成员平均、线性费用节省 `8e−4·(mean(u_members) − u_blend)`；冲击两基准（成员各用总资本 A 的平均；三账户各 A/3）；I-IID 解析期望 `E[w_i] = (m_h/n_h)·u·min(1, cap_h/(m_h·u))` 只给 gross/pos，turn/net/impact 由随机路径分别跑再平均。
- 影子账户（plan §2C4，part2）：固定展示组、L/L-X 全部路径、B 真实选中路径 / 组合在源影子账户重放（E6f 已有路径精确复用）；顺序 源引擎 → 同账户模型理想可成交 → 加实际标志 / 停牌 → 新缓冲或提前退出，每步一开关；卖不掉不删库存、买不到不借未来成交；H 中未被选中的策略至少给逐日不可成交名义暴露与应交易额表。

## 10. 块 D：统计、时间与结果解释（plan §2D 全文执行）
- 支持集：原四段主数据；报每段、全窗口按有效日拼接、逐年、最近段、去 2015+2016（含相对同样删年的参照）；2026 部分年不算完整年；主 native 序列含真实空仓日（经济上的 0）；基准 / 估值未知日按源契约保留 NA；同日做差再汇总；不 dropna 压缩交易日轴。
- HAC：H5 主 lag 5，H 变体 `max(H,5)`，另 20/60；全窗口同时报历史拼接 NW 与固定四段的段内中心化推断。bootstrap 2,000 次 stationary、平均块长 20/60、段内抽样、日期行整体抽、候选 / 参照 / 成分共 draw；无效 draw 按 seed 流补并记录。主同时带 = 共 draw max-|t|；**Romano–Wolf stepdown 调整 p 值作附列**（完整非同义比较集合与共同依赖结构），不作准入门。
- 比较族（plan §2D3 表）：`F-H1add / F-H1replace / F-H2 / F-H3 / F-H4 / F-H5 / F-B2 / F-L / F-B / F-primary-global / F-cost-global / F-K-discovery`；只有精确路径别名可去重回填，其余全部留在 max 统计量；全体描述符、公式、真实路径、有效比较数四种计数同时报。
- 结果服务改善但不造综合分闸门（plan §2D4）：每条策略给原生 gross/net8/net12、实施情景、父 / R1/R2/Blend3 增量、仓位 / 持仓 / 集中度、风险、近段 / 去 15+16、主要成本来源、T0-35 解释标签、仪器敏感性；按收益 / 低换手 / 少改动 / 较少近期回撤分别生成视图；可列值得进一步研究的节点及其邻居，**不只交最高点、不删负例、不默认采纳新 v3**；"无效果"完整句 = 在何信息集、父、角色、方向、权重 / 阈值范围、成本与日期内观察到多大差与多大不确定性；无联合可分辨度时写"当前证据不足以区分"。

---

## 11. 事前登记（执行端逐字落盘为 `preregistration.md`，只补时间、哈希、源 ID 映射；以下为 plan §2E 原文）

### 2E. 预登记问题（主题对应原Q1–Q11；用本版读法替换阈值判决）

本表与后面的边界声明逐字进入最终`preregistration.md`。只补源ID、哈希、实际日期；不得执行前换成另一套“通过条件”但保留本编号。

| 问题 | 目标量与竞争解释 | 输出与允许读法 |
|---|---|---|
| Q1 输家画像 | pool输家、当前保留的输家、错剔赢家是否有不同事前属性？混杂可能是年份、行业、size、重复触发 | 日期级画像、T0-35/74分离、伪标签/早段跨期图；无清楚画像或多种画像都可，不设正年阈值 |
| Q2 覆盖 | 当前规则控制了多少剩余损失，同时错过多少赢家？ | 原规则覆盖×模式×损失/机会；不以伪参照带内就“证明空缺”，不宣称观察性因果 |
| Q3 第四腿/换腿 | 小权重、等权、替代席位能否提高完整策略？ | 原生与共域、同预算、同名腿/否决2×2、vs父/R1/R2；核未胜出也照做聚合与B2 |
| Q4 时序变换 | 水平以外的变化/自身异常是否有信息，还是缺失/噪声改变？ | identity/Δ/z正确端点、双方向各角色、history support；不推广到所有变换 |
| Q5 条件否决 | 哪种个股状态下值得启用？是否仅剔得少或少交易？ | 无焦点父、全开/全关、Tox/Core matchN、随机状态、同费用分解 |
| Q6 网格边缘 | 经济深度、分箱门槛、单/双否决和KMA/T角各贡献多少？ | SRC/QEDGE/RANKBUDGET桥、两侧邻域、mask/交易距离；边界仍上升只登记边界 |
| Q7 四腿聚合 | 同成员同预算下，mean/median/worst/投票是否不同？ | 全可计算四腿集合、自然与定额投票、完整栈；不按早段同号或ρ预筛 |
| Q8 缓冲/H | 续选、提前退出与延长H能否改善8bp或假设实施净值？ | L-loose/L-matchN/actual-incumbent/L-X分名；资本/成分/费用分解；不选生产H |
| Q9 park复验 | 新结构域是否让选择或新腿参数更有意义？ | S1/S3/S4/S1-cost真实政策账户、固定参照；只建议状态迁移，无自动恢复/淘汰 |
| Q10 40键准备 | 哪些基本角色有探索线索，哪些只是单位/别名/处理差？ | 仅推导段原始全表＋登记草稿；无法判定或有机制无统计仍可登记 |
| Q11 仪器与记账 | 候选差异是否依赖平局、NS、复权、门槛、分母或账户模型？ | 逐开关恒等式、原因计数与影响分布；先读于其他问题，错误修正不改收益准入 |

**共同声明：** 所有截至2026-03-27的历史此前用于研究，本轮旧信息结构及历史选择回放均不属于独立OOS。40键本轮只能做推导段研究，低相关不授予first-look资格，任何有新键血缘的后2018持仓/收益计算仍被禁止。统计量、成本翻转、局部弱段、MCSE和风险画像用于读表，不作自动淘汰门。R1/R2/Blend3身份不同；v3候选和线状态由用户决定。E7保持HOLD。

**本 brief 对上表的修正附注（与上表一并进 `preregistration.md`）**：Q1/Q2/Q5 的 age 轴为 1–5（`build_observation_pool` 用 `signal.shift(1..5)`）；Q10 的信号截断键为 `CMF_20d`、`cum_return_5d`、`intraday_ret` 三个；K3 流动性研究在 pool0 已有的"20 日均成交额 > 2,000 万"地板之上；pool0 可能含涨跌停日（源过滤名义化），T0 协变量与 K3 / L-X 解读带涨跌停计数列；Q3 换腿格与 E6d 表 F/G 并排读；Q4 主读数在 `legacy_all` 与 `history_warmed` 的共同形成日。

---

## 12. 自测与验收（只对正确性设硬条件；收益 / 区间 / 某段弱 / 成本翻转不是 BLOCKER）
- **级别**：GLOBAL STOP（真实 E7 数据进入计算；NEW40 血缘越界到 2019+ 收益 / 持仓 / 标签或 T0-74 产物流入 H/B；源码 / 冻结数据意外变化；共用机进程配额不足且无法降并发）；MODULE STOP（符号 / 时间 / 域的逻辑错：未来函数、成本重复扣、账户资产凭空消失、active-leg 或有效域错、pool 级与 Q 内排序混用、source 锚差无法解释且影响结论方向 → 隔离该模块及后继，其余继续）；WARN / LIMIT（独立实现锚差超 1e-10 但可解释、注册表计数与 plan 不符、行业 PIT 不足、某段成本字段缺失、估值未知、SE 退化、旧文件缺失、L-X 恒等式不过 → 保留主结果，缺失列 NA，禁止有利插补）；合法研究结果（net 下降、近段差、未超 R2、联合带跨零、随机参照不显著、低容量、邻域不平 → 全部留表）。
- **锚**：§2 所列（E6f 63 锚、E6e R1/R2/A03/A06/A07/A08 逐日、E3 6bp→8bp、`interior_nopos` 246/67/4、76 = 4×19、E6c 的 H 锚、`A4b_CVRv5` 数字）；新增恒等锚：缓冲 b=0 = 源 N_t 与源账本逐位；条件否决全层启用 = 无条件焦点否决、空集 = Q 逐位；H2 identity = 原值、Δ0 = 0；H1 α=0 端点 = 真实剔除 J 有效性要求（`wcombine_dense` 零权重 bypass）；四腿 `trimmed_mean` = median；QEDGE 与 SRC 在共同可运行日精确一致；Blend3 gross/pos = 成员平均；40 键守卫四条攻击测试全部被拒且 `cvr_1d` 原式不被误封。
- **plan §3.2 八组最小测试矩阵**逐条接到真实 builder 与引擎（时间 / 权限、因子 / 单位、分箱、DEV、结构、路径、会计、统计 / 输出），另独立手算两三个小宇宙；plan 附录 A 的本地合成脚本可复跑但**不替代真接口测试**。
- **完成定义**：每登记单元 ∈ {PENDING, RUNNING, SUCCEEDED, FAILED, LIMIT, SUPERSEDED}，按 task_id 计数之和 = 登记总数（重试是同 task 的 attempt）；每输出带输入 hash、schema / 行数、有限 / NA 计数、产物 hash 与状态；核心模块未跑不得称整轮"通过"，标 `PARTIAL_WITH_LIMITS`。容差不是拟合参数。

## 13. 运行组织（三次交付）
`0（注册 / 源码 / 锚 / 修订）→ H0 → {T0-35, H1, H2, H3, H4, L, K/T0-74}（可并行；K 不等 H 收益，H 不读 K 结果）→ H5 / B2 → C1 括号（H 配置）→ REPORT_part1 → B1 → C（L/B 路径、影子账户）→ D → REPORT_part2 → K 收尾 + E6h 草稿 → REPORT_part3 + coverage/manifest`。part1/part2 不是等用户 GO；**part1 之后不得按收益改网格**；用户中途改方向则保存原登记并做 amendment。
- **问题与交付的映射**：part1 答 Q1/Q2（T0-35 部分）、Q3/Q4/Q5/Q6/Q7、Q11；part2 答 Q8、Q9，以及 Q3–Q7 的冲击后排序与真实政策账户；part3 答 Q10、Q1/Q2 的 T0-74 部分。每份 REPORT 只写本次已答的问题，未答的标"待 partN"。
- **计时**：先在最长段与最短段各跑固定配方试点（特征重建、四种 selector、变换、条件否决、缓冲、引擎、控制、重采样、写盘）报范围，不用最短段线性外推；E6f 约 22 小时，本轮更大，**慢不是问题**，再久也不削配置、随机诊断或交易对照，只分批交付；预计 >30 分钟的阶段按协议报预计时间。
- **并发**：全局同时计算 worker ≤32（父 / 子 / BLAS 线程一起预算；BLAS/OpenMP 每 worker 1 线程；不嵌套起子 worker）；绑 socket 1（`taskset -c 96-191,288-383`）；启动前与运行中监控用户进程 / 线程总数、`ulimit -u`、内存、磁盘，预留 ≥20% 进程限额且不少于 64 任务槽；提升并发须向用户报具体数字并获批后写入 amendment。
- **完成协议**：日志直写文件；父进程 wait/reap；worker 正常 close/join/flush/fsync 后原子 rename 提交；父进程验证产物 hash 与退出码后写 DONE；不默认 `os._exit(0)`；清理残留只按 PID + 启动时间 + cwd + task_id，禁止泛化 `pkill python`。
- **存储**：`/mnt/sda2` 当前余量约 37 TB、`results/` 约 190 GB；新增确定性配置日账本 float64 parquet 分块（须支持任一配置日收益 / 交易复原）；随机路径只存汇总 + 8 条示例；影子账户逐日现金 / 持仓 / 费用账；写前估容量。cache 键至少含数据指纹 / allowed-end / 表达式血缘 / active legs 与权重 / raw-rank-NS 域 / tie / selector / pool 哈希 / veto / H / 状态初值 / seed / 费用版本；不复用源码或边界已变的文件。

## 14. 交回
- `results/<ts>_E6g_structure_layer/`：`PLAN_COPY.md / brief_copy.md / preregistration.md`（含哈希与修订链）、`source_manifest / engine_contract.md / registry/`（U34/U35/NEW40/剩余 8 键索引、血缘、方向、宏观族、别名）、`manifest.json / task_status/ / coverage.csv`（全部经济 / 对照 / 随机 / alias / blocked 格，期望与实际个数，数据守卫范围）、`revisions/`（E6f 段内空仓勘误、计数分母、R2 身份、Blend 估算撤回、数据 / 位级差）、`H0/`、`T0_35/`、`T0_74_discovery/`、`H1/ … H5/`、`B2/`、`L/`、`B/`、`C/`、`D/`、`K_discovery/`、`E6h_registration_draft.md`、`checks/`、`line_state_proposal.md / park_ledger_delta.md`（草稿）、`limit_register.md`、`source_corrections_E6g.md`、`REPORT_part1/2/3.md`。
- `exec_briefs/E6g_REPORT_part1.md`、`_part2.md`、`_part3.md`：协议结构；每份 ≤15 行纯文本摘要；Q1–Q11 每问：原问题 → 数字 / 分母 → 竞争解释 → 仍未知 → 下一步可操作含义；所有统计表附总体计数与分布极值；**不写"可交付 / 已确证 / 必须换核 / 饱和 / 穷尽 / 到平台"**；part3 末尾附全轮 coverage 总表；总 manifest 未完成不得写"E6g 完整交付"。
- **coverage 为硬交付项**：逐条映射 proposal、web plan、本 brief，状态 `done / reused / changed / deferred / unavailable`，改或没做写理由与影响。
- WORKLOG 远端 + 本地同文（只记操作事实）；git：whitelist add `e6g_*.py`、本 brief、`source_corrections_E6g.md`；**七个 `e6e_*.py` 与十九个 `e6f_*.py` 不改、不重新 add；三个 2026-05 的 untracked 文件不 add**；`git push origin main`；不 `git add .`、不 force。

## 15. 禁区
不读 2026-03-27 之后的真实数据、不开 E7；NEW40 血缘不进 2019+ 的收益 / 持仓 / 交易 / 成本 / 标签 / 学习产物，T0-74 不进 H/B；不改 I11 / pool0 / clean 历史成员、生产 DEV、生产 H5、8bp 主口径、v2 交付；QEDGE / RANKBUDGET / 变换 / 条件否决 / 缓冲 / 提前退出 / H≠5 / 影子账户一律研究版本不升格生产；不把网格平坦、族中位、`b/a`、被选比例、年度胜率读成 OOS 或未来概率；不把 0 个联合显著说成 0 个有效策略；不把子杠杆级否定写成线级"穷尽 / 到平台 / 饱和"；不以候选数量作独立样本量；不因慢而减配置；不用 `git add .`；不出现登录信息与主机地址。凡遇"必须改上述任何一项才能继续" → 停，写 BLOCKERS。

## 16. 自审记录（规划 session 2026-09-11；执行端见此段方可开工）
| 类 | 不利因素 | 处置 |
|---|---|---|
| 事实 | proposal 六处错：C = CVR_20d 非 cr20；lclose 语义与除权污染范围；E3 6bp；R2 身份；J_KTC 32 非 31；Δ0/ts-z 伪端点 | §0.1 逐条承认；proposal 顶部加勘误块；`source_corrections_E6g.md` 收录 |
| 事实 | "第四腿 / 换腿从未测"说得过宽（E6d 两因子 528 格 + 第三阶段 162 格） | §0.1 收窄为"三腿核内换席、第四腿、22 个从未进合成的键"；H1 与 E6d 表 F/G 并排读 |
| 事实 | age 0–4、信号只截断 CMF、pool0 无流动性地板、涨跌停过滤有效四处是本轮才核实或推翻的池事实 | 写进 §1.3 契约与 §11 附注；H3/T0 按 age 1–5；涨跌停计数作注册表必交列，源过滤名义化记 `source_corrections_E6g.md`，地基不改 |
| 代码 | 新持仓逻辑路径依赖（缓冲、条件否决、QEDGE/RANKBUDGET、H2 变换） | 恒等锚（b=0、全层 / 空集、identity、SRC=QEDGE 共同日）逐位；玩具池自测；地基不改 |
| 代码 | 40 键守卫被别名 / 学习产物 / 跨年标签绕过 | 血缘 DAG + 四条攻击测试 + H manifest 先冻结 |
| 代码 | 3g 门槛与经济深度混杂、qcut 边界被 NumPy 重造 | 三 selector 分名；QEDGE 复用源 qcut 与 retbins；逐开关账 |
| 代码 | 平局在残差分数上与原值不同 | WHOLE_TIE 施于实际分数；两层 nunique |
| 代码 | 账本口径（pre-return 资本、u_t 不乘 2、N8 不含冲击、中位不可加） | §9 三层账与逐日恒等式；E6f 假象 4.45 点教训写进测试 |
| 统计 | 结构层搜索大（H1 1,544 + H4 1,700 + B2 + H3 + H5） | 每子杠杆一族同时带 + global 族；RW 附列；期望值 = 族中位（E6f）；无闸 |
| 统计 | 选择回放在扩展域上自证 | S1/S3/S4/S1-cost 与切点事前写死；`fixed_hindsight_library`；`spread_to_pairSE` 不作门 |
| 统计 | 40 键推导段结果与 T0-74 间接污染验证段 | 只用推导段 + `label_end ≤ 2018-12-31`；T0-74 产物不进 H/B |
| 统计 | 同源变体从族里删掉 | 只有精确路径别名去重 |
| 统计 | 随机对照 128 条被读成 p 值 | 只作参照与 MCSE；不作门 |
| 成本 | κ 未校准、单位错、A/3 与满 A 混同 | 多 κ 多 A 情景；金额单位核为元；两基准分开 |
| 解读 | 把子杠杆级否定写成线级"穷尽 / 到平台"并换线（proposal 初稿犯过） | §15 禁区明写；每个"无效果"句写子杠杆 × 域；线状态由 REVIEW 提议、用户定 |
| 解读 | 首次观察 / 推导段结果被读成 OOS 或验证 | §11 共同声明；E7 才是 OOS |
| 运行 | 并发与僵尸进程、假 DONE、隐性缩域 | 全局 32、状态表求和、父进程验收、coverage 硬交付、三次交付 |
| 运行 | 随机路径与日账本写爆磁盘 | 只存汇总 + 8 条示例；写前估容量 |
| 流程 | 事前登记被改写；两套 final | §11 逐字；本 brief 唯一有效，plan/proposal/REVIEW 的 SHA 进 manifest |
| 宽松 | 把 plan 的过程性"不得"误当阻断，导致合法结果被 STOP | §0.2 六类硬约束之外一律报告并继续；MODULE STOP 只限符号 / 时间 / 域逻辑错 |
| 节奏 | 有没有把跑得快当约束 | 没有：H1 1,544、H4 1,100 + 600、B2 五点 α 与 MA、H3 全部对照与 256 条路径、L 全部预算与 H 曲线、K 40 键全角色、T0 128 条伪路径、bootstrap 2,000、RW 附列全做；只分批交付 |

方向确认：headline = 34 键结构层（第四腿 / 换腿、腿变换、条件否决、网格边缘、四腿聚合）+ T0 输家解剖固定项；carried = 续选缓冲与期限、40 键推导段准备；park 只收被推翻或无增量项，本轮重测 P1/P16，推导段预看 P3/P4/P5/P7/P8/P12；不加原始因子进生产、不改池、不改生产 H、不改成本口径、不改生产、不开 E7；探索从宽、无闸门、事前登记逐字；三份 REPORT 交用户与规划 session；判读由规划 session 写 REVIEW、更新线状态表与 park 台账并续写复盘台账。
