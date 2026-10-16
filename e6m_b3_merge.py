# -*- coding: utf-8 -*-
"""E6m B3 先行结果的并入（brief §5 N8 / S4）。阶段 N 的 B3 输出封存不读；阶段 S：
  anchor   锚判定（不读 B3 任何数值）：Stage 0 S 的
             A2-5 J_B1_qCC raw 逐位（四段）、A2-5 本轮云机 kQ0 = 引擎 meas_kf(Q0)（四段 structid）、A4-3 状态缓存逐键逐位、A1-2 E5a 交付池 7 个成员逐字节
           全 PASS → ANCHOR_PASSED（原样并入，标 COMPUTED_BEFORE_ANCHOR, ANCHOR_PASSED）；任一 FAIL → ANCHOR_FAILED（全部作废重算，旧产物留档）；
           其余（输入未到）→ ANCHOR_PENDING。先核封存件 404 个文件 sha 未变。写 stageN/B3_anchor_status_S.json（封存目录之外；不改、不增封存件）。
  tables   ANCHOR_PASSED 且两后段已授权后（B3 四段）：五张固定表 b3_cells / b3_mirror_cvr / b3_mirror_gap / b3_pairs / b3_random。
           骨架无段（b3_pairs / b3_random 也无域）列：段与域作前缀编进 id 列（cell_id = 段|格；contrast_id = 段|域|对比），不改骨架列
           （STAGE_S_IMPL_PLAN §5 第 24 项，待决策端定）；weighting 列写 benchmark（cells_summary 的基准口径），capital_decimal = 该域份额。"""
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

B = lambda *p: M.P('stageN', 'B3_prelim', *p)


def checks():
    D = []
    for p in (M.P('stage0_S', 'c2_c4', 'checks_features.csv'), M.P('stage0_S', 'c1', 'checks_identity.csv')) + \
            tuple(sorted(glob.glob(M.P('stage0_S', 'c3', 'checks_structid_*.csv')))):
        if os.path.exists(p):
            D.append(M.read_csv_keep(p, dtype=str).assign(table=os.path.basename(p)))
    return pd.concat(D, ignore_index=True) if D else pd.DataFrame(columns=['item', 'object', 'metric', 'status', 'table'])


def anchor_verdict(C):
    parts = {
        'A2-5 raw（四段）': C[(C.item == 'A2-5') & C.metric.str.startswith('raw 逐位')],
        'A2-5 kQ0 = 引擎（四段）': C[(C.item == 'A2-5') & C.metric.str.contains('本轮云机 kQ0')],
        'A4-3 状态缓存': C[(C.item == 'A4-3') & (C.status != 'INFO')],
        'A1-2 E5a 交付池': C[(C.item == 'A1-2') & C.object.str.startswith('E5a pool')],
    }
    need = {'A2-5 raw（四段）': 4, 'A2-5 kQ0 = 引擎（四段）': 4, 'A1-2 E5a 交付池': 7}
    ev, verdict = {}, 'ANCHOR_PASSED'
    for k, g in parts.items():
        st = g.status.value_counts().to_dict()
        ev[k] = st
        if st.get('FAIL'):
            verdict = 'ANCHOR_FAILED'
        elif verdict != 'ANCHOR_FAILED' and (st.get('SOURCE_WAIT') or st.get('PASS', 0) < need.get(k, 1) or set(st) - {'PASS'}):
            verdict = 'ANCHOR_PENDING'
    return verdict, ev


def verify_seal():
    import e6m_stage0_S as S0
    seal = json.load(open(B('seal_B3_prelim.json'), encoding='utf-8'))
    paths = [M.P(f['path']) if os.path.exists(M.P(f['path'])) else B(f['path']) for f in seal['files']]
    sh = S0.Hasher(workers=8).many(paths)
    bad = [f['path'] for f, p in zip(seal['files'], paths) if sh[p] != f['sha256']]
    return seal['all_ok'] and not bad, len(paths), bad


def task_anchor():
    ok_seal, n, bad = verify_seal()
    verdict, ev = anchor_verdict(checks())
    if not ok_seal:
        verdict = 'SEAL_CHANGED'
    rec = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), verdict=verdict, seal_files=n, seal_changed=bad[:20], evidence=ev,
               labels=['COMPUTED_BEFORE_ANCHOR', verdict] if verdict in ('ANCHOR_PASSED', 'ANCHOR_FAILED') else ['ANCHOR_PENDING'],
               rule='全 PASS → 原样并入（COMPUTED_BEFORE_ANCHOR, ANCHOR_PASSED）；任一 FAIL → 全部作废重算（旧产物留档标 ANCHOR_FAILED）；其余 → 维持 ANCHOR_PENDING')
    p = M.P('stageN', 'B3_anchor_status_S.json')
    M.atomic_write_json(p, rec)
    return p, rec


def cat_out(pattern):
    parts = []
    for f in sorted(glob.glob(B('out', '*', pattern))):
        parts.append(pd.read_csv(f, keep_default_na=False, na_values=[''], low_memory=False))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def task_tables(out):
    import e6m_s_gate as GT
    st = json.load(open(M.P('stageN', 'B3_anchor_status_S.json'), encoding='utf-8')) if os.path.exists(M.P('stageN', 'B3_anchor_status_S.json')) else {}
    if st.get('verdict') != 'ANCHOR_PASSED':
        raise RuntimeError('B3 锚未通过（%s）：不读、不并入' % st.get('verdict', '未判定'))
    GT.post_gate(M.POST_SEGS[0], 'B3 tables')
    sk = lambda n: pd.read_csv(M.P('reports_skeleton', 'fixed', '%s.csv' % n), nrows=0).columns.tolist()
    outs = []
    Cs = cat_out('cells_summary.csv')
    for name, fam in (('b3_cells', None), ('b3_mirror_cvr', 'MIRROR_CVR'), ('b3_mirror_gap', 'MIRROR_GAP')):
        X = Cs[Cs.family == fam] if fam else Cs[~Cs.family.str.startswith('MIRROR')]
        df = pd.DataFrame(dict(query_id=name, cell_id=X.segment + '|' + X.cell_id, domain=X.domain, h=X.h, label=X.label, weighting='benchmark=' + X.benchmark.astype(str),
                               n_dates=X.n_dates, n_events=X.n_events, n_spells=X.n_spells, capital_decimal=X.domain_share, mean_bp_per_h=X.mean_bp_per_h, status=X.status))
        p = os.path.join(out, '%s.csv' % name)
        M.atomic_write_csv(p, df[sk(name)])
        outs.append(p)
    R = cat_out('contrasts_real*.csv')
    Rr = cat_out('contrasts_random*.csv')
    P = cat_out('contrasts_pairs*.csv')
    key = ['segment', 'domain', 'contrast_id', 'matching_id']
    Pk = P.groupby(key).agg(pairs=('pairs', 'sum'), uh=('unmatched_high', 'sum'), ul=('unmatched_low', 'sum')).reset_index() if len(P) else P
    J = R.merge(Pk, on=key, how='left').merge(Rr[key + ['random_id', 'label', 'h', 'mean_of_path_means_bp_per_h', 'mcse_bp_per_h', 'status']].rename(
        columns={'status': 'random_status'}), on=key + ['label', 'h'], how='left')
    miss = J.random_id.isna()
    if miss.any():      # 补丁十六：无随机值行的键（Q09：e6m_b3_run.mech_mode 两种机制全 NOT_APPLICABLE）按 B3 状态表核后填 NONE / NOT_APPLICABLE；不是全 NOT_APPLICABLE 即停
        St = cat_out('contrasts_status*.csv')
        if not len(St):
            raise RuntimeError('B3 合并：%d 行无随机值，且没有 contrasts_status 表可核' % int(miss.sum()))
        na_all = St.groupby(key).random_status.agg(lambda s: bool((s == 'NOT_APPLICABLE').all())).rename('na_all').reset_index()
        ck = J.loc[miss, key].merge(na_all, on=key, how='left')
        okk = ck.na_all.eq(True)
        if not okk.all():
            raise RuntimeError('B3 合并：%d 行无随机值且状态表不是全 NOT_APPLICABLE：%s' % (int((~okk).sum()), ck[~okk.values].head(3).to_dict('records')))
        J.loc[miss, 'random_id'] = 'NONE'
        J.loc[miss, 'random_status'] = 'NOT_APPLICABLE'
    for name in ('b3_pairs', 'b3_random'):
        df = pd.DataFrame(dict(query_id=name, contrast_id=J.segment + '|' + J.domain + '|' + J.contrast_id, matching_id=J.matching_id, random_id=J.random_id,
                               h=J.h, label=J.label, n_pairs=J.pairs, n_unmatched=J.uh.fillna(0) + J.ul.fillna(0), mean_diff_bp_per_h=J.mean_bp_per_h,
                               se_hac_bp_per_h=J.hac_se_bp_per_h, rand_mean_bp_per_h=J.mean_of_path_means_bp_per_h, mcse_bp_per_h=J.mcse_bp_per_h,
                               status=J.status if name == 'b3_pairs' else J.random_status))
        p = os.path.join(out, '%s.csv' % name)
        M.atomic_write_csv(p, df[sk(name)])
        outs.append(p)
    return outs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['anchor', 'tables'])
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    t0 = time.time()
    if a.task == 'anchor':
        p, rec = task_anchor()
        M.write_receipt(os.environ.get('E6M_TASK', 'S_b3_anchor'), [p], status='SUCCEEDED', code=[__file__, M.__file__], verdict=rec['verdict'])
        print(json.dumps(dict(verdict=rec['verdict'], evidence=rec['evidence'], seal_files=rec['seal_files']), ensure_ascii=False))
        return 0
    os.makedirs(a.out, exist_ok=True)
    outs = task_tables(a.out)
    M.write_receipt(os.environ.get('E6M_TASK', 'S_b3_tables'), outs, status='SUCCEEDED', code=[__file__, M.__file__], wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(tables=len(outs)), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
