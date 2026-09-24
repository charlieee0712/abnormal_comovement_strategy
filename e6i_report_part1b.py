#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i REPORT_part1b (M2_SHAPE; plan §7.2 / §7.3; 规格 registry/M2_program_spec.md) 生成器。全部数字现算、带 query_id,
十项表头检查、禁用词 / 主机地址扫描。输出 reports/E6i_REPORT_part1b.md 与 reports/part1_tables/M2_*.csv。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import re
import sys
import glob
import time

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_report_part1_text as TX

R = I.RES
TAB = os.path.join(R, 'reports', 'part1_tables')
SEGS = list(I.DERIV_SEGS)
BUD = {'SLOT': ('0.25', 'FALLBACK'), 'ADD_SCORE': ('0.125', None), 'SWAP': ('0.1', 'out=mother_worst'),
       'VETO_NEW': ('10', None)}


def main():
    t0 = time.time()
    TX.QIDS.clear()
    q, f, pc, hdr, md = TX.q, TX.f, TX.pc, TX.hdr, TX.md
    F = pd.read_csv(os.path.join(R, 'statistics', 'descriptor_stats_full.csv'), low_memory=False)
    A = pd.read_csv(os.path.join(R, 'statistics', 'descriptor_stats_2010-2014.csv'), low_memory=False).set_index('descriptor_id')
    B = pd.read_csv(os.path.join(R, 'statistics', 'descriptor_stats_2015-2018.csv'), low_memory=False).set_index('descriptor_id')
    for c, src in (('d1', A), ('d2', B)):
        F[c] = F.descriptor_id.map(src.d_net8_ann)
    m2 = F[F.route_id == 'M2'].copy()
    is_fa = m2.descriptor_id.str.contains('FOURARM_KA', regex=False)
    m2['kind'] = np.where(is_fa & m2.descriptor_id.str.contains('|uni|', regex=False), 'fourarm_uni',
                          np.where(is_fa, 'fourarm_bi', 'rep'))
    # α 从描述符 id 解析 (M2 合并表的 strength 列写的是家族中间档, 不是四臂 M2 的登记 α; 账户本身用的是登记 α)
    m2['alpha'] = m2.descriptor_id.str.extract(r'\|a=([0-9.]+)\|')[0]
    m2['variant'] = np.where(m2.descriptor_id.str.endswith('|cost_target'), 'cost_target',
                             np.where(m2.descriptor_id.str.endswith('|winsor'), 'winsor', 'primary'))
    a0 = pd.read_csv(os.path.join(R, 'registry', 'descriptors_A0.csv'), low_memory=False)
    a2 = a0[a0.route_id == 'M2'].set_index('descriptor_id')
    base_id = m2.descriptor_id.str.replace(r'\|(cost_target|winsor)$', '', regex=True)
    for c in ('m2_home_route', 'm2_role', 'axis_id'):
        m2[c] = base_id.map(a2[c])
    # 对应 M0: 同路线 / 母体 / 成员 / 角色 / 中间档 / 主方向 / H
    st = F[~F.route_id.isin(['M1', 'M2'])]
    prim = st[st.direction_role.isin(['primary', 'primary_inverse_mapped', 'reversal_domain', 'high_role'])]
    idx = {}
    for r in prim.itertuples():
        idx.setdefault((r.route_id, r.mother_id, r.member_id, r.role, str(r.strength), str(r.policy), int(r.H)), r.d_net8_ann)
    fa_idx = {}
    for r in st[st.route_id == 'FOURARM'].itertuples():
        if str(r.policy) == 'K_resid_x_A_event':
            fa_idx[(r.mother_id, '%g' % float(re.search(r'\|a=([0-9.]+)\|', r.descriptor_id).group(1)),
                    str(r.direction_role), int(r.H))] = r.d_net8_ann
    m0 = []
    for r in m2.itertuples():
        if r.kind != 'rep':
            # 四臂 M2 的同预算 M0: uni (u = K_res_log) -> 四臂 A 臂 (K_res_log 线性, 同 α); bi -> AB 臂 (两者线性合用, 同 α)
            arm = 'A' if r.kind == 'fourarm_uni' else 'AB'
            m0.append(fa_idx.get((r.mother_id, '%g' % float(r.alpha), arm, int(r.H)), np.nan))
            continue
        b, pol = BUD.get(r.m2_role, (None, None))
        strength = str(float(b)) if b and b != '10' else ('10' if b == '10' else None)
        key_pol = pol if pol else 'nan'
        # S 轴程序: u = R_peer20 (RS 的排序量), 最近的固定对照 = RR 无条件 SWAP R_peer20 q=.10
        route, mem = (('RR', 'R_peer20') if r.axis_id == 'S' else (r.m2_home_route, r.member_id))
        v = idx.get((route, r.mother_id, mem, r.m2_role, strength, key_pol, int(r.H)))
        if v is None and b == '10':
            v = idx.get((route, r.mother_id, mem, r.m2_role, '10.0', key_pol, int(r.H)))
        m0.append(v if v is not None else np.nan)
    m2['m0_same_budget_full'] = m0
    m2['m2_minus_m0'] = m2.d_net8_ann - m2.m0_same_budget_full
    m2.to_csv(os.path.join(TAB, 'M2_panel.csv'), index=False)
    # ledger
    lps = [p for s in SEGS for p in glob.glob(os.path.join(R, 'm2', s, 'ledger_[0-9][0-9]*.csv')) if '_timing' not in p]
    led = pd.concat([pd.read_csv(p) for p in lps], ignore_index=True) if lps else pd.DataFrame()
    L = []
    w = L.append
    w('# E6i REPORT_part1b（M2_SHAPE：有界、训练内、低维形状校准分支）\n')
    w('执行 session，%s（47 时间）。规格：`registry/M2_program_spec.md`（任何拟合之前落盘；z = S_peerR20、预算 = 各角色已登记中间档）。'
      '**只有推导段，不是 OOS**；M2 学习不确定性（256 次时间块重采样）见 §5。\n' % time.strftime('%Y-%m-%d %H:%M'))
    w('---\n')
    SUM_AT = len(L)
    w('')
    pr = m2[m2.variant == 'primary']
    w('## 1. M2 对母体（策略主读数）\n')
    rows = []
    for (kd, ax, role), g in pr.groupby(['kind', 'axis_id', 'm2_role']):
        rec = dict(kind=kd, axis=ax, home_role=role)
        rec.update(TX.summ_block(g))
        rec['m2−m0 中位'] = g.m2_minus_m0.median()
        rows.append(rec)
    t1 = pd.DataFrame(rows)
    w(hdr('轴 x home 角色内全部 M2 程序：分段中位 / 计数；m2−m0 = M2 − 同成员同预算的 M0 固定账户（full）',
          '§7.1 代表 x 适用母体 x H（primary 变体 = net8 目标选 λ）', '同 H 母体', 'M2 primary'))
    w(md(t1))
    ci = pr.ci_excludes_zero.astype(bool)
    w('%s；%s。\n' % (
        q('P1B-ALL', 'M2 primary %d 个程序：两段中位 %s / %s，NW 区间排除 0 为正 %d、为负 %d' % (
            len(pr), f(pr.d1.median()), f(pr.d2.median()), int((ci & (pr.d_net8_ann > 0)).sum()),
            int((ci & (pr.d_net8_ann < 0)).sum()))),
        q('P1B-M0', 'M2 − 同预算 M0 的 full 中位 %s、>0 占比 %s（%d 个可配对）' % (
            f(pr.m2_minus_m0.median()), pc((pr.m2_minus_m0 > 0).mean()), int(pr.m2_minus_m0.notna().sum())))))
    w('## 2. 变体：成本目标与 winsor 敏感性\n')
    vb = m2.groupby('variant').apply(lambda g: pd.Series(TX.summ_block(g))).reset_index()
    n_rep, n_fa = int((pr.kind == 'rep').sum()), int((pr.kind != 'rep').sum())
    w(hdr('变体内全部程序', '三种变体各自的全部程序（代表 %d + 四臂 %d）' % (n_rep, n_fa), '同 H 母体',
          'primary / cost_target（net12 目标选 λ）/ winsor（训练段 1%/99% winsor）'))
    w(md(vb))
    fa = pr[pr.kind != 'rep']
    if len(fa):
        w('### 2b. 四臂 K x A 的 M2（A0 v1.3 补登记；brief §6"单变量 M2 与双变量 M2 含一阶交互"）\n')
        fb = fa.groupby(['kind', 'mother_id', 'alpha']).agg(
            n=('descriptor_id', 'size'), d1=('d1', 'median'), d2=('d2', 'median'), full=('d_net8_ann', 'median'),
            m0_full=('m0_same_budget_full', 'median'), m2_minus_m0=('m2_minus_m0', 'median')).reset_index()
        w(hdr('(变体, 母体, α) 内 H ∈ {3,5,10,20} 的描述符中位', '四臂 M2 primary', '同 H 母体；m0_full = 同 α 的四臂线性臂'
              '（uni 对 A 臂 = K_res_log 线性；bi 对 AB 臂 = K_res_log 与 T_evlevel 线性合用）', 'M2 primary 四臂', H='3 / 5 / 10 / 20'))
        w(md(fb))
        w('%s。\n' % q('P1B-FA', '；'.join('%s：%d 个，两段中位 %s / %s，M2 − 同 α 线性臂 full 中位 %s、>0 占比 %s' % (
            kd_, len(g_), f(g_.d1.median()), f(g_.d2.median()), f(g_.m2_minus_m0.median()),
            pc((g_.m2_minus_m0 > 0).mean())) for kd_, g_ in fa.groupby('kind'))))
    if len(led):
        w('## 3. 程序动作台账（逐年；plan §7.3"所有 λ 与零修改结果在台账保留"）\n')
        act = led.groupby(['segment', 'variant', 'action']).size().unstack(fill_value=0).reset_index()
        w(hdr('计数', '全部 (程序 x 年)', '无', '按段 x 变体', unit='个', H='各程序自身 H'))
        w(md(act))
        lm = led[led.action == 'modified'].groupby(['segment', 'variant', 'lam']).size().unstack(fill_value=0).reset_index()
        w(hdr('被执行年份的 λ 计数', 'action = modified 的 (程序 x 年)', '无', '按段 x 变体', unit='个', H='各程序自身 H'))
        w(md(lm))
        w('## 4. 训练内形状（Q17 的 M2 部分）\n')
        mm = led[(led.action == 'modified') & (led.variant == 'primary')].copy()
        if len(mm):
            mm['u2_dom'] = mm.b_u2.abs() > mm.b_u.abs()
            pk_axis = {'%s|%s|%s|H%d' % (r_.m2_home_route, r_.mother_id, r_.member_id, int(r_.H)): r_.axis_id
                       for r_ in a2.itertuples() if 'FOURARM_KA' not in r_.Index}
            mm['axis'] = [('四臂_' + p.split('|')[1]) if p.startswith('FA|') else
                          pk_axis.get(p, p.split('|')[2].split('_')[0] + '（未映射）') for p in mm.program]
            sh = mm.groupby('axis').agg(n=('program', 'size'), b_u_med=('b_u', 'median'), b_u2_med=('b_u2', 'median'),
                                        b_uz_med=('b_uz', 'median'), u2_dominant=('u2_dom', 'mean'),
                                        b_u2_pos=('b_u2', lambda x: (x > 0).mean())).reset_index()
            w(hdr('标准化系数的中位 / 占比', 'primary 变体被执行的 (程序 x 年)', '无', '按成员轴',
                  unit='bp / 标准差（训练样本标准化后的 ridge 系数）', H='各程序自身 H'))
            w(md(sh))
            sg = mm.groupby('program').b_u2.apply(lambda x: (np.sign(x) == np.sign(x.iloc[0])).all() if len(x) > 1 else np.nan)
            w('%s。\n' % q('P1B-SHAPE', '被执行 (程序 x 年) %d 个里 |u² 系数| > |u 系数| 的占 %s；多年被执行的程序中 u² 符号各年一致的占 %s' % (
                len(mm), pc(mm.u2_dom.mean()), pc(sg.dropna().mean()))))
    bp = glob.glob(os.path.join(R, 'm2', '*', 'boot_[0-9][0-9].csv'))
    w('## 5. 学习不确定性（256 次时间块重采样）\n')
    if bp:
        bt = pd.concat([pd.read_csv(p) for p in bp], ignore_index=True)
        bt = bt[bt.b >= 0]
        bq = bt.groupby(['segment', 'program']).d_net8_outer.agg(['size', 'median', lambda x: x.quantile(.05),
                                                                  lambda x: x.quantile(.95)]).reset_index()
        bq.columns = ['segment', 'program', 'n_boot', 'median', 'q05', 'q95']
        bq.to_csv(os.path.join(TAB, 'M2_boot_quantiles.csv'), index=False)
        w(hdr('每程序 256 次重采样的外层 Δnet8 分位', '程序 x 重采样', '同 H 母体', '推导段；固定历史上的程序学习不确定性（不是新市场历史）'))
        w(md(bq.groupby('segment')[['median', 'q05', 'q95']].median().reset_index()))
        w('%s。重采样是在**同一段历史**上扰动训练样本，回答"程序学到的形状有多不稳"，不回答"新市场历史上会怎样"。\n' % q(
            'P1B-BOOT', '；'.join('%s：%d 个程序，5%% 分位 > 0 的占 %s、95%% 分位 < 0 的占 %s，90%% 区间宽度中位 %s' % (
                s_, len(g_), pc((g_.q05 > 0).mean()), pc((g_.q95 < 0).mean()), f((g_.q95 - g_.q05).median()))
                for s_, g_ in bq.groupby('segment'))))
    else:
        w('_（重采样尚在运行；完成后重生成本节）_\n')
    w('## 6. 没有得出的结论\n')
    w('- M2 是对已看历史的低维程序回放，**不消除**选 basis、选 z、选预算的后见性（plan §7.3）；它不是新生产动态策略。')
    w('- 内层选出零修改只是该年的程序动作，不淘汰该测量；技术回退（成熟日不足）与"后段收益弱就回退"无关。')
    w('- 训练内形状（u² / u·z）是描述，不推出"非单调可用"；只有冻结程序在后段的真实账户能回答（记录 B 之后）。\n')
    rp_ = pr[pr.kind == 'rep']
    summ = ['1. %d 个代表 M2 程序（§7.1 代表 x 母体 x H）+ %d 个四臂 K x A 的 M2 程序（v1.3），各 x 三变体 x 两推导段。' % (
        len(rp_), len(pr) - len(rp_)),
            '2. %s——M2 对母体接近 0。' % q('P1B-S1', '代表 M2 primary 两段中位 %s / %s，NW 区间排除 0 为正 %d、为负 %d' % (
                f(rp_.d1.median()), f(rp_.d2.median()),
                int((rp_.ci_excludes_zero.astype(bool) & (rp_.d_net8_ann > 0)).sum()),
                int((rp_.ci_excludes_zero.astype(bool) & (rp_.d_net8_ann < 0)).sum()))),
            '3. %s。' % q('P1B-S2', '代表 M2 − 同预算 M0 固定账户 full 中位 %s、>0 占比 %s' % (
                f(rp_.m2_minus_m0.median()), pc((rp_.m2_minus_m0 > 0).mean())))]
    if len(led):
        lp_ = led[led.variant == 'primary']
        zs = lp_.groupby('segment').action.apply(lambda x: (x == 'zero_modification').mean())
        summ.append('4. %s——M2 的"接近 0"有相当部分来自程序在该年不做修改，而不是修改后抵消。' % q(
            'P1B-ZERO', 'primary 变体 (程序 x 年) 中内层选择零修改的占比：' + '，'.join(
                '%s %s' % (s_, pc(v_)) for s_, v_ in zs.items())))
    if len(pr) > len(rp_):
        fa_ = pr[pr.kind != 'rep']
        summ.append('5. %s。' % q('P1B-S-FA', '四臂 M2：' + '；'.join('%s 两段中位 %s / %s、M2 − 同 α 线性臂 %s' % (
            kd_, f(g_.d1.median()), f(g_.d2.median()), f(g_.m2_minus_m0.median())) for kd_, g_ in fa_.groupby('kind'))))
    summ.append('%d. 程序动作与形状系数见 §3 / §4；学习不确定性见 §5%s。全部是推导段，不是 OOS。' % (
        len(summ) + 1, '' if bp else '（重采样完成后重生成）'))
    L[SUM_AT] = '## 摘要\n\n' + '\n'.join(summ) + '\n\n---\n'
    txt = '\n'.join(L)
    bad = TX.check_headers(txt)
    if bad:
        raise SystemExit('生成 FAIL：%d 张表缺表头项（行 %s）' % (len(bad), bad[:10]))
    for b in TX.FORBID:
        if b in txt:
            raise SystemExit('生成 FAIL：禁用词 %s' % b)
    p = os.path.join(R, 'reports', 'E6i_REPORT_part1b.md')
    open(p, 'w', encoding='utf-8').write(txt)
    pd.DataFrame(TX.QIDS).to_csv(os.path.join(TAB, 'query_ids_part1b.csv'), index=False)
    print('part1b: %s (%d 字节); query_id %d; %.0fs' % (p, len(txt.encode()), len(TX.QIDS), time.time() - t0))


if __name__ == '__main__':
    main()
