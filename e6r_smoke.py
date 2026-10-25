# -*- coding: utf-8 -*-
"""E6r 引擎冒烟（开发期自检，不进交付）：按 registry 行建账户、全历史运行；E6Q 复现锚与 E6q B 结果逐日比对（DY 前 102 列 = E6q 列，相对 1e−9）；
其余账户打印算子活动计数。用法：python3 e6r_smoke.py <logical_id…> | --pick"""
import sys
import json
import time

import numpy as np

import e6r_core as O
import e6r_engine as E
import e6r_acct as A

KEYCOLS = ('nav_pre', 'nav_post', 'fee', 'exposure', 'net_excess', 'cash_share', 'n_hold', 'traded', 'buy_val', 'sell_val')


def build(mk, row, **kw):
    ip, fp, trig = A.spec_params(row, **kw)
    f = mk.formation(row['form'], row['memory'], w15=row['weight_scheme'] == 'UNIFORM_CAP15')
    return A.Account(mk, ip, fp, trig, f, ov=A.overlay_arrays(mk, row))


def pick(R):
    out = []
    main = (R.form == O.MAIN_FORM) & (R.memory == 'HG10') & (R.scenario == O.FEAS)
    for sch, trig, H, op in (('TILT_CVR_L050', 'NONE', '20', 'NATIVE'), ('GATE_STATE', 'NONE', '20', 'NATIVE'), ('DROP_T3', 'T1b_LEVEL', '20', 'NATIVE'),
                             ('TILT_H', 'T1a', '20', 'NATIVE'), ('UNIFORM_CAP15', 'NONE', '20', 'NATIVE'), ('TILT_SIZE_L050', 'NONE', '20', 'NATIVE'),
                             ('GATE_TILT', 'T1b_LEVEL', '20', 'NATIVE'), ('TILT_CVR5_L050', 'NONE', '20', 'NATIVE'), ('TILT_CVR_CELL_L050', 'NONE', '20', 'NATIVE'),
                             ('FLAT', 'T1b_LEVEL', '30', 'GATE_REARM_1E8'), ('FLAT', 'T1A_TIME_LEVEL_RANK', '20', 'NATIVE'), ('FLAT', 'UNION_LEVEL_T8', '20', 'NATIVE'),
                             ('TILT_CVR_L050', 'T1b_LEVEL', '20', 'EXIT_GATE_LIQ_1E8'), ('FLAT', 'NONE', '40', 'NATIVE')):
        m = main & (R.weight_scheme == sch) & (R.trigger == trig) & (R.funding_H == H) & (R.exit_op == op)
        if m.any():
            out.append(R[m].iloc[0].logical_id)
    return out


def main():
    mk = A.Market()
    R = O.read_csv(O.P('registration', 'registry_E6r.csv'))
    args = sys.argv[1:]
    lids = []
    for a in args:
        if a == '--pick':
            lids += pick(R)
        elif a == '--anchors':
            lids += list(R[R.replication_source == 'E6Q'].logical_id[:3])
        else:
            lids.append(a)
    T = mk.T
    for lid in lids:
        row = R[R.logical_id == lid].iloc[0].to_dict()
        t0 = time.time()
        acc = build(mk, row)
        acc.run(0, T)
        wall = time.time() - t0
        DY = acc.DY
        out = dict(lid=lid, scheme=row['weight_scheme'], trigger=row['trigger'], H=row['funding_H'], exit_op=row['exit_op'], wall_s=round(wall, 1),
                   nav_end=float(DY[T - 1, E.DYI['nav_post']]), ov_active_days=int((DY[:, E.DY_OVACT] > 0).sum()), ov_gated_n=int(DY[:, E.DY_OVGN].sum()),
                   ov_status_days=int((DY[:, E.DY_OVST] != 0).sum()), projf=int(acc.S_i[E.SI_PROJF]), capviol=float(DY[:, E.DY_OVCAPV].max()),
                   indviol=float(DY[:, E.DY_OVINDV].max()), na_drift=float(DY[:, E.DY_OVNAD].max()), cell_drift=float(DY[:, E.DY_OVCELLD].max()),
                   sameB=float(np.nanmax(np.abs(DY[:, E.DY_OVX] - DY[:, E.DY_OVB]) / np.maximum(DY[:, E.DY_OVB], 1.0))),
                   grprom=int(DY[:, E.DY_GRPROM].sum()), half=int(acc.S_i[E.SI_HALF]), rearm=int(acc.S_i[E.SI_REARMN]), override=int(acc.S_i[E.SI_OVERRIDE]),
                   tlr_amt_days=int((DY[:, E.DY_TLRAMT] > 0).sum()), n_intents=int(acc.S_i[E.SI_NIN]))
        if row['replication_source'] == 'E6Q':
            h = row['replication_exec_hash']
            z = np.load(O.E6Q('accounts_run', 'full', h[:2], h + '.npz'), allow_pickle=False)
            DQ = z['DY']
            worst = {}
            for k in KEYCOLS:
                i = E.DYI[k]
                a, b = DY[:T, i], DQ[:T, i]
                with np.errstate(all='ignore'):
                    rd = np.abs(a - b) / np.maximum(np.abs(b), 1.0)
                worst[k] = float(np.nanmax(rd))
            allc = np.abs(DY[:T, :102] - DQ[:T, :102]) / np.maximum(np.abs(DQ[:T, :102]), 1.0)
            out['replication_max_rel_key'] = max(worst.values())
            out['replication_max_rel_all102'] = float(np.nanmax(allc))
            out['replication_worst_col'] = E.DY_COLS[int(np.nanargmax(np.nanmax(allc, axis=0)))]
        print(json.dumps(out, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
