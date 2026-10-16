# -*- coding: utf-8 -*-
"""E6m 阶段 S 代码变更登记（附录 D-3）：code_register/deploy_log.csv 中 --since 之后的每次部署 → 时间 / 文件 / 动作 / sha / 上一版 / 原因 / 影响面 /
与上一版的机器差异摘要（增删行数、改动到的顶层函数与类，由 code_register/versions/ 两版逐行 diff 得出，不凭记忆写）。
原因：REASONS 里按 sha16 写的是执行端当时的改动理由；没写的 UPDATE 标"见差异摘要"（不编原因）；NEW = 首次部署。
输出 stageN/code_change_register_stageS_dev.md（B2 开发期）；阶段 S 再跑一次覆盖到交付前。"""
import os
import re
import sys
import json
import difflib
import argparse

import pandas as pd

import e6m_core as M

REASONS = {
    '4f92838808542386': ('REPORT supplement 1（新文件，决策端任务单 2026-10-12 §1）：E01 占位 query 的卡到固定表绑定与行数；E02 字面 nan 的 11 处正确文本；E03 Δgross 三项表合计补算（总差只在权重有变化的列上求和，三项与交付表逐格核）；E04 L-S8 状态栏；输出 supp/R1/ 与 handoff reports/ 新文件', '不改 REPORT、登记与封存件'),
    '934902d6e6d4afb4': ('S15 补充核验修正：路径日期先剥工作目录名（目录名带时间戳，首跑把 4 个测量缓存误判为 E7 期）；第 5 项加扫 stageS_dev/meas 测量缓存', '不改结果与已交付目录'),
    'b1879e010409a5e4': ('闭包门 S15 在 47 上的补充核验（新文件）：按决策端 2026-10-10 判据 S15-47 五项核；第 4 项生产任务当时没装审计钩子，改用同一代码、生产参数重放全部数据入口并记录打开的文件；只读，输出 supp/S15/，补充交付另起 handoff 目录', '不改结果与已交付目录'),
    '77e9b40dfcc580f9': ('副本包收补充件 S1：P0_REVIEW 加 supp/S1 的 manifest / summary / 事实表，P1_LEDGER（final）加 supp/S1 的名单与账户 npz（原 tiers 不含 supp/）', '其余各层文件清单不变'),
    '02bd96f15f928460': ('补充件驱动：结果行 ok 转 bool、打印加 default=str（numpy bool 不能 json 打印；10-12 21:21 四段在 A06 写完后于打印处退出）', '不改计算'),
    '2cf02815e1fb4aa7': ('名单层按形态筛 owner 也认 SUPP: 编号（按 supplemental 的 parent 归形态）：原写法只认带 | 的编号，SUPP 全漏，SAME_N_CORE_DEEP 的 SUPP 分支成死代码（S10 覆盖 240 行 NOT_RUN）', '不重跑；只影响以后的重跑。本轮这 240 行由补充件 S1 补算（用户 2026-10-12 定）'),
    '4662c3dfd4fdc8e1': ('run_aux 加 only_keys / skip_fpwd（缺省不变）：补充件只算指定键、不重算冻结父权重删除', '缺省调用行为不变'),
    'bee60954ad1f20b2': ('aux_facts 另读补充件 S1（supp/S1/）的名单 / 账户事实：只补主路径没有的键，与主路径重键即停', '主路径各键状态不变'),
    'edbf412c14af6ecc': ('交付集加补充件 S1（manifest、summary 与事实表）', '只增交付件'),
    '34b36c20dc0f9471': ('加入口 supp1：四段并行跑 e6m_s_supp1.py run，再写 manifest', '其余入口不变'),
    '7a9c9d13ba73c586': ('补充件 S1 驱动（新文件）：名单用 Aux.v_same_n_core_deep（cfg 同主路径 SUPP 分支），账户用 run_aux（only_keys、skip_fpwd）；写 supp/S1/，不改封存件；verify 用常规 V 行对封存件逐位比对', '只写 supp/S1/ 与回执'),
    'aa0745a1d4d00ef8': ('闭包门 S07：扫交付集（deliver.collect）而非整个工作目录；名字按路径分量匹配（与 M.san 同式）。47 实测：交付集 409 个文件 0 命中；整目录的命中都在不交付的日志 / 代码存档 / 试跑里，或是 2 字符账号名的子串误报', 'IPv4、关键词、家目录三条规则不变；只影响 S07'),
    '5e6456a7946ef084': ('闭包门 S05：A1-auto 判定与补丁十四同一规则（只剩第 2 项 FAIL 且人工逐句核记录 PASS、带用户原话与日期、sha 绑定当前 a1_auto 与转录件）；门里重新核绑定', '只影响 S05；无记录或 sha 不符时照拦'),
    'bec2283470538f3f': ('B3 合并：随机表左连接后无随机值行的键（Q09：两种机制按 e6m_b3_run.mech_mode 全 NOT_APPLICABLE）按 contrasts_status 核后填 random_id = NONE、随机状态 = NOT_APPLICABLE；不是全 NOT_APPLICABLE 即停。原样留 NaN 时 fixed_full 扫到禁用词 nan（b3_pairs 1、b3_random 2）', '只改 180 行 Q09（U0）的 random_id 与 b3_random 状态；数值列与行数不变'),
    '3f71cc8e646aee33': ('s4_tail 起点前移到 b3_tables（补丁十六：B3 表要重建）', '整段 s4 仍按原顺序执行，行为不变'),
    'b9def5aa8a8eb1ed': ('锚 ii 比较改为 NaN 位置一致 + 有限格 max|Δ| ≤ 1e−9（ledger_cmp）：两边 NaN 都是 bench 预热日（四段各前 19 日），原写法 np.max(|a − b|) 遇 NaN 恒 FAIL；容差不变；表加 nan_led / nan_main / same_nan_pos / criterion 列', '10-12 只读诊断：四段 × 六形态 NaN 位置全同、有限格 max|Δ| = 0；status 列与下游读法不变'),
    '7fb01a878e1d9150': ('s4 自 cont_ledger 起拆成 s4_tail，加入口 s4tail：锚 ii 修后只续跑后半（整段重跑会让 topup 覆盖 mc_plan_<段>_r0、seal 改写 written_at）', '整段 s4 仍按原顺序执行，行为不变'),
    '8d155cc0811b195e': ('生效条件：A1-auto 只剩第 2 项 FAIL 且人工逐句核记录 PASS（用户原话 + 日期，绑定当前 a1_auto / 转录件 sha）时视为满足；冻结件不改（用户 2026-10-11 放行）', '只影响 conditions；无记录或 sha 不符时门照拦'),
    '32f50d6ad9768fca': ('random_refs：同分片内同 (desc, H) 的重复登记行只取首行（36 个 V 键在 item 2 / 4 各登记一行，次行全零）；重复行非空即抛错——补丁十的重叠守卫在补算第一轮拦下', '均值 / n 不变（零行原本即被排除），paths_run / shards 不再翻倍'),
    '4a96b03df6bd62b9': ('rand_paths：同分片重复登记行只计一次路径数', '这 36 键路径数由 2048 回到 1024；状态词不变'),
    '7e4af6dd8d5f2fe1': ('交付索引 / 复制收 stageN/E6m_stageS_decisions_*.md（代拟决定记录，advisor 第 5 条）', '只增交付件'),
    '4a4efe872e65213e': ('内容随机下 PARKINSON veto 行：同 owner × H 的 DELETE_BUDGET_COND 各段算满 → RANDOM_NOT_SCHEDULED（plan 第 604 行"V 用同删除机制"；36 / 36 覆盖已核）；否则仍 NOT_RUN', '只影响这 36 行的状态词；回执记 v_content_by_delete'),
    '566d00e37dae5cc3': ('S15 在 47（无封存目录）改判：A1-5 守卫攻击全 PASS 且账户 / 随机日期轴 ≤ 2026-03-27（数据源截止后文件数只记 INFO）；云机分支不变', '只影响 S15；判定为独立函数 e7_cutoff_47 可单测'),
    '7bd2c612679e9120': ('47 执行方式：并发 / 上限 / 内存预算 / 随机分块 / 金丝雀由环境变量设（缺省 = 原值）；已有整段 1024 分片的组合不再分块；随机大机制先跑', '只改调度；结果文件按 p<起>_<数> 分片，统计按路径号拼接'),
    'd460d9cf8ecb7d9c': ('random_refs 加分片路径区间重叠守卫（重叠即抛错，防重复计数）', '无重叠时数值不变'),
    '996f35f6502155d4': ('随机层 stage2 换 e6j_fast.stage2_fast（E6M_STAGE2_FAST=0 可关）；A4b 类形态名单下游提速', '与原实现逐位相同（E6j 核对 + 本轮复核）'),
    '3a929666105059d9': ('r_edit 真实结构取列名（e6l_env.SegL 的 .S.ccolnames；mock 仍 .ccolnames；统一转 str）——随机层试跑 R-EDIT 24 组合 AttributeError', '只影响 R-EDIT 两机制'),
    'dcb6c59ce656384c': ('内容随机下删除类算子（PARKINSON veto，登记 SOURCE_WAIT，V 内容随机未定义）本轮跳过并在回执记数——试跑 CONTENT_ISK 6 组合 ValueError', '36 行维持 SOURCE_WAIT；其余行不变'),
    'a80f4e20b5d401e1': ('make_draws 加 kfs：E6l 环境不认识的测量（E6m 两日测量）用本轮 kfs（Q0 两表示逐位相等已核）；不传 kfs 时行为不变（S1 随机复现不受影响）', '只影响 LEGACY / CONTENT_ISK 在两日测量上的内容随机'),
    'be0462ba129c572f': ('main_accounts 把 rt.kfs 传给 make_draws（canary 5 h 21 min 后在 Q_LAGRAW1 报 ValueError）', '同上'),
    'fdd6e8e17b0a5978': ('memage：登记中本形态无 HG10 / LAG1_10 源记忆对象（R2 / A06）时记 NOT_APPLICABLE（空表 + 回执 applicable=0 与 note），不再判 FAILED；有对象时判据不变（逐日重构 = 段汇总 ≤ 1e−12）', '只影响 R2 / A06 的 memage 回执；memory_age_daily 按 glob 合并，空表无行'),
    '29908753b3796608': ('A2-4：E6K_POLICY 登记中 E6k 未覆盖、E6l 有的对象改由 E6l 锚（用户 10-10 定，登记不改）；新增 E6k∩E6l 同构 policy 一致性检查作前提（1e−9）；两边都无才 FAIL', '只影响 A2-4 的 anchormap 行；锚对象集合不变'),
    '0122f1b57aed20f6': ('A2-4 抽样：policy_E6k 无同构行的 E6K_POLICY 对象归第三组 E6l（E6k 未覆盖），对 policy_E6l（1e−9）；行文里的 policy 名按实际来源写', '只影响 A2-4 抽样分组；随机种子不变（E6k 组组成变化，抽中对象会变）'),
    'b3f0baa676db5078': ('A2-8 判据由完全相等改为 NaN 位置一致 + 有限值 max|Δ| ≤ 1e−12（用户 10-10 定；三段舍入级差 1.6e-17 ~ 2.8e-17）；表里照报不等格数与 max|Δ|', '只影响 A2-8；A2-5 仍完全相等；翻符号埋错仍 FAIL'),
    '6396f38509e6db24': ('X27 改为 V_park20_LEGACY__LEGACY_PARK_NAN（estimand intraday_range_vol / source_bridge / legacy_key __park__；2010-2014 逐位 = 本轮 vol，差 0、NaN 位置一致）；上一版 V_park20_obs 是方差口径 intraday_range_variance，A2-8 四段 FAIL', 'X27 一项；A2-8 判据不变'),
    'ae90595805825d52': ('A2-8 读 V_park20_LEGACY（policy=LEGACY_PARK_NAN）；member() 加 policy 参数（缺省 OBS，其余调用不变）；合成测试同名', 'A2-8 判据不变'),
    '4b506834de4c352e': ('X27 说明改为 LEGACY 实名', '只改说明文字'),
    '21e22db83f1c5945': ('A0-S 在 47 的状态改用本模块状态词 INFO（Book 只收 PASS / FAIL / SOURCE_WAIT / INFO / NOT_RUN，上一版首跑 ValueError；NOT_APPLICABLE 写进 got）', '只影响 A0-S 一行；INFO 不挡 Stage 0 门'),
    '1ad96bd9d93103a5': ('47 实跑：X27 路径改为 47 实名 V_park20_obs__OBS.*（plan 写作 parkinson*__OBS，47 上无此名）；A0-S 在 47 上记 NOT_APPLICABLE（原位读取无拷贝；云机缺清单仍 SOURCE_WAIT）', 'X27 与 A0-S 两项；外部输入身份仍由 A1-2 原件 sha 核'),
    'c276e047e26910e2': ('47 实跑：A2-8 取 V_park20_obs__OBS（47 实名）；合成测试同名', '只改文件名；A2-8 逐位判据不变'),
    'dc1aae09f4c90044': ('X27 说明改为 47 实名', '只改说明文字'),
    'fbf43a9f9ebdf5e9': ('47 可移植：新增 RUNS / SEALED 两个路径常量（环境变量 E6M_RUNS / E6M_SEALED，缺省 = 云机原值）', '只加常量；云机缺省行为不变'),
    'a299085f10cd2299': ('47 可移植：handoff / replica 目的地与封存目录改由 e6m_core.RUNS / SEALED 给出（缺省 = 云机原值）', '只改路径来源；云机缺省行为不变；47 上 S15 封存检查照实报'),
    '4d1a2e1ed2f9c9e7': ('47 可移植：handoff / replica 目的地与封存目录改由 e6m_core.RUNS / SEALED 给出（缺省 = 云机原值）', '只改路径来源；云机缺省行为不变；47 上 S15 封存检查照实报'),
    '8310a4fb87891551': ('47 可移植：handoff / replica 目的地与封存目录改由 e6m_core.RUNS / SEALED 给出（缺省 = 云机原值）', '只改路径来源；云机缺省行为不变；47 上 S15 封存检查照实报'),
    'f6dc0dce710c2245': ('47 可移植：handoff / replica 目的地与封存目录改由 e6m_core.RUNS / SEALED 给出（缺省 = 云机原值）', '只改路径来源；云机缺省行为不变；47 上 S15 封存检查照实报'),
    'edaf56aeb9d20770': ('47 可移植：handoff / replica 目的地与封存目录改由 e6m_core.RUNS / SEALED 给出（缺省 = 云机原值）', '只改路径来源；云机缺省行为不变；47 上 S15 封存检查照实报'),
    '4537b18a95435ca4': ('47 可移植：handoff / replica 目的地与封存目录改由 e6m_core.RUNS / SEALED 给出（缺省 = 云机原值）', '只改路径来源；云机缺省行为不变；47 上 S15 封存检查照实报'),
    'ea90094867d5b488': ('47 可移植：handoff / replica 目的地与封存目录改由 e6m_core.RUNS / SEALED 给出（缺省 = 云机原值）', '只改路径来源；云机缺省行为不变；47 上 S15 封存检查照实报'),
    '3ef26dc9cb260daa': ('47 可移植：conda 只在云机激活；project_core 取脚本自身目录（47 的 /mnt/sda2 下有多人目录）；设 E6M_TASKSET 时绑核；分段日志里家目录 / 环境名脱敏', '云机不设 E6M_TASKSET 时行为不变；日志只多一道脱敏'),
    '8084f8435adaf77d': ('平局键两处：UNPROTECTED 二级键改为当天无记忆新次序；PRIORITY 记忆版减 bonus 后按 ticker 打平局（真实数据端点在 mock 上发现）', '合成 44 / 44；端点四段 PASS'),
    '0260323955d3fccc': ('Mmean RULE_LAG c1 端点拆成"全门域 K_loading = 1/3 的日子"（须 0 差）与其余日子（口径差记 INFO，STAGE_S_IMPL_PLAN §5 第 2 项）', '只影响检查表'),
    '9899aa774d7fdaf4': ('cmp 对补充对象（SUPP: 左端）取 H 报 IndexError → H 从 right_desc_id 取', '合成链'),
    '05d52d02c86c1b00': ('描述符统计加目标层暴露（e6l_stats.target_expo 同式：size 紧区间 / 编辑 gap / lv5 / small30 等）', '合成链'),
    'eddda20f654184b3': ('合成账本加入补充 384 对象（SUPP:前 16 位，与 owner 同 H）', 'SYNTHETIC'),
    '729e923399d5a8a5': ('合成随机分片（randoms 任务，E6l randoms 格式）', 'SYNTHETIC'),
    'f89b6b88818532da': ('rand 任务：random_refs / mc_plan（e6l_stats 同式，目录参数化）', '合成链'),
    '790d85c43698cad7': ('阶段 S 随机账户累计函数 run_accounts（B2 不调用）', '—'),
    'a9491906cae4c287': ('N8 代码登记窗口限定在 08:30 前（之后的阶段 S 开发由 e6m_s_code_register 登记）', '只影响登记文本'),
    '89e6c3b3d91316bc': ('卡片表空串被读成 NaN（.split 报错）→ fillna("")', 'Stage B'),
    '338163526ba68db2': ('bound_comparisons 改取 A0 卡片字段、另列 manifest_bound（第一次修；判据仍按比较清单，rerun2 FAILED）', 'Stage B'),
    'e5ea3edd43434d55': ('"无绑定"判据改按 query（B3 / B4–B6 / 方法卡对象不在比较清单）→ 无绑定 0', 'Stage B rerun3 SUCCEEDED'),
    '3b16b6ef2a4268e8': ('字符串日期数组取 max 报 ufunc 错 → 逐值取最大', 'A1-5 静态末日检查'),
    'd0fe450d4c0056b8': ('记忆门补 E6l 同口径门层事实（gate_facts 转录，供 A2-7）', '名单 facts 多 8 列；名单本身不变'),
    'c784db7bc3143699': ('新增 memgate 任务：源 e6l_ops.mem_gate 按 AST 抽取执行，与转录逐位对拍', 'mock 证据'),
    '0689ae36c6f11ac9': ('advisor：close 只计真实结构结果（mock / selftest 目录不计门）', 'Stage 0 门'),
    '2ac04087ad7cea78': ('advisor：compare_policy 改按列数组（itertuples 会静默丢连字符列）；A2-7 改 records；mock 结果写 mock/', '比较器；夹具 12 / 12'),
    '3f5a998de2092746': ('advisor：随机复现补全程日历；structid 加 Stage A 目标统计转录对 e6k_acct.target_stats 逐键逐位', '阶段 S 检查'),
    '7c98d6c81ff87884': ('--struct real（e6m_s_real 结构工厂与目录约定）', 'mock 回归：数组逐位相同'),
    '1150e2afe96eff9e': ('--struct real；源记忆门；T 桥取结构 drop 字段（mock / 真实同名接口）', 'mock 回归：数组逐位相同'),
    '7529ccfdb8362090': ('--struct real（读写路径按模式切换）', 'mock 回归：Stage A 表逐字节相同'),
    '75311d7c54d9f39e': ('账户入口：主 + 附属 + 冻结父权重删票两端（非子集日数）；后段过 post_gate', '阶段 S 才跑'),
    '458a9470ac9f965a': ('随机账户入口（E6k 键内容置换、源记忆门、补充 owner 展开、--group 增补）', '补充分支原样重放 = 附属名单 4 / 4'),
    '274923c9c371664d': ('Runner 可复用已建好的段（随机入口 V 对象不再另建一份真实段）', '内存'),
    '849791b8560725d2': ('随机复现改用 RT 的 mem_gate 参数与真实段适配视图', '阶段 S 检查'),
    'a1d61ed6a8564213': ('读真实账户 / 随机目录前过封存门（附录 D-2）', '合成 / 开发目录不拦'),
    '9bb7ab956413f4c3': ('读真实账户前过两个封存门', '同上'),
    'e3eb65d4b7a5528b': ('--real（卡写 registry、冻结写 registration）；approve 只照录用户原话；conditions 生效条件回执', '开发路径回归正常'),
    '964edcc9d7d68b47': ('第一版把同号已判行也覆盖了 → 按检查文本只重判第 2 / 7 / 3⑬b 项', '计数回到阶段 N（22 / 2 / 1）'),
    '11921acf923ba48b': ('A1-5 G17 改为攻击 B6 触发入口（e6m_b6_triggers.load）', 'G17 NOT_RUN → PASS'),
    '20b62ea4850e0ff1': ('FACT 缺失值写 UNDEFINED（不写 nan）、按配置去重（H 写 H*）；policy 读入 low_memory=False', '禁用状态词 0；行数 130 万 → 6.8 万'),
    'd97f409873eb8a7b': ('配方按数字排序；表头写配方算子；合成数据醒目标记；rand_deriv 改 agg', '报告格式'),
    'f6b859d299b57ce3': ('同时读 accounts 与 accounts_aux（附属 / 补充对象），重复账户 ID 报错', '合成回归逐列一致'),
    '4b4ae46b93dafbc7': ('同上（bootstrap 读 net8）', '—'),
    '84fe3a13f50ac296': ('advisor：未解决失败只扫阶段 S 队列任务族（开发期带段名的 FAILED 回执会误判）', '封存夹具 8 / 8'),
    'bca4d23f8a3b93c2': ('advisor：A1-2 只约束本轮读取的原件，其余参照 INFO（STAGE_S_IMPL_PLAN §5 第 20 项）', '夹具 12 / 12'),
    'bfb0c412cf8ba12b': ('advisor：structid 先核真实 Env.ctx 的键；门分不逐位但名单 / 下游逐位只记 INFO', '阶段 S 检查'),
    'c020ca715529384c': ('advisor：A2-9 预置查询列名不符记 INFO 而非报错', '—'),
    '0ec06f4c84940e68': ('advisor：金丝雀（最重任务先跑，按回执 rss 定并发 ≤ 78 GB）', '—'),
    'c48bff30ebebd98d': ('回执加 rss_peak_gb（金丝雀用）', '—'),
    '6ee11556af09ba28': ('回执加 rss_peak_gb（金丝雀用）', '—'),
    '28dd3dac71812b61': ('advisor：s1 先刷新 import 检查；engine 锚四段都跑（已暴露源对象）', '运行手册'),
    '1c312a5ccdc2a100': ('按实际 diff 改正两条凭记忆写错位置的原因（stats 9899aa77 / 05d52d02、stage_b 338163526 / e5ea3edd）并补 5 条', '只影响登记文本'),
    '9e557f37b998aa5f': ('N8 补充清单加入勘误 1、阶段 S 实施计划与阶段 S 代码登记', '补充交付 2'),
    'ab0932db41d1b306': ('政策合同里的禁用词清单改写成单个文本值（扫描器不再把清单当状态）；文本值单位记 text', '禁用状态词 10 → 0'),
    '6a04efc18153d75d': ('新增 trefit 任务：附属 FROZEN_SOURCE_T_COEFFICIENTS 账户 − owner（T 重估桥）', '固定表 trefit_bridge 的来源'),
    'c721470931a7c399': ('B4 三表接入（推导段 NOT_AUTHORIZED；签名表每对象 × 签名一行状态，§5 第 22 项）；--b4', '固定表'),
    'dc3e5b55fa19f796': ('删除预算状态细分：随机只登记在部分 H → RANDOM_NOT_SCHEDULED（不与 UNDEFINED 混）', 'b5_delete_budget'),
    '6b6714e315ff4977': ('B5 两表接入：骨架无段列 → 按段日数加权汇总到本阶段各段（§5 第 23 项）；--b5', '固定表'),
    '492230d2421eabf3': ('删除预算明细记 n_days（汇总权重）', 'b5 详表'),
    '7a5f44d255ff3889': ('B6 表接入（触发率按批次数、年化量按段日数加权、受限库存日数求和）；状态 NOT_AUTHORIZED；--b6', '固定表'),
    '3327659032698cd3': ('B6 明细记 n_days（汇总权重）', 'b6 详表'),
    'b49181b614e574ef': ('B3 五表：有并入结果（e6m_b3_merge tables）就取；--b3', '固定表'),
    '575ebe3d42ffdc20': ('completion_coverage 加附属清单逐行状态（e6m_s_aux_status；LIMIT 等显式状态算闭合）；--aux', '闭包门 coverage 核对'),
    '5f221d967b3f20c3': ('gate_facts 可选逐日输出（memory_age_daily）；汇总值不变', '名单 facts 不变'),
    'cf393bfc8b41293e': ('memory_age_daily 接入（读 masks/<段>/memory_age_*.csv）；--masks', '固定表'),
    'cf04e30110f4c317': ('队列加 memage 阶段（段 × 八形态）', '阶段 S 队列'),
    '0d31ec9dd2ace582': ('封存的应有任务与失败扫描加 memage 族', '封存夹具 8 / 8'),
    'a58bbf6e332f16f6': ('runbook s2 加 memage', '运行手册'),
    '68910ba8aff1d7a4': ('补登 17 条原因（1c312a5c 起至 a58bbf6e；按实际 diff）', '只影响登记文本'),
    '273431e67bb3477b': ('R0 嵌入限制登记全文表（原来只列路径与 sha）；mechanisms 第 7 / 10 节标题注明 L-S3 / L-S6 / L-S11', '报告文本'),
    '7501cfcd65e242ed': ('S01 运行中作业排除本进程全部祖先（/proc stat 链；原来只排本进程与父进程，runbook 外壳被误计）；S02 基线键改读 git_head（缺则 head_expected_prefix）', '闭包门 S01 / S02'),
    '2a5c02994a8b2eb4': ('runbook 加 s4（两后段账户 / 随机 / 增补 → seal_post → 全段统计 / 分解 / B3–B6 / 政策 / 报告）与 s5（副本包 / 代码登记 / 交付索引 / 闭包门 / 复制）；用法行同步', '运行手册'),
    '0b9b31844b80e740': ('断点续跑通道（plan §13.3；附属第 7 项连续链）：src_mem_gate_s（源 mem_gate 的 state / d0 / d1 转录，src_mem_gate 改为其包装）、'
                         'source_gate_s、run_days(state, d0, d1) 与末状态 facts["state"]、band_gates / priority_gates 透传、Ctx.mem_gate_s；不传状态时逐位同旧版', '新增接口；旧路径由 selftest 回归'),
    '6798ccbdaa2e509c': ('加 states_equal（续跑状态逐键比较）与 mid_gate_day（断点切分点）', '检查辅助'),
    '1619632f715dd265': ('加 mem_gate_s_of / source_mem_gate_s（真实 = 源 e6l_ops.mem_gate 的 state / d0 / d1 原样透传；mock = 转录）', '新增接口'),
    '1fc0c5a443f52245': ('Runner 给 Ctx 传 mem_gate_s（连续链在真实结构上用源函数续跑）', '名单阶段输出不变'),
    '71e4bb8e04abca0f': ('新增 e6m_s_continuous：附属第 7 项源理论连续链（e6l_continuous 移植；masks / ledger / selftest）', 'L-S2'),
    '0eb1b648f89a1dcf': ('selftest 的状态比较改用 e6m_s_ops.states_equal（同式，去重复定义）', '—'),
    '8797ae18d28b96f5': ('item 7 SOURCE_THEORY：按连续面板里该 aux_id 本阶段各段都 COMPUTED 判定（原来只看面板文件是否存在）', 'S10 覆盖核对'),
    '2807f8f81e790eb3': ('s4 加 cont_masks / cont_ledger 两步（b3_tables 之后、aux_status 之前），删"第 7 项未写"提示', '运行手册'),
    'b127d4c125a1cd8b': ('P1 加连续链名单位图（results/full/continuous/*.npz；deriv 阶段不含）', '副本包'),
    '6e5319bedee1f8e1': ('交付索引"统计与政策"组加 results/full/continuous/*.csv', '交付索引'),
    'ed568e35fa11e739': ('A3 加断点续跑行：真实结构上转录 src_mem_gate_s 与源 mem_gate 各自中段切分续跑，分片 G = 全程、两段末状态逐键', 'Stage 0 S A3（s1 运行）'),
    '1f6827b00a7add68': ('memgate（mock）加断点续跑行：转录与 AST 抽取源函数各自中段切分续跑（α .25）', 'Stage 0 S mock 证据'),
    '70ae7cabcfda2b4f': ('补登 14 条原因（68910ba8 起至 1f6827b0；按实际 diff 与本轮部署）', '只影响登记文本'),
    '0b302e8dfc8f231b': ('B5A 同门核对记具体哪一项不同（IDS_DIFFER 门域单元数 / KEEP_DIFFERS 源门差格数）进 gate_check 列；状态词仍为 GATE_DIFFERS', 'b5 状态账本详表多一列；夹具 PASS'),
    '526454b194ed2443': ('补登 2 条原因（70ae7cab、0b302e8d）', '只影响登记文本'),
    '6c0f258a1fdfc397': ('post_gate 加授权绑定核对：方式 A / B 授权文件的 freeze_sha256 须等于当前冻结清单 sha（amendment 使授权失效，brief W11）；two_way 加两例', '两向实测 11 / 11'),
    'c9ea2f8cd4775e4d': ('方式 B（用户 2026-10-05 原话）：freeze 读阶段 S 决定文件 authorization_status_E6m_S.json（优先于阶段 N 文件）并在两包冻结时照录写 record_B_preauthorized'
                         '（原话 + 日期 + 清单 sha，已存在不覆盖）；Stage B 卡 t09 在 ⑬b 决策端文件到时取补写文本，加 t09_source 列', '开发目录 stage-b + freeze 验过；registration/ 未动'),
    'c1ac7b31d2643385': ('方式 B：s3 收尾按有无事前授权给提示；加 all（s1 → s5，冻结后先核 record_B_preauthorized 在）', '运行手册'),
    'ff98cbc2655f8db7': ('补登 4 条原因（526454b1、6c0f258a、c9ea2f8c、c1ac7b31）', '只影响登记文本'),
    '70faae8f0188a0ce': ('新增 e6m_s_preflight：外部输入 / ⑬b / 方式 B 三项开跑前检查（任一不过退出码 1）', 'runbook all 与 s2'),
    '3b32c1146f6e6ee0': ('all 第一步 preflight；s2 在 Stage B 冻结前单查 ⑬b（冻结只写一次，冻结后补写进不了卡片 t09）', '运行手册'),
    '08615ad1e989ac9a': ('加 clock 任务 = state_clock_ledger（e6l_state_clock 三时钟移植：形成状态 gross / 日历 Vol3 净差 / 执行日 Vol3 费用差 + STRICT250；对象 = B4 的 78 个、H5）；'
                         'state_arrays 抽成共用；ledger / clock 补 post_gate；selftest 加时钟 2 / 3 三项', '合成 4 / 4；L-S5'),
    'ccd486251f6bbe9f': ('state_clock_ledger 从 NOT_YET 移出，读 e6m_b5 clock 逐段宽表转长表（第一版：每行全部量）', '固定表'),
    '8fb1f22e8420b55f': ('state_clock_ledger 只印各时钟适用的量（不适用 ≠ UNDEFINED）、父对象不印父一侧、来源 CLOSURE_FAIL / SOURCE_WAIT 逐行保留，状态无日时日数 0 记 COMPUTED', '合成转换 32 行，列 = 骨架'),
    '3e74ee82e7d42b2b': ('run 直接读后段收益处补 post_gate（授权绑定的冻结清单与生效条件）', '夹具 PASS'),
    '0257c25bc1013874': ('weightchange 直接读后段收益处补 post_gate', '夹具 PASS'),
    '84ae941e84545992': ('s4 每段加 b5_clock', '运行手册'),
    '0b77142a0310f818': ('补登 9 条原因（ff98cbc2 起至 84ae941e）', '只影响登记文本'),
    'cee5b85cd1b8685a': ('clock：目标位图按 SS.load 同式也读 accounts_aux（键前缀 "accounts_aux:"）；SUM_CHECK 闭合超 1e−12 记 CLOSURE_FAIL（与 FORMATION 同容差）', '夹具 4 / 4'),
    'acf66535bfc148e2': ('补登 2 条原因（0b77142a、cee5b85c）', '只影响登记文本'),
    '3dae8094145bcfa1': ('冻结清单收录 ⑬b 补写与用户授权代拟的决定两份 JSON；卡 t09_source 前缀改"⑬b 补写"（来源角色写在 role 里，不冒称决策端）', '开发目录 freeze 验过'),
    '1a136f4aa3be8ad1': ('新增 e6m_b4_sig：B4 签名 1–3（定义 = delegated_decisions 第 22 项；签名 1 账户锚、签名 3 三组价差、签名 2 完整样本方差恒等式 + 分层匹配 1,024 条 numba）', '合成 9 / 9；L-S3'),
    '32d51d11baf2d85d': ('加 par_segs（四段并行、全部结束后任一段非 0 即停）；s4 加 b4sig（签名 1–3）', '运行手册；静态体检 64 / 0'),
    '60bd6ae8ab541b81': ('b4_signatures：SIG1–3 详表逐段齐全即 INFO（第 22 项决定：详表 + 状态行）', '开发目录冒烟'),
    'cbe2f25e89ca614e': ('mechanisms 加 7a–7c（签名 1–3 详表）', '开发目录冒烟（报告写 stageS_dev/reports_smoke）'),
    '5b4287be9829036b': ('补登 6 条原因（acf66535 起至 cbe2f25e）', '只影响登记文本'),
    '53174a191b7fa3a3': ('签名 2 年度行加 formation_days_in_year；有形成日但一天没算的年（段首历史不足）出显式 UNDEFINED 行', '合成 9 / 9 不变'),
    '74704696b2724671': ('签名 1 / 3 与签名 2 分两步并行（签名 2 意外不挡签名 1 账户锚）；s5 拆 s5a（代码登记 + 交付文档）/ s5b（notes 核 → 副本包 → 交付索引 → 闭包门 → 复制），'
                         'all 到 s5a 为止；报告加 --cont / --fixed', '静态体检 67 / 0'),
    '3d36464385f2052b': ('记录 B 草稿按实际方式出文：方式 B 写照录原话、绑定清单 sha 是否与当前一致、生效条件现状，不再请用户补一句话', '—'),
    'fb8f700878c0e8fc': ('限制编号在影响处引用（R0 §1 L-S8、§2 L-S9 / L-S10、§4 L-S1 / L-S2 / L-S7；mechanisms 7a–7c L-S3、§11 状态时钟 L-S5、§12 连续链 L-S2；carried 固定表 L-S4 / L-S5）；'
                         '这些节缺输入时标题仍写；R0 §1 列阶段 S 决定与两份代拟 JSON', '开发目录冒烟：S11 11 / 0 缺口'),
    'f2e3c91c2d3d8771': ('加 docs（限制登记 / 经验增量 / 代码变更登记三份由 stageN 原件拼进 reports/，逐件注明 sha）、notes-check（notes 在且非骨架）、pick（notes 从机器表取数）', '冒烟通过'),
    'e7074570a290305b': ('S11 改为按限制登记"引用于"列核所列报告正文（剔除内嵌限制表行、整词匹配；原实现因 R0 内嵌全表恒过）；S12 报告清单加记录 B / 限制登记 / 经验增量 / 代码变更登记 / notes',
                         '反例：L-S3 指向 R0 时判未引用'),
}


def defs_touched(old, new):
    """两版逐行 diff → (增行数, 删行数, 改动落在的顶层 def / class 名)。"""
    a, b = old.splitlines(), new.splitlines()
    add = rem = 0
    touched = set()
    owner_new = []
    cur = '<模块级>'
    for ln in b:
        m = re.match(r'(def|class)\s+(\w+)', ln)
        if m:
            cur = m.group(2)
        owner_new.append(cur)
    owner_old = []
    cur = '<模块级>'
    for ln in a:
        m = re.match(r'(def|class)\s+(\w+)', ln)
        if m:
            cur = m.group(2)
        owner_old.append(cur)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        rem += i2 - i1
        add += j2 - j1
        touched.update(owner_old[i1:i2])
        touched.update(owner_new[j1:j2])
    return add, rem, sorted(touched)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--since', default='2026-10-05 08:30')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    D = pd.read_csv(M.P('code_register', 'deploy_log.csv'), dtype=str, keep_default_na=False)
    D = D[D.time >= a.since]
    V = lambda f, s: M.P('code_register', 'versions', '%s.%s' % (f, s[:16]))
    L = ['# E6m 阶段 S 代码变更登记（B2 开发期起；附录 D-3）', '',
         '版本存档 `code_register/versions/<文件>.<sha16>`；差异摘要由两版逐行比较得出。原因列只写执行端当时的改动理由，没写的标"见差异摘要"。', '',
         '| 时间 | 文件 | 动作 | sha256（前 16） | 上一版 | 原因 / 范围 | 影响面 / 验证 | 差异摘要 |', '|---|---|---|---|---|---|---|---|']
    ok = True
    for r in D.itertuples():
        arch = os.path.exists(V(r.file, r.sha256))
        ok &= arch
        if r.action == 'NEW':
            why, eff = REASONS.get(r.sha256[:16], ('首次部署', '—'))
            dd = '—'
        else:
            why, eff = REASONS.get(r.sha256[:16], ('见差异摘要', '—'))
            if r.prev_sha256 and os.path.exists(V(r.file, r.prev_sha256)) and arch:
                ad, rm, ts = defs_touched(open(V(r.file, r.prev_sha256), encoding='utf-8').read(), open(V(r.file, r.sha256), encoding='utf-8').read())
                dd = '+%d / −%d 行；%s' % (ad, rm, '、'.join(ts[:8]) + ('…' if len(ts) > 8 else ''))
            else:
                dd = '上一版存档缺'
                ok = False
        L.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (r.time, r.file, r.action, r.sha256[:16], r.prev_sha256[:16] or '—', why, eff, dd))
    L += ['', '每条部署都有存档与上一版比较：%s。' % ('是' if ok else '否'), '']
    p = a.out or M.P('stageN', 'code_change_register_stageS_dev.md')
    M.atomic_write_text(p, '\n'.join(L))
    M.write_receipt(os.environ.get('E6M_TASK', 'S_code_register'), [p], status='SUCCEEDED' if ok else 'FAILED', code=[__file__, M.__file__], deploys=len(D),
                    archived_and_diffed=ok)
    print(json.dumps(dict(deploys=len(D), ok=ok, out=M.san(M.rel(p))), ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
