#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i REPORT_part1 (1a) 表格生成器 (brief §6 / §14 / §15; plan §8)。只读 statistics/ 与 accounts/ 产物。

输出 reports/part1_tables/*.csv 与 reports/E6i_REPORT_part1_tables.md (全部表, 每表十项表头);
叙述 (Q 卡) 由 e6i_report_part1_text.py 在读过这些表之后写。
代表配置 (M0_FIXED 头表) 事前固定 = 与 M2 规格相同的中间档预算 + 主方向 + H5, 不按结果挑。"""
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
OUT = os.path.join(R, 'reports')
TAB = os.path.join(OUT, 'part1_tables')
SEGS = list(I.DERIV_SEGS)
SC = SEGS + ['full']
REQ = ('汇总算子', '分母及构成', '基准', '子集', '单位', '日期支持', 'H', '成本', '支持口径', '资本口径')
MID = {'SLOT': ('0.25', 'FALLBACK'), 'COMMON_SUPPORT': ('0.25', 'COMMON_SUPPORT'), 'VETO_NEW': ('10', None),
       'SOFT': ('0.5', None), 'SOFT_HARD': ('10', None), 'ADD_SCORE': ('0.125', None), 'SWAP': ('0.1', None),
       'T_PAIR': ('0.5', None), 'RL': ('edge_replace', None)}
PRIMARY_DR = ('primary', 'primary_inverse_mapped', 'reversal_domain', 'continuation_domain', 'high_role',
              'low_role', 'P30', 'P70', 'pos', 'neg')


def a0_version():
    vs = [int(m.group(1)) for m in (re.search(r'A0_amendment_v1_(\d+)\.md$', x) for x in
                                    glob.glob(os.path.join(R, 'registry', 'A0_amendment_v1_*.md'))) if m]
    return 'v1.%d' % max(vs) if vs else 'v1.0'


def ss(s):
    return s if s == 'full' else s[2:4] + '-' + s[-2:]


def hdr(op, denom, bench, subset, unit='年化百分点（日均 x 252 x 100）', dates='推导两段（2010-01-04..2014-12-31 / '
        '2015-01-05..2018-12-28）；full = 两段按有效日合并', H='见列', cost='8bp 主口径（net12 另列）',
        support='各段有效日（缺测日不拼接）', capital='源 DEV（原生）'):
    return ('> **汇总算子**：%s ｜ **分母及构成**：%s ｜ **基准**：%s ｜ **子集**：%s ｜ **单位**：%s ｜ '
            '**日期支持**：%s ｜ **H**：%s ｜ **成本**：%s ｜ **支持口径**：%s ｜ **资本口径**：%s\n'
            % (op, denom, bench, subset, unit, dates, H, cost, support, capital))


def md(df, nd=3):
    if df is None or not len(df):
        return '_（无数据）_\n'
    d = df.copy()
    d.columns = [' / '.join(str(x) for x in c if str(x) != '') if isinstance(c, tuple) else str(c)
                 for c in d.columns]
    for c in d.columns:
        if d[c].dtype.kind == 'f':
            d[c] = d[c].map(lambda v: ('%.*f' % (nd, v)) if np.isfinite(v) else '—')
    cols = list(d.columns)
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, r in d.iterrows():
        out.append('| ' + ' | '.join(str(r[c]) for c in cols) + ' |')
    return '\n'.join(out) + '\n'


def save(name, df):
    os.makedirs(TAB, exist_ok=True)
    df.to_csv(os.path.join(TAB, name + '.csv'), index=False)


def load_stats():
    d = {s: pd.read_csv(os.path.join(ST, 'descriptor_stats_%s.csv' % s), low_memory=False) for s in SC}
    return d


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    st = load_stats()
    L = []
    w = L.append
    base = st['full'][['descriptor_id', 'route_id', 'mother_id', 'member_id', 'role', 'strength', 'policy',
                       'direction', 'direction_role', 'H', 'representative', 'axis']].copy()
    for s in SC:
        x = st[s].set_index('descriptor_id')
        base['d_%s' % ss(s)] = base.descriptor_id.map(x.d_net8_ann)
        base['se_%s' % ss(s)] = base.descriptor_id.map(x.se_nwH)
        base['state_%s' % ss(s)] = base.descriptor_id.map(x.state_word)
        base['cix0_%s' % ss(s)] = base.descriptor_id.map(x.ci_excludes_zero)
        if 'band_domain_lo' in x:
            base['bdlo_%s' % ss(s)] = base.descriptor_id.map(x.band_domain_lo)
            base['bdhi_%s' % ss(s)] = base.descriptor_id.map(x.band_domain_hi)
    for s in SEGS:
        x = st[s].set_index('descriptor_id')
        for c in ('d_vs_core_matchN', 'd_same_capital', 'd_vs_reverse_matchN', 'd_gross_ann', 'd_turn', 'd_pos',
                  'attr_added_ann', 'attr_removed_ann', 'attr_common_ann', 'dcore_ann', 'dcore_se_nwH'):
            if c in x:
                base['%s_%s' % (c, ss(s))] = base.descriptor_id.map(x[c])
    comp = base.descriptor_id.str.contains(r'\|(eqcap|cost_target|winsor)$')
    base['companion'] = comp
    save('descriptor_panel', base)
    main_ = base[~comp & ~base.route_id.isin(['M1', 'M2'])]

    # ---------------- 表 1: need 域分布 ----------------
    rows = []
    for (rt, mo), g in main_.groupby(['route_id', 'mother_id']):
        rec = dict(route=rt, mother=mo, n=len(g))
        for s in SC:
            x = g['d_%s' % ss(s)]
            rec['%s 中位' % ss(s)] = x.median()
            rec['%s p10' % ss(s)] = x.quantile(0.1)
            rec['%s p90' % ss(s)] = x.quantile(0.9)
            rec['%s 正值占比' % ss(s)] = (x > 0).mean()
        rows.append(rec)
    t1 = pd.DataFrame(rows)
    save('T1_domain_distribution', t1)
    rows = []
    for (rt, mo), g in main_.groupby(['route_id', 'mother_id']):
        rec = dict(route=rt, mother=mo, n=len(g))
        for s in ('full',):
            x, se = g['d_%s' % s], g['se_%s' % s]
            ci = g['cix0_%s' % s].astype(bool)
            rec['CI 排除 0 且 >0'] = int((ci & (x > 0)).sum())
            rec['CI 排除 0 且 <0'] = int((ci & (x < 0)).sum())
            if 'bdlo_full' in g:
                rec['域同步带 >0'] = int((g.bdlo_full > 0).sum())
                rec['域同步带 <0'] = int((g.bdhi_full < 0).sum())
            vc = g['state_%s' % s].value_counts()
            for k in ('positive_estimate_uncertain', 'negative_estimate_uncertain',
                      'materially_small_under_declared_delta', 'inconclusive'):
                rec[k] = int(vc.get(k, 0))
            rec['SE 中位'] = se.median()
            rec['MDE80 中位'] = (2.8 * se).median()
        rec['两段同号占比'] = float((np.sign(g['d_10-14']) == np.sign(g['d_15-18'])).mean())
        rows.append(rec)
    t1b = pd.DataFrame(rows)
    save('T1b_domain_evidence_full', t1b)

    # ---------------- 表 2: 机制 (sameN / 同资本 / Z-MAP / 归因) ----------------
    zs = []
    for s in SEGS:
        f = os.path.join(ST, 'zmap_summary_%s.csv' % s)
        if os.path.exists(f):
            z = pd.read_csv(f, low_memory=False)
            z['seg'] = ss(s)
            zs.append(z)
    zm = pd.concat(zs, ignore_index=True) if zs else pd.DataFrame()
    rows = []
    for rt, g in main_.groupby('route_id'):
        rec = dict(route=rt, n=len(g))
        for s in SEGS:
            k = ss(s)
            rec['%s 子−母 中位' % k] = g['d_%s' % k].median()
            if 'd_vs_core_matchN_%s' % k in g:
                rec['%s 子−同人数核心 中位' % k] = g['d_vs_core_matchN_%s' % k].median()
                rec['%s 同资本差 中位' % k] = g['d_same_capital_%s' % k].median()
                rec['%s Δgross 中位' % k] = g['d_gross_ann_%s' % k].median()
                rec['%s Δturn 中位' % k] = g['d_turn_%s' % k].median()
            if len(zm):
                zz = zm[(zm.seg == k) & (zm.route_id == rt) & (zm.kind == 'basic')]
                if len(zz):
                    rec['%s 真实−随机(basic) 中位' % k] = zz.d_real_minus_rand.median()
                    rec['%s tail<0.05 占比' % k] = float((zz.diagnostic_tail_fraction < 0.05).mean())
        rows.append(rec)
    t2 = pd.DataFrame(rows)
    save('T2_mechanism_by_route', t2)
    if len(zm):
        zk = zm[zm.kind.isin(['basic', 'industry', 'persist20'])].groupby(['seg', 'route_id', 'kind']).agg(
            n=('descriptor_id', 'size'), d_med=('d_real_minus_rand', 'median'),
            share_pos=('d_real_minus_rand', lambda x: float((x > 0).mean())),
            tail05=('diagnostic_tail_fraction', lambda x: float((x < 0.05).mean())),
            mcse_med=('rand_net8_mcse', 'median'), mcse_max=('rand_net8_mcse', 'max')).reset_index()
        save('T2b_zmap_by_route_kind', zk)
    else:
        zk = pd.DataFrame()

    # ---------------- 表 3: 强度 / H 曲线 ----------------
    sc = main_.groupby(['route_id', 'role', 'strength']).agg(
        n=('descriptor_id', 'size'), **{('%s 中位' % ss(s)): ('d_%s' % ss(s), 'median') for s in SC}).reset_index()
    save('T3_strength_curve', sc)
    hc = main_.groupby(['route_id', 'H']).agg(
        n=('descriptor_id', 'size'), **{('%s 中位' % ss(s)): ('d_%s' % ss(s), 'median') for s in SC}).reset_index()
    save('T3b_H_curve', hc)

    # ---------------- 表 4: 代表 (M0_FIXED 头表) ----------------
    rep = main_[main_.representative.astype(str).isin(['True', 'true', '1'])].copy()
    keep = []
    for i, r in rep.iterrows():
        m = MID.get(r.role)
        if m is None or int(r.H) != 5:
            continue
        if str(r.strength) != m[0] and not (m[0] == 'edge_replace' and str(r.strength) == 'edge_replace'):
            try:
                if abs(float(r.strength) - float(m[0])) > 1e-9:
                    continue
            except ValueError:
                continue
        if m[1] is not None and str(r.policy) != m[1]:
            continue
        keep.append(i)
    rp = rep.loc[keep]
    rcols = ['route_id', 'mother_id', 'member_id', 'role', 'strength', 'direction', 'direction_role',
             'd_10-14', 'd_15-18', 'd_full', 'se_full', 'state_full']
    if 'bdlo_full' in rp:
        rcols += ['bdlo_full', 'bdhi_full']
    for k in ('10-14', '15-18'):
        if 'd_vs_core_matchN_%s' % k in rp:
            rcols.append('d_vs_core_matchN_%s' % k)
    rp = rp[rcols].sort_values(['route_id', 'mother_id', 'member_id', 'direction'])
    if len(zm):
        zb = zm[zm.kind == 'basic'].set_index(['seg', 'descriptor_id'])
        for k in ('10-14', '15-18'):
            ids = rep.loc[keep].descriptor_id
            rp['zmap_basic_%s' % k] = [zb.d_real_minus_rand.get((k, d), np.nan) for d in ids.loc[rp.index]]
    save('T4_representatives_M0_fixed', rp)

    # ---------------- 表 5: 四臂 ----------------
    fi = pd.read_csv(os.path.join(ST, 'fourarm_interaction.csv')) if os.path.exists(
        os.path.join(ST, 'fourarm_interaction.csv')) else pd.DataFrame()
    save('T5_fourarm_interaction', fi)

    # ---------------- 表 6: M1 ----------------
    m1 = base[base.route_id == 'M1'].copy()
    if len(m1):
        m1['variant'] = np.where(m1.descriptor_id.str.endswith('|eqcap'), 'eqcap_merge', 'consensus')
        m1s = m1.groupby(['variant', 'strength', 'H']).agg(
            n=('descriptor_id', 'size'), **{('%s 中位' % ss(s)): ('d_%s' % ss(s), 'median') for s in SC},
            **{('%s 正值占比' % ss(s)): ('d_%s' % ss(s), lambda x: float((x > 0).mean())) for s in SC}).reset_index()
        save('T6_M1_summary', m1s)
    else:
        m1s = pd.DataFrame()

    # ---------------- 表 7: 逐年 ----------------
    yr = []
    for s in SEGS:
        x = st[s]
        ycols = [c for c in x.columns if re.fullmatch(r'y\d{4}', c)]
        g = x[~x.descriptor_id.str.contains(r'\|(eqcap|cost_target|winsor)$')].merge(
            base[['descriptor_id', 'route_id']], on='descriptor_id', how='left', suffixes=('', '_b'))
        rc = 'route_id' if 'route_id' in g else 'route_id_b'
        yy = g.groupby(rc)[ycols].median()
        yr.append(yy)
    yrt = pd.concat(yr, axis=1).reset_index()
    save('T7_yearly_median_by_route', yrt)

    # ---------------- 写 markdown 表集 ----------------
    w('# E6i REPORT_part1 表集（1a；自动生成，叙述另见 E6i_REPORT_part1.md）\n')
    w('## T1 need 域分布（子账户 − 同 H 母体，逐日配对 net8）\n')
    w(hdr('每个 (路线, 母体) 内全部非伴随描述符的点估分布', '该 need 域的全部描述符（成员 x 方向 x 强度 x H）',
          '同 H 母体（源 DEV / 源 8bp）', 'A0 %s 全部主路线' % a0_version()))
    w(md(t1))
    w(hdr('计数与中位', '同上', '同 H 母体；NW(lag H) 95% 区间与 need 域同步带（2,000 次 stationary bootstrap，块 20）',
          'full = 两段按有效日合并', unit='计数 / 年化百分点'))
    w(md(t1b))
    w('## T2 机制读数（按路线）\n')
    w(hdr('描述符中位', '该路线全部描述符', '子−母 / 子−同人数核心 / 同资本 / 真实−随机均值（Z-MAP basic）',
          '两推导段分列'))
    w(md(t2))
    if len(zk):
        w(hdr('(描述符 x 机制) 行的中位 / 占比 / MCSE', '该路线全部有 Z-MAP 的配置 x H', 'Z-MAP 路径均值',
              '三类随机机制', H='见行'))
        w(md(zk))
    w('## T3 强度与 H 曲线\n')
    w(hdr('描述符中位', '(路线, 角色, 强度) 或 (路线, H) 内全部描述符', '同 H 母体', '主路线'))
    w(md(sc))
    w(hdr('描述符中位', '(路线, H) 内全部描述符', '同 H 母体', '主路线'))
    w(md(hc))
    w('## T4 代表（M0_FIXED 头表：事前固定的中间档预算、主方向、H5）\n')
    w(hdr('单描述符点估 / NW 区间 / 同步带 / 状态词', '单描述符', '同 H 母体；同人数核心；Z-MAP basic 路径均值',
          '§7.1 代表 x 适用母体 x 中间档', H='5'))
    w(md(rp))
    w('## T5 四臂交互（Δ_AB − Δ_A − Δ_B，逐日配对）\n')
    w(hdr('交互项年化均值与 NW(lag H) 标准误', '每个 (四臂, 母体, 参数, H)', '同 H 母体（三臂各自 − 母体）',
          'plan §5.6 / §5.7 四个中心'))
    w(md(fi))
    if len(m1s):
        w('## T6 M1（共识 / 等资本合并）\n')
        w(hdr('描述符中位 / 正值占比', '(变体, η, H) 内全部 M1 程序', '同 H 母体', 'A0 M1 1,512 程序 + 等资本伴随'))
        w(md(m1s))
    w('## T7 逐年（描述符中位）\n')
    w(hdr('逐年年化均值的描述符中位', '该路线全部描述符', '同 H 母体', '推导段逐年', H='各描述符自身 H'))
    w(md(yrt))
    txt = '\n'.join(L)
    p = os.path.join(OUT, 'E6i_REPORT_part1_tables.md')
    open(p, 'w', encoding='utf-8').write(txt)
    print('part1 表集: %s (%d 字节); %.0fs' % (p, len(txt.encode()), time.time() - t0))


if __name__ == '__main__':
    main()
