# E6l REPORT part3 —— 正式尺子（六条 + PROPOSED_PORT3_T）与完整候选

用途：plan §13.4 part3 / §10。尺子 = `registration/policy_profiles_E6l.json`（policy_provisional = false；PORT3_T 正式列；LEGACY_EDIT5 / PORT3_LAG1 / DISCLOSE 并印；LEADER 只披露）；判定串顺序 c、d、f、正向门槛、e资本、e随机、size(profile)。新算子 replacement_status = NOT_AUTHORIZED（不 chosen）；deployment_authorized = false；任何"通过"只进《生产变更候选清单》，由用户裁定。

## 1. 判定计数（按族 × profile × 聚合）

> 表头：主体=政策判定计数｜算子=全部算子｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父（8bp）｜子集=全部登记（不含 PARENT）｜单位=计数｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=H 1…20｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-P3-COUNTS


| profile | aggregation | family | objects | pass | fail | undecidable |
|---|---|---|---|---|---|---|
| PROPOSED_PORT3_T | FULL | HG | 16560 | 1373 | 11910 | 3277 |
| PROPOSED_PORT3_T | FULL | MEMORY | 5760 | 638 | 3733 | 1389 |
| PROPOSED_PORT3_T | FULL | NATIVE | 1440 | 211 | 721 | 508 |
| PROPOSED_PORT3_T | FULL | OLD_RULE | 1560 | 0 | 1281 | 279 |
| PROPOSED_PORT3_T | FULL | SMOOTH | 4320 | 117 | 4002 | 201 |
| PROPOSED_PORT3_T | FULL | STATE | 4320 | 492 | 2654 | 1174 |
| PROPOSED_PORT3_T | G4 | HG | 16560 | 1356 | 12057 | 3147 |
| PROPOSED_PORT3_T | G4 | MEMORY | 5760 | 636 | 3789 | 1335 |
| PROPOSED_PORT3_T | G4 | NATIVE | 1440 | 205 | 752 | 483 |
| PROPOSED_PORT3_T | G4 | OLD_RULE | 1560 | 0 | 1264 | 296 |
| PROPOSED_PORT3_T | G4 | SMOOTH | 4320 | 111 | 4033 | 176 |
| PROPOSED_PORT3_T | G4 | STATE | 4320 | 480 | 2734 | 1106 |
| LEGACY_EDIT5 | FULL | HG | 16560 | 224 | 15872 | 464 |
| LEGACY_EDIT5 | FULL | MEMORY | 5760 | 126 | 5373 | 261 |
| LEGACY_EDIT5 | FULL | NATIVE | 1440 | 46 | 1271 | 123 |
| LEGACY_EDIT5 | FULL | OLD_RULE | 1560 | 0 | 1523 | 37 |
| LEGACY_EDIT5 | FULL | SMOOTH | 4320 | 7 | 4313 | 0 |
| LEGACY_EDIT5 | FULL | STATE | 4320 | 149 | 3830 | 341 |
| LEGACY_EDIT5 | G4 | HG | 16560 | 220 | 15909 | 431 |
| LEGACY_EDIT5 | G4 | MEMORY | 5760 | 123 | 5400 | 237 |
| LEGACY_EDIT5 | G4 | NATIVE | 1440 | 44 | 1280 | 116 |
| LEGACY_EDIT5 | G4 | OLD_RULE | 1560 | 0 | 1529 | 31 |
| LEGACY_EDIT5 | G4 | SMOOTH | 4320 | 3 | 4317 | 0 |
| LEGACY_EDIT5 | G4 | STATE | 4320 | 144 | 3857 | 319 |
| PROPOSED_PORT3_LAG1 | FULL | HG | 16560 | 1379 | 11890 | 3291 |
| PROPOSED_PORT3_LAG1 | FULL | MEMORY | 5760 | 638 | 3733 | 1389 |
| PROPOSED_PORT3_LAG1 | FULL | NATIVE | 1440 | 211 | 721 | 508 |
| PROPOSED_PORT3_LAG1 | FULL | OLD_RULE | 1560 | 0 | 1281 | 279 |
| PROPOSED_PORT3_LAG1 | FULL | SMOOTH | 4320 | 117 | 4002 | 201 |
| PROPOSED_PORT3_LAG1 | FULL | STATE | 4320 | 494 | 2652 | 1174 |
| PROPOSED_PORT3_LAG1 | G4 | HG | 16560 | 1362 | 12037 | 3161 |
| PROPOSED_PORT3_LAG1 | G4 | MEMORY | 5760 | 636 | 3789 | 1335 |
| PROPOSED_PORT3_LAG1 | G4 | NATIVE | 1440 | 205 | 752 | 483 |
| PROPOSED_PORT3_LAG1 | G4 | OLD_RULE | 1560 | 0 | 1264 | 296 |
| PROPOSED_PORT3_LAG1 | G4 | SMOOTH | 4320 | 111 | 4033 | 176 |
| PROPOSED_PORT3_LAG1 | G4 | STATE | 4320 | 482 | 2732 | 1106 |
| EXEC_DISCLOSE_ONLY | FULL | HG | 16560 | 1511 | 11489 | 3560 |
| EXEC_DISCLOSE_ONLY | FULL | MEMORY | 5760 | 708 | 3525 | 1527 |
| EXEC_DISCLOSE_ONLY | FULL | NATIVE | 1440 | 211 | 721 | 508 |
| EXEC_DISCLOSE_ONLY | FULL | OLD_RULE | 1560 | 0 | 1281 | 279 |
| EXEC_DISCLOSE_ONLY | FULL | SMOOTH | 4320 | 127 | 3984 | 209 |
| EXEC_DISCLOSE_ONLY | FULL | STATE | 4320 | 541 | 2497 | 1282 |
| EXEC_DISCLOSE_ONLY | G4 | HG | 16560 | 1494 | 11636 | 3430 |
| EXEC_DISCLOSE_ONLY | G4 | MEMORY | 5760 | 706 | 3581 | 1473 |
| EXEC_DISCLOSE_ONLY | G4 | NATIVE | 1440 | 205 | 752 | 483 |
| EXEC_DISCLOSE_ONLY | G4 | OLD_RULE | 1560 | 0 | 1264 | 296 |
| EXEC_DISCLOSE_ONLY | G4 | SMOOTH | 4320 | 121 | 4015 | 184 |
| EXEC_DISCLOSE_ONLY | G4 | STATE | 4320 | 529 | 2577 | 1214 |


## 2. 主展示 72 与剂量面板的正式判定

> 表头：主体=主展示 72｜算子=12 配方｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父（8bp）｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-P3-PRIMARY72


| recipe | mother | FULL_ann_pp | G4_ann_pp | FULL_sc_ann_pp | c_d10 | d_ok | years_pos | f_d10 | positive_FULL | e_cap_FULL | e_rand | size_PROPOSED_PORT3_T | policy_PROPOSED_PORT3_T_FULL | policy_PROPOSED_PORT3_T_G4 | POLICY_INTERPRETATION_PENDING_PROPOSED_PORT3_T | evidence_column |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q0:DECAY5_10 | A4b | 0.532 | 0.4745 | 0.5378 | True | True | 14 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | A4b_CVRv5 | 0.519 | 0.5289 | 0.4907 | True | True | 14 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | M_mean3_v2 | 0.3009 | 0.1167 | 0.3193 | False | False | 8 | True | True | PASS | PASS | PASS | 不通过（c、d） | 不通过（c、d） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | M_mean3_v2_CVRv5 | -0.05638 | -0.06634 | -0.05436 | False | False | 6 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | M_union3_v2 | 0.4686 | 0.4788 | 0.1498 | True | True | 14 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | M_union3_v2_CVRv5 | 0.4706 | 0.555 | 0.1431 | True | True | 14 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:HG10 | A4b | 0.5279 | 0.4851 | 0.5331 | True | True | 14 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 上一轮（同构再评，只作锚） |
| Q0:HG10 | A4b_CVRv5 | 0.5176 | 0.5256 | 0.4858 | True | True | 13 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 上一轮（同构再评，只作锚） |
| Q0:HG10 | M_mean3_v2 | 0.2922 | 0.1053 | 0.3124 | False | False | 9 | True | True | PASS | PASS | PASS | 不通过（c、d） | 不通过（c、d） | False | 上一轮（同构再评，只作锚） |
| Q0:HG10 | M_mean3_v2_CVRv5 | -0.05299 | -0.06691 | -0.051 | False | False | 6 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 上一轮（同构再评，只作锚） |
| Q0:HG10 | M_union3_v2 | 0.5354 | 0.6264 | 0.2134 | True | True | 14 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 上一轮（同构再评，只作锚） |
| Q0:HG10 | M_union3_v2_CVRv5 | 0.5357 | 0.6555 | 0.2051 | True | True | 13 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 上一轮（同构再评，只作锚） |
| Q0:INV10 | A4b | 0.3438 | 0.3111 | 0.3504 | True | False | 11 | True | True | PASS | PASS | PASS | 不通过（d） | 不通过（d） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | A4b_CVRv5 | 0.3381 | 0.2378 | 0.2956 | True | False | 11 | True | True | PASS | PASS | PASS | 不通过（d） | 不通过（d） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | M_mean3_v2 | 0.3861 | 0.1501 | 0.4038 | True | False | 10 | True | True | PASS | PASS | PASS | 不通过（d） | 不通过（d） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | M_mean3_v2_CVRv5 | -0.09855 | -0.1082 | -0.1019 | False | False | 6 | True | False | PASS | PASS | PASS | 不通过（c、d、正向门槛） | 不通过（c、d、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | M_union3_v2 | 0.4824 | 0.4062 | -0.09933 | True | True | 13 | False | True | FAIL | PASS | PASS | 不通过（f、e资本） | 不通过（f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | M_union3_v2_CVRv5 | 0.5208 | 0.4574 | -0.08371 | True | True | 13 | False | True | FAIL | PASS | PASS | 不通过（f、e资本） | 不通过（f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | A4b | 0.4889 | 0.4365 | 0.4945 | True | True | 14 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | A4b_CVRv5 | 0.4819 | 0.5085 | 0.4531 | True | True | 13 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | M_mean3_v2 | 0.2472 | 0.1108 | 0.2656 | False | False | 9 | True | True | PASS | PASS | PASS | 不通过（c、d） | 不通过（c、d） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | M_mean3_v2_CVRv5 | -0.1062 | -0.07999 | -0.1039 | False | False | 6 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | M_union3_v2 | 0.399 | 0.4672 | 0.09716 | True | True | 14 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | M_union3_v2_CVRv5 | 0.4074 | 0.5152 | 0.09517 | True | True | 13 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:NATIVE | A4b | 0.3631 | 0.2695 | 0.3678 | True | True | 12 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | A4b_CVRv5 | 0.3638 | 0.2874 | 0.346 | True | True | 12 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | M_mean3_v2 | 0.318 | 0.1509 | 0.3278 | False | False | 10 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | M_mean3_v2_CVRv5 | -0.09518 | -0.171 | -0.09628 | False | False | 5 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | M_union3_v2 | 0.2276 | 0.265 | 0.004184 | True | False | 10 | False | True | PASS | PASS | PASS | 不通过（d、f） | 不通过（d、f） | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | M_union3_v2_CVRv5 | 0.251 | 0.3142 | 0.01981 | True | True | 12 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 上一轮（同构再评，只作锚） |
| Q_D3:NATIVE | A4b | 0.1652 | 0.1351 | 0.1598 | False | True | 12 | False | True | PASS | FAIL | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | A4b_CVRv5 | 0.1793 | 0.16 | 0.1598 | False | True | 13 | False | True | PASS | FAIL | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | M_mean3_v2 | 0.1561 | 0.1446 | 0.1706 | False | False | 10 | False | True | PASS | FAIL | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | M_mean3_v2_CVRv5 | -0.226 | -0.2113 | -0.233 | False | False | 6 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | M_union3_v2 | 0.1028 | 0.03077 | -0.2071 | False | False | 10 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、正向门槛、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | M_union3_v2_CVRv5 | 0.1735 | 0.1263 | -0.1426 | False | True | 12 | False | True | FAIL | PASS | PASS | 不通过（c、f、e资本） | 不通过（c、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | A4b | 0.2761 | 0.2134 | 0.2801 | False | True | 12 | False | True | PASS | FAIL | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | A4b_CVRv5 | 0.2728 | 0.2394 | 0.2426 | False | True | 12 | False | True | PASS | FAIL | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | M_mean3_v2 | 0.1926 | 0.02559 | 0.2224 | False | False | 10 | False | True | PASS | FAIL | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | M_mean3_v2_CVRv5 | -0.1903 | -0.2763 | -0.1802 | False | False | 6 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | M_union3_v2 | 0.197 | 0.217 | -0.2062 | True | True | 13 | False | True | FAIL | FAIL | PASS | 不通过（f、e资本、e随机） | 不通过（f、e资本、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | M_union3_v2_CVRv5 | 0.273 | 0.3278 | -0.1568 | True | True | 13 | True | True | FAIL | PASS | PASS | 不通过（e资本） | 不通过（e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | A4b | 0.06594 | -0.001793 | 0.0655 | False | False | 9 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e资本、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | A4b_CVRv5 | 0.08245 | 0.03853 | 0.05693 | False | False | 11 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | M_mean3_v2 | 0.1006 | 0.06648 | 0.1182 | False | False | 10 | False | True | PASS | FAIL | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | M_mean3_v2_CVRv5 | -0.2706 | -0.2283 | -0.2804 | False | False | 5 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | M_union3_v2 | 0.09425 | 0.01766 | -0.2449 | False | False | 9 | False | False | FAIL | FAIL | PASS | 不通过（c、d、f、正向门槛、e资本、e随机） | 不通过（c、d、f、正向门槛、e资本、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | M_union3_v2_CVRv5 | 0.1371 | 0.1152 | -0.2141 | False | False | 11 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | A4b | 0.3004 | 0.317 | 0.311 | False | True | 13 | False | True | PASS | FAIL | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | A4b_CVRv5 | 0.2828 | 0.3099 | 0.2534 | False | True | 13 | False | True | PASS | FAIL | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | M_mean3_v2 | 0.1579 | 0.01805 | 0.1863 | False | False | 10 | False | True | PASS | FAIL | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | M_mean3_v2_CVRv5 | -0.2417 | -0.2996 | -0.2371 | False | False | 7 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | M_union3_v2 | 0.2434 | 0.2924 | -0.2153 | False | True | 12 | False | True | FAIL | MC_UNRESOLVED | PASS | 不通过（c、f、e资本） | 不通过（c、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | M_union3_v2_CVRv5 | 0.3224 | 0.4293 | -0.1629 | True | True | 13 | False | True | FAIL | PASS | PASS | 不通过（f、e资本） | 不通过（f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | A4b | 0.07291 | -0.01955 | 0.07954 | False | False | 11 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | A4b_CVRv5 | 0.07016 | 0.02314 | 0.05887 | False | False | 11 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | M_mean3_v2 | 0.191 | 0.2006 | 0.2085 | False | False | 10 | False | True | PASS | FAIL | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | M_mean3_v2_CVRv5 | -0.2558 | -0.2064 | -0.2601 | False | False | 4 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | M_union3_v2 | 0.09204 | 0.06192 | -0.2861 | False | False | 9 | False | False | FAIL | PASS | PASS | 不通过（c、d、f、正向门槛、e资本） | 不通过（c、d、f、正向门槛、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | M_union3_v2_CVRv5 | 0.1438 | 0.1452 | -0.2511 | False | False | 9 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | A4b | 0.4031 | 0.4369 | 0.4114 | True | True | 14 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | A4b_CVRv5 | 0.4536 | 0.4558 | 0.4411 | True | True | 13 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | M_mean3_v2 | 0.2906 | 0.08745 | 0.3035 | False | True | 12 | False | True | PASS | PASS | PASS | 不通过（c、f） | 不通过（c、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | M_mean3_v2_CVRv5 | 0.02612 | -0.07859 | 0.03426 | False | False | 8 | False | False | PASS | MC_UNRESOLVED | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | M_union3_v2 | 0.1735 | 0.2609 | -0.1194 | False | False | 9 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | M_union3_v2_CVRv5 | 0.2117 | 0.3215 | -0.09028 | True | True | 12 | False | True | FAIL | PASS | PASS | 不通过（f、e资本） | 不通过（f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | A4b | 0.2847 | 0.2055 | 0.2867 | False | True | 13 | False | True | PASS | PASS | PASS | 不通过（c、f） | 不通过（c、f） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | A4b_CVRv5 | 0.2224 | 0.17 | 0.2171 | True | True | 13 | True | True | PASS | MC_UNRESOLVED | PASS | 不可判（e随机:MC_UNRESOLVED） | 不可判（e随机:MC_UNRESOLVED） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | M_mean3_v2 | 0.2373 | 0.1238 | 0.2492 | False | False | 10 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | M_mean3_v2_CVRv5 | -0.01106 | -0.08531 | -0.01176 | False | False | 9 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | M_union3_v2 | 0.122 | 0.1062 | -0.08468 | False | False | 6 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | M_union3_v2_CVRv5 | 0.1264 | 0.1206 | -0.08896 | False | False | 8 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |


> 表头：主体=α .5 剂量面板｜算子=12 配方｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父（8bp）｜子集=dose72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-P3-DOSE72


| recipe | mother | FULL_ann_pp | G4_ann_pp | FULL_sc_ann_pp | c_d10 | d_ok | years_pos | f_d10 | positive_FULL | e_cap_FULL | e_rand | size_PROPOSED_PORT3_T | policy_PROPOSED_PORT3_T_FULL | policy_PROPOSED_PORT3_T_G4 | POLICY_INTERPRETATION_PENDING_PROPOSED_PORT3_T | evidence_column |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q0:DECAY5_10 | A4b | 1.431 | 1.722 | 1.407 | True | True | 15 | True | True | PASS | PASS | FAIL | 不通过（size(PROPOSED_PORT3_T)） | 不通过（size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | A4b_CVRv5 | 1.164 | 1.391 | 1.066 | True | True | 13 | True | True | PASS | PASS | FAIL | 不通过（size(PROPOSED_PORT3_T)） | 不通过（size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | M_mean3_v2 | 0.3004 | -0.03955 | 0.3285 | False | False | 8 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | M_mean3_v2_CVRv5 | -0.262 | -0.378 | -0.2574 | False | False | 5 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | M_union3_v2 | 0.797 | 1.256 | 0.1101 | False | False | 10 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | M_union3_v2_CVRv5 | 0.8226 | 1.202 | 0.08119 | False | True | 12 | False | True | PASS | PASS | PASS | 不通过（c、f） | 不通过（c、f） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:HG10 | A4b | 1.372 | 1.634 | 1.351 | True | True | 15 | True | True | PASS | PASS | FAIL | 不通过（size(PROPOSED_PORT3_T)） | 不通过（size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:HG10 | A4b_CVRv5 | 1.109 | 1.281 | 1.021 | True | True | 13 | True | True | PASS | PASS | FAIL | 不通过（size(PROPOSED_PORT3_T)） | 不通过（size(PROPOSED_PORT3_T)） | False | 上一轮（同构再评，只作锚） |
| Q0:HG10 | M_mean3_v2 | 0.3248 | -0.02559 | 0.3527 | False | False | 8 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:HG10 | M_mean3_v2_CVRv5 | -0.2462 | -0.3628 | -0.2424 | False | False | 5 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:HG10 | M_union3_v2 | 0.7043 | 0.9979 | 0.0411 | False | False | 9 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:HG10 | M_union3_v2_CVRv5 | 0.7531 | 1.004 | 0.03221 | False | False | 11 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | A4b | 0.96 | 0.7926 | 0.9534 | True | True | 13 | True | True | PASS | PASS | FAIL | 不通过（size(PROPOSED_PORT3_T)） | 不通过（size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | A4b_CVRv5 | 0.7354 | 0.6467 | 0.6035 | True | False | 11 | True | True | PASS | PASS | FAIL | 不通过（d、size(PROPOSED_PORT3_T)） | 不通过（d、size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | M_mean3_v2 | 0.3716 | -0.04756 | 0.4013 | False | False | 8 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | M_mean3_v2_CVRv5 | -0.2326 | -0.3739 | -0.2336 | False | False | 5 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | M_union3_v2 | 0.8606 | 1.19 | -0.2033 | False | False | 10 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | M_union3_v2_CVRv5 | 0.9687 | 1.297 | -0.181 | False | False | 11 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | A4b | 1.216 | 1.319 | 1.207 | True | True | 15 | True | True | PASS | PASS | FAIL | 不通过（size(PROPOSED_PORT3_T)） | 不通过（size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | A4b_CVRv5 | 0.9569 | 0.9502 | 0.8672 | True | True | 14 | True | True | PASS | PASS | FAIL | 不通过（size(PROPOSED_PORT3_T)） | 不通过（size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | M_mean3_v2 | 0.3272 | -0.02613 | 0.3537 | False | False | 7 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | M_mean3_v2_CVRv5 | -0.2297 | -0.3743 | -0.2234 | False | False | 5 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | M_union3_v2 | 0.7066 | 1.25 | 0.05832 | False | False | 9 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | M_union3_v2_CVRv5 | 0.733 | 1.204 | 0.03853 | False | False | 10 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:NATIVE | A4b | 1.009 | 0.8341 | 1.01 | False | True | 15 | True | True | PASS | PASS | PASS | 不通过（c） | 不通过（c） | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | A4b_CVRv5 | 0.6671 | 0.6556 | 0.579 | False | True | 14 | False | True | PASS | PASS | PASS | 不通过（c、f） | 不通过（c、f） | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | M_mean3_v2 | 0.3136 | 0.06387 | 0.3394 | False | False | 8 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f、正向门槛） | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | M_mean3_v2_CVRv5 | -0.2494 | -0.3602 | -0.2393 | False | False | 5 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | M_union3_v2 | 0.4886 | 0.6044 | -0.06788 | False | False | 11 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f） | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | M_union3_v2_CVRv5 | 0.5007 | 0.5519 | -0.08982 | True | False | 10 | False | True | FAIL | PASS | PASS | 不通过（d、f、e资本） | 不通过（d、f） | False | 上一轮（同构再评，只作锚） |
| Q_D3:NATIVE | A4b | 0.3398 | 0.2854 | 0.3376 | False | False | 9 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | A4b_CVRv5 | -0.05775 | -0.02452 | -0.1648 | False | False | 7 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | M_mean3_v2 | 0.04373 | -0.2716 | 0.086 | False | False | 8 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | M_mean3_v2_CVRv5 | -0.5339 | -0.7072 | -0.5257 | False | False | 5 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | M_union3_v2 | 0.2496 | 0.1337 | -0.3062 | False | False | 9 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | M_union3_v2_CVRv5 | 0.2575 | 0.07877 | -0.3232 | False | False | 9 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、正向门槛、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | A4b | 0.3546 | 0.3222 | 0.3676 | False | False | 9 | False | True | PASS | FAIL | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | A4b_CVRv5 | 0.1851 | 0.2913 | 0.07317 | False | False | 9 | False | True | PASS | FAIL | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | M_mean3_v2 | -0.05229 | -0.4172 | 0.003649 | False | False | 8 | False | False | FAIL | FAIL | PASS | 不通过（c、d、f、正向门槛、e资本、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | M_mean3_v2_CVRv5 | -0.5761 | -0.7438 | -0.5549 | False | False | 6 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | M_union3_v2 | 0.3232 | 0.2663 | -0.3727 | False | False | 9 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | M_union3_v2_CVRv5 | 0.4092 | 0.2844 | -0.3411 | False | False | 11 | False | True | FAIL | PASS | FAIL | 不通过（c、d、f、e资本、size(PROPOSED_PORT3_T)） | 不通过（c、d、f、e资本、size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | A4b | 0.08204 | 0.1384 | 0.09628 | False | False | 9 | False | False | PASS | FAIL | FAIL | 不通过（c、d、f、正向门槛、e随机、size(PROPOSED_PORT3_T)） | 不通过（c、d、f、e随机、size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | A4b_CVRv5 | -0.2349 | -0.06152 | -0.3131 | False | False | 8 | False | False | PASS | FAIL | FAIL | 不通过（c、d、f、正向门槛、e随机、size(PROPOSED_PORT3_T)） | 不通过（c、d、f、正向门槛、e随机、size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | M_mean3_v2 | 0.01037 | -0.18 | 0.0545 | False | False | 7 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | M_mean3_v2_CVRv5 | -0.5131 | -0.5635 | -0.5012 | False | False | 6 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | M_union3_v2 | 0.002247 | -0.1874 | -0.6021 | False | False | 8 | False | False | FAIL | PASS | FAIL | 不通过（c、d、f、正向门槛、e资本、size(PROPOSED_PORT3_T)） | 不通过（c、d、f、正向门槛、size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | M_union3_v2_CVRv5 | 0.04554 | -0.143 | -0.5897 | False | False | 9 | False | False | FAIL | PASS | FAIL | 不通过（c、d、f、正向门槛、e资本、size(PROPOSED_PORT3_T)） | 不通过（c、d、f、正向门槛、size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | A4b | 0.571 | 0.4916 | 0.5867 | False | False | 11 | False | True | PASS | FAIL | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | A4b_CVRv5 | 0.2206 | 0.2569 | 0.1044 | False | False | 11 | False | True | PASS | FAIL | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | M_mean3_v2 | -0.01658 | -0.2105 | 0.03278 | False | False | 6 | False | False | FAIL | FAIL | PASS | 不通过（c、d、f、正向门槛、e资本、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | M_mean3_v2_CVRv5 | -0.5793 | -0.6355 | -0.5766 | False | False | 5 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | M_union3_v2 | 0.3817 | 0.3611 | -0.4775 | False | False | 10 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | M_union3_v2_CVRv5 | 0.4503 | 0.3353 | -0.4564 | False | False | 10 | False | True | FAIL | PASS | FAIL | 不通过（c、d、f、e资本、size(PROPOSED_PORT3_T)） | 不通过（c、d、f、e资本、size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | A4b | 0.5526 | 0.6112 | 0.5723 | False | False | 11 | False | True | PASS | FAIL | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | A4b_CVRv5 | 0.1278 | 0.2926 | 0.02173 | False | False | 8 | False | True | PASS | FAIL | FAIL | 不通过（c、d、f、e随机、size(PROPOSED_PORT3_T)） | 不通过（c、d、f、e随机、size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | M_mean3_v2 | 0.008607 | -0.2309 | 0.0505 | False | False | 7 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | M_mean3_v2_CVRv5 | -0.5763 | -0.6299 | -0.5701 | False | False | 5 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | M_union3_v2 | 0.2928 | 0.1209 | -0.4627 | False | False | 8 | False | True | FAIL | PASS | FAIL | 不通过（c、d、f、e资本、size(PROPOSED_PORT3_T)） | 不通过（c、d、f、e资本、size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | M_union3_v2_CVRv5 | 0.3414 | 0.1393 | -0.4549 | False | False | 8 | False | True | FAIL | PASS | FAIL | 不通过（c、d、f、e资本、size(PROPOSED_PORT3_T)） | 不通过（c、d、f、e资本、size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | A4b | 0.7224 | 0.7479 | 0.7343 | False | False | 11 | True | True | PASS | PASS | FAIL | 不通过（c、d、size(PROPOSED_PORT3_T)） | 不通过（c、d、size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | A4b_CVRv5 | 0.6902 | 0.7269 | 0.6616 | True | False | 11 | True | True | PASS | PASS | FAIL | 不通过（d、size(PROPOSED_PORT3_T)） | 不通过（d、size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | M_mean3_v2 | 0.0587 | -0.3103 | 0.08482 | False | False | 6 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | M_mean3_v2_CVRv5 | -0.3324 | -0.5412 | -0.3258 | False | False | 4 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | M_union3_v2 | 0.2447 | 0.5258 | -0.1409 | False | False | 9 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | M_union3_v2_CVRv5 | 0.1909 | 0.3963 | -0.2268 | False | False | 8 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | A4b | 0.4576 | 0.405 | 0.4659 | False | False | 10 | False | True | PASS | PASS | FAIL | 不通过（c、d、f、size(PROPOSED_PORT3_T)） | 不通过（c、d、f、size(PROPOSED_PORT3_T)） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | A4b_CVRv5 | 0.3849 | 0.274 | 0.3539 | False | False | 11 | True | True | PASS | PASS | PASS | 不通过（c、d） | 不通过（c、d） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | M_mean3_v2 | 0.1087 | -0.1529 | 0.1331 | False | False | 7 | False | True | PASS | PASS | PASS | 不通过（c、d、f） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | M_mean3_v2_CVRv5 | -0.2868 | -0.4514 | -0.2821 | False | False | 4 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | M_union3_v2 | 0.2085 | 0.4632 | -0.07477 | False | False | 7 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | M_union3_v2_CVRv5 | 0.1589 | 0.2529 | -0.1438 | False | False | 8 | False | True | FAIL | PASS | PASS | 不通过（c、d、f、e资本） | 不通过（c、d、f、e资本） | False | 本轮新证据（首评，重复使用的历史） |


> 表头：主体=α .125 邻域｜算子=12 配方｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父（8bp）｜子集=nbhd72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-P3-NBHD72


| recipe | mother | FULL_ann_pp | G4_ann_pp | FULL_sc_ann_pp | c_d10 | d_ok | years_pos | f_d10 | positive_FULL | e_cap_FULL | e_rand | size_PROPOSED_PORT3_T | policy_PROPOSED_PORT3_T_FULL | policy_PROPOSED_PORT3_T_G4 | POLICY_INTERPRETATION_PENDING_PROPOSED_PORT3_T | evidence_column |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q0:DECAY5_10 | A4b | 0.2655 | 0.2292 | 0.2747 | True | True | 15 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | A4b_CVRv5 | 0.3026 | 0.2868 | 0.2965 | True | True | 15 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | M_mean3_v2 | 0.199 | 0.1282 | 0.2036 | True | True | 13 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | M_mean3_v2_CVRv5 | -0.04623 | -0.04793 | -0.04258 | False | False | 9 | True | False | PASS | PASS | PASS | 不通过（c、d、正向门槛） | 不通过（c、d、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | M_union3_v2 | 0.3343 | 0.3231 | 0.158 | True | True | 15 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:DECAY5_10 | M_union3_v2_CVRv5 | 0.32 | 0.3179 | 0.1432 | True | True | 17 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:HG10 | A4b | 0.2839 | 0.2379 | 0.2945 | True | True | 14 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:HG10 | A4b_CVRv5 | 0.3183 | 0.29 | 0.3108 | True | True | 15 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 上一轮（同构再评，只作锚） |
| Q0:HG10 | M_mean3_v2 | 0.2035 | 0.1196 | 0.2094 | True | True | 12 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:HG10 | M_mean3_v2_CVRv5 | -0.03743 | -0.02572 | -0.0333 | False | False | 9 | True | False | PASS | PASS | PASS | 不通过（c、d、正向门槛） | 不通过（c、d、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:HG10 | M_union3_v2 | 0.324 | 0.2997 | 0.1494 | True | True | 15 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:HG10 | M_union3_v2_CVRv5 | 0.3083 | 0.2784 | 0.1344 | True | True | 17 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | A4b | 0.1973 | 0.1038 | 0.2051 | True | False | 10 | True | True | PASS | PASS | PASS | 不通过（d） | 不通过（d） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | A4b_CVRv5 | 0.1899 | 0.1858 | 0.163 | True | False | 11 | True | True | PASS | FAIL | PASS | 不通过（d、e随机） | 不通过（d、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | M_mean3_v2 | 0.1394 | 0.08794 | 0.1456 | False | True | 13 | True | True | PASS | PASS | PASS | 不通过（c） | 不通过（c、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | M_mean3_v2_CVRv5 | -0.1245 | -0.115 | -0.1251 | False | False | 5 | True | False | PASS | PASS | PASS | 不通过（c、d、正向门槛） | 不通过（c、d、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | M_union3_v2 | 0.3671 | 0.4083 | -0.04304 | True | True | 12 | False | True | FAIL | PASS | PASS | 不通过（f、e资本） | 不通过（f） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:INV10 | M_union3_v2_CVRv5 | 0.3738 | 0.4493 | -0.04494 | True | True | 13 | False | True | FAIL | PASS | PASS | 不通过（f、e资本） | 不通过（f） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | A4b | 0.2703 | 0.2619 | 0.2763 | False | True | 12 | True | True | PASS | FAIL | PASS | 不通过（c、e随机） | 不通过（c、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | A4b_CVRv5 | 0.3069 | 0.2404 | 0.2939 | True | True | 15 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | M_mean3_v2 | 0.1902 | 0.1463 | 0.1941 | True | True | 13 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | M_mean3_v2_CVRv5 | -0.02447 | -0.02198 | -0.02234 | True | False | 8 | True | False | PASS | PASS | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | M_union3_v2 | 0.2726 | 0.3097 | 0.101 | True | True | 14 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:LAG1_10 | M_union3_v2_CVRv5 | 0.2733 | 0.3193 | 0.1049 | True | True | 16 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q0:NATIVE | A4b | 0.09697 | 0.07769 | 0.09529 | True | False | 10 | True | False | PASS | PASS | PASS | 不通过（d、正向门槛） | 不通过（d、正向门槛） | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | A4b_CVRv5 | 0.09187 | 0.1729 | 0.08868 | False | False | 11 | True | False | PASS | FAIL | PASS | 不通过（c、d、正向门槛、e随机） | 不通过（c、d、e随机） | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | M_mean3_v2 | 0.2983 | 0.1946 | 0.3011 | True | True | 12 | True | True | PASS | FAIL | PASS | 不通过（e随机） | 不通过（e随机） | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | M_mean3_v2_CVRv5 | 0.08031 | 0.05434 | 0.08058 | True | False | 9 | True | False | PASS | FAIL | PASS | 不通过（d、正向门槛、e随机） | 不通过（d、正向门槛、e随机） | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | M_union3_v2 | 0.06846 | 0.01413 | -0.03173 | True | False | 11 | True | False | FAIL | PASS | PASS | 不通过（d、正向门槛、e资本） | 不通过（d、正向门槛、e资本） | False | 上一轮（同构再评，只作锚） |
| Q0:NATIVE | M_union3_v2_CVRv5 | 0.07265 | 0.02854 | -0.02708 | True | False | 9 | True | False | FAIL | PASS | PASS | 不通过（d、正向门槛、e资本） | 不通过（d、正向门槛、e资本） | False | 上一轮（同构再评，只作锚） |
| Q_D3:NATIVE | A4b | 0.04293 | 0.01918 | 0.04267 | False | False | 8 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | A4b_CVRv5 | 0.05324 | 0.02187 | 0.04431 | False | False | 10 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | M_mean3_v2 | 0.1301 | 0.07186 | 0.1392 | False | False | 11 | True | True | PASS | FAIL | PASS | 不通过（c、d、e随机） | 不通过（c、d、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | M_mean3_v2_CVRv5 | -0.08898 | -0.1214 | -0.09125 | False | False | 6 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | M_union3_v2 | -0.03813 | -0.09971 | -0.1705 | False | False | 8 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D3:NATIVE | M_union3_v2_CVRv5 | 0.001458 | -0.0448 | -0.1379 | True | False | 9 | False | False | FAIL | MC_UNRESOLVED | PASS | 不通过（d、f、正向门槛、e资本） | 不通过（d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | A4b | 0.2927 | 0.2893 | 0.2942 | False | True | 13 | False | True | PASS | FAIL | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | A4b_CVRv5 | 0.3399 | 0.3318 | 0.32 | True | True | 14 | True | True | PASS | FAIL | PASS | 不通过（e随机） | 不通过（e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | M_mean3_v2 | 0.07827 | -0.03653 | 0.08788 | False | False | 10 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | M_mean3_v2_CVRv5 | -0.1567 | -0.2354 | -0.1518 | False | False | 6 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | M_union3_v2 | 0.169 | 0.1585 | -0.07145 | True | False | 11 | True | True | FAIL | PASS | PASS | 不通过（d、e资本） | 不通过（d、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:HG10 | M_union3_v2_CVRv5 | 0.214 | 0.2216 | -0.02791 | True | True | 13 | True | True | FAIL | PASS | PASS | 不通过（e资本） | 不通过（e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | A4b | 0.08507 | 0.0008498 | 0.0873 | False | False | 10 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | A4b_CVRv5 | 0.09451 | 0.01402 | 0.09106 | False | False | 10 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | M_mean3_v2 | 0.1314 | 0.04927 | 0.1372 | False | False | 9 | True | True | PASS | FAIL | PASS | 不通过（c、d、e随机） | 不通过（c、d、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | M_mean3_v2_CVRv5 | -0.05983 | -0.1096 | -0.06432 | False | False | 6 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | M_union3_v2 | 0.02854 | 0.0615 | -0.1409 | True | False | 8 | False | False | FAIL | PASS | PASS | 不通过（d、f、正向门槛、e资本） | 不通过（d、f、正向门槛、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_D5:NATIVE | M_union3_v2_CVRv5 | 0.04741 | 0.07228 | -0.1227 | True | False | 9 | True | False | FAIL | PASS | PASS | 不通过（d、正向门槛、e资本） | 不通过（d、正向门槛、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | A4b | 0.2937 | 0.3123 | 0.2993 | False | True | 12 | False | True | PASS | FAIL | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | A4b_CVRv5 | 0.272 | 0.2971 | 0.2567 | False | True | 14 | False | True | PASS | FAIL | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | M_mean3_v2 | 0.1097 | 0.009437 | 0.1176 | False | False | 11 | True | True | PASS | FAIL | PASS | 不通过（c、d、e随机） | 不通过（c、d、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | M_mean3_v2_CVRv5 | -0.1355 | -0.1983 | -0.1357 | False | False | 7 | True | False | PASS | FAIL | PASS | 不通过（c、d、正向门槛、e随机） | 不通过（c、d、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | M_union3_v2 | 0.1878 | 0.1513 | -0.06016 | True | False | 11 | True | True | FAIL | PASS | PASS | 不通过（d、e资本） | 不通过（d、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:HG10 | M_union3_v2_CVRv5 | 0.1998 | 0.225 | -0.05081 | True | True | 12 | True | True | FAIL | PASS | PASS | 不通过（e资本） | 不通过（e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | A4b | 0.04471 | 0.05897 | 0.04779 | False | False | 9 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | A4b_CVRv5 | 0.0554 | 0.03705 | 0.05114 | False | False | 8 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | M_mean3_v2 | 0.1679 | 0.09981 | 0.177 | True | False | 11 | True | True | PASS | MC_UNRESOLVED | PASS | 不通过（d） | 不通过（d、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | M_mean3_v2_CVRv5 | -0.07682 | -0.1099 | -0.0819 | False | False | 5 | False | False | PASS | FAIL | PASS | 不通过（c、d、f、正向门槛、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | M_union3_v2 | 0.02323 | 0.0008249 | -0.1504 | False | False | 10 | False | False | FAIL | PASS | PASS | 不通过（c、d、f、正向门槛、e资本） | 不通过（c、d、f、正向门槛、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_DEW5:NATIVE | M_union3_v2_CVRv5 | 0.04861 | 0.04036 | -0.1304 | True | False | 9 | False | False | FAIL | PASS | PASS | 不通过（d、f、正向门槛、e资本） | 不通过（d、f、正向门槛、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | A4b | 0.199 | 0.2286 | 0.204 | False | True | 13 | False | True | PASS | FAIL | PASS | 不通过（c、f、e随机） | 不通过（c、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | A4b_CVRv5 | 0.2375 | 0.256 | 0.2351 | True | True | 15 | True | True | PASS | FAIL | PASS | 不通过（e随机） | 不通过（e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | M_mean3_v2 | 0.1564 | 0.04485 | 0.1616 | True | True | 12 | True | True | PASS | PASS | PASS | 通过 | 不通过（正向门槛） | True | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | M_mean3_v2_CVRv5 | -0.03381 | -0.03659 | -0.03316 | False | False | 9 | True | False | PASS | PASS | PASS | 不通过（c、d、正向门槛） | 不通过（c、d、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | M_union3_v2 | 0.1596 | 0.1642 | -0.0186 | True | True | 12 | True | True | FAIL | PASS | PASS | 不通过（e资本） | 通过 | True | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:HG10 | M_union3_v2_CVRv5 | 0.1853 | 0.1996 | 0.01197 | True | True | 12 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | A4b | 0.1596 | 0.1058 | 0.1552 | False | False | 10 | False | True | PASS | FAIL | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | A4b_CVRv5 | 0.1572 | 0.08416 | 0.1563 | False | False | 11 | False | True | PASS | FAIL | PASS | 不通过（c、d、f、e随机） | 不通过（c、d、f、正向门槛、e随机） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | M_mean3_v2 | 0.2212 | 0.1595 | 0.2251 | True | True | 12 | True | True | PASS | PASS | PASS | 通过 | 通过 | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | M_mean3_v2_CVRv5 | 0.07726 | 0.04616 | 0.07269 | False | False | 9 | True | False | PASS | PASS | PASS | 不通过（c、d、正向门槛） | 不通过（c、d、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | M_union3_v2 | -0.03379 | 0.00576 | -0.1258 | False | True | 12 | False | False | PASS | PASS | PASS | 不通过（c、f、正向门槛） | 不通过（c、f、正向门槛、e资本） | False | 本轮新证据（首评，重复使用的历史） |
| Q_RANK5:NATIVE | M_union3_v2_CVRv5 | -0.0376 | -0.01712 | -0.1264 | False | False | 11 | False | False | PASS | PASS | PASS | 不通过（c、d、f、正向门槛） | 不通过（c、d、f、正向门槛） | False | 本轮新证据（首评，重复使用的历史） |


## 3. 生产变更候选清单（PORT3_T FULL 或 G4 通过；分"上一轮 / 本轮新证据"两栏；deployment_authorized = false）

> 表头：主体=正式尺子通过的全部对象（2864）｜算子=全部｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父（8bp）｜子集=PORT3_T 通过｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=H 见 desc_id｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-P3-CANDIDATES


| evidence_column | desc_id | family | FULL_ann_pp | G4_ann_pp | FULL_sc_ann_pp | policy_PROPOSED_PORT3_T_FULL | policy_PROPOSED_PORT3_T_G4 | e_rand | years_pos | replacement_status | deployment_authorized |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.5\|H1\|NATIVE | NATIVE | 3.159 | 2.927 | 3.178 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.5\|H1\|NATIVE | NATIVE | 3.133 | 3.056 | 3.129 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.5\|H1\|NATIVE | NATIVE | 2.454 | 2.4 | 2.313 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.5\|H1\|NATIVE | NATIVE | 2.294 | 2.034 | 2.169 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2\|a0.5\|H1\|NATIVE | NATIVE | 2.152 | 2.16 | 2.107 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b\|a0.5\|H1\|NATIVE | NATIVE | 2.072 | 1.992 | 2.059 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.5\|H1\|NATIVE | NATIVE | 2.052 | 1.781 | 2.06 | 通过 | 通过 | PASS | 17 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H1\|HG15 | HG | 2.038 | 2.156 | 1.942 | 通过 | 通过 | PASS | 17 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2\|a0.5\|H1\|NATIVE | NATIVE | 1.85 | 1.645 | 0.9334 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2\|a0.5\|H1\|NATIVE | NATIVE | 1.823 | 1.779 | 1.838 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H1\|HG10 | HG | 1.81 | 1.799 | 1.751 | 通过 | 通过 | PASS | 17 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H1\|HG5 | HG | 1.774 | 1.628 | 1.713 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.769 | 1.986 | 1.578 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.5\|H2\|NATIVE | NATIVE | 1.75 | 1.455 | 1.748 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.5\|H1\|NATIVE | NATIVE | 1.728 | 1.22 | 0.9202 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.5\|H1\|NATIVE | NATIVE | 1.723 | 1.469 | 0.7168 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.5\|H2\|NATIVE | NATIVE | 1.702 | 1.414 | 1.708 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2_CVRv5\|a0.5\|H1\|NATIVE | NATIVE | 1.624 | 1.624 | 1.58 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.25\|H1\|NATIVE | NATIVE | 1.605 | 1.482 | 1.6 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H1\|HG10 | HG | 1.515 | 1.648 | 1.452 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2\|a0.25\|H1\|NATIVE | NATIVE | 1.501 | 1.599 | 1.491 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.5\|H1\|NATIVE | NATIVE | 1.463 | 1.108 | 1.422 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|NATIVE | NATIVE | 1.451 | 0.9143 | 0.6223 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 1.44 | 1.49 | 1.196 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.5\|H1\|NATIVE | NATIVE | 1.428 | 1.426 | 1.408 | 通过 | 通过 | PASS | 17 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H1\|HG15 | HG | 1.405 | 1.576 | 1.334 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H1\|NATIVE | NATIVE | 1.331 | 1.114 | 1.27 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.25\|H1\|HG10 | HG | 1.295 | 1.406 | 1.28 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.269 | 1.38 | 1.076 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H1\|HG15 | HG | 1.228 | 1.368 | 1.187 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.5\|H1\|NATIVE | NATIVE | 1.22 | 1.465 | 1.185 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.25\|H1\|NATIVE | NATIVE | 1.209 | 1.062 | 1.21 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2\|a0.25\|H1\|NATIVE | NATIVE | 1.199 | 1.227 | 1.177 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H1\|HG15 | HG | 1.19 | 1.305 | 1.148 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H1\|HG5 | HG | 1.185 | 1.125 | 1.15 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.5\|H2\|NATIVE | NATIVE | 1.162 | 0.9885 | 1.034 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.5\|H1\|NATIVE | NATIVE | 1.122 | 1.123 | 1.096 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.25\|H1\|NATIVE | NATIVE | 1.088 | 1.055 | 1.048 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2_CVRv5\|a0.5\|H1\|NATIVE | NATIVE | 1.084 | 1.026 | 1.034 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H1\|HG10 | HG | 1.069 | 1.116 | 1.035 | 通过 | 通过 | PASS | 17 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H1\|HG15 | HG | 1.058 | 1.133 | 1.056 | 通过 | 通过 | PASS | 17 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.058 | 1.076 | 0.9275 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.055 | 1.159 | 1.03 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H1\|HG10 | HG | 1.04 | 1.219 | 1.005 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.5\|H2\|NATIVE | NATIVE | 1.037 | 0.7897 | 0.1682 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2_CVRv5\|a0.5\|H1\|NATIVE | NATIVE | 1.015 | 0.8086 | 0.9635 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|HG5 | HG | 1.008 | 1.099 | 0.8563 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H1\|HG10 | HG | 0.9896 | 1.043 | 0.9642 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H1\|HG5 | HG | 0.9595 | 1.03 | 0.9444 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.5\|H3\|NATIVE | NATIVE | 0.9543 | 0.7261 | 0.1331 | 通过 | 不通过（e资本） | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.5\|H2\|HG10 | HG | 0.9526 | 1.247 | 0.7975 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2\|a0.5\|H2\|NATIVE | NATIVE | 0.951 | 0.7286 | 0.1952 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.125\|H1\|HG10 | HG | 0.9394 | 1.075 | 0.9191 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.125\|H1\|NATIVE | NATIVE | 0.9368 | 0.806 | 0.9376 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2_CVRv5\|a0.25\|H1\|NATIVE | NATIVE | 0.9165 | 1.106 | 0.8834 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H1\|NATIVE | NATIVE | 0.9146 | 0.5812 | 0.9179 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|NATIVE | NATIVE | 0.9116 | 0.9214 | 0.8844 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 0.9116 | 0.9463 | 0.8826 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.8994 | 0.8611 | 0.872 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2\|a0.125\|H1\|NATIVE | NATIVE | 0.8944 | 0.9147 | 0.8949 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H1\|NATIVE | NATIVE | 0.8904 | 0.611 | 0.8585 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG15 | HG | 0.884 | 0.9038 | 0.8685 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H2\|HG15 | HG | 0.8805 | 0.9367 | 0.8324 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.8676 | 1.03 | 0.6987 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.8511 | 0.8169 | 0.7326 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG5 | HG | 0.8431 | 0.9279 | 0.8089 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.5\|H2\|NATIVE | NATIVE | 0.8408 | 0.8337 | 0.8038 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|NATIVE | NATIVE | 0.8362 | 0.88 | 0.7961 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.5\|H5\|NATIVE | NATIVE | 0.8344 | 0.9044 | 0.1044 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.25\|H2\|NATIVE | NATIVE | 0.8343 | 0.7253 | 0.8511 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2_CVRv5\|a0.25\|H1\|NATIVE | NATIVE | 0.818 | 0.8758 | 0.8056 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 0.803 | 0.9627 | 0.7642 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.125\|H1\|HG15 | HG | 0.803 | 0.802 | 0.712 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2\|a0.25\|H1\|NATIVE | NATIVE | 0.8012 | 0.9359 | 0.534 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.5\|H2\|NATIVE | NATIVE | 0.777 | 0.9319 | 0.7294 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.25\|H1\|NATIVE | NATIVE | 0.769 | 0.8522 | 0.5134 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.5\|H10\|HG10 | HG | 0.7667 | 0.7916 | 0.6565 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H1\|NATIVE | NATIVE | 0.7643 | 0.7653 | 0.7667 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|NATIVE | NATIVE | 0.7548 | 0.7842 | 0.6296 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H1\|NATIVE | NATIVE | 0.7514 | 0.7854 | 0.7323 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2\|a0.5\|H1\|NATIVE | NATIVE | 0.7509 | 0.7245 | 0.6181 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.5\|H10\|NATIVE | NATIVE | 0.7452 | 0.8646 | 0.1304 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H3\|HG10 | HG | 0.7361 | 0.7836 | 0.7444 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.5\|H10\|NATIVE | NATIVE | 0.7255 | 0.4944 | 0.713 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H2\|HG10 | HG | 0.7225 | 0.8336 | 0.6886 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2\|a0.5\|H10\|NATIVE | NATIVE | 0.7176 | 0.8717 | 0.1507 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.25\|H1\|NATIVE | NATIVE | 0.7075 | 0.8201 | 0.3986 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.5\|H2\|NATIVE | NATIVE | 0.6931 | 0.5303 | 0.6653 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.5\|H5\|NATIVE | NATIVE | 0.6923 | 0.5115 | 0.6448 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.25\|H3\|NATIVE | NATIVE | 0.689 | 0.6097 | 0.6985 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.25\|H1\|NATIVE | NATIVE | 0.6847 | 0.5867 | 0.5525 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.25\|H2\|NATIVE | NATIVE | 0.6796 | 0.5875 | 0.658 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.5\|H10\|NATIVE | NATIVE | 0.6755 | 0.5146 | 0.6065 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H1\|HG5 | HG | 0.6707 | 0.5776 | 0.6487 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|NATIVE | NATIVE | 0.6678 | 0.7037 | 0.3914 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.25\|H2\|NATIVE | NATIVE | 0.6665 | 0.6621 | 0.6642 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H1\|HG5 | HG | 0.6578 | 0.5309 | 0.6228 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2\|a0.25\|H2\|NATIVE | NATIVE | 0.6526 | 0.6722 | 0.6428 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H2\|HG10 | HG | 0.6403 | 0.6632 | 0.6167 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.25\|H1\|NATIVE | NATIVE | 0.6399 | 0.649 | 0.6205 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.5\|H10\|NATIVE | NATIVE | 0.6382 | 0.5882 | 0.5692 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H3\|HG5 | HG | 0.6344 | 0.4641 | 0.6446 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b_CVRv5\|a0.25\|H1\|NATIVE | NATIVE | 0.6343 | 0.4605 | 0.6316 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H3\|HG15 | HG | 0.6281 | 0.7078 | 0.628 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.5\|H2\|HG15 | HG | 0.6196 | 0.7415 | 0.4506 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 0.6176 | 0.5876 | 0.6016 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.25\|H1\|NATIVE | NATIVE | 0.6143 | 0.6428 | 0.4768 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 0.6026 | 0.6437 | 0.5221 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H3\|HG10 | HG | 0.5974 | 0.6309 | 0.5739 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.25\|H3\|HG10 | HG | 0.5891 | 0.5958 | 0.6031 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H2\|NATIVE | NATIVE | 0.586 | 0.5167 | 0.5447 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.5823 | 0.5363 | 0.5213 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2_CVRv5\|a0.125\|H1\|NATIVE | NATIVE | 0.5775 | 0.6292 | 0.5656 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2_CVRv5\|a0.25\|H3\|HG10 | HG | 0.5633 | 0.5513 | 0.2163 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.25\|H3\|HG10 | HG | 0.5623 | 0.5449 | 0.2325 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.25\|H3\|NATIVE | NATIVE | 0.553 | 0.5741 | 0.5324 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.5\|H20\|NATIVE | NATIVE | 0.5507 | 0.4207 | 0.5521 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H2\|HG5 | HG | 0.5498 | 0.4495 | 0.5374 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H2\|HG10 | HG | 0.5454 | 0.6241 | 0.5154 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H3\|HG15 | HG | 0.5415 | 0.5262 | 0.5038 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H5\|HG10 | HG | 0.5383 | 0.5542 | 0.4994 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H3\|NATIVE | NATIVE | 0.5366 | 0.3474 | 0.5466 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|HG10 | HG | 0.5357 | 0.6555 | 0.2051 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.25\|H5\|HG10 | HG | 0.5354 | 0.6264 | 0.2134 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2\|a0.25\|H3\|NATIVE | NATIVE | 0.5349 | 0.5263 | 0.5274 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2\|a0.25\|H2\|NATIVE | NATIVE | 0.5339 | 0.5604 | 0.2566 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H5\|HG10 | HG | 0.5279 | 0.4851 | 0.5331 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.5\|H20\|HG10 | HG | 0.5275 | 0.5089 | 0.4729 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.25\|H3\|NATIVE | NATIVE | 0.5274 | 0.3267 | 0.5307 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.5\|H20\|NATIVE | NATIVE | 0.525 | 0.5743 | 0.07428 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b\|a0.25\|H3\|HG10 | HG | 0.5247 | 0.4193 | 0.5354 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H5\|HG10 | HG | 0.5176 | 0.5256 | 0.4858 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H5\|HG15 | HG | 0.5155 | 0.5343 | 0.472 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.25\|H2\|HG10 | HG | 0.5135 | 0.6834 | 0.3506 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2_CVRv5\|a0.5\|H20\|NATIVE | NATIVE | 0.5087 | 0.5028 | 0.5083 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.25\|H2\|NATIVE | NATIVE | 0.5053 | 0.4364 | 0.3438 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.25\|H2\|NATIVE | NATIVE | 0.5045 | 0.5461 | 0.1931 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H3\|HG5 | HG | 0.5024 | 0.4991 | 0.4791 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.5\|H2\|HG10 | HG | 0.5023 | 0.6417 | 0.3735 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2\|a0.25\|H3\|HG10 | HG | 0.5004 | 0.4971 | 0.4937 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.125\|H2\|NATIVE | NATIVE | 0.4964 | 0.4108 | 0.4964 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H5\|HG5 | HG | 0.496 | 0.4157 | 0.5037 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H5\|HG5 | HG | 0.4953 | 0.4497 | 0.4671 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.5\|H20\|NATIVE | NATIVE | 0.4912 | 0.3874 | 0.4686 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H2\|NATIVE | NATIVE | 0.491 | 0.3837 | 0.4836 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2\|a0.5\|H20\|NATIVE | NATIVE | 0.4907 | 0.5641 | 0.09349 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H2\|HG15 | HG | 0.4866 | 0.4962 | 0.4528 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2\|a0.25\|H3\|HG10 | HG | 0.4837 | 0.416 | 0.1326 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H10\|HG15 | HG | 0.4808 | 0.5822 | 0.4749 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2_CVRv5\|a0.25\|H3\|HG15 | HG | 0.478 | 0.3053 | 0.09163 | 通过 | 不通过（e资本） | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2\|a0.25\|H10\|HG10 | HG | 0.4774 | 0.4047 | 0.4734 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.25\|H3\|HG10 | HG | 0.4762 | 0.3969 | 0.1016 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.25\|H2\|NATIVE | NATIVE | 0.4758 | 0.4678 | 0.3127 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.5\|H10\|NATIVE | NATIVE | 0.4742 | 0.5273 | 0.4401 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.25\|H3\|HG10 | HG | 0.473 | 0.5941 | 0.4718 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2\|a0.125\|H2\|NATIVE | NATIVE | 0.4714 | 0.5231 | 0.4736 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H5\|HG15 | HG | 0.4689 | 0.4349 | 0.4656 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H2\|HG5 | HG | 0.4688 | 0.4335 | 0.4545 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H2\|HG10 | HG | 0.4688 | 0.5167 | 0.4582 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.5\|H10\|NATIVE | NATIVE | 0.4677 | 0.4555 | 0.3893 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.5\|H20\|NATIVE | NATIVE | 0.4617 | 0.3734 | 0.393 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|HG15 | HG | 0.4539 | 0.5401 | 0.09537 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H2\|HG15 | HG | 0.4518 | 0.3675 | 0.4292 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H5\|HG5 | HG | 0.4488 | 0.4904 | 0.414 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b_CVRv5\|a0.25\|H3\|HG10 | HG | 0.4463 | 0.3777 | 0.4677 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H10\|HG10 | HG | 0.446 | 0.5469 | 0.4284 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.25\|H10\|HG10 | HG | 0.4445 | 0.4662 | 0.2887 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H10\|HG10 | HG | 0.4434 | 0.4887 | 0.4487 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.25\|H5\|HG15 | HG | 0.443 | 0.504 | 0.09716 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H3\|HG15 | HG | 0.4427 | 0.4583 | 0.4136 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.125\|H2\|HG10 | HG | 0.4421 | 0.4015 | 0.4314 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2\|a0.25\|H3\|NATIVE | NATIVE | 0.4407 | 0.3411 | 0.441 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b\|a0.25\|H2\|NATIVE | NATIVE | 0.44 | 0.309 | 0.4443 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.25\|H5\|HG10 | HG | 0.44 | 0.49 | 0.09191 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2\|a0.125\|H3\|NATIVE | NATIVE | 0.4398 | 0.314 | 0.4435 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.5\|H20\|NATIVE | NATIVE | 0.4391 | 0.3918 | 0.409 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2\|a0.25\|H10\|NATIVE | NATIVE | 0.4368 | 0.4388 | 0.4351 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2\|a0.25\|H5\|NATIVE | NATIVE | 0.4361 | 0.4186 | 0.4293 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.25\|H3\|HG15 | HG | 0.436 | 0.2384 | 0.08287 | 通过 | 不通过（e资本） | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.25\|H10\|HG10 | HG | 0.4353 | 0.4746 | 0.2854 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.5\|H2\|NATIVE | NATIVE | 0.4339 | 0.2997 | 0.4239 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.125\|H3\|NATIVE | NATIVE | 0.4332 | 0.3222 | 0.4341 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2\|a0.25\|H5\|HG10 | HG | 0.4324 | 0.4134 | 0.09695 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.25\|H10\|HG10 | HG | 0.4315 | 0.432 | 0.1748 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2\|a0.25\|H20\|HG10 | HG | 0.4288 | 0.4096 | 0.4237 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H2\|HG15 | HG | 0.4277 | 0.5064 | 0.4206 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H10\|HG10 | HG | 0.4274 | 0.4468 | 0.4051 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|HG5 | HG | 0.4268 | 0.5501 | 0.1137 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H10\|HG15 | HG | 0.4256 | 0.4564 | 0.4013 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.5\|H20\|NATIVE | NATIVE | 0.4254 | 0.4027 | 0.349 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | 0.4244 | 0.3578 | 0.4003 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H10\|NATIVE | NATIVE | 0.4206 | 0.3958 | 0.4056 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2\|a0.25\|H10\|HG10 | HG | 0.42 | 0.4856 | 0.1479 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H2\|NATIVE | NATIVE | 0.4195 | 0.3576 | 0.3965 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.25\|H5\|HG10 | HG | 0.4176 | 0.4411 | 0.4005 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.125\|H1\|NATIVE | NATIVE | 0.4162 | 0.2246 | 0.4262 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.25\|H1\|NATIVE | NATIVE | 0.4157 | 0.4664 | 0.3866 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H3\|NATIVE | NATIVE | 0.4154 | 0.3805 | 0.4061 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.25\|H5\|HG10 | HG | 0.4139 | 0.3352 | 0.4235 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.25\|H10\|HG15 | HG | 0.4113 | 0.4443 | 0.1233 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H5\|HG15 | HG | 0.409 | 0.3693 | 0.3799 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.25\|H5\|HG5 | HG | 0.4023 | 0.5357 | 0.1065 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H2\|HG5 | HG | 0.4015 | 0.2621 | 0.3827 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.25\|H5\|NATIVE | NATIVE | 0.3997 | 0.3777 | 0.4052 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.25\|H10\|NATIVE | NATIVE | 0.3992 | 0.4142 | 0.2876 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H3\|HG5 | HG | 0.3984 | 0.4401 | 0.3983 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.25\|H5\|NATIVE | NATIVE | 0.398 | 0.2775 | 0.2507 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.5\|H2\|HG5 | HG | 0.397 | 0.5504 | 0.2994 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.25\|H10\|HG10 | HG | 0.3957 | 0.4452 | 0.105 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H10\|HG5 | HG | 0.3946 | 0.4029 | 0.377 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H2\|NATIVE | NATIVE | 0.391 | 0.3517 | 0.3868 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.25\|H3\|NATIVE | NATIVE | 0.3903 | 0.3504 | 0.2407 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2\|a0.25\|H1\|NATIVE | NATIVE | 0.3884 | 0.3791 | 0.3526 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.5\|H20\|NATIVE | NATIVE | 0.3839 | 0.3684 | 0.397 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H10\|HG15 | HG | 0.3834 | 0.4342 | 0.3583 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2_CVRv5\|a0.25\|H2\|NATIVE | NATIVE | 0.3808 | 0.3447 | 0.3714 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.25\|H10\|HG10 | HG | 0.3798 | 0.257 | 0.3851 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | 0.3768 | 0.3079 | 0.2397 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H10\|HG5 | HG | 0.376 | 0.4033 | 0.384 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2_CVRv5\|a0.125\|H1\|NATIVE | NATIVE | 0.3742 | 0.3743 | 0.37 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.25\|H10\|NATIVE | NATIVE | 0.3737 | 0.2139 | 0.3721 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.125\|H1\|NATIVE | NATIVE | 0.3737 | 0.4107 | 0.2657 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b_CVRv5\|a0.25\|H5\|HG10 | HG | 0.371 | 0.3839 | 0.3812 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H3\|HG10 | HG | 0.3706 | 0.41 | 0.3485 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H20\|HG15 | HG | 0.3692 | 0.341 | 0.3663 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.25\|H10\|NATIVE | NATIVE | 0.3691 | 0.4281 | 0.2541 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.3669 | 0.3361 | 0.3364 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H3\|HG10 | HG | 0.3658 | 0.2446 | 0.3592 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H3\|HG15 | HG | 0.3638 | 0.3738 | 0.3495 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | 0.3638 | 0.2874 | 0.346 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H10\|HG5 | HG | 0.3637 | 0.4047 | 0.3505 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H5\|NATIVE | NATIVE | 0.3631 | 0.2695 | 0.3678 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.25\|H3\|NATIVE | NATIVE | 0.3622 | 0.3292 | 0.06546 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H2\|HG10 | HG | 0.3596 | 0.2703 | 0.3438 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b\|a0.25\|H3\|NATIVE | NATIVE | 0.3591 | 0.2313 | 0.3646 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.25\|H3\|NATIVE | NATIVE | 0.3587 | 0.2941 | 0.2166 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2_CVRv5\|a0.25\|H2\|NATIVE | NATIVE | 0.3573 | 0.4678 | 0.109 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H2\|HG15 | HG | 0.3572 | 0.3994 | 0.3389 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H3\|NATIVE | NATIVE | 0.3568 | 0.3408 | 0.3376 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2\|a0.25\|H3\|NATIVE | NATIVE | 0.3545 | 0.3278 | 0.08385 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H3\|NATIVE | NATIVE | 0.353 | 0.3333 | 0.3498 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2_CVRv5\|a0.25\|H20\|HG10 | HG | 0.3524 | 0.3416 | 0.3484 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | 0.3487 | 0.3481 | 0.08027 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b\|a0.25\|H5\|HG10 | HG | 0.3479 | 0.2125 | 0.3579 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.25\|H5\|HG10 | HG | 0.3473 | 0.4264 | 0.1688 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.5\|H5\|NATIVE | NATIVE | 0.3466 | 0.207 | 0.3474 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.25\|H10\|HG10 | HG | 0.3457 | 0.4036 | 0.3567 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H3\|HG5 | HG | 0.3431 | 0.3274 | 0.328 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2_CVRv5\|a0.25\|H10\|HG10 | HG | 0.3406 | 0.3245 | 0.3408 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | 0.34 | 0.2745 | 0.3456 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2\|a0.25\|H10\|NATIVE | NATIVE | 0.3395 | 0.219 | 0.3423 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b\|a0.25\|H5\|NATIVE | NATIVE | 0.3386 | 0.2736 | 0.3462 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2\|a0.125\|H5\|NATIVE | NATIVE | 0.3385 | 0.1933 | 0.3417 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2\|a0.25\|H20\|NATIVE | NATIVE | 0.3368 | 0.3451 | 0.3327 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.125\|H5\|HG10 | HG | 0.3365 | 0.3608 | 0.3266 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H3\|HG10 | HG | 0.3359 | 0.3858 | 0.3286 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.5\|H20\|NATIVE | NATIVE | 0.3358 | 0.3565 | 0.3152 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H3\|HG15 | HG | 0.3352 | 0.271 | 0.3156 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.125\|H3\|HG10 | HG | 0.3338 | 0.3471 | 0.3228 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H20\|HG15 | HG | 0.3327 | 0.2991 | 0.3051 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.25\|H20\|HG10 | HG | 0.3322 | 0.3079 | 0.2259 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H20\|HG10 | HG | 0.3314 | 0.3102 | 0.3153 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H10\|HG15 | HG | 0.331 | 0.3308 | 0.3166 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2\|a0.25\|H20\|HG10 | HG | 0.3299 | 0.3707 | 0.1218 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.25\|H10\|HG10 | HG | 0.3268 | 0.3486 | 0.3133 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.25\|H20\|HG10 | HG | 0.3236 | 0.3285 | 0.2087 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H20\|HG10 | HG | 0.3228 | 0.2871 | 0.3013 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H5\|HG10 | HG | 0.3183 | 0.29 | 0.3108 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H20\|HG10 | HG | 0.3175 | 0.2799 | 0.3115 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H20\|HG15 | HG | 0.3174 | 0.2774 | 0.3059 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2_CVRv5\|a0.25\|H10\|NATIVE | NATIVE | 0.3126 | 0.2598 | 0.3188 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.25\|H5\|HG10 | HG | 0.3104 | 0.3448 | 0.1293 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.25\|H20\|HG10 | HG | 0.3085 | 0.3426 | 0.08229 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.25\|H20\|HG10 | HG | 0.3073 | 0.2706 | 0.2916 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H3\|HG5 | HG | 0.3061 | 0.2778 | 0.2967 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H5\|HG15 | HG | 0.3046 | 0.267 | 0.2837 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H1\|NATIVE | NATIVE | 0.3042 | 0.3107 | 0.2693 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|NATIVE | NATIVE | 0.3041 | 0.3676 | 0.1902 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H10\|HG10 | HG | 0.3039 | 0.3333 | 0.2984 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.25\|H3\|HG10 | HG | 0.3036 | 0.3507 | 0.1356 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H20\|HG10 | HG | 0.3028 | 0.268 | 0.3077 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b_CVRv5\|a0.25\|H10\|NATIVE | NATIVE | 0.3027 | 0.3362 | 0.31 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.25\|H10\|HG15 | HG | 0.302 | 0.2522 | 0.2951 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.5\|H2\|NATIVE | NATIVE | 0.3009 | 0.4144 | 0.2385 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.25\|H10\|HG5 | HG | 0.3007 | 0.2952 | 0.06939 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2\|a0.25\|H10\|HG15 | HG | 0.2995 | 0.2021 | 0.193 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.25\|H20\|HG10 | HG | 0.2992 | 0.2758 | 0.3067 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H20\|HG5 | HG | 0.2988 | 0.2684 | 0.2828 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H20\|HG5 | HG | 0.2976 | 0.3035 | 0.281 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H20\|HG15 | HG | 0.2967 | 0.2591 | 0.2781 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H10\|HG15 | HG | 0.2954 | 0.2878 | 0.2891 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2\|a0.125\|H10\|NATIVE | NATIVE | 0.2952 | 0.2908 | 0.2919 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H5\|HG5 | HG | 0.2935 | 0.3555 | 0.2952 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H20\|HG10 | HG | 0.2921 | 0.2355 | 0.2787 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b\|a0.25\|H10\|NATIVE | NATIVE | 0.2904 | 0.2214 | 0.2972 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b_CVRv5\|a0.25\|H3\|NATIVE | NATIVE | 0.2893 | 0.2219 | 0.3018 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.5\|H10\|NATIVE | NATIVE | 0.288 | 0.2052 | 0.2828 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | 0.2863 | 0.3224 | 0.2728 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H20\|HG5 | HG | 0.2858 | 0.2651 | 0.2892 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.5\|H20\|NATIVE | NATIVE | 0.2857 | 0.2776 | 0.2734 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b_CVRv5\|a0.25\|H20\|HG10 | HG | 0.2844 | 0.2692 | 0.2849 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H10\|NATIVE | NATIVE | 0.2827 | 0.2889 | 0.2842 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H10\|HG10 | HG | 0.2791 | 0.3346 | 0.2745 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H5\|HG5 | HG | 0.2781 | 0.3306 | 0.2612 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.25\|H20\|NATIVE | NATIVE | 0.2742 | 0.2286 | 0.2025 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H20\|HG15 | HG | 0.2739 | 0.2237 | 0.2632 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.125\|H10\|NATIVE | NATIVE | 0.2726 | 0.1864 | 0.2722 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H5\|HG10 | HG | 0.2722 | 0.2814 | 0.2571 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H10\|NATIVE | NATIVE | 0.2714 | 0.3314 | 0.2618 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2_CVRv5\|a0.25\|H10\|HG5 | HG | 0.2692 | 0.2628 | 0.02534 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.25\|H20\|HG10 | HG | 0.269 | 0.2948 | 0.08229 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b\|a0.25\|H20\|HG10 | HG | 0.2679 | 0.268 | 0.2744 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H10\|HG5 | HG | 0.2672 | 0.2687 | 0.2641 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.25\|H10\|HG10 | HG | 0.2672 | 0.1952 | 0.2637 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.25\|H10\|NATIVE | NATIVE | 0.2671 | 0.2681 | 0.2703 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H20\|HG5 | HG | 0.2658 | 0.2072 | 0.2624 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H5\|NATIVE | NATIVE | 0.2648 | 0.311 | 0.2649 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H10\|NATIVE | NATIVE | 0.2646 | 0.2589 | 0.262 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.25\|H20\|NATIVE | NATIVE | 0.2636 | 0.2134 | 0.2634 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H10\|NATIVE | NATIVE | 0.2616 | 0.2391 | 0.2582 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b_CVRv5\|a0.25\|H20\|NATIVE | NATIVE | 0.2593 | 0.2545 | 0.2621 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2_CVRv5\|a0.25\|H20\|NATIVE | NATIVE | 0.2593 | 0.27 | 0.2615 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2\|a0.25\|H10\|NATIVE | NATIVE | 0.2575 | 0.3401 | 0.05065 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H10\|HG5 | HG | 0.2567 | 0.2308 | 0.2482 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b_CVRv5\|a0.25\|H10\|HG10 | HG | 0.2557 | 0.2757 | 0.2682 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H20\|HG15 | HG | 0.2546 | 0.2405 | 0.2424 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H10\|HG15 | HG | 0.2535 | 0.1389 | 0.1467 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.25\|H20\|HG15 | HG | 0.2532 | 0.1928 | 0.2586 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.25\|H10\|NATIVE | NATIVE | 0.2526 | 0.2806 | 0.2413 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.25\|H20\|NATIVE | NATIVE | 0.2522 | 0.2128 | 0.2506 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | 0.251 | 0.3142 | 0.01981 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.25\|H10\|NATIVE | NATIVE | 0.2505 | 0.3257 | 0.02899 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.25\|H20\|HG5 | HG | 0.2489 | 0.2171 | 0.2464 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2\|a0.125\|H10\|NATIVE | NATIVE | 0.2485 | 0.1643 | 0.2492 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.25\|H20\|NATIVE | NATIVE | 0.2479 | 0.2447 | 0.2393 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b\|a0.25\|H20\|NATIVE | NATIVE | 0.2438 | 0.2533 | 0.2486 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H20\|HG5 | HG | 0.242 | 0.1688 | 0.2287 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.25\|H20\|NATIVE | NATIVE | 0.2408 | 0.2336 | 0.1617 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b\|a0.25\|H10\|HG10 | HG | 0.2406 | 0.2247 | 0.2506 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2\|a0.25\|H20\|NATIVE | NATIVE | 0.2402 | 0.1861 | 0.2412 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.25\|H20\|NATIVE | NATIVE | 0.2393 | 0.2214 | 0.2297 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2\|a0.25\|H10\|HG10 | HG | 0.234 | 0.201 | 0.139 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H20\|NATIVE | NATIVE | 0.2331 | 0.1808 | 0.229 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.25\|H20\|NATIVE | NATIVE | 0.2309 | 0.2337 | 0.2378 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.25\|H10\|HG5 | HG | 0.2282 | 0.1554 | 0.2239 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.25\|H20\|NATIVE | NATIVE | 0.2198 | 0.2081 | 0.2235 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.5\|H10\|HG5 | HG | 0.2183 | 0.1995 | 0.2133 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.5\|H10\|HG15 | HG | 0.2172 | 0.2202 | 0.09072 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.125\|H3\|NATIVE | NATIVE | 0.2128 | 0.1715 | 0.2166 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2\|a0.125\|H20\|NATIVE | NATIVE | 0.2106 | 0.1924 | 0.2075 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.5\|H5\|HG5 | HG | 0.2085 | 0.251 | 0.1148 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H3\|HG15 | HG | 0.2056 | 0.2058 | 0.07655 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2\|a0.25\|H10\|HG5 | HG | 0.205 | 0.146 | 0.1239 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.5\|H10\|NATIVE | NATIVE | 0.2047 | 0.1726 | 0.2007 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.25\|H20\|HG5 | HG | 0.2032 | 0.2101 | 0.02859 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.5\|H20\|NATIVE | NATIVE | 0.203 | 0.1988 | 0.1965 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.25\|H5\|NATIVE | NATIVE | 0.2006 | 0.1498 | 0.1946 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.5\|H5\|NATIVE | NATIVE | 0.1997 | 0.1388 | 0.1931 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H5\|HG5 | HG | 0.1991 | 0.2085 | 0.1951 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1983 | 0.1808 | 0.1886 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.25\|H5\|HG15 | HG | 0.198 | 0.2059 | 0.1815 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2\|a0.25\|H20\|NATIVE | NATIVE | 0.1925 | 0.2406 | 0.03541 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_union3_v2_CVRv5\|a0.25\|H20\|NATIVE | NATIVE | 0.1914 | 0.2408 | 0.01603 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2_CVRv5\|a0.125\|H10\|NATIVE | NATIVE | 0.191 | 0.1823 | 0.1959 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H20\|HG5 | HG | 0.1896 | 0.1822 | 0.182 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.25\|H10\|NATIVE | NATIVE | 0.1893 | 0.1478 | 0.1829 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.125\|H10\|HG10 | HG | 0.1893 | 0.198 | 0.1807 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2\|a0.25\|H20\|HG15 | HG | 0.1882 | 0.1483 | 0.1027 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2\|a0.25\|H20\|HG10 | HG | 0.1855 | 0.133 | 0.1071 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.125\|H10\|HG15 | HG | 0.1842 | 0.119 | 0.08821 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.25\|H20\|HG15 | HG | 0.1818 | 0.2043 | 0.1741 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1798 | 0.1506 | 0.1716 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H10\|HG10 | HG | 0.1784 | 0.1236 | 0.08757 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1748 | 0.1292 | 0.1678 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.5\|H10\|HG15 | HG | 0.1725 | 0.1586 | 0.177 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.125\|H10\|HG10 | HG | 0.1708 | 0.1347 | 0.07769 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.125\|H5\|NATIVE | NATIVE | 0.1691 | 0.1358 | 0.1674 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b_CVRv5\|a0.125\|H10\|NATIVE | NATIVE | 0.1685 | 0.1977 | 0.1738 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H10\|HG10 | HG | 0.1674 | 0.1267 | 0.1628 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H20\|HG15 | HG | 0.1646 | 0.1428 | 0.07762 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1645 | 0.1619 | 0.09129 | 通过 | 通过 | PASS | 16 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H10\|HG10 | HG | 0.1645 | 0.1899 | 0.1601 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H20\|HG5 | HG | 0.1628 | 0.1297 | 0.157 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b_CVRv5\|a0.125\|H10\|HG5 | HG | 0.1614 | 0.1651 | 0.154 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2\|a0.125\|H20\|NATIVE | NATIVE | 0.1613 | 0.1285 | 0.161 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.125\|H10\|NATIVE | NATIVE | 0.1612 | 0.1481 | 0.1139 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2\|a0.25\|H5\|HG5 | HG | 0.1611 | 0.1699 | 0.07187 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.125\|H2\|NATIVE | NATIVE | 0.1588 | 0.09777 | 0.1585 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b\|a0.125\|H10\|NATIVE | NATIVE | 0.1574 | 0.1622 | 0.1645 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H10\|NATIVE | NATIVE | 0.1573 | 0.122 | 0.1605 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2_CVRv5\|a0.125\|H20\|NATIVE | NATIVE | 0.1541 | 0.1293 | 0.1544 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H20\|HG10 | HG | 0.153 | 0.1016 | 0.07663 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.5\|H10\|HG10 | HG | 0.1518 | 0.1296 | 0.1545 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H10\|HG5 | HG | 0.1493 | 0.08643 | 0.07308 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2\|a0.25\|H20\|NATIVE | NATIVE | 0.1488 | 0.1784 | 0.01031 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.125\|H5\|NATIVE | NATIVE | 0.1487 | 0.114 | 0.1534 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2\|a0.25\|H10\|NATIVE | NATIVE | 0.1481 | 0.1065 | 0.09357 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|M_union3_v2_CVRv5\|a0.25\|H20\|NATIVE | NATIVE | 0.1466 | 0.1829 | -0.009125 | 不通过（e资本） | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.125\|H20\|HG15 | HG | 0.1455 | 0.1454 | 0.07214 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.25\|H20\|HG10 | HG | 0.1454 | 0.1441 | 0.1415 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2\|a0.25\|H20\|HG5 | HG | 0.1451 | 0.1214 | 0.08238 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b_CVRv5\|a0.125\|H20\|NATIVE | NATIVE | 0.1425 | 0.1427 | 0.1479 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_mean3_v2_CVRv5\|a0.125\|H2\|NATIVE | NATIVE | 0.1419 | 0.1083 | 0.1417 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H5\|HG5 | HG | 0.1383 | 0.149 | 0.05339 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.25\|H20\|HG5 | HG | 0.1382 | 0.14 | 0.1337 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.125\|H20\|NATIVE | NATIVE | 0.1376 | 0.1433 | 0.1321 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b_CVRv5\|a0.125\|H10\|HG5 | HG | 0.1353 | 0.182 | 0.1355 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b\|a0.125\|H20\|NATIVE | NATIVE | 0.1347 | 0.1498 | 0.1375 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.5\|H10\|NATIVE | NATIVE | 0.1307 | 0.1255 | 0.07009 | 通过 | 通过 | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.125\|H10\|HG10 | HG | 0.1282 | 0.07884 | 0.06254 | 通过 | 不通过（正向门槛） | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.125\|H5\|HG10 | HG | 0.1277 | 0.1365 | 0.01649 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | Q0\|A4b\|a0.125\|H20\|NATIVE | NATIVE | 0.1277 | 0.1099 | 0.1271 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|M_mean3_v2\|a0.125\|H20\|NATIVE | NATIVE | 0.1271 | 0.07713 | 0.1276 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.125\|H10\|NATIVE | NATIVE | 0.1265 | 0.1055 | 0.1285 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.25\|H10\|NATIVE | NATIVE | 0.1254 | 0.1386 | 0.1208 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.125\|H3\|NATIVE | NATIVE | 0.1247 | 0.09482 | 0.0599 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H10\|NATIVE | NATIVE | 0.124 | 0.09377 | 0.07558 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2\|a0.125\|H20\|NATIVE | NATIVE | 0.1221 | 0.119 | 0.08742 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.25\|H10\|HG5 | HG | 0.1216 | 0.1217 | 0.1205 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H20\|HG5 | HG | 0.1179 | 0.09133 | 0.05909 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2\|a0.25\|H20\|NATIVE | NATIVE | 0.1174 | 0.1197 | 0.07219 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|A4b\|a0.125\|H20\|NATIVE | NATIVE | 0.1167 | 0.1325 | 0.1173 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|A4b\|a0.125\|H20\|NATIVE | NATIVE | 0.1138 | 0.1119 | 0.1182 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.5\|H20\|HG5 | HG | 0.1107 | 0.09624 | 0.1039 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.125\|H3\|NATIVE | NATIVE | 0.1094 | 0.03683 | 0.04337 | 通过 | 不通过（正向门槛、e资本） | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | M\|M_union3_v2_CVRv5\|a0.125\|H20\|NATIVE | NATIVE | 0.1091 | 0.1044 | 0.07058 | 通过 | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.25\|H20\|NATIVE | NATIVE | 0.1078 | 0.1021 | 0.1031 | 通过 | 通过 | PASS | 14 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.25\|H5\|NATIVE | NATIVE | 0.1045 | 0.09114 | 0.09502 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | S\|A4b_CVRv5\|a0.125\|H10\|NATIVE | NATIVE | 0.1043 | 0.1088 | 0.1031 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_union3_v2_CVRv5\|a0.25\|H20\|NATIVE | NATIVE | 0.1034 | 0.1126 | 0.06424 | 通过 | 通过 | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2_CVRv5\|a0.125\|H10\|NATIVE | NATIVE | 0.102 | 0.08153 | 0.1022 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_APPLICABLE | False |
| 上一轮（同构再评，只作锚） | C1\|M_mean3_v2\|a0.125\|H20\|NATIVE | NATIVE | 0.08659 | 0.1017 | 0.08388 | 不通过（正向门槛） | 通过 | PASS | 15 | NOT_APPLICABLE | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H1\|HG30 | HG | 3.765 | 3.192 | 3.712 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b\|a0.5\|H1\|HG10 | HG | 3.692 | 3.471 | 3.661 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b\|a0.5\|H1\|HG15 | HG | 3.668 | 3.504 | 3.644 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H1\|HG20 | HG | 3.645 | 3.387 | 3.618 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|A4b\|a0.5\|H1\|HG15 | HG | 3.457 | 2.848 | 3.437 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b\|a0.5\|H1\|HG15 | HG | 3.398 | 3.393 | 3.374 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H1\|HG15 | HG | 3.281 | 3.237 | 3.247 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.5\|H1\|HG15 | HG | 3.24 | 2.784 | 3.211 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|A4b\|a0.5\|H1\|HG10 | HG | 3.214 | 2.695 | 3.201 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 3.129 | 3.51 | 2.008 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H1\|HG30 | HG | 3.127 | 3.216 | 3.053 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|A4b\|a0.5\|H1\|HG15 | HG | 3.117 | 2.33 | 3.051 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H1\|VOL_HI5 | STATE | 3.065 | 2.947 | 3.044 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.5\|H1\|HG10 | HG | 3.053 | 2.318 | 3.037 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H1\|INV10 | MEMORY | 2.982 | 2.746 | 1.57 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H1\|HG15 | HG | 2.976 | 3.176 | 1.979 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|A4b\|a0.5\|H1\|HG15 | HG | 2.964 | 2.295 | 2.959 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 2.92 | 3.163 | 1.692 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H1\|HG10 | HG | 2.903 | 2.295 | 2.882 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H1\|DECAY5_10 | MEMORY | 2.883 | 2.155 | 2.87 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H1\|VOL_HI5 | STATE | 2.883 | 3.083 | 1.928 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H1\|VOL_MEAN5 | STATE | 2.88 | 2.649 | 2.854 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b\|a0.5\|H1\|HG5 | HG | 2.872 | 2.292 | 2.87 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b\|a0.5\|H1\|HG10 | HG | 2.839 | 2.422 | 2.806 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H1\|DECAY2_10 | MEMORY | 2.839 | 2.061 | 2.825 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b\|a0.5\|H1\|HG10 | HG | 2.823 | 2.779 | 2.792 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H1\|HG30 | HG | 2.811 | 3.256 | 1.818 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H1\|VOL_MEAN5 | STATE | 2.809 | 2.989 | 1.814 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.5\|H1\|HG30 | HG | 2.799 | 3.678 | 1.574 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H1\|HG20 | HG | 2.794 | 2.858 | 2.731 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H1\|HG20 | HG | 2.789 | 3.096 | 1.834 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H1\|DECAY5_10 | MEMORY | 2.754 | 2.894 | 1.735 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.5\|H1\|HG15 | HG | 2.745 | 2.203 | 2.586 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 2.732 | 2.843 | 1.719 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H1\|INV10 | MEMORY | 2.723 | 1.928 | 2.715 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H1\|HG15 | HG | 2.691 | 2.063 | 2.693 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H1\|VOL_MEAN15 | STATE | 2.689 | 1.925 | 2.678 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|INV10 | MEMORY | 2.668 | 2.516 | 1.16 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.5\|H1\|HG20 | HG | 2.642 | 2.189 | 2.43 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 2.63 | 2.508 | 2.575 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 2.628 | 2.854 | 1.566 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H1\|VOL_HI5 | STATE | 2.624 | 2.08 | 2.629 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H1\|DECAY2_10 | MEMORY | 2.601 | 2.886 | 1.617 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H1\|HG30 | HG | 2.592 | 2.637 | 2.452 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.5\|H1\|HG30 | HG | 2.586 | 3.243 | 1.318 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H1\|HG20 | HG | 2.583 | 1.811 | 2.59 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H1\|VOL_MEAN15 | STATE | 2.574 | 2.697 | 1.566 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|A4b\|a0.5\|H1\|HG10 | HG | 2.562 | 1.642 | 2.53 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|A4b\|a0.5\|H1\|HG5 | HG | 2.551 | 1.981 | 2.541 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H1\|VOL_MEAN15 | STATE | 2.543 | 2.185 | 2.55 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H1\|VOL_MEAN5 | STATE | 2.54 | 2.025 | 2.543 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H1\|DECAY5_10 | MEMORY | 2.528 | 2.093 | 2.533 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 2.528 | 2.033 | 2.536 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H1\|INV10 | MEMORY | 2.528 | 2.033 | 2.536 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|HG30 | HG | 2.528 | 2.941 | 1.48 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.5\|H1\|HG20 | HG | 2.523 | 3.403 | 1.346 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.5\|H1\|HG15 | HG | 2.519 | 2.159 | 2.309 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H1\|DECAY2_10 | MEMORY | 2.519 | 2.125 | 2.527 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.5\|H1\|HG15 | HG | 2.518 | 2.877 | 1.661 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.5\|H1\|HG10 | HG | 2.503 | 1.848 | 2.357 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H1\|LAG1_10 | MEMORY | 2.502 | 1.635 | 2.486 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|VOL_MEAN5 | STATE | 2.497 | 2.688 | 1.432 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H1\|VOL_HI15 | STATE | 2.488 | 2.011 | 2.488 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|VOL_HI5 | STATE | 2.483 | 2.555 | 1.466 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H1\|VOL_HI15 | STATE | 2.476 | 2.613 | 1.453 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.5\|H1\|HG10 | HG | 2.473 | 2.076 | 2.257 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|DECAY5_10 | MEMORY | 2.472 | 2.549 | 1.383 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|A4b_CVRv5\|a0.5\|H1\|HG15 | HG | 2.463 | 1.849 | 2.218 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 2.461 | 2.513 | 1.374 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|HG20 | HG | 2.45 | 2.758 | 1.444 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H1\|HG15 | HG | 2.448 | 2.457 | 2.392 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.5\|H1\|HG15 | HG | 2.444 | 3.287 | 1.171 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H1\|VOL_HI15 | STATE | 2.432 | 1.628 | 2.424 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H1\|LAG1_10 | MEMORY | 2.43 | 1.995 | 2.439 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|A4b_CVRv5\|a0.5\|H1\|HG15 | HG | 2.426 | 1.999 | 2.232 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H1\|HG30 | HG | 2.405 | 1.676 | 2.416 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.5\|H1\|HG15 | HG | 2.391 | 2.263 | 2.191 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|DECAY2_10 | MEMORY | 2.366 | 2.575 | 1.299 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.5\|H1\|HG15 | HG | 2.348 | 1.818 | 2.356 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.5\|H1\|HG15 | HG | 2.335 | 3.177 | 1.183 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H1\|HG5 | HG | 2.333 | 1.967 | 2.337 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.5\|H1\|HG15 | HG | 2.33 | 2.102 | 2.329 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H1\|HG5 | HG | 2.32 | 2.542 | 1.334 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 2.318 | 2.632 | 1.39 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.5\|H1\|HG15 | HG | 2.311 | 2.902 | 1.048 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2\|a0.5\|H1\|HG15 | HG | 2.308 | 3.148 | 1.21 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b\|a0.5\|H1\|HG5 | HG | 2.304 | 2.034 | 2.302 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 2.303 | 2.894 | 0.9438 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|VOL_MEAN15 | STATE | 2.296 | 2.25 | 1.22 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|HG20 | HG | 2.287 | 1.831 | 2.319 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H1\|HG20 | HG | 2.278 | 2.325 | 2.187 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b_CVRv5\|a0.5\|H1\|HG15 | HG | 2.277 | 2.15 | 2.125 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|VOL_HI15 | STATE | 2.258 | 2.465 | 1.173 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H1\|HG20 | HG | 2.258 | 2.168 | 2.25 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 2.254 | 1.78 | 2.263 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.5\|H1\|INV10 | MEMORY | 2.254 | 1.78 | 2.263 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.5\|H1\|HG20 | HG | 2.253 | 2.897 | 1.046 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b_CVRv5\|a0.5\|H1\|HG10 | HG | 2.252 | 2.171 | 2.244 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 2.245 | 2.084 | 2.245 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H1\|HG30 | HG | 2.233 | 2.349 | 2.2 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H1\|VOL_HI5 | STATE | 2.231 | 1.963 | 2.176 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.5\|H1\|DECAY2_10 | MEMORY | 2.231 | 1.807 | 2.239 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_mean3_v2\|a0.5\|H1\|HG15 | HG | 2.231 | 1.8 | 2.259 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 2.22 | 2.117 | 2.227 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.5\|H1\|INV10 | MEMORY | 2.218 | 2.96 | 1.236 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 2.214 | 2.602 | 1.009 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 2.209 | 2.707 | 1.462 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H1\|HG5 | HG | 2.208 | 1.417 | 2.211 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_mean3_v2\|a0.5\|H1\|HG15 | HG | 2.207 | 1.418 | 2.23 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.5\|H1\|DECAY5_10 | MEMORY | 2.207 | 1.74 | 2.215 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H1\|VOL_HI15 | STATE | 2.204 | 2.095 | 2.166 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.5\|H1\|HG15 | HG | 2.195 | 2.9 | 1.44 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H1\|HG15 | HG | 2.179 | 2.073 | 2.173 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H1\|HG30 | HG | 2.179 | 2.496 | 1.617 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H1\|VOL_MEAN5 | STATE | 2.179 | 2.102 | 2.161 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|HG30 | HG | 2.174 | 1.64 | 2.211 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 2.164 | 2.821 | 0.8325 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H1\|VOL_MEAN15 | STATE | 2.163 | 2.194 | 2.119 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 2.158 | 2.854 | 0.9237 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H1\|VOL_MEAN5 | STATE | 2.147 | 2.102 | 2.1 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H1\|LAG1_10 | MEMORY | 2.139 | 1.764 | 2.104 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.5\|H1\|HG10 | HG | 2.132 | 1.55 | 1.916 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2\|a0.5\|H1\|HG15 | HG | 2.128 | 1.87 | 2.13 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|VOL_MEAN5 | STATE | 2.126 | 1.441 | 2.162 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 2.122 | 1.636 | 2.141 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 2.118 | 2.848 | 0.9749 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.5\|H1\|VOL_HI5 | STATE | 2.113 | 1.728 | 1.918 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.5\|H1\|LAG1_10 | MEMORY | 2.11 | 1.683 | 2.12 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H1\|LAG1_10 | MEMORY | 2.104 | 2.323 | 1.215 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|A4b_CVRv5\|a0.5\|H1\|HG10 | HG | 2.101 | 1.65 | 1.901 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H1\|HG30 | HG | 2.1 | 1.963 | 2.081 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H1\|DECAY5_10 | MEMORY | 2.099 | 2.028 | 2.06 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H1\|VOL_HI5 | STATE | 2.092 | 2.092 | 2.082 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H1\|DECAY2_10 | MEMORY | 2.09 | 2.034 | 2.05 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 2.087 | 1.458 | 2.109 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H1\|HG10 | HG | 2.076 | 1.971 | 2.037 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|HG15 | HG | 2.071 | 1.616 | 2.11 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|DECAY5_10 | MEMORY | 2.069 | 1.44 | 2.107 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|VOL_MEAN15 | STATE | 2.065 | 1.583 | 2.101 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|DECAY2_10 | MEMORY | 2.061 | 1.455 | 2.099 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 2.06 | 1.453 | 2.099 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|INV10 | MEMORY | 2.06 | 1.453 | 2.099 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|HG5 | HG | 2.057 | 2.205 | 1.01 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.5\|H1\|VOL_MEAN5 | STATE | 2.055 | 1.841 | 1.855 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.5\|H1\|DECAY5_10 | MEMORY | 2.049 | 1.436 | 1.849 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 2.046 | 1.654 | 2.071 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|LAG1_10 | MEMORY | 2.045 | 1.444 | 2.077 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 2.043 | 2.008 | 1.974 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.5\|H1\|HG5 | HG | 2.036 | 1.411 | 2.062 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|VOL_HI5 | STATE | 2.034 | 1.663 | 2.066 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|HG30 | HG | 2.028 | 2.357 | 1.423 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H1\|HG30 | HG | 2.025 | 1.971 | 2.022 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H1\|HG5 | HG | 2.023 | 1.748 | 1.988 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 2.023 | 1.661 | 2.026 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H1\|LAG1_10 | MEMORY | 2.019 | 2.076 | 2.012 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H1\|VOL_MEAN15 | STATE | 2.012 | 1.996 | 2.008 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 2.008 | 2.272 | 1.846 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H1\|VOL_HI15 | STATE | 1.994 | 1.916 | 1.991 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.5\|H1\|HG5 | HG | 1.987 | 2.131 | 0.8822 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_mean3_v2\|a0.5\|H1\|HG5 | HG | 1.982 | 1.388 | 2.012 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H1\|VOL_HI15 | STATE | 1.98 | 2.06 | 1.913 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H1\|HG10 | HG | 1.978 | 2.015 | 1.971 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H1\|INV10 | MEMORY | 1.978 | 2.015 | 1.971 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.977 | 2.421 | 0.7269 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.969 | 2.355 | 1.143 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 1.965 | 2.578 | 0.919 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|VOL_HI15 | STATE | 1.96 | 1.373 | 1.995 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.5\|H1\|HG5 | HG | 1.957 | 1.574 | 1.973 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.25\|H1\|HG15 | HG | 1.952 | 1.829 | 1.943 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.95 | 2.024 | 1.944 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|A4b_CVRv5\|a0.5\|H1\|HG10 | HG | 1.946 | 1.371 | 1.784 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.5\|H1\|INV10 | MEMORY | 1.946 | 2.559 | 0.9337 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H1\|HG30 | HG | 1.939 | 1.982 | 1.947 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.5\|H1\|HG5 | HG | 1.938 | 1.794 | 1.952 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 1.937 | 2.658 | 0.9438 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.936 | 2.015 | 1.929 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.5\|H1\|DECAY2_10 | MEMORY | 1.936 | 1.309 | 1.732 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.25\|H1\|HG30 | HG | 1.935 | 2.077 | 1.925 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H1\|INV10 | MEMORY | 1.933 | 1.508 | 1.914 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.5\|H1\|DECAY5_10 | MEMORY | 1.932 | 2.482 | 0.9028 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H1\|HG20 | HG | 1.932 | 1.894 | 1.928 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H1\|LAG1_10 | MEMORY | 1.929 | 2.072 | 0.9704 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 1.922 | 1.527 | 1.917 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.5\|H1\|INV10 | MEMORY | 1.919 | 1.378 | 1.709 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2\|a0.5\|H1\|HG15 | HG | 1.916 | 1.27 | 1.939 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.5\|H1\|HG15 | HG | 1.916 | 1.388 | 1.931 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 1.914 | 1.26 | 1.931 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|HG5 | HG | 1.91 | 1.44 | 1.937 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b_CVRv5\|a0.5\|H1\|HG10 | HG | 1.904 | 1.305 | 1.723 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H1\|HG15 | HG | 1.885 | 1.81 | 1.892 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H1\|VOL_MEAN5 | STATE | 1.883 | 1.68 | 1.888 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.5\|H1\|VOL_MEAN15 | STATE | 1.883 | 1.163 | 1.696 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H1\|HG5 | HG | 1.877 | 1.945 | 1.872 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.5\|H1\|HG5 | HG | 1.877 | 1.398 | 1.899 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H1\|VOL_MEAN5 | STATE | 1.876 | 1.883 | 1.797 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H1\|VOL_MEAN15 | STATE | 1.875 | 2.103 | 1.813 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.25\|H1\|HG15 | HG | 1.87 | 1.681 | 1.869 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.866 | 2.534 | 0.7977 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H1\|LAG1_10 | MEMORY | 1.854 | 1.559 | 1.789 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.5\|H1\|DECAY2_10 | MEMORY | 1.853 | 2.48 | 0.8127 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.5\|H1\|VOL_MEAN15 | STATE | 1.852 | 2.379 | 0.8115 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 1.843 | 2.442 | 1.076 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_mean3_v2\|a0.25\|H1\|HG10 | HG | 1.842 | 1.908 | 1.831 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 1.832 | 1.052 | 1.865 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H1\|DECAY5_10 | MEMORY | 1.828 | 1.859 | 1.767 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H1\|DECAY2_10 | MEMORY | 1.821 | 1.852 | 1.757 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H1\|HG30 | HG | 1.82 | 1.988 | 1.761 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H1\|HG20 | HG | 1.816 | 2.047 | 1.331 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2\|a0.5\|H1\|HG15 | HG | 1.814 | 2.25 | 1.296 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.25\|H1\|HG15 | HG | 1.811 | 1.646 | 1.812 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2\|a0.25\|H1\|HG15 | HG | 1.806 | 1.834 | 1.791 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_mean3_v2\|a0.5\|H1\|HG5 | HG | 1.796 | 1.268 | 1.828 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_mean3_v2\|a0.25\|H1\|HG15 | HG | 1.796 | 1.528 | 1.792 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.5\|H1\|HG5 | HG | 1.795 | 2.047 | 1.12 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.785 | 1.597 | 1.793 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.125\|H1\|HG30 | HG | 1.782 | 1.992 | 1.762 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H1\|VOL_HI5 | STATE | 1.782 | 1.702 | 1.695 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H1\|VOL_HI5 | STATE | 1.779 | 1.602 | 1.788 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 1.77 | 1.092 | 1.798 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H1\|HG15 | HG | 1.769 | 1.975 | 1.758 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2\|a0.25\|H1\|HG10 | HG | 1.768 | 1.604 | 1.761 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H1\|HG10 | HG | 1.765 | 1.611 | 1.774 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H1\|INV10 | MEMORY | 1.765 | 1.611 | 1.774 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 1.764 | 0.9871 | 1.77 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.764 | 1.623 | 1.769 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.5\|H1\|HG5 | HG | 1.758 | 1.905 | 0.5981 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.25\|H1\|HG10 | HG | 1.756 | 1.561 | 1.762 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H1\|HG30 | HG | 1.755 | 1.863 | 1.748 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.5\|H1\|HG5 | HG | 1.755 | 2.001 | 0.596 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H1\|VOL_MEAN5 | STATE | 1.751 | 1.927 | 1.734 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_mean3_v2\|a0.25\|H1\|HG10 | HG | 1.75 | 1.579 | 1.763 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H1\|LAG1_10 | MEMORY | 1.748 | 1.837 | 1.75 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.5\|H1\|DECAY2_10 | MEMORY | 1.742 | 2.331 | 1.087 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.5\|H1\|VOL_HI15 | STATE | 1.741 | 1.062 | 1.585 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H1\|INV10 | MEMORY | 1.74 | 1.504 | 1.659 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 1.74 | 1.311 | 1.772 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H1\|LAG1_10 | MEMORY | 1.739 | 1.571 | 1.749 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2\|a0.5\|H1\|HG5 | HG | 1.738 | 1.298 | 1.748 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H1\|HG30 | HG | 1.738 | 1.918 | 1.056 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_union3_v2\|a0.5\|H1\|HG15 | HG | 1.736 | 2.196 | 0.8786 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.728 | 1.966 | 1.715 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2\|a0.5\|H1\|HG5 | HG | 1.727 | 1.062 | 1.76 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2_CVRv5\|a0.5\|H2\|HG10 | HG | 1.724 | 1.674 | 0.6889 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.724 | 1.85 | 1.721 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2\|a0.25\|H1\|HG10 | HG | 1.716 | 1.467 | 1.731 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.25\|H1\|HG10 | HG | 1.711 | 1.517 | 1.705 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.5\|H1\|DECAY5_10 | MEMORY | 1.71 | 2.372 | 1.068 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H1\|HG20 | HG | 1.706 | 1.749 | 1.676 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2\|a0.25\|H1\|HG15 | HG | 1.705 | 1.7 | 1.711 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 1.704 | 1.589 | 1.726 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H1\|HG10 | HG | 1.704 | 1.892 | 1.693 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|HG20 | HG | 1.702 | 1.898 | 1.143 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b\|a0.5\|H2\|HG10 | HG | 1.7 | 1.225 | 1.698 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_mean3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 1.694 | 1.169 | 1.731 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H1\|HG20 | HG | 1.689 | 1.522 | 1.672 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.25\|H1\|HG5 | HG | 1.687 | 1.431 | 1.698 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H1\|VOL_HI15 | STATE | 1.684 | 1.496 | 1.69 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2\|a0.5\|H2\|HG10 | HG | 1.682 | 1.752 | 0.7625 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 1.676 | 2.394 | 1.195 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 1.666 | 1.306 | 1.634 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H1\|HG20 | HG | 1.656 | 1.757 | 1.403 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 1.656 | 1.159 | 0.6626 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H1\|HG20 | HG | 1.65 | 1.704 | 1.644 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.5\|H1\|HG5 | HG | 1.642 | 0.9445 | 1.459 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H1\|VOL_HI5 | STATE | 1.638 | 1.775 | 1.635 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H1\|VOL_MEAN15 | STATE | 1.636 | 1.637 | 1.637 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 1.634 | 2.318 | 0.9963 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 1.629 | 2.023 | 1.086 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 1.626 | 2.171 | 1.072 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_mean3_v2\|a0.25\|H1\|HG15 | HG | 1.619 | 1.465 | 1.616 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H1\|VOL_MEAN15 | STATE | 1.617 | 1.479 | 1.631 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H1\|LAG1_10 | MEMORY | 1.598 | 1.657 | 1.554 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.25\|H1\|HG15 | HG | 1.594 | 1.39 | 1.598 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG20 | HG | 1.591 | 1.685 | 1.534 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.588 | 1.336 | 1.555 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2\|a0.25\|H1\|HG10 | HG | 1.583 | 1.512 | 1.548 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.5\|H1\|LAG1_10 | MEMORY | 1.582 | 2.154 | 0.9531 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|HG20 | HG | 1.581 | 1.589 | 1.312 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H1\|HG30 | HG | 1.58 | 1.634 | 1.53 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H1\|VOL_MEAN5 | STATE | 1.571 | 1.745 | 1.218 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b\|a0.5\|H2\|HG15 | HG | 1.568 | 1.17 | 1.576 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H1\|HG15 | HG | 1.562 | 1.719 | 1.568 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.552 | 1.477 | 1.522 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H1\|HG15 | HG | 1.548 | 1.762 | 1.152 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H1\|VOL_HI15 | STATE | 1.547 | 1.537 | 1.546 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.5\|H1\|HG5 | HG | 1.545 | 1.737 | 0.7892 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H1\|HG20 | HG | 1.544 | 1.774 | 0.9218 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_mean3_v2\|a0.25\|H1\|HG10 | HG | 1.54 | 1.431 | 1.539 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_union3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 1.537 | 1.858 | 0.6312 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.536 | 1.599 | 1.483 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.536 | 1.723 | 1.473 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|VOL_MEAN5 | STATE | 1.534 | 1.626 | 1.472 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 1.528 | 1.049 | 1.472 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_mean3_v2\|a0.5\|H1\|HG5 | HG | 1.527 | 0.959 | 1.54 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H1\|HG5 | HG | 1.523 | 1.401 | 1.533 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG30 | HG | 1.519 | 1.586 | 0.7845 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG20 | HG | 1.516 | 0.8889 | 1.455 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H1\|VOL_MEAN5 | STATE | 1.515 | 1.626 | 1.445 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.125\|H1\|HG30 | HG | 1.51 | 1.657 | 1.501 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_mean3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 1.508 | 0.976 | 1.543 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG30 | HG | 1.507 | 1.496 | 1.462 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 1.507 | 1.728 | 1.157 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.25\|H1\|HG10 | HG | 1.506 | 1.294 | 1.515 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.25\|H1\|HG10 | HG | 1.506 | 1.409 | 1.507 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.25\|H1\|INV10 | MEMORY | 1.506 | 1.409 | 1.507 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 1.499 | 1.196 | 1.504 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.497 | 1.392 | 1.498 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H1\|INV10 | MEMORY | 1.497 | 1.697 | 0.9359 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 1.496 | 1.704 | 1.087 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 1.496 | 1.046 | 1.447 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.5\|H1\|VOL_HI5 | STATE | 1.496 | 1.128 | 1.436 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|HG30 | HG | 1.495 | 1.584 | 1.226 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H1\|HG15 | HG | 1.494 | 1.47 | 1.486 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 1.493 | 0.8117 | 1.53 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.492 | 1.372 | 1.493 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H1\|HG15 | HG | 1.489 | 1.543 | 1.479 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H1\|HG15 | HG | 1.487 | 1.533 | 1.465 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H1\|HG15 | HG | 1.484 | 1.467 | 1.468 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|A4b\|a0.25\|H1\|HG10 | HG | 1.482 | 1.561 | 1.485 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.481 | 1.695 | 1.123 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.25\|H1\|HG5 | HG | 1.48 | 1.47 | 1.482 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.479 | 1.547 | 1.432 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H1\|VOL_MEAN15 | STATE | 1.477 | 1.472 | 1.418 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H2\|INV10 | MEMORY | 1.476 | 1.198 | 0.1129 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 1.476 | 1.136 | 1.505 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 1.476 | 1.902 | 0.9486 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 1.465 | 1.146 | 1.479 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 1.457 | 1.185 | 1.474 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.25\|H1\|NATIVE | SMOOTH | 1.454 | 1.244 | 1.465 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H1\|HG20 | HG | 1.453 | 1.567 | 1.46 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H1\|HG30 | HG | 1.452 | 1.574 | 1.42 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2\|a0.25\|H1\|HG10 | HG | 1.448 | 1.421 | 1.438 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.5\|H1\|NATIVE | SMOOTH | 1.448 | 1.074 | 0.4056 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H1\|HG15 | HG | 1.446 | 1.565 | 1.391 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.25\|H1\|LAG1_10 | MEMORY | 1.445 | 1.314 | 1.447 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H1\|HG30 | HG | 1.444 | 1.492 | 1.094 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H1\|INV10 | MEMORY | 1.439 | 1.381 | 1.443 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H1\|HG15 | HG | 1.439 | 1.571 | 1.209 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H1\|HG20 | HG | 1.434 | 1.338 | 1.382 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H1\|VOL_MEAN5 | STATE | 1.433 | 1.437 | 1.43 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG20 | HG | 1.433 | 1.635 | 0.7485 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H1\|VOL_HI5 | STATE | 1.432 | 1.694 | 1.077 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H1\|HG15 | HG | 1.431 | 1.576 | 1.417 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.425 | 1.013 | 1.383 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 1.424 | 0.9536 | 1.448 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.5\|H2\|INV10 | MEMORY | 1.423 | 1.042 | 0.173 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.421 | 1.597 | 1.07 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_mean3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 1.417 | 0.8835 | 1.433 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2\|a0.25\|H1\|HG5 | HG | 1.413 | 1.352 | 1.41 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H1\|HG30 | HG | 1.41 | 1.474 | 1.219 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 1.408 | 1.661 | 0.6332 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H1\|VOL_HI5 | STATE | 1.404 | 1.388 | 1.396 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.5\|H1\|VOL_MEAN5 | STATE | 1.403 | 1.028 | 1.348 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.403 | 1.313 | 1.377 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG30 | HG | 1.403 | 1.429 | 1.366 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H1\|DECAY2_10 | MEMORY | 1.399 | 1.4 | 1.393 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H1\|VOL_HI5 | STATE | 1.398 | 1.5 | 1.36 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|VOL_HI5 | STATE | 1.397 | 1.515 | 1.346 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.5\|H1\|DECAY2_10 | MEMORY | 1.396 | 1.109 | 1.34 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|VOL_MEAN5 | STATE | 1.396 | 1.592 | 0.9936 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H1\|HG10 | HG | 1.396 | 1.392 | 1.391 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H1\|INV10 | MEMORY | 1.396 | 1.392 | 1.391 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.394 | 1.655 | 0.9389 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H1\|HG10 | HG | 1.394 | 1.104 | 1.388 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.392 | 1.756 | 0.8194 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 1.391 | 1.026 | 1.352 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H1\|HG15 | HG | 1.39 | 1.424 | 1.358 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.25\|H1\|HG15 | HG | 1.388 | 1.408 | 1.001 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H1\|DECAY5_10 | MEMORY | 1.381 | 1.402 | 1.374 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.125\|H1\|HG15 | HG | 1.38 | 1.443 | 1.375 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H2\|HG15 | HG | 1.378 | 0.9778 | 1.378 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.376 | 0.9191 | 1.341 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.5\|H1\|DECAY5_10 | MEMORY | 1.375 | 1.078 | 1.317 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H1\|HG10 | HG | 1.374 | 1.313 | 1.359 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.374 | 1.343 | 1.304 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.373 | 1.402 | 1.331 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG30 | HG | 1.373 | 1.428 | 1.327 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H1\|HG15 | HG | 1.372 | 1.523 | 1.374 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.371 | 1.041 | 1.313 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.5\|H1\|DECAY5_10 | MEMORY | 1.371 | 0.9593 | 1.33 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H1\|VOL_MEAN15 | STATE | 1.37 | 1.563 | 0.994 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.5\|H1\|DECAY2_10 | MEMORY | 1.37 | 0.973 | 1.324 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H1\|LAG1_10 | MEMORY | 1.365 | 1.311 | 1.336 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|INV10 | MEMORY | 1.364 | 1.534 | 1.3 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.25\|H1\|HG15 | HG | 1.363 | 1.106 | 1.363 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.5\|H2\|HG30 | HG | 1.361 | 1.568 | 0.2796 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H1\|VOL_MEAN5 | STATE | 1.36 | 1.416 | 1.157 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H1\|HG15 | HG | 1.359 | 1.38 | 1.332 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H1\|DECAY2_10 | MEMORY | 1.358 | 1.285 | 1.165 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.5\|H2\|HG10 | HG | 1.357 | 1.009 | 1.349 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_mean3_v2\|a0.25\|H1\|NATIVE | SMOOTH | 1.356 | 1.291 | 1.372 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.5\|H1\|INV10 | MEMORY | 1.356 | 1.08 | 1.279 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|VOL_MEAN15 | STATE | 1.354 | 1.525 | 1.307 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.353 | 1.585 | 0.9554 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H1\|HG20 | HG | 1.353 | 1.422 | 1.205 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H1\|VOL_HI5 | STATE | 1.351 | 1.589 | 1.348 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG5 | HG | 1.35 | 1.094 | 1.316 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.5\|H1\|VOL_HI15 | STATE | 1.346 | 0.9826 | 1.29 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H1\|VOL_HI15 | STATE | 1.344 | 1.427 | 0.9586 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.5\|H1\|DECAY2_10 | MEMORY | 1.343 | 1.748 | 0.6903 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.343 | 1.259 | 1.304 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.5\|H1\|LAG1_10 | MEMORY | 1.342 | 0.9807 | 1.284 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|LAG1_10 | MEMORY | 1.341 | 1.569 | 1.305 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.5\|H1\|DECAY5_10 | MEMORY | 1.341 | 1.836 | 0.6868 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.338 | 1.576 | 0.8741 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H1\|VOL_HI5 | STATE | 1.338 | 1.452 | 1.285 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|VOL_MEAN5 | STATE | 1.334 | 1.306 | 1.13 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H1\|LAG1_10 | MEMORY | 1.333 | 1.341 | 1.326 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H1\|VOL_HI15 | STATE | 1.331 | 1.351 | 1.279 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.5\|H1\|VOL_MEAN15 | STATE | 1.33 | 1.084 | 1.275 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H1\|HG15 | HG | 1.329 | 1.345 | 1.291 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.329 | 1.559 | 1.283 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|DECAY2_10 | MEMORY | 1.327 | 1.416 | 1.134 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_mean3_v2\|a0.25\|H1\|HG5 | HG | 1.325 | 1.216 | 1.331 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.5\|H2\|VOL_HI5 | STATE | 1.325 | 1.035 | 1.333 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H1\|HG15 | HG | 1.325 | 1.434 | 0.9272 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H1\|VOL_HI5 | STATE | 1.324 | 1.467 | 1.119 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H1\|HG5 | HG | 1.324 | 1.196 | 1.328 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H1\|VOL_MEAN5 | STATE | 1.323 | 1.354 | 1.322 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|HG30 | HG | 1.321 | 1.37 | 0.9504 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H1\|VOL_MEAN5 | STATE | 1.319 | 1.205 | 1.287 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H1\|LAG1_10 | MEMORY | 1.318 | 1.274 | 1.13 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.317 | 1.865 | 0.8198 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.316 | 1.139 | 1.296 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H1\|HG30 | HG | 1.316 | 1.38 | 1.113 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.316 | 1.535 | 0.9134 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.125\|H1\|HG15 | HG | 1.313 | 1.413 | 1.311 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.25\|H1\|HG5 | HG | 1.306 | 1.25 | 1.303 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|VOL_HI15 | STATE | 1.306 | 1.478 | 1.264 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 1.303 | 1.486 | 0.708 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|INV10 | MEMORY | 1.299 | 1.463 | 0.6742 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H1\|DECAY2_10 | MEMORY | 1.299 | 1.242 | 1.264 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H1\|HG30 | HG | 1.298 | 1.435 | 1.241 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.5\|H1\|INV10 | MEMORY | 1.296 | 0.8922 | 1.237 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H1\|HG20 | HG | 1.295 | 1.191 | 1.073 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H2\|HG20 | HG | 1.295 | 1.433 | 1.258 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b\|a0.5\|H2\|HG10 | HG | 1.295 | 0.7004 | 1.289 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H1\|VOL_HI5 | STATE | 1.294 | 1.226 | 1.265 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H1\|HG15 | HG | 1.293 | 1.604 | 0.7721 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H1\|DECAY5_10 | MEMORY | 1.288 | 1.269 | 1.094 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H1\|LAG1_10 | MEMORY | 1.287 | 1.439 | 0.9477 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2\|a0.5\|H2\|HG10 | HG | 1.284 | 1.105 | 1.261 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.5\|H2\|HG15 | HG | 1.281 | 1.664 | 0.4771 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.25\|H1\|NATIVE | SMOOTH | 1.281 | 1.189 | 1.279 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2_CVRv5\|a0.5\|H3\|HG10 | HG | 1.281 | 1.143 | 0.3392 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.281 | 1.281 | 1.261 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.25\|H1\|HG15 | HG | 1.28 | 1.558 | 0.661 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.279 | 1.309 | 1.256 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|VOL_HI5 | STATE | 1.278 | 1.414 | 1.069 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b\|a0.5\|H1\|NATIVE | SMOOTH | 1.278 | 1.098 | 1.274 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H1\|HG20 | HG | 1.277 | 1.427 | 1.227 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|INV10 | MEMORY | 1.276 | 1.371 | 0.8838 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.274 | 1.526 | 1.228 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H1\|HG10 | HG | 1.272 | 1.243 | 1.076 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H1\|VOL_MEAN5 | STATE | 1.271 | 1.392 | 1.249 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.271 | 1.528 | 1.226 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H1\|DECAY5_10 | MEMORY | 1.27 | 1.195 | 1.237 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.269 | 1.454 | 0.8707 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.125\|H1\|VOL_HI5 | STATE | 1.269 | 1.295 | 1.266 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H1\|LAG1_10 | MEMORY | 1.267 | 1.351 | 1.245 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_mean3_v2\|a0.125\|H1\|HG15 | HG | 1.266 | 1.375 | 1.261 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|LAG1_10 | MEMORY | 1.264 | 1.36 | 1.075 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|DECAY5_10 | MEMORY | 1.263 | 1.366 | 1.074 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.262 | 1.204 | 1.256 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H1\|VOL_MEAN15 | STATE | 1.262 | 1.212 | 1.229 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG30 | HG | 1.256 | 1.451 | 1.2 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|VOL_MEAN15 | STATE | 1.254 | 1.448 | 0.8289 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.252 | 1.187 | 0.798 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 1.252 | 1.373 | 0.8891 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b\|a0.5\|H2\|HG10 | HG | 1.248 | 1.206 | 1.242 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H1\|INV10 | MEMORY | 1.247 | 1.187 | 0.8823 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|VOL_HI15 | STATE | 1.244 | 1.377 | 0.8079 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.5\|H2\|HG15 | HG | 1.244 | 1.619 | 0.06525 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|VOL_HI5 | STATE | 1.243 | 1.482 | 0.8378 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H1\|HG20 | HG | 1.242 | 1.295 | 1.082 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG5 | HG | 1.239 | 0.9543 | 1.183 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.239 | 1.371 | 1.221 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.25\|H1\|HG15 | HG | 1.237 | 1.015 | 1.207 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H1\|VOL_MEAN15 | STATE | 1.235 | 1.265 | 1.232 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H1\|VOL_HI15 | STATE | 1.235 | 1.238 | 1.204 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H1\|VOL_HI5 | STATE | 1.231 | 1.199 | 1.237 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H2\|DECAY5_10 | MEMORY | 1.231 | 1.25 | 0.3465 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H1\|HG15 | HG | 1.23 | 1.255 | 1.12 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H1\|VOL_MEAN15 | STATE | 1.229 | 1.274 | 1.047 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|VOL_MEAN15 | STATE | 1.228 | 1.256 | 1.05 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.5\|H2\|HG15 | HG | 1.224 | 0.8303 | 1.217 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.25\|H1\|HG15 | HG | 1.223 | 1.37 | 0.6464 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H1\|INV10 | MEMORY | 1.223 | 1.402 | 0.6035 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_union3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.222 | 1.47 | 0.4062 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.5\|H2\|HG15 | HG | 1.221 | 1.634 | 0.5043 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.125\|H1\|HG10 | HG | 1.219 | 1.332 | 1.218 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H1\|INV10 | MEMORY | 1.217 | 1.255 | 1.147 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2\|a0.125\|H1\|HG15 | HG | 1.215 | 1.29 | 1.213 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H2\|HG30 | HG | 1.212 | 1.37 | 1.161 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H1\|HG10 | HG | 1.21 | 1.129 | 1.176 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H1\|INV10 | MEMORY | 1.21 | 1.129 | 1.176 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_mean3_v2\|a0.125\|H1\|HG10 | HG | 1.21 | 1.211 | 1.204 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H1\|INV10 | MEMORY | 1.208 | 1.463 | 0.6922 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 1.206 | 1.531 | 0.6633 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.205 | 0.9008 | 1.163 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H1\|VOL_HI15 | STATE | 1.205 | 1.189 | 1.198 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.201 | 1.412 | 1.146 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 1.201 | 1.069 | 1.179 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG20 | HG | 1.2 | 1.191 | 1.157 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.2 | 1.447 | 0.6092 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.198 | 1.328 | 1.185 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H1\|VOL_HI15 | STATE | 1.198 | 1.256 | 1.183 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.197 | 1.134 | 1.159 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H1\|HG5 | HG | 1.196 | 1.286 | 1.162 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.196 | 1.163 | 1.192 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H1\|INV10 | MEMORY | 1.195 | 1.525 | 0.5052 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.194 | 1.293 | 0.7566 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2\|a0.25\|H1\|HG15 | HG | 1.192 | 1.281 | 0.6204 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.191 | 1.207 | 1.147 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H1\|LAG1_10 | MEMORY | 1.191 | 1.178 | 1.191 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.25\|H1\|HG15 | HG | 1.19 | 1.408 | 0.8196 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG20 | HG | 1.187 | 1.24 | 1.144 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H2\|DECAY2_10 | MEMORY | 1.185 | 1.327 | 0.3053 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H1\|LAG1_10 | MEMORY | 1.183 | 1.179 | 1.175 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H2\|VOL_MEAN5 | STATE | 1.182 | 1.247 | 0.3358 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H2\|HG10 | HG | 1.181 | 1.148 | 0.3089 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.18 | 1.416 | 0.4946 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H1\|HG10 | HG | 1.179 | 1.289 | 1.171 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H1\|HG10 | HG | 1.176 | 1.209 | 1.17 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.176 | 0.8568 | 1.12 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.174 | 1.224 | 1.172 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|HG20 | HG | 1.174 | 1.122 | 0.917 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H1\|HG10 | HG | 1.174 | 1.172 | 1.181 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H1\|VOL_MEAN5 | STATE | 1.172 | 1.227 | 1.175 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H1\|HG5 | HG | 1.172 | 1.342 | 0.8396 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b\|a0.25\|H1\|HG10 | HG | 1.172 | 1.113 | 1.179 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.171 | 1.178 | 1.169 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H1\|VOL_HI15 | STATE | 1.167 | 1.262 | 0.9905 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG20 | HG | 1.166 | 1.27 | 1.122 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.165 | 1.434 | 0.5515 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H1\|VOL_MEAN5 | STATE | 1.157 | 1.215 | 1.13 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|LAG1_10 | MEMORY | 1.157 | 1.333 | 0.7739 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H1\|VOL_HI15 | STATE | 1.155 | 1.176 | 0.9737 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 1.154 | 1.386 | 0.6252 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2\|a0.125\|H1\|HG10 | HG | 1.152 | 1.168 | 1.142 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.25\|H1\|INV10 | MEMORY | 1.151 | 1.044 | 1.1 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H1\|HG10 | HG | 1.151 | 1.057 | 1.141 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H1\|HG10 | HG | 1.15 | 0.9353 | 1.153 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b\|a0.25\|H1\|HG10 | HG | 1.15 | 0.8085 | 1.154 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H1\|VOL_MEAN5 | STATE | 1.15 | 1.277 | 1.155 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 1.147 | 0.7971 | 1.106 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H1\|VOL_HI5 | STATE | 1.142 | 1.287 | 1.124 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.25\|H1\|NATIVE | SMOOTH | 1.14 | 0.9172 | 1.14 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H1\|HG15 | HG | 1.139 | 1.21 | 0.9497 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H2\|HG15 | HG | 1.139 | 1.193 | 1.103 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H1\|VOL_MEAN5 | STATE | 1.135 | 1.237 | 0.6605 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 1.13 | 1.396 | 1.092 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.129 | 1.197 | 0.7055 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2_CVRv5\|a0.25\|H1\|VOL_MEAN5 | STATE | 1.128 | 1.029 | 1.088 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H1\|INV10 | MEMORY | 1.127 | 1.153 | 0.8621 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|A4b\|a0.25\|H1\|HG10 | HG | 1.127 | 0.7514 | 1.133 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H1\|VOL_HI5 | STATE | 1.126 | 1.102 | 1.101 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H1\|VOL_MEAN5 | STATE | 1.123 | 1.192 | 1.027 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.25\|H1\|NATIVE | SMOOTH | 1.121 | 0.8338 | 1.124 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_mean3_v2\|a0.125\|H1\|HG10 | HG | 1.118 | 1.222 | 1.118 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H1\|HG20 | HG | 1.113 | 1.18 | 1.119 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.109 | 0.9672 | 1.073 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG5 | HG | 1.105 | 0.6592 | 1.071 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.25\|H1\|HG10 | HG | 1.104 | 0.7264 | 1.091 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H1\|HG5 | HG | 1.104 | 1.109 | 1.099 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.102 | 1.373 | 0.4662 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.101 | 0.9561 | 1.066 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.101 | 1.034 | 1.067 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.1 | 1.14 | 1.062 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.099 | 0.9309 | 1.064 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2_CVRv5\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.098 | 0.9781 | 1.063 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H1\|VOL_HI5 | STATE | 1.097 | 1.11 | 1.014 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2_CVRv5\|a0.25\|H1\|VOL_HI5 | STATE | 1.095 | 0.9052 | 1.056 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.095 | 1.247 | 0.6868 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.125\|H1\|HG10 | HG | 1.094 | 1.185 | 1.091 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.125\|H1\|INV10 | MEMORY | 1.094 | 1.185 | 1.091 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.094 | 1.159 | 0.4507 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2_CVRv5\|a0.5\|H1\|NATIVE | SMOOTH | 1.092 | 0.9044 | 1.063 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_union3_v2\|a0.5\|H1\|HG5 | HG | 1.09 | 0.9987 | 0.413 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.125\|H1\|HG15 | HG | 1.088 | 1.213 | 1.087 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H1\|HG15 | HG | 1.085 | 1.14 | 1.098 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H1\|HG20 | HG | 1.085 | 0.9985 | 0.9813 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H1\|INV10 | MEMORY | 1.084 | 0.9994 | 1.093 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.082 | 1.383 | 0.4907 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H1\|DECAY5_10 | MEMORY | 1.078 | 1.028 | 1.068 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H1\|VOL_HI5 | STATE | 1.077 | 1.144 | 0.6025 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H1\|DECAY2_10 | MEMORY | 1.076 | 1.022 | 1.066 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H1\|VOL_MEAN5 | STATE | 1.076 | 1.168 | 1.06 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H1\|VOL_MEAN5 | STATE | 1.074 | 1.204 | 1.042 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2_CVRv5\|a0.25\|H1\|INV10 | MEMORY | 1.072 | 0.8397 | 1.018 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG15 | HG | 1.07 | 1.068 | 1.045 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.069 | 1.163 | 0.7168 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.125\|H1\|LAG1_10 | MEMORY | 1.067 | 1.119 | 1.069 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H1\|HG10 | HG | 1.066 | 1.195 | 1.062 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H1\|HG5 | HG | 1.066 | 1.121 | 0.9108 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2_CVRv5\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.064 | 0.9611 | 1.026 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b_CVRv5\|a0.25\|H1\|HG10 | HG | 1.061 | 0.8827 | 1.067 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H1\|DECAY2_10 | MEMORY | 1.06 | 1.104 | 1.059 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2\|a0.25\|H1\|HG15 | HG | 1.058 | 1.239 | 0.7578 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H1\|HG10 | HG | 1.057 | 1.01 | 1.05 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H1\|INV10 | MEMORY | 1.057 | 1.01 | 1.05 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2\|a0.125\|H1\|HG10 | HG | 1.056 | 1.195 | 1.054 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG5 | HG | 1.055 | 0.5456 | 1.009 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_mean3_v2\|a0.25\|H1\|NATIVE | SMOOTH | 1.052 | 0.9955 | 1.055 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H1\|VOL_MEAN5 | STATE | 1.051 | 1.287 | 0.4951 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.5\|H2\|VOL_MEAN15 | STATE | 1.05 | 0.6451 | 1.073 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.125\|H1\|DECAY5_10 | MEMORY | 1.05 | 1.176 | 1.051 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H1\|HG5 | HG | 1.049 | 1.132 | 1.031 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H1\|DECAY2_10 | MEMORY | 1.046 | 1.072 | 0.934 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.043 | 1.121 | 0.6863 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2\|a0.125\|H1\|HG10 | HG | 1.043 | 1.154 | 1.017 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.25\|H1\|INV10 | MEMORY | 1.043 | 1.203 | 0.479 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.043 | 0.9781 | 1.006 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H1\|DECAY5_10 | MEMORY | 1.042 | 1.091 | 1.004 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.125\|H1\|DECAY2_10 | MEMORY | 1.041 | 1.138 | 1.043 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 1.04 | 1.195 | 0.6647 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.125\|H1\|HG15 | HG | 1.038 | 1.067 | 1.015 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 1.037 | 0.8817 | 0.9868 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2_CVRv5\|a0.25\|H1\|LAG1_10 | MEMORY | 1.037 | 0.8149 | 0.9979 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H1\|VOL_HI15 | STATE | 1.036 | 1.109 | 0.9996 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H1\|VOL_HI15 | STATE | 1.033 | 1.352 | 0.4865 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.25\|H1\|HG10 | HG | 1.031 | 0.7022 | 1.003 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|A4b_CVRv5\|a0.25\|H1\|HG10 | HG | 1.031 | 0.7766 | 0.9887 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|A4b\|a0.125\|H1\|HG10 | HG | 1.029 | 1.186 | 1.039 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.125\|H1\|HG10 | HG | 1.027 | 0.9826 | 1.023 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H1\|VOL_HI15 | STATE | 1.027 | 1.38 | 0.5598 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H1\|HG20 | HG | 1.025 | 1.018 | 1.001 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 1.024 | 0.9134 | 0.9834 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H1\|VOL_HI5 | STATE | 1.017 | 1.012 | 1 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H1\|DECAY5_10 | MEMORY | 1.017 | 1.113 | 1.017 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H1\|DECAY5_10 | MEMORY | 1.016 | 1.012 | 0.9088 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H1\|DECAY2_10 | MEMORY | 1.015 | 1.073 | 0.9873 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H1\|HG5 | HG | 1.013 | 1.104 | 1.018 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.5\|H1\|NATIVE | SMOOTH | 1.013 | 1.092 | 0.3577 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 1.012 | 0.9898 | 0.9096 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 1.011 | 1.205 | 0.4925 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H1\|LAG1_10 | MEMORY | 1.011 | 0.9931 | 0.9829 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H2\|HG30 | HG | 1.009 | 1.159 | 0.516 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2\|a0.25\|H1\|HG15 | HG | 1.008 | 1.261 | 0.5001 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H1\|INV10 | MEMORY | 1.005 | 1.016 | 0.7064 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 1.005 | 1.107 | 0.6586 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H1\|INV10 | MEMORY | 1.002 | 1.198 | 0.6878 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|HG15 | HG | 1.002 | 1.119 | 0.7859 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H1\|HG10 | HG | 1.002 | 1.036 | 1.008 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H1\|DECAY2_10 | MEMORY | 1.001 | 1.048 | 0.964 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H1\|VOL_HI5 | STATE | 0.9987 | 0.9749 | 1.004 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b_CVRv5\|a0.125\|H1\|HG15 | HG | 0.9984 | 0.8692 | 0.9674 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H1\|DECAY2_10 | MEMORY | 0.9984 | 1.045 | 0.9722 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H1\|LAG1_10 | MEMORY | 0.9943 | 0.9598 | 0.9847 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H1\|HG5 | HG | 0.9939 | 0.9765 | 0.9917 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 0.9937 | 1.201 | 0.6732 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.9935 | 0.9228 | 0.9508 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H2\|VOL_HI15 | STATE | 0.9932 | 1.001 | 0.9653 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.9909 | 1.151 | 0.9622 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H1\|INV10 | MEMORY | 0.9862 | 1.129 | 0.6718 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H2\|VOL_HI5 | STATE | 0.9859 | 0.9386 | 0.9553 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_union3_v2\|a0.5\|H2\|HG10 | HG | 0.9837 | 1.151 | 0.8585 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b_CVRv5\|a0.5\|H1\|NATIVE | SMOOTH | 0.9824 | 1.163 | 0.9709 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H1\|HG15 | HG | 0.9816 | 1.01 | 0.7792 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.25\|H1\|LAG1_10 | MEMORY | 0.9773 | 0.8282 | 0.9455 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.125\|H1\|HG15 | HG | 0.9766 | 1.016 | 0.7646 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H1\|HG15 | HG | 0.9753 | 0.9608 | 0.9546 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H1\|VOL_MEAN15 | STATE | 0.9751 | 0.9801 | 0.9722 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 0.9743 | 1.076 | 0.5206 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H1\|DECAY5_10 | MEMORY | 0.9715 | 0.9913 | 0.9477 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H1\|LAG1_10 | MEMORY | 0.9711 | 1.04 | 0.8853 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.9711 | 1.042 | 0.9762 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.25\|H1\|HG5 | HG | 0.9687 | 0.9977 | 0.5057 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2\|a0.25\|H1\|NATIVE | SMOOTH | 0.9685 | 0.8703 | 0.9697 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.25\|H1\|HG10 | HG | 0.9639 | 0.7427 | 0.9338 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H2\|HG20 | HG | 0.9623 | 1.017 | 0.9067 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2_CVRv5\|a0.25\|H1\|VOL_HI15 | STATE | 0.9619 | 0.7796 | 0.9255 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H1\|LAG1_10 | MEMORY | 0.9618 | 0.9862 | 0.9677 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H1\|VOL_MEAN5 | STATE | 0.9614 | 0.9919 | 0.8446 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H1\|DECAY2_10 | MEMORY | 0.9604 | 1.108 | 0.5048 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H2\|HG30 | HG | 0.96 | 1.059 | 0.9383 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 0.9595 | 1.089 | 0.8157 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_mean3_v2\|a0.125\|H1\|HG10 | HG | 0.9574 | 0.9873 | 0.9511 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.25\|H1\|VOL_HI15 | STATE | 0.9567 | 0.7365 | 0.9441 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 0.9564 | 0.9282 | 0.9372 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.125\|H1\|HG5 | HG | 0.9549 | 0.9255 | 0.9601 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.9543 | 0.9318 | 0.9214 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.9536 | 1.202 | 0.4217 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.125\|H1\|HG15 | HG | 0.9523 | 1.044 | 0.6497 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H1\|VOL_MEAN5 | STATE | 0.9499 | 1.013 | 0.7837 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H2\|VOL_MEAN15 | STATE | 0.9482 | 1.101 | 0.9167 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b\|a0.25\|H1\|HG10 | HG | 0.9481 | 0.7671 | 0.9439 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H1\|INV10 | MEMORY | 0.9465 | 0.8644 | 0.9237 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|LAG1_10 | MEMORY | 0.9452 | 1.074 | 0.9089 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H1\|VOL_MEAN15 | STATE | 0.9445 | 1.201 | 0.4992 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H1\|LAG1_10 | MEMORY | 0.9443 | 1.078 | 0.6111 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H2\|HG10 | HG | 0.9433 | 1.003 | 0.9137 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.25\|H1\|VOL_HI5 | STATE | 0.9426 | 0.9422 | 0.9139 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H1\|DECAY5_10 | MEMORY | 0.9426 | 0.9968 | 0.4844 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2_CVRv5\|a0.25\|H1\|NATIVE | SMOOTH | 0.9426 | 0.8532 | 0.9211 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG10 | HG | 0.9409 | 0.8052 | 0.9105 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H1\|HG5 | HG | 0.9407 | 0.8259 | 0.9344 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.5\|H2\|HG5 | HG | 0.9403 | 1.285 | 0.265 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H2\|HG30 | HG | 0.9388 | 1.016 | 0.8496 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H1\|VOL_MEAN5 | STATE | 0.9382 | 0.9843 | 0.9245 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.9375 | 0.9727 | 0.943 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H1\|HG5 | HG | 0.9373 | 0.9686 | 0.9367 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H1\|LAG1_10 | MEMORY | 0.9353 | 0.9228 | 0.9108 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H1\|HG15 | HG | 0.9335 | 0.9138 | 0.8487 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b\|a0.25\|H1\|HG10 | HG | 0.9329 | 0.7339 | 0.9323 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H1\|VOL_HI5 | STATE | 0.9328 | 0.9242 | 0.9164 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b\|a0.25\|H1\|HG5 | HG | 0.9304 | 0.5863 | 0.9411 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.25\|H1\|DECAY5_10 | MEMORY | 0.9287 | 0.8957 | 0.9011 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 0.9274 | 0.965 | 0.7185 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H1\|HG5 | HG | 0.9269 | 0.9157 | 0.9168 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2_CVRv5\|a0.5\|H1\|HG15 | HG | 0.9258 | 0.5936 | 0.8872 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H2\|VOL_MEAN5 | STATE | 0.9248 | 0.9394 | 0.8913 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H1\|HG5 | HG | 0.9243 | 0.9372 | 0.919 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2_CVRv5\|a0.25\|H1\|VOL_MEAN15 | STATE | 0.9242 | 0.8527 | 0.8951 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.25\|H1\|DECAY2_10 | MEMORY | 0.924 | 0.877 | 0.8937 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 0.922 | 1.142 | 0.3592 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H1\|VOL_HI5 | STATE | 0.9218 | 1.1 | 0.3896 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b_CVRv5\|a0.25\|H1\|HG5 | HG | 0.9214 | 0.7831 | 0.8984 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.9213 | 1.13 | 0.358 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H1\|DECAY5_10 | MEMORY | 0.9212 | 1.148 | 0.3879 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H1\|DECAY2_10 | MEMORY | 0.9211 | 1.201 | 0.3917 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H1\|VOL_MEAN15 | STATE | 0.9205 | 1.208 | 0.4086 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H1\|INV10 | MEMORY | 0.9199 | 1.071 | 0.5493 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H1\|HG5 | HG | 0.9197 | 0.7407 | 0.9307 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 0.9189 | 0.939 | 0.8857 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H1\|HG20 | HG | 0.9186 | 0.8582 | 0.8119 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H1\|HG15 | HG | 0.9158 | 0.9679 | 0.656 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H1\|LAG1_10 | MEMORY | 0.9076 | 1.12 | 0.4715 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H1\|INV10 | MEMORY | 0.9071 | 0.8403 | 0.911 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.25\|H1\|DECAY2_10 | MEMORY | 0.9064 | 0.9646 | 0.5183 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.25\|H1\|VOL_MEAN5 | STATE | 0.906 | 0.8918 | 0.878 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.125\|H1\|VOL_MEAN15 | STATE | 0.9055 | 1.048 | 0.9059 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H2\|DECAY2_10 | MEMORY | 0.9043 | 0.9551 | 0.8738 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H1\|VOL_HI5 | STATE | 0.904 | 0.961 | 0.7361 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|VOL_HI15 | STATE | 0.904 | 0.9928 | 0.8676 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.125\|H1\|HG15 | HG | 0.9037 | 0.9426 | 0.6283 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b\|a0.125\|H1\|HG10 | HG | 0.9035 | 0.707 | 0.9061 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.9028 | 1.04 | 0.5432 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2\|a0.125\|H1\|HG10 | HG | 0.9013 | 0.8911 | 0.8921 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG15 | HG | 0.9003 | 1.052 | 0.5478 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H1\|INV10 | MEMORY | 0.898 | 0.9837 | 0.6571 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b\|a0.5\|H1\|NATIVE | SMOOTH | 0.8971 | 1.119 | 0.9003 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.8964 | 0.7191 | 0.8798 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 0.8964 | 0.9603 | 0.4978 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 0.8963 | 0.7753 | 0.8602 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H1\|VOL_MEAN15 | STATE | 0.896 | 0.854 | 0.81 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H1\|DECAY2_10 | MEMORY | 0.8952 | 0.907 | 0.7691 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|VOL_HI5 | STATE | 0.8945 | 0.874 | 0.8654 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b_CVRv5\|a0.125\|H1\|HG10 | HG | 0.8933 | 0.6338 | 0.8663 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2\|a0.125\|H1\|HG10 | HG | 0.8918 | 0.9943 | 0.7252 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.25\|H1\|DECAY5_10 | MEMORY | 0.8914 | 0.9327 | 0.495 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H1\|VOL_HI5 | STATE | 0.8899 | 0.857 | 0.8019 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H1\|LAG1_10 | MEMORY | 0.8884 | 0.8836 | 0.8829 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2_CVRv5\|a0.5\|H2\|HG10 | HG | 0.8884 | 0.7862 | 0.8513 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H1\|HG15 | HG | 0.8881 | 0.8945 | 0.6453 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.25\|H1\|HG5 | HG | 0.888 | 0.5766 | 0.8716 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H1\|VOL_MEAN15 | STATE | 0.8873 | 1.051 | 0.8575 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.125\|H1\|HG10 | HG | 0.8868 | 0.8822 | 0.8804 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H1\|LAG1_10 | MEMORY | 0.8863 | 0.7972 | 0.881 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b\|a0.25\|H1\|HG5 | HG | 0.8839 | 0.6946 | 0.8878 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H2\|HG5 | HG | 0.8837 | 0.7721 | 0.8623 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H1\|INV10 | MEMORY | 0.8822 | 0.9006 | 0.8523 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H1\|VOL_HI15 | STATE | 0.881 | 0.9548 | 0.8677 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2_CVRv5\|a0.5\|H10\|HG10 | HG | 0.8792 | 1.047 | 0.2043 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|INV10 | MEMORY | 0.8791 | 0.9688 | 0.8272 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.125\|H1\|VOL_HI15 | STATE | 0.8789 | 0.8769 | 0.8835 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2_CVRv5\|a0.5\|H1\|NATIVE | SMOOTH | 0.8776 | 0.3943 | 0.8482 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H2\|HG30 | HG | 0.8761 | 0.9637 | 0.4396 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|INV10 | MEMORY | 0.8721 | 1.089 | 0.5204 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.8712 | 0.9093 | 0.8606 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.25\|H1\|HG5 | HG | 0.8706 | 0.9522 | 0.5749 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.87 | 0.8611 | 0.8423 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|DECAY2_10 | MEMORY | 0.8679 | 0.9976 | 0.8278 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H1\|HG15 | HG | 0.8673 | 0.904 | 0.6354 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.8661 | 0.9172 | 0.7032 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 0.8647 | 0.939 | 0.6067 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H1\|VOL_MEAN15 | STATE | 0.8646 | 0.8652 | 0.8372 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H1\|HG10 | HG | 0.8645 | 0.9538 | 0.7076 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 0.8644 | 1.013 | 0.3528 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b\|a0.125\|H1\|HG10 | HG | 0.8642 | 0.8947 | 0.8548 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.864 | 0.8749 | 0.8518 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2\|a0.125\|H1\|HG15 | HG | 0.8637 | 0.8469 | 0.6169 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H1\|LAG1_10 | MEMORY | 0.8625 | 1.148 | 0.342 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H1\|INV10 | MEMORY | 0.862 | 0.7937 | 0.8322 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.8614 | 0.8749 | 0.8494 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H1\|VOL_MEAN15 | STATE | 0.8612 | 0.7764 | 0.8531 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.8606 | 0.936 | 0.4735 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H1\|LAG1_10 | MEMORY | 0.8586 | 0.9355 | 0.8414 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H1\|INV10 | MEMORY | 0.8581 | 0.9647 | 0.5026 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H1\|DECAY5_10 | MEMORY | 0.8578 | 0.8339 | 0.7351 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|DECAY5_10 | MEMORY | 0.8537 | 1 | 0.8142 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H1\|LAG1_10 | MEMORY | 0.8523 | 0.9599 | 0.8357 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H1\|NATIVE | SMOOTH | 0.8512 | 0.7451 | 0.8378 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.25\|H1\|HG5 | HG | 0.8505 | 0.5558 | 0.852 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|VOL_MEAN15 | STATE | 0.8505 | 0.9291 | 0.8149 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.8498 | 0.8898 | 0.6949 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b_CVRv5\|a0.125\|H1\|HG10 | HG | 0.8482 | 0.8032 | 0.8414 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H2\|HG20 | HG | 0.8476 | 0.9827 | 0.377 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H1\|LAG1_10 | MEMORY | 0.8474 | 0.6588 | 0.8114 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H1\|HG15 | HG | 0.8473 | 0.8935 | 0.5468 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H2\|DECAY5_10 | MEMORY | 0.847 | 0.886 | 0.8613 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.8465 | 0.6858 | 0.8179 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2\|a0.25\|H1\|HG10 | HG | 0.8455 | 1.024 | 0.4039 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.843 | 0.8748 | 0.8303 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H1\|VOL_MEAN5 | STATE | 0.8423 | 0.9229 | 0.8094 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H2\|LAG1_10 | MEMORY | 0.8421 | 0.9972 | 0.8627 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.125\|H1\|HG15 | HG | 0.842 | 0.9046 | 0.5045 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H1\|VOL_HI15 | STATE | 0.8402 | 0.871 | 0.7432 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.25\|H1\|INV10 | MEMORY | 0.8382 | 0.8103 | 0.8014 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H1\|VOL_HI15 | STATE | 0.8356 | 1.003 | 0.7804 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H2\|VOL_MEAN15 | STATE | 0.8341 | 0.765 | 0.8547 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.833 | 0.9389 | 0.3996 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|VOL_MEAN5 | STATE | 0.8328 | 0.9292 | 0.6464 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H1\|INV10 | MEMORY | 0.8313 | 0.8359 | 0.8401 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2\|a0.125\|H1\|HG15 | HG | 0.8309 | 0.9293 | 0.6653 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2\|a0.25\|H1\|HG5 | HG | 0.8293 | 0.9266 | 0.4308 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.125\|H1\|HG5 | HG | 0.8288 | 0.8507 | 0.8285 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H1\|VOL_MEAN15 | STATE | 0.8286 | 0.8913 | 0.6705 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.25\|H1\|LAG1_10 | MEMORY | 0.8256 | 0.8587 | 0.7939 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H1\|HG10 | HG | 0.8246 | 0.8019 | 0.8123 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H1\|INV10 | MEMORY | 0.8223 | 0.8615 | 0.5512 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.125\|H1\|LAG1_10 | MEMORY | 0.8207 | 0.5581 | 0.8122 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H2\|DECAY2_10 | MEMORY | 0.82 | 0.8229 | 0.8428 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.8178 | 0.7608 | 0.8023 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H1\|INV10 | MEMORY | 0.8141 | 0.6722 | 0.8146 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_mean3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 0.8133 | 0.7271 | 0.7855 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H2\|HG10 | HG | 0.8123 | 0.8444 | 0.8271 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H1\|VOL_MEAN5 | STATE | 0.8098 | 0.9306 | 0.5565 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2\|a0.125\|H1\|HG5 | HG | 0.8086 | 0.9494 | 0.8172 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.25\|H1\|LAG1_10 | MEMORY | 0.8072 | 0.8974 | 0.4327 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.806 | 0.7388 | 0.8057 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2\|a0.125\|H1\|HG15 | HG | 0.8058 | 0.8682 | 0.5192 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.5\|H2\|HG10 | HG | 0.8054 | 1.108 | 0.3207 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H2\|HG30 | HG | 0.8048 | 0.8818 | 0.1631 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H1\|LAG1_10 | MEMORY | 0.8042 | 0.8637 | 0.7046 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.8042 | 0.6149 | 0.8007 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.8037 | 0.9227 | 0.6097 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_mean3_v2\|a0.125\|H1\|HG5 | HG | 0.8015 | 0.8594 | 0.808 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.25\|H1\|VOL_HI15 | STATE | 0.8012 | 0.7674 | 0.7886 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H1\|VOL_MEAN15 | STATE | 0.8002 | 0.8339 | 0.8159 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.125\|H1\|HG10 | HG | 0.8001 | 0.8679 | 0.6234 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.8 | 0.8333 | 0.5659 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.125\|H1\|HG15 | HG | 0.7999 | 0.8348 | 0.4971 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.7968 | 0.6329 | 0.7686 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H1\|HG5 | HG | 0.7963 | 0.9667 | 0.4955 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.7962 | 0.9614 | 0.2976 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.25\|H1\|HG5 | HG | 0.7958 | 0.8052 | 0.3277 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.125\|H1\|HG10 | HG | 0.7957 | 0.8857 | 0.5615 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2\|a0.125\|H1\|HG5 | HG | 0.7898 | 0.7913 | 0.7964 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.7895 | 0.7655 | 0.7651 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H1\|NATIVE | SMOOTH | 0.7894 | 0.8163 | 0.7913 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.125\|H1\|INV10 | MEMORY | 0.7878 | 0.7289 | 0.8084 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|VOL_HI5 | STATE | 0.7861 | 0.8927 | 0.6053 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H2\|VOL_HI15 | STATE | 0.7849 | 0.9203 | 0.7454 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.125\|H1\|HG10 | HG | 0.7839 | 0.7721 | 0.5319 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H1\|NATIVE | SMOOTH | 0.7838 | 0.5488 | 0.7846 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2_CVRv5\|a0.125\|H1\|HG15 | HG | 0.7834 | 0.7542 | 0.5066 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_union3_v2\|a0.5\|H10\|HG10 | HG | 0.7826 | 0.6732 | 0.6812 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.781 | 0.8911 | 0.5951 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 0.7808 | 0.9384 | 0.3319 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H2\|HG30 | HG | 0.7799 | 0.9552 | 0.1887 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.7795 | 0.7421 | 0.7557 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H1\|VOL_HI5 | STATE | 0.7787 | 0.7799 | 0.7038 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H1\|HG10 | HG | 0.778 | 0.6377 | 0.7753 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.7762 | 0.8603 | 0.585 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H2\|HG20 | HG | 0.776 | 0.8806 | 0.362 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H1\|INV10 | MEMORY | 0.7744 | 0.98 | 0.3709 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_mean3_v2\|a0.5\|H1\|NATIVE | SMOOTH | 0.7718 | 0.5358 | 0.7832 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H1\|NATIVE | SMOOTH | 0.7707 | 0.6289 | 0.7548 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.7694 | 0.8334 | 0.5246 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H1\|VOL_HI15 | STATE | 0.769 | 0.8381 | 0.6492 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|A4b\|a0.125\|H1\|HG10 | HG | 0.7681 | 0.608 | 0.7482 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.7675 | 0.7547 | 0.7437 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H1\|NATIVE | SMOOTH | 0.7657 | 0.6385 | 0.7639 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H1\|HG10 | HG | 0.7629 | 0.8061 | 0.5087 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.7626 | 0.6166 | 0.7625 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H2\|VOL_MEAN5 | STATE | 0.7619 | 0.8293 | 0.7747 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.125\|H1\|HG5 | HG | 0.7616 | 0.8472 | 0.7656 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.761 | 0.7423 | 0.7529 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.125\|H1\|HG5 | HG | 0.7608 | 0.8172 | 0.7653 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2_CVRv5\|a0.125\|H1\|HG15 | HG | 0.7595 | 0.851 | 0.58 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_union3_v2\|a0.5\|H5\|HG10 | HG | 0.7592 | 0.6781 | 0.6459 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|A4b\|a0.25\|H1\|HG5 | HG | 0.7582 | 0.4868 | 0.7671 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.25\|H2\|HG15 | HG | 0.7556 | 0.5963 | 0.7602 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2\|a0.125\|H1\|HG10 | HG | 0.7553 | 0.8269 | 0.5018 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.25\|H1\|HG5 | HG | 0.7549 | 0.4477 | 0.7316 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H1\|VOL_HI5 | STATE | 0.754 | 0.8558 | 0.5139 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.7535 | 0.5764 | 0.7493 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H3\|DECAY5_10 | MEMORY | 0.7514 | 0.803 | 0.759 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_mean3_v2\|a0.25\|H1\|NATIVE | SMOOTH | 0.7511 | 0.6192 | 0.7549 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H1\|NATIVE | SMOOTH | 0.7508 | 0.588 | 0.7508 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.7499 | 0.8229 | 0.5051 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H1\|VOL_HI15 | STATE | 0.7484 | 0.7333 | 0.7321 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H1\|VOL_MEAN15 | STATE | 0.7482 | 0.7471 | 0.736 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 0.7479 | 0.7832 | 0.4079 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.7472 | 0.7688 | 0.7258 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H2\|HG15 | HG | 0.7471 | 0.8235 | 0.7785 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H2\|HG15 | HG | 0.7453 | 0.7105 | 0.7586 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H1\|INV10 | MEMORY | 0.7424 | 0.6208 | 0.7032 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.7418 | 0.8272 | 0.562 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H1\|VOL_MEAN15 | STATE | 0.7398 | 0.6886 | 0.6414 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.125\|H1\|HG5 | HG | 0.7393 | 0.6849 | 0.7281 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.125\|H1\|VOL_HI5 | STATE | 0.7386 | 0.7784 | 0.7151 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H2\|VOL_HI5 | STATE | 0.7383 | 0.7649 | 0.7498 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H3\|VOL_MEAN15 | STATE | 0.7372 | 0.7034 | 0.7473 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|VOL_MEAN15 | STATE | 0.7364 | 0.8089 | 0.5567 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b_CVRv5\|a0.125\|H1\|HG10 | HG | 0.7359 | 0.7577 | 0.7165 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H2\|HG15 | HG | 0.7355 | 0.6767 | 0.7408 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2_CVRv5\|a0.125\|H1\|HG15 | HG | 0.7346 | 0.7756 | 0.4006 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H1\|VOL_HI15 | STATE | 0.7344 | 0.8796 | 0.5801 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H2\|VOL_MEAN5 | STATE | 0.7318 | 0.7914 | 0.6864 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2_CVRv5\|a0.5\|H2\|HG10 | HG | 0.7259 | 1.006 | 0.2196 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H1\|VOL_HI15 | STATE | 0.7246 | 0.7123 | 0.7193 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.125\|H1\|LAG1_10 | MEMORY | 0.7229 | 0.6855 | 0.6989 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H2\|HG15 | HG | 0.7219 | 0.6673 | 0.7005 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H2\|HG20 | HG | 0.7186 | 0.8406 | 0.1155 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|A4b\|a0.25\|H2\|HG10 | HG | 0.7174 | 0.7455 | 0.7428 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H2\|DECAY2_10 | MEMORY | 0.7163 | 0.8458 | 0.6793 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|HG30 | HG | 0.713 | 0.8687 | 0.2901 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H1\|VOL_HI15 | STATE | 0.7129 | 0.7279 | 0.7253 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H1\|LAG1_10 | MEMORY | 0.7117 | 0.7275 | 0.5548 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.125\|H1\|INV10 | MEMORY | 0.7112 | 0.7405 | 0.6809 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H2\|VOL_HI5 | STATE | 0.7099 | 0.7591 | 0.6704 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H3\|LAG1_10 | MEMORY | 0.7095 | 0.8319 | 0.72 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H2\|HG10 | HG | 0.7085 | 0.5841 | 0.7228 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.7085 | 0.7656 | 0.4412 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H2\|DECAY2_10 | MEMORY | 0.7074 | 0.6974 | 0.7195 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG10 | HG | 0.7071 | 0.7365 | 0.4292 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H1\|VOL_MEAN5 | STATE | 0.7069 | 0.7935 | 0.4176 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H2\|HG15 | HG | 0.7057 | 0.8006 | 0.7089 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H2\|VOL_MEAN5 | STATE | 0.7047 | 0.6293 | 0.7009 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H2\|LAG1_10 | MEMORY | 0.7032 | 0.6899 | 0.6698 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.125\|H1\|HG10 | HG | 0.7027 | 0.773 | 0.702 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.25\|H1\|NATIVE | SMOOTH | 0.7015 | 0.5103 | 0.6867 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b\|a0.125\|H1\|HG10 | HG | 0.7014 | 0.669 | 0.6904 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 0.7004 | 0.811 | 0.1783 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H2\|VOL_HI15 | STATE | 0.7003 | 0.5912 | 0.7144 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2_CVRv5\|a0.25\|H2\|HG10 | HG | 0.7003 | 0.883 | 0.1015 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.6981 | 0.7441 | 0.4859 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H2\|VOL_MEAN15 | STATE | 0.6956 | 0.6623 | 0.6734 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H3\|VOL_HI5 | STATE | 0.6955 | 0.691 | 0.6984 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H1\|HG5 | HG | 0.6953 | 0.7348 | 0.6219 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H2\|INV10 | MEMORY | 0.6923 | 0.5029 | 0.03262 | 通过 | 不通过（e资本） | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H3\|DECAY2_10 | MEMORY | 0.6917 | 0.74 | 0.706 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H3\|HG30 | HG | 0.69 | 0.6784 | 0.2412 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.6896 | 0.7857 | 0.4036 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H2\|LAG1_10 | MEMORY | 0.6887 | 0.7541 | 0.6771 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H2\|HG5 | HG | 0.6879 | 0.4866 | 0.7084 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.6876 | 0.7187 | 0.6679 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b\|a0.125\|H1\|HG10 | HG | 0.6865 | 0.6161 | 0.6805 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2\|a0.125\|H1\|HG10 | HG | 0.6856 | 0.667 | 0.4801 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.6841 | 0.7982 | 0.4082 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H10\|VOL_HI5 | STATE | 0.6827 | 0.907 | 0.1026 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.125\|H1\|NATIVE | SMOOTH | 0.6811 | 0.6307 | 0.6889 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.125\|H1\|HG5 | HG | 0.6795 | 0.6292 | 0.6887 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H2\|HG30 | HG | 0.6779 | 0.8609 | 0.6548 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.6765 | 0.7856 | 0.4068 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H2\|DECAY2_10 | MEMORY | 0.6763 | 0.6738 | 0.688 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H10\|HG30 | HG | 0.6752 | 0.7636 | 0.3372 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H2\|HG20 | HG | 0.6752 | 0.8273 | 0.1121 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.125\|H1\|HG10 | HG | 0.6748 | 0.6696 | 0.5897 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H2\|INV10 | MEMORY | 0.6729 | 0.5281 | 0.6183 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H2\|INV10 | MEMORY | 0.6721 | 0.7422 | -0.04238 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H1\|HG5 | HG | 0.672 | 0.4857 | 0.6652 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2\|a0.25\|H1\|HG5 | HG | 0.672 | 0.8419 | 0.454 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H1\|NATIVE | SMOOTH | 0.6699 | 0.5976 | 0.6786 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b_CVRv5\|a0.125\|H1\|HG10 | HG | 0.6696 | 0.6719 | 0.6511 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H2\|INV10 | MEMORY | 0.6696 | 0.3806 | 0.6861 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.6692 | 0.6322 | 0.6478 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H2\|INV10 | MEMORY | 0.6677 | 0.7205 | 0.2573 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.6675 | 0.7532 | 0.3979 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H1\|VOL_HI5 | STATE | 0.6665 | 0.7994 | 0.3887 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H2\|HG10 | HG | 0.6664 | 0.7315 | 0.3378 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H1\|LAG1_10 | MEMORY | 0.666 | 0.7803 | 0.4321 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H2\|INV10 | MEMORY | 0.6652 | 0.415 | 0.6912 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H2\|HG10 | HG | 0.6646 | 0.6377 | 0.6701 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_mean3_v2\|a0.125\|H1\|HG5 | HG | 0.6645 | 0.7869 | 0.6663 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.6622 | 0.7073 | 0.3687 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b\|a0.5\|H2\|NATIVE | SMOOTH | 0.6613 | 0.5359 | 0.6741 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H2\|HG15 | HG | 0.661 | 0.5589 | 0.6475 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2\|a0.25\|H2\|HG10 | HG | 0.6606 | 0.7244 | 0.2987 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H2\|DECAY5_10 | MEMORY | 0.6605 | 0.6901 | 0.6397 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2\|a0.25\|H2\|HG10 | HG | 0.6578 | 0.7323 | 0.1043 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.6577 | 0.6387 | 0.637 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H3\|HG20 | HG | 0.6574 | 0.6572 | 0.2077 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 0.6564 | 0.818 | 0.3323 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H2\|INV10 | MEMORY | 0.6556 | 0.4169 | 0.6757 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|VOL_HI15 | STATE | 0.6546 | 0.8386 | 0.4744 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.6536 | 0.6794 | 0.4907 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2_CVRv5\|a0.25\|H2\|HG10 | HG | 0.6533 | 0.7538 | 0.2503 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H1\|HG10 | HG | 0.6526 | 0.6179 | 0.5966 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H2\|INV10 | MEMORY | 0.6521 | 0.4139 | 0.04854 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|A4b\|a0.25\|H1\|NATIVE | SMOOTH | 0.6506 | 0.2639 | 0.6599 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H2\|VOL_MEAN5 | STATE | 0.6494 | 0.6833 | 0.332 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2\|a0.25\|H2\|HG10 | HG | 0.6493 | 0.521 | 0.6495 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H2\|HG15 | HG | 0.649 | 0.6353 | 0.6552 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H2\|VOL_MEAN15 | STATE | 0.6485 | 0.7711 | 0.2656 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H1\|VOL_HI15 | STATE | 0.6475 | 0.7218 | 0.4271 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H3\|HG30 | HG | 0.6458 | 0.7674 | 0.6262 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.25\|H2\|HG10 | HG | 0.6458 | 0.5133 | 0.6485 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H2\|HG10 | HG | 0.6451 | 0.7622 | 0.2885 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H2\|VOL_MEAN5 | STATE | 0.6444 | 0.7435 | 0.2967 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|LAG1_10 | MEMORY | 0.6443 | 0.712 | 0.4702 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.6442 | 0.6437 | 0.6342 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.125\|H1\|HG5 | HG | 0.6434 | 0.7164 | 0.4201 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2_CVRv5\|a0.5\|H20\|HG10 | HG | 0.6424 | 0.824 | 0.1381 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H2\|LAG1_10 | MEMORY | 0.6423 | 0.6525 | 0.6484 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H2\|VOL_MEAN15 | STATE | 0.642 | 0.7149 | 0.2895 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H1\|VOL_HI15 | STATE | 0.6413 | 0.6807 | 0.3863 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H10\|HG30 | HG | 0.6409 | 0.6735 | 0.2826 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.25\|H2\|HG15 | HG | 0.6408 | 0.6375 | 0.2057 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H2\|INV10 | MEMORY | 0.6405 | 0.5719 | -0.02563 | 不通过（e资本） | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.5\|H10\|HG10 | HG | 0.6401 | 0.7888 | 0.06328 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H5\|HG20 | HG | 0.6365 | 0.5784 | 0.6034 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.6365 | 0.663 | 0.4736 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.25\|H2\|HG15 | HG | 0.6362 | 0.7198 | 0.2527 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H2\|HG10 | HG | 0.6356 | 0.624 | 0.6537 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H1\|HG10 | HG | 0.6352 | 0.6538 | 0.4649 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H2\|HG10 | HG | 0.6349 | 0.6481 | 0.6473 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H1\|HG5 | HG | 0.634 | 0.4335 | 0.6245 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H2\|DECAY5_10 | MEMORY | 0.6332 | 0.6591 | 0.6445 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H1\|HG5 | HG | 0.6323 | 0.5181 | 0.6371 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H1\|VOL_HI5 | STATE | 0.6313 | 0.6063 | 0.5537 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_mean3_v2\|a0.125\|H1\|NATIVE | SMOOTH | 0.6302 | 0.5996 | 0.64 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.6282 | 0.5978 | 0.62 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H1\|HG5 | HG | 0.6281 | 0.4581 | 0.6125 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H2\|VOL_HI5 | STATE | 0.6274 | 0.7763 | 0.6252 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H3\|VOL_HI15 | STATE | 0.6266 | 0.5241 | 0.6344 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H2\|DECAY5_10 | MEMORY | 0.6265 | 0.6175 | 0.6395 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H2\|VOL_HI15 | STATE | 0.6256 | 0.7862 | 0.2232 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.125\|H1\|NATIVE | SMOOTH | 0.6236 | 0.5171 | 0.6342 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2\|a0.5\|H20\|HG10 | HG | 0.6231 | 0.8264 | 0.1843 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.623 | 0.6807 | 0.3798 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H2\|HG20 | HG | 0.6224 | 0.6124 | 0.6385 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H1\|LAG1_10 | MEMORY | 0.6214 | 0.6446 | 0.457 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2_CVRv5\|a0.25\|H2\|HG15 | HG | 0.6213 | 0.6774 | -0.006257 | 不通过（e资本） | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H3\|VOL_MEAN5 | STATE | 0.6206 | 0.6717 | 0.6274 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H2\|INV10 | MEMORY | 0.6204 | 0.59 | 0.6375 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.125\|H1\|LAG1_10 | MEMORY | 0.6202 | 0.6072 | 0.603 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H3\|HG10 | HG | 0.6186 | 0.5421 | 0.6265 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H2\|DECAY2_10 | MEMORY | 0.6185 | 0.5822 | 0.6091 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H2\|HG15 | HG | 0.6183 | 0.6436 | 0.2209 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b\|a0.25\|H2\|HG10 | HG | 0.614 | 0.399 | 0.6316 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2_CVRv5\|a0.25\|H1\|NATIVE | SMOOTH | 0.614 | 0.5517 | 0.5971 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b_CVRv5\|a0.5\|H2\|NATIVE | SMOOTH | 0.6136 | 0.6547 | 0.6123 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H3\|VOL_MEAN15 | STATE | 0.6129 | 0.6691 | 0.5889 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2\|a0.125\|H1\|NATIVE | SMOOTH | 0.6091 | 0.5432 | 0.6135 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.125\|H1\|HG5 | HG | 0.6074 | 0.3471 | 0.5898 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H3\|HG15 | HG | 0.6071 | 0.5394 | 0.6162 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H2\|DECAY5_10 | MEMORY | 0.6071 | 0.6482 | 0.2772 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H3\|HG15 | HG | 0.6069 | 0.708 | 0.6297 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.6054 | 0.6133 | 0.5898 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b_CVRv5\|a0.25\|H1\|NATIVE | SMOOTH | 0.6042 | 0.2806 | 0.6048 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.125\|H1\|HG5 | HG | 0.6036 | 0.5313 | 0.3964 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b\|a0.125\|H1\|HG5 | HG | 0.6026 | 0.4674 | 0.6005 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.25\|H2\|HG15 | HG | 0.6023 | 0.7484 | -0.0137 | 不通过（e资本） | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.6018 | 0.5929 | 0.547 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H3\|HG15 | HG | 0.6016 | 0.6104 | 0.5978 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H2\|LAG1_10 | MEMORY | 0.6015 | 0.6167 | 0.6132 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.125\|H1\|HG5 | HG | 0.6014 | 0.6901 | 0.4558 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H2\|HG15 | HG | 0.6013 | 0.7215 | 0.2307 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H5\|HG15 | HG | 0.6008 | 0.5727 | 0.5658 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H2\|VOL_HI15 | STATE | 0.5995 | 0.7269 | 0.2324 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2\|a0.25\|H2\|HG15 | HG | 0.5988 | 0.5641 | 0.01547 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H3\|DECAY5_10 | MEMORY | 0.5973 | 0.647 | 0.5777 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H1\|VOL_HI15 | STATE | 0.5961 | 0.5484 | 0.5603 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H2\|HG15 | HG | 0.5936 | 0.7339 | 0.06584 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.25\|H2\|INV10 | MEMORY | 0.5921 | 0.7774 | 0.01429 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H3\|HG20 | HG | 0.5915 | 0.5186 | 0.5441 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H3\|HG20 | HG | 0.5904 | 0.5026 | 0.1845 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.5893 | 0.6845 | 0.3296 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H2\|VOL_MEAN5 | STATE | 0.5892 | 0.685 | 0.06311 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H2\|HG20 | HG | 0.588 | 0.6578 | 0.4207 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H3\|HG30 | HG | 0.5871 | 0.6409 | 0.602 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.25\|H2\|HG10 | HG | 0.5861 | 0.7835 | 0.2211 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H1\|LAG1_10 | MEMORY | 0.5858 | 0.7039 | 0.32 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.5838 | 0.6502 | 0.5622 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_union3_v2\|a0.125\|H1\|HG10 | HG | 0.5826 | 0.5818 | 0.4701 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H2\|HG15 | HG | 0.5825 | 0.5439 | 0.2331 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H5\|HG10 | HG | 0.5823 | 0.5434 | 0.5496 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.5822 | 0.6392 | 0.4752 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.25\|H2\|HG10 | HG | 0.5812 | 0.7163 | 0.1714 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H5\|VOL_HI5 | STATE | 0.5807 | 0.5053 | 0.5801 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H2\|DECAY2_10 | MEMORY | 0.5793 | 0.6322 | 0.257 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H2\|HG20 | HG | 0.5791 | 0.6027 | 0.4305 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|HG20 | HG | 0.5791 | 0.7276 | 0.1799 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H10\|HG20 | HG | 0.5787 | 0.6567 | 0.5327 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H10\|HG30 | HG | 0.5786 | 0.6399 | 0.5295 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H5\|VOL_HI15 | STATE | 0.5782 | 0.5493 | 0.5438 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H2\|NATIVE | SMOOTH | 0.5772 | 0.4998 | 0.5969 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b\|a0.25\|H2\|HG10 | HG | 0.5764 | 0.4039 | 0.5971 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.25\|H2\|HG15 | HG | 0.5761 | 0.6104 | -0.007407 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H3\|LAG1_10 | MEMORY | 0.5753 | 0.591 | 0.5591 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.25\|H2\|HG15 | HG | 0.5752 | 0.6524 | 0.1822 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H2\|HG5 | HG | 0.574 | 0.5595 | 0.5939 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H2\|VOL_HI5 | STATE | 0.5739 | 0.3853 | 0.5889 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H2\|INV10 | MEMORY | 0.5727 | 0.3196 | 0.5523 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H2\|HG20 | HG | 0.5713 | 0.6732 | 0.4242 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H2\|INV10 | MEMORY | 0.5712 | 0.439 | 0.1849 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b_CVRv5\|a0.125\|H1\|HG5 | HG | 0.5708 | 0.413 | 0.5689 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H2\|VOL_MEAN5 | STATE | 0.5695 | 0.5644 | 0.5479 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_mean3_v2_CVRv5\|a0.25\|H1\|NATIVE | SMOOTH | 0.5694 | 0.4397 | 0.5482 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H5\|VOL_MEAN15 | STATE | 0.5686 | 0.5413 | 0.536 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H2\|HG5 | HG | 0.5685 | 0.5536 | 0.5956 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H2\|INV10 | MEMORY | 0.5682 | 0.7361 | 0.01584 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H2\|VOL_MEAN5 | STATE | 0.5672 | 0.5375 | 0.09263 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_mean3_v2\|a0.25\|H2\|HG15 | HG | 0.5647 | 0.2951 | 0.5821 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H5\|VOL_MEAN15 | STATE | 0.5638 | 0.5183 | 0.5721 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_union3_v2\|a0.125\|H1\|HG10 | HG | 0.5625 | 0.6038 | 0.3788 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H3\|INV10 | MEMORY | 0.5591 | 0.2881 | 0.5612 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H2\|VOL_MEAN5 | STATE | 0.5583 | 0.5719 | 0.5614 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H2\|VOL_HI5 | STATE | 0.5582 | 0.5485 | 0.2501 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H3\|DECAY2_10 | MEMORY | 0.558 | 0.5175 | 0.563 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H2\|VOL_HI5 | STATE | 0.5577 | 0.6918 | 0.4151 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H1\|DECAY2_10 | MEMORY | 0.5577 | 0.574 | 0.3792 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.25\|H2\|HG15 | HG | 0.5554 | 0.4027 | 0.5656 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H3\|INV10 | MEMORY | 0.555 | 0.3633 | 0.5695 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H1\|VOL_MEAN15 | STATE | 0.5534 | 0.569 | 0.4926 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.25\|H2\|HG15 | HG | 0.553 | 0.5932 | 0.06445 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 0.5528 | 0.744 | 0.3147 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H3\|HG10 | HG | 0.5523 | 0.5299 | 0.5591 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.5521 | 0.5679 | 0.3659 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.5519 | 0.532 | 0.3131 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_union3_v2\|a0.5\|H20\|HG10 | HG | 0.5516 | 0.4674 | 0.5177 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H2\|VOL_HI5 | STATE | 0.5507 | 0.5822 | 0.2007 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H1\|VOL_MEAN15 | STATE | 0.5506 | 0.6132 | 0.3077 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H20\|HG30 | HG | 0.5495 | 0.6074 | 0.2907 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2_CVRv5\|a0.25\|H1\|HG5 | HG | 0.5492 | 0.7572 | 0.2161 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.25\|H2\|HG10 | HG | 0.5488 | 0.6464 | -0.01535 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H2\|HG5 | HG | 0.5485 | 0.5432 | 0.5588 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H5\|HG20 | HG | 0.5468 | 0.6716 | 0.1666 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H2\|VOL_HI15 | STATE | 0.5463 | 0.4887 | 0.5206 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H3\|HG5 | HG | 0.5452 | 0.49 | 0.553 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H1\|LAG1_10 | MEMORY | 0.5449 | 0.5522 | 0.3584 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2\|a0.25\|H2\|HG10 | HG | 0.5444 | 0.4973 | 0.5321 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H2\|HG15 | HG | 0.5436 | 0.4367 | 0.554 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H1\|DECAY5_10 | MEMORY | 0.5421 | 0.564 | 0.3643 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H1\|VOL_HI15 | STATE | 0.5412 | 0.5375 | 0.4987 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2\|a0.125\|H1\|HG5 | HG | 0.541 | 0.5701 | 0.3074 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H10\|HG20 | HG | 0.5385 | 0.6023 | 0.2119 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H2\|HG10 | HG | 0.5369 | 0.4646 | 0.5621 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H3\|HG10 | HG | 0.5362 | 0.5825 | 0.5335 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H20\|HG30 | HG | 0.5358 | 0.6175 | 0.2581 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H2\|HG5 | HG | 0.5344 | 0.758 | 0.2181 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H3\|DECAY2_10 | MEMORY | 0.5343 | 0.6058 | 0.5226 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H1\|HG5 | HG | 0.5335 | 0.6252 | 0.3292 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H2\|HG30 | HG | 0.5334 | 0.5783 | 0.522 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H2\|DECAY5_10 | MEMORY | 0.5332 | 0.5953 | 0.4995 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|VOL_MEAN15 | STATE | 0.5322 | 0.6593 | 0.1982 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H2\|VOL_HI5 | STATE | 0.5321 | 0.5202 | 0.5434 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H5\|DECAY5_10 | MEMORY | 0.532 | 0.4745 | 0.5378 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|A4b\|a0.25\|H3\|HG10 | HG | 0.5317 | 0.3974 | 0.5431 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H3\|DECAY5_10 | MEMORY | 0.5312 | 0.5135 | 0.5349 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H2\|VOL_MEAN5 | STATE | 0.5289 | 0.5957 | 0.3924 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b\|a0.5\|H3\|NATIVE | SMOOTH | 0.5281 | 0.5023 | 0.5335 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H3\|HG15 | HG | 0.528 | 0.4633 | 0.5101 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H2\|HG10 | HG | 0.5269 | 0.5291 | 0.5372 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H10\|HG30 | HG | 0.5261 | 0.5562 | 0.4962 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H2\|DECAY2_10 | MEMORY | 0.5259 | 0.6237 | 0.396 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H3\|VOL_MEAN15 | STATE | 0.5251 | 0.4767 | 0.1644 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H5\|HG20 | HG | 0.5225 | 0.4648 | 0.4766 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H5\|VOL_HI5 | STATE | 0.5219 | 0.5531 | 0.4944 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H2\|LAG1_10 | MEMORY | 0.5212 | 0.4729 | 0.5155 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.25\|H3\|HG10 | HG | 0.5198 | 0.3695 | 0.5301 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H5\|DECAY5_10 | MEMORY | 0.519 | 0.5289 | 0.4907 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H3\|HG15 | HG | 0.5172 | 0.4628 | 0.4959 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.5169 | 0.4084 | 0.5117 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.5169 | 0.5516 | 0.3473 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.5161 | 0.5951 | 0.2448 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H3\|VOL_MEAN5 | STATE | 0.5157 | 0.4995 | 0.1793 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|A4b\|a0.125\|H2\|HG10 | HG | 0.5156 | 0.4682 | 0.5307 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H2\|HG5 | HG | 0.5154 | 0.5549 | 0.5179 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b_CVRv5\|a0.25\|H2\|HG10 | HG | 0.5153 | 0.3938 | 0.5402 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H5\|LAG1_10 | MEMORY | 0.5151 | 0.5048 | 0.4833 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H5\|VOL_MEAN15 | STATE | 0.5149 | 0.586 | 0.189 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H2\|DECAY2_10 | MEMORY | 0.5138 | 0.6192 | 0.4802 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_union3_v2\|a0.25\|H2\|HG10 | HG | 0.5135 | 0.6433 | 0.356 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H2\|DECAY2_10 | MEMORY | 0.5135 | 0.6456 | 0.1776 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H10\|VOL_MEAN15 | STATE | 0.5134 | 0.5891 | 0.4704 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H1\|HG5 | HG | 0.513 | 0.5614 | 0.3891 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H2\|VOL_HI5 | STATE | 0.5127 | 0.5027 | 0.4938 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H5\|VOL_HI5 | STATE | 0.5124 | 0.5217 | 0.4835 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H2\|LAG1_10 | MEMORY | 0.5123 | 0.5497 | 0.203 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.5115 | 0.5592 | 0.506 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H3\|VOL_MEAN5 | STATE | 0.51 | 0.4754 | 0.1883 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H5\|HG5 | HG | 0.5099 | 0.4541 | 0.4822 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H10\|HG20 | HG | 0.5093 | 0.5459 | 0.4812 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H3\|HG20 | HG | 0.5091 | 0.5528 | 0.5124 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H2\|HG5 | HG | 0.5091 | 0.4585 | 0.5172 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H2\|HG20 | HG | 0.5085 | 0.6321 | 0.4795 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H2\|DECAY5_10 | MEMORY | 0.5085 | 0.4927 | 0.5069 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H5\|DECAY2_10 | MEMORY | 0.508 | 0.5803 | 0.4687 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H2\|DECAY2_10 | MEMORY | 0.508 | 0.6958 | 0.01247 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H2\|HG5 | HG | 0.5077 | 0.5104 | 0.5223 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H5\|VOL_HI15 | STATE | 0.5062 | 0.5497 | 0.4627 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.25\|H2\|VOL_HI15 | STATE | 0.5062 | 0.3103 | 0.5209 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H10\|HG10 | HG | 0.5055 | 0.5655 | 0.4641 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b\|a0.25\|H3\|HG10 | HG | 0.5049 | 0.3024 | 0.5154 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.125\|H3\|HG30 | HG | 0.5048 | 0.6044 | 0.5108 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H2\|HG20 | HG | 0.5047 | 0.4988 | 0.2731 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H5\|VOL_MEAN15 | STATE | 0.5046 | 0.6553 | 0.4593 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H5\|HG30 | HG | 0.5043 | 0.403 | 0.4461 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H2\|DECAY2_10 | MEMORY | 0.5034 | 0.4662 | 0.516 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b\|a0.25\|H3\|HG15 | HG | 0.5033 | 0.2637 | 0.5132 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H2\|LAG1_10 | MEMORY | 0.5027 | 0.5392 | 0.507 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b\|a0.125\|H2\|HG10 | HG | 0.5022 | 0.292 | 0.5137 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H2\|DECAY5_10 | MEMORY | 0.5008 | 0.6289 | 0.001877 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_union3_v2_CVRv5\|a0.125\|H1\|HG10 | HG | 0.5002 | 0.5664 | 0.2939 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H3\|VOL_MEAN15 | STATE | 0.5001 | 0.4463 | 0.1568 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H2\|VOL_MEAN15 | STATE | 0.5 | 0.6214 | 0.3772 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H2\|DECAY5_10 | MEMORY | 0.4991 | 0.615 | 0.3751 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.125\|H2\|HG15 | HG | 0.499 | 0.56 | 0.514 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H10\|INV10 | MEMORY | 0.4988 | 0.4193 | 0.4824 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.4973 | 0.6324 | 0.2606 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H2\|HG20 | HG | 0.4971 | 0.6069 | 0.336 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H2\|INV10 | MEMORY | 0.4967 | 0.5288 | 0.1429 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H10\|HG15 | HG | 0.4967 | 0.5731 | 0.4931 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H2\|HG5 | HG | 0.4966 | 0.491 | 0.504 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H3\|DECAY5_10 | MEMORY | 0.4965 | 0.4667 | 0.1509 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H2\|DECAY5_10 | MEMORY | 0.4958 | 0.6194 | 0.1542 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H10\|HG15 | HG | 0.4949 | 0.5569 | 0.4511 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H2\|VOL_HI15 | STATE | 0.4947 | 0.4855 | 0.4859 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H3\|VOL_HI15 | STATE | 0.4944 | 0.4477 | 0.4658 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.25\|H2\|HG10 | HG | 0.4942 | 0.5114 | 0.2747 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H3\|DECAY5_10 | MEMORY | 0.494 | 0.4463 | 0.1646 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H2\|HG10 | HG | 0.4939 | 0.4385 | 0.4956 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H2\|LAG1_10 | MEMORY | 0.4938 | 0.6085 | 0.3677 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H5\|HG10 | HG | 0.4937 | 0.4744 | 0.4953 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.25\|H2\|HG10 | HG | 0.4927 | 0.5863 | -0.0061 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H5\|HG10 | HG | 0.4921 | 0.4424 | 0.4691 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H2\|HG20 | HG | 0.4918 | 0.4808 | 0.2727 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H10\|DECAY2_10 | MEMORY | 0.4915 | 0.5988 | 0.4489 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H1\|HG5 | HG | 0.4911 | 0.6064 | 0.3474 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H10\|VOL_HI15 | STATE | 0.4905 | 0.4822 | 0.4466 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.125\|H2\|HG15 | HG | 0.4902 | 0.5617 | 0.2503 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H2\|INV10 | MEMORY | 0.4902 | 0.5489 | 0.1642 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_mean3_v2\|a0.125\|H1\|NATIVE | SMOOTH | 0.4894 | 0.41 | 0.5121 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H5\|LAG1_10 | MEMORY | 0.4889 | 0.4365 | 0.4945 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H2\|HG15 | HG | 0.4874 | 0.4325 | 0.2863 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H5\|DECAY5_10 | MEMORY | 0.4871 | 0.5493 | 0.4484 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H2\|VOL_HI5 | STATE | 0.4865 | 0.5428 | 0.3908 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H2\|LAG1_10 | MEMORY | 0.4862 | 0.4943 | 0.462 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H2\|HG15 | HG | 0.4862 | 0.675 | 0.3146 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H2\|VOL_HI5 | STATE | 0.4861 | 0.2989 | 0.4814 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2\|a0.25\|H3\|HG10 | HG | 0.4859 | 0.2585 | 0.4966 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H2\|HG30 | HG | 0.4856 | 0.5003 | 0.337 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H5\|DECAY2_10 | MEMORY | 0.4855 | 0.444 | 0.4954 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H5\|VOL_MEAN5 | STATE | 0.4847 | 0.4199 | 0.4491 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H5\|HG15 | HG | 0.4847 | 0.4225 | 0.4581 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H3\|VOL_MEAN5 | STATE | 0.4845 | 0.5719 | 0.4623 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H3\|VOL_HI5 | STATE | 0.4836 | 0.576 | 0.4571 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.25\|H2\|HG10 | HG | 0.4836 | 0.336 | 0.4661 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H10\|HG15 | HG | 0.4828 | 0.5761 | 0.4606 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H5\|LAG1_10 | MEMORY | 0.4819 | 0.5085 | 0.4531 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H2\|VOL_MEAN5 | STATE | 0.4815 | 0.424 | 0.4969 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H2\|INV10 | MEMORY | 0.4814 | 0.5473 | 0.06652 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H10\|DECAY5_10 | MEMORY | 0.4802 | 0.585 | 0.4375 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H3\|LAG1_10 | MEMORY | 0.48 | 0.4339 | 0.4844 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H10\|HG10 | HG | 0.4797 | 0.4894 | 0.4804 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H1\|VOL_MEAN15 | STATE | 0.4789 | 0.4318 | 0.4202 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H3\|NATIVE | SMOOTH | 0.4789 | 0.4108 | 0.4872 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|VOL_HI15 | STATE | 0.478 | 0.6377 | 0.1241 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H10\|HG20 | HG | 0.4769 | 0.5128 | 0.141 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H2\|HG30 | HG | 0.4767 | 0.5039 | 0.07844 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H3\|HG15 | HG | 0.4767 | 0.4755 | 0.4789 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H2\|HG10 | HG | 0.4765 | 0.5501 | 0.4786 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H2\|INV10 | MEMORY | 0.4756 | 0.4954 | 0.08361 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H5\|DECAY2_10 | MEMORY | 0.4754 | 0.4574 | 0.4514 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b_CVRv5\|a0.125\|H2\|HG10 | HG | 0.4751 | 0.3009 | 0.4637 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H3\|VOL_HI15 | STATE | 0.4745 | 0.4733 | 0.09165 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H5\|VOL_MEAN5 | STATE | 0.4739 | 0.4221 | 0.4223 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H10\|VOL_HI5 | STATE | 0.4732 | 0.4986 | 0.4366 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H2\|HG10 | HG | 0.4721 | 0.6172 | 0.1356 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.25\|H2\|HG5 | HG | 0.4713 | 0.6039 | 0.1554 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|DECAY5_10 | MEMORY | 0.4706 | 0.555 | 0.1431 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H2\|HG20 | HG | 0.4705 | 0.5629 | 0.477 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.125\|H1\|HG5 | HG | 0.4697 | 0.5522 | 0.3364 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H3\|DECAY2_10 | MEMORY | 0.4697 | 0.4699 | 0.1317 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H3\|HG10 | HG | 0.4692 | 0.4734 | 0.482 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H3\|DECAY2_10 | MEMORY | 0.4689 | 0.4871 | 0.4803 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H5\|DECAY5_10 | MEMORY | 0.4686 | 0.4788 | 0.1498 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H2\|HG15 | HG | 0.4655 | 0.5085 | 0.2566 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H10\|LAG1_10 | MEMORY | 0.4655 | 0.5312 | 0.4254 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H3\|HG10 | HG | 0.4653 | 0.4757 | 0.473 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H10\|HG5 | HG | 0.465 | 0.5216 | 0.4288 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H2\|VOL_HI5 | STATE | 0.4649 | 0.541 | 0.4528 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H5\|LAG1_10 | MEMORY | 0.4644 | 0.5626 | 0.4254 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H5\|HG15 | HG | 0.4639 | 0.3994 | 0.4593 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H10\|DECAY5_10 | MEMORY | 0.4637 | 0.5465 | 0.469 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H3\|DECAY2_10 | MEMORY | 0.4634 | 0.4367 | 0.1441 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b\|a0.5\|H20\|HG10 | HG | 0.4628 | 0.3937 | 0.4604 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H2\|DECAY2_10 | MEMORY | 0.4623 | 0.5595 | 0.4636 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H10\|VOL_HI5 | STATE | 0.4618 | 0.5013 | 0.4604 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H2\|VOL_HI5 | STATE | 0.4617 | 0.6114 | 0.3191 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H2\|HG15 | HG | 0.4616 | 0.5422 | 0.4722 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H2\|HG30 | HG | 0.4614 | 0.4704 | 0.1686 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H5\|HG15 | HG | 0.4608 | 0.4322 | 0.4331 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H2\|DECAY2_10 | MEMORY | 0.4599 | 0.5366 | 0.4638 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b\|a0.25\|H3\|NATIVE | SMOOTH | 0.4598 | 0.3379 | 0.4516 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b_CVRv5\|a0.5\|H20\|HG10 | HG | 0.459 | 0.4442 | 0.4605 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H2\|INV10 | MEMORY | 0.4586 | 0.5122 | 0.4557 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H2\|DECAY5_10 | MEMORY | 0.4583 | 0.474 | 0.4702 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H3\|VOL_HI5 | STATE | 0.4583 | 0.5032 | 0.45 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.25\|H2\|DECAY2_10 | MEMORY | 0.4581 | 0.5333 | 0.1072 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H5\|DECAY2_10 | MEMORY | 0.4575 | 0.504 | 0.1479 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H2\|DECAY5_10 | MEMORY | 0.4573 | 0.5712 | 0.4586 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|DECAY2_10 | MEMORY | 0.457 | 0.5517 | 0.1373 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H3\|HG5 | HG | 0.4562 | 0.4744 | 0.4597 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H5\|VOL_MEAN5 | STATE | 0.4555 | 0.4178 | 0.4613 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H3\|DECAY5_10 | MEMORY | 0.4554 | 0.4686 | 0.4634 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H5\|HG10 | HG | 0.4536 | 0.4558 | 0.4411 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H10\|VOL_MEAN5 | STATE | 0.4522 | 0.4812 | 0.4072 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.4518 | 0.5532 | 0.2877 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H2\|HG15 | HG | 0.4511 | 0.5001 | 0.3364 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.125\|H2\|LAG1_10 | MEMORY | 0.4505 | 0.286 | 0.4557 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H3\|HG5 | HG | 0.45 | 0.3372 | 0.4512 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H1\|HG5 | HG | 0.4493 | 0.4248 | 0.4218 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H5\|VOL_MEAN5 | STATE | 0.4486 | 0.5426 | 0.136 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H5\|VOL_MEAN5 | STATE | 0.4484 | 0.5214 | 0.4232 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H2\|VOL_MEAN5 | STATE | 0.4478 | 0.5233 | 0.4546 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.125\|H2\|DECAY2_10 | MEMORY | 0.4476 | 0.2785 | 0.4529 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H10\|HG10 | HG | 0.4474 | 0.5352 | 0.4279 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H10\|VOL_MEAN15 | STATE | 0.4465 | 0.5 | 0.4535 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.4455 | 0.5091 | 0.3087 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|VOL_MEAN5 | STATE | 0.4442 | 0.518 | 0.1269 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H3\|VOL_HI5 | STATE | 0.4436 | 0.3168 | 0.453 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H2\|DECAY2_10 | MEMORY | 0.4428 | 0.406 | 0.4361 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H5\|VOL_HI15 | STATE | 0.4421 | 0.5765 | 0.1028 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H2\|DECAY2_10 | MEMORY | 0.4421 | 0.312 | 0.4285 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H5\|VOL_HI5 | STATE | 0.4407 | 0.553 | 0.4062 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2_CVRv5\|a0.25\|H2\|HG10 | HG | 0.4405 | 0.439 | 0.2155 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2_CVRv5\|a0.125\|H1\|NATIVE | SMOOTH | 0.4403 | 0.3254 | 0.4372 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H10\|DECAY2_10 | MEMORY | 0.4398 | 0.5211 | 0.4219 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.4396 | 0.5192 | 0.2634 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H3\|LAG1_10 | MEMORY | 0.4393 | 0.4359 | 0.4424 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H3\|NATIVE | SMOOTH | 0.439 | 0.3423 | 0.4503 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H10\|DECAY2_10 | MEMORY | 0.4389 | 0.5156 | 0.446 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H3\|VOL_HI5 | STATE | 0.4384 | 0.3664 | 0.08993 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H3\|HG5 | HG | 0.4381 | 0.3947 | 0.4517 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H2\|VOL_HI15 | STATE | 0.4376 | 0.5873 | 0.3176 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H5\|DECAY2_10 | MEMORY | 0.4376 | 0.4298 | 0.4235 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.125\|H2\|HG15 | HG | 0.4369 | 0.4957 | 0.4328 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.25\|H2\|HG5 | HG | 0.4366 | 0.5274 | 0.09013 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H5\|DECAY5_10 | MEMORY | 0.4364 | 0.4434 | 0.4242 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|VOL_HI5 | STATE | 0.4357 | 0.5016 | 0.1169 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b_CVRv5\|a0.5\|H3\|NATIVE | SMOOTH | 0.4356 | 0.41 | 0.4362 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H10\|VOL_MEAN15 | STATE | 0.4354 | 0.4915 | 0.4134 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H2\|HG15 | HG | 0.4349 | 0.4646 | 0.1903 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H10\|INV10 | MEMORY | 0.4335 | 0.5053 | 0.3982 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.125\|H2\|DECAY5_10 | MEMORY | 0.4328 | 0.272 | 0.4388 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H2\|HG5 | HG | 0.4325 | 0.504 | 0.4362 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.25\|H2\|HG10 | HG | 0.4319 | 0.3317 | 0.4198 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H3\|HG30 | HG | 0.4318 | 0.4828 | 0.42 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2\|a0.125\|H2\|HG10 | HG | 0.4318 | 0.4433 | 0.2563 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b\|a0.25\|H3\|HG15 | HG | 0.4314 | 0.2464 | 0.4425 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H3\|VOL_MEAN5 | STATE | 0.4308 | 0.3821 | 0.3878 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H10\|VOL_MEAN15 | STATE | 0.4298 | 0.4744 | 0.169 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H5\|LAG1_10 | MEMORY | 0.4297 | 0.438 | 0.4119 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H10\|DECAY5_10 | MEMORY | 0.4296 | 0.4699 | 0.4086 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b\|a0.25\|H3\|HG5 | HG | 0.4294 | 0.2128 | 0.4379 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H3\|VOL_HI5 | STATE | 0.4292 | 0.3525 | 0.1128 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H3\|VOL_HI15 | STATE | 0.429 | 0.3781 | 0.07203 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H10\|HG30 | HG | 0.4281 | 0.5126 | 0.4063 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H2\|DECAY5_10 | MEMORY | 0.4278 | 0.3013 | 0.4138 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H2\|VOL_HI5 | STATE | 0.4274 | 0.4397 | 0.4319 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H10\|VOL_MEAN15 | STATE | 0.4272 | 0.4719 | 0.4047 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H2\|VOL_MEAN5 | STATE | 0.4264 | 0.5573 | 0.282 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H5\|VOL_HI5 | STATE | 0.4263 | 0.4458 | 0.1225 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H10\|DECAY5_10 | MEMORY | 0.4256 | 0.504 | 0.4079 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H3\|INV10 | MEMORY | 0.4249 | 0.2216 | 0.4041 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2\|a0.125\|H1\|HG5 | HG | 0.4215 | 0.5058 | 0.3273 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H2\|LAG1_10 | MEMORY | 0.4205 | 0.3032 | 0.4016 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.4191 | 0.4645 | 0.4141 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H10\|VOL_HI15 | STATE | 0.4186 | 0.3793 | 0.3969 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H1\|NATIVE | SMOOTH | 0.4182 | 0.2312 | 0.4236 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H10\|INV10 | MEMORY | 0.4175 | 0.2416 | 0.4218 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H10\|LAG1_10 | MEMORY | 0.417 | 0.4918 | 0.3984 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b\|a0.25\|H1\|NATIVE | SMOOTH | 0.4168 | 0.4128 | 0.4157 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H10\|VOL_HI15 | STATE | 0.4162 | 0.4368 | 0.4205 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H2\|HG30 | HG | 0.4149 | 0.4939 | 0.03796 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H20\|VOL_MEAN15 | STATE | 0.4144 | 0.4071 | 0.3878 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H3\|DECAY2_10 | MEMORY | 0.4141 | 0.341 | 0.4067 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2_CVRv5\|a0.25\|H2\|HG10 | HG | 0.413 | 0.2718 | 0.4006 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.125\|H2\|HG10 | HG | 0.4126 | 0.3387 | 0.2142 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H2\|HG15 | HG | 0.4122 | 0.4528 | 0.1945 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H20\|INV10 | MEMORY | 0.412 | 0.4161 | 0.406 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H10\|VOL_HI5 | STATE | 0.4118 | 0.4797 | 0.3904 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2\|a0.25\|H2\|HG10 | HG | 0.4117 | 0.4199 | 0.4116 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H2\|VOL_MEAN15 | STATE | 0.4117 | 0.3438 | 0.4072 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H2\|HG10 | HG | 0.4113 | 0.5033 | 0.4181 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H10\|VOL_MEAN5 | STATE | 0.411 | 0.4707 | 0.3798 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H2\|VOL_MEAN15 | STATE | 0.4107 | 0.3782 | 0.3996 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b_CVRv5\|a0.25\|H1\|NATIVE | SMOOTH | 0.4103 | 0.4444 | 0.4009 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H2\|DECAY5_10 | MEMORY | 0.41 | 0.509 | 0.4142 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H2\|VOL_MEAN5 | STATE | 0.4099 | 0.4504 | 0.3998 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2_CVRv5\|a0.125\|H2\|HG10 | HG | 0.4095 | 0.4268 | 0.2237 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H5\|VOL_HI15 | STATE | 0.4094 | 0.3274 | 0.3779 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H20\|HG30 | HG | 0.4076 | 0.4178 | 0.3896 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|LAG1_10 | MEMORY | 0.4074 | 0.5152 | 0.09517 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H10\|VOL_MEAN5 | STATE | 0.4066 | 0.4377 | 0.4089 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H5\|HG15 | HG | 0.4064 | 0.429 | 0.4135 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H2\|LAG1_10 | MEMORY | 0.4053 | 0.5742 | 0.08381 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.25\|H2\|HG10 | HG | 0.4052 | 0.4133 | 0.09655 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H10\|DECAY2_10 | MEMORY | 0.4051 | 0.4472 | 0.3866 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H10\|VOL_HI5 | STATE | 0.4048 | 0.4136 | 0.3861 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H3\|HG15 | HG | 0.4046 | 0.2864 | 0.4084 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H3\|LAG1_10 | MEMORY | 0.4045 | 0.3913 | 0.407 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H3\|VOL_MEAN5 | STATE | 0.4042 | 0.4085 | 0.4071 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H20\|HG20 | HG | 0.4039 | 0.3898 | 0.3753 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.25\|H3\|HG15 | HG | 0.4034 | 0.5246 | 0.04576 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H5\|HG10 | HG | 0.4031 | 0.4369 | 0.4114 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H2\|HG10 | HG | 0.403 | 0.285 | 0.3909 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H3\|VOL_HI5 | STATE | 0.4029 | 0.3484 | 0.4128 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.25\|H3\|HG15 | HG | 0.4022 | 0.4809 | 0.007793 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H2\|DECAY5_10 | MEMORY | 0.402 | 0.4078 | 0.2344 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H3\|HG10 | HG | 0.4017 | 0.3766 | 0.4088 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H10\|HG15 | HG | 0.4014 | 0.351 | 0.4033 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H10\|LAG1_10 | MEMORY | 0.401 | 0.4483 | 0.4042 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|A4b\|a0.125\|H3\|HG10 | HG | 0.4 | 0.3469 | 0.4068 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H2\|HG20 | HG | 0.3996 | 0.4312 | 0.2769 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H2\|HG10 | HG | 0.3994 | 0.394 | 0.2329 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H5\|LAG1_10 | MEMORY | 0.399 | 0.4672 | 0.09716 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H2\|VOL_MEAN5 | STATE | 0.3985 | 0.3224 | 0.22 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H10\|DECAY2_10 | MEMORY | 0.3979 | 0.3766 | 0.148 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H2\|INV10 | MEMORY | 0.3974 | 0.4694 | 0.08372 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H3\|VOL_MEAN5 | STATE | 0.3953 | 0.4631 | 0.3827 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H5\|HG5 | HG | 0.3949 | 0.4148 | 0.3735 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H20\|HG30 | HG | 0.3944 | 0.3701 | 0.3634 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H2\|DECAY2_10 | MEMORY | 0.3944 | 0.3258 | 0.3763 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H20\|LAG1_10 | MEMORY | 0.394 | 0.3952 | 0.3682 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H3\|HG20 | HG | 0.3938 | 0.4902 | 0.3632 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H20\|DECAY2_10 | MEMORY | 0.3937 | 0.3815 | 0.3676 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H5\|DECAY2_10 | MEMORY | 0.3928 | 0.4296 | 0.3986 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H5\|INV10 | MEMORY | 0.3927 | 0.3874 | 0.348 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H20\|HG10 | HG | 0.3915 | 0.3936 | 0.3672 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H2\|VOL_HI5 | STATE | 0.3914 | 0.4195 | 0.2965 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H3\|DECAY2_10 | MEMORY | 0.3906 | 0.3205 | 0.4006 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.25\|H10\|HG15 | HG | 0.3902 | 0.2578 | 0.3953 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H10\|DECAY5_10 | MEMORY | 0.3901 | 0.3707 | 0.1367 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2_CVRv5\|a0.25\|H2\|HG10 | HG | 0.3894 | 0.4607 | 0.06399 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.3878 | 0.4686 | 0.2675 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H20\|VOL_MEAN5 | STATE | 0.3869 | 0.3825 | 0.3592 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H10\|LAG1_10 | MEMORY | 0.3868 | 0.4136 | 0.3674 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H2\|DECAY2_10 | MEMORY | 0.3862 | 0.4237 | 0.2248 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2\|a0.125\|H2\|HG10 | HG | 0.3852 | 0.2992 | 0.1063 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H10\|VOL_HI15 | STATE | 0.3845 | 0.4133 | 0.1117 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H2\|INV10 | MEMORY | 0.3837 | 0.3818 | 0.07718 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.125\|H2\|HG15 | HG | 0.3837 | 0.3888 | 0.08157 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H5\|DECAY5_10 | MEMORY | 0.3819 | 0.4201 | 0.3876 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H20\|DECAY5_10 | MEMORY | 0.3818 | 0.3726 | 0.3562 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H2\|VOL_HI15 | STATE | 0.3817 | 0.3727 | 0.3608 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H20\|VOL_HI15 | STATE | 0.3817 | 0.387 | 0.3548 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H2\|VOL_MEAN15 | STATE | 0.3809 | 0.4482 | 0.3864 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2_CVRv5\|a0.125\|H2\|HG15 | HG | 0.3796 | 0.4378 | 0.2036 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H10\|VOL_MEAN5 | STATE | 0.3783 | 0.3445 | 0.1208 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_union3_v2\|a0.25\|H2\|HG10 | HG | 0.377 | 0.462 | 0.124 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H2\|LAG1_10 | MEMORY | 0.3762 | 0.3725 | 0.3797 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2_CVRv5\|a0.125\|H1\|NATIVE | SMOOTH | 0.3761 | 0.2767 | 0.3663 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H2\|HG15 | HG | 0.3761 | 0.4205 | 0.09526 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H5\|HG10 | HG | 0.376 | 0.4118 | 0.3569 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H2\|LAG1_10 | MEMORY | 0.3756 | 0.354 | 0.3785 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H2\|LAG1_10 | MEMORY | 0.3756 | 0.3407 | 0.3872 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2\|a0.125\|H1\|HG5 | HG | 0.3756 | 0.3966 | 0.2181 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2\|a0.125\|H2\|HG15 | HG | 0.3756 | 0.3236 | 0.2039 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H3\|LAG1_10 | MEMORY | 0.3747 | 0.249 | 0.3645 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b_CVRv5\|a0.5\|H5\|NATIVE | SMOOTH | 0.3741 | 0.3912 | 0.3599 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H2\|VOL_MEAN15 | STATE | 0.3733 | 0.1854 | 0.3602 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H10\|VOL_MEAN5 | STATE | 0.3724 | 0.3871 | 0.3524 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H5\|INV10 | MEMORY | 0.3724 | 0.1667 | 0.3735 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H10\|HG20 | HG | 0.3719 | 0.3915 | 0.3555 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H2\|HG10 | HG | 0.3714 | 0.3579 | 0.1595 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.125\|H3\|NATIVE | SMOOTH | 0.3714 | 0.2825 | 0.3801 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H10\|LAG1_10 | MEMORY | 0.371 | 0.3549 | 0.125 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H3\|INV10 | MEMORY | 0.3702 | 0.2752 | 0.3319 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H3\|HG30 | HG | 0.3695 | 0.3289 | 0.3507 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.125\|H2\|HG10 | HG | 0.369 | 0.2601 | 0.09872 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.25\|H3\|HG10 | HG | 0.3681 | 0.1921 | 0.3453 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H10\|HG15 | HG | 0.3678 | 0.3432 | 0.3504 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H3\|NATIVE | SMOOTH | 0.3675 | 0.3058 | 0.3746 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H20\|HG15 | HG | 0.3674 | 0.3402 | 0.3468 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H3\|HG10 | HG | 0.3664 | 0.4043 | 0.3631 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H3\|NATIVE | SMOOTH | 0.3663 | 0.3477 | 0.3787 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H10\|VOL_HI5 | STATE | 0.3655 | 0.3379 | 0.1168 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H20\|HG30 | HG | 0.3653 | 0.3399 | 0.3397 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H5\|HG15 | HG | 0.3642 | 0.2864 | 0.357 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H2\|VOL_MEAN15 | STATE | 0.3637 | 0.4077 | 0.2029 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H3\|DECAY5_10 | MEMORY | 0.3637 | 0.3935 | 0.3389 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H3\|LAG1_10 | MEMORY | 0.363 | 0.371 | 0.3461 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H10\|HG10 | HG | 0.3628 | 0.3805 | 0.3558 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H2\|HG15 | HG | 0.3625 | 0.4169 | 0.09643 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H20\|HG15 | HG | 0.3624 | 0.3462 | 0.3353 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2_CVRv5\|a0.125\|H1\|HG5 | HG | 0.3609 | 0.3845 | 0.173 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H3\|DECAY2_10 | MEMORY | 0.3602 | 0.3344 | 0.3649 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H10\|HG10 | HG | 0.3591 | 0.3411 | 0.3638 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H2\|DECAY2_10 | MEMORY | 0.3576 | 0.3065 | 0.3709 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.125\|H2\|HG15 | HG | 0.3568 | 0.4176 | 0.04367 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H10\|HG30 | HG | 0.3565 | 0.3612 | 0.3457 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H20\|VOL_MEAN15 | STATE | 0.3564 | 0.3187 | 0.3365 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H10\|VOL_HI15 | STATE | 0.3561 | 0.434 | 0.337 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H10\|VOL_HI15 | STATE | 0.3552 | 0.391 | 0.07156 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H20\|HG15 | HG | 0.355 | 0.3411 | 0.3584 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H20\|HG5 | HG | 0.3541 | 0.4002 | 0.331 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H3\|DECAY2_10 | MEMORY | 0.3537 | 0.3849 | 0.3297 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H10\|HG30 | HG | 0.353 | 0.3882 | 0.3484 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H10\|DECAY2_10 | MEMORY | 0.3529 | 0.3288 | 0.09011 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H3\|DECAY5_10 | MEMORY | 0.3527 | 0.3175 | 0.361 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2\|a0.125\|H2\|HG15 | HG | 0.3526 | 0.3234 | 0.04573 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b_CVRv5\|a0.25\|H5\|HG10 | HG | 0.3526 | 0.3402 | 0.3431 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H5\|HG10 | HG | 0.3521 | 0.3057 | 0.3569 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H3\|HG10 | HG | 0.352 | 0.3817 | 0.3516 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2_CVRv5\|a0.125\|H2\|HG15 | HG | 0.3518 | 0.414 | 0.01904 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H3\|HG20 | HG | 0.3514 | 0.4217 | 0.1992 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H3\|DECAY2_10 | MEMORY | 0.3513 | 0.3993 | 0.351 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H5\|INV10 | MEMORY | 0.3509 | 0.2033 | 0.3167 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H10\|DECAY2_10 | MEMORY | 0.3502 | 0.3608 | 0.3532 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H2\|DECAY2_10 | MEMORY | 0.3501 | 0.3612 | 0.08518 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.125\|H2\|HG5 | HG | 0.35 | 0.2704 | 0.3628 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H20\|INV10 | MEMORY | 0.3483 | 0.3221 | 0.3232 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H2\|DECAY5_10 | MEMORY | 0.348 | 0.2897 | 0.3323 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H20\|VOL_HI5 | STATE | 0.3479 | 0.3072 | 0.3451 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H20\|HG20 | HG | 0.3478 | 0.317 | 0.3259 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H10\|DECAY5_10 | MEMORY | 0.3476 | 0.3204 | 0.08113 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H2\|HG20 | HG | 0.3476 | 0.333 | 0.2318 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H10\|LAG1_10 | MEMORY | 0.3468 | 0.3503 | 0.3357 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H2\|NATIVE | SMOOTH | 0.3467 | 0.3843 | 0.3549 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H3\|NATIVE | SMOOTH | 0.3462 | 0.3574 | 0.3482 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H10\|DECAY2_10 | MEMORY | 0.3452 | 0.3654 | 0.3348 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H10\|DECAY5_10 | MEMORY | 0.3452 | 0.3684 | 0.3367 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H20\|HG20 | HG | 0.3451 | 0.4221 | 0.1085 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H3\|DECAY5_10 | MEMORY | 0.3449 | 0.3509 | 0.3444 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H2\|VOL_MEAN5 | STATE | 0.3442 | 0.4256 | 0.2413 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H20\|HG30 | HG | 0.344 | 0.332 | 0.326 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H10\|INV10 | MEMORY | 0.3439 | 0.4036 | 0.008092 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H20\|VOL_HI5 | STATE | 0.3437 | 0.2848 | 0.3164 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H2\|VOL_MEAN5 | STATE | 0.3436 | 0.3273 | 0.07511 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.5\|H20\|VOL_HI5 | STATE | 0.3433 | 0.338 | 0.3195 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b\|a0.5\|H10\|NATIVE | SMOOTH | 0.3431 | 0.3774 | 0.3441 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H3\|HG20 | HG | 0.3426 | 0.3333 | 0.3418 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2_CVRv5\|a0.125\|H2\|HG10 | HG | 0.3425 | 0.3448 | 0.0452 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H2\|VOL_HI15 | STATE | 0.3425 | 0.3816 | 0.3336 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H3\|HG5 | HG | 0.3423 | 0.3304 | 0.3494 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H10\|LAG1_10 | MEMORY | 0.3423 | 0.3404 | 0.3436 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.125\|H2\|HG10 | HG | 0.3423 | 0.3517 | 0.06006 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H20\|HG20 | HG | 0.342 | 0.3098 | 0.3313 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H2\|DECAY5_10 | MEMORY | 0.3402 | 0.3376 | 0.07449 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|A4b\|a0.125\|H1\|NATIVE | SMOOTH | 0.3394 | 0.1671 | 0.3429 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b\|a0.5\|H5\|NATIVE | SMOOTH | 0.3392 | 0.3241 | 0.3401 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H3\|VOL_HI5 | STATE | 0.3389 | 0.2325 | 0.3382 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H3\|INV10 | MEMORY | 0.3386 | 0.3088 | 0.3392 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H3\|HG5 | HG | 0.3385 | 0.2404 | 0.342 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H2\|HG10 | HG | 0.3381 | 0.2973 | 0.06342 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H2\|VOL_HI15 | STATE | 0.3377 | 0.3233 | 0.3423 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.125\|H2\|HG5 | HG | 0.3377 | 0.1208 | 0.3476 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.125\|H2\|HG10 | HG | 0.3376 | 0.4205 | 0.0791 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H5\|HG15 | HG | 0.3376 | 0.3354 | 0.322 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H10\|HG30 | HG | 0.3374 | 0.208 | 0.1954 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H20\|HG30 | HG | 0.3373 | 0.3494 | 0.3393 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.25\|H3\|HG15 | HG | 0.3372 | 0.3837 | -0.02645 | 不通过（e资本） | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.125\|H2\|NATIVE | SMOOTH | 0.3367 | 0.3325 | 0.3461 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H5\|HG5 | HG | 0.3364 | 0.3083 | 0.326 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.125\|H2\|HG15 | HG | 0.3364 | 0.3931 | 0.06198 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H20\|DECAY2_10 | MEMORY | 0.3363 | 0.3062 | 0.3189 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H3\|HG15 | HG | 0.3362 | 0.3807 | 0.3424 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|A4b_CVRv5\|a0.125\|H1\|NATIVE | SMOOTH | 0.3361 | 0.1172 | 0.3229 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H3\|HG20 | HG | 0.3361 | 0.3407 | 0.09757 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H20\|LAG1_10 | MEMORY | 0.3359 | 0.3095 | 0.3172 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H10\|DECAY5_10 | MEMORY | 0.3357 | 0.3239 | 0.3391 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H3\|VOL_MEAN5 | STATE | 0.3354 | 0.3006 | 0.3421 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.125\|H3\|DECAY2_10 | MEMORY | 0.3348 | 0.1833 | 0.336 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H5\|DECAY5_10 | MEMORY | 0.3343 | 0.3231 | 0.158 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H20\|HG10 | HG | 0.3341 | 0.3434 | 0.3187 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H3\|VOL_MEAN5 | STATE | 0.334 | 0.3328 | 0.3414 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b_CVRv5\|a0.5\|H10\|NATIVE | SMOOTH | 0.3336 | 0.4015 | 0.3249 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H10\|HG20 | HG | 0.3326 | 0.3114 | 0.3221 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2\|a0.125\|H10\|HG10 | HG | 0.3315 | 0.2711 | 0.3258 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b_CVRv5\|a0.125\|H2\|HG5 | HG | 0.3313 | 0.1942 | 0.3357 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.125\|H3\|HG5 | HG | 0.3309 | 0.3208 | 0.3368 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H3\|LAG1_10 | MEMORY | 0.3305 | 0.2272 | 0.334 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H5\|DECAY2_10 | MEMORY | 0.3304 | 0.2898 | 0.3248 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.125\|H2\|HG5 | HG | 0.329 | 0.3515 | 0.3359 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H20\|HG20 | HG | 0.3289 | 0.4213 | 0.07942 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H3\|HG5 | HG | 0.3282 | 0.2617 | 0.331 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H3\|HG5 | HG | 0.3282 | 0.3169 | 0.3351 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H2\|VOL_HI5 | STATE | 0.328 | 0.3654 | 0.165 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H20\|HG30 | HG | 0.328 | 0.3292 | 0.3177 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2\|a0.125\|H2\|NATIVE | SMOOTH | 0.3276 | 0.3492 | 0.3338 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H10\|HG20 | HG | 0.3273 | 0.2168 | 0.3263 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b_CVRv5\|a0.125\|H3\|HG10 | HG | 0.3272 | 0.3107 | 0.3325 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H5\|DECAY2_10 | MEMORY | 0.3271 | 0.3205 | 0.1533 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H10\|HG15 | HG | 0.3262 | 0.3947 | 0.3417 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b_CVRv5\|a0.125\|H1\|NATIVE | SMOOTH | 0.3262 | 0.2139 | 0.3208 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H5\|VOL_MEAN5 | STATE | 0.3258 | 0.3849 | 0.3162 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.125\|H3\|HG15 | HG | 0.3256 | 0.2647 | 0.08853 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.3254 | 0.3171 | 0.1749 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H10\|HG15 | HG | 0.3253 | 0.3579 | 0.3236 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H20\|VOL_MEAN5 | STATE | 0.325 | 0.2881 | 0.3037 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H20\|DECAY5_10 | MEMORY | 0.3249 | 0.2965 | 0.3032 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H5\|HG20 | HG | 0.3246 | 0.1643 | 0.3297 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H5\|HG10 | HG | 0.324 | 0.2997 | 0.1494 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H5\|HG20 | HG | 0.3235 | 0.2479 | 0.3061 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H20\|VOL_MEAN15 | STATE | 0.3234 | 0.2838 | 0.3041 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H10\|HG10 | HG | 0.3228 | 0.308 | 0.1735 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.125\|H1\|NATIVE | SMOOTH | 0.3223 | 0.1921 | 0.3169 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H3\|DECAY2_10 | MEMORY | 0.3223 | 0.2954 | 0.3178 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H2\|HG10 | HG | 0.3223 | 0.3864 | 0.04277 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H20\|DECAY5_10 | MEMORY | 0.3223 | 0.2957 | 0.3051 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H3\|DECAY2_10 | MEMORY | 0.3223 | 0.2037 | 0.3091 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H10\|VOL_HI5 | STATE | 0.3221 | 0.219 | 0.3199 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H3\|VOL_MEAN15 | STATE | 0.3216 | 0.2365 | 0.3243 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H3\|DECAY5_10 | MEMORY | 0.3215 | 0.2125 | 0.3082 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.3213 | 0.299 | 0.1714 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H5\|DECAY5_10 | MEMORY | 0.32 | 0.3179 | 0.1432 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H5\|LAG1_10 | MEMORY | 0.3198 | 0.2567 | 0.297 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2\|a0.125\|H2\|HG15 | HG | 0.3197 | 0.321 | 0.0607 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H10\|INV10 | MEMORY | 0.3194 | 0.2256 | 0.3178 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.25\|H3\|HG10 | HG | 0.3191 | 0.3657 | 0.09782 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2_CVRv5\|a0.125\|H2\|HG15 | HG | 0.319 | 0.3548 | 0.05373 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H20\|HG10 | HG | 0.319 | 0.3411 | 0.3239 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.125\|H2\|HG10 | HG | 0.3189 | 0.3326 | 0.3259 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2\|a0.25\|H3\|HG10 | HG | 0.3186 | 0.2195 | 0.3219 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H3\|INV10 | MEMORY | 0.3185 | 0.1643 | 0.3248 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H10\|VOL_HI5 | STATE | 0.3179 | 0.2727 | 0.05463 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H2\|VOL_MEAN5 | STATE | 0.3178 | 0.4285 | 0.2117 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b\|a0.25\|H2\|NATIVE | SMOOTH | 0.3174 | 0.2961 | 0.3296 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H5\|HG5 | HG | 0.3173 | 0.331 | 0.3189 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H3\|HG10 | HG | 0.3171 | 0.2688 | 0.3236 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.125\|H2\|HG5 | HG | 0.3169 | 0.267 | 0.09834 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H5\|DECAY2_10 | MEMORY | 0.3168 | 0.32 | 0.1436 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b_CVRv5\|a0.125\|H5\|HG10 | HG | 0.3168 | 0.3091 | 0.3196 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b\|a0.25\|H3\|NATIVE | SMOOTH | 0.3165 | 0.2934 | 0.326 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H3\|VOL_HI5 | STATE | 0.3161 | 0.2368 | 0.3226 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H3\|DECAY5_10 | MEMORY | 0.316 | 0.2924 | 0.3207 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H10\|HG30 | HG | 0.3152 | 0.2823 | 0.3091 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H10\|HG30 | HG | 0.3148 | 0.3001 | 0.3063 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H2\|DECAY5_10 | MEMORY | 0.3148 | 0.4233 | 0.03992 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2_CVRv5\|a0.25\|H2\|HG10 | HG | 0.3146 | 0.3061 | 0.2938 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H20\|DECAY2_10 | MEMORY | 0.3143 | 0.2722 | 0.307 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H20\|VOL_HI15 | STATE | 0.3142 | 0.2906 | 0.2955 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H3\|HG20 | HG | 0.3141 | 0.3557 | 0.1622 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H20\|DECAY5_10 | MEMORY | 0.314 | 0.2897 | 0.3184 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H20\|VOL_HI15 | STATE | 0.3133 | 0.3097 | 0.317 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.125\|H2\|HG5 | HG | 0.3133 | 0.3015 | 0.06972 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H10\|HG15 | HG | 0.3132 | 0.2106 | 0.3073 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H20\|LAG1_10 | MEMORY | 0.3125 | 0.2906 | 0.2899 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H20\|HG30 | HG | 0.3122 | 0.3071 | 0.3084 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H20\|HG20 | HG | 0.3118 | 0.2498 | 0.2981 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H20\|DECAY5_10 | MEMORY | 0.3116 | 0.2789 | 0.3051 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H2\|VOL_HI15 | STATE | 0.3114 | 0.3596 | 0.05721 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H10\|HG5 | HG | 0.3113 | 0.2252 | 0.3027 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H5\|DECAY2_10 | MEMORY | 0.3113 | 0.2736 | 0.3225 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H10\|VOL_HI5 | STATE | 0.311 | 0.2426 | 0.3054 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H5\|HG5 | HG | 0.311 | 0.3013 | 0.2996 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.125\|H2\|HG10 | HG | 0.3109 | 0.2605 | 0.2145 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H20\|VOL_MEAN15 | STATE | 0.3108 | 0.2805 | 0.3163 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H20\|VOL_MEAN15 | STATE | 0.3108 | 0.2816 | 0.3027 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H5\|VOL_HI15 | STATE | 0.3108 | 0.1558 | 0.3083 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H5\|LAG1_10 | MEMORY | 0.3104 | 0.3597 | 0.2981 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H20\|LAG1_10 | MEMORY | 0.3099 | 0.268 | 0.305 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H3\|DECAY5_10 | MEMORY | 0.3086 | 0.2543 | 0.1311 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H10\|INV10 | MEMORY | 0.3085 | 0.3823 | -0.02105 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H5\|HG10 | HG | 0.3083 | 0.2784 | 0.1344 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H20\|DECAY2_10 | MEMORY | 0.3075 | 0.2915 | 0.2864 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H3\|HG10 | HG | 0.3071 | 0.2583 | 0.1288 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H5\|LAG1_10 | MEMORY | 0.3069 | 0.2404 | 0.2939 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H2\|VOL_MEAN5 | STATE | 0.3068 | 0.3664 | 0.03172 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H10\|HG30 | HG | 0.3064 | 0.2722 | 0.3048 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H20\|VOL_MEAN5 | STATE | 0.3062 | 0.2898 | 0.3098 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H20\|VOL_MEAN5 | STATE | 0.3058 | 0.2772 | 0.2857 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2\|a0.125\|H3\|HG10 | HG | 0.3048 | 0.238 | 0.126 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H5\|VOL_HI5 | STATE | 0.3047 | 0.3612 | 0.297 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H10\|VOL_HI5 | STATE | 0.3036 | 0.2243 | 0.2964 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H3\|HG15 | HG | 0.3034 | 0.2446 | 0.2876 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H3\|HG5 | HG | 0.3033 | 0.1709 | 0.3105 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|A4b_CVRv5\|a0.125\|H5\|HG10 | HG | 0.3032 | 0.2869 | 0.2848 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H10\|HG5 | HG | 0.303 | 0.267 | 0.2877 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H3\|DECAY2_10 | MEMORY | 0.3028 | 0.2592 | 0.2857 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H2\|LAG1_10 | MEMORY | 0.3027 | 0.2755 | 0.04333 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H10\|DECAY5_10 | MEMORY | 0.3026 | 0.3344 | 0.2964 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H5\|DECAY5_10 | MEMORY | 0.3026 | 0.2868 | 0.2965 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H2\|DECAY5_10 | MEMORY | 0.3022 | 0.3309 | 0.1228 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H20\|LAG1_10 | MEMORY | 0.3016 | 0.2829 | 0.3045 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H3\|HG30 | HG | 0.3015 | 0.3151 | -0.06273 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H5\|VOL_MEAN5 | STATE | 0.3012 | 0.3535 | 0.2894 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H10\|DECAY2_10 | MEMORY | 0.3009 | 0.356 | 0.2929 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H5\|HG15 | HG | 0.3005 | 0.1152 | 0.302 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H20\|DECAY2_10 | MEMORY | 0.2989 | 0.2869 | 0.3045 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H5\|HG5 | HG | 0.2989 | 0.1832 | 0.2947 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H10\|INV10 | MEMORY | 0.2987 | 0.2822 | 0.2711 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H3\|HG15 | HG | 0.298 | 0.2242 | 0.07802 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H10\|INV10 | MEMORY | 0.2975 | 0.3583 | 0.2714 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.125\|H2\|HG5 | HG | 0.2973 | 0.3221 | 0.03978 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|A4b\|a0.125\|H5\|HG10 | HG | 0.2972 | 0.288 | 0.3044 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H2\|HG10 | HG | 0.2967 | 0.3265 | 0.1118 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_union3_v2_CVRv5\|a0.25\|H2\|HG10 | HG | 0.2965 | 0.3282 | 0.05179 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H10\|VOL_HI5 | STATE | 0.2959 | 0.2871 | 0.2842 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H2\|LAG1_10 | MEMORY | 0.2947 | 0.2536 | 0.1995 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H20\|VOL_HI5 | STATE | 0.2942 | 0.2409 | 0.2836 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H10\|VOL_HI15 | STATE | 0.2942 | 0.3064 | 0.2873 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H20\|VOL_HI15 | STATE | 0.2936 | 0.2654 | 0.2776 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H2\|VOL_HI5 | STATE | 0.2936 | 0.3288 | 0.04838 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H5\|VOL_MEAN5 | STATE | 0.2935 | 0.2613 | 0.1151 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.125\|H2\|HG5 | HG | 0.2931 | 0.2879 | 0.06563 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H10\|VOL_HI15 | STATE | 0.2928 | 0.1905 | 0.2851 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H3\|DECAY2_10 | MEMORY | 0.2927 | 0.2706 | 0.1191 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.25\|H10\|HG10 | HG | 0.2927 | 0.3486 | 0.06121 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H10\|DECAY2_10 | MEMORY | 0.2924 | 0.1786 | 0.2866 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.125\|H2\|HG15 | HG | 0.2919 | 0.3498 | 0.09462 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H20\|VOL_MEAN15 | STATE | 0.2917 | 0.2519 | 0.2754 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H20\|VOL_HI15 | STATE | 0.2911 | 0.2511 | 0.2864 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.125\|H3\|HG10 | HG | 0.2911 | 0.2281 | 0.08937 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.125\|H1\|NATIVE | SMOOTH | 0.2907 | 0.245 | 0.07958 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H2\|VOL_HI15 | STATE | 0.2905 | 0.3625 | 0.04855 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H10\|HG20 | HG | 0.2903 | 0.2268 | 0.2886 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H5\|LAG1_10 | MEMORY | 0.2902 | 0.2403 | 0.2815 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H20\|LAG1_10 | MEMORY | 0.2902 | 0.2952 | 0.2787 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.5\|H20\|VOL_HI5 | STATE | 0.2902 | 0.2711 | 0.2743 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H3\|INV10 | MEMORY | 0.29 | 0.2369 | 0.2904 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H10\|HG20 | HG | 0.29 | 0.2202 | 0.2864 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H20\|HG30 | HG | 0.2898 | 0.2577 | 0.2822 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.125\|H5\|HG15 | HG | 0.2895 | 0.3432 | 0.282 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2\|a0.125\|H2\|HG5 | HG | 0.2892 | 0.1911 | 0.03419 | 通过 | 不通过（e资本） | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H20\|DECAY2_10 | MEMORY | 0.2889 | 0.2364 | 0.2732 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H10\|HG10 | HG | 0.2887 | 0.286 | 0.2822 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H10\|LAG1_10 | MEMORY | 0.2886 | 0.154 | 0.285 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H20\|DECAY5_10 | MEMORY | 0.2884 | 0.2521 | 0.2891 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H5\|LAG1_10 | MEMORY | 0.2882 | 0.3129 | 0.2925 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H20\|HG10 | HG | 0.2882 | 0.2945 | 0.2785 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H5\|HG15 | HG | 0.2882 | 0.236 | 0.08054 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H10\|HG10 | HG | 0.2882 | 0.3208 | 0.2943 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2\|a0.125\|H3\|HG10 | HG | 0.288 | 0.3073 | 0.2815 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H2\|LAG1_10 | MEMORY | 0.2878 | 0.2938 | 0.1274 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H2\|LAG1_10 | MEMORY | 0.2875 | 0.3209 | 0.109 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2_CVRv5\|a0.25\|H3\|HG10 | HG | 0.2874 | 0.3116 | 0.06499 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H10\|VOL_HI15 | STATE | 0.2872 | 0.2695 | 0.2797 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H20\|DECAY5_10 | MEMORY | 0.2863 | 0.2351 | 0.2719 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H5\|HG20 | HG | 0.2863 | 0.2924 | 0.289 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H5\|HG15 | HG | 0.2859 | 0.2254 | 0.08863 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H3\|LAG1_10 | MEMORY | 0.2857 | 0.1745 | 0.2733 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H5\|DECAY2_10 | MEMORY | 0.2851 | 0.3021 | 0.2656 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H20\|LAG1_10 | MEMORY | 0.2851 | 0.2276 | 0.2734 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2_CVRv5\|a0.125\|H2\|HG5 | HG | 0.2846 | 0.2254 | 0.008354 | 通过 | 不通过（e资本） | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.125\|H10\|HG20 | HG | 0.2846 | 0.2682 | 0.2799 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H10\|DECAY2_10 | MEMORY | 0.2842 | 0.3372 | 0.2761 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H5\|HG10 | HG | 0.2839 | 0.2379 | 0.2945 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H5\|HG15 | HG | 0.2838 | 0.2434 | 0.07549 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H5\|VOL_HI5 | STATE | 0.2838 | 0.1394 | 0.2846 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H2\|LAG1_10 | MEMORY | 0.2827 | 0.3582 | 0.01394 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.125\|H3\|HG15 | HG | 0.2826 | 0.3375 | 0.2762 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H3\|VOL_MEAN5 | STATE | 0.2823 | 0.3585 | 0.2741 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2_CVRv5\|a0.125\|H3\|HG10 | HG | 0.2823 | 0.1988 | 0.09842 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H20\|DECAY5_10 | MEMORY | 0.282 | 0.2911 | 0.2721 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2\|a0.125\|H5\|HG10 | HG | 0.2815 | 0.2227 | 0.1115 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H20\|VOL_MEAN5 | STATE | 0.2814 | 0.2602 | 0.2743 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H10\|HG15 | HG | 0.2808 | 0.161 | 0.277 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2_CVRv5\|a0.25\|H5\|HG10 | HG | 0.2794 | 0.3014 | 0.07272 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H20\|VOL_MEAN5 | STATE | 0.2794 | 0.2397 | 0.2787 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H20\|HG15 | HG | 0.2793 | 0.2958 | 0.2871 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H20\|DECAY2_10 | MEMORY | 0.279 | 0.2951 | 0.2684 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H10\|LAG1_10 | MEMORY | 0.2788 | 0.2235 | 0.2789 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H10\|HG20 | HG | 0.2775 | 0.2691 | 0.2773 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H10\|DECAY5_10 | MEMORY | 0.2772 | 0.3302 | 0.2717 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2\|a0.125\|H3\|NATIVE | SMOOTH | 0.2771 | 0.2458 | 0.282 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H3\|VOL_HI15 | STATE | 0.2769 | 0.2403 | 0.2752 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H5\|VOL_MEAN5 | STATE | 0.276 | 0.359 | 0.2814 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H10\|VOL_MEAN5 | STATE | 0.2755 | 0.1434 | 0.2686 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H3\|DECAY5_10 | MEMORY | 0.2751 | 0.1882 | 0.09473 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.125\|H5\|HG15 | HG | 0.2748 | 0.2618 | 0.2587 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H3\|HG10 | HG | 0.2746 | 0.1893 | 0.09587 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2\|a0.125\|H5\|HG10 | HG | 0.2744 | 0.2173 | 0.2692 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.25\|H10\|HG15 | HG | 0.2744 | 0.3262 | 0.02202 | 通过 | 不通过（e资本） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H5\|LAG1_10 | MEMORY | 0.2742 | 0.08642 | 0.2788 | 通过 | 不通过（正向门槛） | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H5\|NATIVE | SMOOTH | 0.274 | 0.2597 | 0.2737 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H20\|HG15 | HG | 0.2737 | 0.2477 | 0.2607 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H20\|VOL_MEAN15 | STATE | 0.2733 | 0.3097 | 0.07836 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H5\|LAG1_10 | MEMORY | 0.2733 | 0.3193 | 0.1049 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H5\|DECAY5_10 | MEMORY | 0.273 | 0.2935 | 0.2559 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H5\|VOL_MEAN5 | STATE | 0.2728 | 0.2631 | 0.1002 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H3\|VOL_HI15 | STATE | 0.2726 | 0.2947 | 0.2745 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H10\|DECAY5_10 | MEMORY | 0.2726 | 0.1522 | 0.2667 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H5\|LAG1_10 | MEMORY | 0.2726 | 0.3097 | 0.101 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H5\|INV10 | MEMORY | 0.2725 | 0.2667 | 0.2432 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.25\|H5\|HG10 | HG | 0.2723 | 0.3064 | 0.063 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.5\|H10\|NATIVE | SMOOTH | 0.2716 | 0.2394 | 0.2373 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H20\|HG10 | HG | 0.2711 | 0.3112 | 0.2788 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H10\|HG5 | HG | 0.2711 | 0.2208 | 0.2698 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H10\|HG20 | HG | 0.2708 | 0.241 | 0.08583 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H5\|VOL_HI5 | STATE | 0.2707 | 0.2742 | 0.1446 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H2\|VOL_HI5 | STATE | 0.2706 | 0.344 | 0.01418 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H10\|VOL_MEAN15 | STATE | 0.2705 | 0.1864 | 0.2651 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H10\|LAG1_10 | MEMORY | 0.2702 | 0.2362 | 0.1285 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H10\|LAG1_10 | MEMORY | 0.2698 | 0.2852 | 0.2655 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H10\|HG20 | HG | 0.2698 | 0.2109 | 0.2521 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H10\|HG15 | HG | 0.2697 | 0.3249 | 0.02011 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H10\|INV10 | MEMORY | 0.2695 | 0.292 | 0.276 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H3\|HG15 | HG | 0.2692 | 0.2014 | 0.02835 | 通过 | 不通过（e资本） | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H10\|HG20 | HG | 0.2691 | 0.1555 | 0.14 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H5\|VOL_MEAN15 | STATE | 0.2691 | 0.2812 | 0.1583 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H20\|VOL_HI15 | STATE | 0.2691 | 0.2185 | 0.2696 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|M_union3_v2\|a0.125\|H1\|NATIVE | SMOOTH | 0.2684 | 0.2069 | 0.05805 | 通过 | 不通过（e资本） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H10\|DECAY2_10 | MEMORY | 0.268 | 0.1981 | 0.2638 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H10\|HG15 | HG | 0.2677 | 0.2323 | 0.1101 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H20\|LAG1_10 | MEMORY | 0.2672 | 0.3018 | 0.2719 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H3\|NATIVE | SMOOTH | 0.2669 | 0.3159 | 0.2714 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_mean3_v2\|a0.125\|H10\|HG10 | HG | 0.2668 | 0.1956 | 0.2661 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H10\|VOL_MEAN5 | STATE | 0.2665 | 0.2199 | 0.1205 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H20\|DECAY2_10 | MEMORY | 0.2664 | 0.3233 | 0.2729 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2\|a0.125\|H2\|HG10 | HG | 0.2664 | 0.1702 | 0.04911 | 通过 | 不通过（e资本） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.2657 | 0.1832 | 0.2663 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H10\|DECAY5_10 | MEMORY | 0.2657 | 0.2018 | 0.262 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H5\|DECAY5_10 | MEMORY | 0.2655 | 0.2292 | 0.2747 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.25\|H20\|VOL_MEAN15 | STATE | 0.2649 | 0.2171 | 0.2672 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H5\|NATIVE | SMOOTH | 0.2638 | 0.264 | 0.2402 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H5\|VOL_HI15 | STATE | 0.2635 | 0.2924 | 0.2472 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H5\|HG15 | HG | 0.2634 | 0.2607 | 0.06776 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2_CVRv5\|a0.125\|H5\|HG10 | HG | 0.2633 | 0.241 | 0.09225 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H3\|NATIVE | SMOOTH | 0.2632 | 0.2699 | 0.2771 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H10\|VOL_MEAN5 | STATE | 0.263 | 0.1819 | 0.2647 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H2\|HG10 | HG | 0.263 | 0.2791 | 0.08122 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H3\|DECAY2_10 | MEMORY | 0.263 | 0.1954 | 0.08805 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H5\|DECAY2_10 | MEMORY | 0.2627 | 0.3103 | 0.2481 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H20\|VOL_HI15 | STATE | 0.2625 | 0.2011 | 0.2521 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_mean3_v2\|a0.125\|H3\|HG10 | HG | 0.2624 | 0.2162 | 0.2663 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H2\|LAG1_10 | MEMORY | 0.2622 | 0.2654 | 0.08233 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H10\|VOL_HI5 | STATE | 0.2622 | 0.175 | 0.1744 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H5\|VOL_MEAN5 | STATE | 0.262 | 0.2119 | 0.268 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H20\|DECAY2_10 | MEMORY | 0.2619 | 0.28 | 0.0816 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H20\|DECAY5_10 | MEMORY | 0.2615 | 0.3066 | 0.2685 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b\|a0.125\|H3\|HG5 | HG | 0.2615 | 0.1425 | 0.262 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H3\|DECAY2_10 | MEMORY | 0.2613 | 0.237 | 0.264 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H10\|HG5 | HG | 0.2613 | 0.2707 | 0.2708 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H5\|HG20 | HG | 0.2608 | 0.2575 | 0.03662 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H20\|HG5 | HG | 0.2607 | 0.2823 | 0.2438 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.2606 | 0.2491 | 0.1088 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H10\|VOL_MEAN15 | STATE | 0.2605 | 0.2107 | 0.2547 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H10\|VOL_MEAN15 | STATE | 0.2602 | 0.2442 | 0.2532 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H10\|NATIVE | SMOOTH | 0.26 | 0.2563 | 0.2629 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H20\|HG20 | HG | 0.2599 | 0.2466 | 0.2544 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H10\|VOL_MEAN15 | STATE | 0.2596 | 0.2964 | 0.2509 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H10\|VOL_MEAN15 | STATE | 0.2596 | 0.2688 | 0.1202 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b_CVRv5\|a0.25\|H10\|HG10 | HG | 0.2596 | 0.2888 | 0.2594 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.125\|H10\|HG15 | HG | 0.2595 | 0.2967 | 0.0467 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H10\|HG10 | HG | 0.2592 | 0.1429 | 0.2529 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.2587 | 0.2545 | 0.1055 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H3\|LAG1_10 | MEMORY | 0.2585 | 0.248 | 0.2615 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H5\|VOL_HI15 | STATE | 0.2582 | 0.3079 | 0.2543 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H2\|DECAY5_10 | MEMORY | 0.2577 | 0.3151 | 0.08147 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b\|a0.5\|H20\|NATIVE | SMOOTH | 0.2576 | 0.2703 | 0.2659 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.125\|H5\|HG15 | HG | 0.2572 | 0.2594 | 0.2641 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H3\|VOL_MEAN15 | STATE | 0.2572 | 0.2235 | 0.08816 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2\|a0.125\|H10\|HG10 | HG | 0.2571 | 0.2414 | 0.111 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H20\|VOL_HI5 | STATE | 0.257 | 0.2011 | 0.2407 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b_CVRv5\|a0.25\|H20\|HG10 | HG | 0.2566 | 0.2442 | 0.2507 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H20\|VOL_MEAN5 | STATE | 0.2564 | 0.2241 | 0.2437 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H20\|HG15 | HG | 0.2563 | 0.2331 | 0.2662 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2_CVRv5\|a0.125\|H2\|HG10 | HG | 0.2558 | 0.2569 | 0.1527 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H3\|INV10 | MEMORY | 0.2557 | 0.1377 | 0.226 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H10\|LAG1_10 | MEMORY | 0.2553 | 0.3082 | 0.2525 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H20\|HG15 | HG | 0.2551 | 0.241 | 0.2438 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H10\|HG15 | HG | 0.255 | 0.2051 | 0.1534 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H5\|HG20 | HG | 0.2547 | 0.2253 | 0.2322 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H10\|HG10 | HG | 0.2546 | 0.2456 | 0.1024 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H10\|HG30 | HG | 0.254 | 0.07023 | 0.2543 | 通过 | 不通过（正向门槛） | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H20\|DECAY5_10 | MEMORY | 0.254 | 0.2662 | 0.07085 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H20\|HG20 | HG | 0.2532 | 0.2198 | 0.2412 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2_CVRv5\|a0.5\|H20\|HG10 | HG | 0.2532 | 0.3718 | 0.006318 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.25\|H10\|HG10 | HG | 0.253 | 0.2858 | 0.09249 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H5\|VOL_MEAN15 | STATE | 0.2529 | 0.1749 | 0.08466 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H5\|HG30 | HG | 0.2525 | 0.1949 | 0.2552 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.125\|H3\|HG5 | HG | 0.252 | 0.1639 | 0.02637 | 通过 | 不通过（e资本） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H3\|DECAY5_10 | MEMORY | 0.252 | 0.2228 | 0.2549 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H10\|HG5 | HG | 0.252 | 0.1599 | 0.2521 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H5\|HG15 | HG | 0.2517 | 0.1869 | 0.03669 | 通过 | 不通过（e资本） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H20\|HG15 | HG | 0.2514 | 0.258 | 0.2532 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H10\|HG10 | HG | 0.2512 | 0.2019 | 0.2522 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b_CVRv5\|a0.125\|H5\|HG5 | HG | 0.251 | 0.1854 | 0.2447 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H2\|LAG1_10 | MEMORY | 0.2509 | 0.237 | 0.1575 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H5\|HG20 | HG | 0.2508 | 0.2689 | 0.02863 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H10\|HG5 | HG | 0.2506 | 0.2414 | 0.2476 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H10\|LAG1_10 | MEMORY | 0.2503 | 0.1794 | 0.246 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H20\|INV10 | MEMORY | 0.2502 | 0.2322 | 0.2428 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H10\|HG5 | HG | 0.25 | 0.2584 | 0.2556 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H5\|LAG1_10 | MEMORY | 0.2498 | 0.2634 | 0.2299 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H3\|HG10 | HG | 0.2495 | 0.1739 | 0.04458 | 通过 | 不通过（e资本） | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H3\|VOL_HI15 | STATE | 0.2493 | 0.2594 | 0.2432 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H2\|HG5 | HG | 0.2493 | 0.1845 | 0.1805 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H20\|HG20 | HG | 0.2489 | 0.231 | 0.2302 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H5\|NATIVE | SMOOTH | 0.2487 | 0.2151 | 0.2353 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H2\|DECAY2_10 | MEMORY | 0.2482 | 0.2868 | 0.07691 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.25\|H20\|HG10 | HG | 0.2476 | 0.2125 | 0.2544 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H20\|HG15 | HG | 0.2474 | 0.2313 | 0.2427 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H3\|HG20 | HG | 0.2473 | 0.265 | 0.2368 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H10\|HG20 | HG | 0.2471 | 0.1149 | 0.1172 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H5\|VOL_MEAN15 | STATE | 0.247 | 0.1715 | 0.08293 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.125\|H2\|HG10 | HG | 0.2468 | 0.2865 | 0.07795 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H20\|DECAY2_10 | MEMORY | 0.2467 | 0.2514 | 0.1366 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H5\|VOL_MEAN15 | STATE | 0.2461 | 0.1797 | 0.2515 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H3\|VOL_HI5 | STATE | 0.2453 | 0.2902 | 0.1395 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H3\|HG30 | HG | 0.2451 | 0.3112 | 0.1009 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2_CVRv5\|a0.125\|H2\|HG10 | HG | 0.2449 | 0.3536 | 0.1044 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H3\|LAG1_10 | MEMORY | 0.2446 | 0.2143 | 0.06663 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_union3_v2\|a0.125\|H2\|HG10 | HG | 0.2442 | 0.2938 | 0.11 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H2\|HG5 | HG | 0.2437 | 0.321 | 0.02204 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.2437 | 0.1904 | 0.2449 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2_CVRv5\|a0.125\|H1\|NATIVE | SMOOTH | 0.2436 | 0.2388 | 0.004901 | 通过 | 不通过（e资本） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H20\|DECAY5_10 | MEMORY | 0.2436 | 0.2525 | 0.1319 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H10\|DECAY5_10 | MEMORY | 0.2425 | 0.2052 | 0.1475 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.25\|H20\|VOL_MEAN15 | STATE | 0.2425 | 0.2802 | 0.03332 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H10\|DECAY2_10 | MEMORY | 0.2425 | 0.206 | 0.1468 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H20\|LAG1_10 | MEMORY | 0.2423 | 0.2574 | 0.06256 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H10\|VOL_MEAN5 | STATE | 0.2419 | 0.1982 | 0.1455 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.125\|H1\|NATIVE | SMOOTH | 0.2409 | 0.2334 | 0.05792 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H1\|NATIVE | SMOOTH | 0.24 | 0.1749 | 0.0447 | 通过 | 不通过（e资本） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.125\|H2\|HG5 | HG | 0.2399 | 0.3074 | 0.09608 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.25\|H20\|INV10 | MEMORY | 0.2399 | 0.2159 | 0.2167 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b_CVRv5\|a0.25\|H2\|NATIVE | SMOOTH | 0.2397 | 0.2437 | 0.2465 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H5\|VOL_MEAN5 | STATE | 0.2393 | 0.2492 | 0.1244 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H5\|DECAY2_10 | MEMORY | 0.2393 | 0.2718 | 0.1272 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H3\|VOL_MEAN15 | STATE | 0.239 | 0.1632 | 0.07184 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.125\|H1\|NATIVE | SMOOTH | 0.2384 | 0.3239 | 0.1027 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H20\|HG10 | HG | 0.2383 | 0.2419 | 0.1276 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H20\|VOL_HI5 | STATE | 0.2382 | 0.2028 | 0.228 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H3\|VOL_MEAN15 | STATE | 0.2379 | 0.2054 | 0.2297 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.2378 | 0.1829 | 0.2393 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H10\|HG15 | HG | 0.2376 | 0.2395 | 0.07657 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2\|a0.125\|H20\|HG10 | HG | 0.2374 | 0.2161 | 0.2339 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H20\|VOL_MEAN5 | STATE | 0.237 | 0.2281 | 0.05025 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H5\|HG5 | HG | 0.2369 | 0.1269 | 0.2412 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H20\|HG5 | HG | 0.2368 | 0.2341 | 0.2442 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H10\|VOL_MEAN5 | STATE | 0.2363 | 0.2456 | 0.2327 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H5\|VOL_HI5 | STATE | 0.2362 | 0.1313 | 0.242 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.125\|H3\|HG5 | HG | 0.2361 | 0.1208 | 0.2268 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H5\|DECAY2_10 | MEMORY | 0.236 | 0.1648 | 0.2396 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.125\|H5\|HG15 | HG | 0.2359 | 0.3155 | -0.02199 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H20\|HG15 | HG | 0.2357 | 0.2428 | 0.2426 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H20\|HG5 | HG | 0.2347 | 0.2478 | 0.2392 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H10\|VOL_MEAN5 | STATE | 0.2346 | 0.1539 | 0.2298 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H10\|VOL_HI15 | STATE | 0.2346 | 0.1824 | 0.1374 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b_CVRv5\|a0.25\|H10\|HG10 | HG | 0.2345 | 0.2734 | 0.23 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H5\|LAG1_10 | MEMORY | 0.2335 | 0.3062 | -0.00357 | 不通过（e资本） | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H20\|HG10 | HG | 0.233 | 0.2007 | 0.2403 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H10\|VOL_MEAN15 | STATE | 0.2329 | 0.2464 | 0.1243 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H20\|INV10 | MEMORY | 0.2328 | 0.2126 | 0.2371 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H20\|INV10 | MEMORY | 0.2325 | 0.2237 | 0.2098 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H20\|HG20 | HG | 0.2324 | 0.1926 | 0.2288 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H10\|LAG1_10 | MEMORY | 0.2316 | 0.1805 | 0.1357 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H10\|VOL_HI5 | STATE | 0.2312 | 0.2333 | 0.112 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.25\|H10\|HG10 | HG | 0.2311 | 0.3061 | -0.01609 | 不通过（e资本） | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H5\|VOL_MEAN5 | STATE | 0.2307 | 0.2791 | -0.007975 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H20\|HG10 | HG | 0.2306 | 0.1941 | 0.2244 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.125\|H3\|HG5 | HG | 0.2306 | 0.1721 | 0.002232 | 通过 | 不通过（e资本） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H10\|VOL_HI5 | STATE | 0.2306 | 0.2593 | 0.2342 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H5\|DECAY2_10 | MEMORY | 0.2302 | 0.2734 | -0.005367 | 不通过（e资本） | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.125\|H3\|HG5 | HG | 0.2302 | 0.1474 | 0.237 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H20\|HG20 | HG | 0.2301 | 0.2084 | 0.2295 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2_CVRv5\|a0.125\|H10\|HG10 | HG | 0.23 | 0.2156 | 0.2328 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H10\|VOL_HI15 | STATE | 0.23 | 0.1745 | 0.2261 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2_CVRv5\|a0.125\|H5\|HG10 | HG | 0.2299 | 0.2622 | 0.06146 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H10\|INV10 | MEMORY | 0.2297 | 0.1518 | 0.2334 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.25\|H20\|INV10 | MEMORY | 0.2296 | 0.2028 | 0.2347 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H20\|VOL_HI5 | STATE | 0.2292 | 0.2295 | 0.2318 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H10\|HG20 | HG | 0.2291 | 0.2149 | 0.2267 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2_CVRv5\|a0.25\|H10\|HG15 | HG | 0.2286 | 0.2849 | 0.01414 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.125\|H10\|HG10 | HG | 0.2284 | 0.164 | 0.2291 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.125\|H10\|HG15 | HG | 0.2277 | 0.242 | 0.01074 | 通过 | 不通过（e资本） | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H5\|DECAY5_10 | MEMORY | 0.2273 | 0.2752 | 0.2317 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H10\|NATIVE | SMOOTH | 0.2273 | 0.2612 | 0.2138 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2\|a0.125\|H2\|HG5 | HG | 0.2269 | 0.2506 | 0.1277 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H20\|HG15 | HG | 0.2269 | 0.18 | 0.2244 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.2268 | 0.2438 | 0.2188 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H10\|VOL_MEAN15 | STATE | 0.2267 | 0.1387 | 0.2257 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H3\|LAG1_10 | MEMORY | 0.2262 | 0.1551 | 0.05323 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H10\|VOL_HI15 | STATE | 0.2257 | 0.1575 | 0.2239 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H5\|DECAY5_10 | MEMORY | 0.2256 | 0.258 | -0.01469 | 不通过（e资本） | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.125\|H10\|HG5 | HG | 0.2256 | 0.1197 | 0.2291 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.125\|H10\|HG15 | HG | 0.2254 | 0.1838 | 0.2182 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b_CVRv5\|a0.125\|H2\|NATIVE | SMOOTH | 0.2252 | 0.1555 | 0.2275 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.125\|H5\|HG10 | HG | 0.225 | 0.2808 | 0.05827 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H10\|INV10 | MEMORY | 0.2249 | 0.2482 | 0.2042 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H5\|HG10 | HG | 0.2247 | 0.2589 | 0.2291 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H20\|VOL_HI5 | STATE | 0.2246 | 0.1746 | 0.2239 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H10\|VOL_MEAN15 | STATE | 0.224 | 0.282 | 0.1064 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.25\|H10\|VOL_HI5 | STATE | 0.2239 | 0.2236 | 0.22 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.25\|H20\|VOL_HI15 | STATE | 0.2231 | 0.2346 | 0.02626 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2_CVRv5\|a0.125\|H5\|HG15 | HG | 0.223 | 0.2004 | 0.03286 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H20\|HG5 | HG | 0.2226 | 0.2135 | 0.215 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.125\|H3\|HG10 | HG | 0.2226 | 0.1407 | 0.04545 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H3\|INV10 | MEMORY | 0.2223 | 0.03086 | 0.2328 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.25\|H20\|HG15 | HG | 0.2222 | 0.205 | 0.2292 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H5\|VOL_HI15 | STATE | 0.2214 | 0.2119 | 0.2177 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H5\|NATIVE | SMOOTH | 0.2212 | 0.1595 | 0.2251 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H1\|NATIVE | SMOOTH | 0.2204 | 0.1846 | 0.007835 | 通过 | 不通过（e资本） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H10\|HG15 | HG | 0.2201 | 0.2297 | 0.21 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b_CVRv5\|a0.25\|H20\|HG10 | HG | 0.22 | 0.2076 | 0.2112 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b\|a0.25\|H20\|HG10 | HG | 0.22 | 0.2383 | 0.2273 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_mean3_v2\|a0.125\|H20\|HG10 | HG | 0.2191 | 0.1763 | 0.2171 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.2191 | 0.2144 | 0.2098 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H10\|INV10 | MEMORY | 0.2186 | 0.109 | 0.2169 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H10\|HG10 | HG | 0.2184 | 0.2583 | 0.2117 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H5\|HG5 | HG | 0.2184 | 0.1813 | 0.08505 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H10\|VOL_MEAN5 | STATE | 0.218 | 0.2274 | 0.1083 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H10\|LAG1_10 | MEMORY | 0.2179 | 0.1897 | 0.07512 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.125\|H20\|HG15 | HG | 0.2178 | 0.1846 | 0.2104 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.125\|H5\|HG5 | HG | 0.2177 | 0.1728 | 0.2179 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.125\|H5\|HG15 | HG | 0.2174 | 0.1426 | 0.01854 | 通过 | 不通过（e资本） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H20\|HG5 | HG | 0.2174 | 0.204 | 0.2108 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.125\|H10\|HG10 | HG | 0.2173 | 0.2574 | 0.08114 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H10\|INV10 | MEMORY | 0.2173 | 0.2419 | 0.1955 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H20\|HG30 | HG | 0.2171 | 0.1386 | 0.2204 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H10\|VOL_HI5 | STATE | 0.217 | 0.1686 | 0.08749 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.25\|H20\|INV10 | MEMORY | 0.2169 | 0.2095 | 0.2283 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2_CVRv5\|a0.25\|H10\|HG10 | HG | 0.2157 | 0.2492 | 0.05551 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.125\|H10\|HG10 | HG | 0.2156 | 0.2806 | 0.2085 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H10\|INV10 | MEMORY | 0.2145 | 0.1751 | 0.2126 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H10\|VOL_MEAN15 | STATE | 0.214 | 0.1454 | 0.1255 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H20\|HG15 | HG | 0.2139 | 0.2015 | 0.2084 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H20\|VOL_HI15 | STATE | 0.2134 | 0.201 | 0.2029 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H3\|LAG1_10 | MEMORY | 0.2132 | 0.2726 | 0.02939 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H5\|VOL_HI5 | STATE | 0.2132 | 0.1986 | 0.05566 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H3\|DECAY5_10 | MEMORY | 0.2129 | 0.2069 | 0.02368 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.125\|H3\|HG10 | HG | 0.2129 | 0.2274 | 0.2167 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H20\|INV10 | MEMORY | 0.2128 | 0.1802 | 0.1994 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H10\|HG20 | HG | 0.2126 | 0.1768 | 0.2077 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2_CVRv5\|a0.125\|H10\|HG10 | HG | 0.2126 | 0.2132 | 0.06012 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H10\|VOL_HI5 | STATE | 0.212 | 0.2526 | 0.208 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H1\|NATIVE | SMOOTH | 0.212 | 0.2873 | 0.05898 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H10\|DECAY2_10 | MEMORY | 0.2106 | 0.2762 | 0.09135 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.125\|H5\|HG5 | HG | 0.2105 | 0.1543 | 0.1952 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_union3_v2_CVRv5\|a0.125\|H2\|HG10 | HG | 0.2104 | 0.2804 | 0.07283 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H10\|VOL_HI5 | STATE | 0.21 | 0.261 | 0.08466 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H5\|VOL_MEAN15 | STATE | 0.2095 | 0.2608 | 0.2017 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H10\|VOL_MEAN5 | STATE | 0.2093 | 0.2741 | 0.09248 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H10\|HG5 | HG | 0.209 | 0.2248 | 0.2051 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_union3_v2\|a0.125\|H10\|HG10 | HG | 0.2089 | 0.1776 | 0.1197 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H10\|DECAY2_10 | MEMORY | 0.2089 | 0.2485 | 0.09854 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.125\|H20\|HG15 | HG | 0.2087 | 0.1293 | 0.2047 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.25\|H20\|HG10 | HG | 0.2082 | 0.2139 | 0.2144 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H3\|HG10 | HG | 0.2081 | 0.2433 | 0.0138 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b_CVRv5\|a0.125\|H10\|HG10 | HG | 0.2079 | 0.205 | 0.2135 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H10\|LAG1_10 | MEMORY | 0.2079 | 0.1487 | 0.2105 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.25\|H20\|HG10 | HG | 0.2075 | 0.2098 | 0.195 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2\|a0.125\|H10\|NATIVE | SMOOTH | 0.2074 | 0.1829 | 0.2066 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H5\|HG5 | HG | 0.2071 | 0.1788 | 0.08089 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.125\|H20\|HG15 | HG | 0.2065 | 0.2048 | 0.2145 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.125\|H3\|HG15 | HG | 0.2065 | 0.1617 | 0.0004639 | 通过 | 不通过（e资本） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H5\|VOL_HI5 | STATE | 0.2057 | 0.2192 | 0.04422 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b_CVRv5\|a0.125\|H20\|HG10 | HG | 0.2053 | 0.2049 | 0.2083 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2\|a0.125\|H20\|HG10 | HG | 0.2052 | 0.2041 | 0.09376 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H10\|HG30 | HG | 0.2051 | 0.1107 | 0.0796 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H10\|HG30 | HG | 0.205 | 0.2044 | 0.07499 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.125\|H20\|HG15 | HG | 0.2049 | 0.1574 | 0.2146 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H5\|HG10 | HG | 0.2048 | 0.1648 | 0.02774 | 通过 | 不通过（e资本） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.2044 | 0.2201 | 0.02208 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H5\|HG10 | HG | 0.2035 | 0.1196 | 0.2094 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H20\|LAG1_10 | MEMORY | 0.2034 | 0.1962 | 0.2043 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b\|a0.125\|H10\|HG10 | HG | 0.2033 | 0.2636 | 0.2099 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2\|a0.125\|H10\|HG10 | HG | 0.2031 | 0.2213 | 0.00551 | 通过 | 不通过（e资本） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H20\|VOL_MEAN5 | STATE | 0.203 | 0.1785 | 0.203 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H10\|VOL_MEAN5 | STATE | 0.203 | 0.158 | 0.05628 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H10\|VOL_HI5 | STATE | 0.2029 | 0.1065 | 0.1156 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H10\|VOL_MEAN15 | STATE | 0.2024 | 0.2146 | 0.06186 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2_CVRv5\|a0.125\|H3\|HG10 | HG | 0.2019 | 0.1327 | 0.02453 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H20\|DECAY2_10 | MEMORY | 0.2012 | 0.1721 | 0.2019 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H20\|DECAY2_10 | MEMORY | 0.2009 | 0.2078 | 0.08269 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H5\|VOL_HI15 | STATE | 0.2006 | 0.2041 | 0.2067 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.125\|H20\|HG20 | HG | 0.2005 | 0.2238 | 0.1973 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H20\|VOL_HI15 | STATE | 0.2005 | 0.1591 | 0.2021 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.2004 | 0.226 | 0.01477 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H10\|HG30 | HG | 0.2001 | 0.2418 | 0.06919 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H10\|VOL_MEAN5 | STATE | 0.1997 | 0.1207 | 0.1239 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H5\|DECAY5_10 | MEMORY | 0.199 | 0.1282 | 0.2036 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H5\|VOL_HI15 | STATE | 0.1987 | 0.0662 | 0.1998 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H20\|VOL_HI15 | STATE | 0.1983 | 0.1439 | 0.1941 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H20\|VOL_HI15 | STATE | 0.1982 | 0.1842 | 0.2006 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H10\|HG10 | HG | 0.1981 | 0.2353 | 0.01089 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H3\|DECAY2_10 | MEMORY | 0.1979 | 0.2142 | 0.01487 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_union3_v2\|a0.125\|H10\|HG10 | HG | 0.1978 | 0.226 | 0.0009587 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H20\|HG20 | HG | 0.1974 | 0.2255 | 0.192 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H10\|HG5 | HG | 0.1974 | 0.2191 | 0.0894 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H5\|VOL_MEAN5 | STATE | 0.1973 | 0.2287 | 0.1851 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H5\|DECAY2_10 | MEMORY | 0.1972 | 0.2192 | 0.08499 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.125\|H10\|HG10 | HG | 0.197 | 0.2097 | 0.05892 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.125\|H20\|HG15 | HG | 0.1966 | 0.1698 | 0.1984 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.125\|H10\|NATIVE | SMOOTH | 0.1964 | 0.1457 | 0.1956 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.25\|H5\|VOL_MEAN15 | STATE | 0.1961 | 0.1914 | 0.1704 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H20\|DECAY5_10 | MEMORY | 0.1961 | 0.183 | 0.189 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H20\|HG15 | HG | 0.1958 | 0.1824 | 0.12 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H20\|DECAY2_10 | MEMORY | 0.1957 | 0.1741 | 0.1865 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H2\|HG5 | HG | 0.1953 | 0.2406 | 0.04016 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H10\|HG10 | HG | 0.195 | 0.1383 | 0.1251 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H5\|HG5 | HG | 0.1949 | 0.2045 | 0.2054 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H5\|LAG1_10 | MEMORY | 0.1949 | 0.2429 | 0.03306 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.125\|H3\|HG10 | HG | 0.1945 | 0.1811 | 0.08859 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H20\|DECAY5_10 | MEMORY | 0.1943 | 0.2025 | 0.0751 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H10\|VOL_MEAN5 | STATE | 0.194 | 0.2504 | 0.002918 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H3\|LAG1_10 | MEMORY | 0.1938 | 0.1926 | 0.01763 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1937 | 0.1826 | 0.1871 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H20\|INV10 | MEMORY | 0.1935 | 0.1808 | 0.1786 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.1935 | 0.2232 | -5.309e-05 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H20\|DECAY2_10 | MEMORY | 0.193 | 0.1759 | 0.1855 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.25\|H20\|HG10 | HG | 0.1929 | 0.1966 | 0.02703 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H20\|VOL_HI5 | STATE | 0.1928 | 0.1868 | 0.1855 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H10\|VOL_MEAN5 | STATE | 0.1928 | 0.1287 | 0.09757 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.125\|H10\|HG5 | HG | 0.1927 | 0.1293 | 0.1933 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H20\|LAG1_10 | MEMORY | 0.1926 | 0.1699 | 0.1796 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.25\|H20\|NATIVE | SMOOTH | 0.1923 | 0.192 | 0.1971 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2_CVRv5\|a0.125\|H10\|LAG1_10 | MEMORY | 0.1923 | 0.2376 | 0.002775 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|A4b\|a0.125\|H20\|HG10 | HG | 0.1923 | 0.221 | 0.1986 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2\|a0.25\|H20\|HG15 | HG | 0.1922 | 0.2612 | 0.0313 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H20\|VOL_MEAN15 | STATE | 0.1918 | 0.1914 | 0.09108 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1918 | 0.1969 | 0.1801 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H10\|VOL_HI15 | STATE | 0.1913 | 0.1863 | 0.1748 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H20\|DECAY5_10 | MEMORY | 0.1912 | 0.1444 | 0.1123 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H20\|LAG1_10 | MEMORY | 0.1911 | 0.1857 | 0.0862 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H20\|VOL_MEAN5 | STATE | 0.191 | 0.1775 | 0.1818 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.25\|H20\|NATIVE | SMOOTH | 0.1907 | 0.2036 | 0.178 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H20\|DECAY2_10 | MEMORY | 0.1905 | 0.1359 | 0.1116 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H10\|HG15 | HG | 0.1905 | 0.1835 | 0.01869 | 通过 | 不通过（e资本） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H10\|NATIVE | SMOOTH | 0.1904 | 0.1791 | 0.1842 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H10\|VOL_MEAN5 | STATE | 0.1903 | 0.1647 | 0.1901 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H3\|HG10 | HG | 0.1903 | 0.1553 | 0.004056 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H5\|LAG1_10 | MEMORY | 0.1902 | 0.1463 | 0.1941 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H10\|LAG1_10 | MEMORY | 0.1897 | 0.111 | 0.09754 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H10\|LAG1_10 | MEMORY | 0.1896 | 0.1809 | 0.1905 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H20\|DECAY2_10 | MEMORY | 0.1894 | 0.1695 | 0.1815 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.5\|H10\|LAG1_10 | MEMORY | 0.1892 | 0.2041 | 0.0895 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H20\|LAG1_10 | MEMORY | 0.189 | 0.1518 | 0.1108 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H20\|VOL_MEAN5 | STATE | 0.189 | 0.1775 | 0.07903 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H2\|HG5 | HG | 0.1888 | 0.1777 | 0.07013 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H10\|DECAY2_10 | MEMORY | 0.1887 | 0.128 | 0.098 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H20\|VOL_MEAN5 | STATE | 0.1884 | 0.1643 | 0.1802 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H10\|HG10 | HG | 0.1883 | 0.2103 | 0.05314 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H10\|HG15 | HG | 0.1882 | 0.2324 | 0.05441 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1881 | 0.1906 | 0.06928 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_union3_v2\|a0.125\|H20\|HG10 | HG | 0.1879 | 0.1851 | 0.1212 | 通过 | 通过 | PASS | 17 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H5\|VOL_MEAN15 | STATE | 0.1875 | 0.2071 | 0.06806 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H10\|LAG1_10 | MEMORY | 0.1875 | 0.2636 | 0.08084 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.125\|H20\|HG15 | HG | 0.1874 | 0.208 | 0.06693 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H10\|VOL_HI15 | STATE | 0.1873 | 0.1741 | 0.1867 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H20\|VOL_HI15 | STATE | 0.187 | 0.1713 | 0.1789 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H3\|DECAY5_10 | MEMORY | 0.1868 | 0.1382 | 0.007478 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H5\|VOL_HI5 | STATE | 0.1868 | 0.1734 | 0.08768 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.125\|H5\|HG5 | HG | 0.1868 | 0.2319 | -0.01664 | 不通过（e资本） | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H10\|DECAY5_10 | MEMORY | 0.1865 | 0.1282 | 0.0959 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.125\|H20\|HG15 | HG | 0.1863 | 0.1888 | 0.06202 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H5\|DECAY5_10 | MEMORY | 0.1863 | 0.2118 | 0.07627 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.1863 | 0.1377 | 0.1185 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H20\|HG10 | HG | 0.186 | 0.1796 | 0.175 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H20\|VOL_MEAN5 | STATE | 0.186 | 0.1748 | 0.188 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_mean3_v2\|a0.125\|H10\|VOL_HI15 | STATE | 0.1857 | 0.06022 | 0.1867 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H5\|HG10 | HG | 0.1853 | 0.1996 | 0.01197 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H10\|INV10 | MEMORY | 0.185 | 0.2194 | 0.1674 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_mean3_v2\|a0.125\|H5\|HG10 | HG | 0.185 | 0.09372 | 0.1885 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H10\|DECAY2_10 | MEMORY | 0.1847 | 0.1551 | 0.1864 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H5\|LAG1_10 | MEMORY | 0.1846 | 0.192 | 0.07465 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.125\|H10\|HG20 | HG | 0.1841 | 0.2031 | 0.1877 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|M_union3_v2\|a0.125\|H1\|NATIVE | SMOOTH | 0.184 | 0.1163 | 0.03698 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H10\|LAG1_10 | MEMORY | 0.184 | 0.1793 | 0.1794 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H20\|HG5 | HG | 0.1839 | 0.1652 | 0.1735 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H20\|LAG1_10 | MEMORY | 0.1838 | 0.188 | 0.1767 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H20\|DECAY5_10 | MEMORY | 0.1836 | 0.151 | 0.1837 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H10\|VOL_HI5 | STATE | 0.1834 | 0.2344 | 0.1839 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H20\|DECAY5_10 | MEMORY | 0.1833 | 0.1445 | 0.1753 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2_CVRv5\|a0.125\|H2\|NATIVE | SMOOTH | 0.1828 | 0.1939 | 0.1745 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H10\|HG5 | HG | 0.1822 | 0.1359 | 0.1841 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H10\|HG10 | HG | 0.1815 | 0.2392 | 0.1773 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.125\|H10\|HG10 | HG | 0.1815 | 0.1769 | 0.09875 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|M_union3_v2\|a0.125\|H10\|VOL_HI5 | STATE | 0.1814 | 0.2108 | 0.005714 | 通过 | 不通过（e资本） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.25\|H20\|NATIVE | SMOOTH | 0.1813 | 0.1583 | 0.1838 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H5\|HG30 | HG | 0.1813 | 0.2638 | 0.1783 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H20\|INV10 | MEMORY | 0.1812 | 0.1429 | 0.1691 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|A4b_CVRv5\|a0.125\|H10\|HG10 | HG | 0.1811 | 0.2082 | 0.1689 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H20\|VOL_MEAN5 | STATE | 0.1809 | 0.1402 | 0.1011 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b\|a0.25\|H20\|HG10 | HG | 0.1808 | 0.2134 | 0.1894 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H20\|HG10 | HG | 0.1808 | 0.1533 | 0.181 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H20\|VOL_MEAN5 | STATE | 0.1806 | 0.1373 | 0.1773 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H10\|VOL_HI5 | STATE | 0.1798 | 0.1396 | 0.04808 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H20\|VOL_MEAN15 | STATE | 0.1795 | 0.1185 | 0.1077 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.25\|H20\|HG15 | HG | 0.1795 | 0.2204 | -0.005291 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.1793 | 0.1392 | 0.1102 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H10\|LAG1_10 | MEMORY | 0.1787 | 0.1179 | 0.1101 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H5\|DECAY2_10 | MEMORY | 0.1786 | 0.167 | 0.07341 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H20\|VOL_MEAN15 | STATE | 0.1786 | 0.1416 | 0.1715 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H20\|LAG1_10 | MEMORY | 0.1785 | 0.1706 | 0.1803 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H20\|HG15 | HG | 0.1784 | 0.1991 | 0.05112 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.1784 | 0.2014 | 0.1868 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.125\|H10\|HG5 | HG | 0.1781 | 0.1572 | 0.1758 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H5\|DECAY2_10 | MEMORY | 0.1777 | 0.2072 | 0.01562 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.25\|H20\|HG5 | HG | 0.1777 | 0.2121 | 0.164 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H10\|INV10 | MEMORY | 0.1774 | 0.1507 | 0.1504 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H20\|VOL_MEAN15 | STATE | 0.1773 | 0.1323 | 0.1772 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H3\|HG5 | HG | 0.1772 | 0.1049 | 0.04407 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.125\|H5\|HG10 | HG | 0.1771 | 0.1237 | 0.07241 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H20\|HG20 | HG | 0.1768 | 0.1661 | 0.07543 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H3\|DECAY2_10 | MEMORY | 0.1764 | 0.1287 | 0.002416 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H5\|VOL_MEAN5 | STATE | 0.1753 | 0.1416 | 0.06647 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H2\|VOL_MEAN15 | STATE | 0.1752 | 0.2144 | 0.09709 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H20\|DECAY5_10 | MEMORY | 0.1751 | 0.1653 | 0.167 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_mean3_v2_CVRv5\|a0.125\|H20\|HG10 | HG | 0.175 | 0.1459 | 0.1767 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2\|a0.125\|H10\|HG10 | HG | 0.1749 | 0.08113 | 0.1773 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H20\|HG20 | HG | 0.1749 | 0.165 | 0.07242 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2\|a0.125\|H10\|HG5 | HG | 0.1749 | 0.09227 | 0.1797 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.1749 | 0.2021 | 0.1689 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H20\|LAG1_10 | MEMORY | 0.1749 | 0.1442 | 0.1701 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.25\|H20\|NATIVE | SMOOTH | 0.1747 | 0.1844 | 0.1641 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H10\|HG10 | HG | 0.1746 | 0.1805 | 0.1843 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.125\|H20\|DECAY5_10 | MEMORY | 0.1746 | 0.1641 | 0.1764 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H20\|VOL_HI5 | STATE | 0.1745 | 0.1262 | 0.1738 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H20\|VOL_MEAN15 | STATE | 0.174 | 0.1785 | 0.168 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.125\|H10\|VOL_HI15 | STATE | 0.174 | 0.1613 | 0.1704 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.1738 | 0.1922 | 0.04177 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.1738 | 0.2214 | 0.1695 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H20\|HG10 | HG | 0.1734 | 0.1627 | 0.1655 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H20\|HG5 | HG | 0.173 | 0.1196 | 0.1721 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|A4b_CVRv5\|a0.125\|H10\|HG10 | HG | 0.1729 | 0.2023 | 0.1621 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H10\|VOL_HI5 | STATE | 0.1728 | 0.2087 | 0.1681 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.1728 | 0.1966 | 0.04332 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.1727 | 0.1869 | 0.1814 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H10\|LAG1_10 | MEMORY | 0.1722 | 0.1915 | 0.1624 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H10\|VOL_MEAN5 | STATE | 0.1719 | 0.156 | 0.1648 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H20\|HG5 | HG | 0.1717 | 0.157 | 0.1745 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H20\|VOL_HI5 | STATE | 0.1715 | 0.1858 | 0.1648 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H10\|LAG1_10 | MEMORY | 0.1713 | 0.1481 | 0.1765 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H10\|HG10 | HG | 0.1713 | 0.1978 | 0.0231 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.125\|H20\|HG10 | HG | 0.1712 | 0.1659 | 0.1727 | 通过 | 通过 | PASS | 16 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.5\|H20\|VOL_MEAN15 | STATE | 0.1708 | 0.1441 | 0.1625 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.25\|H20\|HG5 | HG | 0.1707 | 0.1909 | 0.1543 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b_CVRv5\|a0.25\|H3\|NATIVE | SMOOTH | 0.1706 | 0.1656 | 0.1813 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H20\|VOL_HI15 | STATE | 0.1704 | 0.1182 | 0.1677 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H10\|VOL_HI5 | STATE | 0.1702 | 0.1087 | 0.09428 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2_CVRv5\|a0.125\|H5\|HG10 | HG | 0.1702 | 0.1655 | 0.03852 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H10\|HG20 | HG | 0.1701 | 0.1582 | 0.1761 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.25\|H20\|NATIVE | SMOOTH | 0.17 | 0.1683 | 0.1636 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2_CVRv5\|a0.25\|H20\|HG15 | HG | 0.17 | 0.2346 | -0.00532 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|A4b\|a0.125\|H20\|HG10 | HG | 0.17 | 0.1823 | 0.1745 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_union3_v2_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1699 | 0.1722 | 0.05065 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.125\|H10\|VOL_HI5 | STATE | 0.1698 | 0.1009 | 0.16 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b\|a0.125\|H20\|LAG1_10 | MEMORY | 0.1697 | 0.1701 | 0.1723 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2_CVRv5\|a0.125\|H5\|HG10 | HG | 0.1696 | 0.1455 | 0.06649 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.1696 | 0.1892 | 0.1651 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.25\|H20\|HG15 | HG | 0.1693 | 0.2543 | -0.01491 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|A4b\|a0.125\|H10\|HG10 | HG | 0.1692 | 0.1898 | 0.1749 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.25\|H20\|HG10 | HG | 0.1688 | 0.1949 | 0.04924 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H5\|LAG1_10 | MEMORY | 0.1685 | 0.09928 | 0.1733 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H10\|LAG1_10 | MEMORY | 0.1681 | 0.1861 | 0.04411 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.1676 | 0.2308 | 0.1634 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H5\|DECAY5_10 | MEMORY | 0.1674 | 0.1623 | 0.06242 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.1673 | 0.1371 | 0.1627 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H20\|VOL_HI15 | STATE | 0.1666 | 0.1043 | 0.09459 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H20\|VOL_MEAN15 | STATE | 0.1666 | 0.1036 | 0.1596 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H20\|LAG1_10 | MEMORY | 0.1665 | 0.1618 | 0.1594 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H20\|DECAY2_10 | MEMORY | 0.1665 | 0.12 | 0.1593 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H20\|HG10 | HG | 0.1662 | 0.1431 | 0.1666 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1661 | 0.1265 | 0.1584 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2\|a0.125\|H10\|HG10 | HG | 0.1659 | 0.2012 | 0.05664 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_mean3_v2\|a0.125\|H20\|HG5 | HG | 0.1657 | 0.121 | 0.1666 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H10\|HG5 | HG | 0.165 | 0.1599 | 0.07184 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H20\|DECAY5_10 | MEMORY | 0.1643 | 0.1176 | 0.157 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H20\|DECAY2_10 | MEMORY | 0.164 | 0.1679 | 0.169 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.25\|H20\|HG5 | HG | 0.1638 | 0.1658 | 0.1692 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1635 | 0.1507 | 0.1569 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H10\|VOL_HI5 | STATE | 0.163 | 0.1955 | 0.1678 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2\|a0.125\|H20\|VOL_MEAN15 | STATE | 0.1629 | 0.1172 | 0.1619 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H10\|DECAY5_10 | MEMORY | 0.1628 | 0.1298 | 0.1646 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW5\|M_mean3_v2\|a0.125\|H10\|NATIVE | SMOOTH | 0.1628 | 0.1098 | 0.1658 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H20\|DECAY5_10 | MEMORY | 0.1625 | 0.1702 | 0.1678 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.25\|H10\|HG20 | HG | 0.1624 | 0.1781 | 0.1636 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H20\|LAG1_10 | MEMORY | 0.1618 | 0.1201 | 0.08491 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H20\|DECAY2_10 | MEMORY | 0.1615 | 0.128 | 0.1623 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H10\|LAG1_10 | MEMORY | 0.1615 | 0.1927 | 0.1559 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H20\|HG20 | HG | 0.1601 | 0.1565 | 0.07498 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.125\|H10\|HG10 | HG | 0.1601 | 0.1712 | 0.1516 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H20\|HG10 | HG | 0.1598 | 0.1744 | 0.1651 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | M\|M_union3_v2\|a0.125\|H5\|HG10 | HG | 0.1596 | 0.1759 | 0.04321 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H5\|HG10 | HG | 0.1596 | 0.1642 | -0.0186 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H20\|DECAY2_10 | MEMORY | 0.1594 | 0.1606 | 0.1646 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D10\|A4b\|a0.125\|H20\|HG10 | HG | 0.1591 | 0.1516 | 0.1654 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H20\|DECAY5_10 | MEMORY | 0.1588 | 0.1131 | 0.08197 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H20\|DECAY2_10 | MEMORY | 0.1587 | 0.1137 | 0.08207 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H20\|VOL_MEAN15 | STATE | 0.1586 | 0.1292 | 0.1632 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.125\|H20\|HG10 | HG | 0.1585 | 0.168 | 0.06301 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2\|a0.125\|H2\|HG5 | HG | 0.158 | 0.1634 | 0.02451 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H20\|LAG1_10 | MEMORY | 0.1579 | 0.1638 | 0.1616 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H20\|VOL_MEAN5 | STATE | 0.1579 | 0.1403 | 0.1015 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H20\|HG10 | HG | 0.1575 | 0.1622 | 0.1044 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H20\|HG10 | HG | 0.1573 | 0.1494 | 0.1622 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H20\|VOL_HI5 | STATE | 0.1571 | 0.1458 | 0.08328 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H20\|DECAY5_10 | MEMORY | 0.1567 | 0.1322 | 0.1571 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H5\|VOL_HI5 | STATE | 0.1566 | 0.1359 | 0.05845 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.5\|H10\|VOL_HI15 | STATE | 0.1564 | 0.221 | 0.05228 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H5\|HG10 | HG | 0.1564 | 0.04485 | 0.1616 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.25\|H20\|NATIVE | SMOOTH | 0.1564 | 0.1794 | 0.1602 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b_CVRv5\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.1563 | 0.1269 | 0.1517 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1562 | 0.1595 | 0.1532 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H20\|HG5 | HG | 0.1562 | 0.1223 | 0.1589 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H20\|HG30 | HG | 0.1558 | 0.1376 | 0.05112 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H20\|INV10 | MEMORY | 0.1556 | 0.1493 | 0.1372 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_union3_v2_CVRv5\|a0.125\|H2\|HG5 | HG | 0.1555 | 0.202 | -0.03121 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H20\|HG15 | HG | 0.155 | 0.1308 | 0.1561 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H20\|LAG1_10 | MEMORY | 0.155 | 0.147 | 0.04415 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H10\|VOL_MEAN15 | STATE | 0.1549 | 0.1414 | 0.1547 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.25\|H20\|HG30 | HG | 0.1546 | 0.1241 | 0.05071 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.125\|H10\|VOL_MEAN15 | STATE | 0.1546 | 0.09203 | 0.1469 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H20\|VOL_MEAN5 | STATE | 0.1545 | 0.1428 | 0.1587 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H10\|VOL_MEAN15 | STATE | 0.1545 | 0.07855 | 0.06833 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b\|a0.125\|H20\|HG10 | HG | 0.1545 | 0.1387 | 0.1592 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b\|a0.125\|H20\|DECAY5_10 | MEMORY | 0.1539 | 0.1384 | 0.1585 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H10\|VOL_MEAN5 | STATE | 0.1538 | 0.09538 | 0.156 | 通过 | 不通过（正向门槛） | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|A4b_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1532 | 0.1346 | 0.1438 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H20\|VOL_MEAN5 | STATE | 0.1527 | 0.1192 | 0.07405 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H20\|VOL_HI15 | STATE | 0.1524 | 0.1531 | 0.1465 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H10\|HG5 | HG | 0.1522 | 0.1811 | 0.04308 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D5\|A4b_CVRv5\|a0.125\|H10\|INV10 | MEMORY | 0.1521 | 0.1193 | 0.1253 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.125\|H10\|VOL_MEAN5 | STATE | 0.152 | 0.1315 | 0.1438 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H20\|DECAY5_10 | MEMORY | 0.1515 | 0.1558 | 0.09848 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b\|a0.125\|H20\|HG10 | HG | 0.1513 | 0.1856 | 0.1533 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2\|a0.125\|H10\|NATIVE | SMOOTH | 0.1511 | 0.1061 | 0.1546 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|A4b\|a0.125\|H20\|INV10 | MEMORY | 0.1511 | 0.1308 | 0.1518 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H20\|HG15 | HG | 0.151 | 0.1458 | 0.01723 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H10\|VOL_MEAN15 | STATE | 0.1506 | 0.1175 | 0.08602 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H20\|LAG1_10 | MEMORY | 0.1502 | 0.1592 | 0.145 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.25\|H10\|VOL_MEAN15 | STATE | 0.15 | 0.1546 | 0.1488 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | S\|M_mean3_v2_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1495 | 0.1006 | 0.1506 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2_CVRv5\|a0.125\|H3\|HG10 | HG | 0.1489 | 0.1026 | 0.04133 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2_CVRv5\|a0.125\|H20\|VOL_MEAN15 | STATE | 0.1488 | 0.1458 | 0.04018 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.125\|H20\|HG5 | HG | 0.1485 | 0.1596 | 0.1437 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H5\|INV10 | MEMORY | 0.1484 | 0.04055 | 0.1487 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H20\|DECAY2_10 | MEMORY | 0.148 | 0.1538 | 0.1434 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_mean3_v2\|a0.125\|H20\|HG15 | HG | 0.1478 | 0.09309 | 0.1449 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2\|a0.125\|H20\|HG10 | HG | 0.1474 | 0.1541 | 0.04223 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|A4b\|a0.125\|H20\|HG10 | HG | 0.1469 | 0.1716 | 0.1486 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H20\|HG15 | HG | 0.1468 | 0.1655 | 0.01217 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H10\|LAG1_10 | MEMORY | 0.1462 | 0.1825 | 0.1498 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1461 | 0.1331 | 0.1349 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_union3_v2_CVRv5\|a0.125\|H20\|HG15 | HG | 0.146 | 0.178 | -0.01928 | 不通过（e资本） | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|A4b_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1455 | 0.1557 | 0.1318 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H20\|VOL_HI5 | STATE | 0.1455 | 0.1242 | 0.04504 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2_CVRv5\|a0.125\|H20\|HG15 | HG | 0.1447 | 0.1648 | 0.01877 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H20\|VOL_MEAN15 | STATE | 0.1441 | 0.08545 | 0.07274 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2\|a0.125\|H5\|HG10 | HG | 0.1441 | 0.1337 | 0.007655 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_mean3_v2\|a0.125\|H5\|NATIVE | SMOOTH | 0.1441 | 0.1214 | 0.1463 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|A4b_CVRv5\|a0.125\|H10\|VOL_MEAN15 | STATE | 0.1441 | 0.1496 | 0.1397 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|M_mean3_v2\|a0.125\|H20\|HG15 | HG | 0.144 | 0.1161 | 0.1436 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.125\|H20\|HG5 | HG | 0.144 | 0.1423 | 0.131 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2_CVRv5\|a0.125\|H10\|HG10 | HG | 0.1439 | 0.1732 | 0.03209 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H5\|VOL_MEAN5 | STATE | 0.1438 | 0.1482 | 0.05711 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|M_union3_v2\|a0.125\|H3\|HG10 | HG | 0.1436 | 0.06947 | 0.005149 | 通过 | 不通过（正向门槛、e资本） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.25\|H20\|VOL_HI15 | STATE | 0.1435 | 0.08473 | 0.07203 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H10\|VOL_HI15 | STATE | 0.1426 | 0.08433 | 0.07408 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.1425 | 0.1066 | 0.1371 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.1422 | 0.1148 | 0.1359 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H20\|DECAY5_10 | MEMORY | 0.1421 | 0.1425 | 0.138 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.125\|H20\|HG10 | HG | 0.141 | 0.174 | 0.1468 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2_CVRv5\|a0.25\|H20\|HG10 | HG | 0.1408 | 0.1665 | 0.01488 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H20\|DECAY2_10 | MEMORY | 0.1406 | 0.1458 | 0.08788 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b_CVRv5\|a0.125\|H10\|HG5 | HG | 0.1401 | 0.1614 | 0.13 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.125\|H10\|INV10 | MEMORY | 0.1399 | 0.07364 | 0.135 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.25\|H20\|VOL_MEAN5 | STATE | 0.1395 | 0.1647 | 0.1345 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.125\|H10\|HG10 | HG | 0.1387 | 0.08439 | 0.1321 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|A4b\|a0.125\|H20\|HG10 | HG | 0.1385 | 0.1272 | 0.1403 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H2\|VOL_MEAN15 | STATE | 0.1383 | 0.1628 | 0.06492 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H20\|HG15 | HG | 0.1383 | 0.1078 | 0.1398 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b\|a0.125\|H10\|HG5 | HG | 0.1376 | 0.1154 | 0.1399 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H20\|LAG1_10 | MEMORY | 0.1374 | 0.1151 | 0.1392 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H10\|VOL_MEAN5 | STATE | 0.1368 | 0.06675 | 0.06606 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.125\|H20\|HG5 | HG | 0.136 | 0.1154 | 0.1343 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_union3_v2_CVRv5\|a0.125\|H20\|HG10 | HG | 0.136 | 0.1528 | 0.03231 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H5\|VOL_MEAN5 | STATE | 0.1347 | 0.1302 | 0.05831 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H20\|LAG1_10 | MEMORY | 0.1325 | 0.1529 | 0.1359 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H5\|LAG1_10 | MEMORY | 0.1323 | 0.1336 | 0.05413 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H20\|VOL_HI15 | STATE | 0.1322 | 0.1306 | 0.0783 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_union3_v2\|a0.125\|H20\|HG10 | HG | 0.1299 | 0.1412 | 0.04618 | 通过 | 通过 | PASS | 15 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.25\|H10\|VOL_MEAN5 | STATE | 0.1297 | 0.1199 | 0.1317 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H5\|HG10 | HG | 0.1292 | 0.159 | 0.05063 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b\|a0.125\|H20\|HG5 | HG | 0.1286 | 0.1511 | 0.132 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H20\|HG20 | HG | 0.1282 | 0.1289 | 0.04265 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H20\|HG5 | HG | 0.1272 | 0.1317 | 0.124 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H20\|VOL_HI5 | STATE | 0.1269 | 0.1265 | 0.0675 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_union3_v2\|a0.125\|H20\|HG5 | HG | 0.1261 | 0.1181 | 0.0483 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_mean3_v2\|a0.125\|H20\|NATIVE | SMOOTH | 0.1259 | 0.08829 | 0.1245 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_union3_v2_CVRv5\|a0.125\|H5\|HG10 | HG | 0.1248 | 0.1329 | -0.008698 | 不通过（e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DEW3\|A4b\|a0.125\|H20\|HG5 | HG | 0.1243 | 0.1499 | 0.1258 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H5\|DECAY5_10 | MEMORY | 0.124 | 0.1472 | 0.0448 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H10\|LAG1_10 | MEMORY | 0.1229 | 0.05938 | 0.06111 | 通过 | 不通过（正向门槛） | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H5\|DECAY2_10 | MEMORY | 0.1219 | 0.155 | 0.04282 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H10\|DECAY5_10 | MEMORY | 0.1216 | 0.08239 | 0.05861 | 通过 | 不通过（正向门槛） | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H20\|LAG1_10 | MEMORY | 0.1216 | 0.1483 | 0.1204 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_DMED5\|A4b_CVRv5\|a0.25\|H20\|HG5 | HG | 0.1215 | 0.1255 | 0.1104 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H20\|LAG1_10 | MEMORY | 0.1208 | 0.1358 | 0.07132 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2\|a0.125\|H20\|HG5 | HG | 0.1193 | 0.06987 | 0.12 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H20\|VOL_MEAN5 | STATE | 0.1191 | 0.1084 | 0.06474 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|M_union3_v2_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1188 | 0.1282 | 0.003328 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H20\|VOL_HI5 | STATE | 0.1187 | 0.06524 | 0.1203 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H20\|HG10 | HG | 0.1186 | 0.1516 | 0.02183 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H20\|DECAY2_10 | MEMORY | 0.1184 | 0.07806 | 0.1203 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|A4b_CVRv5\|a0.125\|H20\|NATIVE | SMOOTH | 0.1175 | 0.1044 | 0.11 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b\|a0.125\|H20\|HG10 | HG | 0.1175 | 0.1395 | 0.1182 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H20\|VOL_MEAN15 | STATE | 0.1173 | 0.1251 | 0.06625 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.25\|H10\|VOL_HI15 | STATE | 0.1172 | 0.1004 | 0.1203 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|A4b_CVRv5\|a0.125\|H10\|HG5 | HG | 0.1171 | 0.144 | 0.1182 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H20\|VOL_MEAN5 | STATE | 0.1161 | 0.09222 | 0.1198 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H10\|DECAY2_10 | MEMORY | 0.1158 | 0.083 | 0.05226 | 通过 | 不通过（正向门槛） | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H10\|VOL_HI5 | STATE | 0.1154 | 0.05565 | 0.04461 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H10\|VOL_HI15 | STATE | 0.1151 | 0.1134 | 0.1204 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|A4b_CVRv5\|a0.25\|H20\|NATIVE | SMOOTH | 0.1148 | 0.1407 | 0.1089 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.25\|H20\|HG20 | HG | 0.1142 | 0.1666 | 0.1116 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2\|a0.125\|H3\|HG10 | HG | 0.1135 | 0.09203 | 0.02392 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_QMEAN5\|A4b_CVRv5\|a0.125\|H20\|HG5 | HG | 0.1125 | 0.1372 | 0.1084 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H20\|DECAY5_10 | MEMORY | 0.1101 | 0.1397 | 0.01406 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H5\|LAG1_10 | MEMORY | 0.1096 | 0.09126 | 0.04162 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b\|a0.125\|H20\|HG5 | HG | 0.1095 | 0.1256 | 0.1112 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_mean3_v2\|a0.125\|H10\|NATIVE | SMOOTH | 0.1081 | 0.09305 | 0.1083 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.125\|H20\|VOL_HI15 | STATE | 0.1081 | 0.1238 | 0.1046 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H20\|INV10 | MEMORY | 0.1081 | 0.09386 | 0.1035 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H5\|VOL_HI15 | STATE | 0.1078 | 0.1361 | 0.05426 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H20\|VOL_HI15 | STATE | 0.1072 | 0.1162 | 0.05523 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK3\|M_mean3_v2_CVRv5\|a0.125\|H20\|HG15 | HG | 0.107 | 0.07339 | 0.1137 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H20\|DECAY2_10 | MEMORY | 0.107 | 0.1165 | 0.05663 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H20\|HG20 | HG | 0.1056 | 0.1044 | 0.1042 | 通过 | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H20\|DECAY2_10 | MEMORY | 0.1054 | 0.1434 | 0.01052 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKOBS5\|M_union3_v2_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1048 | 0.1215 | 0.01763 | 通过 | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_D3\|M_mean3_v2\|a0.125\|H20\|HG10 | HG | 0.1047 | 0.0493 | 0.1071 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H20\|DECAY5_10 | MEMORY | 0.1028 | 0.05865 | 0.1047 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2\|a0.125\|H20\|VOL_MEAN15 | STATE | 0.1026 | 0.07816 | 0.09623 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q0\|M_mean3_v2_CVRv5\|a0.125\|H20\|HG10 | HG | 0.1024 | 0.06305 | 0.1044 | 通过 | 不通过（正向门槛） | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANKSCORE5\|M_union3_v2\|a0.125\|H20\|HG10 | HG | 0.1022 | 0.1088 | 0.04151 | 通过 | 通过 | PASS | 14 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK10\|A4b_CVRv5\|a0.125\|H10\|HG5 | HG | 0.1002 | 0.09453 | 0.1005 | 通过 | 不通过（正向门槛） | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_mean3_v2_CVRv5\|a0.5\|H20\|VOL_HI5 | STATE | 0.0993 | 0.1286 | 0.09791 | 不通过（正向门槛） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2_CVRv5\|a0.125\|H20\|HG10 | HG | 0.0984 | 0.1252 | -0.004146 | 不通过（正向门槛、e资本） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | Q_RANK5\|M_union3_v2\|a0.125\|H20\|LAG1_10 | MEMORY | 0.09755 | 0.1191 | 0.005141 | 不通过（正向门槛） | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H5\|DECAY5_10 | MEMORY | 0.09679 | 0.1122 | 0.02568 | 不通过（正向门槛） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H20\|LAG1_10 | MEMORY | 0.0947 | 0.1032 | 0.04828 | 不通过（正向门槛） | 通过 | PASS | 13 | NOT_AUTHORIZED | False |
| 本轮新证据（首评，重复使用的历史） | C1\|M_union3_v2_CVRv5\|a0.125\|H5\|DECAY2_10 | MEMORY | 0.09236 | 0.1107 | 0.02395 | 不通过（正向门槛） | 通过 | PASS | 12 | NOT_AUTHORIZED | False |


## 4. 边缘清单（全部条件距离；主展示 72 + 剂量 72）

> 表头：主体=条件距离（c / f：min 段 D + .10；正向：FULL − .10；d：正年 − 12；e随机：min 后段 rmr − 2·MCSE；PORT3：离 ±3 的最小距离）｜算子=主展示 + 剂量｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父（8bp）｜子集=primary72 | dose72｜单位=ann_pp / 年数 / pct_pt｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-P3-EDGE


| desc_id | policy_PROPOSED_PORT3_T_FULL | edge_c_margin_ann_pp | edge_f_margin_ann_pp | edge_positive_margin_FULL_ann_pp | edge_years_margin | edge_erand_margin_ann_pp | edge_port3_margin_pct_pt |
|---|---|---|---|---|---|---|---|
| Q0\|A4b\|a0.25\|H5\|DECAY5_10 | 通过 | 0.4055 | 0.497 | 0.432 | 2 | 0.4962 | 0.5809 |
| Q0\|A4b\|a0.25\|H5\|HG10 | 通过 | 0.4257 | 0.5135 | 0.4279 | 2 | 0.5133 | 0.5944 |
| Q0\|A4b\|a0.25\|H5\|INV10 | 不通过（d） | 0.04021 | 0.2249 | 0.2438 | -1 | 0.2386 | 0.7084 |
| Q0\|A4b\|a0.25\|H5\|LAG1_10 | 通过 | 0.4401 | 0.5339 | 0.3889 | 2 | 0.4945 | 0.6629 |
| Q0\|A4b\|a0.25\|H5\|NATIVE | 通过 | 0.05596 | 0.1298 | 0.2631 | 0 | 0.172 | 1.19 |
| Q0\|A4b\|a0.5\|H5\|DECAY5_10 | 不通过（size(PROPOSED_PORT3_T)） | 0.4455 | 0.793 | 1.331 | 3 | 2.708 | -2.756 |
| Q0\|A4b\|a0.5\|H5\|HG10 | 不通过（size(PROPOSED_PORT3_T)） | 0.4298 | 0.7809 | 1.272 | 3 | 2.604 | -2.837 |
| Q0\|A4b\|a0.5\|H5\|INV10 | 不通过（size(PROPOSED_PORT3_T)） | 0.1918 | 0.6435 | 0.86 | 1 | 1.444 | -0.8167 |
| Q0\|A4b\|a0.5\|H5\|LAG1_10 | 不通过（size(PROPOSED_PORT3_T)） | 0.2383 | 0.54 | 1.116 | 3 | 2.259 | -1.778 |
| Q0\|A4b\|a0.5\|H5\|NATIVE | 不通过（c） | -0.3057 | 0.2133 | 0.9089 | 3 | 1.491 | 0.3373 |
| Q0\|A4b_CVRv5\|a0.25\|H5\|DECAY5_10 | 通过 | 0.4705 | 0.5149 | 0.419 | 2 | 0.3474 | 0.6557 |
| Q0\|A4b_CVRv5\|a0.25\|H5\|HG10 | 通过 | 0.4626 | 0.5367 | 0.4176 | 1 | 0.3425 | 0.6709 |
| Q0\|A4b_CVRv5\|a0.25\|H5\|INV10 | 不通过（d） | 0.1491 | 0.3095 | 0.2381 | -1 | 0.1618 | 0.8405 |
| Q0\|A4b_CVRv5\|a0.25\|H5\|LAG1_10 | 通过 | 0.4163 | 0.4907 | 0.3819 | 1 | 0.3006 | 0.734 |
| Q0\|A4b_CVRv5\|a0.25\|H5\|NATIVE | 通过 | 0.2528 | 0.301 | 0.2638 | 0 | 0.2997 | 1.272 |
| Q0\|A4b_CVRv5\|a0.5\|H5\|DECAY5_10 | 不通过（size(PROPOSED_PORT3_T)） | 0.279 | 0.4924 | 1.064 | 1 | 2.349 | -2.592 |
| Q0\|A4b_CVRv5\|a0.5\|H5\|HG10 | 不通过（size(PROPOSED_PORT3_T)） | 0.2504 | 0.4695 | 1.009 | 1 | 2.186 | -2.676 |
| Q0\|A4b_CVRv5\|a0.5\|H5\|INV10 | 不通过（d、size(PROPOSED_PORT3_T)） | 0.05472 | 0.2812 | 0.6354 | -1 | 1.493 | -0.4361 |
| Q0\|A4b_CVRv5\|a0.5\|H5\|LAG1_10 | 不通过（size(PROPOSED_PORT3_T)） | 0.1327 | 0.3066 | 0.8569 | 2 | 1.894 | -1.595 |
| Q0\|A4b_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、f） | -0.8405 | -0.4026 | 0.5671 | 2 | 0.8937 | 0.5154 |
| Q0\|M_mean3_v2\|a0.25\|H5\|DECAY5_10 | 不通过（c、d） | -0.0251 | 0.2133 | 0.2009 | -4 | 0.2421 | 2.594 |
| Q0\|M_mean3_v2\|a0.25\|H5\|HG10 | 不通过（c、d） | -0.03194 | 0.209 | 0.1922 | -3 | 0.2496 | 2.587 |
| Q0\|M_mean3_v2\|a0.25\|H5\|INV10 | 不通过（d） | 0.005553 | 0.1976 | 0.2861 | -2 | 0.3179 | 2.589 |
| Q0\|M_mean3_v2\|a0.25\|H5\|LAG1_10 | 不通过（c、d） | -0.1003 | 0.1287 | 0.1472 | -3 | 0.2763 | 2.587 |
| Q0\|M_mean3_v2\|a0.25\|H5\|NATIVE | 不通过（c、d、f） | -0.1545 | -0.007544 | 0.218 | -2 | 0.1402 | 2.533 |
| Q0\|M_mean3_v2\|a0.5\|H5\|DECAY5_10 | 不通过（c、d、f） | -0.5142 | -0.2354 | 0.2004 | -4 | 0.2435 | 1.716 |
| Q0\|M_mean3_v2\|a0.5\|H5\|HG10 | 不通过（c、d、f） | -0.4331 | -0.1531 | 0.2248 | -4 | 0.326 | 1.717 |
| Q0\|M_mean3_v2\|a0.5\|H5\|INV10 | 不通过（c、d、f） | -0.3952 | -0.08262 | 0.2716 | -4 | 0.4031 | 1.687 |
| Q0\|M_mean3_v2\|a0.5\|H5\|LAG1_10 | 不通过（c、d、f） | -0.441 | -0.1666 | 0.2272 | -5 | 0.3228 | 1.69 |
| Q0\|M_mean3_v2\|a0.5\|H5\|NATIVE | 不通过（c、d、f） | -0.4769 | -0.2064 | 0.2136 | -4 | 0.3239 | 1.603 |
| Q0\|M_mean3_v2_CVRv5\|a0.25\|H5\|DECAY5_10 | 不通过（c、d、f、正向门槛） | -0.2443 | -0.08708 | -0.1564 | -6 | 0.2207 | 2.599 |
| Q0\|M_mean3_v2_CVRv5\|a0.25\|H5\|HG10 | 不通过（c、d、f、正向门槛） | -0.2242 | -0.06467 | -0.153 | -6 | 0.2366 | 2.595 |
| Q0\|M_mean3_v2_CVRv5\|a0.25\|H5\|INV10 | 不通过（c、d、正向门槛） | -0.1518 | 0.00196 | -0.1985 | -6 | 0.2209 | 2.524 |
| Q0\|M_mean3_v2_CVRv5\|a0.25\|H5\|LAG1_10 | 不通过（c、d、f、正向门槛） | -0.3573 | -0.2052 | -0.2062 | -6 | 0.2449 | 2.591 |
| Q0\|M_mean3_v2_CVRv5\|a0.25\|H5\|NATIVE | 不通过（c、d、f、正向门槛） | -0.3543 | -0.1893 | -0.1952 | -7 | 0.02355 | 2.535 |
| Q0\|M_mean3_v2_CVRv5\|a0.5\|H5\|DECAY5_10 | 不通过（c、d、f、正向门槛） | -0.8005 | -0.4991 | -0.362 | -7 | 0.182 | 1.736 |
| Q0\|M_mean3_v2_CVRv5\|a0.5\|H5\|HG10 | 不通过（c、d、f、正向门槛） | -0.75 | -0.4472 | -0.3462 | -7 | 0.2347 | 1.738 |
| Q0\|M_mean3_v2_CVRv5\|a0.5\|H5\|INV10 | 不通过（c、d、f、正向门槛） | -0.709 | -0.4347 | -0.3326 | -7 | 0.4586 | 1.633 |
| Q0\|M_mean3_v2_CVRv5\|a0.5\|H5\|LAG1_10 | 不通过（c、d、f、正向门槛） | -0.6973 | -0.3997 | -0.3297 | -7 | 0.2924 | 1.708 |
| Q0\|M_mean3_v2_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、d、f、正向门槛） | -0.7442 | -0.4455 | -0.3494 | -7 | 0.2709 | 1.611 |
| Q0\|M_union3_v2\|a0.25\|H5\|DECAY5_10 | 通过 | 0.2798 | 0.1439 | 0.3686 | 2 | 0.3237 | 2.359 |
| Q0\|M_union3_v2\|a0.25\|H5\|HG10 | 通过 | 0.3038 | 0.1697 | 0.4354 | 2 | 0.5154 | 2.378 |
| Q0\|M_union3_v2\|a0.25\|H5\|INV10 | 不通过（f、e资本） | 0.2469 | -0.01209 | 0.3824 | 1 | 0.2847 | 1.888 |
| Q0\|M_union3_v2\|a0.25\|H5\|LAG1_10 | 通过 | 0.2173 | 0.08461 | 0.299 | 2 | 0.3866 | 2.348 |
| Q0\|M_union3_v2\|a0.25\|H5\|NATIVE | 不通过（d、f） | 0.04685 | -0.03925 | 0.1276 | -2 | 0.3439 | 2.483 |
| Q0\|M_union3_v2\|a0.5\|H5\|DECAY5_10 | 不通过（c、d、f） | -0.403 | -0.6208 | 0.697 | -2 | 1.78 | 0.6208 |
| Q0\|M_union3_v2\|a0.5\|H5\|HG10 | 不通过（c、d、f） | -0.338 | -0.5578 | 0.6043 | -3 | 1.543 | 0.5915 |
| Q0\|M_union3_v2\|a0.5\|H5\|INV10 | 不通过（c、d、f、e资本） | -0.3608 | -0.8062 | 0.7606 | -2 | 1.239 | 1.605 |
| Q0\|M_union3_v2\|a0.5\|H5\|LAG1_10 | 不通过（c、d、f） | -0.5057 | -0.7182 | 0.6066 | -3 | 1.614 | 0.8622 |
| Q0\|M_union3_v2\|a0.5\|H5\|NATIVE | 不通过（c、d、f、e资本） | -0.198 | -0.3638 | 0.3886 | -1 | 1.028 | 1.4 |
| Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|DECAY5_10 | 通过 | 0.3087 | 0.1788 | 0.3706 | 2 | 0.3863 | 2.365 |
| Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|HG10 | 通过 | 0.3374 | 0.2096 | 0.4357 | 1 | 0.569 | 2.395 |
| Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|INV10 | 不通过（f、e资本） | 0.2323 | -0.01489 | 0.4208 | 1 | 0.2619 | 1.888 |
| Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|LAG1_10 | 通过 | 0.2481 | 0.1234 | 0.3074 | 1 | 0.425 | 2.362 |
| Q0\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | 通过 | 0.08949 | 0.009182 | 0.151 | 0 | 0.357 | 2.485 |
| Q0\|M_union3_v2_CVRv5\|a0.5\|H5\|DECAY5_10 | 不通过（c、f） | -0.1792 | -0.3965 | 0.7226 | 0 | 1.69 | 0.585 |
| Q0\|M_union3_v2_CVRv5\|a0.5\|H5\|HG10 | 不通过（c、d、f） | -0.1208 | -0.3385 | 0.6531 | -1 | 1.51 | 0.5621 |
| Q0\|M_union3_v2_CVRv5\|a0.5\|H5\|INV10 | 不通过（c、d、f、e资本） | -0.2102 | -0.6373 | 0.8687 | -1 | 1.332 | 1.563 |
| Q0\|M_union3_v2_CVRv5\|a0.5\|H5\|LAG1_10 | 不通过（c、d、f） | -0.2513 | -0.4579 | 0.633 | -2 | 1.578 | 0.8162 |
| Q0\|M_union3_v2_CVRv5\|a0.5\|H5\|NATIVE | 不通过（d、f、e资本） | 0.04194 | -0.117 | 0.4007 | -2 | 1.108 | 1.33 |
| Q_D3\|A4b\|a0.25\|H5\|NATIVE | 不通过（c、f、e随机） | -0.3308 | -0.2069 | 0.06525 | 0 | -0.2337 | 2.501 |
| Q_D3\|A4b\|a0.5\|H5\|NATIVE | 不通过（c、d、f） | -1.52 | -0.8905 | 0.2398 | -3 | 0.272 | 0.338 |
| Q_D3\|A4b_CVRv5\|a0.25\|H5\|NATIVE | 不通过（c、f、e随机） | -0.1867 | -0.06484 | 0.07931 | 1 | -0.215 | 2.551 |
| Q_D3\|A4b_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -1.834 | -1.186 | -0.1577 | -5 | -0.122 | 0.2787 |
| Q_D3\|M_mean3_v2\|a0.25\|H5\|NATIVE | 不通过（c、d、f、e随机） | -0.4823 | -0.3068 | 0.05609 | -2 | -0.1523 | 2.174 |
| Q_D3\|M_mean3_v2\|a0.5\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -0.9153 | -0.5734 | -0.05627 | -4 | -0.113 | 1.017 |
| Q_D3\|M_mean3_v2_CVRv5\|a0.25\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -0.7828 | -0.5841 | -0.326 | -6 | -0.3389 | 2.161 |
| Q_D3\|M_mean3_v2_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -1.283 | -0.9013 | -0.6339 | -7 | -0.2679 | 1.011 |
| Q_D3\|M_union3_v2\|a0.25\|H5\|NATIVE | 不通过（c、d、f、e资本） | -0.1663 | -0.2303 | 0.002803 | -2 | 0.003435 | 1.923 |
| Q_D3\|M_union3_v2\|a0.5\|H5\|NATIVE | 不通过（c、d、f、e资本） | -0.5772 | -0.5497 | 0.1496 | -3 | 0.3911 | 0.5739 |
| Q_D3\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | 不通过（c、f、e资本） | -0.05828 | -0.1186 | 0.07345 | 0 | 0.09459 | 1.888 |
| Q_D3\|M_union3_v2_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、d、f、e资本） | -0.3932 | -0.3742 | 0.1575 | -3 | 0.3582 | 0.4557 |
| Q_D5\|A4b\|a0.25\|H5\|HG10 | 不通过（c、f、e随机） | -0.5411 | -0.3865 | 0.1761 | 0 | -0.4659 | 2.202 |
| Q_D5\|A4b\|a0.25\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -0.553 | -0.4215 | -0.03406 | -3 | -0.4529 | 2.666 |
| Q_D5\|A4b\|a0.5\|H5\|HG10 | 不通过（c、d、f、e随机） | -1.677 | -0.8597 | 0.2546 | -3 | -0.5038 | 0.4376 |
| Q_D5\|A4b\|a0.5\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机、size(PROPOSED_PORT3_T)） | -2.202 | -1.483 | -0.01796 | -3 | -0.4048 | -0.08501 |
| Q_D5\|A4b_CVRv5\|a0.25\|H5\|HG10 | 不通过（c、f、e随机） | -0.3541 | -0.2078 | 0.1728 | 0 | -0.3877 | 2.268 |
| Q_D5\|A4b_CVRv5\|a0.25\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -0.4082 | -0.272 | -0.01755 | -1 | -0.4316 | 2.712 |
| Q_D5\|A4b_CVRv5\|a0.5\|H5\|HG10 | 不通过（c、d、f、e随机） | -1.952 | -1.135 | 0.08506 | -3 | -0.8107 | 0.3753 |
| Q_D5\|A4b_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机、size(PROPOSED_PORT3_T)） | -2.47 | -1.74 | -0.3349 | -4 | -0.7594 | -0.1595 |
| Q_D5\|M_mean3_v2\|a0.25\|H5\|HG10 | 不通过（c、d、f、e随机） | -0.3567 | -0.1503 | 0.09256 | -2 | -0.09418 | 2.142 |
| Q_D5\|M_mean3_v2\|a0.25\|H5\|NATIVE | 不通过（c、d、f、e随机） | -0.5538 | -0.3724 | 0.0005622 | -2 | -0.2268 | 2.086 |
| Q_D5\|M_mean3_v2\|a0.5\|H5\|HG10 | 不通过（c、d、f、正向门槛、e资本、e随机） | -1.052 | -0.6722 | -0.1523 | -4 | -0.2845 | 0.928 |
| Q_D5\|M_mean3_v2\|a0.5\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -1.224 | -0.8569 | -0.08963 | -5 | -0.4218 | 0.8725 |
| Q_D5\|M_mean3_v2_CVRv5\|a0.25\|H5\|HG10 | 不通过（c、d、f、正向门槛、e随机） | -0.5229 | -0.2912 | -0.2903 | -6 | -0.157 | 2.134 |
| Q_D5\|M_mean3_v2_CVRv5\|a0.25\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -0.8573 | -0.6501 | -0.3706 | -7 | -0.4116 | 2.077 |
| Q_D5\|M_mean3_v2_CVRv5\|a0.5\|H5\|HG10 | 不通过（c、d、f、正向门槛、e随机） | -1.457 | -1.029 | -0.6761 | -6 | -0.4681 | 0.9229 |
| Q_D5\|M_mean3_v2_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -1.552 | -1.136 | -0.6131 | -6 | -0.5367 | 0.8619 |
| Q_D5\|M_union3_v2\|a0.25\|H5\|HG10 | 不通过（f、e资本、e随机） | 0.04206 | -0.07303 | 0.09697 | 1 | -0.04163 | 1.669 |
| Q_D5\|M_union3_v2\|a0.25\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e资本、e随机） | -0.1902 | -0.2512 | -0.005747 | -3 | -0.1166 | 1.642 |
| Q_D5\|M_union3_v2\|a0.5\|H5\|HG10 | 不通过（c、d、f、e资本） | -0.5587 | -0.5803 | 0.2232 | -3 | 0.345 | 0.01031 |
| Q_D5\|M_union3_v2\|a0.5\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e资本、size(PROPOSED_PORT3_T)） | -0.7695 | -0.7507 | -0.09775 | -4 | 0.02836 | -0.03651 |
| Q_D5\|M_union3_v2_CVRv5\|a0.25\|H5\|HG10 | 不通过（e资本） | 0.1264 | 0.01617 | 0.173 | 1 | 0.1025 | 1.637 |
| Q_D5\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | 不通过（c、d、f、e资本） | -0.0996 | -0.1578 | 0.03708 | -1 | 0.0439 | 1.6 |
| Q_D5\|M_union3_v2_CVRv5\|a0.5\|H5\|HG10 | 不通过（c、d、f、e资本、size(PROPOSED_PORT3_T)） | -0.263 | -0.2939 | 0.3092 | -1 | 0.402 | -0.1072 |
| Q_D5\|M_union3_v2_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e资本、size(PROPOSED_PORT3_T)） | -0.5736 | -0.4592 | -0.05446 | -3 | 0.004327 | -0.1494 |
| Q_DEW5\|A4b\|a0.25\|H5\|HG10 | 不通过（c、f、e随机） | -0.4958 | -0.3251 | 0.2004 | 1 | -0.4173 | 1.972 |
| Q_DEW5\|A4b\|a0.25\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -0.5446 | -0.4001 | -0.02709 | -1 | -0.458 | 2.5 |
| Q_DEW5\|A4b\|a0.5\|H5\|HG10 | 不通过（c、d、f、e随机） | -1.66 | -0.7563 | 0.471 | -1 | -0.4753 | 0.8503 |
| Q_DEW5\|A4b\|a0.5\|H5\|NATIVE | 不通过（c、d、f、e随机） | -1.873 | -1.086 | 0.4526 | -1 | -0.06459 | 0.05665 |
| Q_DEW5\|A4b_CVRv5\|a0.25\|H5\|HG10 | 不通过（c、f、e随机） | -0.2886 | -0.1324 | 0.1828 | 1 | -0.3112 | 2.046 |
| Q_DEW5\|A4b_CVRv5\|a0.25\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -0.3505 | -0.2019 | -0.02984 | -1 | -0.3838 | 2.556 |
| Q_DEW5\|A4b_CVRv5\|a0.5\|H5\|HG10 | 不通过（c、d、f、e随机） | -1.91 | -1.041 | 0.1206 | -1 | -0.7584 | 0.7639 |
| Q_DEW5\|A4b_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、d、f、e随机、size(PROPOSED_PORT3_T)） | -2.161 | -1.374 | 0.02779 | -4 | -0.447 | -0.02211 |
| Q_DEW5\|M_mean3_v2\|a0.25\|H5\|HG10 | 不通过（c、d、f、e随机） | -0.3296 | -0.1077 | 0.0579 | -2 | -0.07757 | 2.135 |
| Q_DEW5\|M_mean3_v2\|a0.25\|H5\|NATIVE | 不通过（c、d、f、e随机） | -0.4427 | -0.2458 | 0.09101 | -2 | -0.1241 | 2.104 |
| Q_DEW5\|M_mean3_v2\|a0.5\|H5\|HG10 | 不通过（c、d、f、正向门槛、e资本、e随机） | -1.159 | -0.7441 | -0.1166 | -6 | -0.3886 | 0.9376 |
| Q_DEW5\|M_mean3_v2\|a0.5\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -1.022 | -0.6205 | -0.09139 | -5 | -0.2291 | 0.8551 |
| Q_DEW5\|M_mean3_v2_CVRv5\|a0.25\|H5\|HG10 | 不通过（c、d、f、正向门槛、e随机） | -0.5556 | -0.3046 | -0.3417 | -5 | -0.1935 | 2.126 |
| Q_DEW5\|M_mean3_v2_CVRv5\|a0.25\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -0.7765 | -0.5507 | -0.3558 | -8 | -0.3396 | 2.087 |
| Q_DEW5\|M_mean3_v2_CVRv5\|a0.5\|H5\|HG10 | 不通过（c、d、f、正向门槛、e随机） | -1.612 | -1.154 | -0.6793 | -7 | -0.6142 | 0.9237 |
| Q_DEW5\|M_mean3_v2_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e随机） | -1.498 | -1.05 | -0.6763 | -7 | -0.488 | 0.8455 |
| Q_DEW5\|M_union3_v2\|a0.25\|H5\|HG10 | 不通过（c、f、e资本） | -0.09171 | -0.231 | 0.1434 | 0 | -0.01515 | 1.684 |
| Q_DEW5\|M_union3_v2\|a0.25\|H5\|NATIVE | 不通过（c、d、f、正向门槛、e资本） | -0.1757 | -0.2552 | -0.007957 | -3 | 0.000943 | 1.67 |
| Q_DEW5\|M_union3_v2\|a0.5\|H5\|HG10 | 不通过（c、d、f、e资本） | -0.5778 | -0.6318 | 0.2817 | -2 | 0.4048 | 0.1073 |
| Q_DEW5\|M_union3_v2\|a0.5\|H5\|NATIVE | 不通过（c、d、f、e资本、size(PROPOSED_PORT3_T)） | -0.5071 | -0.5263 | 0.1928 | -4 | 0.256 | -0.05126 |
| Q_DEW5\|M_union3_v2_CVRv5\|a0.25\|H5\|HG10 | 不通过（f、e资本） | 0.04296 | -0.09106 | 0.2224 | 1 | 0.2008 | 1.642 |
| Q_DEW5\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | 不通过（c、d、f、e资本） | -0.09228 | -0.1693 | 0.04382 | -3 | 0.1233 | 1.615 |
| Q_DEW5\|M_union3_v2_CVRv5\|a0.5\|H5\|HG10 | 不通过（c、d、f、e资本、size(PROPOSED_PORT3_T)） | -0.2797 | -0.3491 | 0.3503 | -2 | 0.4139 | -0.04742 |
| Q_DEW5\|M_union3_v2_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、d、f、e资本、size(PROPOSED_PORT3_T)） | -0.2832 | -0.312 | 0.2414 | -4 | 0.3374 | -0.1812 |
| Q_RANK5\|A4b\|a0.25\|H5\|HG10 | 通过 | 0.1546 | 0.2581 | 0.3031 | 2 | 0.2138 | 0.9018 |
| Q_RANK5\|A4b\|a0.25\|H5\|NATIVE | 不通过（c、f） | -0.09344 | -0.00563 | 0.1847 | 1 | 0.009244 | 1.489 |
| Q_RANK5\|A4b\|a0.5\|H5\|HG10 | 不通过（c、d、size(PROPOSED_PORT3_T)） | -0.2113 | 0.01372 | 0.6224 | -1 | 1.608 | -1.288 |
| Q_RANK5\|A4b\|a0.5\|H5\|NATIVE | 不通过（c、d、f、size(PROPOSED_PORT3_T)） | -0.2778 | -0.08626 | 0.3576 | -2 | 1.71 | -0.1695 |
| Q_RANK5\|A4b_CVRv5\|a0.25\|H5\|HG10 | 通过 | 0.4288 | 0.5003 | 0.3536 | 1 | 0.3829 | 0.9661 |
| Q_RANK5\|A4b_CVRv5\|a0.25\|H5\|NATIVE | 不可判（e随机:MC_UNRESOLVED） | 0.01709 | 0.08314 | 0.1224 | 1 | -0.002351 | 1.513 |
| Q_RANK5\|A4b_CVRv5\|a0.5\|H5\|HG10 | 不通过（d、size(PROPOSED_PORT3_T)） | 0.007089 | 0.1547 | 0.5902 | -1 | 1.602 | -1.121 |
| Q_RANK5\|A4b_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、d） | -0.2918 | 0.03045 | 0.2849 | -1 | 1.423 | 0.005149 |
| Q_RANK5\|M_mean3_v2\|a0.25\|H5\|HG10 | 不通过（c、f） | -0.2058 | -0.06358 | 0.1906 | 0 | 0.05928 | 2.625 |
| Q_RANK5\|M_mean3_v2\|a0.25\|H5\|NATIVE | 不通过（c、d、f） | -0.2592 | -0.1347 | 0.1373 | -2 | 0.07858 | 2.663 |
| Q_RANK5\|M_mean3_v2\|a0.5\|H5\|HG10 | 不通过（c、d、f、正向门槛） | -0.5256 | -0.2894 | -0.0413 | -6 | 0.1794 | 2.175 |
| Q_RANK5\|M_mean3_v2\|a0.5\|H5\|NATIVE | 不通过（c、d、f） | -0.5104 | -0.288 | 0.008691 | -5 | 0.2921 | 2.097 |
| Q_RANK5\|M_mean3_v2_CVRv5\|a0.25\|H5\|HG10 | 不通过（c、d、f、正向门槛） | -0.38 | -0.2222 | -0.07388 | -4 | -0.006793 | 2.606 |
| Q_RANK5\|M_mean3_v2_CVRv5\|a0.25\|H5\|NATIVE | 不通过（c、d、f、正向门槛） | -0.4339 | -0.2984 | -0.1111 | -3 | 0.02328 | 2.653 |
| Q_RANK5\|M_mean3_v2_CVRv5\|a0.5\|H5\|HG10 | 不通过（c、d、f、正向门槛） | -0.7298 | -0.4772 | -0.4324 | -8 | 0.001139 | 2.184 |
| Q_RANK5\|M_mean3_v2_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、d、f、正向门槛） | -0.7407 | -0.4966 | -0.3868 | -8 | 0.09577 | 2.098 |
| Q_RANK5\|M_union3_v2\|a0.25\|H5\|HG10 | 不通过（c、d、f、e资本） | -0.1296 | -0.2193 | 0.0735 | -3 | 0.1904 | 2.505 |
| Q_RANK5\|M_union3_v2\|a0.25\|H5\|NATIVE | 不通过（c、d、f、e资本） | -0.2445 | -0.2933 | 0.02199 | -6 | 0.05049 | 2.458 |
| Q_RANK5\|M_union3_v2\|a0.5\|H5\|HG10 | 不通过（c、d、f、e资本） | -0.8267 | -0.8188 | 0.1447 | -3 | 1.133 | 1.013 |
| Q_RANK5\|M_union3_v2\|a0.5\|H5\|NATIVE | 不通过（c、d、f、e资本） | -0.6417 | -0.5823 | 0.1085 | -5 | 1.335 | 1.347 |
| Q_RANK5\|M_union3_v2_CVRv5\|a0.25\|H5\|HG10 | 不通过（f、e资本） | 0.00288 | -0.08336 | 0.1117 | 0 | 0.2046 | 2.502 |
| Q_RANK5\|M_union3_v2_CVRv5\|a0.25\|H5\|NATIVE | 不通过（c、d、f、e资本） | -0.1512 | -0.1963 | 0.02644 | -4 | 0.05754 | 2.438 |
| Q_RANK5\|M_union3_v2_CVRv5\|a0.5\|H5\|HG10 | 不通过（c、d、f、e资本） | -0.5591 | -0.5558 | 0.0909 | -4 | 1.143 | 0.9211 |
| Q_RANK5\|M_union3_v2_CVRv5\|a0.5\|H5\|NATIVE | 不通过（c、d、f、e资本） | -0.2878 | -0.2329 | 0.05886 | -4 | 1.13 | 1.253 |


## 5. 三句加法（PX1：原生 NATIVE 的 S / M / Q0 / C1，α .25 × H5）

> 表头：主体=三句加法｜算子=NATIVE｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父（8bp）｜子集=原生四测量 × 六形态 × profile × 聚合｜单位=文本｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-P3-ADDITIONS


| form | profile | aggregation | eligible | chosen | why | sm_clause |
|---|---|---|---|---|---|---|
| A4b | PROPOSED_PORT3_T | FULL | C1\|M\|S\|Q0 | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.135 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b | PROPOSED_PORT3_T | G4 | C1\|M\|S\|Q0 | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.178 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b | LEGACY_EDIT5 | FULL | NONE | 无 | NOT_APPLICABLE | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b | LEGACY_EDIT5 | G4 | NONE | 无 | NOT_APPLICABLE | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b | PROPOSED_PORT3_LAG1 | FULL | C1\|M\|S\|Q0 | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.135 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b | PROPOSED_PORT3_LAG1 | G4 | C1\|M\|S\|Q0 | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.178 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b | EXEC_DISCLOSE_ONLY | FULL | C1\|M\|S\|Q0 | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.135 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b | EXEC_DISCLOSE_ONLY | G4 | C1\|M\|S\|Q0 | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.178 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b_CVRv5 | PROPOSED_PORT3_T | FULL | C1\|M\|S\|Q0 | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.138 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b_CVRv5 | PROPOSED_PORT3_T | G4 | C1\|M\|S\|Q0 | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.144 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b_CVRv5 | LEGACY_EDIT5 | FULL | NONE | 无 | NOT_APPLICABLE | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b_CVRv5 | LEGACY_EDIT5 | G4 | NONE | 无 | NOT_APPLICABLE | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b_CVRv5 | PROPOSED_PORT3_LAG1 | FULL | C1\|M\|S\|Q0 | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.138 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b_CVRv5 | PROPOSED_PORT3_LAG1 | G4 | C1\|M\|S\|Q0 | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.144 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b_CVRv5 | EXEC_DISCLOSE_ONLY | FULL | C1\|M\|S\|Q0 | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.138 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| A4b_CVRv5 | EXEC_DISCLOSE_ONLY | G4 | C1\|M\|S\|Q0 | S | S − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.144 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2 | PROPOSED_PORT3_T | FULL | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.236 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2 | PROPOSED_PORT3_T | G4 | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.269 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2 | LEGACY_EDIT5 | FULL | C1 | C1 | C1 合格 → 默认简单 C1 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2 | LEGACY_EDIT5 | G4 | C1 | C1 | C1 合格 → 默认简单 C1 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2 | PROPOSED_PORT3_LAG1 | FULL | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.236 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2 | PROPOSED_PORT3_LAG1 | G4 | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.269 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2 | EXEC_DISCLOSE_ONLY | FULL | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.236 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2 | EXEC_DISCLOSE_ONLY | G4 | C1\|M | M | M − C1：≥ 3/4 段 ≥ +.05，合并配对差 0.269 ≥ +.05 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2_CVRv5 | PROPOSED_PORT3_T | FULL | C1 | C1 | C1 合格 → 默认简单 C1 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2_CVRv5 | PROPOSED_PORT3_T | G4 | NONE | 无 | NOT_APPLICABLE | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2_CVRv5 | LEGACY_EDIT5 | FULL | C1 | C1 | C1 合格 → 默认简单 C1 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2_CVRv5 | LEGACY_EDIT5 | G4 | NONE | 无 | NOT_APPLICABLE | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2_CVRv5 | PROPOSED_PORT3_LAG1 | FULL | C1 | C1 | C1 合格 → 默认简单 C1 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2_CVRv5 | PROPOSED_PORT3_LAG1 | G4 | NONE | 无 | NOT_APPLICABLE | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2_CVRv5 | EXEC_DISCLOSE_ONLY | FULL | C1 | C1 | C1 合格 → 默认简单 C1 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_mean3_v2_CVRv5 | EXEC_DISCLOSE_ONLY | G4 | NONE | 无 | NOT_APPLICABLE | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2 | PROPOSED_PORT3_T | FULL | M | M | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2 | PROPOSED_PORT3_T | G4 | M | M | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2 | LEGACY_EDIT5 | FULL | M | M | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2 | LEGACY_EDIT5 | G4 | M | M | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2 | PROPOSED_PORT3_LAG1 | FULL | M | M | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2 | PROPOSED_PORT3_LAG1 | G4 | M | M | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2 | EXEC_DISCLOSE_ONLY | FULL | M | M | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2 | EXEC_DISCLOSE_ONLY | G4 | M | M | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2_CVRv5 | PROPOSED_PORT3_T | FULL | M\|S\|Q0 | M | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2_CVRv5 | PROPOSED_PORT3_T | G4 | M\|S\|Q0 | S | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2_CVRv5 | LEGACY_EDIT5 | FULL | M | M | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2_CVRv5 | LEGACY_EDIT5 | G4 | M | M | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2_CVRv5 | PROPOSED_PORT3_LAG1 | FULL | M\|S\|Q0 | M | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2_CVRv5 | PROPOSED_PORT3_LAG1 | G4 | M\|S\|Q0 | S | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2_CVRv5 | EXEC_DISCLOSE_ONLY | FULL | M\|S\|Q0 | M | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |
| M_union3_v2_CVRv5 | EXEC_DISCLOSE_ONLY | G4 | M\|S\|Q0 | S | C1 不合格；取最佳合格单臂 | NOT_APPLICABLE（E6l 无 SM 对象） |

