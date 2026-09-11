#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 块 K: carried —— 40 键推导段准备 (brief §7) —— 回答 Q10。

只用 2010-2014 / 2015-2018; 全部 exploratory; 40 键守卫全程有效 (label_end <= 2018-12-31)。
K2: 40 键 x 双方向 x k{2,5} 单因子 (E3 口径 5 组形状 + 1/3/5 日累计) ;
    40 键 x 双方向 x k{5,10} 叠 R2/A06/A08 作否决, RAW / RANK 两种输入都跑;
    每否决配: 母体 / 同人数 core / 同人数反向 / I-IID 解析期望。
随机路径: 主切片 (k=5 x A06 x RAW) 上 128 独立 + 128 五日持续, 只存汇总与 8 条示例。
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
import comprehensive_factor_diagnosis as C
from event_study import get_base_pool

PARENTS = {'R2': 'KT_mean@30|C:k5+cr5:k10', 'A06': 'KTC_mean@25|cvr_1d:k10+cr5:k10',
           'A08': 'T@30|C:k5+cr5:k10'}
M1 = np.uint64(0x9E3779B97F4A7C15); M2 = np.uint64(0xBF58476D1CE4E5B9)
M3 = np.uint64(0x94D049BB133111EB)


def hkey(seed, tkey, cols):
    x = (np.uint64(seed + 1) * M1 + np.uint64(tkey + 1) * M2 + cols.astype(np.uint64) * M3)
    x ^= x >> np.uint64(30); x *= M2
    x ^= x >> np.uint64(27); x *= M3
    x ^= x >> np.uint64(31)
    return x


def iid_expect(S, mask_pool, m_per_day):
    """I-IID 解析期望 gross/pos: 每天从有效域里等概率抽 m 只, DEV 后的期望权重。
       E[w_i] = (m_h/n_h)·u·min(1, cap_h/(m_h·u)), u = min(1/m, MAX_STOCK)。只给 gross/pos。"""
    T = S.T
    gross = np.zeros(T); pos = np.zeros(T)
    for t in range(T):
        v = np.flatnonzero(mask_pool[t])
        n = len(v)
        m = int(m_per_day[t])
        if n == 0 or m <= 0:
            continue
        u = min(1.0 / m, K.MAX_STOCK)
        ic = S.icodes[t, v]
        w = np.zeros(n)
        for h in np.unique(ic):
            sel = ic == h
            nh = int(sel.sum())
            mh = m * nh / n
            cap = S.cap[t, h] if h >= 0 and h < S.G else 1.0
            sc = min(1.0, cap / max(1e-12, mh * u))
            w[sel] = (mh / nh) * u * sc
        pos[t] = w.sum()
        gross[t] = float(np.nansum(w * np.nan_to_num(S.r0[t, v], nan=0.0)))
    # 与引擎同一条 rolling 与 shift(2)
    den = np.minimum(np.arange(1, T + 1), K.HOLD).astype(float)
    cs = np.concatenate([[0.0], np.cumsum(pos)])
    lo = np.maximum(np.arange(1, T + 1) - K.HOLD, 0)
    p2 = np.zeros(T); p2[2:] = ((cs[1:] - cs[lo]) / den)[:-2]
    return float(np.nanmean(gross)) * 252 * 100, float(np.nanmean(p2))


def ev(S, M, mask, impact=True):
    idx, val = F.dev_from_dense(S, mask)
    g_, p_, tu, n8 = F.sparse_pnl_H(S, idx, val, K.HOLD, F.COST)
    d = dict(gross_ann=G.ann(g_), net8_ann=G.ann(n8), net12_ann=G.ann(g_ - tu * 12e-4),
             turn_mean=float(np.nanmean(tu)), pos_mean=float(np.nanmean(p_)),
             target_n=float(mask.sum(1).mean()))
    if impact:
        br = CC.profile_and_impact(M, idx, val, K.HOLD, full_profile=False)[0]
        d['bracket_sqrt_mean'] = float(np.nanmean(br['sqrt']))
    return d, (g_, p_, tu, n8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshard', type=int, default=1)
    ap.add_argument('--npath', type=int, default=128)
    A = ap.parse_args()
    assert A.segment in G.DERIV_SEGS, 'K 只跑推导段 (40 键守卫)'
    t0 = time.time()
    S = G.seg(A.segment, verbose=False)
    ctx = GD.GCtx(S)
    M = CC.MarketCtx(S)
    out = os.path.join(G.RES, 'K_discovery')
    os.makedirs(out, exist_ok=True)
    lab_end = str(pd.Timestamp(S.dates[-1]).date())
    print('段就绪 %.0fs label_end=%s' % (time.time() - t0, lab_end), flush=True)

    keys = [k for k in G.NEW40 if k not in G.DIAGNOSTIC_ONLY]
    keys = [k for i, k in enumerate(keys) if i % A.nshard == A.shard]
    diagkeys = [k for k in G.NEW40 if k in G.DIAGNOSTIC_ONLY] if A.shard == 0 else []
    print('本分片 %d 键 (+ %d 诊断键)' % (len(keys), len(diagkeys)), flush=True)

    # E3 口径的前瞻标签 (只用本段数据, 段尾自然 NaN -> label_end 不越界)
    bp = get_base_pool(S.data)
    fwd = C.compute_forward_5d_excess(S.data, bp, hold_days=K.HOLD, adjust=True)
    lmc = C.compute_log_mcap(S.data.get('mcap'))

    P = {}
    for nm, cid in PARENTS.items():
        m, sc, cand, cm = ctx.full_mask_g(GD.parse_cfg(cid))
        P[nm] = (m, sc, cand, cm)

    rows, shapes, pathrows, exemplars = [], [], [], {}
    for kk in keys + diagkeys:
        lin = G.Lin.of(kk)
        G.guard(lin, 'label', segment=A.segment, label_end=lab_end, where='K2:' + kk)
        try:
            raw = G.build_raw_g(S, G.specF(kk))
        except Exception as e:
            rows.append(dict(segment=A.segment, key=kk, status='BUILD_FAIL: ' + str(e)[:120]))
            continue
        raw = raw.reindex(index=S.pool0.index, columns=S.pool0.columns)
        prk = raw.where(S.pool0 == 1).rank(axis=1, pct=True)
        for inp, src in (('RAW', raw), ('RANK', prk)):
            cch, info = F.neu_cache(src, S.pool0, S.log_mcap, S.icodes_neu, 'NS')
            for dr in ('hi', 'lo'):
                Pk = G.pct_dense_dir(cch, S.dates, S.ccolpos, S.Nc, dr)
                is_diag = kk in G.DIAGNOSTIC_ONLY
                # ---- 单因子形状 (E3 口径) ----
                if dr == 'hi' and inp == 'RAW':
                    res = C.event_study_analysis_cached(cch, fwd, S.pool0, 5, kk)
                    shapes.append(dict(segment=A.segment, key=kk, n_groups=5,
                                       status=('none' if res is None else 'ok'),
                                       detail=json.dumps(
                                           {a: (float(b) if isinstance(b, (int, float))
                                                else str(b)) for a, b in
                                            (res.items() if isinstance(res, dict) else [])},
                                           ensure_ascii=False)[:800]))
                # ---- 单因子剔尾 k ∈ {2,5} ----
                for kv in (2, 5):
                    dm = F.drop_mask_dense(Pk, S.p0c, kv)
                    e, _ = ev(S, M, S.p0c & ~dm, impact=False)
                    rows.append(dict(segment=A.segment, key=kk, input=inp, direction=dr,
                                     role='single_drop', k=kv, parent='pool0',
                                     diagnostic_only=is_diag, **e))
                # ---- 叠父作否决 k ∈ {5,10} ----
                for kv in (5, 10):
                    for pn, (pm, psc, pcand, pcm) in P.items():
                        dm = F.drop_mask_dense(Pk, S.p0c, kv)
                        m2 = pm & ~dm
                        e, dl = ev(S, M, m2)
                        nrem = (pm & dm).sum(axis=1).astype(int)
                        rows.append(dict(segment=A.segment, key=kk, input=inp, direction=dr,
                                         role='veto_on_parent', k=kv, parent=pn,
                                         diagnostic_only=is_diag,
                                         n_removed_mean=float(nrem.mean()), **e))
                        # 同人数 core (按父末级分数)
                        mc = F.coretrim_matchN(S, -psc, pm, nrem)
                        e2, _ = ev(S, M, pm & ~mc, impact=False)
                        rows.append(dict(segment=A.segment, key=kk, input=inp, direction=dr,
                                         role='ctl_core_matchN', k=kv, parent=pn, **e2))
                        # 同人数反向 (反方向的毒尾里取同样人数)
                        Pr = G.pct_dense_dir(cch, S.dates, S.ccolpos, S.Nc,
                                             'lo' if dr == 'hi' else 'hi')
                        mr = F.coretrim_matchN(S, -Pr, pm, nrem)
                        e3, _ = ev(S, M, pm & ~mr, impact=False)
                        rows.append(dict(segment=A.segment, key=kk, input=inp, direction=dr,
                                         role='ctl_reverse_matchN', k=kv, parent=pn, **e3))
                        # I-IID 解析期望 (只 gross/pos)
                        gi, pi = iid_expect(S, pm, (pm.sum(axis=1) - nrem))
                        rows.append(dict(segment=A.segment, key=kk, input=inp, direction=dr,
                                         role='iid_analytic', k=kv, parent=pn,
                                         gross_ann=gi, pos_mean=pi))
                        # ---- 随机路径: 只在主切片 (k=5, A06, RAW) ----
                        if kv == 5 and pn == 'A06' and inp == 'RAW':
                            for kind in ('indep', 'persist'):
                                acc = []
                                for b in range(A.npath):
                                    fake = np.zeros_like(pm)
                                    for t in range(S.T):
                                        v = np.flatnonzero(pm[t])
                                        r = int(nrem[t])
                                        if len(v) == 0 or r <= 0:
                                            continue
                                        hh = hkey(b, t if kind == 'indep' else t // 5, v)
                                        fake[t, v[np.argsort(hh)[:min(r, len(v))]]] = True
                                    e4, dl4 = ev(S, M, pm & ~fake, impact=True)
                                    acc.append(e4)
                                    if b < 4 and len(exemplars) < 8:
                                        exemplars['%s|%s|%s|%d' % (kk, dr, kind, b)] = dl4[3]
                                arr = {c: np.array([x[c] for x in acc], float) for c in acc[0]}
                                r_ = dict(segment=A.segment, key=kk, direction=dr, kind=kind,
                                          n_path=A.npath, parent=pn, k=kv)
                                for c, v in arr.items():
                                    r_[c + '_mean'] = float(v.mean())
                                    r_[c + '_sd'] = float(v.std(ddof=1))
                                    r_[c + '_mcse'] = float(v.std(ddof=1) / np.sqrt(len(v)))
                                pathrows.append(r_)
        print('  %s 完成 %.0fs' % (kk, time.time() - t0), flush=True)

    tag = '%s_s%d' % (A.segment, A.shard)
    pd.DataFrame(rows).to_csv(os.path.join(out, 'K2_%s.csv' % tag), index=False)
    pd.DataFrame(shapes).to_csv(os.path.join(out, 'K2_shapes_%s.csv' % tag), index=False)
    if pathrows:
        pd.DataFrame(pathrows).to_csv(os.path.join(out, 'K2_random_%s.csv' % tag), index=False)
    if exemplars:
        pd.DataFrame(exemplars, index=pd.DatetimeIndex(S.dates)).to_parquet(
            os.path.join(out, 'K2_exemplar_net8_%s.parquet' % tag))
    json.dump(dict(block='K', segment=A.segment, shard=A.shard, n_keys=len(keys),
                   n_rows=len(rows), n_path_rows=len(pathrows), label_end=lab_end,
                   elapsed_s=round(time.time() - t0, 1)),
              open(os.path.join(G.RES, 'task_status', 'DONE_K_%s.json' % tag), 'w'),
              indent=1, ensure_ascii=False)
    print('DONE K %s: %d 行 %.0fs' % (tag, len(rows), time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
