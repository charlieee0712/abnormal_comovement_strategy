#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i A0 登记编译 (brief §3; plan §5.1 九条路线 + §5.7 生成器合同 + §7.1 固定代表)。

产物 (不等收益; 在任何新测量收益评价之前冻结):
  registry/need_estimator_role_map.csv   路线 x 母体 x 成员 x 角色 (含 strength_grid / H_grid / 对照)
  registry/descriptors_A0.csv            展开到账户配置 (一行 = 一个可运行账户) + 随机路径优先级
  registry/hypotheses_A0.json            Q1-Q18 与读法优先级 (brief §12)
  registry/manifest_A0.json              计数 (轴/估计对象/母体/角色/H/支持政策/方向) + SHA
约束 (plan §5.1): 只按真实槽位、字段缺失或数学同义做 source-only 落实; 不按任何 ρ / 收益删。
方向是描述符 (plan §5.7 默认表): 主方向 + 竞争方向各自是一条描述符, 不按 Stage 1 改。
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import json
import time
import hashlib
import itertools
import collections

import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE

HS = (3, 5, 10, 20)
HS_FAST = (1, 2)
ALPHAS = (0.125, 0.25, 0.5)                  # α=0 是 identity 短路 (每母体 x 槽位 1 条锚)
GAMMAS = (0.0625, 0.125, 0.25)
KS = (5, 10)
LAMS = (0.25, 0.5, 1.0)
QS = (0.05, 0.10, 0.20)
BETAS = (0.0, 0.25, 0.5, 0.75, 1.0)
ETAS = (0.25, 0.5, 1.0)                      # M1 父权重混合
M2_LAMS = (0.1, 1.0, 10.0)

SLOTS = {'R1': {'K': 'dep_stage1', 'T': 'dep_stage2'}, 'R2': {'K': 'mean_leg0', 'T': 'mean_leg1'},
         'A06': {'K': 'mean_leg0', 'T': 'mean_leg1', 'C': 'mean_leg2'}, 'A08': {'T': 'single'}}
FOCAL_CVR = {'R1': 'C:k5', 'R2': 'C:k5', 'A08': 'C:k5'}          # CVR_20d 否决 (焦点)
FOCAL_CR5 = {'R2': 'cr5:k10', 'A06': 'cr5:k10', 'A08': 'cr5:k10'}  # 收益焦点
FOCAL_CVR1 = {'A06': 'cvr_1d:k10'}

# plan §7.1 固定代表 (事前按源清楚选, 不按收益)
REPS = {
    'T': ['T_mean20', 'T_cv20', 'T_madrel20', 'T_resid20', 'T_cvpre20', 'T_std60_LEGACY'],
    'K': ['K0_LEGACY', 'K_ROS20_E6F', 'K_log', 'K_res_log', 'K_ar20', 'K_edge20'],
    'V': ['V_park20_obs', 'V_rs20_obs', 'V_yz20_obs', 'V_on20', 'V_semid20'],
    'R': ['R_5_s0', 'R_peer20', 'R_resid20', 'R_eff20'],
    'O': ['O_onmean5', 'O_enshare20', 'O_balance20', 'O_retreat_up20'],
    'C': ['C_mean20', 'C_mean40', 'C_amtw20', 'C_dev1'],
    'A': ['A_rel20', 'A_innov', 'T_evlevel', 'A_frompeak'],
    'S': ['S_peerR20', 'S_peerpos20', 'S_peeriqr20', 'S_peeract'],
}
REP_SET = set(itertools.chain.from_iterable(REPS.values()))

DIAGNOSTIC_ONLY = {'T_zero20', 'T_zero60', 'K_notrade20', 'K_notrade60', 'K_css20', 'K_css60',
                   'K_edges20', 'K_edges60'}
FRICTION_FAM = {'friction_roll', 'friction_cs', 'friction_ar', 'friction_edge', 'friction_zero'}
Q_OF_ROUTE = {'RT': 'Q1', 'RK': 'Q2', 'RV': 'Q3', 'RO': 'Q4', 'RR': 'Q5', 'RC': 'Q6', 'RL': 'Q7',
              'RA': 'Q13', 'RS': 'Q14', 'FOURARM': 'Q15', 'M1': 'Q8', 'M2': 'Q8', 'TPAIR': 'Q1'}
NEED = {
    'RT': 'T 测量是否混合过重 (水平 / 相对尺度 / 趋势 / 事件)',
    'RK': 'K 分母与条件活动 (价平 / 换手水平 / 条件吸收 / 表示)',
    'RV': '保留集的范围风险与尾部风险',
    'RR': '相对落后 / 已涨的识别; 边缘固定名额替换',
    'RO': '保留集昼夜结构与焦点否决',
    'RC': 'C 核心位置 (A06) 与原 CVR 焦点否决 (R1/R2/A08)',
    'RA': '第一关量价例外; 边缘名单',
    'RS': '同行状态调制落后信息与相对收益否决',
    'RL': '边缘交易摩擦 (成本, 不是 alpha)',
}


def cat():
    FE.build_catalog()
    return {m['member_id']: m for m in FE.CATALOG}


def members_for(axis_ids, C, exclude_fam=(), include=(), legacy_ok=()):
    out = []
    for mid, m in C.items():
        if m['axis_id'] in axis_ids and mid not in DIAGNOSTIC_ONLY and m['family_id'] not in exclude_fam:
            if m['source_class'] == 'LEGACY' and mid not in legacy_ok:
                continue
            out.append(mid)
    out += [x for x in include if x not in out]
    return sorted(out)


def dirs_for(mid, C, route):
    """(方向, 读法角色) 列表 —— plan §5.7 默认方向表。"""
    m = C[mid]
    ax, fam = m['axis_id'], m['family_id']
    if route in ('RT', 'RV', 'RC', 'RL'):
        return [('high_bad', 'primary'), ('low_bad', 'reverse_control')]
    if route == 'RK':
        if fam in ('turnover_response', 'amount_response', 'pointwise_inverse_bridge'):
            return [('low_bad', 'primary_inverse_mapped'), ('high_bad', 'competing')]
        return [('high_bad', 'primary'), ('low_bad', 'competing')]
    if route == 'RR':
        return [('high_bad', 'reversal_domain'), ('low_bad', 'continuation_domain')]
    if route in ('RO', 'RA'):
        return [('high_bad', 'high_role'), ('low_bad', 'low_role')]
    return [('state', 'state')]


def main():
    t0 = time.time()
    C = cat()
    maprows, D = [], []

    def add_map(route, mother, mid, role, dirn, dirrole, strength, hgrid, comps, stage, target,
                note=''):
        m = C.get(mid, {})
        maprows.append(dict(
            route_id=route, mother_id=mother, need_id='N_%s' % route, need=NEED.get(route, ''),
            decision_stage=stage, target_set=target,
            estimand_family='%s:%s' % (m.get('axis_id', ''), m.get('estimand_id', mid)),
            members=mid, role=role, direction=dirn, direction_role=dirrole,
            strength_grid='|'.join(map(str, strength)), H_grid='|'.join(map(str, hgrid)),
            comparator_ids=comps, motive_id='M_%s' % m.get('axis_id', route),
            hypothesis_id=Q_OF_ROUTE.get(route, ''), information_status='A0_preregistered',
            enabled_reason=note or 'plan §5.1 路线表 / §5.7 生成器合同',
            representative=mid in REP_SET))

    def expand(route, mother, mid, role, dirn, dirrole, grid, hgrid, policy='', extra=None):
        for s in grid:
            for h in hgrid:
                did = '%s|%s|%s|%s|%s=%s|%s|H%d' % (route, mother, mid, role,
                                                    {'SLOT': 'a', 'ADD_SCORE': 'g', 'VETO_NEW': 'k',
                                                     'SOFT': 'lam', 'SWAP': 'q', 'T_PAIR': 'b',
                                                     'FOCAL_NEW': 'state', 'RL': 'e',
                                                     'SOFT_HARD': 'k', 'COMMON_SUPPORT': 'a'
                                                     }.get(role, 's'),
                                                    s, dirn + (':' + policy if policy else ''), h)
                D.append(dict(descriptor_id=did, route_id=route, mother_id=mother, member_id=mid,
                              axis_id=C[mid]['axis_id'] if mid in C else '', role=role,
                              strength=s, policy=policy, direction=dirn, direction_role=dirrole,
                              H=h, representative=mid in REP_SET,
                              support_policy=C[mid]['policy'] if mid in C else '',
                              random_priority=(256 if mid in REP_SET else 64),
                              hypothesis_id=Q_OF_ROUTE.get(route, ''), **(extra or {})))

    # ---------------- RT: T 槽位 (四母体都有) ----------------
    rt = members_for({'T'}, C, legacy_ok={'T_TCV20_E6H', 'T_mean5_LEGACY'})
    for mother in ('R1', 'R2', 'A06', 'A08'):
        stage = SLOTS[mother]['T']
        for mid in rt:
            for dirn, dr in dirs_for(mid, C, 'RT'):
                add_map('RT', mother, mid, 'SLOT', dirn, dr, (0,) + ALPHAS + (1,), HS,
                        'sameN_core|slot_shuffle_new|reverse|parent_common|same_capital', stage,
                        'pool0 核排序 (T 位)')
                expand('RT', mother, mid, 'SLOT', dirn, dr, ALPHAS, HS, 'FALLBACK')
                expand('RT', mother, mid, 'SLOT', dirn, dr, (1.0,), HS, 'FULL_REPLACE')
                expand('RT', mother, mid, 'SLOT', dirn, dr, (1.0,), HS, 'FALLBACK_REPLACE')
                if dr == 'primary':
                    expand('RT', mother, mid, 'COMMON_SUPPORT', dirn, dr, ALPHAS + (1.0,), (5,),
                           'COMMON_SUPPORT')
        # T 位内二维重构 (plan §4.1): 同窗 level x CV
        for lv, cv in (('T_mean20', 'T_cv20'), ('T_mean60', 'T_cv60')):
            pair = '%s+%s' % (lv, cv)
            C.setdefault(pair, dict(axis_id='T', estimand_id='T_pair', policy='OBS'))
            add_map('TPAIR', mother, pair, 'T_PAIR', 'high_bad', 'primary', BETAS, HS,
                    'orig_rank_std_bridge|sameN_core', stage, 'T 位内部 level x CV')
            expand('TPAIR', mother, pair, 'T_PAIR', 'high_bad', 'primary', BETAS, HS)

    # ---------------- RK: K 槽位 (R1 第一阶段 / R2 / A06; A08 不适用) ----------------
    rk = members_for({'K'}, C, exclude_fam=FRICTION_FAM | {'ra_derived'},
                     legacy_ok={'K_MA3_E6F', 'K_MA5_E6F', 'K_ROS5_E6F', 'K_ROS20_E6F'})
    rk_fast = {m for m in rk if C[m]['window'] in (1, None)}          # 当日响应 -> H{1,2} 快端
    for mother in ('R1', 'R2', 'A06'):
        stage = SLOTS[mother]['K']
        for mid in rk:
            hg = HS + (HS_FAST if mid in rk_fast else ())
            for dirn, dr in dirs_for(mid, C, 'RK'):
                add_map('RK', mother, mid, 'SLOT', dirn, dr, (0,) + ALPHAS + (1,), hg,
                        'sameN_core|slot_shuffle_new|reverse|parent_common', stage, 'pool0 核排序 (K 位)')
                expand('RK', mother, mid, 'SLOT', dirn, dr, ALPHAS, hg, 'FALLBACK')
                expand('RK', mother, mid, 'SLOT', dirn, dr, (1.0,), hg, 'FULL_REPLACE')
                expand('RK', mother, mid, 'SLOT', dirn, dr, (1.0,), hg, 'FALLBACK_REPLACE')
                if dr.startswith('primary'):
                    expand('RK', mother, mid, 'COMMON_SUPPORT', dirn, dr, ALPHAS + (1.0,), (5,),
                           'COMMON_SUPPORT')
    # ---------------- RV: R2 / A06 保留集风险 ----------------
    rv = members_for({'V'}, C)
    for mother in ('R2', 'A06'):
        for mid in rv:
            for dirn, dr in dirs_for(mid, C, 'RV'):
                add_map('RV', mother, mid, 'VETO_NEW|SOFT|SOFT_HARD|ADD_SCORE', dirn, dr,
                        KS + LAMS + GAMMAS, HS, 'veto_random_sameM|veto_core_deeper_sameM|'
                        'veto_reverse_sameM|parent_common', 'post_core_retained', '最终保留集')
                expand('RV', mother, mid, 'VETO_NEW', dirn, dr, KS, HS)
                expand('RV', mother, mid, 'SOFT', dirn, dr, LAMS, HS, 'no_realloc')
                expand('RV', mother, mid, 'SOFT_HARD', dirn, dr, (10,), HS, 'hard_delete_reDEV')
                expand('RV', mother, mid, 'ADD_SCORE', dirn, dr, GAMMAS, HS)
    # ---------------- RR: R1 / R2 (A06 迁移) ----------------
    rr = members_for({'R'}, C)
    for mother in ('R1', 'R2', 'A06'):
        for mid in rr:
            for dirn, dr in dirs_for(mid, C, 'RR'):
                add_map('RR', mother, mid, 'SWAP|ADD_SCORE|FOCAL_NEW', dirn, dr, QS + GAMMAS, HS,
                        'swap_random_same_E|swap_industry_matched|swap_reverse|parent',
                        'edge_fixed_quota', '最终保留集最差 m 个 <-> 经济拒绝集 E')
                expand('RR', mother, mid, 'SWAP', dirn, dr, QS, HS, 'out=mother_worst')
                expand('RR', mother, mid, 'ADD_SCORE', dirn, dr, GAMMAS, HS)
                if mother in FOCAL_CR5:
                    # 【A0 修订 v1.2, 2026-09-23】plan §5.3 焦点替换比较 旧 / 新 / 两者 / 皆无:
                    # 旧 = 母体、皆无 = RO 的 all_off (cr5:k10), v1.0/v1.1 只编了"新"(replace), 补"两者"。
                    expand('RR', mother, mid, 'FOCAL_NEW', dirn, dr, ('replace_cr5', 'both_cr5'), HS,
                           FOCAL_CR5[mother])
        # b=10 桥 (plan §5.5: 固定 b=0 与一个已登记 b=10, 只用于 RR/RS 兑现) —— 代表成员
        for mid in REPS['R']:
            expand('RR', mother, mid, 'SWAP', 'high_bad', 'reversal_domain', (0.10,), HS,
                   'out=mother_worst|buffer_b10', extra=dict(buffer_b=10))
    # ---------------- RO: R1 / R2 / A06 保留集昼夜 ----------------
    ro = members_for({'O'}, C, legacy_ok={'O_jump5_E6H', 'O_jump20_E6H'},
                     include=('V_on20', 'V_oc20'))
    ro_fast = {m for m in ro if C[m]['window'] in (1, 5)}
    for mother in ('R1', 'R2', 'A06'):
        for mid in ro:
            hg = HS + (HS_FAST if mid in ro_fast else ())
            for dirn, dr in dirs_for(mid, C, 'RO'):
                add_map('RO', mother, mid, 'VETO_NEW|SOFT', dirn, dr, KS + LAMS, hg,
                        'veto_random_sameM|veto_core_deeper_sameM|veto_reverse_sameM',
                        'post_core_retained', '最终保留集 (不搬到拒绝集)')
                expand('RO', mother, mid, 'VETO_NEW', dirn, dr, KS, hg)
                expand('RO', mother, mid, 'SOFT', dirn, dr, LAMS, hg, 'no_realloc')
        # 正 / 负 gap 分别作为焦点状态 (有焦点 cvr/cr 规则的母体)
        focal = {**{k: v for k, v in FOCAL_CVR.items() if k == mother},
                 **{k: v for k, v in FOCAL_CR5.items() if k == mother},
                 **{k: v for k, v in FOCAL_CVR1.items() if k == mother}}
        for fk, fv in focal.items():
            for st in ('gap_pos', 'gap_neg'):
                for arm in ('all_on', 'all_off', 'real_state', 'random_state'):
                    expand('RO', mother, 'O_o1', 'FOCAL_NEW', 'state', st, (arm,), HS + HS_FAST,
                           '%s@%s' % (fv, st))
    # ---------------- RC: A06 C 核心 SLOT; R1/R2/A08 CVR 焦点替换 ----------------
    rc = members_for({'C'}, C)
    rc_fast = {'C_p1', 'C_dev1'}
    for mid in rc:
        hg = HS + (HS_FAST if mid in rc_fast else ())
        for dirn, dr in dirs_for(mid, C, 'RC'):
            add_map('RC', 'A06', mid, 'SLOT', dirn, dr, (0,) + ALPHAS + (1,), hg,
                    'sameN_core|slot_shuffle_new|reverse', 'mean_leg2', 'A06 C 核心')
            expand('RC', 'A06', mid, 'SLOT', dirn, dr, ALPHAS, hg, 'FALLBACK')
            expand('RC', 'A06', mid, 'SLOT', dirn, dr, (1.0,), hg, 'FULL_REPLACE')
            expand('RC', 'A06', mid, 'SLOT', dirn, dr, (1.0,), hg, 'FALLBACK_REPLACE')
            for mother in ('R1', 'R2', 'A08'):
                add_map('RC', mother, mid, 'FOCAL_NEW', dirn, dr, ('old', 'new', 'both', 'none'),
                        hg, 'focal_all_on|all_off|random_state', 'focal_veto',
                        '%s 的 CVR_20d k5 否决 (先关原焦点)' % mother)
                expand('RC', mother, mid, 'FOCAL_NEW', dirn, dr, ('new', 'both'), hg,
                       FOCAL_CVR[mother])
    for mother in ('R1', 'R2', 'A08'):                              # 焦点四对照里与成员无关的两臂
        for arm in ('old', 'none'):
            expand('RC', mother, 'C_CVR20_LEGACY', 'FOCAL_NEW', 'high_bad', 'focal_arm', (arm,),
                   HS + HS_FAST, FOCAL_CVR[mother])
    # ---------------- RA: K 槽位内条件测量 + SWAP ----------------
    ra = members_for({'A'}, C, legacy_ok=set(), include=('T_evlevel', 'K_rar20', 'K_rarpre'))
    for mother in ('R1', 'R2', 'A06'):
        for mid in ('K_rar20', 'K_rarpre'):
            for dirn, dr in dirs_for(mid, C, 'RK'):
                add_map('RA', mother, mid, 'SLOT', dirn, dr, (0,) + ALPHAS + (1,), HS,
                        'sameN_core|slot_shuffle_new|reverse', SLOTS[mother]['K'],
                        'K 决策的派生测量 (plan §5.7)')
                expand('RA', mother, mid, 'SLOT', dirn, dr, ALPHAS, HS, 'FALLBACK')
        for mid in ra:
            if mid in ('K_rar20', 'K_rarpre'):
                continue
            for dirn, dr in dirs_for(mid, C, 'RA'):
                add_map('RA', mother, mid, 'SWAP', dirn, dr, QS, HS,
                        'swap_random_same_E|swap_industry_matched|swap_reverse', 'edge_fixed_quota',
                        '边缘名单替换 (不统一高量剔除)')
                expand('RA', mother, mid, 'SWAP', dirn, dr, QS, HS, 'out=mother_worst')
                # 【A0 修订 v1.3, 2026-09-23】plan §5.4.2: "K 针对性路线另有'最高 K 的 m 个'换出规则, 二者分别登记,
                # 不能看收益选" —— RA 是 K 决策内的换入路线, v1.0-v1.2 只编了母体最差换出, 补最高 K 换出。
                expand('RA', mother, mid, 'SWAP', dirn, dr, QS, HS, 'out=max_K')
    # ---------------- RS: S 状态 x R 落后 (条件 SWAP) + 同行弱 / 分化 FOCAL ----------------
    rs = members_for({'S'}, C)
    for mother in ('R1', 'R2', 'A06'):
        for mid in rs:
            for st in ('P30', 'P70') + (('neg', 'pos') if C[mid]['estimand_id'].endswith('return')
                                         else ()):
                add_map('RS', mother, mid, 'SWAP_COND', 'state', st, QS, HS,
                        'swap_random_same_E_in_state|swap_industry_matched', 'edge_fixed_quota',
                        '状态内按 R_peer20 换入 (S 只作条件)')
                expand('RS', mother, 'R_peer20', 'SWAP', 'high_bad', 'reversal_domain', QS, HS,
                       'state=%s@%s' % (mid, st), extra=dict(state_member=mid, state=st))
            if mother in FOCAL_CR5 and mid in ('S_peerR20', 'S_peeriqr20', 'S_peerpos20'):
                for arm in ('all_on', 'all_off', 'real_state', 'random_state'):
                    expand('RS', mother, mid, 'FOCAL_NEW', 'state', 'weak_or_dispersed', (arm,), HS,
                           FOCAL_CR5[mother])
        for mid in REPS['R']:                                             # b=10 桥
            expand('RS', mother, mid, 'SWAP', 'high_bad', 'reversal_domain', (0.10,), HS,
                   'state=S_peerR20@P70|buffer_b10',
                   extra=dict(state_member='S_peerR20', state='P70', buffer_b=10))
    # ---------------- RL: R2 / A06 边缘摩擦 ----------------
    rl = sorted(m for m, c in C.items() if c.get('family_id') in FRICTION_FAM
                and m not in DIAGNOSTIC_ONLY) + ['K_amihud_LEGACY']
    for mother in ('R2', 'A06'):
        for mid in rl:
            add_map('RL', mother, mid, 'RL|VETO_NEW', 'high_bad', 'primary', ('edge_replace',) + KS,
                    HS, 'edge_old_score_sameM|edge_local_random', 'edge_20pct',
                    '保留最好 80%; 边缘域按成本测量选同人数')
            expand('RL', mother, mid, 'RL', 'high_bad', 'primary', ('edge_replace',), HS)
            expand('RL', mother, mid, 'VETO_NEW', 'high_bad', 'primary', KS, HS, 'light_friction')
    # ---------------- 四臂 (plan §5.6 / §5.7 中心固定; 参数逐字) ----------------
    # 【A0 修订 v1.1, 2026-09-23, 任何四臂结果产生之前】v1.0 编译器只登记了 (臂, 位置), 漏了
    # plan §5.7 写死的强度与状态: K×A α∈{.25,.5}; R×S 同行 R20 正 / 负两状态、q=.10;
    # V×O 单项 γ=.0625、联合两项各 .0625 (总 .125); T×CV 在 T 位 A/B 为 FULL 替换、AB 为 T_pair β=.5。
    # 这是对 plan 原文的忠实编译补全, 不是依据结果的改网格 (见 registry/A0_amendment_v1_1.md)。
    fourarm = [('T_level_x_CV', 'T_mean20', 'T_cv20', ('R1', 'R2', 'A06', 'A08'),
                [('full', None)]),
               ('K_resid_x_A_event', 'K_res_log', 'T_evlevel', ('R1', 'R2', 'A06'),
                [('a', 0.25), ('a', 0.5)]),
               ('R_peer_x_S_state', 'R_peer20', 'S_peerR20', ('R1', 'R2', 'A06'),
                [('state', 'pos'), ('state', 'neg')]),
               ('V_rs_x_O_on', 'V_rs20_obs', 'O_onmean5', ('R2', 'A06'), [('g', 0.0625)])]
    for name, a_, b_, mothers, params in fourarm:
        for mother in mothers:
            for pk, pv in params:
                for arm in ('A', 'B', 'AB'):
                    mem = '%s|%s' % (a_, b_) if arm == 'AB' else (a_ if arm == 'A' else b_)
                    for h in HS:
                        D.append(dict(descriptor_id='FOURARM|%s|%s|%s=%s|%s|H%d' % (name, mother, pk, pv,
                                                                                  arm, h),
                                      route_id='FOURARM', mother_id=mother, member_id=mem,
                                      axis_id='', role='FOURARM', strength=pv, policy=name,
                                      direction='fixed_center', direction_role=arm, H=h,
                                      representative=True, support_policy='',
                                      random_priority=0, hypothesis_id='Q15', fourarm=name,
                                      fourarm_param=pk))
    # ---------------- M1 (同估计对象 / 同方向 / 同 role 内先形式等权再窗等权) ----------------
    m1 = collections.defaultdict(set)
    for r in D:
        if r['role'] in ('SLOT',) and r['policy'] == 'FALLBACK':
            m1[(r['route_id'], r['mother_id'], C.get(r['member_id'], {}).get('estimand_id', ''),
                r['direction'], r['role'])].add(r['member_id'])
    n_m1 = 0
    for (route, mother, est, dirn, role), ms in sorted(m1.items()):
        if len(ms) < 2:
            continue
        for eta in ETAS:
            for h in HS:
                D.append(dict(descriptor_id='M1|%s|%s|%s|%s|eta=%s|H%d' % (route, mother, est, dirn,
                                                                         eta, h),
                              route_id='M1', mother_id=mother, member_id='|'.join(sorted(ms)),
                              axis_id='', role='M1', strength=eta, policy='consensus',
                              direction=dirn, direction_role='consensus', H=h,
                              representative=False, support_policy='', random_priority=0,
                              hypothesis_id='Q8', m1_estimand=est, m1_route=route,
                              m1_n_members=len(ms)))
                n_m1 += 1
    # ---------------- M2 (part1b; 只对 §7.1 代表) ----------------
    m2_home = {'T': ('RT', 'SLOT', ('R1', 'R2', 'A06', 'A08')), 'K': ('RK', 'SLOT', ('R1', 'R2', 'A06')),
               'V': ('RV', 'ADD_SCORE', ('R2', 'A06')), 'R': ('RR', 'SWAP', ('R1', 'R2', 'A06')),
               'O': ('RO', 'VETO_NEW', ('R1', 'R2', 'A06')), 'C': ('RC', 'SLOT', ('A06',)),
               'A': ('RA', 'SWAP', ('R1', 'R2', 'A06')), 'S': ('RS', 'SWAP', ('R1', 'R2', 'A06'))}
    for ax, reps in REPS.items():
        route, role, mothers = m2_home[ax]
        for mid in reps:
            for mother in mothers:
                for h in HS:
                    D.append(dict(descriptor_id='M2|%s|%s|%s|%s|H%d' % (route, mother, mid, role, h),
                                  route_id='M2', mother_id=mother, member_id=mid, axis_id=ax,
                                  role='M2', strength='lam_grid', policy='basis=u,u2,u*z',
                                  direction='learned', direction_role='shape', H=h,
                                  representative=True, support_policy='', random_priority=0,
                                  hypothesis_id='Q8', m2_home_route=route, m2_role=role))
    # 【A0 修订 v1.3, 2026-09-23】brief §6 四臂: "K log 条件活动残差 x 因果 event_level (α .25/.5; 单变量 M2 与
    # 双变量 M2 含一阶交互)"; plan §7.2 "K/T 分解域最多两个分量及其交互"。v1.0-v1.2 未编 -> 补:
    #   单变量 M2: basis [u, u²], u = K_res_log;  双变量 M2: basis [u1, u2, u1·u2], u2 = T_evlevel;
    #   K 槽位 FALLBACK, α ∈ {.25, .5} (与四臂同预算), 母体 R1 / R2 / A06, H 网格同主路线。
    for mother in ('R1', 'R2', 'A06'):
        for var, mem, basis in (('uni', 'K_res_log', 'basis=u,u2'),
                                ('bi', 'K_res_log|T_evlevel', 'basis=u1,u2,u1*u2')):
            for a_ in (0.25, 0.5):
                for h in HS:
                    D.append(dict(descriptor_id='M2|FOURARM_KA|%s|%s|a=%s|H%d' % (mother, var, a_, h),
                                  route_id='M2', mother_id=mother, member_id=mem, axis_id='K',
                                  role='M2', strength=a_, policy=basis, direction='learned',
                                  direction_role='shape_fourarm_%s' % var, H=h, representative=True,
                                  support_policy='', random_priority=0, hypothesis_id='Q15',
                                  m2_home_route='RK', m2_role='SLOT', fourarm='K_resid_x_A_event',
                                  m2_variant=var))
    # ---------------- 写出 ----------------
    reg = os.path.join(I.RES, 'registry')
    mp = pd.DataFrame(maprows)
    dd = pd.DataFrame(D)
    assert dd.descriptor_id.is_unique, '描述符 id 重复: %d' % int(dd.descriptor_id.duplicated().sum())
    I.atomic_write_csv(os.path.join(reg, 'need_estimator_role_map.csv'), mp)
    I.atomic_write_csv(os.path.join(reg, 'descriptors_A0.csv'), dd)
    sha = hashlib.sha256(open(os.path.join(reg, 'descriptors_A0.csv'), 'rb').read()).hexdigest()
    # 计数
    by = lambda k: dd.groupby(k).size().to_dict()
    counts = dict(
        total_descriptors=len(dd), total_map_rows=len(mp),
        by_route=by('route_id'), by_role=by('role'), by_H={str(k): v for k, v in by('H').items()},
        by_mother=by('mother_id'), by_axis=by('axis_id'),
        by_direction=by('direction'), by_support_policy=by('support_policy'),
        by_estimand=(dd.assign(est=dd.member_id.map(lambda m: C.get(m, {}).get('estimand_id', m)))
                     .groupby('est').size().to_dict()),
        representative_descriptors=int(dd.representative.sum()),
        random_paths_first_pass=int(dd.random_priority.sum()),
        m1_programs=n_m1, m2_programs=int((dd.route_id == 'M2').sum()),
        not_applicable=[dict(route='RK', mother='A08', why='A08 核只有 T 腿'),
                        dict(route='RC-core', mother='R1/R2/A08', why='无 C 核心腿; CVR 是否决 -> FOCAL'),
                        dict(route='SLOT-C', mother='R1/R2', why='无 C 核心槽位')])
    hyp = json.load(open(os.path.join(I.RES, 'registry', 'hypotheses_A0.json'))) \
        if os.path.exists(os.path.join(I.RES, 'registry', 'hypotheses_A0.json')) else None
    man = dict(round='E6i', stage='A0', version=I.VERSION,
               compiled_at=time.strftime('%Y-%m-%d %H:%M:%S'),
               descriptors_sha256=sha, counts=counts,
               representatives=REPS, grids=dict(H=HS, H_fast=HS_FAST, alpha=ALPHAS, gamma=GAMMAS,
                                                k=KS, lam=LAMS, q=QS, beta=BETAS, eta=ETAS,
                                                m2_lambda=M2_LAMS),
               hypotheses_present=hyp is not None,
               note=('共享计算只减实际计算量, 不减披露的已试假设 (plan §11.5); '
                     '方向 / 状态是描述符, 不按 Stage 1 改写 (plan §5.7)'))
    I.atomic_write_json(os.path.join(reg, 'manifest_A0.json'), man)
    print('A0: map %d 行, 描述符 %d 个 (sha %s), 代表描述符 %d, 首轮随机路径 %d'
          % (len(mp), len(dd), sha[:16], counts['representative_descriptors'],
             counts['random_paths_first_pass']))
    for k in ('by_route', 'by_role', 'by_mother', 'by_H'):
        print(' ', k, counts[k])
    print('  %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
