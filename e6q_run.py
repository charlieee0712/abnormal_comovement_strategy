# -*- coding: utf-8 -*-
"""E6q 运行编排（brief §4 / §6；方式 B）。子命令：
  accounts --phase A2|B  registry 全部 201 个执行对象（全部记成交日志）：A2 跑推导段 [0, d19) 存 checkpoint / 日序列 / 意向 / 成交分片；
                         B 读 seal_A2（不在即拒绝）→ 从 checkpoint 续跑到 2026-03-27（连续全历史主口径；跨段不重置）
  feedback --phase A2|B  成本反馈 80 路径（cost_feedback_refs；A0 ∈ {1, 5} 亿、κ .5、δ .5；冲击费实扣现金），同 checkpoint 链
  warm     --phase A2|B  四段重置敏感性（primary32 + 其同臂父 + H5 全局父；不进 registry；A2 只跑两推导段）
  shadow   --phase A2|B  BERNOULLI_FIRSTHIT 影子：每个 (form, memory, H, scenario, trigger) 的无退出父影子（fhit：首次已知 True / 风险要求次日执行 < due）
  randoms  --phase A2|B  随机与目标控制（random_control_refs 568 条）：128 起（LEVEL_WORST_1D 1 条）；A2 只跑推导段；B 从 0 日整段重放；B 另存全部路径日统计
  topup    --phase B     主形态 HG10 owner × 六机制按 MCSE ≤ .01 以 128 批增补至 1,024（达上限记 MC_LIMIT）
随机种子 = stable(E6q, owner 逻辑 ID, 机制, 路径序号)；路径各自递推（不共享 token / 现金 / 状态）；随机路径施加与 owner 同一种臂 wrapper（M3 门 / M4 半量 / M1 / M2 资金）。
并发：fork 池，父进程先加载 mmap 与形成名单并预编译。"""
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

import e6q_core as O
import e6q_engine as E
import e6q_acct as A

G = {}
PH = {'A2': 'deriv', 'B': 'full'}
CH_DAYS = 400
TLCAP = 1 << 20
MECH = {'AMOUNT_MATCH_V2': (E.SM_AMT2, E.RT_NONE), 'COUNT_ISK': (E.SM_ISK2, E.RT_NONE), 'AMOUNT_ISK_V2': (E.SM_AISK2, E.RT_NONE),
        'BERNOULLI_FIRSTHIT': (E.SM_BERN, E.RT_NONE), 'LEVEL_WORST_1D': (E.SM_LVL2, E.RT_NONE),
        'RANDOM_TARGET_WITHIN_ARM': (E.SM_REAL, E.RT_WITHIN), 'RANDOM_TARGET_SOURCE_DOMAIN': (E.SM_REAL, E.RT_SOURCE)}
TOPUP_MECHS = ('AMOUNT_MATCH_V2', 'COUNT_ISK', 'AMOUNT_ISK_V2', 'BERNOULLI_FIRSTHIT', 'RANDOM_TARGET_WITHIN_ARM', 'RANDOM_TARGET_SOURCE_DOMAIN')
MCSE_TARGET = 0.01
MAX_PATHS = 1024
DCOLS = ('ne', 'feefr', 'expo', 'cash', 'turn', 's05', 's07', 's10', 'req', 'unm', 'rtst', 'rtshort', 'nint', 'xplan', 'tkt')


def d19():
    return int(np.searchsorted(G['mk'].dates, '2019-01-01'))


def d_end(phase):
    return d19() if phase == 'A2' else G['mk'].T


def registry():
    return O.read_csv(O.P('registration', 'registry_E6q.csv'), dtype=str)


def gate(phase, what):
    if not os.path.exists(O.P('registration', 'freeze_E6q.json')):
        raise RuntimeError('%s：freeze_E6q.json 不在（A1 未冻结），拒绝运行' % what)
    if phase == 'B' and not os.path.exists(O.P('registration', 'seal_A2.json')):
        raise RuntimeError('%s：seal_A2.json 不在，拒绝写后段' % what)


def setup():
    mk = A.Market()
    G['mk'] = mk
    G['f'] = {(f, m): mk.formation(f, m) for f in O.FORMS for m in O.MEMS if (f == O.MAIN_FORM or m == 'HG10')}
    G['segi'] = np.array([O.seg_of_date(d) for d in mk.dates])
    for arm in ('NATIVE', 'REINVEST_LIQ_1E8', 'EXIT_GATE_LIQ_5E8', 'EXIT_HALF_REARM'):
        row = dict(form=O.MAIN_FORM, memory='HG10', H=20, arm=arm, trigger='T1a', scenario='FEASIBLE_DAILY')
        ip, fp, tn = A.spec_params(row, tlog=True)
        A.Account(mk, ip, fp, tn, G['f'][(O.MAIN_FORM, 'HG10')], lcap=1 << 14, incap=1 << 16, tlcap=1 << 16).run(0, 30)
    for sel in (E.SM_AMT2, E.SM_ISK2, E.SM_BERN, E.SM_LVL2, E.SM_AISK2):
        row = dict(form=O.MAIN_FORM, memory='HG10', H=20, arm='NATIVE', trigger='T1a', scenario='FEASIBLE_DAILY')
        ip, fp, tn = A.spec_params(row, sel=sel, seed=1, fhit=1 if sel == E.SM_BERN else 0)
        tg = dict(b=np.zeros((mk.T, E.NB)), isk2=np.zeros((mk.T, mk.n_isk * E.NB)), aisk=np.zeros((mk.T, mk.n_isk * E.NB)), bern=np.zeros((mk.T, 20)))
        A.Account(mk, ip, fp, tn, G['f'][(O.MAIN_FORM, 'HG10')], targets=tg, lcap=1 << 14, incap=1 << 16).run(0, 30)


# ------------------------------------------------------------------ 路径
def res_path(phase, h, kind='acct'):
    sub = {'acct': PH[phase], 'fb': PH[phase] + '_fb', 'shadow': 'shadow_' + PH[phase], 'warm': 'warm'}[kind]
    d = O.P('accounts_run', sub, h[:2])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, '%s.npz' % h)


def ckpt_path(h):
    d = O.P('checkpoints', 'A2_end', h[:2])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, '%s.npz' % h)


def trade_path(phase, h):
    d = O.P('trades_parts', PH[phase], h[:2])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, '%s.npz' % h)


def fb_hash(exec_id, A_cny):
    return O.sha_bytes(('%s|FEEDBACK|%d|0.5|0.5' % (exec_id, int(A_cny))).encode())[:16]


def shadow_key(row):
    return O.sha_bytes(('SHADOW|%s|%s|%s|%s|%s' % (row['form'], row['memory'], row['H'], row['scenario'], row['trigger'])).encode())[:16]


# ------------------------------------------------------------------ 账户
def build(row, sel=E.SM_REAL, seed=0, shadow=False, feedback=None, targets=None, tlog=False, start=0, rt=E.RT_NONE, fhit=0):
    mk = G['mk']
    ip, fp, trig = A.spec_params(row, sel=sel, seed=seed, shadow=shadow, tlog=tlog, feedback=feedback, rt=rt, fhit=fhit)
    return A.Account(mk, ip, fp, trig, G['f'][(row['form'], row['memory'])], targets=targets, tlcap=TLCAP if tlog else 0, start=start)


def run_flush(acc, d0, d1, sink):
    d = d0
    while d < d1:
        e = min(d1, d + CH_DAYS)
        acc.run(d, e)
        n = int(acc.S_i[E.SI_NTL])
        if n and sink is not None:
            sink.append((acc.TL_i[:n].copy(), acc.TL_f[:n].copy()))
            acc.S_i[E.SI_NTL] = 0
        d = e


def save_result(path, acc, meta, n_days, final_lots=False):
    n = int(acc.S_i[E.SI_NIN])
    arr = dict(DY=acc.DY[:n_days], IN_i=acc.IN_i[:n], IN_f=acc.IN_f[:n], S_i=acc.S_i, S_f=acc.S_f, HOLDH=acc.HOLDH, LOTH=acc.LOTH,
               meta=np.array([json.dumps(meta, sort_keys=True)]))
    if final_lots:
        nl = int(acc.S_i[E.SI_NL])
        arr.update(L_i=acc.L_i[:nl], L_f=acc.L_f[:nl], L_id=acc.L_id[:nl])
    O.atomic_write_npz(path, **arr)


def save_trades(path, sink):
    if sink:
        ti = np.concatenate([s[0] for s in sink])
        tf = np.concatenate([s[1] for s in sink])
    else:
        ti = np.zeros((0, E.NTLI), np.int64)
        tf = np.zeros((0, E.NTLF))
    O.atomic_write_npz(path, TL_i=ti, TL_f=tf)
    return len(ti)


def job_account(args):
    phase, row, kind, extra = args
    t0 = time.time()
    try:
        h = row['exec_hash'] if kind == 'acct' else extra['hash']
        tlog = kind == 'acct'
        fb = (float(extra['A']), 0.5, 0.5) if kind == 'fb' else None
        acc = build(row, tlog=tlog, feedback=fb)
        dA, T = d19(), G['mk'].T
        sink = [] if tlog else None
        meta = dict(exec_id=row['exec_id'], exec_hash=row['exec_hash'], kind=kind, phase=phase, feedback_A=extra.get('A', '') if extra else '',
                    written_at=time.strftime('%Y-%m-%d %H:%M:%S'), code_sha256=O.sha_file(E.__file__))
        ck = ckpt_path(h)
        if phase == 'A2':
            run_flush(acc, 0, dA, sink)
            acc.checkpoint(ck, dict(meta, day=dA))
            save_result(res_path('A2', h, kind), acc, dict(meta, d0=0, d1=dA), dA)
        else:
            acc.restore(ck)
            run_flush(acc, dA, T, sink)
            save_result(res_path('B', h, kind), acc, dict(meta, d0=0, d1=T, restored_from='A2_end'), T, final_lots=True)
        ntr = save_trades(trade_path(phase, h), sink) if tlog else 0
        return dict(exec_id=row['exec_id'], hash=h, kind=kind, status='OK', wall_s=round(time.time() - t0, 2), n_intents=int(acc.S_i[E.SI_NIN]),
                    n_trades=ntr, rndfix=int(acc.S_i[E.SI_RNDFIX]), err=int(acc.S_i[E.SI_ERR]), rt_limit=int(acc.S_i[E.SI_RTLIM]),
                    deny=int(acc.S_i[E.SI_DENY]), quar=int(acc.S_i[E.SI_QUAR]), override=int(acc.S_i[E.SI_OVERRIDE]), half=int(acc.S_i[E.SI_HALF]),
                    rearm=int(acc.S_i[E.SI_REARMN]), fallback=int(acc.S_i[E.SI_FALLBACK]), new_empty=int(acc.S_i[E.SI_NEWEMPTY]))
    except Exception as e:
        return dict(exec_id=row['exec_id'], kind=kind, status='FAILED', wall_s=round(time.time() - t0, 2), err='%s: %s' % (type(e).__name__, str(e)[:300]),
                    tb=traceback.format_exc()[-900:])


def pool_run(fn, jobs, workers, label, chunksize=1, ordered=False):
    t0 = time.time()
    out = []
    ctx = get_context('fork')
    with ctx.Pool(min(workers, max(1, len(jobs)))) as pool:
        it = pool.imap(fn, jobs, chunksize=chunksize) if ordered else pool.imap_unordered(fn, jobs, chunksize=chunksize)
        for i, r in enumerate(it):
            if isinstance(r, list):
                out.extend(r)
                bad = [x for x in r if x.get('status') == 'FAILED']
            else:
                out.append(r)
                bad = [r] if r.get('status') == 'FAILED' else []
            for b in bad[:1]:
                O.log('%s FAILED %s %s' % (label, b.get('exec_id', b.get('owner_exec_id', '')), b.get('err', '')))
            if (i + 1) % 200 == 0:
                O.log('%s %d/%d（%.0f s）' % (label, i + 1, len(jobs), time.time() - t0))
    return out, time.time() - t0


def finish(label, rows, wall, outname, code=()):
    D = pd.DataFrame(rows)
    p = O.P('task_status', outname)
    O.atomic_write_csv(p, D.drop(columns=[c for c in ('tb',) if c in D.columns]))
    nf = int((D.status == 'FAILED').sum()) if 'status' in D else 0
    O.write_receipt('E6q_%s' % outname.replace('.csv', ''), [p], code=[__file__, E.__file__, A.__file__] + list(code), n=len(D), failed=nf, wall_s=round(wall, 1),
                    rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.log('%s 完成：%d 行，失败 %d，%.0f s' % (label, len(D), nf, wall))
    if nf:
        print(D[D.status == 'FAILED'].head(5).to_string()[:3000], flush=True)
        sys.exit(1)
    return D


def cmd_accounts(a):
    gate(a.phase, 'accounts')
    setup()
    R = G['R'] = registry()
    if a.only:
        keep = set(open(a.only).read().split())
        R = R[R.exec_hash.isin(keep) | R.exec_id.isin(keep)]
    R = R.assign(_o=-R.H.astype(int)).sort_values('_o').drop(columns=['_o'])
    jobs = [(a.phase, r._asdict(), 'acct', {}) for r in R.itertuples(index=False)]
    out, w = pool_run(job_account, jobs, a.workers, 'accounts %s' % a.phase)
    finish('accounts %s' % a.phase, out, w, 'accounts_%s.csv' % a.phase)


def cmd_feedback(a):
    gate(a.phase, 'feedback')
    setup()
    R = G['R'] = registry()
    F = O.read_csv(O.P('registration', 'cost_feedback_refs_E6q.csv'), dtype=str)
    Rf = R.set_index('logical_id', drop=False)
    jobs = []
    for f in F.itertuples(index=False):
        row = Rf.loc[f.owner_logical_id].to_dict()
        jobs.append((a.phase, row, 'fb', dict(A=int(f.A0_cny), hash=fb_hash(row['exec_id'], int(f.A0_cny)), feedback_id=f.feedback_id)))
    out, w = pool_run(job_account, jobs, a.workers, 'feedback %s' % a.phase)
    for r, j in zip(sorted(out, key=lambda x: x.get('hash', '')), sorted(jobs, key=lambda x: x[3]['hash'])):
        pass
    finish('feedback %s' % a.phase, out, w, 'feedback_%s.csv' % a.phase)


def warm_rows():
    R = G['R']
    p32 = R[R.is_primary32 == '1']
    keep = set(p32.exec_id) | set(x for x in p32.parent_same_arm_exec_id if x) | set(x for x in p32.parent_h5_global_exec_id if x)
    return R[R.exec_id.isin(keep)]


def job_warm(args):
    phase, row, seg = args
    t0 = time.time()
    try:
        mk = G['mk']
        segi = G['segi']
        idx = np.flatnonzero(segi == seg)
        s0, s1 = int(idx[0]), int(idx[-1]) + 1
        acc = build(row, start=s0)
        acc.run(s0, s1)
        h = O.sha_bytes(('%s|WARM|%s' % (row['exec_id'], seg)).encode())[:16]
        O.atomic_write_npz(res_path(phase, h, 'warm'), DY=acc.DY[s0:s1], S_i=acc.S_i, d0=np.array([s0]), d1=np.array([s1]),
                           meta=np.array([json.dumps(dict(exec_id=row['exec_id'], start_state='WARM', segment=seg, d0=s0, d1=s1), sort_keys=True)]))
        return dict(exec_id=row['exec_id'], segment=seg, hash=h, status='OK', wall_s=round(time.time() - t0, 2), err=int(acc.S_i[E.SI_ERR]), n_days=s1 - s0,
                    dates=str(mk.dates[s0]) + '..' + str(mk.dates[s1 - 1]))
    except Exception as e:
        return dict(exec_id=row['exec_id'], segment=seg, status='FAILED', err='%s: %s' % (type(e).__name__, str(e)[:300]), tb=traceback.format_exc()[-900:])


def cmd_warm(a):
    gate(a.phase, 'warm')
    setup()
    G['R'] = registry()
    segs = O.DERIV_SEGS if a.phase == 'A2' else O.POST_SEGS
    jobs = [(a.phase, r._asdict(), s) for r in warm_rows().itertuples(index=False) for s in segs]
    out, w = pool_run(job_warm, jobs, a.workers, 'warm %s' % a.phase)
    finish('warm %s' % a.phase, out, w, 'warm_%s.csv' % a.phase)


# ------------------------------------------------------------------ 影子与随机
def shadow_rows():
    R = G['R']
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6q.csv'), dtype=str)
    owners = set(RR[RR.mechanism == 'BERNOULLI_FIRSTHIT'].owner_logical_id)
    S = {}
    for r in R[R.logical_id.isin(owners)].itertuples(index=False):
        k = shadow_key(r._asdict())
        if k not in S:
            S[k] = dict(form=r.form, memory=r.memory, H=r.H, arm='NATIVE', trigger=r.trigger, scenario=r.scenario, shadow_key=k)
    return S


def job_shadow(args):
    phase, row = args
    t0 = time.time()
    try:
        acc = build(row, shadow=True, fhit=1)
        acc.run(0, d_end(phase))
        O.atomic_write_npz(res_path(phase, row['shadow_key'], 'shadow'), HITS=acc.HITS, RISK=acc.RISK,
                           meta=np.array([json.dumps(dict(row, phase=phase), sort_keys=True)]))
        return dict(shadow_key=row['shadow_key'], trigger=row['trigger'], H=row['H'], form=row['form'], memory=row['memory'], status='OK',
                    hits=int(acc.HITS.sum()), risk=int(acc.RISK.sum()), wall_s=round(time.time() - t0, 2))
    except Exception as e:
        return dict(shadow_key=row.get('shadow_key', ''), status='FAILED', err='%s: %s' % (type(e).__name__, str(e)[:300]), tb=traceback.format_exc()[-900:])


def cmd_shadow(a):
    gate(a.phase, 'shadow')
    setup()
    G['R'] = registry()
    jobs = [(a.phase, r) for r in shadow_rows().values()]
    out, w = pool_run(job_shadow, jobs, a.workers, 'shadow %s' % a.phase)
    finish('shadow %s' % a.phase, out, w, 'shadow_%s.csv' % a.phase)


def bern_prob(phase, key, T, NL):
    """BERNOULLI_FIRSTHIT：影子在前 60 个交易日（严格不含 T）的首达风险率 hazard(日龄桶, H, trigger) = 首次事件 / 未首达且次日执行 < due 的有效 lot-day；
    桶 1 / 2 / 3–5 / 6–10 / 11–20 / 21+；桶内无风险分母 → 同 H 同 trigger 全龄池；仍无 → NaN（UNKNOWN，不抽）。零事件但有分母 = 合法零概率。"""
    z = np.load(res_path(phase, key, 'shadow'), allow_pickle=False)
    hits = z['HITS'][:, :NL].astype(float)
    risk = z['RISK'][:, :NL].astype(float)
    bk = np.array([E.bucket_of(l) for l in range(NL)], np.int64)
    hb = np.zeros((T, E.NB))
    rb = np.zeros((T, E.NB))
    for l in range(NL):
        hb[:, bk[l]] += hits[:, l]
        rb[:, bk[l]] += risk[:, l]
    ch = np.vstack([np.zeros((1, E.NB)), np.cumsum(hb, 0)])
    cr = np.vstack([np.zeros((1, E.NB)), np.cumsum(rb, 0)])
    p = np.full((T, NL), np.nan)
    for d in range(T):
        lo = max(0, d - 60)
        den = cr[d] - cr[lo]
        num = ch[d] - ch[lo]
        tot_den = den.sum()
        pool = num.sum() / tot_den if tot_den > 0 else np.nan
        hz = np.where(den > 0, num / np.where(den > 0, den, 1.0), pool)
        p[d] = hz[bk]
    return p


def owner_targets(phase, row, mech):
    """owner 在 T 收盘的意向目标（只用 owner 自己 T 收盘已知量；plan §8.1）：触发意向（KD_TRIG；预包装意向金额 = 批次全额）；BERNOULLI 用影子风险率。"""
    mk = G['mk']
    T = mk.T
    H = int(row['H'])
    NC = mk.n_isk * E.NB
    if mech == 'BERNOULLI_FIRSTHIT':
        return dict(bern=bern_prob(phase, shadow_key(row), T, H))
    if mech.startswith('RANDOM_TARGET'):
        return None
    z = np.load(res_path(phase, row['exec_hash']), allow_pickle=False)
    IN_i, IN_f = z['IN_i'], z['IN_f']
    m = IN_i[:, E.IN_KIND] == E.KD_TRIG
    day, sec, age, isk = IN_i[m, E.IN_DAY], IN_i[m, E.IN_SEC], IN_i[m, E.IN_AGE], IN_i[m, E.IN_ISK]
    val = IN_f[m, 0]
    bk = np.array([E.bucket_of(int(x)) for x in age], np.int64) if len(age) else np.zeros(0, np.int64)
    cell = np.where(isk >= 0, isk, 0).astype(np.int64)
    tg = {}
    if mech in ('AMOUNT_MATCH_V2', 'LEVEL_WORST_1D'):
        b = np.zeros((T, E.NB))
        np.add.at(b, (day, bk), val)
        tg['b'] = b
    elif mech == 'AMOUNT_ISK_V2':
        x = np.zeros((T, NC))
        np.add.at(x, (day, cell * E.NB + bk), val)
        tg['aisk'] = x
    elif mech == 'COUNT_ISK':
        x = np.zeros((T, NC))
        if len(day):
            df = pd.DataFrame(dict(day=day, sec=sec, val=val, bk=bk, cell=cell))
            dom = df.sort_values(['day', 'sec', 'val'], ascending=[True, True, False]).drop_duplicates(['day', 'sec'])
            np.add.at(x, (dom.day.to_numpy(), dom.cell.to_numpy() * E.NB + dom.bk.to_numpy()), 1.0)
        tg['isk2'] = x
    return tg


def seg_D(ne, pne, n_days):
    out = {}
    segi = G['segi']
    for s in O.SEGS:
        mm = (segi == s)[:n_days]
        x = ne[mm] - pne[mm]
        ok = np.isfinite(x)
        out[s] = (float(np.mean(x[ok]) * O.ANN_PP) if ok.any() else np.nan, int(ok.sum()))
    return out


_CACHE = {}


def job_random(args):
    phase, row, parent_h, mech, paths = args
    n_days = d_end(phase)
    rows = []
    try:
        key = (phase, row['exec_hash'], mech)
        if key not in _CACHE:
            _CACHE.clear()
            _CACHE[key] = owner_targets(phase, row, mech)
            _CACHE[('P', phase, parent_h)] = np.load(res_path(phase, parent_h), allow_pickle=False)['DY'][:, E.DYI['net_excess']]
            z = np.load(res_path(phase, row['exec_hash']), allow_pickle=False)
            _CACHE[('O', phase, row['exec_hash'])] = (z['IN_i'], z['IN_f'])
        tg = _CACHE[key]
        pne = _CACHE[('P', phase, parent_h)]
        oin, oif = _CACHE[('O', phase, row['exec_hash'])]
        segi = G['segi']
        sel, rt = MECH[mech]
        fhit = 1 if mech == 'BERNOULLI_FIRSTHIT' else 0
        daily = {k: [] for k in DCOLS} if phase == 'B' else None
        okind = oin[:, E.IN_KIND] == E.KD_TRIG
        o_day = oin[okind, E.IN_DAY]
        o_val = oif[okind, 0]
        o_sec = oin[okind, E.IN_SEC]
        for path in paths:
            seed = O.stable_u64('E6q', row['logical_id'], mech, path) & ((1 << 62) - 1)
            acc = build(row, sel=sel, seed=seed, targets=tg, rt=rt, fhit=fhit)
            acc.run(0, n_days)
            DY = acc.DY[:n_days]
            ne = DY[:, E.DYI['net_excess']]
            Dm = seg_D(ne, pne[:n_days], n_days)
            unm = DY[:, E.DYI['v2_unm']]
            umf = unm > np.maximum(1.0, 1e-6 * DY[:, E.DYI['v2_req']])
            nin = int(acc.S_i[E.SI_NIN])
            pin = acc.IN_i[:nin]
            pf = acc.IN_f[:nin]
            r = dict(owner_exec_id=row['exec_id'], mechanism=mech, path_id=int(path), seed=int(seed), phase=phase, n_unmatched_days=int(umf.sum()),
                     n_intents=nin, err=int(acc.S_i[E.SI_ERR]), rndfix=int(acc.S_i[E.SI_RNDFIX]), rt_limit=int(acc.S_i[E.SI_RTLIM]),
                     rt_nomatch=int(acc.S_i[E.SI_RTNOM]), rt_identity=int(acc.S_i[E.SI_RTID]), status='OK')
            for s, (v, n) in Dm.items():
                r['D_%s' % s] = v
                r['n_%s' % s] = n
                mm = (segi == s)[:n_days]
                for k, c in (('req', 'v2_req'), ('within', 'v2_within'), ('cross', 'v2_cross'), ('unm', 'v2_unm'), ('nreq', 'v2_nreq'), ('rtshort', 'rt_short'),
                             ('list', 'list_n'), ('newn', 'new_n'), ('rttk', 'rt_tickets')):
                    r['%s_%s' % (k, s)] = float(DY[mm, E.DYI[c]].sum())
                r['nunm_%s' % s] = int(umf[mm].sum())
                st = DY[mm, E.DYI['rt_status']].astype(np.int64)
                for code, nm in ((E.RTS_FEASIBLE, 'rtfeas'), (E.RTS_NOMATCH, 'rtnom'), (E.RTS_LIMIT, 'rtlim'), (E.RTS_IDENTITY, 'rtid')):
                    r['%s_%s' % (nm, s)] = int((st == code).sum())
                # 强度：路径意向 / owner 意向（数量、金额、唯一证券）
                sd = (segi[pin[:, E.IN_DAY]] == s) if nin else np.zeros(0, bool)
                so = (segi[o_day] == s) if len(o_day) else np.zeros(0, bool)
                r['pint_%s' % s] = int(sd.sum())
                r['oint_%s' % s] = int(so.sum())
                r['pval_%s' % s] = float(pf[sd, 0].sum()) if nin else 0.0
                r['oval_%s' % s] = float(o_val[so].sum()) if len(o_val) else 0.0
                r['psec_%s' % s] = int(len(set(zip(pin[sd, E.IN_DAY].tolist(), pin[sd, E.IN_SEC].tolist())))) if nin else 0
                r['osec_%s' % s] = int(len(set(zip(o_day[so].tolist(), o_sec[so].tolist())))) if len(o_day) else 0
            rows.append(r)
            if daily is not None:
                nav = DY[:, E.DYI['nav_post']]
                vprev = np.r_[O.V0, nav[:-1]]
                daily['ne'].append(ne.astype(np.float32))
                daily['feefr'].append((DY[:, E.DYI['fee']] / vprev).astype(np.float32))
                daily['expo'].append(DY[:, E.DYI['exposure']].astype(np.float32))
                daily['cash'].append(DY[:, E.DYI['cash_share']].astype(np.float32))
                daily['turn'].append((0.5 * DY[:, E.DYI['traded']] / nav).astype(np.float32))
                daily['s05'].append(DY[:, E.DYI['cost_s05']].astype(np.float32))
                daily['s07'].append(DY[:, E.DYI['cost_s07']].astype(np.float32))
                daily['s10'].append(DY[:, E.DYI['cost_s10']].astype(np.float32))
                daily['req'].append(DY[:, E.DYI['v2_req']].astype(np.float32))
                daily['unm'].append(DY[:, E.DYI['v2_unm']].astype(np.float32))
                daily['rtst'].append(DY[:, E.DYI['rt_status']].astype(np.int8))
                daily['rtshort'].append(DY[:, E.DYI['rt_short']].astype(np.float32))
                daily['nint'].append(DY[:, E.DYI['n_intents']].astype(np.float32))
                daily['xplan'].append(DY[:, E.DYI['extra_plan']])
                daily['tkt'].append(DY[:, E.DY_ARMUSE].copy())
        if daily is not None:
            d = O.P('randoms', 'daily', row['exec_hash'][:2])
            os.makedirs(d, exist_ok=True)
            O.atomic_write_npz(os.path.join(d, '%s_%s_%04d.npz' % (row['exec_hash'], mech, paths[0])), path_id=np.array(paths),
                               seed=np.array([r_['seed'] for r_ in rows], np.int64), **{k: np.stack(v) for k, v in daily.items()})
        return rows
    except Exception as e:
        return [dict(owner_exec_id=row['exec_id'], mechanism=mech, path_id=-1, phase=phase, status='FAILED', err='%s: %s' % (type(e).__name__, str(e)[:300]),
                     tb=traceback.format_exc()[-900:])]


def main_owner_ids():
    R = G['R']
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6q.csv'), dtype=str)
    return set(RR[RR.mcse_target.fillna('') != ''].owner_logical_id)


def random_jobs(phase, batch, path_lo=0, path_hi=None, owners=None, mechs=None):
    R = G['R']
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6q.csv'), dtype=str)
    Rl = R.set_index('logical_id', drop=False)
    byid = R.set_index('exec_id', drop=False)
    jobs = []
    for r in RR.itertuples(index=False):
        row = Rl.loc[r.owner_logical_id].to_dict()
        mech = r.mechanism
        if owners is not None and row['exec_id'] not in owners:
            continue
        if mechs is not None and mech not in mechs:
            continue
        hi = int(r.start_paths) if path_hi is None else path_hi
        lo = path_lo
        if mech == 'LEVEL_WORST_1D':
            if lo > 0:
                continue
            hi = 1
        parent_h = byid.loc[row['parent_same_arm_exec_id']].exec_hash
        bt = max(1, batch // 2) if mech.startswith('RANDOM_TARGET') else batch
        for b0 in range(lo, hi, bt):
            jobs.append((phase, row, parent_h, mech, list(range(b0, min(hi, b0 + bt)))))
    jobs.sort(key=lambda j: (0 if j[3].startswith('RANDOM_TARGET') else 1, j[1]['exec_hash'], j[3], j[4][0]))
    return jobs


def write_random_rows(rows, tag):
    D = pd.DataFrame(rows)
    p = O.P('randoms', 'random_paths_%s.csv' % tag)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    O.atomic_write_csv(p, D.drop(columns=[c for c in ('tb',) if c in D.columns]))
    return D, p


def run_resumable(jobs, workers, tag, label):
    """随机批次：每 1,000 批原子落盘一次部分结果（randoms/random_paths_<tag>.partial.csv）；重启时跳过已完成批次（同 owner × 机制 × 路径）。"""
    part = O.P('randoms', 'random_paths_%s.partial.csv' % tag)
    done_rows = []
    if os.path.exists(part):
        P0 = pd.read_csv(part, keep_default_na=False, na_values=[''])
        P0 = P0[P0.status == 'OK']
        done_rows = P0.to_dict('records')
        done = set(zip(P0.owner_exec_id, P0.mechanism, P0.path_id))
        jobs = [j for j in jobs if not all((j[1]['exec_id'], j[3], p) in done for p in j[4])]
        O.log('%s 续跑：已完成 %d 行，剩余 %d 批' % (label, len(P0), len(jobs)))
    t0 = time.time()
    rows = list(done_rows)
    ctx = get_context('fork')
    with ctx.Pool(min(workers, max(1, len(jobs)))) as pool:
        for i, r in enumerate(pool.imap_unordered(job_random, jobs, chunksize=1)):
            rows.extend(r)
            if any(x.get('status') == 'FAILED' for x in r):
                O.log('%s FAILED %s' % (label, r[0].get('err', '')))
            if (i + 1) % 1000 == 0:
                os.makedirs(os.path.dirname(part), exist_ok=True)
                O.atomic_write_csv(part, pd.DataFrame(rows).drop(columns=['tb'], errors='ignore'))
                O.log('%s %d/%d 批（%.0f s；已落盘）' % (label, i + 1, len(jobs), time.time() - t0))
    return rows, time.time() - t0


def cmd_randoms(a):
    gate(a.phase, 'randoms')
    setup()
    G['R'] = registry()
    jobs = random_jobs(a.phase, a.batch, mechs=set(a.mechs.split(',')) if a.mechs else None)
    O.log('randoms %s：%d 批' % (a.phase, len(jobs)))
    out, w = run_resumable(jobs, a.workers, a.tag or a.phase, 'randoms %s' % a.phase)
    D, p = write_random_rows(out, a.tag or a.phase)
    nf = int((D.status == 'FAILED').sum())
    O.write_receipt('E6q_randoms_%s' % (a.tag or a.phase), [p], code=[__file__, E.__file__, A.__file__], rows=len(D), failed=nf, wall_s=round(w, 1),
                    rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.log('randoms %s 完成：%d 行，失败 %d，%.0f s' % (a.phase, len(D), nf, w))
    if nf:
        print(D[D.status == 'FAILED'].head(5).to_string()[:3000], flush=True)
        sys.exit(1)


def full_D(df):
    num = 0.0
    den = 0
    for s in O.SEGS:
        v = df['D_%s' % s].to_numpy(float)
        n = df['n_%s' % s].to_numpy(float)
        num = num + np.nan_to_num(v) * n
        den = den + n
    with np.errstate(all='ignore'):
        return num / den


def cmd_topup(a):
    gate('B', 'topup')
    setup()
    G['R'] = registry()
    R = G['R']
    mains = R[R.logical_id.isin(main_owner_ids())]
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6q.csv'), dtype=str)
    have = {(o, m) for o, m, t in zip(RR.owner_logical_id, RR.mechanism, RR.mcse_target.fillna('')) if t != ''}   # 只增补带 MCSE 目标的引用（附录 brief §6：主形态 HG10 owner）
    base = pd.read_csv(O.P('randoms', 'random_paths_B.csv'), keep_default_na=False, na_values=[''])
    extra = []
    k = 0
    while True:
        k += 1
        cur = pd.concat([base] + extra) if extra else base
        need = []
        for r in mains.itertuples(index=False):
            for mech in TOPUP_MECHS:
                if (r.logical_id, mech) not in have:
                    continue
                x = cur[(cur.owner_exec_id == r.exec_id) & (cur.mechanism == mech) & (cur.status == 'OK')]
                n = len(x)
                fd = full_D(x)
                mcse = float(np.std(fd, ddof=1) / np.sqrt(n)) if n > 1 else np.inf
                if mcse > MCSE_TARGET and n < MAX_PATHS:
                    need.append((r.exec_id, mech, n))
        O.log('topup 第 %d 轮：%d 个 owner×机制 未达 MCSE ≤ %.2f' % (k, len(need), MCSE_TARGET))
        if not need:
            break
        jobs = []
        for e, mech, n in need:
            jobs += random_jobs('B', a.batch, path_lo=n, path_hi=min(MAX_PATHS, n + 128), owners={e}, mechs={mech})
        out, w = run_resumable(jobs, a.workers, 'B_topup_r%d' % k, 'topup B r%d' % k)
        D = pd.DataFrame(out)
        if (D.status == 'FAILED').any():
            print(D[D.status == 'FAILED'].head(5).to_string()[:3000], flush=True)
            sys.exit(1)
        extra.append(D)
        write_random_rows(pd.concat(extra).to_dict('records'), 'B_topup')
    if extra:
        D, p = write_random_rows(pd.concat(extra).to_dict('records'), 'B_topup')
        O.write_receipt('E6q_randoms_B_topup', [p], code=[__file__], rows=len(D), rounds=k)
    else:
        D, p = write_random_rows([], 'B_topup')
        O.write_receipt('E6q_randoms_B_topup', [p], code=[__file__], rows=0, rounds=k)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['accounts', 'feedback', 'warm', 'shadow', 'randoms', 'topup'])
    ap.add_argument('--phase', choices=['A2', 'B'], required=True)
    ap.add_argument('--workers', type=int, default=96)
    ap.add_argument('--only', default='')
    ap.add_argument('--mechs', default='')
    ap.add_argument('--batch', type=int, default=8)
    ap.add_argument('--tag', default='')
    a = ap.parse_args()
    {'accounts': cmd_accounts, 'feedback': cmd_feedback, 'warm': cmd_warm, 'shadow': cmd_shadow, 'randoms': cmd_randoms, 'topup': cmd_topup}[a.cmd](a)


if __name__ == '__main__':
    main()
