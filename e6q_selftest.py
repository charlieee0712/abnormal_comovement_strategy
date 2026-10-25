# -*- coding: utf-8 -*-
"""E6q 引擎工程自检（brief §1.1 / §2 S0-F / S0-G / §4 断点；只读恒等差、计数与耗时，不读任何新臂的收益读数）：
① E6P_ACCOUNT_REPLICATION：E6q 引擎跑 E6p 已有坐标（NATIVE × {NONE, T1a, LEVEL, T8} × H5 / 20 / 30 × 全部 form / memory；IDEAL H20；CASH_REMAIN / RECYCLE_HALF
   × H5 / 20 × 三触发 × 两情景），与 E6p accounts_run/full 逐日 DY（E6p 全部列）比：相对差 ≤ 1e−9（同 NaN 位置）；
② 零干预（S0-F ZERO_INTERVENTION_EQ_NATIVE）：trigger = NONE 的 10 个非 NATIVE 臂 ≡ NATIVE（H20 / H30 / H5）；
③ 端点（S0-F）：PSTAR_INF（M2 / M3 两档 × T1a / LEVEL，p* = 1e30）≡ 同触发 NATIVE；THETA_ONE（EXIT_HALF θ = 1）≡ 同触发 NATIVE、REARM θ = 0 不卖（≡ NONE 父）；
   NEW_FILTER_OFF（REINVEST_NEW 关 new 过滤）≡ 同触发 NATIVE；
④ 断点恢复幂等：四个新机制账户中点存 → 恢复 → 续跑 vs 一次跑完（全部 DY 与状态 hash）；
⑤ 冒烟（只看错误码、守恒与计数）：11 臂 × {T1a, LEVEL, T8, UNION_T1a_T8} × H20、IDEAL、影子首达、RANDOM_TARGET 两域；计时供 S0-L。
输出 verify/selftest_E6q.json 与 verify/selftest_identities_E6q.csv。用法：python3 e6q_selftest.py --workers 96"""
import os
import sys
import json
import time
import argparse
import traceback
from multiprocessing import get_context

import numpy as np
import pandas as pd

import e6q_core as O
import e6q_engine as E
import e6q_acct as A

G = {}
NAT_COLS = ('nav_pre', 'nav_post', 'fee', 'exposure', 'cash_share', 'n_hold', 'net_excess', 'r_net', 'nav_close', 'n_lots')
TRIG_E6P = {'NONE': 'NONE', 'T1a': 'T1a', 'T1b_LEVEL': 'T1b_LEVEL', 'T8': 'T8_LIMIT_CLOSE'}
TRIG_E6Q = {v: k for k, v in TRIG_E6P.items()}


def relmax(a, b):
    """同形状数组：NaN 位置须相同；返回 (max_abs, max_rel)，rel = |a − b| / max(|a|, |b|)（两者为 0 记 0）。"""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if a.shape != b.shape:
        return float('inf'), float('inf')
    fa, fb = np.isfinite(a), np.isfinite(b)
    if not np.array_equal(fa, fb):
        return float('inf'), float('inf')
    m = fa & fb
    if not m.any():
        return 0.0, 0.0
    d = np.abs(a[m] - b[m])
    s = np.maximum(np.abs(a[m]), np.abs(b[m]))
    r = np.where(s > 0, d / np.where(s > 0, s, 1.0), 0.0)
    return float(d.max()), float(r.max())


def ident(acc, V0=O.V0):
    DY = acc.DY
    I = E.DYI
    navd = float(np.max(np.abs(DY[:, I['nav_pre']] - DY[:, I['fee']] - DY[:, I['nav_post']]) / V0))
    tele = float(np.prod(1.0 + DY[:, I['r_net']])) - DY[-1, I['nav_post']] / V0
    cash = DY[:, I['cash_close']]
    tag = DY[:, I['tag_amt']]
    over = float(np.max(np.where(np.isfinite(cash) & np.isfinite(tag), tag - cash, 0.0)) / V0)
    return dict(nav_identity_rel=navd, telescope_abs=float(abs(tele)), min_cash_share=float(np.nanmin(DY[:, I['cash_share']])), err=int(acc.S_i[E.SI_ERR]),
                tag_minus_cash_max_rel=over, tag_end=float(DY[-1, I['tag_amt']]), lock_end=float(DY[-1, I['lock_amt']]))


def setup():
    mk = A.Market()
    G['mk'] = mk
    G['f'] = {(f, m): mk.formation(f, m) for f in O.FORMS for m in O.MEMS if (f == O.MAIN_FORM or m == 'HG10')}
    # 预编译（父进程编译后 fork 子进程共享）：全部开关组合各跑 30 日
    for arm in O.ARMS:
        for trig in ('NONE', 'T1a', 'UNION_T1a_T8'):
            row = dict(form=O.MAIN_FORM, memory='HG10', H=20, arm=arm, trigger=trig, scenario='FEASIBLE_DAILY')
            ip, fp, tn = A.spec_params(row, tlog=True)
            A.Account(mk, ip, fp, tn, G['f'][(O.MAIN_FORM, 'HG10')], lcap=1 << 14, incap=1 << 16, tlcap=1 << 16).run(0, 30)
    for rt in (E.RT_WITHIN, E.RT_SOURCE):
        row = dict(form=O.MAIN_FORM, memory='HG10', H=20, arm='REINVEST_LIQ_1E8', trigger='T1a', scenario='FEASIBLE_DAILY')
        ip, fp, tn = A.spec_params(row, rt=rt, seed=7)
        A.Account(mk, ip, fp, tn, G['f'][(O.MAIN_FORM, 'HG10')], lcap=1 << 14, incap=1 << 16).run(0, 30)
    row = dict(form=O.MAIN_FORM, memory='HG10', H=20, arm='NATIVE', trigger='T1a', scenario='FEASIBLE_DAILY')
    ip, fp, tn = A.spec_params(row, shadow=True, fhit=1)
    A.Account(mk, ip, fp, tn, G['f'][(O.MAIN_FORM, 'HG10')], lcap=1 << 14, incap=1 << 16).run(0, 30)


def make(row, **kw):
    mk = G['mk']
    tlog = kw.get('tlog', False)
    ip, fp, tn = A.spec_params(row, **kw)
    return A.Account(mk, ip, fp, tn, G['f'][(row['form'], row['memory'])], tlcap=(1 << 21) if tlog else 0)


def dyp(name):
    return O.P('tmp', 'selftest', 'DY_%s.npy' % name)


def job(task):
    t0 = time.time()
    try:
        kind = task['kind']
        mk = G['mk']
        T = mk.T
        res = dict(task=task['name'], kind=kind)
        if kind == 'REPL':
            a = make(task['row']).run(0, T)
            z = np.load(O.E6P('accounts_run', 'full', task['e6p_hash'][:2], '%s.npz' % task['e6p_hash']), allow_pickle=False)
            ref = z['DY']
            ne = ref.shape[1]
            mabs, mrel = relmax(a.DY[:len(ref), :ne], ref)
            res.update(max_abs_diff=mabs, max_rel_diff=mrel, n_rows=int(len(ref)), n_cols=int(ne), ident=ident(a))
        elif kind == 'RUN':
            a = make(task['row'], **task.get('kw', {})).run(0, T)
            np.save(dyp(task['name']), a.DY)
            res.update(ident=ident(a), n_intents=int(a.S_i[E.SI_NIN]))
        elif kind == 'CKPT':
            row = task['row']
            mid = T // 2
            a = make(row).run(0, T)
            b = make(row).run(0, mid)
            pth = O.P('tmp', 'selftest', 'ckpt_%s.npz' % task['name'])
            b.checkpoint(pth, dict(test='selftest', mid=mid))
            c = make(row)
            c.restore(pth)
            c.run(mid, T)
            same = all(np.array_equal(a._used(k), c._used(k), equal_nan=True) if np.asarray(getattr(a, k)).dtype.kind == 'f'
                       else np.array_equal(a._used(k), c._used(k)) for k in A.Account.STATE)
            res.update(DY_maxabs=relmax(a.DY, c.DY)[0], state_equal=bool(same), hash_equal=a.state_hash() == c.state_hash(), ident=ident(a))
        elif kind == 'SMOKE':
            a = make(task['row'], **task.get('kw', {})).run(0, T)
            I = E.DYI
            st = a.IN_i[:int(a.S_i[E.SI_NIN]), E.IN_STATUS]
            res.update(ident=ident(a), n_intents=int(a.S_i[E.SI_NIN]), status_counts={int(k): int(v) for k, v in zip(*np.unique(st, return_counts=True))},
                       si=dict(deny=int(a.S_i[E.SI_DENY]), quar=int(a.S_i[E.SI_QUAR]), override=int(a.S_i[E.SI_OVERRIDE]), half=int(a.S_i[E.SI_HALF]),
                               rearm=int(a.S_i[E.SI_REARMN]), fallback=int(a.S_i[E.SI_FALLBACK]), rt_limit=int(a.S_i[E.SI_RTLIM]),
                               rt_nomatch=int(a.S_i[E.SI_RTNOM]), rt_identity=int(a.S_i[E.SI_RTID]), new_empty=int(a.S_i[E.SI_NEWEMPTY]),
                               noact=int(a.S_i[E.SI_NOACT]), internal=int(a.S_i[E.SI_INTERNAL]), reentry=int(a.S_i[E.SI_REENTRY]), n_trades=int(a.S_i[E.SI_NTL])),
                       dy=dict(extra_plan=float(a.DY[:, I['extra_plan']].sum()), extra_native_plan=float(a.DY[:, I['extra_native_plan']].sum()),
                               deny_amt=float(a.DY[:, I['deny_amt']].sum()), tk_quar_max=float(a.DY[:, I['tk_quar']].max()),
                               m3_req=float(a.DY[:, I['m3_req_val']].sum()), m3_alloc=float(a.DY[:, I['m3_alloc_val']].sum()),
                               m3_forced=float(a.DY[:, I['m3_forced_val']].sum()), half_start=float(a.DY[:, I['half_start_n']].sum()),
                               half_done=float(a.DY[:, I['half_done_n']].sum()), rearm=float(a.DY[:, I['rearm_n']].sum()),
                               new_n_mean=float(np.mean(a.DY[:, I['new_n']])), rt_short=float(a.DY[:, I['rt_short']].sum()),
                               rt_status_counts={int(k): int(v) for k, v in zip(*np.unique(a.DY[:, I['rt_status']].astype(np.int64), return_counts=True))},
                               hits=int(a.HITS.sum()), risk=int(a.RISK.sum()), mean_expo=float(np.mean(a.DY[:, I['exposure']])),
                               cost_s05=float(np.nansum(a.DY[:, I['cost_s05']])), cost_s10=float(np.nansum(a.DY[:, I['cost_s10']]))))
        res['wall_s'] = round(time.time() - t0, 2)
        res['status'] = 'OK'
        return res
    except Exception as e:
        return dict(task=task['name'], kind=task['kind'], status='FAILED', err='%s: %s' % (type(e).__name__, str(e)[:300]), tb=traceback.format_exc()[-1500:],
                    wall_s=round(time.time() - t0, 2))


def row_of(form, mem, H, arm, trig, scen='FEASIBLE_DAILY'):
    return dict(form=form, memory=mem, H=H, arm=arm, trigger=trig, scenario=scen)


def tasks():
    R = pd.read_csv(O.E6P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
    out = []
    sel = R[(R.role == 'ACCOUNT') & (R.cap == 'SOURCE') & (R.renew == '0') & R.trigger.isin(list(TRIG_E6Q)) & R.deploy.isin(['NATIVE', 'CASH_REMAIN', 'RECYCLE_HALF'])]
    for r in sel.itertuples(index=False):
        H = int(r.H)
        if r.deploy == 'NATIVE':
            ok = (H in (5, 20, 30) and r.execution_profile == 'FEASIBLE_DAILY') or (H == 20 and r.execution_profile == 'IDEALIZED_SOURCE_FILL')
        else:
            ok = H in (5, 20)
        if not ok:
            continue
        row = row_of(r.form, r.memory, H, r.deploy, TRIG_E6Q[r.trigger], r.execution_profile)
        out.append(dict(kind='REPL', name='REPL_%s_%s_%s_H%d_%s_%s' % (r.execution_profile[:2], r.form, r.memory, H, r.deploy, r.trigger), row=row,
                        e6p_hash=r.exec_hash, e6p_exec_id=r.exec_id))
    mf = O.MAIN_FORM
    for H in (5, 20, 30):
        out.append(dict(kind='RUN', name='Z_NATIVE_NONE_H%d' % H, row=row_of(mf, 'HG10', H, 'NATIVE', 'NONE')))
        for arm in O.ARMS:
            if arm != 'NATIVE':
                out.append(dict(kind='RUN', name='Z_%s_NONE_H%d' % (arm, H), row=row_of(mf, 'HG10', H, arm, 'NONE')))
    for trig in ('T1a', 'T1b_LEVEL'):
        out.append(dict(kind='RUN', name='E_NATIVE_%s_H20' % trig, row=row_of(mf, 'HG10', 20, 'NATIVE', trig)))
        for arm in ('REINVEST_LIQ_1E8', 'REINVEST_LIQ_5E8', 'EXIT_GATE_LIQ_1E8', 'EXIT_GATE_LIQ_5E8'):
            out.append(dict(kind='RUN', name='PINF_%s_%s_H20' % (arm, trig), row=row_of(mf, 'HG10', 20, arm, trig), kw=dict(pstar=1e30)))
        out.append(dict(kind='RUN', name='TH1_EXIT_HALF_%s_H20' % trig, row=row_of(mf, 'HG10', 20, 'EXIT_HALF', trig), kw=dict(theta=1.0)))
        out.append(dict(kind='RUN', name='TH0_EXIT_HALF_REARM_%s_H20' % trig, row=row_of(mf, 'HG10', 20, 'EXIT_HALF_REARM', trig), kw=dict(theta=0.0)))
        out.append(dict(kind='RUN', name='NF0_REINVEST_NEW_%s_H20' % trig, row=row_of(mf, 'HG10', 20, 'REINVEST_NEW', trig), kw=dict(m1=0)))
    for nm, arm, trig, H in (('CKPT_GATE5_LVL_H20', 'EXIT_GATE_LIQ_5E8', 'T1b_LEVEL', 20), ('CKPT_REARM_T1a_H20', 'EXIT_HALF_REARM', 'T1a', 20),
                             ('CKPT_LIQ1_LVL_H20', 'REINVEST_LIQ_1E8', 'T1b_LEVEL', 20), ('CKPT_NEW_T1a_H30', 'REINVEST_NEW', 'T1a', 30),
                             ('CKPT_HALFRECYCLE_UNION_H20', 'EXIT_HALF_RECYCLE_HALF', 'UNION_T1a_T8', 20)):
        out.append(dict(kind='CKPT', name=nm, row=row_of(mf, 'HG10', H, arm, trig)))
    for arm in O.ARMS:
        for trig in ('T1a', 'T1b_LEVEL', 'T8', 'UNION_T1a_T8'):
            out.append(dict(kind='SMOKE', name='S_%s_%s_H20' % (arm, trig), row=row_of(mf, 'HG10', 20, arm, trig), kw=dict(tlog=(trig == 'T1b_LEVEL'))))
    for arm in O.CORE_ARMS:
        out.append(dict(kind='SMOKE', name='S_IDEAL_%s_LVL_H20' % arm, row=row_of(mf, 'HG10', 20, arm, 'T1b_LEVEL', 'IDEALIZED_SOURCE_FILL')))
    out.append(dict(kind='SMOKE', name='S_SHADOW_FHIT_T1a_H20', row=row_of(mf, 'HG10', 20, 'NATIVE', 'T1a'), kw=dict(shadow=True, fhit=1)))
    for arm in ('NATIVE', 'REINVEST_NEW', 'REINVEST_LIQ_1E8', 'REINVEST_LIQ_5E8'):
        for rt, rn in ((E.RT_WITHIN, 'WITHIN'), (E.RT_SOURCE, 'SOURCE')):
            out.append(dict(kind='SMOKE', name='S_RT_%s_%s_LVL_H20' % (rn, arm), row=row_of(mf, 'HG10', 20, arm, 'T1b_LEVEL'), kw=dict(rt=rt, seed=12345)))
    return out


def cmp_rows(a_name, b_name, cols=None):
    a = np.load(dyp(a_name))
    b = np.load(dyp(b_name))
    if cols is None:
        return relmax(a[:, :76], b[:, :76])
    ix = [E.DYI[c] for c in cols]
    return relmax(a[:, ix], b[:, ix])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=96)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(O.P('tmp', 'selftest'), exist_ok=True)
    setup()
    O.log('预编译完成 %.0f 秒' % (time.time() - t0))
    TS = tasks()
    ctx = get_context('fork')
    res = {}
    with ctx.Pool(a.workers) as pool:
        for r in pool.imap_unordered(job, sorted(TS, key=lambda t: {'REPL': 1, 'RUN': 0, 'CKPT': 2, 'SMOKE': 3}[t['kind']]), chunksize=1):
            res[r['task']] = r
            if r['status'] != 'OK' or r['kind'] in ('CKPT',):
                O.log('%s %s %.1fs %s' % (r['task'], r['status'], r['wall_s'], r.get('err', '')))
    rows = []
    for t in TS:
        if t['kind'] != 'REPL':
            continue
        r = res[t['name']]
        ok = r['status'] == 'OK' and r['max_rel_diff'] <= 1e-9
        rows.append(dict(check_id='E6P_ACCOUNT_REPLICATION', description='E6q 引擎（新开关全关）vs E6p accounts_run/full 逐日 DY 全列：%s' % t['name'],
                         exec_id=t['e6p_exec_id'], value=r.get('max_abs_diff', ''), max_abs_diff=r.get('max_rel_diff', ''), tolerance=1e-9,
                         status='PASS' if ok else 'DIFFERS'))
    for H in (5, 20, 30):
        for arm in O.ARMS:
            if arm == 'NATIVE':
                continue
            nm = 'Z_%s_NONE_H%d' % (arm, H)
            if res[nm]['status'] != 'OK':
                md = float('inf')
            else:
                md = cmp_rows(nm, 'Z_NATIVE_NONE_H%d' % H)[1]
            rows.append(dict(check_id='ZERO_INTERVENTION_EQ_NATIVE', description='%s ≡ NATIVE（trigger = NONE；E6p 76 列逐日相对差）' % nm, exec_id='', value='',
                             max_abs_diff=md, tolerance=1e-9, status='PASS' if md <= 1e-9 else 'DIFFERS'))
    for trig in ('T1a', 'T1b_LEVEL'):
        nat = 'E_NATIVE_%s_H20' % trig
        for arm in ('REINVEST_LIQ_1E8', 'REINVEST_LIQ_5E8', 'EXIT_GATE_LIQ_1E8', 'EXIT_GATE_LIQ_5E8'):
            nm = 'PINF_%s_%s_H20' % (arm, trig)
            md = cmp_rows(nm, nat)[1] if res[nm]['status'] == 'OK' and res[nat]['status'] == 'OK' else float('inf')
            rows.append(dict(check_id='PSTAR_INF_EQ_NATIVE', description='%s（p* = 1e30）≡ 同触发 NATIVE（76 列）' % nm, exec_id='', value='', max_abs_diff=md,
                             tolerance=1e-9, status='PASS' if md <= 1e-9 else 'DIFFERS'))
        nm = 'TH1_EXIT_HALF_%s_H20' % trig
        md = cmp_rows(nm, nat)[1] if res[nm]['status'] == 'OK' else float('inf')
        rows.append(dict(check_id='THETA_ONE_EQ_NATIVE', description='%s（θ = 1）≡ 同触发 NATIVE（76 列）' % nm, exec_id='', value='', max_abs_diff=md,
                         tolerance=1e-9, status='PASS' if md <= 1e-9 else 'DIFFERS'))
        nm = 'TH0_EXIT_HALF_REARM_%s_H20' % trig
        md = cmp_rows(nm, 'Z_NATIVE_NONE_H20', NAT_COLS)[1] if res[nm]['status'] == 'OK' else float('inf')
        rows.append(dict(check_id='THETA_ONE_EQ_NATIVE', description='%s（θ = 0）不产生卖出：NAV / 现金 / 持仓 ≡ 无退出 NATIVE 父' % nm, exec_id='', value='',
                         max_abs_diff=md, tolerance=1e-9, status='PASS' if md <= 1e-9 else 'DIFFERS'))
        nm = 'NF0_REINVEST_NEW_%s_H20' % trig
        md = cmp_rows(nm, nat)[1] if res[nm]['status'] == 'OK' else float('inf')
        rows.append(dict(check_id='NEW_FILTER_OFF_EQ_NATIVE', description='%s（new 过滤关）≡ 同触发 NATIVE（76 列）' % nm, exec_id='', value='', max_abs_diff=md,
                         tolerance=1e-9, status='PASS' if md <= 1e-9 else 'DIFFERS'))
    for t in TS:
        if t['kind'] != 'CKPT':
            continue
        r = res[t['name']]
        ok = r['status'] == 'OK' and r['DY_maxabs'] == 0.0 and r['state_equal'] and r['hash_equal']
        rows.append(dict(check_id='CHECKPOINT_RESTORE_IDEMPOTENT', description='%s：中点 checkpoint → 恢复 → 续跑 vs 一次跑完（全部 DY 与状态数组逐位）' % t['name'],
                         exec_id='', value='', max_abs_diff=r.get('DY_maxabs', ''), tolerance=0.0, status='PASS' if ok else 'DIFFERS'))
    for nm, r in res.items():
        idn = r.get('ident') if r['status'] == 'OK' else None
        if r['status'] != 'OK':
            rows.append(dict(check_id='CASH_EQUATION_SELFTEST', description='%s：运行失败 %s' % (nm, r.get('err', '')), exec_id='', value='', max_abs_diff='',
                             tolerance=1e-9, status='DIFFERS'))
            continue
        if not idn:
            continue
        ok = (idn['err'] == 0 and idn['nav_identity_rel'] <= 1e-9 and idn['telescope_abs'] <= 1e-8 and idn['min_cash_share'] >= -1e-9
              and idn['tag_minus_cash_max_rel'] <= 1e-9)
        rows.append(dict(check_id='CASH_EQUATION_SELFTEST', description='%s：nav_post = nav_pre − fee；NAV 伸缩；错误码 0；现金非负；标签余额 ≤ 收盘现金' % nm, exec_id='',
                         value=idn['err'], max_abs_diff=max(idn['nav_identity_rel'], idn['telescope_abs'], idn['tag_minus_cash_max_rel']), tolerance=1e-8,
                         status='PASS' if ok else 'DIFFERS'))
    I = pd.DataFrame(rows)
    O.atomic_write_csv(O.P('verify', 'selftest_identities_E6q.csv'), I)
    walls = pd.DataFrame([dict(task=k, kind=v['kind'], wall_s=v['wall_s']) for k, v in res.items()])
    out = dict(T=G['mk'].T, wall_s=round(time.time() - t0, 1), n_tasks=len(res), failed=[k for k, v in res.items() if v['status'] != 'OK'],
               n_identity_rows=len(I), n_identity_bad=int((I.status != 'PASS').sum()), by_check=I.groupby('check_id').status.value_counts().unstack(fill_value=0).to_dict('index'),
               wall_by_kind=walls.groupby('kind').wall_s.describe()[['count', 'mean', 'max']].round(2).to_dict('index'), results=res)
    O.atomic_write_json(O.P('verify', 'selftest_E6q.json'), json.loads(json.dumps(out, default=float)))
    O.write_receipt('E6q_selftest', [O.P('verify', 'selftest_identities_E6q.csv'), O.P('verify', 'selftest_E6q.json')],
                    code=[__file__, E.__file__, A.__file__, O.__file__], n_tasks=len(res), n_identity_bad=out['n_identity_bad'], wall_s=out['wall_s'])
    print(json.dumps(dict(wall_s=out['wall_s'], failed=out['failed'], n_identity_rows=len(I), n_identity_bad=out['n_identity_bad'], by_check=out['by_check'],
                          wall_by_kind=out['wall_by_kind']), ensure_ascii=False), flush=True)
    bad = I[I.status != 'PASS']
    if len(bad):
        print(bad.to_string()[:6000], flush=True)
    for k in out['failed']:
        print(k, res[k].get('err'), res[k].get('tb', '')[-900:], flush=True)
    sys.exit(1 if (out['failed'] or out['n_identity_bad']) else 0)


if __name__ == '__main__':
    main()
