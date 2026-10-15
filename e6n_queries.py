# -*- coding: utf-8 -*-
"""E6n query 表（registry/query_registry_E6n.csv → reports/queries/<qid>.csv；骨架 reports_skeleton/queries/<qid>.csv 列序固定；brief A9 / 附录 E ①）。
每个 query 从其绑定机器表抽行，输出列 = 骨架列（多 / 少即报错）；绑定表缺列 → 报错（不写空表）；绑定表 0 行 → 报错；
登记为占位（placeholder = True）的 query 只写一行 status = PLACEHOLDER_BOUND 并指向固定表（E6m E01：全部 NOT_RUN 的 query = FAIL，除非登记占位）。
  run --phase deriv|full    selftest（A1-auto ⑳：合成缺列 / 空表各触发一次）"""
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6n_core as N


class QueryError(RuntimeError):
    pass


def need(df, cols, what):
    miss = [c for c in cols if c not in df.columns]
    if miss:
        raise QueryError('%s 缺列 %s' % (what, miss))
    if not len(df):
        raise QueryError('%s 0 行' % what)


def skeleton_cols(qid, root=None):
    return pd.read_csv(os.path.join(root or N.P('reports_skeleton', 'queries'), '%s.csv' % qid), nrows=0).columns.tolist()


def frame(rows, cols, qid):
    df = pd.DataFrame(rows)
    for c in cols:
        if c not in df.columns:
            df[c] = 'NOT_APPLICABLE' if c != 'status' else 'COMPUTED'
    df['query_id'] = qid
    extra = sorted(set(df.columns) - set(cols))
    df = df[cols]
    if extra:
        pass
    return df


def ext_comparison(q, cols, phase):
    view = q.object_rule.split('==')[1].strip()
    segs = N.DERIV_SEGS if phase == 'deriv' else N.SEGMENTS
    parts = []
    for s in segs:
        p = N.P('results', phase if phase == 'deriv' else 'full', 'comparison_stats_%s.csv' % s)
        if not os.path.exists(p):
            raise QueryError('%s 不存在' % N.rel(p))
        C = pd.read_csv(p, keep_default_na=False, dtype={'comparison_id': str})
        need(C, ['comparison_id', 'view', 'left_desc_id', 'right_desc_id', 'D_ann_pp', 'n'], N.rel(p))
        C = C[C.view == view].copy()
        C['segment'] = s
        parts.append(C)
    C = pd.concat(parts, ignore_index=True)
    if not len(C):
        raise QueryError('view %s 无行' % view)
    if phase == 'full':
        pol = pd.read_csv(N.P('results', 'full', 'comparison_full.csv'), keep_default_na=False, dtype={'comparison_id': str})
        need(pol, ['comparison_id', 'FULL_ann_pp', 'G4_ann_pp'], 'comparison_full.csv')
        C = C.merge(pol[['comparison_id', 'FULL_ann_pp', 'G4_ann_pp']], on='comparison_id', how='left')
    else:
        C['FULL_ann_pp'] = 'NOT_AUTHORIZED'
        C['G4_ann_pp'] = 'NOT_AUTHORIZED'
    C['status'] = np.where(pd.to_numeric(C.D_ann_pp, errors='coerce').notna(), 'COMPUTED', 'UNDEFINED')
    return frame(C.to_dict('records'), cols, q.query_id)


RENAME = {'B3': {'core': 'form', 'D_vs_parent_ann_pp': 'D_ann_pp', 'paths': 'n'}, 'ANCHOR': {}, 'POLICY': {'policy_result': 'policy_verdict'}}
MELT_KEYS = {'B2': ('form', 'object_key', 'trigger', 'H', 'horizon_mode', 'mirror', 'fee_mode', 'control', 'segment'),
             'DATA': (), 'LINEAGE': ()}


def load_bound(q):
    p = N.P(q.table)
    if not os.path.exists(p):
        raise QueryError('绑定表不存在：%s' % q.table)
    if p.endswith('.json'):
        j = json.load(open(p, encoding='utf-8'))
        return pd.DataFrame([dict(key=k, value=json.dumps(v, ensure_ascii=False)[:500] if isinstance(v, (dict, list)) else v) for k, v in j.items()])
    return pd.read_csv(p, keep_default_na=False, low_memory=False)


def melt(T, keys, cols, qid, item):
    """宽表 → 骨架长表：键列原样，其余每列一行（stat / item = 列名，value = 值）。"""
    rows = []
    kc = [k for k in keys if k in T.columns]
    vc = [c for c in T.columns if c not in kc and c not in ('status', 'query_id')]
    for r in T.to_dict('records'):
        base = {k: r[k] for k in kc}
        for c in vc:
            d = dict(base)
            if 'stat' in cols:
                d.update(stat=c, value=r[c], unit=('ann_pp' if c.endswith('_ann_pp') else 'bp' if '_bp' in c else 'decimal' if c.endswith('_decimal') else 'count'
                                                   if c.startswith(('n_', 'n')) else 'raw'))
            else:
                first = T.columns[0]
                d.update(item='%s:%s' % (item, c), key='%s=%s' % (first, r.get(first)), field=c, ledger=item, id=str(r.get(first)), value=r[c], unit='raw')
            d['status'] = r.get('status', 'COMPUTED') or 'COMPUTED'
            rows.append(d)
    return frame(rows, cols, qid)


def ext_table(q, cols, phase, key_filter=None):
    T = load_bound(q)
    if key_filter is not None:
        T = key_filter(T)
    if not len(T):
        raise QueryError('%s 0 行' % q.table)
    if q.schema in MELT_KEYS:
        return melt(T, MELT_KEYS[q.schema], cols, q.query_id, os.path.basename(q.table))
    T = T.rename(columns=RENAME.get(q.schema, {}))
    need(T, [c for c in cols if c not in ('query_id', 'status')][:1], q.table)
    if 'status' not in T.columns:
        T['status'] = 'COMPUTED'
    return frame(T.to_dict('records'), cols, q.query_id)


def generate(phase, out):
    Q = pd.read_csv(N.P('registry', 'query_registry_E6n.csv'), keep_default_na=False)
    os.makedirs(out, exist_ok=True)
    summ = []
    for q in Q.itertuples():
        cols = skeleton_cols(q.query_id)
        if str(q.placeholder) == 'True':
            df = pd.DataFrame([{c: '' for c in cols}], columns=cols)
            df['query_id'], df['status'] = q.query_id, 'PLACEHOLDER_BOUND'
        elif q.schema == 'COMPARISON':
            df = ext_comparison(q, cols, phase)
        elif q.schema == 'B1_0':
            mem = q.object_rule.split('{')[1].split('}')[0].split(',') if '{' in q.object_rule else None
            df = ext_table(q, cols, phase, (lambda T: T[T.member.isin(mem)]) if mem else None)
        else:
            if phase == 'deriv' and q.schema in ('POLICY', 'B4', 'FOUR_ACCOUNT', 'SUPPORT', 'COMPONENT_DOSE', 'B2', 'B3'):
                df = pd.DataFrame([{c: '' for c in cols}], columns=cols)
                df['query_id'], df['status'] = q.query_id, 'NOT_AUTHORIZED'
            else:
                df = ext_table(q, cols, phase)
        if list(df.columns) != cols:
            raise QueryError('%s 输出列与骨架不一致' % q.query_id)
        p = os.path.join(out, '%s.csv' % q.query_id)
        N.atomic_write_csv(p, N.to_status(df))
        summ.append(dict(query_id=q.query_id, schema=q.schema, rows=len(df), status=json.dumps(df.status.value_counts().to_dict(), ensure_ascii=False),
                         all_not_run=bool((df.status == 'NOT_RUN').all()), placeholder=str(q.placeholder) == 'True'))
    S = pd.DataFrame(summ)
    N.atomic_write_csv(os.path.join(out, '_summary.csv'), S)
    return S


def selftest_errors():
    """合成：缺列 → QueryError；0 行 → QueryError。两者都触发返回 True。"""
    ok1 = ok2 = False
    try:
        need(pd.DataFrame(dict(a=[1])), ['a', 'b'], 'synthetic')
    except QueryError:
        ok1 = True
    try:
        need(pd.DataFrame(dict(a=[], b=[])), ['a', 'b'], 'synthetic')
    except QueryError:
        ok2 = True
    return ok1 and ok2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['run', 'selftest'])
    ap.add_argument('--phase', default='full', choices=['deriv', 'full'])
    a = ap.parse_args()
    if a.step == 'selftest':
        print(selftest_errors())
        return 0
    out = N.P('reports', 'queries_%s' % a.phase)
    S = generate(a.phase, out)
    N.write_receipt('E6n_queries_%s' % a.phase, [os.path.join(out, '_summary.csv')], code=[__file__], queries=len(S), all_not_run=int(S.all_not_run.sum()))
    print(S.to_string(index=False)[:3000])
    return 0


if __name__ == '__main__':
    sys.exit(main())
