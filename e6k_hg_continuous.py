# -*- coding: utf-8 -*-
"""E6k HG 跨段连续状态诊断（执行端补充 X09；plan §7.5：主历史四段段首空状态对齐旧引擎 reset，另在固定主对象给一条"允许数据内连续状态"诊断）。
对象：144 主展示里的 48 个 HG 对象（NATIVE_HG10 / INC1_HG10 × 四测量 × 六形态，α .25 × H5）。
按段顺序：上一段段末门内成员（规范 ticker）→ 本段首日初始状态（按 ticker 对到本段列；不在本段门域的不恢复）；
本段目标 → H5 账户；与登记账户（段首空状态）的逐日配对差 D（连续 − 重置）与门差格数。段末状态存 diagnostics/hg_continuous/state_<段>.json，
后段在授权后从推导段末状态接着算（--segments 2019-2023,2024-2026 --init-from 2015-2018）。只在已封存的段上读登记账户。"""
import e6k_boot  # noqa: F401
import os
import sys
import json
import argparse

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_seal as SEAL
import e6j_stats as ST


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segments', required=True)
    ap.add_argument('--init-from', default=None)
    ap.add_argument('--tag', default='')                               # v2（2026-09-29）：输出另起文件名，v1 保留
    ap.add_argument('--hold-init', action='store_true')                # v2：段首预热日（K = 0）不清空上段末状态，带到第一个形成日
    a = ap.parse_args()
    segs = a.segments.split(',')
    vtag = (a.tag + '_') if a.tag else ''
    for s in segs:
        ok, bad = SEAL.verify('deriv' if s in K.DERIV_SEGS else 'post')
        if not ok:
            raise RuntimeError('封存核对失败（%s）：%s' % (s, bad[:5]))
    import e6k_env as E
    import e6k_ops as O
    import e6k_acct as AC
    import e6k_run_det as RD
    od = K.P('diagnostics', 'hg_continuous')
    os.makedirs(od, exist_ok=True)
    state = {}
    if a.init_from:
        state = json.load(open(os.path.join(od, 'state_%s%s.json' % (vtag, a.init_from)), encoding='utf-8'))
    rows = []
    for pname in segs:
        seg = E.Seg(pname)
        acct = AC.Acct(seg, impact=False)
        reg = {}
        for f in (K.P('accounts', pname, '%s__%s.npz' % (p, m)) for p in E.P6 for m in ('S', 'M', 'Q', 'C1')):
            z = K.npz(f)
            for i, did in enumerate(map(str, z['desc'])):
                if did.endswith(('NATIVE_HG10', 'INC1_HG10')) and '|a0.25|H5|' in did:
                    reg[did] = z['d_net8'][i]
        new_state = {}
        for p in E.P6:
            st = seg.struct(p)
            k0 = st.q0
            tid_ids = seg.tid[st.ids]
            for f in ('S', 'M', 'Q', 'C1'):
                ctx = RD.Ctx(seg, st, k0, seg.kf(f))
                for base in ('NATIVE', 'INC1'):
                    did = '%s|%s|a0.25|H5|%s_HG10' % (f, p, base)
                    sc = st.gate_scores(ctx.q_base(base, 0.25)[None, :])
                    init = np.zeros((1, seg.Nc), bool)
                    prev = set(state.get(did, []))
                    if prev:
                        init[0] = np.isin(seg.tid_c, np.array(sorted(prev), np.int64))
                    g, endst = O.hg_gate(st, sc, 10 * st.bunit, tid_ids, init_cols=init, return_state=True, hold_init=a.hold_init)
                    g0 = O.hg_gate(st, sc, 10 * st.bunit, tid_ids)
                    kept = st.down(g)[0]
                    tg = acct.target(kept)
                    n8 = acct.ledgers(tg, (5,), roll=False)[5]['net8']
                    D, n = ST.seg_D(ST.paired(n8, reg[did])[0])
                    rows.append(dict(segment=pname, desc_id=did, init_from_prev_segment=bool(prev), gate_cells_diff=int((g != g0).sum()),
                                     D_continuous_minus_reset=D, n=n))
                    new_state[did] = seg.tid_c[np.flatnonzero(endst[0])].astype(int).tolist()
        K.atomic_write_json(os.path.join(od, 'state_%s%s.json' % (vtag, pname)), new_state)
        state = new_state
        K.log('hg_continuous %s done' % pname)
    p = os.path.join(od, 'hg_continuous_%s%s.csv' % (vtag, '_'.join(segs)))
    K.atomic_write_csv(p, pd.DataFrame(rows))
    K.write_receipt('hg_continuous_%s%s' % (vtag, '_'.join(segs)), [p] + [os.path.join(od, 'state_%s%s.json' % (vtag, s)) for s in segs], 'SUCCEEDED', rows=len(rows),
                    hold_init=bool(a.hold_init))
    print('hg_continuous', len(rows), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
