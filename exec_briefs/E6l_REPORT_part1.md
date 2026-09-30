# E6l REPORT part1 —— 推导两段（2010-2014 / 2015-2018）全部登记对象的作用量、对照与十六卡初读

用途：plan §13.4 part1。只含推导两段；数字全部来自 `results/deriv/*.csv`（seal_deriv 之后生成）。新对象标签 `NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY`（首评、重复使用的历史，非样本外）；E6k 同构对象标 `SECOND_EVALUATION_SAME_HISTORY`，只作锚与基线。不设显著性门、不写判词；新算子 replacement_preference_status = NOT_AUTHORIZED，deployment_authorized = false。

## 1. 主展示 72 行（12 配方 × 六形态，α .25 × H5）

> 表头：主体=配方 Q0:DECAY5_10 × 六形态｜算子=DECAY5_10｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-72-Q0-DECAY5_10


| mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | MDE80 | D_sc | D_imp | D_gross | D_vs_native | D_vs_Q0 | D_vs_QHG10 | D_vs_C1 | D_vs_rule_only | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | edit_gap_mean_T | edit_gap_absmean_T | turn_rel | rmr_deriv_LEGACY_POLICY_RANDOM | mcse_deriv_LEGACY_POLICY_RANDOM | rmr_deriv_CONTENT_COND_ISK_P5 | mcse_deriv_CONTENT_COND_ISK_P5 | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A4b | 0.4416 | 0.7988 | 0.6005 | 0.178 | 0.4984 | 0.5965 | 0.6875 | 0.5517 | 0.04633 |  | 0.01198 | 0.2507 | 0.3413 | -2.127 | -2.127 | -19.57 | 19.57 | -0.03132 | 0.4384 | 0.003287 | 0.2505 | 0.002797 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| A4b_CVRv5 | 0.3829 | 0.7896 | 0.5638 | 0.1501 | 0.4204 | 0.531 | 0.6108 | 0.5275 | 0.05414 |  | -0.00913 | 0.3205 | 0.312 | -2.129 | -2.129 | -19.91 | 19.91 | -0.02711 | 0.4263 | 0.002911 | 0.2444 | 0.0025 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2 | -0.1251 | 1.088 | 0.4145 | 0.2311 | 0.647 | 0.4258 | 0.662 | 0.337 | -0.09889 |  | 0.01229 | 0.01272 | 0.3555 | -0.00798 | -0.00675 | 0.6888 | 2.068 | -0.03244 | 0.1389 | 0.003442 | -0.07224 | 0.003093 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2_CVRv5 | -0.3443 | 0.2885 | -0.06278 | 0.2021 | 0.566 | -0.07596 | 0.127 | -0.1229 | -0.05645 |  | -0.002402 | -0.1928 | 0.008965 | -0.009077 | -0.007707 | 0.5255 | 2.406 | -0.02626 | -0.01169 | 0.003128 | -0.1232 | 0.002871 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2 | 0.1798 | 0.5123 | 0.3277 | 0.1239 | 0.347 | 0.03134 | 0.1806 | 0.361 | 0.2521 |  | -0.06109 | 0.2375 | 0.2433 | -0.6279 | -0.6272 | -15.94 | 15.94 | 0.02921 | 0.3823 | 0.002941 | 0.2982 | 0.002654 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2_CVRv5 | 0.2087 | 0.5604 | 0.3652 | 0.1194 | 0.3343 | 0.07782 | 0.2188 | 0.3996 | 0.2336 |  | -0.06349 | 0.2907 | 0.315 | -0.6038 | -0.6033 | -15.95 | 15.95 | 0.03321 | 0.381 | 0.002704 | 0.2859 | 0.002434 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |


> 表头：主体=配方 Q0:HG10 × 六形态｜算子=HG10｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-72-Q0-HG10


| mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | MDE80 | D_sc | D_imp | D_gross | D_vs_native | D_vs_Q0 | D_vs_QHG10 | D_vs_C1 | D_vs_rule_only | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | edit_gap_mean_T | edit_gap_absmean_T | turn_rel | rmr_deriv_LEGACY_POLICY_RANDOM | mcse_deriv_LEGACY_POLICY_RANDOM | rmr_deriv_CONTENT_COND_ISK_P5 | mcse_deriv_CONTENT_COND_ISK_P5 | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A4b | 0.4631 | 0.745 | 0.5885 | 0.1765 | 0.4941 | 0.5853 | 0.6765 | 0.5397 | 0.03435 |  |  | 0.2218 | 0.3188 | -2.108 | -2.108 | -19.38 | 19.38 | -0.03133 | 0.4276 | 0.003285 | 0.244 | 0.002875 | SECOND_EVALUATION_SAME_HISTORY |
| A4b_CVRv5 | 0.4064 | 0.7809 | 0.573 | 0.15 | 0.42 | 0.535 | 0.6196 | 0.537 | 0.06327 |  |  | 0.3163 | 0.3239 | -2.113 | -2.113 | -19.77 | 19.77 | -0.02684 | 0.4356 | 0.002924 | 0.261 | 0.002558 | SECOND_EVALUATION_SAME_HISTORY |
| M_mean3_v2 | -0.1319 | 1.069 | 0.4022 | 0.2314 | 0.6479 | 0.4168 | 0.6509 | 0.3245 | -0.1112 |  |  | -0.0255 | 0.3384 | -0.005304 | -0.004069 | 0.6989 | 1.989 | -0.03252 | 0.1269 | 0.003468 | -0.08191 | 0.003118 | SECOND_EVALUATION_SAME_HISTORY |
| M_mean3_v2_CVRv5 | -0.3242 | 0.2689 | -0.06038 | 0.2023 | 0.5665 | -0.07268 | 0.1301 | -0.1207 | -0.05404 |  |  | -0.2071 | -0.008131 | -0.007213 | -0.005842 | 0.4797 | 2.302 | -0.02633 | -0.009016 | 0.003154 | -0.1227 | 0.002895 | SECOND_EVALUATION_SAME_HISTORY |
| M_union3_v2 | 0.2038 | 0.6197 | 0.3888 | 0.127 | 0.3556 | 0.08644 | 0.2427 | 0.4219 | 0.3132 |  |  | 0.3242 | 0.2938 | -0.6176 | -0.6169 | -15.6 | 15.6 | 0.02903 | 0.4419 | 0.002964 | 0.3598 | 0.002665 | SECOND_EVALUATION_SAME_HISTORY |
| M_union3_v2_CVRv5 | 0.2374 | 0.6673 | 0.4286 | 0.1231 | 0.3446 | 0.1338 | 0.283 | 0.4629 | 0.2971 |  |  | 0.3763 | 0.3725 | -0.5938 | -0.5932 | -15.61 | 15.61 | 0.033 | 0.4437 | 0.002724 | 0.3522 | 0.002441 | SECOND_EVALUATION_SAME_HISTORY |


> 表头：主体=配方 Q0:INV10 × 六形态｜算子=INV10｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-72-Q0-INV10


| mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | MDE80 | D_sc | D_imp | D_gross | D_vs_native | D_vs_Q0 | D_vs_QHG10 | D_vs_C1 | D_vs_rule_only | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | edit_gap_mean_T | edit_gap_absmean_T | turn_rel | rmr_deriv_LEGACY_POLICY_RANDOM | mcse_deriv_LEGACY_POLICY_RANDOM | rmr_deriv_CONTENT_COND_ISK_P5 | mcse_deriv_CONTENT_COND_ISK_P5 | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A4b | 0.4466 | 0.6451 | 0.5349 | 0.184 | 0.5153 | 0.5399 | 0.6879 | 0.4704 | -0.01922 |  | -0.05357 | 0.225 | 0.3198 | -2.021 | -2.02 | -18.56 | 18.56 | -0.04142 | 0.3298 | 0.002943 | 0.2369 | 0.002662 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| A4b_CVRv5 | 0.3607 | 0.7463 | 0.5322 | 0.155 | 0.4341 | 0.4874 | 0.6004 | 0.4926 | 0.02255 |  | -0.04072 | 0.2134 | 0.3928 | -1.956 | -1.955 | -18.81 | 18.81 | -0.02938 | 0.3644 | 0.002608 | 0.2707 | 0.002355 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2 | -0.01205 | 1.237 | 0.5434 | 0.2336 | 0.6541 | 0.5587 | 0.8367 | 0.451 | 0.02996 |  | 0.1411 | 0.2681 | 0.4677 | -0.004515 | -0.002226 | 0.6441 | 1.799 | -0.03866 | 0.3058 | 0.003382 | 0.06374 | 0.003029 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2_CVRv5 | -0.2518 | 0.09836 | -0.09604 | 0.208 | 0.5823 | -0.1136 | 0.1175 | -0.1609 | -0.0897 |  | -0.03565 | -0.09798 | 0.02129 | 0.05908 | 0.06163 | 0.7862 | 1.978 | -0.02823 | 0.03332 | 0.003101 | -0.08631 | 0.002704 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2 | 0.1469 | 0.9651 | 0.5109 | 0.1597 | 0.4472 | -0.1012 | 0.2402 | 0.586 | 0.4352 |  | 0.1221 | 0.3293 | 0.373 | 0.3898 | 0.3922 | -13.56 | 13.56 | 0.06632 | 0.4063 | 0.002716 | 0.2605 | 0.002449 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2_CVRv5 | 0.1323 | 1.07 | 0.5495 | 0.1534 | 0.4294 | -0.0574 | 0.2833 | 0.6252 | 0.418 |  | 0.1209 | 0.3754 | 0.4007 | 0.4318 | 0.4341 | -13.32 | 13.32 | 0.0735 | 0.4078 | 0.002455 | 0.279 | 0.002262 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |


> 表头：主体=配方 Q0:LAG1_10 × 六形态｜算子=LAG1_10｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-72-Q0-LAG1_10


| mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | MDE80 | D_sc | D_imp | D_gross | D_vs_native | D_vs_Q0 | D_vs_QHG10 | D_vs_C1 | D_vs_rule_only | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | edit_gap_mean_T | edit_gap_absmean_T | turn_rel | rmr_deriv_LEGACY_POLICY_RANDOM | mcse_deriv_LEGACY_POLICY_RANDOM | rmr_deriv_CONTENT_COND_ISK_P5 | mcse_deriv_CONTENT_COND_ISK_P5 | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A4b | 0.4053 | 0.7005 | 0.5366 | 0.1782 | 0.499 | 0.5332 | 0.6219 | 0.4889 | -0.01752 |  | -0.05187 | 0.1476 | 0.2532 | -2.077 | -2.077 | -19 | 19 | -0.03066 | 0.3774 | 0.00325 | 0.1843 | 0.002745 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| A4b_CVRv5 | 0.3592 | 0.7463 | 0.5314 | 0.1513 | 0.4238 | 0.4991 | 0.5766 | 0.496 | 0.02174 |  | -0.04153 | 0.2316 | 0.2568 | -2.073 | -2.073 | -19.27 | 19.27 | -0.0264 | 0.3964 | 0.00288 | 0.2082 | 0.002483 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2 | -0.2003 | 0.9492 | 0.311 | 0.2218 | 0.621 | 0.3258 | 0.5511 | 0.236 | -0.2024 |  | -0.0912 | -0.04202 | 0.2137 | -0.004933 | -0.003708 | 0.836 | 2.064 | -0.03139 | 0.03251 | 0.003376 | -0.1523 | 0.002903 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2_CVRv5 | -0.4573 | 0.226 | -0.1533 | 0.1989 | 0.5569 | -0.1642 | 0.03069 | -0.2112 | -0.147 |  | -0.09294 | -0.2462 | -0.1329 | -0.003561 | -0.002203 | 0.5933 | 2.251 | -0.02527 | -0.1059 | 0.003053 | -0.1922 | 0.002712 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2 | 0.1173 | 0.4502 | 0.2654 | 0.1154 | 0.3231 | -0.01951 | 0.1223 | 0.2981 | 0.1898 |  | -0.1234 | 0.1483 | 0.2084 | -0.6319 | -0.6312 | -15.29 | 15.29 | 0.0287 | 0.3284 | 0.002807 | 0.2477 | 0.00252 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2_CVRv5 | 0.1481 | 0.5279 | 0.3171 | 0.1103 | 0.3088 | 0.03705 | 0.1765 | 0.3502 | 0.1855 |  | -0.1116 | 0.2079 | 0.2655 | -0.6143 | -0.6138 | -15.34 | 15.34 | 0.03201 | 0.3377 | 0.002577 | 0.2484 | 0.002324 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |


> 表头：主体=配方 Q0:NATIVE × 六形态｜算子=NATIVE｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-72-Q0-NATIVE


| mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | MDE80 | D_sc | D_imp | D_gross | D_vs_native | D_vs_Q0 | D_vs_QHG10 | D_vs_C1 | D_vs_rule_only | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | edit_gap_mean_T | edit_gap_absmean_T | turn_rel | rmr_deriv_LEGACY_POLICY_RANDOM | mcse_deriv_LEGACY_POLICY_RANDOM | rmr_deriv_CONTENT_COND_ISK_P5 | mcse_deriv_CONTENT_COND_ISK_P5 | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A4b | 0.3423 | 0.8186 | 0.5542 | 0.1412 | 0.3954 | 0.5572 | 0.6079 | 0.5214 |  |  | -0.03435 | 0.2479 |  | -1.577 | -1.577 | -18.78 | 18.78 | -0.02103 | 0.5215 | 0.003126 | 0.2833 | 0.002567 | SECOND_EVALUATION_SAME_HISTORY |
| A4b_CVRv5 | 0.3291 | 0.735 | 0.5097 | 0.123 | 0.3444 | 0.4965 | 0.538 | 0.4849 |  |  | -0.06327 | 0.1943 |  | -1.587 | -1.587 | -19.96 | 19.96 | -0.01839 | 0.4907 | 0.002878 | 0.2958 | 0.002296 | SECOND_EVALUATION_SAME_HISTORY |
| M_mean3_v2 | 0.08627 | 1.046 | 0.5134 | 0.2006 | 0.5615 | 0.5104 | 0.7259 | 0.4514 |  |  | 0.1112 | 0.2803 |  | 0.04025 | 0.04198 | -0.3875 | 2.003 | -0.02595 | 0.272 | 0.003352 | 0.04691 | 0.002778 | SECOND_EVALUATION_SAME_HISTORY |
| M_mean3_v2_CVRv5 | -0.2432 | 0.2893 | -0.006336 | 0.1787 | 0.5003 | -0.0269 | 0.1564 | -0.05364 |  |  | 0.05404 | -0.1185 |  | 0.04718 | 0.04917 | -0.3268 | 1.868 | -0.02066 | 0.02582 | 0.003088 | -0.09142 | 0.002579 | SECOND_EVALUATION_SAME_HISTORY |
| M_union3_v2 | -0.05315 | 0.2363 | 0.07563 | 0.1004 | 0.281 | -0.125 | -0.01648 | 0.0984 |  |  | -0.3132 | 0.008311 |  | -0.5017 | -0.5013 | -17.94 | 17.94 | 0.02002 | 0.2621 | 0.002636 | 0.1551 | 0.002315 | SECOND_EVALUATION_SAME_HISTORY |
| M_union3_v2_CVRv5 | -0.01051 | 0.3087 | 0.1315 | 0.09265 | 0.2594 | -0.07356 | 0.03971 | 0.1548 |  |  | -0.2971 | 0.05083 |  | -0.4907 | -0.4904 | -17.53 | 17.53 | 0.02248 | 0.261 | 0.002428 | 0.1648 | 0.002138 | SECOND_EVALUATION_SAME_HISTORY |


> 表头：主体=配方 Q_D3:NATIVE × 六形态｜算子=NATIVE｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-72-Q_D3-NATIVE


| mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | MDE80 | D_sc | D_imp | D_gross | D_vs_native | D_vs_Q0 | D_vs_QHG10 | D_vs_C1 | D_vs_rule_only | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | edit_gap_mean_T | edit_gap_absmean_T | turn_rel | rmr_deriv_LEGACY_POLICY_RANDOM | mcse_deriv_LEGACY_POLICY_RANDOM | rmr_deriv_CONTENT_COND_ISK_P5 | mcse_deriv_CONTENT_COND_ISK_P5 | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A4b | 0.2866 | 0.5652 | 0.4105 | 0.135 | 0.3781 | 0.4099 | 0.4972 | 0.3889 |  | -0.1437 | -0.178 | 0.1042 |  | -0.3131 | -0.3131 | -4.476 | 4.476 | -0.01397 | 0.3775 | 0.003098 | 0.2526 | 0.003032 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| A4b_CVRv5 | 0.226 | 0.4811 | 0.3395 | 0.1117 | 0.3127 | 0.3181 | 0.4015 | 0.3241 |  | -0.1702 | -0.2335 | 0.02406 |  | -0.3058 | -0.3057 | -5.114 | 5.114 | -0.01155 | 0.3181 | 0.002739 | 0.2085 | 0.002659 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2 | -0.04822 | 0.586 | 0.2339 | 0.2007 | 0.5619 | 0.24 | 0.4834 | 0.1762 |  | -0.2795 | -0.1683 | 0.0008277 |  | 0.5029 | 0.5046 | 9.82 | 9.82 | -0.02417 | -0.006901 | 0.003452 | -0.1086 | 0.003577 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2_CVRv5 | -0.3633 | 0.09398 | -0.1599 | 0.1817 | 0.5087 | -0.1857 | 0.03798 | -0.2033 |  | -0.1536 | -0.09951 | -0.2721 |  | 0.5022 | 0.5042 | 9.769 | 9.769 | -0.01894 | -0.1304 | 0.00319 | -0.1751 | 0.003336 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2 | -0.2663 | 0.1103 | -0.09876 | 0.1292 | 0.3617 | -0.3716 | -0.1619 | -0.06583 |  | -0.1744 | -0.4876 | -0.1661 |  | 0.506 | 0.5081 | -1.829 | 1.829 | 0.02894 | 0.08807 | 0.002608 | 0.04887 | 0.002858 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2_CVRv5 | -0.1583 | 0.1983 | 0.0003269 | 0.1173 | 0.3283 | -0.2698 | -0.06184 | 0.03231 |  | -0.1312 | -0.4283 | -0.08035 |  | 0.5175 | 0.5196 | -1.517 | 1.517 | 0.03097 | 0.1317 | 0.002426 | 0.08472 | 0.002653 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |


> 表头：主体=配方 Q_D5:HG10 × 六形态｜算子=HG10｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-72-Q_D5-HG10


| mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | MDE80 | D_sc | D_imp | D_gross | D_vs_native | D_vs_Q0 | D_vs_QHG10 | D_vs_C1 | D_vs_rule_only | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | edit_gap_mean_T | edit_gap_absmean_T | turn_rel | rmr_deriv_LEGACY_POLICY_RANDOM | mcse_deriv_LEGACY_POLICY_RANDOM | rmr_deriv_CONTENT_COND_ISK_P5 | mcse_deriv_CONTENT_COND_ISK_P5 | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A4b | 0.2686 | 0.9317 | 0.5636 | 0.1391 | 0.3894 | 0.5602 | 0.6809 | 0.5294 | 0.2642 | -0.02492 | -0.02492 | 0.1969 | 0.2939 | -0.6085 | -0.6085 | -6.937 | 6.937 | -0.02201 | 0.4069 | 0.003232 | 0.2282 | 0.003379 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| A4b_CVRv5 | 0.2723 | 0.7516 | 0.4855 | 0.1193 | 0.3341 | 0.4423 | 0.5642 | 0.4614 | 0.2147 | -0.08746 | -0.08746 | 0.2288 | 0.2364 | -0.5968 | -0.5968 | -7.616 | 7.616 | -0.01791 | 0.3515 | 0.002829 | 0.2048 | 0.002967 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2 | -0.2035 | 0.9623 | 0.3151 | 0.231 | 0.6467 | 0.3323 | 0.6158 | 0.2417 | 0.1474 | -0.08714 | -0.08714 | -0.1126 | 0.2513 | 0.5468 | 0.5479 | 10.15 | 10.15 | -0.03071 | 0.05338 | 0.003528 | -0.04205 | 0.003838 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2_CVRv5 | -0.421 | 0.2597 | -0.1182 | 0.2087 | 0.5843 | -0.1404 | 0.1236 | -0.1746 | 0.08484 | -0.05779 | -0.05779 | -0.2649 | -0.06592 | 0.5436 | 0.545 | 10.14 | 10.14 | -0.02464 | -0.05685 | 0.003254 | -0.1155 | 0.003549 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2 | -0.05794 | 0.3599 | 0.128 | 0.15 | 0.42 | -0.2554 | 0.01185 | 0.1766 | 0.1963 | -0.2608 | -0.2608 | 0.06332 | 0.03296 | 0.6343 | 0.6354 | -3.271 | 3.271 | 0.04282 | 0.1899 | 0.002913 | 0.1642 | 0.003249 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2_CVRv5 | 0.02635 | 0.4318 | 0.2067 | 0.1391 | 0.3894 | -0.1792 | 0.09133 | 0.2548 | 0.2144 | -0.2219 | -0.2219 | 0.1544 | 0.1506 | 0.6307 | 0.6317 | -3.124 | 3.124 | 0.04667 | 0.2312 | 0.002682 | 0.1919 | 0.003 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |


> 表头：主体=配方 Q_D5:NATIVE × 六形态｜算子=NATIVE｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-72-Q_D5-NATIVE


| mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | MDE80 | D_sc | D_imp | D_gross | D_vs_native | D_vs_Q0 | D_vs_QHG10 | D_vs_C1 | D_vs_rule_only | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | edit_gap_mean_T | edit_gap_absmean_T | turn_rel | rmr_deriv_LEGACY_POLICY_RANDOM | mcse_deriv_LEGACY_POLICY_RANDOM | rmr_deriv_CONTENT_COND_ISK_P5 | mcse_deriv_CONTENT_COND_ISK_P5 | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A4b | 0.03736 | 0.6263 | 0.2993 | 0.132 | 0.3695 | 0.3025 | 0.3979 | 0.2773 |  | -0.2548 | -0.2892 | -0.006914 |  | -0.1686 | -0.1685 | -2.563 | 2.563 | -0.01423 | 0.268 | 0.003089 | 0.1342 | 0.003169 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| A4b_CVRv5 | 0.07638 | 0.5135 | 0.2708 | 0.1092 | 0.3057 | 0.2335 | 0.3422 | 0.2549 |  | -0.2388 | -0.3021 | -0.0446 |  | -0.1555 | -0.1554 | -2.656 | 2.656 | -0.01182 | 0.2492 | 0.002718 | 0.1318 | 0.002814 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2 | -0.1751 | 0.5955 | 0.1677 | 0.2124 | 0.5947 | 0.1704 | 0.4316 | 0.1094 |  | -0.3457 | -0.2346 | -0.0654 |  | 0.5814 | 0.5831 | 11.87 | 11.87 | -0.02441 | -0.06926 | 0.003325 | -0.1701 | 0.003509 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2_CVRv5 | -0.3634 | -0.002798 | -0.203 | 0.1858 | 0.5203 | -0.2402 | 0.01004 | -0.2469 |  | -0.1967 | -0.1426 | -0.3152 |  | 0.5884 | 0.5904 | 11.95 | 11.95 | -0.01917 | -0.1679 | 0.003049 | -0.2451 | 0.003258 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2 | -0.2902 | 0.2085 | -0.06834 | 0.1361 | 0.3812 | -0.3694 | -0.1274 | -0.03294 |  | -0.144 | -0.4571 | -0.1357 |  | 0.6946 | 0.6966 | 0.6464 | 0.6464 | 0.03117 | 0.1174 | 0.002633 | 0.06888 | 0.00291 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2_CVRv5 | -0.1996 | 0.2319 | -0.007663 | 0.1215 | 0.3403 | -0.3061 | -0.06687 | 0.02679 |  | -0.1392 | -0.4363 | -0.08834 |  | 0.6923 | 0.6944 | 1.177 | 1.177 | 0.03345 | 0.1221 | 0.002421 | 0.06971 | 0.002685 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |


> 表头：主体=配方 Q_DEW5:HG10 × 六形态｜算子=HG10｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-72-Q_DEW5-HG10


| mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | MDE80 | D_sc | D_imp | D_gross | D_vs_native | D_vs_Q0 | D_vs_QHG10 | D_vs_C1 | D_vs_rule_only | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | edit_gap_mean_T | edit_gap_absmean_T | turn_rel | rmr_deriv_LEGACY_POLICY_RANDOM | mcse_deriv_LEGACY_POLICY_RANDOM | rmr_deriv_CONTENT_COND_ISK_P5 | mcse_deriv_CONTENT_COND_ISK_P5 | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A4b | 0.3208 | 0.7465 | 0.5102 | 0.1453 | 0.4069 | 0.5078 | 0.6353 | 0.4721 | 0.1009 | -0.0783 | -0.0783 | 0.1435 | 0.2405 | -0.757 | -0.757 | -9.058 | 9.058 | -0.02453 | 0.3449 | 0.003237 | 0.1784 | 0.003321 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| A4b_CVRv5 | 0.3088 | 0.5804 | 0.4296 | 0.1214 | 0.34 | 0.384 | 0.5157 | 0.402 | 0.1283 | -0.1433 | -0.1433 | 0.1729 | 0.1805 | -0.756 | -0.756 | -9.605 | 9.605 | -0.02063 | 0.2868 | 0.002865 | 0.1522 | 0.002896 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2 | -0.1712 | 0.8264 | 0.2726 | 0.2308 | 0.6461 | 0.2921 | 0.5968 | 0.1919 | -0.00601 | -0.1296 | -0.1296 | -0.1551 | 0.2088 | 0.5366 | 0.5383 | 9.598 | 9.598 | -0.03377 | 0.007781 | 0.00347 | -0.09659 | 0.003716 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2_CVRv5 | -0.4365 | 0.1275 | -0.1856 | 0.2079 | 0.5822 | -0.2084 | 0.07551 | -0.2483 | 0.02864 | -0.1253 | -0.1253 | -0.3323 | -0.1334 | 0.5348 | 0.5368 | 9.428 | 9.428 | -0.02738 | -0.1285 | 0.003232 | -0.1634 | 0.003466 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2 | -0.1917 | 0.4752 | 0.105 | 0.1511 | 0.423 | -0.3416 | -0.03284 | 0.1589 | 0.1795 | -0.2838 | -0.2838 | 0.04032 | 0.009957 | 0.6191 | 0.6202 | -5.419 | 5.419 | 0.0477 | 0.1636 | 0.002814 | 0.1439 | 0.003163 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2_CVRv5 | -0.05704 | 0.4986 | 0.1901 | 0.1406 | 0.3936 | -0.2611 | 0.05443 | 0.2433 | 0.2035 | -0.2385 | -0.2385 | 0.1378 | 0.134 | 0.6356 | 0.6367 | -5.166 | 5.166 | 0.05186 | 0.2108 | 0.002606 | 0.1785 | 0.002911 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |


> 表头：主体=配方 Q_DEW5:NATIVE × 六形态｜算子=NATIVE｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-72-Q_DEW5-NATIVE


| mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | MDE80 | D_sc | D_imp | D_gross | D_vs_native | D_vs_Q0 | D_vs_QHG10 | D_vs_C1 | D_vs_rule_only | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | edit_gap_mean_T | edit_gap_absmean_T | turn_rel | rmr_deriv_LEGACY_POLICY_RANDOM | mcse_deriv_LEGACY_POLICY_RANDOM | rmr_deriv_CONTENT_COND_ISK_P5 | mcse_deriv_CONTENT_COND_ISK_P5 | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A4b | 0.1808 | 0.6945 | 0.4094 | 0.1371 | 0.3839 | 0.4138 | 0.5152 | 0.3836 |  | -0.1448 | -0.1792 | 0.1031 |  | -0.2912 | -0.2912 | -4.794 | 4.794 | -0.01657 | 0.3807 | 0.003078 | 0.2556 | 0.00311 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| A4b_CVRv5 | 0.1653 | 0.4711 | 0.3013 | 0.1103 | 0.3089 | 0.282 | 0.3739 | 0.2835 |  | -0.2084 | -0.2716 | -0.01411 |  | -0.2943 | -0.2943 | -5.191 | 5.191 | -0.01329 | 0.2801 | 0.002712 | 0.1745 | 0.002714 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2 | 0.04836 | 0.566 | 0.2786 | 0.2212 | 0.6193 | 0.2828 | 0.5612 | 0.2139 |  | -0.2348 | -0.1236 | 0.04553 |  | 0.586 | 0.5877 | 11.57 | 11.57 | -0.02707 | 0.03767 | 0.003378 | -0.05708 | 0.00349 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2_CVRv5 | -0.2779 | -0.1349 | -0.2143 | 0.1938 | 0.5426 | -0.2438 | 0.01116 | -0.2628 |  | -0.2079 | -0.1539 | -0.3264 |  | 0.5865 | 0.5885 | 11.64 | 11.64 | -0.02119 | -0.183 | 0.003147 | -0.212 | 0.003232 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2 | -0.2757 | 0.1764 | -0.07457 | 0.1417 | 0.3969 | -0.4261 | -0.1574 | -0.0332 |  | -0.1502 | -0.4634 | -0.1419 |  | 0.6791 | 0.6812 | -1.942 | 1.942 | 0.0363 | 0.111 | 0.002603 | 0.07818 | 0.002839 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2_CVRv5 | -0.1923 | 0.2099 | -0.01337 | 0.1278 | 0.3577 | -0.3577 | -0.09556 | 0.02713 |  | -0.1449 | -0.442 | -0.09405 |  | 0.6872 | 0.6893 | -1.511 | 1.511 | 0.03921 | 0.1145 | 0.002387 | 0.08022 | 0.002562 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |


> 表头：主体=配方 Q_RANK5:HG10 × 六形态｜算子=HG10｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-72-Q_RANK5-HG10


| mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | MDE80 | D_sc | D_imp | D_gross | D_vs_native | D_vs_Q0 | D_vs_QHG10 | D_vs_C1 | D_vs_rule_only | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | edit_gap_mean_T | edit_gap_absmean_T | turn_rel | rmr_deriv_LEGACY_POLICY_RANDOM | mcse_deriv_LEGACY_POLICY_RANDOM | rmr_deriv_CONTENT_COND_ISK_P5 | mcse_deriv_CONTENT_COND_ISK_P5 | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A4b | 0.3739 | 0.4999 | 0.43 | 0.1735 | 0.4858 | 0.4265 | 0.5119 | 0.3895 | -0.04859 | -0.1585 | -0.1585 | 0.06325 | 0.1603 | -1.869 | -1.869 | -18.71 | 18.71 | -0.02605 | 0.2694 | 0.003258 | -0.02958 | 0.003195 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| A4b_CVRv5 | 0.4416 | 0.516 | 0.4747 | 0.1434 | 0.4016 | 0.454 | 0.5281 | 0.4434 | 0.1228 | -0.09824 | -0.09824 | 0.218 | 0.2256 | -1.846 | -1.846 | -19.38 | 19.38 | -0.02338 | 0.3369 | 0.002901 | 0.06958 | 0.002791 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2 | -0.1 | 1.122 | 0.4436 | 0.236 | 0.6607 | 0.4462 | 0.6565 | 0.3802 | 0.1303 | 0.04136 | 0.04136 | 0.01586 | 0.3798 | -0.2439 | -0.2432 | -3.231 | 3.231 | -0.02651 | 0.1789 | 0.003518 | -0.05545 | 0.003493 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2_CVRv5 | -0.1851 | 0.5627 | 0.1476 | 0.2056 | 0.5757 | 0.1378 | 0.3069 | 0.09885 | 0.115 | 0.2079 | 0.2079 | 0.000853 | 0.1998 | -0.2468 | -0.246 | -3.741 | 3.741 | -0.02127 | 0.206 | 0.003261 | -0.05259 | 0.003239 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2 | -0.2296 | 0.2035 | -0.03694 | 0.1328 | 0.3718 | -0.3114 | -0.1469 | -0.004275 | 0.06414 | -0.4257 | -0.4257 | -0.1016 | -0.1319 | -0.4334 | -0.4326 | -13.36 | 13.36 | 0.02832 | 0.02484 | 0.002861 | 0.004169 | 0.003027 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2_CVRv5 | -0.09712 | 0.2732 | 0.06762 | 0.1232 | 0.3449 | -0.2069 | -0.03849 | 0.09967 | 0.1119 | -0.361 | -0.361 | 0.0153 | 0.01147 | -0.4464 | -0.4457 | -13.32 | 13.32 | 0.03072 | 0.09139 | 0.002668 | 0.05931 | 0.002811 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |


> 表头：主体=配方 Q_RANK5:NATIVE × 六形态｜算子=NATIVE｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-72-Q_RANK5-NATIVE


| mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | MDE80 | D_sc | D_imp | D_gross | D_vs_native | D_vs_Q0 | D_vs_QHG10 | D_vs_C1 | D_vs_rule_only | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | edit_gap_mean_T | edit_gap_absmean_T | turn_rel | rmr_deriv_LEGACY_POLICY_RANDOM | mcse_deriv_LEGACY_POLICY_RANDOM | rmr_deriv_CONTENT_COND_ISK_P5 | mcse_deriv_CONTENT_COND_ISK_P5 | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A4b | 0.2668 | 0.7428 | 0.4786 | 0.1525 | 0.427 | 0.4777 | 0.5424 | 0.4506 |  | -0.07561 | -0.11 | 0.1723 |  | -1.316 | -1.316 | -16.09 | 16.09 | -0.01783 | 0.4517 | 0.003143 | 0.1645 | 0.002921 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| A4b_CVRv5 | 0.2176 | 0.5195 | 0.3519 | 0.127 | 0.3555 | 0.3435 | 0.3942 | 0.3306 |  | -0.1578 | -0.221 | 0.03648 |  | -1.301 | -1.301 | -16.8 | 16.8 | -0.01575 | 0.3341 | 0.002766 | 0.1061 | 0.002607 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2 | -0.1125 | 0.8447 | 0.3133 | 0.2018 | 0.5652 | 0.3147 | 0.4922 | 0.2634 |  | -0.2001 | -0.08893 | 0.08023 |  | -0.1876 | -0.1864 | -4.196 | 4.196 | -0.02089 | 0.07674 | 0.003333 | -0.1296 | 0.003165 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_mean3_v2_CVRv5 | -0.3086 | 0.4583 | 0.03257 | 0.1837 | 0.5142 | 0.01302 | 0.1695 | -0.006447 |  | 0.0389 | 0.09295 | -0.0796 |  | -0.1865 | -0.1851 | -4.591 | 4.591 | -0.01706 | 0.06896 | 0.00315 | -0.1527 | 0.002938 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2 | -0.3445 | 0.2027 | -0.1011 | 0.1223 | 0.3424 | -0.2811 | -0.1552 | -0.07996 |  | -0.1767 | -0.4899 | -0.1684 |  | -0.2633 | -0.2627 | -10.33 | 10.33 | 0.01857 | 0.08748 | 0.00262 | 0.007756 | 0.002709 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| M_union3_v2_CVRv5 | -0.2512 | 0.214 | -0.04428 | 0.1082 | 0.3029 | -0.2249 | -0.09542 | -0.02447 |  | -0.1758 | -0.4729 | -0.125 |  | -0.2882 | -0.2877 | -10.36 | 10.36 | 0.01925 | 0.08754 | 0.002399 | 0.02272 | 0.002512 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |


## 2. 同 72 配方的 α .5 剂量面板与 α .125 邻域（任一剂量按同一正式尺子，政策在 part3）

> 表头：主体=α .5 剂量面板｜算子=12 配方｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=dose72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-DOSE72


| recipe | mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | D_sc | D_vs_native | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | turn_rel | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Q0:DECAY5_10 | A4b | 0.3455 | 1.882 | 1.029 | 0.4239 | 1.021 | -0.1769 | -4.503 | -4.502 | -0.1048 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:DECAY5_10 | A4b_CVRv5 | 0.179 | 1.698 | 0.8549 | 0.3611 | 0.7754 | -0.08386 | -4.501 | -4.501 | -0.09042 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:DECAY5_10 | M_mean3_v2 | -0.3379 | 1.646 | 0.5448 | 0.3517 | 0.5611 | 0.09286 | 0.3355 | 0.3399 | -0.042 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:DECAY5_10 | M_mean3_v2_CVRv5 | -0.6885 | 0.3742 | -0.2157 | 0.3136 | -0.2312 | 0.00255 | 0.3269 | 0.3319 | -0.0326 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:DECAY5_10 | M_union3_v2 | -0.503 | 1.138 | 0.2272 | 0.2829 | -0.4291 | -0.1131 | -2.129 | -2.126 | 0.04631 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:DECAY5_10 | M_union3_v2_CVRv5 | -0.2792 | 1.122 | 0.3444 | 0.2568 | -0.3328 | -0.08522 | -2.14 | -2.137 | 0.0534 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:HG10 | A4b | 0.3298 | 1.899 | 1.028 | 0.419 | 1.02 | -0.1779 | -4.597 | -4.597 | -0.1062 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:HG10 | A4b_CVRv5 | 0.1504 | 1.731 | 0.8535 | 0.3566 | 0.7854 | -0.08528 | -4.597 | -4.597 | -0.09215 | SECOND_EVALUATION_SAME_HISTORY |
| Q0:HG10 | M_mean3_v2 | -0.318 | 1.666 | 0.5646 | 0.3521 | 0.5817 | 0.1127 | 0.3244 | 0.3288 | -0.04257 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:HG10 | M_mean3_v2_CVRv5 | -0.6914 | 0.3725 | -0.2181 | 0.3149 | -0.2344 | 0.0001807 | 0.3155 | 0.3205 | -0.03312 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:HG10 | M_union3_v2 | -0.438 | 0.8528 | 0.1362 | 0.2742 | -0.4872 | -0.2042 | -2.15 | -2.147 | 0.04501 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:HG10 | M_union3_v2_CVRv5 | -0.2208 | 0.9003 | 0.2779 | 0.2505 | -0.3774 | -0.1517 | -2.158 | -2.154 | 0.05238 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:INV10 | A4b | 0.09184 | 2.006 | 0.9432 | 0.4116 | 0.9334 | -0.2626 | -2.811 | -2.811 | -0.1169 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:INV10 | A4b_CVRv5 | -0.04528 | 1.615 | 0.6931 | 0.3465 | 0.5371 | -0.2457 | -2.459 | -2.458 | -0.08536 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:INV10 | M_mean3_v2 | -0.3897 | 1.89 | 0.6242 | 0.357 | 0.6467 | 0.1723 | 0.3531 | 0.3576 | -0.05052 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:INV10 | M_mean3_v2_CVRv5 | -0.809 | 0.5047 | -0.2246 | 0.3151 | -0.247 | -0.006325 | 0.393 | 0.398 | -0.03671 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:INV10 | M_union3_v2 | -0.4608 | 1.962 | 0.6171 | 0.3282 | -0.5015 | 0.2767 | -0.2323 | -0.2292 | 0.1127 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:INV10 | M_union3_v2_CVRv5 | -0.3102 | 2.045 | 0.7373 | 0.304 | -0.4086 | 0.3077 | -0.2374 | -0.2346 | 0.1245 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:LAG1_10 | A4b | 0.1383 | 2.162 | 1.038 | 0.4037 | 1.033 | -0.1673 | -3.483 | -3.483 | -0.09052 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:LAG1_10 | A4b_CVRv5 | 0.03265 | 1.903 | 0.8646 | 0.3395 | 0.7819 | -0.07418 | -3.481 | -3.481 | -0.07684 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:LAG1_10 | M_mean3_v2 | -0.3627 | 1.681 | 0.5466 | 0.3489 | 0.5622 | 0.09462 | 0.3449 | 0.3498 | -0.04079 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:LAG1_10 | M_mean3_v2_CVRv5 | -0.7326 | 0.4396 | -0.2111 | 0.311 | -0.2218 | 0.007179 | 0.3373 | 0.3429 | -0.03144 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:LAG1_10 | M_union3_v2 | -0.6057 | 1.253 | 0.2212 | 0.2692 | -0.3962 | -0.1192 | -1.878 | -1.875 | 0.04895 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:LAG1_10 | M_union3_v2_CVRv5 | -0.3513 | 1.269 | 0.3695 | 0.2455 | -0.2736 | -0.06009 | -1.91 | -1.908 | 0.05466 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:NATIVE | A4b | 0.3977 | 2.214 | 1.206 | 0.3902 | 1.199 |  | -1.295 | -1.295 | -0.07523 | SECOND_EVALUATION_SAME_HISTORY |
| Q0:NATIVE | A4b_CVRv5 | 0.4331 | 1.57 | 0.9388 | 0.3209 | 0.8284 |  | -1.291 | -1.291 | -0.06069 | SECOND_EVALUATION_SAME_HISTORY |
| Q0:NATIVE | M_mean3_v2 | -0.3245 | 1.421 | 0.452 | 0.3357 | 0.4689 |  | 0.4256 | 0.4314 | -0.03702 | SECOND_EVALUATION_SAME_HISTORY |
| Q0:NATIVE | M_mean3_v2_CVRv5 | -0.6739 | 0.3503 | -0.2183 | 0.301 | -0.229 |  | 0.4234 | 0.4301 | -0.02776 | SECOND_EVALUATION_SAME_HISTORY |
| Q0:NATIVE | M_union3_v2 | -0.298 | 1.137 | 0.3403 | 0.2717 | -0.2449 |  | -1.387 | -1.384 | 0.04137 | SECOND_EVALUATION_SAME_HISTORY |
| Q0:NATIVE | M_union3_v2_CVRv5 | -0.05806 | 1.038 | 0.4296 | 0.25 | -0.1643 |  | -1.45 | -1.447 | 0.04564 | SECOND_EVALUATION_SAME_HISTORY |
| Q_D3:NATIVE | A4b | -0.1517 | 1.541 | 0.6013 | 0.3584 | 0.6128 |  | 2.108 | 2.11 | -0.04832 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D3:NATIVE | A4b_CVRv5 | -0.2358 | 0.8792 | 0.2602 | 0.2959 | 0.1375 |  | 2.12 | 2.122 | -0.03443 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D3:NATIVE | M_mean3_v2 | -0.5718 | 1.407 | 0.3084 | 0.3563 | 0.3402 |  | 1.31 | 1.316 | -0.0378 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D3:NATIVE | M_mean3_v2_CVRv5 | -0.9794 | 0.3604 | -0.3834 | 0.3205 | -0.409 |  | 1.294 | 1.3 | -0.02913 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D3:NATIVE | M_union3_v2 | -0.6772 | 0.4805 | -0.1622 | 0.2624 | -0.6746 |  | 0.7398 | 0.7459 | 0.02527 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D3:NATIVE | M_union3_v2_CVRv5 | -0.4932 | 0.4557 | -0.07108 | 0.2407 | -0.5857 |  | 0.6863 | 0.6926 | 0.0292 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:HG10 | A4b | -0.01157 | 1.595 | 0.703 | 0.3994 | 0.7037 | 0.2966 | 1.96 | 1.963 | -0.06867 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:HG10 | A4b_CVRv5 | 0.1402 | 1.136 | 0.5834 | 0.3158 | 0.4337 | 0.4301 | 1.972 | 1.975 | -0.05112 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:HG10 | M_mean3_v2 | -0.8713 | 1.457 | 0.1642 | 0.4118 | 0.2025 | -0.05472 | 1.432 | 1.436 | -0.04471 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:HG10 | M_mean3_v2_CVRv5 | -1.033 | 0.3758 | -0.4064 | 0.3739 | -0.4312 | -0.04149 | 1.405 | 1.41 | -0.03549 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:HG10 | M_union3_v2 | -0.6587 | 0.6147 | -0.09219 | 0.3136 | -0.7888 | 0.2919 | 1.113 | 1.119 | 0.04373 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:HG10 | M_union3_v2_CVRv5 | -0.363 | 0.5984 | 0.06466 | 0.2845 | -0.6325 | 0.2551 | 1.049 | 1.055 | 0.04973 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:NATIVE | A4b | -0.2594 | 1.237 | 0.4063 | 0.3884 | 0.4165 |  | 2.658 | 2.66 | -0.05101 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:NATIVE | A4b_CVRv5 | -0.2063 | 0.6019 | 0.1533 | 0.3115 | 0.04948 |  | 2.667 | 2.669 | -0.03673 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:NATIVE | M_mean3_v2 | -0.5761 | 1.211 | 0.219 | 0.3945 | 0.2478 |  | 1.485 | 1.49 | -0.03897 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:NATIVE | M_mean3_v2_CVRv5 | -0.8429 | 0.2316 | -0.3649 | 0.3617 | -0.3918 |  | 1.472 | 1.477 | -0.03007 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:NATIVE | M_union3_v2 | -0.8695 | 0.2216 | -0.3841 | 0.2933 | -0.9581 |  | 1.178 | 1.183 | 0.03369 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:NATIVE | M_union3_v2_CVRv5 | -0.5732 | 0.2873 | -0.1904 | 0.2625 | -0.7627 |  | 1.096 | 1.102 | 0.03703 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:HG10 | A4b | 0.03516 | 2.036 | 0.9253 | 0.4101 | 0.922 | 0.03776 | 1.695 | 1.697 | -0.08867 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:HG10 | A4b_CVRv5 | 0.01403 | 1.342 | 0.605 | 0.3297 | 0.4425 | 0.1314 | 1.722 | 1.725 | -0.06855 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:HG10 | M_mean3_v2 | -0.6274 | 1.143 | 0.16 | 0.4102 | 0.1963 | -0.02105 | 1.444 | 1.45 | -0.05114 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:HG10 | M_mean3_v2_CVRv5 | -0.9711 | 0.1766 | -0.4606 | 0.3729 | -0.5019 | 0.03575 | 1.42 | 1.427 | -0.04104 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:HG10 | M_union3_v2 | -0.6778 | 0.7305 | -0.05129 | 0.3304 | -0.9287 | 0.02084 | 0.9563 | 0.9634 | 0.0528 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:HG10 | M_union3_v2_CVRv5 | -0.3797 | 0.6763 | 0.09008 | 0.3012 | -0.7903 | 0.03229 | 0.9175 | 0.9248 | 0.06093 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:NATIVE | A4b | 0.173 | 1.779 | 0.8875 | 0.4027 | 0.9008 |  | 2.584 | 2.585 | -0.06533 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:NATIVE | A4b_CVRv5 | 0.03961 | 1.015 | 0.4735 | 0.3212 | 0.3339 |  | 2.616 | 2.618 | -0.04856 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:NATIVE | M_mean3_v2 | -0.6521 | 1.221 | 0.1811 | 0.3859 | 0.2092 |  | 1.49 | 1.495 | -0.04512 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:NATIVE | M_mean3_v2_CVRv5 | -0.9842 | 0.1125 | -0.4963 | 0.3505 | -0.527 |  | 1.475 | 1.482 | -0.03546 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:NATIVE | M_union3_v2 | -0.6071 | 0.5955 | -0.07213 | 0.3023 | -0.7988 |  | 1.118 | 1.123 | 0.04413 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:NATIVE | M_union3_v2_CVRv5 | -0.3832 | 0.608 | 0.05779 | 0.2736 | -0.6771 |  | 1.069 | 1.074 | 0.0501 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:HG10 | A4b | -0.3113 | 1.645 | 0.5592 | 0.4432 | 0.56 | 0.2449 | -3.357 | -3.354 | -0.06096 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:HG10 | A4b_CVRv5 | -0.09291 | 1.399 | 0.571 | 0.369 | 0.5205 | 0.1754 | -3.327 | -3.323 | -0.05348 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:HG10 | M_mean3_v2 | -0.6061 | 1.352 | 0.265 | 0.3737 | 0.2785 | 0.009278 | -0.3019 | -0.3005 | -0.03575 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:HG10 | M_mean3_v2_CVRv5 | -0.6336 | 0.4593 | -0.1474 | 0.3386 | -0.1685 | -0.01113 | -0.3242 | -0.3228 | -0.02865 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:HG10 | M_union3_v2 | -0.9267 | 0.3342 | -0.3658 | 0.2763 | -0.6574 | -0.04189 | -1.711 | -1.706 | 0.01241 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:HG10 | M_union3_v2_CVRv5 | -0.6591 | 0.06846 | -0.3354 | 0.2501 | -0.6218 | -0.138 | -1.808 | -1.803 | 0.01351 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:NATIVE | A4b | -0.3778 | 1.178 | 0.3143 | 0.4142 | 0.32 |  | -2.184 | -2.183 | -0.04376 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:NATIVE | A4b_CVRv5 | -0.1556 | 1.084 | 0.3956 | 0.3435 | 0.3483 |  | -2.152 | -2.151 | -0.03797 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:NATIVE | M_mean3_v2 | -0.4629 | 1.153 | 0.2557 | 0.3552 | 0.2684 |  | -0.2086 | -0.2048 | -0.03093 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:NATIVE | M_mean3_v2_CVRv5 | -0.5862 | 0.4252 | -0.1363 | 0.3266 | -0.1543 |  | -0.2248 | -0.2206 | -0.02408 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:NATIVE | M_union3_v2 | -0.7417 | 0.1975 | -0.3239 | 0.2746 | -0.5198 |  | -1.352 | -1.348 | 0.004155 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:NATIVE | M_union3_v2_CVRv5 | -0.3878 | 0.04022 | -0.1974 | 0.2447 | -0.3878 |  | -1.462 | -1.459 | 0.003894 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |


> 表头：主体=α .125 邻域｜算子=12 配方｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=nbhd72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-NBHD72


| recipe | mother | D_2010-2014 | D_2015-2018 | D_deriv_ann_pp | se_H | D_sc | D_vs_native | port_size_lo_T_segavg_pct_pt | port_size_hi_T_segavg_pct_pt | turn_rel | evidence_exposure |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Q0:DECAY5_10 | A4b | 0.3229 | 0.5097 | 0.406 | 0.1322 | 0.4015 | 0.1945 | -1.151 | -1.151 | -0.01575 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:DECAY5_10 | A4b_CVRv5 | 0.3101 | 0.5381 | 0.4115 | 0.1133 | 0.3885 | 0.2381 | -1.156 | -1.156 | -0.0133 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:DECAY5_10 | M_mean3_v2 | 0.01794 | 0.5074 | 0.2357 | 0.1657 | 0.2318 | -0.2584 | -0.04763 | -0.047 | -0.02007 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:DECAY5_10 | M_mean3_v2_CVRv5 | -0.1528 | -0.04349 | -0.1042 | 0.1487 | -0.1145 | -0.3082 | -0.05371 | -0.053 | -0.01639 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:DECAY5_10 | M_union3_v2 | 0.1613 | 0.2863 | 0.2169 | 0.09122 | 0.06153 | 0.2026 | -0.3589 | -0.3585 | 0.01491 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:DECAY5_10 | M_union3_v2_CVRv5 | 0.1834 | 0.2858 | 0.229 | 0.0864 | 0.07677 | 0.2142 | -0.331 | -0.3307 | 0.01778 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:HG10 | A4b | 0.3175 | 0.5496 | 0.4207 | 0.1321 | 0.416 | 0.2093 | -1.142 | -1.142 | -0.01571 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:HG10 | A4b_CVRv5 | 0.3091 | 0.5672 | 0.4239 | 0.1131 | 0.3984 | 0.2505 | -1.146 | -1.146 | -0.01313 | SECOND_EVALUATION_SAME_HISTORY |
| Q0:HG10 | M_mean3_v2 | 0.01512 | 0.5419 | 0.2495 | 0.1646 | 0.246 | -0.2446 | -0.04572 | -0.04509 | -0.0201 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:HG10 | M_mean3_v2_CVRv5 | -0.1419 | 0.005742 | -0.07622 | 0.1474 | -0.08756 | -0.2802 | -0.05269 | -0.05198 | -0.01648 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:HG10 | M_union3_v2 | 0.1591 | 0.293 | 0.2186 | 0.09346 | 0.06608 | 0.2043 | -0.3483 | -0.3479 | 0.01472 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:HG10 | M_union3_v2_CVRv5 | 0.1884 | 0.2789 | 0.2287 | 0.08802 | 0.07762 | 0.2139 | -0.3201 | -0.3198 | 0.01766 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:INV10 | A4b | 0.1567 | 0.5674 | 0.3394 | 0.1389 | 0.3417 | 0.1279 | -1.072 | -1.072 | -0.02446 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:INV10 | A4b_CVRv5 | 0.08795 | 0.6237 | 0.3263 | 0.1152 | 0.2888 | 0.1529 | -1.028 | -1.028 | -0.01645 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:INV10 | M_mean3_v2 | -0.0355 | 0.4216 | 0.1678 | 0.1671 | 0.1691 | -0.3262 | -0.03386 | -0.03261 | -0.02593 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:INV10 | M_mean3_v2_CVRv5 | -0.1098 | -0.1202 | -0.1144 | 0.1526 | -0.1306 | -0.3185 | 0.02453 | 0.02602 | -0.01763 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:INV10 | M_union3_v2 | -0.009 | 0.6473 | 0.2829 | 0.119 | -0.1194 | 0.2686 | 0.5117 | 0.5125 | 0.04806 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:INV10 | M_union3_v2_CVRv5 | -0.007749 | 0.6733 | 0.2952 | 0.1167 | -0.1001 | 0.2805 | 0.5692 | 0.5699 | 0.05298 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:LAG1_10 | A4b | 0.3301 | 0.5085 | 0.4094 | 0.1339 | 0.4056 | 0.198 | -1.121 | -1.121 | -0.01542 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:LAG1_10 | A4b_CVRv5 | 0.3152 | 0.5784 | 0.4323 | 0.1116 | 0.4041 | 0.2589 | -1.123 | -1.123 | -0.01274 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:LAG1_10 | M_mean3_v2 | 0.1041 | 0.3661 | 0.2207 | 0.1577 | 0.2167 | -0.2734 | -0.05324 | -0.05209 | -0.0193 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:LAG1_10 | M_mean3_v2_CVRv5 | -0.04512 | -0.07595 | -0.05884 | 0.143 | -0.07364 | -0.2629 | -0.05855 | -0.0572 | -0.01576 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:LAG1_10 | M_union3_v2 | 0.1217 | 0.2621 | 0.1841 | 0.08528 | 0.01643 | 0.1698 | -0.3585 | -0.3581 | 0.01542 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:LAG1_10 | M_union3_v2_CVRv5 | 0.1558 | 0.307 | 0.2231 | 0.0815 | 0.05698 | 0.2083 | -0.337 | -0.3368 | 0.01784 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q0:NATIVE | A4b | 0.1992 | 0.2267 | 0.2115 | 0.0989 | 0.2153 |  | -0.7294 | -0.7294 | -0.008809 | SECOND_EVALUATION_SAME_HISTORY |
| Q0:NATIVE | A4b_CVRv5 | 0.126 | 0.2326 | 0.1734 | 0.08542 | 0.1673 |  | -0.732 | -0.732 | -0.007743 | SECOND_EVALUATION_SAME_HISTORY |
| Q0:NATIVE | M_mean3_v2 | 0.3043 | 0.7309 | 0.4941 | 0.1365 | 0.4891 |  | 0.002744 | 0.004435 | -0.01342 | SECOND_EVALUATION_SAME_HISTORY |
| Q0:NATIVE | M_mean3_v2_CVRv5 | 0.1464 | 0.2759 | 0.204 | 0.1202 | 0.2007 |  | 0.005935 | 0.00788 | -0.01082 | SECOND_EVALUATION_SAME_HISTORY |
| Q0:NATIVE | M_union3_v2 | 0.01589 | 0.01237 | 0.01432 | 0.06376 | -0.08953 |  | -0.2202 | -0.2199 | 0.009736 | SECOND_EVALUATION_SAME_HISTORY |
| Q0:NATIVE | M_union3_v2_CVRv5 | -0.009969 | 0.04562 | 0.01476 | 0.0586 | -0.08996 |  | -0.217 | -0.2168 | 0.0103 | SECOND_EVALUATION_SAME_HISTORY |
| Q_D3:NATIVE | A4b | 0.1785 | 0.3255 | 0.2439 | 0.095 | 0.2464 |  | -0.2167 | -0.2166 | -0.005376 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D3:NATIVE | A4b_CVRv5 | 0.1238 | 0.2565 | 0.1828 | 0.07864 | 0.1721 |  | -0.2223 | -0.2223 | -0.004286 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D3:NATIVE | M_mean3_v2 | 0.02004 | 0.4216 | 0.1987 | 0.1286 | 0.203 |  | 0.2217 | 0.2234 | -0.01264 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D3:NATIVE | M_mean3_v2_CVRv5 | -0.1274 | 0.1135 | -0.02023 | 0.1154 | -0.03391 |  | 0.2209 | 0.2229 | -0.009909 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D3:NATIVE | M_union3_v2 | -0.1464 | -0.1582 | -0.1517 | 0.07379 | -0.2792 |  | 0.1887 | 0.1892 | 0.01322 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D3:NATIVE | M_union3_v2_CVRv5 | -0.09292 | -0.06597 | -0.08093 | 0.06745 | -0.2152 |  | 0.2009 | 0.2013 | 0.01436 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:HG10 | A4b | 0.2395 | 0.5642 | 0.3839 | 0.1118 | 0.3833 | 0.07028 | -0.5571 | -0.5571 | -0.01184 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:HG10 | A4b_CVRv5 | 0.2869 | 0.5129 | 0.3874 | 0.09585 | 0.3608 | 0.1103 | -0.5527 | -0.5527 | -0.009593 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:HG10 | M_mean3_v2 | -0.08173 | 0.5415 | 0.1955 | 0.1638 | 0.1995 | -0.002606 | 0.2156 | 0.2162 | -0.01911 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:HG10 | M_mean3_v2_CVRv5 | -0.1646 | 0.1312 | -0.03299 | 0.1472 | -0.04124 | -0.0377 | 0.2126 | 0.2132 | -0.01578 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:HG10 | M_union3_v2 | 0.0471 | 0.2847 | 0.1528 | 0.09235 | -0.05658 | 0.1714 | 0.213 | 0.2135 | 0.02303 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:HG10 | M_union3_v2_CVRv5 | 0.1253 | 0.3101 | 0.2075 | 0.08702 | 0.003661 | 0.2003 | 0.2266 | 0.227 | 0.02563 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:NATIVE | A4b | 0.1134 | 0.5635 | 0.3136 | 0.09226 | 0.3157 |  | -0.1731 | -0.1731 | -0.005818 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:NATIVE | A4b_CVRv5 | 0.0818 | 0.5209 | 0.2771 | 0.07575 | 0.2655 |  | -0.1717 | -0.1716 | -0.004905 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:NATIVE | M_mean3_v2 | -0.03421 | 0.488 | 0.1981 | 0.1335 | 0.1935 |  | 0.2712 | 0.2723 | -0.01217 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:NATIVE | M_mean3_v2_CVRv5 | -0.15 | 0.1977 | 0.004708 | 0.1218 | -0.01592 |  | 0.2753 | 0.2766 | -0.009732 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:NATIVE | M_union3_v2 | -0.09015 | 0.07068 | -0.0186 | 0.07733 | -0.1721 |  | 0.2771 | 0.2777 | 0.01494 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_D5:NATIVE | M_union3_v2_CVRv5 | -0.05692 | 0.08713 | 0.007161 | 0.07051 | -0.1428 |  | 0.2764 | 0.277 | 0.0164 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:HG10 | A4b | 0.3201 | 0.585 | 0.438 | 0.1176 | 0.4375 | 0.2429 | -0.6223 | -0.6223 | -0.01343 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:HG10 | A4b_CVRv5 | 0.2757 | 0.4607 | 0.358 | 0.09461 | 0.3326 | 0.1518 | -0.6277 | -0.6277 | -0.01111 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:HG10 | M_mean3_v2 | -0.08212 | 0.5088 | 0.1808 | 0.1643 | 0.1846 | -0.05939 | 0.2099 | 0.2105 | -0.02051 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:HG10 | M_mean3_v2_CVRv5 | -0.2086 | 0.06276 | -0.08789 | 0.1471 | -0.1022 | -0.08525 | 0.211 | 0.2117 | -0.01676 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:HG10 | M_union3_v2 | 0.01543 | 0.262 | 0.1251 | 0.1023 | -0.1054 | 0.2252 | 0.195 | 0.1956 | 0.02636 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:HG10 | M_union3_v2_CVRv5 | 0.06295 | 0.2553 | 0.1485 | 0.0938 | -0.07492 | 0.2081 | 0.213 | 0.2135 | 0.02915 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:NATIVE | A4b | 0.1726 | 0.2231 | 0.195 | 0.09755 | 0.1982 |  | -0.227 | -0.227 | -0.006374 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:NATIVE | A4b_CVRv5 | 0.1456 | 0.2818 | 0.2062 | 0.08286 | 0.1955 |  | -0.2257 | -0.2257 | -0.005255 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:NATIVE | M_mean3_v2 | 0.05354 | 0.473 | 0.2401 | 0.1385 | 0.2411 |  | 0.2594 | 0.2611 | -0.01374 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:NATIVE | M_mean3_v2_CVRv5 | -0.1044 | 0.1244 | -0.002641 | 0.1234 | -0.02176 |  | 0.2597 | 0.2617 | -0.01076 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:NATIVE | M_union3_v2 | -0.09819 | -0.1024 | -0.1001 | 0.07927 | -0.2542 |  | 0.2723 | 0.2729 | 0.01763 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_DEW5:NATIVE | M_union3_v2_CVRv5 | -0.07373 | -0.04205 | -0.05963 | 0.07324 | -0.2143 |  | 0.2843 | 0.2848 | 0.01929 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:HG10 | A4b | 0.1843 | 0.3293 | 0.2488 | 0.1157 | 0.2483 | -0.1233 | -1.068 | -1.068 | -0.01333 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:HG10 | A4b_CVRv5 | 0.2203 | 0.3127 | 0.2614 | 0.09907 | 0.2526 | -0.06067 | -1.067 | -1.067 | -0.01233 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:HG10 | M_mean3_v2 | 0.01862 | 0.5143 | 0.2391 | 0.1585 | 0.2413 | -0.05429 | -0.1717 | -0.1711 | -0.01758 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:HG10 | M_mean3_v2_CVRv5 | -0.09771 | 0.1761 | 0.02409 | 0.1457 | 0.01101 | -0.117 | -0.1697 | -0.169 | -0.01471 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:HG10 | M_union3_v2 | 0.02091 | 0.06848 | 0.04207 | 0.0845 | -0.1137 | 0.1994 | -0.24 | -0.2396 | 0.01713 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:HG10 | M_union3_v2_CVRv5 | 0.08998 | 0.1571 | 0.1199 | 0.07879 | -0.03003 | 0.2627 | -0.2311 | -0.2308 | 0.01929 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:NATIVE | A4b | 0.2286 | 0.5511 | 0.3721 | 0.09576 | 0.3703 |  | -0.6311 | -0.6311 | -0.007515 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:NATIVE | A4b_CVRv5 | 0.1762 | 0.5041 | 0.3221 | 0.08258 | 0.3178 |  | -0.6282 | -0.6282 | -0.006917 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:NATIVE | M_mean3_v2 | 0.1052 | 0.5284 | 0.2934 | 0.1258 | 0.2916 |  | -0.09919 | -0.09861 | -0.01067 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:NATIVE | M_mean3_v2_CVRv5 | 0.04997 | 0.2547 | 0.141 | 0.1142 | 0.1247 |  | -0.09462 | -0.09397 | -0.008415 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:NATIVE | M_union3_v2 | -0.1988 | -0.1055 | -0.1573 | 0.07848 | -0.2413 |  | -0.154 | -0.1537 | 0.008227 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |
| Q_RANK5:NATIVE | M_union3_v2_CVRv5 | -0.1693 | -0.1097 | -0.1428 | 0.07042 | -0.2223 |  | -0.1646 | -0.1643 | 0.009202 | NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY |


## 3. 全部登记描述符按 族 × 算子 × α 的分布（汇总测量 × 母体 × H1…20）

> 表头：主体=全部登记描述符（不含 PARENT）｜算子=各算子｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=按族 × 算子 × α｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=H 1…20｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-GRID


| family | op | alpha | cells | share_pos | q10_ann_pp | median_ann_pp | q90_ann_pp | median_vs_native_ann_pp | median_vs_Q0_ann_pp |
|---|---|---|---|---|---|---|---|---|---|
| HG | HG10 | 0.125 | 1920 | 0.9656 | 0.07727 | 0.1594 | 0.403 | 0.07053 | -0.03292 |
| HG | HG10 | 0.25 | 1920 | 0.9714 | 0.08148 | 0.2477 | 0.5663 | 0.09006 | -0.08128 |
| HG | HG10 | 0.5 | 1920 | 0.8318 | -0.08174 | 0.2493 | 0.8771 | 0.06777 | -0.2289 |
| HG | HG15 | 0.125 | 1440 | 0.9583 | 0.08369 | 0.1681 | 0.3901 | 0.08975 | -0.04169 |
| HG | HG15 | 0.25 | 1440 | 0.9701 | 0.1148 | 0.2586 | 0.5575 | 0.1097 | -0.07989 |
| HG | HG15 | 0.5 | 1440 | 0.8097 | -0.1193 | 0.2243 | 0.7632 | 0.06177 | -0.2667 |
| HG | HG20 | 0.125 | 360 | 0.9611 | 0.08332 | 0.1724 | 0.3577 | 0.075 | -0.0264 |
| HG | HG20 | 0.25 | 360 | 0.9611 | 0.08631 | 0.2829 | 0.5836 | 0.0931 | -0.09402 |
| HG | HG20 | 0.5 | 360 | 0.9139 | 0.00896 | 0.3433 | 0.847 | 0.06184 | -0.2688 |
| HG | HG30 | 0.125 | 360 | 0.95 | 0.0615 | 0.2159 | 0.4082 | 0.1026 | 0.01377 |
| HG | HG30 | 0.25 | 360 | 0.9389 | 0.04441 | 0.3102 | 0.6432 | 0.1576 | -0.205 |
| HG | HG30 | 0.5 | 360 | 0.8722 | -0.09191 | 0.3474 | 0.769 | 0.06273 | -0.2048 |
| HG | HG5 | 0.125 | 1440 | 0.9812 | 0.05355 | 0.141 | 0.3382 | 0.0526 | -0.05477 |
| HG | HG5 | 0.25 | 1440 | 0.9681 | 0.05408 | 0.1958 | 0.4829 | 0.04847 | -0.07616 |
| HG | HG5 | 0.5 | 1440 | 0.8042 | -0.1161 | 0.1747 | 0.7207 | 0.03322 | -0.2902 |
| MEMORY | DECAY2_10 | 0.125 | 480 | 0.9667 | 0.05492 | 0.1575 | 0.3872 | 0.05716 | -0.05321 |
| MEMORY | DECAY2_10 | 0.25 | 480 | 0.9729 | 0.06478 | 0.2369 | 0.5166 | 0.06892 | -0.1039 |
| MEMORY | DECAY2_10 | 0.5 | 480 | 0.8708 | -0.02966 | 0.241 | 0.8575 | 0.03952 | -0.2385 |
| MEMORY | DECAY5_10 | 0.125 | 480 | 0.9583 | 0.05836 | 0.1561 | 0.3931 | 0.06287 | -0.04983 |
| MEMORY | DECAY5_10 | 0.25 | 480 | 0.9729 | 0.07136 | 0.2423 | 0.5384 | 0.07436 | -0.1058 |
| MEMORY | DECAY5_10 | 0.5 | 480 | 0.8958 | -0.003536 | 0.255 | 0.8723 | 0.05381 | -0.254 |
| MEMORY | INV10 | 0.125 | 480 | 0.9521 | 0.04877 | 0.1897 | 0.4096 | 0.08246 | -0.03277 |
| MEMORY | INV10 | 0.25 | 480 | 0.9833 | 0.1003 | 0.252 | 0.6079 | 0.07387 | -0.05148 |
| MEMORY | INV10 | 0.5 | 480 | 0.9313 | 0.02254 | 0.373 | 0.8705 | 0.135 | -0.2601 |
| MEMORY | LAG1_10 | 0.125 | 480 | 0.9833 | 0.06992 | 0.1591 | 0.3562 | 0.06356 | -0.05551 |
| MEMORY | LAG1_10 | 0.25 | 480 | 0.9708 | 0.06534 | 0.2388 | 0.5124 | 0.05788 | -0.06379 |
| MEMORY | LAG1_10 | 0.5 | 480 | 0.8812 | -0.01688 | 0.2409 | 0.8384 | 0.04677 | -0.2556 |
| NATIVE | NATIVE | 0.125 | 480 | 0.9854 | 0.03415 | 0.1299 | 0.321 |  | 0.001854 |
| NATIVE | NATIVE | 0.25 | 480 | 0.9854 | 0.09215 | 0.214 | 0.5039 |  | -0.002081 |
| NATIVE | NATIVE | 0.5 | 480 | 0.9292 | 0.05467 | 0.4 | 0.9938 |  | -0.1203 |
| OLD_RULE | DECAY2_10 | 0 | 120 | 0.9083 | 0.002593 | 0.0999 | 0.2484 |  |  |
| OLD_RULE | DECAY5_10 | 0 | 120 | 0.925 | 0.01645 | 0.09394 | 0.252 |  |  |
| OLD_RULE | HG10 | 0 | 120 | 0.9333 | 0.02681 | 0.1007 | 0.2497 |  |  |
| OLD_RULE | HG15 | 0 | 120 | 0.7667 | -0.04943 | 0.07602 | 0.2422 |  |  |
| OLD_RULE | HG20 | 0 | 120 | 0.95 | 0.01546 | 0.1148 | 0.2662 |  |  |
| OLD_RULE | HG30 | 0 | 120 | 0.9583 | 0.02806 | 0.156 | 0.3852 |  |  |
| OLD_RULE | HG5 | 0 | 120 | 0.8167 | -0.007566 | 0.02825 | 0.1275 |  |  |
| OLD_RULE | INV10 | 0 | 120 | 0.9 | 0.002013 | 0.1165 | 0.2856 |  |  |
| OLD_RULE | LAG1_10 | 0 | 120 | 0.9333 | 0.0229 | 0.0858 | 0.2542 |  |  |
| OLD_RULE | VOL_HI15 | 0 | 120 | 0.4917 | -0.05955 | -0.001219 | 0.06193 |  |  |
| OLD_RULE | VOL_HI5 | 0 | 120 | 0.9667 | 0.03182 | 0.09574 | 0.3032 |  |  |
| OLD_RULE | VOL_MEAN15 | 0 | 120 | 0.95 | 0.03619 | 0.07907 | 0.2095 |  |  |
| OLD_RULE | VOL_MEAN5 | 0 | 120 | 0.7833 | -0.03309 | 0.1003 | 0.3218 |  |  |
| SMOOTH | NATIVE | 0.125 | 1440 | 0.8083 | -0.02405 | 0.0982 | 0.2531 |  | -0.05252 |
| SMOOTH | NATIVE | 0.25 | 1440 | 0.8569 | -0.01802 | 0.1457 | 0.3759 |  | -0.08637 |
| SMOOTH | NATIVE | 0.5 | 1440 | 0.6854 | -0.152 | 0.09184 | 0.5394 |  | -0.3414 |
| STATE | VOL_HI15 | 0.125 | 360 | 0.9694 | 0.04347 | 0.1572 | 0.3034 | 0.03564 | -0.08334 |
| STATE | VOL_HI15 | 0.25 | 360 | 0.9806 | 0.07492 | 0.2291 | 0.5424 | 0.05644 | -0.1205 |
| STATE | VOL_HI15 | 0.5 | 360 | 0.9139 | 0.01621 | 0.2897 | 0.9188 | 0.06112 | -0.2928 |
| STATE | VOL_HI5 | 0.125 | 360 | 0.9833 | 0.06035 | 0.1662 | 0.4345 | 0.07296 | -0.049 |
| STATE | VOL_HI5 | 0.25 | 360 | 0.9722 | 0.0923 | 0.2479 | 0.5738 | 0.08036 | -0.1135 |
| STATE | VOL_HI5 | 0.5 | 360 | 0.9111 | 0.007226 | 0.3123 | 0.7651 | 0.03719 | -0.2457 |
| STATE | VOL_MEAN15 | 0.125 | 360 | 0.9667 | 0.05091 | 0.1482 | 0.3665 | 0.03556 | -0.06949 |
| STATE | VOL_MEAN15 | 0.25 | 360 | 0.9639 | 0.07252 | 0.252 | 0.5707 | 0.08622 | -0.1238 |
| STATE | VOL_MEAN15 | 0.5 | 360 | 0.9167 | 0.01576 | 0.2829 | 0.9139 | 0.04804 | -0.2309 |
| STATE | VOL_MEAN5 | 0.125 | 360 | 0.9417 | 0.05064 | 0.1522 | 0.3996 | 0.05894 | -0.02999 |
| STATE | VOL_MEAN5 | 0.25 | 360 | 0.9833 | 0.07688 | 0.2402 | 0.5802 | 0.07676 | -0.1268 |
| STATE | VOL_MEAN5 | 0.5 | 360 | 0.9222 | 0.02228 | 0.3019 | 0.8762 | 0.03528 | -0.2592 |


## 4. 机制账户（比较层：日层先闭合再段均；推导段合并）

> 表头：主体=信息 × 规则交互 Y11 − Y10 − Y01 + Y00（Y00 原父 / Y10 新测量无规则 / Y01 旧 K 规则 / Y11 新测量规则）｜算子=FOUR_ACCOUNT_INFO_RULE｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=各端原生｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-INFO-RULE


| meas | right_meas | op | right_op | alpha | cells | median_D_ann_pp | share_pos | median_Dg_ann_pp | median_fee_ann_pp | median_se_H_ann_pp |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | C1 | DECAY2_10 | NATIVE | a0.125 | 6 | -0.06216 | 0.1667 | -0.06296 | 4.053e-05 | 0.09715 |
| C1 | C1 | DECAY2_10 | NATIVE | a0.25 | 6 | -0.04847 | 0.3333 | -0.04799 | -3.463e-05 | 0.1202 |
| C1 | C1 | DECAY2_10 | NATIVE | a0.5 | 6 | -0.07169 | 0.1667 | -0.07113 | -8.603e-05 | 0.1351 |
| C1 | C1 | DECAY5_10 | NATIVE | a0.125 | 6 | -0.08544 | 0.1667 | -0.08623 | -8.741e-07 | 0.09852 |
| C1 | C1 | DECAY5_10 | NATIVE | a0.25 | 6 | -0.05898 | 0.3333 | -0.05877 | -0.0001348 | 0.1205 |
| C1 | C1 | DECAY5_10 | NATIVE | a0.5 | 6 | -0.07658 | 0.1667 | -0.07608 | -3.9e-05 | 0.136 |
| C1 | C1 | HG10 | NATIVE | a0.125 | 6 | -0.09236 | 0 | -0.09323 | 0.0001921 | 0.09777 |
| C1 | C1 | HG10 | NATIVE | a0.25 | 6 | -0.09109 | 0.3333 | -0.09088 | -0.0001987 | 0.1206 |
| C1 | C1 | HG10 | NATIVE | a0.5 | 6 | -0.09861 | 0.1667 | -0.09805 | -8.467e-05 | 0.1385 |
| C1 | C1 | HG15 | NATIVE | a0.125 | 6 | 0.008989 | 0.5 | 0.007728 | 0.00134 | 0.1047 |
| C1 | C1 | HG15 | NATIVE | a0.25 | 6 | -0.1189 | 0.3333 | -0.1205 | 3.67e-05 | 0.1326 |
| C1 | C1 | HG15 | NATIVE | a0.5 | 6 | -0.03495 | 0.3333 | -0.0359 | -0.0006959 | 0.1575 |
| C1 | C1 | HG20 | NATIVE | a0.125 | 6 | 0.02351 | 0.6667 | 0.02293 | 0.0004838 | 0.116 |
| C1 | C1 | HG20 | NATIVE | a0.25 | 6 | -0.03223 | 0.1667 | -0.03346 | 0.000305 | 0.1449 |
| C1 | C1 | HG20 | NATIVE | a0.5 | 6 | -0.09431 | 0 | -0.09455 | -0.000464 | 0.1796 |
| C1 | C1 | HG30 | NATIVE | a0.125 | 6 | -0.1338 | 0.3333 | -0.1336 | 0.0009081 | 0.1173 |
| C1 | C1 | HG30 | NATIVE | a0.25 | 6 | -0.2023 | 0 | -0.2008 | -0.0006935 | 0.1586 |
| C1 | C1 | HG30 | NATIVE | a0.5 | 6 | -0.1085 | 0 | -0.1132 | -0.002115 | 0.2092 |
| C1 | C1 | HG5 | NATIVE | a0.125 | 6 | -0.05586 | 0.3333 | -0.05594 | -8.412e-06 | 0.08323 |
| C1 | C1 | HG5 | NATIVE | a0.25 | 6 | -0.01512 | 0.3333 | -0.01595 | 0.0008471 | 0.09448 |
| C1 | C1 | HG5 | NATIVE | a0.5 | 6 | -0.06098 | 0.3333 | -0.05996 | -0.0004661 | 0.1016 |
| C1 | C1 | INV10 | NATIVE | a0.125 | 6 | -0.00728 | 0.5 | -0.007988 | 0.0005813 | 0.1028 |
| C1 | C1 | INV10 | NATIVE | a0.25 | 6 | -0.04445 | 0.1667 | -0.04532 | 0.002768 | 0.1194 |
| C1 | C1 | INV10 | NATIVE | a0.5 | 6 | -0.03407 | 0.1667 | -0.03126 | 0.004616 | 0.1327 |
| C1 | C1 | LAG1_10 | NATIVE | a0.125 | 6 | -0.06537 | 0.3333 | -0.06563 | 0.0004158 | 0.09305 |
| C1 | C1 | LAG1_10 | NATIVE | a0.25 | 6 | -0.01518 | 0.3333 | -0.01495 | -0.0001929 | 0.1107 |
| C1 | C1 | LAG1_10 | NATIVE | a0.5 | 6 | -0.1107 | 0.3333 | -0.109 | -0.0001726 | 0.1269 |
| C1 | C1 | VOL_HI15 | NATIVE | a0.125 | 6 | 0.01059 | 0.5 | 0.01002 | 0.0004584 | 0.09194 |
| C1 | C1 | VOL_HI15 | NATIVE | a0.25 | 6 | -0.04132 | 0.3333 | -0.04208 | 0.0006551 | 0.1102 |
| C1 | C1 | VOL_HI15 | NATIVE | a0.5 | 6 | 0.04676 | 1 | 0.04792 | -0.0007456 | 0.1246 |
| C1 | C1 | VOL_HI5 | NATIVE | a0.125 | 6 | -0.03256 | 0 | -0.03402 | 0.001298 | 0.09732 |
| C1 | C1 | VOL_HI5 | NATIVE | a0.25 | 6 | -0.06625 | 0.3333 | -0.06833 | 0.0009797 | 0.1192 |
| C1 | C1 | VOL_HI5 | NATIVE | a0.5 | 6 | -0.1141 | 0.1667 | -0.1137 | -2.495e-05 | 0.1393 |
| C1 | C1 | VOL_MEAN15 | NATIVE | a0.125 | 6 | -0.02718 | 0.1667 | -0.02777 | 0.0005831 | 0.09663 |
| C1 | C1 | VOL_MEAN15 | NATIVE | a0.25 | 6 | -0.1508 | 0.3333 | -0.1523 | 0.0005881 | 0.1138 |
| C1 | C1 | VOL_MEAN15 | NATIVE | a0.5 | 6 | -0.03721 | 0.3333 | -0.03691 | 0.0008269 | 0.1328 |
| C1 | C1 | VOL_MEAN5 | NATIVE | a0.125 | 6 | -0.04995 | 0 | -0.05046 | 0.0008323 | 0.1011 |
| C1 | C1 | VOL_MEAN5 | NATIVE | a0.25 | 6 | -0.08445 | 0.3333 | -0.08499 | 7.675e-05 | 0.1222 |
| C1 | C1 | VOL_MEAN5 | NATIVE | a0.5 | 6 | -0.04557 | 0.3333 | -0.04651 | 0.0004754 | 0.1407 |
| M | M | HG10 | NATIVE | a0.125 | 6 | -0.03196 | 0.1667 | -0.03251 | 0.001115 | 0.1034 |
| M | M | HG10 | NATIVE | a0.25 | 6 | -0.1005 | 0.1667 | -0.1034 | 0.002098 | 0.1232 |
| M | M | HG10 | NATIVE | a0.5 | 6 | -0.2052 | 0.1667 | -0.2164 | 0.01099 | 0.1431 |
| Q0 | Q0 | DECAY2_10 | NATIVE | a0.125 | 6 | -0.04609 | 0.3333 | -0.04825 | 0.001772 | 0.1094 |
| Q0 | Q0 | DECAY2_10 | NATIVE | a0.25 | 6 | -0.08384 | 0.5 | -0.08594 | 0.002065 | 0.1249 |
| Q0 | Q0 | DECAY2_10 | NATIVE | a0.5 | 6 | -0.2189 | 0.1667 | -0.2157 | -0.000922 | 0.1614 |
| Q0 | Q0 | DECAY5_10 | NATIVE | a0.125 | 6 | -0.03918 | 0.3333 | -0.04071 | 0.001444 | 0.1083 |
| Q0 | Q0 | DECAY5_10 | NATIVE | a0.25 | 6 | -0.07131 | 0.5 | -0.0733 | 0.00196 | 0.1249 |
| Q0 | Q0 | DECAY5_10 | NATIVE | a0.5 | 6 | -0.1665 | 0.3333 | -0.1659 | 6.418e-06 | 0.1741 |
| Q0 | Q0 | HG10 | NATIVE | a0.125 | 6 | -0.0295 | 0.5 | -0.03073 | 0.001206 | 0.1088 |
| Q0 | Q0 | HG10 | NATIVE | a0.25 | 6 | -0.0884 | 0.3333 | -0.0902 | 0.001768 | 0.1253 |
| Q0 | Q0 | HG10 | NATIVE | a0.5 | 6 | -0.2535 | 0.3333 | -0.2546 | 0.0014 | 0.1755 |
| Q0 | Q0 | HG15 | NATIVE | a0.125 | 6 | -0.02037 | 0.3333 | -0.02347 | 0.002167 | 0.124 |
| Q0 | Q0 | HG15 | NATIVE | a0.25 | 6 | 0.07532 | 0.5 | 0.07525 | 5.978e-05 | 0.1583 |
| Q0 | Q0 | HG15 | NATIVE | a0.5 | 6 | -0.1714 | 0.3333 | -0.1827 | 0.01112 | 0.2103 |
| Q0 | Q0 | HG20 | NATIVE | a0.125 | 6 | -0.08186 | 0.3333 | -0.08606 | 0.002194 | 0.1243 |
| Q0 | Q0 | HG20 | NATIVE | a0.25 | 6 | -0.07675 | 0.3333 | -0.07698 | 0.0002252 | 0.1786 |
| Q0 | Q0 | HG20 | NATIVE | a0.5 | 6 | -0.2083 | 0.1667 | -0.2268 | 0.0182 | 0.2415 |
| Q0 | Q0 | HG30 | NATIVE | a0.125 | 6 | -0.09897 | 0 | -0.1068 | 0.001714 | 0.1336 |
| Q0 | Q0 | HG30 | NATIVE | a0.25 | 6 | -0.1769 | 0.3333 | -0.1989 | 0.01713 | 0.2217 |
| Q0 | Q0 | HG30 | NATIVE | a0.5 | 6 | -0.3366 | 0 | -0.3521 | 0.0319 | 0.2707 |
| Q0 | Q0 | HG5 | NATIVE | a0.125 | 6 | 0.06515 | 0.6667 | 0.06492 | -3.897e-05 | 0.09208 |
| Q0 | Q0 | HG5 | NATIVE | a0.25 | 6 | 0.03518 | 0.6667 | 0.03372 | 0.0001884 | 0.09456 |
| Q0 | Q0 | HG5 | NATIVE | a0.5 | 6 | -0.1 | 0.3333 | -0.09327 | -0.0006433 | 0.1301 |
| Q0 | Q0 | INV10 | NATIVE | a0.125 | 6 | -0.03689 | 0.5 | -0.0382 | 0.00116 | 0.1079 |
| Q0 | Q0 | INV10 | NATIVE | a0.25 | 6 | -0.00905 | 0.5 | -0.01271 | 0.003538 | 0.1341 |
| Q0 | Q0 | INV10 | NATIVE | a0.5 | 6 | 0.1038 | 0.6667 | 0.0977 | 0.005994 | 0.1929 |
| Q0 | Q0 | LAG1_10 | NATIVE | a0.125 | 6 | -0.05065 | 0.3333 | -0.05265 | 0.001317 | 0.1075 |
| Q0 | Q0 | LAG1_10 | NATIVE | a0.25 | 6 | -0.1898 | 0.3333 | -0.1929 | 0.0004692 | 0.1229 |
| Q0 | Q0 | LAG1_10 | NATIVE | a0.5 | 6 | -0.1439 | 0.1667 | -0.1413 | -0.002114 | 0.1398 |
| Q0 | Q0 | VOL_HI15 | NATIVE | a0.125 | 6 | 0.135 | 0.6667 | 0.1347 | 0.000298 | 0.1073 |
| Q0 | Q0 | VOL_HI15 | NATIVE | a0.25 | 6 | 0.1934 | 0.6667 | 0.1928 | 0.0006345 | 0.1264 |
| Q0 | Q0 | VOL_HI15 | NATIVE | a0.5 | 6 | -0.09692 | 0.3333 | -0.09182 | -0.000427 | 0.1739 |
| Q0 | Q0 | VOL_HI5 | NATIVE | a0.125 | 6 | -0.0436 | 0.3333 | -0.04714 | 0.001448 | 0.1066 |
| Q0 | Q0 | VOL_HI5 | NATIVE | a0.25 | 6 | -0.0655 | 0.3333 | -0.07017 | 0.0007187 | 0.1317 |
| Q0 | Q0 | VOL_HI5 | NATIVE | a0.5 | 6 | -0.109 | 0.3333 | -0.1177 | 0.008519 | 0.1735 |
| Q0 | Q0 | VOL_MEAN15 | NATIVE | a0.125 | 6 | 0.04176 | 0.6667 | 0.0402 | 0.0012 | 0.1045 |
| Q0 | Q0 | VOL_MEAN15 | NATIVE | a0.25 | 6 | 0.03494 | 0.5 | 0.03145 | 0.001091 | 0.1165 |
| Q0 | Q0 | VOL_MEAN15 | NATIVE | a0.5 | 6 | -0.1505 | 0.3333 | -0.1494 | 0.0001171 | 0.1634 |
| Q0 | Q0 | VOL_MEAN5 | NATIVE | a0.125 | 6 | -0.1177 | 0.3333 | -0.1205 | 0.00268 | 0.1116 |
| Q0 | Q0 | VOL_MEAN5 | NATIVE | a0.25 | 6 | 0.07921 | 0.5 | 0.08101 | 0.0008216 | 0.136 |
| Q0 | Q0 | VOL_MEAN5 | NATIVE | a0.5 | 6 | -0.2364 | 0.3333 | -0.2408 | 0.004323 | 0.1911 |
| Q_D10 | Q_D10 | HG10 | NATIVE | a0.125 | 6 | 0.01193 | 0.6667 | 0.01064 | 0.001265 | 0.1044 |
| Q_D10 | Q_D10 | HG10 | NATIVE | a0.25 | 6 | 0.06943 | 0.6667 | 0.07324 | 0.002531 | 0.1251 |
| Q_D10 | Q_D10 | HG10 | NATIVE | a0.5 | 6 | -0.1233 | 0 | -0.1335 | 0.0003743 | 0.1442 |
| Q_D10 | Q_D10 | HG15 | NATIVE | a0.125 | 6 | 0.03955 | 0.6667 | 0.04076 | 0.002143 | 0.1111 |
| Q_D10 | Q_D10 | HG15 | NATIVE | a0.25 | 6 | 0.1187 | 1 | 0.1206 | 0.002036 | 0.147 |
| Q_D10 | Q_D10 | HG15 | NATIVE | a0.5 | 6 | -0.06625 | 0.1667 | -0.06546 | 0.002107 | 0.1743 |
| Q_D10 | Q_D10 | HG5 | NATIVE | a0.125 | 6 | 0.06903 | 0.6667 | 0.07017 | -0.0006972 | 0.08804 |
| Q_D10 | Q_D10 | HG5 | NATIVE | a0.25 | 6 | 0.05617 | 0.8333 | 0.05646 | 0.0008286 | 0.09438 |
| Q_D10 | Q_D10 | HG5 | NATIVE | a0.5 | 6 | -0.05386 | 0.1667 | -0.05692 | -0.001291 | 0.1028 |
| Q_D3 | Q_D3 | HG10 | NATIVE | a0.125 | 6 | -0.09106 | 0.3333 | -0.09351 | 0.001612 | 0.1089 |
| Q_D3 | Q_D3 | HG10 | NATIVE | a0.25 | 6 | 0.07446 | 0.6667 | 0.07229 | 0.002135 | 0.126 |
| Q_D3 | Q_D3 | HG10 | NATIVE | a0.5 | 6 | -0.008893 | 0.5 | -0.004783 | 0.001792 | 0.1701 |
| Q_D3 | Q_D3 | HG15 | NATIVE | a0.125 | 6 | 0.06188 | 0.6667 | 0.06017 | 0.00168 | 0.1199 |
| Q_D3 | Q_D3 | HG15 | NATIVE | a0.25 | 6 | 0.09861 | 0.6667 | 0.09562 | 0.002934 | 0.1568 |
| Q_D3 | Q_D3 | HG15 | NATIVE | a0.5 | 6 | 0.03801 | 0.8333 | 0.03687 | 0.0009641 | 0.1837 |
| Q_D3 | Q_D3 | HG5 | NATIVE | a0.125 | 6 | 0.08008 | 0.8333 | 0.07895 | -9.896e-05 | 0.09197 |
| Q_D3 | Q_D3 | HG5 | NATIVE | a0.25 | 6 | 0.02593 | 0.6667 | 0.02569 | 0.0002387 | 0.09595 |
| Q_D3 | Q_D3 | HG5 | NATIVE | a0.5 | 6 | -0.02671 | 0.3333 | -0.02368 | -0.0003693 | 0.1072 |
| Q_D5 | Q_D5 | DECAY2_10 | NATIVE | a0.125 | 6 | -0.008827 | 0.5 | -0.01165 | 0.0004616 | 0.1077 |
| Q_D5 | Q_D5 | DECAY2_10 | NATIVE | a0.25 | 6 | 0.06495 | 0.6667 | 0.06774 | 0.001058 | 0.1299 |
| Q_D5 | Q_D5 | DECAY2_10 | NATIVE | a0.5 | 6 | 0.09395 | 0.8333 | 0.08787 | -0.0004628 | 0.1372 |
| Q_D5 | Q_D5 | DECAY5_10 | NATIVE | a0.125 | 6 | -0.02389 | 0.5 | -0.02685 | 0.0001183 | 0.1092 |
| Q_D5 | Q_D5 | DECAY5_10 | NATIVE | a0.25 | 6 | 0.09624 | 0.8333 | 0.09909 | 0.001169 | 0.1319 |
| Q_D5 | Q_D5 | DECAY5_10 | NATIVE | a0.5 | 6 | 0.146 | 0.8333 | 0.1354 | 0.000286 | 0.143 |
| Q_D5 | Q_D5 | HG10 | NATIVE | a0.125 | 6 | -0.02594 | 0.5 | -0.02857 | 0.0001028 | 0.1098 |
| Q_D5 | Q_D5 | HG10 | NATIVE | a0.25 | 6 | 0.09245 | 0.6667 | 0.09525 | 0.001205 | 0.1327 |
| Q_D5 | Q_D5 | HG10 | NATIVE | a0.5 | 6 | 0.104 | 0.8333 | 0.08865 | 0.0004843 | 0.1462 |
| Q_D5 | Q_D5 | HG15 | NATIVE | a0.125 | 6 | 0.07149 | 0.6667 | 0.07184 | 0.002152 | 0.1176 |
| Q_D5 | Q_D5 | HG15 | NATIVE | a0.25 | 6 | 0.1959 | 0.6667 | 0.2003 | 0.0006319 | 0.1564 |
| Q_D5 | Q_D5 | HG15 | NATIVE | a0.5 | 6 | 0.09395 | 0.8333 | 0.08304 | -0.001214 | 0.1777 |
| Q_D5 | Q_D5 | HG20 | NATIVE | a0.125 | 6 | -0.115 | 0.1667 | -0.1173 | 0.001846 | 0.1176 |
| Q_D5 | Q_D5 | HG20 | NATIVE | a0.25 | 6 | 0.05781 | 1 | 0.05618 | 0.001603 | 0.1685 |
| Q_D5 | Q_D5 | HG20 | NATIVE | a0.5 | 6 | 0.07295 | 0.6667 | 0.0531 | 8.5e-05 | 0.2094 |
| Q_D5 | Q_D5 | HG30 | NATIVE | a0.125 | 6 | -0.1714 | 0.3333 | -0.1781 | 0.001258 | 0.1306 |
| Q_D5 | Q_D5 | HG30 | NATIVE | a0.25 | 6 | -0.01701 | 0.3333 | -0.02418 | -0.001465 | 0.1868 |
| Q_D5 | Q_D5 | HG30 | NATIVE | a0.5 | 6 | -0.06434 | 0.3333 | -0.1113 | 0.01426 | 0.2562 |
| Q_D5 | Q_D5 | HG5 | NATIVE | a0.125 | 6 | 0.01471 | 0.6667 | 0.01576 | 1.02e-06 | 0.09208 |
| Q_D5 | Q_D5 | HG5 | NATIVE | a0.25 | 6 | 0.006354 | 0.5 | 0.005536 | 0.0001058 | 0.09681 |
| Q_D5 | Q_D5 | HG5 | NATIVE | a0.5 | 6 | 0.002702 | 0.6667 | -0.0006715 | -0.0008771 | 0.1063 |
| Q_D5 | Q_D5 | INV10 | NATIVE | a0.125 | 6 | -0.04331 | 0.3333 | -0.04453 | 0.0007725 | 0.1096 |
| Q_D5 | Q_D5 | INV10 | NATIVE | a0.25 | 6 | 0.1555 | 0.8333 | 0.1597 | 0.001031 | 0.1304 |
| Q_D5 | Q_D5 | INV10 | NATIVE | a0.5 | 6 | 0.3101 | 0.8333 | 0.2977 | 0.003672 | 0.1555 |
| Q_D5 | Q_D5 | LAG1_10 | NATIVE | a0.125 | 6 | -0.02319 | 0.5 | -0.02465 | 0.0007238 | 0.102 |
| Q_D5 | Q_D5 | LAG1_10 | NATIVE | a0.25 | 6 | 0.0754 | 0.6667 | 0.07823 | -0.0004249 | 0.1212 |
| Q_D5 | Q_D5 | LAG1_10 | NATIVE | a0.5 | 6 | 0.07398 | 0.8333 | 0.06908 | -0.002165 | 0.131 |
| Q_D5 | Q_D5 | VOL_HI15 | NATIVE | a0.125 | 6 | 0.06891 | 0.6667 | 0.06957 | 0.0008596 | 0.1018 |
| Q_D5 | Q_D5 | VOL_HI15 | NATIVE | a0.25 | 6 | 0.164 | 1 | 0.1657 | 0.0003965 | 0.1309 |
| Q_D5 | Q_D5 | VOL_HI15 | NATIVE | a0.5 | 6 | 0.1574 | 0.8333 | 0.1611 | 0.0002992 | 0.1418 |
| Q_D5 | Q_D5 | VOL_HI5 | NATIVE | a0.125 | 6 | 0.01909 | 0.6667 | 0.01949 | 0.001686 | 0.1139 |
| Q_D5 | Q_D5 | VOL_HI5 | NATIVE | a0.25 | 6 | 0.01819 | 0.5 | 0.01701 | 0.001163 | 0.1314 |
| Q_D5 | Q_D5 | VOL_HI5 | NATIVE | a0.5 | 6 | 0.01024 | 0.6667 | 0.01111 | -0.0008475 | 0.1464 |
| Q_D5 | Q_D5 | VOL_MEAN15 | NATIVE | a0.125 | 6 | -0.05589 | 0.3333 | -0.05545 | 0.0004715 | 0.1058 |
| Q_D5 | Q_D5 | VOL_MEAN15 | NATIVE | a0.25 | 6 | 0.03898 | 0.8333 | 0.04184 | 0.0009849 | 0.1261 |
| Q_D5 | Q_D5 | VOL_MEAN15 | NATIVE | a0.5 | 6 | 0.1794 | 0.8333 | 0.1836 | -0.0001417 | 0.1343 |
| Q_D5 | Q_D5 | VOL_MEAN5 | NATIVE | a0.125 | 6 | 0.03719 | 0.6667 | 0.03442 | 0.001872 | 0.1107 |
| Q_D5 | Q_D5 | VOL_MEAN5 | NATIVE | a0.25 | 6 | 0.1436 | 0.6667 | 0.1509 | 0.00177 | 0.1404 |
| Q_D5 | Q_D5 | VOL_MEAN5 | NATIVE | a0.5 | 6 | 0.06767 | 0.8333 | 0.05846 | 0.0002818 | 0.1543 |
| Q_DEW3 | Q_DEW3 | HG10 | NATIVE | a0.125 | 6 | -0.08365 | 0.3333 | -0.08509 | 0.001407 | 0.1076 |
| Q_DEW3 | Q_DEW3 | HG10 | NATIVE | a0.25 | 6 | -0.003176 | 0.5 | -0.005384 | 0.002171 | 0.12 |
| Q_DEW3 | Q_DEW3 | HG10 | NATIVE | a0.5 | 6 | -0.08928 | 0.1667 | -0.09498 | 0.001608 | 0.1643 |
| Q_DEW3 | Q_DEW3 | HG15 | NATIVE | a0.125 | 6 | -0.06504 | 0.3333 | -0.06798 | 0.00289 | 0.1233 |
| Q_DEW3 | Q_DEW3 | HG15 | NATIVE | a0.25 | 6 | 0.01467 | 0.5 | 0.01305 | 0.001592 | 0.1449 |
| Q_DEW3 | Q_DEW3 | HG15 | NATIVE | a0.5 | 6 | -0.1768 | 0.1667 | -0.1905 | 0.000947 | 0.1892 |
| Q_DEW3 | Q_DEW3 | HG5 | NATIVE | a0.125 | 6 | -0.01901 | 0.3333 | -0.01966 | -0.0001511 | 0.09155 |
| Q_DEW3 | Q_DEW3 | HG5 | NATIVE | a0.25 | 6 | 0.1042 | 1 | 0.1033 | -8.34e-05 | 0.09272 |
| Q_DEW3 | Q_DEW3 | HG5 | NATIVE | a0.5 | 6 | 0.008262 | 0.6667 | 0.01304 | 0.0001125 | 0.1153 |
| Q_DEW5 | Q_DEW5 | HG10 | NATIVE | a0.125 | 6 | -0.02987 | 0.3333 | -0.03163 | 0.001604 | 0.1076 |
| Q_DEW5 | Q_DEW5 | HG10 | NATIVE | a0.25 | 6 | 0.005529 | 0.5 | 0.003018 | 0.002405 | 0.1287 |
| Q_DEW5 | Q_DEW5 | HG10 | NATIVE | a0.5 | 6 | -0.07952 | 0.1667 | -0.07799 | 0.0009866 | 0.1541 |
| Q_DEW5 | Q_DEW5 | HG15 | NATIVE | a0.125 | 6 | -0.01239 | 0.5 | -0.0155 | 0.002503 | 0.1183 |
| Q_DEW5 | Q_DEW5 | HG15 | NATIVE | a0.25 | 6 | 0.1058 | 0.6667 | 0.1032 | 0.002549 | 0.1528 |
| Q_DEW5 | Q_DEW5 | HG15 | NATIVE | a0.5 | 6 | -0.06649 | 0.3333 | -0.06516 | -0.0007111 | 0.1814 |
| Q_DEW5 | Q_DEW5 | HG5 | NATIVE | a0.125 | 6 | 0.03854 | 0.5 | 0.03873 | -0.0001853 | 0.08892 |
| Q_DEW5 | Q_DEW5 | HG5 | NATIVE | a0.25 | 6 | 0.078 | 0.6667 | 0.07781 | 0.0006711 | 0.09826 |
| Q_DEW5 | Q_DEW5 | HG5 | NATIVE | a0.5 | 6 | -0.0641 | 0.1667 | -0.06004 | -0.000902 | 0.1092 |
| Q_DMED5 | Q_DMED5 | HG10 | NATIVE | a0.125 | 6 | -0.05599 | 0.3333 | -0.05647 | 0.001584 | 0.1102 |
| Q_DMED5 | Q_DMED5 | HG10 | NATIVE | a0.25 | 6 | 0.04947 | 0.6667 | 0.05446 | 0.001631 | 0.1292 |
| Q_DMED5 | Q_DMED5 | HG10 | NATIVE | a0.5 | 6 | -0.04747 | 0.3333 | -0.04255 | 0.001234 | 0.1482 |
| Q_DMED5 | Q_DMED5 | HG15 | NATIVE | a0.125 | 6 | 0.05368 | 0.6667 | 0.05343 | 0.00187 | 0.1162 |
| Q_DMED5 | Q_DMED5 | HG15 | NATIVE | a0.25 | 6 | 0.1664 | 0.6667 | 0.1689 | 0.0009002 | 0.148 |
| Q_DMED5 | Q_DMED5 | HG15 | NATIVE | a0.5 | 6 | 0.01095 | 0.5 | -0.0008794 | 8.002e-05 | 0.1806 |
| Q_DMED5 | Q_DMED5 | HG5 | NATIVE | a0.125 | 6 | -0.01299 | 0.5 | -0.01302 | 0.0003801 | 0.0908 |
| Q_DMED5 | Q_DMED5 | HG5 | NATIVE | a0.25 | 6 | 0.09457 | 1 | 0.09677 | 0.0007466 | 0.09639 |
| Q_DMED5 | Q_DMED5 | HG5 | NATIVE | a0.5 | 6 | -0.01052 | 0.5 | -0.01298 | -0.0008542 | 0.1037 |
| Q_QMEAN5 | Q_QMEAN5 | HG10 | NATIVE | a0.125 | 6 | -0.07222 | 0.3333 | -0.0742 | 0.001458 | 0.1048 |
| Q_QMEAN5 | Q_QMEAN5 | HG10 | NATIVE | a0.25 | 6 | -0.03166 | 0.3333 | -0.02678 | 0.001565 | 0.1273 |
| Q_QMEAN5 | Q_QMEAN5 | HG10 | NATIVE | a0.5 | 6 | 0.1006 | 0.8333 | 0.1032 | 0.001048 | 0.1521 |
| Q_QMEAN5 | Q_QMEAN5 | HG15 | NATIVE | a0.125 | 6 | 0.006071 | 0.5 | 0.004552 | 0.001489 | 0.1175 |
| Q_QMEAN5 | Q_QMEAN5 | HG15 | NATIVE | a0.25 | 6 | 0.04649 | 0.6667 | 0.05349 | 0.0007717 | 0.1444 |
| Q_QMEAN5 | Q_QMEAN5 | HG15 | NATIVE | a0.5 | 6 | 0.1122 | 0.6667 | 0.1098 | 0.002416 | 0.1817 |
| Q_QMEAN5 | Q_QMEAN5 | HG5 | NATIVE | a0.125 | 6 | 0.013 | 0.5 | 0.01427 | -0.0006817 | 0.09344 |
| Q_QMEAN5 | Q_QMEAN5 | HG5 | NATIVE | a0.25 | 6 | -0.002587 | 0.3333 | -0.005547 | -0.0005295 | 0.09726 |
| Q_QMEAN5 | Q_QMEAN5 | HG5 | NATIVE | a0.5 | 6 | 0.03089 | 0.8333 | 0.03195 | -0.0007265 | 0.1119 |
| Q_RANK10 | Q_RANK10 | HG10 | NATIVE | a0.125 | 6 | -0.1029 | 0.3333 | -0.1048 | 0.00126 | 0.1103 |
| Q_RANK10 | Q_RANK10 | HG10 | NATIVE | a0.25 | 6 | 0.06048 | 0.6667 | 0.06401 | -0.0002146 | 0.1273 |
| Q_RANK10 | Q_RANK10 | HG10 | NATIVE | a0.5 | 6 | 0.03769 | 0.5 | 0.03648 | 0.003878 | 0.1461 |
| Q_RANK10 | Q_RANK10 | HG15 | NATIVE | a0.125 | 6 | -0.01059 | 0.5 | -0.01262 | 0.001997 | 0.1163 |
| Q_RANK10 | Q_RANK10 | HG15 | NATIVE | a0.25 | 6 | 0.2061 | 0.6667 | 0.2091 | 0.0002929 | 0.1518 |
| Q_RANK10 | Q_RANK10 | HG15 | NATIVE | a0.5 | 6 | 0.08491 | 0.6667 | 0.08015 | 0.01089 | 0.1806 |
| Q_RANK10 | Q_RANK10 | HG5 | NATIVE | a0.125 | 6 | -0.004185 | 0.5 | -0.004541 | -0.0009404 | 0.0942 |
| Q_RANK10 | Q_RANK10 | HG5 | NATIVE | a0.25 | 6 | 0.0569 | 1 | 0.05898 | -0.001115 | 0.09366 |
| Q_RANK10 | Q_RANK10 | HG5 | NATIVE | a0.5 | 6 | -0.02504 | 0.1667 | -0.02611 | 0.00106 | 0.1057 |
| Q_RANK3 | Q_RANK3 | HG10 | NATIVE | a0.125 | 6 | -0.1647 | 0.3333 | -0.1661 | 0.0006781 | 0.1161 |
| Q_RANK3 | Q_RANK3 | HG10 | NATIVE | a0.25 | 6 | -0.01785 | 0.5 | -0.02198 | 0.001961 | 0.1343 |
| Q_RANK3 | Q_RANK3 | HG10 | NATIVE | a0.5 | 6 | -0.1697 | 0.1667 | -0.1674 | 0.001347 | 0.1607 |
| Q_RANK3 | Q_RANK3 | HG15 | NATIVE | a0.125 | 6 | -0.09697 | 0.3333 | -0.09909 | 0.001846 | 0.1275 |
| Q_RANK3 | Q_RANK3 | HG15 | NATIVE | a0.25 | 6 | 0.03497 | 0.6667 | 0.03114 | 0.001539 | 0.1654 |
| Q_RANK3 | Q_RANK3 | HG15 | NATIVE | a0.5 | 6 | -0.2059 | 0 | -0.2205 | 8.973e-05 | 0.1838 |
| Q_RANK3 | Q_RANK3 | HG5 | NATIVE | a0.125 | 6 | -0.0342 | 0.3333 | -0.03447 | -0.0009513 | 0.09563 |
| Q_RANK3 | Q_RANK3 | HG5 | NATIVE | a0.25 | 6 | -0.0001659 | 0.5 | 0.0007599 | 0.0002428 | 0.101 |
| Q_RANK3 | Q_RANK3 | HG5 | NATIVE | a0.5 | 6 | -0.05709 | 0.3333 | -0.06205 | 8.941e-05 | 0.1152 |
| Q_RANK5 | Q_RANK5 | DECAY2_10 | NATIVE | a0.125 | 6 | -0.1004 | 0.3333 | -0.1033 | 0.0005522 | 0.1045 |
| Q_RANK5 | Q_RANK5 | DECAY2_10 | NATIVE | a0.25 | 6 | -0.01566 | 0.5 | -0.01323 | -0.000538 | 0.1219 |
| Q_RANK5 | Q_RANK5 | DECAY2_10 | NATIVE | a0.5 | 6 | -0.09078 | 0.1667 | -0.09751 | -0.001384 | 0.1537 |
| Q_RANK5 | Q_RANK5 | DECAY5_10 | NATIVE | a0.125 | 6 | -0.1065 | 0.3333 | -0.1094 | 0.0002778 | 0.104 |
| Q_RANK5 | Q_RANK5 | DECAY5_10 | NATIVE | a0.25 | 6 | 0.009073 | 0.5 | 0.01178 | -0.000746 | 0.1235 |
| Q_RANK5 | Q_RANK5 | DECAY5_10 | NATIVE | a0.5 | 6 | -0.07436 | 0.3333 | -0.0803 | -0.001369 | 0.1567 |
| Q_RANK5 | Q_RANK5 | HG10 | NATIVE | a0.125 | 6 | -0.09141 | 0.3333 | -0.09432 | 0.0003566 | 0.1064 |
| Q_RANK5 | Q_RANK5 | HG10 | NATIVE | a0.25 | 6 | 0.01245 | 0.5 | 0.01748 | -0.0009623 | 0.1264 |
| Q_RANK5 | Q_RANK5 | HG10 | NATIVE | a0.5 | 6 | -0.06414 | 0.1667 | -0.07046 | -0.001537 | 0.1591 |
| Q_RANK5 | Q_RANK5 | HG15 | NATIVE | a0.125 | 6 | -0.01738 | 0.5 | -0.01919 | 0.001779 | 0.1211 |
| Q_RANK5 | Q_RANK5 | HG15 | NATIVE | a0.25 | 6 | 0.1197 | 0.6667 | 0.1257 | -0.0008384 | 0.154 |
| Q_RANK5 | Q_RANK5 | HG15 | NATIVE | a0.5 | 6 | 0.06032 | 0.8333 | 0.04848 | 0.002636 | 0.1807 |
| Q_RANK5 | Q_RANK5 | HG5 | NATIVE | a0.125 | 6 | 0.01401 | 0.5 | 0.01365 | 0.0003532 | 0.08666 |
| Q_RANK5 | Q_RANK5 | HG5 | NATIVE | a0.25 | 6 | -0.06883 | 0.3333 | -0.06687 | -0.00153 | 0.09722 |
| Q_RANK5 | Q_RANK5 | HG5 | NATIVE | a0.5 | 6 | -0.007824 | 0.5 | -0.01682 | -0.0009327 | 0.1077 |
| Q_RANK5 | Q_RANK5 | INV10 | NATIVE | a0.125 | 6 | -0.01096 | 0.5 | -0.01233 | 0.0004532 | 0.1075 |
| Q_RANK5 | Q_RANK5 | INV10 | NATIVE | a0.25 | 6 | 0.1485 | 0.8333 | 0.1466 | 0.001718 | 0.1301 |
| Q_RANK5 | Q_RANK5 | INV10 | NATIVE | a0.5 | 6 | 0.1597 | 0.8333 | 0.1484 | 0.003271 | 0.1614 |
| Q_RANK5 | Q_RANK5 | LAG1_10 | NATIVE | a0.125 | 6 | -0.1064 | 0.3333 | -0.108 | 0.0009922 | 0.103 |
| Q_RANK5 | Q_RANK5 | LAG1_10 | NATIVE | a0.25 | 6 | -0.04701 | 0.3333 | -0.04439 | -0.00136 | 0.1166 |
| Q_RANK5 | Q_RANK5 | LAG1_10 | NATIVE | a0.5 | 6 | -0.1127 | 0.1667 | -0.1168 | -0.001983 | 0.1383 |
| Q_RANKOBS5 | Q_RANKOBS5 | HG10 | NATIVE | a0.125 | 6 | 0.04229 | 0.6667 | 0.04149 | 0.0006049 | 0.09799 |
| Q_RANKOBS5 | Q_RANKOBS5 | HG10 | NATIVE | a0.25 | 6 | -0.02886 | 0.3333 | -0.02339 | 0.0004659 | 0.1213 |
| Q_RANKOBS5 | Q_RANKOBS5 | HG10 | NATIVE | a0.5 | 6 | 0.0408 | 0.6667 | 0.0439 | -0.001528 | 0.1424 |
| Q_RANKSCORE5 | Q_RANKSCORE5 | HG10 | NATIVE | a0.125 | 6 | -0.02742 | 0.5 | -0.02976 | 0.001117 | 0.08788 |
| Q_RANKSCORE5 | Q_RANKSCORE5 | HG10 | NATIVE | a0.25 | 6 | 0.039 | 0.6667 | 0.03769 | 0.001087 | 0.1169 |
| Q_RANKSCORE5 | Q_RANKSCORE5 | HG10 | NATIVE | a0.5 | 6 | 0.01481 | 0.5 | 0.0147 | 0.0001119 | 0.1504 |
| S | S | HG10 | NATIVE | a0.125 | 6 | -0.1437 | 0.3333 | -0.1462 | 0.001552 | 0.1142 |
| S | S | HG10 | NATIVE | a0.25 | 6 | -0.07403 | 0.3333 | -0.07527 | 0.001226 | 0.1273 |
| S | S | HG10 | NATIVE | a0.5 | 6 | -0.03661 | 0.5 | -0.04509 | 0.008331 | 0.1856 |


> 表头：主体=平滑 × 规则交互（Q0 NATIVE / Qs NATIVE / Q0 规则 / Qs 规则）｜算子=FOUR_ACCOUNT_SMOOTH_RULE｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=各端原生｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-SMOOTH-RULE


| meas | right_meas | op | right_op | alpha | cells | median_D_ann_pp | share_pos | median_Dg_ann_pp | median_fee_ann_pp | median_se_H_ann_pp |
|---|---|---|---|---|---|---|---|---|---|---|
| Q_D10 | Q_D10 | HG10 | NATIVE | a0.125 | 6 | 0.04143 | 0.6667 | 0.04137 | -0.0004091 | 0.1064 |
| Q_D10 | Q_D10 | HG10 | NATIVE | a0.25 | 6 | 0.09688 | 0.6667 | 0.09945 | -4.154e-05 | 0.1305 |
| Q_D10 | Q_D10 | HG10 | NATIVE | a0.5 | 6 | 0.1032 | 0.6667 | 0.104 | -0.001451 | 0.1931 |
| Q_D10 | Q_D10 | HG15 | NATIVE | a0.125 | 6 | 0.04166 | 0.6667 | 0.04108 | -0.000103 | 0.1161 |
| Q_D10 | Q_D10 | HG15 | NATIVE | a0.25 | 6 | 0.06294 | 0.5 | 0.06093 | -0.002924 | 0.1533 |
| Q_D10 | Q_D10 | HG15 | NATIVE | a0.5 | 6 | 0.1317 | 0.6667 | 0.1418 | -0.006816 | 0.2295 |
| Q_D10 | Q_D10 | HG5 | NATIVE | a0.125 | 6 | 0.006578 | 0.6667 | 0.007821 | -0.000447 | 0.08707 |
| Q_D10 | Q_D10 | HG5 | NATIVE | a0.25 | 6 | 0.03717 | 0.6667 | 0.03879 | 0.0002289 | 0.09804 |
| Q_D10 | Q_D10 | HG5 | NATIVE | a0.5 | 6 | 0.02285 | 0.5 | 0.02081 | -0.001079 | 0.1451 |
| Q_D3 | Q_D3 | HG10 | NATIVE | a0.125 | 6 | 0.06625 | 0.6667 | 0.06896 | 2.463e-05 | 0.1077 |
| Q_D3 | Q_D3 | HG10 | NATIVE | a0.25 | 6 | 0.1005 | 0.6667 | 0.1009 | -0.0006836 | 0.1232 |
| Q_D3 | Q_D3 | HG10 | NATIVE | a0.5 | 6 | 0.268 | 0.6667 | 0.2789 | -0.01074 | 0.2231 |
| Q_D3 | Q_D3 | HG15 | NATIVE | a0.125 | 6 | 0.001333 | 0.5 | 0.00338 | -0.0005666 | 0.1153 |
| Q_D3 | Q_D3 | HG15 | NATIVE | a0.25 | 6 | 0.02696 | 0.5 | 0.02946 | -0.001123 | 0.1468 |
| Q_D3 | Q_D3 | HG15 | NATIVE | a0.5 | 6 | 0.2532 | 0.6667 | 0.2746 | -0.009464 | 0.247 |
| Q_D3 | Q_D3 | HG5 | NATIVE | a0.125 | 6 | 0.04434 | 0.8333 | 0.04485 | 3.047e-05 | 0.08288 |
| Q_D3 | Q_D3 | HG5 | NATIVE | a0.25 | 6 | 0.007038 | 0.6667 | 0.006894 | -3.637e-05 | 0.09897 |
| Q_D3 | Q_D3 | HG5 | NATIVE | a0.5 | 6 | 0.04037 | 0.8333 | 0.03971 | -1.952e-05 | 0.1517 |
| Q_D5 | Q_D5 | DECAY2_10 | NATIVE | a0.125 | 6 | -0.01133 | 0.3333 | -0.009007 | -0.001651 | 0.1073 |
| Q_D5 | Q_D5 | DECAY2_10 | NATIVE | a0.25 | 6 | 0.1543 | 0.6667 | 0.1568 | -0.002939 | 0.1264 |
| Q_D5 | Q_D5 | DECAY2_10 | NATIVE | a0.5 | 6 | 0.3442 | 0.6667 | 0.3462 | -0.001986 | 0.167 |
| Q_D5 | Q_D5 | DECAY5_10 | NATIVE | a0.125 | 6 | -0.01512 | 0.3333 | -0.01286 | -0.001374 | 0.1079 |
| Q_D5 | Q_D5 | DECAY5_10 | NATIVE | a0.25 | 6 | 0.1485 | 0.6667 | 0.1507 | -0.002449 | 0.1293 |
| Q_D5 | Q_D5 | DECAY5_10 | NATIVE | a0.5 | 6 | 0.3655 | 0.6667 | 0.3701 | -0.004512 | 0.1806 |
| Q_D5 | Q_D5 | HG10 | NATIVE | a0.125 | 6 | -0.02324 | 0.3333 | -0.02062 | -0.001103 | 0.108 |
| Q_D5 | Q_D5 | HG10 | NATIVE | a0.25 | 6 | 0.1451 | 0.6667 | 0.1469 | -0.002728 | 0.1313 |
| Q_D5 | Q_D5 | HG10 | NATIVE | a0.5 | 6 | 0.4407 | 0.6667 | 0.4537 | -0.006367 | 0.185 |
| Q_D5 | Q_D5 | HG15 | NATIVE | a0.125 | 6 | -0.03983 | 0.3333 | -0.0385 | -0.0005035 | 0.1153 |
| Q_D5 | Q_D5 | HG15 | NATIVE | a0.25 | 6 | 0.1383 | 0.8333 | 0.1407 | -0.005657 | 0.1518 |
| Q_D5 | Q_D5 | HG15 | NATIVE | a0.5 | 6 | 0.4148 | 0.6667 | 0.4297 | -0.01245 | 0.226 |
| Q_D5 | Q_D5 | HG20 | NATIVE | a0.125 | 6 | -0.05638 | 0.3333 | -0.0519 | -0.002273 | 0.1202 |
| Q_D5 | Q_D5 | HG20 | NATIVE | a0.25 | 6 | 0.144 | 1 | 0.1463 | -0.00551 | 0.1688 |
| Q_D5 | Q_D5 | HG20 | NATIVE | a0.5 | 6 | 0.3468 | 0.6667 | 0.3663 | -0.00427 | 0.2379 |
| Q_D5 | Q_D5 | HG30 | NATIVE | a0.125 | 6 | 0.06737 | 0.6667 | 0.06756 | -0.001076 | 0.1278 |
| Q_D5 | Q_D5 | HG30 | NATIVE | a0.25 | 6 | 0.1375 | 0.8333 | 0.153 | -0.01526 | 0.2047 |
| Q_D5 | Q_D5 | HG30 | NATIVE | a0.5 | 6 | 0.4544 | 0.6667 | 0.4606 | -0.001406 | 0.2803 |
| Q_D5 | Q_D5 | HG5 | NATIVE | a0.125 | 6 | -0.1025 | 0.3333 | -0.1008 | 0.0002177 | 0.08881 |
| Q_D5 | Q_D5 | HG5 | NATIVE | a0.25 | 6 | -0.03669 | 0.1667 | -0.03604 | -0.001091 | 0.1011 |
| Q_D5 | Q_D5 | HG5 | NATIVE | a0.5 | 6 | 0.09472 | 0.6667 | 0.09163 | -0.0002338 | 0.1374 |
| Q_D5 | Q_D5 | INV10 | NATIVE | a0.125 | 6 | -0.05023 | 0.3333 | -0.0499 | -4.733e-05 | 0.1064 |
| Q_D5 | Q_D5 | INV10 | NATIVE | a0.25 | 6 | 0.1792 | 0.6667 | 0.1817 | -0.001927 | 0.1305 |
| Q_D5 | Q_D5 | INV10 | NATIVE | a0.5 | 6 | 0.2299 | 0.6667 | 0.2072 | -0.002321 | 0.1907 |
| Q_D5 | Q_D5 | LAG1_10 | NATIVE | a0.125 | 6 | -0.03285 | 0.3333 | -0.03194 | -0.0006554 | 0.1047 |
| Q_D5 | Q_D5 | LAG1_10 | NATIVE | a0.25 | 6 | 0.1983 | 0.6667 | 0.2001 | -0.001974 | 0.1174 |
| Q_D5 | Q_D5 | LAG1_10 | NATIVE | a0.5 | 6 | 0.2908 | 0.8333 | 0.2923 | -0.001288 | 0.1486 |
| Q_D5 | Q_D5 | VOL_HI15 | NATIVE | a0.125 | 6 | -0.1276 | 0.3333 | -0.1259 | -0.0001357 | 0.1006 |
| Q_D5 | Q_D5 | VOL_HI15 | NATIVE | a0.25 | 6 | 0.01613 | 0.5 | 0.01638 | -0.002746 | 0.1293 |
| Q_D5 | Q_D5 | VOL_HI15 | NATIVE | a0.5 | 6 | 0.2543 | 0.8333 | 0.253 | 0.0007261 | 0.1832 |
| Q_D5 | Q_D5 | VOL_HI5 | NATIVE | a0.125 | 6 | -0.02206 | 0.3333 | -0.01916 | -0.001365 | 0.103 |
| Q_D5 | Q_D5 | VOL_HI5 | NATIVE | a0.25 | 6 | 0.04161 | 1 | 0.0467 | -0.003949 | 0.1305 |
| Q_D5 | Q_D5 | VOL_HI5 | NATIVE | a0.5 | 6 | 0.2368 | 0.6667 | 0.249 | -0.01187 | 0.193 |
| Q_D5 | Q_D5 | VOL_MEAN15 | NATIVE | a0.125 | 6 | -0.07962 | 0.3333 | -0.07761 | -0.001053 | 0.1033 |
| Q_D5 | Q_D5 | VOL_MEAN15 | NATIVE | a0.25 | 6 | 0.01936 | 0.6667 | 0.02113 | -0.003293 | 0.1194 |
| Q_D5 | Q_D5 | VOL_MEAN15 | NATIVE | a0.5 | 6 | 0.3299 | 0.6667 | 0.333 | -0.003033 | 0.1755 |
| Q_D5 | Q_D5 | VOL_MEAN5 | NATIVE | a0.125 | 6 | -0.01542 | 0.3333 | -0.01304 | -0.000808 | 0.108 |
| Q_D5 | Q_D5 | VOL_MEAN5 | NATIVE | a0.25 | 6 | 0.103 | 0.8333 | 0.104 | -0.003052 | 0.1345 |
| Q_D5 | Q_D5 | VOL_MEAN5 | NATIVE | a0.5 | 6 | 0.3733 | 0.6667 | 0.3867 | -0.008259 | 0.1961 |
| Q_DEW3 | Q_DEW3 | HG10 | NATIVE | a0.125 | 6 | 0.02473 | 0.6667 | 0.02711 | 0.0001583 | 0.09823 |
| Q_DEW3 | Q_DEW3 | HG10 | NATIVE | a0.25 | 6 | 0.08115 | 0.6667 | 0.08211 | -0.001567 | 0.1204 |
| Q_DEW3 | Q_DEW3 | HG10 | NATIVE | a0.5 | 6 | 0.148 | 0.6667 | 0.1576 | -0.00803 | 0.1995 |
| Q_DEW3 | Q_DEW3 | HG15 | NATIVE | a0.125 | 6 | 0.006508 | 0.5 | 0.007536 | 0.0002072 | 0.1066 |
| Q_DEW3 | Q_DEW3 | HG15 | NATIVE | a0.25 | 6 | 0.008769 | 0.5 | 0.01003 | -0.00371 | 0.1383 |
| Q_DEW3 | Q_DEW3 | HG15 | NATIVE | a0.5 | 6 | -0.04771 | 0.3333 | -0.04081 | -0.003459 | 0.2264 |
| Q_DEW3 | Q_DEW3 | HG5 | NATIVE | a0.125 | 6 | 0.06006 | 0.6667 | 0.05995 | -7.05e-06 | 0.08068 |
| Q_DEW3 | Q_DEW3 | HG5 | NATIVE | a0.25 | 6 | 0.07237 | 1 | 0.07233 | -0.0002718 | 0.09403 |
| Q_DEW3 | Q_DEW3 | HG5 | NATIVE | a0.5 | 6 | 0.1083 | 0.8333 | 0.1063 | 0.0007558 | 0.1443 |
| Q_DEW5 | Q_DEW5 | HG10 | NATIVE | a0.125 | 6 | 0.02727 | 0.6667 | 0.0292 | 0.0002219 | 0.1018 |
| Q_DEW5 | Q_DEW5 | HG10 | NATIVE | a0.25 | 6 | 0.06577 | 0.6667 | 0.06832 | -0.001573 | 0.1228 |
| Q_DEW5 | Q_DEW5 | HG10 | NATIVE | a0.5 | 6 | 0.1998 | 0.8333 | 0.2075 | -0.004826 | 0.1888 |
| Q_DEW5 | Q_DEW5 | HG15 | NATIVE | a0.125 | 6 | 0.01705 | 0.8333 | 0.01966 | 0.0001229 | 0.1082 |
| Q_DEW5 | Q_DEW5 | HG15 | NATIVE | a0.25 | 6 | 0.0502 | 0.8333 | 0.05139 | -0.002336 | 0.1415 |
| Q_DEW5 | Q_DEW5 | HG15 | NATIVE | a0.5 | 6 | 0.1316 | 0.6667 | 0.1452 | -0.007629 | 0.2165 |
| Q_DEW5 | Q_DEW5 | HG5 | NATIVE | a0.125 | 6 | 0.009725 | 0.6667 | 0.01094 | 7.847e-05 | 0.08395 |
| Q_DEW5 | Q_DEW5 | HG5 | NATIVE | a0.25 | 6 | -0.003097 | 0.3333 | -0.002511 | -0.0005781 | 0.09852 |
| Q_DEW5 | Q_DEW5 | HG5 | NATIVE | a0.5 | 6 | 0.05739 | 0.8333 | 0.06185 | -0.0002587 | 0.1437 |
| Q_DMED5 | Q_DMED5 | HG10 | NATIVE | a0.125 | 6 | -0.1194 | 0.3333 | -0.1189 | 0.0002539 | 0.1096 |
| Q_DMED5 | Q_DMED5 | HG10 | NATIVE | a0.25 | 6 | 0.09791 | 0.6667 | 0.09989 | -0.001029 | 0.1223 |
| Q_DMED5 | Q_DMED5 | HG10 | NATIVE | a0.5 | 6 | 0.206 | 0.6667 | 0.2121 | -0.005963 | 0.1896 |
| Q_DMED5 | Q_DMED5 | HG15 | NATIVE | a0.125 | 6 | -0.0603 | 0.3333 | -0.06037 | -0.0002514 | 0.1126 |
| Q_DMED5 | Q_DMED5 | HG15 | NATIVE | a0.25 | 6 | 0.07634 | 0.6667 | 0.07786 | -0.002548 | 0.1459 |
| Q_DMED5 | Q_DMED5 | HG15 | NATIVE | a0.5 | 6 | 0.1361 | 0.6667 | 0.1509 | -0.01452 | 0.2237 |
| Q_DMED5 | Q_DMED5 | HG5 | NATIVE | a0.125 | 6 | -0.09016 | 0.3333 | -0.09075 | 0.0002995 | 0.0891 |
| Q_DMED5 | Q_DMED5 | HG5 | NATIVE | a0.25 | 6 | 0.03221 | 0.6667 | 0.03234 | 0.000368 | 0.09809 |
| Q_DMED5 | Q_DMED5 | HG5 | NATIVE | a0.5 | 6 | 0.0974 | 0.8333 | 0.1064 | -0.0002109 | 0.1452 |
| Q_QMEAN5 | Q_QMEAN5 | HG10 | NATIVE | a0.125 | 6 | -0.0201 | 0.3333 | -0.01667 | -2.292e-05 | 0.108 |
| Q_QMEAN5 | Q_QMEAN5 | HG10 | NATIVE | a0.25 | 6 | 0.0881 | 0.6667 | 0.09042 | -0.00109 | 0.1226 |
| Q_QMEAN5 | Q_QMEAN5 | HG10 | NATIVE | a0.5 | 6 | 0.3426 | 1 | 0.3498 | -0.003632 | 0.1949 |
| Q_QMEAN5 | Q_QMEAN5 | HG15 | NATIVE | a0.125 | 6 | 0.01696 | 0.6667 | 0.01982 | -0.0007567 | 0.1163 |
| Q_QMEAN5 | Q_QMEAN5 | HG15 | NATIVE | a0.25 | 6 | 0.05853 | 0.6667 | 0.06171 | -0.003115 | 0.1445 |
| Q_QMEAN5 | Q_QMEAN5 | HG15 | NATIVE | a0.5 | 6 | 0.2515 | 0.8333 | 0.2592 | -0.003395 | 0.2255 |
| Q_QMEAN5 | Q_QMEAN5 | HG5 | NATIVE | a0.125 | 6 | -0.0459 | 0.3333 | -0.04416 | -0.000418 | 0.09058 |
| Q_QMEAN5 | Q_QMEAN5 | HG5 | NATIVE | a0.25 | 6 | 0.009276 | 0.5 | 0.009852 | -0.0006234 | 0.09396 |
| Q_QMEAN5 | Q_QMEAN5 | HG5 | NATIVE | a0.5 | 6 | 0.117 | 1 | 0.1142 | -8.317e-05 | 0.1425 |
| Q_RANK10 | Q_RANK10 | HG10 | NATIVE | a0.125 | 6 | -0.02541 | 0.3333 | -0.02327 | -2.952e-05 | 0.1036 |
| Q_RANK10 | Q_RANK10 | HG10 | NATIVE | a0.25 | 6 | 0.04761 | 0.6667 | 0.0487 | -0.001069 | 0.1261 |
| Q_RANK10 | Q_RANK10 | HG10 | NATIVE | a0.5 | 6 | 0.09458 | 0.8333 | 0.1049 | -0.001704 | 0.1883 |
| Q_RANK10 | Q_RANK10 | HG15 | NATIVE | a0.125 | 6 | -0.002002 | 0.5 | -6.061e-05 | -0.0005127 | 0.1113 |
| Q_RANK10 | Q_RANK10 | HG15 | NATIVE | a0.25 | 6 | 0.1421 | 0.8333 | 0.1448 | -0.0004466 | 0.1413 |
| Q_RANK10 | Q_RANK10 | HG15 | NATIVE | a0.5 | 6 | 0.2467 | 0.8333 | 0.2607 | -0.0008443 | 0.2118 |
| Q_RANK10 | Q_RANK10 | HG5 | NATIVE | a0.125 | 6 | -0.07541 | 0.3333 | -0.07417 | -0.0006902 | 0.0873 |
| Q_RANK10 | Q_RANK10 | HG5 | NATIVE | a0.25 | 6 | 0.03951 | 0.6667 | 0.04015 | -0.0009195 | 0.09416 |
| Q_RANK10 | Q_RANK10 | HG5 | NATIVE | a0.5 | 6 | 0.0627 | 0.8333 | 0.06957 | -0.0005701 | 0.1281 |
| Q_RANK3 | Q_RANK3 | HG10 | NATIVE | a0.125 | 6 | 0.1015 | 0.6667 | 0.1024 | -0.0008948 | 0.1036 |
| Q_RANK3 | Q_RANK3 | HG10 | NATIVE | a0.25 | 6 | -0.05939 | 0.3333 | -0.05959 | 0.0001923 | 0.1221 |
| Q_RANK3 | Q_RANK3 | HG10 | NATIVE | a0.5 | 6 | 0.1013 | 0.6667 | 0.1073 | -0.00596 | 0.1831 |
| Q_RANK3 | Q_RANK3 | HG15 | NATIVE | a0.125 | 6 | -0.02068 | 0.3333 | -0.02028 | -0.0005571 | 0.1118 |
| Q_RANK3 | Q_RANK3 | HG15 | NATIVE | a0.25 | 6 | 0.01129 | 0.5 | 0.01174 | -0.0004327 | 0.1521 |
| Q_RANK3 | Q_RANK3 | HG15 | NATIVE | a0.5 | 6 | -0.08322 | 0.3333 | -0.07053 | -0.006295 | 0.2088 |
| Q_RANK3 | Q_RANK3 | HG5 | NATIVE | a0.125 | 6 | -0.03503 | 0.3333 | -0.03396 | -0.0005402 | 0.08195 |
| Q_RANK3 | Q_RANK3 | HG5 | NATIVE | a0.25 | 6 | -0.06299 | 0.3333 | -0.06311 | 0.0001233 | 0.0936 |
| Q_RANK3 | Q_RANK3 | HG5 | NATIVE | a0.5 | 6 | 0.04842 | 0.8333 | 0.04598 | 0.0007327 | 0.1395 |
| Q_RANK5 | Q_RANK5 | DECAY2_10 | NATIVE | a0.125 | 6 | 0.03847 | 0.6667 | 0.04145 | -0.001564 | 0.09844 |
| Q_RANK5 | Q_RANK5 | DECAY2_10 | NATIVE | a0.25 | 6 | 0.03871 | 0.5 | 0.04152 | -0.002069 | 0.1131 |
| Q_RANK5 | Q_RANK5 | DECAY2_10 | NATIVE | a0.5 | 6 | 0.09448 | 0.8333 | 0.09398 | -0.0004621 | 0.1768 |
| Q_RANK5 | Q_RANK5 | DECAY5_10 | NATIVE | a0.125 | 6 | 0.04302 | 0.6667 | 0.04618 | -0.00122 | 0.099 |
| Q_RANK5 | Q_RANK5 | DECAY5_10 | NATIVE | a0.25 | 6 | -0.02866 | 0.5 | -0.02582 | -0.00203 | 0.1151 |
| Q_RANK5 | Q_RANK5 | DECAY5_10 | NATIVE | a0.5 | 6 | 0.03291 | 0.5 | 0.0349 | -0.00196 | 0.1924 |
| Q_RANK5 | Q_RANK5 | HG10 | NATIVE | a0.125 | 6 | 0.02189 | 0.5 | 0.02553 | -0.000849 | 0.1017 |
| Q_RANK5 | Q_RANK5 | HG10 | NATIVE | a0.25 | 6 | -0.0117 | 0.5 | -0.009287 | -0.001752 | 0.1189 |
| Q_RANK5 | Q_RANK5 | HG10 | NATIVE | a0.5 | 6 | 0.08796 | 0.6667 | 0.09174 | -0.00372 | 0.1945 |
| Q_RANK5 | Q_RANK5 | HG15 | NATIVE | a0.125 | 6 | 0.09972 | 0.6667 | 0.1017 | -0.0006995 | 0.1092 |
| Q_RANK5 | Q_RANK5 | HG15 | NATIVE | a0.25 | 6 | 0.05142 | 0.5 | 0.05532 | -0.002944 | 0.1385 |
| Q_RANK5 | Q_RANK5 | HG15 | NATIVE | a0.5 | 6 | 0.1923 | 0.8333 | 0.201 | -0.008485 | 0.2222 |
| Q_RANK5 | Q_RANK5 | HG5 | NATIVE | a0.125 | 6 | 0.01962 | 0.6667 | 0.02089 | 0.000451 | 0.08453 |
| Q_RANK5 | Q_RANK5 | HG5 | NATIVE | a0.25 | 6 | -0.1006 | 0 | -0.0998 | -0.001868 | 0.09375 |
| Q_RANK5 | Q_RANK5 | HG5 | NATIVE | a0.5 | 6 | 0.05964 | 0.6667 | 0.0579 | -0.0002894 | 0.1411 |
| Q_RANK5 | Q_RANK5 | INV10 | NATIVE | a0.125 | 6 | 0.1526 | 0.6667 | 0.1537 | -0.0004453 | 0.09859 |
| Q_RANK5 | Q_RANK5 | INV10 | NATIVE | a0.25 | 6 | 0.1524 | 0.6667 | 0.1551 | -0.001441 | 0.1252 |
| Q_RANK5 | Q_RANK5 | INV10 | NATIVE | a0.5 | 6 | 0.04233 | 0.6667 | 0.03384 | -0.001454 | 0.1885 |
| Q_RANK5 | Q_RANK5 | LAG1_10 | NATIVE | a0.125 | 6 | 0.04142 | 0.6667 | 0.04298 | -0.0006249 | 0.09399 |
| Q_RANK5 | Q_RANK5 | LAG1_10 | NATIVE | a0.25 | 6 | 0.03342 | 0.5 | 0.03572 | -0.00151 | 0.1121 |
| Q_RANK5 | Q_RANK5 | LAG1_10 | NATIVE | a0.5 | 6 | 0.02481 | 0.5 | 0.02482 | -9.687e-05 | 0.1602 |
| Q_RANKOBS5 | Q_RANKOBS5 | HG10 | NATIVE | a0.125 | 6 | -0.01318 | 0.3333 | -0.01008 | -0.001062 | 0.1013 |
| Q_RANKOBS5 | Q_RANKOBS5 | HG10 | NATIVE | a0.25 | 6 | 0.04789 | 0.6667 | 0.05062 | -0.001664 | 0.1221 |
| Q_RANKOBS5 | Q_RANKOBS5 | HG10 | NATIVE | a0.5 | 6 | 0.236 | 0.8333 | 0.2436 | -0.007433 | 0.1802 |
| Q_RANKSCORE5 | Q_RANKSCORE5 | HG10 | NATIVE | a0.125 | 6 | 0.004858 | 0.5 | 0.006353 | -8.892e-05 | 0.1015 |
| Q_RANKSCORE5 | Q_RANKSCORE5 | HG10 | NATIVE | a0.25 | 6 | -0.02148 | 0.3333 | -0.01956 | -0.000896 | 0.1255 |
| Q_RANKSCORE5 | Q_RANKSCORE5 | HG10 | NATIVE | a0.5 | 6 | 0.2995 | 0.8333 | 0.3232 | -0.006462 | 0.1872 |


> 表头：主体=机制配对（LAG1 / DECAY / INV / 调度 / 边界 b 相对 HG10 等）｜算子=MECHANISM_PAIR｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=各端原生｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-MECHPAIR


| meas | right_meas | op | right_op | alpha | cells | median_D_ann_pp | share_pos | median_Dg_ann_pp | median_fee_ann_pp | median_se_H_ann_pp |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | C1 | DECAY2_10 | DECAY5_10 | a0.125 | 6 | 0.01301 | 0.8333 | 0.01321 | -0.0001744 | 0.01718 |
| C1 | C1 | DECAY2_10 | DECAY5_10 | a0.25 | 6 | 0.01547 | 0.6667 | 0.01562 | -0.0001558 | 0.01777 |
| C1 | C1 | DECAY2_10 | DECAY5_10 | a0.5 | 6 | 0.009106 | 1 | 0.009537 | -0.0003096 | 0.01663 |
| C1 | C1 | DECAY2_10 | HG10 | a0.125 | 6 | 0.01678 | 1 | 0.01747 | -0.0004807 | 0.02349 |
| C1 | C1 | DECAY2_10 | HG10 | a0.25 | 6 | 0.02025 | 0.6667 | 0.01973 | 0.0001437 | 0.02198 |
| C1 | C1 | DECAY2_10 | HG10 | a0.5 | 6 | 0.009133 | 0.6667 | 0.009516 | -0.0003408 | 0.02336 |
| C1 | C1 | DECAY5_10 | HG10 | a0.125 | 6 | 0.007628 | 0.6667 | 0.007749 | -0.0002689 | 0.0182 |
| C1 | C1 | DECAY5_10 | HG10 | a0.25 | 6 | -0.01508 | 0.3333 | -0.01512 | 0.000183 | 0.01541 |
| C1 | C1 | DECAY5_10 | HG10 | a0.5 | 6 | -0.0024 | 0.3333 | -0.0021 | -0.0002407 | 0.0182 |
| C1 | C1 | HG10 | HG5 | a0.125 | 6 | 0.0009047 | 0.5 | 0.004095 | 0.003745 | 0.07414 |
| C1 | C1 | HG10 | HG5 | a0.25 | 6 | -0.001173 | 0.5 | -0.000556 | 0.002871 | 0.07475 |
| C1 | C1 | HG10 | HG5 | a0.5 | 6 | -0.01261 | 0.5 | -0.01063 | 0.003504 | 0.07139 |
| C1 | C1 | HG15 | HG10 | a0.125 | 6 | 0.02524 | 0.6667 | 0.0228 | 0.005774 | 0.07281 |
| C1 | C1 | HG15 | HG10 | a0.25 | 6 | -0.03877 | 0.1667 | -0.04015 | 0.003602 | 0.07681 |
| C1 | C1 | HG15 | HG10 | a0.5 | 6 | 0.003728 | 0.5 | 0.003293 | 0.003244 | 0.07788 |
| C1 | C1 | HG20 | HG15 | a0.125 | 6 | 0.05658 | 0.6667 | 0.05812 | 0.00334 | 0.07841 |
| C1 | C1 | HG20 | HG15 | a0.25 | 6 | 0.07681 | 0.6667 | 0.07193 | 0.004798 | 0.07616 |
| C1 | C1 | HG20 | HG15 | a0.5 | 6 | -0.01053 | 0.5 | -0.01716 | 0.004078 | 0.07651 |
| C1 | C1 | HG30 | HG15 | a0.125 | 6 | 0.04448 | 0.6667 | 0.03648 | 0.01158 | 0.1293 |
| C1 | C1 | HG30 | HG15 | a0.25 | 6 | -0.03954 | 0.3333 | -0.03948 | 0.01192 | 0.1321 |
| C1 | C1 | HG30 | HG15 | a0.5 | 6 | 0.06838 | 0.6667 | 0.05636 | 0.01181 | 0.134 |
| C1 | C1 | INV10 | HG10 | a0.125 | 6 | 0.1009 | 0.6667 | 0.1108 | 0.00515 | 0.08968 |
| C1 | C1 | INV10 | HG10 | a0.25 | 6 | 0.002648 | 0.5 | -0.009969 | 0.006803 | 0.09311 |
| C1 | C1 | INV10 | HG10 | a0.5 | 6 | 0.05065 | 1 | 0.06484 | 0.01233 | 0.09522 |
| C1 | C1 | INV10 | LAG1_10 | a0.125 | 6 | 0.05176 | 0.6667 | 0.04894 | 0.006333 | 0.08828 |
| C1 | C1 | INV10 | LAG1_10 | a0.25 | 6 | -0.02941 | 0.5 | -0.04214 | 0.007599 | 0.09259 |
| C1 | C1 | INV10 | LAG1_10 | a0.5 | 6 | 0.03002 | 0.8333 | 0.03998 | 0.01365 | 0.09603 |
| C1 | C1 | LAG1_10 | HG10 | a0.125 | 6 | 0.05966 | 1 | 0.0615 | -0.000901 | 0.04054 |
| C1 | C1 | LAG1_10 | HG10 | a0.25 | 6 | 0.03273 | 0.6667 | 0.03303 | -0.0002951 | 0.04319 |
| C1 | C1 | LAG1_10 | HG10 | a0.5 | 6 | 0.005011 | 0.5 | 0.004766 | -0.0001492 | 0.04334 |
| C1 | C1 | VOL_HI15 | HG10 | a0.125 | 6 | -0.02154 | 0.5 | -0.02244 | -0.001142 | 0.07058 |
| C1 | C1 | VOL_HI15 | HG10 | a0.25 | 6 | -0.05699 | 0.1667 | -0.05862 | -0.0007378 | 0.07416 |
| C1 | C1 | VOL_HI15 | HG10 | a0.5 | 6 | 0.046 | 0.8333 | 0.04654 | -0.001647 | 0.07592 |
| C1 | C1 | VOL_HI15 | VOL_HI5 | a0.125 | 6 | -0.02311 | 0.1667 | -0.02077 | -0.004495 | 0.1001 |
| C1 | C1 | VOL_HI15 | VOL_HI5 | a0.25 | 6 | -0.06157 | 0.1667 | -0.06136 | -0.003057 | 0.09973 |
| C1 | C1 | VOL_HI15 | VOL_HI5 | a0.5 | 6 | 0.07828 | 1 | 0.08281 | -0.003271 | 0.09883 |
| C1 | C1 | VOL_HI5 | HG10 | a0.125 | 6 | 0.02547 | 0.6667 | 0.02193 | 0.003252 | 0.06967 |
| C1 | C1 | VOL_HI5 | HG10 | a0.25 | 6 | -0.006632 | 0.3333 | -0.008634 | 0.002149 | 0.07273 |
| C1 | C1 | VOL_HI5 | HG10 | a0.5 | 6 | -0.01901 | 0.1667 | -0.02066 | 0.001623 | 0.07039 |
| C1 | C1 | VOL_MEAN15 | HG10 | a0.125 | 6 | -0.01978 | 0.3333 | -0.01892 | -0.0008421 | 0.04649 |
| C1 | C1 | VOL_MEAN15 | HG10 | a0.25 | 6 | -0.04233 | 0.3333 | -0.041 | -0.001306 | 0.05 |
| C1 | C1 | VOL_MEAN15 | HG10 | a0.5 | 6 | 0.02817 | 0.8333 | 0.02826 | -7.981e-05 | 0.04352 |
| C1 | C1 | VOL_MEAN15 | VOL_MEAN5 | a0.125 | 6 | -0.03684 | 0.3333 | -0.03888 | -0.003011 | 0.06516 |
| C1 | C1 | VOL_MEAN15 | VOL_MEAN5 | a0.25 | 6 | -0.02108 | 0.5 | -0.01837 | -0.002666 | 0.06874 |
| C1 | C1 | VOL_MEAN15 | VOL_MEAN5 | a0.5 | 6 | 0.02888 | 0.6667 | 0.03004 | -0.001191 | 0.06957 |
| C1 | C1 | VOL_MEAN5 | HG10 | a0.125 | 6 | -0.002487 | 0.5 | -0.001414 | 0.002118 | 0.04784 |
| C1 | C1 | VOL_MEAN5 | HG10 | a0.25 | 6 | -0.02125 | 0.3333 | -0.02263 | 0.001359 | 0.05105 |
| C1 | C1 | VOL_MEAN5 | HG10 | a0.5 | 6 | -0.007374 | 0.3333 | -0.006716 | 0.001112 | 0.05397 |
| K0 | K0 | DECAY2_10 | DECAY5_10 | a0 | 6 | 0.004962 | 0.8333 | 0.004837 | -0.0002575 | 0.0151 |
| K0 | K0 | DECAY2_10 | HG10 | a0 | 6 | -0.001271 | 0.5 | -0.001165 | -0.0005786 | 0.02115 |
| K0 | K0 | DECAY5_10 | HG10 | a0 | 6 | -0.008241 | 0.1667 | -0.008313 | -0.0001461 | 0.01497 |
| K0 | K0 | HG10 | HG5 | a0 | 6 | 0.04999 | 0.8333 | 0.0533 | 0.004127 | 0.06801 |
| K0 | K0 | HG15 | HG10 | a0 | 6 | -0.05212 | 0 | -0.05253 | 0.003433 | 0.0736 |
| K0 | K0 | HG20 | HG15 | a0 | 6 | 0.0519 | 1 | 0.05028 | 0.004379 | 0.07481 |
| K0 | K0 | HG30 | HG15 | a0 | 6 | 0.07125 | 0.8333 | 0.0666 | 0.01241 | 0.1331 |
| K0 | K0 | INV10 | HG10 | a0 | 6 | -0.02132 | 0.5 | -0.03402 | 0.003963 | 0.09091 |
| K0 | K0 | INV10 | LAG1_10 | a0 | 6 | -0.04495 | 0.3333 | -0.0591 | 0.005043 | 0.08819 |
| K0 | K0 | LAG1_10 | HG10 | a0 | 6 | 0.01968 | 0.6667 | 0.02101 | -0.00108 | 0.0395 |
| K0 | K0 | VOL_HI15 | HG10 | a0 | 6 | -0.0986 | 0 | -0.09798 | -0.001524 | 0.06744 |
| K0 | K0 | VOL_HI15 | VOL_HI5 | a0 | 6 | -0.06957 | 0 | -0.07043 | -0.002676 | 0.09314 |
| K0 | K0 | VOL_HI5 | HG10 | a0 | 6 | -0.02421 | 0.1667 | -0.02558 | 0.0008427 | 0.06837 |
| K0 | K0 | VOL_MEAN15 | HG10 | a0 | 6 | -0.04121 | 0 | -0.04063 | -0.001681 | 0.04443 |
| K0 | K0 | VOL_MEAN15 | VOL_MEAN5 | a0 | 6 | -0.03469 | 0.3333 | -0.0362 | -0.00277 | 0.06486 |
| K0 | K0 | VOL_MEAN5 | HG10 | a0 | 6 | 0.007198 | 0.6667 | 0.008071 | 0.0005055 | 0.04912 |
| Q0 | Q0 | DECAY2_10 | DECAY5_10 | a0.125 | 6 | 0.01457 | 0.6667 | 0.01438 | 2.264e-05 | 0.01958 |
| Q0 | Q0 | DECAY2_10 | DECAY5_10 | a0.25 | 6 | -0.03928 | 0 | -0.03962 | -1.688e-05 | 0.02341 |
| Q0 | Q0 | DECAY2_10 | DECAY5_10 | a0.5 | 6 | -0.03381 | 0.3333 | -0.03331 | -0.002436 | 0.05274 |
| Q0 | Q0 | DECAY2_10 | HG10 | a0.125 | 6 | 0.002905 | 0.5 | 0.002648 | -4.425e-05 | 0.02553 |
| Q0 | Q0 | DECAY2_10 | HG10 | a0.25 | 6 | -0.03889 | 0 | -0.03903 | 0.0001373 | 0.03049 |
| Q0 | Q0 | DECAY2_10 | HG10 | a0.5 | 6 | 0.0136 | 0.6667 | 0.01839 | -0.003857 | 0.06137 |
| Q0 | Q0 | DECAY5_10 | HG10 | a0.125 | 6 | -0.01312 | 0.1667 | -0.0132 | -8.506e-05 | 0.01744 |
| Q0 | Q0 | DECAY5_10 | HG10 | a0.25 | 6 | -0.005766 | 0.3333 | -0.005864 | -0.0001588 | 0.02165 |
| Q0 | Q0 | DECAY5_10 | HG10 | a0.5 | 6 | 0.001893 | 0.8333 | 0.00363 | -0.001509 | 0.05024 |
| Q0 | Q0 | HG10 | HG5 | a0.125 | 6 | 0.04067 | 0.6667 | 0.03919 | 0.005429 | 0.07329 |
| Q0 | Q0 | HG10 | HG5 | a0.25 | 6 | -0.04458 | 0.3333 | -0.05068 | 0.005993 | 0.078 |
| Q0 | Q0 | HG10 | HG5 | a0.5 | 6 | -0.04813 | 0.3333 | -0.06037 | 0.006042 | 0.1043 |
| Q0 | Q0 | HG15 | HG10 | a0.125 | 6 | -0.01242 | 0.1667 | -0.01458 | 0.005271 | 0.07608 |
| Q0 | Q0 | HG15 | HG10 | a0.25 | 6 | -0.03686 | 0.3333 | -0.03546 | 0.00535 | 0.0843 |
| Q0 | Q0 | HG15 | HG10 | a0.5 | 6 | -0.009253 | 0.5 | -0.0149 | 0.006537 | 0.101 |
| Q0 | Q0 | HG20 | HG15 | a0.125 | 6 | -0.04796 | 0 | -0.05245 | 0.005455 | 0.08626 |
| Q0 | Q0 | HG20 | HG15 | a0.25 | 6 | -0.04053 | 0.3333 | -0.048 | 0.006803 | 0.08911 |
| Q0 | Q0 | HG20 | HG15 | a0.5 | 6 | 0.002527 | 0.5 | -0.001311 | 0.005244 | 0.09208 |
| Q0 | Q0 | HG30 | HG15 | a0.125 | 6 | -0.03163 | 0.3333 | -0.0497 | 0.01704 | 0.1361 |
| Q0 | Q0 | HG30 | HG15 | a0.25 | 6 | 0.02959 | 0.6667 | 0.001268 | 0.02139 | 0.166 |
| Q0 | Q0 | HG30 | HG15 | a0.5 | 6 | -0.0989 | 0 | -0.1166 | 0.01671 | 0.14 |
| Q0 | Q0 | INV10 | HG10 | a0.125 | 6 | -0.05978 | 0.3333 | -0.06807 | 0.003656 | 0.09611 |
| Q0 | Q0 | INV10 | HG10 | a0.25 | 6 | 0.04261 | 0.5 | 0.04311 | 0.004026 | 0.1033 |
| Q0 | Q0 | INV10 | HG10 | a0.5 | 6 | 0.02656 | 0.5 | 0.01289 | -0.0002789 | 0.1938 |
| Q0 | Q0 | INV10 | LAG1_10 | a0.125 | 6 | -0.05422 | 0.3333 | -0.06445 | 0.004745 | 0.09636 |
| Q0 | Q0 | INV10 | LAG1_10 | a0.25 | 6 | 0.1448 | 0.8333 | 0.1326 | 0.005503 | 0.108 |
| Q0 | Q0 | INV10 | LAG1_10 | a0.5 | 6 | 0.03208 | 0.5 | 0.01436 | 0.01139 | 0.1784 |
| Q0 | Q0 | LAG1_10 | HG10 | a0.125 | 6 | -0.008455 | 0.3333 | -0.008112 | -0.0006652 | 0.04189 |
| Q0 | Q0 | LAG1_10 | HG10 | a0.25 | 6 | -0.09207 | 0 | -0.08952 | -0.000839 | 0.05282 |
| Q0 | Q0 | LAG1_10 | HG10 | a0.5 | 6 | 0.01085 | 0.8333 | 0.03288 | -0.004359 | 0.1092 |
| Q0 | Q0 | VOL_HI15 | HG10 | a0.125 | 6 | 0.009823 | 0.6667 | 0.009741 | -0.002252 | 0.07113 |
| Q0 | Q0 | VOL_HI15 | HG10 | a0.25 | 6 | -0.03754 | 0.3333 | -0.03678 | -0.002532 | 0.07952 |
| Q0 | Q0 | VOL_HI15 | HG10 | a0.5 | 6 | 0.03339 | 0.6667 | 0.03874 | -0.005257 | 0.101 |
| Q0 | Q0 | VOL_HI15 | VOL_HI5 | a0.125 | 6 | -0.01349 | 0.3333 | -0.007488 | -0.00488 | 0.09503 |
| Q0 | Q0 | VOL_HI15 | VOL_HI5 | a0.25 | 6 | 0.04918 | 0.6667 | 0.04812 | -0.005011 | 0.1088 |
| Q0 | Q0 | VOL_HI15 | VOL_HI5 | a0.5 | 6 | -0.05728 | 0.3333 | -0.04456 | -0.006246 | 0.1452 |
| Q0 | Q0 | VOL_HI5 | HG10 | a0.125 | 6 | 0.001375 | 0.6667 | -0.001794 | 0.002489 | 0.07313 |
| Q0 | Q0 | VOL_HI5 | HG10 | a0.25 | 6 | -0.05457 | 0.3333 | -0.05644 | 0.001841 | 0.07691 |
| Q0 | Q0 | VOL_HI5 | HG10 | a0.5 | 6 | 0.09357 | 0.6667 | 0.09179 | 0.001746 | 0.0968 |
| Q0 | Q0 | VOL_MEAN15 | HG10 | a0.125 | 6 | 0.003622 | 0.5 | 0.005605 | -0.001878 | 0.04674 |
| Q0 | Q0 | VOL_MEAN15 | HG10 | a0.25 | 6 | 0.05533 | 0.6667 | 0.05774 | -0.001733 | 0.05049 |
| Q0 | Q0 | VOL_MEAN15 | HG10 | a0.5 | 6 | 0.04133 | 0.6667 | 0.04602 | -0.002186 | 0.06696 |
| Q0 | Q0 | VOL_MEAN15 | VOL_MEAN5 | a0.125 | 6 | 0.07208 | 0.6667 | 0.07607 | -0.003925 | 0.06584 |
| Q0 | Q0 | VOL_MEAN15 | VOL_MEAN5 | a0.25 | 6 | 0.03134 | 0.6667 | 0.02857 | -0.003201 | 0.07156 |
| Q0 | Q0 | VOL_MEAN15 | VOL_MEAN5 | a0.5 | 6 | 0.02278 | 0.6667 | 0.02761 | -0.004218 | 0.09689 |
| Q0 | Q0 | VOL_MEAN5 | HG10 | a0.125 | 6 | -0.01526 | 0.3333 | -0.01354 | 0.00198 | 0.04972 |
| Q0 | Q0 | VOL_MEAN5 | HG10 | a0.25 | 6 | -0.0244 | 0.3333 | -0.02694 | 0.00108 | 0.05365 |
| Q0 | Q0 | VOL_MEAN5 | HG10 | a0.5 | 6 | 0.021 | 0.8333 | 0.01921 | 0.00152 | 0.06538 |
| Q_D10 | Q_D10 | HG10 | HG5 | a0.125 | 6 | -0.00701 | 0.5 | -0.002578 | 0.004351 | 0.07178 |
| Q_D10 | Q_D10 | HG10 | HG5 | a0.25 | 6 | 0.06238 | 1 | 0.0565 | 0.005536 | 0.07649 |
| Q_D10 | Q_D10 | HG10 | HG5 | a0.5 | 6 | -0.01884 | 0.5 | -0.02059 | 0.005765 | 0.0829 |
| Q_D10 | Q_D10 | HG15 | HG10 | a0.125 | 6 | -0.04417 | 0 | -0.04483 | 0.00578 | 0.0763 |
| Q_D10 | Q_D10 | HG15 | HG10 | a0.25 | 6 | 0.02525 | 0.6667 | 0.03005 | 0.00547 | 0.07882 |
| Q_D10 | Q_D10 | HG15 | HG10 | a0.5 | 6 | -0.0345 | 0.3333 | -0.03968 | 0.005085 | 0.08469 |
| Q_D3 | Q_D3 | HG10 | HG5 | a0.125 | 6 | -0.06332 | 0.3333 | -0.06886 | 0.005439 | 0.07376 |
| Q_D3 | Q_D3 | HG10 | HG5 | a0.25 | 6 | 0.05894 | 1 | 0.05171 | 0.005656 | 0.0776 |
| Q_D3 | Q_D3 | HG10 | HG5 | a0.5 | 6 | 0.1241 | 0.6667 | 0.1311 | 0.007366 | 0.101 |
| Q_D3 | Q_D3 | HG15 | HG10 | a0.125 | 6 | -0.03654 | 0.3333 | -0.04185 | 0.005212 | 0.07454 |
| Q_D3 | Q_D3 | HG15 | HG10 | a0.25 | 6 | -0.06856 | 0.3333 | -0.07574 | 0.00645 | 0.08204 |
| Q_D3 | Q_D3 | HG15 | HG10 | a0.5 | 6 | 0.02863 | 0.6667 | 0.02383 | 0.006231 | 0.08956 |
| Q_D5 | Q_D5 | DECAY2_10 | DECAY5_10 | a0.125 | 6 | -0.004648 | 0.3333 | -0.004699 | -8.919e-05 | 0.01654 |
| Q_D5 | Q_D5 | DECAY2_10 | DECAY5_10 | a0.25 | 6 | -0.01975 | 0 | -0.02005 | -0.0002238 | 0.02036 |
| Q_D5 | Q_D5 | DECAY2_10 | DECAY5_10 | a0.5 | 6 | -0.04008 | 0 | -0.03926 | -0.0005675 | 0.03322 |
| Q_D5 | Q_D5 | DECAY2_10 | HG10 | a0.125 | 6 | 0.00142 | 0.6667 | 0.00171 | -0.0002198 | 0.02374 |
| Q_D5 | Q_D5 | DECAY2_10 | HG10 | a0.25 | 6 | -0.02227 | 0.1667 | -0.02266 | -0.0004272 | 0.02785 |
| Q_D5 | Q_D5 | DECAY2_10 | HG10 | a0.5 | 6 | -0.01766 | 0.1667 | -0.01607 | -0.0006446 | 0.04335 |
| Q_D5 | Q_D5 | DECAY5_10 | HG10 | a0.125 | 6 | 0.005554 | 0.6667 | 0.005518 | -3.827e-05 | 0.01657 |
| Q_D5 | Q_D5 | DECAY5_10 | HG10 | a0.25 | 6 | -0.002518 | 0.3333 | -0.002615 | -0.0001878 | 0.01815 |
| Q_D5 | Q_D5 | DECAY5_10 | HG10 | a0.5 | 6 | 0.01916 | 0.6667 | 0.01972 | -7.719e-05 | 0.02898 |
| Q_D5 | Q_D5 | HG10 | HG5 | a0.125 | 6 | 0.1115 | 0.6667 | 0.1077 | 0.003741 | 0.06904 |
| Q_D5 | Q_D5 | HG10 | HG5 | a0.25 | 6 | 0.1293 | 1 | 0.1329 | 0.005002 | 0.07693 |
| Q_D5 | Q_D5 | HG10 | HG5 | a0.5 | 6 | 0.2108 | 0.6667 | 0.2072 | 0.006566 | 0.08993 |
| Q_D5 | Q_D5 | HG15 | HG10 | a0.125 | 6 | 0.01601 | 0.6667 | 0.01001 | 0.005896 | 0.07263 |
| Q_D5 | Q_D5 | HG15 | HG10 | a0.25 | 6 | 0.005925 | 0.5 | 0.0001162 | 0.005461 | 0.07889 |
| Q_D5 | Q_D5 | HG15 | HG10 | a0.5 | 6 | -0.00503 | 0.5 | -0.01301 | 0.00536 | 0.08729 |
| Q_D5 | Q_D5 | HG20 | HG15 | a0.125 | 6 | -0.08308 | 0 | -0.08469 | 0.003651 | 0.08013 |
| Q_D5 | Q_D5 | HG20 | HG15 | a0.25 | 6 | 0.05414 | 0.6667 | 0.05323 | 0.007055 | 0.08269 |
| Q_D5 | Q_D5 | HG20 | HG15 | a0.5 | 6 | -0.04362 | 0.3333 | -0.05112 | 0.007363 | 0.09534 |
| Q_D5 | Q_D5 | HG30 | HG15 | a0.125 | 6 | -0.02147 | 0.5 | -0.0382 | 0.01643 | 0.1313 |
| Q_D5 | Q_D5 | HG30 | HG15 | a0.25 | 6 | 0.03223 | 0.6667 | 0.005833 | 0.02056 | 0.149 |
| Q_D5 | Q_D5 | HG30 | HG15 | a0.5 | 6 | -0.09371 | 0.3333 | -0.1229 | 0.02077 | 0.1586 |
| Q_D5 | Q_D5 | INV10 | HG10 | a0.125 | 6 | -0.01419 | 0.5 | -0.02384 | 0.003723 | 0.09051 |
| Q_D5 | Q_D5 | INV10 | HG10 | a0.25 | 6 | 0.055 | 0.6667 | 0.04675 | 0.003297 | 0.09857 |
| Q_D5 | Q_D5 | INV10 | HG10 | a0.5 | 6 | 0.1667 | 0.8333 | 0.1694 | 0.007027 | 0.1342 |
| Q_D5 | Q_D5 | INV10 | LAG1_10 | a0.125 | 6 | -0.004503 | 0.5 | -0.01477 | 0.00521 | 0.09152 |
| Q_D5 | Q_D5 | INV10 | LAG1_10 | a0.25 | 6 | 0.04598 | 0.8333 | 0.03484 | 0.004814 | 0.1023 |
| Q_D5 | Q_D5 | INV10 | LAG1_10 | a0.5 | 6 | 0.1561 | 0.6667 | 0.1335 | 0.01042 | 0.1385 |
| Q_D5 | Q_D5 | LAG1_10 | HG10 | a0.125 | 6 | -0.00969 | 0.5 | -0.009074 | -0.0006048 | 0.04088 |
| Q_D5 | Q_D5 | LAG1_10 | HG10 | a0.25 | 6 | -0.03176 | 0.3333 | -0.03147 | -0.00028 | 0.04841 |
| Q_D5 | Q_D5 | LAG1_10 | HG10 | a0.5 | 6 | -0.01949 | 0.3333 | -0.01522 | -0.003391 | 0.06169 |
| Q_D5 | Q_D5 | VOL_HI15 | HG10 | a0.125 | 6 | -0.09449 | 0.3333 | -0.09556 | -0.001077 | 0.06874 |
| Q_D5 | Q_D5 | VOL_HI15 | HG10 | a0.25 | 6 | -0.02367 | 0.5 | -0.02277 | -0.002099 | 0.07256 |
| Q_D5 | Q_D5 | VOL_HI15 | HG10 | a0.5 | 6 | -0.07258 | 0 | -0.07089 | -0.002222 | 0.08648 |
| Q_D5 | Q_D5 | VOL_HI15 | VOL_HI5 | a0.125 | 6 | -0.01288 | 0.3333 | -0.01059 | -0.003928 | 0.09605 |
| Q_D5 | Q_D5 | VOL_HI15 | VOL_HI5 | a0.25 | 6 | 0.04859 | 0.6667 | 0.05403 | -0.004515 | 0.1082 |
| Q_D5 | Q_D5 | VOL_HI15 | VOL_HI5 | a0.5 | 6 | 0.01153 | 0.6667 | 0.01347 | -0.003781 | 0.1249 |
| Q_D5 | Q_D5 | VOL_HI5 | HG10 | a0.125 | 6 | 0.03563 | 0.6667 | 0.03321 | 0.002325 | 0.06895 |
| Q_D5 | Q_D5 | VOL_HI5 | HG10 | a0.25 | 6 | -0.09196 | 0.3333 | -0.09506 | 0.002416 | 0.07828 |
| Q_D5 | Q_D5 | VOL_HI5 | HG10 | a0.5 | 6 | -0.09035 | 0.1667 | -0.09174 | 0.001744 | 0.08675 |
| Q_D5 | Q_D5 | VOL_MEAN15 | HG10 | a0.125 | 6 | -0.04928 | 0 | -0.04735 | -0.001896 | 0.0444 |
| Q_D5 | Q_D5 | VOL_MEAN15 | HG10 | a0.25 | 6 | -0.07861 | 0 | -0.07645 | -0.001694 | 0.04958 |
| Q_D5 | Q_D5 | VOL_MEAN15 | HG10 | a0.5 | 6 | 0.00142 | 0.5 | 0.003776 | -0.002314 | 0.05355 |
| Q_D5 | Q_D5 | VOL_MEAN15 | VOL_MEAN5 | a0.125 | 6 | -0.06813 | 0 | -0.06388 | -0.004171 | 0.06499 |
| Q_D5 | Q_D5 | VOL_MEAN15 | VOL_MEAN5 | a0.25 | 6 | -0.08585 | 0 | -0.08445 | -0.00392 | 0.07015 |
| Q_D5 | Q_D5 | VOL_MEAN15 | VOL_MEAN5 | a0.5 | 6 | 0.02561 | 0.6667 | 0.02983 | -0.004138 | 0.07346 |
| Q_D5 | Q_D5 | VOL_MEAN5 | HG10 | a0.125 | 6 | -0.007437 | 0.5 | -0.005961 | 0.002264 | 0.04871 |
| Q_D5 | Q_D5 | VOL_MEAN5 | HG10 | a0.25 | 6 | 0.007182 | 0.5 | 0.006623 | 0.002226 | 0.05003 |
| Q_D5 | Q_D5 | VOL_MEAN5 | HG10 | a0.5 | 6 | -0.01439 | 0 | -0.01546 | 0.001824 | 0.05309 |
| Q_DEW3 | Q_DEW3 | HG10 | HG5 | a0.125 | 6 | -0.03182 | 0.3333 | -0.03107 | 0.005215 | 0.06896 |
| Q_DEW3 | Q_DEW3 | HG10 | HG5 | a0.25 | 6 | -0.04801 | 0.1667 | -0.04887 | 0.005565 | 0.07669 |
| Q_DEW3 | Q_DEW3 | HG10 | HG5 | a0.5 | 6 | -0.04962 | 0.3333 | -0.04907 | 0.0067 | 0.09512 |
| Q_DEW3 | Q_DEW3 | HG15 | HG10 | a0.125 | 6 | -0.03192 | 0.1667 | -0.03854 | 0.005365 | 0.07763 |
| Q_DEW3 | Q_DEW3 | HG15 | HG10 | a0.25 | 6 | -0.005891 | 0.3333 | -0.01219 | 0.005711 | 0.08133 |
| Q_DEW3 | Q_DEW3 | HG15 | HG10 | a0.5 | 6 | -0.1679 | 0 | -0.1685 | 0.006398 | 0.09718 |
| Q_DEW5 | Q_DEW5 | HG10 | HG5 | a0.125 | 6 | 0.05815 | 0.6667 | 0.06327 | 0.005094 | 0.06922 |
| Q_DEW5 | Q_DEW5 | HG10 | HG5 | a0.25 | 6 | 0.03567 | 0.6667 | 0.03633 | 0.004932 | 0.07463 |
| Q_DEW5 | Q_DEW5 | HG10 | HG5 | a0.5 | 6 | 0.06508 | 0.6667 | 0.0656 | 0.007093 | 0.09098 |
| Q_DEW5 | Q_DEW5 | HG15 | HG10 | a0.125 | 6 | -0.01894 | 0.3333 | -0.02056 | 0.005682 | 0.07224 |
| Q_DEW5 | Q_DEW5 | HG15 | HG10 | a0.25 | 6 | 0.06784 | 0.6667 | 0.06681 | 0.006704 | 0.08404 |
| Q_DEW5 | Q_DEW5 | HG15 | HG10 | a0.5 | 6 | -0.05759 | 0.3333 | -0.06006 | 0.005361 | 0.09371 |
| Q_DMED5 | Q_DMED5 | HG10 | HG5 | a0.125 | 6 | 0.03105 | 0.6667 | 0.0354 | 0.005224 | 0.07035 |
| Q_DMED5 | Q_DMED5 | HG10 | HG5 | a0.25 | 6 | 0.01796 | 0.8333 | 0.01702 | 0.004924 | 0.0738 |
| Q_DMED5 | Q_DMED5 | HG10 | HG5 | a0.5 | 6 | 0.002531 | 0.5 | 0.0003171 | 0.007293 | 0.08577 |
| Q_DMED5 | Q_DMED5 | HG15 | HG10 | a0.125 | 6 | 0.03133 | 0.6667 | 0.03035 | 0.004803 | 0.07586 |
| Q_DMED5 | Q_DMED5 | HG15 | HG10 | a0.25 | 6 | -0.0196 | 0.5 | -0.02643 | 0.005874 | 0.08181 |
| Q_DMED5 | Q_DMED5 | HG15 | HG10 | a0.5 | 6 | -0.009051 | 0.3333 | -0.01085 | 0.005905 | 0.0878 |
| Q_QMEAN5 | Q_QMEAN5 | HG10 | HG5 | a0.125 | 6 | 0.01354 | 0.5 | 0.009533 | 0.003937 | 0.07138 |
| Q_QMEAN5 | Q_QMEAN5 | HG10 | HG5 | a0.25 | 6 | 0.04137 | 1 | 0.04192 | 0.005038 | 0.07543 |
| Q_QMEAN5 | Q_QMEAN5 | HG10 | HG5 | a0.5 | 6 | 0.1298 | 1 | 0.1197 | 0.006979 | 0.0926 |
| Q_QMEAN5 | Q_QMEAN5 | HG15 | HG10 | a0.125 | 6 | 0.01443 | 0.6667 | 0.009011 | 0.00532 | 0.078 |
| Q_QMEAN5 | Q_QMEAN5 | HG15 | HG10 | a0.25 | 6 | -0.03428 | 0.3333 | -0.04054 | 0.006151 | 0.07524 |
| Q_QMEAN5 | Q_QMEAN5 | HG15 | HG10 | a0.5 | 6 | -0.1319 | 0 | -0.1373 | 0.005261 | 0.1044 |
| Q_RANK10 | Q_RANK10 | HG10 | HG5 | a0.125 | 6 | 0.08848 | 0.6667 | 0.08441 | 0.003999 | 0.07309 |
| Q_RANK10 | Q_RANK10 | HG10 | HG5 | a0.25 | 6 | 0.02394 | 0.6667 | 0.02727 | 0.005483 | 0.07268 |
| Q_RANK10 | Q_RANK10 | HG10 | HG5 | a0.5 | 6 | 0.03794 | 0.8333 | 0.03294 | 0.004908 | 0.09606 |
| Q_RANK10 | Q_RANK10 | HG15 | HG10 | a0.125 | 6 | 0.01114 | 0.8333 | 0.009041 | 0.005135 | 0.07469 |
| Q_RANK10 | Q_RANK10 | HG15 | HG10 | a0.25 | 6 | 0.04514 | 1 | 0.03857 | 0.006358 | 0.07746 |
| Q_RANK10 | Q_RANK10 | HG15 | HG10 | a0.5 | 6 | 0.004302 | 0.5 | -0.00369 | 0.006709 | 0.08788 |
| Q_RANK3 | Q_RANK3 | HG10 | HG5 | a0.125 | 6 | -0.04279 | 0.3333 | -0.04711 | 0.004237 | 0.07183 |
| Q_RANK3 | Q_RANK3 | HG10 | HG5 | a0.25 | 6 | 0.106 | 0.6667 | 0.0985 | 0.006372 | 0.08068 |
| Q_RANK3 | Q_RANK3 | HG10 | HG5 | a0.5 | 6 | -0.03041 | 0.1667 | -0.0346 | 0.006462 | 0.1111 |
| Q_RANK3 | Q_RANK3 | HG15 | HG10 | a0.125 | 6 | -0.03576 | 0.3333 | -0.03144 | 0.005219 | 0.07612 |
| Q_RANK3 | Q_RANK3 | HG15 | HG10 | a0.25 | 6 | 0.01731 | 0.5 | 0.01059 | 0.005859 | 0.08428 |
| Q_RANK3 | Q_RANK3 | HG15 | HG10 | a0.5 | 6 | -0.1301 | 0.3333 | -0.1306 | 0.005802 | 0.0922 |
| Q_RANK5 | Q_RANK5 | DECAY2_10 | DECAY5_10 | a0.125 | 6 | -0.01014 | 0.3333 | -0.01028 | -0.0001582 | 0.01652 |
| Q_RANK5 | Q_RANK5 | DECAY2_10 | DECAY5_10 | a0.25 | 6 | -0.01242 | 0.3333 | -0.01301 | 3.463e-05 | 0.02321 |
| Q_RANK5 | Q_RANK5 | DECAY2_10 | DECAY5_10 | a0.5 | 6 | 0.00999 | 0.6667 | 0.01004 | -0.0001982 | 0.03788 |
| Q_RANK5 | Q_RANK5 | DECAY2_10 | HG10 | a0.125 | 6 | -0.0209 | 0.3333 | -0.02043 | -0.000383 | 0.02433 |
| Q_RANK5 | Q_RANK5 | DECAY2_10 | HG10 | a0.25 | 6 | -0.01645 | 0.1667 | -0.01732 | -9.912e-05 | 0.031 |
| Q_RANK5 | Q_RANK5 | DECAY2_10 | HG10 | a0.5 | 6 | -0.005185 | 0.5 | -0.004099 | -0.0004624 | 0.04759 |
| Q_RANK5 | Q_RANK5 | DECAY5_10 | HG10 | a0.125 | 6 | -0.009349 | 0.3333 | -0.00912 | -0.0002248 | 0.01757 |
| Q_RANK5 | Q_RANK5 | DECAY5_10 | HG10 | a0.25 | 6 | -0.01553 | 0 | -0.01527 | -0.000128 | 0.02051 |
| Q_RANK5 | Q_RANK5 | DECAY5_10 | HG10 | a0.5 | 6 | 0.01801 | 0.6667 | 0.01858 | -0.0001895 | 0.02943 |
| Q_RANK5 | Q_RANK5 | HG10 | HG5 | a0.125 | 6 | -0.02178 | 0.5 | -0.02534 | 0.003498 | 0.07149 |
| Q_RANK5 | Q_RANK5 | HG10 | HG5 | a0.25 | 6 | 0.09625 | 1 | 0.0954 | 0.005675 | 0.08321 |
| Q_RANK5 | Q_RANK5 | HG10 | HG5 | a0.5 | 6 | -0.02159 | 0.5 | -0.02216 | 0.0046 | 0.09072 |
| Q_RANK5 | Q_RANK5 | HG15 | HG10 | a0.125 | 6 | 0.0876 | 0.6667 | 0.08248 | 0.004683 | 0.07625 |
| Q_RANK5 | Q_RANK5 | HG15 | HG10 | a0.25 | 6 | 0.06082 | 1 | 0.0542 | 0.006204 | 0.08037 |
| Q_RANK5 | Q_RANK5 | HG15 | HG10 | a0.5 | 6 | 0.1375 | 0.6667 | 0.1262 | 0.006656 | 0.09111 |
| Q_RANK5 | Q_RANK5 | INV10 | HG10 | a0.125 | 6 | 0.1117 | 1 | 0.1026 | 0.003085 | 0.08994 |
| Q_RANK5 | Q_RANK5 | INV10 | HG10 | a0.25 | 6 | 0.144 | 0.8333 | 0.1347 | 0.004438 | 0.09764 |
| Q_RANK5 | Q_RANK5 | INV10 | HG10 | a0.5 | 6 | 0.1828 | 1 | 0.16 | 0.008244 | 0.145 |
| Q_RANK5 | Q_RANK5 | INV10 | LAG1_10 | a0.125 | 6 | 0.1091 | 1 | 0.09967 | 0.00468 | 0.09257 |
| Q_RANK5 | Q_RANK5 | INV10 | LAG1_10 | a0.25 | 6 | 0.1549 | 1 | 0.1382 | 0.005496 | 0.102 |
| Q_RANK5 | Q_RANK5 | INV10 | LAG1_10 | a0.5 | 6 | 0.2186 | 1 | 0.1901 | 0.01193 | 0.1482 |
| Q_RANK5 | Q_RANK5 | LAG1_10 | HG10 | a0.125 | 6 | 0.001426 | 0.5 | 0.0007301 | -0.0003878 | 0.04165 |
| Q_RANK5 | Q_RANK5 | LAG1_10 | HG10 | a0.25 | 6 | -0.04968 | 0.1667 | -0.05057 | -0.0007279 | 0.0497 |
| Q_RANK5 | Q_RANK5 | LAG1_10 | HG10 | a0.5 | 6 | -0.01357 | 0.1667 | -0.01119 | -0.002334 | 0.06246 |


> 表头：主体=MA vs EW（D3 − DEW3、D5 − DEW5）｜算子=MA_VS_EW｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=各端原生｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-MAEW


| meas | right_meas | op | right_op | alpha | cells | median_D_ann_pp | share_pos | median_Dg_ann_pp | median_fee_ann_pp | median_se_H_ann_pp |
|---|---|---|---|---|---|---|---|---|---|---|
| Q_D3 | Q_DEW3 | HG10 | HG10 | a0.125 | 6 | -0.03398 | 0.3333 | -0.03199 | -0.001655 | 0.05557 |
| Q_D3 | Q_DEW3 | HG10 | HG10 | a0.25 | 6 | 0.0291 | 0.8333 | 0.03399 | -0.004098 | 0.08706 |
| Q_D3 | Q_DEW3 | HG10 | HG10 | a0.5 | 6 | -0.06532 | 0.3333 | -0.08269 | -0.01099 | 0.1374 |
| Q_D3 | Q_DEW3 | HG15 | HG15 | a0.125 | 6 | -0.03112 | 0.3333 | -0.03192 | -0.001808 | 0.05968 |
| Q_D3 | Q_DEW3 | HG15 | HG15 | a0.25 | 6 | -0.03755 | 0.1667 | -0.04092 | -0.003836 | 0.08968 |
| Q_D3 | Q_DEW3 | HG15 | HG15 | a0.5 | 6 | 0.07305 | 0.8333 | 0.07205 | -0.01115 | 0.1394 |
| Q_D3 | Q_DEW3 | HG5 | HG5 | a0.125 | 6 | 0.03498 | 0.6667 | 0.03774 | -0.001826 | 0.05502 |
| Q_D3 | Q_DEW3 | HG5 | HG5 | a0.25 | 6 | -0.08054 | 0 | -0.08117 | -0.004665 | 0.07915 |
| Q_D3 | Q_DEW3 | HG5 | HG5 | a0.5 | 6 | -0.2532 | 0.3333 | -0.2706 | -0.01165 | 0.1217 |
| Q_D3 | Q_DEW3 | NATIVE | NATIVE | a0.125 | 6 | -0.01957 | 0.3333 | -0.01978 | -0.0023 | 0.05348 |
| Q_D3 | Q_DEW3 | NATIVE | NATIVE | a0.25 | 6 | -0.006117 | 0.5 | -0.003435 | -0.004207 | 0.07486 |
| Q_D3 | Q_DEW3 | NATIVE | NATIVE | a0.5 | 6 | -0.1852 | 0.3333 | -0.204 | -0.01117 | 0.1175 |
| Q_D5 | Q_DEW5 | HG10 | HG10 | a0.125 | 6 | 0.02854 | 0.8333 | 0.02771 | -0.002115 | 0.05306 |
| Q_D5 | Q_DEW5 | HG10 | HG10 | a0.25 | 6 | 0.04794 | 1 | 0.05357 | -0.003705 | 0.0793 |
| Q_D5 | Q_DEW5 | HG10 | HG10 | a0.5 | 6 | -0.02351 | 0.3333 | -0.01768 | -0.01372 | 0.126 |
| Q_D5 | Q_DEW5 | HG15 | HG15 | a0.125 | 6 | 0.02536 | 0.8333 | 0.02637 | -0.002015 | 0.05656 |
| Q_D5 | Q_DEW5 | HG15 | HG15 | a0.25 | 6 | 0.0007575 | 0.5 | -0.002505 | -0.006061 | 0.08314 |
| Q_D5 | Q_DEW5 | HG15 | HG15 | a0.5 | 6 | 0.003128 | 0.5 | -0.007967 | -0.01372 | 0.1384 |
| Q_D5 | Q_DEW5 | HG5 | HG5 | a0.125 | 6 | -0.01756 | 0.3333 | -0.01533 | -0.0008855 | 0.0515 |
| Q_D5 | Q_DEW5 | HG5 | HG5 | a0.25 | 6 | -0.07146 | 0 | -0.0722 | -0.003776 | 0.07734 |
| Q_D5 | Q_DEW5 | HG5 | HG5 | a0.5 | 6 | -0.16 | 0.1667 | -0.1565 | -0.0132 | 0.1205 |
| Q_D5 | Q_DEW5 | NATIVE | NATIVE | a0.125 | 6 | 0.06885 | 0.8333 | 0.06764 | -0.0007367 | 0.05233 |
| Q_D5 | Q_DEW5 | NATIVE | NATIVE | a0.25 | 6 | -0.01239 | 0.5 | -0.01446 | -0.00274 | 0.07291 |
| Q_D5 | Q_DEW5 | NATIVE | NATIVE | a0.5 | 6 | -0.2801 | 0.3333 | -0.2831 | -0.01322 | 0.1158 |


> 表头：主体=均值核配对（D5 − QMEAN5、D5 − DMED5、QMEAN5 − DMED5）｜算子=MEAN_KERNEL_PAIR｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=各端原生｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-MEANK


| meas | right_meas | op | right_op | alpha | cells | median_D_ann_pp | share_pos | median_Dg_ann_pp | median_fee_ann_pp | median_se_H_ann_pp |
|---|---|---|---|---|---|---|---|---|---|---|
| Q_D5 | Q_DMED5 | HG10 | HG10 | a0.125 | 6 | 0.0399 | 0.8333 | 0.04116 | -0.001233 | 0.0716 |
| Q_D5 | Q_DMED5 | HG10 | HG10 | a0.25 | 6 | 0.0205 | 0.6667 | 0.02013 | 0.0003563 | 0.1168 |
| Q_D5 | Q_DMED5 | HG10 | HG10 | a0.5 | 6 | 0.09497 | 0.8333 | 0.08027 | 0.01092 | 0.1933 |
| Q_D5 | Q_DMED5 | HG15 | HG15 | a0.125 | 6 | 0.06243 | 1 | 0.06475 | -0.000132 | 0.07786 |
| Q_D5 | Q_DMED5 | HG15 | HG15 | a0.25 | 6 | 0.005185 | 0.5 | 0.005314 | -0.0005726 | 0.1127 |
| Q_D5 | Q_DMED5 | HG15 | HG15 | a0.5 | 6 | 0.02005 | 0.6667 | 0.005801 | 0.01235 | 0.1998 |
| Q_D5 | Q_DMED5 | HG5 | HG5 | a0.125 | 6 | 0.04033 | 0.6667 | 0.04512 | 0.0002497 | 0.06908 |
| Q_D5 | Q_DMED5 | HG5 | HG5 | a0.25 | 6 | -0.1174 | 0.3333 | -0.1177 | 0.0002781 | 0.105 |
| Q_D5 | Q_DMED5 | HG5 | HG5 | a0.5 | 6 | -0.003227 | 0.5 | -0.02176 | 0.01173 | 0.1771 |
| Q_D5 | Q_DMED5 | NATIVE | NATIVE | a0.125 | 6 | 0.04004 | 0.8333 | 0.03919 | 0.0008406 | 0.06911 |
| Q_D5 | Q_DMED5 | NATIVE | NATIVE | a0.25 | 6 | -0.04791 | 0.3333 | -0.05322 | 0.001877 | 0.09118 |
| Q_D5 | Q_DMED5 | NATIVE | NATIVE | a0.5 | 6 | 0.0002019 | 0.5 | -0.001369 | 0.01185 | 0.1805 |
| Q_D5 | Q_QMEAN5 | HG10 | HG10 | a0.125 | 6 | 0.01302 | 0.8333 | 0.01515 | 0.0004688 | 0.08186 |
| Q_D5 | Q_QMEAN5 | HG10 | HG10 | a0.25 | 6 | -0.002505 | 0.5 | -0.004566 | 0.002025 | 0.1377 |
| Q_D5 | Q_QMEAN5 | HG10 | HG10 | a0.5 | 6 | -0.2769 | 0.3333 | -0.2848 | 0.007803 | 0.2926 |
| Q_D5 | Q_QMEAN5 | HG15 | HG15 | a0.125 | 6 | 0.03404 | 0.6667 | 0.03155 | 0.001054 | 0.09252 |
| Q_D5 | Q_QMEAN5 | HG15 | HG15 | a0.25 | 6 | 0.03675 | 0.6667 | 0.04367 | 0.0006798 | 0.1388 |
| Q_D5 | Q_QMEAN5 | HG15 | HG15 | a0.5 | 6 | -0.03236 | 0.5 | -0.04156 | 0.009039 | 0.3018 |
| Q_D5 | Q_QMEAN5 | HG5 | HG5 | a0.125 | 6 | -0.03934 | 0.1667 | -0.03371 | 0.0006649 | 0.07961 |
| Q_D5 | Q_QMEAN5 | HG5 | HG5 | a0.25 | 6 | -0.1273 | 0 | -0.1294 | 0.002061 | 0.13 |
| Q_D5 | Q_QMEAN5 | HG5 | HG5 | a0.5 | 6 | -0.3008 | 0.3333 | -0.3255 | 0.01268 | 0.2744 |
| Q_D5 | Q_QMEAN5 | NATIVE | NATIVE | a0.125 | 6 | 0.006091 | 0.6667 | 0.0174 | 0.002139 | 0.07861 |
| Q_D5 | Q_QMEAN5 | NATIVE | NATIVE | a0.25 | 6 | -0.0929 | 0 | -0.09656 | 0.003222 | 0.1234 |
| Q_D5 | Q_QMEAN5 | NATIVE | NATIVE | a0.5 | 6 | -0.2228 | 0.3333 | -0.2513 | 0.0171 | 0.2609 |
| Q_QMEAN5 | Q_DMED5 | HG10 | HG10 | a0.125 | 6 | 0.02272 | 0.6667 | 0.02451 | -0.001641 | 0.08343 |
| Q_QMEAN5 | Q_DMED5 | HG10 | HG10 | a0.25 | 6 | 0.06479 | 1 | 0.05816 | -0.001669 | 0.1236 |
| Q_QMEAN5 | Q_DMED5 | HG10 | HG10 | a0.5 | 6 | 0.3681 | 1 | 0.3651 | 0.00663 | 0.2558 |
| Q_QMEAN5 | Q_DMED5 | HG15 | HG15 | a0.125 | 6 | 0.02051 | 0.6667 | 0.02171 | -0.001179 | 0.0871 |
| Q_QMEAN5 | Q_DMED5 | HG15 | HG15 | a0.25 | 6 | 0.01323 | 0.5 | 0.0006371 | -0.001252 | 0.128 |
| Q_QMEAN5 | Q_DMED5 | HG15 | HG15 | a0.5 | 6 | 0.1066 | 0.8333 | 0.0649 | 0.009412 | 0.2703 |
| Q_QMEAN5 | Q_DMED5 | HG5 | HG5 | a0.125 | 6 | 0.06946 | 1 | 0.06755 | -0.0004152 | 0.07634 |
| Q_QMEAN5 | Q_DMED5 | HG5 | HG5 | a0.25 | 6 | 0.03131 | 1 | 0.02599 | -0.001783 | 0.1167 |
| Q_QMEAN5 | Q_DMED5 | HG5 | HG5 | a0.5 | 6 | 0.2976 | 0.6667 | 0.3037 | 0.001982 | 0.2394 |
| Q_QMEAN5 | Q_DMED5 | NATIVE | NATIVE | a0.125 | 6 | 0.04657 | 0.8333 | 0.03775 | -0.001123 | 0.07351 |
| Q_QMEAN5 | Q_DMED5 | NATIVE | NATIVE | a0.25 | 6 | 0.07894 | 1 | 0.08289 | -0.001345 | 0.1164 |
| Q_QMEAN5 | Q_DMED5 | NATIVE | NATIVE | a0.5 | 6 | 0.1884 | 0.6667 | 0.1988 | -0.00458 | 0.2218 |


> 表头：主体=秩桥（RANK5 − RANKOBS5、RANK5 − RANKSCORE5）｜算子=RANK_BRIDGE_PAIR｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=各端原生｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-RANKB


| meas | right_meas | op | right_op | alpha | cells | median_D_ann_pp | share_pos | median_Dg_ann_pp | median_fee_ann_pp | median_se_H_ann_pp |
|---|---|---|---|---|---|---|---|---|---|---|
| Q_RANK5 | Q_RANKOBS5 | HG10 | HG10 | a0.125 | 6 | 0.01975 | 1 | 0.02081 | 0.001563 | 0.06565 |
| Q_RANK5 | Q_RANKOBS5 | HG10 | HG10 | a0.25 | 6 | 0.1073 | 1 | 0.115 | 0.00489 | 0.09313 |
| Q_RANK5 | Q_RANKOBS5 | HG10 | HG10 | a0.5 | 6 | 0.1153 | 1 | 0.1191 | 0.009677 | 0.1951 |
| Q_RANK5 | Q_RANKOBS5 | NATIVE | NATIVE | a0.125 | 6 | 0.1244 | 0.6667 | 0.1224 | 0.001953 | 0.05892 |
| Q_RANK5 | Q_RANKOBS5 | NATIVE | NATIVE | a0.25 | 6 | 0.0966 | 1 | 0.09065 | 0.004417 | 0.08764 |
| Q_RANK5 | Q_RANKOBS5 | NATIVE | NATIVE | a0.5 | 6 | 0.2855 | 1 | 0.284 | 0.004145 | 0.1718 |
| Q_RANK5 | Q_RANKSCORE5 | HG10 | HG10 | a0.125 | 6 | -0.01616 | 0.3333 | -0.01871 | 0.004335 | 0.06961 |
| Q_RANK5 | Q_RANKSCORE5 | HG10 | HG10 | a0.25 | 6 | 0.07696 | 0.6667 | 0.06621 | 0.00639 | 0.1027 |
| Q_RANK5 | Q_RANKSCORE5 | HG10 | HG10 | a0.5 | 6 | -0.1481 | 0 | -0.147 | 0.02116 | 0.1986 |
| Q_RANK5 | Q_RANKSCORE5 | NATIVE | NATIVE | a0.125 | 6 | 0.1297 | 0.6667 | 0.1253 | 0.004296 | 0.06205 |
| Q_RANK5 | Q_RANKSCORE5 | NATIVE | NATIVE | a0.25 | 6 | 0.03793 | 1 | 0.03641 | 0.008638 | 0.09551 |
| Q_RANK5 | Q_RANKSCORE5 | NATIVE | NATIVE | a0.5 | 6 | -0.07783 | 0 | -0.0983 | 0.01883 | 0.1748 |


> 表头：主体=窗口配对（D5 − D3、D10 − D5、RANK5 − RANK3、RANK10 − RANK5）｜算子=WINDOW_PAIR｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=各端原生｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-WINDOW


| meas | right_meas | op | right_op | alpha | cells | median_D_ann_pp | share_pos | median_Dg_ann_pp | median_fee_ann_pp | median_se_H_ann_pp |
|---|---|---|---|---|---|---|---|---|---|---|
| Q_D10 | Q_D5 | HG10 | HG10 | a0.125 | 6 | -0.01713 | 0.5 | -0.01483 | -0.0002554 | 0.06907 |
| Q_D10 | Q_D5 | HG10 | HG10 | a0.25 | 6 | 0.02263 | 0.6667 | 0.02992 | 0.00134 | 0.1012 |
| Q_D10 | Q_D5 | HG10 | HG10 | a0.5 | 6 | 0.01551 | 0.6667 | 0.00637 | 0.01105 | 0.1862 |
| Q_D10 | Q_D5 | HG15 | HG15 | a0.125 | 6 | -0.05354 | 0 | -0.05291 | 0.0001968 | 0.0711 |
| Q_D10 | Q_D5 | HG15 | HG15 | a0.25 | 6 | 0.01753 | 0.5 | 0.01984 | 0.001413 | 0.1086 |
| Q_D10 | Q_D5 | HG15 | HG15 | a0.5 | 6 | 0.003993 | 0.5 | -0.006976 | 0.01078 | 0.201 |
| Q_D10 | Q_D5 | HG5 | HG5 | a0.125 | 6 | -0.006231 | 0.5 | -0.006435 | -0.0002887 | 0.06411 |
| Q_D10 | Q_D5 | HG5 | HG5 | a0.25 | 6 | 0.0849 | 1 | 0.08838 | 0.0006457 | 0.0897 |
| Q_D10 | Q_D5 | HG5 | HG5 | a0.5 | 6 | 0.1112 | 0.8333 | 0.09382 | 0.01185 | 0.1793 |
| Q_D10 | Q_D5 | NATIVE | NATIVE | a0.125 | 6 | -0.01621 | 0.3333 | -0.01726 | -0.0008404 | 0.06562 |
| Q_D10 | Q_D5 | NATIVE | NATIVE | a0.25 | 6 | 0.0684 | 1 | 0.07297 | 0.0003358 | 0.09442 |
| Q_D10 | Q_D5 | NATIVE | NATIVE | a0.5 | 6 | 0.1307 | 1 | 0.119 | 0.01149 | 0.1751 |
| Q_D5 | Q_D3 | HG10 | HG10 | a0.125 | 6 | 0.04715 | 1 | 0.04837 | -0.001205 | 0.06585 |
| Q_D5 | Q_D3 | HG10 | HG10 | a0.25 | 6 | -0.01125 | 0.5 | -0.0104 | -0.0009946 | 0.09211 |
| Q_D5 | Q_D3 | HG10 | HG10 | a0.5 | 6 | -0.03056 | 0.5 | -0.02687 | -0.002336 | 0.1587 |
| Q_D5 | Q_D3 | HG15 | HG15 | a0.125 | 6 | 0.07606 | 1 | 0.07615 | -0.0005123 | 0.06779 |
| Q_D5 | Q_D3 | HG15 | HG15 | a0.25 | 6 | 0.04365 | 1 | 0.04864 | -0.002173 | 0.09676 |
| Q_D5 | Q_D3 | HG15 | HG15 | a0.5 | 6 | -0.009058 | 0.3333 | -0.006768 | -0.0007163 | 0.1633 |
| Q_D5 | Q_D3 | HG5 | HG5 | a0.125 | 6 | -0.01587 | 0.3333 | -0.01444 | -0.0006318 | 0.06114 |
| Q_D5 | Q_D3 | HG5 | HG5 | a0.25 | 6 | -0.09078 | 0 | -0.08631 | -0.0001913 | 0.08891 |
| Q_D5 | Q_D3 | HG5 | HG5 | a0.5 | 6 | -0.1105 | 0 | -0.1085 | 0.0006239 | 0.1431 |
| Q_D5 | Q_D3 | NATIVE | NATIVE | a0.125 | 6 | 0.07893 | 0.8333 | 0.0796 | -0.0007317 | 0.05951 |
| Q_D5 | Q_D3 | NATIVE | NATIVE | a0.25 | 6 | -0.05467 | 0.1667 | -0.05524 | 0.0005016 | 0.08341 |
| Q_D5 | Q_D3 | NATIVE | NATIVE | a0.5 | 6 | -0.1132 | 0.1667 | -0.1108 | 0.002451 | 0.1406 |
| Q_RANK10 | Q_RANK5 | HG10 | HG10 | a0.125 | 6 | 0.05492 | 0.6667 | 0.05611 | -0.0007757 | 0.07345 |
| Q_RANK10 | Q_RANK5 | HG10 | HG10 | a0.25 | 6 | 0.03653 | 0.6667 | 0.03797 | -0.000124 | 0.105 |
| Q_RANK10 | Q_RANK5 | HG10 | HG10 | a0.5 | 6 | 0.07272 | 0.6667 | 0.06187 | 0.01066 | 0.2173 |
| Q_RANK10 | Q_RANK5 | HG15 | HG15 | a0.125 | 6 | -0.02189 | 0.3333 | -0.02075 | -0.0007012 | 0.07307 |
| Q_RANK10 | Q_RANK5 | HG15 | HG15 | a0.25 | 6 | 0.04172 | 0.6667 | 0.0406 | 0.0001451 | 0.1093 |
| Q_RANK10 | Q_RANK5 | HG15 | HG15 | a0.5 | 6 | 0.02081 | 0.6667 | 0.009913 | 0.01071 | 0.2205 |
| Q_RANK10 | Q_RANK5 | HG5 | HG5 | a0.125 | 6 | -0.001863 | 0.3333 | 0.0008862 | -0.00171 | 0.07073 |
| Q_RANK10 | Q_RANK5 | HG5 | HG5 | a0.25 | 6 | 0.07714 | 1 | 0.07883 | -2.801e-05 | 0.09969 |
| Q_RANK10 | Q_RANK5 | HG5 | HG5 | a0.5 | 6 | 0.03118 | 0.6667 | 0.008719 | 0.01035 | 0.2057 |
| Q_RANK10 | Q_RANK5 | NATIVE | NATIVE | a0.125 | 6 | -0.003871 | 0.5 | -0.003548 | -0.001234 | 0.06296 |
| Q_RANK10 | Q_RANK5 | NATIVE | NATIVE | a0.25 | 6 | -0.01431 | 0.1667 | -0.01261 | -0.001286 | 0.1009 |
| Q_RANK10 | Q_RANK5 | NATIVE | NATIVE | a0.5 | 6 | 0.1007 | 0.6667 | 0.09154 | 0.01063 | 0.201 |
| Q_RANK5 | Q_RANK3 | HG10 | HG10 | a0.125 | 6 | -0.05087 | 0.3333 | -0.0505 | -0.0008442 | 0.06937 |
| Q_RANK5 | Q_RANK3 | HG10 | HG10 | a0.25 | 6 | -0.09836 | 0.3333 | -0.09792 | -0.002017 | 0.09445 |
| Q_RANK5 | Q_RANK3 | HG10 | HG10 | a0.5 | 6 | 0.1023 | 0.6667 | 0.1029 | -0.0005963 | 0.178 |
| Q_RANK5 | Q_RANK3 | HG15 | HG15 | a0.125 | 6 | 0.02763 | 0.6667 | 0.02836 | -0.0007166 | 0.06878 |
| Q_RANK5 | Q_RANK3 | HG15 | HG15 | a0.25 | 6 | -0.09425 | 0.3333 | -0.09424 | -0.002631 | 0.09698 |
| Q_RANK5 | Q_RANK3 | HG15 | HG15 | a0.5 | 6 | 0.2377 | 1 | 0.2369 | -0.002287 | 0.1741 |
| Q_RANK5 | Q_RANK3 | HG5 | HG5 | a0.125 | 6 | 0.04061 | 0.6667 | 0.04086 | -0.0001862 | 0.06781 |
| Q_RANK5 | Q_RANK3 | HG5 | HG5 | a0.25 | 6 | -0.06632 | 0.3333 | -0.066 | -0.0007425 | 0.09453 |
| Q_RANK5 | Q_RANK3 | HG5 | HG5 | a0.5 | 6 | -0.00621 | 0.5 | -0.008514 | 0.0007665 | 0.1655 |
| Q_RANK5 | Q_RANK3 | NATIVE | NATIVE | a0.125 | 6 | 0.02435 | 0.6667 | 0.02552 | -0.0001035 | 0.06405 |
| Q_RANK5 | Q_RANK3 | NATIVE | NATIVE | a0.25 | 6 | -0.01479 | 0.5 | -0.01441 | 0.0001488 | 0.09421 |
| Q_RANK5 | Q_RANK3 | NATIVE | NATIVE | a0.5 | 6 | -0.03148 | 0.3333 | -0.03485 | 0.0002652 | 0.1512 |


> 表头：主体=X − KERNEL_DOSE（同均值 / RMS 的 Q0 增量控制）｜算子=KERNEL_DOSE｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=H 见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=见视图｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-KDOSE


| meas | op | H | cells | median_D_ann_pp | share_pos | median_se_H_ann_pp |
|---|---|---|---|---|---|---|
| Q_D10 | HG10 | 1 | 6 | -0.2041 | 0.3333 | 0.252 |
| Q_D10 | HG10 | 5 | 6 | -0.1038 | 0.3333 | 0.1567 |
| Q_D10 | HG10 | 20 | 6 | -0.02881 | 0.3333 | 0.1105 |
| Q_D10 | NATIVE | 1 | 6 | -0.1739 | 0 | 0.2405 |
| Q_D10 | NATIVE | 5 | 6 | -0.1138 | 0 | 0.1415 |
| Q_D10 | NATIVE | 20 | 6 | -0.02217 | 0 | 0.09755 |
| Q_D3 | HG10 | 1 | 6 | -0.444 | 0 | 0.2346 |
| Q_D3 | HG10 | 5 | 6 | -0.1094 | 0.1667 | 0.1329 |
| Q_D3 | HG10 | 20 | 6 | -0.06397 | 0.1667 | 0.08419 |
| Q_D3 | NATIVE | 1 | 6 | -0.2444 | 0 | 0.2281 |
| Q_D3 | NATIVE | 5 | 6 | -0.1361 | 0 | 0.125 |
| Q_D3 | NATIVE | 20 | 6 | -0.06255 | 0 | 0.08193 |
| Q_D5 | HG10 | 1 | 6 | -0.2751 | 0 | 0.242 |
| Q_D5 | HG10 | 5 | 6 | -0.1474 | 0.1667 | 0.1458 |
| Q_D5 | HG10 | 20 | 6 | -0.074 | 0.3333 | 0.09772 |
| Q_D5 | NATIVE | 1 | 6 | -0.263 | 0 | 0.2334 |
| Q_D5 | NATIVE | 5 | 6 | -0.2068 | 0 | 0.1327 |
| Q_D5 | NATIVE | 20 | 6 | -0.07447 | 0 | 0.08845 |
| Q_DEW3 | HG10 | 1 | 6 | -0.2544 | 0 | 0.2159 |
| Q_DEW3 | HG10 | 5 | 6 | -0.07566 | 0.1667 | 0.1244 |
| Q_DEW3 | HG10 | 20 | 6 | -0.03231 | 0.3333 | 0.08226 |
| Q_DEW3 | NATIVE | 1 | 6 | -0.1852 | 0.1667 | 0.2123 |
| Q_DEW3 | NATIVE | 5 | 6 | -0.113 | 0 | 0.1157 |
| Q_DEW3 | NATIVE | 20 | 6 | -0.03128 | 0 | 0.07463 |
| Q_DEW5 | HG10 | 1 | 6 | -0.2994 | 0 | 0.2312 |
| Q_DEW5 | HG10 | 5 | 6 | -0.1443 | 0.1667 | 0.1352 |
| Q_DEW5 | HG10 | 20 | 6 | -0.03371 | 0.3333 | 0.09424 |
| Q_DEW5 | NATIVE | 1 | 6 | -0.1928 | 0 | 0.2258 |
| Q_DEW5 | NATIVE | 5 | 6 | -0.1195 | 0 | 0.1284 |
| Q_DEW5 | NATIVE | 20 | 6 | -0.02408 | 0.3333 | 0.08883 |
| Q_DMED5 | HG10 | 1 | 6 | -0.4234 | 0 | 0.2373 |
| Q_DMED5 | HG10 | 5 | 6 | -0.07965 | 0.1667 | 0.1324 |
| Q_DMED5 | HG10 | 20 | 6 | -0.04705 | 0.1667 | 0.08041 |
| Q_DMED5 | NATIVE | 1 | 6 | -0.3456 | 0 | 0.2273 |
| Q_DMED5 | NATIVE | 5 | 6 | -0.1528 | 0 | 0.1208 |
| Q_DMED5 | NATIVE | 20 | 6 | -0.06378 | 0 | 0.07382 |
| Q_QMEAN5 | HG10 | 1 | 6 | -0.3678 | 0.1667 | 0.2234 |
| Q_QMEAN5 | HG10 | 5 | 6 | -0.08488 | 0.1667 | 0.1259 |
| Q_QMEAN5 | HG10 | 20 | 6 | -0.04905 | 0.1667 | 0.07107 |
| Q_QMEAN5 | NATIVE | 1 | 6 | -0.2177 | 0.1667 | 0.2216 |
| Q_QMEAN5 | NATIVE | 5 | 6 | -0.1201 | 0 | 0.1113 |
| Q_QMEAN5 | NATIVE | 20 | 6 | -0.04454 | 0 | 0.06956 |
| Q_RANK10 | HG10 | 1 | 6 | -0.237 | 0.1667 | 0.2237 |
| Q_RANK10 | HG10 | 5 | 6 | -0.1945 | 0.3333 | 0.1315 |
| Q_RANK10 | HG10 | 20 | 6 | -0.08342 | 0.1667 | 0.07531 |
| Q_RANK10 | NATIVE | 1 | 6 | -0.263 | 0.1667 | 0.2188 |
| Q_RANK10 | NATIVE | 5 | 6 | -0.1933 | 0.1667 | 0.1214 |
| Q_RANK10 | NATIVE | 20 | 6 | -0.0457 | 0.1667 | 0.07062 |
| Q_RANK3 | HG10 | 1 | 6 | -0.2505 | 0 | 0.2063 |
| Q_RANK3 | HG10 | 5 | 6 | -0.1642 | 0 | 0.1098 |
| Q_RANK3 | HG10 | 20 | 6 | 0.0007987 | 0.5 | 0.06112 |
| Q_RANK3 | NATIVE | 1 | 6 | -0.1748 | 0 | 0.2093 |
| Q_RANK3 | NATIVE | 5 | 6 | -0.1354 | 0 | 0.1091 |
| Q_RANK3 | NATIVE | 20 | 6 | -0.05135 | 0 | 0.06271 |
| Q_RANK5 | HG10 | 1 | 6 | -0.4039 | 0 | 0.2139 |
| Q_RANK5 | HG10 | 5 | 6 | -0.1601 | 0.1667 | 0.1268 |
| Q_RANK5 | HG10 | 20 | 6 | -0.07679 | 0.1667 | 0.07535 |
| Q_RANK5 | NATIVE | 1 | 6 | -0.2011 | 0 | 0.2119 |
| Q_RANK5 | NATIVE | 5 | 6 | -0.1411 | 0 | 0.1143 |
| Q_RANK5 | NATIVE | 20 | 6 | -0.04759 | 0 | 0.06608 |
| Q_RANKOBS5 | HG10 | 1 | 6 | 0.03902 | 0.6667 | 0.1909 |
| Q_RANKOBS5 | HG10 | 5 | 6 | 0.007321 | 0.5 | 0.1057 |
| Q_RANKOBS5 | HG10 | 20 | 6 | -0.07539 | 0.3333 | 0.05515 |
| Q_RANKOBS5 | NATIVE | 1 | 6 | -0.3849 | 0 | 0.1887 |
| Q_RANKOBS5 | NATIVE | 5 | 6 | -0.1135 | 0 | 0.09572 |
| Q_RANKOBS5 | NATIVE | 20 | 6 | -0.06966 | 0 | 0.05416 |
| Q_RANKSCORE5 | HG10 | 1 | 6 | -0.2203 | 0.1667 | 0.1657 |
| Q_RANKSCORE5 | HG10 | 5 | 6 | -0.1484 | 0.1667 | 0.08953 |
| Q_RANKSCORE5 | HG10 | 20 | 6 | -0.0292 | 0 | 0.05355 |
| Q_RANKSCORE5 | NATIVE | 1 | 6 | 0.05902 | 0.5 | 0.1668 |
| Q_RANKSCORE5 | NATIVE | 5 | 6 | -0.0649 | 0.1667 | 0.08439 |
| Q_RANKSCORE5 | NATIVE | 20 | 6 | -0.07044 | 0 | 0.04314 |


> 表头：主体=支持桥：共同支持上 X − Q0（内容）｜算子=SUPPORT_BRIDGE_CONTENT｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=H 见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=见视图｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-CS-CONTENT


| meas | op | H | cells | median_D_ann_pp | share_pos | median_se_H_ann_pp |
|---|---|---|---|---|---|---|
| Q_D10 | HG10 | 1 | 6 | -0.3617 | 0.3333 | 0.2582 |
| Q_D10 | HG10 | 5 | 6 | -0.1512 | 0.3333 | 0.158 |
| Q_D10 | HG10 | 20 | 6 | -0.07203 | 0 | 0.1065 |
| Q_D10 | NATIVE | 1 | 6 | -0.284 | 0 | 0.2545 |
| Q_D10 | NATIVE | 5 | 6 | -0.1469 | 0 | 0.1465 |
| Q_D10 | NATIVE | 20 | 6 | -0.05049 | 0 | 0.09996 |
| Q_D3 | HG10 | 1 | 6 | -0.4262 | 0 | 0.2418 |
| Q_D3 | HG10 | 5 | 6 | -0.06337 | 0.1667 | 0.1344 |
| Q_D3 | HG10 | 20 | 6 | -0.07769 | 0 | 0.08367 |
| Q_D3 | NATIVE | 1 | 6 | -0.2966 | 0 | 0.2346 |
| Q_D3 | NATIVE | 5 | 6 | -0.1622 | 0 | 0.129 |
| Q_D3 | NATIVE | 20 | 6 | -0.0871 | 0 | 0.07395 |
| Q_D5 | HG10 | 1 | 6 | -0.3086 | 0 | 0.2521 |
| Q_D5 | HG10 | 5 | 6 | -0.09644 | 0 | 0.1467 |
| Q_D5 | HG10 | 20 | 6 | -0.09744 | 0 | 0.09768 |
| Q_D5 | NATIVE | 1 | 6 | -0.3114 | 0 | 0.2438 |
| Q_D5 | NATIVE | 5 | 6 | -0.2067 | 0 | 0.136 |
| Q_D5 | NATIVE | 20 | 6 | -0.07844 | 0 | 0.08725 |
| Q_DEW3 | HG10 | 1 | 6 | -0.2776 | 0 | 0.216 |
| Q_DEW3 | HG10 | 5 | 6 | -0.09247 | 0.1667 | 0.1241 |
| Q_DEW3 | HG10 | 20 | 6 | -0.04948 | 0 | 0.0804 |
| Q_DEW3 | NATIVE | 1 | 6 | -0.1485 | 0 | 0.2131 |
| Q_DEW3 | NATIVE | 5 | 6 | -0.1462 | 0 | 0.1141 |
| Q_DEW3 | NATIVE | 20 | 6 | -0.04595 | 0 | 0.06963 |
| Q_DEW5 | HG10 | 1 | 6 | -0.3178 | 0 | 0.2364 |
| Q_DEW5 | HG10 | 5 | 6 | -0.1456 | 0 | 0.1364 |
| Q_DEW5 | HG10 | 20 | 6 | -0.05433 | 0 | 0.09128 |
| Q_DEW5 | NATIVE | 1 | 6 | -0.259 | 0 | 0.2319 |
| Q_DEW5 | NATIVE | 5 | 6 | -0.1726 | 0 | 0.1293 |
| Q_DEW5 | NATIVE | 20 | 6 | -0.05158 | 0.1667 | 0.08433 |
| Q_DMED5 | HG10 | 1 | 6 | -0.3928 | 0 | 0.2482 |
| Q_DMED5 | HG10 | 5 | 6 | -0.08559 | 0.1667 | 0.1359 |
| Q_DMED5 | HG10 | 20 | 6 | -0.1155 | 0.1667 | 0.0786 |
| Q_DMED5 | NATIVE | 1 | 6 | -0.404 | 0 | 0.2373 |
| Q_DMED5 | NATIVE | 5 | 6 | -0.1905 | 0 | 0.1298 |
| Q_DMED5 | NATIVE | 20 | 6 | -0.08796 | 0 | 0.07427 |
| Q_QMEAN5 | HG10 | 1 | 6 | -0.3823 | 0.1667 | 0.2378 |
| Q_QMEAN5 | HG10 | 5 | 6 | -0.06259 | 0.3333 | 0.129 |
| Q_QMEAN5 | HG10 | 20 | 6 | -0.1072 | 0.1667 | 0.07619 |
| Q_QMEAN5 | NATIVE | 1 | 6 | -0.3218 | 0 | 0.2317 |
| Q_QMEAN5 | NATIVE | 5 | 6 | -0.08998 | 0.1667 | 0.1192 |
| Q_QMEAN5 | NATIVE | 20 | 6 | -0.04132 | 0 | 0.07178 |
| Q_RANK10 | HG10 | 1 | 6 | -0.3767 | 0.1667 | 0.2314 |
| Q_RANK10 | HG10 | 5 | 6 | -0.2009 | 0.3333 | 0.1327 |
| Q_RANK10 | HG10 | 20 | 6 | -0.1334 | 0.3333 | 0.07492 |
| Q_RANK10 | NATIVE | 1 | 6 | -0.4322 | 0.1667 | 0.2267 |
| Q_RANK10 | NATIVE | 5 | 6 | -0.195 | 0.1667 | 0.1244 |
| Q_RANK10 | NATIVE | 20 | 6 | -0.08051 | 0.1667 | 0.07014 |
| Q_RANK3 | HG10 | 1 | 6 | -0.2617 | 0 | 0.2161 |
| Q_RANK3 | HG10 | 5 | 6 | -0.1106 | 0.1667 | 0.1061 |
| Q_RANK3 | HG10 | 20 | 6 | -0.05395 | 0 | 0.06171 |
| Q_RANK3 | NATIVE | 1 | 6 | -0.2642 | 0 | 0.2087 |
| Q_RANK3 | NATIVE | 5 | 6 | -0.1351 | 0.1667 | 0.1074 |
| Q_RANK3 | NATIVE | 20 | 6 | -0.06972 | 0 | 0.06085 |
| Q_RANK5 | HG10 | 1 | 6 | -0.4751 | 0 | 0.2212 |
| Q_RANK5 | HG10 | 5 | 6 | -0.1303 | 0.3333 | 0.1217 |
| Q_RANK5 | HG10 | 20 | 6 | -0.09416 | 0 | 0.07508 |
| Q_RANK5 | NATIVE | 1 | 6 | -0.3105 | 0 | 0.2148 |
| Q_RANK5 | NATIVE | 5 | 6 | -0.1623 | 0.1667 | 0.1119 |
| Q_RANK5 | NATIVE | 20 | 6 | -0.04903 | 0.1667 | 0.06748 |
| Q_RANKOBS5 | HG10 | 1 | 6 | -0.2143 | 0 | 0.1994 |
| Q_RANKOBS5 | HG10 | 5 | 6 | -0.007131 | 0.5 | 0.1123 |
| Q_RANKOBS5 | HG10 | 20 | 6 | -0.09639 | 0.3333 | 0.05685 |
| Q_RANKOBS5 | NATIVE | 1 | 6 | -0.3994 | 0 | 0.1925 |
| Q_RANKOBS5 | NATIVE | 5 | 6 | -0.1729 | 0 | 0.1026 |
| Q_RANKOBS5 | NATIVE | 20 | 6 | -0.0868 | 0 | 0.05293 |
| Q_RANKSCORE5 | HG10 | 1 | 6 | -0.5709 | 0 | 0.2136 |
| Q_RANKSCORE5 | HG10 | 5 | 6 | -0.2371 | 0.1667 | 0.1136 |
| Q_RANKSCORE5 | HG10 | 20 | 6 | -0.09107 | 0 | 0.06517 |
| Q_RANKSCORE5 | NATIVE | 1 | 6 | -0.4087 | 0 | 0.2139 |
| Q_RANKSCORE5 | NATIVE | 5 | 6 | -0.203 | 0.1667 | 0.1023 |
| Q_RANKSCORE5 | NATIVE | 20 | 6 | -0.1014 | 0 | 0.05624 |


> 表头：主体=支持桥：Q0 共同支持 − Q0 原生（Q0 支持变化）｜算子=SUPPORT_BRIDGE_PARENT_SUPPORT｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=H 见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=见视图｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-CS-PSUP


| meas | op | H | cells | median_D_ann_pp | share_pos | median_se_H_ann_pp |
|---|---|---|---|---|---|---|
| Q_D10 | HG10 | 1 | 6 | 0.0205 | 0.8333 | 0.02862 |
| Q_D10 | HG10 | 5 | 6 | 0.01547 | 1 | 0.01441 |
| Q_D10 | HG10 | 20 | 6 | 0.003978 | 0.8333 | 0.007258 |
| Q_D10 | NATIVE | 1 | 6 | 0.01313 | 0.6667 | 0.02035 |
| Q_D10 | NATIVE | 5 | 6 | -0.0007947 | 0.5 | 0.01138 |
| Q_D10 | NATIVE | 20 | 6 | -0.0007002 | 0.5 | 0.005559 |
| Q_D3 | HG10 | 1 | 6 | 0.002873 | 0.5 | 0.009038 |
| Q_D3 | HG10 | 5 | 6 | -0.001859 | 0.3333 | 0.005263 |
| Q_D3 | HG10 | 20 | 6 | 0.002449 | 0.6667 | 0.00441 |
| Q_D3 | NATIVE | 1 | 6 | -0.004935 | 0.3333 | 0.009373 |
| Q_D3 | NATIVE | 5 | 6 | -0.001172 | 0.3333 | 0.004817 |
| Q_D3 | NATIVE | 20 | 6 | -0.002158 | 0.3333 | 0.003002 |
| Q_D5 | HG10 | 1 | 6 | 0.009966 | 0.6667 | 0.01835 |
| Q_D5 | HG10 | 5 | 6 | 0.008352 | 0.6667 | 0.007126 |
| Q_D5 | HG10 | 20 | 6 | -0.0008121 | 0.3333 | 0.003504 |
| Q_D5 | NATIVE | 1 | 6 | -0.004268 | 0.1667 | 0.01044 |
| Q_D5 | NATIVE | 5 | 6 | -0.004525 | 0.1667 | 0.008219 |
| Q_D5 | NATIVE | 20 | 6 | -0.004966 | 0 | 0.004576 |
| Q_DEW3 | HG10 | 1 | 6 | 0.002873 | 0.5 | 0.009038 |
| Q_DEW3 | HG10 | 5 | 6 | -0.001859 | 0.3333 | 0.005263 |
| Q_DEW3 | HG10 | 20 | 6 | 0.002449 | 0.6667 | 0.00441 |
| Q_DEW3 | NATIVE | 1 | 6 | -0.004935 | 0.3333 | 0.009373 |
| Q_DEW3 | NATIVE | 5 | 6 | -0.001172 | 0.3333 | 0.004817 |
| Q_DEW3 | NATIVE | 20 | 6 | -0.002158 | 0.3333 | 0.003002 |
| Q_DEW5 | HG10 | 1 | 6 | 0.009966 | 0.6667 | 0.01835 |
| Q_DEW5 | HG10 | 5 | 6 | 0.008352 | 0.6667 | 0.007126 |
| Q_DEW5 | HG10 | 20 | 6 | -0.0008121 | 0.3333 | 0.003504 |
| Q_DEW5 | NATIVE | 1 | 6 | -0.004268 | 0.1667 | 0.01044 |
| Q_DEW5 | NATIVE | 5 | 6 | -0.004525 | 0.1667 | 0.008219 |
| Q_DEW5 | NATIVE | 20 | 6 | -0.004966 | 0 | 0.004576 |
| Q_DMED5 | HG10 | 1 | 6 | 0.009966 | 0.6667 | 0.01835 |
| Q_DMED5 | HG10 | 5 | 6 | 0.008352 | 0.6667 | 0.007126 |
| Q_DMED5 | HG10 | 20 | 6 | -0.0008121 | 0.3333 | 0.003504 |
| Q_DMED5 | NATIVE | 1 | 6 | -0.004268 | 0.1667 | 0.01044 |
| Q_DMED5 | NATIVE | 5 | 6 | -0.004525 | 0.1667 | 0.008219 |
| Q_DMED5 | NATIVE | 20 | 6 | -0.004966 | 0 | 0.004576 |
| Q_QMEAN5 | HG10 | 1 | 6 | 0.009966 | 0.6667 | 0.01835 |
| Q_QMEAN5 | HG10 | 5 | 6 | 0.008352 | 0.6667 | 0.007126 |
| Q_QMEAN5 | HG10 | 20 | 6 | -0.0008121 | 0.3333 | 0.003504 |
| Q_QMEAN5 | NATIVE | 1 | 6 | -0.004268 | 0.1667 | 0.01044 |
| Q_QMEAN5 | NATIVE | 5 | 6 | -0.004525 | 0.1667 | 0.008219 |
| Q_QMEAN5 | NATIVE | 20 | 6 | -0.004966 | 0 | 0.004576 |
| Q_RANK10 | HG10 | 1 | 6 | 0.02958 | 0.8333 | 0.03892 |
| Q_RANK10 | HG10 | 5 | 6 | 0.008474 | 1 | 0.01906 |
| Q_RANK10 | HG10 | 20 | 6 | 0.001399 | 0.5 | 0.009347 |
| Q_RANK10 | NATIVE | 1 | 6 | 0.002508 | 0.5 | 0.02457 |
| Q_RANK10 | NATIVE | 5 | 6 | 0.001393 | 0.5 | 0.01423 |
| Q_RANK10 | NATIVE | 20 | 6 | -0.000492 | 0.5 | 0.008082 |
| Q_RANK3 | HG10 | 1 | 6 | 0.002215 | 0.5 | 0.009066 |
| Q_RANK3 | HG10 | 5 | 6 | -0.00376 | 0.3333 | 0.005352 |
| Q_RANK3 | HG10 | 20 | 6 | 0.002741 | 0.6667 | 0.00449 |
| Q_RANK3 | NATIVE | 1 | 6 | -0.006172 | 0.3333 | 0.009495 |
| Q_RANK3 | NATIVE | 5 | 6 | -0.001096 | 0.3333 | 0.005138 |
| Q_RANK3 | NATIVE | 20 | 6 | -0.002096 | 0.3333 | 0.003041 |
| Q_RANK5 | HG10 | 1 | 6 | 0.01034 | 0.6667 | 0.02003 |
| Q_RANK5 | HG10 | 5 | 6 | 0.001182 | 0.6667 | 0.008449 |
| Q_RANK5 | HG10 | 20 | 6 | -0.0009963 | 0.3333 | 0.003842 |
| Q_RANK5 | NATIVE | 1 | 6 | -0.007437 | 0.1667 | 0.01127 |
| Q_RANK5 | NATIVE | 5 | 6 | -0.004454 | 0 | 0.00892 |
| Q_RANK5 | NATIVE | 20 | 6 | -0.004375 | 0 | 0.00525 |
| Q_RANKOBS5 | HG10 | 1 | 6 | -0.2302 | 0 | 0.1793 |
| Q_RANKOBS5 | HG10 | 5 | 6 | -0.152 | 0 | 0.09366 |
| Q_RANKOBS5 | HG10 | 20 | 6 | -0.05638 | 0 | 0.05093 |
| Q_RANKOBS5 | NATIVE | 1 | 6 | -0.2467 | 0 | 0.1729 |
| Q_RANKOBS5 | NATIVE | 5 | 6 | -0.05322 | 0.3333 | 0.08539 |
| Q_RANKOBS5 | NATIVE | 20 | 6 | -0.03212 | 0 | 0.04479 |
| Q_RANKSCORE5 | HG10 | 1 | 6 | 0.01034 | 0.6667 | 0.02003 |
| Q_RANKSCORE5 | HG10 | 5 | 6 | 0.001182 | 0.6667 | 0.008449 |
| Q_RANKSCORE5 | HG10 | 20 | 6 | -0.0009963 | 0.3333 | 0.003842 |
| Q_RANKSCORE5 | NATIVE | 1 | 6 | -0.007437 | 0.1667 | 0.01127 |
| Q_RANKSCORE5 | NATIVE | 5 | 6 | -0.004454 | 0 | 0.00892 |
| Q_RANKSCORE5 | NATIVE | 20 | 6 | -0.004375 | 0 | 0.00525 |


> 表头：主体=支持桥：X 原生 − X 共同支持（X 支持变化）｜算子=SUPPORT_BRIDGE_CHILD_SUPPORT｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=H 见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=见视图｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-CS-CSUP


| meas | op | H | cells | median_D_ann_pp | share_pos | median_se_H_ann_pp |
|---|---|---|---|---|---|---|
| Q_D10 | HG10 | 1 | 6 | 0 | 0 | 0 |
| Q_D10 | HG10 | 5 | 6 | 0 | 0 | 0 |
| Q_D10 | HG10 | 20 | 6 | 0 | 0 | 0 |
| Q_D10 | NATIVE | 1 | 6 | 0 | 0 | 0 |
| Q_D10 | NATIVE | 5 | 6 | 0 | 0 | 0 |
| Q_D10 | NATIVE | 20 | 6 | 0 | 0 | 0 |
| Q_D3 | HG10 | 1 | 6 | 0 | 0 | 0 |
| Q_D3 | HG10 | 5 | 6 | 0 | 0 | 0 |
| Q_D3 | HG10 | 20 | 6 | 0 | 0 | 0 |
| Q_D3 | NATIVE | 1 | 6 | 0 | 0 | 0 |
| Q_D3 | NATIVE | 5 | 6 | 0 | 0 | 0 |
| Q_D3 | NATIVE | 20 | 6 | 0 | 0 | 0 |
| Q_D5 | HG10 | 1 | 6 | 0 | 0 | 0 |
| Q_D5 | HG10 | 5 | 6 | 0 | 0 | 0 |
| Q_D5 | HG10 | 20 | 6 | 0 | 0 | 0 |
| Q_D5 | NATIVE | 1 | 6 | 0 | 0 | 0 |
| Q_D5 | NATIVE | 5 | 6 | 0 | 0 | 0 |
| Q_D5 | NATIVE | 20 | 6 | 0 | 0 | 0 |
| Q_DEW3 | HG10 | 1 | 6 | 0 | 0 | 0 |
| Q_DEW3 | HG10 | 5 | 6 | 0 | 0 | 0 |
| Q_DEW3 | HG10 | 20 | 6 | 0 | 0 | 0 |
| Q_DEW3 | NATIVE | 1 | 6 | 0 | 0 | 0 |
| Q_DEW3 | NATIVE | 5 | 6 | 0 | 0 | 0 |
| Q_DEW3 | NATIVE | 20 | 6 | 0 | 0 | 0 |
| Q_DEW5 | HG10 | 1 | 6 | 0 | 0 | 0 |
| Q_DEW5 | HG10 | 5 | 6 | 0 | 0 | 0 |
| Q_DEW5 | HG10 | 20 | 6 | 0 | 0 | 0 |
| Q_DEW5 | NATIVE | 1 | 6 | 0 | 0 | 0 |
| Q_DEW5 | NATIVE | 5 | 6 | 0 | 0 | 0 |
| Q_DEW5 | NATIVE | 20 | 6 | 0 | 0 | 0 |
| Q_DMED5 | HG10 | 1 | 6 | 0 | 0 | 0 |
| Q_DMED5 | HG10 | 5 | 6 | 0 | 0 | 0 |
| Q_DMED5 | HG10 | 20 | 6 | 0 | 0 | 0 |
| Q_DMED5 | NATIVE | 1 | 6 | 0 | 0 | 0 |
| Q_DMED5 | NATIVE | 5 | 6 | 0 | 0 | 0 |
| Q_DMED5 | NATIVE | 20 | 6 | 0 | 0 | 0 |
| Q_QMEAN5 | HG10 | 1 | 6 | 0 | 0 | 0 |
| Q_QMEAN5 | HG10 | 5 | 6 | 0 | 0 | 0 |
| Q_QMEAN5 | HG10 | 20 | 6 | 0 | 0 | 0 |
| Q_QMEAN5 | NATIVE | 1 | 6 | 0 | 0 | 0 |
| Q_QMEAN5 | NATIVE | 5 | 6 | 0 | 0 | 0 |
| Q_QMEAN5 | NATIVE | 20 | 6 | 0 | 0 | 0 |
| Q_RANK10 | HG10 | 1 | 6 | 0 | 0 | 0 |
| Q_RANK10 | HG10 | 5 | 6 | 0 | 0 | 0 |
| Q_RANK10 | HG10 | 20 | 6 | 0 | 0 | 0 |
| Q_RANK10 | NATIVE | 1 | 6 | 0 | 0 | 0 |
| Q_RANK10 | NATIVE | 5 | 6 | 0 | 0 | 0 |
| Q_RANK10 | NATIVE | 20 | 6 | 0 | 0 | 0 |
| Q_RANK3 | HG10 | 1 | 6 | 0 | 0 | 0 |
| Q_RANK3 | HG10 | 5 | 6 | 0 | 0 | 0 |
| Q_RANK3 | HG10 | 20 | 6 | 0 | 0 | 0 |
| Q_RANK3 | NATIVE | 1 | 6 | 0 | 0 | 0 |
| Q_RANK3 | NATIVE | 5 | 6 | 0 | 0 | 0 |
| Q_RANK3 | NATIVE | 20 | 6 | 0 | 0 | 0 |
| Q_RANK5 | HG10 | 1 | 6 | 0 | 0 | 0 |
| Q_RANK5 | HG10 | 5 | 6 | 0 | 0 | 0 |
| Q_RANK5 | HG10 | 20 | 6 | 0 | 0 | 0 |
| Q_RANK5 | NATIVE | 1 | 6 | 0 | 0 | 0 |
| Q_RANK5 | NATIVE | 5 | 6 | 0 | 0 | 0 |
| Q_RANK5 | NATIVE | 20 | 6 | 0 | 0 | 0 |
| Q_RANKOBS5 | HG10 | 1 | 6 | 0 | 0 | 0 |
| Q_RANKOBS5 | HG10 | 5 | 6 | 0 | 0 | 0 |
| Q_RANKOBS5 | HG10 | 20 | 6 | 0 | 0 | 0 |
| Q_RANKOBS5 | NATIVE | 1 | 6 | 0 | 0 | 0 |
| Q_RANKOBS5 | NATIVE | 5 | 6 | 0 | 0 | 0 |
| Q_RANKOBS5 | NATIVE | 20 | 6 | 0 | 0 | 0 |
| Q_RANKSCORE5 | HG10 | 1 | 6 | 0 | 0 | 0 |
| Q_RANKSCORE5 | HG10 | 5 | 6 | 0 | 0 | 0 |
| Q_RANKSCORE5 | HG10 | 20 | 6 | 0 | 0 | 0 |
| Q_RANKSCORE5 | NATIVE | 1 | 6 | 0 | 0 | 0 |
| Q_RANKSCORE5 | NATIVE | 5 | 6 | 0 | 0 | 0 |
| Q_RANKSCORE5 | NATIVE | 20 | 6 | 0 | 0 | 0 |


> 表头：主体=Q0 遮罩到 X 支持 − Q0（只改支持）｜算子=MASKQ0_SUPPORT_ONLY｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=H 见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=见视图｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-MQ0-SUP


| meas | op | H | cells | median_D_ann_pp | share_pos | median_se_H_ann_pp |
|---|---|---|---|---|---|---|
| Q_D10 | HG10 | 1 | 6 | 0.009933 | 0.8333 | 0.02523 |
| Q_D10 | HG10 | 5 | 6 | 0.008127 | 0.6667 | 0.01068 |
| Q_D10 | HG10 | 20 | 6 | 0.001722 | 1 | 0.005286 |
| Q_D10 | NATIVE | 1 | 6 | 0.0008479 | 0.5 | 0.01482 |
| Q_D10 | NATIVE | 5 | 6 | -0.001956 | 0.1667 | 0.008074 |
| Q_D10 | NATIVE | 20 | 6 | -0.001551 | 0 | 0.003677 |
| Q_D3 | HG10 | 1 | 6 | -0.004488 | 0.3333 | 0.005101 |
| Q_D3 | HG10 | 5 | 6 | -0.0009003 | 0.3333 | 0.002567 |
| Q_D3 | HG10 | 20 | 6 | -0.0003251 | 0.3333 | 0.0009908 |
| Q_D3 | NATIVE | 1 | 6 | -0.006526 | 0 | 0.009341 |
| Q_D3 | NATIVE | 5 | 6 | -0.004103 | 0 | 0.003324 |
| Q_D3 | NATIVE | 20 | 6 | -0.0006154 | 0.3333 | 0.0009135 |
| Q_D5 | HG10 | 1 | 6 | -0.004215 | 0.3333 | 0.005653 |
| Q_D5 | HG10 | 5 | 6 | 0.000858 | 0.8333 | 0.003754 |
| Q_D5 | HG10 | 20 | 6 | -0.001305 | 0.3333 | 0.002255 |
| Q_D5 | NATIVE | 1 | 6 | 0.002126 | 0.8333 | 0.005654 |
| Q_D5 | NATIVE | 5 | 6 | -0.006926 | 0 | 0.005829 |
| Q_D5 | NATIVE | 20 | 6 | -0.004694 | 0 | 0.002778 |
| Q_DEW3 | HG10 | 1 | 6 | -0.004488 | 0.3333 | 0.005101 |
| Q_DEW3 | HG10 | 5 | 6 | -0.0009003 | 0.3333 | 0.002567 |
| Q_DEW3 | HG10 | 20 | 6 | -0.0003251 | 0.3333 | 0.0009908 |
| Q_DEW3 | NATIVE | 1 | 6 | -0.006526 | 0 | 0.009341 |
| Q_DEW3 | NATIVE | 5 | 6 | -0.004103 | 0 | 0.003324 |
| Q_DEW3 | NATIVE | 20 | 6 | -0.0006154 | 0.3333 | 0.0009135 |
| Q_DEW5 | HG10 | 1 | 6 | -0.004215 | 0.3333 | 0.005653 |
| Q_DEW5 | HG10 | 5 | 6 | 0.000858 | 0.8333 | 0.003754 |
| Q_DEW5 | HG10 | 20 | 6 | -0.001305 | 0.3333 | 0.002255 |
| Q_DEW5 | NATIVE | 1 | 6 | 0.002126 | 0.8333 | 0.005654 |
| Q_DEW5 | NATIVE | 5 | 6 | -0.006926 | 0 | 0.005829 |
| Q_DEW5 | NATIVE | 20 | 6 | -0.004694 | 0 | 0.002778 |
| Q_DMED5 | HG10 | 1 | 6 | -0.004215 | 0.3333 | 0.005653 |
| Q_DMED5 | HG10 | 5 | 6 | 0.000858 | 0.8333 | 0.003754 |
| Q_DMED5 | HG10 | 20 | 6 | -0.001305 | 0.3333 | 0.002255 |
| Q_DMED5 | NATIVE | 1 | 6 | 0.002126 | 0.8333 | 0.005654 |
| Q_DMED5 | NATIVE | 5 | 6 | -0.006926 | 0 | 0.005829 |
| Q_DMED5 | NATIVE | 20 | 6 | -0.004694 | 0 | 0.002778 |
| Q_QMEAN5 | HG10 | 1 | 6 | -0.004215 | 0.3333 | 0.005653 |
| Q_QMEAN5 | HG10 | 5 | 6 | 0.000858 | 0.8333 | 0.003754 |
| Q_QMEAN5 | HG10 | 20 | 6 | -0.001305 | 0.3333 | 0.002255 |
| Q_QMEAN5 | NATIVE | 1 | 6 | 0.002126 | 0.8333 | 0.005654 |
| Q_QMEAN5 | NATIVE | 5 | 6 | -0.006926 | 0 | 0.005829 |
| Q_QMEAN5 | NATIVE | 20 | 6 | -0.004694 | 0 | 0.002778 |
| Q_RANK10 | HG10 | 1 | 6 | 0.01146 | 0.6667 | 0.0306 |
| Q_RANK10 | HG10 | 5 | 6 | 0.009762 | 1 | 0.01196 |
| Q_RANK10 | HG10 | 20 | 6 | 0.00131 | 0.6667 | 0.006719 |
| Q_RANK10 | NATIVE | 1 | 6 | -0.004215 | 0.3333 | 0.01792 |
| Q_RANK10 | NATIVE | 5 | 6 | -0.004487 | 0.1667 | 0.009549 |
| Q_RANK10 | NATIVE | 20 | 6 | -0.002019 | 0.3333 | 0.004954 |
| Q_RANK3 | HG10 | 1 | 6 | -0.004488 | 0.3333 | 0.005101 |
| Q_RANK3 | HG10 | 5 | 6 | -0.0009003 | 0.3333 | 0.002567 |
| Q_RANK3 | HG10 | 20 | 6 | -0.0003251 | 0.3333 | 0.0009908 |
| Q_RANK3 | NATIVE | 1 | 6 | -0.005346 | 0 | 0.009341 |
| Q_RANK3 | NATIVE | 5 | 6 | -0.00383 | 0.1667 | 0.003374 |
| Q_RANK3 | NATIVE | 20 | 6 | -0.0002209 | 0.5 | 0.00094 |
| Q_RANK5 | HG10 | 1 | 6 | -0.006639 | 0.3333 | 0.00831 |
| Q_RANK5 | HG10 | 5 | 6 | -0.002997 | 0 | 0.004245 |
| Q_RANK5 | HG10 | 20 | 6 | -0.002215 | 0.3333 | 0.002402 |
| Q_RANK5 | NATIVE | 1 | 6 | 0.002776 | 0.6667 | 0.007102 |
| Q_RANK5 | NATIVE | 5 | 6 | -0.00521 | 0 | 0.006336 |
| Q_RANK5 | NATIVE | 20 | 6 | -0.0015 | 0 | 0.004186 |
| Q_RANKOBS5 | HG10 | 1 | 6 | -0.3246 | 0 | 0.165 |
| Q_RANKOBS5 | HG10 | 5 | 6 | -0.186 | 0 | 0.08207 |
| Q_RANKOBS5 | HG10 | 20 | 6 | -0.03498 | 0 | 0.04459 |
| Q_RANKOBS5 | NATIVE | 1 | 6 | -0.1664 | 0 | 0.1526 |
| Q_RANKOBS5 | NATIVE | 5 | 6 | -0.1407 | 0 | 0.07269 |
| Q_RANKOBS5 | NATIVE | 20 | 6 | -0.01427 | 0 | 0.04004 |
| Q_RANKSCORE5 | HG10 | 1 | 6 | -0.006639 | 0.3333 | 0.00831 |
| Q_RANKSCORE5 | HG10 | 5 | 6 | -0.002997 | 0 | 0.004245 |
| Q_RANKSCORE5 | HG10 | 20 | 6 | -0.002215 | 0.3333 | 0.002402 |
| Q_RANKSCORE5 | NATIVE | 1 | 6 | 0.002776 | 0.6667 | 0.007102 |
| Q_RANKSCORE5 | NATIVE | 5 | 6 | -0.00521 | 0 | 0.006336 |
| Q_RANKSCORE5 | NATIVE | 20 | 6 | -0.0015 | 0 | 0.004186 |


> 表头：主体=X − Q0 遮罩（同支持的内容差）｜算子=MASKQ0_CONTENT｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=H 见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=见视图｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-MQ0-CONTENT


| meas | op | H | cells | median_D_ann_pp | share_pos | median_se_H_ann_pp |
|---|---|---|---|---|---|---|
| Q_D10 | HG10 | 1 | 6 | -0.3575 | 0.3333 | 0.2582 |
| Q_D10 | HG10 | 5 | 6 | -0.136 | 0.3333 | 0.1575 |
| Q_D10 | HG10 | 20 | 6 | -0.07081 | 0 | 0.1059 |
| Q_D10 | NATIVE | 1 | 6 | -0.2761 | 0 | 0.2548 |
| Q_D10 | NATIVE | 5 | 6 | -0.1452 | 0 | 0.1461 |
| Q_D10 | NATIVE | 20 | 6 | -0.04722 | 0 | 0.0995 |
| Q_D3 | HG10 | 1 | 6 | -0.4191 | 0 | 0.2416 |
| Q_D3 | HG10 | 5 | 6 | -0.06257 | 0.1667 | 0.1342 |
| Q_D3 | HG10 | 20 | 6 | -0.07532 | 0 | 0.08333 |
| Q_D3 | NATIVE | 1 | 6 | -0.298 | 0 | 0.2344 |
| Q_D3 | NATIVE | 5 | 6 | -0.159 | 0 | 0.1288 |
| Q_D3 | NATIVE | 20 | 6 | -0.08864 | 0 | 0.07366 |
| Q_D5 | HG10 | 1 | 6 | -0.2796 | 0 | 0.2522 |
| Q_D5 | HG10 | 5 | 6 | -0.08921 | 0 | 0.1467 |
| Q_D5 | HG10 | 20 | 6 | -0.09578 | 0 | 0.09752 |
| Q_D5 | NATIVE | 1 | 6 | -0.3179 | 0 | 0.244 |
| Q_D5 | NATIVE | 5 | 6 | -0.2075 | 0 | 0.1358 |
| Q_D5 | NATIVE | 20 | 6 | -0.08002 | 0 | 0.08712 |
| Q_DEW3 | HG10 | 1 | 6 | -0.2705 | 0 | 0.2157 |
| Q_DEW3 | HG10 | 5 | 6 | -0.09167 | 0.1667 | 0.124 |
| Q_DEW3 | HG10 | 20 | 6 | -0.04739 | 0 | 0.07984 |
| Q_DEW3 | NATIVE | 1 | 6 | -0.1387 | 0 | 0.2128 |
| Q_DEW3 | NATIVE | 5 | 6 | -0.1426 | 0 | 0.1137 |
| Q_DEW3 | NATIVE | 20 | 6 | -0.0467 | 0 | 0.06941 |
| Q_DEW5 | HG10 | 1 | 6 | -0.3015 | 0 | 0.2361 |
| Q_DEW5 | HG10 | 5 | 6 | -0.1384 | 0 | 0.1366 |
| Q_DEW5 | HG10 | 20 | 6 | -0.05358 | 0 | 0.09134 |
| Q_DEW5 | NATIVE | 1 | 6 | -0.2615 | 0 | 0.2321 |
| Q_DEW5 | NATIVE | 5 | 6 | -0.1719 | 0 | 0.1292 |
| Q_DEW5 | NATIVE | 20 | 6 | -0.05228 | 0.1667 | 0.08406 |
| Q_DMED5 | HG10 | 1 | 6 | -0.3638 | 0 | 0.2482 |
| Q_DMED5 | HG10 | 5 | 6 | -0.07759 | 0.1667 | 0.1359 |
| Q_DMED5 | HG10 | 20 | 6 | -0.1148 | 0.1667 | 0.07831 |
| Q_DMED5 | NATIVE | 1 | 6 | -0.4073 | 0 | 0.2373 |
| Q_DMED5 | NATIVE | 5 | 6 | -0.1896 | 0 | 0.1298 |
| Q_DMED5 | NATIVE | 20 | 6 | -0.08966 | 0 | 0.07391 |
| Q_QMEAN5 | HG10 | 1 | 6 | -0.3533 | 0.1667 | 0.2373 |
| Q_QMEAN5 | HG10 | 5 | 6 | -0.05459 | 0.3333 | 0.1286 |
| Q_QMEAN5 | HG10 | 20 | 6 | -0.1065 | 0.3333 | 0.07598 |
| Q_QMEAN5 | NATIVE | 1 | 6 | -0.3314 | 0 | 0.2319 |
| Q_QMEAN5 | NATIVE | 5 | 6 | -0.08625 | 0.1667 | 0.1189 |
| Q_QMEAN5 | NATIVE | 20 | 6 | -0.0413 | 0 | 0.07132 |
| Q_RANK10 | HG10 | 1 | 6 | -0.3669 | 0.1667 | 0.2331 |
| Q_RANK10 | HG10 | 5 | 6 | -0.1978 | 0.3333 | 0.1325 |
| Q_RANK10 | HG10 | 20 | 6 | -0.1296 | 0.3333 | 0.07454 |
| Q_RANK10 | NATIVE | 1 | 6 | -0.4272 | 0.1667 | 0.2262 |
| Q_RANK10 | NATIVE | 5 | 6 | -0.1953 | 0.1667 | 0.1246 |
| Q_RANK10 | NATIVE | 20 | 6 | -0.07739 | 0.1667 | 0.06962 |
| Q_RANK3 | HG10 | 1 | 6 | -0.2498 | 0 | 0.216 |
| Q_RANK3 | HG10 | 5 | 6 | -0.1139 | 0.1667 | 0.106 |
| Q_RANK3 | HG10 | 20 | 6 | -0.05435 | 0 | 0.06177 |
| Q_RANK3 | NATIVE | 1 | 6 | -0.2593 | 0 | 0.2085 |
| Q_RANK3 | NATIVE | 5 | 6 | -0.1356 | 0.1667 | 0.1072 |
| Q_RANK3 | NATIVE | 20 | 6 | -0.07228 | 0 | 0.06113 |
| Q_RANK5 | HG10 | 1 | 6 | -0.4462 | 0 | 0.2211 |
| Q_RANK5 | HG10 | 5 | 6 | -0.125 | 0.3333 | 0.1217 |
| Q_RANK5 | HG10 | 20 | 6 | -0.09294 | 0 | 0.0744 |
| Q_RANK5 | NATIVE | 1 | 6 | -0.3209 | 0 | 0.2151 |
| Q_RANK5 | NATIVE | 5 | 6 | -0.1625 | 0.1667 | 0.1115 |
| Q_RANK5 | NATIVE | 20 | 6 | -0.05248 | 0.1667 | 0.06704 |
| Q_RANKOBS5 | HG10 | 1 | 6 | -0.1079 | 0.1667 | 0.1976 |
| Q_RANKOBS5 | HG10 | 5 | 6 | 0.02259 | 0.6667 | 0.109 |
| Q_RANKOBS5 | HG10 | 20 | 6 | -0.1178 | 0.3333 | 0.05729 |
| Q_RANKOBS5 | NATIVE | 1 | 6 | -0.412 | 0.1667 | 0.1931 |
| Q_RANKOBS5 | NATIVE | 5 | 6 | -0.09681 | 0.1667 | 0.09547 |
| Q_RANKOBS5 | NATIVE | 20 | 6 | -0.07373 | 0 | 0.05167 |
| Q_RANKSCORE5 | HG10 | 1 | 6 | -0.5375 | 0 | 0.2138 |
| Q_RANKSCORE5 | HG10 | 5 | 6 | -0.2318 | 0.1667 | 0.1137 |
| Q_RANKSCORE5 | HG10 | 20 | 6 | -0.09669 | 0 | 0.06454 |
| Q_RANKSCORE5 | NATIVE | 1 | 6 | -0.4167 | 0 | 0.214 |
| Q_RANKSCORE5 | NATIVE | 5 | 6 | -0.203 | 0.1667 | 0.1023 |
| Q_RANKSCORE5 | NATIVE | 20 | 6 | -0.1043 | 0 | 0.05622 |


> 表头：主体=INV 闭环同资本（诊断，不进正式 FULL_sc）｜算子=INV_CAP_LOOP｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=H 见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=见视图｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-INVLOOP


| meas | op | H | cells | median_D_ann_pp | share_pos | median_se_H_ann_pp |
|---|---|---|---|---|---|---|
| C1 | INV10 | 1 | 18 | 0.9258 | 1 | 0.2588 |
| C1 | INV10 | 2 | 18 | 0.3536 | 1 | 0.2027 |
| C1 | INV10 | 3 | 18 | 0.1466 | 0.7222 | 0.1689 |
| C1 | INV10 | 4 | 18 | 0.08826 | 0.6111 | 0.1469 |
| C1 | INV10 | 5 | 18 | 0.09146 | 0.5556 | 0.1322 |
| C1 | INV10 | 6 | 18 | 0.106 | 0.5556 | 0.1211 |
| C1 | INV10 | 7 | 18 | 0.1353 | 0.7222 | 0.11 |
| C1 | INV10 | 8 | 18 | 0.1618 | 0.7778 | 0.1028 |
| C1 | INV10 | 9 | 18 | 0.1763 | 0.7222 | 0.09885 |
| C1 | INV10 | 10 | 18 | 0.1648 | 0.6667 | 0.09693 |
| C1 | INV10 | 11 | 18 | 0.1718 | 0.6667 | 0.09398 |
| C1 | INV10 | 12 | 18 | 0.1576 | 0.6667 | 0.09193 |
| C1 | INV10 | 13 | 18 | 0.1347 | 0.6667 | 0.08826 |
| C1 | INV10 | 14 | 18 | 0.08464 | 0.6111 | 0.08531 |
| C1 | INV10 | 15 | 18 | 0.08124 | 0.6111 | 0.08263 |
| C1 | INV10 | 16 | 18 | 0.06084 | 0.6111 | 0.08001 |
| C1 | INV10 | 17 | 18 | 0.0547 | 0.6111 | 0.07704 |
| C1 | INV10 | 18 | 18 | 0.06279 | 0.6111 | 0.07284 |
| C1 | INV10 | 19 | 18 | 0.09161 | 0.7222 | 0.07143 |
| C1 | INV10 | 20 | 18 | 0.09449 | 0.6667 | 0.0701 |
| K0 | INV10 | 1 | 6 | 0.4858 | 1 | 0.1782 |
| K0 | INV10 | 2 | 6 | 0.1723 | 0.8333 | 0.1409 |
| K0 | INV10 | 3 | 6 | 0.0616 | 0.8333 | 0.1198 |
| K0 | INV10 | 4 | 6 | 0.009459 | 0.5 | 0.1063 |
| K0 | INV10 | 5 | 6 | -0.02647 | 0.5 | 0.09615 |
| K0 | INV10 | 6 | 6 | -0.005727 | 0.5 | 0.08736 |
| K0 | INV10 | 7 | 6 | 0.01474 | 0.5 | 0.0797 |
| K0 | INV10 | 8 | 6 | 0.01324 | 0.5 | 0.07525 |
| K0 | INV10 | 9 | 6 | 0.02345 | 0.6667 | 0.07005 |
| K0 | INV10 | 10 | 6 | 0.02387 | 0.6667 | 0.0661 |
| K0 | INV10 | 11 | 6 | 0.03587 | 0.6667 | 0.0614 |
| K0 | INV10 | 12 | 6 | 0.03151 | 0.6667 | 0.05798 |
| K0 | INV10 | 13 | 6 | 0.02735 | 0.5 | 0.05582 |
| K0 | INV10 | 14 | 6 | 0.01751 | 0.5 | 0.05252 |
| K0 | INV10 | 15 | 6 | 0.01557 | 0.5 | 0.05147 |
| K0 | INV10 | 16 | 6 | 0.0009535 | 0.5 | 0.05065 |
| K0 | INV10 | 17 | 6 | 0.001539 | 0.5 | 0.0495 |
| K0 | INV10 | 18 | 6 | 0.001556 | 0.5 | 0.04822 |
| K0 | INV10 | 19 | 6 | 0.01758 | 0.5 | 0.04804 |
| K0 | INV10 | 20 | 6 | 0.01004 | 0.5 | 0.04677 |
| Q0 | INV10 | 1 | 18 | 1.246 | 1 | 0.3156 |
| Q0 | INV10 | 2 | 18 | 0.3468 | 0.8889 | 0.2533 |
| Q0 | INV10 | 3 | 18 | 0.16 | 0.6667 | 0.2159 |
| Q0 | INV10 | 4 | 18 | 0.1393 | 0.5 | 0.1901 |
| Q0 | INV10 | 5 | 18 | 0.05587 | 0.5 | 0.1754 |
| Q0 | INV10 | 6 | 18 | 0.03898 | 0.5 | 0.1628 |
| Q0 | INV10 | 7 | 18 | 0.07496 | 0.5 | 0.1542 |
| Q0 | INV10 | 8 | 18 | 0.1101 | 0.5556 | 0.1472 |
| Q0 | INV10 | 9 | 18 | 0.1429 | 0.6111 | 0.1427 |
| Q0 | INV10 | 10 | 18 | 0.1639 | 0.6111 | 0.138 |
| Q0 | INV10 | 11 | 18 | 0.2021 | 0.6667 | 0.131 |
| Q0 | INV10 | 12 | 18 | 0.1853 | 0.6667 | 0.1266 |
| Q0 | INV10 | 13 | 18 | 0.161 | 0.6667 | 0.1256 |
| Q0 | INV10 | 14 | 18 | 0.1228 | 0.6111 | 0.1219 |
| Q0 | INV10 | 15 | 18 | 0.1026 | 0.6111 | 0.1196 |
| Q0 | INV10 | 16 | 18 | 0.09116 | 0.6111 | 0.1175 |
| Q0 | INV10 | 17 | 18 | 0.106 | 0.6667 | 0.1139 |
| Q0 | INV10 | 18 | 18 | 0.1164 | 0.6667 | 0.1119 |
| Q0 | INV10 | 19 | 18 | 0.1406 | 0.6667 | 0.1094 |
| Q0 | INV10 | 20 | 18 | 0.1289 | 0.6667 | 0.1061 |
| Q_D5 | INV10 | 1 | 18 | 1.047 | 1 | 0.2861 |
| Q_D5 | INV10 | 2 | 18 | 0.2089 | 0.6667 | 0.2259 |
| Q_D5 | INV10 | 3 | 18 | 0.1957 | 0.5556 | 0.1971 |
| Q_D5 | INV10 | 4 | 18 | 0.118 | 0.5 | 0.1758 |
| Q_D5 | INV10 | 5 | 18 | 0.01122 | 0.5 | 0.1583 |
| Q_D5 | INV10 | 6 | 18 | -0.01622 | 0.5 | 0.1485 |
| Q_D5 | INV10 | 7 | 18 | 0.001832 | 0.5 | 0.138 |
| Q_D5 | INV10 | 8 | 18 | 0.07928 | 0.5 | 0.1302 |
| Q_D5 | INV10 | 9 | 18 | 0.09786 | 0.5556 | 0.1249 |
| Q_D5 | INV10 | 10 | 18 | 0.06419 | 0.6111 | 0.1203 |
| Q_D5 | INV10 | 11 | 18 | 0.1055 | 0.6111 | 0.1145 |
| Q_D5 | INV10 | 12 | 18 | 0.0946 | 0.6111 | 0.1089 |
| Q_D5 | INV10 | 13 | 18 | 0.0786 | 0.6111 | 0.1057 |
| Q_D5 | INV10 | 14 | 18 | 0.05027 | 0.6111 | 0.1034 |
| Q_D5 | INV10 | 15 | 18 | 0.02751 | 0.6111 | 0.1003 |
| Q_D5 | INV10 | 16 | 18 | 0.03513 | 0.5556 | 0.09787 |
| Q_D5 | INV10 | 17 | 18 | 0.05759 | 0.6111 | 0.09679 |
| Q_D5 | INV10 | 18 | 18 | 0.08086 | 0.6667 | 0.09564 |
| Q_D5 | INV10 | 19 | 18 | 0.08826 | 0.6667 | 0.09488 |
| Q_D5 | INV10 | 20 | 18 | 0.07 | 0.6667 | 0.09385 |
| Q_RANK5 | INV10 | 1 | 18 | 1.066 | 1 | 0.2991 |
| Q_RANK5 | INV10 | 2 | 18 | 0.3088 | 0.8889 | 0.2362 |
| Q_RANK5 | INV10 | 3 | 18 | 0.2607 | 0.6667 | 0.2012 |
| Q_RANK5 | INV10 | 4 | 18 | 0.2285 | 0.6667 | 0.1829 |
| Q_RANK5 | INV10 | 5 | 18 | 0.1746 | 0.6111 | 0.1693 |
| Q_RANK5 | INV10 | 6 | 18 | 0.1279 | 0.6111 | 0.1598 |
| Q_RANK5 | INV10 | 7 | 18 | 0.103 | 0.6111 | 0.1491 |
| Q_RANK5 | INV10 | 8 | 18 | 0.1571 | 0.6111 | 0.1424 |
| Q_RANK5 | INV10 | 9 | 18 | 0.1741 | 0.6111 | 0.1383 |
| Q_RANK5 | INV10 | 10 | 18 | 0.1313 | 0.6111 | 0.1333 |
| Q_RANK5 | INV10 | 11 | 18 | 0.1518 | 0.6667 | 0.1298 |
| Q_RANK5 | INV10 | 12 | 18 | 0.1427 | 0.6667 | 0.1245 |
| Q_RANK5 | INV10 | 13 | 18 | 0.1125 | 0.6667 | 0.121 |
| Q_RANK5 | INV10 | 14 | 18 | 0.07661 | 0.6667 | 0.1166 |
| Q_RANK5 | INV10 | 15 | 18 | 0.07604 | 0.6667 | 0.1151 |
| Q_RANK5 | INV10 | 16 | 18 | 0.0526 | 0.6111 | 0.1123 |
| Q_RANK5 | INV10 | 17 | 18 | 0.08284 | 0.6667 | 0.1087 |
| Q_RANK5 | INV10 | 18 | 18 | 0.08139 | 0.6667 | 0.1092 |
| Q_RANK5 | INV10 | 19 | 18 | 0.086 | 0.6667 | 0.1071 |
| Q_RANK5 | INV10 | 20 | 18 | 0.07727 | 0.6667 | 0.1056 |


> 表头：主体=STRICT250 状态 − 主定义状态｜算子=STRICT250_VS_MAIN｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=六形态汇总（中位）｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=H 见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=见视图｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-S250


| meas | op | H | cells | median_D_ann_pp | share_pos | median_se_H_ann_pp |
|---|---|---|---|---|---|---|
| C1 | VOL_HI15 | 5 | 6 | 0.01138 | 0.8333 | 0.01595 |
| C1 | VOL_HI5 | 5 | 6 | -0.00699 | 0.3333 | 0.01458 |
| C1 | VOL_MEAN15 | 5 | 6 | -0.001327 | 0.3333 | 0.01263 |
| C1 | VOL_MEAN5 | 5 | 6 | -0.002495 | 0.5 | 0.01387 |
| K0 | VOL_HI15 | 5 | 6 | 0.004438 | 0.6667 | 0.01359 |
| K0 | VOL_HI5 | 5 | 6 | -0.01095 | 0.1667 | 0.01414 |
| K0 | VOL_MEAN15 | 5 | 6 | 0.01036 | 1 | 0.01293 |
| K0 | VOL_MEAN5 | 5 | 6 | -0.01024 | 0.1667 | 0.01552 |
| Q0 | VOL_HI15 | 5 | 6 | 0.005903 | 0.8333 | 0.01431 |
| Q0 | VOL_HI5 | 5 | 6 | -0.01889 | 0.3333 | 0.01852 |
| Q0 | VOL_MEAN15 | 5 | 6 | -0.007792 | 0.3333 | 0.01642 |
| Q0 | VOL_MEAN5 | 5 | 6 | -0.02543 | 0 | 0.01766 |
| Q_D5 | VOL_HI15 | 5 | 6 | 0.0104 | 0.6667 | 0.0161 |
| Q_D5 | VOL_HI5 | 5 | 6 | -0.006498 | 0.3333 | 0.0173 |
| Q_D5 | VOL_MEAN15 | 5 | 6 | 0.01353 | 1 | 0.0162 |
| Q_D5 | VOL_MEAN5 | 5 | 6 | -0.004969 | 0.3333 | 0.01762 |


## 5. 随机层（推导段；real − 随机均值与 MCSE；不作门）

> 表头：主体=随机参照（全部登记随机行）｜算子=按机制｜分母=两推导段有效配对日（n 加权）｜基准=同对象随机路径均值｜子集=随机清单全部行｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=1|2|3|5|10|20（R-MARK 1|5|20）｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-RAND


| mechanism | rows | paths_min | share_pos | median_rmr_ann_pp | worst_mcse_ann_pp | max_path_sd_ann_pp | share_pos_2mcse |
|---|---|---|---|---|---|---|---|
| CONTENT_COND_ISK_P5 | 9720 | 1024 | 0.81 | 0.1083 | 0.01337 | 0.7365 | 0.7969 |
| LEGACY_POLICY_RANDOM | 9720 | 1024 | 0.9131 | 0.1896 | 0.01232 | 0.6866 | 0.9071 |
| RMARK_ISK_P5 | 180 | 1024 | 0.9111 | 0.1082 | 0.008619 | 0.4609 | 0.9 |
| RMARK_UNIFORM_IID | 180 | 1024 | 0.9222 | 0.1728 | 0.009403 | 0.503 | 0.9222 |
| RMARK_UNIFORM_P5 | 180 | 1024 | 0.9222 | 0.1692 | 0.009592 | 0.5173 | 0.9167 |


> 表头：主体=真实 HG10 − R-MARK 随机（本路径自身标记在分区内置换）｜算子=R-MARK 三机制｜分母=两推导段有效配对日（n 加权）｜基准=同对象 R-MARK 路径均值｜子集=Q0 / Q_D5 / Q_RANK5 / 旧 K × HG10｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=1|5|20｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-RMARK


| meas | mother | alpha | H | RMARK_ISK_P5 | RMARK_UNIFORM_IID | RMARK_UNIFORM_P5 |
|---|---|---|---|---|---|---|
| K0 | A4b | a0 | 1 | 0.2414 | 0.4874 | 0.4791 |
| K0 | A4b | a0 | 5 | 0.1006 | 0.2025 | 0.2001 |
| K0 | A4b | a0 | 20 | 0.05144 | 0.0898 | 0.08971 |
| K0 | A4b_CVRv5 | a0 | 1 | 0.31 | 0.493 | 0.4882 |
| K0 | A4b_CVRv5 | a0 | 5 | 0.1 | 0.2006 | 0.1966 |
| K0 | A4b_CVRv5 | a0 | 20 | 0.0289 | 0.06919 | 0.06715 |
| K0 | M_mean3_v2 | a0 | 1 | 0.6075 | 0.5679 | 0.5298 |
| K0 | M_mean3_v2 | a0 | 5 | 0.07929 | 0.03021 | 0.02812 |
| K0 | M_mean3_v2 | a0 | 20 | 0.06925 | 0.0244 | 0.02274 |
| K0 | M_mean3_v2_CVRv5 | a0 | 1 | 0.3889 | 0.3374 | 0.301 |
| K0 | M_mean3_v2_CVRv5 | a0 | 5 | 0.01267 | -0.01257 | -0.01496 |
| K0 | M_mean3_v2_CVRv5 | a0 | 20 | 0.03717 | 0.008375 | 0.006418 |
| K0 | M_union3_v2 | a0 | 1 | 0.2935 | 0.3894 | 0.3575 |
| K0 | M_union3_v2 | a0 | 5 | 0.1589 | 0.2022 | 0.2029 |
| K0 | M_union3_v2 | a0 | 20 | 0.1095 | 0.1284 | 0.1278 |
| K0 | M_union3_v2_CVRv5 | a0 | 1 | 0.23 | 0.3081 | 0.2814 |
| K0 | M_union3_v2_CVRv5 | a0 | 5 | 0.1008 | 0.1399 | 0.1388 |
| K0 | M_union3_v2_CVRv5 | a0 | 20 | 0.09149 | 0.1132 | 0.1119 |
| Q0 | A4b | a0.125 | 1 | 0.3374 | 0.5639 | 0.5431 |
| Q0 | A4b | a0.125 | 5 | 0.1015 | 0.1438 | 0.1387 |
| Q0 | A4b | a0.125 | 20 | 0.0294 | 0.02395 | 0.02498 |
| Q0 | A4b | a0.25 | 1 | 0.3887 | 0.5913 | 0.5606 |
| Q0 | A4b | a0.25 | 5 | 0.03339 | 0.09323 | 0.09147 |
| Q0 | A4b | a0.25 | 20 | 0.01438 | 0.03426 | 0.03688 |
| Q0 | A4b | a0.5 | 1 | 0.684 | 1.596 | 1.335 |
| Q0 | A4b | a0.5 | 5 | 0.126 | 0.4345 | 0.4364 |
| Q0 | A4b | a0.5 | 20 | 0.1885 | 0.394 | 0.3956 |
| Q0 | A4b_CVRv5 | a0.125 | 1 | 0.389 | 0.5856 | 0.5709 |
| Q0 | A4b_CVRv5 | a0.125 | 5 | 0.137 | 0.2035 | 0.1993 |
| Q0 | A4b_CVRv5 | a0.125 | 20 | 0.04205 | 0.04716 | 0.04796 |
| Q0 | A4b_CVRv5 | a0.25 | 1 | 0.3747 | 0.5932 | 0.5679 |
| Q0 | A4b_CVRv5 | a0.25 | 5 | 0.08427 | 0.1777 | 0.1734 |
| Q0 | A4b_CVRv5 | a0.25 | 20 | 0.03273 | 0.06528 | 0.0671 |
| Q0 | A4b_CVRv5 | a0.5 | 1 | 0.5725 | 1.411 | 1.219 |
| Q0 | A4b_CVRv5 | a0.5 | 5 | 0.08396 | 0.4626 | 0.4668 |
| Q0 | A4b_CVRv5 | a0.5 | 20 | 0.07059 | 0.2629 | 0.264 |
| Q0 | M_mean3_v2 | a0.125 | 1 | 0.5637 | 0.5564 | 0.5104 |
| Q0 | M_mean3_v2 | a0.125 | 5 | 0.02926 | 0.007782 | 0.01043 |
| Q0 | M_mean3_v2 | a0.125 | 20 | 0.07206 | 0.05504 | 0.05663 |
| Q0 | M_mean3_v2 | a0.25 | 1 | 0.3948 | 0.3652 | 0.3034 |
| Q0 | M_mean3_v2 | a0.25 | 5 | -0.06424 | -0.08106 | -0.0798 |
| Q0 | M_mean3_v2 | a0.25 | 20 | 0.03034 | 0.04728 | 0.04717 |
| Q0 | M_mean3_v2 | a0.5 | 1 | 0.3904 | 0.6527 | 0.5675 |
| Q0 | M_mean3_v2 | a0.5 | 5 | 0.01092 | 0.04484 | 0.04175 |
| Q0 | M_mean3_v2 | a0.5 | 20 | 0.02566 | 0.04873 | 0.04547 |
| Q0 | M_mean3_v2_CVRv5 | a0.125 | 1 | 0.2478 | 0.2177 | 0.1797 |
| Q0 | M_mean3_v2_CVRv5 | a0.125 | 5 | -0.07387 | -0.07984 | -0.0783 |
| Q0 | M_mean3_v2_CVRv5 | a0.125 | 20 | 0.04669 | 0.03735 | 0.03866 |
| Q0 | M_mean3_v2_CVRv5 | a0.25 | 1 | 0.2428 | 0.2645 | 0.2159 |
| Q0 | M_mean3_v2_CVRv5 | a0.25 | 5 | -0.1106 | -0.0906 | -0.08978 |
| Q0 | M_mean3_v2_CVRv5 | a0.25 | 20 | 0.02626 | 0.04359 | 0.043 |
| Q0 | M_mean3_v2_CVRv5 | a0.5 | 1 | 0.1688 | 0.392 | 0.321 |
| Q0 | M_mean3_v2_CVRv5 | a0.5 | 5 | -0.1273 | -0.08814 | -0.09122 |
| Q0 | M_mean3_v2_CVRv5 | a0.5 | 20 | -0.0215 | 0.005179 | 0.002827 |
| Q0 | M_union3_v2 | a0.125 | 1 | 0.4197 | 0.4754 | 0.4325 |
| Q0 | M_union3_v2 | a0.125 | 5 | 0.2087 | 0.223 | 0.2262 |
| Q0 | M_union3_v2 | a0.125 | 20 | 0.1394 | 0.1467 | 0.149 |
| Q0 | M_union3_v2 | a0.25 | 1 | 0.6486 | 0.8063 | 0.735 |
| Q0 | M_union3_v2 | a0.25 | 5 | 0.2479 | 0.2969 | 0.2937 |
| Q0 | M_union3_v2 | a0.25 | 20 | 0.1326 | 0.1368 | 0.139 |
| Q0 | M_union3_v2 | a0.5 | 1 | 1.002 | 1.564 | 1.335 |
| Q0 | M_union3_v2 | a0.5 | 5 | 0.006707 | 0.22 | 0.2202 |
| Q0 | M_union3_v2 | a0.5 | 20 | 0.2015 | 0.3262 | 0.3284 |
| Q0 | M_union3_v2_CVRv5 | a0.125 | 1 | 0.4178 | 0.4748 | 0.4399 |
| Q0 | M_union3_v2_CVRv5 | a0.125 | 5 | 0.1759 | 0.2063 | 0.2079 |
| Q0 | M_union3_v2_CVRv5 | a0.125 | 20 | 0.1149 | 0.1264 | 0.1283 |
| Q0 | M_union3_v2_CVRv5 | a0.25 | 1 | 0.5819 | 0.7023 | 0.6441 |
| Q0 | M_union3_v2_CVRv5 | a0.25 | 5 | 0.2331 | 0.2873 | 0.2846 |
| Q0 | M_union3_v2_CVRv5 | a0.25 | 20 | 0.1212 | 0.128 | 0.1297 |
| Q0 | M_union3_v2_CVRv5 | a0.5 | 1 | 1.066 | 1.587 | 1.389 |
| Q0 | M_union3_v2_CVRv5 | a0.5 | 5 | 0.04503 | 0.27 | 0.2707 |
| Q0 | M_union3_v2_CVRv5 | a0.5 | 20 | 0.1796 | 0.3104 | 0.311 |
| Q_D5 | A4b | a0.125 | 1 | 0.1938 | 0.4102 | 0.3988 |
| Q_D5 | A4b | a0.125 | 5 | 0.1174 | 0.1615 | 0.1618 |
| Q_D5 | A4b | a0.125 | 20 | 0.0101 | 0.02744 | 0.0275 |
| Q_D5 | A4b | a0.25 | 1 | 0.479 | 0.7528 | 0.7379 |
| Q_D5 | A4b | a0.25 | 5 | 0.2125 | 0.2595 | 0.2627 |
| Q_D5 | A4b | a0.25 | 20 | 0.1146 | 0.1205 | 0.1226 |
| Q_D5 | A4b | a0.5 | 1 | 1.082 | 1.326 | 1.228 |
| Q_D5 | A4b | a0.5 | 5 | 0.0522 | 0.2271 | 0.2199 |
| Q_D5 | A4b | a0.5 | 20 | 0.02031 | 0.1229 | 0.1228 |
| Q_D5 | A4b_CVRv5 | a0.125 | 1 | 0.2993 | 0.4602 | 0.455 |
| Q_D5 | A4b_CVRv5 | a0.125 | 5 | 0.1505 | 0.2143 | 0.2157 |
| Q_D5 | A4b_CVRv5 | a0.125 | 20 | 0.02784 | 0.05479 | 0.05419 |
| Q_D5 | A4b_CVRv5 | a0.25 | 1 | 0.3833 | 0.6001 | 0.5889 |
| Q_D5 | A4b_CVRv5 | a0.25 | 5 | 0.1667 | 0.2339 | 0.234 |
| Q_D5 | A4b_CVRv5 | a0.25 | 20 | 0.1191 | 0.125 | 0.1259 |
| Q_D5 | A4b_CVRv5 | a0.5 | 1 | 0.8837 | 1.128 | 1.055 |
| Q_D5 | A4b_CVRv5 | a0.5 | 5 | 0.1031 | 0.2928 | 0.287 |
| Q_D5 | A4b_CVRv5 | a0.5 | 20 | 0.0628 | 0.1599 | 0.1622 |
| Q_D5 | M_mean3_v2 | a0.125 | 1 | 0.5984 | 0.4836 | 0.443 |
| Q_D5 | M_mean3_v2 | a0.125 | 5 | 0.0782 | 0.06259 | 0.06468 |
| Q_D5 | M_mean3_v2 | a0.125 | 20 | 0.05872 | 0.04007 | 0.04001 |
| Q_D5 | M_mean3_v2 | a0.25 | 1 | 0.7882 | 0.7166 | 0.6702 |
| Q_D5 | M_mean3_v2 | a0.25 | 5 | 0.1525 | 0.1063 | 0.1055 |
| Q_D5 | M_mean3_v2 | a0.25 | 20 | 0.03501 | 0.02385 | 0.02414 |
| Q_D5 | M_mean3_v2 | a0.5 | 1 | 0.5214 | 0.5622 | 0.4938 |
| Q_D5 | M_mean3_v2 | a0.5 | 5 | 0.01567 | -0.01693 | -0.01405 |
| Q_D5 | M_mean3_v2 | a0.5 | 20 | 0.01398 | 0.03296 | 0.03193 |
| Q_D5 | M_mean3_v2_CVRv5 | a0.125 | 1 | 0.4448 | 0.3545 | 0.316 |
| Q_D5 | M_mean3_v2_CVRv5 | a0.125 | 5 | 0.02041 | 0.02414 | 0.02273 |
| Q_D5 | M_mean3_v2_CVRv5 | a0.125 | 20 | 0.02635 | 0.01917 | 0.01825 |
| Q_D5 | M_mean3_v2_CVRv5 | a0.25 | 1 | 0.5928 | 0.5701 | 0.5291 |
| Q_D5 | M_mean3_v2_CVRv5 | a0.25 | 5 | 0.01142 | 0.02459 | 0.02243 |
| Q_D5 | M_mean3_v2_CVRv5 | a0.25 | 20 | -0.004172 | -0.0126 | -0.01229 |
| Q_D5 | M_mean3_v2_CVRv5 | a0.5 | 1 | 0.4022 | 0.4518 | 0.3934 |
| Q_D5 | M_mean3_v2_CVRv5 | a0.5 | 5 | -0.02277 | -0.01776 | -0.01524 |
| Q_D5 | M_mean3_v2_CVRv5 | a0.5 | 20 | 0.03335 | 0.05467 | 0.05418 |
| Q_D5 | M_union3_v2 | a0.125 | 1 | 0.4263 | 0.58 | 0.5402 |
| Q_D5 | M_union3_v2 | a0.125 | 5 | 0.1844 | 0.1962 | 0.1979 |
| Q_D5 | M_union3_v2 | a0.125 | 20 | 0.1101 | 0.1122 | 0.1129 |
| Q_D5 | M_union3_v2 | a0.25 | 1 | 0.3578 | 0.6399 | 0.5906 |
| Q_D5 | M_union3_v2 | a0.25 | 5 | 0.1274 | 0.2266 | 0.225 |
| Q_D5 | M_union3_v2 | a0.25 | 20 | 0.06983 | 0.08946 | 0.08965 |
| Q_D5 | M_union3_v2 | a0.5 | 1 | 0.4329 | 0.641 | 0.5673 |
| Q_D5 | M_union3_v2 | a0.5 | 5 | 0.05093 | 0.1678 | 0.165 |
| Q_D5 | M_union3_v2 | a0.5 | 20 | 0.1084 | 0.1581 | 0.1578 |
| Q_D5 | M_union3_v2_CVRv5 | a0.125 | 1 | 0.418 | 0.5523 | 0.5179 |
| Q_D5 | M_union3_v2_CVRv5 | a0.125 | 5 | 0.1839 | 0.211 | 0.2113 |
| Q_D5 | M_union3_v2_CVRv5 | a0.125 | 20 | 0.08824 | 0.0945 | 0.09454 |
| Q_D5 | M_union3_v2_CVRv5 | a0.25 | 1 | 0.4037 | 0.6222 | 0.5792 |
| Q_D5 | M_union3_v2_CVRv5 | a0.25 | 5 | 0.1486 | 0.2177 | 0.2145 |
| Q_D5 | M_union3_v2_CVRv5 | a0.25 | 20 | 0.0953 | 0.1176 | 0.1178 |
| Q_D5 | M_union3_v2_CVRv5 | a0.5 | 1 | 0.3645 | 0.549 | 0.4891 |
| Q_D5 | M_union3_v2_CVRv5 | a0.5 | 5 | 0.06394 | 0.1939 | 0.1935 |
| Q_D5 | M_union3_v2_CVRv5 | a0.5 | 20 | 0.1078 | 0.1634 | 0.1636 |
| Q_RANK5 | A4b | a0.125 | 1 | 0.1508 | 0.4011 | 0.4003 |
| Q_RANK5 | A4b | a0.125 | 5 | -0.03351 | -0.004187 | -0.0009524 |
| Q_RANK5 | A4b | a0.125 | 20 | 0.006495 | 0.008295 | 0.007112 |
| Q_RANK5 | A4b | a0.25 | 1 | 0.2531 | 0.4736 | 0.4563 |
| Q_RANK5 | A4b | a0.25 | 5 | -0.02129 | 0.06065 | 0.06214 |
| Q_RANK5 | A4b | a0.25 | 20 | 0.001617 | 0.03756 | 0.0387 |
| Q_RANK5 | A4b | a0.5 | 1 | 0.8109 | 1.21 | 1.121 |
| Q_RANK5 | A4b | a0.5 | 5 | 0.05562 | 0.1875 | 0.1855 |
| Q_RANK5 | A4b | a0.5 | 20 | 0.01535 | 0.09648 | 0.09735 |
| Q_RANK5 | A4b_CVRv5 | a0.125 | 1 | 0.1592 | 0.3619 | 0.3615 |
| Q_RANK5 | A4b_CVRv5 | a0.125 | 5 | -0.01146 | 0.054 | 0.05401 |
| Q_RANK5 | A4b_CVRv5 | a0.125 | 20 | 0.009906 | 0.02701 | 0.02511 |
| Q_RANK5 | A4b_CVRv5 | a0.25 | 1 | 0.2247 | 0.4229 | 0.4084 |
| Q_RANK5 | A4b_CVRv5 | a0.25 | 5 | 0.04813 | 0.1519 | 0.1507 |
| Q_RANK5 | A4b_CVRv5 | a0.25 | 20 | 0.01247 | 0.05785 | 0.05753 |
| Q_RANK5 | A4b_CVRv5 | a0.5 | 1 | 0.6163 | 0.9842 | 0.9253 |
| Q_RANK5 | A4b_CVRv5 | a0.5 | 5 | 0.02876 | 0.198 | 0.1957 |
| Q_RANK5 | A4b_CVRv5 | a0.5 | 20 | 0.009626 | 0.09328 | 0.09349 |
| Q_RANK5 | M_mean3_v2 | a0.125 | 1 | 0.539 | 0.4621 | 0.4212 |
| Q_RANK5 | M_mean3_v2 | a0.125 | 5 | 0.07305 | 0.02617 | 0.02401 |
| Q_RANK5 | M_mean3_v2 | a0.125 | 20 | 0.07935 | 0.05851 | 0.05686 |
| Q_RANK5 | M_mean3_v2 | a0.25 | 1 | 0.5635 | 0.5134 | 0.4498 |
| Q_RANK5 | M_mean3_v2 | a0.25 | 5 | 0.1603 | 0.1097 | 0.1005 |
| Q_RANK5 | M_mean3_v2 | a0.25 | 20 | 0.05753 | 0.05658 | 0.05509 |
| Q_RANK5 | M_mean3_v2 | a0.5 | 1 | 0.7957 | 0.8641 | 0.7957 |
| Q_RANK5 | M_mean3_v2 | a0.5 | 5 | -0.0002039 | -0.03591 | -0.0353 |
| Q_RANK5 | M_mean3_v2 | a0.5 | 20 | -0.04641 | -0.03121 | -0.03221 |
| Q_RANK5 | M_mean3_v2_CVRv5 | a0.125 | 1 | 0.4157 | 0.3126 | 0.2761 |
| Q_RANK5 | M_mean3_v2_CVRv5 | a0.125 | 5 | -0.001719 | -0.03528 | -0.03728 |
| Q_RANK5 | M_mean3_v2_CVRv5 | a0.125 | 20 | 0.03005 | 0.02269 | 0.02111 |
| Q_RANK5 | M_mean3_v2_CVRv5 | a0.25 | 1 | 0.567 | 0.5166 | 0.4652 |
| Q_RANK5 | M_mean3_v2_CVRv5 | a0.25 | 5 | 0.1023 | 0.08936 | 0.08352 |
| Q_RANK5 | M_mean3_v2_CVRv5 | a0.25 | 20 | 0.05412 | 0.05605 | 0.0547 |
| Q_RANK5 | M_mean3_v2_CVRv5 | a0.5 | 1 | 0.544 | 0.6276 | 0.5673 |
| Q_RANK5 | M_mean3_v2_CVRv5 | a0.5 | 5 | -0.06491 | -0.07393 | -0.07592 |
| Q_RANK5 | M_mean3_v2_CVRv5 | a0.5 | 20 | -0.01049 | -0.001644 | -0.002569 |
| Q_RANK5 | M_union3_v2 | a0.125 | 1 | 0.217 | 0.3296 | 0.2897 |
| Q_RANK5 | M_union3_v2 | a0.125 | 5 | 0.08127 | 0.09896 | 0.1001 |
| Q_RANK5 | M_union3_v2 | a0.125 | 20 | 0.088 | 0.09733 | 0.09749 |
| Q_RANK5 | M_union3_v2 | a0.25 | 1 | 0.3873 | 0.6283 | 0.5788 |
| Q_RANK5 | M_union3_v2 | a0.25 | 5 | 0.01705 | 0.1106 | 0.1073 |
| Q_RANK5 | M_union3_v2 | a0.25 | 20 | 0.02285 | 0.03453 | 0.03612 |
| Q_RANK5 | M_union3_v2 | a0.5 | 1 | 0.4133 | 0.6188 | 0.5297 |
| Q_RANK5 | M_union3_v2 | a0.5 | 5 | 0.03652 | 0.1156 | 0.1108 |
| Q_RANK5 | M_union3_v2 | a0.5 | 20 | 0.1495 | 0.1996 | 0.1997 |
| Q_RANK5 | M_union3_v2_CVRv5 | a0.125 | 1 | 0.272 | 0.3637 | 0.3297 |
| Q_RANK5 | M_union3_v2_CVRv5 | a0.125 | 5 | 0.108 | 0.1326 | 0.1311 |
| Q_RANK5 | M_union3_v2_CVRv5 | a0.125 | 20 | 0.08426 | 0.09809 | 0.09782 |
| Q_RANK5 | M_union3_v2_CVRv5 | a0.25 | 1 | 0.3728 | 0.5778 | 0.5364 |
| Q_RANK5 | M_union3_v2_CVRv5 | a0.25 | 5 | 0.06041 | 0.1444 | 0.1398 |
| Q_RANK5 | M_union3_v2_CVRv5 | a0.25 | 20 | 0.03795 | 0.056 | 0.05757 |
| Q_RANK5 | M_union3_v2_CVRv5 | a0.5 | 1 | 0.3739 | 0.5353 | 0.4673 |
| Q_RANK5 | M_union3_v2_CVRv5 | a0.5 | 5 | -0.02333 | 0.07211 | 0.06818 |
| Q_RANK5 | M_union3_v2_CVRv5 | a0.5 | 20 | 0.0995 | 0.1495 | 0.1496 |


## 6. Stage A 掩码层事实（推导两段；读数前已冻结）

> 表头：主体=门层记忆 / 库存 / 名单事实（α .25，旧 K α0；六形态 × 测量 × 两段中位）｜算子=按算子｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=mask_facts_deriv_E6l｜单位=份额 / 日数｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=INV 按 H；其余与 H 无关｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-STAGEA


| op | bonus_reliant_share_median | reliant_run_p90_median | confirm_age_p90_median | gate_retention_median | list_retention_median | self_edits_per_day_median | downstream_survival_median | inv_mark_coverage_median | inv_saturated_day_share_median | pending_expiry_overlap_median | edit_persistence_5d_reversal_share_median | same_ticker_overlap_with_native_median |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DECAY2_10 | 0.04771 | 1 | 0 | 0.6179 | 0.5897 | 38.18 | 0.4567 |  |  |  | 0.9244 | 0.5639 |
| DECAY5_10 | 0.04886 | 1 | 0 | 0.619 | 0.5905 | 38.09 | 0.4567 |  |  |  | 0.9221 | 0.5614 |
| HG10 | 0.05655 | 1 | 0 | 0.6195 | 0.5879 | 37.99 | 0.4568 |  |  |  | 0.9183 | 0.6001 |
| HG15 | 0.08436 | 2 | 0 | 0.6479 | 0.6083 | 36.33 | 0.4569 |  |  |  | 0.9055 | 0.4698 |
| HG20 | 0.08957 | 2 | 0 | 0.678 | 0.6273 | 35.08 | 0.4568 |  |  |  | 0.9034 | 0.3267 |
| HG30 | 0.1295 | 2 | 1 | 0.7297 | 0.6684 | 32.75 | 0.4572 |  |  |  | 0.8784 | 0.2315 |
| HG5 | 0.02921 | 1 | 0 | 0.5898 | 0.5676 | 40.08 | 0.4567 |  |  |  | 0.9261 | 0.7806 |
| INV10 |  |  |  |  | 0.5937 | 39.65 | 0.4581 | 0.3296 | 0 | 0.144 | 0.9164 | 0.5264 |
| LAG1_10 | 0.04974 | 1 | 0 | 0.6104 | 0.5833 | 38.63 | 0.4567 |  |  |  | 0.9282 | 0.5568 |
| NATIVE |  |  |  |  | 0.5477 | 42.17 | 0.4973 |  |  |  | 0.9377 |  |
| VOL_HI15 | 0.03788 | 1 | 0 | 0.6144 | 0.5814 | 38.89 | 0.4567 |  |  |  | 0.9243 | 0.5887 |
| VOL_HI5 | 0.05432 | 1 | 0 | 0.6346 | 0.5979 | 37.41 | 0.4568 |  |  |  | 0.9169 | 0.4793 |
| VOL_MEAN15 | 0.03791 | 1 | 0 | 0.6147 | 0.583 | 38.76 | 0.4567 |  |  |  | 0.9244 | 0.5853 |
| VOL_MEAN5 | 0.05431 | 1 | 0 | 0.635 | 0.5977 | 37.39 | 0.4568 |  |  |  | 0.9174 | 0.475 |


## 7. 推导段配对 MDE80 与卡片 ⑬（只用日差标准误；不改预测）

> 表头：主体=16 卡绑定比较的 MDE80（2.80 × HAC(H) se）｜算子=按卡｜分母=两推导段有效配对日（n 加权）｜基准=比较右端｜子集=paired_mde80_deriv｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=各比较自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-T13


| card | segment | n_comparisons | mde80_p10_ann_pp | mde80_median_ann_pp | mde80_p90_ann_pp | t13_label |
|---|---|---|---|---|---|---|
| Q01 | 2010-2014 | 32400 | 0.2027 | 0.4275 | 0.9347 | MDE80 中位 > .30：首看，只记录 |
| Q01 | 2015-2018 | 32400 | 0.3415 | 0.6951 | 1.629 | MDE80 中位 > .30：首看，只记录 |
| Q02 | 2010-2014 | 79920 | 0.168 | 0.2999 | 0.7261 | .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号 |
| Q02 | 2015-2018 | 79920 | 0.2593 | 0.4734 | 1.212 | MDE80 中位 > .30：首看，只记录 |
| Q03 | 2010-2014 | 32112 | 0.1631 | 0.348 | 0.8414 | MDE80 中位 > .30：首看，只记录 |
| Q03 | 2015-2018 | 32112 | 0.2693 | 0.5742 | 1.506 | MDE80 中位 > .30：首看，只记录 |
| Q04 | 2010-2014 | 5760 | 0.1127 | 0.2189 | 0.485 | .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号 |
| Q04 | 2015-2018 | 5760 | 0.1641 | 0.3255 | 0.7483 | MDE80 中位 > .30：首看，只记录 |
| Q05 | 2010-2014 | 6048 | 0.02768 | 0.2384 | 0.6254 | .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号 |
| Q05 | 2015-2018 | 5979 | 0.06204 | 0.3706 | 0.9897 | MDE80 中位 > .30：首看，只记录 |
| Q06 | 2010-2014 | 1560 | 0.07182 | 0.1132 | 0.2501 | .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号 |
| Q06 | 2015-2018 | 1560 | 0.1065 | 0.1682 | 0.3829 | .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号 |
| Q07 | 2010-2014 | 4680 | 0.02929 | 0.05201 | 0.1269 | MDE80 中位 ≤ .10：.10 级配对差可 80% 分辨 |
| Q07 | 2015-2018 | 4680 | 0.04793 | 0.08251 | 0.1965 | MDE80 中位 ≤ .10：.10 级配对差可 80% 分辨 |
| Q08 | 2010-2014 | 3107 | 0.1666 | 0.2386 | 0.4184 | .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号 |
| Q08 | 2015-2018 | 3107 | 0.2396 | 0.408 | 0.7128 | MDE80 中位 > .30：首看，只记录 |
| Q09 | 2010-2014 | 48597 | 0.1672 | 0.3276 | 0.7972 | MDE80 中位 > .30：首看，只记录 |
| Q09 | 2015-2018 | 48597 | 0.263 | 0.5282 | 1.352 | MDE80 中位 > .30：首看，只记录 |
| Q10 | 2010-2014 | 0 |  |  |  | UNDEFINED（无绑定配对比较 / 方法卡） |
| Q10 | 2015-2018 | 0 |  |  |  | UNDEFINED（无绑定配对比较 / 方法卡） |
| Q11 | 2010-2014 | 11280 | 0.1287 | 0.2006 | 0.4021 | .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号 |
| Q11 | 2015-2018 | 11280 | 0.1952 | 0.303 | 0.5962 | MDE80 中位 > .30：首看，只记录 |
| Q12 | 2010-2014 | 7200 | 0.09462 | 0.1618 | 0.3281 | .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号 |
| Q12 | 2015-2018 | 7200 | 0.1409 | 0.2522 | 0.516 | .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号 |
| Q13 | 2010-2014 | 96 | 0.05607 | 0.07917 | 0.09678 | MDE80 中位 ≤ .10：.10 级配对差可 80% 分辨 |
| Q13 | 2015-2018 | 0 |  |  |  | UNDEFINED（无绑定配对比较 / 方法卡） |
| Q14 | 2010-2014 | 0 |  |  |  | UNDEFINED（无绑定配对比较 / 方法卡） |
| Q14 | 2015-2018 | 0 |  |  |  | UNDEFINED（无绑定配对比较 / 方法卡） |
| Q15 | 2010-2014 | 28080 | 0.1915 | 0.4317 | 1.01 | MDE80 中位 > .30：首看，只记录 |
| Q15 | 2015-2018 | 28080 | 0.3174 | 0.7045 | 1.792 | MDE80 中位 > .30：首看，只记录 |
| Q16 | 2010-2014 | 0 |  |  |  | UNDEFINED（无绑定配对比较 / 方法卡） |
| Q16 | 2015-2018 | 0 |  |  |  | UNDEFINED（无绑定配对比较 / 方法卡） |


## 8. 十六张卡的推导段初读（机械计数；后段首看后才用首看标签）

> 表头：主体=16 张卡的登记对象与绑定比较｜算子=按卡｜分母=两推导段有效配对日（n 加权）｜基准=同 H 原父（8bp）｜子集=question_to_objects_E6l / comparison_manifest｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2018-12-28（推导两段；每段前 19 日预热）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（MATCH-CAP 另列 D_sc）｜exposure=见 evidence_exposure 列｜query_id=E6L-P1-CARDS


| card | objects | with_deriv_rows | share_D_pos | median_D_ann_pp | bound_comparisons | median_cmp_D_ann_pp | queries |
|---|---|---|---|---|---|---|---|
| Q01 | 3776 | 3616 | 0.9497 | 0.2084 | 42120 | 0.1907 | E6L-Q01-a\|E6L-Q01-b\|E6L-Q01-c |
| Q02 | 28200 | 28200 | 0.9273 | 0.1952 | 79920 | 0.05672 | E6L-Q02-a\|E6L-Q02-b |
| Q03 | 13284 | 13284 | 0.913 | 0.2188 | 32112 | -0.07236 | E6L-Q03-a\|E6L-Q03-b |
| Q04 | 9360 | 9360 | 0.8939 | 0.1756 | 5760 | -0.000417 | E6L-Q04-a\|E6L-Q04-b |
| Q05 | 4644 | 4644 | 0.862 | 0.1467 | 6480 | 0 | E6L-Q05-a\|E6L-Q05-b |
| Q06 | 8880 | 8880 | 0.9205 | 0.1866 | 1560 | -0.005671 | E6L-Q06-a\|E6L-Q06-b |
| Q07 | 10600 | 10440 | 0.9221 | 0.1874 | 4680 | -0.003597 | E6L-Q07-a\|E6L-Q07-b |
| Q08 | 9000 | 9000 | 0.9317 | 0.2025 | 4680 | 0.04821 | E6L-Q08-a\|E6L-Q08-b |
| Q09 | 12240 | 12240 | 0.9041 | 0.183 | 48600 | -0.04685 | E6L-Q09-a |
| Q10 | 180 | 180 | 0.9278 | 0.2633 | 10260 | 0.1101 | E6L-Q10-a\|E6L-Q10-b |
| Q11 | 1154 | 1146 | 0.774 | 0.1957 | 11280 | 0.01907 | E6L-Q11-a |
| Q12 | 19080 | 19080 | 0.9245 | 0.1938 | 7200 | -0.01023 | E6L-Q12-a\|E6L-Q12-b |
| Q13 | 4392 | 4392 | 0.9488 | 0.2129 | 96 | -0.001067 | E6L-Q13-a\|E6L-Q13-b |
| Q14 | 11360 | 11320 | 0.8943 | 0.1365 | 33960 | 0.1337 | E6L-Q14-a |
| Q15 | 2160 | 2160 | 0.9764 | 0.244 | 28080 | 0.03322 | E6L-Q15-a |
| Q16 | 1 | 33960 | 0.9107 | 0.185 | 0 |  | E6L-Q16-a |


## 9. 未做项及原因

- 两后段（2019-2023 / 2024-2026）：方式 B，record B 草稿与进入核验（`record_B_entry_post_E6l.json`）之后同版本一次算完、seal_post。

- 政策（六条 + PORT3_T）逐对象评分、bootstrap（段内分层 stationary 20 / 60 × 2,000）、连续状态面板、三时钟、影子与风险：brief §5 次序在 seal_post 之后。
