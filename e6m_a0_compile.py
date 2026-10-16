# -*- coding: utf-8 -*-
"""E6m 阶段 N · N3 入口：A0 编译（续 e6m_a0.py 的登记 / 附属 / 比较）——附属八项、18 卡（文本逐字取自 PLAN_COPY.md §12）、
B3–B6 清单、query 注册与带 status 行骨架、固定输出骨架、政策合同转录、A1-auto 阶段 N 可判项、写出与回执。不读收益与行情。"""
import os
import re
import sys
import json
import itertools

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_a0 as A0

P6, LAND, SEM = A0.P6, A0.LAND, A0.SEM
STATUS_N = 'NOT_RUN_STAGE_N'


# ===================================================================== 附属八项（plan §10.3 / §10.3a / §9.1–§9.3）
INTERP = {
    1: '主 26,232 + 附属 384 的确定性账户；全部非母体对象各一条 MATCH_CAP_FIXED_PATH（plan §9.2"所有主账户都做"；§10.3a 附属同）',
    2: '有新增内容的主对象在 H∈{1,3,5,10,20} 的源政策随机（V_STATE 用同删除机制 DELETE_BUDGET_COND）；附属 384 在其 H 范围；OLD_RULE 登记为 NO_NEW_CONTENT_TO_PERMUTE',
    3: '全部 H5 有新增内容对象 + 主 72 在 H1/3/10/20 的对应对象（plan §10.3 第 3 项）',
    4: 'R-BAND：主 72 的 BAND 与 BAND w.10/.20 全 α（H5）；R-FILTER_LABEL：主 72 的 FILTER；R-EDIT：EDIT_MATCH α.25 × H{1,5,20}，固定换出 / 两边随机分开命名；'
       'R-MEMORY-HG / -LAG：主 72 的记忆对象；DELETE_BUDGET_COND：主 72 的 HARD 与全部 V_STATE H5（plan §9.3 末段）',
    5: 'COPY：全部 BAND_Q / BAND_BLEND / FILTER 在 H5；NATIVE_MASKFIX：Q0 / C1 × 六形态 × α3（H5）；B2 支持：Q0 / C1 × α3 × {NONE, LAG1_10} × H{1,3,5,10,20}；'
       '主 72 在 H1/3/10/20 的对应桥',
    6: 'T 重估桥：A4b 两形态 × {BAND_Q w.1/.2, BAND_BLEND w.1/.2 α.25, PRIORITY c.8, HARD c.5} × 两记忆 × H{3,5,10}（冻结源 T 系数版；完整重估 = 主对象）；'
       'V：冻结父权重删票 / 同人数剔深（720 + ALL_KNOWN 240）；HARD：同删除数剔深 / 冻结权重删票 / POST_PARENT_SAME_N（全部 HARD 在 H5 + 主 72 HARD 其余 H）',
    7: '连续状态 / 实施链：主 72 + 六母体 + 同算子 C1 对应对象（H5）× {分段重置, 允许历史内连续} × {源理论, 同模型全可成交, 源限制影子}，去掉主对象本身那一格',
    8: 'B3–B6 cell / contrast / state-clock / event / trigger 清单（b3_cells / b3_contrasts / b4_queries / b5_queries / b6_queries）',
}


def build_aux(spec, rows, D, S):
    sig = {spec.signature(r): r for r in rows}
    out = []

    def add(item, kind, owner, mech, h, note=''):
        out.append(dict(item=item, aux_kind=kind, owner_id=owner, mechanism=mech, H=int(h), note=note))
    for r in D.itertuples():
        add(1, 'DETERMINISTIC_ACCOUNT', r.desc_id, 'NONE', r.H)
        if r.block != 'PARENT':
            add(1, 'MATCH_CAP_FIXED_PATH', r.desc_id, 'NONE', r.H)
    for s in S.itertuples():
        add(1, 'DETERMINISTIC_ACCOUNT', 'SUPP:' + s.supp_id[:16], 'NONE', s.H, s.diagnostic)
        add(1, 'MATCH_CAP_FIXED_PATH', 'SUPP:' + s.supp_id[:16], 'NONE', s.H, s.diagnostic)
    for r in D[D.H.isin(LAND) & (D.block != 'PARENT')].itertuples():
        if r.block == 'OLD_RULE':
            add(2, 'POLICY_RANDOM', r.desc_id, 'NO_NEW_CONTENT_TO_PERMUTE', r.H)
        else:
            add(2, 'POLICY_RANDOM', r.desc_id, 'DELETE_BUDGET_COND' if r.block == 'V_STATE' else 'LEGACY_POLICY_RANDOM', r.H)
    for s in S[S.H.isin(LAND)].itertuples():
        add(2, 'POLICY_RANDOM', 'SUPP:' + s.supp_id[:16], 'DELETE_BUDGET_COND' if s.diagnostic == 'V_ALL_KNOWN' else 'LEGACY_POLICY_RANDOM', s.H, s.diagnostic)
    newc = D[~D.block.isin(['PARENT', 'OLD_RULE'])]
    for r in newc[newc.H == 5].itertuples():
        add(3, 'CONTENT_ISK_P5', r.desc_id, 'CONTENT_ISK_P5', 5)
    prim = [t for t in spec.primary()]
    for t in prim:
        for h in (1, 3, 10, 20):
            tt = list(t)
            tt[6] = h
            add(3, 'CONTENT_ISK_P5', A0.desc_id(sig[tuple(tt)]), 'CONTENT_ISK_P5', h, 'primary72 对应 H')
    pd_ = D[D.is_primary72]
    for r in pd_.itertuples():
        if r.operator in ('BAND_Q', 'BAND_BLEND'):
            add(4, 'MECHANISM_RANDOM', r.desc_id, 'R-BAND', 5, 'primary72')
        if r.operator in ('PRIORITY_PASS', 'HARD_CONJ'):
            add(4, 'MECHANISM_RANDOM', r.desc_id, 'R-FILTER_LABEL', 5, 'primary72')
        if r.operator == 'HARD_CONJ':
            add(4, 'MECHANISM_RANDOM', r.desc_id, 'DELETE_BUDGET_COND', 5, 'primary72 HARD')
        if r.memory == 'HG10':
            add(4, 'MECHANISM_RANDOM', r.desc_id, 'R-MEMORY-HG', 5, 'primary72')
        if r.memory in ('LAG1_10', 'PROTECTED_LAG10', 'RULE_LAG10'):
            add(4, 'MECHANISM_RANDOM', r.desc_id, 'R-MEMORY-LAG', 5, 'primary72')
    pw = pd.to_numeric(D.param, errors='coerce')
    bw = D[D.block.isin(['BAND_Q', 'BAND_BLEND']) & (D.H == 5) & pw.isin([.1, .2]) & ~D.is_primary72]
    for r in bw.itertuples():
        add(4, 'MECHANISM_RANDOM', r.desc_id, 'R-BAND', 5, 'BAND w.10/.20 全 α（H5）')
    al = pd.to_numeric(D.alpha, errors='coerce')
    for r in D[(D.block == 'EDIT_MATCH') & (al == .25) & D.H.isin([1, 5, 20])].itertuples():
        add(4, 'MECHANISM_RANDOM', r.desc_id, 'R-EDIT_FIXED_OUT', r.H)
        add(4, 'MECHANISM_RANDOM', r.desc_id, 'R-EDIT_BOTH_RANDOM', r.H)
    for r in D[(D.block == 'V_STATE') & (D.H == 5)].itertuples():
        add(4, 'MECHANISM_RANDOM', r.desc_id, 'DELETE_BUDGET_COND', 5, 'V_STATE H5 同预算控制')
    for r in D[D.block.isin(['BAND_Q', 'BAND_BLEND', 'FILTER']) & (D.H == 5)].itertuples():
        add(5, 'COPY_CONTROL', r.desc_id, 'COPY_PASS' if r.block == 'FILTER' else 'COPY_GATE_ORDER', 5, '复制 owner 缺失与规则')
    for f, p, a in itertools.product(('Q0', 'C1'), P6, (.125, .25, .5)):
        add(5, 'SUPPORT_BRIDGE', '%s|%s|NATIVE_MASKFIX|a%g' % (f, p, a), 'NATIVE_MASKFIX', 5, 'plan §4.3 / §9.2')
    for f, p, a, m, h in itertools.product(('Q0', 'C1'), P6, (.125, .25, .5), ('NONE', 'LAG1_10'), LAND):
        add(5, 'SUPPORT_BRIDGE', '%s|%s|TWO_DAY_SUPPORT|a%g|%s|H%d' % (f, p, a, m, h), 'TWO_DAY_VALID_SUPPORT_CONTROL', h, 'B2 全 α 支持 Q0 / C1')
    for r in pd_.itertuples():
        for h in (1, 3, 10, 20):
            add(5, 'PRIMARY_H_BRIDGE', r.desc_id + '@H%d' % h, 'COPY_OR_SUPPORT_BY_RECIPE', h, 'primary72 在 H1/3/10/20 的对应桥')
    combos = [('BAND_Q', .1, None, 'NONE'), ('BAND_Q', .2, None, 'NONE'), ('BAND_Q', .1, None, 'PROTECTED_LAG10'), ('BAND_Q', .2, None, 'PROTECTED_LAG10'),
              ('BAND_BLEND', .1, .25, 'NONE'), ('BAND_BLEND', .2, .25, 'NONE'), ('BAND_BLEND', .1, .25, 'PROTECTED_LAG10'),
              ('BAND_BLEND', .2, .25, 'PROTECTED_LAG10'), ('PRIORITY_PASS', .8, None, 'NONE'), ('PRIORITY_PASS', .8, None, 'RULE_LAG10'),
              ('HARD_CONJ', .5, None, 'NONE'), ('HARD_CONJ', .5, None, 'RULE_LAG10')]
    for p, (op, w, a, m), h in itertools.product(('A4b', 'A4b_CVRv5'), combos, (3, 5, 10)):
        add(6, 'T_REFIT_BRIDGE', A0.desc_id(sig[('Q0', p, op, w, a, m, h, 'ACTUAL_GATE', None)]), 'FROZEN_SOURCE_T_COEFFICIENTS', h)
    for r in D[D.block == 'V_STATE'].itertuples():
        add(6, 'V_WEIGHT_ENDS', r.desc_id, 'FROZEN_PARENT_WEIGHT_DELETE', r.H)
        add(6, 'V_SAME_N_CORE_DEEP', r.desc_id, 'SAME_N_CORE_DEEP', r.H)
    for s in S[S.diagnostic == 'V_ALL_KNOWN'].itertuples():
        add(6, 'V_WEIGHT_ENDS', 'SUPP:' + s.supp_id[:16], 'FROZEN_PARENT_WEIGHT_DELETE', s.H, 'ALL_KNOWN')
        add(6, 'V_SAME_N_CORE_DEEP', 'SUPP:' + s.supp_id[:16], 'SAME_N_CORE_DEEP', s.H, 'ALL_KNOWN')
    for r in D[(D.operator == 'HARD_CONJ') & (D.H == 5)].itertuples():
        for k in ('CORE_DEEP_SAME_DELETE_COUNT', 'FROZEN_PARENT_WEIGHT_DELETE', 'POST_PARENT_SAME_N'):
            add(6, 'HARD_CONTROL', r.desc_id, k, 5)
    for t in prim:
        if t[2] != 'HARD_CONJ':
            continue
        for h in (1, 3, 10, 20):
            tt = list(t)
            tt[6] = h
            for k in ('CORE_DEEP_SAME_DELETE_COUNT', 'FROZEN_PARENT_WEIGHT_DELETE', 'POST_PARENT_SAME_N'):
                add(6, 'HARD_CONTROL', A0.desc_id(sig[tuple(tt)]), k, h, 'primary72 HARD 其余 H')
    chain = set(pd_.desc_id)
    for p in P6:
        chain.add(A0.desc_id(sig[('K0', p, 'PARENT', None, None, 'NONE', 5, 'SOURCE', None)]))
        for m in ('NONE', 'HG10', 'LAG1_10'):
            chain.add(A0.desc_id(sig[('C1', p, 'LINEAR', None, .25, m, 5, 'SOURCE', None)]))
        for op, x, a, m in (('BAND_Q', .1, None, 'NONE'), ('BAND_Q', .1, None, 'PROTECTED_LAG10'), ('BAND_BLEND', .1, .25, 'NONE'),
                            ('BAND_BLEND', .1, .25, 'PROTECTED_LAG10'), ('PRIORITY_PASS', .8, None, 'NONE'), ('PRIORITY_PASS', .8, None, 'RULE_LAG10'),
                            ('HARD_CONJ', .5, None, 'NONE')):
            chain.add(A0.desc_id(sig[('C1', p, op, x, a, m, 5, 'ACTUAL_GATE', None)]))
    for o in sorted(chain):
        for init, ch in itertools.product(('SEGMENT_RESET', 'CONTINUOUS_ALLOWED_HISTORY'), ('SOURCE_THEORY', 'FULL_FILL_SAME_MODEL', 'SOURCE_LIMIT_SHADOW')):
            if (init, ch) != ('SEGMENT_RESET', 'SOURCE_THEORY'):
                add(7, 'STATE_CHAIN', o, '%s|%s' % (init, ch), 5)
    A = pd.DataFrame(out)
    A['aux_id'] = ['AUX%07d' % i for i in range(1, len(A) + 1)]
    A['semantic_key'] = A['item'].astype(str) + '|' + A.aux_kind + '|' + A.owner_id + '|' + A.mechanism + '|H' + A.H.astype(str)
    A['status'] = 'SOURCE_WAIT'
    return A


def aux_counts(A, bcounts):
    rows = []
    for it in range(1, 8):
        a = A[A['item'] == it]
        u = a.semantic_key.nunique()
        rows.append(dict(item=it, requested=len(a), unique_semantics=u, exact_path_alias=0, runnable=0, source_wait=u, completed=0,
                         by_kind=json.dumps(a.aux_kind.value_counts().to_dict(), ensure_ascii=False),
                         by_mechanism=json.dumps(a.mechanism.value_counts().to_dict(), ensure_ascii=False), interpretation=INTERP[it]))
    n8 = int(sum(bcounts.values()))
    rows.append(dict(item=8, requested=n8, unique_semantics=n8, exact_path_alias=0, runnable=0, source_wait=n8, completed=0,
                     by_kind=json.dumps(bcounts, ensure_ascii=False), by_mechanism='', interpretation=INTERP[8]))
    df = pd.DataFrame(rows)
    df['runnable_note'] = '阶段 N：账户级引擎在云机起不来（brief W15）；B3 先行未获授权（N8）→ 全部 SOURCE_WAIT / NOT_AUTHORIZED'
    return df


# ===================================================================== B3–B6 清单（plan §7–§8；不含收益，只有定义与骨架）
ACT = ('LOW', 'MID', 'HIGH')
PRICE = ('QUIET', 'UP', 'DOWN')
POS = ('LOW', 'MID', 'HIGH')
VOL = ('LOW', 'MID', 'HIGH')
TREND = ('UP', 'DOWN', 'MIXED')
PEER = ('STOCK_WEAK_PEER_STRONG', 'STOCK_WEAK_PEER_WEAK', 'STOCK_STRONG_PEER_STRONG', 'STOCK_STRONG_PEER_WEAK')
B3_DOMAINS = ('POOL0', 'CLEAN', 'A4B_CVRV5_GATE_IN', 'A4B_CVRV5_REJECTED')
HB3 = (1, 3, 5, 10, 20)
LABELS = ('FWD_SOURCE', 'FWD_ENDPOINT', 'FWD_LINEAR')


def build_b3():
    cells = []

    def cell(fam, dom, act_var, act, price, pos_var='NONE', pos='ALL', st_var='NONE', st='ALL', peer='ALL', extra_var='NONE', extra='ALL'):
        cid = 'B3|%s|%s|%s=%s|P=%s|%s=%s|%s=%s|PEER=%s|%s=%s' % (fam, dom, act_var, act, price, pos_var, pos, st_var, st, peer, extra_var, extra)
        cells.append(dict(cell_id=cid, family=fam, domain=dom, activity_var=act_var, activity=act, price_reaction=price, position_var=pos_var,
                          position=pos, state_var=st_var, state=st, peer_quadrant=peer, extra_var=extra_var, extra=extra))
    for dom in B3_DOMAINS:
        for a, p in itertools.product(ACT, PRICE):
            cell('F1_9CELL', dom, 'A20_PRE', a, p)
        for a, p, q in itertools.product(ACT, PRICE, POS):
            cell('F2_9x3POS', dom, 'A20_PRE', a, p, 'PRE_R20', q)
        for a, q, v in itertools.product(ACT, POS, VOL):
            cell('F3_QUIETxPOSxVOL', dom, 'A20_PRE', a, 'QUIET', 'PRE_R20', q, 'VOL3', v)
        for a, q, t in itertools.product(ACT, POS, TREND):
            cell('F4_QUIETxPOSxTREND', dom, 'A20_PRE', a, 'QUIET', 'PRE_R20', q, 'TREND3', t)
        for a, q, v in itertools.product(ACT, POS, VOL):
            cell('F5_UPxPOSxVOL', dom, 'A20_PRE', a, 'UP', 'PRE_R20', q, 'VOL3', v)
        for a, pr in itertools.product(ACT, PEER):
            cell('F6_QUIETxPEER', dom, 'A20_PRE', a, 'QUIET', peer=pr)
    for av in ('A5_PRE', 'A60_PRE'):
        for a, p in itertools.product(ACT, PRICE):
            cell('BR_9CELL_' + av, 'POOL0', av, a, p)
        for a, p, q in itertools.product(ACT, PRICE, POS):
            cell('BR_9x3POS_' + av, 'POOL0', av, a, p, 'PRE_R20', q)
    for a, p, q in itertools.product(ACT, PRICE, POS):
        cell('BR_9x3POS_DRAWDOWN20', 'POOL0', 'A20_PRE', a, p, 'DRAWDOWN_FROM_20D_HIGH', q)
    for tail, a, q in itertools.product(('CVR_BAD_TAIL', 'CVR_NON_BAD'), ACT, POS):
        cell('MIRROR_CVR', 'POOL0', 'A20_PRE', a, 'ALL', 'PRE_R20', q, extra_var='CVR_TAIL', extra=tail)
    for g, a, q in itertools.product(('GAP_UP', 'GAP_DOWN', 'GAP_ZERO'), ACT, POS):
        cell('MIRROR_GAP', 'POOL0', 'A20_PRE', a, 'ALL', 'PRE_R20', q, extra_var='OVERNIGHT_GAP', extra=g)
    C = pd.DataFrame(cells)
    C['status'] = 'NOT_AUTHORIZED_N8_OR_STAGE_S'
    C['n_dates'] = ''
    C['n_events'] = ''
    C['n_spells'] = ''
    # 对比（plan §7.3 固定优先问题；HIGH−LOW 为主，两侧对 MID 另立 ID）
    con = []

    def contrast(cid, card, desc, family_cells):
        for mt in ('U0', 'U1', 'U2'):
            for rnd in ('R_CELL_REMATCH', 'R_PAIR_SWAP'):
                con.append(dict(contrast_id=cid, card=card, description=desc, matching_id=mt, random_id=rnd, cells=family_cells,
                                labels='|'.join(LABELS), h='|'.join(map(str, HB3)), status='NOT_AUTHORIZED_N8_OR_STAGE_S'))
    for dom in B3_DOMAINS:
        for q in POS:
            for lhs, rhs in (('HIGH', 'LOW'), ('HIGH', 'MID'), ('MID', 'LOW')):
                contrast('B3C|Q10|%s|QUIET|POS=%s|%s-%s' % (dom, q, lhs, rhs), 'Q10', 'QUIET 内活动差，按前置位置', 'F2_9x3POS')
        contrast('B3C|Q10|%s|QUIET|DID_POS_HIGH-LOW|HIGH-LOW' % dom, 'Q10', '条件差之差：高位 (HIGH−LOW) − 低位 (HIGH−LOW)', 'F2_9x3POS')
        for p in ('UP', 'DOWN'):
            contrast('B3C|Q10|%s|%s|HIGH-LOW|D_MATCHED' % (dom, p), 'Q10', '同价格方向、相近 d 下高活动延续 / 反转', 'F1_9CELL')
        contrast('B3C|Q09|%s|QUIET_VS_QGOOD' % dom, 'Q09', 'raw QUIET 与中性化 Q 优组：cross-tab、共同 / 独有名单', 'F1_9CELL')
        contrast('B3C|Q11|%s|QUIET|LOW|PEER_STRONG-PEER_WEAK|STOCK_WEAK' % dom, 'Q11', '个股落后时同业强 vs 同业弱（QUIET 低活动）', 'F6_QUIETxPEER')
    for q in POS:
        contrast('B3C|Q12|CVR|POS=%s|BAD_TAIL:HIGH-LOW' % q, 'Q12', 'CVR 坏尾内活动差，按前置位置', 'MIRROR_CVR')
        for g in ('GAP_UP', 'GAP_DOWN'):
            contrast('B3C|Q12|GAP|%s|POS=%s|HIGH-LOW' % (g, q), 'Q12', 'gap 方向内活动差，按前置位置', 'MIRROR_GAP')
    K = pd.DataFrame(con)
    return C, K


def build_b4_b6(D, spec):
    sig = {spec.signature(r): r for r in spec.registry()}
    objs = list(D[D.is_primary72].desc_id) + [A0.desc_id(sig[('K0', p, 'PARENT', None, None, 'NONE', 5, 'SOURCE', None)]) for p in P6]
    objs = list(dict.fromkeys(objs))
    b4 = [dict(query_kind='EVENT_CONTRIB', object=o, window=w, status='SOURCE_WAIT') for o in objs for w in ('W1_20240115_20240223', 'W2_20240924_PM20')]
    b4 += [dict(query_kind='SIGNATURE', object=o, window='SIG%d' % s, status='SOURCE_WAIT') for o in objs for s in (1, 2, 3, 4)]
    segs = M.SEGMENTS
    b4 += [dict(query_kind='SYMDEC', object=o, window='%s_VS_%s|%s' % (a, b, sv), status='SOURCE_WAIT') for o in objs
           for a, b in itertools.combinations(segs, 2) for sv in ('VOL3', 'ACT3')]
    B4 = pd.DataFrame(b4)
    b5 = [dict(query_kind='B5A_CVR_CONDITIONAL', object='%s_CVRv5_VS_%s' % (base, base), partition=pt, H=h, status='SOURCE_WAIT')
          for base, pt, h in itertools.product(('A4b', 'M_mean3_v2', 'M_union3_v2'), ('TREND3_FORMATION', 'VOL3'), LAND)]
    b5 += [dict(query_kind='B5B_V_STATE', object=r.desc_id, partition=r.condition, H=r.H, status='SOURCE_WAIT') for r in D[D.block == 'V_STATE'].itertuples()]
    B5 = pd.DataFrame(b5)
    b6 = [dict(query_kind='EXIT_TRIGGER', object=o, trigger=t, status='SOURCE_WAIT') for o in objs
          for t in ('PRICE_BREAK_2SIGMA20', 'CVR_JUMP_INTO_P90_BAD_TAIL', 'CVR_FIRST_VISIBLE_HIGH_TAIL_BRIDGE', 'TREND_ENTERS_DOWN', 'TREND_ANY_CHANGE_BRIDGE')]
    B6 = pd.DataFrame(b6)
    return B4, B5, B6, objs


# ===================================================================== 18 卡（文本逐字取自 PLAN_COPY.md §12）
LBL = ('动机', '工作方向', '预期', '收益假设', '反解释', '判别', '更新', '读法', '限制', '边界', '检查', '更新产物')


def parse_cards():
    plan = open(M.P('PLAN_COPY.md'), encoding='utf-8').read().split('\n')
    cards = []
    for i, ln in enumerate(plan):
        m = re.match(r'^### (E6M-Q(\d\d))｜(.+)$', ln)
        if not m:
            continue
        body = []
        j = i + 1
        while j < len(plan) and not plan[j].startswith('#'):
            if plan[j].strip():
                body.append(plan[j].strip())
            j += 1
        text = ' '.join(body)
        parts = {}
        for lb in LBL:
            mm = re.search(r'\*\*%s：\*\*(.*?)(?=\*\*(?:%s)：\*\*|$)' % (lb, '|'.join(LBL)), text)
            if mm:
                parts[lb] = mm.group(1).strip()
        cards.append(dict(card='Q' + m.group(2), card_id=m.group(1), title=m.group(3), plan_line=i + 1, text=text, **{'f_' + k: parts.get(k, '') for k in LBL}))
    return pd.DataFrame(cards)


CARD_BIND = {  # 执行端编译口径：estimand / unit / parent / contrast 视图 / support / time_clock / exposure
    'Q01': ('HG10 − LAG1_10 同测量 / 母体 / α / H 的段 D 与 FULL；目标 / 库存 / 费用路径指纹', 'ann_pp', '六形态', 'Q01_HG_VS_LAG|Q01_OLDRULE_HG_VS_LAG', 'SOURCE_NATIVE_FALLBACK', 'T 收盘形成 → T+1 VWAP；H 1…20', 'SOURCE_WAIT_REGISTRY_INTERSECTION'),
    'Q02': ('BAND_Q(w) − 源 NATIVE(α)；EDIT 三账户', 'ann_pp', '六形态', 'Q02_BAND_VS_NATIVE|Q07_EDIT_PAIRS', 'OWNER_MISSING_IDENTITY_FROZEN', '同上', M.LABEL_FIRST_LOOK),
    'Q03': ('BAND_BLEND(w,α) − BAND_Q(w)（同 B / 名额 / 记忆）', 'ann_pp', '六形态', 'Q03_BLEND_VS_BANDQ|SUPP_VS_OWNER', 'OWNER_MISSING_IDENTITY_FROZEN', '同上', M.LABEL_FIRST_LOOK),
    'Q04': ('Mmean K_SLOT − ACTUAL_GATE（同 w / Q 或 BLEND25）', 'ann_pp', 'M_mean3_v2 两形态', 'Q04_SLOT_VS_ACTUAL', 'OWNER_MISSING_IDENTITY_FROZEN', '同上', M.LABEL_FIRST_LOOK),
    'Q05': ('PRIORITY_PASS(c) − HARD_CONJ(c)（同 c / 记忆）', 'ann_pp', '六形态', 'Q05_PRIORITY_VS_HARD', 'OWNER_MISSING_IDENTITY_FROZEN', '同上', M.LABEL_FIRST_LOOK),
    'Q06': ('PROTECTED − NONE；UNPROTECTED − PROTECTED；RULE_LAG − NONE；NATIVE_METRIC − SLOT_MAPPED', 'ann_pp', '六形态', 'Q06_PROTECTED_VS_NONE|Q06_UNPROTECTED_VS_PROTECTED|Q06_RULE_LAG_VS_NONE|SUPP_VS_OWNER', 'OWNER_MISSING_IDENTITY_FROZEN', '同上', M.LABEL_FIRST_LOOK),
    'Q07': ('EDIT_LOCAL / GLOBAL / NATIVE_TRIM 两两差与对源 NATIVE', 'ann_pp', '六形态', 'Q07_EDIT_PAIRS|Q07_EDIT_VS_NATIVE', 'OWNER_MISSING_IDENTITY_FROZEN', '同上', M.LABEL_FIRST_LOOK),
    'Q08': ('两日测量 − Q0（同 α / 记忆 / H）；MAX2 − MIN2；Q0 − LAGRAW1；MAX2 − Q0 HG10', 'ann_pp', '六形态', 'Q08_TWO_DAY_VS_Q0|Q08_MAX2_VS_MIN2|Q08_Q0_VS_LAGRAW1|Q08_TWO_DAY_VS_HG10', 'TWO_DAY_BOTH_VALID_ELSE_OLD_K_MARKED', '同上', M.LABEL_FIRST_LOOK),
    'Q09': ('raw QUIET 与中性化 Q 优组的 cross-tab、共同 / 独有名单与其后收益（B3）', 'bp_per_h', 'pool0（主）/ clean / 门内 / 拒绝集', 'B3C|Q09', 'B3_POOL0_MAIN', 'T 形成 → T+1 VWAP 入场 → T+1+h；h∈{1,3,5,10,20}', 'HISTORICAL_CONDITIONAL_RESULT_EXPOSED'),
    'Q10': ('QUIET 内 HIGH−LOW 活动差的位置差之差；同方向相近 d 的活动差（B3，U0/U1/U2）', 'bp_per_h', '同上', 'B3C|Q10', 'B3_POOL0_MAIN', '同上', 'HISTORICAL_CONDITIONAL_RESULT_EXPOSED'),
    'Q11': ('个股落后时同业强 vs 弱（QUIET 低活动；B3 同业 2×2）', 'bp_per_h', '同上', 'B3C|Q11', 'B3_POOL0_MAIN', '同上', 'HISTORICAL_CONDITIONAL_RESULT_EXPOSED'),
    'Q12': ('CVR 坏尾 / gap 方向内的活动差按位置（B3 镜像）', 'bp_per_h', 'pool0', 'B3C|Q12', 'B3_POOL0_MAIN', '同上', 'HISTORICAL_CONDITIONAL_RESULT_EXPOSED'),
    'Q13': ('V 条件删除 − ALL；DOWN_MIXED − UP；对父；ALL_KNOWN 覆盖桥；同预算随机 / 剔深 / 冻结权重', 'ann_pp', 'A4b_CVRv5 / R2 / A06', 'Q13_V_COND_VS_ALL|Q13_V_DOWNMIXED_VS_UP|SUPP_VS_OWNER', 'V_VALID_AND_CONDITION（UNKNOWN 不删）', 'T 收盘形成 → T+1 VWAP；H 1…20', M.LABEL_FIRST_LOOK),
    'Q14': ('W1 / W2 固定分母事件内外贡献、剔窗条件均值、四签名、SYMDEC（B4）', 'ann_pp', '主 72 + 六母体', 'B4|EVENT_CONTRIB|SIGNATURE|SYMDEC', 'SOURCE_NATIVE_FALLBACK', '同上', 'SOURCE_WAIT_REGISTRY_INTERSECTION'),
    'Q15': ('触发后下一可执行 VWAP 退出的局部潜力（B6；不改账户）', 'ann_pp', '主 72（H5）+ 母体', 'B6|EXIT_TRIGGER', 'SOURCE_NATIVE_FALLBACK', 'T 收盘触发 → T+1 VWAP 最早可卖', 'SOURCE_WAIT_REGISTRY_INTERSECTION'),
    'Q16': ('FULL / FULL_sc / 紧区间 / CAP 分解 / 新增-消失-共同重定权', 'ann_pp', '主 72', 'PRIMARY_EXT|BASE', 'SOURCE_NATIVE_FALLBACK', 'T 收盘形成 → T+1 VWAP；H5', M.LABEL_FIRST_LOOK),
    'Q17': ('逐对象 vs 族中位、区间 / MCSE、退化随机、构造别名', 'ann_pp', '全部', 'BASE|PRIMARY_EXT', 'SOURCE_NATIVE_FALLBACK', '同上', M.LABEL_FIRST_LOOK),
    'Q18': ('用户原话 / 解释 / 采纳 / 算子 / 对照 / 结果 query / 结论范围逐项绑定（方法卡）', 'count', '全部', 'LINEAGE', 'NOT_APPLICABLE', 'NOT_APPLICABLE', 'NOT_APPLICABLE'),
}


def build_cards(C):
    K = parse_cards()
    rows = []
    views = set(C.view)
    for r in K.itertuples():
        est, unit, parent, contrast, support, clock, expo = CARD_BIND[r.card]
        cv = [v for v in contrast.split('|') if v in views]
        nbound = int(C.view.isin(cv).sum() + (C.card == r.card).sum() * 0)
        counter = r.f_反解释 or ''
        explicit = bool(counter)
        if not explicit:
            alt = r.f_预期 or r.f_工作方向 or r.f_检查
            counter = '（plan 未单列反解释；本卡竞争解释见原文"预期 / 更新"：%s｜%s）' % (alt, r.f_更新 or r.f_读法 or r.f_更新产物)
        rows.append(dict(card=r.card, card_id=r.card_id, title=r.title, plan_line=r.plan_line, claim_id='E6M-%s-CLAIM' % r.card,
                         source_version='plan v1.1 df20f5f4（PLAN_COPY.md 第 %d 行）' % r.plan_line, estimand=est, unit=unit, parent=parent,
                         contrast=contrast, contrast_views_in_manifest='|'.join(cv), bound_comparisons=nbound, support=support, time_clock=clock,
                         exposure=expo, counter_explanation=counter, counter_explicit_in_plan=explicit, motivation=r.f_动机,
                         prediction=r.f_工作方向 or r.f_预期 or r.f_收益假设 or r.f_检查, discriminator=r.f_判别,
                         update_rule=r.f_更新 or r.f_读法 or r.f_更新产物, card_kind='METHOD_CARD' if r.card == 'Q18' else 'QUESTION_CARD'))
    return pd.DataFrame(rows)


# ===================================================================== query 注册与骨架
COLS = {
    'ACCOUNT': ['query_id', 'desc_id', 'segment', 'D_seg_ann_pp', 'D_sc_seg_ann_pp', 'n_days', 'FULL_ann_pp', 'G4_ann_pp', 'FULL_sc_ann_pp', 'status'],
    'COMPARISON': ['query_id', 'comparison_id', 'view', 'kind', 'left_desc_id', 'right_desc_id', 'segment', 'D_ann_pp', 'se_hac_H_ann_pp', 'n_days',
                   'FULL_ann_pp', 'FULL_sc_ann_pp', 'mde80_ann_pp', 'status'],
    'B3_CELL': ['query_id', 'cell_id', 'domain', 'h', 'label', 'weighting', 'n_dates', 'n_events', 'n_spells', 'capital_decimal', 'mean_bp_per_h', 'status'],
    'B3_CONTRAST': ['query_id', 'contrast_id', 'matching_id', 'random_id', 'h', 'label', 'n_pairs', 'n_unmatched', 'mean_diff_bp_per_h', 'se_hac_bp_per_h',
                    'rand_mean_bp_per_h', 'mcse_bp_per_h', 'status'],
    'B4': ['query_id', 'object', 'window', 'D_full_ann_pp', 'cond_mean_excl_ann_pp', 'contrib_in_ann_pp', 'contrib_out_ann_pp', 'status'],
    'B5': ['query_id', 'object', 'partition', 'H', 'gross_contrib_ann_pp', 'fee_ann_pp', 'n_days', 'status'],
    'B6': ['query_id', 'object', 'trigger', 'trigger_rate_decimal', 'potential_gross_ann_pp', 'fee_proxy_ann_pp', 'restricted_inventory_days', 'status'],
    'FACT': ['query_id', 'desc_id', 'segment', 'fact', 'value', 'unit', 'status'],
    'LINEAGE': ['query_id', 'card', 'user_quote', 'cc_interpretation', 'adopted', 'operator', 'control', 'result_query', 'scope', 'status'],
}


def build_queries(cards, C, D, B3C, B3K, B4, B5, B6):
    q = []

    def add(qid, card, title, kind, table, rule, n):
        q.append(dict(query_id=qid, card=card, title=title, schema=kind, machine_table=table, object_rule=rule, n_objects=int(n), unit=COLS[kind][3] if kind in COLS else '',
                      status=STATUS_N))
    for c in cards.itertuples():
        views = [v for v in c.contrast.split('|') if v in set(C.view)]
        if views:
            for k, v in enumerate(views):
                add('E6M-%s-%s' % (c.card, chr(ord('a') + k)), c.card, '%s：%s' % (c.title, v), 'COMPARISON', 'comparison_stats_<段>.csv', 'view == %s' % v,
                    (C.view == v).sum())
        nxt = chr(ord('a') + len(views))
        if c.card in ('Q09', 'Q10', 'Q11', 'Q12'):
            add('E6M-%s-%s' % (c.card, nxt), c.card, '%s：B3 cells' % c.title, 'B3_CELL', 'b3_cells', 'card %s 相关 cell 族' % c.card, len(B3C))
            add('E6M-%s-%s' % (c.card, chr(ord(nxt) + 1)), c.card, '%s：B3 contrasts' % c.title, 'B3_CONTRAST', 'b3_pairs + b3_random',
                'contrast_id startswith B3C|%s' % c.card, (B3K.card == c.card).sum())
        elif c.card == 'Q14':
            for k, kind in enumerate(('EVENT_CONTRIB', 'SIGNATURE', 'SYMDEC')):
                add('E6M-Q14-%s' % chr(ord('a') + k), 'Q14', '%s：%s' % (c.title, kind), 'B4', 'b4_event_contrib / b4_signatures / symdec',
                    'query_kind == %s' % kind, (B4.query_kind == kind).sum())
        elif c.card == 'Q15':
            add('E6M-Q15-a', 'Q15', '%s：触发 × 对象' % c.title, 'B6', 'b6_trigger_ledger', 'all', len(B6))
        elif c.card == 'Q13':
            add('E6M-Q13-%s' % nxt, 'Q13', '%s：V 状态账本与删除预算' % c.title, 'B5', 'b5_state_ledger / b5_delete_budget', 'B5B', (B5.query_kind == 'B5B_V_STATE').sum())
        elif c.card == 'Q12':
            pass
        elif c.card == 'Q16':
            add('E6M-Q16-c', 'Q16', '%s：CAP / 新增-消失-共同重定权' % c.title, 'FACT', 'weight_change_attribution / match_cap_ledger', 'primary72', D.is_primary72.sum())
        elif c.card == 'Q18':
            add('E6M-Q18-a', 'Q18', '%s：lineage' % c.title, 'LINEAGE', 'hypothesis_lineage.csv', 'all cards', 18)
        if c.card in ('Q02', 'Q05', 'Q06', 'Q07', 'Q08'):
            add('E6M-%s-z' % c.card, c.card, '%s：掩码层事实（附录 B）' % c.title, 'FACT', 'band_facts / filter_facts / edit_budget_ledger / two_day_support / memory_reference_ledger',
                'card objects', 0)
    add('E6M-B5A-a', 'Q12', 'B5a：现有 CVR 的条件价值（Trend / Vol 拆）', 'B5', 'b5_state_ledger', 'B5A', (B5.query_kind == 'B5A_CVR_CONDITIONAL').sum())
    Q = pd.DataFrame(q)
    if Q.query_id.duplicated().any():
        raise RuntimeError('query_id 重复：%s' % list(Q.query_id[Q.query_id.duplicated()]))
    return Q


FIXED_E6L = ['source_lineage', 'kernel_contracts', 'memory_contracts', 'hypothesis_lineage', 'candidate72', 'dose72', 'comparison_manifest', 'policy_profiles',
             'memory_age_daily', 'state_clock_ledger', 'turn_cost_frontier', 'risk_tight_bounds', 'random_refs', 'mc_precision', 'completion_coverage',
             'paired_mde80_deriv', 'state_unknown_days', 'inventory_saturation', 'membership_age_ledger', 'frontier_dose_tilt']
NOT_CARRIED = {'kernel_contracts': 'E6l 平滑核合同；E6m 无平滑核对象', 'paired_mde80_deriv': 'MDE 只是列（plan §1.3 / §9.5），不单列事实表',
               'inventory_saturation': 'INV（P52）本轮不做', 'membership_age_ledger': 'E6l 记忆年龄专表；E6m 记忆引用改记 memory_reference_ledger',
               'frontier_dose_tilt': 'E6l 剂量倾斜前沿；E6m 前沿并入 turn_cost_frontier / risk_tight_bounds'}
RENAME = {'candidate72': 'primary72', 'dose72': 'neighborhood_panels'}
NEW_FIXED = ['band_facts', 'filter_facts', 'edit_budget_ledger', 'two_day_support', 'copy_gate_ledger', 'memory_reference_ledger', 'four_account_ledger',
             'trefit_bridge', 'weight_change_attribution', 'match_cap_ledger', 'b3_cells', 'b3_pairs', 'b3_random', 'b3_mirror_cvr', 'b3_mirror_gap',
             'b4_event_contrib', 'b4_signatures', 'symdec', 'b5_state_ledger', 'b5_delete_budget', 'b6_trigger_ledger', 'external_inputs_E6m',
             'import_closure_E6m', 'replica_manifest_P0', 'replica_manifest_P1', 'replica_manifest_P2', 'replica_manifest_P3']
FIXED_COLS = {'b3_cells': COLS['B3_CELL'], 'b3_pairs': COLS['B3_CONTRAST'], 'b3_random': COLS['B3_CONTRAST'], 'b3_mirror_cvr': COLS['B3_CELL'],
              'b3_mirror_gap': COLS['B3_CELL'], 'b4_event_contrib': COLS['B4'], 'b4_signatures': COLS['B4'], 'symdec':
              ['query_id', 'object', 'seg_a', 'seg_b', 'state_var', 'frequency_ann_pp', 'within_ann_pp', 'one_sided_ann_pp', 'total_ann_pp', 'unknown_share_decimal', 'status'],
              'b5_state_ledger': COLS['B5'], 'b5_delete_budget': ['query_id', 'object', 'H', 'delete_count', 'same_n_core_deep_ann_pp', 'random_ann_pp', 'status'],
              'b6_trigger_ledger': COLS['B6']}


def fixed_outputs():
    rows = []
    for t in FIXED_E6L:
        if t in NOT_CARRIED:
            rows.append(dict(table=t, origin='E6L_FIXED', carried=False, e6m_name='', reason=NOT_CARRIED[t]))
        else:
            rows.append(dict(table=t, origin='E6L_FIXED', carried=True, e6m_name=RENAME.get(t, t), reason=''))
    for t in NEW_FIXED:
        rows.append(dict(table=t, origin='E6M_BRIEF_§9_OR_APPENDIX_E', carried=True, e6m_name=t, reason=''))
    F = pd.DataFrame(rows)
    F['columns'] = F.e6m_name.map(lambda t: '|'.join(FIXED_COLS.get(t, ['query_id', 'object', 'segment', 'metric', 'value', 'unit', 'aggregation', 'support', 'status'])) if t else '')
    return F


def write_skeletons(Q, F, B3C, B3K):
    sk = M.P('reports_skeleton')
    os.makedirs(os.path.join(sk, 'queries'), exist_ok=True)
    os.makedirs(os.path.join(sk, 'fixed'), exist_ok=True)
    n = 0
    for r in Q.itertuples():
        cols = COLS[r.schema]
        row = {c: '' for c in cols}
        row['query_id'] = r.query_id
        row['status'] = STATUS_N
        M.atomic_write_csv(os.path.join(sk, 'queries', '%s.csv' % r.query_id), pd.DataFrame([row], columns=cols))
        n += 1
    for r in F[F.carried].itertuples():
        cols = r.columns.split('|')
        if r.e6m_name == 'b3_cells':
            df = pd.DataFrame({c: '' for c in cols}, index=range(len(B3C)))
            df['query_id'] = 'B3_CELLS'
            df['cell_id'] = B3C.cell_id.values
            df['domain'] = B3C.domain.values
            df['status'] = B3C.status.values
        elif r.e6m_name in ('b3_pairs', 'b3_random'):
            df = pd.DataFrame({c: '' for c in cols}, index=range(len(B3K)))
            df['query_id'] = 'B3_CONTRASTS'
            for c in ('contrast_id', 'matching_id', 'random_id', 'status'):
                df[c] = B3K[c].values
        else:
            row = {c: '' for c in cols}
            row['query_id'] = r.e6m_name
            row['status'] = STATUS_N
            df = pd.DataFrame([row], columns=cols)
        M.atomic_write_csv(os.path.join(sk, 'fixed', '%s.csv' % r.e6m_name), df)
        n += 1
    return n


def render_query(table, columns):
    """报告生成器取列合同（E6l E01 教训；brief A9）：缺列报错，不写空表。"""
    miss = [c for c in columns if c not in table.columns]
    if miss:
        raise KeyError('登记 query 缺列：%s' % miss)
    if len(table) == 0:
        raise ValueError('登记 query 印出 0 行')
    return table[columns]


# ===================================================================== 政策合同转录（W12；原件 SOURCE_WAIT）
def policy_profiles():
    return dict(source='E6m brief §6 + E6l brief §6（文本转录）；PX1–PX8 原件 = E6l registration/policy_profiles_E6l.json（SOURCE_WAIT，47 恢复后逐句对原件）',
                policy_provisional=False, delta_main=0.10,
                conditions=dict(c='四段 D ≥ −.10', d='years_pos ≥ 12/17（10/17 敏感列并印）', e_capital='sign(FULL) = sign(FULL_sc)，tol 1e−9',
                                e_random='两后段 rmr ≥ 2·MCSE；未排 → RANDOM_NOT_SCHEDULED；OLD_RULE → NO_NEW_CONTENT_TO_PERMUTE',
                                f='A5 κ.5 后四段 ≥ −.10（A10 κ1 压力列）', positive='≥ +.10'),
                judgement_order=['c', 'd', 'f', 'positive', 'e_capital', 'e_random', 'size(profile)'],
                size_profiles=dict(formal='PROPOSED_PORT3_T（形成日 T clean 市值分位；四段组合层紧区间 ⊂ [−3, +3]）',
                                   printed=['LEGACY_EDIT5', 'PROPOSED_PORT3_LAG1', 'EXEC_DISCLOSE_ONLY', 'EXEC_LEADER_VS_PARENT'],
                                   leader='只披露', legacy_edit5_undefined='只在有编辑日的段上判；四段全无编辑 → UNDEFINED'),
                three_sentence_addition='PX1：只对原生四测量 + SM；含 Q 的新规则不自动得资格（plan §11.1）',
                evidence_columns=['policy_pass', 'economic_improvement', 'mechanism_status', 'new_evidence', 'replacement_authorized', 'deployment_authorized', 'exposure'],
                deployment_authorized=False, new_route_replacement_preference_status='NOT_AUTHORIZED',
                second_evaluation_rule='SECOND_EVALUATION_SAME_HISTORY 不进本轮新证据栏',
                status_words_forbidden=list(M.FORBIDDEN_STATUS), no_new_gates='IC / 名单重叠 / 随机全赢 / 三段 FULL_sc / 显著性 / 机制确认 / 压力窗口不亏都不是门（plan §11.1）',
                random=dict(first_paths=1024, topup=512, cap=8192, mcse_target_ann_pp=0.03, MC_Z=2.0),
                bootstrap=dict(reps=2000, block_lengths=[20, 60]), hac_lags=['H', 'max(2H,20)', 60], original_status='SOURCE_WAIT')


# ===================================================================== A1-auto 阶段 N 可判项（附录 A1-auto；E6l 十二项 + ⑬–⑳）
def a1_auto(spec, rows, D, S, C, A, cards, Q, F, B3C, B3K, pol, nskel):
    res = []

    def chk(item, what, ok, detail=''):
        st = 'SOURCE_WAIT' if ok is None else ('PASS' if ok else 'FAIL')
        res.append(dict(item=str(item), check=what, status=st, detail=str(detail)[:600]))
    spec_rows = spec.registry()
    sem_spec = {spec.semantic_id(r) for r in spec_rows}
    tup_spec = {spec.signature(r) for r in spec_rows}
    tup_D = {tuple(None if (v == 'NOT_APPLICABLE') else v for v in t) for t in D[list(SEM)].itertuples(index=False, name=None)}
    reg_json = json.load(open(M.P('stage0', 'plan_tests', 'registry.json'), encoding='utf-8'))
    tup_json = {tuple(r[k] for k in SEM) for r in reg_json}
    blocks = D.block.value_counts().to_dict()
    blocks_json = pd.Series([r['block'] for r in reg_json]).value_counts().to_dict()
    chk(1, '描述符 26,232；语义元组集合 = spec 函数输出 = N2 registry.json；semantic_id 集合相同；逐块计数相同',
        len(D) == 26232 and tup_D == tup_spec == tup_json and set(D.semantic_id) == sem_spec and blocks == blocks_json and D.semantic_id.is_unique,
        json.dumps(blocks, sort_keys=True))
    sup_json = json.load(open(M.P('stage0', 'plan_tests', 'supplemental.json'), encoding='utf-8'))
    chk(1, '附属 384（NATIVE_METRIC_LAG 72 / COPY_NATIVE_METRIC_LAG 72 / V_ALL_KNOWN 240）= N2 supplemental.json（owner × diagnostic）',
        len(S) == 384 and set(zip(S.owner_semantic_id, S.diagnostic)) == {(r['owner'], r['diagnostic']) for r in sup_json},
        json.dumps(S.diagnostic.value_counts().to_dict()))
    cmp_json = json.load(open(M.P('stage0', 'plan_tests', 'comparison.json'), encoding='utf-8'))
    base = C[C.view == 'BASE']
    chk(1, '基础比较 43,428 = N2 comparison.json（left, right, kind 逐条）；全部比较两端存在',
        len(base) == 43428 and set(zip(base.left, base.right, base.kind)) == {(e['left'], e['right'], e['kind']) for e in cmp_json}
        and not (C.left_desc_id == 'MISSING').any() and not (C.right_desc_id == 'MISSING').any(),
        json.dumps(C.view.value_counts().to_dict(), ensure_ascii=False))
    chk(1, 'primary72：72 行、每母体 12 配方、全部在登记表', int(D.is_primary72.sum()) == 72 and D[D.is_primary72].groupby('parent').size().eq(12).all())
    chk(1, '任务键（语义部分）唯一；暴露标签覆盖全部描述符', D.task_key_semantic.is_unique and D.exposure.ne('').all(), json.dumps(D.exposure.value_counts().to_dict()))
    chk(2, '政策合同转录：PORT3_T 正式；四列并印；LEADER 只披露；LEGACY_EDIT5 未定义段 = UNDEFINED；policy_provisional = false',
        pol['size_profiles']['formal'].startswith('PROPOSED_PORT3_T') and pol['policy_provisional'] is False and 'UNDEFINED' in pol['size_profiles']['legacy_edit5_undefined'])
    chk(2, 'PX1–PX8 原件逐句对（E6l policy_profiles_E6l.json）', None, 'E6l 结果目录未到（47 / P0）')
    plan = open(M.P('PLAN_COPY.md'), encoding='utf-8').read().split('\n')
    chk(3, '18 张卡；标题行与 PLAN_COPY 原文逐行相同', len(cards) == 18 and all(plan[r.plan_line - 1] == '### %s｜%s' % (r.card_id, r.title) for r in cards.itertuples()))
    chk(3, '每卡 queries 非空且都在 query 注册表', set(cards.card) <= set(Q.card), json.dumps(Q.card.value_counts().sort_index().to_dict()))
    nb = {r.card: int((C.view.isin(r.contrast_views_in_manifest.split('|'))).sum()) if r.contrast_views_in_manifest else 0 for r in cards.itertuples()}
    b3b = {c: int((B3K.card == c).sum()) for c in ('Q09', 'Q10', 'Q11', 'Q12')}
    okb = all((nb[c] > 0) or (b3b.get(c, 0) > 0) or c in ('Q14', 'Q15', 'Q18') for c in nb)
    chk('3/⑬', '⑬ 每卡 ≥ 1 绑定比较（B3 卡绑 contrast；Q14 / Q15 绑 B4 / B6 清单；Q18 方法卡）；estimand / unit / contrast / 反解释字段非空',
        okb and cards[['estimand', 'unit', 'contrast', 'counter_explanation']].ne('').all().all(),
        json.dumps(dict(account_views=nb, b3=b3b), ensure_ascii=False))
    nexp = cards[~cards.counter_explicit_in_plan].card.tolist()
    chk('3/⑬b', 'plan 原文单列"反解释"的卡（执行端不代写；其余卡的反解释字段取原文"预期 / 更新"句）', len(nexp) == 0, '未单列：%s' % nexp)
    dirs = {'Q0': 'lo', 'C1': 'hi', 'S': 'lo', 'M': 'lo'}
    chk(4, '测量集合 = {Q0, C1, S, M, K0, Q_MAX2, Q_MIN2, Q_LAGRAW1, Q_MEAN2, PARKINSON}；方向（Q 族 lo；C1 hi；S / M lo）沿 E6l A1-auto 第 4 项',
        set(D.measurement) == {'Q0', 'C1', 'S', 'M', 'K0', 'Q_MAX2', 'Q_MIN2', 'Q_LAGRAW1', 'Q_MEAN2', 'PARKINSON'}, json.dumps(dirs))
    al = pd.to_numeric(D.alpha, errors='coerce')
    pw = pd.to_numeric(D.param, errors='coerce')
    chk(5, 'α 网格 {.125,.25,.5}（OLD_RULE α0）；H 1…20；w {.02,.05,.1,.2,.4}（BLEND 无 .02）；c {.3,.5,.7,.8,.9}；V 剂量 {.1,.2}',
        set(al.dropna()) <= {0., .125, .25, .5} and set(D.H) == set(range(1, 21)) and set(pw[D.block == 'BAND_Q']) == {.02, .05, .1, .2, .4}
        and set(pw[D.block == 'BAND_BLEND']) == {.05, .1, .2, .4} and set(pw[D.block == 'FILTER']) == {.3, .5, .7, .8, .9} and set(pw[D.block == 'V_STATE']) == {.1, .2})
    chk(5, '随机：首 1,024 / 增补 512 / 上限 8,192 / MCSE .03；δ .10；bootstrap 2,000 × 20 / 60；HAC H / max(2H,20) / 60',
        pol['random'] == dict(first_paths=1024, topup=512, cap=8192, mcse_target_ann_pp=0.03, MC_Z=2.0) and pol['delta_main'] == .1)
    chk(6, '固定输出 + 每个 query 一张骨架（空表带 status 行）', nskel == int(F.carried.sum()) + len(Q), '%d 张（固定 %d + query %d）' % (nskel, int(F.carried.sum()), len(Q)))
    newb = D[D.block.isin(A0.NEW_BLOCKS)]
    chk(7, '新算子 replacement_preference_status = NOT_AUTHORIZED；deployment_authorized 全 False；新算子暴露 = 首评标签',
        (newb.replacement_preference_status == 'NOT_AUTHORIZED').all() and (~D.deployment_authorized.astype(bool)).all() and (newb.exposure == M.LABEL_FIRST_LOOK).all())
    chk(7, 'SECOND_EVALUATION 对象 = 与 E6k / E6l 登记表真实交集', None, 'E6k / E6l registry 未到（S1）')
    v = D[D.block == 'V_STATE']
    chk('8/⑯', '⑯ V_STATE 条件 ∈ {ALL, DOWN_MIXED, UP}；附属 ALL_KNOWN 240；状态定义 = e6l_state.py（sha 记录）',
        set(v.condition) == {'ALL', 'DOWN_MIXED', 'UP'} and (S.diagnostic == 'V_ALL_KNOWN').sum() == 240, M.sha_file(os.path.join(M.CODE, 'e6l_state.py'))[:16])
    t2 = D[D.block == 'TWO_DAY']
    chk(9, '两日对象：记忆 ∈ {NONE, LAG1_10}；支持 = 两日都有效、否则回旧 K 并标记', set(t2.memory) == {'NONE', 'LAG1_10'} and (t2.support == 'TWO_DAY_BOTH_VALID_ELSE_OLD_K_MARKED').all())
    nonmix = D[D.operator.isin(['BAND_Q', 'PRIORITY_PASS', 'HARD_CONJ', 'SLOT_Q']) | (D.block.isin(['V_STATE', 'LEAK_BRIDGE']))]
    mix = D[D.operator.isin(['BAND_BLEND', 'SLOT_BLEND25'])]
    chk('10/⑭', '⑭ 非混合算子 α 为空；BAND_BLEND / SLOT_BLEND25 α 有值', (nonmix.alpha == 'NOT_APPLICABLE').all() and (mix.alpha != 'NOT_APPLICABLE').all())
    mem = D[D.memory != 'NONE']
    chk('11/⑮', '⑮ 每个带记忆对象登记 memory_reference（HG = 本路径实际 G；LAG 类 = 同算子昨日自然 U）',
        (mem.memory_reference != 'NONE').all() and (D[D.memory == 'HG10'].memory_reference == 'ACTUAL_G_PREV_DAY_OWN_PATH').all()
        and D[D.memory.isin(['LAG1_10', 'PROTECTED_LAG10', 'UNPROTECTED_LAG10', 'RULE_LAG10'])].memory_reference.str.startswith('NATURAL_U').all())
    chk('⑰', '⑰ B3 每格有 status 行；每个 contrast 有匹配 ID（U0/U1/U2）与两种随机 ID',
        B3C.status.ne('').all() and set(B3K.matching_id) == {'U0', 'U1', 'U2'} and set(B3K.random_id) == {'R_CELL_REMATCH', 'R_PAIR_SWAP'}
        and B3K.groupby('contrast_id').size().eq(6).all(), '%d cells / %d contrast 行' % (len(B3C), len(B3K)))
    ext = M.P('registry', 'external_inputs_E6m.csv')
    if os.path.exists(ext):
        X = M.read_csv_keep(ext)
        chk('⑱', '⑱ 外部输入清单每行有 sha 或 SOURCE_WAIT', bool(((X.sha256 != '') | (X.status == 'SOURCE_WAIT')).all()), '%d 行' % len(X))
    else:
        chk('⑱', '⑱ 外部输入清单每行有 sha 或 SOURCE_WAIT', None, 'N6 尚未生成 external_inputs_E6m.csv（A0 之后复判）')
    bad = []
    for nm, df in (('descriptors', D), ('supplemental', S), ('comparison', C), ('aux', A), ('cards', cards), ('queries', Q), ('b3_cells', B3C), ('b3_contrasts', B3K)):
        bad += ['%s:%s=%s' % (nm, c, x) for c, x in M.scan_status_words(df.astype({c: str for c in df.columns}))]
    chk('12/⑲', '⑲ 状态词扫描（登记表与清单）无 N/A / NA / nan / null 作状态', not bad, '; '.join(bad[:8]))
    ok20 = False
    try:
        render_query(pd.DataFrame({'a': [1]}), ['a', 'b'])
    except KeyError:
        ok20 = True
    ok20b = False
    try:
        render_query(pd.DataFrame({'a': []}), ['a'])
    except ValueError:
        ok20b = True
    chk('⑳', '⑳ 生成器对缺列报错、对 0 行报错（合成缺列 / 空表各触发一次）', ok20 and ok20b)
    return pd.DataFrame(res)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--attempt', default='a1')
    args = ap.parse_args()
    task = 'N3_a0_compile' if args.attempt == 'a1' else 'N3_a0_compile_rerun' + ('' if args.attempt == 'a2' else args.attempt[1:])
    spec = A0.load_spec()
    D, rows = A0.build_descriptors(spec)
    S = A0.build_supplemental(spec, rows)
    C = A0.build_comparisons(spec, rows, D, S)
    A = build_aux(spec, rows, D, S)
    B3C, B3K = build_b3()
    B4, B5, B6, objs = build_b4_b6(D, spec)
    bcounts = {'b3_cells': len(B3C), 'b3_contrast_rows': len(B3K), 'b4_rows': len(B4), 'b5_rows': len(B5), 'b6_rows': len(B6)}
    AC = aux_counts(A, bcounts)
    cards = build_cards(C)
    Q = build_queries(cards, C, D, B3C, B3K, B4, B5, B6)
    F = fixed_outputs()
    pol = policy_profiles()
    nskel = write_skeletons(Q, F, B3C, B3K)
    reg = M.P('registry')
    outs = {}
    for nm, df in (('descriptors_E6m.csv', D), ('supplemental_E6m.csv', S), ('comparison_manifest_E6m.csv', C), ('auxiliary_manifest_E6m.csv', A),
                   ('auxiliary_counts_E6m.csv', AC), ('cards_E6m.csv', cards), ('query_registry_E6m.csv', Q), ('b3_cells_E6m.csv', B3C),
                   ('b3_contrasts_E6m.csv', B3K), ('b4_queries_E6m.csv', B4), ('b5_queries_E6m.csv', B5), ('b6_queries_E6m.csv', B6),
                   ('fixed_outputs_E6m.csv', F)):
        p = os.path.join(reg, nm)
        M.atomic_write_csv(p, df)
        outs[nm] = p
    qj = M.P('registry', 'query_registry_E6m.json')
    M.atomic_write_json(qj, dict(queries=Q.to_dict('records'), cards=cards[['card', 'card_id', 'title', 'contrast', 'estimand', 'unit']].to_dict('records')))
    pj = M.P('registration', 'policy_profiles_E6m_stageN.json')
    M.atomic_write_json(pj, pol)
    AA = a1_auto(spec, rows, D, S, C, A, cards, Q, F, B3C, B3K, pol, nskel)
    aj = M.P('registration', 'a1_auto_E6m.json')
    M.atomic_write_json(aj, dict(stage='N', written_at=M.time.strftime('%Y-%m-%d %H:%M:%S'), n_items=len(AA),
                                 counts=AA.status.value_counts().to_dict(), items=AA.to_dict('records')))
    M.atomic_write_csv(M.P('registration', 'a1_auto_E6m_stageN.csv'), AA)
    man = dict(written_at=M.time.strftime('%Y-%m-%d %H:%M:%S'), stage='N', spec_sha256=A0.SPEC_SHA, raw_id_count=len(D), block_counts=D.block.value_counts().to_dict(),
               primary72=int(D.is_primary72.sum()), supplemental=len(S), supplemental_kinds=S.diagnostic.value_counts().to_dict(),
               comparisons_base=int((C.view == 'BASE').sum()), comparisons_total=len(C), comparison_views=C.view.value_counts().to_dict(),
               aux_counts=AC[['item', 'requested', 'unique_semantics', 'exact_path_alias', 'runnable', 'source_wait', 'completed']].to_dict('records'),
               b3=dict(cells=len(B3C), contrasts=int(B3K.contrast_id.nunique()), contrast_rows=len(B3K)), b4_rows=len(B4), b5_rows=len(B5), b6_rows=len(B6),
               b4_b6_objects=len(objs), cards=len(cards), queries=len(Q), skeletons=nskel, fixed_carried=int(F.carried.sum()),
               policy_rows_expected=int(D.in_policy_table.sum()), files={k: M.sha_file(v) for k, v in outs.items()},
               a1_auto=AA.status.value_counts().to_dict())
    mj = M.P('registration', 'a0_manifest_E6m.json')
    M.atomic_write_json(mj, man)
    ok = bool((AA[AA['item'].astype(str) == '1'].status == 'PASS').all() and nskel == int(F.carried.sum()) + len(Q))   # 编译对账成功；A1-auto 结论另记（registration/a1_auto_E6m.json）
    M.write_receipt(task, list(outs.values()) + [qj, pj, aj, mj], status='SUCCEEDED' if ok else 'FAILED',
                    inputs=[M.P('stage0', 'plan_tests', f) for f in ('e6m_spec_tests.py', 'registry.json', 'supplemental.json', 'comparison.json')] + [M.P('PLAN_COPY.md')],
                    code=[__file__, A0.__file__, M.__file__], a1_auto=AA.status.value_counts().to_dict())
    print(json.dumps(dict(raw=len(D), supp=len(S), cmp_base=int((C.view == 'BASE').sum()), cmp_total=len(C), aux=len(A), cards=len(cards), queries=len(Q),
                          skeletons=nskel, b3_cells=len(B3C), b3_contrast_rows=len(B3K), a1=AA.status.value_counts().to_dict()), ensure_ascii=False))
    print(AA[AA.status != 'PASS'].to_string(max_colwidth=120))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
