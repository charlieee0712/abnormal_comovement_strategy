# E6l REPORT R0 —— 仪器与权限：输入身份、授权、Stage 0、登记计数、掩码事实、耗时与限制

用途：plan §13.4 R0。数字来自 `source_manifest.json`、`stage0/`、`registration/`、`registry/`、`results/stage_a/`；本文件不读任何登记对象的收益均值（校准分布与状态日数只作描述，注明未用于门值）。

## 1. 输入身份与环境

> 表头：主体=本轮输入与结果目录副本｜算子=—｜分母=—｜基准=—｜子集=source_manifest.docs_sha256｜单位=文本｜日期=Stage 0｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6L-R0-DOCS


| file | sha256_16 |
|---|---|
| 00_协议_copy.md | f685e538dd6c5a27 |
| E6k_REPORT_supplement_1_copy.md | 8b6dedc92c12c807 |
| E6k_REVIEW_copy.md | 8ef42f86b7cb6984 |
| E6k_RULING_copy.md | b0a87798a896dfab |
| E6k_VERIFY_report_copy.md | 7281cd63e95c92ef |
| E6k_code_change_register_copy.md | fd822bcb660e9582 |
| E6l_proposal_copy.md | f79c523a98ccf3c4 |
| REVIEW_protocol_copy.md | 0b15019e0867a7a0 |
| brief_appendix_copy.md | f5c33bc783418ffb |
| brief_copy.md | 4c55fb4b051954b6 |
| PLAN_COPY.md | e7385cb784df6818 |
| engine_contract.md | a08038ed27f6ed19 |
| source_resolution.md | be7b5770a5a38580 |


> 表头：主体=47 环境与生成器｜算子=—｜分母=—｜基准=—｜子集=source_manifest.env｜单位=文本｜日期=Stage 0｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=—｜资本视图=—｜exposure=不适用｜query_id=E6L-R0-ENV


| item | value |
|---|---|
| python | 3.10.13 |
| numpy | 1.26.1 |
| pandas | 2.2.3 |
| scipy | 1.11.3 |
| numba | 0.58.1 |
| statsmodels | 0.14.0 |
| polars | NOT_USED |
| numba_cache | NUMBA_CACHE_DIR = 研究临时目录（不写共享环境）；e6l_fast 全部 njit(cache=True, error_model="numpy") |
| permutation_generator | splitmix64x2-counter(key^block*C1^ticker*C2)>>11 * 2^-53; key=blake2b-64(canonical_json) |
| bootstrap_generator | blake2b-128(canonical_json(key)) -> SeedSequence -> PCG64 |
| cpu_binding | taskset -c 96-191,288-383；并发 ≤ 64；BLAS 线程 4 |
| git_head | ec91def327bc |


> 表头：主体=随机量 → 生成器｜算子=—｜分母=—｜基准=—｜子集=全部随机量｜单位=文本｜日期=全段｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=—｜资本视图=—｜exposure=不适用｜query_id=E6L-R0-GEN


| random_quantity | generator |
|---|---|
| LEGACY_POLICY_RANDOM | splitmix64 计数器 u(键, 绝对交易日, ticker)；键 = blake2b-64(canonical_json)：Q0 / C1 / S / M 沿 E6k Legacy（E6j.P / E6j.B），新测量 E6j.P + 成员 id E6l.<测量> |
| CONTENT_COND_ISK_P5 | 同一计数器；键 (E6k.NEW, 测量键, COND_ISK, B5, content, path)；Q0 键 = Q（E6k 同路径）；块 = 绝对交易日 // 5 |
| RMARK_UNIFORM_IID / UNIFORM_P5 / ISK_P5 | 同一计数器；键 (E6l.RMARK, 机制, ALL, gate, marks, path)；全测量 / 母体 / α 共用 |
| bootstrap（段内分层 stationary 20 / 60 × 2,000） | blake2b-128(canonical_json(E6l, bootstrap, L, 段)) → SeedSequence → PCG64 |
| profile 置换（只测时，临时目录） | default_rng(blake2b(E6l.profile, 段, 测量)) |


## 2. 授权（方式 B）与读数前登记

> 表头：主体=授权 / 登记 / 封存文件｜算子=—｜分母=—｜基准=—｜子集=registration/｜单位=文本｜日期=全程｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=—｜资本视图=—｜exposure=不适用｜query_id=E6L-R0-AUTH


| file | sha256_16 |
|---|---|
| registration/B_package_manifest_E6l.json | 02a2d2ca9058e929 |
| registration/P_package_manifest_E6l.json | 8805206989df4a3c |
| registration/a0_manifest_E6l.json | f31464da37229bfc |
| registration/a1_auto_E6l.json | 6e6458cb6e4e3208 |
| registration/a1_auto_E6l_rerun.json | 382041ff0223fcc7 |
| registration/a1_auto_E6l_rerun2.json | a4d26aad22c9bdbb |
| registration/a1_auto_E6l_rerun3.json | d7100c2e380216e4 |
| registration/a1_auto_draft_E6l.json | a564abac34949b43 |
| registration/authorization_intake_E6l.json | cca52495d3cad75c |
| registration/policy_profiles_E6l.json | 590d200fee3f0d9e |
| registration/preregistration_B_E6l.md | 3d1a6be1dec52f6a |
| registration/preregistration_P_E6l.md | a5cc93fb81a63e06 |
| registration/record_B_conditions_receipt_E6l.json | 585e619a0077b95b |
| registration/record_B_draft_objects_E6l.csv | 60348c11acdce402 |
| registration/record_B_entry_post_E6l.json | a1a61caaa1486a27 |
| registration/record_B_preauthorized_E6l.json | 35a7027e5895577f |
| registration/seal_deriv.json | 60b7e4d1274df18c |
| registration/seal_post.json | aadceca4a2c73978 |


- 授权方式 B：用户转交消息原话「记得好好思考提速优化方案 中途不需要停下来报告 避免空转」（不含 W11 字面触发词）；执行端当场询问，用户选「方式 B：一口气跑完」（2026-09-30）。`record_B_preauthorized_E6l.json` 在 Stage A / B 两包冻结时写入，引用两句原话与 B 包清单 sha；生效条件 = Stage 0 全 PASS + A1-auto 全 PASS + 进入后段时清单 sha 不变（`record_B_entry_post_E6l.json` 核验）。经济裁定 = E6k RULING 第 2 项（PORT3_T 正式列，policy_provisional = false）。

## 3. Stage 0 六类（FAILED 由同名 _rerun 覆盖）

> 表头：主体=Stage 0 六类回执｜算子=—｜分母=—｜基准=—｜子集=source_manifest.stage0｜单位=计数｜日期=Stage 0｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=—｜资本视图=—｜exposure=不适用｜query_id=E6L-R0-STAGE0


| category | ok | receipts |
|---|---|---|
| 1_identity | True | stage0_c1_identity_rerun=SUCCEEDED |
| 2_source | True | stage0_c2_source_prod=SUCCEEDED；stage0_c2_source_engine_2010-2014=SUCCEEDED；stage0_c2_source_engine_2015-2018=SUCCEEDED；stage0_c2_source_engine_2019-2023=SUCCEEDED；stage0_c2_source_engine_2024-2026=SUCCEEDED |
| 3_new_operators_deriv | True | stage0_c3_ops_2010-2014=SUCCEEDED；stage0_c3_ops_2015-2018=SUCCEEDED |
| 4_data_clock | True | stage0_c4_state=SUCCEEDED；stage0_c4_data_2010-2014=SUCCEEDED；stage0_c4_data_2015-2018=SUCCEEDED；stage0_c4_data_2019-2023=SUCCEEDED；stage0_c4_data_2024-2026=SUCCEEDED |
| 5_random_state | True | stage0_c5_random_rerun=SUCCEEDED |
| 6_output_resources | True | stage0_c6_fast=SUCCEEDED；stage0_c6_output_rerun=SUCCEEDED |


> 表头：主体=Stage 0 检查表计数｜算子=—｜分母=—｜基准=—｜子集=stage0/*｜单位=计数｜日期=Stage 0｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=—｜资本视图=—｜exposure=不适用｜query_id=E6L-R0-STAGE0-COUNTS


| category | file | PASS | INFO | FAIL |
|---|---|---|---|---|
| c1 | stage0/c1_identity_rerun/identity_checks.csv | 336 | 10 | 0 |
| c2 | stage0/c2_source/source_prod_checks.csv | 187 | 0 | 0 |
| c2 | stage0/c2_source/source_engine_2024-2026.csv | 139 | 0 | 0 |
| c2 | stage0/c2_source/source_engine_2015-2018.csv | 139 | 0 | 0 |
| c2 | stage0/c2_source/source_engine_2010-2014.csv | 139 | 0 | 0 |
| c2 | stage0/c2_source/source_engine_2019-2023.csv | 139 | 0 | 0 |
| c3 | stage0/c3_ops/ops_identity_2010-2014.csv | 210 | 58 | 0 |
| c3 | stage0/c3_ops/ops_identity_2015-2018.csv | 210 | 58 | 0 |
| c4 | stage0/c4_data/state_checks.csv | 6 | 5 | 0 |
| c4 | stage0/c4_data/data_checks_2010-2014.csv | 4 | 6 | 0 |
| c4 | stage0/c4_data/data_checks_2015-2018.csv | 4 | 6 | 0 |
| c4 | stage0/c4_data/data_checks_2024-2026.csv | 4 | 6 | 0 |
| c4 | stage0/c4_data/data_checks_2019-2023.csv | 4 | 6 | 0 |
| c5 | stage0/c5_random_rerun/random_checks.csv | 11 | 1 | 0 |
| c6 | stage0/c6_output/fast_identity.csv | 13 | 0 | 0 |
| c6 | stage0/c6_output_rerun/output_checks.csv | 3 | 4 | 0 |


## 4. 登记计数（A0 与 spec 逐元组相等；A1-auto）

> 表头：主体=A0 计数｜算子=—｜分母=—｜基准=—｜子集=registration/a0_manifest_E6l.json｜单位=计数｜日期=登记｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=—｜资本视图=—｜exposure=不适用｜query_id=E6L-R0-A0


| item | value |
|---|---|
| raw_id_count | 34120 |
| block_counts | {"CORE": 15840, "CONTROL": 2880, "MEMORY": 5760, "STATE": 4320, "OLD_RULE": 1320, "BRIDGE": 1440, "EDGE": 2160, "EDGE_OLD": 240, "PARENT": 160} |
| primary72 / dose72 / nbhd72 | 72 / 72 / 72 |
| targets / tasks | 3188 / 104 |
| accessory | {"INV_CAP_LOOP_PAIR": 1560, "INV_CAP_LOOP_PARENT": 1560, "SUPPORT_MASKQ0": 432, "KERNEL_DOSE": 432, "SUPPORT_CS_CHILD": 432, "SUPPORT_CS_PARENT": 432, "STRICT250_STATE": 96, "BOUNDARY_CONT_PARENT_PAIR": 72, "BOUNDARY_CONT_PARENT": 72} |
| comparisons base / extended | 172440 / 144420 |
| randoms | {"LEGACY_POLICY_RANDOM": 9720, "CONTENT_COND_ISK_P5": 9720, "RMARK_UNIFORM_IID": 180, "RMARK_UNIFORM_P5": 180, "RMARK_ISK_P5": 180} |
| bootstrap families | {"child_minus_parent": 33960, "minus_Q0_HG10": 32040, "mechanism_pair": 27840, "minus_same_op_Q0": 27360, "minus_same_op_C1": 27360, "minus_same_meas_native": 26640, "minus_rule_only": 26640, "kernel_pair_window_pair": 5760, "kernel_pair_mean_kernel_pair": 4320, "kernel_pair_ma_vs_ew": 2880, "kernel_pair_rank_bridge_pair": 1440, "kernel_pair_smn_pair": 720} |
| exposure | {"NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY": 31184, "SECOND_EVALUATION_SAME_HISTORY": 2776, "SOURCE_PARENT": 160} |
| E6k 同构（真实清单交集） | 2936 |
| spec 对账 | {"ok": true, "design_only_mine": 0, "design_only_spec": 0, "design_block_diffs": 0, "policy_content_equal": true, "memory_random_equal": true, "support_equal": true, "comparison_equal": true, "audit_control_equal": true} |


## 5. 掩码层事实与校准分布（Stage A；推导两段读数前 + 后段授权后）

> 表头：主体=附录 C 校准分布（deriv；诊断，不作门）｜算子=—｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=—｜子集=C1 / Q 平滑族 / Q0 / 旧 K 规则 / 母体｜单位=pct_pt（紧区间）/ 份额｜日期=deriv｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-R0-CAL-DERIV


| segment | group | column | n_targets | p50 | p90 | p95 | share_outside_pm3_pct_pt |
|---|---|---|---|---|---|---|---|
| 2010-2014 | C1 | size_port_lo_T_segavg | 594 | -0.2286 | 0.3686 | 0.5065 | 0 |
| 2010-2014 | C1 | size_port_hi_T_segavg | 594 | -0.2262 | 0.3686 | 0.5065 | 0 |
| 2010-2014 | C1 | size_port_delta_T | 594 | -0.2276 | 0.3686 | 0.5065 | 0 |
| 2010-2014 | C1 | lv5_mean | 594 | -0.0462 | 0.04714 | 0.04732 |  |
| 2010-2014 | Q_SMOOTH | size_port_lo_T_segavg | 1728 | 0.06138 | 1.388 | 1.476 | 0.003472 |
| 2010-2014 | Q_SMOOTH | size_port_hi_T_segavg | 1728 | 0.06232 | 1.391 | 1.477 | 0.003472 |
| 2010-2014 | Q_SMOOTH | size_port_delta_T | 1728 | 0.06183 | 1.389 | 1.477 | 0.003472 |
| 2010-2014 | Q_SMOOTH | lv5_mean | 1728 | -0.0504 | 0.04418 | 0.0456 |  |
| 2010-2014 | Q0 | size_port_lo_T_segavg | 594 | -0.03595 | 0.5498 | 0.5795 | 0.03872 |
| 2010-2014 | Q0 | size_port_hi_T_segavg | 594 | -0.03589 | 0.5519 | 0.5796 | 0.03872 |
| 2010-2014 | Q0 | size_port_delta_T | 594 | -0.03592 | 0.5505 | 0.5796 | 0.03872 |
| 2010-2014 | Q0 | lv5_mean | 594 | -0.04538 | 0.04545 | 0.04599 |  |
| 2010-2014 | OLD_RULE_K0 | size_port_lo_T_segavg | 192 | -0.05345 | 0.628 | 0.6472 | 0 |
| 2010-2014 | OLD_RULE_K0 | size_port_hi_T_segavg | 192 | -0.05341 | 0.628 | 0.6472 | 0 |
| 2010-2014 | OLD_RULE_K0 | size_port_delta_T | 192 | -0.05343 | 0.628 | 0.6472 | 0 |
| 2010-2014 | OLD_RULE_K0 | lv5_mean | 192 | -0.0452 | 0.04707 | 0.04716 |  |
| 2015-2018 | C1 | size_port_lo_T_segavg | 594 | -0.2006 | 0.432 | 0.5201 | 0 |
| 2015-2018 | C1 | size_port_hi_T_segavg | 594 | -0.2003 | 0.4356 | 0.5216 | 0 |
| 2015-2018 | C1 | size_port_delta_T | 594 | -0.2005 | 0.4338 | 0.5208 | 0 |
| 2015-2018 | C1 | lv5_mean | 594 | 0.04512 | 0.1078 | 0.1079 |  |
| 2015-2018 | Q_SMOOTH | size_port_lo_T_segavg | 1728 | -0.1062 | 1.478 | 1.702 | 0.04514 |
| 2015-2018 | Q_SMOOTH | size_port_hi_T_segavg | 1728 | -0.1053 | 1.487 | 1.707 | 0.04572 |
| 2015-2018 | Q_SMOOTH | size_port_delta_T | 1728 | -0.1057 | 1.482 | 1.704 | 0.04514 |
| 2015-2018 | Q_SMOOTH | lv5_mean | 1728 | 0.042 | 0.105 | 0.1067 |  |
| 2015-2018 | Q0 | size_port_lo_T_segavg | 594 | -0.3501 | 0.3764 | 0.5146 | 0.08754 |
| 2015-2018 | Q0 | size_port_hi_T_segavg | 594 | -0.3494 | 0.3792 | 0.5163 | 0.08586 |
| 2015-2018 | Q0 | size_port_delta_T | 594 | -0.3497 | 0.3778 | 0.5154 | 0.08586 |
| 2015-2018 | Q0 | lv5_mean | 594 | 0.05586 | 0.1059 | 0.1067 |  |
| 2015-2018 | OLD_RULE_K0 | size_port_lo_T_segavg | 192 | -0.08003 | 0.6096 | 0.6388 | 0 |
| 2015-2018 | OLD_RULE_K0 | size_port_hi_T_segavg | 192 | -0.07981 | 0.6109 | 0.6397 | 0 |
| 2015-2018 | OLD_RULE_K0 | size_port_delta_T | 192 | -0.07992 | 0.6102 | 0.6393 | 0 |
| 2015-2018 | OLD_RULE_K0 | lv5_mean | 192 | 0.0464 | 0.1081 | 0.1084 |  |
| 2010-2014 | PARENT | lv5_mean | 8 | -0.05575 | 0.02724 | 0.03733 |  |
| 2015-2018 | PARENT | lv5_mean | 8 | 0.02773 | 0.1021 | 0.1052 |  |


> 表头：主体=状态三分位日数与 UNKNOWN（deriv）｜算子=—｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=—｜子集=Vol3 / Act3（主 / STRICT250）/ Trend3｜单位=日数 / 份额｜日期=deriv｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-R0-STATE-DERIV


| segment | variable | definition | unknown_days | low_days | mid_days | high_days |
|---|---|---|---|---|---|---|
| 2010-2014 | Vol3 | MAIN_GE150 | 186 | 404 | 338 | 284 |
| 2010-2014 | Vol3 | STRICT250 | 286 | 381 | 290 | 255 |
| 2010-2014 | Act3 | MAIN_GE150 | 202 | 313 | 359 | 338 |
| 2010-2014 | Act3 | STRICT250 | 302 | 263 | 338 | 309 |
| 2010-2014 | Trend3 | ENDPOINT_MA20_GE16（pool0 单元份额） | 0.04908 | 0.2596 | 0.1815 | 0.5098 |
| 2015-2018 | Vol3 | MAIN_GE150 | 0 | 299 | 299 | 377 |
| 2015-2018 | Vol3 | STRICT250 | 0 | 299 | 299 | 377 |
| 2015-2018 | Act3 | MAIN_GE150 | 0 | 379 | 324 | 272 |
| 2015-2018 | Act3 | STRICT250 | 0 | 379 | 324 | 272 |
| 2015-2018 | Trend3 | ENDPOINT_MA20_GE16（pool0 单元份额） | 0.03613 | 0.314 | 0.1832 | 0.4667 |


> 表头：主体=R-MARK ISK 分区（deriv）｜算子=—｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=—｜子集=六形态门域｜单位=计数 / 份额｜日期=deriv｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-R0-RMARKPART-DERIV


| segment | mother | leaves_per_day_p10 | leaves_per_day_p50 | leaves_per_day_p90 | movable_cell_share_p10 | movable_cell_share_p50 | tree |
|---|---|---|---|---|---|---|---|
| 2010-2014 | A4b | 7 | 8 | 9 | 1 | 1 | {"I": {"nodes_split": 46, "nodes_total": 1193}, "K": {"nodes_split": 1742, "nodes_total": 2342}, "S": {"nodes_split": 4034, "nodes_total": 5464}} |
| 2010-2014 | A4b_CVRv5 | 7 | 8 | 9 | 1 | 1 | {"I": {"nodes_split": 46, "nodes_total": 1193}, "K": {"nodes_split": 1742, "nodes_total": 2342}, "S": {"nodes_split": 4034, "nodes_total": 5464}} |
| 2010-2014 | M_mean3_v2 | 7 | 8 | 9 | 1 | 1 | {"I": {"nodes_split": 46, "nodes_total": 1183}, "K": {"nodes_split": 1732, "nodes_total": 2332}, "S": {"nodes_split": 4006, "nodes_total": 5434}} |
| 2010-2014 | M_mean3_v2_CVRv5 | 7 | 8 | 9 | 1 | 1 | {"I": {"nodes_split": 46, "nodes_total": 1183}, "K": {"nodes_split": 1732, "nodes_total": 2332}, "S": {"nodes_split": 4006, "nodes_total": 5434}} |
| 2010-2014 | M_union3_v2 | 7 | 8 | 9 | 1 | 1 | {"I": {"nodes_split": 46, "nodes_total": 1193}, "K": {"nodes_split": 1742, "nodes_total": 2342}, "S": {"nodes_split": 4034, "nodes_total": 5464}} |
| 2010-2014 | M_union3_v2_CVRv5 | 7 | 8 | 9 | 1 | 1 | {"I": {"nodes_split": 46, "nodes_total": 1193}, "K": {"nodes_split": 1742, "nodes_total": 2342}, "S": {"nodes_split": 4034, "nodes_total": 5464}} |
| 2015-2018 | A4b | 7 | 9 | 69 | 1 | 1 | {"I": {"nodes_split": 180, "nodes_total": 956}, "K": {"nodes_split": 3730, "nodes_total": 5768}, "S": {"nodes_split": 6483, "nodes_total": 12154}} |
| 2015-2018 | A4b_CVRv5 | 7 | 9 | 69 | 1 | 1 | {"I": {"nodes_split": 180, "nodes_total": 956}, "K": {"nodes_split": 3730, "nodes_total": 5768}, "S": {"nodes_split": 6483, "nodes_total": 12154}} |
| 2015-2018 | M_mean3_v2 | 7 | 9 | 69 | 1 | 1 | {"I": {"nodes_split": 179, "nodes_total": 946}, "K": {"nodes_split": 3712, "nodes_total": 5733}, "S": {"nodes_split": 6439, "nodes_total": 12083}} |
| 2015-2018 | M_mean3_v2_CVRv5 | 7 | 9 | 69 | 1 | 1 | {"I": {"nodes_split": 179, "nodes_total": 946}, "K": {"nodes_split": 3712, "nodes_total": 5733}, "S": {"nodes_split": 6439, "nodes_total": 12083}} |
| 2015-2018 | M_union3_v2 | 7 | 9 | 69 | 1 | 1 | {"I": {"nodes_split": 180, "nodes_total": 956}, "K": {"nodes_split": 3730, "nodes_total": 5768}, "S": {"nodes_split": 6483, "nodes_total": 12154}} |
| 2015-2018 | M_union3_v2_CVRv5 | 7 | 9 | 69 | 1 | 1 | {"I": {"nodes_split": 180, "nodes_total": 956}, "K": {"nodes_split": 3730, "nodes_total": 5768}, "S": {"nodes_split": 6483, "nodes_total": 12154}} |


> 表头：主体=A2-7：E6k 掩码事实同构目标逐值（deriv）｜算子=—｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=—｜子集=E6k mask_facts 同构目标｜单位=计数｜日期=deriv｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-R0-A27-DERIV


| segment | field | PASS |
|---|---|---|
| 2010-2014 | edit_persistence_5d_reversal_share | 174 |
| 2010-2014 | edit_weight_share | 174 |
| 2010-2014 | n_edits_in | 174 |
| 2010-2014 | size_edit_gap_T | 174 |
| 2010-2014 | size_port_delta_T | 174 |
| 2015-2018 | edit_persistence_5d_reversal_share | 174 |
| 2015-2018 | edit_weight_share | 174 |
| 2015-2018 | n_edits_in | 174 |
| 2015-2018 | size_edit_gap_T | 174 |
| 2015-2018 | size_port_delta_T | 174 |


> 表头：主体=附录 C 校准分布（post；诊断，不作门）｜算子=—｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=—｜子集=C1 / Q 平滑族 / Q0 / 旧 K 规则 / 母体｜单位=pct_pt（紧区间）/ 份额｜日期=post｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-R0-CAL-POST


| segment | group | column | n_targets | p50 | p90 | p95 | share_outside_pm3_pct_pt |
|---|---|---|---|---|---|---|---|
| 2019-2023 | C1 | size_port_lo_T_segavg | 594 | -0.1104 | 0.7433 | 0.794 | 0 |
| 2019-2023 | C1 | size_port_hi_T_segavg | 594 | -0.1089 | 0.7442 | 0.7945 | 0 |
| 2019-2023 | C1 | size_port_delta_T | 594 | -0.1096 | 0.7436 | 0.7942 | 0 |
| 2019-2023 | C1 | lv5_mean | 594 | 0.08859 | 0.1199 | 0.1208 |  |
| 2019-2023 | Q_SMOOTH | size_port_lo_T_segavg | 1728 | 0.5128 | 2.238 | 2.653 | 0.03241 |
| 2019-2023 | Q_SMOOTH | size_port_hi_T_segavg | 1728 | 0.5133 | 2.239 | 2.655 | 0.03241 |
| 2019-2023 | Q_SMOOTH | size_port_delta_T | 1728 | 0.5129 | 2.238 | 2.654 | 0.03241 |
| 2019-2023 | Q_SMOOTH | lv5_mean | 1728 | 0.08374 | 0.1194 | 0.1213 |  |
| 2019-2023 | Q0 | size_port_lo_T_segavg | 594 | 0.1409 | 1.323 | 1.389 | 0.01684 |
| 2019-2023 | Q0 | size_port_hi_T_segavg | 594 | 0.141 | 1.325 | 1.39 | 0.01684 |
| 2019-2023 | Q0 | size_port_delta_T | 594 | 0.1409 | 1.324 | 1.389 | 0.01684 |
| 2019-2023 | Q0 | lv5_mean | 594 | 0.08574 | 0.1233 | 0.1262 |  |
| 2019-2023 | OLD_RULE_K0 | size_port_lo_T_segavg | 192 | -0.06132 | 0.8587 | 0.8618 | 0 |
| 2019-2023 | OLD_RULE_K0 | size_port_hi_T_segavg | 192 | -0.0609 | 0.8589 | 0.862 | 0 |
| 2019-2023 | OLD_RULE_K0 | size_port_delta_T | 192 | -0.06106 | 0.8588 | 0.8619 | 0 |
| 2019-2023 | OLD_RULE_K0 | lv5_mean | 192 | 0.08882 | 0.1198 | 0.1201 |  |
| 2024-2026 | C1 | size_port_lo_T_segavg | 594 | -0.1336 | 0.5923 | 0.8147 | 0 |
| 2024-2026 | C1 | size_port_hi_T_segavg | 594 | -0.1335 | 0.5923 | 0.8148 | 0 |
| 2024-2026 | C1 | size_port_delta_T | 594 | -0.1336 | 0.5923 | 0.8148 | 0 |
| 2024-2026 | C1 | lv5_mean | 594 | 0.09391 | 0.1634 | 0.1644 |  |
| 2024-2026 | Q_SMOOTH | size_port_lo_T_segavg | 1728 | 0.1983 | 1.93 | 2.53 | 0.07986 |
| 2024-2026 | Q_SMOOTH | size_port_hi_T_segavg | 1728 | 0.1987 | 1.932 | 2.53 | 0.07986 |
| 2024-2026 | Q_SMOOTH | size_port_delta_T | 1728 | 0.1985 | 1.931 | 2.53 | 0.07986 |
| 2024-2026 | Q_SMOOTH | lv5_mean | 1728 | 0.09111 | 0.1665 | 0.1748 |  |
| 2024-2026 | Q0 | size_port_lo_T_segavg | 594 | -0.004671 | 0.6526 | 0.8146 | 0.1145 |
| 2024-2026 | Q0 | size_port_hi_T_segavg | 594 | -0.004545 | 0.656 | 0.8168 | 0.1145 |
| 2024-2026 | Q0 | size_port_delta_T | 594 | -0.004608 | 0.6545 | 0.8157 | 0.1145 |
| 2024-2026 | Q0 | lv5_mean | 594 | 0.09191 | 0.1778 | 0.1875 |  |
| 2024-2026 | OLD_RULE_K0 | size_port_lo_T_segavg | 192 | -0.1012 | 0.6811 | 0.6913 | 0 |
| 2024-2026 | OLD_RULE_K0 | size_port_hi_T_segavg | 192 | -0.1011 | 0.6813 | 0.6915 | 0 |
| 2024-2026 | OLD_RULE_K0 | size_port_delta_T | 192 | -0.1011 | 0.6812 | 0.6914 | 0 |
| 2024-2026 | OLD_RULE_K0 | lv5_mean | 192 | 0.095 | 0.1623 | 0.1625 |  |
| 2019-2023 | PARENT | lv5_mean | 8 | 0.08766 | 0.09983 | 0.1087 |  |
| 2024-2026 | PARENT | lv5_mean | 8 | 0.1178 | 0.1533 | 0.1568 |  |


> 表头：主体=状态三分位日数与 UNKNOWN（post）｜算子=—｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=—｜子集=Vol3 / Act3（主 / STRICT250）/ Trend3｜单位=日数 / 份额｜日期=post｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-R0-STATE-POST


| segment | variable | definition | unknown_days | low_days | mid_days | high_days |
|---|---|---|---|---|---|---|
| 2019-2023 | Vol3 | MAIN_GE150 | 0 | 507 | 380 | 327 |
| 2019-2023 | Vol3 | STRICT250 | 0 | 507 | 380 | 327 |
| 2019-2023 | Act3 | MAIN_GE150 | 0 | 392 | 425 | 397 |
| 2019-2023 | Act3 | STRICT250 | 0 | 392 | 425 | 397 |
| 2019-2023 | Trend3 | ENDPOINT_MA20_GE16（pool0 单元份额） | 0.03171 | 0.2601 | 0.1959 | 0.5123 |
| 2024-2026 | Vol3 | MAIN_GE150 | 0 | 190 | 150 | 199 |
| 2024-2026 | Vol3 | STRICT250 | 0 | 190 | 150 | 199 |
| 2024-2026 | Act3 | MAIN_GE150 | 0 | 189 | 153 | 197 |
| 2024-2026 | Act3 | STRICT250 | 0 | 189 | 153 | 197 |
| 2024-2026 | Trend3 | ENDPOINT_MA20_GE16（pool0 单元份额） | 0.01357 | 0.2562 | 0.1882 | 0.542 |


> 表头：主体=R-MARK ISK 分区（post）｜算子=—｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=—｜子集=六形态门域｜单位=计数 / 份额｜日期=post｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-R0-RMARKPART-POST


| segment | mother | leaves_per_day_p10 | leaves_per_day_p50 | leaves_per_day_p90 | movable_cell_share_p10 | movable_cell_share_p50 | tree |
|---|---|---|---|---|---|---|---|
| 2019-2023 | A4b | 8 | 9 | 83.6 | 1 | 1 | {"I": {"nodes_split": 281, "nodes_total": 1195}, "K": {"nodes_split": 5983, "nodes_total": 8885}, "S": {"nodes_split": 10659, "nodes_total": 19265}} |
| 2019-2023 | A4b_CVRv5 | 8 | 9 | 83.6 | 1 | 1 | {"I": {"nodes_split": 281, "nodes_total": 1195}, "K": {"nodes_split": 5983, "nodes_total": 8885}, "S": {"nodes_split": 10659, "nodes_total": 19265}} |
| 2019-2023 | M_mean3_v2 | 8 | 9 | 84 | 1 | 1 | {"I": {"nodes_split": 274, "nodes_total": 1185}, "K": {"nodes_split": 5858, "nodes_total": 8686}, "S": {"nodes_split": 10499, "nodes_total": 18894}} |
| 2019-2023 | M_mean3_v2_CVRv5 | 8 | 9 | 84 | 1 | 1 | {"I": {"nodes_split": 274, "nodes_total": 1185}, "K": {"nodes_split": 5858, "nodes_total": 8686}, "S": {"nodes_split": 10499, "nodes_total": 18894}} |
| 2019-2023 | M_union3_v2 | 8 | 9 | 83.6 | 1 | 1 | {"I": {"nodes_split": 281, "nodes_total": 1195}, "K": {"nodes_split": 5983, "nodes_total": 8885}, "S": {"nodes_split": 10659, "nodes_total": 19265}} |
| 2019-2023 | M_union3_v2_CVRv5 | 8 | 9 | 83.6 | 1 | 1 | {"I": {"nodes_split": 281, "nodes_total": 1195}, "K": {"nodes_split": 5983, "nodes_total": 8885}, "S": {"nodes_split": 10659, "nodes_total": 19265}} |
| 2024-2026 | A4b | 8 | 9 | 102 | 1 | 1 | {"I": {"nodes_split": 136, "nodes_total": 520}, "K": {"nodes_split": 3195, "nodes_total": 4258}, "S": {"nodes_split": 5879, "nodes_total": 9949}} |
| 2024-2026 | A4b_CVRv5 | 8 | 9 | 102 | 1 | 1 | {"I": {"nodes_split": 136, "nodes_total": 520}, "K": {"nodes_split": 3195, "nodes_total": 4258}, "S": {"nodes_split": 5879, "nodes_total": 9949}} |
| 2024-2026 | M_mean3_v2 | 8 | 9 | 102 | 1 | 1 | {"I": {"nodes_split": 134, "nodes_total": 510}, "K": {"nodes_split": 3153, "nodes_total": 4196}, "S": {"nodes_split": 5803, "nodes_total": 9812}} |
| 2024-2026 | M_mean3_v2_CVRv5 | 8 | 9 | 102 | 1 | 1 | {"I": {"nodes_split": 134, "nodes_total": 510}, "K": {"nodes_split": 3153, "nodes_total": 4196}, "S": {"nodes_split": 5803, "nodes_total": 9812}} |
| 2024-2026 | M_union3_v2 | 8 | 9 | 102 | 1 | 1 | {"I": {"nodes_split": 136, "nodes_total": 520}, "K": {"nodes_split": 3195, "nodes_total": 4258}, "S": {"nodes_split": 5879, "nodes_total": 9949}} |
| 2024-2026 | M_union3_v2_CVRv5 | 8 | 9 | 102 | 1 | 1 | {"I": {"nodes_split": 136, "nodes_total": 520}, "K": {"nodes_split": 3195, "nodes_total": 4258}, "S": {"nodes_split": 5879, "nodes_total": 9949}} |


> 表头：主体=A2-7：E6k 掩码事实同构目标逐值（post）｜算子=—｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=—｜子集=E6k mask_facts 同构目标｜单位=计数｜日期=post｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-R0-A27-POST


| segment | field | PASS |
|---|---|---|
| 2019-2023 | edit_persistence_5d_reversal_share | 174 |
| 2019-2023 | edit_weight_share | 174 |
| 2019-2023 | n_edits_in | 174 |
| 2019-2023 | size_edit_gap_T | 174 |
| 2019-2023 | size_port_delta_T | 174 |
| 2024-2026 | edit_persistence_5d_reversal_share | 174 |
| 2024-2026 | edit_weight_share | 174 |
| 2024-2026 | n_edits_in | 174 |
| 2024-2026 | size_edit_gap_T | 174 |
| 2024-2026 | size_port_delta_T | 174 |


> 表头：主体=状态 UNKNOWN 日数（主定义 ≥ 150 / STRICT250；Trend3）｜算子=—｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=—｜子集=四段｜单位=日数｜日期=四段｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-R0-UNKNOWN


| segment | variable | definition | unknown_days | defined_days | query_id |
|---|---|---|---|---|---|
| 2010-2014 | Vol3 | MAIN_GE150 | 186 | 1026 | E6L-Q13-a |
| 2010-2014 | Vol3 | STRICT250 | 286 | 926 | E6L-Q13-a |
| 2010-2014 | Act3 | MAIN_GE150 | 202 | 1010 | E6L-Q13-a |
| 2010-2014 | Act3 | STRICT250 | 302 | 910 | E6L-Q13-a |
| 2010-2014 | Trend3 | ENDPOINT_MA20_GE16 | 21 | 1191 | E6L-Q13-a |
| 2015-2018 | Vol3 | MAIN_GE150 | 0 | 975 | E6L-Q13-a |
| 2015-2018 | Vol3 | STRICT250 | 0 | 975 | E6L-Q13-a |
| 2015-2018 | Act3 | MAIN_GE150 | 0 | 975 | E6L-Q13-a |
| 2015-2018 | Act3 | STRICT250 | 0 | 975 | E6L-Q13-a |
| 2015-2018 | Trend3 | ENDPOINT_MA20_GE16 | 0 | 975 | E6L-Q13-a |
| 2019-2023 | Vol3 | MAIN_GE150 | 0 | 1214 | E6L-Q13-a |
| 2019-2023 | Vol3 | STRICT250 | 0 | 1214 | E6L-Q13-a |
| 2019-2023 | Act3 | MAIN_GE150 | 0 | 1214 | E6L-Q13-a |
| 2019-2023 | Act3 | STRICT250 | 0 | 1214 | E6L-Q13-a |
| 2019-2023 | Trend3 | ENDPOINT_MA20_GE16 | 0 | 1214 | E6L-Q13-a |
| 2024-2026 | Vol3 | MAIN_GE150 | 0 | 539 | E6L-Q13-a |
| 2024-2026 | Vol3 | STRICT250 | 0 | 539 | E6L-Q13-a |
| 2024-2026 | Act3 | MAIN_GE150 | 0 | 539 | E6L-Q13-a |
| 2024-2026 | Act3 | STRICT250 | 0 | 539 | E6L-Q13-a |
| 2024-2026 | Trend3 | ENDPOINT_MA20_GE16 | 0 | 539 | E6L-Q13-a |


## 6. 耗时（Stage 0 外推 vs 实际）

> 表头：主体=耗时｜算子=—｜分母=—｜基准=—｜子集=Stage 0 外推 / 随机回执｜单位=小时｜日期=全程｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=—｜资本视图=—｜exposure=不适用｜query_id=E6L-R0-TIMING


| item | value |
|---|---|
| 外推：随机首 1,024 路径两机制 + R-MARK（CPU 小时） | 111 |
| 外推：64 进程墙钟区间（小时） | [1.56, 2.77] |
| 外推：确定性（CPU 小时） | 12 |
| 实际：2010-2014 随机任务 CPU 小时（回执 wall 之和） | 20.5 |
| 实际：2015-2018 随机任务 CPU 小时（回执 wall 之和） | 27.4 |
| 实际：2019-2023 随机任务 CPU 小时（回执 wall 之和） | 51.4 |
| 实际：2024-2026 随机任务 CPU 小时（回执 wall 之和） | 32.3 |


## 7. 源合同、源差异与限制

- `engine_contract.md`（源函数定义处 / 调用处 / 默认值 / 证据）；`source_resolution.md`（20 条源差异与落法，均不改登记语义）；`reports/E6l_limit_register.md`（本轮限制 L 条目）；`reports/E6l_code_change_register.md`（Stage 0 之后 e6l_* 改动逐文件 before / after sha）。

## 8. 执行次序与口径说明

> 表头：主体=MC 增补（首 1,024 路径后按共享路径组 MCSE ≤ .03 规划；回执链逐条；topup_rounds = 该次调用的增补轮数）｜算子=—｜分母=—｜基准=—｜子集=随机共享路径组（机制 × 测量）｜单位=ann_pp｜日期=四段｜H=—｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=—｜资本视图=—｜exposure=不适用｜query_id=E6L-R0-MC


| phase | segment | receipt | written_at | topup_rounds | path_groups | worst_mcse_ann_pp | topped_up_groups |
|---|---|---|---|---|---|---|---|
| deriv | 2010-2014 | mc_done_deriv_2010-2014 | 2026-09-30 15:06:01 | 0 | 44 | 0.0155 | NONE |
| deriv | 2010-2014 | mc_done_deriv_2010-2014_rerun | 2026-09-30 15:10:20 | 0 | 44 | 0.0155 | NONE |
| deriv | 2015-2018 | mc_done_deriv_2015-2018 | 2026-09-30 15:10:20 | 0 | 44 | 0.02302 | NONE |
| post | 2019-2023 | mc_done_post_2019-2023 | 2026-09-30 17:05:26 | 0 | 44 | 0.02117 | NONE |
| post | 2024-2026 | mc_done_post_2024-2026 | 2026-09-30 16:58:31 | 1 | 44 | 0.02984 | CONTENT_COND_ISK_P5\|Q_D3（1024→1536）；CONTENT_COND_ISK_P5\|Q_D5（1024→1536）；CONTENT_COND_ISK_P5\|Q_DEW3（1024→1536）；CONTENT_COND_ISK_P5\|Q_DEW5（1024→1536） |
| post | 2024-2026 | mc_done_post_2024-2026_rerun | 2026-09-30 17:05:24 | 0 | 44 | 0.02984 | CONTENT_COND_ISK_P5\|Q_D3（1024→1536）；CONTENT_COND_ISK_P5\|Q_D5（1024→1536）；CONTENT_COND_ISK_P5\|Q_DEW3（1024→1536）；CONTENT_COND_ISK_P5\|Q_DEW5（1024→1536） |


- seal_post 首次运行（17:05:26）失败：`e6l_seal.planned` 的增补队列仍按 512 路径一片推算，与 16:48 起 64 一片的增补分片不符（报"缺 4"）；改为从 `e6l_topup.TOPUP_CHUNK` 推算后续跑，17:09:09 写入 `seal_post.json`（1,636 个文件，队列 800 行）。v1 失败标记 `logs/chain_main.failed` 保留，续跑标记 `logs/chain_main2.*`。

- 次序：每段先 masks（名单 + 目标层统计，不含收益）→ 推导段 Stage A 掩码事实冻结（A2-7 与 E6k 同构目标逐值）→ Stage B / A1-auto 冻结 → accounts；后段在 `record_B_entry_post_E6l.json` all_pass 之后同一代码版本 masks → accounts → 随机 → seal_post，后段 Stage A 掩码事实在 seal_post 之后汇总（沿 E6k mask_facts_post；不参与任何登记或门）。

- 连续面板（`results/full/continuous/`）只含"记忆按 ticker 跨段接续 + 全日历拼接账户"；源因子与池子没有全程重算（limit L6），continuous − segmented 不分离源预热差。

- bootstrap 比较族另含 CR（真实 − 该机制逐日随机路径均值，plan §7.5；键 = 描述符 × H × 机制，与 `random_daily_<段>.npz` 同键）。

- 推导段配对 MDE80 工具只覆盖确定性配对视图：Q10（真实 − 随机）与 Q14（同资本 MATCH-CAP 视图）的 ⑬ 因此印 UNDEFINED，精度分别见随机 MCSE（`random_refs`）与 bootstrap（`results/full/bootstrap/`）。
