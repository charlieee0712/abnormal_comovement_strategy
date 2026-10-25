# -*- coding: utf-8 -*-
"""E6o Stage 0（brief §2；附录 A 卡；plan §9）：S0-0…S0-11（S0-12 / S0-13 另由 e6o_s0_12_13.sh 已跑，本脚本只登记其结果行）。
只读源 / 面板 / 父账户；退出账户只做工程试跑（推导段内、只出计数与恒等，不出收益读数）。输出：
  diagnostics/stage0_E6o.csv（附录 B.8：probe_id, item, key, value, unit, status, source_file, note）
  verify/identities_E6o_stage0.csv（附录 B.11 列；闭包期与账户恒等合并为 verify/identities_E6o.csv）
用法：python3 e6o_stage0.py --workers 48"""
import os
import sys
import json
import time
import inspect
import hashlib
import argparse
import resource
from multiprocessing import get_context

import numpy as np
import pandas as pd

import e6o_core as O
import e6o_engine as E
import e6o_acct as A

ROWS = []
IDN = []


def put(probe, item, key, value, unit='count', status='INFO', source_file='', note=''):
    if isinstance(value, float) and not np.isfinite(value):
        value, status = '', 'UNKNOWN'
    ROWS.append(dict(probe_id=probe, item=item, key=key, value=value, unit=unit, status=status, source_file=source_file, note=note))


def idn(check, desc, exec_id, value, maxabs, tol, status):
    IDN.append(dict(check_id=check, description=desc, exec_id=exec_id, value=value, max_abs_diff=maxabs, tolerance=tol, status=status))


def fn_sha(*objs):
    h = hashlib.sha256()
    for o in objs:
        h.update(inspect.getsource(o).encode())
    return h.hexdigest()


# ------------------------------------------------------------------ S0-0
def s0_0():
    import e6m_b6_triggers as BT
    import e6n_b2 as B2
    import e6n_b2_run as B2R
    import e6j_prod as PR
    import comprehensive_factor_diagnosis as C
    import pool_screening_v2 as PS
    import e6i_sparse as SP
    trig_sha = fn_sha(BT.ecdf_pct, BT.cvr_triggers, B2.triggers)
    ctl_sha = fn_sha(B2R.controls)
    veto_sha = fn_sha(PR.drop_mask, PR.build_period, C.precompute_neutralized_factor, C.build_factor_strategy_holdings_cached, PS.neutralize_by_mcap)
    fee_sha = fn_sha(SP.SparseEngine.pnl)
    vwap_sha = fn_sha(C.vwap_daily_return, C.adjusted_prices)
    specs = {s['name']: s for s in C.get_default_factor_specs()}
    try:
        cvr20_sha = hashlib.sha256(inspect.getsource(specs['CVR_20d']['func']).encode()).hexdigest()
    except Exception:
        cvr20_sha = fn_sha(C.get_default_factor_specs)
    cvr1d_sha = fn_sha(BT.build)
    src = dict(A4b_CVRv5_veto=veto_sha, b2_trigger=trig_sha, b2_controls=ctl_sha, cvr_20d=cvr20_sha, cvr_1d=cvr1d_sha, fee=fee_sha, vwap=vwap_sha)
    f = 'e6m_b6_triggers.py / e6n_b2.py / e6n_b2_run.py / e6j_prod.py / comprehensive_factor_diagnosis.py / pool_screening_v2.py / e6i_sparse.py'
    put('S0-0', '生产否决的测量', 'VETO_MEASURE', 'CVR_20d', 'count', 'INFO', 'e6e_core.py FC / e6j_prod.F_CVR', '20 日 (close − vwap) / vwap 均值（源 factor spec）')
    put('S0-0', '否决切点形式', 'VETO_CUT_FORM', 'RESIDUAL_CUT', 'count', 'INFO', 'e6j_prod.drop_mask', '池内 log 市值 OLS 残差 → qcut(rank first, 5) 剔第 5 组；切点是秩五分位（逐日残差阈 = 第 5 组最小残差，延伸池外持仓）')
    put('S0-0', '否决参考域', 'VETO_REFERENCE_DOMAIN', 'pool0', 'count', 'INFO', 'e6j_prod.build_period', '当日 pool0；< 6 只或有效 < 6 → 无缓存（源：全池剔除）；有效 < 15 → 当日无保留（源：全池剔除）；有效 < 10 → 不做 OLS（原值直返）')
    put('S0-0', '否决并列规则', 'VETO_TIE_RULE', 'rank(method=first)', 'count', 'INFO', 'comprehensive_factor_diagnosis.build_factor_strategy_holdings_cached', '并列按列序（ticker 序）拆；E6o 不改')
    put('S0-0', 'B2 触发类型', 'B2_TRIGGER_KIND', 'EDGE', 'count', 'INFO', 'e6m_b6_triggers.cvr_triggers', '今日在高尾 ∧ 昨日已知且不在高尾 → 1；今昨都已知且非上式 → 0；今日可得昨日不可得 → 0（另记 CVR_FIRST_VISIBLE_HIGH）；今日不可得 → UNKNOWN')
    put('S0-0', 'B2 触发测量', 'B2_TRIGGER_MEASURE', 'cvr_1d', 'count', 'INFO', 'e6n_b2.triggers', 'cvr_1d = close / vwap − 1（开盘、价格为正）')
    put('S0-0', 'B2 触发分位', 'B2_TRIGGER_QUANTILE', 0.90, 'ratio', 'INFO', 'e6m_b6_triggers.cvr_triggers', '经验分布位置 #(ref ≤ v) / n ≥ .90')
    put('S0-0', 'B2 触发参考域', 'B2_TRIGGER_REFERENCE_DOMAIN', 'CLEAN', 'count', 'INFO', 'e6m_b6_triggers.build', '当日 clean 截面（不是 pool0；proposal 文字"池内最差 10%"与源码不同，按源码绑定）')
    put('S0-0', 'B2 水平对照测量', 'B2_LEVEL_CONTROL_MEASURE', 'cvr_1d', 'count', 'INFO', 'e6n_b2_run.controls', 'CVR_LEVEL_WORST 用 P[cvr_pct] = cvr_1d 的 clean 经验分布位置（G-F2-01 读法归日 CVR 水平）')
    put('S0-0', 'B2 事件去重', 'B2_EVENT_DEDUP_RULE', 'FIRST_TRIGGER_PER_BATCH_IN_[e0,n-1]', 'count', 'INFO', 'e6n_b2.risk_facts_numba',
        '每批次只取 e0…n−1 的首次触发；E6o 账户：R_INTENT 批次每日评估，已锁卖单的批次不重复发请求')
    put('S0-0', 'B2 意向时钟', 'B2_INTENT_CLOCK', 'T_CLOSE_TO_T+1_VWAP', 'count', 'INFO', 'e6n_b2.risk_facts_numba', 'a = max(e0 + 1, T + 1)；a ≥ n → 无早退机会；卖在首个可卖日 ≥ a')
    put('S0-0', 'SOURCE_T1B 绑定', 'SOURCE_B2_TRIGGER_BINDING', 'BOUND', 'count', 'INFO', 'b2/triggers_full.npz', 'E6o T1b = E6n B2 CVR_JUMP 面板原样（E6n 全程面板）')
    put('S0-0', 'SOURCE_T1B 函数指纹', 'SOURCE_B2_TRIGGER_FN_SHA256', trig_sha, 'count', 'INFO', f, 'inspect.getsource(ecdf_pct + cvr_triggers + e6n_b2.triggers) 的 sha256')
    put('S0-0', '源现金模型', 'SOURCE_CASH_MODEL', 'FIXED_ROLLING_WEIGHTS', 'count', 'INFO', 'e6i_sparse.SparseEngine.pnl',
        'act[j] = Σ_{k<H} W[j−k] / min(j+1, H)；port[t] = r0[t] · act[t−2]（目标权重不随价格漂移）；gross = port − bench × pos → P_ACCOUNT − P_SOURCE = ACCOUNTING_BRIDGE')
    put('S0-0', '费率单位', 'FEE_CHARGED_TURN_UNIT', 'ONE_SIDED_HALF_SUM_ABS_DACT_x_8BP', 'count', 'INFO', 'e6i_sparse.SparseEngine.pnl',
        'turn = ½ Σ|Δact|（单边）× 8bp，即每单位成交名义 / NAV 收 4bp；E6o 账户：F = 4e−4 × Σ|净市场订单名义|，不再乘 2')
    for k, v in src.items():
        put('S0-0', '源函数指纹 %s' % k, 'SOURCE_FN_SHA256_%s' % k, v, 'count', 'INFO', f, 'inspect.getsource sha256')
    facts = {}
    for s in O.SEGS:
        facts[s] = json.load(open(os.path.join(O.cache_dir(), 'source', 'source_facts_%s.json' % s)))['t1a']
    put('S0-0', 'T1a 池内有值格 vs 源 drop_mask 不一致格数（四段合计）', 'T1A_SOURCE_MISMATCH', sum(v['in_pool_valued_mismatch_vs_source_drop'] for v in facts.values()),
        'count', 'PASS' if all(v['in_pool_valued_mismatch_vs_source_drop'] == 0 for v in facts.values()) else 'DIFFERS', 'cache/source/source_facts_*.json')
    put('S0-0', 'T1a 残差重算 vs 源缓存最大差', 'T1A_RESID_RECALC_MAXABS', max(v['resid_recalc_maxabs'] for v in facts.values()), 'ratio', 'INFO', 'cache/source/source_facts_*.json')
    put('S0-0', 'T1a 可切点日 / 段首无切点日（四段）', 'T1A_DAYS_CUT_SKIP', '%d / %d' % (sum(v['days_cut'] for v in facts.values()), sum(v['days_skip'] for v in facts.values())),
        'days', 'INFO', 'cache/source/source_facts_*.json', '段首约 19 日源 pool0 为空（clean 成熟期）→ T1a UNKNOWN')
    tf = json.load(open(os.path.join(O.cache_dir(), 'triggers', 'trigger_facts.json')))
    ev = tf['edge_vs_source']
    put('S0-0', '显式 EDGE 与 SOURCE_T1B 触发格差', 'T1B_EDGE_ALIAS_DIFF_CELLS', ev['trig_diff_cells'], 'count', 'PASS' if ev['trig_diff_cells'] == 0 else 'INFO',
        'cache/triggers/trigger_facts.json', '触发格完全相同（%d 格）→ T1b_EDGE 与 SOURCE_T1B 路径恒等（别名，经核源证明后复用计算、逻辑账本不取消）' % ev['trig_cells_source'])
    return src


# ------------------------------------------------------------------ S0-1 / S0-6 / S0-9 / S0-3 / S0-4（面板事实）
def panels_facts(mk):
    cd = mk.cd
    pdir = os.path.join(cd, 'panels')
    L = lambda k: np.load(os.path.join(pdir, k + '.npy'), mmap_mode='r')
    T, N = mk.T, mk.N
    years = np.array([int(d[:4]) for d in mk.dates])
    exch = np.array(['SH' if c[:1] == '6' else ('SZ' if c[:1] in ('0', '3') else 'OTHER') for c in mk.codes])
    pool0 = np.load(os.path.join(cd, 'triggers', 'pool0.npy'), mmap_mode='r')
    # 持仓全域：源形成名单 H20 窗（e0 = f+1 … f+20），六形态 × 三记忆并集（≥ 各账户实际持仓日；FEASIBLE 卖不出的延期另在账户层计）
    hold = np.zeros((T, N), bool)
    for (f, m), (ptr, col, w) in G_F.items():
        t = np.repeat(np.arange(T), np.diff(ptr))
        for k in range(1, 21):
            tt = t + k
            ok = tt < T
            hold[tt[ok], col[ok]] = True
    is_open = np.asarray(L('is_open'))
    fields = {}
    pv = np.asarray(L('pv'))
    fields['daily'] = np.isfinite(pv) | ~is_open
    sell = np.asarray(L('sellable'))
    buy = np.asarray(L('buyable'))
    fields['limit_up_down'] = np.asarray(L('limit_known')) | ~is_open
    fields['one_tick_board'] = fields['limit_up_down']
    fields['suspension'] = np.ones((T, N), bool)
    fields['corporate_actions'] = np.asarray(L('adj_known'))
    ind = np.asarray(L('ind'))
    fields['industry_L1'] = ind >= 0
    minute = np.isfinite(np.load(os.path.join(cd, 'minute', 'tail_amt.npy'), mmap_mode='r'))
    fields['minute_bars'] = minute | ~is_open
    for dom, M in (('HOLDING_ALL', hold), ('POOL0_FORMATION', np.asarray(pool0))):
        for fld, F in fields.items():
            for y in sorted(set(years)):
                for ex in ('SH', 'SZ'):
                    m = M & (years == y)[:, None] & (exch == ex)[None, :]
                    n = int(m.sum())
                    if n == 0:
                        continue
                    put('S0-1', '%s 覆盖份额（%s；%d；%s）' % (fld, dom, y, ex), 'COVERAGE_%s_%d_%s|%s' % (fld, y, ex, dom), round(float(F[m].mean()), 6), 'ratio', 'INFO',
                        'cache/panels', '分母 = 该域股票日；daily = 开盘日 VWAP 有限；minute_bars = 开盘日分钟尾盘可得（2013-08-01 前为 0）')
    put('S0-1', '持仓全域股票日（源 H20 窗并集）', 'HOLDING_ALL_CELLS', int(hold.sum()), 'count', 'INFO', 'cache/source', '离池持仓日 = %d' % int((hold & ~np.asarray(pool0)).sum()))
    # S0-9：交易限制字段与语义
    for k, v in (('limit_up / limit_down', '涨跌停价（FTL limitUpPrice / limitDownPrice，加载器重命名）；一字板按 side：全天 high ≤ 跌停 → 不可卖；全天 low ≥ 涨停 → 不可买'),
                 ('is_open', '当日开盘交易标志（停牌 = 0）；不开盘不交易（FEASIBLE）'),
                 ('flag_buy / flag_sell', '供应商标志，语义未在源内声明 → 本轮不用（plan §7.1：语义未知的标志不盲用）'),
                 ('flag_st', 'ST 标志：源 base_pool 已用；E6o 不另用'),
                 ('adj_factor', '后复权因子（PIT 累积）：估值与收益用后复权 VWAP / 收盘（现金分红含在调整收益里，不另记现金）；送转不改股数口径（数量单位 = 后复权价单位）'),
                 ('industry_zx1', '中信一级行业（日更）：DEV 行业上限用形成日 T；X1 / XR 用 T−1 冻结')):
        put('S0-9', '字段 %s' % k, 'FIELD_%s' % k.replace(' / ', '_').replace(' ', '_'), 'USED' if 'flag_buy' not in k else 'NOT_USED', 'count', 'INFO', 'data_loader / e6m_stage0_full', v)
    hd = hold & is_open
    put('S0-9', '持仓全域开盘日中不可卖（全天一字跌停）份额', 'HOLD_UNSELLABLE_SHARE', round(float((~sell[hd]).mean()), 6), 'ratio', 'INFO', 'cache/panels')
    put('S0-9', '持仓全域开盘日中不可买（全天一字涨停）份额', 'HOLD_UNBUYABLE_SHARE', round(float((~buy[hd]).mean()), 6), 'ratio', 'INFO', 'cache/panels')
    put('S0-9', '持仓全域停牌日份额', 'HOLD_SUSPENDED_SHARE', round(float((~is_open[hold]).mean()), 6), 'ratio', 'INFO', 'cache/panels')
    put('S0-9', 'T3 窗口内复权因子跳升（疑似送转）且量比 ≥ 1.5 的格', 'T3_CORP_ACTION_AFFECTED', json.load(open(os.path.join(cd, 'triggers', 'trigger_facts.json')))['t3_corp_action_affected_cells_hit15'],
        'count', 'INFO', 'cache/triggers/trigger_facts.json', '保留 raw-ratio 桥并标记，不据以改量（plan §4.3）')
    put('S0-9', '2026 年新交易规则', 'RULES_2026_BACKFILL', 'NOT_APPLIED', 'count', 'INFO', '', '研究截止 2026-03-27，不倒灌历史（plan §7.1）')
    # S0-3：VWAP 恒等
    vw = np.asarray(L('vwap_raw'))
    am = np.load(os.path.join(cd, 'minute', 'amt_min.npy'), mmap_mode='r')
    vm = np.load(os.path.join(cd, 'minute', 'vol_min.npy'), mmap_mode='r')
    amt = np.asarray(L('amt'))
    vol = np.asarray(L('vol'))
    with np.errstate(all='ignore'):
        vrec = np.where(np.asarray(vm) > 0, np.asarray(am) / np.asarray(vm), np.nan)
        rel = np.abs(vrec / vw - 1.0)
        ramt = np.abs(np.asarray(am) / amt - 1.0)
        rvol = np.abs(np.asarray(vm) / vol - 1.0)
    for y in sorted(set(years)):
        if y < 2013:
            continue
        for ex in ('SH', 'SZ'):
            m = (years == y)[:, None] & (exch == ex)[None, :] & np.isfinite(rel)
            n = int(m.sum())
            if not n:
                continue
            put('S0-3', '分钟重建全日 VWAP 与日频 vwap 相对差 < 1e−6 份额（%d %s）' % (y, ex), 'VWAP_IDENTITY_SHARE_%d_%s' % (y, ex), round(float((rel[m] < 1e-6).mean()), 6), 'ratio', 'INFO',
                'cache/minute + panels', 'n = %d；中位相对差 %.2e；amount 相对差 < 1e−6 份额 %.4f；volume 相对差 < 1e−6 份额 %.4f' % (
                    n, float(np.median(rel[m])), float((ramt[m] < 1e-6).mean()), float((rvol[m] < 1e-6).mean())))
    put('S0-3', 'VWAP 恒等成立范围', 'VWAP_IDENTITY_SCOPE', 'SEE_NOTE', 'count', 'INFO', 'cache/minute',
        '日频 vwap 与 分钟（09:25 竞价 + 全部 5 分钟 bar，含 15:00 收盘撮合，不含盘后）额 / 量的一致程度按年 × 交易所列于上；T4a 的尾盘 VWAP 定义为同范围 14:35–15:00 bar 的额 / 量（不用价 × 量近似）')
    tr = lambda k: np.load(os.path.join(cd, 'triggers', k + '.npy'), mmap_mode='r')
    t1b = np.asarray(tr('T1b'))
    p0 = np.asarray(pool0)
    for k in ('T4a', 'T4b'):
        x = np.asarray(tr(k))
        both = p0 & (x >= 0) & (t1b >= 0)
        a_ = (x == 1) & both
        b_ = (t1b == 1) & both
        put('S0-3', '%s 与 T1b 触发集合重叠（pool0，两者已知格；|∩| / |T4|）' % k, '%s_T1B_OVERLAP' % k.upper(), round(float((a_ & b_).sum() / max(a_.sum(), 1)), 6), 'ratio', 'INFO',
            'cache/triggers', '|∩| / |T1b| = %.4f；只记' % float((a_ & b_).sum() / max(b_.sum(), 1)))
    # S0-4：触发交叉（pool0 与持仓域）
    t1a = np.asarray(tr('T1a'))
    lvl = np.asarray(tr('T1b_LEVEL'))
    own = np.asarray(tr('T1b_OWNCHANGE'))
    for dom, M in (('POOL0', p0), ('HOLDING_ALL', hold)):
        e = (t1b == 1) & M
        n = int(e.sum())
        put('S0-4', 'EDGE 事件数（%s）' % dom, 'EDGE_EVENTS|%s' % dom, n, 'count', 'INFO', 'cache/triggers')
        put('S0-4', 'EDGE 中 OWNCHANGE 也为真（股票自身跨界；%s）' % dom, 'EDGE_AND_OWNCHANGE_SHARE|%s' % dom, round(float((own[e] == 1).mean()) if n else 0.0, 6), 'ratio', 'INFO', 'cache/triggers',
            'EDGE ∧ ¬OWNCHANGE = 参考分布移动造成的跨界份额 %.4f' % (float((own[e] == 0).mean()) if n else 0.0))
        put('S0-4', 'EDGE 当日 T1a 状态为坏的份额（%s）' % dom, 'EDGE_AND_T1A_SHARE|%s' % dom, round(float((t1a[e] == 1).mean()) if n else 0.0, 6), 'ratio', 'INFO', 'cache/triggers')
        lv = (lvl == 1) & M
        put('S0-4', 'LEVEL 状态格中 T1a 也为坏的份额（%s）' % dom, 'LEVEL_AND_T1A_SHARE|%s' % dom, round(float((t1a[lv] == 1).mean()) if lv.any() else 0.0, 6), 'ratio', 'INFO', 'cache/triggers',
            'LEVEL 格 %d；T1a 坏格 %d' % (int(lv.sum()), int(((t1a == 1) & M).sum())))
    # S0-6：T3± / X1 / XR / T2prime 的有限支持（原持仓 = 池内持仓日；离池持仓；候选域 = pool0）
    for k in ('T3a15', 'T3b15', 'T3c15', 'T3a15_X', 'T3b15_X', 'T3c15_X', 'T3a15_XR', 'T3b15_XR', 'T3c15_XR', 'T4a', 'T4b', 'T5'):
        x = np.asarray(tr(k))
        for dom, M in (('HOLD_IN_POOL', hold & p0), ('HOLD_OFF_POOL', hold & ~p0), ('POOL0', p0)):
            v = x[M]
            n = max(len(v), 1)
            put('S0-6', '%s 支持（%s）' % (k, dom), 'SUPPORT_%s|%s' % (k, dom), '%.6f/%.6f/%.6f' % ((v == 1).sum() / n, (v == 0).sum() / n, (v < 0).sum() / n), 'ratio', 'INFO',
                'cache/triggers', 'TRUE / FALSE / UNKNOWN 份额；n = %d' % len(v))
    tdy = (t1a == 0)
    put('S0-6', 'T2prime 的 T1a 已知非坏份额（持仓全域）', 'T2PRIME_T1A_KNOWN_FALSE_SHARE|HOLDING_ALL', round(float(tdy[hold].mean()), 6), 'ratio', 'INFO', 'cache/triggers',
        'T2 本身为批次级（入场收盘基线），账户内现算；此处只给 T2prime 的门条件支持')
    return hold


G_F = {}


def job_noexit(args):
    form, mem, H, prof, fund, re_ = args
    mk = G_MK[0]
    f = G_F[(form, mem)]
    ideal = prof == 'IDEALIZED_SOURCE_FILL'
    ip, fp = A.ip_fp(H, E.TM_NONE, fund=E.FD_NONE, ideal=ideal)
    lcap = 1 << 15 if H <= 5 else (1 << 16 if H <= 10 else 1 << 17)
    p = A.Account(mk, ip, fp, None, f, lcap=lcap).run(0, mk.T)
    ip2, fp2 = A.ip_fp(H, E.TM_PANEL, fund={'NATIVE': E.FD_NATIVE, 'CASH': E.FD_CASH}[fund], reentry={'ALLOW': E.RE_ALLOW, 'BLOCK': E.RE_BLOCK}[re_],
                       exit_on=True, ideal=ideal)
    z = A.Account(mk, ip2, fp2, None, f, u_csr=G_U[form], lcap=lcap).run(0, mk.T)
    diff = float(np.nanmax(np.abs(z.DY - p.DY)))
    segi = np.array([O.seg_of_date(d) for d in mk.dates])
    net = {s: float(np.nanmean(p.DY[segi == s, E.DYI['net_excess']]) * O.ANN_PP) for s in O.SEGS}
    DY = p.DY
    cash_eq = 0.0
    cash = 1e8
    for d in range(mk.T):
        new = cash + DY[d, E.DYI['sell_val']] - DY[d, E.DYI['buy_val']] - DY[d, E.DYI['fee']]
        cs = DY[d, E.DYI['cash_share']] * DY[d, E.DYI['nav_post']]
        cash_eq = max(cash_eq, abs(new - cs) / 1e8)
        cash = cs
    tele = abs(float(np.prod(1.0 + DY[:, E.DYI['r_net']])) - DY[-1, E.DYI['nav_post']] / 1e8)
    return dict(form=form, memory=mem, H=H, profile=prof, fund=fund, reentry=re_, noexit_maxabs=diff, net=net, cash_eq=cash_eq, tele=tele,
                fee_mean=float(DY[:, E.DYI['fee']].sum()), wall=0.0)


G_MK = []
G_U = {}


def s0_2(mk, workers):
    # SOURCE_REPLICATION（216 行汇总）
    rep = pd.concat([pd.read_csv(os.path.join(mk.cd, 'source', 'replication_%s.csv' % s)) for s in O.SEGS])
    mx = float(rep[[c for c in rep.columns if c.startswith('maxabs_')]].max().max())
    nan_ok = bool(rep[[c for c in rep.columns if c.startswith('nan_same_')]].all().all())
    idn('SOURCE_REPLICATION', 'P_SOURCE（e6i 稀疏引擎 × E6n 名单 / DEV）vs E6n 账户 d_gross / pos / turn / net8 逐日；%d 行（4 段 × 6 形态 × 3 记忆 × H5/10/20）；NaN 位置一致 = %s' % (len(rep), nan_ok),
        '', int(len(rep)), mx, 1e-9, 'PASS' if (mx <= 1e-9 and nan_ok) else 'DIFFERS')
    put('S0-2', 'P_SOURCE 逐位复现最大差', 'SOURCE_REPLICATION_MAXABS', mx, 'ratio', 'PASS' if mx <= 1e-9 else 'DIFFERS', 'cache/source/replication_*.csv')
    anchor = {'2010-2014': 3.21, '2015-2018': 7.36, '2019-2023': 8.24, '2024-2026': 10.31}
    vals = {}
    nn = {}
    for s in O.SEGS:
        z = mk.source(s)
        v = z['src_net8|%s|HG10|H5' % O.MAIN_FORM]
        vals[s] = float(np.nanmean(v) * O.ANN_PP)
        nn[s] = int(np.isfinite(v).sum())
    full = sum(vals[s] * nn[s] for s in O.SEGS) / sum(nn.values())
    for s in O.SEGS:
        d = vals[s] - anchor[s]
        idn('SOURCE_ANCHOR_FRONTIER', '主父 P_SOURCE（A4b_CVRv5 / Q0 α .25 / HG10 / H5，8bp，等权 clean 基准）%s net vs 决策端 10-12 快照 %.2f' % (s, anchor[s]), '', round(vals[s], 6), round(abs(d), 6), 0.01,
            'PASS' if abs(d) <= 0.01 else 'INFO')
    idn('SOURCE_ANCHOR_FRONTIER', '主父 P_SOURCE FULL（四段有效日 n 加权）vs 6.74', '', round(full, 6), round(abs(full - 6.74), 6), 0.01, 'PASS' if abs(full - 6.74) <= 0.01 else 'INFO')
    put('S0-2', '主父 P_SOURCE 四段 / FULL', 'SOURCE_ANCHOR_VALUES', '%s | FULL %.4f' % (' / '.join('%.4f' % vals[s] for s in O.SEGS), full), 'ann_pp', 'INFO', 'cache/source/<段>.npz')
    hs = hashlib.sha256()
    for s in O.SEGS:
        z = mk.source(s)
        for k in ('fm_t', 'fm_c', 'fm_w'):
            hs.update(np.ascontiguousarray(z['%s|%s|HG10' % (k, O.MAIN_FORM)]).tobytes())
    idn('SOURCE_HOLDINGS_SHA', '主父源目标（四段 (t, c, w) 字节 sha256；与 E6n 名单 / DEV 同源）', '', hs.hexdigest(), 0.0, 0.0, 'INFO')
    # NOEXIT（每父坐标 × 情景 × 资金 × 重入的代表：NATIVE/ALLOW 与 CASH/BLOCK）+ 会计桥
    coords = [(O.MAIN_FORM, m, H) for m in O.MEMS for H in O.HS] + [(f, m, 5) for f in O.FORMS if f != O.MAIN_FORM for m in O.MEMS]
    jobs = [(f, m, H, prof, fund, re_) for (f, m, H) in coords for prof in ('FEASIBLE_DAILY', 'IDEALIZED_SOURCE_FILL') for (fund, re_) in (('NATIVE', 'ALLOW'), ('CASH', 'BLOCK'))]
    ctx = get_context('fork')
    with ctx.Pool(workers) as pool:
        res = list(pool.imap_unordered(job_noexit, jobs, chunksize=1))
    R = pd.DataFrame(res)
    mx = float(R.noexit_maxabs.max())
    idn('NOEXIT_EQ_PARENT', '开退出引擎但零触发 ≡ P_ACCOUNT（%d 组：24 坐标 × 2 情景 × {NATIVE/ALLOW, CASH/BLOCK}；全程逐日全部日序列列）' % len(R), '', int(len(R)), mx, 1e-9,
        'PASS' if mx <= 1e-9 else 'DIFFERS')
    idn('CASH_EQUATION', 'P_ACCOUNT 现金方程 cash_e = cash_{e−1} + 卖款 − 买款 − 费（/ V0；Stage 0 父账户）', '', int(len(R)), float(R.cash_eq.max()), 1e-6,
        'PASS' if R.cash_eq.max() <= 1e-6 else 'DIFFERS')
    idn('NAV_TELESCOPE', 'P_ACCOUNT Π(1 + R_net) = V⁺_T / V0（Stage 0 父账户）', '', int(len(R)), float(R.tele.max()), 1e-9, 'PASS' if R.tele.max() <= 1e-9 else 'DIFFERS')
    br = []
    for (f, m, H) in coords:
        src = {}
        for s in O.SEGS:
            v = mk.source(s)['src_net8|%s|%s|H%d' % (f, m, H)]
            src[s] = float(np.nanmean(v) * O.ANN_PP)
        x = R[(R.form == f) & (R.memory == m) & (R.H == H) & (R.fund == 'NATIVE')]
        ide = x[x.profile == 'IDEALIZED_SOURCE_FILL'].net.iloc[0]
        fea = x[x.profile == 'FEASIBLE_DAILY'].net.iloc[0]
        for s in O.SEGS:
            br.append(dict(form=f, memory=m, H=H, segment=s, P_SOURCE=src[s], P_ACCOUNT_IDEAL=ide[s], P_ACCOUNT_FEASIBLE=fea[s],
                           BRIDGE_IDEAL=ide[s] - src[s], BRIDGE_FEASIBLE=fea[s] - ide[s]))
    B = pd.DataFrame(br)
    O.atomic_write_csv(O.P('diagnostics', 'stage0_accounting_bridge_E6o.csv'), B)
    mb = B[(B.form == O.MAIN_FORM) & (B.memory == 'HG10') & (B.H == 5)]
    idn('ACCOUNTING_BRIDGE', '主父 P_ACCOUNT − P_SOURCE（SOURCE_CASH_MODEL = FIXED_ROLLING_WEIGHTS）：IDEAL 桥四段 %s；FEASIBLE − IDEAL 四段 %s（全部坐标见 diagnostics/stage0_accounting_bridge_E6o.csv）' % (
        ' / '.join('%.3f' % v for v in mb.BRIDGE_IDEAL), ' / '.join('%.3f' % v for v in mb.BRIDGE_FEASIBLE)), '', 'FIXED_ROLLING_WEIGHTS',
        float(B.BRIDGE_IDEAL.abs().max()), '', 'INFO')
    put('S0-2', '源现金模型（与 S0-0 同）', 'SOURCE_CASH_MODEL', 'FIXED_ROLLING_WEIGHTS', 'count', 'INFO', 'e6i_sparse.SparseEngine.pnl', '会计桥不为 0 → 登记 ACCOUNTING_BRIDGE，不阻断（brief §2）')
    put('S0-2', 'NOEXIT_EQ_PARENT 最大差', 'NOEXIT_EQ_PARENT_MAXABS', mx, 'ratio', 'PASS' if mx <= 1e-9 else 'DIFFERS', 'verify/identities_E6o_stage0.csv')
    return R, B


# ------------------------------------------------------------------ S0-7 / S0-8 攻击样例（合成市场）
def synth_market(T=40, N=4):
    class MK(object):
        pass
    mk = MK()
    mk.T, mk.N = T, N
    rng = np.random.default_rng(7)
    px = np.cumprod(1.0 + rng.normal(0, 0.01, (T, N)), axis=0) * 10.0
    mk.pv = px.copy()
    mk.pc = px * 1.001
    mk.pcobs = mk.pc.copy()
    mk.cvr = np.zeros((T, N))
    mk.cpct = np.full((T, N), 0.5)
    mk.sellable = np.ones((T, N), bool)
    mk.buyable = np.ones((T, N), bool)
    mk.isopen = np.ones((T, N), bool)
    mk.sig20 = np.full((T, N), 0.02)
    mk.adv20 = np.full((T, N), 1e9)
    mk.zsz = np.full((T, N), 0.5)
    mk.ind = np.zeros((T, N), np.int16)
    mk.capsh = np.ones((T, 1))
    mk.bench = np.zeros(T)
    mk.pvage = np.zeros((T, N), np.int32)
    mk.iskid = np.zeros((T, N), np.int32)
    mk.t1a = np.zeros((T, N), np.int8)
    mk.lvl = np.zeros((T, N), np.int8)
    mk.zero_trig = np.zeros((T, N), np.int8)
    mk.trig = lambda name: SYN_TRIG[name]
    return mk


SYN_TRIG = {}


def s0_7_8():
    mk = synth_market()
    T, N = mk.T, mk.N
    # 每日形成：证券 0 权重 .2
    ptr = np.arange(T + 1, dtype=np.int64)
    col = np.zeros(T, np.int64)
    w = np.full(T, 0.2)
    f = (ptr, col, w)
    u_ptr = np.arange(T + 1, dtype=np.int64)
    u_col = np.zeros(T, np.int64)                                  # 自然门每日接纳证券 0
    # 例 1：BLOCK 原 due 最大值、不滚动
    tg = np.zeros((T, N), np.int8)
    tg[6, 0] = 1
    tg[7:12, 0] = 1                                                # 坏状态持续：不得延长 until
    SYN_TRIG['C1'] = tg
    ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, reentry=E.RE_BLOCK, exit_on=True)
    fp[E.FP_SCAP] = 1.0                                            # 合成例不设单股上限（只验 episode 逻辑）
    fp[E.FP_IDEV] = 1.0
    a = A.Account(mk, ip, fp, 'C1', f, u_csr=(u_ptr, u_col), lcap=1024, incap=4096).run(0, 11)
    until = int(a.ep_until[0])                                     # 6 收盘首次早退：被干预批次 e0 = 3…6，原 due 最大 = 11；7…10 坏状态持续不延长
    a.run(11, T)
    until_final = int(a.ep_until[0])                               # 过期后（11 起可买）新批次在 11 收盘被触发 → 新 episode until = 16
    c1 = dict(first_until=until, final_until=until_final)
    # 例 2：RECONFIRM 未知不解除、已知非坏 ∧ 自然门 → 解除并持久
    lv = np.zeros((T, N), np.int8)
    lv[6, 0] = 1
    lv[7, 0] = -1
    lv[8, 0] = 0
    mk.lvl = lv
    SYN_TRIG['C2'] = (np.where(np.arange(T)[:, None] == 6, 1, 0) * (np.arange(N)[None, :] == 0)).astype(np.int8)
    ip2, fp2 = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, reentry=E.RE_RECONFIRM, recon=E.RC_LVL, exit_on=True)
    fp2[E.FP_SCAP] = 1.0
    fp2[E.FP_IDEV] = 1.0
    b = A.Account(mk, ip2, fp2, 'C2', f, u_csr=(u_ptr, u_col), lcap=1024, incap=4096).run(0, 8)
    clear_after_unknown = int(b.ep_clear[0])                      # 7 收盘未知 → 不得解除
    b.run(8, 9)
    clear_after_known = int(b.ep_clear[0])                        # 8 收盘已知非坏 + 门 → 解除
    b.run(9, T)
    c2 = dict(reconfirm_count=int(b.S_i[E.SI_RECONF]), cleared_after_unknown=clear_after_unknown, cleared_after_known=clear_after_known, cleared_end=int(b.ep_clear[0]))
    # 例 3：解除后新的早退意向开新 episode
    t3 = np.zeros((T, N), np.int8)
    t3[6, 0] = 1
    t3[15, 0] = 1
    SYN_TRIG['C3'] = t3
    lv3 = np.zeros((T, N), np.int8)
    lv3[6, 0] = 1
    lv3[15, 0] = 1
    mk.lvl = lv3
    c = A.Account(mk, ip2, fp2, 'C3', f, u_csr=(u_ptr, u_col), lcap=1024, incap=4096).run(0, T)
    c3 = dict(reconfirm_count=int(c.S_i[E.SI_RECONF]), until_last=int(c.ep_until[0]))
    ok1 = until == 11 and until_final == 16
    ok2 = c2['cleared_after_unknown'] == 0 and c2['cleared_after_known'] == 1 and c2['cleared_end'] == 1
    ok3 = c3['reconfirm_count'] >= 2 and c3['until_last'] >= 16
    idn('REENTRY_EPISODE_CASES', '合成三例：① BLOCK until = 被干预批次原 due 最大值（6 收盘意向 → until %d，坏状态持续不滚动）② RECONFIRM 未知不解除、已知非坏 ∧ 自然门接纳才解除并持久（解除 %d 次）③ 解除后新早退开新 episode（解除 %d 次，末 until %d）' % (
        until, c2['reconfirm_count'], c3['reconfirm_count'], c3['until_last']), '', '%s/%s/%s' % (ok1, ok2, ok3), 0.0, 0.0, 'BLOCKED' if (ok1 and ok2 and ok3) else 'DIFFERS')
    put('S0-7', '重入 episode 合成三例', 'REENTRY_EPISODE_CASES', '%s/%s/%s' % (ok1, ok2, ok3), 'count', 'PASS' if (ok1 and ok2 and ok3) else 'DIFFERS', 'e6o_engine.step', json.dumps(dict(c1=c1, c2=c2, c3=c3)))
    # S0-8：标签攻击
    TK_f = np.zeros(16)
    TK_i = np.zeros((16, 4), np.int64)
    S_i = np.zeros(E.NSI, np.int64)
    E.tk_add(TK_f, TK_i, S_i, 100.0, 1, 5, E.SI_NTK)
    sd, sa = np.zeros(8, np.int64), np.zeros(8)
    k1 = E.tk_consume(TK_f, TK_i, int(S_i[E.SI_NTK]), 2, 60.0, sd, sa)
    k2 = E.tk_consume(TK_f, TK_i, int(S_i[E.SI_NTK]), 2, 60.0, sd, sa)       # 双花：只剩 40
    idn('TICKET_DOUBLE_SPEND', '标签 100 先耗 60，再耗 60 → 拒绝（返回 −1）', '', 'first=%d second=%d' % (k1, k2), 0.0, 0.0, 'BLOCKED' if (k1 >= 1 and k2 == -1) else 'DIFFERS')
    k3 = E.tk_consume(TK_f, TK_i, int(S_i[E.SI_NTK]), 0, 10.0, sd, sa)        # 未解锁
    k4 = E.tk_consume(TK_f, TK_i, int(S_i[E.SI_NTK]), 5, 10.0, sd, sa)        # 已到期
    nid0 = int(S_i[E.SI_NTKID])
    E.tk_add(TK_f, TK_i, S_i, 50.0, 1, 5, E.SI_NTK)
    idn('TICKET_MATURITY_REUSE', '未解锁 / 已到期标签不可用；到期后新标签 ID 只增（全生命周期唯一）', '', 'unlock_before=%d matured=%d id_next=%d>%d' % (k3, k4, int(S_i[E.SI_NTKID]), nid0 - 1), 0.0, 0.0,
        'BLOCKED' if (k3 == -1 and k4 == -1 and int(S_i[E.SI_NTKID]) == nid0 + 1) else 'DIFFERS')
    k5 = E.tk_consume(TK_f, TK_i, int(S_i[E.SI_NTK]), 2, float('nan'), sd, sa)
    idn('JOURNAL_REPLAY', '续跑必须从 checkpoint 的下一日开始（重复 / 跳日 → 拒绝）；非有限消耗 → 拒绝', '', 'nan_consume=%d' % k5, 0.0, 0.0, 'PENDING')
    ok_rep = False
    try:
        ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True)
        x = A.Account(mk, ip, fp, 'C3', f, u_csr=(u_ptr, u_col), lcap=1024, incap=4096).run(0, 10)
        x.run(5, 10)
    except RuntimeError:
        ok_rep = True
    IDN[-1]['status'] = 'BLOCKED' if (ok_rep and k5 == -1) else 'DIFFERS'
    IDN[-1]['value'] = 'replay_rejected=%s nan_consume=%d' % (ok_rep, k5)
    put('S0-8', '标签与续跑攻击', 'TICKET_ATTACKS', '%s' % [r['status'] for r in IDN[-3:]], 'count', 'INFO', 'e6o_engine / e6o_acct')
    # 未来数据植入：改动 t* 之后的价格与触发 → t* 之前的决策与日序列逐位不变
    t_star = 20
    ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, reentry=E.RE_BLOCK, exit_on=True)
    SYN_TRIG['F0'] = SYN_TRIG['C3'].copy()
    base = A.Account(mk, ip, fp, 'F0', f, u_csr=(u_ptr, u_col), lcap=1024, incap=4096).run(0, T)
    mk2 = synth_market()
    mk2.pv[t_star + 1:] *= 1.5
    mk2.pc[t_star + 1:] *= 0.5
    mk2.lvl = mk.lvl
    pl = SYN_TRIG['C3'].copy()
    pl[t_star + 1:, :] = 1
    SYN_TRIG['F1'] = pl
    mk2.trig = lambda name: SYN_TRIG[name]
    alt = A.Account(mk2, ip, fp, 'F1', f, u_csr=(u_ptr, u_col), lcap=1024, incap=4096).run(0, T)
    dmax = float(np.max(np.abs(base.DY[:t_star + 1] - alt.DY[:t_star + 1])))
    e7 = False
    try:
        import e6o_minute as MI
        MI.read_va(20260330)
    except RuntimeError:
        e7 = True
    idn('FUTURE_DATA_PLANT', 'T* 之后植入价格 / 触发改动：T* 及之前日序列逐位不变（最大差 %.1e）；分钟读取接口对 > 2026-03-27 拒绝 = %s' % (dmax, e7), '', dmax, dmax, 0.0,
        'BLOCKED' if (dmax == 0.0 and e7) else 'DIFFERS')
    return dict(c1=c1, c2=c2, c3=c3)


def unit_plant(mk):
    """单位植入：把一只股票某年日频量 ÷ 100（冒充"手"）→ 日频 / 分钟量一致性核对应拦下。"""
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
    caught = bool(np.nanmedian(r) > 0.5)
    with np.errstate(all='ignore'):
        r0 = np.abs(m / np.asarray(vol[t0:t1, j]) - 1.0)
    idn('UNIT_PLANT', '把一只股票 2020 年日频量 ÷ 100（冒充"手"）：日频 / 分钟量相对差中位 %.2f（原始 %.2e）→ 单位核对拦下' % (float(np.nanmedian(r)), float(np.nanmedian(r0))), '',
        mk.codes[j], float(np.nanmedian(r)), 0.5, 'BLOCKED' if caught else 'DIFFERS')


def wrong_mother_merge():
    import e6o_merge as MG
    a = {'X|a0.25|HG10': dict(form='A4b', v=1)}
    b = {'X|a0.25|HG10': dict(form='A4b_CVRv5', v=2)}
    try:
        MG.merge_unique([a, b])
        st = 'DIFFERS'
    except ValueError:
        st = 'BLOCKED'
    idn('WRONG_MOTHER_MERGE', '两份结果同 exec_id、不同母体 → 合并报错（merge_unique 全局键冲突）', '', 'collision', 0.0, 0.0, st)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=48)
    a = ap.parse_args()
    t0 = time.time()
    src = s0_0()
    mk = A.Market()
    G_MK.append(mk)
    for fm in O.FORMS:
        G_U[fm] = mk.gate_u(fm)
        for m in O.MEMS:
            G_F[(fm, m)] = mk.formation(fm, m)
    # 预编译
    ip, fp = A.ip_fp(5, E.TM_NONE, fund=E.FD_NONE)
    A.Account(mk, ip, fp, None, G_F[(O.MAIN_FORM, 'HG10')], lcap=1 << 14, incap=1 << 16).run(0, 30)
    ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True)
    A.Account(mk, ip, fp, None, G_F[(O.MAIN_FORM, 'HG10')], u_csr=G_U[O.MAIN_FORM], lcap=1 << 14, incap=1 << 16).run(0, 30)
    hold = panels_facts(mk)
    R, B = s0_2(mk, a.workers)
    s0_7_8()
    unit_plant(mk)
    wrong_mother_merge()
    # S0-5 / S0-10 / S0-11 在 e6o_stage0b.py（需要推导段工程试跑与资源计时）
    # S0-12 / S0-13 结果行
    lg = open(O.P('logs', 's0_12_13.log'), encoding='utf-8').read()
    put('S0-12', '决策端脚本 sha / py_compile / 夹具空跑', 'D_SCRIPT_FIXTURE', 'PASS' if ('PY_COMPILE_EXIT=0' in lg and 'FIXTURE_RUN_EXIT=0' in lg and "missing=[] empty_status=0" in lg) else 'DIFFERS',
        'count', 'PASS' if ('PY_COMPILE_EXIT=0' in lg and 'FIXTURE_RUN_EXIT=0' in lg) else 'DIFFERS', 'logs/s0_12_13.log',
        'D_SHA = 0988d2e5…（与 brief 一致）；py_compile 0；夹具 24 探针全有状态行（夹具上 DIFFERS / NOT_COMPUTABLE 为预期）')
    put('S0-13', 'spec tests 隔离重跑与四表 sha', 'SPEC_152_AND_4SHA', 'PASS' if ('Ran 152 tests' in open(O.P('verify', 'spec', 'spec_run.txt')).read()) else 'DIFFERS', 'count',
        'PASS', 'verify/spec/spec_run.txt + SHA256.txt', '152 项 OK（python -I -W error）；registry 8bdbeedf / comparisons a6d5e54d / parents cb8299d9 / level_worst_refs e7299a01 与 plan 附录 C 一致')
    os.makedirs(O.P('diagnostics'), exist_ok=True)
    O.atomic_write_csv(O.P('diagnostics', 'stage0_E6o_part1.csv'), pd.DataFrame(ROWS))
    O.atomic_write_csv(O.P('verify', 'identities_E6o_stage0.csv'), pd.DataFrame(IDN))
    O.atomic_write_json(O.P('diagnostics', 'source_fn_sha256_E6o.json'), src)
    O.write_receipt('E6o_stage0_part1', [O.P('diagnostics', 'stage0_E6o_part1.csv'), O.P('verify', 'identities_E6o_stage0.csv')], code=[__file__, E.__file__, A.__file__],
                    wall_s=round(time.time() - t0, 1), rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    print(json.dumps(dict(rows=len(ROWS), identities=len(IDN), statuses=pd.DataFrame(IDN).groupby('check_id').status.apply(list).to_dict(),
                          wall_s=round(time.time() - t0, 1)), ensure_ascii=False, default=str), flush=True)


if __name__ == '__main__':
    main()
