# -*- coding: utf-8 -*-
"""E6l 政策评分（brief §6 / W12；plan §10；registration/policy_profiles_E6l.json；E6k e6k_policy / e6j_policy_p.verdict 同式）。
四段统计齐（results/full/descriptor_stats_<段>.csv、random_refs_<段>.csv）且 seal_deriv / seal_post 核对通过后运行。
逐描述符 × 四个 verdict profile（PROPOSED_PORT3_T 正式 / LEGACY_EDIT5 / PROPOSED_PORT3_LAG1 / EXEC_DISCLOSE_ONLY）× {FULL, G4}；
EXEC_LEADER_VS_PARENT 只披露（状态列，无 verdict）。判定串顺序 c、d、f、正向门槛、e资本、e随机、size(profile)；
c（四段 D ≥ −δ，δ .05 / .10 / .15；缺失不自动满足）/ d（正年 ≥ 12 / 17；16 年与 10 / 17 敏感列）/ e 资本（sign(FULL) = sign(FULL_sc)，1e−9）/
e 随机（LEGACY 两后段 rmr 与 2·MCSE 三态；未排 → RANDOM_NOT_SCHEDULED；K0 规则 → NO_NEW_CONTENT_TO_PERMUTE）/ f（A 5 亿 κ .5 四段 D_imp ≥ −δ）/
正向（≥ +.10）→ 通过 / 不通过（列已定失败项）/ 不可判（列未定项）。三句加法 PX1 只对原生 NATIVE 的 S / M / Q0 / C1（α .25 × H5）。
每对象七列证据状态；SECOND_EVALUATION 对象不进"本轮新证据"栏；边缘清单列全部条件距离。policy_provisional = false。"""
import e6l_boot  # noqa: F401
import os
import sys
import json

import numpy as np
import pandas as pd

import e6l_core as L
import e6j_stats as ST

SEGS = L.SEGMENTS
POST = L.POST_SEGS
DELTAS = (0.05, 0.10, 0.15)
MC_Z, SIGN_TOL = 2.0, 1e-9
VERDICT_PROFILES = ('PROPOSED_PORT3_T', 'LEGACY_EDIT5', 'PROPOSED_PORT3_LAG1', 'EXEC_DISCLOSE_ONLY')


def tri_sign(x):
    return np.nan if not np.isfinite(x) else (0.0 if abs(x) <= SIGN_TOL else float(np.sign(x)))


def e_rand(row):
    if row['random_content'] == 'NO_NEW_CONTENT_TO_PERMUTE':
        return 'NO_NEW_CONTENT_TO_PERMUTE'
    if row['random_content'] == 'RANDOM_NOT_SCHEDULED':
        return 'RANDOM_NOT_SCHEDULED'
    st = []
    for s in POST:
        d, se = row.get('rmr_%s' % s, np.nan), row.get('mcse_%s' % s, np.nan)
        if not (np.isfinite(d) and np.isfinite(se)):
            st.append('MISSING')
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
    if 'MISSING' in st:
        return 'RANDOM_NOT_SCHEDULED'
    return 'MC_UNRESOLVED'


def size_status(row, prof):
    if prof == 'EXEC_DISCLOSE_ONLY':
        return 'PASS'
    if prof == 'LEGACY_EDIT5':
        g = np.array([row.get('edit_gap_absmean_T_%s' % s, np.nan) for s in SEGS], float)
        if np.all(np.isnan(g)):
            return 'UNDEFINED'
        return 'FAIL' if np.nanmax(g) > 5.0 else 'PASS'
    if prof in ('PROPOSED_PORT3_T', 'PROPOSED_PORT3_LAG1'):
        z = 'T' if prof.endswith('_T') else 'L'
        st = []
        for s in SEGS:
            lo, hi = row.get('port_size_lo_%s_%s' % (z, s), np.nan), row.get('port_size_hi_%s_%s' % (z, s), np.nan)
            if not (np.isfinite(lo) and np.isfinite(hi)):
                st.append('UNDEFINED')
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
        return 'SIZE_PARTIALLY_IDENTIFIED' if 'SIZE_PARTIALLY_IDENTIFIED' in st else 'UNDEFINED'
    if prof == 'EXEC_LEADER_VS_PARENT':
        st = []
        for s in SEGS:
            c, p = row.get('lv5_mean_%s' % s, np.nan), row.get('parent_lv5_mean_%s' % s, np.nan)
            if not np.isfinite(c):
                st.append('UNDEFINED')
            else:
                st.append('PASS' if c <= max(0.03, p if np.isfinite(p) else 0.03) + 1e-12 else 'FAIL')
        return 'FAIL' if 'FAIL' in st else ('PASS' if all(x == 'PASS' for x in st) else 'UNDEFINED')
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
    elif ss not in ('PASS',):
        pend.append('size:%s' % ss)
    if fails:
        return '不通过（%s）' % '、'.join(fails)
    if pend:
        return '不可判（%s）' % '、'.join(pend)
    return '通过'


def main():
    import e6l_seal as SEAL
    for pkg in ('deriv', 'post'):
        ok, bad = SEAL.verify(pkg)
        if not ok:
            raise RuntimeError('seal_%s 核对失败：%s' % (pkg, bad[:5]))
    for s in POST:
        L.post_gate(s, 'policy')
    D = L.read_csv_keep(L.P('registry', 'descriptors_E6l.csv'))
    pp = json.load(open(L.P('registration', 'policy_profiles_E6l.json'), encoding='utf-8'))
    S = {s: pd.read_csv(L.P('results', 'full', 'descriptor_stats_%s.csv' % s), keep_default_na=False, na_values=['']).set_index('desc_id') for s in SEGS}
    R = pd.concat([pd.read_csv(L.P('results', 'full', 'random_refs_%s.csv' % s), keep_default_na=False, na_values=['']).assign(segment=s) for s in SEGS],
                  ignore_index=True)
    leg = R[R.mechanism == 'LEGACY_POLICY_RANDOM'].set_index(['desc_id', 'segment'])
    rows = []
    keys = ('D', 'n', 'D_sc', 'D_imp', 'D_str', 'D_6bp', 'D_12bp', 'D_gross', 'D_vs_native', 'D_vs_C1', 'D_vs_Q0', 'D_vs_QHG10', 'D_vs_rule_only',
            'edit_gap_absmean_T', 'edit_gap_mean_T', 'port_size_lo_T', 'port_size_hi_T', 'port_size_lo_L', 'port_size_hi_L', 'lv5_mean', 'parent_lv5_mean',
            'small30_delta', 'unkT_mean', 'turn_rel', 'se_H', 'se_2H', 'net8_ann', 'parent_net8_ann')
    for r in D[D.family != 'PARENT'].itertuples():
        row = dict(desc_id=r.desc_id, meas=r.meas, mother=r.mother, alpha=r.alpha, H=r.H, op=r.op, family=r.family, recipe=r.recipe,
                   primary72=r.primary72, dose72=r.dose72, nbhd72=r.nbhd72, random_content=r.random_content, evidence_exposure=r.evidence_exposure,
                   e6k_equiv=r.e6k_equiv)
        Ds, ns, Dsc, Dimp = [], [], [], []
        for s in SEGS:
            x = S[s].loc[r.desc_id] if r.desc_id in S[s].index else None
            for k in keys:
                row['%s_%s' % (k, s)] = float(x[k]) if (x is not None and k in x.index and pd.notna(x[k])) else np.nan
            Ds.append(row['D_%s' % s])
            ns.append(row['n_%s' % s])
            Dsc.append(row['D_sc_%s' % s])
            Dimp.append(row['D_imp_%s' % s])
            if x is not None:
                for k in x.index:
                    if k.startswith('Y') and k[1:].isdigit():
                        row[k] = row.get(k, np.nan) if np.isfinite(row.get(k, np.nan)) else (float(x[k]) if pd.notna(x[k]) else np.nan)
            if (r.desc_id, s) in leg.index:
                lr = leg.loc[(r.desc_id, s)]
                lr = lr.iloc[0] if isinstance(lr, pd.DataFrame) else lr
                row['rmr_%s' % s] = float(lr.real_minus_rand)
                row['mcse_%s' % s] = float(lr.mcse)
                row['npaths_%s' % s] = int(lr.n)
            else:
                row['rmr_%s' % s] = np.nan
                row['mcse_%s' % s] = np.nan
                row['npaths_%s' % s] = 0
        row['FULL'], row['G4'] = ST.full_g4(Ds, ns)
        row['FULL_sc'], row['G4_sc'] = ST.full_g4(Dsc, ns)
        row['FULL_imp'], row['G4_imp'] = ST.full_g4(Dimp, ns)
        for dl in DELTAS:
            tag = 'd%02d' % int(round(dl * 100))
            row['c_%s' % tag] = bool(np.all([np.isfinite(v) and v >= -dl for v in Ds]))
            row['f_%s' % tag] = bool(np.all([np.isfinite(v) and v >= -dl for v in Dimp]))
        for agg in ('FULL', 'G4'):
            sn, sc = tri_sign(row[agg]), tri_sign(row['%s_sc' % agg])
            row['e_cap_%s' % agg] = 'UNDEFINED' if (np.isnan(sn) or np.isnan(sc)) else ('PASS' if sn == sc else 'FAIL')
            row['positive_%s' % agg] = bool(np.isfinite(row[agg]) and row[agg] >= 0.10)
        ys = {int(k[1:]): v for k, v in row.items() if k.startswith('Y') and k[1:].isdigit()}
        vals = [v for v in ys.values() if np.isfinite(v)]
        row['years_pos'] = int(sum(v > 0 for v in vals))
        row['years_n'] = len(vals)
        row['years_pos_2010_2025'] = int(sum(ys[y] > 0 for y in range(2010, 2026) if y in ys and np.isfinite(ys[y])))
        row['d_ok'] = row['years_pos'] >= 12
        row['d_ok_10of17'] = row['years_pos'] >= 10
        row['e_rand'] = e_rand(row)
        for prof in VERDICT_PROFILES + ('EXEC_LEADER_VS_PARENT',):
            row['size_%s' % prof] = size_status(row, prof)
        for prof in VERDICT_PROFILES:
            for agg in ('FULL', 'G4'):
                row['policy_%s_%s' % (prof, agg)] = verdict(row, agg, prof)
            row['POLICY_INTERPRETATION_PENDING_%s' % prof] = row['policy_%s_FULL' % prof][:3] != row['policy_%s_G4' % prof][:3]
        rows.append(row)
    P = pd.DataFrame(rows)
    newop = P.evidence_exposure == L.LABEL_FIRST_LOOK
    P['economic_effect_FULL_ann_pp'] = P.FULL
    P['policy_profile'] = 'PROPOSED_PORT3_T'
    P['policy_result'] = P['policy_PROPOSED_PORT3_T_FULL']
    P['mechanism_status'] = '未分离（见 E6l_REPORT_mechanisms）'
    P['historical_exposure'] = P.evidence_exposure
    P['replacement_status'] = np.where(newop, 'NOT_AUTHORIZED', 'NOT_APPLICABLE')
    P['deployment_authorized'] = False
    P['policy_provisional'] = False
    P['evidence_column'] = np.where(P.evidence_exposure == L.LABEL_SECOND, '上一轮（同构再评，只作锚）', '本轮新证据（首评，重复使用的历史）')
    P['edge_c_margin_ann_pp'] = P[['D_%s' % s for s in SEGS]].min(axis=1) + 0.10
    P['edge_f_margin_ann_pp'] = P[['D_imp_%s' % s for s in SEGS]].min(axis=1) + 0.10
    P['edge_positive_margin_FULL_ann_pp'] = P.FULL - 0.10
    P['edge_years_margin'] = P.years_pos - 12
    P['edge_erand_margin_ann_pp'] = pd.concat([P['rmr_%s' % s] - MC_Z * P['mcse_%s' % s] for s in POST], axis=1).min(axis=1)
    P['edge_port3_margin_pct_pt'] = pd.concat([3.0 - P['port_size_hi_T_%s' % s] for s in SEGS] + [P['port_size_lo_T_%s' % s] + 3.0 for s in SEGS], axis=1).min(axis=1)
    os.makedirs(L.P('results', 'full'), exist_ok=True)
    p1 = L.P('results', 'full', 'policy_E6l.csv')
    L.atomic_write_csv(p1, P)
    # 三句加法（PX1：原生 NATIVE 的 S / M / Q0 / C1，α .25 × H5）
    add = []
    nat = P[(P.op == 'NATIVE') & (P.alpha.astype(float) == 0.25) & (P.H.astype(int) == 5) & P.meas.isin(['S', 'M', 'Q0', 'C1'])].set_index(['mother', 'meas'])
    for form in sorted(set(nat.index.get_level_values(0))):
        m = nat.loc[form]
        for prof in VERDICT_PROFILES:
            for agg in ('FULL', 'G4'):
                col = 'policy_%s_%s' % (prof, agg)
                elig = [x for x in ('C1', 'M', 'S', 'Q0') if x in m.index and m.loc[x, col] == '通过']
                chosen, why = None, ''
                if 'C1' in elig:
                    chosen, why = 'C1', 'C1 合格 → 默认简单 C1'
                    beat = []
                    for arm in ('M', 'S', 'Q0'):
                        if arm in elig:
                            dseg = np.array([m.loc[arm, 'D_%s' % s] - m.loc['C1', 'D_%s' % s] for s in SEGS], float)
                            nseg = np.array([m.loc[arm, 'n_%s' % s] for s in SEGS], float)
                            full, g4 = ST.full_g4(dseg, nseg)
                            md = full if agg == 'FULL' else g4
                            if int((dseg >= 0.05).sum()) >= 3 and md >= 0.05:
                                beat.append((md, arm))
                    if beat:
                        md, arm = sorted(beat, key=lambda x: (-x[0], ('M', 'S', 'Q0').index(x[1])))[0]
                        chosen, why = arm, '%s − C1：≥ 3/4 段 ≥ +.05，合并配对差 %.3f ≥ +.05' % (arm, md)
                elif elig:
                    best = sorted(elig, key=lambda x: (-m.loc[x, agg], ('C1', 'M', 'S', 'Q0').index(x)))[0]
                    chosen, why = best, 'C1 不合格；取最佳合格单臂'
                add.append(dict(form=form, profile=prof, aggregation=agg, eligible='|'.join(elig) if elig else 'NONE', chosen=chosen or '无', why=why or 'NOT_APPLICABLE',
                                sm_clause='NOT_APPLICABLE（E6l 无 SM 对象）'))
    p2 = L.P('results', 'full', 'policy_additions_E6l.csv')
    L.atomic_write_csv(p2, pd.DataFrame(add))
    L.write_receipt(L.next_rerun('policy_E6l'), [p1, p2], 'SUCCEEDED', n_objects=len(P), profile_contract=pp['record_id'])
    print('政策：%d 对象；三句加法 %d 行；PORT3_T FULL 通过 %d' % (len(P), len(add), int((P.policy_PROPOSED_PORT3_T_FULL == '通过').sum())), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
