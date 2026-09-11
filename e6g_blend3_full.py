#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Blend3 / R2 的【全窗口】账户值: 四段逐日序列拼接后再年化 (ann 对日均线性,
但必须按有效日数加权, 所以直接拼日序列最稳)。补 revisions/E6f_blend_estimate_withdrawn。"""
import os, sys, json
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6g_core as G
import e6g_desc as GD
import e6f_core as F
import e6e_core as K

OUT = os.path.join(G.RES, 'revisions', 'E6f_blend_estimate_withdrawn')
WANT = ['A03', 'A06', 'A08', 'R1', 'R2']


def main():
    os.makedirs(OUT, exist_ok=True)
    acc = {}                                    # name -> list of per-seg daily tuples
    nfin = []
    for pname in G.SEGMENTS:
        S = G.seg(pname, verbose=False)
        ctx = GD.GCtx(S)
        ivs, lv = {}, {}
        for lab, cid, _ in G.DISPLAY:
            if lab not in WANT:
                continue
            pnl, iv, _ = ctx.run(GD.parse_cfg(cid))
            ivs[lab], lv[lab] = iv, pnl
        bi, bv = G.blend3_weights([ivs[m] for m in G.BLEND3_MEMBERS])
        lv['Blend3'] = F.sparse_pnl_H(S, bi, bv, K.HOLD, F.COST)
        for lab, pnl in lv.items():
            acc.setdefault(lab, []).append(np.asarray(pnl))
        nfin.append(dict(segment=S.name, n_cal=int(S.T),
                         n_finite_gross=int(np.isfinite(lv['R2'][0]).sum())))
        print(' %s ok' % S.name, flush=True)
        del S

    rows = []
    for lab, segs in acc.items():
        cat = np.concatenate(segs, axis=1)      # (4, T_total)
        gr, po, tu, n8 = cat
        rows.append(dict(account=lab, scope='full_window',
                         n_days_cal=int(cat.shape[1]),
                         n_days_finite_gross=int(np.isfinite(gr).sum()),
                         gross_ann=float(G.ann(gr)), net8_ann=float(G.ann(n8)),
                         net12_ann=float(G.ann(gr - tu * 12.0 / 1e4)),
                         turn_mean=float(np.nanmean(tu)),
                         turn_ann_x252=float(np.nanmean(tu) * 252),
                         pos_mean=float(np.nanmean(po))))
    d = pd.DataFrame(rows).sort_values('account')
    d.to_csv(os.path.join(OUT, 'blend3_fullwindow.csv'), index=False)
    json.dump(nfin, open(os.path.join(OUT, 'day_counts.json'), 'w'), indent=1)
    pd.set_option('display.width', 220)
    print(d.round(4).to_string(index=False))
    print(json.dumps(nfin, ensure_ascii=False))


if __name__ == '__main__':
    main()
