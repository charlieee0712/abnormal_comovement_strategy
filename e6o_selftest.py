# -*- coding: utf-8 -*-
"""E6o 引擎工程自测（S0-2 / S0-8 / S0-11 的工程部分；不读任何退出账户的后段收益）：
① 主母体 P_ACCOUNT（FEASIBLE / IDEAL）全程：现金方程、NAV 伸缩、耗时；② 开退出引擎但零触发 ≡ P_ACCOUNT（NOEXIT_EQ_PARENT，全程）；
③ 主对象 C_ACCOUNT 只跑推导段（< 2019-01-01）：恒等、标签守恒、计数；④ checkpoint：推导段中点存 → 新对象恢复 → 续跑与一次跑完逐项一致。
输出只含恒等差、计数与耗时（后段 C 账户不跑）。用法：python3 e6o_selftest.py"""
import os
import sys
import json
import time

import numpy as np

import e6o_core as O
import e6o_engine as E
import e6o_acct as A


def ident(acc, d0, d1, V0=1e8):
    DY = acc.DY[d0:d1]
    navd = float(np.max(np.abs(DY[:, 0] - DY[:, 2] - DY[:, 1])))
    r = DY[:, 9]
    tele = float(np.prod(1.0 + r)) - DY[-1, 1] / (V0 if d0 == 0 else acc.DY[d0 - 1, 1])
    return dict(nav_identity_maxabs=navd, telescope_rel=float(abs(tele)), min_cash_share=float(DY[:, 6].min()), err=int(acc.S_i[E.SI_ERR]))


def main():
    t0 = time.time()
    mk = A.Market()
    T = mk.T
    d19 = int(np.searchsorted(mk.dates, '2019-01-01'))
    f = mk.formation(O.MAIN_FORM, 'HG10')
    u = mk.gate_u(O.MAIN_FORM)
    nx = mk.next_order('HG10')
    out = dict(T=T, d19=d19, f_nnz=int(len(f[1])), gate_nnz=int(len(u[1])), next_nnz=int(len(nx[1])), load_s=round(time.time() - t0, 1))
    res = {}
    for prof, ideal in (('FEASIBLE', False), ('IDEAL', True)):
        ip, fp = A.ip_fp(5, E.TM_NONE, fund=E.FD_NONE, ideal=ideal)
        t1 = time.time()
        p = A.Account(mk, ip, fp, None, f).run(0, T)
        out['parent_%s_s' % prof] = round(time.time() - t1, 2)
        out['parent_%s_ident' % prof] = ident(p, 0, T)
        res[prof] = p
        # NOEXIT：开退出引擎、零触发、NATIVE / BLOCK
        ip2, fp2 = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, reentry=E.RE_BLOCK, exit_on=True, ideal=ideal)
        z = A.Account(mk, ip2, fp2, None, f, u_csr=u).run(0, T)
        out['noexit_%s_maxabs' % prof] = float(np.nanmax(np.abs(z.DY[:, :E.NDY] - p.DY[:, :E.NDY])))
    # P_SOURCE 主父对照（全程逐段 net，ann_pp）
    seg_net = {}
    for s in O.SEGS:
        zz = mk.source(s)
        v = zz['src_net8|%s|HG10|H5' % O.MAIN_FORM]
        seg_net[s] = float(np.nanmean(v) * O.ANN_PP)
    out['P_SOURCE_main_net_ann_pp'] = seg_net
    pa = res['FEASIBLE']
    segi = np.array([O.seg_of_date(d) for d in mk.dates])
    out['P_ACCOUNT_FEAS_main_net_ann_pp'] = {s: float(np.nanmean(pa.DY[segi == s, 5]) * O.ANN_PP) for s in O.SEGS}
    out['P_ACCOUNT_IDEAL_main_net_ann_pp'] = {s: float(np.nanmean(res['IDEAL'].DY[segi == s, 5]) * O.ANN_PP) for s in O.SEGS}
    out['P_ACCOUNT_FEAS_exposure_mean'] = {s: float(np.mean(pa.DY[segi == s, 3])) for s in O.SEGS}
    # ③ 主对象推导段
    ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, reentry=E.RE_ALLOW, exit_on=True)
    t1 = time.time()
    c = A.Account(mk, ip, fp, 'T1b', f, u_csr=u).run(0, d19)
    out['child_deriv_s'] = round(time.time() - t1, 2)
    out['child_ident'] = ident(c, 0, d19)
    st = c.IN_i[:int(c.S_i[E.SI_NIN]), E.IN_STATUS]
    out['child_intents'] = int(c.S_i[E.SI_NIN])
    out['child_status_counts'] = {int(k): int(v) for k, v in zip(*np.unique(st, return_counts=True))}
    out['child_err'] = int(c.S_i[E.SI_ERR])
    out['child_internal'] = int(c.S_i[E.SI_INTERNAL])
    out['child_reentry'] = int(c.S_i[E.SI_REENTRY])
    # ④ checkpoint：中点存 → 恢复 → 续跑
    mid = d19 // 2
    a1 = A.Account(mk, ip, fp, 'T1b', f, u_csr=u).run(0, mid)
    pth = O.P('tmp', 'selftest_ckpt.npz')
    a1.checkpoint(pth, dict(test='selftest', mid=mid))
    a2 = A.Account(mk, ip, fp, 'T1b', f, u_csr=u)
    a2.restore(pth)
    a2.run(mid, d19)
    out['ckpt_DY_maxabs'] = float(np.nanmax(np.abs(a2.DY[:d19] - c.DY[:d19])))
    out['ckpt_state_equal'] = bool(np.array_equal(a2.L_f[:int(a2.S_i[E.SI_NL])], c.L_f[:int(c.S_i[E.SI_NL])]))
    out['wall_s'] = round(time.time() - t0, 1)
    print(json.dumps(out, ensure_ascii=False, default=str, indent=1), flush=True)


if __name__ == '__main__':
    main()
