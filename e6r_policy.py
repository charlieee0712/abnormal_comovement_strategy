# -*- coding: utf-8 -*-
"""E6r 政策（附录 B.13 / B.14；plan §13.2；brief §0.1 #6 / #7）：每个执行对象 × {E6R_POLICY_ESTIMAND（主）, E6Q_ORIGINAL_AUDIT（审计）} = 700 行；
profile = POLICY_E6Q_A1_CANONICAL（阈值不改）：c1 四段 D ≥ −.10；c2 正年 ≥ 12 / 17（2026 部分年计入）；c3 FULL D 与 FULL D_sc 同号；
c4 两后段 real − 主随机均值 ≥ 2 MCSE（主映射 = policy_primary 引用；审计 = AMOUNT_MATCH_V2；只 FEASIBLE）；c5 四段 1 亿 κ .5 δ .5 成本后 D ≥ −.10
（副读 .5 / 5 亿两列；kappa_consistent = 1 亿 FULL κ .5 与 κ 1 同号，只作列）；c6 = A1 冻结声明（主：estimand ≠ PARENT；审计：trigger ≠ NONE）；
port3t = 四段 |PORT3_T| 最大 ≤ 3；positive = FULL D ≥ .10。verdict：任一 false → 不通过；无 false 有 NA → 不可判（必有 undecidable_reason）；全 true → 通过。
参照（statistics/policy_mapping_E6r.csv，A1 冻结）：主 = ENTRY_OVERLAY → 同退出 FLAT、EXIT_RULE → 无退出父、PARENT → 空（全字段 NA）；审计 = 无退出父（trigger = NONE → 空）。
research_status 沿 E6q CANONICAL（未覆盖 = 非 COMPUTED / 纯父 / 机制从未动作）。数值一律从 account_summary / yearly / randoms / cost_curve 表的印出值重算（与 D 脚本同源）。
用法：python3 e6r_policy.py [--root <输出根>]（与 e6r_stats.py 同根）"""
import os
import json
import argparse

import numpy as np
import pandas as pd

import e6r_core as O

SEG4 = list(O.SEGS)
POST2 = ['2019-2023', '2024-2026']
FIELDS = ('c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'port3t', 'positive')
MAPPINGS = ('E6R_POLICY_ESTIMAND', 'E6Q_ORIGINAL_AUDIT')
UNDEC_ORDER = ('SOURCE_BINDING_PENDING', 'MAPPING_UNRESOLVED', 'RANDOM_NOT_COVERED', 'CONTROL_NOT_COMPARABLE', 'PARTIAL_YEAR_ONLY', 'KAPPA_SIGN_DEPENDENT',
               'MC_LIMIT', 'NOT_CANDIDATE_ELIGIBLE')
PROFILE = 'POLICY_E6Q_A1_CANONICAL'
PCOLS = ['exec_id', 'scenario', 'profile_name', 'mapping', 'policy_estimand', 'reference_exec_id', 'c4_ref_id', 'c4_mechanism', 'candidate_eligible', 'A_main_cny',
         'reconciliation_status', 'c1_segment_tolerance_ok', 'c2_year_positive_share', 'c2_ok', 'c3_full_sc_same_sign', 'c4_random_post_ok', 'c5_impact_ok',
         'c5_A_used_cny', 'c5_sub_5e7_ok', 'c5_sub_5e8_ok', 'kappa_consistent', 'c6_declared_ok', 'positive_ok', 'port3t_dev_pp', 'port3t_ok', 'verdict',
         'research_status', 'known_failure', 'undecidable_reason', 'status']
SPEC = dict(c1=('四段 D（net − 映射参照 net）', '≥ −0.10 每段', 'QRY-POL-C1'), c2=('17 个观察年（2026 部分年）的 D', '正年 ≥ 12', 'QRY-POL-C2'),
            c3=('FULL D 与 FULL 同资本 D_sc', '同号', 'QRY-POL-C3'), c4=('两后段 real − 映射主随机均值', '≥ 2·MCSE（两段都）', 'QRY-POL-C4'),
            c5=('四段 D（curve；1 亿 κ .5 δ .5，固定路径）', '≥ −0.10 每段', 'QRY-POL-C5'), c6=('A1 冻结声明（registry + policy_mapping）', '在映射域内且已声明', 'QRY-POL-C6'),
            port3t=('四段 PORT3_T（clean 市值分位资本加权均值差 × 100）', '|·| ≤ 3 每段', 'QRY-POL-P3'), positive=('FULL D', '≥ +0.10', 'QRY-POL-POS'))


def rd(root, rel):
    p = os.path.join(root, rel)
    if not os.path.exists(p) and os.path.exists(p + '.gz'):
        p = p + '.gz'
    return pd.read_csv(p, dtype=str, keep_default_na=False)


def f(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if np.isfinite(v) else None


def tri(v):
    return 'NA' if v is None else ('true' if v else 'false')


def policy_verdict(vals):
    if any(v is False for v in vals.values()):
        return '不通过'
    if any(v is None for v in vals.values()):
        return '不可判'
    return '通过'


def research_status(full_d, g4_d, seg_d, computed=True):
    if not computed or full_d is None:
        return '未覆盖'
    if full_d <= 0 and g4_d <= 0:
        return '方向不支持'
    if full_d >= 0.10 and g4_d > 0:
        return '有改善点估'
    if full_d > 0 and (g4_d <= 0 or sum(1 for d in seg_d if d < 0) >= 2):
        return '结构依赖'
    return '证据有限'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    root = O.P(*a.root.split('/')) if a.root else O.work()
    R = O.read_csv(O.P('registration', 'registry_E6r.csv'))
    PM = O.read_csv(O.P('statistics', 'policy_mapping_E6r.csv')).set_index('exec_id')
    fz = json.load(open(O.P('registration', 'freeze_E6r.json'), encoding='utf-8'))
    recon = fz['reconciliation_status']
    AS = rd(root, 'statistics/account_summary_E6r.csv')
    Y = rd(root, 'statistics/yearly_E6r.csv')
    CC = rd(root, 'statistics/cost_curve_E6r.csv')
    rp = os.path.join(root, 'statistics', 'randoms_E6r.csv')
    RD = rd(root, 'statistics/randoms_E6r.csv') if os.path.exists(rp) else pd.DataFrame(columns=['ref_id', 'segment', 'status', 'real_D_ann_pp', 'rand_mean_D_ann_pp', 'mcse',
                                                                                             'control_comparability', 'rank_real'])
    sm = {(r.exec_id, r.segment): r for r in AS.itertuples(index=False)}
    yv = {e: g for e, g in Y.groupby('exec_id')}
    rnd = {(r.ref_id, r.segment): r for r in RD.itertuples(index=False)}
    cc = {}
    for r in CC.itertuples(index=False):
        if r.comparator_kind in ('POLICY_REFERENCE', 'NOEXIT_SAME_OVERLAY') and f(r.exponent) == 0.5:
            cc[(r.exec_id, r.comparator_kind, r.comparator_exec_id, int(float(r.A_cny)), f(r.kappa), r.segment)] = f(r.net_after_impact_diff_ann_pp)

    def net(e, s):
        r = sm.get((e, s))
        return f(r.net_ann_pp) if (r is not None and r.status == 'COMPUTED') else None
    prow, frow, p9rows = [], [], []
    for r in R.itertuples(index=False):
        e = r.exec_id
        pm = PM.loc[e]
        for m in MAPPINGS:
            if m == 'E6R_POLICY_ESTIMAND':
                ref, c4id, c4m, est = pm.reference_exec_id, pm.c4_ref_id, pm.c4_mechanism, pm.policy_estimand
                dcol, sccol, devcol, ckind = 'D_policy_ann_pp', 'D_sc_policy_ann_pp', 'port3t_dev_pp', 'POLICY_REFERENCE'
                c6 = True if est != 'PARENT_NO_MECHANISM' else None
            else:
                ref, c4id = pm.audit_reference_exec_id, pm.audit_c4_ref_id
                c4m = 'AMOUNT_MATCH_V2' if c4id else ''
                est = 'EXIT_RULE' if r.trigger != 'NONE' else 'PARENT_NO_MECHANISM'
                dcol, sccol, devcol, ckind = 'D_noexit_ann_pp', 'D_sc_noexit_ann_pp', 'port3t_dev_noexit_pp', 'NOEXIT_SAME_OVERLAY'
                c6 = True if r.trigger != 'NONE' else None
            ff = {k: None for k in FIELDS}
            why = {}
            share = ''
            dev = np.nan
            rs = '未覆盖'
            k5 = k1 = None
            c5c = {5e7: None, 1e8: None, 5e8: None}
            if not ref:
                for k in FIELDS:
                    why[k] = 'MAPPING_UNRESOLVED'
            else:
                ds = [net(e, q) - net(ref, q) if (net(e, q) is not None and net(ref, q) is not None) else None for q in SEG4]
                full = net(e, 'FULL') - net(ref, 'FULL') if (net(e, 'FULL') is not None and net(ref, 'FULL') is not None) else None
                if all(d is not None for d in ds):
                    ff['c1'] = all(d >= -0.10 for d in ds)
                if full is not None:
                    ff['positive'] = full >= 0.10
                yy = yv.get(e)
                ys = [f(x) for x in (yy[dcol] if yy is not None else [])]
                ys = [x for x in ys if x is not None]
                if len(ys) == 17:
                    npos = sum(1 for x in ys if x > 0)
                    ff['c2'] = npos >= 12
                    share = npos / 17.0
                else:
                    why['c2'] = 'PARTIAL_YEAR_ONLY'
                fr = sm.get((e, 'FULL'))
                dsc = f(getattr(fr, sccol)) if fr is not None else None
                if full is not None and dsc is not None:
                    ff['c3'] = bool(np.sign(full) == np.sign(dsc))
                if c4id:
                    rs4 = [rnd.get((c4id, q)) for q in POST2]
                    if all(x is not None and x.status in ('COMPUTED', 'MC_LIMIT') for x in rs4) and all(f(x.mcse) is not None for x in rs4):
                        ff['c4'] = all(f(x.real_D_ann_pp) - f(x.rand_mean_D_ann_pp) >= 2.0 * f(x.mcse) for x in rs4)
                    else:
                        fx = rnd.get((c4id, 'FULL'))
                        why['c4'] = 'CONTROL_NOT_COMPARABLE' if (fx is not None and fx.status in ('CONTROL_NOT_COMPARABLE', 'STRUCTURAL_DEGENERATE')) else \
                            ('MC_LIMIT' if (fx is not None and fx.status == 'MC_LIMIT') else 'RANDOM_NOT_COVERED')
                else:
                    why['c4'] = 'RANDOM_NOT_COVERED'
                if recon == 'RECONCILED':
                    for A_ in c5c:
                        v = [cc.get((e, ckind, ref, int(A_), 0.5, q)) for q in SEG4]
                        c5c[A_] = all(x >= -0.10 for x in v) if all(x is not None for x in v) else None
                    ff['c5'] = c5c[1e8]
                    k5, k1 = cc.get((e, ckind, ref, 100000000, 0.5, 'FULL')), cc.get((e, ckind, ref, 100000000, 1.0, 'FULL'))
                else:
                    why['c5'] = 'SOURCE_BINDING_PENDING'
                ff['c6'] = c6
                dv = [f(getattr(sm[(e, q)], devcol)) if (e, q) in sm else None for q in SEG4]
                if all(x is not None for x in dv):
                    dev = float(max(abs(x) for x in dv))
                    ff['port3t'] = dev <= 3.0
                if all(d is not None for d in ds) and full is not None:
                    g4 = float(np.median(ds))
                    acted = not ((est == 'ENTRY_OVERLAY' and int(float(fr.n_cohorts_overlay_active or 0)) == 0) or
                                 (est == 'EXIT_RULE' and int(float(fr.n_exit_intents or 0)) == 0))
                    rs = research_status(full, g4, ds, acted and est != 'PARENT_NO_MECHANISM')
                for k in FIELDS:
                    if ff[k] is None and k not in why:
                        why[k] = 'MAPPING_UNRESOLVED'
            verdict = policy_verdict(ff)
            reasons = [why[k] for k in FIELDS if ff[k] is None]
            und = next((x for x in UNDEC_ORDER if x in reasons), 'MAPPING_UNRESOLVED') if verdict == '不可判' else ''
            kc = (bool(np.sign(k5) == np.sign(k1)) if (k5 is not None and k1 is not None) else None)
            prow.append(dict(exec_id=e, scenario=r.scenario, profile_name=PROFILE, mapping=m, policy_estimand=est, reference_exec_id=ref, c4_ref_id=c4id,
                             c4_mechanism=c4m, candidate_eligible=pm.candidate_eligible, A_main_cny=100000000, reconciliation_status=recon,
                             c1_segment_tolerance_ok=tri(ff['c1']), c2_year_positive_share=share, c2_ok=tri(ff['c2']), c3_full_sc_same_sign=tri(ff['c3']),
                             c4_random_post_ok=tri(ff['c4']), c5_impact_ok=tri(ff['c5']), c5_A_used_cny=100000000, c5_sub_5e7_ok=tri(c5c[5e7]),
                             c5_sub_5e8_ok=tri(c5c[5e8]), kappa_consistent=tri(kc), c6_declared_ok=tri(ff['c6']), positive_ok=tri(ff['positive']),
                             port3t_dev_pp=dev if np.isfinite(dev) else '', port3t_ok=tri(ff['port3t']), verdict=verdict, research_status=rs,
                             known_failure=';'.join(k for k in FIELDS if ff[k] is False), undecidable_reason=und, status='COMPUTED'))
            for k in FIELDS:
                frow.append(dict(exec_id=e, mapping=m, field=k, value=tri(ff[k]), reason=why.get(k, '') if ff[k] is None else '', denominator=SPEC[k][0],
                                 threshold=SPEC[k][1], query_id=SPEC[k][2], source='registration/policy_profile_E6q.json + statistics/policy_mapping_E6r.csv（A1 冻结）',
                                 approval_status='A1_FROZEN'))
    PO = pd.DataFrame(prow, columns=PCOLS)
    PF = pd.DataFrame(frow, columns=['exec_id', 'mapping', 'field', 'value', 'reason', 'denominator', 'threshold', 'query_id', 'source', 'approval_status'])
    os.makedirs(os.path.join(root, 'statistics'), exist_ok=True)
    O.atomic_write_csv(os.path.join(root, 'statistics', 'policy_E6r.csv'), PO)
    O.atomic_write_csv(os.path.join(root, 'statistics', 'policy_fields_E6r.csv'), PF)
    # primary9（primary.json 顺序）
    prim = json.load(open(O.P('registration', 'spec', 'primary.json'), encoding='utf-8'))
    lid2e = dict(zip(R.logical_id, R.exec_id))
    pol = PO.set_index(['exec_id', 'mapping'])
    reg = R.set_index('exec_id')
    for lid in prim['primary9']:
        e = lid2e[lid]
        rr = reg.loc[e]
        fr = sm[(e, 'FULL')]
        g4 = sm.get((e, 'G4'))
        ref = PM.loc[e].reference_exec_id
        c4id = PM.loc[e].c4_ref_id
        rk = rnd.get((c4id, 'FULL')) if c4id else None
        row = {'exec_id': e, 'logical_id': lid, 'trigger': rr.trigger, 'weight_scheme': rr.weight_scheme, 'FULL_net_ann_pp': fr.net_ann_pp,
               'FULL_gross_ann_pp': fr.gross_ann_pp, 'FULL_D_policy_ann_pp': fr.D_policy_ann_pp, 'FULL_gross_D_policy_ann_pp': fr.gross_D_policy_ann_pp,
               'G4_D_policy_ann_pp': g4.D_policy_ann_pp if g4 is not None else ''}
        for q in SEG4:
            row['D_%s' % q] = sm[(e, q)].D_policy_ann_pp
        row.update({'FULL_D_native_same_trigger_flat_ann_pp': fr.D_native_same_trigger_flat_ann_pp, 'FULL_D_frontier_ann_pp': fr.D_frontier_ann_pp,
                    'FULL_D_scale_gate_ann_pp': fr.D_scale_gate_ann_pp, 'FULL_D_scale_rearm_ann_pp': fr.D_scale_rearm_ann_pp,
                    'cost_1e8_D_policy_ann_pp': fnum(cc.get((e, 'POLICY_REFERENCE', ref, 100000000, 0.5, 'FULL'))),
                    'cost_5e8_D_policy_ann_pp': fnum(cc.get((e, 'POLICY_REFERENCE', ref, 500000000, 0.5, 'FULL'))), 'abs_net_ann_pp': fr.abs_net_ann_pp,
                    'max_drawdown_total': fr.max_drawdown_total, 'rank_vs_c4': rk.rank_real if rk is not None else '',
                    'verdict': pol.loc[(e, 'E6R_POLICY_ESTIMAND'), 'verdict'], 'research_status': pol.loc[(e, 'E6R_POLICY_ESTIMAND'), 'research_status']})
        p9rows.append(row)
    cols = ['exec_id', 'logical_id', 'trigger', 'weight_scheme', 'FULL_net_ann_pp', 'FULL_gross_ann_pp', 'FULL_D_policy_ann_pp', 'FULL_gross_D_policy_ann_pp',
            'G4_D_policy_ann_pp', 'D_2010-2014', 'D_2015-2018', 'D_2019-2023', 'D_2024-2026', 'FULL_D_native_same_trigger_flat_ann_pp', 'FULL_D_frontier_ann_pp',
            'FULL_D_scale_gate_ann_pp', 'FULL_D_scale_rearm_ann_pp', 'cost_1e8_D_policy_ann_pp', 'cost_5e8_D_policy_ann_pp', 'abs_net_ann_pp', 'max_drawdown_total',
            'rank_vs_c4', 'verdict', 'research_status']
    P9 = pd.DataFrame(p9rows, columns=cols)
    O.atomic_write_csv(os.path.join(root, 'statistics', 'primary9_E6r.csv'), P9)
    vc = {'|'.join(k): int(v) for k, v in PO.groupby(['mapping', 'scenario', 'verdict']).size().items()}
    facts = dict(policy_rows=len(PO), fields=len(PF), primary9=len(P9), verdicts=vc, reconciliation=recon)
    O.atomic_write_json(os.path.join(root, 'statistics', 'policy_facts_E6r.json'), facts)
    O.write_receipt('E6r_policy', [os.path.join(root, 'statistics', x) for x in ('policy_E6r.csv', 'policy_fields_E6r.csv', 'primary9_E6r.csv')],
                    code=[__file__, O.__file__], **{k: v for k, v in facts.items() if k != 'verdicts'})
    print(json.dumps(facts, ensure_ascii=False), flush=True)


def fnum(x):
    return '' if x is None else x


if __name__ == '__main__':
    main()
