# -*- coding: utf-8 -*-
"""E6j supplement_1（事后口径，VERIFY_brief §6 S1 / S3 / S4 的逐段计算；一段一个进程）。
只读已封存 P 账户（masks_<形态>.npz、<形态>.npz、summary.csv）；目标权重用本轮生产路径 DEV（env.SE.dev，与 assign_weights_dev 逐位同）。
不写 accounts/ 与 results_P 根目录；产物写 results_P/supplement_1/seg/<段>/。
  S1  四层 size 暴露：(a) pool0 层分布；(b) 编辑层 gap_t（= e6j_run_p.size_gap 同式，逐日）；(c) 最终名单等权 size 百分位均值；
      (d) 实际权重层：Σw·pct/Σw（形成日目标权重）与 H5 滚动持仓 act_t = Σ_{k<min(t+1,5)} W_{t−k}/min(t+1,5) 的同式（pct 用当日 clean 域秩）；
      小盘（pct ≤ .3）/ 大盘（pct > .7）权重份额；子 − 母逐日差的逐段 mean_t、sd_t（百分位点）。
  S3  d_t（子 − 母 8bp 日配对，P 账本 H5）对 SMB_t 回归：SMB = 前一日流通市值五分组等权最小组 − 最大组 当日 vwap 日收益（源 vwap_daily_return 同口径），
      universe = 前一日 clean 域（全市场）/ 前一日 pool0；α（×252×100）、β、HAC(Bartlett, L=5) SE、R²、n；母体 C0 net8 对 SMB 的 β。
  S4  size 五分组当"行业"：bench share_b = 当日 clean 域在该组的数量份额（同 bench_industry_shares）；dev_b = Σ_{i∈b} w_i − share_b（源 DEV 口径：未归一目标权重，
      只超配受 +3% 约束）与归一版 Σw_b/Σw − share_b；另逐日核个股 w ≤ 1% 与行业 Σw ≤ share + 3%。"""
import e6j_boot  # noqa: F401
import os
import sys
import time

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_prod as P
import e6j_engine as EN
import e6e_core as K
import comprehensive_factor_diagnosis as C

ACC = os.path.join(J.RES, 'accounts', 'P')
OUT = os.path.join(J.RES, 'results_P', 'supplement_1', 'seg')
MAIN = ('S', 'M', 'SM', 'C1')
H = 5


def dense_pct(S):
    mc = S.data['mcap'].astype(float).reindex(index=S.pool0.index, columns=S.pool0.columns)
    cl = S.clean.reindex(index=S.pool0.index, columns=S.pool0.columns).fillna(0) == 1
    return mc.where(cl).rank(axis=1, pct=True).values                # (T, Nfull)，clean 域逐日升序秩


def wmean(T, t, w, x):
    f = np.isfinite(x)
    num = np.bincount(t[f], weights=(w * x)[f], minlength=T); den = np.bincount(t[f], weights=w[f], minlength=T)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(den > 0, num / den, np.nan)


def seg_stats(diff):
    f = np.isfinite(diff)
    return (float(np.mean(diff[f])) * 100 if f.any() else np.nan, float(np.std(diff[f], ddof=1)) * 100 if f.sum() > 1 else np.nan, int(f.sum()))


def hac_ols(y, x, L=5):
    f = np.isfinite(y) & np.isfinite(x)
    y, x = y[f], x[f]
    n = len(y)
    if n < 20:
        return dict(alpha=np.nan, beta=np.nan, se_alpha=np.nan, se_beta=np.nan, r2=np.nan, n=n)
    X = np.column_stack([np.ones(n), x])
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    e = y - X @ b
    Xe = X * e[:, None]
    Sm = Xe.T @ Xe
    for l in range(1, L + 1):
        w = 1.0 - l / (L + 1.0)
        G = Xe[l:].T @ Xe[:-l]
        Sm += w * (G + G.T)
    V = XtX_inv @ Sm @ XtX_inv
    r2 = 1.0 - float(e @ e) / float(((y - y.mean()) ** 2).sum()) if n > 1 else np.nan
    return dict(alpha=float(b[0]), beta=float(b[1]), se_alpha=float(np.sqrt(V[0, 0])), se_beta=float(np.sqrt(V[1, 1])), r2=r2, n=n)


def smb_series(S, universe):
    """universe: (T, Nfull) bool（前一日域）；返回 SMB_t（小 − 大）与五分组日均成员数。"""
    dr = C.vwap_daily_return(S.data, K.ADJUST).reindex(index=S.pool0.index, columns=S.pool0.columns).values
    mc = S.data['mcap'].astype(float).reindex(index=S.pool0.index, columns=S.pool0.columns).values
    T = S.T
    smb = np.full(T, np.nan); mem = []
    for t in range(1, T):
        u = universe[t - 1] & np.isfinite(mc[t - 1]) & np.isfinite(dr[t])
        idx = np.flatnonzero(u)
        if len(idx) < 50:
            continue
        r = pd.Series(mc[t - 1, idx]).rank(pct=True, method='first').values
        q = np.minimum((r * 5 - 1e-12).astype(int), 4)
        m0, m4 = q == 0, q == 4
        smb[t] = dr[t, idx[m0]].mean() - dr[t, idx[m4]].mean()
        mem.append(np.bincount(q, minlength=5))
    return smb, (np.mean(mem, axis=0) if mem else np.full(5, np.nan))


def run(pname):
    t0 = time.time()
    env = EN.Env(pname, with_prod=False)
    S, ci, SE = env.S, env.ci, env.SE
    T, Nc = ci.T, ci.Nc
    cc = np.asarray(S.ccols)
    PCT = dense_pct(S)[:, cc]                                     # (T, Nc)
    cell_pct = PCT[ci.t, ci.c]
    od = os.path.join(OUT, pname); os.makedirs(od, exist_ok=True)
    rows, dev_rows, reg_rows, st_rows, gap_rows, pool_rows = [], [], [], [], [], []
    # ---- (a) pool0 层分布（子母相同，只给分布）
    p0 = S.p0c
    for q, lab in ((None, 'mean'), (.1, 'q10'), (.5, 'q50'), (.9, 'q90')):
        v = np.where(p0, PCT, np.nan)
        s = np.nanmean(v, axis=1) if q is None else np.nanquantile(v, q, axis=1)
        pool_rows.append(dict(segment=pname, stat=lab, pool0_size_pct_mean_over_days=float(np.nanmean(s)) * 100))
    # size 五分组（clean 域，当日）与 bench 份额
    clean_c = (S.clean.reindex(index=S.pool0.index, columns=S.pool0.columns).fillna(0).values == 1)
    Pfull = dense_pct(S)
    bfull = np.where(np.isfinite(Pfull), np.minimum(np.ceil(Pfull * 5) - 1, 4), -1).astype(int)
    share = np.zeros((T, 5))
    for t in range(T):
        b = bfull[t][clean_c[t] & (bfull[t] >= 0)]
        if len(b):
            share[t] = np.bincount(b, minlength=5) / len(b)
    bcell = np.where(np.isfinite(PCT), np.minimum(np.ceil(PCT * 5) - 1, 4), -1).astype(int)
    # ---- S3 SMB
    smb_all, mem_all = smb_series(S, clean_c)
    smb_p0, mem_p0 = smb_series(S, (S.pool0.values == 1))
    st_rows.append(dict(segment=pname, universe='clean_full', days=int(np.isfinite(smb_all).sum()), **{'members_q%d' % (i + 1): float(m) for i, m in enumerate(mem_all)},
                        smb_mean_ann=float(np.nanmean(smb_all)) * J.ANN))
    st_rows.append(dict(segment=pname, universe='pool0', days=int(np.isfinite(smb_p0).sum()), **{'members_q%d' % (i + 1): float(m) for i, m in enumerate(mem_p0)},
                        smb_mean_ann=float(np.nanmean(smb_p0)) * J.ANN))
    summ = pd.read_csv(os.path.join(ACC, pname, 'summary.csv'))
    for form in P.DELIV:
        z = np.load(os.path.join(ACC, pname, 'masks_%s.npz' % form), allow_pickle=False)
        keys = [str(x) for x in z['rows']]
        n = int(z['n'][0]); assert n == ci.n, (n, ci.n)
        M = np.unpackbits(z['bits'], axis=1, count=n).astype(bool)
        acc = np.load(os.path.join(ACC, pname, '%s.npz' % form), allow_pickle=False)
        desc = [str(x) for x in acc['desc']]
        net = acc['net8']

        def lay(mask, holdings):
            t, c = ci.t[mask], ci.c[mask]; w = SE.dev(t, c); x = cell_pct[mask]
            out = dict(t=t, c=c, w=w)
            out['tw'] = wmean(T, t, w, x)                                        # (d) 目标权重层
            out['names'] = wmean(T, t, np.ones(len(t)), x)                        # (c) 名单等权
            out['small'] = wmean(T, t, w, (x <= .3).astype(float) + np.where(np.isfinite(x), 0, np.nan))
            out['large'] = wmean(T, t, w, (x > .7).astype(float) + np.where(np.isfinite(x), 0, np.nan))
            if holdings:
                W = np.zeros((T, Nc)); W[t, c] = w
                cs = np.cumsum(W, axis=0); A = cs.copy(); A[H:] -= cs[:-H]
                A /= np.minimum(np.arange(1, T + 1), H)[:, None]
                with np.errstate(invalid='ignore', divide='ignore'):
                    num = np.nansum(A * np.where(np.isfinite(PCT), PCT, 0.0), axis=1); den = np.sum(A * np.isfinite(PCT), axis=1)
                    out['hold'] = np.where(den > 0, num / den, np.nan)
            # S4
            wb = np.zeros((T, 5)); ok = bcell[t, c] >= 0
            np.add.at(wb, (t[ok], bcell[t, c][ok]), w[ok])
            ws = np.bincount(t, weights=w, minlength=T)
            has = ws > 0
            dev = np.where(has[:, None], wb - share, np.nan)
            with np.errstate(invalid='ignore', divide='ignore'):
                devn = np.where(has[:, None], wb / ws[:, None] - share, np.nan)
            out['dev'], out['devn'] = dev, devn
            # DEV 约束核对
            ic = S.icodes[t, c]; g = ic >= 0
            wi = np.zeros((T, S.G)); np.add.at(wi, (t[g], ic[g]), w[g])
            out['stock_max'] = float(w.max()) if len(w) else np.nan
            out['ind_excess_max'] = float(np.max(np.where(wi > 0, wi - S.cap, -np.inf))) if len(w) else np.nan
            return out
        base = lay(M[keys.index('C0|0.0')], True)
        pdesc = 'P|%s|C0|-|-|a=0|H%d' % (form, H)
        pnet = net[desc.index(pdesc)]
        rb = hac_ols(pnet, smb_all); rb0 = hac_ols(pnet, smb_p0)
        reg_rows.append(dict(segment=pname, form=form, arm='C0', alpha=0.0, universe='clean_full', parent_beta=rb['beta'], parent_beta_se=rb['se_beta'],
                             parent_alpha_ann=rb['alpha'] * J.ANN, n=rb['n']))
        reg_rows.append(dict(segment=pname, form=form, arm='C0', alpha=0.0, universe='pool0', parent_beta=rb0['beta'], parent_beta_se=rb0['se_beta'],
                             parent_alpha_ann=rb0['alpha'] * J.ANN, n=rb0['n']))
        for k in keys:
            arm, a = k.split('|'); a = float(a)
            main = (arm in MAIN and a == 0.25) or arm == 'C0'
            ch = base if arm == 'C0' else lay(M[keys.index(k)], main)
            r = dict(segment=pname, form=form, arm=arm, alpha=a, main_config=bool(arm in MAIN and a == 0.25))
            for lab in ('tw', 'names', 'small', 'large') + (('hold',) if main else ()):
                mu, sd, nd = seg_stats(ch[lab] - base[lab])
                r['%s_diff_mean' % lab], r['%s_diff_sd' % lab], r['%s_days' % lab] = mu, sd, nd
                r['%s_child_mean' % lab] = float(np.nanmean(ch[lab])) * 100
            r['tw_parent_mean'] = float(np.nanmean(base['tw'])) * 100
            # (b) 编辑层 gap_t（照 size_gap 同式逐日重算，并与 summary 对账）
            if arm != 'C0':
                kj, k0 = M[keys.index(k)], M[keys.index('C0|0.0')]
                ent, ext = kj & ~k0, k0 & ~kj
                gaps = []
                for d_ in np.unique(ci.t[ent | ext]):
                    sl = ci.t == d_
                    e = cell_pct[sl & ent]; x = cell_pct[sl & ext]; e = e[np.isfinite(e)]; x = x[np.isfinite(x)]
                    if len(e) and len(x):
                        gaps.append(np.median(e) - np.median(x))
                g = np.array(gaps)
                r['edit_gap_mean'] = float(g.mean()) * 100 if len(g) else np.nan
                r['edit_gap_absmean'] = float(np.abs(g).mean()) * 100 if len(g) else np.nan
                sm = summ[(summ.form == form) & (summ.arm == arm) & np.isclose(summ.alpha, a) & (summ.H == H)]
                r['edit_gap_summary'] = float(sm.size_gap_mean.iloc[0]) * 100 if len(sm) else np.nan
            # S4（全部掩码行：S2 的领导词表门要对 288 网格对象判定）
            if True:
                for nm, dv in (('src', ch['dev']), ('norm', ch['devn'])):
                    mx = np.nanmax(dv, axis=1)
                    r['s4_%s_max_over_days' % nm] = float(np.nanmax(mx)) * 100
                    r['s4_%s_mean_daily_max' % nm] = float(np.nanmean(mx)) * 100
                    r['s4_%s_absmax_over_days' % nm] = float(np.nanmax(np.abs(dv))) * 100
                    r['s4_%s_n_daybucket_gt3' % nm] = int(np.nansum(dv > 0.03))
                    r['s4_%s_mean_by_bucket' % nm] = '|'.join('%.2f' % (v * 100) for v in np.nanmean(dv, axis=0))
                r['dev_stock_max_w'] = ch['stock_max']; r['dev_ind_excess_max'] = ch['ind_excess_max']
            # S3（主对象）
            if arm in MAIN and a == 0.25:
                cdesc = [d for d in desc if d.startswith('P|%s|%s|' % (form, arm)) and d.endswith('|a=0.25|H%d' % H)][0]
                d = np.where(np.isfinite(net[desc.index(cdesc)]) & np.isfinite(pnet), net[desc.index(cdesc)] - pnet, np.nan)
                for uni, smb in (('clean_full', smb_all), ('pool0', smb_p0)):
                    rr = hac_ols(d, smb)
                    fd = np.isfinite(d)
                    reg_rows.append(dict(segment=pname, form=form, arm=arm, alpha=a, universe=uni, D_ann=float(np.mean(d[fd])) * J.ANN, n_D=int(fd.sum()),
                                         alpha_ann=rr['alpha'] * J.ANN, alpha_se_ann=rr['se_alpha'] * J.ANN, beta=rr['beta'], beta_se=rr['se_beta'],
                                         r2=rr['r2'], n=rr['n'], parent_beta=(rb if uni == 'clean_full' else rb0)['beta']))
            rows.append(r)
        J.log('supp1 %s %s done %.0fs' % (pname, form, time.time() - t0), os.path.join(J.RES, 'logs', 'supp1_%s.log' % pname))
    # 自测
    df = pd.DataFrame(rows)
    c0 = df[df.arm == 'C0']
    st_rows.append(dict(segment=pname, universe='SELFTEST', check='C0 子 − 母四层 = 0',
                        value=float(np.nanmax(np.abs(c0[[c for c in c0.columns if c.endswith('_diff_mean')]].values)))))
    e = df[df.arm != 'C0']
    st_rows.append(dict(segment=pname, universe='SELFTEST', check='编辑层 gap 逐日重算 vs summary.csv 最大差（百分位点）',
                        value=float(np.nanmax(np.abs(e.edit_gap_mean - e.edit_gap_summary)))))
    st_rows.append(dict(segment=pname, universe='SELFTEST', check='dense pct 在 pool0 单元 = e6j_run_p.size_pct_cells 最大差',
                        value=float(np.nanmax(np.abs(cell_pct - __import__('e6j_run_p').size_pct_cells(env))))))
    for nm, x in (('layers', df), ('regress', pd.DataFrame(reg_rows)), ('stats', pd.DataFrame(st_rows)), ('pool0', pd.DataFrame(pool_rows))):
        J.atomic_write_csv(os.path.join(od, '%s.csv' % nm), x)
    J.log('supp1 %s all done %.0fs' % (pname, time.time() - t0), os.path.join(J.RES, 'logs', 'supp1_%s.log' % pname))
    return 0


if __name__ == '__main__':
    sys.exit(run(sys.argv[sys.argv.index('--segment') + 1]))
