# -*- coding: utf-8 -*-
"""E6k_REPORT_mechanisms（plan §13.5：LX 归因、八条件随机、RP、TREFIT、实际编辑 / 交易与 gross 闭合；plan §6 / §7 / §10 / §12）。
输入：results/full/policy_E6k.csv（四段 D / 相对比较）、diagnostics/mechanisms/<段>_{shapley,capital,lx_gross}.csv、diagnostics/risk/<段>_{smb,tails}.csv、
diagnostics/shadow/<段>.csv、results/full/descriptor_stats_<段>.csv（COMMON_SUPPORT 桥、附属）、registry/mask_facts_*（编辑事实）。
名称只写"算法 / 账户效应"：Shapley 是改变置换条件的算法效应、LX 是配额 / 优先序移植、gross 账本是特征匹配基准分解，均不是因果份额（plan §2.5 / §6.1 / §10.1）。"""
import e6k_boot  # noqa: F401
import os
import sys
import glob

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_report as RP
import e6k_seal as SEAL

OUT = K.P('reports', 'E6k_REPORT_mechanisms.md')
DATES = '2010-01-04..2026-03-27（四段）'


def head(subject, sub, H='5', unit='年化百分点', expo='见 policy_E6k.evidence_exposure', support='原生（FALLBACK）'):
    return {'主体': subject, '算子': '见列', '分母': '四段有效配对日（n 加权）', '基准': '同 H 原父（8bp）或见列', '子集': sub, '单位': unit, '日期': DATES,
            'H': H, '成本模型': '源 8bp', '支持': support, '资本视图': '实际源 DEV', 'exposure': expo}


def cat(pattern):
    fs = sorted(glob.glob(K.P(*pattern.split('/'))))
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else pd.DataFrame()


def full(df, col, ncol='n'):
    """跨段 n 加权合并（每 desc_id）。"""
    g = df.dropna(subset=[col])
    return g.groupby('desc_id').apply(lambda x: float(np.average(x[col], weights=x[ncol])) if x[ncol].sum() > 0 else np.nan)


def main():
    for pkg in ('deriv', 'post'):
        ok, bad = SEAL.verify(pkg)
        if not ok:
            raise RuntimeError('seal_%s 核对失败：%s' % (pkg, bad[:5]))
    P = pd.read_csv(K.P('results', 'full', 'policy_E6k.csv'))
    rp = RP.Report('mechanisms')
    rp.h(1, 'E6k REPORT mechanisms —— 层配置 / 层内选择、条件随机、名单修复、第二关与交易安排')
    rp.p('用途：plan §13.5 mechanisms。所有分解都是算法 / 账户层的明确干预或记账恒等式，不是经济因果份额；完整账户的成本另收、不按 gross 份额分摊。')
    m5 = P[(P.alpha == 0.25) & (P.H == 5)].set_index(['meas', 'mother', 'op'])
    # LX 四账户
    rows = []
    for (f, p), _ in P[(P.family == 'LX') & (P.alpha == 0.25) & (P.H == 5)].groupby(['meas', 'mother']):
        for lay in ('SIZE3', 'ISK'):
            v10 = m5.FULL.get((f, p, 'LX_%s_10' % lay), np.nan)
            v01 = m5.FULL.get((f, p, 'LX_%s_01' % lay), np.nan)
            v11 = m5.FULL.get((f, p, 'NATIVE'), np.nan)
            rows.append(dict(meas=f, mother=p, layer=lay, allocation_at_old=v10, within_at_old=v01, interaction=v11 - v10 - v01, V11_minus_V00=v11,
                             order_avg_allocation=0.5 * (v10 + v11 - v01), order_avg_within=0.5 * (v01 + v11 - v10)))
    rp.table(pd.DataFrame(rows), head('LX 四账户（FULL；V00 = 原父）', 'α .25 × H5 × 四测量 × 八母体', support='合法域先锁（X07-rev）'), 'E6K-MX-LX4')
    lg = cat('diagnostics/mechanisms/*_lx_gross.csv')
    if len(lg):
        t = lg.groupby(['desc_id', 'child']).agg(within_group=('within_group_ann', 'mean'), allocation=('allocation_ann', 'mean'),
                                                  allocation_excess=('allocation_excess_ann', 'mean'), total=('total_ann', 'mean'),
                                                  closure_resid_max=('closure_resid', 'max')).reset_index()
        rp.table(t, head('§6.1 gross 特征匹配账本（段均；组内差 + 组配置；成本不分摊）', 'LX 与对应 NATIVE（α .25 × H5）'), 'E6K-MX-LXGROSS')
    sh = cat('diagnostics/mechanisms/*_shapley.csv')
    if len(sh):
        cols = [c for c in sh.columns if c.startswith(('shapley_', 'rand_net_'))]
        t = sh.groupby('desc_id')[cols + ['closure_net']].mean().reset_index()
        rp.table(t, head('八子集条件置换：各子集随机均值与 I / S / K 六顺序 Shapley 差（段均；算法效应）', '24 个 NATIVE 主配置',
                         expo='随机路径（无登记读数）'), 'E6K-MX-SHAPLEY')
    # RP 链
    rows = []
    for (f, p), _ in P[(P.family == 'RP') & (P.alpha == 0.25) & (P.H == 5)].groupby(['meas', 'mother']):
        nat = m5.FULL.get((f, p, 'NATIVE'), np.nan)
        pa = m5.FULL.get((f, p, 'RPINF'), np.nan)
        r = dict(meas=f, mother=p, NATIVE=nat, PAIR_ALL=pa, NATIVE_minus_PAIR_ALL=nat - pa)
        for tau in ('0p5', '1', '3'):
            r['RP%s' % tau] = m5.FULL.get((f, p, 'RP%s' % tau), np.nan)
            r['RP%s_minus_PAIR_ALL' % tau] = r['RP%s' % tau] - pa
        rows.append(r)
    rp.table(pd.DataFrame(rows), head('RP 链：NATIVE → PAIR_ALL（结构限制代价）→ RP τ（预算代价）', 'α .25 × H5'), 'E6K-MX-RP')
    for fam in ('TREFIT', 'POST2'):
        t = P[(P.family == fam) & (P.alpha == 0.25) & (P.H == 5)][['meas', 'mother', 'op', 'FULL', 'G4', 'FULL_vs_native', 'FULL_vs_C1']]
        rp.table(t, head('%s（A4b 两形态）' % fam, 'α .25 × H5'), 'E6K-MX-%s' % fam)
    # INC 链与剂量
    acc = cat('results/full/descriptor_stats_*.csv')
    if len(acc):
        a = acc[acc.desc_id.str.startswith('ACC|')]
        t = a.groupby('desc_id').apply(lambda x: pd.Series(dict(D=np.average(x.D, weights=x.n) if x.n.sum() > 0 else np.nan,
                                                                  D_vs_compare=np.average(x.D_vs_compare.fillna(0), weights=x.n) if x.n.sum() > 0 else np.nan))).reset_index()
        rp.table(t, head('INC 附属（INC_SUPPORT0 / INC_DOSE）与 BAND 剂量控制：FULL 与相对比较对象', '附属清单', 'H 见描述符'), 'E6K-MX-ACC')
        cs = acc[acc.desc_id.str.startswith('CS|')]
        if len(cs):
            t = cs.groupby('desc_id')[['N1_minus_N0', 'C1_minus_C0', 'C0_minus_N0', 'N1_minus_C1']].mean().reset_index()
            t['block'] = t.desc_id.str.split('|').str[-1]
            tb = t.groupby('block').agg(n_desc=('desc_id', 'count'), N1_minus_N0=('N1_minus_N0', 'mean'), C1_minus_C0=('C1_minus_C0', 'mean'),
                                        C0_minus_N0=('C0_minus_N0', 'mean'), N1_minus_C1=('N1_minus_C1', 'mean')).reset_index()
            rp.table(tb, head('COMMON_SUPPORT 四账户桥（段均后按算子块平均；逐描述符全表见 results/full/descriptor_stats_<段>.csv 的 CS| 行）',
                              'α .25 × H{3,5,10,20}', 'H 3|5|10|20', support='J = k0 ∧ kf'), 'E6K-MX-CS')
    # HG 四账户
    rows = []
    for r in P[(P.family == 'BAND') & P.op.str.contains('_HG') & (P.alpha == 0.25) & (P.H == 5)].itertuples():
        base = r.op.split('_')[0]
        v10 = m5.FULL.get((r.meas, r.mother, base), np.nan)
        b = r.op[-2:].lstrip('G')
        v01 = P[(P.desc_id == 'K0|%s|a0|H5|HG_ONLY%s' % (r.mother, b))].FULL
        v01 = float(v01.iloc[0]) if len(v01) else np.nan
        rows.append(dict(meas=r.meas, mother=r.mother, op=r.op, V11=r.FULL, V10=v10, V01=v01, info_margin_V11_minus_V01=r.FULL - v01,
                         rule_V01_minus_V00=v01, interaction=r.FULL - v10 - v01))
    rp.table(pd.DataFrame(rows), head('HG 信息 × 续选规则四账户（FULL；V00 = 原父）', 'α .25 × H5'), 'E6K-MX-HG4')
    hc = sorted(glob.glob(K.P('diagnostics', 'hg_continuous', 'hg_continuous_v2_*.csv')))
    if hc:                                                              # 执行端补充 X09：跨段连续状态诊断（v2；v1 因预热日清空状态而退化，见 lessons 24）
        h = pd.concat([pd.read_csv(f) for f in hc], ignore_index=True)
        t = h.groupby('segment').agg(objects=('desc_id', 'count'), init_from_prev=('init_from_prev_segment', 'mean'),
                                     gate_cells_diff_median=('gate_cells_diff', 'median'), gate_cells_diff_max=('gate_cells_diff', 'max'),
                                     D_cont_minus_reset_median=('D_continuous_minus_reset', 'median'),
                                     D_cont_minus_reset_min=('D_continuous_minus_reset', 'min'),
                                     D_cont_minus_reset_max=('D_continuous_minus_reset', 'max')).reset_index()
        rp.table(t, head('HG 跨段连续状态诊断 v2（上段末门内成员带到本段第一个形成日；连续 − 段首空状态，逐日配对）', '48 个 HG 主展示对象（α .25 × H5）',
                         unit='计数 / 年化百分点', expo='主对象（诊断，不改登记账户）'), 'E6K-MX-HGCONT')
        rp.p('逐对象见 `diagnostics/hg_continuous/hg_continuous_v2_*.csv`；v1（`hg_continuous_<段>_<段>.csv`）的上段末状态在段首预热日（门域 K = 0）被清空，连续 − 重置恒为 0，保留不删、不作读数。')
    cap = cat('diagnostics/mechanisms/*_capital.csv')
    if len(cap):
        t = cap.groupby('desc_id')[['selection_ann', 'capital_ann', 'one_sided_dE_ann']].mean().reset_index()
        mains = set(P[P.primary144.astype(bool) | P.c1_hi.astype(bool) | P.meas.eq('SM')].desc_id)
        rp.table(t[t.desc_id.isin(mains)], head('§12.1 资本分解（段均；两边有仓日 ΔE = 选股 + 资本；一边零仓日单列；表内 = 主对象，全部 %d 个见 '
                                                 'diagnostics/mechanisms/<段>_capital.csv）' % len(t), '主展示 144 + C1_hi + SM'), 'E6K-MX-CAP')
    smb = cat('diagnostics/risk/*_smb.csv')
    if len(smb):
        t = smb.groupby(['desc_id', 'universe'])[['alpha_ann', 'beta', 'r2', 'D_ann', 'alpha_over_D']].mean().reset_index()
        rp.table(t, head('SMB 暴露回归（段均；E6j S3 同构造；截距占比只作描述）', '144 + C1_hi + SM'), 'E6K-MX-SMB')
    tails = cat('diagnostics/risk/*_tails.csv')
    if len(tails):
        tt = tails[tails.bucket != 'worst1pct_days'].groupby(['desc_id', 'bucket'])[['capital_share_delta', 'gross_contrib_delta_ann']].mean().reset_index()
        rp.table(tt, head('clean 分桶（小盘 ≤ .3 / 中 / 大盘 > .7 / 未知）资本份额差与 gross 贡献差（段均）', '144 + C1_hi + SM'), 'E6K-MX-TAILS')
    shd = cat('diagnostics/shadow/*.csv')
    if len(shd):
        t = shd.groupby(['desc_id', 'view'])[['excess_ann', 'child_minus_parent_ann', 'unfilled_buy', 'unfilled_sell', 'trapped_mean']].mean().reset_index()
        rp.table(t, head('实施影子账户（ideal = 同库存模型全可成交；X1 = 源限制库存）', '160 个 shadow 对象', support='E6g 库存模型'), 'E6K-MX-SHADOW')
    rp.write(OUT)
    K.write_receipt('report_mechanisms', [OUT], 'SUCCEEDED', queries=len(rp.qids))
    print('mechanisms 写出：%d 个 query' % len(rp.qids), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
