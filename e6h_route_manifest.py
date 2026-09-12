#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 记录 A v0 的物化 (brief §4: "记录 A v0 本 brief 即生效, 执行端 R0 交付后可开跑")。

产出:
  registry/route_manifest.json      —— 机器可读, 【研究程序只从这里编译策略】
  registry/need_parent_role_map.csv —— plan §2.1 第三层, 含 status 与证据
  registry/consideration_ledger.csv —— 所有被考虑过的键 x 母体, 含未路由的理由

关键约束 (plan §2.1 末段): "研究程序只从已签署的 routed 行编译策略, 不能遍历 U74
自动把 LEG/VETO/ADD 等全部展开。RouteManifest 与因子总表的交集之外, 不产出后段结果。"

方向要特别小心 (proposal 勘误 / 复盘 #33): `abn_turnover` 源值已取负, 所以
  源值【高】= MA20/MA120 【低】= 换手相对自身历史更安静 = E-V 的【量静】分支
  源值【低】= 换手比高 = 【量增】分支
两者各自成卡, 不合并成一个方向。
"""
from __future__ import annotations
import os
import sys
import json
import time
import hashlib

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H

RES = H.RES
PARENTS = ['R1', 'R2', 'A06', 'A08']

# ---------------------------------------------------------------- 记录 A v0
# plan §3.1 的七条初始路线, 竞争解释各自成卡 (brief §4)
ROUTES = [
    dict(route_id='M-T-tcv-vs-t60', need_id='MEASURE_T_MIXES_LEVEL_AND_INSTABILITY',
         question='T 的标准差是否混合了活动水平与不稳定性; 也可能这种混合本来就有用',
         measurements=['turnover_volatility_60d', 'turnover_5d', 'TCV_20', 'TCV_60'],
         parents=['A08', 'T25'], migrate_parents=['R2', 'A06'],
         stage='core_leg_T', roles=['SLOT_FALLBACK', 'SLOT_REPLACE'],
         direction='hi', competitor=None,
         grids=dict(alpha=[0, 0.25, 0.5, 1.0]),
         rationale=('R0 实测: R1 两关的分离力在两段间翻转 (2010-14 第一关 29.2bp / '
                    '第二关 17.6bp; 2015-18 第一关 11.3bp / 第二关 28.0bp) —— '
                    'T 位承担的工作量本身不稳定'),
         evidence_origin='discovery'),
    dict(route_id='M-C-position-window', need_id='MEASURE_C_TOO_SLOW_OR_WRONG_POSITION',
         question='20 日 C 是否测得太慢, 或另一种位置指标更清楚; 也可能替换损失有效信息',
         measurements=['CVR_20d', 'CVR_5d', 'CLV_20d', 'CLV'],
         alias_bridge=['intraday_cvr_1d', 'CVR'],
         parents=['A06'], migrate_parents=['R2'],
         stage='core_leg_C_and_focal_veto', roles=['SLOT_FALLBACK', 'SLOT_REPLACE',
                                                   'FOCAL_REPLACE'],
         direction='hi', competitor=None,
         grids=dict(alpha=[0, 0.25, 0.5, 1.0], k=[5, 10]),
         rationale='替换核心与替换否决不能混为一次改动 (plan §3.1), 两处分域',
         evidence_origin='mechanism_motivated'),
    dict(route_id='E-V-quiet-price', need_id='CORE_EXCEPTION_VOLUME',
         question='高 K/T 的某些股票是否只是量能变化良性而价格未响应 —— 【量静】分支',
         measurements=['abn_turnover', 'volume_ratio_3d', 'volume_ratio_5d',
                       'amount_ratio_1d', 'cum_return_20d'],
         parents=['R1'], migrate_parents=['R2', 'A06'],
         stage='economic_rejection_set', roles=['ADD', 'SWAP', 'CONJ'],
         direction='hi',
         direction_note=('abn_turnover 源值【高】= 换手比低 = 量静。这是 T0 支持的分支 '
                         '(brief §4 / 复盘 #33)'),
         competitor='E-V-surge-price',
         grids=dict(eta=[0, 0.10, 0.25, 0.50], price_cond=['REL_LOW_q20', 'REL_LOW_q30',
                                                           'NEAR_ZERO_20d_10pct',
                                                           'NEAR_ZERO_5d_5pct']),
         rationale='T0 画像反读后的支持分支; R1 的第二关拒绝集实测【优于】同构成随机',
         evidence_origin='discovery'),
    dict(route_id='E-V-surge-price', need_id='CORE_EXCEPTION_VOLUME',
         question='同上 —— 【量增】竞争分支 (越吵越好还是越静越好)',
         measurements=['abn_turnover', 'volume_ratio_3d', 'volume_ratio_5d',
                       'amount_ratio_1d', 'cum_return_20d'],
         parents=['R1'], migrate_parents=['R2', 'A06'],
         stage='economic_rejection_set', roles=['ADD', 'SWAP', 'CONJ'],
         direction='lo',
         direction_note='abn_turnover 源值【低】= 换手比高 = 量增。竞争分支, 与量静同价格条件',
         competitor='E-V-quiet-price',
         grids=dict(eta=[0, 0.10, 0.25, 0.50], price_cond=['REL_LOW_q20', 'REL_LOW_q30',
                                                           'NEAR_ZERO_20d_10pct',
                                                           'NEAR_ZERO_5d_5pct']),
         rationale='plan §3.2 要求量增/量静在同一价格条件内比较, 不预判方向',
         evidence_origin='mechanism_motivated'),
    dict(route_id='E-P-path-conditional-focal', need_id='PATH_DIFFERS_SAME_RETURN',
         question='同样低/高近期收益是否因路径不同而应有不同处理',
         measurements=['intraday_ret_consistency_5d', 'positive_day_ratio_5d',
                       'agreement_count_5d', 'daynight_divergence'],
         parents=['R2', 'A06'], migrate_parents=[],
         stage='focal_veto_cr5', roles=['FOCAL_CONDITION'],
         direction='both',
         grids=dict(k=[5, 10],
                    ratio_thresholds=[0.2, 0.8], count_thresholds=[1, 4],
                    divergence=[0, 1],
                    mode=['enable_in_state', 'exempt_in_state']),
         rationale=('比例键用 0.2/0.8, 计数键 agreement_count_5d 用 <=1/>=4 —— '
                    '已按源码核: 前三个是 .mean() 是比例, 后者是 .sum() 是计数'),
         evidence_origin='mechanism_motivated'),
    dict(route_id='R-O-overnight-risk', need_id='UNPROCESSED_OVERNIGHT_RISK_IN_KEPT',
         question='最终保留集里隔夜主导/异常跳空是否留下未处理风险; 也可能只是总波动代理',
         measurements=['JUMP_5', 'JUMP_20', 'gap_abs_zscore_20d'],
         diagnostic=['gap_zscore_20d'],
         parents=['R1', 'R2', 'A06'], migrate_parents=[],
         stage='kept_set_B', roles=['FOCAL_CONDITION', 'SOFT_DEWEIGHT'],
         direction='hi', competitor='R-O-overnight-risk-low',
         grids=dict(k=[5, 10], lam=[0, 0.5, 1.0]),
         rationale='JUMP 是隔夜平方收益占比, 不是严格跳跃检验; 高/低状态分卡不混平均',
         evidence_origin='mechanism_motivated'),
    dict(route_id='I-P-peer-up-laggard', need_id='INDUSTRY_MOVED_STOCK_DID_NOT',
         question='同业已上行而个股未响应 —— 补涨机会分支',
         measurements=['IND_CUR_5', 'IND_CUR_20', 'REL_IND_5', 'REL_IND_20'],
         parents=['R1', 'R2', 'A06'], migrate_parents=[],
         stage='economic_rejection_set', roles=['ADD', 'SWAP'],
         direction='hi', competitor='I-P-peer-down-risk',
         grids=dict(w=[5, 20], q=[0.2, 0.3], eta=[0, 0.10, 0.25, 0.50]),
         rationale=('R0 实测: REL_IND_20 在 D 内对标签的排序 rho -0.062~-0.068, '
                    '两段同号、三母体一致, 与最好的已有键同档'),
         evidence_origin='discovery'),
    dict(route_id='I-P-peer-down-risk', need_id='INDUSTRY_MOVED_STOCK_DID_NOT',
         question='同业已下行而个股未响应 —— 下行滞后风险分支 (竞争问题, 不是同一方向)',
         measurements=['IND_CUR_5', 'IND_CUR_20'],
         parents=['R1', 'R2', 'A06'], migrate_parents=[],
         stage='kept_set_B', roles=['FOCAL_CONDITION'],
         direction='lo', competitor='I-P-peer-up-laggard',
         grids=dict(w=[5, 20], k=[5, 10]),
         rationale='plan §3.2: 负同行卡与向上机会卡互为竞争问题, 不平均成"行业轴无效"',
         evidence_origin='mechanism_motivated'),
    dict(route_id='L-Q-margin-liquidity', need_id='MARGINAL_NAMES_COST_TOO_MUCH',
         question='已有信号的边缘替代品能否省成本而少损 gross; 便宜也可能意味着丢流动性溢价',
         measurements=['amihud_daily', 'amihud_ratio_5d_20d', 'amount_ratio_1d'],
         parents=['A06', 'R2', 'A08'], migrate_parents=[],
         stage='core_margin', roles=['MARGIN'],
         direction='hi',
         grids=dict(e=[0.10, 0.25, 0.50],
                    order=['source', 'cheap_first', 'expensive_first', 'random_in_band']),
         rationale='归 L 线但用 NEW40 血缘 (amihud), 登记前只跑推导段 (brief §8)',
         evidence_origin='mechanism_motivated'),
]

# 明确【只作诊断, 不进交易角色】的键 (plan 附录 A)
DIAGNOSTIC_ONLY = {
    'gap_vs_sector': '源为全市场去均值占位, 不是行业信息 (plan 附录 A #11)',
    'gap_rank_in_sector': '源为全市场 rank 占位, 不冒充行业内 rank (#12)',
    'mcap_rank': '诊断/混杂控制, 本轮不自动加入交易评分 (#40)',
    'volume_rank_market': '股数量截面 rank, 与股本混杂; 未路由不交易 (#38)',
    'CMF_20d': 'I11 已用 (pct>=0.80 截断); 若提持续性需求可另路由, 本轮不改 I11 (#39)',
    'intraday_ret': 'I11 信号成分 (pct<0.70 截断), 同源诊断',
    'cum_return_5d': 'I11 信号成分 (0.25-0.55 截断), 同源诊断',
}


def main():
    os.makedirs(os.path.join(RES, 'registry'), exist_ok=True)
    sem = pd.read_csv(os.path.join(RES, 'registry', 'feature_semantics.csv'))
    rel = pd.concat([pd.read_csv(os.path.join(
        RES, 'T0_full_distribution', 'factor_parent_relation_%s.csv' % s)).assign(seg=s)
        for s in H.DERIV_SEGS], ignore_index=True)

    # --- 证据标志: 按两段一致性 + 分位, 不用拍脑袋阈值 ---
    ev = rel.pivot_table(index=['key', 'parent'], columns='seg',
                         values=['rho_label_in_D', 'rho_label_in_B', 'max_abs_rho_leg',
                                 'pct_sep_D_minus_B'])
    flags = []
    for (k, p), r in ev.iterrows():
        def two(col):
            a = r.get((col, H.DERIV_SEGS[0]), np.nan)
            b = r.get((col, H.DERIV_SEGS[1]), np.nan)
            same = np.isfinite(a) and np.isfinite(b) and np.sign(a) == np.sign(b)
            return a, b, same, (min(abs(a), abs(b)) if same else 0.0)
        dA, dB, dS, dM = two('rho_label_in_D')
        bA, bB, bS, bM = two('rho_label_in_B')
        lA, lB, lS, lM = two('max_abs_rho_leg')
        flags.append(dict(key=k, parent=p,
                          rho_label_in_D_min_abs_same_sign=round(dM, 4),
                          rho_label_in_B_min_abs_same_sign=round(bM, 4),
                          max_abs_rho_leg_min=round(lM, 4),
                          d_consistent=bool(dS), b_consistent=bool(bS)))
    fl = pd.DataFrame(flags)
    # 分位阈值 (数据定, 不拍脑袋): 取同号一致者的 p90
    thD = fl.loc[fl.d_consistent, 'rho_label_in_D_min_abs_same_sign'].quantile(0.90)
    thB = fl.loc[fl.b_consistent, 'rho_label_in_B_min_abs_same_sign'].quantile(0.90)
    thL = fl['max_abs_rho_leg_min'].quantile(0.90)
    fl['flag_rejection_opportunity'] = fl.d_consistent & (
        fl.rho_label_in_D_min_abs_same_sign >= thD)
    fl['flag_kept_risk'] = fl.b_consistent & (fl.rho_label_in_B_min_abs_same_sign >= thB)
    fl['flag_same_axis_replacement'] = fl.max_abs_rho_leg_min >= thL

    # --- 路由表 ---
    routed = {}
    for rt in ROUTES:
        for m in rt['measurements']:
            for p in rt['parents'] + rt.get('migrate_parents', []):
                routed.setdefault((m, p), []).append(rt['route_id'])

    rows = []
    for _, s in sem.iterrows():
        k = s['key']
        for p in PARENTS:
            rids = routed.get((k, p), [])
            if rids:
                status, why = 'routed', '记录 A v0: %s' % ','.join(rids)
            elif k in DIAGNOSTIC_ONLY:
                status, why = 'diagnostic_only', DIAGNOSTIC_ONLY[k]
            else:
                f = fl[(fl.key == k) & (fl.parent == p)]
                anyflag = bool(len(f)) and bool(f.iloc[0][['flag_rejection_opportunity',
                                                           'flag_kept_risk',
                                                           'flag_same_axis_replacement']].any())
                status = 'candidate_for_routing' if anyflag else 'unassigned'
                why = ('有证据标志但记录 A v0 未路由; 规划 session 在 v1 决定'
                       if anyflag else
                       '本轮无用途行; **未路由 != 无效** (plan §2.1), 留考虑台账')
            f = fl[(fl.key == k) & (fl.parent == p)]
            fd = f.iloc[0].to_dict() if len(f) else {}
            rows.append(dict(
                key=k, parent=p, status=status, status_basis=why,
                route_ids='|'.join(rids),
                measurement_families=s['measurement_families'],
                protected=s['protected'], key_class=s['key_class'],
                source_sign=s['source_sign'],
                economic_direction_of_high_source=s['economic_direction_of_high_source'],
                tie_frac_raw=s.get('tie_frac_raw'),
                market_wide_placeholder=s.get('market_wide_placeholder'),
                signal_overlap=s.get('signal_overlap'),
                flag_rejection_opportunity=fd.get('flag_rejection_opportunity'),
                flag_kept_risk=fd.get('flag_kept_risk'),
                flag_same_axis_replacement=fd.get('flag_same_axis_replacement'),
                rho_label_in_D_consistent=fd.get('rho_label_in_D_min_abs_same_sign'),
                rho_label_in_B_consistent=fd.get('rho_label_in_B_min_abs_same_sign'),
                max_abs_rho_leg=fd.get('max_abs_rho_leg_min'),
                previous_looks=s.get('previous_looks')))
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(RES, 'registry', 'need_parent_role_map.csv'), index=False)
    d[d.status != 'routed'].to_csv(
        os.path.join(RES, 'registry', 'consideration_ledger.csv'), index=False)

    man = dict(
        plan_version='E6h-v2.0', record='A', version='v0',
        status='ACTIVE',
        written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
        note=('记录 A v0 按 brief §4 在 brief 落地即生效。规划 session 在 R0 交付后出 v1 '
              '(只增改, 不按推导段收益删 routed 行)。研究程序【只从本清单编译策略】。'),
        thresholds=dict(rho_label_in_D_p90=round(float(thD), 4),
                        rho_label_in_B_p90=round(float(thB), 4),
                        max_abs_rho_leg_p90=round(float(thL), 4),
                        basis='同号一致者的 90 分位, 由数据定, 不是事前拍的门'),
        market_data_end_max=H.MARKET_DATA_END_MAX,
        training_label_end_max=H.PROTECTED_LABEL_END,
        post2018_allowed=False,
        approval_receipt=None,
        routes=ROUTES,
        counts=dict(n_routes=len(ROUTES),
                    n_routed_pairs=int((d.status == 'routed').sum()),
                    n_candidate=int((d.status == 'candidate_for_routing').sum()),
                    n_diagnostic_only=int((d.status == 'diagnostic_only').sum()),
                    n_unassigned=int((d.status == 'unassigned').sum()),
                    n_keys=len(sem), n_parents=len(PARENTS)))
    raw = json.dumps(man, indent=1, ensure_ascii=False, default=str)
    man['self_sha256'] = hashlib.sha256(raw.encode()).hexdigest()
    with open(os.path.join(RES, 'registry', 'route_manifest.json'), 'w') as fh:
        json.dump(man, fh, indent=1, ensure_ascii=False, default=str)

    print('== 记录 A v0 物化 ==')
    print(' 路线 %d 条; (键 x 母体) 对: routed %d / candidate %d / diagnostic_only %d / unassigned %d'
          % (len(ROUTES), man['counts']['n_routed_pairs'], man['counts']['n_candidate'],
             man['counts']['n_diagnostic_only'], man['counts']['n_unassigned']))
    print(' 证据阈值 (数据定的 p90): D %.4f / B %.4f / leg %.4f' % (thD, thB, thL))
    print(' sha256 %s' % man['self_sha256'][:16])
    print()
    print(' 逐路线:')
    for rt in ROUTES:
        print('   %-26s %-14s 母体 %-18s 角色 %s'
              % (rt['route_id'], rt['stage'][:14],
                 ','.join(rt['parents']) + (('+' + ','.join(rt['migrate_parents']))
                                            if rt.get('migrate_parents') else ''),
                 ','.join(rt['roles'])))


if __name__ == '__main__':
    main()
