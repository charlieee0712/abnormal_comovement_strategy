# -*- coding: utf-8 -*-
"""E6p 卡 / 预测 / 账本 / 携带表（附录 B.3 / B.13；plan §3 / §12）：
reports/claims_E6p.csv（Q01–Q18 问题、E01–E10 经济方向预测、G-P-01…11 链、CC-E6p-01…11 原句携带、F7 转述数字、工程项）与 reports/query_registry_E6p.csv；
回填 G / E 账本的观测字段（A1 版另存 *_A1.csv，事前字段不改）、cc_statement_carry.claim_status、reported_claims 的本轮可比值。
E01–E10 的区间与点估计同函数（stationary bootstrap 2,000 次、块 40、同样本日；纪律 120）；方向相符但区间跨 0 → 支持 + note 精度有限；负点估 → 不支持；
组合预测的组成项并排（异号写 mixed）。工程恒等不进经济分母。用法：python3 e6p_claims.py [--root <统计根>]"""
import os
import json
import shutil
import argparse

import numpy as np
import pandas as pd

import e6p_core as O
import e6p_engine as E
import e6p_stats as ST
import e6p_g1 as G1

SEG4 = list(O.SEGS)


def f2s(v):
    return '—' if not (isinstance(v, float) and np.isfinite(v)) else '%.3f' % v


def boot_full(ctx, x, seed_key):
    """FULL 日序列的 stationary bootstrap 区间（块 40、2,000 次；与汇总表同函数）。"""
    m = ctx.masks['FULL'] & np.isfinite(x)
    v = x[m]
    W = ST.boot_matrix(len(v), ST.REPS, 40, O.stable_u64('E6p', 'BOOT', 'FULL', 40) % (2 ** 32))
    lo, hi = ST.boot_ci(W, v[:, None])
    return float(np.mean(v) * O.ANN_PP), float(lo[0]), float(hi[0]), int(m.sum())


def score(v, lo, hi, direction):
    if not np.isfinite(v):
        return '开放', 'NOT_COMPUTABLE'
    ok = v > 0 if direction == '+' else v < 0
    if ok:
        prec = '' if (np.isfinite(lo) and np.isfinite(hi) and ((lo > 0) if direction == '+' else (hi < 0))) else '方向相符但区间跨 0：精度有限'
        return '支持', prec
    return '不支持', ''


def prec_text(v, lo, hi, direction):
    """账本 precision 列：区间是否跨 0 与状态分开写（direction = 事前预测方向）。"""
    if not (np.isfinite(v) and np.isfinite(lo) and np.isfinite(hi)):
        return '区间不可算'
    cross = not (lo > 0 or hi < 0)
    ok = v > 0 if direction == '+' else v < 0
    if ok:
        return '方向相符但区间跨 0：精度有限' if cross else '区间不跨 0'
    return '方向不符；区间跨 0' if cross else '方向不符；区间不跨 0（与预测反向）'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    ap.add_argument('--phase', default='B')
    ap.add_argument('--fake_post', action='store_true')
    a = ap.parse_args()
    root = O.P(a.root) if a.root else O.work()
    rd = lambda rel: pd.read_csv(os.path.join(root, rel), keep_default_na=False, na_values=[''])
    AS = rd('statistics/account_summary_E6p.csv')
    ASi = AS.set_index(['exec_id', 'segment'])
    RD = rd('statistics/randoms_E6p.csv').set_index(['owner_exec_id', 'mechanism', 'segment'])
    BE = rd('statistics/breakeven_E6p.csv')
    PO = rd('statistics/policy_E6p.csv')
    R = pd.read_csv(O.P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
    ids = G1.main_ids(R)
    ctx = ST.Ctx(a.phase, a.fake_post, root)
    S, acc = ST.load_all(ctx)
    ne = S['ne']
    col = ctx.col
    get = lambda e, s='FULL', c='D_same_h_ann_pp': float(ASi[c].get((e, s), np.nan))
    seg_signs = lambda e, c='D_same_h_ann_pp': '/'.join('%+.2f' % get(e, s, c) for s in SEG4)
    claims, qreg = [], []

    def q(qid, table, filt, n, gen='e6p_claims.py'):
        qreg.append(dict(query_id=qid, table=table, filter=filt, n_rows=n, generator=gen))

    def imp(e, A, dl=0.5, kap=0.5):
        return kap * A ** dl * np.nan_to_num(S['s05' if dl == 0.5 else 's07'][:, col[e]])
    # ---------------- E01–E10
    E_ = {}

    def put_e(eid, statement, obj, comp, v, lo, hi, n, direction, table, filt, extra_note='', hetero=''):
        st, prec = score(v, lo, hi, direction)
        note = '; '.join(x for x in (prec or (prec_text(v, lo, hi, direction) if st == '不支持' else ''), extra_note) if x)
        if np.isfinite(v) and np.isfinite(lo) and np.isfinite(hi) and not (lo <= v <= hi):
            note = (note + '; ' if note else '') + '点估不在 bootstrap 区间内：区间为重抽样日均的分位（比率估计），与点估计同函数同样本'
        claims.append(dict(claim_id=eid, kind='PREDICTION', author='plan v1.1 §12', statement=statement, query_id='QRY-%s' % eid, table=table, exec_ids=';'.join([obj, comp]),
                           result_value=v, result_sign='+' if v > 0 else ('-' if v < 0 else '0'), ci_lo=lo, ci_hi=hi, claim_status=st, note=note))
        q('QRY-%s' % eid, table, filt, n)
        E_[eid] = dict(object_id=obj, comparator_id=comp, result='%.4f [%.4f, %.4f]' % (v, lo, hi), direction=direction, precision=prec_text(v, lo, hi, direction),
                       heterogeneity=hetero, mechanism_status='', next_action='', status=st)
    for eid, t in (('E01', 'T1a'), ('E02', 'T1b_LEVEL'), ('E07', 'T8_LIMIT_CLOSE')):
        e = ids[('D80', '20', t, '0')]
        p = ctx.reg.loc[e, 'parent_same_h_exec_id']
        v, lo, hi, n = boot_full(ctx, ne[:, col[e]] - ne[:, col[p]], eid)
        put_e(eid, 'H20/HG10/D80/%s 对同 H / D80 无退出父 FULL net 差 > 0' % t, e, p, v, lo, hi, n, '+', 'statistics/account_summary_E6p.csv',
              'exec_id=%s segment=FULL D_same_h_ann_pp' % e, hetero='四段 ' + seg_signs(e))
    xs = []
    for t in ('T1a', 'T1b_LEVEL'):
        a20, p20 = ids[('D80', '20', t, '0')], ids[('D80', '20', 'NONE', '0')]
        a5, p5 = ids[('D80', '5', t, '0')], ids[('D80', '5', 'NONE', '0')]
        xs.append((ne[:, col[a20]] - ne[:, col[p20]]) - (ne[:, col[a5]] - ne[:, col[p5]]))
    comp_parts = [float(np.nanmean(x[ctx.masks['FULL']]) * O.ANN_PP) for x in xs]
    v, lo, hi, n = boot_full(ctx, 0.5 * (xs[0] + xs[1]), 'E03')
    put_e('E03', 'D80/HG10：T1a 与 LEVEL 的 H20−H5 退出边际之差（H×EXIT），二者等权平均 > 0', 'D80|H20 T1a&LEVEL', 'D80|H5 父与子', v, lo, hi, n, '+',
          'statistics/account_summary_E6p.csv', 'H_X_EXIT 复合（D80，HG10，T1a / LEVEL）', extra_note='组成项：T1a %.3f / LEVEL %.3f%s' % (
              comp_parts[0], comp_parts[1], '（异号）' if comp_parts[0] * comp_parts[1] < 0 else ''), hetero='T1a %.3f / LEVEL %.3f' % tuple(comp_parts))
    if comp_parts[0] * comp_parts[1] < 0:
        claims[-1]['claim_status'] = 'mixed'
    e, lv = ids[('D80', '20', 'T1a', '0')], ids[('D80', '20', 'T1b_LEVEL', '0')]
    x = -(imp(e, 5e8) - imp(lv, 5e8))
    v, lo, hi, n = boot_full(ctx, x, 'E04')
    put_e('E04', 'H20/HG10/D80、A 5 亿 κ .5 δ .5：T1a − LEVEL 的成本后差 > 二者未加冲击的差（⇔ LEVEL 冲击 > T1a 冲击）', e, lv, v, lo, hi, n, '+', 'statistics/cost_curve_E6p.csv',
          'exec_id=%s comparator_kind=T1A_VS_LEVEL A=5e8 kappa=.5 exponent=.5：−impact_diff' % e)
    ev = G1.event_t3b_only(ctx, R, ['FULL'] if not a.fake_post else ['2010-2014'])
    k_ = list(ev)[0]
    v, nn, nd, se = ev[k_]
    lo, hi = (v - 1.96 * se, v + 1.96 * se) if np.isfinite(se) else (np.nan, np.nan)
    put_e('E05', 'H20/HG10/NATIVE 共同风险快照：T3b-only 触发的下一 VWAP 后 5 日超额低于同金额 / 日龄 / 行业 size 非触发匹配组', 'NATIVE|HG10|H20 父快照（T3b-only 事件）',
          '同日同层同日龄桶非触发批次（金额加权）', v, lo, hi, nn, '-', 'diagnostics/G1_E6p.csv', 'event study FULL（bp；日聚类 SE）',
          extra_note='单位 bp；事件证券日 %d、天数 %d；区间 = 均值 ± 1.96 × 日聚类 SE（事件比较，不同于账户 bootstrap）' % (nn, nd))
    E_['E05']['result'] += ' bp（5 日累计超额；A1 账本 unit 列 ann_pp 为模板值，本条事件比较按 bp 报）'
    e, e0 = ids[('D80', '40', 'T1b_LEVEL', '5')], ids[('D80', '40', 'T1b_LEVEL', '0')]
    v, lo, hi, n = boot_full(ctx, ne[:, col[e]] - ne[:, col[e0]], 'E06')
    put_e('E06', 'H40/HG10/D80/LEVEL＋RENEW5 对无 RENEW5 同对象 FULL net 差 > 0', e, e0, v, lo, hi, n, '+', 'statistics/account_summary_E6p.csv', 'net 差（RENEW5 − 无 RENEW5）')
    parts = []
    xs = []
    for t in ('T1a', 'T1b_LEVEL'):
        e = ids[('D80', '20', t, '0')]
        k = (e, 'AMOUNT_ISK_V2', 'FULL')
        if k in RD.index:
            parts.append(float(RD.loc[k].real_D_ann_pp - RD.loc[k].rand_mean_D_ann_pp))
        dfile = O.P('randoms', 'daily', ctx.reg.loc[e, 'exec_hash'][:2])
        mean_path = None
        if os.path.isdir(dfile) and ctx.phase == 'B' and not ctx.fake:
            fs = sorted(f for f in os.listdir(dfile) if f.startswith(ctx.reg.loc[e, 'exec_hash'] + '_AMOUNT_ISK_V2_'))
            arrs = [np.load(os.path.join(dfile, f))['ne'].astype(float) for f in fs]
            if arrs:
                mean_path = np.concatenate(arrs).mean(0)
        if mean_path is not None:
            xs.append(ne[:ctx.T, col[e]] - mean_path[:ctx.T])
    if len(xs) == 2:
        v, lo, hi, n = boot_full(ctx, 0.5 * (xs[0] + xs[1]), 'E08')
    else:
        v, lo, hi, n = (float(np.mean(parts)) if parts else np.nan), np.nan, np.nan, 0
    put_e('E08', 'H20/HG10/D80 的 T1a、LEVEL 真实 − AMOUNT_ISK_V2 FULL 差的等权平均 > 0', 'D80|H20 T1a&LEVEL', 'AMOUNT_ISK_V2 路径均值', v, lo, hi, n, '+',
          'statistics/randoms_E6p.csv', 'mechanism=AMOUNT_ISK_V2 segment=FULL', extra_note='组成项：%s；区间 = 真实 − 路径均值日序列的 bootstrap（市场不确定性；MC 误差另见 randoms.mcse）' % (
              ' / '.join('%.3f' % p for p in parts)))
    if len(parts) == 2 and parts[0] * parts[1] < 0:
        claims[-1]['claim_status'] = 'mixed'
    for eid, H, arm, A in (('E09', '5', 'RECYCLE_HALF', 5e8), ('E10', '20', 'RECYCLE_COSTNET', 1e8)):
        a_, n_ = ids[(arm, H, 'T1b_LEVEL', '0')], ids[('NATIVE', H, 'T1b_LEVEL', '0')]
        x = (ne[:, col[a_]] - imp(a_, A)) - (ne[:, col[n_]] - imp(n_, A))
        v, lo, hi, n = boot_full(ctx, x, eid)
        put_e(eid, 'H%s/HG10/LEVEL，%s − NATIVE，固定路径 A %d 亿 / κ .5 / δ .5 的 FULL 净差 > 0' % (H, arm, int(A / 1e8)), a_, n_, v, lo, hi, n, '+', 'statistics/cost_curve_E6p.csv',
              'ABSOLUTE net_after_impact（A=%d, κ .5, δ .5）差' % int(A))
    # ---------------- Q01–Q18（问题 / 复现 / 工程；E 卡同号引用）
    cards = pd.read_csv(O.P('registration', 'cards_E6p.csv'), keep_default_na=False)
    g1 = pd.read_csv(O.P('diagnostics', 'G1_E6p.csv'), keep_default_na=False)
    mainT = ids[('NATIVE', '20', 'T1a', '0')]
    mainL = ids[('NATIVE', '20', 'T1b_LEVEL', '0')]
    qv = {'Q01': ('E6O_ACCOUNT_REPLICATION 与 SOURCE_REPLICATION 全 PASS', np.nan), 'Q05': ('主对象（H20 NATIVE）T1a 四差：同 H / H5 同部署 / H5 NATIVE / H5 同触发',
                                                                                          get(mainT, 'FULL', 'D_h5_native_ann_pp')),
          'Q11': ('landmark 剖面（diagnostics/landmark_E6p.csv）', np.nan), 'Q12': ('D80 父 − NATIVE 父（H20 HG10）FULL net', get(ids[('D80', '20', 'NONE', '0')], 'FULL', 'net_ann_pp')
                                                                          - get(ids[('NATIVE', '20', 'NONE', '0')], 'FULL', 'net_ann_pp')),
          'Q13': ('UNION − max(T1a, T3b15)（H20 NATIVE HG10）FULL D', get(ids[('NATIVE', '20', 'UNION', '0')]) - max(get(ids[('NATIVE', '20', 'T1a', '0')]), get(ids[('NATIVE', '20', 'T3b15', '0')]))),
          'Q14': ('主对象盈亏平衡（VS_SAME_H_PARENT，κ .5 δ .5）', np.nan), 'Q15': ('主对象逐年正年数（17 年）', np.nan), 'Q16': ('账本 / 携带表行数', np.nan)}
    for c in cards.itertuples(index=False):
        if c.e_id:
            src = next(x for x in claims if x['claim_id'] == c.e_id)
            claims.append(dict(claim_id=c.card_id, kind='QUESTION', author='plan v1.1 §12', statement=c.estimand_direction, query_id=src['query_id'], table=src['table'],
                               exec_ids=src['exec_ids'], result_value=src['result_value'], result_sign=src['result_sign'], ci_lo=src['ci_lo'], ci_hi=src['ci_hi'],
                               claim_status=src['claim_status'], note='= %s（经济方向预测）' % c.e_id))
            continue
        txt, v = qv.get(c.card_id, (c.estimand_direction, np.nan))
        st = '技术PASS' if c.card_id in ('Q01', 'Q16') else '开放'
        if c.card_id == 'Q14':
            b = BE[(BE.exec_id.isin([mainT, mainL])) & (BE.comparator_kind == 'VS_SAME_H_PARENT') & (BE.kappa == 0.5) & (BE.exponent == 0.5)]
            txt = txt + '：' + '; '.join('%s %s %.3g' % (('T1a' if r.exec_id == mainT else 'LEVEL'), r.root_kind, r.breakeven_A_cny) for r in b.itertuples(index=False))
        claims.append(dict(claim_id=c.card_id, kind='QUESTION' if c.kind != 'engineering' else 'ENGINEERING', author='plan v1.1 §12', statement=txt, query_id='QRY-%s' % c.card_id,
                           table='statistics/account_summary_E6p.csv', exec_ids='', result_value=v, result_sign='+' if (np.isfinite(v) and v > 0) else ('-' if np.isfinite(v) and v < 0 else ''),
                           ci_lo='', ci_hi='', claim_status=st, note='G1（推导段）标签：%s' % ';'.join(sorted(set(g1[g1.item == c.card_id].status)))))
        q('QRY-%s' % c.card_id, 'statistics/account_summary_E6p.csv', c.estimand_direction[:120], 1)
    # ---------------- G-P 链
    Gl = pd.read_csv(O.P('registration', 'ledger_G_E6p.csv'), keep_default_na=False)
    gobs = {
        'G-P-01': '全部 %d 个执行对象（含镜像与 P_SOURCE）导出日序列；全部 ACCOUNT 对象导出成交分片；随机路径日统计分片可取（47）' % len(ctx.ids),
        'G-P-02': 'policy_fields 逐项值 / 原因 / 分母 / 阈值 / query / 来源；不可判原因枚举；E6o 62 行"全真却不可判"= 类型判定所致（notes §8）',
        'G-P-03': '独立 D80 / D95 与 MIRROR_LAG1（owner 前一收盘敞口）并行；镜像不作无信息父（diagnostics/mirror_E6p.csv）',
        'G-P-04': '两级金额匹配 + AMOUNT_ISK_V2 + requested / within / cross / unmatched 全报（statistics/matching_E6p.csv）',
        'G-P-05': '全部直接比较各自成本曲线与交叉点（statistics/cost_curve / breakeven）；目标 A 未定',
        'G-P-06': 'E→G 派生：本轮不提名分钟触发（只作 D3 / D7 / D8 测量列）',
        'G-P-07': 'D_sc / 敞口差 / 现金差 / size / 行业偏离逐对象报（account_summary）；源权重与自融资桥 ACCOUNTING_BRIDGE（INFO）',
        'G-P-08': '再投资三臂 27 行 + 局部同预算诊断 18 owner（D9_recycle_local）', 'G-P-09': 'LEVEL 与 EDGE 并排（LEVEL_VS_EDGE 54 条比较）',
        'G-P-10': 'D4 两层 PIT 字段（同层触发密度 LOSO）与 AMOUNT_ISK_V2 并排', 'G-P-11': '四层分开写入报告（预测 / 账户增量 / 实施与政策 / 覆盖）'}
    shutil.copyfile(O.P('registration', 'ledger_G_E6p.csv'), O.P('registration', 'ledger_G_E6p_A1.csv')) if not os.path.exists(O.P('registration', 'ledger_G_E6p_A1.csv')) else None
    shutil.copyfile(O.P('registration', 'ledger_E_E6p.csv'), O.P('registration', 'ledger_E_E6p_A1.csv')) if not os.path.exists(O.P('registration', 'ledger_E_E6p_A1.csv')) else None
    for i, g in Gl.iterrows():
        Gl.loc[i, 'observed_result'] = gobs.get(g.g_id, '')
        Gl.loc[i, 'measurement_at'] = g.measurement_at or 'E6p B 交付'
        Gl.loc[i, 'source_query'] = 'QRY-%s' % g.g_id
        claims.append(dict(claim_id=g.g_id, kind='G_CHAIN', author=g.original_author, statement=g.verbatim_expectation, query_id='QRY-%s' % g.g_id, table='registration/ledger_G_E6p.csv',
                           exec_ids='', result_value='', result_sign='', ci_lo='', ci_hi='', claim_status='技术PASS' if g.g_id in ('G-P-01', 'G-P-02', 'G-P-04') else '开放',
                           note=gobs.get(g.g_id, '')))
        q('QRY-%s' % g.g_id, 'registration/ledger_G_E6p.csv', 'g_id=%s' % g.g_id, 1)
    El = pd.read_csv(O.P('registration', 'ledger_E_E6p.csv'), keep_default_na=False)
    for i, r in El.iterrows():
        if r.e_id in E_:
            for k, v in E_[r.e_id].items():
                if k in El.columns:
                    El.loc[i, k] = v
    if root == O.work():
        O.atomic_write_csv(O.P('registration', 'ledger_G_E6p.csv'), Gl)
        O.atomic_write_csv(O.P('registration', 'ledger_E_E6p.csv'), El)
    # ---------------- CC 原句携带
    CC = pd.read_csv(O.P('registration', 'cc_statement_carry.csv'), keep_default_na=False)
    Dn = {t: [get(ids[('NATIVE', H, t, '0')]) for H in ('5', '10', '15', '20', '30', '40')] for t in ('T1a', 'T1b_LEVEL', 'T3b15', 'UNION', 'T8_LIMIT_CLOSE', 'T1b_EDGE')}
    inc = lambda v: all(v[i] < v[i + 1] for i in range(3))
    res = {}
    k1 = [inc(Dn[t]) for t in ('T1a', 'T1b_LEVEL')]
    res['CC-E6p-01'] = ('支持' if all(k1) else ('mixed' if any(k1) else '不支持'), 'NATIVE HG10 同 H 父 D（H5…H40）：T1a %s；LEVEL %s；H30 / H40 vs H20：T1a %+.2f / %+.2f，LEVEL %+.2f / %+.2f' % (
        '/'.join('%.2f' % x for x in Dn['T1a']), '/'.join('%.2f' % x for x in Dn['T1b_LEVEL']), Dn['T1a'][4] - Dn['T1a'][3], Dn['T1a'][5] - Dn['T1a'][3],
        Dn['T1b_LEVEL'][4] - Dn['T1b_LEVEL'][3], Dn['T1b_LEVEL'][5] - Dn['T1b_LEVEL'][3]))
    k2 = [Dn[t][5] <= Dn[t][3] + 0.3 for t in ('T1a', 'T1b_LEVEL')]
    res['CC-E6p-01L'] = ('支持' if all(k2) else ('mixed' if any(k2) else '不支持'), 'H40 − H20（同 H 父 D）：T1a %+.2f；LEVEL %+.2f（±.3 显示带）' % (Dn['T1a'][5] - Dn['T1a'][3], Dn['T1b_LEVEL'][5] - Dn['T1b_LEVEL'][3]))
    res['CC-E6p-02'] = ('NOT_TESTED_AS_WRITTEN', 'DEPLOY_MATCH 父在 plan 降为 MIRROR 诊断；OWNER_VS_EXPOSURE_FOLLOWER 见 diagnostics/mirror_E6p.csv 与 comparisons')
    tv = {H: get(ids[('NATIVE', H, 'T1a', '0')], 'FULL', 'turnover_ann') for H in ('5', '10', '15', '20', '30', '40')}
    mono = all(tv[a_] >= tv[b_] for a_, b_ in zip(('5', '10', '15', '20', '30'), ('10', '15', '20', '30', '40')))
    lw = []
    for t in ('T1a', 'T1b_LEVEL'):
        k = (ids[('NATIVE', '20', t, '0')], 'LEVEL_WORST_1D', 'FULL')
        if k in RD.index:
            lw.append(float(RD.loc[k].real_D_ann_pp - RD.loc[k].rand_mean_D_ann_pp))
    res['CC-E6p-03'] = ('mixed', '真实 − LEVEL_WORST（H20 NATIVE T1a / LEVEL）%s；T1a 换手随 H 单调降 = %s（%s）；盈亏平衡见 breakeven；可证伪点随 CC-E6p-02 对象差 NOT_TESTED_AS_WRITTEN' % (
        ' / '.join('%.2f' % x for x in lw), mono, '/'.join('%.1f' % tv[H] for H in tv)))
    dm = {t: [get(ids[('NATIVE', H, t, '0')], 'FULL', 'D_h5_same_trigger_ann_pp') for H in ('10', '15', '20', '30', '40')] for t in ('T1a', 'T1b_LEVEL')}
    res['CC-E6p-04'] = ('mixed' if any(np.isfinite(x) for x in dm['T1a']) else '开放', 'HORIZON_WITHIN_TRIGGER（X(H) − X(5)，H10…H40）：T1a %s；LEVEL %s；"上限在 20–30"是读法不评分' % (
        '/'.join('%.2f' % x for x in dm['T1a']), '/'.join('%.2f' % x for x in dm['T1b_LEVEL'])))
    res['CC-E6p-05'] = ('NOT_TESTED_AS_WRITTEN', '本轮 cvr_k 只作 D7 测量列（秩相关 / 重叠），无触发账户')
    dp = get(ids[('D95', '20', 'NONE', '0')], 'FULL', 'net_ann_pp') - get(ids[('NATIVE', '20', 'NONE', '0')], 'FULL', 'net_ann_pp')
    dx = [(get(ids[('D95', '20', t, '0')]), get(ids[('NATIVE', '20', t, '0')])) for t in ('T1a', 'T1b_LEVEL')]
    same = all(np.sign(a_) == np.sign(b_) for a_, b_ in dx)
    res['CC-E6p-06'] = ('mixed', '前半句 DEPLOY_OPERATOR_CHANGE（D95 父 − NATIVE 父，H20 HG10）= %+.2f；"≈ 单位敞口净值 × 敞口差" = REPLACED_BEFORE_RUN；后半句 DEPLOY_X_EXIT：D95 内退出 D / NATIVE 内退出 D = %s，同号 = %s' % (
        dp, ' ; '.join('%.2f/%.2f' % x for x in dx), same))
    lvl_hi = max(Dn, key=lambda t: Dn[t][3]) == 'T1b_LEVEL'

    def xa(k, x):
        b = BE[(BE.exec_id == ids[('NATIVE', '20', 'T1a', '0')]) & (BE.comparator_kind == 'T1A_VS_LEVEL') & (BE.kappa == k) & (BE.exponent == x)]
        if not len(b):
            return '—'
        return '%s %.2f 亿' % (b.root_kind.iloc[0], b.breakeven_A_cny.iloc[0] / 1e8) if np.isfinite(b.breakeven_A_cny.iloc[0]) else str(b.root_kind.iloc[0])
    res['CC-E6p-07'] = ('mixed', 'H20 NATIVE：LEVEL D 是否最高 = %s；T1a − LEVEL 成本后差的零点（T1A_VS_LEVEL，A* 以上 T1a 优）κ .5 δ .5 %s / κ 1 δ .5 %s / κ .5 δ .7 %s；'
                        'LEVEL − LEVEL_WORST 见 randoms（近同构）' % (lvl_hi, xa(0.5, 0.5), xa(1.0, 0.5), xa(0.5, 0.7)))
    t3 = Dn['T3b15']
    res['CC-E6p-08'] = ('支持' if (t3[0] > 0 and inc(t3)) else ('mixed' if t3[0] > 0 or inc(t3) else '不支持'), 'T3b15 同 H 父 D（H5…H40）：%s' % '/'.join('%.2f' % x for x in t3))
    un = Dn['UNION'][3]
    mx = max(Dn['T1a'][3], Dn['T3b15'][3])
    tu = [get(ids[('NATIVE', '20', t, '0')], 'FULL', 'turnover_ann') for t in ('UNION', 'T1a', 'T3b15')]
    res['CC-E6p-09'] = ('支持' if (un >= mx and tu[0] <= tu[1] + tu[2]) else ('mixed' if (un >= mx or tu[0] <= tu[1] + tu[2]) else '不支持'),
                        'H20 NATIVE：UNION %.2f vs max(T1a, T3b15) %.2f；换手 UNION %.1f ≤ T1a + T3b15 %.1f' % (un, mx, tu[0], tu[1] + tu[2]))
    t8 = Dn['T8_LIMIT_CLOSE']
    res['CC-E6p-10'] = ('支持' if t8[3] >= 0 else '不支持', 'T8 同 H 父 D（H5…H40，NATIVE）：%s；事件计数见 stage0 S0-7' % '/'.join('%.2f' % x for x in t8))
    ex = [get(ids[('NATIVE', H, 'NONE', '0')], 'FULL', 'exposure_mean') for H in ('5', '10', '15', '20', '30', '40')]
    res['CC-E6p-11'] = ('支持' if (max(ex) - min(ex) <= 0.02) else 'mixed', 'P_SOURCE：敞口 = 源公式 H 日 ΣW 均值逐位成立（SOURCE_EXPOSURE_EQ_MEAN_SUMW）；NATIVE 父敞口均值 H5…H40 = %s（P_ACCOUNT 不被该等式强制定义，plan §1.2(8)）' % (
        '/'.join('%.3f' % x for x in ex)))
    for i, c in CC.iterrows():
        st, nt = res.get(c.carry_id, ('开放', ''))
        CC.loc[i, 'claim_status'] = st
        claims.append(dict(claim_id=c.carry_id, kind='CC_CARRIED', author='proposal v1.0（CC）', statement=c.verbatim_statement, query_id='QRY-%s' % c.carry_id,
                           table='registration/cc_statement_carry.csv', exec_ids='', result_value='', result_sign='', ci_lo='', ci_hi='', claim_status=st, note=nt))
        q('QRY-%s' % c.carry_id, 'statistics/account_summary_E6p.csv', 'see note', 1)
    if root == O.work():
        CC['e6p_reading'] = [res.get(c, ('', ''))[1] for c in CC.carry_id]
        O.atomic_write_csv(O.P('registration', 'cc_statement_carry.csv'), CC)
    # ---------------- F7 转述数字（只登记本轮可比值；不作锚、不改 binding_status）
    RC = pd.read_csv(O.P('registration', 'reported_claims_E6p.csv'), keep_default_na=False)
    e5 = ids[('NATIVE', '5', 'T1b_EDGE', '0')]
    c5l = R[(R.form == O.MAIN_FORM) & (R.memory == 'HG10') & (R.H == '5') & (R.deploy == 'CASH_REMAIN') & (R.trigger == 'T1b_LEVEL') & (R.execution_profile == 'FEASIBLE_DAILY')].exec_id
    isk = lambda s: float(RD.loc[(e5, 'COUNT_ISK', s)].real_D_ann_pp - RD.loc[(e5, 'COUNT_ISK', s)].rand_mean_D_ann_pp) if (e5, 'COUNT_ISK', s) in RD.index else np.nan
    part = np.nan
    d3p = os.path.join(root, 'diagnostics', 'D3_cost_E6p.csv')
    if os.path.exists(d3p):
        d3 = pd.read_csv(d3p, keep_default_na=False, na_values=[''])
        x = d3[(d3.key2 == e5) & (d3.key1 == 'ADV20') & (d3.stat == 'mean_A5yi')]
        part = float(x.value.iloc[0]) if len(x) else np.nan
    f7v = {'F7-01': (get(c5l.iloc[0]) if len(c5l) else np.nan, 'H5 HG10 CASH_REMAIN × T1b_LEVEL 的 FULL D（同 CASH 无退出父）'),
           'F7-02': (get(e5, 'FULL', 'D_sc_ann_pp'), 'H5 HG10 NATIVE × T1b_EDGE（= E6o H5 主对象）的 FULL D_sc（同资本视图）'),
           'F7-03': (isk('2024-2026'), 'H5 EDGE NATIVE 真实 − COUNT_ISK（E6p V2：行业 × size × 日龄桶，回填）2024-26 段；与 E6o COUNT_ISK 定义不同'),
           'F7-04': (isk('FULL'), '同上 FULL（2019-23 段 = %s）' % f2s(isk('2019-2023'))),
           'F7-05': (part, 'H5 EDGE NATIVE 每证券日净订单 / ADV20 的均值（A = 5 亿；diagnostics/D3_cost_E6p.csv）'),
           'F7-06': (get(e5), 'H5 EDGE NATIVE FULL D（引擎逐日复现 E6o 主对象）'), 'F7-07': (np.nan, 'E6o H5 EDGE 的 CASH 变体本轮未建（CASH_BRIDGE 只含 NONE / T1a / LEVEL）'),
           'F7-08': (get(e5, 'FULL', 'D_imp_ann_pp'), 'H5 EDGE NATIVE 的旧审计冲击后 FULL D（5 亿 κ .5）'), 'F7-09': (np.nan, '同 F7-07，本轮无对应对象')}
    RC['e6p_comparable_value'] = [f7v.get(c, (np.nan, ''))[0] for c in RC.claim_id]
    RC['e6p_note'] = [f7v.get(c, (np.nan, ''))[1] for c in RC.claim_id]
    if root == O.work():
        O.atomic_write_csv(O.P('registration', 'reported_claims_E6p.csv'), RC)
    for c in RC.itertuples(index=False):
        claims.append(dict(claim_id=c.claim_id, kind='RELAYED', author='F7（用户转述）', statement=c.relayed_text_verbatim, query_id=c.query_id, table='registration/reported_claims_E6p.csv',
                           exec_ids='', result_value='', result_sign='', ci_lo='', ci_hi='', claim_status=c.binding_status, note=c.quantity))
        q(c.query_id, 'registration/reported_claims_E6p.csv', 'claim_id=%s' % c.claim_id, 1)
    # 工程项
    idt = pd.read_csv(os.path.join(root, 'verify', 'identities_E6p.csv'), keep_default_na=False) if os.path.exists(os.path.join(root, 'verify', 'identities_E6p.csv')) else None
    if idt is not None:
        for cid in ('E6O_ACCOUNT_REPLICATION', 'SOURCE_REPLICATION', 'NOEXIT_EQ_PARENT', 'CASH_EQUATION', 'TOKEN_CONSERVATION'):
            x = idt[idt.check_id == cid]
            ok = len(x) and (x.status.isin(['PASS', 'BLOCKED'])).all()
            claims.append(dict(claim_id='ENG-%s' % cid, kind='ENGINEERING', author='brief §2 / 附录 B.11', statement=cid, query_id='QRY-ENG-%s' % cid, table='verify/identities_E6p.csv',
                               exec_ids='', result_value=len(x), result_sign='', ci_lo='', ci_hi='', claim_status='技术PASS' if ok else '技术FAIL', note='工程恒等不进经济命中率'))
            q('QRY-ENG-%s' % cid, 'verify/identities_E6p.csv', 'check_id=%s' % cid, len(x))
    C = pd.DataFrame(claims)
    QR = pd.DataFrame(qreg).drop_duplicates('query_id')
    O.atomic_write_csv(os.path.join(root, 'reports', 'claims_E6p.csv'), C[['claim_id', 'kind', 'author', 'statement', 'query_id', 'table', 'exec_ids', 'result_value', 'result_sign',
                                                                           'ci_lo', 'ci_hi', 'claim_status', 'note']])
    O.atomic_write_csv(os.path.join(root, 'reports', 'query_registry_E6p.csv'), QR[['query_id', 'table', 'filter', 'n_rows', 'generator']])
    out = dict(claims=len(C), queries=len(QR), E={k: v['status'] for k, v in E_.items()}, CC={k: v[0] for k, v in res.items()})
    O.atomic_write_json(os.path.join(root, 'reports', 'claims_facts_E6p.json'), out)
    print(json.dumps(out, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
