# -*- coding: utf-8 -*-
"""E6m 推导段配对 MDE80 与卡片 ⑬（brief §5 S3；plan §9.5；e6l_mde80 同式标签）。Stage B 冻结之后、后段之前运行。
- 输入：比较统计 comparison_stats_<推导段>.csv（e6m_s_stats cmp：se_H、mde80 = 2.80 · se_H，年化百分点）；
- 输入：cards_stageB_E6m.csv（各卡绑定视图）。
- 输出：paired_mde80_deriv.csv（只取 se 与 MDE 列，不取均值）；cards_t13_deriv_E6m.csv（每卡 × 推导段：MDE80 分位与机械标签）。
标签只描述"配对差需多大才 80% 可辨"，不改任何预测、不作门（plan §9.5：MDE 不决定只能看符号或剔卡）。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import argparse

import numpy as np
import pandas as pd

import e6m_core as M

DERIV = ('2010-2014', '2015-2018')


def label(med):
    if not np.isfinite(med):
        return 'UNDEFINED（无绑定配对比较）'
    if med <= 0.10:
        return 'MDE80 中位 ≤ .10：.10 级配对差可 80% 分辨'
    if med <= 0.30:
        return '.10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号'
    return 'MDE80 中位 > .30：首看，只记录'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stats', required=True)
    ap.add_argument('--cards', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    cols = ['comparison_id', 'view', 'card', 'kind', 'left_desc_id', 'right_desc_id', 'H', 'segment', 'se_H_ann_pp', 'mde80_ann_pp', 'n_days', 'status']
    M_ = pd.concat([pd.read_csv(os.path.join(a.stats, 'comparison_stats_%s.csv' % s), usecols=cols, keep_default_na=False, na_values=[''])
                    for s in DERIV], ignore_index=True)
    os.makedirs(a.out, exist_ok=True)
    p1 = os.path.join(a.out, 'paired_mde80_deriv.csv')
    M.atomic_write_csv(p1, M_)
    Cb = pd.read_csv(a.cards, keep_default_na=False, na_values=[''])
    rows = []
    for r in Cb.itertuples():
        views = [v for v in str(r.contrast_views).split('|') if v]
        for s in DERIV:
            v = M_[(M_.segment == s) & M_.view.isin(views)].mde80_ann_pp.values
            v = v[np.isfinite(v)]
            med = float(np.median(v)) if len(v) else np.nan
            rows.append(dict(card=r.card, segment=s, n_comparisons=int(len(v)), mde80_p10_ann_pp=float(np.percentile(v, 10)) if len(v) else np.nan,
                             mde80_median_ann_pp=med, mde80_p90_ann_pp=float(np.percentile(v, 90)) if len(v) else np.nan, t13_label=label(med)))
    T13 = pd.DataFrame(rows)
    p2 = os.path.join(a.out, 'cards_t13_deriv_E6m.csv')
    M.atomic_write_csv(p2, T13)
    M.write_receipt(os.environ.get('E6M_TASK', 'S_mde80_deriv'), [p1, p2], status='SUCCEEDED', code=[__file__, M.__file__], rows=len(M_), cards=len(Cb))
    print(json.dumps(dict(rows=len(M_), cards=len(Cb), labelled=int((T13.n_comparisons > 0).sum())), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
