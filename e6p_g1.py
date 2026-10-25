# -*- coding: utf-8 -*-
"""E6p S0-15 / G1 第一道 probe（brief §2；附录 A15；plan §11.1 S0c）：卡 Q01–Q18 的推导段（2010-2014、2015-2018）读数，每卡一组行，status 只打标签
（PRESPECIFIED_DISCRIMINATING_TEST / NOT_YET_SUPPORTED / SUPPORTED_DERIVATION / NOT_COMPUTABLE）；不选支、不改名单、不改参数。随后封存 seal_A2.json（任何后段写入之前）。
读数来源：tmp/a2stats（e6p_stats / e6p_diag 的推导段版本）+ stage0 恒等 + A2 账户 / 成交分片。也提供 E05 事件比较（claims 复用）。
用法：python3 e6p_g1.py probe | seal"""
import os
import sys
import json
import time
import hashlib
from multiprocessing import get_context

import numpy as np
import pandas as pd

import e6p_core as O
import e6p_engine as E
import e6p_stats as ST

ROOT_A2 = 'tmp/a2stats'
DER = list(O.DERIV_SEGS)
GCOLS = ['block', 'item', 'key1', 'key2', 'segment', 'stat', 'value', 'unit', 'n', 'status', 'query_id']


def rid(R, **kw):
    m = R
    for k, v in kw.items():
        m = m[m[k] == v]
    if len(m) != 1:
        raise RuntimeError('对象不唯一：%s → %d' % (kw, len(m)))
    return m.iloc[0].exec_id


def main_ids(R, prof='FEASIBLE_DAILY'):
    base = dict(form=O.MAIN_FORM, memory='HG10', role='ACCOUNT', execution_profile=prof)
    out = {}
    for d, cap in (('NATIVE', 'SOURCE'), ('D80', 'RELATIVE_UPPER'), ('D95', 'RELATIVE_UPPER')):
        for H in ('5', '10', '15', '20', '30', '40'):
            for t in ('NONE', 'T1a', 'T1b_LEVEL', 'T1b_EDGE', 'T3b15', 'UNION', 'T8_LIMIT_CLOSE'):
                out[(d, H, t, '0')] = rid(R, deploy=d, cap=cap, H=H, trigger=t, renew='0', **base)
    for d, cap in (('NATIVE', 'SOURCE'), ('D80', 'RELATIVE_UPPER')):
        for H in ('20', '40'):
            for t in ('NONE', 'T1a', 'T1b_LEVEL'):
                out[(d, H, t, '5')] = rid(R, deploy=d, cap=cap, H=H, trigger=t, renew='5', **base)
    for d in ('CASH_REMAIN', 'RECYCLE_HALF', 'RECYCLE_COST0', 'RECYCLE_COSTNET'):
        for H in ('5', '20', '40'):
            for t in ('NONE', 'T1a', 'T1b_LEVEL'):
                out[(d, H, t, '0')] = rid(R, deploy=d, cap='SOURCE', H=H, trigger=t, renew='0', **base)
    return out


def event_t3b_only(ctx, R, segs, prof='FEASIBLE_DAILY'):
    """E05：H20 / HG10 / NATIVE 无退出父的共同风险快照（成交日志重建活批次）；事件 = T3b15 真且 T1a 非真（T3b-only）；下一 VWAP 起 5 日超额（扣同日 clean 等权基准）
    减同日同（行业 × size）层 × 同日龄桶、非触发批次的金额加权均值；按证券日汇总（一股多批算一次）。返回 {段: (均值 bp, 事件证券日数, 天数, 日聚类 SE bp)}。"""
    pid = main_ids(R, prof)[('NATIVE', '20', 'NONE', '0')]
    h = ctx.reg.loc[pid, 'exec_hash']
    ti, tf = ST.load_trades(ctx, h)
    import e6p_diag as DG
    lt = DG.lots_table(ti, tf, ctx.d_end)
    cd = ctx.cd
    t3 = np.load(os.path.join(cd, 'triggers', 'T3b15.npy'), mmap_mode='r')
    t1 = np.load(os.path.join(cd, 'triggers', 'T1a.npy'), mmap_mode='r')
    isk = np.load(os.path.join(cd, 'panels', 'iskid.npy'), mmap_mode='r')
    pv = np.load(os.path.join(cd, 'panels', 'pv_ff.npy'), mmap_mode='r')
    pc = np.load(os.path.join(cd, 'panels', 'pc_ff.npy'), mmap_mode='r')
    cb = np.cumprod(1.0 + np.nan_to_num(ctx.bench))
    e0 = lt.e0.to_numpy()
    cl = np.where(lt.close_day.to_numpy() >= 0, lt.close_day.to_numpy(), ctx.d_end + 5)
    sec = lt.sec.to_numpy()
    qty = lt.qty.to_numpy()
    out = {}
    for s in segs:
        idx = np.flatnonzero(ctx.masks[s])
        diffs, days = [], []
        for d in idx:
            if d + 6 >= ctx.d_end:
                continue
            alive = (e0 <= d) & (cl > d + 1)
            if not alive.any():
                continue
            ss, ag = sec[alive], d + 1 - e0[alive]
            val = qty[alive] * np.asarray(pc[d, ss])
            with np.errstate(all='ignore'):
                fwd = (np.asarray(pv[d + 6, ss]) / np.asarray(pv[d + 1, ss]) - 1.0) - (cb[d + 6] / cb[d + 1] - 1.0)
            ev = (np.asarray(t3[d, ss]) == 1) & (np.asarray(t1[d, ss]) != 1)
            non = (np.asarray(t3[d, ss]) == 0) & (np.asarray(t1[d, ss]) != 1)
            if not ev.any():
                continue
            bk = np.array([E.bucket_of(int(a)) for a in ag])
            cell = np.asarray(isk[d, ss]).astype(np.int64)
            key = cell * 10 + bk
            df = pd.DataFrame(dict(sec=ss, key=key, val=val, fwd=fwd, ev=ev, non=non))
            df = df[np.isfinite(df.fwd) & (df.key >= 0)]
            ctrl = df[df.non].groupby('key').apply(lambda g: np.average(g.fwd, weights=np.maximum(g.val, 0) + 1e-12) if len(g) else np.nan)
            evs = df[df.ev].groupby('sec').agg(fwd=('fwd', 'mean'), key=('key', 'first'))
            evs['ctrl'] = evs.key.map(ctrl)
            evs = evs[np.isfinite(evs.ctrl)]
            if not len(evs):
                continue
            diffs.append((evs.fwd - evs.ctrl).to_numpy())
            days.append(d)
        if diffs:
            dm = np.array([x.mean() for x in diffs])
            allx = np.concatenate(diffs)
            se = float(np.std(dm, ddof=1) / np.sqrt(len(dm))) * 1e4 if len(dm) > 1 else np.nan
            out[s] = (float(allx.mean() * 1e4), len(allx), len(days), se)
        else:
            out[s] = (np.nan, 0, 0, np.nan)
    return out


def label(vals, direction='+'):
    v = [x for x in vals if x is not None and np.isfinite(x)]
    if len(v) < len(vals) or not v:
        return 'NOT_COMPUTABLE'
    pos = [x > 0 for x in v] if direction == '+' else [x < 0 for x in v]
    if all(pos):
        return 'SUPPORTED_DERIVATION'
    if not any(pos):
        return 'NOT_YET_SUPPORTED'
    return 'PRESPECIFIED_DISCRIMINATING_TEST'


def probe():
    t0 = time.time()
    root = O.P(ROOT_A2)
    rd = lambda rel: pd.read_csv(os.path.join(root, rel), keep_default_na=False, na_values=[''])
    AS = rd('statistics/account_summary_E6p.csv').set_index(['exec_id', 'segment'])
    RDm = rd('statistics/randoms_E6p.csv').set_index(['owner_exec_id', 'mechanism', 'segment'])
    CC = rd('statistics/cost_curve_E6p.csv')
    BE = rd('statistics/breakeven_E6p.csv')
    Y = rd('statistics/yearly_E6p.csv')
    LMt = rd('diagnostics/landmark_E6p.csv')
    R = pd.read_csv(O.P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
    ids = main_ids(R)
    ctx = ST.Ctx('A2', False, root)
    rows = []
    get = lambda e, s, c='D_same_h_ann_pp': float(AS[c].get((e, s), np.nan))

    def card(q, entries, direction='+', kind='prediction'):
        vals = []
        for key1, key2, s, v, unit, n in entries:
            vals.append(v)
        lab = label([v for (_, _, s, v, _, _) in entries if s in DER], direction) if kind == 'prediction' else (
            'NOT_COMPUTABLE' if any(not np.isfinite(v) for (_, _, _, v, _, _) in entries) else 'PRESPECIFIED_DISCRIMINATING_TEST')
        for key1, key2, s, v, unit, n in entries:
            rows.append(dict(block='G1', item=q, key1=key1, key2=key2, segment=s, stat='derivation_reading', value=v, unit=unit, n=n, status=lab, query_id='QRY-G1-%s' % q))
        return lab
    labs = {}
    st0 = pd.read_csv(O.P('verify', 'identities_E6p_stage0.csv'), keep_default_na=False)
    rp = st0[st0.check_id.isin(['SOURCE_REPLICATION', 'E6O_ACCOUNT_REPLICATION'])]
    npass = int((rp.status == 'PASS').sum())
    rows.append(dict(block='G1', item='Q01', key1='source_and_e6o_replication_pass', key2='', segment='FULL', stat='count', value=npass, unit='count', n=len(rp),
                     status='SUPPORTED_DERIVATION' if npass == len(rp) else 'NOT_YET_SUPPORTED', query_id='QRY-G1-Q01'))
    labs['Q01'] = rows[-1]['status']
    for q, t in (('Q02', 'T1a'), ('Q03', 'T1b_LEVEL'), ('Q09', 'T8_LIMIT_CLOSE')):
        e = ids[('D80', '20', t, '0')]
        labs[q] = card(q, [('D_same_h', e, s, get(e, s), 'ann_pp', int(AS['n_days'].get((e, s), 0))) for s in DER])
    ent = []
    for s in DER:
        v = []
        for t in ('T1a', 'T1b_LEVEL'):
            v.append(get(ids[('D80', '20', t, '0')], s) - get(ids[('D80', '5', t, '0')], s))
        ent.append(('H_X_EXIT_mean_T1a_LEVEL', 'D80|HG10|H20−H5', s, float(np.mean(v)), 'ann_pp', 2))
    labs['Q04'] = card('Q04', ent)
    ent = []
    for t in ('T1a', 'T1b_LEVEL'):
        e = ids[('NATIVE', '20', t, '0')]
        for c in ('D_same_h_ann_pp', 'D_h5_same_deploy_ann_pp', 'D_h5_native_ann_pp', 'D_h5_same_trigger_ann_pp'):
            for s in DER:
                ent.append((c, e, s, get(e, s, c), 'ann_pp', ''))
    labs['Q05'] = card('Q05', ent, kind='question')
    ent = []
    e = ids[('D80', '20', 'T1a', '0')]
    for s in DER:
        x = CC[(CC.exec_id == e) & (CC.comparator_kind == 'T1A_VS_LEVEL') & (CC.A_cny == 500000000) & (CC.kappa == 0.5) & (CC.exponent == 0.5) & (CC.segment == s)]
        ent.append(('minus_impact_diff_T1a_vs_LEVEL_A5yi', e, s, -float(x.impact_diff_ann_pp.iloc[0]) if len(x) else np.nan, 'ann_pp', ''))
    labs['Q06'] = card('Q06', ent)
    ev = event_t3b_only(ctx, R, DER)
    labs['Q07'] = card('Q07', [('T3b_only_minus_matched_fwd5', 'NATIVE|HG10|H20 parent snapshot', s, ev[s][0], 'bp', ev[s][1]) for s in DER], direction='-')
    ent = []
    for s in DER:
        a_ = get(ids[('D80', '40', 'T1b_LEVEL', '5')], s, 'net_ann_pp')
        b_ = get(ids[('D80', '40', 'T1b_LEVEL', '0')], s, 'net_ann_pp')
        ent.append(('RENEW5_minus_noRENEW_net', ids[('D80', '40', 'T1b_LEVEL', '5')], s, a_ - b_, 'ann_pp', ''))
    labs['Q08'] = card('Q08', ent)
    ent = []
    for s in DER:
        v = []
        for t in ('T1a', 'T1b_LEVEL'):
            k = (ids[('D80', '20', t, '0')], 'AMOUNT_ISK_V2', s)
            v.append(float(RDm.loc[k].real_D_ann_pp - RDm.loc[k].rand_mean_D_ann_pp) if k in RDm.index else np.nan)
        ent.append(('real_minus_AMOUNT_ISK_V2_mean', 'D80|HG10|H20 T1a & LEVEL', s, float(np.mean(v)), 'ann_pp', 2))
    labs['Q10'] = card('Q10', ent)
    e = ids[('NATIVE', '20', 'T1b_LEVEL', '0')]
    ent = []
    for a in (10, 15):
        x = LMt[(LMt.exec_id == e) & (LMt.landmark_age == a) & (LMt.q == 10) & (LMt.weighting == 'EQUAL')].set_index('state')
        nt = float(x.mean_fwd_excess_bp.get('NOT_TRIGGERED', np.nan))
        ent.append(('landmark_age%d_q10_NOT_TRIGGERED_bp' % a, e, 'FULL', nt, 'bp', int(x.n.get('NOT_TRIGGERED', 0)) if 'NOT_TRIGGERED' in x.index else 0))
    labs['Q11'] = card('Q11', ent, kind='question')
    ent = []
    for d in ('D80', 'D95'):
        for s in DER:
            ent.append(('net_diff_vs_NATIVE_parent', ids[(d, '20', 'NONE', '0')], s, get(ids[(d, '20', 'NONE', '0')], s, 'net_ann_pp') - get(ids[('NATIVE', '20', 'NONE', '0')], s, 'net_ann_pp'),
                        'ann_pp', ''))
    labs['Q12'] = card('Q12', ent, kind='question')
    ent = []
    for s in DER:
        u = get(ids[('NATIVE', '20', 'UNION', '0')], s)
        ent.append(('UNION_minus_max_component', ids[('NATIVE', '20', 'UNION', '0')], s, u - max(get(ids[('NATIVE', '20', 'T1a', '0')], s), get(ids[('NATIVE', '20', 'T3b15', '0')], s)),
                    'ann_pp', ''))
        ent.append(('LEVEL_minus_EDGE', ids[('NATIVE', '20', 'T1b_LEVEL', '0')], s, get(ids[('NATIVE', '20', 'T1b_LEVEL', '0')], s) - get(ids[('NATIVE', '20', 'T1b_EDGE', '0')], s),
                    'ann_pp', ''))
    labs['Q13'] = card('Q13', ent, kind='question')
    ent = []
    for t in ('T1a', 'T1b_LEVEL'):
        e = ids[('NATIVE', '20', t, '0')]
        x = BE[(BE.exec_id == e) & (BE.comparator_kind == 'VS_SAME_H_PARENT') & (BE.kappa == 0.5) & (BE.exponent == 0.5)]
        ent.append(('breakeven_A_cny_vs_same_H_parent_k.5_d.5|%s' % (x.root_kind.iloc[0] if len(x) else ''), e, 'FULL', float(x.breakeven_A_cny.iloc[0]) if len(x) else np.nan,
                    'CNY', ''))
    labs['Q14'] = card('Q14', ent, kind='question')
    ent = []
    for t in ('T1a', 'T1b_LEVEL'):
        e = ids[('NATIVE', '20', t, '0')]
        y = Y[(Y.exec_id == e) & (Y.year <= 2018)]
        ent.append(('positive_years_2010_2018', e, 'FULL', float((y.D_same_h_ann_pp > 0).sum()), 'count', len(y)))
    labs['Q15'] = card('Q15', ent, kind='question')
    g = pd.read_csv(O.P('registration', 'ledger_G_E6p.csv'), keep_default_na=False)
    e_ = pd.read_csv(O.P('registration', 'ledger_E_E6p.csv'), keep_default_na=False)
    c_ = pd.read_csv(O.P('registration', 'cc_statement_carry.csv'), keep_default_na=False)
    rows.append(dict(block='G1', item='Q16', key1='ledger_rows_G_E_CC', key2='', segment='FULL', stat='count', value='%d/%d/%d' % (len(g), len(e_), len(c_)), unit='count',
                     n=len(g) + len(e_) + len(c_), status='SUPPORTED_DERIVATION' if (len(g) >= 11 and len(e_) >= 10 and len(c_) >= 11) else 'NOT_YET_SUPPORTED', query_id='QRY-G1-Q16'))
    labs['Q16'] = rows[-1]['status']
    for q, H, arm, A in (('Q17', '5', 'RECYCLE_HALF', 500000000), ('Q18', '20', 'RECYCLE_COSTNET', 100000000)):
        ent = []
        a_id, n_id = ids[(arm, H, 'T1b_LEVEL', '0')], ids[('NATIVE', H, 'T1b_LEVEL', '0')]
        for s in DER:
            xa = CC[(CC.exec_id == a_id) & (CC.comparator_kind == 'ABSOLUTE') & (CC.A_cny == A) & (CC.kappa == 0.5) & (CC.exponent == 0.5) & (CC.segment == s)]
            xn = CC[(CC.exec_id == n_id) & (CC.comparator_kind == 'ABSOLUTE') & (CC.A_cny == A) & (CC.kappa == 0.5) & (CC.exponent == 0.5) & (CC.segment == s)]
            v = float(xa.net_after_impact_diff_ann_pp.iloc[0] - xn.net_after_impact_diff_ann_pp.iloc[0]) if (len(xa) and len(xn)) else np.nan
            ent.append(('%s_minus_NATIVE_after_impact_A%dyi' % (arm, A // 100000000), a_id, s, v, 'ann_pp', ''))
        labs[q] = card(q, ent)
    D = pd.DataFrame(rows, columns=GCOLS)
    O.atomic_write_csv(O.P('diagnostics', 'G1_E6p.csv'), D)
    # stage0 S0-15 行（标签汇总；不选支）
    s15 = pd.DataFrame([dict(probe_id='S0-15', item='G1 第一道 probe（推导段；只打标签）', key='G1_%s' % q, value=lab, unit='count', status='INFO', source_file='diagnostics/G1_E6p.csv',
                             note='不选支、不改名单；方式 B 推导段封存后不停等') for q, lab in sorted(labs.items())])
    O.atomic_write_csv(O.P('diagnostics', 'stage0_E6p_S015.csv'), s15)
    O.write_receipt('E6p_G1', [O.P('diagnostics', 'G1_E6p.csv'), O.P('diagnostics', 'stage0_E6p_S015.csv')], code=[__file__], labels=labs, wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(rows=len(D), labels=labs), ensure_ascii=False), flush=True)


def _sha(p):
    return O.sha_file(p), p


def seal():
    if os.path.exists(O.P('registration', 'seal_A2.json')):
        raise RuntimeError('seal_A2.json 已存在')
    if not os.path.exists(O.P('diagnostics', 'G1_E6p.csv')):
        raise RuntimeError('G1 未完成')
    for d in ('full', 'full_fb', 'shadow_full'):
        p = O.P('accounts_run', d)
        if os.path.isdir(p) and any(os.scandir(p)):
            raise RuntimeError('已有后段写入（%s）：拒绝封存' % d)
    files = []
    for sub in ('accounts_run/deriv', 'accounts_run/deriv_fb', 'accounts_run/shadow_deriv', 'accounts_run/warm', 'checkpoints/A2_end', 'trades_parts/deriv'):
        for dp, dn, fn in os.walk(O.P(sub)):
            files += [os.path.join(dp, f) for f in fn if '.tmp' not in f]
    for rel in ('randoms/random_paths_A2.csv', 'diagnostics/G1_E6p.csv', 'diagnostics/stage0_E6p_part1.csv', 'diagnostics/stage0_E6p_S015.csv', 'verify/identities_E6p_stage0.csv'):
        files.append(O.P(rel))
    for f in sorted(os.listdir(O.P('registration'))):
        p = O.P('registration', f)
        if os.path.isfile(p):
            files.append(p)
    files = sorted(set(files))
    ctxp = get_context('fork')
    with ctxp.Pool(64) as pool:
        shas = pool.map(_sha, files, chunksize=8)
    man = '\n'.join('%s  %s' % (s, O.rel(p)) for s, p in shas) + '\n'
    mp = O.P('registration', 'seal_A2_manifest.txt')
    O.atomic_write_text(mp, man)
    seal_ = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), n_files=len(files), sha256_manifest=O.sha_file(mp), manifest='registration/seal_A2_manifest.txt',
                 note='推导段（2010-01-04 … 2018-12-28）全部预设账户 / 反馈 / WARM / 影子 / 随机与 G1 封存；方式 B 不停等')
    O.atomic_write_json(O.P('registration', 'seal_A2.json'), seal_)
    print(json.dumps(seal_, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    {'probe': probe, 'seal': seal}[sys.argv[1]]()
