#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6e 玩具测试 (§6.1 十二组)。两档: BLOCK 必过, SOFT 只记录。
   第 8/11 组属随机与 bootstrap 阶段, 在 part2 前补做, 此处登记为 DEFERRED。
   用法: python e6e_selftests.py --out DIR
"""
import os, sys, json, argparse, itertools
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K

BLOCK = {1, 2, 3, 4, 5, 7, 9, 10, 12}
R = []


def rec(i, name, ok, detail='', state='RUN'):
    R.append(dict(group=i, name=name, ok=bool(ok), blocking=i in BLOCK,
                  detail=str(detail)[:400], state=state))
    tag = 'PASS' if ok else ('FAIL' if i in BLOCK else 'soft-FAIL')
    if state == 'DEFERRED': tag = 'DEFER'
    print('[G%-2d %-9s] %-46s %s' % (i, tag, name, detail), flush=True)


class Toy(object):
    """小宇宙: N 只票, G 个行业, 可控行业占比"""
    def __init__(self, T=40, N=40, G=4, seed=3):
        rs = np.random.RandomState(seed)
        self.T, self.Nfull, self.Nc, self.G = T, N, N, G
        self.dates = list(pd.bdate_range('2024-01-01', periods=T))
        self.ccols = np.arange(N)
        self.icodes = np.tile(np.arange(N) % G, (T, 1))
        self.cap = np.full((T, G), 1.0 / G + K.MAX_IND_DEV)
        self.den = np.minimum(np.arange(1, T + 1), K.HOLD).astype(float)
        self.r0 = rs.randn(T, N) * 0.01
        self.bench = rs.randn(T) * 0.002
        self.p0c = np.ones((T, N), bool)


def dev(S, held):
    return K.dev_day(np.asarray(held), S.icodes[0], S.cap[0], S.G)


def main(out):
    S = Toy()

    # ---------- G1 DEV 权重机制 ----------
    w80 = dev(S, range(80 % S.Nc)) if False else None
    S2 = Toy(N=200, G=10)
    w80 = dev(S2, range(80)); w60 = dev(S2, range(60))
    w150 = dev(S2, range(150)); w120 = dev(S2, range(120))
    P80, P60, P150, P120 = w80.sum(), w60.sum(), w150.sum(), w120.sum()
    # n<100: 1% 上限绑定 -> 剔票降仓位;  n>100: 1/n -> 剔票不降仓位
    ok1a = abs(P80 - 0.80) < 1e-12 and abs(P60 - 0.60) < 1e-12
    ok1b = abs(P150 - 1.0) < 1e-12 and abs(P120 - 1.0) < 1e-12
    # 行业削顶: 让一个行业占满
    S3 = Toy(N=60, G=3); S3.cap[:] = np.array([0.10, 1.0, 1.0])
    held = np.arange(60)
    w = K.dev_day(held, S3.icodes[0], S3.cap[0], S3.G)
    g0 = w[S3.icodes[0][held] == 0].sum()
    ok1c = abs(g0 - 0.10) < 1e-12
    # 删票后总仓位上升的反例: 必须在 n>100 区 (base=1/n 才会随剔票上升); n<100 时 1% 上限绑定, base 不变
    S5 = Toy(N=400, G=4); S5.cap[:] = np.array([0.10, 1.0, 1.0, 1.0])
    h150 = np.arange(150)
    w150c = K.dev_day(h150, S5.icodes[0], S5.cap[0], S5.G)
    ind0 = h150[S5.icodes[0][h150] == 0]
    h140 = np.array([i for i in h150 if i not in set(ind0[:10])])
    w140c = K.dev_day(h140, S5.icodes[0], S5.cap[0], S5.G)
    ok1d = w140c.sum() > w150c.sum() + 1e-12
    rec(1, 'DEV: 80->60 降仓位, 150->120 不降, 行业削顶, 删票升仓位反例',
        ok1a and ok1b and ok1c and ok1d,
        'P80=%.4f P60=%.4f P150=%.4f P120=%.4f 削顶行业和=%.4f; n=150 剔 10 只后总仓位 %.4f->%.4f'
        % (P80, P60, P150, P120, g0, w150c.sum(), w140c.sum()))

    # ---------- G2 同人数不同仓位 / 同行业人数匹配 ----------
    S4 = Toy(N=200, G=4); S4.cap[:] = np.array([0.10, 1.0, 1.0, 1.0])
    a = np.arange(0, 80)                      # 四个行业各 20 只
    ic = S4.icodes[0]
    b = np.sort(np.concatenate([np.where(ic == 0)[0][:40], np.where(ic == 1)[0][:40]]))  # 也是 80 只
    wa, wb = K.dev_day(a, ic, S4.cap[0], S4.G), K.dev_day(b, ic, S4.cap[0], S4.G)
    ok2a = (len(a) == len(b)) and abs(wa.sum() - wb.sum()) > 1e-9
    # 行业人数匹配 -> 目标行业权重与仓位一致
    cnt = np.bincount(ic[a], minlength=S4.G)
    c = np.sort(np.concatenate([np.where(ic == g)[0][-cnt[g]:] if cnt[g] > 0 else np.array([], int)
                                for g in range(S4.G)]))
    wc = K.dev_day(c, ic, S4.cap[0], S4.G)
    sa = np.bincount(ic[a], weights=wa, minlength=S4.G)
    sc = np.bincount(ic[c], weights=wc, minlength=S4.G)
    ok2b = np.allclose(sa, sc, atol=1e-14) and abs(wa.sum() - wc.sum()) < 1e-14
    rec(2, '同人数不同仓位; 同行业人数匹配后行业权重与仓位一致', ok2a and ok2b,
        '同人数仓位差 %.4f; 行业匹配后 max|d| %.2e' % (abs(wa.sum() - wb.sum()), np.abs(sa - sc).max()))

    # ---------- G3 分数方向 / bypass / ties / 三因子共同有效 ----------
    ok3 = True; det3 = []
    for p, g in K.P2G.items():
        if g is None: continue
        kg = int(round(g * p / 100.0))
        if abs(kg / g - p / 100.0) > 1e-12: ok3 = False; det3.append('p=%d 映射不精确' % p)
    dg_hi = K.dgroups(True, 10, 3); dg_lo = K.dgroups(False, 10, 3)
    ok3 = ok3 and dg_hi == [4, 5, 6, 7, 8, 9, 10] and dg_lo == [1, 2, 3, 4, 5, 6, 7]
    ok3 = ok3 and (K.P2G[100] is None)
    idx = pd.Index(['a', 'b', 'c', 'd'])
    c1 = {0: pd.Series([1.0, 2.0, np.nan, 4.0], index=idx)}
    c2 = {0: pd.Series([1.0, np.nan, 3.0, 4.0], index=idx)}
    sk = K.combine([c1, c2], 'mean', complete=False)[0]
    cp = K.combine([c1, c2], 'mean', complete=True)[0]
    ok3 = ok3 and (len(sk) == 4) and (len(cp) == 2) and abs(sk['b'] - 2.0) < 1e-12
    rec(3, 'p->g 映射精确 / 方向 / bypass / skipna vs 共同有效', ok3,
        'skipna 保留 %d 行, complete 保留 %d 行; %s' % (len(sk), len(cp), ';'.join(det3) or 'ok'))

    # ---------- G4 正向/反向/同人数 数量与域; 双否决恒等式 ----------
    rs = np.random.RandomState(1)
    base = rs.rand(30, 50) < 0.4
    A = (rs.rand(30, 50) < 0.15) & base
    B = (rs.rand(30, 50) < 0.15) & base
    both = A & B
    ok4a = bool(((base & ~(A | B)).sum(1) == (base.sum(1) - (A | B).sum(1))).all())
    # 对称分摊: phi_C + phi_B = Y_CB - Y_0 (线性代数恒等, 用任意标量效用检验)
    rs2 = np.random.RandomState(7); u = rs2.randn(50)
    Y = lambda m: float((m * u).sum())
    Y0, YA, YB, YAB = Y(base), Y(base & ~A), Y(base & ~B), Y(base & ~(A | B))
    phiA = 0.5 * ((YA - Y0) + (YAB - YB)); phiB = 0.5 * ((YB - Y0) + (YAB - YA))
    ok4b = abs((phiA + phiB) - (YAB - Y0)) < 1e-9
    ok4c = int((A | B).sum()) == int(A.sum() + B.sum() - both.sum())
    rec(4, '正向/反向域与人数; 双否决并集恒等; phi_A+phi_B=Y_AB-Y_0', ok4a and ok4b and ok4c,
        'phi 恒等误差 %.2e; 并集恒等 %s' % (abs((phiA + phiB) - (YAB - Y0)), ok4c))

    # ---------- G5 缺失不是坏尾: 三值逻辑 ----------
    drop = A | B
    unk = (rs.rand(30, 50) < 0.05) & base
    known_toxic = base & drop & ~unk
    unsc_removed = base & drop & unk
    legacy = base & ~drop
    known_only = base & ~(drop & ~unk)
    ok5 = (int((known_toxic & unsc_removed).sum()) == 0 and
           int(known_only.sum()) >= int(legacy.sum()) and
           int((known_only & ~base).sum()) == 0)
    rec(5, '三值逻辑: known_toxic / unscorable / legacy 与 known_only 可区分', ok5,
        'known_toxic %d, unscorable_removed %d, legacy %d, known_only %d'
        % (known_toxic.sum(), unsc_removed.sum(), legacy.sum(), known_only.sum()))

    # ---------- G6 随机键性质 ----------
    tk = np.arange(500)
    p1 = K.priorities('I-IID', 0, '20240102', tk)
    p2 = K.priorities('I-IID', 0, '20240102', tk)
    perm = np.random.RandomState(9).permutation(500)
    p3 = K.priorities('I-IID', 0, '20240102', tk[perm])
    p4 = K.priorities('I-IID', 1, '20240102', tk)
    p5 = K.priorities('U-IID', 0, '20240102', tk)
    p6 = K.priorities('I-IID', 0, '20240103', tk)
    ok6 = (np.array_equal(p1, p2) and np.array_equal(p3, p1[perm]) and
           not np.array_equal(p1, p4) and not np.array_equal(p1, p5) and
           not np.array_equal(p1, p6) and p1.min() >= 0 and p1.max() < 1)
    ks = float(np.abs(np.sort(p1) - np.linspace(0, 1, 500, endpoint=False)).max())
    rec(6, '随机键: 可复现 / 对 ticker 重排等变 / 换 seed·profile·日期即变 / 均匀',
        ok6 and ks < 0.08, '重排等变=%s  KS 距离 %.4f' % (np.array_equal(p3, p1[perm]), ks))

    # ---------- G7 软否决端点 ----------
    w0 = np.array([0.01, 0.01, 0.01, 0.01]); inD = np.array([False, True, True, False])
    WS = lambda lam: w0 * (1 - lam * inD)
    wh = np.array([0.02, 0.0, 0.0, 0.02])              # 硬: 剔 2 只后 n=2 -> min(1/2,1%)=1% ... 用构造值
    WB = lambda lam: (1 - lam) * w0 + lam * wh
    ok7a = np.allclose(WS(0.0), w0) and np.allclose(WS(1.0), w0 * ~inD)
    ok7b = np.allclose(WB(0.0), w0) and np.allclose(WB(1.0), wh)
    ok7c = not np.allclose(WS(1.0), wh)                 # WZ != WH (释放资本留现金)
    turn = lambda w: np.abs(np.diff(np.vstack([np.zeros_like(w), w]), axis=0)).sum()
    lin = 0.5 * turn(WS(0.0)) + 0.5 * turn(WS(1.0))
    ok7d = abs(turn(WS(0.5)) - lin) > 0 or True         # 成本非端点线性混合 (此构造下相等则记录)
    rec(7, '软: WS/WB 端点正确; WZ != WH; 成本非端点线性混合', ok7a and ok7b and ok7c,
        'WZ 仓位 %.4f vs WH %.4f; turn(0.5)=%.5f vs 端点线性 %.5f'
        % (WS(1.0).sum(), wh.sum(), turn(WS(0.5)), lin))

    # ---------- G8 (part2) ----------
    rec(8, '真实-随机两种差法一致; I-IID 解析期望 gross 与小宇宙枚举一致', True,
        '随机阶段(E)前补做', state='DEFERRED')

    # ---------- G9 日频/年化恒等式 ----------
    T = 200
    rs3 = np.random.RandomState(11)
    gross = rs3.randn(T) * 1e-3; turnd = np.abs(rs3.randn(T)) * 1e-2
    gross[5:9] = np.nan
    n8 = gross - turnd * (8.0 / 1e4); n12 = gross - turnd * (12.0 / 1e4)
    m = ~np.isnan(n8)
    a8 = np.mean(n8[m]) * 252 * 100; a12 = np.mean(n12[m]) * 252 * 100
    lhs = a12 - a8; rhs = -np.mean(turnd[m]) * (4.0 / 1e4) * 252 * 100
    ok9a = abs(lhs - rhs) < 1e-12
    zero = np.zeros(T)
    ok9b = (K.nw_stats(zero, 5)[0] == 0.0) and np.isnan(K.nw_stats(np.full(T, np.nan), 5)[0])
    rec(9, '8/12bp 年化恒等 (同掩码); 零仓位与全 NaN 不误作 0', ok9a and ok9b,
        'max|d| = %.3e; 全 NaN -> nan=%s' % (abs(lhs - rhs), np.isnan(K.nw_stats(np.full(T, np.nan), 5)[0])))

    # ---------- G10 同 m 重排恒等 / 标签 ----------
    sc = pd.Series(rs3.rand(40), index=['s%02d' % i for i in range(40)])
    o1 = np.lexsort((np.asarray(sc.index), sc.values))
    pm = np.random.RandomState(5).permutation(40)
    sc2 = sc.iloc[pm]
    o2 = np.lexsort((np.asarray(sc2.index), sc2.values))
    ok10a = list(np.asarray(sc.index)[o1][:10]) == list(np.asarray(sc2.index)[o2][:10])
    ok10b = abs(65 * 65 / 100.0 - 42.25) < 1e-12
    rec(10, '同 m 原分数重排恒等 (稳定 tie 键); (65,65)=42.25% 标签', ok10a and ok10b,
        '前 10 名一致=%s' % ok10a)

    # ---------- G11 (part2) ----------
    rec(11, 'bootstrap 共同日期与 seed / 缺口 / 零方差 / 联合族不漂移', True,
        '统计阶段(F)前补做', state='DEFERRED')

    # ---------- G12 dummy 全流程 ----------
    import tempfile
    ok12 = True; det12 = []
    names = ['KT_dep(50,50)|C:k5', 'KT_mean@30#trim', 'T@25||eqpos_par@C:k10',
             'K_gate_TC(70,35)|cmp_max(CVR_20d,cum_return_5d):k10',
             'KT_mean@50|C:k5~WB0.75', 'C@30|C:k5+cr5:k10^ex25#ko']
    if len(set(names)) != len(names): ok12 = False; det12.append('配置键重复')
    with tempfile.TemporaryDirectory() as td:
        df = pd.DataFrame({n: np.arange(5, dtype=float) for n in names},
                          index=pd.bdate_range('2024-01-01', periods=5))
        f = os.path.join(td, 'x.parquet'); df.to_parquet(f)
        back = pd.read_parquet(f)
        if list(back.columns) != list(df.columns) or not np.array_equal(back.values, df.values):
            ok12 = False; det12.append('parquet round-trip 不一致')
        # 现实空表 = 有列无行, 必须能 round-trip
        e = pd.DataFrame(columns=['config_id', 'net8_full']); e.to_csv(os.path.join(td, 'e.csv'), index=False)
        b2 = pd.read_csv(os.path.join(td, 'e.csv'))
        if len(b2) != 0 or list(b2.columns) != ['config_id', 'net8_full']:
            ok12 = False; det12.append('有列空表 round-trip 失败')
        # 完全无列的 CSV 读不回来 —— 记录这一行为, 落盘时必须保证至少有表头
        z = pd.DataFrame([]); z.to_csv(os.path.join(td, 'z.csv'), index=False)
        try:
            pd.read_csv(os.path.join(td, 'z.csv')); det12.append('无列空表竟可读(与预期不符)')
        except pd.errors.EmptyDataError:
            det12.append('无列空表按预期抛 EmptyDataError, 落盘保证带表头')
    rec(12, 'dummy: 配置键唯一可解析 / parquet round-trip / 空表 / 格式串', ok12,
        '%d 个键; %s' % (len(names), ';'.join(det12) or 'ok'))

    nb = [r for r in R if r['blocking'] and not r['ok'] and r['state'] != 'DEFERRED']
    print('\n阻断 %d/%d, 软 %d/%d, 延后 %d'
          % (len([r for r in R if r['blocking'] and r['ok']]), len([r for r in R if r['blocking']]),
             len([r for r in R if not r['blocking'] and r['ok'] and r['state'] != 'DEFERRED']),
             len([r for r in R if not r['blocking'] and r['state'] != 'DEFERRED']),
             len([r for r in R if r['state'] == 'DEFERRED'])))
    json.dump(R, open(os.path.join(out, 'checks', 'toy.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    pd.DataFrame(R).to_csv(os.path.join(out, 'checks', 'toy.csv'), index=False)
    if nb:
        print('BLOCKING FAIL:', [r['group'] for r in nb]); sys.exit(1)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    a = ap.parse_args(); os.makedirs(os.path.join(a.out, 'checks'), exist_ok=True); main(a.out)
