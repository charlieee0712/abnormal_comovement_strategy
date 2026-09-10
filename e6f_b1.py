#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 块 B1: 只读账本的时间面板 (§5.1)。全部基于 E6e 已存日账本, 不跑引擎。
   用法: python e6f_b1.py --out DIR
"""
import os, sys, json, time, argparse
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K
import e6f_core as F

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
A = ap.parse_args()
OUT = A.out
for d in ('B_yearly', 'B_leaveout', 'B_rolling', 'B_split', 'checks'):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
LOG = []
NOTE = []


def P(s=''):
    print(s, flush=True); LOG.append(s)


def chk(name, cond, detail=''):
    P('  %-50s %s %s' % (name, 'OK  ' if cond else '!!  ', detail))
    if not cond:
        NOTE.append(dict(item=name, detail=detail))


T0 = time.time()
R1, R2 = 'KT_dep(50,50)|C:k5', 'KT_mean@30|C:k5+cr5:k10'
P('=== E6f B1 只读账本 === %s' % time.strftime('%Y-%m-%d %H:%M:%S'))

# ---------------- 载入 ----------------
G, T_, Pz, mark = [], [], [], []
for s in F.SEGS:
    G.append(pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_gross_%s.parquet' % s)))
    T_.append(pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_turn_%s.parquet' % s)))
    Pz.append(pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_pos_%s.parquet' % s)))
    mark.append(np.array([s] * len(G[-1].index)))
allc = sorted(set.intersection(*[set(x.columns) for x in G]))
DOM = pd.read_csv(os.path.join(OUT, 'domain_U0.csv'))
cols = [c for c in DOM.config_id if c in set(allc)]
for r in (R1, R2):
    if r not in cols:
        cols.append(r)
GG = pd.concat([x.reindex(columns=cols) for x in G], axis=0)
TT = pd.concat([x.reindex(columns=cols) for x in T_], axis=0)
PP = pd.concat([x.reindex(columns=cols) for x in Pz], axis=0)
seg = np.concatenate(mark)
DT = pd.DatetimeIndex(GG.index)
yr, mo = DT.year.values, DT.month.values
Gv, Tv, Pv = GG.values, TT.values, PP.values
N8 = Gv - Tv * (F.COST / 1e4)
N12 = Gv - Tv * (F.COST_HI / 1e4)
Tn, Nc = N8.shape
P('配置 %d (U0-broad %d + 参照), 日 %d, 段 %s' % (Nc, len(DOM), Tn, dict(pd.Series(seg).value_counts())))

obs = ~np.isnan(N8)
common = obs.all(axis=1)
chk('NaN 模式跨配置一致 (基准全 NaN 日)', bool((obs.any(axis=1) == common).all()),
    '共同有效日 %d, 无效日 %d' % (int(common.sum()), int((~common).sum())))
chk('无效日 = 76', int((~common).sum()) == 76, '%d' % int((~common).sum()))
V = common
iR1, iR2 = cols.index(R1), cols.index(R2)


def hac_mat(D, L=5, minn=10):
    """D=(T,N) 含 NaN 的日序列 -> (年化, HAC t, n)。缺口安全, 与 e6e score_hac 同式。"""
    o = ~np.isnan(D)
    n = o.sum(axis=0).astype(float)
    mu = np.where(n > 0, np.nansum(np.where(o, D, 0.0), axis=0) / np.maximum(n, 1), np.nan)
    E = np.where(o, D - mu, 0.0)
    S = (E * E).sum(axis=0)
    for l in range(1, L + 1):
        if l < D.shape[0]:
            S += 2.0 * (1 - l / (L + 1.0)) * (E[l:] * E[:-l]).sum(axis=0)
    se = np.where(S > 0, np.sqrt(S) / np.maximum(n, 1), np.nan)
    with np.errstate(invalid='ignore', divide='ignore'):
        t = np.where((se == se) & (se > 0) & (n >= minn), mu / se, np.nan)
    return mu * 252 * 100.0, t, n.astype(int)


def blockstats(rowmask, tag, extra=None):
    """一个日期子集上的全字段 + 对 R1/R2 的同日配对差。"""
    m = rowmask & V
    n = int(m.sum())
    if n == 0:
        return None
    d = dict(window=tag, n_days=n,
             start=str(DT[m][0].date()), end=str(DT[m][-1].date()))
    a8, t8, _ = hac_mat(np.where(m[:, None], N8, np.nan))
    a12, _, _ = hac_mat(np.where(m[:, None], N12, np.nan))
    ag, _, _ = hac_mat(np.where(m[:, None], Gv, np.nan))
    d['net8'] = a8; d['net12'] = a12; d['gross'] = ag; d['nw8'] = t8
    d['cost'] = ag - a8
    d['turn'] = Tv[m].mean(axis=0) * 252
    d['pos'] = Pv[m].mean(axis=0)
    for nm, i in (('R1', iR1), ('R2', iR2)):
        D = np.where(m[:, None], N8 - N8[:, [i]], np.nan)
        dv, tv, _ = hac_mat(D)
        d['d_vs_' + nm] = dv
        d['t_vs_' + nm] = tv
        with np.errstate(invalid='ignore', divide='ignore'):
            d['se_vs_' + nm] = np.where(np.abs(tv) > 0, np.abs(dv / tv), np.nan)
    if extra:
        d.update(extra)
    return d


def to_frame(rows):
    out = []
    for d in rows:
        if d is None:
            continue
        f = pd.DataFrame({k: v for k, v in d.items() if isinstance(v, np.ndarray)}, index=cols)
        for k, v in d.items():
            if not isinstance(v, np.ndarray):
                f[k] = v
        out.append(f.reset_index().rename(columns={'index': 'config_id'}))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


# ---------------- 逐年 / 段 / 全窗口 ----------------
P('')
P('=== 逐年 / 段 / 全窗口 ===')
years = sorted(set(yr))
rows = []
for y in years:
    partial = (y == 2026)
    rows.append(blockstats(yr == y, 'year_%d' % y,
                           dict(kind='year', year=y, partial_year=partial)))
for s in F.SEGS:
    rows.append(blockstats(seg == s, 'seg_' + s, dict(kind='segment', year=-1, partial_year=False)))
rows.append(blockstats(np.ones(Tn, bool), 'full', dict(kind='full', year=-1, partial_year=False)))
YB = to_frame(rows)
YB.to_csv(os.path.join(OUT, 'B_yearly', 'panel_year_segment_full.csv'), index=False)
P('  写出 panel_year_segment_full.csv %d 行 (%d 年 + 4 段 + 全窗口)' % (len(YB), len(years)))
ycomp = YB[YB.kind == 'year'].pivot(index='config_id', columns='year', values='net8')
P('  完整年 %d 个, 部分年 %d 个 (2026)' % (len(years) - 1, 1))

# 与 E6e yearly.csv 对锚
ref = pd.read_csv(os.path.join(F.E6E_DIR, 'summary', 'yearly.csv'))
mg = ref.merge(YB[YB.kind == 'year'][['config_id', 'year', 'net8']], on=['config_id', 'year'],
               how='inner', suffixes=('_ref', '_new'))
if len(mg):
    dd = float((mg.net8_ref - mg.net8_new).abs().max())
    chk('逐年对 E6e yearly.csv (%d 个配置-年)' % len(mg), dd < 1e-10, 'max|d|=%.3e' % dd)
sf = pd.concat([pd.read_csv(os.path.join(F.E6E_DIR, 'summary', 'sf_%s.csv' % s)) for s in F.SEGS],
               ignore_index=True)
sfp = sf.pivot_table(index='config_id', columns='period', values='net8_ann')
segt = YB[YB.kind == 'segment'].copy()
segt['period'] = segt.window.str.replace('seg_', '', regex=False)
mg2 = segt.merge(sfp.stack().rename('ref').reset_index(), on=['config_id', 'period'], how='inner')
if len(mg2):
    dd = float((mg2.net8 - mg2.ref).abs().max())
    chk('段 net8 对 sf_*.csv (%d 行)' % len(mg2), dd < 1e-9, 'max|d|=%.3e' % dd)

# ---------------- 年度集中度 (三种) ----------------
P('')
P('=== 年度集中度 (三种分母, 不裁剪) ===')
tot_signed = np.where(V[:, None], N8, 0.0).sum(axis=0)
tot_pos = np.where(V[:, None], np.maximum(N8, 0), 0.0).sum(axis=0)
tot_abs = np.where(V[:, None], np.abs(N8), 0.0).sum(axis=0)
crow = []
for y in years:
    m = (yr == y) & V
    s_signed = np.where(m[:, None], N8, 0.0).sum(axis=0)
    s_pos = np.where(m[:, None], np.maximum(N8, 0), 0.0).sum(axis=0)
    s_abs = np.where(m[:, None], np.abs(N8), 0.0).sum(axis=0)
    with np.errstate(invalid='ignore', divide='ignore'):
        crow.append(pd.DataFrame(dict(
            config_id=cols, year=y, partial_year=(y == 2026),
            share_signed=np.where(np.abs(tot_signed) > 1e-12, s_signed / tot_signed, np.nan),
            share_positive=np.where(tot_pos > 1e-12, s_pos / tot_pos, np.nan),
            share_abs=np.where(tot_abs > 1e-12, s_abs / tot_abs, np.nan),
            denom_signed=tot_signed,
            denom_flag=np.where(tot_signed <= 0, 'nonpositive',
                                np.where(np.abs(tot_signed) < 1e-6, 'near_zero', 'ok')),
            contrib_signed=s_signed)))
CC = pd.concat(crow, ignore_index=True)
CC.to_csv(os.path.join(OUT, 'B_yearly', 'annual_concentration.csv'), index=False)
nflag = int((CC.groupby('config_id').denom_flag.first() != 'ok').sum())
P('  写出 annual_concentration.csv %d 行; 分母非正/近零的配置 %d 个 (已标记, 未裁剪)' % (len(CC), nflag))

top = CC[~CC.partial_year].sort_values('contrib_signed', ascending=False).groupby('config_id')
TB = pd.DataFrame(dict(
    config_id=[k for k, _ in top],
    top1_year=[g.year.iloc[0] for _, g in top],
    top1_share=[g.share_signed.iloc[0] for _, g in top],
    top2_share=[g.share_signed.iloc[:2].sum() for _, g in top],
    worst_year=[g.year.iloc[-1] for _, g in top],
    worst_share=[g.share_signed.iloc[-1] for _, g in top]))
TB.to_csv(os.path.join(OUT, 'B_yearly', 'top_bottom_years.csv'), index=False)

# ---------------- 留一年 / 留 2015-16 ----------------
P('')
P('=== 留一年 / 留 2015-16 (含留年后的实际同日 Δ) ===')
rows = []
for y in years:
    rows.append(blockstats(yr != y, 'drop_%d' % y, dict(kind='leave_one_year', dropped=y)))
rows.append(blockstats(~np.isin(yr, [2015, 2016]), 'drop_2015_2016',
                       dict(kind='leave_1516', dropped=-1516)))
LB = to_frame(rows)
LB.to_csv(os.path.join(OUT, 'B_leaveout', 'leave_one_year.csv'), index=False)
P('  写出 leave_one_year.csv %d 行' % len(LB))

# ---------------- 滚动窗 3/5 年 ----------------
P('')
P('=== 3/5 年滚动窗 (每年 1 月起; 完整窗主表, 截尾窗另表) ===')
full_rows, trunc_rows = [], []
last = DT[-1]
for w in (3, 5):
    for y in years:
        st = pd.Timestamp('%d-01-01' % y)
        en = pd.Timestamp('%d-01-01' % (y + w))
        m = (DT >= st) & (DT < en)
        if m.sum() == 0:
            continue
        complete = en <= last + pd.Timedelta(days=1)
        d = blockstats(m, '%dy_%d' % (w, y),
                       dict(kind='rolling%dy' % w, start_year=y, complete_window=bool(complete)))
        (full_rows if complete else trunc_rows).append(d)
RB = to_frame(full_rows)
RB.to_csv(os.path.join(OUT, 'B_rolling', 'rolling_windows_complete.csv'), index=False)
RT = to_frame(trunc_rows)
RT.to_csv(os.path.join(OUT, 'B_rolling', 'rolling_windows_truncated.csv'), index=False)
P('  完整窗 %d 组, 截尾窗 %d 组' % (len(full_rows), len(trunc_rows)))

# ---------------- 逐月 ----------------
P('')
P('=== 逐月 ===')
ym = yr * 100 + mo
umo = sorted(set(ym))
MM = np.zeros((len(umo), Nc))
MD = np.zeros((len(umo), Nc))
for i, u in enumerate(umo):
    m = (ym == u) & V
    MM[i] = np.where(m[:, None], N8, 0.0).sum(axis=0)
    MD[i] = np.where(m[:, None], N8 - N8[:, [iR1]], 0.0).sum(axis=0)
pd.DataFrame(MM, index=umo, columns=cols).to_csv(os.path.join(OUT, 'B_yearly', 'monthly_net8_sum.csv'))
P('  写出 monthly_net8_sum.csv %d 月 × %d 配置' % (len(umo), Nc))

# ---------------- 最差 k 日窗口 + 回撤 ----------------
P('')
P('=== 最差 5/20/60 日窗口 + 回撤 (主组合与配对差) ===')


def worst_and_dd(X):
    Z = np.where(V[:, None], X, 0.0)
    cs = np.vstack([np.zeros((1, Nc)), np.cumsum(Z, axis=0)])
    out = {}
    for k in (5, 20, 60):
        s = cs[k:] - cs[:-k]
        out['worst%dd' % k] = s.min(axis=0)
    run = np.maximum.accumulate(cs, axis=0)
    out['max_drawdown'] = (cs - run).min(axis=0)
    return out


W1 = worst_and_dd(N8)
W2 = worst_and_dd(N8 - N8[:, [iR1]])
W3 = worst_and_dd(N8 - N8[:, [iR2]])
DD = pd.DataFrame(dict(config_id=cols,
                       **{('main_' + k): v for k, v in W1.items()},
                       **{('vsR1_' + k): v for k, v in W2.items()},
                       **{('vsR2_' + k): v for k, v in W3.items()}))
DD.to_csv(os.path.join(OUT, 'B_yearly', 'worst_windows_drawdown.csv'), index=False)
P('  写出 worst_windows_drawdown.csv (单位: 累计小数超额, 未年化)')

# ---------------- 静态 ledger_portability ----------------
P('')
P('=== 静态 ledger_portability (6 切点) ===')
SPLITS = ['2012-12-31', '2014-12-31', '2016-12-31', '2018-12-31', '2020-12-31', '2022-12-31']
rows = []
for sd in SPLITS:
    ts = pd.Timestamp(sd)
    tr = (DT <= ts)
    ev = (DT > ts)
    if tr.sum() < 60 or ev.sum() < 60:
        continue
    a = blockstats(tr, 'train_' + sd,
                   dict(kind='portability_train', split=sd,
                        short_training=(sd == '2012-12-31')))
    b = blockstats(ev, 'eval_' + sd,
                   dict(kind='portability_eval', split=sd,
                        short_training=(sd == '2012-12-31')))
    rows += [a, b]
SB = to_frame(rows)
SB['note'] = '静态截取: 评估段含分割前已生成的持仓 (不是可执行政策账户)'
SB.to_csv(os.path.join(OUT, 'B_split', 'ledger_portability_static.csv'), index=False)
piv = SB.pivot_table(index='config_id', columns=['kind', 'split'], values='net8')
P('  写出 ledger_portability_static.csv %d 行 (6 切点 × 训练/评估)' % len(SB))

# a / b / b-a 读法表
ab = []
for sd in SPLITS:
    tr = SB[(SB.kind == 'portability_train') & (SB.split == sd)].set_index('config_id')
    ev = SB[(SB.kind == 'portability_eval') & (SB.split == sd)].set_index('config_id')
    if not len(tr) or not len(ev):
        continue
    idx = tr.index.intersection(ev.index)
    for refnm in ('R1', 'R2'):
        a_ = tr.loc[idx, 'd_vs_' + refnm].values
        b_ = ev.loc[idx, 'd_vs_' + refnm].values
        se_ = ev.loc[idx, 'se_vs_' + refnm].values
        with np.errstate(invalid='ignore', divide='ignore'):
            ratio = np.where(np.abs(a_) > 1e-9, b_ / a_, np.nan)
        ab.append(pd.DataFrame(dict(
            config_id=idx, split=sd, ref=refnm, a_train=a_, b_eval=b_, b_minus_a=b_ - a_,
            se_eval=se_, b_over_a=ratio,
            unstable_ratio=(np.abs(a_) < 0.5) | (a_ <= 0),
            train_days=tr.loc[idx, 'n_days'].values, eval_days=ev.loc[idx, 'n_days'].values,
            short_training=(sd == '2012-12-31'))))
AB = pd.concat(ab, ignore_index=True)
AB.to_csv(os.path.join(OUT, 'B_split', 'ab_readout_static.csv'), index=False)
P('  写出 ab_readout_static.csv %d 行; 其中 a 不稳定(|a|<0.5 或 a≤0) 占 %.1f%%'
  % (len(AB), 100.0 * AB.unstable_ratio.mean()))
P('  注: 六切点互相重叠, 不当 12 次独立试验 (§13); b/a 只作带符号描述')

# ---------------- 旧 8 配置锚 ----------------
watch = [R1, R2, 'KT_dep(50,50)', 'KT_mean@30', 'KT_mean@50', 'T@25', 'K@50', 'C@30']
wa = YB[(YB.kind == 'year') & (YB.config_id.isin(watch))][['config_id', 'year', 'net8']]
wa.to_csv(os.path.join(OUT, 'B_yearly', 'watch8_yearly.csv'), index=False)
chk('旧 8 配置有 %d 个在账本里' % len(set(wa.config_id)), len(set(wa.config_id)) >= 6,
    str(sorted(set(watch) - set(wa.config_id))))

# ---------------- 摘要 ----------------
P('')
P('=== 摘要 (只读账本, 无采纳含义) ===')
fu = YB[YB.kind == 'full'].set_index('config_id')
P('  全窗口 net8: R1 %+.3f  R2 %+.3f;  U0-broad 中位 %+.3f  P90 %+.3f  最大 %+.3f'
  % (fu.loc[R1, 'net8'], fu.loc[R2, 'net8'], fu.net8.median(),
     fu.net8.quantile(0.9), fu.net8.max()))
P('  对 R1 的全窗口配对差 > 0 的配置占 %.1f%%; |t|>2 的占 %.1f%%'
  % (100.0 * (fu.d_vs_R1 > 0).mean(), 100.0 * (fu.t_vs_R1.abs() > 2).mean()))
yy = YB[(YB.kind == 'year') & (~YB.partial_year)]
pos_years = yy.assign(p=yy.net8 > 0).groupby('config_id').p.sum()
P('  完整年 %d 个; 正年数中位 %d, R1 %d, R2 %d'
  % (len(years) - 1, int(pos_years.median()), int(pos_years.get(R1, -1)), int(pos_years.get(R2, -1))))
c15 = CC[CC.year.isin([2015, 2016])].groupby('config_id').share_signed.sum()
P('  2015+2016 带符号贡献份额: 中位 %.2f, R1 %.2f, R2 %.2f (分母非正者已标 NA)'
  % (c15.median(), c15.get(R1, np.nan), c15.get(R2, np.nan)))

json.dump(dict(stage='B1', when=time.strftime('%Y-%m-%d %H:%M:%S'), n_configs=Nc,
               n_days=Tn, n_valid_days=int(V.sum()), years=[int(y) for y in years],
               splits=SPLITS, notes=NOTE, seconds=time.time() - T0),
          open(os.path.join(OUT, 'checks', 'b1_manifest.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'logs', 'b1.log'), 'w', encoding='utf-8').write('\n'.join(LOG) + '\n')
P('')
P('B1 完成 %.0fs; 待查 %d 项' % (time.time() - T0, len(NOTE)))
