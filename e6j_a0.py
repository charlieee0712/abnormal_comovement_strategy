# -*- coding: utf-8 -*-
"""E6j A0 登记编译器（brief v1.2 §3 / W10 / W11；plan §4.3 / §5.10 / §5.9；A1-auto 第 1–4 项的机器对象）。
不读任何收益；只读 E6i merged_index（别名 / 暴露查找）与本轮 J 成员覆盖表。
产物（registry/）：
  rows_B.csv                 210 个 测量—方向—槽位 登记行（方向论证句、双向标记、问题卡、来源、别名）
  descriptors_P.csv          P 包 528（主五臂 312 + 列对象 216）
  descriptors_B.csv          B 包 每段 13,398（W10：α{.125,.25,.5} × H{1,2,3,5,10,15,20}）
  cs_P.csv / cs_B.csv        COMMON_SUPPORT 子 / 父（α .25 × H{3,5,10,20}）
  controls.csv               匹配 N / 同资本 / TRANSPORT / T-refit / 剂量控制 / 随机机制 的分表计数（不混进主计数）
  question_to_objects.csv    问题 → 对象（由登记行 × 网格展开）
  task_to_objects.csv        任务 → 对象（由执行任务规划器独立枚举）
  exposure_ledger.csv        selection_exposure_ledger（alias_of / historical_exposed / direction_2of1 / related_exposed）
  a0_manifest.json           计数、两表逐元组对账结果、输入 sha
两表逐元组相等且计数 = 编译器现算值时 PASS；否则 FAIL（不改设计，报 amendment）。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import itertools

import pandas as pd

import e6j_core as J

REG = os.path.join(J.RES, 'registry')
ALPHAS = (0.125, 0.25, 0.5)
H_B = (1, 2, 3, 5, 10, 15, 20)          # brief W10
H_P = (3, 5, 10, 20)                    # brief W11 / plan §4.3
H_CS = (3, 5, 10, 20)
FORMS = ('A4b', 'M_mean3_v2', 'M_union3_v2', 'A4b_CVRv5', 'M_mean3_v2_CVRv5', 'M_union3_v2_CVRv5')
MAIN_FORM = 'A4b_CVRv5'
RMOTHERS = ('R1', 'R2', 'A06')
POLICY = dict(policy_aggregation='FULL_E6I_ALL4', random_ref='R-MATCH-SRC (Z-MAP basic)', capital_ref='same_capital',
              delta=0.10, delta_sensitivity=[0.05, 0.15], policy_confirmation_status='confirmed_by_proceeding',
              main_config=dict(alpha=0.25, H=5), cost_bp=8.0)

# ------------------------------------------------------------------ 210 登记行（plan §5.10）
def _r(block, key, mid, src, direction, role, why, qs, slot='K', op='SLOT_FALLBACK', extra=''):
    return dict(block=block, row_key=key, measurement_id=mid, source=src, direction=direction, direction_role=role,
                rationale=why, hypothesis_ids='|'.join(qs), slot=slot, operator_id='%s_%s' % (op, slot), note=extra)


def rows_B():
    R = []
    # B1（12）
    R += [_r('B1', 'S_source', 'K_rar20', 'E6I', 'low_bad', 'main', '源反向方向：相对自身放量而价稳（高 rar）= 好；E6i 对照方向事后转正（已暴露）', ['Q02', 'Q03']),
          _r('B1', 'b20', 'J_B1_b20', 'J', 'high_bad', 'main', '低历史活动好：S 在同 K 层内可能主要表现为低 b（S = K0 / b 代数）', ['Q02']),
          _r('B1', 'b20', 'J_B1_b20', 'J', 'low_bad', 'competitor', '高历史活动好（关注 / 流动性竞争解释）', ['Q02']),
          _r('B1', 'a20', 'J_B1_a20', 'J', 'low_bad', 'main', '高相对活动好：同槽位检验相对放量本身，不借 A / SWAP 旧结果', ['Q02']),
          _r('B1', 'a20', 'J_B1_a20', 'J', 'high_bad', 'competitor', '高相对活动 = 拥挤 / 追涨（竞争解释）', ['Q02']),
          _r('B1', 'qCC', 'J_B1_qCC', 'J', 'low_bad', 'main', '价稳（1/(|r_cc|+ε) 高）好：拆出价稳本身是否足够', ['Q02']),
          _r('B1', 'qCC', 'J_B1_qCC', 'J', 'high_bad', 'competitor', '价动好（信息冲击延续，竞争解释）', ['Q02']),
          _r('B1', 'S20lag', 'J_B1_S20lag', 'J', 'low_bad', 'main', 'a×q 高好：同时改变基线与分母的解释拆分（J 政策 20 日至少 10 对）', ['Q02']),
          _r('B1', 'S20lag', 'J_B1_S20lag', 'J', 'high_bad', 'competitor', 'a×q 高 = 拥挤放量不涨（竞争解释）', ['Q02']),
          _r('B1', 'S60lag', 'J_B1_S60lag', 'J', 'low_bad', 'main', '60 日历史基线同构：判断常态测量而非只沿 20 日赢家解释', ['Q02', 'Q03']),
          _r('B1', 'logK0', 'J_B1_logK0', 'J', 'high_bad', 'main', '对应源 K 方向；log 改变原值 OLS 与 rank，不当恒等', ['Q02']),
          _r('B1', 'logS20lag', 'J_B1_logS20lag', 'J', 'low_bad', 'main', '对应 S 方向的 log 表示对照', ['Q02'])]
    # B2（64）
    for agg in ('POINT', 'MR3', 'MR5', 'ROS20', 'SLOPE20'):
        for z in ('TR', 'AMT'):
            for y in ('CC', 'ID', 'RANGE'):
                mid = 'J_B2_%s_%s_%s' % (agg, z, y)
                qs = ['Q10'] + (['Q04'] if agg == 'SLOPE20' else []) + (['Q06'] if agg in ('MR3', 'MR5') else [])
                main = 'low_bad' if agg == 'SLOPE20' else 'high_bad'
                comp = 'high_bad' if main == 'low_bad' else 'low_bad'
                why = ('SLOPE 方向高好（|收益| 对活动的边际响应高 = 好）' if agg == 'SLOPE20' else '源坏度方向高坏（活动 / 响应高 = 坏）')
                R.append(_r('B2', '%s_%s_%s' % (agg, z, y), mid, 'J', main, 'main', why, qs,
                            extra='K0 锚（与 K0_LEGACY 逐位同值）' if mid == 'J_B2_POINT_TR_CC' else ''))
                R.append(_r('B2', '%s_%s_%s' % (agg, z, y), mid, 'J', comp, 'competitor', '相反方向作命名竞争对照，分别登记、不事后继承', qs))
    for z in ('TR', 'AMT'):
        R.append(_r('B2', 'POINT_%s_ON' % z, 'J_B2_POINT_%s_ON' % z, 'J', 'high_bad', 'main', '隔夜部分是否本来含预测信息（不是真零因子）；K 方向高坏', ['Q10']))
        R.append(_r('B2', 'POINT_%s_ON' % z, 'J_B2_POINT_%s_ON' % z, 'J', 'low_bad', 'competitor', '相反方向命名竞争对照', ['Q10']))
    # B3-A（20）
    for y in ('CC', 'ID'):
        for w in (3, 20):
            for lam in ('0', '05', '1'):
                R.append(_r('B3A', 'Q%s_%s_W%d' % (lam, y, w), 'J_B3A_Q%s_%s_W%d' % (lam, y, w), 'J', 'high_bad', 'main',
                            'K 的高坏方向；λ = 1 严格等于 MR，λ = 0 为独立均值乘积对照，λ = .5 保留部分协动', ['Q06']))
            for d, why in (('high_bad', '解释一：协动占比高 = 活动与价稳同涨（坏）'), ('low_bad', '解释二：协动占比高 = 吸收稳定（好）')):
                R.append(_r('B3A', 'COVP_%s_W%d' % (y, w), 'J_B3A_COVP_%s_W%d' % (y, w), 'J', d, 'both_registered', why, ['Q06']))
    # B3-B（12）
    for y in ('CC', 'ID'):
        for nm in ('BETANORM', 'RHO'):
            R.append(_r('B3B', '%s_%s' % (nm, y), 'J_B3B_%s_%s' % (nm, y), 'J', 'low_bad', 'main', '主方向与 M 同为高好（尺度 / 协动解释分别记）', ['Q04']))
            R.append(_r('B3B', '%s_%s' % (nm, y), 'J_B3B_%s_%s' % (nm, y), 'J', 'high_bad', 'competitor', '相反方向命名竞争对照', ['Q04']))
        for d in ('high_bad', 'low_bad'):
            R.append(_r('B3B', 'SCALE_%s' % y, 'J_B3B_SCALE_%s' % y, 'J', d, 'both_registered', 'scale = sd(y)/sd(x) 按高好 / 高坏两向同槽位比较', ['Q04']))
    # B3-C（2）
    for y, qm in (('CC', 'K_slope20'), ('ID', 'J_B2_SLOPE20_TR_ID')):
        R.append(_r('B3C', 'MREL_%s' % y, 'J_B3C_REL_%s' % y, 'J', 'low_bad', 'main',
                    '只在新 qM（%s，M 方向低坏）与 q0 之间按留一可靠性 r 收缩：q = q0 + α·r·(qM − q0)' % qm, ['Q05'], op='SLOT_REL',
                    extra='qM=%s' % qm))
    # B4（24）
    for y in ('CC', 'ID'):
        for agg in ('ROS', 'MR'):
            for side in ('UP', 'DN'):
                R.append(_r('B4', '%s_%s_%s' % (agg, side, y), 'J_B4_%s_%s_%s' % (agg, side, y), 'J', 'high_bad', 'both_registered',
                            ('低 K_dn 好（下跌冲击 / 风险补偿）' if side == 'DN' else '源 K 方向（高坏）'), ['Q11']))
                R.append(_r('B4', '%s_%s_%s' % (agg, side, y), 'J_B4_%s_%s_%s' % (agg, side, y), 'J', 'low_bad', 'both_registered',
                            ('高 K_dn 好（下跌日供给被承接）' if side == 'DN' else '高 K_up 好（上涨日活动被吸收）'), ['Q11']))
            for d in ('high_bad', 'low_bad'):
                R.append(_r('B4', 'ASYM_%s_%s' % (agg, y), 'J_B4_ASYM_%s_%s' % (agg, y), 'J', d, 'both_registered',
                            'log K_up − log K_dn 两向分别登记（不生造不对称故事）', ['Q11']))
    # B5（64）
    for y in ('CC', 'ID'):
        for w in (20, 60):
            for ck in ('LT', 'SE'):
                for m in ('RARPRE', 'REV', 'REV5', 'U'):
                    mid = 'J_B5_%s_%s_W%d_%s' % (m, y, w, ck)
                    for d in ('high_bad', 'low_bad'):
                        why = {'RARPRE': ('事件前冻结基线的相对放量 / 价稳：低坏 = 与 S 同向（高好）', '相反：高相对活动 = 拥挤（坏）'),
                               'REV': ('事件内单位活动响应高于事件前 = 脆弱（坏）', '事件内响应高 = 信息被价格吸收（好）'),
                               'REV5': ('m = 5 收缩的 R_ev：高坏', '相反解释：高好'),
                               'U': ('高 U = 更强响应 / 信息冲击（坏）', '低 U = 相对自身过去关系的低价格响应（坏）')}[m][0 if d == 'high_bad' else 1]
                        R.append(_r('B5', '%s_%s_W%d_%s' % (m, y, w, ck), mid, 'J', d, 'both_registered', why, ['Q12', 'Q03']))
    # B6（8；T 槽位；四母体含 A08）
    for mid, src in (('J_B6_CV20', 'J'), ('J_B6_RELROLL20', 'J'), ('J_B6_DETREND20', 'J'), ('T_ewcv20', 'E6I')):
        R.append(_r('B6', mid, mid, src, 'high_bad', 'main', '原 T 语义分支：活动不稳定高 = 坏', ['Q14'], slot='T'))
        R.append(_r('B6', mid, mid, src, 'low_bad', 'competitor', '反向只作竞争诊断', ['Q14'], slot='T'))
    # B7（4；K / T 两位置）
    for slot in ('K', 'T'):
        R.append(_r('B7', 'R_peer20_%s' % slot, 'R_peer20', 'E6I', 'high_bad', 'main', '相对同业落后（低 R_peer）= 好：表达相对价格未响应', ['Q14'], slot=slot))
        R.append(_r('B7', 'R_peer20_%s' % slot, 'R_peer20', 'E6I', 'low_bad', 'competitor', '相对同业领先 = 好（延续，竞争解释）', ['Q14'], slot=slot))
    df = pd.DataFrame(R)
    df.insert(0, 'row_id', ['BR%03d' % (i + 1) for i in range(len(df))])
    df['bidirectional'] = df.groupby(['measurement_id', 'slot'])['direction'].transform('nunique') > 1
    df['mothers'] = df.block.map(lambda b: 'R1|R2|A06|A08' if b == 'B6' else 'R1|R2|A06')
    return df


def descriptors_B(rows):
    out = []
    for _, r in rows.iterrows():
        for mo in r.mothers.split('|'):
            for a in ALPHAS:
                for H in H_B:
                    out.append(dict(descriptor_id='B|%s|%s|%s|%s|%s|FALLBACK|a=%s|H%d' % (r.block, mo, r.slot, r.measurement_id, r.direction, a, H),
                                    row_id=r.row_id, block=r.block, mother=mo, slot=r.slot, measurement_id=r.measurement_id,
                                    direction=r.direction, operator_id=r.operator_id, alpha=a, H=H, parent_id=mo,
                                    main_config=(a == 0.25 and H == 5), hypothesis_ids=r.hypothesis_ids))
    return pd.DataFrame(out)


P_ARMS = {'S': ('K_rar20', 'low_bad'), 'M': ('K_slope20', 'low_bad'), 'SM': ('K_rar20+K_slope20', 'low_bad+low_bad'),
          'C1': ('K_MA3_E6F', 'high_bad')}
P_COLS = {'K_rarpre': ('K_rarpre', 'low_bad'), 'K_samt20': ('K_samt20', 'low_bad'),
          'AMT4': ('K_amt5+K_samt5+K_amt20+K_samt20', 'low_bad×4')}


def descriptors_P():
    out = []
    for f in FORMS:
        for H in H_P:
            out.append(dict(descriptor_id='P|%s|C0|-|-|a=0|H%d' % (f, H), form=f, arm='C0', kind='identity', member='-', direction='-',
                            alpha=0.0, H=H, operator_id='P_C0_IDENTITY', main_config=(H == 5), hypothesis_ids='Q13|Q16'))
        for arm, (mem, d) in P_ARMS.items():
            for a in ALPHAS:
                for H in H_P:
                    qs = ['Q13', 'Q15', 'Q16'] + (['Q01'] if f == MAIN_FORM and arm != 'SM' else []) + (['Q07'] if arm == 'SM' else []) + \
                        (['Q09'] if f.startswith('A4b') else []) + (['Q08'] if (a == 0.25 and H == 5) else [])
                    out.append(dict(descriptor_id='P|%s|%s|%s|%s|a=%s|H%d' % (f, arm, mem, d, a, H), form=f, arm=arm, kind='arm',
                                    member=mem, direction=d, alpha=a, H=H,
                                    operator_id='P_SLOT_SM_FALLBACK' if arm == 'SM' else 'P_SLOT_FALLBACK',
                                    main_config=(a == 0.25 and H == 5), hypothesis_ids='|'.join(sorted(set(qs)))))
        for col, (mem, d) in P_COLS.items():
            for a in ALPHAS:
                for H in H_P:
                    out.append(dict(descriptor_id='P|%s|COL|%s|%s|a=%s|H%d' % (f, col, d, a, H), form=f, arm='COL:' + col, kind='column',
                                    member=mem, direction=d, alpha=a, H=H,
                                    operator_id='P_SLOT_AMT4_FALLBACK' if col == 'AMT4' else 'P_SLOT_FALLBACK',
                                    main_config=False, hypothesis_ids='Q13|Q16'))
    return pd.DataFrame(out)


def cs_tables(rows):
    cs_b = []
    for _, r in rows.iterrows():
        for mo in r.mothers.split('|'):
            for H in H_CS:
                for role in ('CS_PARENT', 'CS_CHILD'):
                    cs_b.append(dict(descriptor_id='CS|B|%s|%s|%s|%s|%s|a=0.25|H%d|%s' % (r.block, mo, r.slot, r.measurement_id, r.direction, H, role),
                                     row_id=r.row_id, mother=mo, H=H, role=role))
    cs_p = []
    for f in FORMS:
        for arm, (mem, d) in P_ARMS.items():
            for H in H_CS:
                for role in ('CS_PARENT', 'CS_CHILD'):
                    cs_p.append(dict(descriptor_id='CS|P|%s|%s|%s|%s|a=0.25|H%d|%s' % (f, arm, mem, d, H, role), form=f, arm=arm, H=H, role=role))
    return pd.DataFrame(cs_b), pd.DataFrame(cs_p)


def controls():
    """分表计数（不混进主计数）：每项 = 主配置对象数 × 需要的账户数。随机路径数另按 MC 规则（1,024 起）。"""
    P_main = [(f, arm) for f in FORMS for arm in P_ARMS]            # 4 臂 × 6 形态
    rows = [dict(table='matched_N_P', objects=len(P_main), accounts_per=1, note='真实子 vs 同最终人数原核排序账户（plan §6.3 全序）'),
            dict(table='same_capital_P', objects=len(P_main) * len(H_P) * len(ALPHAS), accounts_per=2, note='子 / 母共同资本重跑（plan §7.2），全 P 网格'),
            dict(table='transport_P', objects=len(P_main), accounts_per=1, note='SRC vs TRANSPORT 配对（plan §4.1a），主配置'),
            dict(table='T_refit_A4b', objects=len([p for p in P_main if p[0].startswith('A4b')]), accounts_per=2, note='V10 / V01 诊断臂（V00 = 母、V11 = 原生子），主配置'),
            dict(table='edit_ledger_P', objects=len(P_main), accounts_per=0, note='决策编辑账本（无新账户）'),
            dict(table='transport_B_SM_MA3', objects=3 * 3, accounts_per=1, note='B 的 S / M / MA3 主配置 × R1/R2/A06'),
            dict(table='same_capital_B', objects=None, accounts_per=2, note='B 全网格 × H（与主账户同批，编译器现算）'),
            dict(table='dose_B3C', objects=2 * 3, accounts_per=2, note='COMMON-DOSE 与 r-shuffle（CC / ID × 三母体），主配置 × α 网格另跑'),
            dict(table='random_P_main', objects=len(P_main), accounts_per=None,
                 note='R-MATCH-SRC 主；R-COND / R-SCORE-P5 / R-SCORE-IID / EDIT-ENTRY / EDIT-BOTH 诊断；1,024 路径起，MCSE ≤ .03 否则 +512'),
            dict(table='random_B', objects=None, accounts_per=None,
                 note='随机三类（R-SCORE-IID≡R-MATCH-SRC 条件 / R-COND / EDIT-ENTRY）× 每登记行 × 母体；B 流式可重放')]
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 两张独立表
def question_table(rows, dP, dB):
    q = []
    for _, d in dP.iterrows():
        for h in d.hypothesis_ids.split('|'):
            q.append(dict(hypothesis_id=h, descriptor_id=d.descriptor_id, package='P'))
    rq = rows.set_index('row_id').hypothesis_ids
    for _, d in dB.iterrows():
        for h in rq[d.row_id].split('|'):
            q.append(dict(hypothesis_id=h, descriptor_id=d.descriptor_id, package='B'))
    return pd.DataFrame(q)


def task_table(rows):
    """执行任务规划器（与登记展开独立的枚举次序）：任务 = (包, 段组, 母体/形态, 槽位, 成员, 方向, α) → H 展开。"""
    t = []
    for f in FORMS:                                   # P：每形态一个 C0 任务 + 臂 × α 任务
        t.append(dict(task_id='TP|%s|C0' % f, package='P', descriptors=['P|%s|C0|-|-|a=0|H%d' % (f, H) for H in H_P]))
        for arm, (mem, d) in list(P_ARMS.items()) + [('COL:' + k, v) for k, v in P_COLS.items()]:
            for a in ALPHAS:
                pre = 'P|%s|COL|%s|%s' % (f, arm[4:], d) if arm.startswith('COL:') else 'P|%s|%s|%s|%s' % (f, arm, mem, d)
                t.append(dict(task_id='TP|%s|%s|a=%s' % (f, arm, a), package='P', descriptors=['%s|a=%s|H%d' % (pre, a, H) for H in H_P]))
    by = {}
    for _, r in rows.iterrows():
        by.setdefault((r.block, r.slot, r.measurement_id), []).append(r)
    for (block, slot, mid), rs in sorted(by.items()):
        mothers = ('R1', 'R2', 'A06', 'A08') if block == 'B6' else RMOTHERS
        for mo in mothers:
            for r in rs:
                for a in ALPHAS:
                    t.append(dict(task_id='TB|%s|%s|%s|%s|%s|a=%s' % (block, mo, slot, mid, r.direction, a), package='B',
                                  descriptors=['B|%s|%s|%s|%s|%s|FALLBACK|a=%s|H%d' % (block, mo, slot, mid, r.direction, a, H) for H in H_B]))
    return pd.DataFrame([dict(task_id=x['task_id'], package=x['package'], descriptor_id=d) for x in t for d in x['descriptors']])


# ------------------------------------------------------------------ 暴露台账
def exposure(dP, rows):
    idx = {}
    for seg in J.SEGMENTS:
        mi = pd.read_csv(os.path.join(J.E6I_RES, 'accounts', seg, 'merged_index.csv'), usecols=['descriptor_id'])
        idx[seg] = set(mi.descriptor_id)
    route = {'K_rar20': 'RA', 'K_rarpre': 'RA', 'K_slope20': 'RK', 'K_MA3_E6F': 'RK', 'K_samt20': 'RK', 'T_ewcv20': 'RT'}
    ex = []
    for _, d in dP.iterrows():
        if d.kind == 'identity':
            continue
        mem = d.member
        single = mem in route
        if d.form == MAIN_FORM and single:
            ids = {seg: '%s|R1|%s|SLOT|a=%s|%s:FALLBACK|H%d' % (route[mem], mem, d.alpha, d.direction, d.H) for seg in J.SEGMENTS}
            hit = {seg: ids[seg] in idx[seg] for seg in J.SEGMENTS}
            ex.append(dict(descriptor_id=d.descriptor_id, exposure_type='alias_of' if all(hit.values()) else 'historical_exposed_partial',
                           alias_of=ids['2010-2014'] if all(hit.values()) else '', segments_seen='|'.join(s for s in J.SEGMENTS if hit[s]),
                           historical_exposed=True, note='R1 ≡ A4b_CVRv5 exact_alias（锚 2）+ SLOT 逐格同（锚 3 T6）'))
        elif single:
            ex.append(dict(descriptor_id=d.descriptor_id, exposure_type='related_exposed', alias_of='', segments_seen='',
                           historical_exposed=False, note='同成员同方向已在 E6i R1 / R2 / A06 四段见过；本形态账户未见'))
        else:
            ex.append(dict(descriptor_id=d.descriptor_id, exposure_type='new_combination', alias_of='', segments_seen='',
                           historical_exposed=False, note='SM / AMT4 为新组合；分量已在 E6i 见过'))
    for _, d in dP.iterrows():
        if d.arm == 'S':
            ex.append(dict(descriptor_id=d.descriptor_id, exposure_type='direction_2of1', alias_of='', segments_seen='',
                           historical_exposed=True, note='S 方向 = E6i 对照方向事后转正（非未见数据的首次预测）'))
    for _, r in rows.iterrows():
        if r.source == 'E6I':
            ex.append(dict(descriptor_id='ROW|%s' % r.row_id, exposure_type='source_member_seen', alias_of='', segments_seen='',
                           historical_exposed=True, note='%s 在 E6i 已以 %s 跑过（R_peer20 在 E6i 只作 SWAP，SLOT 为新）' % (r.measurement_id, r.direction)))
        if r.measurement_id == 'J_B2_POINT_TR_CC' and r.direction == 'high_bad':
            ex.append(dict(descriptor_id='ROW|%s' % r.row_id, exposure_type='alias_of', alias_of='mother K leg (K0_LEGACY)', segments_seen='',
                           historical_exposed=True, note='K0 锚：J 原值 = K0_LEGACY 逐位（Stage 0 第 4 项 R05）→ FALLBACK 恒等，账户 = 母体，不重复计算'))
    return pd.DataFrame(ex)


def main():
    os.makedirs(REG, exist_ok=True)
    rows = rows_B(); dP = descriptors_P(); dB = descriptors_B(rows)
    cs_b, cs_p = cs_tables(rows)
    qt = question_table(rows, dP, dB); tt = task_table(rows)
    ctl = controls(); ex = exposure(dP, rows)
    # ---- 计数与对账
    blocks = rows.block.value_counts().reindex(['B1', 'B2', 'B3A', 'B3B', 'B3C', 'B4', 'B5', 'B6', 'B7']).tolist()
    exp_blocks = [12, 64, 20, 12, 2, 24, 64, 8, 4]
    n_B_expected = (len(rows) - (rows.block == 'B6').sum()) * 3 * len(ALPHAS) * len(H_B) + (rows.block == 'B6').sum() * 4 * len(ALPHAS) * len(H_B)
    q_set = set(qt.descriptor_id); t_set = set(tt.descriptor_id)
    reg_set = set(dP.descriptor_id) | set(dB.descriptor_id)
    checks = dict(
        rows_210=len(rows) == 210, blocks=blocks == exp_blocks,
        P_528=len(dP) == 528, P_main_312=int((dP.kind != 'column').sum()) == 312, P_cols_216=int((dP.kind == 'column').sum()) == 216,
        B_per_segment=len(dB) == n_B_expected, B_equals_13398=len(dB) == 13398,
        ids_unique=dP.descriptor_id.is_unique and dB.descriptor_id.is_unique,
        question_eq_task=(q_set == t_set), question_eq_registry=(q_set == reg_set),
        every_object_has_question=set(dP.descriptor_id) | set(dB.descriptor_id) <= q_set,
        main_config_everywhere=bool(dB.groupby('row_id').main_config.any().all()) and bool(
            dP[dP.kind == 'arm'].groupby(['form', 'arm']).main_config.any().all()),
        H_set=sorted(dB.H.unique().tolist()) == list(H_B), alpha_set=sorted(dB.alpha.unique().tolist()) == list(ALPHAS),
        A08_only_B6=set(dB[dB.mother == 'A08'].block) == {'B6'}, B6_only_T=set(dB[dB.block == 'B6'].slot) == {'T'},
        B7_K_and_T=set(dB[dB.block == 'B7'].slot) == {'K', 'T'})
    checks = {k: bool(v) for k, v in checks.items()}
    blocks = [int(b) for b in blocks]
    man = dict(version=J.VERSION, counts=dict(rows=len(rows), blocks=dict(zip(['B1', 'B2', 'B3A', 'B3B', 'B3C', 'B4', 'B5', 'B6', 'B7'], blocks)),
                                              P=len(dP), P_main=int((dP.kind != 'column').sum()), P_cols=int((dP.kind == 'column').sum()),
                                              B_per_segment=len(dB), CS_B=len(cs_b), CS_P=len(cs_p),
                                              question_rows=len(qt), task_rows=len(tt), tasks=int(tt.task_id.nunique()),
                                              exposure_rows=len(ex)),
               brief_B_count_13230=13230, compiled_B_count=len(dB), policy_locks=POLICY, grids=dict(alpha=ALPHAS, H_B=H_B, H_P=H_P, H_CS=H_CS),
               checks=checks, all_pass=all(checks.values()))
    outs = {}
    for name, df in (('rows_B.csv', rows), ('descriptors_P.csv', dP), ('descriptors_B.csv', dB), ('cs_B.csv', cs_b), ('cs_P.csv', cs_p),
                     ('controls.csv', ctl), ('question_to_objects.csv', qt), ('task_to_objects.csv', tt), ('exposure_ledger.csv', ex)):
        p = os.path.join(REG, name); J.atomic_write_csv(p, df); outs[name] = J.sha_file(p)
    man['outputs_sha256'] = outs
    man['src_sha256'] = {f: J.sha_file(os.path.join(J.CODE, f)) for f in ('e6j_a0.py', 'e6j_core.py')}
    J.atomic_write_json(os.path.join(REG, 'a0_manifest.json'), man)
    print(json.dumps(dict(counts=man['counts'], checks=checks), ensure_ascii=False, indent=1, default=str))
    return 0 if man['all_pass'] else 2


if __name__ == '__main__':
    sys.exit(main())
