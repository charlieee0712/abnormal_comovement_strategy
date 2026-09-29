# E6k limit_register（L01 起；执行端）

- **L01** 同一历史反复研究：后段是新算子首次评价（NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY），不是样本外
- **L02** RP 最优性只在固定规范配对集内（plan §5.4 更正）；未配对结构性编辑不执行
- **L03** LX 为本项目的配额 / 优先序移植（E6j matched_n 同 N 合同键），不是 DGTW AS 公式；A4b 的 T 重估不是固定共同门
- **L04** HG 主历史四段段首空状态（对齐旧引擎 reset）；跨段连续状态只在 48 个 HG 主展示对象作诊断
- **L05** z_LAG1 段首日无 T−1（未知 size 处理）；size 紧区间对共同未知只算一次
- **L06** Stage 0 第 3 类新算子恒等锚只在推导两段（后段在授权后同代码补算）
- **L07** A6-3 / A3-12 在 profile 产物上抽样 455 / 154（附录 500 / 200）；推导段真实账户落盘后足额复核（checks/closure_deriv.csv）
- **L08** 随机均值是条件于历史的机会基线，不是精确 p 值；MC 误差另报（plan §10.2 / W15）
- **L09** descriptors_E6k.csv 的 evidence_exposure 列为编译器粗分类；逐账户暴露以 selection_exposure_ledger_E6k.csv 为准
- **L10** 对照分布的随机路径只取前 256 条（诊断）
- **L11** 冲击括号（A 5 亿 κ .5 / A 10 亿 κ 1）为未校准情景，不是实际成交成本
- **L12** SMB 暴露回归与尾部账本只作描述；截距占比不等于"不是 size"（plan §10.3）
- **L13** RP 主路径（DFS 节点上限 → 逐级 MILP）在部分日复核失败（HiGHS presolve 下见证解越出预算，2026-09-29 后段首跑发现）：按 X08 / plan §5.4 第 6 条由两条独立精确路径恢复（关闭 presolve、逐级见证复核的 MILP；带符号可达界剪枝的精确深搜；两者一致才采用），恢复日计数 {"2019-2023": 6, "2024-2026": 11}；未恢复日隔离回父并标 SOLVER_LIMIT，计数 {}（含此类日的 RP 账户是混合路径，不称完整 RP 经济结果）；推导两段无失败日（主路径结果与恢复代码无关）
- **L14** 执行端补充 X04：Stage 0 第 3 类新算子恒等锚与 A1-auto 掩码事实在两后段于授权后同代码补算（R0 第 3 / 5 节按段分列）；后段第 3 类结果不回写 Stage 0 manifest（source_manifest 保持开工时状态）
- **L15** 两个诊断的首版退化、由 v2 替代（v1 文件保留不删、不作读数）：衰减场景前瞻版误用同一 draw（`diagnostics/decay/decay_scenarios.csv` → `decay_scenarios_v2.csv`）；HG 跨段连续状态（X09）的上段末状态在段首预热日（门域 K = 0）被清空（`hg_continuous_<段>_<段>.csv` → `hg_continuous_v2_*.csv`，hold_init 只用于该诊断，登记账户不变）
- **L16** 覆盖不足（登记 query 有、本轮未记账）：PM 固定配对交换数的嵌套与结构单边编辑（E6K-Q10-c）；TREFIT 第二关逐日有效样本数（E6K-Q07-b）；POST2 第二关前编辑数只以最终名单相对原父的换入近似（E6K-Q08-b）

## VERIFY 阶段追加（2026-09-30；执行端；L01–L16 不改）

- **L17** 同时带统计量的口径。
  - 定义：`results/full/bootstrap/simultaneous_band_q95.csv` 的统计量是标准化 max-t，M_b = max_j |(FULL*_bj − FULL_j) / SE_j|。FULL* 是段内分层 stationary bootstrap draw 的四段 n 加权年化百分点；SE_j 是 draw 的 sd（ddof 1）；集合限于 SE > 0 且无无支持 draw 的比较。q95 以 SE 为单位。
  - 数值：primary144 L20 3.379 / L60 3.435；all L20 4.810 / L60 4.780。逐对象同时带半宽 = q95·SE_j，primary144 L20 为年化百分点中位 .360、最大 .524。
  - 它与逐对象 95% CI 半宽（中位 .209 / 最大 .298）单位不同，不能直接比。
  - 同单位（未标准化 max-abs，年化百分点）的分位见 `E6k_REPORT_supplement_1.md` S1-Q01（事后口径）。不作门。
- **L18** LEGACY_EDIT5 的"四段全无编辑"处理是实现口径（PX5 未写）。
  - 只在有编辑日的段上判 |edit_gap_absmean_T| ≤ 5；四段都未定义时状态为字面 `N/A`，判定串里既不计失败、也不计待定。
  - 共 140 行：PM15 α .125 四段无换入的 7 个目标 × H 1…20。
  - 字面 `N/A` 用 pandas 默认 `read_csv` 读会变成 NaN。
- **L19** 段均类诊断表与政策表的分母不同。
  - 段均类（四段等权均值）：SMB 的 `D_ann` 与 `alpha_over_D`（逐段比值的均值）、CAP 的 selection / capital / one_sided、Shapley 的 `rand_net_*` 与 Shapley 差、MX-CS 块均、TAILS 的桶份额。政策表的 FULL 是四段 n 加权。
  - CAP 定义：
    - 两边有仓日：sel = ½(Pc + Pb)(uc − ub)，cap = ½(uc + ub)(Pc − Pb)，其中 u = E / P。
    - 只一边有仓日：one_sided = Ec − Eb。
    - 三列都按全段交易日取均值后 × 25,200。
    - sel + cap + one_sided = gross 配对差（不含费用），与 FULL（8bp 净）或 FULL_sc 没有恒等关系。
- **L20** `random_refs_<段>.csv` 中路径间方差为 0 的对象（本轮只有 OWN），`rand_sd` / `mcse` 是单遍方差式的舍入值（约 1e−7 / 7.5e−9），不是 0。
  - 不影响 `e_rand`：OWN 按 PX6 取 NO_NEW_CONTENT_TO_PERMUTE。
  - 也不影响 MC 增补需求（E01）。
