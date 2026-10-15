# -*- coding: utf-8 -*-
"""E6n B3：现行 CVR 否决的真实同数对照（plan §9.1；brief §1.3-13；registry/b3_manifest_E6n.csv）。读收益：推导段 deriv_ready、后段 post_gate。
对象：三裸核心（A4b / M_mean3_v2 / M_union3_v2）× {原生 NATIVE、Q0 NONE / HG10 / LAG1_10（α .25）}；固定源 CVR20 k5（X_CVRv5 = X ∧ ¬否决）。
P = CVR 之前的真实父名单（裸核心最终名单），D = P ∖ X_CVRv5 最终名单（本日被源 CVR 实际删掉），m = |D|（逐日）。同数对照（删 m）：
  RANDOM_LEGAL_CVR   P ∩ 合法 CVR 观测域（源 neu_cvr 当日有限）内随机删 m（64 路径，稳定哈希；不足 → 可行性计数，不从域外补）
  WORST_OLD_K        P 内旧 K（pcond 坏度）最坏 m
  SOURCE_PRIORITY    A4b：最终 T 优先序（第二关 T 在 S1 上按源口径中性化后的坏度，最坏 m）；Mmean：综合分最坏 m；
  MAX_EXISTING_RANK  Munion 研究控制：max(K 坏度, T 坏度, cr20 坏度) 最坏 m（不冒称原有"最终核心分"）
权重两条：REDO_DEV（删后重做 DEV）与 FROZEN（冻结父 DEV 权重删票，删掉的权重留现金）；H5 主、H1 / H10 附。
层贡献（FROZEN，固定总体分母 = 段全部日）：位置 T−1（pre_r20 三分，E6m B3 事件 pos）、年、制度（SH 2018-08-20 前 / 后、SZ）。
输出 results/<phase>/b3/b3_same_count_<段>.csv、b3_same_count_split_<段>.csv。"""
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6n_core as N

CORES = (('A4b', 'A4b_CVRv5'), ('M_mean3_v2', 'M_mean3_v2_CVRv5'), ('M_union3_v2', 'M_union3_v2_CVRv5'))
KEYS = ('NONE|a0|NATIVE', 'NONE|a0.25|Q0', 'HG10|a0.25|Q0', 'LAG1_10|a0.25|Q0')
HS = (1, 5, 10)
NPATH = 64
E6M_W = N.E6M_WORK


def mask(seg, form, key, n, what='final_bits'):
    z = np.load(N.P('masks', seg, '%s.npz' % form), allow_pickle=False)
    keys = [str(k) for k in z['mask_keys']]
    return np.unpackbits(z[what][keys.index(key)])[:n].astype(bool)


def run(seg_name):
    import e6l_env as V
    import e6k_acct as AC
    import e6j_random as RND
    import e6n_rand as RN
    import e6n_vars as VR
    import e6n_support as SU
    t0 = time.time()
    seg = V.SegL(seg_name, state=False)
    acct = AC.Acct(seg, impact=False)
    SE = seg.SE
    B = VR.Base(seg_name)
    n = seg.n
    import pickle
    with open(os.path.join(E6M_W, 'tmp', 'ctx_%s.pkl' % seg_name), 'rb') as fh:
        ctx = pickle.load(fh)
    p0 = ctx['p0']
    ccols = np.flatnonzero(p0.any(0))
    cvr_fin = np.zeros(p0.shape, bool)
    di = {x: i for i, x in enumerate(ctx['pool0'].index)}
    cp = {x: j for j, x in enumerate(ctx['pool0'].columns)}
    for d, s in ctx['neu_cvr'].items():
        s = s.dropna()
        if d in di:
            cvr_fin[di[d], [cp[x] for x in s.index]] = True
    cvr_ok = cvr_fin[:, ccols][B.t, B.c]
    k0 = B.get('k0')
    # 调节：位置（E6m POOL0 事件 pos）、年、制度
    ev = np.load(os.path.join(E6M_W, 'stageN', 'B3_prelim', 'work', 'events_%s__POOL0.npz' % seg_name), allow_pickle=False)
    ed = np.array([int(str(x).replace('-', '')) for x in ev['dates']], np.int64)
    dates = B.get('dates')
    codes = B.get('codes')
    dmap = {int(d): i for i, d in enumerate(dates)}
    key = {(int(a), str(b)): i for i, (a, b) in enumerate(zip(B.t, codes[B.c]))}
    pos = np.full(n, -9, np.int64)
    for t_, tk, pv in zip(ev['t'], ev['tick'], ev['pos']):
        j = key.get((dmap.get(int(ed[t_]), -1), '%06d' % int(tk)))
        if j is not None:
            pos[j] = int(pv)
    yr = (dates // 10000)[B.t]
    ex = np.where(np.char.startswith(codes[B.c].astype(str), '6'), 'SH', 'SZ')
    regime = np.where(ex == 'SZ', 'SZ', np.where(dates[B.t] >= 20180820, 'SH_POST', 'SH_PRE'))
    lm = RN.CTX.get('lm')
    if lm is None:
        import e6n_meas as ME
        S = ME.SegM(seg_name)
        lm = S.cells(S.ctx['log_mcap'].reindex(index=S.pool0.index, columns=S.pool0.columns).to_numpy(float)[:, S.ccols])
    off = np.r_[0, np.cumsum(np.bincount(B.t, minlength=seg.T))].astype(np.int64)
    rows, srows = [], []
    for core, cvf in CORES:
        st = seg.struct(core)
        for k in KEYS:
            P = mask(seg_name, core, k, n)
            C = mask(seg_name, cvf, k, n)
            if (C & ~P).any():
                srows.append(dict(segment=seg_name, core=core, object_key=k, note='CVR 名单不是裸名单子集：%d 格' % int((C & ~P).sum()), status='FAIL'))
            Dl = P & ~C
            m_day = np.bincount(B.t[Dl], minlength=seg.T)
            # 优先序（越大越坏）
            if st.kind == 'A4b':
                G = mask(seg_name, core, k, n, 'gate_bits')
                S1 = np.zeros(n, bool)
                S1[np.asarray(st.ids)] = G
                prio = SU.pct_pool(np.asarray(st.st.M.T_raw_c, float), S1, lm, off, 'hi')
                prio_name = 'SOURCE_PRIORITY'
            elif st.kind == 'mean':
                K = np.asarray(st.q0, float) if k.endswith('NATIVE') else VR.native_q(np.asarray(st.q0, float), B.kQ, 0.25)
                prio = np.full(n, np.nan)
                prio[np.asarray(st.ids)] = st.gate_scores(K[None, :])[0]
                prio_name = 'SOURCE_PRIORITY'
            else:
                K = np.asarray(st.q0, float) if k.endswith('NATIVE') else VR.native_q(np.asarray(st.q0, float), B.kQ, 0.25)
                env = seg.env
                prio = np.fmax(np.fmax(np.nan_to_num(K, nan=9), np.nan_to_num(env.pT, nan=9)), np.nan_to_num(env.pR, nan=9))
                prio_name = 'MAX_EXISTING_RANK'
            ctrls = {}
            for nm, score in (('WORST_OLD_K', k0), (prio_name, prio)):
                keep = P.copy()
                feas = 0
                for d in np.flatnonzero(m_day):
                    a0, a1 = off[d], off[d + 1]
                    cand = np.flatnonzero(P[a0:a1]) + a0
                    sc = np.where(np.isfinite(score[cand]), score[cand], -np.inf)
                    o = np.lexsort((-cand, -sc))
                    keep[cand[o[:m_day[d]]]] = False
                    feas += len(cand) >= m_day[d]
                ctrls[nm] = [keep]
            rk = []
            short = 0
            for p in range(NPATH):
                keep = P.copy()
                for d in np.flatnonzero(m_day):
                    a0, a1 = off[d], off[d + 1]
                    cand = np.flatnonzero(P[a0:a1] & cvr_ok[a0:a1]) + a0
                    m = int(m_day[d])
                    if len(cand) < m:
                        short += 1
                        m = len(cand)
                    u = RND.uniform(RND.path_key('E6n.B3.RANDOM_LEGAL_CVR', '%s|%s' % (core, k), seg_name, 'LEGAL_CVR', 'IID', p),
                                    np.full(len(cand), d), cand)
                    keep[cand[np.argsort(-u, kind='stable')[:m]]] = False
                rk.append(keep)
            ctrls['RANDOM_LEGAL_CVR'] = rk
            tp = acct.target(P)
            led_p = acct.ledgers(tp, HS, impact=False, roll=False)
            wcell = np.zeros(n)
            wcell[tp['ids']] = tp['w']
            for nm, lists in [('CVR_REAL', [C])] + list(ctrls.items()):
                for wmode in ('REDO_DEV', 'FROZEN'):
                    vals = {H: [] for H in HS}
                    for L in lists:
                        if wmode == 'REDO_DEV':
                            tg = acct.target(L)
                        else:
                            ids = np.flatnonzero(L & P)
                            tg = dict(ids=ids, t=seg.ci.t[ids], c=seg.ci.c[ids], w=wcell[ids])
                        led = acct.ledgers(tg, HS, impact=False, roll=False)
                        for H in HS:
                            dd = led[H]['net8'] - led_p[H]['net8']
                            ok = np.isfinite(dd)
                            vals[H].append(float(np.mean(dd[ok])) * N.ANN if ok.any() else np.nan)
                    for H in HS:
                        v = np.asarray(vals[H], float)
                        rows.append(dict(segment=seg_name, core=core, cvr_form=cvf, object_key=k, control=nm, weights=wmode, H=H,
                                         D_vs_parent_ann_pp=float(np.nanmean(v)), D_sd_paths=float(np.nanstd(v, ddof=1)) if len(v) > 1 else np.nan, paths=len(v),
                                         deleted_cells=int(Dl.sum()), days_with_deletion=int((m_day > 0).sum()),
                                         feasibility_shortfall=short if nm == 'RANDOM_LEGAL_CVR' else 0, main=(H == 5 and wmode == 'REDO_DEV'), status='COMPUTED'))
            # 层贡献（FROZEN，固定总体分母）：删 D 的贡献 = Σ_{i∈D} −(w_i/den)(r − bench)，按层累加
            r0 = np.asarray(SE.r0, float)
            bench = np.asarray(SE.bench, float)
            for H in HS:
                for nm, lists in [('CVR_REAL', [C])] + [(a, b[:1] if a != 'RANDOM_LEGAL_CVR' else b) for a, b in ctrls.items()]:
                    acc = {}
                    for L in lists:
                        delc = np.flatnonzero(P & ~L)
                        if not len(delc):
                            continue
                        f = seg.ci.t[delc]
                        c = seg.ci.c[delc]
                        w = wcell[delc]
                        contrib = np.zeros(len(delc))
                        for jj in range(H):
                            tt = f + 2 + jj
                            okk = tt < seg.T
                            den = np.minimum(tt[okk] - 1, H).astype(float)
                            contrib[okk] += -(w[okk] / den) * (r0[tt[okk], c[okk]] - bench[tt[okk]])
                        for lay, lv in (('POSITION_T-1', pos[delc]), ('YEAR', yr[delc]), ('REGIME', regime[delc])):
                            for v in np.unique(lv):
                                acc.setdefault((lay, str(v)), []).append(float(contrib[lv == v].sum()) / seg.T * N.ANN)
                    for (lay, v), xs in acc.items():
                        srows.append(dict(segment=seg_name, core=core, object_key=k, control=nm, weights='FROZEN', H=H, split=lay, cell=v,
                                          contribution_ann_pp=float(np.mean(xs)), paths=len(xs), denominator='段全部日（固定总体分母）', status='COMPUTED'))
        N.log('B3 %s %s（%.0f s）' % (seg_name, core, time.time() - t0))
    od = N.P('results', 'deriv' if seg_name in N.DERIV_SEGS else 'full', 'b3')
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, 'b3_same_count_%s.csv' % seg_name)
    p2 = os.path.join(od, 'b3_same_count_split_%s.csv' % seg_name)
    N.atomic_write_csv(p1, N.to_status(pd.DataFrame(rows)))
    N.atomic_write_csv(p2, N.to_status(pd.DataFrame(srows)))
    return [p1, p2], time.time() - t0


def main():
    import e6n_gate as GT
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    a = ap.parse_args()
    GT.deriv_ready(a.seg, 'B3 %s' % a.seg)
    outs, wall = run(a.seg)
    N.write_receipt('E6n_b3_%s' % a.seg, outs, code=[__file__], wall_s=round(wall, 1))
    print(json.dumps(dict(seg=a.seg, wall_s=round(wall, 1)), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
