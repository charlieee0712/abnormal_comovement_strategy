# -*- coding: utf-8 -*-
"""E6l 交付（brief §9；plan §13.4；附录 D-5 / D-6 / E；E6k e6k_deliver 同式）。
  --tables      机器表：results/account_manifest.csv（全部账户 / 掩码 / 随机文件 sha）、results/coverage.csv（登记 vs 已算）、
                results/read_permissions.csv（读数程序 × 时刻 × 封存版本）、results/random_registry.csv（随机登记 + 回执路径数 / 分片 / 生成器）、
                results/risk_exposure_daily.parquet（主展示 / 剂量 / 母体目标逐日暴露）、results/mask_edit_ledger.csv（掩码事实全段）
  --hypotheses  results/hypothesis_outcomes.json：16 卡（PLAN_COPY 行号 + query_id + 执行端读完结果后写的八字段，文字来自 results/hypothesis_text_input_E6l.json）
  --review      reports/E6l_REVIEW_input.md：全部 REPORT / 表 / 账本 / 登记 / 授权 / 代码 / 输入的路径与 sha256
  --gate        闭包门（附录 D-5）→ results/completion_receipt.json
  --mirror      E6l_MIRROR.md5：交付文档三处（结果目录 / 47 exec_briefs / 本地由工作站现算后提供）md5 + sha256
不写判词、不写共享 memory。"""
import e6l_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time
import shutil
import hashlib
import subprocess

import numpy as np
import pandas as pd

import e6l_core as L

REPORTS = ['E6l_REPORT_R0.md', 'E6l_REPORT_part1.md', 'E6l_REPORT_part2.md', 'E6l_REPORT_part3.md', 'E6l_REPORT_mechanisms.md', 'E6l_REPORT_carried.md',
           'E6l_REPORT_cards.md', 'E6l_REVIEW_input.md', 'E6l_lessons_delta.md', 'E6l_limit_register.md', 'E6l_code_change_register.md', 'E6l_record_B_draft.md']
FIXED = ['source_lineage', 'kernel_contracts', 'memory_contracts', 'hypothesis_lineage', 'candidate72', 'dose72', 'comparison_manifest', 'policy_profiles',
         'memory_age_daily', 'state_clock_ledger', 'turn_cost_frontier', 'risk_tight_bounds', 'random_refs', 'mc_precision', 'completion_coverage',
         'paired_mde80_deriv', 'state_unknown_days', 'inventory_saturation', 'membership_age_ledger', 'frontier_dose_tilt']
TABLES = ['source_manifest.json', 'engine_contract.md', 'source_resolution.md', 'results/account_manifest.csv', 'results/full/policy_E6l.csv',
          'results/full/policy_additions_E6l.csv', 'registry/hypothesis_lineage_E6l.csv', 'results/hypothesis_outcomes.json', 'results/mask_edit_ledger.csv',
          'results/risk_exposure_daily.parquet', 'results/random_registry.csv', 'results/read_permissions.csv', 'results/coverage.csv',
          'results/completion_receipt.json'] + ['results/full/%s.csv' % t for t in FIXED]
CARD8 = ('source_claim', 'exposure', 'missing_assumption', 'experiment', 'result_query', 'supported_scope', 'alternative_surviving', 'next_design_change')


def tables():
    rows = []
    for f in sorted(glob.glob(L.P('accounts', '*', '*.npz')) + glob.glob(L.P('masks', '*', '*.npz')) + glob.glob(L.P('randoms', '*', '*', '*.npz'))):
        rows.append(dict(file=L.rel(f), sha256=L.sha_file(f), bytes=os.path.getsize(f)))
    L.atomic_write_csv(L.P('results', 'account_manifest.csv'), pd.DataFrame(rows))
    cov = pd.read_csv(L.P('results', 'full', 'completion_coverage.csv'), keep_default_na=False, na_values=[''])
    L.atomic_write_csv(L.P('results', 'coverage.csv'), cov)
    rr = L.read_csv_keep(L.P('registry', 'randoms_E6l.csv'))
    rec = [json.load(open(p, encoding='utf-8')) for p in glob.glob(L.P('task_status', 'run_rand_*.receipt.json'))]
    g = pd.DataFrame([dict(task_id=r['task_id'], n_paths=r.get('n_paths'), path0=r.get('path0')) for r in rec])
    g['mechanism'] = g.task_id.str.extract(r'run_rand_(.+?)_(?:2010|2015|2019|2024)')[0]
    g['segment'] = g.task_id.str.extract(r'_((?:2010|2015|2019|2024)-\d{4})_')[0]
    g['meas'] = g.task_id.str.extract(r'_\d{4}-\d{4}_(.+?)__p')[0]
    agg = g.groupby(['mechanism', 'meas', 'segment']).agg(shards=('task_id', 'count'), paths_total=('n_paths', 'sum')).reset_index()
    wide = agg.pivot_table(index=['mechanism', 'meas'], columns='segment', values='paths_total').reset_index()
    wide.columns = [c if c in ('mechanism', 'meas') else 'paths_%s' % c for c in wide.columns]
    out = rr.merge(wide, on=['mechanism', 'meas'], how='left')
    out['generator'] = 'splitmix64x2-counter(key^block*C1^ticker*C2)>>11 * 2^-53; key=blake2b-64(canonical_json)'
    L.atomic_write_csv(L.P('results', 'random_registry.csv'), out)
    rp = []
    for p in sorted(glob.glob(L.P('task_status', '*.receipt.json'))):
        r = json.load(open(p, encoding='utf-8'))
        if r['task_id'].startswith(('stats_', 'cmpstats_', 'report', 'policy_', 'bootstrap', 'state_clock', 'shadow_risk', 'continuous', 'fixed_tables',
                                    'memory_age', 'mde80', 'record_b', 'stage_a', 'seal_')):
            rp.append(dict(reader=r['task_id'], written_at=r['written_at'], status=r['status']))
    L.atomic_write_csv(L.P('results', 'read_permissions.csv'), pd.DataFrame(rp).sort_values('written_at'))
    mf = [pd.read_csv(f, keep_default_na=False, na_values=['']) for f in glob.glob(L.P('results', 'stage_a', 'mask_facts_*_E6l.csv'))]
    if mf:
        L.atomic_write_csv(L.P('results', 'mask_edit_ledger.csv'), pd.concat(mf, ignore_index=True))
    D = L.read_csv_keep(L.P('registry', 'descriptors_E6l.csv'))
    fixed = set(D[(D.primary72.astype(str) == 'True') | (D.dose72.astype(str) == 'True') | (D.family == 'PARENT')].target_id)
    parts = []
    for s in L.SEGMENTS:
        for f in glob.glob(L.P('accounts', s, '*.npz')):
            if os.path.basename(f).startswith('weights_'):
                continue
            z = L.npz(f)
            for j, tid in enumerate(map(str, z['targets'])):
                if tid in fixed:
                    df = pd.DataFrame({k[2:]: z[k][j] for k in z if k.startswith('t_')})
                    df['date'] = z['dates']
                    df['target_id'] = tid
                    df['segment'] = s
                    parts.append(df)
    if parts:
        outp = L.P('results', 'risk_exposure_daily.parquet')
        tmp = outp + '.tmp.%d' % os.getpid()
        pd.concat(parts, ignore_index=True).to_parquet(tmp, index=False)
        os.replace(tmp, outp)
    # 登记 query 的表路径（registry/query_registry_E6l.csv 的 table 列 = results/full/E6L_Qxx_x.csv）：REPORT 生成器写在 results/full/query_tables/，
    # 此处按登记路径逐字节另存一份并写映射（登记文件不改）
    Qy = L.read_csv_keep(L.P('registry', 'query_registry_E6l.csv'))
    qp = []
    for r in Qy.itertuples():
        src = L.P('results', 'full', 'query_tables', '%s.csv' % r.query_id.replace('-', '_'))
        dst = L.P(*r.table.split('/'))
        if os.path.exists(src):
            tmp = dst + '.tmp.%d' % os.getpid()
            shutil.copyfile(src, tmp)
            os.replace(tmp, dst)
            qp.append(dict(query_id=r.query_id, registered_table=r.table, source=L.rel(src), sha256=L.sha_file(dst), same_as_source=L.sha_file(dst) == L.sha_file(src)))
        else:
            qp.append(dict(query_id=r.query_id, registered_table=r.table, source='MISSING', sha256='UNDEFINED', same_as_source=False))
    L.atomic_write_csv(L.P('results', 'query_table_paths.csv'), pd.DataFrame(qp))
    L.write_receipt(L.next_rerun('deliver_tables'), [L.P('results', x) for x in ('account_manifest.csv', 'coverage.csv', 'random_registry.csv', 'read_permissions.csv',
                                                                               'query_table_paths.csv')], 'SUCCEEDED')
    print('tables done', flush=True)


def hypotheses():
    txt = json.load(open(L.P('results', 'hypothesis_text_input_E6l.json'), encoding='utf-8'))
    cards = L.read_csv_keep(L.P('registry', 'cards_E6l.csv'))
    out = []
    for c in cards.itertuples():
        t = txt.get(c.card, {})
        miss = [k for k in CARD8 if not t.get(k)]
        if miss:
            raise RuntimeError('%s 八字段缺 %s' % (c.card, miss))
        out.append(dict(card=c.card, plan_line=int(c.plan_line), title=c.title, queries=c.queries.split('|'), **{k: t[k] for k in CARD8},
                        category=t.get('category', 'UNDEFINED')))
    L.atomic_write_json(L.P('results', 'hypothesis_outcomes.json'), out)
    L.write_receipt(L.next_rerun('deliver_hypotheses'), [L.P('results', 'hypothesis_outcomes.json')], 'SUCCEEDED', cards=len(out))


def review():
    lines = ['# E6l REVIEW_input（执行端交付清单；全部路径相对结果目录 `results/20260930_1141_E6l_time_memory_stage/`）', '',
             '用途：决策端 V / D / REVIEW 的输入清单。REPORT 交付即冻结；补充另起 supplement。读法要点见 `reports/E6l_REVIEW_input_notes.md`（执行端读完结果后写）。', '']
    groups = [('REPORT 与交付文档', ['reports/' + r for r in REPORTS] + ['reports/E6l_REVIEW_input_notes.md']), ('机器表与固定表', TABLES),
              ('登记 / 授权 / 封存', sorted(L.rel(p) for p in glob.glob(L.P('registration', '*')) if os.path.isfile(p))),
              ('registry', sorted(L.rel(p) for p in glob.glob(L.P('registry', '*.csv')))),
              ('Stage 0', sorted(L.rel(p) for p in glob.glob(L.P('stage0', '**', '*.csv'), recursive=True) + glob.glob(L.P('stage0', '**', '*.json'), recursive=True))),
              ('Stage A', sorted(L.rel(p) for p in glob.glob(L.P('results', 'stage_a', '*.csv')))),
              ('结果与诊断', sorted(L.rel(p) for p in glob.glob(L.P('results', 'deriv', '*.csv')) + glob.glob(L.P('results', 'full', '*.csv'))
                                   + glob.glob(L.P('results', 'full', '*', '*.csv')) + glob.glob(L.P('diagnostics', '**', '*.csv'), recursive=True))),
              ('代码（47 code/project_core）', sorted('code/' + os.path.basename(p) for p in glob.glob(os.path.join(L.CODE, 'e6l_*')))),
              ('输入副本', sorted(L.rel(p) for p in glob.glob(L.P('*.md'))))]
    for gname, paths in groups:
        lines.append('## %s' % gname)
        for p in paths:
            full = os.path.join(L.CODE, p[5:]) if p.startswith('code/') else L.P(p)
            if p == 'reports/E6l_REVIEW_input.md':
                lines.append('- `%s`（本文件）' % p)
            elif p in ('results/completion_receipt.json', 'reports/E6l_MIRROR.md5'):
                lines.append('- `%s`（本清单之后写入：闭包门 / 三处镜像）' % p)
            elif os.path.exists(full):
                lines.append('- `%s`（%s）' % (p, L.sha_file(full)[:16]))
            else:
                lines.append('- `%s`（缺）' % p)
        lines.append('')
    q = json.load(open(L.P('reports', 'query_registry_E6l.json'), encoding='utf-8')) if os.path.exists(L.P('reports', 'query_registry_E6l.json')) else {}
    lines.append('## query_id 登记（%d 个；跨文件唯一）' % len(q))
    lines += ['- %s → %s' % (k, v['file']) for k, v in sorted(q.items())]
    L.atomic_write_text(L.P('reports', 'E6l_REVIEW_input.md'), '\n'.join(lines) + '\n')
    L.write_receipt(L.next_rerun('deliver_review_input'), [L.P('reports', 'E6l_REVIEW_input.md')], 'SUCCEEDED')


def gate():
    import e6l_report as RP
    import e6l_seal as SEAL
    rows = []

    def chk(what, ok, detail=''):
        rows.append(dict(check=what, status='PASS' if ok else 'FAIL', detail=L.txt(detail)[:300]))
    run = subprocess.run(['bash', '-c', 'ps -eo args | grep -c "[e]6l_run_\\|[e]6l_stats\\|[e]6l_cmpstats\\|[e]6l_bootstrap"'], capture_output=True, text=True).stdout.strip()
    chk('无运行中 E6l 作业（按命令行）', run == '0', run)
    st = {}
    names = set()
    for p in glob.glob(L.P('task_status', '*.receipt.json')):
        r = json.load(open(p, encoding='utf-8'))
        st[r['task_id']] = r['status']
        names.add(re.sub(r'_rerun\d*$', '', r['task_id']))
    bad = []
    for b in sorted(names):
        ch = L.rerun_chain(b)
        last = json.load(open(L._receipt_path(ch[-1]), encoding='utf-8'))['status'] if ch else 'MISSING'
        if last != 'SUCCEEDED':
            bad.append(b)
    chk('回执链全部以 SUCCEEDED 结束（FAILED 由后继 _rerun 覆盖；旧回执不删）', not bad, '%d 条链；未覆盖 %s' % (len(names), bad[:5]))
    for pkg in ('deriv', 'post'):
        ok, b = SEAL.verify(pkg)
        chk('seal_%s 核对' % pkg, ok, b[:3])
    for r in REPORTS:
        p = L.P('reports', r)
        if not os.path.exists(p):
            chk('交付文档存在 %s' % r, False)
            continue
        t = open(p, encoding='utf-8').read()
        hits = [w for w in RP.FORBIDDEN if w in t] if r.startswith('E6l_REPORT') else []
        leaks = [x for x in RP.LEAK_PATTERNS if re.search(x, t, flags=re.I)]
        chk('文档扫描 %s（判词 / 主机 / 账号 / 家目录 / 连接串）' % r, not hits and not leaks, '%s %s' % (hits, leaks))
    q = json.load(open(L.P('reports', 'query_registry_E6l.json'), encoding='utf-8'))
    Qy = L.read_csv_keep(L.P('registry', 'query_registry_E6l.csv'))
    chk('登记 query 每个都有真实表（cards）', set(Qy.query_id) <= set(q), sorted(set(Qy.query_id) - set(q))[:5])
    chk('query_id 唯一（登记表天然唯一；逐文件映射）', len(q) == len(set(q)), len(q))
    qtp = pd.read_csv(L.P('results', 'query_table_paths.csv'), keep_default_na=False, na_values=['']) if os.path.exists(L.P('results', 'query_table_paths.csv')) else pd.DataFrame()
    miss_q = [t for t in Qy.table if not os.path.exists(L.P(*t.split('/')))]
    chk('登记 query 表路径逐项存在且与 REPORT 查询表同字节（registry table 列）', len(qtp) == len(Qy) and not miss_q and bool(qtp.same_as_source.astype(str).eq('True').all()),
        miss_q[:5])
    cov = pd.read_csv(L.P('results', 'coverage.csv'), keep_default_na=False, na_values=[''])
    chk('登记对象全有账户（每段 34,120 + 附属 + 随机）', bool((cov.registered == cov.computed).all()), cov[cov.registered != cov.computed].head(3).to_dict('records'))
    miss = [t for t in TABLES if not os.path.exists(L.P(t)) and t != 'results/completion_receipt.json']
    chk('固定输出（plan §13.4 十五张 + brief §9 五张）与机器表逐项存在', not miss, miss)
    user, host = __import__('getpass').getuser(), __import__('socket').gethostname()
    leak = []
    for f in glob.glob(L.P('reports', '*')) + glob.glob(L.P('results', '**', '*.csv'), recursive=True) + glob.glob(L.P('registration', '*.json')):
        if os.path.isfile(f) and os.path.getsize(f) < 200 * 2 ** 20:
            t = open(f, encoding='utf-8', errors='replace').read()
            if user in t or host in t:
                leak.append(L.rel(f))
    chk('交付件无本机账号名 / 主机名（运行时比对，不落盘）', not leak, leak[:3])
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=L.CODE, capture_output=True, text=True).stdout.strip()
    chk('HEAD 未变（白名单提交之前）', head.startswith('ec91def'), head[:7])
    ok = all(r['status'] == 'PASS' for r in rows)
    rec = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), all_pass=ok, checks=rows, receipts_counted_before='本闭包门写入之前')
    L.atomic_write_json(L.P('results', 'completion_receipt.json'), rec)
    print(pd.DataFrame(rows).to_string(max_colwidth=100), flush=True)
    return 0 if ok else 2


def mirror(local_json):
    loc = json.load(open(local_json, encoding='utf-8'))['files'] if local_json and os.path.exists(local_json) else {}
    eb = os.path.join(L.CODE, 'exec_briefs')
    lines = ['# E6l_MIRROR.md5（md5  sha256  位置  文件）']
    for r in REPORTS + ['E6l_REVIEW_input_notes.md']:
        src = L.P('reports', r)
        if not os.path.exists(src):
            continue
        dst = os.path.join(eb, r)
        shutil.copy2(src, dst)
        b = open(src, 'rb').read()
        lines.append('%s  %s  RD  reports/%s' % (hashlib.md5(b).hexdigest(), hashlib.sha256(b).hexdigest(), r))
        b2 = open(dst, 'rb').read()
        lines.append('%s  %s  EB47  exec_briefs/%s' % (hashlib.md5(b2).hexdigest(), hashlib.sha256(b2).hexdigest(), r))
        if r in loc:
            lines.append('%s  %s  EBLOCAL  exec_briefs/%s' % (loc[r]['md5'], loc[r]['sha256'], r))
    L.atomic_write_text(L.P('reports', 'E6l_MIRROR.md5'), '\n'.join(lines) + '\n')
    shutil.copy2(L.P('reports', 'E6l_MIRROR.md5'), os.path.join(eb, 'E6l_MIRROR.md5'))
    print('mirror %d 行' % (len(lines) - 1), flush=True)


if __name__ == '__main__':
    a = sys.argv
    if '--tables' in a:
        tables()
    if '--hypotheses' in a:
        hypotheses()
    if '--review' in a:
        review()
    if '--gate' in a:
        sys.exit(gate())
    if '--mirror' in a:
        mirror(a[a.index('--mirror') + 1] if len(a) > a.index('--mirror') + 1 else None)
