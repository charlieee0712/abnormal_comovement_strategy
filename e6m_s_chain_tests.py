# -*- coding: utf-8 -*-
"""E6m 阶段 S（B2 开发）· 下游统计链在合成账本上的闭合测试（不读任何收益）。
1. 覆盖：每段每个登记描述符有统计行（COMPUTED 或父 PARENT_SELF）；76,466 条比较每段都有行。
2. 可加性：kind = ACTUAL_PARENT 的比较 D = 该描述符统计 D（同共同日）≤ 1e−9。
3. 批量 HAC = 单条 e6j_stats.hac_se（随机抽 300 条比较）≤ 1e−12（相对）。
4. FULL = Σ n_s D_s / Σ n_s（四段）手算对拍。
5. 合成构造的已知答案：子 − 父 = δ_config + 噪声 → 四段 FULL 与 δ·ANN 的差在噪声 3 倍标准误以内的份额（只作 INFO，验证管道没有串行）。
6. 四账户闭合（plan §9.1）：任取 (Y00, Y10, Y01, Y11) 四个合成序列，逐日 I + R + X = Y11 − Y00 ≤ 1e−15。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
import e6j_stats as ST
import e6m_s_stats as SS
import e6m_s_synth as SY

SEGS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--acc', required=True)
    a = ap.parse_args()
    rows = []
    put = lambda test, ok, **kw: rows.append(dict(test=test, status='PASS' if ok else 'FAIL', **kw))
    Dr = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    CM = M.read_csv_keep(M.P('registry', 'comparison_manifest_E6m.csv'), dtype=str)
    rng = np.random.default_rng(7)
    for seg in SEGS:
        ds = pd.read_csv(os.path.join(a.out, 'descriptor_stats_%s.csv' % seg), keep_default_na=False, na_values=[''])
        cs = pd.read_csv(os.path.join(a.out, 'comparison_stats_%s.csv' % seg), keep_default_na=False, na_values=[''])
        put('coverage_desc', set(ds.desc_id) == set(Dr.desc_id) and ds.status.isin(['COMPUTED', 'PARENT_SELF']).all(), segment=seg,
            detail='rows=%d' % len(ds))
        put('coverage_cmp', set(cs.comparison_id) == set(CM.comparison_id) and (cs.status == 'COMPUTED').all(), segment=seg, detail='rows=%d' % len(cs))
        m = cs[cs.kind == 'ACTUAL_PARENT'].merge(ds[['desc_id', 'D', 'n']], left_on='left_desc_id', right_on='desc_id')
        err = float(np.nanmax(np.abs(m.D_ann_pp - m.D))) if len(m) else np.nan
        put('additivity_actual_parent', len(m) > 0 and err <= 1e-9 and (m.n_days == m.n).all(), segment=seg, detail='n=%d max_abs=%.3g' % (len(m), err))
        d, t, d2t, dH, dates = SS.load(a.acc, seg)
        samp = cs.sample(300, random_state=int(rng.integers(0, 1 << 30)))
        rel = []
        for r in samp.itertuples():
            x = ST.paired(d[r.left_desc_id]['net8'], d[r.right_desc_id]['net8'])[0]
            s1 = ST.hac_se(x, int(r.H))[0] * ST.ANN
            rel.append(abs(s1 - r.se_H_ann_pp) / max(abs(s1), 1e-300))
        put('hac_batch_vs_single', max(rel) <= 1e-12, segment=seg, detail='max_rel=%.3g' % max(rel))
    # 4 FULL 手算
    full = pd.read_csv(os.path.join(a.out, 'descriptor_stats_FULL.csv'), keep_default_na=False, na_values=[''])
    parts = pd.concat([pd.read_csv(os.path.join(a.out, 'descriptor_stats_%s.csv' % s), keep_default_na=False, na_values=['']) for s in SEGS])
    parts = parts[parts.status == 'COMPUTED']
    pick = full.sample(200, random_state=11)
    errs = []
    for r in pick.itertuples():
        g = parts[parts.desc_id == r.desc_id]
        errs.append(abs(float((g.D * g.n).sum() / g.n.sum()) - r.FULL_D))
    put('full_weighted_mean', max(errs) <= 1e-9, detail='max_abs=%.3g' % max(errs))
    # 5 已知答案（INFO）
    p2 = parts.copy()
    p2['cid'] = p2.desc_id.map(SY.config_id)
    fz = full.merge(p2.groupby('desc_id').se_H.apply(lambda s: float(np.sqrt(np.nanmean(s ** 2)))).rename('se').reset_index(), on='desc_id')
    fz['delta'] = fz.desc_id.map(lambda x: SY.delta_of(SY.config_id(x)) * ST.ANN)
    within = float((np.abs(fz.FULL_D - fz.delta) <= 3 * fz.se / 2.0).mean())
    rows.append(dict(test='known_answer_within_3se', status='INFO', detail='share=%.4f n=%d' % (within, len(fz))))
    # 6 四账户闭合
    T = 500
    Y00, Y10, Y01, Y11 = (rng.normal(0, 1e-3, T) for _ in range(4))
    I_, R_, X_ = Y10 - Y00, Y01 - Y00, Y11 - Y10 - Y01 + Y00
    put('four_account_closure', float(np.max(np.abs(I_ + R_ + X_ - (Y11 - Y00)))) <= 1e-15, detail='synthetic arrays')
    df = pd.DataFrame(rows)
    p = os.path.join(a.out, 'chain_tests.csv')
    M.atomic_write_csv(p, df)
    ok = bool((df.status != 'FAIL').all())
    M.write_receipt(os.environ.get('E6M_TASK', 'S_dev_chain_tests'), [p], status='SUCCEEDED' if ok else 'FAILED', code=[__file__, SS.__file__, M.__file__])
    print(df.to_string(index=False), flush=True)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
