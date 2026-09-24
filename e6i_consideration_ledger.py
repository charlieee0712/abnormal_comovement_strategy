#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i consideration_ledger (brief §6 part1a 交付物; plan §4.9)。轴 -> 族 -> 成员 -> 角色 四层, 三部分:
  A  E6i 目录 276 成员: 路由到的 (路线, 角色, 母体)、描述符数、推导段结果摘要 (不按结果改状态词: 状态只描述"测了什么")
  B  E6h 登记的 U34 / NEW40 / E6H_DERIVED 键 -> 本轮覆盖方式 (源桥成员 / 同估计对象族成员 / 本轮未覆盖)
  C  考虑过但未构造的测量 (plan §4.9 与 P0 事实): 原因 = 数据 / 签名交易 / 需求不明确 —— **不是无效**
输出 reports/consideration_ledger_E6i.csv (+ _B.csv / _C.csv) 与 reports/consideration_ledger_E6i.md。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I

R = I.RES
E6H_LEDGER = os.path.join(I.E6H_RES, 'registry', 'consideration_ledger.csv')
NOT_BUILT = [
    ('K', 'Pástor–Stambaugh 回转流动性', '需日频回归到收益与签名成交量; 本轮 K 需求 (价格对活动的响应) 已由 ratio / 残差 / 价差族覆盖',
     'plan §4.9', 'no_current_mother_need'),
    ('K', 'Kyle λ（真实订单流）', '需要签名交易 / 逐笔主买主卖; 日频数据不可得', 'plan §4.9', 'data_unavailable'),
    ('V', 'tick 跳跃 / 已实现核 (realized kernel)', '需要分钟或 tick 数据; 本轮只有日 OHLC', 'plan §4.9', 'data_unavailable'),
    ('S', '概念图 / 主题共振 (东财概念)', '需要概念成分的 PIT 表; 本轮未接入', 'plan §4.9', 'data_unavailable'),
    ('R', 'DFA / Hurst 持续性', '长窗口估计在 I11 事件短窗下不稳定, 当前母体没有明确需求', 'plan §4.9', 'no_current_mother_need'),
    ('T', 'turnover_ff（自由流通股本换手）', 'P0: 数据只有流通股口径 (negMarketValue/close), 无自由流通股本字段 -> 不造',
     'source_resolution.md', 'data_unavailable'),
    ('K', 'L2 / 分钟级微观结构 (订单簿深度、分时参与率)', 'I11 事前选材框架的缺口轴; 本轮无分钟数据 (C2 只用日频 Q/ADV 代理)',
     'plan §9.2', 'data_unavailable'),
]


def md(df):
    cols = [str(c) for c in df.columns]
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, r in df.iterrows():
        out.append('| ' + ' | '.join(str(v) for v in r.values) + ' |')
    return '\n'.join(out) + '\n'


def main():
    reg = os.path.join(R, 'registry')
    sem = pd.read_csv(os.path.join(reg, 'feature_semantics_v2.csv'))
    a0 = pd.read_csv(os.path.join(reg, 'descriptors_A0.csv'), low_memory=False)
    stp = os.path.join(R, 'statistics', 'descriptor_stats_full.csv')
    stf = pd.read_csv(stp, low_memory=False) if os.path.exists(stp) else None
    # ---------------- A ----------------
    a0m = a0[a0.route_id.isin(['RT', 'RK', 'RV', 'RR', 'RO', 'RC', 'RA', 'RS', 'RL', 'TPAIR', 'FOURARM', 'M1', 'M2'])]
    ex = []
    for r in a0m[['member_id', 'route_id', 'role', 'mother_id', 'descriptor_id']].itertuples():
        for m in str(r.member_id).replace('+', '|').split('|'):
            ex.append((m, r.route_id, r.role, r.mother_id, r.descriptor_id))
    exd = pd.DataFrame(ex, columns=['member_id', 'route_id', 'role', 'mother_id', 'descriptor_id'])
    rows = []
    for m in sem.itertuples():
        e = exd[exd.member_id == m.member_id]
        rec = dict(axis=m.axis_id, family=m.family_id, estimand=m.estimand_id, member_id=m.member_id,
                   source_class=m.source_class, representative=bool(m.representative),
                   direction_primary=m.direction_primary, n_descriptors=int(e.descriptor_id.nunique()),
                   routes='|'.join(sorted(e.route_id.unique())), roles='|'.join(sorted(e.role.unique())),
                   mothers='|'.join(sorted(e.mother_id.unique())))
        if rec['n_descriptors'] == 0:
            rec['status'] = 'measured_only_stage1'
            rec['status_basis'] = 'Stage 1 全部测量层 / 预测 / 决策 / 事件 / T0 已算; A0 未给账户角色 (状态 / 诊断 / 同义桥); 未路由 != 无效'
        else:
            rec['status'] = 'routed_tested_derivation'
            rec['status_basis'] = 'A0 路由的全部角色 x 母体 x 强度 x H 已跑推导段主账户 (+ Z-MAP 随机对照)'
        if stf is not None and rec['n_descriptors']:
            s = stf[stf.descriptor_id.isin(e.descriptor_id)]
            if len(s):
                rec['d_full_median'] = float(s.d_net8_ann.median())
                rec['d_full_share_pos'] = float((s.d_net8_ann > 0).mean())
                rec['n_ci_excl0_pos'] = int((s.ci_excludes_zero & (s.d_net8_ann > 0)).sum())
                rec['n_ci_excl0_neg'] = int((s.ci_excludes_zero & (s.d_net8_ann < 0)).sum())
                if 'band_domain_lo' in s:
                    rec['n_domain_band_pos'] = int((s.band_domain_lo > 0).sum())
                    rec['n_domain_band_neg'] = int((s.band_domain_hi < 0).sum())
        rows.append(rec)
    A = pd.DataFrame(rows)
    # ---------------- B ----------------
    B = pd.DataFrame()
    if os.path.exists(E6H_LEDGER):
        e6h = pd.read_csv(E6H_LEDGER)
        keys = e6h.drop_duplicates('key')[['key', 'key_class', 'measurement_families', 'status']]
        mids = set(sem.member_id)
        brow = []
        for k in keys.itertuples():
            cand = [m for m in mids if m.upper().startswith(str(k.key).upper()) or
                    str(k.key).upper() in m.upper()]
            fam = str(k.measurement_families)
            est_hits = sem[sem.estimand_id.isin(fam.split('|'))].member_id.tolist() if fam != 'nan' else []
            if cand:
                cov, how = 'bridged_or_named', '|'.join(sorted(cand))
            elif est_hits:
                cov, how = 'covered_by_family', '|'.join(sorted(est_hits)[:6])
            else:
                cov, how = 'not_covered_this_round', ''
            brow.append(dict(e6h_key=k.key, key_class=k.key_class, e6h_status=k.status,
                             e6h_measurement_families=fam, e6i_coverage=cov, e6i_members=how))
        B = pd.DataFrame(brow)
    # ---------------- C ----------------
    C = pd.DataFrame(NOT_BUILT, columns=['axis', 'measure', 'reason', 'source', 'status'])
    od = os.path.join(R, 'reports')
    I.atomic_write_csv(os.path.join(od, 'consideration_ledger_E6i.csv'), A)
    I.atomic_write_csv(os.path.join(od, 'consideration_ledger_E6i_B_e6h_keys.csv'), B)
    I.atomic_write_csv(os.path.join(od, 'consideration_ledger_E6i_C_not_built.csv'), C)
    summ = A.groupby(['axis', 'status']).size().unstack(fill_value=0)
    lines = ['# E6i consideration_ledger（轴 → 族 → 成员 → 角色）\n',
             '三部分：A = 本轮目录 %d 个成员（研究 %d / 源桥 %d）；B = E6h 登记键 %d 个的本轮覆盖方式；'
             'C = 考虑过但未构造 %d 项（**未构造 / 未路由 ≠ 无效**）。全表见同名 csv。\n'
             % (len(A), int((A.source_class == 'RESEARCH').sum()), int((A.source_class == 'LEGACY').sum()),
                len(B), len(C)),
             '> **汇总算子**：计数 ｜ **分母及构成**：目录成员 ｜ **基准**：无 ｜ **子集**：A 部分按轴 x 状态 ｜ **单位**：个 ｜ '
             '**日期支持**：推导两段 ｜ **H**：不适用 ｜ **成本**：不适用 ｜ **支持口径**：不适用 ｜ **资本口径**：不适用\n',
             md(summ.reset_index())]
    if len(B):
        bc = B.groupby(['key_class', 'e6i_coverage']).size().unstack(fill_value=0)
        lines += ['\n> **汇总算子**：计数 ｜ **分母及构成**：E6h 登记键（去重） ｜ **基准**：无 ｜ **子集**：B 部分 ｜ **单位**：个 ｜ '
                  '**日期支持**：不适用 ｜ **H**：不适用 ｜ **成本**：不适用 ｜ **支持口径**：不适用 ｜ **资本口径**：不适用\n',
                  md(bc.reset_index())]
    lines += ['\n## C. 考虑过但未构造\n'] + ['- **%s**（%s）：%s —— %s（来源 %s）' % (r.measure, r.axis, r.status, r.reason, r.source)
                                        for r in C.itertuples()]
    open(os.path.join(od, 'consideration_ledger_E6i.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('ledger A %d / B %d / C %d' % (len(A), len(B), len(C)))


if __name__ == '__main__':
    main()
