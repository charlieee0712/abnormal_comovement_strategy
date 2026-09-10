#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 块 D: 统计补全与统一读表 (§7)。主表不设任何闸。
   用法: python e6f_d.py --out DIR [--B 2000]
"""
import os, sys, json, time, argparse, collections
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K
import e6f_core as F
import e6f_desc as D

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--B', type=int, default=2000)
ap.add_argument('--seed', type=int, default=20260911)
A = ap.parse_args()
for d in ('D_hac', 'D_bootstrap', 'D_analytic_random', 'checks', 'logs'):
    os.makedirs(os.path.join(A.out, d), exist_ok=True)
_lf = open(os.path.join(A.out, 'logs', 'blockD.log'), 'w', encoding='utf-8', buffering=1)


def P(s=''):
    print(s, flush=True); _lf.write(s + '\n')


T0 = time.time()
R1, R2 = 'KT_dep(50,50)|C:k5', 'KT_mean@30|C:k5+cr5:k10'
P('=== 块 D === %s' % time.strftime('%Y-%m-%d %H:%M:%S'))

# ============================================================
# 载入: U0-broad + UA(H5)
# ============================================================
G, T_, mark = [], [], []
for s in F.SEGS:
    G.append(pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_gross_%s.parquet' % s)))
    T_.append(pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_turn_%s.parquet' % s)))
    mark.append(np.array([s] * len(G[-1].index)))
u0 = sorted(set(pd.read_csv(os.path.join(A.out, 'domain_U0.csv')).config_id)
            & set.intersection(*[set(x.columns) for x in G]))
GG = pd.concat([x.reindex(columns=u0) for x in G], axis=0)
TT = pd.concat([x.reindex(columns=u0) for x in T_], axis=0)
seg = np.concatenate(mark)
UAOK = all(os.path.exists(os.path.join(A.out, 'daily', 'A_gross_%s__legacy_all.parquet' % s))
           for s in F.SEGS)
PAR = {}
if UAOK:
    cf = [c for c in D.gen_all() if c['H'] == 5]
    PAR = {'UA::' + c['config_id']: c['parent_id'] for c in cf}
    LAYER = {'UA::' + c['config_id']: c['layer'] for c in cf}
    ug = [pd.read_parquet(os.path.join(A.out, 'daily', 'A_gross_%s__legacy_all.parquet' % s))
          for s in F.SEGS]
    ut = [pd.read_parquet(os.path.join(A.out, 'daily', 'A_turn_%s__legacy_all.parquet' % s))
          for s in F.SEGS]
    # KTC_mean@15 的 4 个配置由 e6f_fix15 补跑, 列在此并回
    for i_, s in enumerate(F.SEGS):
        for n_, tgt in (('gross', ug[i_]), ('turn', ut[i_])):
            fx = os.path.join(A.out, 'daily', 'A_%s_%s__legacy_all_fix15.parquet' % (n_, s))
            if os.path.exists(fx):
                add = pd.read_parquet(fx)
                assert list(add.index) == list(tgt.index), 'fix15 日期不齐 %s' % fx
                for c_ in add.columns:
                    tgt[c_] = add[c_].values
    ua = sorted(set(c['config_id'] for c in cf) & set.intersection(*[set(x.columns) for x in ug]))
    UG = pd.concat([x.reindex(columns=ua) for x in ug], axis=0)
    UT = pd.concat([x.reindex(columns=ua) for x in ut], axis=0)
    UG.columns = ['UA::' + c for c in ua]
    UT.columns = ['UA::' + c for c in ua]
    GG = pd.concat([GG, UG], axis=1); TT = pd.concat([TT, UT], axis=1)
    P('  UA 并入 %d 个' % len(ua))
else:
    LAYER = {}
    P('  !! 块 A 日账本未齐, F-A 族本次不出, 登记 deferred')

cols = list(GG.columns)
DT = pd.DatetimeIndex(GG.index)
N8 = GG.values - TT.values * (F.COST / 1e4)
N12 = GG.values - TT.values * (F.COST_HI / 1e4)
Tn, Nc = N8.shape
V = ~np.isnan(N8).any(axis=1)
ci = {c: i for i, c in enumerate(cols)}
P('  %d 配置 × %d 日 (有效 %d)' % (Nc, Tn, int(V.sum())))


def hac_mat(X, L=5, minn=10):
    o = ~np.isnan(X)
    n = o.sum(axis=0).astype(float)
    mu = np.where(n > 0, np.nansum(np.where(o, X, 0.0), axis=0) / np.maximum(n, 1), np.nan)
    E = np.where(o, X - mu, 0.0)
    S = (E * E).sum(axis=0)
    for l in range(1, L + 1):
        if l < X.shape[0]:
            S += 2.0 * (1 - l / (L + 1.0)) * (E[l:] * E[:-l]).sum(axis=0)
    se = np.where(S > 0, np.sqrt(S) / np.maximum(n, 1), np.nan)
    with np.errstate(invalid='ignore', divide='ignore'):
        t = np.where((se == se) & (se > 0) & (n >= minn), mu / se, np.nan)
    return mu * 252 * 100.0, t, n.astype(int), se


def hac_calendar_mat(X, L=5):
    """日历感知影响序列 z_t = I_t (x_t - mu)/mean(I), 在【原时钟】上做 HAC (§7 新增列)。"""
    o = (~np.isnan(X)).astype(float)
    n = o.sum(axis=0)
    mu = np.where(n > 0, np.nansum(np.where(o > 0, X, 0.0), axis=0) / np.maximum(n, 1), np.nan)
    Ibar = o.mean(axis=0)
    Z = o * (np.nan_to_num(X) - mu) / np.maximum(Ibar, 1e-12)
    S = (Z * Z).sum(axis=0)
    for l in range(1, L + 1):
        S += 2.0 * (1 - l / (L + 1.0)) * (Z[l:] * Z[:-l]).sum(axis=0)
    se = np.where(S > 0, np.sqrt(S) / X.shape[0], np.nan)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where((se == se) & (se > 0), mu / se, np.nan)


# ============================================================
# D1: HAC 表
# ============================================================
P('')
P('=== D1: HAC (L=5 主列; 20/60 敏感性; 日历感知附加列) ===')
rows = {}
for nm, X in (('net8', N8), ('net12', N12), ('gross', GG.values)):
    for L in (5, 20, 60):
        a, t, n, se = hac_mat(np.where(V[:, None], X, np.nan), L)
        rows['%s_ann' % nm] = a
        rows['%s_t_L%d' % (nm, L)] = t
        rows['%s_se_L%d' % (nm, L)] = se
    rows['%s_t_calendarL5' % nm] = hac_calendar_mat(np.where(V[:, None], X, np.nan), 5)
for refnm, i in (('R1', ci[R1]), ('R2', ci[R2])):
    Dm = np.where(V[:, None], N8 - N8[:, [i]], np.nan)
    for L in (5, 20, 60):
        a, t, n, se = hac_mat(Dm, L)
        rows['d_vs_%s' % refnm] = a
        rows['t_vs_%s_L%d' % (refnm, L)] = t
        rows['se_vs_%s_L%d' % (refnm, L)] = se
    rows['t_vs_%s_calendarL5' % refnm] = hac_calendar_mat(Dm, 5)
    Dm12 = np.where(V[:, None], N12 - N12[:, [i]], np.nan)
    a12, t12, _, _ = hac_mat(Dm12, 5)
    rows['d12_vs_%s' % refnm] = a12
    rows['t12_vs_%s_L5' % refnm] = t12
HAC = pd.DataFrame(rows, index=cols)
HAC['n_clock'] = Tn
HAC['n_valid'] = int(V.sum())
HAC['support_id'] = 'legacy_all'
HAC['zero_se'] = (HAC.filter(like='se_vs_R1_L5').iloc[:, 0].fillna(0) <= 0)
HAC.to_csv(os.path.join(A.out, 'D_hac', 'hac_table.csv'))
P('  写出 hac_table.csv %d 行 × %d 列' % HAC.shape)
for L in (5, 20, 60):
    P('  |t vs R1| > 2 占比 (L=%d): %.1f%%' % (L, 100 * (HAC['t_vs_R1_L%d' % L].abs() > 2).mean()))
P('  日历感知 t vs 原 t 的中位比值: %.3f'
  % float((HAC.t_vs_R1_calendarL5 / HAC.t_vs_R1_L5).median()))

# ============================================================
# D2: bootstrap 族
# ============================================================
P('')
P('=== D2: stationary bootstrap (块长 20 / 60, B=%d, 段内重采样段长固定) ===' % A.B)
rng = np.random.default_rng(A.seed)


def seg_cnt(mean_block, B):
    """段内重采样、段长固定: 逐段各自建计数矩阵再纵向拼接。"""
    parts = []
    for s in F.SEGS:
        m = (seg == s)
        parts.append(F.stationary_blocks(rng, int(m.sum()), mean_block, B))
    return np.vstack(parts).astype(np.float64)


FAMS = collections.OrderedDict()
FAMS['F-R_vs_R1_8bp'] = [(c, N8[:, ci[c]] - N8[:, ci[R1]]) for c in cols if c != R1]
FAMS['F-R_vs_R2_8bp'] = [(c, N8[:, ci[c]] - N8[:, ci[R2]]) for c in cols if c != R2]
FAMS['F-R_vs_R1_12bp'] = [(c, N12[:, ci[c]] - N12[:, ci[R1]]) for c in cols if c != R1]
if UAOK:
    fa = []
    for c in cols:
        if not c.startswith('UA::'):
            continue
        p = PAR.get(c)
        pc = 'UA::' + p if ('UA::' + p) in ci else (p if p in ci else None)
        if pc is None or pc == c:
            continue
        fa.append((c, N8[:, ci[c]] - N8[:, ci[pc]]))
    FAMS['F-A_all'] = fa
    sub = collections.defaultdict(list)
    for c, d in fa:
        sub['F-A_' + LAYER.get(c, 'other')].append((c, d))
    for k_, v in sub.items():
        if len(v) >= 5:
            FAMS[k_] = v
# ---- F-C: 冲击成本情景族 (C1 的日冲击成本; 每个 (A,κ) 情景 × 每个配置一条) ----
#      C1 存的是【每日括号】bracket_<段>.npy (T×n) + bracket_cols_<段>.json:
#      c_e(A,κ) = κ·√(A·1e8) · bracket_e。情景只是标量倍, 所以在这里现算不重跑 C1。
YI_ = 1e8
nfc = 0
imp_dir = os.path.join(A.out, 'C_impact')
brp = [os.path.join(imp_dir, 'bracket_%s.npy' % s) for s in F.SEGS]
brc = [os.path.join(imp_dir, 'bracket_cols_%s.json' % s) for s in F.SEGS]
if all(os.path.exists(p) for p in brp + brc):
    try:
        bc = [json.load(open(p, encoding='utf-8')) for p in brc]
        common = sorted(set.intersection(*[set(x) for x in bc]))
        parts = []
        for i_, s in enumerate(F.SEGS):
            M_ = np.load(brp[i_])
            pos_ = {c_: j for j, c_ in enumerate(bc[i_])}
            parts.append(M_[:, [pos_[c_] for c_ in common]])
        BRC = np.vstack(parts)
        assert BRC.shape[0] == len(DT), '括号行数 %d ≠ 账本日数 %d' % (BRC.shape[0], len(DT))
        bj = {c_: j for j, c_ in enumerate(common)}
        for (Acap, kap) in ((1.0, 0.5), (5.0, 0.5), (10.0, 0.5), (5.0, 1.0)):
            mult = kap * np.sqrt(Acap * YI_)
            r2b = mult * BRC[:, bj[R2]] if R2 in bj else 0.0
            mem = []
            for c_ in common:
                key = c_ if c_ in ci else ('UA::' + c_ if 'UA::' + c_ in ci else None)
                if key is None or c_ == R2:
                    continue
                mem.append((c_, (N8[:, ci[key]] - mult * BRC[:, bj[c_]])
                            - (N8[:, ci[R2]] - r2b)))
            if len(mem) >= 5:
                FAMS['F-C_A%gyi_k%g_vs_R2' % (Acap, kap)] = mem
                nfc += 1
        P('  F-C: %d 个情景族 × %d 成员 (括号 %d 列)' % (nfc, len(mem), len(common)))
    except Exception as e_:
        P('  !! F-C 组装失败 (%s), 登记 deferred' % e_)
if not nfc:
    P('  F-C: C1 每日括号尚未落盘, 本轮不出, 登记 deferred')

# ---- F-B: 政策账户族 (B2 的政策账户对 R1/R2 同日配对差) ----
nfb = 0
pol = [os.path.join(A.out, 'B_walkforward', 'policy_gross_%s.parquet' % s) for s in F.SEGS]
polt = [os.path.join(A.out, 'B_walkforward', 'policy_turn_%s.parquet' % s) for s in F.SEGS]
if all(os.path.exists(p) for p in pol + polt):
    try:
        PG_ = pd.concat([pd.read_parquet(p) for p in pol], axis=0)
        PT_ = pd.concat([pd.read_parquet(p) for p in polt], axis=0)
        assert list(PG_.index) == list(DT), '政策账户日期与账本不齐'
        PN8_ = PG_.values - PT_.values * (F.COST / 1e4)
        pc_ = {c_: i for i, c_ in enumerate(PG_.columns)}
        for lbl, rr in (('R1', R1), ('R2', R2)):
            if 'REF::' + rr not in pc_:
                continue
            mem = [(c_, PN8_[:, pc_[c_]] - PN8_[:, pc_['REF::' + rr]])
                   for c_ in PG_.columns if not c_.startswith('REF::')]
            if len(mem) >= 5:
                FAMS['F-B_policy_vs_' + lbl] = mem
                nfb += 1
    except Exception as e_:
        P('  !! F-B 组装失败 (%s), 登记 deferred' % e_)
if not nfb:
    P('  F-B: B2 政策账户日序列尚未落盘, 本轮不出, 登记 deferred')

e6f = {}
brows = []
for fam, members in FAMS.items():
    if not members:
        continue
    Xd = np.column_stack([d for _, d in members])
    Xd = np.where(V[:, None], Xd, np.nan)
    mu, t5, n, se = hac_mat(Xd, 5)
    Xf = np.nan_to_num(Xd, nan=0.0)
    for mb in (20, 60):
        CNT = seg_cnt(mb, A.B)
        DEN = CNT.sum(axis=0)
        BM = (Xf.T @ CNT) / DEN * 252 * 100.0                     # (m, B) 共 draw
        lo = np.percentile(BM, 2.5, axis=1)
        hi = np.percentile(BM, 97.5, axis=1)
        sd = BM.std(axis=1, ddof=1)
        # sd 是 (m,), BM 是 (m,B): np.where 的条件按【最后一个轴】对齐, 必须先补上列轴,
        # 否则 (m,) 会去对 B 广播。除法也要先把 0 换掉, 不能靠 errstate 掩盖。
        sdc = sd[:, None]
        with np.errstate(invalid='ignore', divide='ignore'):
            tb = np.where(sdc > 0, (BM - mu[:, None]) / np.where(sdc > 0, sdc, 1.0), np.nan)
        crit = float(np.nanpercentile(np.nanmax(np.abs(tb), axis=0), 95))
        for j, (c, _) in enumerate(members):
            brows.append(dict(family=fam, config_id=c, mean_block=mb, B=A.B,
                              point=mu[j], hac_t_L5=t5[j], hac_se_L5=se[j] * 252 * 100.0,
                              boot_lo=lo[j], boot_hi=hi[j], boot_sd=sd[j],
                              simult_crit=crit,
                              simult_lo=mu[j] - crit * sd[j], simult_hi=mu[j] + crit * sd[j],
                              zero_se=bool(not (se[j] > 0)), n_valid=int(n[j])))
    P('  %-22s m=%-5d 逐点 95%% 区间不含 0 占 %.1f%%; 同时带(块长20)不含 0 占 %.1f%%'
      % (fam, len(members),
         100 * np.mean([(r['boot_lo'] > 0) or (r['boot_hi'] < 0)
                        for r in brows if r['family'] == fam and r['mean_block'] == 20]),
         100 * np.mean([(r['simult_lo'] > 0) or (r['simult_hi'] < 0)
                        for r in brows if r['family'] == fam and r['mean_block'] == 20])))
BS = pd.DataFrame(brows)
BS.to_csv(os.path.join(A.out, 'D_bootstrap', 'bootstrap_families.csv'), index=False)
P('  写出 bootstrap_families.csv %d 行' % len(BS))

# F-source: E6e F1/F2/F4 复算 (若原族定义可读)
try:
    af = json.load(open(os.path.join(F.E6E_DIR, 'analysis_families.json'), encoding='utf-8'))
    json.dump({'F-source_note': 'E6e F1/F2/F4 成员定义已读入; 本轮以同一日账本复算 L20/60 与块长 20',
               'keys': list(af.keys())},
              open(os.path.join(A.out, 'D_bootstrap', 'F_source_note.json'), 'w',
                   encoding='utf-8'), ensure_ascii=False, indent=1)
    P('  F-source: 读到 E6e analysis_families.json, 键 %s' % list(af.keys()))
except Exception as e:
    P('  F-source: 读不到 E6e 族定义 (%s), 登记 deferred' % e)

# ============================================================
# D3: I-IID 解析 gross 旁证 (小宇宙全枚举 = 确定性测试)
# ============================================================
P('')
P('=== D3: I-IID 解析期望权重 (小宇宙全子集枚举) ===')
import itertools


def dev_weights(sel, ind, G, cap):
    n = len(sel)
    if n == 0:
        return np.zeros(0)
    w = np.full(n, min(1.0 / n, K.MAX_STOCK))
    ic = ind[sel]
    gs = np.bincount(ic, weights=w, minlength=G)
    over = gs > cap
    if over.any():
        sc = np.ones(G)
        np.divide(cap, gs, out=sc, where=over)
        sc[~over] = 1.0
        w = w * sc[ic]
    return w


ok = True
rows3 = []
rngd = np.random.default_rng(3)
for trial in range(6):
    n_tot = int(rngd.integers(6, 11))
    G_ = int(rngd.integers(2, 4))
    ind = rngd.integers(0, G_, n_tot)
    cap = np.array([float(np.mean(ind == g)) + K.MAX_IND_DEV for g in range(G_)])
    m = int(rngd.integers(2, n_tot))
    subs = list(itertools.combinations(range(n_tot), m))
    Ew = np.zeros(n_tot)
    for sub in subs:
        w = dev_weights(np.array(sub), ind, G_, cap)
        Ew[list(sub)] += w
    Ew /= len(subs)
    # 解析: E[w_i] = (m_h/n_h)·u·min(1, cap_h/(m_h·u)) 只在"每行业保留数固定"时成立;
    # 均匀无放回抽 m 只时 m_h 是随机的 -> 对 m_h 取期望后再比。这里按 §7 的固定 m_h 版本枚举验证。
    Ean = np.zeros(n_tot)
    cnt = collections.Counter()
    for sub in subs:
        mh = np.bincount(ind[list(sub)], minlength=G_)
        cnt[tuple(mh)] += 1
    for mh, c in cnt.items():
        mh = np.array(mh)
        u = min(1.0 / m, K.MAX_STOCK)
        with np.errstate(invalid='ignore', divide='ignore'):
            shrink = np.minimum(1.0, np.where(mh > 0, cap / np.maximum(mh * u, 1e-30), 1.0))
        nh = np.bincount(ind, minlength=G_)
        for i in range(n_tot):
            h = ind[i]
            if nh[h] == 0:
                continue
            Ean[i] += c * (mh[h] / nh[h]) * u * shrink[h]
    Ean /= len(subs)
    d = float(np.max(np.abs(Ew - Ean)))
    rows3.append(dict(trial=trial, n=n_tot, G=G_, m=m, n_subsets=len(subs), max_abs_diff=d,
                      ok=bool(d < 1e-12)))
    ok = ok and d < 1e-12
pd.DataFrame(rows3).to_csv(os.path.join(A.out, 'D_analytic_random', 'small_universe_enum.csv'),
                           index=False)
P('  小宇宙全枚举 6 组: max|E[w] 枚举 - 解析| = %.3e  %s'
  % (max(r['max_abs_diff'] for r in rows3), 'OK' if ok else 'FAIL'))
P('  (解析式 E[w_i] = (m_h/n_h)·u·min(1, cap_h/(m_h·u)), 对 m_h 的分布取期望)')

json.dump(dict(stage='D', when=time.strftime('%Y-%m-%d %H:%M:%S'), n_configs=Nc,
               B=A.B, mean_blocks=[20, 60], hac_L=[5, 20, 60], ua_included=bool(UAOK),
               analytic_ok=bool(ok), seconds=time.time() - T0,
               deferred=['RW 调整 p 值 (未验证实现, 按 §7 只作可选附列 -> 不出)']),
          open(os.path.join(A.out, 'checks', 'blockD.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
P('')
P('块 D 完成 %.0fs' % (time.time() - T0))
_lf.close()
