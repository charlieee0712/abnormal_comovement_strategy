# E6j routing_review_A1_auto（执行端机械对账七项；brief v1.2 §5）

用途：替代中途人工 A1（决策端中途不动）；任一 FAIL 不得提交记录 B 草稿；语义级登记错误留整轮 REVIEW 事后降级。

| 项 | 内容 | 状态 | 说明 |
|---|---|---|---|
| 1 | 登记对账：问题→对象、任务→对象两表逐元组相等；B 每段计数 = 编译器现算；P = 528 | PASS | B=13398（brief 写 13,230；plan §5.10 现算 13,398）P=528 |
| 2 | 五类身份齐全（measurement / orientation / operator / parent / account）；方向论证句与双向标记；hypothesis_id ⊂ Q01–Q17；exposure 标记齐 | PASS | rows=210；exposure 类型 ['alias_of', 'direction_2of1', 'new_combination', 'related_exposed', 'source_member_seen'] |
| 3 | 槽位合法（A08 无 K、B6 只 T、B7 K / T 分域）；每对象含主配置 .25 × H5；H = {1,2,3,5,10,15,20}；α = {.125,.25,.5} | PASS |  |
| 4 | 锁定值非空且与 brief 一致 | PASS | {"policy_aggregation": "FULL_E6I_ALL4", "random_ref": "R-MATCH-SRC (Z-MAP basic)", "capital_ref": "same_capital", "delta": 0.1, "delta_sensitivity": [0.05, 0.15], "policy_confirmation_status": "confirmed_by_proceeding", "main_config": {"alpha": 0.25, "H": 5}, "cost_bp": 8.0} |
| 5 | source_resolution.md 覆盖 §1.3 七条源事实；差异逐条登记 | PASS |  |
| 6 | Stage 0 六项锚全 PASS | PASS |  |
| 7 | B 草稿逐对象含 source exposure / 机制重要性 / 有效支持 / 推导读数 / 未解决限制；无"推导中位 ≤ 0"门 | PASS | 对象 638 / 应有 638 |

结论：七项全部 PASS。
