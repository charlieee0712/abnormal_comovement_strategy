# E6l REPORT cards —— 16 张卡：每个 query 一张表（对象集合与绑定比较）

用途：plan §12 / §13.4 cards。每张卡先列登记原文（Stage B 冻结，⑬ 为推导段 MDE80 机械填），再按 query 给对象统计与绑定比较的 FULL / G4；结论词只来自预登记的读法，不据结果改卡。登记文本里库存标记到上限的技术词在正文写作“满额（saturation）”（禁用词扫描按字面；登记文件原文不改，见 `registry/query_registry_E6l.csv`）。

## E6L-Q01｜当前HG线索能否在正确身份与正式尺子下复现？

- ⑮ Y00=parent|Y10=Q0 NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=Q0 NATIVE|Y01=K0 HG15|Y11=self；Y00=parent|Y10=Q0 NATIVE|Y01=K0 HG5|Y11=self；child−parent；⑯ meas=1d|decision=recursive(unbounded)×1080；meas=20d|decision=same_day×720；meas=3d|decision=recursive(unbounded)×576；meas=3d|decision=same_day×360；meas=1d|decision=same_day×360；meas=source|decision=recursive(unbounded)×360；⑰ RANDOM_NOT_SCHEDULED×2226；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×976；NO_NEW_CONTENT_TO_PERMUTE×502；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×54；RMARK×3×18；⑱ NOT_APPLICABLE×3764；三时钟账本（形成 / 日历 / 交易）×12

- ⑬（推导段 MDE80 中位）：2010-2014 MDE80 中位 > .30：首看，只记录；2015-2018 MDE80 中位 > .30：首看，只记录

> 表头：主体=E6k 同构对象逐值复现（D 段 / n / D_sc / FULL / G4 vs policy_E6k）｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=e6k_equiv != 'NOT_APPLICABLE'｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q01-a


| item | value |
|---|---|
| objects | 2776 |
| share_FULL_pos | 0.9517 |
| median_FULL_ann_pp | 0.1907 |
| median_G4_ann_pp | 0.175 |
| median_FULL_sc_ann_pp | 0.1441 |
| policy_PORT3_T_FULL_pass | 430 |
| bound_comparisons_rows | 0 |


> 表头：主体=Q0 × NATIVE / HG5 / HG10 / HG15 各 α / H 的正式尺子（PORT3_T 主列）与四段 lo / hi｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=meas=='Q0' & op.isin(['NATIVE','HG5','HG10','HG15'])｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q01-b


| item | value |
|---|---|
| objects | 1440 |
| share_FULL_pos | 0.9319 |
| median_FULL_ann_pp | 0.2726 |
| median_G4_ann_pp | 0.239 |
| median_FULL_sc_ann_pp | 0.1618 |
| policy_PORT3_T_FULL_pass | 200 |
| bound_comparisons_rows | 168480 |
| cmp:PARENT median_D_ann_pp（段行） | 0.1705 |
| cmp:PARENT share_D_pos（段行） | 0.7429 |
| cmp:REAL_MINUS_LEGACY median_D_ann_pp（段行） | 0.2063 |
| cmp:REAL_MINUS_LEGACY share_D_pos（段行） | 0.8109 |


> 表头：主体=W09：Q0|A4b_CVRv5|a0.5|H5|HG10 四段组合层 lo_T / hi_T 追查｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=desc_id=='Q0|A4b_CVRv5|a0.5|H5|HG10'｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q01-c


| item | value |
|---|---|
| objects | 1 |
| share_FULL_pos | 1 |
| median_FULL_ann_pp | 1.109 |
| median_G4_ann_pp | 1.281 |
| median_FULL_sc_ann_pp | 1.021 |
| policy_PORT3_T_FULL_pass | 0 |
| bound_comparisons_rows | 0 |


## E6L-Q02｜“规则有用”中多少是净选股路径，多少是费用？

- ⑮ Y00=parent|Y10=Q_DEW5 NATIVE|Y01=K0 HG5|Y11=self；Y00=parent|Y10=Q_DMED5 NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=Q_DMED5 NATIVE|Y01=K0 HG15|Y11=self；child−parent；⑯ meas=5d|decision=recursive(unbounded)×8280；meas=3d|decision=recursive(unbounded)×6480；meas=1d|decision=recursive(unbounded)×3240；meas=10d|decision=recursive(unbounded)×2160；meas=source|decision=recursive(unbounded)×1080；meas=5d|decision=confirmed_decay_L2×720；⑰ RANDOM_NOT_SCHEDULED×18648；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×7830；NO_NEW_CONTENT_TO_PERMUTE×1542；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×162；RMARK×3×18；⑱ NOT_APPLICABLE×23358；Vol3 四调度（UNKNOWN→b10；STRICT250 对照）×4800；三时钟账本（形成 / 日历 / 交易）×42

- ⑬（推导段 MDE80 中位）：2010-2014 .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号；2015-2018 MDE80 中位 > .30：首看，只记录

> 表头：主体=信息 × 规则四账户（Y00 / Y10 / Y01 / Y11）gross / 线性费用 / 冲击 / 资本 / 换手分列｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=family.isin(['HG','MEMORY','STATE']) & meas!='K0'｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q02-a


| item | value |
|---|---|
| objects | 26640 |
| share_FULL_pos | 0.8845 |
| median_FULL_ann_pp | 0.1898 |
| median_G4_ann_pp | 0.1732 |
| median_FULL_sc_ann_pp | 0.1142 |
| policy_PORT3_T_FULL_pass | 2503 |
| bound_comparisons_rows | 319680 |
| cmp:FOUR_ACCOUNT_INFO_RULE median_D_ann_pp（段行） | 0.02208 |
| cmp:FOUR_ACCOUNT_INFO_RULE share_D_pos（段行） | 0.5605 |
| cmp:RULE_ONLY median_D_ann_pp（段行） | 0.1218 |
| cmp:RULE_ONLY share_D_pos（段行） | 0.7077 |
| cmp:SAME_MEAS_NATIVE median_D_ann_pp（段行） | 0.08547 |
| cmp:SAME_MEAS_NATIVE share_D_pos（段行） | 0.7303 |


> 表头：主体=零费敏感（gross 差）与规则 ONLY（旧 K）账户｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=meas=='K0' & family=='OLD_RULE'｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q02-b


| item | value |
|---|---|
| objects | 1560 |
| share_FULL_pos | 0.8763 |
| median_FULL_ann_pp | 0.06971 |
| median_G4_ann_pp | 0.0657 |
| median_FULL_sc_ann_pp | 0.04677 |
| policy_PORT3_T_FULL_pass | 0 |
| bound_comparisons_rows | 0 |


## E6L-Q03｜平均活动、安静日与持续相对安静，哪种更匹配母体？

- ⑮ Y00=parent|Y10=Q0 NATIVE|Y01=K0 DECAY2_10|Y11=self；Y00=parent|Y10=Q0 NATIVE|Y01=K0 DECAY5_10|Y11=self；Y00=parent|Y10=Q0 NATIVE|Y01=K0 HG10|Y11=self；child−parent；⑯ meas=5d|decision=recursive(unbounded)×5472；meas=1d|decision=recursive(unbounded)×3240；meas=5d|decision=same_day×1152；meas=1d|decision=1d_nonrecursive×360；meas=1d|decision=confirmed_decay_L5×360；meas=1d|decision=confirmed_decay_L2×360；⑰ RANDOM_NOT_SCHEDULED×9072；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×4086；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×126；⑱ NOT_APPLICABLE×10332；Vol3 四调度（UNKNOWN→b10；STRICT250 对照）×2880；三时钟账本（形成 / 日历 / 交易）×72

- ⑬（推导段 MDE80 中位）：2010-2014 MDE80 中位 > .30：首看，只记录；2015-2018 MDE80 中位 > .30：首看，只记录

> 表头：主体=Q_D5 / Q_QMEAN5 / Q_DMED5 / Q0 同 α / H / 算子；ε 主导份额；名单差｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=meas.isin(['Q0','Q_D5','Q_QMEAN5','Q_DMED5'])｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q03-a


| item | value |
|---|---|
| objects | 12960 |
| share_FULL_pos | 0.8397 |
| median_FULL_ann_pp | 0.1805 |
| median_G4_ann_pp | 0.1583 |
| median_FULL_sc_ann_pp | 0.09519 |
| policy_PORT3_T_FULL_pass | 998 |
| bound_comparisons_rows | 126720 |
| cmp:MEAN_KERNEL_PAIR median_D_ann_pp（段行） | 0.02812 |
| cmp:MEAN_KERNEL_PAIR share_D_pos（段行） | 0.5879 |
| cmp:SAME_OPERATOR_Q0 median_D_ann_pp（段行） | -0.1188 |
| cmp:SAME_OPERATOR_Q0 share_D_pos（段行） | 0.2403 |


> 表头：主体=KERNEL_DOSE（同均值 / RMS 控制）vs 平滑账户（432 支持格）｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=kernel_support｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q03-b


| item | value |
|---|---|
| objects | 432 |
| share_FULL_pos | 0.9236 |
| median_FULL_ann_pp | 0.1931 |
| median_G4_ann_pp | 0.1811 |
| median_FULL_sc_ann_pp | 0.1428 |
| policy_PORT3_T_FULL_pass | 112 |
| bound_comparisons_rows | 1728 |
| cmp:KERNEL_DOSE median_D_ann_pp（段行） | -0.1119 |
| cmp:KERNEL_DOSE share_D_pos（段行） | 0.2442 |


## E6L-Q04｜等信息年龄的MA/EW是否仍有实质不同？

- ⑮ Y00=parent|Y10=Q_D3 NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=Q_D3 NATIVE|Y01=K0 HG15|Y11=self；Y00=parent|Y10=Q_D3 NATIVE|Y01=K0 HG5|Y11=self；child−parent；⑯ meas=5d|decision=recursive(unbounded)×4320；meas=3d|decision=recursive(unbounded)×2160；meas=3d|decision=same_day×720；meas=5d|decision=same_day×720；meas=5d|decision=confirmed_decay_L2×360；meas=5d|decision=1d_nonrecursive×360；⑰ RANDOM_NOT_SCHEDULED×6552；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×2754；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×54；⑱ NOT_APPLICABLE×7890；Vol3 四调度（UNKNOWN→b10；STRICT250 对照）×1440；三时钟账本（形成 / 日历 / 交易）×30

- ⑬（推导段 MDE80 中位）：2010-2014 .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号；2015-2018 MDE80 中位 > .30：首看，只记录

> 表头：主体=D3 vs DEW3、D5 vs DEW5（同 α / H / 算子）｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=meas.isin(['Q_D3','Q_DEW3','Q_D5','Q_DEW5'])｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q04-a


| item | value |
|---|---|
| objects | 9360 |
| share_FULL_pos | 0.8027 |
| median_FULL_ann_pp | 0.1446 |
| median_G4_ann_pp | 0.1282 |
| median_FULL_sc_ann_pp | 0.001868 |
| policy_PORT3_T_FULL_pass | 385 |
| bound_comparisons_rows | 23040 |
| cmp:MA_VS_EW median_D_ann_pp（段行） | -0.02176 |
| cmp:MA_VS_EW share_D_pos（段行） | 0.4085 |
| cmp:WINDOW_PAIR median_D_ann_pp（段行） | -0.00943 |
| cmp:WINDOW_PAIR share_D_pos（段行） | 0.4694 |


> 表头：主体=EW 有效权重 / 平均年龄与有效数份额（测量事实）｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=meas.isin(['Q_DEW3','Q_DEW5'])｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q04-b


| item | value |
|---|---|
| objects | 2880 |
| share_FULL_pos | 0.8139 |
| median_FULL_ann_pp | 0.149 |
| median_G4_ann_pp | 0.1406 |
| median_FULL_sc_ann_pp | 0.007788 |
| policy_PORT3_T_FULL_pass | 125 |
| bound_comparisons_rows | 0 |


## E6L-Q05｜排名平滑是否只是观察池历史选择或剂量收缩？

- ⑮ Y00=parent|Y10=Q_RANK5 NATIVE|Y01=K0 DECAY2_10|Y11=self；Y00=parent|Y10=Q_RANKOBS5 NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=Q_RANKSCORE5 NATIVE|Y01=K0 HG10|Y11=self；child−parent；⑯ meas=5d|decision=recursive(unbounded)×1872；meas=5d|decision=same_day×1152；meas=5d|decision=1d_nonrecursive×360；meas=5d|decision=confirmed_decay_L2×360；meas=5d|decision=confirmed_decay_L5×360；meas=3d|decision=recursive(unbounded)×54；⑰ RANDOM_NOT_SCHEDULED×3024；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×1548；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×72；⑱ NOT_APPLICABLE×4602；三时钟账本（形成 / 日历 / 交易）×42

- ⑬（推导段 MDE80 中位）：2010-2014 .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号；2015-2018 MDE80 中位 > .30：首看，只记录

> 表头：主体=RANK5 vs RANKOBS5 vs RANKSCORE5｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=meas.isin(['Q_RANK5','Q_RANKOBS5','Q_RANKSCORE5'])｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q05-a


| item | value |
|---|---|
| objects | 4320 |
| share_FULL_pos | 0.8859 |
| median_FULL_ann_pp | 0.1675 |
| median_G4_ann_pp | 0.1605 |
| median_FULL_sc_ann_pp | 0.09502 |
| policy_PORT3_T_FULL_pass | 369 |
| bound_comparisons_rows | 17280 |
| cmp:RANK_BRIDGE_PAIR median_D_ann_pp（段行） | 0.04137 |
| cmp:RANK_BRIDGE_PAIR share_D_pos（段行） | 0.6323 |
| cmp:WINDOW_PAIR median_D_ann_pp（段行） | 0.02134 |
| cmp:WINDOW_PAIR share_D_pos（段行） | 0.5801 |


> 表头：主体=支持桥（COMMON_SUPPORT 子 / 父、Q0 遮罩）与延伸覆盖｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=kernel_support｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q05-b


| item | value |
|---|---|
| objects | 432 |
| share_FULL_pos | 0.9236 |
| median_FULL_ann_pp | 0.1931 |
| median_G4_ann_pp | 0.1811 |
| median_FULL_sc_ann_pp | 0.1428 |
| policy_PORT3_T_FULL_pass | 112 |
| bound_comparisons_rows | 8640 |
| cmp:MASKQ0_CONTENT median_D_ann_pp（段行） | -0.1637 |
| cmp:MASKQ0_CONTENT share_D_pos（段行） | 0.1591 |
| cmp:MASKQ0_SUPPORT_ONLY median_D_ann_pp（段行） | 0 |
| cmp:MASKQ0_SUPPORT_ONLY share_D_pos（段行） | 0.2963 |
| cmp:SUPPORT_BRIDGE_CHILD_SUPPORT median_D_ann_pp（段行） | 0 |
| cmp:SUPPORT_BRIDGE_CHILD_SUPPORT share_D_pos（段行） | 0 |
| cmp:SUPPORT_BRIDGE_CONTENT median_D_ann_pp（段行） | -0.1624 |
| cmp:SUPPORT_BRIDGE_CONTENT share_D_pos（段行） | 0.1534 |
| cmp:SUPPORT_BRIDGE_PARENT_SUPPORT median_D_ann_pp（段行） | -3.791e-05 |
| cmp:SUPPORT_BRIDGE_PARENT_SUPPORT share_D_pos（段行） | 0.467 |


## E6L-Q06｜递归HG是否超过“昨日自然入选”的价值？

- ⑮ Y00=parent|Y10=C1 NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=C1 NATIVE|Y01=K0 LAG1_10|Y11=self；Y00=parent|Y10=M NATIVE|Y01=K0 HG10|Y11=self；child−parent；⑯ meas=5d|decision=recursive(unbounded)×2520；meas=3d|decision=recursive(unbounded)×1440；meas=5d|decision=1d_nonrecursive×720；meas=20d|decision=recursive(unbounded)×720；meas=10d|decision=recursive(unbounded)×720；meas=5d|decision=same_day×720；⑰ RANDOM_NOT_SCHEDULED×6048；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×2430；NO_NEW_CONTENT_TO_PERMUTE×222；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×162；RMARK×3×18；⑱ NOT_APPLICABLE×8832；三时钟账本（形成 / 日历 / 交易）×48

- ⑬（推导段 MDE80 中位）：2010-2014 .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号；2015-2018 .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号

> 表头：主体=HG10 vs LAG1_10 vs NATIVE（Q0 / Q_D5 / Q_RANK5 / C1）｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=op.isin(['HG10','LAG1_10','NATIVE']) & meas.isin(['Q0','Q_D5','Q_RANK5','C1'])｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q06-a


| item | value |
|---|---|
| objects | 4320 |
| share_FULL_pos | 0.8949 |
| median_FULL_ann_pp | 0.1753 |
| median_G4_ann_pp | 0.1599 |
| median_FULL_sc_ann_pp | 0.1088 |
| policy_PORT3_T_FULL_pass | 454 |
| bound_comparisons_rows | 6240 |
| cmp:MECHANISM_PAIR median_D_ann_pp（段行） | -0.01008 |
| cmp:MECHANISM_PAIR share_D_pos（段行） | 0.4321 |


> 表头：主体=记忆年龄分布（membership_age_ledger）｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=op.isin(['HG10','LAG1_10'])｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q06-b


| item | value |
|---|---|
| objects | 7440 |
| share_FULL_pos | 0.8913 |
| median_FULL_ann_pp | 0.1886 |
| median_G4_ann_pp | 0.1784 |
| median_FULL_sc_ann_pp | 0.121 |
| policy_PORT3_T_FULL_pass | 736 |
| bound_comparisons_rows | 0 |


## E6L-Q07｜衰减记忆能否保留短期保护并少留陈旧名字？

- ⑮ Y00=parent|Y10=C1 NATIVE|Y01=K0 DECAY2_10|Y11=self；Y00=parent|Y10=C1 NATIVE|Y01=K0 DECAY5_10|Y11=self；Y00=parent|Y10=C1 NATIVE|Y01=K0 HG10|Y11=self；child−parent；⑯ meas=5d|decision=recursive(unbounded)×2520；meas=3d|decision=recursive(unbounded)×1440；meas=5d|decision=confirmed_decay_L5×720；meas=5d|decision=confirmed_decay_L2×720；meas=10d|decision=recursive(unbounded)×720；meas=20d|decision=recursive(unbounded)×720；⑰ RANDOM_NOT_SCHEDULED×7056；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×2862；NO_NEW_CONTENT_TO_PERMUTE×502；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×162；RMARK×3×18；⑱ NOT_APPLICABLE×10552；三时钟账本（形成 / 日历 / 交易）×48

- ⑬（推导段 MDE80 中位）：2010-2014 MDE80 中位 ≤ .10：.10 级配对差可 80% 分辨；2015-2018 MDE80 中位 ≤ .10：.10 级配对差可 80% 分辨

> 表头：主体=DECAY2 / DECAY5 vs HG10 vs NATIVE｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=op.isin(['DECAY2_10','DECAY5_10','HG10','NATIVE']) & meas.isin(['Q0','Q_D5','Q_RANK5','C1','K0'])｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q07-a


| item | value |
|---|---|
| objects | 6120 |
| share_FULL_pos | 0.8995 |
| median_FULL_ann_pp | 0.1743 |
| median_G4_ann_pp | 0.1595 |
| median_FULL_sc_ann_pp | 0.1054 |
| policy_PORT3_T_FULL_pass | 635 |
| bound_comparisons_rows | 18720 |
| cmp:MECHANISM_PAIR median_D_ann_pp（段行） | -0.0004137 |
| cmp:MECHANISM_PAIR share_D_pos（段行） | 0.4924 |


> 表头：主体=纯 bonus 连续依靠日数 / 重确认年龄｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=op.isin(['DECAY2_10','DECAY5_10','HG10'])｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q07-b


| item | value |
|---|---|
| objects | 9000 |
| share_FULL_pos | 0.8938 |
| median_FULL_ann_pp | 0.19 |
| median_G4_ann_pp | 0.1794 |
| median_FULL_sc_ann_pp | 0.1236 |
| policy_PORT3_T_FULL_pass | 917 |
| bound_comparisons_rows | 0 |


## E6L-Q08｜库存身份是否比门内身份更符合成本动机？

- ⑮ Y00=parent|Y10=C1 NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=C1 NATIVE|Y01=K0 INV10|Y11=self；Y00=parent|Y10=C1 NATIVE|Y01=K0 LAG1_10|Y11=self；child−parent；⑯ meas=5d|decision=recursive(unbounded)×2520；meas=3d|decision=recursive(unbounded)×1440；meas=5d|decision=1d_nonrecursive×720；meas=10d|decision=recursive(unbounded)×720；meas=20d|decision=recursive(unbounded)×720；meas=1d|decision=1d_nonrecursive×360；⑰ RANDOM_NOT_SCHEDULED×6048；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×2430；NO_NEW_CONTENT_TO_PERMUTE×342；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×162；RMARK×3×18；⑱ NOT_APPLICABLE×8964；三时钟账本（形成 / 日历 / 交易）×36

- ⑬（推导段 MDE80 中位）：2010-2014 .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号；2015-2018 MDE80 中位 > .30：首看，只记录

> 表头：主体=INV10 vs HG10 vs LAG1 与 INV_ONLY（H 剖面）｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=op.isin(['INV10','HG10','LAG1_10'])｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q08-a


| item | value |
|---|---|
| objects | 9000 |
| share_FULL_pos | 0.8902 |
| median_FULL_ann_pp | 0.1889 |
| median_G4_ann_pp | 0.1775 |
| median_FULL_sc_ann_pp | 0.11 |
| policy_PORT3_T_FULL_pass | 857 |
| bound_comparisons_rows | 12480 |
| cmp:MECHANISM_PAIR median_D_ann_pp（段行） | -0.02432 |
| cmp:MECHANISM_PAIR share_D_pos（段行） | 0.4234 |


> 表头：主体=库存覆盖 / 满额（saturation）、INV_CAP_LOOP_PAIR vs FIXED_PATH｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=op=='INV10'｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q08-b


| item | value |
|---|---|
| objects | 1560 |
| share_FULL_pos | 0.8853 |
| median_FULL_ann_pp | 0.1894 |
| median_G4_ann_pp | 0.1706 |
| median_FULL_sc_ann_pp | 0.05011 |
| policy_PORT3_T_FULL_pass | 121 |
| bound_comparisons_rows | 6240 |
| cmp:INV_CAP_LOOP median_D_ann_pp（段行） | 0.03018 |
| cmp:INV_CAP_LOOP share_D_pos（段行） | 0.551 |


## E6L-Q09｜平滑与HG组合是否优于各自单独？

- ⑮ Y00=parent|Y10=Q_D10 NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=Q_D10 NATIVE|Y01=K0 HG15|Y11=self；Y00=parent|Y10=Q_D10 NATIVE|Y01=K0 HG5|Y11=self；Y00=parent|Y10=Q_D3 NATIVE|Y01=K0 HG10|Y11=self；⑯ meas=5d|decision=recursive(unbounded)×6840；meas=3d|decision=recursive(unbounded)×3240；meas=10d|decision=recursive(unbounded)×2160；⑰ RANDOM_NOT_SCHEDULED×8568；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×3564；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×108；⑱ NOT_APPLICABLE×12222；三时钟账本（形成 / 日历 / 交易）×18

- ⑬（推导段 MDE80 中位）：2010-2014 MDE80 中位 > .30：首看，只记录；2015-2018 MDE80 中位 > .30：首看，只记录

> 表头：主体=平滑 × 规则四账户（Q0 NATIVE / Qs NATIVE / Q0 HG / Qs HG）｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=meas.str.startswith('Q_') & family=='HG'｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q09-a


| item | value |
|---|---|
| objects | 12240 |
| share_FULL_pos | 0.8427 |
| median_FULL_ann_pp | 0.1655 |
| median_G4_ann_pp | 0.1493 |
| median_FULL_sc_ann_pp | 0.06312 |
| policy_PORT3_T_FULL_pass | 738 |
| bound_comparisons_rows | 194400 |
| cmp:FOUR_ACCOUNT_SMOOTH_RULE median_D_ann_pp（段行） | -0.02 |
| cmp:FOUR_ACCOUNT_SMOOTH_RULE share_D_pos（段行） | 0.4455 |
| cmp:KNOWN_QHG10 median_D_ann_pp（段行） | -0.1232 |
| cmp:KNOWN_QHG10 share_D_pos（段行） | 0.2406 |


## E6L-Q10｜随机记忆能否复制真实HG的增量？

- ⑮ Y00=parent|Y10=Q0 NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=Q_D5 NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=Q_RANK5 NATIVE|Y01=K0 HG10|Y11=self；child−parent；⑯ meas=5d|decision=recursive(unbounded)×108；meas=1d|decision=recursive(unbounded)×54；meas=source|decision=recursive(unbounded)×18；⑰ LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×162；RMARK×3×18；⑱ NOT_APPLICABLE×162；三时钟账本（形成 / 日历 / 交易）×18

- ⑬（推导段 MDE80 中位）：2010-2014 UNDEFINED（无绑定配对比较 / 方法卡）；2015-2018 UNDEFINED（无绑定配对比较 / 方法卡）

> 表头：主体=真实 HG10 − R-MARK 三机制（gross / 费用分列）｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=rmark｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q10-a


| item | value |
|---|---|
| objects | 180 |
| share_FULL_pos | 0.8889 |
| median_FULL_ann_pp | 0.2879 |
| median_G4_ann_pp | 0.2907 |
| median_FULL_sc_ann_pp | 0.2114 |
| policy_PORT3_T_FULL_pass | 71 |
| bound_comparisons_rows | 41040 |
| cmp:REAL_MINUS_COND median_D_ann_pp（段行） | 0.07793 |
| cmp:REAL_MINUS_COND share_D_pos（段行） | 0.6692 |
| cmp:REAL_MINUS_RMARK median_D_ann_pp（段行） | 0.1658 |
| cmp:REAL_MINUS_RMARK share_D_pos（段行） | 0.825 |


> 表头：主体=标记保持率 / 可移动资本 / 熵｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=rmark｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q10-b


| item | value |
|---|---|
| objects | 180 |
| share_FULL_pos | 0.8889 |
| median_FULL_ann_pp | 0.2879 |
| median_G4_ann_pp | 0.2907 |
| median_FULL_sc_ann_pp | 0.2114 |
| policy_PORT3_T_FULL_pass | 71 |
| bound_comparisons_rows | 0 |


## E6L-Q11｜α/b放大后，收益–倾斜权衡是否仍值得？

- ⑮ Y00=parent|Y10=C1 NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=C1 NATIVE|Y01=K0 HG15|Y11=self；Y00=parent|Y10=C1 NATIVE|Y01=K0 HG20|Y11=self；child−parent；⑯ meas=5d|decision=recursive(unbounded)×342；meas=3d|decision=recursive(unbounded)×252；meas=5d|decision=same_day×126；meas=10d|decision=recursive(unbounded)×108；meas=1d|decision=recursive(unbounded)×90；meas=3d|decision=same_day×72；⑰ LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×1062；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×54；NO_NEW_CONTENT_TO_PERMUTE×32；RMARK×3×6；⑱ NOT_APPLICABLE×1100；三时钟账本（形成 / 日历 / 交易）×54

- ⑬（推导段 MDE80 中位）：2010-2014 .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号；2015-2018 MDE80 中位 > .30：首看，只记录

> 表头：主体=剂量面板 α .125 / .25 / .5 × b 5 / 10 / 15 / 20 / 30 与正式紧区间；frontier_dose_tilt｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=op.isin(['HG5','HG10','HG15','HG20','HG30','NATIVE']) & H==5｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q11-a


| item | value |
|---|---|
| objects | 1146 |
| share_FULL_pos | 0.8063 |
| median_FULL_ann_pp | 0.1714 |
| median_G4_ann_pp | 0.129 |
| median_FULL_sc_ann_pp | 0.0586 |
| policy_PORT3_T_FULL_pass | 143 |
| bound_comparisons_rows | 45120 |
| cmp:MECHANISM_PAIR median_D_ann_pp（段行） | 0.02775 |
| cmp:MECHANISM_PAIR share_D_pos（段行） | 0.6122 |


## E6L-Q12｜高波动时强记忆还是弱记忆更好？

- ⑮ Y00=parent|Y10=C1 NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=C1 NATIVE|Y01=K0 HG15|Y11=self；Y00=parent|Y10=C1 NATIVE|Y01=K0 HG5|Y11=self；Y00=parent|Y10=C1 NATIVE|Y01=K0 VOL_HI15|Y11=self；⑯ meas=5d|decision=recursive(unbounded)×7560；meas=3d|decision=recursive(unbounded)×5760；meas=1d|decision=recursive(unbounded)×2520；meas=10d|decision=recursive(unbounded)×2160；meas=20d|decision=recursive(unbounded)×720；meas=source|decision=recursive(unbounded)×360；⑰ RANDOM_NOT_SCHEDULED×13104；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×5454；NO_NEW_CONTENT_TO_PERMUTE×342；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×162；RMARK×3×18；⑱ NOT_APPLICABLE×14736；Vol3 四调度（UNKNOWN→b10；STRICT250 对照）×4320；三时钟账本（形成 / 日历 / 交易）×24

- ⑬（推导段 MDE80 中位）：2010-2014 .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号；2015-2018 .10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号

> 表头：主体=四调度 vs 固定 HG5 / 10 / 15（同测量 / α / H）｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=family=='STATE' | op.isin(['HG5','HG10','HG15'])｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q12-a


| item | value |
|---|---|
| objects | 19080 |
| share_FULL_pos | 0.8758 |
| median_FULL_ann_pp | 0.1803 |
| median_G4_ann_pp | 0.1622 |
| median_FULL_sc_ann_pp | 0.106 |
| policy_PORT3_T_FULL_pass | 1665 |
| bound_comparisons_rows | 28800 |
| cmp:MECHANISM_PAIR median_D_ann_pp（段行） | -0.01136 |
| cmp:MECHANISM_PAIR share_D_pos（段行） | 0.4398 |


> 表头：主体=H_noise / H_change 切片（形成状态 gross；state_clock_ledger）｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=family=='STATE'｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q12-b


| item | value |
|---|---|
| objects | 4320 |
| share_FULL_pos | 0.9056 |
| median_FULL_ann_pp | 0.1929 |
| median_G4_ann_pp | 0.1741 |
| median_FULL_sc_ann_pp | 0.1284 |
| policy_PORT3_T_FULL_pass | 492 |
| bound_comparisons_rows | 0 |


## E6L-Q13｜状态读法能否跨时钟闭合？

- ⑮ Y00=parent|Y10=C1 NATIVE|Y01=K0 VOL_HI15|Y11=self；Y00=parent|Y10=C1 NATIVE|Y01=K0 VOL_HI5|Y11=self；Y00=parent|Y10=C1 NATIVE|Y01=K0 VOL_MEAN15|Y11=self；Y00=parent|Y10=C1 NATIVE|Y01=K0 VOL_MEAN5|Y11=self；⑯ meas=5d|decision=recursive(unbounded)×1458；meas=1d|decision=recursive(unbounded)×1446；meas=3d|decision=recursive(unbounded)×1440；meas=5d|decision=same_day×18；meas=1d|decision=confirmed_decay_L5×6；meas=1d|decision=1d_nonrecursive×6；⑰ RANDOM_NOT_SCHEDULED×3024；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×1350；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×18；⑱ Vol3 四调度（UNKNOWN→b10；STRICT250 对照）×4320；三时钟账本（形成 / 日历 / 交易）×72

- ⑬（推导段 MDE80 中位）：2010-2014 MDE80 中位 ≤ .10：.10 级配对差可 80% 分辨；2015-2018 UNDEFINED（无绑定配对比较 / 方法卡）

> 表头：主体=三时钟、UNKNOWN、状态贡献加回 FULL、对称分解、STRICT250 对照｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=family=='STATE' | primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q13-a


| item | value |
|---|---|
| objects | 4392 |
| share_FULL_pos | 0.9046 |
| median_FULL_ann_pp | 0.193 |
| median_G4_ann_pp | 0.174 |
| median_FULL_sc_ann_pp | 0.1282 |
| policy_PORT3_T_FULL_pass | 509 |
| bound_comparisons_rows | 384 |
| cmp:STRICT250_VS_MAIN median_D_ann_pp（段行） | 0 |
| cmp:STRICT250_VS_MAIN share_D_pos（段行） | 0.1224 |


> 表头：主体=两压力窗口（2015-06-15 / 2024-09-24 起 40 交易日）与连续边界｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=primary72｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q13-b


| item | value |
|---|---|
| objects | 72 |
| share_FULL_pos | 0.8472 |
| median_FULL_ann_pp | 0.2324 |
| median_G4_ann_pp | 0.1555 |
| median_FULL_sc_ann_pp | 0.1077 |
| policy_PORT3_T_FULL_pass | 17 |
| bound_comparisons_rows | 0 |


## E6L-Q14｜并集核在同资本下能否保留有价值的改善？

- ⑮ Y00=parent|Y10=Q_DEW5 NATIVE|Y01=K0 HG5|Y11=self；Y00=parent|Y10=Q_DMED5 NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=Q_DMED5 NATIVE|Y01=K0 HG15|Y11=self；child−parent；⑯ meas=5d|decision=recursive(unbounded)×2760；meas=3d|decision=recursive(unbounded)×2160；meas=1d|decision=recursive(unbounded)×1080；meas=5d|decision=same_day×840；meas=10d|decision=recursive(unbounded)×720；meas=3d|decision=same_day×480；⑰ RANDOM_NOT_SCHEDULED×7560；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×3186；NO_NEW_CONTENT_TO_PERMUTE×554；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5+RMARK×3×54；RMARK×3×6；⑱ NOT_APPLICABLE×9736；Vol3 四调度（UNKNOWN→b10；STRICT250 对照）×1600；三时钟账本（形成 / 日历 / 交易）×24

- ⑬（推导段 MDE80 中位）：2010-2014 UNDEFINED（无绑定配对比较 / 方法卡）；2015-2018 UNDEFINED（无绑定配对比较 / 方法卡）

> 表头：主体=Munion FULL vs FULL_sc（FIXED_PATH）+ INV_LOOP 诊断 + CAP 同单位｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=mother.str.startswith('M_union')｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q14-a


| item | value |
|---|---|
| objects | 11320 |
| share_FULL_pos | 0.9492 |
| median_FULL_ann_pp | 0.1818 |
| median_G4_ann_pp | 0.1826 |
| median_FULL_sc_ann_pp | -0.02091 |
| policy_PORT3_T_FULL_pass | 1027 |
| bound_comparisons_rows | 135840 |
| cmp:MATCH_CAP_FIXED_PATH median_D_ann_pp（段行） | 0.08128 |
| cmp:MATCH_CAP_FIXED_PATH share_D_pos（段行） | 0.6271 |


## E6L-Q15｜S/M/C1的差异真由名义窗口解释吗？

- ⑮ Y00=parent|Y10=C1 NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=M NATIVE|Y01=K0 HG10|Y11=self；Y00=parent|Y10=S NATIVE|Y01=K0 HG10|Y11=self；child−parent；⑯ meas=20d|decision=same_day×720；meas=20d|decision=recursive(unbounded)×720；meas=3d|decision=same_day×360；meas=3d|decision=recursive(unbounded)×360；⑰ RANDOM_NOT_SCHEDULED×1512；LEGACY_POLICY_RANDOM+CONTENT_COND_ISK_P5×648；⑱ NOT_APPLICABLE×2160

- ⑬（推导段 MDE80 中位）：2010-2014 MDE80 中位 > .30：首看，只记录；2015-2018 MDE80 中位 > .30：首看，只记录

> 表头：主体=S / M / C1 × NATIVE / HG10 同 α / H；rank ACF 与门重叠｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=meas.isin(['S','M','C1']) & op.isin(['NATIVE','HG10'])｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q15-a


| item | value |
|---|---|
| objects | 2160 |
| share_FULL_pos | 0.9699 |
| median_FULL_ann_pp | 0.2463 |
| median_G4_ann_pp | 0.2287 |
| median_FULL_sc_ann_pp | 0.2011 |
| policy_PORT3_T_FULL_pass | 362 |
| bound_comparisons_rows | 112320 |
| cmp:SAME_OPERATOR_C1 median_D_ann_pp（段行） | -0.008424 |
| cmp:SAME_OPERATOR_C1 share_D_pos（段行） | 0.4864 |
| cmp:SMN_PAIR median_D_ann_pp（段行） | -0.02705 |
| cmp:SMN_PAIR share_D_pos（段行） | 0.4253 |


## E6L-Q16｜本轮方法是否减少题目、账户与结论错位？

- ⑮ ALL；⑯ ALL；⑰ ALL；⑱ ALL

- ⑬（推导段 MDE80 中位）：2010-2014 UNDEFINED（无绑定配对比较 / 方法卡）；2015-2018 UNDEFINED（无绑定配对比较 / 方法卡）

> 表头：主体=hypothesis_lineage 完整性与固定输出清单逐项｜算子=见卡｜分母=四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）｜基准=同 H 原父 / 比较右端｜子集=ALL｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=各对象自身 H｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-Q16-a


| item | value |
|---|---|
| objects | 33960 |
| share_FULL_pos | 0.8712 |
| median_FULL_ann_pp | 0.1697 |
| median_G4_ann_pp | 0.15 |
| median_FULL_sc_ann_pp | 0.09556 |
| policy_PORT3_T_FULL_pass | 2831 |
| bound_comparisons_rows | 0 |


## 附：判别读数（执行端写卡片八字段所引）

口径：比较层逐比较先把四段日层闭合读数合成 FULL（n_days 加权）与 G4（四段中位）、gross 与线性费用分列、合成 se = √Σ n²·se_H² / N、t = FULL / se，再按卡的判别维度取分布（cells = 比较数；share_FULL_pos = FULL > 0 的份额；share_4seg_pos = 四段 D 全为正的份额）。费用列 = 子与右端的 −8bp × 换手差（正 = 子少付费）。描述符层读 `results/full/policy_E6l.csv`；事实层读 Stage A 掩码事实（推导 + 后段）与固定表。t 只作描述列，不作门。

### Q01

> 表头：主体=Q0 × NATIVE / HG5 / HG10 / HG15 的正式尺子（按算子 × α；H1…20 合并）｜算子=NATIVE / HG｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=同 H 原父（8bp）｜子集=meas = Q0｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q01-1


| op | a | objects | port3_T_full_pass | FULL_med_ann_pp | G4_med_ann_pp | FULL_sc_med_ann_pp | share_FULL_sc_pos |
|---|---|---|---|---|---|---|---|
| HG10 | 0.125 | 120 | 30 | 0.2158 | 0.1978 | 0.158 | 0.9583 |
| HG10 | 0.25 | 120 | 25 | 0.3487 | 0.3356 | 0.2836 | 0.9667 |
| HG10 | 0.5 | 120 | 6 | 0.6501 | 0.789 | 0.1747 | 0.8167 |
| HG15 | 0.125 | 120 | 20 | 0.2275 | 0.2142 | 0.1935 | 0.9667 |
| HG15 | 0.25 | 120 | 24 | 0.3693 | 0.3355 | 0.2581 | 0.95 |
| HG15 | 0.5 | 120 | 4 | 0.6923 | 0.833 | 0.2105 | 0.8333 |
| HG5 | 0.125 | 120 | 23 | 0.1734 | 0.1459 | 0.1521 | 0.9833 |
| HG5 | 0.25 | 120 | 23 | 0.2996 | 0.2835 | 0.2456 | 0.8917 |
| HG5 | 0.5 | 120 | 4 | 0.6536 | 0.8116 | 0.1303 | 0.8 |
| NATIVE | 0.125 | 120 | 9 | 0.09504 | 0.09672 | 0.08883 | 0.825 |
| NATIVE | 0.25 | 120 | 22 | 0.2247 | 0.2084 | 0.1991 | 0.775 |
| NATIVE | 0.5 | 120 | 10 | 0.4845 | 0.4273 | 0.05814 | 0.65 |


> 表头：主体=W09：Q0|A4b_CVRv5|a0.5|H5|HG10 的四段 D、组合层 PORT3_T 段均紧区间与判定（D / FULL 为 ann_pp；port_size 为 pct_pt）｜算子=HG10｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=同 H 原父（8bp）｜子集=单对象｜单位=ann_pp / pct_pt（见 item）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q01-2


| item | value |
|---|---|
| FULL | 1.109 |
| G4 | 1.281 |
| FULL_sc | 1.021 |
| D_2010-2014 | 0.1504 |
| D_2015-2018 | 1.731 |
| D_2019-2023 | 1.659 |
| D_2024-2026 | 0.9029 |
| port_size_lo_T_2010-2014 | -4.018 |
| port_size_lo_T_2015-2018 | -5.176 |
| port_size_lo_T_2019-2023 | -2.806 |
| port_size_lo_T_2024-2026 | -5.676 |
| port_size_hi_T_2010-2014 | -4.018 |
| port_size_hi_T_2015-2018 | -5.175 |
| port_size_hi_T_2019-2023 | -2.804 |
| port_size_hi_T_2024-2026 | -5.676 |
| years_pos | 13 |
| size_PROPOSED_PORT3_T | FAIL |
| policy_PROPOSED_PORT3_T_FULL | 不通过（size(PROPOSED_PORT3_T)） |


### Q02

> 表头：主体=规则在同一测量上的效应：X op − X NATIVE（全部 α / H；按 op）｜算子=SAME_MEAS_NATIVE｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=新测量 × 规则族｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q02-1


| l_op | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DECAY2_10 | 1440 | 0.09017 | 0.03232 | 0.1616 | 0.8396 | 0.09972 | 0.08361 | 0.001791 | 1.534 | 0.3493 | 0.001389 | 0.3576 |
| DECAY5_10 | 1440 | 0.09106 | 0.02742 | 0.1718 | 0.8229 | 0.1042 | 0.08374 | 0.001818 | 1.531 | 0.3688 | 0.002778 | 0.3604 |
| HG10 | 5760 | 0.09746 | 0.03209 | 0.1677 | 0.8599 | 0.1034 | 0.08876 | 0.001889 | 1.528 | 0.3665 | 0.003819 | 0.371 |
| HG15 | 4320 | 0.1194 | 0.03409 | 0.197 | 0.8475 | 0.1211 | 0.1087 | 0.002853 | 1.538 | 0.3451 | 0.002083 | 0.3773 |
| HG20 | 1080 | 0.1186 | 0.04052 | 0.1882 | 0.8565 | 0.1262 | 0.1069 | 0.003493 | 1.303 | 0.2361 | 0 | 0.3296 |
| HG30 | 1080 | 0.1262 | 0.03429 | 0.2313 | 0.8296 | 0.117 | 0.101 | 0.004792 | 1.071 | 0.2306 | 0.001852 | 0.3778 |
| HG5 | 4320 | 0.04556 | 0.01221 | 0.08777 | 0.8171 | 0.04656 | 0.04135 | 0.0009921 | 1.088 | 0.1977 | 0.003009 | 0.2398 |
| INV10 | 1440 | 0.07394 | -0.002259 | 0.1964 | 0.7479 | 0.06173 | 0.05613 | 0.003856 | 0.9452 | 0.259 | 0.02986 | 0.2125 |
| LAG1_10 | 1440 | 0.08173 | 0.01643 | 0.1517 | 0.8264 | 0.08916 | 0.07533 | 0.001545 | 1.527 | 0.3535 | 0.0006944 | 0.3639 |
| VOL_HI15 | 1080 | 0.07704 | 0.02759 | 0.1344 | 0.8481 | 0.07588 | 0.07198 | 0.00141 | 1.41 | 0.2296 | 0.0009259 | 0.2935 |
| VOL_HI5 | 1080 | 0.0925 | 0.02445 | 0.1488 | 0.8296 | 0.09298 | 0.08685 | 0.002211 | 1.369 | 0.2648 | 0.001852 | 0.3824 |
| VOL_MEAN15 | 1080 | 0.07681 | 0.02274 | 0.1527 | 0.8167 | 0.0839 | 0.07138 | 0.001506 | 1.448 | 0.3111 | 0.00463 | 0.35 |
| VOL_MEAN5 | 1080 | 0.09388 | 0.0286 | 0.1617 | 0.8204 | 0.09397 | 0.09066 | 0.002112 | 1.435 | 0.3028 | 0.005556 | 0.3398 |


> 表头：主体=信息 × 规则交互 Y11 − Y10 − Y01 + Y00（按 α）｜算子=FOUR_ACCOUNT_INFO_RULE｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q02-2


| l_alpha | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a0.125 | 8880 | 0.0103 | -0.03724 | 0.05983 | 0.552 | 0.01356 | 0.009298 | 0.000222 | 0.1671 | 0.06824 | 0.02466 | 0.1226 |
| a0.25 | 8880 | 0.01969 | -0.02531 | 0.07325 | 0.6055 | 0.02175 | 0.01827 | 0.0001418 | 0.2776 | 0.03446 | 0.009347 | 0.09223 |
| a0.5 | 8880 | 0.03874 | -0.02473 | 0.1372 | 0.649 | 0.04437 | 0.03453 | -4.458e-05 | 0.4439 | 0.1024 | 0.01002 | 0.09369 |


> 表头：主体=新测量 × 规则 − 旧 K × 同规则（全部 α / H；按 op）｜算子=RULE_ONLY｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q02-3


| l_op | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DECAY2_10 | 1440 | 0.148 | 0.07262 | 0.2702 | 0.9021 | 0.1356 | 0.1399 | 0.00363 | 1.699 | 0.4118 | 0.0006944 | 0.3375 |
| DECAY5_10 | 1440 | 0.1434 | 0.06836 | 0.267 | 0.8979 | 0.1311 | 0.1349 | 0.00367 | 1.628 | 0.3979 | 0.0006944 | 0.3778 |
| HG10 | 5760 | 0.1198 | 0.05061 | 0.2527 | 0.8562 | 0.1127 | 0.116 | 0.004708 | 1.332 | 0.3017 | 0.004167 | 0.2898 |
| HG15 | 4320 | 0.1225 | 0.05038 | 0.2221 | 0.8597 | 0.1143 | 0.1158 | 0.004958 | 1.271 | 0.2551 | 0.002546 | 0.144 |
| HG20 | 1080 | 0.09026 | 0.02964 | 0.2172 | 0.8398 | 0.09189 | 0.08279 | 0.003534 | 1.037 | 0.2546 | 0.001852 | 0.2657 |
| HG30 | 1080 | 0.07251 | -0.007628 | 0.2458 | 0.7185 | 0.07491 | 0.06029 | 0.003819 | 0.8375 | 0.2139 | 0.01852 | 0.2509 |
| HG5 | 4320 | 0.1125 | 0.04154 | 0.2094 | 0.8225 | 0.101 | 0.1084 | 0.004368 | 1.171 | 0.2646 | 0.005556 | 0.2606 |
| INV10 | 1440 | 0.1299 | 0.06081 | 0.2488 | 0.8806 | 0.1236 | 0.1248 | 0.004332 | 1.561 | 0.3493 | 0.0006944 | 0.3243 |
| LAG1_10 | 1440 | 0.1347 | 0.06103 | 0.238 | 0.8896 | 0.1294 | 0.1288 | 0.003627 | 1.588 | 0.3861 | 0.002083 | 0.3576 |
| VOL_HI15 | 1080 | 0.1884 | 0.1101 | 0.3112 | 0.925 | 0.1741 | 0.1792 | 0.003322 | 2.491 | 0.6102 | 0 | 0.5176 |
| VOL_HI5 | 1080 | 0.1121 | 0.03942 | 0.2206 | 0.8565 | 0.1024 | 0.1026 | 0.003299 | 1.365 | 0.2981 | 0.001852 | 0.3093 |
| VOL_MEAN15 | 1080 | 0.1208 | 0.05696 | 0.259 | 0.8935 | 0.1274 | 0.1124 | 0.003161 | 1.6 | 0.388 | 0 | 0.3852 |
| VOL_MEAN5 | 1080 | 0.1231 | 0.05299 | 0.2445 | 0.8787 | 0.1055 | 0.1104 | 0.003384 | 1.428 | 0.3472 | 0 | 0.3685 |


> 表头：主体=费用敏感：同一对象 FULL 在 6 / 8 / 12bp 与 gross（对象中位）｜算子=按族｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=同 H 原父（同费率）｜子集=HG / MEMORY / STATE / OLD_RULE｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=H1…20｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q02-4


| family | objects | FULL_8bp_med_ann_pp | FULL_6bp_med_ann_pp | FULL_12bp_med_ann_pp | FULL_gross_med_ann_pp |
|---|---|---|---|---|---|
| HG | 16560 | 0.1855 | 0.1854 | 0.184 | 0.1794 |
| MEMORY | 5760 | 0.1998 | 0.2004 | 0.2007 | 0.1962 |
| OLD_RULE | 1560 | 0.06971 | 0.06933 | 0.07064 | 0.06246 |
| STATE | 4320 | 0.1929 | 0.1925 | 0.1945 | 0.1867 |


### Q03 / Q15（名单事实）

> 表头：主体=均值核配对（D5 − QMEAN5 / D5 − DMED5 / QMEAN5 − DMED5）｜算子=MEAN_KERNEL_PAIR｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q03-1


| l_meas | r_meas | l_op | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q_D5 | Q_DMED5 | HG10 | 360 | 0.04248 | -0.00474 | 0.1162 | 0.7139 | 0.04437 | 0.04124 | 0.0003918 | 0.7441 | 0.1639 | 0 | 0.2917 |
| Q_D5 | Q_DMED5 | HG15 | 360 | 0.02193 | -0.01609 | 0.07642 | 0.6722 | 0.03075 | 0.02198 | 0.0005082 | 0.4831 | 0.1194 | 0 | 0.1 |
| Q_D5 | Q_DMED5 | HG5 | 360 | 0.03561 | -0.02634 | 0.1158 | 0.6417 | 0.03924 | 0.03153 | 0.0004218 | 0.5775 | 0.2028 | 0.02222 | 0.2306 |
| Q_D5 | Q_DMED5 | NATIVE | 360 | 0.02827 | -0.01973 | 0.09561 | 0.6444 | 0.02749 | 0.02413 | 0.0003694 | 0.4176 | 0.1056 | 0 | 0.1278 |
| Q_D5 | Q_QMEAN5 | HG10 | 360 | -0.04297 | -0.1507 | 0.04783 | 0.4028 | -0.05893 | -0.04187 | 0.0005196 | -0.46 | 0.01111 | 0.06944 | 0.1194 |
| Q_D5 | Q_QMEAN5 | HG15 | 360 | -0.04584 | -0.1299 | 0.03467 | 0.3806 | -0.02453 | -0.0418 | 0.0007014 | -0.4649 | 0.002778 | 0.04444 | 0.05833 |
| Q_D5 | Q_QMEAN5 | HG5 | 360 | -0.03565 | -0.1061 | 0.02195 | 0.425 | -0.01943 | -0.03676 | 0.0006334 | -0.2705 | 0 | 0.06389 | 0.06944 |
| Q_D5 | Q_QMEAN5 | NATIVE | 360 | -0.009186 | -0.07099 | 0.04274 | 0.425 | -0.01292 | -0.01264 | 0.0004673 | -0.1017 | 0.005556 | 0.002778 | 0.09444 |
| Q_QMEAN5 | Q_DMED5 | HG10 | 360 | 0.08379 | 0.04932 | 0.2436 | 0.8694 | 0.09795 | 0.07699 | -3.873e-05 | 1.194 | 0.1306 | 0 | 0.35 |
| Q_QMEAN5 | Q_DMED5 | HG15 | 360 | 0.08119 | 0.02957 | 0.1387 | 0.8611 | 0.07645 | 0.07389 | -9.618e-05 | 1.03 | 0.06944 | 0 | 0.2583 |
| Q_QMEAN5 | Q_DMED5 | HG5 | 360 | 0.07085 | 0.03427 | 0.1613 | 0.8778 | 0.08243 | 0.06639 | 2.891e-05 | 1.086 | 0.06667 | 0 | 0.2778 |
| Q_QMEAN5 | Q_DMED5 | NATIVE | 360 | 0.03779 | 0.007181 | 0.07922 | 0.8111 | 0.03611 | 0.03459 | -5.872e-05 | 0.555 | 0.01667 | 0 | 0.1306 |


> 表头：主体=X − 同算子 Q0（D5 / QMEAN5 / DMED5）｜算子=SAME_OPERATOR_Q0｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H / 算子｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q03-2


| l_meas | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q_D5 | 5040 | -0.1634 | -0.3161 | -0.08243 | 0.05437 | -0.1542 | -0.1517 | -0.002949 | -1.6 | 0 | 0.2885 | 0.001984 |
| Q_DMED5 | 1440 | -0.183 | -0.452 | -0.1038 | 0.02222 | -0.1747 | -0.1729 | -0.002337 | -2.125 | 0 | 0.5542 | 0 |
| Q_QMEAN5 | 1440 | -0.1151 | -0.3059 | -0.0382 | 0.1264 | -0.1106 | -0.1065 | -0.001455 | -1.685 | 0 | 0.4007 | 0.0006944 |


> 表头：主体=X − 同算子 Q0（全部测量）｜算子=SAME_OPERATOR_Q0｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H / 算子｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q03-3


| l_meas | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | 5040 | -0.09732 | -0.3347 | -0.02475 | 0.1748 | -0.09171 | -0.09252 | -0.00455 | -1.204 | 0.003373 | 0.2264 | 0.01587 |
| M | 720 | 0.04929 | -0.07841 | 0.142 | 0.6681 | 0.04562 | 0.04369 | -0.00194 | 0.6487 | 0.1667 | 0.04722 | 0.2181 |
| Q_D10 | 1440 | -0.1572 | -0.3212 | -0.08716 | 0.03264 | -0.1486 | -0.1469 | -0.003915 | -1.563 | 0 | 0.316 | 0.001389 |
| Q_D3 | 1440 | -0.1627 | -0.298 | -0.1007 | 0.01111 | -0.1539 | -0.1482 | -0.002929 | -1.886 | 0 | 0.4444 | 0.0006944 |
| Q_D5 | 5040 | -0.1634 | -0.3161 | -0.08243 | 0.05437 | -0.1542 | -0.1517 | -0.002949 | -1.6 | 0 | 0.2885 | 0.001984 |
| Q_DEW3 | 1440 | -0.1288 | -0.2552 | -0.06317 | 0.03333 | -0.1239 | -0.1187 | -0.003406 | -1.593 | 0 | 0.2569 | 0.0006944 |
| Q_DEW5 | 1440 | -0.1524 | -0.2754 | -0.08017 | 0.02847 | -0.1432 | -0.1446 | -0.003731 | -1.624 | 0 | 0.2889 | 0.002083 |
| Q_DMED5 | 1440 | -0.183 | -0.452 | -0.1038 | 0.02222 | -0.1747 | -0.1729 | -0.002337 | -2.125 | 0 | 0.5542 | 0 |
| Q_QMEAN5 | 1440 | -0.1151 | -0.3059 | -0.0382 | 0.1264 | -0.1106 | -0.1065 | -0.001455 | -1.685 | 0 | 0.4007 | 0.0006944 |
| Q_RANK10 | 1440 | -0.06968 | -0.1888 | -0.01342 | 0.1938 | -0.07117 | -0.0665 | -0.000596 | -0.9795 | 0.002083 | 0.1021 | 0.02431 |
| Q_RANK3 | 1440 | -0.09961 | -0.2917 | -0.03844 | 0.1069 | -0.09674 | -0.093 | -0.0007191 | -1.6 | 0 | 0.3806 | 0.001389 |
| Q_RANK5 | 2880 | -0.08489 | -0.2329 | -0.02336 | 0.1552 | -0.09338 | -0.07615 | -0.0006759 | -1.167 | 0.0006944 | 0.2847 | 0.00625 |
| Q_RANKOBS5 | 720 | -0.1644 | -0.3494 | -0.09795 | 0.03333 | -0.1685 | -0.1599 | -0.00166 | -2.363 | 0 | 0.6556 | 0 |
| Q_RANKSCORE5 | 720 | -0.1202 | -0.2242 | -0.06631 | 0.1083 | -0.1186 | -0.1096 | -0.001729 | -1.84 | 0 | 0.4292 | 0.01806 |
| S | 720 | 0.008935 | -0.02668 | 0.05904 | 0.5653 | 0.01341 | 0.0085 | 0.0008604 | 0.2439 | 0.07778 | 0.02222 | 0.1708 |


> 表头：主体=X − KERNEL_DOSE（同均值 / RMS 的 Q0 增量控制；432 支持格）｜算子=KERNEL_DOSE｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=432 支持格｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=1 / 5 / 20｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q03-4


| l_meas | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q_D10 | 36 | -0.147 | -0.1871 | -0.09854 | 0.05556 | -0.128 | -0.1162 | -0.015 | -1.104 | 0 | 0.08333 | 0 |
| Q_D3 | 36 | -0.1603 | -0.2257 | -0.1251 | 0 | -0.1595 | -0.139 | -0.008354 | -1.627 | 0 | 0.3333 | 0 |
| Q_D5 | 36 | -0.1696 | -0.2198 | -0.1495 | 0 | -0.1943 | -0.1525 | -0.01039 | -1.546 | 0 | 0.1944 | 0 |
| Q_DEW3 | 36 | -0.1253 | -0.1803 | -0.07192 | 0.02778 | -0.1507 | -0.08731 | -0.01076 | -1.238 | 0 | 0.05556 | 0 |
| Q_DEW5 | 36 | -0.1484 | -0.1981 | -0.08134 | 0 | -0.1432 | -0.1125 | -0.01301 | -1.354 | 0 | 0.1389 | 0 |
| Q_DMED5 | 36 | -0.1754 | -0.3297 | -0.1352 | 0 | -0.1698 | -0.1565 | -0.009363 | -1.862 | 0 | 0.3611 | 0 |
| Q_QMEAN5 | 36 | -0.1477 | -0.2917 | -0.07336 | 0 | -0.1031 | -0.1105 | -0.007472 | -1.569 | 0 | 0.3333 | 0 |
| Q_RANK10 | 36 | -0.03319 | -0.07964 | -0.0005933 | 0.25 | -0.02683 | -0.02553 | -0.005037 | -0.4099 | 0 | 0 | 0.05556 |
| Q_RANK3 | 36 | -0.07179 | -0.2414 | -0.04645 | 0.05556 | -0.09685 | -0.07028 | -0.002566 | -1.263 | 0 | 0.2222 | 0 |
| Q_RANK5 | 36 | -0.07677 | -0.1972 | -0.03755 | 0.05556 | -0.09393 | -0.0736 | -0.002809 | -1.116 | 0 | 0.1667 | 0 |
| Q_RANKOBS5 | 36 | -0.06488 | -0.1732 | -0.04225 | 0.08333 | -0.07914 | -0.05799 | -0.001718 | -1.175 | 0 | 0.1111 | 0 |
| Q_RANKSCORE5 | 36 | -0.07845 | -0.1176 | -0.04844 | 0.1667 | -0.08219 | -0.06518 | -0.002523 | -1.451 | 0 | 0.2222 | 0.02778 |


> 表头：主体=门层名单事实（α .25 × NATIVE / HG10；四段 × 六形态中位）｜算子=NATIVE / HG10｜分母=目标 × 段｜基准=同算子 Q0（overlap_in_q0_same_op）/ 同测量原生（same_ticker_overlap_with_native）｜子集=mask_facts（推导 + 后段）｜单位=份额 / 名数每日｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=与 H 无关｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-FACTS-1


| meas | op | overlap_in_q0_same_op | same_ticker_overlap_with_native | list_retention | gate_retention | self_edits_per_day | edit_persistence_5d_reversal_share |
|---|---|---|---|---|---|---|---|
| C1 | HG10 | 0.4734 | 0.4909 | 0.6114 | 0.643 | 55.92 | 0.9295 |
| C1 | NATIVE | 0.3085 |  | 0.5739 |  | 60.86 | 0.9408 |
| M | HG10 | 0.4568 | 0.6302 | 0.6099 | 0.641 | 55.6 | 0.9164 |
| M | NATIVE | 0.352 |  | 0.5692 |  | 61.36 | 0.9278 |
| Q0 | HG10 |  | 0.6004 | 0.631 | 0.6635 | 52.74 | 0.9082 |
| Q0 | NATIVE |  |  | 0.5878 |  | 58.92 | 0.9256 |
| Q_D10 | HG10 | 0.4937 | 0.653 | 0.6147 | 0.637 | 55.77 | 0.9009 |
| Q_D10 | NATIVE | 0.4103 |  | 0.5751 |  | 61.42 | 0.9275 |
| Q_D3 | HG10 | 0.5217 | 0.6335 | 0.6069 | 0.6307 | 56 | 0.9137 |
| Q_D3 | NATIVE | 0.4527 |  | 0.5702 |  | 61.8 | 0.9352 |
| Q_D5 | HG10 | 0.4971 | 0.6388 | 0.6104 | 0.6348 | 55.76 | 0.9034 |
| Q_D5 | NATIVE | 0.4261 |  | 0.5728 |  | 61.51 | 0.9319 |
| Q_DEW3 | HG10 | 0.6015 | 0.6352 | 0.618 | 0.6437 | 54.83 | 0.9009 |
| Q_DEW3 | NATIVE | 0.5346 |  | 0.5766 |  | 60.73 | 0.9271 |
| Q_DEW5 | HG10 | 0.557 | 0.6475 | 0.6165 | 0.6405 | 55.23 | 0.9049 |
| Q_DEW5 | NATIVE | 0.4866 |  | 0.5755 |  | 61.05 | 0.9283 |
| Q_DMED5 | HG10 | 0.5053 | 0.6248 | 0.6058 | 0.6313 | 55.86 | 0.9117 |
| Q_DMED5 | NATIVE | 0.4387 |  | 0.5687 |  | 61.77 | 0.9373 |
| Q_QMEAN5 | HG10 | 0.4618 | 0.5931 | 0.6042 | 0.625 | 55.89 | 0.9192 |
| Q_QMEAN5 | NATIVE | 0.3737 |  | 0.5627 |  | 61.74 | 0.9366 |
| Q_RANK10 | HG10 | 0.5662 | 0.6309 | 0.6156 | 0.6398 | 55.4 | 0.9077 |
| Q_RANK10 | NATIVE | 0.4819 |  | 0.5787 |  | 61.15 | 0.9295 |
| Q_RANK3 | HG10 | 0.5886 | 0.6331 | 0.6102 | 0.631 | 55.72 | 0.9136 |
| Q_RANK3 | NATIVE | 0.5256 |  | 0.5708 |  | 61.65 | 0.9297 |
| Q_RANK5 | HG10 | 0.5678 | 0.631 | 0.6126 | 0.6363 | 55.48 | 0.9103 |
| Q_RANK5 | NATIVE | 0.5 |  | 0.5747 |  | 61.3 | 0.9319 |
| Q_RANKOBS5 | HG10 | 0.5185 | 0.597 | 0.6061 | 0.6258 | 56.36 | 0.9186 |
| Q_RANKOBS5 | NATIVE | 0.4185 |  | 0.5688 |  | 62.18 | 0.9371 |
| Q_RANKSCORE5 | HG10 | 0.5137 | 0.4112 | 0.601 | 0.6257 | 56.06 | 0.9251 |
| Q_RANKSCORE5 | NATIVE | 0.3827 |  | 0.5617 |  | 62.02 | 0.9433 |
| S | HG10 | 0.7851 | 0.6105 | 0.6313 | 0.6638 | 52.67 | 0.8992 |
| S | NATIVE | 0.7332 |  | 0.5885 |  | 58.83 | 0.9286 |


> 表头：主体=pool0 单元 d 的零值与 ε 主导（d < 1e−4）份额（Stage 0 A4-3）｜算子=—｜分母=pool0 单元｜基准=—｜子集=pool0 单元｜单位=份额｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=与 H 无关｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q03-5


| segment | valid_share | zero_d_share | eps_dominant_share |
|---|---|---|---|
| 2010-2014 | 1 | 0.02705 | 0.02705 |
| 2015-2018 | 1 | 0.03212 | 0.03213 |
| 2019-2023 | 1 | 0.03114 | 0.03125 |
| 2024-2026 | 1 | 0.02976 | 0.02981 |


### Q04 / Q05

> 表头：主体=MA − EW（D3 − DEW3、D5 − DEW5；按测量 × 算子）｜算子=MA_VS_EW｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q04-1


| l_meas | l_op | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q_D3 | HG10 | 360 | -0.0384 | -0.06414 | -0.01227 | 0.2028 | -0.04135 | -0.03494 | -0.0008499 | -0.9019 | 0 | 0.05278 | 0.01389 |
| Q_D3 | HG15 | 360 | -0.04314 | -0.07177 | -0.02437 | 0.1028 | -0.04079 | -0.04111 | -0.0007022 | -1.039 | 0 | 0.04722 | 0 |
| Q_D3 | HG5 | 360 | -0.0385 | -0.06503 | -0.01724 | 0.1083 | -0.03789 | -0.03502 | -0.0007319 | -0.8825 | 0 | 0.05 | 0 |
| Q_D3 | NATIVE | 360 | -0.01998 | -0.06394 | 0.007888 | 0.325 | -0.02327 | -0.0181 | -0.0007096 | -0.5525 | 0.01111 | 0.07222 | 0.01111 |
| Q_D5 | HG10 | 360 | -0.01806 | -0.04757 | 0.00822 | 0.325 | -0.01524 | -0.01492 | -0.0005526 | -0.3563 | 0.002778 | 0.002778 | 0.03056 |
| Q_D5 | HG15 | 360 | 0.01215 | -0.01623 | 0.04287 | 0.6194 | 0.01166 | 0.01422 | -0.0005783 | 0.2339 | 0.03333 | 0 | 0.08611 |
| Q_D5 | HG5 | 360 | -0.02393 | -0.05592 | 0.0008692 | 0.2611 | -0.02057 | -0.02118 | -0.0005249 | -0.6284 | 0 | 0.03889 | 0 |
| Q_D5 | NATIVE | 360 | 0.0109 | -0.07143 | 0.03255 | 0.575 | 0.005612 | 0.0112 | -0.0004673 | 0.3155 | 0.01667 | 0.2111 | 0.04722 |


> 表头：主体=窗口配对（D10 − D5、D5 − D3、RANK10 − RANK5、RANK5 − RANK3）｜算子=WINDOW_PAIR｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H / 算子｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q04-2


| l_meas | r_meas | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q_D10 | Q_D5 | 1440 | -0.0189 | -0.05773 | 0.01675 | 0.3521 | -0.02559 | -0.0188 | 0.0002442 | -0.3347 | 0.007639 | 0.02847 | 0.02292 |
| Q_D5 | Q_D3 | 1440 | 0.003956 | -0.04631 | 0.04047 | 0.5257 | 0.002072 | 0.002864 | 0.000113 | 0.08723 | 0.0375 | 0.01528 | 0.06944 |
| Q_RANK10 | Q_RANK5 | 1440 | 0.01772 | -0.01844 | 0.06606 | 0.6347 | 0.02226 | 0.01718 | 0.0004092 | 0.3133 | 0.02569 | 0.001389 | 0.1104 |
| Q_RANK5 | Q_RANK3 | 1440 | 0.01474 | -0.02305 | 0.06579 | 0.6111 | 0.01369 | 0.01432 | 4.656e-05 | 0.2595 | 0.075 | 0.02153 | 0.1125 |


> 表头：主体=秩桥（RANK5 − RANKOBS5、RANK5 − RANKSCORE5）｜算子=RANK_BRIDGE_PAIR｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q05-1


| l_meas | r_meas | l_op | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q_RANK5 | Q_RANKOBS5 | HG10 | 360 | 0.07784 | 0.03997 | 0.1132 | 0.8917 | 0.07889 | 0.07621 | 0.001088 | 1.191 | 0.1639 | 0 | 0.1889 |
| Q_RANK5 | Q_RANKOBS5 | NATIVE | 360 | 0.08184 | 0.03842 | 0.126 | 0.975 | 0.07135 | 0.07995 | 0.001039 | 1.235 | 0.1417 | 0 | 0.2806 |
| Q_RANK5 | Q_RANKSCORE5 | HG10 | 360 | 0.01485 | -0.08002 | 0.06427 | 0.5889 | 0.01029 | 0.0128 | 0.001549 | 0.2882 | 0.06111 | 0 | 0.125 |
| Q_RANK5 | Q_RANKSCORE5 | NATIVE | 360 | 0.025 | -0.01527 | 0.06656 | 0.6667 | 0.01841 | 0.02278 | 0.001476 | 0.6038 | 0.03889 | 0 | 0.1167 |


> 表头：主体=支持桥与 Q0 遮罩（按分解项；12 个平滑测量合并）｜算子=支持分解｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=432 支持格｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=1 / 5 / 20｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q05-2


| kind | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MASKQ0_CONTENT | 432 | -0.1742 | -0.2879 | -0.1051 | 0.04167 | -0.1599 | -0.1297 | -0.009912 | -1.806 | 0 | 0.4097 | 0.00463 |
| MASKQ0_SUPPORT_ONLY | 432 | -0.001009 | -0.003511 | 0.0004463 | 0.2731 | -0.0001615 | -0.0009844 | -2.769e-06 | -0.6558 | 0 | 0.04861 | 0.01157 |
| SUPPORT_BRIDGE_CHILD_SUPPORT | 432 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  | 0 | 0 | 0 |
| SUPPORT_BRIDGE_CONTENT | 432 | -0.1723 | -0.2874 | -0.1051 | 0.03935 | -0.1586 | -0.129 | -0.009872 | -1.753 | 0 | 0.3981 | 0.002315 |
| SUPPORT_BRIDGE_PARENT_SUPPORT | 432 | -0.0007025 | -0.003678 | 0.002977 | 0.4282 | -6.331e-05 | -0.0006677 | -7.379e-06 | -0.2084 | 0.006944 | 0.09259 | 0.08102 |


> 表头：主体=测量覆盖：新测量坏度有限份额 / 共同支持份额 / 回旧 K 份额（四段 × 六形态中位）｜算子=—｜分母=pool0 单元｜基准=—｜子集=measure_facts｜单位=份额｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=与 H 无关｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q05-3


| meas | meas_kf_finite_share | meas_cs_share | fallback_k0_valid_meas_missing |
|---|---|---|---|
| Q_D10 | 0.9994 | 0.9994 | 0.0005749 |
| Q_D3 | 0.9999 | 0.9999 | 8.991e-05 |
| Q_D5 | 0.9998 | 0.9998 | 0.0002017 |
| Q_DEW3 | 0.9999 | 0.9999 | 8.991e-05 |
| Q_DEW5 | 0.9998 | 0.9998 | 0.0002017 |
| Q_DMED5 | 0.9998 | 0.9998 | 0.0002017 |
| Q_QMEAN5 | 0.9998 | 0.9998 | 0.0002017 |
| Q_RANK10 | 0.994 | 0.994 | 0.005953 |
| Q_RANK3 | 0.9988 | 0.9988 | 0.00115 |
| Q_RANK5 | 0.9977 | 0.9977 | 0.002325 |
| Q_RANKOBS5 | 0.7463 | 0.7463 | 0.2537 |
| Q_RANKSCORE5 | 0.9977 | 0.9977 | 0.002325 |


### Q06 / Q07 / Q08

> 表头：主体=LAG1_10 − HG10（按测量）｜算子=MECHANISM_PAIR｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q06-1


| l_meas | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | 360 | 0.006283 | -0.01493 | 0.02129 | 0.6194 | 0.004126 | 0.006649 | -0.0001048 | 0.2237 | 0.03333 | 0.01389 | 0.07222 |
| K0 | 120 | -0.0005034 | -0.01868 | 0.007895 | 0.4917 | -0.002988 | 0.00138 | -0.000161 | -0.02638 | 0 | 0 | 0.05 |
| Q0 | 360 | -0.02007 | -0.04483 | 0.01052 | 0.3167 | -0.01953 | -0.01755 | -0.0003415 | -0.6106 | 0.03889 | 0.1194 | 0.03889 |
| Q_D5 | 360 | -0.01198 | -0.03189 | 0.005499 | 0.3583 | -0.01569 | -0.009218 | -0.0002916 | -0.3637 | 0 | 0.03889 | 0.01389 |
| Q_RANK5 | 360 | -0.01835 | -0.03692 | -0.004829 | 0.1917 | -0.01895 | -0.01693 | -0.0002761 | -0.6346 | 0 | 0.05278 | 0.02222 |


> 表头：主体=记忆算子 − 同测量 NATIVE（按算子）｜算子=SAME_MEAS_NATIVE｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H / 测量｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q06-2


| l_op | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DECAY2_10 | 1440 | 0.09017 | 0.03232 | 0.1616 | 0.8396 | 0.09972 | 0.08361 | 0.001791 | 1.534 | 0.3493 | 0.001389 | 0.3576 |
| DECAY5_10 | 1440 | 0.09106 | 0.02742 | 0.1718 | 0.8229 | 0.1042 | 0.08374 | 0.001818 | 1.531 | 0.3688 | 0.002778 | 0.3604 |
| HG10 | 5760 | 0.09746 | 0.03209 | 0.1677 | 0.8599 | 0.1034 | 0.08876 | 0.001889 | 1.528 | 0.3665 | 0.003819 | 0.371 |
| INV10 | 1440 | 0.07394 | -0.002259 | 0.1964 | 0.7479 | 0.06173 | 0.05613 | 0.003856 | 0.9452 | 0.259 | 0.02986 | 0.2125 |
| LAG1_10 | 1440 | 0.08173 | 0.01643 | 0.1517 | 0.8264 | 0.08916 | 0.07533 | 0.001545 | 1.527 | 0.3535 | 0.0006944 | 0.3639 |


> 表头：主体=纯 bonus 依靠份额 / 连续依靠日数 / 重确认年龄（目标 × 段中位）｜算子=记忆算子｜分母=目标 × 段｜基准=—｜子集=mask_facts（推导 + 后段）｜单位=份额 / 交易日｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=与 H 无关｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q06-3


| op | bonus_reliant_share | reliant_run_p90 | reliant_run_max | confirm_age_p90 | confirm_age_max | gate_retention | list_retention |
|---|---|---|---|---|---|---|---|
| DECAY2_10 | 0.04739 | 1 | 2 | 0 | 2 | 0.6982 | 0.6491 |
| DECAY5_10 | 0.0485 | 1 | 3 | 0 | 3 | 0.6999 | 0.6498 |
| HG10 | 0.05024 | 1 | 4 | 0 | 4 | 0.7023 | 0.6556 |
| HG15 | 0.07393 | 2 | 6 | 0 | 6 | 0.7368 | 0.6852 |
| HG20 | 0.09108 | 2 | 7 | 0 | 7 | 0.7312 | 0.6746 |
| HG30 | 0.1278 | 2 | 10 | 1 | 10 | 0.7656 | 0.7078 |
| HG5 | 0.02557 | 1 | 3 | 0 | 3 | 0.67 | 0.6324 |
| LAG1_10 | 0.04934 | 1 | 1 | 0 | 1 | 0.6864 | 0.6402 |
| VOL_HI15 | 0.03876 | 1 | 4 | 0 | 4 | 0.6841 | 0.6362 |
| VOL_HI5 | 0.05665 | 2 | 5 | 0 | 5 | 0.7013 | 0.6512 |
| VOL_MEAN15 | 0.03993 | 1 | 4 | 0 | 4 | 0.6867 | 0.638 |
| VOL_MEAN5 | 0.0562 | 1 | 5 | 0 | 5 | 0.7011 | 0.6515 |


> 表头：主体=DECAY2 / DECAY5 − HG10、DECAY2 − DECAY5｜算子=MECHANISM_PAIR｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H / 测量｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q07-1


| l_op | r_op | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DECAY2_10 | DECAY5_10 | 1560 | 0.0003547 | -0.009084 | 0.00913 | 0.5141 | 0.001655 | 0.0007902 | -2.909e-05 | 0.03854 | 0.04551 | 0.025 | 0.09423 |
| DECAY2_10 | HG10 | 1560 | -0.00226 | -0.01466 | 0.008902 | 0.4449 | -0.0008858 | -0.001615 | -5.504e-05 | -0.1357 | 0.03269 | 0.02436 | 0.08013 |
| DECAY5_10 | HG10 | 1560 | -0.0004571 | -0.009593 | 0.006201 | 0.4814 | -0.0003244 | -0.0001557 | -2.426e-05 | -0.04065 | 0.0109 | 0.05705 | 0.04487 |


> 表头：主体=INV10 − HG10 / LAG1_10（按 H）｜算子=MECHANISM_PAIR｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / 测量｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q08-1


| r_op | H | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HG10 | 1 | 78 | 0 | -0.05998 | 0.1429 | 0.4487 | 0 | 0 | 0.007654 | 0.1851 | 0.1154 | 0.05128 | 0.1154 |
| HG10 | 2 | 78 | 0.05491 | -0.04373 | 0.1597 | 0.6538 | 0.0468 | 0.02689 | 0.04157 | 0.5874 | 0.141 | 0.01282 | 0.2179 |
| HG10 | 3 | 78 | 0.01765 | -0.06716 | 0.1269 | 0.6154 | 0.02123 | -0.01011 | 0.02312 | 0.2599 | 0.1282 | 0.02564 | 0.07692 |
| HG10 | 4 | 78 | 0.007209 | -0.07585 | 0.1592 | 0.5256 | 0.0211 | -0.004858 | 0.01535 | 0.1196 | 0.1154 | 0 | 0.141 |
| HG10 | 5 | 78 | 0.004447 | -0.06367 | 0.1119 | 0.5385 | -0.005246 | -0.001471 | 0.008409 | 0.06618 | 0.0641 | 0.0641 | 0.1538 |
| HG10 | 6 | 78 | -0.007561 | -0.0807 | 0.085 | 0.4744 | -0.03723 | -0.009477 | 0.005902 | -0.1169 | 0.01282 | 0.07692 | 0.08974 |
| HG10 | 7 | 78 | -0.01547 | -0.07032 | 0.06736 | 0.4487 | -0.04084 | 0.001836 | 0.004297 | -0.1796 | 0 | 0.07692 | 0.03846 |
| HG10 | 8 | 78 | -0.00855 | -0.06238 | 0.06236 | 0.4615 | -0.03553 | -0.003046 | 0.002679 | -0.1704 | 0 | 0.03846 | 0.02564 |
| HG10 | 9 | 78 | -0.01316 | -0.06111 | 0.06654 | 0.4487 | -0.03553 | -0.01465 | 0.002136 | -0.2003 | 0.01282 | 0.05128 | 0.03846 |
| HG10 | 10 | 78 | -0.008626 | -0.05556 | 0.06852 | 0.4487 | -0.02531 | -0.007813 | 0.001435 | -0.09715 | 0.01282 | 0.07692 | 0.03846 |
| HG10 | 11 | 78 | -0.008703 | -0.05712 | 0.06137 | 0.4487 | -0.02683 | -0.005375 | 0.0008719 | -0.2063 | 0.02564 | 0.07692 | 0.01282 |
| HG10 | 12 | 78 | -0.01497 | -0.06685 | 0.0473 | 0.4359 | -0.04343 | -0.01526 | 0.0006984 | -0.3291 | 0.01282 | 0.08974 | 0.02564 |
| HG10 | 13 | 78 | -0.01639 | -0.06987 | 0.02634 | 0.4103 | -0.03685 | -0.01618 | 0.0003816 | -0.3249 | 0.01282 | 0.1282 | 0.01282 |
| HG10 | 14 | 78 | -0.01971 | -0.06583 | 0.02205 | 0.3718 | -0.0361 | -0.01678 | 0.0001181 | -0.3748 | 0.01282 | 0.1282 | 0 |
| HG10 | 15 | 78 | -0.01461 | -0.06445 | 0.01776 | 0.3462 | -0.03233 | -0.01253 | 7.435e-05 | -0.2925 | 0.01282 | 0.1538 | 0.01282 |
| HG10 | 16 | 78 | -0.02331 | -0.069 | 0.01146 | 0.3205 | -0.03874 | -0.02367 | 4.024e-05 | -0.5066 | 0.01282 | 0.1667 | 0.01282 |
| HG10 | 17 | 78 | -0.02537 | -0.068 | 0.005421 | 0.2949 | -0.04365 | -0.0197 | 0.0001279 | -0.4517 | 0.01282 | 0.141 | 0.01282 |
| HG10 | 18 | 78 | -0.02826 | -0.06958 | -0.001663 | 0.2436 | -0.04257 | -0.0233 | 8.942e-05 | -0.5572 | 0 | 0.141 | 0.01282 |
| HG10 | 19 | 78 | -0.02925 | -0.06421 | 0.0008439 | 0.2564 | -0.05137 | -0.02092 | 0.0002289 | -0.5216 | 0.01282 | 0.08974 | 0.01282 |
| HG10 | 20 | 78 | -0.03535 | -0.0684 | 0.00333 | 0.2692 | -0.05181 | -0.01948 | 0.0002498 | -0.5756 | 0 | 0.0641 | 0.01282 |
| LAG1_10 | 1 | 78 | 0.04271 | -0.03904 | 0.2339 | 0.6667 | 0.07123 | -0.01007 | 0.06054 | 0.6123 | 0.2436 | 0.02564 | 0.2308 |
| LAG1_10 | 2 | 78 | 0.1197 | 0.0103 | 0.1873 | 0.7564 | 0.1034 | 0.03783 | 0.06539 | 1.113 | 0.2051 | 0.02564 | 0.2179 |
| LAG1_10 | 3 | 78 | 0.03742 | -0.05326 | 0.151 | 0.6282 | 0.03652 | 0.00537 | 0.02927 | 0.4679 | 0.1026 | 0 | 0.1154 |
| LAG1_10 | 4 | 78 | 0.02154 | -0.0555 | 0.1565 | 0.5513 | 0.01651 | 0.0012 | 0.01906 | 0.3463 | 0.141 | 0.01282 | 0.141 |
| LAG1_10 | 5 | 78 | 0.02053 | -0.0727 | 0.1229 | 0.5513 | 0.01178 | 0.02144 | 0.01077 | 0.3441 | 0.1154 | 0.02564 | 0.141 |
| LAG1_10 | 6 | 78 | 0.005403 | -0.08853 | 0.08427 | 0.5128 | -0.02639 | -0.002154 | 0.006827 | 0.07146 | 0.07692 | 0.08974 | 0.0641 |
| LAG1_10 | 7 | 78 | 0.0001073 | -0.06763 | 0.06559 | 0.5 | -0.02757 | 0.005225 | 0.004831 | 0.003405 | 0.07692 | 0.07692 | 0.0641 |
| LAG1_10 | 8 | 78 | -0.001257 | -0.06347 | 0.06512 | 0.5 | -0.03907 | 0.0002348 | 0.003255 | -0.01557 | 0.03846 | 0.07692 | 0.02564 |
| LAG1_10 | 9 | 78 | 0.004948 | -0.07036 | 0.06659 | 0.5256 | -0.02673 | 0.003247 | 0.002615 | 0.05833 | 0.03846 | 0.0641 | 0.02564 |
| LAG1_10 | 10 | 78 | 0.01364 | -0.05212 | 0.07201 | 0.5385 | -0.02217 | 0.01325 | 0.001857 | 0.2362 | 0.05128 | 0.05128 | 0.0641 |
| LAG1_10 | 11 | 78 | 0.01052 | -0.05156 | 0.06053 | 0.5385 | -0.0106 | 0.011 | 0.001229 | 0.187 | 0.01282 | 0.08974 | 0.05128 |
| LAG1_10 | 12 | 78 | 0.001976 | -0.06368 | 0.04922 | 0.5128 | -0.02066 | 0.007259 | 0.0009793 | 0.027 | 0.01282 | 0.1154 | 0.0641 |
| LAG1_10 | 13 | 78 | 0.0005595 | -0.06468 | 0.04275 | 0.5 | -0.02699 | 0.000861 | 0.0006448 | 0.01419 | 0.01282 | 0.1282 | 0.02564 |
| LAG1_10 | 14 | 78 | -0.01113 | -0.06461 | 0.02959 | 0.4615 | -0.03261 | -0.01139 | 0.0005094 | -0.2149 | 0.02564 | 0.1667 | 0.02564 |
| LAG1_10 | 15 | 78 | -0.01801 | -0.0564 | 0.0253 | 0.4231 | -0.03546 | -0.0005406 | 0.0002458 | -0.2801 | 0.01282 | 0.1282 | 0.03846 |
| LAG1_10 | 16 | 78 | -0.01856 | -0.06115 | 0.02692 | 0.3846 | -0.03513 | -0.008332 | 0.0001705 | -0.3668 | 0 | 0.1538 | 0.02564 |
| LAG1_10 | 17 | 78 | -0.01289 | -0.05616 | 0.02564 | 0.3718 | -0.03763 | -0.01114 | 0.000191 | -0.2943 | 0.01282 | 0.1282 | 0.02564 |
| LAG1_10 | 18 | 78 | -0.01581 | -0.06556 | 0.01286 | 0.3205 | -0.04734 | -0.01332 | 9.542e-05 | -0.3539 | 0.01282 | 0.1154 | 0.03846 |
| LAG1_10 | 19 | 78 | -0.02189 | -0.05785 | 0.00647 | 0.3462 | -0.0449 | -0.0152 | 0.0002058 | -0.3969 | 0.01282 | 0.0641 | 0.03846 |
| LAG1_10 | 20 | 78 | -0.02523 | -0.06063 | 0.003367 | 0.2949 | -0.04574 | -0.019 | 0.0002457 | -0.5515 | 0.01282 | 0.0641 | 0.01282 |


> 表头：主体=INV10 的 FULL 与同资本 FULL_sc（按 H）｜算子=INV10｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=同 H 原父（8bp）｜子集=op = INV10｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q08-2


| H | objects | port3_T_full_pass | FULL_med_ann_pp | G4_med_ann_pp | FULL_sc_med_ann_pp | share_FULL_sc_pos |
|---|---|---|---|---|---|---|
| 1 | 78 | 55 | 1.089 | 1.085 | 0.9042 | 1 |
| 2 | 78 | 21 | 0.4631 | 0.37 | 0.2123 | 0.8846 |
| 3 | 78 | 9 | 0.3083 | 0.1819 | 0.03982 | 0.5256 |
| 4 | 78 | 0 | 0.2457 | 0.1887 | 0.03152 | 0.5128 |
| 5 | 78 | 5 | 0.2306 | 0.1692 | 0.00292 | 0.5 |
| 6 | 78 | 0 | 0.1761 | 0.1712 | -0.002263 | 0.5 |
| 7 | 78 | 0 | 0.2046 | 0.1797 | 0.003766 | 0.5128 |
| 8 | 78 | 0 | 0.2118 | 0.1963 | 0.03406 | 0.5513 |
| 9 | 78 | 0 | 0.2285 | 0.2195 | 0.06799 | 0.6026 |
| 10 | 78 | 17 | 0.2218 | 0.2001 | 0.04353 | 0.6026 |
| 11 | 78 | 0 | 0.2162 | 0.1974 | 0.06711 | 0.5897 |
| 12 | 78 | 0 | 0.1876 | 0.1794 | 0.0524 | 0.5769 |
| 13 | 78 | 0 | 0.1655 | 0.1419 | 0.03069 | 0.5641 |
| 14 | 78 | 0 | 0.1406 | 0.1258 | 0.02096 | 0.5385 |
| 15 | 78 | 0 | 0.1435 | 0.1259 | 0.02663 | 0.5385 |
| 16 | 78 | 0 | 0.1377 | 0.1276 | 0.007117 | 0.5 |
| 17 | 78 | 0 | 0.1288 | 0.126 | 0.008091 | 0.5256 |
| 18 | 78 | 0 | 0.107 | 0.09863 | 0.01117 | 0.5128 |
| 19 | 78 | 0 | 0.1119 | 0.08719 | 0.02133 | 0.5385 |
| 20 | 78 | 14 | 0.1081 | 0.08319 | 0.02129 | 0.5385 |


> 表头：主体=INV 闭环同资本（诊断，不进正式 FULL_sc）｜算子=INV_CAP_LOOP｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q08-3


| H | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 78 | 0.9042 | 0.6759 | 1.237 | 1 | 0.8915 | 0 | 0 | 4.31 | 0.9872 | 0 | 0.8462 |
| 2 | 78 | 0.2123 | 0.08364 | 0.4533 | 0.8846 | 0.1993 | 0 | 0 | 1.293 | 0.2949 | 0 | 0.2436 |
| 3 | 78 | 0.03982 | -0.1221 | 0.3016 | 0.5256 | 0.01572 | 0 | 0 | 0.2306 | 0.2179 | 0 | 0.141 |
| 4 | 78 | 0.03152 | -0.1584 | 0.2444 | 0.5128 | -0.02481 | 0 | 0 | 0.2697 | 0.1923 | 0.1154 | 0.1026 |
| 5 | 78 | 0.00292 | -0.138 | 0.1866 | 0.5 | -0.008355 | 0 | 0 | 0.01644 | 0.1795 | 0.05128 | 0.1026 |
| 6 | 78 | -0.002263 | -0.127 | 0.148 | 0.5 | -0.01417 | 0 | 0 | -0.01936 | 0.1282 | 0.03846 | 0.07692 |
| 7 | 78 | 0.003766 | -0.1155 | 0.1706 | 0.5128 | -0.02185 | 0 | 0 | 0.01857 | 0.1667 | 0.02564 | 0.1282 |
| 8 | 78 | 0.03406 | -0.1212 | 0.1967 | 0.5513 | 0.001778 | 0 | 0 | 0.2542 | 0.2179 | 0.02564 | 0.2051 |
| 9 | 78 | 0.06799 | -0.1137 | 0.2133 | 0.6026 | 0.03838 | 0 | 0 | 0.449 | 0.2692 | 0.03846 | 0.2051 |
| 10 | 78 | 0.04353 | -0.09947 | 0.2057 | 0.6026 | 0.03886 | 0 | 0 | 0.5405 | 0.2821 | 0.01282 | 0.2308 |
| 11 | 78 | 0.06711 | -0.09545 | 0.2009 | 0.5897 | 0.04213 | 0 | 0 | 0.8217 | 0.2821 | 0.03846 | 0.2436 |
| 12 | 78 | 0.0524 | -0.09002 | 0.1784 | 0.5769 | 0.03392 | 0 | 0 | 0.6528 | 0.2564 | 0.0641 | 0.2308 |
| 13 | 78 | 0.03069 | -0.1084 | 0.1489 | 0.5641 | 0.007331 | 0 | 0 | 0.399 | 0.1923 | 0.1538 | 0.2436 |
| 14 | 78 | 0.02096 | -0.1103 | 0.1331 | 0.5385 | 0.01213 | 0 | 0 | 0.1912 | 0.1667 | 0.141 | 0.2308 |
| 15 | 78 | 0.02663 | -0.1185 | 0.125 | 0.5385 | -0.001382 | 0 | 0 | 0.2592 | 0.1667 | 0.1538 | 0.2564 |
| 16 | 78 | 0.007117 | -0.1169 | 0.1258 | 0.5 | -0.01038 | 0 | 0 | 0.05332 | 0.1795 | 0.1667 | 0.2564 |
| 17 | 78 | 0.008091 | -0.1112 | 0.1191 | 0.5256 | 0.01002 | 0 | 0 | 0.08207 | 0.1795 | 0.1667 | 0.2692 |
| 18 | 78 | 0.01117 | -0.1199 | 0.1275 | 0.5128 | 0.01094 | 0 | 0 | 0.09972 | 0.2051 | 0.2179 | 0.2949 |
| 19 | 78 | 0.02133 | -0.1216 | 0.1332 | 0.5385 | 0.02951 | 0 | 0 | 0.2684 | 0.2179 | 0.1923 | 0.3077 |
| 20 | 78 | 0.02129 | -0.1242 | 0.133 | 0.5385 | 0.02275 | 0 | 0 | 0.3152 | 0.2179 | 0.2308 | 0.3205 |


> 表头：主体=库存标记覆盖 / 满额日份额 / 到期重叠（按 H）｜算子=INV10｜分母=目标 × 段｜基准=—｜子集=inventory_saturation｜单位=份额｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q08-4


| H | mark_coverage | saturated_day_share | pending_expiry_overlap |
|---|---|---|---|
| 1 | 0.2021 | 0 | 0.6523 |
| 2 | 0.2408 | 0 | 0.5235 |
| 3 | 0.2617 | 0 | 0.4239 |
| 4 | 0.2767 | 0 | 0.3423 |
| 5 | 0.286 | 0 | 0.2674 |
| 6 | 0.2934 | 0 | 0.2371 |
| 7 | 0.2991 | 0 | 0.212 |
| 8 | 0.3044 | 0 | 0.1916 |
| 9 | 0.3094 | 0 | 0.1725 |
| 10 | 0.314 | 0 | 0.1569 |
| 11 | 0.318 | 0 | 0.1444 |
| 12 | 0.3217 | 0 | 0.1311 |
| 13 | 0.3252 | 0 | 0.1189 |
| 14 | 0.3282 | 0 | 0.1076 |
| 15 | 0.3313 | 0 | 0.0988 |
| 16 | 0.3344 | 0 | 0.09095 |
| 17 | 0.3372 | 0 | 0.08463 |
| 18 | 0.34 | 0 | 0.07952 |
| 19 | 0.3429 | 0 | 0.07686 |
| 20 | 0.3456 | 0 | 0.07492 |


### Q09 / Q10

> 表头：主体=平滑 × 规则交互（按 op）｜算子=FOUR_ACCOUNT_SMOOTH_RULE｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H / 测量｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q09-1


| l_op | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DECAY2_10 | 720 | -0.02775 | -0.07866 | 0.01867 | 0.3722 | -0.0221 | -0.02287 | -0.0003241 | -0.3533 | 0 | 0.04444 | 0.01667 |
| DECAY5_10 | 720 | -0.03607 | -0.08774 | 0.01969 | 0.3319 | -0.02359 | -0.03244 | -0.0002573 | -0.4604 | 0 | 0.04861 | 0.002778 |
| HG10 | 4320 | -0.02415 | -0.08227 | 0.02557 | 0.365 | -0.02241 | -0.02161 | -0.0003001 | -0.3137 | 0.004861 | 0.04514 | 0.01782 |
| HG15 | 3600 | -0.01456 | -0.07789 | 0.03574 | 0.4203 | -0.01167 | -0.01244 | -0.0002827 | -0.1808 | 0.004167 | 0.02556 | 0.02361 |
| HG20 | 360 | -0.02479 | -0.07166 | 0.01422 | 0.3222 | -0.01991 | -0.02361 | -0.00102 | -0.293 | 0.005556 | 0.008333 | 0.02222 |
| HG30 | 360 | -0.0147 | -0.1443 | 0.07201 | 0.4556 | -0.003444 | -0.008614 | -0.0006593 | -0.1251 | 0.01389 | 0.08889 | 0.05833 |
| HG5 | 3600 | -0.0274 | -0.0801 | 0.00853 | 0.3033 | -0.02225 | -0.02604 | -0.0001279 | -0.4684 | 0.003611 | 0.04444 | 0.01556 |
| INV10 | 720 | 0.01558 | -0.03029 | 0.06592 | 0.6153 | 0.01243 | 0.01602 | -0.0001769 | 0.2401 | 0.04306 | 0.01389 | 0.08333 |
| LAG1_10 | 720 | -0.02199 | -0.0845 | 0.0279 | 0.4097 | -0.01196 | -0.01987 | -0.000168 | -0.3121 | 0.009722 | 0.04861 | 0.01806 |
| VOL_HI15 | 360 | -0.02864 | -0.0756 | 0.01694 | 0.3306 | -0.00277 | -0.02819 | -0.0001757 | -0.3804 | 0 | 0.008333 | 0.01667 |
| VOL_HI5 | 360 | -0.02714 | -0.0682 | 0.00466 | 0.2861 | -0.02082 | -0.02389 | -0.0003335 | -0.3808 | 0 | 0.03333 | 0.005556 |
| VOL_MEAN15 | 360 | -0.03351 | -0.09302 | 0.01916 | 0.3306 | -0.02014 | -0.03173 | -0.0001937 | -0.3936 | 0 | 0.08889 | 0.002778 |
| VOL_MEAN5 | 360 | -0.009026 | -0.06187 | 0.03467 | 0.4583 | 0.002998 | -0.007619 | -0.0004327 | -0.1123 | 0 | 0.02222 | 0 |


> 表头：主体=X HG10 − Q0 HG10（按测量）｜算子=KNOWN_QHG10｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q09-2


| l_meas | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | 360 | -0.1157 | -0.4047 | -0.03821 | 0.1611 | -0.1186 | -0.1137 | -0.004547 | -1.593 | 0 | 0.3306 | 0.01389 |
| M | 360 | 0.02246 | -0.1431 | 0.1121 | 0.5333 | 0.01704 | 0.006402 | -0.002206 | 0.2365 | 0.1639 | 0.08611 | 0.2167 |
| Q_D10 | 360 | -0.1546 | -0.3218 | -0.07894 | 0.05 | -0.1439 | -0.142 | -0.004791 | -1.491 | 0 | 0.2639 | 0 |
| Q_D3 | 360 | -0.1703 | -0.2907 | -0.1183 | 0.008333 | -0.1728 | -0.1606 | -0.003141 | -1.921 | 0 | 0.475 | 0 |
| Q_D5 | 360 | -0.1715 | -0.3043 | -0.09022 | 0.09167 | -0.1644 | -0.161 | -0.002763 | -1.626 | 0 | 0.3083 | 0 |
| Q_DEW3 | 360 | -0.1457 | -0.2702 | -0.06772 | 0.03611 | -0.132 | -0.1301 | -0.004319 | -1.649 | 0 | 0.2806 | 0 |
| Q_DEW5 | 360 | -0.1536 | -0.2635 | -0.07617 | 0.06111 | -0.1315 | -0.1442 | -0.004452 | -1.544 | 0 | 0.25 | 0 |
| Q_DMED5 | 360 | -0.2121 | -0.5206 | -0.1036 | 0.03056 | -0.1959 | -0.1968 | -0.002552 | -2.467 | 0 | 0.6194 | 0 |
| Q_QMEAN5 | 360 | -0.1369 | -0.3213 | -0.01311 | 0.2056 | -0.126 | -0.1277 | -0.001568 | -1.827 | 0 | 0.4556 | 0 |
| Q_RANK10 | 360 | -0.09158 | -0.226 | -0.0152 | 0.1806 | -0.08807 | -0.08814 | -0.0007711 | -1.304 | 0.002778 | 0.1611 | 0.01944 |
| Q_RANK3 | 360 | -0.1171 | -0.3188 | -0.03395 | 0.1389 | -0.1101 | -0.1075 | -0.0007908 | -1.683 | 0 | 0.4194 | 0 |
| Q_RANK5 | 360 | -0.09922 | -0.3149 | -0.02119 | 0.175 | -0.1193 | -0.09265 | -0.0007013 | -1.322 | 0 | 0.3861 | 0.005556 |
| Q_RANKOBS5 | 360 | -0.1847 | -0.3991 | -0.1083 | 0.01667 | -0.1901 | -0.1796 | -0.001888 | -2.421 | 0 | 0.7056 | 0 |
| Q_RANKSCORE5 | 360 | -0.117 | -0.2578 | -0.07128 | 0.06389 | -0.1384 | -0.1096 | -0.001853 | -1.847 | 0 | 0.4444 | 0.005556 |
| S | 360 | 0.003957 | -0.03905 | 0.05503 | 0.5222 | 0.005988 | 0.002181 | 0.0009021 | 0.07703 | 0.08056 | 0.01389 | 0.2083 |


> 表头：主体=真实 − 随机路径均值（按机制）｜算子=RANDOM_PATH_MEAN｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=同对象随机路径逐日均值｜子集=随机清单全部行｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q10-1


| kind | r_pre | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| REAL_MINUS_COND | CONTENT_COND_ISK_P5 | 9720 | 0.09346 | 0.02075 | 0.2352 | 0.8241 | 0.08724 | 0 | 0 | 1.122 | 0.2515 | 0.004012 | 0.2081 |
| REAL_MINUS_LEGACY | LEGACY_POLICY_RANDOM | 9720 | 0.209 | 0.09245 | 0.4906 | 0.9429 | 0.2094 | 0 | 0 | 2.091 | 0.5233 | 0.0002058 | 0.4592 |
| REAL_MINUS_RMARK | RMARK_ISK_P5 | 180 | 0.08885 | 0.02653 | 0.3353 | 0.8278 | 0.08007 | 0 | 0 | 1.777 | 0.4778 | 0 | 0.4278 |
| REAL_MINUS_RMARK | RMARK_UNIFORM_IID | 180 | 0.1805 | 0.08091 | 0.5231 | 0.9167 | 0.1694 | 0 | 0 | 3.037 | 0.6944 | 0 | 0.6722 |
| REAL_MINUS_RMARK | RMARK_UNIFORM_P5 | 180 | 0.1798 | 0.0808 | 0.4661 | 0.9111 | 0.1707 | 0 | 0 | 2.987 | 0.6944 | 0 | 0.6667 |


> 表头：主体=真实 HG10 − R-MARK（按机制 × 测量 × H）｜算子=RANDOM_PATH_MEAN｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=同对象 R-MARK 路径逐日均值｜子集=R-MARK 540 行｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=1 / 5 / 20｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q10-2


| r_pre | l_meas | H | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RMARK_ISK_P5 | K0 | 1 | 6 | 0.2963 | 0.2669 | 0.3156 | 1 | 0.288 | 0 | 0 | 2.862 | 1 | 0 | 1 |
| RMARK_ISK_P5 | K0 | 5 | 6 | 0.01624 | -0.006855 | 0.03958 | 0.6667 | 0.04383 | 0 | 0 | 0.2959 | 0 | 0 | 0 |
| RMARK_ISK_P5 | K0 | 20 | 6 | 0.04865 | 0.04334 | 0.04918 | 1 | 0.03685 | 0 | 0 | 1.631 | 0.1667 | 0 | 0 |
| RMARK_ISK_P5 | Q0 | 1 | 18 | 0.451 | 0.3718 | 0.6458 | 1 | 0.5029 | 0 | 0 | 3.959 | 1 | 0 | 1 |
| RMARK_ISK_P5 | Q0 | 5 | 18 | 0.1112 | -0.03745 | 0.1541 | 0.6667 | 0.05528 | 0 | 0 | 1.24 | 0.3889 | 0 | 0.2778 |
| RMARK_ISK_P5 | Q0 | 20 | 18 | 0.03458 | 0.00993 | 0.1158 | 0.8333 | 0.03312 | 0 | 0 | 1.096 | 0.2778 | 0 | 0.1111 |
| RMARK_ISK_P5 | Q_D5 | 1 | 18 | 0.418 | 0.3664 | 0.6198 | 1 | 0.4263 | 0 | 0 | 4.107 | 1 | 0 | 1 |
| RMARK_ISK_P5 | Q_D5 | 5 | 18 | 0.09195 | 0.01096 | 0.134 | 0.7222 | 0.08589 | 0 | 0 | 1.229 | 0.2222 | 0 | 0.1667 |
| RMARK_ISK_P5 | Q_D5 | 20 | 18 | 0.06951 | 0.006213 | 0.08184 | 0.7778 | 0.06419 | 0 | 0 | 1.353 | 0.3889 | 0 | 0.2222 |
| RMARK_ISK_P5 | Q_RANK5 | 1 | 18 | 0.3897 | 0.3255 | 0.5221 | 1 | 0.4056 | 0 | 0 | 3.588 | 1 | 0 | 1 |
| RMARK_ISK_P5 | Q_RANK5 | 5 | 18 | 0.01229 | -0.01095 | 0.04824 | 0.6111 | 0.001049 | 0 | 0 | 0.1652 | 0 | 0 | 0.05556 |
| RMARK_ISK_P5 | Q_RANK5 | 20 | 18 | 0.03379 | 0.005917 | 0.04809 | 0.7778 | 0.03312 | 0 | 0 | 0.9242 | 0.1111 | 0 | 0.1111 |
| RMARK_UNIFORM_IID | K0 | 1 | 6 | 0.4325 | 0.3864 | 0.4684 | 1 | 0.4539 | 0 | 0 | 3.863 | 1 | 0 | 1 |
| RMARK_UNIFORM_IID | K0 | 5 | 6 | 0.1001 | 0.005215 | 0.1262 | 0.6667 | 0.1029 | 0 | 0 | 1.666 | 0.1667 | 0 | 0.1667 |
| RMARK_UNIFORM_IID | K0 | 20 | 6 | 0.09414 | 0.04877 | 0.1002 | 1 | 0.08609 | 0 | 0 | 2.824 | 0.6667 | 0 | 0.6667 |
| RMARK_UNIFORM_IID | Q0 | 1 | 18 | 0.6581 | 0.554 | 0.8937 | 1 | 0.6791 | 0 | 0 | 5.137 | 1 | 0 | 1 |
| RMARK_UNIFORM_IID | Q0 | 5 | 18 | 0.2123 | -0.0006436 | 0.3537 | 0.7222 | 0.2141 | 0 | 0 | 2.722 | 0.6111 | 0 | 0.6667 |
| RMARK_UNIFORM_IID | Q0 | 20 | 18 | 0.08794 | 0.04955 | 0.1856 | 1 | 0.09049 | 0 | 0 | 2.451 | 0.5556 | 0 | 0.7222 |
| RMARK_UNIFORM_IID | Q_D5 | 1 | 18 | 0.6258 | 0.5324 | 0.7241 | 1 | 0.6312 | 0 | 0 | 5.385 | 1 | 0 | 1 |
| RMARK_UNIFORM_IID | Q_D5 | 5 | 18 | 0.166 | 0.03496 | 0.2424 | 0.7778 | 0.1869 | 0 | 0 | 2.395 | 0.6111 | 0 | 0.5556 |
| RMARK_UNIFORM_IID | Q_D5 | 20 | 18 | 0.1147 | 0.02966 | 0.1308 | 0.9444 | 0.1149 | 0 | 0 | 2.376 | 0.6667 | 0 | 0.5 |
| RMARK_UNIFORM_IID | Q_RANK5 | 1 | 18 | 0.5682 | 0.5029 | 0.6737 | 1 | 0.5772 | 0 | 0 | 4.477 | 1 | 0 | 1 |
| RMARK_UNIFORM_IID | Q_RANK5 | 5 | 18 | 0.1095 | 0.04825 | 0.1507 | 0.8333 | 0.1151 | 0 | 0 | 1.445 | 0.2778 | 0 | 0.3333 |
| RMARK_UNIFORM_IID | Q_RANK5 | 20 | 18 | 0.09936 | 0.03618 | 0.1437 | 1 | 0.1124 | 0 | 0 | 2.304 | 0.6111 | 0 | 0.3333 |
| RMARK_UNIFORM_P5 | K0 | 1 | 6 | 0.4075 | 0.3461 | 0.4571 | 1 | 0.4271 | 0 | 0 | 3.627 | 1 | 0 | 1 |
| RMARK_UNIFORM_P5 | K0 | 5 | 6 | 0.09772 | 0.005003 | 0.1246 | 0.6667 | 0.09953 | 0 | 0 | 1.627 | 0.1667 | 0 | 0.1667 |
| RMARK_UNIFORM_P5 | K0 | 20 | 6 | 0.09375 | 0.04774 | 0.1001 | 1 | 0.0871 | 0 | 0 | 2.833 | 0.6667 | 0 | 0.6667 |
| RMARK_UNIFORM_P5 | Q0 | 1 | 18 | 0.6036 | 0.4817 | 0.8103 | 1 | 0.6453 | 0 | 0 | 4.646 | 1 | 0 | 0.9444 |
| RMARK_UNIFORM_P5 | Q0 | 5 | 18 | 0.2102 | -0.001216 | 0.3508 | 0.6667 | 0.2131 | 0 | 0 | 2.691 | 0.6111 | 0 | 0.6667 |
| RMARK_UNIFORM_P5 | Q0 | 20 | 18 | 0.08842 | 0.05008 | 0.1858 | 1 | 0.09207 | 0 | 0 | 2.472 | 0.5556 | 0 | 0.7222 |
| RMARK_UNIFORM_P5 | Q_D5 | 1 | 18 | 0.5766 | 0.4926 | 0.695 | 1 | 0.5849 | 0 | 0 | 4.881 | 1 | 0 | 1 |
| RMARK_UNIFORM_P5 | Q_D5 | 5 | 18 | 0.1658 | 0.03481 | 0.2452 | 0.7778 | 0.191 | 0 | 0 | 2.356 | 0.6111 | 0 | 0.5556 |
| RMARK_UNIFORM_P5 | Q_D5 | 20 | 18 | 0.1144 | 0.02967 | 0.1309 | 0.9444 | 0.1146 | 0 | 0 | 2.362 | 0.6667 | 0 | 0.5 |
| RMARK_UNIFORM_P5 | Q_RANK5 | 1 | 18 | 0.4891 | 0.4562 | 0.6234 | 1 | 0.5167 | 0 | 0 | 4.103 | 1 | 0 | 1 |
| RMARK_UNIFORM_P5 | Q_RANK5 | 5 | 18 | 0.1072 | 0.04557 | 0.1476 | 0.8333 | 0.1153 | 0 | 0 | 1.416 | 0.2778 | 0 | 0.3333 |
| RMARK_UNIFORM_P5 | Q_RANK5 | 20 | 18 | 0.09861 | 0.03627 | 0.1419 | 1 | 0.1103 | 0 | 0 | 2.278 | 0.6111 | 0 | 0.3333 |


### Q11 / Q12 / Q13

> 表头：主体=剂量面板（H5；α × b）｜算子=NATIVE / HG5…HG30｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=同 H 原父（8bp）｜子集=H = 5｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q11-1


| a | op | objects | port3_T_full_pass | FULL_med_ann_pp | G4_med_ann_pp | FULL_sc_med_ann_pp | share_FULL_sc_pos |
|---|---|---|---|---|---|---|---|
| 0 | HG10 | 6 | 0 | 0.0391 | 0.06659 | 0.005317 | 0.5 |
| 0 | HG15 | 6 | 0 | 0.05756 | 0.07112 | -0.002267 | 0.5 |
| 0 | HG20 | 6 | 0 | 0.1361 | 0.187 | 0.03118 | 0.6667 |
| 0 | HG30 | 6 | 0 | 0.1094 | 0.05294 | 0.0402 | 0.5 |
| 0 | HG5 | 6 | 0 | 0.01341 | -0.0003924 | 0.001852 | 0.5 |
| 0.125 | HG10 | 96 | 27 | 0.1736 | 0.1583 | 0.08015 | 0.6875 |
| 0.125 | HG15 | 72 | 12 | 0.1926 | 0.1588 | 0.05783 | 0.6667 |
| 0.125 | HG20 | 18 | 3 | 0.171 | 0.1364 | 0.03907 | 0.6667 |
| 0.125 | HG30 | 18 | 2 | 0.2033 | 0.1799 | 0.09255 | 0.6111 |
| 0.125 | HG5 | 72 | 8 | 0.1178 | 0.1107 | 0.05802 | 0.6111 |
| 0.125 | NATIVE | 96 | 5 | 0.07496 | 0.04671 | 0.05027 | 0.5833 |
| 0.25 | HG10 | 96 | 21 | 0.2568 | 0.2355 | 0.1763 | 0.6354 |
| 0.25 | HG15 | 72 | 10 | 0.2553 | 0.2318 | 0.1297 | 0.5972 |
| 0.25 | HG20 | 18 | 4 | 0.2869 | 0.2424 | 0.1676 | 0.7222 |
| 0.25 | HG30 | 18 | 1 | 0.2302 | 0.2399 | 0.176 | 0.6111 |
| 0.25 | HG5 | 72 | 12 | 0.2035 | 0.1714 | 0.1101 | 0.5694 |
| 0.25 | NATIVE | 96 | 18 | 0.1427 | 0.09447 | 0.0799 | 0.6146 |
| 0.5 | HG10 | 96 | 3 | 0.2804 | 0.2506 | 0.05623 | 0.625 |
| 0.5 | HG15 | 72 | 3 | 0.2713 | 0.139 | 0.002714 | 0.5 |
| 0.5 | HG20 | 18 | 3 | 0.298 | 0.1854 | 0.04594 | 0.7222 |
| 0.5 | HG30 | 18 | 1 | 0.2977 | 0.1744 | -0.02198 | 0.4444 |
| 0.5 | HG5 | 72 | 4 | 0.1841 | 0.1009 | 0.006157 | 0.5 |
| 0.5 | NATIVE | 96 | 6 | 0.1581 | 0.09984 | -0.01022 | 0.5 |


> 表头：主体=剂量 × 倾斜前沿（frontier_dose_tilt；段 × 配方 × 母体）｜算子=α × b｜分母=段 × 母体｜基准=同 H 原父（8bp）｜子集=frontier_dose_tilt｜单位=ann_pp / pct_pt（见列名）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q11-2


| alpha | b | cells | FULL_med_ann_pp | port_size_mid_T_med_pct_pt | port_size_mid_T_min_pct_pt |
|---|---|---|---|---|---|
| 0.125 | 0 | 24 | 0.08609 | -0.22 | -0.7958 |
| 0.125 | 5 | 24 | 0.2094 | -0.3048 | -1.009 |
| 0.125 | 10 | 24 | 0.2961 | -0.3374 | -1.297 |
| 0.125 | 15 | 24 | 0.2741 | -0.3408 | -1.512 |
| 0.125 | 20 | 24 | 0.2558 | -0.3189 | -1.766 |
| 0.125 | 30 | 24 | 0.1861 | -0.4169 | -2.24 |
| 0.25 | 0 | 24 | 0.2845 | -0.4938 | -1.81 |
| 0.25 | 5 | 24 | 0.4146 | -0.5494 | -2.118 |
| 0.25 | 10 | 24 | 0.5228 | -0.6026 | -2.406 |
| 0.25 | 15 | 24 | 0.426 | -0.6232 | -2.725 |
| 0.25 | 20 | 24 | 0.3831 | -0.7129 | -3.072 |
| 0.25 | 30 | 24 | 0.5156 | -1.428 | -4.14 |
| 0.5 | 0 | 24 | 0.4947 | -0.1061 | -2.663 |
| 0.5 | 5 | 24 | 0.787 | -1.545 | -4.876 |
| 0.5 | 10 | 24 | 0.7287 | -1.733 | -5.836 |
| 0.5 | 15 | 24 | 0.7447 | -1.698 | -6.217 |
| 0.5 | 20 | 24 | 0.6834 | -1.52 | -6.26 |
| 0.5 | 30 | 24 | 0.6111 | -1.056 | -6.138 |


> 表头：主体=四调度 − 固定 HG10、调度之间｜算子=MECHANISM_PAIR｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H / 测量｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q12-1


| l_op | r_op | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| VOL_HI15 | HG10 | 1200 | -0.01974 | -0.05181 | 0.006718 | 0.3058 | -0.01507 | -0.01749 | -0.0004383 | -0.4387 | 0 | 0.04917 | 0.02 |
| VOL_HI15 | VOL_HI5 | 1200 | -0.01391 | -0.05893 | 0.01922 | 0.4 | -0.01856 | -0.01149 | -0.0007777 | -0.2364 | 0.0025 | 0.03417 | 0.03083 |
| VOL_HI5 | HG10 | 1200 | -0.0005156 | -0.03058 | 0.02817 | 0.4942 | -0.0006821 | -0.003424 | 0.000428 | -0.01228 | 0.02167 | 0.05083 | 0.05667 |
| VOL_MEAN15 | HG10 | 1200 | -0.01127 | -0.03516 | 0.007039 | 0.3417 | -0.01273 | -0.009801 | -0.0003098 | -0.4084 | 0.008333 | 0.08083 | 0.01083 |
| VOL_MEAN15 | VOL_MEAN5 | 1200 | -0.01238 | -0.0432 | 0.01521 | 0.3625 | -0.01503 | -0.009443 | -0.0005783 | -0.3263 | 0.004167 | 0.06167 | 0.01417 |
| VOL_MEAN5 | HG10 | 1200 | 0.002397 | -0.01886 | 0.02013 | 0.5517 | -0.0005763 | 0.00116 | 0.0002733 | 0.09974 | 0.015 | 0.02583 | 0.075 |


> 表头：主体=形成状态切片的 gross 贡献差（子 − 父，对象中位；H_noise / H_change 为 Q12 事前切片）｜算子=FORMATION 时钟｜分母=形成日 × 状态｜基准=同 H 原父｜子集=state_clock_ledger｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q12-2


|  |
||


> 表头：主体=日历时钟：状态份额 / 贡献 / 状态内均值（对象中位）｜算子=CALENDAR_NET｜分母=日历日 × 状态｜基准=同 H 原父（8bp）｜子集=state_clock_ledger｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q13-1


| state_var | state | rows | share_med | contribution_med_ann_pp | conditional_mean_med_ann_pp |
|---|---|---|---|---|---|
| VOL3_CALENDAR | HIGH | 1200 | 0.3118 | 0.02926 | 0.09814 |
| VOL3_CALENDAR | LOW | 1200 | 0.352 | 0.06848 | 0.1882 |
| VOL3_CALENDAR | MID | 1200 | 0.2987 | 0.03341 | 0.1098 |
| VOL3_CALENDAR | SUM_CHECK | 1200 | 1 | 0.1747 | 0.1747 |
| VOL3_CALENDAR | UNKNOWN | 1200 | 0 | 0 | -0.00199 |


> 表头：主体=跨段 ΔFULL 的对称分解（状态内均值 / 状态频率 / 残差；对象中位）｜算子=对称分解｜分母=共同状态｜基准=前一段｜子集=state_symmetric_decomposition｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q13-2


| old | new | delta_FULL_ann_pp | within_state_ann_pp | state_frequency_ann_pp | residual_ann_pp |
|---|---|---|---|---|---|
| 2010-2014 | 2015-2018 | 0.4581 | 0.449 | 0.0328 | 0.0002786 |
| 2015-2018 | 2019-2023 | -0.2878 | -0.2884 | 0.009837 | 1.388e-17 |
| 2019-2023 | 2024-2026 | -0.2628 | -0.2591 | -0.01321 | 6.939e-18 |
| DERIV | POST | -0.106 | -0.1207 | 0.01984 | 0.0001546 |


> 表头：主体=压力窗口与段首边界窗口（各 40 个交易日；对象中位）｜算子=累计相对 / NAV 回撤｜分母=窗口内交易日｜基准=同 H 原父｜子集=状态时钟对象｜单位=百分比（%）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q13-3


| window_start | rows | cum_rel_net_med_pct | share_cum_rel_pos | nav_dd_child_med_pct | nav_dd_parent_med_pct |
|---|---|---|---|---|---|
| 2015-06-15 | 300 | 0.1426 | 0.65 | 30.5 | 30.17 |
| 2019-01-02 | 300 | -0.01983 | 0.2867 | 0.05499 | 0.09178 |
| 2024-01-02 | 300 | -0.05321 | 0.2933 | 1.496 | 1.48 |
| 2024-09-24 | 300 | -0.314 | 0.1 | 8.224 | 8.156 |


> 表头：主体=连续面板：记忆跨段接续 − 段首重置（按段）｜算子=carry / reset｜分母=各段有效日｜基准=连续原父｜子集=primary72 × 四记忆算子｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=5｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q13-4


| segment | rows | carry_minus_reset_med_ann_pp | carry_minus_reset_nonzero | carry_minus_reset_max_ann_pp | carry_minus_reset_min_ann_pp | boundary40_carry_minus_parent_med_ann_pp |
|---|---|---|---|---|---|---|
| 2010-2014 | 72 | 0 | 0 | 0 | 0 | 0.322 |
| 2015-2018 | 72 | 0 | 8 | 0.002273 | -0.006687 | 0.1886 |
| 2019-2023 | 72 | 0 | 2 | 0.007273 | 0 | -0.1644 |
| 2024-2026 | 72 | 0 | 14 | 0.01144 | -0.004655 | -0.7173 |


### Q14 / Q15

> 表头：主体=M_union 两母体：FULL vs 同资本 FULL_sc（按族）｜算子=按族｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=同 H 原父（8bp）｜子集=mother ∈ M_union｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=H1…20｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q14-1


| mother | family | objects | port3_T_full_pass | FULL_med_ann_pp | G4_med_ann_pp | FULL_sc_med_ann_pp | share_FULL_sc_pos |
|---|---|---|---|---|---|---|---|
| M_union3_v2 | HG | 2760 | 285 | 0.2065 | 0.2048 | -0.01342 | 0.45 |
| M_union3_v2 | MEMORY | 960 | 119 | 0.2318 | 0.2549 | 0.001282 | 0.5052 |
| M_union3_v2 | NATIVE | 240 | 31 | 0.1624 | 0.1802 | 0.0436 | 0.7708 |
| M_union3_v2 | OLD_RULE | 260 | 0 | 0.09566 | 0.09841 | 0.04735 | 0.8115 |
| M_union3_v2 | SMOOTH | 720 | 8 | 0.04902 | 0.04062 | -0.1008 | 0.06111 |
| M_union3_v2 | STATE | 720 | 97 | 0.2103 | 0.1985 | 0.06802 | 0.6333 |
| M_union3_v2_CVRv5 | HG | 2760 | 256 | 0.1932 | 0.1961 | -0.03304 | 0.3822 |
| M_union3_v2_CVRv5 | MEMORY | 960 | 103 | 0.2141 | 0.2457 | -0.01166 | 0.4656 |
| M_union3_v2_CVRv5 | NATIVE | 240 | 35 | 0.162 | 0.183 | 0.0355 | 0.7 |
| M_union3_v2_CVRv5 | OLD_RULE | 260 | 0 | 0.05957 | 0.06055 | 0.01558 | 0.6423 |
| M_union3_v2_CVRv5 | SMOOTH | 720 | 5 | 0.04625 | 0.03286 | -0.1242 | 0.03056 |
| M_union3_v2_CVRv5 | STATE | 720 | 88 | 0.199 | 0.1989 | 0.04038 | 0.6444 |


> 表头：主体=同资本 FIXED_PATH（子 − 同 H 原父；按母体）｜算子=MATCH_CAP_FIXED_PATH｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=同 H 原父（同资本）｜子集=全部｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q14-2


| l_mother | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A4b | 5660 | 0.2371 | 0.1441 | 0.4049 | 0.9532 | 0.2238 | 0 | 0 | 2.258 | 0.6088 | 0 | 0.5323 |
| A4b_CVRv5 | 5660 | 0.2117 | 0.1235 | 0.3446 | 0.914 | 0.207 | 0 | 0 | 2.41 | 0.6348 | 0 | 0.5887 |
| M_mean3_v2 | 5660 | 0.171 | 0.09112 | 0.2663 | 0.8906 | 0.09825 | 0 | 0 | 1.596 | 0.358 | 0 | 0.2108 |
| M_mean3_v2_CVRv5 | 5660 | 0.01877 | -0.1019 | 0.09889 | 0.5599 | -0.02358 | 0 | 0 | 0.2167 | 0.08746 | 0.02138 | 0.115 |
| M_union3_v2 | 5660 | -0.01225 | -0.1118 | 0.08239 | 0.4634 | -0.0001796 | 0 | 0 | -0.147 | 0.1148 | 0.0689 | 0.1482 |
| M_union3_v2_CVRv5 | 5660 | -0.02839 | -0.128 | 0.05174 | 0.4104 | -0.02574 | 0 | 0 | -0.3762 | 0.0629 | 0.1127 | 0.09717 |


> 表头：主体=S − M（按算子）｜算子=SMN_PAIR｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q15-1


| l_op | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HG10 | 360 | 0.009288 | -0.07358 | 0.1106 | 0.5306 | 0.009003 | 0.00602 | 0.003139 | 0.1172 | 0.03889 | 0.1694 | 0.08056 |
| NATIVE | 360 | -0.04523 | -0.09135 | 0.01415 | 0.2806 | -0.0453 | -0.05025 | 0.002975 | -0.6146 | 0.01667 | 0.1278 | 0.04722 |


> 表头：主体=S / M / Q0 − 同算子 C1（按测量）｜算子=SAME_OPERATOR_C1｜分母=四段有效日（FULL = n 加权；G4 = 四段中位）｜基准=比较右端（见 kind / right 列）｜子集=全部 α / H / 算子｜单位=年化百分点（ann_pp）｜日期=2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）｜H=见列｜成本模型=源 8bp（冲击列 A 5 亿 κ .5）｜支持=原生（FALLBACK）｜资本视图=实际源 DEV（FULL_sc 另列）｜exposure=见 evidence_exposure 列｜query_id=E6L-CD-Q15-2


| l_meas | cells | FULL_med_ann_pp | FULL_p25_ann_pp | FULL_p75_ann_pp | share_FULL_pos | G4_med_ann_pp | gross_med_ann_pp | fee_med_ann_pp | t_med | share_t_gt2 | share_t_lt_m2 | share_4seg_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M | 720 | 0.148 | 0.04517 | 0.3015 | 0.9083 | 0.1372 | 0.1363 | 0.00306 | 1.799 | 0.4319 | 0 | 0.1931 |
| Q0 | 5040 | 0.09732 | 0.02475 | 0.3347 | 0.8252 | 0.09171 | 0.09252 | 0.00455 | 1.204 | 0.2264 | 0.003373 | 0.1659 |
| S | 720 | 0.07618 | 0.02006 | 0.2383 | 0.8278 | 0.06916 | 0.06689 | 0.004913 | 1.102 | 0.2528 | 0.002778 | 0.1694 |

