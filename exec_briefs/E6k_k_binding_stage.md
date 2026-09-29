# E6k —— 最终 brief（v1，2026-09-28）：K 腿绑定环节研究 —— 六接入（NATIVE / SZL / INC / RP / TREFIT / POST2）+ 层配置四账户 LX + 三门（SA / PM / HG）+ 144 行主展示（plan v1.1 全采纳）

用途：执行端开工文件。设计全文 = `exec_briefs/plans/E6k_plan_web_final.md` v1.1（1,643 行，sha256 前缀 `1f9e949c`；执行端复制为结果目录 `PLAN_COPY.md`，plan 不进 47 仓库的 exec_briefs），**本 brief 不重写 plan，只做三件事**：① 规划端在 47 上核过的源事实与身份（§1.3、W★）；② 规划端对 plan 的采纳与少数调整（§0.1 W 项；冲突处以本 brief 为准并写明理由）；③ 执行组织、登记时序、授权、交付与复核（协议 v1.1 + v1.2 卫生项）。proposal `E6k_proposal.md`（`65d2b010`）是参考输入，不是设计权威；plan §3.1 对 proposal 复盘归因的更正照单接受。上一轮读法 `E6j_REVIEW.md`（`b036617d`）、复核 `E6j_VERIFY_report.md`（`3e6345e1`）、事后口径 `E6j_REPORT_supplement_1.md`（`727f4892`）、流程裁定 `E6j_RULING_20260926.md`（`cb3b8a5f`）。执行端自检探针见附录 `E6k_brief_appendix_probes.md`。

**执行端第一个动作**（协议 v1.1）：完整读经验册——`resonance-methodology-hypothesis-postmortem`（#1–#76 与纪律 ①–㊽，见 `E6k_proposal.md` §2.3 / §2.7 / 附录 C）、`00_协议.md`、`REVIEW_protocol_v1.md`（v1.1 节 + v1.1a）、`E6j_lessons_delta.md`（含 § 交付后 19–27 条）、`E6j_VERIFY_report.md` §3 E 项；然后读本 brief §0、plan §0 / §4–§10 / §13，再编译登记清单。

**硬边界不变**：四地基（`data_loader / features_daily / event_study / pool_screening_v2`）与 e6e–e6j 脚本只读；新代码 `e6k_` 前缀放研究目录；`results/` 只增不删；白名单提交 + push main，不 `git add .`；任何文档 / 日志 / 提交不含登录信息、主机地址、账号名；不读 2026-03-27 之后任何真实行情（E7 守卫沿 E6i / E6j，攻击测试用合成未来数据）；生产 v2 / v3 展示候选 / U34 / U35 / I11 信号成分 / DEV 不改——任何"通过"只产出《生产变更候选清单》，`deployment_authorized = false` 永远由用户改；E6j 所列 38 个遗留进程本轮不动（plan §13.4）。**算力与时间不是约束**（用户 09-26 / 09-28）。

---

## 0. 一句话问题与设计结论

**问题**（plan §0.1 原话）：保留已经有用的 I11 核心和 K 信息，改善"测量 → 比较对象 → 过滤边界 → 成员与资本 → 交易"的接入过程。风格更中性不是最终目标；相同现实约束下，完整策略表现更好才是目标。

**结论**：P 包 = 六生产形态 × 四测量（S / M / Q / C1）× 六接入（NATIVE、SZL5、INC1、RP3、NATIVE_HG10、INC1_HG10），统一 α .25 × H5 的 **144 行主展示** + 四条 C1_hi（A4b ± CVR，α .5，H10 / H20）+ 六条 SM 交互历史锚；B 包 = 其余全部接入 / 机制 / 对照（CORE / OWN / REPAIR / LAYER / BAND / BAND_COMPARATOR / HG_ONLY / TREFIT / POST2 / RAR / PARENT，每段 39,142 个原始账户描述符 + 72 条 INC 附属对照），全 α {.125, .25, .5} × H 1…20；两包在任何新收益读取前同时冻结，两后段在 E6k 自身授权下一次算完、封存后读，标签 `NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY`；政策按两套独立 profile 评分（登记口径 edit_5 复现 + 建议口径 `PROPOSED_PORT3_LAG1`，`policy_provisional = true` 直到用户裁定）；随机 = 复现 E6j IID 的 `LEGACY_POLICY_RANDOM` + 新机制内容置换（含八子集条件置换）；决策端中途不动。

### 0.1 相对 plan v1.1 的采纳与调整（规划端 2026-09-28 在 47 核源码 / 账本后定；★ = 规划端核出的事实；W = 规划端决定）

| # | 项 | 处置 |
|---|---|---|
| W01 | plan §0–§15、§17 | **全部采纳为执行设计**（含 §14.2 A01–A20 终审修订与 §16.3 内嵌规范脚本）；本表只列源事实与少数调整 |
| ★W02 | Q 的实际身份（plan §1.3 要核） | `e6j_features.b1`：`q = sdiv(1.0, d + EPS)`，d = \|log(C/lclose)\|（CC），EPS = 1e−4；登记 `J_B1_qCC`，主方向 **low_bad**（价稳 = q 高 = 好），对照 high_bad 双向登记（`rows_B.csv` BR006 / BR007）。S20lag = a20 × q，a20 = x / lag1(rmean₂₀ x)，b20 = lag1(rmean₂₀ x)。**Q 没有相对放量条件、没有 W20 / W60 基线**——plan §2.8 正确 |
| ★W03 | size 坐标的口径与日期（plan §1.3 要核） | E6j `e6j_run_p.size_pct_cells`：`mcap` = `negMarketValue`（流通市值），**形成日 T 当日**在 clean 域内 `rank(pct=True)` ∈ (0, 1]，取 pool0 单元；编辑层 gap = 换入中位 − 换出中位（带符号）。**调整**：plan §4.3 定 z 为 T−1；生产在 T 收盘形成、T+1 VWAP 执行，T 日收盘市值在形成时点已知、无前视，且与引擎其余 T 日字段同口径。→ **主坐标 `z_T`（T 日，legacy 同口径）、`z_LAG1`（T−1）作并列列**；两者的编辑层 / 组合层 size 差都算，policy profile 用 z_T，另印 LAG1 差值；plan §4.3 的"不能拿今天存活名单重建过去 clean 分位"照做（逐日 clean 域） |
| ★W04 | DEV 精确合同 | `export_delivery_pools_v2.assign_weights_dev` :71–84（逐字复制于 `e6j_prod.assign_weights_dev` :69）：个股 w = min(1/n, 1%)；行业组权重和 > `shares_t[ind] + 0.03` 时按比例压缩；**不归一**；`shares` = `bench_industry_shares(clean, industry)`（当日 clean 域行业数量份额）。plan §4.2 正确；size 当"行业"的 S4 口径沿 supplement_1 |
| ★W05 | 行业字段 | 生产 `industry = data.get('industry_zx1', data.get('industry'))`（`export_delivery_pools_v2.py:109`）：中信一级，`industry_zx_1_all` 长表按日期（`data_loader.py:284`），逐日 pivot → **逐日可用即 PIT**；Stage 0 核长表的日期语义（生效日 vs 快照日）并写进 `engine_contract.md` |
| ★W06 | E6j "推导正 / 后段正" flag（plan §1.3 要核） | `results_B/part2_main_config_all_objects.csv`：deriv_pos = `D_FULL_deriv > 0`，post_pos = `D_FULL_post > 0`，两者都是**两段按有效配对日 n 加权合并**的年化增量（决策端 D13 复核恒等）；638 对象、410 推导正、205 后段转负；plan §10.5 场景以此为原 flag |
| ★W07 | 生产路径与 SLOT | 沿 E6j brief W04 / W05：`precompute_neutralized_factor` → `rank(pct=True)` → `build_factor_strategy_holdings_cached(...,2,[2])` → `combine / 交集` → `drop_mask(CVR k5)` → `assign_weights_dev` → `compute_calendar_pnl`（T+1 VWAP、后复权、8bp = `cost_bp_bilateral`）；SLOT = `e6j_slot.blend_q`（pct 层线性混合、FALLBACK 新缺用旧、不重排、α = 0 短路）；六形态 `e6j_prod.form_masks`；Munion = 三腿保留集合的**交集**（plan §4.2 正确）；Mmean 的 K 腿占综合分 1/3 → b 的 mean 换算 b/3（plan §5.0） |
| ★W08 | 47 环境 | Python 3.10.13 / NumPy 1.26.1 / pandas 2.2.3 / SciPy **1.11.3**（`optimize.milp`、`linear_sum_assignment` 可用）/ statsmodels 0.14.0 / **无 `arch`**（stationary bootstrap 沿 E6j 自实现）；384 逻辑核、2.27 TB 内存、`/mnt/sda2` 余 37 TB；plan §16.3 脚本在 Python 3.13 / NumPy 2.3 / SciPy 1.17 下 103 / 103，**在 47 环境重跑**（Stage 0 第 6 类），环境差只改测试 harness 不改规范 |
| ★W09 | 算力校准（E6j 回执 wall_s 汇总） | E6j `run_b` 112 任务 3.3 任务时 / 53,592 描述符（≈ 0.2 s / 描述符段，含复用）；`run_brand` 741 任务 677 任务时；`run_prand` 96 任务 103 任务时；`diag_b` 7 任务时。E6k 账户 ≈ 3× E6j-B + 新算子（RP 求解按 list 级缓存、与 H 无关；HG 有状态逐日），随机 ≈ 1,900 单元 × 4 段 × ~46 s ≈ 100 任务时 + HG 有状态路径；**预估 4–7 天含三次登记与两次封存**；不以短为目标；开跑前 profile 分段计时并报（E6j lessons 11 / 17） |
| W10 | 存储合同 | 掩码（bit-packed，沿 E6j `masks_*.npz` 布局）+ 日聚合账本（gross / pos / turn / net8 / sc_child / sc_parent / qmiss / nnames / wsum / **size_exposure_T、size_exposure_LAG1、small30_share、n_edits、edit_weight_share**）对**全部**描述符；**完整日目标权重与滚动持仓**只对固定清单持久化：144 主展示 + 四 C1_hi + 八母体 + SM 锚 + 各研究算子 α .25 × H5 全部对象 + 四 owner 全网格 + LX 四账户 + RP 全 τ 主配置 + HG 状态账户；其余账户的权重由掩码 + DEV 输入**可确定性重算**（Stage 0 写重算恒等锚）。随机路径存每路径 / 每段统计 + 预指定复核样本路径完整日账本（plan §13.4） |
| W11 | 授权状态（plan §0.4） | **三件事分开**：(a) 开工 = 用户把本 brief 交给执行端；(b) 两后段授权 = **E6k 自身**预授权（不沿用 E6j）：用户消息含"B"/"事前整表授权" → 执行端写 `registration/record_B_preauthorized_E6k.json`（生效条件 = Stage 0 六类全 PASS + A1-auto 全 PASS + 进入 Stage 3 时冻结清单 sha 不变），否则**方式 A**：推导两段算完、封存、写 B 草稿后停在后段之前等用户一句话；(c) 经济裁定（E6j REVIEW §11：size 尺子 / 四候选入清单 / 其余）= 用户另行一句话；未取得则 `policy_provisional = true`，两套 profile 独立评分，不阻塞研究（plan §0.4 / §9） |
| W12 | 政策 profile | ① `LEGACY_EDIT5`：逐字复现 E6j 登记口径（六条 + 正向 + 简单性 + 编辑层 ≤ 5 点，`e6j_policy_p.verdict` 同源），用于原生对象的历史连续性；② `PROPOSED_PORT3_LAG1`（plan §9.2）：组合层 `abs(mean_t size_delta_t) ≤ 3`，逐段判断，共同未知 size 用紧区间（`SIZE_PARTIALLY_IDENTIFIED` 不淘汰）；**本 brief 加 `PROPOSED_PORT3_T`（z_T 版）作第三列**，与 LAG1 并印，差异属定义不择优；固定曝光列（带符号均值 / 平均绝对差 / p95 / 最大 / 五组份额偏移 / 小盘 30% 份额 / 未知 size 资本 / 目标与滚动 / 换入换出 gap / 资本与编辑比例）全部只披露；新算子 `replacement_preference_status = NOT_AUTHORIZED`（不自动 chosen）；原生四测量按源 policy 复现三句加法；五标签 `economic_effect / policy_score(profile) / mechanism_status / evidence_exposure / deployment_authorized = false`；边缘清单只报距离、CI、MC 误差 |
| W13 | 随机 | `LEGACY_POLICY_RANDOM` = 逐位复现 E6j R-MATCH-SRC（Z-MAP basic 匹配条件、E6j 稳定哈希种子）用于六条之 e-随机；新机制置换（plan §10.2：置换统一方向后的有限 kf、稳定股票 ID、绝对交易日块长 5、整行联合、每路径独立状态与费用）用于八子集条件置换与新算子机会基线；首 1,024 路径，MCSE > .03 按 512 增补至 8,192 上限（E6j MC-1…5 沿用）；HG_ONLY 标 `NO_NEW_CONTENT_TO_PERMUTE` |
| W14 | 网格 | 研究块 H = 1…20 全整数（plan §8.1；E6j 用 7 档，本轮账户便宜、按 plan）；α {.125, .25, .5}；主解释 α .25 × H5；BAND 跨结构主扫描 H {3, 5, 10, 20}，四 owner（S / Q → A4b_CVRv5；M → M_union3_v2_CVRv5；C1 → M_mean3_v2_CVRv5）补全 α / H |
| W15 | A0 / A1-auto / A2 | A0 冻结 plan + 全量参数元组 + 18 张卡 + policy profiles + 掩码诊断字段 + 回退 / 插值 / 分组规则；A1-auto = E6j 七项（登记对账 / 五类身份与方向论证 / 槽位合法 / 锁定值 / 源事实表 / Stage 0 全 PASS / B 草稿字段）+ plan §13.2 七类合同作细目；**词表补 `both_registered`**（E6j #65）；每张卡 `queries` 非空（E6j #73）；掩码事实由 A1-auto 机械计算、只触发预冻结的回退 / 不适用标注，不生成阈值、不挑臂 |
| W16 | 首看读法 | 两后段各自估计、合并、CI、与推导差、与原生对应版本差、随机位置、风险变化一起报；标签 `NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY`；不用"半样本外 / 替代 E7 / 通过确认旧赢家"；不用显著性过门（plan §10.6；proposal 的"首看三档"不作标签） |
| W17 | 交付物 | plan §13.5 八件 REPORT（R0 / part1 / part2 / part3 / mechanisms / carried / REVIEW_input / lessons_delta）+ 机器表（source_manifest / account_manifest / policy_profiles / hypothesis_lineage / hypothesis_outcomes / mask_edit_ledger / risk_exposure_daily / layer_transplants / random_registry / read_permissions / coverage / completion_receipt）+ `limit_register.md`；表头十项 + 主体 + exposure + query_id；**取绝对值作门的量同印带符号值**（E6j #70 / #74）；全称句由计数；REPORT 交付即冻结，补充另起 supplement |
| W18 | 协议 | 复核按 v1.1（VERIFY brief 预期值脚本现算、只写标量或随附文件；V 可读生成器不可执行；D 先读语义、按 plan 原句逐 profile 实现）；**v1.2 卫生候选即时采用**（不涉经济）：A1-auto 词表补项、每卡 queries 非空、生成器"固定输出"清单必产（plan §13.5 表逐项打勾）、绝对值量同印符号、回执计数写"截至哪个回执之前"、R0 环境节按随机量逐类写生成器 |
| W19 | 遗留进程 | 38 个（`verify/legacy_processes.csv`）不动；只管理 E6k 自身进程组（PID + 启动时间 + 命令行）；不 `pkill -f`、不 `os._exit(0)` |
| W20 | plan 规范脚本与计数 | 从 `PLAN_COPY.md` 提取 §16.3 脚本（提取后 sha 与 plan 所记 `ebc9d4eb…` 核对）在 47 跑：103 项 + 39,142 / 段 + 72 附属；A0 编译器独立枚举后逐元组比对（E6i #49 / E6j A1-auto 第 1 项的先例） |

### 0.2 "跑久一些、多用算力都没关系"的落法
全 H 1…20；每段 39,142 + 72；随机 1,024 起并按 MCSE 增补；bootstrap 2,000 × 块长 20 / 60 × 全部确定性配对路径；MATCH-CAP 全部非恒等账户；影子库存对 §8.4 对象；八子集条件置换 24 对象；不为省时间砍范围；并发按 §8 实测配额。

---

## 1. 起点确认与契约

### 1.1 起点
- 47 HEAD = 远端 main = `82b6cf3`（E6j VERIFY 交付）；E6j 结果目录 `results/20260927_0038_E6j_k_two_dimension_pilot/`（registry / accounts / randoms / results_P / results_B / supplement_1 / verify 只读复用）；E6i 结果目录 `results/20260923_0254_E6i_measurement_need_fit/`（registry / statistics / accounts 只读）；E5a v2 交付 `results/20260903_1214_delivery_pools_v2/`（六个 pool2 + summary + _delivery_stats + check）；生产脚本 `code/project_core/export_delivery_pools_v2.py`；E6j 研究代码 `e6j_*.py`（只读复用：`e6j_prod / e6j_slot / e6j_features / e6j_random / e6j_policy_p / e6j_engine / e6j_fast`）。
- 本轮输入三处镜像（本地 exec_briefs / 47 exec_briefs / 结果目录副本）：本 brief、附录、proposal（`65d2b010`）、E6j REVIEW（`b036617d`）、E6j RULING（`cb3b8a5f`）、E6j VERIFY report（`3e6345e1`）、supplement_1（`727f4892`）、addendum_1（`5c662cd5`）、协议（`REVIEW_protocol_v1.md` `0b15019e`、`00_协议.md` `f685e538`）；plan 只在本地与结果目录 `PLAN_COPY.md`（执行端从 47 临时交接路径复制，sha 必须 = `1f9e949c…` 全长核对）。执行端开工时按 sha 写 `source_manifest.json`。
- 结果目录命名 `results/<YYYYMMDD_HHMM>_E6k_k_binding_stage/`，结构沿 E6j（registration / registry / anchors / stage0 / accounts / randoms / results_P / results_B / results / diagnostics / carried / checks / reports / task_status / verify）。

### 1.2 数据与生产锁
2010-01-04 .. 2026-03-27；四段 2010-14 / 2015-18 / 2019-23 / 2024-26；E7 不读；基础池、I11 定义（`define_i11_signal`，分位阈值）、5 日观察、DEV（W04）、T+1 VWAP、后复权、生产 H5、源 8bp 成本算法不改。

### 1.3 契约（规划端已核；执行端整段读函数体复核并写 `engine_contract.md` + `source_resolution.md`，每条三栏：定义处 / 调用处 / 默认值；差异登记不改源）
1. 生产路径、六形态、6bp、pool2、DEV（W04 / W07）。
2. SLOT 语义、FALLBACK / REPLACE 分名、α = 0 短路（W07）；Mmean 综合分 1/3 换算。
3. 四测量源：S = `K_rar20` 反向（`e6i_features.py:897–905`，基线 lag(rmean₂₀ x, 1)）；M = `K_slope20`（:828–831，低坏）；Q = `J_B1_qCC`（W02）；C1 = `K_MA3_E6F`（`e6f_core.build_raw` :154–156，高坏，min_periods = mp(3)）；四个 RARPRE 源对象（W20 / W60 × LT / SE，`e6j_features` :329–336）。
4. size 坐标 z_T / z_LAG1（W03）；行业 PIT（W05）；float 股本与 `negMarketValue` 的身份分别核（plan §4.3：不预设成交额 = 换手 × 市值）。
5. R2 / A06 定义（E6i `registry/mothers.csv`：R2 `KT_mean@30|C:k5+cr5:k10`；A06 `KTC_mean@25|cvr_1d:k10+cr5:k10`）；R1 = `alias_of A4b_CVRv5`（E6j R0-Q05，不重复计算）。
6. E6j 随机（`e6j_random.py`：Z-MAP basic 匹配、稳定哈希种子、`cond_cells` 四层回退 行业×size3×旧K3 → 行业×旧K3 → 行业 → 全池，格内 ≥ 2）；`same_capital`（`e6i_stage2.py:11`）；E6j 政策代码 `e6j_policy_p.verdict` 与追记 `policy_P_operational_addendum.json`（MC-1…5、V-1…5）。
7. E6j 封存 / 回执 / 记录 B 文件格式（`registration/record_B_preauthorized_E6j.json`、`record_B_conditions_receipt.json`、`seal_P.json`、`seal_B_post.json`）作模板。

### 1.4 事前登记
两个登记包在任何新收益读取前落盘：**P 包** `preregistration_P.md` = plan §8.2 144 行 + 四 C1_hi + SM 锚 + §9 两套 profile 全文 + 18 张卡里与 P 相关者 + `selection_exposure_ledger`（原生四测量 = E6i / E6j 已见；C1_hi = E6j §13 已见；SM = E6j 已见；新算子 = 首次评价）；**B 包** `preregistration_B.md` = plan §5–§8、§10 全文 + 全量描述符表（编译器现算 39,142 / 段 + 72）+ 18 张卡原文（`PLAN_COPY.md` §11 行号逐字引用）+ `hypothesis_lineage.csv`（plan §3.1 字段）。修订另起 `preregistration_amend_<日期>.md`，任何语义 amendment 使后段授权失效（W11）。

---

## 2. Stage 0 六类起点核验（plan §13.1；任何账户之前；附录 A 给逐项探针）
1. **身份 / 权限**：三处输入 sha、E6j 原件（policy JSON、P / B manifest、parent map、S1–S5、VERIFY、D 探针）、E6k 预授权文件、数据截止、白名单与只读 sha、`PLAN_COPY.md` = `1f9e949c…`；版本链写 `source_manifest.json`。
2. **源账户**：六生产形态 α = 0 逐位重现六个 pool2（E6j 锚 1 复用同代码 + sha 核）；6 / 8bp 双锚（精确式 net8 = net6 − 0.02·turn·L/n）；R2 / A06 母体重算 = E6i 已存账本；R1 别名；原生 S / M / C1 / SM 主配置 = E6j `accounts/P` 同描述符逐日相同；Q 与四个 RARPRE 源对象 = E6j `accounts/B` 同 ID 逐日相同。
3. **新算子恒等**：SZL_OWN 复制（同分组同掩码施于旧 K）；SZL 单组 ≡ NATIVE；INC γ = 1 投影正交 + 均值保留、γ0 = `INC_SUPPORT0`（全支持时 ≡ NATIVE）、INC_DOSE 同均值同 RMS；RP：父名单恒可行、`PAIR_ALL` 与父同 N 同行业人数、τ = ∞ ≡ PAIR_ALL、词典序唯一解重放；LX：V00 ≡ B、V11 ≡ C（合法域先锁，含 CVR 毒尾排除）、四账户闭合 V11 − V00 = 三项和；SA / PM / HG：b = 0 ≡ 对应无带账户、HG 状态依赖前日（不同起点不同结果）、HG_ONLY(α0) ≠ 父；TREFIT g = 1 ≡ NATIVE；POST2 α0 ≡ 父且非 no-op（对账实际编辑数）。
4. **数据 / 时钟**：z_T / z_LAG1 的 PIT；行业长表日期语义；OHLC / lclose；事件时钟；缺失；共同支持；E7 边界攻击（合成未来数据 ≥ 覆盖矩阵）；T+1 成交。
5. **随机 / 状态**：显式 stream（blake2b → SeedSequence，回执 `generator` 字段逐类写）；股票重排不变性；串 / 并行 / 断点续跑逐位重放；跨分片 HG 状态交接；联合分量整行置换；`LEGACY_POLICY_RANDOM` 8 条路径哈希 = E6j。
6. **输出 / 资源**：单任务 RSS / 线程 profile；日账本 schema（W10）；费用恒等 net8 = gross − 8e−4·turn、net8 − net6 = −2e−4·turn；冻结 / 回执 / 闭包 / query 链接；plan §16.3 脚本 103 / 103 在 47 环境；A0 计数 39,142 + 72 与编译器独立枚举逐元组相等。

任一核心时钟 / 母体锚不一致 → 阻断依赖包并写 BLOCKER；不改阈值或历史结果凑 PASS。

## 3. A0 登记（执行端编译；不等收益）
P 包 144 + 4 + 6 + 8 母体；B 包 39,142 / 段 − P 部分 + 附属 72 + COMMON_SUPPORT（CORE / REPAIR / LAYER / TREFIT / POST2 / RAR 在 α .25 × H {3, 5, 10, 20}）+ MATCH-CAP（全部非恒等）+ 随机（144 + 4 + 各研究算子 α .25 × H5 全部对象 × {LEGACY_POLICY_RANDOM, 新机制}；八子集 × 24 NATIVE）+ SA / PM / HG 剂量与持续性控制（四 owner × 两起点 × b × H {3,5,10,20}）+ 影子库存（144 + 父 + C1_hi + 六形态旧 K_HG10/H5）+ bootstrap 全部确定性配对路径。A0 输出 `measurement_count / operator_count / raw_id_count / exact_target_alias / account_alias / exposed_count / policy_count`；两张对账表（问题 → 对象、任务 → 对象）逐元组相等才开跑。

## 4. A1-auto（W15）
E6j 七项 + plan §13.2 七类细目；掩码事实字段（附录 B）机械填写；任一 FAIL 不得进入 A2；报告 `routing_review_A1_auto.md` 随 B 草稿附上；决策端人工 A1 移到 REVIEW。

## 5. A2 执行次序（决策端中途不动）
Stage 0 → A0 / A1-auto → **推导两段**全部 P / B 账户 → 封存推导段（`seal_deriv.json`）→ part1 + 记录 B 草稿（逐对象 exposure / 机制重要性 / 有效支持 / 推导读数 / 未解决限制；**不设"推导中位 ≤ 0 不进"的门**）→ E6k 后段授权条件核验（W11：方式 B 自动进入；方式 A 停等用户）→ **两后段**同版本一次算完 → 封存（`seal_post.json`）→ 随机 / bootstrap / MATCH-CAP / 影子 / 八子集 / 衰减场景 → part2 / part3 / mechanisms / carried → REVIEW_input + lessons_delta + limit_register + 闭包门 → **一次性交付**。中途只落盘并镜像，决策端不读；技术重试只允许相同代码 / 参数 / 输入；改算法沿 amendment 边界（W11）。

## 6. 政策合同（plan §9；只复述锁定值）
六条（用户 09-25）：δ .10；c 四段 ≥ −.10（NA 不自动满足）；d ≥ 12 / 17（2026 partial；另给 2010–2025 16 年敏感，**不替换分母**）；e 同资本同号（0 容差 1e−9）+ 对 `LEGACY_POLICY_RANDOM` 两后段为正（|真实 − 随机| < 2·MCSE → MC_UNRESOLVED → 不可判）；f A5 亿 κ.5 后仍过 c；正向 ≥ +.10；简单性（G4 用 median 配对差）——**这些只对原生四测量的历史连续性复现三句加法**；新算子不 chosen（W12）。FULL 主 profile、G4 并印；两套 size profile（W12）+ PORT3_T 第三列；`policy_provisional = true` 直到用户裁定；不因 C1 / 随机通过率改门（plan §9.3）；`policy_confirmation_status = confirmed_by_proceeding`（用户 09-28 指示写 brief；开工以用户转交本 brief 为准；经济裁定另记，见 W11）。

## 7. 随机、bootstrap、HAC（plan §10；锁定值）
`LEGACY_POLICY_RANDOM`（E6j 复现）与新机制内容置换分开登记；八子集 {∅, I, S, K, IS, IK, SK, ISK} 对 24 个 NATIVE 主配置，分层树不重叠、叶 < 2 不细分、主 ISK 顺序对齐 E6j 回退；每路径独立费用；首 1,024，MCSE ≤ .03 目标，512 增补，8,192 上限，不以收益符号停止；bootstrap：四段内分层 stationary，块长 20 / 60，各 2,000 次，所有对象共享索引，抽已生成配对 PnL 向量、不回喂 HG；HAC 主 lag H、敏感 max(2H, 20)，日历对齐不压缩缺口（保留 E6j 兼容列）；年度正数按原 17 标签；同时带用固定 comparison_id 的中心化差，**无新 FWER 门**。

## 8. 运行组织
先 profile（代表性对象：RP / HG / LX / 随机各一，报 RSS / 线程 / 单账户秒数），再报并发与时长（> 30 分钟先报用户）；起步 24、上限 **64**（E6j 用户已批到 64；再高须用户）、BLAS ≤ 4、`ulimit -u 4096`、`taskset -c 96-191,288-383`；不整块加载 npz；原子写（临时 → flush → checksum → rename → SUCCESS）；attempt_id 与 semantic_id 分开；按 PID + 启动时间 + 完整命令行管理自身进程组；HG / checkpoint 存每 gate 状态；缓存分层（目标权重别名只复用目标；账户别名须同 H / lag / 费用 / A / 基准 / 状态 / 末端）；试跑一律写临时目录，`verify/` 与结果目录只落最终产物（E6j #74）。

## 9. 交付与复核
plan §13.5 八件 + 机器表 + `limit_register.md`（L01 起）+ `E6k_MIRROR.md5`（三处）；WORKLOG 只记操作事实；`E6k_lessons_delta.md` 收拢判断与教训，**执行端不写共享 memory**；REPORT 交付即冻结；复核按协议 v1.1：规划端写 `E6k_VERIFY_brief.md`（预期值脚本现算，只写标量或随附文件）→ 执行端只读程序 V + §C 收尾 → 决策端 D + REVIEW → 用户裁定。

## 10. 禁区
不读 E7；不改四地基 / e6e–e6j / 生产 v2 / U34 / U35 / v3 / I11 / DEV；不按推导段收益预筛或改网格；不在出数后选 profile（LEGACY_EDIT5 / PORT3_LAG1 / PORT3_T）、随机机制、bootstrap 块长中较好的一套；不把研究块的好候选替换 144 主对象；不把新算子自动 chosen；不写"可以上线 / 半样本外 / 替代 E7 / 证实"类判词；不用 `hash()` 作随机种子；不 `git add .`；不删 results；不写登录 / 主机 / 账号信息；不清理遗留进程。

## 11. 自审记录（规划端 2026-09-28；四类不利因素 + 两问；执行端见此段方可开工）

| 类 | 不利因素 | 处置 |
|---|---|---|
| 代码 | 六种新接入 + 三门 + LX 是 E6j SLOT 之外的大量新代码 | Stage 0 第 3 类逐算子恒等锚（附录 A）；plan §16.3 脚本 47 重跑；A0 独立枚举对账 |
| 代码 | RP 求解器（milp / 指派）并列解与容差 | 词典序逐级解、容差在 A0 登记、DEV 重验证、`SOLVER_LIMIT` 隔离回退（plan §5.4） |
| 代码 | HG 状态跨分片 / 跨年 | checkpoint 状态 hash、串并行重放、`test_90` 类实测 |
| 代码 | size 坐标日期口径两种（T / T−1） | 两列并算并印；policy 用 z_T + LAG1 差值列；不择优 |
| 统计 | 39,142 描述符 / 段的挑选空间 | 主展示 144 事前定死；切片不进结论；随机通过率作机会基线；多重性表 |
| 统计 | 首看功效低（两后段合并 MDE80 ≈ 0.5） | 只报估计 / CI / 与推导差 / 随机位置，不用显著性、不用"三档"标签（plan §10.6） |
| 统计 | 政策 profile 未裁定 | 双 profile + `policy_provisional`；不阻塞研究 |
| 运行 | 存储（全描述符权重不可持久化） | W10 存储合同：掩码 + 日聚合全存，权重固定清单 + 可确定性重算锚 |
| 运行 | 耗时预估偏乐观（E6j lessons 17） | 分段计时 profile 先于长队列；并发按实测报 |
| 解读 | 新算子成败被读成旧对象确认 / 否定 | 原生对照保留；首看标签统一；plan §3.2 第四条 |
| 解读 | 条件随机份额被读成因果 | 八子集 + LX 四账户 + gross 归因分别命名（plan §2.5 / §6） |
| 解读 | 绝对值 / 符号、profile 差 | 同印带符号值；D 脚本逐 profile 实现（㊻ ㊽） |
| 流程 | 后段授权若用户未给一句话 | 方式 A 停等，不自行推进（W11） |
| 节奏 | 有没有把跑得快当约束 | 没有 |

**两问**：① 不利因素是否已最大程度降低——剩余最大风险是"同一历史反复研究"与"新算子多、首看功效低"，只能靠事前 144 冻结、原生对照并排、随机机会基线、标签纪律缓解，不能消除；② 没有把跑得快当约束。

**执行端开工信号**：见到本段即可按 §5 次序开工；开工前先完成"第一个动作"并在 WORKLOG 记一行（时间、本 brief sha256、附录 sha256、`PLAN_COPY.md` sha256）；后段授权按 W11 判定并写文件。
