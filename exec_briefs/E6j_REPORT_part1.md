# E6j REPORT part1 —— B 块推导段（K 分离研究）

用途：B 包推导两段（2010-2014 / 2015-2018）的原生 FALLBACK 账户读数、完整负结果、源 / 新表示对照、Q 初读、A1-auto 与记录 B 清单（plan §10.7）。**随机参照（三类 × 1,024 路径）尚未完成，本文件不引用任何随机列**，在 part1b 补；后段账户在本文件写完之后才按记录 B 生效条件计算。

读法：每个对象 = 登记行（测量 × 方向 × 槽位）× 母体；主读数固定 α .25 × H5；"合并"= 两推导段按有效配对日合并（W07 同式）；网格（α × H 共 21 格）只作标明探索，不进结论句。一个登记行在三个母体上各是一个对象，不取跨母体中位代替对象读数（plan §4.5）。

## 0. 总览（主配置）

> 表头：主体=B 包全部对象（块 × 母体）｜算子=FALLBACK SLOT（研究引擎）｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=推导两段；主配置 α .25 × H5｜单位=子 − 母 8bp 日配对增量，年化百分点｜日期=2010-01-04..2018-12-31｜H=5（主配置）｜成本模型=8bp 线性｜支持=native FALLBACK｜资本视图=NATIVE｜exposure=含 E6i 源成员与 K0 锚｜query_id=P1-Q01


| block | mother | objects | median_FULL | p10 | p90 | both_segments_pos | both_segments_neg |
|---|---|---|---|---|---|---|---|
| B1 | A06 | 12 | 0.134 | 0.01953 | 0.2952 | 2 | 1 |
| B1 | R1 | 12 | 0.2523 | -0.338 | 0.5229 | 7 | 4 |
| B1 | R2 | 12 | 0.2321 | -0.2171 | 0.4574 | 5 | 3 |
| B2 | A06 | 64 | 0.08171 | -0.2395 | 0.3795 | 24 | 13 |
| B2 | R1 | 64 | 0.01668 | -0.3315 | 0.3506 | 26 | 15 |
| B2 | R2 | 64 | 0.1005 | -0.3198 | 0.4994 | 31 | 18 |
| B3A | A06 | 20 | 0.2188 | 0.05338 | 0.4515 | 16 | 0 |
| B3A | R1 | 20 | 0.1925 | -0.08462 | 0.3193 | 14 | 2 |
| B3A | R2 | 20 | 0.3146 | -0.06635 | 0.4893 | 15 | 1 |
| B3B | A06 | 12 | 0.0836 | -0.2965 | 0.5243 | 4 | 3 |
| B3B | R1 | 12 | 0.02633 | -0.4525 | 0.451 | 5 | 4 |
| B3B | R2 | 12 | 0.1295 | -0.3815 | 0.5248 | 5 | 2 |
| B3C | A06 | 2 | 0.3186 | 0.2895 | 0.3477 | 2 | 0 |
| B3C | R1 | 2 | 0.4076 | 0.399 | 0.4162 | 2 | 0 |
| B3C | R2 | 2 | 0.4715 | 0.4198 | 0.5232 | 2 | 0 |
| B4 | A06 | 24 | 0.01922 | -0.212 | 0.279 | 7 | 7 |
| B4 | R1 | 24 | 0.05802 | -0.3193 | 0.3159 | 12 | 9 |
| B4 | R2 | 24 | 0.07345 | -0.2387 | 0.4859 | 10 | 8 |
| B5 | A06 | 64 | 0.04608 | -0.1556 | 0.2613 | 10 | 13 |
| B5 | R1 | 64 | 0.05931 | -0.1043 | 0.2641 | 33 | 11 |
| B5 | R2 | 64 | 0.1238 | -0.1168 | 0.3199 | 30 | 8 |
| B6 | A06 | 8 | 0.04068 | -0.5587 | 0.4874 | 4 | 4 |
| B6 | A08 | 8 | -0.02154 | -0.8056 | 0.8382 | 4 | 4 |
| B6 | R1 | 8 | -0.08003 | -0.4704 | 0.3266 | 3 | 4 |
| B6 | R2 | 8 | -0.1453 | -0.6245 | 0.39 | 4 | 4 |
| B7 | A06 | 4 | 0.01189 | -0.2253 | 0.1239 | 1 | 1 |
| B7 | R1 | 4 | 0.1283 | -0.3607 | 0.3893 | 2 | 1 |
| B7 | R2 | 4 | 0.1073 | -0.4559 | 0.3864 | 2 | 2 |


计数口径：both_segments_pos / neg = 两推导段增量同为正 / 负的对象数；对象总数 638（= 202 行 × 3 母体 + 8 行 × 4 母体）〔P1-Q01〕。

## 1. 全部对象（主配置；完整负结果照列）

全部 638 个对象的主配置读数写在 `results_B/part1_main_config_all_objects.csv`（逐对象：两段增量、合并、同资本合并、含冲击 A5 κ.5 合并、Δturn、改动格数）；全部 21 格网格写在 `results_B/descriptor_stats_<段>.csv`〔P1-Q02〕。下表按块给出每块 D_FULL 最低与最高的 3 个对象，负结果与正结果同样列出。

> 表头：主体=每块主配置 D_FULL 最低 / 最高各 3 个对象（完整表见 CSV）｜算子=FALLBACK SLOT（研究引擎）｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=推导段 2010-2014 / 2015-2018｜单位=子 − 母 8bp 日配对增量，年化百分点｜日期=2010-01-04..2018-12-31｜H=5（主配置）｜成本模型=8bp 线性｜支持=native FALLBACK｜资本视图=NATIVE｜exposure=见表内 source 列｜query_id=P1-Q02


| block | mother | slot | measurement_id | direction | D_2010-2014 | D_2015-2018 | D_FULL |
|---|---|---|---|---|---|---|---|
| B1 | R2 | K | J_B1_S20lag | high_bad | -0.3002 | -0.4499 | -0.3668 |
| B1 | R1 | K | J_B1_b20 | low_bad | -0.0712 | -0.7241 | -0.3616 |
| B1 | R1 | K | J_B1_qCC | high_bad | -0.1638 | -0.5758 | -0.3471 |
| B1 | R1 | K | J_B1_qCC | low_bad | 0.3291 | 0.735 | 0.5097 |
| B1 | R1 | K | J_B1_S20lag | low_bad | 0.3872 | 0.6954 | 0.5243 |
| B1 | R1 | K | K_rar20 | low_bad | 0.4081 | 0.6797 | 0.5289 |
| B2 | R2 | K | J_B2_SLOPE20_TR_ID | high_bad | -0.5483 | -0.2648 | -0.4222 |
| B2 | R1 | K | J_B2_MR5_TR_RANGE | low_bad | -0.1486 | -0.759 | -0.4201 |
| B2 | R1 | K | J_B2_ROS20_TR_CC | low_bad | -0.235 | -0.6496 | -0.4194 |
| B2 | R2 | K | J_B2_POINT_AMT_CC | low_bad | 0.2836 | 0.8296 | 0.5265 |
| B2 | R2 | K | J_B2_MR5_TR_ID | high_bad | 0.1245 | 1.074 | 0.5467 |
| B2 | R2 | K | J_B2_MR3_TR_ID | high_bad | 0.2524 | 0.9501 | 0.5628 |
| B3A | R1 | K | J_B3A_COVP_ID_W3 | high_bad | -0.2443 | -0.05995 | -0.1623 |
| B3A | R2 | K | J_B3A_COVP_ID_W20 | high_bad | -0.1998 | -0.08933 | -0.1507 |
| B3A | A06 | K | J_B3A_COVP_ID_W20 | high_bad | -0.4143 | 0.1903 | -0.1453 |
| B3A | A06 | K | J_B3A_Q1_ID_W3 | high_bad | 0.1423 | 0.9368 | 0.4958 |
| B3A | R2 | K | J_B3A_Q05_ID_W3 | high_bad | 0.2187 | 0.9695 | 0.5527 |
| B3A | R2 | K | J_B3A_Q1_ID_W3 | high_bad | 0.2524 | 0.9501 | 0.5628 |
| B3B | R1 | K | J_B3B_SCALE_CC | high_bad | -0.4125 | -0.7878 | -0.5795 |
| B3B | R1 | K | J_B3B_SCALE_ID | high_bad | -0.2431 | -0.8087 | -0.4947 |
| B3B | A06 | K | J_B3B_SCALE_CC | high_bad | -0.5055 | -0.4037 | -0.4602 |
| B3B | A06 | K | J_B3B_SCALE_CC | low_bad | 0.4205 | 0.733 | 0.5595 |
| B3B | A06 | K | J_B3B_SCALE_ID | low_bad | 0.423 | 0.8249 | 0.6018 |
| B3B | R2 | K | J_B3B_SCALE_CC | low_bad | 0.478 | 0.8079 | 0.6247 |
| B3C | A06 | K | J_B3C_REL_ID | low_bad | 0.2578 | 0.3127 | 0.2822 |
| B3C | A06 | K | J_B3C_REL_CC | low_bad | 0.264 | 0.4684 | 0.3549 |
| B3C | R1 | K | J_B3C_REL_ID | low_bad | 0.3033 | 0.5136 | 0.3968 |
| B3C | R2 | K | J_B3C_REL_CC | low_bad | 0.3376 | 0.4933 | 0.4069 |
| B3C | R1 | K | J_B3C_REL_CC | low_bad | 0.2882 | 0.5809 | 0.4184 |
| B3C | R2 | K | J_B3C_REL_ID | low_bad | 0.3285 | 0.7952 | 0.5361 |
| B4 | R1 | K | J_B4_ROS_DN_CC | low_bad | -0.1635 | -0.6311 | -0.3715 |
| B4 | R1 | K | J_B4_ROS_DN_ID | low_bad | -0.2602 | -0.4682 | -0.3527 |
| B4 | R2 | K | J_B4_MR_DN_ID | low_bad | -0.2523 | -0.4737 | -0.3508 |
| B4 | R2 | K | J_B4_ROS_UP_CC | high_bad | 0.1891 | 0.8609 | 0.4879 |
| B4 | R2 | K | J_B4_ROS_UP_ID | high_bad | 0.1605 | 1.009 | 0.538 |
| B4 | R2 | K | J_B4_MR_DN_ID | high_bad | 0.2831 | 0.9379 | 0.5744 |
| B5 | R2 | K | J_B5_RARPRE_CC_W20_LT | high_bad | -0.2619 | -0.4956 | -0.3659 |
| B5 | R2 | K | J_B5_RARPRE_CC_W20_SE | high_bad | -0.2509 | -0.4757 | -0.3509 |
| B5 | A06 | K | J_B5_REV5_ID_W60_SE | high_bad | -0.3657 | -0.2977 | -0.3354 |
| B5 | R1 | K | J_B5_RARPRE_CC_W20_LT | low_bad | 0.3199 | 0.6087 | 0.4484 |
| B5 | R2 | K | J_B5_RARPRE_CC_W60_LT | low_bad | 0.232 | 0.7359 | 0.4562 |
| B5 | R1 | K | J_B5_RARPRE_CC_W20_SE | low_bad | 0.4262 | 0.7057 | 0.5506 |
| B6 | A08 | T | T_ewcv20 | low_bad | -0.5729 | -1.234 | -0.8671 |
| B6 | A08 | T | J_B6_CV20 | low_bad | -0.5698 | -1.041 | -0.7793 |
| B6 | A08 | T | J_B6_DETREND20 | low_bad | -0.3728 | -1.083 | -0.6885 |
| B6 | A08 | T | J_B6_DETREND20 | high_bad | 0.6662 | 0.569 | 0.623 |
| B6 | A08 | T | J_B6_CV20 | high_bad | 0.8815 | 0.749 | 0.8226 |
| B6 | A08 | T | T_ewcv20 | high_bad | 0.9318 | 0.8036 | 0.8748 |
| B7 | R2 | T | R_peer20 | low_bad | -0.3803 | -0.9066 | -0.6144 |
| B7 | R1 | T | R_peer20 | low_bad | -0.1712 | -0.9398 | -0.5131 |
| B7 | A06 | T | R_peer20 | low_bad | -0.1303 | -0.4675 | -0.2803 |
| B7 | R2 | T | R_peer20 | high_bad | 0.283 | 0.3226 | 0.3006 |
| B7 | R2 | K | R_peer20 | high_bad | 0.1668 | 0.7432 | 0.4232 |
| B7 | R1 | T | R_peer20 | high_bad | 0.3081 | 0.6135 | 0.444 |


## 2. 问题卡初读（主配置；同母体配对；不设门）

### Q02 / Q03：B1 分量（b / a / q / a×q / 60 日基线 / log）与源 S（K_rar20 低坏）

> 表头：主体=Q02 / Q03：B1 分量（b / a / q / a×q / 60 日基线 / log）与源 S（K_rar20 低坏）｜算子=FALLBACK SLOT（研究引擎）｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=推导段 2010-2014 / 2015-2018｜单位=子 − 母 8bp 日配对增量，年化百分点｜日期=2010-01-04..2018-12-31｜H=5（主配置）｜成本模型=8bp 线性｜支持=native FALLBACK｜资本视图=NATIVE｜exposure=见表内 source 列｜query_id=P1-Q03


| mother | slot | measurement_id | direction | direction_role | D_2010-2014 | D_2015-2018 | D_FULL | minus_ref_FULL |
|---|---|---|---|---|---|---|---|---|
| A06 | K | J_B1_S20lag | high_bad | competitor | -0.02882 | -0.1593 | -0.08687 | -0.3283 |
| A06 | K | J_B1_S20lag | low_bad | main | -0.1491 | 0.8589 | 0.2993 | 0.05789 |
| A06 | K | J_B1_S60lag | low_bad | main | -0.1387 | 0.7532 | 0.2581 | 0.01665 |
| A06 | K | J_B1_a20 | high_bad | competitor | 0.08338 | 0.3219 | 0.1895 | -0.05192 |
| A06 | K | J_B1_a20 | low_bad | main | -0.2961 | 0.4644 | 0.04222 | -0.1992 |
| A06 | K | J_B1_b20 | high_bad | main | -0.2704 | 0.5166 | 0.07971 | -0.1617 |
| A06 | K | J_B1_b20 | low_bad | competitor | 0.04499 | 0.2902 | 0.1541 | -0.08734 |
| A06 | K | J_B1_logK0 | high_bad | main | 0.07937 | -0.0005396 | 0.04382 | -0.1976 |
| A06 | K | J_B1_logS20lag | low_bad | main | -0.2875 | 0.6148 | 0.1139 | -0.1275 |
| A06 | K | J_B1_qCC | high_bad | competitor | 0.03424 | -0.004505 | 0.017 | -0.2244 |
| A06 | K | J_B1_qCC | low_bad | main | -0.08305 | 0.9526 | 0.3777 | 0.1362 |
| A06 | K | K_rar20 | low_bad | main | -0.1614 | 0.7441 | 0.2414 | 0 |
| R1 | K | J_B1_S20lag | high_bad | competitor | -0.04799 | -0.5176 | -0.2569 | -0.7858 |
| R1 | K | J_B1_S20lag | low_bad | main | 0.3872 | 0.6954 | 0.5243 | -0.004602 |
| R1 | K | J_B1_S60lag | low_bad | main | 0.3409 | 0.421 | 0.3766 | -0.1524 |
| R1 | K | J_B1_a20 | high_bad | competitor | 0.1916 | -0.1758 | 0.02815 | -0.5008 |
| R1 | K | J_B1_a20 | low_bad | main | -0.06855 | -0.007176 | -0.04124 | -0.5702 |
| R1 | K | J_B1_b20 | high_bad | main | 0.1702 | 0.6625 | 0.3892 | -0.1397 |
| R1 | K | J_B1_b20 | low_bad | competitor | -0.0712 | -0.7241 | -0.3616 | -0.8906 |
| R1 | K | J_B1_logK0 | high_bad | main | 0.218 | 0.1099 | 0.1699 | -0.359 |
| R1 | K | J_B1_logS20lag | low_bad | main | 0.1254 | 0.5958 | 0.3347 | -0.1943 |
| R1 | K | J_B1_qCC | high_bad | competitor | -0.1638 | -0.5758 | -0.3471 | -0.876 |
| R1 | K | J_B1_qCC | low_bad | main | 0.3291 | 0.735 | 0.5097 | -0.01924 |
| R1 | K | K_rar20 | low_bad | main | 0.4081 | 0.6797 | 0.5289 | 0 |
| R2 | K | J_B1_S20lag | high_bad | competitor | -0.3002 | -0.4499 | -0.3668 | -0.8251 |
| R2 | K | J_B1_S20lag | low_bad | main | 0.1686 | 0.8427 | 0.4685 | 0.01016 |
| R2 | K | J_B1_S60lag | low_bad | main | 0.2132 | 0.7439 | 0.4493 | -0.009055 |
| R2 | K | J_B1_a20 | high_bad | competitor | -0.1225 | 0.05789 | -0.04226 | -0.5006 |
| R2 | K | J_B1_a20 | low_bad | main | -0.1149 | 0.3609 | 0.09673 | -0.3616 |
| R2 | K | J_B1_b20 | high_bad | main | 0.04824 | 0.8924 | 0.4238 | -0.03456 |
| R2 | K | J_B1_b20 | low_bad | competitor | -0.1394 | -0.2992 | -0.2105 | -0.6688 |
| R2 | K | J_B1_logK0 | high_bad | main | -0.06347 | 0.1662 | 0.0387 | -0.4196 |
| R2 | K | J_B1_logS20lag | low_bad | main | -0.05138 | 0.9241 | 0.3826 | -0.07577 |
| R2 | K | J_B1_qCC | high_bad | competitor | -0.2115 | -0.2258 | -0.2179 | -0.6762 |
| R2 | K | J_B1_qCC | low_bad | main | 0.05659 | 0.7554 | 0.3675 | -0.09085 |
| R2 | K | K_rar20 | low_bad | main | 0.1642 | 0.8254 | 0.4583 | 0 |


### Q04：M 的尺度分解（β_norm / ρ / scale）与 SLOPE20 各价格口径

> 表头：主体=Q04：M 的尺度分解（β_norm / ρ / scale）与 SLOPE20 各价格口径｜算子=FALLBACK SLOT（研究引擎）｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=推导段 2010-2014 / 2015-2018｜单位=子 − 母 8bp 日配对增量，年化百分点｜日期=2010-01-04..2018-12-31｜H=5（主配置）｜成本模型=8bp 线性｜支持=native FALLBACK｜资本视图=NATIVE｜exposure=见表内 source 列｜query_id=P1-Q04


| mother | slot | measurement_id | direction | direction_role | D_2010-2014 | D_2015-2018 | D_FULL |
|---|---|---|---|---|---|---|---|
| A06 | K | J_B2_SLOPE20_AMT_CC | high_bad | competitor | -0.2739 | -0.2025 | -0.2422 |
| A06 | K | J_B2_SLOPE20_AMT_CC | low_bad | main | 0.2586 | 0.4962 | 0.3643 |
| A06 | K | J_B2_SLOPE20_AMT_ID | high_bad | competitor | -0.3118 | -0.05677 | -0.1983 |
| A06 | K | J_B2_SLOPE20_AMT_ID | low_bad | main | 0.1682 | 0.1958 | 0.1805 |
| A06 | K | J_B2_SLOPE20_AMT_RANGE | high_bad | competitor | -0.2456 | -0.2181 | -0.2333 |
| A06 | K | J_B2_SLOPE20_AMT_RANGE | low_bad | main | 0.2556 | 0.6159 | 0.4159 |
| A06 | K | J_B2_SLOPE20_TR_CC | high_bad | competitor | -0.3218 | 0.008347 | -0.1749 |
| A06 | K | J_B2_SLOPE20_TR_CC | low_bad | main | 0.3325 | 0.4524 | 0.3858 |
| A06 | K | J_B2_SLOPE20_TR_ID | high_bad | competitor | -0.396 | 0.03848 | -0.2027 |
| A06 | K | J_B2_SLOPE20_TR_ID | low_bad | main | 0.2933 | 0.3854 | 0.3342 |
| A06 | K | J_B2_SLOPE20_TR_RANGE | high_bad | competitor | -0.3795 | 0.05535 | -0.1861 |
| A06 | K | J_B2_SLOPE20_TR_RANGE | low_bad | main | 0.3509 | 0.46 | 0.3994 |
| A06 | K | J_B3B_BETANORM_CC | high_bad | competitor | -0.2769 | 0.1724 | -0.07704 |
| A06 | K | J_B3B_BETANORM_CC | low_bad | main | 0.1562 | 0.2344 | 0.1909 |
| A06 | K | J_B3B_BETANORM_ID | high_bad | competitor | -0.131 | 0.33 | 0.07405 |
| A06 | K | J_B3B_BETANORM_ID | low_bad | main | 0.04177 | -0.03083 | 0.009471 |
| A06 | K | J_B3B_RHO_CC | high_bad | competitor | -0.1523 | 0.4597 | 0.12 |
| A06 | K | J_B3B_RHO_CC | low_bad | main | 0.07438 | 0.1166 | 0.09314 |
| A06 | K | J_B3B_RHO_ID | high_bad | competitor | -0.02016 | 0.4927 | 0.208 |
| A06 | K | J_B3B_RHO_ID | low_bad | main | -0.06566 | -0.3023 | -0.1709 |
| A06 | K | J_B3B_SCALE_CC | high_bad | both_registered | -0.5055 | -0.4037 | -0.4602 |
| A06 | K | J_B3B_SCALE_CC | low_bad | both_registered | 0.4205 | 0.733 | 0.5595 |
| A06 | K | J_B3B_SCALE_ID | high_bad | both_registered | -0.4981 | -0.07613 | -0.3104 |
| A06 | K | J_B3B_SCALE_ID | low_bad | both_registered | 0.423 | 0.8249 | 0.6018 |
| R1 | K | J_B2_SLOPE20_AMT_CC | high_bad | competitor | 0.005821 | -0.2298 | -0.09898 |
| R1 | K | J_B2_SLOPE20_AMT_CC | low_bad | main | 0.04958 | 0.738 | 0.3558 |
| R1 | K | J_B2_SLOPE20_AMT_ID | high_bad | competitor | -0.1141 | -0.1827 | -0.1446 |
| R1 | K | J_B2_SLOPE20_AMT_ID | low_bad | main | 0.1545 | 0.6054 | 0.3551 |
| R1 | K | J_B2_SLOPE20_AMT_RANGE | high_bad | competitor | 0.02158 | -0.1645 | -0.06118 |
| R1 | K | J_B2_SLOPE20_AMT_RANGE | low_bad | main | 0.1118 | 0.5452 | 0.3046 |
| R1 | K | J_B2_SLOPE20_TR_CC | high_bad | competitor | -0.1466 | -0.5349 | -0.3194 |
| R1 | K | J_B2_SLOPE20_TR_CC | low_bad | main | 0.2934 | 0.5483 | 0.4068 |
| R1 | K | J_B2_SLOPE20_TR_ID | high_bad | competitor | -0.1395 | -0.5899 | -0.3399 |
| R1 | K | J_B2_SLOPE20_TR_ID | low_bad | main | 0.2876 | 0.4421 | 0.3563 |
| R1 | K | J_B2_SLOPE20_TR_RANGE | high_bad | competitor | -0.1184 | -0.4765 | -0.2777 |
| R1 | K | J_B2_SLOPE20_TR_RANGE | low_bad | main | 0.4261 | 0.6107 | 0.5082 |
| R1 | K | J_B3B_BETANORM_CC | high_bad | competitor | -0.02431 | -0.1053 | -0.06036 |
| R1 | K | J_B3B_BETANORM_CC | low_bad | main | 0.1215 | 0.2858 | 0.1946 |
| R1 | K | J_B3B_BETANORM_ID | high_bad | competitor | 0.05562 | -0.06752 | 0.0008385 |
| R1 | K | J_B3B_BETANORM_ID | low_bad | main | 0.0645 | 0.3086 | 0.1731 |
| R1 | K | J_B3B_RHO_CC | high_bad | competitor | 0.07806 | 0.008723 | 0.04722 |
| R1 | K | J_B3B_RHO_CC | low_bad | main | -0.02199 | 0.07454 | 0.02095 |
| R1 | K | J_B3B_RHO_ID | high_bad | competitor | 0.1006 | -0.0543 | 0.03171 |
| R1 | K | J_B3B_RHO_ID | low_bad | main | -0.0389 | -0.1153 | -0.07287 |
| R1 | K | J_B3B_SCALE_CC | high_bad | both_registered | -0.4125 | -0.7878 | -0.5795 |
| R1 | K | J_B3B_SCALE_CC | low_bad | both_registered | 0.4282 | 0.5434 | 0.4795 |
| R1 | K | J_B3B_SCALE_ID | high_bad | both_registered | -0.2431 | -0.8087 | -0.4947 |
| R1 | K | J_B3B_SCALE_ID | low_bad | both_registered | 0.3984 | 0.6027 | 0.4893 |
| R2 | K | J_B2_SLOPE20_AMT_CC | high_bad | competitor | -0.1471 | 0.1362 | -0.0211 |
| R2 | K | J_B2_SLOPE20_AMT_CC | low_bad | main | 0.1964 | 0.6795 | 0.4113 |
| R2 | K | J_B2_SLOPE20_AMT_ID | high_bad | competitor | -0.1007 | -0.1139 | -0.1066 |
| R2 | K | J_B2_SLOPE20_AMT_ID | low_bad | main | 0.04177 | 0.5792 | 0.2808 |
| R2 | K | J_B2_SLOPE20_AMT_RANGE | high_bad | competitor | -0.2132 | -0.2974 | -0.2506 |
| R2 | K | J_B2_SLOPE20_AMT_RANGE | low_bad | main | 0.03001 | 0.6505 | 0.3061 |
| R2 | K | J_B2_SLOPE20_TR_CC | high_bad | competitor | -0.5234 | -0.2304 | -0.3931 |
| R2 | K | J_B2_SLOPE20_TR_CC | low_bad | main | 0.3652 | 0.4661 | 0.4101 |
| R2 | K | J_B2_SLOPE20_TR_ID | high_bad | competitor | -0.5483 | -0.2648 | -0.4222 |
| R2 | K | J_B2_SLOPE20_TR_ID | low_bad | main | 0.3078 | 0.7859 | 0.5205 |
| R2 | K | J_B2_SLOPE20_TR_RANGE | high_bad | competitor | -0.5036 | -0.2853 | -0.4064 |
| R2 | K | J_B2_SLOPE20_TR_RANGE | low_bad | main | 0.3145 | 0.6933 | 0.483 |
| R2 | K | J_B3B_BETANORM_CC | high_bad | competitor | -0.1993 | 0.3877 | 0.0618 |
| R2 | K | J_B3B_BETANORM_CC | low_bad | main | 0.1759 | 0.04679 | 0.1185 |
| R2 | K | J_B3B_BETANORM_ID | high_bad | competitor | -0.256 | 0.6354 | 0.1405 |
| R2 | K | J_B3B_BETANORM_ID | low_bad | main | 0.1527 | 0.2125 | 0.1793 |
| R2 | K | J_B3B_RHO_CC | high_bad | competitor | -0.1297 | 0.508 | 0.154 |
| R2 | K | J_B3B_RHO_CC | low_bad | main | 0.02377 | -0.3365 | -0.1365 |
| R2 | K | J_B3B_RHO_ID | high_bad | competitor | 0.05809 | 0.4394 | 0.2277 |
| R2 | K | J_B3B_RHO_ID | low_bad | main | 0.1369 | -0.0587 | 0.04986 |
| R2 | K | J_B3B_SCALE_CC | high_bad | both_registered | -0.4379 | -0.4051 | -0.4233 |
| R2 | K | J_B3B_SCALE_CC | low_bad | both_registered | 0.478 | 0.8079 | 0.6247 |
| R2 | K | J_B3B_SCALE_ID | high_bad | both_registered | -0.4714 | -0.3306 | -0.4087 |
| R2 | K | J_B3B_SCALE_ID | low_bad | both_registered | 0.3042 | 0.8743 | 0.5578 |


### Q05：可靠性收缩 J_M_reliable（CC / ID）

> 表头：主体=Q05：可靠性收缩 J_M_reliable（CC / ID）｜算子=FALLBACK SLOT（研究引擎）｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=推导段 2010-2014 / 2015-2018｜单位=子 − 母 8bp 日配对增量，年化百分点｜日期=2010-01-04..2018-12-31｜H=5（主配置）｜成本模型=8bp 线性｜支持=native FALLBACK｜资本视图=NATIVE｜exposure=见表内 source 列｜query_id=P1-Q05


| mother | slot | measurement_id | direction | direction_role | D_2010-2014 | D_2015-2018 | D_FULL | minus_ref_FULL |
|---|---|---|---|---|---|---|---|---|
| A06 | K | J_B3C_REL_CC | low_bad | main | 0.264 | 0.4684 | 0.3549 | -0.03089 |
| A06 | K | J_B3C_REL_ID | low_bad | main | 0.2578 | 0.3127 | 0.2822 | -0.1036 |
| R1 | K | J_B3C_REL_CC | low_bad | main | 0.2882 | 0.5809 | 0.4184 | 0.01164 |
| R1 | K | J_B3C_REL_ID | low_bad | main | 0.3033 | 0.5136 | 0.3968 | -0.009953 |
| R2 | K | J_B3C_REL_CC | low_bad | main | 0.3376 | 0.4933 | 0.4069 | -0.003197 |
| R2 | K | J_B3C_REL_ID | low_bad | main | 0.3285 | 0.7952 | 0.5361 | 0.126 |


### Q06：聚合协动 λ ∈ {0, .5, 1} 与 COV/P

> 表头：主体=Q06：聚合协动 λ ∈ {0, .5, 1} 与 COV/P｜算子=FALLBACK SLOT（研究引擎）｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=推导段 2010-2014 / 2015-2018｜单位=子 − 母 8bp 日配对增量，年化百分点｜日期=2010-01-04..2018-12-31｜H=5（主配置）｜成本模型=8bp 线性｜支持=native FALLBACK｜资本视图=NATIVE｜exposure=见表内 source 列｜query_id=P1-Q06


| mother | slot | measurement_id | direction | direction_role | D_2010-2014 | D_2015-2018 | D_FULL |
|---|---|---|---|---|---|---|---|
| A06 | K | J_B3A_COVP_CC_W20 | high_bad | both_registered | -0.2356 | 0.3276 | 0.01498 |
| A06 | K | J_B3A_COVP_CC_W20 | low_bad | both_registered | 0.1345 | 0.5983 | 0.3408 |
| A06 | K | J_B3A_COVP_CC_W3 | high_bad | both_registered | -0.1605 | 0.3299 | 0.05764 |
| A06 | K | J_B3A_COVP_CC_W3 | low_bad | both_registered | 0.02494 | 0.1593 | 0.0847 |
| A06 | K | J_B3A_COVP_ID_W20 | high_bad | both_registered | -0.4143 | 0.1903 | -0.1453 |
| A06 | K | J_B3A_COVP_ID_W20 | low_bad | both_registered | 0.2256 | 0.6072 | 0.3954 |
| A06 | K | J_B3A_COVP_ID_W3 | high_bad | both_registered | -0.02955 | 0.2549 | 0.09699 |
| A06 | K | J_B3A_COVP_ID_W3 | low_bad | both_registered | 0.002512 | 0.4832 | 0.2164 |
| A06 | K | J_B3A_Q05_CC_W20 | high_bad | main | 0.1841 | 0.2677 | 0.2213 |
| A06 | K | J_B3A_Q05_CC_W3 | high_bad | main | 0.1056 | 0.3284 | 0.2047 |
| A06 | K | J_B3A_Q05_ID_W20 | high_bad | main | 0.03631 | 0.6661 | 0.3165 |
| A06 | K | J_B3A_Q05_ID_W3 | high_bad | main | 0.08957 | 0.9224 | 0.46 |
| A06 | K | J_B3A_Q0_CC_W20 | high_bad | main | 0.1927 | 0.2271 | 0.208 |
| A06 | K | J_B3A_Q0_CC_W3 | high_bad | main | 0.07495 | 0.3534 | 0.1988 |
| A06 | K | J_B3A_Q0_ID_W20 | high_bad | main | 0.1164 | 0.5781 | 0.3218 |
| A06 | K | J_B3A_Q0_ID_W3 | high_bad | main | 0.08423 | 0.9076 | 0.4505 |
| A06 | K | J_B3A_Q1_CC_W20 | high_bad | main | 0.1346 | 0.3597 | 0.2347 |
| A06 | K | J_B3A_Q1_CC_W3 | high_bad | main | 0.1058 | 0.3331 | 0.2069 |
| A06 | K | J_B3A_Q1_ID_W20 | high_bad | main | 0.003675 | 0.6661 | 0.2984 |
| A06 | K | J_B3A_Q1_ID_W3 | high_bad | main | 0.1423 | 0.9368 | 0.4958 |
| R1 | K | J_B3A_COVP_CC_W20 | high_bad | both_registered | -0.1467 | -0.1045 | -0.1279 |
| R1 | K | J_B3A_COVP_CC_W20 | low_bad | both_registered | 0.1071 | 0.1441 | 0.1236 |
| R1 | K | J_B3A_COVP_CC_W3 | high_bad | both_registered | -0.1973 | 0.09244 | -0.06843 |
| R1 | K | J_B3A_COVP_CC_W3 | low_bad | both_registered | 0.205 | -0.03737 | 0.0972 |
| R1 | K | J_B3A_COVP_ID_W20 | high_bad | both_registered | -0.1979 | 0.06757 | -0.07981 |
| R1 | K | J_B3A_COVP_ID_W20 | low_bad | both_registered | 0.3062 | 0.09252 | 0.2111 |
| R1 | K | J_B3A_COVP_ID_W3 | high_bad | both_registered | -0.2443 | -0.05995 | -0.1623 |
| R1 | K | J_B3A_COVP_ID_W3 | low_bad | both_registered | 0.1169 | 0.148 | 0.1307 |
| R1 | K | J_B3A_Q05_CC_W20 | high_bad | main | -0.00106 | 0.2625 | 0.1162 |
| R1 | K | J_B3A_Q05_CC_W3 | high_bad | main | 0.2328 | 0.3793 | 0.298 |
| R1 | K | J_B3A_Q05_ID_W20 | high_bad | main | 0.1049 | 0.6007 | 0.3255 |
| R1 | K | J_B3A_Q05_ID_W3 | high_bad | main | 0.2241 | 0.4366 | 0.3187 |
| R1 | K | J_B3A_Q0_CC_W20 | high_bad | main | 0.04509 | 0.2208 | 0.1232 |
| R1 | K | J_B3A_Q0_CC_W3 | high_bad | main | 0.1767 | 0.3937 | 0.2732 |
| R1 | K | J_B3A_Q0_ID_W20 | high_bad | main | 0.04771 | 0.5625 | 0.2767 |
| R1 | K | J_B3A_Q0_ID_W3 | high_bad | main | 0.2426 | 0.3652 | 0.2971 |
| R1 | K | J_B3A_Q1_CC_W20 | high_bad | main | 0.07543 | 0.2967 | 0.1739 |
| R1 | K | J_B3A_Q1_CC_W3 | high_bad | main | 0.2701 | 0.3925 | 0.3246 |
| R1 | K | J_B3A_Q1_ID_W20 | high_bad | main | 0.03354 | 0.5952 | 0.2834 |
| R1 | K | J_B3A_Q1_ID_W3 | high_bad | main | 0.1968 | 0.4061 | 0.2899 |
| R2 | K | J_B3A_COVP_CC_W20 | high_bad | both_registered | -0.2044 | 0.07707 | -0.07921 |
| R2 | K | J_B3A_COVP_CC_W20 | low_bad | both_registered | 0.2417 | 0.1131 | 0.1845 |
| R2 | K | J_B3A_COVP_CC_W3 | high_bad | both_registered | -0.1512 | 0.2038 | 0.006725 |
| R2 | K | J_B3A_COVP_CC_W3 | low_bad | both_registered | -0.07527 | 0.4426 | 0.1551 |
| R2 | K | J_B3A_COVP_ID_W20 | high_bad | both_registered | -0.1998 | -0.08933 | -0.1507 |
| R2 | K | J_B3A_COVP_ID_W20 | low_bad | both_registered | 0.0699 | 0.7656 | 0.3794 |
| R2 | K | J_B3A_COVP_ID_W3 | high_bad | both_registered | -0.1558 | 0.04846 | -0.06492 |
| R2 | K | J_B3A_COVP_ID_W3 | low_bad | both_registered | 0.1238 | 0.4398 | 0.2644 |
| R2 | K | J_B3A_Q05_CC_W20 | high_bad | main | 0.06581 | 0.291 | 0.166 |
| R2 | K | J_B3A_Q05_CC_W3 | high_bad | main | 0.02749 | 0.7989 | 0.3706 |
| R2 | K | J_B3A_Q05_ID_W20 | high_bad | main | 0.1113 | 0.7874 | 0.4121 |
| R2 | K | J_B3A_Q05_ID_W3 | high_bad | main | 0.2187 | 0.9695 | 0.5527 |
| R2 | K | J_B3A_Q0_CC_W20 | high_bad | main | 0.1478 | 0.393 | 0.2569 |
| R2 | K | J_B3A_Q0_CC_W3 | high_bad | main | 0.01871 | 0.7968 | 0.3649 |
| R2 | K | J_B3A_Q0_ID_W20 | high_bad | main | 0.2254 | 0.7818 | 0.4729 |
| R2 | K | J_B3A_Q0_ID_W3 | high_bad | main | 0.1842 | 0.8541 | 0.4822 |
| R2 | K | J_B3A_Q1_CC_W20 | high_bad | main | 0.1295 | 0.248 | 0.1822 |
| R2 | K | J_B3A_Q1_CC_W3 | high_bad | main | 0.04621 | 0.7957 | 0.3796 |
| R2 | K | J_B3A_Q1_ID_W20 | high_bad | main | 0.04682 | 0.776 | 0.3712 |
| R2 | K | J_B3A_Q1_ID_W3 | high_bad | main | 0.2524 | 0.9501 | 0.5628 |


### Q10：价格时段（CC / ID / RANGE / ON）× 聚合 × 单位（主方向）

> 表头：主体=B2 主方向对象｜算子=FALLBACK SLOT（研究引擎）｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=推导段 2010-2014 / 2015-2018｜单位=D_FULL 年化百分点（列 = 价格口径）｜日期=2010-01-04..2018-12-31｜H=5（主配置）｜成本模型=8bp 线性｜支持=native FALLBACK｜资本视图=NATIVE｜exposure=见表内 source 列｜query_id=P1-Q07


| mother | agg | unit | CC | ID | ON | RANGE |
|---|---|---|---|---|---|---|
| A06 | MR3 | AMT | -0.02466 | 0.1269 |  | 0.1037 |
| A06 | MR3 | TR | 0.2069 | 0.4958 |  | 0.3701 |
| A06 | MR5 | AMT | -0.03849 | 0.07958 |  | 0.02601 |
| A06 | MR5 | TR | 0.2027 | 0.3836 |  | 0.4002 |
| A06 | POINT | AMT | 0.08385 | 0.2349 | -0.02694 | 0.1711 |
| A06 | POINT | TR | 0 | 0.1948 | 0.2365 | 0.4465 |
| A06 | ROS20 | AMT | 0.009123 | 0.01427 |  | 0.02797 |
| A06 | ROS20 | TR | 0.2601 | 0.2906 |  | 0.219 |
| A06 | SLOPE20 | AMT | 0.3643 | 0.1805 |  | 0.4159 |
| A06 | SLOPE20 | TR | 0.3858 | 0.3342 |  | 0.3994 |
| R1 | MR3 | AMT | -0.1174 | -0.1128 |  | 0.06793 |
| R1 | MR3 | TR | 0.3246 | 0.2899 |  | 0.2513 |
| R1 | MR5 | AMT | -0.1385 | -0.07435 |  | 0.04756 |
| R1 | MR5 | TR | 0.2484 | 0.3333 |  | 0.3075 |
| R1 | POINT | AMT | -0.1473 | -0.09003 | -0.07792 | 0.1741 |
| R1 | POINT | TR | 0 | 0.2788 | 0.3401 | 0.4103 |
| R1 | ROS20 | AMT | 0.02721 | -0.02258 |  | 0.006156 |
| R1 | ROS20 | TR | 0.3223 | 0.3105 |  | 0.2843 |
| R1 | SLOPE20 | AMT | 0.3558 | 0.3551 |  | 0.3046 |
| R1 | SLOPE20 | TR | 0.4068 | 0.3563 |  | 0.5082 |
| R2 | MR3 | AMT | -0.2505 | -0.07502 |  | -0.1242 |
| R2 | MR3 | TR | 0.3796 | 0.5628 |  | 0.5054 |
| R2 | MR5 | AMT | -0.1262 | -0.1486 |  | -0.08778 |
| R2 | MR5 | TR | 0.4487 | 0.5467 |  | 0.5037 |
| R2 | POINT | AMT | -0.2708 | -0.2492 | -0.122 | -0.06219 |
| R2 | POINT | TR | 0 | 0.3449 | 0.424 | 0.4354 |
| R2 | ROS20 | AMT | -0.1104 | -0.05107 |  | -0.02623 |
| R2 | ROS20 | TR | 0.4826 | 0.5085 |  | 0.4894 |
| R2 | SLOPE20 | AMT | 0.4113 | 0.2808 |  | 0.3061 |
| R2 | SLOPE20 | TR | 0.4101 | 0.5205 |  | 0.483 |


### Q11：涨跌分解（ROS / MR × UP / DN × CC / ID）与 asym

> 表头：主体=Q11：涨跌分解（ROS / MR × UP / DN × CC / ID）与 asym｜算子=FALLBACK SLOT（研究引擎）｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=推导段 2010-2014 / 2015-2018｜单位=子 − 母 8bp 日配对增量，年化百分点｜日期=2010-01-04..2018-12-31｜H=5（主配置）｜成本模型=8bp 线性｜支持=native FALLBACK｜资本视图=NATIVE｜exposure=见表内 source 列｜query_id=P1-Q08


| mother | slot | measurement_id | direction | direction_role | D_2010-2014 | D_2015-2018 | D_FULL |
|---|---|---|---|---|---|---|---|
| A06 | K | J_B4_ASYM_MR_CC | high_bad | both_registered | -0.09566 | 0.1832 | 0.02839 |
| A06 | K | J_B4_ASYM_MR_CC | low_bad | both_registered | -0.1627 | 0.1763 | -0.01194 |
| A06 | K | J_B4_ASYM_MR_ID | high_bad | both_registered | -0.2292 | 0.5334 | 0.11 |
| A06 | K | J_B4_ASYM_MR_ID | low_bad | both_registered | 0.009709 | -0.2868 | -0.1222 |
| A06 | K | J_B4_ASYM_ROS_CC | high_bad | both_registered | 0.1011 | 0.3192 | 0.1981 |
| A06 | K | J_B4_ASYM_ROS_CC | low_bad | both_registered | -0.1726 | 0.238 | 0.01005 |
| A06 | K | J_B4_ASYM_ROS_ID | high_bad | both_registered | 0.1273 | 0.469 | 0.2793 |
| A06 | K | J_B4_ASYM_ROS_ID | low_bad | both_registered | -0.335 | -0.06191 | -0.2135 |
| A06 | K | J_B4_MR_DN_CC | high_bad | both_registered | 0.04029 | 0.5824 | 0.2815 |
| A06 | K | J_B4_MR_DN_CC | low_bad | both_registered | -0.3078 | -0.08447 | -0.2085 |
| A06 | K | J_B4_MR_DN_ID | high_bad | both_registered | 0.07657 | 0.3951 | 0.2183 |
| A06 | K | J_B4_MR_DN_ID | low_bad | both_registered | -0.3491 | 0.2062 | -0.102 |
| A06 | K | J_B4_MR_UP_CC | high_bad | both_registered | -0.1447 | 0.2766 | 0.04273 |
| A06 | K | J_B4_MR_UP_CC | low_bad | both_registered | -0.2553 | 0.0107 | -0.1369 |
| A06 | K | J_B4_MR_UP_ID | high_bad | both_registered | -0.1412 | 0.7596 | 0.2595 |
| A06 | K | J_B4_MR_UP_ID | low_bad | both_registered | -0.04679 | -0.2285 | -0.1276 |
| A06 | K | J_B4_ROS_DN_CC | high_bad | both_registered | 0.1483 | 0.5297 | 0.3179 |
| A06 | K | J_B4_ROS_DN_CC | low_bad | both_registered | -0.08312 | -0.135 | -0.1062 |
| A06 | K | J_B4_ROS_DN_ID | high_bad | both_registered | 0.119 | 0.4772 | 0.2783 |
| A06 | K | J_B4_ROS_DN_ID | low_bad | both_registered | -0.132 | -0.2665 | -0.1919 |
| A06 | K | J_B4_ROS_UP_CC | high_bad | both_registered | 0.08976 | 0.46 | 0.2545 |
| A06 | K | J_B4_ROS_UP_CC | low_bad | both_registered | -0.2447 | -0.4525 | -0.3371 |
| A06 | K | J_B4_ROS_UP_ID | high_bad | both_registered | -0.05325 | 0.5887 | 0.2323 |
| A06 | K | J_B4_ROS_UP_ID | low_bad | both_registered | -0.2501 | -0.3039 | -0.274 |
| R1 | K | J_B4_ASYM_MR_CC | high_bad | both_registered | 0.1826 | 0.1797 | 0.1813 |
| R1 | K | J_B4_ASYM_MR_CC | low_bad | both_registered | -0.02276 | -0.05433 | -0.0368 |
| R1 | K | J_B4_ASYM_MR_ID | high_bad | both_registered | 0.08341 | 0.02993 | 0.05962 |
| R1 | K | J_B4_ASYM_MR_ID | low_bad | both_registered | 0.1379 | -0.02083 | 0.06727 |
| R1 | K | J_B4_ASYM_ROS_CC | high_bad | both_registered | 0.166 | -0.125 | 0.03651 |
| R1 | K | J_B4_ASYM_ROS_CC | low_bad | both_registered | 0.05694 | 0.07074 | 0.06308 |
| R1 | K | J_B4_ASYM_ROS_ID | high_bad | both_registered | 0.0009606 | -0.0197 | -0.008229 |
| R1 | K | J_B4_ASYM_ROS_ID | low_bad | both_registered | 0.01466 | 0.1086 | 0.05643 |
| R1 | K | J_B4_MR_DN_CC | high_bad | both_registered | 0.1012 | 0.5413 | 0.297 |
| R1 | K | J_B4_MR_DN_CC | low_bad | both_registered | -0.04292 | -0.6158 | -0.2978 |
| R1 | K | J_B4_MR_DN_ID | high_bad | both_registered | 0.1375 | 0.7259 | 0.3992 |
| R1 | K | J_B4_MR_DN_ID | low_bad | both_registered | -0.2674 | -0.3773 | -0.3163 |
| R1 | K | J_B4_MR_UP_CC | high_bad | both_registered | 0.2351 | 0.5701 | 0.3841 |
| R1 | K | J_B4_MR_UP_CC | low_bad | both_registered | -0.01997 | -0.5221 | -0.2433 |
| R1 | K | J_B4_MR_UP_ID | high_bad | both_registered | 0.1788 | 0.4778 | 0.3118 |
| R1 | K | J_B4_MR_UP_ID | low_bad | both_registered | -0.01803 | -0.6351 | -0.2925 |
| R1 | K | J_B4_ROS_DN_CC | high_bad | both_registered | 0.08188 | 0.4715 | 0.2552 |
| R1 | K | J_B4_ROS_DN_CC | low_bad | both_registered | -0.1635 | -0.6311 | -0.3715 |
| R1 | K | J_B4_ROS_DN_ID | high_bad | both_registered | 0.09048 | 0.5772 | 0.307 |
| R1 | K | J_B4_ROS_DN_ID | low_bad | both_registered | -0.2602 | -0.4682 | -0.3527 |
| R1 | K | J_B4_ROS_UP_CC | high_bad | both_registered | 0.239 | 0.4071 | 0.3138 |
| R1 | K | J_B4_ROS_UP_CC | low_bad | both_registered | -0.1456 | -0.5131 | -0.3091 |
| R1 | K | J_B4_ROS_UP_ID | high_bad | both_registered | 0.2316 | 0.4232 | 0.3168 |
| R1 | K | J_B4_ROS_UP_ID | low_bad | both_registered | -0.07647 | -0.6251 | -0.3205 |
| R2 | K | J_B4_ASYM_MR_CC | high_bad | both_registered | 0.08659 | 0.719 | 0.3679 |
| R2 | K | J_B4_ASYM_MR_CC | low_bad | both_registered | -0.1803 | 0.3066 | 0.03629 |
| R2 | K | J_B4_ASYM_MR_ID | high_bad | both_registered | -0.2262 | 0.05674 | -0.1003 |
| R2 | K | J_B4_ASYM_MR_ID | low_bad | both_registered | 0.1815 | 0.2305 | 0.2033 |
| R2 | K | J_B4_ASYM_ROS_CC | high_bad | both_registered | 0.1511 | -0.1387 | 0.0222 |
| R2 | K | J_B4_ASYM_ROS_CC | low_bad | both_registered | -0.1285 | 0.3609 | 0.08925 |
| R2 | K | J_B4_ASYM_ROS_ID | high_bad | both_registered | 0.05232 | 0.1791 | 0.1087 |
| R2 | K | J_B4_ASYM_ROS_ID | low_bad | both_registered | -0.1188 | 0.2779 | 0.05766 |
| R2 | K | J_B4_MR_DN_CC | high_bad | both_registered | 0.04429 | 0.9841 | 0.4624 |
| R2 | K | J_B4_MR_DN_CC | low_bad | both_registered | -0.2593 | -0.04257 | -0.1629 |
| R2 | K | J_B4_MR_DN_ID | high_bad | both_registered | 0.2831 | 0.9379 | 0.5744 |
| R2 | K | J_B4_MR_DN_ID | low_bad | both_registered | -0.2523 | -0.4737 | -0.3508 |
| R2 | K | J_B4_MR_UP_CC | high_bad | both_registered | 0.09027 | 0.9686 | 0.481 |
| R2 | K | J_B4_MR_UP_CC | low_bad | both_registered | -0.2451 | -0.2619 | -0.2526 |
| R2 | K | J_B4_MR_UP_ID | high_bad | both_registered | 0.1427 | 0.7076 | 0.394 |
| R2 | K | J_B4_MR_UP_ID | low_bad | both_registered | -0.1176 | -0.317 | -0.2063 |
| R2 | K | J_B4_ROS_DN_CC | high_bad | both_registered | 0.05944 | 0.9533 | 0.4571 |
| R2 | K | J_B4_ROS_DN_CC | low_bad | both_registered | -0.1428 | -0.2425 | -0.1872 |
| R2 | K | J_B4_ROS_DN_ID | high_bad | both_registered | -0.02482 | 1.093 | 0.4725 |
| R2 | K | J_B4_ROS_DN_ID | low_bad | both_registered | -0.1084 | -0.2238 | -0.1597 |
| R2 | K | J_B4_ROS_UP_CC | high_bad | both_registered | 0.1891 | 0.8609 | 0.4879 |
| R2 | K | J_B4_ROS_UP_CC | low_bad | both_registered | -0.1528 | -0.4729 | -0.2952 |
| R2 | K | J_B4_ROS_UP_ID | high_bad | both_registered | 0.1605 | 1.009 | 0.538 |
| R2 | K | J_B4_ROS_UP_ID | low_bad | both_registered | -0.1938 | -0.1738 | -0.1849 |


### Q12 / Q03：事件基线（RARPRE / R_ev / R_ev5 / U × CC / ID × W20 / 60 × 时钟）

> 表头：主体=B5 全部对象｜算子=FALLBACK SLOT（研究引擎）｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=推导段 2010-2014 / 2015-2018｜单位=D_FULL 年化百分点｜日期=2010-01-04..2018-12-31｜H=5（主配置）｜成本模型=8bp 线性｜支持=native FALLBACK｜资本视图=NATIVE｜exposure=见表内 source 列｜query_id=P1-Q09


| mother | stat | direction | CC_W20_LT | CC_W20_SE | CC_W60_LT | CC_W60_SE | ID_W20_LT | ID_W20_SE | ID_W60_LT | ID_W60_SE |
|---|---|---|---|---|---|---|---|---|---|---|
| A06 | RARPRE | high_bad | -0.0728 | -0.0806 | 0.055 | 0.0597 | 0.2197 | 0.2255 | 0.3357 | 0.3823 |
| A06 | RARPRE | low_bad | 0.2359 | 0.2486 | 0.2656 | 0.2896 | 0.0159 | 0.0364 | 0.0318 | 0.0232 |
| A06 | REV | high_bad | 0.0263 | 0.0004 | -0.1015 | -0.1878 | 0.0479 | -0.2953 | -0.0758 | -0.3152 |
| A06 | REV | low_bad | 0.0624 | -0.0285 | 0.1135 | 0.1414 | 0.0396 | 0.1652 | 0.19 | 0.3101 |
| A06 | REV5 | high_bad | -0.0525 | -0.0941 | -0.1581 | -0.265 | -0.1102 | -0.2689 | -0.1496 | -0.3354 |
| A06 | REV5 | low_bad | 0.0984 | 0.1699 | 0.2042 | 0.2305 | 0.1643 | 0.2511 | 0.2948 | 0.3896 |
| A06 | U | high_bad | 0.1364 | 0.1546 | 0.1333 | 0.1096 | 0.0435 | 0.0117 | -0.0822 | -0.0324 |
| A06 | U | low_bad | 0.0222 | -0.0217 | -0.0531 | -0.0621 | 0.0673 | 0.0508 | 0.0443 | 0.0527 |
| R1 | RARPRE | high_bad | -0.2456 | -0.2401 | -0.1815 | -0.1305 | -0.067 | -0.0887 | -0.0485 | 0.0151 |
| R1 | RARPRE | low_bad | 0.4484 | 0.5506 | 0.3751 | 0.3999 | 0.3547 | 0.3581 | 0.2636 | 0.24 |
| R1 | REV | high_bad | 0.1223 | -0.0351 | 0.0669 | -0.0733 | 0.0734 | -0.0514 | 0.1238 | -0.0553 |
| R1 | REV | low_bad | -0.0943 | 0.1169 | -0.0174 | 0.1375 | -0.0805 | 0.2161 | 0.0895 | 0.1562 |
| R1 | REV5 | high_bad | -0.0225 | -0.1086 | 0.0318 | -0.1342 | -0.0507 | -0.0712 | -0.056 | -0.1146 |
| R1 | REV5 | low_bad | 0.0336 | 0.2643 | 0.2083 | 0.2576 | 0.1043 | 0.2144 | 0.2294 | 0.2337 |
| R1 | U | high_bad | 0.1496 | 0.1293 | 0.1388 | 0.171 | 0.1332 | 0.1226 | 0.1642 | 0.1395 |
| R1 | U | low_bad | 0.0518 | -0.077 | -0.0525 | -0.0493 | 0.0347 | 0.0276 | 0.0027 | -0.02 |
| R2 | RARPRE | high_bad | -0.3659 | -0.3509 | -0.2214 | -0.2164 | -0.0424 | -0.0431 | 0.0026 | -0.0443 |
| R2 | RARPRE | low_bad | 0.3889 | 0.3964 | 0.4562 | 0.3934 | 0.3205 | 0.3208 | 0.2952 | 0.2848 |
| R2 | REV | high_bad | 0.126 | 0.116 | 0.2575 | -0 | 0.1119 | 0.0625 | 0.103 | -0.1315 |
| R2 | REV | low_bad | 0.0184 | 0.0113 | 0.1524 | 0.1805 | 0.1881 | 0.122 | 0.3184 | 0.2975 |
| R2 | REV5 | high_bad | 0.0272 | 0.004 | 0.0748 | -0.1779 | 0.1741 | -0.0407 | -0.0094 | -0.1976 |
| R2 | REV5 | low_bad | -0.0825 | 0.2137 | 0.1751 | 0.2415 | 0.0222 | 0.1977 | 0.3107 | 0.4188 |
| R2 | U | high_bad | 0.3125 | 0.1639 | 0.1666 | 0.185 | 0.1789 | 0.0679 | 0.1586 | 0.151 |
| R2 | U | low_bad | -0.0369 | 0.0441 | 0.1255 | 0.104 | 0.0325 | 0.0441 | 0.128 | 0.1658 |


### Q14：T 窄种子（T 槽位；含 A08）

> 表头：主体=Q14：T 窄种子（T 槽位；含 A08）｜算子=FALLBACK SLOT（研究引擎）｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=推导段 2010-2014 / 2015-2018｜单位=子 − 母 8bp 日配对增量，年化百分点｜日期=2010-01-04..2018-12-31｜H=5（主配置）｜成本模型=8bp 线性｜支持=native FALLBACK｜资本视图=NATIVE｜exposure=见表内 source 列｜query_id=P1-Q10


| mother | slot | measurement_id | direction | direction_role | D_2010-2014 | D_2015-2018 | D_FULL |
|---|---|---|---|---|---|---|---|
| A06 | T | J_B6_CV20 | high_bad | main | 0.305 | 0.5863 | 0.4301 |
| A06 | T | J_B6_CV20 | low_bad | competitor | -0.3307 | -0.8567 | -0.5647 |
| A06 | T | J_B6_DETREND20 | high_bad | main | 0.392 | 0.5958 | 0.4827 |
| A06 | T | J_B6_DETREND20 | low_bad | competitor | -0.1672 | -0.8068 | -0.4517 |
| A06 | T | J_B6_RELROLL20 | high_bad | main | 0.3079 | 0.5691 | 0.4241 |
| A06 | T | J_B6_RELROLL20 | low_bad | competitor | -0.1365 | -0.6001 | -0.3427 |
| A06 | T | T_ewcv20 | high_bad | main | 0.4347 | 0.5778 | 0.4983 |
| A06 | T | T_ewcv20 | low_bad | competitor | -0.2655 | -0.9188 | -0.5561 |
| A08 | T | J_B6_CV20 | high_bad | main | 0.8815 | 0.749 | 0.8226 |
| A08 | T | J_B6_CV20 | low_bad | competitor | -0.5698 | -1.041 | -0.7793 |
| A08 | T | J_B6_DETREND20 | high_bad | main | 0.6662 | 0.569 | 0.623 |
| A08 | T | J_B6_DETREND20 | low_bad | competitor | -0.3728 | -1.083 | -0.6885 |
| A08 | T | J_B6_RELROLL20 | high_bad | main | 0.6701 | 0.2529 | 0.4845 |
| A08 | T | J_B6_RELROLL20 | low_bad | competitor | -0.3288 | -0.7756 | -0.5276 |
| A08 | T | T_ewcv20 | high_bad | main | 0.9318 | 0.8036 | 0.8748 |
| A08 | T | T_ewcv20 | low_bad | competitor | -0.5729 | -1.234 | -0.8671 |
| R1 | T | J_B6_CV20 | high_bad | main | 0.4033 | 0.142 | 0.2871 |
| R1 | T | J_B6_CV20 | low_bad | competitor | -0.2824 | -0.465 | -0.3636 |
| R1 | T | J_B6_DETREND20 | high_bad | main | 0.4154 | -0.06082 | 0.2036 |
| R1 | T | J_B6_DETREND20 | low_bad | competitor | -0.3397 | -0.4711 | -0.3981 |
| R1 | T | J_B6_RELROLL20 | high_bad | main | 0.3765 | 0.197 | 0.2967 |
| R1 | T | J_B6_RELROLL20 | low_bad | competitor | -0.4164 | -0.4598 | -0.4357 |
| R1 | T | T_ewcv20 | high_bad | main | 0.4999 | 0.2675 | 0.3965 |
| R1 | T | T_ewcv20 | low_bad | competitor | -0.4545 | -0.672 | -0.5512 |
| R2 | T | J_B6_CV20 | high_bad | main | 0.2003 | 0.4705 | 0.3205 |
| R2 | T | J_B6_CV20 | low_bad | competitor | -0.4979 | -0.7793 | -0.6231 |
| R2 | T | J_B6_DETREND20 | high_bad | main | 0.286 | 0.1024 | 0.2043 |
| R2 | T | J_B6_DETREND20 | low_bad | competitor | -0.4355 | -0.6743 | -0.5417 |
| R2 | T | J_B6_RELROLL20 | high_bad | main | 0.4118 | 0.4694 | 0.4375 |
| R2 | T | J_B6_RELROLL20 | low_bad | competitor | -0.3895 | -0.6263 | -0.4948 |
| R2 | T | T_ewcv20 | high_bad | main | 0.3416 | 0.4047 | 0.3696 |
| R2 | T | T_ewcv20 | low_bad | competitor | -0.3623 | -0.9589 | -0.6277 |


### Q14：同业相对位置（K / T 两位置分域）

> 表头：主体=Q14：同业相对位置（K / T 两位置分域）｜算子=FALLBACK SLOT（研究引擎）｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=推导段 2010-2014 / 2015-2018｜单位=子 − 母 8bp 日配对增量，年化百分点｜日期=2010-01-04..2018-12-31｜H=5（主配置）｜成本模型=8bp 线性｜支持=native FALLBACK｜资本视图=NATIVE｜exposure=见表内 source 列｜query_id=P1-Q11


| mother | slot | measurement_id | direction | direction_role | D_2010-2014 | D_2015-2018 | D_FULL |
|---|---|---|---|---|---|---|---|
| A06 | K | R_peer20 | high_bad | main | -0.05383 | 0.3385 | 0.1207 |
| A06 | T | R_peer20 | high_bad | main | 0.1151 | 0.1381 | 0.1253 |
| A06 | K | R_peer20 | low_bad | competitor | -0.2745 | 0.1246 | -0.09692 |
| A06 | T | R_peer20 | low_bad | competitor | -0.1303 | -0.4675 | -0.2803 |
| R1 | K | R_peer20 | high_bad | main | 0.08608 | 0.4809 | 0.2617 |
| R1 | T | R_peer20 | high_bad | main | 0.3081 | 0.6135 | 0.444 |
| R1 | K | R_peer20 | low_bad | competitor | 0.08043 | -0.112 | -0.005165 |
| R1 | T | R_peer20 | low_bad | competitor | -0.1712 | -0.9398 | -0.5131 |
| R2 | K | R_peer20 | high_bad | main | 0.1668 | 0.7432 | 0.4232 |
| R2 | T | R_peer20 | high_bad | main | 0.283 | 0.3226 | 0.3006 |
| R2 | K | R_peer20 | low_bad | competitor | -0.1304 | -0.03067 | -0.08602 |
| R2 | T | R_peer20 | low_bad | competitor | -0.3803 | -0.9066 | -0.6144 |


## 3. 源表示与本轮新表示（同母体、主配置）

> 表头：主体=源 / 新表示配对｜算子=FALLBACK SLOT（研究引擎）｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=推导段 2010-2014 / 2015-2018｜单位=子 − 母 8bp 日配对增量，年化百分点｜日期=2010-01-04..2018-12-31｜H=5（主配置）｜成本模型=8bp 线性｜支持=native FALLBACK｜资本视图=NATIVE｜exposure=见表内 source 列｜query_id=P1-Q12


| mother | object_a | FULL_a | note | object_b | FULL_b | a_minus_b |
|---|---|---|---|---|---|---|
| R1 | K_rar20\|low_bad | 0.5289 | 源 S（E6i 缓存，最少观测 14）vs J 自包含版（最少 10；代数同式） | J_B1_S20lag\|low_bad | 0.5243 | 0.004602 |
| R2 | K_rar20\|low_bad | 0.4583 | 源 S（E6i 缓存，最少观测 14）vs J 自包含版（最少 10；代数同式） | J_B1_S20lag\|low_bad | 0.4685 | -0.01016 |
| A06 | K_rar20\|low_bad | 0.2414 | 源 S（E6i 缓存，最少观测 14）vs J 自包含版（最少 10；代数同式） | J_B1_S20lag\|low_bad | 0.2993 | -0.05789 |
| R1 | J_B2_POINT_TR_CC\|high_bad | 0 | K0 锚（J 原值 = K0 逐位 → 账户 = 母体，增量应为 0） |  |  |  |
| R2 | J_B2_POINT_TR_CC\|high_bad | 0 | K0 锚（J 原值 = K0 逐位 → 账户 = 母体，增量应为 0） |  |  |  |
| A06 | J_B2_POINT_TR_CC\|high_bad | 0 | K0 锚（J 原值 = K0 逐位 → 账户 = 母体，增量应为 0） |  |  |  |


## 4. 同资本与含冲击（主配置，按块汇总）

> 表头：主体=B 包主配置对象（按块）｜算子=FALLBACK SLOT（研究引擎）｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=推导段 2010-2014 / 2015-2018｜单位=子 − 母 8bp 日配对增量，年化百分点｜日期=2010-01-04..2018-12-31｜H=5（主配置）｜成本模型=8bp；另列 A=5 亿 κ=.5 平方根冲击｜支持=native FALLBACK｜资本视图=NATIVE / MATCH-CAP（逐形成日共同资本只缩不放）｜exposure=见表内 source 列｜query_id=P1-Q13


| block | native_median | same_capital_median | impact_A5k05_median | native_vs_samecap_sign_agree_share |
|---|---|---|---|---|
| B1 | 0.162 | 0.1536 | 0.2403 | 1 |
| B2 | 0.04496 | 0.03414 | 0.1264 | 0.9688 |
| B3A | 0.228 | 0.189 | 0.2785 | 0.9667 |
| B3B | 0.06793 | 0.02681 | 0.1585 | 0.9167 |
| B3C | 0.4019 | 0.3971 | 0.4102 | 1 |
| B4 | 0.04958 | 0.02184 | 0.1013 | 0.9167 |
| B5 | 0.06706 | 0.05676 | 0.1404 | 0.9375 |
| B6 | -0.06959 | -0.06495 | -0.1444 | 1 |
| B7 | 0.05777 | 0.007991 | 0.06236 | 0.6667 |


## 5. A1-auto 与记录 B 清单

> 表头：主体=A1-auto 七项｜算子=机械对账｜分母=推导两段有效配对日｜基准=同 H 研究母体（R1 / R2 / A06 / A08）｜子集=全部登记对象｜单位=PASS / FAIL｜日期=—｜H=—｜成本模型=—｜支持=—｜资本视图=—｜exposure=见表内 source 列｜query_id=P1-Q14


| item | what | status | detail |
|---|---|---|---|
| 1 | 登记对账：问题→对象、任务→对象两表逐元组相等；B 每段计数 = 编译器现算；P = 528 | PASS | B=13398（brief 写 13,230；plan §5.10 现算 13,398）P=528 |
| 2 | 五类身份齐全（measurement / orientation / operator / parent / account）；方向论证句与双向标记；hypothesis_id ⊂ Q01–Q17；exposure 标记齐 | PASS | rows=210；exposure 类型 ['alias_of', 'direction_2of1', 'new_combination', 'related_exposed', 'source_member_seen'] |
| 3 | 槽位合法（A08 无 K、B6 只 T、B7 K / T 分域）；每对象含主配置 .25 × H5；H = {1,2,3,5,10,15,20}；α = {.125,.25,.5} | PASS |  |
| 4 | 锁定值非空且与 brief 一致 | PASS | {"policy_aggregation": "FULL_E6I_ALL4", "random_ref": "R-MATCH-SRC (Z-MAP basic)", "capital_ref": "same_capital", "delta": 0.1, "delta_sensitivity": [0.05, 0.15], "policy_confirmation_status": "confirmed_by_proceeding", "main_config": {"alpha": 0.25, "H": 5}, "cost_bp": 8.0} |
| 5 | source_resolution.md 覆盖 §1.3 七条源事实；差异逐条登记 | PASS |  |
| 6 | Stage 0 六项锚全 PASS | PASS |  |
| 7 | B 草稿逐对象含 source exposure / 机制重要性 / 有效支持 / 推导读数 / 未解决限制；无"推导中位 ≤ 0"门 | PASS | 对象 638 / 应有 638 |


记录 B 草稿：`reports/E6j_record_B_draft.md` 与 `registration/record_B_draft_objects.csv`（638 个对象，逐对象 source exposure / 机制重要性 / 有效支持 / 推导读数 / 未解决限制）。方式 B 事前整表授权下，后段对象 = 冻结清单全部对象，不按推导读数增删〔P1-Q14〕。

## 6. 限制与待补

- 随机参照三类（R-SCORE-IID / R-COND / EDIT-ENTRY，1,024 路径起）与 COMMON_SUPPORT 四账户、TRANSPORT、剂量控制（B3-C）在 part1b 补；本文件的读数都是"子 − 母"原生增量。

- 一个 2010-2014 R2 × B3C 的 32 路径随机分片是测时样本，其路径作为该配置 1,024 路径中的前 32 条保留，不单独读数。

- 两推导段已在 E6i 中暴露于同源母体的成员选择（exposure：`registration/selection_exposure_ledger.csv`）；推导段读数不是样本外证据。
