# PROJECT_STATUS.md — I11 事件驱动 A 股策略交接文档

> 交接给 Claude Code (SSH 操作 47/56 服务器)。本文件是接手项目的唯一入口，先读完再动手。
> 最后更新：2026-09-03

---

## 0. 一句话项目定位

在 **I11 事件驱动信号**圈定的股票池（约 150-350 只/天）内，用多个**日频因子做规则筛选（剔尾）**，构造一个**纯多头、持仓 5 天**的选股策略（池2），交付给基金经理（下称"领导"）。领导会自测，决定直接用还是叠加他自己的因子上实盘。**截止 6/10。**

**当前阶段**：**回测引擎修正 + 全候选库复审完成（2026-09-02/03）**，v2 六候选已产出（`delivery/I11_candidate_pools_v2_20260903/`，公共库交付按用户指令），见 §9。引擎两处修正与因子池三处调整见 §4.8–4.11；7/8 的 v1 六候选及其数字已被取代。当前因子池：合成池 = conditional_turnover + turnover_volatility_60d + cum_return_20d（决策层 mean 剔最差半）；规则池 = CVR_20d 窄否决（剔池内最高 1/5）。下一步：样本延长到 2026-09 做确证、T+1 可成交性、L2/概念数据。（"单因子先过关，再谈规则筛选/合成"——这是领导明确要求的方法论，务必遵守）。

---

## 1. 服务器 / 路径 / 环境

- **主力服务器：47**（代码 + 跑回测）
  - 项目代码：`/mnt/sda2/lichenchen/code/project_core/`
  - 数据缓存：`/mnt/sda2/lichenchen/data/cache/`（parquet 缓存，首次加载会生成）
  - 结果输出：`/mnt/sda2/lichenchen/results/<时间戳>_<后缀>/`（**每次跑都是新的带时间戳子文件夹**，不要往根目录堆）
  - 用户：`PengSX`
- **56 服务器**：ClickHouse 高频数据库（分钟/L2），目前**未接入本项目**，6/10 后才用。连接信息见 §12。
- **GitHub**：`charlieee0712/abnormal_comovement_strategy`（Private）
  - **认证 = SSH key（不是 token）**。47 上 git 操作（push/pull/fetch）一律走 SSH；remote 是 `git@github.com:charlieee0712/abnormal_comovement_strategy.git`。**不要用 token 或 https 方式**（旧 classic token `47_server` 已删，用了也会失败）。
  - 47 SSH key：`~/.ssh/id_ed25519`（注释 `47-to-github`），公钥已加到 GitHub 账户（key 名 `turing_47_server`）。变更日期 2026-06-17。
- **数据源（47 上）**：
  - 日 K：`/mnt/big/base/shibo/KLines_make/daily_temp3/`
  - Barra/中性化因子：服务器上已有 loader 封装
- **跑长任务规范**：`nohup python xxx.py > /dev/null 2>&1 &` 然后 `disown`；清理用 `pkill -f xxx`

---

## 2. 核心代码文件（都在 `project_core/`）

| 文件 | 作用 | 状态 |
|---|---|---|
| `data_loader.py` | 加载日频数据，返回 dict（close/high/low/vwap/volume/turnover_rate/mcap/industry_zx1 等）| 稳定 |
| `features_daily.py` | 计算 70 个日频特征，`calc_all_daily_features(data)` 返回 `{name: DataFrame}` | 稳定 |
| `event_study.py` | 含 `PERIODS`（4 段定义）、`get_base_pool(data)` | 稳定 |
| `pool_screening_v2.py` | 含 I11 信号定义、硬约束、各因子计算函数、中性化 | 稳定（地基）。⚠️ 其内 `compute_calendar_pnl` 的 v2 sleeve 路径持仓不 shift（整整早一天），第二次汇报的 +2.45 出自此，已被 DEV 链路取代，勿再引用 |
| `comprehensive_factor_diagnosis.py` | **当前主力诊断脚本**（Event Study + Calendar PnL）| **引擎口径 2026-09-02 定稿（commit cb9fea2）**：`compute_calendar_pnl(..., exec_lag=1, adjust=True)`（持仓按信号日 T 索引、T+1 vwap 成交、`shift(exec_lag+1)`、后复权收益）、`compute_forward_5d_excess(..., adjust=True)`、`adjust_factor / adjusted_prices / vwap_daily_return`。`exec_lag=0 / adjust=False` = 旧口径，仅自测与分解用，禁止用于正式输出（§14）。§5 的旧数字已失效 |
| `selftest_engine_fix.py` | 引擎修正真数据自测 5 条（复权对账 / 除权计数 / 旧口径逐格回归 / 两视角恒等式 / 前视探测器） | **口径守卫·动引擎必跑，应 5/5** |
| `e2_decomposition.py` | 六候选 × {旧/新时点} × {未/已复权} 四格分解 + phase3 24 锚点接线自检（`results/20260903_0935_E2_decomposition`） | 引擎修正证据 |
| `e3_single_factor_rerun.py` | 35 因子 × 双向 × k2/k5 × 旧/新口径 单因子复审表，每段一进程（`results/20260903_1037_E3_single_factor`） | 复审证据 |
| `e4_agg_review.py` | 聚合层复审：rev 席位 / 反转代表 / CVR 合成 vs 否决 / cmf 正向否决 + 双基准 + 8 因子相关矩阵（`results/20260903_1132_E4_agg_review`） | 复审证据·终判依据 |
| `export_delivery_pools_v2.py` | v2 六候选交付导出（自检 E4 锚点 12/12 + 池1 md5 == 0708） | 活跃·交付工具（取代 v1 导出脚本） |
| `export_factors_to_library.py` | 把 I11 信号 + 4 因子按领导格式导出到公共因子库（3 列长表） | 活跃·交付工具（P3 用） |
| `engine.py` | 因子回测引擎,实现领导 PnL 公式（VWAP 旧/新仓位）;纯函数库,当前被 0 处 import | 保留·领导 PnL 公式参照（被 0 处 import,不在现行链路）。⚠️ PnL 除数口径“有条件正确”:喂归一化权重才对;用其自带 factor_to_weight 默认助手会除以全市场（约5000）,即 /5000 bug 形态。复用作参照时必须喂归一化权重,不要走默认路径。 |
| `factor_marginal_diagnosis.py` | 因子相关性矩阵 + leave-one-out 边际贡献回测（建在旧 score_pool 合成框架上） | 历史脚本,但 leave-one-out 边际贡献逻辑当下就相关（确立每因子真实价值）;复用时换双向剔尾口径。留着,优先级不低 |
| `factor_ic_diagnosis.py` | I11 池内因子 IC 参数扫描（找每因子最优窗口） | 历史·参数已固化进 pool_v2;若做“滚动 IC 降权”增强可复用 |
| `full_a_single_factor.py` | 全A 单因子分组测试（跳过 I11 预筛选） | 重要证据·证明 cmf 在全市场反向（非 I11 池选择效应）,支撑 cmf 反向用法 |
| `single_factor_groups.py` | 单因子 2/3/5 分组（I11 池内,看头/尾区分度） | 废弃·错误 √252 年化口径的“案发现场”（勿用其 Sharpe） |
| `sharpe_credibility_diagnosis.py` | 单因子 Sharpe 可信度 3 合 1 诊断（对齐/扣成本/跨段衰减） | 历史·诊断并确立 √(252/5) 修复的证据 |
| `i11_calendar_pnl.py` | I11 日历时间 PnL（回应领导反馈2:拉到时间轴看暴露） | 历史·Phase1 信号验证证据（领导问信号是否过拟合可直接跑,留原地）。⚠️ 其记账时点从 T 日 vwap 起记（同旧 shift(1)），数字带半天前视，只作历史证据，勿再引用 |
| `i11_cross_validation.py` | I11 信号交叉验证（v2a/v2b/v2c 变种对比） | 历史·Phase1 信号验证证据（同上,留原地） |
| `i11_final.py` | I11 最终确认（final_min 等极简变种） | 历史·Phase1 信号验证证据（同上,留原地） |
| `i11_risk_adjusted.py` | I11 风险调整评估 Phase1.7（Sharpe/Calmar/IR） | 历史·Phase1 信号验证证据（同上,留原地） |
| `i11_sensitivity.py` | I11 参数敏感性 & 消融（验证非过拟合） | 历史·Phase1 信号验证证据（同上,留原地） |

**4 段定义（PERIODS）**：2010-2014 / 2015-2018 / 2019-2023 / 2024-2026。**重点永远看 2024-2026**（最难、最接近实盘的样本外）。

---

## 3. I11 信号 + 池子定义（不要改动，已与领导确认）

**I11 触发条件**（在 `pool_screening_v2.define_i11_signal`）：
```
CMF_20d ≥ P80  AND  cr5 ∈ [P25, P55]  AND  ir_pct < P70
```

**池子构造流程**：
```
入场过滤 (apply_hard_constraints):
  剔: ST / 北交所 / 停牌 / 次新(<20日) / 低成交(<2000万)
  保留: 涨跌停 (信号还在, 能否成交是交易层面的事, 不在池定义里剔)  ← 领导明确纠正过
  保留: 科创 / 创业
  不卡市值 (min_mcap=0)
    ↓
I11 触发 (当日 OR 5日窗口 build_observation_pool obs_window=5)
    ↓
池规模约 150-350 只/天 (随段不同)
```

**领导 Q1 权重公式**（池2 用）：
```
weight = min(0.01, 0.03/N_行业内, 1.00/N_总)
```
行业用**中信一级**（industry_zx1）。

---

## 4. 关键认知 / 踩过的坑（最重要，避免重蹈覆辙）

### 4.1 年化系数（已修，但要警惕）
- **5 日 forward 收益必须用 `sqrt(252/5)` 年化，不是 sqrt(252)**。早期用 sqrt(252) 导致 Sharpe 虚高 √5≈2.24 倍（那个 +3.84 就是这么来的，真实 ~1.04）。
- Event Study 部分已修为 sqrt(252/5)。

### 4.2 Calendar PnL 自相关高估（已用三口径解决）
- Calendar PnL 是**每日收益**序列，但持仓 5 天 → 相邻日持仓重叠 4/5 → **强正自相关** → 标准 Sharpe（√252）**高估约 1.9 倍**（已用模拟数据验证）。
- 解决：输出**三个 Sharpe**——
  - `sharpe_naive`（√252，乐观，会高估）
  - `sharpe_nw`（Newey-West，**lag=5**，和持仓周期对齐，保守）
  - `sharpe_weekly`（非重叠 5 日收益，√(252/5)，最干净）
- **NW 和 weekly 应高度接近**（模拟里 2.22 vs 2.43），两条独立保守线互相印证。汇报/判断**以 NW 为准**，naive 仅作上界参考。
- **Calmar / MDD 不受自相关影响**（看累积净值回撤），是稳的。

### 4.3 Event Study 多空 Sharpe ≠ 我们策略的正确度量（关键！）
- 我们策略是"**剔掉最差组、持有其余的纯多头**"，**不是多空对冲**。
- 多空 Sharpe = G_top − G_bottom，只看两个端点，且做空。对"**只有 G1 该剔、其余都不错**"这种"剔尾型"因子会**失明**（多空看着像 0，实际剔尾很强）。
- **实例**：reversal_skip1 在 2024-26，多空 Net Sharpe ≈ -0.02（像失效），但 Calendar PnL（剔G1）naive Sharpe = +2.47，去自相关后 ~1.3（**很能打**）。
- **结论：判断因子有没有用，看 Calendar PnL（剔尾口径），不是看多空 Sharpe。**

### 4.4 "vol/反转大类失效"是错误的预判（已纠正）
- 一度以为传统低波/反转在 2024-26 整类失效（来自多空 Sharpe + 同事口述），差点把 vol/reversal 从池子里拿掉。
- **Calendar PnL 推翻了这个结论**：2024-26 段 reversal ~1.3、parkinson_vol ~0.9、abn_turnover ~0.8（去自相关后），**都没失效**。
- **教训：不要按因子大类预先排除任何东西。一个具体实现失效 ≠ 整个大类失效。我们的 parkinson_vol 是"正向（偏好高波）"，和传统"低波因子"方向相反，别人的低波结论不直接适用。**
- 唯一合理的排除 = **实测后**发现 2024-26 失效或与现有因子高度冗余。

### 4.5 cmf 方向问题（正在用双向剔尾解决）
- cmf_change 是**反向因子**（资金流加速→短期见顶→未来差），全A 和 I11 池内都反向（已验证，非池选择效应）。
- 早期手工"乘负号 + 剔G1"叠加出错，导致 Calendar 结果错乱（-1.11/1.93/-0.28/0.64）。
- **解决方案**：不靠人工判断方向，**双向剔尾**——每个因子都试"剔最低组 vs 剔最高组"，按 NW Sharpe 选最优方向。cmf 应自动选中"剔最高组（反向）"。

### 4.6 成本口径
- 当前用 **6bp 双边**（与历史 factor_marginal_v3 口径一致，便于因子相对比较）。脚本支持 `--cost_bp` 调。
- **实盘真实成本更高**：印花税 5bp（卖出硬底）+ 佣金 + 滑点，百亿私募中低频双边现实下限 **10-12bp**，6bp 实盘达不到。
- 我们换手低（年化~21倍），成本侵蚀温和，是缓冲。**对领导谈实盘绝对收益时，心里按 10-12bp 估。**

### 4.7 其他工程坑
- 47 上 **pandas 版本较老**，`resample('ME')` 会报 `Invalid frequency`，要 try `'ME'` except `'M'`（脚本已兼容）。
- 因子计算别逐 cell 写 DataFrame（极慢），用 numpy 数组累积最后一次性建（脚本已优化）。
- 中性化只算一次缓存复用，别重复算（脚本已优化 `precompute_neutralized_factor`）。

### 4.8 Calendar 记账时点（2026-09-02 修，最重要的口径坑）
- 原 `compute_calendar_pnl` 用回看日收益 `vwap_t/vwap_{t-1}-1`，持仓只 `shift(1)` → T 收盘信号从 **T 日 vwap** 起记收益。收盘后买不到 T 日 vwap，是半天前视；且这段收益与信号相关（CMF 高 / 收盘近区间高的票被系统性高估，反转型被低估）。
- 现口径：持仓按信号日 T 索引、`shift(exec_lag+1)=2`、T+1 vwap 进、T+1+hold_days vwap 出，与视角① `compute_forward_5d_excess`（k=2..1+hold_days）逐笔同起点（`selftest_engine_fix` T4 恒等式 max|diff| 3.5e-17）。
- 量级：只含 T 日盘中信息的探测器（close/vwap−1 keep-HIGH）旧口径年化 +29.5% / NW 9.0，新口径 −6.2% / NW −2.0；六候选 DEV-net 每段下移 1～6 个点，带 cmf 否决的版本更多。
- 视角①（事件研究 / IC / 分组形状）时点一直是对的；受影响的是 2026-05 之后所有 Calendar 口径的数字（含 6/9 归因、7/7 汇报）。

### 4.9 收益复权（2026-09-02 修）
- 原两视角都用 daily_temp3 未复权 close/vwap 算收益，除权除息日记成假跌（2010–2026 共 42,968 个事件，中位 −1.21%，16.5% 的事件 <−20%，最小 −80%）。
- 现口径：`adjust_factor` 由 `lclose`（交易所前收盘价，与 `change_pct` 逐格一致到 5e-5）推后复权累计因子；**用 `is_open` 掩掉停牌行 + `prev` 用 ffill 跨停牌**（数据源在停牌行把 close/lclose 填成正数搬运值，不掩会重复计）。不用 `adj_factor` 列（首次除权前 NaN，3.5%）。
- 方向：组合与基准同受假跌，但我们的选股避开除权前抢权股 → 基准比组合多挨假跌 → 旧口径 2010–2018 超额被抬 1～3.4 个点；后两段≈0。
- 信号 / 因子值仍按未复权价算：是噪声不是前视，改它 = 改信号定义，未动（列为开放问题）。

### 4.10 cmf 方向与"规则池否决"的教训（2026-09-02）
- 6/18 把 cmf_change 从"反向"纠成"keep-high"，依据是旧口径 Calendar 数字；新口径下 cmf_change 激增组是池内最差组（原 4.5 的判断本来是对的），而 7/8 交付的 CMFv5 否决剔的是资金流转弱组 = 池内最好的一组。否决层的 +2.7～3.3 抬升全是时点假象（新口径边际 −1.18/−0.60/+0.19/+0.97）。
- 按正确方向再测否决：三底座只 M_mean3 过 → cmf_change 退役。
- 教训：① 否决层判据"不实质变差即保留"太松，现改为"≥3 段净值升 且 NW 升 且无一段降超 1.0"；② 任何"纠符号"都要在两视角同时成立（形状 worst 组 + Calendar），单靠 Calendar 会被时点假象带偏。

### 4.11 池拖累与双基准（2026-09-02）
- I11 池自身（pool0 DEV 同机制）vs 干净全市场等权：新口径 −5.22 / −2.86 / −1.93 / −0.35（NW −2.75 / −0.80 / −0.89 / −0.09）。6/9 的"裸底池≈中性"更新为"早段显著偏负，alpha 全在池内剔尾"。
- 因此报数固定两条基准：主 = 干净全市场等权（投资者视角，含池拖累）；副 = pool0 DEV 同机制（池内选股能力）。

---

## 5. `comprehensive_factor_diagnosis.py` 当前状态（主力脚本）

> ⚠️ 2026-09-03：本节数字为 2026-05-29 旧口径（shift(1) + 未复权），已失效。单因子最新数字见 `results/20260903_1037_E3_single_factor/summary.txt`（新口径、DEV 剔尾、4 段）。

**最新版刚改完，待在 47 上跑验证。** 当前配置：
- **因子**：目前 spec 里是 4 个原始因子（reversal_skip1 / parkinson_vol / abn_turnover / cmf_change_neg）。
- **每个因子双视图**：
  - Event Study：2/3/5 分组多空 Sharpe（仅参考，非策略口径）
  - **Calendar PnL（主）**：双向剔尾扫描（2/3/5 分组 × 剔最低/剔最高 = 6 组合），按 NW Sharpe 选最优配置，输出三个 Sharpe + Calmar + MDD + 月胜率
- **成本**：6bp（`--cost_bp` 可调）
- **输出**：`results/<时间戳>_comprehensive_diag/` 下 log.txt + factor_metrics.csv + 每因子每段一张 calendar_pnl 图

**跑法**：
```bash
cd /mnt/sda2/lichenchen/code/project_core
nohup python comprehensive_factor_diagnosis.py --period all > /dev/null 2>&1 &
disown
# 预计 15-25 分钟 (每因子扫 6 个分组组合)
```

**最近一次完整跑的结果（旧版，单一 Sharpe，2026-05-29 06:13）**，Calendar PnL Net Sharpe（6bp，naive 口径，未去自相关）：

| 因子 | 2010-14 | 2015-18 | 2019-23 | 2024-26 | 均值 |
|---|---|---|---|---|---|
| reversal_skip1 | 1.43 | 4.40 | 2.37 | **2.47** | 2.67 |
| parkinson_vol | 0.45 | 3.64 | 2.17 | **1.75** | 2.00 |
| abn_turnover | 0.85 | 3.52 | 2.12 | **1.50** | 2.00 |
| cmf_change_neg | -1.11 | 1.93 | -0.28 | 0.64 | 0.30（**方向有问题，待双向修正**）|

> 注：上面是 naive 口径，**去自相关后约打 5-6 折**（reversal 2024-26 ~1.3）。新版跑出来会直接给 NW/weekly。

---

## 6. 待办（按优先级）

> 2026-09-03：本节是 5 月的待办，已被后续阶段覆盖；当前待办见 §0（延长样本确证 / T+1 可成交性 / L2·概念数据）。

### P0 — 验证新版诊断脚本（立即）
跑 4 个原始因子，确认：
1. cmf 双向剔尾**自动选中"剔最高/反向"**，NW Sharpe 转正
2. 三个 Sharpe 关系合理：**naive > NW ≈ weekly**
3. Calmar/MDD 正常
若 OK → 进 P1。

### P1 — 全测 34 个因子（features_daily 30 + 现有 4）
- 把 features_daily 里**重新筛选的 30 个候选**加入 factor_specs（见 §7 清单）。这些都在 `features` 字典里，直接按名字取，**不用写计算逻辑**。
- **加因子相关性矩阵输出**（34×34），用于后续替换/去重/合成判断：哪个新因子强且与现有因子低相关（<0.6）= 真正的新增/替换候选。
- 仍走双向剔尾 + 三 Sharpe。
- **目标**：找出在 2024-26 仍有效、且与现有 4 因子互补的因子，**可能替换掉现有 4 因子里偏弱的**。

### P2 — 外部因子库（99 篇，"量化拯救散户"公众号复现）
- 已分类，结果在 `factor_classification_v2.csv`（见 §8）。
- **23 个 6/10 前可用**（20 个 `usable_now=yes` 日频有代码 + 3 个 `yes_needs_impl` 纯思路需自己实现）。
- 这 23 个的计算逻辑是**独立读 parquet 的脚本形态**，需逐个**改写成接收我们 `data` dict 的形式**才能进诊断框架。这是真功夫，**分批做**。
- 注意：作者回测差 ≠ 思路没用，`author_ic_claim` 列区分"直接复现" vs "改进尝试"。

### P3 — 池2 构建器 + 回测（因子定下来后）
- 单因子过关的因子选定后，才做规则筛选/合成的池2。
- 交付 7 个文件（见 §9）。
- 测 5/10/20 三种持仓期（领导要求）。

### 6/10 之后
- 降频思路（分钟因子→日频近似）+ 56 服务器分钟数据接入。**这部分用户要亲自参与设计，不要自动推进。**

---

## 7. features_daily 30 个重测候选（P1 用）

> 之前用"排除 vol/反转大类"的**错误标准**只筛了 14 个；现已纠正，把误排除的 vol/反转/动量类加回，共 30 个。**全部一视同仁测，不预判大类。**

**原 14（量价微观结构等，未被大类排除）**：
CCV_20d, info_discreteness_20d, CLV_20d, CVR_20d, drawdown_volume_ratio, tug_of_war_20d, shadow_asymmetry_20d, conditional_turnover, RPV_20d, ou_halflife_60d, stealth_score, amihud_asymmetry_20d, realized_skewness_20d, gap_survival_ratio

**加回的 16（之前被大类误排除）**：
- vol 类：realized_vol_20d, vol_ratio_5d_20d, realized_kurtosis_20d, turnover_volatility_60d, max_abs_return_10d
- 反转类：cum_return_5d, cum_return_10d, cum_return_20d, distance_from_high_20d, days_since_high, recent_high_20d
- 动量类：cum_intraday_ret_5d, cum_intraday_ret_10d, cum_intraday_ret_20d, overnight_return_ratio_20d, overnight_ret_surprise

> 这些名字需与 `features_daily.py` 实际 key 核对（接手时先 `print(features.keys())` 确认拼写）。

---

## 8. 外部因子库分类（P2 用）

- 原始 99 篇 .py 在用户本地因子库（公众号"量化拯救散户"复现）。
- 分类结果：`factor_classification_v2.csv`（列：date / original_title / **usable_now** / data_source / data_freq_text_hint / has_code / likely_factor_type / **author_ic_claim** / author_layer_claim / core_formula / ...）。
- `usable_now` 取值：
  - `yes`（20 个）：日频 + 有代码，直接可测
  - `yes_needs_impl`（3 个）：纯思路文，日频，需自己实现
  - `no_minute`（72 个）：需分钟数据，6/10 后
  - `review`（4 个）：数据源待人工核实
- **分类脚本曾误判**：把"数据在父类 `__init__` 加载、代码块只有 `cal_factor(idx)`、靠 `self.rtn.iloc[idx-N:idx]` 跨日切片"的日频因子误判为 unclear/minute。判断数据频率要看**整个文件**的 load 行为，不只代码块内的 `load_data`。`stock_bar_1day.parquet`=日频；`self.files[idx]` + `加载当日分钟数据`=分钟。

---

## 9. 池2 交付文件清单（v2 2026-09-03；v1 2026-07-08 已被取代；格式经领导"可后调"授权）

**v2（2026-09-03，引擎修正 + 复审后）** = {A4b, M_mean3_v2（cond+tvol+cum_return_20d mean 剔上半）, M_union3_v2（三 drop 并集之外）} × {纯净, +CVRv5（剔池内 CVR_20d 最高 1/5）} = 6 池2 + 共用池1。
- 仓库：`delivery/I11_candidate_pools_v2_20260903/`（tar.gz + README + _delivery_stats + summary + old_vs_new.txt + `export_delivery_pools_v2.py`）；results：`results/20260903_1214_delivery_pools_v2`。
- 公共库：`/mnt/big/base/public/FundamentalTL/量价因子/I11_candidate_pools_v2/`（按用户指令复制；v1 目录保留并放 SUPERSEDED 标注）。
- 池1 与 v1 逐字节相同（md5 6006780eb791fe6a7f66e3829cb23763）；6 个池2 全部更新。日均持仓：A4b 73/62（veto）、Mmean_v2 146/127、Munion_v2 51/47。
- 数字（新口径 DEV net 4 段 | NW）：A4b_CVRv5 3.06/6.99/8.43/10.33 | 3.47/3.77/3.95/1.96 为最强；全表见 README。

**v1（2026-07-08，已取代，下文为历史记录）**：

两层结构最终产出 = 3 构造 × {纯净 / +cmf veto} = **6 候选池2 + 1 共用池1**,`ticker/tradeDate/weight` 三列长表(领导 5/25 第9条 + 7/7 报告口径;ticker=去零整数、与 clc_ts_all_* 可 join)。全历史 2010-02-12 ~ 2026-03-27。

- `pool1_I11_screening.csv` — I11 初筛母池(3列:ticker / tradeDate / in_pool=1)
- `pool2_{Mmean,A4b,Munion}_{pure,cmfveto}.csv` — 6 候选精选池(3列:ticker / tradeDate / weight;weight=DEV 偏离约束目标权重、不归一)
- 交付落点:公共库 `/mnt/big/base/public/FundamentalTL/量价因子/I11_candidate_pools/`(+ README/_delivery_stats)
- 复现:`delivery/I11_candidate_pools_20260708/export_delivery_pools.py`(config-for-config 复现 phase3,24/24 自检 |d|0)

（注:旧"列名锁定"曾设想单一 `pool2_filtered` 4列含 in_pool、pool1 拆 signal/window;两层聚合定稿后演变为上述 6 候选 3 列。领导要 in_pool/window 变体可再加。）

---

## 10. 领导的关键指示（汇报/决策时遵守）

- **方法论**："先单因子过关，再去合成"——现在就是单因子阶段，**别急着做合成**。
- **滚动 IC 思路**：因子失效时自动降权（滚动 60/120 天 IC，低于阈值权重=0）——可作 P1/P3 的增强，不是必需。
- **分域思路**：科技抱团股先挪开，在非抱团股上用反转/低波，再把抱团股加回——领导想得最深的方向，但实现复杂，6/10 内不强求。
- **持仓期**：测 5/10/20 天。
- **涨跌停**：信号层保留，交易层处理，**不在池定义里剔**。
- 领导预期是"**半成品**"——足够强他直接用，不够强他叠加自己的因子。**不必追求单因子 Sharpe 3+**，A 股单因子真实 1-1.5 已经很好。

---

## 11. 给 Claude Code 的工作纪律

1. **每次跑长任务前先在本地（或小样本/单段）验证逻辑能跑通**，别直接全量跑——这个项目因为没本地验证白跑过好几次。
2. **结果一律进 `results/<时间戳>_<后缀>/` 子文件夹**，别堆根目录。
3. **改完代码先 `python -c "import ast; ast.parse(...)"` 语法检查**，关键逻辑用模拟数据离线测。
4. **简单优先**。这个项目反复因为"过度复杂化"踩坑——能用简单方案就别加复杂诊断。
5. **不预判因子大类好坏**（见 4.4），让数据说话。
6. **判断因子看 Calendar PnL（剔尾口径，NW Sharpe），不看多空 Sharpe**（见 4.3）。
7. **降频 / 分钟数据接入（6/10后）用户要亲自参与，不要自动推进。**
8. 涉及给领导的数，**用保守口径（NW Sharpe）+ 标注成本假设**，不报乐观裸数。

---

## 12. ClickHouse 高频数据库（56 服务器，6/10 后用）

> 本项目当前**不用**这个库，分钟/L2 数据接入是 6/10 之后的独立工作，且**用户要亲自参与**（见 §15 红线）。这里完整记录连接信息，备查。

**连接信息**：
- host: `192.168.2.56`，port: `9000`
- 用户：`DZhang`（密码 `92JD#zd.13@`）或 `YQLi`
- **47 是共享服务器**，DZhang / YQLi 是同事，跑高频查询前先看负载（见 §14）

**库表结构**（表名 = 日期，如 `20241213`）：
| 表 | 内容 |
|---|---|
| `MinData` | 分钟 K 线 |
| `TLOrderSH` / `TLOrderSZ` | 逐笔委托（沪/深）|
| `TLTradeSH` / `TLTradeSZ` | 逐笔成交（沪/深）|
| `TLMDSH` / `TLMDSZ` | 快照行情（沪/深）|

**注意**：
- L2 快照约 4800 笔/天（3 秒间隔）；A 股 tick 间隔是 Weibull 非 Poisson，建模用 Hawkes/ACD（幂律核），别假设泊松。
- 90 分钟午休要分段建模（AM/PM 分开）。
- 涨跌停按板块校准（主板 ±10%、创业/科创 ±20%、北交所 ±30%）。

**另一套数据（47 服务器，原始 MySQL，东财/同花顺另类数据）**：
- 东财另类库（alterDC）：`/mnt/HuaTZ_47/AlterDatabase/alterDC/`
- 同花顺概念数据：本地 `/mnt/sda2/HuaTZ/AlterDatabase/concept_data/`；挂载 `/mnt/HuaTZ_47/AlterDatabase/concept_data/`
- 同花顺原始 DB：`host=192.168.2.47, port=3306, user=Turing, pw=turing123, db=AlterDataIfind, charset=utf8mb4`
- 东财 alterDC 含：投资倾向（自选/持仓/访问/关注）、社区情绪（活跃度/新闻/公告/研报阅读）、人气（排名/趋势/飙升/热门/粉丝）、市场因子、股东数、就业数据
- 同花顺 concept_data 含：成分股映射、日/分钟行情、概念热度

---

## 13. Claude Code 首次连接 checklist

接手第一件事，按顺序确认环境（防止基于错误假设瞎跑）：

```bash
# 1. 确认在对的目录, 核心文件都在
cd /mnt/sda2/lichenchen/code/project_core
ls -la *.py
# 应看到: data_loader.py, features_daily.py, event_study.py,
#         pool_screening_v2.py, comprehensive_factor_diagnosis.py

# 2. 确认核心模块能 import (不报错说明依赖环境 OK)
python -c "from features_daily import calc_all_daily_features; print('features OK')"
python -c "from pool_screening_v2 import define_i11_signal; print('pool OK')"
python -c "from event_study import get_base_pool, PERIODS; print('event OK', PERIODS)"

# 3. ★核对 30 个候选因子的真实拼写 (文档 §7 的名字是凭记忆写的, 必须核对)
python -c "
from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
data = load_all_daily_data(start_date='2024-01-01', end_date='2024-03-01')
features = calc_all_daily_features(data)
print('实际特征 keys:')
for k in sorted(features.keys()): print(' ', k)
"
# 把输出和 §7 的 30 个候选名逐一对照, 不一致的以实际 keys 为准

# 4. 看 results 历史 (不要动这些, 是用户的实验记录)
ls -lt /mnt/sda2/lichenchen/results/ | head -10

# 5. 看 git 状态 + 是否有别人/自己的任务在跑
git -C /mnt/sda2/lichenchen/code/project_core status
ps -ef | grep python | grep -v grep
```

**只有以上全部正常，才开始执行用户的 prompt。** 任何一步异常先报告用户，不要自行"修复"环境。

---

## 14. 只读 vs 可写边界（远程 agent 必须守）

**绝对不能改（稳定地基，改了会连锁崩）**：
- `data_loader.py`
- `features_daily.py`
- `event_study.py`
- `pool_screening_v2.py`
- **`comprehensive_factor_diagnosis.py` 里的引擎口径**：`compute_calendar_pnl` 的 `exec_lag=1 / adjust=True` 默认值与 `shift(exec_lag+1)`、`adjust_factor` 的写法（is_open 掩码 + ffill）、`compute_forward_5d_excess` 的 `k=2..1+hold_days` —— 属口径，改动须经用户；`exec_lag=0 / adjust=False` 只许出现在自测与分解脚本里。动引擎必跑 `selftest_engine_fix.py`，应 5/5。

→ 如果某个任务**确实**需要改这四个里的东西，**先停下来报告用户**，说明为什么要改、改哪里，等用户确认。改之前**必须 git commit 当前状态 + 单独备份该文件**（`cp xxx.py xxx.py.bak_<日期>`）。

**可以改 / 新建**：
- `comprehensive_factor_diagnosis.py`（主诊断脚本）
- 新建的分析脚本、临时脚本

**绝对不能删**：
- `results/` 下任何历史子文件夹（用户的实验记录，删了不可逆）
- 任何 `.py` 稳定文件
- git 历史

**新建文件规范**：临时脚本放 `project_core/` 或 `/tmp/`，**结果一律进 `results/<时间戳>_<后缀>/`**。

---

## 15. 资源/并发纪律 + Git 工作流 + "不要自动推进"红线

### 资源/并发（47 是共享服务器）
- 47 上还有同事 DZhang / YQLi 在用。**跑任务前先 `ps -ef | grep python` 看负载**，别开一堆并发把内存吃爆。
- 长任务必须 `nohup python xxx.py > /dev/null 2>&1 &` 然后 `disown`，清理用 `pkill -f xxx`。
- **预计超过 30 分钟的任务，启动前先告诉用户**（说明预计时长 + 占用资源），等用户确认再跑。不要自主启动几小时的任务。

### Git 工作流（repo: `abnormal_comovement_strategy`，Private）
**推荐做法：每次有意义的代码改动后都 commit**（不是只在大节点）。理由：这个项目反复改脚本、踩坑、回退，频繁 commit 能随时回滚到任一可用版本。
```bash
# 改完 + 验证通过后:
git -C /mnt/sda2/lichenchen/code/project_core add <改的文件>
git -C /mnt/sda2/lichenchen/code/project_core commit -m "清晰描述改了什么、为什么"
# 跑回测前确保已 commit, 这样出问题能 git checkout 回退
```
commit message 要具体（"把 Calendar PnL 改成双向剔尾 + 三 Sharpe"），不要 "update"、"fix" 这种。

### 数据 / 交付入 git 政策（2026-07-08 起）
- **领导 2026-07-08 确认交付数据无隐私** → 交付产物(池1/池2 CSV、README、复现脚本)**可入 git**,放 `delivery/<交付名>_<日期>/`;大体量 CSV 用 gzip 归档(`.tar.gz`)进库,README/stats/脚本明文可浏览。
- **`results/` 仍不入 git**(防仓库臃肿;结果可由脚本复现)。`.gitignore` 已对 `delivery/` 开例外。

### 输出纪律：分析任务末尾附「可复制纯文本摘要」

**每次跑完分析任务，末尾必须附一段「可直接复制粘贴的纯文本摘要」**，供协作的网页版 Claude 阅读（它无法接收文件，只能读文本）。
- 紧凑、纯文本，含关键数值 + 标签/分类 + 结论 + 异常/存疑项；长度按任务内容合理控制。
- **不要把完整大矩阵或几百行原始数据全贴进去**——只放判断需要的关键信息。
- CSV / 图照常存到 `results/<时间戳>_<后缀>/` 备查，但**纯文本摘要是给网页版 Claude 复制用的主要交付物**。

### "不要自动推进" 红线清单（必须等用户 prompt，CC 不能自己决定）
1. **降频思路 / 分钟数据接入 / 56 服务器对接**——用户要亲自参与设计。
2. **删除任何文件**（results、py、git 历史）。
3. **改动 §14 的四个稳定地基文件**——先报告，等确认。
4. **启动预计 >30 分钟的任务**——先报告时长，等确认。
5. **任何要给领导看的数字/结论**——必须经用户过目，CC 不直接对接领导，也不在文档/输出里替用户下"可以交付"的结论。
6. **改动 I11 信号定义、池子构造规则、权重公式**（§3）——这些已与领导确认，改动前必须经用户。
7. **改动回测引擎口径**（§14 新增项：记账时点、复权、前向收益起点）。

**默认姿势**：拿不准就停下来问用户，而不是替用户做决定。用户的工作流是"和 Claude（网页）讨论策略 → 写 prompt 给 CC 执行"，所以 CC 收到的 prompt 应该是明确的执行指令；**指令没覆盖到的判断，回退给用户，不要自行外推。**
