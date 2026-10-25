# -*- coding: utf-8 -*-
"""E6p 运行编排（brief §4 / §6；方式 B）。子命令：
  accounts --phase A2|B  registry 全部执行对象（先 ACCOUNT、后 MIRROR：镜像目标取 owner 同阶段 T 收盘敞口）；A2 跑推导段 [0, d19) 存 checkpoint / 日序列 / 意向 / 成交分片；
                         B 读 seal_A2（不在即拒绝）→ 从 checkpoint 续跑到 2026-03-27（连续全历史主口径，brief §0.1 #18）
  feedback --phase A2|B  成本反馈 84 路径（cost_feedback_refs；κ .5、δ .5、A ∈ {1, 5} 亿；冲击费实扣现金），同 checkpoint 链
  warm     --phase A2|B  WARM 四段重置敏感性（主对象两只 + 同 H 父 + H5 NATIVE 父 × 两情景；不进 registry；A2 只跑推导两段）
  shadow   --phase A2|B  576 个信息退出 owner 的同 H 无退出父影子（owner 触发面板只记 HITS / RISK，不发单；BERNOULLI_LAG60 概率）
  randoms  --phase A2|B  随机 / 水平控制（brief §6）：FEASIBLE 全部 refs（576 × 四机制、AMOUNT_ISK_V2 180、R_CHECKPOINT 12）128 起；IDEAL 18 主对象 owner
                         AMOUNT_MATCH_V2 128；A2 只跑推导段；B 从 0 日整段重放（推导段与 A2 逐位一致由 replaycheck 核）；B 另存全部路径日统计分片
  topup    --phase B     18 个主对象 owner × {AMOUNT_MATCH_V2, COUNT_ISK, BERNOULLI_LAG60} 按 MCSE ≤ .01 以 128 批增补至 1,024（达上限记 MC_LIMIT）
随机种子 = stable(E6p, owner 逻辑 ID, 机制, 路径序号)（brief §7）；路径各自递推（不共享 token / 现金 / 状态）。并发：fork 池，父进程先加载 mmap 与形成名单并预编译。"""
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

import e6p_core as O
import e6p_engine as E
import e6p_acct as A

G = {}
PH = {'A2': 'deriv', 'B': 'full'}
CH_DAYS = 400
TLCAP = 1 << 20
MECH_SEL = {'AMOUNT_MATCH_V2': E.SM_AMT2, 'COUNT_ISK': E.SM_ISK2, 'BERNOULLI_LAG60': E.SM_BERN, 'LEVEL_WORST_1D': E.SM_LVL2, 'AMOUNT_ISK_V2': E.SM_AISK2,
            'R_CHECKPOINT': E.SM_RCHK}
TOPUP_MECHS = ('AMOUNT_MATCH_V2', 'COUNT_ISK', 'BERNOULLI_LAG60')
MCSE_TARGET = 0.01
MAX_PATHS = 1024
DCOLS = ('ne', 'feefr', 'expo', 'cash', 's05', 's07', 'req', 'unm')


def d19():
    return int(np.searchsorted(G['mk'].dates, '2019-01-01'))


def d_end(phase):
    return d19() if phase == 'A2' else G['mk'].T


def registry():
    return pd.read_csv(O.P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)


def gate(phase, what):
    if not os.path.exists(O.P('registration', 'freeze_E6p.json')):
        raise RuntimeError('%s：freeze_E6p.json 不在（A1 未冻结），拒绝运行' % what)
    if phase == 'B' and not os.path.exists(O.P('registration', 'seal_A2.json')):
        raise RuntimeError('%s：seal_A2.json 不在，拒绝写后段' % what)


def setup():
    mk = A.Market()
    G['mk'] = mk
    G['f'] = {(f, m): mk.formation(f, m) for f in O.FORMS for m in O.MEMS if (f == O.MAIN_FORM or m == 'HG10')}
    G['nf'] = {f: mk.natural(f) for f in O.FORMS}
    ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True, deploy=E.DP_TARGET, target=0.8, cap=E.CP_REL, renew=5, recycle=E.RY_COSTNET, tlog=True)
    A.Account(mk, ip, fp, 'T1a', G['f'][(O.MAIN_FORM, 'HG10')], nf_csr=G['nf'][O.MAIN_FORM], lcap=1 << 14, incap=1 << 16, tlcap=1 << 16).run(0, 30)
    for sel in (E.SM_AMT2, E.SM_ISK2, E.SM_BERN, E.SM_LVL2, E.SM_AISK2, E.SM_RCHK):
        ip, fp = A.ip_fp(20, E.TM_PANEL, sel=sel, fund=E.FD_NATIVE, exit_on=True, renew=5 if sel == E.SM_RCHK else 0, seed=1)
        tg = dict(b=np.zeros((mk.T, E.NB)), isk2=np.zeros((mk.T, (mk.n_isk + 1) * E.NB)), aisk=np.zeros((mk.T, (mk.n_isk + 1) * E.NB)),
                  rchk=np.zeros(mk.T), bern=np.zeros((mk.T, 20)))
        A.Account(mk, ip, fp, 'T1a', G['f'][(O.MAIN_FORM, 'HG10')], nf_csr=G['nf'][O.MAIN_FORM], targets=tg, lcap=1 << 14, incap=1 << 16).run(0, 30)


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


# ------------------------------------------------------------------ 账户
def mirror_target(phase, row):
    """镜像目标 = owner 在 T 收盘已观测到的风险敞口（1 − 收盘现金 / 收盘 NAV；owner 同情景、同阶段结果）；不读 owner 的 T+1 成交或未来路径。"""
    R = G['R']
    o = R[(R.logical_id == row['owner_logical_id']) & (R.execution_profile == row['execution_profile'])]
    if len(o) != 1:
        raise RuntimeError('镜像 owner 不唯一')
    z = np.load(res_path(phase, o.iloc[0].exec_hash), allow_pickle=False)
    DY = z['DY']
    T = G['mk'].T
    out = np.full(T, np.nan)
    n = len(DY)
    navc = DY[:, E.DYI['nav_close']]
    cash = DY[:, E.DYI['cash_share']] * DY[:, E.DYI['nav_post']]
    with np.errstate(all='ignore'):
        out[:n] = np.where(navc > 0, 1.0 - cash / navc, np.nan)
    return out


def build(row, phase, sel=E.SM_REAL, seed=0, shadow=False, feedback=None, targets=None, tlog=False, start=0):
    mk = G['mk']
    ip, fp, trig = A.spec_params(row, profile=row['execution_profile'], sel=sel, seed=seed, shadow=shadow, tlog=tlog, feedback=feedback)
    form, mem = row['form'], row['memory']
    nf = G['nf'][form] if int(row['renew']) != 0 else None
    te = mirror_target(phase, row) if row['deploy'] == 'MIRROR_LAG1' else None
    return A.Account(mk, ip, fp, trig, G['f'][(form, mem)], nf_csr=nf, targets=targets, tgt_expo=te, tlcap=TLCAP if tlog else 0, start=start)


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
        ti = np.zeros((0, 7), np.int64)
        tf = np.zeros((0, 4))
    O.atomic_write_npz(path, TL_i=ti, TL_f=tf)
    return len(ti)


def job_account(args):
    phase, row, kind, extra = args
    t0 = time.time()
    try:
        h = row['exec_hash'] if kind == 'acct' else extra['hash']
        tlog = kind == 'acct' and row['role'] == 'ACCOUNT'
        fb = (float(extra['A']), 0.5, 0.5) if kind == 'fb' else None
        acc = build(row, phase, tlog=tlog, feedback=fb)
        dA, T = d19(), G['mk'].T
        sink = [] if tlog else None
        meta = dict(exec_id=row['exec_id'], exec_hash=row['exec_hash'], kind=kind, phase=phase, feedback_A=extra.get('A', '') if extra else '',
                    written_at=time.strftime('%Y-%m-%d %H:%M:%S'), code_sha256=O.sha_file(E.__file__))
        if phase == 'A2':
            run_flush(acc, 0, dA, sink)
            acc.checkpoint(ckpt_path(h), dict(meta, day=dA))
            save_result(res_path('A2', h, kind), acc, dict(meta, d0=0, d1=dA), dA)
        else:
            acc.restore(ckpt_path(h))
            run_flush(acc, dA, T, sink)
            save_result(res_path('B', h, kind), acc, dict(meta, d0=0, d1=T, restored_from='A2_end'), T, final_lots=True)
        ntr = save_trades(trade_path(phase, h), sink) if tlog else 0
        return dict(exec_id=row['exec_id'], hash=h, kind=kind, status='OK', wall_s=round(time.time() - t0, 2), n_intents=int(acc.S_i[E.SI_NIN]),
                    n_trades=ntr, rndfix=int(acc.S_i[E.SI_RNDFIX]), err=int(acc.S_i[E.SI_ERR]))
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
    O.write_receipt('E6p_%s' % outname.replace('.csv', ''), [p], code=[__file__, E.__file__, A.__file__] + list(code), n=len(D), failed=nf, wall_s=round(wall, 1),
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
    R = R[R.series != 'P_SOURCE']
    if a.only:
        keep = set(open(a.only).read().split())
        R = R[R.exec_hash.isin(keep) | R.exec_id.isin(keep)]
    acc_rows = R[R.role == 'ACCOUNT']
    mir_rows = R[R.role == 'MIRROR']
    rows = []
    wall = 0.0
    for wave, df in (('owners', acc_rows), ('mirrors', mir_rows)):
        df = df.assign(_o=-df.H.astype(int)).sort_values('_o').drop(columns=['_o'])
        jobs = [(a.phase, r._asdict(), 'acct', {}) for r in df.itertuples(index=False)]
        out, w = pool_run(job_account, jobs, a.workers, 'accounts %s %s' % (a.phase, wave))
        rows += out
        wall += w
        if any(x['status'] == 'FAILED' for x in out):
            break
    finish('accounts %s' % a.phase, rows, wall, 'accounts_%s.csv' % a.phase)


def cmd_feedback(a):
    gate(a.phase, 'feedback')
    setup()
    R = G['R'] = registry()
    F = pd.read_csv(O.P('registration', 'cost_feedback_refs_E6p.csv'), keep_default_na=False, dtype=str)
    Rf = R[R.execution_profile == 'FEASIBLE_DAILY'].set_index('logical_id', drop=False)
    jobs = []
    for f in F.itertuples(index=False):
        row = Rf.loc[f.owner_logical_id].to_dict()
        jobs.append((a.phase, row, 'fb', dict(A=int(f.A_cny), hash=fb_hash(row['exec_id'], int(f.A_cny)))))
    out, w = pool_run(job_account, jobs, a.workers, 'feedback %s' % a.phase)
    finish('feedback %s' % a.phase, out, w, 'feedback_%s.csv' % a.phase)


def warm_rows():
    R = G['R']
    acc = R[(R.role == 'ACCOUNT')]
    main = acc[acc.is_main_object == '1']
    keep = set(main.exec_id) | set(main.parent_same_h_exec_id) | set(main.parent_h5_native_exec_id)
    return R[R.exec_id.isin(keep)]


def job_warm(args):
    phase, row, seg = args
    t0 = time.time()
    try:
        mk = G['mk']
        segi = G['segi']
        idx = np.flatnonzero(segi == seg)
        s0, s1 = int(idx[0]), int(idx[-1]) + 1
        acc = build(row, phase, start=s0)
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
    G['segi'] = np.array([O.seg_of_date(d) for d in G['mk'].dates])
    segs = O.DERIV_SEGS if a.phase == 'A2' else O.POST_SEGS
    jobs = [(a.phase, r._asdict(), s) for r in warm_rows().itertuples(index=False) for s in segs]
    out, w = pool_run(job_warm, jobs, a.workers, 'warm %s' % a.phase)
    finish('warm %s' % a.phase, out, w, 'warm_%s.csv' % a.phase)


# ------------------------------------------------------------------ 影子与随机
def owners_576():
    R = G['R']
    return R[(R.role == 'ACCOUNT') & (R.trigger != 'NONE') & (R.execution_profile == 'FEASIBLE_DAILY')]


def main_owner_ids():
    R = G['R']
    m = R[(R.role == 'ACCOUNT') & (R.form == O.MAIN_FORM) & (R.H == '20') & (R.trigger.isin(['T1a', 'T1b_LEVEL'])) & (R.renew == '0') & (R.block == 'MAIN')]
    return set(m.logical_id)


def job_shadow(args):
    phase, row = args
    t0 = time.time()
    try:
        acc = build(row, phase, shadow=True)
        acc.run(0, d_end(phase))
        O.atomic_write_npz(res_path(phase, row['exec_hash'], 'shadow'), HITS=acc.HITS, RISK=acc.RISK,
                           meta=np.array([json.dumps(dict(owner=row['exec_id'], phase=phase), sort_keys=True)]))
        return dict(exec_id=row['exec_id'], status='OK', hits=int(acc.HITS.sum()), wall_s=round(time.time() - t0, 2))
    except Exception as e:
        return dict(exec_id=row['exec_id'], status='FAILED', err='%s: %s' % (type(e).__name__, str(e)[:300]), tb=traceback.format_exc()[-900:])


def cmd_shadow(a):
    gate(a.phase, 'shadow')
    setup()
    G['R'] = registry()
    jobs = [(a.phase, r._asdict()) for r in owners_576().itertuples(index=False)]
    out, w = pool_run(job_shadow, jobs, a.workers, 'shadow %s' % a.phase)
    finish('shadow %s' % a.phase, out, w, 'shadow_%s.csv' % a.phase)


def bern_prob(phase, h, T, NL):
    """BERNOULLI_LAG60：owner 同 H 无退出父影子在前 60 个交易日（不含当日）的逐日龄层已成熟触发率；有效日（层风险集 > 0）< 20 → NaN（不抽）。"""
    z = np.load(res_path(phase, h, 'shadow'), allow_pickle=False)
    hits = z['HITS'][:, :NL].astype(float)
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


def owner_targets(phase, row, mech):
    """owner 在 T 收盘的意向目标（只用 owner 自己 T 收盘已知量；plan §8.1）：触发意向（KD_TRIG）；R_CHECKPOINT 用 renew-only owner 的检查点退出意向（KD_RENEW）。"""
    mk = G['mk']
    T = mk.T
    H = int(row['H'])
    NC1 = (mk.n_isk + 1) * E.NB
    z = np.load(res_path(phase, row['exec_hash']), allow_pickle=False)
    IN_i, IN_f = z['IN_i'], z['IN_f']
    kind = E.KD_RENEW if mech == 'R_CHECKPOINT' else E.KD_TRIG
    m = IN_i[:, E.IN_KIND] == kind
    day, sec, age, isk = IN_i[m, E.IN_DAY], IN_i[m, E.IN_SEC], IN_i[m, E.IN_AGE], IN_i[m, E.IN_ISK]
    val = IN_f[m, 0]
    bk = np.array([E.bucket_of(int(x)) for x in age], np.int64) if len(age) else np.zeros(0, np.int64)
    cell = np.where(isk >= 0, isk, mk.n_isk).astype(np.int64)
    tg = {}
    if mech in ('AMOUNT_MATCH_V2', 'LEVEL_WORST_1D'):
        b = np.zeros((T, E.NB))
        np.add.at(b, (day, bk), val)
        tg['b'] = b
    elif mech == 'AMOUNT_ISK_V2':
        x = np.zeros((T, NC1))
        np.add.at(x, (day, cell * E.NB + bk), val)
        tg['aisk'] = x
    elif mech == 'COUNT_ISK':
        x = np.zeros((T, NC1))
        if len(day):
            df = pd.DataFrame(dict(day=day, sec=sec, val=val, bk=bk, cell=cell))
            dom = df.sort_values(['day', 'sec', 'val'], ascending=[True, True, False]).drop_duplicates(['day', 'sec'])
            np.add.at(x, (dom.day.to_numpy(), dom.cell.to_numpy() * E.NB + dom.bk.to_numpy()), 1.0)
        tg['isk2'] = x
    elif mech == 'BERNOULLI_LAG60':
        tg['bern'] = bern_prob(phase, row['exec_hash'], T, H)
    elif mech == 'R_CHECKPOINT':
        x = np.zeros(T)
        np.add.at(x, day, val)
        tg['rchk'] = x
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
    mk = G['mk']
    n_days = d_end(phase)
    rows = []
    try:
        key = (phase, row['exec_hash'], mech)
        if key not in _CACHE:
            _CACHE.clear()
            _CACHE[key] = owner_targets(phase, row, mech)
            _CACHE[('P', phase, parent_h)] = np.load(res_path(phase, parent_h), allow_pickle=False)['DY'][:, E.DYI['net_excess']]
        tg = _CACHE[key]
        pne = _CACHE[('P', phase, parent_h)]
        segi = G['segi']
        daily = {k: [] for k in DCOLS} if phase == 'B' else None
        for path in paths:
            seed = O.stable_u64('E6p', row['logical_id'], mech, path) & ((1 << 62) - 1)
            acc = build(row, phase, sel=MECH_SEL[mech], seed=seed, targets=tg)
            acc.run(0, n_days)
            DY = acc.DY[:n_days]
            ne = DY[:, E.DYI['net_excess']]
            Dm = seg_D(ne, pne[:n_days], n_days)
            unm = DY[:, E.DYI['v2_unm']]
            umf = unm > np.maximum(1.0, 1e-6 * DY[:, E.DYI['v2_req']])     # 未匹配日：≥ 1 元且 ≥ 1e−6 × 当日请求（去掉浮点残差；COUNT_ISK 计数同用）
            r = dict(owner_exec_id=row['exec_id'], mechanism=mech, path_id=int(path), seed=int(seed), phase=phase,
                     n_unmatched_days=int(umf.sum()), n_intents=int(acc.S_i[E.SI_NIN]), err=int(acc.S_i[E.SI_ERR]),
                     rndfix=int(acc.S_i[E.SI_RNDFIX]), status='OK')
            for s, (v, n) in Dm.items():
                r['D_%s' % s] = v
                r['n_%s' % s] = n
                mm = (segi == s)[:n_days]
                for k, c in (('req', 'v2_req'), ('within', 'v2_within'), ('cross', 'v2_cross'), ('unm', 'v2_unm'), ('nreq', 'v2_nreq')):
                    r['%s_%s' % (k, s)] = float(DY[mm, E.DYI[c]].sum())
                r['nunm_%s' % s] = int(umf[mm].sum())
            rows.append(r)
            if daily is not None:
                nav = DY[:, E.DYI['nav_post']]
                vprev = np.r_[O.V0, nav[:-1]]
                daily['ne'].append(ne.astype(np.float32))
                daily['feefr'].append((DY[:, E.DYI['fee']] / vprev).astype(np.float32))
                daily['expo'].append(DY[:, E.DYI['exposure']].astype(np.float32))
                daily['cash'].append(DY[:, E.DYI['cash_share']].astype(np.float32))
                daily['s05'].append(DY[:, E.DYI['cost_s05']].astype(np.float32))
                daily['s07'].append(DY[:, E.DYI['cost_s07']].astype(np.float32))
                daily['req'].append(DY[:, E.DYI['v2_req']].astype(np.float32))
                daily['unm'].append(DY[:, E.DYI['v2_unm']].astype(np.float32))
        if daily is not None:
            d = O.P('randoms', 'daily', row['exec_hash'][:2])
            os.makedirs(d, exist_ok=True)
            O.atomic_write_npz(os.path.join(d, '%s_%s_%04d.npz' % (row['exec_hash'], mech, paths[0])), path_id=np.array(paths),
                               seed=np.array([r_['seed'] for r_ in rows], np.int64), **{k: np.stack(v) for k, v in daily.items()})
        return rows
    except Exception as e:
        return [dict(owner_exec_id=row['exec_id'], mechanism=mech, path_id=-1, phase=phase, status='FAILED', err='%s: %s' % (type(e).__name__, str(e)[:300]),
                     tb=traceback.format_exc()[-900:])]


def random_jobs(phase, batch, path_lo=0, path_hi=None, owners=None, mechs=None):
    R = G['R']
    RR = pd.read_csv(O.P('registration', 'random_control_refs_E6p.csv'), keep_default_na=False, dtype=str)
    Rf = R[R.execution_profile == 'FEASIBLE_DAILY'].set_index('logical_id', drop=False)
    Ri = R[R.execution_profile == 'IDEALIZED_SOURCE_FILL'].set_index('logical_id', drop=False)
    byid = R.set_index('exec_id', drop=False)
    jobs = []
    specs = [(Rf.loc[r.owner_logical_id].to_dict(), r.mechanism, int(r.minimum_paths)) for r in RR.itertuples(index=False)]
    specs += [(Ri.loc[lid].to_dict(), 'AMOUNT_MATCH_V2', 128) for lid in sorted(main_owner_ids())]
    for row, mech, mp in specs:
        if owners is not None and row['exec_id'] not in owners:
            continue
        if mechs is not None and mech not in mechs:
            continue
        hi = mp if path_hi is None else path_hi
        lo = path_lo
        if mech == 'LEVEL_WORST_1D':
            if lo > 0:
                continue
            hi = 1
        parent_h = byid.loc[row['parent_same_h_exec_id']].exec_hash
        for b0 in range(lo, hi, batch):
            jobs.append((phase, row, parent_h, mech, list(range(b0, min(hi, b0 + batch)))))
    jobs.sort(key=lambda j: (j[1]['exec_hash'], j[3], j[4][0]))
    return jobs


def write_random_rows(rows, tag):
    D = pd.DataFrame(rows)
    p = O.P('randoms', 'random_paths_%s.csv' % tag)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    O.atomic_write_csv(p, D.drop(columns=[c for c in ('tb',) if c in D.columns]))
    return D, p


def run_resumable(jobs, workers, tag, label):
    """随机批次：每 1,000 批原子落盘一次部分结果（randoms/random_paths_<tag>.partial.csv）；重启时跳过已完成批次（同 owner × 机制 × 起始路径）。"""
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
    G['segi'] = np.array([O.seg_of_date(d) for d in G['mk'].dates])
    jobs = random_jobs(a.phase, a.batch, mechs=set(a.mechs.split(',')) if a.mechs else None)
    O.log('randoms %s：%d 批' % (a.phase, len(jobs)))
    out, w = run_resumable(jobs, a.workers, a.tag or a.phase, 'randoms %s' % a.phase)
    D, p = write_random_rows(out, a.tag or a.phase)
    nf = int((D.status == 'FAILED').sum())
    O.write_receipt('E6p_randoms_%s' % (a.tag or a.phase), [p], code=[__file__, E.__file__, A.__file__], rows=len(D), failed=nf, wall_s=round(w, 1),
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
    G['segi'] = np.array([O.seg_of_date(d) for d in G['mk'].dates])
    R = G['R']
    mains = R[(R.logical_id.isin(main_owner_ids())) & (R.execution_profile == 'FEASIBLE_DAILY')]
    base = pd.read_csv(O.P('randoms', 'random_paths_B.csv'), keep_default_na=False, na_values=[''])
    extra = []
    k = 0
    while True:
        k += 1
        cur = pd.concat([base] + extra) if extra else base
        need = []
        for r in mains.itertuples(index=False):
            for mech in TOPUP_MECHS:
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
        out, w = pool_run(job_random, jobs, a.workers, 'topup B r%d' % k, ordered=True)
        D = pd.DataFrame(out)
        if (D.status == 'FAILED').any():
            print(D[D.status == 'FAILED'].head(5).to_string()[:3000], flush=True)
            sys.exit(1)
        extra.append(D)
        write_random_rows(pd.concat(extra).to_dict('records'), 'B_topup')
    if extra:
        D, p = write_random_rows(pd.concat(extra).to_dict('records'), 'B_topup')
        O.write_receipt('E6p_randoms_B_topup', [p], code=[__file__], rows=len(D), rounds=k)
    else:
        write_random_rows([], 'B_topup')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['accounts', 'feedback', 'warm', 'shadow', 'randoms', 'topup'])
    ap.add_argument('--phase', choices=['A2', 'B'], required=True)
    ap.add_argument('--workers', type=int, default=96)
    ap.add_argument('--only', default='')
    ap.add_argument('--mechs', default='')
    ap.add_argument('--batch', type=int, default=16)
    ap.add_argument('--tag', default='')
    a = ap.parse_args()
    {'accounts': cmd_accounts, 'feedback': cmd_feedback, 'warm': cmd_warm, 'shadow': cmd_shadow, 'randoms': cmd_randoms, 'topup': cmd_topup}[a.cmd](a)


if __name__ == '__main__':
    main()
