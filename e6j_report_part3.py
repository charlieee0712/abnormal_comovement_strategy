# -*- coding: utf-8 -*-
"""生成 E6j_REPORT_part3.md（plan §10.7：P 冻结试点完整政策表（FULL / G4 并印）、全部形态与剂量、与历史对象关系、《生产变更候选清单》）。
数字全部来自 results_P/pilot_policy*.csv、diagnostics/P、accounts/P 与 E6i merged_*.csv 的结构化查询；结论词只用 通过 / 不通过 / 不可判 / 结构依赖。
--src <目录> 可指向 dryrun 以检排版（dryrun 不写 query 登记、不写回执）。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob

import numpy as np
import pandas as pd

import e6j_core as J
from e6j_report import Report

RES = J.RES
SEGS = J.SEGMENTS
FORMS = ('A4b_CVRv5', 'A4b', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
ARMS = ('S', 'M', 'SM', 'C1')


def head(**kw):
    h = dict(主体='—', 算子='生产路径 SLOT FALLBACK（W05 接入）', 分母='四段有效配对日', 基准='同形态同 H 生产母体（C0）', 子集='见表',
             单位='子 − 母 8bp 日配对增量，年化百分点', 日期='2010-01-04..2026-03-27（四段；2026 截至 03-27）', H='5（主配置）', 成本模型='8bp 线性',
             支持='native FALLBACK', 资本视图='NATIVE', exposure='见 historical_exposed 列')
    h.update(kw)
    return h


def main():
    src = sys.argv[sys.argv.index('--src') + 1] if '--src' in sys.argv else os.path.join(RES, 'results_P')
    dry = 'dryrun' in src
    pol = pd.read_csv(os.path.join(src, 'pilot_policy.csv'))
    add = pd.read_csv(os.path.join(src, 'pilot_policy_additions.csv'))
    boot = pd.read_csv(os.path.join(src, 'pilot_policy_bootstrap.csv'))
    main_ = pol[pol.main_config & pol.arm.isin(ARMS)].copy()
    R = Report('part3')
    R.h(1, 'E6j REPORT part3 —— P 冻结五臂试点：政策评分卡与《生产变更候选清单》')
    R.p('用途：P 包（登记于 2026-09-27 03:14:05）六形态四段一次算完后的政策计算（plan §4.5；RULING 第 15 项六条 + 三句加法 + 实施条件；W07–W09 锁定值）。'
        '四段都不是样本外；主母体 A4b_CVRv5 上 S / M / C1 的账户与 E6i R1 账户是同一对象（exact_alias，§5），它们的读数是历史复现，不是独立证据。'
        '结论词只有 通过 / 不通过 / 不可判 / 结构依赖；《生产变更候选清单》四个标签分开，`deployment_authorized = false`。')
    R.p('读法：D_<段> = 子 − 母 8bp 日配对增量（年化百分点）；FULL = 四段按有效配对日合并（主 profile，W07）；G4 = 四段增量中位（并印，不交叉拼接）；'
        '六条：c 四段 ≥ −0.10（NA 不自动满足）、d 逐年正 ≥ 12/17、e-资本 同资本与原生同号（0 按 1e−9 舍入容差，同资本缺 → 不可判）、'
        'e-随机 两后段对 R-MATCH-SRC（IID）随机均值为正、f 含 A=5 亿 κ=.5 冲击后仍满足 c；正向门槛 profile 值 ≥ +0.10；'
        '市值通道 逐段 |mean_t(换入 − 换出 clean 域市值百分位中位)| ≤ 5 个百分位点（无两边都有编辑日的段为 N/A，不当 0、不进闸）；Δturn > 10% 只标注。')
    R.p('判定三态（`registration/policy_P_operational_addendum.json`，读数前 2026-09-27 05:23:31 落盘）：已定的不满足项优先并全部列出 → 不通过（…）；'
        '无不满足项而有未定项 → 不可判（项:状态）；否则通过。e-随机逐后段：|真实 − 随机均值| < 2·MCSE 即"MC 误差仍影响符号"→ MC_UNRESOLVED'
        '（2 为执行端事前声明的倍数，plan 未给；不论 MCSE 是否已 ≤ .03）。MC 增补：每 (后段, 形态, 臂) 取 12 个 (α, H) 格的最大 MCSE，> .03 即以 512 路径增补（§11a）。'
        '`POLICY_INTERPRETATION_PENDING` = 主臂上 FULL 与 G4 的结论类（通过 / 不通过 / 不可判）不同，交用户裁定。')
    cols = ['arm'] + ['D_%s' % s for s in SEGS] + ['FULL', 'G4', 'years_pos', 'FULL_sc', 'e_cap_FULL', 'rand_IID_2019-2023', 'rand_IID_2024-2026',
                                                   'mcse_IID_2019-2023', 'mcse_IID_2024-2026', 'npaths_IID_2019-2023', 'npaths_IID_2024-2026', 'e_rand',
                                                   'FULL_imp', 'size_status', 'dturn_flag', 'policy_FULL', 'policy_G4', 'POLICY_INTERPRETATION_PENDING',
                                                   'structure_dependent', 'historical_exposed']
    cols = [c for c in cols if c in main_.columns]
    for i, form in enumerate(FORMS):
        R.h(2, '%d. %s（主配置 α .25 × H5）' % (i + 1, form))
        t = main_[main_.form == form][cols]
        R.table(t, head(主体='%s × 四个非恒等臂' % form, 子集='主配置 α .25 × H5'), 'P3-Q%02d' % (i + 1))
    R.h(2, '7. 三句加法（每形态；FULL / G4 分列）')
    R.table(add, head(主体='每形态主配置的合格单臂与取代规则', 算子='C1 默认；S / M 取代 C1 须 ≥ 3/4 段且合并配对差 ≥ +.05；SM 取代最佳合格单臂须合并配对差 ≥ +.10',
                      单位='臂名 / 说明'), 'P3-Q07')
    R.h(2, '8. δ 敏感与条件逐条（主母体）')
    dcols = ['arm'] + [c for c in pol.columns if c.startswith(('c_FULL_', 'f_FULL_', 'c_G4_', 'f_G4_'))] + ['d_ok', 'e_cap_FULL', 'e_cap_G4', 'e_rand',
                                                                                                            'mc_ok', 'positive_FULL', 'positive_G4',
                                                                                                            'size_status', 'size_na_segments']
    R.table(main_[main_.form == 'A4b_CVRv5'][[c for c in dcols if c in main_.columns]],
            head(主体='A4b_CVRv5 × 四臂', 单位='布尔（条件是否满足）', 子集='δ ∈ {.05, .10, .15}'), 'P3-Q08')
    R.h(2, '9. S+M 的同剂量互补（plan §4.4）')
    rows = []
    for form in FORMS:
        f = pol[(pol.form == form) & (pol.H == 5)]
        g = lambda arm, a: f[(f.arm == arm) & np.isclose(f.alpha, a)]
        for s in list(SEGS) + ['FULL']:
            k = 'D_%s' % s if s != 'FULL' else 'FULL'
            try:
                I = g('SM', 0.25)[k].iloc[0] - g('S', 0.125)[k].iloc[0] - g('M', 0.125)[k].iloc[0]
                rows.append(dict(form=form, span=s, I_interaction=I, SM25_minus_S25=g('SM', 0.25)[k].iloc[0] - g('S', 0.25)[k].iloc[0],
                                 SM25_minus_M25=g('SM', 0.25)[k].iloc[0] - g('M', 0.25)[k].iloc[0]))
            except IndexError:
                pass
    R.table(pd.DataFrame(rows), head(主体='六形态 H5', 算子='I = V(S.125,M.125) − V(S.125,0) − V(0,M.125) + V(0,0)（V 为对母体增量，V(0,0) = 0）',
                                     子集='四段与合并'), 'P3-Q09')
    R.h(2, '10. 统计不确定性（主对象）')
    R.table(boot, head(主体='六形态 × 四臂主配置', 算子='平稳块自助 FULL（块均长 20 / 60，2,000 次，四段内分别抽、共享 draw）',
                       单位='分位（年化百分点）；centered = 零均值参照（不是收益区间）'), 'P3-Q10')
    sc = ['form', 'arm', 'FULL', 'FULL_se_H', 'FULL_MDE80'] + ['se_H_%s' % s for s in SEGS] + ['MDE80_%s' % s for s in SEGS]
    R.table(main_[[c for c in sc if c in main_.columns]], head(主体='主对象', 算子='HAC（Bartlett，滞后 H；原日历 mask）；MDE80 = 2.80·SE',
                                                              单位='年化百分点'), 'P3-Q11')
    R.h(2, '11. 诊断（CS 四账户闭合 / TRANSPORT / T 双开关 / 同 N / 编辑账本 / 影子库存）')
    dg = [p for p in sorted(glob.glob(os.path.join(RES, 'diagnostics', 'P', '*', 'diagnostics_*.csv')))]
    if dg:
        d = pd.concat([pd.read_csv(p) for p in dg], ignore_index=True)
        for kind, qid in (('CS', 'P3-Q12'), ('TRANSPORT', 'P3-Q13'), ('TREFIT', 'P3-Q14'), ('MATCHN', 'P3-Q15')):
            x = d[d['diag'] == kind].dropna(axis=1, how='all')
            if kind in ('CS', 'TRANSPORT', 'MATCHN'):
                x = x[x.H == 5]
            R.table(x, head(主体='六形态 × 四臂（α .25）', 算子=kind, 子集='H5'), qid)
        x = d[d['diag'].str.startswith('EDIT')].dropna(axis=1, how='all')
        R.table(x, head(主体='六形态 × 四臂（α .25）', 算子='决策编辑账本：形成日原因 → 线性批次映射到收益日的 gross 贡献（费用单列）', 子集='H5'), 'P3-Q16')
        x = d[d['diag'].str.startswith('SHADOW')].dropna(axis=1, how='all')
        R.table(x, head(主体='六形态 × 四臂（α .25）与母体', 算子='影子账户 ideal（全可成交）/ X1（买卖标志限制）', 资本视图='固定名义 5 亿',
                        单位='超额年化百分点 / 未成交金额'), 'P3-Q17')
    else:
        R.p('诊断产物尚未生成（dryrun）。')
    # ---- 11a MC 增补轮次
    R.h(3, '11a. MC 增补（R-MATCH-SRC IID，两后段）')
    mcs = sorted(glob.glob(os.path.join(RES, 'checks', 'mc_topup_P_round*.csv')), key=lambda p: int(p.split('round')[-1][:-4]))
    if mcs:
        rr = []
        for p in mcs:
            m = pd.read_csv(p)
            rr.append(dict(round=int(p.split('round')[-1][:-4]), cells=len(m), cells_over_03=int(m.over_target.sum()), mcse_max=float(m.mcse.max()),
                           mcse_median=float(m.mcse.median()), n_paths_min=int(m.n_paths.min()), n_paths_max=int(m.n_paths.max())))
        R.table(pd.DataFrame(rr), head(主体='两后段 × 六形态 × 四主臂 × 12 个 (α, H) 格', 算子='MCSE = 随机路径年化 net8 的 sd / √n（真实账户固定）；'
                                       '每 (段, 形态, 臂) 取 12 格最大 MCSE > .03 → 512 路径增补（新 path_index，不挑 seed）', 单位='年化百分点 / 路径数',
                                       基准='—'), 'P3-Q22')
    else:
        R.p('MC 增补尚未运行。')
    # ---- 11b CS_FROZEN_SCORE 与 11c 回撤对
    ext = os.path.join(src, 'cs_frozen_score.csv')
    if os.path.exists(ext):
        fz = pd.read_csv(ext)
        R.h(3, '11b. CS_FROZEN_SCORE 附表（只缩域、保留全池评分；与重估 CS 分列）')
        R.table(fz[fz.H == 5].dropna(axis=1, how='all'), head(主体='六形态 × 四臂（α .25）', 算子='J 上只缩域：q0 与新分量保留全池中性化 / 排序；'
                                                             '闭合 N1−N0 = (C1F−C0F)+(C0F−N0)+(N1−C1F)；右侧 CS_reestimated_* 为 J 上重估的 CS（§11 P3-Q12）',
                                                             子集='H5', 支持='COMMON_SUPPORT（FROZEN_SCORE / 重估 并列）'), 'P3-Q23')
        dd = pd.read_csv(os.path.join(src, 'drawdown_pair.csv'))
        R.h(3, '11c. 回撤：超额路径回撤 与 账户财富回撤 分列（plan §8.5）')
        R.table(dd, head(主体='六形态 × 四臂主配置与同形态母体', 算子='超额路径回撤 = 源 net8 日序列累计和（百分点）的最大回撤（子 / 母 / 子−母差路径）；'
                                                           '账户财富回撤 = 自融资 shadow NAV（日初 NAV 为资本基数；ideal / X1）逐段最大回撤比率，段间不拼接',
                         单位='超额：累计百分点；财富：比率（0–1）', 资本视图='超额：源名义资本；财富：自融资 shadow'), 'P3-Q24')
        R.p('两种回撤定义不同、不互换：累计超额路径不是投资财富；自融资 shadow 才对应账户财富回撤（其 NAV 含市场暴露，不是超额）〔P3-Q24〕。')
    R.h(2, '12. 列对象（不评分）')
    colo = pol[pol.arm.str.startswith('COL') & np.isclose(pol.alpha, 0.25) & (pol.H == 5)][['form', 'arm'] + ['D_%s' % s for s in SEGS] + ['FULL', 'G4']]
    R.table(colo, head(主体='K_rarpre / K_samt20 / AMT4（四分量各 α/4 回退）', 子集='α .25 × H5'), 'P3-Q18')
    R.h(2, '13. 探索网格（α × H，标明探索，不进结论句）')
    grid = pol[pol.arm.isin(ARMS)].groupby(['form', 'arm', 'alpha', 'H'])['FULL'].first().unstack('H').reset_index()
    R.table(grid, head(主体='六形态 × 四臂', 子集='α {.125,.25,.5} × H {3,5,10,20}', H='见列', 单位='FULL 年化百分点'), 'P3-Q19')
    nm = pol[pol.arm.isin(ARMS) & ~pol.main_config & (pol.policy_FULL == '通过')]
    nm = nm[~nm.set_index(['form', 'arm']).index.isin(main_[main_.policy_FULL == '通过'].set_index(['form', 'arm']).index)]
    R.p('exploratory_next_candidate（plan §8.6：非主配置在 FULL profile 下"通过"、而同形态同臂的主配置未通过；只作下一轮冻结的线索，不进候选清单）：')
    R.table(nm[['form', 'arm', 'alpha', 'H', 'FULL', 'G4', 'policy_FULL', 'policy_G4', 'dturn_flag', 'historical_exposed']] if len(nm) else
            pd.DataFrame([dict(说明='无')]), head(主体='非主配置（α × H 探索网格）', 子集='主配置未通过的 (形态, 臂)', H='见列', exposure='探索；选择史见暴露台账'), 'P3-Q25')
    R.h(2, '14. 与历史对象的关系：主母体别名交叉核对')
    rows = []
    for seg in SEGS:
        e = pd.concat([pd.read_csv(os.path.join(J.E6I_RES, 'accounts', seg, 'merged_%s.csv' % r)) for r in ('RA', 'RK')], ignore_index=True).set_index('descriptor_id')
        s = pd.read_csv(os.path.join(RES, 'accounts', 'P', seg, 'summary.csv'))
        s = s[(s.form == 'A4b_CVRv5') & s.arm.isin(['S', 'M', 'C1', 'COL:K_rarpre', 'COL:K_samt20'])]
        route = {'S': ('RA', 'K_rar20', 'low_bad'), 'M': ('RK', 'K_slope20', 'low_bad'), 'C1': ('RK', 'K_MA3_E6F', 'high_bad'),
                 'COL:K_rarpre': ('RA', 'K_rarpre', 'low_bad'), 'COL:K_samt20': ('RK', 'K_samt20', 'low_bad')}
        for _, r in s.iterrows():
            ro, mem, d_ = route[r.arm]
            did = '%s|R1|%s|SLOT|a=%s|%s:FALLBACK|H%d' % (ro, mem, r.alpha, d_, r.H)
            if did in e.index:
                rows.append(dict(segment=seg, arm=r.arm, alpha=r.alpha, H=r.H, E6j_net8_ann=r.net8_ann, E6i_net8_ann=float(e.loc[did, 'net8_ann']),
                                 abs_diff=abs(r.net8_ann - float(e.loc[did, 'net8_ann']))))
    al = pd.DataFrame(rows)
    R.table(al.groupby(['segment', 'arm']).agg(n=('abs_diff', 'size'), max_abs_diff=('abs_diff', 'max')).reset_index(),
            head(主体='A4b_CVRv5（生产路径，E6j）vs R1（研究引擎，E6i）同一描述符', 算子='净值年化逐描述符比对', 单位='最大绝对差（年化百分点）',
                 子集='S / M / C1 与 K_rarpre / K_samt20 全网格（α × H）', exposure='E6i 已暴露（alias_of）'), 'P3-Q20')
    if os.path.exists(os.path.join(src, 'robustness_main.csv')):
        R.h(2, '15. 年度稳定性与稳健性（plan §8.5；主配置）')
        rb = pd.read_csv(os.path.join(src, 'robustness_main.csv'))
        rcols = ['form', 'arm', 'FULL', 'G4', 'c', 'years_pos_17', 'years_n', 'years_pos_2010_2025', 'worst_year', 'worst_year_D', 'LOYO_FULL_min',
                 'LOYO_FULL_max', 'LOYO_G4_min', 'LOYO_c_fail_years', 'ex2015_2016_FULL', 'ex2015_2016_c', 'ex2020_FULL', 'ex2020_c',
                 'recent_D_2024_2026', 'recent_se_H']
        R.table(rb[[c for c in rcols if c in rb.columns]], head(主体='六形态 × 四臂主配置', 算子='逐一留一年 / 去 2015+2016 / 去 2020 后重算 FULL、G4 与 c（d 不重定义分母）；'
                                                             '最近段 = 2024-01-02..2026-03-27 单独列', 子集='α .25 × H5',
                                                             exposure='去除年份来自历史已暴露问题，不是新随机样本；不以删年版本替代主结果'), 'P3-Q26')
        ycols = ['form', 'arm'] + ['Y%d' % y for y in range(2010, 2027)]
        R.table(rb[[c for c in ycols if c in rb.columns]], head(主体='六形态 × 四臂主配置', 算子='逐年配对增量（2026 截至 03-27，partial）', 子集='α .25 × H5',
                                                             日期='2010..2026（16 完整年 + 2026 partial）'), 'P3-Q27')
        qcols = ['form', 'arm', 'daily_mean_bp', 'daily_median_bp', 'daily_q05_bp', 'daily_q25_bp', 'daily_q75_bp', 'daily_q95_bp', 'worst_day_bp', 'worst_day',
                 'tail_ES5_bp', 'top1pct_days_contrib', 'best_year_contrib', 'worst_year_contrib', 'top1pct_days_share', 'concentration_note'] + \
                [c for c in rb.columns if c.startswith(('entry_weight_share_', 'exit_weight_share_'))]
        R.table(rb[[c for c in qcols if c in rb.columns]], head(主体='六形态 × 四臂主配置', 算子='日增量分布（基点）、最差 5% 日均（尾部）、前 1% |d| 日与最好 / 最差年对 FULL 的带符号贡献（年化百分点）；'
                                                             '编辑资本占比 = 形成日子在换入者上 / 母在换出者上的目标权重份额', 子集='α .25 × H5',
                                                             单位='基点 / 年化百分点 / 份额'), 'P3-Q28')
        R.h(2, '16. 机会基线与"按规则挑最佳合格单臂"的整个程序（plan §8.3–§8.4）')
        ob = pd.read_csv(os.path.join(src, 'opportunity_baseline.csv'))
        R.table(ob, head(主体='六形态 × 四臂主配置的随机新增分量（各机制；主 = R-MATCH-SRC IID）', 算子='逐路径（0–1,023，四段齐全）按冻结规则算 c / d / 正向门槛；'
                                                                                '比例 = 固定历史与该生成机制下的机会基线，不是 p 值、不是实盘失败概率',
                         子集='α .25 × H5', 单位='比例 / 年化百分点', 基准='同形态同 H 母体'), 'P3-Q29')
        R.p('e-资本 / e-随机 / f / 市值逐路径不可算（随机层未存逐路径同资本、冲击与市值账本），未伪造；MA3（C1）是有历史效果的主动基线、identity 是真零，二者都不是本表的零假设〔P3-Q29〕。')
        for fn, lab, qid in (('selection_bootstrap.csv', '未中心化（点估区间）', 'P3-Q30'), ('selection_bootstrap_centered.csv', '中心化（零均值基线，不是收益区间）', 'P3-Q31')):
            sb = pd.read_csv(os.path.join(src, fn))
            R.table(sb, head(主体='每形态"三句加法"选择程序', 算子='平稳块自助（块均长 20 / 60，2,000 次，四段内抽、共享 draw）：每 draw 重算 c / d / e-资本 / e-随机 / f / 正向门槛'
                                                         '（市值静态、随机均值固定）、FULL / G4 与选择；program = 所选臂对母体增量（无选择 = 0）',
                             单位='比例 / 年化百分点', 子集='α .25 × H5；%s' % lab), qid)
        R.h(2, '17. 同时带、多重性与可分辨量（plan §8.4）')
        bd = pd.read_csv(os.path.join(src, 'simultaneous_bands.csv'))
        R.table(bd, head(主体='每形态 7 个对比（四臂 − 母、S / M / SM − C1）', 算子='bootstrap max-t 同时带（SE = bootstrap sd；零 sd 列不入族）与逐点 ±1.96·sd 并列；无新 FWER 门',
                         子集='α .25 × H5', 单位='年化百分点'), 'P3-Q32')
        mu = pd.read_csv(os.path.join(src, 'multiplicity.csv'))
        R.table(mu, head(主体='P 包各族与主对象', 算子='账户数 / 问题 / 随机规模 / 同时带分位；MDE80 = 2.80·SE（HAC 滞后 H）；T_required = T·(MDE80/δ)²，δ = .10',
                         单位='个 / 年化百分点 / 年'), 'P3-Q33')
        R.p('T_required 只是依赖当前方差与正态近似的静态尺度提示，不是采纳所需等待年数，也不说明 E7 没有信息〔P3-Q33〕。')
        R.h(2, '18. 合成臂成员 c 状态并印')
        mc = pd.read_csv(os.path.join(src, 'member_c_status.csv'))
        R.table(mc, head(主体='SM（S / M 各半剂量）与 AMT4（四个 amount 成员各 α/4）', 算子='c = 四段 D ≥ −.10；成员与合成同形态、同 α、同 H',
                         单位='布尔 / 年化百分点'), 'P3-Q34')
        R.p('合成通过不代表每个成员都满足 c；AMT4 为列对象、不评分，只有 K_samt20 有本轮单独账户〔P3-Q34〕。')
    R.h(2, '19. 《生产变更候选清单》')
    cand = main_[main_.policy_FULL == '通过'][['form', 'arm', 'alpha', 'H', 'FULL', 'G4', 'policy_FULL', 'policy_G4', 'POLICY_INTERPRETATION_PENDING',
                                               'mechanism_status', 'replication_status', 'deployment_authorized', 'dturn_flag', 'size_status', 'structure_dependent']]
    if len(cand):
        R.table(cand, head(主体='政策计算 FULL profile 下"通过"的主对象', 算子='四标签分开：policy_score / mechanism_status / replication_status / deployment_authorized',
                           单位='—'), 'P3-Q21')
    else:
        R.p('按冻结政策计算，主配置没有"通过"的对象；清单为空〔P3-Q01–Q06〕。')
    pend = main_[main_.POLICY_INTERPRETATION_PENDING][['form', 'arm', 'FULL', 'G4', 'policy_FULL', 'policy_G4']]
    R.p('FULL 与 G4 结论类不同的主对象（`POLICY_INTERPRETATION_PENDING`，主解释仍为 FULL，差异交用户裁定）：')
    R.table(pend if len(pend) else pd.DataFrame([dict(说明='无')]), head(主体='主对象', 单位='年化百分点 / 结论'), 'P3-Q35')
    R.p('清单只是固定计算政策下的候选：不改生产、不自动读 E7；deployment_authorized 永远由用户改；对外数字须用户过目。')
    R.h(2, '20. 限制')
    R.p('- 四段非样本外；S 方向为 E6i 对照方向事后转正（direction_2of1）；S / M / C1 与两列对象在主母体上 = E6i 已见账户。')
    R.p('- 随机参照为 R-MATCH-SRC（Z-MAP basic 匹配条件，E6j 稳定哈希种子）；其余机制（P5 / COND / COND_IID / EDIT / EDIT_IID / EDITB）只作诊断，结果在 randoms/P 与本表 rand_* 列。')
    R.p('- 冲击为源平方根模型的事后加性成本（不改库存）；影子库存账户只对主对象与母体做 H5。')
    if dry:
        print(R.text()[:3000]); return 0
    out = os.path.join(RES, 'reports', 'E6j_REPORT_part3.md')
    sha = R.write(out)
    J.write_receipt('report_part3', [out], 'SUCCEEDED', n_tables=len(R.qids))
    print('part3 written', sha[:12], len(R.qids))
    return 0


if __name__ == '__main__':
    sys.exit(main())
