#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 块 B2 第一步: 选择程序回放 (§5.2)。只用训练日账本, 不看评估段。
   出 selected_sets.csv (域×规则×切点×方向×vintage -> 选中 ID 与权重) 与选择稳定性重采样。
   用法: python e6f_b2_select.py --out DIR [--B 2000]
"""
import os, sys, json, time, argparse, itertools, collections, warnings
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K
import e6f_core as F
import e6f_desc as D

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--B', type=int, default=2000)
ap.add_argument('--seed', type=int, default=20260910)
ap.add_argument('--skip_stability', action='store_true',
                help='跳过第 6 节重采样 (C1 落盘后为了补 S-cost 重跑时用, 稳定性沿用首轮)')
A = ap.parse_args()
for d in ('B_nested', 'B_selection_stability', 'B_walkforward', 'checks', 'logs'):
    os.makedirs(os.path.join(A.out, d), exist_ok=True)
_lf = open(os.path.join(A.out, 'logs', 'b2_select.log'), 'w', encoding='utf-8', buffering=1)


def P(s=''):
    print(s, flush=True); _lf.write(s + '\n')


T0 = time.time()
R1, R2 = 'KT_dep(50,50)|C:k5', 'KT_mean@30|C:k5+cr5:k10'
SPLITS = ['2012-12-31', '2014-12-31', '2016-12-31', '2018-12-31', '2020-12-31', '2022-12-31']
RULES = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']
GAP = 120 + K.HOLD + K.EXEC_LAG + 5      # max_feature_dependency + H + exec_lag + obs_window
P('=== B2 选择回放 === %s  反向保护区 %d 个交易日' % (time.strftime('%Y-%m-%d %H:%M:%S'), GAP))

# ============================================================
# 1. 账本: U0-broad (E6e) + UA(H5) (块 A legacy_all)
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

UAg, UAt, ua_cols = [], [], None
ok_ua = True
for s in F.SEGS:
    p = os.path.join(A.out, 'daily', 'A_gross_%s__legacy_all.parquet' % s)
    if not os.path.exists(p):
        ok_ua = False
        break
    g = pd.read_parquet(p)
    t = pd.read_parquet(os.path.join(A.out, 'daily', 'A_turn_%s__legacy_all.parquet' % s))
    # KTC_mean@15 那 4 个配置在主轮以 KeyError:15 失败, 由 e6f_fix15 补跑, 列在此并回
    for nm, tgt in (('gross', g), ('turn', t)):
        pf = os.path.join(A.out, 'daily', 'A_%s_%s__legacy_all_fix15.parquet' % (nm, s))
        if os.path.exists(pf):
            f = pd.read_parquet(pf)
            assert list(f.index) == list(tgt.index), 'fix15 日期与主轮不齐 %s' % pf
            for c in f.columns:
                tgt[c] = f[c].values
    UAg.append(g); UAt.append(t)
if ok_ua:
    prim = set(c['config_id'] for c in D.gen_all() if c['H'] == 5)
    ua_cols = sorted(prim & set.intersection(*[set(x.columns) for x in UAg]))
    UG = pd.concat([x.reindex(columns=ua_cols) for x in UAg], axis=0)
    UT = pd.concat([x.reindex(columns=ua_cols) for x in UAt], axis=0)
    assert list(UG.index) == list(GG.index), 'UA 与 E6e 账本日期不对齐'
    ua_cols = ['UA::' + c for c in ua_cols]
    UG.columns = ua_cols; UT.columns = ua_cols
    GG = pd.concat([GG, UG], axis=1)
    TT = pd.concat([TT, UT], axis=1)
    P('  UA 并入: %d 个 H5 配置' % len(ua_cols))
else:
    ua_cols = []
    P('  !! 块 A 日账本尚未齐备, 本次只跑 OLD/U0-primary/U0-broad 三域; EXPANDED 待块 A 完成后重跑')

cols = list(GG.columns)
DT = pd.DatetimeIndex(GG.index)
N8 = (GG.values - TT.values * (F.COST / 1e4))
TU = TT.values
V = ~np.isnan(N8).any(axis=1)
P('  账本 %d 配置 × %d 日 (有效 %d)' % (len(cols), len(DT), int(V.sum())))

# ============================================================
# 2. 域
# ============================================================
AC = pd.read_csv(os.path.join(F.E6E_DIR, 'summary', 'all_candidates.csv')).set_index('config_id')
kind = {c: (AC.loc[c, 'kind'] if c in AC.index else 'UA') for c in cols}
core_of = {c: (AC.loc[c, 'core'] if (c in AC.index and isinstance(AC.loc[c, 'core'], str))
               else c.split('|')[0].replace('UA::', '')) for c in cols}
fam_of = {}
for c in cols:
    k_ = core_of[c]
    fam_of[c] = k_.split('@')[0].split('(')[0].split('{')[0]
OLD = [c for c in cols if (not c.startswith('UA::')) and
       fam_of[c] in ('KT_dep', 'KT_mean') and kind[c] in ('core', 'hard')]
U0P = [c for c in cols if kind[c] in ('core', 'hard', 'composite', 'exempt')]
U0B = [c for c in cols if kind[c] in ('core', 'hard', 'composite', 'exempt', 'soft')]
EXP = U0B + [c for c in cols if c.startswith('UA::')]
DOMAINS = collections.OrderedDict([('OLD_structural', OLD), ('U0-primary', U0P),
                                   ('U0-broad', U0B)] + ([('EXPANDED', EXP)] if ua_cols else []))
for k_, v in DOMAINS.items():
    P('  域 %-14s %5d' % (k_, len(v)))
ci = {c: i for i, c in enumerate(cols)}

# ============================================================
# 3. 邻域图 (S6 用; §4.4 元数据预定义)
# ============================================================
def coord(c):
    """把 config_id 解析成有序坐标向量 (只用构造元数据, 不看收益)。"""
    base = c.replace('UA::', '')
    corepart = base.split('|')[0]
    vp = base.split('|')[1] if '|' in base else ''
    d = {}
    if '@' in corepart:
        try:
            d['depth'] = int(corepart.split('@')[1].split('{')[0])
        except ValueError:
            pass
    if '(' in corepart:
        try:
            a, b = corepart.split('(')[1].split(')')[0].split(',')
            d['a'] = int(a); d['b'] = int(b)
        except ValueError:
            pass
    for leg in [x for x in vp.split('+') if ':k' in x]:
        nm, kk = leg.split(':k')
        d['k_' + nm] = int(kk)
    return (fam_of[c], tuple(sorted((x, y) for x, y in d.items() if not isinstance(y, str))),
            vp.replace('k%d' % 0, ''))


ORD = {'depth': [15, 20, 25, 30, 35, 40, 50, 60], 'a': [45, 50, 55, 60, 65, 70],
       'b': [45, 50, 55, 60, 65, 70]}
KORD = [5, 10, 15, 20]


def nbrs_build(dom):
    """结构邻居: 同族 + 其余坐标全同 + 恰好一个有序坐标相邻。类别变换不算邻居。"""
    key = {}
    for c in dom:
        base = c.replace('UA::', '')
        cp = base.split('|')[0]
        vp = base.split('|')[1] if '|' in base else ''
        dd = {}
        rest = cp
        if '@' in cp:
            head, tail = cp.split('@', 1)
            num = ''
            for ch in tail:
                if ch.isdigit():
                    num += ch
                else:
                    break
            if num:
                dd['depth'] = int(num)
                rest = head + '@#' + tail[len(num):]
        legs = []
        for leg in vp.split('+'):
            if ':k' in leg:
                nm, kk = leg.rsplit(':k', 1)
                if kk.isdigit():
                    dd['k_' + nm] = int(kk)
                    legs.append(nm + ':k#')
                    continue
            legs.append(leg)
        key[c] = (rest, '+'.join(legs), tuple(sorted(dd.items())))
    bucket = collections.defaultdict(list)
    for c in dom:
        rest, legs, dd = key[c]
        bucket[(rest, legs)].append((c, dict(dd)))
    out = collections.defaultdict(list)
    for _, members in bucket.items():
        for i in range(len(members)):
            ci_, di = members[i]
            for j in range(i + 1, len(members)):
                cj_, dj = members[j]
                if set(di) != set(dj):
                    continue
                diff = [k_ for k_ in di if di[k_] != dj[k_]]
                if len(diff) != 1:
                    continue
                k_ = diff[0]
                grid = ORD.get(k_, KORD if k_.startswith('k_') else None)
                if grid is None or di[k_] not in grid or dj[k_] not in grid:
                    continue
                if abs(grid.index(di[k_]) - grid.index(dj[k_])) == 1:
                    out[ci_].append(cj_); out[cj_].append(ci_)
    return out


# ============================================================
# 4. 规则
# ============================================================
def pareto_front(sc, tu):
    """非支配: 高 net8 / 低 turn。按 turn 升序(并列按 sc 降序)扫, 保留 sc 创新高者。全向量化。"""
    o = np.lexsort((-sc, tu))
    s = sc[o]
    run = np.maximum.accumulate(np.concatenate([[-np.inf], s[:-1]]))
    return list(o[s > run])


class DomPrep(object):
    """一个域的预计算结构 —— 稳定性重采样要调 apply_rules 上万次, 逐配置 Python 循环跑不完。"""

    def __init__(self, dom, nbr):
        self.dom = dom
        self.n = len(dom)
        self.arr = np.asarray(dom, dtype=object)
        self.fam = np.asarray([fam_of[c] for c in dom])
        _, self.famcode = np.unique(self.fam, return_inverse=True)
        self.lex = np.argsort(np.asarray(dom))          # 字典序名次, 作最后一级并列键
        self.rank_name = np.empty(self.n, int)
        self.rank_name[self.lex] = np.arange(self.n)
        pos = {c: i for i, c in enumerate(dom)}
        nb = [np.asarray([pos[x] for x in nbr.get(c, []) if x in pos], dtype=int) for c in dom]
        self.maxdeg = max((len(x) for x in nb), default=0)
        M = np.full((self.n, max(self.maxdeg, 1)), -1, dtype=int)
        for i, a in enumerate(nb):
            if len(a):
                M[i, :len(a)] = a
        self.NBM = M
        self.has_nb = np.asarray([len(a) > 0 for a in nb])


def apply_rules(prep, sc, tu, need=('S1', 'S2', 'S3', 'S4', 'S5', 'S6'), tstat=None):
    """sc/tu/tstat 按 prep.dom 的顺序。同分依次用训练均值、较低换手、cfg_id 字典序。"""
    dom, n = prep.dom, prep.n
    order = np.lexsort((prep.rank_name, tu, -sc))
    out = {}
    if 'S1' in need:
        out['S1'] = [(dom[order[0]], 1.0)]
    if 'S2' in need:
        sel = order[:20]
        out['S2'] = [(dom[i], 1.0 / len(sel)) for i in sel]
    if 'S3' in need:
        _, first = np.unique(prep.famcode[order], return_index=True)
        sel = order[np.sort(first)]
        out['S3'] = [(dom[i], 1.0 / len(sel)) for i in sel]
    if 'S4' in need:
        fr = pareto_front(sc, tu)
        fr = sorted(fr, key=lambda i: tu[i])
        if len(fr) <= 5:
            sel = fr
        else:
            pos = np.linspace(0, len(fr) - 1, 5).round().astype(int)
            sel = [fr[i] for i in sorted(set(pos.tolist()))]
        out['S4'] = [(dom[i], 1.0 / len(sel)) for i in sel]
    if 'S5' in need:
        if tstat is None or not np.isfinite(tstat).any():
            out['S5'] = []
        else:
            j = int(np.nanargmax(np.where(np.isfinite(tstat), tstat, -np.inf)))
            out['S5'] = [(dom[j], 1.0)]
    if 'S6' in need:
        if prep.maxdeg == 0:
            out['S6'] = []
        else:
            V_ = np.where(prep.NBM >= 0, sc[np.maximum(prep.NBM, 0)], np.nan)
            allv = np.concatenate([V_, sc[:, None]], axis=1)
            with np.errstate(invalid='ignore'), warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                med = np.nanmedian(allv, axis=1)
            med = np.where(prep.has_nb, med, np.nan)
            if np.isfinite(med).any():
                j = int(np.nanargmax(np.where(np.isfinite(med), med, -np.inf)))
                out['S6'] = [(dom[j], 1.0)]
            else:
                out['S6'] = []
    return out


def ledger_score(members, daymask):
    """一组 (cid, α) 在给定日集合上的账本平均 net8 (年化点)。
       注意: 多成员规则 (S2/S3/S4) 的【真实混合账户】net8 ≥ 成员 net8 的加权平均 ——
       混合后的换手 ≤ 各成员换手的加权平均 (先平均权重再算成本)。故本式对多成员规则偏保守,
       用作 S_meta 的内层比较是有方向性的近似, 不是政策账户本身。"""
    if not members or daymask.sum() < 20:
        return np.nan, 0
    j = [ci[c] for c, _ in members if c in ci]
    w = np.array([a for c, a in members if c in ci], float)
    if not j:
        return np.nan, 0
    w = w / w.sum()
    X = N8[np.ix_(daymask, j)]
    return float(np.nanmean(X @ w)) * 252 * 100.0, int(daymask.sum())


_ICACHE = {}


def s_meta(dname, prep, outer_mask, start_ts, end_ts, sc, tu, tst):
    """§5.2 S_meta: 外层训练区间【内部】再切 —— 从起点满 3 年后起, 每个年末做一个前向小折,
       在小折训练段上跑 S1-S6, 用小折验证段的账本表现给六个规则打分, 按有效日加权取胜者,
       最后把胜出的规则应用在整个外层训练段上。选规则本身只用 vintage 之前可见的信息。
       无可用小折 -> 回退 S1 并标 insufficient_inner_folds。
       sc/tu/tst 是调用方已在 outer_mask 上算好的评分, 直接复用, 不重算。"""
    dom = prep.dom
    y0, y1 = start_ts.year, end_ts.year
    st_i = int(np.argmax(outer_mask))
    tot = collections.defaultdict(float)
    wsum = collections.defaultdict(float)
    nfold = 0
    for y in range(y0 + 3, y1):
        cut = pd.Timestamp('%d-12-31' % y)
        itr = outer_mask & (DT <= cut)
        iev = outer_mask & (DT > cut)
        if itr.sum() < 250 or iev.sum() < 60:
            continue
        nfold += 1
        # 内层训练掩码由 (域, 外层起点, 切年) 唯一决定 -> 跨外层 vintage 复用
        ck = (dname, st_i, y)
        sel = _ICACHE.get(ck)
        if sel is None:
            isc, itu, itst = score_on(itr, dom)
            sel = apply_rules(prep, isc, itu, tstat=itst)
            _ICACHE[ck] = sel
        for rule, members in sel.items():
            v, nd = ledger_score(members, iev)
            if v == v:
                tot[rule] += v * nd
                wsum[rule] += nd
    if not nfold or not wsum:
        return apply_rules(prep, sc, tu, tstat=tst, need=('S1',)).get('S1', []), 'S1', 0, True
    best = max(wsum, key=lambda r: tot[r] / wsum[r])
    return apply_rules(prep, sc, tu, tstat=tst, need=(best,)).get(best, []), best, nfold, False


def train_eval_days(split, direction, gap=True, exclude_2024=False):
    ts = pd.Timestamp(split)
    if direction == 'forward':
        tr = (DT <= ts) & V
        ev = (DT > ts) & V
    else:
        st = DT[DT > ts]
        if len(st) <= GAP:
            return None, None
        cut = st[GAP] if (gap and len(st) > GAP) else st[0]
        tr = (DT >= cut) & V
        ev = (DT <= ts) & V
        if exclude_2024:
            tr = tr & (DT < pd.Timestamp('2024-01-01'))
    return tr, ev


# ============================================================
# 4b. S-cost 用的冲击后训练评分 (§6.1 S1-cost / S6-cost)
#     C1 存的是每日括号 bracket_<段>.npy; c(A,κ) = κ·√(A·1e8)·bracket, 情景只是标量倍。
#     没有括号的配置评分为 NaN -> 排序落到最后, 不会被选中 (如实登记, 不填 0)。
# ============================================================
YI_ = 1e8
COST_SCEN = [(1.0, 0.5), (5.0, 0.5)]
BRC = None
_brp = [os.path.join(A.out, 'C_impact', 'bracket_%s.npy' % s) for s in F.SEGS]
_brc = [os.path.join(A.out, 'C_impact', 'bracket_cols_%s.json' % s) for s in F.SEGS]
if all(os.path.exists(p) for p in _brp + _brc):
    try:
        _bc = [json.load(open(p, encoding='utf-8')) for p in _brc]
        _com = sorted(set.intersection(*[set(x) for x in _bc]))
        _parts = []
        for _i, _s in enumerate(F.SEGS):
            _M = np.load(_brp[_i])
            _pos = {c_: j_ for j_, c_ in enumerate(_bc[_i])}
            _parts.append(_M[:, [_pos[c_] for c_ in _com]])
        BRC = np.vstack(_parts)
        assert BRC.shape[0] == len(DT), '括号行数与账本不齐'
        _bj = {c_: j_ for j_, c_ in enumerate(_com)}
        # C1 存括号时 UA 的键【带 UA:: 前缀】、E6e 的键是裸名, 与账本列名一致 ->
        # 先按原名查, 查不到再退回剥前缀 (只对两边命名不一致的历史产物兜底)。
        BJ = np.array([_bj.get(c, _bj.get(c.replace('UA::', ''), -1)) for c in cols])
        P('  S-cost: 读到每日括号 %d 列; 账本中有括号的配置 %d/%d'
          % (len(_com), int((BJ >= 0).sum()), len(cols)))
        assert (BJ >= 0).mean() > 0.99, \
            'S-cost 括号覆盖只有 %d/%d —— 多半是账本列名与括号键命名不一致, 不是真缺' \
            % (int((BJ >= 0).sum()), len(cols))
    except Exception as _e:
        BRC = None
        P('  !! S-cost 括号读取失败 (%s), 本轮不出 S-cost' % _e)
else:
    P('  S-cost: C1 每日括号尚未落盘, 本轮不出 S-cost (待 C1 后用 --skip_stability 重跑补上)')


def score_cost_on(daymask, dom, mult):
    """冲击后训练评分: net8_daily − mult × bracket_daily, 再按同分母年化。"""
    j = np.array([ci[c] for c in dom])
    b = BJ[j]
    X = N8[np.ix_(daymask, j)].copy()
    Bm = BRC[np.ix_(daymask, np.maximum(b, 0))]
    X -= mult * np.where(b[None, :] >= 0, Bm, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        sc = np.nanmean(X, axis=0) * 252 * 100.0
    tu = np.nanmean(TU[np.ix_(daymask, j)], axis=0) * 252
    return sc, tu


def add_cost_rules(sel, prep, dom, tr):
    """把 S1-cost / S6-cost 加进 sel; 返回 {规则名: 该规则用的冲击后评分向量}。
       括号未落盘时什么也不做, 由 coverage 登记 deferred。"""
    out = {}
    if BRC is None:
        return out
    for (Ay, kp) in COST_SCEN:
        csc, ctu = score_cost_on(tr, dom, kp * np.sqrt(Ay * YI_))
        if not np.isfinite(csc).any():
            continue                      # 该域没有一个配置有括号: 不选, 也不凭并列键乱选
        cs = apply_rules(prep, csc, ctu, need=('S1', 'S6'))
        for r_ in ('S1', 'S6'):
            nm_ = '%s-cost@A%g_k%g' % (r_, Ay, kp)
            sel[nm_] = cs.get(r_, [])
            out[nm_] = csc
    return out


def score_on(daymask, dom):
    j = [ci[c] for c in dom]
    X = N8[np.ix_(daymask, j)]
    sc = np.nanmean(X, axis=0) * 252 * 100.0
    tu = np.nanmean(TU[np.ix_(daymask, j)], axis=0) * 252
    d, t, _ = _hacmat(X)
    return sc, tu, t


def _hacmat(X, L=5):
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
        t = np.where((se == se) & (se > 0) & (n >= 10), mu / se, np.nan)
    return mu * 252 * 100.0, t, n


# ============================================================
# 5. 单次选择 + 年度 walk-forward 的 vintage 选择
# ============================================================
P('')
P('=== 单次选择 (6 切点 × 2 方向 × %d 域) ===' % len(DOMAINS))
NBR = {k_: nbrs_build(v) for k_, v in DOMAINS.items()}
PREP = {k_: DomPrep(v, NBR[k_]) for k_, v in DOMAINS.items()}
IPOS = {k_: {c: i for i, c in enumerate(v)} for k_, v in DOMAINS.items()}
for k_, v in NBR.items():
    deg = [len(v.get(c, [])) for c in DOMAINS[k_]]
    P('  %s 邻域: 有邻居的配置 %d/%d, 度中位 %d'
      % (k_, sum(1 for x in deg if x), len(deg), int(np.median(deg))))

rows = []
for dname, dom in DOMAINS.items():
    for split in SPLITS:
        for direction in ('forward', 'reverse'):
            for variant in (['main'] if direction == 'forward' else ['main', 'nogap', 'ex2024']):
                tr, ev = train_eval_days(split, direction,
                                         gap=(variant != 'nogap'),
                                         exclude_2024=(variant == 'ex2024'))
                if tr is None or tr.sum() < 250 or ev.sum() < 60:
                    continue
                sc, tu, tst = score_on(tr, dom)
                sel = apply_rules(PREP[dname], sc, tu, tstat=tst)
                mi = {}
                if direction == 'forward':
                    dts = DT[tr]
                    mm, mrule, nf, fb = s_meta(dname, PREP[dname], tr, dts[0], dts[-1], sc, tu, tst)
                    sel['S_meta'] = mm
                    mi = dict(meta_pick=mrule, meta_folds=nf, meta_fallback=fb)
                cs_sc = add_cost_rules(sel, PREP[dname], dom, tr)
                ip = IPOS[dname]
                for rule, members in sel.items():
                    for cid, w in members:
                        rows.append(dict(domain=dname, split=split, direction=direction,
                                         variant=variant, rule=rule, account='single',
                                         vintage=split, config_id=cid, weight=w,
                                         train_days=int(tr.sum()), eval_days=int(ev.sum()),
                                         train_score=float(sc[ip[cid]]),
                                         train_score_cost=(float(cs_sc[rule][ip[cid]])
                                                           if rule in cs_sc else np.nan),
                                         **(mi if rule == 'S_meta' else {})))
P('  单次选择行 %d' % len(rows))

P('')
P('=== 年度 walk-forward vintage (2014 年末起, 每年末重选) ===')
YEARS = list(range(2014, 2026))
for dname, dom in DOMAINS.items():
    for train_mode in ('expanding', 'rolling5y'):
        for y in YEARS:
            ts = pd.Timestamp('%d-12-31' % y)
            if train_mode == 'expanding':
                tr = (DT <= ts) & V
            else:
                tr = (DT <= ts) & (DT > pd.Timestamp('%d-12-31' % (y - 5))) & V
            if tr.sum() < 250:
                continue
            sc, tu, tst = score_on(tr, dom)
            sel = apply_rules(PREP[dname], sc, tu, tstat=tst)
            dts = DT[tr]
            mm, mrule, nf, fb = s_meta(dname, PREP[dname], tr, dts[0], ts, sc, tu, tst)
            sel['S_meta'] = mm
            mi = dict(meta_pick=mrule, meta_folds=nf, meta_fallback=fb)
            cs_sc = add_cost_rules(sel, PREP[dname], dom, tr)
            ip = IPOS[dname]
            for rule, members in sel.items():
                for cid, w in members:
                    rows.append(dict(domain=dname, split='WF_' + train_mode, direction='forward',
                                     variant=train_mode, rule=rule, account='walkforward',
                                     vintage='%d-12-31' % y, config_id=cid, weight=w,
                                     train_days=int(tr.sum()), eval_days=-1,
                                     train_score=float(sc[ip[cid]]),
                                     train_score_cost=(float(cs_sc[rule][ip[cid]])
                                                       if rule in cs_sc else np.nan),
                                     **(mi if rule == 'S_meta' else {})))
SEL = pd.DataFrame(rows)
SEL['fixed_hindsight_library'] = True
if 'meta_pick' in SEL.columns:
    M_ = SEL[SEL.rule == 'S_meta'].drop_duplicates(['domain', 'split', 'variant', 'vintage'])
    P('  S_meta: %d 个 vintage; 内层选中规则分布 %s; 折数不足回退 S1 %d 个'
      % (len(M_), dict(M_.meta_pick.value_counts()), int(M_.meta_fallback.sum())))
P('  注: S_meta 不参与第 6 节重采样稳定性 —— 重采样后的日多重集没有时间序, 内层前向小折不可识别')
SEL.to_csv(os.path.join(A.out, 'B_nested', 'selected_sets.csv'), index=False)
P('  总选择行 %d (单次 + walk-forward)' % len(SEL))
P('  被选中过的唯一配置 %d 个; 其中 UA %d 个'
  % (SEL.config_id.nunique(), int(SEL.config_id.str.startswith('UA::').sum() > 0 and
                                  SEL[SEL.config_id.str.startswith('UA::')].config_id.nunique())))

# ============================================================
# 6. 选择稳定性 (训练区间共同块重采样 B)
# ============================================================
P('')
P('=== 选择稳定性重采样 B=%d ===' % A.B)
rng = np.random.default_rng(A.seed)
strows = []
t1 = time.time()
for dname, dom in ([] if A.skip_stability else DOMAINS.items()):
    j = [ci[c] for c in dom]
    for split in SPLITS:
        tr, ev = train_eval_days(split, 'forward')
        if tr is None or tr.sum() < 250:
            continue
        di = np.where(tr)[0]
        Tt = len(di)
        X = np.nan_to_num(N8[np.ix_(tr, j)], nan=0.0)
        Xt = np.nan_to_num(TU[np.ix_(tr, j)], nan=0.0)
        CNT = F.stationary_blocks(rng, Tt, 20, A.B).astype(np.float64)
        DEN = CNT.sum(axis=0)
        SC = (X.T @ CNT) / DEN * 252 * 100.0                    # (n, B)
        TUb = (Xt.T @ CNT) / DEN * 252
        X2 = (X * X).T @ CNT / DEN
        var = np.maximum(X2 - ((X.T @ CNT) / DEN) ** 2, 0)
        with np.errstate(invalid='ignore', divide='ignore'):
            TST = np.where(var > 0, ((X.T @ CNT) / DEN) / np.sqrt(var / DEN), np.nan)
        cnt = collections.Counter()
        famcnt = collections.Counter()
        rulehit = collections.defaultdict(collections.Counter)
        for b in range(A.B):
            sel = apply_rules(PREP[dname], SC[:, b], TUb[:, b], tstat=TST[:, b])
            for rule, members in sel.items():
                for cid, w in members:
                    rulehit[rule][cid] += 1
                    cnt[cid] += 1
                    famcnt[fam_of[cid]] += 1
        for rule, cc in rulehit.items():
            tot = sum(cc.values())
            for cid, k_ in cc.most_common(20):
                strows.append(dict(domain=dname, split=split, rule=rule, config_id=cid,
                                   hits=k_, share=k_ / max(tot, 1), B=A.B,
                                   family=fam_of[cid],
                                   note='S5 用重采样朴素 t (HAC 在重采样日多重集上不可识别)'
                                   if rule == 'S5' else ''))
        P('  %-14s %s  最常选中: %s' % (dname, split,
                                    ', '.join('%s×%d' % (a[:34], b) for a, b in cnt.most_common(3))))
ST = pd.DataFrame(strows)
if A.skip_stability:
    P('  --skip_stability: 沿用首轮 selection_stability.csv, 不覆盖')
else:
    ST.to_csv(os.path.join(A.out, 'B_selection_stability', 'selection_stability.csv'), index=False)
P('  稳定性行 %d, 用时 %.0fs' % (len(ST), time.time() - t1))
if len(ST):
    top = ST[ST.rule == 'S1'].groupby(['domain', 'split']).share.max()
    P('  S1 最高单一配置被选份额: 中位 %.2f, 最小 %.2f, 最大 %.2f'
      % (top.median(), top.min(), top.max()))

json.dump(dict(stage='B2_select', when=time.strftime('%Y-%m-%d %H:%M:%S'),
               domains={k_: len(v) for k_, v in DOMAINS.items()}, B=A.B, gap=GAP,
               n_selected_rows=len(SEL), ua_included=bool(ua_cols),
               seconds=time.time() - T0),
          open(os.path.join(A.out, 'checks', 'b2_select.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
P('')
P('B2 选择完成 %.0fs' % (time.time() - T0))
_lf.close()
