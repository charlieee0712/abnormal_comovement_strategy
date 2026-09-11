# E1 —— 引擎修正：Calendar 记账时点 exec_lag=1 + 收益后复权 + 真数据自测

用途：把 `comprehensive_factor_diagnosis.py` 的两处收益口径缺陷一次修掉，参数化旧口径供对照，加一套真数据自测把时点和复权焊死。**只改这一个既有文件 + 新建一个自测脚本。** 前置：`E0_REPORT.md` 存在且 G0-1、G0-2 都 PASS。先读 `00_协议.md`。

## 0. 背景（读懂再动手）

两处缺陷都在 `comprehensive_factor_diagnosis.py`（可写文件），所有 phase 脚本和交付脚本都直接 `import comprehensive_factor_diagnosis as C` 调它的引擎：

| 缺陷 | 现状 | 修成 |
|---|---|---|
| 记账时点 | `compute_calendar_pnl` 里 `daily_ret = vwap_t/vwap_{t-1} - 1` 是回看日收益，持仓只 `actual_holding.shift(1)` → T 收盘算出的信号从 **T 日 vwap** 起记收益。收盘后买不到 T 日 vwap，是半天前视；且 T 日池已剔当日停牌/低成交，收益被选择污染 | 持仓 `shift(exec_lag + 1)`，默认 `exec_lag=1` = T+1 vwap 成交。每笔 T+1 vwap 进、T+1+hold_days vwap 出，与视角① `compute_forward_5d_excess` 的 `k in range(2, 2+hold_days)`（= vwap_{T+1} → vwap_{T+1+hold_days}）逐笔同起点 |
| 收益未复权 | 两个函数都用 daily_temp3 原始 `vwap` 算收益。除权除息日全是假跌（factor_library 实测 2010-2026 共 34,353 个除权日，中位 −1.8%，20% 的事件 <−20%，全市场等权年化被拖 −3%~−13%） | 收益一律用后复权 vwap。复权因子由 `lclose`（交易所口径前收盘价，与 `change_pct` 逐格一致）推得，**不用 `adj_factor` 列**（首次除权前 NaN，约 3.5% 格子） |

- 视角① 的时点本来就是对的（k=2..6），只需补复权。**因子值本身不改**（同一日截面内除权不影响排序；特征/信号侧改复权价 = 改信号定义，用户已决定推迟）。
- 参照物：factor_library（同源 copy）已按同样思路修完，commit `40b4719`（时点）与 `a654a12`（复权）。那边自测在合成数据上：旧口径下"只含 T 日盘中信息"的探测器年化 +108%、NW +74；新口径 −0.3%。真数据上旧口径会更夸张，这是 T5 阈值的量级依据。
- **改完默认值后，phase3 / export 脚本的锚点自检会 FAIL —— 这是设计内的**（锚点是旧口径数字）。E1 **不跑**那些脚本；旧口径锚点复现由本步 T3 的逐格回归 + E2 的分解表接管。
- 停牌日语义不变：`vwap` 在停牌日为 NaN（已核实：NaN 仅出现在 isOpen=0，从不为 0），复牌日 `vwap_t/vwap_{t-1}` 因 vwap_{t-1} 为 NaN 而记 NaN、贡献 0。本步不动这一点，只记录。
- 数据事实（2026-09-02 在 2015+2024 两年原始 csv 上核过，190 万行）：停牌行（isOpen=0，共 98,680 行）的 `closePrice` / `preClosePrice` **全是正数搬运值、不是 NaN 也不是 0**；交易行无 0 无 NaN；`chgPct` = close/preClose−1 最大偏差 5e-5（含复牌日）；`adj_factor` 列缺失 3.5%。所以复权因子必须用 `is_open` 掩掉停牌行、prev 用 ffill 跨停牌（2a 的写法），否则停牌期间的除权可能重复计。

## 1. 起点确认（任一不符 → 停，写 BLOCKERS）
1. `exec_briefs/E0_REPORT.md` 存在，G0-1 与 G0-2 均 PASS。
2. 47 上 `git log -1 --oneline` = `5623e59`；`git status --short` 仍只有 E0 说的 3 个 untracked；tracked 零改动。
3. `python -c "import comprehensive_factor_diagnosis as C; print(C.compute_calendar_pnl.__defaults__, C.compute_forward_5d_excess.__defaults__)"` 输出 `(5, 6) (5,)`（改前）。
4. 留一份改前副本供 T3 粘贴：`git show 5623e59:comprehensive_factor_diagnosis.py > /tmp/cfd_5623e59.py`。
5. 缓存 `/mnt/sda2/lichenchen/data/cache/daily_kline_20100101_20260327.parquet` 在（自测按全窗口一次性加载，靠它）。

## 2. 改 `comprehensive_factor_diagnosis.py`（唯一改动的既有文件）

**要改的函数整段读完再改。** 改动只有 2a–2c 三处，其余一行不动（`assign_weights` / `calendar_pnl_metrics` / `_sharpe_newey_west` / `_sharpe_weekly` / `main()` / 因子注册表 / 双向剔尾扫描 全部不碰）。

### 2a 新增三个 helper
放在 `# Forward return 计算 (Event Study 用)` 那段分隔注释**之前**：

```python
# ============================================================
# 后复权 + VWAP 日收益 (2026-09 E1 引擎修正; 参照 factor_library forward_returns.adjust_factor, commit a654a12)
# ============================================================

def adjust_factor(data):
    """后复权累计因子 A_t = Π_{s≤t} prev_s / lclose_s, prev_s = s 日之前最近一个有效收盘价.
    lclose 是交易所口径的前收盘价(已含除权除息调整, 与 change_pct 逐格一致), 不用 adj_factor 列(首次除权前 NaN, 约 3.5% 格子).
    只在交易日(is_open==1)算比值, 停牌行记 1: 数据源在停牌行把 close/lclose 填成搬运值(正数, 非 NaN), 不能当真实成交价用;
    prev 取上一交易日收盘(ffill 跨停牌), 因此停牌期间发生的除权在复牌日被一次性捕捉、不重复计.
    只用于算收益(跨日比价); 复权价 = 原始价 × A_t. 同一日截面内的因子值不受影响.
    与 factor_library 版本的差别: 加 is_open 掩码 + prev 用 ffill 跨停牌(那边 prev=close.shift(1) 且不掩停牌行, 依赖数据源对停牌行的填法).
    """
    is_open = data['is_open'] == 1
    close = data['close'].where(is_open & (data['close'] > 0))
    lclose = data['lclose'].where(is_open & (data['lclose'] > 0))
    prev = close.ffill().shift(1)
    ok = close.notna() & prev.notna() & lclose.notna()
    ratio = (prev / lclose).where(ok).fillna(1.0)
    return ratio.cumprod()


def adjusted_prices(data, keys=('close', 'vwap')):
    """{key: 后复权价}, 见 adjust_factor."""
    a = adjust_factor(data)
    return {k: data[k] * a for k in keys}


def vwap_daily_return(data, adjust=True):
    """VWAP 回看日收益 vwap_t / vwap_{t-1} - 1.
    adjust=True: 后复权 vwap (正式口径). adjust=False: 原始 vwap = 2026-09 之前的旧写法, 仅供自测/分解对照, 禁止用于正式输出.
    """
    vwap = adjusted_prices(data, ('vwap',))['vwap'] if adjust else data['vwap']
    return (vwap / vwap.shift(1) - 1).replace([np.inf, -np.inf], np.nan)
```

### 2b `compute_forward_5d_excess`
- 签名 → `def compute_forward_5d_excess(data, base_pool, hold_days=5, adjust=True):`
- 把 `vwap_daily_ret = (vwap / vwap.shift(1) - 1).replace([np.inf, -np.inf], np.nan)` 换成 `vwap_daily_ret = vwap_daily_return(data, adjust)`。`vwap = data['vwap']` 保留（ref_idx / ref_col 仍从它取）。
- docstring 追加两行：「时点: k=2..1+hold_days → vwap_{T+1} 买入、vwap_{T+1+hold_days} 卖出 (与 Calendar exec_lag=1 同起点)。adjust=True 用后复权 vwap (2026-09 E1 起); adjust=False 仅供对照。」
- 其余（`for k in range(2, 2 + hold_days)` 等）一字不动。

### 2c `compute_calendar_pnl`
- 签名 → `def compute_calendar_pnl(weights, data, base_pool, hold_days=5, cost_bp_bilateral=6, exec_lag=1, adjust=True):`
- `daily_ret = (vwap / vwap.shift(1) - 1).replace(...)` → `daily_ret = vwap_daily_return(data, adjust)`。`vwap = data['vwap']` 保留（对齐用）。
- `actual_holding_t1 = actual_holding.shift(1)` → `actual_holding_t1 = actual_holding.shift(exec_lag + 1)`；把那行上方的注释改为：`# 持仓按信号日 T 索引; exec_lag=1 = T+1 vwap 成交; daily_ret 是回看日收益, 故 shift(exec_lag+1)=2`。
- 返回 dict **保留全部现有键名**（phase / export 脚本消费 `net_excess_daily` / `gross_excess_daily` / `turnover_annual`），追加四个键：
  ```python
  'port_daily': portfolio_daily_ret,   # 组合自身日收益(未减基准), 自测恒等式用
  'bench_daily': bm_daily,             # 基准日收益
  'exec_lag': exec_lag, 'adjust': adjust,
  ```
- docstring 换成：
  ```
  Calendar PnL: hold_days 日持有期, 持仓累积 (每天换 1/hold_days).
  口径 (2026-09 E1 定稿):
    - weights 一律按【信号日 T】索引, 调用方不预先 shift.
    - exec_lag=1: T 收盘出信号, T+1 vwap 成交. daily_ret 是回看日收益 (vwap_t/vwap_{t-1}-1),
      故持仓 shift(exec_lag+1)=2. 每笔 T+1 vwap 进、T+1+hold_days vwap 出,
      与 compute_forward_5d_excess (k=2..1+hold_days) 逐笔同起点 (selftest_engine_fix T4 恒等式保证).
    - adjust=True: 收益用后复权 vwap (adjust_factor), 除权除息日不再记假跌.
    - exec_lag=0 / adjust=False = 2026-09 之前的旧写法 (T 日 vwap 起记 + 未复权),
      仅供自测复现与 E2 分解对照, 禁止用于任何正式输出.
  每日 PnL = sum(实际持仓权重 × 当日 daily return) - 当日基准 daily return × 总仓位.
  ```

### 2d 不动的清单（别顺手修）
- `monotonicity_diag.py` / `factor_ic_diagnosis.py` / `full_a_single_factor.py` 各自那份 `compute_forward_5d_excess` 副本：E3 处理。
- `i11_calendar_pnl.py`、`pool_screening_v2.compute_calendar_pnl`（地基）：历史脚本，E5 只做文档标注。
- `delivery/.../export_delivery_pools.py`、本地 `_remote_tmp/` 各 phase 脚本：不改、不跑。
- 四个地基文件。

### 2e 改完立刻做
```bash
python -c "import ast; ast.parse(open('comprehensive_factor_diagnosis.py').read()); print('syntax OK')"
python -c "import comprehensive_factor_diagnosis as C; print(C.compute_calendar_pnl.__defaults__, C.compute_forward_5d_excess.__defaults__)"
# 期望: (5, 6, 1, True) (5, True)
git diff --stat            # 只应有 comprehensive_factor_diagnosis.py 一个文件
```

## 3. 新建 `selftest_engine_fix.py`（project_core 根目录，import-only，只读地基）

真数据、全窗口（2010-01-01 ~ 2026-03-27，命中缓存），池 = `event_study.get_base_pool(data)`（既当组合域也当基准）。五条硬断言 + 一条软检查 + 两行只报告。**代码骨架如下：允许修语法/对齐类小错，不得改断言与阈值；两份 legacy 函数体必须从 `/tmp/cfd_5623e59.py` 逐字粘贴。**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest_engine_fix.py — E1 引擎修正自测 (真数据, import-only, 只读地基 4 文件)
T1 复权因子对账: 后复权 close 日收益 == change_pct (交易日, 含复牌日), max|diff| < 1e-4
T2 除权事件计数: 事件数 > 20000; 报告中位假跌 / <-20% 占比 / 最小值
T3 旧口径回归: (exec_lag=0, adjust=False) 与 5623e59 版函数逐格相等 (calendar 4 序列 × 2 组权重 + forward), |d| <= 1e-15 且 NaN 位置相同
T4 两视角焊死: hold=1 池等权无成本, Calendar 有效仓位口径超额 .shift(-2) == compute_forward_5d_excess(hold=1) 池内均值/1e4, max|diff| < 1e-10, n > 3000
T5 前视探测器: S = close/vwap-1 (只含 T 日盘中信息), 池内 keep-HIGH 上半区等权, hold=5 无成本:
   旧口径 (exec_lag=0) NW > 5 且 年化 > +10%; 新口径年化比旧口径低 >= 5pp. 软检查 |新口径年化| < 2% (WARN 不算失败)
附: 池等权 vs 同池基准 在 exec_lag=0/1 下的年化与 NW, 只报告
"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import comprehensive_factor_diagnosis as C
from data_loader import load_all_daily_data
from event_study import get_base_pool

OUT = C.make_output_dir('engine_fix_selftest'); C.setup_dual_logging(OUT); print('[out]', OUT, flush=True)
results = []
def check(name, ok, detail):
    results.append((name, bool(ok))); print('[%s %s] %s' % (name, 'PASS' if ok else 'FAIL', detail), flush=True)

# ---------- legacy copies: 从 /tmp/cfd_5623e59.py 逐字粘贴, 只改函数名 ----------
def _legacy_forward(data, base_pool, hold_days=5):
    ...  # = 5623e59 版 compute_forward_5d_excess 函数体
def _legacy_calendar(weights, data, base_pool, hold_days=5, cost_bp_bilateral=6):
    ...  # = 5623e59 版 compute_calendar_pnl 函数体
# ------------------------------------------------------------------------------

data = load_all_daily_data(start_date='20100101', end_date='20260327')
for k in ('close', 'lclose', 'vwap', 'is_open', 'change_pct'):
    assert k in data, 'data 缺字段 %s -> BLOCKER' % k
close, lclose, vwap = data['close'], data['lclose'], data['vwap']
pool = get_base_pool(data).reindex(index=vwap.index, columns=vwap.columns).fillna(0.0)
print('days', len(vwap.index), 'stocks', vwap.shape[1], 'range', vwap.index[0].date(), vwap.index[-1].date(), flush=True)

# ---------- T1 ----------
is_open = data['is_open'] == 1
close_v = close.where(is_open & (close > 0))          # 交易日收盘价; 停牌行(数据源填搬运值)置 NaN
lclose_v = lclose.where(is_open & (lclose > 0))
A = C.adjust_factor(data)
adj_close = close_v * A
ret_adj = adj_close / adj_close.ffill().shift(1) - 1   # 跨停牌: 复牌日对上一交易日
m = is_open & close_v.notna() & data['change_pct'].notna() & ret_adj.notna() & np.isfinite(ret_adj)
diff = (ret_adj - data['change_pct']).where(m)
mx = float(np.nanmax(np.abs(diff.values))); nbad = int((diff.abs() > 1e-4).sum().sum()); ncell = int(m.sum().sum())
check('T1', mx < 1e-4, '后复权 close 日收益 vs change_pct: cells=%d max|diff|=%.2e n(|diff|>1e-4)=%d' % (ncell, mx, nbad))

# ---------- T2 ----------
prev = close_v.ffill().shift(1)
ok = close_v.notna() & prev.notna() & lclose_v.notna()
ratio = (prev / lclose_v).where(ok)
ev = ratio.notna() & ((ratio - 1).abs() > 1e-6)
drop = (lclose_v / prev - 1).where(ev).stack()
n_ev = int(ev.sum().sum())
check('T2', n_ev > 20000, '除权事件 n=%d 中位假跌=%.2f%% 占比<-20%%=%.1f%% 最小=%.1f%%'
      % (n_ev, drop.median() * 100, (drop < -0.2).mean() * 100, drop.min() * 100))

# ---------- T3 ----------
def _same(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    if not np.array_equal(np.isnan(a), np.isnan(b)):
        return False, np.inf
    d = float(np.nanmax(np.abs(a - b))) if a.size else 0.0
    return d <= 1e-15, d
w_ew = pool.div(pool.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
rng = np.random.RandomState(0)
w_rand = pool * rng.rand(*pool.shape)
w_rand = w_rand.div(w_rand.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
t3_ok, t3_detail = True, []
for wname, w in (('ew', w_ew), ('rand', w_rand)):
    new = C.compute_calendar_pnl(w, data, pool, hold_days=5, cost_bp_bilateral=6, exec_lag=0, adjust=False)
    old = _legacy_calendar(w, data, pool, hold_days=5, cost_bp_bilateral=6)
    for key in ('gross_excess_daily', 'net_excess_daily', 'daily_position', 'daily_turnover'):
        okk, d = _same(new[key].values, old[key].values)
        t3_ok &= okk; t3_detail.append('%s/%s d=%.1e' % (wname, key, d))
okk, d = _same(C.compute_forward_5d_excess(data, pool, hold_days=5, adjust=False).values,
               _legacy_forward(data, pool, hold_days=5).values)
t3_ok &= okk; t3_detail.append('forward d=%.1e' % d)
check('T3', t3_ok, '旧口径逐格回归: ' + '; '.join(t3_detail))
del new, old

# ---------- T4 ----------
r = C.vwap_daily_return(data, adjust=True)
pr = C.compute_calendar_pnl(w_ew, data, pool, hold_days=1, cost_bp_bilateral=0)   # 默认 exec_lag=1, adjust=True
ah = w_ew.shift(2)
pos_eff = ah.where(r.notna()).sum(axis=1)
lhs = (pr['port_daily'] / pos_eff.replace(0, np.nan) - pr['bench_daily']).shift(-2)
fwd1 = C.compute_forward_5d_excess(data, pool, hold_days=1)                       # 默认 adjust=True, 单位 bp
rhs = fwd1.where(pool == 1).mean(axis=1) / 1e4
both = pd.concat([lhs.rename('lhs'), rhs.rename('rhs')], axis=1).dropna()
err = float((both.lhs - both.rhs).abs().max())
check('T4', (len(both) > 3000) and (err < 1e-10), '两视角焊死: n=%d max|diff|=%.1e' % (len(both), err))
del fwd1, pr

# ---------- T5 ----------
S = (close / vwap - 1).where(pool == 1)
keep = ((S.rank(axis=1, pct=True) > 0.5) & (pool == 1)).astype(float)
w_S = keep.div(keep.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
m_old = C.calendar_pnl_metrics(C.compute_calendar_pnl(w_S, data, pool, hold_days=5, cost_bp_bilateral=0, exec_lag=0, adjust=True)['gross_excess_daily'])
m_new = C.calendar_pnl_metrics(C.compute_calendar_pnl(w_S, data, pool, hold_days=5, cost_bp_bilateral=0)['gross_excess_daily'])
ao, nwo, an, nwn = m_old['annual_ret'], m_old['sharpe_nw'], m_new['annual_ret'], m_new['sharpe_nw']
hard = (nwo > 5) and (ao > 0.10) and ((ao - an) > 0.05)
check('T5', hard, '前视探测器 S=close/vwap-1 keep-HIGH: 旧口径 ann=%+.1f%% NW=%+.2f | 新口径 ann=%+.1f%% NW=%+.2f | 软检查 |新口径ann|<2%%: %s'
      % (ao * 100, nwo, an * 100, nwn, 'PASS' if abs(an) < 0.02 else 'WARN'))

# ---------- 附: 池等权自比 (只报告) ----------
for lag in (0, 1):
    mm = C.calendar_pnl_metrics(C.compute_calendar_pnl(w_ew, data, pool, hold_days=5, cost_bp_bilateral=0, exec_lag=lag, adjust=True)['gross_excess_daily'])
    print('[INFO] 池等权 vs 同池基准 exec_lag=%d: ann=%+.2f%% NW=%+.2f' % (lag, mm['annual_ret'] * 100, mm['sharpe_nw']), flush=True)

npass = sum(ok for _, ok in results)
print('[SELFTEST] %d/%d PASS' % (npass, len(results)), flush=True)
sys.exit(0 if npass == len(results) else 1)
```

跑法（预计 5-10 分钟；加载缓存 1-2 分钟，其余是全矩阵运算）：
```bash
cd /mnt/sda2/lichenchen/code/project_core
nohup taskset -c 96-191,288-383 python -u selftest_engine_fix.py > /tmp/E1_selftest.log 2>&1 &
disown
```
结果目录由脚本打印（`results/<ts>_engine_fix_selftest/log.txt`）。

## 4. 验收
- 日志末行 `[SELFTEST] 5/5 PASS`。T3 必须 `d=0.0e+00` 全部（允许 ≤1e-15）；T4 `max|diff| < 1e-10` 且 n>3000；T5 三个硬条件；T1 `max|diff| < 1e-4`；T2 n>20000。
- T5 软检查 WARN 不算失败，但把新口径的 ann / NW 原样写进 REPORT（E2 要用）。两行 `[INFO]` 也写进 REPORT。
- 任一硬断言 FAIL → **不 commit**，REPORT 写 BLOCKERS（现象 + 数字 + 你认为的原因 + 建议），停。**不调阈值、不改判据。** 常见可疑点：T1 不过 → 先看 `change_pct` 单位（应为小数）与复牌日；T3 不过 → 新代码路径在 adjust=False 时的表达式是否与旧的逐字相同；T4 不过 → `port_daily` 是否用的 `actual_holding_t1`、pool 与 vwap 的 index/columns 是否对齐。
- 5/5 PASS → commit（**只加这两个文件**）：
  ```bash
  git add comprehensive_factor_diagnosis.py selftest_engine_fix.py
  git commit -m "E1 引擎修正: Calendar PnL 记账时点 exec_lag=1 (T 收盘信号, T+1 vwap 成交, 与 compute_forward_5d_excess k=2..6 同起点) + 收益改后复权 (adjust_factor, lclose 法, 停牌跨除权一次捕捉) + selftest_engine_fix 5/5; 旧口径 (exec_lag=0, adjust=False) 仅自测/分解用"
  git log -1 --oneline
  ```
  **不 push**（仓库当前 PUBLIC，见 `00_协议.md` 第 6 条），REPORT 注明"未 push"。

## 5. 交回
- `exec_briefs/E1_REPORT.md`（结构见 `00_协议.md`）：起点确认 5 项；改动清单（2a/2b/2c 各自落在哪些行、`git diff --stat`）；T1–T5 逐条 PASS/FAIL 与日志原句；两行 `[INFO]`；results 目录名 + `/tmp/E1_selftest.log`；commit 哈希；纯文本摘要 ≤15 行；BLOCKERS。
- WORKLOG 一条（远端 + 本地 `_tmp_WORKLOG.md` 同文）：改了什么（两函数 + 三 helper + 新自测文件）/ 自测 5/5 与关键实得数字（T2 事件数与中位假跌、T4 max|diff|、T5 新旧口径 ann/NW）/ results 目录 / commit / 红线（地基未动、phase 与交付脚本未动未跑、未 push）/ 客观结论一句 / 状态：E2 待规划 session 出 brief。

## 6. E2 预告（本步不做）
E2 会基于 export 脚本的 config-for-config 逻辑：权重算一次，引擎调四次（{exec_lag 0/1} × {adjust False/True}），产出六候选 + A5 + cond solo + I11 池等权的分解表；其中 (0, False) 组合必须逐格复现 phase3 的 24 个锚点，那才是 phase 链路的接线自检。所以 E1 不必、也不要去跑 phase3 / export 脚本。

## 7. 禁区
四个地基文件一行不动；不改不跑 phase / export 脚本；不改 `main()` 与双向剔尾扫描；不调自测阈值；`exec_lag=0` / `adjust=False` 只许出现在自测与 E2 分解里；不删 results；不 push；不改 PROJECT_STATUS（E5 统一改）；结果数字不外发；文档与日志里不出现登录信息与主机地址。凡遇"必须改上述任何一项才能继续" → 停，写 BLOCKERS，交回。
