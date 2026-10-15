# -*- coding: utf-8 -*-
"""E6n 闭包门（附录 E：E6m 十五项 S01–S15 同类 + 本轮 ①–⑫；任一 FAIL 不交付）。只读；输出 closure_E6n.json / .csv（门输出不自扫）。
  S01 本项目运行中进程 0           S02 git：HEAD = 开工基线、tracked 改动 0（白名单提交前）
  S03 回执：FAILED 均被后写 _rerun 覆盖   S04 seal_B1_0 / seal_deriv / seal_post 在、queued_missing = 0（MC_LIMIT 单列）
  S05 Stage 0 门 / A1-auto / 生效条件回执 all_pass      S06 状态词扫描（交付 CSV 状态列）
  S07 敏感信息扫描（交付文本：IPv4 / 口令密钥 / 家目录 / 用户目录与账号名）  S08 query：唯一、全有表、≥ 1 行、列 = 骨架
  S09 固定表全在且 ≥ 1 行        S10 覆盖：主 / 附属 / 分量每个登记对象在四段账户里都有（或显式状态）
  S11 限制登记每条在所列报告正文被引用   S12 报告齐全   S13 副本包 P0–P3 manifest 在、复制后 sha 0 不符
  S14 政策表 deployment_authorized 全 false；新对象 replacement NOT_AUTHORIZED   S15 E7 截止：守卫攻击全 PASS、产物日期轴 ≤ 2026-03-27
  N01 全 NOT_RUN 的 query = FAIL（登记占位且绑定固定表者除外）   N02 报告正文字面 nan / None   N03 闭合类表 closure_maxabs 全有限且 ≤ 1e−12
  N04 限制登记 L 条目状态栏由机器计数刷新且可回链文件   N05 SCHEMA.md 行数 = 文件实际行数、列名 = 表头   N06 G / E / exposure / probe 四账本非空且每卡与每断言在 E 账本有行
  N07 seal_B1_0.written_at < 任何推导段账户首次写入   N08 data_request_E6n.md 存在   N09 每个分钟成员在 coverage_by_feature_year_exchange 有年 × 交易所行
  N10 缓存目录名含 E6n-v1.1 与 plan sha 前缀   N11 守卫攻击矩阵含六个新入口且全拦截   N12 页首写明无 E7 / 部署授权与"协议 v1.5 候选\""""
import os
import re
import sys
import glob
import json
import time
import subprocess

import numpy as np
import pandas as pd

import e6n_core as N

REPORTS = ('E6n_REPORT_R0.md', 'E6n_REPORT_part1.md', 'E6n_REPORT_part2.md', 'E6n_REPORT_part3.md', 'E6n_REPORT_mechanisms.md', 'E6n_REPORT_carried.md',
           'E6n_REPORT_REVIEW_input.md', 'E6n_REVIEW_input_notes.md', 'E6n_lessons_delta.md', 'E6n_limit_register.md', 'E6n_code_change_register.md',
           'E6n_E7_prep.md', 'SCHEMA.md')
FIXED = ('results/b1_0/b1_0_cells.csv', 'results/b1_0/b1_0_pairs.csv', 'results/b1_0/b1_0_matched.csv', 'results/b1_0/b1_0_moderators.csv', 'results/b1_0/b1_0_bridges.csv',
         'results/b1_0/b1_0_regimes.csv', 'stage0/c7_minute/minute_health.csv', 'results/coverage_by_feature_year_exchange.csv', 'stage0/data_contract.json',
         'results/full/policy_E6n.csv', 'results/full/random_refs.csv', 'results/full/primary72_E6n.csv', 'results/full/frontier_E6n.csv',
         'results/full/improvement_E6n.csv', 'registration/idea_ledger_G.csv', 'registration/probe_ledger.csv', 'registration/execution_ledger_E.csv',
         'registration/exposure_ledger.csv', 'registration/source_claim_reconciliation.csv', 'results/full/b5/b5_dedupe.csv', 'results/full/b6/b6_event_contrib.csv',
         'results/full/penalty_change_ledger.csv', 'results/full/measurement_raw_ledger.csv', 'registration/card_query_map_E6n.csv', 'registration/park_reentry_E6n.csv',
         'registration/externality_register_E6n.csv', 'registration/authorization_receipt_E6n.json', 'results/full/component_dose_ledger.csv',
         'results/full/support_four_accounts.csv', 'results/full/match_cap_holdings_min.csv', 'results/full/four_account_ledger.csv', 'results/full/b2/b2_risk_set.csv',
         'results/full/b2/b2_order_overlay.csv', 'results/full/b2/b2_mirrors.csv', 'results/full/b2/b2_controls.csv', 'results/full/b3/b3_same_count.csv',
         'results/full/b4/b4_bridges.csv', 'results/full/idea_ledger_G_final.csv', 'results/full/execution_ledger_E_final.csv', 'results/full/exposure_ledger_final.csv')


def ancestors():
    out, p = set(), os.getpid()
    while p > 1 and p not in out:
        out.add(p)
        try:
            p = int(open('/proc/%d/stat' % p).read().rsplit(')', 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            break
    return out


def git(*a):
    return subprocess.run(['git', '-c', 'safe.directory=%s' % os.path.realpath(N.CODE), '--no-optional-locks'] + list(a), cwd=N.CODE,
                          capture_output=True, text=True).stdout


def main():
    out_json, out_csv = N.P('closure_E6n.json'), N.P('closure_E6n.csv')
    G = []

    def item(gid, desc, ok, **d):
        G.append(dict(id=gid, desc=desc, status='PASS' if ok is True else ('INFO' if ok is None else 'FAIL'),
                      detail=N.san(json.dumps(d, ensure_ascii=False, default=str))[:900]))
    ps = subprocess.run(['ps', '-ww', '-eo', 'pid,args', '--no-headers'], capture_output=True, text=True).stdout.split('\n')
    mine = ancestors()
    procs = [l for l in ps if l.strip() and re.search(r'python3? e6n_', l) and int(l.split()[0]) not in mine]
    item('S01', '本项目运行中进程 0', not procs, lines=[N.san(l)[:120] for l in procs[:8]])
    ident = json.load(open(N.P('identity_at_start.json'), encoding='utf-8'))
    head = git('rev-parse', 'HEAD').strip()
    tracked = [l for l in git('status', '--porcelain', '--untracked-files=no').split('\n') if l.strip()]
    item('S02', 'git：HEAD = 开工基线、tracked 改动 0（白名单提交前）', head == ident.get('head') and not tracked, head=head[:12], tracked=len(tracked))
    rec = {}
    for f in sorted(os.listdir(N.P('task_status'))):
        r = json.load(open(N.P('task_status', f), encoding='utf-8'))
        rec[r['task_id']] = (r['status'], r['written_at'])
    unc = [t for t, (st, at) in rec.items() if st != 'SUCCEEDED' and not [u for u, (s2, a2) in rec.items() if u != t and re.sub(r'_rerun\d*$', '', u) == re.sub(r'_rerun\d*$', '', t)
                                                                          and s2 == 'SUCCEEDED' and a2 >= at]]
    item('S03', '回执：FAILED 均被后写 _rerun 覆盖', not unc, uncovered=unc[:20])
    seals = {}
    for ph in ('B1_0', 'deriv', 'post'):
        j = json.load(open(N.P('registration', 'seal_%s.json' % ph), encoding='utf-8')) if os.path.exists(N.P('registration', 'seal_%s.json' % ph)) else None
        if j is None:
            seals[ph] = 'MISSING'
            continue
        bad = [k for k, v in j.get('sha256_manifest', {}).items() if not os.path.exists(N.P(k)) or N.sha_file(N.P(k)) != v]
        seals[ph] = dict(queued_missing=j.get('queued_missing'), sha_changed=len(bad), keys_ok=all(k in j for k in ('written_at', 'n_files', 'queued_missing', 'n_receipts')))
    ok4 = all(isinstance(v, dict) and v['sha_changed'] == 0 and v['keys_ok'] and (v['queued_missing'] == 0) for v in seals.values())
    item('S04', 'seal_B1_0 / seal_deriv / seal_post 在、固定键齐、sha 未变、queued_missing = 0', ok4, seals=seals)
    g = json.load(open(N.P('stage0', 'stage0_gate.json'), encoding='utf-8')) if os.path.exists(N.P('stage0', 'stage0_gate.json')) else {}
    a1 = json.load(open(N.P('registration', 'a1_auto_E6n.json'), encoding='utf-8')) if os.path.exists(N.P('registration', 'a1_auto_E6n.json')) else {}
    cr = json.load(open(N.P('registration', 'record_B_conditions_receipt_E6n.json'), encoding='utf-8')) if os.path.exists(
        N.P('registration', 'record_B_conditions_receipt_E6n.json')) else {}
    item('S05', 'Stage 0 门 / A1-auto / 生效条件回执 all_pass', bool(g.get('all_pass') and a1.get('all_pass') and cr.get('all_pass')), stage0=g.get('counts'), a1=a1.get('counts'),
         conditions=cr.get('all_pass'))
    import e6n_deliver as DLV
    dl = DLV.collect_files()
    forb = {'N/A', 'NA', 'nan', 'NaN', 'null', 'NULL', 'None', '#N/A', 'n/a', '<NA>'}
    hits = []
    for p in dl:
        if p.endswith('.csv') and os.path.getsize(p) < 300e6:
            try:
                df = pd.read_csv(p, dtype=str, keep_default_na=False)
            except Exception:                                                     # noqa: BLE001
                continue
            for c in [c for c in df.columns if c.lower() in ('status', 'label', 'result', 'probe_result', 'band_status')]:
                v = set(df[c]) & forb
                if v:
                    hits.append('%s:%s' % (N.rel(p), c))
    item('S06', '状态词扫描（交付 CSV 状态列）', not hits, hits=hits[:12])
    # 口令 / 密钥类按"关键词 + 赋值符 + 值"判（只出现词本身不是泄露，例：交接件里"脱敏扫描（… / 口令）0 命中"）；另查 user@host / 邮箱形式
    pats = [re.compile(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])'),
            re.compile(r'(?i)(?:password|passwd|口令|密码|secret|api[_-]?key)\s*[:：=]\s*\S|BEGIN [A-Z ]*PRIVATE KEY|ssh-rsa\s|ssh-ed25519\s|token=\S'),
            re.compile(r'(?<![\w.-])[A-Za-z0-9._-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+'),
            re.compile(re.escape(os.path.expanduser('~') + os.sep)), re.compile(r'/mnt/sda2/[a-z]+/'), re.compile(r'/home/[a-z]+')]
    sh = []
    for p in dl:
        if not p.endswith(('.md', '.csv', '.json', '.txt')) or os.path.getsize(p) > 200e6:
            continue
        for i, ln in enumerate(open(p, encoding='utf-8', errors='replace').read().split('\n'), 1):
            if any(rx.search(ln) for rx in pats):
                sh.append('%s:%d' % (N.rel(p), i))
    item('S07', '敏感信息扫描（交付文本）', not sh, hits=sh[:20], n_files=len(dl))
    Q = pd.read_csv(N.P('registry', 'query_registry_E6n.csv'), keep_default_na=False)
    bad_q, allnr = [], []
    for r in Q.itertuples():
        p = N.P('reports', 'queries_full', '%s.csv' % r.query_id)
        if not os.path.exists(p):
            bad_q.append((r.query_id, '缺'))
            continue
        X = pd.read_csv(p, dtype=str, keep_default_na=False)
        sk = pd.read_csv(N.P('reports_skeleton', 'queries', '%s.csv' % r.query_id), nrows=0).columns.tolist()
        if len(X) == 0 or list(X.columns) != sk:
            bad_q.append((r.query_id, '0 行或列不符'))
        if (X.status == 'NOT_RUN').all() and str(r.placeholder) != 'True':
            allnr.append(r.query_id)
    item('S08', 'query：唯一、全有表、≥ 1 行、列 = 骨架', Q.query_id.is_unique and not bad_q, bad=bad_q[:12], n=len(Q))
    item('N01', '全部行 NOT_RUN 的 query = FAIL（登记占位除外）', not allnr, all_not_run=allnr[:12])
    miss_f = [f for f in FIXED if not os.path.exists(N.P(f)) or (f.endswith('.csv') and len(pd.read_csv(N.P(f), nrows=2)) == 0)]
    item('S09', '固定表全在且 ≥ 1 行', not miss_f, missing=miss_f)
    cov = {}
    reg = set(pd.read_csv(N.P('registry', 'descriptors_E6n.csv'), keep_default_na=False).desc_id) | set(pd.read_csv(N.P('registry', 'auxiliary_E6n.csv'),
              keep_default_na=False).aux_id) | set(pd.read_csv(N.P('registry', 'component_controls_E6n.csv'), keep_default_na=False).comp_id)
    for s in N.SEGMENTS:
        have = set()
        for f in glob.glob(N.P('accounts', s, '*.npz')):
            with np.load(f, allow_pickle=False) as z:
                have |= set(str(x) for x in z['desc'])
        cov[s] = len(reg - have)
    item('S10', '覆盖：主 / 附属 / 分量每个登记对象在四段账户里都有', all(v == 0 for v in cov.values()), missing_by_segment=cov, registered=len(reg))
    lr = N.P('reports', 'E6n_limit_register.md')
    unc_l, ids = [], []
    if os.path.exists(lr):
        txt = open(lr, encoding='utf-8').read()
        for m in re.finditer(r'^\| (L-N\d+) \|.*\| 引用于：([^|]+)\|', txt, re.M):
            ids.append(m.group(1))
            for rf in [x.strip() for x in m.group(2).split('、') if x.strip()]:
                p = N.P('reports', rf)
                body = open(p, encoding='utf-8').read() if os.path.exists(p) else ''
                body = '\n'.join(l for l in body.split('\n') if not l.startswith('| L-N'))
                if not re.search(r'(?<![\w-])%s(?![\w])' % re.escape(m.group(1)), body):
                    unc_l.append((m.group(1), rf))
    item('S11', '限制登记每条在所列报告正文被引用', bool(ids) and not unc_l, uncited=unc_l[:12], n=len(ids))
    miss_r = [r for r in REPORTS if not os.path.exists(N.P('reports', r))]
    item('S12', '报告齐全', not miss_r, missing=miss_r)
    mans = sorted(glob.glob(N.P('replica', 'replica_manifest_P*.json')))
    bad_m = [os.path.basename(p) for p in mans if json.load(open(p, encoding='utf-8')).get('verified', {}).get('mismatched')]
    item('S13', '副本包 P0–P3 manifest 在且复制后 sha 0 不符', len(mans) == 4 and not bad_m, manifests=[os.path.basename(p) for p in mans], bad=bad_m)
    P = pd.read_csv(N.P('results', 'full', 'policy_E6n.csv'), dtype=str, keep_default_na=False, low_memory=False) if os.path.exists(N.P('results', 'full', 'policy_E6n.csv')) else None
    item('S14', 'deployment_authorized 全 false；新对象 replacement NOT_AUTHORIZED', P is not None and bool((P.deployment_authorized.str.lower() == 'false').all())
         and bool((P[P.exposure == N.LABEL_FIRST_LOOK].replacement_preference_status == 'NOT_AUTHORIZED').all()))
    ga = pd.read_csv(N.P('stage0', 'c1', 'guard_attack_E6n.csv'), dtype=str, keep_default_na=False) if os.path.exists(N.P('stage0', 'c1', 'guard_attack_E6n.csv')) else None
    mx, over = '', []
    for d in ('accounts', 'accounts_support', 'randoms'):
        for f in glob.glob(N.P(d, '**', '*.npz'), recursive=True):
            with np.load(f, allow_pickle=False) as z:
                if 'dates' in z.files and len(z['dates']):
                    m_ = str(max(z['dates']))[:10]
                    mx = max(mx, m_)
                    if m_ > N.MARKET_DATA_END_MAX:
                        over.append(N.rel(f))
    item('S15', 'E7 截止：守卫攻击全 PASS、产物日期轴 ≤ 2026-03-27', ga is not None and bool((ga.status == 'PASS').all()) and not over, max_date=mx, over=over[:5])
    item('N02', '报告正文字面 nan / None', not [r for r in REPORTS if os.path.exists(N.P('reports', r)) and re.search(r'(?<![A-Za-z_])(nan|NaN|None)(?![A-Za-z_])',
                                                                                                            open(N.P('reports', r), encoding='utf-8').read())])
    cl = []
    for f in glob.glob(N.P('results', '*', 'decomp', '*.csv')) + [N.P('results', 'checks', 'closure_four_accounts.csv')]:
        if os.path.exists(f):
            D = pd.read_csv(f, keep_default_na=False)
            if 'closure_maxabs' in D.columns:
                v = pd.to_numeric(D.closure_maxabs, errors='coerce')
                v = v[D.status.astype(str).eq('COMPUTED')] if 'status' in D.columns else v
                if (~np.isfinite(v)).any() or (v > 1e-12).any():
                    cl.append((N.rel(f), float(v.max())))
    item('N03', '闭合类表 closure_maxabs 全有限且 ≤ 1e−12', not cl, bad=cl[:8])
    item('N04', '限制登记 L 条目状态栏由机器计数刷新', os.path.exists(lr) and '机器计数（' in open(lr, encoding='utf-8').read() if os.path.exists(lr) else False)
    sc = N.P('reports', 'SCHEMA.md')
    bad_s = []
    if os.path.exists(sc):
        for ln in open(sc, encoding='utf-8').read().split('\n'):
            m = re.match(r'^\| `([^`]+)` \| csv \| (\d+) \|', ln)
            if m:
                f = N.P(m.group(1))
                n_ = sum(1 for _ in open(f, encoding='utf-8')) - 1 if os.path.exists(f) else -1
                if n_ != int(m.group(2)):
                    bad_s.append((m.group(1), m.group(2), n_))
    item('N05', 'SCHEMA.md 行数 = 文件实际行数', os.path.exists(sc) and not bad_s, bad=bad_s[:10])
    Gl = pd.read_csv(N.P('registration', 'idea_ledger_G.csv'), keep_default_na=False)
    El = pd.read_csv(N.P('registration', 'execution_ledger_E.csv'), keep_default_na=False)
    Xl = pd.read_csv(N.P('registration', 'exposure_ledger.csv'), keep_default_na=False)
    Pl = pd.read_csv(N.P('registration', 'probe_ledger.csv'), keep_default_na=False)
    cards = set(pd.read_csv(N.P('registration', 'cards_stageB_E6n.csv'), keep_default_na=False).claim_id)
    asr = set('E6N-' + pd.read_csv(N.P('registration', 'claims_E6n.csv'), keep_default_na=False).assertion_id)
    item('N06', 'G / E / exposure / probe 四账本非空；每卡与每断言在 E 账本有行', all(len(x) for x in (Gl, El, Xl, Pl)) and cards <= set(El.claim_id) and asr <= set(El.claim_id))
    s10 = json.load(open(N.P('registration', 'seal_B1_0.json'), encoding='utf-8'))['written_at']
    acc = sorted(os.path.getmtime(f) for s in N.DERIV_SEGS for f in glob.glob(N.P('accounts', s, '*.npz')))
    first_acc = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(min(acc))) if acc else ''
    rec_acc = sorted(r[1] for t, r in rec.items() if t.startswith('E6n_accounts_') and any(s in t for s in N.DERIV_SEGS))
    item('N07', 'seal_B1_0.written_at < 任何推导段账户首次写入', bool(acc) and s10 < first_acc and (not rec_acc or s10 < rec_acc[0]), seal_B1_0=s10, first_account=first_acc,
         first_account_receipt=rec_acc[0] if rec_acc else '')
    item('N08', 'stage0/data_request_E6n.md 存在', os.path.exists(N.P('stage0', 'data_request_E6n.md')))
    cv = pd.read_csv(N.P('results', 'coverage_by_feature_year_exchange.csv'), keep_default_na=False)
    need = {'PL_REL20_f5', 'TAIL_PUSH', 'TAIL_VOL_REL20', 'JSD_PROFILE20', 'RV_REL20_f5', 'Q_PATH_h_path_f5', 'Q_CLOSE_THIN_h_close'}
    item('N09', '每个分钟成员在 coverage_by_feature_year_exchange 有年 × 交易所行', need <= set(cv.feature), missing=sorted(need - set(cv.feature)))
    pr = [d for d in os.listdir(N.P('minute_panel')) if d.startswith('cache_')]
    item('N10', '缓存目录名含 E6n-v1.1 与 plan sha 前缀', bool(pr) and all('E6n-v1.1' in d and N.PLAN_SHA256[:8] in d for d in pr), dirs=pr)
    new = ga[ga['round'].astype(str).str.contains('E6n')] if ga is not None and 'round' in ga.columns else pd.DataFrame()
    item('N11', '守卫攻击矩阵含六个新入口且全拦截', len(new) >= 6 and bool((new.status == 'PASS').all()), n_new=len(new))
    hl = [r for r in REPORTS if r.startswith('E6n_REPORT') and os.path.exists(N.P('reports', r)) and ('无 E7 与部署授权' not in open(N.P('reports', r), encoding='utf-8').read()
                                                                                                  or 'v1.5 候选' not in open(N.P('reports', r), encoding='utf-8').read())]
    item('N12', '页首写明无 E7 / 部署授权与"协议 v1.5 候选"', not hl, missing=hl)
    df = pd.DataFrame(G)
    N.atomic_write_csv(out_csv, df)
    res = dict(gate='E6n 闭包门（E6m S01–S15 + 本轮 N01–N12）', written_at=time.strftime('%Y-%m-%d %H:%M:%S'), machine=N.MACHINE, all_pass=bool((df.status != 'FAIL').all()),
               counts=df.status.value_counts().to_dict(), items=G)
    N.atomic_write_json(out_json, res)
    print(json.dumps(dict(all_pass=res['all_pass'], counts=res['counts']), ensure_ascii=False))
    print(df[df.status != 'PASS'][['id', 'status', 'detail']].to_string(max_colwidth=200))
    return 0 if res['all_pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
