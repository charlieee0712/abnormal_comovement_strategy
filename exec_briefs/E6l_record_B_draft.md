# E6l 记录 B 草稿（方式 B：推导两段算完、封存；后段按预授权直接进入）

用途：brief §5 / W11。授权对象 = 冻结清单（`registration/B_package_manifest_E6l.json` + `P_package_manifest_E6l.json`）全部描述符 × 两后段 + 附属 / 同资本 / 随机闭包；逐对象字段见 `registration/record_B_draft_objects_E6l.csv`（34120 行）。

- 生效条件（W11 方式 B）：Stage 0 六类全 PASS + A1-auto（pre / 草稿）全 PASS + 进入后段时冻结清单 sha 不变 → `record_B_entry_post_E6l.json`
- 用户原话（`record_B_preauthorized_E6l.json`）：转交消息"记得好好思考提速优化方案 中途不需要停下来报告 避免空转"；执行端询问后用户选"方式 B：一口气跑完"
- 草稿不含门：不设"推导中位 ≤ 0 不进"；新算子不 chosen；deployment_authorized = false

| 机制重要性 | 描述符数 | 暴露分布 |
|---|---|---|
| control | 1560 | {"NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY": 1200, "SECOND_EVALUATION_SAME_HISTORY": 360} |
| dose_panel | 72 | {"NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY": 65, "SECOND_EVALUATION_SAME_HISTORY": 7} |
| main_display | 72 | {"NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY": 60, "SECOND_EVALUATION_SAME_HISTORY": 12} |
| neighborhood | 72 | {"NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY": 65, "SECOND_EVALUATION_SAME_HISTORY": 7} |
| research_grid | 32184 | {"NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY": 29794, "SECOND_EVALUATION_SAME_HISTORY": 2390} |
| source_parent | 160 | {"SOURCE_PARENT": 160} |

A1-auto 草稿项（字段齐，PARENT 源锚行除外）：PASS（缺失计数 {"exposure": 0, "mechanism_importance": 0, "effective_support_days": 0, "D_deriv": 0, "unresolved_limits": 0}）
