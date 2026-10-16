# -*- coding: utf-8 -*-
"""E6m query 表（registry/query_registry_E6m.csv 的 46 个 query；骨架 reports_skeleton/queries/<qid>.csv 列序固定；附录 A6-5 / D-5）。
  --phase deriv  只用推导两段；FULL / FULL_sc 列写 NOT_AUTHORIZED（两后段未授权、未算），不用 NaN 冒充
  --phase full   四段；FULL = e6j_stats.full_g4（四段 D、n），某段缺 → UNDEFINED；FULL_sc 只对 ACTUAL_PARENT（取 policy 表 FULL_sc）
机器表：
  COMPARISON   <stats>/comparison_stats_<段>.csv 中 view == X 的行（object_rule）
  FACT         <stage_a>/<段>/mask_facts_*.csv：卡片对象（该卡全部视图的左端描述符 → 配置）的掩码层事实，长表 desc_id|segment|fact|value|unit
               （权重变化归因 / MATCH_CAP 两张账户层表到位前 NOT_RUN）
  LINEAGE      Q18 用户原话 / CC 解释 / 采纳 / 算子 / 对照 / 结果 query / 范围逐项绑定：交付期写（NOT_RUN）
  B3_* / B4 / B5 / B6   对应机器表到位前写 NOT_RUN
任何 query 都至少一行（空 → status 行）；输出列 = 骨架列，多 / 少即报错。"""
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

SEGS = tuple(M.SEGMENTS)
UNIT = (('port_size', 'pct_pt'), ('edit_gap', 'pct_pt'), ('port3_mid', 'pct_pt'), ('n_', 'count'), ('_days', 'count'), ('days_', 'count'),
        ('movable', 'count'), ('_total', 'count'), ('members', 'count'), ('f_J', 'count'), ('f_deleted', 'count'), ('f_refill', 'count'))


def unit_of(col):
    for k, u in UNIT:
        if k in col:
            return u
    return 'decimal'


def skeleton_cols(qid):
    return pd.read_csv(M.P('reports_skeleton', 'queries', '%s.csv' % qid), nrows=0).columns.tolist()


def status_row(cols, qid, status):
    r = {c: '' for c in cols}
    r['query_id'], r['status'] = qid, status
    return pd.DataFrame([r], columns=cols)


def comparison(q, cols, stats_dir, phase, pol):
    view = q.object_rule.split('==')[1].strip()
    segs = M.DERIV_SEGS if phase == 'deriv' else SEGS
    parts = []
    for s in segs:
        p = os.path.join(stats_dir, 'comparison_stats_%s.csv' % s)
        if os.path.exists(p):
            parts.append(M.read_csv_keep(p, dtype={'comparison_id': str}))
    if not parts:
        return status_row(cols, q.query_id, 'SOURCE_WAIT')
    C = pd.concat(parts, ignore_index=True)
    C = C[C.view == view].copy()
    if C.empty:
        return status_row(cols, q.query_id, 'UNDEFINED')
    C['query_id'] = q.query_id
    C['se_hac_H_ann_pp'] = C['se_H_ann_pp']
    if phase == 'deriv':
        C['FULL_ann_pp'] = 'NOT_AUTHORIZED'
        C['FULL_sc_ann_pp'] = 'NOT_AUTHORIZED'
    else:
        full = {}
        for cid, g in C.groupby('comparison_id'):
            if set(g.segment) >= set(SEGS):
                g = g.set_index('segment').loc[list(SEGS)]
                full[cid] = ST.full_g4(g.D_ann_pp.astype(float).tolist(), g.n_days.astype(float).tolist())[0]
        C['FULL_ann_pp'] = C.comparison_id.map(lambda c: full.get(c, 'UNDEFINED'))
        fsc = pol.set_index('desc_id').FULL_sc.to_dict() if pol is not None and 'FULL_sc' in pol.columns else {}
        C['FULL_sc_ann_pp'] = [fsc.get(l, 'UNDEFINED') if k == 'ACTUAL_PARENT' else 'NOT_APPLICABLE' for l, k in zip(C.left_desc_id, C.kind)]
    return C[cols]


def card_objects(card):
    K = M.read_csv_keep(M.P('registry', 'cards_E6m.csv'), dtype=str).fillna('')
    CM = M.read_csv_keep(M.P('registry', 'comparison_manifest_E6m.csv'), dtype=str, usecols=['view', 'left_desc_id'])
    views = [v for v in K[K.card == card].contrast_views_in_manifest.iloc[0].split('|') if v] if (K.card == card).any() else []
    return sorted(set(CM[CM.view.isin(views)].left_desc_id))


def config_of(did):
    p = did.split('|')
    return '|'.join(p[:6] + p[7:])


def facts(q, cols, sa_dir, phase):
    if 'weight_change' in q.machine_table:
        return status_row(cols, q.query_id, 'NOT_RUN')
    objs = card_objects(q.card)
    segs = M.DERIV_SEGS if phase == 'deriv' else SEGS
    rows = []
    for s in segs:
        fs = sorted(glob.glob(os.path.join(sa_dir, s, 'mask_facts_*.csv')))
        if not fs:
            continue
        A = pd.concat([M.read_csv_keep(f, dtype={'param': str, 'alpha': str}) for f in fs], ignore_index=True)
        A = A[(A.kind == 'MAIN')].drop_duplicates('target').set_index('target')
        num = [c for c in A.columns if c not in ('segment', 'form', 'kind', 'block', 'measurement', 'operator', 'param', 'alpha', 'memory', 'status')]
        for cfg in sorted(set(config_of(d) for d in objs)):         # 掩码层事实与 H 无关：每配置一份，desc_id 的 H 段写 H*
            p_ = cfg.split('|')
            did = '|'.join(p_[:6] + ['H*'] + p_[6:])
            if cfg not in A.index:
                rows.append(dict(query_id=q.query_id, desc_id=did, segment=s, fact='', value='', unit='', status='UNDEFINED'))
                continue
            r = A.loc[cfg]
            if r.status != 'COMPUTED':
                rows.append(dict(query_id=q.query_id, desc_id=did, segment=s, fact='', value='', unit='', status=str(r.status)))
                continue
            for c in num:
                v = r[c]
                if isinstance(v, str) and v == '':
                    continue
                if not isinstance(v, str) and pd.isna(v):                # 缺失不当 0、不写 nan：显式 UNDEFINED
                    rows.append(dict(query_id=q.query_id, desc_id=did, segment=s, fact=c, value='', unit=unit_of(c), status='UNDEFINED'))
                    continue
                rows.append(dict(query_id=q.query_id, desc_id=did, segment=s, fact=c, value=v, unit=unit_of(c), status='COMPUTED'))
    if not rows:
        return status_row(cols, q.query_id, 'SOURCE_WAIT')
    return pd.DataFrame(rows)[cols]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', required=True, choices=['deriv', 'full'])
    ap.add_argument('--stats', required=True)
    ap.add_argument('--stage-a', required=True)
    ap.add_argument('--policy', default='')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    t0 = time.time()
    if a.phase == 'full':
        import e6m_s_gate as GT                                     # 四段 query 只在两后段授权后生成（推导段读法另有 deriv 表）
        GT.post_gate(M.POST_SEGS[0], 'queries full')
    Q = M.read_csv_keep(M.P('registry', 'query_registry_E6m.csv'), dtype=str)
    pol = pd.read_csv(a.policy, keep_default_na=False, na_values=[''], low_memory=False) if a.policy and os.path.exists(a.policy) else None
    os.makedirs(a.out, exist_ok=True)
    summ, outs = [], []
    for q in Q.itertuples():
        cols = skeleton_cols(q.query_id)
        if q.schema == 'COMPARISON':
            df = comparison(q, cols, a.stats, a.phase, pol)
        elif q.schema == 'FACT':
            df = facts(q, cols, a.stage_a, a.phase)
        else:
            df = status_row(cols, q.query_id, 'NOT_RUN')
        if list(df.columns) != cols:
            raise RuntimeError('%s 输出列与骨架不一致：%s' % (q.query_id, sorted(set(df.columns) ^ set(cols))))
        p = os.path.join(a.out, '%s.csv' % q.query_id)
        M.atomic_write_csv(p, df)
        outs.append(p)
        bad = M.scan_status_words(df)
        summ.append(dict(query_id=q.query_id, schema=q.schema, rows=len(df), status=json.dumps(df.status.value_counts().to_dict(), ensure_ascii=False),
                         forbidden_status_hits=len(bad)))
    S = pd.DataFrame(summ)
    ps = os.path.join(a.out, 'queries_summary_%s.csv' % a.phase)
    M.atomic_write_csv(ps, S)
    ok = int(S.forbidden_status_hits.sum()) == 0 and (S.rows > 0).all()
    M.write_receipt(os.environ.get('E6M_TASK', 'S_queries_%s' % a.phase), [ps] + outs, status='SUCCEEDED' if ok else 'FAILED', code=[__file__, M.__file__],
                    queries=len(S), wall_s=round(time.time() - t0, 1))
    print(S.groupby('schema').rows.agg(['count', 'sum']).to_string(), flush=True)
    print(json.dumps(dict(queries=len(S), zero_row=int((S.rows == 0).sum()), forbidden=int(S.forbidden_status_hits.sum())), ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
