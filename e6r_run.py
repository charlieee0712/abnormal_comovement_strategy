# -*- coding: utf-8 -*-
"""E6r 运行编排（brief §4 / §6 / §7；方式 B；沿 e6q_run）。子命令：
  accounts --phase A2|B  registry 全部 350 个执行对象（全部记成交日志与批次标签）：A2 跑推导段 [0, d19) 存 checkpoint / 日序列 / 意向 / 成交分片；
                         B 读 seal_A2（不在即拒绝）→ 从 checkpoint 续跑到 2026-03-27（连续全历史主口径；跨段不重置）
  feedback --phase A2|B  成本反馈 202 路径（cost_feedback_refs；A0 ∈ {1, 5} 亿、κ .5、δ .5；冲击费实扣现金），同 checkpoint 链
  shadow   --phase A2|B  BERNOULLI_FIRSTHIT 影子：每个 (form, memory, funding_H, scenario, trigger, weight_scheme) 的无退出影子（带本 overlay；首次已知 True）
  randoms  --phase A2|B  1,408 条机制引用：起始路径 = spec paths（256；主 9 相关 1,024；LEVEL_WORST_1D 确定性 1 路）；
                         A2 只跑推导段并给每条路径存 A2 末原子 checkpoint；B 从 A2 末状态续跑（不再从 0 日整段重放；checkpoint 缺失则整段跑并计数）
  topup    --phase B     带 MCSE 目标的随机引用按 FULL MCSE ≤ .01 以 256 → 512 → 1,024 增补（整段跑；达上限记 MC_LIMIT）
随机种子 = path_seed(owner 逻辑 ID, 机制, 路径序号)（E6R_BLOCK5_STABLE_SECURITY_V11；引擎内混五日块与证券稳定键）；路径各自递推（不共享 token / 现金 / 状态）；
随机账户施加与 owner 同一入场算子、退出算子与资金规则；入场层随机在路径自身快照上生成；退出层取 owner T 收盘意向目标（不复制 owner 未来成交）。
并发：fork 池，父进程先加载 mmap、形成名单与形成层数组并预编译。"""
import os
import sys
import json
import time
import queue
import argparse
import resource
import traceback
from multiprocessing import get_context

import numpy as np
import pandas as pd

import e6r_core as O
import e6r_engine as E
import e6r_acct as A

G = {}
PH = {'A2': 'deriv', 'B': 'full'}
CH_DAYS = 400
TLCAP = 1 << 20
EXIT_MECH = {'AMOUNT_MATCH_V2': E.SM_AMT2, 'COUNT_ISK': E.SM_ISK2, 'AMOUNT_ISK_V2': E.SM_AISK2, 'BERNOULLI_FIRSTHIT': E.SM_BERN, 'LEVEL_WORST_1D': E.SM_LVL2}
ENTRY_MECH = {'RANDOM_TILT_TICKETS': E.ER_TICKETS, 'RANDOM_TILT_LABEL_PROJECT': E.ER_LABEL, 'RANDOM_GATE_COUNT': E.ER_GCOUNT, 'RANDOM_GATE_AMOUNT': E.ER_GAMOUNT,
              'RANDOM_GATE_TILT_JOINT': E.ER_JOINT, 'RANDOM_TENOR_LABEL': E.ER_TENOR}
MAX_PATHS = 1024
DCOLS = ('ne', 'feefr', 'expo', 'cash', 'turn', 's05', 's07', 's10', 'req', 'unm', 'ovx', 'erst', 'nint')


def d19():
    return int(np.searchsorted(G['mk'].dates, '2019-01-01'))


def d_end(phase):
    return d19() if phase == 'A2' else G['mk'].T


def registry():
    return O.read_csv(O.P('registration', 'registry_E6r.csv'))


def gate(phase, what):
    if not os.path.exists(O.P('registration', 'freeze_E6r.json')):
        raise RuntimeError('%s：freeze_E6r.json 不在（A1 未冻结），拒绝运行' % what)
    if phase == 'B' and not os.path.exists(O.P('registration', 'seal_A2.json')):
        raise RuntimeError('%s：seal_A2.json 不在，拒绝写后段' % what)


def setup(compile_=True):
    mk = A.Market()
    G['mk'] = mk
    G['segi'] = O.segs_of_dates(mk.dates)
    for f in O.FORMS:
        for m in O.MEMS:
            mk.formation(f, m)
            mk.overlay(f, m)
    mk.formation(O.MAIN_FORM, 'HG10', w15=True)
    if compile_:
        R = registry()
        row = R[(R.weight_scheme == 'GATE_TILT') & (R.trigger == 'T1b_LEVEL')].iloc[0].to_dict()
        build(row, tlog=True).run(0, 30)
        build(row, ernd=E.ER_JOINT, seed=1).run(0, 30)


# ------------------------------------------------------------------ 路径与存放
def res_path(phase, h, kind='acct'):
    sub = {'acct': PH[phase], 'fb': PH[phase] + '_fb', 'shadow': 'shadow_' + PH[phase]}[kind]
    d = O.P('accounts_run', sub, h[:2])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, '%s.npz' % h)


def ckpt_path(h, sub='A2_end'):
    d = O.P('checkpoints', sub, h[:2])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, '%s.npz' % h)


def trade_path(phase, h):
    d = O.P('trades_parts', PH[phase], h[:2])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, '%s.npz' % h)


def fb_hash(exec_id, A_cny):
    return O.sha_bytes(('%s|FEEDBACK|%d|0.5|0.5' % (exec_id, int(A_cny))).encode())[:16]


def shadow_key(row):
    return O.sha_bytes(('SHADOW|%s|%s|%s|%s|%s|%s' % (row['form'], row['memory'], row['funding_H'], row['scenario'], row['trigger'],
                                                    row['weight_scheme'])).encode())[:16]


def path_hash(owner_h, mech, path):
    return O.sha_bytes(('%s|%s|%d' % (owner_h, mech, int(path))).encode())[:16]


# ------------------------------------------------------------------ 账户
def build(row, sel=E.SM_REAL, seed=0, shadow=False, feedback=None, targets=None, tlog=False, start=0, fhit=0, ernd=E.ER_NONE):
    mk = G['mk']
    ip, fp, trig = A.spec_params(row, sel=sel, seed=seed, shadow=shadow, tlog=tlog, feedback=feedback, fhit=fhit, ernd=ernd)
    f = mk.formation(row['form'], row['memory'], w15=row['weight_scheme'] == 'UNIFORM_CAP15')
    return A.Account(mk, ip, fp, trig, f, ov=A.overlay_arrays(mk, row), targets=targets, tlcap=TLCAP if tlog else 0, start=start)


def run_flush(acc, d0, d1, sink):
    d = d0
    while d < d1:
        e = min(d1, d + CH_DAYS)
        acc.run(d, e)
        n = int(acc.S_i[E.SI_NTL])
        if n and sink is not None:
            sink.append((acc.TL_i[:n].copy(), acc.TL_f[:n].copy()))
            acc.S_i[E.SI_NTL] = 0
            A.reset_tl_labels(acc.TL_i, acc.TL_f, n)
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
        S = acc.S_i
        return dict(exec_id=row['exec_id'], hash=h, kind=kind, status='OK', wall_s=round(time.time() - t0, 2), n_intents=int(S[E.SI_NIN]), n_trades=ntr,
                    err=int(S[E.SI_ERR]), projf=int(S[E.SI_PROJF]), override=int(S[E.SI_OVERRIDE]), half=int(S[E.SI_HALF]), rearm=int(S[E.SI_REARMN]),
                    fallback=int(S[E.SI_FALLBACK]), rndfix=int(S[E.SI_RNDFIX]))
    except Exception as e:
        return dict(exec_id=row['exec_id'], kind=kind, status='FAILED', wall_s=round(time.time() - t0, 2), err='%s: %s' % (type(e).__name__, str(e)[:300]),
                    tb=traceback.format_exc()[-900:])


def pool_run(fn, jobs, workers, label, chunksize=1):
    t0 = time.time()
    out = []
    ctx = get_context('fork')
    with ctx.Pool(min(workers, max(1, len(jobs)))) as pool:
        for i, r in enumerate(pool.imap_unordered(fn, jobs, chunksize=chunksize)):
            if isinstance(r, list):
                out.extend(r)
                bad = [x for x in r if x.get('status') == 'FAILED']
            else:
                out.append(r)
                bad = [r] if r.get('status') == 'FAILED' else []
            for b in bad[:1]:
                O.log('%s FAILED %s %s' % (label, b.get('exec_id', b.get('owner_exec_id', '')), b.get('err', '')))
            if (i + 1) % 100 == 0:
                O.log('%s %d/%d（%.0f s）' % (label, i + 1, len(jobs), time.time() - t0))
    return out, time.time() - t0


def finish(label, rows, wall, outname, code=()):
    D = pd.DataFrame(rows)
    p = O.P('task_status', outname)
    O.atomic_write_csv(p, D.drop(columns=[c for c in ('tb',) if c in D.columns]))
    nf = int((D.status == 'FAILED').sum()) if 'status' in D else 0
    O.write_receipt('E6r_%s' % outname.replace('.csv', ''), [p], code=[__file__, E.__file__, A.__file__] + list(code), n=len(D), failed=nf, wall_s=round(wall, 1),
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
        R = R[R.exec_hash.isin(keep) | R.exec_id.isin(keep) | R.logical_id.isin(keep)]
    R = R.assign(_o=-R.funding_H.astype(int)).sort_values('_o').drop(columns=['_o'])
    jobs = [(a.phase, r._asdict(), 'acct', {}) for r in R.itertuples(index=False)]
    out, w = pool_run(job_account, jobs, a.workers, 'accounts %s' % a.phase)
    finish('accounts %s' % a.phase, out, w, 'accounts_%s.csv' % a.phase)


def cmd_feedback(a):
    gate(a.phase, 'feedback')
    setup()
    R = G['R'] = registry()
    F = O.read_csv(O.P('registration', 'cost_feedback_refs_E6r.csv'))
    Rf = R.set_index('logical_id', drop=False)
    jobs = []
    for f in F.itertuples(index=False):
        row = Rf.loc[f.owner_logical_id].to_dict()
        jobs.append((a.phase, row, 'fb', dict(A=int(float(f.A0_cny)), hash=fb_hash(row['exec_id'], int(float(f.A0_cny))), feedback_id=f.feedback_id)))
    out, w = pool_run(job_account, jobs, a.workers, 'feedback %s' % a.phase)
    finish('feedback %s' % a.phase, out, w, 'feedback_%s.csv' % a.phase)


# ------------------------------------------------------------------ 影子
def shadow_rows():
    R = G['R']
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6r.csv'))
    owners = set(RR[RR.mechanism == 'BERNOULLI_FIRSTHIT'].owner_logical_id)
    S = {}
    for r in R[R.logical_id.isin(owners)].itertuples(index=False):
        d = r._asdict()
        k = shadow_key(d)
        if k not in S:
            S[k] = dict(d, exit_op='NATIVE', shadow_key=k)
    return S


def job_shadow(args):
    phase, row = args
    t0 = time.time()
    try:
        acc = build(row, shadow=True, fhit=1)
        acc.run(0, d_end(phase))
        O.atomic_write_npz(res_path(phase, row['shadow_key'], 'shadow'), HITS=acc.HITS, RISK=acc.RISK,
                           meta=np.array([json.dumps({k: str(v) for k, v in row.items()}, sort_keys=True)]))
        return dict(shadow_key=row['shadow_key'], trigger=row['trigger'], H=row['funding_H'], form=row['form'], memory=row['memory'],
                    weight_scheme=row['weight_scheme'], status='OK', hits=int(acc.HITS.sum()), risk=int(acc.RISK.sum()), wall_s=round(time.time() - t0, 2))
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
    """BERNOULLI_FIRSTHIT：影子在前 60 个交易日（严格不含 T）的首达风险率 hazard(日龄桶) = 首次事件 / 未首达且次日执行 < due 的有效 lot-day；
    桶内无风险分母 → 全龄池；仍无 → NaN（UNKNOWN，不抽）。零事件但有分母 = 合法零概率（沿 E6q）。"""
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
    """退出层随机：owner 在 T 收盘的意向目标（只用 owner 自己 T 收盘已知量；plan §8.3）：触发意向（KD_TRIG / T1A_TIME_LEVEL_RANK 的 KD_RAND）；BERNOULLI 用影子风险率。"""
    mk = G['mk']
    T = mk.T
    NL = int(A.spec_params(row)[0][E.IP_NLAYER])
    NC = mk.n_isk * E.NB
    if mech == 'BERNOULLI_FIRSTHIT':
        return dict(bern=bern_prob(phase, shadow_key(row), T, NL))
    z = np.load(res_path(phase, row['exec_hash']), allow_pickle=False)
    IN_i, IN_f = z['IN_i'], z['IN_f']
    m = np.isin(IN_i[:, E.IN_KIND], (E.KD_TRIG, E.KD_RAND, E.KD_REARM))
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


def seg_D(ne, pne, n_days, d0=0):
    out = {}
    segi = G['segi']
    for s in O.SEGS:
        mm = (segi == s)[d0:n_days]
        x = ne[d0:n_days][mm] - pne[d0:n_days][mm]
        ok = np.isfinite(x)
        out[s] = (float(np.mean(x[ok]) * O.ANN_PP) if ok.any() else np.nan, int(ok.sum()))
    return out


_CACHE = {}


def path_row(row, mech, path, seed, phase, acc, DY, pne, n_days, oin, oif, oovb, oocn):
    segi = G['segi']
    ne = DY[:, E.DYI['net_excess']]
    Dm = seg_D(ne, pne, n_days)
    r = dict(owner_exec_id=row['exec_id'], mechanism=mech, path_id=int(path), seed=str(seed), phase=phase, n_intents=int(acc.S_i[E.SI_NIN]),
             err=int(acc.S_i[E.SI_ERR]), projf=int(acc.S_i[E.SI_PROJF]), er_feas=int(acc.S_i[E.SI_ERFEAS]), er_nom=int(acc.S_i[E.SI_ERNOM]),
             er_lim=int(acc.S_i[E.SI_ERLIM]), er_id=int(acc.S_i[E.SI_ERID]), status='OK')
    st = DY[:, E.DY_ERST].astype(np.int64)
    okind = np.isin(oin[:, E.IN_KIND], (E.KD_TRIG, E.KD_RAND, E.KD_REARM)) if len(oin) else np.zeros(0, bool)
    o_day = oin[okind, E.IN_DAY] if len(oin) else np.zeros(0, np.int64)
    o_val = oif[okind, 0] if len(oin) else np.zeros(0)
    nin = int(acc.S_i[E.SI_NIN])
    pin_ = acc.IN_i[:nin]
    pf_ = acc.IN_f[:nin]
    for s, (v, n) in Dm.items():
        r['D_%s' % s] = v
        r['n_%s' % s] = n
        mm = (segi == s)[:n_days]
        for k, c in (('req', 'v2_req'), ('within', 'v2_within'), ('cross', 'v2_cross'), ('unm', 'v2_unm'), ('nreq', 'v2_nreq'), ('nunm', 'v2_nunm'), ('ovb', 'ov_B'), ('ovx', 'ov_X'),
                     ('gn', 'ov_gated_n'), ('gv', 'ov_gated_val'), ('ershort', 'er_short'), ('nodes', 'er_nodes')):
            r['%s_%s' % (k, s)] = float(DY[mm, E.DYI[c]].sum())
        r['dwmax_%s' % s] = float(DY[mm, E.DY_ERDW].max()) if mm.any() else 0.0
        r['dw2max_%s' % s] = float(DY[mm, E.DY_ERDW2].max()) if mm.any() else 0.0
        for code, nm in ((1, 'erfeas'), (2, 'ernom'), (3, 'erlim'), (4, 'erid'), (5, 'erdeg')):
            r['%s_%s' % (nm, s)] = int(DY[mm, E.DY_ERC1 + code - 1].sum())        # 常规 + 额外批次的抽样计数
        r['ercoh_%s' % s] = int(((DY[mm, E.DY_OVCN] > 0)).sum())
        r['ovbown_%s' % s] = float(oovb[mm].sum())                     # 闭环层：owner 同日常规批次 B（random_tilt_feasibility）
        r['ercohown_%s' % s] = int((oocn[mm] > 0).sum())
        sd = (segi[pin_[:, E.IN_DAY]] == s) if nin else np.zeros(0, bool)
        so = (segi[o_day] == s) if len(o_day) else np.zeros(0, bool)
        r['pint_%s' % s] = int(sd.sum())
        r['oint_%s' % s] = int(so.sum())
        r['pval_%s' % s] = float(pf_[sd, 0].sum()) if nin else 0.0
        r['oval_%s' % s] = float(o_val[so].sum()) if len(o_val) else 0.0
    return r


def daily_pack(DY):
    nav = DY[:, E.DYI['nav_post']]
    vprev = np.r_[O.V0, nav[:-1]]
    return dict(ne=DY[:, E.DYI['net_excess']].astype(np.float32), feefr=(DY[:, E.DYI['fee']] / vprev).astype(np.float32),
                expo=DY[:, E.DYI['exposure']].astype(np.float32), cash=DY[:, E.DYI['cash_share']].astype(np.float32),
                turn=(0.5 * DY[:, E.DYI['traded']] / np.where(nav > 0, nav, 1.0)).astype(np.float32), s05=DY[:, E.DYI['cost_s05']].astype(np.float32),
                s07=DY[:, E.DYI['cost_s07']].astype(np.float32), s10=DY[:, E.DYI['cost_s10']].astype(np.float32), req=DY[:, E.DYI['v2_req']].astype(np.float32),
                unm=DY[:, E.DYI['v2_unm']].astype(np.float32), ovx=DY[:, E.DY_OVX].astype(np.float32), erst=DY[:, E.DY_ERST].astype(np.int8),
                nint=DY[:, E.DYI['n_intents']].astype(np.float32))


def job_random(args):
    phase, row, ref_h, mech, paths, ck_on = args
    n_days = d_end(phase)
    dA = d19()
    rows = []
    try:
        key = (phase, row['exec_hash'], mech)
        if key not in _CACHE:
            _CACHE.clear()
            _CACHE[key] = owner_targets(phase, row, mech) if mech in EXIT_MECH else None
            _CACHE[('P', phase, ref_h)] = np.load(res_path(phase, ref_h), allow_pickle=False)['DY'][:, E.DYI['net_excess']]
            z = np.load(res_path(phase, row['exec_hash']), allow_pickle=False)
            _CACHE[('O', phase, row['exec_hash'])] = (z['IN_i'], z['IN_f'], z['DY'][:, E.DY_OVB].copy(), z['DY'][:, E.DY_OVCN].copy())
        tg = _CACHE[key]
        pne = _CACHE[('P', phase, ref_h)]
        oin, oif, oovb, oocn = _CACHE[('O', phase, row['exec_hash'])]
        sel = EXIT_MECH.get(mech, E.SM_REAL)
        ernd = ENTRY_MECH.get(mech, E.ER_NONE)
        fhit = 1 if mech == 'BERNOULLI_FIRSTHIT' else 0
        daily = {k: [] for k in DCOLS} if (phase == 'B' and paths[0] == 0) else None
        for path in paths:
            seed = O.path_seed(row['logical_id'], mech, path)
            acc = build(row, sel=sel, seed=seed, targets=tg, fhit=fhit, ernd=ernd)
            ph = path_hash(row['exec_hash'], mech, path)
            restored = 0
            ck_equal = ''
            a2row = None
            if phase == 'A2':
                acc.run(0, dA)
            else:
                cp = ckpt_path(ph, 'A2_rand')
                if ck_on and os.path.exists(cp) and path == 0:
                    # 每个 (owner, 机制) 的 0 号路径：整段重跑作主读数（并写日序列），另从 A2 末状态续跑一份逐位比对（续跑等价核验）
                    acc.run(0, n_days)
                    acc2 = build(row, sel=sel, seed=seed, targets=tg, fhit=fhit, ernd=ernd)
                    acc2.restore(cp)
                    acc2.run(dA, n_days)
                    ck_equal = int(np.array_equal(acc.DY[dA:n_days], acc2.DY[dA:n_days], equal_nan=True) and np.array_equal(np.delete(acc.S_i, E.SI_NL), np.delete(acc2.S_i, E.SI_NL)))
                elif ck_on and os.path.exists(cp):
                    a2row = acc.restore(cp)['a2_row']
                    acc.run(dA, n_days)
                    restored = 1
                else:
                    acc.run(0, n_days)
            DY = acc.DY[:n_days]
            r = path_row(row, mech, path, seed, phase, acc, DY, pne[:n_days], n_days, oin, oif, oovb[:n_days], oocn[:n_days])
            if a2row is not None:
                # 续跑路径的 DY 推导段行未存（checkpoint 不存 DY）：推导段字段取 A2 同一路径的读数（确定性同值），后段字段取本次续跑
                for k, v in a2row.items():
                    if any(k.endswith('_' + s) for s in O.DERIV_SEGS):
                        r[k] = v
            if phase == 'A2' and ck_on:
                acc.checkpoint_compact(ckpt_path(ph, 'A2_rand'), dict(owner=row['exec_id'], mech=mech, path=int(path), day=dA, seed=str(seed), a2_row=r))
            r['restored'] = restored
            r['ck_equal'] = ck_equal
            rows.append(r)
            if daily is not None and path == 0 and not restored:
                for k, v in daily_pack(DY).items():
                    daily[k].append(v)
        if daily is not None and daily['ne']:
            d = O.P('randoms', 'daily', row['exec_hash'][:2])
            os.makedirs(d, exist_ok=True)
            O.atomic_write_npz(os.path.join(d, '%s_%s_0000.npz' % (row['exec_hash'], mech)), path_id=np.array([0]),
                               seed=np.array([str(rows[0]['seed'])]), **{k: np.stack(v) for k, v in daily.items()})
        return rows
    except Exception as e:
        return [dict(owner_exec_id=row['exec_id'], mechanism=mech, path_id=-1, phase=phase, status='FAILED', err='%s: %s' % (type(e).__name__, str(e)[:300]),
                     tb=traceback.format_exc()[-900:])]


def random_jobs(phase, batch, path_lo=0, path_hi=None, refs=None, mechs=None, ck_on=True):
    R = G['R']
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6r.csv'))
    Rl = R.set_index('logical_id', drop=False)
    byid = R.set_index('exec_id', drop=False)
    jobs = []
    for r in RR.itertuples(index=False):
        if refs is not None and r.ref_id not in refs:
            continue
        if mechs is not None and r.mechanism not in mechs:
            continue
        row = Rl.loc[r.owner_logical_id].to_dict()
        mech = r.mechanism
        hi = int(r.start_paths) if path_hi is None else path_hi
        lo = path_lo
        if r.draw_kind == 'DETERMINISTIC':
            if lo > 0:
                continue
            hi = 1
        refc = 'flat_same_exit_exec_id' if r.layer == 'ENTRY' else 'noexit_same_overlay_exec_id'
        ref_h = byid.loc[row[refc]].exec_hash
        for b0 in range(lo, hi, batch):
            jobs.append((phase, row, ref_h, mech, list(range(b0, min(hi, b0 + batch))), ck_on))
    jobs.sort(key=lambda j: (j[1]['exec_hash'], j[3], j[4][0]))
    return jobs


def write_random_rows(rows, tag):
    D = pd.DataFrame(rows)
    p = O.P('randoms', 'random_paths_%s.csv' % tag)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    O.atomic_write_csv(p, D.drop(columns=[c for c in ('tb',) if c in D.columns]))
    return D, p


def run_resumable(jobs, workers, tag, label):
    """随机批次：每 3,000 批原子落盘一次部分结果（randoms/random_paths_<tag>.partial.csv）；重启时跳过已完成批次（同 owner × 机制 × 路径）。"""
    part = O.P('randoms', 'random_paths_%s.partial.csv' % tag)
    done_rows = []
    if os.path.exists(part):
        P0 = O.read_csv(part)
        P0 = P0[P0.status == 'OK']
        done_rows = P0.to_dict('records')
        done = set(zip(P0.owner_exec_id, P0.mechanism, P0.path_id.astype(int)))
        jobs = [j for j in jobs if not all((j[1]['exec_id'], j[3], p) in done for p in j[4])]
        O.log('%s 续跑：已完成 %d 行，剩余 %d 批' % (label, len(P0), len(jobs)))
    t0 = time.time()
    rows = list(done_rows)

    def take(i, r):
        rows.extend(r)
        if any(x.get('status') == 'FAILED' for x in r):
            O.log('%s FAILED %s' % (label, r[0].get('err', '')))
        if (i + 1) % 3000 == 0:
            os.makedirs(os.path.dirname(part), exist_ok=True)
            O.atomic_write_csv(part, pd.DataFrame(rows).drop(columns=['tb'], errors='ignore'))
            O.log('%s %d/%d 批（%.0f s；已落盘）' % (label, i + 1, len(jobs), time.time() - t0))
    specs = pool_specs()
    if specs and jobs:
        run_pools(specs, jobs, take, label)
        return rows, time.time() - t0
    ctx = get_context('fork')
    with ctx.Pool(min(workers, max(1, len(jobs)))) as pool:
        for i, r in enumerate(pool.imap_unordered(job_random, jobs, chunksize=1)):
            take(i, r)
    return rows, time.time() - t0


def _cpuset(s):
    out = set()
    for part in s.split(','):
        a, _, b = part.partition('-')
        out.update(range(int(a), int(b or a) + 1))
    return out


def pool_specs():
    """E6R_POOLS = '<cpus>:<n>[:<cd，相对 E6R_WORK>[:<tail>]];…'：每路一个 fork 池（只管调度与内存放置，不改计算）。第一项沿用 setup() 的市场状态；
    带 cd 的项在该路 CPU 上从 cd（市场缓存六个子目录的逐字节副本）重建市场与形成层后再 fork，使该路 worker 读本路内存。
    tail > 0 的池（慢路，47 的 socket 0 被限频，单 worker 约为 node1 的 1 / 4–1 / 6，notes §8）：不排队（在途 = n），
    未派发批数 < tail 后不再给它派新批，避免每轮末尾等慢路。未设则单池（原路径）。"""
    out = []
    for part in [p for p in os.environ.get('E6R_POOLS', '').split(';') if p.strip()]:
        f = part.split(':')
        out.append((_cpuset(f[0]), int(f[1]), os.path.join(O.work(), f[2]) if len(f) > 2 and f[2] else None,
                    int(f[3]) if len(f) > 3 and f[3] else 0))
    return out


def local_state(cd):
    """与 setup() 同式重建市场与形成层（不预编译）：调用时父进程已绑在目标路 CPU 上，新分配落在本路。"""
    mk = A.Market(cd=cd)
    for f in O.FORMS:
        for m in O.MEMS:
            mk.formation(f, m)
            mk.overlay(f, m)
    mk.formation(O.MAIN_FORM, 'HG10', w15=True)
    g = dict(G)
    g['mk'] = mk
    g['segi'] = O.segs_of_dates(mk.dates)
    return g


def run_pools(specs, jobs, take, label):
    """多池派发：哪个池先空出来就派给哪个池（动态均衡）；每批仍是 job_random(同一参数)，结果与单池 imap_unordered 逐位相同，只是完成顺序不同。"""
    ctx = get_context('fork')
    home = os.sched_getaffinity(0)
    g_home = dict(G)
    pools = []
    try:
        for cpus, n, cd, _ in specs:
            os.sched_setaffinity(0, cpus)
            if cd:
                G.clear()
                G.update(local_state(cd))
            pools.append(ctx.Pool(n))
            G.clear()
            G.update(g_home)
        os.sched_setaffinity(0, home)
        O.log('%s 多池：%s workers（%d 批；慢路收尾阈值 %s）' % (label, ' + '.join(str(s[1]) for s in specs), len(jobs),
                                                         ' / '.join(str(s[3]) for s in specs)))
        q = queue.Queue()
        it = iter(jobs)
        busy = [0] * len(pools)
        cnt = [0] * len(pools)
        sent = [0]
        tail = [s[3] for s in specs]
        has_free = any(t == 0 for t in tail)

        def submit(k):
            if tail[k] and has_free and len(jobs) - sent[0] < tail[k]:
                return
            j = next(it, None)
            if j is not None:
                sent[0] += 1
                busy[k] += 1
                pools[k].apply_async(job_random, (j,), callback=lambda r, k=k: q.put((k, r)), error_callback=lambda e, k=k: q.put((k, e)))

        # 快路在途 2n（每个 worker 1 个在算 + 1 个排队）：父进程写部分结果期间不断粮；慢路（tail > 0）在途 n、不排队
        for k, s in enumerate(specs):
            for _ in range(s[1] if tail[k] else 2 * s[1]):
                submit(k)
        i = 0
        while sum(busy):
            k, r = q.get()
            busy[k] -= 1
            if isinstance(r, BaseException):
                raise r
            cnt[k] += 1
            submit(k)
            take(i, r)
            i += 1
            if i % 3000 == 0 or not sum(busy):
                O.log('%s 各池完成批数：%s（每 worker：%s）' % (label, ' / '.join(str(c) for c in cnt),
                                                      ' / '.join('%.1f' % (c / s[1]) for c, s in zip(cnt, specs))))
    finally:
        G.clear()
        G.update(g_home)
        for p in pools:
            p.terminate()
            p.join()


def cmd_randoms(a):
    gate(a.phase, 'randoms')
    setup()
    G['R'] = registry()
    jobs = random_jobs(a.phase, a.batch, mechs=set(a.mechs.split(',')) if a.mechs else None, ck_on=not a.no_ckpt)
    O.log('randoms %s：%d 批（checkpoint %s）' % (a.phase, len(jobs), 'on' if not a.no_ckpt else 'off'))
    out, w = run_resumable(jobs, a.workers, a.tag or a.phase, 'randoms %s' % a.phase)
    D, p = write_random_rows(out, a.tag or a.phase)
    nf = int((D.status == 'FAILED').sum())
    O.write_receipt('E6r_randoms_%s' % (a.tag or a.phase), [p], code=[__file__, E.__file__, A.__file__], rows=len(D), failed=nf, wall_s=round(w, 1),
                    restored=int(D.get('restored', pd.Series([0])).astype(float).sum()) if len(D) else 0,
                    rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.log('randoms %s 完成：%d 行，失败 %d，%.0f s' % (a.phase, len(D), nf, w))
    if nf:
        print(D[D.status == 'FAILED'].head(5).to_string()[:3000], flush=True)
        sys.exit(1)


def full_D(df):
    num = 0.0
    den = 0
    for s in O.SEGS:
        v = pd.to_numeric(df['D_%s' % s], errors='coerce').to_numpy(float)
        n = pd.to_numeric(df['n_%s' % s], errors='coerce').to_numpy(float)
        num = num + np.nan_to_num(v) * n
        den = den + n
    with np.errstate(all='ignore'):
        return num / den


def cmd_topup(a):
    gate('B', 'topup')
    setup()
    G['R'] = registry()
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6r.csv'))
    tgt = RR[(RR.draw_kind == 'STOCHASTIC') & (RR.mcse_target != '')]
    base = O.read_csv(O.P('randoms', 'random_paths_B.csv'))
    extra = []
    k = 0
    while True:
        k += 1
        cur = pd.concat([base] + extra) if extra else base
        cur = cur[cur.status == 'OK']
        g = {key: x for key, x in cur.groupby(['owner_exec_id', 'mechanism'])}
        need = []
        for r in tgt.itertuples(index=False):
            x = g.get((r.owner_exec_id, r.mechanism))
            n = 0 if x is None else len(x)
            if n == 0:
                continue
            fd = full_D(x)
            mcse = float(np.nanstd(fd, ddof=1) / np.sqrt(n)) if n > 1 else np.inf
            mx = int(r.max_paths)
            if mcse > float(r.mcse_target) and n < mx:
                nxt = 512 if n < 512 else 1024
                need.append((r.ref_id, n, min(mx, nxt)))
        O.log('topup 第 %d 轮：%d 条引用未达 MCSE ≤ .01（FULL）' % (k, len(need)))
        if not need:
            break
        jobs = []
        for rid, n, hi in need:
            jobs += random_jobs('B', a.batch, path_lo=n, path_hi=hi, refs={rid}, ck_on=False)
        out, w = run_resumable(jobs, a.workers, 'B_topup_r%d' % k, 'topup B r%d' % k)
        D = pd.DataFrame(out)
        if (D.status == 'FAILED').any():
            print(D[D.status == 'FAILED'].head(5).to_string()[:3000], flush=True)
            sys.exit(1)
        extra.append(D.astype(str))
        write_random_rows(pd.concat(extra).to_dict('records'), 'B_topup')
    D, p = write_random_rows(pd.concat(extra).to_dict('records') if extra else [], 'B_topup')
    O.write_receipt('E6r_randoms_B_topup', [p], code=[__file__], rows=len(D), rounds=k)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['accounts', 'feedback', 'shadow', 'randoms', 'topup'])
    ap.add_argument('--phase', choices=['A2', 'B'], required=True)
    ap.add_argument('--workers', type=int, default=96)
    ap.add_argument('--only', default='')
    ap.add_argument('--mechs', default='')
    ap.add_argument('--batch', type=int, default=8)
    ap.add_argument('--tag', default='')
    ap.add_argument('--no-ckpt', dest='no_ckpt', action='store_true')
    a = ap.parse_args()
    sp = pool_specs()
    if sp:
        os.sched_setaffinity(0, sp[0][0])  # 多池：父进程与 setup() 的分配放在第一路（第一池沿用此状态）
    {'accounts': cmd_accounts, 'feedback': cmd_feedback, 'shadow': cmd_shadow, 'randoms': cmd_randoms, 'topup': cmd_topup}[a.cmd](a)


if __name__ == '__main__':
    main()
