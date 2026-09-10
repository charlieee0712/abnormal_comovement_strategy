#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 块 B2 第二步: 政策账户 (§5.2)。一个进程 = 一个段 (主回放保留四段 reset)。
   W_T(policy) = Σ_j α_{j,D(T)} W_T(j), α 在前一选择日锁定; 整条政策路径一次过引擎,
   rolling 自然承接旧 vintage。
   用法: python e6f_b2_account.py --out DIR --period P
"""
import os, sys, json, time, argparse, collections
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K
import e6f_core as F
import e6f_desc as D
import e6f_blockA_lib as BA

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--period', required=True)
A = ap.parse_args()
PN = A.period
for d in ('B_walkforward', 'checks', 'logs', 'task_status'):
    os.makedirs(os.path.join(A.out, d), exist_ok=True)
_lf = open(os.path.join(A.out, 'logs', 'b2_acct_%s.log' % PN), 'w', encoding='utf-8', buffering=1)


def P(s=''):
    print(s, flush=True); _lf.write(s + '\n')


T0 = time.time()
P('=== B2 政策账户 [%s] === %s' % (PN, time.strftime('%Y-%m-%d %H:%M:%S')))
SEL = pd.read_csv(os.path.join(A.out, 'B_nested', 'selected_sets.csv'))
S = F.build_segment(PN, 'legacy_all')
ctx = BA.Ctx(S)
Sre = K.load_segment(PN, verbose=False)
DT = pd.DatetimeIndex(S.dates)
CF = {c['config_id']: c for c in D.gen_all()}

# ---- E6e 配置重建 ----
_e6e_cache = {}
_CD = {d['core_id']: d for d in K.core_descriptors() + K.twin_descriptors(K.core_descriptors())}
_tox = None
_full_tox = None
_unsc = None
_EXTREME = None
_COLPOS = None


def _lazy():
    global _tox, _full_tox, _unsc, _EXTREME, _COLPOS
    if _tox is None:
        _full_tox = K.tox_masks(Sre)
        _tox = {k: K.toc(Sre, v) for k, v in _full_tox.items()}
        _unsc = {f: K.toc(Sre, K.unscorable_mask(Sre, f)) for f in K.VF6}
        _EXTREME = K.extreme_masks(Sre)
        _COLPOS = K.col_positions(Sre)


VD = {v['veto_id']: v for v in (K.hard_veto_descriptors() + K.composite_veto_descriptors()
                                + K.exemption_veto_descriptors() + K.soft_descriptors())}


def rebuild(cid):
    """任意 config_id -> (idx, val) 形成日目标权重。UA:: 前缀走块 A 描述符, 否则走 E6e 路径。"""
    if cid in _e6e_cache:
        return _e6e_cache[cid]
    out = None
    if cid.startswith('UA::'):
        c = CF.get(cid[4:])
        if c is not None:
            out = F.dev_from_dense(S, ctx.full_mask(c)[0])
    else:
        core = cid.split('|')[0]
        vid = cid.split('|')[1] if '|' in cid else None
        d = _CD.get(core)
        if d is not None:
            m, sc, pool = K.build_core(Sre, d)
            base = K.toc(Sre, m)
            if vid is None:
                out = K.dev_from_mask(Sre, base)
            else:
                _lazy()
                vd = VD.get(vid)
                if vd is not None:
                    if vd['kind'] == 'hard':
                        dr = np.zeros_like(base)
                        for (f, k) in vd['legs']:
                            dr |= _tox[(f, k)]
                        out = K.dev_from_mask(Sre, base & ~dr)
                    elif vd['kind'] in ('composite', 'exempt'):
                        fb = np.zeros((Sre.T, Sre.Nfull), bool)
                        fb[:, Sre.ccols] = base
                        df, _ = K.veto_drop(Sre, vd, _full_tox, _unsc, core_mask=fb,
                                            core_score=sc, cand_pool=None,
                                            extreme=_EXTREME, colpos=_COLPOS)
                        out = K.dev_from_mask(Sre, base & ~K.toc(Sre, df))
                    elif vd['kind'] == 'soft':
                        pv = K.dev_from_mask(Sre, base)
                        d0 = K.toc(Sre, K.parse_start(Sre, vd['start'], _full_tox))
                        inD = base & d0
                        hv = K.dev_from_mask(Sre, base & ~d0)
                        lam = vd['lam']
                        if vd['mode'] == 'WS':
                            val = []
                            for t in range(Sre.T):
                                v = pv[1][t].copy()
                                if len(v):
                                    v[inD[t][pv[0][t]]] *= (1.0 - lam)
                                val.append(v)
                            out = (pv[0], val)
                        else:
                            idx2, val2 = [], []
                            for t in range(Sre.T):
                                u = np.union1d(pv[0][t], hv[0][t])
                                a_ = np.zeros(len(u)); b_ = np.zeros(len(u))
                                if len(pv[0][t]):
                                    a_[np.searchsorted(u, pv[0][t])] = pv[1][t]
                                if len(hv[0][t]):
                                    b_[np.searchsorted(u, hv[0][t])] = hv[1][t]
                                v = (1 - lam) * a_ + lam * b_
                                nz = v != 0
                                idx2.append(u[nz]); val2.append(v[nz])
                            out = (idx2, val2)
    _e6e_cache[cid] = out
    return out


need = sorted(set(SEL.config_id))
P('  需要重建的配置 %d 个' % len(need))
ok = 0
t1 = time.time()
for cid in need:
    if rebuild(cid) is not None:
        ok += 1
P('  重建成功 %d/%d, %.0fs' % (ok, len(need), time.time() - t1))

# ---- 验证: 重建的配置对已存账本 ----
GG = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_gross_%s.parquet' % PN))
TT = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_turn_%s.parquet' % PN))
ver = []
for cid in need:
    iv = _e6e_cache.get(cid)
    if iv is None or cid not in GG.columns:
        continue
    g, p_, u_, _ = F.sparse_pnl_H(S, iv[0], iv[1], 5)
    m = ~np.isnan(g) & ~np.isnan(GG[cid].values)
    ver.append(dict(config_id=cid, d_gross=float(np.max(np.abs(g[m] - GG[cid].values[m]))),
                    d_turn=float(np.max(np.abs(u_ - TT[cid].values)))))
if ver:
    VF = pd.DataFrame(ver)
    w = float(np.nanmax(VF[['d_gross', 'd_turn']].values))
    P('  重建对 E6e 账本: %d 个, max|d| = %.3e %s' % (len(VF), w, 'OK' if w < 1e-12 else 'FAIL'))
    VF.to_csv(os.path.join(A.out, 'checks', 'b2_rebuild_verify_%s.csv' % PN), index=False)


def policy_path(members_by_vintage, start_after=None):
    """members_by_vintage: {vintage_date(Timestamp): [(cid, alpha)]}
       形成日 T 用【≤T 的最近一个 vintage】的 α; start_after 之前不产生目标 (零库存起点)。"""
    vs = sorted(members_by_vintage)
    idx, val = [], []
    for t in range(S.T):
        day = DT[t]
        if start_after is not None and day <= start_after:
            idx.append(np.empty(0, int)); val.append(np.empty(0))
            continue
        act = None
        for v in vs:
            if v <= day:
                act = v
            else:
                break
        if act is None:
            idx.append(np.empty(0, int)); val.append(np.empty(0))
            continue
        acc = {}
        for cid, al in members_by_vintage[act]:
            iv = _e6e_cache.get(cid)
            if iv is None:
                continue
            for c, v in zip(iv[0][t], iv[1][t]):
                acc[c] = acc.get(c, 0.0) + al * v
        if acc:
            ks = np.fromiter(acc.keys(), int, len(acc))
            o = np.argsort(ks)
            idx.append(ks[o]); val.append(np.fromiter(acc.values(), float, len(acc))[o])
        else:
            idx.append(np.empty(0, int)); val.append(np.empty(0))
    return idx, val


# ---- 账户 ----
P('')
P('=== 政策账户 ===')
rows, daily = [], {}
R1, R2 = 'KT_dep(50,50)|C:k5', 'KT_mean@30|C:k5+cr5:k10'
for cid in (R1, R2):
    iv = rebuild(cid)
    if iv:
        g, p_, u_, _ = F.sparse_pnl_H(S, iv[0], iv[1], 5)
        daily['REF::' + cid] = (g, p_, u_)

grp = SEL.groupby(['domain', 'split', 'direction', 'variant', 'rule', 'account'])
n_rev_skip = 0
for key, sub in grp:
    dom, split, direc, var, rule, acct = key
    # 反向切分是【迁移诊断】不是可执行策略: 它的评估窗在训练窗【之前】, 建不出一条随时间前进的
    # 政策账户 (start_after=split 会把持仓落在训练窗上, 是错的)。反向只在 merge2 里出静态 b。
    if direc == 'reverse':
        n_rev_skip += 1
        continue
    mv = collections.defaultdict(list)
    for _, r in sub.iterrows():
        mv[pd.Timestamp(r.vintage)].append((r.config_id, float(r.weight)))
    if not mv:
        continue
    sa = pd.Timestamp(split) if acct == 'single' else None
    try:
        idx, val = policy_path(mv, start_after=sa)
    except Exception as e:
        P('  !! %s -> %s' % (str(key), e)); continue
    g, p_, u_, _ = F.sparse_pnl_H(S, idx, val, 5)
    nm = '%s|%s|%s|%s|%s|%s' % key
    daily[nm] = (g, p_, u_)
    m = ~np.isnan(g)
    n8 = g - u_ * (F.COST / 1e4)
    rows.append(dict(domain=dom, split=split, direction=direc, variant=var, rule=rule,
                     account=acct, period=PN, n_vintage=len(mv),
                     n_members=int(sub.config_id.nunique()),
                     net8=F.ann(n8), net12=F.ann(g - u_ * (F.COST_HI / 1e4)),
                     gross=F.ann(g), turn=252 * float(np.mean(u_[m])) if m.any() else np.nan,
                     pos=float(np.mean(p_[m])) if m.any() else np.nan,
                     days_valid=int(m.sum()),
                     active_days=int(np.sum([len(x) > 0 for x in idx]))))
AC = pd.DataFrame(rows)
AC.to_csv(os.path.join(A.out, 'B_walkforward', 'policy_accounts_%s.csv' % PN), index=False)
P('  政策账户 %d 条' % len(AC))
if len(AC):
    for acct in AC.account.unique():
        s = AC[AC.account == acct]
        P('  %-12s net8 中位 %+.3f (n=%d); 各规则中位: %s'
          % (acct, s.net8.median(), len(s),
             {k: round(v, 2) for k, v in s.groupby('rule').net8.median().items()}))
cols = sorted(daily)
for nm, k in (('gross', 0), ('pos', 1), ('turn', 2)):
    pd.DataFrame({c: daily[c][k] for c in cols}, index=DT).to_parquet(
        os.path.join(A.out, 'B_walkforward', 'policy_%s_%s.parquet' % (nm, PN)))
json.dump(dict(period=PN, n_accounts=len(AC), n_rebuilt=ok, n_needed=len(need),
               rebuild_max_abs_diff=(float(np.nanmax(VF[['d_gross', 'd_turn']].values))
                                     if ver else None),
               seconds=time.time() - T0),
          open(os.path.join(A.out, 'checks', 'b2_account_%s.json' % PN), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
P('')
P('B2 政策账户 [%s] 完成 %.0fs' % (PN, time.time() - T0))
_lf.close()
open(os.path.join(A.out, 'task_status', '_DONE_B2acct_%s' % PN), 'w').write(
    '%s n=%d\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), len(AC)))
