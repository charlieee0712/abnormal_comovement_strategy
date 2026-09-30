# E6l lessons_delta（执行端；六类标注 A 仪器 / B 未匹配比较 / C 机制未读源码 / D 前提外推 / E 过早收口 / F 节奏文档；不写共享 memory；交付后冻结，补充另起 supplement）

用途：协议 v1.1 执行端交付件。只记本轮执行中实际发生、可复用的做法与失误；编号接 E6k lessons 1–37。

| # | 类 | 事件（本轮实际发生） | 做法 / 改法 | 证据 |
|---|---|---|---|---|
| 38 | A | numba `cache=True` 的**自递归**函数（numpy pairwise 求和复刻）首次编译运行正确，第二个进程从缓存加载时段错误 | 缓存的 numba 函数一律写成非递归（显式栈）；提速件的逐位对拍必须在"从缓存加载"的新进程里再跑一次，不只在首编译进程里跑 | `e6l_fast._pairwise`；Stage 0 c6 fast_identity（新进程） |
| 39 | A | 状态缓存 npz 的 ticker 列存成 object 数组，`allow_pickle=False` 读不回 | 字符串一律转 unicode 数组再存；缓存写完立刻用读路径（`L.npz`）读一次 | `cache/state/state_full.npz`（未用）→ `state_full_E6l.npz` |
| 40 | A | `load_all_daily_data` 默认写公共缓存目录（不可写），首次状态缓存构建失败，回溯含家目录路径进日志 | 全程数据一律走 `e6f_core.guarded_load(cache_dir=私有)`；所有运行从第一条起经输出脱敏包装（`e6l_run.sh`） | `logs/state_cache.log`（已就地脱敏）；A6-6 |
| 41 | F | Stage 0 检查脚本的期望值手写错两次（c1：E6k 每段账户 npz 116 → 实为 58 + 58 权重；c5：增补规划 (1.2/.03)² = 1,600 → 应 2,048 而非 1,536） | 期望值从源文件 / 公式现算（纪律 ㊵ 的执行端版）；被测代码不因检查脚本的错而改 | `task_status/stage0_c1_identity_rerun`、`stage0_c5_random_rerun` |
| 42 | F | A1-auto 首跑拦下：卡 Q04 无绑定比较（A0 只编了 spec 的基础比较，测量核配对未编）；复跑又拦下 Q10（真实 − 随机未编入比较清单） | A0 编译器加"每卡 ≥ 1 条绑定比较"的自检，在 A1-auto 之前；卡的判别列（plan §12"判别"）逐条映射到比较 kind | `registry/_superseded_v1..v2/`；A0 v3 |
| 43 | F | 政策 JSON 转录 E6k 原文带进 N/A / NA / NaN 状态词；禁用词表本身以字面写进被扫描的 JSON | 转录时归一为 UNDEFINED，原件以 sha 引用；禁用词清单只写代码引用（`e6l_core.FORBIDDEN_STATUS`），不以字面进文档 | `registration/_superseded_v3/`；A1-auto rerun3 |
| 44 | A | 附录 A3-4 写"DECAY(L = 10⁶) ≡ HG10 逐位"：有限 L 的折让 < b，近似并列会被改变（2010-2014 有 10 格不同） | 机械端点按 spec 写成显式特例（L = ∞ → fac = 1），逐位 PASS；有限大 L 的差异作 INFO 报 | `source_resolution.md` #2；A3-4 |
| 45 | C | 生产 Mmean 的综合分是"可得腿均值"（complete = False），门域 .2% 单元不足三腿，b/3 在这些单元不是精确 K 点折让 | 核源（`e6j_engine.py:173`）后按 brief 锁定 b/3 并登记限制；不另开对象 | A3-12；limit_register |
| 46 | B | brief W08"E6k 同构对象 ~4,000 个"按类型计；真实清单交集 2,936 | 同构集合一律从真实清单交集算（plan §13.1） | `descriptors_E6l.csv` e6k_equiv；carried A2-4 全量 |
| 47 | A | 部署脚本 14:12 才开始逐版本存档，13:44–14:12 的中间版（e6l_a0 / prereg / a1_auto / stage_a 首版）字节未留 | 部署脚本从第一次部署起存档；代码变更登记的反向还原只对存档版本核验 | `reports/E6l_code_change_register.md` |
| 48 | A | 提速：numba 门递推 / 第二关 / 多 H 账本（逐位 = 参照）+ 段内 fork 进程池共享环境 → 随机每路径约 77 s → 约 25–29 s（2010-2014，全部测量合计） | 先 profile 找瓶颈（账本 > 门递推 > 第二关）；逐位对拍作为 Stage 0 必检项 | `stage0/c6_output/fast_identity.csv`、`timing_extrapolation.json` |
| 49 | F | plan §7.5 写明"真实 − 随机的跨时间均值另做共享日期 bootstrap"，A0 生成的 bootstrap 比较清单没有这一族；开跑前逐条对 plan 复核分析脚本时发现 | 分析脚本开跑前把 plan 的统计条目逐条映射到"脚本 + 函数 + 输出文件"，映射表缺项即补；本轮补 CR 族（键 = 描述符 × H × 机制，与 `random_daily_<段>.npz` 同键，试跑文件 3,942 / 3,942 键命中） | `e6l_bootstrap.py`（15:00 版）；R0 §8 |
| 50 | A | 后段计算期间在临时目录跑冒烟链（推导两段；后段列名用推导段顶替；封存核对打桩；只写 `tmp/e6l_trial/res_smoke`），抓到两处会让正式链在最后一步抛错的问题：mechanisms 同时带只有 `q95_maxabs_t`、没有带符号列；cards 印出登记 query 标题里库存标记到上限的技术词，该词在 REPORT 禁用词表内，触发扫描 | 正式链之前用已封存的推导段把全部下游脚本走一遍；同时带补单侧带符号 `q95_max_t` / `q05_min_t`；登记原文进正文经 `regtext()` 写作"满额（saturation）"，登记文件不改 | `tmp/e6l_trial/res_smoke/logs/`；`e6l_bootstrap.py` / `e6l_reports.py` 15:27–15:30 版 |
| 51 | A | 冒烟链日志行把 `$(date)` 写在 `$?` 前，命令替换先执行并重置 `$?`，失败步骤被记成 rc=0（政策冒烟实际抛错） | 取返回码一律先存 `r=$?` 再拼日志；正式链用 `cmd \|\| fail` 形式，不受影响；判断以日志里的 Traceback 为准 | `tmp/e6l_trial/smoke_chain.sh` 与 `smoke2.sh` 对照 |
| 52 | A | MC 增补规划在首 1,024 路径完成后即可算：推导两段 0 / 44 组需增补（最差 MCSE .0155 / .0230，路径 sd 最大约 .74 ann_pp）；2010-2014 段增补提前在空闲核上启动，结果为空操作 | 随机首批路径数可按 (sd_max / MCSE 目标)² 事前估；同类随机下轮可直接按此定首批数，省一轮规划 | `task_status/mc_done_deriv_*`；R0 表 E6L-R0-MC |
| 53 | A | MC 增补驱动沿用"每组一次调用、512 路径一片、逐组串行"：推导段 0 组需增补时无影响；后段 2024-2026 有 4 个 COND 组需增补，单组 512 路径约 30 分钟，串行约 2 小时，会成为关键路径 | 用已完成分片先估路径离散（sd > .03·√1024 ≈ .96 即需增补）；增补按（机制, have, topup）合并一次调用、小分片（64）并行；某段首批完成即在空出的核上提前增补，主链步骤届时重新规划为 0 组 | `e6l_topup.py` 16:48 版；`logs/topup_2024-2026_early.log`；WORKLOG 16:3x–16:48 |
| 54 | A | 分片不变性第一次核验用 profile 模式：该模式先把新测量日内打乱，COND（ISK 树叶内置换）结果随之改变而 LEGACY（日内置换）不变，误报成"COND 与分片大小有关" | 不变性 / 复现核验一律用与正式运行相同的内容与参数，只改被测因素（这里是分片大小）；profile 模式只用于计时 | `tmp/e6l_trial/chunktest64`（profile）与 `chunktest_real`（真实内容，32 / 32 / 8 片逐位相同） |
| 55 | A | 增补分片改为 64 一片后，`e6l_seal.planned` 的队列推算仍写死 512 一片，seal_post 报"缺 4"失败（17:05:26）；改为从 `e6l_topup.TOPUP_CHUNK` 推算后续跑（17:08:56） | 同一口径（分片大小、文件命名）只在一处定义，所有生产方与消费方引用它；改任何产物命名规则前先 grep 全部读方；改完先干跑消费方（这里是队列核对）再放行 | `logs/seal_post.log`、`seal_post_rerun.log`；`logs/chain_main.failed`（保留）；`chain_main2.*` |
| 56 | F | 卡片八字段需要的逐卡判别读数（比较层 FULL 的分布）只在执行端临时汇总里，决策端按 query_id 回链不到 | 把逐卡判别读数做成 cards 附节（41 张带 query_id 的表，E6L-CD-*），与正文同一结构化查询生成；卡片文字只引 REPORT 表 | `reports/E6l_REPORT_cards.md` 附节；`e6l_reports.card_digest` |
| 57 | F | Q03 按零 d 分组的名单差、Q04 EW 数据有效年龄、Q15 rank ACF 三项登记判别事实未算：A0 只把判别项映射到比较 kind，没映射到事实表列 | A0 编译时"判别项 → 比较 kind / 事实表列"两类都逐条映射，A1-auto 对缺列拦下（lessons 42 的事实版） | limit L16；三张卡的 alternative_surviving |
| 58 | A | 分析链原设计等主链全部完成（含 bootstrap）才起分段诊断；这些诊断只读已封存账户与登记 | 按输入依赖定触发点：状态时钟 / 影子风险 / 记忆年龄 / 连续面板在 seal_post 后即起，与统计 / 政策 / bootstrap 并行；固定表等政策；REPORT 等 bootstrap（同时带要进 mechanisms） | `tmp/e6l_stage/chain_analysis2.sh` / `chain_analysis3.sh`；`logs/chain_analysis3.steps` |
| 59 | A | 随机耗时外推只用 2010-2014 profile：外推 111 CPU 小时，实际 131.6（2019-2023 单片 LEGACY 1,671 s / COND 3,069 s，是 2010-2014 的 3.3 / 5.6 倍；后段股票数约翻倍，COND 树置换成本随叶内股票数上升） | 外推按段的股票数 × 日数加权，并对最大段单独 profile 一个 COND 分片；把长分片放在最前（本轮已按行数 × 路径数排序） | R0 表 E6L-R0-TIMING；`task_status/run_rand_*` wall_s |
