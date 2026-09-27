# -*- coding: utf-8 -*-
"""生成 E6j_REPORT_part1.md（plan §10.7：B 推导段、完整负结果、源 / 新表示、Q 初读、A1 与记录 B 清单）。
只读推导段（2010-2014 / 2015-2018）的 B 统计；随机参照（1,024 路径）未完成，本文件不引用任何随机列（part1b 补）。
所有数字由本文件的结构化查询产生；主读数 = 事前主配置 α .25 × H5；网格只作标明探索。"""
import e6j_boot  # noqa: F401
import os
import sys
import json

import numpy as np
import pandas as pd

import e6j_core as J
from e6j_report import Report

RES = J.RES
OUT = os.path.join(RES, 'reports', 'E6j_REPORT_part1.md')
DS = J.DERIV_SEGS


def load():
    st = pd.concat([pd.read_csv(os.path.join(RES, 'results_B', 'descriptor_stats_%s.csv' % s)) for s in DS], ignore_index=True)
    keep = [c for c in st.columns if not c.startswith(('rand_', 'mcse_', 'npaths_'))]
    st = st[keep]
    w = st.pivot_table(index=['descriptor_id', 'row_id', 'block', 'mother', 'slot', 'measurement_id', 'direction', 'alpha', 'H'],
                       columns='segment', values=['D', 'n', 'D_sc', 'D_imp', 'turn_rel', 'cells_changed'], aggfunc='first')
    w.columns = ['%s_%s' % (a, b) for a, b in w.columns]
    w = w.reset_index()
    n1, n2 = w['n_%s' % DS[0]], w['n_%s' % DS[1]]
    for k in ('D', 'D_sc', 'D_imp'):
        w['%s_FULL' % k] = (w['%s_%s' % (k, DS[0])] * n1 + w['%s_%s' % (k, DS[1])] * n2) / (n1 + n2)
    return st, w


def head(**kw):
    h = dict(主体='—', 算子='FALLBACK SLOT（研究引擎）', 分母='推导两段有效配对日', 基准='同 H 研究母体（R1 / R2 / A06 / A08）', 子集='推导段 2010-2014 / 2015-2018',
             单位='子 − 母 8bp 日配对增量，年化百分点', 日期='2010-01-04..2018-12-31', H='5（主配置）', 成本模型='8bp 线性', 支持='native FALLBACK',
             资本视图='NATIVE', exposure='见表内 source 列')
    h.update(kw)
    return h


def main():
    st, w = load()
    rows = pd.read_csv(os.path.join(RES, 'registry', 'rows_B.csv'))
    a1 = json.load(open(os.path.join(RES, 'registration', 'a1_auto.json')))
    main_ = w[np.isclose(w.alpha, 0.25) & (w.H == 5)].copy()
    main_ = main_.merge(rows[['row_id', 'source', 'direction_role', 'hypothesis_ids']], on='row_id', how='left')
    R = Report('part1')
    R.h(1, 'E6j REPORT part1 —— B 块推导段（K 分离研究）')
    R.p('用途：B 包推导两段（2010-2014 / 2015-2018）的原生 FALLBACK 账户读数、完整负结果、源 / 新表示对照、Q 初读、A1-auto 与记录 B 清单（plan §10.7）。'
        '**随机参照（三类 × 1,024 路径）尚未完成，本文件不引用任何随机列**，在 part1b 补；后段账户在本文件写完之后才按记录 B 生效条件计算。')
    R.p('读法：每个对象 = 登记行（测量 × 方向 × 槽位）× 母体；主读数固定 α .25 × H5；"合并"= 两推导段按有效配对日合并（W07 同式）；'
        '网格（α × H 共 21 格）只作标明探索，不进结论句。一个登记行在三个母体上各是一个对象，不取跨母体中位代替对象读数（plan §4.5）。')

    # ---- 0 总览
    R.h(2, '0. 总览（主配置）')
    g = main_.groupby(['block', 'mother']).agg(objects=('D_FULL', 'size'), median_FULL=('D_FULL', 'median'),
                                                  both_pos=('D_FULL', lambda x: 0), p10=('D_FULL', lambda x: x.quantile(.1)),
                                                  p90=('D_FULL', lambda x: x.quantile(.9))).reset_index()
    bp = main_.assign(bp=(main_['D_%s' % DS[0]] > 0) & (main_['D_%s' % DS[1]] > 0),
                      bn=(main_['D_%s' % DS[0]] < 0) & (main_['D_%s' % DS[1]] < 0)).groupby(['block', 'mother'])[['bp', 'bn']].sum().reset_index()
    g = g.drop(columns='both_pos').merge(bp, on=['block', 'mother'])
    g = g.rename(columns={'bp': 'both_segments_pos', 'bn': 'both_segments_neg'})
    R.table(g, head(主体='B 包全部对象（块 × 母体）', 子集='推导两段；主配置 α .25 × H5', exposure='含 E6i 源成员与 K0 锚'), 'P1-Q01')
    R.p('计数口径：both_segments_pos / neg = 两推导段增量同为正 / 负的对象数；对象总数 %d（= 202 行 × 3 母体 + 8 行 × 4 母体）〔P1-Q01〕。' % len(main_))

    # ---- 1 完整结果（主配置）
    R.h(2, '1. 全部对象（主配置；完整负结果照列）')
    full = main_[['block', 'mother', 'slot', 'measurement_id', 'direction', 'direction_role', 'source', 'D_%s' % DS[0], 'D_%s' % DS[1], 'D_FULL',
                  'D_sc_FULL', 'D_imp_FULL', 'turn_rel_%s' % DS[1], 'cells_changed_%s' % DS[1], 'hypothesis_ids']].sort_values(
        ['block', 'measurement_id', 'direction', 'mother'])
    p = os.path.join(RES, 'results_B', 'part1_main_config_all_objects.csv'); J.atomic_write_csv(p, full)
    R.p('全部 %d 个对象的主配置读数写在 `results_B/part1_main_config_all_objects.csv`（逐对象：两段增量、合并、同资本合并、含冲击 A5 κ.5 合并、Δturn、改动格数）；'
        '全部 21 格网格写在 `results_B/descriptor_stats_<段>.csv`〔P1-Q02〕。下表按块给出每块 D_FULL 最低与最高的 3 个对象，负结果与正结果同样列出。' % len(full))
    ext = []
    for b, x in full.groupby('block'):
        x = x.sort_values('D_FULL')
        ext.append(x.head(3)); ext.append(x.tail(3))
    R.table(pd.concat(ext)[['block', 'mother', 'slot', 'measurement_id', 'direction', 'D_%s' % DS[0], 'D_%s' % DS[1], 'D_FULL']],
            head(主体='每块主配置 D_FULL 最低 / 最高各 3 个对象（完整表见 CSV）'), 'P1-Q02')

    # ---- 2 Q 初读
    R.h(2, '2. 问题卡初读（主配置；同母体配对；不设门）')
    def comp(block_filter, qid, title, ref=None):
        x = main_[block_filter].copy()
        if ref is not None:
            r = main_[ref].set_index('mother')['D_FULL']
            x['minus_ref_FULL'] = x.D_FULL - x.mother.map(r)
        cols = ['mother', 'slot', 'measurement_id', 'direction', 'direction_role', 'D_%s' % DS[0], 'D_%s' % DS[1], 'D_FULL'] + (['minus_ref_FULL'] if ref is not None else [])
        R.h(3, title)
        R.table(x[cols].sort_values(['mother', 'measurement_id', 'direction']), head(主体=title), qid)
    comp(main_.block == 'B1', 'P1-Q03', 'Q02 / Q03：B1 分量（b / a / q / a×q / 60 日基线 / log）与源 S（K_rar20 低坏）',
         ref=(main_.block == 'B1') & (main_.measurement_id == 'K_rar20'))
    comp((main_.block == 'B2') & main_.measurement_id.str.contains('SLOPE20') | (main_.block == 'B3B'), 'P1-Q04',
         'Q04：M 的尺度分解（β_norm / ρ / scale）与 SLOPE20 各价格口径')
    comp(main_.block == 'B3C', 'P1-Q05', 'Q05：可靠性收缩 J_M_reliable（CC / ID）',
         ref=(main_.block == 'B2') & (main_.measurement_id == 'J_B2_SLOPE20_TR_CC') & (main_.direction == 'low_bad'))
    comp(main_.block == 'B3A', 'P1-Q06', 'Q06：聚合协动 λ ∈ {0, .5, 1} 与 COV/P')
    b2 = main_[(main_.block == 'B2') & (main_.direction_role == 'main')].copy()
    b2['agg'] = b2.measurement_id.str.split('_').str[2]; b2['unit'] = b2.measurement_id.str.split('_').str[3]; b2['price'] = b2.measurement_id.str.split('_').str[4]
    piv = b2.pivot_table(index=['mother', 'agg', 'unit'], columns='price', values='D_FULL').reset_index()
    R.h(3, 'Q10：价格时段（CC / ID / RANGE / ON）× 聚合 × 单位（主方向）')
    R.table(piv, head(主体='B2 主方向对象', 单位='D_FULL 年化百分点（列 = 价格口径）'), 'P1-Q07')
    comp(main_.block == 'B4', 'P1-Q08', 'Q11：涨跌分解（ROS / MR × UP / DN × CC / ID）与 asym')
    b5 = main_[main_.block == 'B5'].copy()
    b5['stat'] = b5.measurement_id.str.split('_').str[2]; b5['price'] = b5.measurement_id.str.split('_').str[3]
    b5['W'] = b5.measurement_id.str.split('_').str[4]; b5['clock'] = b5.measurement_id.str.split('_').str[5]
    R.h(3, 'Q12 / Q03：事件基线（RARPRE / R_ev / R_ev5 / U × CC / ID × W20 / 60 × 时钟）')
    R.table(b5.pivot_table(index=['mother', 'stat', 'direction'], columns=['price', 'W', 'clock'], values='D_FULL').round(4).reset_index()
            .set_axis(['mother', 'stat', 'direction'] + ['%s_%s_%s' % c for c in b5.pivot_table(index=['mother', 'stat', 'direction'],
                                                                                                  columns=['price', 'W', 'clock'], values='D_FULL').columns], axis=1),
            head(主体='B5 全部对象', 单位='D_FULL 年化百分点'), 'P1-Q09')
    comp(main_.block == 'B6', 'P1-Q10', 'Q14：T 窄种子（T 槽位；含 A08）')
    comp(main_.block == 'B7', 'P1-Q11', 'Q14：同业相对位置（K / T 两位置分域）')

    # ---- 3 源 / 新表示
    R.h(2, '3. 源表示与本轮新表示（同母体、主配置）')
    pairs = [('K_rar20', 'low_bad', 'J_B1_S20lag', 'low_bad', '源 S（E6i 缓存，最少观测 14）vs J 自包含版（最少 10；代数同式）'),
             ('J_B2_POINT_TR_CC', 'high_bad', None, None, 'K0 锚（J 原值 = K0 逐位 → 账户 = 母体，增量应为 0）')]
    t = []
    for a_, da, b_, db, note in pairs:
        for mo in ('R1', 'R2', 'A06'):
            xa = main_[(main_.measurement_id == a_) & (main_.direction == da) & (main_.mother == mo)]
            if not len(xa):
                continue
            row = dict(mother=mo, object_a='%s|%s' % (a_, da), FULL_a=float(xa.D_FULL.iloc[0]), note=note)
            if b_:
                xb = main_[(main_.measurement_id == b_) & (main_.direction == db) & (main_.mother == mo)]
                row.update(object_b='%s|%s' % (b_, db), FULL_b=float(xb.D_FULL.iloc[0]), a_minus_b=float(xa.D_FULL.iloc[0] - xb.D_FULL.iloc[0]))
            t.append(row)
    R.table(pd.DataFrame(t), head(主体='源 / 新表示配对'), 'P1-Q12')

    # ---- 4 资本与成本视图
    R.h(2, '4. 同资本与含冲击（主配置，按块汇总）')
    cv = main_.groupby('block').agg(native_median=('D_FULL', 'median'), same_capital_median=('D_sc_FULL', 'median'),
                                    impact_A5k05_median=('D_imp_FULL', 'median'),
                                    sign_agree_share=('D_FULL', lambda x: 0)).reset_index()
    agree = main_.assign(a=np.sign(main_.D_FULL) == np.sign(main_.D_sc_FULL)).groupby('block').a.mean().reset_index()
    cv = cv.drop(columns='sign_agree_share').merge(agree.rename(columns={'a': 'native_vs_samecap_sign_agree_share'}), on='block')
    R.table(cv, head(主体='B 包主配置对象（按块）', 资本视图='NATIVE / MATCH-CAP（逐形成日共同资本只缩不放）', 成本模型='8bp；另列 A=5 亿 κ=.5 平方根冲击'),
            'P1-Q13')

    # ---- 5 A1 与记录 B
    R.h(2, '5. A1-auto 与记录 B 清单')
    R.table(pd.DataFrame(a1['items']), head(主体='A1-auto 七项', 算子='机械对账', 单位='PASS / FAIL', 子集='全部登记对象', 日期='—', H='—', 成本模型='—',
                                            支持='—', 资本视图='—'), 'P1-Q14')
    R.p('记录 B 草稿：`reports/E6j_record_B_draft.md` 与 `registration/record_B_draft_objects.csv`（%d 个对象，逐对象 source exposure / 机制重要性 / 有效支持 / 推导读数 / 未解决限制）。'
        '方式 B 事前整表授权下，后段对象 = 冻结清单全部对象，不按推导读数增删〔P1-Q14〕。' % (len(main_)))
    R.h(2, '6. 限制与待补')
    R.p('- 随机参照三类（R-SCORE-IID / R-COND / EDIT-ENTRY，1,024 路径起）与 COMMON_SUPPORT 四账户、TRANSPORT、剂量控制（B3-C）在 part1b 补；本文件的读数都是"子 − 母"原生增量。')
    R.p('- 一个 2010-2014 R2 × B3C 的 32 路径随机分片是测时样本，其路径作为该配置 1,024 路径中的前 32 条保留，不单独读数。')
    R.p('- 两推导段已在 E6i 中暴露于同源母体的成员选择（exposure：`registration/selection_exposure_ledger.csv`）；推导段读数不是样本外证据。')
    sha = R.write(OUT)
    J.write_receipt('report_part1', [OUT, p], 'SUCCEEDED', n_tables=len(R.qids))
    print('part1 written', sha[:12], len(R.qids))
    return 0


if __name__ == '__main__':
    sys.exit(main())
