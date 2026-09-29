# -*- coding: utf-8 -*-
"""E6k 逐描述符统计（plan §9 / §10.4 / §12；brief §6 / §7；E6j e6j_stats 同式，只 import 不改）。一段一个进程：
  --segment S [--mc-plan]  读 accounts/<段>/*.npz（确定性）与 randoms/<机制>/<段>/*.npz（随机，含 MC 增补分片）→
     results/<阶段>/descriptor_stats_<段>.csv：
       D / n（子 − 原父 8bp 日配对年化）、D_sc（MATCH-CAP）、D_imp（A 5 亿 κ .5）、D_str（A 10 亿 κ 1）、D_6bp / D_12bp、D_gross、
       se_H / se_2H（日历对齐 HAC，缺失日 u = 0）、turn_rel、pos_diff；
       相对比较（同段日配对）：op − 同测量 NATIVE、op − 同算子 C1、带 − 无带基础、HG − HG_ONLY、INC 链（INC − INC_DOSE、INC_DOSE − INC_SUPPORT0、
       INC_SUPPORT0 − NATIVE；附属 72）、剂量控制差（带 − DOSE）、COMMON_SUPPORT 四账户桥（N1−N0 = (C1−C0) + (C0−N0) + (N1−C1)）；
       暴露：组合层 size 差紧区间日均（T / LAG1）、编辑层 gap 日均（带符号；×100）、五分组最大超配（子 / 父）、小盘 30% 份额差、未知 size 份额、
       编辑数 / 换入资本份额 / 名数 / 资本、滚动 size 差（子 − 父，T / LAG1）；
     results/<阶段>/random_refs_<段>.csv：逐 (描述符, H, 机制) 随机均值 / 路径标准差 / MCSE / 路径数 / real − 随机均值
  --mc-plan 另写 results/<阶段>/mc_plan_<段>.csv：共享 u 流的比较组（段 × 任务 × 机制）取组内最大所需路径（MCSE ≤ .03），512 一批至 8,192。
读数门：推导段须 registration/seal_deriv.json 在且核对通过；后段须 seal_post.json。"""
import e6k_boot  # noqa: F401
import os
import sys
import glob
import json
import argparse

import numpy as np
import pandas as pd

import e6k_core as K
import e6j_stats as ST

A_POL, K_POL = 5.0, 0.5
A_STR, K_STR = 10.0, 1.0
MC_TARGET = 0.03
YEARS = None                         # 段内交易日的年份（main 里按账户日期设置）


def load_accounts(pname):
    """desc_id → dict(日数组)；target_id → dict(日数组)；desc_id → target_id / H。"""
    d, t, d2t, dH = {}, {}, {}, {}
    for f in sorted(glob.glob(K.P('accounts', pname, '*.npz'))):
        if os.path.basename(f).startswith('weights_'):
            continue
        z = K.npz(f)
        tg = [str(x) for x in z['targets']]
        TA = {k[2:]: z[k] for k in z.files if k.startswith('t_')}          # NpzFile 每次取键都整读：每个数组只取一次
        for j, tid in enumerate(tg):
            t[tid] = {k: v[j] for k, v in TA.items()}
        DA = {k[2:]: z[k] for k in z.files if k.startswith('d_')}
        dtg, dh = z['desc_target'], z['desc_H']
        for i, did in enumerate([str(x) for x in z['desc']]):
            d[did] = {k: v[i] for k, v in DA.items()}
            d2t[did] = tg[int(dtg[i])]
            dH[did] = int(dh[i])
    return d, t, d2t, dH


def seg_pair(a, b):
    return ST.seg_D(ST.paired(a, b)[0])


def imp(x, A, k):
    return x['net8'] - ST.impact_cost(x['bracket'], A, k)


def pid(did):
    """登记描述符的原父（K0 | 母体 | a0 | H | PARENT）。"""
    p = did.split('|')
    return 'K0|%s|a0|%s|PARENT' % (p[1], p[3])


def stats_row(did, c, p, H, T):
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
    r['MDE80'] = 2.80 * r['se_H']
    mt = float(np.mean(p['turn']))
    r['turn_rel'] = float(np.mean(c['turn'])) / mt - 1.0 if mt > 0 else np.nan
    r['pos_diff'] = float(np.mean(c['pos']) - np.mean(p['pos']))
    if YEARS is not None:                                               # 逐年配对增量（政策 d：17 年标签，2026 partial）
        for y in np.unique(YEARS):
            m = (YEARS == y) & np.isfinite(dd)
            r['Y%d' % y] = float(np.mean(dd[m])) * ST.ANN if m.any() else np.nan
            r['Yn%d' % y] = int(m.sum())
    r['net8_ann'] = float(np.nanmean(c['net8'])) * ST.ANN
    r['parent_net8_ann'] = float(np.nanmean(p['net8'])) * ST.ANN
    r['qmiss_share'] = float(np.nansum(c['qmiss']) / max(np.sum(c['turn']), 1e-300))
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
        r['edit_gap_mean_%s' % z] = float(np.mean(g[mg]) * 100.0) if mg.any() else np.nan       # 带符号（×100 百分位点）
        r['edit_gap_absmean_%s' % z] = abs(r['edit_gap_mean_%s' % z]) if mg.any() else np.nan   # LEGACY_EDIT5 口径 = |mean_t gap_t|·100
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


def random_refs(pname, d):
    rows = []
    for f in sorted(glob.glob(K.P('randoms', '*', pname, '*.npz'))):
        mech = os.path.basename(os.path.dirname(os.path.dirname(f)))
        z = K.npz(f)
        for i, (did, H) in enumerate(zip([str(x) for x in z['desc']], z['H'])):
            rows.append(dict(desc_id=did, H=int(H), mechanism=mech, file=os.path.basename(f), n=int(np.isfinite(z['ann'][i, :, 0]).sum()),
                             s1=float(np.nansum(z['ann'][i, :, 0])), s2=float(np.nansum(z['ann'][i, :, 0] ** 2))))
    if not rows:
        return pd.DataFrame()
    R = pd.DataFrame(rows).groupby(['desc_id', 'H', 'mechanism'], as_index=False).agg(n=('n', 'sum'), s1=('s1', 'sum'), s2=('s2', 'sum'),
                                                                                    shards=('file', 'count'))
    R['rand_mean'] = R.s1 / R.n
    R['rand_sd'] = np.sqrt(np.maximum(R.s2 / R.n - R.rand_mean ** 2, 0.0) * R.n / np.maximum(R.n - 1, 1))
    R['mcse'] = R.rand_sd / np.sqrt(R.n)
    real = []
    for r in R.itertuples():
        parts = r.desc_id.split("|")
        real_id = "|".join(parts[:3] + ["H%d" % r.H] + parts[4:])            # HG 持续性控制行（H ≠ 5）对应同目标的该 H 描述符
        dd = d.get(real_id)
        real.append(float(np.nanmean(dd["net8"])) * ST.ANN if dd is not None else np.nan)
    R['real_net8_ann'] = real
    R['real_minus_rand'] = R.real_net8_ann - R.rand_mean
    return R.drop(columns=['s1', 's2'])


def mc_plan(R, pname):
    RR = pd.read_csv(K.P('registry', 'randoms_E6k.csv'))
    task = dict(zip(RR.desc_id, RR.task))
    R = R.copy()
    R['task'] = R.desc_id.map(task)
    R['n_req'] = np.ceil((R.rand_sd / MC_TARGET) ** 2)
    out = []
    for (t, m), g in R.groupby(['task', 'mechanism']):
        have = int(g.n.min())
        need = int(min(8192, max(have, g.n_req.max())))
        tgt = have if need <= have else int(min(8192, have + 512 * np.ceil((need - have) / 512.0)))
        out.append(dict(segment=pname, task=t, mechanism=m, have=have, need_max=int(g.n_req.max()), target=tgt,
                        topup=max(0, tgt - have), worst_mcse=float(g.mcse.max())))
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--phase', default='deriv')
    ap.add_argument('--mc-plan', action='store_true')
    ap.add_argument('--trial', action='store_true')                # 试跑：只允许 E6K_RES 指向临时目录时跳过封存核对
    a = ap.parse_args()
    pname = a.segment
    od = K.P('results', a.phase)
    os.makedirs(od, exist_ok=True)
    if a.mc_plan:
        # 队列完整性（2026-09-29 补）：有分片缺回执时增补的起点 = 已有路径数会与缺失分片的路径区间重叠，先补跑再规划
        import e6k_seal as SEAL
        st_ = SEAL.receipts('deriv' if pname in K.DERIV_SEGS else 'post')
        miss = [n for n in SEAL.queued_receipts(a.phase) if ('_%s_' % pname) in n and st_.get(n) != 'SUCCEEDED']
        if miss:
            raise RuntimeError('MC 规划前队列未全部成功（%d 个缺回执，例 %s）：先补跑' % (len(miss), miss[:3]))
        # MC 规划只读随机路径的路径间离散（机制内），不读真实账户（real 列在规划表里不输出）
        d = {}
        R = random_refs_nodet(pname)
        P = mc_plan(R, pname)
        p = os.path.join(od, 'mc_plan_%s_%s.csv' % (pname, pd.Timestamp.now().strftime('%H%M%S')))
        K.atomic_write_csv(p, P)
        print(P.topup.describe().to_string(), '\n需增补组数', int((P.topup > 0).sum()), flush=True)
        return 0
    import e6k_seal as SEAL
    if a.trial:
        if not K.RES.startswith(K.TRIAL):
            raise RuntimeError('--trial 只允许在临时目录')
    else:
        ok, bad = SEAL.verify('deriv' if pname in K.DERIV_SEGS else 'post')
        if not ok:
            raise RuntimeError('封存核对失败：%s' % bad[:5])
    global YEARS
    d, t, d2t, dH = load_accounts(pname)
    T = len(next(iter(d.values()))['net8'])
    z0 = np.load(sorted(f for f in glob.glob(K.P('accounts', pname, '*.npz')) if not os.path.basename(f).startswith('weights_'))[0], allow_pickle=False)
    YEARS = pd.to_datetime(pd.Index([str(x) for x in z0['dates']])).year.values
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    A = pd.read_csv(K.P('registry', 'accessory_E6k.csv'))
    rows = []
    for r in D.itertuples():
        if r.op == 'PARENT' or r.desc_id not in d:
            continue
        c = d[r.desc_id]
        p = d[r.parent_desc]
        s = stats_row(r.desc_id, c, p, int(r.H), T)
        s.update(desc_id=r.desc_id, segment=pname, kind='registered')
        nc1 = 'C1|%s|a%s|H%d|NATIVE' % (r.mother, ('%g' % r.alpha), int(r.H)) if r.meas in ('S', 'M', 'Q', 'C1', 'SM') else ''
        for lab, other in (('vs_native', r.native_desc), ('vs_C1', r.c1_desc), ('vs_base', r.base_desc), ('vs_hg_only', r.hg_only_desc),
                           ('vs_nativeC1', nc1)):
            if isinstance(other, str) and other and other in d and other != r.desc_id:
                s['D_%s' % lab] = seg_pair(c['net8'], d[other]['net8'])[0]
                s['Dg_%s' % lab] = seg_pair(c['gross'], d[other]['gross'])[0]
        s.update(target_expo(t[d2t[r.desc_id]], t[d2t[r.parent_desc]]))
        rows.append(s)
    for r in A.itertuples():
        if r.acc_id not in d:
            continue
        c = d[r.acc_id]
        if r.kind == "COMMON_SUPPORT_PARENT":
            continue
        par = r.compare_to if r.kind == "COMMON_SUPPORT_CHILD" else pid(r.acc_id.split("|", 1)[1])
        p = d[par]
        s = stats_row(r.acc_id, c, p, int(r.H), T)
        s.update(desc_id=r.acc_id, segment=pname, kind=r.kind)
        cmp_ = r.compare_to if isinstance(r.compare_to, str) else ''
        if cmp_ in d and r.kind != "COMMON_SUPPORT_CHILD":
            s['D_vs_compare'] = seg_pair(c['net8'], d[cmp_]['net8'])[0]
        if r.kind == 'COMMON_SUPPORT_CHILD':                           # 四账户桥
            n1 = d[r.acc_id[3:]]['net8']
            n0 = d[pid(r.acc_id[3:])]['net8']
            c1, c0 = c['net8'], p['net8']
            s['N1_minus_N0'] = seg_pair(n1, n0)[0]
            s['C1_minus_C0'] = seg_pair(c1, c0)[0]
            s['C0_minus_N0'] = seg_pair(c0, n0)[0]
            s['N1_minus_C1'] = seg_pair(n1, c1)[0]
        rows.append(s)
    S = pd.DataFrame(rows)
    p1 = os.path.join(od, 'descriptor_stats_%s.csv' % pname)
    K.atomic_write_csv(p1, S)
    R = random_refs(pname, d)
    p2 = os.path.join(od, 'random_refs_%s.csv' % pname)
    K.atomic_write_csv(p2, R)
    K.write_receipt('stats_%s_%s' % (a.phase, pname), [p1, p2], 'SUCCEEDED', n_rows=len(S), n_random_rows=len(R))
    print('%s: %d 行统计；%d 行随机参照' % (pname, len(S), len(R)), flush=True)
    return 0


def random_refs_nodet(pname):
    """MC 规划：只统计随机路径（不读真实账户）。"""
    rows = []
    for f in sorted(glob.glob(K.P('randoms', '*', pname, '*.npz'))):
        mech = os.path.basename(os.path.dirname(os.path.dirname(f)))
        z = K.npz(f)
        for i, (did, H) in enumerate(zip([str(x) for x in z['desc']], z['H'])):
            x = z['ann'][i, :, 0]
            rows.append(dict(desc_id=did, H=int(H), mechanism=mech, n=int(np.isfinite(x).sum()), s1=float(np.nansum(x)), s2=float(np.nansum(x ** 2))))
    R = pd.DataFrame(rows).groupby(['desc_id', 'H', 'mechanism'], as_index=False).agg(n=('n', 'sum'), s1=('s1', 'sum'), s2=('s2', 'sum'))
    R['rand_mean'] = R.s1 / R.n
    R['rand_sd'] = np.sqrt(np.maximum(R.s2 / R.n - R.rand_mean ** 2, 0.0) * R.n / np.maximum(R.n - 1, 1))
    R['mcse'] = R.rand_sd / np.sqrt(R.n)
    return R


if __name__ == '__main__':
    sys.exit(main())
