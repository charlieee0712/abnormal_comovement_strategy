# E6k REPORT R0 —— 输入身份、授权、源锚、新算子恒等、掩码 / 风险事实与限制

用途：plan §13.5 R0。全部数字来自 `source_manifest.json`、`stage0/`、`registration/`、`registry/` 与 `diagnostics/control_distributions/`；本文件不含任何登记对象的收益读数。

## 1. 输入身份（三处镜像；全长 sha 见 source_manifest.docs_sha256 与 stage0/local_exec_briefs_hashes.json）

> 表头：主体=本轮输入与结果目录副本｜算子=—｜分母=见表｜基准=—｜子集=docs_sha256｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-DOCS


| file | sha256_16 |
|---|---|
| 00_协议_copy.md | f685e538dd6c5a27 |
| E6j_REPORT_supplement_1_copy.md | 727f4892944e7116 |
| E6j_REVIEW_copy.md | b036617dbe4e96b0 |
| E6j_RULING_copy.md | cb3b8a5f4df910f7 |
| E6j_VERIFY_report_copy.md | 3e6345e16246e64c |
| E6j_delivery_addendum_1_copy.md | 5c662cd56478fdf4 |
| E6k_proposal_copy.md | 65d2b01007ce6130 |
| REVIEW_protocol_copy.md | 0b15019e0867a7a0 |
| brief_appendix_copy.md | 2258b2c66e794614 |
| brief_copy.md | 8be4df3da41f28f8 |
| PLAN_COPY.md | 1f9e949c238b9125 |
| engine_contract.md | 6f8cd4c61e76bc50 |
| source_resolution.md | 80ba7665d162d64c |


> 表头：主体=47 环境与生成器｜算子=—｜分母=见表｜基准=—｜子集=source_manifest.env｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-ENV


| item | value |
|---|---|
| python | 3.10.13 |
| numpy | 1.26.1 |
| pandas | 2.2.3 |
| scipy | 1.11.3 |
| numba | 0.58.1 |
| polars | 1.44.2 |
| polars_install | pip --target 私有目录（不改共享 conda 环境；e6k_boot 追加 sys.path 末尾） |
| permutation_generator | splitmix64x2-counter(key^block*C1^ticker*C2)>>11 * 2^-53; key=blake2b-64(canonical_json) |
| bootstrap_generator | blake2b-128(canonical_json(key)) -> SeedSequence -> PCG64 |
| git_head | 82b6cf397c83 |


> 表头：主体=随机量 → 生成器 → 回执字段（W18；E6j E05 改法）｜算子=—｜分母=见表｜基准=—｜子集=全部随机量｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-GEN


| random_quantity | generator | receipt_field |
|---|---|---|
| LEGACY_POLICY_RANDOM（E6j R-MATCH-SRC 复现） | splitmix64 计数器 u(键, 绝对交易日, ticker)；键 = blake2b-64(canonical_json)：E6j.P / E6j.B 命名空间（E6j 原键） | run_rand_* generator |
| NEW_COND_ISK_P5 / NEW_COND_ISK_IID / EIGHT_SUBSET_* | 同一 splitmix64 计数器；键 = blake2b-64(canonical_json(E6k.NEW, 测量, 分区, 块长, path))；块 = 绝对交易日 // 块长 | run_rand_* generator |
| bootstrap（段内分层 stationary） | blake2b-128(canonical_json(E6k, bootstrap, L, 段)) → SeedSequence → PCG64；e6j_stats.stationary_indices | bootstrap_full generator |
| 衰减场景时间块 | blake2b-128(canonical_json(E6k, decay, L, 段)) → SeedSequence → PCG64 | decay_scenarios |
| profile 置换（只测时，临时目录，不入结果） | default_rng(blake2b(E6k.profile, 段, 任务)) | — |


## 2. 授权与读数前登记

> 表头：主体=授权 / 登记 / 封存文件｜算子=—｜分母=见表｜基准=—｜子集=registration/｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-AUTH


| file | present | sha256_16 |
|---|---|---|
| registration/record_B_mode_A.json | True | 2a04112058198934 |
| registration/record_B_approved_E6k.json | True | d0a96601a09c4673 |
| registration/record_B_preauthorized_E6k.json | False |  |
| registration/record_B_conditions_receipt_E6k.json | True | fc84b6a9b6358243 |
| registration/executor_supplements_E6k.json | True | bf937d8490b4dfdf |
| registration/executor_supplements_E6k_amend_1.json | True | a252027038cdec64 |
| registration/policy_profiles_E6k.json | True | 82c1c8a0623c823b |
| registration/policy_profiles_E6k_amend_1.json | True | 1be280274a566882 |
| registration/policy_profiles_E6k_amend_2.json | True | 4638cca64134dc24 |
| registration/preregistration_amend_20260929.md | True | 6a7820853e6ccdfe |
| registration/P_package_manifest_E6k.json | True | 77f24f0ead89678c |
| registration/B_package_manifest_E6k.json | True | 436b71e780b90355 |
| registration/a1_auto_E6k.json | True | 897afd49866a3219 |
| registration/a1_auto_masks_E6k.json | True | 42c31894417c112a |
| registration/a1_auto_masks_post_E6k.json | True | 6124be9862e13785 |
| registration/a1_auto_draft_E6k.json | True | c0d8cbb7d8dd3ae1 |
| registration/seal_deriv.json | True | e065ffe0d4bcb62f |
| registration/seal_post.json | True | e366a2b58cb682d7 |


- 授权方式：用户转交消息不含"B" → 方式 A；推导两段封存后用户一句话：「stop point不用特意停下来汇报了 继续推进就好」（2026-09-29；`record_B_approved_E6k.json` 写于 2026-09-29 07:28:09，记录背景见其 context_note）→ 条件回执 all_pass → 两后段同版本计算。E6j REVIEW §11 经济裁定未给 → `policy_provisional = true`。

## 3. Stage 0 六类（source_manifest.stage0；FAILED 由同名 _rerun 覆盖）

> 表头：主体=Stage 0 六类回执｜算子=—｜分母=见表｜基准=—｜子集=source_manifest.stage0｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-STAGE0


| category | ok | receipts |
|---|---|---|
| 1_identity | True | stage0_c1_identity_rerun=SUCCEEDED |
| 2_source | True | stage0_c2_source_prod=SUCCEEDED；stage0_c2_source_engine_2010-2014=SUCCEEDED；stage0_c2_source_engine_2015-2018=SUCCEEDED；stage0_c2_source_engine_2019-2023=SUCCEEDED；stage0_c2_source_engine_2024-2026=SUCCEEDED |
| 3_new_operators_deriv | True | stage0_c3_ops_2010-2014=SUCCEEDED；stage0_c3_ops_2015-2018=SUCCEEDED |
| 4_data_clock | True | stage0_c4_data_2010-2014=SUCCEEDED；stage0_c4_data_2015-2018=SUCCEEDED；stage0_c4_data_2019-2023=SUCCEEDED；stage0_c4_data_2024-2026=SUCCEEDED |
| 5_random_state | True | stage0_c5_random=SUCCEEDED |
| 6_output_resources | True | stage0_c6_output=SUCCEEDED |


> 表头：主体=Stage 0 c2_source 逐项状态计数｜算子=—｜分母=见表｜基准=—｜子集=stage0/c2_source/*.csv｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-S0-C2SOURCE


| check_id | PASS |
|---|---|
| A2-1 | 7 |
| A2-2 | 180 |
| A2-3 | 24 |
| A2-4 | 768 |
| A2-5 | 480 |
| A2-7 | 24 |


> 表头：主体=Stage 0 c3_ops 逐项状态计数｜算子=—｜分母=见表｜基准=—｜子集=stage0/c3_ops/ops_identity_*.csv｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-S0-C3OPS


| file_segment | check_id | INFO | PASS |
|---|---|---|---|
| 2010-2014 | A3-1 | 64 | 64 |
| 2010-2014 | A3-10 | 0 | 16 |
| 2010-2014 | A3-11 | 0 | 2 |
| 2010-2014 | A3-2 | 0 | 96 |
| 2010-2014 | A3-3 | 0 | 192 |
| 2010-2014 | A3-4 | 64 | 97 |
| 2010-2014 | A3-5 | 0 | 224 |
| 2010-2014 | A3-6 | 0 | 136 |
| 2010-2014 | A3-7 | 24 | 24 |
| 2010-2014 | A3-8 | 0 | 24 |
| 2010-2014 | A3-9 | 16 | 16 |
| 2015-2018 | A3-1 | 64 | 64 |
| 2015-2018 | A3-10 | 0 | 16 |
| 2015-2018 | A3-11 | 0 | 2 |
| 2015-2018 | A3-2 | 0 | 96 |
| 2015-2018 | A3-3 | 0 | 192 |
| 2015-2018 | A3-4 | 64 | 97 |
| 2015-2018 | A3-5 | 0 | 224 |
| 2015-2018 | A3-6 | 0 | 136 |
| 2015-2018 | A3-7 | 24 | 24 |
| 2015-2018 | A3-8 | 0 | 24 |
| 2015-2018 | A3-9 | 16 | 16 |
| 2019-2023 | A3-1 | 64 | 64 |
| 2019-2023 | A3-10 | 0 | 16 |
| 2019-2023 | A3-11 | 0 | 2 |
| 2019-2023 | A3-2 | 0 | 96 |
| 2019-2023 | A3-3 | 0 | 192 |
| 2019-2023 | A3-4 | 64 | 97 |
| 2019-2023 | A3-5 | 0 | 224 |
| 2019-2023 | A3-6 | 0 | 136 |
| 2019-2023 | A3-7 | 24 | 24 |
| 2019-2023 | A3-8 | 0 | 24 |
| 2019-2023 | A3-9 | 16 | 16 |
| 2024-2026 | A3-1 | 64 | 64 |
| 2024-2026 | A3-10 | 0 | 16 |
| 2024-2026 | A3-11 | 0 | 2 |
| 2024-2026 | A3-2 | 0 | 96 |
| 2024-2026 | A3-3 | 0 | 192 |
| 2024-2026 | A3-4 | 64 | 97 |
| 2024-2026 | A3-5 | 0 | 224 |
| 2024-2026 | A3-6 | 0 | 136 |
| 2024-2026 | A3-7 | 24 | 24 |
| 2024-2026 | A3-8 | 0 | 24 |
| 2024-2026 | A3-9 | 16 | 16 |


> 表头：主体=Stage 0 c4_data 逐项状态计数｜算子=—｜分母=见表｜基准=—｜子集=stage0/c4_data/*.csv｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-S0-C4DATA


| check_id | INFO | PASS |
|---|---|---|
| A4-1 | 4 | 8 |
| A4-2 | 8 | 4 |
| A4-3 | 16 | 0 |
| A4-4 | 0 | 8 |
| A4-5 | 4 | 8 |


> 表头：主体=Stage 0 c5_random 逐项状态计数｜算子=—｜分母=见表｜基准=—｜子集=stage0/c5_random/random_checks.csv｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-S0-C5RANDOM


| check_id | INFO | PASS |
|---|---|---|
| A2-6 | 0 | 2 |
| A5-1 | 0 | 1 |
| A5-2 | 0 | 5 |
| A5-3 | 0 | 17 |
| A5-4 | 1 | 8 |
| A5-5 | 0 | 2 |
| A5-6 | 0 | 1 |


> 表头：主体=Stage 0 c6_output 逐项状态计数｜算子=—｜分母=见表｜基准=—｜子集=stage0/c6_output/output_checks.csv｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-S0-C6OUTPUT


| check_id | INFO | PASS |
|---|---|---|
| A3-12 | 0 | 1 |
| A6-1 | 1 | 0 |
| A6-2 | 0 | 4 |
| A6-3 | 0 | 1 |
| A6-4 | 0 | 1 |
| A6-5 | 0 | 1 |
| A6-6 | 0 | 3 |


> 表头：主体=Stage 0 c1_identity 逐项状态计数｜算子=—｜分母=见表｜基准=—｜子集=stage0/c1_identity_rerun/identity_checks.csv｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-S0-C1IDENTITY


| check_id | INFO | PASS |
|---|---|---|
| A1-1 | 0 | 11 |
| A1-2 | 13 | 10 |
| A1-3 | 0 | 1 |
| A1-4 | 179 | 38 |
| A1-5 | 0 | 14 |
| A1-6 | 0 | 2 |


## 4. A0 与 A1-auto

> 表头：主体=A0 计数（每段）｜算子=—｜分母=见表｜基准=—｜子集=a0_manifest_E6k.json｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-A0


| item | value |
|---|---|
| raw_id_count | 39142 |
| accessory_INC | 72 |
| band_dose_controls | 288 |
| cs_children | 1800 |
| cs_parents | 176 |
| block_counts | {"CORE": 9600, "OWN": 3840, "REPAIR": 7680, "LAYER": 7680, "BAND": 5760, "BAND_COMPARATOR": 2016, "HG_ONLY": 360, "TREFIT": 960, "POST2": 360, "RAR": 720, "PARENT": 160, "SM_ANCHOR": 6} |
| measurement_count | 10 |
| measurements | ["C1", "K0", "M", "Q", "RARPRE20_LT", "RARPRE20_SE", "RARPRE60_LT", "RARPRE60_SE", "S", "SM"] |
| operator_count | 40 |
| operators | ["HG_ONLY10", "HG_ONLY15", "HG_ONLY5", "INC05", "INC1", "INC1_HG10", "INC1_HG15", "INC1_HG5", "INC1_PM10", "INC1_PM15", "INC1_PM5", "INC1_SA10", "INC1_SA15", "INC1_SA5", "LX_ISK_01", "LX_ISK_10", "LX_SIZE3_01", "LX_SIZE3_10", "NATIVE", "NATIVE_HG10", "NATIVE_HG15", "NATIVE_HG5", "NATIVE_PM10", "NATIVE_PM15", "NATIVE_PM5", "NATIVE_SA10", "NATIVE_SA15", "NATIVE_SA5", "PARENT", "POST2_INCREMENT", "RP0p5", "RP1", "RP3", "RPINF", "SZL3", "SZL3_OWN", "SZL5", "SZL5_OWN", "TREFIT0", "TREFIT0p5"] |
| target_count | 2222 |
| primary144 | 144 |
| c1_hi | 4 |
| sm_anchor | 6 |
| mothers | 8 |
| exposed_count | 2806 |
| new_operator_count | 36336 |
| policy_count | 956 |
| random_objects | 956 |
| random_units | 2252 |
| shadow_accounts | 160 |
| bootstrap_comparisons | 112926 |
| exact_target_alias | A1-auto 由推导段掩码 hash 现算（本表只列结构别名） |
| account_alias | 同 H / lag / 费用 / A / 基准 / 状态 / 末端才算账户别名（plan §13.4）；A0 不预设 |


> 表头：主体=A1-auto（读数前）｜算子=—｜分母=见表｜基准=—｜子集=a1_auto_E6k.json｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-A1PRE


| item | sub | what | status |
|---|---|---|---|
| 1 |  | 描述符 = 39,142 / 段，与 plan §16.3 compile_design 逐元组、块集合相等 | PASS |
| 1 |  | 任务 → 对象：每个描述符恰属一个任务 | PASS |
| 1 |  | 问题 → 对象：对象全在登记表内；每条 query 至少一个对象 | PASS |
| 1 |  | 暴露台账覆盖全部描述符 | PASS |
| 2 |  | 方向角色在词表内（main / competitor / both_registered；E6j #65 补 both_registered） | PASS |
| 2 |  | 测量方向：S / M / Q / RARPRE = low_bad（lo），C1 = high_bad（hi） | PASS |
| 2 |  | 方向论证：engine_contract §3 / source_resolution #5 / 补充 X05（RARPRE 与 S 同向；Q 价稳高 = 好） | PASS |
| 3 |  | BAND / BAND_COMPARATOR / HG_ONLY 只在生产六形态 | PASS |
| 3 |  | TREFIT / POST2 只在 A4b 两形态 | PASS |
| 3 |  | RAR 只在 A4b_CVRv5（= R1）/ R2 / A06；R1 不另算 | PASS |
| 3 |  | POST2 测量 ∈ {S, Q, C1}（C1 = 同算子主动控制） | PASS |
| 4 |  | 锁定值（α / H / b / τ / γ / g / δ / MC / bootstrap / HAC / mean b÷3） | PASS |
| 4 |  | 政策常数与 E6j 口径一致（δ .10、MC_Z 2、MC_TARGET .03、SIGN_TOL 1e−9） | PASS |
| 5 |  | 源事实表（brief §0.1 ★ 项）逐条有 Stage 0 证据 | PASS |
| 6 |  | Stage 0 六类全 PASS（source_manifest.stage0_all_pass） | PASS |
| 13.2 | ① | 参数完整性 / 不存在收益预筛：编译器只读登记规则，网格全枚举（A0 不读账户） | PASS |
| 13.2 | ② | 对象 / 方向 / 母体映射：任务 = 母体 × 测量，SM 双分量、K0 = PARENT / HG_ONLY | PASS |
| 13.2 | ③ | 支持 / 状态 / 权限：方式 A 文件存在；后段守卫 post_gate；HG 段首空状态（X09）；COMMON_SUPPORT 定义（X16） | PASS |
| 13.2 | ④ | 公式与端点：Stage 0 第 3 类恒等锚全 PASS（两推导段） | PASS |
| 13.2 | ⑤ | 主对象与政策版本：144 唯一存在；policy_profiles 五列（三登记 + 两 print-only） | PASS |
| 13.2 | ⑥ | Q 原文与 query 模板非空：18 卡原文 = PLAN_COPY 对应行；每卡 queries 非空（E6j #73） | PASS |
| 13.2 | ⑦ | P / B 派生闭包与登记 sha 一致（两包清单记录的 registry 文件 sha = 当前） | PASS |


## 5. 掩码事实（附录 B；推导段；只作描述与预冻结回退 / 不适用标注，不生成阈值、不挑臂）

> 表头：主体=掩码事实中位（按算子族；目标 × 段）｜算子=—｜分母=见表｜基准=—｜子集=mask_facts_deriv_E6k.csv｜单位=名数 / 份额 / 百分位点｜日期=推导两段｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-MASK


| family | targets | n_edits_in | edit_weight_share | size_edit_gap_T_signed | size_port_delta_T_signed | small30_share_delta | size_unknown_weight | overlap_with_native |
|---|---|---|---|---|---|---|---|---|
| DOSE_INC1_HG | 24 | 2.366 | 0.06401 | -7.781 | -0.4348 | 0.009774 | 7.673e-05 | 0.7899 |
| DOSE_INC1_PM | 24 | 0.7442 | 0.01585 | -7.608 | -0.07465 | 0.001512 | 7.719e-05 | 0.8595 |
| DOSE_INC1_SA | 24 | 2.212 | 0.06271 | -8.055 | -0.4319 | 0.009648 | 7.695e-05 | 0.7968 |
| DOSE_NATIVE_HG | 24 | 2.584 | 0.07008 | -10.75 | -0.8575 | 0.01658 | 8.1e-05 | 0.9996 |
| DOSE_NATIVE_PM | 24 | 0.8272 | 0.01818 | -13.18 | -0.1149 | 0.002098 | 8.084e-05 | 0.9321 |
| DOSE_NATIVE_SA | 24 | 2.437 | 0.06907 | -10.93 | -0.8321 | 0.0161 | 8.084e-05 | 0.9935 |
| HG_ONLY | 36 | 1.748 | 0.03845 | -5.528 | -0.1099 | 0.001326 | 7.696e-05 |  |
| INC | 384 | 2.986 | 0.05801 | -3.954 | -0.143 | 0.001312 | 8.054e-05 | 0.875 |
| INC1_HG | 216 | 3.696 | 0.07527 | -6.376 | -0.3571 | 0.004902 | 7.687e-05 | 0.577 |
| INC1_PM | 216 | 1.001 | 0.02047 | -6.856 | -0.07323 | 0.001199 | 7.7e-05 | 0.9321 |
| INC1_SA | 216 | 2.62 | 0.05441 | -5.741 | -0.1922 | 0.002857 | 8.053e-05 | 0.8321 |
| INC_DOSE | 96 | 2.768 | 0.05873 | -7.611 | -0.3412 | 0.004632 | 7.72e-05 | 0.9924 |
| INC_SUPPORT | 48 | 3.074 | 0.06635 | -7.69 | -0.3703 | 0.005683 | 8.106e-05 | 0.999 |
| LX_ISK_ | 384 | 1.165 | 0.02822 | -1.774 | -0.01572 | 0.0001904 | 8.116e-05 | 0.8339 |
| LX_SIZE3_ | 384 | 2.159 | 0.04491 | -1.773 | -0.08103 | 0.0009011 | 8.116e-05 | 0.7615 |
| NATIVE | 276 | 3.65 | 0.06961 | -3.872 | -0.2787 | 0.004161 | 8.096e-05 |  |
| NATIVE_HG | 216 | 4.108 | 0.08326 | -7.204 | -0.5581 | 0.008431 | 8.114e-05 | 0.5912 |
| NATIVE_PM | 216 | 1.161 | 0.025 | -11.28 | -0.1512 | 0.002211 | 8.116e-05 | 1 |
| NATIVE_SA | 216 | 2.896 | 0.06523 | -6.407 | -0.4037 | 0.005859 | 8.339e-05 | 0.9726 |
| PARENT | 16 |  |  |  |  | 0 | 7.717e-05 |  |
| POST2_INCREMENT | 36 | 3.466 | 0.08732 | 4.083 | 0.3523 | -0.01074 | 3.954e-05 | 0.1488 |
| RP | 384 | 0.4513 | 0.008145 | -2.932 | -0.01702 | 0.0002936 | 7.717e-05 | 1 |
| RP0p | 192 | 0.2732 | 0.004943 | -1.102 | -0.00258 | 7.797e-05 | 7.717e-05 | 1 |
| RPINF | 192 | 0.5135 | 0.009104 | -3.552 | -0.0379 | 0.0006539 | 7.717e-05 | 1 |
| SZL | 384 | 3.69 | 0.06926 | 8.25 | 0.4708 | -0.005853 | 8.094e-05 | 0.7348 |
| SZL3_OWN | 192 | 1.968 | 0.04605 | 21.73 | 0.8609 | -0.008737 | 7.684e-05 | 0.3344 |
| SZL5_OWN | 192 | 2.024 | 0.04609 | 22.6 | 0.885 | -0.007692 | 8.489e-05 | 0.3325 |
| TREFIT | 48 | 2.177 | 0.05088 | -11.2 | -0.5323 | 0.008091 | 4.004e-05 | 0.9442 |
| TREFIT0p | 48 | 2.481 | 0.05804 | -11.17 | -0.6989 | 0.01085 | 3.966e-05 | 0.9732 |


> 表头：主体=预冻结回退 / 不适用标注触发计数｜算子=—｜分母=见表｜基准=—｜子集=mask_facts_deriv_E6k.csv｜单位=计数｜日期=推导两段｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-FLAGS


| flag | targets |
|---|---|
| NO_DOSE_MATCH_DAYS | 96 |
| COEF_INTERP_UNAVAILABLE | 48 |
| NO_EDITS_EQUIV_PARENT | 20 |


> 表头：主体=回退域（K 腿有效域内：新测量缺 / size 缺份额）｜算子=—｜分母=见表｜基准=—｜子集=FALLBACK_DOMAIN｜单位=份额｜日期=推导两段｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-FBDOM


| segment | meas | mother | fallback_native_kf_missing | fallback_szl_inc_z_missing |
|---|---|---|---|---|
| 2010-2014 | S | A4b | 0.002967 | 5.384e-05 |
| 2010-2014 | M | A4b | 0.002353 | 5.384e-05 |
| 2010-2014 | Q | A4b | 0 | 5.384e-05 |
| 2010-2014 | C1 | A4b | 0 | 5.384e-05 |
| 2010-2014 | S | A4b_CVRv5 | 0.002967 | 5.384e-05 |
| 2010-2014 | M | A4b_CVRv5 | 0.002353 | 5.384e-05 |
| 2010-2014 | Q | A4b_CVRv5 | 0 | 5.384e-05 |
| 2010-2014 | C1 | A4b_CVRv5 | 0 | 5.384e-05 |
| 2010-2014 | S | M_mean3_v2 | 0.002967 | 5.384e-05 |
| 2010-2014 | M | M_mean3_v2 | 0.002353 | 5.384e-05 |
| 2010-2014 | Q | M_mean3_v2 | 0 | 5.384e-05 |
| 2010-2014 | C1 | M_mean3_v2 | 0 | 5.384e-05 |
| 2010-2014 | S | M_mean3_v2_CVRv5 | 0.002967 | 5.384e-05 |
| 2010-2014 | M | M_mean3_v2_CVRv5 | 0.002353 | 5.384e-05 |
| 2010-2014 | Q | M_mean3_v2_CVRv5 | 0 | 5.384e-05 |
| 2010-2014 | C1 | M_mean3_v2_CVRv5 | 0 | 5.384e-05 |
| 2010-2014 | S | M_union3_v2 | 0.002967 | 5.384e-05 |
| 2010-2014 | M | M_union3_v2 | 0.002353 | 5.384e-05 |
| 2010-2014 | Q | M_union3_v2 | 0 | 5.384e-05 |
| 2010-2014 | C1 | M_union3_v2 | 0 | 5.384e-05 |
| 2010-2014 | S | M_union3_v2_CVRv5 | 0.002967 | 5.384e-05 |
| 2010-2014 | M | M_union3_v2_CVRv5 | 0.002353 | 5.384e-05 |
| 2010-2014 | Q | M_union3_v2_CVRv5 | 0 | 5.384e-05 |
| 2010-2014 | C1 | M_union3_v2_CVRv5 | 0 | 5.384e-05 |
| 2010-2014 | S | R2 | 0.002967 | 5.384e-05 |
| 2010-2014 | M | R2 | 0.002353 | 5.384e-05 |
| 2010-2014 | Q | R2 | 0 | 5.384e-05 |
| 2010-2014 | C1 | R2 | 0 | 5.384e-05 |
| 2010-2014 | S | A06 | 0.002967 | 5.384e-05 |
| 2010-2014 | M | A06 | 0.002353 | 5.384e-05 |
| 2010-2014 | Q | A06 | 0 | 5.384e-05 |
| 2010-2014 | C1 | A06 | 0 | 5.384e-05 |
| 2015-2018 | S | A4b | 0.006019 | 0.0001218 |
| 2015-2018 | M | A4b | 0.00489 | 0.0001218 |
| 2015-2018 | Q | A4b | 0 | 0.0001218 |
| 2015-2018 | C1 | A4b | 0 | 0.0001218 |
| 2015-2018 | S | A4b_CVRv5 | 0.006019 | 0.0001218 |
| 2015-2018 | M | A4b_CVRv5 | 0.00489 | 0.0001218 |
| 2015-2018 | Q | A4b_CVRv5 | 0 | 0.0001218 |
| 2015-2018 | C1 | A4b_CVRv5 | 0 | 0.0001218 |
| 2015-2018 | S | M_mean3_v2 | 0.006019 | 0.0001218 |
| 2015-2018 | M | M_mean3_v2 | 0.00489 | 0.0001218 |
| 2015-2018 | Q | M_mean3_v2 | 0 | 0.0001218 |
| 2015-2018 | C1 | M_mean3_v2 | 0 | 0.0001218 |
| 2015-2018 | S | M_mean3_v2_CVRv5 | 0.006019 | 0.0001218 |
| 2015-2018 | M | M_mean3_v2_CVRv5 | 0.00489 | 0.0001218 |
| 2015-2018 | Q | M_mean3_v2_CVRv5 | 0 | 0.0001218 |
| 2015-2018 | C1 | M_mean3_v2_CVRv5 | 0 | 0.0001218 |
| 2015-2018 | S | M_union3_v2 | 0.006019 | 0.0001218 |
| 2015-2018 | M | M_union3_v2 | 0.00489 | 0.0001218 |
| 2015-2018 | Q | M_union3_v2 | 0 | 0.0001218 |
| 2015-2018 | C1 | M_union3_v2 | 0 | 0.0001218 |
| 2015-2018 | S | M_union3_v2_CVRv5 | 0.006019 | 0.0001218 |
| 2015-2018 | M | M_union3_v2_CVRv5 | 0.00489 | 0.0001218 |
| 2015-2018 | Q | M_union3_v2_CVRv5 | 0 | 0.0001218 |
| 2015-2018 | C1 | M_union3_v2_CVRv5 | 0 | 0.0001218 |
| 2015-2018 | S | R2 | 0.006019 | 0.0001218 |
| 2015-2018 | M | R2 | 0.00489 | 0.0001218 |
| 2015-2018 | Q | R2 | 0 | 0.0001218 |
| 2015-2018 | C1 | R2 | 0 | 0.0001218 |
| 2015-2018 | S | A06 | 0.006019 | 0.0001218 |
| 2015-2018 | M | A06 | 0.00489 | 0.0001218 |
| 2015-2018 | Q | A06 | 0 | 0.0001218 |
| 2015-2018 | C1 | A06 | 0 | 0.0001218 |


> 表头：主体=掩码事实中位（按算子族；目标 × 段）｜算子=—｜分母=见表｜基准=—｜子集=mask_facts_post_E6k.csv｜单位=名数 / 份额 / 百分位点｜日期=2019-01-02..2026-03-27（两后段；X04 授权后补算）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-MASK-POST


| family | targets | n_edits_in | edit_weight_share | size_edit_gap_T_signed | size_port_delta_T_signed | small30_share_delta | size_unknown_weight | overlap_with_native |
|---|---|---|---|---|---|---|---|---|
| DOSE_INC1_HG | 24 | 5.644 | 0.06975 | -9.793 | -0.5679 | 0.009852 | 1.085e-05 | 0.816 |
| DOSE_INC1_PM | 24 | 1.829 | 0.0196 | -11.69 | -0.09443 | 0.001468 | 1.106e-05 | 0.8947 |
| DOSE_INC1_SA | 24 | 5.228 | 0.06837 | -10.48 | -0.5549 | 0.0095 | 1.085e-05 | 0.8305 |
| DOSE_NATIVE_HG | 24 | 5.894 | 0.07347 | -9.885 | -0.7032 | 0.0107 | 1.085e-05 | 0.9997 |
| DOSE_NATIVE_PM | 24 | 1.895 | 0.01874 | -11.15 | -0.08567 | 0.001117 | 1.106e-05 | 0.9434 |
| DOSE_NATIVE_SA | 24 | 5.234 | 0.0711 | -10.26 | -0.7023 | 0.0104 | 1.092e-05 | 0.9946 |
| HG_ONLY | 36 | 3.668 | 0.03664 | -8.025 | -0.09154 | 0.0009159 | 4.299e-05 |  |
| INC | 384 | 6.622 | 0.06126 | -3.43 | -0.1059 | 0.0008682 | 4.225e-05 | 0.8819 |
| INC1_HG | 216 | 8.098 | 0.07675 | -9.04 | -0.3847 | 0.004292 | 3.19e-05 | 0.6238 |
| INC1_PM | 216 | 2.394 | 0.02401 | -10.51 | -0.1112 | 0.001135 | 3.263e-05 | 0.9388 |
| INC1_SA | 216 | 5.87 | 0.05731 | -8.491 | -0.2634 | 0.003155 | 3.197e-05 | 0.8412 |
| INC_DOSE | 96 | 6.168 | 0.06167 | -8.868 | -0.1533 | 0.002611 | 4.295e-05 | 0.9958 |
| INC_SUPPORT | 48 | 6.68 | 0.06801 | -8.141 | -0.1501 | 0.00283 | 4.286e-05 | 0.9993 |
| LX_ISK_ | 384 | 3.24 | 0.03164 | -0.9108 | -0.008089 | 0.0001776 | 3.479e-05 | 0.8031 |
| LX_SIZE3_ | 384 | 4.554 | 0.04324 | -0.1331 | -0.01436 | 0.0005922 | 3.479e-05 | 0.7885 |
| NATIVE | 276 | 7.838 | 0.07084 | -0.07995 | -0.06174 | 0.001456 | 3.142e-05 |  |
| NATIVE_HG | 216 | 8.965 | 0.08407 | -8.977 | -0.2845 | 0.005299 | 3.185e-05 | 0.6232 |
| NATIVE_PM | 216 | 2.59 | 0.02798 | -11.19 | -0.07256 | 0.001248 | 3.242e-05 | 1 |
| NATIVE_SA | 216 | 6.358 | 0.06684 | -8.131 | -0.1561 | 0.003831 | 3.185e-05 | 0.9809 |
| PARENT | 16 |  |  |  |  | 0 | 4.319e-05 |  |
| POST2_INCREMENT | 36 | 7.543 | 0.08956 | 8.376 | 0.4546 | -0.01101 | 1.08e-05 | 0.1112 |
| RP | 384 | 1.699 | 0.01478 | -1.135 | -0.01689 | 0.0004058 | 4.319e-05 | 1 |
| RP0p | 192 | 1.417 | 0.01193 | -0.7898 | -0.003925 | 0.0001778 | 4.319e-05 | 1 |
| RPINF | 192 | 1.753 | 0.01553 | -1.576 | -0.0276 | 0.0005367 | 4.319e-05 | 1 |
| SZL | 384 | 7.981 | 0.07173 | 11.72 | 0.6072 | -0.008048 | 4.509e-05 | 0.8165 |
| SZL3_OWN | 192 | 4.508 | 0.04672 | 26.1 | 1.099 | -0.01359 | 4.27e-05 | 0.3499 |
| SZL5_OWN | 192 | 4.639 | 0.04754 | 26.69 | 1.143 | -0.01219 | 4.305e-05 | 0.3217 |
| TREFIT | 48 | 4.887 | 0.05314 | -10.95 | -0.5157 | 0.00768 | 1.056e-05 | 0.9406 |
| TREFIT0p | 48 | 5.281 | 0.056 | -12.93 | -0.5531 | 0.008585 | 9.779e-06 | 0.9748 |


> 表头：主体=预冻结回退 / 不适用标注触发计数｜算子=—｜分母=见表｜基准=—｜子集=mask_facts_post_E6k.csv｜单位=计数｜日期=2019-01-02..2026-03-27（两后段；X04 授权后补算）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-FLAGS-POST


| flag | targets |
|---|---|
| NO_DOSE_MATCH_DAYS | 96 |
| COEF_INTERP_UNAVAILABLE | 48 |
| NO_EDITS_EQUIV_PARENT | 16 |


> 表头：主体=回退域（K 腿有效域内：新测量缺 / size 缺份额）｜算子=—｜分母=见表｜基准=—｜子集=FALLBACK_DOMAIN｜单位=份额｜日期=2019-01-02..2026-03-27（两后段；X04 授权后补算）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-FBDOM-POST


| segment | meas | mother | fallback_native_kf_missing | fallback_szl_inc_z_missing |
|---|---|---|---|---|
| 2019-2023 | S | A4b | 0.000363 | 8.842e-05 |
| 2019-2023 | M | A4b | 0.0003095 | 8.842e-05 |
| 2019-2023 | Q | A4b | 0 | 8.842e-05 |
| 2019-2023 | C1 | A4b | 0 | 8.842e-05 |
| 2019-2023 | S | A4b_CVRv5 | 0.000363 | 8.842e-05 |
| 2019-2023 | M | A4b_CVRv5 | 0.0003095 | 8.842e-05 |
| 2019-2023 | Q | A4b_CVRv5 | 0 | 8.842e-05 |
| 2019-2023 | C1 | A4b_CVRv5 | 0 | 8.842e-05 |
| 2019-2023 | S | M_mean3_v2 | 0.000363 | 8.842e-05 |
| 2019-2023 | M | M_mean3_v2 | 0.0003095 | 8.842e-05 |
| 2019-2023 | Q | M_mean3_v2 | 0 | 8.842e-05 |
| 2019-2023 | C1 | M_mean3_v2 | 0 | 8.842e-05 |
| 2019-2023 | S | M_mean3_v2_CVRv5 | 0.000363 | 8.842e-05 |
| 2019-2023 | M | M_mean3_v2_CVRv5 | 0.0003095 | 8.842e-05 |
| 2019-2023 | Q | M_mean3_v2_CVRv5 | 0 | 8.842e-05 |
| 2019-2023 | C1 | M_mean3_v2_CVRv5 | 0 | 8.842e-05 |
| 2019-2023 | S | M_union3_v2 | 0.000363 | 8.842e-05 |
| 2019-2023 | M | M_union3_v2 | 0.0003095 | 8.842e-05 |
| 2019-2023 | Q | M_union3_v2 | 0 | 8.842e-05 |
| 2019-2023 | C1 | M_union3_v2 | 0 | 8.842e-05 |
| 2019-2023 | S | M_union3_v2_CVRv5 | 0.000363 | 8.842e-05 |
| 2019-2023 | M | M_union3_v2_CVRv5 | 0.0003095 | 8.842e-05 |
| 2019-2023 | Q | M_union3_v2_CVRv5 | 0 | 8.842e-05 |
| 2019-2023 | C1 | M_union3_v2_CVRv5 | 0 | 8.842e-05 |
| 2019-2023 | S | R2 | 0.000363 | 8.842e-05 |
| 2019-2023 | M | R2 | 0.0003095 | 8.842e-05 |
| 2019-2023 | Q | R2 | 0 | 8.842e-05 |
| 2019-2023 | C1 | R2 | 0 | 8.842e-05 |
| 2019-2023 | S | A06 | 0.000363 | 8.842e-05 |
| 2019-2023 | M | A06 | 0.0003095 | 8.842e-05 |
| 2019-2023 | Q | A06 | 0 | 8.842e-05 |
| 2019-2023 | C1 | A06 | 0 | 8.842e-05 |
| 2024-2026 | S | A4b | 0.0002729 | 6.15e-05 |
| 2024-2026 | M | A4b | 0.000246 | 6.15e-05 |
| 2024-2026 | Q | A4b | 0 | 6.15e-05 |
| 2024-2026 | C1 | A4b | 0 | 6.15e-05 |
| 2024-2026 | S | A4b_CVRv5 | 0.0002729 | 6.15e-05 |
| 2024-2026 | M | A4b_CVRv5 | 0.000246 | 6.15e-05 |
| 2024-2026 | Q | A4b_CVRv5 | 0 | 6.15e-05 |
| 2024-2026 | C1 | A4b_CVRv5 | 0 | 6.15e-05 |
| 2024-2026 | S | M_mean3_v2 | 0.0002729 | 6.15e-05 |
| 2024-2026 | M | M_mean3_v2 | 0.000246 | 6.15e-05 |
| 2024-2026 | Q | M_mean3_v2 | 0 | 6.15e-05 |
| 2024-2026 | C1 | M_mean3_v2 | 0 | 6.15e-05 |
| 2024-2026 | S | M_mean3_v2_CVRv5 | 0.0002729 | 6.15e-05 |
| 2024-2026 | M | M_mean3_v2_CVRv5 | 0.000246 | 6.15e-05 |
| 2024-2026 | Q | M_mean3_v2_CVRv5 | 0 | 6.15e-05 |
| 2024-2026 | C1 | M_mean3_v2_CVRv5 | 0 | 6.15e-05 |
| 2024-2026 | S | M_union3_v2 | 0.0002729 | 6.15e-05 |
| 2024-2026 | M | M_union3_v2 | 0.000246 | 6.15e-05 |
| 2024-2026 | Q | M_union3_v2 | 0 | 6.15e-05 |
| 2024-2026 | C1 | M_union3_v2 | 0 | 6.15e-05 |
| 2024-2026 | S | M_union3_v2_CVRv5 | 0.0002729 | 6.15e-05 |
| 2024-2026 | M | M_union3_v2_CVRv5 | 0.000246 | 6.15e-05 |
| 2024-2026 | Q | M_union3_v2_CVRv5 | 0 | 6.15e-05 |
| 2024-2026 | C1 | M_union3_v2_CVRv5 | 0 | 6.15e-05 |
| 2024-2026 | S | R2 | 0.0002729 | 6.15e-05 |
| 2024-2026 | M | R2 | 0.000246 | 6.15e-05 |
| 2024-2026 | Q | R2 | 0 | 6.15e-05 |
| 2024-2026 | C1 | R2 | 0 | 6.15e-05 |
| 2024-2026 | S | A06 | 0.0002729 | 6.15e-05 |
| 2024-2026 | M | A06 | 0.000246 | 6.15e-05 |
| 2024-2026 | Q | A06 | 0 | 6.15e-05 |
| 2024-2026 | C1 | A06 | 0 | 6.15e-05 |


> 表头：主体=RP 逐日求解路径计数（全部 RP 目标 × 日 × τ 求和；recovered_* = 主路径复核失败后由独立精确路径恢复；SOLVER_LIMIT* = 隔离回父）｜算子=—｜分母=见表｜基准=—｜子集=accounts/<段>/facts_*.csv 的 rp_solver｜单位=目标 × 日 × τ｜日期=四段｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-RPSOLVER


| segment | accept_all | dfs | milp | none | recovered_both | recovered_milp_checked |
|---|---|---|---|---|---|---|
| 2010-2014 | 160128 | 60660 | 0 | 338536 | 0 | 0 |
| 2015-2018 | 196531 | 53892 | 9 | 219172 | 0 | 0 |
| 2019-2023 | 319827 | 65393 | 246 | 213232 | 5 | 1 |
| 2024-2026 | 169925 | 32887 | 577 | 56952 | 11 | 0 |


## 6. 对照分布（附录 C；诊断，未用于任何门值）

> 表头：主体=C0 / C1 / LEGACY / IID 对照分布（跨对象中位的分位）｜算子=—｜分母=见表｜基准=—｜子集=diagnostics/control_distributions｜单位=百分位点 / 份额 / 年化百分点｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=对照（C1 为已暴露原生对象；随机路径无登记读数）｜query_id=E6K-R0-CTRL


| kind | metric | objects | q10 | q50 | q90 | p95 |
|---|---|---|---|---|---|---|
| C0 | all | 6 | 0 | 0 | 0 | 0 |
| C1_daily | edit_gap_T | 6 | -45 | -4.188 | 28.32 | 55.37 |
| C1_daily | port_size_mid_LAG1 | 6 | -1.84 | -0.1642 | 1.071 | 2.735 |
| C1_daily | port_size_mid_T | 6 | -1.844 | -0.1578 | 1.077 | 2.721 |
| C1_daily | small30_delta | 6 | -0.01816 | 0 | 0.03248 | 0.04779 |
| LEGACY_POLICY_RANDOM | dturn_rel | 24 | -0.005287 | -0.004038 | -0.002822 | 0.007125 |
| LEGACY_POLICY_RANDOM | edit_gap_T | 24 | 6.191 | 7.022 | 7.825 | 8.062 |
| LEGACY_POLICY_RANDOM | impact_net_diff | 24 | -0.213 | -0.04971 | 0.1633 | 0.3694 |
| LEGACY_POLICY_RANDOM | port_size_mid_LAG1 | 24 | 0.3183 | 0.3651 | 0.4085 | 0.4188 |
| LEGACY_POLICY_RANDOM | port_size_mid_T | 24 | 0.318 | 0.3658 | 0.4084 | 0.4198 |
| LEGACY_POLICY_RANDOM | small30_delta | 24 | -0.006782 | -0.005987 | -0.00512 | 0.007062 |
| NEW_COND_ISK_IID | dturn_rel | 24 | -0.006479 | -0.005334 | -0.004414 | 0.006765 |
| NEW_COND_ISK_IID | edit_gap_T | 24 | -6.303 | -5.483 | -4.652 | 7.49 |
| NEW_COND_ISK_IID | impact_net_diff | 24 | -0.03438 | 0.1372 | 0.2842 | 0.3831 |
| NEW_COND_ISK_IID | port_size_mid_LAG1 | 24 | -0.4282 | -0.3889 | -0.3485 | 0.4744 |
| NEW_COND_ISK_IID | port_size_mid_T | 24 | -0.4279 | -0.3881 | -0.3478 | 0.4746 |
| NEW_COND_ISK_IID | small30_delta | 24 | 0.006117 | 0.006758 | 0.007425 | 0.007559 |


## 7. 限制（全部；limit_register_E6k.md 同步）

> 表头：主体=限制登记（L01 起）｜算子=—｜分母=见表｜基准=—｜子集=limit_register_E6k.md｜单位=计数｜日期=四段（Stage 0）或推导两段（掩码事实）｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=不适用（无收益读数）｜query_id=E6K-R0-LIMITS


| id | limit |
|---|---|
| L01 | 同一历史反复研究：后段是新算子首次评价（NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY），不是样本外 |
| L02 | RP 最优性只在固定规范配对集内（plan §5.4 更正）；未配对结构性编辑不执行 |
| L03 | LX 为本项目的配额 / 优先序移植（E6j matched_n 同 N 合同键），不是 DGTW AS 公式；A4b 的 T 重估不是固定共同门 |
| L04 | HG 主历史四段段首空状态（对齐旧引擎 reset）；跨段连续状态只在 48 个 HG 主展示对象作诊断 |
| L05 | z_LAG1 段首日无 T−1（未知 size 处理）；size 紧区间对共同未知只算一次 |
| L06 | Stage 0 第 3 类新算子恒等锚只在推导两段（后段在授权后同代码补算） |
| L07 | A6-3 / A3-12 在 profile 产物上抽样 455 / 154（附录 500 / 200）；推导段真实账户落盘后足额复核（checks/closure_deriv.csv） |
| L08 | 随机均值是条件于历史的机会基线，不是精确 p 值；MC 误差另报（plan §10.2 / W15） |
| L09 | descriptors_E6k.csv 的 evidence_exposure 列为编译器粗分类；逐账户暴露以 selection_exposure_ledger_E6k.csv 为准 |
| L10 | 对照分布的随机路径只取前 256 条（诊断） |
| L11 | 冲击括号（A 5 亿 κ .5 / A 10 亿 κ 1）为未校准情景，不是实际成交成本 |
| L12 | SMB 暴露回归与尾部账本只作描述；截距占比不等于"不是 size"（plan §10.3） |
| L13 | RP 主路径（DFS 节点上限 → 逐级 MILP）在部分日复核失败（HiGHS presolve 下见证解越出预算，2026-09-29 后段首跑发现）：按 X08 / plan §5.4 第 6 条由两条独立精确路径恢复（关闭 presolve、逐级见证复核的 MILP；带符号可达界剪枝的精确深搜；两者一致才采用），恢复日计数 {"2019-2023": 6, "2024-2026": 11}；未恢复日隔离回父并标 SOLVER_LIMIT，计数 {}（含此类日的 RP 账户是混合路径，不称完整 RP 经济结果）；推导两段无失败日（主路径结果与恢复代码无关） |
| L14 | 执行端补充 X04：Stage 0 第 3 类新算子恒等锚与 A1-auto 掩码事实在两后段于授权后同代码补算（R0 第 3 / 5 节按段分列）；后段第 3 类结果不回写 Stage 0 manifest（source_manifest 保持开工时状态） |
| L15 | 两个诊断的首版退化、由 v2 替代（v1 文件保留不删、不作读数）：衰减场景前瞻版误用同一 draw（`diagnostics/decay/decay_scenarios.csv` → `decay_scenarios_v2.csv`）；HG 跨段连续状态（X09）的上段末状态在段首预热日（门域 K = 0）被清空（`hg_continuous_<段>_<段>.csv` → `hg_continuous_v2_*.csv`，hold_init 只用于该诊断，登记账户不变） |
| L16 | 覆盖不足（登记 query 有、本轮未记账）：PM 固定配对交换数的嵌套与结构单边编辑（E6K-Q10-c）；TREFIT 第二关逐日有效样本数（E6K-Q07-b）；POST2 第二关前编辑数只以最终名单相对原父的换入近似（E6K-Q08-b） |

