# -*- coding: utf-8 -*-
"""E6m N8 · B3 先行 · 封存（合同 §7）。只读文件名、sha、状态列与计数列；不读任何收益 / 标签数值列。
1. 日志脱敏（同一 M.san，只改路径段）；
2. 覆盖核：冻结 contrast 清单 390 行 × 四段都有状态行；冻结 cell 清单 660 格 × 四段都有汇总行；队列全部 rc = 0；
3. 写 stageN/B3_prelim/b3_status_N8.csv（对比状态）、b3_cells_index_N8.csv（格 × 段：状态与计数）、seal_B3_prelim.json（文件 sha 全表）。"""
import e6j_boot  # noqa: F401
import os
import re
import sys
import json
import time

import pandas as pd

import e6m_core as M

SEGS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')
B = lambda *p: M.P('stageN', 'B3_prelim', *p)


def main():
    t0 = time.time()
    nsan = 0
    for f in sorted(os.listdir(B('logs'))):
        p = B('logs', f)
        s = open(p, encoding='utf-8', errors='replace').read()
        t = M.san(s)
        if t != s:
            M.atomic_write_text(p, t)
            nsan += 1
    q = open(B('logs', 'queue.log'), encoding='utf-8').read().split('\n')
    done = [l for l in q if ' done ' in l]
    bad_rc = [l for l in done if not l.endswith('rc=0')]
    # 对比状态覆盖
    reg = M.read_csv_keep(M.P('registry', 'b3_contrasts_E6m.csv'), dtype=str)
    st = []
    for d in sorted(os.listdir(B('out'))):
        for f in sorted(os.listdir(B('out', d))):
            if f.startswith('contrasts_status'):
                st.append(M.read_csv_keep(B('out', d, f), dtype=str))
    st = pd.concat(st, ignore_index=True)
    key = ['contrast_id', 'matching_id', 'random_id']
    # 合并状态以逐行状态为准（v1 的进程级状态表把"跑过"记成 COMPUTED；只改状态词，不读数值列）
    rr, rd = [], []
    for d in sorted(os.listdir(B('out'))):
        for f in sorted(os.listdir(B('out', d))):
            if f.startswith('contrasts_real') and f.endswith('.csv'):
                rr.append(pd.read_csv(B('out', d, f), usecols=['segment', 'contrast_id', 'matching_id', 'status'], dtype=str, keep_default_na=False))
            if f.startswith('contrasts_random') and f.endswith('.csv'):
                rd.append(pd.read_csv(B('out', d, f), usecols=['segment', 'contrast_id', 'matching_id', 'random_id', 'status'], dtype=str,
                                      keep_default_na=False))
    agg = lambda s: 'COMPUTED' if (s == 'COMPUTED').any() else 'DEGENERATE_CONDITIONAL_CONTROL'
    rr = pd.concat(rr).groupby(['segment', 'contrast_id', 'matching_id']).status.agg(agg).rename('real_row').reset_index()
    rd = pd.concat(rd).groupby(['segment', 'contrast_id', 'matching_id', 'random_id']).status.agg(agg).rename('random_row').reset_index()
    st = st.merge(rr, on=['segment', 'contrast_id', 'matching_id'], how='left').merge(rd, on=['segment'] + key, how='left')
    st['real_status_process'] = st.real_status
    st['random_status_process'] = st.random_status
    st['real_status'] = st.real_row.where(st.real_row.notna(), st.real_status)
    st['random_status'] = st.random_row.where(st.random_row.notna(), st.random_status)
    relabel = int((st.random_status != st.random_status_process).sum() + (st.real_status != st.real_status_process).sum())
    st = st.drop(columns=['real_row', 'random_row'])
    cover = []
    for s in SEGS:
        x = st[st.segment == s]
        m = reg[key].merge(x[key + ['real_status', 'random_status']], on=key, how='left', indicator=True)
        cover.append(dict(segment=s, registry_rows=len(reg), status_rows=len(x), missing=int((m._merge == 'left_only').sum()),
                          duplicated=int(x.duplicated(key).sum())))
    stat = st.groupby(['segment', 'real_status', 'random_status']).size().reset_index(name='rows')
    # 格覆盖（只取状态 / 计数列）
    creg = M.read_csv_keep(M.P('registry', 'b3_cells_E6m.csv'), dtype=str)
    cols = ['segment', 'domain', 'cell_id', 'status', 'n_dates', 'n_events', 'n_spells']
    ci = []
    for d in sorted(os.listdir(B('out'))):
        p = B('out', d, 'cells_summary.csv')
        if os.path.exists(p):
            ci.append(pd.read_csv(p, usecols=cols, dtype=str, keep_default_na=False).drop_duplicates(['segment', 'cell_id']))
    ci = pd.concat(ci, ignore_index=True)
    ccov = [dict(segment=s, registry_cells=len(creg), summary_cells=int((ci.segment == s).sum()),
                 missing=len(set(creg.cell_id) - set(ci[ci.segment == s].cell_id)), empty=int(((ci.segment == s) & (ci.status != 'COMPUTED')).sum()))
            for s in SEGS]
    M.atomic_write_csv(B('b3_status_N8.csv'), st)
    M.atomic_write_csv(B('b3_cells_index_N8.csv'), ci)
    # 文件 sha 全表
    files = []
    for root, _, fs in os.walk(B()):
        for f in sorted(fs):
            p = os.path.join(root, f)
            if f.startswith('seal_B3_prelim'):
                continue
            files.append(dict(path=os.path.relpath(p, M.work()), bytes=os.path.getsize(p), sha256=M.sha_file(p)))
    rec = {}
    for f in sorted(os.listdir(M.P('task_status'))):
        if f.startswith('N8_'):
            r = json.load(open(M.P('task_status', f), encoding='utf-8'))
            rec[r['task_id']] = r['status']
    ok = (not bad_rc and len(done) == 32 and all(c['missing'] == 0 and c['duplicated'] == 0 for c in cover)
          and all(c['missing'] == 0 for c in ccov))
    seal = dict(seal='E6m N8 B3 先行封存', written_at=time.strftime('%Y-%m-%d %H:%M:%S'), machine=M.MACHINE,
                labels=['HISTORICAL_CONDITIONAL_RESULT_EXPOSED', 'ANCHOR_PENDING'],
                executor_read_values=False, note='执行端只读了文件名、sha、状态与计数列；锚通过前不读、不报数值（合同 §7）',
                contract=dict(main=M.sha_file(B('B3_run_contract.md')), addendum_1=M.sha_file(B('B3_run_contract_addendum.md'))),
                authorization=M.sha_file(M.P('stageN', 'B3_prelim_authorization.json')),
                queue=dict(jobs_done=len(done), bad_rc=bad_rc), contrast_coverage=cover, cell_coverage=ccov,
                status_counts=stat.to_dict('records'), status_relabelled_from_row_level=relabel,
                status_note='合并状态取逐行状态（contrasts_real / contrasts_random 的 status 列）；进程级 contrasts_status*.csv 的 random_status 按"是否跑过"标记，'
                            '另存为 *_process 列备查；e6m_b3_run.py 已改为"有值才算 COMPUTED"（不重跑）',
                receipts_N8=rec, logs_sanitized=nsan, files=files, all_ok=bool(ok),
                script_sha256=M.sha_file(os.path.realpath(__file__)))
    M.atomic_write_json(B('seal_B3_prelim.json'), seal)
    M.write_receipt(os.environ.get('E6M_TASK', 'N8_b3_seal'), [B('seal_B3_prelim.json'), B('b3_status_N8.csv'), B('b3_cells_index_N8.csv')],
                    status='SUCCEEDED' if ok else 'FAILED', code=[__file__, M.__file__], files=len(files), all_ok=ok)
    print(json.dumps(dict(all_ok=ok, files=len(files), jobs_done=len(done), bad_rc=len(bad_rc), contrast_coverage=cover, cell_coverage=ccov,
                          logs_sanitized=nsan, wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    print(stat.to_string(index=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
