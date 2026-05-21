# 时序事件驱动选股策略 — 核心代码

A股事件驱动量价策略：I11入场信号 + 观察池截面筛选 + 因子精简

工作区路径：`/mnt/sda2/lichenchen/code/project_core/`

---

## 📊 项目当前状态

| 维度 | 状态 |
|---|---|
| **当前baseline** | 4因子框架，跨4段平均Sharpe 2.45（17年16年正） |
| **诊断主要发现** | 4因子中只有ΔCMF是真正的alpha来源，其他3个是稀释项 |
| **初步最优精简** | 3因子drop_reversal，扣6bp成本后Sharpe **3.27** |
| **进一步探索** | 2因子/单因子组合扫描（还未跑） |
| **下一阶段方向** | 分钟数据接入 → 日内相似度聚类 → 真补涨因子v2 |

---

## 📁 文件清单

### 基础设施层

| 文件 | 作用 |
|---|---|
| `data_loader.py` | 日频数据加载（OHLCV+辅助字段，含缓存） |
| `features_daily.py` | 70个B1-B5特征计算库（隔夜跳空/量能/流动性/CMF等） |
| `engine.py` | 通用因子回测引擎（旧版备用） |

### I11入场信号层

| 文件 | 作用 |
|---|---|
| `event_study.py` | 18个入场信号 + event study主框架（含PERIODS定义） |
| `i11_final.py` | I11定稿版（P80） |
| `i11_calendar_pnl.py` | Calendar Time PnL诊断（揭示event vs calendar差异） |
| `i11_sensitivity.py` | I11参数敏感性分析 |
| `i11_cross_validation.py` | I11跨段交叉验证 |
| `i11_risk_adjusted.py` | I11风险调整评估 |

### 截面筛选层（核心策略）

| 文件 | 作用 |
|---|---|
| `pool_screening_v2.py` | **观察池4因子截面筛选 + P0诊断函数库** |

**当前默认配置**：4因子，Sharpe 2.45 baseline
- I11入场信号（CMF高+涨幅适中+当日未涨3条件AND）
- 观察池：最近5日内触发过的股票
- 硬约束：停牌/涨跌停/次新/低成交/50亿市值
- 4因子评分：反转 + Parkinson + 异常换手率 + ΔCMF
- 等权合成 → 行业约束 → Top 15

**消融开关**：`include_reversal/vol/abn_to/cmf_change` 用于leave-one-out

**P0诊断函数库**（新加）：
- `plot_pnl_curves`：累积PnL + 回撤双面板图
- `plot_rolling_sharpe`：滚动60日Sharpe图
- `compute_extended_stats`：Sortino / VaR / CVaR / 回撤天数 / 恢复天数
- `compute_holding_overlap`：持仓重叠率矩阵
- `compute_random_baseline`：池内随机选股基准（100次）
- `compute_turnover_and_costs`：换手率 + 扣交易成本Sharpe

### 因子诊断层

| 文件 | 作用 |
|---|---|
| `factor_ic_diagnosis.py` | 池内19个参数变种IC扫描（4段×19参数，方式B forward return） |
| `factor_marginal_diagnosis.py` | Leave-one-out边际贡献 + 5项P0诊断 |

### 工具层（新加）

| 文件 | 作用 |
|---|---|
| `export_factors_to_library.py` | 导出5个因子到公共因子库格式 |

---

## 🎯 关键运行命令

### 1. 跑当前baseline（4因子，Sharpe 2.45）

```bash
python pool_screening_v2.py --period all 2>&1 | tee /mnt/sda2/lichenchen/results/pool_v2_all.txt
```

### 2. 跑边际贡献诊断（含P0诊断，约1-1.5小时全4段）

```bash
nohup python factor_marginal_diagnosis.py --period all \
    > /mnt/sda2/lichenchen/results/factor_marginal_v3_all.txt 2>&1 &
disown
```

输出包括：
- 8张图（每段2张：PnL曲线 + 滚动Sharpe）
- 文本：边际贡献表 + 扩展统计 + 持仓重叠 + 换手成本 + 随机基准
- 跨段汇总表

### 3. 跑因子IC诊断（3-4小时全4段）

```bash
python factor_ic_diagnosis.py --period all 2>&1 | tee /mnt/sda2/lichenchen/results/factor_ic_all.txt
```

### 4. 导出因子到公共库

```bash
python export_factors_to_library.py
```

5个因子输出到 `/mnt/big/base/public/FundamentalTL/量价因子/`

---

## 📈 项目历史结论

### ✅ 已验证有效

1. **I11入场信号**：跨4段Event Study Sharpe 3.45，4/4段正
2. **观察池+截面筛选框架v2**：Calendar Sharpe从-1.15提升到+2.45
3. **5日观察窗口** > 3日
4. **50亿市值阈值**：风险控制贡献明确（2024-02崩盘回撤减半）
5. **选15只** > 20只（精选度高alpha集中）
6. **ΔCMF是策略的真正alpha引擎**：边际贡献+4.92 Sharpe，跨4段一致

### ❌ 已证明无效

1. **粗行业补涨因子**（中信一级30类）：跨段一致有害
2. **P0改动**（窗口缩短+涨跌停掩码+STR换手率+全4因子行业中性化）：Sharpe从2.51崩到0.27
3. **删ΔCMF**：Sharpe从+2.48崩到-2.29
4. **反转因子（在我们I11池+5日持有场景）**：边际贡献-1.31 Sharpe，跨4段稀释
5. **Parkinson波动率（同上）**：边际贡献-2.03 Sharpe
6. **异常换手率（同上）**：边际贡献-0.98 Sharpe

### 🔍 重要诊断教训

**IC高 ≠ Sharpe贡献高**。ΔCMF独立IC≈0但删除后Sharpe暴跌4.77，说明它在组合里是关键的"去相关器"。

**池子做过筛选后，传统因子逻辑被颠倒**：I11池里"反转/低波/低换手"的股票本质是"死水"（主力还没拉），反向选反而对。

**研报方案不能直接照搬**：P0方案来自全A月频研报，搬到我们小池+5日持有完全失效。

---

## 🚀 下一步计划

### P0（即将落地）

- [x] 4因子leave-one-out诊断（全4段）
- [x] P0诊断函数库（PnL曲线/滚动Sharpe/扩展统计/重叠率/随机基准/扣成本）
- [x] 因子导出脚本
- [ ] **2因子/单因子组合扫描**（4个新配置 × 4段，~1.5小时）
  - `cmf_only`（单ΔCMF）
  - `cmf+rev` / `cmf+vol` / `cmf+abn`（3个2因子组合）
- [ ] 基于完整数据决定最终精简方案

### P1（核心方向，领导指导）

- [ ] **接入分钟K线数据**（`/mnt/big/origin/public/MatrixDailyFix/`）
- [ ] **日内相似度聚类 → 隐含板块识别**
- [ ] **基于隐含板块的补涨因子v2**

### P2

- [ ] Barra风险因子接入（`/mnt/big/base/zhuhuihao/host_zhu/neutral/`）
- [ ] Phase 2组合回测（完整换手率/交易成本/仓位）
- [ ] 出场信号设计

---

## 📂 数据路径

| 数据 | 路径 | 当前状态 |
|---|---|---|
| 日线OHLCV | `/mnt/big/base/shibo/KLines_make/daily_temp3/` | ✅ 已用 |
| **分钟K** | `/mnt/big/origin/public/MatrixDailyFix/` | 🔄 下一步 |
| Barra因子 | `/mnt/big/base/zhuhuihao/host_zhu/neutral/` | ❌ 未用 |
| 停牌/ST/复权/行业 | `/mnt/big/base/zhuhuihao/alphagp_lv2_daily/*.csv` | ⚠️ 部分已用 |
| 数据缓存 | `/mnt/big/base/public/FundamentalTL/cache/` | ✅ 已用 |
| **公共因子库** | `/mnt/big/base/public/FundamentalTL/量价因子/` | 📤 已导出 |

## 📂 输出目录

| 类型 | 路径 |
|---|---|
| 文本回测结果 | `/mnt/sda2/lichenchen/results/*.txt` |
| 图表 | `/mnt/sda2/lichenchen/results/*.png` |
| 日志 | `/mnt/sda2/lichenchen/logs/` |
