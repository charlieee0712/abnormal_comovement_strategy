# -*- coding: utf-8 -*-
"""E6m 阶段 N 闭包门（附录 D-5 的 N 子集 + A6-3 / A6-4 / A6-6）。只读；输出 stageN/closure_gate_stageN.json（门输出不自扫，E6l G10 教训）。"""
import os
import re
import sys
import json
import subprocess

import pandas as pd

import e6m_core as M

HANDOFF = os.path.expanduser('~/autodl-tmp/factor_runs/resonance/handoff/E6m')
SKIP_DIRS = ('tmp',)
TEXT_EXT = ('.csv', '.json', '.md', '.txt', '.py', '.log')


def git(*args):
    cmd = ['git', '-c', 'safe.directory=%s' % os.path.realpath(M.CODE), '--no-optional-locks', '-C', M.CODE] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def files(skip_out):
    W = M.work()
    for root, dirs, fs in os.walk(W):
        rel = os.path.relpath(root, W)
        if rel.split(os.sep)[0] in SKIP_DIRS:
            continue
        for f in fs:
            p = os.path.join(root, f)
            if os.path.realpath(p) not in skip_out and not f.startswith('closure_gate_stageN'):   # 门输出（含存档副本）不自扫
                yield p


def main():
    out_json = M.P('stageN', 'closure_gate_stageN.json')
    out_csv = M.P('stageN', 'closure_gate_stageN.csv')
    skip_out = {os.path.realpath(out_json), os.path.realpath(out_csv)}
    G = []

    def item(gid, desc, ok, **d):
        G.append(dict(id=gid, desc=desc, status='PASS' if ok is True else ('INFO' if ok is None else 'FAIL'), detail=M.san(json.dumps(d, ensure_ascii=False, default=str))[:900]))
    ps = subprocess.run(['ps', '-eo', 'pid,lstart,args', '--no-headers'], capture_output=True, text=True).stdout.split('\n')
    mine = {os.getpid(), os.getppid()}
    kw = re.compile(r'e6m_|e6l_|e6k_|e6j_|verify_e6')
    procs = [l for l in ps if l.strip() and kw.search(l) and int(l.split()[0]) not in mine and 'ps -eo' not in l]
    item('G01', '本项目运行中进程 0（PID + 启动时间 + 命令行；不含本进程）', not procs, lines=[M.san(l)[:150] for l in procs[:8]])
    ident = json.load(open(M.P('identity_at_start.json'), encoding='utf-8'))
    head, om = git('rev-parse', 'HEAD').strip(), git('rev-parse', '--verify', '-q', 'origin/main').strip()
    tracked = [l for l in git('status', '--porcelain', '--untracked-files=no').split('\n') if l.strip()]
    untracked = sorted(l[3:] for l in git('status', '--porcelain', '--untracked-files=all').split('\n') if l.startswith('?? '))
    base0 = sorted(u for u in ident['untracked'] if not u.startswith('e6m_'))
    now_non = sorted(u for u in untracked if not u.startswith('e6m_'))
    e6m = sorted(u for u in untracked if u.startswith('e6m_'))
    item('G02', 'git：HEAD = origin/main = eb2f51f；tracked 改动 0；e6m_ 以外的未跟踪文件 = 开工时 26 个（未动）；本轮新增 e6m_*.py 列出',
         head.startswith('eb2f51f') and om == head and not tracked and now_non == base0 and len(base0) == 26, head=head[:12], tracked=len(tracked),
         untracked_non_e6m=len(now_non), e6m_files=e6m)
    rec = {}
    for f in sorted(os.listdir(M.P('task_status'))):
        r = json.load(open(M.P('task_status', f), encoding='utf-8'))
        rec[r['task_id']] = (r['status'], r['written_at'])
    unc = []
    for t, (st, at) in rec.items():
        if t.startswith('N7_handoff_copy'):                # 复制在闭包门之后（门不判自己之后的步骤）
            continue
        if st != 'SUCCEEDED':
            base = re.sub(r'_rerun\d*$', '', t)
            cover = [u for u, (s2, a2) in rec.items() if u != t and re.sub(r'_rerun\d*$', '', u) == base and s2 == 'SUCCEEDED' and a2 >= at]
            if not cover:
                unc.append(t)
    item('G03', '回执：全部 SUCCEEDED，或 FAILED 由同名 _rerun（后写、SUCCEEDED）覆盖', not unc, receipts=len(rec), failed=[t for t, v in rec.items() if v[0] != 'SUCCEEDED'],
         uncovered=unc)
    listed = {}
    for ln in open(os.path.join(HANDOFF, 'HANDOFF_SHA256.txt'), encoding='utf-8'):
        p = ln.split()
        if len(p) == 2:
            listed[p[1]] = p[0]
    badh = [f for f, s in listed.items() if M.sha_file(os.path.join(HANDOFF, f)) != s]
    item('G04', '交接件 sha 与 HANDOFF_SHA256.txt 相同（阶段 N 结束时复核）', not badh, n=len(listed), bad=badh)
    forb = set(M.FORBIDDEN_STATUS)
    hits = []
    for p in files(skip_out):
        rel = os.path.relpath(p, M.work())
        if p.endswith('.csv'):
            try:
                df = pd.read_csv(p, dtype=str, keep_default_na=False)
            except Exception:                              # noqa: BLE001
                continue
            for c in df.columns:
                v = set(df[c]) & forb
                if v:
                    hits.append('%s:%s=%s' % (rel, c, sorted(v)))
        elif p.endswith('.json'):
            def walk(o, k=''):
                if isinstance(o, dict):
                    for kk, vv in o.items():
                        if kk not in ('status_words_forbidden', 'FORBIDDEN_STATUS'):
                            walk(vv, kk)
                elif isinstance(o, list):
                    for vv in o:
                        walk(vv, k)
                elif isinstance(o, str) and o in forb:
                    hits.append('%s:%s=%s' % (rel, k, o))
            try:
                walk(json.load(open(p, encoding='utf-8')))
            except Exception:                              # noqa: BLE001
                pass
    item('G05', 'A6-3 状态词扫描：全部 CSV 单元格 / JSON 值（不含禁用词清单本身）无 N/A / NA / nan / NaN / null / None', not hits, hits=hits[:12], n_hits=len(hits))
    udir, accts = M._names()
    names = [x for x in [udir] + accts if x]
    pats = [('ipv4', re.compile(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])')), ('user@host', re.compile(r'\b[\w.-]+@[\w-]+(?:\.[\w-]+)+\b')),
            ('secret', re.compile(r'(?i)password|passwd|口令|密码|secret|api[_-]?key|BEGIN [A-Z ]*PRIVATE KEY|ssh-rsa|ssh-ed25519|token=')),
            ('home', re.compile(re.escape(os.path.expanduser('~') + os.sep)))]
    sh = []
    nfile = 0
    for p in files(skip_out):
        if not p.endswith(TEXT_EXT) or os.path.basename(p) in ('e6m_stageN_gate.py',) or os.path.getsize(p) > 200e6:
            continue
        nfile += 1
        try:
            text = open(p, encoding='utf-8', errors='replace').read()
        except Exception:                                  # noqa: BLE001
            continue
        rel = os.path.relpath(p, M.work())
        for i, ln in enumerate(text.split('\n'), 1):
            for tag, rx in pats:
                m_ = rx.search(ln)
                if m_ and tag == 'user@host' and (ln[m_.end():m_.end() + 1] == '(' or '@np.' in m_.group(0)):
                    continue                              # 矩阵乘写法（X@np.linalg…）不是 user@host
                if m_:
                    sh.append('%s:%d:%s' % (rel, i, tag))
            if any(n in ln for n in names):
                sh.append('%s:%d:account' % (rel, i))
    item('G06', 'A6-6 敏感信息扫描（工作目录全部文本，tmp / 门输出 / 本脚本除外）：IPv4 / user@host / 口令密钥类 / 家目录 / 用户目录与账号名', not sh, files=nfile, hits=sh[:20],
         n_hits=len(sh))
    cols = []
    for root in (M.P('reports_skeleton', 'queries'), M.P('reports_skeleton', 'fixed')):
        for f in sorted(os.listdir(root)):
            cols += list(pd.read_csv(os.path.join(root, f), nrows=0).columns)
    suf = ('_ann_pp', '_bp_per_h', '_pct_pt', '_decimal', '_segavg', 'q95_maxabs_t', 'halfwidth_ann_pp')
    valued = sorted({c for c in cols if c.endswith(suf)})
    item('G07', 'A6-4 列名带单位：骨架表中带单位后缀的数值列清单（计数列 n_* 无单位）', None, with_unit=valued)
    a1 = json.load(open(M.P('registration', 'a1_auto_E6m.json'), encoding='utf-8'))
    item('G08', 'A0 / A1-auto（阶段 N）：编译对账成功；A1-auto 计数', None, counts=a1['counts'],
         fails=[(x['item'], x['check'][:40]) for x in a1['items'] if x['status'] == 'FAIL'])
    cl = json.load(open(M.P('registry', 'import_closure_E6m.json'), encoding='utf-8'))
    ext = M.read_csv_keep(M.P('registry', 'external_inputs_E6m.csv'))
    item('G09', 'import 闭包：数据侧不含 e6e_core、import 期不读数据文件；账户侧缺 X01；外部输入清单每行有 sha 或 SOURCE_WAIT',
         (cl['data_side']['ok'] and not cl['data_side']['contains_e6e_core'] and not cl['data_side'].get('data_file_reads_at_import') and not cl['account_side']['ok']
          and bool(((ext.sha256 != '') | ext.status.isin(['SOURCE_WAIT', 'PRESENT_NOT_READ', 'PRESENT_UNHASHED'])).all())), external=ext.status.value_counts().to_dict())
    se = os.path.expanduser('~/autodl-tmp/sealed_after_20260327')
    sealed = {d: len(os.listdir(os.path.join(se, d))) for d in sorted(os.listdir(se)) if os.path.isdir(os.path.join(se, d))}
    item('G10', '封存目录只列名（文件数与开工前一致：cache 1 / daily_temp3 127）；阶段 N 未读', sealed == {'cache': 1, 'daily_temp3': 127}, sealed=sealed)
    df = pd.DataFrame(G)
    os.makedirs(M.P('stageN'), exist_ok=True)
    M.atomic_write_csv(out_csv, df)
    res = dict(gate='E6m 阶段 N 闭包门', written_at=M.time.strftime('%Y-%m-%d %H:%M:%S'), machine=M.MACHINE, script_sha256=M.sha_file(os.path.realpath(__file__)),
               all_pass=bool((df.status != 'FAIL').all()), counts=df.status.value_counts().to_dict(), items=G)
    M.atomic_write_json(out_json, res)
    print(json.dumps(dict(all_pass=res['all_pass'], counts=res['counts']), ensure_ascii=False))
    print(df[df.status != 'PASS'][['id', 'status', 'detail']].to_string(max_colwidth=200))
    return 0 if res['all_pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
