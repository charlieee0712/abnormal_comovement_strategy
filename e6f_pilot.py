#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 试点: 等价性阻断验收 + 计时 (§10 计时要求)。最短段先跑, 再跑最长段。"""
import os, sys, time, json, argparse
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K
import e6f_core as F

ap = argparse.ArgumentParser()
ap.add_argument('--period', default='2024-2026')
ap.add_argument('--out', default='/mnt/sda2/lichenchen/results/_e6f_pilot')
A = ap.parse_args()
os.makedirs(A.out, exist_ok=True)
L = []
FAIL = []


def P(s=''):
    print(s, flush=True); L.append(s)


def chk(name, cond, detail=''):
    P('  %-46s %s %s' % (name, 'OK  ' if cond else 'FAIL', detail))
    if not cond:
        FAIL.append(name)


t0 = time.time()
P('=== E6f 试点 [%s] ===' % A.period)
P('源数据日期范围 %s  冻结末日 %s' % (str(F.source_last_date()), F.FROZEN_END))

# ---------- 0. E7 守卫 ----------
P('')
P('=== 0. E7 守卫 ===')
try:
    F.guarded_load('20240101', '20260909')
    chk('end_date=20260909 应被拒', False, '没抛错!')
except RuntimeError as e:
    chk('end_date=20260909 被拒', 'E7 GUARD' in str(e), str(e)[:60])
try:
    F.guarded_load('20240101', '20260328')
    chk('end_date=20260328 应被拒', False, '没抛错!')
except RuntimeError:
    chk('end_date=20260328 (冻结末日+1) 被拒', True)

# ---------- 1. qcut_group vs pandas ----------
P('')
P('=== 1. qcut_group 对 pandas 逐 (n,g) ===')
bad = []
for g in (2, 4, 5, 10, 15, 20, 25):
    for n in list(range(3 * g, 3 * g + 40)) + [200, 371, 500, 733, 1000, 1497]:
        if n < 3 * g:
            continue
        r = pd.Series(np.arange(1, n + 1, dtype=float))
        ref = pd.qcut(r.rank(method='first'), g, labels=range(1, g + 1)).astype(int).values
        got = F.qcut_group(n, g)
        if not np.array_equal(ref, got):
            bad.append((n, g, int((ref != got).sum())))
chk('qcut_group == pd.qcut (7 个 g × ~46 个 n)', not bad, str(bad[:3]))

# ---------- 2. 段上下文 ----------
P('')
P('=== 2. 段上下文 ===')
t1 = time.time()
S = F.build_segment(A.period, 'legacy_all')
t_pipe = time.time() - t1
P('  pipeline %.0fs' % t_pipe)
Sref = K.load_segment(A.period, verbose=False)
chk('pool0 与 e6e load_segment 一致', np.array_equal(S.p0, Sref.p0))
chk('ccols 一致', np.array_equal(S.ccols, Sref.ccols))
chk('bench 一致', np.allclose(S.bench, Sref.bench, equal_nan=True))
chk('r0 一致', np.allclose(S.r0, Sref.r0))
chk('icodes 一致', np.array_equal(S.icodes, Sref.icodes))
chk('cap 一致', np.allclose(S.cap, Sref.cap))
chk('基准全 NaN 日 = 19', int(np.isnan(S.bench).sum()) == 19,
    'got %d' % int(np.isnan(S.bench).sum()))

# ---------- 3. 默认因子锚 ----------
P('')
P('=== 3. 默认因子锚 (库值逐项复现) ===')
for sp, libname, how in F.DEFAULT_ANCHORS:
    if libname in S.feats:
        ref = S.feats[libname]
    elif libname == 'intraday_cvr_1d':
        ref = S.data['close'] / S.data['vwap'] - 1
    else:
        chk('%-14s vs %s' % (F.fid(sp), libname), False, '库里没有')
        continue
    got = F.build_raw(S.data, sp).reindex(index=ref.index, columns=ref.columns)
    a, b = got.values, ref.values
    same_nan = np.array_equal(np.isnan(a), np.isnan(b))
    m = ~np.isnan(a) & ~np.isnan(b)
    d = float(np.nanmax(np.abs(a[m] - b[m]))) if m.any() else 0.0
    if how == 'exact':
        chk('%-14s vs %-22s 逐位' % (F.fid(sp), libname), same_nan and d == 0.0,
            'NaN模式%s max|d|=%.3e' % ('同' if same_nan else '异', d))
    else:
        chk('%-14s vs %-22s allclose' % (F.fid(sp), libname), same_nan and d < 1e-12,
            'NaN模式%s max|d|=%.3e' % ('同' if same_nan else '异', d))

# ---------- 4. 稠密掩码 == e6e 路径 ----------
P('')
P('=== 4. 稠密掩码路径 == e6e ===')
t1 = time.time()
PT = F.get_pct(S, F.spec('T', 60), 'NS')
PC = F.get_pct(S, F.spec('C', 20), 'NS')
PK = F.get_pct(S, F.spec('K', 1, est='MA'), 'NS')
t_pct = time.time() - t1
P('  3 个 pct 表 %.1fs' % t_pct)
# pct 表逐值比对 (用 e6e opct 的 Series 直接查)
for nm, sp, f6 in (('T60', F.spec('T', 60), K.FT), ('C20', F.spec('C', 20), K.FC),
                   ('KMA1', F.spec('K', 1, est='MA'), K.FK)):
    Pd = F.get_pct(S, sp, 'NS')
    worst = 0.0
    nchk = 0
    for i in range(0, S.T, 37):
        s = Sref.opct[f6].get(S.dates[i])
        if s is None:
            continue
        pos = np.fromiter((S.ccolpos.get(x, -1) for x in np.asarray(s.index)), int, len(s))
        v = pos >= 0
        got = Pd[i, pos[v]]
        ref = s.values[v]
        mm = ~np.isnan(got) & ~np.isnan(ref)
        if mm.any():
            worst = max(worst, float(np.max(np.abs(got[mm] - ref[mm]))))
        nchk += int(mm.sum())
    chk('pct 表 %-6s == e6e opct (%d 值)' % (nm, nchk), worst == 0.0, 'max|d|=%.3e' % worst)

for pctkeep in (20, 25, 30, 50):
    m_new = F.keep_mask_dense(PT, S.p0c, pctkeep)
    m_ref = K.toc(Sref, K.keep_pct_mask(Sref.opct[K.FT], Sref.pool0, pctkeep))
    chk('keep_mask_dense T@%d == e6e' % pctkeep, np.array_equal(m_new, m_ref),
        '差 %d 格' % int((m_new != m_ref).sum()))
for k in (5, 10, 15, 20):
    d_new = F.drop_mask_dense(PC, S.p0c, k)
    d_ref = K.toc(Sref, K.drop_or(Sref.neu[K.FC], Sref.pool0, k, K.HB[K.FC]))
    chk('drop_mask_dense C:k%d == e6e' % k, np.array_equal(d_new, d_ref),
        '差 %d 格' % int((d_new != d_ref).sum()))

# 合成核
Pm = F.combine_dense([PK, PT, PC], 'mean', complete=True)
m_new = F.keep_mask_dense(Pm, S.p0c, 25)
sc_ref = K.combine([Sref.opct[K.FK], Sref.opct[K.FT], Sref.opct[K.FC]], 'mean', complete=True)
m_ref = K.toc(Sref, K.keep_pct_mask(sc_ref, Sref.pool0, 25))
chk('KTC_mean@25 掩码 == e6e', np.array_equal(m_new, m_ref), '差 %d 格' % int((m_new != m_ref).sum()))

# ---------- 5. 引擎 ----------
P('')
P('=== 5. 引擎 ===')
t1 = time.time()
(g1, p1, u1, n1), (idx, val) = F.eval_dense(S, m_new, H=5)
t_eng = time.time() - t1
g0, p0_, u0, n0 = K.eval_mask(Sref, m_ref)
chk('sparse_pnl_H(H=5) == e6e sparse_pnl',
    np.allclose(g1, g0, atol=1e-15, equal_nan=True) and np.allclose(u1, u0, atol=1e-15)
    and np.allclose(p1, p0_, atol=1e-15),
    'max|dg|=%.3e' % float(np.nanmax(np.abs(g1 - g0))))
gr, pr, ur, nr = K.reference_pnl(Sref, m_ref)
mm = ~np.isnan(g1) & ~np.isnan(gr)
chk('sparse == 稠密参照引擎 (compute_calendar_pnl)',
    float(np.max(np.abs(g1[mm] - gr[mm]))) < 1e-12 and float(np.max(np.abs(u1 - ur))) < 1e-12,
    'max|dg|=%.3e max|dturn|=%.3e' % (float(np.max(np.abs(g1[mm] - gr[mm]))),
                                      float(np.max(np.abs(u1 - ur)))))
dd = float(np.nanmax(np.abs((g1 - u1 * 12e-4) - (g1 - u1 * 8e-4) + u1 * 4e-4)))
chk('net12 - net8 == -turn*4bp', dd < 1e-15, 'max|d|=%.3e (抵消式, 容差 1e-15)' % dd)

# ---------- 6. 对 E6e 账本锚 ----------
P('')
P('=== 6. 对 E6e 日账本 (A12 锚) ===')
GG = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_gross_%s.parquet' % A.period))
TT = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_turn_%s.parquet' % A.period))
PPz = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_pos_%s.parquet' % A.period))
if 'KTC_mean@25' in GG.columns:
    ref_g = GG['KTC_mean@25'].values
    ref_t = TT['KTC_mean@25'].values
    ref_p = PPz['KTC_mean@25'].values
    mm = ~np.isnan(g1) & ~np.isnan(ref_g)
    dg = float(np.max(np.abs(g1[mm] - ref_g[mm])))
    chk('KTC_mean@25 日 gross 对账本 atol 1e-12', dg < 1e-12, 'max|d|=%.3e' % dg)
    chk('KTC_mean@25 日 turn 对账本', float(np.max(np.abs(u1 - ref_t))) < 1e-12,
        'max|d|=%.3e' % float(np.max(np.abs(u1 - ref_t))))
    chk('KTC_mean@25 日 pos 对账本', float(np.max(np.abs(p1 - ref_p))) < 1e-12,
        'max|d|=%.3e' % float(np.max(np.abs(p1 - ref_p))))
    P('  年化 net8 = %+.4f (账本 %+.4f)'
      % (F.ann(g1 - u1 * 8e-4), F.ann(ref_g - ref_t * 8e-4)))

# ---------- 7. NSI: svd vs fwl ----------
P('')
P('=== 7. 中性化 ===')
rng = np.random.default_rng(7)
worst = 0.0
for _ in range(200):
    n = int(rng.integers(15, 400))
    G = int(rng.integers(2, 32))
    ic = rng.integers(0, G, n)
    ic = pd.factorize(ic)[0]
    y = rng.normal(size=n)
    m = rng.normal(size=n) + ic * 0.3
    a, ra, _ = F._resid_nsi(y, m, ic, 'svd')
    b, rb, _ = F._resid_nsi(y, m, ic, 'fwl')
    worst = max(worst, float(np.max(np.abs(a - b))))
chk('NSI: SVD == FWL (200 随机截面)', worst < 1e-9, 'max|d|=%.3e' % worst)
# FWL 反例: 只去 y 的行业均值再对原始 m 回归, 必须不同
y = rng.normal(size=300); m = rng.normal(size=300) + 1.0
ic = pd.factorize(rng.integers(0, 8, 300))[0]
good, _, _ = F._resid_nsi(y, m, ic, 'fwl')
yt, _ = F._resid_ni(y, ic)
wrong = yt - (float(m @ yt) / float(m @ m)) * m
chk('FWL 反例 (只去 y 均值) 确实不同', float(np.max(np.abs(good - wrong))) > 1e-6,
    'max|d|=%.3e' % float(np.max(np.abs(good - wrong))))
for mode in ('N0', 'NI', 'NSI'):
    t1 = time.time()
    Pn = F.get_pct(S, F.spec('T', 60), mode)
    inf = F.get_info(S, F.spec('T', 60), mode)
    P('  T60/%-4s %5.1fs  有值日 %d  回退NS %d  size退化 %d  最小自由度 %s'
      % (mode, time.time() - t1, inf['days'], inf['fallback_ns'],
         inf['degenerate_size'], inf['dof_min']))

# ---------- 8. 计时: 单配置 ----------
P('')
P('=== 8. 计时 ===')
t1 = time.time()
NB = 20
for i in range(NB):
    mk = F.keep_mask_dense(Pm, S.p0c, 25 + (i % 4) * 5)
    F.eval_dense(S, mk, H=5)
t_cfg = (time.time() - t1) / NB
P('  单配置 (掩码+DEV+引擎) %.3fs  -> 1000 配置 %.0fs' % (t_cfg, t_cfg * 1000))
t1 = time.time()
newP = F.get_pct(S, F.spec('T', 120), 'NS')
P('  新因子 T120 (重建+中性化+pct) %.1fs' % (time.time() - t1))
t1 = time.time()
tn = m_new.sum(axis=1)
tm = F.coretrim_matchN(S, Pm, F.keep_mask_dense(Pm, S.p0c, 30), tn)
P('  coretrim_matchN %.2fs' % (time.time() - t1))

P('')
P('T=%d Nc=%d  试点总耗时 %.0fs' % (S.T, S.Nc, time.time() - t0))
P('FAIL: %s' % (FAIL if FAIL else '无'))
json.dump(dict(period=A.period, T=S.T, Nc=S.Nc, t_pipeline=t_pipe, t_cfg=t_cfg,
               fails=FAIL), open(os.path.join(A.out, 'pilot_%s.json' % A.period), 'w'), indent=1)
open(os.path.join(A.out, 'pilot_%s.txt' % A.period), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
sys.exit(1 if FAIL else 0)
