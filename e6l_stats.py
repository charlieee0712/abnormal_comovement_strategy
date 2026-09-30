# -*- coding: utf-8 -*-
"""E6l 逐描述符统计（plan §10 / §11；brief §6 / §7；E6k e6k_stats / e6j_stats 同式，只 import 不改）。一段一个进程，母体逐个处理：
  --segment S [--phase deriv|full]   读 accounts/<段>/*.npz → results/<阶段>/descriptor_stats_<段>.csv：
     D / n（子 − 原父 8bp 日配对年化，共同有限日）、D_sc（MATCH_CAP_FIXED_PATH）、D_imp（A 5 亿 κ .5）、D_str（A 10 亿 κ 1）、D_6bp / D_12bp、
     D_gross（零费敏感）、se_H / se_2H（max(2H, 20)）/ se_60（日历 HAC，缺失日 u = 0）、MDE80 = 2.80·se_H、turn_rel、pos_diff、逐年（Y / Yn）、
     net8_ann / gross_ann / turn_mean_decimal / parent_net8_ann、qmiss_share、roll_size_delta；
     相对比较（同段日配对）D_vs_native / D_vs_C1 / D_vs_Q0 / D_vs_QHG10 / D_vs_rule_only（+ gross 版 Dg_*）；
     暴露（组合层紧区间 T / LAG1 段均、编辑 gap 带符号 + 绝对、lv5、small30、未知 size、编辑数、名数、资本）；附属行对其 compare_to 另列 D_vs_compare
  随机：randoms/<机制>/<段>/*.npz → random_refs_<段>.csv（每 (描述符, H, 机制)：路径数 / 路径均值 / 路径 sd（两遍）/ MCSE / real − 随机均值 /
     gross 与换手路径均值）；random_paths_<段>.npz（每行每路径 s_net / n_net，供 FULL 级路径统计）；random_daily_<段>.npz（逐日随机均值）
  --mc-plan：只读随机（不读真实账户）→ mc_plan_<段>_<时刻>.csv（共享路径组 = (机制, 测量)，组内最大所需 (sd/.03)²，512 一批至 8,192）
读数门：推导段须 seal_deriv 核对通过；后段须 seal_post（--mc-plan 不需要封存，只读随机路径离散）。"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import json
import argparse

import numpy as np
import pandas as pd

import e6l_core as L
import e6j_stats as ST

A_POL, K_POL = 5.0, 0.5
A_STR, K_STR = 10.0, 1.0
MC_TARGET = 0.03


def seg_pair(a, b):
    return ST.seg_D(ST.paired(a, b)[0])


def imp(x, A, k):
    return x['net8'] - ST.impact_cost(x['bracket'], A, k)


def load_mother(pname, mother):
    d, t, d2t, dH = {}, {}, {}, {}
    for f in sorted(glob.glob(L.P('accounts', pname, '%s__*.npz' % mother))):
        if os.path.basename(f).startswith('weights_'):
            continue
        z = L.npz(f)
        tg = [str(x) for x in z['targets']]
        TA = {k[2:]: z[k] for k in z if k.startswith('t_')}
        for j, tid in enumerate(tg):
            t[tid] = {k: v[j] for k, v in TA.items()}
        DA = {k[2:]: z[k] for k in z if k.startswith('d_')}
        dtg, dh = z['desc_target'], z['desc_H']
        for i, did in enumerate([str(x) for x in z['desc']]):
            d[did] = {k: v[i] for k, v in DA.items()}
            d2t[did] = tg[int(dtg[i])]
            dH[did] = int(dh[i])
    return d, t, d2t, dH


def stats_row(c, p, H, years):
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


def pid(desc):
    p = desc.split('|')
    return 'K0|%s|a0|%s|NATIVE' % (p[1], p[3])


def random_refs(pname, real):
    """real：desc → net8 年化（真实账户，共同于随机的同 H 描述符）。返回 (表, 路径 dict, 逐日 dict)。"""
    acc = {}
    for f in sorted(glob.glob(L.P('randoms', '*', pname, '*.npz'))):
        mech = os.path.basename(os.path.dirname(os.path.dirname(f)))
        z = L.npz(f)
        for i, (did, H) in enumerate(zip([str(x) for x in z['desc']], z['H'])):
            k = (did, int(H), mech)
            a = acc.setdefault(k, dict(s_net=[], n_net=[], s_gross=[], n_gross=[], s_turn=[], dsum=0.0, dcnt=0, shards=0, p0=[]))
            a['s_net'].append(z['s_net'][i])
            a['n_net'].append(z['n_net'][i])
            a['s_gross'].append(z['s_gross'][i])
            a['n_gross'].append(z['n_gross'][i])
            a['s_turn'].append(z['s_turn'][i])
            a['dsum'] = a['dsum'] + z['dsum'][i]
            a['dcnt'] = a['dcnt'] + z['dcnt'][i]
            a['shards'] += 1
            a['p0'].append(int(z['path0'][0]))
        T = len(z['dates'])
    rows, paths, daily = [], {}, {}
    for (did, H, mech), a in acc.items():
        o = np.argsort(a['p0'])
        sn = np.concatenate([a['s_net'][j] for j in o])
        nn = np.concatenate([a['n_net'][j] for j in o])
        sg = np.concatenate([a['s_gross'][j] for j in o])
        ng = np.concatenate([a['n_gross'][j] for j in o])
        st = np.concatenate([a['s_turn'][j] for j in o])
        with np.errstate(all='ignore'):
            v = np.where(nn > 0, sn / nn * L.ANN, np.nan)
            g = np.where(ng > 0, sg / ng * L.ANN, np.nan)
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


def mc_plan(pname, phase):
    R, _, _ = random_refs(pname, {})
    if not len(R):
        return pd.DataFrame()
    R['meas'] = R.desc_id.str.split('|').str[0]
    R['rtask'] = R.mechanism + '|' + R.meas
    R['n_req'] = np.ceil((R.rand_sd / MC_TARGET) ** 2)
    out = []
    for rt, g in R.groupby('rtask'):
        have = int(g.paths_run.min())                      # 已跑路径数（含无有效日的路径），增补起点不与已有分片重叠
        need = int(min(8192, max(have, g.n_req.max())))
        tgt = have if need <= have else int(min(8192, have + 512 * np.ceil((need - have) / 512.0)))
        out.append(dict(segment=pname, rtask=rt, have=have, need_max=int(g.n_req.max()), target=tgt, topup=max(0, tgt - have),
                        worst_mcse=float(g.mcse.max()), worst_sd=float(g.rand_sd.max())))
    P = pd.DataFrame(out)
    od = L.P('results', phase)
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, 'mc_plan_%s_%s.csv' % (pname, pd.Timestamp.now().strftime('%H%M%S')))
    L.atomic_write_csv(p, P)
    L.write_receipt(L.next_rerun('mc_plan_%s_%s' % (phase, pname)), [p], 'SUCCEEDED', groups=len(P), topup_groups=int((P.topup > 0).sum()))
    print(P.to_string(), '\n需增补组数', int((P.topup > 0).sum()), flush=True)
    return P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--phase', default='deriv')
    ap.add_argument('--mc-plan', action='store_true')
    ap.add_argument('--trial', action='store_true')                # 试跑：只在 E6L_RES 指向临时目录时跳过封存核对
    a = ap.parse_args()
    pname = a.segment
    if pname in L.POST_SEGS:
        L.post_gate(pname, 'stats %s' % pname)
    if a.mc_plan:
        mc_plan(pname, a.phase)
        return 0
    import e6l_seal as SEAL
    ok, bad = (True, []) if (a.trial and L.RES.startswith(L.TRIAL)) else SEAL.verify('deriv' if pname in L.DERIV_SEGS else 'post')
    if not ok:
        raise RuntimeError('封存核对失败：%s' % bad[:5])
    od = L.P('results', a.phase)
    os.makedirs(od, exist_ok=True)
    D = L.read_csv_keep(L.P('registry', 'descriptors_E6l.csv'))
    A = L.read_csv_keep(L.P('registry', 'accessory_E6l.csv'))
    import e6l_registry as RG
    rows = []
    real = {}
    years = None
    for mother in sorted(D.mother.unique()):
        d, t, d2t, dH = load_mother(pname, mother)
        if not d:
            continue
        if years is None:
            f0 = sorted(f for f in glob.glob(L.P('accounts', pname, '*.npz')) if not os.path.basename(f).startswith('weights_'))[0]
            years = pd.to_datetime(pd.Index([str(x) for x in np.load(f0, allow_pickle=False)['dates']])).year.values
        for did, c in d.items():
            real[did] = float(np.nanmean(c['net8'])) * L.ANN
        Dm = D[D.mother == mother]
        for r in Dm.itertuples():
            if r.family == 'PARENT' or r.desc_id not in d:
                continue
            c = d[r.desc_id]
            if r.parent_desc not in d:
                if a.trial:
                    continue
                raise RuntimeError('母体账户缺失：%s（%s）' % (r.parent_desc, r.desc_id))
            p = d[r.parent_desc]
            s = stats_row(c, p, int(r.H), years)
            s.update(desc_id=r.desc_id, segment=pname, kind='registered')
            for lab, other in (('native', r.native_desc), ('C1', r.c1_desc), ('Q0', r.q0_desc), ('QHG10', r.qhg10_desc), ('rule_only', r.rule_only_desc)):
                if other != 'NOT_APPLICABLE' and other in d:
                    s['D_vs_%s' % lab] = seg_pair(c['net8'], d[other]['net8'])[0]
                    s['Dg_vs_%s' % lab] = seg_pair(c['gross'], d[other]['gross'])[0]
                    s['Dsc_vs_%s' % lab] = seg_pair(c['sc_child'], d[other]['sc_child'])[0]
            s.update(target_expo(t[d2t[r.desc_id]], t[d2t[r.parent_desc]]))
            rows.append(s)
        for r in A[A.mother == mother].itertuples():
            if r.acc_id not in d or r.kind in ('BOUNDARY_CONT_PARENT_PAIR', 'BOUNDARY_CONT_PARENT'):
                continue
            c = d[r.acc_id]
            p = d.get(pid(r.base_desc)) if r.kind != 'INV_CAP_LOOP_PARENT' else None
            if p is None:
                if r.kind != 'INV_CAP_LOOP_PARENT' and not a.trial:
                    raise RuntimeError('母体账户缺失：%s（%s）' % (pid(r.base_desc), r.acc_id))
                continue
            s = stats_row(c, p, int(r.H), years)
            s.update(desc_id=r.acc_id, segment=pname, kind=r.kind)
            if r.compare_to in d:
                s['D_vs_compare'] = seg_pair(c['net8'], d[r.compare_to]['net8'])[0]
                s['Dg_vs_compare'] = seg_pair(c['gross'], d[r.compare_to]['gross'])[0]
            if r.kind == 'INV_CAP_LOOP_PAIR':
                s['D_loop'] = seg_pair(c['sc_child'], c['sc_parent'])[0]
            rows.append(s)
        print('%s %s：累计 %d 行' % (pname, mother, len(rows)), flush=True)
    S = pd.DataFrame(rows)
    p1 = os.path.join(od, 'descriptor_stats_%s.csv' % pname)
    L.atomic_write_csv(p1, S)
    R, paths, daily = random_refs(pname, real)
    p2 = os.path.join(od, 'random_refs_%s.csv' % pname)
    L.atomic_write_csv(p2, R)
    p3 = os.path.join(od, 'random_paths_%s.npz' % pname)
    L.atomic_write_npz(p3, **{k.replace('|', '~'): v for k, v in paths.items()})
    p4 = os.path.join(od, 'random_daily_%s.npz' % pname)
    L.atomic_write_npz(p4, **{k.replace('|', '~'): v for k, v in daily.items()})
    L.write_receipt(L.next_rerun('stats_%s_%s' % (a.phase, pname)), [p1, p2, p3, p4], 'SUCCEEDED', n_rows=len(S), n_random_rows=len(R))
    print('%s：%d 行统计；%d 行随机参照' % (pname, len(S), len(R)), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
