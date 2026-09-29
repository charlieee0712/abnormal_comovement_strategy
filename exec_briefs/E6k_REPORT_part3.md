# E6k REPORT part3 —— 144 主配置 / 四 C1_hi / SM 锚：五列政策 profile 与生产变更候选清单

用途：plan §13.5 part3。政策 profile 五列并印（`registration/policy_profiles_E6k.json` + `_amend_1`）：LEGACY_EDIT5（E6j 登记口径复现）、PROPOSED_PORT3_T、PROPOSED_PORT3_LAG1（brief W12）与两列执行端 print-only（EXEC_DISCLOSE_ONLY、EXEC_LEADER_VS_PARENT；用户"设计尽量宽松"）；差异属定义、不择优；`policy_provisional = true`；新算子 `replacement_preference_status = NOT_AUTHORIZED`；`deployment_authorized = false`。标签：新算子行 `NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY`。

## profile LEGACY_EDIT5

> 表头：主体=144 主展示 + C1_hi + SM 锚｜算子=见列｜分母=四段有效配对日（FULL = n 加权；G4 = 段中位）｜基准=同 H 原父（8bp）｜子集=primary144 | c1_hi | sm_anchor｜单位=年化百分点 / 判词｜日期=2010-01-04..2026-03-27（四段；2026 partial）｜H=H 见列｜成本模型=源 8bp（f：A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（e 资本：MATCH-CAP）｜exposure=见 evidence_exposure 列｜query_id=E6K-P3-POL-LEGACYEDIT5


| meas | mother | op | alpha | H | FULL | G4 | ci_L20_lo | ci_L20_hi | FULL_sc | FULL_imp | years_pos | e_rand | FULL_vs_native | FULL_vs_nativeC1 | evidence_exposure | size_LEGACY_EDIT5 | policy_LEGACY_EDIT5_FULL | policy_LEGACY_EDIT5_G4 | POLICY_INTERPRETATION_PENDING_LEGACY_EDIT5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | A4b | INC1 | 0.25 | 5 | 0.1993 | 0.1666 | 0.03081 | 0.3619 | 0.2035 | 0.2056 | 13 | MC_UNRESOLVED | -0.06553 | -0.06553 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| C1 | A4b | INC1_HG10 | 0.25 | 5 | 0.2376 | 0.3176 | 0.01428 | 0.453 | 0.2399 | 0.2533 | 11 | FAIL | -0.02717 | -0.02717 | first_evaluation | FAIL | 不通过（d、e随机、size(LEGACY_EDIT5)） | 不通过（d、e随机、size(LEGACY_EDIT5)） | False |
| C1 | A4b | NATIVE | 0.25 | 5 | 0.2648 | 0.311 | 0.07639 | 0.4442 | 0.2649 | 0.2738 | 13 | PASS |  |  | same_account_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| C1 | A4b | NATIVE | 0.5 | 10 | 0.4742 | 0.5273 | 0.19 | 0.755 | 0.4401 | 0.4511 | 14 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b | NATIVE | 0.5 | 20 | 0.3358 | 0.3565 | 0.1394 | 0.5252 | 0.3152 | 0.3247 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b | NATIVE_HG10 | 0.25 | 5 | 0.2929 | 0.2275 | 0.04494 | 0.5338 | 0.2869 | 0.309 | 10 | PASS | 0.02809 | 0.02809 | first_evaluation | FAIL | 不通过（d、size(LEGACY_EDIT5)） | 不通过（d、size(LEGACY_EDIT5)） | False |
| C1 | A4b | RP3 | 0.25 | 5 | 0.02682 | 0.01826 | -0.04199 | 0.0943 | 0.02682 | 0.02785 | 11 | PASS | -0.238 | -0.238 | first_evaluation | FAIL | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | False |
| C1 | A4b | SZL5 | 0.25 | 5 | 0.1258 | 0.03719 | -0.0705 | 0.3107 | 0.1328 | 0.1327 | 10 | PASS | -0.139 | -0.139 | first_evaluation | FAIL | 不通过（d、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | False |
| C1 | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1824 | 0.2094 | 0.03225 | 0.32 | 0.1639 | 0.1768 | 12 | FAIL | -0.1039 | -0.1039 | first_evaluation | FAIL | 不通过（e随机、size(LEGACY_EDIT5)） | 不通过（e随机、size(LEGACY_EDIT5)） | False |
| C1 | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2232 | 0.3032 | 0.02851 | 0.4113 | 0.2118 | 0.2213 | 10 | FAIL | -0.06307 | -0.06307 | first_evaluation | FAIL | 不通过（d、e随机、size(LEGACY_EDIT5)） | 不通过（d、e随机、size(LEGACY_EDIT5)） | False |
| C1 | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.2863 | 0.3224 | 0.1182 | 0.4473 | 0.2728 | 0.2809 | 14 | PASS |  |  | same_account_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| C1 | A4b_CVRv5 | NATIVE | 0.5 | 10 | 0.4206 | 0.3958 | 0.1749 | 0.6575 | 0.4056 | 0.3929 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b_CVRv5 | NATIVE | 0.5 | 20 | 0.2857 | 0.2776 | 0.1175 | 0.456 | 0.2734 | 0.2736 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.2387 | 0.2548 | 0.02666 | 0.4464 | 0.2218 | 0.2312 | 11 | PASS | -0.04761 | -0.04761 | first_evaluation | FAIL | 不通过（d、size(LEGACY_EDIT5)） | 不通过（d、size(LEGACY_EDIT5)） | False |
| C1 | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.03286 | 0.03379 | -0.02538 | 0.0921 | 0.03286 | 0.0335 | 11 | PASS | -0.2534 | -0.2534 | first_evaluation | FAIL | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | False |
| C1 | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.124 | 0.07449 | -0.04594 | 0.2898 | 0.1211 | 0.1234 | 11 | FAIL | -0.1623 | -0.1623 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| C1 | M_mean3_v2 | INC1 | 0.25 | 5 | 0.1792 | 0.0971 | 0.04069 | 0.319 | 0.1741 | 0.1999 | 13 | FAIL | -0.02146 | -0.02146 | first_evaluation | PASS | 不通过（e随机） | 不通过（正向门槛、e随机） | False |
| C1 | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.06166 | 0.008405 | -0.1416 | 0.2776 | 0.05662 | 0.1124 | 11 | FAIL | -0.139 | -0.139 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.2006 | 0.1498 | 0.04456 | 0.3478 | 0.1946 | 0.2267 | 13 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.1979 | 0.111 | -0.03353 | 0.4343 | 0.1943 | 0.254 | 12 | FAIL | -0.002698 | -0.002698 | first_evaluation | PASS | 不通过（c、e随机） | 不通过（c、e随机） | False |
| C1 | M_mean3_v2 | RP3 | 0.25 | 5 | 0.07358 | 0.06543 | 0.02002 | 0.1256 | 0.07358 | 0.07844 | 9 | FAIL | -0.127 | -0.127 | first_evaluation | FAIL | 不通过（d、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| C1 | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.1672 | 0.1965 | -0.03337 | 0.3789 | 0.1737 | 0.2275 | 10 | FAIL | -0.03339 | -0.03339 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | False |
| C1 | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.08837 | 0.07339 | -0.0385 | 0.2151 | 0.0802 | 0.1053 | 12 | FAIL | -0.01609 | -0.01609 | first_evaluation | PASS | 不通过（正向门槛、e随机） | 不通过（正向门槛、e随机） | False |
| C1 | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.1125 | -0.1064 | -0.3101 | 0.08312 | -0.1186 | -0.0699 | 7 | FAIL | -0.217 | -0.217 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.1045 | 0.09114 | -0.03507 | 0.2393 | 0.09502 | 0.1255 | 12 | PASS |  |  | same_account_exposed | PASS | 通过 | 不通过（正向门槛） | True |
| C1 | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.00137 | -0.009876 | -0.2139 | 0.2206 | -0.009498 | 0.04625 | 10 | PASS | -0.1031 | -0.1031 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e资本） | 不通过（c、d、f、正向门槛） | False |
| C1 | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.03224 | 0.03028 | -0.0182 | 0.08394 | 0.03224 | 0.03556 | 8 | PASS | -0.07222 | -0.07222 | first_evaluation | FAIL | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | False |
| C1 | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.02625 | 0.02404 | -0.1984 | 0.1458 | -0.02549 | 0.03063 | 9 | PASS | -0.1307 | -0.1307 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | False |
| C1 | M_union3_v2 | INC1 | 0.25 | 5 | 0.03555 | 0.07215 | -0.1007 | 0.173 | 0.0064 | -0.004975 | 11 | FAIL | -0.05409 | -0.05409 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| C1 | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.1696 | 0.1773 | -0.01546 | 0.3613 | 0.06871 | 0.09116 | 12 | PASS | 0.07999 | 0.07999 | first_evaluation | FAIL | 不通过（f、size(LEGACY_EDIT5)） | 不通过（f、size(LEGACY_EDIT5)） | False |
| C1 | M_union3_v2 | NATIVE | 0.25 | 5 | 0.08964 | 0.09268 | -0.06266 | 0.2459 | 0.04254 | 0.03047 | 12 | PASS |  |  | same_account_exposed | FAIL | 不通过（正向门槛、size(LEGACY_EDIT5)） | 不通过（正向门槛、size(LEGACY_EDIT5)） | False |
| C1 | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.1652 | 0.1857 | -0.0345 | 0.3763 | 0.05509 | 0.06316 | 12 | PASS | 0.07554 | 0.07554 | first_evaluation | FAIL | 不通过（f、size(LEGACY_EDIT5)） | 不通过（f、size(LEGACY_EDIT5)） | False |
| C1 | M_union3_v2 | RP3 | 0.25 | 5 | 0.01305 | 0.004054 | -0.03189 | 0.05926 | 0.01305 | 0.01005 | 11 | FAIL | -0.07659 | -0.07659 | first_evaluation | FAIL | 不通过（d、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| C1 | M_union3_v2 | SZL5 | 0.25 | 5 | -0.05162 | -0.05403 | -0.2646 | 0.16 | -0.1339 | -0.1258 | 8 | FAIL | -0.1413 | -0.1413 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| C1 | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.01715 | 0.04369 | -0.1179 | 0.1548 | -0.009748 | -0.02245 | 10 | FAIL | -0.05489 | -0.05489 | first_evaluation | FAIL | 不通过（d、f、正向门槛、e资本、e随机、size(LEGACY_EDIT5)） | 不通过（d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| C1 | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.1555 | 0.1447 | -0.02468 | 0.3374 | 0.06176 | 0.0744 | 12 | PASS | 0.08346 | 0.08346 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| C1 | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.07205 | 0.08064 | -0.07399 | 0.2168 | 0.03263 | 0.01425 | 10 | PASS |  |  | same_account_exposed | FAIL | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | False |
| C1 | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.1526 | 0.1473 | -0.04438 | 0.3466 | 0.04796 | 0.0497 | 12 | PASS | 0.08059 | 0.08059 | first_evaluation | FAIL | 不通过（f、size(LEGACY_EDIT5)） | 不通过（f、size(LEGACY_EDIT5)） | False |
| C1 | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.00119 | -0.00744 | -0.03962 | 0.04427 | 0.00119 | -0.0009616 | 9 | FAIL | -0.07086 | -0.07086 | first_evaluation | FAIL | 不通过（d、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| C1 | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.02526 | 0.01453 | -0.2121 | 0.1562 | -0.09905 | -0.09544 | 9 | FAIL | -0.0973 | -0.0973 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e资本、e随机、size(LEGACY_EDIT5)） | False |
| M | A4b | INC1 | 0.25 | 5 | 0.1232 | 0.04958 | -0.07289 | 0.3303 | 0.1384 | 0.1445 | 11 | FAIL | -0.2154 | -0.1416 | first_evaluation | FAIL | 不通过（d、e随机、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| M | A4b | INC1_HG10 | 0.25 | 5 | 0.1888 | 0.1395 | -0.05864 | 0.4124 | 0.1945 | 0.2289 | 11 | FAIL | -0.1499 | -0.07604 | first_evaluation | FAIL | 不通过（c、d、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、e随机、size(LEGACY_EDIT5)） | False |
| M | A4b | NATIVE | 0.25 | 5 | 0.3386 | 0.2736 | 0.1176 | 0.5664 | 0.3462 | 0.3521 | 14 | PASS |  | 0.07382 | same_account_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| M | A4b | NATIVE_HG10 | 0.25 | 5 | 0.3479 | 0.2125 | 0.113 | 0.5916 | 0.3579 | 0.3797 | 12 | PASS | 0.009267 | 0.08309 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| M | A4b | RP3 | 0.25 | 5 | 0.0804 | 0.1039 | 0.001027 | 0.1645 | 0.0804 | 0.08056 | 10 | PASS | -0.2582 | -0.1844 | first_evaluation | FAIL | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | 不通过（d、size(LEGACY_EDIT5)） | False |
| M | A4b | SZL5 | 0.25 | 5 | 0.2483 | 0.1122 | 0.03211 | 0.4758 | 0.2632 | 0.2705 | 12 | FAIL | -0.09035 | -0.01653 | first_evaluation | FAIL | 不通过（c、f、e随机、size(LEGACY_EDIT5)） | 不通过（c、f、e随机、size(LEGACY_EDIT5)） | False |
| M | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1118 | 0.1358 | -0.06575 | 0.2965 | 0.1217 | 0.1257 | 12 | FAIL | -0.2282 | -0.1745 | first_evaluation | FAIL | 不通过（c、f、e随机、size(LEGACY_EDIT5)） | 不通过（c、f、e随机、size(LEGACY_EDIT5)） | False |
| M | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2176 | 0.143 | 0.004276 | 0.4178 | 0.2152 | 0.2404 | 12 | FAIL | -0.1224 | -0.06868 | first_evaluation | FAIL | 不通过（e随机、size(LEGACY_EDIT5)） | 不通过（e随机、size(LEGACY_EDIT5)） | False |
| M | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.34 | 0.2745 | 0.1475 | 0.5325 | 0.3456 | 0.3408 | 15 | PASS |  | 0.0537 | same_account_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| M | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.371 | 0.3839 | 0.1612 | 0.5794 | 0.3812 | 0.3836 | 12 | PASS | 0.03103 | 0.08473 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| M | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.06943 | 0.08925 | 0.000882 | 0.1387 | 0.06943 | 0.06759 | 10 | PASS | -0.2706 | -0.2169 | first_evaluation | FAIL | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | False |
| M | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.2398 | 0.1384 | 0.03711 | 0.4456 | 0.2481 | 0.253 | 13 | PASS | -0.1002 | -0.04655 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| M | M_mean3_v2 | INC1 | 0.25 | 5 | 0.3977 | 0.3379 | 0.1925 | 0.6053 | 0.3944 | 0.4544 | 14 | PASS | -0.03838 | 0.1971 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.3382 | 0.2332 | 0.1108 | 0.5797 | 0.3284 | 0.4276 | 13 | FAIL | -0.09796 | 0.1376 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| M | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.4361 | 0.4186 | 0.1961 | 0.6759 | 0.4293 | 0.4951 | 13 | PASS |  | 0.2355 | same_account_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| M | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.4293 | 0.341 | 0.1746 | 0.7063 | 0.4247 | 0.5226 | 13 | PASS | -0.006868 | 0.2286 | first_evaluation | FAIL | 不通过（c、size(LEGACY_EDIT5)） | 不通过（c、size(LEGACY_EDIT5)） | False |
| M | M_mean3_v2 | RP3 | 0.25 | 5 | 0.1187 | 0.07533 | 0.02214 | 0.2133 | 0.1187 | 0.1295 | 11 | PASS | -0.3174 | -0.08192 | first_evaluation | FAIL | 不通过（d、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | False |
| M | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.3756 | 0.314 | 0.1205 | 0.6218 | 0.3727 | 0.4703 | 11 | FAIL | -0.06055 | 0.175 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | False |
| M | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2247 | 0.172 | 0.03871 | 0.4167 | 0.2218 | 0.2742 | 12 | PASS | 0.008202 | 0.1202 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.1566 | 0.1241 | -0.05568 | 0.3851 | 0.1422 | 0.2329 | 11 | PASS | -0.05994 | 0.0521 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| M | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.2165 | 0.2578 | -0.005673 | 0.4458 | 0.2137 | 0.2696 | 12 | PASS |  | 0.112 | same_account_exposed | FAIL | 不通过（c、f、size(LEGACY_EDIT5)） | 不通过（c、f、size(LEGACY_EDIT5)） | False |
| M | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.1976 | 0.1692 | -0.05168 | 0.4646 | 0.1866 | 0.2783 | 11 | PASS | -0.0189 | 0.09313 | first_evaluation | FAIL | 不通过（c、d、size(LEGACY_EDIT5)） | 不通过（c、d、size(LEGACY_EDIT5)） | False |
| M | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.01163 | 0.01061 | -0.06285 | 0.08551 | 0.01163 | 0.01876 | 8 | FAIL | -0.2049 | -0.09283 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| M | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.1803 | 0.173 | -0.05175 | 0.4166 | 0.1802 | 0.2702 | 11 | PASS | -0.03617 | 0.07587 | first_evaluation | FAIL | 不通过（c、d、f、size(LEGACY_EDIT5)） | 不通过（c、d、f、size(LEGACY_EDIT5)） | False |
| M | M_union3_v2 | INC1 | 0.25 | 5 | 0.2595 | 0.2783 | 0.06196 | 0.4666 | 0.1492 | 0.1901 | 12 | PASS | -0.1385 | 0.1698 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.2833 | 0.2853 | 0.06601 | 0.4978 | 0.1202 | 0.1746 | 14 | MC_UNRESOLVED | -0.1147 | 0.1936 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| M | M_union3_v2 | NATIVE | 0.25 | 5 | 0.398 | 0.2775 | 0.1808 | 0.615 | 0.2507 | 0.3111 | 13 | PASS |  | 0.3084 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.3104 | 0.3448 | 0.04982 | 0.5717 | 0.1293 | 0.1844 | 12 | PASS | -0.08756 | 0.2208 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| M | M_union3_v2 | RP3 | 0.25 | 5 | 0.04687 | 0.05325 | -0.01152 | 0.101 | 0.04687 | 0.03928 | 10 | FAIL | -0.3511 | -0.04277 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| M | M_union3_v2 | SZL5 | 0.25 | 5 | 0.3308 | 0.2388 | 0.1182 | 0.5691 | 0.1725 | 0.2336 | 14 | PASS | -0.06722 | 0.2411 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| M | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2577 | 0.287 | 0.07197 | 0.4523 | 0.1482 | 0.1885 | 11 | PASS | -0.1191 | 0.1856 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| M | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3035 | 0.3393 | 0.1005 | 0.5104 | 0.1428 | 0.1913 | 15 | MC_UNRESOLVED | -0.07329 | 0.2315 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| M | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3768 | 0.3079 | 0.1588 | 0.5886 | 0.2397 | 0.2903 | 14 | PASS |  | 0.3048 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.3473 | 0.4264 | 0.09834 | 0.5926 | 0.1688 | 0.2166 | 14 | PASS | -0.02949 | 0.2753 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| M | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.05518 | 0.04137 | 0.001627 | 0.1068 | 0.05518 | 0.04858 | 12 | FAIL | -0.3216 | -0.01687 | first_evaluation | PASS | 不通过（正向门槛、e随机） | 不通过（正向门槛、e随机） | False |
| M | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.34 | 0.3027 | 0.1414 | 0.5592 | 0.186 | 0.2437 | 14 | PASS | -0.03683 | 0.2679 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| Q | A4b | INC1 | 0.25 | 5 | 0.1974 | 0.1573 | -0.03012 | 0.4159 | 0.2034 | 0.2552 | 11 | FAIL | -0.1657 | -0.06739 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | False |
| Q | A4b | INC1_HG10 | 0.25 | 5 | 0.2725 | 0.1948 | -0.02394 | 0.5488 | 0.2762 | 0.3561 | 11 | FAIL | -0.09065 | 0.007678 | first_evaluation | FAIL | 不通过（c、d、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、e随机、size(LEGACY_EDIT5)） | False |
| Q | A4b | NATIVE | 0.25 | 5 | 0.3631 | 0.2695 | 0.1178 | 0.6074 | 0.3678 | 0.4301 | 12 | PASS |  | 0.09833 | related_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| Q | A4b | NATIVE_HG10 | 0.25 | 5 | 0.5279 | 0.4851 | 0.2413 | 0.8061 | 0.5331 | 0.6251 | 14 | PASS | 0.1648 | 0.2631 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| Q | A4b | RP3 | 0.25 | 5 | 0.165 | 0.2136 | 0.05828 | 0.2607 | 0.165 | 0.1784 | 13 | PASS | -0.1981 | -0.09981 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| Q | A4b | SZL5 | 0.25 | 5 | 0.1683 | 0.1394 | -0.05735 | 0.3757 | 0.1837 | 0.244 | 11 | FAIL | -0.1948 | -0.0965 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | False |
| Q | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1879 | 0.1204 | -0.02715 | 0.3904 | 0.1622 | 0.2257 | 11 | FAIL | -0.1758 | -0.09839 | first_evaluation | FAIL | 不通过（d、e随机、size(LEGACY_EDIT5)） | 不通过（d、e随机、size(LEGACY_EDIT5)） | False |
| Q | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2386 | 0.1158 | -0.03909 | 0.489 | 0.2139 | 0.2883 | 12 | FAIL | -0.1251 | -0.04769 | first_evaluation | FAIL | 不通过（e随机、size(LEGACY_EDIT5)） | 不通过（e随机、size(LEGACY_EDIT5)） | False |
| Q | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.3638 | 0.2874 | 0.1376 | 0.5732 | 0.346 | 0.4006 | 12 | PASS |  | 0.07746 | same_account_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| Q | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.5176 | 0.5256 | 0.2634 | 0.7718 | 0.4858 | 0.5728 | 13 | PASS | 0.1538 | 0.2313 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| Q | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.1344 | 0.1481 | 0.04428 | 0.2225 | 0.1344 | 0.1432 | 11 | PASS | -0.2294 | -0.152 | first_evaluation | FAIL | 不通过（d、size(LEGACY_EDIT5)） | 不通过（d、size(LEGACY_EDIT5)） | False |
| Q | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.1393 | 0.08961 | -0.06583 | 0.332 | 0.1252 | 0.1917 | 10 | FAIL | -0.2244 | -0.147 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| Q | M_mean3_v2 | INC1 | 0.25 | 5 | 0.2682 | 0.2419 | 0.06332 | 0.4805 | 0.2709 | 0.4345 | 13 | PASS | -0.04979 | 0.06757 | first_evaluation | FAIL | 不通过（c、size(LEGACY_EDIT5)） | 不通过（c、size(LEGACY_EDIT5)） | False |
| Q | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.2153 | 0.2007 | -0.05116 | 0.4861 | 0.228 | 0.4097 | 11 | PASS | -0.1026 | 0.01471 | first_evaluation | FAIL | 不通过（c、d、size(LEGACY_EDIT5)） | 不通过（c、d、size(LEGACY_EDIT5)） | False |
| Q | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.318 | 0.1509 | 0.06691 | 0.5805 | 0.3278 | 0.5171 | 10 | PASS |  | 0.1174 | related_exposed | FAIL | 不通过（c、d、f、size(LEGACY_EDIT5)） | 不通过（c、d、f、size(LEGACY_EDIT5)） | False |
| Q | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.2922 | 0.1053 | -0.0002321 | 0.5957 | 0.3124 | 0.5217 | 9 | PASS | -0.02582 | 0.09154 | first_evaluation | FAIL | 不通过（c、d、size(LEGACY_EDIT5)） | 不通过（c、d、size(LEGACY_EDIT5)） | False |
| Q | M_mean3_v2 | RP3 | 0.25 | 5 | 0.157 | 0.1219 | 0.02507 | 0.2841 | 0.157 | 0.2143 | 12 | PASS | -0.161 | -0.04359 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| Q | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.3539 | 0.2182 | 0.08788 | 0.6125 | 0.361 | 0.5822 | 13 | PASS | 0.03593 | 0.1533 | first_evaluation | FAIL | 不通过（c、size(LEGACY_EDIT5)） | 不通过（c、size(LEGACY_EDIT5)） | False |
| Q | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | -0.07264 | -0.03039 | -0.2838 | 0.1367 | -0.07703 | 0.07222 | 7 | FAIL | 0.02254 | -0.1771 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| Q | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.0359 | 0.06857 | -0.2929 | 0.2169 | -0.03624 | 0.1291 | 7 | PASS | 0.05927 | -0.1404 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | False |
| Q | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | -0.09518 | -0.171 | -0.3332 | 0.1615 | -0.09628 | 0.08211 | 5 | PASS |  | -0.1996 | related_exposed | FAIL | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | False |
| Q | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | -0.05299 | -0.06691 | -0.332 | 0.234 | -0.051 | 0.1477 | 6 | PASS | 0.04218 | -0.1575 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | False |
| Q | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | -0.009236 | -0.005467 | -0.1218 | 0.1075 | -0.009236 | 0.03193 | 7 | FAIL | 0.08594 | -0.1137 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| Q | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.1288 | -0.1459 | -0.3646 | 0.119 | -0.1377 | 0.07605 | 6 | PASS | -0.03362 | -0.2333 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | False |
| Q | M_union3_v2 | INC1 | 0.25 | 5 | 0.1757 | 0.04392 | -0.003759 | 0.3493 | 0.01306 | 0.1249 | 10 | FAIL | -0.05185 | 0.08609 | first_evaluation | FAIL | 不通过（d、e随机、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、e资本、e随机、size(LEGACY_EDIT5)） | False |
| Q | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.3813 | 0.4576 | 0.1571 | 0.5919 | 0.1495 | 0.2919 | 13 | PASS | 0.1537 | 0.2917 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| Q | M_union3_v2 | NATIVE | 0.25 | 5 | 0.2276 | 0.265 | 0.02649 | 0.435 | 0.004184 | 0.1169 | 10 | PASS |  | 0.1379 | related_exposed | FAIL | 不通过（d、f、size(LEGACY_EDIT5)） | 不通过（d、f、size(LEGACY_EDIT5)） | False |
| Q | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.5354 | 0.6264 | 0.2958 | 0.77 | 0.2134 | 0.3778 | 14 | PASS | 0.3078 | 0.4458 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| Q | M_union3_v2 | RP3 | 0.25 | 5 | 0.01474 | 0.0004187 | -0.03288 | 0.06085 | 0.01474 | 0.01866 | 12 | MC_UNRESOLVED | -0.2128 | -0.0749 | first_evaluation | FAIL | 不通过（正向门槛、size(LEGACY_EDIT5)） | 不通过（正向门槛、size(LEGACY_EDIT5)） | False |
| Q | M_union3_v2 | SZL5 | 0.25 | 5 | 0.1543 | 0.07127 | -0.06497 | 0.3644 | -0.1164 | 0.04941 | 8 | MC_UNRESOLVED | -0.0733 | 0.06464 | first_evaluation | FAIL | 不通过（c、d、f、e资本、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e资本、size(LEGACY_EDIT5)） | False |
| Q | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.1689 | 0.06355 | -0.01053 | 0.3354 | -0.005782 | 0.1099 | 8 | FAIL | -0.08217 | 0.0968 | first_evaluation | FAIL | 不通过（d、e资本、e随机、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、e资本、e随机、size(LEGACY_EDIT5)） | False |
| Q | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3636 | 0.4359 | 0.1469 | 0.5628 | 0.1242 | 0.2628 | 11 | PASS | 0.1126 | 0.2916 | first_evaluation | FAIL | 不通过（d、size(LEGACY_EDIT5)） | 不通过（d、size(LEGACY_EDIT5)） | False |
| Q | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.251 | 0.3142 | 0.05259 | 0.453 | 0.01981 | 0.1315 | 12 | PASS |  | 0.179 | related_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| Q | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.5357 | 0.6555 | 0.3049 | 0.762 | 0.2051 | 0.3633 | 13 | PASS | 0.2847 | 0.4637 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| Q | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.01083 | 0.01371 | -0.03572 | 0.05664 | 0.01083 | 0.01423 | 11 | PASS | -0.2402 | -0.06122 | first_evaluation | FAIL | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、size(LEGACY_EDIT5)） | False |
| Q | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.2018 | 0.1657 | 0.002061 | 0.4021 | -0.07678 | 0.08688 | 9 | PASS | -0.04917 | 0.1298 | first_evaluation | FAIL | 不通过（c、d、f、e资本、size(LEGACY_EDIT5)） | 不通过（c、d、f、e资本、size(LEGACY_EDIT5)） | False |
| S | A4b | INC1 | 0.25 | 5 | 0.08125 | 0.03575 | -0.182 | 0.316 | 0.08413 | 0.1401 | 9 | FAIL | -0.3184 | -0.1836 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| S | A4b | INC1_HG10 | 0.25 | 5 | 0.3096 | 0.2318 | 0.01812 | 0.5834 | 0.3166 | 0.3913 | 11 | FAIL | -0.09011 | 0.04475 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | False |
| S | A4b | NATIVE | 0.25 | 5 | 0.3997 | 0.3777 | 0.1498 | 0.6517 | 0.4052 | 0.4669 | 12 | PASS |  | 0.1349 | same_account_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| S | A4b | NATIVE_HG10 | 0.25 | 5 | 0.4139 | 0.3352 | 0.1192 | 0.7094 | 0.4235 | 0.5146 | 12 | PASS | 0.0142 | 0.1491 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| S | A4b | RP3 | 0.25 | 5 | 0.1341 | 0.132 | 0.03198 | 0.23 | 0.1341 | 0.1476 | 10 | PASS | -0.2656 | -0.1307 | first_evaluation | FAIL | 不通过（d、size(LEGACY_EDIT5)） | 不通过（d、size(LEGACY_EDIT5)） | False |
| S | A4b | SZL5 | 0.25 | 5 | 0.07851 | 0.08158 | -0.1723 | 0.3188 | 0.09533 | 0.1514 | 10 | FAIL | -0.3212 | -0.1863 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| S | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1428 | 0.118 | -0.09349 | 0.3519 | 0.1123 | 0.1847 | 10 | FAIL | -0.2816 | -0.1435 | first_evaluation | FAIL | 不通过（d、e随机、size(LEGACY_EDIT5)） | 不通过（d、e随机、size(LEGACY_EDIT5)） | False |
| S | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2624 | 0.1307 | -0.00494 | 0.513 | 0.239 | 0.3167 | 11 | FAIL | -0.162 | -0.02388 | first_evaluation | FAIL | 不通过（d、e随机、size(LEGACY_EDIT5)） | 不通过（d、e随机、size(LEGACY_EDIT5)） | False |
| S | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.4244 | 0.3578 | 0.2037 | 0.6299 | 0.4003 | 0.4661 | 13 | PASS |  | 0.1381 | same_account_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| S | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.4176 | 0.4411 | 0.1467 | 0.69 | 0.4005 | 0.4798 | 12 | PASS | -0.00678 | 0.1313 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| S | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.1102 | 0.1287 | 0.01884 | 0.197 | 0.1102 | 0.1185 | 12 | PASS | -0.3142 | -0.1761 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| S | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.1414 | 0.08738 | -0.0766 | 0.3438 | 0.1183 | 0.1962 | 9 | FAIL | -0.283 | -0.1449 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| S | M_mean3_v2 | INC1 | 0.25 | 5 | 0.2785 | 0.1308 | 0.05481 | 0.5142 | 0.2835 | 0.4437 | 12 | MC_UNRESOLVED | -0.06625 | 0.07789 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| S | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.1936 | 0.1127 | -0.08192 | 0.4596 | 0.2019 | 0.3867 | 10 | PASS | -0.1512 | -0.007023 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| S | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.3448 | 0.2127 | 0.08606 | 0.6127 | 0.3502 | 0.5437 | 12 | PASS |  | 0.1441 | same_account_exposed | FAIL | 不通过（c、size(LEGACY_EDIT5)） | 不通过（c、size(LEGACY_EDIT5)） | False |
| S | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.313 | 0.1216 | 0.01307 | 0.6066 | 0.3267 | 0.5408 | 9 | PASS | -0.03177 | 0.1124 | first_evaluation | FAIL | 不通过（c、d、size(LEGACY_EDIT5)） | 不通过（c、d、size(LEGACY_EDIT5)） | False |
| S | M_mean3_v2 | RP3 | 0.25 | 5 | 0.2204 | 0.2108 | 0.1022 | 0.3388 | 0.2204 | 0.2763 | 13 | PASS | -0.1243 | 0.01982 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.1754 | 0.03933 | -0.09069 | 0.4579 | 0.1843 | 0.4015 | 10 | FAIL | -0.1693 | -0.0252 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| S | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | -0.03874 | -0.05733 | -0.2481 | 0.1745 | -0.04475 | 0.1062 | 6 | FAIL | -0.03297 | -0.1432 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| S | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.09065 | -0.009104 | -0.3398 | 0.1548 | -0.1008 | 0.07603 | 6 | FAIL | -0.08487 | -0.1951 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e资本、e随机、size(LEGACY_EDIT5)） | False |
| S | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | -0.005773 | -0.06165 | -0.2485 | 0.247 | -0.00439 | 0.173 | 8 | PASS |  | -0.1102 | same_account_exposed | FAIL | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | False |
| S | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | -0.08456 | -0.1577 | -0.3562 | 0.2011 | -0.08925 | 0.1173 | 7 | PASS | -0.07878 | -0.189 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、size(LEGACY_EDIT5)） | False |
| S | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.06107 | 0.03759 | -0.04222 | 0.1648 | 0.06107 | 0.102 | 9 | PASS | 0.06684 | -0.04339 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| S | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.231 | -0.2775 | -0.4855 | 0.03084 | -0.2383 | -0.02566 | 7 | FAIL | -0.2252 | -0.3355 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| S | M_union3_v2 | INC1 | 0.25 | 5 | 0.1842 | 0.162 | -0.007725 | 0.3661 | 0.03547 | 0.1348 | 12 | MC_UNRESOLVED | -0.1336 | 0.09456 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（e资本、size(LEGACY_EDIT5)） | False |
| S | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.3984 | 0.3503 | 0.1868 | 0.6027 | 0.148 | 0.3032 | 15 | FAIL | 0.08065 | 0.3088 | first_evaluation | FAIL | 不通过（e随机、size(LEGACY_EDIT5)） | 不通过（e随机、size(LEGACY_EDIT5)） | False |
| S | M_union3_v2 | NATIVE | 0.25 | 5 | 0.3178 | 0.271 | 0.1204 | 0.5191 | 0.06444 | 0.2039 | 13 | PASS |  | 0.2282 | same_account_exposed | FAIL | 不通过（f、size(LEGACY_EDIT5)） | 不通过（f、size(LEGACY_EDIT5)） | False |
| S | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.4324 | 0.4134 | 0.2008 | 0.6539 | 0.09695 | 0.2664 | 14 | PASS | 0.1146 | 0.3428 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| S | M_union3_v2 | RP3 | 0.25 | 5 | 0.01587 | 0.004026 | -0.03517 | 0.06561 | 0.01587 | 0.01965 | 11 | FAIL | -0.3019 | -0.07376 | first_evaluation | FAIL | 不通过（d、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| S | M_union3_v2 | SZL5 | 0.25 | 5 | 0.1094 | 0.03241 | -0.1109 | 0.3209 | -0.1559 | -0.009295 | 9 | FAIL | -0.2084 | 0.01974 | first_evaluation | FAIL | 不通过（c、d、f、e资本、e随机、size(LEGACY_EDIT5)） | 不通过（c、d、f、正向门槛、e资本、e随机、size(LEGACY_EDIT5)） | False |
| S | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2101 | 0.2426 | 0.02444 | 0.3802 | 0.04257 | 0.1535 | 13 | PASS | -0.1386 | 0.138 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| S | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3916 | 0.4481 | 0.1765 | 0.5906 | 0.1351 | 0.2837 | 12 | PASS | 0.04289 | 0.3195 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| S | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3487 | 0.3481 | 0.1639 | 0.5396 | 0.08027 | 0.2279 | 12 | PASS |  | 0.2767 | same_account_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| S | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.44 | 0.49 | 0.2019 | 0.6616 | 0.09191 | 0.2616 | 14 | PASS | 0.09127 | 0.3679 | first_evaluation | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| S | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.003435 | -0.00127 | -0.04276 | 0.05014 | 0.003435 | 0.006165 | 9 | FAIL | -0.3453 | -0.06861 | first_evaluation | FAIL | 不通过（d、正向门槛、e随机、size(LEGACY_EDIT5)） | 不通过（d、正向门槛、e随机、size(LEGACY_EDIT5)） | False |
| S | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.1666 | 0.1094 | -0.04141 | 0.3695 | -0.1125 | 0.04038 | 11 | PASS | -0.1821 | 0.09452 | first_evaluation | FAIL | 不通过（d、f、e资本、size(LEGACY_EDIT5)） | 不通过（d、f、e资本、size(LEGACY_EDIT5)） | False |
| SM | A4b | NATIVE | 0.25 | 5 | 0.2996 | 0.2374 | 0.06651 | 0.5287 | 0.3078 | 0.3298 | 11 | MC_UNRESOLVED |  | 0.03475 | same_account_exposed | FAIL | 不通过（c、d、f、size(LEGACY_EDIT5)） | 不通过（c、d、f、size(LEGACY_EDIT5)） | False |
| SM | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.2566 | 0.1949 | 0.05383 | 0.4491 | 0.2426 | 0.2695 | 13 | PASS |  | -0.02975 | same_account_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| SM | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.4969 | 0.4043 | 0.2813 | 0.7331 | 0.4962 | 0.6275 | 15 | PASS |  | 0.2963 | same_account_exposed | FAIL | 不通过（c、size(LEGACY_EDIT5)） | 不通过（c、size(LEGACY_EDIT5)） | False |
| SM | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.1814 | 0.1383 | -0.03136 | 0.4078 | 0.1738 | 0.2958 | 13 | PASS |  | 0.07694 | same_account_exposed | FAIL | 不通过（c、f、size(LEGACY_EDIT5)） | 不通过（c、f、size(LEGACY_EDIT5)） | False |
| SM | M_union3_v2 | NATIVE | 0.25 | 5 | 0.3699 | 0.3221 | 0.1824 | 0.5623 | 0.1812 | 0.2567 | 13 | PASS |  | 0.2802 | same_account_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |
| SM | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3634 | 0.3373 | 0.1836 | 0.5513 | 0.1663 | 0.2469 | 12 | PASS |  | 0.2914 | same_account_exposed | FAIL | 不通过（size(LEGACY_EDIT5)） | 不通过（size(LEGACY_EDIT5)） | False |


## profile PROPOSED_PORT3_T

> 表头：主体=144 主展示 + C1_hi + SM 锚｜算子=见列｜分母=四段有效配对日（FULL = n 加权；G4 = 段中位）｜基准=同 H 原父（8bp）｜子集=primary144 | c1_hi | sm_anchor｜单位=年化百分点 / 判词｜日期=2010-01-04..2026-03-27（四段；2026 partial）｜H=H 见列｜成本模型=源 8bp（f：A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（e 资本：MATCH-CAP）｜exposure=见 evidence_exposure 列｜query_id=E6K-P3-POL-PROPOSEDPORT3T


| meas | mother | op | alpha | H | FULL | G4 | ci_L20_lo | ci_L20_hi | FULL_sc | FULL_imp | years_pos | e_rand | FULL_vs_native | FULL_vs_nativeC1 | evidence_exposure | size_PROPOSED_PORT3_T | policy_PROPOSED_PORT3_T_FULL | policy_PROPOSED_PORT3_T_G4 | POLICY_INTERPRETATION_PENDING_PROPOSED_PORT3_T |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | A4b | INC1 | 0.25 | 5 | 0.1993 | 0.1666 | 0.03081 | 0.3619 | 0.2035 | 0.2056 | 13 | MC_UNRESOLVED | -0.06553 | -0.06553 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| C1 | A4b | INC1_HG10 | 0.25 | 5 | 0.2376 | 0.3176 | 0.01428 | 0.453 | 0.2399 | 0.2533 | 11 | FAIL | -0.02717 | -0.02717 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| C1 | A4b | NATIVE | 0.25 | 5 | 0.2648 | 0.311 | 0.07639 | 0.4442 | 0.2649 | 0.2738 | 13 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b | NATIVE | 0.5 | 10 | 0.4742 | 0.5273 | 0.19 | 0.755 | 0.4401 | 0.4511 | 14 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b | NATIVE | 0.5 | 20 | 0.3358 | 0.3565 | 0.1394 | 0.5252 | 0.3152 | 0.3247 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b | NATIVE_HG10 | 0.25 | 5 | 0.2929 | 0.2275 | 0.04494 | 0.5338 | 0.2869 | 0.309 | 10 | PASS | 0.02809 | 0.02809 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| C1 | A4b | RP3 | 0.25 | 5 | 0.02682 | 0.01826 | -0.04199 | 0.0943 | 0.02682 | 0.02785 | 11 | PASS | -0.238 | -0.238 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| C1 | A4b | SZL5 | 0.25 | 5 | 0.1258 | 0.03719 | -0.0705 | 0.3107 | 0.1328 | 0.1327 | 10 | PASS | -0.139 | -0.139 | first_evaluation | PASS | 不通过（d） | 不通过（d、正向门槛） | False |
| C1 | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1824 | 0.2094 | 0.03225 | 0.32 | 0.1639 | 0.1768 | 12 | FAIL | -0.1039 | -0.1039 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| C1 | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2232 | 0.3032 | 0.02851 | 0.4113 | 0.2118 | 0.2213 | 10 | FAIL | -0.06307 | -0.06307 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| C1 | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.2863 | 0.3224 | 0.1182 | 0.4473 | 0.2728 | 0.2809 | 14 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b_CVRv5 | NATIVE | 0.5 | 10 | 0.4206 | 0.3958 | 0.1749 | 0.6575 | 0.4056 | 0.3929 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b_CVRv5 | NATIVE | 0.5 | 20 | 0.2857 | 0.2776 | 0.1175 | 0.456 | 0.2734 | 0.2736 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.2387 | 0.2548 | 0.02666 | 0.4464 | 0.2218 | 0.2312 | 11 | PASS | -0.04761 | -0.04761 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| C1 | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.03286 | 0.03379 | -0.02538 | 0.0921 | 0.03286 | 0.0335 | 11 | PASS | -0.2534 | -0.2534 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| C1 | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.124 | 0.07449 | -0.04594 | 0.2898 | 0.1211 | 0.1234 | 11 | FAIL | -0.1623 | -0.1623 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_mean3_v2 | INC1 | 0.25 | 5 | 0.1792 | 0.0971 | 0.04069 | 0.319 | 0.1741 | 0.1999 | 13 | FAIL | -0.02146 | -0.02146 | first_evaluation | PASS | 不通过（e随机） | 不通过（正向门槛、e随机） | False |
| C1 | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.06166 | 0.008405 | -0.1416 | 0.2776 | 0.05662 | 0.1124 | 11 | FAIL | -0.139 | -0.139 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.2006 | 0.1498 | 0.04456 | 0.3478 | 0.1946 | 0.2267 | 13 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.1979 | 0.111 | -0.03353 | 0.4343 | 0.1943 | 0.254 | 12 | FAIL | -0.002698 | -0.002698 | first_evaluation | PASS | 不通过（c、e随机） | 不通过（c、e随机） | False |
| C1 | M_mean3_v2 | RP3 | 0.25 | 5 | 0.07358 | 0.06543 | 0.02002 | 0.1256 | 0.07358 | 0.07844 | 9 | FAIL | -0.127 | -0.127 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| C1 | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.1672 | 0.1965 | -0.03337 | 0.3789 | 0.1737 | 0.2275 | 10 | FAIL | -0.03339 | -0.03339 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| C1 | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.08837 | 0.07339 | -0.0385 | 0.2151 | 0.0802 | 0.1053 | 12 | FAIL | -0.01609 | -0.01609 | first_evaluation | PASS | 不通过（正向门槛、e随机） | 不通过（正向门槛、e随机） | False |
| C1 | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.1125 | -0.1064 | -0.3101 | 0.08312 | -0.1186 | -0.0699 | 7 | FAIL | -0.217 | -0.217 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.1045 | 0.09114 | -0.03507 | 0.2393 | 0.09502 | 0.1255 | 12 | PASS |  |  | same_account_exposed | PASS | 通过 | 不通过（正向门槛） | True |
| C1 | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.00137 | -0.009876 | -0.2139 | 0.2206 | -0.009498 | 0.04625 | 10 | PASS | -0.1031 | -0.1031 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e资本） | 不通过（c、d、f、正向门槛） | False |
| C1 | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.03224 | 0.03028 | -0.0182 | 0.08394 | 0.03224 | 0.03556 | 8 | PASS | -0.07222 | -0.07222 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| C1 | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.02625 | 0.02404 | -0.1984 | 0.1458 | -0.02549 | 0.03063 | 9 | PASS | -0.1307 | -0.1307 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| C1 | M_union3_v2 | INC1 | 0.25 | 5 | 0.03555 | 0.07215 | -0.1007 | 0.173 | 0.0064 | -0.004975 | 11 | FAIL | -0.05409 | -0.05409 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.1696 | 0.1773 | -0.01546 | 0.3613 | 0.06871 | 0.09116 | 12 | PASS | 0.07999 | 0.07999 | first_evaluation | PASS | 不通过（f） | 不通过（f） | False |
| C1 | M_union3_v2 | NATIVE | 0.25 | 5 | 0.08964 | 0.09268 | -0.06266 | 0.2459 | 0.04254 | 0.03047 | 12 | PASS |  |  | same_account_exposed | PASS | 不通过（正向门槛） | 不通过（正向门槛） | False |
| C1 | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.1652 | 0.1857 | -0.0345 | 0.3763 | 0.05509 | 0.06316 | 12 | PASS | 0.07554 | 0.07554 | first_evaluation | PASS | 不通过（f） | 不通过（f） | False |
| C1 | M_union3_v2 | RP3 | 0.25 | 5 | 0.01305 | 0.004054 | -0.03189 | 0.05926 | 0.01305 | 0.01005 | 11 | FAIL | -0.07659 | -0.07659 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| C1 | M_union3_v2 | SZL5 | 0.25 | 5 | -0.05162 | -0.05403 | -0.2646 | 0.16 | -0.1339 | -0.1258 | 8 | FAIL | -0.1413 | -0.1413 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.01715 | 0.04369 | -0.1179 | 0.1548 | -0.009748 | -0.02245 | 10 | FAIL | -0.05489 | -0.05489 | first_evaluation | PASS | 不通过（d、f、正向门槛、e资本、e随机） | 不通过（d、f、正向门槛、e随机） | False |
| C1 | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.1555 | 0.1447 | -0.02468 | 0.3374 | 0.06176 | 0.0744 | 12 | PASS | 0.08346 | 0.08346 | first_evaluation | PASS | 通过 | 通过 | False |
| C1 | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.07205 | 0.08064 | -0.07399 | 0.2168 | 0.03263 | 0.01425 | 10 | PASS |  |  | same_account_exposed | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| C1 | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.1526 | 0.1473 | -0.04438 | 0.3466 | 0.04796 | 0.0497 | 12 | PASS | 0.08059 | 0.08059 | first_evaluation | PASS | 不通过（f） | 不通过（f） | False |
| C1 | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.00119 | -0.00744 | -0.03962 | 0.04427 | 0.00119 | -0.0009616 | 9 | FAIL | -0.07086 | -0.07086 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| C1 | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.02526 | 0.01453 | -0.2121 | 0.1562 | -0.09905 | -0.09544 | 9 | FAIL | -0.0973 | -0.0973 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e资本、e随机） | False |
| M | A4b | INC1 | 0.25 | 5 | 0.1232 | 0.04958 | -0.07289 | 0.3303 | 0.1384 | 0.1445 | 11 | FAIL | -0.2154 | -0.1416 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、正向门槛、e随机） | False |
| M | A4b | INC1_HG10 | 0.25 | 5 | 0.1888 | 0.1395 | -0.05864 | 0.4124 | 0.1945 | 0.2289 | 11 | FAIL | -0.1499 | -0.07604 | first_evaluation | PASS | 不通过（c、d、e随机） | 不通过（c、d、e随机） | False |
| M | A4b | NATIVE | 0.25 | 5 | 0.3386 | 0.2736 | 0.1176 | 0.5664 | 0.3462 | 0.3521 | 14 | PASS |  | 0.07382 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | A4b | NATIVE_HG10 | 0.25 | 5 | 0.3479 | 0.2125 | 0.113 | 0.5916 | 0.3579 | 0.3797 | 12 | PASS | 0.009267 | 0.08309 | first_evaluation | PASS | 通过 | 通过 | False |
| M | A4b | RP3 | 0.25 | 5 | 0.0804 | 0.1039 | 0.001027 | 0.1645 | 0.0804 | 0.08056 | 10 | PASS | -0.2582 | -0.1844 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d） | False |
| M | A4b | SZL5 | 0.25 | 5 | 0.2483 | 0.1122 | 0.03211 | 0.4758 | 0.2632 | 0.2705 | 12 | FAIL | -0.09035 | -0.01653 | first_evaluation | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False |
| M | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1118 | 0.1358 | -0.06575 | 0.2965 | 0.1217 | 0.1257 | 12 | FAIL | -0.2282 | -0.1745 | first_evaluation | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False |
| M | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2176 | 0.143 | 0.004276 | 0.4178 | 0.2152 | 0.2404 | 12 | FAIL | -0.1224 | -0.06868 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| M | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.34 | 0.2745 | 0.1475 | 0.5325 | 0.3456 | 0.3408 | 15 | PASS |  | 0.0537 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.371 | 0.3839 | 0.1612 | 0.5794 | 0.3812 | 0.3836 | 12 | PASS | 0.03103 | 0.08473 | first_evaluation | PASS | 通过 | 通过 | False |
| M | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.06943 | 0.08925 | 0.000882 | 0.1387 | 0.06943 | 0.06759 | 10 | PASS | -0.2706 | -0.2169 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| M | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.2398 | 0.1384 | 0.03711 | 0.4456 | 0.2481 | 0.253 | 13 | PASS | -0.1002 | -0.04655 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_mean3_v2 | INC1 | 0.25 | 5 | 0.3977 | 0.3379 | 0.1925 | 0.6053 | 0.3944 | 0.4544 | 14 | PASS | -0.03838 | 0.1971 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.3382 | 0.2332 | 0.1108 | 0.5797 | 0.3284 | 0.4276 | 13 | FAIL | -0.09796 | 0.1376 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| M | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.4361 | 0.4186 | 0.1961 | 0.6759 | 0.4293 | 0.4951 | 13 | PASS |  | 0.2355 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.4293 | 0.341 | 0.1746 | 0.7063 | 0.4247 | 0.5226 | 13 | PASS | -0.006868 | 0.2286 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| M | M_mean3_v2 | RP3 | 0.25 | 5 | 0.1187 | 0.07533 | 0.02214 | 0.2133 | 0.1187 | 0.1295 | 11 | PASS | -0.3174 | -0.08192 | first_evaluation | PASS | 不通过（d） | 不通过（d、正向门槛） | False |
| M | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.3756 | 0.314 | 0.1205 | 0.6218 | 0.3727 | 0.4703 | 11 | FAIL | -0.06055 | 0.175 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| M | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2247 | 0.172 | 0.03871 | 0.4167 | 0.2218 | 0.2742 | 12 | PASS | 0.008202 | 0.1202 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.1566 | 0.1241 | -0.05568 | 0.3851 | 0.1422 | 0.2329 | 11 | PASS | -0.05994 | 0.0521 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| M | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.2165 | 0.2578 | -0.005673 | 0.4458 | 0.2137 | 0.2696 | 12 | PASS |  | 0.112 | same_account_exposed | PASS | 不通过（c、f） | 不通过（c、f） | False |
| M | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.1976 | 0.1692 | -0.05168 | 0.4646 | 0.1866 | 0.2783 | 11 | PASS | -0.0189 | 0.09313 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| M | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.01163 | 0.01061 | -0.06285 | 0.08551 | 0.01163 | 0.01876 | 8 | FAIL | -0.2049 | -0.09283 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| M | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.1803 | 0.173 | -0.05175 | 0.4166 | 0.1802 | 0.2702 | 11 | PASS | -0.03617 | 0.07587 | first_evaluation | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False |
| M | M_union3_v2 | INC1 | 0.25 | 5 | 0.2595 | 0.2783 | 0.06196 | 0.4666 | 0.1492 | 0.1901 | 12 | PASS | -0.1385 | 0.1698 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.2833 | 0.2853 | 0.06601 | 0.4978 | 0.1202 | 0.1746 | 14 | MC_UNRESOLVED | -0.1147 | 0.1936 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| M | M_union3_v2 | NATIVE | 0.25 | 5 | 0.398 | 0.2775 | 0.1808 | 0.615 | 0.2507 | 0.3111 | 13 | PASS |  | 0.3084 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.3104 | 0.3448 | 0.04982 | 0.5717 | 0.1293 | 0.1844 | 12 | PASS | -0.08756 | 0.2208 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2 | RP3 | 0.25 | 5 | 0.04687 | 0.05325 | -0.01152 | 0.101 | 0.04687 | 0.03928 | 10 | FAIL | -0.3511 | -0.04277 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| M | M_union3_v2 | SZL5 | 0.25 | 5 | 0.3308 | 0.2388 | 0.1182 | 0.5691 | 0.1725 | 0.2336 | 14 | PASS | -0.06722 | 0.2411 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2577 | 0.287 | 0.07197 | 0.4523 | 0.1482 | 0.1885 | 11 | PASS | -0.1191 | 0.1856 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| M | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3035 | 0.3393 | 0.1005 | 0.5104 | 0.1428 | 0.1913 | 15 | MC_UNRESOLVED | -0.07329 | 0.2315 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| M | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3768 | 0.3079 | 0.1588 | 0.5886 | 0.2397 | 0.2903 | 14 | PASS |  | 0.3048 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.3473 | 0.4264 | 0.09834 | 0.5926 | 0.1688 | 0.2166 | 14 | PASS | -0.02949 | 0.2753 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.05518 | 0.04137 | 0.001627 | 0.1068 | 0.05518 | 0.04858 | 12 | FAIL | -0.3216 | -0.01687 | first_evaluation | PASS | 不通过（正向门槛、e随机） | 不通过（正向门槛、e随机） | False |
| M | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.34 | 0.3027 | 0.1414 | 0.5592 | 0.186 | 0.2437 | 14 | PASS | -0.03683 | 0.2679 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | A4b | INC1 | 0.25 | 5 | 0.1974 | 0.1573 | -0.03012 | 0.4159 | 0.2034 | 0.2552 | 11 | FAIL | -0.1657 | -0.06739 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| Q | A4b | INC1_HG10 | 0.25 | 5 | 0.2725 | 0.1948 | -0.02394 | 0.5488 | 0.2762 | 0.3561 | 11 | FAIL | -0.09065 | 0.007678 | first_evaluation | PASS | 不通过（c、d、e随机） | 不通过（c、d、e随机） | False |
| Q | A4b | NATIVE | 0.25 | 5 | 0.3631 | 0.2695 | 0.1178 | 0.6074 | 0.3678 | 0.4301 | 12 | PASS |  | 0.09833 | related_exposed | PASS | 通过 | 通过 | False |
| Q | A4b | NATIVE_HG10 | 0.25 | 5 | 0.5279 | 0.4851 | 0.2413 | 0.8061 | 0.5331 | 0.6251 | 14 | PASS | 0.1648 | 0.2631 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | A4b | RP3 | 0.25 | 5 | 0.165 | 0.2136 | 0.05828 | 0.2607 | 0.165 | 0.1784 | 13 | PASS | -0.1981 | -0.09981 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | A4b | SZL5 | 0.25 | 5 | 0.1683 | 0.1394 | -0.05735 | 0.3757 | 0.1837 | 0.244 | 11 | FAIL | -0.1948 | -0.0965 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| Q | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1879 | 0.1204 | -0.02715 | 0.3904 | 0.1622 | 0.2257 | 11 | FAIL | -0.1758 | -0.09839 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| Q | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2386 | 0.1158 | -0.03909 | 0.489 | 0.2139 | 0.2883 | 12 | FAIL | -0.1251 | -0.04769 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| Q | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.3638 | 0.2874 | 0.1376 | 0.5732 | 0.346 | 0.4006 | 12 | PASS |  | 0.07746 | same_account_exposed | PASS | 通过 | 通过 | False |
| Q | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.5176 | 0.5256 | 0.2634 | 0.7718 | 0.4858 | 0.5728 | 13 | PASS | 0.1538 | 0.2313 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.1344 | 0.1481 | 0.04428 | 0.2225 | 0.1344 | 0.1432 | 11 | PASS | -0.2294 | -0.152 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| Q | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.1393 | 0.08961 | -0.06583 | 0.332 | 0.1252 | 0.1917 | 10 | FAIL | -0.2244 | -0.147 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| Q | M_mean3_v2 | INC1 | 0.25 | 5 | 0.2682 | 0.2419 | 0.06332 | 0.4805 | 0.2709 | 0.4345 | 13 | PASS | -0.04979 | 0.06757 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| Q | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.2153 | 0.2007 | -0.05116 | 0.4861 | 0.228 | 0.4097 | 11 | PASS | -0.1026 | 0.01471 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| Q | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.318 | 0.1509 | 0.06691 | 0.5805 | 0.3278 | 0.5171 | 10 | PASS |  | 0.1174 | related_exposed | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False |
| Q | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.2922 | 0.1053 | -0.0002321 | 0.5957 | 0.3124 | 0.5217 | 9 | PASS | -0.02582 | 0.09154 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| Q | M_mean3_v2 | RP3 | 0.25 | 5 | 0.157 | 0.1219 | 0.02507 | 0.2841 | 0.157 | 0.2143 | 12 | PASS | -0.161 | -0.04359 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| Q | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.3539 | 0.2182 | 0.08788 | 0.6125 | 0.361 | 0.5822 | 13 | PASS | 0.03593 | 0.1533 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| Q | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | -0.07264 | -0.03039 | -0.2838 | 0.1367 | -0.07703 | 0.07222 | 7 | FAIL | 0.02254 | -0.1771 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| Q | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.0359 | 0.06857 | -0.2929 | 0.2169 | -0.03624 | 0.1291 | 7 | PASS | 0.05927 | -0.1404 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | -0.09518 | -0.171 | -0.3332 | 0.1615 | -0.09628 | 0.08211 | 5 | PASS |  | -0.1996 | related_exposed | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | -0.05299 | -0.06691 | -0.332 | 0.234 | -0.051 | 0.1477 | 6 | PASS | 0.04218 | -0.1575 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | -0.009236 | -0.005467 | -0.1218 | 0.1075 | -0.009236 | 0.03193 | 7 | FAIL | 0.08594 | -0.1137 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| Q | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.1288 | -0.1459 | -0.3646 | 0.119 | -0.1377 | 0.07605 | 6 | PASS | -0.03362 | -0.2333 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_union3_v2 | INC1 | 0.25 | 5 | 0.1757 | 0.04392 | -0.003759 | 0.3493 | 0.01306 | 0.1249 | 10 | FAIL | -0.05185 | 0.08609 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、正向门槛、e资本、e随机） | False |
| Q | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.3813 | 0.4576 | 0.1571 | 0.5919 | 0.1495 | 0.2919 | 13 | PASS | 0.1537 | 0.2917 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | M_union3_v2 | NATIVE | 0.25 | 5 | 0.2276 | 0.265 | 0.02649 | 0.435 | 0.004184 | 0.1169 | 10 | PASS |  | 0.1379 | related_exposed | PASS | 不通过（d、f） | 不通过（d、f） | False |
| Q | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.5354 | 0.6264 | 0.2958 | 0.77 | 0.2134 | 0.3778 | 14 | PASS | 0.3078 | 0.4458 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | M_union3_v2 | RP3 | 0.25 | 5 | 0.01474 | 0.0004187 | -0.03288 | 0.06085 | 0.01474 | 0.01866 | 12 | MC_UNRESOLVED | -0.2128 | -0.0749 | first_evaluation | PASS | 不通过（正向门槛） | 不通过（正向门槛） | False |
| Q | M_union3_v2 | SZL5 | 0.25 | 5 | 0.1543 | 0.07127 | -0.06497 | 0.3644 | -0.1164 | 0.04941 | 8 | MC_UNRESOLVED | -0.0733 | 0.06464 | first_evaluation | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、正向门槛、e资本） | False |
| Q | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.1689 | 0.06355 | -0.01053 | 0.3354 | -0.005782 | 0.1099 | 8 | FAIL | -0.08217 | 0.0968 | first_evaluation | PASS | 不通过（d、e资本、e随机） | 不通过（d、正向门槛、e资本、e随机） | False |
| Q | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3636 | 0.4359 | 0.1469 | 0.5628 | 0.1242 | 0.2628 | 11 | PASS | 0.1126 | 0.2916 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| Q | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.251 | 0.3142 | 0.05259 | 0.453 | 0.01981 | 0.1315 | 12 | PASS |  | 0.179 | related_exposed | PASS | 通过 | 通过 | False |
| Q | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.5357 | 0.6555 | 0.3049 | 0.762 | 0.2051 | 0.3633 | 13 | PASS | 0.2847 | 0.4637 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.01083 | 0.01371 | -0.03572 | 0.05664 | 0.01083 | 0.01423 | 11 | PASS | -0.2402 | -0.06122 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| Q | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.2018 | 0.1657 | 0.002061 | 0.4021 | -0.07678 | 0.08688 | 9 | PASS | -0.04917 | 0.1298 | first_evaluation | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False |
| S | A4b | INC1 | 0.25 | 5 | 0.08125 | 0.03575 | -0.182 | 0.316 | 0.08413 | 0.1401 | 9 | FAIL | -0.3184 | -0.1836 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | A4b | INC1_HG10 | 0.25 | 5 | 0.3096 | 0.2318 | 0.01812 | 0.5834 | 0.3166 | 0.3913 | 11 | FAIL | -0.09011 | 0.04475 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| S | A4b | NATIVE | 0.25 | 5 | 0.3997 | 0.3777 | 0.1498 | 0.6517 | 0.4052 | 0.4669 | 12 | PASS |  | 0.1349 | same_account_exposed | PASS | 通过 | 通过 | False |
| S | A4b | NATIVE_HG10 | 0.25 | 5 | 0.4139 | 0.3352 | 0.1192 | 0.7094 | 0.4235 | 0.5146 | 12 | PASS | 0.0142 | 0.1491 | first_evaluation | PASS | 通过 | 通过 | False |
| S | A4b | RP3 | 0.25 | 5 | 0.1341 | 0.132 | 0.03198 | 0.23 | 0.1341 | 0.1476 | 10 | PASS | -0.2656 | -0.1307 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| S | A4b | SZL5 | 0.25 | 5 | 0.07851 | 0.08158 | -0.1723 | 0.3188 | 0.09533 | 0.1514 | 10 | FAIL | -0.3212 | -0.1863 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1428 | 0.118 | -0.09349 | 0.3519 | 0.1123 | 0.1847 | 10 | FAIL | -0.2816 | -0.1435 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| S | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2624 | 0.1307 | -0.00494 | 0.513 | 0.239 | 0.3167 | 11 | FAIL | -0.162 | -0.02388 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| S | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.4244 | 0.3578 | 0.2037 | 0.6299 | 0.4003 | 0.4661 | 13 | PASS |  | 0.1381 | same_account_exposed | PASS | 通过 | 通过 | False |
| S | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.4176 | 0.4411 | 0.1467 | 0.69 | 0.4005 | 0.4798 | 12 | PASS | -0.00678 | 0.1313 | first_evaluation | PASS | 通过 | 通过 | False |
| S | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.1102 | 0.1287 | 0.01884 | 0.197 | 0.1102 | 0.1185 | 12 | PASS | -0.3142 | -0.1761 | first_evaluation | PASS | 通过 | 通过 | False |
| S | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.1414 | 0.08738 | -0.0766 | 0.3438 | 0.1183 | 0.1962 | 9 | FAIL | -0.283 | -0.1449 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_mean3_v2 | INC1 | 0.25 | 5 | 0.2785 | 0.1308 | 0.05481 | 0.5142 | 0.2835 | 0.4437 | 12 | MC_UNRESOLVED | -0.06625 | 0.07789 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| S | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.1936 | 0.1127 | -0.08192 | 0.4596 | 0.2019 | 0.3867 | 10 | PASS | -0.1512 | -0.007023 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| S | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.3448 | 0.2127 | 0.08606 | 0.6127 | 0.3502 | 0.5437 | 12 | PASS |  | 0.1441 | same_account_exposed | PASS | 不通过（c） | 不通过（c） | False |
| S | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.313 | 0.1216 | 0.01307 | 0.6066 | 0.3267 | 0.5408 | 9 | PASS | -0.03177 | 0.1124 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| S | M_mean3_v2 | RP3 | 0.25 | 5 | 0.2204 | 0.2108 | 0.1022 | 0.3388 | 0.2204 | 0.2763 | 13 | PASS | -0.1243 | 0.01982 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.1754 | 0.03933 | -0.09069 | 0.4579 | 0.1843 | 0.4015 | 10 | FAIL | -0.1693 | -0.0252 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | -0.03874 | -0.05733 | -0.2481 | 0.1745 | -0.04475 | 0.1062 | 6 | FAIL | -0.03297 | -0.1432 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.09065 | -0.009104 | -0.3398 | 0.1548 | -0.1008 | 0.07603 | 6 | FAIL | -0.08487 | -0.1951 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e资本、e随机） | False |
| S | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | -0.005773 | -0.06165 | -0.2485 | 0.247 | -0.00439 | 0.173 | 8 | PASS |  | -0.1102 | same_account_exposed | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| S | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | -0.08456 | -0.1577 | -0.3562 | 0.2011 | -0.08925 | 0.1173 | 7 | PASS | -0.07878 | -0.189 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| S | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.06107 | 0.03759 | -0.04222 | 0.1648 | 0.06107 | 0.102 | 9 | PASS | 0.06684 | -0.04339 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| S | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.231 | -0.2775 | -0.4855 | 0.03084 | -0.2383 | -0.02566 | 7 | FAIL | -0.2252 | -0.3355 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_union3_v2 | INC1 | 0.25 | 5 | 0.1842 | 0.162 | -0.007725 | 0.3661 | 0.03547 | 0.1348 | 12 | MC_UNRESOLVED | -0.1336 | 0.09456 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不通过（e资本） | True |
| S | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.3984 | 0.3503 | 0.1868 | 0.6027 | 0.148 | 0.3032 | 15 | FAIL | 0.08065 | 0.3088 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| S | M_union3_v2 | NATIVE | 0.25 | 5 | 0.3178 | 0.271 | 0.1204 | 0.5191 | 0.06444 | 0.2039 | 13 | PASS |  | 0.2282 | same_account_exposed | PASS | 不通过（f） | 不通过（f） | False |
| S | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.4324 | 0.4134 | 0.2008 | 0.6539 | 0.09695 | 0.2664 | 14 | PASS | 0.1146 | 0.3428 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_union3_v2 | RP3 | 0.25 | 5 | 0.01587 | 0.004026 | -0.03517 | 0.06561 | 0.01587 | 0.01965 | 11 | FAIL | -0.3019 | -0.07376 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| S | M_union3_v2 | SZL5 | 0.25 | 5 | 0.1094 | 0.03241 | -0.1109 | 0.3209 | -0.1559 | -0.009295 | 9 | FAIL | -0.2084 | 0.01974 | first_evaluation | PASS | 不通过（c、d、f、e资本、e随机） | 不通过（c、d、f、正向门槛、e资本、e随机） | False |
| S | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2101 | 0.2426 | 0.02444 | 0.3802 | 0.04257 | 0.1535 | 13 | PASS | -0.1386 | 0.138 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3916 | 0.4481 | 0.1765 | 0.5906 | 0.1351 | 0.2837 | 12 | PASS | 0.04289 | 0.3195 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3487 | 0.3481 | 0.1639 | 0.5396 | 0.08027 | 0.2279 | 12 | PASS |  | 0.2767 | same_account_exposed | PASS | 通过 | 通过 | False |
| S | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.44 | 0.49 | 0.2019 | 0.6616 | 0.09191 | 0.2616 | 14 | PASS | 0.09127 | 0.3679 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.003435 | -0.00127 | -0.04276 | 0.05014 | 0.003435 | 0.006165 | 9 | FAIL | -0.3453 | -0.06861 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| S | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.1666 | 0.1094 | -0.04141 | 0.3695 | -0.1125 | 0.04038 | 11 | PASS | -0.1821 | 0.09452 | first_evaluation | PASS | 不通过（d、f、e资本） | 不通过（d、f、e资本） | False |
| SM | A4b | NATIVE | 0.25 | 5 | 0.2996 | 0.2374 | 0.06651 | 0.5287 | 0.3078 | 0.3298 | 11 | MC_UNRESOLVED |  | 0.03475 | same_account_exposed | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False |
| SM | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.2566 | 0.1949 | 0.05383 | 0.4491 | 0.2426 | 0.2695 | 13 | PASS |  | -0.02975 | same_account_exposed | PASS | 通过 | 通过 | False |
| SM | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.4969 | 0.4043 | 0.2813 | 0.7331 | 0.4962 | 0.6275 | 15 | PASS |  | 0.2963 | same_account_exposed | PASS | 不通过（c） | 不通过（c） | False |
| SM | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.1814 | 0.1383 | -0.03136 | 0.4078 | 0.1738 | 0.2958 | 13 | PASS |  | 0.07694 | same_account_exposed | PASS | 不通过（c、f） | 不通过（c、f） | False |
| SM | M_union3_v2 | NATIVE | 0.25 | 5 | 0.3699 | 0.3221 | 0.1824 | 0.5623 | 0.1812 | 0.2567 | 13 | PASS |  | 0.2802 | same_account_exposed | PASS | 通过 | 通过 | False |
| SM | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3634 | 0.3373 | 0.1836 | 0.5513 | 0.1663 | 0.2469 | 12 | PASS |  | 0.2914 | same_account_exposed | PASS | 通过 | 通过 | False |


## profile PROPOSED_PORT3_LAG1

> 表头：主体=144 主展示 + C1_hi + SM 锚｜算子=见列｜分母=四段有效配对日（FULL = n 加权；G4 = 段中位）｜基准=同 H 原父（8bp）｜子集=primary144 | c1_hi | sm_anchor｜单位=年化百分点 / 判词｜日期=2010-01-04..2026-03-27（四段；2026 partial）｜H=H 见列｜成本模型=源 8bp（f：A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（e 资本：MATCH-CAP）｜exposure=见 evidence_exposure 列｜query_id=E6K-P3-POL-PROPOSEDPORT3LAG1


| meas | mother | op | alpha | H | FULL | G4 | ci_L20_lo | ci_L20_hi | FULL_sc | FULL_imp | years_pos | e_rand | FULL_vs_native | FULL_vs_nativeC1 | evidence_exposure | size_PROPOSED_PORT3_LAG1 | policy_PROPOSED_PORT3_LAG1_FULL | policy_PROPOSED_PORT3_LAG1_G4 | POLICY_INTERPRETATION_PENDING_PROPOSED_PORT3_LAG1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | A4b | INC1 | 0.25 | 5 | 0.1993 | 0.1666 | 0.03081 | 0.3619 | 0.2035 | 0.2056 | 13 | MC_UNRESOLVED | -0.06553 | -0.06553 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| C1 | A4b | INC1_HG10 | 0.25 | 5 | 0.2376 | 0.3176 | 0.01428 | 0.453 | 0.2399 | 0.2533 | 11 | FAIL | -0.02717 | -0.02717 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| C1 | A4b | NATIVE | 0.25 | 5 | 0.2648 | 0.311 | 0.07639 | 0.4442 | 0.2649 | 0.2738 | 13 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b | NATIVE | 0.5 | 10 | 0.4742 | 0.5273 | 0.19 | 0.755 | 0.4401 | 0.4511 | 14 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b | NATIVE | 0.5 | 20 | 0.3358 | 0.3565 | 0.1394 | 0.5252 | 0.3152 | 0.3247 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b | NATIVE_HG10 | 0.25 | 5 | 0.2929 | 0.2275 | 0.04494 | 0.5338 | 0.2869 | 0.309 | 10 | PASS | 0.02809 | 0.02809 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| C1 | A4b | RP3 | 0.25 | 5 | 0.02682 | 0.01826 | -0.04199 | 0.0943 | 0.02682 | 0.02785 | 11 | PASS | -0.238 | -0.238 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| C1 | A4b | SZL5 | 0.25 | 5 | 0.1258 | 0.03719 | -0.0705 | 0.3107 | 0.1328 | 0.1327 | 10 | PASS | -0.139 | -0.139 | first_evaluation | PASS | 不通过（d） | 不通过（d、正向门槛） | False |
| C1 | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1824 | 0.2094 | 0.03225 | 0.32 | 0.1639 | 0.1768 | 12 | FAIL | -0.1039 | -0.1039 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| C1 | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2232 | 0.3032 | 0.02851 | 0.4113 | 0.2118 | 0.2213 | 10 | FAIL | -0.06307 | -0.06307 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| C1 | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.2863 | 0.3224 | 0.1182 | 0.4473 | 0.2728 | 0.2809 | 14 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b_CVRv5 | NATIVE | 0.5 | 10 | 0.4206 | 0.3958 | 0.1749 | 0.6575 | 0.4056 | 0.3929 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b_CVRv5 | NATIVE | 0.5 | 20 | 0.2857 | 0.2776 | 0.1175 | 0.456 | 0.2734 | 0.2736 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.2387 | 0.2548 | 0.02666 | 0.4464 | 0.2218 | 0.2312 | 11 | PASS | -0.04761 | -0.04761 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| C1 | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.03286 | 0.03379 | -0.02538 | 0.0921 | 0.03286 | 0.0335 | 11 | PASS | -0.2534 | -0.2534 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| C1 | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.124 | 0.07449 | -0.04594 | 0.2898 | 0.1211 | 0.1234 | 11 | FAIL | -0.1623 | -0.1623 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_mean3_v2 | INC1 | 0.25 | 5 | 0.1792 | 0.0971 | 0.04069 | 0.319 | 0.1741 | 0.1999 | 13 | FAIL | -0.02146 | -0.02146 | first_evaluation | PASS | 不通过（e随机） | 不通过（正向门槛、e随机） | False |
| C1 | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.06166 | 0.008405 | -0.1416 | 0.2776 | 0.05662 | 0.1124 | 11 | FAIL | -0.139 | -0.139 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.2006 | 0.1498 | 0.04456 | 0.3478 | 0.1946 | 0.2267 | 13 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.1979 | 0.111 | -0.03353 | 0.4343 | 0.1943 | 0.254 | 12 | FAIL | -0.002698 | -0.002698 | first_evaluation | PASS | 不通过（c、e随机） | 不通过（c、e随机） | False |
| C1 | M_mean3_v2 | RP3 | 0.25 | 5 | 0.07358 | 0.06543 | 0.02002 | 0.1256 | 0.07358 | 0.07844 | 9 | FAIL | -0.127 | -0.127 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| C1 | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.1672 | 0.1965 | -0.03337 | 0.3789 | 0.1737 | 0.2275 | 10 | FAIL | -0.03339 | -0.03339 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| C1 | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.08837 | 0.07339 | -0.0385 | 0.2151 | 0.0802 | 0.1053 | 12 | FAIL | -0.01609 | -0.01609 | first_evaluation | PASS | 不通过（正向门槛、e随机） | 不通过（正向门槛、e随机） | False |
| C1 | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.1125 | -0.1064 | -0.3101 | 0.08312 | -0.1186 | -0.0699 | 7 | FAIL | -0.217 | -0.217 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.1045 | 0.09114 | -0.03507 | 0.2393 | 0.09502 | 0.1255 | 12 | PASS |  |  | same_account_exposed | PASS | 通过 | 不通过（正向门槛） | True |
| C1 | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.00137 | -0.009876 | -0.2139 | 0.2206 | -0.009498 | 0.04625 | 10 | PASS | -0.1031 | -0.1031 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e资本） | 不通过（c、d、f、正向门槛） | False |
| C1 | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.03224 | 0.03028 | -0.0182 | 0.08394 | 0.03224 | 0.03556 | 8 | PASS | -0.07222 | -0.07222 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| C1 | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.02625 | 0.02404 | -0.1984 | 0.1458 | -0.02549 | 0.03063 | 9 | PASS | -0.1307 | -0.1307 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| C1 | M_union3_v2 | INC1 | 0.25 | 5 | 0.03555 | 0.07215 | -0.1007 | 0.173 | 0.0064 | -0.004975 | 11 | FAIL | -0.05409 | -0.05409 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.1696 | 0.1773 | -0.01546 | 0.3613 | 0.06871 | 0.09116 | 12 | PASS | 0.07999 | 0.07999 | first_evaluation | PASS | 不通过（f） | 不通过（f） | False |
| C1 | M_union3_v2 | NATIVE | 0.25 | 5 | 0.08964 | 0.09268 | -0.06266 | 0.2459 | 0.04254 | 0.03047 | 12 | PASS |  |  | same_account_exposed | PASS | 不通过（正向门槛） | 不通过（正向门槛） | False |
| C1 | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.1652 | 0.1857 | -0.0345 | 0.3763 | 0.05509 | 0.06316 | 12 | PASS | 0.07554 | 0.07554 | first_evaluation | PASS | 不通过（f） | 不通过（f） | False |
| C1 | M_union3_v2 | RP3 | 0.25 | 5 | 0.01305 | 0.004054 | -0.03189 | 0.05926 | 0.01305 | 0.01005 | 11 | FAIL | -0.07659 | -0.07659 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| C1 | M_union3_v2 | SZL5 | 0.25 | 5 | -0.05162 | -0.05403 | -0.2646 | 0.16 | -0.1339 | -0.1258 | 8 | FAIL | -0.1413 | -0.1413 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.01715 | 0.04369 | -0.1179 | 0.1548 | -0.009748 | -0.02245 | 10 | FAIL | -0.05489 | -0.05489 | first_evaluation | PASS | 不通过（d、f、正向门槛、e资本、e随机） | 不通过（d、f、正向门槛、e随机） | False |
| C1 | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.1555 | 0.1447 | -0.02468 | 0.3374 | 0.06176 | 0.0744 | 12 | PASS | 0.08346 | 0.08346 | first_evaluation | PASS | 通过 | 通过 | False |
| C1 | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.07205 | 0.08064 | -0.07399 | 0.2168 | 0.03263 | 0.01425 | 10 | PASS |  |  | same_account_exposed | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| C1 | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.1526 | 0.1473 | -0.04438 | 0.3466 | 0.04796 | 0.0497 | 12 | PASS | 0.08059 | 0.08059 | first_evaluation | PASS | 不通过（f） | 不通过（f） | False |
| C1 | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.00119 | -0.00744 | -0.03962 | 0.04427 | 0.00119 | -0.0009616 | 9 | FAIL | -0.07086 | -0.07086 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| C1 | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.02526 | 0.01453 | -0.2121 | 0.1562 | -0.09905 | -0.09544 | 9 | FAIL | -0.0973 | -0.0973 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e资本、e随机） | False |
| M | A4b | INC1 | 0.25 | 5 | 0.1232 | 0.04958 | -0.07289 | 0.3303 | 0.1384 | 0.1445 | 11 | FAIL | -0.2154 | -0.1416 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、正向门槛、e随机） | False |
| M | A4b | INC1_HG10 | 0.25 | 5 | 0.1888 | 0.1395 | -0.05864 | 0.4124 | 0.1945 | 0.2289 | 11 | FAIL | -0.1499 | -0.07604 | first_evaluation | PASS | 不通过（c、d、e随机） | 不通过（c、d、e随机） | False |
| M | A4b | NATIVE | 0.25 | 5 | 0.3386 | 0.2736 | 0.1176 | 0.5664 | 0.3462 | 0.3521 | 14 | PASS |  | 0.07382 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | A4b | NATIVE_HG10 | 0.25 | 5 | 0.3479 | 0.2125 | 0.113 | 0.5916 | 0.3579 | 0.3797 | 12 | PASS | 0.009267 | 0.08309 | first_evaluation | PASS | 通过 | 通过 | False |
| M | A4b | RP3 | 0.25 | 5 | 0.0804 | 0.1039 | 0.001027 | 0.1645 | 0.0804 | 0.08056 | 10 | PASS | -0.2582 | -0.1844 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d） | False |
| M | A4b | SZL5 | 0.25 | 5 | 0.2483 | 0.1122 | 0.03211 | 0.4758 | 0.2632 | 0.2705 | 12 | FAIL | -0.09035 | -0.01653 | first_evaluation | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False |
| M | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1118 | 0.1358 | -0.06575 | 0.2965 | 0.1217 | 0.1257 | 12 | FAIL | -0.2282 | -0.1745 | first_evaluation | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False |
| M | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2176 | 0.143 | 0.004276 | 0.4178 | 0.2152 | 0.2404 | 12 | FAIL | -0.1224 | -0.06868 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| M | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.34 | 0.2745 | 0.1475 | 0.5325 | 0.3456 | 0.3408 | 15 | PASS |  | 0.0537 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.371 | 0.3839 | 0.1612 | 0.5794 | 0.3812 | 0.3836 | 12 | PASS | 0.03103 | 0.08473 | first_evaluation | PASS | 通过 | 通过 | False |
| M | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.06943 | 0.08925 | 0.000882 | 0.1387 | 0.06943 | 0.06759 | 10 | PASS | -0.2706 | -0.2169 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| M | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.2398 | 0.1384 | 0.03711 | 0.4456 | 0.2481 | 0.253 | 13 | PASS | -0.1002 | -0.04655 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_mean3_v2 | INC1 | 0.25 | 5 | 0.3977 | 0.3379 | 0.1925 | 0.6053 | 0.3944 | 0.4544 | 14 | PASS | -0.03838 | 0.1971 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.3382 | 0.2332 | 0.1108 | 0.5797 | 0.3284 | 0.4276 | 13 | FAIL | -0.09796 | 0.1376 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| M | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.4361 | 0.4186 | 0.1961 | 0.6759 | 0.4293 | 0.4951 | 13 | PASS |  | 0.2355 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.4293 | 0.341 | 0.1746 | 0.7063 | 0.4247 | 0.5226 | 13 | PASS | -0.006868 | 0.2286 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| M | M_mean3_v2 | RP3 | 0.25 | 5 | 0.1187 | 0.07533 | 0.02214 | 0.2133 | 0.1187 | 0.1295 | 11 | PASS | -0.3174 | -0.08192 | first_evaluation | PASS | 不通过（d） | 不通过（d、正向门槛） | False |
| M | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.3756 | 0.314 | 0.1205 | 0.6218 | 0.3727 | 0.4703 | 11 | FAIL | -0.06055 | 0.175 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| M | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2247 | 0.172 | 0.03871 | 0.4167 | 0.2218 | 0.2742 | 12 | PASS | 0.008202 | 0.1202 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.1566 | 0.1241 | -0.05568 | 0.3851 | 0.1422 | 0.2329 | 11 | PASS | -0.05994 | 0.0521 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| M | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.2165 | 0.2578 | -0.005673 | 0.4458 | 0.2137 | 0.2696 | 12 | PASS |  | 0.112 | same_account_exposed | PASS | 不通过（c、f） | 不通过（c、f） | False |
| M | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.1976 | 0.1692 | -0.05168 | 0.4646 | 0.1866 | 0.2783 | 11 | PASS | -0.0189 | 0.09313 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| M | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.01163 | 0.01061 | -0.06285 | 0.08551 | 0.01163 | 0.01876 | 8 | FAIL | -0.2049 | -0.09283 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| M | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.1803 | 0.173 | -0.05175 | 0.4166 | 0.1802 | 0.2702 | 11 | PASS | -0.03617 | 0.07587 | first_evaluation | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False |
| M | M_union3_v2 | INC1 | 0.25 | 5 | 0.2595 | 0.2783 | 0.06196 | 0.4666 | 0.1492 | 0.1901 | 12 | PASS | -0.1385 | 0.1698 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.2833 | 0.2853 | 0.06601 | 0.4978 | 0.1202 | 0.1746 | 14 | MC_UNRESOLVED | -0.1147 | 0.1936 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| M | M_union3_v2 | NATIVE | 0.25 | 5 | 0.398 | 0.2775 | 0.1808 | 0.615 | 0.2507 | 0.3111 | 13 | PASS |  | 0.3084 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.3104 | 0.3448 | 0.04982 | 0.5717 | 0.1293 | 0.1844 | 12 | PASS | -0.08756 | 0.2208 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2 | RP3 | 0.25 | 5 | 0.04687 | 0.05325 | -0.01152 | 0.101 | 0.04687 | 0.03928 | 10 | FAIL | -0.3511 | -0.04277 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| M | M_union3_v2 | SZL5 | 0.25 | 5 | 0.3308 | 0.2388 | 0.1182 | 0.5691 | 0.1725 | 0.2336 | 14 | PASS | -0.06722 | 0.2411 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2577 | 0.287 | 0.07197 | 0.4523 | 0.1482 | 0.1885 | 11 | PASS | -0.1191 | 0.1856 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| M | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3035 | 0.3393 | 0.1005 | 0.5104 | 0.1428 | 0.1913 | 15 | MC_UNRESOLVED | -0.07329 | 0.2315 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| M | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3768 | 0.3079 | 0.1588 | 0.5886 | 0.2397 | 0.2903 | 14 | PASS |  | 0.3048 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.3473 | 0.4264 | 0.09834 | 0.5926 | 0.1688 | 0.2166 | 14 | PASS | -0.02949 | 0.2753 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.05518 | 0.04137 | 0.001627 | 0.1068 | 0.05518 | 0.04858 | 12 | FAIL | -0.3216 | -0.01687 | first_evaluation | PASS | 不通过（正向门槛、e随机） | 不通过（正向门槛、e随机） | False |
| M | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.34 | 0.3027 | 0.1414 | 0.5592 | 0.186 | 0.2437 | 14 | PASS | -0.03683 | 0.2679 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | A4b | INC1 | 0.25 | 5 | 0.1974 | 0.1573 | -0.03012 | 0.4159 | 0.2034 | 0.2552 | 11 | FAIL | -0.1657 | -0.06739 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| Q | A4b | INC1_HG10 | 0.25 | 5 | 0.2725 | 0.1948 | -0.02394 | 0.5488 | 0.2762 | 0.3561 | 11 | FAIL | -0.09065 | 0.007678 | first_evaluation | PASS | 不通过（c、d、e随机） | 不通过（c、d、e随机） | False |
| Q | A4b | NATIVE | 0.25 | 5 | 0.3631 | 0.2695 | 0.1178 | 0.6074 | 0.3678 | 0.4301 | 12 | PASS |  | 0.09833 | related_exposed | PASS | 通过 | 通过 | False |
| Q | A4b | NATIVE_HG10 | 0.25 | 5 | 0.5279 | 0.4851 | 0.2413 | 0.8061 | 0.5331 | 0.6251 | 14 | PASS | 0.1648 | 0.2631 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | A4b | RP3 | 0.25 | 5 | 0.165 | 0.2136 | 0.05828 | 0.2607 | 0.165 | 0.1784 | 13 | PASS | -0.1981 | -0.09981 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | A4b | SZL5 | 0.25 | 5 | 0.1683 | 0.1394 | -0.05735 | 0.3757 | 0.1837 | 0.244 | 11 | FAIL | -0.1948 | -0.0965 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| Q | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1879 | 0.1204 | -0.02715 | 0.3904 | 0.1622 | 0.2257 | 11 | FAIL | -0.1758 | -0.09839 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| Q | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2386 | 0.1158 | -0.03909 | 0.489 | 0.2139 | 0.2883 | 12 | FAIL | -0.1251 | -0.04769 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| Q | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.3638 | 0.2874 | 0.1376 | 0.5732 | 0.346 | 0.4006 | 12 | PASS |  | 0.07746 | same_account_exposed | PASS | 通过 | 通过 | False |
| Q | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.5176 | 0.5256 | 0.2634 | 0.7718 | 0.4858 | 0.5728 | 13 | PASS | 0.1538 | 0.2313 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.1344 | 0.1481 | 0.04428 | 0.2225 | 0.1344 | 0.1432 | 11 | PASS | -0.2294 | -0.152 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| Q | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.1393 | 0.08961 | -0.06583 | 0.332 | 0.1252 | 0.1917 | 10 | FAIL | -0.2244 | -0.147 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| Q | M_mean3_v2 | INC1 | 0.25 | 5 | 0.2682 | 0.2419 | 0.06332 | 0.4805 | 0.2709 | 0.4345 | 13 | PASS | -0.04979 | 0.06757 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| Q | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.2153 | 0.2007 | -0.05116 | 0.4861 | 0.228 | 0.4097 | 11 | PASS | -0.1026 | 0.01471 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| Q | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.318 | 0.1509 | 0.06691 | 0.5805 | 0.3278 | 0.5171 | 10 | PASS |  | 0.1174 | related_exposed | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False |
| Q | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.2922 | 0.1053 | -0.0002321 | 0.5957 | 0.3124 | 0.5217 | 9 | PASS | -0.02582 | 0.09154 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| Q | M_mean3_v2 | RP3 | 0.25 | 5 | 0.157 | 0.1219 | 0.02507 | 0.2841 | 0.157 | 0.2143 | 12 | PASS | -0.161 | -0.04359 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| Q | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.3539 | 0.2182 | 0.08788 | 0.6125 | 0.361 | 0.5822 | 13 | PASS | 0.03593 | 0.1533 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| Q | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | -0.07264 | -0.03039 | -0.2838 | 0.1367 | -0.07703 | 0.07222 | 7 | FAIL | 0.02254 | -0.1771 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| Q | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.0359 | 0.06857 | -0.2929 | 0.2169 | -0.03624 | 0.1291 | 7 | PASS | 0.05927 | -0.1404 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | -0.09518 | -0.171 | -0.3332 | 0.1615 | -0.09628 | 0.08211 | 5 | PASS |  | -0.1996 | related_exposed | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | -0.05299 | -0.06691 | -0.332 | 0.234 | -0.051 | 0.1477 | 6 | PASS | 0.04218 | -0.1575 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | -0.009236 | -0.005467 | -0.1218 | 0.1075 | -0.009236 | 0.03193 | 7 | FAIL | 0.08594 | -0.1137 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| Q | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.1288 | -0.1459 | -0.3646 | 0.119 | -0.1377 | 0.07605 | 6 | PASS | -0.03362 | -0.2333 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_union3_v2 | INC1 | 0.25 | 5 | 0.1757 | 0.04392 | -0.003759 | 0.3493 | 0.01306 | 0.1249 | 10 | FAIL | -0.05185 | 0.08609 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、正向门槛、e资本、e随机） | False |
| Q | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.3813 | 0.4576 | 0.1571 | 0.5919 | 0.1495 | 0.2919 | 13 | PASS | 0.1537 | 0.2917 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | M_union3_v2 | NATIVE | 0.25 | 5 | 0.2276 | 0.265 | 0.02649 | 0.435 | 0.004184 | 0.1169 | 10 | PASS |  | 0.1379 | related_exposed | PASS | 不通过（d、f） | 不通过（d、f） | False |
| Q | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.5354 | 0.6264 | 0.2958 | 0.77 | 0.2134 | 0.3778 | 14 | PASS | 0.3078 | 0.4458 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | M_union3_v2 | RP3 | 0.25 | 5 | 0.01474 | 0.0004187 | -0.03288 | 0.06085 | 0.01474 | 0.01866 | 12 | MC_UNRESOLVED | -0.2128 | -0.0749 | first_evaluation | PASS | 不通过（正向门槛） | 不通过（正向门槛） | False |
| Q | M_union3_v2 | SZL5 | 0.25 | 5 | 0.1543 | 0.07127 | -0.06497 | 0.3644 | -0.1164 | 0.04941 | 8 | MC_UNRESOLVED | -0.0733 | 0.06464 | first_evaluation | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、正向门槛、e资本） | False |
| Q | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.1689 | 0.06355 | -0.01053 | 0.3354 | -0.005782 | 0.1099 | 8 | FAIL | -0.08217 | 0.0968 | first_evaluation | PASS | 不通过（d、e资本、e随机） | 不通过（d、正向门槛、e资本、e随机） | False |
| Q | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3636 | 0.4359 | 0.1469 | 0.5628 | 0.1242 | 0.2628 | 11 | PASS | 0.1126 | 0.2916 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| Q | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.251 | 0.3142 | 0.05259 | 0.453 | 0.01981 | 0.1315 | 12 | PASS |  | 0.179 | related_exposed | PASS | 通过 | 通过 | False |
| Q | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.5357 | 0.6555 | 0.3049 | 0.762 | 0.2051 | 0.3633 | 13 | PASS | 0.2847 | 0.4637 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.01083 | 0.01371 | -0.03572 | 0.05664 | 0.01083 | 0.01423 | 11 | PASS | -0.2402 | -0.06122 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| Q | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.2018 | 0.1657 | 0.002061 | 0.4021 | -0.07678 | 0.08688 | 9 | PASS | -0.04917 | 0.1298 | first_evaluation | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False |
| S | A4b | INC1 | 0.25 | 5 | 0.08125 | 0.03575 | -0.182 | 0.316 | 0.08413 | 0.1401 | 9 | FAIL | -0.3184 | -0.1836 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | A4b | INC1_HG10 | 0.25 | 5 | 0.3096 | 0.2318 | 0.01812 | 0.5834 | 0.3166 | 0.3913 | 11 | FAIL | -0.09011 | 0.04475 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| S | A4b | NATIVE | 0.25 | 5 | 0.3997 | 0.3777 | 0.1498 | 0.6517 | 0.4052 | 0.4669 | 12 | PASS |  | 0.1349 | same_account_exposed | PASS | 通过 | 通过 | False |
| S | A4b | NATIVE_HG10 | 0.25 | 5 | 0.4139 | 0.3352 | 0.1192 | 0.7094 | 0.4235 | 0.5146 | 12 | PASS | 0.0142 | 0.1491 | first_evaluation | PASS | 通过 | 通过 | False |
| S | A4b | RP3 | 0.25 | 5 | 0.1341 | 0.132 | 0.03198 | 0.23 | 0.1341 | 0.1476 | 10 | PASS | -0.2656 | -0.1307 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| S | A4b | SZL5 | 0.25 | 5 | 0.07851 | 0.08158 | -0.1723 | 0.3188 | 0.09533 | 0.1514 | 10 | FAIL | -0.3212 | -0.1863 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1428 | 0.118 | -0.09349 | 0.3519 | 0.1123 | 0.1847 | 10 | FAIL | -0.2816 | -0.1435 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| S | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2624 | 0.1307 | -0.00494 | 0.513 | 0.239 | 0.3167 | 11 | FAIL | -0.162 | -0.02388 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| S | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.4244 | 0.3578 | 0.2037 | 0.6299 | 0.4003 | 0.4661 | 13 | PASS |  | 0.1381 | same_account_exposed | PASS | 通过 | 通过 | False |
| S | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.4176 | 0.4411 | 0.1467 | 0.69 | 0.4005 | 0.4798 | 12 | PASS | -0.00678 | 0.1313 | first_evaluation | PASS | 通过 | 通过 | False |
| S | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.1102 | 0.1287 | 0.01884 | 0.197 | 0.1102 | 0.1185 | 12 | PASS | -0.3142 | -0.1761 | first_evaluation | PASS | 通过 | 通过 | False |
| S | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.1414 | 0.08738 | -0.0766 | 0.3438 | 0.1183 | 0.1962 | 9 | FAIL | -0.283 | -0.1449 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_mean3_v2 | INC1 | 0.25 | 5 | 0.2785 | 0.1308 | 0.05481 | 0.5142 | 0.2835 | 0.4437 | 12 | MC_UNRESOLVED | -0.06625 | 0.07789 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| S | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.1936 | 0.1127 | -0.08192 | 0.4596 | 0.2019 | 0.3867 | 10 | PASS | -0.1512 | -0.007023 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| S | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.3448 | 0.2127 | 0.08606 | 0.6127 | 0.3502 | 0.5437 | 12 | PASS |  | 0.1441 | same_account_exposed | PASS | 不通过（c） | 不通过（c） | False |
| S | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.313 | 0.1216 | 0.01307 | 0.6066 | 0.3267 | 0.5408 | 9 | PASS | -0.03177 | 0.1124 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| S | M_mean3_v2 | RP3 | 0.25 | 5 | 0.2204 | 0.2108 | 0.1022 | 0.3388 | 0.2204 | 0.2763 | 13 | PASS | -0.1243 | 0.01982 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.1754 | 0.03933 | -0.09069 | 0.4579 | 0.1843 | 0.4015 | 10 | FAIL | -0.1693 | -0.0252 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | -0.03874 | -0.05733 | -0.2481 | 0.1745 | -0.04475 | 0.1062 | 6 | FAIL | -0.03297 | -0.1432 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.09065 | -0.009104 | -0.3398 | 0.1548 | -0.1008 | 0.07603 | 6 | FAIL | -0.08487 | -0.1951 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e资本、e随机） | False |
| S | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | -0.005773 | -0.06165 | -0.2485 | 0.247 | -0.00439 | 0.173 | 8 | PASS |  | -0.1102 | same_account_exposed | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| S | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | -0.08456 | -0.1577 | -0.3562 | 0.2011 | -0.08925 | 0.1173 | 7 | PASS | -0.07878 | -0.189 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| S | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.06107 | 0.03759 | -0.04222 | 0.1648 | 0.06107 | 0.102 | 9 | PASS | 0.06684 | -0.04339 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| S | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.231 | -0.2775 | -0.4855 | 0.03084 | -0.2383 | -0.02566 | 7 | FAIL | -0.2252 | -0.3355 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_union3_v2 | INC1 | 0.25 | 5 | 0.1842 | 0.162 | -0.007725 | 0.3661 | 0.03547 | 0.1348 | 12 | MC_UNRESOLVED | -0.1336 | 0.09456 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不通过（e资本） | True |
| S | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.3984 | 0.3503 | 0.1868 | 0.6027 | 0.148 | 0.3032 | 15 | FAIL | 0.08065 | 0.3088 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| S | M_union3_v2 | NATIVE | 0.25 | 5 | 0.3178 | 0.271 | 0.1204 | 0.5191 | 0.06444 | 0.2039 | 13 | PASS |  | 0.2282 | same_account_exposed | PASS | 不通过（f） | 不通过（f） | False |
| S | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.4324 | 0.4134 | 0.2008 | 0.6539 | 0.09695 | 0.2664 | 14 | PASS | 0.1146 | 0.3428 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_union3_v2 | RP3 | 0.25 | 5 | 0.01587 | 0.004026 | -0.03517 | 0.06561 | 0.01587 | 0.01965 | 11 | FAIL | -0.3019 | -0.07376 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| S | M_union3_v2 | SZL5 | 0.25 | 5 | 0.1094 | 0.03241 | -0.1109 | 0.3209 | -0.1559 | -0.009295 | 9 | FAIL | -0.2084 | 0.01974 | first_evaluation | PASS | 不通过（c、d、f、e资本、e随机） | 不通过（c、d、f、正向门槛、e资本、e随机） | False |
| S | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2101 | 0.2426 | 0.02444 | 0.3802 | 0.04257 | 0.1535 | 13 | PASS | -0.1386 | 0.138 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3916 | 0.4481 | 0.1765 | 0.5906 | 0.1351 | 0.2837 | 12 | PASS | 0.04289 | 0.3195 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3487 | 0.3481 | 0.1639 | 0.5396 | 0.08027 | 0.2279 | 12 | PASS |  | 0.2767 | same_account_exposed | PASS | 通过 | 通过 | False |
| S | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.44 | 0.49 | 0.2019 | 0.6616 | 0.09191 | 0.2616 | 14 | PASS | 0.09127 | 0.3679 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.003435 | -0.00127 | -0.04276 | 0.05014 | 0.003435 | 0.006165 | 9 | FAIL | -0.3453 | -0.06861 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| S | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.1666 | 0.1094 | -0.04141 | 0.3695 | -0.1125 | 0.04038 | 11 | PASS | -0.1821 | 0.09452 | first_evaluation | PASS | 不通过（d、f、e资本） | 不通过（d、f、e资本） | False |
| SM | A4b | NATIVE | 0.25 | 5 | 0.2996 | 0.2374 | 0.06651 | 0.5287 | 0.3078 | 0.3298 | 11 | MC_UNRESOLVED |  | 0.03475 | same_account_exposed | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False |
| SM | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.2566 | 0.1949 | 0.05383 | 0.4491 | 0.2426 | 0.2695 | 13 | PASS |  | -0.02975 | same_account_exposed | PASS | 通过 | 通过 | False |
| SM | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.4969 | 0.4043 | 0.2813 | 0.7331 | 0.4962 | 0.6275 | 15 | PASS |  | 0.2963 | same_account_exposed | PASS | 不通过（c） | 不通过（c） | False |
| SM | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.1814 | 0.1383 | -0.03136 | 0.4078 | 0.1738 | 0.2958 | 13 | PASS |  | 0.07694 | same_account_exposed | PASS | 不通过（c、f） | 不通过（c、f） | False |
| SM | M_union3_v2 | NATIVE | 0.25 | 5 | 0.3699 | 0.3221 | 0.1824 | 0.5623 | 0.1812 | 0.2567 | 13 | PASS |  | 0.2802 | same_account_exposed | PASS | 通过 | 通过 | False |
| SM | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3634 | 0.3373 | 0.1836 | 0.5513 | 0.1663 | 0.2469 | 12 | PASS |  | 0.2914 | same_account_exposed | PASS | 通过 | 通过 | False |


## profile EXEC_DISCLOSE_ONLY

> 表头：主体=144 主展示 + C1_hi + SM 锚｜算子=见列｜分母=四段有效配对日（FULL = n 加权；G4 = 段中位）｜基准=同 H 原父（8bp）｜子集=primary144 | c1_hi | sm_anchor｜单位=年化百分点 / 判词｜日期=2010-01-04..2026-03-27（四段；2026 partial）｜H=H 见列｜成本模型=源 8bp（f：A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（e 资本：MATCH-CAP）｜exposure=见 evidence_exposure 列｜query_id=E6K-P3-POL-EXECDISCLOSEONLY


| meas | mother | op | alpha | H | FULL | G4 | ci_L20_lo | ci_L20_hi | FULL_sc | FULL_imp | years_pos | e_rand | FULL_vs_native | FULL_vs_nativeC1 | evidence_exposure | size_EXEC_DISCLOSE_ONLY | policy_EXEC_DISCLOSE_ONLY_FULL | policy_EXEC_DISCLOSE_ONLY_G4 | POLICY_INTERPRETATION_PENDING_EXEC_DISCLOSE_ONLY |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | A4b | INC1 | 0.25 | 5 | 0.1993 | 0.1666 | 0.03081 | 0.3619 | 0.2035 | 0.2056 | 13 | MC_UNRESOLVED | -0.06553 | -0.06553 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| C1 | A4b | INC1_HG10 | 0.25 | 5 | 0.2376 | 0.3176 | 0.01428 | 0.453 | 0.2399 | 0.2533 | 11 | FAIL | -0.02717 | -0.02717 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| C1 | A4b | NATIVE | 0.25 | 5 | 0.2648 | 0.311 | 0.07639 | 0.4442 | 0.2649 | 0.2738 | 13 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b | NATIVE | 0.5 | 10 | 0.4742 | 0.5273 | 0.19 | 0.755 | 0.4401 | 0.4511 | 14 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b | NATIVE | 0.5 | 20 | 0.3358 | 0.3565 | 0.1394 | 0.5252 | 0.3152 | 0.3247 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b | NATIVE_HG10 | 0.25 | 5 | 0.2929 | 0.2275 | 0.04494 | 0.5338 | 0.2869 | 0.309 | 10 | PASS | 0.02809 | 0.02809 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| C1 | A4b | RP3 | 0.25 | 5 | 0.02682 | 0.01826 | -0.04199 | 0.0943 | 0.02682 | 0.02785 | 11 | PASS | -0.238 | -0.238 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| C1 | A4b | SZL5 | 0.25 | 5 | 0.1258 | 0.03719 | -0.0705 | 0.3107 | 0.1328 | 0.1327 | 10 | PASS | -0.139 | -0.139 | first_evaluation | PASS | 不通过（d） | 不通过（d、正向门槛） | False |
| C1 | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1824 | 0.2094 | 0.03225 | 0.32 | 0.1639 | 0.1768 | 12 | FAIL | -0.1039 | -0.1039 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| C1 | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2232 | 0.3032 | 0.02851 | 0.4113 | 0.2118 | 0.2213 | 10 | FAIL | -0.06307 | -0.06307 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| C1 | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.2863 | 0.3224 | 0.1182 | 0.4473 | 0.2728 | 0.2809 | 14 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b_CVRv5 | NATIVE | 0.5 | 10 | 0.4206 | 0.3958 | 0.1749 | 0.6575 | 0.4056 | 0.3929 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b_CVRv5 | NATIVE | 0.5 | 20 | 0.2857 | 0.2776 | 0.1175 | 0.456 | 0.2734 | 0.2736 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.2387 | 0.2548 | 0.02666 | 0.4464 | 0.2218 | 0.2312 | 11 | PASS | -0.04761 | -0.04761 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| C1 | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.03286 | 0.03379 | -0.02538 | 0.0921 | 0.03286 | 0.0335 | 11 | PASS | -0.2534 | -0.2534 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| C1 | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.124 | 0.07449 | -0.04594 | 0.2898 | 0.1211 | 0.1234 | 11 | FAIL | -0.1623 | -0.1623 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_mean3_v2 | INC1 | 0.25 | 5 | 0.1792 | 0.0971 | 0.04069 | 0.319 | 0.1741 | 0.1999 | 13 | FAIL | -0.02146 | -0.02146 | first_evaluation | PASS | 不通过（e随机） | 不通过（正向门槛、e随机） | False |
| C1 | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.06166 | 0.008405 | -0.1416 | 0.2776 | 0.05662 | 0.1124 | 11 | FAIL | -0.139 | -0.139 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.2006 | 0.1498 | 0.04456 | 0.3478 | 0.1946 | 0.2267 | 13 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.1979 | 0.111 | -0.03353 | 0.4343 | 0.1943 | 0.254 | 12 | FAIL | -0.002698 | -0.002698 | first_evaluation | PASS | 不通过（c、e随机） | 不通过（c、e随机） | False |
| C1 | M_mean3_v2 | RP3 | 0.25 | 5 | 0.07358 | 0.06543 | 0.02002 | 0.1256 | 0.07358 | 0.07844 | 9 | FAIL | -0.127 | -0.127 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| C1 | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.1672 | 0.1965 | -0.03337 | 0.3789 | 0.1737 | 0.2275 | 10 | FAIL | -0.03339 | -0.03339 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| C1 | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.08837 | 0.07339 | -0.0385 | 0.2151 | 0.0802 | 0.1053 | 12 | FAIL | -0.01609 | -0.01609 | first_evaluation | PASS | 不通过（正向门槛、e随机） | 不通过（正向门槛、e随机） | False |
| C1 | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.1125 | -0.1064 | -0.3101 | 0.08312 | -0.1186 | -0.0699 | 7 | FAIL | -0.217 | -0.217 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.1045 | 0.09114 | -0.03507 | 0.2393 | 0.09502 | 0.1255 | 12 | PASS |  |  | same_account_exposed | PASS | 通过 | 不通过（正向门槛） | True |
| C1 | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.00137 | -0.009876 | -0.2139 | 0.2206 | -0.009498 | 0.04625 | 10 | PASS | -0.1031 | -0.1031 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e资本） | 不通过（c、d、f、正向门槛） | False |
| C1 | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.03224 | 0.03028 | -0.0182 | 0.08394 | 0.03224 | 0.03556 | 8 | PASS | -0.07222 | -0.07222 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| C1 | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.02625 | 0.02404 | -0.1984 | 0.1458 | -0.02549 | 0.03063 | 9 | PASS | -0.1307 | -0.1307 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| C1 | M_union3_v2 | INC1 | 0.25 | 5 | 0.03555 | 0.07215 | -0.1007 | 0.173 | 0.0064 | -0.004975 | 11 | FAIL | -0.05409 | -0.05409 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.1696 | 0.1773 | -0.01546 | 0.3613 | 0.06871 | 0.09116 | 12 | PASS | 0.07999 | 0.07999 | first_evaluation | PASS | 不通过（f） | 不通过（f） | False |
| C1 | M_union3_v2 | NATIVE | 0.25 | 5 | 0.08964 | 0.09268 | -0.06266 | 0.2459 | 0.04254 | 0.03047 | 12 | PASS |  |  | same_account_exposed | PASS | 不通过（正向门槛） | 不通过（正向门槛） | False |
| C1 | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.1652 | 0.1857 | -0.0345 | 0.3763 | 0.05509 | 0.06316 | 12 | PASS | 0.07554 | 0.07554 | first_evaluation | PASS | 不通过（f） | 不通过（f） | False |
| C1 | M_union3_v2 | RP3 | 0.25 | 5 | 0.01305 | 0.004054 | -0.03189 | 0.05926 | 0.01305 | 0.01005 | 11 | FAIL | -0.07659 | -0.07659 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| C1 | M_union3_v2 | SZL5 | 0.25 | 5 | -0.05162 | -0.05403 | -0.2646 | 0.16 | -0.1339 | -0.1258 | 8 | FAIL | -0.1413 | -0.1413 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.01715 | 0.04369 | -0.1179 | 0.1548 | -0.009748 | -0.02245 | 10 | FAIL | -0.05489 | -0.05489 | first_evaluation | PASS | 不通过（d、f、正向门槛、e资本、e随机） | 不通过（d、f、正向门槛、e随机） | False |
| C1 | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.1555 | 0.1447 | -0.02468 | 0.3374 | 0.06176 | 0.0744 | 12 | PASS | 0.08346 | 0.08346 | first_evaluation | PASS | 通过 | 通过 | False |
| C1 | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.07205 | 0.08064 | -0.07399 | 0.2168 | 0.03263 | 0.01425 | 10 | PASS |  |  | same_account_exposed | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| C1 | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.1526 | 0.1473 | -0.04438 | 0.3466 | 0.04796 | 0.0497 | 12 | PASS | 0.08059 | 0.08059 | first_evaluation | PASS | 不通过（f） | 不通过（f） | False |
| C1 | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.00119 | -0.00744 | -0.03962 | 0.04427 | 0.00119 | -0.0009616 | 9 | FAIL | -0.07086 | -0.07086 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| C1 | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.02526 | 0.01453 | -0.2121 | 0.1562 | -0.09905 | -0.09544 | 9 | FAIL | -0.0973 | -0.0973 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e资本、e随机） | False |
| M | A4b | INC1 | 0.25 | 5 | 0.1232 | 0.04958 | -0.07289 | 0.3303 | 0.1384 | 0.1445 | 11 | FAIL | -0.2154 | -0.1416 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、正向门槛、e随机） | False |
| M | A4b | INC1_HG10 | 0.25 | 5 | 0.1888 | 0.1395 | -0.05864 | 0.4124 | 0.1945 | 0.2289 | 11 | FAIL | -0.1499 | -0.07604 | first_evaluation | PASS | 不通过（c、d、e随机） | 不通过（c、d、e随机） | False |
| M | A4b | NATIVE | 0.25 | 5 | 0.3386 | 0.2736 | 0.1176 | 0.5664 | 0.3462 | 0.3521 | 14 | PASS |  | 0.07382 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | A4b | NATIVE_HG10 | 0.25 | 5 | 0.3479 | 0.2125 | 0.113 | 0.5916 | 0.3579 | 0.3797 | 12 | PASS | 0.009267 | 0.08309 | first_evaluation | PASS | 通过 | 通过 | False |
| M | A4b | RP3 | 0.25 | 5 | 0.0804 | 0.1039 | 0.001027 | 0.1645 | 0.0804 | 0.08056 | 10 | PASS | -0.2582 | -0.1844 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d） | False |
| M | A4b | SZL5 | 0.25 | 5 | 0.2483 | 0.1122 | 0.03211 | 0.4758 | 0.2632 | 0.2705 | 12 | FAIL | -0.09035 | -0.01653 | first_evaluation | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False |
| M | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1118 | 0.1358 | -0.06575 | 0.2965 | 0.1217 | 0.1257 | 12 | FAIL | -0.2282 | -0.1745 | first_evaluation | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False |
| M | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2176 | 0.143 | 0.004276 | 0.4178 | 0.2152 | 0.2404 | 12 | FAIL | -0.1224 | -0.06868 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| M | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.34 | 0.2745 | 0.1475 | 0.5325 | 0.3456 | 0.3408 | 15 | PASS |  | 0.0537 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.371 | 0.3839 | 0.1612 | 0.5794 | 0.3812 | 0.3836 | 12 | PASS | 0.03103 | 0.08473 | first_evaluation | PASS | 通过 | 通过 | False |
| M | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.06943 | 0.08925 | 0.000882 | 0.1387 | 0.06943 | 0.06759 | 10 | PASS | -0.2706 | -0.2169 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| M | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.2398 | 0.1384 | 0.03711 | 0.4456 | 0.2481 | 0.253 | 13 | PASS | -0.1002 | -0.04655 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_mean3_v2 | INC1 | 0.25 | 5 | 0.3977 | 0.3379 | 0.1925 | 0.6053 | 0.3944 | 0.4544 | 14 | PASS | -0.03838 | 0.1971 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.3382 | 0.2332 | 0.1108 | 0.5797 | 0.3284 | 0.4276 | 13 | FAIL | -0.09796 | 0.1376 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| M | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.4361 | 0.4186 | 0.1961 | 0.6759 | 0.4293 | 0.4951 | 13 | PASS |  | 0.2355 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.4293 | 0.341 | 0.1746 | 0.7063 | 0.4247 | 0.5226 | 13 | PASS | -0.006868 | 0.2286 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| M | M_mean3_v2 | RP3 | 0.25 | 5 | 0.1187 | 0.07533 | 0.02214 | 0.2133 | 0.1187 | 0.1295 | 11 | PASS | -0.3174 | -0.08192 | first_evaluation | PASS | 不通过（d） | 不通过（d、正向门槛） | False |
| M | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.3756 | 0.314 | 0.1205 | 0.6218 | 0.3727 | 0.4703 | 11 | FAIL | -0.06055 | 0.175 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| M | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2247 | 0.172 | 0.03871 | 0.4167 | 0.2218 | 0.2742 | 12 | PASS | 0.008202 | 0.1202 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.1566 | 0.1241 | -0.05568 | 0.3851 | 0.1422 | 0.2329 | 11 | PASS | -0.05994 | 0.0521 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| M | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.2165 | 0.2578 | -0.005673 | 0.4458 | 0.2137 | 0.2696 | 12 | PASS |  | 0.112 | same_account_exposed | PASS | 不通过（c、f） | 不通过（c、f） | False |
| M | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.1976 | 0.1692 | -0.05168 | 0.4646 | 0.1866 | 0.2783 | 11 | PASS | -0.0189 | 0.09313 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| M | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.01163 | 0.01061 | -0.06285 | 0.08551 | 0.01163 | 0.01876 | 8 | FAIL | -0.2049 | -0.09283 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| M | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.1803 | 0.173 | -0.05175 | 0.4166 | 0.1802 | 0.2702 | 11 | PASS | -0.03617 | 0.07587 | first_evaluation | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False |
| M | M_union3_v2 | INC1 | 0.25 | 5 | 0.2595 | 0.2783 | 0.06196 | 0.4666 | 0.1492 | 0.1901 | 12 | PASS | -0.1385 | 0.1698 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.2833 | 0.2853 | 0.06601 | 0.4978 | 0.1202 | 0.1746 | 14 | MC_UNRESOLVED | -0.1147 | 0.1936 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| M | M_union3_v2 | NATIVE | 0.25 | 5 | 0.398 | 0.2775 | 0.1808 | 0.615 | 0.2507 | 0.3111 | 13 | PASS |  | 0.3084 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.3104 | 0.3448 | 0.04982 | 0.5717 | 0.1293 | 0.1844 | 12 | PASS | -0.08756 | 0.2208 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2 | RP3 | 0.25 | 5 | 0.04687 | 0.05325 | -0.01152 | 0.101 | 0.04687 | 0.03928 | 10 | FAIL | -0.3511 | -0.04277 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| M | M_union3_v2 | SZL5 | 0.25 | 5 | 0.3308 | 0.2388 | 0.1182 | 0.5691 | 0.1725 | 0.2336 | 14 | PASS | -0.06722 | 0.2411 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2577 | 0.287 | 0.07197 | 0.4523 | 0.1482 | 0.1885 | 11 | PASS | -0.1191 | 0.1856 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| M | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3035 | 0.3393 | 0.1005 | 0.5104 | 0.1428 | 0.1913 | 15 | MC_UNRESOLVED | -0.07329 | 0.2315 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| M | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3768 | 0.3079 | 0.1588 | 0.5886 | 0.2397 | 0.2903 | 14 | PASS |  | 0.3048 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.3473 | 0.4264 | 0.09834 | 0.5926 | 0.1688 | 0.2166 | 14 | PASS | -0.02949 | 0.2753 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.05518 | 0.04137 | 0.001627 | 0.1068 | 0.05518 | 0.04858 | 12 | FAIL | -0.3216 | -0.01687 | first_evaluation | PASS | 不通过（正向门槛、e随机） | 不通过（正向门槛、e随机） | False |
| M | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.34 | 0.3027 | 0.1414 | 0.5592 | 0.186 | 0.2437 | 14 | PASS | -0.03683 | 0.2679 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | A4b | INC1 | 0.25 | 5 | 0.1974 | 0.1573 | -0.03012 | 0.4159 | 0.2034 | 0.2552 | 11 | FAIL | -0.1657 | -0.06739 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| Q | A4b | INC1_HG10 | 0.25 | 5 | 0.2725 | 0.1948 | -0.02394 | 0.5488 | 0.2762 | 0.3561 | 11 | FAIL | -0.09065 | 0.007678 | first_evaluation | PASS | 不通过（c、d、e随机） | 不通过（c、d、e随机） | False |
| Q | A4b | NATIVE | 0.25 | 5 | 0.3631 | 0.2695 | 0.1178 | 0.6074 | 0.3678 | 0.4301 | 12 | PASS |  | 0.09833 | related_exposed | PASS | 通过 | 通过 | False |
| Q | A4b | NATIVE_HG10 | 0.25 | 5 | 0.5279 | 0.4851 | 0.2413 | 0.8061 | 0.5331 | 0.6251 | 14 | PASS | 0.1648 | 0.2631 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | A4b | RP3 | 0.25 | 5 | 0.165 | 0.2136 | 0.05828 | 0.2607 | 0.165 | 0.1784 | 13 | PASS | -0.1981 | -0.09981 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | A4b | SZL5 | 0.25 | 5 | 0.1683 | 0.1394 | -0.05735 | 0.3757 | 0.1837 | 0.244 | 11 | FAIL | -0.1948 | -0.0965 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| Q | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1879 | 0.1204 | -0.02715 | 0.3904 | 0.1622 | 0.2257 | 11 | FAIL | -0.1758 | -0.09839 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| Q | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2386 | 0.1158 | -0.03909 | 0.489 | 0.2139 | 0.2883 | 12 | FAIL | -0.1251 | -0.04769 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| Q | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.3638 | 0.2874 | 0.1376 | 0.5732 | 0.346 | 0.4006 | 12 | PASS |  | 0.07746 | same_account_exposed | PASS | 通过 | 通过 | False |
| Q | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.5176 | 0.5256 | 0.2634 | 0.7718 | 0.4858 | 0.5728 | 13 | PASS | 0.1538 | 0.2313 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.1344 | 0.1481 | 0.04428 | 0.2225 | 0.1344 | 0.1432 | 11 | PASS | -0.2294 | -0.152 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| Q | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.1393 | 0.08961 | -0.06583 | 0.332 | 0.1252 | 0.1917 | 10 | FAIL | -0.2244 | -0.147 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| Q | M_mean3_v2 | INC1 | 0.25 | 5 | 0.2682 | 0.2419 | 0.06332 | 0.4805 | 0.2709 | 0.4345 | 13 | PASS | -0.04979 | 0.06757 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| Q | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.2153 | 0.2007 | -0.05116 | 0.4861 | 0.228 | 0.4097 | 11 | PASS | -0.1026 | 0.01471 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| Q | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.318 | 0.1509 | 0.06691 | 0.5805 | 0.3278 | 0.5171 | 10 | PASS |  | 0.1174 | related_exposed | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False |
| Q | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.2922 | 0.1053 | -0.0002321 | 0.5957 | 0.3124 | 0.5217 | 9 | PASS | -0.02582 | 0.09154 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| Q | M_mean3_v2 | RP3 | 0.25 | 5 | 0.157 | 0.1219 | 0.02507 | 0.2841 | 0.157 | 0.2143 | 12 | PASS | -0.161 | -0.04359 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| Q | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.3539 | 0.2182 | 0.08788 | 0.6125 | 0.361 | 0.5822 | 13 | PASS | 0.03593 | 0.1533 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| Q | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | -0.07264 | -0.03039 | -0.2838 | 0.1367 | -0.07703 | 0.07222 | 7 | FAIL | 0.02254 | -0.1771 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| Q | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.0359 | 0.06857 | -0.2929 | 0.2169 | -0.03624 | 0.1291 | 7 | PASS | 0.05927 | -0.1404 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | -0.09518 | -0.171 | -0.3332 | 0.1615 | -0.09628 | 0.08211 | 5 | PASS |  | -0.1996 | related_exposed | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | -0.05299 | -0.06691 | -0.332 | 0.234 | -0.051 | 0.1477 | 6 | PASS | 0.04218 | -0.1575 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | -0.009236 | -0.005467 | -0.1218 | 0.1075 | -0.009236 | 0.03193 | 7 | FAIL | 0.08594 | -0.1137 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| Q | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.1288 | -0.1459 | -0.3646 | 0.119 | -0.1377 | 0.07605 | 6 | PASS | -0.03362 | -0.2333 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_union3_v2 | INC1 | 0.25 | 5 | 0.1757 | 0.04392 | -0.003759 | 0.3493 | 0.01306 | 0.1249 | 10 | FAIL | -0.05185 | 0.08609 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、正向门槛、e资本、e随机） | False |
| Q | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.3813 | 0.4576 | 0.1571 | 0.5919 | 0.1495 | 0.2919 | 13 | PASS | 0.1537 | 0.2917 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | M_union3_v2 | NATIVE | 0.25 | 5 | 0.2276 | 0.265 | 0.02649 | 0.435 | 0.004184 | 0.1169 | 10 | PASS |  | 0.1379 | related_exposed | PASS | 不通过（d、f） | 不通过（d、f） | False |
| Q | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.5354 | 0.6264 | 0.2958 | 0.77 | 0.2134 | 0.3778 | 14 | PASS | 0.3078 | 0.4458 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | M_union3_v2 | RP3 | 0.25 | 5 | 0.01474 | 0.0004187 | -0.03288 | 0.06085 | 0.01474 | 0.01866 | 12 | MC_UNRESOLVED | -0.2128 | -0.0749 | first_evaluation | PASS | 不通过（正向门槛） | 不通过（正向门槛） | False |
| Q | M_union3_v2 | SZL5 | 0.25 | 5 | 0.1543 | 0.07127 | -0.06497 | 0.3644 | -0.1164 | 0.04941 | 8 | MC_UNRESOLVED | -0.0733 | 0.06464 | first_evaluation | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、正向门槛、e资本） | False |
| Q | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.1689 | 0.06355 | -0.01053 | 0.3354 | -0.005782 | 0.1099 | 8 | FAIL | -0.08217 | 0.0968 | first_evaluation | PASS | 不通过（d、e资本、e随机） | 不通过（d、正向门槛、e资本、e随机） | False |
| Q | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3636 | 0.4359 | 0.1469 | 0.5628 | 0.1242 | 0.2628 | 11 | PASS | 0.1126 | 0.2916 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| Q | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.251 | 0.3142 | 0.05259 | 0.453 | 0.01981 | 0.1315 | 12 | PASS |  | 0.179 | related_exposed | PASS | 通过 | 通过 | False |
| Q | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.5357 | 0.6555 | 0.3049 | 0.762 | 0.2051 | 0.3633 | 13 | PASS | 0.2847 | 0.4637 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.01083 | 0.01371 | -0.03572 | 0.05664 | 0.01083 | 0.01423 | 11 | PASS | -0.2402 | -0.06122 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| Q | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.2018 | 0.1657 | 0.002061 | 0.4021 | -0.07678 | 0.08688 | 9 | PASS | -0.04917 | 0.1298 | first_evaluation | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False |
| S | A4b | INC1 | 0.25 | 5 | 0.08125 | 0.03575 | -0.182 | 0.316 | 0.08413 | 0.1401 | 9 | FAIL | -0.3184 | -0.1836 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | A4b | INC1_HG10 | 0.25 | 5 | 0.3096 | 0.2318 | 0.01812 | 0.5834 | 0.3166 | 0.3913 | 11 | FAIL | -0.09011 | 0.04475 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| S | A4b | NATIVE | 0.25 | 5 | 0.3997 | 0.3777 | 0.1498 | 0.6517 | 0.4052 | 0.4669 | 12 | PASS |  | 0.1349 | same_account_exposed | PASS | 通过 | 通过 | False |
| S | A4b | NATIVE_HG10 | 0.25 | 5 | 0.4139 | 0.3352 | 0.1192 | 0.7094 | 0.4235 | 0.5146 | 12 | PASS | 0.0142 | 0.1491 | first_evaluation | PASS | 通过 | 通过 | False |
| S | A4b | RP3 | 0.25 | 5 | 0.1341 | 0.132 | 0.03198 | 0.23 | 0.1341 | 0.1476 | 10 | PASS | -0.2656 | -0.1307 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| S | A4b | SZL5 | 0.25 | 5 | 0.07851 | 0.08158 | -0.1723 | 0.3188 | 0.09533 | 0.1514 | 10 | FAIL | -0.3212 | -0.1863 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1428 | 0.118 | -0.09349 | 0.3519 | 0.1123 | 0.1847 | 10 | FAIL | -0.2816 | -0.1435 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| S | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2624 | 0.1307 | -0.00494 | 0.513 | 0.239 | 0.3167 | 11 | FAIL | -0.162 | -0.02388 | first_evaluation | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False |
| S | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.4244 | 0.3578 | 0.2037 | 0.6299 | 0.4003 | 0.4661 | 13 | PASS |  | 0.1381 | same_account_exposed | PASS | 通过 | 通过 | False |
| S | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.4176 | 0.4411 | 0.1467 | 0.69 | 0.4005 | 0.4798 | 12 | PASS | -0.00678 | 0.1313 | first_evaluation | PASS | 通过 | 通过 | False |
| S | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.1102 | 0.1287 | 0.01884 | 0.197 | 0.1102 | 0.1185 | 12 | PASS | -0.3142 | -0.1761 | first_evaluation | PASS | 通过 | 通过 | False |
| S | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.1414 | 0.08738 | -0.0766 | 0.3438 | 0.1183 | 0.1962 | 9 | FAIL | -0.283 | -0.1449 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_mean3_v2 | INC1 | 0.25 | 5 | 0.2785 | 0.1308 | 0.05481 | 0.5142 | 0.2835 | 0.4437 | 12 | MC_UNRESOLVED | -0.06625 | 0.07789 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False |
| S | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.1936 | 0.1127 | -0.08192 | 0.4596 | 0.2019 | 0.3867 | 10 | PASS | -0.1512 | -0.007023 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| S | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.3448 | 0.2127 | 0.08606 | 0.6127 | 0.3502 | 0.5437 | 12 | PASS |  | 0.1441 | same_account_exposed | PASS | 不通过（c） | 不通过（c） | False |
| S | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.313 | 0.1216 | 0.01307 | 0.6066 | 0.3267 | 0.5408 | 9 | PASS | -0.03177 | 0.1124 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| S | M_mean3_v2 | RP3 | 0.25 | 5 | 0.2204 | 0.2108 | 0.1022 | 0.3388 | 0.2204 | 0.2763 | 13 | PASS | -0.1243 | 0.01982 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.1754 | 0.03933 | -0.09069 | 0.4579 | 0.1843 | 0.4015 | 10 | FAIL | -0.1693 | -0.0252 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | -0.03874 | -0.05733 | -0.2481 | 0.1745 | -0.04475 | 0.1062 | 6 | FAIL | -0.03297 | -0.1432 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.09065 | -0.009104 | -0.3398 | 0.1548 | -0.1008 | 0.07603 | 6 | FAIL | -0.08487 | -0.1951 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e资本、e随机） | False |
| S | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | -0.005773 | -0.06165 | -0.2485 | 0.247 | -0.00439 | 0.173 | 8 | PASS |  | -0.1102 | same_account_exposed | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| S | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | -0.08456 | -0.1577 | -0.3562 | 0.2011 | -0.08925 | 0.1173 | 7 | PASS | -0.07878 | -0.189 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| S | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.06107 | 0.03759 | -0.04222 | 0.1648 | 0.06107 | 0.102 | 9 | PASS | 0.06684 | -0.04339 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| S | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.231 | -0.2775 | -0.4855 | 0.03084 | -0.2383 | -0.02566 | 7 | FAIL | -0.2252 | -0.3355 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_union3_v2 | INC1 | 0.25 | 5 | 0.1842 | 0.162 | -0.007725 | 0.3661 | 0.03547 | 0.1348 | 12 | MC_UNRESOLVED | -0.1336 | 0.09456 | first_evaluation | PASS | 不可判（e随机:MC_UNRESOLVED） | 不通过（e资本） | True |
| S | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.3984 | 0.3503 | 0.1868 | 0.6027 | 0.148 | 0.3032 | 15 | FAIL | 0.08065 | 0.3088 | first_evaluation | PASS | 不通过（e随机） | 不通过（e随机） | False |
| S | M_union3_v2 | NATIVE | 0.25 | 5 | 0.3178 | 0.271 | 0.1204 | 0.5191 | 0.06444 | 0.2039 | 13 | PASS |  | 0.2282 | same_account_exposed | PASS | 不通过（f） | 不通过（f） | False |
| S | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.4324 | 0.4134 | 0.2008 | 0.6539 | 0.09695 | 0.2664 | 14 | PASS | 0.1146 | 0.3428 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_union3_v2 | RP3 | 0.25 | 5 | 0.01587 | 0.004026 | -0.03517 | 0.06561 | 0.01587 | 0.01965 | 11 | FAIL | -0.3019 | -0.07376 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| S | M_union3_v2 | SZL5 | 0.25 | 5 | 0.1094 | 0.03241 | -0.1109 | 0.3209 | -0.1559 | -0.009295 | 9 | FAIL | -0.2084 | 0.01974 | first_evaluation | PASS | 不通过（c、d、f、e资本、e随机） | 不通过（c、d、f、正向门槛、e资本、e随机） | False |
| S | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2101 | 0.2426 | 0.02444 | 0.3802 | 0.04257 | 0.1535 | 13 | PASS | -0.1386 | 0.138 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3916 | 0.4481 | 0.1765 | 0.5906 | 0.1351 | 0.2837 | 12 | PASS | 0.04289 | 0.3195 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3487 | 0.3481 | 0.1639 | 0.5396 | 0.08027 | 0.2279 | 12 | PASS |  | 0.2767 | same_account_exposed | PASS | 通过 | 通过 | False |
| S | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.44 | 0.49 | 0.2019 | 0.6616 | 0.09191 | 0.2616 | 14 | PASS | 0.09127 | 0.3679 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.003435 | -0.00127 | -0.04276 | 0.05014 | 0.003435 | 0.006165 | 9 | FAIL | -0.3453 | -0.06861 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| S | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.1666 | 0.1094 | -0.04141 | 0.3695 | -0.1125 | 0.04038 | 11 | PASS | -0.1821 | 0.09452 | first_evaluation | PASS | 不通过（d、f、e资本） | 不通过（d、f、e资本） | False |
| SM | A4b | NATIVE | 0.25 | 5 | 0.2996 | 0.2374 | 0.06651 | 0.5287 | 0.3078 | 0.3298 | 11 | MC_UNRESOLVED |  | 0.03475 | same_account_exposed | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False |
| SM | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.2566 | 0.1949 | 0.05383 | 0.4491 | 0.2426 | 0.2695 | 13 | PASS |  | -0.02975 | same_account_exposed | PASS | 通过 | 通过 | False |
| SM | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.4969 | 0.4043 | 0.2813 | 0.7331 | 0.4962 | 0.6275 | 15 | PASS |  | 0.2963 | same_account_exposed | PASS | 不通过（c） | 不通过（c） | False |
| SM | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.1814 | 0.1383 | -0.03136 | 0.4078 | 0.1738 | 0.2958 | 13 | PASS |  | 0.07694 | same_account_exposed | PASS | 不通过（c、f） | 不通过（c、f） | False |
| SM | M_union3_v2 | NATIVE | 0.25 | 5 | 0.3699 | 0.3221 | 0.1824 | 0.5623 | 0.1812 | 0.2567 | 13 | PASS |  | 0.2802 | same_account_exposed | PASS | 通过 | 通过 | False |
| SM | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3634 | 0.3373 | 0.1836 | 0.5513 | 0.1663 | 0.2469 | 12 | PASS |  | 0.2914 | same_account_exposed | PASS | 通过 | 通过 | False |


## profile EXEC_LEADER_VS_PARENT

> 表头：主体=144 主展示 + C1_hi + SM 锚｜算子=见列｜分母=四段有效配对日（FULL = n 加权；G4 = 段中位）｜基准=同 H 原父（8bp）｜子集=primary144 | c1_hi | sm_anchor｜单位=年化百分点 / 判词｜日期=2010-01-04..2026-03-27（四段；2026 partial）｜H=H 见列｜成本模型=源 8bp（f：A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（e 资本：MATCH-CAP）｜exposure=见 evidence_exposure 列｜query_id=E6K-P3-POL-EXECLEADERVSPARENT


| meas | mother | op | alpha | H | FULL | G4 | ci_L20_lo | ci_L20_hi | FULL_sc | FULL_imp | years_pos | e_rand | FULL_vs_native | FULL_vs_nativeC1 | evidence_exposure | size_EXEC_LEADER_VS_PARENT | policy_EXEC_LEADER_VS_PARENT_FULL | policy_EXEC_LEADER_VS_PARENT_G4 | POLICY_INTERPRETATION_PENDING_EXEC_LEADER_VS_PARENT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | A4b | INC1 | 0.25 | 5 | 0.1993 | 0.1666 | 0.03081 | 0.3619 | 0.2035 | 0.2056 | 13 | MC_UNRESOLVED | -0.06553 | -0.06553 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | A4b | INC1_HG10 | 0.25 | 5 | 0.2376 | 0.3176 | 0.01428 | 0.453 | 0.2399 | 0.2533 | 11 | FAIL | -0.02717 | -0.02717 | first_evaluation | FAIL | 不通过（d、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | A4b | NATIVE | 0.25 | 5 | 0.2648 | 0.311 | 0.07639 | 0.4442 | 0.2649 | 0.2738 | 13 | PASS |  |  | same_account_exposed | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | A4b | NATIVE | 0.5 | 10 | 0.4742 | 0.5273 | 0.19 | 0.755 | 0.4401 | 0.4511 | 14 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b | NATIVE | 0.5 | 20 | 0.3358 | 0.3565 | 0.1394 | 0.5252 | 0.3152 | 0.3247 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b | NATIVE_HG10 | 0.25 | 5 | 0.2929 | 0.2275 | 0.04494 | 0.5338 | 0.2869 | 0.309 | 10 | PASS | 0.02809 | 0.02809 | first_evaluation | FAIL | 不通过（d、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | A4b | RP3 | 0.25 | 5 | 0.02682 | 0.01826 | -0.04199 | 0.0943 | 0.02682 | 0.02785 | 11 | PASS | -0.238 | -0.238 | first_evaluation | FAIL | 不通过（d、正向门槛、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、正向门槛、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | A4b | SZL5 | 0.25 | 5 | 0.1258 | 0.03719 | -0.0705 | 0.3107 | 0.1328 | 0.1327 | 10 | PASS | -0.139 | -0.139 | first_evaluation | PASS | 不通过（d） | 不通过（d、正向门槛） | False |
| C1 | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1824 | 0.2094 | 0.03225 | 0.32 | 0.1639 | 0.1768 | 12 | FAIL | -0.1039 | -0.1039 | first_evaluation | FAIL | 不通过（e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2232 | 0.3032 | 0.02851 | 0.4113 | 0.2118 | 0.2213 | 10 | FAIL | -0.06307 | -0.06307 | first_evaluation | FAIL | 不通过（d、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.2863 | 0.3224 | 0.1182 | 0.4473 | 0.2728 | 0.2809 | 14 | PASS |  |  | same_account_exposed | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | A4b_CVRv5 | NATIVE | 0.5 | 10 | 0.4206 | 0.3958 | 0.1749 | 0.6575 | 0.4056 | 0.3929 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b_CVRv5 | NATIVE | 0.5 | 20 | 0.2857 | 0.2776 | 0.1175 | 0.456 | 0.2734 | 0.2736 | 15 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.2387 | 0.2548 | 0.02666 | 0.4464 | 0.2218 | 0.2312 | 11 | PASS | -0.04761 | -0.04761 | first_evaluation | FAIL | 不通过（d、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.03286 | 0.03379 | -0.02538 | 0.0921 | 0.03286 | 0.0335 | 11 | PASS | -0.2534 | -0.2534 | first_evaluation | FAIL | 不通过（d、正向门槛、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、正向门槛、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.124 | 0.07449 | -0.04594 | 0.2898 | 0.1211 | 0.1234 | 11 | FAIL | -0.1623 | -0.1623 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_mean3_v2 | INC1 | 0.25 | 5 | 0.1792 | 0.0971 | 0.04069 | 0.319 | 0.1741 | 0.1999 | 13 | FAIL | -0.02146 | -0.02146 | first_evaluation | FAIL | 不通过（e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.06166 | 0.008405 | -0.1416 | 0.2776 | 0.05662 | 0.1124 | 11 | FAIL | -0.139 | -0.139 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.2006 | 0.1498 | 0.04456 | 0.3478 | 0.1946 | 0.2267 | 13 | PASS |  |  | same_account_exposed | PASS | 通过 | 通过 | False |
| C1 | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.1979 | 0.111 | -0.03353 | 0.4343 | 0.1943 | 0.254 | 12 | FAIL | -0.002698 | -0.002698 | first_evaluation | PASS | 不通过（c、e随机） | 不通过（c、e随机） | False |
| C1 | M_mean3_v2 | RP3 | 0.25 | 5 | 0.07358 | 0.06543 | 0.02002 | 0.1256 | 0.07358 | 0.07844 | 9 | FAIL | -0.127 | -0.127 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| C1 | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.1672 | 0.1965 | -0.03337 | 0.3789 | 0.1737 | 0.2275 | 10 | FAIL | -0.03339 | -0.03339 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| C1 | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.08837 | 0.07339 | -0.0385 | 0.2151 | 0.0802 | 0.1053 | 12 | FAIL | -0.01609 | -0.01609 | first_evaluation | FAIL | 不通过（正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.1125 | -0.1064 | -0.3101 | 0.08312 | -0.1186 | -0.0699 | 7 | FAIL | -0.217 | -0.217 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.1045 | 0.09114 | -0.03507 | 0.2393 | 0.09502 | 0.1255 | 12 | PASS |  |  | same_account_exposed | PASS | 通过 | 不通过（正向门槛） | True |
| C1 | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.00137 | -0.009876 | -0.2139 | 0.2206 | -0.009498 | 0.04625 | 10 | PASS | -0.1031 | -0.1031 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e资本） | 不通过（c、d、f、正向门槛） | False |
| C1 | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.03224 | 0.03028 | -0.0182 | 0.08394 | 0.03224 | 0.03556 | 8 | PASS | -0.07222 | -0.07222 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| C1 | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.02625 | 0.02404 | -0.1984 | 0.1458 | -0.02549 | 0.03063 | 9 | PASS | -0.1307 | -0.1307 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| C1 | M_union3_v2 | INC1 | 0.25 | 5 | 0.03555 | 0.07215 | -0.1007 | 0.173 | 0.0064 | -0.004975 | 11 | FAIL | -0.05409 | -0.05409 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.1696 | 0.1773 | -0.01546 | 0.3613 | 0.06871 | 0.09116 | 12 | PASS | 0.07999 | 0.07999 | first_evaluation | FAIL | 不通过（f、size(EXEC_LEADER_VS_PARENT)） | 不通过（f、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | M_union3_v2 | NATIVE | 0.25 | 5 | 0.08964 | 0.09268 | -0.06266 | 0.2459 | 0.04254 | 0.03047 | 12 | PASS |  |  | same_account_exposed | FAIL | 不通过（正向门槛、size(EXEC_LEADER_VS_PARENT)） | 不通过（正向门槛、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.1652 | 0.1857 | -0.0345 | 0.3763 | 0.05509 | 0.06316 | 12 | PASS | 0.07554 | 0.07554 | first_evaluation | FAIL | 不通过（f、size(EXEC_LEADER_VS_PARENT)） | 不通过（f、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | M_union3_v2 | RP3 | 0.25 | 5 | 0.01305 | 0.004054 | -0.03189 | 0.05926 | 0.01305 | 0.01005 | 11 | FAIL | -0.07659 | -0.07659 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| C1 | M_union3_v2 | SZL5 | 0.25 | 5 | -0.05162 | -0.05403 | -0.2646 | 0.16 | -0.1339 | -0.1258 | 8 | FAIL | -0.1413 | -0.1413 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| C1 | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.01715 | 0.04369 | -0.1179 | 0.1548 | -0.009748 | -0.02245 | 10 | FAIL | -0.05489 | -0.05489 | first_evaluation | FAIL | 不通过（d、f、正向门槛、e资本、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.1555 | 0.1447 | -0.02468 | 0.3374 | 0.06176 | 0.0744 | 12 | PASS | 0.08346 | 0.08346 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.07205 | 0.08064 | -0.07399 | 0.2168 | 0.03263 | 0.01425 | 10 | PASS |  |  | same_account_exposed | FAIL | 不通过（d、正向门槛、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、正向门槛、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.1526 | 0.1473 | -0.04438 | 0.3466 | 0.04796 | 0.0497 | 12 | PASS | 0.08059 | 0.08059 | first_evaluation | FAIL | 不通过（f、size(EXEC_LEADER_VS_PARENT)） | 不通过（f、size(EXEC_LEADER_VS_PARENT)） | False |
| C1 | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.00119 | -0.00744 | -0.03962 | 0.04427 | 0.00119 | -0.0009616 | 9 | FAIL | -0.07086 | -0.07086 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| C1 | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.02526 | 0.01453 | -0.2121 | 0.1562 | -0.09905 | -0.09544 | 9 | FAIL | -0.0973 | -0.0973 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e资本、e随机） | False |
| M | A4b | INC1 | 0.25 | 5 | 0.1232 | 0.04958 | -0.07289 | 0.3303 | 0.1384 | 0.1445 | 11 | FAIL | -0.2154 | -0.1416 | first_evaluation | FAIL | 不通过（d、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| M | A4b | INC1_HG10 | 0.25 | 5 | 0.1888 | 0.1395 | -0.05864 | 0.4124 | 0.1945 | 0.2289 | 11 | FAIL | -0.1499 | -0.07604 | first_evaluation | FAIL | 不通过（c、d、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| M | A4b | NATIVE | 0.25 | 5 | 0.3386 | 0.2736 | 0.1176 | 0.5664 | 0.3462 | 0.3521 | 14 | PASS |  | 0.07382 | same_account_exposed | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| M | A4b | NATIVE_HG10 | 0.25 | 5 | 0.3479 | 0.2125 | 0.113 | 0.5916 | 0.3579 | 0.3797 | 12 | PASS | 0.009267 | 0.08309 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| M | A4b | RP3 | 0.25 | 5 | 0.0804 | 0.1039 | 0.001027 | 0.1645 | 0.0804 | 0.08056 | 10 | PASS | -0.2582 | -0.1844 | first_evaluation | FAIL | 不通过（d、正向门槛、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、size(EXEC_LEADER_VS_PARENT)） | False |
| M | A4b | SZL5 | 0.25 | 5 | 0.2483 | 0.1122 | 0.03211 | 0.4758 | 0.2632 | 0.2705 | 12 | FAIL | -0.09035 | -0.01653 | first_evaluation | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False |
| M | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1118 | 0.1358 | -0.06575 | 0.2965 | 0.1217 | 0.1257 | 12 | FAIL | -0.2282 | -0.1745 | first_evaluation | FAIL | 不通过（c、f、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、f、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| M | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2176 | 0.143 | 0.004276 | 0.4178 | 0.2152 | 0.2404 | 12 | FAIL | -0.1224 | -0.06868 | first_evaluation | FAIL | 不通过（e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| M | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.34 | 0.2745 | 0.1475 | 0.5325 | 0.3456 | 0.3408 | 15 | PASS |  | 0.0537 | same_account_exposed | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| M | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.371 | 0.3839 | 0.1612 | 0.5794 | 0.3812 | 0.3836 | 12 | PASS | 0.03103 | 0.08473 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| M | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.06943 | 0.08925 | 0.000882 | 0.1387 | 0.06943 | 0.06759 | 10 | PASS | -0.2706 | -0.2169 | first_evaluation | FAIL | 不通过（d、正向门槛、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、正向门槛、size(EXEC_LEADER_VS_PARENT)） | False |
| M | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.2398 | 0.1384 | 0.03711 | 0.4456 | 0.2481 | 0.253 | 13 | PASS | -0.1002 | -0.04655 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_mean3_v2 | INC1 | 0.25 | 5 | 0.3977 | 0.3379 | 0.1925 | 0.6053 | 0.3944 | 0.4544 | 14 | PASS | -0.03838 | 0.1971 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| M | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.3382 | 0.2332 | 0.1108 | 0.5797 | 0.3284 | 0.4276 | 13 | FAIL | -0.09796 | 0.1376 | first_evaluation | FAIL | 不通过（e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| M | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.4361 | 0.4186 | 0.1961 | 0.6759 | 0.4293 | 0.4951 | 13 | PASS |  | 0.2355 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.4293 | 0.341 | 0.1746 | 0.7063 | 0.4247 | 0.5226 | 13 | PASS | -0.006868 | 0.2286 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| M | M_mean3_v2 | RP3 | 0.25 | 5 | 0.1187 | 0.07533 | 0.02214 | 0.2133 | 0.1187 | 0.1295 | 11 | PASS | -0.3174 | -0.08192 | first_evaluation | PASS | 不通过（d） | 不通过（d、正向门槛） | False |
| M | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.3756 | 0.314 | 0.1205 | 0.6218 | 0.3727 | 0.4703 | 11 | FAIL | -0.06055 | 0.175 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False |
| M | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2247 | 0.172 | 0.03871 | 0.4167 | 0.2218 | 0.2742 | 12 | PASS | 0.008202 | 0.1202 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| M | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.1566 | 0.1241 | -0.05568 | 0.3851 | 0.1422 | 0.2329 | 11 | PASS | -0.05994 | 0.0521 | first_evaluation | PASS | 不通过（d） | 不通过（d） | False |
| M | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.2165 | 0.2578 | -0.005673 | 0.4458 | 0.2137 | 0.2696 | 12 | PASS |  | 0.112 | same_account_exposed | PASS | 不通过（c、f） | 不通过（c、f） | False |
| M | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.1976 | 0.1692 | -0.05168 | 0.4646 | 0.1866 | 0.2783 | 11 | PASS | -0.0189 | 0.09313 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| M | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.01163 | 0.01061 | -0.06285 | 0.08551 | 0.01163 | 0.01876 | 8 | FAIL | -0.2049 | -0.09283 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| M | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.1803 | 0.173 | -0.05175 | 0.4166 | 0.1802 | 0.2702 | 11 | PASS | -0.03617 | 0.07587 | first_evaluation | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False |
| M | M_union3_v2 | INC1 | 0.25 | 5 | 0.2595 | 0.2783 | 0.06196 | 0.4666 | 0.1492 | 0.1901 | 12 | PASS | -0.1385 | 0.1698 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| M | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.2833 | 0.2853 | 0.06601 | 0.4978 | 0.1202 | 0.1746 | 14 | MC_UNRESOLVED | -0.1147 | 0.1936 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| M | M_union3_v2 | NATIVE | 0.25 | 5 | 0.398 | 0.2775 | 0.1808 | 0.615 | 0.2507 | 0.3111 | 13 | PASS |  | 0.3084 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.3104 | 0.3448 | 0.04982 | 0.5717 | 0.1293 | 0.1844 | 12 | PASS | -0.08756 | 0.2208 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| M | M_union3_v2 | RP3 | 0.25 | 5 | 0.04687 | 0.05325 | -0.01152 | 0.101 | 0.04687 | 0.03928 | 10 | FAIL | -0.3511 | -0.04277 | first_evaluation | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False |
| M | M_union3_v2 | SZL5 | 0.25 | 5 | 0.3308 | 0.2388 | 0.1182 | 0.5691 | 0.1725 | 0.2336 | 14 | PASS | -0.06722 | 0.2411 | first_evaluation | PASS | 通过 | 通过 | False |
| M | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2577 | 0.287 | 0.07197 | 0.4523 | 0.1482 | 0.1885 | 11 | PASS | -0.1191 | 0.1856 | first_evaluation | FAIL | 不通过（d、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、size(EXEC_LEADER_VS_PARENT)） | False |
| M | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3035 | 0.3393 | 0.1005 | 0.5104 | 0.1428 | 0.1913 | 15 | MC_UNRESOLVED | -0.07329 | 0.2315 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| M | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3768 | 0.3079 | 0.1588 | 0.5886 | 0.2397 | 0.2903 | 14 | PASS |  | 0.3048 | same_account_exposed | PASS | 通过 | 通过 | False |
| M | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.3473 | 0.4264 | 0.09834 | 0.5926 | 0.1688 | 0.2166 | 14 | PASS | -0.02949 | 0.2753 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| M | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.05518 | 0.04137 | 0.001627 | 0.1068 | 0.05518 | 0.04858 | 12 | FAIL | -0.3216 | -0.01687 | first_evaluation | PASS | 不通过（正向门槛、e随机） | 不通过（正向门槛、e随机） | False |
| M | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.34 | 0.3027 | 0.1414 | 0.5592 | 0.186 | 0.2437 | 14 | PASS | -0.03683 | 0.2679 | first_evaluation | PASS | 通过 | 通过 | False |
| Q | A4b | INC1 | 0.25 | 5 | 0.1974 | 0.1573 | -0.03012 | 0.4159 | 0.2034 | 0.2552 | 11 | FAIL | -0.1657 | -0.06739 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | A4b | INC1_HG10 | 0.25 | 5 | 0.2725 | 0.1948 | -0.02394 | 0.5488 | 0.2762 | 0.3561 | 11 | FAIL | -0.09065 | 0.007678 | first_evaluation | FAIL | 不通过（c、d、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | A4b | NATIVE | 0.25 | 5 | 0.3631 | 0.2695 | 0.1178 | 0.6074 | 0.3678 | 0.4301 | 12 | PASS |  | 0.09833 | related_exposed | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| Q | A4b | NATIVE_HG10 | 0.25 | 5 | 0.5279 | 0.4851 | 0.2413 | 0.8061 | 0.5331 | 0.6251 | 14 | PASS | 0.1648 | 0.2631 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| Q | A4b | RP3 | 0.25 | 5 | 0.165 | 0.2136 | 0.05828 | 0.2607 | 0.165 | 0.1784 | 13 | PASS | -0.1981 | -0.09981 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| Q | A4b | SZL5 | 0.25 | 5 | 0.1683 | 0.1394 | -0.05735 | 0.3757 | 0.1837 | 0.244 | 11 | FAIL | -0.1948 | -0.0965 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1879 | 0.1204 | -0.02715 | 0.3904 | 0.1622 | 0.2257 | 11 | FAIL | -0.1758 | -0.09839 | first_evaluation | FAIL | 不通过（d、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2386 | 0.1158 | -0.03909 | 0.489 | 0.2139 | 0.2883 | 12 | FAIL | -0.1251 | -0.04769 | first_evaluation | FAIL | 不通过（e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.3638 | 0.2874 | 0.1376 | 0.5732 | 0.346 | 0.4006 | 12 | PASS |  | 0.07746 | same_account_exposed | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| Q | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.5176 | 0.5256 | 0.2634 | 0.7718 | 0.4858 | 0.5728 | 13 | PASS | 0.1538 | 0.2313 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| Q | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.1344 | 0.1481 | 0.04428 | 0.2225 | 0.1344 | 0.1432 | 11 | PASS | -0.2294 | -0.152 | first_evaluation | FAIL | 不通过（d、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.1393 | 0.08961 | -0.06583 | 0.332 | 0.1252 | 0.1917 | 10 | FAIL | -0.2244 | -0.147 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_mean3_v2 | INC1 | 0.25 | 5 | 0.2682 | 0.2419 | 0.06332 | 0.4805 | 0.2709 | 0.4345 | 13 | PASS | -0.04979 | 0.06757 | first_evaluation | FAIL | 不通过（c、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.2153 | 0.2007 | -0.05116 | 0.4861 | 0.228 | 0.4097 | 11 | PASS | -0.1026 | 0.01471 | first_evaluation | FAIL | 不通过（c、d、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.318 | 0.1509 | 0.06691 | 0.5805 | 0.3278 | 0.5171 | 10 | PASS |  | 0.1174 | related_exposed | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False |
| Q | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.2922 | 0.1053 | -0.0002321 | 0.5957 | 0.3124 | 0.5217 | 9 | PASS | -0.02582 | 0.09154 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| Q | M_mean3_v2 | RP3 | 0.25 | 5 | 0.157 | 0.1219 | 0.02507 | 0.2841 | 0.157 | 0.2143 | 12 | PASS | -0.161 | -0.04359 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| Q | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.3539 | 0.2182 | 0.08788 | 0.6125 | 0.361 | 0.5822 | 13 | PASS | 0.03593 | 0.1533 | first_evaluation | PASS | 不通过（c） | 不通过（c） | False |
| Q | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | -0.07264 | -0.03039 | -0.2838 | 0.1367 | -0.07703 | 0.07222 | 7 | FAIL | 0.02254 | -0.1771 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.0359 | 0.06857 | -0.2929 | 0.2169 | -0.03624 | 0.1291 | 7 | PASS | 0.05927 | -0.1404 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、正向门槛、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | -0.09518 | -0.171 | -0.3332 | 0.1615 | -0.09628 | 0.08211 | 5 | PASS |  | -0.1996 | related_exposed | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | -0.05299 | -0.06691 | -0.332 | 0.234 | -0.051 | 0.1477 | 6 | PASS | 0.04218 | -0.1575 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | -0.009236 | -0.005467 | -0.1218 | 0.1075 | -0.009236 | 0.03193 | 7 | FAIL | 0.08594 | -0.1137 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| Q | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.1288 | -0.1459 | -0.3646 | 0.119 | -0.1377 | 0.07605 | 6 | PASS | -0.03362 | -0.2333 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| Q | M_union3_v2 | INC1 | 0.25 | 5 | 0.1757 | 0.04392 | -0.003759 | 0.3493 | 0.01306 | 0.1249 | 10 | FAIL | -0.05185 | 0.08609 | first_evaluation | FAIL | 不通过（d、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、正向门槛、e资本、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.3813 | 0.4576 | 0.1571 | 0.5919 | 0.1495 | 0.2919 | 13 | PASS | 0.1537 | 0.2917 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_union3_v2 | NATIVE | 0.25 | 5 | 0.2276 | 0.265 | 0.02649 | 0.435 | 0.004184 | 0.1169 | 10 | PASS |  | 0.1379 | related_exposed | FAIL | 不通过（d、f、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、f、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.5354 | 0.6264 | 0.2958 | 0.77 | 0.2134 | 0.3778 | 14 | PASS | 0.3078 | 0.4458 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_union3_v2 | RP3 | 0.25 | 5 | 0.01474 | 0.0004187 | -0.03288 | 0.06085 | 0.01474 | 0.01866 | 12 | MC_UNRESOLVED | -0.2128 | -0.0749 | first_evaluation | FAIL | 不通过（正向门槛、size(EXEC_LEADER_VS_PARENT)） | 不通过（正向门槛、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_union3_v2 | SZL5 | 0.25 | 5 | 0.1543 | 0.07127 | -0.06497 | 0.3644 | -0.1164 | 0.04941 | 8 | MC_UNRESOLVED | -0.0733 | 0.06464 | first_evaluation | FAIL | 不通过（c、d、f、e资本、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、正向门槛、e资本、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.1689 | 0.06355 | -0.01053 | 0.3354 | -0.005782 | 0.1099 | 8 | FAIL | -0.08217 | 0.0968 | first_evaluation | FAIL | 不通过（d、e资本、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、正向门槛、e资本、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3636 | 0.4359 | 0.1469 | 0.5628 | 0.1242 | 0.2628 | 11 | PASS | 0.1126 | 0.2916 | first_evaluation | FAIL | 不通过（d、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.251 | 0.3142 | 0.05259 | 0.453 | 0.01981 | 0.1315 | 12 | PASS |  | 0.179 | related_exposed | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.5357 | 0.6555 | 0.3049 | 0.762 | 0.2051 | 0.3633 | 13 | PASS | 0.2847 | 0.4637 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.01083 | 0.01371 | -0.03572 | 0.05664 | 0.01083 | 0.01423 | 11 | PASS | -0.2402 | -0.06122 | first_evaluation | FAIL | 不通过（d、正向门槛、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、正向门槛、size(EXEC_LEADER_VS_PARENT)） | False |
| Q | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.2018 | 0.1657 | 0.002061 | 0.4021 | -0.07678 | 0.08688 | 9 | PASS | -0.04917 | 0.1298 | first_evaluation | FAIL | 不通过（c、d、f、e资本、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、e资本、size(EXEC_LEADER_VS_PARENT)） | False |
| S | A4b | INC1 | 0.25 | 5 | 0.08125 | 0.03575 | -0.182 | 0.316 | 0.08413 | 0.1401 | 9 | FAIL | -0.3184 | -0.1836 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| S | A4b | INC1_HG10 | 0.25 | 5 | 0.3096 | 0.2318 | 0.01812 | 0.5834 | 0.3166 | 0.3913 | 11 | FAIL | -0.09011 | 0.04475 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| S | A4b | NATIVE | 0.25 | 5 | 0.3997 | 0.3777 | 0.1498 | 0.6517 | 0.4052 | 0.4669 | 12 | PASS |  | 0.1349 | same_account_exposed | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| S | A4b | NATIVE_HG10 | 0.25 | 5 | 0.4139 | 0.3352 | 0.1192 | 0.7094 | 0.4235 | 0.5146 | 12 | PASS | 0.0142 | 0.1491 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| S | A4b | RP3 | 0.25 | 5 | 0.1341 | 0.132 | 0.03198 | 0.23 | 0.1341 | 0.1476 | 10 | PASS | -0.2656 | -0.1307 | first_evaluation | FAIL | 不通过（d、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、size(EXEC_LEADER_VS_PARENT)） | False |
| S | A4b | SZL5 | 0.25 | 5 | 0.07851 | 0.08158 | -0.1723 | 0.3188 | 0.09533 | 0.1514 | 10 | FAIL | -0.3212 | -0.1863 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| S | A4b_CVRv5 | INC1 | 0.25 | 5 | 0.1428 | 0.118 | -0.09349 | 0.3519 | 0.1123 | 0.1847 | 10 | FAIL | -0.2816 | -0.1435 | first_evaluation | FAIL | 不通过（d、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| S | A4b_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.2624 | 0.1307 | -0.00494 | 0.513 | 0.239 | 0.3167 | 11 | FAIL | -0.162 | -0.02388 | first_evaluation | FAIL | 不通过（d、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| S | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.4244 | 0.3578 | 0.2037 | 0.6299 | 0.4003 | 0.4661 | 13 | PASS |  | 0.1381 | same_account_exposed | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| S | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.4176 | 0.4411 | 0.1467 | 0.69 | 0.4005 | 0.4798 | 12 | PASS | -0.00678 | 0.1313 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| S | A4b_CVRv5 | RP3 | 0.25 | 5 | 0.1102 | 0.1287 | 0.01884 | 0.197 | 0.1102 | 0.1185 | 12 | PASS | -0.3142 | -0.1761 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| S | A4b_CVRv5 | SZL5 | 0.25 | 5 | 0.1414 | 0.08738 | -0.0766 | 0.3438 | 0.1183 | 0.1962 | 9 | FAIL | -0.283 | -0.1449 | first_evaluation | FAIL | 不通过（c、d、f、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_mean3_v2 | INC1 | 0.25 | 5 | 0.2785 | 0.1308 | 0.05481 | 0.5142 | 0.2835 | 0.4437 | 12 | MC_UNRESOLVED | -0.06625 | 0.07789 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_mean3_v2 | INC1_HG10 | 0.25 | 5 | 0.1936 | 0.1127 | -0.08192 | 0.4596 | 0.2019 | 0.3867 | 10 | PASS | -0.1512 | -0.007023 | first_evaluation | FAIL | 不通过（c、d、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.3448 | 0.2127 | 0.08606 | 0.6127 | 0.3502 | 0.5437 | 12 | PASS |  | 0.1441 | same_account_exposed | PASS | 不通过（c） | 不通过（c） | False |
| S | M_mean3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.313 | 0.1216 | 0.01307 | 0.6066 | 0.3267 | 0.5408 | 9 | PASS | -0.03177 | 0.1124 | first_evaluation | PASS | 不通过（c、d） | 不通过（c、d） | False |
| S | M_mean3_v2 | RP3 | 0.25 | 5 | 0.2204 | 0.2108 | 0.1022 | 0.3388 | 0.2204 | 0.2763 | 13 | PASS | -0.1243 | 0.01982 | first_evaluation | PASS | 通过 | 通过 | False |
| S | M_mean3_v2 | SZL5 | 0.25 | 5 | 0.1754 | 0.03933 | -0.09069 | 0.4579 | 0.1843 | 0.4015 | 10 | FAIL | -0.1693 | -0.0252 | first_evaluation | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | -0.03874 | -0.05733 | -0.2481 | 0.1745 | -0.04475 | 0.1062 | 6 | FAIL | -0.03297 | -0.1432 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_mean3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | -0.09065 | -0.009104 | -0.3398 | 0.1548 | -0.1008 | 0.07603 | 6 | FAIL | -0.08487 | -0.1951 | first_evaluation | FAIL | 不通过（c、d、f、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、正向门槛、e资本、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | -0.005773 | -0.06165 | -0.2485 | 0.247 | -0.00439 | 0.173 | 8 | PASS |  | -0.1102 | same_account_exposed | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| S | M_mean3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | -0.08456 | -0.1577 | -0.3562 | 0.2011 | -0.08925 | 0.1173 | 7 | PASS | -0.07878 | -0.189 | first_evaluation | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False |
| S | M_mean3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.06107 | 0.03759 | -0.04222 | 0.1648 | 0.06107 | 0.102 | 9 | PASS | 0.06684 | -0.04339 | first_evaluation | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False |
| S | M_mean3_v2_CVRv5 | SZL5 | 0.25 | 5 | -0.231 | -0.2775 | -0.4855 | 0.03084 | -0.2383 | -0.02566 | 7 | FAIL | -0.2252 | -0.3355 | first_evaluation | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False |
| S | M_union3_v2 | INC1 | 0.25 | 5 | 0.1842 | 0.162 | -0.007725 | 0.3661 | 0.03547 | 0.1348 | 12 | MC_UNRESOLVED | -0.1336 | 0.09456 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（e资本、size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_union3_v2 | INC1_HG10 | 0.25 | 5 | 0.3984 | 0.3503 | 0.1868 | 0.6027 | 0.148 | 0.3032 | 15 | FAIL | 0.08065 | 0.3088 | first_evaluation | FAIL | 不通过（e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_union3_v2 | NATIVE | 0.25 | 5 | 0.3178 | 0.271 | 0.1204 | 0.5191 | 0.06444 | 0.2039 | 13 | PASS |  | 0.2282 | same_account_exposed | FAIL | 不通过（f、size(EXEC_LEADER_VS_PARENT)） | 不通过（f、size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | 0.4324 | 0.4134 | 0.2008 | 0.6539 | 0.09695 | 0.2664 | 14 | PASS | 0.1146 | 0.3428 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_union3_v2 | RP3 | 0.25 | 5 | 0.01587 | 0.004026 | -0.03517 | 0.06561 | 0.01587 | 0.01965 | 11 | FAIL | -0.3019 | -0.07376 | first_evaluation | FAIL | 不通过（d、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_union3_v2 | SZL5 | 0.25 | 5 | 0.1094 | 0.03241 | -0.1109 | 0.3209 | -0.1559 | -0.009295 | 9 | FAIL | -0.2084 | 0.01974 | first_evaluation | FAIL | 不通过（c、d、f、e资本、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、正向门槛、e资本、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | 0.2101 | 0.2426 | 0.02444 | 0.3802 | 0.04257 | 0.1535 | 13 | PASS | -0.1386 | 0.138 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | 0.3916 | 0.4481 | 0.1765 | 0.5906 | 0.1351 | 0.2837 | 12 | PASS | 0.04289 | 0.3195 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3487 | 0.3481 | 0.1639 | 0.5396 | 0.08027 | 0.2279 | 12 | PASS |  | 0.2767 | same_account_exposed | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | 0.44 | 0.49 | 0.2019 | 0.6616 | 0.09191 | 0.2616 | 14 | PASS | 0.09127 | 0.3679 | first_evaluation | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_union3_v2_CVRv5 | RP3 | 0.25 | 5 | 0.003435 | -0.00127 | -0.04276 | 0.05014 | 0.003435 | 0.006165 | 9 | FAIL | -0.3453 | -0.06861 | first_evaluation | FAIL | 不通过（d、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、正向门槛、e随机、size(EXEC_LEADER_VS_PARENT)） | False |
| S | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | 0.1666 | 0.1094 | -0.04141 | 0.3695 | -0.1125 | 0.04038 | 11 | PASS | -0.1821 | 0.09452 | first_evaluation | FAIL | 不通过（d、f、e资本、size(EXEC_LEADER_VS_PARENT)） | 不通过（d、f、e资本、size(EXEC_LEADER_VS_PARENT)） | False |
| SM | A4b | NATIVE | 0.25 | 5 | 0.2996 | 0.2374 | 0.06651 | 0.5287 | 0.3078 | 0.3298 | 11 | MC_UNRESOLVED |  | 0.03475 | same_account_exposed | FAIL | 不通过（c、d、f、size(EXEC_LEADER_VS_PARENT)） | 不通过（c、d、f、size(EXEC_LEADER_VS_PARENT)） | False |
| SM | A4b_CVRv5 | NATIVE | 0.25 | 5 | 0.2566 | 0.1949 | 0.05383 | 0.4491 | 0.2426 | 0.2695 | 13 | PASS |  | -0.02975 | same_account_exposed | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| SM | M_mean3_v2 | NATIVE | 0.25 | 5 | 0.4969 | 0.4043 | 0.2813 | 0.7331 | 0.4962 | 0.6275 | 15 | PASS |  | 0.2963 | same_account_exposed | PASS | 不通过（c） | 不通过（c） | False |
| SM | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.1814 | 0.1383 | -0.03136 | 0.4078 | 0.1738 | 0.2958 | 13 | PASS |  | 0.07694 | same_account_exposed | PASS | 不通过（c、f） | 不通过（c、f） | False |
| SM | M_union3_v2 | NATIVE | 0.25 | 5 | 0.3699 | 0.3221 | 0.1824 | 0.5623 | 0.1812 | 0.2567 | 13 | PASS |  | 0.2802 | same_account_exposed | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |
| SM | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | 0.3634 | 0.3373 | 0.1836 | 0.5513 | 0.1663 | 0.2469 | 12 | PASS |  | 0.2914 | same_account_exposed | FAIL | 不通过（size(EXEC_LEADER_VS_PARENT)） | 不通过（size(EXEC_LEADER_VS_PARENT)） | False |


## 三句加法（原生四测量 + SM；逐形态 × profile × 聚合；PX1）

> 表头：主体=原生对象三句加法｜算子=见列｜分母=四段有效配对日（FULL = n 加权；G4 = 段中位）｜基准=同 H 原父（8bp）｜子集=NATIVE S / M / Q / C1 + SM × 六形态｜单位=年化百分点 / 判词｜日期=2010-01-04..2026-03-27（四段；2026 partial）｜H=5｜成本模型=源 8bp（f：A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（e 资本：MATCH-CAP）｜exposure=原生对象按暴露台账｜query_id=E6K-P3-ADD


| form | profile | aggregation | eligible | chosen | why |
|---|---|---|---|---|---|
| A06 | LEGACY_EDIT5 | FULL |  | 无 |  |
| A06 | LEGACY_EDIT5 | G4 |  | 无 |  |
| A06 | PROPOSED_PORT3_T | FULL |  | 无 |  |
| A06 | PROPOSED_PORT3_T | G4 |  | 无 |  |
| A06 | PROPOSED_PORT3_LAG1 | FULL |  | 无 |  |
| A06 | PROPOSED_PORT3_LAG1 | G4 |  | 无 |  |
| A06 | EXEC_DISCLOSE_ONLY | FULL |  | 无 |  |
| A06 | EXEC_DISCLOSE_ONLY | G4 |  | 无 |  |
| A06 | EXEC_LEADER_VS_PARENT | FULL |  | 无 |  |
| A06 | EXEC_LEADER_VS_PARENT | G4 |  | 无 |  |
| A4b | LEGACY_EDIT5 | FULL |  | 无 |  |
| A4b | LEGACY_EDIT5 | G4 |  | 无 |  |
| A4b | PROPOSED_PORT3_T | FULL | C1\|M\|S\|Q | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.135 ≥ +.05 |
| A4b | PROPOSED_PORT3_T | G4 | C1\|M\|S\|Q | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.178 ≥ +.05 |
| A4b | PROPOSED_PORT3_LAG1 | FULL | C1\|M\|S\|Q | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.135 ≥ +.05 |
| A4b | PROPOSED_PORT3_LAG1 | G4 | C1\|M\|S\|Q | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.178 ≥ +.05 |
| A4b | EXEC_DISCLOSE_ONLY | FULL | C1\|M\|S\|Q | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.135 ≥ +.05 |
| A4b | EXEC_DISCLOSE_ONLY | G4 | C1\|M\|S\|Q | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.178 ≥ +.05 |
| A4b | EXEC_LEADER_VS_PARENT | FULL |  | 无 |  |
| A4b | EXEC_LEADER_VS_PARENT | G4 |  | 无 |  |
| A4b_CVRv5 | LEGACY_EDIT5 | FULL |  | 无 |  |
| A4b_CVRv5 | LEGACY_EDIT5 | G4 |  | 无 |  |
| A4b_CVRv5 | PROPOSED_PORT3_T | FULL | C1\|M\|S\|Q | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.138 ≥ +.05 |
| A4b_CVRv5 | PROPOSED_PORT3_T | G4 | C1\|M\|S\|Q | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.144 ≥ +.05 |
| A4b_CVRv5 | PROPOSED_PORT3_LAG1 | FULL | C1\|M\|S\|Q | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.138 ≥ +.05 |
| A4b_CVRv5 | PROPOSED_PORT3_LAG1 | G4 | C1\|M\|S\|Q | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.144 ≥ +.05 |
| A4b_CVRv5 | EXEC_DISCLOSE_ONLY | FULL | C1\|M\|S\|Q | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.138 ≥ +.05 |
| A4b_CVRv5 | EXEC_DISCLOSE_ONLY | G4 | C1\|M\|S\|Q | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.144 ≥ +.05 |
| A4b_CVRv5 | EXEC_LEADER_VS_PARENT | FULL |  | 无 |  |
| A4b_CVRv5 | EXEC_LEADER_VS_PARENT | G4 |  | 无 |  |
| M_mean3_v2 | LEGACY_EDIT5 | FULL | C1 | C1 | C1 合格 → 默认简单 C1 |
| M_mean3_v2 | LEGACY_EDIT5 | G4 | C1 | C1 | C1 合格 → 默认简单 C1 |
| M_mean3_v2 | PROPOSED_PORT3_T | FULL | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.236 ≥ +.05 |
| M_mean3_v2 | PROPOSED_PORT3_T | G4 | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.269 ≥ +.05 |
| M_mean3_v2 | PROPOSED_PORT3_LAG1 | FULL | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.236 ≥ +.05 |
| M_mean3_v2 | PROPOSED_PORT3_LAG1 | G4 | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.269 ≥ +.05 |
| M_mean3_v2 | EXEC_DISCLOSE_ONLY | FULL | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.236 ≥ +.05 |
| M_mean3_v2 | EXEC_DISCLOSE_ONLY | G4 | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.269 ≥ +.05 |
| M_mean3_v2 | EXEC_LEADER_VS_PARENT | FULL | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.236 ≥ +.05 |
| M_mean3_v2 | EXEC_LEADER_VS_PARENT | G4 | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.269 ≥ +.05 |
| M_mean3_v2_CVRv5 | LEGACY_EDIT5 | FULL | C1 | C1 | C1 合格 → 默认简单 C1 |
| M_mean3_v2_CVRv5 | LEGACY_EDIT5 | G4 |  | 无 |  |
| M_mean3_v2_CVRv5 | PROPOSED_PORT3_T | FULL | C1 | C1 | C1 合格 → 默认简单 C1 |
| M_mean3_v2_CVRv5 | PROPOSED_PORT3_T | G4 |  | 无 |  |
| M_mean3_v2_CVRv5 | PROPOSED_PORT3_LAG1 | FULL | C1 | C1 | C1 合格 → 默认简单 C1 |
| M_mean3_v2_CVRv5 | PROPOSED_PORT3_LAG1 | G4 |  | 无 |  |
| M_mean3_v2_CVRv5 | EXEC_DISCLOSE_ONLY | FULL | C1 | C1 | C1 合格 → 默认简单 C1 |
| M_mean3_v2_CVRv5 | EXEC_DISCLOSE_ONLY | G4 |  | 无 |  |
| M_mean3_v2_CVRv5 | EXEC_LEADER_VS_PARENT | FULL | C1 | C1 | C1 合格 → 默认简单 C1 |
| M_mean3_v2_CVRv5 | EXEC_LEADER_VS_PARENT | G4 |  | 无 |  |
| M_union3_v2 | LEGACY_EDIT5 | FULL | M | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2 | LEGACY_EDIT5 | G4 | M | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2 | PROPOSED_PORT3_T | FULL | M | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2 | PROPOSED_PORT3_T | G4 | M | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2 | PROPOSED_PORT3_LAG1 | FULL | M | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2 | PROPOSED_PORT3_LAG1 | G4 | M | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2 | EXEC_DISCLOSE_ONLY | FULL | M | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2 | EXEC_DISCLOSE_ONLY | G4 | M | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2 | EXEC_LEADER_VS_PARENT | FULL | M | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2 | EXEC_LEADER_VS_PARENT | G4 | M | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2_CVRv5 | LEGACY_EDIT5 | FULL | M | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2_CVRv5 | LEGACY_EDIT5 | G4 | M | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2_CVRv5 | PROPOSED_PORT3_T | FULL | M\|S\|Q | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2_CVRv5 | PROPOSED_PORT3_T | G4 | M\|S\|Q | S | C1 不合格；取最佳合格单臂 |
| M_union3_v2_CVRv5 | PROPOSED_PORT3_LAG1 | FULL | M\|S\|Q | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2_CVRv5 | PROPOSED_PORT3_LAG1 | G4 | M\|S\|Q | S | C1 不合格；取最佳合格单臂 |
| M_union3_v2_CVRv5 | EXEC_DISCLOSE_ONLY | FULL | M\|S\|Q | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2_CVRv5 | EXEC_DISCLOSE_ONLY | G4 | M\|S\|Q | S | C1 不合格；取最佳合格单臂 |
| M_union3_v2_CVRv5 | EXEC_LEADER_VS_PARENT | FULL | M | M | C1 不合格；取最佳合格单臂 |
| M_union3_v2_CVRv5 | EXEC_LEADER_VS_PARENT | G4 | M | M | C1 不合格；取最佳合格单臂 |
| R2 | LEGACY_EDIT5 | FULL | C1 | C1 | C1 合格 → 默认简单 C1 |
| R2 | LEGACY_EDIT5 | G4 | C1 | C1 | C1 合格 → 默认简单 C1 |
| R2 | PROPOSED_PORT3_T | FULL | C1\|M\|S | C1 | C1 合格 → 默认简单 C1 |
| R2 | PROPOSED_PORT3_T | G4 | C1\|M\|S | C1 | C1 合格 → 默认简单 C1 |
| R2 | PROPOSED_PORT3_LAG1 | FULL | C1\|M\|S | C1 | C1 合格 → 默认简单 C1 |
| R2 | PROPOSED_PORT3_LAG1 | G4 | C1\|M\|S | C1 | C1 合格 → 默认简单 C1 |
| R2 | EXEC_DISCLOSE_ONLY | FULL | C1\|M\|S | C1 | C1 合格 → 默认简单 C1 |
| R2 | EXEC_DISCLOSE_ONLY | G4 | C1\|M\|S | C1 | C1 合格 → 默认简单 C1 |
| R2 | EXEC_LEADER_VS_PARENT | FULL | M | M | C1 不合格；取最佳合格单臂 |
| R2 | EXEC_LEADER_VS_PARENT | G4 | M | M | C1 不合格；取最佳合格单臂 |


## 《生产变更候选清单》（任一 profile FULL 通过；逐 profile 分列；deployment_authorized = false）

> 表头：主体=候选计数（全部登记对象；逐 profile × 族）｜算子=见列｜分母=四段有效配对日（FULL = n 加权；G4 = 段中位）｜基准=同 H 原父（8bp）｜子集=政策 FULL 通过｜单位=计数｜日期=2010-01-04..2026-03-27（四段；2026 partial）｜H=H 1…20｜成本模型=源 8bp（f：A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（e 资本：MATCH-CAP）｜exposure=见 evidence_exposure 列｜query_id=E6K-P3-CAND-COUNT


| profile | family | objects | main_objects |
|---|---|---|---|
| EXEC_DISCLOSE_ONLY | BAND | 134 | 15 |
| EXEC_DISCLOSE_ONLY | INC | 18 | 4 |
| EXEC_DISCLOSE_ONLY | LX | 24 | 0 |
| EXEC_DISCLOSE_ONLY | NATIVE | 32 | 22 |
| EXEC_DISCLOSE_ONLY | RP | 14 | 3 |
| EXEC_DISCLOSE_ONLY | SZL | 5 | 3 |
| EXEC_DISCLOSE_ONLY | TREFIT | 6 | 0 |
| EXEC_LEADER_VS_PARENT | BAND | 25 | 0 |
| EXEC_LEADER_VS_PARENT | INC | 3 | 0 |
| EXEC_LEADER_VS_PARENT | LX | 7 | 0 |
| EXEC_LEADER_VS_PARENT | NATIVE | 10 | 9 |
| EXEC_LEADER_VS_PARENT | RP | 6 | 1 |
| EXEC_LEADER_VS_PARENT | SZL | 4 | 3 |
| LEGACY_EDIT5 | BAND | 34 | 0 |
| LEGACY_EDIT5 | INC | 7 | 3 |
| LEGACY_EDIT5 | LX | 9 | 0 |
| LEGACY_EDIT5 | NATIVE | 9 | 8 |
| LEGACY_EDIT5 | RP | 5 | 1 |
| LEGACY_EDIT5 | SZL | 2 | 0 |
| PROPOSED_PORT3_LAG1 | BAND | 134 | 15 |
| PROPOSED_PORT3_LAG1 | INC | 18 | 4 |
| PROPOSED_PORT3_LAG1 | LX | 24 | 0 |
| PROPOSED_PORT3_LAG1 | NATIVE | 32 | 22 |
| PROPOSED_PORT3_LAG1 | RP | 14 | 3 |
| PROPOSED_PORT3_LAG1 | SZL | 5 | 3 |
| PROPOSED_PORT3_LAG1 | TREFIT | 6 | 0 |
| PROPOSED_PORT3_T | BAND | 134 | 15 |
| PROPOSED_PORT3_T | INC | 18 | 4 |
| PROPOSED_PORT3_T | LX | 24 | 0 |
| PROPOSED_PORT3_T | NATIVE | 32 | 22 |
| PROPOSED_PORT3_T | RP | 14 | 3 |
| PROPOSED_PORT3_T | SZL | 5 | 3 |
| PROPOSED_PORT3_T | TREFIT | 6 | 0 |


> 表头：主体=候选（主展示 144 + C1_hi + SM 锚）｜算子=见列｜分母=四段有效配对日（FULL = n 加权；G4 = 段中位）｜基准=同 H 原父（8bp）｜子集=政策 FULL 通过 ∩ 主对象｜单位=年化百分点 / 判词｜日期=2010-01-04..2026-03-27（四段；2026 partial）｜H=H 见列｜成本模型=源 8bp（f：A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（e 资本：MATCH-CAP）｜exposure=见 evidence_exposure 列｜query_id=E6K-P3-CAND


| profile | desc_id | family | meas | mother | op | alpha | H | main_object | FULL | G4 | evidence_exposure | replacement_preference_status | deployment_authorized |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LEGACY_EDIT5 | C1\|A4b\|a0.5\|H10\|NATIVE | NATIVE | C1 | A4b | NATIVE | 0.5 | 10 | True | 0.4742 | 0.5273 | same_account_exposed |  | False |
| LEGACY_EDIT5 | C1\|A4b\|a0.5\|H20\|NATIVE | NATIVE | C1 | A4b | NATIVE | 0.5 | 20 | True | 0.3358 | 0.3565 | same_account_exposed |  | False |
| LEGACY_EDIT5 | C1\|A4b_CVRv5\|a0.5\|H10\|NATIVE | NATIVE | C1 | A4b_CVRv5 | NATIVE | 0.5 | 10 | True | 0.4206 | 0.3958 | same_account_exposed |  | False |
| LEGACY_EDIT5 | C1\|A4b_CVRv5\|a0.5\|H20\|NATIVE | NATIVE | C1 | A4b_CVRv5 | NATIVE | 0.5 | 20 | True | 0.2857 | 0.2776 | same_account_exposed |  | False |
| LEGACY_EDIT5 | C1\|M_mean3_v2\|a0.25\|H5\|NATIVE | NATIVE | C1 | M_mean3_v2 | NATIVE | 0.25 | 5 | True | 0.2006 | 0.1498 | same_account_exposed |  | False |
| LEGACY_EDIT5 | C1\|M_mean3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | C1 | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.1045 | 0.09114 | same_account_exposed |  | False |
| LEGACY_EDIT5 | M\|M_mean3_v2\|a0.25\|H5\|INC1 | INC | M | M_mean3_v2 | INC1 | 0.25 | 5 | True | 0.3977 | 0.3379 | first_evaluation | NOT_AUTHORIZED | False |
| LEGACY_EDIT5 | M\|M_mean3_v2_CVRv5\|a0.25\|H5\|INC1 | INC | M | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | True | 0.2247 | 0.172 | first_evaluation | NOT_AUTHORIZED | False |
| LEGACY_EDIT5 | M\|M_union3_v2\|a0.25\|H5\|INC1 | INC | M | M_union3_v2 | INC1 | 0.25 | 5 | True | 0.2595 | 0.2783 | first_evaluation | NOT_AUTHORIZED | False |
| LEGACY_EDIT5 | M\|M_union3_v2\|a0.25\|H5\|NATIVE | NATIVE | M | M_union3_v2 | NATIVE | 0.25 | 5 | True | 0.398 | 0.2775 | same_account_exposed |  | False |
| LEGACY_EDIT5 | M\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | M | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3768 | 0.3079 | same_account_exposed |  | False |
| LEGACY_EDIT5 | S\|M_mean3_v2\|a0.25\|H5\|RP3 | RP | S | M_mean3_v2 | RP3 | 0.25 | 5 | True | 0.2204 | 0.2108 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | C1\|A4b\|a0.25\|H5\|NATIVE | NATIVE | C1 | A4b | NATIVE | 0.25 | 5 | True | 0.2648 | 0.311 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | C1\|A4b\|a0.5\|H10\|NATIVE | NATIVE | C1 | A4b | NATIVE | 0.5 | 10 | True | 0.4742 | 0.5273 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | C1\|A4b\|a0.5\|H20\|NATIVE | NATIVE | C1 | A4b | NATIVE | 0.5 | 20 | True | 0.3358 | 0.3565 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | C1\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | C1 | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.2863 | 0.3224 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | C1\|A4b_CVRv5\|a0.5\|H10\|NATIVE | NATIVE | C1 | A4b_CVRv5 | NATIVE | 0.5 | 10 | True | 0.4206 | 0.3958 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | C1\|A4b_CVRv5\|a0.5\|H20\|NATIVE | NATIVE | C1 | A4b_CVRv5 | NATIVE | 0.5 | 20 | True | 0.2857 | 0.2776 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | C1\|M_mean3_v2\|a0.25\|H5\|NATIVE | NATIVE | C1 | M_mean3_v2 | NATIVE | 0.25 | 5 | True | 0.2006 | 0.1498 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | C1\|M_mean3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | C1 | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.1045 | 0.09114 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | C1\|M_union3_v2_CVRv5\|a0.25\|H5\|INC1_HG10 | BAND | C1 | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | True | 0.1555 | 0.1447 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | M\|A4b\|a0.25\|H5\|NATIVE | NATIVE | M | A4b | NATIVE | 0.25 | 5 | True | 0.3386 | 0.2736 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | M\|A4b\|a0.25\|H5\|NATIVE_HG10 | BAND | M | A4b | NATIVE_HG10 | 0.25 | 5 | True | 0.3479 | 0.2125 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | M\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | M | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.34 | 0.2745 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | M\|A4b_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | M | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.371 | 0.3839 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | M\|A4b_CVRv5\|a0.25\|H5\|SZL5 | SZL | M | A4b_CVRv5 | SZL5 | 0.25 | 5 | True | 0.2398 | 0.1384 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | M\|M_mean3_v2\|a0.25\|H5\|INC1 | INC | M | M_mean3_v2 | INC1 | 0.25 | 5 | True | 0.3977 | 0.3379 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | M\|M_mean3_v2\|a0.25\|H5\|NATIVE | NATIVE | M | M_mean3_v2 | NATIVE | 0.25 | 5 | True | 0.4361 | 0.4186 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | M\|M_mean3_v2_CVRv5\|a0.25\|H5\|INC1 | INC | M | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | True | 0.2247 | 0.172 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | M\|M_union3_v2\|a0.25\|H5\|INC1 | INC | M | M_union3_v2 | INC1 | 0.25 | 5 | True | 0.2595 | 0.2783 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | M\|M_union3_v2\|a0.25\|H5\|NATIVE | NATIVE | M | M_union3_v2 | NATIVE | 0.25 | 5 | True | 0.398 | 0.2775 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | M\|M_union3_v2\|a0.25\|H5\|NATIVE_HG10 | BAND | M | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | True | 0.3104 | 0.3448 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | M\|M_union3_v2\|a0.25\|H5\|SZL5 | SZL | M | M_union3_v2 | SZL5 | 0.25 | 5 | True | 0.3308 | 0.2388 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | M\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | M | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3768 | 0.3079 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | M\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | M | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.3473 | 0.4264 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | M\|M_union3_v2_CVRv5\|a0.25\|H5\|SZL5 | SZL | M | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | True | 0.34 | 0.3027 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | Q\|A4b\|a0.25\|H5\|NATIVE | NATIVE | Q | A4b | NATIVE | 0.25 | 5 | True | 0.3631 | 0.2695 | related_exposed |  | False |
| PROPOSED_PORT3_T | Q\|A4b\|a0.25\|H5\|NATIVE_HG10 | BAND | Q | A4b | NATIVE_HG10 | 0.25 | 5 | True | 0.5279 | 0.4851 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | Q\|A4b\|a0.25\|H5\|RP3 | RP | Q | A4b | RP3 | 0.25 | 5 | True | 0.165 | 0.2136 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | Q\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | Q | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3638 | 0.2874 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | Q\|A4b_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | Q | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.5176 | 0.5256 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | Q\|M_union3_v2\|a0.25\|H5\|INC1_HG10 | BAND | Q | M_union3_v2 | INC1_HG10 | 0.25 | 5 | True | 0.3813 | 0.4576 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | Q\|M_union3_v2\|a0.25\|H5\|NATIVE_HG10 | BAND | Q | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | True | 0.5354 | 0.6264 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | Q\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | Q | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.251 | 0.3142 | related_exposed |  | False |
| PROPOSED_PORT3_T | Q\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | Q | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.5357 | 0.6555 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | S\|A4b\|a0.25\|H5\|NATIVE | NATIVE | S | A4b | NATIVE | 0.25 | 5 | True | 0.3997 | 0.3777 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | S\|A4b\|a0.25\|H5\|NATIVE_HG10 | BAND | S | A4b | NATIVE_HG10 | 0.25 | 5 | True | 0.4139 | 0.3352 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | S\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | S | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.4244 | 0.3578 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | S\|A4b_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | S | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.4176 | 0.4411 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | S\|A4b_CVRv5\|a0.25\|H5\|RP3 | RP | S | A4b_CVRv5 | RP3 | 0.25 | 5 | True | 0.1102 | 0.1287 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | S\|M_mean3_v2\|a0.25\|H5\|RP3 | RP | S | M_mean3_v2 | RP3 | 0.25 | 5 | True | 0.2204 | 0.2108 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | S\|M_union3_v2\|a0.25\|H5\|NATIVE_HG10 | BAND | S | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | True | 0.4324 | 0.4134 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | S\|M_union3_v2_CVRv5\|a0.25\|H5\|INC1 | INC | S | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | True | 0.2101 | 0.2426 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | S\|M_union3_v2_CVRv5\|a0.25\|H5\|INC1_HG10 | BAND | S | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | True | 0.3916 | 0.4481 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | S\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | S | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3487 | 0.3481 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | S\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | S | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.44 | 0.49 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_T | SM\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | SM | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.2566 | 0.1949 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | SM\|M_union3_v2\|a0.25\|H5\|NATIVE | NATIVE | SM | M_union3_v2 | NATIVE | 0.25 | 5 | True | 0.3699 | 0.3221 | same_account_exposed |  | False |
| PROPOSED_PORT3_T | SM\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | SM | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3634 | 0.3373 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | C1\|A4b\|a0.25\|H5\|NATIVE | NATIVE | C1 | A4b | NATIVE | 0.25 | 5 | True | 0.2648 | 0.311 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | C1\|A4b\|a0.5\|H10\|NATIVE | NATIVE | C1 | A4b | NATIVE | 0.5 | 10 | True | 0.4742 | 0.5273 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | C1\|A4b\|a0.5\|H20\|NATIVE | NATIVE | C1 | A4b | NATIVE | 0.5 | 20 | True | 0.3358 | 0.3565 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | C1\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | C1 | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.2863 | 0.3224 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | C1\|A4b_CVRv5\|a0.5\|H10\|NATIVE | NATIVE | C1 | A4b_CVRv5 | NATIVE | 0.5 | 10 | True | 0.4206 | 0.3958 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | C1\|A4b_CVRv5\|a0.5\|H20\|NATIVE | NATIVE | C1 | A4b_CVRv5 | NATIVE | 0.5 | 20 | True | 0.2857 | 0.2776 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | C1\|M_mean3_v2\|a0.25\|H5\|NATIVE | NATIVE | C1 | M_mean3_v2 | NATIVE | 0.25 | 5 | True | 0.2006 | 0.1498 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | C1\|M_mean3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | C1 | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.1045 | 0.09114 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | C1\|M_union3_v2_CVRv5\|a0.25\|H5\|INC1_HG10 | BAND | C1 | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | True | 0.1555 | 0.1447 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | M\|A4b\|a0.25\|H5\|NATIVE | NATIVE | M | A4b | NATIVE | 0.25 | 5 | True | 0.3386 | 0.2736 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | M\|A4b\|a0.25\|H5\|NATIVE_HG10 | BAND | M | A4b | NATIVE_HG10 | 0.25 | 5 | True | 0.3479 | 0.2125 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | M\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | M | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.34 | 0.2745 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | M\|A4b_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | M | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.371 | 0.3839 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | M\|A4b_CVRv5\|a0.25\|H5\|SZL5 | SZL | M | A4b_CVRv5 | SZL5 | 0.25 | 5 | True | 0.2398 | 0.1384 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | M\|M_mean3_v2\|a0.25\|H5\|INC1 | INC | M | M_mean3_v2 | INC1 | 0.25 | 5 | True | 0.3977 | 0.3379 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | M\|M_mean3_v2\|a0.25\|H5\|NATIVE | NATIVE | M | M_mean3_v2 | NATIVE | 0.25 | 5 | True | 0.4361 | 0.4186 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | M\|M_mean3_v2_CVRv5\|a0.25\|H5\|INC1 | INC | M | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | True | 0.2247 | 0.172 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | M\|M_union3_v2\|a0.25\|H5\|INC1 | INC | M | M_union3_v2 | INC1 | 0.25 | 5 | True | 0.2595 | 0.2783 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | M\|M_union3_v2\|a0.25\|H5\|NATIVE | NATIVE | M | M_union3_v2 | NATIVE | 0.25 | 5 | True | 0.398 | 0.2775 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | M\|M_union3_v2\|a0.25\|H5\|NATIVE_HG10 | BAND | M | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | True | 0.3104 | 0.3448 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | M\|M_union3_v2\|a0.25\|H5\|SZL5 | SZL | M | M_union3_v2 | SZL5 | 0.25 | 5 | True | 0.3308 | 0.2388 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | M\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | M | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3768 | 0.3079 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | M\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | M | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.3473 | 0.4264 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | M\|M_union3_v2_CVRv5\|a0.25\|H5\|SZL5 | SZL | M | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | True | 0.34 | 0.3027 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | Q\|A4b\|a0.25\|H5\|NATIVE | NATIVE | Q | A4b | NATIVE | 0.25 | 5 | True | 0.3631 | 0.2695 | related_exposed |  | False |
| PROPOSED_PORT3_LAG1 | Q\|A4b\|a0.25\|H5\|NATIVE_HG10 | BAND | Q | A4b | NATIVE_HG10 | 0.25 | 5 | True | 0.5279 | 0.4851 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | Q\|A4b\|a0.25\|H5\|RP3 | RP | Q | A4b | RP3 | 0.25 | 5 | True | 0.165 | 0.2136 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | Q\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | Q | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3638 | 0.2874 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | Q\|A4b_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | Q | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.5176 | 0.5256 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | Q\|M_union3_v2\|a0.25\|H5\|INC1_HG10 | BAND | Q | M_union3_v2 | INC1_HG10 | 0.25 | 5 | True | 0.3813 | 0.4576 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | Q\|M_union3_v2\|a0.25\|H5\|NATIVE_HG10 | BAND | Q | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | True | 0.5354 | 0.6264 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | Q\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | Q | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.251 | 0.3142 | related_exposed |  | False |
| PROPOSED_PORT3_LAG1 | Q\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | Q | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.5357 | 0.6555 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | S\|A4b\|a0.25\|H5\|NATIVE | NATIVE | S | A4b | NATIVE | 0.25 | 5 | True | 0.3997 | 0.3777 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | S\|A4b\|a0.25\|H5\|NATIVE_HG10 | BAND | S | A4b | NATIVE_HG10 | 0.25 | 5 | True | 0.4139 | 0.3352 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | S\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | S | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.4244 | 0.3578 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | S\|A4b_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | S | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.4176 | 0.4411 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | S\|A4b_CVRv5\|a0.25\|H5\|RP3 | RP | S | A4b_CVRv5 | RP3 | 0.25 | 5 | True | 0.1102 | 0.1287 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | S\|M_mean3_v2\|a0.25\|H5\|RP3 | RP | S | M_mean3_v2 | RP3 | 0.25 | 5 | True | 0.2204 | 0.2108 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | S\|M_union3_v2\|a0.25\|H5\|NATIVE_HG10 | BAND | S | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | True | 0.4324 | 0.4134 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | S\|M_union3_v2_CVRv5\|a0.25\|H5\|INC1 | INC | S | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | True | 0.2101 | 0.2426 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | S\|M_union3_v2_CVRv5\|a0.25\|H5\|INC1_HG10 | BAND | S | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | True | 0.3916 | 0.4481 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | S\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | S | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3487 | 0.3481 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | S\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | S | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.44 | 0.49 | first_evaluation | NOT_AUTHORIZED | False |
| PROPOSED_PORT3_LAG1 | SM\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | SM | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.2566 | 0.1949 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | SM\|M_union3_v2\|a0.25\|H5\|NATIVE | NATIVE | SM | M_union3_v2 | NATIVE | 0.25 | 5 | True | 0.3699 | 0.3221 | same_account_exposed |  | False |
| PROPOSED_PORT3_LAG1 | SM\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | SM | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3634 | 0.3373 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | C1\|A4b\|a0.25\|H5\|NATIVE | NATIVE | C1 | A4b | NATIVE | 0.25 | 5 | True | 0.2648 | 0.311 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | C1\|A4b\|a0.5\|H10\|NATIVE | NATIVE | C1 | A4b | NATIVE | 0.5 | 10 | True | 0.4742 | 0.5273 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | C1\|A4b\|a0.5\|H20\|NATIVE | NATIVE | C1 | A4b | NATIVE | 0.5 | 20 | True | 0.3358 | 0.3565 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | C1\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | C1 | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.2863 | 0.3224 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | C1\|A4b_CVRv5\|a0.5\|H10\|NATIVE | NATIVE | C1 | A4b_CVRv5 | NATIVE | 0.5 | 10 | True | 0.4206 | 0.3958 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | C1\|A4b_CVRv5\|a0.5\|H20\|NATIVE | NATIVE | C1 | A4b_CVRv5 | NATIVE | 0.5 | 20 | True | 0.2857 | 0.2776 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | C1\|M_mean3_v2\|a0.25\|H5\|NATIVE | NATIVE | C1 | M_mean3_v2 | NATIVE | 0.25 | 5 | True | 0.2006 | 0.1498 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | C1\|M_mean3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | C1 | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.1045 | 0.09114 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | C1\|M_union3_v2_CVRv5\|a0.25\|H5\|INC1_HG10 | BAND | C1 | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | True | 0.1555 | 0.1447 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | M\|A4b\|a0.25\|H5\|NATIVE | NATIVE | M | A4b | NATIVE | 0.25 | 5 | True | 0.3386 | 0.2736 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | M\|A4b\|a0.25\|H5\|NATIVE_HG10 | BAND | M | A4b | NATIVE_HG10 | 0.25 | 5 | True | 0.3479 | 0.2125 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | M\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | M | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.34 | 0.2745 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | M\|A4b_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | M | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.371 | 0.3839 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | M\|A4b_CVRv5\|a0.25\|H5\|SZL5 | SZL | M | A4b_CVRv5 | SZL5 | 0.25 | 5 | True | 0.2398 | 0.1384 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | M\|M_mean3_v2\|a0.25\|H5\|INC1 | INC | M | M_mean3_v2 | INC1 | 0.25 | 5 | True | 0.3977 | 0.3379 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | M\|M_mean3_v2\|a0.25\|H5\|NATIVE | NATIVE | M | M_mean3_v2 | NATIVE | 0.25 | 5 | True | 0.4361 | 0.4186 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | M\|M_mean3_v2_CVRv5\|a0.25\|H5\|INC1 | INC | M | M_mean3_v2_CVRv5 | INC1 | 0.25 | 5 | True | 0.2247 | 0.172 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | M\|M_union3_v2\|a0.25\|H5\|INC1 | INC | M | M_union3_v2 | INC1 | 0.25 | 5 | True | 0.2595 | 0.2783 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | M\|M_union3_v2\|a0.25\|H5\|NATIVE | NATIVE | M | M_union3_v2 | NATIVE | 0.25 | 5 | True | 0.398 | 0.2775 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | M\|M_union3_v2\|a0.25\|H5\|NATIVE_HG10 | BAND | M | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | True | 0.3104 | 0.3448 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | M\|M_union3_v2\|a0.25\|H5\|SZL5 | SZL | M | M_union3_v2 | SZL5 | 0.25 | 5 | True | 0.3308 | 0.2388 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | M\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | M | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3768 | 0.3079 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | M\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | M | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.3473 | 0.4264 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | M\|M_union3_v2_CVRv5\|a0.25\|H5\|SZL5 | SZL | M | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | True | 0.34 | 0.3027 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | Q\|A4b\|a0.25\|H5\|NATIVE | NATIVE | Q | A4b | NATIVE | 0.25 | 5 | True | 0.3631 | 0.2695 | related_exposed |  | False |
| EXEC_DISCLOSE_ONLY | Q\|A4b\|a0.25\|H5\|NATIVE_HG10 | BAND | Q | A4b | NATIVE_HG10 | 0.25 | 5 | True | 0.5279 | 0.4851 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | Q\|A4b\|a0.25\|H5\|RP3 | RP | Q | A4b | RP3 | 0.25 | 5 | True | 0.165 | 0.2136 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | Q\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | Q | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3638 | 0.2874 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | Q\|A4b_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | Q | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.5176 | 0.5256 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | Q\|M_union3_v2\|a0.25\|H5\|INC1_HG10 | BAND | Q | M_union3_v2 | INC1_HG10 | 0.25 | 5 | True | 0.3813 | 0.4576 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | Q\|M_union3_v2\|a0.25\|H5\|NATIVE_HG10 | BAND | Q | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | True | 0.5354 | 0.6264 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | Q\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | Q | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.251 | 0.3142 | related_exposed |  | False |
| EXEC_DISCLOSE_ONLY | Q\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | Q | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.5357 | 0.6555 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | S\|A4b\|a0.25\|H5\|NATIVE | NATIVE | S | A4b | NATIVE | 0.25 | 5 | True | 0.3997 | 0.3777 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | S\|A4b\|a0.25\|H5\|NATIVE_HG10 | BAND | S | A4b | NATIVE_HG10 | 0.25 | 5 | True | 0.4139 | 0.3352 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | S\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | S | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.4244 | 0.3578 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | S\|A4b_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | S | A4b_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.4176 | 0.4411 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | S\|A4b_CVRv5\|a0.25\|H5\|RP3 | RP | S | A4b_CVRv5 | RP3 | 0.25 | 5 | True | 0.1102 | 0.1287 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | S\|M_mean3_v2\|a0.25\|H5\|RP3 | RP | S | M_mean3_v2 | RP3 | 0.25 | 5 | True | 0.2204 | 0.2108 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | S\|M_union3_v2\|a0.25\|H5\|NATIVE_HG10 | BAND | S | M_union3_v2 | NATIVE_HG10 | 0.25 | 5 | True | 0.4324 | 0.4134 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | S\|M_union3_v2_CVRv5\|a0.25\|H5\|INC1 | INC | S | M_union3_v2_CVRv5 | INC1 | 0.25 | 5 | True | 0.2101 | 0.2426 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | S\|M_union3_v2_CVRv5\|a0.25\|H5\|INC1_HG10 | BAND | S | M_union3_v2_CVRv5 | INC1_HG10 | 0.25 | 5 | True | 0.3916 | 0.4481 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | S\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | S | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3487 | 0.3481 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | S\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE_HG10 | BAND | S | M_union3_v2_CVRv5 | NATIVE_HG10 | 0.25 | 5 | True | 0.44 | 0.49 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_DISCLOSE_ONLY | SM\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | SM | A4b_CVRv5 | NATIVE | 0.25 | 5 | True | 0.2566 | 0.1949 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | SM\|M_union3_v2\|a0.25\|H5\|NATIVE | NATIVE | SM | M_union3_v2 | NATIVE | 0.25 | 5 | True | 0.3699 | 0.3221 | same_account_exposed |  | False |
| EXEC_DISCLOSE_ONLY | SM\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | SM | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3634 | 0.3373 | same_account_exposed |  | False |
| EXEC_LEADER_VS_PARENT | C1\|A4b\|a0.5\|H10\|NATIVE | NATIVE | C1 | A4b | NATIVE | 0.5 | 10 | True | 0.4742 | 0.5273 | same_account_exposed |  | False |
| EXEC_LEADER_VS_PARENT | C1\|A4b\|a0.5\|H20\|NATIVE | NATIVE | C1 | A4b | NATIVE | 0.5 | 20 | True | 0.3358 | 0.3565 | same_account_exposed |  | False |
| EXEC_LEADER_VS_PARENT | C1\|A4b_CVRv5\|a0.5\|H10\|NATIVE | NATIVE | C1 | A4b_CVRv5 | NATIVE | 0.5 | 10 | True | 0.4206 | 0.3958 | same_account_exposed |  | False |
| EXEC_LEADER_VS_PARENT | C1\|A4b_CVRv5\|a0.5\|H20\|NATIVE | NATIVE | C1 | A4b_CVRv5 | NATIVE | 0.5 | 20 | True | 0.2857 | 0.2776 | same_account_exposed |  | False |
| EXEC_LEADER_VS_PARENT | C1\|M_mean3_v2\|a0.25\|H5\|NATIVE | NATIVE | C1 | M_mean3_v2 | NATIVE | 0.25 | 5 | True | 0.2006 | 0.1498 | same_account_exposed |  | False |
| EXEC_LEADER_VS_PARENT | C1\|M_mean3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | C1 | M_mean3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.1045 | 0.09114 | same_account_exposed |  | False |
| EXEC_LEADER_VS_PARENT | M\|A4b_CVRv5\|a0.25\|H5\|SZL5 | SZL | M | A4b_CVRv5 | SZL5 | 0.25 | 5 | True | 0.2398 | 0.1384 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_LEADER_VS_PARENT | M\|M_mean3_v2\|a0.25\|H5\|NATIVE | NATIVE | M | M_mean3_v2 | NATIVE | 0.25 | 5 | True | 0.4361 | 0.4186 | same_account_exposed |  | False |
| EXEC_LEADER_VS_PARENT | M\|M_union3_v2\|a0.25\|H5\|NATIVE | NATIVE | M | M_union3_v2 | NATIVE | 0.25 | 5 | True | 0.398 | 0.2775 | same_account_exposed |  | False |
| EXEC_LEADER_VS_PARENT | M\|M_union3_v2\|a0.25\|H5\|SZL5 | SZL | M | M_union3_v2 | SZL5 | 0.25 | 5 | True | 0.3308 | 0.2388 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_LEADER_VS_PARENT | M\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | M | M_union3_v2_CVRv5 | NATIVE | 0.25 | 5 | True | 0.3768 | 0.3079 | same_account_exposed |  | False |
| EXEC_LEADER_VS_PARENT | M\|M_union3_v2_CVRv5\|a0.25\|H5\|SZL5 | SZL | M | M_union3_v2_CVRv5 | SZL5 | 0.25 | 5 | True | 0.34 | 0.3027 | first_evaluation | NOT_AUTHORIZED | False |
| EXEC_LEADER_VS_PARENT | S\|M_mean3_v2\|a0.25\|H5\|RP3 | RP | S | M_mean3_v2 | RP3 | 0.25 | 5 | True | 0.2204 | 0.2108 | first_evaluation | NOT_AUTHORIZED | False |


研究块候选全表在 `results/full/production_change_candidates_E6k.csv`（逐 profile 分列、不合并、不择优）；研究块候选不替换 144 主对象（brief §10）；新算子行 `replacement_preference_status = NOT_AUTHORIZED`，不自动 chosen。

## 边缘清单（距离、CI、MC 误差；不另设门）

> 表头：主体=边缘对象（主对象；c 或正向距离 < .05，按距离排序）｜算子=见列｜分母=四段有效配对日（FULL = n 加权；G4 = 段中位）｜基准=同 H 原父（8bp）｜子集=policy_E6k.csv 边缘 ∩ 主对象｜单位=年化百分点 / 判词｜日期=2010-01-04..2026-03-27（四段；2026 partial）｜H=H 见描述符｜成本模型=源 8bp（f：A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（e 资本：MATCH-CAP）｜exposure=见 evidence_exposure 列｜query_id=E6K-P3-EDGE


| desc_id | edge_c_margin | edge_f_margin | edge_positive_margin_FULL | edge_years_margin | ci_L20_lo | ci_L20_hi | mcse_2019-2023 | mcse_2024-2026 |
|---|---|---|---|---|---|---|---|---|
| Q\|M_union3_v2_CVRv5\|a0.25\|H5\|SZL5 | -0.00245 | -0.08681 | 0.1018 | -3 | 0.002061 | 0.4021 | 0.004252 | 0.006976 |
| S\|M_mean3_v2_CVRv5\|a0.25\|H5\|RP3 | 0.004454 | 0.04631 | -0.03893 | -3 | -0.04222 | 0.1648 | 0.002394 | 0.003289 |
| C1\|M_mean3_v2_CVRv5\|a0.25\|H5\|NATIVE | 0.1462 | 0.1682 | 0.004461 | 0 | -0.03507 | 0.2393 | 0.004084 | 0.005311 |
| M\|M_mean3_v2\|a0.25\|H5\|NATIVE | 0.005577 | 0.06665 | 0.3361 | 1 | 0.1961 | 0.6759 | 0.004226 | 0.005113 |
| S\|M_union3_v2\|a0.25\|H5\|SZL5 | -0.1148 | -0.148 | 0.009378 | -3 | -0.1109 | 0.3209 | 0.004529 | 0.007337 |
| Q\|M_mean3_v2\|a0.25\|H5\|RP3 | -0.009529 | 0.04628 | 0.05703 | 0 | 0.02507 | 0.2841 | 0.002404 | 0.003443 |
| S\|M_union3_v2_CVRv5\|a0.25\|H5\|SZL5 | 0.009924 | -0.08296 | 0.06657 | -1 | -0.04141 | 0.3695 | 0.004276 | 0.007175 |
| S\|A4b_CVRv5\|a0.25\|H5\|RP3 | 0.1378 | 0.1387 | 0.01018 | 0 | 0.01884 | 0.197 | 0.002246 | 0.004413 |
| C1\|M_union3_v2\|a0.25\|H5\|NATIVE | 0.1305 | 0.08117 | -0.01036 | 0 | -0.06266 | 0.2459 | 0.00459 | 0.007314 |
| C1\|M_mean3_v2_CVRv5\|a0.25\|H5\|INC1 | 0.1088 | 0.1221 | -0.01163 | 0 | -0.0385 | 0.2151 | 0.003986 | 0.004989 |
| M\|A4b_CVRv5\|a0.25\|H5\|INC1 | -0.05608 | -0.03776 | 0.01181 | 0 | -0.06575 | 0.2965 | 0.004108 | 0.007557 |
| M\|A4b\|a0.25\|H5\|INC1 | 0.01334 | 0.05089 | 0.02324 | -1 | -0.07289 | 0.3303 | 0.004481 | 0.007379 |
| C1\|A4b_CVRv5\|a0.25\|H5\|SZL5 | -0.0164 | -0.01041 | 0.024 | -1 | -0.04594 | 0.2898 | 0.004624 | 0.007622 |
| M\|M_mean3_v2\|a0.25\|H5\|RP3 | 0.03202 | 0.04968 | 0.01869 | -1 | 0.02214 | 0.2133 | 0.002548 | 0.00346 |
| S\|A4b\|a0.25\|H5\|INC1 | -0.239 | -0.1552 | -0.01875 | -3 | -0.182 | 0.316 | 0.004879 | 0.006936 |
| C1\|M_mean3_v2\|a0.25\|H5\|RP3 | 0.01899 | 0.02571 | -0.02642 | -3 | 0.02002 | 0.1256 | 0.002582 | 0.003472 |
| M\|A4b\|a0.25\|H5\|RP3 | 0.1025 | 0.09856 | -0.0196 | -2 | 0.001027 | 0.1645 | 0.002545 | 0.004571 |
| C1\|M_mean3_v2\|a0.25\|H5\|NATIVE_HG10 | -0.02132 | 0.01818 | 0.09792 | 0 | -0.03353 | 0.4343 | 0.004506 | 0.005352 |
| S\|A4b\|a0.25\|H5\|SZL5 | -0.442 | -0.3569 | -0.02149 | -2 | -0.1723 | 0.3188 | 0.004934 | 0.00729 |
| Q\|M_mean3_v2\|a0.25\|H5\|INC1 | -0.02342 | 0.1496 | 0.1682 | 1 | 0.06332 | 0.4805 | 0.004001 | 0.005222 |
| C1\|M_union3_v2\|a0.25\|H5\|INC1 | -0.02374 | -0.05871 | -0.06445 | -1 | -0.1007 | 0.173 | 0.004247 | 0.007141 |
| C1\|M_union3_v2_CVRv5\|a0.25\|H5\|INC1 | 0.02428 | -0.01162 | -0.08285 | -2 | -0.1179 | 0.1548 | 0.003975 | 0.006951 |
| Q\|M_union3_v2\|a0.25\|H5\|SZL5 | -0.02553 | -0.114 | 0.05428 | -4 | -0.06497 | 0.3644 | 0.004524 | 0.007241 |
| C1\|A4b\|a0.25\|H5\|SZL5 | 0.07135 | 0.08936 | 0.02585 | -2 | -0.0705 | 0.3107 | 0.004962 | 0.007638 |
| C1\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | 0.133 | 0.05959 | -0.02795 | -2 | -0.07399 | 0.2168 | 0.004283 | 0.007189 |
| C1\|M_mean3_v2_CVRv5\|a0.25\|H5\|RP3 | 0.03006 | 0.03412 | -0.06776 | -4 | -0.0182 | 0.08394 | 0.002376 | 0.003215 |
| M\|A4b_CVRv5\|a0.25\|H5\|RP3 | 0.0895 | 0.08486 | -0.03057 | -2 | 0.000882 | 0.1387 | 0.002223 | 0.004545 |
| Q\|M_mean3_v2\|a0.25\|H5\|NATIVE_HG10 | -0.03194 | 0.209 | 0.1922 | -3 | -0.0002321 | 0.5957 | 0.004397 | 0.00543 |
| S\|A4b\|a0.25\|H5\|NATIVE | 0.0328 | 0.1011 | 0.2997 | 0 | 0.1498 | 0.6517 | 0.004958 | 0.007313 |
| S\|A4b\|a0.25\|H5\|RP3 | 0.1497 | 0.1513 | 0.03408 | -2 | 0.03198 | 0.23 | 0.002633 | 0.004638 |
| Q\|A4b_CVRv5\|a0.25\|H5\|RP3 | 0.1481 | 0.1501 | 0.03435 | -1 | 0.04428 | 0.2225 | 0.00219 | 0.004321 |
| C1\|M_mean3_v2\|a0.25\|H5\|INC1_HG10 | -0.05109 | -0.01578 | -0.03834 | -1 | -0.1416 | 0.2776 | 0.004472 | 0.005239 |
| Q\|A4b_CVRv5\|a0.25\|H5\|SZL5 | -0.09861 | -0.02686 | 0.03935 | -2 | -0.06583 | 0.332 | 0.004481 | 0.007671 |
| S\|M_union3_v2_CVRv5\|a0.25\|H5\|RP3 | 0.04042 | 0.04248 | -0.09656 | -3 | -0.04276 | 0.05014 | 0.001908 | 0.003761 |
| SM\|A4b\|a0.25\|H5\|NATIVE | -0.04118 | -0.01186 | 0.1996 | -1 | 0.06651 | 0.5287 | 0.004334 | 0.006614 |
| S\|A4b_CVRv5\|a0.25\|H5\|SZL5 | -0.1496 | -0.07974 | 0.04141 | -3 | -0.0766 | 0.3438 | 0.004574 | 0.007356 |
| S\|M_mean3_v2\|a0.25\|H5\|INC1 | 0.04196 | 0.2136 | 0.1785 | 0 | 0.05481 | 0.5142 | 0.004127 | 0.004952 |
| S\|A4b_CVRv5\|a0.25\|H5\|INC1 | 0.06199 | 0.1132 | 0.04277 | -2 | -0.09349 | 0.3519 | 0.004442 | 0.00708 |
| C1\|M_union3_v2_CVRv5\|a0.25\|H5\|RP3 | 0.04294 | 0.03945 | -0.09881 | -3 | -0.03962 | 0.04427 | 0.002054 | 0.003711 |
| M\|M_union3_v2_CVRv5\|a0.25\|H5\|RP3 | 0.1096 | 0.0949 | -0.04482 | 0 | 0.001627 | 0.1068 | 0.001923 | 0.003852 |
| M\|M_union3_v2\|a0.25\|H5\|INC1 | 0.04526 | 0.006367 | 0.1595 | 0 | 0.06196 | 0.4666 | 0.004458 | 0.00725 |
| Q\|M_union3_v2\|a0.25\|H5\|NATIVE | 0.04685 | -0.03925 | 0.1276 | -2 | 0.02649 | 0.435 | 0.004611 | 0.00731 |
| M\|A4b\|a0.25\|H5\|NATIVE | 0.04806 | 0.07238 | 0.2386 | 2 | 0.1176 | 0.5664 | 0.004901 | 0.007873 |


> 表头：主体=边缘对象计数（全部登记对象；逐族 × 算子）｜算子=见列｜分母=四段有效配对日（FULL = n 加权；G4 = 段中位）｜基准=同 H 原父（8bp）｜子集=policy_E6k.csv 边缘｜单位=计数 / 年化百分点｜日期=2010-01-04..2026-03-27（四段；2026 partial）｜H=H 1…20｜成本模型=源 8bp（f：A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（e 资本：MATCH-CAP）｜exposure=见 evidence_exposure 列｜query_id=E6K-P3-EDGE-COUNT


| family | op | edge_objects | median_min_dist |
|---|---|---|---|
| BAND | INC1_HG10 | 161 | 0.02467 |
| BAND | INC1_HG15 | 105 | 0.02428 |
| BAND | INC1_HG5 | 231 | 0.02071 |
| BAND | INC1_PM10 | 214 | 0.02556 |
| BAND | INC1_PM15 | 147 | 0.02488 |
| BAND | INC1_PM5 | 218 | 0.02691 |
| BAND | INC1_SA10 | 256 | 0.02733 |
| BAND | INC1_SA15 | 275 | 0.02487 |
| BAND | INC1_SA5 | 228 | 0.02483 |
| BAND | NATIVE_HG10 | 93 | 0.02444 |
| BAND | NATIVE_HG15 | 68 | 0.02138 |
| BAND | NATIVE_HG5 | 104 | 0.03271 |
| BAND | NATIVE_PM10 | 192 | 0.02068 |
| BAND | NATIVE_PM15 | 127 | 0.02686 |
| BAND | NATIVE_PM5 | 161 | 0.02735 |
| BAND | NATIVE_SA10 | 172 | 0.01834 |
| BAND | NATIVE_SA15 | 179 | 0.01695 |
| BAND | NATIVE_SA5 | 181 | 0.01984 |
| HG_ONLY | HG_ONLY10 | 91 | 0.01998 |
| HG_ONLY | HG_ONLY15 | 92 | 0.02618 |
| HG_ONLY | HG_ONLY5 | 50 | 0.02121 |
| INC | INC05 | 789 | 0.02195 |
| INC | INC1 | 974 | 0.02331 |
| LX | LX_ISK_01 | 714 | 0.02735 |
| LX | LX_ISK_10 | 797 | 0.02241 |
| LX | LX_SIZE3_01 | 881 | 0.02242 |
| LX | LX_SIZE3_10 | 1122 | 0.02297 |
| NATIVE | NATIVE | 948 | 0.02366 |
| OWN | SZL3_OWN | 275 | 0.03012 |
| OWN | SZL5_OWN | 310 | 0.01899 |
| POST2 | POST2_INCREMENT | 101 | 0.02405 |
| RP | RP0p5 | 755 | 0.02581 |
| RP | RP1 | 740 | 0.02656 |
| RP | RP3 | 853 | 0.0265 |
| RP | RPINF | 825 | 0.02657 |
| SZL | SZL3 | 801 | 0.02222 |
| SZL | SZL5 | 782 | 0.02231 |
| TREFIT | TREFIT0 | 174 | 0.02152 |
| TREFIT | TREFIT0p5 | 163 | 0.01767 |

