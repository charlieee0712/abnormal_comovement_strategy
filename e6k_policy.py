# -*- coding: utf-8 -*-
"""E6k 政策评分（brief §6 / W12；plan §9；registration/policy_profiles_E6k.json + _amend_1.json；e6j_policy_p.verdict 同式）。
四段统计齐（results/full/descriptor_stats_<段>.csv、random_refs_<段>.csv）且 seal_deriv / seal_post 核对通过后运行。
逐描述符 × 五列 size profile（LEGACY_EDIT5 / PROPOSED_PORT3_T / PROPOSED_PORT3_LAG1 / EXEC_DISCLOSE_ONLY / EXEC_LEADER_VS_PARENT）× {FULL, G4}：
  c（四段 D ≥ −δ，δ .05 / .10 / .15；NA 不满足）/ d（正年 ≥ 12 / 17）/ e 资本（FULL 与 FULL_sc 同号，1e−9 容差）/ e 随机（LEGACY 两后段，
  2·MCSE 三态；无随机 = RANDOM_NOT_SCHEDULED）/ f（A 5 亿 κ .5 四段 D_imp ≥ −δ）/ 正向（≥ +.10）/ size（按 profile）→ 通过 / 不通过（列已定失败项）/ 不可判（列未定项）。
原生对象三句加法（PX1）；新算子不 chosen（PX2），并印相对 NATIVE_C1 / 同测量 NATIVE / 同算子 C1 的配对差；五标签；边缘距离。
policy_provisional = true；不在出数后择优 profile。"""
import e6k_boot  # noqa: F401
import os
import sys

import numpy as np
import pandas as pd

import e6k_core as K
import e6j_stats as ST
import e6k_seal as SEAL

SEGS = K.SEGMENTS
POST = K.POST_SEGS
DELTAS = (0.05, 0.10, 0.15)
MC_Z, SIGN_TOL = 2.0, 1e-9
PROFILES = ('LEGACY_EDIT5', 'PROPOSED_PORT3_T', 'PROPOSED_PORT3_LAG1', 'EXEC_DISCLOSE_ONLY', 'EXEC_LEADER_VS_PARENT')


def tri_sign(x):
    return np.nan if not np.isfinite(x) else (0.0 if abs(x) <= SIGN_TOL else float(np.sign(x)))


def e_rand(row):
    if row.get('family') in ('OWN', 'HG_ONLY'):                       # PX6：无新内容可置换
        return 'NO_NEW_CONTENT_TO_PERMUTE'
    st = []
    for s in POST:
        d, se = row.get('rmr_%s' % s, np.nan), row.get('mcse_%s' % s, np.nan)
        if not (np.isfinite(d) and np.isfinite(se)):
            st.append('NA')
        elif d > 0 and d >= MC_Z * se:
            st.append('POS')
        elif d <= 0 and -d >= MC_Z * se:
            st.append('NONPOS')
        else:
            st.append('UNRES')
    if 'NONPOS' in st:
        return 'FAIL'
    if all(x == 'POS' for x in st):
        return 'PASS'
    if 'NA' in st:
        return 'RANDOM_NOT_SCHEDULED' if row.get('random_scheduled') is False else 'NA'
    return 'MC_UNRESOLVED'


def size_status(row, prof):
    if prof == 'EXEC_DISCLOSE_ONLY':
        return 'PASS'
    if prof == 'LEGACY_EDIT5':
        g = np.array([row.get('edit_gap_absmean_T_%s' % s, np.nan) for s in SEGS], float)
        if np.all(np.isnan(g)):
            return 'N/A'
        return 'FAIL' if np.nanmax(g) > 5.0 else 'PASS'
    if prof in ('PROPOSED_PORT3_T', 'PROPOSED_PORT3_LAG1'):
        z = 'T' if prof.endswith('_T') else 'L'
        st = []
        for s in SEGS:
            lo, hi = row.get('port_size_lo_%s_%s' % (z, s), np.nan), row.get('port_size_hi_%s_%s' % (z, s), np.nan)
            if not (np.isfinite(lo) and np.isfinite(hi)):
                st.append('NA')
            elif lo >= -3.0 and hi <= 3.0:
                st.append('PASS')
            elif hi < -3.0 or lo > 3.0:
                st.append('FAIL')
            else:
                st.append('SIZE_PARTIALLY_IDENTIFIED')
        if 'FAIL' in st:
            return 'FAIL'
        if all(x == 'PASS' for x in st):
            return 'PASS'
        return 'SIZE_PARTIALLY_IDENTIFIED' if 'SIZE_PARTIALLY_IDENTIFIED' in st else 'N/A'
    if prof == 'EXEC_LEADER_VS_PARENT':
        st = []
        for s in SEGS:
            c, p = row.get('lv5_mean_%s' % s, np.nan), row.get('parent_lv5_mean_%s' % s, np.nan)
            if not np.isfinite(c):
                st.append('NA')
            else:
                st.append('PASS' if c <= max(0.03, p if np.isfinite(p) else 0.03) + 1e-12 else 'FAIL')
        return 'FAIL' if 'FAIL' in st else ('PASS' if all(x == 'PASS' for x in st) else 'N/A')
    raise ValueError(prof)


def verdict(row, agg, prof, delta=0.10):
    fails, pend = [], []
    tag = 'd%02d' % int(round(delta * 100))
    for name, ok in (('c', row['c_%s' % tag]), ('d', row['d_ok']), ('f', row['f_%s' % tag]), ('正向门槛', row['positive_%s' % agg])):
        if not ok:
            fails.append(name)
    for name, st in (('e资本', row['e_cap_%s' % agg]), ('e随机', row['e_rand'])):
        if st == 'FAIL':
            fails.append(name)
        elif st != 'PASS':
            pend.append('%s:%s' % (name, st))
    ss = row['size_%s' % prof]
    if ss == 'FAIL':
        fails.append('size(%s)' % prof)
    elif ss not in ('PASS', 'N/A'):
        pend.append('size:%s' % ss)
    if fails:
        return '不通过（%s）' % '、'.join(fails)
    if pend:
        return '不可判（%s）' % '、'.join(pend)
    return '通过'


def main():
    for pkg in ('deriv', 'post'):
        ok, bad = SEAL.verify(pkg)
        if not ok:
            raise RuntimeError('seal_%s 核对失败：%s' % (pkg, bad[:5]))
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    X = pd.read_csv(K.P('registry', 'selection_exposure_ledger_E6k.csv'))
    S = {s: pd.read_csv(K.P('results', 'full', 'descriptor_stats_%s.csv' % s)).set_index('desc_id') for s in SEGS}
    R = pd.concat([pd.read_csv(K.P('results', 'full', 'random_refs_%s.csv' % s)).assign(segment=s) for s in SEGS], ignore_index=True)
    leg = R[R.mechanism == 'LEGACY_POLICY_RANDOM']
    rows = []
    for r in D[D.op != 'PARENT'].itertuples():
        row = dict(desc_id=r.desc_id, meas=r.meas, mother=r.mother, alpha=r.alpha, H=r.H, op=r.op, family=r.family, primary144=r.primary144,
                   c1_hi=r.c1_hi, random_scheduled=(r.random == 'LEGACY+NEW'))
        Ds, ns, Dsc, Dimp = [], [], [], []
        for s in SEGS:
            x = S[s].loc[r.desc_id] if r.desc_id in S[s].index else None
            for k in ('D', 'n', 'D_sc', 'D_imp', 'D_str', 'D_6bp', 'D_12bp', 'D_vs_native', 'D_vs_C1', 'D_vs_nativeC1', 'edit_gap_absmean_T',
                      'edit_gap_mean_T', 'port_size_lo_T', 'port_size_hi_T', 'port_size_lo_L', 'port_size_hi_L', 'lv5_mean', 'parent_lv5_mean',
                      'small30_delta', 'unkT_mean', 'turn_rel', 'se_H'):
                row['%s_%s' % (k, s)] = float(x[k]) if (x is not None and k in x.index and pd.notna(x[k])) else np.nan
            Ds.append(row['D_%s' % s]); ns.append(row['n_%s' % s]); Dsc.append(row['D_sc_%s' % s]); Dimp.append(row['D_imp_%s' % s])
            if x is not None:
                for k in x.index:
                    if k.startswith('Y') and k[1:].isdigit():
                        row[k] = float(x[k]) if pd.notna(x[k]) else np.nan
            lr = leg[(leg.desc_id == r.desc_id) & (leg.H == r.H) & (leg.segment == s)]
            row['rmr_%s' % s] = float(lr.real_minus_rand.iloc[0]) if len(lr) else np.nan
            row['mcse_%s' % s] = float(lr.mcse.iloc[0]) if len(lr) else np.nan
            row['npaths_%s' % s] = int(lr.n.iloc[0]) if len(lr) else 0
        row['FULL'], row['G4'] = ST.full_g4(Ds, ns)
        row['FULL_sc'], row['G4_sc'] = ST.full_g4(Dsc, ns)
        row['FULL_imp'], row['G4_imp'] = ST.full_g4(Dimp, ns)
        for dl in DELTAS:
            tag = 'd%02d' % int(round(dl * 100))
            row['c_%s' % tag] = bool(np.all([np.isfinite(v) and v >= -dl for v in Ds]))
            row['f_%s' % tag] = bool(np.all([np.isfinite(v) and v >= -dl for v in Dimp]))
        for agg in ('FULL', 'G4'):
            sn, sc = tri_sign(row[agg]), tri_sign(row['%s_sc' % agg])
            row['e_cap_%s' % agg] = 'NA' if (np.isnan(sn) or np.isnan(sc)) else ('PASS' if sn == sc else 'FAIL')
            row['positive_%s' % agg] = bool(np.isfinite(row[agg]) and row[agg] >= 0.10)
        ys = {int(k[1:]): v for k, v in row.items() if k.startswith('Y') and k[1:].isdigit()}
        vals = [v for v in ys.values() if np.isfinite(v)]
        row['years_pos'] = int(sum(v > 0 for v in vals))
        row['years_n'] = len(vals)
        row['years_pos_2010_2025'] = int(sum(ys[y] > 0 for y in range(2010, 2026) if y in ys and np.isfinite(ys[y])))
        row['d_ok'] = row['years_pos'] >= 12
        row['e_rand'] = e_rand(row)
        for prof in PROFILES:
            row['size_%s' % prof] = size_status(row, prof)
        for prof in PROFILES:
            for agg in ('FULL', 'G4'):
                row['policy_%s_%s' % (prof, agg)] = verdict(row, agg, prof)
            row['POLICY_INTERPRETATION_PENDING_%s' % prof] = row['policy_%s_FULL' % prof][:3] != row['policy_%s_G4' % prof][:3]
        for lab in ('native', 'C1', 'nativeC1'):
            v = [row.get('D_vs_%s_%s' % (lab, s), np.nan) for s in SEGS]
            row['FULL_vs_%s' % lab], row['G4_vs_%s' % lab] = ST.full_g4(v, ns)
        rows.append(row)
    P = pd.DataFrame(rows).merge(X[['desc_id', 'exposure_type']], on='desc_id', how='left')
    P['economic_effect'] = P.FULL
    P['mechanism_status'] = '未分离（见 E6k_REPORT_mechanisms）'
    P['evidence_exposure'] = P.exposure_type
    P['deployment_authorized'] = False
    newop = ~P.family.isin(['NATIVE', 'PARENT'])                         # 新算子（台账上全部 = first_evaluation）；plan §9 / §10.6
    P['replacement_preference_status'] = np.where(newop, 'NOT_AUTHORIZED', '')
    P['policy_provisional'] = True
    P['first_look_label'] = np.where(newop, K.LABEL_FIRST_LOOK, '')
    for dl in (0.10,):
        P['edge_c_margin'] = P[['D_%s' % s for s in SEGS]].min(axis=1) + dl
        P['edge_f_margin'] = P[['D_imp_%s' % s for s in SEGS]].min(axis=1) + dl
    P['edge_positive_margin_FULL'] = P.FULL - 0.10
    P['edge_years_margin'] = P.years_pos - 12
    os.makedirs(K.P('results', 'full'), exist_ok=True)
    p1 = K.P('results', 'full', 'policy_E6k.csv')
    K.atomic_write_csv(p1, P)
    # ---- 三句加法（原生对象，α .25 × H5，逐形态 × profile × 聚合）
    add = []
    nat = P[(P.op == 'NATIVE') & (P.alpha == 0.25) & (P.H == 5) & P.meas.isin(['S', 'M', 'Q', 'C1', 'SM'])].set_index(['mother', 'meas'])
    for form in sorted(set(nat.index.get_level_values(0))):
        m = nat.loc[form]
        for prof in PROFILES:
            for agg in ('FULL', 'G4'):
                col = 'policy_%s_%s' % (prof, agg)
                elig = [a for a in ('C1', 'M', 'S', 'Q') if a in m.index and m.loc[a, col] == '通过']
                chosen, why = None, ''
                if 'C1' in elig:
                    chosen, why = 'C1', 'C1 合格 → 默认简单 C1'
                    beat = []
                    for arm in ('M', 'S', 'Q'):
                        if arm in elig:
                            dseg = np.array([m.loc[arm, 'D_%s' % s] - m.loc['C1', 'D_%s' % s] for s in SEGS], float)
                            nseg = np.array([m.loc[arm, 'n_%s' % s] for s in SEGS], float)
                            full, g4 = ST.full_g4(dseg, nseg)
                            md = full if agg == 'FULL' else g4
                            if int((dseg >= 0.05).sum()) >= 3 and md >= 0.05:
                                beat.append((md, arm))
                    if beat:
                        md, arm = sorted(beat, key=lambda x: (-x[0], ('M', 'S', 'Q').index(x[1])))[0]
                        chosen, why = arm, '%s − C1：≥ 3/4 段 ≥ +.05，合并配对差 %.3f ≥ +.05' % (arm, md)
                elif elig:
                    best = sorted(elig, key=lambda a: (-m.loc[a, agg], ('C1', 'M', 'S', 'Q').index(a)))[0]
                    chosen, why = best, 'C1 不合格；取最佳合格单臂'
                if 'SM' in m.index and m.loc['SM', col] == '通过':
                    best = sorted(elig, key=lambda a: (-m.loc[a, agg], ('C1', 'M', 'S', 'Q').index(a)))[0] if elig else None
                    if best is None:
                        chosen, why = 'SM', '无合格单臂；SM 自身满足六条与正向门槛'
                    else:
                        dseg = np.array([m.loc['SM', 'D_%s' % s] - m.loc[best, 'D_%s' % s] for s in SEGS], float)
                        nseg = np.array([m.loc['SM', 'n_%s' % s] for s in SEGS], float)
                        full, g4 = ST.full_g4(dseg, nseg)
                        md = full if agg == 'FULL' else g4
                        if md >= 0.10:
                            chosen, why = 'SM', 'SM − %s 合并配对差 %.3f ≥ +.10' % (best, md)
                add.append(dict(form=form, profile=prof, aggregation=agg, eligible='|'.join(elig), chosen=chosen or '无', why=why))
    p2 = K.P('results', 'full', 'policy_additions_E6k.csv')
    K.atomic_write_csv(p2, pd.DataFrame(add))
    K.write_receipt('policy_E6k', [p1, p2], 'SUCCEEDED', n_objects=len(P))
    print('政策：%d 对象；三句加法 %d 行' % (len(P), len(add)), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
