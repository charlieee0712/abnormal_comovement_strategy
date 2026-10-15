# -*- coding: utf-8 -*-
"""E6n Stage A 掩码层事实（brief §1.4、附录 B；任何收益读取之前落盘）。不读收益。
四段（掩码层事实不经后段守卫，与 E6m L-S10 同约定）：
  覆盖：分特征 × 年 × 交易所 × pool0 的可算份额（coverage_by_feature_year_exchange.csv）；
  QGOOD 逐日人数与份额；PL / RV（5 / 1 / 10）、六点尾盘价、8 格 profile、b20 基线（≥ 10 有限）完整率；
  零惩罚（h_path = 0、h_close = 0）与零 RV 份额；竞价可分离率（开盘竞价有量；收盘集合竞价期 14:58 / 14:59 无量）；1 / 10 分钟可得率；
  分钟指数可得日数（无源 → UNKNOWN）；源 Q 坏度缺失；B2 冻结源风险集规模与触发率（e6n_b2 prep 表并入）；B3 每日 m 分布与三种同数对照可行率；
  B4 clean / pool0 / clean\pool0 人数；UNKNOWN 日数。MDE80 / 配对 se / IC 不是掩码事实，冻结后作为结果生成（brief §1.4）。
输出 registration/mask_facts_E6n.csv（长表）、results/coverage_by_feature_year_exchange.csv、registration/stage_a_E6n.json。"""
import os
import sys
import json
import time
import pickle

import numpy as np
import pandas as pd

import e6n_core as N
import e6n_vars as VR

E6M_TMP = os.path.join(N.E6M_WORK, 'tmp')
FEATS = [('PL_REL20_f5', 'raw_PL_REL20_f5'), ('TAIL_PUSH', 'raw_TAIL_PUSH_f5'), ('TAIL_VOL_REL20', 'raw_TAIL_VOL_REL20_f5'),
         ('JSD_PROFILE20', 'raw_JSD_PROFILE20_f5'), ('RV_REL20_f5', 'raw_RV_REL20_f5'), ('PL_REL20_f1', 'raw_PL_REL20_f1'),
         ('PL_REL20_f10', 'raw_PL_REL20_f10'), ('RV_REL20_f1', 'raw_RV_REL20_f1'), ('RV_REL20_f10', 'raw_RV_REL20_f10'),
         ('Q_PATH_h_path_f5', 'comp_h_path_f5'), ('Q_PATH_h_path_f1', 'comp_h_path_f1'), ('Q_PATH_h_path_f10', 'comp_h_path_f10'),
         ('Q_CLOSE_THIN_h_close', 'comp_h_close_f5'), ('Q_RV_sqrtRV_f5', 'comp_sqrtRV_f5'), ('Q_RANGE_log_hl', 'comp_log_hl_f5'),
         ('Q_CLOSE_LEVEL_u_close', 'comp_h_close_level_f5'), ('K_RANGE_SOURCE', 'raw_K_RANGE_SOURCE_f5'), ('CLV20_SOURCE', 'raw_CLV20_SOURCE_f5')]
FORMS_B3 = ('A4b', 'M_mean3_v2', 'M_union3_v2')
CVR_OF = {'A4b': 'A4b_CVRv5', 'M_mean3_v2': 'M_mean3_v2_CVRv5', 'M_union3_v2': 'M_union3_v2_CVRv5'}


def exch(codes):
    c = np.asarray(codes).astype(str)
    return np.where(np.char.startswith(c, '6'), 'SH', np.where(np.char.startswith(c, '0') | np.char.startswith(c, '3'), 'SZ', 'OTHER'))


def seg_facts(seg):
    B = VR.Base(seg)
    out = []
    put = lambda fact, key, value, unit='count': out.append(dict(segment=seg, fact=fact, key=key, value=value, unit=unit))
    dates = B.get('dates')
    codes = B.get('codes')
    yr = (dates // 10000)[B.t]
    ex = exch(codes)[B.c]
    cov = []
    for name, col in FEATS:
        v = B.get(col)
        fin = np.isfinite(v)
        for (y, e), g in pd.DataFrame(dict(y=yr, e=ex, f=fin)).groupby(['y', 'e']):
            cov.append(dict(segment=seg, feature=name, year=int(y), exchange=e, domain='pool0', n_cells=int(len(g)), computable=int(g.f.sum()),
                            share_decimal=float(g.f.mean())))
        put('computable_share_pool0', name, float(fin.mean()), 'decimal')
    qg = B.qgood
    per_day = np.bincount(B.t[qg], minlength=len(dates))
    put('qgood_cells', 'ALL_DAYS', int(qg.sum()))
    put('qgood_share', 'ALL_DAYS', float(qg.mean()), 'decimal')
    put('qgood_per_day_median', 'ALL_DAYS', float(np.median(per_day)))
    put('qgood_per_day_min', 'ALL_DAYS', int(per_day.min()))
    put('source_q_bad_missing_cells', 'kQ', int((~np.isfinite(B.kQ)).sum()))
    for nm in ('col_PL_5', 'col_RV_5', 'raw_PL_REL20_f1', 'raw_PL_REL20_f10', 'col_S_TAIL', 'col_base_S_TAIL', 'col_b20_absL', 'col_U_CLOSE'):
        put('complete_share', nm, float(np.isfinite(B.get(nm)).mean()), 'decimal')
    hp, hc, rv = B.get('comp_h_path_f5'), B.get('comp_h_close_f5'), B.get('col_RV_5')
    put('zero_penalty_share', 'h_path_f5', float((hp[np.isfinite(hp)] == 0).mean()) if np.isfinite(hp).any() else np.nan, 'decimal')
    put('zero_penalty_share', 'h_close', float((hc[np.isfinite(hc)] == 0).mean()) if np.isfinite(hc).any() else np.nan, 'decimal')
    put('zero_rv_share', 'RV_5', float((rv[np.isfinite(rv)] == 0).mean()) if np.isfinite(rv).any() else np.nan, 'decimal')
    pres = B.get('col_minute_present') == 1
    auc = B.get('col_M_auction_traded')
    v58 = B.get('col_M_v1_1458_59')
    put('minute_present_share', 'pool0', float(pres.mean()), 'decimal')
    put('open_auction_separable_share', 'present', float((auc[pres] == 1).mean()) if pres.any() else np.nan, 'decimal')
    reg_post = (dates[B.t] >= 20180820) | (ex == 'SZ')
    m = pres & reg_post & np.isfinite(v58)
    put('close_auction_separable_share', 'SZ_all_or_SH_post', float((v58[m] == 0).mean()) if m.any() else np.nan, 'decimal')
    put('minute_index_available_days', 'A13_000852_000985_000300', 'UNKNOWN', 'status')
    minute_day = B.get('col_MINUTE_DAY')
    put('unknown_minute_days', 'days_without_minute_partition', int(len(np.unique(B.t[minute_day != 1]))))
    # B3：P = 裸核心（或其 Q0 变体）在 CVR 之前的名单，D = P 中被源 CVR k5 否决删掉的格，m = |D|（逐日）
    with open(os.path.join(E6M_TMP, 'ctx_%s.pkl' % seg), 'rb') as fh:
        ctx = pickle.load(fh)
    p0 = ctx['p0']
    ccols = np.flatnonzero(p0.any(0))
    cvr_fin = np.zeros(p0.shape, bool)
    di = {x: i for i, x in enumerate(ctx['pool0'].index)}
    cp = {x: j for j, x in enumerate(ctx['pool0'].columns)}
    for d, s in ctx['neu_cvr'].items():
        s = s.dropna()
        cvr_fin[di[d], [cp[x] for x in s.index]] = True
    cvr_cells = cvr_fin[:, ccols][B.t, B.c]
    k0 = B.get('k0')
    for form in FORMS_B3:
        zp = np.load(N.P('masks', seg, '%s.npz' % form), allow_pickle=False)
        zc = np.load(N.P('masks', seg, '%s.npz' % CVR_OF[form]), allow_pickle=False)
        kp = [str(k) for k in zp['mask_keys']]
        kc = [str(k) for k in zc['mask_keys']]
        for key in ('NONE|a0|NATIVE', 'NONE|a0.25|Q0', 'HG10|a0.25|Q0', 'LAG1_10|a0.25|Q0'):
            P = np.unpackbits(zp['final_bits'][kp.index(key)])[:B.n].astype(bool)
            C = np.unpackbits(zc['final_bits'][kc.index(key)])[:B.n].astype(bool)
            D = P & ~C
            extra = C & ~P
            m = np.bincount(B.t[D], minlength=len(dates))
            nP = np.bincount(B.t[P], minlength=len(dates))
            legal = np.bincount(B.t[P & cvr_cells], minlength=len(dates))
            k0ok = np.bincount(B.t[P & np.isfinite(k0)], minlength=len(dates))
            live = nP > 0
            kk = '%s|%s' % (form, key)
            put('b3_cvr_not_subset_cells', kk, int(extra.sum()))
            put('b3_m_mean', kk, float(m[live].mean()) if live.any() else np.nan, 'names_per_day')
            put('b3_m_p90', kk, float(np.percentile(m[live], 90)) if live.any() else np.nan, 'names_per_day')
            put('b3_m_zero_day_share', kk, float((m[live] == 0).mean()) if live.any() else np.nan, 'decimal')
            put('b3_feasible_random_legal_cvr', kk, float((legal[live] >= m[live]).mean()) if live.any() else np.nan, 'decimal')
            put('b3_feasible_worst_old_k', kk, float((k0ok[live] >= m[live]).mean()) if live.any() else np.nan, 'decimal')
            put('b3_feasible_source_priority', kk, float((nP[live] >= m[live]).mean()) if live.any() else np.nan, 'decimal')
    clean = ctx['clean'].to_numpy() == 1
    pool = p0
    put('b4_clean_per_day_median', 'clean', float(np.median(clean.sum(1))))
    put('b4_pool0_per_day_median', 'pool0', float(np.median(pool.sum(1))))
    put('b4_clean_minus_pool0_per_day_median', 'clean\\pool0', float(np.median((clean & ~pool).sum(1))))
    put('b4_pool0_not_clean_cells', 'pool0\\clean', int((pool & ~clean).sum()))
    return out, cov


def main():
    t0 = time.time()
    rows, covs = [], []
    for seg in N.SEGMENTS:
        r, c = seg_facts(seg)
        rows += r
        covs += c
        b2 = N.P('b2', 'b2_risk_set_facts_%s.csv' % seg)
        if os.path.exists(b2):
            D = pd.read_csv(b2, keep_default_na=False)
            for x in D.itertuples():
                k = '%s|%s|%s|H%d' % (x.form, x.object_key, x.trigger, x.H)
                rows += [dict(segment=seg, fact='b2_batches', key=k, value=x.batches, unit='count'),
                         dict(segment=seg, fact='b2_trigger_rate', key=k, value=x.trigger_rate_decimal, unit='decimal'),
                         dict(segment=seg, fact='b2_no_early_opportunity_share', key=k, value=x.no_early_share_decimal, unit='decimal'),
                         dict(segment=seg, fact='b2_realized_early', key=k, value=x.realized_early, unit='count')]
        else:
            rows.append(dict(segment=seg, fact='b2_risk_set', key='ALL', value='NOT_RUN', unit='status'))
    F = pd.DataFrame(rows)
    C = pd.DataFrame(covs)
    p1 = N.P('registration', 'mask_facts_E6n.csv')
    N.atomic_write_csv(p1, F)
    os.makedirs(N.P('results'), exist_ok=True)
    p2 = N.P('results', 'coverage_by_feature_year_exchange.csv')
    N.atomic_write_csv(p2, C)
    s = dict(rows=len(F), coverage_rows=len(C), b2_not_run=int((F.value.astype(str) == 'NOT_RUN').sum()), secs=round(time.time() - t0, 1))
    p3 = N.P('registration', 'stage_a_E6n.json')
    N.atomic_write_json(p3, s)
    N.write_receipt('E6n_stage_a', [p1, p2, p3], code=[__file__], **s)
    print(json.dumps(s, ensure_ascii=False))


if __name__ == '__main__':
    main()
