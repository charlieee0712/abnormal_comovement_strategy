#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6e 阶段 F: 随机增量 + 配对统计 + bootstrap(F1-F5) + 两层(日期+MC)敏感性。
   用法: python e6e_stats.py --out DIR
"""
import os, sys, glob, json, hashlib, argparse
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K

ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
ap.add_argument('--nboot', type=int, default=2000)
A = ap.parse_args(); OUT, NBOOT = A.out, A.nboot
SUM = os.path.join(OUT, 'summary'); BST = os.path.join(OUT, 'bootstrap')
os.makedirs(BST, exist_ok=True)
BLOCK_L, SEED_ROOT = 60, 'E6e-v1/'
R1 = 'KT_dep(50,50)|C:k5'; R2 = 'KT_mean@30|C:k5+cr5:k10'
L = []
def P(s=''):
    print(s, flush=True); L.append(s)


def sub_seed(ns):
    return int.from_bytes(hashlib.sha256((SEED_ROOT + ns).encode()).digest()[:8], 'big') % (2 ** 32)


def stat_idx(n, Lb, rng):
    out = np.empty(n, np.int64); i = 0; p = 1.0 / Lb
    while i < n:
        s = rng.randint(n); ln = min(rng.geometric(p), n - i)
        out[i:i + ln] = (s + np.arange(ln)) % n; i += ln
    return out


# ---------------- 确定性侧 (part1 产物) ----------------
segs = [s for s in K.SEGS if os.path.exists(os.path.join(SUM, 'sf_%s.csv' % s))]
G, T_, mark = [], [], []
for s in segs:
    G.append(pd.read_parquet(os.path.join(OUT, 'daily', 'daily_gross_%s.parquet' % s)))
    T_.append(pd.read_parquet(os.path.join(OUT, 'daily', 'daily_turn_%s.parquet' % s)))
    mark.append(np.array([s] * len(G[-1].index)))
cols = sorted(set.intersection(*[set(x.columns) for x in G]))
GG = pd.concat([x.reindex(columns=cols) for x in G], axis=0)
TT = pd.concat([x.reindex(columns=cols) for x in T_], axis=0)
NET = GG - TT * (K.COST / 1e4)
segmark = np.concatenate(mark); Tn = len(NET.index)
segidx = {s: np.where(segmark == s)[0] for s in segs}
P('确定性配置 %d, 日序列 %d 行, 段 %s' % (len(cols), Tn, '/'.join(segs)))
FULL = pd.read_csv(os.path.join(SUM, 'all_candidates.csv')).set_index('config_id')

# 共用日期 draw (所有序列、所有族共用)
rng = np.random.RandomState(sub_seed('dates'))
DRAWS = np.stack([np.concatenate([segidx[s][stat_idx(len(segidx[s]), BLOCK_L, rng)] for s in segs])
                  for _ in range(NBOOT)])
P('bootstrap: stationary, 块长 %d, B=%d, 按段, 共用日期 draw' % (BLOCK_L, NBOOT))


def boot_mean(x):
    """x: (Tn,) -> (NBOOT,) 年化"""
    v = np.nan_to_num(x, nan=0.0); ok = (~np.isnan(x)).astype(float)
    num = v[DRAWS].sum(axis=1); den = ok[DRAWS].sum(axis=1)
    return np.where(den > 0, num / np.maximum(den, 1), np.nan) * 252 * 100.0


def band(obs, bt, names, fam):
    lo = np.nanpercentile(bt, 2.5, axis=0); hi = np.nanpercentile(bt, 97.5, axis=0)
    sd = np.nanstd(bt, axis=0)
    z = np.nanmax(np.abs((bt - np.nanmean(bt, axis=0)) / np.where(sd > 0, sd, np.nan)), axis=1)
    q = float(np.nanpercentile(z, 95))
    return pd.DataFrame(dict(family=fam, name=names, obs=obs, lo95=lo, hi95=hi, sd=sd,
                             joint_lo=obs - q * sd, joint_hi=obs + q * sd, q95=q))


# ---------------- 随机侧: 流式读 shard ----------------
RM, RS, RN = {}, {}, {}        # (rule,profile) -> 逐日均值 / 逐日 sd / 路径数 (拼接四段)
PREF = {}                       # 前缀稳定性 32/64/128
TWO = {}                        # 两层 bootstrap 用的 draw-mean 矩阵 (128 x NBOOT)
DMAT = None
scal = []
for s in segs:
    rd = os.path.join(OUT, 'random_daily', s)
    if not os.path.isdir(rd): continue
    for f in sorted(glob.glob(os.path.join(rd, 'scalars_*.csv'))):
        scal.append(pd.read_csv(f))
    idx = segidx[s]
    if DMAT is None or DMAT.shape[0] != Tn:
        DMAT = None
    files = sorted(glob.glob(os.path.join(rd, 'net8_*.parquet')))
    P('  段 %s: %d 个随机 shard-profile 文件' % (s, len(files)))
    for f in files:
        d = pd.read_parquet(f)
        keys = {}
        for c in d.columns:
            rp, b = c.rsplit('|b', 1)
            keys.setdefault(rp, []).append((int(b), c))
        for rp, lst in keys.items():
            lst.sort()
            X = d[[c for _, c in lst]].values.T           # (B, Tseg)
            if rp not in RM:
                RM[rp] = np.full(Tn, np.nan); RS[rp] = np.full(Tn, np.nan); RN[rp] = len(lst)
            RM[rp][idx] = np.nanmean(X, axis=0)
            RS[rp][idx] = np.nanstd(X, axis=0)
            for k in (32, 64, 128):
                if len(lst) >= k:
                    PREF.setdefault((rp, k), np.full(Tn, np.nan))[idx] = np.nanmean(X[:k], axis=0)
            TWO.setdefault(rp, {})[s] = X.astype(np.float32)
        del d
S = pd.concat(scal, ignore_index=True) if scal else pd.DataFrame()
P('随机规则-profile 组合 %d 个; 标量行 %d' % (len(RM), len(S)))

# ---------------- increment_vs_random ----------------
rows = []
for rp in sorted(RM):
    rule, profile = rp.rsplit('@', 1)
    real = rule if rule in NET.columns else rule.replace('#soft', '')
    if real not in NET.columns: continue
    d = NET[real].values - RM[rp]
    ann, t, n = K.score_hac(d, 5)
    mc = float(np.nanmean(RS[rp]) / np.sqrt(max(RN[rp], 1))) * 252 * 100.0
    r = dict(rule=rule, profile=profile, n_paths=RN[rp],
             real_net8=float(np.nanmean(NET[real].values)) * 252 * 100.0,
             rand_net8=float(np.nanmean(RM[rp])) * 252 * 100.0,
             increment=ann, t_increment=t, mcse=mc)
    for k in (32, 64, 128):
        if (rp, k) in PREF:
            r['rand_net8_%d' % k] = float(np.nanmean(PREF[(rp, k)])) * 252 * 100.0
    if 'rand_net8_128' in r and 'rand_net8_64' in r:
        r['prefix_drift_64_128'] = r['rand_net8_128'] - r['rand_net8_64']
    rows.append(r)
INC = pd.DataFrame(rows)
if len(INC): INC.to_csv(os.path.join(SUM, 'random_controls.csv'), index=False)
P('random_controls.csv %d 行' % len(INC))

# ---------------- 两层 (日期 + MC) 敏感性: F3 与软起点 ----------------
two_rows = []
if TWO:
    Dcnt = np.zeros((Tn, NBOOT), np.float32)
    for j in range(NBOOT):
        np.add.at(Dcnt[:, j], DRAWS[j], 1.0)
    rng2 = np.random.RandomState(sub_seed('mc'))
    for rp in sorted(TWO):
        rule, profile = rp.rsplit('@', 1)
        real = rule if rule in NET.columns else rule.replace('#soft', '')
        if real not in NET.columns: continue
        Xs = TWO[rp]
        B = min(v.shape[0] for v in Xs.values())
        Xfull = np.zeros((B, Tn), np.float32)
        for s2, v in Xs.items(): Xfull[:, segidx[s2]] = v[:B]
        M = np.nan_to_num(Xfull) @ Dcnt / np.maximum(Dcnt.sum(axis=0), 1)      # (B, NBOOT)
        y = boot_mean(NET[real].values)
        w = rng2.multinomial(B, np.full(B, 1.0 / B), size=NBOOT).T.astype(np.float32) / B
        rnd = (M * 252 * 100.0 * w).sum(axis=0)
        th = y - rnd
        two_rows.append(dict(rule=rule, profile=profile, n_paths=B,
                             theta=float(np.nanmean(th)), lo95=float(np.nanpercentile(th, 2.5)),
                             hi95=float(np.nanpercentile(th, 97.5)), sd=float(np.nanstd(th))))
    if two_rows:
        pd.DataFrame(two_rows).to_csv(os.path.join(BST, 'two_level_F3.parquet').replace('.parquet', '.csv'),
                                      index=False)
P('两层敏感性 %d 行' % len(two_rows))

# ---------------- F1-F5 bootstrap ----------------
econ = [c for c in cols if str(FULL.loc[c, 'kind']) in ('core', 'hard', 'composite', 'exempt', 'soft')]
fams = {}
for fam, ref in (('F1', R1), ('F2', R2)):
    if ref not in NET.columns: continue
    D = np.stack([boot_mean(NET[c].values - NET[ref].values) for c in econ])
    obs = np.array([float(np.nanmean(NET[c].values - NET[ref].values)) * 252 * 100 for c in econ])
    fams[fam] = band(obs, D.T, econ, fam)
kids = [c for c in econ if isinstance(FULL.loc[c, 'parent'], str)
        and FULL.loc[c, 'parent'] in NET.columns and str(FULL.loc[c, 'kind']) != 'core']
tr = [(c, c + '#trim') for c in kids if (c + '#trim') in NET.columns]
if tr:
    D = np.stack([boot_mean(NET[a].values - NET[b].values) for a, b in tr])
    obs = np.array([float(np.nanmean(NET[a].values - NET[b].values)) * 252 * 100 for a, b in tr])
    fams['F4'] = band(obs, D.T, [a for a, _ in tr], 'F4')
if len(INC):
    sel = INC.dropna(subset=['increment'])
    fams['F3'] = pd.DataFrame(dict(family='F3', name=sel.rule + '@' + sel.profile,
                                   obs=sel.increment.values, lo95=np.nan, hi95=np.nan,
                                   sd=sel.mcse.values, joint_lo=np.nan, joint_hi=np.nan, q95=np.nan))
soft = [c for c in econ if str(FULL.loc[c, 'kind']) == 'soft']
sp = []
for c in soft:
    par = FULL.loc[c, 'parent']; st = str(FULL.loc[c, 'veto']).split('~')[0]
    hardc = '%s|%s' % (par, st)
    if hardc in NET.columns: sp.append((c, hardc))
if sp:
    D = np.stack([boot_mean(NET[a].values - NET[b].values) for a, b in sp])
    obs = np.array([float(np.nanmean(NET[a].values - NET[b].values)) * 252 * 100 for a, b in sp])
    fams['F5'] = band(obs, D.T, [a for a, _ in sp], 'F5')
if fams:
    allf = pd.concat(fams.values(), ignore_index=True)
    allf.to_csv(os.path.join(BST, 'families.csv'), index=False)
json.dump(dict(nboot=NBOOT, block=BLOCK_L, block_sens=20, seed_root=SEED_ROOT, by_segment=True,
               shared_date_draw=True, families=sorted(fams)),
          open(os.path.join(BST, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---------------- summary ----------------
P('')
P('== (A) increment_vs_random 按 profile (单位 点) ==')
if len(INC):
    g = INC.groupby('profile').agg(n=('increment', 'size'), inc_median=('increment', 'median'),
                                   inc_mean=('increment', 'mean'),
                                   pos=('increment', lambda z: float((z > 0).mean())),
                                   t_median=('t_increment', 'median'),
                                   mcse_median=('mcse', 'median'),
                                   mcse_gt_010=('mcse', lambda z: float((z > 0.10).mean())))
    P(g.to_string(float_format=lambda z: '%+.4f' % z))
    if 'prefix_drift_64_128' in INC.columns:
        P('  前缀稳定性 |rand(128)-rand(64)| 中位 %.4f, 95 分位 %.4f'
          % (float(INC.prefix_drift_64_128.abs().median()),
             float(INC.prefix_drift_64_128.abs().quantile(0.95))))
P('')
P('== (B) 两层 (日期+MC) 敏感性 ==')
if two_rows:
    tw = pd.DataFrame(two_rows)
    P('  n=%d; theta 中位 %+.4f; 区间不含 0 的比例 %.3f'
      % (len(tw), tw.theta.median(), float(((tw.lo95 > 0) | (tw.hi95 < 0)).mean())))
P('')
P('== (C) bootstrap 族 ==')
for fam in sorted(fams):
    f = fams[fam]
    if f['lo95'].notna().any():
        P('  %s n=%d 逐点区间不含 0 %d; 联合带不含 0 %d (q95=%.2f)'
          % (fam, len(f), int(((f.lo95 > 0) | (f.hi95 < 0)).sum()),
             int(((f.joint_lo > 0) | (f.joint_hi < 0)).sum()), f.q95.iloc[0]))
    else:
        P('  %s n=%d (只出 MCSE, 见 random_controls.csv)' % (fam, len(f)))
open(os.path.join(OUT, 'summary_part2.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
P('')
P('stats done.')
