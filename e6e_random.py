#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6e 阶段 E: 随机对照。U-IID / I-IID / I-P5 各 128 路径; 软起点另 I-IID / I-P20。
   每条路径独立: 名单 -> DEV -> H5 -> 逐日 gross/成本/net。严禁先平均权重再跑一次引擎。
   循环序 = profile -> seed -> rule, 使每个 (profile,seed) 的优先级只生成一次且不常驻。
   用法: python e6e_random.py --period SEG --shard i --nshard N --out DIR
"""
import os, sys, time, json, argparse
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K

ap = argparse.ArgumentParser()
ap.add_argument('--period', required=True); ap.add_argument('--shard', type=int, required=True)
ap.add_argument('--nshard', type=int, required=True); ap.add_argument('--out', required=True)
ap.add_argument('--paths', type=int, default=128)
A = ap.parse_args()
OUT, PN, SH, NSH, RPATH = A.out, A.period, A.shard, A.nshard, A.paths
TAG = '%s_s%02d' % (PN, SH)
os.makedirs(os.path.join(OUT, 'random_daily', PN), exist_ok=True)
LOG = open(os.path.join(OUT, 'logs', 'rand_%s.txt' % TAG), 'w', encoding='utf-8')


def P(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); LOG.write(s + '\n'); LOG.flush()


t0 = time.time()
S = K.load_segment(PN, verbose=False)
ICC, GG = S.icodes, S.G
tick_codes = np.arange(S.Nc, dtype=np.uint64)          # 冻结票码表 = ccols 顺序
dates_s = [str(d)[:10].replace('-', '') for d in S.dates]
P('[%s shard %d/%d] pipeline %.0fs T=%d Nc=%d G=%d' % (PN, SH, NSH, time.time() - t0, S.T, S.Nc, GG))

cores = K.core_descriptors()
mine = cores[SH::NSH]
hard = K.hard_veto_descriptors(); comp = K.composite_veto_descriptors()
exem = K.exemption_veto_descriptors()
full_tox = K.tox_masks(S)
tox = {k: K.toc(S, v) for k, v in full_tox.items()}
unsc = {f: K.toc(S, K.unscorable_mask(S, f)) for f in K.VF6}
EXTREME = K.extreme_masks(S); COLPOS = K.col_positions(S)
# 池级复合掩码只算一次 (part1 记录的 54 倍冗余在此修掉)
COMP_DROP = {vd['veto_id']: K.toc(S, K.veto_drop(S, vd, full_tox, unsc)[0]) for vd in comp}

PROFILES = ['U-IID', 'I-IID', 'I-P5']
SOFT_PROFILES = ['I-IID', 'I-P20', 'I-Q3', 'I-L3']     # 后两个 = 分层诊断 (§3.7)
RHO = {'I-P5': float(np.exp(-1.0 / 5)), 'I-P20': float(np.exp(-1.0 / 20))}
LAMS = [('WS', l) for l in (0.25, 0.5, 0.75, 1.0)] + [('WB', l) for l in (0.25, 0.5, 0.75)]

# 流动性分层用: 形成日可得的 20 日成交额均值 (至少 10 个有效日)
_amt = S.data.get('amount')
AMT20 = (_amt.rolling(20, min_periods=10).mean().values[:, S.ccols]
         if _amt is not None else np.full((S.T, S.Nc), np.nan))


def terciles(vals):
    """当日可观察成员内的三分位标签 0/1/2; 全 NaN 或过少记 3"""
    ok = ~np.isnan(vals)
    lab = np.full(len(vals), 3, np.int64)
    if ok.sum() >= 6:
        v = vals[ok]
        q1, q2 = np.nanpercentile(v, [33.3333, 66.6667])
        lab[ok] = (vals[ok] > q1).astype(np.int64) + (vals[ok] > q2).astype(np.int64)
    return lab

# ---------------- 规则清单 (先把每条规则的每日名单/剔除人数算好) ----------------
RULES = []
for d in mine:
    cid = d['core_id']
    bm, sc, pool = K.build_core(S, d)
    base = K.toc(S, bm)
    fullbase = np.zeros((S.T, S.Nfull), bool); fullbase[:, S.ccols] = base
    idxs = [np.where(base[t])[0] for t in range(S.T)]
    w0 = [K.dev_day(h, ICC[t], S.cap[t], GG) for t, h in enumerate(idxs)]   # 父核 DEV 权重
    # 分层标签: 行业 x 核质量三分位 / 行业 x 流动性三分位 (当日父核成员内定)
    ccnames = np.asarray(S.pool0.columns)[S.ccols]
    GQ, GL = [], []
    for t, h in enumerate(idxs):
        if len(h) == 0:
            GQ.append(np.zeros(0, np.int64)); GL.append(np.zeros(0, np.int64)); continue
        g = ICC[t][h]; gb = np.where(g >= 0, g, GG)
        s_ = sc.get(S.dates[t])
        if s_ is None:
            q = np.full(len(h), 3, np.int64)
        else:
            mp = dict(zip(np.asarray(s_.index), s_.values))
            q = terciles(np.array([mp.get(ccnames[j], np.nan) for j in h]))
        GQ.append(gb * 4 + q)
        GL.append(gb * 4 + terciles(AMT20[t][h]))
    def add(rid, dm, profiles, soft=False):
        m_t = np.empty(S.T, np.int64)
        cnts = {}
        for lab, garr in (('ind', None), ('q3', GQ), ('l3', GL)):
            cnts[lab] = None
        cI = np.zeros((S.T, GG + 1), np.int64)
        cQ = np.zeros((S.T, (GG + 1) * 4), np.int64)
        cL = np.zeros((S.T, (GG + 1) * 4), np.int64)
        for t in range(S.T):
            dd = np.where(base[t] & dm[t])[0]
            m_t[t] = len(dd)
            if len(dd):
                g = ICC[t][dd]
                cI[t] = np.bincount(np.where(g >= 0, g, GG), minlength=GG + 1)
                if soft:
                    pos = {v: i for i, v in enumerate(idxs[t])}
                    sel = np.array([pos[x] for x in dd])
                    cQ[t] = np.bincount(GQ[t][sel], minlength=(GG + 1) * 4)
                    cL[t] = np.bincount(GL[t][sel], minlength=(GG + 1) * 4)
        RULES.append(dict(rule_id=rid, core=cid, idxs=idxs, m_t=m_t, cI=cI, cQ=cQ, cL=cL,
                          GQ=GQ, GL=GL, w0=w0, profiles=profiles, soft=soft))
    for vd in hard:
        dm = np.zeros_like(base)
        for (f, k) in vd['legs']: dm |= tox[(f, k)]
        add('%s|%s' % (cid, vd['veto_id']), dm, PROFILES)
    if d['set'] == 'P54':
        for vd in comp:
            add('%s|%s' % (cid, vd['veto_id']), COMP_DROP[vd['veto_id']], PROFILES)
        for vd in exem:
            dfull, _ = K.veto_drop(S, vd, full_tox, unsc, core_mask=fullbase, core_score=sc,
                                   cand_pool=pool, extreme=EXTREME, colpos=COLPOS)
            add('%s|%s' % (cid, vd['veto_id']), K.toc(S, dfull), PROFILES)
        for st in K.SOFT_STARTS:
            add('%s|%s#soft' % (cid, st), K.toc(S, K.parse_start(S, st, full_tox)),
                SOFT_PROFILES, soft=True)
P('  规则清单 %d 条 (%d 个核) %.0fs' % (len(RULES), len(mine), time.time() - t0))


def gen_prio(profile, seed):
    """(T,Nc) 优先级; I-P* 走 AR(1), 状态按 ticker 沿全路径确定性重建 (与分片/并发无关)"""
    e = np.empty((S.T, S.Nc))
    for i, ds in enumerate(dates_s):
        e[i] = K.priorities(profile, seed, ds, tick_codes)
    if profile not in RHO:
        return e
    z = (e - 0.5) * np.sqrt(12.0)          # U(0,1) -> 零均值单位方差
    rho = RHO[profile]; c = np.sqrt(1.0 - rho * rho)
    out = np.empty_like(z); out[0] = z[0]
    for i in range(1, S.T):
        out[i] = rho * out[i - 1] + c * z[i]
    return out


def within_rank(held, pr, groups=None):
    """held 内按优先级降序的名次 (0 = 最先被剔); groups 给定则组内排名"""
    p = -pr[held]
    if groups is None:
        o = np.argsort(p, kind='stable')
        r = np.empty(len(held), np.int64); r[o] = np.arange(len(held))
        return r
    o = np.lexsort((p, groups))
    gs = groups[o]; n = len(held); ii = np.arange(n)
    start = np.empty(n, bool); start[0] = True
    if n > 1: start[1:] = gs[1:] != gs[:-1]
    base = np.maximum.accumulate(np.where(start, ii, 0))
    r = np.empty(n, np.int64); r[o] = ii - base
    return r


rows = []; DN = {}; DT = {}
npath = 0
for profile in sorted(set(PROFILES + SOFT_PROFILES)):
    rl = [r for r in RULES if profile in r['profiles']]
    if not rl: continue
    isU = profile.startswith('U')
    for b in range(RPATH):
        pr = gen_prio(profile, b)
        for r in rl:
            idxs, m_t = r['idxs'], r['m_t']
            if profile == 'I-Q3':
                garrs, cnts = r['GQ'], r['cQ']
            elif profile == 'I-L3':
                garrs, cnts = r['GL'], r['cL']
            else:
                garrs, cnts = None, r['cI']
            iv_i, iv_v, drop_i = [], [], []
            for t in range(S.T):
                h = idxs[t]
                if len(h) == 0 or m_t[t] == 0:
                    keep = h; rem = np.zeros(0, np.int64)
                elif isU:
                    rk = within_rank(h, pr[t]); sel = rk >= m_t[t]
                    keep = h[sel]; rem = h[~sel]
                else:
                    gg = (garrs[t] if garrs is not None
                          else np.where(ICC[t][h] >= 0, ICC[t][h], GG))
                    rk = within_rank(h, pr[t], gg); sel = rk >= cnts[t][gg]
                    keep = h[sel]; rem = h[~sel]
                iv_i.append(keep); drop_i.append(rem)
                iv_v.append(K.dev_day(keep, ICC[t], S.cap[t], GG))
            g_, p_, tn_, n_ = K.sparse_pnl(S, iv_i, iv_v)
            key = '%s@%s|b%03d' % (r['rule_id'], profile, b)
            DN[key] = n_; DT[key] = tn_
            a = K.annualize(S, g_, p_, tn_)
            a.update(period=PN, rule_id=r['rule_id'], core=r['core'], profile=profile, seed=b,
                     overlay='')
            rows.append(a); npath += 1
            if not r['soft']:
                continue
            # 软覆盖层: 复用同一随机剔除集合, 每个 λ 各自构造权重并算自身成本
            w0 = r['w0']
            for mode, lam in LAMS:
                if mode == 'WS':
                    vv = []
                    for t in range(S.T):
                        v = w0[t].copy()
                        if len(v) and len(drop_i[t]):
                            pos = np.searchsorted(idxs[t], drop_i[t])
                            v[pos] = v[pos] * (1.0 - lam)
                        vv.append(v)
                    ii = idxs
                else:
                    ii, vv = [], []
                    for t in range(S.T):
                        u = np.union1d(idxs[t], iv_i[t])
                        aa = np.zeros(len(u)); bb = np.zeros(len(u))
                        if len(idxs[t]): aa[np.searchsorted(u, idxs[t])] = w0[t]
                        if len(iv_i[t]): bb[np.searchsorted(u, iv_i[t])] = iv_v[t]
                        v = (1 - lam) * aa + lam * bb
                        nz = v != 0
                        ii.append(u[nz]); vv.append(v[nz])
                gs, ps, ts, ns = K.sparse_pnl(S, ii, vv)
                k2 = '%s~%s%.2f@%s|b%03d' % (r['rule_id'], mode, lam, profile, b)
                DN[k2] = ns; DT[k2] = ts
                a2 = K.annualize(S, gs, ps, ts)
                a2.update(period=PN, rule_id='%s~%s%.2f' % (r['rule_id'], mode, lam),
                          core=r['core'], profile=profile, seed=b, overlay='research_overlay')
                rows.append(a2); npath += 1
        if (b + 1) % 16 == 0:
            P('    %s seed %d/%d 累计路径 %d %.0fs' % (profile, b + 1, RPATH, npath, time.time() - t0))
    # 按 profile 分块落盘 (临时名 -> 校验行数 -> 原子改名), 保持内存有界
    for nm, dd in (('net8', DN), ('turn', DT)):
        if not dd: continue
        fp = os.path.join(OUT, 'random_daily', PN, '%s_%s_%s.parquet' % (nm, TAG, profile))
        tmp = fp + '.tmp'
        df = pd.DataFrame(dd, index=S.pool0.index)
        df.to_parquet(tmp)
        assert pd.read_parquet(tmp).shape == df.shape, 'shard 落盘行列不符'
        os.replace(tmp, fp)
    DN.clear(); DT.clear()
    P('  profile %s 完成 (规则 %d) 累计路径 %d %.0fs' % (profile, len(rl), npath, time.time() - t0))

pd.DataFrame(rows).to_csv(os.path.join(OUT, 'random_daily', PN, 'scalars_%s.csv' % TAG), index=False)
with open(os.path.join(OUT, '_DONE_E_%s' % TAG), 'w') as fh:
    fh.write('rules=%d paths=%d\n' % (len(RULES), npath))
P('[SHARD DONE] %s 规则 %d 路径 %d %.0fs' % (TAG, len(RULES), npath, time.time() - t0))
LOG.close()
