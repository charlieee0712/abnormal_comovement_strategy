#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f part2 合并: 块 A 汇总 + 邻域度量 (§4.4) + C1/B2/D 汇总表。只出表, 不下采纳结论。
   用法: python e6f_merge2.py --out DIR
"""
import os, sys, json, time, argparse, collections
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K
import e6f_core as F
import e6f_desc as D

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
A = ap.parse_args()
OUT = A.out
for d in ('neighborhoods', 'A_oat', 'A_interactions', 'A_weights', 'A_neutralization',
          'A_horizon', 'checks', 'logs'):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
_lf = open(os.path.join(OUT, 'logs', 'merge2.log'), 'w', encoding='utf-8', buffering=1)
LOG = []


def P(s=''):
    print(s, flush=True); _lf.write(s + '\n')


def hac(X, L=5):
    o = ~np.isnan(X)
    n = o.sum(axis=0).astype(float)
    mu = np.where(n > 0, np.nansum(np.where(o, X, 0.0), axis=0) / np.maximum(n, 1), np.nan)
    E = np.where(o, X - mu, 0.0)
    Sx = (E * E).sum(axis=0)
    for l in range(1, L + 1):
        Sx += 2.0 * (1 - l / (L + 1.0)) * (E[l:] * E[:-l]).sum(axis=0)
    se = np.where(Sx > 0, np.sqrt(Sx) / np.maximum(n, 1), np.nan)
    with np.errstate(invalid='ignore', divide='ignore'):
        t = np.where((se == se) & (se > 0) & (n >= 10), mu / se, np.nan)
    return mu * 252 * 100.0, t, n.astype(int)


T0 = time.time()
R1, R2 = 'KT_dep(50,50)|C:k5', 'KT_mean@30|C:k5+cr5:k10'
P('=== E6f part2 合并 === %s' % time.strftime('%Y-%m-%d %H:%M:%S'))

# ============================================================
# 1. 块 A 汇总 (四段 × 两支持集)
# ============================================================
SUM = []
for f in sorted(os.listdir(os.path.join(OUT, 'A_oat'))):
    if f.startswith('A_summary_') and f.endswith('.csv'):
        SUM.append(pd.read_csv(os.path.join(OUT, 'A_oat', f)))
SF = pd.concat(SUM, ignore_index=True) if SUM else pd.DataFrame()
P('  块 A 配置-段行 %d; 支持集 %s' % (len(SF), sorted(SF.support.unique()) if len(SF) else []))
if not len(SF):
    P('  !! 块 A 尚无产物, 退出'); sys.exit(1)
tab = SF.groupby(['period', 'support']).agg(n=('config_id', 'size'),
                                            prim=('role', lambda s: int((s == 'primary').sum())))
P(tab.to_string())

# 全窗口: 用日账本重算 (legacy_all 主口径)
G, T_, Pz, mark = [], [], [], []
for s in F.SEGS:
    ps = [os.path.join(OUT, 'daily', 'A_%s_%s__legacy_all.parquet' % (n, s))
          for n in ('gross', 'pos', 'turn')]
    if not all(os.path.exists(p) for p in ps):
        P('  !! 缺 %s 的 legacy_all 日账本, 全窗口表跳过' % s)
        G = None
        break
    g = pd.read_parquet(ps[0]); p_ = pd.read_parquet(ps[1]); t_ = pd.read_parquet(ps[2])
    for n in ('gross', 'pos', 'turn'):
        fx = os.path.join(OUT, 'daily', 'A_%s_%s__legacy_all_fix15.parquet' % (n, s))
        if os.path.exists(fx):
            add = pd.read_parquet(fx)
            if n == 'gross':
                g = pd.concat([g, add], axis=1)
            elif n == 'pos':
                p_ = pd.concat([p_, add], axis=1)
            else:
                t_ = pd.concat([t_, add], axis=1)
    G.append(g); Pz.append(p_); T_.append(t_)
    mark.append(np.array([s] * len(g.index)))

FULL = pd.DataFrame()
if G:
    cols = sorted(set.intersection(*[set(x.columns) for x in G]))
    GG = pd.concat([x.reindex(columns=cols) for x in G], axis=0)
    TT = pd.concat([x.reindex(columns=cols) for x in T_], axis=0)
    PP = pd.concat([x.reindex(columns=cols) for x in Pz], axis=0)
    seg = np.concatenate(mark)
    DT = pd.DatetimeIndex(GG.index)
    N8 = GG.values - TT.values * (F.COST / 1e4)
    N12 = GG.values - TT.values * (F.COST_HI / 1e4)
    V = ~np.isnan(N8).any(axis=1)
    P('  UA 全窗口: %d 配置 × %d 日 (有效 %d)' % (len(cols), len(DT), int(V.sum())))

    # 参照的日序列取自 E6e 账本
    RG, RT = [], []
    for s in F.SEGS:
        RG.append(pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_gross_%s.parquet' % s))
                  [[R1, R2]])
        RT.append(pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_turn_%s.parquet' % s))
                  [[R1, R2]])
    RGG = pd.concat(RG, axis=0); RTT = pd.concat(RT, axis=0)
    # 配对差全靠这一条: 块 A 与 E6e 的日期必须逐位相同, 否则 d_vs_R1/R2 会静默算错
    assert list(RGG.index) == list(DT), '块 A 与 E6e 账本日期不逐位相同, 配对差不可信'
    RN8 = RGG.values - RTT.values * (F.COST / 1e4)

    a8, t8, nn = hac(np.where(V[:, None], N8, np.nan))
    a12, _, _ = hac(np.where(V[:, None], N12, np.nan))
    ag, _, _ = hac(np.where(V[:, None], GG.values, np.nan))
    d1, tt1, _ = hac(np.where(V[:, None], N8 - RN8[:, [0]], np.nan))
    d2, tt2, _ = hac(np.where(V[:, None], N8 - RN8[:, [1]], np.nan))
    pos = np.nanmean(np.where(V[:, None], PP.values, np.nan), axis=0)
    trn = np.nanmean(np.where(V[:, None], TT.values, np.nan), axis=0) * 252
    seg8 = {}
    for s in F.SEGS:
        m = (seg == s) & V
        seg8[s] = np.nanmean(np.where(m[:, None], N8, np.nan), axis=0) * 252 * 100
    FULL = pd.DataFrame(dict(config_id=cols, net8=a8, net12=a12, gross=ag,
                             cost=ag - a8, nw8=t8, turn=trn, pos=pos, n_valid=nn,
                             d_vs_R1=d1, t_vs_R1=tt1, d_vs_R2=d2, t_vs_R2=tt2,
                             **{('net8_' + s[:4]): seg8[s] for s in F.SEGS}))
    FULL['pu_net'] = np.where(FULL.pos > 0, FULL.net8 / FULL.pos, np.nan)
    FULL['n_seg_pos'] = sum((FULL['net8_' + s[:4]] > 0).astype(int) for s in F.SEGS)
    meta = SF[SF.role == 'primary'].drop_duplicates('config_id').set_index('config_id')
    for c in ('layer', 'core_id', 'veto_id', 'family', 'parent_id', 'H', 'neu', 'neu_veto',
              'anchor', 'n_zero_weight'):
        if c in meta.columns:
            FULL[c] = FULL.config_id.map(meta[c])
    # avg_nh / days_nohold 按【有持仓天数】加权合成全窗口 (E6f 阶段 0 的教训)
    pv = SF[SF.role == 'primary'].pivot_table(index='config_id', columns='period',
                                              values='avg_nh')
    nd = SF[SF.role == 'primary'].pivot_table(index='config_id', columns='period',
                                              values='days_nohold')
    Ts = {s: int((seg == s).sum()) for s in F.SEGS}
    npos = pd.DataFrame({s: Ts[s] - nd[s] for s in F.SEGS if s in nd.columns})
    num = sum(pv[s].fillna(0) * npos[s] for s in npos.columns)
    FULL['avg_nh'] = FULL.config_id.map(num / npos.sum(axis=1).replace(0, np.nan))
    FULL['days_nohold'] = FULL.config_id.map(nd.sum(axis=1))
    FULL = FULL.set_index('config_id')
    FULL.to_csv(os.path.join(OUT, 'A_oat', 'A_full_window.csv'))
    P('  写出 A_full_window.csv %d 行' % len(FULL))
    P('  UA net8 全窗口: 中位 %+.3f, p90 %+.3f, 最大 %+.3f (%s); R1 %+.3f R2 %+.3f'
      % (FULL.net8.median(), FULL.net8.quantile(.9), FULL.net8.max(), FULL.net8.idxmax(),
         F.ann(RN8[V, 0]), F.ann(RN8[V, 1])))
    P('  对 R2 配对差 > 0 的 UA 配置占 %.1f%%' % (100 * (FULL.d_vs_R2 > 0).mean()))

# ============================================================
# 2. 分层表
# ============================================================
if len(FULL):
    P('')
    P('=== 分层 (仅 primary; 单位 = 年化点) ===')
    pr = FULL[FULL.layer.notna()]
    lay = pr.groupby('layer').agg(n=('net8', 'size'), net8_med=('net8', 'median'),
                                  net8_max=('net8', 'max'), d_R1_med=('d_vs_R1', 'median'),
                                  d_R1_pos=('d_vs_R1', lambda s: float((s > 0).mean())),
                                  d_R2_med=('d_vs_R2', 'median'),
                                  turn_med=('turn', 'median'), nh_med=('avg_nh', 'median'))
    P(lay.round(3).to_string())
    lay.to_csv(os.path.join(OUT, 'A_oat', 'layer_summary.csv'))
    for lname, fn in (('A_TxC', 'A_interactions/TxC.csv'),
                      ('A_slowC_x_fastC', 'A_interactions/slowC_x_fastC.csv'),
                      ('A_fastC_x_B', 'A_interactions/fastC_x_B.csv'),
                      ('A_KTC_template', 'A_interactions/KTC_template.csv'),
                      ('A_weights', 'A_weights/weights.csv'),
                      ('A_k_platform', 'A_oat/k_platform.csv'),
                      ('A_neutralization', 'A_neutralization/neutralization.csv'),
                      ('A_neutralization_split', 'A_neutralization/neutralization_split.csv'),
                      ('A_horizon', 'A_horizon/horizon.csv'),
                      ('A_oat_P54', 'A_oat/oat_P54.csv'),
                      ('A_oat_A12', 'A_oat/oat_A12.csv'),
                      ('A_veto_window', 'A_oat/veto_window.csv'),
                      ('A_depth_extra', 'A_oat/depth_extra.csv')):
        sub = pr[pr.layer == lname]
        if len(sub):
            os.makedirs(os.path.dirname(os.path.join(OUT, fn)), exist_ok=True)
            sub.to_csv(os.path.join(OUT, fn))

# ============================================================
# 2b. 分量权重按 K/T/C 拆开 (Q5: cond 的贡献落在核里哪一处)
#     A_weights 层是 KTC_mean 的三分量单纯形, 深度与否决固定成对照 ->
#     同深度、同否决下改 T(=cond) 的权重, 就是 cond 在核内的边际。
# ============================================================
if len(FULL):
    P('')
    P('=== 分量权重 (K/T/C 单纯形, 单位 = 1/6) ===')
    CFa = {c['config_id']: c for c in D.gen_all() if c['H'] == 5}
    wr = []
    for cid in FULL.index:
        c = CFa.get(cid)
        if c is None or c['layer'] != 'A_weights':
            continue
        ws = c['core'].get('ws')
        if not ws:
            continue
        rl = [sp['role'] for sp in c['core'].get('comps', [])]
        d_ = dict(config_id=cid, depth=c['core'].get('s'), veto_id=c.get('veto_id'),
                  net8=FULL.net8[cid], d_vs_R2=FULL.d_vs_R2[cid], turn=FULL.turn[cid],
                  avg_nh=FULL.avg_nh[cid])
        for r_, w_ in zip(rl, ws):
            d_['w_' + r_] = round(float(w_) * 6.0)
        wr.append(d_)
    WT = pd.DataFrame(wr)
    if len(WT):
        WT.to_csv(os.path.join(OUT, 'A_weights', 'weights_by_component.csv'), index=False)
        P('  写出 weights_by_component.csv %d 行' % len(WT))
        for r_ in [c for c in WT.columns if c.startswith('w_')]:
            g_ = WT.groupby(r_).agg(n=('net8', 'size'), net8=('net8', 'median'),
                                    dR2=('d_vs_R2', 'median'), turn=('turn', 'median'))
            P('  按 %s (0=该分量完全不进核):' % r_)
            P('    ' + g_.round(3).to_string().replace('\n', '\n    '))
        eq = WT[(WT.get('w_K') == 2) & (WT.get('w_T') == 2) & (WT.get('w_C') == 2)]
        if len(eq):
            P('  等权 (2,2,2) 基准: net8 中位 %+.3f (n=%d)' % (eq.net8.median(), len(eq)))

# ============================================================
# 2c. Q5 cond 时间异质 (§5.2 逐字三对)
#     cond = conditional_turnover = turnover/(|log ret|+1e-4) = 本核里的 K 分量。
#     三对: 阶段结构(dep vs mean) / 核内有无 cond(KTC vs TC, 同深度) / 组合 vs 纯 tvol。
#     配对差按【同日】做, 再按年 HAC(L=5) —— 不是"年均值相减"。
# ============================================================
P('')
P('=== Q5 cond 时间异质 (同日配对差, 逐年) ===')
PAIRS = [('阶段结构', 'KT_dep(50,50)', 'KT_mean@30'),
         ('核内有无 cond (同深度)', 'KTC_mean@25', 'TC_mean@25'),
         ('组合 vs 纯 tvol', R1, 'T@25')]
QG, QT, QM = [], [], []
for s in F.SEGS:
    QG.append(pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_gross_%s.parquet' % s)))
    QT.append(pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_turn_%s.parquet' % s)))
    QM.append(np.array([s] * len(QG[-1].index)))
qc = sorted(set.intersection(*[set(x.columns) for x in QG]))
QGG = pd.concat([x.reindex(columns=qc) for x in QG], axis=0)
QTT = pd.concat([x.reindex(columns=qc) for x in QT], axis=0)
QDT = pd.DatetimeIndex(QGG.index)
QN8 = QGG.values - QTT.values * (F.COST / 1e4)
qi = {c: i for i, c in enumerate(qc)}
crow = []
for nm, a_, b_ in PAIRS:
    if a_ not in qi or b_ not in qi:
        P('  !! %s: 账本里缺 %s' % (nm, a_ if a_ not in qi else b_))
        continue
    d_ = QN8[:, qi[a_]] - QN8[:, qi[b_]]
    for lbl, m_ in ([('全窗口', np.ones(len(QDT), bool))]
                    + [(s, np.array([x == s for x in np.concatenate(QM)])) for s in F.SEGS]
                    + [(str(y), np.asarray(QDT.year == y)) for y in sorted(set(QDT.year))]):
        x_ = np.where(m_, d_, np.nan)
        if (~np.isnan(x_)).sum() < 20:
            continue
        mu, t_, n_ = hac(x_[:, None])
        crow.append(dict(pair=nm, a=a_, b=b_, window=lbl, d_net8=float(mu[0]),
                         hac_t=float(t_[0]), n_days=int(n_[0]),
                         partial_year=bool(lbl == '2026')))
CQ = pd.DataFrame(crow)
if len(CQ):
    CQ.to_csv(os.path.join(OUT, 'B_yearly', 'cond_heterogeneity.csv'), index=False)
    P('  写出 cond_heterogeneity.csv %d 行' % len(CQ))
    P(CQ[CQ.window.isin(['全窗口'] + list(F.SEGS))]
      .pivot_table(index='pair', columns='window', values='d_net8').round(3).to_string())
    yr = CQ[CQ.window.str.match(r'^\d{4}$')]
    for nm in CQ.pair.unique():
        g_ = yr[yr.pair == nm]
        P('  %s: 逐年 Δ 为正的年份 %d/%d; 最好 %s(%+.2f), 最差 %s(%+.2f)'
          % (nm, int((g_.d_net8 > 0).sum()), len(g_),
             g_.loc[g_.d_net8.idxmax(), 'window'], g_.d_net8.max(),
             g_.loc[g_.d_net8.idxmin(), 'window'], g_.d_net8.min()))

# ============================================================
# 3. 邻域度量 (§4.4)
# ============================================================
P('')
P('=== 邻域度量 ===')
CF = {c['config_id']: c for c in D.gen_all()}
ORD = {'depth': [15, 20, 25, 30, 35, 40, 50, 60],
       'a': [45, 50, 55, 60, 65, 70], 'b': [45, 50, 55, 60, 65, 70],
       'T': D.GT, 'C': D.GC, 'K': D.GK_W, 'Cf': D.GCF, 'B': D.GB}
KORD = [5, 10, 15, 20]


def coords(c):
    """有序坐标 + 类别键。类别变换不伪造距离 -> 只在类别键完全相同的桶内找邻居。"""
    core = c['core']
    o = {}
    cat = [core['fam'], core['kind'], core.get('neu', 'NS'), core.get('neu_veto') or '',
           str(c['H'])]
    if core.get('s') is not None:
        o['depth'] = core['s']
    if core.get('a') is not None:
        o['a'] = core['a']; o['b'] = core['b']
    for i, sp in enumerate(core.get('comps', []) + ([core['x']] if core.get('x') else [])
                           + core.get('ys', [])):
        r = sp['role']
        o['%s%d' % (r, i)] = sp['w']
        cat.append('%s%d:%s/%s' % (r, i, sp.get('est', ''), sp.get('base', '')))
        if r == 'K':
            cat.append('eps%.0e' % sp['eps'])
        if r == 'B':
            cat.append('adj%d' % int(bool(sp.get('adj'))))
    if core.get('ws') is not None:
        cat.append('W')
        for i, w in enumerate(core['ws']):
            o['w%d' % i] = float(w) * 6.0
    v = c['veto']
    if v:
        cat.append(v['kind'] + ':' + str(v.get('how', '')))
        for i, (sp, k) in enumerate(v['legs']):
            o['vk%d' % i] = k
            cat.append('v%d:%s' % (i, F.fid(sp)))
    else:
        cat.append('noveto')
    return o, tuple(cat)


def grid_of(name):
    if name in ORD:
        return ORD[name]
    if name.startswith('vk'):
        return KORD
    for r in ('T', 'C', 'K', 'Cf', 'B'):
        if name.startswith(r) and name[len(r):].isdigit():
            return ORD[r]
    if name.startswith('w'):
        return list(range(0, 7))
    return None


bucket = collections.defaultdict(list)
CO = {}
for cid, c in CF.items():
    o, cat = coords(c)
    CO[cid] = o
    bucket[cat].append(cid)
NB = collections.defaultdict(list)
for cat, mem in bucket.items():
    for i in range(len(mem)):
        oi = CO[mem[i]]
        for j in range(i + 1, len(mem)):
            oj = CO[mem[j]]
            if set(oi) != set(oj):
                continue
            diff = [k for k in oi if oi[k] != oj[k]]
            if len(diff) == 1:
                g = grid_of(diff[0])
                if g and oi[diff[0]] in g and oj[diff[0]] in g \
                        and abs(g.index(oi[diff[0]]) - g.index(oj[diff[0]])) == 1:
                    NB[mem[i]].append(mem[j]); NB[mem[j]].append(mem[i])
            elif len(diff) == 2 and all(k.startswith('w') for k in diff):
                # 单纯形边: 1/6 权重从一分量移到另一分量
                a, b = diff
                if abs((oi[a] - oj[a]) + (oi[b] - oj[b])) < 1e-9 and abs(oi[a] - oj[a]) == 1:
                    NB[mem[i]].append(mem[j]); NB[mem[j]].append(mem[i])
deg = [len(NB.get(c, [])) for c in CF]
P('  邻居图: 有邻居的节点 %d/%d, 度中位 %d, 度最大 %d, 孤立 %d'
  % (sum(1 for d_ in deg if d_), len(deg), int(np.median(deg)), max(deg),
     sum(1 for d_ in deg if d_ == 0)))

rows = []
if len(FULL):
    n8 = FULL.net8.to_dict(); pu = FULL.pu_net.to_dict(); tn = FULL.turn.to_dict()
    for cid in CF:
        nb = [x for x in NB.get(cid, []) if x in n8]
        if cid not in n8:
            continue
        dv = np.array([n8[x] - n8[cid] for x in nb]) if nb else np.array([])
        dp = np.array([pu[x] - pu[cid] for x in nb]) if nb else np.array([])
        o = CO[cid]
        boundary = any((grid_of(k) or [None]) and o[k] in (grid_of(k) or [0])[:1] +
                       (grid_of(k) or [0])[-1:] for k in o if grid_of(k))
        r = dict(config_id=cid, n_neighbors=len(nb), net8=n8[cid], pu_net=pu.get(cid),
                 turn=tn.get(cid), on_grid_boundary=bool(boundary),
                 few_neighbors=bool(len(nb) < 2))
        if len(dv):
            r.update(d_med=float(np.median(dv)), d_p10=float(np.percentile(dv, 10)),
                     d_p90=float(np.percentile(dv, 90)), d_min=float(dv.min()),
                     dpu_med=float(np.nanmedian(dp)))
            for tau in (0.1, 0.3, 0.5):
                r['cover_tau%.1f' % tau] = float(np.mean(np.abs(dv) <= tau))
        rows.append(r)
NBt = pd.DataFrame(rows)
NBt.to_csv(os.path.join(OUT, 'neighborhoods', 'neighborhood_metrics.csv'), index=False)
if len(NBt):
    P('  写出 neighborhood_metrics.csv %d 行' % len(NBt))
    ok = NBt[NBt.n_neighbors > 0]
    P('  邻居 Δnet8 中位的分布: 中位 %+.3f, p10 %+.3f, p90 %+.3f'
      % (ok.d_med.median(), ok.d_med.quantile(.1), ok.d_med.quantile(.9)))
    for tau in (0.1, 0.3, 0.5):
        P('  容忍带 τ=%.1f 的邻居覆盖率 中位 %.2f' % (tau, ok['cover_tau%.1f' % tau].median()))
    P('  网格边界节点 %d, 有效邻居 <2 的节点 %d'
      % (int(NBt.on_grid_boundary.sum()), int(NBt.few_neighbors.sum())))
pd.DataFrame([dict(config_id=k, neighbors='|'.join(v)) for k, v in NB.items()]).to_csv(
    os.path.join(OUT, 'neighborhoods', 'neighbor_graph.csv'), index=False)

# ============================================================
# 4. C1 / B2 / D 汇总
# ============================================================
P('')
P('=== C1 / B2 / D ===')
for nm, sub, pat in (('C1 画像', 'C_exposures', 'profile_'),
                     ('C1 冲击情景', 'C_impact', 'impact_scenarios_'),
                     ('C1 容量情景', 'C_capacity_scenarios', 'capacity_'),
                     ('C1 订单', 'C_orders', 'orders_'),
                     ('B2 政策账户', 'B_walkforward', 'policy_accounts_'),
                     ('C2 影子账户', 'C_shadow_accounts', 'shadow_accounts_')):
    d = os.path.join(OUT, sub)
    # 排除 (a) 自己上一轮写出的 *_all.csv, 否则重跑会把汇总表当分片再并一次;
    #      (b) *_H_* —— 持有期分支 (H≠5) 的画像/情景与 H5 主表不是一回事, 另并一张表
    fs = [f for f in os.listdir(d)
          if f.startswith(pat) and f.endswith('.csv')
          and not f.endswith('_all.csv') and '_H_' not in f] if os.path.isdir(d) else []
    if not fs:
        P('  %s: 无产物 (待该阶段完成)' % nm); continue
    df = pd.concat([pd.read_csv(os.path.join(d, f)) for f in fs], ignore_index=True)
    df.to_csv(os.path.join(OUT, sub, pat.rstrip('_') + '_all.csv'), index=False)
    P('  %s: %d 行 (%d 个分片)' % (nm, len(df), len(fs)))
    hs = [f for f in os.listdir(d)
          if f.startswith(pat) and f.endswith('.csv') and '_H_' in f and '_all' not in f]
    if hs:
        dh = pd.concat([pd.read_csv(os.path.join(d, f)) for f in hs], ignore_index=True)
        dh.to_csv(os.path.join(OUT, sub, pat.rstrip('_') + '_H_all.csv'), index=False)
        P('    (持有期分支另并 %s_H_all.csv: %d 行 / %d 分片)'
          % (pat.rstrip('_'), len(dh), len(hs)))

# ============================================================
# 5. 政策账户 a / b / b−a 读法 (§5.2)
#    a      = 训练窗内被选中集合的【账本加权平均】net8   (样本内)
#    b_led  = 评估窗内同一集合的【账本加权平均】net8     (同口径 -> b_led − a = 纯选择衰减)
#    b_acct = 评估窗内【真实混合政策账户】的 net8        (b_acct − b_led = 混合省下的换手)
#    Δ vs R1/R2 = 同日配对差 + HAC(L=5) SE
# ============================================================
P('')
P('=== 政策账户 a/b/b−a ===')
PA = pd.DataFrame()
sel_p = os.path.join(OUT, 'B_nested', 'selected_sets.csv')
pol_ps = [os.path.join(OUT, 'B_walkforward', 'policy_gross_%s.parquet' % s) for s in F.SEGS]
if os.path.exists(sel_p) and all(os.path.exists(p) for p in pol_ps):
    SEL = pd.read_csv(sel_p)
    # --- 账本 (E6e U0 + 块 A UA), 与 b2_select 同一构造 ---
    LG, LT, LM = [], [], []
    for s in F.SEGS:
        g = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_gross_%s.parquet' % s))
        t = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_turn_%s.parquet' % s))
        ug = os.path.join(OUT, 'daily', 'A_gross_%s__legacy_all.parquet' % s)
        if os.path.exists(ug):
            a_ = pd.read_parquet(ug); b_ = pd.read_parquet(
                os.path.join(OUT, 'daily', 'A_turn_%s__legacy_all.parquet' % s))
            for n_, tgt in (('gross', a_), ('turn', b_)):
                fx = os.path.join(OUT, 'daily', 'A_%s_%s__legacy_all_fix15.parquet' % (n_, s))
                if os.path.exists(fx):
                    add = pd.read_parquet(fx)
                    for c_ in add.columns:
                        tgt[c_] = add[c_].values
            a_.columns = ['UA::' + c_ for c_ in a_.columns]
            b_.columns = ['UA::' + c_ for c_ in b_.columns]
            g = pd.concat([g, a_], axis=1); t = pd.concat([t, b_], axis=1)
        LG.append(g); LT.append(t); LM.append(np.array([s] * len(g.index)))
    lcols = sorted(set.intersection(*[set(x.columns) for x in LG]))
    LGG = pd.concat([x.reindex(columns=lcols) for x in LG], axis=0)
    LTT = pd.concat([x.reindex(columns=lcols) for x in LT], axis=0)
    LDT = pd.DatetimeIndex(LGG.index)
    LN8 = LGG.values - LTT.values * (F.COST / 1e4)
    lci = {c: i for i, c in enumerate(lcols)}
    # --- 政策账户日序列 ---
    PG = pd.concat([pd.read_parquet(p) for p in pol_ps], axis=0)
    PT = pd.concat([pd.read_parquet(os.path.join(OUT, 'B_walkforward',
                                                 'policy_turn_%s.parquet' % s))
                    for s in F.SEGS], axis=0)
    assert list(PG.index) == list(LDT), '政策账户日期与账本不齐'
    PN8 = PG.values - PT.values * (F.COST / 1e4)
    pci = {c: i for i, c in enumerate(PG.columns)}
    refj = {r: pci['REF::' + r] for r in (R1, R2) if 'REF::' + r in pci}

    def _led(members, mask):
        j = [lci[c] for c, _ in members if c in lci]
        w = np.array([a_ for c, a_ in members if c in lci], float)
        if not j or mask.sum() < 20:
            return np.nan
        X = LN8[np.ix_(mask, j)] @ (w / w.sum())
        m = ~np.isnan(X)
        return float(np.mean(X[m])) * 252 * 100.0 if m.any() else np.nan

    prow = []
    key_cols = ['domain', 'split', 'direction', 'variant', 'rule', 'account']
    for key, sub in SEL.groupby(key_cols):
        dom, split, direc, var, rule, acct = key
        nm_ = '%s|%s|%s|%s|%s|%s' % key
        if acct == 'single':
            ev = LDT > pd.Timestamp(split) if direc == 'forward' else LDT <= pd.Timestamp(split)
            tr = ~ev
            mem = [(r.config_id, float(r.weight)) for _, r in sub.iterrows()]
            a_v = float(np.average(sub.train_score, weights=sub.weight))
            r_ = dict(zip(key_cols, key), n_members=sub.config_id.nunique(),
                      a_train=a_v, b_ledger=_led(mem, ev), b_account=np.nan,
                      d_vs_R1=np.nan, t_vs_R1=np.nan, d_vs_R2=np.nan, t_vs_R2=np.nan,
                      eval_days=int(ev.sum()),
                      note='' if direc == 'forward'
                      else '反向=迁移诊断, 只出静态 b_ledger, 不建政策账户')
            if nm_ in pci and direc == 'forward':
                x = PN8[:, pci[nm_]]
                r_['b_account'] = F.ann(x[ev])
                for lbl, rj in (('R1', refj.get(R1)), ('R2', refj.get(R2))):
                    if rj is None:
                        continue
                    d_ = np.where(ev, x - PN8[:, rj], np.nan)
                    mu, t_, _ = hac(d_[:, None])
                    r_['d_vs_' + lbl] = float(mu[0]); r_['t_vs_' + lbl] = float(t_[0])
            r_['b_minus_a'] = r_['b_ledger'] - a_v
            r_['mix_gain'] = r_['b_account'] - r_['b_ledger']
            prow.append(r_)
        elif nm_ in pci:
            x = PN8[:, pci[nm_]]
            yrs = LDT.year
            r_ = dict(zip(key_cols, key), n_members=sub.config_id.nunique(),
                      a_train=np.nan, b_ledger=np.nan, b_account=F.ann(x),
                      b_minus_a=np.nan, mix_gain=np.nan,
                      eval_days=int((~np.isnan(x)).sum()), note='walk-forward 全窗口')
            for lbl, rj in (('R1', refj.get(R1)), ('R2', refj.get(R2))):
                if rj is None:
                    continue
                mu, t_, _ = hac((x - PN8[:, rj])[:, None])
                r_['d_vs_' + lbl] = float(mu[0]); r_['t_vs_' + lbl] = float(t_[0])
            prow.append(r_)
            for y in sorted(set(yrs)):
                m_ = (yrs == y) & ~np.isnan(x)
                if m_.sum() < 20:
                    continue
                prow.append(dict(zip(key_cols, key), n_members=sub.config_id.nunique(),
                                 a_train=np.nan, b_ledger=np.nan, b_account=F.ann(x[m_]),
                                 b_minus_a=np.nan, mix_gain=np.nan, eval_days=int(m_.sum()),
                                 d_vs_R1=(F.ann((x - PN8[:, refj[R1]])[m_])
                                          if R1 in refj else np.nan),
                                 d_vs_R2=(F.ann((x - PN8[:, refj[R2]])[m_])
                                          if R2 in refj else np.nan),
                                 t_vs_R1=np.nan, t_vs_R2=np.nan,
                                 note='年度 %d%s' % (y, ' (部分年)' if y == 2026 else '')))
    PA = pd.DataFrame(prow)
    PA.to_csv(os.path.join(OUT, 'B_walkforward', 'policy_readout.csv'), index=False)
    P('  写出 policy_readout.csv %d 行' % len(PA))
    sg = PA[(PA.account == 'single') & (PA.direction == 'forward')]
    if len(sg):
        P('  单次(前向): a 中位 %+.2f, b_ledger 中位 %+.2f, b−a 中位 %+.2f, 混合增益中位 %+.3f'
          % (sg.a_train.median(), sg.b_ledger.median(), sg.b_minus_a.median(),
             sg.mix_gain.median()))
        P('  按规则 b−a 中位: %s'
          % {k: round(v, 2) for k, v in sg.groupby('rule').b_minus_a.median().items()})
        P('  b_account 对 R2 的配对差: 中位 %+.3f, |t|>2 的比例 %.2f'
          % (sg.d_vs_R2.median(), float((sg.t_vs_R2.abs() > 2).mean())))
    rv = PA[PA.direction == 'reverse']
    if len(rv):
        P('  反向(迁移诊断, 只有静态 b_ledger): 中位 %+.2f, b−a 中位 %+.2f'
          % (rv.b_ledger.median(), rv.b_minus_a.median()))
    wf = PA[(PA.account == 'walkforward') & (PA.note == 'walk-forward 全窗口')]
    if len(wf):
        P('  walk-forward 全窗口 net8 中位 %+.3f; 对 R2 中位 %+.3f'
          % (wf.b_account.median(), wf.d_vs_R2.median()))
else:
    P('  缺 selected_sets.csv 或政策账户日序列, 跳过 (待 B2 完成)')

# ============================================================
# 6. E6c 持有期锚 (§9)
# ============================================================
P('')
P('=== E6c H 锚 (A4b_CVRv5, legacy_all) ===')
HR = []
try:
    for s in F.SEGS:
        sf = pd.read_csv(os.path.join(F.E6C_DIR, 'sf_%s.csv' % s))
        dl = pd.read_parquet(os.path.join(F.E6C_DIR, 'daily_%s.parquet' % s))
        for H_ in (3, 4, 5, 7, 10):
            r = sf[(sf.cfg == 'A4b_CVRv5') & (sf.hold == H_) & (sf.scope == 'legacy_all')]
            d = dl[(dl.cfg == 'A4b_CVRv5') & (dl.hold == H_)]
            if not len(r) or not len(d):
                continue
            x = d.gross.values - d.turnover.values * (F.COST / 1e4)
            HR.append(dict(period=s, cfg='A4b_CVRv5', hold=H_,
                           e6c_net8_ann=float(r.net8_ann.iloc[0]),
                           recomputed=F.ann(x), n_days=int((~np.isnan(x)).sum()),
                           d_abs=abs(float(r.net8_ann.iloc[0]) - F.ann(x))))
except Exception as e:
    P('  !! E6c 锚读取失败: %s' % e)
HA = pd.DataFrame(HR)
if len(HA):
    HA.to_csv(os.path.join(OUT, 'checks', 'e6c_horizon_anchor.csv'), index=False)
    P('  %d 格 (4 段 × 5 个 H); max|d| = %.3e; 全部 <1e-10: %s'
      % (len(HA), HA.d_abs.max(), bool(HA.d_abs.max() < 1e-10)))
    P('  E6c A4b_CVRv5 net8 逐 H (段 × H):')
    P(HA.pivot_table(index='period', columns='hold', values='e6c_net8_ann').round(3).to_string())
    P('  注: A4b_CVRv5 是 v2 形态, 不在 E6f 描述符空间内, 无法在本核重建 —— 本表锚的是【年化与'
      '净额口径与 E6c 一致】; 持有期机制本身的锚在自测组 4 (sparse_pnl_H 逐 H = 生产引擎)。')
else:
    P('  !! 未取到 E6c A4b_CVRv5 的 H 行')

# ============================================================
# 7. legacy_all vs history_warmed
# ============================================================
P('')
P('=== 支持集对照 legacy_all vs history_warmed ===')
WR = []
if len(SF) and 'history_warmed' in set(SF.support.unique()):
    pr_ = SF[SF.role == 'primary']
    for s in F.SEGS:
        a_ = pr_[(pr_.period == s) & (pr_.support == 'legacy_all')].set_index('config_id')
        b_ = pr_[(pr_.period == s) & (pr_.support == 'history_warmed')].set_index('config_id')
        com = a_.index.intersection(b_.index)
        if not len(com):
            continue
        WR.append(dict(period=s, n=len(com),
                       d_net8_med=float((b_.net8[com] - a_.net8[com]).median()),
                       d_net8_p10=float((b_.net8[com] - a_.net8[com]).quantile(.1)),
                       d_net8_p90=float((b_.net8[com] - a_.net8[com]).quantile(.9)),
                       d_net8_absmax=float((b_.net8[com] - a_.net8[com]).abs().max()),
                       share_up=float((b_.net8[com] > a_.net8[com]).mean()),
                       d_nh_med=float((b_.avg_nh[com] - a_.avg_nh[com]).median()),
                       d_days_nohold_med=float((b_.days_nohold[com]
                                                - a_.days_nohold[com]).median()),
                       d_turn_med=float((b_.turn[com] - a_.turn[com]).median()),
                       nohold_legacy=str(dict(a_.days_nohold[com].value_counts().head(4))),
                       nohold_warmed=str(dict(b_.days_nohold[com].value_counts().head(4)))))
WA = pd.DataFrame(WR)
if len(WA):
    WA.to_csv(os.path.join(OUT, 'A_oat', 'support_compare.csv'), index=False)
    P(WA.drop(columns=['nohold_legacy', 'nohold_warmed']).round(4).to_string(index=False))
    for _, r in WA.iterrows():
        P('  %s 无持仓日取值: legacy %s -> warmed %s'
          % (r.period, r.nohold_legacy, r.nohold_warmed))
    P('  读法: 预热只提前【因子】的可见历史, clean/基准/pool0 冻结不重算, 所以段头 19 天'
      '(mature 过滤) 无论如何都空 —— 这是 legacy_all 下 days_nohold 的下限。超出 19 的部分'
      '正好是核里最长窗因子的 min_periods−1 (T60 -> mp=30 -> 29 天; 更长窗 -> 44/59 天),'
      '预热把这一段截断整个抹掉。2024-2026 预热后 4,602 个配置【全部】落回 19, 即预期结果;'
      '2015-2018 还剩 339 个停在 23~25, 是可预热的源历史不足以填满最长窗。'
      'net8 中位反而略降 (share_up<0.5): 多出来的日子都在段初、平均比段内其余日子差,'
      '是分母变化的机械稀释, 不是因子变好变坏。')
lim = os.path.join(OUT, 'checks', 'warm_2010-2014__history_warmed.json')
if os.path.exists(lim):
    P('  2010-2014 history_warmed: %s' % json.load(open(lim, encoding='utf-8')).get('status'))

json.dump(dict(stage='merge2', when=time.strftime('%Y-%m-%d %H:%M:%S'),
               n_blockA_rows=len(SF), n_full=len(FULL), n_neighborhood=len(NBt),
               n_policy_readout=len(PA), n_e6c_anchor=len(HA),
               e6c_anchor_max_abs=(float(HA.d_abs.max()) if len(HA) else None),
               n_support_compare=len(WA),
               seconds=time.time() - T0),
          open(os.path.join(OUT, 'checks', 'merge2.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
P('')
P('part2 合并完成 %.0fs' % (time.time() - T0))
_lf.close()
