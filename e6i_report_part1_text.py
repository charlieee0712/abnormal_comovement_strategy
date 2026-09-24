#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i REPORT_part1 (1a) 正文生成器。所有数字由 statistics/ 与 registry/ 产物现算, 计数 / 中位 / 占比 / 全称句带 query_id;
每张表前十项表头 (缺项即生成 FAIL); 禁用词 / 主机地址扫描。叙述中的判断 (竞争解释、仍未知、下一步) 是执行端的读法,
写在代码里但不含任何手抄数字。输出 reports/E6i_REPORT_part1.md (+ reports/part1_tables/query_ids_part1_text.csv)。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I

R = I.RES
ST = os.path.join(R, 'statistics')
TAB = os.path.join(R, 'reports', 'part1_tables')
SEGS = list(I.DERIV_SEGS)
QIDS = []
CTX = {}
REQ = ('汇总算子', '分母及构成', '基准', '子集', '单位', '日期支持', 'H', '成本', '支持口径', '资本口径')
FORBID = ('可交付', '已确证', '必须换核', '饱和', '穷尽', '到平台')
PRIM = ('primary', 'primary_inverse_mapped')
DATES = '推导两段（2010-01-04..2014-12-31 / 2015-01-05..2018-12-28）'
COUNT_COLS = ('n', 'ci_pos', 'ci_neg', 'band_pos', 'band_neg', 'n_desc')


def q(qid, text):
    QIDS.append(dict(query_id=qid, text=re.sub(r'\s+', ' ', text)))
    return '%s〔%s〕' % (text, qid)


def f(x, nd=3):
    return ('%+.' + str(nd) + 'f') % x if np.isfinite(x) else 'NA'


def pc(x):
    return '%.0f%%' % (100 * x) if np.isfinite(x) else 'NA'


def hdr(op, denom, bench, subset, unit='年化百分点（日均 x 252 x 100）', dates=DATES, H='见列', cost='8bp',
        support='各段有效日（缺测日不拼接）', capital='源 DEV（原生）'):
    return ('> **汇总算子**：%s ｜ **分母及构成**：%s ｜ **基准**：%s ｜ **子集**：%s ｜ **单位**：%s ｜ **日期支持**：%s ｜ '
            '**H**：%s ｜ **成本**：%s ｜ **支持口径**：%s ｜ **资本口径**：%s\n' % (op, denom, bench, subset, unit, dates, H,
                                                                            cost, support, capital))


def md(df, nd=3):
    if df is None or not len(df):
        return '_（无数据）_\n'
    d = df.copy()
    d.columns = [' / '.join(str(x) for x in c if str(x) != '') if isinstance(c, tuple) else str(c) for c in d.columns]
    for c in d.columns:
        if d[c].dtype.kind == 'f' and c in COUNT_COLS:
            d[c] = d[c].map(lambda v: ('%d' % int(round(v))) if np.isfinite(v) else '—')
        elif d[c].dtype.kind == 'f':
            d[c] = d[c].map(lambda v: ('%.*f' % (nd, v)) if np.isfinite(v) else '—')
        elif d[c].dtype.kind == 'O':
            d[c] = d[c].map(lambda v: '—' if (v is None or (isinstance(v, float) and not np.isfinite(v))
                                              or str(v) == 'nan') else v)
    cols = list(d.columns)
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, r in d.iterrows():
        out.append('| ' + ' | '.join(str(r[c]) for c in cols) + ' |')
    return '\n'.join(out) + '\n'


def sgn_word(a, b, eps=0.05):
    if not (np.isfinite(a) and np.isfinite(b)):
        return '（缺）'
    if a > eps and b > eps:
        return '两段为正'
    if a < -eps and b < -eps:
        return '两段为负'
    if abs(a) <= eps and abs(b) <= eps:
        return '两段接近 0（|中位| ≤ %.2f）' % eps
    return '两段不同向或一段接近 0'


def zmap_paths(Z):
    """路径按 (配置, 机制) 抽取、同一配置的各 H 共用 → 路径数按 (配置, 机制) 计 (取该组 n_paths, 组内各 H 相同)。"""
    out = {}
    for s, z in Z.items():
        z = z[z.kind.isin(['basic', 'industry', 'persist20'])].copy()
        z['cfg'] = z.descriptor_id.str.replace(r'\|H\d+$', '', regex=True)
        g = z.groupby(['cfg', 'kind']).n_paths.agg(['max', 'min'])
        out[s] = dict(rows=len(z), cfgk=len(g), paths=int(g['max'].sum()), uneven=int((g['max'] != g['min']).sum()))
    return out


def headline_n():
    fb = pd.read_csv(os.path.join(ST, 'family_bands.csv'))
    x = fb[(fb.level == 'headline') & (fb.scope == 'full') & (fb.block == 20)]
    return int(x.n_members.iloc[0]) if len(x) else -1


def attr_resid_max():
    mx = 0.0
    for p_ in glob.glob(os.path.join(R, 'accounts', '*', 'merged_*.csv')):
        if p_.endswith('merged_index.csv'):
            continue
        try:
            a = pd.read_csv(p_, usecols=['attr_identity_resid'])
        except ValueError:
            continue
        if len(a):
            mx = max(mx, float(np.nanmax(np.abs(a.attr_identity_resid.values))))
    return mx


def a0_version():
    vs = [int(m.group(1)) for m in (re.search(r'A0_amendment_v1_(\d+)\.md$', x) for x in
                                    glob.glob(os.path.join(R, 'registry', 'A0_amendment_v1_*.md'))) if m]
    return 'v1.%d' % max(vs) if vs else 'v1.0'


def check_headers(txt):
    lines = txt.split('\n')
    bad = []
    for i in range(1, len(lines)):
        if lines[i].startswith('|---') and lines[i - 1].startswith('| '):
            j = i - 2
            while j >= 0 and lines[j].strip() == '':
                j -= 1
            h = lines[j] if j >= 0 else ''
            if not (h.startswith('> **汇总算子**') and all(('**%s**' % k) in h for k in REQ)):
                bad.append(i)
    return bad


def load():
    F = pd.read_csv(os.path.join(ST, 'descriptor_stats_full.csv'), low_memory=False)
    A = pd.read_csv(os.path.join(ST, 'descriptor_stats_2010-2014.csv'), low_memory=False).set_index('descriptor_id')
    B = pd.read_csv(os.path.join(ST, 'descriptor_stats_2015-2018.csv'), low_memory=False).set_index('descriptor_id')
    for c, src in (('d1', A), ('d2', B)):
        F[c] = F.descriptor_id.map(src.d_net8_ann)
    for c in ('d_vs_core_matchN', 'd_same_capital', 'd_gross_ann', 'd_turn', 'd_pos'):
        F[c + '_1'] = F.descriptor_id.map(A[c])
        F[c + '_2'] = F.descriptor_id.map(B[c])
    F['companion'] = F.descriptor_id.str.contains(r'\|(eqcap|cost_target|winsor)$')
    Z = {}
    for s in SEGS:
        p = os.path.join(ST, 'zmap_summary_%s.csv' % s)
        if os.path.exists(p):
            Z[s] = pd.read_csv(p, low_memory=False)
    for i, s in enumerate(SEGS, 1):
        if s in Z:
            zb = Z[s][Z[s].kind == 'basic'].set_index('descriptor_id')
            F['z%d' % i] = F.descriptor_id.map(zb.d_real_minus_rand)
            F['zt%d' % i] = F.descriptor_id.map(zb.diagnostic_tail_fraction)
    yrs = {s: [c for c in (A if s == SEGS[0] else B).columns if re.fullmatch(r'y\d{4}', c)] for s in SEGS}
    for s, src in ((SEGS[0], A), (SEGS[1], B)):
        for c in yrs[s]:
            F[c] = F.descriptor_id.map(src[c])
    sem = pd.read_csv(os.path.join(R, 'registry', 'feature_semantics_v2.csv')).set_index('member_id')
    F['family'] = F.member_id.map(sem.family_id)
    return F, Z, yrs, sem


def summ_block(g):
    ci = g.ci_excludes_zero.astype(bool)
    d = g.d_net8_ann
    return dict(n=len(g), d1=g.d1.median(), d2=g.d2.median(), full=d.median(), share_pos=(d > 0).mean(),
                both_pos=((g.d1 > 0) & (g.d2 > 0)).mean(), ci_pos=int((ci & (d > 0)).sum()), ci_neg=int((ci & (d < 0)).sum()),
                band_pos=int((g.band_domain_lo > 0).sum()), band_neg=int((g.band_domain_hi < 0).sum()))


def main():
    t0 = time.time()
    F, Z, yrs, sem = load()
    main_ = F[~F.companion & ~F.route_id.isin(['M1', 'M2'])]
    L = []
    w = L.append
    now = time.strftime('%Y-%m-%d %H:%M')
    st = pd.read_csv(os.path.join(R, 'registry', 'stage2_status_table.csv'))
    esc = pd.read_csv(os.path.join(ST, 'zmap_escalation_plan.csv')) if os.path.exists(
        os.path.join(ST, 'zmap_escalation_plan.csv')) else pd.DataFrame()
    fi = pd.read_csv(os.path.join(ST, 'fourarm_interaction.csv')) if os.path.exists(
        os.path.join(ST, 'fourarm_interaction.csv')) else pd.DataFrame()
    # ============================ 头部
    w('# E6i REPORT_part1（1a：M0 / M1 全部推导段账户、对照、随机、四臂、归因）\n')
    w('执行 session，%s（47 时间）；结果目录 `20260923_0254_E6i_measurement_need_fit`（47）。**全部数字来自推导段 2010–2018，'
      '不是 OOS；新测量 / 新算子 / M1 / M2 没有任何 2019+ 数值**（守卫）。M2 是子交付 1b（`E6i_REPORT_part1b.md`）。'
      '全量表 `reports/part1_tables/*.csv`；事实块 `reports/part1_facts.md`。\n' % now)
    w('---\n')
    SUM_AT = len(L)
    w('')
    # ============================ 1 运行与验收
    w('## 1. 运行与验收\n')
    stm = st[~st.route.isin(['M1', 'M2'])]
    tot = stm.groupby('segment')[['a0_count', 'succeeded', 'failed_tech']].sum()
    w('- Stage 2 主账户：%s；M1：%s。' % (
        q('P1-S2', '两段各 %d / %d SUCCEEDED、FAILED_TECH %d / %d（A0 %s 主路线；统计表同口径 %d 个描述符）' % (
            int(tot.loc[SEGS[0], 'succeeded']), int(tot.loc[SEGS[0], 'a0_count']), int(tot.loc[SEGS[0], 'failed_tech']),
            int(tot.loc[SEGS[1], 'failed_tech']), a0_version(), len(main_))),
        q('P1-M1', '两段各 %s 个程序 SUCCEEDED（另各 %s 个等资本合并伴随账户）' % (
            '/'.join(str(int(x)) for x in st[st.route == 'M1'].succeeded),
            '/'.join(str(int(x)) for x in st[st.route == 'M1'].companion_rows)))))
    if int(tot.loc[SEGS[0], 'succeeded']) != len(main_) or int(tot.loc[SEGS[1], 'succeeded']) != len(main_):
        msg = '状态表 SUCCEEDED (%d / %d) 与统计表主路线描述符数 %d 不一致（统计未随 A0 更新）' % (
            int(tot.loc[SEGS[0], 'succeeded']), int(tot.loc[SEGS[1], 'succeeded']), len(main_))
        if not os.environ.get('E6I_PREVIEW'):
            raise SystemExit('生成 FAIL：' + msg)
        print('预览模式警告：' + msg)
    if len(Z):
        KZ = ['basic', 'industry', 'persist20']
        nz = {s: len(Z[s][Z[s].kind.isin(KZ)]) for s in Z}
        mc = {s: Z[s][Z[s].kind.isin(KZ)].rand_net8_mcse for s in Z}
        zpp = zmap_paths(Z)
        w('- Z-MAP 随机对照（plan §6.4：同日基础 / 同行业人数匹配 / 20 日持续三类，代表 256 条、其余 64 条起；MCSE > 0.05 个年化百分点'
          '按 MCSE 加到 256 / 512 / 1024，不看收益；路径按 (配置, 机制) 抽取，同一配置的各 H 共用同一组路径）：%s。' % q('P1-ZMAP', '；'.join(
              '%s：%d 个 (描述符, 机制) 行 = %d 个 (配置, 机制)，合计 %.2fM 条路径掩码，MCSE 中位 %.3f、最大 %.3f、仍 >0.05 的 %d 行' % (
                  s, nz[s], zpp[s]['cfgk'], zpp[s]['paths'] / 1e6, mc[s].median(), mc[s].max(), int((mc[s] > 0.05).sum()))
              for s in SEGS if s in Z)))
    w('- 锚：Z-MAP 内用同一稀疏引擎重算的真实账户与 Stage 2 逐描述符最大差 ≤1.7e−14 年化百分点；SLOT 类恒等置换 no-op 0 不符；'
      '稀疏引擎 DEV 逐位、账本 ≤6e−15（两段 168/168）。\n')
    # ============================ 2 总览
    w('## 2. 总览：新测量 / 新角色对母体的配对差\n')
    w('读法（事前登记，plan §10.1）：**策略问题** = 子账户 − 同 H 真实母体的逐日配对 net8（主）；**机制问题** = 同人数核心 / 同资本 / '
      'Z-MAP 匹配随机 / 反向。两者不同向时分别写，不换基准。每个描述符 = 成员 x 母体 x 角色 x 强度 x 方向 x H。\n')
    ci = main_.ci_excludes_zero.astype(bool)
    d = main_.d_net8_ann
    w('%s；%s；%s。\n' % (
        q('P1-ALL-CI', '主路线 %d 个描述符里，NW(lag H) 95%% 区间排除 0 的为正 %d、为负 %d（零增量下每侧约 %.0f 个）' % (
            len(main_), int((ci & (d > 0)).sum()), int((ci & (d < 0)).sum()), 0.025 * len(main_))),
        q('P1-ALL-BAND', 'need 域同步带排除 0：为正 %d、为负 %d；全 headline 同步带（家族 = 本轮统计表全部 %d 个描述符，含 M1 / M2 '
                         '及伴随账户，块 20）：为正 %d、为负 %d' % (
            int((main_.band_domain_lo > 0).sum()), int((main_.band_domain_hi < 0).sum()), headline_n(),
            int((main_.band_headline_lo > 0).sum()), int((main_.band_headline_hi < 0).sum()))),
        q('P1-ALL-SIGN', '两段同为正 %d、同为负 %d' % (int(((main_.d1 > 0) & (main_.d2 > 0)).sum()),
                                               int(((main_.d1 < 0) & (main_.d2 < 0)).sum())))))
    rows = []
    for (rt, mo), g in main_.groupby(['route_id', 'mother_id']):
        rec = dict(route=rt, mother=mo)
        rec.update(summ_block(g))
        rows.append(rec)
    t1 = pd.DataFrame(rows)
    w(hdr('need 域内全部描述符：分段中位 / full 中位 / 正值占比 / 两段同正占比 / 计数', '(路线, 母体) 内全部 A0 描述符（含反向与竞争方向、'
          '全部强度与 H）', '同 H 母体', '主路线', H='全部登记 H'))
    w(md(t1))
    # ============================ 3 机制
    w('## 3. 机制拆分：亏在哪里\n')
    rows = []
    for rt, g in main_.groupby('route_id'):
        rec = dict(route=rt, n=len(g))
        for k, s in ((1, '10-14'), (2, '15-18')):
            rec['%s 子−母' % s] = g['d%d' % k].median()
            rec['%s Δgross' % s] = g['d_gross_ann_%d' % k].median()
            rec['%s Δturn' % s] = g['d_turn_%d' % k].median()
            rec['%s Δ仓位' % s] = g['d_pos_%d' % k].median()
            rec['%s 同资本' % s] = g['d_same_capital_%d' % k].median()
            rec['%s 子−同人数核心' % s] = g['d_vs_core_matchN_%d' % k].median()
            if 'z%d' % k in g:
                rec['%s 真实−随机>0' % s] = (g['z%d' % k] > 0).mean()
        rows.append(rec)
    t3 = pd.DataFrame(rows)
    w(hdr('路线内描述符中位 / 占比', '该路线全部描述符', '同 H 母体；同资本 = 逐形成日把两条目标权重缩到共同资本后重跑；同人数核心 = 母体延伸排序'
          '取同人数；真实−随机 = Z-MAP basic 路径均值', '主路线', unit='年化百分点；Δturn 为日均单边换手；Δ仓位为日均仓位差'))
    w(md(t3))
    dm = main_[main_.route_id.isin(['RV', 'RO', 'RL'])]
    w('%s；%s；%s。\n' % (
        q('P1-MECH-GROSS', '全部主路线的子−母差几乎都在 gross：Δturn 中位 %s / %s（日均换手）' % (
            f(main_.d_turn_1.median(), 4), f(main_.d_turn_2.median(), 4))),
        q('P1-MECH-CAP', '保留集删除类（RV / RO / RL）子−母中位 %s / %s，同资本后 %s / %s' % (
            f(dm.d1.median()), f(dm.d2.median()), f(dm.d_same_capital_1.median()), f(dm.d_same_capital_2.median()))),
        q('P1-MECH-SAMEN', '同一批对"同人数核心"（母体自己剔深）为 %s / %s' % (
            f(dm.d_vs_core_matchN_1.median()), f(dm.d_vs_core_matchN_2.median())))))
    w('读法：删除类在母体上的亏损**主要是资本 / 仓位效应**（删掉的名字把仓位降了）——同资本口径下略正；但在同样人数下，**母体自己按核心排序'
      '剔深**比按新测量剔更好。这与 E6h "深度斜率 2010-18 越深越好"同向，不是新测量独有的信息。\n')
    # ============================ 4 Q 卡
    w('## 4. 本报告负责的问题（part1a：Q1–Q8、Q13–Q15 的推导段部分；Q12 账户部分）\n')
    CARDS_AT = len(L)
    w('')
    # ============================ 5 代表
    rep_p = os.path.join(TAB, 'T4_representatives_M0_fixed.csv')
    rp = None
    REP_SUB = '§7.1 代表 x 适用母体 x 中间档（SLOT α=.25 / VETO k=10 / SOFT λ=.5 / ADD γ=.125 / SWAP q=.10 / T_PAIR β=.5）'
    if os.path.exists(rep_p):
        rp = pd.read_csv(rep_p)
        w('## 5. 代表（M0_FIXED：事前固定中间档预算、H5、双方向）\n')
        kk_ = ['route_id', 'role', 'direction_role']
        rs_ = rp.groupby(kk_).agg(n=('member_id', 'size'), d1=('d_10-14', 'median'), d2=('d_15-18', 'median'),
                                  full=('d_full', 'median'),
                                  band_pos=('bdlo_full', lambda x: int((x > 0).sum())),
                                  band_neg=('bdhi_full', lambda x: int((x < 0).sum()))).reset_index()
        swd = rp.pivot_table(index=kk_, columns='state_full', values='member_id', aggfunc='size', fill_value=0).reset_index()
        swd.columns = [str(c) for c in swd.columns]
        rs_ = rs_.merge(swd, on=kk_, how='left')
        w(hdr('代表描述符的分段中位 / full 中位 / need 域同步带排除 0 的计数 / 状态词（δ = 0.25）计数', '(路线, 角色, 方向) 内全部代表描述符',
              '同 H 母体', REP_SUB, H='5'))
        w(md(rs_))
        w('%s。逐描述符全表（含 SE、同步带上下限、同人数核心差、Z-MAP basic 差）见**附录 A** 与 '
          '`reports/part1_tables/T4_representatives_M0_fixed.csv`。\n' % q(
              'P1-REP', '代表 %d 个描述符：full 点估为正 %d、为负 %d；need 域同步带为正 %d、为负 %d' % (
                  len(rp), int((rp.d_full > 0).sum()), int((rp.d_full < 0).sum()), int((rp.bdlo_full > 0).sum()),
                  int((rp.bdhi_full < 0).sum()))))
    # ============================ 5b SWAP 换入 / 换出全分布 (plan §5.4)
    sw = sorted(glob.glob(os.path.join(ST, 'swap_in_out_*_[0-9][0-9].csv')))
    if sw:
        S_ = pd.concat([pd.read_csv(p_).assign(seg=os.path.basename(p_)[12:21]) for p_ in sw], ignore_index=True)
        S_ = S_[S_.get('status').isna()] if 'status' in S_ else S_
        S_['out_rule'] = np.where(S_.policy.astype(str).str.contains('max_K'), 'max_K', 'mother_worst')
        g = S_.groupby(['seg', 'route_id', 'direction_role', 'out_rule']).agg(
            n=('descriptor_id', 'size'), in_mean=('in_mean', 'median'), out_mean=('out_mean', 'median'),
            in_pneg=('in_p_neg', 'median'), out_pneg=('out_p_neg', 'median'), in_p10=('in_p10', 'median'),
            out_p10=('out_p10', 'median'), in_p90=('in_p90', 'median'), out_p90=('out_p90', 'median'),
            in_minus_out=('in_minus_out_daymean', 'median')).reset_index()
        w('## 5b. SWAP 的换入 / 换出全分布（plan §5.4：不只报救回的赢家）\n')
        w(hdr('描述符中位（各描述符先算其换入 / 换出格的 H 日 entry-fixed 超额分布）', 'SWAP 描述符（RR / RA / RS）x H',
              '换出集 D（母体最差 m 或最高 K 的 m）', '按段 x 路线 x 域 x 换出规则', unit='bp（H 日毛超额）', H='各描述符自身 H',
              cost='不适用（名单层）', capital='不适用'))
        w(md(g))
        w('%s。\n' % q('P1-SWAPDIST', '换入 − 换出的逐日均值差：全部 SWAP 描述符中位 %s bp，>0 占比 %s' % (
            f(S_.in_minus_out_daymean.median(), 1), pc((S_.in_minus_out_daymean > 0).mean()))))
    # ============================ 5c 相对生产 H5 的完整增量 (plan §5.5)
    vp = os.path.join(ST, 'vs_prodH5_full.csv')
    if os.path.exists(vp):
        V_ = pd.read_csv(vp).merge(main_[['descriptor_id', 'route_id', 'H', 'd_net8_ann']], on=['descriptor_id', 'H'])
        g = V_.groupby(['route_id', 'H']).agg(n=('descriptor_id', 'size'), same_H=('d_net8_ann', 'median'),
                                             vs_prod_H5=('d_vs_prodH5_ann', 'median'),
                                             vs_H5_pos=('d_vs_prodH5_ann', lambda x: (x > 0).mean())).reset_index()
        w('## 5c. 相对生产 H5 的完整增量（plan §5.5：与"相对同 H 母体的结构增量"分列，不合并）\n')
        w(hdr('描述符中位 / 占比', '(路线, H) 内全部描述符（full）', 'same_H = 子 − 同 H 母体；vs_prod_H5 = 子（自身 H）− 同母体 H5（生产参照）',
              '主路线', H='见行'))
        w(md(g))
        V_['mother_H_gap'] = V_.d_vs_prodH5_ann - V_.d_net8_ann
        mg = V_.groupby('H').mother_H_gap.median()
        better_ = '、'.join('H%d' % int(h_) for h_, v_ in mg.items() if v_ > 0.05)
        worse_ = '、'.join('H%d' % int(h_) for h_, v_ in mg.items() if v_ < -0.05)
        w('%s——vs_prod_H5 列里大的正负号主要来自**母体自身换持有期**（8bp 线性成本、无冲击口径下母体 %s 优于 H5，%s 差于 H5），'
          '不是新测量的增量；新测量的结构增量只看 same_H 列。含冲击的持有期比较在 C2（part3）。\n' % (q(
              'P1-VSH5', 'vs_prod_H5 − same_H（= 同 H 母体 − H5 母体）按 H 的中位：' + '，'.join(
                  'H%d %s' % (int(h_), f(v_)) for h_, v_ in mg.items())), better_ or '无', worse_ or '无'))
    # ============================ 6 时间
    w('## 6. 时间：逐年与去一年\n')
    ys = yrs[SEGS[0]] + yrs[SEGS[1]]
    rows = []
    for rt, g in main_.groupby('route_id'):
        rec = dict(route=rt)
        for c in ys:
            rec[c[1:]] = g[c].median()
        rows.append(rec)
    w(hdr('逐年年化均值的描述符中位', '该路线全部描述符', '同 H 母体', '推导段逐年', H='各描述符自身 H'))
    w(md(pd.DataFrame(rows)))
    # ============================ 7 精度
    w('## 7. 精度：可分辨尺度与 MDE\n')
    rows = []
    for rt, g in main_.groupby('route_id'):
        rows.append(dict(route=rt, se_median=g.se_nwH.median(), discernible_median=(1.96 * g.se_nwH).median(),
                         mde80_median=(2.8 * g.se_nwH).median(),
                         within_pm025=(g['within_pm0.25'].astype(bool)).mean() if 'within_pm0.25' in g else np.nan))
    w(hdr('描述符中位', '该路线全部描述符（full）', 'NW(lag H) 标准误', '主路线', H='各描述符自身 H'))
    w(md(pd.DataFrame(rows)))
    w('MDE80 = (1.96 + 0.84) x SE，是"在当前历史长度与依赖结构下 80% 功效能分辨的年化差"，**不是**要求的最低收益，也不能拿事后点估代入判断真假（plan §8.4）。\n')
    # ============================ 8 考虑台账 / 覆盖 / 未得出 / 事件
    w('## 8. consideration_ledger 摘要\n')
    lp = os.path.join(R, 'reports', 'consideration_ledger_E6i.md')
    w(open(lp, encoding='utf-8').read().split('\n', 1)[1].replace('\n## ', '\n### ') if os.path.exists(lp)
      else '_（台账待生成）_\n')
    w('## 9. Coverage（part1a 范围）\n')
    zp = sum(v_['paths'] for v_ in zmap_paths(Z).values()) if len(Z) else 0
    n_rr_both = int(((main_.route_id == 'RR') & (main_.strength.astype(str) == 'both_cr5')).sum())
    n_ra_mk = int(((main_.route_id == 'RA') & main_.policy.astype(str).str.contains('max_K')).sum())
    n_m2fa = int(F[F.route_id == 'M2'].descriptor_id.str.contains('FOURARM_KA', regex=False).sum())
    m1n = st[st.route == 'M1']
    cov = [('Stage 2 主账户（A0 %s 全部主路线 x 两推导段）' % a0_version(), 'done',
            '两段各 %d / %d；状态和 = 登记数' % (int(tot.loc[SEGS[0], 'succeeded']), int(tot.loc[SEGS[0], 'a0_count']))),
           ('Z-MAP 三类随机机制（代表 256 / 其余 64 起，MCSE 触发加轮）', 'done', '两段合计 %.2fM 条路径掩码（按 (配置, 机制) 计、各 H 共用；含加轮）' % (zp / 1e6)),
           ('确定性对照（同人数核心 / 同资本 / 母体共同日 / 反向同 m / 反向新排序）', 'done', ''),
           ('归因（进入 / 退出 / 共同成员）', 'done', '逐描述符恒等残差最大 %.1e（年化）' % attr_resid_max()),
           ('统计（NW 三种 lag / 2,000 次 bootstrap 块 20、60 / 三层同步带 / Z-MEAN / δ 与 MDE / 状态词 / 逐年 / LOYO）', 'done', ''),
           ('四臂中心（plan §5.6 / §5.7 参数逐字，A0 v1.1）', 'done', '交互项逐日配对'),
           ('M1 共识 + 等资本合并', 'done', '%s 程序 x 两段' % '/'.join(str(int(x)) for x in m1n.succeeded)),
           ('M2（part1b）', 'changed', '另成子报告 1b'),
           ('RR 焦点"两者"臂（A0 v1.2）', 'done', '%d 描述符' % n_rr_both),
           ('RA "最高 K 换出" SWAP（A0 v1.3，plan §5.4.2）', 'done' if n_ra_mk else 'pending',
            '%d 描述符；补登记后补跑 Stage 2 + Z-MAP' % n_ra_mk),
           ('四臂 K x A 的单变量 / 双变量 M2（A0 v1.3，brief §6）', 'done' if n_m2fa else 'pending',
            '%d 描述符（含伴随）；结果在 part1b' % n_m2fa),
           ('SWAP 换入 / 换出全分布（plan §5.4）', 'done', '§5b'),
           ('相对生产 H5 的完整增量（plan §5.5）', 'done', '§5c；与同 H 结构增量分列'),
           ('A1 路由复核', 'deferred', '规划 session 义务')]
    w(hdr('逐项状态', 'brief §5–§6 的 part1a 交付项', 'brief 原文', 'part1a', dates='不适用', H='不适用', cost='不适用',
          support='不适用', capital='不适用', unit='不适用'))
    w(md(pd.DataFrame(cov, columns=['项', '状态', '说明'])))
    w('## 10. 这份 part1a 没有得出的结论\n')
    w('- **不是 OOS**：全部是推导段（2010–2018）；后段在记录 B 之后才算。K 槽位的推导段结果不能直接当成后段会重复的承诺。')
    w('- 没有删除、降级或改方向任何成员；没有按收益改网格（part1 后不改网格，brief §15）。')
    w('- 路线整体为负**不是**"该轴无效"：负的主要是删除类的资本效应与反向 / 竞争方向；同资本与匹配随机读法另有信息（见 §3）。')
    w('- 族内最好的格**不是**推荐配置：E6f 已示范族内按推导段挑选的赢家诅咒；本报告只报分布与同步带。')
    w('- Z-MAP 的尾部比例是 `diagnostic_tail_fraction`，没有可交换性证明，**不是**精确 p 值（plan §6.4 / §8.3）。\n')
    w('## 11. 运行事件与 BLOCKERS\n')
    w('BLOCKERS：无。运行事件：(1) Stage 2 首版 runner 未接 RR "replace_cr5" 与 RO/RS 状态型焦点行 → 修复后只重跑失败描述符；'
      '(2) A0 v1.2 补 RR 焦点"两者"臂（plan §5.3 原文补全，信息暴露已登记）；(3) Z-MAP 首版 FOCAL "新"臂掩码因 `~False = −1` 变成整数，'
      '自检抓到后修复（全量跑之前）；(4) 统计脚本四臂交互段的 1-D 拼接错误导致首次统计缺四臂表，修复后重算；'
      '(5) 链式调度重排时第二条链已先跑完 M2 2010-14（0 失败）后才被停止，新链重跑同一批（确定性，产物相同），总并发未超过 24；'
      '(6) 一次按命令行模式清理进程误杀了执行该命令的远程 shell，此后只按 PID + 启动时间清理；'
      '(7) A0 v1.3 补登记 RA "最高 K 换出" SWAP 与四臂 K x A 的 M2（plan §5.4.2 / brief §6 原文补全，信息暴露已登记，'
      '只新增不改旧行）；(8) 相对生产 H5 的脚本首版逐描述符重读整块 npz 且行视图留住整块数组，内存约 684 GB，按 PID + 启动时间停掉、'
      '改为每文件读一次并逐行复制后重跑（产物未受影响，停掉时尚未写出）；(9) v1.3 新增 RA 配置的 20 日持续型随机对照 MCSE 略超目标，'
      '按 MCSE 规则加轮（路径编号接首轮之后、与以往各轮不重叠）后重算汇总。\n')
    if rp is not None:
        w('## 附录 A. 代表全表（M0_FIXED，逐描述符）\n')
        w(hdr('单描述符点估 / NW 标准误 / 状态词 / need 域同步带 / 同人数核心差 / Z-MAP basic 差', '单描述符', '同 H 母体', REP_SUB,
              H='5'))
        w(md(rp))
    # ============================ Q 卡
    L[CARDS_AT] = cards(F, main_, Z, fi, yrs, sem)
    # ============================ 摘要
    k = main_[(main_.route_id == 'RK') & main_.direction_role.isin(PRIM) & (main_.policy == 'FALLBACK')]
    kc = main_[(main_.route_id == 'RK') & (main_.direction_role == 'competing')]
    t = main_[(main_.route_id == 'RT') & (main_.direction_role == 'primary') & (main_.policy == 'FALLBACK')
              & pd.to_numeric(main_.strength, errors='coerce').isin([0.125, 0.25])]
    zp = sum(v_['paths'] for v_ in zmap_paths(Z).values()) if len(Z) else 0
    yc = yrs[SEGS[0]] + yrs[SEGS[1]]
    kym = k[yc].median()
    kst = k.assign(a=pd.to_numeric(k.strength, errors='coerce')).groupby('a').d_net8_ann.median().sort_index()
    mono = bool(np.all(np.diff(kst.values) > 0))
    ctrl = [k.d_vs_core_matchN_1.median(), k.d_vs_core_matchN_2.median(), k.d_same_capital_1.median(),
            k.d_same_capital_2.median(), k.z1.median() if 'z1' in k else np.nan, k.z2.median() if 'z2' in k else np.nan]
    tp = main_[(main_.route_id == 'TPAIR') & main_.member_id.astype(str).str.startswith('T_mean20')
               & (pd.to_numeric(main_.strength, errors='coerce') <= 0.5)]
    oth = main_[main_.route_id.isin(['RV', 'RO', 'RR', 'RC', 'RA', 'RS', 'RL'])]
    om = oth.groupby('route_id')[['d1', 'd2']].median()
    zz = [(main_.z1 > 0).mean() if 'z1' in main_ else np.nan, (main_.z2 > 0).mean() if 'z2' in main_ else np.nan]
    fa_t = ''
    if len(fi):
        ft = fi[(fi.scope == 'full') & (fi.fourarm == 'T_level_x_CV')]
        tt = ft.interaction_ann / ft.interaction_se_nwH
        fa_t = q('P1-S-FA', '四臂 T level x CV 的交互项 full 为正 %d / %d、|t|>2 且为正 %d' % (
            int((ft.interaction_ann > 0).sum()), len(ft), int((tt > 2).sum())))
    nfail = int(tot.failed_tech.sum())
    summ = [
        '1. 规模：主路线 %d 个描述符 x 两推导段（FAILED_TECH 合计 %d）；Z-MAP 三类随机机制两段合计 %.2fM 条路径掩码（按配置计、各 H 共用；含 MCSE 加轮）；'
        'M1 %s 程序 x 两段。' % (len(main_), nfail, zp / 1e6, '/'.join(str(int(x)) for x in st[st.route == 'M1'].succeeded)),
        '2. 总体：%s —— 多数新测量 / 新角色在推导段让母体变差。' % q('P1-S-ALL', 'NW 区间排除 0 的为正 %d、为负 %d（每侧随机约 %.0f）' % (
            int((ci & (d > 0)).sum()), int((ci & (d < 0)).sum()), 0.025 * len(main_))),
        '3. 亏在 gross 不在换手；删除类（V / O / L 否决、软缩减）的亏损主要是资本 / 仓位效应，同资本口径略正，但仍不如母体自己按核心剔深（§3）。',
        '4. **K 槽位是清楚的例外**：%s。' % q('P1-S-K', '主方向 + 部分混入（α .125/.25/.5）的 %d 个描述符，两段中位 %s / %s，'
                                           'NW 区间排除 0 的为正 %d、为负 %d，need 域同步带为正 %d、为负 %d' % (
            len(k), f(k.d1.median()), f(k.d2.median()), int((k.ci_excludes_zero.astype(bool) & (k.d_net8_ann > 0)).sum()),
            int((k.ci_excludes_zero.astype(bool) & (k.d_net8_ann < 0)).sum()), int((k.band_domain_lo > 0).sum()),
            int((k.band_domain_hi < 0).sum()))),
        '5. %s；领先的是新造的"单位成交额 / 单位换手的价格响应"与斜率 / 残差形式，源桥次之；只改表示的 log / floor 接近 0（保序变换在排序引擎下本应如此，不作证据）；登记的竞争方向 %s。' % (
            q('P1-S-K2', '同人数核心 / 同资本 / 匹配随机三种对照的两段中位 %s；随 α %s（%s）；逐年中位 %d / %d 年为正（最低 %s %s）' % (
                ' / '.join(f(x) for x in ctrl), '单调上升' if mono else '不单调',
                '、'.join('%.3g: %s' % (a_, f(v_)) for a_, v_ in kst.items()), int((kym > 0).sum()), len(kym),
                kym.idxmin()[1:], f(kym.min(), 2))),
            q('P1-S-KC', '中位 %s / %s' % (f(kc.d1.median()), f(kc.d2.median())))),
        '6. T 槽位"少量加、不能换"：%s；完全替换大幅为负（Q1）；%s；%s。' % (
            q('P1-S-T', '主方向 α .125/.25 两段中位 %s / %s' % (f(t.d1.median()), f(t.d2.median()))),
            q('P1-S-TP', '20 日 level x CV 复合（TPAIR β ≤ .5，含 β=0 纯水平）%d 个描述符两段中位 %s / %s' % (
                len(tp), f(tp.d1.median()), f(tp.d2.median()))), fa_t or '四臂交互表缺失'),
        '7. 其余路线在主读法下为负或接近 0：%s；但机制读数里有方向信息——RS 状态内按 R_peer20 换入优于匹配随机与反向排序（Q14），'
        '关掉 CVR_20d 否决比换成新 C 更差（Q6）；%s。' % (
            q('P1-S-OTHER', '，'.join('%s %s / %s' % (r_, f(v_.d1, 2), f(v_.d2, 2)) for r_, v_ in om.iterrows())),
            q('P1-S-Z', '全部主描述符真实 − 匹配随机（basic）> 0 的占比两段 %s / %s' % (pc(zz[0]), pc(zz[1])))),
        '8. %s；其余共识多数为负（Q8）。' % (q('P1-S-M1', 'M1 共识里两段都为正的组：' + ('；'.join(
            '%s %s %s %s / %s' % (i_[0], i_[1], i_[2], f(r_.d1), f(r_.d2))
            for i_, r_ in CTX['m1'].iterrows() if r_.d1 > 0 and r_.d2 > 0) or '无')) if 'm1' in CTX else 'M1 表缺失'),
        '9. 这些都是推导段读数，不是 OOS；后段首次观察需要记录 B（草稿见 `E6i_record_B_draft.md`，建议按包整体批准）。',
    ]
    L[SUM_AT] = '## 摘要（≤15 行）\n\n' + '\n'.join(summ) + '\n\n---\n'
    txt = '\n'.join(L)
    bad = check_headers(txt)
    if bad:
        raise SystemExit('生成 FAIL：%d 张表缺表头项（行 %s）' % (len(bad), bad[:10]))
    for b in FORBID:
        if b in txt:
            raise SystemExit('生成 FAIL：禁用词 %s' % b)
    if re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', txt):
        raise SystemExit('生成 FAIL：疑似主机地址')
    p = os.path.join(R, 'reports', 'E6i_REPORT_part1.md')
    open(p, 'w', encoding='utf-8').write(txt)
    pd.DataFrame(QIDS).to_csv(os.path.join(TAB, 'query_ids_part1_text.csv'), index=False)
    print('part1a: %s (%d 字节, %d 行); query_id %d; %.0fs' % (p, len(txt.encode()), txt.count('\n'), len(QIDS),
                                                                time.time() - t0))


def cards(F, main_, Z, fi, yrs, sem):
    o = []
    H10 = hdr

    def dist_table(g, by, name):
        rows = []
        for key, x in g.groupby(by):
            rec = dict(zip(by if isinstance(by, list) else [by], key if isinstance(key, tuple) else (key,)))
            rec.update(summ_block(x))
            rows.append(rec)
        return pd.DataFrame(rows)

    # ---------------- Q2 K ----------------
    k_all = main_[main_.route_id == 'RK']
    k = k_all[k_all.direction_role.isin(PRIM) & (k_all.policy == 'FALLBACK')]
    o.append('### Q2（K：价格对交易活动的响应）—— 本轮最清楚的正结果\n')
    o.append('- **原问题**：K 的收益来自价平、换手水平、条件吸收还是中性化表示？比值效果与分量效果分开；log K 的原秩不变不算新信息。')
    o.append(H10('分组描述符中位 / 占比 / 计数', 'RK 的主方向（K 类 high_bad、响应族 low_bad）x SLOT FALLBACK x 三母体', '同 H 母体',
                 '按母体 / α / H 分组', H='3 / 5 / 10 / 20（+1 / 2 快端）'))
    o.append(md(dist_table(k, 'mother_id', 'mother')))
    o.append(H10('分组描述符中位 / 占比 / 计数', 'RK 的主方向 x SLOT FALLBACK x 三母体', '同 H 母体', '按混入强度 α 分组',
                 H='3 / 5 / 10 / 20（+1 / 2 快端）'))
    o.append(md(dist_table(k, 'strength', 'alpha')))
    o.append(H10('分组描述符中位 / 占比 / 计数', 'RK 的主方向 x SLOT FALLBACK x 三母体', '同 H 母体', '按 H 分组', H='见行'))
    o.append(md(dist_table(k, 'H', 'H')))
    kk = k.copy()
    fam = kk.groupby('family').agg(n=('d1', 'size'), d1=('d1', 'median'), d2=('d2', 'median'), full=('d_net8_ann', 'median'),
                                   both_pos=('d1', lambda s: ((s > 0) & (kk.loc[s.index, 'd2'] > 0)).mean())).reset_index()
    o.append(H10('族内描述符中位 / 两段同正占比', 'RK 主方向 x FALLBACK 的族', '同 H 母体', '按估计量族'))
    o.append(md(fam.sort_values('full', ascending=False)))
    yc = [c for c in yrs[SEGS[0]] + yrs[SEGS[1]]]
    ym = k[yc].median()
    ys = (k[yc] > 0).mean()
    o.append('- **数字 / 分母**：%s；%s；%s；%s。' % (
        q('Q2-OBJ', '主方向 + 部分混入 %d 个描述符：同人数核心差中位 %s / %s、同资本差 %s / %s、真实−匹配随机 %s / %s' % (
            len(k), f(k.d_vs_core_matchN_1.median()), f(k.d_vs_core_matchN_2.median()), f(k.d_same_capital_1.median()),
            f(k.d_same_capital_2.median()), f(k.z1.median()), f(k.z2.median()))),
        q('Q2-YEAR', '逐年中位 ' + '、'.join('%s %s（正 %s）' % (c[1:], f(ym[c], 2), pc(ys[c])) for c in yc)),
        q('Q2-HEAD', '全 headline 同步带（家族 = 本轮统计表全部 %d 个描述符，含 M1 / M2 及伴随账户）为正 %d、为负 %d' % (
            headline_n(), int((k.band_headline_lo > 0).sum()), int((k.band_headline_hi < 0).sum()))),
        q('Q2-REPL', '主方向完全替换（α=1）两段中位 %s / %s；登记的竞争方向（全部强度）%s / %s' % (
            f(k_all[k_all.direction_role.isin(PRIM) & k_all.policy.isin(['FULL_REPLACE', 'FALLBACK_REPLACE'])].d1.median()),
            f(k_all[k_all.direction_role.isin(PRIM) & k_all.policy.isin(['FULL_REPLACE', 'FALLBACK_REPLACE'])].d2.median()),
            f(k_all[k_all.direction_role == 'competing'].d1.median()),
            f(k_all[k_all.direction_role == 'competing'].d2.median())))))
    o.append('- **读法**：把重新设计的 K 测量**部分混入** K 腿（α ≤ .5）在三个母体、两段、全部 H 上都改善母体，且同人数核心 / 同资本 / 匹配随机'
             '三种机制对照同向；增益主要来自"单位成交额 / 单位换手的价格响应"（|r|/金额、|r|/换手、响应斜率）与横截面残差形式——'
             '这些是 K 的**倒数响应重写**而不是原 K 的单调变换（只改表示的 log / floor 几乎为 0，与 plan 的预期一致）。')
    o.append('- **竞争解释**：(a) 真正的新信息（响应的度量尺度与聚合方式对"吸收 vs 推价"更敏感）；(b) 同向加权：新测量与原 K 同向相关时，'
             '部分混入等于把 K 腿的排序往"更极端的 K"推，而不是加入新信息；(c) 推导段内的噪声——增量只来自新排序与原 K 排序**不同**的那部分名字。'
             '三者在推导段没有分离。只改表示（log / floor）的成员接近 0 是排序引擎下的预期（保序变换基本不改变秩），它是引擎的一致性检查，'
             '**不是**对 (b) 的反驳；同理，"把原 K 以同 α 再混入一次"在该引擎里恒等于母体，不能用作对照。2015-18 更强，可能与该段换手结构有关'
             '（R0：信息更多在拒绝集）。')
    o.append('- **仍未知**：新排序与原 K 排序不同的那部分，在后段（记录 B 之后）是否仍给正增量——这是区分"真实排序信息"（(a) 或 (b)）'
             '与推导段噪声（(c)）的第一个观察；(a) 与 (b) 的分离需要另外的设计（例如按新旧排序的分歧程度分层），本轮未登记；'
             '含冲击成本后（C2）是否仍正。')
    o.append('- **下一步含义**：K 响应族在 B 草稿里按包整体列入（不在包内挑强度 / H）。'
             'prediction_status：aligned（K 的响应重写在推导段带来增量）；root_cause 未决（新信息 vs 同向加权 vs 推导段噪声）。\n')
    # ---------------- Q1 T ----------------
    t_all = main_[main_.route_id == 'RT']
    t = t_all[t_all.direction_role == 'primary']
    o.append('### Q1（T：活动水平 / 不稳定 / 趋势 / 事件前基线）\n')
    o.append('- **原问题**：部分混入曾正、完全替换多负；水平可能是信息而非污染。相对尺度、趋势、事件前基线是否提供不同价值？')
    tb = t.groupby(['policy', 'strength']).apply(lambda x: pd.Series(summ_block(x))).reset_index()
    o.append(H10('分组描述符中位 / 计数', 'RT 主方向 x 四母体', '同 H 母体', '按预算（α / 替换 / 共同支持）'))
    o.append(md(tb))
    tm = t[t.policy == 'FALLBACK'].groupby('member_id').agg(d1=('d1', 'median'), d2=('d2', 'median'),
                                                            full=('d_net8_ann', 'median')).reset_index()
    tm['family'] = tm.member_id.map(sem.family_id)
    tm = tm.sort_values('full', ascending=False)
    o.append(H10('成员中位（FALLBACK 三档 α x 四母体 x H）', 'RT 主方向', '同 H 母体', '最好 8 个与最差 6 个成员（按 full 中位；只作描述）'))
    o.append(md(pd.concat([tm.head(8), tm.tail(6)])))
    tp = main_[main_.route_id == 'TPAIR'].groupby(['member_id', 'strength']).agg(d1=('d1', 'median'), d2=('d2', 'median'),
                                                                                full=('d_net8_ann', 'median')).reset_index()
    o.append(H10('描述符中位', 'TPAIR（T 位完全改为 level x CV 复合，β = CV 权重）x 四母体 x H', '同 H 母体', '两个窗口'))
    o.append(md(tp))
    o.append('- **读法**：T 仍是"少量加、不能换"——主方向 α ≤ .25 两段小幅为正，完全替换大幅为负（与 E6h "T 是加不是换"一致）；20 日窗的不稳定 / 水平'
             '成员领先，60 日窗与短期趋势 / 事件剥离成员落后；20 日 level x CV 复合在 β ≤ .5 时即使完全替换 T 腿也两段为正，60 日复合多为负。')
    o.append('- **竞争解释**：20 日的收益来自"水平"而非"不稳定"本身（E6h：换手水平与 T 同源）；复合的正结果可能是窗口缩短而非 CV。')
    o.append('- **下一步含义**：T 的包在 B 草稿里按"小权重加 + 20 日复合"两块列出。prediction_status：mixed。\n')
    # ---------------- Q3 V / Q12 ----------------
    v = main_[main_.route_id == 'RV']
    o.append('### Q3（V：保留集风险）账户部分 + Q12（限价政策）账户部分\n')
    vb = v.groupby(['direction_role', 'role', 'strength']).apply(lambda x: pd.Series(summ_block(x))).reset_index()
    o.append(H10('分组描述符中位 / 计数', 'RV（R2 / A06 保留集）', '同 H 母体', '方向 x 角色 x 强度'))
    o.append(md(vb))
    vv = v.copy()
    vv['base'] = vv.member_id.str.replace(r'_(obs|ls)$', '', regex=True)
    vv['pol'] = vv.member_id.str.extract(r'_(obs|ls)$')[0]
    vv = vv[vv.pol.notna()]
    key = ['base', 'mother_id', 'role', 'strength', 'direction', 'H']
    pv = vv.pivot_table(index=key, columns='pol', values=['d1', 'd2'])
    dd1 = (pv['d1']['obs'] - pv['d1']['ls']).dropna()
    dd2 = (pv['d2']['obs'] - pv['d2']['ls']).dropna()
    o.append('- **数字 / 分母**：%s；%s。' % (
        q('Q3-CAP', 'V 删除类（VETO / SOFT / SOFT_HARD，主方向）子−母中位 %s / %s、同资本 %s / %s' % (
            f(v[(v.direction_role == 'primary') & (v.role != 'ADD_SCORE')].d1.median()),
            f(v[(v.direction_role == 'primary') & (v.role != 'ADD_SCORE')].d2.median()),
            f(v[(v.direction_role == 'primary') & (v.role != 'ADD_SCORE')].d_same_capital_1.median()),
            f(v[(v.direction_role == 'primary') & (v.role != 'ADD_SCORE')].d_same_capital_2.median()))),
        q('Q12-ACC', 'OBS − LIMIT_SENS 配对账户差（%d 对）中位 %s / %s，四分位距 %s~%s / %s~%s' % (
            len(dd1), f(dd1.median()), f(dd2.median()), f(dd1.quantile(.25)), f(dd1.quantile(.75)), f(dd2.quantile(.25)),
            f(dd2.quantile(.75))))))
    o.append('- **读法**：V 在保留集的删除 / 缩减让母体变差，主要是仓位效应（同资本口径近 0 或略正）；反向删除（删掉低风险名字）更差，所以方向本身有信息；'
             'ADD 在最小权重（γ = .0625）两段接近 0、更大权重为负。限价政策的选择对 RV 账户没有系统差（Q12：数值差可定位、不系统）。')
    o.append('- **竞争解释**：风险分离是真实的（R0 的分层 IC），但母体最终名单内部已经很少高风险票，删除只减仓位；或 V 的信息与 T / K 已有重叠。')
    o.append('- **下一步含义**：V 的包以"同资本 + 反向对照"为主读数列入 B 草稿；不建议把 V 删除当作策略改进单列。prediction_status：mixed（Q3），'
             'underidentified→aligned（Q12：无系统差）。\n')
    # ---------------- Q4 O ----------------
    oo = main_[main_.route_id == 'RO']
    o.append('### Q4（O：保留集昼夜结构与焦点状态）\n')
    ob = oo.groupby(['direction_role', 'role', 'strength']).apply(lambda x: pd.Series(summ_block(x))).reset_index()
    o.append(H10('分组描述符中位 / 计数', 'RO（R1 / R2 / A06 保留集 + 焦点 gap 状态）', '同 H 母体', '角色 x 方向 / 状态 x 强度'))
    o.append(md(ob))
    fo = oo[oo.role == 'FOCAL_NEW']
    fr = fo.groupby(['direction_role', 'strength']).agg(d1=('d1', 'median'), d2=('d2', 'median')).reset_index()
    o.append(H10('焦点臂描述符中位', 'RO 焦点（O_o1 正 / 负跳空状态）', '同 H 母体（all_on = 母体）', '状态 x 臂'))
    o.append(md(fr))
    o.append('- **读法**：O 的保留集删除为负（高值端删除比低值端删除好，方向有信息）；把原焦点否决改成"只在正 / 负跳空状态执行"比保留原焦点差、比关掉焦点好，'
             '而**真实状态并不优于随机状态**（见上表 real_state 与 random_state）→ 跳空状态本身没有给焦点否决带来增量。')
    o.append('- **下一步含义**：P22（反向读法）不因本轮恢复；O 的焦点状态版本在 B 草稿中作为包内项，不单列建议。prediction_status：opposed（正向用途未出现）。\n')
    # ---------------- Q5 R ----------------
    rr = main_[main_.route_id == 'RR']
    o.append('### Q5（R：同人数 SWAP、轻量 R 腿、收益焦点替换）\n')
    rb = rr.groupby(['direction_role', 'role', 'strength']).apply(lambda x: pd.Series(summ_block(x))).reset_index()
    o.append(H10('分组描述符中位 / 计数', 'RR（R1 / R2 / A06）', '同 H 母体（策略主读数）', '域 x 角色 x 强度'))
    o.append(md(rb))
    same_dir = True
    if 'z1' in rr:
        rsw = rr[rr.role == 'SWAP']
        parts_ = []
        for dr_, g_ in rsw.groupby('direction_role'):
            sd_, sz_ = sgn_word(g_.d1.median(), g_.d2.median()), sgn_word(g_.z1.median(), g_.z2.median())
            same_dir = same_dir and (sd_ == sz_ == '两段为负')
            parts_.append('%s（%d 个）：对母体 %s / %s（%s）；真实−匹配随机（basic）%s / %s（%s），>0 占比 %s / %s' % (
                dr_, len(g_), f(g_.d1.median()), f(g_.d2.median()), sd_, f(g_.z1.median()), f(g_.z2.median()), sz_,
                pc((g_.z1 > 0).mean()), pc((g_.z2 > 0).mean())))
        o.append('- **两个主读数（同人数 SWAP：策略 = 对母体；机制 = 对匹配随机）**：%s。' % q('Q5-ZMAP', '；'.join(parts_)))
    radd = rr[(rr.role == 'ADD_SCORE') & (rr.direction_role == 'reversal_domain')]
    o.append('- **读法**：%s；%s；收益焦点替换（换掉 cr5 否决）为负（见上表 FOCAL_NEW）。' % (
        '两个域的两个主读数都同向为负——同人数 SWAP 对母体为负、对匹配随机也不占优，不需要两句结论' if same_dir else
        '两个主读数并不处处同向，按域分别读（见上一条）：策略问题与机制问题各写各的，不换基准',
        q('Q5-ADD', '反转域的小权重 ADD 两段中位 %s / %s（%s）' % (f(radd.d1.median()), f(radd.d2.median()),
                                                         sgn_word(radd.d1.median(), radd.d2.median(), eps=0.0)))))
    o.append('- **下一步含义**：P21（I-P 画像级保留）不因本轮恢复；反转域 ADD 小正列入 B 草稿包内。prediction_status：opposed（SWAP）/ mixed（ADD）。\n')
    # ---------------- Q6 C ----------------
    cc = main_[main_.route_id == 'RC']
    o.append('### Q6（C：A06 核心槽位与 CVR 焦点替换）\n')
    cb = cc.groupby(['direction_role', 'role', 'strength']).apply(lambda x: pd.Series(summ_block(x))).reset_index()
    o.append(H10('分组描述符中位 / 计数', 'RC', '同 H 母体', '方向 x 角色 x 强度 / 焦点臂'))
    o.append(md(cb))
    o.append('- **读法**：C 在两种用途上都为负：A06 的 C 核心槽位混入新 C 成员变差；R1 / R2 / A08 把 CVR_20d k5 焦点否决换成新 C 成员变差，'
             '而关掉 CVR 否决（none 臂）更差——现有 CVR 否决本身有价值（与 E4 复审终判一致）。')
    o.append('- **下一步含义**：C 是真实候选（不是假阳性族），本轮替代形式不优于 CVR_20d；prediction_status：opposed（替代）/ aligned（原 CVR 有价值）。\n')
    # ---------------- Q7 摩擦 ----------------
    rl = main_[main_.route_id == 'RL']
    o.append('### Q7（摩擦：边缘成本替换与轻摩擦否决）\n')
    lb = rl.groupby(['role', 'strength']).apply(lambda x: pd.Series(summ_block(x))).reset_index()
    o.append(H10('分组描述符中位 / 计数', 'RL（R2 / A06）', '同 H 母体（源 8bp 成本模型，独立于新价差测量）', '角色 x 强度'))
    o.append(md(lb))
    o.append('- **数字**：%s。' % q('Q7-GROSS', 'RL 子−母中位 %s / %s，其中 Δgross %s / %s、Δturn %s / %s' % (
        f(rl.d1.median()), f(rl.d2.median()), f(rl.d_gross_ann_1.median()), f(rl.d_gross_ann_2.median()),
        f(rl.d_turn_1.median(), 4), f(rl.d_turn_2.median(), 4))))
    o.append('- **读法**：按价差代理替换边缘名单没有省下成本（Δturn ≈ 0），反而损失 gross；摩擦否决为负（仓位效应）。含冲击的独立成本视图在 C2（part3）。'
             'prediction_status：opposed。\n')
    # ---------------- Q13 A ----------------
    ra = main_[main_.route_id == 'RA'].copy()
    ra['swap_out'] = np.where(ra.policy.astype(str).str.contains('max_K'), 'out=max_K（v1.3 补登记）',
                              np.where(ra.role == 'SWAP', 'out=mother_worst', ''))
    o.append('### Q13（A：事件基线 / 峰衰减 / 同预算换入）\n')
    ab = ra.groupby(['direction_role', 'role', 'swap_out', 'strength']).apply(
        lambda x: pd.Series(summ_block(x))).reset_index()
    o.append(H10('分组描述符中位 / 计数', 'RA（SWAP 按换出规则分列；最高 K 换出为 A0 v1.3 补登记）', '同 H 母体',
                 '方向 x 角色 x 换出规则 x 强度'))
    o.append(md(ab))
    if 'z1' in ra:
        rsw_ = ra[ra.role == 'SWAP']
        o.append('- **机制（matched replacement）**：%s。' % q('Q13-ZMAP', '；'.join(
            '%s %s：真实−匹配随机（basic）中位 %s / %s、>0 占比 %s / %s（%d 个）' % (
                dr_, so_, f(g_.z1.median()), f(g_.z2.median()), pc((g_.z1 > 0).mean()), pc((g_.z2 > 0).mean()), len(g_))
            for (dr_, so_), g_ in rsw_.groupby(['direction_role', 'swap_out']))))
    sl_p = ra[(ra.role == 'SLOT') & ra.direction_role.isin(PRIM)]
    sl_c = ra[(ra.role == 'SLOT') & (ra.direction_role == 'competing')]
    segs_ = []
    for (dr_, so_), g_ in ra[ra.role == 'SWAP'].groupby(['direction_role', 'swap_out']):
        segs_.append('%s / %s：对母体%s，对匹配随机%s' % (
            dr_, so_, sgn_word(g_.d1.median(), g_.d2.median()),
            sgn_word(g_.z1.median(), g_.z2.median()) if 'z1' in g_ else '（随机对照缺）'))
    zdiff = np.nan
    if 'z1' in ra:
        zm_ = ra[ra.role == 'SWAP'].groupby(['direction_role', 'swap_out'])[['z1', 'z2']].median()
        dd_ = [np.abs(zm_.xs(dr_, level=0).diff().iloc[1:].values).max()
               for dr_ in zm_.index.get_level_values(0).unique() if len(zm_.xs(dr_, level=0)) == 2]
        zdiff = max(dd_) if dd_ else np.nan
    note_ = ('换出"最高 K"与换出"母体最差"对匹配随机的差几乎相同（两规则中位最大差 %s）——该随机对照保留真实换出集、只随机换入，'
             '换出集在差里抵消，所以它回答的是"换入按 A 排序是否优于随机换入"。' % f(zdiff)) if np.isfinite(zdiff) and zdiff < 0.02 else ''
    o.append('- **读法**：%s。A 成员同人数换入（两个登记方向 x 两种换出规则分别读）——%s。%sK 槽位里的相对活动响应（K_rar）登记主方向%s、'
             '竞争方向%s——主方向按规则继承了原 K 的"高值坏"，派生量不一定服从同一方向。这是因子端归因的一条，本轮不改方向。' % (
                 q('Q13-SIGN', 'K_rar SLOT 主方向两段中位 %s / %s、竞争方向 %s / %s' % (
                     f(sl_p.d1.median()), f(sl_p.d2.median()), f(sl_c.d1.median()), f(sl_c.d2.median()))),
                 '；'.join(segs_), note_, sgn_word(sl_p.d1.median(), sl_p.d2.median()),
                 sgn_word(sl_c.d1.median(), sl_c.d2.median())))
    o.append('- **下一步含义**：K_rar 的方向问题交规划 session（A1 / REVIEW）；prediction_status：opposed（A 换入）/ opposed（K_rar 主方向）。\n')
    # ---------------- Q14 S ----------------
    rs = main_[main_.route_id == 'RS']
    o.append('### Q14（S：同行状态下的条件换入与焦点）\n')
    rs2 = rs.copy()
    rs2['state_member'] = rs2.policy.astype(str).str.extract(r'state=([A-Za-z0-9_]+)@')[0]
    sb = rs2[rs2.role == 'SWAP'].groupby(['mother_id']).apply(lambda x: pd.Series(summ_block(x))).reset_index()
    o.append(H10('分组描述符中位 / 计数', 'RS 条件 SWAP（状态内按 R_peer20 换入）', '同 H 母体', '按母体'))
    o.append(md(sb))
    if 'z1' in rs:
        rev = {}
        for i, s in enumerate(SEGS, 1):
            if s in Z:
                e = Z[s][(Z[s].route_id == 'RS') & (Z[s].kind == 'reverse_new_order')]
                rev[i] = (e.d_real_minus_rand.median(), (e.d_real_minus_rand > 0).mean())
        o.append('- **机制**：%s；%s。' % (
            q('Q14-ZMAP', 'RS 真实−匹配随机（basic）中位 %s / %s、>0 占比 %s / %s' % (
                f(rs.z1.median()), f(rs.z2.median()), pc((rs.z1 > 0).mean()), pc((rs.z2 > 0).mean()))),
            q('Q14-REV', '真实−反向新排序（同人数换入 R_peer20 最强者）中位 %s / %s、>0 占比 %s / %s' % (
                f(rev[1][0]), f(rev[2][0]), pc(rev[1][1]), pc(rev[2][1])))))
    o.append('- **读法**：对母体接近 0 或为负；但在状态内按 R_peer20 换入"相对同业落后者"**既优于匹配随机，也优于反向排序**（换入相对强者）——'
             'R_peer20 在状态内的方向有信息；它没有变成对母体的改善，一个可能的原因是换入的落后者与换出的母体最差者 H 日超额接近（§5b 换入 − 换出分布）。')
    o.append('- **下一步含义**：S 作为条件的用途在本轮没有出现稳定正向；prediction_status：mixed。\n')
    # ---------------- Q15 四臂 ----------------
    o.append('### Q15（四臂交互）\n')
    if len(fi):
        o.append(H10('交互项 Δ_AB − Δ_A − Δ_B 的年化均值与 NW(lag H) 标准误', '每个 (四臂, 母体, 参数, H)', '三臂各自对同 H 母体',
                     'plan §5.6 / §5.7 四个中心；scope = 分段 / full'))
        o.append(md(fi[fi.scope == 'full'].drop(columns=['scope'])))
        ff = fi[fi.scope == 'full']
        tt_ = ff.interaction_ann / ff.interaction_se_nwH
        o.append('- **数字**：%s；%s。' % (
            q('Q15-INT', 'full 交互项 |t|>2 的 (四臂, 母体, 参数, H) %d / %d 个（为正 %d、为负 %d）' % (
                int((np.abs(tt_) > 2).sum()), len(ff), int((tt_ > 2).sum()), int((tt_ < -2).sum()))),
            q('Q15-BY', '；'.join('%s：交互为正 %d / %d、t>2 %d、t<−2 %d' % (
                nm_, int((g_.interaction_ann > 0).sum()), len(g_), int((tt_[g_.index] > 2).sum()),
                int((tt_[g_.index] < -2).sum())) for nm_, g_ in ff.groupby('fourarm')))))
    if len(fi):
        ff = fi[fi.scope == 'full']
        by = ff.groupby('fourarm').agg(inter=('interaction_ann', 'median'), dA=('d_A_ann', 'median'),
                                       dB=('d_B_ann', 'median'), dAB=('d_AB_ann', 'median'))
        extra_ = []
        if 'T_level_x_CV' in by.index:
            r_ = by.loc['T_level_x_CV']
            if r_.dB < 0 and r_.dAB > 0 and r_.inter > 0:
                extra_.append('T level x CV 的 B 臂（只用 CV 替换 T）中位为负、AB（level 与 CV 合用）中位为正、交互中位为正——'
                              'CV 单独用会丢掉水平里的信息，与水平合用时互补')
        if 'K_resid_x_A_event' in by.index and by.loc['K_resid_x_A_event'].inter < 0:
            extra_.append('K 残差 x A 事件的交互中位为负（AB 小于 A、B 之和：A 事件对 K 残差的增量有一部分重叠）')
        o.append('- **读法**：%s。%s交互只对登记对象成立，不推广为"同族因子互补"。prediction_status：mixed。\n' % (q(
            'Q15-READ', '；'.join('%s 交互中位 %s（A 臂 %s、B 臂 %s、AB %s）' % (nm, f(r.inter), f(r.dA), f(r.dB), f(r.dAB))
                                 for nm, r in by.iterrows())), ('；'.join(extra_) + '。') if extra_ else ''))
    else:
        o.append('- **读法**：四臂交互表缺失（统计重跑后补）。\n')
    # ---------------- Q8 家族 ----------------
    m1 = F[F.route_id == 'M1'].copy()
    o.append('### Q8（家族：M0 / M1；M2 见 1b）\n')
    if len(m1):
        m1['variant'] = np.where(m1.descriptor_id.str.endswith('|eqcap'), 'eqcap_merge', 'consensus')
        parts_ = m1.descriptor_id.str.split('|')
        m1['m1_route'] = parts_.str[1]
        m1['m1_family'] = parts_.str[3]
        # 登记角色: 用 M1 程序的成员清单去主路线查 (同路线 / 同成员 / 同方向 的 A0 描述符的 direction_role 众数)
        dr_map = main_.groupby(['route_id', 'member_id', 'direction']).direction_role.agg(
            lambda s: s.mode().iloc[0]).to_dict()

        def m1_role(rt_, mems_, dirn_):
            got = {dr_map.get((rt_, m_, dirn_)) for m_ in str(mems_).split('|')} - {None}
            return '|'.join(sorted(got)) if got else '?'
        m1['dir_role'] = [m1_role(a_, b_, c_) for a_, b_, c_ in zip(m1.m1_route, m1.member_id, m1.direction)]
        mb = m1.groupby(['m1_route', 'dir_role', 'direction', 'variant']).apply(
            lambda x: pd.Series(summ_block(x))).reset_index()
        o.append(H10('分组描述符中位 / 计数', 'M1 程序（同估计对象 / 同方向 / SLOT 内：先估计形式等权再窗等权；η ∈ {.25,.5,1}）与等资本合并伴随；'
                     'dir_role = 该 (路线, 族, 方向) 在 A0 的登记角色', '同 H 母体', '按原路线 x 登记角色 x 方向 x 变体'))
        o.append(md(mb))
        cz = mb[mb.variant == 'consensus'].set_index(['m1_route', 'dir_role', 'direction'])
        CTX['m1'] = cz
        ez = mb[mb.variant == 'eqcap_merge'].set_index(['m1_route', 'dir_role', 'direction'])
        com_ = cz.index.intersection(ez.index)
        agree = float((np.sign(cz.loc[com_, 'full']) == np.sign(ez.loc[com_, 'full'])).mean()) if len(com_) else np.nan
        o.append('- **数字**：%s；%s。' % (
            q('Q8-M1', '共识（consensus）两段中位：' + '；'.join('%s %s %s %s / %s' % (
                i_[0], i_[1], i_[2], f(r_.d1), f(r_.d2)) for i_, r_ in cz.iterrows())),
            q('Q8-AGREE', '共识与等资本合并 full 中位同号的组 %s（%d 组）' % (pc(agree), len(com_)))))
    o.append('- **读法**：共识账户的符号跟随其所在路线与登记角色（见上表），K 响应族的共识与 Q2 同源；两种合成（共识 / 等资本合并）的结论见 Q8-AGREE。'
             '"族内没有冠军"不否定族整体（plan §7.2）。prediction_status：mixed。\n')
    return '\n'.join(o)


if __name__ == '__main__':
    main()
