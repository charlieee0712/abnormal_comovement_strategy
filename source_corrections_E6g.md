# `source_corrections_E6g.md` —— E6g 阶段 0 的源码与文档更正

规则：**只记录，不改地基文件**（硬约束 ③）。每条给：声称 → 实测 → 证据文件 → 影响 → 处置。
四个地基文件、七个 `e6e_*.py`、十九个 `e6f_*.py` 的 SHA256 在 `source_manifest.json`，本轮未改动。

---

## §1 涨跌停过滤：实际走的是 OR 分支，不是回退分支；且 OR 写法恒真

**声称**（brief §1.3 / proposal）：「`data_loader` 的字段表没有 `limit_up/limit_down`，规划 session 判断实际走的是
回退分支」——即未复权 `close/close.shift(1)` 的 ±9.8%，会把除权日误当跌停剔除。

**实测**：`data_loader.load_all_daily_data` 的 `load_limits` 默认 `True`，调 `load_limit_prices()`
把 `limit_up / limit_down / flag_buy / flag_sell / flag_st / industry_zx1` 一并放进 `data`
（`data_loader.py:279–285`，`guarded_load` 不覆盖该参数）。四段 `limit_up > 0` 的**日覆盖率都是 1.000**，
第一个有值日就是每段首日，故 `has_limit_data` 恒为 `True` → **四段全部走 OR 分支**。
而 `not_limit = (close < limit_up − 0.01) | (close > limit_down + 0.01)` 在 `limit_down < limit_up` 下**恒真**
（缺值格被 `align(fill=0)` 填 0，`close > 0.01` 仍为真），本意应是 `&`。

| 段 | 观察池格 | A 源 OR（实际剔除） | A2 本意 AND | B 回退未复权（未执行） | 回退分支会误剔的除权日 |
|---|---|---|---|---|---|
| 2010-2014 | 262,188 | **0** | 2,281 (0.87%) | 2,530 (0.96%) | 204 |
| 2015-2018 | 280,587 | **0** | 7,989 (2.85%) | 8,398 (2.99%) | 191 |
| 2019-2023 | 506,729 | **5**（`close ≤ 0.01` 退化行） | 6,685 (1.32%) | 7,961 (1.57%) | 246 |
| 2024-2026 | 276,097 | **0** | 4,416 (1.60%) | 5,779 (2.09%) | 63 |

**证据**：`H0/pool_facts_<段>.json`、`H0/limit_hits_<段>.csv`、`engine_contract.md` §1。

**影响**：结论方向与 brief 一致（过滤是名义的、pool0 含涨跌停日），但**机制不同**：不是「用错公式剔了 1–3%」，
而是**一格都没剔**。因此 brief 担心的「除权日被误当跌停剔除」在本轮**不存在**；同时
「pool0 里 0.9%–2.9% 的形成日 × 票其实当天涨跌停、VWAP 不一定成交得到」是**真的**，
这条只能在影子账户与标志层处理。

**处置**：地基不改；`registry/`、`H0/limit_hits_*.csv` 逐段逐年给涨跌停计数列（必交项）；
T0 协变量、K3 流动性规则、L-X 提前退出的解读都带这一列。若将来数据缺涨停价而落到回退支，
上表 B 列与「除权误剔」列就是那时的量级。

---

## §2 E3 标签：日超额算术累加，基准是 `base_pool`

**声称**（brief §4）：「主标签严格复用 E3 的 `compute_forward_5d_excess`（bench = pool0 等权、已复权）」。

**实测**（`comprehensive_factor_diagnosis.py:209`）：
`sum(excess_daily.shift(-k) for k in 2..1+hold_days) × 1e4`，`excess_daily = vwap 日收益 − 基准日收益`。

1. **是日超额的算术和，不是端点复利**。
2. **基准是函数第二个实参**，E3 传的是 `base_pool`（`is_open ∧ ¬ST ∧ volume>0 ∧ close>0 ∧ lclose>0`），
   既不是 `pool0`，也不是引擎用的 `clean`（= `base_pool ∧ mature20`、北交所置 0）。三者规模差很大。

**处置**：主标签用源版 `fwd5_sum_src`，另报端点复利版 `fwd5_compound_alt`，命名不混；
T0 的三层对象表标明基准来源；`Δgross vs R1/R2` 一律用引擎的 `clean` 基准。
40 键守卫按 T+6 ≤ 2018-12-31 判 `label_end`。

---

## §3 方向来源：`HB` 只有 7 条，本轮不依赖它

**实测**：`e6e_core.HB` = `{f: roles.worst_pooled==5 for f in FACTORS}`，只有 **7 个键**，全部 `True`。
34/35 + NEW40 的其余键没有条目。

**处置**：按 brief §2，统一 `bad_pct`，反向走真实反序 `(−s).rank(pct=True)`，**两个方向都报**。
阶段 0 量化了「真实反序」与「1 − pct」的关系（`checks/selftests_*.json`）：

* `(−s).rank(pct) + s.rank(pct) ≡ 1 + 1/n`（average 并列法），实测最大偏差 **2.220e-16**；
* 因此**单腿同序**，掩码逐位相同（实测差 0 格）；
* 但**分数值差一个 1/n 的逐日常数**（2010-2014 池中位 154 只 → 差约 0.0065，最大 1.695e-2），
  多腿 rank-mean 里这个偏移**不抵消**，会改变合成分数。这正是「不许默认 1 − pct」的原因。

---

## §4 `CONFIRMED_FEATURE_NAMES` 的位置

**声称**：brief §1.3 的语境像是 `features_daily` 的概念。
**实测**：该常量在 `comprehensive_factor_diagnosis.py:90`。内容（30 个）相符。只是位置更正。

---

## §5 「剩余 8 键」不存在于日频键集合

**声称**（proposal §附录）：「剩余 8 个日频因子清单的来源文件（481 库文档 / PROJECT_STATUS §8）」。

**实测**：
* `calc_all_daily_features` 恰好算出 **70 键** = `CONFIRMED_FEATURE_NAMES`(30) ⊎ proposal 附录 A 的 NEW40(40)，
  **无重叠、无遗漏、无余项**（`registry/keyset_counts.csv`）；
* 加 4 个自定义 spec（`reversal_skip1 / parkinson_vol / abn_turnover / cmf_change_neg`）= `U34` 34 个；
  加 `intraday_cvr_1d` = `U35` 35 个；`CVR`（NEW40）与 `intraday_cvr_1d` 是**公式别名**，故 74 个不同表达式；
* PROJECT_STATUS §8 讲的是**外部 99 篇研报因子库**（`factor_classification_v2.csv`：
  `usable_now` = 20 `yes` / 3 `yes_needs_impl` / 72 `no_minute` / 4 `review`），与日频键集合是两个宇宙。

**处置**：按 plan §2K1「不另发明清单」，`registry/external_library_index.md` 只索引来源，不实现。
`J_KTC = 32`、`J_KT = 33` 由注册表生成，与 brief §0.1 一致（`registry/keyset_counts.csv` 七项全 `True`）。

---

## §6 `wcombine_dense` 与 `combine_dense` 在等权点差 1 ULP，边界票会翻组

**实测**：`wcombine_dense(Ps, [1/3,1/3,1/3])` 算 `Σw·P / Σw`，`combine_dense(Ps,'mean')` 算 `nanmean`。
数学恒等，浮点末位差 **3.331e-16**。NaN 位**完全一致**（零权重 bypass 正确）。但恰在 `pd.qcut` 分箱边界上的票会翻组：

| 深度 | 边界翻组 | 占该配置持仓格 | net8 年化差 |
|---|---|---|---|
| `KTC_mean@25` | 104 格 | 0.2241% | −0.0083 点 |
| `KTC_mean@30` | 144 格 | 0.2597% | −0.0098 点 |

**影响**：(i) E6f §4.2 的权重单纯形在**等权点**上与同深度的无权重核有 ~0.2% 的掩码差与约 0.01 点/年的 net8 差，
这是仪器噪声不是经济效应；(ii) E6g 的 α 网格整条曲线都由 `wcombine_dense` 算，**内部一致**，
但与无权重母体比较时要带这个量级。

**处置**：**不改 E6f 的代码路径**（否则 OLD 域不能逐位复现）。锚的内容改写为其真正要测的东西——
域一致（NaN 位逐位相同）+ 分数在 1 ULP 内——两条都过；边界翻组格数与 net8 差作登记列。
与 E6f §1 的 `pd.qcut` 1 ULP 是同一类仪器事实。

---

## §7 `zprior60` 的条件数：`pandas.rolling.std` 在近常数窗上丢精度

**实测**（四段）：`z(a·F)` 与 `z(F)` 应恒等。
* **相对**差最大 **1.882e-06**，p99.99 = 3.653e-09；
* **池内格**（H2 唯一实际用到的格）绝对差最大 **2.165e-07**；
* 全网格绝对差最大 8.923e-05，只落在 6 格，且这些格 |z| 高达 2,006（全网格最大 |z| = 2,608）；
* 若再加一个相对量级 264 倍的平移，差扩大到 1.581e-03。

**机制**：近常数的 60 日历史 → `std` 极小 → z 极大，`rolling.std` 的流式更新在这里条件数很差。

**处置**：`std == 0` 已按 plan 置 NaN；近退化窗**不过滤、不设闸**，但 H2 的每个输出带
`n_z_gt100 / n_z_gt1000 / max_abs_z` 三列，解读时与该键的 `tie_frac`、`q99/MAD` 并读。

---

## §8 E6f 遗留更正：段内零仓位日（E6f_REVIEW §1.3）

见 `revisions/E6f_interior_nopos/README.md`。要点：`source_corrections_E6f.md` §5 与 `coverage.md`
的「段内 0 天」结论**错误**（用中位配置代全体），E6f_REVIEW 已指出；本轮从 E6e 逐日 `pos` 账本重算，
与 `all_candidates.csv` 已存的 `interior_nopos` 列**逐条相等（最大差 0，0 条不等）**，并把 REVIEW 的
三个代表数 **246 / 67 / 4 更正为 245 / 66 / 4**（`KT_dep(45,45)`；`CT_dep` 与 `K_gate_TC` 的 (45,45) 是 244）。

---

## §9 `e6f_c1.py` / `e6f_c2.py` / `e6f_b2_select.py` 不可 import

**实测**：三者在模块层跑 `argparse.parse_args()`，`import` 即 `SystemExit`。
**处置**：E6g 需要 `walk_holdings / profile_and_impact / shadow_account` 时把函数体复制进 `e6g_c.py`
并重新对锚（Xengine、订单恒等式 `Σ|q|/(2·turn) = 1`），**不改 E6f 文件**。记为已知取用约束，不是缺陷。

---

## §10 `e6e_core.sparse_pnl` 读 `S.den`，`e6f_core.build_segment` 只写 `S.den5`

**实测**：直接把 `e6f_core.build_segment` 造的段喂给 `e6e_core.sparse_pnl` 会 `AttributeError: 'SegX' object has no attribute 'den'`。
**处置**：E6g 在对锚前显式 `S.den = S.den5`。两者在 `H=5` 下**逐位相同**（实测四段 max|d| = 0.000e+00）。

---

## §11 `E6g_proposal.md` 的 SHA256 与 brief 声明不一致（WARN）

brief 与 plan 附录 B 都记 `79f5632d…`；实际文件是 `709fe2c1…`。原因：proposal 顶部现有一个
「勘误（2026-09-11）」块，其六条与 brief §0.1 的六条 ★ 项逐条对应，说明指纹取自**加勘误块之前**的版本。
**内容没有丢失**。记 WARN，不阻断，不改文件；两个哈希都进 `source_manifest.json` 与 `preregistration.md` §3.1。

---

## §13 **E6f 缺陷：FundamentalTL 六个字段没对齐到 `close` 的列空间就按位置取列**

**实测**：`load_all_daily_data` 里，行情字段（`close/open/vwap/volume/amount/mcap/is_open/…`）来自
K 线加载器，列集合与列序**等于** `close`；而 `load_limit_prices()` 加载的六个 FundamentalTL 字段
（`limit_up / limit_down / flag_buy / flag_sell / flag_st / industry_zx1`）是**全历史宽表**，
列集合与列序都不同：

| 段 | `close` 列数 | FundamentalTL 列数 | 列同序 | 交集 |
|---|---|---|---|---|
| 2010-2014 | 2,612 | 5,450 | 否 | 2,610 |
| 2015-2018 | 3,587 | — | 否 | — |
| 2019-2023 | 5,231 | — | 否 | — |
| 2024-2026 | 5,276 | — | 否 | — |

`e6f_c1.py:52–57` 与 `e6f_c2.py:52–53` 写的是

```python
FB = S.data['flag_buy'].values[:, cc]      # cc = S.ccols, 是【close 列空间】的位置下标
```

`cc` 的最大值 < 2,612 < 5,450，所以**不会报错**，只是静默取到了另一批股票。

**影响量化**（pool0 格上的 `flag_buy`）：

| 段 | 非缺：错列 → 对齐 | `==1`：错列 → 对齐 | 逐格一致 |
|---|---|---|---|
| 2010-2014 | 0.5529 → **1.0000** | 0.5083 → **0.9990** | 0.5079 |
| 2015-2018 | 0.6065 → **1.0000** | 0.5432 → **0.9987** | 0.5428 |
| 2019-2023 | 0.8999 → **1.0000** | 0.8593 → **0.9989** | 0.8585 |
| 2024-2026 | 0.9369 → **1.0000** | 0.9028 → **0.9988** | 0.9018 |

**结论**：`flag_buy / flag_sell` 在四段上的真实覆盖率都是 **100%**，pool0 成员 **99.9%** 可买可卖。

**受影响的 E6f 结论（只有两处，都不涉及收益引擎）**：

1. **`E6f_REPORT_part3` 的 X1「unknown 当不可成交」情景失效**。报的
   −2.49 / −4.53 / −0.97 / −0.37 与「与 `flag_buy` 覆盖率 0.534 / 0.678 / 0.824 / 0.944 严格反向」
   **量的正是这个列错位**：错列后 45% 的格是 NaN，`unknown_tradable=False` 就把这 45% 的单子全挡掉。
   而那条「覆盖率随时间上升」的趋势也是假象——随着上市家数增加，`close` 的列数
   （2,612 → 5,276）逼近 FundamentalTL 的 5,450，位置索引**碰巧越来越准**。
   正确读法：标志几乎不挡单（~0.1%），**X1 ≈ X0**。本轮块 C 重跑并给正确数。
2. **`e6f_c1` 的画像列 `tw_nobuy` / `tw_nosell` / `tw_st` 指向错误股票**，不可用。
   `flag_st` 给出第三重内部一致性证明：错列口径下 pool0 里有 **1.6%–3.7%** 的格是 ST，
   但 `pool0 ⊆ base_pool`，而 `get_base_pool` 用 `reindex_like`（**对齐的**）显式排除了
   `flag_st == 1` —— 池内按构造就不可能有 ST。对齐后实测 **0.005%–0.012%**。
   也就是说 E6f 的 `tw_st` 报的是一个构造上不可能存在的暴露。

**不受影响**：冲击 bracket（不读标志——本轮把 `profile_and_impact` 移植进 `e6g_c.py` 后与 E6f
已存的 `C_impact/bracket_<段>.npy` 对锚，11 个展示组配置四段 **max|d| = 0.000e+00**）；
引擎、DEV、成本、pool0 成员（`apply_hard_constraints` 用 `align()` 助手，`get_base_pool` 用
`reindex_like`，都对齐）；行业上限（`e6e_core:174` 与 `e6f_core:462` 都显式 `reindex`）；
影子账户的 **Xideal 与 X0**（只用 `is_open` 与价格有效性）。

**处置**：地基与 E6f 文件**不改**；`e6g_c.align_to_close()` 一律先 `reindex` 再按 `ccols` 取位置，
本轮所有标志相关量走它。`revisions/E6f_flag_alignment/` 存对照表。

---

## §12 注册表里的两条仪器事实（供 H0 / H1 / K2 解读，不是缺陷）

1. **八个 NEW40 键是离散计数/二值，池内并列占比 = 1.000**：`agreement_count_5d`、`daynight_divergence`、
   `gap_direction_consistency_5d`、`inside_bar_freq_20d`、`intraday_ret_consistency_5d`、
   `positive_day_ratio_5d`、`volume_regime_break`、`consecutive_gap_same_direction`
   （`nunique` 2–22，最大 tie 块到 404,654 格）。`info_discreteness_20d`、`days_since_high`（都在 U34）
   的并列占比也 > 0.9999。这些键上任何 k 分位否决或 rank-mean 腿，**结果由平局处置规则决定而不是由因子决定**
   → `WHOLE_TIE` / `RANDOM_TIE` 必触发，并另报原始类别的收益与持仓贡献（brief §3 已规定）。
2. **复权敏感要拆成两个独立标志，不是一个互斥三分类**（本轮反事实只把 `open/close/high/low/vwap/lclose`
   乘后复权因子，**没动** `volume` / `amount` / `turnover_rate`）：

   * **[A] 实测数值真的变（14 个）**：`cum_return_{5,10,20}d`、`recent_high_20d`、`days_since_high`、
     `distance_from_high_20d`、`info_discreteness_20d`、`ou_halflife_60d`、`overnight_return_ratio_20d`、
     `tug_of_war`、`tug_of_war_20d`、`CCV_20d`、`inside_bar_freq_20d`、`volume_momentum_divergence`。
     判据：`max|Δ| / max|x| ≥ 1e-11`（低于此是浮点末位）。
   * **[B] 依赖股数 / 成交额、本轮未测（26 个）**：全部 `volume_*` / `turnover_*` / `amount_*` / `amihud_*`，
     以及 `CMF_20d`、`conditional_turnover`、`turnover_volatility_60d`、`abn_turnover`、`stealth_score`、
     `RPV_20d`、`drawdown_volume_ratio`、`amihud_asymmetry_20d`、`gap_volume_ratio`、`mcap_rank`。
     这些键「测出恒等」**不构成证据**，一律标 `unknown_share_count_not_tested`，只披露不猜系数（brief §3）。
   * **两个标志可以同时为真（3 个）**：`CCV_20d`、`inside_bar_freq_20d`、`volume_momentum_divergence`。
   * **[C] 数值恒等（或底层键恒等）但秩被并列翻转（16 个）**：`CLV`、`CLV_20d`、`shadow_asymmetry`、
     `shadow_asymmetry_20d`、`gap_vs_sector`、`gap_trend_5d`、`overnight_ret_trend`、`cum_intraday_ret_5d`、
     `intraday_ret`、`overnight_ret`、`max_abs_return_10d`、`gap_survival_ratio`、`conditional_turnover`，
     以及三个单调变换键 `gap_rank_in_sector`、`gap_percentile_60d`、`overnight_ret_cross_sectional_rank`。
     后三者是 gap / `overnight_ret` 的**单调变换**，底层键实测不变，数值差只来自「gap 恰为 0」这类
     大并列块被 1e-16 噪声重排（`gap_rank_in_sector` 差 0.073 ≈ 市场上 gap 为 0 的比例）。
     **这不是复权敏感，是并列敏感** → `WHOLE_TIE` 必须处理。
   * **四个自定义 spec 不在 `calc_all_daily_features` 里，本轮未实测**，按函数体判：
     `reversal_skip1`（`close.shift(1)/close.shift(w+1)`）属 [A]；`parkinson_vol`（同日 `log(high/low)`）恒等；
     `abn_turnover`、`cmf_change_neg` 属 [B]。登记为「读公式判定、未实测」。

   brief §0.1 关于 `lclose` 的勘误**实测成立**：`overnight_ret`、`positive_day_ratio_5d`、`gap_zscore_20d`、
   `gap_abs_zscore_20d`、`gap_direction_consistency_5d` 等 gap 族在复权下数值不变。
   逐键三列（`price_adj_measured_change` / `volume_dependent_untested` / `tie_driven_rank_shift`）
   见 `registry/key_registry.csv`。
