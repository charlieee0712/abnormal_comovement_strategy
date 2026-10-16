# -*- coding: utf-8 -*-
"""E6m 阶段 S 闭包门（附录 D-5；阶段 N 门 e6m_stageN_gate 的扩展）。只读；输出 closure_gate_stageS.json / .csv（门输出不自扫，E6l G10 教训）。
  S01 本项目运行中进程 0（PID + 启动时间 + 命令行）           S02 git：HEAD = 开工基线、tracked 改动 0（白名单提交前）
  S03 回执：阶段 S 生产任务全部 SUCCEEDED 或被后写的同名 _rerun 覆盖（S_dev_* 开发回执不计）
  S04 seal_deriv / seal_post all_ok 且文件 sha 未变           S05 Stage 0 S 门与 A1-auto（S）all_pass；生效条件回执 all_pass
  S06 状态词扫描（A6-3）                                     S07 敏感信息扫描（A6-6：IPv4 / user@host / 口令密钥 / 家目录 / 用户目录与账号名）
  S08 query：query_id 唯一；每个登记 query 都有表且 ≥ 1 行（印出 0 行 = FAIL）；列 = 骨架
  S09 固定输出：carried 表全在、≥ 1 行、列 = 骨架
  S10 覆盖：附属 66,698 行逐行状态无 NOT_RUN / PARTIAL_PATHS / UNDEFINED（允许 LIMIT / NO_NEW_CONTENT_TO_PERMUTE / RANDOM_NOT_SCHEDULED；DEFINITION_PENDING 单列）
  S11 限制登记：每条 L 在其"引用于"所列报告正文里被引用（嵌入的限制表行不算）
  S12 报告齐全（R0 / part1 / part2 / part3 / mechanisms / B3 / carried + cards + E7 + 记录 B + 限制登记 / 经验增量 / 代码变更登记 + REVIEW_input_notes）
  S13 副本包 P0–P3 manifest 在、复制后 sha 0 不符             S14 政策表全部 deployment_authorized = false；新路线 replacement NOT_AUTHORIZED
  S15 封存目录（sealed_after_20260327）只列名、文件数不变"""
import e6j_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import subprocess

import pandas as pd

import e6m_core as M
import e6m_stageN_gate as GN

ALLOWED_AUX = ('COMPUTED', 'LIMIT', 'NO_NEW_CONTENT_TO_PERMUTE', 'RANDOM_NOT_SCHEDULED')


def e7_cutoff_47(cut='2026-03-27'):
    """47 上的 S15 判据（无封存目录）：A1-5 守卫攻击全 PASS，且 accounts / accounts_aux / randoms 下带 dates 的 npz 末日 ≤ cut。
    数据源截止后的日文件数只作 INFO（攻击测试已证明守卫会拦）。返回 (ok, 明细)。"""
    import numpy as np
    ga = M.P('stage0_S', 'c1', 'guard_attack.csv')
    G_ = pd.read_csv(ga, dtype=str, keep_default_na=False) if os.path.exists(ga) else pd.DataFrame(columns=['status'])
    ga_ok = len(G_) > 0 and bool((G_.status == 'PASS').all())
    mx, nf, over = '', 0, []
    for d in ('accounts', 'accounts_aux', 'randoms'):
        for f in glob.glob(M.P(d, '**', '*.npz'), recursive=True):
            with np.load(f, allow_pickle=False) as z:
                if 'dates' not in z.files:
                    continue
                m_ = str(max(z['dates']))[:10]
            nf += 1
            mx = max(mx, m_)
            if m_ > cut:
                over.append(M.rel(f))
    post = None
    try:
        import data_loader as DL
        src = DL.PATHS.get('daily_kline')
        post = sum(1 for x in os.listdir(src) if x[:8].isdigit() and x[:8] > cut.replace('-', '')) if src and os.path.isdir(src) else None
    except Exception:  # noqa: BLE001
        post = None
    ok = ga_ok and nf > 0 and not over
    return ok, dict(guard_attack=G_.status.value_counts().to_dict(), dated_npz=nf, max_date=mx, over_cutoff=over[:5],
                    source_post_cutoff_files_info=post)
def limit_citations(lr, reports_dir):
    """S11（brief A9 / E6l E03）：限制登记表"引用于"列所列的每份报告正文里都要出现该编号；报告里嵌入的限制表行（以"| L-S"起头）不算引用，
    编号整词匹配（L-S1 不匹配 L-S10）。返回 (编号列表, [(编号, 文件, 原因)])；登记缺"引用于"列即整体不过。"""
    if not os.path.exists(lr):
        return [], [('ALL', M.rel(lr), '限制登记缺')]
    head, rows = None, []
    for line in open(lr, encoding='utf-8').read().split('\n'):
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if head is None and '编号' in cells:
            head = cells
        elif re.match(r'^L-S\d+$', cells[0]):
            rows.append(cells)
    ids = [r[0] for r in rows]
    if head is None or '引用于' not in head:
        return ids, [('ALL', M.rel(lr), '限制登记缺"引用于"列')]
    k = head.index('引用于')
    texts, bad = {}, []
    for r in rows:
        files = [f.strip().strip('`') for f in re.split(r'[；、,，]', r[k] if k < len(r) else '') if f.strip()]
        if not files:
            bad.append((r[0], '', '"引用于"为空'))
        for f in files:
            if f not in texts:
                p = os.path.join(reports_dir, f)
                texts[f] = None if not os.path.exists(p) else '\n'.join(l for l in open(p, encoding='utf-8', errors='replace').read().split('\n')
                                                                       if not l.lstrip().startswith('| L-S'))
            if texts[f] is None:
                bad.append((r[0], f, '报告缺'))
            elif not re.search(re.escape(r[0]) + r'(?!\d)', texts[f]):
                bad.append((r[0], f, '未引用'))
    return ids, bad


REPORTS = ('E6m_REPORT_R0.md', 'E6m_REPORT_part1.md', 'E6m_REPORT_part2.md', 'E6m_REPORT_part3.md', 'E6m_REPORT_mechanisms.md', 'E6m_REPORT_B3.md',
           'E6m_REPORT_carried.md', 'E6m_cards.md', 'E6m_E7_prep.md',
           'E6m_record_B_draft.md', 'E6m_limit_register.md', 'E6m_lessons_delta.md', 'E6m_code_change_register.md',   # brief §9 交付文档（s5a docs）
           'E6m_REVIEW_input_notes.md')                                                                              # 执行端读结果后写（s5b notes-check）


def ancestors():
    """本进程及其全部祖先（runbook 的 bash、ssh 外壳等不算"运行中作业"）。"""
    out, p = set(), os.getpid()
    while p > 1 and p not in out:
        out.add(p)
        try:
            p = int(open('/proc/%d/stat' % p).read().rsplit(')', 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            break
    return out


def main():
    out_json, out_csv = M.P('closure_gate_stageS.json'), M.P('closure_gate_stageS.csv')
    skip = {os.path.realpath(out_json), os.path.realpath(out_csv)}
    G = []

    def item(gid, desc, ok, **d):
        G.append(dict(id=gid, desc=desc, status='PASS' if ok is True else ('INFO' if ok is None else 'FAIL'), detail=M.san(json.dumps(d, ensure_ascii=False, default=str))[:900]))
    ps = subprocess.run(['ps', '-eo', 'pid,lstart,args', '--no-headers'], capture_output=True, text=True).stdout.split('\n')
    mine = ancestors()
    procs = [l for l in ps if l.strip() and re.search(r'e6m_', l) and int(l.split()[0]) not in mine and 'ps -eo' not in l]
    item('S01', '本项目运行中进程 0', not procs, lines=[M.san(l)[:150] for l in procs[:8]])
    ident = json.load(open(M.P('identity_at_start.json'), encoding='utf-8'))
    head = GN.git('rev-parse', 'HEAD').strip()
    tracked = [l for l in GN.git('status', '--porcelain', '--untracked-files=no').split('\n') if l.strip()]
    item('S02', 'git：HEAD = 开工基线、tracked 改动 0（白名单提交前）', head.startswith((ident.get('git_head') or ident.get('head_expected_prefix') or 'eb2f51f')[:7]) and not tracked, head=head[:12], tracked=len(tracked))
    rec = {}
    for f in sorted(os.listdir(M.P('task_status'))):
        r = json.load(open(M.P('task_status', f), encoding='utf-8'))
        rec[r['task_id']] = (r['status'], r['written_at'], r.get('stage', ''))
    unc = []
    for t, (st, at, sg) in rec.items():
        if sg != 'S' or t.startswith('S_dev_') or st == 'SUCCEEDED':
            continue
        base = re.sub(r'_rerun\d*$', '', t)
        if not [u for u, (s2, a2, _) in rec.items() if u != t and re.sub(r'_rerun\d*$', '', u) == base and s2 == 'SUCCEEDED' and a2 >= at]:
            unc.append(t)
    item('S03', '回执：阶段 S 生产任务 FAILED 均被后写 _rerun 覆盖', not unc, uncovered=unc[:20], n_uncovered=len(unc))
    import e6m_s_seal as SEAL
    seals = {}
    for ph in ('deriv', 'post'):
        try:
            SEAL.require(ph)
            seals[ph] = 'OK'
        except RuntimeError as e:
            seals[ph] = str(e)[:80]
    item('S04', 'seal_deriv / seal_post all_ok 且 sha 未变', all(v == 'OK' for v in seals.values()), seals=seals)
    g = GN.json.load(open(M.P('stage0_S', 'stage0_S_gate.json'), encoding='utf-8')) if os.path.exists(M.P('stage0_S', 'stage0_S_gate.json')) else {}
    a1 = json.load(open(M.P('registration', 'a1_auto_E6m_S.json'), encoding='utf-8')) if os.path.exists(M.P('registration', 'a1_auto_E6m_S.json')) else {}
    cr = json.load(open(M.P('registration', 'record_B_conditions_receipt_E6m.json'), encoding='utf-8')) if os.path.exists(
        M.P('registration', 'record_B_conditions_receipt_E6m.json')) else {}
    a1_eff, rc2 = bool(a1.get('all_pass')), M.P('registration', 'a1_auto_item2_reconciliation_E6m_S.json')
    if not a1_eff and os.path.exists(rc2):      # 补丁十七：同补丁十四（用户 2026-10-11 原话放行 A1-auto 第 2 项；冻结件不改）——门里重新核绑定
        R2 = json.load(open(rc2, encoding='utf-8'))
        np_ = a1.get('not_pass', [])
        a1_eff = (len(np_) == 1 and str(np_[0].get('item')) == '2' and R2.get('verdict') == 'PASS' and bool(R2.get('user_quote'))
                  and bool(R2.get('user_quote_date')) and R2.get('a1_auto_sha256') == M.sha_file(M.P('registration', 'a1_auto_E6m_S.json'))
                  and R2.get('transcription_sha256') == M.sha_file(M.P('registration', 'policy_profiles_E6m_stageN.json')))
    item('S05', 'Stage 0 S 门 / A1-auto（S）/ 生效条件回执 all_pass', bool(g.get('all_pass') and a1_eff and cr.get('all_pass')),
         stage0=g.get('counts'), a1_auto=a1.get('counts'), a1_auto_effective=a1_eff, a1_auto_item2_reconciliation=M.rel(rc2) if os.path.exists(rc2) else '',
         conditions=cr.get('all_pass'))
    forb = set(M.FORBIDDEN_STATUS)
    hits = []
    prod = [p for p in GN.files(skip) if os.path.relpath(p, M.work()).split(os.sep)[0] not in ('stageS_dev', 'stageN', 'tmp')]
    for p in prod:
        if p.endswith('.csv') and os.path.getsize(p) < 500e6:
            try:
                df = pd.read_csv(p, dtype=str, keep_default_na=False)
            except Exception:                              # noqa: BLE001
                continue
            for c in df.columns:
                v = set(df[c]) & forb
                if v:
                    hits.append('%s:%s=%s' % (os.path.relpath(p, M.work()), c, sorted(v)))
    item('S06', 'A6-3 状态词扫描（阶段 S 产物 CSV）', not hits, hits=hits[:12], n_hits=len(hits))
    udir, accts = M._names()
    names = ([os.sep + udir + os.sep] if udir else []) + ['/base/' + x + '/' for x in accts if x]   # 补丁十八：名字按路径分量，与 M.san 同式（子串匹配遇 2 字符账号名满屏误报）
    pats = [('ipv4', re.compile(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])')),
            ('secret', re.compile(r'(?i)password|passwd|口令|密码|secret|api[_-]?key|BEGIN [A-Z ]*PRIVATE KEY|ssh-rsa|ssh-ed25519|token=')),
            ('home', re.compile(re.escape(os.path.expanduser('~') + os.sep)))]
    sh = []
    import e6m_s_deliver as DLV
    dl = sorted(set(os.path.join(M.work(), f) for _, g in DLV.collect() for f in g))   # 补丁十八：扫交付集（拷到 handoff 的文件）；不交付的运行日志 / 代码存档 / 试跑不扫
    for p in dl:
        if not p.endswith(GN.TEXT_EXT) or os.path.getsize(p) > 200e6:
            continue
        text = open(p, encoding='utf-8', errors='replace').read()
        for i, ln in enumerate(text.split('\n'), 1):
            if any(rx.search(ln) for _, rx in pats) or any(n in ln for n in names):
                sh.append('%s:%d' % (os.path.relpath(p, M.work()), i))
    item('S07', 'A6-6 敏感信息扫描（阶段 S 产物文本）', not sh, hits=sh[:20], n_hits=len(sh), scope='deliver.collect', n_files=len(dl))
    Q = M.read_csv_keep(M.P('registry', 'query_registry_E6m.csv'), dtype=str)
    qd = M.P('reports', 'queries_full')
    bad_q = []
    for q in Q.query_id:
        p = os.path.join(qd, '%s.csv' % q)
        if not os.path.exists(p):
            bad_q.append((q, '缺'))
            continue
        X = pd.read_csv(p, dtype=str, keep_default_na=False)
        if len(X) == 0 or list(X.columns) != list(pd.read_csv(M.P('reports_skeleton', 'queries', '%s.csv' % q), nrows=0).columns):
            bad_q.append((q, '0 行或列不符'))
    item('S08', 'query：唯一、全有表、≥ 1 行、列 = 骨架', Q.query_id.is_unique and not bad_q, bad=bad_q[:12], n=len(Q))
    F = M.read_csv_keep(M.P('registry', 'fixed_outputs_E6m.csv'), dtype=str)
    bad_f = []
    for nm in F[F.carried == 'True'].e6m_name:
        p = M.P('reports', 'fixed_full', '%s.csv' % nm)
        if not os.path.exists(p):
            bad_f.append((nm, '缺'))
            continue
        X = pd.read_csv(p, dtype=str, keep_default_na=False)
        if len(X) == 0 or list(X.columns) != list(pd.read_csv(M.P('reports_skeleton', 'fixed', '%s.csv' % nm), nrows=0).columns):
            bad_f.append((nm, '0 行或列不符'))
    item('S09', '固定输出全在、≥ 1 行、列 = 骨架', not bad_f, bad=bad_f)
    ap_ = M.P('results', 'full', 'aux_status', 'aux_status_E6m_full.csv')
    if os.path.exists(ap_):
        A = pd.read_csv(ap_, dtype=str, keep_default_na=False)
        bad_a = A[~A.status.isin(ALLOWED_AUX + ('DEFINITION_PENDING',))]
        item('S10', '覆盖：附属逐行状态（允许 LIMIT 等显式状态；DEFINITION_PENDING 单列）', bad_a.empty, bad=bad_a.status.value_counts().to_dict(),
             definition_pending=int((A.status == 'DEFINITION_PENDING').sum()))
    else:
        item('S10', '覆盖：附属逐行状态', False, missing=M.rel(ap_))
    lr = M.P('reports', 'E6m_limit_register.md')                          # 交付版（s5a 由 stageN 草稿拼成）；未生成时看草稿
    lr = lr if os.path.exists(lr) else M.P('stageN', 'limit_register_stageS_draft.md')
    ids, uncited = limit_citations(lr, M.P('reports'))
    item('S11', '限制登记每条在"引用于"所列报告正文里被引用（嵌入的限制表行不算）', bool(ids) and not uncited, uncited=uncited[:20], n=len(ids),
         register=M.rel(lr))
    miss_r = [r for r in REPORTS if not os.path.exists(M.P('reports', r))]
    item('S12', '报告齐全', not miss_r, missing=miss_r)
    mans = sorted(glob.glob(M.P('replica', 'replica_manifest_P*_final.json')))
    bad_m = [os.path.basename(p) for p in mans if json.load(open(p, encoding='utf-8')).get('verified', {}).get('mismatched')]
    item('S13', '副本包 P0–P3（final）manifest 在且复制后 sha 0 不符', len(mans) == 4 and not bad_m, manifests=[os.path.basename(p) for p in mans], bad=bad_m)
    pol = M.P('results', 'full', 'policy_E6m.csv')
    if os.path.exists(pol):
        P = pd.read_csv(pol, dtype=str, keep_default_na=False, low_memory=False)
        item('S14', 'deployment_authorized 全 false；新路线 replacement NOT_AUTHORIZED', bool((P.deployment_authorized.str.lower() == 'false').all()),
             replacement=P.replacement_status.value_counts().to_dict() if 'replacement_status' in P.columns else {})
    else:
        item('S14', '政策表', False, missing=M.rel(pol))
    se = M.SEALED
    if M.MACHINE == '47' and not os.path.isdir(se):    # 47 无封存目录（2026-10-11 用户经 advisor 定）
        ok15, d15 = e7_cutoff_47()
        item('S15', 'E7 截止（47 无封存目录）：A1-5 守卫攻击全 PASS 且产物日期轴 ≤ 2026-03-27', ok15, **d15)
    else:
        sealed = {d: len(os.listdir(os.path.join(se, d))) for d in sorted(os.listdir(se)) if os.path.isdir(os.path.join(se, d))} if os.path.isdir(se) else {}
        item('S15', '封存目录只列名、文件数不变', sealed == {'cache': 1, 'daily_temp3': 127}, sealed=sealed)
    df = pd.DataFrame(G)
    M.atomic_write_csv(out_csv, df)
    res = dict(gate='E6m 阶段 S 闭包门', written_at=M.time.strftime('%Y-%m-%d %H:%M:%S'), machine=M.MACHINE, script_sha256=M.sha_file(os.path.realpath(__file__)),
               all_pass=bool((df.status != 'FAIL').all()), counts=df.status.value_counts().to_dict(), items=G)
    M.atomic_write_json(out_json, res)
    print(json.dumps(dict(all_pass=res['all_pass'], counts=res['counts']), ensure_ascii=False))
    print(df[df.status != 'PASS'][['id', 'status', 'detail']].to_string(max_colwidth=160))
    return 0 if res['all_pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
