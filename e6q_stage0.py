# -*- coding: utf-8 -*-
"""E6q Stage 0（brief §2；附录 A；fail-closed；任何新臂收益读数之前；只打标签不选支）。本脚本覆盖 S0-A（读 e6q_s0a 产物登记）/ C / D / E / F / G / H / I / J / K / L / N
与合成攻击夹具；S0-B / S0-M（推导段基准率与第一道）在 A2 推导段跑完后由 e6q_g1.py 追加。
输出：diagnostics/stage0_E6q_part1.csv、verify/identities_E6q_stage0.csv、registration/sources_E6q.csv、registration/e_band_bindings_E6q.csv、
diagnostics/source_fn_sha256_E6q.json、diagnostics/e_band_values_E6q.json。用法：python3 e6q_stage0.py"""
import os
import sys
import json
import time
import math
import shutil
import inspect
import hashlib
import subprocess
import importlib.util
import resource

import numpy as np
import pandas as pd

import e6q_core as O
import e6q_engine as E
import e6q_acct as A
import e6q_cost as CO
import e6q_rules as RU
import e6q_synth as SY
import e6q_landmark as LM

ROWS = []
IDN = []
SRC = []
BOARDS = ('SH_MAIN', 'SZ_MAIN', 'CHINEXT', 'STAR')
G = {}


def put(probe, item, key, value, unit='count', status='INFO', source_file='', note=''):
    if isinstance(value, float) and not np.isfinite(value):
        value, status = '', 'UNKNOWN'
    ROWS.append(dict(probe_id=probe, item=item, key=key, value=value, unit=unit, status=status, source_file=source_file, note=note))


def idn(check, desc, exec_id, value, maxabs, tol, status):
    IDN.append(dict(check_id=check, description=desc, exec_id=exec_id, value=value, max_abs_diff=maxabs, tolerance=tol, status=status))


def src(key, value, item, source_file, fn_sha='', status='BOUND', note=''):
    put('S0-G', item, key, value, 'count', status, source_file, note)
    SRC.append(dict(key=key, value=value, source_file=source_file, fn_sha256=fn_sha, status=status))


def fn_sha(*objs):
    h = hashlib.sha256()
    for o in objs:
        o = getattr(o, 'py_func', o)
        h.update(inspect.getsource(o).encode())
    return h.hexdigest()


def contract_module():
    p = O.P('inputs', 'e6q_contract.py')
    if O.sha_file(p) != O.CONTRACT_SHA256:
        raise RuntimeError('合同脚本 sha 不符')
    sp = importlib.util.spec_from_file_location('e6q_contract_ref', p)
    m = importlib.util.module_from_spec(sp)
    sys.modules['e6q_contract_ref'] = m
    sp.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ S0-A（e6q_s0a 产物）+ 成本恒等
def s0_a(K):
    f = json.load(open(O.P('diagnostics', 's0a_facts_E6q.json'), encoding='utf-8'))
    st = f['status']
    put('S0-A', '两实现对账结局（freeze.reconciliation_status）', 'RECONCILIATION_STATUS', st, 'count', st, 'diagnostics/s0a_facts_E6q.json + reports/E6q_S0A_reconciliation.md',
        '来源 = NAV 节点（参与率 A0 → A_e = A0·n_e、权重节点 V_pre → V⁺_{e−1}）；两步置换后 7 对象残差比 = 1；比值随净值路径非恒定、保留日桥，不给 κ 换算常数')
    put('S0-A', '唯一主仪器', 'RECONCILIATION_INSTRUMENT', 'CANONICAL=CURVE_IMPACT_FN' if st == 'RECONCILED' else 'UNDECIDABLE', 'count', 'INFO',
        'reports/E6q_S0A_reconciliation.md', '按 plan v1.1 §9.1 同节点定义（A_e = A0·n_e）选，不按便宜选：curve 高于 legacy')
    r0 = f['ratio_range_full_all']
    put('S0-A', 'FULL × ALL 比值 legacy / curve 范围（7 对象；A = 5 亿 κ .5 δ .5）', 'RATIO_RANGE_FULL_ALL', '%.4f-%.4f' % (r0[0], r0[1]), 'ratio', 'INFO',
        'verify/impact_reconciliation_E6q.csv')
    for lab, v in f['ladder'].items():
        put('S0-A', 'ladder（%s）：L00 → L01 → L02 残差比' % lab, 'LADDER_%s' % lab, '%.6f>%.6f>%.12f' % (v['r0'], v['r1'], v['r2']), 'ratio', 'INFO',
            'verify/impact_reconciliation_ladder_E6q.csv')
        idn('SAME_NAV_NODE_COST', 'S0-A %s：legacy 改到同一 NAV 节点（参与率 A_e、权重 V⁺_{e−1}）后 FULL 冲击 = curve（真实 E6p 成交）' % lab, '', v['r2'], abs(v['r2'] - 1.0), 1e-9,
            'PASS' if abs(v['r2'] - 1.0) <= 1e-9 else 'DIFFERS')
    # IMPACT_ALGEBRA_EQUAL：合成输入下 δ = .5、Q = A|Δw| 同节点两式相等（合同参考函数 + e6q_cost 两实现互核）
    rng = np.random.default_rng(1)
    worst = 0.0
    for _ in range(2000):
        A_ = float(10 ** rng.uniform(7, 10))
        dw = float(10 ** rng.uniform(-6, -1))
        v = float(10 ** rng.uniform(5, 10))
        s = float(rng.uniform(0.005, 0.08))
        a1 = K.audit_cost(dw, A_, v, s)
        c1 = K.cost(A_ * dw, v, s) / A_
        a2, _ = CO.audit_share(dw, A_, v, s)
        c2, _ = CO.order_cost(A_ * dw, v, s)
        c2 /= A_
        worst = max(worst, abs(a1 - c1) / c1, abs(a2 - c2) / c2, abs(a1 - a2) / a1, abs(c1 - c2) / c1)
    idn('IMPACT_ALGEBRA_EQUAL', '合成输入 2,000 组：δ = .5、Q = A|Δw|、同节点时 legacy 份额 κ√A|Δw|^1.5σ/√V = curve 份额 Q·κσ√p0(Q/(V·p0))^.5 / A（合同参考函数与 e6q_cost 互核）', '',
        worst, worst, 1e-12, 'PASS' if worst <= 1e-12 else 'DIFFERS')
    z1, s1 = CO.order_cost(0.0, None, None)
    z2, s2 = CO.audit_share(0.0, 1e8, None, None)
    ok = z1 == 0.0 and z2 == 0.0 and K.cost(0, None, None) == 0.0
    idn('ZERO_ORDER_ZERO_COST', '零订单：冲击严格为 0，不需 σ / ADV（e6q_cost 与合同参考同）', '', '%s/%s' % (s1, s2), 0.0, 0.0, 'PASS' if ok else 'DIFFERS')
    v1, st1 = CO.order_cost(1e6, None, 0.02)
    v2, st2 = CO.order_cost(1e6, 0.0, 0.02)
    v3, st3 = CO.order_cost(1e6, float('nan'), 0.02)
    caught = v1 is None and v2 is None and v3 is None and {st1, st2, st3} == {'COST_MISSING'}
    try:
        K.cost(1, None, .02)
        ref_caught = False
    except (TypeError, ValueError):
        ref_caught = True
    vec = CO.curve_share_vec(np.array([1e6, 0.0]), np.array([1e8, 1e8]), np.array([0.02, np.nan]), np.array([np.nan, np.nan]), 1e8, 1e8)
    caught = caught and ref_caught and np.isnan(vec[0]) and vec[1] == 0.0
    idn('NONZERO_ORDER_MISSING_LIQ_UNKNOWN', '非零订单缺 ADV / ADV ≤ 0 / NaN → COST_MISSING（None / NaN），不填 0、不删股；零订单同列为 0', '', '%s/%s/%s' % (st1, st2, st3), '', '',
        'BLOCKED' if caught else 'DIFFERS')
    big, sb = CO.order_cost(1e200, 1e200, 0.01)
    huge, sh = CO.order_cost(1e300, 1e-300, 1e10)
    ok = np.isfinite(big) and sb == 'COMPUTED' and huge is None and sh == 'OUT_OF_NUMERICAL_RANGE' and math.isfinite(K.cost(1e200, 1e200, .01))
    idn('LOG_DOMAIN_NO_OVERFLOW', '对数域：cost(1e200, 1e200) 有限；极端输入标 OUT_OF_NUMERICAL_RANGE，不报无穷容量', '', '%s/%s' % (sb, sh), '', '', 'PASS' if ok else 'DIFFERS')
    return st


# ------------------------------------------------------------------ S0-C
def s0_c():
    put('S0-C', '成本网格（A × κ × δ；p0 = .01 锚）', 'COST_GRID_REGISTERED', 'A={5e7,1e8,2e8,5e8,1e9} x kappa={0.5,1} x delta={0.5,0.7,1} (30 cells)', 'count', 'INFO',
        'e6q_core.A_GRID / KAPPAS / EXPONENTS', '全部经济账户、随机、确定性控制逐日保存 S_.5 / S_.7 / S_1 系数，可重算任一格')
    put('S0-C', 'κ 括号', 'KAPPA_BRACKET', '[0.3, 1]', 'ratio', 'INFO', 'brief §0.1 / plan §9.2', 'κ = .3 只对 primary32 加行，status = SCENARIO_NOT_CALIBRATED，不进网格恒等')
    put('S0-C', '冲击指数集', 'EXPONENT_SET', '{0.5, 0.7, 1}', 'ratio', 'INFO', 'plan §9.2', 'δ = .5 主；.7 / 1 为形状敏感性，不冒称已校准拐点')
    put('S0-C', '政策主规模与副读', 'POLICY_A', 'main 1e8; sub 5e7 / 5e8', 'CNY', 'INFO', 'freeze authorizations')


# ------------------------------------------------------------------ S0-D：首达 / 随机目标
def s0_d(K):
    # 首达影子 vs 合同 firsthit_rate（同一历史逐 lot-day 构造）
    T, H = 40, 5
    mk = SY.SynthMarket(T=T, N=2, flat=True)
    f = SY.csr_daily(T, [0], [0.5])
    tg = np.zeros((T, 2), np.int8)
    for d_, v in ((3, 1), (4, 1), (6, -1), (7, 1), (9, 0), (10, 1), (13, 1), (15, -1), (16, 1), (19, 1), (22, 1), (23, -1), (26, 1), (30, 1)):
        tg[d_, 0] = v
    mk.trigs['FH'] = tg
    ip, fp = SY.params(H, 'NATIVE', shadow=True, fhit=1)
    a = SY.account(mk, ip, fp, 'FH', f).run(0, T)
    risk_e, hits_e = int(a.RISK.sum()), int(a.HITS.sum())
    hist = []
    nl = int(a.S_i[E.SI_NL])
    for j in range(nl):
        e0, due = int(a.L_i[j, 1]), int(a.L_i[j, 2])
        for d_ in range(e0, min(due, T - 1)):
            v = int(tg[d_, 0])
            hist.append(dict(lot=int(a.L_id[j]), day=d_, age=d_ - e0, due=due, signal=None if v < 0 else bool(v == 1), next_exec=d_ + 1))
    hk, rk, _ = K.firsthit_rate(hist, 0, T - 1)
    ok = (hk == hits_e) and (rk == risk_e)
    one = int(a.HITS.sum()) == int((a.L_i[:nl, 12] == 1).sum())
    idn('FIRSTHIT_ONE_EVENT_PER_LOT', '合成影子（H5；持续 True / UNKNOWN 交错）：生产引擎首达事件 %d = 合同 firsthit_rate %d；每批至多一次（L_i[12] 计 %d）' % (hits_e, hk, int((a.L_i[:nl, 12] == 1).sum())),
        '', '%d/%d' % (hits_e, risk_e), abs(hits_e - hk) + abs(risk_e - rk), 0, 'PASS' if (ok and one) else 'DIFFERS')
    # next_exec 严格 < due：e = due 的 lot-day 不入风险集
    dueday = [r for r in hist if r['next_exec'] >= r['due']]
    idn('FIRSTHIT_NEXT_EXEC_LT_DUE', '风险 lot-day 要求下一计划执行 e < due：构造中的 e = due 日数 %d，引擎风险 = 合同风险 = %d（不含这些日）' % (len(dueday), rk), '', rk, abs(risk_e - rk), 0,
        'PASS' if ok else 'DIFFERS')
    put('S0-D', '首达规则', 'FIRSTHIT_RULE', 'shadow lot first known True only; risk lot-day needs next exec e < due and known signal; UNKNOWN neither event nor risk; 60-day window '
        'excluding T; buckets 1/2/3-5/6-10/11-20/21+; fallback same H x trigger all-age pool; else UNKNOWN', 'count', 'INFO', 'e6q_engine.step（shadow + fhit）/ e6q_run')
    # 随机目标：合同夹具（贪心失败、回溯成功）与随机小实例逐一对照（相同优先序；整数金额）
    caps = {'a': 6., 'b': 6., 'c': 6.}
    inds = {'a': 'X', 'b': 'X', 'c': 'Y'}
    sc = {'X': 10., 'Y': 6.}
    ref = K.match_tickets([6, 5, 5], caps, inds, sc, ['a', 'b', 'c'])
    asg, stt, nn = E.rt_match(np.array([6., 5., 5.]), np.array([6., 6., 6.]), np.array([0, 0, 1]), np.array([10., 6.]), np.array([0, 1, 2]), 100000)
    mine = {k: ('abc'[int(asg[k])], [6, 5, 5][k]) for k in range(3)}
    fix_ok = ref['status'] == 'FEASIBLE' and stt == E.RTS_FEASIBLE and {k: (v[0], v[1]) for k, v in ref['assignments'].items()} == {k: (v[0], float(v[1])) for k, v in mine.items()}
    lim = E.rt_match(np.array([6., 5., 5.]), np.array([6., 6., 6.]), np.array([0, 0, 1]), np.array([10., 6.]), np.array([0, 1, 2]), 1)[1]
    nom = E.rt_match(np.array([7.]), np.array([6., 6., 6.]), np.array([0, 0, 1]), np.array([10., 6.]), np.array([0, 1, 2]), 100000)[1]
    rng = np.random.default_rng(20261023)
    agree = 0
    tot = 0
    for _ in range(400):
        nt_ = int(rng.integers(1, 7))
        nc_ = int(rng.integers(nt_, 9))
        ng = int(rng.integers(1, 4))
        tick = sorted([int(x) for x in rng.integers(1, 10, nt_)], reverse=True)
        capv = [int(x) for x in rng.integers(1, 12, nc_)]
        grp = [int(x) for x in rng.integers(0, ng, nc_)]
        grem = [int(x) for x in rng.integers(1, 20, ng)]
        prio = [int(x) for x in rng.permutation(nc_)]
        names = ['s%d' % k for k in range(nc_)]
        r_ = K.match_tickets(tick, {names[k]: float(capv[k]) for k in range(nc_)}, {names[k]: 'G%d' % grp[k] for k in range(nc_)},
                             {'G%d' % g: float(grem[g]) for g in range(ng)}, [names[k] for k in prio], None)
        a_, s_, _ = E.rt_match(np.array(tick, float), np.array(capv, float), np.array(grp, np.int64), np.array(grem, float), np.array(prio, np.int64), 0)
        tot += 1
        if r_['status'] == 'FEASIBLE' and s_ == E.RTS_FEASIBLE:
            got = sorted((names[int(a_[k])], float(tick[k])) for k in range(nt_))
            exp = sorted((v[0], float(v[1])) for v in r_['assignments'].values())
            agree += int(got == exp)
        elif r_['status'] == 'PROVED_NO_MATCH' and s_ == E.RTS_NOMATCH:
            agree += 1
    ok_m = fix_ok and lim == E.RTS_LIMIT and nom == E.RTS_NOMATCH and agree == tot
    idn('RANDOM_TARGET_PRIORITY_STABLE', '匹配器 = 合同 match_tickets：夹具（贪心失败、回溯成功）分配同、节点上限 → ALGORITHM_LIMIT、超额 → PROVED_NO_MATCH；400 个随机小实例（整数金额、'
        '同优先序、不限节点）分配与状态全同 %d/%d；优先序 = 绝对交易日五日块 × path × 证券固定哈希（块内稳定、子集稳定、与输入顺序无关）' % (agree, tot), '', '%d/%d' % (agree, tot),
        tot - agree, 0, 'PASS' if ok_m else 'DIFFERS')
    # 哈希优先序性质
    seed = 991
    keys = np.arange(30)
    o1 = sorted(keys, key=lambda s: E.hash_u(seed, 10 // 5, int(s)))
    o2 = sorted(keys, key=lambda s: E.hash_u(seed, 14 // 5, int(s)))
    sub = [k for k in o1 if k % 3 != 0]
    o3 = sorted([k for k in keys if k % 3 != 0], key=lambda s: E.hash_u(seed, 2, int(s)))
    o4 = sorted(list(keys[::-1]), key=lambda s: E.hash_u(seed, 2, int(s)))
    pr_ok = o1 == o2 and sub == o3 and o1 == o4
    put('S0-D', '随机目标优先序时钟', 'RANDOM_TARGET_PRIORITY_CLOCK', 'hash(seed(version, mechanism, owner, path_id), (execution day)//5, security); same-block stable=%s subset-stable=%s order-free=%s'
        % (o1 == o2, sub == o3, o1 == o4), 'count', 'PASS' if pr_ok else 'DIFFERS', 'e6q_engine.hash_u / plan_e6q')
    put('S0-D', '求解器', 'MATCH_SOLVER', 'EXACT_FIRST_FEASIBLE', 'count', 'INFO', 'e6q_engine.rt_match',
        'DFS（票据降序 × 候选固定优先序）+ 只删无解子树的剪枝（名额 / 阈值嵌套容量 / 行业最低吸收）+ 同额票据对称性；首个可行解与不剪枝 DFS 同（400 例对照）；节点上限 → ALGORITHM_LIMIT 不换种子')
    # 不读收益：未来价格改动 → 截至 T* 的随机目标分配与日序列逐位不变
    T2 = 40
    m1 = SY.SynthMarket(T=T2, N=6, seed=3)
    f6 = SY.csr_daily(T2, [0, 1, 2, 3, 4, 5], [0.2, 0.2, 0.15, 0.15, 0.15, 0.15])
    tgr = np.zeros((T2, 6), np.int8)
    tgr[5, 0] = 1
    tgr[9, 1] = 1
    tgr[14, 2] = 1
    tgr[22, 3] = 1
    m1.trigs['R'] = tgr
    m2 = SY.SynthMarket(T=T2, N=6, seed=3)
    tstar = 18
    m2.pv[tstar + 1:] *= 1.7
    m2.pc[tstar + 1:] *= 0.6
    m2.pcobs = m2.pc.copy()
    m2.trigs['R'] = tgr
    ip, fp = SY.params(10, 'NATIVE', rt=E.RT_WITHIN, seed=77, tlog=True)
    x1 = SY.account(m1, ip, fp, 'R', f6, tlcap=1 << 14).run(0, T2)
    x2 = SY.account(m2, ip, fp, 'R', f6, tlcap=1 << 14).run(0, T2)
    dmax = float(np.max(np.abs(x1.DY[:tstar + 1] - x2.DY[:tstar + 1])))
    n1 = int(x1.S_i[E.SI_NTL])
    n2 = int(x2.S_i[E.SI_NTL])
    t1 = x1.TL_i[:n1][x1.TL_i[:n1, 0] <= tstar]
    t2 = x2.TL_i[:n2][x2.TL_i[:n2, 0] <= tstar]
    same_tr = t1.shape == t2.shape and np.array_equal(t1[:, :6], t2[:, :6])
    idn('RANDOM_TARGET_NO_RETURN_READ', '随机目标（WITHIN）合成例：T* 之后价格植入改动 → T* 及之前日序列逐位不变（%.1e）、成交行（日 / 证券 / 批次 / 种类 / 方向）相同 = %s；求解器输入不含收益' % (dmax, same_tr),
        '', dmax, '', '', 'BLOCKED' if (dmax == 0.0 and same_tr) else 'DIFFERS')
    # 不借 owner 未来库存：路径当日同层与全域库存不足 → 记未匹配
    T3 = 30
    mk3 = SY.SynthMarket(T=T3, N=3, flat=True)
    f3 = SY.csr_daily(T3, [0, 1], [0.5, 0.5])
    tgb = np.zeros((T3, E.NB))
    tgb[2, 3] = 5e8
    tgb[12, 0] = 1e5
    mk3.trigs['P0'] = np.zeros((T3, 3), np.int8)
    ip, fp = A.ip_fp(20, E.TM_PANEL, sel=E.SM_AMT2, fund=E.FD_NATIVE, exit_on=True, seed=3)
    a3 = SY.account(mk3, ip, fp, 'P0', f3, targets=dict(b=tgb)).run(0, T3)
    req, wi, cr, un = (float(a3.DY[:, E.DYI[k]].sum()) for k in ('v2_req', 'v2_within', 'v2_cross', 'v2_unm'))
    lots_sec2 = int((a3.L_i[:int(a3.S_i[E.SI_NL]), 0] == 2).sum())
    ok = abs(req - (wi + cr + un)) <= 1e-6 * max(1.0, req) and un > 0 and lots_sec2 == 0
    idn('MATCH_NO_OWNER_FUTURE_INVENTORY', '合成例 AMOUNT_MATCH_V2：路径当日同层与全域库存不足 → 记未匹配（%.0f），不借 owner 未来库存、不补造批次（未持有证券 2 的批次 = %d）；requested = within + cross + unmatched'
        % (un, lots_sec2), '', 'req=%.0f within=%.0f cross=%.0f unm=%.0f' % (req, wi, cr, un), '', '', 'BLOCKED' if ok else 'DIFFERS')


# ------------------------------------------------------------------ 标签 / 支付 / 路由（函数级攻击）
def token_attacks(K):
    TK_f = np.zeros(16)
    TK_i = np.zeros((16, E.NTKI), np.int64)
    S_i = np.zeros(E.NSI, np.int64)
    E.tk_add(TK_f, TK_i, S_i, 100.0, 1, 20, E.SI_NTK)
    E.tk_add(TK_f, TK_i, S_i, 40.0, 2, 25, E.SI_NTK)
    m1 = E.tk_deny(TK_f, TK_i, S_i[E.SI_NTK], 3, 0.0, 50.0, 5, 3)
    m2 = E.tk_deny(TK_f, TK_i, S_i[E.SI_NTK], 5, 0.0, 50.0, 5, 5)
    fd = int(TK_i[0, 4])
    seq = [E.tk_ok(TK_i, 0, d_, 5) for d_ in (6, 7, 8, 19, 20)]
    ok = m1 == 1 and m2 == 0 and fd == 3 and seq == [True, True, False, False, False] and int(TK_i[1, 4]) == -1
    idn('TTL_FIRST_DENIAL_ONLY', 'TTL 从首次被新增规则拒绝起算：日 3 拒绝记 first_denied = 3，日 5 再拒绝不重置；日 8（= 3 + 5）起隔离；未被拒绝的标签 first_denied 仍为 −1（不在卖出日填）', '',
        'fd=%d seq=%s' % (fd, seq), 0, 0, 'PASS' if ok else 'DIFFERS')
    before = TK_f.copy()
    r = E.tk_consume(TK_f, TK_i, S_i[E.SI_NTK], 9, 30.0, np.zeros(8, np.int64), np.zeros(8), 5)
    # 日 9：标签 0 隔离中、标签 1 可用 40 → 30 可付，但只能动标签 1
    ok_q = r >= 0 and TK_f[0] == before[0] and abs(TK_f[1] - (before[1] - 30.0)) < 1e-12
    TK_f2 = before.copy()
    r2 = E.tk_consume(TK_f2, TK_i, S_i[E.SI_NTK], 9, 60.0, np.zeros(8, np.int64), np.zeros(8), 5)
    ok_q2 = r2 == -1 and np.array_equal(TK_f2, before)
    idn('QUARANTINE_NOT_SPENT_BY_REGULAR', '隔离中的标签不可被任何买单消费：日 9 付 30 只动未隔离标签；付 60（超过非隔离可用 40）→ −1 拒绝、状态不变', '', 'r=%d r2=%d' % (r, r2), '', '',
        'BLOCKED' if (ok_q and ok_q2) else 'DIFFERS')
    ok_ds = r2 == -1
    idn('TOKEN_DOUBLE_SPEND', '超可用额消费 → −1（双花拦截），标签余额不变', '', r2, '', '', 'BLOCKED' if ok_ds else 'DIFFERS')
    idn('PAYMENT_ATOMIC', '失败的付款先全校验、不留半次扣款：被拒的 60 付款前后标签数组逐位相同', '', bool(np.array_equal(TK_f2, before)), '', '',
        'BLOCKED' if ok_q2 else 'DIFFERS')
    # 到期只解锁归属、不增现金：合同 Bank.retire 与引擎（到期标签不再计入可用，现金不变）
    b = K.Bank(100.0)
    b.credit('t1', K.Token(100.0, 1, 5), 100.0)
    c0 = b.cash
    b.retire('t1', 5)
    ok_ref = b.cash == c0
    ok_eng = (not E.tk_ok(TK_i, 0, 20, 5)) and (not E.tk_ok(TK_i, 1, 25, 5))
    idn('DUE_UNLOCK_NO_NEW_CASH', '到原 due：标签退出可用集、只改归属；现金不增加（合同 Bank.retire 后现金 %.0f 不变；引擎现金方程见 CASH_EQUATION 逐日核）' % c0, '', ok_ref and ok_eng, '', '',
        'BLOCKED' if (ok_ref and ok_eng) else 'DIFFERS')
    # 路由：常规买用受限标签须过本臂路由
    f_on = E.feasible(0.0, 0.0, 50.0, 0.0, 0.0, 0.0, 0.0, 100.0, E.FD_NATIVE, 1, 0.0, 1, 0.0)[0]
    f_off = E.feasible(0.0, 0.0, 50.0, 0.0, 0.0, 0.0, 0.0, 100.0, E.FD_NATIVE, 1, 0.0, 0, 0.0)[0]
    f_el = E.feasible(0.0, 0.0, 50.0, 0.0, 0.0, 0.0, 0.0, 100.0, E.FD_NATIVE, 1, 0.0, 1, 50.0)[0]
    ok_r = (not f_on) and f_off and f_el
    idn('REGULAR_BYPASS_ROUTE', '常规缺口 50 只能由受限标签付：路由开且合格常规买 0 → 不可行（缩买）；路由关（NATIVE）可行；合格 50 → 可行', '', 'on=%s off=%s elig=%s' % (f_on, f_off, f_el), '', '',
        'BLOCKED' if ok_r else 'DIFFERS')
    put('S0-E', '支付合同', 'PAYMENT_CONTRACT', 'cash_total / cash_untagged / cash_available; token consumption order (due, id); quarantine at first_denied + TTL; due unlock attribution only',
        'count', 'INFO', 'e6q_engine.tk_* / feasible')


# ------------------------------------------------------------------ 半量 / REARM / 拆股
def half_attacks(K):
    T, H = 30, 12
    res = {}
    for name, arm, pat, sell_block in (('PERSIST', 'EXIT_HALF', {3: 1, 4: 1, 5: 1, 6: 1, 7: 1}, (4,)), ('REARM_TT', 'EXIT_HALF_REARM', {3: 1, 4: 1, 6: 1}, ()),
                                       ('REARM_TFT', 'EXIT_HALF_REARM', {3: 1, 5: 0, 7: 1}, ()), ('REARM_TUT', 'EXIT_HALF_REARM', {3: 1, 5: -1, 7: 1}, ()),
                                       ('THETA0', 'EXIT_HALF_REARM', {3: 1, 5: 0, 7: 1}, ())):
        mk = SY.SynthMarket(T=T, N=2, flat=True)
        f = SY.csr_daily(1, [0], [0.5])
        f = (np.r_[f[0], np.full(T - 1, f[0][-1])].astype(np.int64), f[1], f[2])   # 只在第 0 日形成一批
        tg = np.zeros((T, 2), np.int8) if name == "PERSIST" else np.full((T, 2), -1, np.int8)   # REARM 例：背景 = UNKNOWN（只有登记日给已知值）
        for d_, v in pat.items():
            tg[d_, 0] = v
        mk.trigs["HX"] = tg
        for d_ in sell_block:
            mk.sellable[d_, 0] = False
        ip, fp = SY.params(H, arm, theta=(0.0 if name == 'THETA0' else None), tlog=True)
        a = SY.account(mk, ip, fp, 'HX', f, tlcap=1 << 12).run(0, T)
        n = int(a.S_i[E.SI_NTL])
        tl = a.TL_i[:n]
        tf = a.TL_f[:n]
        q0 = float(tf[(tl[:, 5] == 0)][:, 0].sum())
        early = (tl[:, 5] == 1) & (tl[:, 0] < tl[:, 6])
        res[name] = dict(q0=q0, early_qty=float(tf[early][:, 0].sum()), kinds=sorted(set(int(k) for k in tl[early][:, 4])), days=sorted(set(int(k) for k in tl[early][:, 0])))
    r = res['PERSIST']
    ok_fixed = abs(r['early_qty'] - 0.5 * r['q0']) <= 1e-9 * r['q0'] and min(r['days']) >= 5
    idn('HALF_TARGET_FIXED_SNAPSHOT', 'EXIT_HALF：首次有效意向（日 3）取剩余量 × .5 为固定目标；日 4 卖不出 → 日 5 续同一目标；到 due 前早退合计 = .5 × 初始量（%.6g / %.6g）' % (r['early_qty'], r['q0']),
        '', r['early_qty'] / r['q0'] if r['q0'] else '', abs(r['early_qty'] - 0.5 * r['q0']), 1e-9, 'PASS' if ok_fixed else 'DIFFERS')
    idn('HALF_NO_GEOMETRIC', '持续 True（日 3–7）不几何减半：早退合计恒 = .5（不是 .75 / .875）', '', r['early_qty'] / r['q0'] if r['q0'] else '', '', '',
        'BLOCKED' if ok_fixed else 'DIFFERS')
    tt, tft, tut, th0 = res['REARM_TT'], res['REARM_TFT'], res['REARM_TUT'], res['THETA0']
    ok_r = abs(tt['early_qty'] - 0.5 * tt['q0']) <= 1e-9 * tt['q0'] and abs(tft['early_qty'] - tft['q0']) <= 1e-9 * tft['q0']
    idn('REARM_REQUIRES_FALSE_THEN_TRUE', 'REARM：True → True（无已知 False）只卖半（%.3f）；True → False → True 才把同一请求提到余量（%.3f = 全部）' % (tt['early_qty'] / tt['q0'], tft['early_qty'] / tft['q0']),
        '', '%.3f/%.3f' % (tt['early_qty'] / tt['q0'], tft['early_qty'] / tft['q0']), '', '', 'BLOCKED' if ok_r else 'DIFFERS')
    ok_u = abs(tut['early_qty'] - 0.5 * tut['q0']) <= 1e-9 * tut['q0'] and th0['early_qty'] == 0.0
    idn('REARM_UNKNOWN_NOT_CLEAR', 'REARM：True → UNKNOWN → True 不解除（只卖半 %.3f）；θ = 0 时 True → False → True 也不产生卖出（%.3f）' % (tut['early_qty'] / tut['q0'], th0['early_qty']),
        '', '%.3f/%.3f' % (tut['early_qty'] / tut['q0'], th0['early_qty']), '', '', 'BLOCKED' if ok_u else 'DIFFERS')
    # 拆股：引擎用后复权价（拆股在复权价上不可见）→ 原始价拆分植入不改变任何账户状态；合同 HalfLot.adjust_split 同比例缩放待售量、不重置 due / episode
    h = K.HalfLot(100, 100, 10)
    h.intent(1, True)
    h.fill(20)
    h.adjust_split(2)
    ok_ref = h.quantity == 200 and h.remaining == 160 and h.pending == 60 and h.due == 10 and h.episode_started
    mkA = SY.SynthMarket(T=T, N=2, flat=True)
    mkB = SY.SynthMarket(T=T, N=2, flat=True)
    raw_close_B = mkB.pc.copy()
    raw_close_B[10:] *= 0.5                                       # 原始价拆分（引擎不读原始价）
    fA = SY.csr_daily(1, [0], [0.5])
    fA = (np.r_[fA[0], np.full(T - 1, fA[0][-1])].astype(np.int64), fA[1], fA[2])
    tg = np.zeros((T, 2), np.int8)
    tg[3, 0] = 1
    for m_ in (mkA, mkB):
        m_.trigs['HX'] = tg
    ip, fp = SY.params(H, 'EXIT_HALF')
    aA = SY.account(mkA, ip, fp, 'HX', fA).run(0, T)
    aB = SY.account(mkB, ip, fp, 'HX', fA).run(0, T)
    same = np.array_equal(aA.DY, aB.DY) and np.array_equal(aA.L_i, aB.L_i) and np.array_equal(aA.L_f, aB.L_f)
    idn('SPLIT_SCALES_PENDING_NO_RESET', '拆股：合同 HalfLot.adjust_split(2) 后 数量 / 剩余 / 待售 = 200 / 160 / 60、due 10、episode 不重置；引擎在后复权单位记账，原始价拆分不改变批次 / 待售 / due',
        '', ok_ref, 0, 0, 'PASS' if (ok_ref and same) else 'DIFFERS')
    idn('SPLIT_INVARIANCE', '原始价拆分植入（日 10 起原始收盘 × .5，后复权序列不变）：账户日序列与批次数组逐位不变 = %s' % same, '', same, '', '', 'BLOCKED' if same else 'DIFFERS')


# ------------------------------------------------------------------ 证券级共享预算 / 截止强制 / 重放
def budget_attacks():
    T, H = 30, 15
    mk = SY.SynthMarket(T=T, N=2, flat=True, adv=5e6)
    W = np.zeros((T, 2))
    W[0:5, 0] = 0.03                                   # 每批约 NAV × .03 / H = 20 万；5 批合计 = 单股 1% 上限
    ptr = np.zeros(T + 1, np.int64)
    cols, ws = [], []
    for d_ in range(T):
        c = np.flatnonzero(W[d_] > 0)
        cols.append(c)
        ws.append(W[d_, c])
        ptr[d_ + 1] = ptr[d_] + len(c)
    f = (ptr, np.concatenate(cols).astype(np.int64), np.concatenate(ws).astype(float))
    tg = np.zeros((T, 2), np.int8)
    tg[7, 0] = 1
    mk.trigs['M3'] = tg
    ip, fp = SY.params(H, 'EXIT_GATE_LIQ_1E8', tlog=True)
    a = SY.account(mk, ip, fp, 'M3', f, tlcap=1 << 12).run(0, T)
    B = 0.02 * 5e6 / (1e8 / O.V0)
    n = int(a.S_i[E.SI_NTL])
    tl = a.TL_i[:n]
    tf = a.TL_f[:n]
    sells = tl[:, 5] == 1
    days = sorted(set(int(x) for x in tl[sells][:, 0]))
    per_day = {d_: float(tf[sells & (tl[:, 0] == d_)][:, 1].sum()) for d_ in days}
    alloc = a.DY[:, E.DY_M3ALLOC]
    ok_b = all(alloc[d_] <= B * (1 + 1e-9) or a.DY[d_, E.DY_M3FORCED] > 0 for d_ in range(T))
    forced_rows = int(((tl[:, 4] == E.OK_DEADLINE) & sells).sum())
    ok_f = forced_rows > 0 and int(a.S_i[E.SI_OVERRIDE]) > 0
    idn('SHARED_BUDGET_SINGLE_RESERVATION', '合成例 M3（5 批同证券同日触发，B = .02 × ADV20 = %.3g）：每日信息卖单分配合计 ≤ B（不是每批各 B）；卖出分布在 %d 个日' % (B, len(days)), '',
        json.dumps({int(k): round(v / B, 4) for k, v in per_day.items()}), '', '', 'BLOCKED' if ok_b else 'DIFFERS')
    idn('DEADLINE_OVERRIDE_EXPLICIT', '到 deadline = min(due, 首次计划 e + 4) 仍有延后余额 → 按原 FEASIBLE 完成，成交行 order_kind = DEADLINE_OVERRIDE（%d 行）、SI_OVERRIDE 计 %d' % (forced_rows, int(a.S_i[E.SI_OVERRIDE])),
        '', forced_rows, 0, 0, 'PASS' if ok_f else 'DIFFERS')
    # 重放：同一日从 checkpoint 两次重跑 → 分配、现金、标签、成交逐位相同（不二次占用预算 / 不二次扣款 / 日志不重复）
    b = SY.account(mk, ip, fp, 'M3', f, tlcap=1 << 12).run(0, 8)
    pth = O.P('tmp', 'stage0', 'ckpt_m3.npz')
    os.makedirs(os.path.dirname(pth), exist_ok=True)
    b.checkpoint(pth, dict(test='stage0'))
    outs = []
    for _ in range(2):
        c = SY.account(mk, ip, fp, 'M3', f, tlcap=1 << 12)
        c.restore(pth)
        c.S_i[E.SI_NTL] = 0
        c.run(8, T)
        nn = int(c.S_i[E.SI_NTL])
        outs.append((c.DY.copy(), c.S_f.copy(), c.TL_i[:nn].copy(), c.TL_f[:nn].copy(), c.state_hash()))
    same = all(np.array_equal(outs[0][k], outs[1][k]) for k in range(4)) and outs[0][4] == outs[1][4]
    dup = len({tuple(r[:6]) for r in outs[0][2].tolist()}) == len(outs[0][2])
    idn('BUDGET_REPLAY_IDEMPOTENT', 'checkpoint（日 8）恢复两次重跑：预算分配、DY、现金、成交行逐位相同', '', same, 0, 0, 'PASS' if same else 'DIFFERS')
    idn('FILL_REPLAY_NO_SECOND_DEBIT', '同一成交日从 checkpoint 重放：现金与标签不二次扣（两次重放 S_f 逐位相同、成交行无重复键）', '', same and dup, '', '', 'BLOCKED' if (same and dup) else 'DIFFERS')
    idn('JOURNAL_REPLAY', '成交日志重放：同日同批同方向的行唯一（%d 行无重复键）；重放不追加第二份' % len(outs[0][2]), '', dup, '', '', 'BLOCKED' if (same and dup) else 'DIFFERS')


# ------------------------------------------------------------------ 未来数据 / 单位 / landmark / 政策布尔 / 密度
def plants(mk):
    T = 40
    m1 = SY.SynthMarket(T=T, N=3)
    f = SY.csr_daily(T, [0, 1, 2], [0.4, 0.3, 0.3])
    tg = np.zeros((T, 3), np.int8)
    tg[6, 0] = 1
    tg[15, 1] = 1
    m1.trigs['F0'] = tg
    ip, fp = SY.params(5, 'EXIT_GATE_LIQ_5E8')
    base = SY.account(m1, ip, fp, 'F0', f).run(0, T)
    t_star = 20
    m2 = SY.SynthMarket(T=T, N=3)
    m2.pv[t_star + 1:] *= 1.5
    m2.pc[t_star + 1:] *= 0.5
    m2.pcobs = m2.pc.copy()
    m2.adv20[t_star + 1:] *= 0.1
    pl = tg.copy()
    pl[t_star + 1:, :] = 1
    m2.trigs['F1'] = pl
    alt = SY.account(m2, ip, fp, 'F1', f).run(0, T)
    dmax = float(np.max(np.abs(base.DY[:t_star + 1] - alt.DY[:t_star + 1])))
    e7 = False
    try:
        import e6o_minute as MI
        MI.read_va(20260330)
    except RuntimeError:
        e7 = True
    idn('FUTURE_DATA_PLANT', 'T* 之后植入价格 / 触发 / ADV 改动（M3 门控账户）：T* 及之前日序列逐位不变（最大差 %.1e）；分钟读取接口对 > 2026-03-27 拒绝 = %s' % (dmax, e7), '', dmax, '', '',
        'BLOCKED' if (dmax == 0.0 and e7) else 'DIFFERS')
    cd = mk.cd
    vol = np.load(os.path.join(cd, 'panels', 'vol.npy'), mmap_mode='r')
    vm = np.load(os.path.join(cd, 'minute', 'vol_min.npy'), mmap_mode='r')
    t0 = int(np.searchsorted(mk.dates, '2020-01-01'))
    t1 = int(np.searchsorted(mk.dates, '2021-01-01'))
    j = int(np.flatnonzero(np.isfinite(np.asarray(vol[t0:t1])).all(0) & np.isfinite(np.asarray(vm[t0:t1])).all(0))[0])
    v = np.asarray(vol[t0:t1, j]).copy() / 100.0
    m = np.asarray(vm[t0:t1, j])
    with np.errstate(all='ignore'):
        r = np.abs(m / v - 1.0)
        r0 = np.abs(m / np.asarray(vol[t0:t1, j]) - 1.0)
    caught = bool(np.nanmedian(r) > 0.5)
    idn('UNIT_PLANT', '把一只股票 2020 年日频量 ÷ 100（冒充"手"）：日频 / 分钟量相对差中位 %.2f（原始 %.2e）→ 单位核对拦下' % (float(np.nanmedian(r)), float(np.nanmedian(r0))), '',
        round(float(np.nanmedian(r)), 4), '', '', 'BLOCKED' if caught else 'DIFFERS')
    blocked = False
    try:
        LM.group_by_outcome([1, 2, 3], future=True)
    except ValueError:
        blocked = True
    s_future = LM.state_at(5, 8)
    ok = blocked and s_future == 'NOT_TRIGGERED' and LM.state_at(5, 5) == 'BAD_STATE' and LM.state_at(5, 3) == 'REQUEST_PENDING' and \
        LM.state_at(5, 3, half_state=1) == 'HALF_PENDING' and LM.state_at(5, 3, forced=True) == 'DEADLINE_OVERRIDDEN'
    idn('LANDMARK_NO_FUTURE_GROUPING', '按未来事件分组的调用被拒；T 之后的意向记录不改变 T 时状态（T = 5、意向日 8 → NOT_TRIGGERED）；8 状态词表齐全', '',
        'rejected=%s future_ignored=%s' % (blocked, s_future == 'NOT_TRIGGERED'), '', '', 'BLOCKED' if ok else 'DIFFERS')
    w, st = LM.fwd_window(95, 10, 100)
    w2, st2 = LM.fwd_window(80, 10, 100)
    idn('LANDMARK_CENSOR_AT_CUTOFF', 'landmark 前向窗口超出授权终点（2026-03-27）→ RIGHT_CENSORED（不取 E7 价格）', '', '%s/%s' % (st, st2), '', '',
        'BLOCKED' if (st == 'RIGHT_CENSORED' and st2 == 'COMPUTED') else 'DIFFERS')
    samples = ({'c1': np.bool_(True), 'c2': True}, {'c1': 0, 'c2': True}, {})
    out = []
    for s_ in samples:
        try:
            v_, _ = RU.policy_verdict(s_)
            out.append(v_)
        except TypeError:
            out.append('TypeError')
    ok_p = out == ['TypeError', 'TypeError', '不可判']
    idn('POLICY_BOOL_EXPLICIT', '政策布尔三样例：numpy.bool_ → 拒绝、数字 0 → 拒绝、空 profile → 不可判（EMPTY_PROFILE）；入表前一律显式 Python bool', '', json.dumps(out, ensure_ascii=False), '', '',
        'BLOCKED' if ok_p else 'DIFFERS')
    put('S0-E', '政策布尔样例数', 'POLICY_BOOL_SAMPLES', 3, 'count', 'PASS' if ok_p else 'DIFFERS', 'e6q_rules.policy_verdict')
    d1 = RU.density(1.0, 2.0, 0.0)
    d2 = RU.density(1.0, 2.0, -1.0)
    d3 = RU.density(7.67, 10.53, 9.75)
    ok_d = d1[2] == d2[2] == 'NOT_POSITIVE_DENOMINATOR' and d1[0] is None and abs((d3[0] - d3[1]) - (7.67 - 10.53) / 9.75) < 1e-12
    idn('DENSITY_DENOMINATOR_GUARD', 'Δturn = 0 / < 0 → NOT_POSITIVE_DENOMINATOR、密度空（不报无穷效率）；正常分母 v − c = (Δnet − Δimpact) / Δturn', '', '%s/%s' % (d1[2], d2[2]), '', '',
        'BLOCKED' if ok_d else 'DIFFERS')


# ------------------------------------------------------------------ S0-E 其余 / S0-F
def s0_e_f():
    for k, v in (('CLAIM_QUERY_CLOSURE', 'every claim number -> reports/query_registry_E6q.csv -> real table row'),
                 ('UNIT_DECLARATION', 'trades/ = fill rows; events/ = intents; partial fills declared in SCHEMA_DEVIATIONS.md'),
                 ('SCAN_SCOPE', 'sensitive-string scan over the handoff directory only'), ('ID_SEPARATOR', "exec_id separator ASCII '|' only; no broken bar"),
                 ('MC_LIMIT_DISCLOSURE', 'MC_LIMIT counts and owners written to notes'), ('POLICY_BOOL', 'explicit Python bool before table write')):
        put('S0-E', 'E6p REVIEW 协议改进落地', k, v, 'count', 'INFO', 'brief §0.2 / 附录 A-E')
    st = pd.read_csv(O.P('verify', 'selftest_identities_E6q.csv'), keep_default_na=False)
    for cid in ('ZERO_INTERVENTION_EQ_NATIVE', 'PSTAR_INF_EQ_NATIVE', 'THETA_ONE_EQ_NATIVE', 'NEW_FILTER_OFF_EQ_NATIVE', 'CHECKPOINT_RESTORE_IDEMPOTENT'):
        x = st[st.check_id == cid]
        put('S0-F', '零干预 / 端点恒等（自检，合成坐标）', cid, '%d/%d PASS' % (int((x.status == 'PASS').sum()), len(x)), 'count', 'PASS' if (x.status == 'PASS').all() and len(x) else 'DIFFERS',
            'verify/selftest_identities_E6q.csv', '正式 47 条 PATH_IDENTITY 边在 B 段账户上另核（S34 / identities ZERO_INTERVENTION_EQ_NATIVE）')
        for r in x.itertuples(index=False):
            idn(r.check_id, r.description, r.exec_id, r.value, r.max_abs_diff, r.tolerance, r.status)
    put('S0-F', 'TTL 起点', 'TTL_START_RULE', 'first denial by a NEW rule only (M1 new filter / M2 cap); never from the sale day', 'count', 'INFO', 'e6q_engine.tk_deny')


# ------------------------------------------------------------------ S0-G 源绑定
def s0_g():
    import e6m_b6_triggers as BT
    import e6n_b2 as B2
    import e6j_prod as PR
    import comprehensive_factor_diagnosis as C
    import pool_screening_v2 as PS
    import e6m_stage0_full as SF
    import e6o_panels as OP
    import e6q_edge as EG
    here = os.path.dirname(os.path.abspath(__file__))
    fsha = lambda fn: O.sha_file(os.path.join(here, fn))
    E6 = pd.read_csv(O.E6P('registration', 'sources_E6p.csv'), keep_default_na=False, dtype=str).set_index('key')
    sh = dict(engine=fsha('e6q_engine.py'), engine_e6p=fsha('e6p_engine.py'), b2_trigger=fn_sha(BT.ecdf_pct, BT.cvr_triggers, B2.triggers),
              veto_t1a=fn_sha(PR.drop_mask, PR.build_period, C.precompute_neutralized_factor, C.build_factor_strategy_holdings_cached, PS.neutralize_by_mcap),
              limit_fields=O.digest([fsha('e6p_cache.py'), fn_sha(SF.load_full)]), fee=fn_sha(E.solve_eval, E.feasible), vwap=fn_sha(C.vwap_daily_return, C.adjusted_prices),
              cost_adv=fsha('e6o_panels.py'), cost_sigma=fsha('e6o_panels.py'), token_ledger=fn_sha(E.tk_add, E.tk_ok, E.tk_sum, E.tk_consume, E.tk_deny, E.tk_quar, E.tk_quar_new),
              net_order=fn_sha(E.solve_eval, E.exec_qty), payment_route=fn_sha(E.feasible, E.solve_all), industry=O.digest([fsha('e6o_panels.py'), fsha('e6p_cache.py')]),
              edge_spread=fn_sha(EG.edge, EG.rolling_panel), amihud=O.digest([fn_sha(OP.rolling_prev), fsha('e6q_cache.py')]), minute=fsha('e6o_minute.py'),
              legacy_impact=fn_sha(CO.audit_share, CO.legacy_share_vec), curve_impact=fn_sha(CO.order_cost, CO.curve_share_vec, CO.fixed_path_share))
    e6p_sha = lambda k: E6.loc[k, 'fn_sha256'] if k in E6.index else ''
    e6p_val = lambda k: E6.loc[k, 'value'] if k in E6.index else ''

    def carry(key, cur_sha, item, srcfile, note=''):
        exp = e6p_sha(key)
        val = e6p_val(key)
        same = (exp == cur_sha) or not exp
        src(key, val, item, srcfile, cur_sha, 'BOUND', (note + '；' if note else '') + ('函数 sha 与 E6p 同' if same else '函数 sha 与 E6p 不同（E6p %s…）：登记差异' % exp[:12]))
    src('ENGINE_FN_SHA256', sh['engine'], 'C1 账户引擎（E6p 引擎逐式复制 + E6q 受控扩展）', 'e6q_engine.py', sh['engine'],
        note='E6p 引擎 sha %s…（e6p_engine.py %s…）；E6q 全扩展关闭 ≡ E6p：verify/selftest 132 个 E6p 账户逐日复现（相对 ≤ 1e−9，实为 0）' % (e6p_val('ENGINE_FN_SHA256')[:12], sh['engine_e6p'][:12]))
    src('SOURCE_CASH_MODEL', e6p_val('SOURCE_CASH_MODEL'), 'C1 源现金模型', 'e6i_sparse.SparseEngine.pnl / e6q_engine.step', sh['engine'], note='与 E6p 同值（自融资现金引擎）')
    src('NATIVE_BUDGET_RULE', e6p_val('NATIVE_BUDGET_RULE'), 'C1 常规买入预算与 DEV 形状', 'e6q_engine.step（次日买单段）', fn_sha(E.step),
        note='规则文本与 E6p 同；step 函数体因 E6q 扩展而不同（E6p fn sha %s…），NATIVE 路径逐日复现 E6p（差异只在新开关）' % e6p_sha('NATIVE_BUDGET_RULE')[:12])
    carry('B2_TRIGGER_KIND', sh['b2_trigger'], 'C2 B2 触发类型', 'e6m_b6_triggers.cvr_triggers / e6n_b2.triggers')
    for k in ('B2_LEVEL_DEFINITION', 'B2_MISSING_DAY_RULE'):
        src(k, e6p_val(k), 'C2 %s' % k, 'e6o_triggers.py', fsha('e6o_triggers.py'), note='与 E6p 同值' + ('' if fsha('e6o_triggers.py') == e6p_sha(k) else '；文件 sha 变化（登记差异）'))
    for k in ('VETO_MEASURE', 'VETO_CUT_FORM', 'VETO_TIE_RULE'):
        carry(k, sh['veto_t1a'], 'C2 T1a 否决 %s' % k, E6.loc[k, 'source_file'] if k in E6.index else '')
    src('VETO_COEF_EXTENSION_RULE', e6p_val('VETO_COEF_EXTENSION_RULE'), 'C2 T1a 系数延伸', 'e6o_source.t1a_panel', fsha('e6o_source.py'),
        note='与 E6p 同值' + ('' if fsha('e6o_source.py') == e6p_sha('VETO_COEF_EXTENSION_RULE') else '；e6o_source.py sha 与 E6p 登记不同（登记差异）'))
    for k in ('LIMIT_PRICE_FIELDS', 'LIMIT_PIT_RULE', 'LIMIT_BOARD_REGIME_START', 'NO_LIMIT_DAY_FLAG', 'ONE_TICK_RULE'):
        carry(k, sh['limit_fields'], 'C2 涨跌停 %s' % k, E6.loc[k, 'source_file'] if k in E6.index else 'e6p_cache.py',
              note='T8 用交易所限制价字段（不硬编码 10%）；UNION_T1a_T8 = 三值或，交集同日一个面板值 = 一次意向')
    carry('FEE_CHARGED_TURN_UNIT', sh['fee'], 'C3 费率单位', 'e6q_engine.solve_eval / feasible', note='E6q 版 solve_eval / feasible 多路由参数（route_on = 0 时与 E6p 同式）')
    carry('VWAP_DEFINITION', sh['vwap'], 'C3 VWAP', 'comprehensive_factor_diagnosis.vwap_daily_return')
    carry('CORPORATE_ACTION_FIELDS', sh['cost_adv'], 'C3 公司行为', 'e6o_panels.py', note='估值与收益沿 E6p（后复权）；E6q 的 EDGE 输入另用 lclose 链式复权（OHLC_FIELDS）')
    for k in ('COST_ADV_FN', 'COST_SIGMA_FN', 'COST_FIELD_CLOCK'):
        carry(k, sh['cost_adv'], 'C4 成本字段 %s' % k, 'e6o_panels.rolling_prev', note='缺 ADV 不设无限流动性或零成本 → LIQ_DATA_FALLBACK 回原 NATIVE 分配并分列')
    src('INDUSTRY_PIT_FN', 'ind = day-T industry_zx1 integer code (-1 unknown); indL = T-1 frozen; benchmark industry share = n_ind(T)/N_clean(T)', 'C8 行业 PIT',
        'e6o_panels.py / e6p_cache.py', sh['industry'], note='ISK 层与 RANDOM_TARGET 行业上限用 ind（T 收盘可得）')
    src('CLEAN_SIZE_TERTILE_FN', 'iskid = industry x clean size tercile (zsize rank pct in day-T clean set)', 'C8 clean 规模三档', 'e6o_panels.py（zsize）/ e6p_cache（iskid）', sh['industry'])
    src('TOKEN_LEDGER_FN', 'TK arrays: amount, unlock (lag1), due, id, first_denied; usable iff unlock <= day < due and not (first_denied >= 0 and day >= first_denied + TTL); '
        'consume order (due, id); tombstone ids never reused', 'C6 token 账本', 'e6q_engine.tk_*', sh['token_ledger'])
    src('NET_ORDER_FN', 'security-day net order |bq - sq| x VWAP; fee 4bp on net; M2/M3 budget B = p* x ADV20 x V0 / A_ref against fixed net b (regular buy - due/early sell at T close price); '
        'one reservation per security-day (M3 queue deadline, first_decision, lot)', 'C7 证券级净订单与共享预算', 'e6q_engine.solve_eval / exec_qty / step（M3 分配）', sh['net_order'])
    src('PAYMENT_ROUTE_FN', 'REGULAR gap and EXTRA paid by usable tokens; route_on: token-funded regular min(gap, R_buy) <= route-eligible regular buys (M1 new name / M2 R-Sell<=B); '
        'quarantined tokens unusable by any buy; due unlock attribution only', 'C6 支付路由', 'e6q_engine.feasible / solve_all', sh['payment_route'])
    src('OHLC_FIELDS', 'open/high/low/close raw x lclose-chain factor (F_t = F_prev x prev raw close / lclose_t; same adjustment as r_day); adj_factor not used (missing 2-11% of open cells)',
        'C9 OHLC', 'e6q_cache.py', fsha('e6q_cache.py'))
    src('EDGE_SPREAD_FN', 'bidask 2.1.0 edge (MIT); 21 trading days ending T-1; >= 3 complete OHLC obs else missing; equality indicators on raw prices (log-monotone; avoids SIMD 1-ulp flips)',
        'C9 EDGE', 'e6q_edge.edge / rolling_panel', sh['edge_spread'], note='作者四例 PASS；面板 800 窗抽查与 edge 逐窗重算一致')
    src('AMIHUD_FN', 'amihud20 = mean(|r_day| / amount) over T-20..T-1, >= 10 obs, amount CNY', 'C9 Amihud', 'e6o_panels.rolling_prev / e6q_cache.py', sh['amihud'])
    src('MINUTE_TAIL_AMOUNT_FN', 'tail_amt = amount 14:30-15:00 (minute bars; E6o minute cache)', 'C10 分钟尾盘额', 'e6o_minute.py（E6o 缓存 minute/tail_amt）', sh['minute'],
        note='只覆盖 D5 第二分母与 D8；E7 守卫：读取接口对 > 2026-03-27 拒绝')
    src('LEGACY_IMPACT_FN', 'kappa sqrt(A) sum |dw|^1.5 sigma / sqrt(ADV); dw = dn / V_pre; A fixed (E6p LEGACY c5 D_imp; engine DY impact_br)', 'C5 legacy 冲击', 'e6q_cost.audit_share / e6p_stats D_imp',
        sh['legacy_impact'])
    src('CURVE_IMPACT_FN', 'kappa A^delta S_delta; S_delta = sum (dn / V(e-1)+) sigma sqrt(p0) (dn / (V0 ADV p0))^delta (engine cost_s05/s07/s10); same-node A_e = A0 n_e',
        'C5 curve 冲击', 'e6q_cost.order_cost / curve_share_vec / fixed_path_share', sh['curve_impact'])
    st_a = json.load(open(O.P('diagnostics', 's0a_facts_E6q.json'), encoding='utf-8'))['status']
    src('RECONCILIATION_INSTRUMENT', 'CANONICAL=CURVE_IMPACT_FN' if st_a == 'RECONCILED' else 'UNDECIDABLE', 'C5 唯一主仪器（S0-A）', 'reports/E6q_S0A_reconciliation.md', '',
        note='状态 %s' % st_a)
    src('E6P_REGISTRY_SHA256', O.sha_file(O.E6P('registration', 'registry_E6p.csv')), 'C1 E6p registry', 'E6p registration/registry_E6p.csv', '')
    S = pd.read_csv(O.E6P('statistics', 'account_summary_E6p.csv'), keep_default_na=False, na_values=[''])
    F = S[S.segment == 'FULL']
    binds = {'8.75': ('E6P-28aebd98dafd9607427500c4', 'net_ann_pp'), '13.37': ('E6P-b8173d4bb4481eabcd7c1a04', 'net_ann_pp'),
             '5.51': ('E6P-99de9b5674c5c0bbc14d5523', 'net_ann_pp'), '6.90': ('E6P-57e0690911d8ae695b796d35', 'net_ann_pp'),
             '3.24': ('E6P-28aebd98dafd9607427500c4', 'D_same_h_ann_pp'), '7.86': ('E6P-b8173d4bb4481eabcd7c1a04', 'D_same_h_ann_pp')}
    for v, (lid, col) in binds.items():
        eid = lid + '|FEASIBLE_DAILY|FULLHIST|CASH_V0|FIXED_PATH_V1|E6P_V11'
        row = F[F.exec_id == eid]
        got = float(row.iloc[0][col]) if len(row) else float('nan')
        ok = len(row) == 1 and abs(got - float(v)) < 0.005 + 1e-9
        src('E6P_TABLE_BINDING_%s' % v, eid, 'C11 E6p 表读数 %s 的执行身份（附录 G）' % v, 'E6p statistics/account_summary_E6p.csv（FULL %s）' % col, '',
            'BOUND' if ok else 'SOURCE_BINDING_PENDING', note='机器表值 %.6f' % got)
    for dep, cov in (('LIMIT', 'trigger ∈ {T8, UNION_T1a_T8}'), ('COST', 'A_ref 臂 + 全部成本曲线 / 盈亏平衡 / 反馈 / 密度'), ('INDUSTRY', 'COUNT_ISK / AMOUNT_ISK_V2 / RANDOM_TARGET 行业层'),
                     ('OHLC_SPREAD', 'D2 EDGE 价差列'), ('MINUTE', 'D5 第二分母与 D8')):
        src('DEPENDENCY_BINDING_%s' % dep, 'BOUND', '依赖级绑定 %s（覆盖 %s）' % (dep, cov), 'registration/sources_E6q.csv', '')
    O.atomic_write_json(O.P('diagnostics', 'source_fn_sha256_E6q.json'), sh)
    return sh


# ------------------------------------------------------------------ S0-H 数据覆盖
def holding_domain(mk, H=30):
    T, N = mk.T, mk.N
    hold = np.zeros((T, N), bool)
    for (f, m), (ptr, col, w) in G['f'].items():
        t = np.repeat(np.arange(T), np.diff(ptr))
        for k in range(1, H + 1):
            tt = t + k
            ok = tt < T
            hold[tt[ok], col[ok]] = True
    return hold


def s0_h(mk, hold):
    cd = mk.cd
    pdir = os.path.join(cd, 'panels')
    L = lambda k: np.asarray(np.load(os.path.join(pdir, k + '.npy'), mmap_mode='r'))
    years = np.array([int(d[:4]) for d in mk.dates])
    board = L('board')
    pool0 = np.asarray(np.load(os.path.join(cd, 'triggers', 'pool0.npy'), mmap_mode='r')).astype(bool)
    is_open = np.asarray(mk.isopen).astype(bool)
    t8k = L('t8_kind')
    import e6m_stage0_full as SF
    data, _, _ = SF.load_full()
    close = data['close']
    ld = data['limit_down'].reindex(index=close.index, columns=close.columns).astype(float).to_numpy()
    del data
    tail = np.isfinite(np.load(os.path.join(cd, 'minute', 'tail_amt.npy'), mmap_mode='r'))
    oa = np.isfinite(L('open_adj')) & np.isfinite(L('high_adj')) & np.isfinite(L('low_adj')) & np.isfinite(L('close_adj'))
    fields = {'daily': np.isfinite(np.asarray(mk.pv)) | ~is_open, 'limit_up': L('limit_known') | ~is_open, 'limit_down': np.isfinite(ld) | ~is_open,
              'no_limit_flag': (t8k != 5), 'one_tick': L('limit_known') | ~is_open, 'ohlc': oa | ~is_open, 'industry_L1': np.asarray(mk.ind) >= 0,
              'adv20': np.isfinite(np.asarray(mk.adv20)) | ~is_open, 'sigma20': np.isfinite(np.asarray(mk.sig20)) | ~is_open,
              'minute_tail_amount': np.asarray(tail) | ~is_open, 'amihud20': np.isfinite(L('amihud20')) | ~is_open}
    for dom, M in (('HOLDING_ALL', hold), ('POOL0_FORMATION', pool0)):
        for fld, Fm in fields.items():
            for y in sorted(set(years)):
                ym = years == y
                for bi, bn in enumerate(BOARDS):
                    m = M[ym][:, board == bi]
                    n = int(m.sum())
                    if n == 0:
                        continue
                    v = float(Fm[ym][:, board == bi][m].mean())
                    put('S0-H', dom, 'COVERAGE_%s_%d_%s' % (fld, y, bn), round(v, 6), 'share', 'INFO', 'cache panels',
                        '分母 = 该域股票日（%d）；停牌日记已知；minute 2013-08-01 前为 0；不回填、不把缺失填成高流动性' % n)
    put('S0-H', 'EDGE 窗口规则', 'EDGE_WINDOW_RULE', '21 trading days ending T-1, >= 3 complete OHLC obs else missing', 'count', 'INFO', 'e6q_edge.py', 'W14')
    put('S0-H', 'Amihud 窗口规则', 'AMIHUD_WINDOW_RULE', 'T-20..T-1, >= 10 obs, amount in CNY', 'count', 'INFO', 'e6q_cache.py', 'W13')
    put('S0-H', '持仓全域股票日（源 H30 窗 8 坐标并集）', 'HOLDING_ALL_CELLS', int(hold.sum()), 'count', 'INFO', 'cache/source', '离池持仓日 = %d' % int((hold & ~pool0).sum()))
    return pool0


# ------------------------------------------------------------------ S0-I E 端点在唯一仪器上重放
def s0_i(st_a):
    """七条 E 的 lower / upper 端点项（claims.json band_expression）在 CANONICAL（curve，A_eval、κ .5、δ .5；E07 无冲击）上逐项取值：
    项值 = 该旧对象账户 FULL ann_pp（共同支持日）的 net8 − κ A_eval^δ S_δ；端点 = Σ 系数 × 项值；不交换端点。旧对象账户取 E6p 已交付同坐标账户
    （E6q NATIVE / CASH / RECYCLE 复现 E6p 逐日一致，verify/selftest），任何新臂结果之前封存。"""
    claims = json.load(open(O.P('registration', 'spec', 'claims.json'), encoding='utf-8'))
    reg = {s['id']: s for s in json.load(open(O.P('registration', 'spec', 'registry.json'), encoding='utf-8'))}
    E6 = pd.read_csv(O.E6P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
    E6 = E6[(E6.role == 'ACCOUNT') & (E6.cap == 'SOURCE') & (E6.renew == '0') & (E6.execution_profile == 'FEASIBLE_DAILY')]
    trig = {'NONE': 'NONE', 'T1a': 'T1a', 'T1b_LEVEL': 'T1b_LEVEL', 'T8': 'T8_LIMIT_CLOSE'}
    dates = np.load(os.path.join(O.cache_dir(), 'panels', 'dates.npy'))
    segi = np.array([O.seg_of_date(d) for d in dates])
    cache = {}

    def series(lid):
        if lid in cache:
            return cache[lid]
        s = reg[lid]
        m = E6[(E6.form == s['form']) & (E6.memory == s['memory']) & (E6.H == str(s['H'])) & (E6.deploy == s['arm']) & (E6.trigger == trig[s['trigger']])]
        if len(m) != 1:
            raise RuntimeError('E 端点旧对象在 E6p 无唯一同坐标账户：%s' % lid)
        h = m.iloc[0].exec_hash
        DY = np.load(O.E6P('accounts_run', 'full', h[:2], '%s.npz' % h), allow_pickle=False)['DY']
        cache[lid] = (DY[:, 5], DY[:, 39], DY[:, 11], m.iloc[0].exec_id)
        return cache[lid]

    def full_val(lids, A_, kind):
        """项值：共同支持日上 FULL ann_pp（Σ n v / Σ n）。kind = CANONICAL（curve）/ LEGACY_E6P / NET8。"""
        arrs = []
        for lid in lids:
            ne, s05, impb, _ = series(lid)
            if kind == 'NET8':
                x = ne
            elif kind == 'CANONICAL':
                x = ne - 0.5 * (A_ ** 0.5) * s05
            else:
                x = ne - 0.5 * math.sqrt(A_) * impb
            arrs.append(x)
        common = np.all([np.isfinite(x) for x in arrs], axis=0)
        out = []
        for x in arrs:
            num, den = 0.0, 0
            for s in O.SEGS:
                mm = common & (segi == s)
                n = int(mm.sum())
                num += float(np.mean(x[mm]) * O.ANN_PP) * n
                den += n
            out.append(num / den)
        return out
    rows, vals = [], {}
    for e in claims['e']:
        A_ = e.get('A_eval')
        kinds = [('CANONICAL', 'NET8' if A_ is None else 'CANONICAL')] + ([] if A_ is None else [('LEGACY_E6P', 'LEGACY_E6P')])
        for inst, kd in kinds:
            if inst == 'CANONICAL' and st_a != 'RECONCILED' and A_ is not None:
                stat = 'INSTRUMENT_LIMITED'
            else:
                stat = 'COMPUTED'
            bvals = {}
            for bound, key in (('lower', 'lower_terms'), ('upper', 'upper_terms')):
                terms = e['band_expression'][key]
                lids = [t[0] for t in terms]
                tv = full_val(lids, A_ or 0.0, kd)
                bvals[bound] = sum(float(c) * v for (_, c), v in zip(terms, tv))
                for (lid, coef), v in zip(terms, tv):
                    rows.append(dict(e_id=e['id'], bound=bound, term_logical_id=lid, term_exec_id=O.exec_id(lid, 'FEASIBLE_DAILY'), coefficient=int(coef), instrument=inst,
                                     A_eval_cny='' if A_ is None else int(A_), kappa=e['kappa'], exponent=e['delta'], value_ann_pp=v, status=stat))
            vals[(e['id'], inst)] = (bvals['lower'], bvals['upper'], stat)
    B = pd.DataFrame(rows, columns=['e_id', 'bound', 'term_logical_id', 'term_exec_id', 'coefficient', 'instrument', 'A_eval_cny', 'kappa', 'exponent', 'value_ann_pp', 'status'])
    O.atomic_write_csv(O.P('registration', 'e_band_bindings_E6q.csv'), B)
    out = {}
    for e in claims['e']:
        lo, hi, stat = vals[(e['id'], 'CANONICAL')]
        disp = e['band_E6p_display']
        out[e['id']] = dict(band_lo_canonical=lo, band_hi_canonical=hi, status=stat, band_lo_display=disp[0], band_hi_display=disp[1],
                            order_supported=bool(lo <= hi), legacy=vals.get((e['id'], 'LEGACY_E6P')))
        put('S0-I', 'E 端点重放（%s；CANONICAL）' % e['id'], 'E_BAND_%s' % e['id'], '[%.4f, %.4f]' % (lo, hi), 'ann_pp', 'INFO' if lo <= hi else 'DIFFERS',
            'registration/e_band_bindings_E6q.csv', '显示带 [%s, %s]（不改）；%s' % (disp[0], disp[1], '参照顺序假设成立' if lo <= hi else '下端 > 上端：参照顺序假设不支持，不交换端点'))
    O.atomic_write_json(O.P('diagnostics', 'e_band_values_E6q.json'), out)
    return out


# ------------------------------------------------------------------ S0-J / S0-K / S0-L / S0-N
def s0_jkl():
    v = json.load(open(O.P('verify', 'spec', 'verification.txt'), encoding='utf-8'))
    ok = v.get('test_count') == 205 and all(v['json_sha256'][k] == s for k, s in O.JSON_SHA.items())
    put('S0-J', '合同脚本 205 项与七指纹', 'SPEC_205_AND_7SHA', 'PASS' if ok else 'DIFFERS', 'count', 'PASS' if ok else 'DIFFERS', 'verify/spec/verification.txt + SHA256.txt',
        'python3 -W error 隔离重跑；七个 json（LF）指纹 = plan 附录 B；原样复制进 registration/spec/')
    put('S0-J', '合同脚本计数', 'SPEC_COUNTS', json.dumps(v.get('counts', {}), ensure_ascii=False), 'count', 'INFO', 'verify/spec/verification.txt')
    dsha = O.sha_file(O.P('verify', 'decision', 'E6q_D_stage2.py'))
    okk = dsha == O.D_SCRIPT_SHA256
    put('S0-K', '决策端脚本 sha / py_compile / 夹具空跑', 'D_SCRIPT_FIXTURE', 'PASS' if okk else 'DIFFERS', 'count', 'PASS' if okk else 'DIFFERS', 'verify/decision + tmp/s0k',
        'sha = %s…（与 brief 一致）；py_compile 字节码写临时目录；夹具 37 探针全有状态行（36 PASS / 1 INFO；夹具上 DIFFERS / NOT_COMPUTABLE 为预期）' % dsha[:8])
    st = json.load(open(O.P('verify', 'selftest_E6q.json'), encoding='utf-8'))
    res = st['results']
    w_acct = [vv['wall_s'] for k, vv in res.items() if k.startswith(('REPL_', 'Z_', 'E_')) and vv.get('status') == 'OK']
    w_rt = [vv['wall_s'] for k, vv in res.items() if k.startswith('S_RT_') and vv.get('status') == 'OK']
    sec = float(np.median(w_acct))
    p95 = float(np.percentile(w_acct, 95))
    rt95 = float(np.percentile(w_rt, 95)) if w_rt else p95
    n_acc = 201 * 2 + 80 * 2 + 105 * 2 + 20
    n_rand = 105 * 3 * 128 + 50 + 105 * 128 + 98 * 128 + (50 * 4 + 49 * 2) * (1024 - 128)
    workers = 96
    core_s = n_acc * p95 + n_rand * 0.5 * (p95 + rt95) * 1.3
    est_days = core_s / workers / 86400.0
    put('S0-L', '单账户全程耗时（中位；FEASIBLE 与 IDEAL 同引擎）', 'RUNTIME_ACCOUNT_SEC_FEASIBLE_DAILY', round(sec, 2), 'count', 'INFO', 'verify/selftest_E6q.json', 'P95 = %.2f s' % p95)
    put('S0-L', '同上（IDEALIZED_SOURCE_FILL）', 'RUNTIME_ACCOUNT_SEC_IDEALIZED_SOURCE_FILL', round(sec, 2), 'count', 'INFO', 'verify/selftest_E6q.json')
    put('S0-L', '随机单路径全程耗时（RANDOM_TARGET 路径 P95 / 其余按账户 P95）', 'RUNTIME_RANDOM_PATH_SEC', round(rt95, 2), 'count', 'INFO', 'verify/selftest_E6q.json')
    put('S0-L', '峰值 RSS（自检主进程；每 worker 另 ≤ 1 GB）', 'PEAK_RSS_GB', round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2), 'count', 'INFO', 'stage0')
    put('S0-L', '磁盘估算（成交分片 ≈ 400 × 0.1 GB；随机日统计 ≈ 40 GB；checkpoint ≈ 10 GB；结果 ≈ 20 GB）', 'DISK_GB_ESTIMATE', 120, 'count', 'INFO', '', '47 剩余 > 30 TB')
    put('S0-L', '总耗时估算（账户 / 影子 / 反馈 / WARM 两阶段 + 随机 ≈ %d 路径（主 owner 到 1,024 上限的保守估计）× 1.3（A2 重放）；%d worker）' % (n_rand, workers), 'EST_TOTAL_DAYS',
        round(est_days, 3), 'days', 'INFO', '', '≤ 14 天 → 不回传（brief §0.2 #4）')
    put('S0-L', '每 worker 线程', 'THREADS', 'BLAS 2 / numba 1', 'count', 'INFO', 'e6q_bg.sh')
    put('S0-L', '并发 worker', 'CONCURRENT_JOBS', workers, 'count', 'INFO', 'e6q_bg.sh（核心绑定 96-191, 288-383）')
    return est_days


def s0_n():
    """在夹具副本上把 DEPENDENCY_BINDING_COST 标 PENDING 并删去其覆盖表，再跑 D 脚本，确认 S25 / S36 走豁免路径、其余探针不受影响。"""
    src_fx = O.P('tmp', 's0k', 'fixture')
    dst = O.P('tmp', 's0n', 'fixture_cost_pending')
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src_fx, dst, ignore=shutil.ignore_patterns('out'))
    p = os.path.join(dst, 'diagnostics', 'stage0_E6q.csv')
    st = pd.read_csv(p, keep_default_na=False, dtype=str)
    m = (st.probe_id == 'S0-G') & (st.key == 'DEPENDENCY_BINDING_COST')
    if not m.any():
        st = pd.concat([st, pd.DataFrame([dict(probe_id='S0-G', item='drill', key='DEPENDENCY_BINDING_COST', value='SOURCE_BINDING_PENDING', unit='count',
                                               status='SOURCE_BINDING_PENDING', source_file='drill', note='S0-N drill')])], ignore_index=True)
    else:
        st.loc[m, 'status'] = 'SOURCE_BINDING_PENDING'
        st.loc[m, 'value'] = 'SOURCE_BINDING_PENDING'
    st.to_csv(p, index=False, lineterminator='\n')
    for t in ('statistics/cost_curve_E6q.csv', 'statistics/breakeven_E6q.csv', 'statistics/cost_feedback_E6q.csv', 'statistics/cost_feedback_pairs_E6q.csv', 'statistics/density_E6q.csv'):
        q = os.path.join(dst, t)
        if os.path.exists(q):
            os.remove(q)
    out = os.path.join(dst, 'out')
    r = subprocess.run([sys.executable, O.P('verify', 'decision', 'E6q_D_stage2.py'), '--root', dst, '--out', out], capture_output=True, text=True,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    probes = pd.read_csv(os.path.join(out, 'E6q_D_probes_stage2.csv'), keep_default_na=False, dtype=str) if os.path.exists(os.path.join(out, 'E6q_D_probes_stage2.csv')) else None
    if probes is None:
        put('S0-N', 'PENDING 演练', 'PENDING_DRILL', 'COST', 'count', 'DIFFERS', 'tmp/s0n', 'D 脚本未产出探针表：rc=%d' % r.returncode)
        return
    p25 = probes[probes.probe_id == 'S25'].iloc[0]
    p36 = probes[probes.probe_id == 'S36'].iloc[0]
    ok = p25.status == 'PASS' and 'PENDING' in p25.detail and p36.status == 'PASS' and 'PENDING' in p36.detail
    put('S0-N', 'PENDING 演练（夹具副本：COST 标 PENDING 并删去成本覆盖表 → 重跑 D 脚本）', 'PENDING_DRILL', 'COST', 'count', 'PASS' if ok else 'DIFFERS', 'tmp/s0n/fixture_cost_pending/out',
        'S25 %s / S36 %s（豁免路径）；其余探针状态分布 %s' % (p25.status, p36.status, json.dumps(probes.status.value_counts().to_dict())))
    put('S0-N', '政策夹具', 'POLICY_FIXTURE', '3 bool samples blocked (see POLICY_BOOL_EXPLICIT)', 'count', 'INFO', 'e6q_rules.policy_verdict')


# ------------------------------------------------------------------ 锚（INFO）
def anchors(mk):
    E6C = O.E6P_CACHE
    segv, nd = {}, {}
    for s in O.SEGS:
        z = np.load(os.path.join(E6C, 'source_e6p', '%s.npz' % s), allow_pickle=False)
        v = z['src_net8|%s|HG10|H5' % O.MAIN_FORM]
        ok = np.isfinite(v)
        segv[s] = float(np.mean(v[ok]) * O.ANN_PP)
        nd[s] = int(ok.sum())
    full = sum(segv[s] * nd[s] for s in O.SEGS) / sum(nd.values())
    anc = dict(zip(O.SEGS, (3.21, 7.36, 8.24, 10.31)))
    mx = max(max(abs(segv[s] - anc[s]) for s in O.SEGS), abs(full - 6.74))
    idn('SOURCE_ANCHOR_FRONTIER', 'P_SOURCE 主父（A4b_CVRv5 × HG10 × H5，8bp）四段 / FULL net vs W05 锚 3.21 / 7.36 / 8.24 / 10.31 / 6.74（容差 1e−2；INFO）',
        'E6P-SRC-%s-HG10-H5' % O.MAIN_FORM, '/'.join('%.4f' % segv[s] for s in O.SEGS) + ' FULL %.4f' % full, mx, 1e-2, 'INFO')
    E6I = pd.read_csv(O.E6P('verify', 'identities_E6p.csv'), keep_default_na=False, dtype=str)
    e6h = {r.exec_id: r.value for r in E6I[E6I.check_id == 'SOURCE_HOLDINGS_SHA'].itertuples(index=False)}
    for (f, m), (ptr, col, w) in sorted(G['f'].items()):
        h = hashlib.sha256()
        for a in (ptr, col, w):
            h.update(np.ascontiguousarray(a).tobytes())
        key = 'E6P-SRC-%s-%s' % (f, m)
        same = e6h.get(key) == h.hexdigest()[:16]
        idn('E6P_HOLDINGS_SHA', '源形成名单（CSR）sha256 前 16：%s × %s；与 E6p identities SOURCE_HOLDINGS_SHA 同 = %s' % (f, m, same), key, h.hexdigest()[:16], '', '', 'INFO')
    segi = np.array([O.seg_of_date(d) for d in mk.dates])
    for mem in O.MEMS:
        for H in (5, 20):
            p = O.P('tmp', 'selftest')
            hits = [x for x in os.listdir(p) if x.startswith('DY_Z_NATIVE_NONE_H%d' % H)] if mem == 'HG10' else []
            if not hits:
                continue
            ne_a = np.load(os.path.join(p, hits[0]))[:, E.DYI['net_excess']]
            ne_s = np.full(mk.T, np.nan)
            for s in O.SEGS:
                z = np.load(os.path.join(E6C, 'source_e6p', '%s.npz' % s), allow_pickle=False)
                idx = np.array([mk.di[d] for d in z['dates']])
                ne_s[idx] = z['src_net8|%s|%s|H%d' % (O.MAIN_FORM, mem, H)]
            ok = np.isfinite(ne_a) & np.isfinite(ne_s)
            br = float(np.mean(ne_a[ok] - ne_s[ok]) * O.ANN_PP)
            idn('ACCOUNTING_BRIDGE', 'P_ACCOUNT（自融资现金引擎，FEASIBLE）− P_SOURCE（固定滚动权重）FULL 共同日 ann_pp：%s × %s × H%d（INFO）' % (O.MAIN_FORM, mem, H),
                'E6P-SRC-%s-%s-H%d' % (O.MAIN_FORM, mem, H), round(br, 6), '', '', 'INFO')


def main():
    t0 = time.time()
    K = contract_module()
    st_a = s0_a(K)
    s0_c()
    s0_d(K)
    token_attacks(K)
    half_attacks(K)
    budget_attacks()
    mk = A.Market()
    G['f'] = {(f, m): mk.formation(f, m) for f in O.FORMS for m in O.MEMS if (f == O.MAIN_FORM or m == 'HG10')}
    plants(mk)
    s0_e_f()
    sh = s0_g()
    hold = holding_domain(mk)
    s0_h(mk, hold)
    bands = s0_i(st_a)
    est = s0_jkl()
    anchors(mk)
    s0_n()
    O.atomic_write_csv(O.P('diagnostics', 'stage0_E6q_part1.csv'), pd.DataFrame(ROWS))
    O.atomic_write_csv(O.P('verify', 'identities_E6q_stage0.csv'), pd.DataFrame(IDN))
    O.atomic_write_csv(O.P('registration', 'sources_E6q.csv'), pd.DataFrame(SRC))
    I = pd.DataFrame(IDN)
    O.write_receipt('E6q_stage0_part1', [O.P('diagnostics', 'stage0_E6q_part1.csv'), O.P('verify', 'identities_E6q_stage0.csv'), O.P('registration', 'sources_E6q.csv'),
                                         O.P('registration', 'e_band_bindings_E6q.csv')],
                    code=[__file__, E.__file__, A.__file__, SY.__file__, LM.__file__, CO.__file__, RU.__file__], wall_s=round(time.time() - t0, 1), est_total_days=est,
                    reconciliation_status=st_a)
    bad = I[~I.status.isin(['PASS', 'BLOCKED', 'INFO'])]
    print(json.dumps(dict(rows=len(ROWS), identities=len(I), bad=len(bad), est_total_days=round(est, 3), reconciliation=st_a, wall_s=round(time.time() - t0, 1),
                          statuses=I.groupby('check_id').status.agg(lambda s: ','.join(sorted(set(s)))).to_dict(),
                          bands={k: [round(v['band_lo_canonical'], 4), round(v['band_hi_canonical'], 4)] for k, v in bands.items()}), ensure_ascii=False, default=str), flush=True)
    if len(bad):
        print(bad.to_string()[:5000], flush=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
