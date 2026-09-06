#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6d 玩具测试(合成面板/合成因子). 两档: BLOCK 必须全过才继续; SOFT 失败只记录。
   用法: python e6d_selftests.py --out <dir>
"""
import sys, os, json, argparse, itertools
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import comprehensive_factor_diagnosis as C
import e6d_combination_taxonomy as M

BLOCK = {1, 2, 3, 4, 5, 6, 7, 8}
R = []


def rec(i, name, ok, detail=''):
    R.append(dict(id=i, name=name, ok=bool(ok), blocking=i in BLOCK, detail=str(detail)[:400]))
    tag = 'PASS' if ok else ('FAIL' if i in BLOCK else 'soft-FAIL')
    print('[T%-2d %-9s] %-44s %s' % (i, tag, name, detail), flush=True)


def panel(T=44, N=4, jumps=None):
    """无除权合成面板: lclose = 前一日 close -> adjust_factor 恒为 1"""
    idx = pd.bdate_range('2024-01-01', periods=T)
    cols = ['S%d' % i for i in range(N)]
    v = np.ones((T, N))
    for (t, i, r) in (jumps or []):
        v[t:, i] *= (1.0 + r)
    vwap = pd.DataFrame(v, index=idx, columns=cols)
    close = vwap.copy()
    lclose = close.shift(1); lclose.iloc[0] = close.iloc[0]
    return dict(close=close, lclose=lclose, vwap=vwap,
                is_open=pd.DataFrame(1, index=idx, columns=cols),
                change_pct=close / lclose - 1), idx, cols


def synth(T=40, N=60, seed=7, rho=0.0):
    """合成因子面板: X, Y 目标截面相关 rho; log_mcap 独立随机"""
    rs = np.random.RandomState(seed)
    idx = pd.bdate_range('2024-01-01', periods=T)
    cols = ['S%03d' % i for i in range(N)]
    a = rs.randn(T, N); b = rs.randn(T, N)
    y = rho * a + np.sqrt(max(0.0, 1.0 - rho ** 2)) * b
    X = pd.DataFrame(a, index=idx, columns=cols)
    Y = pd.DataFrame(y, index=idx, columns=cols)
    lm = pd.DataFrame(rs.randn(T, N) * 0.5 + 10.0, index=idx, columns=cols)
    pool = pd.DataFrame(1.0, index=idx, columns=cols)
    return X, Y, lm, pool, idx, cols


def sep_ok(cache, mask_keep, pool_df, high_bad=True, restrict=None):
    """保留集内的因子值必须整体优于被丢弃集 (逐日检验分组切分的定义性质)。
       restrict: 只在这个子universe内比较 —— 二阶段规则只承诺在 S1 内部分离, 不在全池分离。"""
    cols = np.asarray(pool_df.columns); bad_days = 0; checked = 0
    for i, d in enumerate(pool_df.index):
        if d not in cache: continue
        s = cache[d]
        univ = set(s.index)
        if restrict is not None:
            univ &= set(cols[restrict[i]])
        keep = sorted(univ & set(cols[mask_keep[i]]))
        drop = sorted(univ - set(keep))
        if not keep or not drop: continue
        checked += 1
        if high_bad:
            if s.loc[keep].max() > s.loc[drop].min() + 1e-12: bad_days += 1
        else:
            if s.loc[keep].min() < s.loc[drop].max() - 1e-12: bad_days += 1
    return bad_days, checked


def main(out):
    # ---------- T1 (BLOCK) 分组/保留比例的组号全枚举 ----------
    exp = {(True, 2, 1): [2], (False, 2, 1): [1], (True, 4, 1): [2, 3, 4], (False, 4, 1): [1, 2, 3],
           (True, 5, 4): [5], (False, 5, 4): [1], (True, 10, 5): [6, 7, 8, 9, 10],
           (True, 10, 3): [4, 5, 6, 7, 8, 9, 10], (True, 20, 7): list(range(8, 21)),
           (True, 20, 14): list(range(15, 21)), (False, 10, 7): [1, 2, 3]}
    bad = [(k, M.dgroups(*k), v) for k, v in exp.items() if M.dgroups(*k) != v]
    # keep_pct 的 n_groups 与 keep_g 选取
    kp = {}
    for f in sorted({50, 30, 20, 25, 35, 40, 60, 70}):
        n = 10 if f % 10 == 0 else 20
        kp[f] = (n, int(round(n * f / 100.0)))
    ok1 = (not bad) and kp[35] == (20, 7) and kp[70] == (10, 7) and kp[25] == (20, 5) and kp[30] == (10, 3)
    rec(1, u'dgroups 全枚举 + keep_pct 组数选取', ok1,
        'bad=%s  keep_pct[35]=%s [70]=%s [25]=%s' % (bad, kp[35], kp[70], kp[25]))

    # ---------- T2 (BLOCK) DEP = 先按 X 切一半, 再在保留集内按重中性化的 Y 切一半 ----------
    X, Y, lm, pool, idx, cols = synth(seed=11, rho=0.3)
    neuX = C.precompute_neutralized_factor(X, pool, lm)
    S1 = M.holds(neuX, pool, 2, 1, True)
    b1, c1 = sep_ok(neuX, M.mk(S1), pool, True)
    cY = C.precompute_neutralized_factor(Y, S1, lm)
    mdep = M.mk(M.holds(cY, S1, 2, 1, True))
    b2, c2 = sep_ok(cY, mdep, pool, True, restrict=M.mk(S1))
    subset = bool((mdep & ~M.mk(S1)).sum() == 0)
    r1 = float(M.mk(S1).sum()) / float((pool.values == 1).sum())
    r2 = float(mdep.sum()) / float((pool.values == 1).sum())
    ok2 = (b1 == 0) and (b2 == 0) and subset and 0.45 < r1 < 0.55 and 0.20 < r2 < 0.30
    rec(2, u'DEP 两阶段切分性质 + 子集 + 浓度', ok2,
        'S1 违例 %d/%d, S2 违例 %d/%d, 子集=%s, 保留 %.3f -> %.3f' % (b1, c1, b2, c2, subset, r1, r2))

    # ---------- T3 (BLOCK) IND 浓度随相关性 ----------
    conc = {}
    for rho in (0.9, 0.0, -0.9):
        Xa, Ya, lma, poola, _, _ = synth(seed=23, rho=rho)
        ha = M.mk(M.holds(C.precompute_neutralized_factor(Xa, poola, lma), poola, 2, 1, True))
        hb = M.mk(M.holds(C.precompute_neutralized_factor(Ya, poola, lma), poola, 2, 1, True))
        conc[rho] = float((ha & hb).sum()) / float((poola.values == 1).sum())
    ok3 = conc[0.9] > 0.28 and 0.22 < conc[0.0] < 0.28 and conc[-0.9] < 0.22
    rec(3, u'IND 浓度: 正相关>25% 零相关≈25% 负相关<25%', ok3,
        'rho +0.9 -> %.3f, 0.0 -> %.3f, -0.9 -> %.3f' % (conc[0.9], conc[0.0], conc[-0.9]))

    # ---------- T4 (BLOCK) CMEAN/CMAX 构造 + 四分组薄日门槛 ----------
    X, Y, lm, pool, idx, cols = synth(seed=31, rho=0.2)
    px = M.pct_or(C.precompute_neutralized_factor(X, pool, lm), True)
    py = M.pct_or(C.precompute_neutralized_factor(Y, pool, lm), True)
    cm = M.combine([px, py], 'mean'); cx = M.combine([px, py], 'max')
    ge = all(bool((cx[d] >= cm[d] - 1e-12).all()) for d in cm)
    m25 = M.mk(M.holds(cm, pool, 4, 1, True)); m50 = M.mk(M.holds(cm, pool, 2, 1, True))
    mx25 = M.mk(M.holds(cx, pool, 4, 1, True))
    bm, cmn = sep_ok(cm, m25, pool, True)
    bx, cxn = sep_ok(cx, mx25, pool, True)
    r25 = float(m25.sum()) / float((pool.values == 1).sum())
    r50 = float(m50.sum()) / float((pool.values == 1).sum())
    # 薄日: 11 只 -> n_groups=4 需 >=12, 应无持仓; n_groups=2 需 >=6, 应有持仓
    thin = pool.copy(); thin.iloc[:, 11:] = 0.0
    tn4 = M.mk(M.holds(C.precompute_neutralized_factor(X, thin, lm), thin, 4, 1, True)).sum()
    tn2 = M.mk(M.holds(C.precompute_neutralized_factor(X, thin, lm), thin, 2, 1, True)).sum()
    ok4 = ge and bm == 0 and bx == 0 and 0.20 < r25 < 0.30 and 0.45 < r50 < 0.55 and tn4 == 0 and tn2 > 0
    rec(4, u'CMEAN/CMAX 切分 + max>=mean + 薄日门槛', ok4,
        'max>=mean=%s, 违例 %d/%d & %d/%d, 保留 %.3f/%.3f, 11 只: 四分组 %d 票 二分组 %d 票'
        % (ge, bm, cmn, bx, cxn, r25, r50, int(tn4), int(tn2)))

    # ---------- T5 (BLOCK) 低=坏 因子保留高端 ----------
    X, Y, lm, pool, idx, cols = synth(seed=41)
    nx = C.precompute_neutralized_factor(X, pool, lm)
    hi = M.mk(M.holds(nx, pool, 2, 1, False))      # 低=坏 -> 保留高端
    lo = M.mk(M.holds(nx, pool, 2, 1, True))       # 高=坏 -> 保留低端
    bhi, chi = sep_ok(nx, hi, pool, False)
    disjoint = int((hi & lo).sum())
    ok5 = bhi == 0 and disjoint == 0 and abs(int(hi.sum()) - int(lo.sum())) <= len(idx)
    rec(5, u'方向: 低=坏 保留高端, 与高=坏 互补', ok5,
        '违例 %d/%d, 两侧交集 %d 格, 票数 %d vs %d' % (bhi, chi, disjoint, int(hi.sum()), int(lo.sum())))

    # ---------- T6 (BLOCK) DEPnr 只换排序范围, 不换中性化范围 ----------
    X, Y, lm, pool, idx, cols = synth(seed=53, rho=0.25)
    neuX = C.precompute_neutralized_factor(X, pool, lm)
    neuY = C.precompute_neutralized_factor(Y, pool, lm)
    S1 = M.holds(neuX, pool, 2, 1, True)
    mdep = M.mk(M.holds(C.precompute_neutralized_factor(Y, S1, lm), S1, 2, 1, True))
    sub = M.sub_cache(neuY, M.stock_map(S1))
    mnr = M.mk(M.holds(sub, S1, 2, 1, True))
    bnr, cnr = sep_ok(neuY, mnr, pool, True, restrict=M.mk(S1))   # 只在 S1 内检验分离
    sub_ok = bool((mnr & ~M.mk(S1)).sum() == 0)
    differ = int((mdep ^ mnr).sum())
    keys_ok = set(sub) <= set(neuY)
    ok6 = bnr == 0 and sub_ok and keys_ok and differ > 0
    rec(6, u'DEPnr: 用 pool0 中性化值在 S1 内排序, 且与 DEP 不同', ok6,
        '违例 %d/%d, 子集=%s, 与 DEP 差 %d 格' % (bnr, cnr, sub_ok, differ))

    # ---------- T7 (BLOCK) net12 = net8 - 换手x4bp 的逐日恒等 ----------
    data, idx7, cols7 = panel(T=60, N=6, jumps=[(20, 0, 0.02), (35, 3, -0.015)])
    pool7 = pd.DataFrame(1.0, index=idx7, columns=cols7)
    rs = np.random.RandomState(5)
    W = pd.DataFrame((rs.rand(len(idx7), len(cols7)) < 0.5) * 0.01, index=idx7, columns=cols7)
    p8 = C.compute_calendar_pnl(W, data, pool7, hold_days=5, cost_bp_bilateral=8.0)
    p12 = C.compute_calendar_pnl(W, data, pool7, hold_days=5, cost_bp_bilateral=12.0)
    lhs = p8['net_excess_daily'] - p8['daily_turnover'] * (4.0 / 1e4)
    err = float(np.nanmax(np.abs((lhs - p12['net_excess_daily']).values)))
    same_idx = bool(p8['daily_turnover'].index.equals(p8['net_excess_daily'].index))
    ok7 = err < 1e-15 and same_idx
    rec(7, u'net12 解析换算 = 引擎 12bp 重跑', ok7, 'max|d| = %.3e, 索引一致=%s' % (err, same_idx))

    # ---------- T8 (BLOCK) 全部配置名唯一且可反解 ----------
    names = []
    for f in M.F12:
        names += ['SF50:' + f, 'SF25:' + f]
    for a in M.F12:
        for b in M.F12:
            if a != b: names += ['DEP:%s>%s' % (a, b), 'DEPnr:%s>%s' % (a, b)]
    for i, a in enumerate(M.F12):
        for b in M.F12[i + 1:]:
            names += ['IND:%s+%s' % (a, b), 'CMEAN25:%s+%s' % (a, b),
                      'CMEAN50:%s+%s' % (a, b), 'CMAX25:%s+%s' % (a, b)]
    for a, b in [(M.F12[0], M.F12[1])]:
        for z in M.Z6:
            if z in (a, b): continue
            names += ['T3rel:%s>%s>%s' % (a, b, z), 'T3abs5:%s>%s>%s' % (a, b, z),
                      'T3abs10:%s>%s>%s' % (a, b, z)]
        for (s1, s2) in M.DEPTH_GRID + [(50, 50)]:
            names.append('DEPTH:%s>%s@%d_%d' % (a, b, s1, s2))
    names += M.ANCH_CFG + ['pool0_DEV']

    def parse(c):
        head, _, body = c.partition(':')
        if head in ('SF50', 'SF25'): return dict(method=head, X=body)
        if head in ('DEP', 'DEPnr'):
            x, y = body.split('>'); return dict(method=head, X=x, Y=y)
        if head == 'DEPTH':
            bb, _, dep = body.partition('@'); x, y = bb.split('>'); s1, s2 = dep.split('_')
            return dict(method='DEPTH', X=x, Y=y, s1=int(s1), s2=int(s2))
        if head in ('IND', 'CMEAN25', 'CMEAN50', 'CMAX25'):
            x, y = body.split('+'); return dict(method=head, X=x, Y=y)
        if head.startswith('T3'):
            x, y, z = body.split('>'); return dict(method=head, X=x, Y=y, Z=z)
        return dict(method='other')      # 锚点/基线名不带因子参数, 不检因子成员
    dup = len(names) - len(set(names))
    bad8 = []
    for c in names:
        try:
            p = parse(c)
            for k in ('X', 'Y', 'Z'):
                if p.get(k) and p[k] not in M.F12: bad8.append((c, k, p[k]))
        except Exception as e:
            bad8.append((c, 'exc', str(e)))
    n_pair = sum(1 for c in names if c.startswith(('IND:', 'CMEAN', 'CMAX')))
    n_dep = sum(1 for c in names if c.startswith('DEP:'))
    ok8 = dup == 0 and not bad8 and n_dep == 132 and n_pair == 264
    rec(8, u'配置名唯一 + 可反解 + 计数', ok8,
        '共 %d 个, 重名 %d, 反解失败 %d, DEP=%d, 无序对=%d' % (len(names), dup, len(bad8), n_dep, n_pair))

    # ---------- T9 (soft) keep_pct 实际保留比例 ----------
    X, Y, lm, pool, idx, cols = synth(T=30, N=200, seed=61)
    nx = C.precompute_neutralized_factor(X, pool, lm)
    got = {}
    for f in (70, 60, 50, 40, 35, 30, 25, 20):
        m = M.keep_pct(nx, pool, f, True)
        got[f] = float(m.sum()) / float((pool.values == 1).sum())
    ok9 = all(abs(got[f] - f / 100.0) < 0.03 for f in got)
    rec(9, u'keep_pct 实际保留比例 (200 只池)', ok9,
        ' '.join('%d%%->%.3f' % (f, got[f]) for f in sorted(got, reverse=True)))

    # ---------- T10 (soft) (70,35) 在薄池上的门槛行为 ----------
    det10 = []
    for N in (100, 80, 60):
        Xa, Ya, lma, poola, _, _ = synth(T=20, N=N, seed=71)
        nxa = C.precompute_neutralized_factor(Xa, poola, lma)
        h1m = M.keep_pct(nxa, poola, 70, True)
        h1 = pd.DataFrame(h1m.astype(float), index=poola.index, columns=poola.columns)
        pY = M.pct_or(C.precompute_neutralized_factor(Ya, h1, lma), True)
        m = M.keep_pct(pY, h1, 35, True)
        nd = int((m.sum(axis=1) == 0).sum())
        det10.append('N=%d: S1均%.0f 无持仓 %d/%d 天' % (N, h1m.sum(axis=1).mean(), nd, len(poola.index)))
    rec(10, u'(70,35) 用 20 分位在薄池上的无持仓天数', True, '; '.join(det10))

    # ---------- T11 (soft) drop_or 与 e6 drop_mask 逐字一致 ----------
    X, Y, lm, pool, idx, cols = synth(seed=83)
    nx = C.precompute_neutralized_factor(X, pool, lm)
    diffs = []
    for k in (5, 10):
        ref = (pool.values == 1) & ~(C.build_factor_strategy_holdings_cached(nx, pool, k, [k]).values == 1)
        diffs.append(int((ref ^ M.drop_or(nx, pool, k, True)).sum()))
        ref2 = (pool.values == 1) & ~(C.build_factor_strategy_holdings_cached(nx, pool, k, [1]).values == 1)
        diffs.append(int((ref2 ^ M.drop_or(nx, pool, k, False)).sum()))
    rec(11, u'drop_or == e6 drop_mask / e6b tox (两方向)', all(d == 0 for d in diffs), 'diffs=%s' % diffs)

    # ---------- T12 (soft) 定向 pct 使相关号正确 ----------
    X, Y, lm, pool, idx, cols = synth(seed=97, rho=0.8)
    px = M.pct_or(C.precompute_neutralized_factor(X, pool, lm), True)
    py_hi = M.pct_or(C.precompute_neutralized_factor(Y, pool, lm), True)
    py_lo = M.pct_or(C.precompute_neutralized_factor(Y, pool, lm), False)
    d0 = sorted(set(px) & set(py_hi))[0]
    r_hi = px[d0].corr(py_hi[d0], method='spearman')
    r_lo = px[d0].corr(py_lo[d0], method='spearman')
    ok12 = (r_hi > 0) and (abs(r_hi + r_lo) < 1e-9)
    rec(12, u'定向 pct: 翻向后相关号取反', ok12, 'rho_hi=%+.4f rho_lo=%+.4f' % (r_hi, r_lo))

    # ---------- T13 (soft) msha 稳定且敏感 ----------
    a = np.zeros((7, 5), dtype=bool); a[2, 3] = True
    b = a.copy(); c2 = a.copy(); c2[0, 0] = True
    ok13 = (M.msha(a) == M.msha(b)) and (M.msha(a) != M.msha(c2))
    rec(13, u'msha 同掩码同值/改一格变值', ok13, '%s vs %s' % (M.msha(a), M.msha(c2)))

    # ---------- T14 (soft) 无持仓日不贡献收益且仓位为 0 ----------
    data, idx14, cols14 = panel(T=40, N=5, jumps=[(10, 0, 0.05)])
    pool14 = pd.DataFrame(1.0, index=idx14, columns=cols14)
    W = pd.DataFrame(0.0, index=idx14, columns=cols14)
    pr = C.compute_calendar_pnl(W, data, pool14, hold_days=5, cost_bp_bilateral=8.0)
    ok14 = (float(np.nanmax(np.abs(pr['net_excess_daily'].values))) == 0.0 and
            float(np.nanmax(np.abs(pr['daily_position'].values))) == 0.0)
    rec(14, u'全空持仓 -> 净收益与仓位恒为 0', ok14,
        'max|net| = %.3e' % float(np.nanmax(np.abs(pr['net_excess_daily'].values))))

    nb = [r for r in R if r['blocking'] and not r['ok']]
    ns = [r for r in R if not r['blocking'] and not r['ok']]
    print('\n阻断档 %d/%d, 软档 %d/%d' % (len([r for r in R if r['blocking'] and r['ok']]),
                                        len([r for r in R if r['blocking']]),
                                        len([r for r in R if not r['blocking'] and r['ok']]),
                                        len([r for r in R if not r['blocking']])))
    with open(os.path.join(out, 'selftest_results.json'), 'w', encoding='utf-8') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
    if nb:
        print('BLOCKING FAIL:', [r['id'] for r in nb]); sys.exit(1)
    if ns:
        print('soft-FAIL (记录, 不中止):', [r['id'] for r in ns])


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); main(a.out)
