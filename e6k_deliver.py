# -*- coding: utf-8 -*-
"""E6k 交付（brief W17 / §9；plan §13.5；附录 D-6 / D-7 / E；E6j e6j_deliver 同式）。
  --tables      机器表：results/account_manifest.csv（全部账户文件 sha / 描述符数）、results/coverage.csv（登记 vs 已算，逐段逐块）、
                results/read_permissions.csv（读数程序 × 读取时刻 × 所依封存版本）、results/random_registry.csv（随机登记 + 回执生成器 + 实际路径数）、
                results/risk_exposure_daily.parquet（固定清单目标级逐日暴露）、results/layer_transplants.csv（LX 四账户）、results/mask_edit_ledger.csv（掩码事实全段）
  --hypotheses  results/hypothesis_outcomes.json：18 卡（PLAN_COPY 行号 + query_id + 执行端读完结果后写的八字段；文字来自 results/hypothesis_text_input_E6k.json）
  --review      reports/E6k_REVIEW_input.md：全部 REPORT / 表 / 账本 / 登记 / 授权 / 状态 / 代码 / 原假设文本的路径与 sha256
  --gate        闭包门：无运行中 E6k 作业；回执全 SUCCEEDED（FAILED 有 _rerun）；seal_deriv / seal_post 核对；报告扫描；query_id 唯一；
                登记对象全有账户（每段 39,142 + 附属）；plan §13.5 固定输出清单逐项存在 → results/completion_receipt.json
  --mirror      E6k_MIRROR.md5：交付文档三处（结果目录 / 47 exec_briefs / 本地由工作站算后提供）md5 + sha256
不写判词、不写共享 memory。"""
import e6k_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time
import shutil
import subprocess

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_seal as SEAL

REPORTS = ['E6k_REPORT_R0.md', 'E6k_REPORT_part1.md', 'E6k_REPORT_part2.md', 'E6k_REPORT_part3.md', 'E6k_REPORT_mechanisms.md', 'E6k_REPORT_carried.md', 'E6k_REPORT_cards.md',
           'E6k_REVIEW_input.md', 'E6k_lessons_delta.md', 'E6k_limit_register.md', 'E6k_record_B_draft.md', 'E6k_routing_review_A1_auto.md']
TABLES = ['source_manifest.json', 'results/account_manifest.csv', 'results/full/policy_E6k.csv', 'registry/hypothesis_lineage_E6k.csv',
          'results/hypothesis_outcomes.json', 'results/mask_edit_ledger.csv', 'results/risk_exposure_daily.parquet', 'results/layer_transplants.csv',
          'results/random_registry.csv', 'results/read_permissions.csv', 'results/coverage.csv', 'results/completion_receipt.json']
CARD8 = ('source_claim', 'exposure', 'missing_assumption', 'experiment', 'result_query', 'supported_scope', 'alternative_surviving', 'next_design_change')


def tables():
    os.makedirs(K.P('results'), exist_ok=True)
    rows = []
    for f in sorted(glob.glob(K.P('accounts', '*', '*.npz')) + glob.glob(K.P('randoms', '*', '*', '*.npz'))):
        z = np.load(f, allow_pickle=False)
        rows.append(dict(file=K.rel(f), sha256=K.sha_file(f), n_desc=len(z['desc']) if 'desc' in z.files else np.nan, bytes=os.path.getsize(f)))
    K.atomic_write_csv(K.P('results', 'account_manifest.csv'), pd.DataFrame(rows))
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    A = pd.read_csv(K.P('registry', 'accessory_E6k.csv'))
    cov = []
    for s in K.SEGMENTS:
        have = set()
        for f in glob.glob(K.P('accounts', s, '*.npz')):
            if not os.path.basename(f).startswith('weights_'):
                have |= set(map(str, K.npz(f)['desc']))
        for b in ('CORE', 'OWN', 'REPAIR', 'LAYER', 'BAND', 'BAND_COMPARATOR', 'HG_ONLY', 'TREFIT', 'POST2', 'RAR', 'PARENT', 'SM_ANCHOR'):
            ids = set(D[D.blocks.str.split('|').apply(lambda x: b in x)].desc_id)
            cov.append(dict(segment=s, block=b, registered=len(ids), computed=len(ids & have)))
        for k, g in A.groupby('kind'):
            cov.append(dict(segment=s, block=k, registered=len(g), computed=len(set(g.acc_id) & have)))
    K.atomic_write_csv(K.P('results', 'coverage.csv'), pd.DataFrame(cov))
    rr = pd.read_csv(K.P('registry', 'randoms_E6k.csv'))
    rec = [json.load(open(p, encoding='utf-8')) for p in glob.glob(K.P('task_status', 'run_rand_*.receipt.json'))]
    gen = pd.DataFrame([dict(task_id=r['task_id'], generator=r.get('generator'), n_paths=r.get('n_paths')) for r in rec])
    K.atomic_write_csv(K.P('results', 'random_registry.csv'), rr.merge(gen.assign(mechanism=gen.task_id.str.extract(r'run_rand_(.+?)_(?:2010|2015|2019|2024)')[0])
                                                                       .groupby('mechanism').agg(shards=('task_id', 'count'), paths_total=('n_paths', 'sum'),
                                                                                                 generator=('generator', 'first')).reset_index(),
                                                                       on='mechanism', how='left'))
    rp = []
    for p in sorted(glob.glob(K.P('task_status', '*.receipt.json'))):
        r = json.load(open(p, encoding='utf-8'))
        if r['task_id'].startswith(('stats_', 'report_', 'policy_', 'bootstrap', 'mechanisms_', 'risk_', 'shadow_', 'control_dist', 'closure_', 'record_b')):
            rp.append(dict(reader=r['task_id'], written_at=r['written_at'], status=r['status']))
    seals = []
    for pkg in ('deriv', 'post'):
        for v in SEAL.versions(pkg):
            m = json.load(open(SEAL.seal_path(pkg, v), encoding='utf-8'))
            seals.append(dict(reader='SEAL_%s_v%d' % (pkg, v), written_at=m['written_at'], status='SEALED'))
    K.atomic_write_csv(K.P('results', 'read_permissions.csv'), pd.DataFrame(seals + rp).sort_values('written_at'))
    mf = [pd.read_csv(f) for f in glob.glob(K.P('registry', 'mask_facts_*_E6k.csv'))]
    if mf:
        K.atomic_write_csv(K.P('results', 'mask_edit_ledger.csv'), pd.concat(mf, ignore_index=True))
    P = pd.read_csv(K.P('results', 'full', 'policy_E6k.csv')) if os.path.exists(K.P('results', 'full', 'policy_E6k.csv')) else None
    if P is not None:
        lx = P[P.family == 'LX'][['desc_id', 'meas', 'mother', 'op', 'alpha', 'H', 'FULL', 'G4'] + [c for c in P.columns if c.startswith('D_') and 'vs' not in c]]
        K.atomic_write_csv(K.P('results', 'layer_transplants.csv'), lx)
    fixed = set(D[D.primary144 | D.c1_hi | D.sm_anchor | (D.op == 'PARENT')].target_id)
    parts = []
    for s in K.SEGMENTS:
        for f in glob.glob(K.P('accounts', s, '*.npz')):
            if os.path.basename(f).startswith('weights_'):
                continue
            z = K.npz(f)
            for j, tid in enumerate(map(str, z['targets'])):
                if tid in fixed:
                    df = pd.DataFrame({k[2:]: z[k][j] for k in z.files if k.startswith('t_')})
                    df['date'] = z['dates']
                    df['target_id'] = tid
                    df['segment'] = s
                    parts.append(df)
    if parts:
        out = K.P('results', 'risk_exposure_daily.parquet')
        tmp = out + '.tmp.%d' % os.getpid()
        pd.concat(parts, ignore_index=True).to_parquet(tmp, index=False)
        os.replace(tmp, out)
    K.write_receipt('deliver_tables', [K.P('results', x) for x in ('account_manifest.csv', 'coverage.csv', 'random_registry.csv', 'read_permissions.csv')],
                    'SUCCEEDED')
    print('tables done', flush=True)


def hypotheses():
    txt = json.load(open(K.P('results', 'hypothesis_text_input_E6k.json'), encoding='utf-8'))
    cards = pd.read_csv(K.P('registry', 'cards_E6k.csv'))
    out = []
    for c in cards.itertuples():
        t = txt.get(c.card, {})
        miss = [k for k in CARD8 if not t.get(k)]
        if miss:
            raise RuntimeError('%s 八字段缺 %s' % (c.card, miss))
        out.append(dict(card=c.card, plan_line=int(c.plan_line), title=c.title, queries=c.queries.split('|'), **{k: t[k] for k in CARD8},
                        category=t.get('category', '')))
    K.atomic_write_json(K.P('results', 'hypothesis_outcomes.json'), out)
    K.write_receipt('deliver_hypotheses', [K.P('results', 'hypothesis_outcomes.json')], 'SUCCEEDED', cards=len(out))


def review():
    lines = ['# E6k REVIEW_input（执行端交付清单；全部路径相对结果目录 `results/20260928_2325_E6k_k_binding_stage/`）', '',
             '用途：决策端 V / D / REVIEW 的输入清单。REPORT 交付即冻结；补充另起 supplement。', '',
             '读法注（part1 §6 十八卡机械计数表）：Q16 / Q18 的"1 个对象、0 行推导段数"是卡级占位对象（`E6J_638_OBJECTS` 在 part2 衰减场景与 '
             'E6j 原表复现里读；`ALL_DESCRIPTORS` 在 `registry/hypothesis_lineage_E6k.csv` 与闭包门清单里读），不是缺算；'
             'Q14 的对象数与推导段行数之差是 PARENT 源锚行（相对自身的差不定义）。', '']
    groups = [('REPORT', ['reports/' + r for r in REPORTS]), ('机器表', TABLES),
              ('登记 / 授权 / 封存', sorted(K.rel(p) for p in glob.glob(K.P('registration', '*')))),
              ('registry', sorted(K.rel(p) for p in glob.glob(K.P('registry', '*.csv')))),
              ('Stage 0', sorted(K.rel(p) for p in glob.glob(K.P('stage0', '**', '*.csv'), recursive=True))),
              ('结果与诊断', sorted(K.rel(p) for p in glob.glob(K.P('results', '**', '*.csv'), recursive=True) + glob.glob(K.P('diagnostics', '**', '*.csv'), recursive=True))),
              ('代码（47 code/project_core）', sorted('code/' + os.path.basename(p) for p in glob.glob(os.path.join(K.CODE, 'e6k_*')))),
              ('输入副本', sorted(K.rel(p) for p in glob.glob(K.P('*.md'))))]
    for g, paths in groups:
        lines.append('## %s' % g)
        for p in paths:
            full = os.path.join(K.CODE, p[5:]) if p.startswith('code/') else K.P(p)
            if p == 'reports/E6k_REVIEW_input.md':
                lines.append('- `%s`（本文件）' % p)
            elif p in ('results/completion_receipt.json', 'reports/E6k_MIRROR.md5'):
                lines.append('- `%s`（本清单之后写入：闭包门 / 三处镜像）' % p)
            elif os.path.exists(full):
                lines.append('- `%s`（%s）' % (p, K.sha_file(full)[:16]))
            else:
                lines.append('- `%s`（缺）' % p)
        lines.append('')
    q = json.load(open(K.P('reports', 'query_registry_E6k.json'), encoding='utf-8')) if os.path.exists(K.P('reports', 'query_registry_E6k.json')) else {}
    lines.append('## query_id 登记（%d 个；跨文件唯一）' % len(q))
    lines += ['- %s → %s' % (k, v['file']) for k, v in sorted(q.items())]
    K.atomic_write_text(K.P('reports', 'E6k_REVIEW_input.md'), '\n'.join(lines) + '\n')
    K.write_receipt('deliver_review_input', [K.P('reports', 'E6k_REVIEW_input.md')], 'SUCCEEDED')


def gate():
    import e6k_report as RP
    rows = []

    def chk(what, ok, detail=''):
        rows.append(dict(check=what, status='PASS' if ok else 'FAIL', detail=str(detail)[:300]))
    run = subprocess.run(['bash', '-c', 'ps -eo args | grep -c "[e]6k_run_"'], capture_output=True, text=True).stdout.strip()
    chk('无运行中 E6k 作业', run == '0', run)
    st = {}
    for p in glob.glob(K.P('task_status', '*.receipt.json')):
        r = json.load(open(p, encoding='utf-8'))
        st[r['task_id']] = r['status']
    for k in list(st):
        if k.endswith('_rerun') and st[k] == 'SUCCEEDED':
            st[k[:-6]] = 'SUCCEEDED'
    bad = [k for k, v in st.items() if v != 'SUCCEEDED' and not k.endswith('_rerun')]
    chk('回执全 SUCCEEDED（FAILED 有同名 _rerun 覆盖；截至本门之前的全部回执）', not bad, '%d 个回执；未覆盖 %s' % (len(st), bad[:5]))
    for pkg in ('deriv', 'post'):
        ok, b = SEAL.verify(pkg)
        chk('seal_%s 核对' % pkg, ok, b[:3])
    for r in REPORTS:
        p = K.P('reports', r)
        if not os.path.exists(p):
            chk('报告存在 %s' % r, False)
            continue
        t = open(p, encoding='utf-8').read()
        hits = [w for w in RP.FORBIDDEN if w in t]
        leaks = [x for x in RP.LEAK_PATTERNS if re.search(x, t, flags=re.I)]
        chk('报告扫描 %s（禁用词 / 主机 / 账号 / 家目录 / 连接串）' % r, not hits and not leaks, '%s %s' % (hits, leaks))
    q = json.load(open(K.P('reports', 'query_registry_E6k.json'), encoding='utf-8'))
    chk('query_id 唯一（登记表天然唯一；逐文件映射）', len(q) == len(set(q)), len(q))
    cov = pd.read_csv(K.P('results', 'coverage.csv'))
    chk('登记对象全有账户（每段 39,142 + 附属）', bool((cov.registered == cov.computed).all()), cov[cov.registered != cov.computed].head(3).to_dict('records'))
    miss = [t for t in TABLES if not os.path.exists(K.P(t)) and t != 'results/completion_receipt.json']
    chk('plan §13.5 固定输出清单逐项存在（机器表）', not miss, miss)
    ok = all(r['status'] == 'PASS' for r in rows)
    rec = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), all_pass=ok, checks=rows, receipts_counted_before='本闭包门写入之前')
    K.atomic_write_json(K.P('results', 'completion_receipt.json'), rec)
    print(pd.DataFrame(rows).to_string(max_colwidth=100), flush=True)
    return 0 if ok else 2


def mirror(local_json):
    """交付文档复制到 47 exec_briefs，并写 E6k_MIRROR.md5（结果目录 / 47 exec_briefs / 本地（工作站现算 json））。"""
    loc = json.load(open(local_json, encoding='utf-8'))['files'] if local_json and os.path.exists(local_json) else {}
    eb = os.path.join(K.CODE, 'exec_briefs')
    lines = ['# E6k_MIRROR.md5（md5  sha256  位置  文件）']
    for r in REPORTS:
        src = K.P('reports', r)
        if not os.path.exists(src):
            continue
        dst = os.path.join(eb, r)
        shutil.copy2(src, dst)
        import hashlib
        b = open(src, 'rb').read()
        md5, sha = hashlib.md5(b).hexdigest(), hashlib.sha256(b).hexdigest()
        lines.append('%s  %s  RD  reports/%s' % (md5, sha, r))
        b2 = open(dst, 'rb').read()
        lines.append('%s  %s  EB47  exec_briefs/%s' % (hashlib.md5(b2).hexdigest(), hashlib.sha256(b2).hexdigest(), r))
        if r in loc:
            lines.append('%s  %s  EBLOCAL  exec_briefs/%s' % (loc[r]['md5'], loc[r]['sha256'], r))
    K.atomic_write_text(K.P('reports', 'E6k_MIRROR.md5'), '\n'.join(lines) + '\n')
    shutil.copy2(K.P('reports', 'E6k_MIRROR.md5'), os.path.join(eb, 'E6k_MIRROR.md5'))
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
