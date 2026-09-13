#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 后段首次观察 (brief §7)。**只跑记录 B 冻结的清单。**

跑前核 `registration/record_B_approved.json` 的清单 SHA; 只有清单内的描述符会被算。
守卫仍在生效 —— 清单外的 route_id 一律被 `guard_h` 拒绝。

两后段**按同一清单全部计算并封存**, 完成 receipt 后共同展示
(brief §6: 不看 2019-2023 之后再改 2024-2026)。所以本脚本一次跑一段,
两段都跑完才由 `e6h_post_receipt.py` 开封。

对照沿推导段: 原父同 H / 同人数核心 / 同人数反向 / 共同可得域父 / 同仓位。

用法: python3 e6h_post.py --segment 2019-2023
"""
from __future__ import annotations
import os
import sys
import json
import time
import hashlib
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_rules as RU
import e6h_run_routes as RR
import e6h_expand as EX
import e6h_samepos as SP
import e6g_core as G
import e6g_desc as GD
import e6g_l as L6
import e6f_core as F
import e6e_core as K

RES = H.RES
HS = [3, 5, 10, 20]


def load_approved():
    p = os.path.join(RES, 'registration', 'record_B_approved.json')
    d = json.load(open(p))
    assert d.get('status') == 'APPROVED', '记录 B 未批准'
    ids = set()
    for e in d['entries']:
        ids |= set(e.get('descriptor_ids') or [])
    # 复核清单 SHA (防批准后被改)
    chk = dict(d)
    chk.pop('list_sha256', None)
    raw = json.dumps(chk, indent=1, ensure_ascii=False, sort_keys=True)
    sha = hashlib.sha256(raw.encode()).hexdigest()
    return d, ids, sha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    assert a.segment in H.POST_SEGS, '本脚本只跑后段'
    t0 = time.time()
    appr, ids, sha_now = load_approved()
    H.load_approval()
    print('  记录 B: 批准于 %s; 清单 %d 个描述符; SHA 复核 %s'
          % (appr['approved_at'], len(ids),
             'OK' if sha_now == appr['list_sha256'] else '!! 不符'), flush=True)
    if sha_now != appr['list_sha256']:
        raise SystemExit('清单 SHA 与批准时不符 —— 批准后被改过, 拒绝运行')

    rows = [r for r in EX.all_descriptors() if r['descriptor_id'] in ids]
    assert len(rows) == len(ids), '清单里有 %d 个 ID 在描述符表里找不到' % (len(ids) - len(rows))
    S = H.seg(a.segment, verbose=False)
    print('  段就绪 %.0fs; 本段要跑 %d 个描述符 x %d 个 H'
          % (time.time() - t0, len(rows), len(HS)), flush=True)

    out, pctx = [], {}
    for i, r in enumerate(rows):
        p = r['parent']
        if p not in pctx:
            pctx[p] = RR.ParentCtx(S, p)
        P = pctx[p]
        keys = [k for k in (r.get('new_key'), r.get('vol_key'), r.get('risk_key'),
                            r.get('liq_key'), r.get('state_key')) if k]
        if r['route_id'] == 'I-P-peer-up-laggard':
            keys += ['IND_CUR_20', 'REL_IND_20']
        H.guard_h(keys, 'trade', segment=a.segment, where=r['descriptor_id'],
                  route_id=r['route_id'], rule_objects=[r['role']])
        mask, wmul, ex = RR.build_mask(P, r)
        idx, val = F.dev_from_dense(S, mask)
        if wmul is not None:
            val = [v * wmul[t, idx[t]] if len(idx[t]) else v for t, v in enumerate(val)]
        pidx, pval = F.dev_from_dense(S, P.B)
        for Hh in HS:
            g1, p1, t1, n1 = F.sparse_pnl_H(S, idx, val, Hh, F.COST)
            g0, p0_, t0_, n0 = F.sparse_pnl_H(S, pidx, pval, Hh, F.COST)
            both = np.isfinite(g1) & np.isfinite(g0)
            # 同仓位
            sC, sP = SP.scale_to_min((idx, val), (pidx, pval))
            pc = F.sparse_pnl_H(S, sC[0], sC[1], Hh, F.COST)
            pp = F.sparse_pnl_H(S, sP[0], sP[1], Hh, F.COST)
            rec = dict(segment=a.segment, descriptor_id=r['descriptor_id'],
                       route_id=r['route_id'], parent=p, role=r['role'], H=Hh,
                       is_identity=bool(r.get('is_identity')),
                       new_key=r.get('new_key'), alpha=r.get('alpha'),
                       policy=r.get('policy'), w=r.get('w'), q=r.get('q'),
                       eta=r.get('eta'),
                       net8_ann=H.ann(n1), gross_ann=H.ann(g1),
                       turn_mean=float(np.nanmean(t1)), pos_mean=float(np.nanmean(p1)),
                       parent_net8_ann=H.ann(n0),
                       d_net8_ann=H.ann(np.where(both, n1 - n0, np.nan)),
                       d_gross_ann=H.ann(np.where(both, g1 - g0, np.nan)),
                       d_net8_samepos=H.ann(np.where(both, np.asarray(pc[3])
                                                     - np.asarray(pp[3]), np.nan)))
            if Hh == K.HOLD:
                ctl = RR.controls(P, mask)
                for cn, cp in ctl.items():
                    rec['d_vs_%s' % cn] = H.ann(np.where(both, n1 - cp[3], np.nan))
            out.append(rec)
        if (i + 1) % 20 == 0:
            print('    %d/%d  %.0fs' % (i + 1, len(rows), time.time() - t0), flush=True)

    # 参照账户
    for nm, cid in list(L6.ATOMS.items()):
        ctxp = GD.GCtx(S)
        m = ctxp.full_mask_g(GD.parse_cfg(cid))[0]
        ix, vl = F.dev_from_dense(S, m)
        for Hh in HS:
            g_, p_, tu, n8 = F.sparse_pnl_H(S, ix, vl, Hh, F.COST)
            out.append(dict(segment=a.segment, descriptor_id='REF|%s|H=%d' % (nm, Hh),
                            route_id=None, parent=nm, role='source', H=Hh,
                            is_identity=False, net8_ann=H.ann(n8), gross_ann=H.ann(g_),
                            turn_mean=float(np.nanmean(tu)),
                            pos_mean=float(np.nanmean(p_))))

    od = os.path.join(RES, 'post_segments')
    os.makedirs(od, exist_ok=True)
    d = pd.DataFrame(out)
    p_out = os.path.join(od, 'SEALED_post_%s.csv' % a.segment)
    d.to_csv(p_out, index=False)
    with open(os.path.join(od, 'SEALED_receipt_%s.json' % a.segment), 'w') as fh:
        json.dump(dict(segment=a.segment, n_descriptors=len(rows), n_rows=len(d),
                       list_sha256=appr['list_sha256'],
                       approved_at=appr['approved_at'],
                       computed_at=time.strftime('%Y-%m-%d %H:%M:%S'),
                       elapsed_s=round(time.time() - t0, 1),
                       output_sha256=H.sha_file(p_out),
                       sealed=True,
                       note='封存; 两后段都跑完后才由 e6h_post_receipt.py 开封共同展示'),
                  fh, indent=1, ensure_ascii=False)
    print('  [%s] 封存 %d 行 (%d 描述符 x %d H + 参照), %.0fs'
          % (a.segment, len(d), len(rows), len(HS), time.time() - t0))


if __name__ == '__main__':
    main()
