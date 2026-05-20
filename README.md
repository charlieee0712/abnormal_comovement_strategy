# 时序事件驱动选股策略 — 核心代码

恢复路径：原服务器 `/mnt/nvme/2020Starbit/abormal_movement_stock/` 下的代码丢失。
新工作区：`/mnt/sda2/lichenchen/code/`

## 文件清单

### 基础设施层

| 文件 | 作用 | 上游/下游 |
|---|---|---|
| `data_loader.py` | 日频数据加载（OHLCV+辅助字段，含缓存机制） | 所有脚本入口 |
| `features_daily.py` | 70个B1-B5特征计算库（隔夜跳空、量能、流动性、CMF等） | 所有策略脚本依赖 |
| `engine.py` | 通用因子回测引擎（旧版，目前不用） | — |

### I11入场信号层

| 文件 | 作用 | 关键产出 |
|---|---|---|
| `event_study.py` | I11/I13等多个入场信号的event study框架 | 18个候选信号的+T1~T5表现 |
| `i11_sensitivity.py` | I11灵敏度分析（12种变种参数） | 确认I11在各阈值下都稳定 |
| `i11_cross_validation.py` | I11跨段交叉验证（7变种） | 跨4段稳定性验证 |
| `i11_risk_adjusted.py` | I11风险调整评估（Sharpe/Calmar/最大回撤） | 风险维度补充评估 |
| `i11_final.py` | I11最终定稿（P80版本） | 4段平均+21.5bp, Sharpe 3.45 |
| `i11_calendar_pnl.py` | Calendar Time PnL诊断（揭示event vs calendar的差异） | 揭示baseline Sharpe -1.15 |

### 截面筛选层（核心策略）

| 文件 | 作用 | 关键产出 |
|---|---|---|
| `pool_screening_v2.py` | **观察池4因子截面筛选定稿版** | **跨4段Sharpe 2.45, 17年16年正** |

`pool_screening_v2.py` 包含：
- I11入场信号定义（P80）
- 观察池构建（最近5天内触发）
- 硬约束（停牌/涨跌停/次新/低成交/50亿市值）
- 4因子评分：反转/Parkinson/异常换手率/ΔCMF
- 行业约束Top15贪心选择
- Calendar Time PnL评估

**默认配置**：`('v2_obs5_sel15_nolag', 5, 5e9, 15, False, 3)` - 这是Sharpe 2.45的最优配置

**实验开关**：`include_reversal/vol/abn_to/cmf_change` 四个因子单独开关，用于leave-one-out诊断

### 因子诊断层

| 文件 | 作用 | 用途 |
|---|---|---|
| `factor_ic_diagnosis.py` | 池内19个参数变种的IC扫描（4段×19参数） | 探索各因子参数最优窗口 |
| `factor_marginal_diagnosis.py` | 4因子相关性矩阵 + Leave-one-out边际贡献回测 | 真正判断每个因子的实际价值 |

## 关键运行命令

### 1. 跑当前baseline (Sharpe 2.45)
```bash
python pool_screening_v2.py --period all 2>&1 | tee pool_v2_all.txt
```

### 2. 跑因子IC诊断 (3-4小时)
```bash
python factor_ic_diagnosis.py --period all 2>&1 | tee factor_ic_all.txt
```

### 3. 跑边际贡献诊断 (~50分钟, 2024-2026段)
```bash
python factor_marginal_diagnosis.py --period 2024-2026 2>&1 | tee factor_marginal_2426.txt
```

## 重要项目历史结论

### ✅ 已验证有效
1. **I11入场信号**：跨4段Event Study Sharpe 3.45，4/4段正
2. **4因子截面筛选**：Calendar Time Sharpe从-1.15提升到+2.45
3. **5日观察窗口** 优于3日
4. **50亿市值阈值** 不显著影响Sharpe但显著减少尾部风险（2024年2月崩盘）
5. **选15只** 优于20只（精选度高alpha集中）

### ❌ 已证明无效
1. **粗行业补涨因子**（中信一级30类）：跨段一致有害
2. **P0改动**（窗口缩短+涨跌停掩码+STR换手率+全4因子行业中性化）：Sharpe从2.51崩到0.27
3. **删ΔCMF**：Sharpe从+2.48崩到-2.29 (即使ΔCMF独立IC≈0)

### 🔍 重要诊断教训
**IC高 ≠ Sharpe贡献高**。ΔCMF独立IC=-0.004但删除后Sharpe暴跌4.77，说明它在组合里是关键的"去相关器"。任何因子改动必须用回测验证，不能只看IC排名。

## 数据路径（210服务器）
- 日线: `/mnt/big/base/shibo/KLines_make/daily_temp3/`
- 分钟K: `/mnt/big/origin/public/MatrixDailyFix/` (尚未接入)
- Barra: `/mnt/big/base/zhuhuihao/host_zhu/neutral/new_factor_日期.csv` (尚未接入)
- 停牌/ST/复权/行业: `/mnt/big/base/zhuhuihao/alphagp_lv2_daily/*.csv`
- 缓存: `/mnt/big/base/public/FundamentalTL/cache/`

## 下一步计划

### P0
- [ ] 接入分钟K线数据
- [ ] 接入Barra因子（替代手写市值OLS）

### P1
- [ ] 日内相似度聚类→隐含板块→真正的"补涨因子v2"（领导核心方向）
- [ ] 跑factor_marginal_diagnosis看4因子真实边际贡献

### P2
- [ ] Phase 2组合回测（换手率/交易成本/仓位）
- [ ] 出场信号设计
