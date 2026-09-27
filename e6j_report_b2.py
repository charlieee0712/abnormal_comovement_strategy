# -*- coding: utf-8 -*-
"""生成 B 块的 E6j_REPORT_part1b.md（推导段随机参照 + CS / TRANSPORT / 剂量诊断）与 E6j_REPORT_part2.md（两后段：封存后读）。
  --part1b   读 results_B/descriptor_stats_<推导段>_final.csv 与 diagnostics/B/<推导段>/*.csv
  --part2    读 results_B/descriptor_stats_<后段>_final.csv（e6j_stats_b 已核封存）与推导段 final；diagnostics/B/<后段>
主读数 = α .25 × H5；随机参照 = 真实 − 各机制路径均值（R-SCORE-IID 与 R-MATCH-SRC 匹配条件相同）；MCSE 并列。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob

import numpy as np
import pandas as pd

import e6j_core as J
from e6j_report import Report

RES = J.RES


def head(**kw):
    h = dict(主体='—', 算子='FALLBACK SLOT（研究引擎）', 分母='有效配对日', 基准='同 H 研究母体', 子集='—', 单位='年化百分点', 日期='—', H='5（主配置）',
             成本模型='8bp 线性', 支持='native FALLBACK', 资本视图='NATIVE', exposure='见 source 列')
    h.update(kw)
    return h


def load(segs, tag='final'):
    x = pd.concat([pd.read_csv(os.path.join(RES, 'results_B', 'descriptor_stats_%s_%s.csv' % (s, tag))) for s in segs], ignore_index=True)
    return x


def merge_full(x, segs, col='D'):
    w = x.pivot_table(index=['descriptor_id', 'row_id', 'block', 'mother', 'slot', 'measurement_id', 'direction', 'alpha', 'H'],
                      columns='segment', values=[col, 'n'], aggfunc='first')
    w.columns = ['%s_%s' % (a, b) for a, b in w.columns]
    w = w.reset_index()
    num = sum(w['%s_%s' % (col, s)] * w['n_%s' % s] for s in segs)
    den = sum(w['n_%s' % s] for s in segs)
    w['%s_FULL' % col] = num / den
    return w


def part1b():
    segs = J.DERIV_SEGS
    x = load(segs)
    m = x[np.isclose(x.alpha, 0.25) & (x.H == 5)]
    R = Report('part1b')
    R.h(1, 'E6j REPORT part1b —— B 块推导段：随机参照与诊断（补 part1）')
    R.p('用途：part1 写成时随机参照（三类 × 1,024 路径）与 CS / TRANSPORT / 剂量诊断尚未完成，本文件补齐；对象、登记与主配置不变。'
        '随机参照 = 真实子年化净值 − 该机制路径年化净值均值（同一母体、同 α / H、同段）；R-SCORE-IID 与政策的 R-MATCH-SRC 匹配条件相同。')
    for mech, qid in (('IID', 'P1B-Q01'), ('COND', 'P1B-Q02'), ('EDIT', 'P1B-Q03')):
        c = 'rand_%s' % mech
        if c not in m.columns:
            continue
        g = m.groupby(['block', 'mother', 'segment']).agg(objects=(c, 'size'), median_real_minus_random=(c, 'median'),
                                                           share_pos=(c, lambda v: float((v > 0).mean())),
                                                           max_mcse=('mcse_%s' % mech, 'max'), min_paths=('npaths_%s' % mech, 'min'),
                                                           mc_unresolved=('mc_status_%s' % mech, lambda v: int((v == 'MC_UNRESOLVED').sum()))).reset_index()
        R.h(2, '%s：真实 − 随机均值（主配置，按块 × 母体 × 段）' % mech)
        R.table(g, head(主体='B 包全部对象', 算子='真实 − %s 路径均值；mc_unresolved = |真实 − 随机均值| < 2·MCSE 的对象数（符号未定）' % mech,
                        子集='推导段 %s' % ' / '.join(segs), 日期='2010-01-04..2018-12-31'), qid)
    p = os.path.join(RES, 'results_B', 'part1b_main_config_random_refs.csv')
    J.atomic_write_csv(p, m[['segment', 'block', 'mother', 'slot', 'measurement_id', 'direction', 'D'] +
                            [c for c in m.columns if c.startswith(('rand_', 'mcse_', 'npaths_'))]])
    R.p('逐对象（主配置）的三类随机参照写在 `results_B/part1b_main_config_random_refs.csv`〔P1B-Q01–Q03〕。')
    dg = [p for s in segs for p in sorted(glob.glob(os.path.join(RES, 'diagnostics', 'B', s, '*.csv')))]
    if dg:
        d = pd.concat([pd.read_csv(p) for p in dg], ignore_index=True)
        cs = d[(d['diag'] == 'CS') & (d.H == 5)]
        R.h(2, 'COMMON_SUPPORT 四账户闭合（α .25 × H5；按块汇总）')
        R.table(cs.groupby(['block', 'mother']).agg(objects=('N1_minus_N0', 'size'), N1_minus_N0=('N1_minus_N0', 'median'),
                                                    C1_minus_C0=('C1_minus_C0', 'median'), C0_minus_N0=('C0_minus_N0', 'median'),
                                                    N1_minus_C1=('N1_minus_C1', 'median'), max_abs_closure=('closure_resid', lambda v: float(np.abs(v).max())),
                                                    J_share=('J_share', 'median')).reset_index(),
                head(主体='B 包对象（按块 × 母体中位）', 算子='N1−N0 = (C1−C0)+(C0−N0)+(N1−C1)；后两项含中性化 / 排序 / 资本 / 费用变化，不是缺失的因果效应',
                     支持='COMMON_SUPPORT（J 上重做中性化与排名）', 子集='推导段', 日期='2010-01-04..2018-12-31'), 'P1B-Q04')
        tr = d[d['diag'].str.startswith('TR_')]
        R.h(2, 'SRC vs TRANSPORT（S / M / MA3 主配置）')
        R.table(tr, head(主体='S_source / SLOPE20_TR_CC / MR3_TR_CC × 母体', 算子='SRC 秩坐标 vs TRANSPORT（J 内把 q0 有序值按新坏度分配）', 子集='推导段',
                         日期='2010-01-04..2018-12-31'), 'P1B-Q05')
        do = d[d['diag'] == 'DOSE']
        R.h(2, 'B3-C 剂量控制（可靠性 vs COMMON-DOSE vs r-shuffle）')
        R.table(do, head(主体='J_M_reliable（CC / ID）× 母体 × α', 算子='可靠性收缩 / 同日同有效域平均 r / r 在同日旧 K 三档内按五日优先序置换（1,024 路径，固定 qM）',
                         子集='推导段', 日期='2010-01-04..2018-12-31'), 'P1B-Q06')
    out = os.path.join(RES, 'reports', 'E6j_REPORT_part1b.md')
    sha = R.write(out)
    J.write_receipt('report_part1b', [out, p], 'SUCCEEDED', n_tables=len(R.qids))
    print('part1b', sha[:12])


def part2():
    post, der = J.POST_SEGS, J.DERIV_SEGS
    xp = load(post); xd = load(der)
    wp = merge_full(xp, post); wd = merge_full(xd, der)
    key = ['descriptor_id', 'row_id', 'block', 'mother', 'slot', 'measurement_id', 'direction', 'alpha', 'H']
    w = wp.merge(wd[key + ['D_FULL'] + ['D_%s' % s for s in der] + ['n_%s' % s for s in der]].rename(columns={'D_FULL': 'D_FULL_deriv'}), on=key, how='left')
    w = w.rename(columns={'D_FULL': 'D_FULL_post'})
    n_all = sum(w['n_%s' % s] for s in J.SEGMENTS)
    w['D_FULL_all4'] = sum(w['D_%s' % s] * w['n_%s' % s] for s in J.SEGMENTS) / n_all
    m = w[np.isclose(w.alpha, 0.25) & (w.H == 5)]
    R = Report('part2')
    R.h(1, 'E6j REPORT part2 —— B 块两后段（记录 B 事前整表授权后，封存回执后读）')
    R.p('用途：B 包冻结清单全部对象在 2019-2023 / 2024-2026 两后段的原生 FALLBACK 账户、同日配对、随机参照、同资本与含冲击读数（plan §10.7）。'
        '后段在记录 B 生效条件核验（2026-09-27 04:23:40 三条全过）之后一次算完、封存（`registration/seal_B_post.json`）后读取。'
        '未批准集合 = 空（方式 B 整表授权，对象集合 = 冻结清单）。')
    g = m.groupby(['block', 'mother']).agg(objects=('D_FULL_post', 'size'), median_deriv=('D_FULL_deriv', 'median'), median_post=('D_FULL_post', 'median'),
                                           median_all4=('D_FULL_all4', 'median'),
                                           post_both_pos=('D_FULL_post', lambda v: 0)).reset_index()
    bp = m.assign(bp=(m['D_%s' % post[0]] > 0) & (m['D_%s' % post[1]] > 0)).groupby(['block', 'mother']).bp.sum().reset_index()
    g = g.drop(columns='post_both_pos').merge(bp.rename(columns={'bp': 'post_both_segments_pos'}), on=['block', 'mother'])
    R.table(g, head(主体='B 包全部对象（块 × 母体）', 子集='主配置 α .25 × H5；推导 / 后段 / 四段合并', 日期='2010-01-04..2026-03-27'), 'P2-Q01')
    p = os.path.join(RES, 'results_B', 'part2_main_config_all_objects.csv')
    J.atomic_write_csv(p, m.sort_values(['block', 'measurement_id', 'direction', 'mother']))
    R.p('全部对象主配置的四段读数写在 `results_B/part2_main_config_all_objects.csv`；全网格在 `results_B/descriptor_stats_<段>_final.csv`〔P2-Q01〕。')
    for mech, qid in (('IID', 'P2-Q02'), ('COND', 'P2-Q03'), ('EDIT', 'P2-Q04')):
        c = 'rand_%s' % mech
        mm = xp[np.isclose(xp.alpha, 0.25) & (xp.H == 5)]
        if c not in mm.columns:
            continue
        gg = mm.groupby(['block', 'mother', 'segment']).agg(objects=(c, 'size'), median_real_minus_random=(c, 'median'),
                                                             share_pos=(c, lambda v: float((v > 0).mean())), max_mcse=('mcse_%s' % mech, 'max'),
                                                             mc_unresolved=('mc_status_%s' % mech, lambda v: int((v == 'MC_UNRESOLVED').sum()))).reset_index()
        R.h(2, '%s 随机参照（后段）' % mech)
        R.table(gg, head(主体='B 包全部对象', 算子='真实 − %s 路径均值；mc_unresolved = |真实 − 随机均值| < 2·MCSE 的对象数（符号未定）' % mech,
                         子集='后段', 日期='2019-01-02..2026-03-27'), qid)
    cv = xp[np.isclose(xp.alpha, 0.25) & (xp.H == 5)].groupby(['block', 'segment']).agg(native=('D', 'median'), same_capital=('D_sc', 'median'),
                                                                                         impact_A5k05=('D_imp', 'median'), impact_A10k1=('D_str', 'median'),
                                                                                         bp6=('D_6bp', 'median'), bp12=('D_12bp', 'median')).reset_index()
    R.h(2, '资本与成本视图（后段，按块中位）')
    R.table(cv, head(主体='B 包主配置对象', 资本视图='NATIVE / MATCH-CAP', 成本模型='8bp；6 / 12bp；A5 κ.5 / A10 κ1 平方根冲击', 日期='2019-01-02..2026-03-27'),
            'P2-Q05')
    R.h(2, '推导段 → 后段（同一对象、主配置）')
    t = m.assign(deriv_pos=m.D_FULL_deriv > 0, post_pos=m.D_FULL_post > 0).groupby(['block', 'deriv_pos', 'post_pos']).size().reset_index(name='objects')
    R.table(t, head(主体='B 包全部对象', 算子='推导合并与后段合并的符号交叉计数', 单位='对象数', 日期='2010-01-04..2026-03-27'), 'P2-Q06')
    bf = os.path.join(RES, 'results_B', 'simultaneous_bands_B.csv')
    if os.path.exists(bf):
        b = pd.read_csv(bf)
        R.h(2, '同时带（plan §8.4 第二层：每个研究块；第三层：全部 B 主配置）')
        rows = []
        for blk, x in b.groupby('block'):
            r = dict(block=blk, objects=len(x))
            for L in (20, 60):
                r.update({'block_q95_L%d' % L: float(x['block_maxt_q95_L%d' % L].iloc[0]), 'allB_q95_L%d' % L: float(x['allB_maxt_q95_L%d' % L].iloc[0]),
                          'point_excl0_L%d' % L: int(((x['point_lo_L%d' % L] > 0) | (x['point_hi_L%d' % L] < 0)).sum()),
                          'block_band_excl0_L%d' % L: int(((x['block_simul_lo_L%d' % L] > 0) | (x['block_simul_hi_L%d' % L] < 0)).sum()),
                          'allB_band_excl0_L%d' % L: int(((x['allB_simul_lo_L%d' % L] > 0) | (x['allB_simul_hi_L%d' % L] < 0)).sum())})
            rows.append(r)
        R.table(pd.DataFrame(rows), head(主体='B 包主配置对象（α .25 × H5，全部母体与方向）', 算子='平稳块自助（与 P 包同一日期 draw，块均长 20 / 60，2,000 次）的 max-t 同时带；'
                                                                                   'SE = bootstrap sd；零 sd 列不入族', 单位='分位 / 对象数（区间不含 0 的计数，只描述，不作门）',
                                         日期='2010-01-04..2026-03-27（四段合并 FULL）'), 'P2-Q07')
        R.p('逐对象的逐点区间与两层同时带在 `results_B/simultaneous_bands_B.csv`；同时带与逐点区间、δ 政策、全窗口点估并列，不设新的 FWER 通过门〔P2-Q07〕。')
    out = os.path.join(RES, 'reports', 'E6j_REPORT_part2.md')
    sha = R.write(out)
    J.write_receipt('report_part2', [out, p], 'SUCCEEDED', n_tables=len(R.qids))
    print('part2', sha[:12])


if __name__ == '__main__':
    if '--part1b' in sys.argv:
        part1b()
    if '--part2' in sys.argv:
        part2()
