#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6e 阶段 B/C/D: 一段内的全部确定性配置与对照。
   用法: python e6e_run.py --period <seg> --out DIR
"""
import os, sys, time, json, argparse
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K

ap = argparse.ArgumentParser()
ap.add_argument('--period', required=True)
ap.add_argument('--out', required=True)
A = ap.parse_args()
OUT, PN = A.out, A.period
os.makedirs(os.path.join(OUT, 'daily'), exist_ok=True)
LOG = open(os.path.join(OUT, 'logs', 'run_%s.txt' % PN), 'w', encoding='utf-8')


def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True); LOG.write(s + '\n'); LOG.flush()


t0 = time.time()
S = K.load_segment(PN)
cols = np.asarray(S.pool0.columns)
rows = []
D_gross, D_pos, D_turn = {}, {}, {}
STATE = {}


def evaluate(cid, mask=None, idxval=None, **meta):
    if idxval is None:
        idx, val = K.dev_from_mask(S, mask)
    else:
        idx, val = idxval
    g, p, tn, _ = K.sparse_pnl(S, idx, val)
    a = K.annualize(S, g, p, tn)
    nh = np.fromiter((len(i) for i in idx), float, S.T)
    a.update(period=PN, config_id=cid, avg_nh=float(nh[nh > 0].mean()) if (nh > 0).any() else np.nan,
             days_nohold=int((nh == 0).sum()), **meta)
    rows.append(a)
    D_gross[cid] = g; D_pos[cid] = p; D_turn[cid] = tn
    STATE[cid] = 'DONE'
    return g, p, tn, (idx, val)


def wsum_daily(val):
    return np.fromiter((v.sum() if len(v) else 0.0 for v in val), float, S.T)


def scale_weights(val, f):
    return [v * f[t] if len(v) else v for t, v in enumerate(val)]


# ================== 阶段 B: P114 核 + 双胞胎 ==================
cores = K.core_descriptors(); twins = K.twin_descriptors(cores)
_LIM = int(os.environ.get("E6E_LIMIT", "0"))
if _LIM:
    keep = set([c["core_id"] for c in cores[:2]] + ["KT_dep(50,50)", "KT_mean", "KT_mean", "KT_mean", "K_gate_TC(70,35)", "KT_dep_nr(50,50)"])
    cores = [c for c in cores if c["core_id"] in keep]
    twins = [t for t in K.twin_descriptors(cores)]
    P("  [LIMIT] 只跑 %d 个核 (冒烟)" % len(cores))
CM, CS, CP, CIV = {}, {}, {}, {}
alias = []
for d in cores + twins:
    cid = d['core_id']
    m, sc, pool = K.build_core(S, d)
    CM[cid] = K.toc(S, m); CS[cid] = sc; CP[cid] = pool
    if d.get('variant') != 'main':
        base = cid.split('#')[0]
        if base in CM and K.msha(CM[base]) == K.msha(CM[cid]):
            alias.append(dict(period=PN, config_id=cid, alias_of=base, reason='mask identical'))
            STATE[cid] = 'ALIAS'; continue
    g, p, tn, iv = evaluate(cid, mask=m, kind='core', family=d['family'], cset=d['set'],
                            variant=d.get('variant', 'main'), sha=K.msha(CM[cid]))
    CIV[cid] = iv
P('  [B] 核 %d + 双胞胎 %d (别名 %d) %.0fs' % (len(cores), len(twins), len(alias), time.time() - t0))

P114 = [d['core_id'] for d in cores]
P54 = [d['core_id'] for d in cores if d['set'] == 'P54']

# ---- 内部锚 ----
anch = []
def ianchor(nm, a, b):
    ok = (K.msha(a) == K.msha(b))
    anch.append(dict(period=PN, anchor=nm, kind='internal_sha', ok=bool(ok)))
    P('    [内锚] %-28s %s' % (nm, 'SAME OK' if ok else 'DIFF (软锚, 记录不中止)'))
a4b_dep = CM.get('KT_dep(50,50)')
if a4b_dep is not None:
    s1 = K.keep_pct_mask(S.opct[K.FK], S.pool0, 50)
    S1 = pd.DataFrame(s1.astype(float), index=S.pool0.index, columns=S.pool0.columns)
    a4b = K.keep_pct_mask(K.pct_or(K.C.precompute_neutralized_factor(S.raw[K.FT], S1, S.log_mcap),
                                   K.HB[K.FT]), S1, 50)
    ianchor('KT_dep(50,50) == A4b', a4b_dep, K.toc(S, a4b))
if 'KT_mean@50' in CM:
    mm2 = K.keep_pct_mask(K.combine([S.opct[K.FK], S.opct[K.FT]], 'mean'), S.pool0, 50)
    ianchor('KT_mean@50 == M_mean2', CM['KT_mean@50'], K.toc(S, mm2))

# ---- 外部锚 (E6b / E6d) ----
e6b = pd.read_csv(os.path.join(K.E6B_DIR, 'scan_all.csv')).set_index('cfg')
ycol = 'net_%s' % PN[:4]
EXT = {'A4b': ('KT_dep(50,50)', None), 'M_mean2@keep30': ('KT_mean@30', None),
       'M_mean2@keep20': ('KT_mean@20', None)}
for src, (cid, _) in EXT.items():
    if cid not in CM or src not in e6b.index: continue
    got = [r['net8_ann'] for r in rows if r['config_id'] == cid][0]
    a_ = float(e6b.loc[src, ycol]); dd = abs(got - a_)
    anch.append(dict(period=PN, anchor='E6b:' + src, kind='external', got=got, ref=a_, dabs=dd,
                     ok=bool(dd < 0.02)))
    P('    [外锚 E6b] %-20s got %+8.4f ref %+8.4f |d|%.8f %s'
      % (src, got, a_, dd, 'OK' if dd < 0.02 else 'FAIL'))

# ================== 阶段 C: 硬否决 + 对照 ==================
CCPOS = {c: i for i, c in enumerate(np.asarray(S.pool0.columns)[S.ccols])}
COLPOS = K.col_positions(S)
EXTREME = K.extreme_masks(S)
tox = {k: K.toc(S, v) for k, v in K.tox_masks(S).items()}
unsc = {f: K.toc(S, K.unscorable_mask(S, f)) for f in K.VF6}
hard = K.hard_veto_descriptors()
p0c = S.p0c


def coretrim(cid, r_t):
    """在父核内按末级质量分保留恰好 r_t 只 (§3.1)"""
    sc = CS[cid]; base = CM[cid]
    m = np.zeros_like(base)
    for i, dd in enumerate(S.dates):
        r = int(r_t[i])
        if r <= 0: continue
        s = sc.get(dd)
        if s is None: continue
        inc = np.isin(np.asarray(s.index), cols[S.ccols][base[i]])
        s2 = s[inc]
        if len(s2) == 0: continue
        r = min(r, len(s2))
        order = np.lexsort((np.asarray(s2.index), s2.values))
        sel = np.asarray(s2.index)[order[:r]]
        m[i, [CCPOS[x] for x in sel]] = True
    return m


def eqpos(cid_parent, cid_child, pv, cv, tag):
    """等仓位配对 (§3.6): 只向下缩"""
    P0 = wsum_daily(pv[1]); P1 = wsum_daily(cv[1])
    f0 = np.where(P0 > 0, np.minimum(1.0, np.divide(P1, P0, out=np.zeros_like(P0), where=P0 > 0)), 0.0)
    f1 = np.where(P1 > 0, np.minimum(1.0, np.divide(P0, P1, out=np.zeros_like(P1), where=P1 > 0)), 0.0)
    evaluate(cid_parent + '||eqpos_par@' + tag, idxval=(pv[0], scale_weights(pv[1], f0)),
             kind='eqpos_parent', parent=cid_parent, child=cid_child)
    evaluate(cid_child + '||eqpos_chd', idxval=(cv[0], scale_weights(cv[1], f1)),
             kind='eqpos_child', parent=cid_parent, child=cid_child)


tri = []          # 三值逻辑计数
nC = 0
for cid in P114:
    base = CM[cid]; pv = CIV[cid]
    nbase = base.sum(axis=1)
    for vd in hard:
        vid = vd['veto_id']
        drop = np.zeros_like(base)
        uu = np.zeros_like(base)
        for (f, k) in vd['legs']:
            drop |= tox[(f, k)]; uu |= unsc[f]
        child = base & ~drop
        cid2 = '%s|%s' % (cid, vid)
        g, p, tn, cv = evaluate(cid2, mask=child, kind='hard', core=cid, veto=vid, parent=cid)
        nC += 1
        # 三值逻辑
        kt = int((base & drop & ~uu).sum()); un = int((base & drop & uu).sum())
        tri.append(dict(period=PN, config_id=cid2, known_toxic=kt, unscorable_removed=un,
                        known_non_toxic=int((base & ~drop).sum())))
        # known_only 双胞胎
        evaluate(cid2 + '#ko', mask=base & ~(drop & ~uu), kind='known_only', core=cid, veto=vid, parent=cid)
        # 同人数剔深
        evaluate(cid2 + '#trim', mask=coretrim(cid, child.sum(axis=1)), kind='coretrim',
                 core=cid, veto=vid, parent=cid)
        # 等仓位
        eqpos(cid, cid2, pv, cv, vid)
    # 反向否决: 同父同有效域剔最好 m_t 只 (单否决 12)
    for vd in hard[:12]:
        (f, k) = vd['legs'][0]
        m_t = (base & tox[(f, k)] & ~unsc[f]).sum(axis=1)
        sc = CS[cid]; rev = base.copy()
        for i, dd in enumerate(S.dates):
            mm = int(m_t[i])
            if mm <= 0: continue
            s = sc.get(dd)
            if s is None: continue
            inc = np.isin(np.asarray(s.index), cols[S.ccols][base[i]])
            s2 = s[inc]
            if len(s2) == 0: continue
            order = np.lexsort((np.asarray(s2.index), s2.values))
            bestk = np.asarray(s2.index)[order[:min(mm, len(s2))]]
            rev[i, [CCPOS[x] for x in bestk]] = False
        evaluate('%s|rev_%s' % (cid, vd['veto_id']), mask=rev, kind='reverse',
                 core=cid, veto=vd['veto_id'], parent=cid)
P('  [C] 硬否决 %d 及对照完成 %.0fs (累计配置 %d)' % (nC, time.time() - t0, len(rows)))

# ================== 阶段 D: P54 复合 / 豁免 / 软 ==================
comp = K.composite_veto_descriptors(); exem = K.exemption_veto_descriptors()
soft = K.soft_descriptors()
full_tox = K.tox_masks(S)
for cid in P54:
    base = CM[cid]; pv = CIV[cid]
    fullbase = np.zeros((S.T, S.Nfull), bool); fullbase[:, S.ccols] = base
    for vd in comp + exem:
        drop_full, info = K.veto_drop(S, vd, full_tox, unsc, core_mask=fullbase,
                                      core_score=CS[cid], cand_pool=CP[cid],
                                      extreme=EXTREME, colpos=COLPOS)
        drop = K.toc(S, drop_full)
        child = base & ~drop
        cid2 = '%s|%s' % (cid, vd['veto_id'])
        g, p, tn, cv = evaluate(cid2, mask=child, kind=vd['kind'], core=cid,
                                veto=vd['veto_id'], parent=cid)
        evaluate(cid2 + '#trim', mask=coretrim(cid, child.sum(axis=1)), kind='coretrim',
                 core=cid, veto=vd['veto_id'], parent=cid)
        eqpos(cid, cid2, pv, cv, vd['veto_id'])
    # 软否决
    for st in K.SOFT_STARTS:
        d0 = K.toc(S, K.parse_start(S, st, full_tox))
        inD = base & d0
        hardm = base & ~d0
        hv = K.dev_from_mask(S, hardm)
        w0 = pv[1]
        for vd in [x for x in soft if x['start'] == st]:
            lam = vd['lam']
            if vd['mode'] == 'WS':
                val = []
                for t in range(S.T):
                    v = w0[t].copy()
                    if len(v):
                        inm = inD[t][pv[0][t]]
                        v[inm] = v[inm] * (1.0 - lam)
                    val.append(v)
                iv = (pv[0], val)
            else:
                # WB: (1-lam)W0 + lam*WH, 两套支持并集
                val = []; idx = []
                for t in range(S.T):
                    u = np.union1d(pv[0][t], hv[0][t])
                    a_ = np.zeros(len(u)); b_ = np.zeros(len(u))
                    if len(pv[0][t]): a_[np.searchsorted(u, pv[0][t])] = w0[t]
                    if len(hv[0][t]): b_[np.searchsorted(u, hv[0][t])] = hv[1][t]
                    v = (1 - lam) * a_ + lam * b_
                    nz = v != 0
                    idx.append(u[nz]); val.append(v[nz])
                iv = (idx, val)
            evaluate('%s|%s' % (cid, vd['veto_id']), idxval=iv, kind='soft', core=cid,
                     veto=vd['veto_id'], parent=cid, overlay='research_overlay')
P('  [D] P54 复合/豁免/软完成 %.0fs (累计配置 %d)' % (time.time() - t0, len(rows)))

# ================== 落盘 ==================
sf = pd.DataFrame(rows)
sf.to_csv(os.path.join(OUT, 'summary', 'sf_%s.csv' % PN), index=False)
for nm, dd in (('gross', D_gross), ('pos', D_pos), ('turn', D_turn)):
    pd.DataFrame(dd, index=S.pool0.index).to_parquet(
        os.path.join(OUT, 'daily', 'daily_%s_%s.parquet' % (nm, PN)))
pd.DataFrame(anch).to_csv(os.path.join(OUT, 'checks', 'anchors_%s.csv' % PN), index=False)
pd.DataFrame(tri).to_csv(os.path.join(OUT, 'summary', 'three_valued_%s.csv' % PN), index=False)
if alias: pd.DataFrame(alias).to_csv(os.path.join(OUT, 'summary', 'alias_%s.csv' % PN), index=False)
json.dump(STATE, open(os.path.join(OUT, 'summary', 'state_%s.json' % PN), 'w'))
with open(os.path.join(OUT, '_DONE_BCD_%s' % PN), 'w') as fh:
    fh.write('configs=%d\n' % len(rows))
P('[PERIOD DONE] %s 配置 %d 个 %.0fs' % (PN, len(rows), time.time() - t0))
LOG.close()
