# E5b —— 文档收口 + v1 标注取代 + 公共库交付（后者按用户指令门控）

用途：把引擎修正与复审的结果落进 47 的 `PROJECT_STATUS.md`（唯一入口文档），给 7/8 的 v1 交付目录加"已取代"标注，并在用户明确说"复制公共库"时把 v2 复制到公共库。纯文档与文件操作，不跑回测。前置：`E5a_REPORT.md`（commit `a55c77c`）。先读 `00_协议.md`。

**门控规则**：§2 A、B、C 三部分默认做；§2 D（公共库）与 §2 E（§12 连接信息）**只在用户给你的 prompt 里明确写了"做 D"/"做 E"时才做**，否则跳过并在 REPORT 写"未授权，未做"。

## 1. 起点确认
1. 47 上 `git log -1 --oneline` = `a55c77c`，`git status -sb` 首行 `## main...origin/main`，untracked 仍只有那 3 个。
2. `wc -l PROJECT_STATUS.md` ≈ 389（±5）；`grep -c '最后更新：2026-07-08' PROJECT_STATUS.md` = 1。
3. `delivery/I11_candidate_pools_20260708/` 与 `delivery/I11_candidate_pools_v2_20260903/` 都在。

## 2. 做什么

### A. `PROJECT_STATUS.md`（用带锚点断言的脚本改，每个锚点 `count==1`；改前 `cp PROJECT_STATUS.md /tmp/PROJECT_STATUS_before_E5b.md`）

**A1 头部**：`> 最后更新：2026-07-08` → `> 最后更新：2026-09-03`

**A2 §0 当前阶段**：把整行
`**当前阶段**：两层结构定稿·6 候选 2026-07-08 已交付(见 §9)（"单因子先过关，再谈规则筛选/合成"——这是领导明确要求的方法论，务必遵守）。`
换成
`**当前阶段**：**回测引擎修正 + 全候选库复审完成（2026-09-02/03）**，v2 六候选已产出（`delivery/I11_candidate_pools_v2_20260903/`，公共库交付按用户指令），见 §9。引擎两处修正与因子池三处调整见 §4.8–4.11；7/8 的 v1 六候选及其数字已被取代。当前因子池：合成池 = conditional_turnover + turnover_volatility_60d + cum_return_20d（决策层 mean 剔最差半）；规则池 = CVR_20d 窄否决（剔池内最高 1/5）。下一步：样本延长到 2026-09 做确证、T+1 可成交性、L2/概念数据。（"单因子先过关，再谈规则筛选/合成"——这是领导明确要求的方法论，务必遵守）。`

**A3 §2 表**：
- `comprehensive_factor_diagnosis.py` 那一行的状态格 `见 §5，最新版刚改完待跑` → `**引擎口径 2026-09-02 定稿（commit cb9fea2）**：`compute_calendar_pnl(..., exec_lag=1, adjust=True)`（持仓按信号日 T 索引、T+1 vwap 成交、`shift(exec_lag+1)`、后复权收益）、`compute_forward_5d_excess(..., adjust=True)`、`adjust_factor / adjusted_prices / vwap_daily_return`。`exec_lag=0 / adjust=False` = 旧口径，仅自测与分解用，禁止用于正式输出（§14）。§5 的旧数字已失效`
- 在该行之后插入 5 行：
  `| `selftest_engine_fix.py` | 引擎修正真数据自测 5 条（复权对账 / 除权计数 / 旧口径逐格回归 / 两视角恒等式 / 前视探测器） | **口径守卫·动引擎必跑，应 5/5** |`
  `| `e2_decomposition.py` | 六候选 × {旧/新时点} × {未/已复权} 四格分解 + phase3 24 锚点接线自检（`results/20260903_0935_E2_decomposition`） | 引擎修正证据 |`
  `| `e3_single_factor_rerun.py` | 35 因子 × 双向 × k2/k5 × 旧/新口径 单因子复审表，每段一进程（`results/20260903_1037_E3_single_factor`） | 复审证据 |`
  `| `e4_agg_review.py` | 聚合层复审：rev 席位 / 反转代表 / CVR 合成 vs 否决 / cmf 正向否决 + 双基准 + 8 因子相关矩阵（`results/20260903_1132_E4_agg_review`） | 复审证据·终判依据 |`
  `| `export_delivery_pools_v2.py` | v2 六候选交付导出（自检 E4 锚点 12/12 + 池1 md5 == 0708） | 活跃·交付工具（取代 v1 导出脚本） |`
- `i11_calendar_pnl.py` 那一行的状态格末尾追加：`。⚠️ 其记账时点从 T 日 vwap 起记（同旧 shift(1)），数字带半天前视，只作历史证据，勿再引用`
- `pool_screening_v2.py` 那一行的状态格 `稳定` → `稳定（地基）。⚠️ 其内 `compute_calendar_pnl` 的 v2 sleeve 路径持仓不 shift（整整早一天），第二次汇报的 +2.45 出自此，已被 DEV 链路取代，勿再引用`

**A4 §4 追加**（在 `### 4.7 其他工程坑` 小节末尾、`## 5.` 之前插入）：
```
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
```

**A5 §5 头部**：在 `## 5. `comprehensive_factor_diagnosis.py` 当前状态（主力脚本）` 标题下一行插入：
`> ⚠️ 2026-09-03：本节数字为 2026-05-29 旧口径（shift(1) + 未复权），已失效。单因子最新数字见 `results/20260903_1037_E3_single_factor/summary.txt`（新口径、DEV 剔尾、4 段）。`

**A6 §6 头部**：在 `## 6. 待办（按优先级）` 标题下一行插入：
`> 2026-09-03：本节是 5 月的待办，已被后续阶段覆盖；当前待办见 §0（延长样本确证 / T+1 可成交性 / L2·概念数据）。`

**A7 §9**：把标题行 `## 9. 池2 交付文件清单（2026-07-08 实际交付；格式经领导"可后调"授权）` 换成 `## 9. 池2 交付文件清单（v2 2026-09-03；v1 2026-07-08 已被取代；格式经领导"可后调"授权）`，并在该节正文最前面插入：
```
**v2（2026-09-03，引擎修正 + 复审后）** = {A4b, M_mean3_v2（cond+tvol+cum_return_20d mean 剔上半）, M_union3_v2（三 drop 并集之外）} × {纯净, +CVRv5（剔池内 CVR_20d 最高 1/5）} = 6 池2 + 共用池1。
- 仓库：`delivery/I11_candidate_pools_v2_20260903/`（tar.gz + README + _delivery_stats + summary + old_vs_new.txt + `export_delivery_pools_v2.py`）；results：`results/20260903_1214_delivery_pools_v2`。
- 公共库：`/mnt/big/base/public/FundamentalTL/量价因子/I11_candidate_pools_v2/`（按用户指令复制；v1 目录保留并放 SUPERSEDED 标注）。
- 池1 与 v1 逐字节相同（md5 6006780eb791fe6a7f66e3829cb23763）；6 个池2 全部更新。日均持仓：A4b 73/62（veto）、Mmean_v2 146/127、Munion_v2 51/47。
- 数字（新口径 DEV net 4 段 | NW）：A4b_CVRv5 3.06/6.99/8.43/10.33 | 3.47/3.77/3.95/1.96 为最强；全表见 README。

**v1（2026-07-08，已取代，下文为历史记录）**：
```

**A8 §14**：在"绝对不能改"列表的 `- `pool_screening_v2.py`` 之后追加一行：
`- **`comprehensive_factor_diagnosis.py` 里的引擎口径**：`compute_calendar_pnl` 的 `exec_lag=1 / adjust=True` 默认值与 `shift(exec_lag+1)`、`adjust_factor` 的写法（is_open 掩码 + ffill）、`compute_forward_5d_excess` 的 `k=2..1+hold_days` —— 属口径，改动须经用户；`exec_lag=0 / adjust=False` 只许出现在自测与分解脚本里。动引擎必跑 `selftest_engine_fix.py`，应 5/5。`

**A9 §15 红线清单**：在 `6. **改动 I11 信号定义、池子构造规则、权重公式**（§3）——这些已与领导确认，改动前必须经用户。` 之后追加：
`7. **改动回测引擎口径**（§14 新增项：记账时点、复权、前向收益起点）。`

改完：`git diff --stat` 只应有 `PROJECT_STATUS.md`；`grep -c '4\.8 Calendar' PROJECT_STATUS.md` = 1；`grep -cE '192\.168\.|user=|pw='` 的数量与改前**相同**（本部分不动 §12）。

### B. v1 交付目录标注
新建 `delivery/I11_candidate_pools_20260708/SUPERSEDED.md`：
```
# 已被取代（2026-09-03）
本目录（2026-07-08 交付 v1）的 6 个池2 基于修正前的回测引擎（记账时点半天前视 + 收益未复权）与旧因子池（reversal_skip1 / cmf_change_high 否决）。
取代者：`../I11_candidate_pools_v2_20260903/`（引擎修正 + 复审后 v2）。池1 两版逐字节相同；池2 请改用 v2。旧口径与新口径数字对照见 v2 目录 `old_vs_new.txt`。
```

### C. commit + push + WORKLOG
`git add PROJECT_STATUS.md delivery/I11_candidate_pools_20260708/SUPERSEDED.md && git commit -m "docs(E5b): PROJECT_STATUS 收口引擎修正与复审(§0/§2/§4.8-4.11/§5/§6/§9/§14/§15) + v1 交付目录 SUPERSEDED 标注" && git push origin main`。WORKLOG 一条（远端 + 本地 `_tmp_WORKLOG.md`）：改了哪些节 / commit / D、E 是否执行 / 红线。

### D. 公共库交付（**仅用户 prompt 明确写"做 D"**）
```bash
SRC=/mnt/sda2/lichenchen/results/20260903_1214_delivery_pools_v2
DST="/mnt/big/base/public/FundamentalTL/量价因子/I11_candidate_pools_v2"
mkdir -p "$DST" && cp $SRC/pool1_I11_screening.csv $SRC/pool2_*.csv $SRC/README.md $SRC/_delivery_stats.csv $SRC/old_vs_new.txt "$DST"/
cp delivery/I11_candidate_pools_20260708/SUPERSEDED.md "/mnt/big/base/public/FundamentalTL/量价因子/I11_candidate_pools/SUPERSEDED.md"
ls -la "$DST"; md5sum "$DST"/pool1_I11_screening.csv     # 应为 6006780eb791fe6a7f66e3829cb23763
```
不删、不覆盖 v1 目录里的任何文件。REPORT 列出目标目录清单与 md5。

### E. §12 连接信息脱敏（**仅用户 prompt 明确写"做 E"**）
把 §12 里含账号 / 口令 / 主机地址端口的行替换为一行 `连接信息见用户本地私有文件，不入库（2026-09-03 脱敏）`，其余表结构说明保留；单独 commit `docs: §12 连接信息脱敏` 并 push。改后 `grep -cE '192\.168\.|user=|pw='` 应为 0。**历史 commit 里的明文不在本步处理范围**（清历史属用户操作）。

## 3. 验收
- A：9 个锚点全部 `count==1`；改后 `python -c "open('PROJECT_STATUS.md',encoding='utf-8').read()"` 可读；`git diff --stat` 只此一文件。
- B：文件存在，3 行。
- C：push 后 `## main...origin/main`。
- D / E：只在授权时验收，按各自末行检查。

## 4. 交回
`exec_briefs/E5b_REPORT.md`：起点确认；A1–A9 逐项落点行号；B / C 结果；D / E 做没做（未授权就写"未授权，未做"）；commit 哈希、push；纯文本摘要 ≤10 行；BLOCKERS。

## 5. 禁区
四个地基文件不动；不改任何 `.py`；不跑回测；不改 v1 交付目录已有文件（只新增 SUPERSEDED.md）；未授权不碰公共库、不动 §12；不删 results；文档不出现新的登录信息与主机地址。凡遇"必须改上述任何一项才能继续" → 停，写 BLOCKERS，交回。
