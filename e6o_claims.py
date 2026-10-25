# -*- coding: utf-8 -*-
"""E6o 声明与查询登记（附录 B.13；plan §12）：reports/claims_E6o.csv + reports/query_registry_E6o.csv + statistics/contrasts_E6o.csv，
并把结果字段追加进 registration/ledger_E_E6o.csv / ledger_G_E6o.csv（事前登记栏不动，只填 result / evidence_strength / probe_result 等）。
E01–E07 的符号与区间：配对日差（同日）的 stationary bootstrap（2,000 次、几何块长 20；相关账户共同抽日期），年化 ann_pp；事件级（E04 / E05）按日聚合后同法。
数字只从机器表与账户日序列现算。用法：python3 e6o_claims.py"""
import os
import re
import sys
import json
import math

import numpy as np
import pandas as pd

import e6o_core as O
import e6o_engine as E
import e6o_stats as ST

QROWS = []
CROWS = []
XROWS = []


def q(qid, table, filt, n_rows, gen='e6o_claims.py'):
    QROWS.append(dict(query_id=qid, table=table, filter=filt, n_rows=int(n_rows), generator=gen))
    return qid


NANTOK = re.compile(r'(?<![A-Za-z_])(nan|None)(?![A-Za-z_])')


def claim(cid, kind, author, statement, qid, table, exec_ids, val=np.nan, sign='', lo=np.nan, hi=np.nan, status='开放', note=''):
    """缺值在 %.4f 下会印成字面 nan：文字栏统一换成"—"（与 D 脚本 S22 同正则）。"""
    CROWS.append(dict(claim_id=cid, kind=kind, author=author, statement=NANTOK.sub('—', str(statement)), query_id=qid, table=table, exec_ids=exec_ids or '',
                      result_value=val, result_sign=sign, ci_lo=lo, ci_hi=hi, claim_status=status, note=NANTOK.sub('—', str(note))))


def sgn(x):
    return '' if not np.isfinite(x) else ('+' if x > 0 else ('−' if x < 0 else '0'))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--test_root', default='', help='测试用：statistics / events / verify 从该目录读，输出写该目录；不写账本')
    a = ap.parse_args()
    TR = a.test_root
    SP = (lambda *x: os.path.join(TR, *x)) if TR else O.P
    R = pd.read_csv(O.P('registration', 'registry_E6o.csv'), keep_default_na=False, na_values=[''])
    reg = R.set_index('exec_id')
    AS = pd.read_csv(SP('statistics', 'account_summary_E6o.csv'), keep_default_na=False, na_values=[''])
    asi = AS.set_index(['exec_id', 'segment'])
    RT = pd.read_csv(SP('statistics', 'randoms_E6o.csv'), keep_default_na=False, na_values=[''])
    rti = RT.set_index(['owner_exec_id', 'mechanism', 'segment'])
    PO = pd.read_csv(SP('statistics', 'policy_E6o.csv'), keep_default_na=False, na_values=[''])
    EV = pd.read_csv(SP('events', 'event_counts_E6o.csv'), keep_default_na=False, na_values=[''])
    S0 = pd.read_csv(O.P('diagnostics', 'stage0_E6o.csv'), keep_default_na=False, na_values=[''])
    cd = O.cache_dir()
    dates = np.load(os.path.join(cd, 'panels', 'dates.npy'))
    T = len(dates)
    W20 = ST.boot_matrix_fast(T, 2000, 20, O.stable_u64('E6o', 'BOOT', 'CLAIMS', 20) % (2 ** 32))
    cache = {}

    def ne(e):
        if e not in cache:
            h = reg.loc[e, 'exec_hash']
            cache[e] = np.load(O.P('accounts_run', 'full', h[:2], '%s.npz' % h), allow_pickle=False)['DY']
        return cache[e][:, E.DYI['net_excess']]

    def paired(e1, e2, mask=None, series2=None):
        a = ne(e1)
        b = ne(e2) if series2 is None else series2
        x = a - b
        m = np.isfinite(x) if mask is None else (np.isfinite(x) & mask)
        xx = np.where(m, x, 0.0)
        n = m.sum()
        val = float(xx.sum() / n * O.ANN_PP)
        bm = (W20 @ xx.astype(np.float32)) / (W20 @ m.astype(np.float32)) * O.ANN_PP
        return val, float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))

    def D(e, s='FULL', c='D_ann_pp'):
        try:
            return float(asi.loc[(e, s), c])
        except (KeyError, ValueError):
            return np.nan

    def find(form=O.MAIN_FORM, mem='HG10', H='H5', trig='T1b', fund='ENGINE_NATIVE', lag='lag1', mat='RESET_H', re_='ALLOW', eg='OFF', ex='ON', prof='FEASIBLE_DAILY'):
        e = '|'.join([form, 'a0.25', mem, H, trig, fund, lag if fund != 'CASH' else 'NA', mat if fund != 'CASH' else 'NA', re_, eg, ex, prof, 'ACCOUNT',
                      'MINUTE_2013' if trig in ('T4a', 'T4b', 'T5') else 'FULLHIST', 'CASH_V0', 'POLICY_E6O_PARENT_Q'])
        return e if e in reg.index else None

    main = find()
    tb = 'statistics/account_summary_E6o.csv'
    # ---------------- E01
    v, lo, hi = D(main), D(main, 'FULL', 'boot_lo'), D(main, 'FULL', 'boot_hi')
    try:
        rr = rti.loc[(main, 'AMOUNT_MATCH', 'FULL')]
        rm, mc = float(rr.rand_mean_D_ann_pp), float(rr.mcse)
    except KeyError:
        rm, mc = np.nan, np.nan
    q('Q-E01', tb + ' + statistics/randoms_E6o.csv', 'exec_id = 主对象 FEASIBLE；segment = FULL；mechanism = AMOUNT_MATCH', 2)
    st = '支持' if (v > 0 and v - rm > 0) else ('不支持' if v <= 0 else 'mixed')
    claim('E01', 'PREDICTION', 'Web plan v1.1', 'SOURCE_T1b主配置NATIVE/ALLOW净FULL相对同引擎父>0，并相对amount随机>0；不预言各段全正', 'Q-E01', tb, main, v, sgn(v), lo, hi, st,
          '相对同引擎父 FULL D = %.4f [%.4f, %.4f]；同金额随机均值 %.4f（MCSE %.4f），real − 随机 = %.4f' % (v, lo, hi, rm, mc, v - rm))
    XROWS.append(dict(contrast='E01_MAIN_EXIT', a=main, b=reg.loc[main, 'parent_exec_id'], segment='FULL', value=v, ci_lo=lo, ci_hi=hi))
    # ---------------- E02（同金额：各自减去同金额随机均值后比较；原生差另报）
    lv, ed = find(trig='T1b_LEVEL'), find(trig='T1b_EDGE')
    vn, lon, hin = paired(lv, ed)
    try:
        r_l = float(rti.loc[(lv, 'AMOUNT_MATCH', 'FULL')].rand_mean_D_ann_pp)
        r_e = float(rti.loc[(ed, 'AMOUNT_MATCH', 'FULL')].rand_mean_D_ann_pp)
        mc_l = float(rti.loc[(lv, 'AMOUNT_MATCH', 'FULL')].mcse)
        mc_e = float(rti.loc[(ed, 'AMOUNT_MATCH', 'FULL')].mcse)
    except KeyError:
        r_l = r_e = mc_l = mc_e = np.nan
    ctl = (D(lv) - r_l) - (D(ed) - r_e)
    # 区间与点估同一估计量：原生配对差的 bootstrap 区间按 (随机_EDGE − 随机_LEVEL) 平移（随机均值作常数，其 MCSE 另报）
    lo2, hi2 = lon + (ctl - vn), hin + (ctl - vn)
    q('Q-E02', tb + ' + statistics/randoms_E6o.csv', 'T1b_LEVEL vs T1b_EDGE（主母体 HG10 H5 NATIVE ALLOW FEASIBLE）；FULL；AMOUNT_MATCH', 4)
    claim('E02', 'PREDICTION', 'Web plan v1.1', '主LEVEL在同金额/日龄下不弱于EDGE；原生LEVEL可能因多退而不同', 'Q-E02', tb, '%s;%s' % (lv, ed), ctl, sgn(ctl), lo2, hi2,
          '支持' if ctl >= 0 else '不支持', '同金额口径：(D_LEVEL − 随机_LEVEL) − (D_EDGE − 随机_EDGE) = %.4f [%.4f, %.4f]（区间 = 原生配对差 bootstrap 区间平移，随机均值 MCSE %.4f / %.4f 未计入）；'
          '原生配对差 D_LEVEL − D_EDGE = %.4f [%.4f, %.4f]' % (ctl, lo2, hi2, mc_l, mc_e, vn, lon, hin))
    # ---------------- E03
    pairs = []
    for mem in O.MEMS:
        for fund in ('ENGINE_NATIVE', 'CASH'):
            y11 = find(mem=mem, trig='T1b_LEVEL', fund=fund, eg='ON', ex='ON')
            y10 = find(mem=mem, trig='T1b_LEVEL', fund=fund, eg='ON', ex='OFF')
            if y11 and y10:
                pairs.append((mem, fund, y11, y10, *paired(y11, y10)))
    m0 = ([p for p in pairs if p[0] == 'HG10' and p[1] == 'ENGINE_NATIVE'] + pairs + [('NA', 'NA', '', '', np.nan, np.nan, np.nan)])[0]
    npos = sum(1 for p in pairs if p[4] > 0)
    q('Q-E03', 'accounts_run（日序列）+ ' + tb, 'ENTRY_EXIT 族 T1b_LEVEL：Y11（entry ON exit ON）− Y10（entry ON exit OFF）；3 记忆 × 2 资金；FULL', len(pairs))
    claim('E03', 'PREDICTION', 'Web plan v1.1', '对日LEVEL卖已有库存相对只停新买仍有正FULL贡献', 'Q-E03', tb, '%s;%s' % (m0[2], m0[3]), m0[4], sgn(m0[4]), m0[5], m0[6],
          '支持' if (m0[4] > 0 and npos >= 4) else ('不支持' if (m0[4] <= 0 and npos <= 2) else 'mixed'),
          'HG10 / NATIVE：Y11 − Y10 = %.4f [%.4f, %.4f]；6 组中为正 %d 组：%s' % (m0[4], m0[5], m0[6], npos, '; '.join('%s/%s %.3f' % (p[0], p[1][:6], p[4]) for p in pairs)))
    for p in pairs:
        XROWS.append(dict(contrast='E03_Y11_minus_Y10|%s|%s' % (p[0], p[1]), a=p[2], b=p[3], segment='FULL', value=p[4], ci_lo=p[5], ci_hi=p[6]))
    # ---------------- E04 / E05（事件级：父影子风险集，全程）
    ev = event_level()
    for k in ('E04', 'E05'):
        r = ev[k]
        q('Q-%s' % k, 'statistics/contrasts_E6o.csv', r['filter'], r['n'])
        claim(k, 'PREDICTION', 'Web plan v1.1', r['statement'], 'Q-%s' % k, 'statistics/contrasts_E6o.csv', r['exec'], r['value'], sgn(r['value']), r['lo'], r['hi'],
              r['status'], r['note'])
        XROWS.append(dict(contrast=k, a=r['exec'], b='', segment='FULL', value=r['value'], ci_lo=r['lo'], ci_hi=r['hi']))
    # ---------------- E06
    res6 = []
    for trig in ('T1b', 'T1b_LEVEL'):
        rc = find(trig=trig, re_='RECONFIRM')
        bk = find(trig=trig, re_='BLOCK')
        if rc and bk:
            res6.append((trig, rc, bk, *paired(rc, bk)))
    if not res6:
        res6.append(('NA', '', '', np.nan, np.nan, np.nan))
    v6 = res6[0][3]
    q('Q-E06', 'accounts_run + ' + tb, 'RECONFIRM − BLOCK（T1b、T1b_LEVEL；主母体 HG10 H5 NATIVE FEASIBLE）；FULL', 2)
    st6 = '支持' if all(r[3] > 0 for r in res6) else ('不支持' if all(r[3] <= 0 for r in res6) else 'mixed')
    claim('E06', 'PREDICTION', 'Web plan v1.1', 'RECONFIRM对BLOCK的主T1b/LEVEL全净FULL增量>0；代价是早恢复可能再遇坏状态', 'Q-E06', tb, '%s;%s' % (res6[0][1], res6[0][2]),
          v6, sgn(v6), res6[0][4], res6[0][5], st6, '; '.join('%s：RECONFIRM − BLOCK = %.4f [%.4f, %.4f]' % (r[0], r[3], r[4], r[5]) for r in res6))
    for r in res6:
        XROWS.append(dict(contrast='E06_RECONFIRM_minus_BLOCK|%s' % r[0], a=r[1], b=r[2], segment='FULL', value=r[3], ci_lo=r[4], ci_hi=r[5]))
    # ---------------- E07（冲击侵蚀：(D − D_imp)_NEXT − (D − D_imp)_NATIVE）
    er = []
    for mem in O.MEMS:
        for trig in ('T1a', 'T1b', 'T3c15_X', 'T4a'):
            for re_ in ('ALLOW', 'BLOCK'):
                nx = find(mem=mem, trig=trig, fund='NEXT_RANK', re_=re_)
                nv = find(mem=mem, trig=trig, fund='ENGINE_NATIVE', re_=re_)
                if nx and nv:
                    er_nx = D(nx) - D(nx, 'FULL', 'D_imp_ann_pp')
                    er_nv = D(nv) - D(nv, 'FULL', 'D_imp_ann_pp')
                    er.append((mem, trig, re_, nx, nv, er_nx - er_nv))
    vals = np.array([x[5] for x in er])
    v7 = float(np.nanmean(vals))
    # 区间与点估同一估计量：每对的日冲击成本差（各减各父；同父时父项相消）在"子 / 对照 / 父都有限"的共同日上，共同抽日期 bootstrap，每次重抽对 24 对取均值
    br = lambda e: cache.setdefault(e, np.load(O.P('accounts_run', 'full', reg.loc[e, 'exec_hash'][:2], '%s.npz' % reg.loc[e, 'exec_hash']), allow_pickle=False)['DY'])[:, E.DYI['impact_br']]
    kap = ST.K_MAIN * math.sqrt(ST.A_MAIN)
    est7, bms7 = [], []
    for (_m, _t, _r, nx, nv, _v) in er:
        pnx, pnv = reg.loc[nx, 'parent_exec_id'], reg.loc[nv, 'parent_exec_id']
        m_ = np.isfinite(ne(nx)) & np.isfinite(ne(nv)) & np.isfinite(ne(pnx)) & np.isfinite(ne(pnv))
        x_ = np.where(m_, kap * ((np.nan_to_num(br(nx)) - np.nan_to_num(br(pnx))) - (np.nan_to_num(br(nv)) - np.nan_to_num(br(pnv)))), 0.0)
        est7.append(float(x_.sum() / max(m_.sum(), 1)) * O.ANN_PP)
        with np.errstate(all='ignore'):
            bms7.append((W20 @ x_.astype(np.float32)) / (W20 @ m_.astype(np.float32)) * O.ANN_PP)
    if est7:
        v7d = float(np.mean(est7))
        bm = np.nanmean(np.vstack(bms7), 0)
    else:
        v7d, bm = np.nan, np.full(2, np.nan)
    m7 = ([x for x in er if x[0] == 'HG10' and x[1] == 'T1b' and x[2] == 'ALLOW'] + er + [('NA', 'NA', 'NA', '', '', np.nan)])[0]
    q('Q-E07', tb, 'FUNDING_NEXT vs CORE NATIVE（4 主触发 × 主母体三记忆 × 两重入，FEASIBLE）；FULL D − D_imp（A = 5 亿、κ = .5）', len(er))
    claim('E07', 'PREDICTION', 'Web plan v1.1', 'NEXT比NATIVE的增量更易被同规模冲击削弱', 'Q-E07', tb, '%s;%s' % (m7[3], m7[4]), v7, sgn(v7),
          float(np.nanpercentile(bm, 2.5)), float(np.nanpercentile(bm, 97.5)), '支持' if (v7 > 0 and (vals > 0).mean() >= 0.5) else ('不支持' if v7 <= 0 else 'mixed'),
          '%d 对冲击侵蚀差均值 %.4f（为正 %d / %d；由日序列现算 %.4f）；区间 = 各对日冲击成本差共同抽日期 bootstrap 后对对取均值（与点估同一估计量）' % (
              len(vals), v7, int((vals > 0).sum()), len(vals), v7d))
    # ---------------- Q01–Q18
    cards = pd.read_csv(O.P('registration', 'cards_E6o.csv'), keep_default_na=False)
    idn = pd.read_csv(SP('verify', 'identities_E6o.csv'), keep_default_na=False, na_values=[''])
    qmap = {}
    qmap['Q01'] = ('技术PASS' if (idn[idn.check_id.isin(['SOURCE_REPLICATION', 'NOEXIT_EQ_PARENT'])].status == 'PASS').all() else '技术FAIL',
                   'verify/identities_E6o.csv', "check_id ∈ {SOURCE_REPLICATION, NOEXIT_EQ_PARENT, ACCOUNTING_BRIDGE}", 'P_SOURCE 逐位复现；零触发 ≡ P_ACCOUNT；会计桥登记（FIXED_ROLLING_WEIGHTS）')
    for k, e in (('Q02', 'E01'), ('Q03', 'E02'), ('Q06', 'E03'), ('Q07', 'E04'), ('Q08', 'E05'), ('Q10', 'E06'), ('Q13', 'E07')):
        r = [c for c in CROWS if c['claim_id'] == e][0]
        qmap[k] = (r['claim_status'], r['table'], '同 %s' % e, '见 %s：%s' % (e, r['note'][:200]))
    own, edg = find(trig='T1b_OWNCHANGE'), find(trig='T1b_EDGE')
    qmap['Q04'] = ('开放', tb, 'OWNCHANGE vs EDGE / SOURCE（主母体 HG10 H5 NATIVE ALLOW）', 'D_OWNCHANGE = %.4f；D_EDGE = %.4f；D_SOURCE_T1B = %.4f；EDGE 事件中参考移动份额见 S0-4' % (D(own), D(edg), D(main)))
    t2, t2p = find(trig='T2'), find(trig='T2prime')
    qmap['Q05'] = ('开放', tb, 'T2 vs T2prime（主母体 HG10 H5 NATIVE ALLOW）', 'D_T2 = %.4f；D_T2prime = %.4f' % (D(t2), D(t2p)))
    t4 = {k_: find(trig=k_) for k_ in ('T4a', 'T4b', 'T5')}
    m13 = dates >= O.MINUTE_START
    b13 = paired(main, reg.loc[main, 'parent_exec_id'], mask=m13)[0]
    qmap['Q09'] = ('开放', tb, 'T4a / T4b / T5 FULL_2013 vs 同窗 T1b（主母体 HG10 H5 NATIVE ALLOW）', 'FULL_2013：T4a %.4f、T4b %.4f、T5 %.4f；同窗 T1b %.4f' % (
        D(t4['T4a'], 'FULL_2013'), D(t4['T4b'], 'FULL_2013'), D(t4['T5'], 'FULL_2013'), b13))
    e_main = EV[EV.exec_id == main].iloc[0]
    qmap['Q11'] = ('开放', 'events/event_counts_E6o.csv', 'exec_id = 主对象', '意向 %d、早退实现 %d、迟到 %d、内部转移证券日 %d、重入（原 due 前买回）见 account_summary n_reentries' % (
        e_main.n_intents, e_main.n_realized_early, e_main.n_late_fill, e_main.n_internal_transfers))
    fd = {k_: find(fund=k_) for k_ in ('CASH', 'NEXT_RANK')}
    l0, rmn = find(lag='lag0'), find(mat='ORIGINAL_DUE')
    qmap['Q12'] = ('开放', tb, '主对象坐标的资金去向（CASH / NATIVE / NEXT / lag0 / REMAIN）FULL D', 'NATIVE %.4f；CASH %.4f；NEXT %.4f；lag0 %.4f；REMAIN %.4f' % (
        D(main), D(fd['CASH']), D(fd['NEXT_RANK']), D(l0), D(rmn)))
    ideal = main.replace('|FEASIBLE_DAILY|', '|IDEALIZED_SOURCE_FILL|')
    qmap['Q14'] = ('开放', tb, '主对象 FEASIBLE vs IDEALIZED；父桥', 'FEASIBLE %.4f；IDEALIZED %.4f；P_ACCOUNT 可成交桥（FEASIBLE − IDEAL，FULL）%.4f' % (
        D(main), D(ideal), D(reg.loc[main, 'parent_exec_id']) - D(reg.loc[ideal, 'parent_exec_id'])))
    qmap['Q15'] = ('开放', 'diagnostics/S0_10_age_remaining_E6o.csv + diagnostics/D2_age_weight_E6o.csv', '日龄 × 剩余超额；事件 / 证券 / 批次日龄', '见 S0-10（剩余超额随日龄 0→3 递减）与 D-2')
    qmap['Q16'] = ('开放', 'statistics/yearly_D_E6o.csv + diagnostics/D4_regime_E6o.csv', '主对象逐年与状态分解', '主对象 G4 = %.4f；逐年与状态见 D-4' % D(main, 'G4'))
    pm = PO[(PO.exec_id == main) & (PO.profile_name == 'POLICY_E6O_PARENT_Q')].iloc[0]
    qmap['Q17'] = ('技术PASS', 'statistics/policy_E6o.csv', 'exec_id = 主对象', '主对象 POLICY_E6O_PARENT_Q：%s / %s；相对 P_SOURCE FULL %.4f' % (pm.verdict, pm.research_status, D(main, 'FULL', 'D_source_ann_pp')))
    qmap['Q18'] = ('技术PASS', 'reports/query_registry_E6o.csv', '全部 claims 的 query_id 闭合', '每条 G / E / CC / Q 声明绑定 query；deployment_authorized = false')
    for r in cards.itertuples():
        st_, tab, filt, note = qmap[r.q_id]
        qid = q('Q-%s' % r.q_id, tab, filt, 1)
        claim(r.q_id, 'QUESTION', 'Web plan v1.1（plan §12）', '%s｜%s' % (r.title, r.discrimination), qid, tab, main, np.nan, '', np.nan, np.nan, st_, note)
    # ---------------- CC 原句
    cc = pd.read_csv(O.P('registration', 'cc_carried_E6o.csv'), keep_default_na=False)
    lw = find(trig='T1b_LEVEL')
    t1a = find(trig='T1a')
    veto_pairs = [(D(find(trig=t)) - D(find(form='A4b', trig=t))) for t in ('T1a', 'T1b', 'T3c15_X', 'T4a')]
    x_pairs = [(D(find(trig='T3%s15_X' % s)) - D(find(trig='T3%s15' % s))) for s in ('a', 'b', 'c')]
    t6 = [D(find(trig='T6a')), D(find(trig='T6b'))]
    t1 = [D(t1a), D(main)]
    hold_mean = float(e_main.mean_realized_hold_days)
    s0 = S0.set_index('key')['value'].to_dict()
    unsell = float(s0.get('HOLD_UNSELLABLE_SHARE', 'nan'))
    ov = float(s0.get('T4A_T1B_OVERLAP', 'nan'))
    nxt = fd['NEXT_RANK']
    sc_ratio = D(nxt, 'FULL', 'D_sc_ann_pp')
    age_bp = []
    for a_ in range(0, 21):
        k_ = 'AGE_REMAINING_BP|HG10|age%d' % a_
        if k_ in s0:
            try:
                age_bp.append(float(s0[k_]))
            except (TypeError, ValueError):
                pass
    f = lambda x_, nd: ('%.' + str(nd) + 'f') % x_ if np.isfinite(x_) else '缺'
    b2 = b2_overlay()
    ccres = {
        'CC-01': ('支持' if (D(main) > 0 and D(main) - rm > 0) else ('不支持' if D(main) <= 0 else 'mixed'), D(main), '同 E01（MAIN_EXIT + AMOUNT_MATCH）'),
        'CC-02': (('支持' if D(fd['CASH']) < b2 else '不支持') if np.isfinite(b2) else '开放', D(fd['CASH']),
                  '对象不同：账户级 CASH D（FULL）%.4f vs E6n B2 CASH overlay（FIXED_H JOINT net，四段 n 加权）%.4f' % (D(fd['CASH']), b2)),
        'CC-03': ('支持' if (D(lw) >= D(edg) and D(t1a) >= D(t2)) else ('不支持' if (D(lw) < D(edg) and D(t1a) < D(t2)) else 'mixed'), D(lw) - D(edg),
                  'LEVEL − EDGE = %.4f；T1a − T2 = %.4f（同金额控制见 E02）' % (D(lw) - D(edg), D(t1a) - D(t2))),
        'CC-04': ('支持' if all(v_ < 0 for v_ in veto_pairs) else ('不支持' if all(v_ >= 0 for v_ in veto_pairs) else 'mixed'), float(np.nanmean(veto_pairs)),
                  '有否决 − 无否决（主触发 4 支 HG10）：%s' % ', '.join('%.3f' % v_ for v_ in veto_pairs)),
        'CC-05': ('开放', np.nan, '读法，不评分'),
        'CC-06': ('开放', D(find(trig='T3b15')), '条件句：D(T3b15) = %.4f、D(T1b) = %.4f；D 的符号不能单独证实"需求延续"这一条件' % (D(find(trig='T3b15')), D(main))),
        'CC-07': ('支持' if all(v_ >= 0 for v_ in x_pairs) else ('不支持' if all(v_ < 0 for v_ in x_pairs) else 'mixed'), float(np.nanmean(x_pairs)),
                  '带 X1 − 不带（a / b / c）：%s' % ', '.join('%.3f' % v_ for v_ in x_pairs)),
        'CC-08': ('支持' if (max(t6) <= 0 and min(t1) > max(t6)) else ('不支持' if (min(t6) > 0 and max(t1) <= min(t6)) else 'mixed'), float(np.nanmean(t6)),
                  'D(T6a) %.4f、D(T6b) %.4f；D(T1a) %.4f、D(T1b) %.4f' % (t6[0], t6[1], t1[0], t1[1])),
        'CC-09': ('支持' if D(t4['T4a'], 'FULL_2013') >= b13 else '不支持', D(t4['T4a'], 'FULL_2013') - b13,
                  '公共窗口（2013-08 起）D(T4a) %.4f vs D(T1b) %.4f' % (D(t4['T4a'], 'FULL_2013'), b13)),
        'CC-10': ('REPLACED_BEFORE_RUN', np.nan, 'plan D-1 不做不可识别分摊；只报暴露对比（D-1）'),
        'CC-11': ('mixed', np.nan, '日龄单调：S0-10（HG10，资本加权）剩余超额按日龄 %s bp（%s）；均持 > 3 日：主对象早退实现均持 %.2f 日；受限 < 5%%：持仓日不可卖 %.4f%%（%s）；重叠 < 50%%：T4a ∩ T1b / T4a = %.4f（%s）；"收缩到 ≈ 0"：NEXT 同资本 D_sc %.4f（派生读法）' % (
            ' → '.join(f(x_, 2) for x_ in age_bp) if age_bp else '缺', ('单调下降' if age_bp and all(a_ > b_ for a_, b_ in zip(age_bp, age_bp[1:])) else '非单调'),
            hold_mean, unsell * 100, '支持' if unsell < 0.05 else '不支持', ov, '支持' if ov < 0.5 else '不支持', sc_ratio)),
        'CC-12': ('REPLACED_BEFORE_RUN', np.nan, '不是门；作 REVIEW 读法'),
    }
    for r in cc.itertuples():
        st_, val, note = ccres[r.cc_id]
        qid = q('Q-%s' % r.cc_id, tb, '见 note', 1)
        claim(r.cc_id, 'CC_CARRIED', 'CC 决策端（E6o proposal v2，%s）' % r.source, r.original_statement, qid, tb, main, val, sgn(val), np.nan, np.nan, st_, note)
    # ---------------- G 链
    G1 = pd.read_csv(O.P('diagnostics', 'G1_E6o.csv'), keep_default_na=False, na_values=[''])
    def g1(item, stat, seg):
        x = G1[(G1['item'] == item) & (G1.key1 == 'ALL') & (G1.stat == stat) & (G1.segment == seg)]
        return float(x.value.iloc[0]) if len(x) else np.nan
    gtxt = {
        'G-F2-01': ('开放', 'G1（推导段）同日同日龄对照差：T1b %.2f / %.2f bp，T1b_LEVEL %.2f / %.2f bp；全程账户：LEVEL − EDGE FULL %.4f（E02）' % (
            g1('T1b|HG10', 'diff_vs_sameday_bp', '2010-2014'), g1('T1b|HG10', 'diff_vs_sameday_bp', '2015-2018'), g1('T1b_LEVEL|HG10', 'diff_vs_sameday_bp', '2010-2014'),
            g1('T1b_LEVEL|HG10', 'diff_vs_sameday_bp', '2015-2018'), D(lw) - D(edg))),
        'G-F2-02': ('开放', '闭环资金去向 FULL：NATIVE %.4f / CASH %.4f / NEXT %.4f；NEXT 同资本 D_sc %.4f（"缩至 ≈ 0"的派生读法见 CC-11）' % (D(main), D(fd['CASH']), D(nxt), sc_ratio)),
        'G-F2-03': ('开放', '有否决 − 无否决（主触发 HG10）：%s；四账户交互见 D-5' % ', '.join('%.3f' % v_ for v_ in veto_pairs)),
    }
    for gid, (st_, note) in gtxt.items():
        qid = q('Q-%s' % gid, 'diagnostics/G1_E6o.csv + ' + tb, 'G1 ALL 分层 + 账户 FULL', 1)
        claim(gid, 'G_CHAIN', 'CC 决策端（F2）/ Web plan v1.1 §3.4', '见 registration/ledger_G_E6o.csv 同 g_id', qid, tb, main, np.nan, '', np.nan, np.nan, st_, note)
    # 写出
    od = SP('reports')
    os.makedirs(od, exist_ok=True)
    QR = pd.DataFrame(QROWS).drop_duplicates('query_id')
    O.atomic_write_csv(os.path.join(od, 'query_registry_E6o.csv'), QR)
    O.atomic_write_csv(os.path.join(od, 'claims_E6o.csv'), pd.DataFrame(CROWS))
    O.atomic_write_csv(SP('statistics', 'contrasts_E6o.csv'), pd.DataFrame(XROWS))
    # 账本结果栏（只填结果字段）
    if TR:
        print(json.dumps(dict(test_root=True, claims=len(CROWS), queries=len(QROWS), contrasts=len(XROWS)), ensure_ascii=False), flush=True)
        return
    LE = pd.read_csv(O.P('registration', 'ledger_E_E6o.csv'), keep_default_na=False)
    for i, r in LE.iterrows():
        c = [x for x in CROWS if x['claim_id'] == r.e_id][0]
        LE.loc[i, 'result'] = '%s：%s' % (c['claim_status'], c['note'][:300])
        LE.loc[i, 'evidence_strength'] = 'CI 不跨 0' if (np.isfinite(c['ci_lo']) and (c['ci_lo'] > 0 or c['ci_hi'] < 0)) else 'CI 跨 0 或无区间'
        LE.loc[i, 'first_stage_evidence'] = 'G1（推导段）见 diagnostics/G1_E6o.csv'
        LE.loc[i, 'query_id'] = c['query_id']
    O.atomic_write_csv(O.P('registration', 'ledger_E_E6o.csv'), LE)
    LG = pd.read_csv(O.P('registration', 'ledger_G_E6o.csv'), keep_default_na=False)
    for i, r in LG.iterrows():
        if r.g_id in gtxt:
            LG.loc[i, 'probe_result'] = gtxt[r.g_id][1][:400]
            LG.loc[i, 'result_at'] = 'B 阶段（seal_A2 之后）'
            LG.loc[i, 'probe_code_hash'] = O.sha_file(os.path.join(os.path.dirname(O.__file__), 'e6o_g1.py'))[:16]
    O.atomic_write_csv(O.P('registration', 'ledger_G_E6o.csv'), LG)
    print(json.dumps(dict(claims=len(CROWS), queries=len(QR), contrasts=len(XROWS)), ensure_ascii=False), flush=True)


def b2_overlay():
    """E6n B2 CASH overlay（主母体 HG10 Q0 α .25；FIXED_H；CASH；JOINT_FROZEN；net；四段 n 加权）作 CC-02 的比较物。"""
    import glob
    fs = glob.glob(O.E6N('results', '*', 'b2', 'b2_order_overlay_*__*.csv'))
    if not fs:
        return np.nan
    D = pd.concat([pd.read_csv(f, keep_default_na=False, na_values=['']) for f in fs], ignore_index=True)
    m = (D.form == O.MAIN_FORM) & (D.object_key == 'HG10|a0.25|Q0') & (D.trigger == 'CVR_JUMP') & (D.H == 5) & (D.horizon_mode == 'FIXED_H') & (D.mirror == 'CASH') & (D.fee_mode == 'JOINT_FROZEN')
    x = D[m].drop_duplicates('segment')
    if len(x) < 4:
        return np.nan
    nd = {'2010-2014': 1212, '2015-2018': 975, '2019-2023': 1214, '2024-2026': 539}
    w = np.array([nd[s] for s in x.segment])
    return float(np.sum(w * pd.to_numeric(x.net_ann_pp).to_numpy()) / w.sum())


def event_level():
    """E04 / E05：主母体 HG10 H5 父影子批次（全程），首触发事件的剩余超额（至原 due）相对同日同日龄全部风险集批次；按日聚合后 bootstrap。"""
    import e6o_acct as A
    mk = A.Market()
    T = mk.T
    cd = mk.cd
    L = lambda k: np.load(os.path.join(cd, 'panels', k + '.npy'), mmap_mode='r')
    rv = np.asarray(L('r_vwap'))
    ex = np.where(np.isfinite(rv), rv - mk.bench[:, None], 0.0)
    ex = np.where(np.isfinite(ex), ex, 0.0)
    cs = np.vstack([np.zeros((1, ex.shape[1])), np.cumsum(ex, axis=0)])
    ptr, col, w = mk.formation(O.MAIN_FORM, 'HG10')
    f = np.repeat(np.arange(T), np.diff(ptr))
    H = 5
    e0 = f + 1
    due = e0 + H
    ok = due < T
    f, col, w, e0, due = f[ok], col[ok], w[ok], e0[ok], due[ok]
    li = np.repeat(np.arange(len(f)), H - 1)
    ag = np.tile(np.arange(H - 1), len(f))
    d = e0[li] + ag
    keep = d + 1 < due[li]
    li, ag, d = li[keep], ag[keep], d[keep]
    c = col[li]
    rem = cs[due[li] + 1, c] - cs[d + 2, c]
    key = d * 8 + ag
    base = pd.Series(rem).groupby(key).transform('mean').to_numpy()
    W = ST.boot_matrix_fast(T, 2000, 20, O.stable_u64('E6o', 'BOOT', 'EVENT', 20) % (2 ** 32))
    out = {}

    def first_events(st):
        idx = np.flatnonzero(st)
        if not len(idx):
            return np.zeros(len(li), bool)
        fst = pd.Series(idx).groupby(li[idx]).min().to_numpy()
        e = np.zeros(len(li), bool)
        e[fst] = True
        return e

    def daily_ci(x_ev, d_ev):
        s = np.zeros(T)
        n = np.zeros(T)
        np.add.at(s, d_ev, x_ev)
        np.add.at(n, d_ev, 1.0)
        bm = (W @ s.astype(np.float32)) / np.maximum(W @ n.astype(np.float32), 1.0) * 1e4
        return float(s.sum() / n.sum() * 1e4), float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5)), int(n.sum())

    tb = np.asarray(mk.trig('T3b15'))[d, c] == 1
    ev = first_events(tb)
    v, lo, hi, n = daily_ci((rem - base)[ev], d[ev])
    out['E04'] = dict(statement='T3b在旧父持有风险集的剩余收益相对同日龄匹配更弱；T3a方向开放并报延续/反转', value=v, lo=lo, hi=hi, n=n,
                      status='支持' if v < 0 else '不支持', exec='SHADOW_PARENT|A4b_CVRv5|HG10|H5',
                      filter='父影子批次（全程）T3b15 首触发事件：剩余超额 − 同日同日龄风险集均值（bp）', note='T3b15 事件 %d 个：差 %.2f bp [%.2f, %.2f]；T3a15 另报见 contrasts' % (n, v, lo, hi))
    ta = np.asarray(mk.trig('T3a15'))[d, c] == 1
    eva = first_events(ta)
    va, loa, hia, na = daily_ci((rem - base)[eva], d[eva])
    XROWS.append(dict(contrast='E04_T3a15_open', a='SHADOW_PARENT', b='', segment='FULL', value=va, ci_lo=loa, ci_hi=hia))
    out['E04']['note'] += '；T3a15（开放）%d 个：%.2f bp [%.2f, %.2f]' % (na, va, loa, hia)
    rank = np.asarray(L('ind_rank'))[d, c]
    peer = np.asarray(L('peer_ret'))[d, c]
    own = np.asarray(L('r_day'))[d, c]
    t3a = np.asarray(mk.trig('T3a15'))[d, c] == 1
    x1 = t3a & np.isfinite(rank) & (rank <= 0.2)
    xr = x1 & np.isfinite(peer) & np.isfinite(own) & (peer < 0) & (own < peer)
    e_x1 = first_events(x1)
    e_xr = first_events(xr)
    v1, _, _, n1 = daily_ci(rem[e_x1], d[e_x1])
    v2, _, _, n2 = daily_ci(rem[e_xr], d[e_xr])
    # 差的 bootstrap：两组按日聚合后的差
    s1 = np.zeros(T)
    c1 = np.zeros(T)
    s2 = np.zeros(T)
    c2 = np.zeros(T)
    np.add.at(s1, d[e_x1], rem[e_x1])
    np.add.at(c1, d[e_x1], 1)
    np.add.at(s2, d[e_xr], rem[e_xr])
    np.add.at(c2, d[e_xr], 1)
    bm = ((W @ s2.astype(np.float32)) / np.maximum(W @ c2.astype(np.float32), 1) - (W @ s1.astype(np.float32)) / np.maximum(W @ c1.astype(np.float32), 1)) * 1e4
    out['E05'] = dict(statement='XR_DOWN相对X1_RANK在同豁免预算下提高保留集剩余收益；账户全净另评', value=v2 - v1, lo=float(np.percentile(bm, 2.5)), hi=float(np.percentile(bm, 97.5)),
                      n=n2, status='支持' if v2 - v1 > 0 else '不支持', exec='SHADOW_PARENT|A4b_CVRv5|HG10|H5',
                      filter='T3a15 触发且被豁免的保留集剩余超额：XR_DOWN 豁免集 − X1_RANK 豁免集（bp / 事件；父影子全程）',
                      note='XR 豁免集 %d 个 %.2f bp；X1 豁免集 %d 个 %.2f bp（XR ⊂ X1：同豁免预算的逐事件均值口径）' % (n2, v2, n1, v1))
    return out


if __name__ == '__main__':
    main()
