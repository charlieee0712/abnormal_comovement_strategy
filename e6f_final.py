#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 收尾: 写 limit_register.md 与 study_manifest.json (§11 硬交付项)。
   在全部阶段跑完后执行 —— 它读 checks/ 与产物本身, 不重算任何数字。
   用法: python e6f_final.py --out DIR
"""
import os, sys, json, time, glob, hashlib, argparse
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6f_core as F
import e6f_desc as D

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
A = ap.parse_args()
OUT = A.out
SRC = '/mnt/sda2/lichenchen/code/project_core'
BRIEF = '/mnt/sda2/lichenchen/exec_briefs_in/E6f_construction_selection.md'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def jread(p):
    try:
        return json.load(open(os.path.join(OUT, 'checks', p), encoding='utf-8'))
    except Exception:
        return None


def nrows(p):
    q = os.path.join(OUT, p)
    try:
        return len(pd.read_csv(q))
    except Exception:
        return None


# ============================================================
# limit_register.md
# ============================================================
LIM = [
    # (id, 级别, 触发条件, 实际发生了什么, 影响范围, 处置)
    ('L01', 'LIMIT', '某段源数据没有更早日期, history_warmed 无法预热',
     '2010-2014 段源 kline 最早日 = 段首日 (20100104)。脚本跑完段构建后如实写标签并退出',
     '该段只有 legacy_all 一个支持集; 支持集对照表少一行',
     '`checks/warm_2010-2014__history_warmed.json` status=LIMIT; brief §0.1 已预授权'),
    ('L02', 'LIMIT', 'history_warmed 下可预热的源历史不足以填满最长窗',
     '2015-2018 预热后仍有 339/4,602 个配置停在 23~25 个无持仓日 (其余 4,263 个落回地板 19)',
     '仅影响支持集对照表的读法, 不影响 legacy_all 主口径',
     '在 `A_oat/support_compare.csv` 与 merge2 日志里逐段列出取值分布'),
    ('L03', 'LIMIT', 'E6e 未存逐日 nh, days_nohold 的严格四分拆不可得',
     '改出可推导的四列 days_nopos / warmup_lead / benchmark_missing / interior_nopos',
     'Q7 的 days_nohold 分解只到这四列', '`revisions/E6e_summary_fix/`; part1 已写明'),
    ('L04', 'LIMIT', 'live_nh (5 批叠加后的实际持股数) 需重建全部 20,282 配置的逐日 mask',
     '与本轮其余部分不成比例 (= 重跑 E6e 阶段 B-D)',
     '`avg_nh` 一律标为 target_nh; live_nh 只在 C1 画像覆盖范围内给出',
     'part1 已写明; C1 `profile_*.csv` 的 names 列标注'),
    ('L05', 'LIMIT', 'A4b_CVRv5 是 v2 形态, 不在 E6f 描述符空间内',
     '无法在本核重建该形态, 因此 §9 的 E6c 持有期锚不能是"重算出同一个数"',
     '该锚改为【用 E6c 存档日序列重算, 核对年化与净额口径一致】: 20 格 max|d| 1.8e-15; '
     '持有期机制本身另在自测组 4 对生产引擎逐 H(1,2,3,4,5,7,10) 锚, max|d| 2.9e-14',
     '`checks/e6c_horizon_anchor.csv` + `checks/selftests_*.csv`'),
    ('L06', 'LIMIT', 'E6e `run_manifest.json` 的 SHA 表写于阶段 A, 只覆盖 8 个文件',
     '四个更晚写的 e6e 脚本从未进过该表, 首轮误判成 "3/7 不符"',
     '验收判据改为「manifest ∩ 现存文件全部 SHA 相符 且 七个文件 git 全部干净」= 8/8 + clean',
     '`source_corrections_E6f.md` §4'),
    ('L07', 'LIMIT', '`e6e_random.py` 的解释器退出卡死不在本轮修 (保 provenance)',
     'E6e 阶段 E 的 89 个进程写完产物后卡在退出 (parquet writer 非守护线程)',
     '不影响 E6f: 新脚本一律 close/join/flush/fsync + 原子 rename, 父进程验收后写 DONE',
     '`source_corrections_E6f.md` §8'),
    ('L08', 'LIMIT', '真实股数 / 现金分红分支需要分红数据',
     '源里没有分红数据', 'C2 影子账户只做【调整单位的总收益代理账】主版本',
     'brief §6.2 已预授权; coverage 标 unavailable'),
    ('L09', 'DEFERRED', 'k15/k20 的确切人数预算诊断 (m = ceil(n_valid/k))',
     '本轮只跑源 helper 原生版', '不影响 k 平台的 net/turn 读数',
     '≥3k 门槛已由自测第 7 组 thin-day 验证 (违例 0 天)'),
    ('L10', 'DEFERRED', 'H 分支的 E6c 三项分解 (legacy / common_mature / 日龄桥)',
     '需重跑 E6c 口径', 'Q6 只出 H 分支的 net/turn/pos 与对 H5 的差',
     'E6c 原表的三项分解仍可直接引用'),
    ('L11', 'DEFERRED', '邻域的 mask Jaccard 与目标权重 L1',
     '需为约 1.8 万对邻居各重建两套掩码', '邻域的收益侧度量已全出 (Δnet8/Δpu_net/容忍带)', '—'),
    ('L12', 'DEFERRED', '否决选择回放 (每源父核选 Δ_vs_coretrim_matchN 最大的否决规则)',
     'coretrim_matchN 日账本已产 (每段 1,462 条) 但按父核的回放本轮未做',
     '不影响 S1-S6 / S_meta 主回放', '—'),
    ('L13', 'DEFERRED', 'cond 的逐票 / 行业分层成分归因与单调性五组',
     '本轮出的是同日配对差的逐年/逐段面板 (`B_yearly/cond_heterogeneity.csv`)',
     'Q5 的结构维 (核 / 深度 / 否决 / 阶段结构) 由块 A 的权重-深度-k 三层给出; 成分维缺',
     '—'),
    ('L14', 'DEFERRED', 'RW (Romano-Wolf) 调整 p 值附列',
     '实现未经验证, brief §7 只作可选附列',
     '多重检验用 bootstrap 同时带 (逐点 + 同时) 代替', 'brief §7 允许'),
    ('L15', 'WARN', 'history_warmed 下的锚与 E6e 账本不逐位相同',
     '63 个锚只有 12 个相同, max|d| 约 0.96',
     '这是【预期】: E6e 账本本身是 legacy_all 口径, 预热改了因子可见历史; '
     '相同的 12 个正是核里没有长窗因子的那些',
     '主口径锚 legacy_all 四段各 63/63、max|d| = 0.000e+00'),
    ('L16', 'LIMIT', 'E6e 的 P2G 分位映射没有深度 15',
     '首轮 4 个 KTC_mean@15 配置 KeyError: 15',
     '在 `e6f_core.P2G` 按生成 P2G 其余条目的同一规则补 15->g=20 并单独补跑 '
     '(`*_fix15.parquet` / `*_fix15.csv`), **不改 e6e_core**',
     '规则已对 20/25/30/35/40/50/75 逐个回验'),
]
rows = []
for i, (lid, lv, cond, what, scope, how) in enumerate(LIM):
    rows.append('| %s | %s | %s | %s | %s | %s |' % (lid, lv, cond, what, scope, how))
LR = ('# E6f LIMIT / WARN 登记表\n\n'
      '生成时间 %s。级别定义见 brief §9: GLOBAL STOP / MODULE STOP / LIMIT・WARN / 合法研究结果。\n'
      '**本轮无 GLOBAL STOP, 无 MODULE STOP。**净值下降、近段差、未超 R2、联合带跨零、'
      '低容量、邻域不平等一律是合法研究结果, 不进本表。\n\n'
      '| id | 级别 | 触发条件 | 实际发生 | 影响范围 | 处置与证据 |\n'
      '|---|---|---|---|---|---|\n%s\n'
      % (time.strftime('%Y-%m-%d %H:%M:%S'), '\n'.join(rows)))
open(os.path.join(OUT, 'limit_register.md'), 'w', encoding='utf-8').write(LR)
print('写出 limit_register.md: %d 条 (LIMIT %d / DEFERRED %d / WARN %d)'
      % (len(LIM), sum(1 for x in LIM if x[1] == 'LIMIT'),
         sum(1 for x in LIM if x[1] == 'DEFERRED'), sum(1 for x in LIM if x[1] == 'WARN')))

# ============================================================
# study_manifest.json
# ============================================================
scripts = {}
for p in sorted(glob.glob(os.path.join(SRC, 'e6f_*.py'))):
    scripts[os.path.basename(p)] = dict(sha256=sha(p),
                                        lines=sum(1 for _ in open(p, encoding='utf-8')),
                                        bytes=os.path.getsize(p))
cf = D.gen_all()
layers = {}
for c in cf:
    layers[c['layer']] = layers.get(c['layer'], 0) + 1

stages = {}
for p in sorted(glob.glob(os.path.join(OUT, 'checks', '*.json'))):
    try:
        d = json.load(open(p, encoding='utf-8'))
        if isinstance(d, dict) and 'seconds' in d:
            stages[os.path.basename(p)[:-5]] = round(float(d['seconds']), 1)
    except Exception:
        pass

st = {}
for p in sorted(glob.glob(os.path.join(OUT, 'checks', 'selftests_*.json'))):
    d = json.load(open(p, encoding='utf-8'))
    st[os.path.basename(p)[:-5]] = dict(n=d.get('n'), n_fail=d.get('n_fail'))

anchors = {}
for p in sorted(glob.glob(os.path.join(OUT, 'checks', 'anchors_*.csv'))):
    d = pd.read_csv(p)
    cs = [c for c in ('d_gross', 'd_turn', 'd_pos') if c in d.columns]
    anchors[os.path.basename(p)[8:-4]] = dict(
        n=len(d), n_ok=(int(d.ok.sum()) if 'ok' in d.columns else None),
        max_abs=(float(np.nanmax(np.abs(d[cs].values))) if cs else None))
ea = os.path.join(OUT, 'checks', 'e6c_horizon_anchor.csv')
if os.path.exists(ea):
    d = pd.read_csv(ea)
    anchors['E6c_horizon_A4b_CVRv5'] = dict(n=len(d), n_ok=int((d.d_abs < 1e-10).sum()),
                                            max_abs=float(d.d_abs.max()))

MAN = dict(
    study='E6f_construction_selection',
    version=F.VERSION,
    generated=time.strftime('%Y-%m-%d %H:%M:%S'),
    run_dir=os.path.basename(OUT.rstrip('/')),
    frozen_end=F.FROZEN_END,
    brief_sha256=(sha(BRIEF) if os.path.exists(BRIEF) else None),
    copies={n: (sha(os.path.join(OUT, n)) if os.path.exists(os.path.join(OUT, n)) else None)
            for n in ('brief_copy.md', 'PLAN_COPY.md', 'preregistration.md',
                      'engine_contract.md', 'source_corrections_E6f.md', 'limit_register.md')},
    scripts=scripts,
    upstream=dict(E6e=F.E6E_DIR, E6c=F.E6C_DIR),
    segments={s: dict(days=int(len(pd.read_parquet(
        os.path.join(OUT, 'daily', 'A_gross_%s__legacy_all.parquet' % s)).index))
        if os.path.exists(os.path.join(OUT, 'daily',
                                       'A_gross_%s__legacy_all.parquet' % s)) else None,
        supports=sorted(set(os.path.basename(x).split('__')[1][:-8]
                            for x in glob.glob(os.path.join(
                                OUT, 'daily', 'A_gross_%s__*.parquet' % s))
                            if '_fix15' not in x)))
        for s in F.SEGS},
    engine=dict(hold=5, cost_bp_bilateral=F.COST, cost_bp_high=F.COST_HI,
                exec_lag=1, adjust=True, max_stock=0.01, max_ind_dev=0.03,
                annualize='252 x 100 x mean(有效日)'),
    descriptors=dict(total=len(cf), by_layer=layers,
                     primary_H5=sum(1 for c in cf if c['H'] == 5)),
    products=dict(
        A_full_window=nrows('A_oat/A_full_window.csv'),
        neighborhood=nrows('neighborhoods/neighborhood_metrics.csv'),
        selected_sets=nrows('B_nested/selected_sets.csv'),
        policy_readout=nrows('B_walkforward/policy_readout.csv'),
        selection_stability=nrows('B_selection_stability/selection_stability.csv'),
        bootstrap_families=nrows('D_bootstrap/bootstrap_families.csv'),
        cond_heterogeneity=nrows('B_yearly/cond_heterogeneity.csv'),
        e6c_horizon_anchor=nrows('checks/e6c_horizon_anchor.csv'),
        support_compare=nrows('A_oat/support_compare.csv'),
        coverage=nrows('coverage.csv')),
    selftests=st,
    anchors=anchors,
    stage_seconds=stages,
    limits=[dict(id=x[0], level=x[1], trigger=x[2]) for x in LIM],
    boundaries=['不读 %s 之后的真实数据' % F.FROZEN_END, '不开 E7',
                '不改 I11 / pool0 / clean 历史成员', '不改生产 DEV 与 v2 交付',
                '研究变体 (中性化 / 复权 B / H≠5 / 影子账户) 不升格生产'],
)
json.dump(MAN, open(os.path.join(OUT, 'study_manifest.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('写出 study_manifest.json: %d 个脚本, %d 个描述符, %d 个阶段计时'
      % (len(scripts), len(cf), len(stages)))
for k, v in sorted(anchors.items()):
    print('  锚 %-32s n=%-4s max|d|=%s' % (k, v['n'], v['max_abs']))
