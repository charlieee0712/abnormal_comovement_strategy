# -*- coding: utf-8 -*-
"""E6p 引擎工程自检（brief §2 S0-2 / S0-3 / S0-5 恢复幂等 / S0-12 计时；只读恒等差、计数与耗时，不读任何退出账户的后段收益）：
① E6O_ACCOUNT_REPLICATION：E6p 引擎跑 E6o P_ACCOUNT 坐标（A4b_CVRv5 × 三记忆 × H5 / 10 / 20 × 两情景），与 E6o accounts_run/full 逐日 DY（E6o 39 列）比 ≤ 1e−9；
   E6o 主对象（HG10 × H5 × SOURCE_T1b × ENGINE_NATIVE）逐日复现 + FULL D 现算 vs E6o 汇总 1.979759（≤ 1e−6）。（E6o 账户是已曝光读数，复现只核仪器）
② 零干预恒等（S0-3）：NOEXIT / RECYCLE 三臂 NONE / CASH NONE / D80·D95 K ≡ 0 / RENEW5 无检查点（H5 自然无检查点 + H20 全确认）≡ 同 H NATIVE 父（E6o 39 列 ≤ 1e−9）；
③ 断点恢复幂等：主对象 H20 × T1a 中点存 → 恢复 → 续跑 vs 一次跑完（全部 DY 与状态 hash）；
④ 新功能冒烟（只看错误码与守恒，不读收益）：D80 / D95 / ABS01 / CASH_REMAIN / RECYCLE 三臂 / MIRROR / T8 / UNION / RENEW5 / 影子 / IDEAL；计时供 S0-12。
输出 verify/selftest_E6p.json 与 verify/selftest_identities_E6p.csv。用法：python3 e6p_selftest.py --workers 48"""
import os
import sys
import json
import time
import argparse
import traceback
from multiprocessing import get_context

import numpy as np
import pandas as pd

import e6p_core as O
import e6p_engine as E
import e6p_acct as A

G = {}
NE6O = 39


def e6o_reg():
    R = pd.read_csv(O.E6O('registration', 'registry_E6o.csv'), keep_default_na=False, dtype=str)
    return R


def e6o_dy(h):
    z = np.load(O.E6O('accounts_run', 'full', h[:2], '%s.npz' % h), allow_pickle=False)
    return z['DY']


def maxabs(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    fa, fb = np.isfinite(a), np.isfinite(b)
    if not np.array_equal(fa, fb):
        return float('inf')
    m = fa & fb
    return float(np.max(np.abs(a[m] - b[m]))) if m.any() else 0.0


def seg_D(dc, dp):
    """段 D 与 FULL（按共同有限日数加权）：ann_pp × 日均（子 − 父）。"""
    mk = G['mk']
    segi = np.array([O.seg_of_date(d) for d in mk.dates])
    out = {}
    num = 0.0
    den = 0
    for s in O.SEGS:
        m = (segi == s) & np.isfinite(dc) & np.isfinite(dp)
        v = float(np.mean(dc[m] - dp[m]) * O.ANN_PP)
        out[s] = v
        num += v * int(m.sum())
        den += int(m.sum())
    out['FULL'] = num / den
    return out


def ident(acc, V0=O.V0):
    DY = acc.DY
    navd = float(np.max(np.abs(DY[:, 0] - DY[:, 2] - DY[:, 1])))
    tele = float(np.prod(1.0 + DY[:, 9])) - DY[-1, 1] / V0
    return dict(nav_identity_maxabs=navd, telescope_abs=float(abs(tele)), min_cash_share=float(DY[:, 6].min()), err=int(acc.S_i[E.SI_ERR]),
                tag_end=float(DY[-1, 16]), lock_end=float(DY[-1, 26]))


def setup():
    mk = A.Market()
    G['mk'] = mk
    G['f'] = {(f, m): mk.formation(f, m) for f in O.FORMS for m in O.MEMS if (f == O.MAIN_FORM or m == 'HG10')}
    G['nf'] = {f: mk.natural(f) for f in O.FORMS}
    ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True, deploy=E.DP_TARGET, target=0.8, cap=E.CP_REL, renew=5, recycle=E.RY_COSTNET)
    A.Account(mk, ip, fp, 'T1a', G['f'][(O.MAIN_FORM, 'HG10')], nf_csr=G['nf'][O.MAIN_FORM], lcap=1 << 14, incap=1 << 16).run(0, 30)


def make(H, trig_name, form=O.MAIN_FORM, mem='HG10', **kw):
    mk = G['mk']
    tm = kw.pop('tm', E.TM_PANEL if trig_name else E.TM_NONE)
    tg = kw.pop('targets', None)
    te = kw.pop('tgt_expo', None)
    ip, fp = A.ip_fp(H, tm, **kw)
    return A.Account(mk, ip, fp, trig_name, G['f'][(form, mem)], nf_csr=G['nf'][form], tgt_expo=te, targets=tg,
                     tlcap=(1 << 21) if kw.get('tlog') else 0)


def job(task):
    t0 = time.time()
    try:
        kind = task['kind']
        mk = G['mk']
        T = mk.T
        res = dict(task=task['name'], kind=kind)
        if kind == 'REPL':
            ip, fp = A.ip_fp(task['H'], E.TM_NONE, fund=E.FD_NATIVE, ideal=task['ideal'])
            a = A.Account(mk, ip, fp, None, G['f'][(O.MAIN_FORM, task['mem'])]).run(0, T)
            ref = e6o_dy(task['e6o_hash'])
            res.update(max_abs_diff=maxabs(a.DY[:, :NE6O], ref[:, :NE6O]), ident=ident(a))
            np.save(O.P('tmp', 'selftest', 'DY_%s.npy' % task['name']), a.DY)
        elif kind == 'MAIN_E6O':
            ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True, ideal=task['ideal'])
            a = A.Account(mk, ip, fp, 'T1b', G['f'][(O.MAIN_FORM, 'HG10')]).run(0, T)
            ref = e6o_dy(task['e6o_hash'])
            res.update(max_abs_diff=maxabs(a.DY[:, :NE6O], ref[:, :NE6O]), ident=ident(a))
            np.save(O.P('tmp', 'selftest', 'DY_%s.npy' % task['name']), a.DY)
        elif kind == 'ZERO':
            a = make(task['H'], None, **task['kw']).run(0, T)
            res.update(ident=ident(a), n_intents=int(a.S_i[E.SI_NIN]), renew_ck=int(a.S_i[E.SI_RCHK]))
            np.save(O.P('tmp', 'selftest', 'DY_%s.npy' % task['name']), a.DY)
        elif kind == 'CKPT':
            kw = task['kw']
            mid = T // 2
            a = make(20, 'T1a', **dict(kw)).run(0, T)
            b = make(20, 'T1a', **dict(kw)).run(0, mid)
            pth = O.P('tmp', 'selftest', 'ckpt_%s.npz' % task['name'])
            b.checkpoint(pth, dict(test='selftest', mid=mid))
            c = make(20, 'T1a', **dict(kw))
            c.restore(pth)
            c.run(mid, T)
            same = all(np.array_equal(a._used(k), c._used(k), equal_nan=True) if np.asarray(getattr(a, k)).dtype.kind == 'f'
                       else np.array_equal(a._used(k), c._used(k)) for k in A.Account.STATE)
            res.update(DY_maxabs=maxabs(a.DY, c.DY), state_equal=bool(same), hash_equal=a.state_hash() == c.state_hash(), ident=ident(a))
        elif kind == 'SMOKE':
            kw = dict(task['kw'])
            if task.get('mirror_of'):
                o = np.load(O.P('tmp', 'selftest', 'DY_%s.npy' % task['mirror_of']))
                cash = o[:, 6] * o[:, 1]
                kw['tgt_expo'] = np.where(o[:, 17] > 0, 1.0 - cash / np.where(o[:, 17] > 0, o[:, 17], 1.0), np.nan)
            a = make(task['H'], task['trig'], form=task.get('form', O.MAIN_FORM), mem=task.get('mem', 'HG10'), **kw).run(0, T)
            st = a.IN_i[:int(a.S_i[E.SI_NIN]), E.IN_STATUS]
            res.update(ident=ident(a), n_intents=int(a.S_i[E.SI_NIN]), status_counts={int(k): int(v) for k, v in zip(*np.unique(st, return_counts=True))},
                       n_lots_max=int(a.DY[:, 47].max()), deploy_plan_sum=float(a.DY[:, 41].sum()), deploy_buy_sum=float(a.DY[:, 42].sum()),
                       renew=dict(ck=int(a.S_i[E.SI_RCHK]), conf=int(a.S_i[E.SI_RCONF2]), rej=int(a.S_i[E.SI_RREJ]), unk=int(a.S_i[E.SI_RUNK])),
                       noact=int(a.S_i[E.SI_NOACT]), n_trades=int(a.S_i[E.SI_NTL]), hits=int(a.HITS.sum()), lots_closed=int(a.S_i[E.SI_LCLOSED]),
                       zd_min=float(np.nanmin(a.DY[:, 44])), sector_active_max=float(np.nanmax(a.DY[:, 61])),
                       rt=dict(budget=float(a.DY[:, 55].sum()), native=float(a.DY[:, 56].sum()), cost0=float(a.DY[:, 57].sum()), costnet=float(a.DY[:, 58].sum()),
                               unknown=float(a.DY[:, 59].sum()), degen=float(a.DY[:, 60].sum())),
                       mean_expo=float(np.mean(a.DY[:, 3])), cost_s05_sum=float(np.nansum(a.DY[:, 39])), fb_sum=float(a.DY[:, 48].sum()))
            if task.get('save'):
                np.save(O.P('tmp', 'selftest', 'DY_%s.npy' % task['name']), a.DY)
        res['wall_s'] = round(time.time() - t0, 2)
        res['status'] = 'OK'
        return res
    except Exception as e:
        return dict(task=task['name'], kind=task['kind'], status='FAILED', err='%s: %s' % (type(e).__name__, str(e)[:300]), tb=traceback.format_exc()[-1200:],
                    wall_s=round(time.time() - t0, 2))


def tasks():
    R = e6o_reg()
    out = []
    for prof, ideal in (('FEASIBLE_DAILY', False), ('IDEALIZED_SOURCE_FILL', True)):
        for H in (5, 10, 20):
            for mem in O.MEMS:
                r = R[(R.series == 'P_ACCOUNT') & (R.form == O.MAIN_FORM) & (R.memory == mem) & (R.H == 'H%d' % H) & (R.execution_profile == prof)
                      & (R.support == 'FULLHIST')]
                if len(r) != 1:
                    raise RuntimeError('E6o P_ACCOUNT 坐标不唯一：%s %s H%d' % (prof, mem, H))
                out.append(dict(kind='REPL', name='REPL_%s_%s_H%d' % (prof[:2], mem, H), H=H, mem=mem, ideal=ideal, e6o_hash=r.iloc[0].exec_hash,
                                e6o_exec_id=r.iloc[0].exec_id))
        m = R[(R.is_main_object == '1') & (R.execution_profile == prof)]
        out.append(dict(kind='MAIN_E6O', name='MAIN_E6O_%s' % prof[:2], ideal=ideal, e6o_hash=m.iloc[0].exec_hash, e6o_exec_id=m.iloc[0].exec_id,
                        e6o_parent_hash=R[R.exec_id == m.iloc[0].parent_exec_id].iloc[0].exec_hash))
    for H in (5, 20):
        nat = dict(fund=E.FD_NATIVE)
        out += [dict(kind='ZERO', name='Z_PARENT_H%d' % H, H=H, kw=dict(nat)),
                dict(kind='ZERO', name='Z_NOEXIT_H%d' % H, H=H, kw=dict(fund=E.FD_NATIVE, exit_on=True, tm=E.TM_PANEL)),
                dict(kind='ZERO', name='Z_RECYCLE_HALF_H%d' % H, H=H, kw=dict(fund=E.FD_NATIVE, exit_on=True, tm=E.TM_PANEL, recycle=E.RY_HALF)),
                dict(kind='ZERO', name='Z_RECYCLE_COST0_H%d' % H, H=H, kw=dict(fund=E.FD_NATIVE, exit_on=True, tm=E.TM_PANEL, recycle=E.RY_COST0)),
                dict(kind='ZERO', name='Z_RECYCLE_COSTNET_H%d' % H, H=H, kw=dict(fund=E.FD_NATIVE, exit_on=True, tm=E.TM_PANEL, recycle=E.RY_COSTNET)),
                dict(kind='ZERO', name='Z_CASH_H%d' % H, H=H, kw=dict(fund=E.FD_CASH, exit_on=True, tm=E.TM_PANEL)),
                dict(kind='ZERO', name='Z_D80K0_H%d' % H, H=H, kw=dict(fund=E.FD_NATIVE, deploy=E.DP_TARGET, target=0.80, cap=E.CP_REL, zerok=True)),
                dict(kind='ZERO', name='Z_D95K0_H%d' % H, H=H, kw=dict(fund=E.FD_NATIVE, deploy=E.DP_TARGET, target=0.95, cap=E.CP_REL, zerok=True)),
                dict(kind='ZERO', name='Z_RENEW_%s_H%d' % ('NATURAL' if H == 5 else 'ALLOK', H), H=H,
                     kw=dict(fund=E.FD_NATIVE, exit_on=True, renew=5, renewok=(H != 5)))]
    out.append(dict(kind='CKPT', name='CKPT_MAIN_T1a', kw=dict(fund=E.FD_NATIVE, exit_on=True)))
    out.append(dict(kind='CKPT', name='CKPT_D80_RENEW_COSTNET', kw=dict(fund=E.FD_NATIVE, exit_on=True, deploy=E.DP_TARGET, target=0.8, cap=E.CP_REL, renew=5,
                                                                        recycle=E.RY_COSTNET, tlog=False)))
    sm = [('S_NATIVE_T1a_H20', 20, 'T1a', dict(fund=E.FD_NATIVE, exit_on=True, tlog=True), True),
          ('S_NATIVE_LVL_H20', 20, 'T1b_LEVEL', dict(fund=E.FD_NATIVE, exit_on=True), False),
          ('S_D80_T1a_H20', 20, 'T1a', dict(fund=E.FD_NATIVE, exit_on=True, deploy=E.DP_TARGET, target=0.80, cap=E.CP_REL), False),
          ('S_D95_T1a_H20', 20, 'T1a', dict(fund=E.FD_NATIVE, exit_on=True, deploy=E.DP_TARGET, target=0.95, cap=E.CP_REL), False),
          ('S_D80_PARENT_H20', 20, None, dict(fund=E.FD_NATIVE, deploy=E.DP_TARGET, target=0.80, cap=E.CP_REL), False),
          ('S_D95_ABS01_PARENT_H20', 20, None, dict(fund=E.FD_NATIVE, deploy=E.DP_TARGET, target=0.95, cap=E.CP_ABS01), False),
          ('S_CASH_T1a_H20', 20, 'T1a', dict(fund=E.FD_CASH, exit_on=True), False),
          ('S_HALF_T1a_H20', 20, 'T1a', dict(fund=E.FD_NATIVE, exit_on=True, recycle=E.RY_HALF), False),
          ('S_COST0_T1a_H20', 20, 'T1a', dict(fund=E.FD_NATIVE, exit_on=True, recycle=E.RY_COST0), False),
          ('S_COSTNET_T1a_H20', 20, 'T1a', dict(fund=E.FD_NATIVE, exit_on=True, recycle=E.RY_COSTNET), False),
          ('S_T8_H20', 20, 'T8_LIMIT_CLOSE', dict(fund=E.FD_NATIVE, exit_on=True), False),
          ('S_UNION_H20', 20, 'UNION', dict(fund=E.FD_NATIVE, exit_on=True), False),
          ('S_RENEW_ONLY_H20', 20, None, dict(fund=E.FD_NATIVE, exit_on=True, renew=5), False),
          ('S_RENEW_T1a_H40', 40, 'T1a', dict(fund=E.FD_NATIVE, exit_on=True, renew=5), False),
          ('S_SHADOW_T1a_H20', 20, 'T1a', dict(fund=E.FD_NATIVE, shadow=True), False),
          ('S_IDEAL_T1a_H40', 40, 'T1a', dict(fund=E.FD_NATIVE, exit_on=True, ideal=True), False),
          ('S_FB_T1a_H20', 20, 'T1a', dict(fund=E.FD_NATIVE, exit_on=True, feedback=(5e8, 0.5, 0.5)), False),
          ('S_T1a_H40', 40, 'T1a', dict(fund=E.FD_NATIVE, exit_on=True), False),
          ('S_TRANSFER_MUNION_LVL_H40', 40, 'T1b_LEVEL', dict(fund=E.FD_NATIVE, exit_on=True), False)]
    for name, H, trig, kw, save in sm:
        t = dict(kind='SMOKE', name=name, H=H, trig=trig, kw=kw, save=save)
        if name == 'S_TRANSFER_MUNION_LVL_H40':
            t['form'] = 'M_union3_v2_CVRv5'
        out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=48)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(O.P('tmp', 'selftest'), exist_ok=True)
    setup()
    TS = tasks()
    first = [t for t in TS if t['kind'] != 'SMOKE' or t['name'] in ('S_NATIVE_T1a_H20',)]
    later = [t for t in TS if t not in first]
    ctx = get_context('fork')
    res = {}
    with ctx.Pool(a.workers) as pool:
        for r in pool.imap_unordered(job, first, chunksize=1):
            res[r['task']] = r
            O.log('%s %s %.1fs %s' % (r['task'], r['status'], r['wall_s'], r.get('err', '')))
    # 镜像冒烟需要 owner 日序列
    later.append(dict(kind='SMOKE', name='S_MIRROR_of_T1a_H20', H=20, trig=None, kw=dict(fund=E.FD_NATIVE, deploy=E.DP_MIRROR), mirror_of='S_NATIVE_T1a_H20'))
    with ctx.Pool(a.workers) as pool:
        for r in pool.imap_unordered(job, later, chunksize=1):
            res[r['task']] = r
            O.log('%s %s %.1fs %s' % (r['task'], r['status'], r['wall_s'], r.get('err', '')))
    # ---- 恒等行
    rows = []
    TD = {t['name']: t for t in TS}
    for t in TS:
        if t['kind'] == 'REPL':
            r = res[t['name']]
            rows.append(dict(check_id='E6O_ACCOUNT_REPLICATION', description='E6p 引擎 NATIVE 父 vs E6o P_ACCOUNT 逐日 DY（E6o 39 列）：%s' % t['name'],
                             exec_id=t['e6o_exec_id'], value='', max_abs_diff=r.get('max_abs_diff', ''), tolerance=1e-9,
                             status='PASS' if r['status'] == 'OK' and r['max_abs_diff'] <= 1e-9 else 'DIFFERS'))
    for prof in ('FE', 'ID'):
        nm = 'MAIN_E6O_%s' % prof
        r = res[nm]
        t = TD[nm]
        dc = np.load(O.P('tmp', 'selftest', 'DY_%s.npy' % nm))[:, 5]
        dp = np.load(O.P('tmp', 'selftest', 'DY_REPL_%s_HG10_H5.npy' % prof))[:, 5]
        D = seg_D(dc, dp)
        r['D'] = D
        S = pd.read_csv(O.E6O('statistics', 'account_summary_E6o.csv'), keep_default_na=False)
        ref = S[(S.exec_id == t['e6o_exec_id']) & (S.segment == 'FULL')]
        refD = float(ref.iloc[0].D_ann_pp) if len(ref) else float('nan')
        r['D_ref'] = refD
        rows.append(dict(check_id='E6O_ACCOUNT_REPLICATION', description='E6o 主对象（HG10 × H5 × SOURCE_T1b × ENGINE_NATIVE）逐日 DY + FULL D 现算 vs E6o 汇总',
                         exec_id=t['e6o_exec_id'], value=D['FULL'], max_abs_diff=max(r.get('max_abs_diff', np.inf), abs(D['FULL'] - refD)),
                         tolerance=1e-6, status='PASS' if r['status'] == 'OK' and r['max_abs_diff'] <= 1e-9 and abs(D['FULL'] - refD) <= 1e-6 else 'DIFFERS'))
    zmap = {'Z_NOEXIT': 'NOEXIT_EQ_PARENT', 'Z_RECYCLE_HALF': 'RECYCLE_NONE_EQ_NATIVE', 'Z_RECYCLE_COST0': 'RECYCLE_NONE_EQ_NATIVE',
            'Z_RECYCLE_COSTNET': 'RECYCLE_NONE_EQ_NATIVE', 'Z_CASH': 'CASH_NONE_EQ_NATIVE', 'Z_D80K0': 'DEPLOY_ZERO_BUDGET_EQ_NATIVE',
            'Z_D95K0': 'DEPLOY_ZERO_BUDGET_EQ_NATIVE', 'Z_RENEW_NATURAL': 'RENEW_NO_CHECKPOINT_EQ_PARENT', 'Z_RENEW_ALLOK': 'RENEW_NO_CHECKPOINT_EQ_PARENT'}
    for H in (5, 20):
        par = np.load(O.P('tmp', 'selftest', 'DY_Z_PARENT_H%d.npy' % H))
        for k, cid in zmap.items():
            nm = '%s_H%d' % (k, H)
            if nm not in res:
                continue
            r = res[nm]
            dy = np.load(O.P('tmp', 'selftest', 'DY_%s.npy' % nm)) if r['status'] == 'OK' else None
            md = maxabs(dy[:, :NE6O], par[:, :NE6O]) if dy is not None else float('inf')
            r['max_abs_diff'] = md
            rows.append(dict(check_id=cid, description='%s ≡ 同 H NATIVE 父（E6o 39 列；A4b_CVRv5 × HG10 × H%d；全程）' % (nm, H), exec_id='', value='',
                             max_abs_diff=md, tolerance=1e-9, status='PASS' if md <= 1e-9 else 'DIFFERS'))
    for nm in ('CKPT_MAIN_T1a', 'CKPT_D80_RENEW_COSTNET'):
        r = res[nm]
        ok = r['status'] == 'OK' and r['DY_maxabs'] == 0.0 and r['state_equal'] and r['hash_equal']
        rows.append(dict(check_id='CHECKPOINT_RESTORE_IDEMPOTENT', description='%s：中点 checkpoint → 恢复 → 续跑 vs 一次跑完（全部 DY 与状态数组逐位）' % nm,
                         exec_id='', value='', max_abs_diff=r.get('DY_maxabs', ''), tolerance=0.0, status='PASS' if ok else 'DIFFERS'))
    for nm, r in res.items():
        if r['status'] != 'OK':
            continue
        idn = r.get('ident')
        if not idn:
            continue
        rows.append(dict(check_id='CASH_EQUATION_SELFTEST', description='%s：nav_post = nav_pre − fee；NAV 伸缩；错误码 0；现金非负' % nm, exec_id='', value=idn['err'],
                         max_abs_diff=max(idn['nav_identity_maxabs'], idn['telescope_abs']), tolerance=1e-6,
                         status='PASS' if idn['err'] == 0 and idn['nav_identity_maxabs'] <= 1e-6 and idn['telescope_abs'] <= 1e-6 and idn['min_cash_share'] >= -1e-9 else 'DIFFERS'))
    I = pd.DataFrame(rows)
    O.atomic_write_csv(O.P('verify', 'selftest_identities_E6p.csv'), I)
    out = dict(T=G['mk'].T, wall_s=round(time.time() - t0, 1), n_tasks=len(res), failed=[k for k, v in res.items() if v['status'] != 'OK'],
               n_identity_rows=len(I), n_identity_bad=int((I.status != 'PASS').sum()), results=res)
    O.atomic_write_json(O.P('verify', 'selftest_E6p.json'), json.loads(json.dumps(out, default=float)))
    O.write_receipt('E6p_selftest', [O.P('verify', 'selftest_identities_E6p.csv'), O.P('verify', 'selftest_E6p.json')], code=[__file__, E.__file__, A.__file__, O.__file__],
                    n_tasks=len(res), n_identity_bad=out['n_identity_bad'], wall_s=out['wall_s'])
    print(json.dumps(dict(wall_s=out['wall_s'], failed=out['failed'], n_identity_rows=len(I), n_identity_bad=out['n_identity_bad']), ensure_ascii=False), flush=True)
    print(I[I.status != 'PASS'].to_string()[:3000], flush=True)
    if out['failed']:
        for k in out['failed']:
            print(k, res[k].get('err'), res[k].get('tb', '')[-600:], flush=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
