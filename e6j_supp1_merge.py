# -*- coding: utf-8 -*-
"""E6j supplement_1 合并与报告（事后口径；VERIFY_brief §6 S1–S5）。读 results_P/supplement_1/seg/<段>/*.csv（e6j_supp1_seg.py）
与已封存 P 包的 results_P/*.csv；不改 pilot_policy.csv、不改 REPORT / 登记；不写 reports/、task_status/、query_registry.json。
产物全部写 results_P/supplement_1/：size_exposure_layers.csv / size_exposure_grid.csv / policy_rescore_calibers.csv /
policy_rescore_counts.csv / policy_rescore_additions.csv / size_neutral_alpha.csv / leader_vocab_deviation.csv / marginality_table.csv /
selftest.csv / E6j_REPORT_supplement_1.md / query_registry_supplement_1.json / receipts/*.json。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import hashlib

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_stats as ST
import e6j_policy_p as PP
from e6j_report import Report

SUP = os.path.join(J.RES, 'results_P', 'supplement_1')
RP = os.path.join(J.RES, 'results_P')
SEGS = list(J.SEGMENTS)
MAIN = ('S', 'M', 'SM', 'C1')
DATES = {'2010-2014': '2010-01-04..2014-12-31', '2015-2018': '2015-01-05..2018-12-28', '2019-2023': '2019-01-02..2023-12-29',
         '2024-2026': '2024-01-02..2026-03-27'}
CALIBERS = ([('edit_%d' % k, '编辑层 |mean_t gap_t| ≤ %d 百分位点（5 = 登记值）' % k) for k in (5, 10, 15, 20)] + [('edit_none', '编辑层无门')] +
            [('port_%d' % k, '组合层（目标权重）|mean_t(子 − 母)| ≤ %d 百分位点' % k) for k in (1, 2, 3, 5)] +
            [('leader_daily', '领导词表 A：每日 max_b(Σw_b − share_b) ≤ 3%（源 DEV 口径，未归一，只看超配）'),
             ('leader_mean', '领导词表 B：逐段 mean_t max_b(Σw_b − share_b) ≤ 3%'),
             ('leader_vs_parent', '领导词表 C：逐段 mean_t max_b ≤ max(3%, 母体同值)'),
             ('disclose', '只披露、不设门')])


def receipt(task, outputs, **kw):
    d = os.path.join(SUP, 'receipts'); os.makedirs(d, exist_ok=True)
    J.atomic_write_json(os.path.join(d, '%s.json' % task), dict(task_id=task, status='SUCCEEDED', written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
                                                               outputs={os.path.relpath(p, J.RES): J.sha_file(p) for p in outputs}, **kw))


def load(name):
    return pd.concat([pd.read_csv(os.path.join(SUP, 'seg', s, '%s.csv' % name)) for s in SEGS], ignore_index=True)


def status_from(vals, k):
    v = np.asarray(vals, float)
    if np.all(np.isnan(v)):
        return 'N/A'
    return 'FAIL' if np.nanmax(np.abs(v)) > k else 'PASS'


def additions(df):
    """= e6j_policy_p 三句加法（逐字搬运其规则）。"""
    def merged_diff(m, a1, a2, prof):
        d = np.array([m.loc[a1, 'D_%s' % s] - m.loc[a2, 'D_%s' % s] for s in SEGS], float)
        n = np.array([m.loc[a1, 'n_%s' % s] for s in SEGS], float)
        full, g4 = ST.full_g4(d, n)
        return (full if prof == 'FULL' else g4), d
    out = []
    for form in PP.FORMS:
        for prof in ('FULL', 'G4'):
            m = df[(df.form == form) & (df.main_config)].set_index('arm')
            elig = [a for a in ('C1', 'M', 'S') if a in m.index and m.loc[a, 'policy_' + prof] == '通过']
            best = sorted(elig, key=lambda a: (-m.loc[a, prof], ('C1', 'M', 'S').index(a)))[0] if elig else None
            chosen = None
            if 'C1' in elig:
                chosen = 'C1'; beat = []
                for arm in ('M', 'S'):
                    if arm in elig:
                        md, dseg = merged_diff(m, arm, 'C1', prof)
                        if int((dseg >= 0.05).sum()) >= 3 and md >= 0.05:
                            beat.append((md, arm))
                if beat:
                    chosen = sorted(beat, key=lambda x: (-x[0], ('M', 'S').index(x[1])))[0][1]
            elif elig:
                chosen = best
            if 'SM' in m.index and m.loc['SM', 'policy_' + prof] == '通过':
                if best is None:
                    chosen = 'SM'
                else:
                    md, _ = merged_diff(m, 'SM', best, prof)
                    if md >= 0.10:
                        chosen = 'SM'
            out.append(dict(form=form, profile=prof, eligible='|'.join(elig), chosen=chosen or '无'))
    return out


def main():
    t0 = time.time()
    lay = load('layers'); reg = load('regress'); stt = load('stats'); pool = load('pool0')
    pol = pd.read_csv(os.path.join(RP, 'pilot_policy.csv'))
    boot = pd.read_csv(os.path.join(RP, 'pilot_policy_bootstrap.csv'))
    outs = []

    def w(name, df):
        p = os.path.join(SUP, name); J.atomic_write_csv(p, df); outs.append(p); return p
    # ---- 自测
    self_ = stt[stt.universe == 'SELFTEST'][['segment', 'check', 'value']].copy()
    self_['status'] = np.where(self_.value.abs() <= 1e-12, 'PASS', 'FAIL')
    w('selftest.csv', self_)
    # ---- S1
    key = ['segment', 'form', 'arm', 'alpha']
    mainlay = lay[(lay.main_config) | (lay.arm == 'C0')].copy()
    w('size_exposure_layers.csv', mainlay)
    w('size_exposure_grid.csv', lay[key + ['main_config', 'tw_diff_mean', 'tw_diff_sd', 'tw_days', 'tw_child_mean', 'tw_parent_mean', 'names_diff_mean',
                                           'small_diff_mean', 'large_diff_mean', 'edit_gap_mean', 'edit_gap_absmean', 'edit_gap_summary']])
    # ---- S3
    r3 = reg[reg.arm != 'C0'].copy()
    full = []
    for (form, arm, uni), g in r3.groupby(['form', 'arm', 'universe']):
        n = g.n.values.astype(float); nd = g.n_D.values.astype(float)
        a_full = float(np.sum(g.alpha_ann * n) / n.sum()); d_full = float(np.sum(g.D_ann * nd) / nd.sum())
        pb = reg[(reg.arm == 'C0') & (reg.form == form) & (reg.universe == uni)]
        full.append(dict(form=form, arm=arm, universe=uni, alpha_FULL_ann=a_full, D_FULL_ann=d_full, alpha_share_of_D=(a_full / d_full if abs(d_full) > 1e-12 else np.nan),
                         beta_nweighted=float(np.sum(g.beta * n) / n.sum()), r2_mean=float(g.r2.mean()),
                         parent_beta_nweighted=float(np.sum(pb.parent_beta * pb.n) / pb.n.sum())))
    s3full = pd.DataFrame(full)
    w('size_neutral_alpha.csv', r3)
    w('size_neutral_alpha_full.csv', s3full)
    # ---- S4
    s4cols = key + [c for c in lay.columns if c.startswith(('s4_', 'dev_'))]
    w('leader_vocab_deviation.csv', lay[s4cols])
    # ---- S2
    lk = lay.set_index(key)
    rows, counts, adds = [], [], []
    polm = pol[pol.arm.isin(MAIN)].copy()
    for cal, lab in CALIBERS:
        df = pol.copy()
        st_ = []
        for _, r in df.iterrows():
            if r.arm not in MAIN:
                st_.append(r.size_status); continue
            if cal.startswith('edit_'):
                st_.append('PASS' if cal == 'edit_none' else status_from([r['size_gap_pctpt_%s' % s] for s in SEGS], int(cal.split('_')[1])))
            elif cal.startswith('port_'):
                st_.append(status_from([lk.loc[(s, r.form, r.arm, r.alpha), 'tw_diff_mean'] for s in SEGS], int(cal.split('_')[1])))
            elif cal == 'leader_daily':
                st_.append(status_from([lk.loc[(s, r.form, r.arm, r.alpha), 's4_src_max_over_days'] for s in SEGS], 3))
            elif cal == 'leader_mean':
                st_.append(status_from([lk.loc[(s, r.form, r.arm, r.alpha), 's4_src_mean_daily_max'] for s in SEGS], 3))
            elif cal == 'leader_vs_parent':
                ok = all(lk.loc[(s, r.form, r.arm, r.alpha), 's4_src_mean_daily_max'] <= max(3.0, lk.loc[(s, r.form, 'C0', 0.0), 's4_src_mean_daily_max']) + 1e-12
                         for s in SEGS)
                st_.append('PASS' if ok else 'FAIL')
            else:
                st_.append('PASS')
        df['size_status'] = st_
        for prof in ('FULL', 'G4'):
            df['policy_' + prof] = [PP.verdict(r, prof) for _, r in df.iterrows()]
        m = df[df.arm.isin(MAIN)]
        for _, r in m.iterrows():
            rows.append(dict(caliber=cal, form=r.form, arm=r.arm, alpha=r.alpha, H=r.H, main_config=bool(r.main_config), size_status=r.size_status,
                             policy_FULL=r.policy_FULL, policy_G4=r.policy_G4))
        mc = m[m.main_config]
        counts.append(dict(caliber=cal, definition=lab, main24_pass_FULL=int((mc.policy_FULL == '通过').sum()), main24_pass_G4=int((mc.policy_G4 == '通过').sum()),
                           grid288_pass_FULL=int((m.policy_FULL == '通过').sum()), grid288_pass_G4=int((m.policy_G4 == '通过').sum()),
                           main24_size_fail=int((mc.size_status == 'FAIL').sum()), grid288_size_fail=int((m.size_status == 'FAIL').sum())))
        for a in additions(df):
            adds.append(dict(caliber=cal, **a))
    rs = pd.DataFrame(rows)
    # 对照：登记口径（edit_5）须逐行复现 pilot_policy
    chk = rs[rs.caliber == 'edit_5'].merge(polm[['form', 'arm', 'alpha', 'H', 'policy_FULL', 'policy_G4']], on=['form', 'arm', 'alpha', 'H'], suffixes=('', '_reg'))
    n_bad = int(((chk.policy_FULL != chk.policy_FULL_reg) | (chk.policy_G4 != chk.policy_G4_reg)).sum())
    self_ = pd.concat([self_, pd.DataFrame([dict(segment='ALL', check='S2 登记口径（edit_5）逐行复现 pilot_policy 的 policy_FULL / G4：不符行数（288）',
                                                 value=float(n_bad), status='PASS' if n_bad == 0 else 'FAIL')])], ignore_index=True)
    w('selftest.csv', self_)
    w('policy_rescore_calibers.csv', rs); cnt = pd.DataFrame(counts); w('policy_rescore_counts.csv', cnt); ad = pd.DataFrame(adds); w('policy_rescore_additions.csv', ad)
    # ---- S5
    pm = pol[pol.main_config & pol.arm.isin(MAIN)].set_index(['form', 'arm'])
    mar = []
    for (form, arm), r in pm.iterrows():
        d = dict(form=form, arm=arm, FULL=r.FULL, G4=r.G4, **{'D_%s' % s: r['D_%s' % s] for s in SEGS}, years_pos=r.years_pos, MDE80_FULL=r.FULL_MDE80)
        for L in (20, 60):
            b = boot[(boot.form == form) & (boot.arm == arm) & (boot.L == L) & (boot.centered)]
            d['boot_centered_q975_L%d' % L] = float(b.q975.iloc[0]) if len(b) else np.nan
        for s in SEGS:
            x = lk.loc[(s, form, arm, 0.25)]
            d['turn_rel_%s' % s] = r['turn_rel_%s' % s]; d['pos_diff_%s' % s] = r['pos_diff_%s' % s]
            d['edit_gap_signed_%s' % s] = x.edit_gap_mean; d['port_tw_diff_%s' % s] = x.tw_diff_mean; d['port_hold_diff_%s' % s] = x.hold_diff_mean
        for uni in ('clean_full', 'pool0'):
            f3 = s3full[(s3full.form == form) & (s3full.arm == arm) & (s3full.universe == uni)].iloc[0]
            d['S3_alpha_FULL_%s' % uni] = f3.alpha_FULL_ann; d['S3_beta_%s' % uni] = f3.beta_nweighted
        d['S4_mean_daily_max_worst_seg'] = max(lk.loc[(s, form, arm, 0.25), 's4_src_mean_daily_max'] for s in SEGS)
        d['historical_exposed'] = bool(r.historical_exposed); d['registered_policy_FULL'] = r.policy_FULL; d['registered_policy_G4'] = r.policy_G4
        for cal, _ in CALIBERS:
            q = rs[(rs.caliber == cal) & (rs.form == form) & (rs.arm == arm) & rs.main_config].iloc[0]
            d['S2_%s_FULL' % cal] = q.policy_FULL
        mar.append(d)
    mt = pd.DataFrame(mar); w('marginality_table.csv', mt)
    # ---- 报告
    R = Report('supplement_1')

    def head(**kw):
        h = dict(主体='—', 算子='—', 分母='四段有效日', 基准='同形态 C0 生产母体', 子集='24 主对象（六形态 × S / M / SM / C1，α .25）', 单位='百分位点',
                 日期='2010-01-04..2026-03-27（四段）', H='5', 成本模型='8bp 线性（只用于 S3 的 d_t）', 支持='native FALLBACK（已封存 P 账户）', 资本视图='NATIVE',
                 exposure='事后口径（已见本轮读数）')
        h.update(kw); return h
    R.h(1, 'E6j REPORT supplement_1 —— 事后口径：市值四层暴露、政策重评分口径网格、size 中性增量、领导词表偏离、边际性一览')
    R.h(2, '0. 性质与口径')
    R.p('**本文件全部为事后口径**（已见本轮登记读数之后计算），**不替代登记结果**：`results_P/pilot_policy.csv`、part3 与登记的政策结论不变；本文件只给数，不给建议。'
        '依据：`E6j_VERIFY_brief.md` §6；用户 2026-09-27 原话"合理的限制我可以理解"与"在大致满足领导要求的基础上 标准尽量宽松 不要太严格"（`E6j_delivery_addendum_1.md` §0）。')
    R.p('计算口径：账户与收益只读已封存 P 账户（`accounts/P/<段>/<形态>.npz` 与 `masks_<形态>.npz`），不重跑收益、随机与 bootstrap；目标权重用本轮生产路径 DEV（`env.SE.dev`，与 `assign_weights_dev` 逐位同：'
        '个股 min(1/n, 1%)，行业权重超过"当日 clean 域行业数量份额 + 3%"时按比例压缩、不归一）。size 百分位 = 当日 clean 域流通市值升序秩（[0,1]，大市值 = 高；与 `e6j_run_p.size_pct_cells` 逐位同，见自测）。')
    R.p('S1 四层：(a) pool0 层（子母同域，只给分布）；(b) 编辑层 gap_t = median(换入 pct) − median(换出 pct)（逐日按 `size_gap` 同式重算，与 summary.csv 对账）；'
        '(c) 最终名单等权 pct 均值；(d) 实际权重层 Σw·pct / Σw：形成日目标权重，另给 H5 滚动持仓 act_t = Σ_{k<min(t+1,5)} W_{t−k} / min(t+1,5)（pct 用当日值）。'
        '子 − 母逐日差的逐段 mean_t / sd_t，单位百分位点；小盘 / 大盘 = clean 域 pct ≤ .3 / > .7 的目标权重份额之差（百分点）。**主读数 = (d) 目标权重层 |mean_t(子 − 母)|**。')
    R.p('**符号事实（供决策端核对）**：`accounts/P/<段>/summary.csv` 的 `size_gap_mean` 带符号（换入 − 换出）；A4b / A4b_CVRv5 四臂与 M_union3_v2 两形态的 S / SM / C1 在四段全部为负 = 换入者市值更小。'
        '`pilot_policy.csv` 的 `size_gap_pctpt_*` 是其**绝对值** × 100，读符号须回到 summary.csv 或本文件 `edit_gap_mean` 列。')
    R.p('S3：d_t = 子 − 母 H5 8bp 日配对增量（P 账本）；SMB_t = 前一日流通市值五分组等权最小组 − 最大组的当日 vwap 日收益（`vwap_daily_return` 同口径），'
        'universe = 前一日 clean 域（全市场）或前一日 pool0；OLS + Bartlett(L = 5) HAC；α 年化 = 252 × 100 × 日截距；FULL 合并 α 按各段回归样本数加权；α / D = 非 size 部分份额（D 与 α 同段口径）。'
        'S4：size 五分组当"行业"，share_b = 当日 clean 域数量份额；dev_b = Σ_{i∈b} w_i − share_b（源 DEV 口径：未归一、只有超配受 +3% 约束）与归一版 Σw_b / Σw − share_b。')
    R.p('S2 口径网格：%s。其余五条（c / d / e-资本 / e-随机 / f）与正向门槛、三句加法、MC 状态全部沿用 `pilot_policy.csv` 的已存列与 `e6j_policy_p.verdict`，只替换 `size_status`；'
        '组合层与领导词表门对网格对象用同 (形态, 臂, α) 的目标权重（与 H 无关）。' % '；'.join('%s = %s' % c for c in CALIBERS))
    R.p('过程披露：`seg/<段>/*.csv` 首次运行后为把 S4 扩到全部掩码行（S2 领导词表门需要）重跑一次并覆盖（同为本目录新产物，首次版本未被读用于任何表）；回执写 `receipts/`，不写 `task_status/`；'
        'query_id 登记写 `query_registry_supplement_1.json`，不进 `reports/query_registry.json`。')
    R.h(2, '1. S1 市值四层暴露')
    cols1 = key + ['tw_diff_mean', 'tw_diff_sd', 'hold_diff_mean', 'hold_diff_sd', 'names_diff_mean', 'small_diff_mean', 'large_diff_mean', 'edit_gap_mean',
                   'edit_gap_absmean', 'tw_child_mean', 'tw_parent_mean', 'tw_days']
    R.table(mainlay[mainlay.arm != 'C0'][cols1], head(主体='24 主对象 × 四段', 算子='子 − 母逐日差的段内 mean / sd；edit_gap 为换入 − 换出中位差（带符号）'), 'S1-Q01')
    R.table(pool, head(主体='pool0 层', 算子='逐日 pool0 单元 pct 的均值 / 分位，再对日取均值', 基准='—', 子集='四段'), 'S1-Q02')
    gsum = lay[lay.arm.isin(MAIN)].assign(abs_tw=lambda x: x.tw_diff_mean.abs()).groupby(['form', 'arm', 'alpha']).abs_tw.max().unstack('alpha').reset_index()
    R.table(gsum, head(主体='六形态 × 四臂 × 三 α', 算子='目标权重层 |mean_t(子 − 母)| 的四段最大值', 子集='网格（与 H 无关）'), 'S1-Q03')
    R.h(2, '2. S2 政策重评分（事后口径网格）')
    R.table(cnt, head(主体='24 主对象与 288 网格对象', 算子='只替换市值通道；其余条件沿用登记列', 单位='个'), 'S1-Q04')
    wide = rs[rs.main_config].pivot_table(index=['form', 'arm'], columns='caliber', values='policy_FULL', aggfunc='first').reset_index()
    R.table(wide[['form', 'arm'] + [c for c, _ in CALIBERS]], head(主体='24 主对象', 算子='FULL profile 结论（各口径）', 单位='结论'), 'S1-Q05')
    R.table(ad, head(主体='每形态 × profile', 算子='三句加法 chosen（各口径）', 单位='臂名'), 'S1-Q06')
    R.h(2, '3. S3 size 中性化后的增量')
    R.table(s3full, head(主体='24 主对象', 算子='d_t 对 SMB_t 回归，FULL 按样本数合并', 单位='年化百分点 / 系数', 基准='SMB（两种 universe）'), 'S1-Q07')
    R.table(r3[r3.universe == 'clean_full'][['segment', 'form', 'arm', 'D_ann', 'alpha_ann', 'alpha_se_ann', 'beta', 'beta_se', 'r2', 'n', 'parent_beta']],
            head(主体='24 主对象 × 四段', 算子='逐段 OLS + HAC(L = 5)', 单位='年化百分点 / 系数', 基准='SMB clean 全市场'), 'S1-Q08')
    R.table(stt[stt.universe != 'SELFTEST'][['segment', 'universe', 'days'] + ['members_q%d' % i for i in range(1, 6)] + ['smb_mean_ann']],
            head(主体='SMB 构造', 算子='前一日流通市值五分组；日均成员数', 单位='只 / 年化百分点', 基准='—', 子集='四段 × 两 universe'), 'S1-Q09')
    R.h(2, '4. S4 领导词表下的 size 偏离')
    s4m = lay[(lay.main_config) | (lay.arm == 'C0')][key + ['s4_src_max_over_days', 's4_src_mean_daily_max', 's4_src_n_daybucket_gt3', 's4_norm_mean_daily_max',
                                                           's4_norm_absmax_over_days', 's4_src_mean_by_bucket']]
    R.table(s4m, head(主体='24 主对象与 6 个 C0 母体 × 四段', 算子='size 五分组当行业：dev_b = Σw_b − share_b（源口径）/ 归一版', 单位='百分点 / 计数'), 'S1-Q10')
    dv = lay.groupby('segment').agg(stock_max_w=('dev_stock_max_w', 'max'), industry_excess_max=('dev_ind_excess_max', 'max')).reset_index()
    R.table(dv, head(主体='全部掩码行（六形态 × 22 行）', 算子='逐日：max 个股权重；max(行业 Σw − (share + 3%))（≤ 0 即满足）', 单位='权重', 子集='全部'), 'S1-Q11')
    R.h(2, '5. S5 边际性一览（不写建议）')
    R.table(mt, head(主体='24 主对象', 算子='登记列 + S1–S4 汇总 + S2 各口径 FULL 结论', 单位='年化百分点 / 百分位点 / 结论'), 'S1-Q12')
    R.h(2, '6. 自测')
    R.table(self_, head(主体='自测', 算子='逐项', 单位='最大差 / 不符数', 基准='—', 子集='—'), 'S1-Q13')
    hits, leaks = R.scan()
    if hits or leaks:
        raise RuntimeError('supplement 扫描 FAIL：%s %s' % (hits, leaks))
    rp = os.path.join(SUP, 'E6j_REPORT_supplement_1.md'); J.atomic_write_text(rp, R.text()); outs.append(rp)
    qp = os.path.join(SUP, 'query_registry_supplement_1.json')
    J.atomic_write_json(qp, {q: dict(file='E6j_REPORT_supplement_1.md', **v) for q, v in R.qids.items()}); outs.append(qp)
    receipt('supp1_merge', outs, wall_s=round(time.time() - t0, 1), code_sha256={f: J.sha_file(os.path.join(J.CODE, f)) for f in ('e6j_supp1_seg.py', 'e6j_supp1_merge.py')})
    print('supplement', hashlib.sha256(R.text().encode()).hexdigest()[:12], len(R.qids), 'selftest', self_.status.value_counts().to_dict())
    return 0


if __name__ == '__main__':
    sys.exit(main())
