#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6e 阶段 A: 四件注册表 + 事前登记 + run_manifest。用法: python e6e_stageA.py --out DIR"""
import os, sys, json, platform, argparse, hashlib
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K

ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
OUT = ap.parse_args().out
for d in ('daily', 'random_daily', 'logs', 'checks', 'summary', 'bootstrap'):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

cores = K.core_descriptors(); twins = K.twin_descriptors(cores)
hard = K.hard_veto_descriptors(); comp = K.composite_veto_descriptors()
exem = K.exemption_veto_descriptors(); soft = K.soft_descriptors()
P54 = [c['core_id'] for c in cores if c['set'] == 'P54']

# ---- 1. config_registry ----
rows = []
for d in cores + twins:
    rows.append({k: v for k, v in d.items()})
cfg = pd.DataFrame(rows)
cfg['status'] = 'PLANNED'
cfg.to_csv(os.path.join(OUT, 'config_registry.csv'), index=False)

# ---- 2. veto / comparison registry ----
vr = []
for v in hard: vr.append(dict(veto_id=v['veto_id'], kind=v['kind'], scope='P114',
                              legs=';'.join('%s:k%d' % (f, k) for f, k in v['legs'])))
for v in comp: vr.append(dict(veto_id=v['veto_id'], kind=v['kind'], scope='P54',
                              legs=';'.join('%s:k%d' % (f, k) for f, k in v['legs']), how=v['how']))
for v in exem: vr.append(dict(veto_id=v['veto_id'], kind=v['kind'], scope='P54',
                              legs=v['start'], how='exempt_top%d' % v['q']))
for v in soft: vr.append(dict(veto_id=v['veto_id'], kind=v['kind'], scope='P54',
                              legs=v['start'], how='%s lam=%.2f' % (v['mode'], v['lam'])))
pd.DataFrame(vr).to_csv(os.path.join(OUT, 'veto_registry.csv'), index=False)

comps = [
    dict(name='coretrim_matchN', target='每个真实子配置', definition='父核内按冻结末级质量分保留恰好 r_t 只'),
    dict(name='reverse', target='P114 x 12 单否决', definition='同父同有效域剔最好 m_t 只 (m_t = 正向已知毒尾数)'),
    dict(name='equal_position', target='全部子配置(含软覆盖层)', definition='W0_down=W0*min(1,P1/P0), W1_down=W1*min(1,P0/P1); P=当日权重和'),
    dict(name='known_only', target='全部硬否决', definition='只剔已知毒尾, 不可判断者留在父中'),
    dict(name='allocation_matchN', target='三种两阶段 x q x a', definition='共同可观察域上 r_t=ceil(q|U_t|), 只作诊断'),
    dict(name='relative_vs_pool', target='P54 x {C,cr5,cr20}', definition='pool0分位 / 父内固定 / 父内同 m / 父内重中性化同 m 四种'),
]
pd.DataFrame(comps).to_csv(os.path.join(OUT, 'comparison_registry.csv'), index=False)

# ---- 3. randomization_registry ----
rnd = dict(version=K.VERSION, profiles=['U-IID', 'I-IID', 'I-P5'], soft_extra_profile='I-P20',
           paths=128, escalate=[256, 512], escalate_trigger='MCSE > 0.10 点 (年化 gross 或 net 随机均值)',
           ar_rho={'I-P5': float(np.exp(-1.0 / 5)), 'I-P20': float(np.exp(-1.0 / 20))},
           n_rules=len(cores) * len(hard) + len(P54) * (len(comp) + len(exem)),
           key_scheme='SHA256(VERSION|profile|seed|date) -> u64, 再对冻结票码表做向量化 64 位混合器 '
                      '(采纳调整 1: 逐元素 SHA256 需 1.52 亿次/段; 性质等价, 验收见玩具测试第 6 组)',
           nested='同父不同 m 共用优先级', forbid_python_hash=True,
           per_path_cost=True, analytic_gross_for='I-IID')
json.dump(rnd, open(os.path.join(OUT, 'randomization_registry.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ---- 4. analysis_families ----
fam = dict(F1='全部经济配置 vs R1 (A4b_CVRv5@H5), 8bp 与 12bp',
           F2='全部经济配置 vs R2 (M_mean2@keep30|CVR_20d:k5+cum_return_5d:k10@H5)',
           F3='真实规则 vs 对应随机均值 (按 profile)',
           F4='真实 vs coretrim_matchN',
           F5='软 vs 自身硬与无否决两个端点',
           bootstrap=dict(kind='stationary', block=60, block_sens=20, B=2000, by_segment=True,
                          shared_date_draw=True),
           hac=dict(main_L=5, sens_L=[20, 60], gap='score-HAC (缺失处 u=0)',
                    cols=['nw_full_concat', 'nw_full_fixedmix']),
           two_level='对 F3 与软起点: 先有放回抽 seed 编号再抽日期')
json.dump(fam, open(os.path.join(OUT, 'analysis_families.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ---- 事前登记 ----
PRE = u"""# E6e 事前登记 (preregistration)

登记日期 **2026-09-06**，写于阶段 B 的第一次正式收益评价之前（阶段 A）。一经写出不再修改；
如需修订另起 `preregistration_amend_<日期>.md`。对应 brief `E6e_architecture.md`（v1）。

## 0. 问题
在既有 I11 候选域与 DEV 资金约束下，底座怎样筛、否决怎样用，才能改善当前完整策略的净表现；
观察到的改善分别来自股票成分、资本使用、行业结构还是交易成本。**本轮只出地图与账，不定 v3。**

## 1. 六个开放式问题（web §2K 的 H1–H6，事前写死，不预设方向）
- **H1** 否决层相对"同人数剔深"（`coretrim_matchN`）是否还有增量？增量在四段上是否同号？
- **H2** 否决的增量里，多少来自剔掉的股票本身（成分），多少来自仓位下降/资本再配置（DEV 在 n<100 区剔票即降仓位）？
- **H3** 相对随机剔除同样人数（三种 profile），真实否决的增量是多少？反向否决（剔最好）是否也为正？
- **H4** 组内相对否决与池级绝对否决，哪种在同一父核上更好？差是否随核的浓度变化？
- **H5** 软否决（冻权降权 WS / 父—硬插值 WB）相对两个端点是否存在中间更优点？成本是否非线性？
- **H6** 核族 × 深度 × 否决三维上，非支配集合长什么样？是否存在近邻平台（邻域内表现相近）？

## 2. 对照定义（事前）
`coretrim_matchN`、`reverse`（同 m 剔最好）、`equal_position`（双边只向下缩）、`known_only`（三值逻辑）、
`allocation_matchN`（同预算，仅诊断）、`relative_vs_pool`（四种实现）。定义见 `comparison_registry.csv`。

## 3. 随机对照
三种 profile（U-IID / I-IID / I-P5）各 128 路径，软起点另 I-P20；全部 3,570 条规则统一覆盖，不按核族分层。
`increment_vs_random = Y_child − mean_b(Y_random,b)`；`random_design_tail_fraction` **不是 p 值**。
MCSE > 0.10 点才追加至 256/512。I-IID 的解析期望 gross 作对账与 gross 主估计，成本只用路径。

## 4. 比较族与两个固定参照
F1–F5 见 `analysis_families.json`。R1 = `A4b_CVRv5@H5`（生产终形态）；R2 = `M_mean2@keep30|CVR_20d:k5+cum_return_5d:k10@H5`。

## 5. 判据（只对正确性设硬条件）
外部源锚 TOL 0.02 且报所有非零差；内部锚 `KT_dep(50,50)`=A4b、`KT_mean@50`=M_mean2（软锚）；
批量/稀疏内核 vs 参考引擎逐日 atol 1e-12；会计恒等式同表同掩码。
**收益、z、区间、某段弱都不是 BLOCKER；不要求产生改进配置。**

## 6. 结果怎么读（事前）
- 若否决相对 `coretrim_matchN` 与随机对照都无稳定增量 → 否决层的价值主要是"切得更深"与"降仓位"，不是选股。
- 若相对增量为正但反向否决也为正 → 增量来自浓度/仓位而非毒尾识别。
- 若相对增量为正且反向为负、且四段同号 → 毒尾识别本身有价值。
三种都是合法答案。本轮不设盈利闸门、不按中途结果淘汰、不下采纳结论。
"""
open(os.path.join(OUT, 'preregistration.md'), 'w', encoding='utf-8').write(PRE)

CORE = '/mnt/sda2/lichenchen/code/project_core'
BR = '/c/Users/cnc/resonance_strategy/exec_briefs'
mani = dict(written='2026-09-06', version=K.VERSION, python=platform.python_version(),
            numpy=np.__version__, pandas=pd.__version__,
            periods={k: list(v) for k, v in K.PERIODS.items()},
            cost_bp=K.COST, cost_hi=K.COST_HI, hold=K.HOLD, exec_lag=K.EXEC_LAG, adjust=K.ADJUST,
            p2g=K.P2G, factors=K.FACTORS, high_bad={f: bool(K.HB[f]) for f in K.FACTORS},
            n_cores=len(cores), n_twins=len(twins), n_hard=len(hard), n_composite=len(comp),
            n_exempt=len(exem), n_soft=len(soft),
            n_rules_random=len(cores) * len(hard) + len(P54) * (len(comp) + len(exem)),
            sha={os.path.basename(p): K.sha_file(p) for p in [
                os.path.join(CORE, x) for x in ('e6e_core.py', 'e6e_run.py', 'e6e_stageA.py',
                                                'comprehensive_factor_diagnosis.py', 'data_loader.py',
                                                'features_daily.py', 'event_study.py',
                                                'pool_screening_v2.py')]},
            sha_inputs={'roles.csv': K.sha_file(os.path.join(K.E6_DIR, 'roles.csv')),
                        'e6b_scan_all.csv': K.sha_file(os.path.join(K.E6B_DIR, 'scan_all.csv')),
                        'e6d_full_summary.csv': K.sha_file(os.path.join(K.E6D_DIR, 'full_summary.csv'))})
json.dump(mani, open(os.path.join(OUT, 'run_manifest.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('阶段 A 完成 ->', OUT)
print('  config_registry %d 行; veto_registry %d 行; 随机规则数 %d'
      % (len(cfg), len(vr), mani['n_rules_random']))
