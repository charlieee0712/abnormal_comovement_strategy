# E6k routing_review_A1_auto（执行端机械对账；决策端人工 A1 移到 REVIEW）

状态：**全 PASS**（2026-09-29 00:47:40）

| 项 | 细目 | 核对 | 结果 | 说明 |
|---|---|---|---|---|
| 1 |  | 描述符 = 39,142 / 段，与 plan §16.3 compile_design 逐元组、块集合相等 | PASS | {"ok": true, "only_in_compiler": 0, "only_in_spec": 0, "block_set_diffs": 0, "accessory_72_equal": true, "primary144_present": true} |
| 1 |  | 任务 → 对象：每个描述符恰属一个任务 | PASS | 39142 行 |
| 1 |  | 问题 → 对象：对象全在登记表内；每条 query 至少一个对象 | PASS | 47 条 query |
| 1 |  | 暴露台账覆盖全部描述符 | PASS | {"first_evaluation": 36336, "related_exposed": 2010, "same_account_exposed": 636, "source_parent": 160} |
| 2 |  | 方向角色在词表内（main / competitor / both_registered；E6j #65 补 both_registered） | PASS | [] |
| 2 |  | 测量方向：S / M / Q / RARPRE = low_bad（lo），C1 = high_bad（hi） | PASS | {"S": "lo", "M": "lo", "C1": "hi", "Q": "lo", "RARPRE20_LT": "lo", "RARPRE60_LT": "lo", "RARPRE20_SE": "lo", "RARPRE60_SE": "lo"} |
| 2 |  | 方向论证：engine_contract §3 / source_resolution #5 / 补充 X05（RARPRE 与 S 同向；Q 价稳高 = 好） | PASS |  |
| 3 |  | BAND / BAND_COMPARATOR / HG_ONLY 只在生产六形态 | PASS |  |
| 3 |  | TREFIT / POST2 只在 A4b 两形态 | PASS |  |
| 3 |  | RAR 只在 A4b_CVRv5（= R1）/ R2 / A06；R1 不另算 | PASS |  |
| 3 |  | POST2 测量 ∈ {S, Q, C1}（C1 = 同算子主动控制） | PASS |  |
| 4 |  | 锁定值（α / H / b / τ / γ / g / δ / MC / bootstrap / HAC / mean b÷3） | PASS | {"alpha": [0.125, 0.25, 0.5], "H": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20], "landmark": [3, 5, 10, 20], "b": [5, 10, 15], "tau": ["0p5", "1", "3", "INF"], "gamma": ["05", "1"], "trefit_g": ["0", "0p5"], "delta": 0.1, "MC_Z": 2.0, "MC_TARGET": 0.03, "paths_initial": 10 |
| 4 |  | 政策常数与 E6j 口径一致（δ .10、MC_Z 2、MC_TARGET .03、SIGN_TOL 1e−9） | PASS |  |
| 5 |  | 源事实表（brief §0.1 ★ 项）逐条有 Stage 0 证据 | PASS | W02 Q = J_B1_qCC low_bad（c4 A4-4 真实重算逐位） / W03 z_T = negMarketValue 当日 clean pct（c4 A4-1） / W04 DEV 精确合同（c2 A2-1 / A2-4） / W05 行业逐日快照 PIT（c4 A4-3） / W06 E6j flag = 两段 n 加权合并（Q16 复现时按原表） / W07 生产路径 / SLOT / 六形态（c2 / c3） |
| 6 |  | Stage 0 六类全 PASS（source_manifest.stage0_all_pass） | PASS | {"1_identity": true, "2_source": true, "3_new_operators_deriv": true, "4_data_clock": true, "5_random_state": true, "6_output_resources": true} |
| 13.2 | ① | 参数完整性 / 不存在收益预筛：编译器只读登记规则，网格全枚举（A0 不读账户） | PASS |  |
| 13.2 | ② | 对象 / 方向 / 母体映射：任务 = 母体 × 测量，SM 双分量、K0 = PARENT / HG_ONLY | PASS |  |
| 13.2 | ③ | 支持 / 状态 / 权限：方式 A 文件存在；后段守卫 post_gate；HG 段首空状态（X09）；COMMON_SUPPORT 定义（X16） | PASS |  |
| 13.2 | ④ | 公式与端点：Stage 0 第 3 类恒等锚全 PASS（两推导段） | PASS |  |
| 13.2 | ⑤ | 主对象与政策版本：144 唯一存在；policy_profiles 五列（三登记 + 两 print-only） | PASS |  |
| 13.2 | ⑥ | Q 原文与 query 模板非空：18 卡原文 = PLAN_COPY 对应行；每卡 queries 非空（E6j #73） | PASS |  |
| 13.2 | ⑦ | P / B 派生闭包与登记 sha 一致（两包清单记录的 registry 文件 sha = 当前） | PASS |  |

第 7 项（记录 B 草稿字段）在 part1 之后核；附录 B 掩码事实在推导段目标落盘后机械计算（--masks），不读收益
