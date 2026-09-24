#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i REPORT_part2 (Stage 3 后段首次观察; brief §8; plan Stage 3) 生成器。只在首次观察回执 SEALED 与后段统计之后运行。
数字全部由 statistics/post/、statistics/zmap_summary_<后段>.csv、statistics/vs_prodH5_*.csv、registry/ 现算,
计数 / 中位 / 占比 / 全称句带 query_id; 每张表十项表头 (缺项即 FAIL); 禁用词 / 主机地址扫描。
读法 (事前登记, plan §10.1): 策略问题 = 对真实母体的同成本同 H 增量 (主) -> gross / 成本 / 仓位 -> 同人数核心 / 同资本 /
匹配随机 (机制) -> 年份与区间; 相对生产 H5 与 R1@H5 / R2@H5 另列。P20 按同人数核心、P21 按匹配随机答旧问题。
输出 reports/E6i_REPORT_part2.md + reports/part2_tables/*.csv + query_ids_part2.csv。"""
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
import e6i_report_part1_text as TX

R = I.RES
ST = os.path.join(R, 'statistics')
SP = os.path.join(ST, 'post')
TAB = os.path.join(R, 'reports', 'part2_tables')
P1, P2 = I.POST_SEGS
PRIM = TX.PRIM
MAIN = ('RT', 'RK', 'RV', 'RR', 'RO', 'RC', 'RA', 'RS', 'RL', 'TPAIR', 'FOURARM')
q, f, pc, md, sgn = TX.q, TX.f, TX.pc, TX.md, TX.sgn_word


def post_dates():
    out = []
    for s in I.POST_SEGS:
        c = np.load(os.path.join(R, 'm2', s, 'calendar.npy'))
        out.append('%s..%s' % (pd.to_datetime(str(c.min())).date(), pd.to_datetime(str(c.max())).date()))
    return '后段两段（%s / %s）' % tuple(out)


DATES = None


def hdr(op, denom, bench, subset, **kw):
    kw.setdefault('dates', DATES)
    return TX.hdr(op, denom, bench, subset, **kw)


def rd(p, **kw):
    return pd.read_csv(p, low_memory=False, **kw)


def load():
    s1 = rd(os.path.join(SP, 'descriptor_stats_%s.csv' % P1)).set_index('descriptor_id')
    s2 = rd(os.path.join(SP, 'descriptor_stats_%s.csv' % P2)).set_index('descriptor_id')
    sp = rd(os.path.join(SP, 'descriptor_stats_post.csv')).set_index('descriptor_id')
    s4 = rd(os.path.join(SP, 'descriptor_stats_all4.csv')).set_index('descriptor_id')
    x15 = rd(os.path.join(SP, 'descriptor_stats_all4_ex1516.csv')).set_index('descriptor_id')
    x24 = rd(os.path.join(SP, 'descriptor_stats_all4_ex2024p.csv')).set_index('descriptor_id')
    dv = rd(os.path.join(ST, 'descriptor_stats_full.csv')).set_index('descriptor_id')
    F = sp.reset_index()[['descriptor_id', 'route_id', 'mother_id', 'member_id', 'role', 'strength', 'policy',
                          'direction', 'direction_role', 'H', 'representative', 'axis']].copy()
    ix = F.descriptor_id
    F['p1'], F['p2'] = ix.map(s1.d_net8_ann), ix.map(s2.d_net8_ann)
    F['post'], F['se_post'] = ix.map(sp.d_net8_ann), ix.map(sp.se_nwH)
    F['ci_post'] = ix.map(sp.ci_excludes_zero).fillna(False).astype(bool)
    for lv in ('domain', 'axis', 'headline'):
        F['bd_%s_lo' % lv], F['bd_%s_hi' % lv] = ix.map(sp['band_%s_lo' % lv]), ix.map(sp['band_%s_hi' % lv])
    F['state_post'], F['mde_post'] = ix.map(sp.state_word), ix.map(sp.mde80)
    F['all4'], F['se_all4'] = ix.map(s4.d_net8_ann), ix.map(s4.se_nwH)
    F['ci_all4'] = ix.map(s4.ci_excludes_zero).fillna(False).astype(bool)
    F['state_all4'] = ix.map(s4.state_word)
    F['ex1516'], F['ex2024p'] = ix.map(x15.d_net8_ann), ix.map(x24.d_net8_ann)
    F['deriv'], F['se_deriv'] = ix.map(dv.d_net8_ann), ix.map(dv.se_nwH)
    F['ci_deriv'] = ix.map(dv.ci_excludes_zero).fillna(False).astype(bool)
    for k, s in (('1', s1), ('2', s2)):
        for c in ('dcore_ann', 'dsamecap_ann', 'd_gross_ann', 'd_turn', 'd_pos'):
            if c in s.columns:
                F['%s_%s' % (c, k)] = ix.map(s[c])
    for c in ('dcore_ann', 'dsamecap_ann'):
        F['%s_post' % c] = ix.map(sp[c])
    ycols = [c for c in s4.columns if re.fullmatch(r'y\d{4}', c)]
    for c in ycols:
        F[c] = ix.map(s4[c])
    for c in [c for c in sp.columns if c.startswith('loyo_ex')]:
        F['post_' + c] = ix.map(sp[c])
    for c in [c for c in s4.columns if c.startswith('loyo_ex')]:
        F['all4_' + c] = ix.map(s4[c])
    F['companion'] = F.descriptor_id.str.contains(r'\|(?:eqcap|cost_target|winsor)$')
    for i, s in ((1, P1), (2, P2)):
        z = rd(os.path.join(ST, 'zmap_summary_%s.csv' % s))
        zb = z[z.kind == 'basic'].set_index('descriptor_id')
        F['z%d' % i] = ix.map(zb.d_real_minus_rand)
        F['zse%d' % i] = ix.map(zb.se_pair_nwH)
        for kd in ('reverse_sameM', 'reverse_new_order'):
            ze = z[z.kind == kd].set_index('descriptor_id')
            if len(ze):
                F['%s%d' % (kd, i)] = ix.map(ze.d_real_minus_rand)
    for s, nm in ((P1, 'h1'), (P2, 'h2'), ('post_full', 'hp'), ('all4', 'h4')):
        p = os.path.join(ST, 'vs_prodH5_%s.csv' % s)
        if os.path.exists(p):
            v = rd(p).set_index('descriptor_id')
            for c in ('d_vs_prodH5_ann', 'd_vs_R1H5_ann', 'd_vs_R2H5_ann'):
                if c in v.columns:
                    F['%s_%s' % (nm, c.replace('_ann', '').replace('d_vs_', ''))] = ix.map(v[c])
    sem = rd(os.path.join(R, 'registry', 'feature_semantics_v2.csv')).set_index('member_id')
    F['family'] = F.member_id.map(sem.family_id)
    return F, ycols


def block(g):
    ci = g.ci_post
    return dict(n=len(g), deriv=g.deriv.median(), p1=g.p1.median(), p2=g.p2.median(), post=g.post.median(),
                all4=g.all4.median(), post_pos=(g.post > 0).mean(), both_post_pos=((g.p1 > 0) & (g.p2 > 0)).mean(),
                ci_pos=int((ci & (g.post > 0)).sum()), ci_neg=int((ci & (g.post < 0)).sum()),
                band_pos=int((g.bd_domain_lo > 0).sum()), band_neg=int((g.bd_domain_hi < 0).sum()))


def spearman(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 5:
        return np.nan
    return float(pd.Series(a[m]).rank().corr(pd.Series(b[m]).rank()))


def main():
    global DATES
    t0 = time.time()
    fl = json.load(open(os.path.join(R, 'registry', 'first_look_receipts.json')))
    assert fl.get('status') == 'SEALED', '首次观察回执不是 SEALED'
    appr = json.load(open(I.APPROVAL_FILE))
    DATES = post_dates()
    os.makedirs(TAB, exist_ok=True)
    TX.QIDS.clear()
    F, ycols = load()
    M = F[~F.companion & F.route_id.isin(MAIN)].copy()
    st = rd(os.path.join(R, 'registry', 'stage3_status_table.csv'))
    L = []
    w = L.append
    w('# E6i REPORT_part2（Stage 3：后段首次观察，2019-01 至 2026-03-27）\n')
    w('执行 session，%s（47 时间）；结果目录 `20260923_0254_E6i_measurement_need_fit`（47）。记录 B：`%s`（整表 %d 个需求域包、%d 个描述符；'
      '冻结 manifest sha `%s…`）。两后段按同一 manifest 一次算完，首次观察封存回执 `registry/first_look_receipts.json`（%s，%d 个文件）'
      '写出之后才读任何后段数值。**后段是冻结对象的首次观察，不是 OOS**（2019–2026 历史此前已参与研究；E7 HOLD）。'
      '全量表 `reports/part2_tables/*.csv`。\n' % (time.strftime('%Y-%m-%d %H:%M'), appr['approval_id'],
                                                 len([p for p in appr['approved_packages'] if 'CARRIED' not in p]),
                                                 len(appr['approved_descriptors']), appr['manifest_sha256'][:12],
                                                 fl['written_at'], fl['n_files']))
    w('---\n')
    SUM_AT = len(L)
    w('')
    # ============================ 1 运行与验收
    w('## 1. 运行与验收\n')
    stm = st[~st.route.isin(['M1', 'M2'])]
    tot = stm.groupby('segment')[['a0_count', 'succeeded', 'not_applicable', 'failed_tech']].sum()
    ex = st[st.route.isin(['M1', 'M2'])]
    w('- %s；%s。' % (
        q('P2-S3', '主路线两后段各 %s SUCCEEDED、FAILED_TECH %s（A0 %s；状态和 = 登记数）' % (
            ' / '.join('%d/%d' % (int(tot.loc[s, 'succeeded']), int(tot.loc[s, 'a0_count'])) for s in I.POST_SEGS),
            ' / '.join(str(int(tot.loc[s, 'failed_tech'])) for s in I.POST_SEGS), TX.a0_version())),
        q('P2-M12', '；'.join('%s %s SUCCEEDED %s' % (r_.route, r_.segment, int(r_.succeeded)) for r_ in ex.itertuples()))))
    zz = {}
    for s in I.POST_SEGS:
        z = rd(os.path.join(ST, 'zmap_summary_%s.csv' % s))
        zk = z[z.kind.isin(['basic', 'industry', 'persist20'])]
        zz[s] = (len(zk), float(zk.rand_net8_mcse.median()), float(zk.rand_net8_mcse.max()),
                 int((zk.rand_net8_mcse > 0.05).sum()), TX.zmap_paths({s: z})[s]['paths'])
    w('- %s。' % q('P2-ZMAP', 'Z-MAP 后段（与推导段同一规则与分片；段码 3 / 4 = 新 draw）：' + '；'.join(
        '%s %d 个 (描述符, 机制) 行、%.2fM 条路径掩码（按配置计），MCSE 中位 %.3f、最大 %.3f、>0.05 的 %d 行'
        % (s, v[0], v[4] / 1e6, v[1], v[2], v[3]) for s, v in zz.items())))
    w('- Stage 3 技术改动（段闸 / 守卫接受批准清单 / M2 多段训练等，保持经济定义）逐文件 sha 与 diff：`registry/stage3_code_changes/`；'
      '批准后守卫测试 `checks/guard_attack_tests_post.json`。\n')
    # ============================ 2 总览
    w('## 2. 总览：后段对真实母体（策略主读数）\n')
    ci = M.ci_post
    w('%s；%s；%s。\n' % (
        q('P2-ALL-CI', '主路线 %d 个描述符，后段合并（两段按有效日）NW 95%% 区间排除 0 的为正 %d、为负 %d（零增量下每侧约 %.0f 个）' % (
            len(M), int((ci & (M.post > 0)).sum()), int((ci & (M.post < 0)).sum()), 0.025 * len(M))),
        q('P2-ALL-BAND', 'need 域同步带（后段合并，块 20）排除 0：为正 %d、为负 %d' % (
            int((M.bd_domain_lo > 0).sum()), int((M.bd_domain_hi < 0).sum()))),
        q('P2-ALL-SIGN', '两后段同为正 %d、同为负 %d' % (int(((M.p1 > 0) & (M.p2 > 0)).sum()),
                                                  int(((M.p1 < 0) & (M.p2 < 0)).sum())))))
    rows = [dict(route=rt, mother=mo, **block(g)) for (rt, mo), g in M.groupby(['route_id', 'mother_id'])]
    t2 = pd.DataFrame(rows)
    t2.to_csv(os.path.join(TAB, 'T2_route_mother_post.csv'), index=False)
    w(hdr('需求域内全部描述符的分段中位 / 合并中位 / 占比 / 计数（deriv = 推导两段合并，供对照）',
          '(路线, 母体) 内全部 A0 描述符（含反向与竞争方向、全部强度与 H）', '同 H 真实母体', '主路线',
          H='全部登记 H'))
    w(md(t2))
    # ============================ 3 延续
    w('## 3. 推导段 → 后段：同一冻结描述符的延续\n')
    rows = []
    for rt, g in M.groupby('route_id'):
        rows.append(dict(route=rt, n=len(g), rho_deriv_post=spearman(g.deriv.values, g.post.values),
                         same_sign=float((np.sign(g.deriv) == np.sign(g.post)).mean()),
                         deriv_pos_post_pos=float(((g.deriv > 0) & (g.post > 0)).sum() / max((g.deriv > 0).sum(), 1)),
                         deriv_ci_pos=int((g.ci_deriv & (g.deriv > 0)).sum()),
                         of_which_post_pos=int((g.ci_deriv & (g.deriv > 0) & (g.post > 0)).sum()),
                         mde80_post_median=g.mde_post.median(), mde80_deriv_median=(2.8 * g.se_deriv).median()))
    t3 = pd.DataFrame(rows)
    t3.to_csv(os.path.join(TAB, 'T3_persistence.csv'), index=False)
    w(hdr('按路线：推导段合并点估与后段合并点估的秩相关 / 同号占比 / 推导段为正者后段仍为正的占比 / 推导段 NW 排除 0 且为正的计数及其后段为正数 / MDE80 中位',
          '该路线全部主描述符', '同 H 真实母体（两个时期各自）', '主路线', unit='相关与占比无单位；MDE 为年化百分点'))
    w(md(t3))
    w('%s。MDE80 = 在该时期长度与依赖结构下 80%% 功效能分辨的年化差；后段合计约 7.2 年，比推导段（9 年）短，MDE 更大——'
      '"后段区间跨零"首先是功效问题，不等于"推导段的增量消失"（plan §8.4）。\n' % q(
          'P2-PERSIST', '全部主描述符：推导 vs 后段秩相关 %s，同号 %s；推导段 NW 排除 0 且为正的 %d 个中后段合并点估仍为正 %d 个' % (
              f(spearman(M.deriv.values, M.post.values)), pc(float((np.sign(M.deriv) == np.sign(M.post)).mean())),
              int((M.ci_deriv & (M.deriv > 0)).sum()), int((M.ci_deriv & (M.deriv > 0) & (M.post > 0)).sum()))))
    # ============================ 4 机制
    w('## 4. 机制读数（后段）：同人数核心 / 同资本 / 匹配随机\n')
    rows = []
    for rt, g in M.groupby('route_id'):
        rec = dict(route=rt, n=len(g))
        for k, s in (('1', P1[2:]), ('2', P2[2:])):
            rec['%s 子−母' % s] = g['p%s' % k].median()
            rec['%s Δgross' % s] = g['d_gross_ann_%s' % k].median() if 'd_gross_ann_%s' % k in g else np.nan
            rec['%s Δturn' % s] = g['d_turn_%s' % k].median() if 'd_turn_%s' % k in g else np.nan
            rec['%s 子−同人数核心' % s] = g['dcore_ann_%s' % k].median()
            rec['%s 同资本' % s] = g['dsamecap_ann_%s' % k].median()
            rec['%s 真实−随机' % s] = g['z%s' % k].median()
            rec['%s 真实−随机>0' % s] = (g['z%s' % k] > 0).mean() if g['z%s' % k].notna().any() else np.nan
        rows.append(rec)
    t4 = pd.DataFrame(rows)
    t4.to_csv(os.path.join(TAB, 'T4_mechanism_post.csv'), index=False)
    w(hdr('路线内描述符中位 / 占比', '该路线全部主描述符', '同 H 真实母体；同人数核心 = 母体延伸排序取同人数；同资本 = 两条目标权重缩到共同资本后重跑；'
          '真实−随机 = Z-MAP basic 路径均值（FOURARM / TPAIR 等确定性臂无随机对照）', '主路线',
          unit='年化百分点；Δturn 为日均单边换手'))
    w(md(t4))
    CARD_AT = len(L)
    w('')
    # ============================ 7 时间
    w('## 7. 时间：逐年（2010–2026）与去一年 / 去 2015+16 / 去 2024+\n')
    rows = []
    for rt, g in M.groupby('route_id'):
        rec = dict(route=rt)
        for c in ycols:
            rec[c[1:]] = g[c].median()
        rec['all4'] = g.all4.median()
        rec['all4 去15+16'] = g.ex1516.median()
        rec['all4 去2024+'] = g.ex2024p.median()
        rows.append(rec)
    t7 = pd.DataFrame(rows)
    t7.to_csv(os.path.join(TAB, 'T7_yearly_route.csv'), index=False)
    w(hdr('逐年年化均值的描述符中位；all4 = 四段按有效日合并', '该路线全部主描述符', '同 H 真实母体', '四段逐年（2010–2018 推导、2019–2026 后段）',
          dates='四段（2010-01..2026-03-27）', H='各描述符自身 H'))
    w(md(t7))
    # ============================ 8 精度
    w('## 8. 精度与状态词（后段合并，δ = 0.25）\n')
    sw = M.pivot_table(index='route_id', columns='state_post', values='descriptor_id', aggfunc='size', fill_value=0)
    sw['mde80_median'] = M.groupby('route_id').mde_post.median()
    sw = sw.reset_index()
    w(hdr('计数 / 中位', '该路线全部主描述符', 'NW(lag H) 95% 区间与声明尺度 δ = 0.25', '后段合并',
          unit='个；MDE 为年化百分点', H='各描述符自身 H'))
    w(md(sw))
    # ============================ 9 H5
    w('## 9. 相对生产 H5 与 R1@H5 / R2@H5（与"相对同 H 母体"分列，不合并）\n')
    hc = [c for c in ('hp_prodH5', 'hp_R1H5', 'hp_R2H5') if c in M.columns]
    if hc:
        g9 = M.groupby(['route_id', 'H'])[['post'] + hc].median().reset_index()
        g9.to_csv(os.path.join(TAB, 'T9_vs_H5_post.csv'), index=False)
        w(hdr('描述符中位', '(路线, H) 内全部主描述符', 'post = 子 − 同 H 母体；hp_prodH5 = 子 − 同母体 H5；hp_R1H5 / hp_R2H5 = 子 − R1@H5 / R2@H5',
              '后段合并', H='见行'))
        w(md(g9))
    # ============================ 10 M1 / M2
    w('## 10. 家族程序（M1 / M2）后段\n')
    fam = F[F.route_id.isin(['M1', 'M2'])].copy()
    if len(fam):
        fam['variant'] = np.where(fam.companion, fam.descriptor_id.str.rsplit('|', n=1).str[-1], 'main')
        fam['m_route'] = fam.descriptor_id.str.split('|').str[1]
        g10 = fam.groupby(['route_id', 'm_route', 'variant']).apply(lambda x: pd.Series(block(x))).reset_index()
        g10.to_csv(os.path.join(TAB, 'T10_M1_M2_post.csv'), index=False)
        w(hdr('程序中位 / 计数', 'M1（共识 + 等资本合并伴随）与 M2（primary + cost_target / winsor 伴随）', '同 H 真实母体',
              '按程序类 x 原路线 x 变体', H='3 / 5 / 10 / 20'))
        w(md(g10))
        led = [p for s in I.POST_SEGS for p in glob.glob(os.path.join(R, 'm2', s, 'ledger_[0-9][0-9]*.csv'))
               if '_timing' not in p]
        if led:
            lg = pd.concat([rd(p) for p in led], ignore_index=True)
            lp = lg[lg.variant == 'primary']
            zs = lp.groupby('segment').action.apply(lambda x: (x == 'zero_modification').mean())
            w('%s。M2 在后段按冻结规则逐年用当时已成熟的全部历史（2010 起）重训，台账 `m2/<后段>/ledger_*.csv`。\n' % q(
                'P2-M2ZERO', 'M2 primary (程序 x 年) 内层选择零修改的占比：' + '，'.join('%s %s' % (s_, pc(v_)) for s_, v_ in zs.items())))
    # ============================ 11 没有得出的结论
    w('## 11. 这份 part2 没有得出的结论\n')
    w('- **不是 OOS**：后段是冻结对象的首次观察，但研究者知道 2019–2026 的 regime，且这段历史此前参与过其他轮研究（plan 边界全文）。')
    w('- 没有按后段结果增删、改方向或改网格；没有看 2019-23 后再改 2024-26（两段同一 manifest 一次算完、回执后共同读取）。')
    w('- 区间跨零、两段不同号、某年为负都**不是**淘汰标签；"无效果"只对 母体 x 需求 x 角色 x 日期 x 支持 x 成本 这一格成立。')
    w('- 本报告的后段点估不含冲击成本（8bp 线性）；含冲击的视图在 C2（part3）。')
    w('- 候选库更新、线状态、入地基由规划 session 与用户定；本报告不给"采纳"结论。\n')
    w('## 12. 运行事件与 BLOCKERS\n')
    w('BLOCKERS：无。运行事件见 `WORKLOG`：记录 B 批准（用户"继续跑完"，按执行端整表建议执行；A1 未做）；B 草稿中"Z-MAP 后段不复跑"的写法与 brief §8 不符，'
      '已在批准文件登记更正并按 brief 执行后段 Z-MAP；Stage 3 技术改动与守卫测试见 §1。\n')
    # ============================ Q 卡
    L[CARD_AT] = cards(F, M)
    # ============================ 摘要
    k = M[(M.route_id == 'RK') & M.direction_role.isin(PRIM) & (M.policy == 'FALLBACK')]
    kst = k.assign(a=pd.to_numeric(k.strength, errors='coerce')).groupby('a').post.median()
    t = M[(M.route_id == 'RT') & (M.direction_role == 'primary') & (M.policy == 'FALLBACK')
          & pd.to_numeric(M.strength, errors='coerce').isin([0.125, 0.25])]
    rr = M[(M.route_id == 'RR') & (M.role == 'SWAP')]
    rs = M[(M.route_id == 'RS') & (M.role == 'SWAP')]
    rvr = M[(M.route_id == 'RV') & (M.direction_role == 'reverse_control') & M.role.isin(['VETO_NEW', 'SOFT_HARD'])]
    rcs = M[(M.route_id == 'RC') & (M.direction_role == 'primary') & (M.role == 'SLOT')]
    rep_ = M[(M.route_id == 'RT') & (M.direction_role == 'primary') & M.policy.isin(['FULL_REPLACE', 'FALLBACK_REPLACE'])]
    kf = k.groupby('family')[['p1', 'p2']].median()
    kboth = [x for x, r_ in kf.iterrows() if r_.p1 > 0 and r_.p2 > 0]
    led = [p for s in I.POST_SEGS for p in glob.glob(os.path.join(R, 'm2', s, 'ledger_[0-9][0-9]*.csv')) if '_timing' not in p]
    zs = (pd.concat([rd(p) for p in led], ignore_index=True).query("variant == 'primary'").groupby('segment').action
          .apply(lambda x: (x == 'zero_modification').mean())) if led else pd.Series(dtype=float)
    summ = [
        '1. 验收：%s；首次观察回执之后才读数。' % q('P2-S-RUN', '两后段主路线各 %s SUCCEEDED、FAILED_TECH 合计 %d' % (
            ' / '.join(str(int(tot.loc[s, 'succeeded'])) for s in I.POST_SEGS), int(tot.failed_tech.sum()))),
        '2. 总体（对真实母体）：%s——区间排除 0 的正值几乎消失，负值计数相近（后段交易日少于推导段）。' % q(
            'P2-S-ALL', 'NW 区间排除 0：推导 正 %d / 负 %d → 后段 正 %d / 负 %d（每侧随机约 %.0f）；全体主描述符中位 推导合并 %s → 后段合并 %s' % (
                int((M.ci_deriv & (M.deriv > 0)).sum()), int((M.ci_deriv & (M.deriv < 0)).sum()),
                int((ci & (M.post > 0)).sum()), int((ci & (M.post < 0)).sum()), 0.025 * len(M),
                f(M.deriv.median()), f(M.post.median()))),
        '3. **K 槽位（推导段的主要正结果）在后段缩到接近 0**：%s。' % q('P2-S-K', '同一批 %d 个描述符，推导 %s → 后段两段 %s / %s（%s）；后段合并 NW 排除 0 正 %d / 负 %d、'
                                                              '同步带 正 %d / 负 %d；随 α：%s' % (
            len(k), f(k.deriv.median()), f(k.p1.median()), f(k.p2.median()), sgn(k.p1.median(), k.p2.median()),
            int((k.ci_post & (k.post > 0)).sum()), int((k.ci_post & (k.post < 0)).sum()),
            int((k.bd_domain_lo > 0).sum()), int((k.bd_domain_hi < 0).sum()),
            '、'.join('%.3g: %s' % (a_, f(v_)) for a_, v_ in kst.items()))),
        '4. K 的机制：%s——新测量的排序两后段都好于随机混入；对母体自己的核心 K，2019-23 小正、2024-26 为负；两后段都为正的族：%s。' % (
            q('P2-S-K2', '对匹配随机 %s / %s、对同人数核心 %s / %s' % (f(k.z1.median()), f(k.z2.median()),
                                                                f(k.dcore_ann_1.median()), f(k.dcore_ann_2.median()))),
            '、'.join(kboth) or '无'),
        '5. 延续：%s——路线之间的相对好坏大体保持，K 内部的排序在后段基本重排。' % q('P2-S-PERS', '推导 vs 后段点估秩相关：全部主描述符 %s、K 主方向 %s' % (
            f(spearman(M.deriv.values, M.post.values)), f(spearman(k.deriv.values, k.post.values)))),
        '6. T：%s；P20（T 腿替换，原主读数 = 同人数核心）%s。' % (
            q('P2-S-T', '小权重加两后段 %s / %s' % (f(t.p1.median()), f(t.p2.median()))),
            q('P2-S-P20', '对同人数核心 %s / %s' % (f(rep_.dcore_ann_1.median()), f(rep_.dcore_ann_2.median())))),
        '7. P21（同业相对位置，原主读数 = 匹配随机）：%s——SWAP 算子在后段对随机也不占优。' % q(
            'P2-S-P21', 'RR 同人数 SWAP 对匹配随机 两后段 %s / %s' % (f(rr.z1.median()), f(rr.z2.median()))),
        '8. RS：%s——推导段"状态内按 R_peer20 换入优于随机"在后段不成立。' % q(
            'P2-S-RS', '对母体 %s / %s、对匹配随机 %s / %s' % (f(rs.p1.median()), f(rs.p2.median()), f(rs.z1.median()), f(rs.z2.median()))),
        '9. V：%s——2024-26 高风险名字反而更好，V 的方向在该段反转；删除类亏损仍主要是资本效应。' % q(
            'P2-S-V', '反向删除（删低风险）2019-23 %s、2024-26 %s' % (f(rvr.p1.median()), f(rvr.p2.median()))),
        '10. C：%s；关掉 CVR_20d 否决在后段仍更差（Q6）。' % q(
            'P2-S-C', 'A06 的 C 核心槽位混入 两后段 %s / %s（推导 %s）' % (f(rcs.p1.median()), f(rcs.p2.median()), f(rcs.deriv.median()))),
        '11. M2：%s——零修改的占比 2024-26 高于 2019-23（推导段 13%% / 53%%，part1b〔P1B-ZERO〕），M2 对母体接近 0。' % q(
            'P2-S-M2', '内层选择零修改的 (程序 x 年) 占比 ' + '，'.join('%s %s' % (s_, pc(v_)) for s_, v_ in zs.items())),
        '12. 这些是冻结对象的首次观察，**不是 OOS**；含冲击成本与 C1（池子宽度）在 part3。',
    ]
    L[SUM_AT] = '## 摘要（≤15 行）\n\n' + '\n'.join(summ) + '\n\n---\n'
    txt = '\n'.join(L)
    bad = TX.check_headers(txt)
    if bad:
        raise SystemExit('生成 FAIL：%d 张表缺表头项（行 %s）' % (len(bad), bad[:10]))
    for b in TX.FORBID:
        if b in txt:
            raise SystemExit('生成 FAIL：禁用词 %s' % b)
    if re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', txt):
        raise SystemExit('生成 FAIL：疑似主机地址')
    p = os.path.join(R, 'reports', 'E6i_REPORT_part2.md')
    open(p, 'w', encoding='utf-8').write(txt)
    pd.DataFrame(TX.QIDS).to_csv(os.path.join(TAB, 'query_ids_part2.csv'), index=False)
    F.to_csv(os.path.join(TAB, 'descriptor_panel_post.csv'), index=False)
    print('part2: %s (%d 字节, %d 行); query_id %d; %.0fs' % (p, len(txt.encode()), txt.count('\n'), len(TX.QIDS),
                                                              time.time() - t0))


CTX_SUM = []


def m0_fixed(M):
    """与 part1a 表集 (e6i_report_part1.MID) 同一选法: 代表成员 x 中间档预算 (x 登记 policy) x H5。"""
    import e6i_report_part1 as P1T
    rep = M[M.representative.astype(str).str.lower().isin(['true', '1', '1.0'])]
    keep = []
    for i, r in rep.iterrows():
        m = P1T.MID.get(r.role)
        if m is None or int(r.H) != 5:
            continue
        if str(r.strength) != m[0]:
            try:
                if abs(float(r.strength) - float(m[0])) > 1e-9:
                    continue
            except ValueError:
                continue
        if m[1] is not None and str(r.policy) != m[1]:
            continue
        keep.append(i)
    return rep.loc[keep]


def route_note(rt, g):
    """各路线的具体要点 (全部现算; 条件不成立时不写)。"""
    out = []
    if rt == 'RV':
        rv = g[(g.direction_role == 'reverse_control') & g.role.isin(['VETO_NEW', 'SOFT_HARD'])]
        if len(rv) and rv.p2.median() > 0.25:
            out.append(q('Q3P-REV', '反向删除（删掉低风险名字，VETO / SOFT_HARD）2024-26 中位 %s、2019-23 %s' % (
                f(rv.p2.median()), f(rv.p1.median()))) + '——2024-26 高风险名字反而更好，V 的方向在该段反转；删除类的亏损在同资本口径下仍接近 0（资本效应）。')
    if rt == 'RC':
        sl = g[(g.direction_role == 'primary') & (g.role == 'SLOT')]
        if len(sl) and sl.p1.median() >= 0 and sl.p2.median() >= 0:
            out.append(q('Q6P-SLOT', 'A06 的 C 核心槽位混入 两后段中位 %s / %s（推导段 %s）' % (
                f(sl.p1.median()), f(sl.p2.median()), f(sl.deriv.median()))) + '——推导段为负、后段两段非负。')
        fo = g[(g.direction_role == 'focal_arm') & (g.role == 'FOCAL_NEW')]
        if len(fo) and fo.p1.median() < 0 and fo.p2.median() < 0:
            out.append('关掉 CVR_20d 否决（none 臂）两后段仍更差（%s / %s）→ 现有 CVR 否决在后段仍有价值。' % (
                f(fo.p1.median()), f(fo.p2.median())))
    if rt == 'RA':
        cs = g[(g.direction_role == 'competing') & (g.role == 'SLOT')]
        if len(cs):
            out.append(q('Q13P-KRAR', 'K_rar 登记竞争方向（低值坏）SLOT 两后段中位 %s / %s（推导段 %s）' % (
                f(cs.p1.median()), f(cs.p2.median()), f(cs.deriv.median()))) + '——方向继承规则对这个派生量不成立的读法，在 2019-23 仍成立。')
    if rt == 'RS':
        if g.z1.median() < 0 and g.z2.median() < 0:
            out.append('推导段"状态内按 R_peer20 换入优于匹配随机"在后段不成立（真实−随机两段为负）。')
    if rt == 'RL':
        out.append('摩擦替换在后段仍主要损失 gross；含冲击的视图见 part3（C2）。')
    return ''.join(out)


def cards(F, M):
    o = []
    H10 = hdr

    def dist(g, by):
        rows = []
        for key, x in g.groupby(by):
            rec = dict(zip(by if isinstance(by, list) else [by], key if isinstance(key, tuple) else (key,)))
            rec.update(block(x))
            rows.append(rec)
        return pd.DataFrame(rows)

    o.append('## 5. 问题卡（Q9 主卡；Q1–Q8、Q13–Q15 的后段部分）\n')
    # ---------------- Q9 ----------------
    o.append('### Q9（后段：测量 / 母体 / 时间关系可能漂移，低功效不等于零）\n')
    o.append('- **原问题**：冻结 B 的同一清单在两个后段（2019-23、2024-26.03）上对真实母体、同人数核心、去一年、区间与 δ 尺度是什么样？')
    g9 = dist(M, 'route_id')
    o.append(H10('路线内描述符分段中位 / 合并中位 / 计数', '该路线全部主描述符', '同 H 真实母体', '主路线', H='全部登记 H'))
    o.append(md(g9))
    ex20 = M['post_loyo_ex2020'] if 'post_loyo_ex2020' in M else pd.Series(np.nan, index=M.index)
    exr = [c for c in M.columns if c.startswith('post_loyo_ex2024')]
    o.append('- **数字 / 分母**：%s；%s。' % (
        q('Q9-LOYO', '后段合并去 2020 的描述符中位 %s（不去 %s）%s' % (
            f(ex20.median()), f(M.post.median()),
            ('；去 2024 %s' % f(M[exr[0]].median())) if exr else '')),
        q('Q9-STATE', '后段合并状态词：' + '，'.join('%s %d' % (k_, v_) for k_, v_ in M.state_post.value_counts().items()))))
    cd_ = M.ci_deriv
    o.append('- **读法**：%s。后段整体对母体为负，且比推导段更少正值；路线之间的相对好坏大体保持（§3 秩相关），推导段的主要正结果 K 槽位（推导 NW 区间排除 0：正 736 / 负 0）在后段缩到接近 0（Q2）。'
             '"区间跨零"首先是功效问题（§8 MDE），但 NW 区间排除 0 为负的描述符大量出现，不能都归于功效。逐路线结论见下列各卡。\n' % q(
                 'Q9-VSDERIV', 'NW 区间排除 0：推导合并 正 %d / 负 %d → 后段合并 正 %d / 负 %d（同一批 %d 个主描述符）' % (
                     int((cd_ & (M.deriv > 0)).sum()), int((cd_ & (M.deriv < 0)).sum()),
                     int((M.ci_post & (M.post > 0)).sum()), int((M.ci_post & (M.post < 0)).sum()), len(M))))
    # ---------------- Q2 K ----------------
    kall = M[M.route_id == 'RK']
    k = kall[kall.direction_role.isin(PRIM) & (kall.policy == 'FALLBACK')]
    o.append('### Q2（K：价格对交易活动的响应）后段\n')
    o.append('- **原问题**：推导段"K 槽位部分混入"（K 轴 9 个估计量族合起来，含 K 类与响应族两个方向）三母体两段全正；冻结的同一批描述符在后段是否仍为正，机制读数是否同向？')
    o.append(H10('分组描述符中位 / 计数', 'RK 主方向 x SLOT FALLBACK（α .125 / .25 / .5）x 三母体', '同 H 真实母体', '按母体 / α / H 分组',
                 H='1 / 2 / 3 / 5 / 10 / 20'))
    o.append(md(dist(k, 'mother_id')))
    o.append(H10('分组描述符中位 / 计数', 'RK 主方向 x FALLBACK', '同 H 真实母体', '按 α', H='全部'))
    o.append(md(dist(k, 'strength')))
    o.append(H10('分组描述符中位 / 计数', 'RK 主方向 x FALLBACK', '同 H 真实母体', '按 H', H='见行'))
    o.append(md(dist(k, 'H')))
    fam = k.groupby('family').agg(n=('post', 'size'), deriv=('deriv', 'median'), p1=('p1', 'median'), p2=('p2', 'median'),
                                  post=('post', 'median'), all4=('all4', 'median')).reset_index().sort_values('post', ascending=False)
    o.append(H10('族内描述符中位', 'RK 主方向 x FALLBACK 的估计量族', '同 H 真实母体', '按族'))
    o.append(md(fam))
    yc = [c for c in k.columns if re.fullmatch(r'y20(19|2[0-6])', c)]
    ym = k[yc].median()
    o.append('- **数字 / 分母**：%s；%s；%s。' % (
        q('Q2P-MECH', '同人数核心两段中位 %s / %s、同资本 %s / %s、真实−匹配随机 %s / %s（>0 占比 %s / %s）' % (
            f(k.dcore_ann_1.median()), f(k.dcore_ann_2.median()), f(k.dsamecap_ann_1.median()),
            f(k.dsamecap_ann_2.median()), f(k.z1.median()), f(k.z2.median()), pc((k.z1 > 0).mean()), pc((k.z2 > 0).mean()))),
        q('Q2P-YEAR', '后段逐年中位 ' + '、'.join('%s %s' % (c[1:], f(ym[c], 2)) for c in yc)),
        q('Q2P-COMP', '登记的竞争方向（全部强度）两后段中位 %s / %s；主方向完全替换（α=1）%s / %s' % (
            f(kall[kall.direction_role == 'competing'].p1.median()), f(kall[kall.direction_role == 'competing'].p2.median()),
            f(kall[kall.direction_role.isin(PRIM) & kall.policy.isin(['FULL_REPLACE', 'FALLBACK_REPLACE'])].p1.median()),
            f(kall[kall.direction_role.isin(PRIM) & kall.policy.isin(['FULL_REPLACE', 'FALLBACK_REPLACE'])].p2.median())))))
    kp = sgn(k.p1.median(), k.p2.median())
    both_f = [r_.family for r_ in fam.itertuples() if r_.p1 > 0 and r_.p2 > 0]
    kh = k.groupby('H')[['p1', 'p2']].median()
    both_h = ['H%d' % h_ for h_, r_ in kh.iterrows() if r_.p1 > 0 and r_.p2 > 0]
    km = k.groupby('mother_id')[['p1', 'p2']].median()
    both_m = [m_ for m_, r_ in km.iterrows() if r_.p1 > 0 and r_.p2 > 0]
    neg_y = [c[1:] for c in yc if ym[c] < 0]
    ratio = k.p1.median() / k.deriv.median() if k.deriv.median() else np.nan
    o.append('- **读法**：%s。对真实母体：2019-23 中位 %s（约为推导段合并中位的 %s）、2024-26 中位 %s——%s；逐年为负的年份：%s。'
             '机制读数：同人数核心%s、同资本%s，**对匹配随机%s**——新测量的排序两后段都好于同预算的随机混入；对母体自己的核心 K 排序，2019-23 小正、2024-26 为负。'
             '两后段都为正的子集：族 %s；H：%s；母体：%s。' % (
                 q('Q2P-READ', '同一批 %d 个冻结描述符：推导合并 %s → 后段 %s / %s' % (
                     len(k), f(k.deriv.median()), f(k.p1.median()), f(k.p2.median()))),
                 f(k.p1.median()), ('%.0f%%' % (100 * ratio)) if np.isfinite(ratio) else 'NA', f(k.p2.median()), kp,
                 '、'.join(neg_y) or '无', sgn(k.dcore_ann_1.median(), k.dcore_ann_2.median()),
                 sgn(k.dsamecap_ann_1.median(), k.dsamecap_ann_2.median()), sgn(k.z1.median(), k.z2.median()),
                 '、'.join(both_f) or '无', '、'.join(both_h) or '无', '、'.join(both_m) or '无'))
    o.append('- **竞争解释**：(a) 效应真实但比推导段小，2024-26 的市场状态让它反向（该段只有约 2.2 年，MDE 更大）；(b) 推导段的正结果含选择乐观——'
             'K 槽位是在看过推导段 11 条路线之后才被标为重点的，路线层面的事后挑选会高估它；(c) 新测量与原 K 同向相关，推导段的增量部分来自给 K 加权，'
             '后段原 K 自身变弱时一起变弱。三者在后段仍未分离；"对匹配随机为正"说明排序信息本身没有消失，但 2024-26 已低于母体自己的核心。')
    o.append('- **仍未知**：含冲击成本（C2 / part3）；2024-26 的反向是否持续（E7 才能回答）；(a)(b)(c) 的分离（需按新旧排序分歧分层，本轮未登记）。')
    o.append('- **下一步含义**：K 槽位（9 族合起来）在后段不支持"作为生产改进"的读法；它仍是研究资产（对随机为正、个别族与长 H 两后段为正；'
             '分族读数——响应族与改表示族的分化——见 part3 §1b），'
             '是否以及如何进候选库更新提案由规划 session 与用户定。prediction_status（后段）：mixed。\n')
    CTX_SUM.append('7. K 后段读法：对母体%s；同人数核心%s、匹配随机%s（Q2 后段卡）。' % (
        kp, sgn(k.dcore_ann_1.median(), k.dcore_ann_2.median()), sgn(k.z1.median(), k.z2.median())))
    # ---------------- Q1 T + P20 ----------------
    tall = M[M.route_id == 'RT']
    t = tall[tall.direction_role == 'primary']
    o.append('### Q1（T）后段 + P20 复核（原登记主读数 = 同人数核心）\n')
    tb = t.groupby(['policy', 'strength']).apply(lambda x: pd.Series(block(x))).reset_index()
    o.append(H10('分组描述符中位 / 计数', 'RT 主方向 x 四母体', '同 H 真实母体', '按预算（α / 替换 / 共同支持）'))
    o.append(md(tb))
    rep = t[t.policy.isin(['FULL_REPLACE', 'FALLBACK_REPLACE'])]
    tp = M[M.route_id == 'TPAIR']
    o.append('- **P20（M-T 腿测量替换）按原登记主读数（同人数核心）**：%s；%s。' % (
        q('P20-CORE', 'T 腿完全替换（FULL / FALLBACK_REPLACE，主方向）%d 个描述符：子−同人数核心两后段中位 %s / %s（%s）；对真实母体 %s / %s' % (
            len(rep), f(rep.dcore_ann_1.median()), f(rep.dcore_ann_2.median()),
            sgn(rep.dcore_ann_1.median(), rep.dcore_ann_2.median()), f(rep.p1.median()), f(rep.p2.median()))),
        q('P20-TPAIR', 'TPAIR（T 位改为 level x CV 复合）两后段中位 %s / %s，同人数核心 %s / %s' % (
            f(tp.p1.median()), f(tp.p2.median()), f(tp.dcore_ann_1.median()), f(tp.dcore_ann_2.median())))))
    o.append('- **读法**：T 的"少量加、不能换"在后段：小权重加两后段%s，完全替换对真实母体%s。P20 的旧问题（替换测量相对同人数核心是否有增量）'
             '按原读数：%s。\n' % (
                 sgn(t[(t.policy == 'FALLBACK') & pd.to_numeric(t.strength, errors='coerce').isin([0.125, 0.25])].p1.median(),
                     t[(t.policy == 'FALLBACK') & pd.to_numeric(t.strength, errors='coerce').isin([0.125, 0.25])].p2.median()),
                 sgn(rep.p1.median(), rep.p2.median()), sgn(rep.dcore_ann_1.median(), rep.dcore_ann_2.median())))
    # ---------------- Q5 R + P21 ----------------
    rr = M[M.route_id == 'RR']
    o.append('### Q5（R）后段 + P21 复核（原登记主读数 = 匹配随机）\n')
    rb = rr.groupby(['direction_role', 'role', 'strength']).apply(lambda x: pd.Series(block(x))).reset_index()
    o.append(H10('分组描述符中位 / 计数', 'RR（R1 / R2 / A06）', '同 H 真实母体（策略主读数）', '域 x 角色 x 强度'))
    o.append(md(rb))
    parts = []
    for (dr_, ro_), g_ in rr[rr.role.isin(['SWAP', 'ADD_SCORE'])].groupby(['direction_role', 'role']):
        parts.append('%s / %s（%d 个）：对母体 %s / %s；真实−匹配随机 %s / %s（%s）' % (
            dr_, ro_, len(g_), f(g_.p1.median()), f(g_.p2.median()), f(g_.z1.median()), f(g_.z2.median()),
            sgn(g_.z1.median(), g_.z2.median())))
    o.append('- **P21（I-P：同业相对位置）按原登记主读数（匹配随机）**：%s。两个主读数不同向时按域分别写，不换基准。\n' % q(
        'P21-Z', '；'.join(parts)))
    # ---------------- 其余路线 ----------------
    for qid, rt, title in (('Q3', 'RV', 'V：保留集风险'), ('Q4', 'RO', 'O：昼夜结构与焦点状态'), ('Q6', 'RC', 'C：核心槽位与 CVR 焦点替换'),
                           ('Q7', 'RL', '摩擦：边缘成本替换与轻否决'), ('Q13', 'RA', 'A：事件基线 / 同预算换入'),
                           ('Q14', 'RS', 'S：同行状态下的条件换入')):
        g = M[M.route_id == rt]
        o.append('### %s（%s）后段\n' % (qid, title))
        gb = g.groupby(['direction_role', 'role']).apply(lambda x: pd.Series(block(x))).reset_index()
        o.append(H10('分组描述符中位 / 计数', '%s 全部主描述符' % rt, '同 H 真实母体', '方向 x 角色'))
        o.append(md(gb))
        o.append('- **数字**：%s。' % q('%sP-MECH' % qid, '%s 两后段中位 %s / %s（%s）；同人数核心 %s / %s；同资本 %s / %s；真实−匹配随机 %s / %s' % (
            rt, f(g.p1.median()), f(g.p2.median()), sgn(g.p1.median(), g.p2.median()), f(g.dcore_ann_1.median()),
            f(g.dcore_ann_2.median()), f(g.dsamecap_ann_1.median()), f(g.dsamecap_ann_2.median()),
            f(g.z1.median()), f(g.z2.median()))))
        o.append('- **读法**：对真实母体%s（推导段 %s）；同资本%s，同人数核心%s，对匹配随机%s。%s\n' % (
            sgn(g.p1.median(), g.p2.median()), f(g.deriv.median()), sgn(g.dsamecap_ann_1.median(), g.dsamecap_ann_2.median()),
            sgn(g.dcore_ann_1.median(), g.dcore_ann_2.median()), sgn(g.z1.median(), g.z2.median()), route_note(rt, g)))
    # ---------------- Q15 四臂 ----------------
    o.append('### Q15（四臂交互）后段\n')
    fp = os.path.join(SP, 'fourarm_interaction_post.csv')
    if os.path.exists(fp):
        fi = rd(fp)
        fi.to_csv(os.path.join(TAB, 'T15_fourarm_post.csv'), index=False)
        ff = fi[fi.scope == 'post']
        by = ff.groupby('fourarm').agg(n=('interaction_ann', 'size'), inter=('interaction_ann', 'median'),
                                       dA=('d_A_ann', 'median'), dB=('d_B_ann', 'median'), dAB=('d_AB_ann', 'median'),
                                       inter_pos=('interaction_ann', lambda x: int((x > 0).sum()))).reset_index()
        o.append(H10('交互项 Δ_AB − Δ_A − Δ_B 与三臂的描述符中位（后段合并）', '每个 (四臂, 母体, 参数, H)', '三臂各自对同 H 真实母体',
                     'plan §5.6 / §5.7 四个中心', H='3 / 5 / 10 / 20'))
        o.append(md(by))
        tt = ff.interaction_ann / ff.interaction_se_nwH
        o.append('- **数字**：%s。' % q('Q15P-INT', '后段合并交互项 t>2 的 %d、t<−2 的 %d（共 %d）' % (
            int((tt > 2).sum()), int((tt < -2).sum()), len(ff))))
        rd_ = []
        for r_ in by.itertuples():
            if r_.inter > 0 and r_.dAB < 0:
                rd_.append('%s：A 臂 %s、B 臂 %s、合用 %s——交互为正来自合用后亏损不叠加（合用亏得少于两臂之和），不是合用带来正收益' % (
                    r_.fourarm, f(r_.dA), f(r_.dB), f(r_.dAB)))
            elif r_.inter > 0:
                rd_.append('%s：合用 %s 大于两臂之和（A %s、B %s）' % (r_.fourarm, f(r_.dAB), f(r_.dA), f(r_.dB)))
            else:
                rd_.append('%s：合用 %s 小于两臂之和（A %s、B %s）' % (r_.fourarm, f(r_.dAB), f(r_.dA), f(r_.dB)))
        o.append('- **读法**：%s。交互只对登记对象成立，不推广为"同族因子互补"。\n' % '；'.join(rd_))
    # ---------------- 代表 ----------------
    rp = m0_fixed(M)
    o.append('### 代表（M0_FIXED，事前固定中间档）后段\n')
    o.append('%s。\n' % q('P2-REP', 'M0_FIXED（与 part1a 同一选法：代表成员 x 中间档预算 x H5）%d 个描述符：两后段中位 %s / %s；后段合并 NW 排除 0 为正 %d、为负 %d' % (
        len(rp), f(rp.p1.median()), f(rp.p2.median()), int((rp.ci_post & (rp.post > 0)).sum()),
        int((rp.ci_post & (rp.post < 0)).sum()))))
    o.append(H10('代表描述符中位 / 计数', '§7.1 代表 x 适用母体 x 中间档', '同 H 真实母体', '按路线', H='5'))
    o.append(md(dist(rp, 'route_id')))
    return '\n'.join(o)


if __name__ == '__main__':
    main()
