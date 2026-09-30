# E6l —— 最终 brief（v1，2026-09-30）：续选门 × 一日价稳 —— 时间滤波 / 续选记忆 / 库存 / 状态的分离与适配（plan v1.1 全采纳 + 规划端调整 A1–A12）

用途：执行端开工文件。设计全文 = `exec_briefs/plans/E6l_plan_web_final.md` v1.1（1,748 行，152,579 字节，sha256 前缀 `e7385cb7`；规划端已复制到 47 `tmp/e6l_handoff/E6l_plan_web_final.md`，执行端复制为结果目录 `PLAN_COPY.md`；plan 不进 47 仓库的 exec_briefs），**本 brief 不重写 plan，只做三件事**：① 规划端在 47 上核过的源事实与身份（§1.3、W★）；② 规划端对 plan 的采纳与少数调整（§0.1 W / A 项；冲突处以本 brief 为准并写明理由）；③ 执行组织、登记时序、授权、交付与复核（协议 v1.1 + v1.2 追加项）。proposal `E6l_proposal.md`（`f79c523a`）是参考输入，不是设计权威；plan §1.3 / §2.8 / §10.3 / §11 对 proposal 的更正（α .5 不预设为"机制真相"、Munion 同资本不加门、撤销同换手插值、R-HG 改 R-MARK、16 格不给二项概率、状态样本不设 n ≥ 120）照单接受。上一轮读法 `E6k_REVIEW.md`（`8ef42f86`）、裁定 `E6k_RULING_20260930.md`（`b0a87798`）、复核 `E6k_VERIFY_report.md`（`7281cd63`）、事后口径 `E6k_REPORT_supplement_1.md`（`8b6dedc9`）、代码变更登记 `E6k_code_change_register.md`（`fd822bcb`）。执行端自检探针见附录 `E6l_brief_appendix_probes.md`。

**执行端第一个动作**（协议 v1.1）：完整读经验册——复盘台账 #1–#93 与纪律 ①–63（`E6l_proposal.md` §2.3 / §2.7 / 附录 C、`E6k_REVIEW.md` §7）、`00_协议.md`、`REVIEW_protocol_v1.md`（v1.1 节 + v1.1a）、`E6k_lessons_delta.md`（含 § 交付后 27–37 条）、`E6k_VERIFY_report.md` §3 E 项与口径说明、`E6k_code_change_register.md`；然后读本 brief §0、plan §0 / §4–§13，再编译登记清单。

**硬边界不变**：四地基（`data_loader / features_daily / event_study / pool_screening_v2`）与 e6e–e6k 脚本只读；新代码 `e6l_` 前缀放研究目录；`results/` 只增不删；白名单提交 + push main，不 `git add .`；任何文档 / 日志 / 提交不含登录信息、主机地址、账号名（文件属主、`/mnt/big/base/<账号>` 类路径一律脱敏）；不读 2026-03-27 之后任何真实行情（E7 守卫沿 E6i–E6k，攻击测试用合成未来数据）；生产 v2 / v3 展示候选 / U34 / U35 / I11 信号成分 / DEV / 源执行时钟不改——任何"通过"只产出《生产变更候选清单》，`deployment_authorized = false` 永远由用户改；E6k 复核所列 38 个遗留进程本轮不动（用户未裁）。**算力与时间不是约束**（用户 09-26 / 09-28 / 09-30）：plan §9.4 不承诺天数，Stage 0 实测每条路径耗时后在 WORKLOG 与 R0 给出区间，不为缩短而删既定任务。

---

## 0. 一句话问题与设计结论（plan §0；此处只复述锁定项）

**问题**：E6k 的正向线索 Q × HG10（四形态 FULL .53 / .52 / .54 / .54 vs NATIVE .36 / .36 / .23 / .25）混着三样东西——规则本身的选择集改变（HG_ONLY 不是费用项，plan §1.3A）、"曾入选"这一状态的信息、以及随 b 与 α 加深的小市值倾斜。本轮单一主题 = **时间信息如何进入 K 槽位的选择决策**：同一信息可以在测量端被平滑（TIME）、在选择端被记忆（MEMORY：HG 原样 / LAG1 / 会衰减的 HG / INV 库存参照）、在持仓端被延续，并按市场状态调度（STATE）；每一处都以可闭合账户读（ACCOUNT）。

**锁定项**：
- 主展示 **72 行** = 12 配方 × 六形态，α .25 × H5：`Q0:NATIVE, Q0:HG10, Q0:LAG1_10, Q0:DECAY5_10, Q0:INV10, Q_D3:NATIVE, Q_D5:NATIVE, Q_D5:HG10, Q_RANK5:NATIVE, Q_RANK5:HG10, Q_DEW5:NATIVE, Q_DEW5:HG10`；同 72 配方另印 α .5 剂量面板、α .125 参数邻域；任一剂量按同一正式尺子评分。
- 全量 **34,120 原始描述符 / 段**（CORE 15,840 / CONTROL 2,880 / MEMORY 5,760 / STATE 4,320 / OLD_RULE 1,320 / BRIDGE 1,440 / EDGE 2,160 / EDGE_OLD 240 / PARENT 160）；附属 KERNEL_DOSE 432 / INV_CAP_LOOP_PAIR 1,560 / STRICT250_STATE 96 / BOUNDARY_CONT_PARENT_PAIR 72 = 2,160 项；基础配对比较 172,440 条；随机 LEGACY_POLICY_RANDOM 与 CONTENT_COND_ISK_P5 各 9,720 基础 ID / 段（全部非 K0 对象在 H ∈ {1, 2, 3, 5, 10, 20}，含全部 α）、R-MARK 三机制 × 180 基础 ID；支持 / 秩坐标控制 432。数字由 plan §16.3 脚本编译，A0 以真实源 ID 重编并对账。
- 正式尺子（已裁）：六条 + **PROPOSED_PORT3_T**（形成日 T clean 市值分位；四段组合层紧区间 ⊂ [−3, +3]）`policy_provisional = false`；LEGACY_EDIT5 / PORT3_LAG1 / DISCLOSE / LEADER_VS_PARENT 并印（LEADER 只披露）；**不新增任何门**（plan §10.3：Munion 同资本、R-MARK ≥ +.10、随机通过率、状态 n、同时带下界都不是门）。
- 不做：SZL / INC / RP / POST2 / SA / PM（P42–P48）、HMM / SJM、订单簿、新 K 概念、T 腿、E7。

### 0.1 相对 plan v1.1 的采纳与调整（规划端 2026-09-30 在 47 核源码 / 账本后定；★ = 规划端核出的事实；W = 源事实；A = 调整；冲突处以本 brief 为准）

- **W01 plan 全采纳。** v1.1 §0–§17 为设计权威；§14.2 R01–R22 与 §14 L01–L34 的修订全部接受；§16.3 内嵌脚本（sha `fb9908d6`，727 行）规划端已抽出放 47 `tmp/e6l_handoff/e6l_spec_tests.py`，**在 47 冻结环境（Python 3.10.13 / NumPy 1.26.1 / pandas 2.2.3）实跑 129 / 129 PASS**，输出 `design_manifest.json` 34,120 / `policy_content_manifest.json` 9,720 / `memory_random_manifest.json` 180 / `support_manifest.json` 432 / `comparison_manifest.json` 172,440 / `audit_control_manifest.json` 2,160——执行端 Stage 0 再跑一次并把结果目录复制进 `stage0/plan_tests/`。
- **W02 Q 源（★）**：`e6j_features.b1` :120–131：`q = sdiv(1.0, d + EPS)`，`d = |log(close / lclose)|`，EPS = 1e−4，缓存 `J_B1_qCC`，方向 low_bad（价稳高 = 好），无放量条件、无 W20 / W60 基线；`S20lag = a20·q`，`a20 = x / lag1(rmean20 x)`。E6l 的 Q0 = 这个 q 经源市值 OLS 中性化 + 方向 + 秩后的坏度 kQ；Q_D / Q_DEW / Q_QMEAN / Q_DMED 的 raw 量由 `data['close']` 与 `data['lclose']` 逐日现算（字段见 W07），**只在形成日 T 做一次源中性化与排名**（plan §4.2）。
- **W03 HG 源（★）**：`e6k_ops.hg_gate(st, sc, b_eff, tid_ids, init_cols=None, return_state=False, hold_init=False)` :185：`s_HG = s − b_eff·1(上一形成日本账户门内成员)`，当日技术合法域取无带门同数 `dom.K[d]`；`b_eff = b · st.bunit`，`Struct.bunit = 1 / (100 · nlegs)`（`e6k_env.py:173`；A4b / union nlegs = 1，mean = 3 → b/3）；`b_eff == 0` 直接回无带门（源平局端点）；`hold_init` 只供跨段连续诊断，登记账户恒 False。plan §5.1a "b 以 K 坏度百分位点登记、0–1 评分上 5 点 = .05" 与源一致。PM / SA 本轮不用。
- **W04 门与合法域（★）**：`e6k_env.Struct`：kind A4b（门 = K 第一关；下游 = T 在幸存集重中性化 + 第二关 + 否决）/ union（门 = K keep 50；下游 ∧ T / cr20 通过域 ∧ ~CVR）/ mean（门 = 综合分门；下游 ∧ ~否决）；`legal()`：A4b = ids ∧ T_raw 有效 ∧ ~drop、union = ids ∧ base、mean = ids ∧ ~drop——这就是 plan §5.1a 的 `E_t`；`gate_scores / gate_keep(dom.keep) / down / kept`；`order_keys` 为 E6j matched_n 合同键。新测量缺失 → 回 k0（FALLBACK，`e6j_slot.blend_q`），不清记忆（plan R07）。
- **W05 费用与库存时钟（★，定 INV 的合同）**：`comprehensive_factor_diagnosis.compute_calendar_pnl` :488（2026-09 E1 定稿）：持仓 = 形成日权重 `rolling(hold_days, min_periods=1).mean()` 再 `shift(2)`（T 收盘出信号、T+1 VWAP 成交、收益为回看日收益）；**每笔 T+1 VWAP 进、T+1+H VWAP 出**；换手 = |Δ持仓| / 2；成本 = 换手 × 8bp / 1e4（双边名义）；`e6i_sparse.SparseEngine.pnl` :85 同式（E6k c2 ≤ 1e−12）。由此：T 日成交完成后的库存 = 形成日 τ ∈ [T−H, T−1] 的批次（各 1/H 权重），T+1 到期退出的批次 = τ = T−H，T+1 的逐票净订单 = (W_T − W_{T−H}) / H——**plan §5.5 / §5.5a 的示意公式在源引擎下就是精确式**（均匀批次、固定 1/H、无价格漂移权重）；INV10 的标记 A_i,T = Σ_{τ∈[T−H,T−1]} W_τ,i > 0。INV 目标路径依 H 递推，不得复用他 H 的名单。
- **W06 DEV（★）**：`e6i_sparse.SparseEngine.dev` :61 = 源 `export_delivery_pools_v2.assign_weights_dev` :71–84：w0 = min(1/n, 1%)，行业组和 > clean 数量份额 + 3% 按比例压缩，不归一。
- **W07 数据与允许历史（★）**：`load_all_daily_data(start, end)` 字段：open / close / high / low / lclose / vwap / volume / amount / turnover_rate / change_pct / mcap / adj_factor / industry / flag_st / industry_zx1；`e6j_prod.build_period` 逐段只加载该段窗口（缓存 `daily_kline_20100104_20141231` 等），另有全程缓存 `daily_kline_20100101_20260327`；**行情最早 2010-01-04，没有 2010 年之前的数据**。段日历：2010-01-04…2014-12-31（1,212 日）/ 2015-01-05…2018-12-28（975）/ 2019-01-02…2023-12-29（1,214）/ 2024-01-02…2026-03-27（539）；每段前 19 个交易日为预热（形成日 1,193 / 956 / 1,195 / 520）。→ **A1 状态变量按全程日历算**：Vol3 / Act3 / Trend3 在全程缓存上逐日 PIT 计算后按日期并入各段（段 2–4 的 250 日参考取自前段"允许历史"，plan §6.1）；**段 1 的前约 250（Vol3）/ 约 330（Act3：60 日比值 + 20 日均 + 250 参考）个交易日为 STATE_UNKNOWN → b10 回退、照跑照报**；Stage A 必印每段每变量 UNKNOWN 日数。主四段账户仍按源分段预热约定（可比 E6k 锚），连续状态面板另做（plan §5.6）。
- **W08 E6k 锚（★，跨轮身份第一层）**：E6k 结果目录 `results/20260928_2325_E6k_k_binding_stage/`，`results/full/policy_E6k.csv` sha 前缀 `3ab02a59`（38,982 × 186）。E6l 中与 E6k 完全同构的对象（Q / C1 × {NATIVE, HG5, HG10, HG15}、S / M × {NATIVE, HG10}、K0 × HG_ONLY{5,10,15}、PARENT，六形态 × α × H）**逐值 = E6k**（≤ 1e−9；D / D_sc / FULL / G4 / 段 n）；锚值举例（四段 D；FULL；FULL_sc）：`Q|A4b_CVRv5|a0.25|H5|NATIVE` .329105 / .735040 / .152763 / .245640；.363769；.345993；`…|NATIVE_HG10` .406365 / .780853 / .362650 / .644916；.517601；.485757；`K0|A4b_CVRv5|a0|H5|HG_ONLY10` .189921 / .322932 / −.066850 / .015769；.119983；.113722；`Q|M_union3_v2_CVRv5|a0.25|H5|NATIVE_HG10` .237350 / .667346 / .643610 / .730216；.535706；.205062。HG_ONLY10 H5 FULL 六形态：A4b .1194 / A4b_CVRv5 .1200 / Mmean −.0044 / Munion .0631 / Munion_CVRv5 .0151（Mmean_CVRv5 见 policy）。这些对象标 `SECOND_EVALUATION_SAME_HISTORY`，只作锚与基线。
- **W09 plan §1.3B 的 −2.8（★，已查）**：`Q|A4b_CVRv5|a0.5|H5|NATIVE_HG10` 四段组合层 lo_T / hi_T = −4.018 / −5.176 / −2.806 … −2.804 / −5.676（PORT3_T FAIL 因三段 < −3，不是 2019-2023 那一点）；`…|a0.5|H5|NATIVE` = −0.913 / −1.669 / +0.286 / −2.485（PASS）；α .25 HG10 = −1.944 / −2.281 / −1.921 / −2.329（PASS）。proposal §0 / §1.2 把 −2.8 与"出 ±3"连写是决策端读法错（决策端记复盘候选），plan 的处理（Stage 0 读四段区间）成立；**剂量面板照印，不预判**。
- **W10 随机源（★）**：`e6k_random.Legacy`（P 机制 = `FAST.Assigner` 对当日有限 kf 的 IID 置换，缺失位置不动；B 机制 = `DonorMapper`；`path_key('E6j.P', mid, 'P_production_v2', 'native', 'IID', path)`）= plan §7.4 的注入点（完整平滑 / 中性化 / 方向之后、HG 之前）；条件树 `tree_leaves(seg, valid, k0, subset)` 变量序 I > K > S、任一子叶 < 2 则父节点不细分 = plan §7.3 R-MARK ISK 回退树合同（行业 → 旧 K3 → size3，每名恰属一叶）。新测量成员沿同一 `path_key` 族命名，绝对日期块 P5 沿 E6k。
- **W11 授权三件分开（用户 09-26 / 09-30；RULING 第 1 项）**：(a) 开工 = 用户把本 brief 转交执行端；(b) 两后段 = E6l 自己的完整清单授权：转交消息含"B" / "事前整表授权"、或明确一句"按这个完整方案一口气执行"且范围含两后段 → **方式 B**（Stage A / B 两包冻结时写 `registration/record_B_preauthorized_E6l.json`，引用原话 + 日期 + 清单 sha；生效条件 = Stage 0 全 PASS + A1-auto 全 PASS + 进入后段时清单 sha 不变，任何语义 amendment 使其后代授权失效）；否则 **方式 A**（推导两段算完、封存、记录 B 草稿后停，等用户一句话；E6k 先例：用户"继续推进就好"= 批准，RULING 第 1 项）。不把文件名里的 B、本次写 plan / brief 的请求、E6k 的批准回执当授权。(c) 经济裁定 = RULING 第 2 项已给 → PORT3_T 列 `policy_provisional = false`；E6k §11 第 3–10 项按 REVIEW 建议（proposal 前置），不影响本轮登记。
- **W12 政策合同**：沿 E6k `policy_profiles_E6k.json` + PX1–PX6 文本逐句复现（Stage 0 转录），加：PORT3_T 主列；**PX 文本补写 LEGACY_EDIT5 未定义段处理**（只在有编辑日的段上判、四段全无编辑 → 状态词 `UNDEFINED`，纪律 ㊿ / 56）；状态词禁用 `N/A / NA / nan / null`（读写 `keep_default_na=False`）；新算子 / 新表达 `replacement_preference_status = NOT_AUTHORIZED`、不 chosen、不继承三句加法资格（plan §10.1）；同构对象 `SECOND_EVALUATION_SAME_HISTORY`；新对象 `NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY`；每对象七列证据状态（plan §10.4）。
- **W13 随机与精度锁定**：LEGACY_POLICY_RANDOM 与 CONTENT_COND_ISK_P5 对 9,720 基础 ID / 段（H ∈ {1, 2, 3, 5, 10, 20} 全部非 K0 对象，H5 含全部 α——补 E6k 的 α 网格洞）；同形成名单跨 H 共享路径、费用与持有独立算；**INV 与 STATE 调度按 H 独立递推**；R-MARK UNIFORM_IID / UNIFORM_P5 / ISK_P5 对 180 基础 ID（Q0 / Q_D5 / Q_RANK5 / K0 × HG10 × H {1, 5, 20} × 六形态 × 适用 α）；OLD_RULE 无内容随机 → `NO_NEW_CONTENT_TO_PERMUTE`（PX6 同类）；首 1,024 路径永久保留、按 512 增补至 MCSE ≤ .03 或 8,192、共享配对组同路径集、Welford / 两遍方差、恒等路径 sd = 0 单独核（E6k E01）；MCSE 与时间 HAC / bootstrap 分列（plan §7.5）。
- **W14 环境与算力（★）**：47：384 逻辑核、2.27 TB 内存、`/mnt/sda2` 余 37 TB；共享 python3 = Python 3.10.13 / NumPy 1.26.1 / pandas 2.2.3 / SciPy 1.11.3 / statsmodels 0.14.0 / numba 0.58.1；**polars 不在共享环境**（E6k 执行端私装 1.44.2 于用户目录；本轮若用须写进 `source_manifest.env` 并给纯 numpy 回退）；核绑定 `taskset -c 96-191,288-383`，并发起 24 上限 64（用户 E6j 批准），BLAS ≤ 4，`ulimit -u 4096`；plan §16 环境（3.13 / 2.3.5）只是 web 侧，不是 47。
- **A1 状态变量的允许历史**：见 W07；执行端在 Stage 0 第 4 类加"状态序列截断重算恒等"探针（附录 A4-5）。
- **A2 α .5 面板**：接受 plan（不预设为机制真相）；决策端 REVIEW 会在两剂量上并读机制符号，配对 se 在结果阶段算（plan §11.1）。proposal 的"α .5 = 机制读数配置"表述作废。
- **A3 Munion 同资本**：接受 plan §10.3——FULL 与 FULL_sc 双主视图，不加门；`MATCH_CAP_FIXED_PATH` 为源政策 FULL_sc，`MATCH_CAP_INV_LOOP` 只作 INV 诊断。
- **A4 R-MARK 替代 R-HG**：接受 plan §7.3；三机制路径自状态递推。
- **A5 撤销同换手插值**：接受 plan §7.6；真实前沿 + 逐对费用交叉点 c* + "单位收费量收益诊断"。
- **A6 计算规模**：附录 A6 要求 Stage 0 用合成 + 源锚任务实测每条路径（排序 / 递推 / DEV / 账本 / IO）耗时并外推区间写进 R0 与 WORKLOG；不设上限；真实资源不足 → 完整队列 + checkpoint 暂停未完成块，不删任务、不抽参数（plan §9.4）。
- **A7 Q_RANK 延伸的源系数合同（★）**：plan §4.3 需要"u 当日源 Q 中性化的参考样本、系数 / 回退模式"。源 `comprehensive_factor_diagnosis.precompute_neutralized_factor(factor, filtered_pool, log_mcap)` :315 对 pool0 成员逐日调用 `pool_screening_v2.neutralize_by_mcap(factor_vals, log_mcap)` :292（四地基，只读）：截面 OLS `factor ~ α + β·log_mcap` 取残差（`beta = cov(x, y, bias=True) / var(x)`），**有效样本 < 10 只时原值直返（不中性化）**；`precompute_neutralized_factor` 另在 pool0 成员 < 6 或有效残差 < 6 时跳过当日。系数不落盘 → 执行端按同一函数体在 u 日 pool0 成员上**重算** (α_u, β_u) 与回退状态，再对当时 clean 池外股票算残差并按 plan §4.3 单调插值映射到源秩；Stage 0 探针：pool0 成员重算残差与秩 = 源缓存逐位、回退日集合一致（附录 A3-11）；无法取得等价系数合同时只隔离 RANK 延伸后代（plan §4.3 末），D / EW 主线不受影响。
- **A8 手册与原件**：plan §1.1 / §15 记三本内部手册与 E6k VERIFY / supplement / code_change_register 未在 web 侧取得。执行端侧：E6k 三件在 47 `exec_briefs/` 与结果目录 `reports/`（Stage 0 A1 核 sha）；三本手册是决策端输入、不在项目目录、**没有任何可执行定义依赖它们**，附录 A1-2 记 `NOT_REQUIRED`，不标 `SOURCE_NOT_OBTAINED`。
- **A9 复盘血缘**：plan §3.1 的 `hypothesis_lineage.csv` 字段沿用；复盘编号不自改 #77–#93；本 brief 的 W09 记为决策端读法错候选（下轮 REVIEW 编号）。
- **A10 报告卫生（纪律 56–63 进生成器）**：段均列 `_segavg`（57）；统计量列名带单位、同时带印 `q95_maxabs_t` 与 `halfwidth_ann_pp` 两列（58）；"全部 / 所有 / 从不 / 仅由"句由查询生成或附分母（59）；supported_scope 每个数字带产生它的 query_id 且该表印出该数（60）；事后补做的诊断表头写"事后"及发现时间（61）；brief / R0 正文计数取脚本输出（63）；代码变更登记为固定 §C（E6k C-7 格式：before / after sha、时间、范围、触发、影响面、等价证据、反向撤回逐字节还原）。
- **A11 决策端中途不动**（E6j RULING）：整轮一次性交付前不读中途产物；A1 人工判断在 REVIEW；A1-auto 机械对账阻断 B 草稿。
- **A12 名称**：结果目录 `results/<时间戳>_E6l_time_memory_stage/`；新模块 `e6l_*.py`；登记 / 封存 / 记录 B / 回执文件名沿 E6k 模板换 `E6l` 后缀（plan §13.2；`post_gate` 清单文件名核两向，E6k lessons 17）。

### 0.2 "跑久一些、多用算力都没关系"的落法
全 H 1…20；α 三档；六形态 + R2 / A06 参照曲线；LEGACY + COND 随机对 9,720 基础 ID 全排（E6k 只排 956）；R-MARK 三机制；连续状态面板与连续父；MATCH-CAP 两视图；bootstrap 2,000 × 两块长；状态三时钟；前沿全格；附属 2,160 项；172,440 条比较逐条闭合。不以"快"为红利；唯一的节奏约束是登记 / 封存 / 授权的先后（§5）。

---

## 1. 起点确认与契约

### 1.1 起点
- 47 HEAD = 远端 main = `ec91def`（E6k VERIFY 提交）；`git status` 只有既知 untracked（chain / wave 脚本 7、单因子脚本 3、exec_briefs 下决策端 / 裁定文件 11 + E6k VERIFY 输入 2）——开工前记 `identity_at_start.json`。
- 只读输入：E6k 结果目录（W08；`accounts/`、`randoms/`、`registry/`、`registration/`、`results/`、`stage0/`、`verify/`）；E6j 结果目录 `results/20260927_0038_E6j_k_two_dimension_pilot/`（Q / RARPRE B 块账户、E6i 母体锚、`pilot_policy.csv`）；E5a v2 交付目录（六 pool2）；E6j `cache/<段>/J_B1_qCC.npy`、E6i `cache/<段>/K_rar20__OBS.npy` 等（sidecar sha）。
- 决策端交接件（三处镜像：本地 / 47 `exec_briefs/` / 结果目录副本）：本 brief、附录、proposal、E6k REVIEW / RULING / VERIFY_report / supplement_1 / code_change_register、协议两件、plan（`tmp/e6l_handoff/` → `PLAN_COPY.md`）、spec 脚本 `e6l_spec_tests.py`（`fb9908d6`）。

### 1.2 数据与生产锁
行情终点 2026-03-27（`market_data_end_max`）；全程缓存只用于状态序列与连续面板的允许历史（W07 / A1），主四段账户沿源分段加载与 19 日预热；I11 / 观察窗 5 日 / 硬约束 / CVR k5 否决 / 源市值 OLS / DEV / T 收盘 → T+1 VWAP / 后复权 / 8bp 收费函数不改；H 是研究维度、生产 H5。

### 1.3 契约（规划端已核；执行端整段读函数体复核并写 `engine_contract.md` + `source_resolution.md`，每条 定义处 / 调用处 / 默认值 / 证据）
1. 生产路径与六形态：`e6j_prod.build_period` :92（源 :96–119 逐字）→ `form_masks`（源 :120–128）；A4b = K 第一关 → 幸存集内 tvol 中性化 → 第二关；Mmean = combine mean keep 50；Munion = 三腿剔尾集之外；CVRv5 否决（E6k c2 A2-1 逐字节 = E5a）。
2. 门与合法域：W04。
3. 费用 / 库存时钟：W05；净费恒等 d_net8 = d_gross − 8e−4·d_turn（E6k VE01 全量残差 0）；年化 = 252 × 100 × mean；段 D = 252 × 100 × (mean 子 − mean 母[K0, H])，n = 共同有限日。
4. DEV：W06。
5. 测量：W02（Q0）；Q 平滑族 / 秩延伸族 / 桥按 plan §4.2–§4.4a 逐条实现，raw 量只在 T 做一次源中性化 + 方向 + 秩；EW 用 plan §4.2 的绝对日期归一化递推；有效数 ≥ ceil(.6k) 且当前 d 有效；λ = 1 短路回 Q0。
6. 记忆：W03（HG）；LAG1 / DECAY / INV 按 plan §5.3–§5.5a；`E_t` = W04 `legal()`；零 bonus → `source_U` 及源 ties（R06）；名额不可行 → 报错不缩；checkpoint 保存 `previous_U / previous_G / last_confirmed / EW A,B / 库存批次 / 股票身份 / 状态哈希`（R04 / R05）。
7. 状态：plan §6.1 三变量 PIT（≥ 150 / 250 有效参考主定义 + STRICT250 诊断；Trend3 端点法）；四调度 §6.2（UNKNOWN → b10）；三时钟 §6.3；对称分解 §6.4。
8. 随机：W10 / W13。
9. 同资本：`MATCH_CAP_FIXED_PATH`（源 `e6k_acct.ledgers(par=…)` sc_child / sc_parent 逐日缩到 min(Pc, Pb)）= 政策 FULL_sc；`MATCH_CAP_INV_LOOP` 新增诊断（plan §8.2）。
10. 尺子：W12；紧区间函数沿 E6k（未知 size 共同变量相消）。

### 1.4 事前登记（G1 两阶段 + G6–G11）
Stage A（任何收益读取之前落盘）：对象 sha、掩码层事实表（附录 B）、状态 UNKNOWN 日数、INV 标记覆盖与饱和、R-MARK 分区叶统计、Q_MA 有效数份额、RANK 延伸覆盖、尺子校准分布（附录 C）、配对 MDE80 表（推导段 child − child 日差 HAC(H) se × 2.80，只在推导段账户算完后、后段之前；⑬ 据此写）→ Stage B（16 张卡 plan §12 逐条绑定比较 ID 与 query_id；模板 v4 ⑮–⑱ 由 A0 机械字段填充；`hypothesis_lineage.csv`）→ 推导两段 → 封存 → 记录 B（W11）→ 后段 → 政策 → 交付。

---

## 2. Stage 0 六类起点核验（plan §13.1；任何账户之前；附录 A 逐项）
1 身份 / 权限；2 源账户与 E6k / E6j / E6i / E5a 锚；3 新算子恒等（MA1 / EWλ1 / b0 / α0-ONLY / DECAY∞ / LAG1≠HG / INV 排除当日与 H 相依 / KERNEL_DOSE 退化 / 源平局零 bonus / checkpoint 拆分 / RANK 延伸源锚）；4 数据 / 时钟（E7 守卫、状态 PIT 截断恒等、允许历史、复权同源）；5 随机 / 状态（显式种子、E6k 同路径复现、R-MARK 分区、退化组计数）；6 输出 / 资源（耗时实测、内存、回执、状态词、单位、固定表存在性）。任一 FAIL 阻断依赖包；FAILED 回执由同名 `_rerun` 覆盖（协议 v1.1 第 5 条）。

## 3. A0 登记（执行端编译；不等收益）
把 plan §16.3 的 34,120 / 72 / 9,720 / 180 / 432 / 2,160 / 172,440 用真实源 ID、policy、授权、附属控制与输出 schema 重编（`registry/descriptors_E6l.csv` 等），与 spec 输出对账（计数逐块相同、ID 元组集合相同）；`comparison_manifest` 每条含系数 / 左右 ID / view / 共同行情日 / 聚合 / 单位 / 源费用 / query（plan §9.3a）；固定输出清单（plan §13.4 十五张表）生成空骨架，每个 query_id 真实有表（E6k lessons 21）。

## 4. A1-auto（机械对账；任一 FAIL 阻断 B 草稿）
沿 E6k 七项（登记对账 / 五列 profile 文本 / 卡 queries 非空 / 词表 / 锁定值 / 固定输出 / 暴露台账）+ 本轮：⑧ 每个 STATE 对象带状态变量定义 sha 与 UNKNOWN 回退登记；⑨ 每个 INV 对象 H 进状态键；⑩ 每个平滑对象带核 ID / 有效数规则 / λ；⑪ 每条 R-MARK 机制带分区合同；⑫ 状态词扫描无 `N/A / NA / nan / null`。掩码事实字段见附录 B。

## 5. A2 执行次序（决策端中途不动）
Stage 0 → A0 → Stage A（掩码事实 + 校准 + 配对 MDE80 表在推导段账户后）→ Stage B（卡与预测冻结）→ 推导两段确定性账户 → 推导段随机（LEGACY / COND / R-MARK 首 1,024）→ MC 增补 → `seal_deriv` → 推导段统计 / part1 / 记录 B 草稿 → **W11 授权**（方式 B 直接过；方式 A 停等）→ 两后段确定性 + 随机 + 增补 → `seal_post` → 全段统计 / 政策 / bootstrap / mechanisms / 状态 / 连续面板 / 附属 2,160 → 七份 REPORT + cards → REVIEW_input → 闭包门 → 一次性交付 → 协议复核（决策端 VERIFY brief 预期值脚本现算；执行端 §C + V；决策端 D + REVIEW；用户裁定）。

## 6. 政策合同（plan §10；只复述锁定值）
δ .10；c 四段 D ≥ −.10；d years_pos ≥ 12 / 17（16 年与 10 / 17 敏感列并印）；e 资本 sign(FULL) = sign(FULL_sc)（tol 1e−9）；e 随机 两后段 rmr ≥ 2·MCSE（PX3 未排 → RANDOM_NOT_SCHEDULED 不可判；OLD_RULE → NO_NEW_CONTENT）；f A5 κ.5 后四段 ≥ −.10（A10 κ1 压力列）；正向 ≥ +.10；三句加法 PX1 只对原生四测量 + SM；五列 size 并印、**PORT3_T 为正式列**；判定串顺序 c、d、f、正向门槛、e资本、e随机、size(profile)；`POLICY_INTERPRETATION_PENDING`；边缘清单列全部条件距离；`SECOND_EVALUATION_SAME_HISTORY` 对象不进"本轮新证据"栏。

## 7. 随机、bootstrap、HAC（plan §7.5 / §11；锁定值）
W13；bootstrap = 段内分层平稳、平均块长 20 / 60、各 2,000、同 draw 用于所有相关账户 / 形态 / 状态、四段各保样本量；HAC 主 lag = H，补 max(2H, 20) 与 60；配对 se 用 child − child 共同日历日差（plan §11.1）；同时带两单位列；bootstrap 比较前缀沿 E6k（CP / CN / CC1 / CB / CH）加 CM（机制配对）与 CQ（对 Q0 HG10）；状态条件均值按 plan §11.2a 缺日 HAC；`INSUFFICIENT_REPLICATE_SUPPORT` 显式；不设 FWER 门。

## 8. 运行组织
W14 核绑定与并发；`ssh -f` 后台 + 完成标记（E6k lessons 6）；等待循环只按显式 PID（lessons 7）；`df['flags']`（lessons 8）；npz 整读（lessons 9）；队列逐行回执核对（lessons 20）；守卫两向实测（lessons 17）；求解器无（本轮无 MILP）；缓存键含 measurement / operator / α / b / H_state_dependency / source_mode / support_view / seed / absolute_start / state_hash / input_sha / code_sha（plan §13.3a）；stateful 对象不当无序 map；checkpoint 完整状态；成功回执含参数 / 输入 / 输出 sha、行数、状态、代码、对照 ID、query 闭包；临时写 → flush → checksum → 原子 rename；代码变更逐文件登记（A10）；WORKLOG 只记操作事实（时间、脚本 sha、耗时、并发）；lessons_delta 六类标注、不写共享 memory。

## 9. 交付与复核
七份 REPORT（R0 / part1 / part2 / part3 / mechanisms / carried / cards）+ REVIEW_input + lessons_delta + limit_register + code_change_register + 完整 manifest / 授权 / 回执 / 源合同 / 环境 / 日账本索引；固定表十五张（plan §13.4）+ 本 brief 追加：`paired_mde80_deriv`、`state_unknown_days`、`inventory_saturation`、`membership_age_ledger`、`frontier_dose_tilt`；表头十项 + 主体 + exposure + query_id；每个数带主体 / 参照 / α / H / b / 时间支持 / 费用 / 聚合权重 / 单位 / query_id；REPORT 交付后冻结，补充另起 supplement；三处镜像 MIRROR；git 白名单。复核：决策端 `E6l_VERIFY_brief.md`（预期值脚本现算、只写标量或随附文件、正文计数取脚本）→ 执行端 §C（含代码变更登记复核）+ V（只读、不 import、独立核对象语义与取数集合）→ 决策端 D（先转录字段含义、两行手算再批算）+ `E6l_REVIEW.md`（尺子先写）→ 用户裁定 → `E6l_RULING`。

## 10. 禁区
不改生产 / 地基 / U34 / U35 / v2 / v3 / I11 / DEV / 源时钟；不读 E7；不动 E6k 结果与 38 遗留进程；不 `git add .`；不 `pkill -f`；不删 results；不在文档 / 日志 / 提交里出现登录信息 / 主机地址 / 账号名；不把合成 PASS 当真实回测；不用 α .5 / HG20 / 30 / 任何未排随机对象自动进候选；不因慢删任务；不中途改预测；不用 `N/A` 类状态词；不复用不同 H 的 INV 名单；不把 `MATCH_CAP_INV_LOOP` 写进正式 FULL_sc；不读决策端 REVIEW 草稿。

## 11. 自审记录（规划端 2026-09-30；四类不利因素 + 两问；执行端见此段方可开工）

| 类 | 不利因素 | 处置 |
|---|---|---|
| 代码 | 11 个 Q 表达 + 4 种记忆 + 4 种调度 + 秩延伸 + INV 库存 + R-MARK 三机制 + KERNEL_DOSE + INV_LOOP，是历轮最多的新算子 | plan §16.3 129 项合成规范已在 47 冻结环境实跑 129 / 129；Stage 0 第 3 类 11 条恒等锚（附录 A3）；E6k 同构对象 ~4,000 个逐值锚；checkpoint 拆分一致性在真实账户上核（A3-9） |
| 代码 | 状态变量的允许历史与 PIT | W07 / A1：全程缓存、`shift(1)`、截断重算恒等探针、UNKNOWN 日数必印；段 1 前 250–330 日 UNKNOWN 照跑照报 |
| 代码 | INV 库存时钟与源引擎不一致 | W05 用源 `compute_calendar_pnl` / `SparseEngine.pnl` 逐字核出 T+1 进、T+1+H 出、均匀 1/H 批次——plan 示意式在源下就是精确式；A3-6 用 E6k 账户 `d_pos` 逐日核 |
| 代码 | 中途改代码无登记（E6k 四文件） | 代码变更登记固定 §C；守卫两向实测；attempt / revision / 首读时间 |
| 统计 | 34,120 描述符 + 172,440 比较的挑选空间 | 主 72 与配方事前定死；两剂量并印不择优；随机对 H5 全 α 与五个 H landmark 全排；同时带带单位；多重性表；exposure 账本记全部已见选择史（W09 的 α .5 数字已见） |
| 统计 | 机制差 ≈ .05–.1 vs 单对象 se .3 / .45 | 配对 child − child 四段日差 HAC se（结果阶段算，不预设可判）；Stage A 推导段配对 MDE80 表；两剂量并读；不靠量级的判别列（H 剖面形状、成员留存率 / 年龄、R-MARK 置换精度、16 格符号矩阵 + 共享日期重采样） |
| 统计 | 状态条件样本少、Trend3 个股级不能给组合贴标签 | 三时钟分开（plan §6.3）；短样本照报带 n；对称分解只在共同支持状态上闭合 |
| 统计 | 库存标记饱和（长 H 全域标记 → 规则 no-op） | 覆盖饱和与差异 bonus 计数必印（R03）；不下"无信息"结论 |
| 运行 | 随机规模约 E6k 的 4–5 倍 | Stage 0 实测耗时外推区间；分批 / 内存映射 / 共享分数 / 固定 seed 流；checkpoint 暂停不删；不承诺天数 |
| 运行 | 授权方式再次落成方式 A 停等 | W11 写明三种触发方式 B 的原话形式；用户转交时可选 |
| 解读 | 列义 / 单位 / 分母（E6k 决策端 7 处 + 同时带单位） | 纪律 ㊾ / 56–58 / 63 进生成器与 D 脚本；`_segavg`；两单位列 |
| 解读 | 规则贡献被读成费用份额、"换手更低"一句话 | 四账户 gross / 费用 / 冲击 / 资本分列（plan §7.1）；相对母体编辑数与自身换手分列 |
| 解读 | 同构对象再评被当新证据 | `SECOND_EVALUATION_SAME_HISTORY`；候选清单分"上一轮 / 本轮新证据"两栏 |
| 解读 | "无增量"写成"证伪" | 纪律 62；结论词表固定 |
| 节奏 | 是否把跑得快当约束 | 没有：§0.2 全部保留；实测后报区间，不缩 |
| 流程 | E6k §11 第 3–10 项未单独裁 | 不影响本轮登记（RULING 第 2 项已给尺子）；候选清单按 REVIEW 建议分栏，用户审 proposal / REVIEW 时改 |

**两问**：① 不利因素是否已最大程度降低——剩余的是：真实订单方向 / 成交冲击未知（κ 未校准，只作情景）；同一历史反复使用（首评非样本外，标签写死）；状态变量只有三分位一种定义（不调参是为了 PIT 与持续性，代价是可能错过更好的状态定义——留给下一轮）；② 没有把跑得快当约束。

**执行端开工信号**：见到本段即可按 §5 顺序开工；开工前在 WORKLOG 记一行（时间、本 brief sha256、附录 sha256、plan sha `e7385cb7`、spec sha `fb9908d6`）。
