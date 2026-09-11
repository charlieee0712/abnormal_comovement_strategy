# `exec_briefs/` —— 各轮执行 brief

本目录收 I11 线**每一轮的执行 brief**（规划 session 写、执行 session 照着跑的那一份）。
按三方流程：规划 session 写 proposal → Claude web 写 plan → 规划 session 审定后出 **brief**
（末尾「自审记录」段 = 执行端开工信号）→ 执行 session 在远端跑并回同名 REPORT。

**这里只有 brief。** proposal / plan / REVIEW / REPORT 不在本目录。

| 文件 | 轮次 | 说明 |
|---|---|---|
| `00_协议.md` | —— | 三方协作协议，约束所有轮次（只读边界、并发上限、git 白名单、文档表达规范等） |
| `E0_baseline_reproduction.md` | E0 | 基线复现 |
| `E1_engine_fix.md` | E1 | 引擎两缺陷修正（Calendar `shift(1)` 半天前视 + 收益未复权） |
| `E2_decomposition.md` | E2 | 修正后的分解表 |
| `E3_single_factor_rerun.md` | E3 | 单因子复审（6bp 口径） |
| `E4_aggregation_review.md` | E4 | 聚合复审 |
| `E5a_final_forms_delivery_v2.md` | E5a | 终形态复现 + v2 交付 |
| `E5b_docs_and_delivery.md` | E5b | 文档 + 公共库 + 周报 |
| `E6_wide_scan.md` | E6 | 宽扫描 |
| `E6b_stack_and_sleeves.md` | E6b | 栈与 sleeve |
| `E6c_holding_horizon.md` | E6c | 持有期 |
| `E6d_proposal.md` | E6d | 组合分类学（该轮 proposal 即执行文件） |
| `E6e_architecture.md` | E6e | 架构：否决层的选股价值 |
| `E6f_construction_selection.md` | E6f | 构造参数与选择程序稳健性地图 |
| `E6g_structure_layer.md` | E6g | 结构层（第四腿/换腿、腿变换、条件否决、网格边缘、四腿聚合）+ T0 输家解剖 |
| `E7_oos_extension.md` | E7 | 延长样本 OOS。**⏸ HOLD，尚未执行** |
| `H1_handoff_i11_build.md` | H1 | 建 Claude web 交接包的生成脚本 |

## 脱敏

本仓库为 **PUBLIC**。按 `00_协议.md` §7，入库副本不含登录信息、主机地址、IP、端口、账号名；
主机一律只写别名（`47` / `56`）。`H1_handoff_i11_build.md` 与 `E7_oos_extension.md` 两份里的
**同事账号名**已替换为占位符（`ACCT0` / `ACCT_A`…`ACCT_H` / `ACCT_LIB`），文件头部有说明；
**除这些标识符外一字未改**。其余 15 份与用户本地原件逐字节相同。
