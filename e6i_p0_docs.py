#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i P0 登记文件: source_manifest.json / registry/{mothers, mother_needs, feature_semantics_v2,
estimator_families}.csv。不产生任何新测量的收益数字 (mother_needs 只含母体本身的旧读数)。

用法:
  python3 e6i_p0_docs.py --part manifest
  python3 e6i_p0_docs.py --part semantics
  python3 e6i_p0_docs.py --part needs --segment 2015-2018     (母体是旧对象, 四段都可跑)
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import glob
import json
import time
import argparse
import platform
import subprocess

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE

CODE = I.CODE
EXEC = '/c/Users/cnc/resonance_strategy/exec_briefs'   # 仅作记录


def sha(p):
    return I.sha_file(p)


# ------------------------------------------------------------------ manifest
def part_manifest():
    groups = {
        'foundation_readonly': ['data_loader.py', 'features_daily.py', 'event_study.py',
                                'pool_screening_v2.py'],
        'engine_readonly_by_contract': ['comprehensive_factor_diagnosis.py'],
        'e6e_frozen': sorted(os.path.basename(p) for p in glob.glob(os.path.join(CODE, 'e6e_*.py'))),
        'e6f_frozen': sorted(os.path.basename(p) for p in glob.glob(os.path.join(CODE, 'e6f_*.py'))),
        'e6g_frozen': sorted(os.path.basename(p) for p in glob.glob(os.path.join(CODE, 'e6g_*.py'))),
        'e6h_frozen': sorted(os.path.basename(p) for p in glob.glob(os.path.join(CODE, 'e6h_*.py'))),
    }
    out = {g: {f: sha(os.path.join(CODE, f)) for f in fs} for g, fs in groups.items()}
    out['counts'] = {g: len(fs) for g, fs in groups.items()}
    out['e6i_code_at_manifest'] = {os.path.basename(p): sha(p) for p in
                                   sorted(glob.glob(os.path.join(CODE, 'e6i_*.py')))}
    ven = os.path.join(CODE, 'e6i_vendor')
    out['e6i_vendor'] = {os.path.relpath(p, CODE): sha(p) for p in
                         sorted(glob.glob(os.path.join(ven, '**', '*'), recursive=True))
                         if os.path.isfile(p)}
    docs = {}
    for f in ('PLAN_COPY.md', 'brief_copy.md', 'E6i_proposal_copy.md', 'E6h_REVIEW_copy.md'):
        p = os.path.join(I.RES, f)
        docs[f] = dict(sha256=sha(p), bytes=os.path.getsize(p),
                       lines=sum(1 for _ in open(p, 'rb')))
    out['input_documents'] = docs
    out['input_fingerprints_vs_plan_appendix_C'] = [
        dict(file='E6h_REVIEW.md', plan=('5eb27e87dd9a819e', 37021),
             actual=(docs['E6h_REVIEW_copy.md']['sha256'][:16], docs['E6h_REVIEW_copy.md']['bytes']),
             status='MATCH'),
        dict(file='E6i_proposal.md', plan=('38feb8c124ad1dd0', 68130),
             actual=(docs['E6i_proposal_copy.md']['sha256'][:16],
                     docs['E6i_proposal_copy.md']['bytes']),
             status='WARN: 规划 session 定稿日在顶部加勘误块 (#43), 加后 f3c2fd44...; brief §0.1 已登记'),
        dict(file='E6i_plan_web_final.md', plan=('cf9ce859575401dc', None),
             actual=(docs['PLAN_COPY.md']['sha256'][:16], docs['PLAN_COPY.md']['bytes']),
             status='MATCH (brief §0 记的前缀)')]
    # 数据缓存
    cache_dir = '/mnt/sda2/lichenchen/data/cache_e6f'
    dc = {}
    for p in sorted(glob.glob(os.path.join(cache_dir, '*.parquet'))):
        rp = os.path.realpath(p)
        dc[os.path.basename(p)] = dict(bytes=os.path.getsize(rp),
                                       mtime=time.strftime('%Y-%m-%d %H:%M:%S',
                                                           time.localtime(os.path.getmtime(rp))),
                                       sha256=sha(rp))
    out['data_cache'] = dc
    import numpy, pandas, scipy, sklearn, pyarrow
    out['runtime'] = dict(python=platform.python_version(), numpy=numpy.__version__,
                          pandas=pandas.__version__, scipy=scipy.__version__,
                          sklearn=sklearn.__version__, pyarrow=pyarrow.__version__,
                          pyarrow_s3_blocked=('S3FileSystem' in __import__(
                              'pyarrow.fs', fromlist=['_not_imported'])._not_imported),
                          ulimit_u=int(subprocess.check_output(['bash', '-c', 'ulimit -u'])
                                       .decode().strip()),
                          cpu_logical=os.cpu_count(),
                          approved_cpuset='96-191,288-383')
    g = lambda *a: subprocess.check_output(['git', '-C', CODE] + list(a)).decode().strip()
    out['git'] = dict(head=g('rev-parse', '--short', 'HEAD'),
                      status_porcelain=g('status', '--porcelain').splitlines())
    out['written_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    out['frozen_end'] = I.MARKET_DATA_END_MAX
    I.atomic_write_json(os.path.join(I.RES, 'source_manifest.json'), out)
    print('manifest: 冻结文件 %s; 数据缓存 %d 件; HEAD %s; 未跟踪/改动 %d 行'
          % (out['counts'], len(dc), out['git']['head'], len(out['git']['status_porcelain'])))


# ------------------------------------------------------------------ semantics
DIR_PRIMARY = {
    # (axis, family) -> (primary, competing, basis)  —— plan §5.7 默认方向表; 方向是描述符
    'T': ('high_bad', 'low_bad', '继承原 T 低值为主, 反向作机制对照'),
    'K': ('high_bad', 'low_bad', '延用原 K 低值方向且保留高值竞争'),
    'V': ('high_bad', 'low_bad', '范围/尾风险低值保护, 反方向对照'),
    'R': ('split', 'split', '低值/高值按反转/延续分域 (两个域, 不合并)'),
    'O': ('both', 'both', '均值/份额/方差不共享方向, 高低两种角色都登记'),
    'C': ('high_bad', 'low_bad', '高位置为坏是主假设, 反向另域'),
    'A': ('both', 'both', '量能高低竞争均保留'),
    'S': ('state', 'state', '只按 §4.8 状态作用, 不作截面排序分量'),
}
INVERSE_RESPONSE_FAMILIES = {'turnover_response', 'amount_response', 'pointwise_inverse_bridge'}
FRICTION_FAMILIES = {'friction_roll', 'friction_cs', 'friction_ar', 'friction_edge',
                     'friction_zero'}
SRC_TAG = {'LEGACY': '[E]', 'RESEARCH': '[P]'}
LIT_FAMILIES = {'range': '[L] Parkinson 1980', 'ohlc': '[L] GK1980/RS1991/YZ2000/Meilijson2011',
                'friction_roll': '[L] Roll 1984', 'friction_cs': '[L] Corwin-Schultz 2012',
                'friction_ar': '[L] Abdi-Ranaldo 2017', 'friction_edge': '[L] AGK 2024 (vendor)',
                'semivariance': '[L] 部分矩', 'tail': '[L] Bali-Cakici-Whitelaw 2011 (MAX)',
                'relative_scale': '[L] CSA2001 (活动变异)', 'position': '[L] George-Hwang 2004 语义桥',
                'peer_relative': '[L] Moskowitz-Grinblatt 1999 / Hou 2007',
                'residual': '[P] 预估计残差 (W12)', 'path': '[L] Da-Gurun-Warachka 2014 (派生)'}


def part_semantics():
    FE.build_catalog()
    cat = FE.catalog_df()
    rt = []
    for p in glob.glob(os.path.join(I.RES, 'runtime', 'compute_*_*.csv')):
        seg = os.path.basename(p).split('_')[1]
        d = pd.read_csv(p)
        d['segment'] = seg
        rt.append(d)
    rt = pd.concat(rt, ignore_index=True) if rt else pd.DataFrame()
    rows = []
    for _, m in cat.iterrows():
        ax, fam = m['axis_id'], m['family_id']
        prim, comp, basis = DIR_PRIMARY[ax]
        if ax == 'K' and fam in INVERSE_RESPONSE_FAMILIES:
            prim, comp, basis = 'low_bad', 'high_bad', '倒数响应反向映射 (高 |r|/x = 低 K = 好)'
        if ax == 'K' and fam in FRICTION_FAMILIES:
            prim, comp, basis = 'high_bad', 'low_bad', '摩擦高 = 成本高 (RL 边缘替换 / 轻量摩擦否决)'
        cov = {}
        if len(rt):
            sub = rt[(rt.member_id == m['member_id']) & (rt.status == 'SUCCEEDED')]
            for _, r in sub.iterrows():
                cov['cov_pool0_%s' % r['segment']] = r['cov_pool0']
        src_tag = SRC_TAG.get(m['source_class'], '[P]')
        if fam in LIT_FAMILIES and m['source_class'] != 'LEGACY':
            src_tag = LIT_FAMILIES[fam]
        rows.append(dict(
            axis_id=ax, family_id=fam, estimand_id=m['estimand_id'], member_id=m['member_id'],
            formula_version=I.VERSION, source_class=m['source_class'], source_label=src_tag,
            raw_fields=m['raw_fields'], unit=m['unit'], source_sign='as_is',
            direction_primary=prim, direction_competing=comp, direction_basis=basis,
            window=m['window'], min_obs=m['min_obs'] if m['source_class'] != 'LEGACY' else 'source',
            ddof=1, price_policy=('adjusted_cross_day' if ax in ('R',) or fam.startswith('friction')
                                  else 'same_day_ratio'),
            one_word_policy=m['policy'], valid_mask=('is_open & OHLC>0 & L<=min(O,C) & H>=max(O,C)'
                                                     if m['source_class'] != 'LEGACY' else 'source'),
            missing_policy='NaN (不补 0, 不 nanmean 成满权重)', event_clock=m['event_clock'],
            neutralize_scope='pool0 当日 mcap OLS (NS)', transform_order='raw -> mcap_OLS -> rank',
            source_ref=m['source_ref'], representative=bool(m['representative']),
            executable_status='SUCCEEDED' if cov else 'PENDING', note=m['note'], **cov))
    d = pd.DataFrame(rows)
    I.atomic_write_csv(os.path.join(I.RES, 'registry', 'feature_semantics_v2.csv'), d)
    fam = (d.groupby(['axis_id', 'family_id', 'estimand_id'])
           .agg(n_members=('member_id', 'size'), members=('member_id', lambda s: '|'.join(s)),
                source_label=('source_label', 'first'),
                n_representative=('representative', 'sum')).reset_index())
    I.atomic_write_csv(os.path.join(I.RES, 'registry', 'estimator_families.csv'), fam)
    print('semantics_v2: %d 成员 x %d 列; families: %d 行 (%d 族 / %d 估计对象)'
          % (len(d), d.shape[1], len(fam), fam.family_id.nunique(), fam.estimand_id.nunique()))
    print(d.groupby('axis_id').agg(n=('member_id', 'size'),
                                   legacy=('source_class', lambda s: int((s == 'LEGACY').sum())),
                                   rep=('representative', 'sum')).T.to_string())


# ------------------------------------------------------------------ mothers / needs
MOTHER_SLOTS = {
    # mother: (descriptor, core_family, slots{K,T,C: stage/leg}, vetoes, focal_vetoes, dep)
    'R1': ('KT_dep(50,50)|C:k5', 'KT_dep', {'K': 'dep_stage1', 'T': 'dep_stage2'},
           'C:k5', ['C:k5 (CVR_20d 否决, 不是 C 核心腿)'], True),
    'R2': ('KT_mean@30|C:k5+cr5:k10', 'KT_mean', {'K': 'mean_leg0', 'T': 'mean_leg1'},
           'C:k5+cr5:k10', ['C:k5', 'cr5:k10'], False),
    'A06': ('KTC_mean@25|cvr_1d:k10+cr5:k10', 'KTC_mean',
            {'K': 'mean_leg0', 'T': 'mean_leg1', 'C': 'mean_leg2'}, 'cvr_1d:k10+cr5:k10',
            ['cvr_1d:k10', 'cr5:k10'], False),
    'A08': ('T@30|C:k5+cr5:k10', 'T', {'T': 'single'}, 'C:k5+cr5:k10',
            ['C:k5 (CVR_20d 否决, 不是 C 核心腿)', 'cr5:k10'], False),
}


def part_mothers():
    import e6g_core as G
    rows = []
    for mn, (desc, fam, slots, vet, focal, dep) in MOTHER_SLOTS.items():
        assert G.DISPLAY_ID[mn] == desc, (mn, G.DISPLAY_ID[mn], desc)
        rows.append(dict(mother_id=mn, descriptor=desc, core_family=fam, is_dep=dep,
                         K_slot=slots.get('K', 'NOT_APPLICABLE'),
                         T_slot=slots.get('T', 'NOT_APPLICABLE'),
                         C_core_slot=slots.get('C', 'NOT_APPLICABLE'),
                         vetoes=vet, focal_vetoes='|'.join(focal),
                         role='主母体', source='e6g_core.DISPLAY (E6h registry 同一描述符)',
                         note=('C 核心槽位只有 A06 真含 C 腿; A08 / R1 / R2 的 CVR 是否决 -> RC 走 FOCAL 分支'
                               if mn in ('A08', 'R1', 'R2') else '')))
    for mn in I.ANCHOR_MOTHERS:
        rows.append(dict(mother_id=mn, descriptor=G.DISPLAY_ID[mn], role='展示锚',
                         source='e6g_core.DISPLAY'))
    rows.append(dict(mother_id='Blend3', descriptor='(A03+A06+A08)/3 目标权重', role='展示锚',
                     source='e6g_core.blend3_weights'))
    I.atomic_write_csv(os.path.join(I.RES, 'registry', 'mothers.csv'), pd.DataFrame(rows))
    print('mothers.csv: %d 行' % len(rows))


def part_needs(segment):
    import e6h_run_routes as RR
    S = I.seg_i(segment, warm=False)
    rows = []
    for mn in I.MOTHERS:
        P = RR.ParentCtx(S, mn)
        p0 = S.p0c
        g, pos, turn, n8 = P.pnl
        # 持仓日龄: B 中连续在册天数
        age = np.zeros(P.B.shape)
        for t in range(1, S.T):
            age[t] = np.where(P.B[t], age[t - 1] + 1, 0)
        age[0] = P.B[0].astype(float)
        miss = P.cand & ~P.fin
        edge_n = []
        for t in range(S.T):
            d_t = np.where(P.D[t])[0]
            if len(d_t) == 0 or P.nb[t] == 0:
                edge_n.append(0)
                continue
            k = max(1, int(np.floor(0.2 * P.nb[t])))
            edge_n.append(min(k, len(d_t)))
        rows.append(dict(
            segment=segment, mother_id=mn,
            pool0_per_day=float(p0.sum(1).mean()), cand_per_day=float(P.cand.sum(1).mean()),
            score_missing_per_day=float(miss.sum(1).mean()),
            core_keep_per_day=float(P.C.sum(1).mean()),
            econ_reject_D_per_day=float(P.D.sum(1).mean()),
            veto_drop_in_core_per_day=float(P.V.sum(1).mean()),
            final_B_per_day=float(P.nb.mean()), empty_days=int((P.nb == 0).sum()),
            edge_20pct_per_day=float(np.mean(edge_n)),
            capital_pos_mean=float(np.nanmean(pos[2:])), turn_mean=float(np.nanmean(turn[3:])),
            hold_age_mean_days=float(age[P.B].mean()) if P.B.any() else np.nan,
            gross_ann=I.ann(g), net8_ann=I.ann(n8),
            net12_ann=I.ann(g - turn * I.COST_HI / 1e4),
            label='母体旧读数 (源引擎, H5, 8bp); 母体是旧对象, 四段都公开'))
        print('  %s %s B/日 %.1f D/日 %.1f 缺分 %.1f 否决 %.1f net8 %.2f'
              % (segment, mn, rows[-1]['final_B_per_day'], rows[-1]['econ_reject_D_per_day'],
                 rows[-1]['score_missing_per_day'], rows[-1]['veto_drop_in_core_per_day'],
                 rows[-1]['net8_ann']), flush=True)
    p = os.path.join(I.RES, 'registry', 'mother_needs_%s.csv' % segment)
    I.atomic_write_csv(p, pd.DataFrame(rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--part', required=True, choices=['manifest', 'semantics', 'mothers', 'needs'])
    ap.add_argument('--segment', default='2015-2018')
    a = ap.parse_args()
    FE.build_catalog()
    I.set_protected_members(FE.protected_ids())
    {'manifest': part_manifest, 'semantics': part_semantics, 'mothers': part_mothers,
     'needs': lambda: part_needs(a.segment)}[a.part]()


if __name__ == '__main__':
    main()
