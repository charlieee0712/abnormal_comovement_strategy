# -*- coding: utf-8 -*-
"""E6l_REPORT_part1（plan §13.4：推导两段全表）。只在 seal_deriv 核对通过后运行。
输入：results/deriv/descriptor_stats_<段>.csv、random_refs_<段>.csv（e6l_stats）、comparison_stats_<段>.csv（e6l_cmpstats）、
results/stage_a/*、results/deriv/paired_mde80_deriv.csv / cards_t13_deriv_E6l.csv、registry/*。
推导段合并：D 类量按两段有效配对日 n 加权；SE 合并 = √Σ(n_s/N)²·se_s²；暴露量两段平均；随机 real − 随机均值按两段 n 加权、MCSE 同式。
新算子读数只标 NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY；同构对象 SECOND_EVALUATION_SAME_HISTORY；不设显著性门、不写判词。"""
import e6l_boot  # noqa: F401
import os
import sys

import numpy as np
import pandas as pd

import e6l_core as L
import e6l_report as RP
import e6l_registry as RG

SEGS = L.DERIV_SEGS
DATES = '2010-01-04..2018-12-28（推导两段；每段前 19 日预热）'
OUT = L.P('reports', 'E6l_REPORT_part1.md')


def wavg(x, w):
    x = np.asarray(x, float)
    w = np.asarray(w, float)
    m = np.isfinite(x) & np.isfinite(w) & (w > 0)
    return float((x[m] * w[m]).sum() / w[m].sum()) if m.any() else np.nan


def merge_deriv(S):
    Dc = [c for c in S.columns if (c.startswith('D') or c.startswith('Dg_') or c.startswith('Dsc_')) and not c.startswith('D_20')]
    ex = [c for c in S.columns if c.startswith(('port_size', 'edit_gap', 'lv5', 'small30', 'unk', 'n_edits', 'edit_w_in', 'nnames', 'wsum', 'parent_',
                                                'roll_size', 'turn_rel', 'pos_diff', 'qmiss', 'net8_ann', 'gross_ann', 'turn_mean', 'pos_mean'))]
    rows = []
    for did, g in S.groupby('desc_id'):
        r = dict(desc_id=did, kind=g.kind.iloc[0], n=float(g.n.sum()))
        for c in Dc:
            r[c] = wavg(g[c], g.n)
        for c in ex:
            v = g[c].astype(float)
            r[c] = float(np.nanmean(v)) if np.isfinite(v).any() else np.nan
        N = g.n.sum()
        for sec in ('se_H', 'se_2H', 'se_60'):
            r[sec] = float(np.sqrt(np.nansum((g.n / N) ** 2 * g[sec] ** 2))) if N > 0 else np.nan
        r['MDE80'] = 2.80 * r['se_H']
        for s in SEGS:
            gs = g[g.segment == s]
            r['D_%s' % s] = float(gs.D.iloc[0]) if len(gs) else np.nan
            r['n_%s' % s] = float(gs.n.iloc[0]) if len(gs) else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


def merge_cmp(C):
    rows = []
    for cid, g in C.groupby('cmp_id'):
        N = g.n_days.sum()
        r = dict(cmp_id=cid, kind=g.kind.iloc[0], view=g.view.iloc[0], left_id=g.left_id.iloc[0], right_id=g.right_id.iloc[0], H=int(g.H.iloc[0]),
                 query_id=g.query_id.iloc[0], n_days=float(N), D_ann_pp=wavg(g.D_ann_pp, g.n_days), Dg_ann_pp=wavg(g.Dg_ann_pp, g.n_days),
                 fee_ann_pp=wavg(g.fee_ann_pp, g.n_days),
                 se_H_ann_pp=float(np.sqrt(np.nansum((g.n_days / N) ** 2 * g.se_H_ann_pp ** 2))) if N > 0 else np.nan)
        for s in SEGS:
            gs = g[g.segment == s]
            r['D_%s' % s] = float(gs.D_ann_pp.iloc[0]) if len(gs) else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


def rand_deriv(R, nmap):
    out = []
    for (did, H, m), g in R.groupby(['desc_id', 'H', 'mechanism']):
        ns = np.array([nmap.get((did, s), np.nan) for s in g.segment], float)
        d = g.real_minus_rand.values.astype(float)
        se = g.mcse.values.astype(float)
        ok = np.isfinite(ns) & np.isfinite(d)
        if not ok.any():
            continue
        w = ns[ok] / ns[ok].sum()
        out.append(dict(desc_id=did, H=H, mechanism=m, rmr_deriv=float((w * d[ok]).sum()), mcse_deriv=float(np.sqrt((w ** 2 * se[ok] ** 2).sum())),
                        paths_min=int(g.n.min()), rand_sd_max=float(g.rand_sd.max()),
                        **{'rmr_%s' % s: float(g[g.segment == s].real_minus_rand.iloc[0]) if (g.segment == s).any() else np.nan for s in SEGS}))
    return pd.DataFrame(out)


def head(subject, op, sub, H='5', support='原生（FALLBACK）', expo='见 evidence_exposure 列', unit='年化百分点（ann_pp）', base='同 H 原父（8bp）',
         cap='实际源 DEV（MATCH-CAP 另列 D_sc）'):
    return {'主体': subject, '算子': op, '分母': '两推导段有效配对日（n 加权）', '基准': base, '子集': sub, '单位': unit, '日期': DATES, 'H': H,
            '成本模型': '源 8bp（冲击列 A 5 亿 κ .5）', '支持': support, '资本视图': cap, 'exposure': expo}


def main():
    import e6l_seal as SEAL
    ok, bad = SEAL.verify('deriv')
    if not ok:
        raise RuntimeError('seal_deriv 核对失败：%s' % bad[:5])
    D = L.read_csv_keep(L.P('registry', 'descriptors_E6l.csv'))
    S = pd.concat([pd.read_csv(L.P('results', 'deriv', 'descriptor_stats_%s.csv' % s), keep_default_na=False, na_values=['']) for s in SEGS],
                  ignore_index=True)
    R = pd.concat([pd.read_csv(L.P('results', 'deriv', 'random_refs_%s.csv' % s), keep_default_na=False, na_values=['']).assign(segment=s) for s in SEGS],
                  ignore_index=True)
    C = pd.concat([pd.read_csv(L.P('results', 'deriv', 'comparison_stats_%s.csv' % s), keep_default_na=False, na_values=['']) for s in SEGS],
                  ignore_index=True)
    M = merge_deriv(S)
    nmap = {(r.desc_id, r.segment): r.n for r in S.itertuples()}
    RD = rand_deriv(R, nmap)
    CD = merge_cmp(C)
    keep = ['desc_id', 'meas', 'mother', 'alpha', 'H', 'op', 'family', 'blocks', 'primary72', 'dose72', 'nbhd72', 'recipe', 'target_id', 'evidence_exposure']
    M = M.merge(D[keep], on='desc_id', how='left')
    L.atomic_write_csv(L.P('results', 'deriv', 'descriptor_stats_deriv_merged.csv'), M)
    L.atomic_write_csv(L.P('results', 'deriv', 'random_refs_deriv_merged.csv'), RD)
    L.atomic_write_csv(L.P('results', 'deriv', 'comparison_stats_deriv_merged.csv'), CD)
    rp = RP.Report('part1')
    rp.h(1, 'E6l REPORT part1 —— 推导两段（2010-2014 / 2015-2018）全部登记对象的作用量、对照与十六卡初读')
    rp.p('用途：plan §13.4 part1。只含推导两段；数字全部来自 `results/deriv/*.csv`（seal_deriv 之后生成）。新对象标签 `%s`（首评、重复使用的历史，非样本外）；'
         'E6k 同构对象标 `%s`，只作锚与基线。不设显著性门、不写判词；新算子 replacement_preference_status = NOT_AUTHORIZED，deployment_authorized = false。'
         % (L.LABEL_FIRST_LOOK, L.LABEL_SECOND))
    rr = RD[RD.H == 5].pivot_table(index='desc_id', columns='mechanism', values=['rmr_deriv', 'mcse_deriv'], aggfunc='first')
    rr.columns = ['%s_%s' % (a, b) for a, b in rr.columns]
    # §1 主展示 72
    rp.h(2, '1. 主展示 72 行（12 配方 × 六形态，α .25 × H5）')
    P72 = M[M.primary72.astype(str) == 'True'].merge(rr, left_on='desc_id', right_index=True, how='left')
    for rec in [r for r in dict.fromkeys(P72.recipe)]:
        t = P72[P72.recipe == rec].sort_values('mother')
        cols = ['mother', 'D_2010-2014', 'D_2015-2018', 'D', 'se_H', 'MDE80', 'D_sc', 'D_imp', 'D_gross', 'D_vs_native', 'D_vs_Q0', 'D_vs_QHG10', 'D_vs_C1',
                'D_vs_rule_only', 'port_size_lo_T', 'port_size_hi_T', 'edit_gap_mean_T', 'edit_gap_absmean_T', 'turn_rel',
                'rmr_deriv_LEGACY_POLICY_RANDOM', 'mcse_deriv_LEGACY_POLICY_RANDOM', 'rmr_deriv_CONTENT_COND_ISK_P5', 'mcse_deriv_CONTENT_COND_ISK_P5',
                'evidence_exposure']
        tt = t[[c for c in cols if c in t.columns]].rename(columns={'D': 'D_deriv_ann_pp', 'port_size_lo_T': 'port_size_lo_T_segavg_pct_pt',
                                                                    'port_size_hi_T': 'port_size_hi_T_segavg_pct_pt'})
        rp.table(tt, head('配方 %s × 六形态' % rec, rec.split(':')[1], 'primary72'), 'E6L-P1-72-%s' % rec.replace(':', '-'))
    # §2 剂量面板 / 邻域
    rp.h(2, '2. 同 72 配方的 α .5 剂量面板与 α .125 邻域（任一剂量按同一正式尺子，政策在 part3）')
    for lab, col in (('α .5 剂量面板', 'dose72'), ('α .125 邻域', 'nbhd72')):
        t = M[M[col].astype(str) == 'True'].sort_values(['recipe', 'mother'])
        rp.table(t[['recipe', 'mother', 'D_2010-2014', 'D_2015-2018', 'D', 'se_H', 'D_sc', 'D_vs_native', 'port_size_lo_T', 'port_size_hi_T', 'turn_rel',
                    'evidence_exposure']].rename(columns={'D': 'D_deriv_ann_pp', 'port_size_lo_T': 'port_size_lo_T_segavg_pct_pt',
                                                           'port_size_hi_T': 'port_size_hi_T_segavg_pct_pt'}),
                 head(lab, '12 配方', col), 'E6L-P1-%s' % col.upper())
    # §3 网格分布
    rp.h(2, '3. 全部登记描述符按 族 × 算子 × α 的分布（汇总测量 × 母体 × H1…20）')
    grid = []
    reg = M[M.kind == 'registered']
    for (fam, op, a), g in reg.groupby(['family', 'op', 'alpha']):
        x = g.D.astype(float)
        grid.append(dict(family=fam, op=op, alpha=a, cells=int(x.notna().sum()), share_pos=float((x > 0).mean()) if x.notna().any() else np.nan,
                         q10_ann_pp=float(x.quantile(.1)), median_ann_pp=float(x.median()), q90_ann_pp=float(x.quantile(.9)),
                         median_vs_native_ann_pp=float(g.D_vs_native.median()) if 'D_vs_native' in g else np.nan,
                         median_vs_Q0_ann_pp=float(g.D_vs_Q0.median()) if 'D_vs_Q0' in g else np.nan))
    rp.table(pd.DataFrame(grid), head('全部登记描述符（不含 PARENT）', '各算子', '按族 × 算子 × α', 'H 1…20'), 'E6L-P1-GRID')
    # §4 机制账户（日层闭合）
    rp.h(2, '4. 机制账户（比较层：日层先闭合再段均；推导段合并）')
    cd5 = CD[CD.H == 5]
    for kind, lab, qid in (('FOUR_ACCOUNT_INFO_RULE', '信息 × 规则交互 Y11 − Y10 − Y01 + Y00（Y00 原父 / Y10 新测量无规则 / Y01 旧 K 规则 / Y11 新测量规则）', 'E6L-P1-INFO-RULE'),
                           ('FOUR_ACCOUNT_SMOOTH_RULE', '平滑 × 规则交互（Q0 NATIVE / Qs NATIVE / Q0 规则 / Qs 规则）', 'E6L-P1-SMOOTH-RULE'),
                           ('MECHANISM_PAIR', '机制配对（LAG1 / DECAY / INV / 调度 / 边界 b 相对 HG10 等）', 'E6L-P1-MECHPAIR'),
                           ('MA_VS_EW', 'MA vs EW（D3 − DEW3、D5 − DEW5）', 'E6L-P1-MAEW'),
                           ('MEAN_KERNEL_PAIR', '均值核配对（D5 − QMEAN5、D5 − DMED5、QMEAN5 − DMED5）', 'E6L-P1-MEANK'),
                           ('RANK_BRIDGE_PAIR', '秩桥（RANK5 − RANKOBS5、RANK5 − RANKSCORE5）', 'E6L-P1-RANKB'),
                           ('WINDOW_PAIR', '窗口配对（D5 − D3、D10 − D5、RANK5 − RANK3、RANK10 − RANK5）', 'E6L-P1-WINDOW')):
        g = cd5[cd5.kind == kind]
        if not len(g):
            continue
        lt = g.left_id.str.split('|')
        g = g.assign(meas=lt.str[0], mother=lt.str[1], alpha=lt.str[2], op=lt.str[4], right_op=g.right_id.str.split('|').str[4],
                     right_meas=g.right_id.str.split('|').str[0])
        t = g.groupby(['meas', 'right_meas', 'op', 'right_op', 'alpha']).agg(cells=('cmp_id', 'count'), median_D_ann_pp=('D_ann_pp', 'median'),
                                                                               share_pos=('D_ann_pp', lambda x: float((x > 0).mean())),
                                                                               median_Dg_ann_pp=('Dg_ann_pp', 'median'), median_fee_ann_pp=('fee_ann_pp', 'median'),
                                                                               median_se_H_ann_pp=('se_H_ann_pp', 'median')).reset_index()
        rp.table(t, head(lab, kind, '六形态汇总（中位）', support='各端原生'), qid)
    for kind, lab, qid in (('KERNEL_DOSE', 'X − KERNEL_DOSE（同均值 / RMS 的 Q0 增量控制）', 'E6L-P1-KDOSE'),
                           ('SUPPORT_BRIDGE_CONTENT', '支持桥：共同支持上 X − Q0（内容）', 'E6L-P1-CS-CONTENT'),
                           ('SUPPORT_BRIDGE_PARENT_SUPPORT', '支持桥：Q0 共同支持 − Q0 原生（Q0 支持变化）', 'E6L-P1-CS-PSUP'),
                           ('SUPPORT_BRIDGE_CHILD_SUPPORT', '支持桥：X 原生 − X 共同支持（X 支持变化）', 'E6L-P1-CS-CSUP'),
                           ('MASKQ0_SUPPORT_ONLY', 'Q0 遮罩到 X 支持 − Q0（只改支持）', 'E6L-P1-MQ0-SUP'),
                           ('MASKQ0_CONTENT', 'X − Q0 遮罩（同支持的内容差）', 'E6L-P1-MQ0-CONTENT'),
                           ('INV_CAP_LOOP', 'INV 闭环同资本（诊断，不进正式 FULL_sc）', 'E6L-P1-INVLOOP'),
                           ('STRICT250_VS_MAIN', 'STRICT250 状态 − 主定义状态', 'E6L-P1-S250')):
        g = CD[CD.kind == kind]
        if not len(g):
            continue
        lt = g.left_id.str.split('|')
        off = 1 if kind in ('KERNEL_DOSE',) else 0
        g = g.assign(meas=[x[1] if x[0] in ('KD', 'CSC', 'CSP', 'MQ0', 'S250', 'ICL') else x[0] for x in lt],
                     op=[x[-1] for x in lt])
        t = g.groupby(['meas', 'op', 'H']).agg(cells=('cmp_id', 'count'), median_D_ann_pp=('D_ann_pp', 'median'), share_pos=('D_ann_pp', lambda x: float((x > 0).mean())),
                                               median_se_H_ann_pp=('se_H_ann_pp', 'median')).reset_index()
        rp.table(t, head(lab, kind, '六形态汇总（中位）', 'H 见列', support='见视图'), qid)
    # §5 随机层
    rp.h(2, '5. 随机层（推导段；real − 随机均值与 MCSE；不作门）')
    if len(RD):
        g = RD.groupby('mechanism')
        t = g.agg(rows=('desc_id', 'count'), paths_min=('paths_min', 'min'), share_pos=('rmr_deriv', lambda x: float((x > 0).mean())),
                  median_rmr_ann_pp=('rmr_deriv', 'median'), worst_mcse_ann_pp=('mcse_deriv', 'max'), max_path_sd_ann_pp=('rand_sd_max', 'max')).reset_index()
        t['share_pos_2mcse'] = [float(((x.rmr_deriv > 0) & (x.rmr_deriv >= 2 * x.mcse_deriv)).mean()) for _, x in g]
        rp.table(t, head('随机参照（全部登记随机行）', '按机制', '随机清单全部行', '1|2|3|5|10|20（R-MARK 1|5|20）', base='同对象随机路径均值'), 'E6L-P1-RAND')
        rm = RD[RD.mechanism.str.startswith('RMARK')]
        if len(rm):
            rm = rm.assign(meas=rm.desc_id.str.split('|').str[0], mother=rm.desc_id.str.split('|').str[1], alpha=rm.desc_id.str.split('|').str[2])
            t = rm.pivot_table(index=['meas', 'mother', 'alpha', 'H'], columns='mechanism', values='rmr_deriv').reset_index()
            t.columns = [str(c) for c in t.columns]
            rp.table(t, head('真实 HG10 − R-MARK 随机（本路径自身标记在分区内置换）', 'R-MARK 三机制', 'Q0 / Q_D5 / Q_RANK5 / 旧 K × HG10', '1|5|20',
                             base='同对象 R-MARK 路径均值'), 'E6L-P1-RMARK')
    # §6 Stage A 事实
    rp.h(2, '6. Stage A 掩码层事实（推导两段；读数前已冻结）')
    MF = pd.read_csv(L.P('results', 'stage_a', 'mask_facts_deriv_E6l.csv'), keep_default_na=False, na_values=[''])
    mf = MF[(MF.variant == 'REGISTERED')].copy()
    mf['alpha_'] = mf.alpha
    cols = [c for c in ('bonus_reliant_share', 'reliant_run_p90', 'confirm_age_p90', 'gate_retention', 'list_retention', 'self_edits_per_day',
                        'downstream_survival', 'inv_mark_coverage', 'inv_saturated_day_share', 'pending_expiry_overlap', 'edit_persistence_5d_reversal_share',
                        'same_ticker_overlap_with_native') if c in mf.columns]
    for c in cols:
        mf[c] = pd.to_numeric(mf[c], errors='coerce')
    t = mf[mf.alpha.isin(['a0.25', 'a0'])].groupby(['op']).agg(**{('%s_median' % c): (c, 'median') for c in cols}).reset_index()
    rp.table(t, head('门层记忆 / 库存 / 名单事实（α .25，旧 K α0；六形态 × 测量 × 两段中位）', '按算子', 'mask_facts_deriv_E6l', 'INV 按 H；其余与 H 无关',
                     unit='份额 / 日数'), 'E6L-P1-STAGEA')
    # §7 MDE80 与 ⑬
    rp.h(2, '7. 推导段配对 MDE80 与卡片 ⑬（只用日差标准误；不改预测）')
    T13 = pd.read_csv(L.P('results', 'deriv', 'cards_t13_deriv_E6l.csv'), keep_default_na=False, na_values=[''])
    rp.table(T13.rename(columns={'mde80_median_ann_pp': 'mde80_median_ann_pp'}), head('16 卡绑定比较的 MDE80（2.80 × HAC(H) se）', '按卡', 'paired_mde80_deriv',
                                                                                    '各比较自身 H', base='比较右端'), 'E6L-P1-T13')
    # §8 十六卡初读
    rp.h(2, '8. 十六张卡的推导段初读（机械计数；后段首看后才用首看标签）')
    cards = L.read_csv_keep(L.P('registry', 'cards_E6l.csv'))
    q2o = L.read_csv_keep(L.P('registry', 'question_to_objects_E6l.csv'))
    rows = []
    for c in cards.itertuples():
        ids = set(q2o[q2o.query_id.str.startswith('E6L-%s-' % c.card)].desc_id)
        g = M[M.desc_id.isin(ids)] if ids != {'ALL_DESCRIPTORS'} else M[M.kind == 'registered']
        cc = CD[CD.query_id.str.startswith('E6L-%s-' % c.card)]
        rows.append(dict(card=c.card, objects=len(ids), with_deriv_rows=len(g), share_D_pos=float((g.D > 0).mean()) if len(g) else np.nan,
                         median_D_ann_pp=float(g.D.median()) if len(g) else np.nan, bound_comparisons=len(cc),
                         median_cmp_D_ann_pp=float(cc.D_ann_pp.median()) if len(cc) else np.nan, queries=c.queries))
    rp.table(pd.DataFrame(rows), head('16 张卡的登记对象与绑定比较', '按卡', 'question_to_objects_E6l / comparison_manifest', '各对象自身 H'), 'E6L-P1-CARDS')
    rp.h(2, '9. 未做项及原因')
    rp.p('- 两后段（2019-2023 / 2024-2026）：方式 B，record B 草稿与进入核验（`record_B_entry_post_E6l.json`）之后同版本一次算完、seal_post。')
    rp.p('- 政策（六条 + PORT3_T）逐对象评分、bootstrap（段内分层 stationary 20 / 60 × 2,000）、连续状态面板、三时钟、影子与风险：brief §5 次序在 seal_post 之后。')
    rp.write(OUT)
    L.write_receipt(L.next_rerun('report_part1'), [OUT], 'SUCCEEDED', queries=len(rp.qids))
    print('part1 写出：%d 个 query' % len(rp.qids), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
