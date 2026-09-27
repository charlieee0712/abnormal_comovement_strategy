# -*- coding: utf-8 -*-
"""E6j P 块政策评分卡（plan §4.5；brief W07 / W08 / W09 / W12；RULING 第 15 项六条 + 三句加法 + 实施条件）。
读 accounts/P/<段>/<形态>.npz、summary.csv、randoms/P/<段>/<形态>__<臂>.npz；只在全部四段账户与随机回执齐全后运行。
两个解释 profile 分列、不交叉拼接：FULL（主，W07）与 G4（并印）。结论词只有 通过 / 不通过 / 不可判 / 结构依赖。
输出 results/pilot_policy.csv（逐对象）+ pilot_policy_additions.csv（三句加法）+ pilot_policy_bootstrap_*.csv。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import glob

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_stats as ST

ACC = os.path.join(J.RES, 'accounts', 'P')
RAN = os.path.join(J.RES, 'randoms', 'P')
OUT = os.path.join(J.RES, 'results_P', 'dryrun') if '--dryrun' in sys.argv else os.path.join(J.RES, 'results_P')
FORMS = ('A4b', 'M_mean3_v2', 'M_union3_v2', 'A4b_CVRv5', 'M_mean3_v2_CVRv5', 'M_union3_v2_CVRv5')
MAIN_FORM = 'A4b_CVRv5'
ARMS_MAIN = ('S', 'M', 'SM', 'C1')
DELTAS = (0.05, 0.10, 0.15)
A_POL, K_POL = 5.0, 0.5            # f：政策情景
A_STR, K_STR = 10.0, 1.0           # 压力列
SIZE_PCT = 5.0                     # 市值通道（百分位点）
DTURN = 0.10
MC_TARGET = 0.03                   # plan §8.1：MCSE 目标（年化百分点），超过按 512 路径增补（e6j_mc_topup.py）
MC_Z = 2.0                         # 执行端事前声明（读数前落盘）：|真实 − 随机均值| < 2·MCSE 即"MC 误差仍影响符号"（plan §8.1 / §4.5）
SIGN_TOL = 1e-9                    # e-资本 0 的数值舍入容差（年化百分点）


def tri_sign(x):
    """带数值舍入容差的符号：|x| ≤ SIGN_TOL → 0；NaN 保留。"""
    x = np.asarray(x, float)
    return np.where(np.isnan(x), np.nan, np.where(np.abs(x) <= SIGN_TOL, 0.0, np.sign(x)))


def e_rand_status(df, post):
    """两后段 real − 随机均值 > 0。逐段：≥ MC_Z·MCSE 且 > 0 → 正已定；≤ 0 且 |·| ≥ MC_Z·MCSE → 非正已定；其余 MC 未定。
    任一段非正已定 → FAIL；两段正已定 → PASS；有缺 → NA；否则 MC_UNRESOLVED。"""
    out = []
    for _, r in df.iterrows():
        st_ = []
        for s in post:
            d, se = r.get('rand_IID_%s' % s, np.nan), r.get('mcse_IID_%s' % s, np.nan)
            if not (np.isfinite(d) and np.isfinite(se)):
                st_.append('NA')
            elif d > 0 and d >= MC_Z * se:
                st_.append('POS')
            elif d <= 0 and -d >= MC_Z * se:
                st_.append('NONPOS')
            else:
                st_.append('UNRES')
        out.append('FAIL' if 'NONPOS' in st_ else 'PASS' if all(x == 'POS' for x in st_) else 'NA' if 'NA' in st_ else 'MC_UNRESOLVED')
    return out


def verdict(r, prof):
    """已定的 FAIL 优先（列出全部不满足项）；无 FAIL 而有未定项 → 不可判（列出）；否则通过。δ 主值 .10。"""
    if r.arm not in ARMS_MAIN:
        return '列对象（不评分）'
    fails, pend = [], []
    for name, st_ in (('c', r['c_%s_d10' % prof]), ('d', r.d_ok), ('f', r['f_%s_d10' % prof]), ('正向门槛', r['positive_%s' % prof])):
        if not st_:
            fails.append(name)
    for name, st_ in (('e资本', r['e_cap_%s' % prof]), ('e随机', r.e_rand)):
        if st_ == 'FAIL':
            fails.append(name)
        elif st_ != 'PASS':
            pend.append('%s:%s' % (name, st_))
    if r.size_status == 'FAIL':
        fails.append('市值通道')
    if fails:
        return '不通过（%s）' % '、'.join(fails)
    if pend:
        return '不可判（%s）' % '、'.join(pend)
    return '通过'


def load_seg(seg, form):
    z = np.load(os.path.join(ACC, seg, '%s.npz' % form), allow_pickle=False)
    return {k: z[k] for k in z.files}


def parse(did):
    p = did.split('|')
    form, arm = p[1], p[2]
    if arm == 'C0':
        return form, 'C0', 0.0, int(p[-1][1:])
    if arm == 'COL':
        return form, 'COL:' + p[3], float(p[5][2:]), int(p[6][1:])
    return form, arm, float(p[5][2:]), int(p[6][1:])          # P|形态|臂|成员|方向|a=α|H


def arrays_for(form):
    """{(arm, α, H): {seg: dict(字段 → 日序列)}}；母体键 ('C0', 0.0, H)。"""
    out, dates = {}, {}
    for seg in J.SEGMENTS:
        L = load_seg(seg, form)
        dates[seg] = L['dates']
        for i, did in enumerate(L['desc']):
            f, arm, a, H = parse(str(did))
            out.setdefault((arm, a, H), {})[seg] = {k: L[k][i] for k in ('gross', 'pos', 'turn', 'net8', 'sc_child', 'sc_parent', 'bracket', 'qmiss')}
    return out, dates


def object_stats(ch, pa, dates, H):
    """一个子账户 vs 同 H 母体：四段 D、FULL / G4、逐年、同资本、冲击、6 / 12bp、HAC、Δturn。"""
    r = {}
    Ds, ns, dsc, nsc, Dimp, nimp, Dstr, D6, D12, se, se2 = [], [], [], [], [], [], [], [], [], [], []
    d_all, dt_all = [], []
    by_seg = {}
    for seg in J.SEGMENTS:
        c, p = ch[seg], pa[seg]
        d, _ = ST.paired(c['net8'], p['net8'])
        D, n = ST.seg_D(d); Ds.append(D); ns.append(n); by_seg[seg] = d
        ds_, _ = ST.paired(c['sc_child'], c['sc_parent']); D2, n2 = ST.seg_D(ds_); dsc.append(D2); nsc.append(n2)
        ci_ = c['net8'] - ST.impact_cost(c['bracket'], A_POL, K_POL); pi_ = p['net8'] - ST.impact_cost(p['bracket'], A_POL, K_POL)
        D3, n3 = ST.seg_D(ST.paired(ci_, pi_)[0]); Dimp.append(D3); nimp.append(n3)
        cs_ = c['net8'] - ST.impact_cost(c['bracket'], A_STR, K_STR); ps_ = p['net8'] - ST.impact_cost(p['bracket'], A_STR, K_STR)
        Dstr.append(ST.seg_D(ST.paired(cs_, ps_)[0])[0])
        for cost, lst in ((6.0, D6), (12.0, D12)):
            lst.append(ST.seg_D(ST.paired(c['gross'] - c['turn'] * cost / 1e4, p['gross'] - p['turn'] * cost / 1e4)[0])[0])
        se.append(ST.hac_se(d, H)[0] * ST.ANN); se2.append(ST.hac_se(d, max(2 * H, 20))[0] * ST.ANN)
        d_all.append(d); dt_all.append(dates[seg])
        r['turn_rel_%s' % seg] = (float(np.mean(c['turn'])) / float(np.mean(p['turn'])) - 1.0) if np.mean(p['turn']) > 0 else np.nan
        r['pos_diff_%s' % seg] = float(np.mean(c['pos']) - np.mean(p['pos']))
        r['qmiss_share_%s' % seg] = float(np.nansum(c['qmiss']) / max(np.sum(c['turn']), 1e-300))
    for seg, D, n, D2, D3, s1, s2 in zip(J.SEGMENTS, Ds, ns, dsc, Dimp, se, se2):
        r['D_%s' % seg] = D; r['n_%s' % seg] = n; r['Dsc_%s' % seg] = D2; r['Dimp_%s' % seg] = D3
        r['se_H_%s' % seg] = s1; r['se_2H_%s' % seg] = s2; r['MDE80_%s' % seg] = 2.80 * s1
    r['FULL'], r['G4'] = ST.full_g4(Ds, ns)
    r['FULL_sc'], r['G4_sc'] = ST.full_g4(dsc, nsc)
    r['FULL_imp'], r['G4_imp'] = ST.full_g4(Dimp, nimp)
    r['FULL_str'] = ST.full_g4(Dstr, ns)[0]
    r['FULL_6bp'] = ST.full_g4(D6, ns)[0]; r['FULL_12bp'] = ST.full_g4(D12, ns)[0]
    d = np.concatenate(d_all); dt = np.concatenate(dt_all)
    y = ST.yearly(d, dt)
    for k, v in y.items():
        r['Y%d' % k] = v
    vals = [v for v in y.values() if np.isfinite(v)]
    r['years_pos'] = int(sum(v > 0 for v in vals)); r['years_n'] = len(vals)
    r['years_pos_2010_2025'] = int(sum(y[k] > 0 for k in range(2010, 2026) if np.isfinite(y[k])))
    fullse = ST.hac_se(d, H)[0] * ST.ANN
    r['FULL_se_H'] = fullse; r['FULL_MDE80'] = 2.80 * fullse
    return r, by_seg


_RCACHE = {}


def random_paths(seg, form, arm):
    """合并该 (段, 形态, 臂) 的全部随机分片（主 1,024 路径 + MC 增补分片）：{机制: ann (路径, α, H, 4)}。"""
    k = (seg, form, arm)
    if k not in _RCACHE:
        acc = {}
        files = [os.path.join(RAN, seg, '%s__%s.npz' % (form, arm))] + sorted(glob.glob(os.path.join(RAN, seg, '%s__%s_p*.npz' % (form, arm))))
        for p in [f for f in files if os.path.exists(f)]:          # 精确匹配臂名（'S' 不得匹配 'SM'）
            z = np.load(p, allow_pickle=False)
            for mi, m in enumerate([str(x) for x in z['mechs']]):
                acc.setdefault(m, []).append((z['alphas'], z['Hs'], z['ann'][mi]))
        _RCACHE[k] = acc
    return _RCACHE[k]


def random_ref(seg, form, arm, a, H, real_ann):
    """R-MATCH-SRC（IID）主参照：real − mean_paths(random)；MCSE = sd / √n（全部分片合并）；另报其余机制。"""
    acc = random_paths(seg, form, arm)
    out = {}
    for m, parts in acc.items():
        xs = []
        for alphas, Hs, ann in parts:
            ai = list(np.round(alphas, 6)).index(round(a, 6)); hi = list(Hs).index(H)
            xs.append(ann[:, ai, hi, 0])
        x = np.concatenate(xs); x = x[np.isfinite(x)]
        out['rand_%s_%s' % (m, seg)] = float(real_ann - x.mean()) if len(x) else np.nan
        out['mcse_%s_%s' % (m, seg)] = float(x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else np.nan
        out['npaths_%s_%s' % (m, seg)] = len(x)
    return out


def main():
    if '--dryrun' not in sys.argv:                        # 正式读数：P 包封存回执之后（plan §10.2）
        import e6j_seal as SEAL
        ok, bad = SEAL.verify('P')
        if not ok:
            raise RuntimeError('P 包封存核对失败：%d 个文件 hash 不符或回执不全' % len(bad))
    os.makedirs(OUT, exist_ok=True)
    summ = pd.concat([pd.read_csv(os.path.join(ACC, s, 'summary.csv')) for s in J.SEGMENTS], ignore_index=True)
    exl = pd.read_csv(os.path.join(J.RES, 'registry', 'exposure_ledger.csv'))
    alias = set(exl[exl.exposure_type == 'alias_of'].descriptor_id)
    rows, boots = [], []
    for form in FORMS:
        A, dates = arrays_for(form)
        for (arm, a, H), ch in sorted(A.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])):
            if arm == 'C0':
                continue
            pa = A[('C0', 0.0, H)]
            r, by_seg = object_stats(ch, pa, dates, H)
            did = ('P|%s|%s' % (form, arm)) if not arm.startswith('COL') else ('P|%s|COL|%s' % (form, arm[4:]))
            r.update(form=form, arm=arm, alpha=a, H=H, main_config=(a == 0.25 and H == 5),
                     historical_exposed=any(x.startswith(did) and x.endswith('a=%s|H%d' % (a, H)) for x in alias))
            for seg in J.SEGMENTS:
                g = summ[(summ.segment == seg) & (summ.form == form) & (summ.arm == arm) & (np.isclose(summ.alpha, a)) & (summ.H == H)]
                if len(g):
                    r['size_gap_pctpt_%s' % seg] = abs(float(g.size_gap_mean.iloc[0])) * 100.0
                    r['matched_capital_share_%s' % seg] = float(g.matched_capital_share.iloc[0])
                if arm in ARMS_MAIN:
                    real_ann = float(np.nanmean(ch[seg]['net8'])) * ST.ANN
                    r.update(random_ref(seg, form, arm, a, H, real_ann))
            if a == 0.25 and H == 5 and arm in ARMS_MAIN:
                for L in (20, 60):
                    for centered in (False, True):
                        dr = ST.bootstrap_full(by_seg, L, 2000, 'P-main', centered)
                        boots.append(dict(form=form, arm=arm, L=L, centered=centered, q025=float(np.nanquantile(dr, .025)),
                                          q50=float(np.nanquantile(dr, .5)), q975=float(np.nanquantile(dr, .975))))
            rows.append(r)
    df = pd.DataFrame(rows)
    # ---- 六条（逐 δ、逐 profile）。每项三态 PASS / FAIL / 不可判：已定的 FAIL 优先于不可判（不确定只在决定结论时才让结论不可判）
    for prof in ('FULL', 'G4'):
        for dl in DELTAS:
            tag = '%s_d%02d' % (prof, int(round(dl * 100)))
            c_ok = np.all([df['D_%s' % s] >= -dl for s in J.SEGMENTS], axis=0)          # NA 不自动满足（plan §4.5 c）
            f_ok = np.all([df['Dimp_%s' % s] >= -dl for s in J.SEGMENTS], axis=0)
            df['c_' + tag] = c_ok; df['f_' + tag] = f_ok
        s_nat, s_sc = tri_sign(df[prof].values), tri_sign(df['%s_sc' % prof].values)   # 0 按数值舍入容差（不设收益死区）
        df['e_cap_' + prof] = np.where(np.isnan(s_sc) | np.isnan(s_nat), 'NA', np.where(s_nat == s_sc, 'PASS', 'FAIL'))
        df['positive_' + prof] = df[prof] >= 0.10
    df['d_ok'] = df.years_pos >= 12
    post = list(J.POST_SEGS)
    df['e_rand'] = e_rand_status(df, post)                  # R-MATCH-SRC（IID）两后段；MC 误差影响符号 → MC_UNRESOLVED
    df['mc_ok'] = np.all([df.get('mcse_IID_%s' % s, pd.Series(np.inf, index=df.index)) <= MC_TARGET for s in post], axis=0)   # 描述列，不作闸
    gaps = np.column_stack([df.get('size_gap_pctpt_%s' % s, pd.Series(np.nan, index=df.index)).values for s in J.SEGMENTS])
    df['size_status'] = np.where(np.all(np.isnan(gaps), axis=1), 'N/A（无两边都有的编辑日）',
                                 np.where(np.nanmax(np.where(np.isnan(gaps), -np.inf, gaps), axis=1) > SIZE_PCT, 'FAIL', 'PASS'))
    df['size_na_segments'] = [','.join(s for s, g in zip(J.SEGMENTS, row) if np.isnan(g)) for row in gaps]
    df['dturn_flag'] = np.any([df['turn_rel_%s' % s] > DTURN for s in J.SEGMENTS], axis=0)
    for prof in ('FULL', 'G4'):
        df['policy_' + prof] = [verdict(r, prof) for _, r in df.iterrows()]
    df['policy_aggregation'] = 'FULL_E6I_ALL4（主）/ G4（并印）'
    df['random_ref'] = 'R-MATCH-SRC（IID，两后段）'
    cls = lambda s: s.str[:3]                               # 通过 / 不通过 / 不可判（原因另列）
    df['POLICY_INTERPRETATION_PENDING'] = df.arm.isin(ARMS_MAIN) & (cls(df.policy_FULL) != cls(df.policy_G4))
    df['structure_dependent'] = False
    for arm in ARMS_MAIN:
        for a in (0.125, 0.25, 0.5):
            for H in (3, 5, 10, 20):
                m = (df.arm == arm) & np.isclose(df.alpha, a) & (df.H == H)
                others = df[m & (df.form != MAIN_FORM)]
                dep = bool((others[['D_%s' % s for s in J.SEGMENTS]] < -0.10).any(axis=None))
                df.loc[m, 'structure_dependent'] = dep
    df['mechanism_status'] = '未分离（见 B 块与诊断）'
    df['replication_status'] = np.where(df.historical_exposed, 'historical_exposed（E6i 已见同一账户）', '本轮首次')
    df['deployment_authorized'] = False
    p = os.path.join(OUT, 'pilot_policy.csv'); J.atomic_write_csv(p, df)
    # ---- 三句加法（每形态 α .25 × H5）
    def merged_diff(m, a1, a2, prof):
        """配对差的合并（plan §4.5：先对配对差逐段、再按 profile 聚合；不先分别聚合后相减）。同形态同 H 母体 → 两臂有效日相同。"""
        d = np.array([m.loc[a1, 'D_%s' % s] - m.loc[a2, 'D_%s' % s] for s in J.SEGMENTS], float)
        n = np.array([m.loc[a1, 'n_%s' % s] for s in J.SEGMENTS], float)
        full, g4 = ST.full_g4(d, n)
        return (full if prof == 'FULL' else g4), d

    add = []
    for form in FORMS:
        for prof in ('FULL', 'G4'):
            m = df[(df.form == form) & (df.main_config)].set_index('arm')
            elig = [a for a in ('C1', 'M', 'S') if a in m.index and m.loc[a, 'policy_' + prof] == '通过']
            best = sorted(elig, key=lambda a: (-m.loc[a, prof], ('C1', 'M', 'S').index(a)))[0] if elig else None
            chosen, why = None, ''
            if 'C1' in elig:
                chosen, why = 'C1', 'C1 合格 → 默认简单 C1'
                beat = []
                for arm in ('M', 'S'):
                    if arm in elig:
                        md, dseg = merged_diff(m, arm, 'C1', prof)
                        if int((dseg >= 0.05).sum()) >= 3 and md >= 0.05:
                            beat.append((md, arm))
                if beat:
                    md, arm = sorted(beat, key=lambda x: (-x[0], ('M', 'S').index(x[1])))[0]
                    chosen, why = arm, '%s − C1：≥ 3/4 段 ≥ +.05，合并配对差 %.3f ≥ +.05' % (arm, md)
            elif elig:
                chosen, why = best, 'C1 不合格；取最佳合格单臂（不要求打赢不合格的 C1）'
            if 'SM' in m.index and m.loc['SM', 'policy_' + prof] == '通过':
                if best is None:
                    chosen, why = 'SM', '无合格单臂；SM 自身满足六条与正向门槛，作独立复杂候选'
                else:
                    md, _ = merged_diff(m, 'SM', best, prof)
                    if md >= 0.10:
                        chosen, why = 'SM', 'SM − 最佳合格单臂 %s 合并配对差 %.3f ≥ +.10' % (best, md)
            add.append(dict(form=form, profile=prof, eligible='|'.join(elig), best_single=best or '', chosen=chosen or '无', why=why))
    pa = os.path.join(OUT, 'pilot_policy_additions.csv'); J.atomic_write_csv(pa, pd.DataFrame(add))
    pb = os.path.join(OUT, 'pilot_policy_bootstrap.csv'); J.atomic_write_csv(pb, pd.DataFrame(boots))
    if '--dryrun' not in sys.argv:
        J.write_receipt('policy_P', [p, pa, pb], 'SUCCEEDED', n_objects=len(df))
    return 0


if __name__ == '__main__':
    sys.exit(main())
