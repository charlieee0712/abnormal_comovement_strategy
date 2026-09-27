# -*- coding: utf-8 -*-
"""E6j carried（brief v1.2 §10；plan §7.7）：
  --leader   领导六形态资本分解（生产 v2 六母体 × 四段，H5，8bp；另印 6bp 列供对 E5a）：名义投入资金（目标权重和）、实际仓位、
             单位资金 gross / net（只在仓位 > 0 日定义）、总 gross / net、目标持股数、年化换手、费用。措辞"投入资金上升"。对外须用户过目。
  --e04      E04 补记（E6i RULING 第 17 项）：random_state 焦点臂两次抽样（Stage 2 账户 vs carried C2 子账户）的分段中位比较与 part1 Q4 句复核；不重跑。
  --signal   信号线：只复用 E6i C3 signal_margin_profile 描述面板（不建新阈值账户），写出处与文件 sha。
输出 carried/。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob
import json

import numpy as np
import pandas as pd

import e6j_core as J

OUT = os.path.join(J.RES, 'carried')
E6I = J.E6I_RES


def leader():
    rows = []
    for seg in J.SEGMENTS:
        for form in ('A4b', 'M_mean3_v2', 'M_union3_v2', 'A4b_CVRv5', 'M_mean3_v2_CVRv5', 'M_union3_v2_CVRv5'):
            z = np.load(os.path.join(J.RES, 'accounts', 'P', seg, '%s.npz' % form), allow_pickle=False)
            i = list(z['desc']).index('P|%s|C0|-|-|a=0|H5' % form)
            g, pos, tu, n8, ws, nn = z['gross'][i], z['pos'][i], z['turn'][i], z['net8'][i], z['wsum'][i], z['nnames'][i]
            act = pos > 0
            fee8 = tu * 8e-4
            rows.append(dict(segment=seg, form=form, invested_target_mean=float(ws[ws > 0].mean()), position_actual_mean=float(pos.mean()),
                             unit_gross_ann=float(np.nanmean(g[act] / pos[act])) * J.ANN, unit_net8_ann=float(np.nanmean(n8[act] / pos[act])) * J.ANN,
                             total_gross_ann=float(np.nanmean(g)) * J.ANN, total_net8_ann=float(np.nanmean(n8)) * J.ANN,
                             total_net6_ann=float(np.nanmean(g - tu * 6e-4)) * J.ANN, target_names_mean=float(nn[nn > 0].mean()),
                             turnover_ann=float(tu.sum() / (len(tu) / 252.0)), fee8_ann=float(np.nanmean(fee8)) * J.ANN,
                             days=len(g), active_days=int(act.sum())))
    df = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, 'leader_six_forms_capital.csv'); J.atomic_write_csv(p, df)
    J.write_receipt('carried_leader', [p], 'SUCCEEDED', n=len(df), note='对外数字须用户过目')
    return 0


def e04():
    rows = []
    c2 = pd.read_csv(os.path.join(E6I, 'carried', 'summary', 'C2_children_delta.csv'))
    for seg in J.SEGMENTS:
        m = pd.read_csv(os.path.join(E6I, 'accounts', seg, 'merged_RO.csv'))
        rs = pd.read_csv(os.path.join(E6I, 'accounts', seg, 'merged_RS.csv')) if os.path.exists(os.path.join(E6I, 'accounts', seg, 'merged_RS.csv')) else None
        acc = pd.concat([m] + ([rs] if rs is not None else []), ignore_index=True)
        acc = acc[acc.strength == 'random_state']
        d2 = c2[(c2.segment == seg)].set_index('descriptor_id')['d_net8_ann']
        acc = acc.assign(draw2=acc.descriptor_id.map(d2))
        for (route, drole), g in acc.groupby(['route_id', 'direction_role']):
            rows.append(dict(segment=seg, route=route, direction_role=drole, n=len(g), median_draw1_stage2=float(g.d_net8_ann.median()),
                             median_draw2_carried=float(g.draw2.median()), n_equal=int((np.abs(g.d_net8_ann - g.draw2) <= 1e-12).sum()),
                             max_abs_diff=float(np.abs(g.d_net8_ann - g.draw2).max())))
    df = pd.DataFrame(rows)
    # part1 Q4 句复核（推导段；RO FOCAL_NEW random_state vs real_state 中位）
    chk = []
    for seg in J.DERIV_SEGS:
        m = pd.read_csv(os.path.join(E6I, 'accounts', seg, 'merged_RO.csv'))
        m = m[m.role == 'FOCAL_NEW']
        d2 = c2[c2.segment == seg].set_index('descriptor_id')['d_net8_ann']
        for drole in ('gap_neg', 'gap_pos'):
            real = m[(m.strength == 'real_state') & (m.direction_role == drole)].d_net8_ann.median()
            r1 = m[(m.strength == 'random_state') & (m.direction_role == drole)].d_net8_ann.median()
            r2 = m[(m.strength == 'random_state') & (m.direction_role == drole)].descriptor_id.map(d2).median()
            chk.append(dict(segment=seg, direction_role=drole, real_state_median=float(real), random_draw1_median=float(r1),
                            random_draw2_median=float(r2), real_not_better_draw1=bool(real <= r1), real_not_better_draw2=bool(real <= r2)))
    os.makedirs(OUT, exist_ok=True)
    p1 = os.path.join(OUT, 'E04_two_draws.csv'); J.atomic_write_csv(p1, df)
    p2 = os.path.join(OUT, 'E04_part1_Q4_recheck.csv'); J.atomic_write_csv(p2, pd.DataFrame(chk))
    J.write_receipt('carried_e04', [p1, p2], 'SUCCEEDED', note='不重跑；E6i 随机臂种子 = abs(hash(descriptor_id))，未设 PYTHONHASHSEED')
    return 0


def signal():
    cand = sorted(glob.glob(os.path.join(E6I, 'reports', 'R0_tables', '*signal*'))) + sorted(glob.glob(os.path.join(E6I, 'carried', '*', '*signal*')))
    rows = [dict(file=os.path.relpath(p, E6I), sha256=J.sha_file(p)) for p in cand if os.path.isfile(p)]
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, 'signal_panel_reuse.csv'); J.atomic_write_csv(p, pd.DataFrame(rows))
    J.write_receipt('carried_signal', [p], 'SUCCEEDED', n=len(rows), note='只复用 E6i C3 描述面板，不建新阈值账户')
    return 0


if __name__ == '__main__':
    a = sys.argv
    if '--leader' in a:
        sys.exit(leader())
    if '--e04' in a:
        sys.exit(e04())
    if '--signal' in a:
        sys.exit(signal())
