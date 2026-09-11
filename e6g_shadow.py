#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 块 C4: 影子账户 (brief §9) —— part2。

顺序开关: 源引擎 -> 同账户模型的理想可成交 (Xideal) -> 加实际标志/停牌 (X0)
         -> 再加 flag_buy/flag_sell (X1, unknown 两种处置)。每步一个开关。
锚: Xengine (引擎价格路径 + 无现金约束 + bp=0) 必须逐位等于源引擎。
**X1 用对齐后的标志** —— E6f 的列错位使其 X1 失效 (source_corrections_E6g §13), 本轮给正确数。
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--A_yi', type=float, default=5.0)
    A = ap.parse_args()
    t0 = time.time()
    S = G.seg(A.segment, verbose=False)
    ctx = GD.GCtx(S)
    SC = CC.ShadowCtx(S)
    out = os.path.join(G.RES, 'C')
    os.makedirs(out, exist_ok=True)
    Ai = A.A_yi * CC.YI
    rows, checks = [], []

    # 标志覆盖 (对齐后)
    for nm, arr in (('flag_buy', SC.FB), ('flag_sell', SC.FS)):
        if arr is None:
            continue
        a = arr.astype(float)
        checks.append(dict(segment=A.segment, field=nm,
                           cov_on_pool0=float(np.mean(np.isfinite(a[S.p0c]))),
                           eq1_on_pool0=float(np.nanmean(a[S.p0c] == 1)),
                           note='已对齐 (align_to_close)'))

    for lab, cid, _ in G.DISPLAY:
        cfg = GD.parse_cfg(cid)
        pnl, iv, _ = ctx.run(cfg)
        W = CC.target_weights(S, iv[0], iv[1], K.HOLD)
        eng_ex = pnl[0] - pnl[2] * F.COST / 1e4          # 源引擎 net8
        # --- 锚: Xengine ---
        ax = CC.shadow_account(SC, W, 'ideal', 'constant_notional', Ai, bp=0.0,
                               convention='engine')
        d_eng = np.abs(np.nan_to_num(ax['excess'], nan=0.0)
                       - np.nan_to_num(pnl[0], nan=0.0))
        checks.append(dict(segment=A.segment, label=lab, config_id=cid,
                           anchor='Xengine_vs_source_gross',
                           max_abs_diff=float(np.nanmax(d_eng)),
                           recon_max=float(np.nanmax(np.abs(ax['recon']))),
                           bad_fill_total=float(np.nansum(ax['bad_fill']))))
        base = dict(segment=A.segment, label=lab, config_id=cid, A_yi=A.A_yi,
                    engine_net8_ann=G.ann(eng_ex))
        for mode, unk, tag in (('ideal', True, 'Xideal'), ('X0', True, 'X0'),
                               ('X1', True, 'X1_unknown_tradable'),
                               ('X1', False, 'X1_unknown_untradable')):
            acc = CC.shadow_account(SC, W, mode, 'constant_notional', Ai, bp=F.COST,
                                    unknown_tradable=unk)
            ex = acc['excess']
            rows.append(dict(base, scenario=tag,
                             account_net8_ann=G.ann(ex),
                             vs_engine=G.ann(ex) - G.ann(eng_ex),
                             pos_mean=float(np.nanmean(acc['pos'])),
                             fee_ann=float(np.nansum(acc['fee'])) / Ai / len(ex) * 252 * 100,
                             unfilled_buy_mean=float(np.nanmean(acc['unfilled_buy'])) / Ai,
                             unfilled_sell_mean=float(np.nanmean(acc['unfilled_sell'])) / Ai,
                             trapped_mean=float(np.nanmean(acc['trapped'])) / Ai,
                             scaled_down_days=int(np.nansum(acc['scaled_down'])),
                             bad_fill_total=float(np.nansum(acc['bad_fill'])),
                             recon_max=float(np.nanmax(np.abs(acc['recon'])))))
        print('  %s 完成 %.0fs' % (lab, time.time() - t0), flush=True)

    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(out, 'shadow_%s.csv' % A.segment), index=False)
    json.dump(checks, open(os.path.join(out, 'shadow_checks_%s.json' % A.segment), 'w'),
              indent=1, ensure_ascii=False)
    print()
    print('== 逐开关 (相对源引擎, 年化点) ==')
    print(R.pivot_table(index='label', columns='scenario', values='vs_engine').round(3).to_string())
    json.dump(dict(block='C4shadow', segment=A.segment, n_rows=len(R),
                   elapsed_s=round(time.time() - t0, 1)),
              open(os.path.join(G.RES, 'task_status', 'DONE_shadow_%s.json' % A.segment), 'w'),
              indent=1)
    print('DONE shadow %s %.0fs' % (A.segment, time.time() - t0))


if __name__ == '__main__':
    main()
