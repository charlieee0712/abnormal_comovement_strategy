# -*- coding: utf-8 -*-
"""E6l 比较层统计（plan §7.1 / §9.3a / §11.1–§11.2a；brief §7）：comparison_manifest 的每条比较在日层先闭合（Σ 系数 × 日序列，全部端点同日有限）
再出段均 D（年化百分点）与 HAC se（lag H / max(2H, 20) / 60）。一段一个进程；读数门同 e6l_stats（seal 核对）。
视图：SOURCE_RAW 与附属视图（KERNEL_DOSE / 支持桥 / STRICT250）= net8 与 gross（零费）两版 + 线性费用项（−8e−4·Δturn）；
      MATCH_CAP_FIXED_PATH = 左端描述符自身的 sc_child − sc_parent；MATCH_CAP_INV_LOOP = ICL 行的 sc_child − sc_parent；
      RANDOM_PATH_MEAN（真实 − 随机）= 真实 net8 − 随机逐日路径均值（random_daily_<段>.npz；MCSE 另在 random_refs，时间 se 在此）。
输出 results/<阶段>/comparison_stats_<段>.csv：cmp_id / kind / view / query_id / D_ann_pp / Dg_ann_pp / fee_ann_pp / n_days / se_H_ann_pp / se_2H_ann_pp /
se_60_ann_pp（+ 每条左右 ID、H）。CONTINUOUS 视图由连续面板脚本另算。"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import time
import argparse

import numpy as np
import pandas as pd

import e6l_core as L
import e6l_mde80 as MD

DET_VIEWS = ('SOURCE_RAW', 'DOSE_MATCHED_MEAN_RMS', 'COMMON_SUPPORT', 'Q0_MASKED_TO_CHILD_SUPPORT', 'STRICT250')


def load(pname):
    d = {}
    for f in sorted(glob.glob(L.P('accounts', pname, '*.npz'))):
        if os.path.basename(f).startswith('weights_'):
            continue
        z = L.npz(f, keys=['desc', 'd_net8', 'd_gross', 'd_turn', 'd_sc_child', 'd_sc_parent'])
        for i, did in enumerate([str(v) for v in z['desc']]):
            d[did] = dict(net8=z['d_net8'][i], gross=z['d_gross'][i], turn=z['d_turn'][i], scc=z['d_sc_child'][i], scp=z['d_sc_parent'][i])
    return d


def batch(rows_x, H):
    Dm = np.vstack(rows_x)
    I = np.isfinite(Dm)
    n = I.sum(1)
    with np.errstate(all='ignore'):
        mu = np.where(n > 0, np.nansum(Dm, 1) / np.maximum(n, 1), np.nan)
    out = dict(D=mu * L.ANN, n=n)
    for lab, lag in (('se_H', H), ('se_2H', max(2 * H, 20)), ('se_60', 60)):
        se, _ = MD.hac_batch(Dm, lag)
        out[lab] = se * L.ANN
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--phase', default='deriv')
    ap.add_argument('--trial', action='store_true')                # 试跑：只在 E6L_RES 指向临时目录时跳过封存核对
    a = ap.parse_args()
    t0 = time.time()
    pname = a.segment
    if pname in L.POST_SEGS:
        L.post_gate(pname, 'cmpstats %s' % pname)
    import e6l_seal as SEAL
    ok, bad = (True, []) if (a.trial and L.RES.startswith(L.TRIAL)) else SEAL.verify('deriv' if pname in L.DERIV_SEGS else 'post')
    if not ok:
        raise RuntimeError('封存核对失败：%s' % bad[:5])
    CM = L.read_csv_keep(L.P('registry', 'comparison_manifest_E6l.csv'))
    CM = CM[CM.view != 'CONTINUOUS'].copy()
    CM['tl'] = CM.terms.map(MD.split_terms)
    CM['H'] = [int(t[0].split('|')[4 if t[0].split('|')[0] in MD.ACC else 3][1:]) for t in CM.tl]
    d = load(pname)
    rd = L.npz(L.P('results', a.phase, 'random_daily_%s.npz' % pname))
    out = []
    for (view, H), g in CM.groupby(['view', 'H']):
        xs, gs, fs, keep = [], [], [], []
        for r in g.itertuples():
            tl = r.tl
            coefs = [int(c) for c in r.coef.split('|')]
            if view in DET_VIEWS:
                if any(t not in d for t in tl):
                    continue
                x = sum(c * d[t]['net8'] for c, t in zip(coefs, tl))
                gg = sum(c * d[t]['gross'] for c, t in zip(coefs, tl))
                ff = sum(c * (-8e-4 * d[t]['turn']) for c, t in zip(coefs, tl))
            elif view in ('MATCH_CAP_FIXED_PATH', 'MATCH_CAP_INV_LOOP'):
                t = tl[0]
                if t not in d:
                    continue
                x = d[t]['scc'] - d[t]['scp']
                gg = np.full(len(x), np.nan)
                ff = np.full(len(x), np.nan)
            elif view == 'RANDOM_PATH_MEAN':
                t, rk = tl[0], r.right_id
                key = ('%s~H%d~%s' % (t, H, rk.split('|', 1)[0])).replace('|', '~')
                if t not in d or key not in rd:
                    continue
                x = d[t]['net8'] - rd[key]
                gg = np.full(len(x), np.nan)
                ff = np.full(len(x), np.nan)
            else:
                continue
            xs.append(x)
            gs.append(gg)
            fs.append(ff)
            keep.append(r)
        if not keep:
            continue
        bx = batch(xs, H)
        bg = batch(gs, H)
        bf = batch(fs, H)
        for i, r in enumerate(keep):
            out.append(dict(cmp_id=r.cmp_id, kind=r.kind, view=r.view, left_id=r.left_id, right_id=r.right_id, H=int(H), segment=pname,
                            D_ann_pp=float(bx['D'][i]), Dg_ann_pp=float(bg['D'][i]), fee_ann_pp=float(bf['D'][i]), n_days=int(bx['n'][i]),
                            se_H_ann_pp=float(bx['se_H'][i]), se_2H_ann_pp=float(bx['se_2H'][i]), se_60_ann_pp=float(bx['se_60'][i]), query_id=r.query_id))
    S = pd.DataFrame(out)
    od = L.P('results', a.phase)
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, 'comparison_stats_%s.csv' % pname)
    L.atomic_write_csv(p, S)
    L.write_receipt(L.next_rerun('cmpstats_%s_%s' % (a.phase, pname)), [p], 'SUCCEEDED', n_rows=len(S), wall_s=round(time.time() - t0, 1),
                    views=S.view.value_counts().to_dict() if len(S) else {})
    print('%s：%d 条比较（%.0fs）' % (pname, len(S), time.time() - t0), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
