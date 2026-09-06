#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6e 阶段 D 后的 part1 汇总: 地图 + 确定性对照。只出表, 不下采纳结论。
   用法: python e6e_merge1.py --out DIR
"""
import os, sys, json, argparse
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K

ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
OUT = ap.parse_args().out
SUM = os.path.join(OUT, 'summary')
L = []
def P(s=''):
    print(s, flush=True); L.append(s)

R1 = 'KT_dep(50,50)|C:k5'                    # A4b_CVRv5@H5 (生产终形态)
R2 = 'KT_mean@30|C:k5+cr5:k10'               # E6b 样本内最强 (非生产)

sf = pd.concat([pd.read_csv(os.path.join(SUM, 'sf_%s.csv' % s)) for s in K.SEGS
                if os.path.exists(os.path.join(SUM, 'sf_%s.csv' % s))], ignore_index=True)
segs = sorted(sf.period.unique())
P('载入段 %s; 配置-段行 %d' % ('/'.join(segs), len(sf)))

G, Pz, Tn, mark = [], [], [], []
for s in segs:
    g = pd.read_parquet(os.path.join(OUT, 'daily', 'daily_gross_%s.parquet' % s))
    p = pd.read_parquet(os.path.join(OUT, 'daily', 'daily_pos_%s.parquet' % s))
    t = pd.read_parquet(os.path.join(OUT, 'daily', 'daily_turn_%s.parquet' % s))
    G.append(g); Pz.append(p); Tn.append(t); mark.append(np.array([s] * len(g.index)))
cols = sorted(set.intersection(*[set(x.columns) for x in G]))
GG = pd.concat([x.reindex(columns=cols) for x in G], axis=0)
PP = pd.concat([x.reindex(columns=cols) for x in Pz], axis=0)
TT = pd.concat([x.reindex(columns=cols) for x in Tn], axis=0)
segmark = np.concatenate(mark)
yr = pd.Index(GG.index).year
P('四段共有配置 %d 个; 日序列 %d 行' % (len(cols), len(GG.index)))

meta = sf.drop_duplicates(subset=['config_id']).set_index('config_id')
NET8 = GG - TT * (K.COST / 1e4)
NET12 = GG - TT * (K.COST_HI / 1e4)


def full_row(c):
    x = NET8[c].values; m = ~np.isnan(x)
    a8, _, t8, n = K.nw_stats(x[m], 5)
    a12, _, _, _ = K.nw_stats(NET12[c].values[m], 5)
    ag, _, _, _ = K.nw_stats(GG[c].values[m], 5)
    d = dict(config_id=c, net8_full=a8, net12_full=a12, gross_full=ag, cost_full=ag - a8,
             nw_full_concat=t8, turn=252 * float(np.mean(TT[c].values[m])),
             pos=float(np.mean(PP[c].values[m])), n=n)
    d['pu_net'] = a8 / d['pos'] if d['pos'] > 0 else np.nan
    for s in segs:
        z = x[(segmark == s) & m]
        d['net8_' + s[:4]] = float(np.mean(z)) * 252 * 100.0 if len(z) else np.nan
    d['n_seg_pos'] = int(sum(1 for s in segs
                             if (lambda z: len(z) and np.mean(z) > 0)(x[(segmark == s) & m])))
    for k in ('kind', 'core', 'veto', 'parent', 'family', 'cset', 'variant', 'avg_nh', 'days_nohold'):
        d[k] = meta.loc[c, k] if (c in meta.index and k in meta.columns) else np.nan
    return d

FULL = pd.DataFrame([full_row(c) for c in cols]).set_index('config_id')
FULL.to_csv(os.path.join(SUM, 'all_candidates.csv'))
P('all_candidates.csv %d 行' % len(FULL))


def nv(c, col='net8_full'):
    return FULL.loc[c, col] if c in FULL.index else np.nan


def dpair(a, b):
    if a not in NET8.columns or b not in NET8.columns: return np.nan, np.nan, 0
    return K.score_hac(NET8[a].values - NET8[b].values, 5)


# ---------- 核 × 深度 ----------
cd = FULL[FULL.kind == 'core'].copy()
cd.to_csv(os.path.join(SUM, 'core_depth.csv'))

# ---------- 否决边际 + 四组分解 + 对照 ----------
rows = []
kids = FULL[FULL.kind.isin(['hard', 'composite', 'exempt'])]
for cid in kids.index:
    par = FULL.loc[cid, 'parent']
    if not isinstance(par, str) or par not in FULL.index: continue
    d_par = dpair(cid, par)
    trim = cid + '#trim'; ko = cid + '#ko'
    ep_p = par + '||eqpos_par@' + str(FULL.loc[cid, 'veto']); ep_c = cid + '||eqpos_chd'
    d_trim = dpair(cid, trim) if trim in FULL.index else (np.nan, np.nan, 0)
    d_eq = dpair(ep_c, ep_p) if (ep_c in FULL.index and ep_p in FULL.index) else (np.nan, np.nan, 0)
    rows.append(dict(config_id=cid, core=FULL.loc[cid, 'core'], veto=FULL.loc[cid, 'veto'],
                     kind=FULL.loc[cid, 'kind'], net8=nv(cid), net12=nv(cid, 'net12_full'),
                     net8_parent=nv(par), gross=nv(cid, 'gross_full'), cost=nv(cid, 'cost_full'),
                     pos=nv(cid, 'pos'), pos_parent=nv(par, 'pos'), nh=nv(cid, 'avg_nh'),
                     d_vs_parent=d_par[0], t_vs_parent=d_par[1],
                     d_vs_coretrim=d_trim[0], t_vs_coretrim=d_trim[1], net8_coretrim=nv(trim),
                     d_eqpos=d_eq[0], t_eqpos=d_eq[1],
                     net8_known_only=nv(ko), d_known_only=nv(ko) - nv(cid) if ko in FULL.index else np.nan,
                     n_seg_pos=FULL.loc[cid, 'n_seg_pos'],
                     dgross_vs_parent=nv(cid, 'gross_full') - nv(par, 'gross_full'),
                     dcost_vs_parent=nv(cid, 'cost_full') - nv(par, 'cost_full'),
                     dpos_vs_parent=nv(cid, 'pos') - nv(par, 'pos'),
                     pu_net=nv(cid, 'pu_net'), pu_net_parent=nv(par, 'pu_net')))
VM = pd.DataFrame(rows)
VM.to_csv(os.path.join(SUM, 'veto_marginals.csv'), index=False)
P('veto_marginals.csv %d 行' % len(VM))

# ---------- 反向否决 ----------
rv = []
for cid in FULL[FULL.kind == 'reverse'].index:
    par = FULL.loc[cid, 'parent']; vid = str(FULL.loc[cid, 'veto'])
    fwd = '%s|%s' % (par, vid)
    d1 = dpair(cid, par); d2 = dpair(fwd, cid) if fwd in FULL.index else (np.nan, np.nan, 0)
    rv.append(dict(config_id=cid, core=par, veto=vid, net8_reverse=nv(cid), net8_forward=nv(fwd),
                   net8_parent=nv(par), d_rev_vs_parent=d1[0], t_rev_vs_parent=d1[1],
                   d_fwd_vs_rev=d2[0], t_fwd_vs_rev=d2[1]))
RV = pd.DataFrame(rv); RV.to_csv(os.path.join(SUM, 'relative_rerank.csv'), index=False)

# ---------- 软否决与再配置 ----------
sr = []
for cid in FULL[FULL.kind == 'soft'].index:
    par = FULL.loc[cid, 'parent']; vid = str(FULL.loc[cid, 'veto'])
    start = vid.split('~')[0]; mode = vid.split('~')[1][:2]; lam = float(vid.split('~')[1][2:])
    hardc = '%s|%s' % (par, start)
    wz = '%s|%s~WS1.00' % (par, start)
    d_h = dpair(cid, hardc) if hardc in FULL.index else (np.nan, np.nan, 0)
    d_p = dpair(cid, par)
    sr.append(dict(config_id=cid, core=par, start=start, mode=mode, lam=lam, net8=nv(cid),
                   net8_parent=nv(par), net8_hard=nv(hardc), net8_WZ=nv(wz),
                   gross=nv(cid, 'gross_full'), cost=nv(cid, 'cost_full'), pos=nv(cid, 'pos'),
                   d_vs_hard=d_h[0], t_vs_hard=d_h[1], d_vs_parent=d_p[0], t_vs_parent=d_p[1],
                   # 冻权删票 vs 幸存者再配置 (仅在 WZ 可得时)
                   frozen_delete=(nv(wz) - nv(par)) if wz in FULL.index else np.nan,
                   survivor_realloc=(nv(hardc) - nv(wz)) if (wz in FULL.index and hardc in FULL.index) else np.nan))
SR = pd.DataFrame(sr); SR.to_csv(os.path.join(SUM, 'soft_and_reallocation.csv'), index=False)

# ---------- 条件豁免 ----------
EX = VM[VM.kind == 'exempt'].copy()
EX.to_csv(os.path.join(SUM, 'conditional_exemption.csv'), index=False)

# ---------- 归因四组 ----------
att = SR[(SR['mode'] == 'WS') & (SR['lam'] == 1.0)][
    ['core', 'start', 'net8_parent', 'net8_WZ', 'net8_hard', 'frozen_delete', 'survivor_realloc']
].drop_duplicates()
att['hard_total'] = att['net8_hard'] - att['net8_parent']
att['identity_err'] = att['hard_total'] - (att['frozen_delete'] + att['survivor_realloc'])
att.to_csv(os.path.join(SUM, 'attribution.csv'), index=False)

# ---------- 对两个固定参照 ----------
pr = []
for c in cols:
    if c not in FULL.index: continue
    d1 = dpair(c, R1); d2 = dpair(c, R2)
    pr.append(dict(config_id=c, kind=FULL.loc[c, 'kind'], net8=nv(c), net12=nv(c, 'net12_full'),
                   d_vs_R1=d1[0], t_vs_R1=d1[1], d_vs_R2=d2[0], t_vs_R2=d2[1]))
PR = pd.DataFrame(pr); PR.to_csv(os.path.join(SUM, 'paired_vs_references.csv'), index=False)

# ---------- 非支配集合 ----------
econ = FULL[FULL.kind.isin(['core', 'hard', 'composite', 'exempt', 'soft'])].copy()
e = econ[['net8_full', 'turn', 'n_seg_pos', 'nw_full_concat']].dropna()
v = e[['net8_full', 'turn']].values
nd = []
for i in range(len(v)):
    dom = ((v[:, 0] >= v[i, 0]) & (v[:, 1] <= v[i, 1]) &
           ((v[:, 0] > v[i, 0]) | (v[:, 1] < v[i, 1]))).any()
    if not dom: nd.append(e.index[i])
FR = econ.loc[nd].sort_values('net8_full', ascending=False)
FR.to_csv(os.path.join(SUM, 'neighborhoods_and_frontiers.csv'))

# ---------- 逐年 / 留一年 ----------
watch = [R1, R2, 'KT_dep(50,50)', 'KT_mean@30', 'KT_mean@50', 'T@25', 'K@50', 'C@30']
yl, ll = [], []
for c in [w for w in watch if w in NET8.columns]:
    x = NET8[c].values
    for y in sorted(set(yr)):
        z = x[yr == y]; z = z[~np.isnan(z)]
        yl.append(dict(config_id=c, year=int(y), net8=float(np.mean(z)) * 252 * 100 if len(z) else np.nan))
        z2 = x[yr != y]; z2 = z2[~np.isnan(z2)]
        ll.append(dict(config_id=c, dropped=int(y), net8=float(np.mean(z2)) * 252 * 100 if len(z2) else np.nan))
pd.DataFrame(yl).to_csv(os.path.join(SUM, 'yearly.csv'), index=False)
pd.DataFrame(ll).to_csv(os.path.join(SUM, 'leave_one_year.csv'), index=False)

# ---------- 覆盖 ----------
cov = FULL.groupby('kind').agg(n=('net8_full', 'size'), net8_median=('net8_full', 'median'),
                               net8_max=('net8_full', 'max'), turn_mean=('turn', 'mean'),
                               nh_mean=('avg_nh', 'mean'), nohold=('days_nohold', 'sum'))
cov.to_csv(os.path.join(SUM, 'coverage_and_execution.csv'))

# ================= summary.txt =================
P('')
P('== (A) 覆盖 ==')
P(cov.to_string(float_format=lambda z: '%+.3f' % z))
P('')
P('== (B) 核 × 深度: 各族 net8 全窗口 ==')
piv = cd[cd.cset == 'P54'].pivot_table(index='family', columns='avg_nh', values='net8_full', aggfunc='first')
P(cd[cd.cset == 'P54'].sort_values('net8_full', ascending=False)
  [['family', 'net8_full', 'net12_full', 'turn', 'avg_nh', 'n_seg_pos']].head(15)
  .to_string(float_format=lambda z: '%+.3f' % z))
P('')
P('== (C) 否决边际: 相对父核 / 相对同人数剔深 / 等仓位 (中位, 单位 点) ==')
g = VM.groupby('kind').agg(n=('d_vs_parent', 'size'), d_parent=('d_vs_parent', 'median'),
                           pos_share=('d_vs_parent', lambda z: float((z > 0).mean())),
                           d_coretrim=('d_vs_coretrim', 'median'),
                           coretrim_pos=('d_vs_coretrim', lambda z: float((z > 0).mean())),
                           d_eqpos=('d_eqpos', 'median'),
                           dgross=('dgross_vs_parent', 'median'), dcost=('dcost_vs_parent', 'median'),
                           dpos=('dpos_vs_parent', 'median'))
P(g.to_string(float_format=lambda z: '%+.4f' % z))
P('')
P('== (D) 反向否决 (剔最好 m_t 只) ==')
if len(RV):
    P(RV.agg({'d_rev_vs_parent': ['median', 'mean'], 'd_fwd_vs_rev': ['median', 'mean']})
      .to_string(float_format=lambda z: '%+.4f' % z))
    P('  反向也为正的比例: %.3f;  正向优于反向的比例: %.3f'
      % (float((RV.d_rev_vs_parent > 0).mean()), float((RV.d_fwd_vs_rev > 0).mean())))
P('')
P('== (E) 软否决 λ 曲线 (按 mode 与 λ 的 net8 中位) ==')
if len(SR):
    P(SR.pivot_table(index='lam', columns='mode', values='net8', aggfunc='median')
      .to_string(float_format=lambda z: '%+.3f' % z))
    P('  冻权删票中位 %+.4f;  幸存者再配置中位 %+.4f'
      % (SR.frozen_delete.median(), SR.survivor_realloc.median()))
P('')
P('== (F) 归因恒等式 hard_total = 冻权删票 + 幸存者再配置 ==')
if len(att):
    P('  max|err| = %.3e  (n=%d)' % (np.nanmax(np.abs(att.identity_err.values)), len(att)))
P('')
P('== (G) 两个固定参照 ==')
P('  R1 = %s  net8 %+.3f   R2 = %s  net8 %+.3f' % (R1, nv(R1), R2, nv(R2)))
P('  强于 R1 的经济配置数 %d / %d;  强于 R2 %d / %d'
  % (int((PR.d_vs_R1 > 0).sum()), len(PR), int((PR.d_vs_R2 > 0).sum()), len(PR)))
P('')
P('== (H) 非支配集合 (net8 高 / 换手低) 前 12 ==')
P(FR[['kind', 'net8_full', 'net12_full', 'turn', 'avg_nh', 'n_seg_pos']].head(12)
  .to_string(float_format=lambda z: '%+.3f' % z))
open(os.path.join(OUT, 'summary.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
P('')
P('merge part1 done.')
