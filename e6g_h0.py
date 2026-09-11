#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 块 H0 仪器诊断 (brief §3 / plan §2H0) —— 回答 Q11。

  1. selector 逐开关账 SRC -> QEDGE -> RANKBUDGET (影响集、人数、逐日计数)
  2. 平局: 是否真的压在 cutoff 上; WHOLE_TIE (整块同落); RANDOM_TIE 64 seed (独立 / 5 日持续)
  3. NEW40 输入变换并排 RAW->NS->rank vs pool_rank(raw)->NS->rank (只推导段)
  4. 源中性化的退化日计数 + NS_safe

平局只对【实际影响 cutoff】的那些日子扩展 (brief §3)。所有结果只作列, 不作闸。
"""
import os, sys, json, time, argparse
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6g_core as G
import e6g_desc as GD
import e6g_c as CC

M1 = np.uint64(0x9E3779B97F4A7C15)
M2 = np.uint64(0xBF58476D1CE4E5B9)
M3 = np.uint64(0x94D049BB133111EB)
NSEED = 64
BRIDGES = ['KT_dep(45,45)', 'KT_dep(50,50)', 'KT_dep(55,55)', 'KT_dep(65,65)',
           'CT_dep(45,45)', 'CT_dep(50,50)', 'CT_dep(55,55)', 'CT_dep(65,65)']
DEPTH_CORES = ['KTC_mean@25', 'KTC_mean@30', 'KT_mean@30', 'T@25', 'T@30']


def hkey(seed, tkey, cols):
    x = (np.uint64(seed + 1) * M1 + np.uint64(tkey + 1) * M2 + cols.astype(np.uint64) * M3)
    x ^= x >> np.uint64(30); x *= M2
    x ^= x >> np.uint64(27); x *= M3
    x ^= x >> np.uint64(31)
    return x


def tie_diag(score, p0c, pctkeep, g):
    """哪些天的并列真的压在 cutoff 上。返回逐日 (有效数, 唯一值数, cutoff 并列块大小)。"""
    T = score.shape[0]
    nval = np.zeros(T, int); nuni = np.zeros(T, int); cutblk = np.zeros(T, int)
    keep_g = int(round(g * pctkeep / 100.0))
    for t in range(T):
        v = np.flatnonzero(p0c[t] & ~np.isnan(score[t]))
        n = len(v)
        nval[t] = n
        if n < 3 * g:
            continue
        s = score[t, v]
        nuni[t] = len(np.unique(s))
        gid = F.qcut_group(n, g)
        order = np.lexsort((v, s))
        so = s[order]
        last_in = np.flatnonzero(gid <= keep_g)
        if len(last_in) == 0 or last_in[-1] + 1 >= n:
            continue
        cutval = so[last_in[-1]]
        if so[last_in[-1] + 1] == cutval:              # cutoff 值跨界重复 = 并列压边
            cutblk[t] = int((s == cutval).sum())
    return nval, nuni, cutblk


def keep_whole_tie(score, p0c, pctkeep, g):
    """整块落箱: 用【平均秩】定组, 同分票整块进同一组 (人数会偏离预算, 报偏差)。"""
    T, Nc = score.shape
    out = np.zeros((T, Nc), bool)
    keep_g = int(round(g * pctkeep / 100.0))
    dev = np.zeros(T)
    for t in range(T):
        v = np.flatnonzero(p0c[t] & ~np.isnan(score[t]))
        n = len(v)
        if n < 3 * g:
            continue
        gid_by_rank = F.qcut_group(n, g)
        avg = pd.Series(score[t, v]).rank(method='average').to_numpy()
        gi = gid_by_rank[np.clip(np.rint(avg).astype(int) - 1, 0, n - 1)]
        sel = v[gi <= keep_g]
        out[t, sel] = True
        dev[t] = len(sel) - int(round(n * pctkeep / 100.0))
    return out, dev


def keep_random_tie(score, p0c, pctkeep, g, seed, persist=False):
    """同分块内用 hash(seed, date|block5, stock) 定序, 其余与 SRC 相同。"""
    T, Nc = score.shape
    out = np.zeros((T, Nc), bool)
    keep_g = int(round(g * pctkeep / 100.0))
    for t in range(T):
        v = np.flatnonzero(p0c[t] & ~np.isnan(score[t]))
        n = len(v)
        if n < 3 * g:
            continue
        kk = hkey(seed, t // 5 if persist else t, v)
        order = np.lexsort((kk, score[t, v]))
        gid = F.qcut_group(n, g)
        out[t, v[order[gid <= keep_g]]] = True
    return out


def ev(S, mask):
    idx, val = F.dev_from_dense(S, mask)
    g_, p_, tu, n8 = F.sparse_pnl_H(S, idx, val, K.HOLD, F.COST)
    return dict(gross_ann=G.ann(g_), net8_ann=G.ann(n8), turn_mean=float(np.nanmean(tu)),
                pos_mean=float(np.nanmean(p_)), target_n=float(mask.sum(1).mean()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--nseed', type=int, default=NSEED)
    A = ap.parse_args()
    t0 = time.time()
    S = G.seg(A.segment, verbose=False)
    ctx = GD.GCtx(S)
    out = os.path.join(G.RES, 'H0')
    os.makedirs(out, exist_ok=True)
    print('段就绪 %.0fs' % (time.time() - t0), flush=True)

    sel_rows, tie_rows, tie_runs = [], [], []
    for cname in DEPTH_CORES + BRIDGES:
        core = GD.parse_core(cname)
        core = dict(core); core.setdefault('dirs', ['hi'] * len(core.get('comps') or []))
        core.setdefault('tfs', ['identity'] * len(core.get('comps') or []))
        depth = core['s'] if core['kind'] in ('single', 'mean') else core['b']
        g = F.P2G.get(int(depth))
        if g is None:
            continue
        c_src = dict(core, sel='SRC', depth=None)
        m_src, score, cand = ctx.build_core_g(c_src)
        rep_q, rep_r = {}, {}
        ctx.report = rep_q
        m_q, _, _ = ctx.build_core_g(dict(core, sel='QEDGE', depth=None))
        ctx.report = rep_r
        m_r, _, _ = ctx.build_core_g(dict(core, sel='RANKBUDGET', depth=depth))
        ctx.report = {}
        nval = np.array([int((cand[t] & ~np.isnan(score[t])).sum()) for t in range(S.T)])
        common = nval >= 3 * g
        row = dict(segment=A.segment, core=cname, depth=float(depth), g=g,
                   n_common_days=int(common.sum()), T=S.T,
                   SRC_vs_QEDGE_cells=int((m_src != m_q).sum()),
                   SRC_vs_QEDGE_cells_on_common=int((m_src[common] != m_q[common]).sum()),
                   QEDGE_extra_days=int((m_q.any(1) & ~m_src.any(1)).sum()),
                   SRC_vs_RANKBUDGET_cells=int((m_src != m_r).sum()),
                   n_src=float(m_src.sum(1).mean()), n_qedge=float(m_q.sum(1).mean()),
                   n_rankbudget=float(m_r.sum(1).mean()))
        row.update({('qedge_' + k2): v for k2, v in rep_q.items()})
        row.update({('rb_' + k2): v for k2, v in rep_r.items()})
        for tag, mm in (('SRC', m_src), ('QEDGE', m_q), ('RANKBUDGET', m_r)):
            e = ev(S, mm)
            row.update({'%s_%s' % (tag, k2): v for k2, v in e.items()})
        sel_rows.append(row)

        # ---- 平局 ----
        nv, nu, cb = tie_diag(score, cand, depth, g)
        bind = int((cb > 0).sum())
        tie_rows.append(dict(segment=A.segment, core=cname, depth=float(depth), g=g,
                             days_scored=int((nv >= 3 * g).sum()),
                             days_cutoff_tie=bind,
                             frac_cutoff_tie=float(bind / max(1, (nv >= 3 * g).sum())),
                             max_cut_block=int(cb.max()),
                             median_unique_over_valid=float(np.median(
                                 (nu[nv > 0] / nv[nv > 0])) if (nv > 0).any() else np.nan)))
        if bind == 0:
            continue                                   # 并列不压边 -> 不扩展 64 seed
        mw, dev = keep_whole_tie(score, cand, depth, g)
        tie_runs.append(dict(segment=A.segment, core=cname, policy='WHOLE_TIE', seed=-1,
                             headcount_dev_mean=float(dev.mean()),
                             headcount_dev_max=float(np.abs(dev).max()),
                             cells_vs_SRC=int((mw != m_src).sum()), **ev(S, mw)))
        for persist in (False, True):
            acc = []
            for sd in range(A.nseed):
                mr = keep_random_tie(score, cand, depth, g, sd, persist)
                acc.append(dict(cells_vs_SRC=int((mr != m_src).sum()), **ev(S, mr)))
            arr = {k2: np.array([x[k2] for x in acc], float) for k2 in acc[0]}
            r = dict(segment=A.segment, core=cname,
                     policy='RANDOM_TIE_' + ('persist5' if persist else 'indep'),
                     seed=A.nseed)
            for k2, v in arr.items():
                r[k2 + '_mean'] = float(v.mean()); r[k2 + '_sd'] = float(v.std(ddof=1))
            tie_runs.append(r)
        print('  %s 完成 %.0fs (cutoff 并列 %d 天)' % (cname, time.time() - t0, bind), flush=True)

    pd.DataFrame(sel_rows).to_csv(os.path.join(out, 'selector_switch_%s.csv' % A.segment),
                                  index=False)
    pd.DataFrame(tie_rows).to_csv(os.path.join(out, 'tie_prevalence_%s.csv' % A.segment),
                                  index=False)
    if tie_runs:
        pd.DataFrame(tie_runs).to_csv(os.path.join(out, 'tie_runs_%s.csv' % A.segment),
                                      index=False)

    # ---- NEW40 输入变换并排 (只推导段) ----
    if A.segment in G.DERIV_SEGS:
        rows = []
        for kk in G.NEW40:
            if kk in G.DIAGNOSTIC_ONLY:
                continue
            G.guard(G.Lin.of(kk), 'shape', segment=A.segment,
                    label_end=G.NEW40_LABEL_END, where='H0_input_variant')
            try:
                raw = G.build_raw_g(S, G.specF(kk))
            except Exception as e:
                rows.append(dict(segment=A.segment, key=kk, status=str(e)[:80]))
                continue
            raw = raw.reindex(index=S.pool0.index, columns=S.pool0.columns)
            pr = raw.where(S.pool0 == 1).rank(axis=1, pct=True)   # pool_rank(raw)
            c1, _ = F.neu_cache(raw, S.pool0, S.log_mcap, S.icodes_neu, 'NS')
            c2, _ = F.neu_cache(pr, S.pool0, S.log_mcap, S.icodes_neu, 'NS')
            P1 = G.pct_dense_dir(c1, S.dates, S.ccolpos, S.Nc, 'hi')
            P2 = G.pct_dense_dir(c2, S.dates, S.ccolpos, S.Nc, 'hi')
            both = np.isfinite(P1) & np.isfinite(P2) & S.p0c
            sp = []
            for t in range(0, S.T, 5):
                v = both[t]
                if v.sum() >= 10:
                    sp.append(float(pd.Series(P1[t, v]).corr(pd.Series(P2[t, v]),
                                                             method='spearman')))
            m1 = G.keep_SRC(P1, S.p0c, 25)
            m2 = G.keep_SRC(P2, S.p0c, 25)
            rows.append(dict(segment=A.segment, key=kk, status='ok',
                             n_cells=int(both.sum()),
                             max_abs_diff=float(np.max(np.abs(P1[both] - P2[both])))
                             if both.any() else np.nan,
                             spearman_median=float(np.nanmedian(sp)) if sp else np.nan,
                             spearman_min=float(np.nanmin(sp)) if sp else np.nan,
                             mask_diff_cells_at_d25=int((m1 != m2).sum()),
                             mask_jaccard_d25=float((m1 & m2).sum() / max(1, (m1 | m2).sum()))))
        pd.DataFrame(rows).to_csv(os.path.join(out, 'new40_input_variant_%s.csv' % A.segment),
                                  index=False)
        print('  NEW40 输入变换 %d 键 %.0fs' % (len(rows), time.time() - t0), flush=True)

    # ---- 源中性化的退化日 ----
    lm = S.log_mcap.reindex(index=S.pool0.index, columns=S.pool0.columns).values
    deg = dict(days_pool_lt6=0, days_pool_6to9_ns_fallback=0, days_mcap_var0=0)
    for t in range(S.T):
        v = np.flatnonzero(S.p0[t] & np.isfinite(lm[t]))
        n = len(v)
        if n < 6:
            deg['days_pool_lt6'] += 1
        elif n < 10:
            deg['days_pool_6to9_ns_fallback'] += 1     # 源 neutralize_by_mcap 原样返回
        if n >= 2 and float(np.var(lm[t, v])) == 0.0:
            deg['days_mcap_var0'] += 1
    deg['segment'] = A.segment
    json.dump(deg, open(os.path.join(out, 'ns_degenerate_%s.json' % A.segment), 'w'),
              indent=1, ensure_ascii=False)
    json.dump(dict(block='H0diag', segment=A.segment, elapsed_s=round(time.time() - t0, 1)),
              open(os.path.join(G.RES, 'task_status', 'DONE_H0diag_%s.json' % A.segment), 'w'),
              indent=1)
    print('DONE H0 诊断 %s  %.0fs  中性化退化 %s' % (A.segment, time.time() - t0, deg), flush=True)


if __name__ == '__main__':
    main()
