# E6j REPORT R0 —— Stage 0 仪器：源锚、6 / 8bp、R1 身份、测量合同、种子与守卫

用途：Stage 0 六项锚的结果与证据链（brief v1.2 §2；plan §3.2 / §10.1）。**本文件不含任何新收益读数**：出现的净值只来自既有生产母体与 E6i 研究母体的账本，用于钉住此后一切"子 − 母"的母。执行端，2026-09-27（47 时间）；HEAD `1113038`；结果目录 `results/20260927_0038_E6j_k_two_dimension_pilot/`。

读法：每张表前一行"表头"给出 主体 / 算子 / 分母 / 基准 / 子集 / 单位 / 日期 / H / 成本模型 / 支持 / 资本视图 / exposure / query_id；正文句尾〔query_id〕指向同一查询。

## 0. 结论

- Stage 0 六项：全部 PASS；锚检查合计 904 项，PASS 794、INFO 108、DIFFERS 2、FAIL 0〔R0-Q00〕。

> 表头：主体=Stage 0 六项｜算子=任务回执｜分母=回执｜基准=—｜子集=FAILED 须由同名 _rerun 成功覆盖｜单位=状态｜日期=2010-01-04..2026-03-27（四段）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=—｜query_id=R0-Q00


| item | receipts | status | ok |
|---|---|---|---|
| 1_prod_path_anchor | stage0_anchor1_prod_path_rerun | SUCCEEDED | True |
| 2_parent_identity | stage0_anchor2_parent_identity、stage0_anchor2_parent_identity_rerun | SUCCEEDED、SUCCEEDED | True |
| 3_slot_identity | stage0_anchor3_slot_identity | SUCCEEDED | True |
| 4_features_synthetic_real | stage0_item4_features | SUCCEEDED | True |
| 5_seed_replay_guard_a0 | stage0_item5_replay、stage0_item5_guard | SUCCEEDED、SUCCEEDED | True |


- **R1 ≡ A4b_CVRv5 是精确别名**（掩码逐格、权重 / 持仓 / 8bp 日账本浮点求和序内相同）〔R0-Q05〕；brief W03 的"同源不同路径"暂判来自两处未匹配比较：展示口径（有持仓日平均 vs 全日平均）与 8bp 近似换算〔R0-Q04、R0-Q06〕。

- **P 主母体上 S / M / C1 三臂（α .125 / .25 / .5 × H 3 / 5 / 10 / 20）= E6i R1 SLOT 账户的精确别名**，四段均已在 E6i 暴露；K_rarpre / K_samt20 两列对象同理；SM 与 AMT4 为新组合〔R0-Q10、R0-Q18〕。试点在主母体上的新信息只来自 SM；其余五形态是同成员同方向的转移证据。

- 输入差异 17 条只登记不改源（`source_resolution.md` §2）；其中 B 包计数按 plan §5.10 现算为每段 13,398（brief 写 13,230）〔R0-Q17〕。

## 1. 起点、输入与环境

> 表头：主体=决策端输入与执行端合同文件（结果目录副本）｜算子=sha256｜分母=—｜基准=—｜子集=—｜单位=十六进制前缀｜日期=2010-01-04..2026-03-27（四段）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=—｜query_id=R0-Q01


| file | sha256_prefix |
|---|---|
| brief_copy.md | b80be105 |
| PLAN_COPY.md | 6dd59dbf |
| E6j_proposal_copy.md | 2bc4b346 |
| E6i_RULING_copy.md | 9f28b132 |
| E6j_RULING_copy.md | cb3b8a5f |
| E6i_REVIEW_copy.md | 6441389e |
| E6i_REVIEW_supplement_1_copy.md | c065a15b |
| E6i_REVIEW_supplement_2_copy.md | 785ef7db |
| REVIEW_protocol_copy.md | 0b15019e |
| 00_协议_copy.md | f685e538 |
| source_resolution.md | c6fb578f |
| engine_contract.md | 6a26bb6d |


环境：Python 3.10.13 / NumPy 1.26.1 / pandas 2.2.3；随机：blake2b-128(canonical_json(key)) -> SeedSequence。

## 2. 生产路径锚（第 1 项）：α = 0 逐位重现 E5a；6 / 8bp 双锚

> 表头：主体=E5a v2 交付文件｜算子=生产路径 α = 0（e6j_prod 逐字复制生产脚本）重算后逐字节比对｜分母=文件字节｜基准=—｜子集=六个 pool2 + pool1 + summary / _delivery_stats / check｜单位=sha256 相同与否｜日期=2010-01-04..2026-03-27（四段）｜H=5｜成本模型=6bp（E5a 原口径）｜支持=native｜资本视图=NATIVE｜exposure=E5a 已交付｜query_id=R0-Q02


| check_id | object | status | note |
|---|---|---|---|
| A1-P1 | pool2_A4b_pure.csv | PASS | rows=279649 days=3824 2010-02-12..2026-03-27 wmax=0.01 |
| A1-P1 | pool2_Mmean_v2_pure.csv | PASS | rows=557683 days=3824 2010-02-12..2026-03-27 wmax=0.01 |
| A1-P1 | pool2_Munion_v2_pure.csv | PASS | rows=196546 days=3824 2010-02-12..2026-03-27 wmax=0.01 |
| A1-P1 | pool2_A4b_cvrveto.csv | PASS | rows=237213 days=3824 2010-02-12..2026-03-27 wmax=0.01 |
| A1-P1 | pool2_Mmean_v2_cvrveto.csv | PASS | rows=485751 days=3824 2010-02-12..2026-03-27 wmax=0.01 |
| A1-P1 | pool2_Munion_v2_cvrveto.csv | PASS | rows=178572 days=3824 2010-02-12..2026-03-27 wmax=0.01 |
| A1-P0 | pool1_I11_screening.csv | PASS | md5=6006780eb791fe6a7f66e3829cb23763 (源 POOL1_MD5 6006780eb791fe6a7f66e3829cb23763) rows=1122054 |
| A1-S1 | summary.csv | PASS |  |
| A1-S1 | _delivery_stats.csv | PASS |  |
| A1-S1 | check.csv | PASS |  |


> 表头：主体=六生产形态母体｜算子=生产路径 α = 0；cost_bp_bilateral = 8 重算｜分母=段内非缺失净值日 n｜基准=clean 全市场等权（主基准）｜子集=各段全部形成日｜单位=net / gross 年化百分点；turn 年化倍；avg_nh 只；avg_pos 资金占比（有持仓日平均）｜日期=2010-01-04..2026-03-27（四段）｜H=5｜成本模型=8bp 线性（政策口径）｜支持=native｜资本视图=NATIVE｜exposure=同形态 6bp 已在 E5a 交付；8bp 为本锚重算｜query_id=R0-Q03


| period | cfg | net_ann | net_nw | gross_ann | turn | avg_nh | avg_pos | n |
|---|---|---|---|---|---|---|---|---|
| 2010-2014 | A4b | 2.199 | 2.168 | 3.422 | 15.06 | 39.24 | 0.3909 | 1193 |
| 2010-2014 | M_mean3_v2 | 3.008 | 1.935 | 5.162 | 26.5 | 78.12 | 0.7444 | 1193 |
| 2010-2014 | M_union3_v2 | 2.417 | 3.189 | 3.319 | 11.1 | 27.8 | 0.2777 | 1193 |
| 2010-2014 | A4b_CVRv5 | 2.799 | 3.181 | 3.837 | 12.78 | 32.65 | 0.3256 | 1193 |
| 2010-2014 | M_mean3_v2_CVRv5 | 4.047 | 2.855 | 5.981 | 23.8 | 66.9 | 0.6506 | 1193 |
| 2010-2014 | M_union3_v2_CVRv5 | 2.302 | 3.288 | 3.118 | 10.05 | 24.81 | 0.2479 | 1193 |
| 2015-2018 | A4b | 4.564 | 2.157 | 6.488 | 23.59 | 64.89 | 0.6396 | 956 |
| 2015-2018 | M_mean3_v2 | 6.362 | 2.084 | 9.047 | 32.91 | 129.3 | 0.9584 | 956 |
| 2015-2018 | M_union3_v2 | 6.622 | 4.098 | 8.06 | 17.62 | 45.93 | 0.4572 | 956 |
| 2015-2018 | A4b_CVRv5 | 6.575 | 3.55 | 8.23 | 20.28 | 54.14 | 0.5369 | 956 |
| 2015-2018 | M_mean3_v2_CVRv5 | 9.39 | 3.113 | 12.08 | 32.92 | 110.6 | 0.9281 | 956 |
| 2015-2018 | M_union3_v2_CVRv5 | 6.647 | 4.393 | 7.949 | 15.95 | 40.79 | 0.4064 | 956 |
| 2019-2023 | A4b | 6.958 | 3.026 | 9.393 | 29.97 | 90.52 | 0.8031 | 1195 |
| 2019-2023 | M_mean3_v2 | 4.873 | 2.254 | 7.61 | 33.68 | 180.6 | 0.9562 | 1195 |
| 2019-2023 | M_union3_v2 | 5 | 2.866 | 6.984 | 24.42 | 65.05 | 0.6256 | 1195 |
| 2019-2023 | A4b_CVRv5 | 7.874 | 3.689 | 10.1 | 27.37 | 77.45 | 0.7187 | 1195 |
| 2019-2023 | M_mean3_v2_CVRv5 | 6.382 | 2.899 | 9.182 | 34.45 | 158.2 | 0.9476 | 1195 |
| 2019-2023 | M_union3_v2_CVRv5 | 5.021 | 3.044 | 6.869 | 22.74 | 59.38 | 0.5745 | 1195 |
| 2024-2026 | A4b | 8.255 | 1.564 | 10.94 | 32.35 | 126.6 | 0.9123 | 520 |
| 2024-2026 | M_mean3_v2 | 5.67 | 1.197 | 8.31 | 31.83 | 252.7 | 0.9577 | 520 |
| 2024-2026 | M_union3_v2 | 6.701 | 1.463 | 9.109 | 29.03 | 84.54 | 0.7718 | 520 |
| 2024-2026 | A4b_CVRv5 | 9.665 | 1.831 | 12.32 | 32.06 | 109 | 0.8831 | 520 |
| 2024-2026 | M_mean3_v2_CVRv5 | 6.741 | 1.404 | 9.443 | 32.59 | 224.6 | 0.9526 | 520 |
| 2024-2026 | M_union3_v2_CVRv5 | 7.257 | 1.64 | 9.564 | 27.82 | 78.96 | 0.7313 | 520 |


> 表头：主体=A4b_CVRv5 母体｜算子=年化 8bp：精确式 vs brief 近似式 vs brief W02 两位小数｜分母=L = 账本行数；n = 非缺失净值日｜基准=—｜子集=—｜单位=年化百分点｜日期=2010-01-04..2026-03-27（四段）｜H=5｜成本模型=8bp / 6bp｜支持=native｜资本视图=NATIVE｜exposure=—｜query_id=R0-Q04


| check_id | object | metric | expected | got | abs_diff | status |
|---|---|---|---|---|---|---|
| A1-C3 | 2010-2014\|A4b_CVRv5 | net8_ann vs net6_ann−0.02·turn·L/n（缺失日换手=0） | 2.7987671463889088 | 2.7987671463889088 | 0 | PASS |
| A1-C3a | 2010-2014\|A4b_CVRv5 | brief 近似式残差 net8_ann−(net6_ann−0.02·turn) | 2.8028380400371704 | 2.7987671463889088 | -0.004071 | INFO |
| A1-C4 | 2010-2014\|A4b_CVRv5 | net8_ann vs brief W02 换算值（两位小数、近似式） | 2.8 | 2.7987671463889088 | 0.001233 | PASS |
| A1-C3 | 2015-2018\|A4b_CVRv5 | net8_ann vs net6_ann−0.02·turn·L/n（缺失日换手=0） | 6.575448445384895 | 6.575448445384893 | 1.776e-15 | PASS |
| A1-C3a | 2015-2018\|A4b_CVRv5 | brief 近似式残差 net8_ann−(net6_ann−0.02·turn) | 6.583510546516918 | 6.575448445384893 | -0.008062 | INFO |
| A1-C4 | 2015-2018\|A4b_CVRv5 | net8_ann vs brief W02 换算值（两位小数、近似式） | 6.58 | 6.575448445384893 | 0.004552 | PASS |
| A1-C3 | 2019-2023\|A4b_CVRv5 | net8_ann vs net6_ann−0.02·turn·L/n（缺失日换手=0） | 7.8738805497106785 | 7.873880549710679 | 8.882e-16 | PASS |
| A1-C3a | 2019-2023\|A4b_CVRv5 | brief 近似式残差 net8_ann−(net6_ann−0.02·turn) | 7.88258322620719 | 7.873880549710679 | -0.008703 | INFO |
| A1-C4 | 2019-2023\|A4b_CVRv5 | net8_ann vs brief W02 换算值（两位小数、近似式） | 7.88 | 7.873880549710679 | 0.006119 | DIFFERS |
| A1-C3 | 2024-2026\|A4b_CVRv5 | net8_ann vs net6_ann−0.02·turn·L/n（缺失日换手=0） | 9.664660536543353 | 9.664660536543353 | 0 | PASS |
| A1-C3a | 2024-2026\|A4b_CVRv5 | brief 近似式残差 net8_ann−(net6_ann−0.02·turn) | 9.688089759890863 | 9.664660536543353 | -0.02343 | INFO |
| A1-C4 | 2024-2026\|A4b_CVRv5 | net8_ann vs brief W02 换算值（两位小数、近似式） | 9.69 | 9.664660536543353 | 0.02534 | DIFFERS |


读法：逐日 net8 − net6 = −2e−4 × 换手逐位成立；年化精确式 net8 = net6 − 0.02 × turn × L / n（缺失日换手为 0），brief 的"≈ net6 − 0.02 × turn"少了 L / n 因子，在近段差到 0.025〔R0-Q04〕。首跑回执 FAILED（30 项全是检查定义错，见 lessons_delta），`--rerun` 覆盖。

## 3. R1 vs A4b_CVRv5 四层身份（第 2 项）

> 表头：主体=R1（E6i 研究）与 A4b_CVRv5（生产 v2）｜算子=掩码 / DEV 目标权重 / 五日持仓 / 8bp 日账本 四层比对｜分母=逐格 / 逐日｜基准=—｜子集=四段｜单位=最大绝对差（小数）｜日期=2010-01-04..2026-03-27（四段）｜H=5｜成本模型=8bp｜支持=native｜资本视图=NATIVE｜exposure=R1 四段已在 E6i 暴露｜query_id=R0-Q05


| object_a | object_b | classification | alias_of | L1_mask_exact | L2_max_abs | L3_max_abs | L4_max_abs |
|---|---|---|---|---|---|---|---|
| R1 (E6i research: KT_dep(50,50)\|C:k5) | A4b_CVRv5 (production v2) | exact_alias | A4b_CVRv5 | True | 3.469e-18 | 3.469e-18 | 2.22e-16 |


根目录 `parent_identity_map.csv`（首跑）L4_max_abs = 1.0 是汇总伪值（布尔检查被计成 1.0），以 `stage0/anchor2_rerun/parent_identity_map_rerun.csv` 为准〔R0-Q05〕。

> 表头：主体=同一掩码 / 账本｜算子=两种展示口径｜分母=E5a：有持仓日；E6i：全部日｜基准=—｜子集=—｜单位=只 / 资金占比｜日期=2010-01-04..2026-03-27（四段）｜H=5｜成本模型=—｜支持=native｜资本视图=NATIVE（目标权重和 vs 实际持仓和）｜exposure=—｜query_id=R0-Q06


| segment | E5a_avg_nh | E6i_parent_n_mean | E5a_avg_pos | E6i_pos_mean | days | days_nh_pos |
|---|---|---|---|---|---|---|
| 2010-2014 | 32.65 | 31.86 | 0.3256 | 0.3166 | 1212 | 1183 |
| 2015-2018 | 54.14 | 52.53 | 0.5369 | 0.5188 | 975 | 946 |
| 2019-2023 | 77.45 | 75.6 | 0.7187 | 0.6989 | 1214 | 1185 |
| 2024-2026 | 109 | 103.2 | 0.8831 | 0.8297 | 539 | 510 |


> 表头：主体=E6i 研究母体 R1 / R2 / A06 / A08｜算子=E6j 调用 E6i 引擎重算 vs E6i 已存母体日账本（任一 H5 子账户 net8 − dnet8）｜分母=共同有限日｜基准=clean 全市场等权｜子集=—｜单位=年化百分点 / 只 / 小数｜日期=2010-01-04..2026-03-27（四段）｜H=5｜成本模型=8bp｜支持=native｜资本视图=NATIVE｜exposure=E6i 已暴露｜query_id=R0-Q07


| segment | mother | net8_ann_recomputed | E6i_parent_net8_ann | parent_n_mean | E6i_parent_n_mean | max_abs_daily |
|---|---|---|---|---|---|---|
| 2010-2014 | R1 | 2.799 | 2.799 | 31.86 | 31.86 | 5.421e-20 |
| 2010-2014 | R2 | 3.947 | 3.947 | 35.65 | 35.65 | 5.421e-20 |
| 2010-2014 | A06 | 4.591 | 4.591 | 34.46 | 34.46 | 2.711e-20 |
| 2010-2014 | A08 | 3.376 | 3.376 | 35.69 | 35.69 | 2.168e-19 |
| 2015-2018 | R1 | 6.575 | 6.575 | 52.53 | 52.53 | 2.711e-20 |
| 2015-2018 | R2 | 8.174 | 8.174 | 58.61 | 58.61 | 5.421e-20 |
| 2015-2018 | A06 | 9.813 | 9.813 | 56.61 | 56.61 | 2.711e-20 |
| 2015-2018 | A08 | 9.239 | 9.239 | 59.09 | 59.09 | 4.337e-19 |
| 2019-2023 | R1 | 7.874 | 7.874 | 75.6 | 75.6 | 4.066e-20 |
| 2019-2023 | R2 | 8.776 | 8.776 | 85.2 | 85.2 | 5.421e-20 |
| 2019-2023 | A06 | 8.694 | 8.694 | 81.02 | 81.02 | 5.421e-20 |
| 2019-2023 | A08 | 8.997 | 8.997 | 86.59 | 86.59 | 4.337e-19 |
| 2024-2026 | R1 | 9.665 | 9.665 | 103.2 | 103.2 | 2.711e-20 |
| 2024-2026 | R2 | 8.683 | 8.683 | 116.5 | 116.5 | 2.168e-19 |
| 2024-2026 | A06 | 8.597 | 8.597 | 110.1 | 110.1 | 5.421e-20 |
| 2024-2026 | A08 | 9.042 | 9.042 | 120.2 | 120.2 | 8.674e-19 |


## 4. SLOT 恒等与无经济新增反例（第 3 项）

> 表头：主体=六形态 × 四段｜算子=T1 α = 0；T2 MA1 ≡ K0；T3 FALLBACK ≠ REPLACE；T4 复制旧残差；T5 置缺失不重估 + TRANSPORT；T6 SRC vs E6i SLOT；T7 成员缓存｜分母=检查项｜基准=—｜子集=—｜单位=项数｜日期=2010-01-04..2026-03-27（四段）｜H=—｜成本模型=—｜支持=native｜资本视图=—｜exposure=只算掩码 / 分数，不算收益｜query_id=R0-Q08


| test | status | n |
|---|---|---|
| T1 | PASS | 52 |
| T2 | PASS | 56 |
| T3 | INFO | 12 |
| T3 | PASS | 2 |
| T4 | PASS | 100 |
| T5 | INFO | 24 |
| T5 | PASS | 28 |
| T6 | PASS | 24 |
| T7 | PASS | 32 |


> 表头：主体=六形态｜算子=复制旧残差、稳定哈希置 5% 格缺失、不重估；SRC 秩坐标 α .25｜分母=掩码格｜基准=—｜子集=各段全部形成日｜单位=变化格数｜日期=2010-01-04..2026-03-27（四段）｜H=—｜成本模型=—｜支持=native（NEW 有效域缩小）｜资本视图=—｜exposure=诊断，无经济新增｜query_id=R0-Q09


| segment | form | mask_cells_changed |
|---|---|---|
| 2010-2014 | A4b | 4 |
| 2010-2014 | M_mean3_v2 | 316 |
| 2010-2014 | M_union3_v2 | 0 |
| 2010-2014 | A4b_CVRv5 | 4 |
| 2010-2014 | M_mean3_v2_CVRv5 | 255 |
| 2010-2014 | M_union3_v2_CVRv5 | 0 |
| 2015-2018 | A4b | 6 |
| 2015-2018 | M_mean3_v2 | 282 |
| 2015-2018 | M_union3_v2 | 0 |
| 2015-2018 | A4b_CVRv5 | 3 |
| 2015-2018 | M_mean3_v2_CVRv5 | 236 |
| 2015-2018 | M_union3_v2_CVRv5 | 0 |
| 2019-2023 | A4b | 2 |
| 2019-2023 | M_mean3_v2 | 362 |
| 2019-2023 | M_union3_v2 | 0 |
| 2019-2023 | A4b_CVRv5 | 2 |
| 2019-2023 | M_mean3_v2_CVRv5 | 296 |
| 2019-2023 | M_union3_v2_CVRv5 | 0 |
| 2024-2026 | A4b | 6 |
| 2024-2026 | M_mean3_v2 | 164 |
| 2024-2026 | M_union3_v2 | 1 |
| 2024-2026 | A4b_CVRv5 | 5 |
| 2024-2026 | M_mean3_v2_CVRv5 | 135 |
| 2024-2026 | M_union3_v2_CVRv5 | 0 |


读法：纯秩坐标移动即可改变掩码，Mmean 两形态最敏感（均值合成对坐标连续敏感），A4b / Munion（切半阈值）几乎不动；TRANSPORT 在同输入下逐值回到 q0〔R0-Q09〕。

> 表头：主体=A4b_CVRv5（= R1）｜算子=生产坐标 SLOT vs E6i Mother(R1).slot K FALLBACK｜分母=掩码格｜基准=—｜子集=推导两段；其余五形态 SPEC_only｜单位=不同格数｜日期=2010-01-04..2026-03-27（四段）｜H=—｜成本模型=—｜支持=native｜资本视图=—｜exposure=E6i 已暴露｜query_id=R0-Q10


| segment | form | arm | member | direction | alpha | mask_cells_differ | verdict |
|---|---|---|---|---|---|---|---|
| 2010-2014 | A4b_CVRv5 | S | K_rar20 | low_bad | 0.125 | 0 | identical |
| 2010-2014 | A4b_CVRv5 | S | K_rar20 | low_bad | 0.25 | 0 | identical |
| 2010-2014 | A4b_CVRv5 | S | K_rar20 | low_bad | 0.5 | 0 | identical |
| 2010-2014 | A4b_CVRv5 | M | K_slope20 | low_bad | 0.125 | 0 | identical |
| 2010-2014 | A4b_CVRv5 | M | K_slope20 | low_bad | 0.25 | 0 | identical |
| 2010-2014 | A4b_CVRv5 | M | K_slope20 | low_bad | 0.5 | 0 | identical |
| 2010-2014 | A4b_CVRv5 | C1 | K_MA3_E6F | high_bad | 0.125 | 0 | identical |
| 2010-2014 | A4b_CVRv5 | C1 | K_MA3_E6F | high_bad | 0.25 | 0 | identical |
| 2010-2014 | A4b_CVRv5 | C1 | K_MA3_E6F | high_bad | 0.5 | 0 | identical |
| 2015-2018 | A4b_CVRv5 | S | K_rar20 | low_bad | 0.125 | 0 | identical |
| 2015-2018 | A4b_CVRv5 | S | K_rar20 | low_bad | 0.25 | 0 | identical |
| 2015-2018 | A4b_CVRv5 | S | K_rar20 | low_bad | 0.5 | 0 | identical |
| 2015-2018 | A4b_CVRv5 | M | K_slope20 | low_bad | 0.125 | 0 | identical |
| 2015-2018 | A4b_CVRv5 | M | K_slope20 | low_bad | 0.25 | 0 | identical |
| 2015-2018 | A4b_CVRv5 | M | K_slope20 | low_bad | 0.5 | 0 | identical |
| 2015-2018 | A4b_CVRv5 | C1 | K_MA3_E6F | high_bad | 0.125 | 0 | identical |
| 2015-2018 | A4b_CVRv5 | C1 | K_MA3_E6F | high_bad | 0.25 | 0 | identical |
| 2015-2018 | A4b_CVRv5 | C1 | K_MA3_E6F | high_bad | 0.5 | 0 | identical |
| ALL | A4b | S/M/SM/C1 |  |  |  |  | SPEC_only：本轮生产 SLOT 即 SRC；恒等锚 T1/T2/T4/T5 |
| ALL | M_mean3_v2 | S/M/SM/C1 |  |  |  |  | SPEC_only：本轮生产 SLOT 即 SRC；恒等锚 T1/T2/T4/T5 |
| ALL | M_union3_v2 | S/M/SM/C1 |  |  |  |  | SPEC_only：本轮生产 SLOT 即 SRC；恒等锚 T1/T2/T4/T5 |
| ALL | M_mean3_v2_CVRv5 | S/M/SM/C1 |  |  |  |  | SPEC_only：本轮生产 SLOT 即 SRC；恒等锚 T1/T2/T4/T5 |
| ALL | M_union3_v2_CVRv5 | S/M/SM/C1 |  |  |  |  | SPEC_only：本轮生产 SLOT 即 SRC；恒等锚 T1/T2/T4/T5 |


## 5. 新测量合同（第 4 项）：合成检验与真实字段检验分开

> 表头：主体=玩具网格（稳定哈希种子）｜算子=代数 / 因果 / 退化状态｜分母=检查项｜基准=—｜子集=—｜单位=—｜日期=2010-01-04..2026-03-27（四段）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不碰行情｜query_id=R0-Q11


| test | what | status | detail |
|---|---|---|---|
| F00 | 成员数（B1 7 + B2 32 + B3A 16 + B3B 6 + B3C 2 + B4 12 + B5 32 + B6 3 = 110 个 J 原值） | PASS | 110 |
| F01 | 后缀扰动（t0 之后全部输入 / 触发 / pool0 改写）→ 所有 J 原值在 ≤ t0 逐位不变 | PASS |  |
| F01b | 同一扰动确实改变了 t0 之后的值（扰动有效，反"空检验"） | PASS | 110/110 |
| F02 | r_cc = r_on + r_id（有符号；浮点） | PASS | 3.09e-16 |
| F03 | CC：n_up + n_down + n_zero = n_all（逐格） | PASS |  |
| F03 | ID：n_up + n_down + n_zero = n_all（逐格） | PASS |  |
| F03b | 频率加权三组贡献之和 = 全体响应均值（相对误差） | PASS | 5.16e-16 |
| F04 | J_B5_REV_CC_W20_LT：常数比例过程 ≡ 1（有效格 8650） | PASS | 7.86e-14 |
| F04 | J_B5_REV5_CC_W20_LT：常数比例过程 ≡ 1（有效格 8650） | PASS | 1.15e-14 |
| F04 | J_B5_REV_CC_W60_SE：常数比例过程 ≡ 1（有效格 7828） | PASS | 7.85e-14 |
| F04 | J_B5_REV5_ID_W20_SE：常数比例过程 ≡ 1（有效格 8745） | PASS | 1.04e-14 |
| F05 | R_ev(m=0) 逐位 = 原始 R_ev 公式 | PASS |  |
| F06 | z 无变异 → β NA、码 2 | PASS |  |
| F06 | y 常数 → β = 0 有效、ρ NA、码 3 | PASS |  |
| F06 | 正常列 → β 有效、码 0 | PASS |  |
| F06 | 窗内不足 10 对 → 码 1 | PASS |  |
| F07 | Q_1 = MR（CC W3，相对误差） | PASS | 1.69e-13 |
| F07 | Q_1 = MR（ID W3，相对误差） | PASS | 3.49e-13 |
| F07 | β = ρ · sd(y)/sd(x)（CC） | PASS | 5.06e-16 |
| F07 | β = ρ · sd(y)/sd(x)（ID） | PASS | 5.57e-16 |
| F07 | x 全 0 → P = 0 → COV/P 全 NA | PASS |  |
| F08 | 留一可靠性 r 与 β 对暴力 polyfit（300 窗） | PASS | max\|Δr\|=4.44e-14 max relΔβ=3.35e-12 |
| F09 | B4 侧别 ROS / MR 对暴力（599 窗×侧） | PASS | 5.21e-15 |
| F10 | spell_entry 行号 = 最近连续段首日（含延长；段外保持上一段） | PASS | [-1, 1, 1, 1, 4, 4, 4, 4, 4, 9] |
| F11 | t1 新增触发 → t1 之前事件成员逐位不变 | PASS |  |
| F12 | 基线冻结在 [τ−W, τ−1]：事件内放大 x 不改 rarpre 分母（1252 格） | PASS |  |


> 表头：主体=E6i 同款预热网格（真实字段）｜算子=恒等核对｜分母=有效格｜基准=—｜子集=四段｜单位=最大相对 / 绝对误差｜日期=2010-01-04..2026-03-27（四段）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不含收益｜query_id=R0-Q12


| segment | test | what | status | detail |
|---|---|---|---|---|
| 2010-2014 | R01 | 真实字段 r_cc = r_on + r_id（有符号） | PASS | 3.27e-16; cells=2616939 |
| 2010-2014 | R02 | 真实字段 CC 涨跌零计数闭合 | PASS |  |
| 2010-2014 | R03 | 真实字段 Q_1 = MR3（CC） | PASS | 5.49e-11 |
| 2010-2014 | R04 | 真实字段 β = ρ·scale（CC） | PASS | 5.95e-16 |
| 2010-2014 | R02 | 真实字段 ID 涨跌零计数闭合 | PASS |  |
| 2010-2014 | R03 | 真实字段 Q_1 = MR3（ID） | PASS | 8.69e-13 |
| 2010-2014 | R04 | 真实字段 β = ρ·scale（ID） | PASS | 5.86e-16 |
| 2015-2018 | R01 | 真实字段 r_cc = r_on + r_id（有符号） | PASS | 3.26e-16; cells=3139477 |
| 2015-2018 | R02 | 真实字段 CC 涨跌零计数闭合 | PASS |  |
| 2015-2018 | R03 | 真实字段 Q_1 = MR3（CC） | PASS | 5.99e-11 |
| 2015-2018 | R04 | 真实字段 β = ρ·scale（CC） | PASS | 5.98e-16 |
| 2015-2018 | R02 | 真实字段 ID 涨跌零计数闭合 | PASS |  |
| 2015-2018 | R03 | 真实字段 Q_1 = MR3（ID） | PASS | 3.81e-12 |
| 2015-2018 | R04 | 真实字段 β = ρ·scale（ID） | PASS | 6.37e-16 |
| 2019-2023 | R01 | 真实字段 r_cc = r_on + r_id（有符号） | PASS | 4.44e-16; cells=5747653 |
| 2019-2023 | R02 | 真实字段 CC 涨跌零计数闭合 | PASS |  |
| 2019-2023 | R03 | 真实字段 Q_1 = MR3（CC） | PASS | 6.55e-11 |
| 2019-2023 | R04 | 真实字段 β = ρ·scale（CC） | PASS | 5.94e-16 |
| 2019-2023 | R02 | 真实字段 ID 涨跌零计数闭合 | PASS |  |
| 2019-2023 | R03 | 真实字段 Q_1 = MR3（ID） | PASS | 1.58e-12 |
| 2019-2023 | R04 | 真实字段 β = ρ·scale（ID） | PASS | 6.14e-16 |
| 2024-2026 | R01 | 真实字段 r_cc = r_on + r_id（有符号） | PASS | 4.44e-16; cells=3505487 |
| 2024-2026 | R02 | 真实字段 CC 涨跌零计数闭合 | PASS |  |
| 2024-2026 | R03 | 真实字段 Q_1 = MR3（CC） | PASS | 2.88e-11 |
| 2024-2026 | R04 | 真实字段 β = ρ·scale（CC） | PASS | 5.91e-16 |
| 2024-2026 | R02 | 真实字段 ID 涨跌零计数闭合 | PASS |  |
| 2024-2026 | R03 | 真实字段 Q_1 = MR3（ID） | PASS | 4.04e-13 |
| 2024-2026 | R04 | 真实字段 β = ρ·scale（ID） | PASS | 5.88e-16 |


> 表头：主体=E6i 源成员 vs E6j J 成员｜算子=pool0 格逐格比对｜分母=pool0 格｜基准=—｜子集=四段｜单位=占比 / 最大相对差 / 格数｜日期=2010-01-04..2026-03-27（四段）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=源成员已在 E6i 暴露｜query_id=R0-Q13


| segment | what | detail |
|---|---|---|
| 2010-2014 | K0_LEGACY vs J_B2_POINT_TR_CC（K0 锚：同式；有效掩码不同处可能差） | both=1.0000 exact_eq=1.0000 maxrel=0.00e+00 only_src=0 only_J=0 |
| 2010-2014 | K_MA3_E6F vs J_B2_MR3_TR_CC（源 mp(3)=2 与 J 至少 2 同；有效掩码不同） | both=0.9997 exact_eq=0.9773 maxrel=5.00e-01 only_src=50 only_J=0 |
| 2010-2014 | K_MA5_E6F vs J_B2_MR5_TR_CC（源 mp(5)=3 vs J 至少 4） | both=0.9986 exact_eq=0.9666 maxrel=2.50e-01 only_src=253 only_J=0 |
| 2010-2014 | K_ROS20_E6F vs J_B2_ROS20_TR_CC（源 mp(20)=10 vs J 10） | both=1.0000 exact_eq=0.8584 maxrel=9.88e-03 only_src=0 only_J=0 |
| 2010-2014 | K_slope20 vs J_B2_SLOPE20_TR_CC（源 minobs 14 vs J 10） | both=0.9976 exact_eq=0.0133 maxrel=9.58e-10 only_src=0 only_J=435 |
| 2010-2014 | K_rar20 vs J_B1_S20lag（源 minobs 14 vs J 10（代数同式）） | both=0.9970 exact_eq=0.7393 maxrel=2.22e-16 only_src=0 only_J=551 |
| 2010-2014 | K_rarpre vs J_B5_RARPRE_CC_W20_LT（源 minobs 14 vs J 10；同 last_trigger 时钟） | both=0.9950 exact_eq=1.0000 maxrel=0.00e+00 only_src=0 only_J=880 |
| 2010-2014 | T_cv20 vs J_B6_CV20（源 minobs 14 vs J 10） | both=0.9977 exact_eq=1.0000 maxrel=0.00e+00 only_src=0 only_J=435 |
| 2010-2014 | K_amt20 vs J_B2_SLOPE20_AMT_CC（不同估计量（均比 vs 斜率），只作量纲参照） | both=0.9977 exact_eq=0.0000 maxrel=3.61e+00 only_src=0 only_J=435 |
| 2015-2018 | K0_LEGACY vs J_B2_POINT_TR_CC（K0 锚：同式；有效掩码不同处可能差） | both=1.0000 exact_eq=1.0000 maxrel=0.00e+00 only_src=0 only_J=0 |
| 2015-2018 | K_MA3_E6F vs J_B2_MR3_TR_CC（源 mp(3)=2 与 J 至少 2 同；有效掩码不同） | both=0.9998 exact_eq=0.9969 maxrel=5.00e-01 only_src=38 only_J=0 |
| 2015-2018 | K_MA5_E6F vs J_B2_MR5_TR_CC（源 mp(5)=3 vs J 至少 4） | both=0.9988 exact_eq=0.9952 maxrel=2.50e-01 only_src=285 only_J=0 |
| 2015-2018 | K_ROS20_E6F vs J_B2_ROS20_TR_CC（源 mp(20)=10 vs J 10） | both=1.0000 exact_eq=0.9439 maxrel=4.16e-02 only_src=0 only_J=0 |
| 2015-2018 | K_slope20 vs J_B2_SLOPE20_TR_CC（源 minobs 14 vs J 10） | both=0.9951 exact_eq=0.0087 maxrel=1.21e-09 only_src=0 only_J=1205 |
| 2015-2018 | K_rar20 vs J_B1_S20lag（源 minobs 14 vs J 10（代数同式）） | both=0.9940 exact_eq=0.7392 maxrel=2.22e-16 only_src=0 only_J=1483 |
| 2015-2018 | K_rarpre vs J_B5_RARPRE_CC_W20_LT（源 minobs 14 vs J 10；同 last_trigger 时钟） | both=0.9911 exact_eq=1.0000 maxrel=0.00e+00 only_src=0 only_J=2077 |
| 2015-2018 | T_cv20 vs J_B6_CV20（源 minobs 14 vs J 10） | both=0.9951 exact_eq=1.0000 maxrel=0.00e+00 only_src=0 only_J=1205 |
| 2015-2018 | K_amt20 vs J_B2_SLOPE20_AMT_CC（不同估计量（均比 vs 斜率），只作量纲参照） | both=0.9951 exact_eq=0.0000 maxrel=6.18e+00 only_src=0 only_J=1205 |
| 2019-2023 | K0_LEGACY vs J_B2_POINT_TR_CC（K0 锚：同式；有效掩码不同处可能差） | both=1.0000 exact_eq=1.0000 maxrel=0.00e+00 only_src=0 only_J=0 |
| 2019-2023 | K_MA3_E6F vs J_B2_MR3_TR_CC（源 mp(3)=2 与 J 至少 2 同；有效掩码不同） | both=1.0000 exact_eq=0.9995 maxrel=5.00e-01 only_src=11 only_J=0 |
| 2019-2023 | K_MA5_E6F vs J_B2_MR5_TR_CC（源 mp(5)=3 vs J 至少 4） | both=0.9999 exact_eq=0.9992 maxrel=2.50e-01 only_src=55 only_J=0 |
| 2019-2023 | K_ROS20_E6F vs J_B2_ROS20_TR_CC（源 mp(20)=10 vs J 10） | both=1.0000 exact_eq=0.9953 maxrel=6.98e-03 only_src=0 only_J=0 |
| 2019-2023 | K_slope20 vs J_B2_SLOPE20_TR_CC（源 minobs 14 vs J 10） | both=0.9997 exact_eq=0.0068 maxrel=1.37e-09 only_src=0 only_J=133 |
| 2019-2023 | K_rar20 vs J_B1_S20lag（源 minobs 14 vs J 10（代数同式）） | both=0.9996 exact_eq=0.7385 maxrel=2.22e-16 only_src=0 only_J=156 |
| 2019-2023 | K_rarpre vs J_B5_RARPRE_CC_W20_LT（源 minobs 14 vs J 10；同 last_trigger 时钟） | both=0.9995 exact_eq=1.0000 maxrel=0.00e+00 only_src=0 only_J=210 |
| 2019-2023 | T_cv20 vs J_B6_CV20（源 minobs 14 vs J 10） | both=0.9997 exact_eq=1.0000 maxrel=0.00e+00 only_src=0 only_J=133 |
| 2019-2023 | K_amt20 vs J_B2_SLOPE20_AMT_CC（不同估计量（均比 vs 斜率），只作量纲参照） | both=0.9997 exact_eq=0.0000 maxrel=5.70e+00 only_src=0 only_J=133 |
| 2024-2026 | K0_LEGACY vs J_B2_POINT_TR_CC（K0 锚：同式；有效掩码不同处可能差） | both=1.0000 exact_eq=1.0000 maxrel=0.00e+00 only_src=0 only_J=0 |
| 2024-2026 | K_MA3_E6F vs J_B2_MR3_TR_CC（源 mp(3)=2 与 J 至少 2 同；有效掩码不同） | both=1.0000 exact_eq=0.9999 maxrel=5.00e-01 only_src=6 only_J=0 |
| 2024-2026 | K_MA5_E6F vs J_B2_MR5_TR_CC（源 mp(5)=3 vs J 至少 4） | both=0.9999 exact_eq=0.9998 maxrel=2.50e-01 only_src=28 only_J=0 |
| 2024-2026 | K_ROS20_E6F vs J_B2_ROS20_TR_CC（源 mp(20)=10 vs J 10） | both=1.0000 exact_eq=0.9979 maxrel=9.55e-03 only_src=0 only_J=0 |
| 2024-2026 | K_slope20 vs J_B2_SLOPE20_TR_CC（源 minobs 14 vs J 10） | both=0.9998 exact_eq=0.0098 maxrel=2.56e-10 only_src=0 only_J=64 |
| 2024-2026 | K_rar20 vs J_B1_S20lag（源 minobs 14 vs J 10（代数同式）） | both=0.9997 exact_eq=0.7396 maxrel=2.22e-16 only_src=0 only_J=71 |
| 2024-2026 | K_rarpre vs J_B5_RARPRE_CC_W20_LT（源 minobs 14 vs J 10；同 last_trigger 时钟） | both=0.9996 exact_eq=1.0000 maxrel=0.00e+00 only_src=0 only_J=96 |
| 2024-2026 | T_cv20 vs J_B6_CV20（源 minobs 14 vs J 10） | both=0.9998 exact_eq=1.0000 maxrel=0.00e+00 only_src=0 only_J=64 |
| 2024-2026 | K_amt20 vs J_B2_SLOPE20_AMT_CC（不同估计量（均比 vs 斜率），只作量纲参照） | both=0.9998 exact_eq=0.0000 maxrel=1.25e+01 only_src=0 only_J=64 |


读法：J_B2_POINT_TR_CC 与 K0 逐位同值（K0 锚，账户 = 母体，不重复计算）；J_B6_CV20、J_B5_RARPRE_CC_W20_LT 与源在共同格逐位同值、只多出最少观测数（10 vs 14）带来的覆盖；J_B1_S20lag、J_B2_SLOPE20_TR_CC 与源差在浮点与覆盖；J_B2_MR3 / MR5 / ROS20 与源的差来自有效 OHLC 掩码（源在全市场原值上算）——按 plan §3.4 各自保留、不合并〔R0-Q13〕。

> 表头：主体=110 个 J 原值｜算子=pool0 格有限值占比｜分母=pool0 格｜基准=—｜子集=按块｜单位=占比｜日期=2010-01-04..2026-03-27（四段）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=—｜query_id=R0-Q14


| block | 2010-2014_min | 2010-2014_median | 2015-2018_min | 2015-2018_median | 2019-2023_min | 2019-2023_median | 2024-2026_min | 2024-2026_median |
|---|---|---|---|---|---|---|---|---|
| B1 | 0.9828 | 1 | 0.987 | 1 | 0.9992 | 1 | 0.9999 | 1 |
| B2 | 0.9986 | 1 | 0.9988 | 1 | 0.9999 | 1 | 0.9999 | 1 |
| B3A | 0.9997 | 0.9999 | 0.9998 | 0.9999 | 1 | 1 | 1 | 1 |
| B3B | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| B3C | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| B4 | 0.9987 | 0.9995 | 0.9983 | 0.9991 | 0.9994 | 0.9997 | 0.9997 | 0.9998 |
| B5 | 0.9778 | 0.9894 | 0.9844 | 0.9922 | 0.9988 | 0.9994 | 0.9997 | 0.9999 |
| B6 | 0.9955 | 1 | 0.9936 | 1 | 1 | 1 | 1 | 1 |


## 6. 种子重放、E7 守卫、A0 编译（第 5 项）

> 表头：主体=R1 × K_rar20（低坏）IID 随机路径 8 条（推导段 2010-2014）｜算子=哈希比对（不读收益值）｜分母=路径｜基准=—｜子集=—｜单位=逐位相同与否｜日期=2010-01-04..2026-03-27（四段）｜H=5｜成本模型=8bp｜支持=native｜资本视图=—｜exposure=不读数值｜query_id=R0-Q15


| test | what | status | detail |
|---|---|---|---|
| Z1 | u 矩阵：整段 vs 日期切两半后拼接逐位相同 | PASS |  |
| Z2 | u 矩阵：列重排后按 ticker 对回逐位相同 | PASS |  |
| Z3 | P5：同一绝对五日块内优先序逐位相同 | PASS |  |
| Z4 | 路径键：同 JSON 同键、换 path_index 不同键（blake2b，与进程无关） | PASS |  |
| Z5 | serial vs 两进程并行（奇偶分片）：8 条路径 掩码 / 权重 / net8 哈希逐位相同 | PASS | pids=5 |
| Z6 | serial vs 续跑（0–3 后 4–7）：8 条路径哈希逐位相同 | PASS |  |
| Z7 | 不同路径的掩码哈希互不相同（随机确有作用） | PASS |  |


> 表头：主体=E6j 触及行情 / 特征的全部入口（覆盖矩阵 G1–G7）｜算子=合成未来数据 / 伪造 sidecar 攻击｜分母=入口｜基准=—｜子集=—｜单位=是否拦截｜日期=2010-01-04..2026-03-27（四段）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=—｜query_id=R0-Q16


| entry_id | entry | attack | status | detail |
|---|---|---|---|---|
| G1 | e6j_prod.build_period | 段 ('20260301','20260410') | PASS | RuntimeError('E7 守卫：PERIODS[__ATTACK__] 的截止日 2026-04-10 晚于 2026-03-27'); load calls=0 |
| G2 | e6f_core.guarded_load（seg_i 唯一取数口） | guarded_load('20260301','20260401') | PASS | RuntimeError('E7 GUARD 触发 (GLOBAL STOP): end_date=20260401 > 冻结末日 20260327。源数据物理上有更晚日期, 但 E6f 禁区 §12 禁止读取。') |
| G3 | e6j_slot.e6i_member_raw | sidecar max_feature_date=2026-04-01 | PASS | RuntimeError('E7 守卫：member 2024-2026/FAKE max_feature_date 的截止日 2026-04-01 晚于 2026-03-27') |
| G4 | e6j_slot.j_member_raw | sidecar max_feature_date=2026-04-01 | PASS | RuntimeError('E7 守卫：J member 2024-2026/FAKE_J max_feature_date 的截止日 2026-04-01 晚于 2026-03-27') |
| G5 | e6j_core.assert_index_ok | 索引含 20260330 | PASS | RuntimeError('E7 守卫：attack 含 2026-03-27 之后的日期 2026-03-30') |
| G5b | e6j_core.assert_index_ok | 合法索引（止于 20260327）不应误报 | PASS |  |
| G6 | e6j_random.Grid / day_index | 日期 2026-03-30 不在日历 | PASS | RuntimeError('日期不在全样本交易日历内') |
| G6b | registry/trade_calendar.csv | 日历末日 | PASS | 2026-03-27 |
| G7a | anchors/mother_ledger_prod_v2.parquet | 账本末日 | PASS | 2026-03-27 |
| G7b | cache/<段>/J_*.json | J 成员 max_feature_date 最大值 | PASS | 2026-03-27 |


> 表头：主体=A0 登记编译（P 528 / B 210 行）｜算子=登记展开 vs 任务规划器独立枚举；逐元组比对｜分母=描述符｜基准=—｜子集=W10 H 网格 × α 网格｜单位=个 / 是否｜日期=2010-01-04..2026-03-27（四段）｜H=B {1,2,3,5,10,15,20}；P {3,5,10,20}｜成本模型=8bp｜支持=native（CS 另表）｜资本视图=—｜exposure=—｜query_id=R0-Q17


| item | value |
|---|---|
| rows | 210 |
| blocks | {"B1": 12, "B2": 64, "B3A": 20, "B3B": 12, "B3C": 2, "B4": 24, "B5": 64, "B6": 8, "B7": 4} |
| P | 528 |
| P_main | 312 |
| P_cols | 216 |
| B_per_segment | 13398 |
| CS_B | 5104 |
| CS_P | 192 |
| question_rows | 21396 |
| task_rows | 13926 |
| tasks | 2046 |
| exposure_rows | 584 |
| brief 写的 B 计数 | 13230 |
| 编译器现算 B 计数 | 13398 |
| check:rows_210 | True |
| check:blocks | True |
| check:P_528 | True |
| check:P_main_312 | True |
| check:P_cols_216 | True |
| check:B_per_segment | True |
| check:B_equals_13398 | True |
| check:ids_unique | True |
| check:question_eq_task | True |
| check:question_eq_registry | True |
| check:every_object_has_question | True |
| check:main_config_everywhere | True |
| check:H_set | True |
| check:alpha_set | True |
| check:A08_only_B6 | True |
| check:B6_only_T | True |
| check:B7_K_and_T | True |


> 表头：主体=P 描述符与 B 登记行｜算子=E6i merged_index 查找 + 登记规则｜分母=台账行｜基准=—｜子集=—｜单位=行数｜日期=2010-01-04..2026-03-27（四段）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=见各类｜query_id=R0-Q18


| exposure_type | rows |
|---|---|
| related_exposed | 300 |
| new_combination | 144 |
| direction_2of1 | 72 |
| alias_of | 61 |
| source_member_seen | 7 |


> 表头：主体=plan §13.3 合成脚本（从 PLAN_COPY.md 提取，sha 与 plan 所记一致）｜算子=原样运行｜分母=命名检查｜基准=—｜子集=—｜单位=项｜日期=2010-01-04..2026-03-27（四段）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不碰行情；不是真实回测｜query_id=R0-Q19


| total | passed | python | numpy | pandas | script_sha_prefix |
|---|---|---|---|---|---|
| 90 | 90 | 3.10.13 | 1.26.1 | 2.2.3 | a3fec9bd |


plan 合成测试 T81 / T84 按 plan 原网格 H = 1…20 断言，原样通过；W10 的 7 档计数由 A0 编译器另核〔R0-Q17、R0-Q19〕。

## 7. 限制与待办（不影响 Stage 0 结论）

- Stage 0 第 4 项的真实字段检验在四段上计算了 J 原值、覆盖与别名统计（无任何收益、无账户）；B 包后段账户与收益关联统计仍按记录 B 生效条件执行。

- W03 所引 E6i 投入资金 0.317 / 0.520 / 0.700 / 0.833 的出处表未定位；同一账本上两种定义实算见〔R0-Q06〕。

- 段首事件钟沿 E6i：预热期无已知触发，段首 spell / 触发被截断（登记为限制，不改源）。

- 下一步：Stage A 两个登记包（P / B）同时冻结 → A0 登记落盘 → Stage 1 推导段测量诊断 → profile 后报并发与时长。
