# E0 —— 基线复现：改引擎前证明环境能逐格复现 2026-07-08 交付

用途：在动 `compute_calendar_pnl` 之前，用**当前**引擎把 7/8 的交付脚本原样再跑一遍，证明 (a) 24 个 DEV-net 锚点 |d|=0，(b) 7 个交付 CSV 逐字节相同。这是 E1 的地基：之后所有"数字变了"才能归因于引擎改动，而不是环境漂移。纯跑批，不改任何代码。先读 `00_协议.md`。

## 0. 背景（读懂再动手）
- 交付脚本 `delivery/I11_candidate_pools_20260708/export_delivery_pools.py` config-for-config 复现 phase3（`results/20260707_1952_agg_matrix_phase3_cmfveto/summary.csv`），自检 24 格（4 段 × 6 候选）的 DEV net 年化，任一 |d| ≥ 0.05 即 ABORT、不写文件。7/8 实跑结果在 `results/20260709_0001_delivery_pools/`（目录名 0709 是远端时钟超前，实为 7/8），24/24 |d|0.000，耗时约 4.5 分钟。
- 脚本只写自己的 `results/<ts>_delivery_pools/`，**不会**碰公共库 `/mnt/big/base/public/FundamentalTL/量价因子/I11_candidate_pools/`（7/8 那次是手工复制）。本次也**不复制**。
- 脚本 import-only：只读地基 4 文件 + `comprehensive_factor_diagnosis`。本地 `_remote_tmp/export_delivery_pools.py` 与仓库内副本 md5 相同（`b9e71a5ef61737722f01f07a244fba90`），直接跑仓库内副本，不用 scp。
- 引擎当前状态（E1 要改的对象，本步只看不动）：`comprehensive_factor_diagnosis.compute_calendar_pnl` 持仓 `shift(1)` 配回看日收益，收益未复权。这就是 E0 要冻结的"旧口径"基线。

## 1. 起点确认（任一不符 → 停，写进 REPORT 的 BLOCKERS）
1. `ssh 47`，`cd /mnt/sda2/lichenchen/code/project_core`。`git log -1 --oneline` = `5623e59`；`git status --short` 只有 3 个已知 untracked（`full_a_single_factor.py` / `sharpe_credibility_diagnosis.py` / `single_factor_groups.py`，是 §2 表里的历史脚本，**不要 add 也不要删**）；tracked 文件零改动。
2. 跑 `PROJECT_STATUS.md` §13 的第 1、2、4、5 步（第 3 步 features keys 核对本次不做）。
3. `md5sum delivery/I11_candidate_pools_20260708/export_delivery_pools.py` = `b9e71a5ef61737722f01f07a244fba90`。
4. `ps -ef | grep python | grep -v grep`：只应有同事的 jupyter / ipython 常驻进程，没有我们自己的残留任务；`uptime` 负载 <5。
5. `ls /mnt/sda2/lichenchen/data/cache/`：四个分段缓存 `daily_kline_20100104_20141231 / 20150101_20181231 / 20190101_20231231 / 20240101_20260327 .parquet` 都在（脚本按段加载，靠它们）。

## 2. 跑
```bash
cd /mnt/sda2/lichenchen/code/project_core
nohup taskset -c 96-191,288-383 python -u delivery/I11_candidate_pools_20260708/export_delivery_pools.py > /tmp/E0_export.log 2>&1 &
disown
```
- 脚本第一行打印 `[out] /mnt/sda2/lichenchen/results/<ts>_delivery_pools`，`log.txt` 同时落在该目录（脚本自带 dual logging）。
- 预计 5 分钟。超过 30 分钟仍无 `[ALLDONE]` → 多半落到慢 socket 或负载异常：`ps` 看清楚后报告，不要重复启动。
- 轮询只看 `tail -3`，间隔 ≥60 秒。

## 3. 验收（两条都过才算 E0 完成）
- **G0-1 数字**：日志出现 `[SELF-CHECK] ALL 24 PASS`，且 24 行 `got / anchor` 全部打印 `|d|0.000`。24 行原样摘进 REPORT。
- **G0-2 持仓**：新目录 7 个 CSV（`pool1_I11_screening.csv` + 6 个 `pool2_*.csv`）与 `results/20260709_0001_delivery_pools/` 同名文件 `md5sum` 逐一相同，列成 7 行表。`README.md` / `_delivery_stats.csv` 不比（README 是手写的）。
- 任一不过 → **不进 E1**。REPORT 写 BLOCKERS：哪一格 / 哪个文件、差多少、你认为的原因（缓存被改？数据源更新？pandas 版本？）。**不要改脚本、不要改锚点、不要调 TOL。**

## 4. 交回
- `exec_briefs/E0_REPORT.md`（结构见 `00_协议.md`）：起点确认 5 项逐条结果；results 目录名；G0-1 的 24 行；G0-2 的 7 行 md5 表；耗时（目录时间戳 → log.txt 的 mtime）；纯文本摘要 ≤10 行；BLOCKERS。
- WORKLOG 一条（远端 + 本地 `_tmp_WORKLOG.md` 同文），格式沿用 2026-07-08 那条：跑了什么 / 结果目录 / 自检结果 / 红线（只读地基+数据、未改代码、未 commit）/ 客观结论一句 / 状态。

## 5. 禁区
不改任何 `.py`；不 commit；不 push；不碰公共库目录；不删 results；不跑 brief 之外的脚本；结果数字不外发；日志与 REPORT 里不出现登录信息与主机地址。
