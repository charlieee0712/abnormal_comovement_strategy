# -*- coding: utf-8 -*-
"""E6k_REPORT_part1（plan §13.5：推导段所有路线、作用量、对照、十八 Q 初读，未做项及原因）。只在 seal_deriv 核对通过后运行。
输入：results/deriv/descriptor_stats_<段>.csv、random_refs_<段>.csv（e6k_stats）、accounts/<段>/facts_*.csv、registry/*。
推导段合并：D 类量按两段有效配对日 n 加权（= E6i descriptor_stats_all4 口径的两段版）；SE 合并 = √Σ(n_s/N)²·se_s²；
暴露量按有效日加权平均；随机 real − 随机均值按两段 n 加权、MCSE 合并同式。所有表头带首看 / 暴露标签；不设显著性门、不写判词。"""
import e6k_boot  # noqa: F401
import os
import sys
import glob
import re

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_report as RP
import e6k_seal as SEAL

SEGS = K.DERIV_SEGS
DATES = '2010-01-04..2018-12-28（推导两段）'
OUT = K.P('reports', 'E6k_REPORT_part1.md')


def present(df, cols):
    return [c for c in cols if c in df.columns]


def wavg(df, col, wcol):
    x = df[col].astype(float)
    w = df[wcol].astype(float)
    m = np.isfinite(x) & np.isfinite(w) & (w > 0)
    return float((x[m] * w[m]).sum() / w[m].sum()) if m.any() else np.nan


def merge_deriv(S):
    """两段 → 推导段合并行（逐描述符）。"""
    rows = []
    Dcols = [c for c in S.columns if c.startswith('D') and c not in ('D',)] + ['D']
    expo = [c for c in S.columns if c.startswith(('port_size', 'edit_gap', 'lv5', 'small30', 'unk', 'n_edits', 'edit_w_in', 'nnames', 'wsum',
                                                  'parent_', 'roll_size', 'turn_rel', 'pos_diff', 'N1_', 'C1_', 'C0_', 'qmiss'))]
    for did, g in S.groupby('desc_id'):
        r = dict(desc_id=did, n=float(g.n.sum()))
        for c in set(Dcols):
            if c in g:
                r[c] = wavg(g, c, 'n')
        for c in expo:
            if c in g:
                r[c] = float(np.nanmean(g[c].astype(float))) if np.isfinite(g[c].astype(float)).any() else np.nan
        N = g.n.sum()
        r['se_H'] = float(np.sqrt(np.nansum((g.n / N) ** 2 * g.se_H ** 2))) if N > 0 else np.nan
        for s in SEGS:
            gs = g[g.segment == s]
            r['D_%s' % s] = float(gs.D.iloc[0]) if len(gs) else np.nan
            r['n_%s' % s] = float(gs.n.iloc[0]) if len(gs) else np.nan
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
                        paths_min=int(g.n.min()), **{'rmr_%s' % s: float(g[g.segment == s].real_minus_rand.iloc[0]) if (g.segment == s).any() else np.nan
                                                   for s in SEGS}))
    return pd.DataFrame(out)


def head(subject, op, sub, H='5', support='原生（FALLBACK）', expo='见 selection_exposure_ledger', unit='年化百分点', base='同 H 原父（8bp）'):
    return {'主体': subject, '算子': op, '分母': '两推导段有效配对日（n 加权）', '基准': base, '子集': sub, '单位': unit, '日期': DATES, 'H': H,
            '成本模型': '源 8bp（冲击列 A 5 亿 κ .5）', '支持': support, '资本视图': '实际源 DEV（MATCH-CAP 另列）', 'exposure': expo}


def main():
    if '--trial' in sys.argv:
        if not K.RES.startswith(K.TRIAL):
            raise RuntimeError('--trial 只允许在临时目录')
    else:
        ok, bad = SEAL.verify('deriv')
        if not ok:
            raise RuntimeError('seal_deriv 核对失败：%s' % bad[:5])
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    X = pd.read_csv(K.P('registry', 'selection_exposure_ledger_E6k.csv'))
    S = pd.concat([pd.read_csv(K.P('results', 'deriv', 'descriptor_stats_%s.csv' % s)) for s in SEGS], ignore_index=True)
    R = pd.concat([pd.read_csv(K.P('results', 'deriv', 'random_refs_%s.csv' % s)).assign(segment=s) for s in SEGS], ignore_index=True)
    F = pd.concat([pd.read_csv(f).assign(segment=f.split('/')[-2]) for s in SEGS for f in glob.glob(K.P('accounts', s, 'facts_*.csv'))], ignore_index=True)
    M = merge_deriv(S)
    nmap = {(r.desc_id, r.segment): r.n for r in S.itertuples()}
    RD = rand_deriv(R, nmap)
    M = M.merge(D[['desc_id', 'meas', 'mother', 'alpha', 'H', 'op', 'family', 'blocks', 'primary144', 'c1_hi', 'sm_anchor', 'target_id']],
                on='desc_id', how='left').merge(X[['desc_id', 'exposure_type']], on='desc_id', how='left')
    K.atomic_write_csv(K.P('results', 'deriv', 'descriptor_stats_deriv_merged.csv'), M)
    K.atomic_write_csv(K.P('results', 'deriv', 'random_refs_deriv_merged.csv'), RD)
    rp = RP.Report('part1')
    rp.h(1, 'E6k REPORT part1 —— 推导两段（2010-2014 / 2015-2018）全部登记对象的作用量、对照与十八 Q 初读')
    rp.p('用途：plan §13.5 part1。只含推导两段；两后段按方式 A 未计算（`registration/record_B_mode_A.json`），读法标签 `%s` 只在后段首看后使用。'
         '本文件所有数字来自 `results/deriv/*.csv`（seal_deriv 之后生成），不设显著性门、不写判词；新算子 replacement_preference_status = NOT_AUTHORIZED，'
         'deployment_authorized = false。' % K.LABEL_FIRST_LOOK)
    # ---------------- §1 主展示 144
    rp.h(2, '1. 主展示 144 行（六形态 × 四测量 × 六接入，α .25 × H5）')
    rr = RD[(RD.H == 5)].pivot_table(index='desc_id', columns='mechanism', values=['rmr_deriv', 'mcse_deriv'], aggfunc='first')
    rr.columns = ['%s_%s' % (a, b) for a, b in rr.columns]
    P144 = M[M.primary144 == True].merge(rr, left_on='desc_id', right_index=True, how='left')  # noqa: E712
    for f in ('S', 'M', 'Q', 'C1'):
        t = P144[P144.meas == f].sort_values(['mother', 'op'])
        cols = ['mother', 'op', 'D_2010-2014', 'D_2015-2018', 'D', 'se_H', 'D_sc', 'D_imp', 'D_vs_native', 'D_vs_C1',
                'port_size_lo_T', 'port_size_hi_T', 'edit_gap_mean_T', 'edit_gap_absmean_T', 'turn_rel', 'exposure_type']
        cols += [c for c in ('rmr_deriv_LEGACY_POLICY_RANDOM', 'mcse_deriv_LEGACY_POLICY_RANDOM', 'rmr_deriv_NEW_COND_ISK_P5', 'mcse_deriv_NEW_COND_ISK_P5')
                 if c in t.columns]
        tt = t[[c for c in cols if c in t.columns]].rename(columns={'D': 'D_deriv', 'edit_gap_mean_T': 'edit_gap_signed_T'})
        rp.table(tt, head('测量 %s × 六形态 × 六接入' % f, 'NATIVE / SZL5 / INC1 / RP3 / NATIVE_HG10 / INC1_HG10', 'primary144'), 'E6K-P1-144-%s' % f)
    # ---------------- §2 C1_hi / SM
    rp.h(2, '2. 四条 C1_hi 与六条 SM 锚')
    t = M[(M.c1_hi == True) | (M.sm_anchor == True)].sort_values(['meas', 'mother', 'H'])  # noqa: E712
    rp.table(t[present(t, ['meas', 'mother', 'alpha', 'H', 'D_2010-2014', 'D_2015-2018', 'D', 'se_H', 'D_sc', 'D_imp', 'port_size_lo_T', 'port_size_hi_T',
                'turn_rel', 'exposure_type'])].rename(columns={'D': 'D_deriv'}), head('C1_hi（α .5 × H10 / 20）与 SM 锚（α .25 × H5）', 'NATIVE', 'c1_hi | sm_anchor', 'H 见列'),
             'E6K-P1-C1HI-SM')
    # ---------------- §3 研究块分布
    rp.h(2, '3. 研究块：α × H 网格上的分布（每格 = 测量 × 母体）')
    M['H'] = M.H.astype(float)
    grid = []
    for (fam, op, a), g in M.groupby(['family', 'op', 'alpha']):
        if fam in ('PARENT',):
            continue
        x = g.D.astype(float)
        grid.append(dict(family=fam, op=op, alpha=a, cells=int(x.notna().sum()), share_pos=float((x > 0).mean()) if x.notna().any() else np.nan,
                         q10=float(x.quantile(.1)), median=float(x.median()), q90=float(x.quantile(.9)),
                         median_vs_native=float(g.D_vs_native.median()) if 'D_vs_native' in g else np.nan))
    G = pd.DataFrame(grid)
    rp.table(G, head('全部研究描述符（按算子 × α 汇总 H 1…20 与测量 × 母体）', '各算子', '全部登记（不含 PARENT）', 'H 1…20'), 'E6K-P1-GRID')
    # ---------------- §4 机制账户（推导段）
    rp.h(2, '4. 机制账户（推导段）')
    cs = M[M.desc_id.str.startswith('CS|')]
    if len(cs):
        cs = cs.assign(block=cs.desc_id.str.split('|').str[-1])
        t = cs.groupby(['block']).agg(n_desc=('desc_id', 'count'), N1_minus_N0=('N1_minus_N0', 'mean'), C1_minus_C0=('C1_minus_C0', 'mean'),
                                       C0_minus_N0=('C0_minus_N0', 'mean'), N1_minus_C1=('N1_minus_C1', 'mean')).reset_index()
        rp.table(t, head('COMMON_SUPPORT 四账户桥（N1−N0 = (C1−C0) + (C0−N0) + (N1−C1)）', '各 CS 算子', 'α .25 × H{3,5,10,20}', '3|5|10|20',
                         'J = k0 ∧ kf 有效；K 与新测量在 J 上重做中性化与排名（X16）'), 'E6K-P1-CS')
    acc = M[M.desc_id.str.startswith('ACC|')]
    if len(acc):
        t = acc[['desc_id', 'D', 'D_vs_compare']].rename(columns={'D': 'D_deriv'})
        rp.table(t, head('INC 附属 72 与 BAND 剂量控制 288', 'INC_SUPPORT0 / INC_DOSE / DOSE_*', '附属清单', '5（剂量 3|5|10|20）',
                         'INC：C = k0 ∧ kf ∧ z_T 有效'), 'E6K-P1-ACC')
    rpf = F[F.op.astype(str).str.startswith('RP') & (F.cs == False)]  # noqa: E712
    if len(rpf):
        t = rpf.groupby('op').agg(targets=('target_id', 'count'), pairs=('rp_pairs', 'sum'), kept=('rp_kept_pairs', 'sum'),
                                  unknown=('rp_unknown_edits', 'sum'), unpaired=('rp_unpaired_structural', 'sum')).reset_index()
        t['kept_share'] = t.kept / t.pairs.replace(0, np.nan)
        rp.table(t, head('RP 编辑事实（配对 / 保留 / 未知 size 或行业 / 结构性未配对）', 'RP τ', '全部 α × 母体 × 测量 × 两段', '—', unit='计数'), 'E6K-P1-RPFACTS')
    lx = M[M.family == 'LX']
    if len(lx):
        m5 = M[(M.alpha == 0.25) & (M.H == 5)]
        base = m5.set_index(['meas', 'mother', 'op'])['D']
        rows = []
        for (f, p), g in m5[m5.family == 'LX'].groupby(['meas', 'mother']):
            for lay in ('SIZE3', 'ISK'):
                v10 = base.get((f, p, 'LX_%s_10' % lay), np.nan)
                v01 = base.get((f, p, 'LX_%s_01' % lay), np.nan)
                v11 = base.get((f, p, 'NATIVE'), np.nan)
                rows.append(dict(meas=f, mother=p, layer=lay, V10_minus_V00=v10, V01_minus_V00=v01, V11_minus_V00=v11,
                                 interaction=v11 - v10 - v01, order_avg_allocation=0.5 * (v10 + (v11 - v01)), order_avg_within=0.5 * (v01 + (v11 - v10))))
        rp.table(pd.DataFrame(rows), head('LX 四账户（V00 = 原父；V11 = NATIVE；差都是相对原父的年化配对增量）', 'LX', 'α .25 × H5',
                                          support='合法域先锁（X07-rev）'), 'E6K-P1-LX')
    band = M[(M.family == 'BAND') & (M.alpha == 0.25) & (M.H == 5)]
    if len(band):
        spec = dict(cells=('D', 'count'), median_D=('D', 'median'), median_vs_base=('D_vs_base', 'median'), median_turn_rel=('turn_rel', 'median'),
                    median_vs_C1=('D_vs_C1', 'median'))
        spec = {k: v for k, v in spec.items() if v[0] in band.columns}
        t = band.assign(kind=band.op.str.split('_').str[1].str[:2], b=band.op.str.extract(r'(\d+)$')[0].astype(int),
                        base=band.op.str.split('_').str[0]).groupby(['base', 'kind', 'b']).agg(**spec).reset_index()
        rp.table(t, head('SA / PM / HG（四测量 × 六形态）', 'BAND', 'α .25 × H5'), 'E6K-P1-BAND')
        hg = band[band.op.str.contains('_HG')]
        rows = []
        for r in hg.itertuples():
            v11 = r.D
            v10 = M.loc[(M.desc_id == r.desc_id.rsplit('|', 1)[0] + '|' + r.op.split('_')[0]), 'D']
            v01 = M.loc[(M.desc_id == 'K0|%s|a0|H5|HG_ONLY%s' % (r.mother, re.search(r'(\d+)$', r.op).group(1))), 'D']
            v10 = float(v10.iloc[0]) if len(v10) else np.nan
            v01 = float(v01.iloc[0]) if len(v01) else np.nan
            rows.append(dict(meas=r.meas, mother=r.mother, op=r.op, V11_minus_V00=v11, V10_minus_V00=v10, V01_minus_V00=v01, V11_minus_V01=v11 - v01,
                             interaction=v11 - v10 - v01))
        rp.table(pd.DataFrame(rows), head('HG 信息 × 续选规则四账户（V00 原父 / V10 无带基础 / V01 HG_ONLY / V11 HG）', 'HG', 'α .25 × H5'),
                 'E6K-P1-HG4')
    for fam in ('TREFIT', 'POST2'):
        t = M[(M.family == fam) & (M.alpha == 0.25) & (M.H == 5)]
        if len(t):
            rp.table(t[present(t, ['meas', 'mother', 'op', 'D', 'D_vs_native', 'D_vs_C1', 'port_size_lo_T', 'port_size_hi_T', 'turn_rel'])].rename(columns={'D': 'D_deriv'}),
                     head('%s（A4b 两形态）' % fam, fam, 'α .25 × H5'), 'E6K-P1-%s' % fam)
    rar = M[(M.blocks.astype(str).str.contains('RAR')) & (M.alpha == 0.25) & (M.H == 5)]
    if len(rar):
        rp.table(rar[present(rar, ['meas', 'mother', 'D', 'D_vs_native', 'port_size_lo_T', 'port_size_hi_T'])].rename(columns={'D': 'D_deriv', 'D_vs_native': 'D_vs_NATIVE_S'}),
                 head('RARPRE 2×2（W20 / W60 × LT / SE）', 'NATIVE', 'α .25 × H5'), 'E6K-P1-RAR')
    # ---------------- §5 随机层位置
    rp.h(2, '5. 随机层位置（推导段；real − 随机均值，MCSE；不作门）')
    if len(RD):
        t = RD.groupby('mechanism').agg(rows=('desc_id', 'count'), paths_min=('paths_min', 'min'), share_pos=('rmr_deriv', lambda x: float((x > 0).mean())),
                                        share_pos_2mcse=('rmr_deriv', lambda x: np.nan), median=('rmr_deriv', 'median'),
                                        worst_mcse=('mcse_deriv', 'max')).reset_index()
        t['share_pos_2mcse'] = [float(((g.rmr_deriv > 0) & (g.rmr_deriv >= 2 * g.mcse_deriv)).mean()) for _, g in RD.groupby('mechanism')]
        rp.table(t, head('随机参照（全部登记随机行）', '按机制', '随机清单全部行', '5（HG 持续性另 3|10|20）', base='同对象随机路径均值'), 'E6K-P1-RAND')
    # ---------------- §6 十八 Q 初读
    rp.h(2, '6. 十八张卡的推导段初读（机械计数；新增解释标事后；后段首看后才用首看标签）')
    cards = pd.read_csv(K.P('registry', 'cards_E6k.csv'))
    q2o = pd.read_csv(K.P('registry', 'question_to_objects_E6k.csv'))
    rows = []
    for c in cards.itertuples():
        ids = set(q2o[q2o.query_id.str.startswith('E6K-%s-' % c.card)].desc_id)
        g = M[M.desc_id.isin(ids)]
        rows.append(dict(card=c.card, objects=len(ids), with_deriv_rows=len(g), share_D_pos=float((g.D > 0).mean()) if len(g) else np.nan,
                         median_D=float(g.D.median()) if len(g) else np.nan, median_vs_native=float(g.D_vs_native.median()) if len(g) and 'D_vs_native' in g else np.nan,
                         queries=c.queries))
    rp.table(pd.DataFrame(rows), head('18 张卡的登记对象', '按卡', 'question_to_objects_E6k.csv', '各对象自身 H'), 'E6K-P1-CARDS')
    # ---------------- §7 未做项
    rp.h(2, '7. 未做项及原因')
    rp.p('- 两后段（2019-2023 / 2024-2026）全部新对象：方式 A，等用户一句话后写 `record_B_approved_E6k.json` 与条件回执（W11）。')
    rp.p('- bootstrap（段内分层 stationary 20 / 60 × 2,000）、影子库存、八子集 Shapley、衰减场景（§10.5）、SMB 与尾部账本、资本分解（§12.1）：brief §5 A2 次序在两后段封存之后。')
    rp.p('- 政策五列逐对象评分：需两后段（e-随机按两后段）与逐年 17 标签，在 part3。')
    rp.write(OUT)
    K.write_receipt('report_part1', [OUT], 'SUCCEEDED', queries=len(rp.qids))
    print('part1 写出：%d 个 query' % len(rp.qids), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
