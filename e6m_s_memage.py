# -*- coding: utf-8 -*-
"""E6m 逐日门层记忆事实（固定表 memory_age_daily；E6l a0 同列：segment | target_id | date | reliant_share | reliant_run_p50 | confirm_age_p50 | query_id）。
名单层（不读收益）：源记忆族（Q0 LINEAR α × HG10 / LAG1_10、K0 OLD_RULE × HG10 / LAG1_10），与 e6m_s_run_masks 同一门（mock 用转录记忆门，真实结构用源 mem_gate）。
逐日量由 e6m_s_ops.gate_facts(daily=…) 给出，与名单 facts 里的段汇总同一函数；本脚本另核"逐日依靠数之和 / 门成员之和 = 段汇总 bonus_reliant_share"。
输出 <根>/masks/<段>/memory_age_<形态>.csv。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_s_ops as S


def main():
    import e6m_s_real as RL
    import e6m_s_run_masks as RM
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--form', required=True)
    ap.add_argument('--struct', default='mock', choices=['mock', 'real'])
    a = ap.parse_args()
    t0 = time.time()
    R = RM.Runner(a.seg, a.form, a.struct)
    st, seg = R.st, R.seg
    dates = [str(x)[:10] for x in seg.dates]
    C = RM.configs(a.form)
    n_app = sum(1 for c_ in C.to_dict('records') if c_['memory'] in ('HG10', 'LAG1_10') and c_['block'] in ('SOURCE', 'OLD_RULE'))   # 登记中本形态的源记忆对象数（R2 / A06 = 0）
    rows, chk = [], []
    for cfg in C.to_dict('records'):
        mem = cfg['memory']
        if mem not in ('HG10', 'LAG1_10') or cfg['block'] not in ('SOURCE', 'OLD_RULE') or cfg['measurement'] in R.wait:
            continue
        if cfg['block'] == 'OLD_RULE':
            ctx, a_ = S._OldCtx(R.ctx0), 0.0
        else:
            ctx, a_ = R.ctx(cfg['measurement']), float(cfg['alpha'][1:]) if str(cfg['alpha']).startswith('a') else float(cfg['alpha'])
        q = ctx.q0 if (ctx.kf is None or a_ == 0.0) else S.native_q(ctx.q0, ctx.kf, a_)
        sc = st.gate_scores(q[None, :])
        U = st.gate_keep(sc)
        kind, b = {'HG10': ('HG', 10.0), 'LAG1_10': ('LAG1', 10.0)}[mem]
        G = (ctx.mem_gate or S.src_mem_gate)(st, sc, U, kind, b)
        daily = []
        f = S.gate_facts(G[0], U[0], st, daily=daily)
        for d, rs, rr, ca in daily:
            rows.append(dict(segment=a.seg, target_id=cfg['config_id'], date=dates[d], reliant_share=rs, reliant_run_p50=rr, confirm_age_p50=ca,
                             query_id='E6M-memage'))
        nrel = sum(rs * int(G[0][st.dom.off[d]:st.dom.off[d + 1]].sum()) for d, rs, _, _ in daily if np.isfinite(rs))
        ng = max(int(G[0].sum()), 1)
        chk.append(dict(target_id=cfg['config_id'], agg_share=f['bonus_reliant_share'], daily_reconstructed_share=nrel / ng,
                        diff=abs(f['bonus_reliant_share'] - nrel / ng)))
    df = pd.DataFrame(rows, columns=['segment', 'target_id', 'date', 'reliant_share', 'reliant_run_p50', 'confirm_age_p50', 'query_id'])
    od = RL.root(a.struct, 'masks', a.seg)
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, 'memory_age_%s.csv' % a.form)
    M.atomic_write_csv(p, df)
    K = pd.DataFrame(chk)
    ok = (n_app == 0) or (bool(len(K)) and float(K['diff'].max()) <= 1e-12)     # 本形态无源记忆对象 = NOT_APPLICABLE（空表 + 回执注明），不算失败（2026-10-10）
    note = 'NOT_APPLICABLE：登记中本形态无 HG10 / LAG1_10 源记忆对象' if n_app == 0 else ''
    M.write_receipt(os.environ.get('E6M_TASK', ('S_dev_memage_%s_%s' if a.struct == 'mock' else 'S_memage_%s_%s') % (a.seg, a.form)), [p],
                    status='SUCCEEDED' if ok else 'FAILED', code=[__file__, S.__file__, M.__file__], rows=len(df), targets=len(K), applicable=n_app, note=note,
                    max_share_diff=float(K['diff'].max()) if len(K) else None, wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(seg=a.seg, form=a.form, rows=len(df), targets=len(K), max_share_diff=float(K['diff'].max()) if len(K) else None,
                          wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
