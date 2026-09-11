#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 收尾补: Blend3 的【账户级】水平值 (gross/net8/turn/pos, 逐段年化)。
brief §14 要求 revisions/ 收录「Blend 估算撤回」—— E6g_proposal §5 表里 Blend3 的数是
「账本平均估」。本脚本走与 D 块 refs() 完全相同的路径 (GD.GCtx + blend3_weights +
sparse_pnl_H, 三成员目标权重各 1/3 合并后【重新过引擎】) 算真实账户值, 供撤回那行估算。
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6g_core as G
import e6g_desc as GD
import e6f_core as F
import e6e_core as K

OUT = os.path.join(G.RES, 'revisions', 'E6f_blend_estimate_withdrawn')


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for pname in G.SEGMENTS:
        S = G.seg(pname, verbose=False)
        ctx = GD.GCtx(S)
        ivs, lv = {}, {}
        for lab, cid, _ in G.DISPLAY:
            if lab not in G.BLEND3_MEMBERS:
                continue
            pnl, iv, _ = ctx.run(GD.parse_cfg(cid))
            ivs[lab], lv[lab] = iv, pnl
        bi, bv = G.blend3_weights([ivs[m] for m in G.BLEND3_MEMBERS])
        bp = F.sparse_pnl_H(S, bi, bv, K.HOLD, F.COST)
        for lab in list(G.BLEND3_MEMBERS) + ['Blend3']:
            gr, po, tu, n8 = (bp if lab == 'Blend3' else lv[lab])
            rows.append(dict(segment=S.name, account=lab,
                             gross_ann=float(G.ann(gr)), net8_ann=float(G.ann(n8)),
                             turn_mean=float(np.nanmean(tu)),
                             pos_mean=float(np.nanmean(po))))
        gm = np.mean([lv[m][0] for m in G.BLEND3_MEMBERS], axis=0)
        pm = np.mean([lv[m][1] for m in G.BLEND3_MEMBERS], axis=0)
        tm = np.mean([lv[m][2] for m in G.BLEND3_MEMBERS], axis=0)
        rows[-1]['anchor_gross_maxdiff'] = float(np.nanmax(np.abs(bp[0] - gm)))
        rows[-1]['anchor_pos_maxdiff'] = float(np.nanmax(np.abs(bp[1] - pm)))
        rows[-1]['turn_minus_member_mean'] = float(np.nanmean(bp[2]) - np.nanmean(tm))
        print(' %s ok' % S.name, flush=True)
        del S

    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(OUT, 'blend3_account_levels.csv'), index=False)
    print(d.to_string(index=False))


if __name__ == '__main__':
    main()
