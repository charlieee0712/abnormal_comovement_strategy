#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 4: research_catalog_v36.csv + factor_iteration_delta.md (brief §9; plan §12.3 / §12.4)。
在 part2 之后运行 (读 reports/part2_tables/descriptor_panel_post.csv)。
research_catalog_v36: 每个已考虑成员 (276 个目录成员 + 考虑过未构造的项) 一行 —— 来源 / 定义 / 有效域 / 尝试 / 未测用途,
  不只存"通过者"; 推导段与后段读数只作描述 (主方向单成员描述符的中位), 不作准入。
factor_iteration_delta: 每成员一行 —— 构造版本 / 角色证据 / 失效归因 (五选: measurement / role / capital / time / precision,
  可多选, 各附证据数字) / 状态。归因是【执行端规则化初判】(规则写在文件头), 供规划 session 更新因子迭代台账时复核, 不是定案。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import json
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I

R = I.RES
EPS = 0.05
MAIN = ('RT', 'RK', 'RV', 'RR', 'RO', 'RC', 'RA', 'RS', 'RL')
PRIM = ('primary', 'primary_inverse_mapped', 'high_role', 'reversal_domain')
ALL_ROLES = ('SLOT', 'COMMON_SUPPORT', 'ADD_SCORE', 'VETO_NEW', 'SOFT', 'SOFT_HARD', 'SWAP', 'FOCAL_NEW', 'RL', 'M1', 'M2')


def fmt(x):
    return ('%+.3f' % x) if np.isfinite(x) else 'NA'


def main():
    t0 = time.time()
    sem = pd.read_csv(os.path.join(R, 'registry', 'feature_semantics_v2.csv'))
    led = pd.read_csv(os.path.join(R, 'reports', 'consideration_ledger_E6i.csv')).set_index('member_id')
    notb = pd.read_csv(os.path.join(R, 'reports', 'consideration_ledger_E6i_C_not_built.csv'))
    P = pd.read_csv(os.path.join(R, 'reports', 'part2_tables', 'descriptor_panel_post.csv'), low_memory=False)
    a0 = pd.read_csv(os.path.join(R, 'registry', 'descriptors_A0.csv'), low_memory=False)
    appr_mem = set(json.load(open(I.APPROVAL_FILE))['approved_members'])
    zdv, scd = {}, {}
    for s in I.DERIV_SEGS:
        z = pd.read_csv(os.path.join(R, 'statistics', 'zmap_summary_%s.csv' % s), low_memory=False)
        zdv[s] = z[z.kind == 'basic'].set_index('descriptor_id').d_real_minus_rand
        ds = pd.read_csv(os.path.join(R, 'statistics', 'descriptor_stats_%s.csv' % s), low_memory=False)
        scd[s] = ds.set_index('descriptor_id').d_same_capital
    P['zd'] = (P.descriptor_id.map(zdv[I.DERIV_SEGS[0]]) + P.descriptor_id.map(zdv[I.DERIV_SEGS[1]])) / 2.0
    P['samecap_d'] = (P.descriptor_id.map(scd[I.DERIV_SEGS[0]]) + P.descriptor_id.map(scd[I.DERIV_SEGS[1]])) / 2.0
    single = P[P.route_id.isin(MAIN) & ~P.companion.astype(bool)].copy()
    single = single[~single.member_id.astype(str).str.contains(r'[|+]')]
    rows, drows = [], []
    for r in sem.itertuples():
        mid = r.member_id
        g_all = single[single.member_id == mid]
        g = g_all[g_all.direction_role.isin(PRIM)]
        a0m = a0[a0.member_id.astype(str).str.split(r'[|+]').apply(lambda xs, m=mid: m in xs)]
        roles = sorted(set(a0m.role.astype(str)))
        rec = dict(member_id=mid, axis=r.axis_id, family=r.family_id, estimand=r.estimand_id,
                   source_class=r.source_class, formula_version=r.formula_version, raw_fields=r.raw_fields,
                   unit=r.unit, window=r.window, min_obs=r.min_obs, price_policy=r.price_policy,
                   one_word_policy=r.one_word_policy, missing_policy=r.missing_policy, event_clock=r.event_clock,
                   neutralize_scope=r.neutralize_scope, transform_order=r.transform_order,
                   direction_primary=r.direction_primary, direction_competing=r.direction_competing,
                   source_ref=r.source_ref, executable_status=r.executable_status,
                   ledger_status=led.status.get(mid, 'not_in_ledger'),
                   valid_domain=('推导段 2010-2018 + 后段 2019-2026（记录 B 批准）' if mid in appr_mem else
                                 ('推导段 2010-2018 + 后段（源键，不受保护）' if r.source_class == 'LEGACY' else
                                  '仅推导段 2010-2018（未进任何需求域包，后段未解封）')),
                   n_descriptors_A0=len(a0m), routes=('|'.join(sorted(set(a0m.route_id.astype(str)))) or ''),
                   roles_tested=('|'.join(roles) or ''),
                   untested_roles='|'.join(x for x in ALL_ROLES if x not in roles),
                   mothers=('|'.join(sorted(set(a0m.mother_id.astype(str)))) or ''),
                   n_primary_single=len(g), deriv_median=g.deriv.median(), post_median=g.post.median(),
                   all4_median=g.all4.median(), deriv_share_pos=(g.deriv > 0).mean() if len(g) else np.nan,
                   post_share_pos=(g.post > 0).mean() if len(g) else np.nan,
                   post_ci_pos=int((g.ci_post.astype(bool) & (g.post > 0)).sum()),
                   post_ci_neg=int((g.ci_post.astype(bool) & (g.post < 0)).sum()),
                   zmap_deriv_median=g.zd.median(), zmap_post_median=((g.z1 + g.z2) / 2.0).median(),
                   core_post_median=((g.dcore_ann_1 + g.dcore_ann_2) / 2.0).median())
        if len(g):
            br = g.groupby('role').deriv.median()
            bp = g.groupby('role').post.median()
            rec['best_role_deriv'] = '%s %s' % (br.idxmax(), fmt(br.max()))
            rec['best_role_post'] = '%s %s' % (bp.idxmax(), fmt(bp.max())) if bp.notna().any() else ''
        rows.append(rec)
        # ---------- 因子迭代增量 (执行端初判) ----------
        d_, p_ = rec['deriv_median'], rec['post_median']
        if not len(g):
            status, attr = ('untested_single_role' if len(a0m) else 'measured_only'), []
        else:
            if d_ > EPS and p_ > EPS:
                status = 'positive_deriv_and_post'
            elif d_ > EPS:
                status = 'positive_deriv_only'
            elif p_ > EPS:
                status = 'positive_post_only'
            elif abs(d_) <= EPS and abs(p_) <= EPS:
                status = 'near_zero_both'
            else:
                status = 'negative_or_mixed'
            attr = []
            sc = g.samecap_d.median()
            zd = rec['zmap_deriv_median']
            mde = g.mde_post.median() if 'mde_post' in g else np.nan
            if status != 'positive_deriv_and_post':
                if d_ < -EPS and np.isfinite(sc) and sc > 0:
                    attr.append('capital（对母体 %s，同资本 %s）' % (fmt(d_), fmt(sc)))
                if d_ < -EPS and np.isfinite(zd) and zd > 0:
                    attr.append('role（对母体 %s，但对匹配随机 %s：方向有信息、角色 / 预算不合适）' % (fmt(d_), fmt(zd)))
                if d_ < -EPS and np.isfinite(zd) and zd <= 0:
                    attr.append('measurement（对母体 %s，对匹配随机 %s）' % (fmt(d_), fmt(zd)))
                if d_ > EPS and np.isfinite(p_) and p_ < -EPS:
                    attr.append('time（推导 %s → 后段 %s）' % (fmt(d_), fmt(p_)))
                if d_ > EPS and np.isfinite(p_) and abs(p_) <= EPS:
                    attr.append('precision（推导 %s，后段 %s，后段 MDE80 中位 %s）' % (fmt(d_), fmt(p_), fmt(mde)))
        drows.append(dict(member_id=mid, axis=r.axis_id, family=r.family_id, construction=r.formula_version,
                          source_class=r.source_class, roles_tested=rec['roles_tested'],
                          evidence='推导 %s / 后段 %s / 四段 %s（主方向单成员描述符 %d 个的中位；匹配随机 推导 %s）' % (
                              fmt(d_), fmt(p_), fmt(rec['all4_median']), len(g), fmt(rec['zmap_deriv_median'])),
                          best_role=rec.get('best_role_deriv', ''), status=status,
                          failure_attribution='；'.join(attr) if attr else ('—' if status == 'positive_deriv_and_post' else 'unknown')))
    cat = pd.DataFrame(rows)
    for r in notb.itertuples():
        cat = pd.concat([cat, pd.DataFrame([dict(member_id=r.measure, axis=r.axis, ledger_status='considered_not_built',
                                                 valid_domain='未构造（%s）' % r.status,
                                                 executable_status='%s：%s' % (r.status, r.reason),
                                                 source_ref=r.source)])], ignore_index=True)
    cat.to_csv(os.path.join(R, 'reports', 'research_catalog_v36.csv'), index=False)
    D = pd.DataFrame(drows)
    md = ['# E6i factor_iteration_delta（每成员一行；执行端规则化初判，供规划 session 更新因子迭代台账时复核）\n',
          '规则（写死在 `e6i_stage4_catalog.py`，不看结果改）：读数 = 该成员**主方向、单成员**描述符（主路线，不含 M1 / M2 / 四臂 / TPAIR 复合）的中位；'
          '推导 = 推导两段合并，后段 = 两后段合并，四段 = 按有效日合并；年化百分点。状态：推导与后段都 > +%.2f → positive_deriv_and_post；'
          '只推导 > +%.2f → positive_deriv_only；只后段 → positive_post_only；两者都在 ±%.2f 内 → near_zero_both；其余 negative_or_mixed；'
          '无单成员描述符 → untested_single_role / measured_only。失效归因（可多选）：capital = 对母体为负但同资本为正；role = 对母体为负但对匹配随机为正；'
          'measurement = 对母体与匹配随机都不为正；time = 推导为正、后段为负；precision = 推导为正、后段接近 0（附后段 MDE）。'
          '这些是可复核的机械标签，不是因果定案；"无效果"只对该成员 x 角色 x 母体 x 时期 x 口径成立。\n' % (EPS, EPS, EPS)]
    cnt = D.status.value_counts()
    md.append('状态计数：' + '，'.join('%s %d' % (k, v) for k, v in cnt.items()) + '（共 %d 个目录成员）。\n' % len(D))
    md.append('| member_id | axis | family | construction | roles_tested | evidence | best_role（推导） | status | failure_attribution |')
    md.append('|---|---|---|---|---|---|---|---|---|')
    for r in D.sort_values(['axis', 'status', 'member_id']).itertuples():
        md.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            r.member_id, r.axis, r.family, r.construction, r.roles_tested, r.evidence, r.best_role, r.status,
            r.failure_attribution))
    open(os.path.join(R, 'reports', 'factor_iteration_delta.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    D.to_csv(os.path.join(R, 'reports', 'factor_iteration_delta.csv'), index=False)
    I.write_receipt(os.path.join(R, 'task_status', 'stage4_catalog.receipt.json'), 'stage4:catalog',
                    [os.path.join(R, 'reports', f) for f in ('research_catalog_v36.csv', 'factor_iteration_delta.md',
                                                              'factor_iteration_delta.csv')])
    print('research_catalog_v36 %d 行; factor_iteration_delta %d 行 %s; %.0fs' % (len(cat), len(D), cnt.to_dict(),
                                                                                  time.time() - t0))


if __name__ == '__main__':
    main()
