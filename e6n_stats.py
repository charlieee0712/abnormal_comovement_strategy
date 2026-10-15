# -*- coding: utf-8 -*-
"""E6n 逐描述符统计 / 比较统计 / 随机参照 / MC 计划（plan §7.3、§7.1；brief §1.3-8 / -11、W12；e6m_s_stats 同式，统计工具只 import：
e6j_stats（paired / seg_D / hac_se / full_g4 / impact_cost）、e6l_mde80.hac_batch）。读账户 / 随机目录前过封存门（推导段：seal_B1_0 + 冻结；后段：post_gate）。
  desc  --seg S --out D：descriptor_stats_<段>.csv（主 / 附属 / 分量对象 − 本形态原父同 H；R2 / A06 = 自身）
  cmp   --seg S --out D：comparison_stats_<段>.csv（comparison_manifest 每条 left − right，共同有限日；se_H / se_2H / se_60 / MDE80）
  rand  --seg S --out D：random_refs_<段>.csv（对象 × 机制：real / rand_mean / rmr / rand_sd / paths_run / mcse）+ 配对随机（同组同路径的 left − right）
        + mc_plan_<段>.csv（共享路径组 = (机制, 载荷组)：组内最大 (sd/.03)²，512 一批至 8,192）
  full  --out D：FULL = Σ n_s D_s / Σ n_s、G4 = 段 D 中位；comparison_full.csv；random_refs.csv（四段 + FULL；FULL MCSE = √Σ(n_s/N)² MCSE_s²）
单位：*_ann_pp = 252 × 100 × 日均；n = 共同有限日。"""
import os
import sys
import glob
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6n_core as N

ANN = 252.0 * 100.0
A_POL, K_POL = 5.0, 0.5
A_STR, K_STR = 10.0, 1.0
MC_TARGET = 0.03


def gate(seg):
    import e6n_gate as GT
    GT.deriv_ready(seg, 'stats %s' % seg)


def load(seg):
    d, t, d2t, dH, dates = {}, {}, {}, {}, None
    for f in sorted(glob.glob(N.P('accounts', seg, '*.npz'))):
        z = np.load(f, allow_pickle=False)
        dates = z['dates']
        tg = [str(x) for x in z['targets']]
        form = os.path.basename(f)[:-4]
        TA = {k[2:]: z[k] for k in z.files if k.startswith('t_')}
        for j, tid in enumerate(tg):
            t['%s#%s' % (form, tid)] = {k: v[j] for k, v in TA.items()}
        DA = {k[2:]: z[k] for k in z.files if k.startswith('d_')}
        for i, did in enumerate([str(x) for x in z['desc']]):
            if did in d:
                raise RuntimeError('账户 ID 重复：%s' % did)
            d[did] = {k: v[i] for k, v in DA.items()}
            d2t[did] = '%s#%s' % (form, tg[int(z['desc_target'][i])])
            dH[did] = int(z['desc_H'][i])
    return d, t, d2t, dH, dates


def parent_of(did, form, H):
    k = did.split('|')[0]
    if k == 'STRONG_ANCHOR':
        return did
    return 'ANCHOR|ORIGINAL|%s|NONE|H%d|s0|ALL|a0|f5|d+1' % (form, H)


def stats_row(c, p, H, years):
    import e6j_stats as ST
    r = {}
    seg_pair = lambda a, b: ST.seg_D(ST.paired(a, b)[0])
    imp = lambda x, A, k: x['net8'] - ST.impact_cost(x['bracket'], A, k)
    D, n = seg_pair(c['net8'], p['net8'])
    r['D_ann_pp'], r['n'] = D, n
    r['D_gross_ann_pp'] = seg_pair(c['gross'], p['gross'])[0]
    r['D_sc_ann_pp'] = seg_pair(c['sc_child'], c['sc_parent'])[0]
    r['D_imp_ann_pp'] = seg_pair(imp(c, A_POL, K_POL), imp(p, A_POL, K_POL))[0]
    r['D_str_ann_pp'] = seg_pair(imp(c, A_STR, K_STR), imp(p, A_STR, K_STR))[0]
    for cost in (6.0, 12.0):
        r['D_%dbp_ann_pp' % cost] = seg_pair(c['gross'] - c['turn'] * cost / 1e4, p['gross'] - p['turn'] * cost / 1e4)[0]
    dd = ST.paired(c['net8'], p['net8'])[0]
    r['se_H_ann_pp'] = ST.hac_se(dd, H)[0] * ANN
    r['se_2H_ann_pp'] = ST.hac_se(dd, max(2 * H, 20))[0] * ANN
    r['se_60_ann_pp'] = ST.hac_se(dd, 60)[0] * ANN
    r['mde80_ann_pp'] = 2.80 * r['se_H_ann_pp']
    mt = float(np.mean(p['turn']))
    r['turn_rel_decimal'] = float(np.mean(c['turn'])) / mt - 1.0 if mt > 0 else np.nan
    r['pos_diff_decimal'] = float(np.mean(c['pos']) - np.mean(p['pos']))
    for y in np.unique(years):
        m = (years == y) & np.isfinite(dd)
        r['Y%d_ann_pp' % y] = float(np.mean(dd[m])) * ANN if m.any() else np.nan
        r['Yn%d' % y] = int(m.sum())
    r['net8_ann_pp'] = float(np.nanmean(c['net8'])) * ANN
    r['gross_ann_pp'] = float(np.nanmean(c['gross'])) * ANN
    r['turn_mean_decimal'] = float(np.mean(c['turn']))
    r['pos_mean_decimal'] = float(np.mean(c['pos']))
    r['parent_net8_ann_pp'] = float(np.nanmean(p['net8'])) * ANN
    r['qmiss_share_decimal'] = float(np.nansum(c['qmiss']) / max(np.sum(c['turn']), 1e-300)) if np.isfinite(c['qmiss']).any() else np.nan
    for z in ('T', 'L'):
        a, b = c['roll_z%s' % z], p['roll_z%s' % z]
        m = np.isfinite(a) & np.isfinite(b)
        r['roll_size_delta_%s_pct_pt' % z] = float(np.mean(a[m] - b[m]) * 100.0) if m.any() else np.nan
    return r


def target_expo(tc, tp):
    r = {}
    for z in ('T', 'L'):
        lo, hi = tc['sz%s_lo' % z], tc['sz%s_hi' % z]
        m = np.isfinite(lo) & np.isfinite(hi)
        r['port_size_lo_%s_pct_pt' % z] = float(np.mean(lo[m])) if m.any() else np.nan
        r['port_size_hi_%s_pct_pt' % z] = float(np.mean(hi[m])) if m.any() else np.nan
        r['port_size_absmean_mid_%s_pct_pt' % z] = float(np.mean(np.abs(0.5 * (lo[m] + hi[m])))) if m.any() else np.nan
        r['port_size_maxabs_mid_%s_pct_pt' % z] = float(np.max(np.abs(0.5 * (lo[m] + hi[m])))) if m.any() else np.nan
        r['port_days_%s' % z] = int(m.sum())
        g = tc['gap%s' % z]
        mg = np.isfinite(g)
        r['edit_gap_mean_%s_pct_pt' % z] = float(np.mean(g[mg]) * 100.0) if mg.any() else np.nan
        r['edit_gap_days_%s' % z] = int(mg.sum())
    for k in ('lv5', 'small30', 'unkT', 'unkL', 'n_edits', 'edit_w_in', 'nnames', 'wsum'):
        x = tc[k]
        m = np.isfinite(x) & (tc['wsum'] > 0)
        r['%s_mean' % k] = float(np.mean(x[m])) if m.any() else np.nan
    for k in ('lv5', 'small30', 'nnames', 'wsum'):
        x = tp[k]
        m = np.isfinite(x) & (tp['wsum'] > 0)
        r['parent_%s_mean' % k] = float(np.mean(x[m])) if m.any() else np.nan
    r['small30_delta'] = r['small30_mean'] - r['parent_small30_mean']
    return r


def registry_objs():
    D = pd.read_csv(N.P('registry', 'descriptors_E6n.csv'), keep_default_na=False)
    A = pd.read_csv(N.P('registry', 'auxiliary_E6n.csv'), keep_default_na=False)
    C = pd.read_csv(N.P('registry', 'component_controls_E6n.csv'), keep_default_na=False)
    out = [(r.desc_id, r.parent, int(r.H), 'MAIN') for r in D.itertuples()]
    out += [(r.aux_id, r.parent, int(r.H), 'AUX') for r in A.itertuples()]
    out += [(r.comp_id, r.parent, int(r.H), 'COMP') for r in C.itertuples()]
    return out


def task_desc(seg, out):
    t0 = time.time()
    d, t, d2t, dH, dates = load(seg)
    years = pd.to_datetime(pd.Index([str(x) for x in dates])).year.values
    rows = []
    for did, form, H, tab in registry_objs():
        if did not in d:
            rows.append(dict(desc_id=did, segment=seg, table=tab, status='NOT_COMPUTED'))
            continue
        pid = parent_of(did, form, H)
        if pid not in d:
            rows.append(dict(desc_id=did, segment=seg, table=tab, status='PARENT_MISSING'))
            continue
        r = stats_row(d[did], d[pid], H, years)
        if d2t.get(did) in t and d2t.get(pid) in t:
            r.update(target_expo(t[d2t[did]], t[d2t[pid]]))
        r.update(desc_id=did, segment=seg, table=tab, H=H, parent_desc_id=pid, status='COMPUTED' if did != pid else 'PARENT_SELF')
        rows.append(r)
    df = pd.DataFrame(rows)
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, 'descriptor_stats_%s.csv' % seg)
    N.atomic_write_csv(p, N.to_status(df))
    return p, df, round(time.time() - t0, 1)


def task_cmp(seg, out):
    import e6j_stats as ST
    from e6l_mde80 import hac_batch
    t0 = time.time()
    d, t, d2t, dH, dates = load(seg)
    CM = pd.read_csv(N.P('registry', 'comparison_manifest_E6n.csv'), keep_default_na=False)
    CM['H'] = CM.left_desc_id.map(lambda s: int(s.split('|')[4][1:]))
    rows = []
    for H, g in CM.groupby('H'):
        X, keep, miss = [], [], []
        for r in g.itertuples():
            if r.left_desc_id in d and r.right_desc_id in d:
                X.append(ST.paired(d[r.left_desc_id]['net8'], d[r.right_desc_id]['net8'])[0])
                keep.append(r)
            else:
                miss.append(r)
        if X:
            Dm = np.vstack(X)
            n = np.isfinite(Dm).sum(1)
            with np.errstate(all='ignore'):
                mu = np.where(n > 0, np.nansum(Dm, 1) / np.maximum(n, 1), np.nan)
            seH = hac_batch(Dm, H)[0]
            se2 = hac_batch(Dm, max(2 * H, 20))[0]
            s60 = hac_batch(Dm, 60)[0]
            for i, r in enumerate(keep):
                rows.append(dict(comparison_id=r.comparison_id, view=r.view, card=r.card, kind=r.kind, left_desc_id=r.left_desc_id, right_desc_id=r.right_desc_id,
                                 H=int(H), segment=seg, D_ann_pp=float(mu[i]) * ANN, n=int(n[i]), hac_se_ann_pp=float(seH[i]) * ANN,
                                 se_2H_ann_pp=float(se2[i]) * ANN, se_60_ann_pp=float(s60[i]) * ANN, mde80_ann_pp=2.80 * float(seH[i]) * ANN,
                                 status='COMPUTED' if n[i] > 0 else 'NO_COMMON_DAYS'))
        for r in miss:
            rows.append(dict(comparison_id=r.comparison_id, view=r.view, card=r.card, kind=r.kind, left_desc_id=r.left_desc_id, right_desc_id=r.right_desc_id,
                             H=int(H), segment=seg, status='ENDPOINT_NOT_COMPUTED'))
    df = pd.DataFrame(rows).sort_values('comparison_id')
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, 'comparison_stats_%s.csv' % seg)
    N.atomic_write_csv(p, N.to_status(df))
    return p, df, round(time.time() - t0, 1)


PAIRED_VIEWS = ('PATH_MINUS_Q_RV', 'PATH_MINUS_Q_RANGE', 'THIN_MINUS_LEVEL', 'COMPONENT', 'COMPONENT_DOSE')


def random_refs(seg, real):
    """randoms/<机制>/<段>/*.npz → 对象 × 机制行 + 同组同路径配对行（comparison_manifest 的配对视图）。"""
    acc = {}
    T = None
    files = sorted(glob.glob(N.P('randoms', '*', seg, '*.npz')))
    files = [f for f in files if not os.path.basename(f).startswith('donor_')]
    for f in files:
        mech = os.path.basename(os.path.dirname(os.path.dirname(f)))
        z = np.load(f, allow_pickle=False)
        grp = str(z['group'][0])
        for i, (did, H) in enumerate(zip([str(x) for x in z['desc']], z['H'])):
            k = (did, int(H), mech)
            a = acc.setdefault(k, dict(s_net=[], n_net=[], s_gross=[], n_gross=[], s_turn=[], dsum=0.0, dcnt=0, shards=0, p0=[], npaths=[], group=grp))
            for kk in ('s_net', 'n_net', 's_gross', 'n_gross', 's_turn'):
                a[kk].append(z[kk][i])
            a['dsum'] = a['dsum'] + z['dsum'][i]
            a['dcnt'] = a['dcnt'] + z['dcnt'][i]
            a['shards'] += 1
            a['p0'].append(int(z['path0'][0]))
            a['npaths'].append(int(z['n_paths'][0]))
        T = len(z['dates'])
    rows, per = [], {}
    for (did, H, mech), a in acc.items():
        o = np.argsort(a['p0'])
        p0s, nps = np.asarray(a['p0'])[o], np.asarray(a['npaths'])[o]
        if (p0s[1:] < p0s[:-1] + nps[:-1]).any():
            raise RuntimeError('随机分片路径区间重叠：%s|H%d|%s' % (did, H, mech))
        cat = lambda k: np.concatenate([a[k][j] for j in o])
        sn, nn, sg, ng, st = cat('s_net'), cat('n_net'), cat('s_gross'), cat('n_gross'), cat('s_turn')
        pid = np.concatenate([np.arange(p0s[j], p0s[j] + nps[j]) for j in range(len(o))])
        with np.errstate(all='ignore'):
            v = np.where(nn > 0, sn / nn * ANN, np.nan)
            g = np.where(ng > 0, sg / ng * ANN, np.nan)
        per[(did, H, mech)] = (pid, v)
        ok = np.isfinite(v)
        n = int(ok.sum())
        mu = float(np.mean(v[ok])) if n else np.nan
        sd = float(np.std(v[ok], ddof=1)) if n > 1 else np.nan
        re_ = real.get(did, np.nan)
        rows.append(dict(desc_id=did, H=H, mechanism=mech, segment=seg, group=a['group'], kind='OBJECT', real=re_, rand_mean=mu,
                         rmr=re_ - mu if np.isfinite(re_) else np.nan, rand_sd=sd, paths_run=int(len(sn)), n_paths_finite=n,
                         mcse=sd / np.sqrt(n) if n > 1 else np.nan, rand_gross_mean_ann_pp=float(np.nanmean(g)), rand_turn_mean_decimal=float(np.mean(st) / T),
                         status='COMPUTED' if n > 1 else 'NOT_COMPUTABLE'))
    # 配对随机：同组同路径 left − right（comparison_manifest 的配对视图）
    CM = pd.read_csv(N.P('registry', 'comparison_manifest_E6n.csv'), keep_default_na=False)
    CM = CM[CM.view.isin(PAIRED_VIEWS)]
    for r in CM.itertuples():
        H = int(r.left_desc_id.split('|')[4][1:])
        for mech in ('CONTENT_IID', 'CONTENT_ISK_P5'):
            L, R_ = per.get((r.left_desc_id, H, mech)), per.get((r.right_desc_id, H, mech))
            if L is None or R_ is None:
                continue
            common, il, ir = np.intersect1d(L[0], R_[0], return_indices=True)
            dv = L[1][il] - R_[1][ir]
            ok = np.isfinite(dv)
            n = int(ok.sum())
            rl, rr = real.get(r.left_desc_id, np.nan), real.get(r.right_desc_id, np.nan)
            mu = float(np.mean(dv[ok])) if n else np.nan
            sd = float(np.std(dv[ok], ddof=1)) if n > 1 else np.nan
            rows.append(dict(desc_id=r.comparison_id, H=H, mechanism=mech, segment=seg, group=acc[(r.left_desc_id, H, mech)]['group'], kind='PAIRED', real=rl - rr, rand_mean=mu,
                             rmr=(rl - rr) - mu if np.isfinite(rl - rr) else np.nan, rand_sd=sd, paths_run=int(len(common)), n_paths_finite=n,
                             mcse=sd / np.sqrt(n) if n > 1 else np.nan, status='COMPUTED' if n > 1 else 'NOT_COMPUTABLE'))
    return pd.DataFrame(rows)


def mc_plan(R):
    """共享路径组 = (机制, 载荷组)；组内最大所需 (sd/.03)²；512 一批至 8,192（同一比较连通组共享路径数）。"""
    if not len(R):
        return pd.DataFrame()
    R = R.copy()                                  # 对象行与配对行（配对行的 group = 左端 owner 的载荷组）一起定增补
    R['n_req'] = np.ceil((R.rand_sd / MC_TARGET) ** 2)
    out = []
    for (mech, grp), g in R.groupby(['mechanism', 'group']):
        have = int(g.paths_run.min())
        need = int(min(8192, max(have, np.nanmax(g.n_req.values) if g.n_req.notna().any() else have)))
        tgt = have if need <= have else int(min(8192, have + 512 * np.ceil((need - have) / 512.0)))
        out.append(dict(mechanism=mech, group=grp, have=have, need_max=need, target=tgt, topup=max(0, tgt - have), worst_mcse=float(g.mcse.max()),
                        worst_sd=float(g.rand_sd.max()), mc_limit=bool(need >= 8192 and g.mcse.max() > MC_TARGET)))
    return pd.DataFrame(out)


def task_full(out, segs):
    import e6j_stats as ST
    parts = [pd.read_csv(os.path.join(out, 'descriptor_stats_%s.csv' % s), keep_default_na=False, na_values=['']) for s in segs
             if os.path.exists(os.path.join(out, 'descriptor_stats_%s.csv' % s))]
    A = pd.concat(parts)
    A = A[A.status == 'COMPUTED']
    rows = []
    for did, g in A.groupby('desc_id'):
        full, g4 = ST.full_g4(g.D_ann_pp.values, g.n.values)
        sc = ST.full_g4(g.D_sc_ann_pp.values, g.n.values)[0] if 'D_sc_ann_pp' in g else np.nan
        rows.append(dict(desc_id=did, segments=len(g), FULL_ann_pp=full, G4_ann_pp=g4, FULL_sc_ann_pp=sc, n_total=int(g.n.sum())))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'descriptor_stats_FULL.csv')
    N.atomic_write_csv(p, df)
    cparts = [pd.read_csv(os.path.join(out, 'comparison_stats_%s.csv' % s), keep_default_na=False, na_values=[''], dtype={'comparison_id': str}) for s in segs
              if os.path.exists(os.path.join(out, 'comparison_stats_%s.csv' % s))]
    C = pd.concat(cparts)
    C = C[C.status == 'COMPUTED']
    crow = []
    for cid, g in C.groupby('comparison_id'):
        full, g4 = ST.full_g4(g.D_ann_pp.values, g.n.values)
        crow.append(dict(comparison_id=cid, view=g.view.iloc[0], left_desc_id=g.left_desc_id.iloc[0], right_desc_id=g.right_desc_id.iloc[0], segments=len(g),
                         FULL_ann_pp=full, G4_ann_pp=g4, n_total=int(g.n.sum()), status='COMPUTED'))
    pc = os.path.join(out, 'comparison_full.csv')
    N.atomic_write_csv(pc, pd.DataFrame(crow))
    rparts = [pd.read_csv(os.path.join(out, 'random_refs_%s.csv' % s), keep_default_na=False, na_values=['']) for s in segs
              if os.path.exists(os.path.join(out, 'random_refs_%s.csv' % s))]
    outs = [p, pc]
    if rparts:
        R = pd.concat(rparts, ignore_index=True)
        nmap = {(r.desc_id, r.segment): r.n for r in A.itertuples()}
        fr = []
        for (did, H, mech), g in R.groupby(['desc_id', 'H', 'mechanism']):
            if len(g) < len(segs):
                continue
            w = np.array([nmap.get((did, s), np.nan) for s in g.segment], float)
            if not np.isfinite(w).all() or w.sum() <= 0:
                w = np.ones(len(g))
            ww = w / w.sum()
            rm = float(np.sum(ww * g.rand_mean.values))
            mcse = float(np.sqrt(np.sum((ww * g.mcse.values) ** 2)))
            real = float(np.sum(ww * g.real.values))
            fr.append(dict(desc_id=did, H=H, mechanism=mech, segment='FULL', group=g.group.iloc[0], kind=g.kind.iloc[0], real=real, rand_mean=rm, rmr=real - rm,
                           rand_sd=np.nan, paths_run=int(g.paths_run.min()), n_paths_finite=int(g.n_paths_finite.min()), mcse=mcse, status='COMPUTED'))
        RR = pd.concat([R, pd.DataFrame(fr)], ignore_index=True)
        pr = os.path.join(out, 'random_refs.csv')
        N.atomic_write_csv(pr, N.to_status(RR))
        outs.append(pr)
    return outs, df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['desc', 'cmp', 'rand', 'full'])
    ap.add_argument('--seg')
    ap.add_argument('--out', required=True)
    ap.add_argument('--segs', default=','.join(N.SEGMENTS))
    a = ap.parse_args()
    out = N.P(a.out) if not os.path.isabs(a.out) else a.out
    if a.seg:
        gate(a.seg)
    if a.task == 'full':
        outs, df = task_full(out, a.segs.split(','))
        N.write_receipt('E6n_stats_full_%s' % os.path.basename(out), outs, code=[__file__], rows=len(df))
        print(json.dumps(dict(rows=len(df)), ensure_ascii=False))
        return 0
    if a.task == 'rand':
        d, t, d2t, dH, dates = load(a.seg)
        real = {did: float(np.nanmean(x['net8'])) * ANN for did, x in d.items()}
        R = random_refs(a.seg, real)
        os.makedirs(out, exist_ok=True)
        p1 = os.path.join(out, 'random_refs_%s.csv' % a.seg)
        N.atomic_write_csv(p1, N.to_status(R))
        P = mc_plan(R)
        p3 = os.path.join(out, 'mc_plan_%s.csv' % a.seg)
        N.atomic_write_csv(p3, P if len(P) else pd.DataFrame([dict(group='NONE')]))
        N.write_receipt('E6n_stats_rand_%s_%s' % (a.seg, os.path.basename(out)), [p1, p3], code=[__file__], rows=len(R))
        print(json.dumps(dict(task='rand', seg=a.seg, rows=len(R), topup_groups=int((P.topup > 0).sum()) if len(P) else 0), ensure_ascii=False))
        return 0
    p, df, sec = (task_desc if a.task == 'desc' else task_cmp)(a.seg, out)
    N.write_receipt('E6n_stats_%s_%s_%s' % (a.task, a.seg, os.path.basename(out)), [p], code=[__file__], rows=len(df), status_counts=df.status.value_counts().to_dict(),
                    wall_s=sec)
    print(json.dumps(dict(task=a.task, seg=a.seg, rows=len(df), status=df.status.value_counts().to_dict(), wall_s=sec), ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
