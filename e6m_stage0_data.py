# -*- coding: utf-8 -*-
"""E6m 阶段 N · N5 数据层 Stage 0（附录 A2-1 云机版 / A2-5 N / A4-1 / A4-5 / A4-6 / A6-1 / A6-2）。
只读：云机代码目录、resonance 缓存（命中即读、不写）、仓库 delivery/ 交付包（只读解包到工作目录）。
不计算任何前向收益或账户损益（阶段 N 不读收益，brief A6）。
云机适配（只改运行方式、不改语义；登记于 code_register）：data_loader.PATHS['cache_dir'] 在进程内指向 resonance 缓存目录
（47 同批文件）；运行前核所需缓存文件齐全（不触发回写），运行后核目录清单不变。
任务：
  seg   --seg <段>：源 e6j_prod.build_period / form_masks / weights_of / pool2_part / pool1_part 重建六形态；Q 源重算 kQ
        （e6j_features.b1 → C.precompute_neutralized_factor → 'lo' 秩）与中性化分支逐日计数；字段语义；耗时 / RSS。
  merge：四段拼接按源 pool2_bytes / pool1_bytes 成字节，对仓库交付包逐字节比对。"""
import e6j_boot  # noqa: F401  （先于 numpy / pandas）
import os
import sys
import json
import time
import pickle
import tarfile
import hashlib
import argparse
import resource
from types import SimpleNamespace

import numpy as np
import pandas as pd

import data_loader as DL
import e6m_core as M

FTL = ('flag_buy', 'flag_sell', 'flag_st_new', 'industry_zx_1_all', 'limitDownPrice', 'limitUpPrice')
TOL_LIMIT = 0.005                     # e6i_features.py:36（源常量，读源码转录；该模块云机 import 不起来）
DELIV_DIR = 'delivery/I11_candidate_pools_v2_20260903'
DELIV_TAR = 'I11_candidate_pools_v2_20260903.tar.gz'


def cache_dir():
    return os.path.join(os.path.dirname(os.path.dirname(M.CODE.rstrip('/'))), 'data', 'cache')


def listing(d):
    return sorted((f, os.path.getsize(os.path.join(d, f))) for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)))


def prep_cache(ps, pe):
    cd = cache_dir()
    need = ['daily_kline_%s_%s.parquet' % (ps, pe)] + ['ftl_%s.parquet' % x for x in FTL]
    miss = [f for f in need if not os.path.exists(os.path.join(cd, f))]
    if miss:
        raise RuntimeError('缓存缺件（不允许触发回写）：%s' % miss)
    DL.PATHS['cache_dir'] = cd
    return cd, listing(cd)


def rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 / 1024.0


def to_parquet_atomic(df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp.%d' % os.getpid()
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)


def kq_branches(raw_df, pool0, log_mcap):
    """逐日复刻 C.precompute_neutralized_factor（:315–331）与 neutralize_by_mcap（pool_screening_v2 :292–309）的分支（只计数，不改源）。"""
    rows = []
    for d in pool0.index:
        inp = pool0.loc[d] == 1
        n0 = int(inp.sum())
        if n0 < 6:
            rows.append(dict(date=str(d)[:10], n_pool0=n0, n_q_finite=0, branch='SKIP_POOL_LT6', n_out=0))
            continue
        st = pool0.columns[inp]
        f = raw_df.loc[d, st]
        m = log_mcap.loc[d, st]
        nboth = int((f.notna() & m.notna()).sum())
        if nboth < 10:
            br, nout = 'RAW_RETURNED_LT10', int(f.notna().sum())
        else:
            br, nout = 'OLS', nboth
        if nout < 6:
            br += '_THEN_SKIP_LT6'
        rows.append(dict(date=str(d)[:10], n_pool0=n0, n_q_finite=int(f.notna().sum()), branch=br, n_out=nout))
    return pd.DataFrame(rows)


def task_seg(pname, attempt):
    import e6j_prod as PR
    import e6j_slot as SL
    import e6j_features as EF
    import comprehensive_factor_diagnosis as C
    from event_study import PERIODS
    ps, pe = PERIODS[pname]
    M.assert_end_ok(pe, 'segment end')
    cd, before = prep_cache(ps, pe)
    T = {}
    t0 = time.time()
    cpk = M.P('tmp', 'ctx_%s.pkl' % pname)            # 源上下文落盘（去掉 feats / specs）：后续核验与重试复用，不交付
    if os.path.exists(cpk):
        with open(cpk, 'rb') as fh:
            ctx = pickle.load(fh)
        T['build_period_s'] = -1.0
        T['ctx_reused_from_pickle'] = True
        T['load_pickle_s'] = time.time() - t0
    else:
        ctx = PR.build_period(pname)
        T['build_period_s'] = time.time() - t0
        t0 = time.time()
        keep = {k: v for k, v in ctx.items() if k not in ('feats', 'specs')}
        with open(cpk + '.tmp', 'wb') as fh:
            pickle.dump(keep, fh, protocol=5)
        os.replace(cpk + '.tmp', cpk)
        T['pickle_ctx_s'] = time.time() - t0
        T['ctx_reused_from_pickle'] = False
    t0 = time.time()
    masks = PR.form_masks(ctx)
    T['form_masks_s'] = time.time() - t0
    pdir = M.P('stage0', 'c2_rebuild_parts', pname)
    t0 = time.time()
    wsum = {}
    for f in PR.DELIV:
        hold, w = PR.weights_of(ctx, masks[f])
        to_parquet_atomic(PR.pool2_part(ctx, w), os.path.join(pdir, 'pool2_%s.parquet' % PR.FNAME[f]))
        wsum[f] = w.sum(axis=1).to_numpy()
    T['dev_weights_6forms_s'] = time.time() - t0
    to_parquet_atomic(PR.pool1_part(ctx), os.path.join(pdir, 'pool1.parquet'))
    pool0, p0, log_mcap = ctx['pool0'], ctx['p0'], ctx['log_mcap']
    clean = ctx['clean'].reindex_like(pool0).fillna(0.0).to_numpy() == 1
    ind = ctx['industry']
    # A4-6：逐日人数 / 行业数 / size 分位
    lm = log_mcap.reindex_like(pool0).to_numpy()
    indv = ind.reindex_like(pool0).to_numpy() if ind is not None else None
    cnt = dict(date=[str(d)[:10] for d in pool0.index], n_pool0=p0.sum(1), n_clean=clean.sum(1))
    for f in PR.DELIV:
        cnt['n_' + f] = masks[f].sum(1)
        cnt['wsum_' + f] = np.round(wsum[f], 10)
    nind, q10, q50, q90 = [], [], [], []
    for t in range(p0.shape[0]):
        sel = p0[t]
        nind.append(int(pd.Series(indv[t, sel]).nunique(dropna=True)) if (indv is not None and sel.any()) else 0)
        v = lm[t, sel]
        v = v[np.isfinite(v)]
        q10.append(np.percentile(v, 10) if len(v) else np.nan)
        q50.append(np.percentile(v, 50) if len(v) else np.nan)
        q90.append(np.percentile(v, 90) if len(v) else np.nan)
    cnt.update(n_ind_pool0=nind, logmcap_p10_pool0=q10, logmcap_p50_pool0=q50, logmcap_p90_pool0=q90,
               n_E_cond=[len(ctx['neu_cond'].get(d, [])) for d in pool0.index])
    cdf = pd.DataFrame(cnt)
    M.atomic_write_csv(M.P('stage0', 'c2_cloud_rebuild_counts_%s.csv' % pname), cdf)
    # A2-5（N）：Q 源重算（e6j_features.b1 的 J_B1_qCC；x / d 的有效日按 e6i_features.Base :269–306 原式）
    t0 = time.time()
    data = ctx['data']
    close = data['close'].astype(float)
    g = lambda k: data[k].reindex(index=close.index, columns=close.columns).astype(float).to_numpy()
    is_open = (data['is_open'].reindex(index=close.index, columns=close.columns) == 1).to_numpy()
    o, h, l, c, lc = g('open'), g('high'), g('low'), g('close'), g('lclose')
    with np.errstate(all='ignore'):
        valid = is_open & (o > 0) & (h > 0) & (l > 0) & (c > 0) & (lc > 0)
        valid &= (l <= np.minimum(o, c) + 1e-9) & (h >= np.maximum(o, c) - 1e-9)
        r = np.where(valid, np.log(c / lc), np.nan)
    x = g('turnover_rate')
    x = np.where(is_open & np.isfinite(x) & (x >= 0), x, np.nan)
    d = np.abs(r)
    qcc = EF.b1(SimpleNamespace(x=x, d=d))['J_B1_qCC']
    raw_df = pd.DataFrame(qcc, index=close.index, columns=close.columns).reindex_like(pool0)
    neu = C.precompute_neutralized_factor(raw_df, pool0, log_mcap)
    kq = SL.pct_dir(neu, 'lo')
    br = kq_branches(raw_df, pool0, log_mcap)
    br['in_neu_cache'] = [dd in neu for dd in pool0.index]
    br['branch_consistent'] = br['in_neu_cache'] == ~br['branch'].str.contains('SKIP')
    M.atomic_write_csv(M.P('stage0', 'c4_data_kq_%s.csv' % pname), br)
    cc = SL.ccols_of(ctx)
    kq_dense = SL.dense(ctx, kq)
    M.atomic_write_npz(M.P('stage0', 'cache_cloud', 'kq_%s.npz' % pname), dates=np.array([str(x)[:10] for x in pool0.index]),
                       ccols=np.array([str(x) for x in pool0.columns[cc]]), q_raw=np.ascontiguousarray(raw_df.to_numpy()[:, cc]),
                       kq=kq_dense, status=np.array(['ANCHOR_PENDING']))
    T['kq_recompute_s'] = time.time() - t0
    # A4-1 字段语义（pool0 / 有效单元；只看形成日已知字段，不涉及前向收益）
    vp = valid & p0
    chg = g('change_pct')
    with np.errstate(all='ignore'):
        simple = c / lc - 1.0
        dfrac = np.abs(chg - simple)[vp]
        dpct = np.abs(chg - 100.0 * simple)[vp]
    unit_pct = bool(np.nanmedian(dpct) < np.nanmedian(dfrac))
    with np.errstate(all='ignore'):
        chg_frac = chg / 100.0 if unit_pct else chg
        dlog = np.abs(r - np.log1p(chg_frac))[vp]
    xo = x[vp]
    LU, LD = g('limit_up'), g('limit_down')
    known = np.isfinite(LU) & np.isfinite(LD)
    touch = known & ((h >= LU - TOL_LIMIT) | (l <= LD + TOL_LIMIT)) & valid
    one_word = touch & (h == l)
    st_flag = g('flag_st')
    closed = (~is_open)
    carry = closed & np.isfinite(c) & np.isfinite(lc) & (c > 0) & (c == lc)
    bse_cols = [cname for cname in close.columns if PR.is_bse(cname)]
    fields = [
        ('turnover_rate_median_pool0valid', float(np.nanmedian(xo))), ('turnover_rate_p99_pool0valid', float(np.nanpercentile(xo, 99))),
        ('turnover_rate_max_pool0valid', float(np.nanmax(xo))), ('turnover_rate_share_gt1_pool0valid', float(np.nanmean(xo > 1))),
        ('change_pct_absdiff_vs_fraction_p50', float(np.nanpercentile(dfrac, 50))), ('change_pct_absdiff_vs_fraction_p99', float(np.nanpercentile(dfrac, 99))),
        ('change_pct_absdiff_vs_fraction_max', float(np.nanmax(dfrac))), ('change_pct_absdiff_vs_percent_p50', float(np.nanpercentile(dpct, 50))),
        ('logret_vs_log1p_chg_absdiff_max', float(np.nanmax(dlog))), ('logret_vs_log1p_chg_share_le_1e-9', float(np.nanmean(dlog <= 1e-9))),
        ('closed_cells_share_all', float(closed.mean())), ('closed_cells_close_eq_lclose_share', float(carry.sum() / max(closed.sum(), 1))),
        ('limit_known_share_pool0valid', float(known[vp].mean())), ('limit_touch_share_pool0valid', float(touch[vp].mean())),
        ('one_word_share_pool0valid', float(one_word[vp].mean())), ('flag_st_eq1_share_pool0', float(np.nanmean(st_flag[p0] == 1))),
        ('change_pct_unit', 'percent' if unit_pct else 'fraction'),
        ('bse_columns_in_data', len(bse_cols)),
        ('bse_in_pool0_cells', int(p0[:, [pool0.columns.get_loc(b) for b in bse_cols if b in pool0.columns]].sum()) if bse_cols else 0),
        ('valid_share_pool0', float(valid[p0].mean())), ('d_true_zero_share_pool0valid', float(np.mean(d[vp] == 0))),
        ('d_lt_eps_share_pool0valid', float(np.mean(d[vp] < 1e-4))), ('pool0_cells', int(p0.sum())), ('dates', int(p0.shape[0])),
    ]
    # A4-5 复权同源：源 C.adjust_factor（lclose 链，收益正式口径）与 adj_factor 列（e6l_state Trend 用）两端点有限份额
    A = C.adjust_factor(data).reindex(index=close.index, columns=close.columns).to_numpy()
    adjc = np.where(np.isfinite(c * A) & (c * A > 0), c * A, np.nan)
    af = g('adj_factor')
    adjf = np.where(np.isfinite(c * af) & (c * af > 0), c * af, np.nan)
    for tag, X in (('lclose_chain', adjc), ('adj_factor_col', adjf)):
        e1 = np.full_like(X, np.nan)
        e1[1:] = X[:-1]
        e21 = np.full_like(X, np.nan)
        e21[21:] = X[:-21]
        ok = np.isfinite(e1) & np.isfinite(e21)
        ma = pd.DataFrame(X).rolling(20, min_periods=16).mean().shift(1).to_numpy()
        fields += [('pre_r20_endpoints_finite_share_pool0_%s' % tag, float(ok[p0].mean())),
                   ('ma20_ge16_finite_share_pool0_%s' % tag, float(np.isfinite(ma)[p0].mean()))]
    with np.errstate(all='ignore'):
        both = np.isfinite(adjc) & np.isfinite(adjf)
        ra = adjc[1:] / adjc[:-1] - 1.0
        rb = adjf[1:] / adjf[:-1] - 1.0
        agree = np.abs(ra - rb)[(both[1:] & both[:-1]) & p0[1:]]
    fields += [('adj_two_sources_daily_ret_absdiff_p99_pool0', float(np.nanpercentile(agree, 99)) if agree.size else np.nan),
               ('adj_two_sources_daily_ret_absdiff_max_pool0', float(np.nanmax(agree)) if agree.size else np.nan),
               ('adj_factor_col_nan_share_valid', float(np.mean(~np.isfinite(af[valid]))))]
    M.atomic_write_csv(M.P('stage0', 'c4_data_fields_%s.csv' % pname), pd.DataFrame(fields, columns=['metric', 'value']))
    rng = M.rng_for('E6m', 'A4-1 samples', pname)
    ii, jj = np.nonzero(vp)
    pick = rng.choice(len(ii), size=min(8, len(ii)), replace=False)
    smp = pd.DataFrame(dict(date=[str(close.index[i])[:10] for i in ii[pick]], ticker=[str(close.columns[j]) for j in jj[pick]],
                            open=o[ii[pick], jj[pick]], high=h[ii[pick], jj[pick]], low=l[ii[pick], jj[pick]], close=c[ii[pick], jj[pick]],
                            lclose=lc[ii[pick], jj[pick]], turnover_rate=x[ii[pick], jj[pick]], change_pct=chg[ii[pick], jj[pick]],
                            log_c_lclose=r[ii[pick], jj[pick]], is_open=is_open[ii[pick], jj[pick]].astype(int)))
    M.atomic_write_csv(M.P('stage0', 'c4_data_samples_%s.csv' % pname), smp)
    after = listing(cd)
    T['cache_dir_unchanged'] = before == after
    T['rss_peak_gb'] = round(rss_gb(), 2)
    T['n_dates'] = int(p0.shape[0])
    T['n_columns'] = int(p0.shape[1])
    T['pool0_cells'] = int(p0.sum())
    tm = pd.DataFrame([dict(segment=pname, attempt=attempt, item=k, value=v) for k, v in T.items()])
    M.atomic_write_csv(M.P('stage0', 'c6_timing_cloud_%s.csv' % pname), tm)
    outs = [M.P('stage0', f) for f in ('c2_cloud_rebuild_counts_%s.csv' % pname, 'c4_data_kq_%s.csv' % pname, 'c4_data_fields_%s.csv' % pname,
                                       'c4_data_samples_%s.csv' % pname, 'c6_timing_cloud_%s.csv' % pname)]
    outs += [os.path.join(pdir, f) for f in sorted(os.listdir(pdir))] + [M.P('stage0', 'cache_cloud', 'kq_%s.npz' % pname)]
    ok = T['cache_dir_unchanged']
    M.write_receipt('stage0_N5_seg_%s_%s' % (pname, attempt), outs, status='SUCCEEDED' if ok else 'FAILED', code=[__file__, M.__file__],
                    timing=T, cloud_adaptation="data_loader.PATHS['cache_dir'] → resonance 缓存目录（进程内）")
    print(json.dumps(dict(seg=pname, **{k: (round(v, 1) if isinstance(v, float) else v) for k, v in T.items()}), ensure_ascii=False), flush=True)
    return 0 if ok else 1


def task_merge(attempt):
    import e6j_prod as PR
    from event_study import PERIODS
    src = os.path.join(M.CODE, DELIV_DIR)
    tgz = os.path.join(src, DELIV_TAR)
    ad = M.P('stage0', 'anchor_repo_delivery')
    os.makedirs(ad, exist_ok=True)
    with tarfile.open(tgz, 'r:gz') as tf:
        for m in tf.getmembers():
            nm = os.path.basename(m.name)
            dst = os.path.join(ad, nm)
            if m.isfile() and nm.endswith('.csv') and not os.path.exists(dst):      # 只取常规 csv 文件，按文件名落位（不信任包内路径）
                with tf.extractfile(m) as fh, open(dst + '.tmp', 'wb') as out:
                    out.write(fh.read())
                os.replace(dst + '.tmp', dst)
    stats = pd.read_csv(os.path.join(src, '_delivery_stats.csv'))
    rows = []
    segs = list(PERIODS.keys())
    for f in PR.DELIV:
        fn = 'pool2_%s.csv' % PR.FNAME[f]
        parts = [pd.read_parquet(M.P('stage0', 'c2_rebuild_parts', s, 'pool2_%s.parquet' % PR.FNAME[f])) for s in segs]
        b, dfp = PR.pool2_bytes(parts)
        ref = open(os.path.join(ad, fn), 'rb').read()
        st = stats[stats.file == fn]
        rows.append(dict(file=fn, rows_rebuild=len(dfp), rows_delivery=int(st.rows.iloc[0]) if len(st) else -1, bytes_rebuild=len(b), bytes_delivery=len(ref),
                         sha256_rebuild=hashlib.sha256(b).hexdigest(), sha256_delivery=hashlib.sha256(ref).hexdigest(),
                         status='PASS' if b == ref else 'FAIL'))
        if b != ref:
            M.atomic_write_bytes(M.P('stage0', 'c2_rebuild_mismatch_%s' % fn), b)
    p1parts = [pd.read_parquet(M.P('stage0', 'c2_rebuild_parts', s, 'pool1.parquet')) for s in segs]
    b1, dfp1 = PR.pool1_bytes(p1parts)
    ref1 = open(os.path.join(ad, 'pool1_I11_screening.csv'), 'rb').read()
    rows.append(dict(file='pool1_I11_screening.csv', rows_rebuild=len(dfp1), rows_delivery=-1, bytes_rebuild=len(b1), bytes_delivery=len(ref1),
                     sha256_rebuild=hashlib.sha256(b1).hexdigest(), sha256_delivery=hashlib.sha256(ref1).hexdigest(),
                     status='PASS' if (b1 == ref1 and hashlib.md5(b1).hexdigest() == PR.POOL1_MD5) else 'FAIL'))
    df = pd.DataFrame(rows)
    df['anchor_source'] = 'repo %s/%s（git 跟踪，sha256 %s）' % (DELIV_DIR, DELIV_TAR, M.sha_file(tgz)[:16])
    df['formal_A2_1'] = 'SOURCE_WAIT（E5a 结果目录副本未到；本行为仓库交付包的同名文件）'
    M.atomic_write_csv(M.P('stage0', 'c2_cloud_rebuild_anchor_%s.csv' % attempt), df)
    ok = (df.status == 'PASS').all()
    M.write_receipt('stage0_N5_merge_%s' % attempt, [M.P('stage0', 'c2_cloud_rebuild_anchor_%s.csv' % attempt)], status='SUCCEEDED' if ok else 'FAILED',
                    inputs=[tgz], code=[__file__, M.__file__], passed=int((df.status == 'PASS').sum()), files=len(df))
    print(df[['file', 'rows_rebuild', 'rows_delivery', 'status']].to_string(index=False), flush=True)
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--task', required=True, choices=['seg', 'merge'])
    ap.add_argument('--seg', default='')
    ap.add_argument('--attempt', default='a1')
    a = ap.parse_args()
    if a.task == 'seg':
        return task_seg(a.seg, a.attempt)
    return task_merge(a.attempt)


if __name__ == '__main__':
    sys.exit(main())
