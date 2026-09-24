# E6i source corrections —— brief / plan 与 47 源码的差异（执行端 P0 核出，2026-09-23）

规则：plan 与 brief 原文不改；这里逐条登记"原文写的 / 源码实际 / 处置 / 影响"。
brief 的 source-level 事实句整体核对：**0 处事实错误**（I11 分位定义、三腿公式与行号、源键符号、
限价装载、`turnover_rate` 无缩放、环境五项、输入指纹、E6h registry 行数全部对上）。以下是细节补正。

| # | 原文 | 源码 / 实测 | 处置 | 影响 |
|---|---|---|---|---|
| C1 | brief §0.1 / §1.1："47 可达 GitHub（raw 200）" | 47 上 `raw.githubusercontent.com` 两次超时（15 s / 40 s），`https git clone` SSL EOF；`api.github.com` 200（1.56 s）、`git ls-remote` 返回 HEAD `1caba55d` | EDGE 改为本地工作站 clone 固定 commit、逐行审阅后原样复制 `e6i_vendor/bidask/`；vendor check 5/5 | 无（实现来源不变）|
| C2 | plan §5.1 RC "A06/A08 的 C 核心"；brief §0.1 同 | A08 = `T@30\|C:k5+cr5:k10` —— 核只有 T，C 是 **k5 否决** | 按 plan §3.5 自己的规则：C 核心 SLOT 只在 A06；A08 的 CVR 否决与 R1/R2 同入 FOCAL 替换分支；RK 在 A08 标 NOT_APPLICABLE | RC 的核心槽位格数少一个母体；A08 多出 FOCAL 格 |
| C3 | brief §1.1 "可复用 `e6h_core`（SLOT_FALLBACK / … / 软降权与恒等锚）" | 算子实现在 `e6h_rules.py`；`e6h_core` 只放注册表、守卫、派生键、RULE_OBJECTS 名单 | 复用时从 `e6h_rules` 取 | 无 |
| C4 | brief §1.3 "`compute_abnormal_turnover` = −(MA20/MA120)" | `−(MA20(min 10) / (MA120(min 60) + 1e−10))` | LEGACY 桥按源（含 +1e−10 与 min_periods）；锚 A8 逐位 | 无 |
| C5 | brief §1.3 "`cmf_change_neg` = −compute_cmf_change" | 源函数 docstring 写 ΔCMF_10d，实际 `CMF_20d − CMF_20d.shift(5)`；负号在 spec 层 | 登记事实；本轮不重造 cmf | 无 |
| C6 | brief §1.3 "E6h R0 源标签属哪种由 P0 确认" | `compute_forward_5d_excess` = Σ 日超额（**日龄线性归因**）；`e6g_t0.labels` 的 `comp` = entry-fixed | 两钟都有现成实现，作精确旧桥 | 无 |
| C7 | E6h `feature_semantics.csv` "87 键 × 32 列"（E6h 交付记录）| 87 行 × **33** 列 | 登记 | 无 |
| C8 | plan §0.4 / §4.9 "481 原件未取得" | 两个原件在项目目录（tex 211 KB、xlsx 56 KB）| 本轮目录按 plan 自包含公式，无 `[481-source-pending]` 成员 | 无 |
| C9 | E6g / E6h limit_register I7："每进程 ~205 线程、来源未查明，非 BLAS 非 pyarrow 池" | **是 pyarrow 13 `import pyarrow.fs` 时无条件初始化 S3，AWS SDK 起 192 个 `AwsEventLoop`**（与亲和性无关；`initialize_s3(num_event_loop_threads=1)` 在 13.0.0 不生效）| `e6i_boot` 预置 `sys.modules['pyarrow._s3fs'] = None` → 205 → 13 线程/进程，parquet 读取不受影响 | 并发线程预算宽裕（13 worker 时本用户总线程 880）|
| C10 | plan §4.3 Meilijson "执行端对照 arXiv 0807.3492 式 (1)/(3) 复核" | 已读原文 PDF：四分量、翻转规则、α = .273520/.160358/.365212/.200910 与 plan 逐项一致 | 保留成员，不隔离 | 无 |
| C11 | brief §1.3 "`realized_vol_20d`（先核 simple/log、复权、ddof）" | log(C/LC)（同日比值、复权抵消）、ddof=1、min_periods=10、**不掩停牌**（停牌搬运值给 r=0）| LEGACY 桥按源；研究版 V_cc 掩停牌、0.7w（桥差见锚 D 组）| 无 |
| C12 | plan §3.2 "换手率统一为比例而非百分数；原值单位先核源" | 源 `turnover_rate` 本来就是**比例**（中位 0.0145–0.0163），分母 = 流通股（与 volume/(negMarketValue/close) 比中位 1.0000）| 不缩放；不造 `turnover_ff` | 无 |
