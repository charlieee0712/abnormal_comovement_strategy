# E6k REPORT supplement_1 —— 同时带统计量的定义与同单位读数；诊断 v2 的事后标注（事后口径）

用途：
- 依据：VERIFY brief §6（"统计量是别的量"分支）与 §C-9。
- 口径：本文是事后口径，在十二份 REPORT 冻结（`E6k_MIRROR.md5` 第一 / 二节）之后由复核触发计算，不替代任何登记结果。`results/full/bootstrap/simultaneous_band_q95.csv` 与 REPORT 均不改；随机与 bootstrap 不重跑（同一路径、同一种子）。
- 内容：只给数，不给建议；对外数字须用户过目。
- 表头格式同 REPORT，query_id 前缀 `S1-Q`。

## §0 事后口径与定义

### 0.1 登记的同时带是什么量（VC12；从 `e6k_bootstrap.py` 源码转录，V 程序独立转录一致）

- **统计量**：M_b = max_j |(FULL*_bj − FULL_j) / SE_j|，是标准化 max-t。
  - FULL*_bj：第 b 次 bootstrap draw 的四段 n 加权年化百分点，Σ_s num*_s / Σ_s den*_s × 252 × 100。重抽方法是段内分层 stationary，几何块长均值 L ∈ {20, 60}，段内环绕、不跨段接缝。
  - FULL_j：全样本点估。
  - SE_j：2,000 个 draw 的 sd（ddof 1）。
  - 集合：固定比较集合中 SE > 0 且没有无支持 draw 的比较。primary144 为 144 个；all 为 112,926 个中的 111,766 个。
- **单位**：`q95_maxabs_centered` 以 SE 为单位（SE 的倍数），不是年化百分点。
  - 数值：primary144 L20 3.379 / L60 3.435；all L20 4.810 / L60 4.780。
  - 逐对象的同时带半宽 = q95 · SE_j，单位为年化百分点。
- **读法缺口**：决策端 D17 拿 q95（3.379）与逐对象 95% CI 半宽（最大 .298）直接比较，两者单位不同。本文 §1 给出同单位（年化百分点）的两种读数：
  - S1-Q01 / S1-Q02：未标准化 max-abs 的分位；
  - S1-Q03：登记统计量折成逐对象半宽。
- 计算脚本 `e6k_supp1_band.py`（本轮代码，与 V 分进程、分目录），回执 `supp1_band`（2026-09-30 03:14:13，47 时间）。产物在 `results/full/bootstrap/supplement_1/`（新目录）。

### 0.2 事后标注（C-9；VERIFY E06）

两个诊断的 v2 都是**事后**补做的——读了 part2 首版、发现 v1 退化之后才做：

- 衰减场景：v1 `decay_scenarios.csv` 回执 11:01:01 → v2 `decay_scenarios_v2.csv` 回执 12:13:35 → `report_part2` 回执 12:14:02。
- HG 跨段连续状态：v1 回执 02:42:27 / 11:04:35 → v2 `hg_continuous_v2_*` 回执 12:27:32 → `report_mechanisms` 回执 12:29:48。

以下三处都写了"v1 退化、v2 替代、v1 保留不作读数"，但没有"事后"字样，本节补上这一标注：

- part2 衰减场景表注（`E6K-P2-DECAY` 之后）；
- mechanisms `E6K-MX-HGCONT` 表头与表注；
- limit_register L15。

两者都是诊断，不进入任何登记账户或政策判定。

## §1 同单位读数（年化百分点；事后口径）

> 表头：主体=同时带统计量的未标准化版本 U_b = max_j \|FULL*_bj − FULL_j\|（同一 bootstrap 路径）｜算子=CP 比较（子 − 同 H 原父）｜分母=四段有效配对日（FULL = n 加权）｜基准=全样本点估 FULL_j｜子集=primary144（CP）/ all（112,926 中 SE > 0 且无无支持 draw 的 111,766）｜单位=年化百分点｜日期=2010-01-04..2026-03-27（四段；2026 partial）｜H=各对象自身 H｜成本模型=源 8bp｜支持=原生（FALLBACK）｜资本视图=实际源 DEV｜exposure=事后口径（不替代登记结果）｜query_id=S1-Q01

| L | set | q90 | q95 | q99 | draws | n_comparisons |
|---|---|---|---|---|---|---|
| 20 | primary144 | 0.3735 | 0.4059 | 0.4858 | 2000 | 144 |
| 20 | all | 1.545 | 1.688 | 2.009 | 2000 | 111766 |
| 60 | primary144 | 0.3697 | 0.4026 | 0.4675 | 2000 | 144 |
| 60 | all | 1.549 | 1.696 | 1.976 | 2000 | 111766 |

> 表头：主体=primary144 中点估 FULL_j 超过 S1-Q01 各分位（或低于其负值）的对象数｜算子=CP 比较｜分母=四段有效配对日（FULL = n 加权）｜基准=S1-Q01 同 L 的 primary144 分位｜子集=primary144（144）｜单位=计数 / 年化百分点｜日期=2010-01-04..2026-03-27（四段；2026 partial）｜H=5｜成本模型=源 8bp｜支持=原生（FALLBACK）｜资本视图=实际源 DEV｜exposure=事后口径（不设门，只给数）｜query_id=S1-Q02

| L | quantile | value | n_objects | n_FULL_above | n_FULL_below_neg |
|---|---|---|---|---|---|
| 20 | q90 | 0.3735 | 144 | 19 | 0 |
| 20 | q95 | 0.4059 | 144 | 11 | 0 |
| 20 | q99 | 0.4858 | 144 | 4 | 0 |
| 60 | q90 | 0.3697 | 144 | 20 | 0 |
| 60 | q95 | 0.4026 | 144 | 11 | 0 |
| 60 | q99 | 0.4675 | 144 | 4 | 0 |

> 表头：主体=登记同时带折成同单位：逐对象半宽 q95（登记值，SE 单位）× SE_j，与逐对象 95% CI 半宽 ½(q97.5 − q2.5) 并列｜算子=CP 比较｜分母=四段有效配对日（FULL = n 加权）｜基准=全样本点估 FULL_j｜子集=primary144（144）｜单位=年化百分点（q95 列为 SE 倍数）｜日期=2010-01-04..2026-03-27（四段；2026 partial）｜H=5｜成本模型=源 8bp｜支持=原生（FALLBACK）｜资本视图=实际源 DEV｜exposure=事后口径（不替代登记结果）｜query_id=S1-Q03

| L | set | q95_registered_se_units | n_objects | band_halfwidth_median | band_halfwidth_min | band_halfwidth_max | ci95_halfwidth_median | ci95_halfwidth_max | se_median | se_max |
|---|---|---|---|---|---|---|---|---|---|---|
| 20 | primary144 | 3.379 | 144 | 0.3603 | 0.07207 | 0.5239 | 0.2087 | 0.298 | 0.1066 | 0.155 |
| 60 | primary144 | 3.435 | 144 | 0.3474 | 0.07511 | 0.5547 | 0.196 | 0.3104 | 0.1011 | 0.1615 |

读法限制（只说明口径，不作判读）：

- S1-Q01 的 U_b 未标准化，由 SE 大的对象主导；登记的 M_b 按各对象 SE 标准化。两者回答的是不同问题，本文不在两者之间择一。
- "all"集合含 CP / CN / CC1 / CB / CH 五种前缀的比较，SE 尺度不同的比较放在同一个未标准化 max 里，因此 all 的分位高于 primary144。
- plan 不以显著性过门：同时带只作读法，不进入政策判定或候选清单。
