#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g C1 冲击情景 (part1 交付项): 把已存的逐日括号折成 (A, κ) 网格上的实施净收益。

bracket 与 (A, κ) 无关, 情景只是它的标量倍:
   sqrt: c_t = κ·√(A·1e8) · bracket_t          (主口径)
   lin : c_t = (κ·A·1e8/√p0) · bracket_t,  p0 = 1%
A ∈ {1, 5, 10} 亿; κ ∈ {0.25, 0.5, 1.0}。net8 与 net12 各出一套。
参照 R1 / R2 / Blend3 用同一 (A, κ) 同一模型, 配对差按同日做。
"""
import os, sys, json, glob, time, argparse
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6g_core as G
import e6g_desc as GD
import e6g_c as CC

BLOCK_DIR = {'H0': 'H0', 'H1': 'H1', 'H2': 'H2', 'H4a': 'H4', 'H4b': 'H4',
             'H5': 'H5', 'B2': 'B2'}
AS = [1.0, 5.0, 10.0]
KAPPAS = [0.25, 0.5, 1.0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segments', default=','.join(G.SEGMENTS))
    A = ap.parse_args()
    t0 = time.time()
    out = os.path.join(G.RES, 'C')
    os.makedirs(out, exist_ok=True)
    rows = []
    for seg in A.segments.split(','):
        S = G.seg(seg, verbose=False)
        ctx = GD.GCtx(S)
        M = CC.MarketCtx(S)
        # 参照的逐日 net8 与括号 (同一模型同一 (A,κ))
        ref = {}
        ivs = {}
        for lab, cid, _ in G.DISPLAY:
            pnl, iv, _ = ctx.run(GD.parse_cfg(cid))
            br = CC.profile_and_impact(M, iv[0], iv[1], K.HOLD, full_profile=False)[0]
            ref[lab] = (pnl[0] - pnl[2] * F.COST / 1e4, br['sqrt'], br['lin'])
            ivs[lab] = iv
        bi, bv = G.blend3_weights([ivs[m] for m in G.BLEND3_MEMBERS])
        bp = F.sparse_pnl_H(S, bi, bv, K.HOLD, F.COST)
        bbr = CC.profile_and_impact(M, bi, bv, K.HOLD, full_profile=False)[0]
        ref['Blend3'] = (bp[0] - bp[2] * F.COST / 1e4, bbr['sqrt'], bbr['lin'])

        n8, brs, brl = {}, {}, {}
        for b, d in BLOCK_DIR.items():
            for fg in sorted(glob.glob(os.path.join(
                    G.RES, d, 'daily_gross_%s_%s_s*.parquet' % (b, seg)))):
                ft = fg.replace('daily_gross_', 'daily_turn_')
                fs = fg.replace('daily_gross_', 'daily_brsqrt_')
                fl = fg.replace('daily_gross_', 'daily_brlin_')
                if not all(os.path.exists(x) for x in (ft, fs, fl)):
                    continue
                gg = pd.read_parquet(fg); tt = pd.read_parquet(ft)
                ss = pd.read_parquet(fs); ll = pd.read_parquet(fl)
                v = gg.values - tt.values * F.COST / 1e4
                for i, c in enumerate(gg.columns):
                    n8[c] = v[:, i]; brs[c] = ss.values[:, i]; brl[c] = ll.values[:, i]
        if not n8:
            print('  %s 无账本' % seg, flush=True); continue
        cols = list(n8)
        X = np.column_stack([n8[c] for c in cols])
        BS = np.column_stack([brs[c] for c in cols])
        BL = np.column_stack([brl[c] for c in cols])
        print('  %s: %d 列, %.0fs' % (seg, len(cols), time.time() - t0), flush=True)

        for Ay in AS:
            for kp in KAPPAS:
                for form, B in (('sqrt', BS), ('lin', BL)):
                    c = CC.impact_cost(B, Ay, kp, form)
                    NI = X - np.nan_to_num(c, nan=0.0)
                    ann = np.nanmean(NI, axis=0) * 252 * 100
                    imp = np.nanmean(np.nan_to_num(c, nan=0.0), axis=0) * 252 * 100
                    rr = {}
                    for rn in ('R1', 'R2', 'Blend3'):
                        rc = CC.impact_cost(ref[rn][1] if form == 'sqrt' else ref[rn][2],
                                            Ay, kp, form)
                        rNI = ref[rn][0] - np.nan_to_num(rc, nan=0.0)
                        rr[rn] = np.nanmean(NI - rNI[:, None], axis=0) * 252 * 100
                    rows.append(pd.DataFrame(dict(
                        segment=seg, A_yi=Ay, kappa=kp, form=form, config_id=cols,
                        net_impact_ann=ann, impact_ann=imp,
                        d_vs_R1=rr['R1'], d_vs_R2=rr['R2'], d_vs_Blend3=rr['Blend3'])))
        del X, BS, BL
        print('  %s 情景完成 %.0fs' % (seg, time.time() - t0), flush=True)

    if not rows:
        print('无结果'); return
    R = pd.concat(rows, ignore_index=True)
    R.to_csv(os.path.join(out, 'impact_scenarios.csv'), index=False)
    # 容量 A*: 相对 R2 的优势过零点 (按 A 的网格线性插值, 无解 / 多解如实报)
    print('DONE impact: %d 行 %.0fs' % (len(R), time.time() - t0))
    s = R[(R.form == 'sqrt') & (R.kappa == 0.5)]
    print()
    print('== sqrt, κ=0.5: 各段各 A 下 vs R2 为正的配置数 / 总数 ==')
    print(s.groupby(['segment', 'A_yi']).apply(
        lambda g: '%d / %d' % (int((g.d_vs_R2 > 0).sum()), len(g))).to_string())


if __name__ == '__main__':
    main()
