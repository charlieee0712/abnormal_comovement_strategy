# -*- coding: utf-8 -*-
"""E6r 缓存命名空间（brief §7 / §1.2 / C6 / C7；目录名含 E6r-v1.1 与 c89305fb，闭包门 ㉑；v1.0 缓存不复用；E6q / E6i 只读）。
1. E6q 缓存 panels / triggers / source / minute 逐文件硬链（只读复用；sha 清单 cache_reuse_manifest.json）；
2. 新触发 UNION_LEVEL_T8 = T1b_LEVEL ∨ T8_LIMIT_CLOSE 三值或（与 E6q UNION_T1a_T8 同式：任一已知真 → 1；两者已知假 → 0；否则 −1 = UNKNOWN）；
3. 新面板：
   - cvr20 = E6i C_CVR20_LEGACY__OBS（= 源 features_daily.py A3 块 CVR_20d = ((close − vwap) / vwap).rolling(20, min_periods=10).mean()）四段拼全程网格；
     研究 CVR20_risk 原值（高 = 坏），T0 收盘可得；
   - e6r_cvr5/cvr5 = 同一源函数块 CVR_5d = rolling(5, min_periods=3)（E6i C_CVR5_LEGACY__OBS）四段拼全程网格（新派生目录，不覆盖 E6i）；
     绑定核：各段第 ≥ 20 行用 E6i C_cvr1_LEGACY（源 CVR 日值）重算 rolling(5, 3) 与 rolling(20, 10) 逐格比对（max 相对差、缺失口径一致）；
   - seckey = int(sha256(code)[:15], 16)（随机优先序用证券稳定键，不用列号）。
4. source15/<段>.npz：源 DEV（e6i_sparse.SparseEngine.dev 逐式：w0 = min(1/n, MAX_STOCK)；行业和 = 同值 w0 顺序累加；超限行业 w = w0·cap/gs）
   单股参数 .01 → .015（UNIFORM_CAP15，用户 #15 研究维度）；先以 .01 在 18 组合 × 4 段上逐位复现 fm_w，证明面板 ind / ind_share + .03 = 源 icodes / cap。
不读策略收益。用法：python3 e6r_cache.py"""
import os
import json
import time
import hashlib
import resource

import numpy as np
import pandas as pd

import e6r_core as O

E6I_CACHE = os.path.join(O.E6I_DIR, 'cache')


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


def e6i_to_grid(name, dates, codes, src):
    """E6i 段内测量（形状 = 源段 dates × codes）→ 全程网格；返回 (面板, {段: sha256})。"""
    X = np.full((len(dates), len(codes)), np.nan)
    di_all = {d: i for i, d in enumerate(dates)}
    cj = {c: j for j, c in enumerate(codes)}
    shas = {}
    for s in O.SEGS:
        p = os.path.join(E6I_CACHE, s, name + '__OBS.npy')
        a = np.load(p)
        z = src[s]
        di = np.array([di_all[str(d)] for d in z['dates']])
        cc = np.array([cj[str(c)] for c in z['codes']])
        if a.shape != (len(di), len(cc)):
            raise RuntimeError('E6i %s %s 形状 %s ≠ 源 %s' % (name, s, a.shape, (len(di), len(cc))))
        X[np.ix_(di, cc)] = a
        shas[s] = O.sha_file(p)
    return X, shas


def roll_mean(x, w, mp):
    return pd.DataFrame(x).rolling(w, min_periods=mp).mean().to_numpy()


def dev_weights(t, c, ic, cap, max_stock, T):
    """e6i_sparse.SparseEngine.dev 逐式（参数化单股上限）：(t, c) 段内单元 → 同序 DEV 权重。"""
    if len(t) == 0:
        return np.zeros(0)
    n_t = np.bincount(t, minlength=T)
    n = n_t[t]
    w0 = np.minimum(1.0 / n, max_stock)
    icv = ic[t, c]
    v = icv >= 0
    w = w0.copy()
    if v.any():
        G = int(ic.max()) + 1
        tv, iv = t[v], icv[v]
        key = tv * G + iv
        cnt = np.bincount(key, minlength=T * G)
        nmax = int(n.max())
        tab = np.zeros((nmax + 1, nmax + 1))
        for k in range(1, nmax + 1):
            tab[k, 1:k + 1] = np.cumsum(np.full(k, min(1.0 / k, max_stock)))
        gs = tab[n[v], cnt[key]]
        capv = cap[tv, iv]
        over = gs > capv
        wv = w0[v]
        with np.errstate(divide='ignore', invalid='ignore'):
            w[v] = np.where(over, wv * (capv / gs), wv)
    return w


def main():
    t0 = time.time()
    cd = O.cache_dir()
    if 'E6r-v1.1' not in cd or 'c89305fb' not in cd:
        raise RuntimeError('缓存命名空间不含 E6r-v1.1 / c89305fb')
    man = link_tree(O.E6Q_CACHE, ('panels', 'triggers', 'source', 'minute'), cd, 'E6q cache（硬链，只读复用）')
    O.atomic_write_json(os.path.join(cd, 'cache_reuse_manifest.json'), man)
    O.log('硬链 %d 个文件' % len(man))
    pdir = os.path.join(cd, 'panels')
    tdir = os.path.join(cd, 'triggers')
    L = lambda k, d=pdir: np.load(os.path.join(d, k + '.npy'), mmap_mode='r')
    dates = [str(x) for x in np.load(os.path.join(pdir, 'dates.npy'))]
    codes = [str(x) for x in np.load(os.path.join(pdir, 'codes.npy'))]
    T, N = len(dates), len(codes)
    if dates[-1] > O.CUTOFF:
        raise RuntimeError('面板末日晚于 cutoff')
    facts = dict(T=T, N=N, reused_files=len(man), cache_dir=os.path.basename(cd))
    # ---- UNION_LEVEL_T8（三值或，与 E6q UNION_T1a_T8 同式）
    lv = np.asarray(L('T1b_LEVEL', tdir))
    t8 = np.asarray(L('T8_LIMIT_CLOSE', tdir))
    un = np.full((T, N), -1, np.int8)
    un[(lv == 0) & (t8 == 0)] = 0
    un[(lv == 1) | (t8 == 1)] = 1
    O.atomic_save_npy(os.path.join(tdir, 'UNION_LEVEL_T8.npy'), un)
    rng = np.random.default_rng(20261024)
    up = rng.integers(0, T, 4000), rng.integers(0, N, 4000)
    for t, j in zip(*up):
        a_, b_ = int(lv[t, j]), int(t8[t, j])
        e_ = 1 if (a_ == 1 or b_ == 1) else (0 if (a_ == 0 and b_ == 0) else -1)
        if e_ != int(un[t, j]):
            raise RuntimeError('UNION_LEVEL_T8 抽查不符')
    is_open = np.asarray(L('is_open')).astype(bool)
    facts['union_level_t8'] = dict(true=int((un == 1).sum()), false=int((un == 0).sum()), unknown_open=int(((un < 0) & is_open).sum()),
                                   both_true=int(((lv == 1) & (t8 == 1)).sum()), level_true=int((lv == 1).sum()), t8_true=int((t8 == 1).sum()),
                                   rule='1 if LEVEL==1 or T8==1; 0 if both known 0; else -1 (UNKNOWN); same as E6q UNION_T1a_T8', spot_checks=4000)
    O.log('UNION_LEVEL_T8 落盘')
    # ---- CVR20 / CVR5（E6i 物化的源特征 → 全程网格）+ 公式绑定核
    src = {s: np.load(os.path.join(cd, 'source', '%s.npz' % s), allow_pickle=False) for s in O.SEGS}
    cv20, sh20 = e6i_to_grid('C_CVR20_LEGACY', dates, codes, src)
    cv5, sh5 = e6i_to_grid('C_CVR5_LEGACY', dates, codes, src)
    O.atomic_save_npy(os.path.join(pdir, 'cvr20.npy'), cv20)
    os.makedirs(os.path.join(cd, 'e6r_cvr5'), exist_ok=True)
    O.atomic_save_npy(os.path.join(cd, 'e6r_cvr5', 'cvr5.npy'), cv5)
    chk = {}
    for s in O.SEGS:
        a1 = np.load(os.path.join(E6I_CACHE, s, 'C_cvr1_LEGACY__OBS.npy'))
        a5 = np.load(os.path.join(E6I_CACHE, s, 'C_CVR5_LEGACY__OBS.npy'))
        a20 = np.load(os.path.join(E6I_CACHE, s, 'C_CVR20_LEGACY__OBS.npy'))
        r5 = roll_mean(a1, 5, 3)
        r20 = roll_mean(a1, 20, 10)
        res = {}
        for nm, ref, rec in (('CVR_5d', a5, r5), ('CVR_20d', a20, r20)):
            ref_i, rec_i = ref[20:], rec[20:]
            fa, fb = np.isfinite(ref_i), np.isfinite(rec_i)
            both = fa & fb
            with np.errstate(all='ignore'):
                rd = np.abs(ref_i[both] - rec_i[both]) / np.maximum(np.abs(ref_i[both]), 1e-12)
            res[nm] = dict(cells=int(both.sum()), max_rel_diff=float(rd.max()) if both.any() else 0.0,
                           nan_pattern_mismatch=int((fa != fb).sum()), rows_checked=int(ref_i.shape[0]))
        chk[s] = res
    facts['cvr_binding'] = dict(cvr20_source='features_daily.py A3: CVR_20d = ((close-vwap)/vwap).rolling(20, min_periods=10).mean() (E6i C_CVR20_LEGACY)',
                                cvr5_source='features_daily.py A3: CVR_5d = ((close-vwap)/vwap).rolling(5, min_periods=3).mean() (E6i C_CVR5_LEGACY)',
                                e6i_sha_cvr20=sh20, e6i_sha_cvr5=sh5, recompute_check=chk,
                                finite_cvr20=int(np.isfinite(cv20).sum()), finite_cvr5=int(np.isfinite(cv5).sum()))
    worst = max(v['max_rel_diff'] for s in chk for v in chk[s].values())
    nanm = sum(v['nan_pattern_mismatch'] for s in chk for v in chk[s].values())
    O.log('CVR20 / CVR5 落盘；段内重算 max 相对差 %.3g、缺失口径不一致格 %d' % (worst, nanm))
    # ---- 证券稳定键
    seck = np.array([int(hashlib.sha256(c.encode()).hexdigest()[:15], 16) for c in codes], np.int64)
    if len(set(seck.tolist())) != N:
        raise RuntimeError('证券稳定键冲突')
    O.atomic_save_npy(os.path.join(pdir, 'seckey.npy'), seck)
    # ---- 源 DEV .015（先 .01 逐位复现 fm_w）
    ind = np.asarray(L('ind'))
    capsh = np.asarray(L('ind_share'))
    di_all = {d: i for i, d in enumerate(dates)}
    cj = {c: j for j, c in enumerate(codes)}
    os.makedirs(os.path.join(cd, 'source15'), exist_ok=True)
    rep = []
    for s in O.SEGS:
        z = src[s]
        dd = np.array([di_all[str(d)] for d in z['dates']])
        cc = np.array([cj[str(c)] for c in z['codes']])
        Ts = len(dd)
        ic = ind[np.ix_(dd, cc)].astype(np.int64)
        G = int(ind.max()) + 1
        cap = np.zeros((Ts, G))
        cap[:, :] = capsh[dd, :G] + O.IND_DEV
        out = {}
        for f in O.FORMS:
            for m in O.MEMS:
                k = '%s|%s' % (f, m)
                t_ = z['fm_t|' + k].astype(np.int64)
                c_ = z['fm_c|' + k].astype(np.int64)
                w_ = z['fm_w|' + k].astype(np.float64)
                w01 = dev_weights(t_, c_, ic, cap, O.STOCK_CAP, Ts)
                same = bool(np.array_equal(w01, w_))
                mx = float(np.max(np.abs(w01 - w_))) if len(w_) else 0.0
                w15 = dev_weights(t_, c_, ic, cap, O.RESEARCH_CAP, Ts)
                sw = np.bincount(t_, weights=w_, minlength=Ts)
                sw15 = np.bincount(t_, weights=w15, minlength=Ts)
                live = sw > 0
                rep.append(dict(segment=s, form=f, memory=m, n=len(w_), bitwise_equal_010=same, max_abs_diff_010=mx,
                                mean_g_010=float(sw[live].mean()) if live.any() else 0.0, mean_g_015=float(sw15[live].mean()) if live.any() else 0.0,
                                share_cap_bound_010=float(np.mean(np.isclose(w_, O.STOCK_CAP, rtol=0, atol=1e-15))) if len(w_) else 0.0,
                                share_cap_bound_015=float(np.mean(np.isclose(w15, O.RESEARCH_CAP, rtol=0, atol=1e-15))) if len(w15) else 0.0))
                out['fm_w15|' + k] = w15
        O.atomic_write_npz(os.path.join(cd, 'source15', '%s.npz' % s), **out)
    R = pd.DataFrame(rep)
    O.atomic_write_csv(os.path.join(cd, 'source15', 'dev015_replication.csv'), R)
    nbad = int((~R.bitwise_equal_010.astype(bool)).sum())
    facts['dev015'] = dict(rule='w0 = min(1/n, MAX_STOCK); industry sum by sequential accumulation; over-cap industry w = w0*cap/gs; cap = ind_share + .03',
                           combos=len(R), bitwise_equal_010=int(R.bitwise_equal_010.astype(bool).sum()), not_equal=nbad,
                           max_abs_diff_010=float(R.max_abs_diff_010.max()), mean_g_010=float(R.mean_g_010.mean()), mean_g_015=float(R.mean_g_015.mean()))
    if nbad:
        O.log('警告：DEV .01 逐位复现不符 %d 组（见 dev015_replication.csv）' % nbad)
    facts['wall_s'] = round(time.time() - t0, 1)
    facts['rss_peak_gb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2)
    O.atomic_write_json(os.path.join(cd, 'cache_facts.json'), facts)
    outs = [os.path.join(cd, 'cache_facts.json'), os.path.join(cd, 'cache_reuse_manifest.json'), os.path.join(tdir, 'UNION_LEVEL_T8.npy'),
            os.path.join(pdir, 'cvr20.npy'), os.path.join(cd, 'e6r_cvr5', 'cvr5.npy'), os.path.join(pdir, 'seckey.npy'),
            os.path.join(cd, 'source15', 'dev015_replication.csv')] + [os.path.join(cd, 'source15', '%s.npz' % s) for s in O.SEGS]
    O.write_receipt('E6r_cache', outs, code=[__file__, O.__file__], **{k: v for k, v in facts.items() if k not in ('cvr_binding',)})
    print(json.dumps({k: v for k, v in facts.items() if k != 'cvr_binding'}, ensure_ascii=False), flush=True)
    print(json.dumps(dict(cvr_check_worst=worst, cvr_nan_mismatch=nanm), ensure_ascii=False), flush=True)
    if nbad:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
