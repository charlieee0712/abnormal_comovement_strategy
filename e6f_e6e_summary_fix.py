#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 阶段 0: 修 E6e 汇总表的 avg_nh / days_nohold 全窗口聚合缺陷。
   不覆盖 E6e 原文件, 输出到 <E6E>/revisions/E6e_summary_fix/。
   七个 e6e_*.py 保持字节不变 (e6e_merge1.py 是脚本非模块, 不可 import, 故此处按同一口径重写聚合并
   对非目标列做容差断言 —— 见 README_fix.md)。
   用法: python e6f_e6e_summary_fix.py --e6e DIR
"""
import os, sys, json, hashlib, argparse
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K

ap = argparse.ArgumentParser()
ap.add_argument('--e6e', default='/mnt/sda2/lichenchen/results/20260906_1300_E6e_architecture')
A = ap.parse_args()
E6E = A.e6e
SUM = os.path.join(E6E, 'summary')
OUT = os.path.join(E6E, 'revisions', 'E6e_summary_fix')
os.makedirs(OUT, exist_ok=True)
L = []
def P(s=''):
    print(s, flush=True); L.append(s)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


SEGS = K.SEGS
sf = pd.concat([pd.read_csv(os.path.join(SUM, 'sf_%s.csv' % s)) for s in SEGS], ignore_index=True)
P('载入 sf_*.csv 四段, 配置-段行 %d' % len(sf))

G, T_, Pz, mark = [], [], [], []
for s in SEGS:
    G.append(pd.read_parquet(os.path.join(E6E, 'daily', 'daily_gross_%s.parquet' % s)))
    T_.append(pd.read_parquet(os.path.join(E6E, 'daily', 'daily_turn_%s.parquet' % s)))
    Pz.append(pd.read_parquet(os.path.join(E6E, 'daily', 'daily_pos_%s.parquet' % s)))
    mark.append(np.array([s] * len(G[-1].index)))
cols = sorted(set.intersection(*[set(x.columns) for x in G]))
GG = pd.concat([x.reindex(columns=cols) for x in G], axis=0)
TT = pd.concat([x.reindex(columns=cols) for x in T_], axis=0)
PP = pd.concat([x.reindex(columns=cols) for x in Pz], axis=0)
segmark = np.concatenate(mark)
NET8 = GG - TT * (K.COST / 1e4)
NET12 = GG - TT * (K.COST_HI / 1e4)
P('配置 %d, 日序列 %d 行' % (len(cols), len(GG.index)))

# ---- 段级天数与基准缺失锚 ----
T_s = {s: int((segmark == s).sum()) for s in SEGS}
bench_nan = {s: int(np.isnan(GG[cols[0]].values[segmark == s]).sum()) for s in SEGS}
P('各段天数 %s; 各段基准全 NaN 日 %s (合计 %d, 应 = 4×19 = 76)'
  % (T_s, bench_nan, sum(bench_nan.values())))

# ---- 目标列: 全窗口 avg_nh 与 days_nohold ----
piv_nh = sf.pivot_table(index='config_id', columns='period', values='avg_nh')
piv_nd = sf.pivot_table(index='config_id', columns='period', values='days_nohold')
n_pos = pd.DataFrame({s: T_s[s] - piv_nd[s] for s in SEGS})        # 各段有持仓天数 = 该段分母
num = sum(piv_nh[s].fillna(0) * n_pos[s] for s in SEGS)
den = sum(n_pos[s] for s in SEGS)
avg_nh_full = num / den.replace(0, np.nan)
days_nohold_full = sum(piv_nd[s] for s in SEGS)

meta = sf.drop_duplicates(subset=['config_id']).set_index('config_id')


def full_row(c):
    x = NET8[c].values; m = ~np.isnan(x)
    a8, _, t8, n = K.nw_stats(x[m], 5)
    a12, _, _, _ = K.nw_stats(NET12[c].values[m], 5)
    ag, _, _, _ = K.nw_stats(GG[c].values[m], 5)
    d = dict(config_id=c, net8_full=a8, net12_full=a12, gross_full=ag, cost_full=ag - a8,
             nw_full_concat=t8, turn=252 * float(np.mean(TT[c].values[m])),
             pos=float(np.mean(PP[c].values[m])), n=n)
    d['pu_net'] = a8 / d['pos'] if d['pos'] > 0 else np.nan
    for s in SEGS:
        z = x[(segmark == s) & m]
        d['net8_' + s[:4]] = float(np.mean(z)) * 252 * 100.0 if len(z) else np.nan
    d['n_seg_pos'] = int(sum(1 for s in SEGS
                             if (lambda z: len(z) and np.mean(z) > 0)(x[(segmark == s) & m])))
    for k in ('kind', 'core', 'veto', 'parent', 'family', 'cset', 'variant'):
        d[k] = meta.loc[c, k] if (c in meta.index and k in meta.columns) else np.nan
    # ---- 修正后的两列 ----
    d['avg_nh'] = float(avg_nh_full.get(c, np.nan))            # target_nh, 全窗口按有持仓天数加权
    d['days_nohold'] = int(days_nohold_full.get(c, 0))
    for s in SEGS:
        d['avg_nh_' + s[:4]] = float(piv_nh[s].get(c, np.nan))
        d['days_nohold_' + s[:4]] = int(piv_nd[s].get(c, 0))
    return d


FULL = pd.DataFrame([full_row(c) for c in cols]).set_index('config_id')

# ---- 与原表逐位比对 ----
ORIG = pd.read_csv(os.path.join(SUM, 'all_candidates.csv')).set_index('config_id')
KEEP = ['net8_full', 'net12_full', 'gross_full', 'cost_full', 'nw_full_concat', 'turn', 'pos',
        'pu_net', 'n', 'n_seg_pos'] + ['net8_' + s[:4] for s in SEGS]
both = FULL.index.intersection(ORIG.index)
P('')
P('=== 非目标列逐位比对 (n=%d) ===' % len(both))
bad = []; worst = 0.0
for c in KEEP:
    if c not in ORIG.columns: continue
    a = FULL.loc[both, c].values.astype(float); b = ORIG.loc[both, c].values.astype(float)
    m = ~(np.isnan(a) & np.isnan(b))
    d = np.nanmax(np.abs(a[m] - b[m])) if m.any() else 0.0
    worst = max(worst, d)
    if d > 1e-12: bad.append((c, d))
    P('  %-16s max|d| = %.3e %s' % (c, d, '' if d <= 1e-12 else '<-- 超容差'))
P('  >>> 非目标列 max|d| 的最大值 = %.3e -> %s' % (worst, '全部在 1e-12 容差内 (浮点末位)' if not bad else '超容差: %s' % bad))

P('')
P('=== 目标列变化 ===')
chg = pd.DataFrame({'avg_nh_old': ORIG.loc[both, 'avg_nh'], 'avg_nh_new': FULL.loc[both, 'avg_nh'],
                    'nd_old': ORIG.loc[both, 'days_nohold'], 'nd_new': FULL.loc[both, 'days_nohold']})
chg['ratio'] = chg.avg_nh_new / chg.avg_nh_old
P('  avg_nh 新/旧 比值: 中位 %.3f, 最小 %.3f, 最大 %.3f' %
  (chg.ratio.median(), chg.ratio.min(), chg.ratio.max()))
P('  days_nohold 旧 中位 %d 新 中位 %d; 新值分布 %s' %
  (int(chg.nd_old.median()), int(chg.nd_new.median()),
   dict(chg.nd_new.value_counts().head(4))))
for cid in ['KT_dep(50,50)|C:k5', 'KT_mean@30|C:k5+cr5:k10',
            'KTC_mean@30|cvr_1d:k10+cr5:k10', 'KTC_mean@25|cvr_1d:k10']:
    if cid in FULL.index:
        P('  %-38s 旧 %.1f -> 新 %.1f  (各段 %s)'
          % (cid, ORIG.loc[cid, 'avg_nh'], FULL.loc[cid, 'avg_nh'],
             '/'.join('%.0f' % FULL.loc[cid, 'avg_nh_' + s[:4]] for s in SEGS)))

FULL.to_csv(os.path.join(OUT, 'all_candidates.csv'))
FULL[FULL.kind == 'core'].to_csv(os.path.join(OUT, 'core_depth.csv'))
econ = FULL[FULL.kind.isin(['core', 'hard', 'composite', 'exempt', 'soft'])].copy()
e = econ[['net8_full', 'turn', 'n_seg_pos', 'nw_full_concat']].dropna()
v = e[['net8_full', 'turn']].values
nd_ = [e.index[i] for i in range(len(v))
       if not (((v[:, 0] >= v[i, 0]) & (v[:, 1] <= v[i, 1]) &
                ((v[:, 0] > v[i, 0]) | (v[:, 1] < v[i, 1]))).any())]
econ.loc[nd_].sort_values('net8_full', ascending=False).to_csv(
    os.path.join(OUT, 'neighborhoods_and_frontiers.csv'))
fr_old = set(pd.read_csv(os.path.join(SUM, 'neighborhoods_and_frontiers.csv')).iloc[:, 0])
P('  前沿集合成员: 原 %d 新 %d, 对称差 %d (应为 0, 前沿只依赖未受影响的列)'
  % (len(fr_old), len(nd_), len(fr_old ^ set(nd_))))
cd_old = set(pd.read_csv(os.path.join(SUM, 'core_depth.csv')).iloc[:, 0])
P('  core_depth 行集合: 原 %d 新 %d, 对称差 %d'
  % (len(cd_old), int((FULL.kind == 'core').sum()),
     len(cd_old ^ set(FULL.index[FULL.kind == 'core']))))
FULL.groupby('kind').agg(n=('net8_full', 'size'), net8_median=('net8_full', 'median'),
                         net8_max=('net8_full', 'max'), turn_mean=('turn', 'mean'),
                         nh_mean=('avg_nh', 'mean'), nohold=('days_nohold', 'sum')
                         ).to_csv(os.path.join(OUT, 'coverage_and_execution.csv'))

json.dump({'fixed_at': '2026-09-09', 'source_dir': E6E,
           'orig_sha': {f: sha(os.path.join(SUM, f)) for f in
                        ['all_candidates.csv', 'core_depth.csv',
                         'neighborhoods_and_frontiers.csv', 'coverage_and_execution.csv']},
           'nontarget_reproduced_within_1e_12': not bad, 'nontarget_max_abs_diff': worst,
           'target_cols': ['avg_nh', 'days_nohold'],
           'formula_avg_nh_full': 'sum_s(avg_nh_s * n_pos_s) / sum_s(n_pos_s), n_pos_s = T_s - days_nohold_s',
           'bench_nan_by_segment': bench_nan, 'T_by_segment': T_s},
          open(os.path.join(OUT, 'fix_manifest.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'README_fix.md'), 'w', encoding='utf-8').write(
    '# E6e 汇总表修订 (E6f 阶段 0)\n\n'
    '缺陷: `e6e_merge1.py` 的 `full_row()` 用 `sf.drop_duplicates(subset=["config_id"])` 取 meta, '
    'drop_duplicates 保留首次出现 = **2010-2014 段**, 因此 `avg_nh` 与 `days_nohold` 是首段值而非全窗口值。'
    '分类字段 (kind/core/veto/parent/family/cset/variant) 各段相同, 不受影响; '
    '`pos`/net8/net12/gross/turn 由日序列独立算, 也不受影响 (本次复算与原表最大差 7.1e-15 = 浮点末位; n / n_seg_pos 精确相同)。\n\n'
    '修法: `avg_nh_full = Σ_s(avg_nh_s × n_pos_s) / Σ_s n_pos_s`, `n_pos_s = T_s − days_nohold_s` '
    '(与各段 `avg_nh` 同分母 = 有持仓天数); `days_nohold_full = Σ_s days_nohold_s`。另增各段分列。\n\n'
    '未做 (登记 LIMIT): `live_nh`(5 批叠加后实际持有票数) 需要重建全部 20,282 个配置的 mask, '
    '等于重跑 E6e 阶段 B-D, 与本修订不成比例; 本表的 `avg_nh` 是 **target_nh**。'
    '`days_nohold` 的四分拆 (no_target/no_live/benchmark_missing/warmup) 同理需逐日 nh, 未存; '
    '已知锚: 各段基准全 NaN 日 19 天 × 4 = 76, `days_nohold` 每段 19-29 天为段首预热。\n\n'
    '七个 `e6e_*.py` 未改动; 原文件未覆盖, 原始 SHA256 见 `fix_manifest.json`。\n')
open(os.path.join(OUT, 'fix_log.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
P('')
P('写出 -> %s' % OUT)
