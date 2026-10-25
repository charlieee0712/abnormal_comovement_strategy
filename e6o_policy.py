# -*- coding: utf-8 -*-
"""E6o 随机汇总 + 政策 + 主展示（附录 B.7 / B.9 / B.10；plan §8、§11.3；policy_profile_E6o.json 为 A1 冻结的规则）。
  python3 e6o_policy.py --phase B [--dryrun]
randoms_E6o.csv：owner × 机制 × 段：paths / real_D（owner 账户 D）/ rand_mean / rand_sd（ddof 1）/ mcse = sd / √paths / rank_real（随机路径 D < real 的份额）/
  unmatched_share（Σ 未匹配金额 / Σ 目标金额）/ status（COMPUTED；主母体 AMOUNT_MATCH 到 1024 仍 mcse > .01 → MC_LIMIT）；
  其余 IDEALIZED 配置记 NO_RANDOM_BY_SCOPE；无退出的入场暂停账户 AMOUNT_MATCH 记 NOT_APPLICABLE。
policy_E6o.csv：每 C_ACCOUNT × 情景一行 POLICY_E6O_PARENT_Q；分钟触发另加 PARTIAL_HISTORY_RESEARCH_V1 行。
main72_E6o.csv：72 主展示（FEASIBLE）。"""
import os
import sys
import json
import glob
import math
import argparse

import numpy as np
import pandas as pd

import e6o_core as O

SEG4 = list(O.SEGS)
MSEG = ['2013-2014', '2015-2018', '2019-2023', '2024-2026']
PRIMARY = ('T1a', 'T1b', 'T3c15_X', 'T4a')
MINUTE = ('T4a', 'T4b', 'T5')


def load_paths(phase):
    fs = sorted(glob.glob(O.P('randoms', 'random_paths_%s*.csv' % phase)))
    D = pd.concat([pd.read_csv(f, keep_default_na=False, na_values=['']) for f in fs], ignore_index=True)
    if 'status' in D.columns and (D.status == 'FAILED').any():
        raise RuntimeError('随机路径含 FAILED 行')
    k = ['owner_exec_id', 'mechanism', 'path_id']
    if D.duplicated(k).any():
        raise RuntimeError('随机路径键重复 %d' % int(D.duplicated(k).sum()))
    return D


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=['A2', 'B'], required=True)
    ap.add_argument('--dryrun', action='store_true')
    ap.add_argument('--fake_post', action='store_true')
    a = ap.parse_args()
    root = O.P('tmp', 'dryrun') if a.dryrun else O.work()
    R = pd.read_csv(O.P('registration', 'registry_E6o.csv'), keep_default_na=False, na_values=[''])
    reg = R.set_index('exec_id')
    AS = pd.read_csv(os.path.join(root, 'statistics', 'account_summary_E6o.csv'), keep_default_na=False, na_values=[''])
    YR = pd.read_csv(os.path.join(root, 'statistics', 'yearly_D_E6o.csv'), keep_default_na=False, na_values=[''])
    RS = pd.read_csv(O.P('registration', 'random_scope_E6o.csv'), keep_default_na=False)
    PP = json.load(open(O.P('registration', 'policy_profile_E6o.json')))
    PA = load_paths(a.phase)
    if a.fake_post:
        if not (a.dryrun and a.phase == 'A2'):
            raise RuntimeError('--fake_post 只用于 --phase A2 --dryrun')
        for dst, src_ in (('2019-2023', '2010-2014'), ('2024-2026', '2015-2018')):     # 假数据：后段列 ← 推导段列（只为执行全路径）
            PA['D_%s' % dst] = PA['D_%s' % src_]
            PA['n_%s' % dst] = PA['n_%s' % src_]
    asi = AS.set_index(['exec_id', 'segment'])
    rows = []
    main_rows = []
    for (owner, mech), g in PA.groupby(['owner_exec_id', 'mechanism']):
        sup = reg.loc[owner, 'support']
        segs = SEG4 + ['FULL', 'G4'] + (['2013-2014', 'FULL_2013', 'G4_2013'] if sup == 'MINUTE_2013' else [])
        Dseg = {}
        nseg = {}
        for s in SEG4 + ['2013-2014']:
            if 'D_%s' % s in g.columns:
                Dseg[s] = g['D_%s' % s].to_numpy(float)
                nseg[s] = g['n_%s' % s].to_numpy(float)
        for tag, ss in (('', SEG4), ('_2013', MSEG)):
            if all(s in Dseg for s in ss):
                Dm = np.vstack([Dseg[s] for s in ss])
                W = np.vstack([nseg[s] for s in ss])
                with np.errstate(all='ignore'):
                    Dseg['FULL' + tag] = np.nansum(Dm * W, 0) / np.nansum(np.where(np.isfinite(Dm), W, 0), 0)
                    Dseg['G4' + tag] = np.median(Dm, 0) if np.isfinite(Dm).all() else np.full(Dm.shape[1], np.nan)
        topped = int(g.path_id.max()) + 1 if len(g) else 0
        for s in segs:
            v = Dseg.get(s)
            if v is None:
                continue
            ok = np.isfinite(v)
            n = int(ok.sum())
            try:
                real = float(asi.loc[(owner, s), 'D_ann_pp'])
            except KeyError:
                real = np.nan
            if n:
                mu = float(np.mean(v[ok]))
                sd = float(np.std(v[ok], ddof=1)) if n > 1 else 0.0
                mc = sd / math.sqrt(n)
                rk = float(np.mean(v[ok] < real)) if np.isfinite(real) else np.nan
            else:
                mu = sd = mc = rk = np.nan
            tgt = float(g.target_amt.sum())
            um = float(g.unmatched_amt.sum() / tgt) if tgt > 0 else 0.0
            st = 'COMPUTED' if n else 'UNKNOWN'
            rows.append(dict(owner_exec_id=owner, mechanism=mech, segment=s, paths=n, real_D_ann_pp=real, rand_mean_D_ann_pp=mu, rand_sd_D_ann_pp=sd, mcse=mc,
                             rank_real=rk, unmatched_share=um, status=st))
        if mech == 'AMOUNT_MATCH' and reg.loc[owner, 'is_main_object'] == 1:
            for r in g.itertuples():
                main_rows.append(dict(owner_exec_id=owner, mechanism=mech, path_id=int(r.path_id), seed=int(r.seed),
                                      FULL_D_ann_pp=float(Dseg['FULL'][list(g.path_id).index(r.path_id)]) if 'FULL' in Dseg else np.nan,
                                      n_unmatched_days=int(r.n_unmatched_days)))
    RT = pd.DataFrame(rows)
    # 主母体精度：mcse ≤ .01 否则（到 1024）MC_LIMIT；精度集与 e6o_topup.precision_owners 同（random_scope topup_to = 1024 ∪ D 脚本 S11 规则）
    am_ = RS[RS.mechanism == 'AMOUNT_MATCH']
    mains = set(am_[pd.to_numeric(am_.topup_to, errors='coerce').fillna(0) >= 1024].owner_exec_id)
    for e in R[(R.series == 'C_ACCOUNT') & (R.execution_profile == 'FEASIBLE_DAILY')].exec_id:
        q = e.split('|')
        if len(q) == 16 and q[0] == O.MAIN_FORM and q[3] == 'H5' and q[4] in PRIMARY and q[5] == 'ENGINE_NATIVE' and q[8] == 'ALLOW':
            mains.add(e)
    for e in sorted(mains & set(am_.owner_exec_id)):
        m = (RT.owner_exec_id == e) & (RT.mechanism == 'AMOUNT_MATCH') & (RT.segment == 'FULL')
        if m.any():
            r = RT[m].iloc[0]
            if r.mcse > 0.01 and r.paths >= 1024:
                RT.loc[(RT.owner_exec_id == e) & (RT.mechanism == 'AMOUNT_MATCH'), 'status'] = 'MC_LIMIT'
    # 无随机的执行对象登记
    have = set(RT.owner_exec_id)
    extra = []
    for r in R[R.series == 'C_ACCOUNT'].itertuples():
        if r.exec_id in have:
            continue
        st = 'NO_RANDOM_BY_SCOPE' if r.execution_profile != 'FEASIBLE_DAILY' else 'NOT_APPLICABLE'
        extra.append(dict(owner_exec_id=r.exec_id, mechanism='AMOUNT_MATCH', segment='FULL', paths=0, real_D_ann_pp=np.nan, rand_mean_D_ann_pp=np.nan,
                          rand_sd_D_ann_pp=np.nan, mcse=np.nan, rank_real=np.nan, unmatched_share=np.nan, status=st))
    RT = pd.concat([RT, pd.DataFrame(extra)], ignore_index=True)
    od = os.path.join(root, 'statistics')
    O.atomic_write_csv(os.path.join(od, 'randoms_E6o.csv'), RT)
    O.atomic_write_csv(os.path.join(od, 'random_paths_main_E6o.csv'), pd.DataFrame(main_rows))
    # ---------------- 政策
    rti = RT.set_index(['owner_exec_id', 'mechanism', 'segment'])
    prow = []

    def get(e, s, c='D_ann_pp'):
        try:
            v = asi.loc[(e, s), c]
            return float(v) if v != '' else np.nan
        except KeyError:
            return np.nan

    def research_status(e, tag=''):
        st = asi.loc[(e, 'FULL' + tag), 'status'] if (e, 'FULL' + tag) in asi.index else 'UNKNOWN'
        if st != 'COMPUTED':
            return '未覆盖'
        r = reg.loc[e]
        nx = get(e, 'FULL' + tag, 'n_exit_intents')
        if r.exit_enabled == 'ON' and not (nx > 0):
            return '未覆盖'
        D = get(e, 'FULL' + tag)
        G = get(e, 'G4' + tag)
        Ds = get(e, 'FULL' + tag, 'D_source_ann_pp')
        segs = SEG4 if tag == '' else MSEG
        nneg = sum(1 for s in segs if get(e, s) < 0)
        if D <= 0 and G <= 0:
            return '方向不支持'
        if D >= 0.10 and G > 0 and Ds > 0:
            return '有改善点估'
        if D > 0 and (G <= 0 or nneg >= 2 or Ds <= 0):
            return '结构依赖'
        return '证据有限'

    for r in R[R.series == 'C_ACCOUNT'].itertuples():
        e = r.exec_id
        for prof_name, tag, segs in (('POLICY_E6O_PARENT_Q', '', SEG4), ('PARTIAL_HISTORY_RESEARCH_V1', '_2013', MSEG)):
            if prof_name == 'PARTIAL_HISTORY_RESEARCH_V1' and r.trigger not in MINUTE:
                continue
            Dsg = [get(e, s) for s in segs]
            c1 = all(np.isfinite(x) and x >= -0.10 for x in Dsg) if all(np.isfinite(x) for x in Dsg) else None
            y = YR[YR.exec_id == e]
            if tag == '_2013':
                y = y[y.year >= 2013]
            yv = y.D_ann_pp.to_numpy(float)
            Y = int(np.isfinite(yv).sum())
            pos = int((yv[np.isfinite(yv)] > 0).sum())
            share = pos / Y if Y else np.nan
            need = 12 if tag == '' else int(math.ceil(2 * Y / 3.0))
            c2 = (pos >= need) if Y else None
            Df = get(e, 'FULL' + tag)
            Dsc = get(e, 'FULL' + tag, 'D_sc_ann_pp')
            c3 = (np.sign(Df) == np.sign(Dsc)) if (np.isfinite(Df) and np.isfinite(Dsc)) else None
            mech = 'ENTRY_RANDOM' if (r.exit_enabled == 'OFF') else 'AMOUNT_MATCH'
            c4 = None
            ok4 = []
            for s in ('2019-2023', '2024-2026'):
                k = (e, mech, s)
                if k in rti.index:
                    rr = rti.loc[k]
                    if rr.status in ('COMPUTED', 'MC_LIMIT') and np.isfinite(rr.real_D_ann_pp) and np.isfinite(rr.rand_mean_D_ann_pp):
                        ok4.append(rr.real_D_ann_pp - rr.rand_mean_D_ann_pp >= 2.0 * rr.mcse)
            if len(ok4) == 2:
                c4 = all(ok4)
            Dimp = [get(e, s, 'D_imp_ann_pp') for s in segs]
            c5 = all(x >= -0.10 for x in Dimp) if all(np.isfinite(x) for x in Dimp) else None
            szs = [get(e, s, 'size_dev_pp') for s in segs]
            dev = float(np.nanmax(np.abs(szs))) if any(np.isfinite(x) for x in szs) else np.nan
            p3 = (dev <= 3.0) if np.isfinite(dev) else None
            positive = (Df >= 0.10) if np.isfinite(Df) else None
            conds = [c1, c2, c5, positive, c3, c4, p3]
            if any(c is False for c in conds):
                verdict = '不通过'
            elif all(c is True for c in conds):
                verdict = '通过'
            else:
                verdict = '不可判'
            if prof_name == 'POLICY_E6O_PARENT_Q' and r.trigger in MINUTE:
                verdict = '不可判'                                             # 分钟触发：旧 17 年政策照旧不可判（plan §11.3；研究列另给）
            b = lambda c: '' if c is None else (1 if c else 0)
            prow.append(dict(exec_id=e, execution_profile=r.execution_profile, profile_name=prof_name, policy_version='POLICY_E6O_PARENT_Q@A1',
                             c1_segment_tolerance_ok=b(c1), c2_year_positive_share=share, c2_ok=b(c2), c3_full_sc_same_sign=b(c3), c4_random_post_ok=b(c4),
                             c5_impact_ok=b(c5), c6_declared_ok=1, port3t_dev_pp=dev, port3t_ok=b(p3), verdict=verdict, research_status=research_status(e, tag),
                             partial_history_years=(Y if tag == '_2013' else ''), mapping_unresolved_fields='', status='COMPUTED', positive_ok=b(positive),
                             years_positive=pos, years_evaluable=Y, random_mechanism=mech))
    PO = pd.DataFrame(prow)
    O.atomic_write_csv(os.path.join(od, 'policy_E6o.csv'), PO)
    # ---------------- 主展示 72
    m72 = []
    poi = PO[PO.profile_name == 'POLICY_E6O_PARENT_Q'].set_index('exec_id')
    for r in R[(R.series == 'C_ACCOUNT') & (R.is_primary72 == 1)].itertuples():
        e = r.exec_id
        try:
            rk = float(rti.loc[(e, 'AMOUNT_MATCH', 'FULL'), 'rank_real'])
        except KeyError:
            rk = np.nan
        m72.append(dict(exec_id=e, trigger=r.trigger, form=r.form, memory=r.memory, FULL_D_ann_pp=get(e, 'FULL'), G4_D_ann_pp=get(e, 'G4'),
                        **{'D_%s' % s: get(e, s) for s in SEG4}, rank_vs_random=rk, verdict=poi.loc[e, 'verdict'], research_status=poi.loc[e, 'research_status']))
    O.atomic_write_csv(os.path.join(od, 'main72_E6o.csv'), pd.DataFrame(m72))
    print(json.dumps(dict(randoms=len(RT), policy=len(PO), main72=len(m72),
                          verdicts={'|'.join(map(str, k)): int(v) for k, v in PO.groupby(['profile_name', 'execution_profile', 'verdict']).size().items()}),
                     ensure_ascii=False, default=str), flush=True)


if __name__ == '__main__':
    main()
