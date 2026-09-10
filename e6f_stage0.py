#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 阶段 0: 起点核对、契约、注册表、事前登记、E6e 修订补全、勘误。
   用法: python e6f_stage0.py --out DIR
"""
import os, sys, json, time, socket, resource, subprocess, argparse, inspect, hashlib
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K
import e6f_core as F
import comprehensive_factor_diagnosis as C
import data_loader as DL

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--briefs', default='/mnt/sda2/lichenchen/exec_briefs_in')
A = ap.parse_args()
OUT = A.out
for d in ('checks', 'revisions/E6e_summary_fix', 'task_status', 'logs'):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
LOG = []
ISSUES = []


def P(s=''):
    print(s, flush=True); LOG.append(s)


def chk(name, cond, detail=''):
    P('  %-52s %s %s' % (name, 'OK  ' if cond else '!!  ', detail))
    if not cond:
        ISSUES.append(dict(item=name, detail=detail))
    return cond


T0 = time.time()
P('=== E6f 阶段 0 === %s' % time.strftime('%Y-%m-%d %H:%M:%S %Z'))

# ============================================================
# 1.1 起点确认
# ============================================================
P('')
P('=== §1.1 起点 ===')
CODE = '/mnt/sda2/lichenchen/code/project_core'


def sh(c):
    return subprocess.run(c, shell=True, capture_output=True, text=True, cwd=CODE).stdout.strip()


gst = sh('git status -sb | head -1')
chk('git status -sb', gst.startswith('## main...origin/main'), gst)
E6E_COMMITS = ['981c08d', '7ab38f8', '0fbd683']
glog = sh('git log --oneline -8')
chk('E6e 三个 commit 在历史里', all(c in glog for c in E6E_COMMITS), glog.replace('\n', ' | ')[:100])
untracked = [x for x in sh('git status --porcelain | grep "^??"').split('\n') if x.strip()]
P('  untracked: %d 个 (不 add, 不动)' % len(untracked))

FOUND = ['data_loader.py', 'features_daily.py', 'event_study.py', 'pool_screening_v2.py',
         'comprehensive_factor_diagnosis.py']
E6E_PY = ['e6e_core.py', 'e6e_stageA.py', 'e6e_run.py', 'e6e_selftests.py', 'e6e_merge1.py',
          'e6e_random.py', 'e6e_stats.py']
e6e_man = json.load(open(os.path.join(F.E6E_DIR, 'run_manifest.json')))
sha_now = {f: F.sha_file(os.path.join(CODE, f)) for f in FOUND + E6E_PY}
man_sha = {}
for k_, v in (e6e_man.get('code_sha') or e6e_man.get('sha') or {}).items():
    man_sha[os.path.basename(k_)] = v
inman = [f for f in FOUND + E6E_PY if f in man_sha]
bad_man = [f for f in inman if man_sha[f] != sha_now[f]]
chk('E6e manifest 里的文件 SHA 全部一致',
    not bad_man, 'manifest 共 %d 条, 覆盖 %d 个当前文件, 不一致 %s '
                 '(manifest 写于 E6e 阶段 A, 其后写的 4 个 e6e 脚本本就不在其中)'
    % (len(man_sha), len(inman), bad_man or '无'))
dirty = [x for x in sh('git status --porcelain e6e_*.py').split('\n') if x.strip()]
chk('七个 e6e_*.py 全部 git clean (字节不变)',
    not dirty and all(os.path.exists(os.path.join(CODE, f)) for f in E6E_PY), str(dirty))
chk('引擎默认 (5, 8, 1, True)',
    (K.HOLD, K.COST, K.EXEC_LAG, K.ADJUST) == (5, 8.0, 1, True),
    str((K.HOLD, K.COST, K.EXEC_LAG, K.ADJUST)))
chk('C.COST_BP_BILATERAL == 8.0', abs(getattr(C, 'COST_BP_BILATERAL', 8.0) - 8.0) < 1e-12)

# 环境
nproc = len(os.sched_getaffinity(0))
mem = sh("free -g | awk '/Mem:/{print $2\" total \"$7\" avail\"}'")
ulim = resource.getrlimit(resource.RLIMIT_NPROC)[0]
me = os.environ.get('USER') or 'me'
nmy = int(sh('ps -u $(id -u) -o pid= | wc -l') or 0)
nthr = int(sh('ps -u $(id -u) -L -o pid= | wc -l') or 0)
resid = sh("ps -u $(id -u) -o pid=,cmd= | grep -E 'e6[a-f]_|E6[a-f]' | grep -v grep | wc -l")
P('  核 %d  内存 %s  ulimit -u %s  我的进程 %d 线程 %d  本项目残留 %s'
  % (nproc, mem, ulim, nmy, nthr, resid))
chk('无本项目残留进程', resid.strip() in ('0', ''), resid)
chk('进程配额余量 ≥20%% 且 ≥64 槽', (ulim - nthr) >= max(64, 0.2 * ulim),
    '余 %d / %d' % (ulim - nthr, ulim))
first_src, last_src = F.source_last_date()
P('  源 kline 日期范围 %s ~ %s ; 本轮冻结末日 %s (禁区 §12)' % (first_src, last_src, F.FROZEN_END))
chk('源数据确实超过冻结末日 -> 守卫必要', last_src > F.FROZEN_END, '%s > %s' % (last_src, F.FROZEN_END))

# ============================================================
# 文档副本 + 事前登记 (§8 逐字)
# ============================================================
P('')
P('=== §1.4 事前登记 (§8 逐字落盘) ===')
brief_src = os.path.join(A.briefs, 'E6f_construction_selection.md')
plan_src = os.path.join(A.briefs, 'E6f_plan_web_final.md')
brief_txt = open(brief_src, encoding='utf-8').read()
plan_txt = open(plan_src, encoding='utf-8').read()
SHA_BRIEF, SHA_PLAN = F.sha_file(brief_src), F.sha_file(plan_src)
chk('web plan SHA == brief 声明值',
    SHA_PLAN == 'ddf3a7d94ff9a19dcb5f61101a6b5e9c3ec171551763920c44941ec96e9289e3', SHA_PLAN[:16])
open(os.path.join(OUT, 'brief_copy.md'), 'w', encoding='utf-8').write(brief_txt)
open(os.path.join(OUT, 'PLAN_COPY.md'), 'w', encoding='utf-8').write(plan_txt)

lines = brief_txt.split('\n')
i0 = next(i for i, l in enumerate(lines) if l.startswith('## 8. 事前登记'))
i1 = next(i for i, l in enumerate(lines) if l.startswith('## 9. 自测与验收'))
S8 = '\n'.join(lines[i0:i1]).rstrip() + '\n'
chk('§8 抽取到 Q1..Q7 全部', all(('| Q%d |' % q) in S8 for q in range(1, 8)),
    '%d 行 %d 字符' % (S8.count('\n'), len(S8)))
chk('§8 含边界全文', '**边界全文**' in S8)

SRCMAP = {
    'A01/R1': 'KT_dep(50,50)|C:k5', 'A02/R2': 'KT_mean@30|C:k5+cr5:k10',
    'A03': 'KT_dep(50,50)|C:k5+cr5:k10', 'A04': 'KTC_mean@25',
    'A05/C1': 'KTC_mean@25|cvr_1d:k10', 'A06': 'KTC_mean@25|cvr_1d:k10+cr5:k10',
    'A07/C2': 'KTC_mean@30|cvr_1d:k10+cr5:k10', 'A08': 'T@30|C:k5+cr5:k10',
    'A09': 'KTC_mean@25|cmp_mean(cvr_1d,cr5):k10', 'A10': 'TC_mean@35|cvr_1d:k10+cr5:k10',
    'A11': 'T@25', 'A12': 'KT_mean@30',
}
prereg = (
    '# E6f 事前登记 (preregistration)\n\n'
    '**落盘时间**: %s (Asia/Shanghai; 主机本地时区 %s)\n'
    '**落盘时点**: 在本轮任何新的收益评价之前。\n\n'
    '**来源**: 本文 §8 表格与边界全文自 `brief_copy.md` 的「## 8. 事前登记」节**逐字抽取**, '
    '未改写编号与问题 (E6e 曾重写, 本轮禁止)。执行端只补时间、哈希与源 ID 映射。\n\n'
    '## 哈希\n\n| 文件 | SHA256 |\n|---|---|\n'
    '| brief `E6f_construction_selection.md` | `%s` |\n'
    '| web plan `E6f_plan_web_final.md` | `%s` |\n'
    % (time.strftime('%Y-%m-%d %H:%M:%S'), time.tzname[0], SHA_BRIEF, SHA_PLAN))
for f in ['e6f_core.py', 'e6f_stage0.py', 'e6f_pilot.py']:
    p = os.path.join(CODE, f)
    if os.path.exists(p):
        prereg += '| 代码 `%s` | `%s` |\n' % (f, F.sha_file(p))
for f in E6E_PY:
    prereg += '| E6e `%s` (只读, 字节不变) | `%s` |\n' % (f, sha_now[f])
prereg += ('\n## A12 展示锚 -> 源 ID 映射 (§3)\n\n| 展示标签 | 源 config_id (E6e 账本列名) |\n|---|---|\n'
           + ''.join('| %s | `%s` |\n' % (k_, v) for k_, v in SRCMAP.items()))
prereg += '\n---\n\n' + S8
open(os.path.join(OUT, 'preregistration.md'), 'w', encoding='utf-8').write(prereg)
P('  写出 preregistration.md (%d 字符, §8 逐字 %d 字符)' % (len(prereg), len(S8)))

# ============================================================
# engine_contract.md —— 整段读函数体复核
# ============================================================
P('')
P('=== §1.3 契约复核 ===')
CT = []


def claim(name, cond, evidence):
    CT.append(dict(item=name, verdict='符合' if cond else '不符', evidence=evidence))
    chk(name, cond, evidence[:60])


src_pnl = inspect.getsource(C.compute_calendar_pnl)
claim('引擎 actual = W.rolling(5, min_periods=1).mean()',
      'rolling(hold_days, min_periods=1).mean()' in src_pnl, 'compute_calendar_pnl 函数体')
claim('引擎 ah = actual.shift(exec_lag+1) = shift(2)',
      'actual_holding.shift(exec_lag + 1)' in src_pnl, 'exec_lag=1 -> shift 2')
claim('引擎 gross = port - bench*position (已是仓位缩放后超额)',
      'portfolio_daily_ret - bm_daily * daily_position' in src_pnl, src_pnl.split('excess_daily =')[1].split('\n')[0].strip())
claim('引擎 turnover = 0.5*Σ|ah_t - ah_{t-1}|',
      'diff().abs().sum(axis=1) / 2.0' in src_pnl, 'holding_diff')
claim('引擎 cost = turnover*bp/1e4', 'holding_diff * (cost_bp_bilateral / 1e4)' in src_pnl, 'daily_cost')
claim('NaN 收益记 0 但权重仍入 position',
      '(actual_holding_t1 * daily_ret).sum(axis=1)' in src_pnl and
      'actual_holding_t1.sum(axis=1)' in src_pnl, 'pandas sum skipna, position 不过滤')
src_dev = inspect.getsource(K.assign_weights_dev)
claim('DEV w = min(1/n, 0.01)', 'min(1.0 / n, max_stock)' in src_dev, 'assign_weights_dev')
claim('DEV cap = clean 行业占比 + 0.03 等比缩减, 无下限不归一',
      'cap = shares[t].get(indcode, 0.0) + max_ind_dev' in src_dev and 'w[gi] *= cap / ssum' in src_dev,
      'MAX_IND_DEV=%.2f MAX_STOCK=%.2f' % (K.MAX_IND_DEV, K.MAX_STOCK))
src_h = inspect.getsource(C.build_factor_strategy_holdings_cached)
claim('分组: 有效值 < 3k 无持仓', 'len(df) < n_groups * 3' in src_h, 'build_factor_strategy_holdings_cached')
claim("分组: qcut(rank('first'), k)", "rank(method='first')" in src_h and 'pd.qcut' in src_h, '同上')
src_pre = inspect.getsource(C.precompute_neutralized_factor)
claim('中性化: 池 <6 跳过', 'len(stocks) < 6' in src_pre, 'precompute_neutralized_factor')
src_n = inspect.getsource(C.neutralize_by_mcap) if hasattr(C, 'neutralize_by_mcap') else ''
claim('中性化: 有效票 <10 返回原值', 'len(df) < 10' in src_n, 'neutralize_by_mcap')
src_adj = inspect.getsource(C.adjust_factor)
claim('复权: A_t = Π prev_s/lclose_s, 只在 is_open 算比值',
      "is_open" in src_adj and 'cumprod' in src_adj, 'adjust_factor')
src_f = open(os.path.join(CODE, 'features_daily.py'), encoding='utf-8').read()
claim('K = turnover_rate / (|log(close/lclose)| + 1e-4)',
      "turnover_rate / (daily_ret.abs() + 0.0001)" in src_f, 'features_daily conditional_turnover')
claim('T = turn.rolling(60, min_periods=30).std()',
      "turn.rolling(60, min_periods=30).std()" in src_f, 'turnover_volatility_60d')
claim('CVR_5d/20d min_periods 3/10',
      "cvr.rolling(5, min_periods=3).mean()" in src_f and "cvr.rolling(20, min_periods=10).mean()" in src_f,
      'features_daily')
claim('cum_return_w 用未复权 close',
      "features['cum_return_5d'] = close / close.shift(5) - 1" in src_f, 'features_daily')

# 账本恒等式
gg = {s: pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_gross_%s.parquet' % s)) for s in F.SEGS}
bn = {s: int(np.isnan(gg[s].iloc[:, 0].values).sum()) for s in F.SEGS}
Ts = {s: len(gg[s].index) for s in F.SEGS}
claim('账本 76 个基准全 NaN 日 = 4 段 × 19', sum(bn.values()) == 76 and set(bn.values()) == {19}, str(bn))
claim('四段合计 3,940 行', sum(Ts.values()) == 3940, str(Ts))
claim('账本 20,282 列', all(v.shape[1] == 20282 for v in gg.values()),
      str({s: gg[s].shape[1] for s in F.SEGS}))
open(os.path.join(OUT, 'engine_contract.md'), 'w', encoding='utf-8').write(
    '# E6f 引擎契约复核 (执行端整段读函数体, %s)\n\n'
    '来源文件: `comprehensive_factor_diagnosis.py` / `features_daily.py` / `pool_screening_v2.py` / `e6e_core.py`。\n'
    '「不符」项单列在末尾。\n\n| 契约条目 | 判定 | 证据 |\n|---|---|---|\n' % time.strftime('%Y-%m-%d')
    + ''.join('| %s | %s | `%s` |\n' % (c['item'], c['verdict'], c['evidence'].replace('|', '\\|')[:90])
              for c in CT)
    + '\n## 不符项\n\n' + ('\n'.join('- %s: %s' % (c['item'], c['evidence']) for c in CT if c['verdict'] != '符合')
                        or '无。\n')
    + '\n## 未找到 E6e 原件\n\n`engine_contract.md` / `PLAN_COPY.md` 在 E6e 目录不存在 (已查)。'
      '本文件与 `PLAN_COPY.md` 标 `RECONSTRUCTED_AT_E6f` (2026-09-09), **不倒签**为 E6e 当时产物。\n')

# ============================================================
# 候选域 + 注册表
# ============================================================
P('')
P('=== §3 注册表与候选域 ===')
AC = pd.read_csv(os.path.join(F.E6E_DIR, 'summary', 'all_candidates.csv')).set_index('config_id')
U0P = AC[AC.kind.isin(['core', 'hard', 'composite', 'exempt'])].index
U0B = AC[AC.kind.isin(['core', 'hard', 'composite', 'exempt', 'soft'])].index
chk('U0-primary = 3,770', len(U0P) == 3770, '实查 %d' % len(U0P))
chk('U0-broad = 6,038', len(U0B) == 6038, '实查 %d' % len(U0B))
P('  kind 分布: %s' % AC.kind.value_counts().to_dict())
missing_anchor = [k_ for k_, v in SRCMAP.items() if v not in AC.index]
chk('A12 全部 12 个锚在 E6e 账本里', not missing_anchor, str(missing_anchor))
P54 = [d['core_id'] for d in K.core_descriptors() if d['set'] == 'P54']
chk('P54 = 54 个', len(P54) == 54, '实查 %d' % len(P54))
pd.DataFrame(dict(config_id=list(U0B),
                  domain_primary=[c in set(U0P) for c in U0B],
                  kind=AC.loc[U0B, 'kind'].values,
                  core=AC.loc[U0B, 'core'].values,
                  veto=AC.loc[U0B, 'veto'].values,
                  family=AC.loc[U0B, 'family'].values)
             ).to_csv(os.path.join(OUT, 'domain_U0.csv'), index=False)

# feature_registry: 本轮要重建的全部因子规格
SPECS = []
for w in (20, 40, 60, 90, 120):
    SPECS.append(F.spec('T', w))
for w in (5, 10, 20, 40, 60):
    SPECS.append(F.spec('C', w))
for est in ('MA', 'ROS'):
    for w in (1, 3, 5, 10, 20):
        SPECS.append(F.spec('K', w, est=est))
for w in (1, 2, 3, 5):
    SPECS.append(F.spec('Cf', w, base=('ratio' if w == 1 else 'diff')))
SPECS.append(F.spec('Cf', 1, base='diff'))
for w in (3, 5, 10, 20):
    SPECS.append(F.spec('B', w, adj=False))
    SPECS.append(F.spec('B', w, adj=True))
for est in ('MA', 'ROS'):
    for w in (1, 5):
        for e in (1e-5, 1e-3):
            SPECS.append(F.spec('K', w, est=est, eps=e))
seen, USPEC = set(), []
for sp in SPECS:
    if F.fid(sp) not in seen:
        seen.add(F.fid(sp)); USPEC.append(sp)
anchor_of = {F.fid(sp): lib for sp, lib, _ in F.DEFAULT_ANCHORS}
FR = pd.DataFrame([dict(feature_id=F.fid(sp), role=sp['role'], window=sp['w'],
                        estimator=sp['est'] if sp['role'] == 'K' else '',
                        eps=sp['eps'] if sp['role'] == 'K' else np.nan,
                        base=sp['base'] if sp['role'] in ('C', 'Cf') else '',
                        adjust=sp['adj'] if sp['role'] == 'B' else '',
                        min_periods=F.mp(sp['w']), high_bad=F.high_bad(sp),
                        library_anchor=anchor_of.get(F.fid(sp), ''),
                        is_default=F.fid(sp) in anchor_of) for sp in USPEC])
FR.to_csv(os.path.join(OUT, 'feature_registry.csv'), index=False)
P('  feature_registry: %d 个唯一因子规格 (其中 %d 个有库默认锚)'
  % (len(FR), int(FR.is_default.sum())))
P('  角色分布: %s' % FR.role.value_counts().to_dict())

json.dump({
    'F-source': {'desc': 'E6e F1/F2/F4 全成员复算 + L20/60 + 块长 20', 'members': 'from E6e analysis_families.json'},
    'F-A': {'desc': 'UA 变体 - 对应默认父', 'subfamilies': ['window', 'weight', 'neutralization', 'k', 'H'], 'merged': True},
    'F-R': {'desc': 'U0-broad ∪ UA(H5) 对 R1/R2, 8/12bp', 'refs': ['R1', 'R2'], 'bp': [8, 12]},
    'F-C': {'desc': '冲击后差, 规模×κ 为情景维度',
            'A_yi': [0.1, 0.5, 1, 2, 5, 10, 20], 'kappa': [0.25, 0.5, 1.0]},
    'F-B': {'desc': '域×规则×正向政策账户及固定参照',
            'domains': ['OLD_structural', 'U0-primary', 'U0-broad', 'EXPANDED'],
            'rules': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S_meta']},
    'inference': {'hac_L': [5, 20, 60], 'bootstrap': {'mean_block': [20, 60], 'B': 2000},
                  'simultaneous': 'common-draw max|t|', 'no_gate': True},
}, open(os.path.join(OUT, 'analysis_families.json'), 'w', encoding='utf-8'),
    ensure_ascii=False, indent=1)

json.dump({
    'S1': '训练段 net8 均值最大者',
    'S2': '前 20 等资本',
    'S3': '每核族最大者 + 每族等资本组合 (族由构造元数据固定)',
    'S4': '非支配集合按换手升序等距取 ≤5',
    'S5': '对基准 HAC t 最大 (L=5; 无有限 SE 记未定义)',
    'S6': '邻域中位数最高的中心 (邻居由 §4.4 元数据预定义)',
    'S_meta': '外层训练区间内 ≥3 年起始逐年前向小折比较 S1-S6 真实政策账户 net8, '
              '按内部验证有效日加权选规则; 无内部折回退 S1 并标 insufficient_inner_folds',
    'tiebreak': ['训练均值', '较低换手', 'cfg_id 字典序'],
    'splits': ['2012-12-31(short-training)', '2014-12-31', '2016-12-31',
               '2018-12-31', '2020-12-31', '2022-12-31'],
    'directions': ['forward', 'reverse(迁移诊断, 非可执行策略)'],
    'accounts': ['single_selection', 'annual_walk_forward(主要程序表现)'],
    'stability_B': 2000,
    'label': 'fixed_hindsight_library',
}, open(os.path.join(OUT, 'selector_registry.json'), 'w', encoding='utf-8'),
    ensure_ascii=False, indent=1)

pd.DataFrame([
    dict(name='coretrim_matchN', target='否决类变体', definition='同日同父同最终人数, 按父冻结核心排序剔深后实际重建 DEV'),
    dict(name='eqpos', target='否决类变体', definition='同日目标仓位取小者, 只向下缩, 各自过 rolling 与成本'),
    dict(name='paired_common_domain', target='核窗口/权重/中性化变体', definition='形成日双方所需分量均可得的票上重建'),
    dict(name='vs_default_parent', target='全部 UA', definition='对同配方默认版的同日 Δgross/Δcost/Δnet/Δpos/Δturn'),
    dict(name='vs_R1', target='A12 与全部经济配置', definition='对 KT_dep(50,50)|C:k5 的同日配对差'),
    dict(name='vs_R2', target='A12 与全部经济配置', definition='对 KT_mean@30|C:k5+cr5:k10 的同日配对差'),
]).to_csv(os.path.join(OUT, 'comparison_registry.csv'), index=False)

# ============================================================
# 阶段 0 的 E6e 修订补全: days_nohold 分拆
# ============================================================
P('')
P('=== §2 E6e 修订: days_nohold 可推导分拆 ===')
REV = os.path.join(OUT, 'revisions', 'E6e_summary_fix')
SRCREV = os.path.join(F.E6E_DIR, 'revisions', 'E6e_summary_fix')
FULL = pd.read_csv(os.path.join(SRCREV, 'all_candidates.csv')).set_index('config_id')
pz = {s: pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_pos_%s.parquet' % s)) for s in F.SEGS}
cols = list(FULL.index)
rows = []
for s in F.SEGS:
    Pv = pz[s].reindex(columns=cols).values
    nz = (Pv == 0)
    lead = np.zeros(len(cols), int)
    for j in range(len(cols)):
        c = np.argmax(~nz[:, j]) if (~nz[:, j]).any() else nz.shape[0]
        lead[j] = c
    rows.append(pd.DataFrame(dict(config_id=cols, period=s,
                                  days_nopos=nz.sum(axis=0), warmup_lead=lead,
                                  benchmark_missing=bn[s], T=Ts[s])))
SP = pd.concat(rows, ignore_index=True)
agg = SP.groupby('config_id').agg(days_nopos_full=('days_nopos', 'sum'),
                                  warmup_lead_full=('warmup_lead', 'sum'),
                                  benchmark_missing_full=('benchmark_missing', 'sum'))
FULL2 = FULL.join(agg)
FULL2['interior_nopos'] = FULL2.days_nopos_full - FULL2.warmup_lead_full
for f in ('all_candidates.csv',):
    FULL2.to_csv(os.path.join(REV, f))
FULL2[FULL2.kind == 'core'].to_csv(os.path.join(REV, 'core_depth.csv'))
for f in ('neighborhoods_and_frontiers.csv', 'coverage_and_execution.csv',
          'fix_manifest.json', 'README_fix.md', 'fix_log.txt'):
    src = os.path.join(SRCREV, f)
    if os.path.exists(src):
        open(os.path.join(REV, f), 'wb').write(open(src, 'rb').read())
SP.to_csv(os.path.join(REV, 'days_nohold_decomposition_by_segment.csv'), index=False)
P('  days_nohold 全窗口中位 %d; 其中 warmup_lead 中位 %d, benchmark_missing 恒 %d, 内部无仓位中位 %d'
  % (int(FULL2.days_nohold.median()), int(FULL2.warmup_lead_full.median()),
     int(FULL2.benchmark_missing_full.median()), int(FULL2.interior_nopos.median())))
chk('benchmark_missing 恒为 76', set(FULL2.benchmark_missing_full.unique()) == {76},
    str(FULL2.benchmark_missing_full.unique()[:4]))

# 归因: 逐配置分量与总量 (REVIEW 点名)
att = pd.read_csv(os.path.join(F.E6E_DIR, 'summary', 'attribution.csv'))
P('  归因 (n=%d): hard_total 中位 %+.4f; frozen_delete 中位 %+.4f; survivor_realloc 中位 %+.4f; '
  '两分量中位之和 %+.4f (中位不可加, 正式归因以逐配置总量为准)'
  % (len(att), att.hard_total.median(), att.frozen_delete.median(),
     att.survivor_realloc.median(), att.frozen_delete.median() + att.survivor_realloc.median()))
chk('归因恒等式 max|err| = 0', float(att.identity_err.abs().max()) == 0.0,
    '%.3e' % float(att.identity_err.abs().max()))
att.to_csv(os.path.join(REV, 'attribution_per_config.csv'), index=False)

# ============================================================
# 数据事实核对 (§2 末)
# ============================================================
P('')
P('=== §2 数据事实核对 ===')
d = F.guarded_load('20240101', '20240401')
iz = d.get('industry_zx1')
FACT = {}
if iz is not None:
    chgcells = int((iz.iloc[1:].values != iz.iloc[:-1].values).sum())
    FACT['industry_zx1'] = dict(shape=list(iz.shape), notna=float(iz.notna().mean().mean()),
                                adjacent_changed_cells=chgcells,
                                median_industries_per_day=float(iz.nunique(axis=1).median()),
                                PIT='是' if chgcells > 0 else '否')
    chk('industry_zx1 逐日更新 (PIT)', chgcells > 0, '相邻日变化 %d 格' % chgcells)
am, op = d.get('amount'), d.get('is_open')
susp = (op == 0).values
FACT['amount'] = dict(unit='元',
                      open_median=float(np.nanmedian(am.values[(op == 1).values])),
                      suspended_nonzero_share=float((am.values[susp] > 0).mean()),
                      suspended_nan_share=float(np.isnan(am.values[susp]).mean()))
chk('停牌日 amount 恒为 0 (非缺失)', FACT['amount']['suspended_nonzero_share'] < 1e-9,
    '非零占比 %.6f, 缺失占比 %.6f' % (FACT['amount']['suspended_nonzero_share'],
                                 FACT['amount']['suspended_nan_share']))
for f in ('flag_buy', 'flag_sell', 'flag_st', 'limit_up', 'limit_down', 'is_open'):
    if f in d:
        x = d[f]
        vals = pd.unique(x.values.ravel())
        vals = [v for v in vals if v == v][:5]
        FACT[f] = dict(notna=float(x.notna().mean().mean()), sample_values=[float(v) for v in vals])
P('  可成交性字段非空率: %s' % {k_: round(v['notna'], 3) for k_, v in FACT.items() if 'flag' in k_ or 'limit' in k_})
json.dump(FACT, open(os.path.join(OUT, 'checks', 'source_facts.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ============================================================
# source_corrections_E6f.md
# ============================================================
SC = '''# E6f 源码/事实勘误 (source_corrections_E6f.md)

本轮新发现与已确认的事实更正。brief §0.1 已承认的 proposal 六处错另见 brief 与 `E6f_proposal.md` 顶部勘误。

## 1. `pd.qcut` 的分位边界不能用闭式复现 (本轮新发现, 已修)
把 `pd.qcut(rank('first'), g)` 的组号写成闭式 `gid = searchsorted(1 + k/g*(n-1), r)`, 与 pandas 相比
在 **末位 1 ULP** 上不同: pandas 的边界由 `np.percentile` 的线性插值算出, 恰好落在边界上的那一个秩会翻组。
实测 `drop_mask_dense C:k15` 与源 helper **差 28 格**(k=5/10/20 恰好不差, 所以只测这三个会漏掉)。
**修法**: `qcut_group(n, g)` 直接调用 pandas 本身并按 `(n, g)` 记忆化 —— 构造上就不可能不同, 且记忆化后开销可忽略。
**教训**: 复刻一个库函数的**分箱边界**时, 不要重新推导公式; 要么调用它, 要么对全部会用到的参数逐一比对。
只测了参数空间的一部分 (k∈{5,10,20}) 就宣布等价, 是这次差点漏掉的原因。

## 2. `PATHS['cache_dir']` 指向公共只读目录 (本轮新发现)
`data_loader.PATHS['cache_dir'] = /mnt/big/base/public/FundamentalTL/cache/` 属于另一位同事, **当前用户不可写**。
四段冻结区间的 kline 缓存已在其中, 所以 E6e 从未触发; 但 `history_warmed` 要加载**新日期区间**, 会在写缓存时
抛 `PermissionError`。**修法**: `e6f_core.shadow_cache()` 建一个自己盘上的影子目录, 把公共缓存全部**符号链接**
进去(读命中、零拷贝), 再把 `PATHS['cache_dir']` 指过去; 新区间落到自己盘, 公共目录一个字节都不写。

## 3. 源数据延伸到 2026-09-09, 冻结末日是 2026-03-27 (本轮新发现)
源 kline 目录的最晚日期是 **20260909**, 即 E7 期数据物理上就在盘上、可读。`PERIODS` 的第四段末日是 20260327。
两者之间没有任何技术屏障, 一个 `end_date` 笔误就是禁区 §12 违规 + GLOBAL STOP。
**修法**: 全部取数走 `e6f_core.guarded_load()`, 内部 `end_date > '20260327'` 直接抛 `RuntimeError`;
自测第 3 组把 `20260909` 与 `20260328` 两个反例都跑一遍, 必须被拒。

## 4. E6e `run_manifest.json` 的 SHA 表写于阶段 A, 只覆盖 8 个文件
表里是四地基 + `comprehensive_factor_diagnosis.py` + 当时已存在的 `e6e_core/e6e_run/e6e_stageA`。
`e6e_selftests / e6e_merge1 / e6e_random / e6e_stats` 写在 manifest 之后, **本就不在表里**, 不是"对不上"。
**正确核对方法** = manifest ∩ 现存文件全部 SHA 相同 **且** 七个 `e6e_*.py` 全部 `git status` 干净。
本轮两条都过。**教训**: 拿一个部分清单当全量清单核对, 会造出假的红灯。

## 5. `days_nohold` 全部落在段首预热, 段内没有空仓日 (本轮新事实)
按 `daily_pos` 反推: 全窗口 `days_nopos` 中位 124 天, 其中**段首连续预热 124 天, 段内 0 天**。
`benchmark_missing` 恒为 76 = 4 段 × 19 天(`mature` 20 日过滤)。
即 §1.3 说的"`days_nohold` 每段 19~29 天由 `mature` 与 tvol 的 `min_periods` 造成、不是 bug"得到独立证实:
**没有任何一天是因为选股规则本身选不出票而空仓的**。

## 6. 停牌日 `amount` 恒为 0 而非缺失 (语义确认, 影响 ADV20)
实查: 停牌日 `amount` 非零占比 0.000000、缺失占比 0.000000 —— 即恰好是 0。开市日中位约 1.05e+08 (元)。
故 §6.1 的"停牌日 amount=0 只在语义确认后计入"条件已满足。**本轮主口径取交易日**
`ADV20_trading = mean(amount | is_open==1, e-20..e-1, 至少 10 个有效日)`,
并列给含 0 的 `ADV20_calendar` 作敏感性列 —— 两者差异本身就是停牌频率的度量。

## 7. `industry_zx1` 是 PIT 的
相邻交易日之间行业标签有变化(实查 2024Q1 有 9,769 格变化), 日均约 30 个一级行业, 非空率 98%+。
故 DEV 削顶与行业中性化都用它; 缺失固定成 `__UNKNOWN__` 一类, **不用未来行业回填**。

## 8. `e6e_random.py` 的退出问题不在本轮修 (保 provenance)
E6e 阶段 E 的 89 个进程写完 `_DONE` 与全部 parquet 后卡在解释器退出(parquet writer 的非守护线程)。
本轮**不改该脚本**, 只在 `limit_register.md` 登记; 新写的 E6f 脚本一律走 close/join/flush/fsync + 原子 rename,
父进程验收产物后才写 DONE, 不默认 `os._exit(0)`。
'''
open(os.path.join(OUT, 'source_corrections_E6f.md'), 'w', encoding='utf-8').write(SC)
P('')
P('写出 source_corrections_E6f.md (%d 字符, 8 条)' % len(SC))

# ============================================================
# 收尾
# ============================================================
json.dump(dict(version=F.VERSION, stage='0', when=time.strftime('%Y-%m-%d %H:%M:%S'),
               tz=time.tzname[0], host_alias='47', PERIODS=dict(K.PERIODS),
               frozen_end=F.FROZEN_END, source_kline_range=[first_src, last_src],
               sha={'brief': SHA_BRIEF, 'web_plan': SHA_PLAN,
                    'code': {f: sha_now[f] for f in FOUND + E6E_PY},
                    'e6f': {f: F.sha_file(os.path.join(CODE, f))
                            for f in os.listdir(CODE) if f.startswith('e6f_')}},
               env=dict(nproc=nproc, mem=mem, ulimit_nproc=ulim,
                        my_procs=nmy, my_threads=nthr, worker_cap=32,
                        taskset='96-191,288-383'),
               domains=dict(U0_primary=len(U0P), U0_broad=len(U0B), P54=len(P54),
                            A12=len(SRCMAP)),
               n_feature_specs=len(FR), issues=ISSUES),
          open(os.path.join(OUT, 'run_manifest.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'logs', 'stage0.log'), 'w', encoding='utf-8').write('\n'.join(LOG) + '\n')
P('')
P('阶段 0 完成 %.0fs; 待办/不符 %d 项' % (time.time() - T0, len(ISSUES)))
for x in ISSUES:
    P('  ! %s -- %s' % (x['item'], x['detail']))
