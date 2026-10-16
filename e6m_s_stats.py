# -*- coding: utf-8 -*-
"""E6m 阶段 S · 逐描述符统计与比较统计（plan §9.4–§9.5 / §10；e6l_stats.stats_row / target_expo 与 e6l_cmpstats 同式；
统计工具只 import 不改：e6j_stats（配对 / HAC / 冲击）、e6l_mde80.hac_batch（批量 HAC）。
  desc --acc <账户目录> --seg S --out <输出目录>：descriptor_stats_<段>.csv（每描述符对本形态实际父 K0 PARENT 同 H）
  cmp  --acc … --seg S --out …：comparison_stats_<段>.csv（comparison_manifest 每条 left − right，共同有限日；se_H / se_2H / se_60 / MDE80）
  full --out …：四段合并 FULL = Σ n_s D_s / Σ n_s、G4 = 段 D 中位（e6j_stats.full_g4）
B2 开发期只在合成账本（SYNTHETIC）上运行；阶段 S 换真实账户目录。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
import e6j_stats as ST
from e6l_mde80 import hac_batch

A_POL, K_POL = 5.0, 0.5
A_STR, K_STR = 10.0, 1.0
SEGS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')


def npz_all(p):
    z = np.load(p, allow_pickle=False)
    return {k: z[k] for k in z.files}


def acc_dirs(acc_dir):
    """真实账户：accounts/ 与同级 accounts_aux/（附属 / 补充 / 冻结父权重对象，e6m_s_accounts.run_aux）一并读；其它目录（合成）只读自身。"""
    out = [acc_dir]
    if os.path.basename(os.path.normpath(acc_dir)) == 'accounts':
        sib = os.path.join(os.path.dirname(os.path.normpath(acc_dir)), 'accounts_aux')
        if os.path.isdir(sib):
            out.append(sib)
    return out


def load(acc_dir, seg):
    """→ d：desc → {key: 日数组}；t：target → {key}；d2t / dH；dates。"""
    d, t, d2t, dH, dates = {}, {}, {}, {}, None
    for ad in acc_dirs(acc_dir):
        tag = '' if ad == acc_dir else os.path.basename(os.path.normpath(ad)) + ':'
        for f in sorted(glob.glob(os.path.join(ad, seg, '*.npz'))):
            if os.path.basename(f).startswith('weights_'):
                continue
            z = npz_all(f)
            dates = z['dates']
            tg = [str(x) for x in z['targets']]
            TA = {k[2:]: z[k] for k in z if k.startswith('t_')}
            for j, tid in enumerate(tg):
                t['%s%s#%s' % (tag, os.path.basename(f)[:-4], tid)] = {k: v[j] for k, v in TA.items()}
            DA = {k[2:]: z[k] for k in z if k.startswith('d_')}
            for i, did in enumerate([str(x) for x in z['desc']]):
                if did in d:
                    raise RuntimeError('账户 ID 重复：%s' % did)
                d[did] = {k: v[i] for k, v in DA.items()}
                d2t[did] = '%s%s#%s' % (tag, os.path.basename(f)[:-4], tg[int(z['desc_target'][i])])
                dH[did] = int(z['desc_H'][i])
    return d, t, d2t, dH, dates


def seg_pair(a, b):
    return ST.seg_D(ST.paired(a, b)[0])


def imp(x, A, k):
    return x['net8'] - ST.impact_cost(x['bracket'], A, k)


def stats_row(c, p, H, years):
    """e6l_stats.stats_row 同式。"""
    r = {}
    D, n = seg_pair(c['net8'], p['net8'])
    r['D'], r['n'] = D, n
    r['D_gross'] = seg_pair(c['gross'], p['gross'])[0]
    r['D_sc'] = seg_pair(c['sc_child'], c['sc_parent'])[0]
    r['D_imp'] = seg_pair(imp(c, A_POL, K_POL), imp(p, A_POL, K_POL))[0]
    r['D_str'] = seg_pair(imp(c, A_STR, K_STR), imp(p, A_STR, K_STR))[0]
    for cost in (6.0, 12.0):
        r['D_%dbp' % cost] = seg_pair(c['gross'] - c['turn'] * cost / 1e4, p['gross'] - p['turn'] * cost / 1e4)[0]
    dd = ST.paired(c['net8'], p['net8'])[0]
    r['se_H'] = ST.hac_se(dd, H)[0] * ST.ANN
    r['se_2H'] = ST.hac_se(dd, max(2 * H, 20))[0] * ST.ANN
    r['se_60'] = ST.hac_se(dd, 60)[0] * ST.ANN
    r['MDE80'] = 2.80 * r['se_H']
    mt = float(np.mean(p['turn']))
    r['turn_rel'] = float(np.mean(c['turn'])) / mt - 1.0 if mt > 0 else np.nan
    r['pos_diff'] = float(np.mean(c['pos']) - np.mean(p['pos']))
    for y in np.unique(years):
        m = (years == y) & np.isfinite(dd)
        r['Y%d' % y] = float(np.mean(dd[m])) * ST.ANN if m.any() else np.nan
        r['Yn%d' % y] = int(m.sum())
    r['net8_ann'] = float(np.nanmean(c['net8'])) * ST.ANN
    r['gross_ann'] = float(np.nanmean(c['gross'])) * ST.ANN
    r['turn_mean_decimal'] = float(np.mean(c['turn']))
    r['pos_mean'] = float(np.mean(c['pos']))
    r['parent_net8_ann'] = float(np.nanmean(p['net8'])) * ST.ANN
    r['qmiss_share'] = float(np.nansum(c['qmiss']) / max(np.sum(c['turn']), 1e-300)) if np.isfinite(c['qmiss']).any() else np.nan
    for z in ('T', 'L'):
        a, b = c['roll_z%s' % z], p['roll_z%s' % z]
        m = np.isfinite(a) & np.isfinite(b)
        r['roll_size_delta_%s' % z] = float(np.mean(a[m] - b[m]) * 100.0) if m.any() else np.nan
    return r


def target_expo(tc, tp):
    """e6l_stats.target_expo 同式（组合层 size 紧区间、编辑 gap、lv5 / small30 / 未知 size / 编辑数 / 名数 / 资本）。"""
    r = {}
    for z in ('T', 'L'):
        lo, hi = tc['sz%s_lo' % z], tc['sz%s_hi' % z]
        m = np.isfinite(lo) & np.isfinite(hi)
        r['port_size_lo_%s' % z] = float(np.mean(lo[m])) if m.any() else np.nan
        r['port_size_hi_%s' % z] = float(np.mean(hi[m])) if m.any() else np.nan
        r['port_size_absmean_mid_%s' % z] = float(np.mean(np.abs(0.5 * (lo[m] + hi[m])))) if m.any() else np.nan
        r['port_size_p95abs_mid_%s' % z] = float(np.percentile(np.abs(0.5 * (lo[m] + hi[m])), 95)) if m.any() else np.nan
        r['port_size_maxabs_mid_%s' % z] = float(np.max(np.abs(0.5 * (lo[m] + hi[m])))) if m.any() else np.nan
        r['port_days_%s' % z] = int(m.sum())
        g = tc['gap%s' % z]
        mg = np.isfinite(g)
        r['edit_gap_mean_%s' % z] = float(np.mean(g[mg]) * 100.0) if mg.any() else np.nan
        r['edit_gap_absmean_%s' % z] = abs(r['edit_gap_mean_%s' % z]) if mg.any() else np.nan
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


def parent_of(did):
    p = did.split('|')
    return 'K0|%s|PARENT|-|-|NONE|%s|SOURCE|-' % (p[1], p[6])


def task_desc(acc, seg, out):
    t0 = time.time()
    d, t, d2t, dH, dates = load(acc, seg)
    years = pd.to_datetime(pd.Index(dates)).year.values
    Dr = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    rows = []
    for did in Dr.desc_id:
        if did not in d:
            rows.append(dict(desc_id=did, segment=seg, status='NOT_COMPUTED'))
            continue
        pid = parent_of(did)
        if pid not in d:
            rows.append(dict(desc_id=did, segment=seg, status='PARENT_MISSING'))
            continue
        r = stats_row(d[did], d[pid], dH[did], years)
        if d2t.get(did) in t and d2t.get(pid) in t:
            r.update(target_expo(t[d2t[did]], t[d2t[pid]]))
        r.update(desc_id=did, segment=seg, H=dH[did], status='COMPUTED' if did != pid else 'PARENT_SELF')
        rows.append(r)
    df = pd.DataFrame(rows)
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, 'descriptor_stats_%s.csv' % seg)
    M.atomic_write_csv(p, df)
    return p, df, round(time.time() - t0, 1)


def task_cmp(acc, seg, out):
    t0 = time.time()
    d, t, d2t, dH, dates = load(acc, seg)
    CM = M.read_csv_keep(M.P('registry', 'comparison_manifest_E6m.csv'), dtype=str)
    CM['H'] = CM.right_desc_id.map(lambda s: int(s.split('|')[6][1:]))          # 左端可为补充对象 SUPP:…（与 owner 同 H）
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
            I = np.isfinite(Dm)
            n = I.sum(1)
            with np.errstate(all='ignore'):
                mu = np.where(n > 0, np.nansum(Dm, 1) / np.maximum(n, 1), np.nan)
            seH = hac_batch(Dm, H)[0]
            se2 = hac_batch(Dm, max(2 * H, 20))[0]
            s60 = hac_batch(Dm, 60)[0]
            for i, r in enumerate(keep):
                rows.append(dict(comparison_id=r.comparison_id, view=r.view, card=r.card, kind=r.kind, left_desc_id=r.left_desc_id,
                                 right_desc_id=r.right_desc_id, H=int(H), segment=seg, D_ann_pp=float(mu[i]) * ST.ANN, n_days=int(n[i]),
                                 se_H_ann_pp=float(seH[i]) * ST.ANN, se_2H_ann_pp=float(se2[i]) * ST.ANN, se_60_ann_pp=float(s60[i]) * ST.ANN,
                                 mde80_ann_pp=2.80 * float(seH[i]) * ST.ANN, status='COMPUTED' if n[i] > 0 else 'NO_COMMON_DAYS'))
        for r in miss:
            rows.append(dict(comparison_id=r.comparison_id, view=r.view, card=r.card, kind=r.kind, left_desc_id=r.left_desc_id,
                             right_desc_id=r.right_desc_id, H=int(H), segment=seg, status='ENDPOINT_NOT_COMPUTED'))
    df = pd.DataFrame(rows).sort_values('comparison_id')
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, 'comparison_stats_%s.csv' % seg)
    M.atomic_write_csv(p, df)
    return p, df, round(time.time() - t0, 1)


MC_TARGET = 0.03


def random_refs(rand_dir, seg, real):
    """e6l_stats.random_refs 同式（目录参数化）：randoms/<机制>/<段>/*.npz → (表, 路径 dict, 逐日 dict)。
    real：desc → net8 年化（真实账户；同 H 描述符）。每路径统计先按该路径自己的有效日求，路径间再求均值 / 方差。"""
    acc = {}
    T = None
    for f in sorted(glob.glob(os.path.join(rand_dir, '*', seg, '*.npz'))):
        mech = os.path.basename(os.path.dirname(os.path.dirname(f)))
        z = npz_all(f)
        seen = set()
        for i, (did, H) in enumerate(zip([str(x) for x in z['desc']], z['H'])):
            if (did, int(H)) in seen:      # 同分片内同 (desc, H) 的重复登记行（不同 aux_id）：run_accounts 只填首行，余行全零（2026-10-11）
                if np.any(z['n_net'][i]) or np.any(z['s_net'][i]):
                    raise RuntimeError('分片内重复行非空：%s|H%d|%s %s' % (did, int(H), mech, os.path.basename(f)))
                continue
            seen.add((did, int(H)))
            k = (did, int(H), mech)
            a = acc.setdefault(k, dict(s_net=[], n_net=[], s_gross=[], n_gross=[], s_turn=[], dsum=0.0, dcnt=0, shards=0, p0=[], npaths=[]))
            for kk in ('s_net', 'n_net', 's_gross', 'n_gross', 's_turn'):
                a[kk].append(z[kk][i])
            a['dsum'] = a['dsum'] + z['dsum'][i]
            a['dcnt'] = a['dcnt'] + z['dcnt'][i]
            a['shards'] += 1
            a['p0'].append(int(z['path0'][0]))
            a['npaths'].append(int(z['n_paths'][0]))
        T = len(z['dates'])
    rows, paths, daily = [], {}, {}
    for (did, H, mech), a in acc.items():
        o = np.argsort(a['p0'])
        p0s, nps = np.asarray(a['p0'])[o], np.asarray(a['npaths'])[o]
        if (p0s[1:] < p0s[:-1] + nps[:-1]).any():         # 分片路径区间重叠 = 重复计数（2026-10-11）
            raise RuntimeError('随机分片路径区间重叠：%s|H%d|%s p0=%s n=%s' % (did, H, mech, p0s.tolist(), nps.tolist()))
        cat = lambda k: np.concatenate([a[k][j] for j in o])
        sn, nn, sg, ng, st = cat('s_net'), cat('n_net'), cat('s_gross'), cat('n_gross'), cat('s_turn')
        with np.errstate(all='ignore'):
            v = np.where(nn > 0, sn / nn * ST.ANN, np.nan)
            g = np.where(ng > 0, sg / ng * ST.ANN, np.nan)
        ok = np.isfinite(v)
        n = int(ok.sum())
        mu = float(np.mean(v[ok])) if n else np.nan
        sd = float(np.std(v[ok], ddof=1)) if n > 1 else np.nan
        re_ = real.get(did, np.nan)
        rows.append(dict(desc_id=did, H=H, mechanism=mech, n=n, paths_run=int(len(sn)), rand_mean=mu, rand_sd=sd, mcse=sd / np.sqrt(n) if n > 1 else np.nan,
                         rand_gross_mean=float(np.nanmean(g)), rand_turn_mean_decimal=float(np.mean(st) / T), real_net8_ann=re_,
                         real_minus_rand=re_ - mu if np.isfinite(re_) else np.nan, shards=a['shards']))
        key = '%s|H%d|%s' % (did, H, mech)
        paths[key + '|s_net'] = sn
        paths[key + '|n_net'] = nn
        with np.errstate(all='ignore'):
            daily[key] = np.where(a['dcnt'] > 0, a['dsum'] / np.maximum(a['dcnt'], 1), np.nan)
    return pd.DataFrame(rows), paths, daily


def mc_plan(R):
    """e6l_stats.mc_plan 同式：共享路径组 = (机制, 测量)；组内最大所需 (sd/.03)²；512 一批至 8,192。"""
    if not len(R):
        return pd.DataFrame()
    R = R.copy()
    R['meas'] = R.desc_id.str.split('|').str[0]
    R['rtask'] = R.mechanism + '|' + R.meas
    R['n_req'] = np.ceil((R.rand_sd / MC_TARGET) ** 2)
    out = []
    for rt_, g in R.groupby('rtask'):
        have = int(g.paths_run.min())
        need = int(min(8192, max(have, g.n_req.max())))
        tgt = have if need <= have else int(min(8192, have + 512 * np.ceil((need - have) / 512.0)))
        out.append(dict(rtask=rt_, have=have, need_max=int(g.n_req.max()), target=tgt, topup=max(0, tgt - have), worst_mcse=float(g.mcse.max()),
                        worst_sd=float(g.rand_sd.max())))
    return pd.DataFrame(out)


def task_full(out):
    parts = [pd.read_csv(os.path.join(out, 'descriptor_stats_%s.csv' % s), keep_default_na=False, na_values=['']) for s in SEGS
             if os.path.exists(os.path.join(out, 'descriptor_stats_%s.csv' % s))]
    A = pd.concat(parts)
    A = A[A.status == 'COMPUTED']
    rows = []
    for did, g in A.groupby('desc_id'):
        full, g4 = ST.full_g4(g.D.values, g.n.values)
        rows.append(dict(desc_id=did, segments=len(g), FULL_D=full, G4_D=g4, n_total=int(g.n.sum())))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'descriptor_stats_FULL.csv')
    M.atomic_write_csv(p, df)
    return p, df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['desc', 'cmp', 'full', 'rand'])
    ap.add_argument('--acc')
    ap.add_argument('--rand-dir')
    ap.add_argument('--seg')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    if a.seg:                                                        # 读真实账户 / 随机目录前过封存门（附录 D-2；合成 / 开发目录不拦）
        import e6m_s_seal as SEAL
        for d in (a.acc, a.rand_dir):
            if d:
                SEAL.require_for(d, a.seg)
    if a.task == 'rand':
        d, t, d2t, dH, dates = load(a.acc, a.seg)
        real = {did: float(np.nanmean(x['net8'])) * ST.ANN for did, x in d.items()}
        R, paths, daily = random_refs(a.rand_dir, a.seg, real)
        os.makedirs(a.out, exist_ok=True)
        p1 = os.path.join(a.out, 'random_refs_%s.csv' % a.seg)
        M.atomic_write_csv(p1, R)
        p2 = os.path.join(a.out, 'random_daily_%s.npz' % a.seg)
        M.atomic_write_npz(p2, **{k.replace('|', '~'): v for k, v in daily.items()})
        P = mc_plan(R)
        p3 = os.path.join(a.out, 'mc_plan_%s.csv' % a.seg)
        M.atomic_write_csv(p3, P if len(P) else pd.DataFrame([dict(rtask='NONE')]))
        M.write_receipt(os.environ.get('E6M_TASK', 'S_stats_rand_%s' % a.seg), [p1, p2, p3], status='SUCCEEDED', code=[__file__, M.__file__], rows=len(R))
        print(json.dumps(dict(task='rand', seg=a.seg, rows=len(R), mc_groups=len(P), topup_groups=int((P.topup > 0).sum()) if len(P) else 0), ensure_ascii=False))
        return 0
    if a.task == 'full':
        p, df = task_full(a.out)
        M.write_receipt(os.environ.get('E6M_TASK', 'S_stats_full'), [p], status='SUCCEEDED', code=[__file__, M.__file__], rows=len(df))
        print(json.dumps(dict(rows=len(df)), ensure_ascii=False))
        return 0
    p, df, sec = (task_desc if a.task == 'desc' else task_cmp)(a.acc, a.seg, a.out)
    M.write_receipt(os.environ.get('E6M_TASK', 'S_stats_%s_%s' % (a.task, a.seg)), [p], status='SUCCEEDED', code=[__file__, M.__file__],
                    rows=len(df), status_counts=df.status.value_counts().to_dict(), wall_s=sec)
    print(json.dumps(dict(task=a.task, seg=a.seg, rows=len(df), status=df.status.value_counts().to_dict(), wall_s=sec), ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
