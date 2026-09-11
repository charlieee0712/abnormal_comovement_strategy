# H1 —— 建 I11 交接包生成脚本 `scripts/build_handoff_i11.py`（搬运件 + 机器生成件；手写件由规划 session 提供）

> **入库副本脱敏说明（2026-09-11）**：本仓库为 PUBLIC。按 `00_协议.md` §7「不写用户名；旧文档里的登录信息也不得转抄」，入库副本把同事账号名替换成了占位符（`ACCT0` / `ACCT_A`…`ACCT_H` / `ACCT_LIB`）。**除这些标识符外一字未改**；真实映射见用户本地原件，不入库。

用途：给 Claude web 建一个独立 Claude Project 的知识库（≤40 个 .md，长度不限）。包分两类：**手写件**（`00–06`、`10`，规划 session 已写好放在 `handoff_i11/`，脚本**不得覆盖**）与**脚本生成件**（其余编号，本步建脚本一次生成，以后用户说"更新"就重跑）。生成过程必须**脱敏**（不出现登录信息、主机地址、账号名、同事用户名），最后自检零命中才算成功。先读 `00_协议.md`；本 brief 末尾有自审记录。

## 0. 背景
- 先例：`C:\Users\cnc\quant_factor_notes\scripts\build_handoff.py`（另一项目的 24 件搬运/机器生成，带 `--check`）。本脚本照它的思路，独立实现，不 import 它。
- 输出目录：`C:\Users\cnc\resonance_strategy\handoff_i11\`（已存在，内含手写件）。脚本只写下表"脚本生成"的文件与 `_build_manifest.txt`；启动时若手写件缺失只 WARN 不创建。
- 运行环境：本机 Git Bash，`~/anaconda3/python.exe`（Store 空壳 `python` 不能用）；远端读取用 `subprocess.run(['ssh','47','cat',path])`（`ssh` 在 Git Bash PATH 里；失败即 abort 并打印路径）。
- 文本一律 UTF-8、`\n` 换行；每个生成件顶部加两行头：`# <标题>` 与 `> 脚本生成于 <日期>，来源：<源路径列表>；勿手改，重生成会覆盖。`

## 1. 文件清单（编号即文件名前缀；共 35 个 .md，上限 40）

| 编号-文件名 | 类型 | 来源与处理 |
|---|---|---|
| `00-总索引与使用说明.md` … `06-术语与配置命名速查.md`、`10-策略经济含义与因子角色.md` | **手写（不动）** | 规划 session 维护 |
| `11-方法论总纲.md` | 搬运 | `quant_factor_notes/references/_方法论总纲.md` 原文 + 末尾附 `_速查卡.md` 原文 |
| `12-真假因子判据.md` | 搬运 | `quant_factor_notes/references/02_Navigating_the_Factor_Zoo/_真假因子判据.md` |
| `13-回测框架与检验方法.md` | 搬运 | `quant_factor_notes/references/04_因子投资_方法与实践/_回测框架与检验方法.md` |
| `14-成本模型与L2理论.md` | 搬运 | `quant_factor_notes/references/03_Market_Microstructure_in_Practice/_成本模型与L2理论.md` |
| `15-参考文献清单.md` | 搬运 | 本地 `_tmp_REFERENCES.md` |
| `16-早期方法论研究报告合集(2026-06).md` | 搬运·合并 | 本地 8 篇：`A股4因子框架优化 深度研究报告` / `A股日频截面选股：从160只到20只…` / `A股日频量价选股策略方法论改进…` / `A股观察池内二次截面筛选框架…` / `VWAP执行约束下的日频选股信号…` / `信号触发池内二次截面筛选：方法论文献综述` / `多因子决策层流程层组合的文献与方法论调研` / `多因子聚合规则选择：≥3因子下 worst-rank…`；每篇前加 `## <原文件名>` 分隔 |
| `20-47工程规范PROJECT_STATUS全文(脱敏).md` | 搬运·脱敏 | `ssh 47 cat /mnt/sda2/lichenchen/code/project_core/PROJECT_STATUS.md`；§12 内含连接信息的行整行替换为 `- （连接信息已脱敏，见用户本地私有文件）`；再过全局脱敏 |
| `21-WORKLOG全文.md` | 搬运·脱敏 | 本地 `_tmp_WORKLOG.md`（是远端 worklog 的镜像） |
| `22-代码结构与接口.md` | 机器生成 | ① 用 `ast` 解析 47 上 `comprehensive_factor_diagnosis.py / pool_screening_v2.py / event_study.py / features_daily.py / data_loader.py` 的顶层 `def`：函数名、参数表、docstring 首行（`data_loader` 只列 `load_all_daily_data` 与 `load_daily_kline_from_csv` 的签名与返回键说明，**不输出 `PATHS` 字典**）；② `features_daily.py` 的全部 `features['xxx'] = ...` 定义行（70 个）；③ `PERIODS` 原文；④ 附录：本地 `_remote_tmp/e6b_stack_sleeves.py` 全文作"参考实现"（pipeline、helper、配置命名都在里面） |
| `23-因子清单34+1与形状角色.md` | 机器生成 | ① `ssh 47 "cd .../project_core && python -c \"import comprehensive_factor_diagnosis as C; [print(s['name'], {k:v for k,v in s.items() if k not in ('name','func')}) for s in C.get_default_factor_specs()]\""`；② `pool_screening_v2.py` 中 `compute_reversal_skip1 / compute_parkinson_vol / compute_abnormal_turnover / compute_cmf_change / neutralize_by_mcap` 的源码段；③ 47 `results/20260904_1051_E6_wide_scan/roles.csv` 转 markdown 表；④ 说明行：`intraday_cvr_1d = close/vwap − 1`（台账 H1，探索性） |
| `30-E0基线复现+E1引擎修正.md` | 搬运·合并 | `exec_briefs/E0_baseline_reproduction.md` + `E0_REPORT.md` + `E1_engine_fix.md` + `E1_REPORT.md`，每件前加 `## <文件名>` |
| `31-E2分解表.md` | 同上 | `E2_decomposition.md` + `E2_REPORT.md` |
| `32-E3单因子复审.md` | 同上 | `E3_single_factor_rerun.md` + `E3_REPORT.md` |
| `33-E4聚合复审.md` | 同上 | `E4_aggregation_review.md` + `E4_REPORT.md` |
| `34-E5a终形态交付v2+E5b文档收口.md` | 同上 | `E5a_final_forms_delivery_v2.md` + `E5a_REPORT.md` + `E5b_docs_and_delivery.md` + `E5b_REPORT.md` |
| `35-E6宽扫描v1.md` | 同上 | `E6_wide_scan.md` + `E6_REPORT.md` |
| `36-E6b宽扫描v2.md` | 同上 | `E6b_stack_and_sleeves.md` + `E6b_REPORT.md` |
| `37-E6c持有期(待执行)+E7延长样本(HOLD).md` | 同上 | `E6c_holding_horizon.md` + `E7_oos_extension.md`（若存在 `E6c_REPORT.md` 也并入） |
| `38-exec_briefs协议原文.md` | 搬运 | `exec_briefs/00_协议.md` |
| `40-汇报_I11最终版本+第二次进展.md` | 搬运·合并 | `汇报_I11最终版本.md` + `汇报_第二次进展.md` |
| `41-A组矩阵汇报+总结0609+第三次进展.md` | 搬运·合并 | `_tmp_A组矩阵汇报.md` + `总结_第二次汇报后至0609.md` + `汇报_第三次进展_0609至0707.md` |
| `42-周报草稿_引擎修正_20260903.md` | 搬运 | `汇报_周报_引擎修正_20260903.md` |
| `50-结果表汇编_E2E3E4.md` | 搬运·合并（47） | `results/20260903_0935_E2_decomposition/log.txt` 从 `DECOMPOSITION` 起到文件尾 + `decomp.csv` 转表；`results/20260903_1037_E3_single_factor/summary.txt` 全文；`results/20260903_1132_E4_agg_review/log.txt` 从第一处 `MAIN` 起到文件尾 |
| `51-结果表汇编_E6E6b.md` | 搬运·合并（47） | `results/20260904_1051_E6_wide_scan/summary.txt` + `results/20260904_1202_E6b_stack_sleeves/summary.txt` 全文（若 E6c 结果目录已存在，追加其 `summary.txt`） |
| `52-研究档合集_memory(一)策略与因子.md` | 搬运·合并·脱敏 | memory 目录下：`resonance-engine-fix-calendar-timing-adjustment` / `resonance-engine-fix-readjudication-verdict` / `resonance-factor-combo-stack-status` / `resonance-factor-combo-pool-delivery` / `constraint-definition-correction` / `resonance-factor-combo-bottom-pool-excess-attribution` / `resonance-factor-combo-group-a-matrix-verdict` / `resonance-factor-combo-plan2-c-residual-verdict` / `resonance-factor-combo-manual-review-verdict` / `resonance-factor-combo-agg-matrix-phase1` / `resonance-factor-combo-aggregation-phase1-verdict` / `resonance-factor-combo-group-b-evolution` / `resonance-factor-combo-abn-tvol-relationship` / `resonance-factor-combo-invU-distanceification-verdict` / `resonance-factor-combo-invu-shape-evolution`（去掉 frontmatter，每件前加 `## <name>`） |
| `53-研究档合集_memory(二)方法论与读书.md` | 同上 | `resonance-methodology-exante-factor-selection` / `resonance-methodology-ex-ante-registry` / `resonance-factor-combo-pool-entry-checklist` / `exploration-loose-admission-strict` / `brief-self-review-before-handoff` / `resonance-refbooks-shichuan-verdict` / `resonance-refbooks-factorzoo-verdict` / `resonance-refbooks-microstructure-verdict` / `resonance-refbooks-nagel-verdict` / `resonance-refbooks-future-directions-verdict` / `resonance-refbooks-reading-progress` / `resonance-downloaded-research-reports-map`。**排除** `remote-quant-project-access.md`、`user-name.md`、`MEMORY.md` |
| `60-交付v1v2清单与README.md` | 搬运·合并（47+本地） | 本地 `DELIVERY_README.md`（v1）+ 47 `delivery/I11_candidate_pools_20260708/SUPERSEDED.md` + 47 `delivery/I11_candidate_pools_v2_20260903/{README.md,_delivery_stats.csv(转表),old_vs_new.txt}` |

memory 目录：`C:\Users\cnc\.claude\projects\C--Users-cnc-resonance-strategy\memory\`。

## 2. 脱敏（对所有生成件，逐行；手写件不处理但要**检查**）
- 行级替换：含任一模式的整行 → `（已脱敏）`：`\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b`、`user=`、`pass=`、`pw=`、`password`、`密码`、`口令`、`ssh -p`、`-p 90\d\d`、`\w+@[\w.-]+:\d+`（user@host:port）、`@\d{1,3}\.\d{1,3}`（@ 后接 IP）、`id_ed25519`、`token`（大小写不敏感）。**不要用裸 `@\d`**：配置名 `…@30`、`…@h10` 会误伤（规划 session 自审时用手写件实测过）。
- 词级替换（不删行）：账号与同事用户名 → 别名：`ACCT0→<账号>`、`ACCT_A→<同事A>`、`ACCT_B→<同事B>`、`ACCT_C→<同事C>`、`ACCT_D→<同事D>`、`ACCT_E→<同事E>`、`ACCT_F→<同事F>`、`ACCT_G→<同事G>`、`ACCT_H→<同事H>`、`ACCT_LIB→<库账号>`（作为独立词或路径段匹配）。`lichenchen` 是用户本人目录名，保留。
- PROJECT_STATUS §12：从 `## 12.` 到 `## 13.` 之间，含 `host`、`port`、`用户`、`密码`、`user=` 的行整行替换（同上规则会覆盖，但要确认 `host:`/`port:` 两行也被替换——加模式 `^\s*-\s*(host|port)\s*:`）。
- 最终自检：对 `handoff_i11/*.md`（含手写件）跑 `grep -nE '192\.168\.|user=|pass=|pw=|password|密码|口令|ssh -p|[A-Za-z0-9_]+@[A-Za-z0-9_.-]+:[0-9]+|@[0-9]{1,3}\.[0-9]{1,3}|梯子|反爬|验证码|ACCT0|ACCT_A|ACCT_B|ACCT_C|ACCT_D'`，**任何命中 → 退出码 1、打印命中行、不写 manifest**。

## 3. 脚本骨架（`scripts/build_handoff_i11.py`；照此实现，函数名可变，行为不可变）
```python
# -*- coding: utf-8 -*-
"""build_handoff_i11.py — I11 交接包生成器. 用法:
   ~/anaconda3/python.exe scripts/build_handoff_i11.py --check   # 只比对: 逐件 identical/changed/new, 不写
   ~/anaconda3/python.exe scripts/build_handoff_i11.py           # 生成脚本件 + _build_manifest.txt; 手写件不动
"""
import os, re, io, sys, ast, subprocess, argparse, datetime, csv, tempfile
ROOT = r'C:\Users\cnc\resonance_strategy'; OUT = os.path.join(ROOT, 'handoff_i11'); QFN = r'C:\Users\cnc\quant_factor_notes'
MEM = r'C:\Users\cnc\.claude\projects\C--Users-cnc-resonance-strategy\memory'
R47 = '/mnt/sda2/lichenchen'; PC = R47 + '/code/project_core'; RES = R47 + '/results'
HANDWRITTEN = ['00-','01-','02-','03-','04-','05-','06-','10-']
def read_local(p): return io.open(p, encoding='utf-8').read()
def read_47(p):
    r = subprocess.run(['ssh', '47', 'cat', p], capture_output=True); assert r.returncode == 0, ('ssh cat failed: ' + p + ' ' + r.stderr.decode('utf-8', 'ignore')[:200]); return r.stdout.decode('utf-8')
def run_47(cmd): r = subprocess.run(['ssh', '47', cmd], capture_output=True); assert r.returncode == 0, ('ssh cmd failed: ' + cmd[:80]); return r.stdout.decode('utf-8')
def scrub(text): ...            # §2 行级 + 词级规则; 返回 (text, n_replaced_lines)
def strip_frontmatter(md): ...  # 去掉开头 --- ... --- 块
def csv_to_md(text, max_rows=None): ...  # csv 文本 → markdown 表 (全部列; 浮点保留 4 位)
def header(title, sources): return '# %s\n\n> 脚本生成于 %s，来源：%s；勿手改，重生成会覆盖。\n\n' % (title, datetime.date.today(), '；'.join(sources))
def concat(parts): return '\n\n'.join('## %s\n\n%s' % (name, body.strip()) for name, body in parts)
def code_interface(): ...       # ast 解析 5 个 py: 顶层 def 的 签名 + docstring 首行; features_daily 的 features['x'] = 行; PERIODS 原文; 附 e6b 全文
def factor_list(): ...          # run_47 python -c specs; pool_screening_v2 五个函数源码段 (用 ast 取 lineno..end_lineno); roles.csv → 表
BUILD = {  # 文件名 -> callable 返回 (title, sources, body_text_before_scrub)
  '11-方法论总纲.md': lambda: ('方法论总纲 + 速查卡', [...], concat([...])),
  ...
}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--check', action='store_true'); a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    for h in HANDWRITTEN:
        if not any(f.startswith(h) for f in os.listdir(OUT)): print('[WARN] 手写件缺失:', h)
    manifest = []; changed = 0
    for fname, fn in BUILD.items():
        title, sources, body = fn(); body, n_scrub = scrub(body); text = header(title, sources) + body.rstrip() + '\n'
        path = os.path.join(OUT, fname); old = read_local(path) if os.path.exists(path) else None
        state = 'new' if old is None else ('identical' if old.split('\n', 3)[3:] == text.split('\n', 3)[3:] else 'changed')   # 忽略头部日期行
        print('%-52s %-9s %7d chars  scrubbed_lines=%d' % (fname, state, len(text), n_scrub)); changed += state != 'identical'
        if not a.check: io.open(path, 'w', encoding='utf-8', newline='\n').write(text)
        manifest.append((fname, len(text), n_scrub, '; '.join(sources)))
    if a.check: print('[check] changed/new =', changed); return
    # 自检
    pat = re.compile(r'192\.168\.|user=|pass=|pw=|password|密码|口令|ssh -p|\w+@[\w.-]+:\d+|@\d{1,3}\.\d{1,3}|梯子|反爬|验证码|ACCT0|ACCT_A|ACCT_B|ACCT_C|ACCT_D', re.I)
    hits = [(f, i + 1, l[:120]) for f in sorted(os.listdir(OUT)) if f.endswith('.md') for i, l in enumerate(read_local(os.path.join(OUT, f)).split('\n')) if pat.search(l)]
    n_md = len([f for f in os.listdir(OUT) if f.endswith('.md')])
    if hits or n_md > 40:
        for h in hits: print('[LEAK]', *h)
        print('[FAIL] hits=%d n_md=%d' % (len(hits), n_md)); sys.exit(1)
    io.open(os.path.join(OUT, '_build_manifest.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join('%s\t%d\t%d\t%s' % m for m in manifest) + '\n')
    print('[OK] generated %d files, total .md = %d (<=40), leak hits = 0' % (len(BUILD), n_md))
if __name__ == '__main__': main()
```
要点：`--check` 比对时忽略头部日期行；`concat` 的每件前 `## <文件名>`；`12–14` 若源文件路径有变用 `glob` 找并打印实际路径；47 上 `python -c` 取 specs 时只 import、不加载数据（`get_default_factor_specs` 不读数据）。

## 4. 验收
- **H1-1**：`--check` 首跑全部 `new`；正式跑后 `--check` 全部 `identical`（幂等）。
- **H1-2**：`handoff_i11/` 内 `.md` 总数 = 35（手写 8 + 生成 27）；`_build_manifest.txt` 27 行。
- **H1-3**：自检零命中（含手写件）；额外人工 `grep -c '已脱敏' handoff_i11/20-*.md` ≥ 3（§12 的连接行被替换）；`grep -c '<账号>\|<同事' handoff_i11/*.md` 的命中列出来（应集中在 20、21、30、35、36）。
- **H1-4**：抽样打开 `22`（能看到 `compute_calendar_pnl(weights, data, base_pool, hold_days=5, cost_bp_bilateral=8, exec_lag=1, adjust=True)` 与 70 个 features 定义行）、`23`（35 行 roles 表）、`50`（E3 summary 353 行在内）、`52/53`（frontmatter 已去、`remote-quant-project-access` 不在）。
- 每件字符数写进 REPORT。

## 5. 交回
- 本地 git（`resonance_strategy` 若不是 git 仓库则只落盘不 commit；是的话 `git add scripts/build_handoff_i11.py handoff_i11/` 并 commit，不 push——本地仓库无 remote 时跳过）。
- `exec_briefs/H1_REPORT.md`：H1-1～4；manifest 全文；脱敏统计（每件替换行数）；自检输出末行；BLOCKERS。
- 不写 WORKLOG（这是本地工具，不是研究操作）。

## 6. 禁区
不改 47 上任何文件；不改 `exec_briefs/` 与 memory 目录里任何文件；不覆盖手写件（`00–06`、`10`）；不在生成件里保留任何登录信息/主机地址/账号名；`.md` 总数不得超过 40；不 push。凡遇"必须改上述任何一项才能继续" → 停，写 BLOCKERS。

## 7. 自审记录（规划 session 2026-09-04；执行端见此段方可开工）
| 类 | 不利因素 | 处置 |
|---|---|---|
| 安全 | PROJECT_STATUS §12、memory 接入档、E0 REPORT 的 `ps` 输出里有主机/账号/同事用户名 | 行级 + 词级双规则；接入档与 user-name 整件排除；最终自检零命中否则 exit 1 |
| 安全 | 手写件也可能不小心带账号名 | 自检覆盖全目录含手写件 |
| 误伤 | 初稿的 `@\d` 规则会把配置名 `S_A(cond+tvol)@30`、`A4b@h10` 所在行整行删掉，导致 06/36/37/51 大面积"已脱敏"且最终自检失败 | 已改为 `user@host:port` 与 `@IP` 两个精确模式（规划 session 用手写件实测出的误报） |
| 误伤 | 规则里的敏感词本身出现在"文档表达规范"的正文里（如"口令"） | 手写件 01 已改措辞；生成件若源文里有该词（PROJECT_STATUS/协议原文），整行替换为「（已脱敏）」可接受 |
| 代码 | Windows 下 `subprocess` 找不到 `ssh`，或输出编码非 UTF-8 | 从 Git Bash 用 anaconda python 跑；`decode('utf-8')` 失败即 abort 打印路径 |
| 代码 | 写文件默认 CRLF、GBK | 显式 `encoding='utf-8', newline='\n'` |
| 代码 | `--check` 因头部日期每次都"changed" | 比对时忽略头部日期行 |
| 代码 | `ast` 解析 47 文件需要完整源码（不能 `cut`） | `ssh cat` 取全文；解析失败即 abort |
| 内容 | 多件合并后单文件很长（41、16、50 均 >100 KB） | Claude Project 长度不限；但 `.md` 数量 ≤40 由脚本断言 |
| 内容 | E6c/E7 尚未执行，`37` 只有 brief | 头部注明"待执行/HOLD"；以后重生成自动并入 REPORT |
| 内容 | 结果目录路径写死，结果目录名带时间戳 | 写死当前四个已知目录；E6c 结果目录用 `glob` 匹配 `*_E6c_holding_horizon` 取最新 |
| 一致 | 手写件与生成件对同一事实的口径可能漂移 | 手写件只写结论与指针，数字以 `50/51` 为准（`00` 已声明） |

方向确认：交接包服务于"web 出 plan"，所以接口（22）、命名（06）、协议（38）、E 系列全档（30–37）与结果表（50/51）齐全；OOS 仍 HOLD，与包内 `37` 一致。
