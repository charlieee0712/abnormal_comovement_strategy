# -*- coding: utf-8 -*-
"""E6q 缓存命名空间（brief §7 / §1.2 / A-H；目录名含 E6q-v1.1 与 86c246dd，闭包门 ⑮；E6q v1.0 缓存不复用）。
1. E6p 缓存 panels / triggers / source 与 E6o 缓存 minute 逐文件硬链（只读复用；sha 清单 cache_reuse_manifest.json）；
2. 新触发 UNION_T1a_T8 = T1a ∨ T8_LIMIT_CLOSE 三值或（任一已知真 → 1；两者已知假 → 0；否则 −1 = UNKNOWN）；同日交集只是一个面板值 = 一次意向；
3. 新面板（brief §1.2 / C9）：
   - amihud20 = T−20…T−1 上 |r_day| / amt 的均值（≥ 10 观测；amt ≤ 0、非开盘或缺失 → 不计；单位 1 / CNY），e6o_panels.rolling_prev 同式；
   - open_adj / high_adj / low_adj / close_adj = raw × F（后复权；开盘日外 NaN）；F = lclose 链式因子：每个开盘日 F_t = F_prev × 上一开盘日 raw 收盘 / lclose_t
     （lclose = 数据商已按除权除息调整的前收盘，与 r_day 同一口径；上市首日 F = 1）。不用 adj_factor：其在开盘格上缺 2–11%（各年），lclose 全覆盖；
     edge21 = e6q_edge.rolling_panel（止于 T−1 的 21 日窗，完整 OHLC ≥ 3）；
4. 事实 cache_facts.json：计数、作者四例自检、面板抽查（edge 逐窗重算、UNION 逐格重算、amihud 逐格重算）。不读策略收益。
用法：python3 e6q_cache.py [--workers 96] [--ref-dir <作者样本目录>]"""
import os
import sys
import json
import time
import argparse
import resource

import numpy as np

import e6q_core as O
import e6q_edge as EG


def link_tree(src_root, subs, cd, tag):
    man = {}
    for sub in subs:
        sd = os.path.join(src_root, sub)
        dd = os.path.join(cd, sub)
        os.makedirs(dd, exist_ok=True)
        for fn in sorted(os.listdir(sd)):
            sp = os.path.join(sd, fn)
            if not os.path.isfile(sp) or '.tmp' in fn:
                continue
            dp = os.path.join(dd, fn)
            if not os.path.exists(dp):
                os.link(sp, dp)
            man['%s/%s' % (sub, fn)] = dict(bytes=os.path.getsize(dp), sha256=O.sha_file(dp), source=tag)
    return man


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=96)
    ap.add_argument('--ref-dir', default='')
    a = ap.parse_args()
    t0 = time.time()
    cd = O.cache_dir()
    if 'E6q-v1.1' not in cd or '86c246dd' not in cd:
        raise RuntimeError('缓存命名空间不含 E6q-v1.1 / 86c246dd')
    man = link_tree(O.E6P_CACHE, ('panels', 'triggers', 'source'), cd, 'E6p cache（硬链，只读复用）')
    man.update(link_tree(O.P6.e6o_cache(), ('minute',), cd, 'E6o cache minute（硬链，只读复用）'))
    O.atomic_write_json(os.path.join(cd, 'cache_reuse_manifest.json'), man)
    O.log('硬链 %d 个文件' % len(man))
    pdir = os.path.join(cd, 'panels')
    tdir = os.path.join(cd, 'triggers')
    L = lambda k, d=pdir: np.load(os.path.join(d, k + '.npy'), mmap_mode='r')
    dates = np.load(os.path.join(pdir, 'dates.npy'))
    codes = np.load(os.path.join(pdir, 'codes.npy'))
    T, N = len(dates), len(codes)
    if str(dates[-1]) > O.CUTOFF:
        raise RuntimeError('面板末日晚于 cutoff')
    is_open = np.asarray(L('is_open')).astype(bool)
    # ---- UNION_T1a_T8（三值或）
    ta = np.asarray(L('T1a', tdir))
    t8 = np.asarray(L('T8_LIMIT_CLOSE', tdir))
    un = np.full((T, N), -1, np.int8)
    un[(ta == 0) & (t8 == 0)] = 0
    un[(ta == 1) | (t8 == 1)] = 1
    O.atomic_save_npy(os.path.join(tdir, 'UNION_T1a_T8.npy'), un)
    # ---- amihud20
    import e6o_panels as OP
    r = np.asarray(L('r_day'))
    amt = np.asarray(L('amt'))
    with np.errstate(all='ignore'):
        x = np.where(is_open & np.isfinite(r) & np.isfinite(amt) & (amt > 0), np.abs(r) / amt, np.nan)
    ami = OP.rolling_prev(x, 20, 10, 'mean')
    O.atomic_save_npy(os.path.join(pdir, 'amihud20.npy'), np.asarray(ami, np.float64))
    O.log('UNION_T1a_T8 / amihud20 落盘')
    # ---- 后复权 OHLC 与 EDGE
    import e6m_stage0_full as SF
    data, before, dcd = SF.load_full()
    close = data['close']
    if [str(d)[:10] for d in close.index] != list(dates) or [str(c) for c in close.columns] != list(codes):
        raise RuntimeError('日线轴与 E6p 面板轴不一致')
    g = lambda k: data[k].reindex(index=close.index, columns=close.columns).astype(float).to_numpy()
    adj = g('adj_factor')
    lc = g('lclose')
    craw = g('close')
    F = np.full((T, N), np.nan)
    cur = np.ones(N)
    last = np.full(N, np.nan)
    seen = np.zeros(N, bool)
    n_ca = 0
    n_lc_missing = 0
    for t in range(T):
        o = is_open[t]
        m = o & seen & np.isfinite(last) & np.isfinite(lc[t]) & (lc[t] > 0)
        n_lc_missing += int((o & seen & ~(np.isfinite(lc[t]) & (lc[t] > 0))).sum())
        ratio = last[m] / lc[t, m]
        n_ca += int((np.abs(ratio - 1.0) > 1e-6).sum())
        cur[m] = cur[m] * ratio
        F[t, o] = cur[o]
        seen |= o
        last = np.where(o & np.isfinite(craw[t]) & (craw[t] > 0), craw[t], last)
    if n_lc_missing:
        raise RuntimeError('lclose 在开盘格缺 %d 处：链式因子不可无缺口构造' % n_lc_missing)
    paths = []
    raw = {}
    for k in ('open', 'high', 'low', 'close'):
        v = g(k)
        raw[k] = v
        with np.errstate(all='ignore'):
            av = np.where(is_open & np.isfinite(v) & (v > 0), v * F, np.nan)
        p = os.path.join(pdir, '%s_adj.npy' % k)
        O.atomic_save_npy(p, av)
        paths.append(p)
    O.atomic_save_npy(os.path.join(pdir, 'lclose_chain_factor.npy'), F)
    del data
    tests = EG.selftest(a.ref_dir) if a.ref_dir else []
    if tests and not all(t[3] for t in tests):
        raise RuntimeError('EDGE 作者四例不符：%s' % tests)
    O.log('EDGE 作者四例 %s；开始面板（%d workers）' % ('PASS' if tests else '未跑', a.workers))
    t1 = time.time()
    ed, n_eval = EG.rolling_panel(tuple(paths), T, N, workers=a.workers)
    O.atomic_save_npy(os.path.join(pdir, 'edge21.npy'), ed)
    O.log('edge21 落盘：实算窗 %d，%.0f 秒' % (n_eval, time.time() - t1))
    # ---- 抽查（逐窗 / 逐格重算）
    rng = np.random.default_rng(20261023)
    fin = np.argwhere(np.isfinite(ed))
    pick = fin[rng.choice(len(fin), size=min(800, len(fin)), replace=False)]
    oa, ha, la, ca = (np.load(p, mmap_mode='r') for p in paths)
    worst = 0.0
    for t, j in pick:
        v = EG.edge(oa[t - EG.WINDOW:t, j], ha[t - EG.WINDOW:t, j], la[t - EG.WINDOW:t, j], ca[t - EG.WINDOW:t, j])
        worst = max(worst, abs(v - ed[t, j]) / max(abs(v), 1e-12))
    if worst > 1e-12:
        raise RuntimeError('edge21 抽查相对差 %g' % worst)
    nanpick = np.argwhere(~np.isfinite(ed[EG.WINDOW:]))
    nanpick = nanpick[rng.choice(len(nanpick), size=min(800, len(nanpick)), replace=False)]
    bad_nan = 0
    for t, j in nanpick:
        t = t + EG.WINDOW
        o_, h_, l_, c_ = oa[t - EG.WINDOW:t, j], ha[t - EG.WINDOW:t, j], la[t - EG.WINDOW:t, j], ca[t - EG.WINDOW:t, j]
        nc = int((np.isfinite(o_) & np.isfinite(h_) & np.isfinite(l_) & np.isfinite(c_)).sum())
        if nc >= EG.MIN_COMPLETE and np.isfinite(EG.edge(o_, h_, l_, c_)):
            bad_nan += 1
    if bad_nan:
        raise RuntimeError('edge21 缺失格抽查 %d 处应有值' % bad_nan)
    up = rng.integers(0, T, 2000), rng.integers(0, N, 2000)
    for t, j in zip(*up):
        a_, b_ = int(ta[t, j]), int(t8[t, j])
        e_ = 1 if (a_ == 1 or b_ == 1) else (0 if (a_ == 0 and b_ == 0) else -1)
        if e_ != int(un[t, j]):
            raise RuntimeError('UNION_T1a_T8 抽查不符')
    worst_a = 0.0
    for t, j in zip(*up):
        if t < 21:
            continue
        w = x[t - 20:t, j]
        w = w[np.isfinite(w)]
        e_ = w.mean() if len(w) >= 10 else np.nan
        g_ = ami[t, j]
        if np.isfinite(e_) != np.isfinite(g_):
            raise RuntimeError('amihud20 缺失口径不符')
        if np.isfinite(e_):
            worst_a = max(worst_a, abs(e_ - g_) / abs(e_))
    if worst_a > 1e-9:
        raise RuntimeError('amihud20 抽查相对差 %g' % worst_a)
    years = np.array([int(str(d)[:4]) for d in dates])
    facts = dict(T=int(T), N=int(N), reused_files=len(man), cache_dir=os.path.basename(cd),
                 union_t1a_t8=dict(true=int((un == 1).sum()), false=int((un == 0).sum()), unknown_open=int(((un < 0) & is_open).sum()),
                                   both_true=int(((ta == 1) & (t8 == 1)).sum()), t1a_true=int((ta == 1).sum()), t8_true=int((t8 == 1).sum())),
                 amihud20=dict(finite=int(np.isfinite(ami).sum()), open_cells=int(is_open.sum()), rule=O_AMIHUD_RULE, unit='1/CNY'),
                 edge21=dict(finite=int(np.isfinite(ed).sum()), windows_evaluated=int(n_eval), rule=O_EDGE_RULE, version=EG.VERSION, license=EG.LICENSE,
                             source=EG.SOURCE, author_tests=[dict(name=t[0], expected=t[1], got=t[2], ok=t[3]) for t in tests],
                             spot_checks=int(len(pick)), spot_max_abs_diff=worst, nan_spot_checks=int(len(nanpick)),
                             finite_by_year={int(y): int(np.isfinite(ed[years == y]).sum()) for y in sorted(set(years))}),
                 ohlc_complete_open_cells=int((is_open & np.isfinite(raw['open']) & np.isfinite(raw['high']) & np.isfinite(raw['low'])
                                               & np.isfinite(raw['close'])).sum()),
                 adj_factor_finite_open_cells=int((is_open & np.isfinite(adj) & (adj > 0)).sum()),
                 lclose_chain=dict(rule='F_t = F_prev * prev_open_day_raw_close / lclose_t on open days; first listed day F = 1',
                                   corporate_action_cells=int(n_ca), lclose_missing_open_cells=int(n_lc_missing),
                                   reason='adj_factor missing on 2-11% of open cells by year; lclose (same adjustment as r_day) covers 100%'),
                 wall_s=round(time.time() - t0, 1), rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.atomic_write_json(os.path.join(cd, 'cache_facts.json'), facts)
    outs = [os.path.join(cd, 'cache_facts.json'), os.path.join(cd, 'cache_reuse_manifest.json'), os.path.join(tdir, 'UNION_T1a_T8.npy'),
            os.path.join(pdir, 'amihud20.npy'), os.path.join(pdir, 'edge21.npy'), os.path.join(pdir, 'lclose_chain_factor.npy')] + paths
    O.write_receipt('E6q_cache', outs, code=[__file__, O.__file__, EG.__file__], **{k: v for k, v in facts.items() if k != 'edge21'})
    print(json.dumps({k: v for k, v in facts.items() if k not in ('edge21',)}, ensure_ascii=False), flush=True)
    print(json.dumps(dict(edge21={k: v for k, v in facts['edge21'].items() if k != 'finite_by_year'}), ensure_ascii=False), flush=True)


O_AMIHUD_RULE = 'T-20..T-1, >= 10 obs, |r_day| / amount, amount in CNY'
O_EDGE_RULE = '21 trading days ending T-1, >= 3 complete OHLC obs else missing'

if __name__ == '__main__':
    main()
