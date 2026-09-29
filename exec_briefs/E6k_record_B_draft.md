# E6k 记录 B 草稿（方式 A：推导两段算完、封存；后段等用户一句话）

用途：brief §5 / W11。授权对象 = 冻结清单（`registration/B_package_manifest_E6k.json` + `P_package_manifest_E6k.json`）全部描述符 × 两后段 + 其 COMMON_SUPPORT / 同资本 / 随机 / 附属对照闭包；逐对象字段见 `registration/record_B_draft_objects_E6k.csv`（39142 行）。

- 生效条件：Stage 0 六类全 PASS（source_manifest）+ A1-auto（pre / masks / draft）全 PASS + 进入后段时冻结清单 sha 不变（`--conditions` 回执）
- 用户动作：一句话批准（或"B"事前整表授权）→ 执行端写 `record_B_approved_E6k.json`（引原话与日期）→ 条件回执 → 两后段同版本一次算完 → seal_post
- 草稿不含门：不设"推导中位 ≤ 0 不进"；新算子不 chosen；deployment_authorized = false

| 机制重要性 | 描述符数 | 暴露分布 |
|---|---|---|
| control | 4200 | {"first_evaluation": 4200} |
| main_display | 154 | {"first_evaluation": 120, "same_account_exposed": 29, "related_exposed": 5} |
| research_grid | 34628 | {"first_evaluation": 32016, "related_exposed": 2005, "same_account_exposed": 607} |
| source_parent | 160 | {"source_parent": 160} |

A1-auto 第 7 项（草稿字段齐，PARENT 源锚行除外）：PASS（缺失计数 {"exposure": 0, "mechanism_importance": 0, "effective_support_days": 0, "D_deriv": 0, "unresolved_limits": 0}）
