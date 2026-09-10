#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f part2 数字摘要: 从已落盘的表里抽 part2 要用的数, 不重算。
   用法: python e6f_part2_digest.py --out DIR
"""
import os, sys, json, argparse
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6f_core as F

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
A = ap.parse_args()
OUT = A.out
R1, R2 = 'KT_dep(50,50)|C:k5', 'KT_mean@30|C:k5+cr5:k10'
pd.set_option('display.width', 220)


def has(p):
    return os.path.exists(os.path.join(OUT, p))


def rd(p):
    return pd.read_csv(os.path.join(OUT, p))


def H(s):
    print('\n' + '=' * 78)
    print(s)
    print('=' * 78)


FU = None
# ---------- Q1 构造参数邻域 ----------
if has('A_oat/A_full_window.csv'):
    ALL = rd('A_oat/A_full_window.csv').set_index('config_id')
    # 日账本里含对照角色 (coretrim #trim / eqpos / common_domain); 主表只算 primary
    FU = ALL[ALL.layer.notna()]
    H('Q1 构造参数邻域 (全窗口, legacy_all): primary %d / 含对照共 %d' % (len(FU), len(ALL)))
    print('R1 %+.3f   R2 %+.3f' % (ALL.net8.get(R1, np.nan), ALL.net8.get(R2, np.nan)))
    print('primary net8: 中位 %+.3f  p90 %+.3f  最大 %+.3f (%s)'
          % (FU.net8.median(), FU.net8.quantile(.9), FU.net8.max(), FU.net8.idxmax()))
    print('四段全正比例 %.3f; 对 R2 配对差>0 比例 %.3f; 对 R1 配对差>0 比例 %.3f'
          % (float((FU.n_seg_pos == 4).mean()), float((FU.d_vs_R2 > 0).mean()),
             float((FU.d_vs_R1 > 0).mean())))
    print('对 R2 配对差 t>2 个数 %d; t<-2 个数 %d (分母 %d)'
          % (int((FU.t_vs_R2 > 2).sum()), int((FU.t_vs_R2 < -2).sum()), len(FU)))
    print('对 R1 配对差 t>2 个数 %d; t<-2 个数 %d'
          % (int((FU.t_vs_R1 > 2).sum()), int((FU.t_vs_R1 < -2).sum())))
    print('')
    print('分层中位:')
    print(FU.groupby('layer').agg(n=('net8', 'size'), net8=('net8', 'median'),
                                  best=('net8', 'max'), dR2=('d_vs_R2', 'median'),
                                  dR2_pos=('d_vs_R2', lambda s: float((s > 0).mean())),
                                  turn=('turn', 'median'),
                                  nh=('avg_nh', 'median')).round(3).to_string())
    print('')
    print('逐段中位:')
    print(FU.groupby('layer')[['net8_' + s[:4] for s in F.SEGS]].median().round(2).to_string())

if FU is not None:
    # 层中位数【不是】参数效应 —— 各层包含的核不同。参数轴一律在【同核】内读。
    H('Q1 参数轴 (同核内; Δ = 相对该核在该轴上的中位)')
    import re


    def _depth(c):
        m = re.search(r'@(\d+)', c.split('|')[0])
        return int(m.group(1)) if m else None

    def _core(c):
        return c.split('|')[0]

    def _vetok(c):
        out = []
        for x in (c.split('|')[1] if '|' in c else '').split('+'):
            if ':k' not in x:
                continue
            m = re.match(r'^(\d+)', x.rsplit(':k', 1)[1])
            if m:
                out.append(int(m.group(1)))
        return tuple(sorted(out))
    # 参数轴只在 H=5 且中性化 = NS 的格位上读: H 分支与中性化分支各自是独立的轴,
    # 混进来会让"同核"分组不唯一 (KT_dep(50,50)|C:k5 有 7 个 H 变体)。
    W = FU.reset_index()
    W = W[(W.H == 5) & (W.neu.fillna('NS') == 'NS') & (W.neu_veto.fillna('NS') == 'NS')].copy()
    print('参数轴样本: H=5 且 neu=NS 的 primary 共 %d' % len(W))
    W['depth'] = W.config_id.map(_depth)
    W['core'] = W.config_id.map(_core)
    W['vk'] = W.config_id.map(lambda c: _vetok(c)[0] if _vetok(c) else None)
    W['corebase'] = W.core.map(lambda c: re.sub(r'@\d+', '@*', c))
    # 深度轴: 同 (corebase, 否决串) 内, 深度对 net8
    dd = W[W.depth.notna()].copy()
    dd['vetostr'] = dd.config_id.map(lambda c: c.split('|')[1] if '|' in c else '')
    g = dd.groupby(['corebase', 'vetostr'])
    dd['rel'] = dd.net8 - g.net8.transform('median')
    t = dd.pivot_table(index='depth', values=['net8', 'rel'], aggfunc='median')
    t['n'] = dd.groupby('depth').size()
    print('深度轴 (同 corebase+同否决串内去中位):')
    print(t.round(3).to_string())
    # k 轴: 同 (core, 否决腿名) 内
    kk = W[W.vk.notna()].copy()
    kk['vetoname'] = kk.config_id.map(
        lambda c: '+'.join(x.rsplit(':k', 1)[0]
                           for x in c.split('|')[1].split('+') if ':k' in x))
    # 组内成员少时"去中位"会退化 (两个成员时中位=均值, rel 恒为 ±半差、中位≈0);
    # 且多腿否决时 vk 只是第一条腿, (核, 腿名) 不唯一。所以 k 轴只看【单腿否决】,
    # 组 = (核, 腿名), rel5 = 组内减去该组 k=5 那一格。
    kk = kk[kk.config_id.map(lambda c: c.split('|')[1].count(':k') == 1)].copy()
    base = kk[kk.vk == 5].set_index(['core', 'vetoname']).net8
    assert base.index.is_unique, '单腿分组仍不唯一'
    kk['b5'] = pd.MultiIndex.from_frame(kk[['core', 'vetoname']]).map(base)
    kk['rel5'] = kk.net8 - kk.b5
    ok5 = kk[kk.b5.notna()]
    t2 = ok5.pivot_table(index='vk', values=['net8', 'rel5'], aggfunc='median')
    t2['n'] = ok5.groupby('vk').size()
    print('')
    print('否决强度 k 轴 (只看单腿否决; 组 = 同核+同腿名; rel5 = 减去该组 k=5 那一格):')
    print(t2.round(3).to_string())
    print('  组数 %d; 覆盖格位 %d' % (ok5.groupby(['core', 'vetoname']).ngroups, len(ok5)))
    print('  按腿名分开的 rel5 中位:')
    print('    ' + ok5.pivot_table(index='vetoname', columns='vk', values='rel5',
                                   aggfunc='median').round(3).to_string().replace(
                                       '\n', '\n    '))

if has('neighborhoods/neighborhood_metrics.csv'):
    NB = rd('neighborhoods/neighborhood_metrics.csv')
    ok = NB[NB.n_neighbors > 0]
    H('Q1 邻域平坦度 (%d 有邻居 / %d)' % (len(ok), len(NB)))
    print('邻居 Δnet8 中位: 中位 %+.3f, p10 %+.3f, p90 %+.3f'
          % (ok.d_med.median(), ok.d_med.quantile(.1), ok.d_med.quantile(.9)))
    for tau in (0.1, 0.3, 0.5):
        c = 'cover_tau%.1f' % tau
        if c in ok.columns:
            print('tau=%.1f 覆盖率: 中位 %.2f, 覆盖率<0.5 的节点占 %.2f'
                  % (tau, ok[c].median(), float((ok[c] < 0.5).mean())))
    print('网格边界 %d, 有效邻居<2 %d' % (int(NB.on_grid_boundary.sum()),
                                  int(NB.few_neighbors.sum())))
    cc = [c for c in ['config_id', 'net8', 'n_neighbors', 'd_med', 'd_p10',
                      'cover_tau0.3', 'on_grid_boundary'] if c in ok.columns]
    print('')
    print('net8 前 10 的邻域:')
    print(ok.nlargest(10, 'net8')[cc].round(3).to_string(index=False))

# ---------- Q6 持有期 ----------
if has('A_horizon/horizon.csv') and FU is not None:
    HZ = rd('A_horizon/horizon.csv')
    H('Q6 持有期 (全窗口)')
    t = HZ.pivot_table(index='anchor', columns='H', values='net8')
    t[5] = [FU.net8.get(HZ[HZ.anchor == a].parent_id.iloc[0], np.nan) for a in t.index]
    t = t[sorted(t.columns)]
    print(t.round(2).to_string())
    print('逐锚最优 H: %s' % dict(t.idxmax(axis=1).value_counts()))
    print('H5 相对各自最优的差距: 中位 %+.3f, 最差 %+.3f'
          % ((t[5] - t.max(axis=1)).median(), (t[5] - t.max(axis=1)).min()))
    tt = HZ.pivot_table(index='anchor', columns='H', values='turn')
    print('换手 逐H中位: %s' % dict((int(c), round(float(tt[c].median()), 1))
                                for c in tt.columns))

# ---------- Q6 × Q4: 冲击后的 H 曲线 ----------
import glob as _glob
_hp = sorted(_glob.glob(os.path.join(OUT, 'C_impact', 'impact_scenarios_H_*.csv')))
if _hp:
    IH = pd.concat([pd.read_csv(p) for p in _hp], ignore_index=True)
    H('Q6 x Q4 冲击后的 H 曲线 (%d 段, %d 格位)'
      % (IH.period.nunique(), IH.config_id.nunique()))
    for kp in sorted(IH.kappa.unique()):
        s = IH[(IH.form == 'sqrt') & (IH.kappa == kp)]
        t = s.pivot_table(index='H', columns='A_yi', values='net_impact_ann', aggfunc='median')
        print('')
        print('[平方根 kappa=%.2f] 四段合并中位; 每列最优 H: %s' % (kp, dict(t.idxmax())))
        print(t.round(2).to_string())
    print('')
    print('逐段 (平方根 kappa=0.5) 的每列最优 H:')
    for pg, s in IH[(IH.form == 'sqrt') & (IH.kappa == 0.5)].groupby('period'):
        t = s.pivot_table(index='H', columns='A_yi', values='net_impact_ann', aggfunc='median')
        print('  %-10s %s   (A=0 时最优 H = %s)'
              % (pg, dict(t.idxmax()),
                 s[s.A_yi == s.A_yi.min()].groupby('H').net_impact_ann.median().idxmax()))
    print('  注: H=10 是网格上界 (HGRID={1,2,3,4,5,7,10}), 再长没有格位')

# ---------- Q3 选择程序 ----------
if has('B_nested/selected_sets.csv'):
    SL = rd('B_nested/selected_sets.csv')
    H('Q3 选择程序 (%d 行)' % len(SL))
    sg = SL[(SL.account == 'single') & (SL.direction == 'forward')]
    print('域 x 规则 的选中配置数 (单次前向):')
    print(sg.pivot_table(index='domain', columns='rule', values='config_id',
                         aggfunc='nunique').to_string())
    if 'meta_pick' in SL.columns:
        M = SL[SL.rule == 'S_meta'].drop_duplicates(['domain', 'split', 'variant', 'vintage'])
        print('')
        print('S_meta: %d 个 vintage; 内层胜出规则 %s; 折数不足回退 %d'
              % (len(M), dict(M.meta_pick.value_counts()), int(M.meta_fallback.sum())))
    print('')
    print('被选中最多的配置 (前 10):')
    print(sg.config_id.value_counts().head(10).to_string())

if has('B_walkforward/policy_readout.csv'):
    PA = rd('B_walkforward/policy_readout.csv')
    H('Q3 政策账户 a / b / b-a')
    s = PA[(PA.account == 'single') & (PA.direction == 'forward')]
    print(s.groupby(['domain', 'rule']).agg(
        n=('a_train', 'size'), a=('a_train', 'median'), b_led=('b_ledger', 'median'),
        b_acct=('b_account', 'median'), b_a=('b_minus_a', 'median'),
        mix=('mix_gain', 'median'), dR2=('d_vs_R2', 'median')).round(3).to_string())
    print('')
    print('对 R2 |t|>2 比例 %.3f; d_vs_R2>0 比例 %.3f'
          % (float((s.t_vs_R2.abs() > 2).mean()), float((s.d_vs_R2 > 0).mean())))
    r = PA[PA.direction == 'reverse']
    if len(r):
        print('反向 (迁移诊断): b_ledger 中位 %+.3f, b-a 中位 %+.3f'
              % (r.b_ledger.median(), r.b_minus_a.median()))
    w = PA[(PA.account == 'walkforward') & (PA.note == 'walk-forward 全窗口')]
    if len(w):
        print('')
        print('walk-forward 全窗口:')
        print(w.groupby(['domain', 'variant', 'rule'])[
            ['b_account', 'd_vs_R1', 'd_vs_R2', 't_vs_R2']].median().round(3).to_string())

if has('B_selection_stability/selection_stability.csv'):
    ST = rd('B_selection_stability/selection_stability.csv')
    H('Q3 选择稳定性 (B=%d)' % ST.B.iloc[0])
    print(ST.groupby(['domain', 'rule']).share.max().unstack().round(3).to_string())

# ---------- Q4 成本 ----------
if has('C_impact/impact_scenarios_all.csv'):
    IM = rd('C_impact/impact_scenarios_all.csv')
    H('Q4 冲击成本情景')
    sq = IM[(IM.form == 'sqrt') & (IM.kappa == 0.5)]
    print('平方根律 kappa=0.5 逐 A 的年化冲击成本 (点) 中位:')
    print(sq.groupby(['period', 'A_yi']).cost_impact_ann.median().unstack().round(3).to_string())
    print('')
    print('四种形式在 A=5亿 kappa=0.5 的成本中位: %s'
          % dict((f, round(float(IM[(IM.form == f) & (IM.A_yi == 5.0)
                                    & (IM.kappa == 0.5)].cost_impact_ann.median()), 3))
                 for f in IM.form.unique()))

if has('C_capacity_scenarios/capacity_all.csv'):
    CP = rd('C_capacity_scenarios/capacity_all.csv')
    H('Q4 容量')
    cc = [c for c in CP.columns if c.startswith('A_star')]
    print(CP.groupby('period')[cc].median().round(2).to_string())

# ---------- 块 D ----------
if has('D_bootstrap/bootstrap_families.csv'):
    BS = rd('D_bootstrap/bootstrap_families.csv')
    H('块 D 多重检验族 (块长 20)')
    b = BS[BS.mean_block == 20]
    rows = []
    for fam, d in b.groupby('family'):
        rows.append(dict(family=fam, m=len(d), pt_med=d.point.median(),
                         pt_max=d.point.max(),
                         pointwise=float(((d.boot_lo > 0) | (d.boot_hi < 0)).mean()),
                         simult=float(((d.simult_lo > 0) | (d.simult_hi < 0)).mean()),
                         crit=float(d.simult_crit.iloc[0])))
    print(pd.DataFrame(rows).round(3).to_string(index=False))
print('')
