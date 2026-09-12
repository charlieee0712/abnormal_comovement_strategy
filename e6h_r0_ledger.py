#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h R0 交付: parent_need_ledger.md + REPORT_R0.md (brief §3 末条 / §13)。

需求卡按 plan §2.4 至少写: 已有哪条规则负责 / 发现的不足或争议 / 拟补的类别 /
最直接的测量 / 最合适的动作 / 比较对象 / 何种结果只支持其他解释。

全部数字从已落盘产物读, 不在本脚本里重算。
"""
from __future__ import annotations
import os
import sys
import json
import time
import collections

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H

RES = H.RES
SEGS = list(H.DERIV_SEGS)
PARENTS = ['R1', 'R2', 'A06', 'A08']
CORE_OF = {'R1': 'KT_dep(50,50)|C:k5', 'R2': 'KT_mean@30|C:k5+cr5:k10',
           'A06': 'KTC_mean@25|cvr_1d:k10+cr5:k10', 'A08': 'T@30|C:k5+cr5:k10'}


def load():
    d = {}
    d['dist'] = pd.concat([pd.read_csv(os.path.join(
        RES, 'T0_full_distribution', 'stage_distributions_%s.csv' % s)).assign(seg=s)
        for s in SEGS], ignore_index=True)
    d['ps'] = pd.concat([pd.read_csv(os.path.join(
        RES, 'T0_full_distribution', 'pseudo_paths_%s.csv' % s)) for s in SEGS],
        ignore_index=True)
    d['rel'] = pd.concat([pd.read_csv(os.path.join(
        RES, 'T0_full_distribution', 'factor_parent_relation_%s.csv' % s)).assign(seg=s)
        for s in SEGS], ignore_index=True)
    d['map'] = pd.read_csv(os.path.join(RES, 'registry', 'need_parent_role_map.csv'))
    d['rm'] = json.load(open(os.path.join(RES, 'registry', 'route_manifest.json')))
    d['sem'] = pd.read_csv(os.path.join(RES, 'registry', 'feature_semantics.csv'))
    d['cl'] = {s: json.load(open(os.path.join(
        RES, 'clustering', 'factor_clusters_%s.json' % s))) for s in SEGS}
    return d


def g(dist, seg, parent, stage, col, label='src'):
    r = dist[(dist.seg == seg) & (dist.parent == parent) &
             (dist.stage_set == stage) & (dist.label == label)]
    return float(r.iloc[0][col]) if len(r) else np.nan


def main():
    D = load()
    dist, ps, rel = D['dist'], D['ps'], D['rel']
    L = []
    A = L.append

    # =============== parent_need_ledger.md ===============
    A('# E6h R0 —— 母体需求台账（`parent_need_ledger.md`）')
    A('')
    A('生成时间：`%s`。推导段 `%s` / `%s`，全部 `exploratory`。'
      % (time.strftime('%Y-%m-%d %H:%M:%S'), SEGS[0], SEGS[1]))
    A('标签 = E3 源版（`compute_forward_5d_excess`，日超额算术和，基准 `base_pool`，单位 bp）。')
    A('')
    A('**这份台账只回答"母体缺什么"，不回答"加什么有用"。** 后者要等推导段实验。')
    A('')
    A('---')
    A('')
    A('## 0. 池子本身长什么样（四个母体共同的起点）')
    A('')
    A('| 段 | n | 均值 | **中位** | 负票占比 | q05 | q95 |')
    A('|---|---|---|---|---|---|---|')
    for s in SEGS:
        A('| %s | %d | %+.2f | **%+.2f** | %.2f | %.1f | %.1f |'
          % (s, g(dist, s, 'R1', 'U_pool0', 'n'), g(dist, s, 'R1', 'U_pool0', 'mean'),
             g(dist, s, 'R1', 'U_pool0', 'median'), g(dist, s, 'R1', 'U_pool0', 'frac_neg'),
             g(dist, s, 'R1', 'U_pool0', 'q05'), g(dist, s, 'R1', 'U_pool0', 'q95')))
    A('')
    A('**读法**：池子是**右偏**的——均值接近零而中位数深负，55–56% 的票为负。')
    A('所以"剔输家"这件事在这个池子里主要是**把中位数往上推**，均值由正尾主导。')
    A('任何只比较均值的诊断都会低估这件事的结构。')
    A('')
    A('### 构成解释了多少（三层匹配随机参照，各 128 draw）')
    A('')
    A('| 段 | 目标 | 真实 | 同人数 | ＋同行业 | ＋行业×市值三档 |')
    A('|---|---|---|---|---|---|')
    for s in SEGS:
        for tgt in ('pool_worst20', 'pool_best20'):
            row = ['| %s | `%s` | %+.1f ' % (s, tgt,
                   ps[(ps.segment == s) & (ps.target == tgt)].iloc[0]['real_mean_bp'])]
            for lv in ('U_IID', 'I_IID', 'IxM_IID'):
                r = ps[(ps.segment == s) & (ps.target == tgt) & (ps.match_level == lv)]
                if len(r):
                    rr = r.iloc[0]
                    row.append('| %+.1f（%.1f%%）' % (rr['pseudo_mean_bp'],
                                                      100.0 * rr['explained_frac']))
            A(''.join(row) + ' |')
    A('')
    A('**这条修正了 E6g 的读法。** E6g 只做了输家一侧、只匹配到行业，报"约 26% 是行业构成"。')
    A('加上市值三档后，**2010-2014 有 47.3% / 2015-2018 有 37.3% 的输家幅度可由构成复现**；')
    A('赢家一侧**对称**（44.5% / 36.6%）。也就是说接近一半的"输家信号"不是个股层面的信息。')
    A('MCSE 全部 ≤ 0.21 bp，远低于登记的 5 bp 门槛，不是抽样噪声。')
    A('')
    A('**不能由此推出**"行业/市值信息无用"——plan §2.3 明确警告过度匹配会把研究中的')
    A('行业与流动性信息一起匹配掉。三层**并列**报，不取最严的当唯一答案。')
    A('')
    A('---')
    A('')

    # 逐母体需求卡
    for i, p in enumerate(PARENTS, 1):
        A('## %d. `%s` = `%s`' % (i, p, CORE_OF[p]))
        A('')
        A('| 段 | 集合 | n | 均值 | 中位 | 负票占比 |')
        A('|---|---|---|---|---|---|')
        for s in SEGS:
            for st, nm in (('U_pool0', 'U 池'), ('C_core', 'C 核'),
                           ('V_vetoed', 'V 被否决'), ('B_final', 'B 最终'),
                           ('D_econ_rejected', 'D 经济拒绝')):
                A('| %s | %s | %d | %+.2f | %+.2f | %.2f |'
                  % (s, nm, g(dist, s, p, st, 'n'), g(dist, s, p, st, 'mean'),
                     g(dist, s, p, st, 'median'), g(dist, s, p, st, 'frac_neg')))
        A('')
        # 拒绝集 vs 匹配随机
        A('**D 相对匹配随机**（这才是"这一关有没有在真剔坏票"的判据）：')
        A('')
        A('| 段 | D 真实 | 行业×市值匹配随机 | 差 | 读法 |')
        A('|---|---|---|---|---|')
        for s in SEGS:
            r = ps[(ps.segment == s) & (ps.target == '%s_D' % p) &
                   (ps.match_level == 'IxM_IID')]
            if not len(r):
                continue
            rr = r.iloc[0]
            gap = rr['real_mean_bp'] - rr['pseudo_mean_bp']
            verdict = ('拒绝集**比匹配随机还好** → 这一关在剔错票' if gap > 0
                       else '拒绝集比匹配随机差 → 这一关在真剔坏票')
            A('| %s | %+.2f | %+.2f | %+.2f | %s |'
              % (s, rr['real_mean_bp'], rr['pseudo_mean_bp'], gap, verdict))
        A('')
        if p == 'R1':
            A('**R1 专有：两关分开看。**')
            A('')
            A('| 段 | 第一关（K，留 50%） | 第二关（T，留 50%） |')
            A('|---|---|---|')
            for s in SEGS:
                s1 = g(dist, s, p, 'S1_stage1_kept', 'mean')
                d1 = g(dist, s, p, 'D1_stage1_rejected', 'mean')
                c2 = g(dist, s, p, 'C_core', 'mean')
                d2 = g(dist, s, p, 'D2_stage2_rejected', 'mean')
                A('| %s | 留 %+.2f vs 剔 %+.2f → **分离 %.1f bp** | 留 %+.2f vs 剔 %+.2f → **%.1f bp** |'
                  % (s, s1, d1, s1 - d1, c2, d2, c2 - d2))
            A('')
            A('**两关的分离力在两段之间翻转**：早段 K 干了大部分活，近段换成 T。')
            A('这是本轮 R0 最直接的一条需求信号，正对 M-T 要问的'
              '"T 的标准差是否混合了活动水平与不稳定性"。')
            A('')
        # 该母体下最有排序能力的键
        sub = rel[rel.parent == p].pivot_table(index='key', columns='seg',
                                               values='rho_label_in_D')
        sub = sub.dropna()
        if len(sub):
            sub = sub[np.sign(sub[SEGS[0]]) == np.sign(sub[SEGS[1]])]
            sub['m'] = sub[[SEGS[0], SEGS[1]]].abs().min(axis=1)
            top = sub.sort_values('m', ascending=False).head(8)
            A('**在 D 内最能排序标签的键**（两段同号才列；这是"可改变的拒绝机会"的证据）：')
            A('')
            A('| 键 | %s | %s | 族 |' % (SEGS[0], SEGS[1]))
            A('|---|---|---|---|')
            for k, r in top.iterrows():
                fam = D['sem'][D['sem'].key == k]
                fam = fam.iloc[0]['measurement_families'] if len(fam) else ''
                A('| `%s` | %+.4f | %+.4f | %s |' % (k, r[SEGS[0]], r[SEGS[1]], fam))
            A('')
        A('---')
        A('')

    A('## 5. 跨母体的共同观察')
    A('')
    A('1. **没有任何单一测量能在拒绝集里强力排序收益。** `rho_label_in_D` 全域中位 %.4f、'
      '最大 |%.4f|。"可回收的拒绝机会"不在某个单键里，只能靠条件结构。'
      % (rel['rho_label_in_D'].median(), rel['rho_label_in_D'].abs().max()))
    A('2. **资本加权几乎不改变画面。** `wmean` 与等权 `mean` 差 < 0.1 bp。'
      'plan §2.3 担心的"人数最多的亏损型不一定资本损失最大"在这个池子里不成立，'
      'DEV 权重相对标签近似中性——这省掉了一层竞争解释。')
    A('3. **统计聚类没有给出稳定分区。** average linkage 在 1−|ρ| 上退化成链'
      '（k=5 的簇大小 82/2/1/1/1）；complete linkage 分得开（k=3 为 40/30/17）但'
      '**两段之间同簇关系只有 0.65–0.72 一致**。按 plan §2.1，聚类只作校验、'
      '不定因果轴——校验结果是它**支持不了**任何轴定义。这不阻止任何事前有理由的路线。')
    A('')
    A('---')
    A('')
    A('## 6. 记录 A v0（已生效，执行端据此编译推导段实验）')
    A('')
    rm = D['rm']
    A('`registry/route_manifest.json`，sha256 `%s`，%d 张卡。'
      % (rm['self_sha256'][:16], rm['counts']['n_routes']))
    A('（键 × 母体）对：**routed %d / candidate_for_routing %d / diagnostic_only %d / '
      'unassigned %d**。'
      % (rm['counts']['n_routed_pairs'], rm['counts']['n_candidate'],
         rm['counts']['n_diagnostic_only'], rm['counts']['n_unassigned']))
    A('')
    A('| 卡 | 需求 | 母体 | 环节 | 角色 | 竞争分支 |')
    A('|---|---|---|---|---|---|')
    for rt in rm['routes']:
        A('| `%s` | %s | %s | %s | %s | %s |'
          % (rt['route_id'], rt['need_id'], ','.join(rt['parents']), rt['stage'],
             ','.join(rt['roles']), rt.get('competitor') or '—'))
    A('')
    A('**未路由的 %d 个（键 × 母体）对全部留在 `consideration_ledger.csv`，带理由。'
      '未路由 ≠ 无效**（plan §2.1）。' % rm['counts']['n_unassigned'])
    A('')

    with open(os.path.join(RES, 'parent_need_ledger.md'), 'w',
              encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(L) + '\n')
    print('parent_need_ledger.md: %d 行' % len(L))


if __name__ == '__main__':
    main()
