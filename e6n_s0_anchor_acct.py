# -*- coding: utf-8 -*-
"""E6n Stage 0 第 2 类（账户层锚；附录 A2-2 / A2-4 / H02）：只算源对象——原父（α = 0）、Q0 / C1 × α .125 / .25 / .5 × NONE / HG10 / LAG1_10、
R2 / A06 原父——的账户（本轮登记的 ANCHOR 282 + STRONG_ANCHOR 10），落在 stage0/anchor_accounts/<段>/<形态>.npz（不进主账户目录 accounts/，
主账户在 seal_B1_0 之后另算，见闭包门 ⑦ 的范围说明）。源对象在 E6m / E6l 已评（SECOND_EVALUATION_SAME_HISTORY），不是本轮新对象，四段都算。
核对（判据来源 = 基线：E6m 阶段 S 交付账户 npz，同输入同引擎）：逐日 d_net8 / d_gross / d_turn / d_sc_child / d_sc_parent / d_pos，NaN 位置一致 + 有限格最大差；
另核 8bp 恒等 net8 = gross − 8e−4·turn（1e−12）。输出 stage0/c2_anchor_accounts_E6m.csv + .json。"""
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6n_core as N
import e6n_masks as MK

E6M_W = N.E6M_WORK
KEYS = ('net8', 'gross', 'turn', 'pos', 'sc_child', 'sc_parent')


def e6m_id(did):
    """本轮锚 desc_id → E6m desc_id。"""
    p = did.split('|')
    kind, feat, parent, mem, H, alpha = p[0], p[1], p[2], p[3], p[4], p[7][1:]
    if kind == 'STRONG_ANCHOR' or feat == 'ORIGINAL':
        return 'K0|%s|PARENT|-|-|NONE|%s|SOURCE|-' % (parent, H)
    return '%s|%s|LINEAR|-|a%s|%s|%s|SOURCE|-' % (feat, parent, alpha, mem, H)


def run(seg_name, parent):
    import e6k_acct as AC
    import e6l_env as V
    t0 = time.time()
    seg = V.SegL(seg_name, state=False)
    acct = AC.Acct(seg)
    z = np.load(N.P('masks', seg_name, '%s.npz' % parent), allow_pickle=False)
    keys = [str(x) for x in z['mask_keys']]
    n = int(z['n_cells'][0])
    R = MK.registry_rows()
    R = R[(R.parent == parent) & (R.table == 'MAIN') & R.obj.str.match(r'^(ANCHOR|STRONG_ANCHOR)\|')]
    by_key = {}
    for r in R.itertuples():
        by_key.setdefault(r.mask_key, []).append((r.obj, int(r.H)))
    nat = [k for k in keys if k.split('|', 2)[2].startswith('NATIVE') and k.startswith('NONE|')][0]
    un = lambda k: np.unpackbits(z['final_bits'][keys.index(k)])[:n].astype(bool)
    F0 = un(nat)
    tp = acct.target(F0)
    out = {k: [] for k in AC.DESC_KEYS}
    ids, Hs_ = [], []
    for mk, rows in by_key.items():
        kept = un(mk)
        tg = acct.target(kept)
        Hs = tuple(sorted({h for _, h in rows}))
        led = acct.ledgers(tg, Hs, par=None if mk == nat else tp, impact=True, roll=True)
        for obj, H in rows:
            ids.append(obj)
            Hs_.append(H)
            for k in AC.DESC_KEYS:
                out[k].append(led[H][k])
    od = N.P('stage0', 'anchor_accounts', seg_name)
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, '%s.npz' % parent)
    N.atomic_write_npz(p, desc=np.array(ids), desc_H=np.array(Hs_), dates=np.array([str(d)[:10] for d in seg.dates]),
                       **{'d_' + k: np.vstack(out[k]) for k in AC.DESC_KEYS})
    return p, time.time() - t0


def compare(seg_name, parent):
    p = N.P('stage0', 'anchor_accounts', seg_name, '%s.npz' % parent)
    a = np.load(p, allow_pickle=False)
    e = np.load(os.path.join(E6M_W, 'accounts', seg_name, '%s.npz' % parent), allow_pickle=False)
    ei = {str(x): j for j, x in enumerate(e['desc'])}
    rows = []
    for j, did in enumerate(a['desc']):
        did = str(did)
        k = e6m_id(did)
        r = dict(segment=seg_name, parent=parent, desc_id=did, e6m_desc_id=k)
        if k not in ei:
            r.update(status='NOT_APPLICABLE', note='E6m 无该对象')
            rows.append(r)
            continue
        i = ei[k]
        worst = 0.0
        nan_mm = 0
        for kk in KEYS:
            x, y = a['d_' + kk][j], e['d_' + kk][i]
            nan_mm += int((np.isfinite(x) != np.isfinite(y)).sum())
            f = np.isfinite(x) & np.isfinite(y)
            if f.any():
                worst = max(worst, float(np.abs(x[f] - y[f]).max()))
        idn = float(np.nanmax(np.abs(a['d_net8'][j] - (a['d_gross'][j] - 8e-4 * a['d_turn'][j]))))
        r.update(max_abs_diff=worst, nan_mismatch=nan_mm, net8_identity_maxabs=idn,
                 status='PASS' if (nan_mm == 0 and worst <= 1e-12 and idn <= 1e-12) else 'FAIL')
        rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['run', 'compare'])
    ap.add_argument('--seg', default='')
    ap.add_argument('--parent', default='')
    a = ap.parse_args()
    if a.step == 'run':
        p, wall = run(a.seg, a.parent)
        N.write_receipt('E6n_s0_anchor_acct_%s_%s' % (a.seg, a.parent), [p], code=[__file__], wall_s=round(wall, 1))
        print(json.dumps(dict(seg=a.seg, parent=a.parent, wall_s=round(wall, 1))), flush=True)
        return
    rows = []
    for seg in N.SEGMENTS:
        for parent in ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5', 'R2', 'A06'):
            rows += compare(seg, parent)
    df = pd.DataFrame(rows)
    p = N.P('stage0', 'c2_anchor_accounts_E6m.csv')
    N.atomic_write_csv(p, N.to_status(df))
    s = dict(df.status.value_counts().to_dict(), worst=float(df.max_abs_diff.max()), net8_identity_worst=float(df.net8_identity_maxabs.max()))
    N.atomic_write_json(N.P('stage0', 'c2_anchor_accounts_E6m.json'), s)
    N.write_receipt('E6n_s0_anchor_compare', [p], code=[__file__], **{k: v for k, v in s.items()})
    print(json.dumps(s, ensure_ascii=False))


if __name__ == '__main__':
    main()
