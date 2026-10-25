# -*- coding: utf-8 -*-
"""E6o 运行编排（brief §4；方式 B）。子命令：
  accounts --phase A2   全部 P_ACCOUNT + C_ACCOUNT 跑推导段 [2010-01-04, 2019-01-01)，存 checkpoint 与推导段日序列（不写任何后段数据）
  accounts --phase B    读 seal_A2（不在即拒绝）→ 各账户从 checkpoint 续跑至 2026-03-27，写全程日序列
  shadow   --phase A2|B 主母体 × 3 记忆 × 4 主触发的父影子风险集（BERNOULLI_LAG60 概率）
  randoms  --phase A2|B 随机 / 水平控制路径（brief §6 覆盖表；seed = stable(E6o, 机制, 路径序号)；路径各自递推状态）；
                        A2 只跑推导段；B 整段重放（推导段与 A2 逐位一致由 C 节核）；主母体 AMOUNT_MATCH 按 MCSE ≤ .01 增补至 ≤ 1024
并发：fork 池（--workers），父进程先加载 mmap 市场输入与形成名单并预编译，子进程共享；不写同 ID 文件。"""
import os
import sys
import json
import time
import argparse
import resource
import traceback
from multiprocessing import get_context

import numpy as np
import pandas as pd

import e6o_core as O
import e6o_engine as E
import e6o_acct as A

G = {}
TRIG_MODE = {'PANEL': E.TM_PANEL, 'T1C': E.TM_T1C, 'T1D': E.TM_T1D, 'T2': E.TM_T2, 'T2P': E.TM_T2P, 'T6A': E.TM_T6A, 'T6B': E.TM_T6B, 'NONE': E.TM_NONE}
FUND = {'NATIVE': E.FD_NATIVE, 'CASH': E.FD_CASH, 'NEXT': E.FD_NEXT, 'NONE': E.FD_NONE}
REM = {'ALLOW': E.RE_ALLOW, 'BLOCK': E.RE_BLOCK, 'RECONFIRM': E.RE_RECONFIRM}
GUARD = {'NONE': E.GD_OFF, 'T1A': E.GD_T1A, 'LVL': E.GD_LVL, 'RANDOM': E.GD_RANDOM}
RECON = {'NONE': E.RC_NONE, 'T1A': E.RC_T1A, 'LVL': E.RC_LVL}
SEL = {'AMOUNT_MATCH': E.SM_AMOUNT, 'RECONFIRM_RANDOM': E.SM_AMOUNT, 'COUNT_IID': E.SM_COUNT, 'COUNT_ISK': E.SM_ISK, 'LEVEL_WORST_1D': E.SM_LEVEL,
       'BERNOULLI_LAG60': E.SM_BERN, 'RE_ELIGIBILITY_MATCH': E.SM_REELIG, 'ENTRY_RANDOM': E.SM_REAL}


def d19():
    return int(np.searchsorted(G['mk'].dates, '2019-01-01'))


def plan():
    P = pd.read_csv(O.P('registration', 'run_plan_E6o.csv'), keep_default_na=False, na_values=[''])
    R = pd.read_csv(O.P('registration', 'registry_E6o.csv'), keep_default_na=False, na_values=[''])
    P = P.merge(R[['exec_id', 'exec_hash', 'parent_exec_id', 'family', 'trigger']], on='exec_id', how='left')
    return P


def setup():
    mk = A.Market()
    G['mk'] = mk
    G['f'] = {(f, m): mk.formation(f, m) for f in O.FORMS for m in O.MEMS}
    G['u'] = {f: mk.gate_u(f) for f in O.FORMS}
    G['n'] = {m: mk.next_order(m) for m in O.MEMS}
    # 预编译（父进程编译一次，fork 子进程共享）
    ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True)
    a = A.Account(mk, ip, fp, 'T1b', G['f'][(O.MAIN_FORM, 'HG10')], u_csr=G['u'][O.MAIN_FORM], lcap=1 << 14, incap=1 << 16)
    a.run(0, 40)
    ip2, fp2 = A.ip_fp(5, E.TM_NONE, fund=E.FD_NONE)
    A.Account(mk, ip2, fp2, None, G['f'][(O.MAIN_FORM, 'HG10')], lcap=1 << 14, incap=1 << 16).run(0, 40)


def make_account(p, sel=E.SM_REAL, seed=0, shadow=False, guard=None, targets=None):
    mk = G['mk']
    H = int(p['H'])
    ip, fp = A.ip_fp(H, TRIG_MODE[p['trig_mode']], sel=sel, fund=FUND[p['fund']], lag=int(p['lag']), maturity=int(p['maturity']),
                     reentry=REM[p['reentry']], guard=GUARD[guard or p['guard']], exit_on=bool(int(p['exit_on'])) or False, ideal=bool(int(p['ideal'])),
                     recon=RECON[p['recon']], seed=seed, shadow=shadow)
    tp = p['trig_panel'] if isinstance(p['trig_panel'], str) and p['trig_panel'] else None
    lcap = 1 << 15 if H <= 5 else (1 << 16 if H <= 10 else 1 << 17)
    return A.Account(mk, ip, fp, tp, G['f'][(p['form'], p['memory'])], u_csr=G['u'][p['form']], n_csr=G['n'][p['memory']], targets=targets, lcap=lcap)


def acct_path(phase, h):
    sub = 'deriv' if phase == 'A2' else 'full'
    d = O.P('accounts_run', sub, h[:2])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, '%s.npz' % h)


def ckpt_path(h):
    d = O.P('checkpoints', 'A2_end', h[:2])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, '%s.npz' % h)


def save_account(path, acc, meta):
    n = int(acc.S_i[E.SI_NIN])
    O.atomic_write_npz(path, DY=acc.DY, IN_i=acc.IN_i[:n], IN_f=acc.IN_f[:n], S_i=acc.S_i, S_f=acc.S_f, HOLDH=acc.HOLDH, RISK=acc.RISK,
                       meta=np.array([json.dumps(meta, sort_keys=True)]))


def job_account(args):
    phase, p = args
    t0 = time.time()
    try:
        h = p['exec_hash']
        acc = make_account(p)
        dA = d19()
        T = G['mk'].T
        if phase == 'A2':
            acc.run(0, dA)
            acc.checkpoint(ckpt_path(h), dict(exec_id=p['exec_id'], phase='A2_end', day=dA))
            save_account(acct_path('A2', h), acc, dict(exec_id=p['exec_id'], exec_hash=h, phase='A2', d0=0, d1=dA, written_at=time.strftime('%Y-%m-%d %H:%M:%S')))
        else:
            acc.restore(ckpt_path(h))
            acc.run(dA, T)
            save_account(acct_path('B', h), acc, dict(exec_id=p['exec_id'], exec_hash=h, phase='B', d0=0, d1=T, restored_from='A2_end', written_at=time.strftime('%Y-%m-%d %H:%M:%S')))
        return dict(exec_id=p['exec_id'], exec_hash=h, status='OK', wall_s=round(time.time() - t0, 2), n_intents=int(acc.S_i[E.SI_NIN]))
    except Exception as e:
        return dict(exec_id=p['exec_id'], exec_hash=p.get('exec_hash', ''), status='FAILED', wall_s=round(time.time() - t0, 2), err='%s: %s' % (type(e).__name__, str(e)[:300]),
                    tb=traceback.format_exc()[-800:])


def gate_post(what):
    if not os.path.exists(O.P('registration', 'seal_A2.json')):
        raise RuntimeError('%s：seal_A2.json 不在，拒绝写后段' % what)


def cmd_accounts(a):
    setup()
    P = plan()
    P = P[P.series.isin(['P_ACCOUNT', 'C_ACCOUNT'])]
    if a.only:
        P = P[P.exec_id.isin(open(a.only).read().split('\n'))]
    if a.phase == 'B':
        gate_post('accounts B')
    # 先父后子；同类按 H 降序（长 H 慢）
    P = P.assign(_o=(P.series == 'C_ACCOUNT').astype(int) * 10 - P.H.astype(int) / 100.0).sort_values('_o')
    jobs = [(a.phase, r._asdict()) for r in P.drop(columns=['_o']).itertuples(index=False)]
    t0 = time.time()
    rows = []
    ctx = get_context('fork')
    with ctx.Pool(a.workers) as pool:
        for i, r in enumerate(pool.imap_unordered(job_account, jobs, chunksize=1)):
            rows.append(r)
            if (i + 1) % 100 == 0 or r['status'] != 'OK':
                O.log('accounts %s %d/%d %s %s' % (a.phase, i + 1, len(jobs), r['status'], r.get('err', '')))
    D = pd.DataFrame(rows)
    p = O.P('task_status', 'accounts_%s.csv' % a.phase)
    O.atomic_write_csv(p, D.drop(columns=[c for c in ('tb',) if c in D.columns]))
    O.write_receipt('E6o_accounts_%s' % a.phase, [p], code=[__file__, E.__file__, A.__file__], n=len(D), failed=int((D.status != 'OK').sum()),
                    wall_s=round(time.time() - t0, 1), rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.log('accounts %s 完成：%d 个，失败 %d，%.0f s' % (a.phase, len(D), int((D.status != 'OK').sum()), time.time() - t0))
    if (D.status != 'OK').any():
        print(D[D.status != 'OK'].head(5).to_string(), flush=True)
        sys.exit(1)


# ------------------------------------------------------------------ 影子风险集（BERNOULLI_LAG60）
def shadow_path(phase, h):
    d = O.P('accounts_run', 'shadow_' + ('deriv' if phase == 'A2' else 'full'))
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, '%s.npz' % h)


def job_shadow(args):
    phase, p = args
    try:
        q = dict(p)
        q['exit_on'] = 0
        acc = make_account(q, shadow=True)
        d1 = d19() if phase == 'A2' else G['mk'].T
        acc.run(0, d1)
        n = int(acc.S_i[E.SI_NIN])
        O.atomic_write_npz(shadow_path(phase, p['exec_hash']), IN_i=acc.IN_i[:n], IN_f=acc.IN_f[:n], RISK=acc.RISK, meta=np.array([json.dumps(dict(owner=p['exec_id'], phase=phase))]))
        return dict(exec_id=p['exec_id'], status='OK', hits=n)
    except Exception as e:
        return dict(exec_id=p['exec_id'], status='FAILED', err='%s: %s' % (type(e).__name__, str(e)[:300]))


def bern_prob(phase, h, T, NL):
    z = np.load(shadow_path(phase, h), allow_pickle=False)
    IN_i = z['IN_i']
    hits = np.zeros((T, NL))
    m = IN_i[:, E.IN_STATUS] == 9
    np.add.at(hits, (IN_i[m, E.IN_DAY], IN_i[m, E.IN_LAYER]), 1.0)
    risk = z['RISK'][:, :NL].astype(float)
    ch = np.vstack([np.zeros((1, NL)), np.cumsum(hits, 0)])
    cr = np.vstack([np.zeros((1, NL)), np.cumsum(risk, 0)])
    cv = np.vstack([np.zeros((1, NL)), np.cumsum((risk > 0).astype(float), 0)])
    p = np.full((T, NL), np.nan)
    for d in range(T):
        lo = max(0, d - 60)
        nv = cv[d] - cv[lo]
        den = cr[d] - cr[lo]
        ok = (nv >= 20) & (den > 0)
        p[d, ok] = (ch[d, ok] - ch[lo, ok]) / den[ok]
    return p


# ------------------------------------------------------------------ 随机 / 水平控制
def owner_targets(phase, p, mech):
    """真账户（owner）T 收盘意向目标（只用 owner 自己的 T 收盘已知量；plan §8.2）。"""
    mk = G['mk']
    T = mk.T
    H = int(p['H'])
    z = np.load(acct_path(phase, p['exec_hash']), allow_pickle=False)
    IN_i, IN_f, DY = z['IN_i'], z['IN_f'], z['DY']
    real = IN_i[:, E.IN_STATUS] != 9
    day, sec, lay, isk, re_ = IN_i[real, E.IN_DAY], IN_i[real, E.IN_SEC], IN_i[real, E.IN_LAYER], IN_i[real, E.IN_ISK], IN_i[real, E.IN_RE]
    val = IN_f[real, 0]
    tg = {}
    amt = np.zeros((T, max(H, 4)))
    np.add.at(amt, (day, lay), val)
    tg['amt'] = amt
    # 唯一证券：主本金意向批次定层
    if len(day):
        df = pd.DataFrame(dict(day=day, sec=sec, lay=lay, isk=isk, val=val))
        dom = df.sort_values(['day', 'sec', 'val'], ascending=[True, True, False]).drop_duplicates(['day', 'sec'])
        cnt = np.zeros((T, H), np.int64)
        np.add.at(cnt, (dom.day.to_numpy(), dom.lay.to_numpy()), 1)
        tg['cnt'] = cnt
        isk_n = mk.n_isk * H
        ik = np.zeros((T, isk_n), np.int64)
        ok = dom.isk.to_numpy() >= 0
        np.add.at(ik, (dom.day.to_numpy()[ok], dom.isk.to_numpy()[ok] * H + dom.lay.to_numpy()[ok]), 1)
        tg['isk'] = ik
    else:
        tg['cnt'] = np.zeros((T, H), np.int64)
        tg['isk'] = np.zeros((T, mk.n_isk * H), np.int64)
    rr = np.zeros((T, 4))
    np.add.at(rr, (day, np.clip(re_, 0, 3)), val)
    tg['re'] = rr
    tg['cancel'] = DY[:, E.DYI['cancel_val']].copy()
    if mech == 'BERNOULLI_LAG60':
        tg['bern'] = bern_prob(phase, p['exec_hash'], T, H)
    return tg, float(val.sum()), float(DY[:, E.DYI['cancel_val']].sum())


def seg_D(ne, pne, dates_seg, mask_days):
    out = {}
    for s in list(O.SEGS) + ['2013-2014']:
        m = mask_days[s]
        x = ne[m] - pne[m]
        ok = np.isfinite(x)
        out[s] = (float(np.mean(x[ok]) * O.ANN_PP) if ok.any() else np.nan, int(ok.sum()))
    return out


_CACHE = {}


def job_random(args):
    phase, p, parent_h, mech, paths = args
    mk = G['mk']
    T = mk.T
    d1 = d19() if phase == 'A2' else T
    rows = []
    try:
        key = (phase, p['exec_hash'], mech)
        if key not in _CACHE:
            _CACHE.clear()
            _CACHE[key] = owner_targets(phase, p, mech)
        tg, tot_amt, tot_cancel = _CACHE[key]
        pk = ('P', phase, parent_h)
        if pk not in _CACHE:
            _CACHE[pk] = np.load(acct_path(phase, parent_h), allow_pickle=False)['DY'][:, E.DYI['net_excess']]
        pne = _CACHE[pk]
        masks = G['segmask']
        for path in paths:
            seed = O.stable_u64('E6o', mech, path) & ((1 << 62) - 1)
            guard = 'RANDOM' if mech == 'ENTRY_RANDOM' else None
            acc = make_account(p, sel=SEL[mech], seed=seed, guard=guard, targets=tg)
            acc.run(0, d1)
            ne = acc.DY[:, E.DYI['net_excess']]
            Dm = {}
            for s in list(O.SEGS) + ['2013-2014']:
                m = masks[s].copy()
                m[d1:] = False
                x = ne[m] - pne[m]
                ok = np.isfinite(x)
                Dm[s] = (float(np.mean(x[ok]) * O.ANN_PP) if ok.any() else np.nan, int(ok.sum()))
            um = acc.DY[:d1, E.DYI['unmatched_val']]
            row = dict(owner_exec_id=p['exec_id'], mechanism=mech, path_id=int(path), seed=int(seed), phase=phase, n_unmatched_days=int((um > 0).sum()),
                       unmatched_amt=float(um.sum()), target_amt=tot_amt if mech != 'ENTRY_RANDOM' else tot_cancel, n_intents=int(acc.S_i[E.SI_NIN]))
            for s, (v, n) in Dm.items():
                row['D_%s' % s] = v
                row['n_%s' % s] = n
            rows.append(row)
        return rows
    except Exception as e:
        return [dict(owner_exec_id=p['exec_id'], mechanism=mech, path_id=-1, phase=phase, status='FAILED', err='%s: %s' % (type(e).__name__, str(e)[:300]),
                     tb=traceback.format_exc()[-600:])]


def segmasks():
    mk = G['mk']
    segi = np.array([O.seg_of_date(d) for d in mk.dates])
    m = {s: segi == s for s in O.SEGS}
    m['2013-2014'] = (mk.dates >= O.MINUTE_START) & (segi == '2010-2014')
    return m


def cmd_shadow(a):
    setup()
    if a.phase == 'B':
        gate_post('shadow B')
    P = plan().set_index('exec_id', drop=False)
    RS = pd.read_csv(O.P('registration', 'random_scope_E6o.csv'), keep_default_na=False)
    owners = RS[RS.mechanism == 'BERNOULLI_LAG60'].owner_exec_id.unique()
    jobs = [(a.phase, P.loc[e].to_dict()) for e in owners]
    ctx = get_context('fork')
    with ctx.Pool(min(a.workers, len(jobs))) as pool:
        res = list(pool.imap_unordered(job_shadow, jobs))
    D = pd.DataFrame(res)
    O.atomic_write_csv(O.P('task_status', 'shadow_%s.csv' % a.phase), D)
    O.log('shadow %s：%d，失败 %d' % (a.phase, len(D), int((D.status != 'OK').sum())))
    if (D.status != 'OK').any():
        print(D[D.status != 'OK'].to_string(), flush=True)
        sys.exit(1)


def cmd_randoms(a):
    setup()
    if a.phase == 'B':
        gate_post('randoms B')
    G['segmask'] = segmasks()
    P = plan().set_index('exec_id', drop=False)
    RS = pd.read_csv(O.P('registration', 'random_scope_E6o.csv'), keep_default_na=False)
    if a.mechs:
        RS = RS[RS.mechanism.isin(a.mechs.split(','))]
    batch = a.batch
    jobs = []
    for r in RS.itertuples():
        p = P.loc[r.owner_exec_id].to_dict()
        n0 = int(r.paths) if not a.path_range else int(a.path_range.split(':')[1])
        s0 = 0 if not a.path_range else int(a.path_range.split(':')[0])
        if a.path_range and r.mechanism != 'AMOUNT_MATCH':
            continue
        for b0 in range(s0, n0, batch):
            jobs.append((a.phase, p, p['parent_exec_id'] and P.loc[p['parent_exec_id']]['exec_hash'], r.mechanism, list(range(b0, min(n0, b0 + batch)))))
    if a.owners:
        keep = set(open(a.owners).read().split('\n'))
        jobs = [j for j in jobs if j[1]['exec_id'] in keep]
    # 同 owner 的批次相邻（进程内缓存目标）
    jobs.sort(key=lambda j: (j[1]['exec_hash'], j[3], j[4][0]))
    t0 = time.time()
    rows = []
    ctx = get_context('fork')
    with ctx.Pool(a.workers) as pool:
        for i, r in enumerate(pool.imap(job_random, jobs, chunksize=1)):
            rows.extend(r)
            if (i + 1) % 500 == 0:
                O.log('randoms %s %d/%d 批（%.0f s）' % (a.phase, i + 1, len(jobs), time.time() - t0))
    D = pd.DataFrame(rows)
    tag = a.tag or a.phase
    p = O.P('randoms', 'random_paths_%s.csv' % tag)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    O.atomic_write_csv(p, D.drop(columns=[c for c in ('tb',) if c in D.columns]))
    nf = int((D.get('status', pd.Series(dtype=str)) == 'FAILED').sum()) if 'status' in D else 0
    O.write_receipt('E6o_randoms_%s' % tag, [p], code=[__file__, E.__file__, A.__file__], rows=len(D), failed=nf, wall_s=round(time.time() - t0, 1),
                    rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.log('randoms %s 完成：%d 行，失败 %d，%.0f s' % (tag, len(D), nf, time.time() - t0))
    if nf:
        print(D[D.get('status') == 'FAILED'].head(5).to_string(), flush=True)
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['accounts', 'shadow', 'randoms'])
    ap.add_argument('--phase', choices=['A2', 'B'], required=True)
    ap.add_argument('--workers', type=int, default=64)
    ap.add_argument('--only', default='')
    ap.add_argument('--mechs', default='')
    ap.add_argument('--batch', type=int, default=16)
    ap.add_argument('--path_range', default='')
    ap.add_argument('--owners', default='')
    ap.add_argument('--tag', default='')
    a = ap.parse_args()
    if a.cmd == 'accounts':
        cmd_accounts(a)
    elif a.cmd == 'shadow':
        cmd_shadow(a)
    else:
        cmd_randoms(a)


if __name__ == '__main__':
    main()
