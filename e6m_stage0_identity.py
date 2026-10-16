# -*- coding: utf-8 -*-
"""E6m 阶段 N · N1 / Stage 0 第 1 类（身份 / 权限）中云机可做的项（附录 A1-1 / A1-3 登记 / A1-4 HEAD / A1-6）。
输出：identity_at_start.json、PLAN_COPY.md、stage0/c1_identity_handoff.csv、stage0/c1_env_lock.csv、
registration/authorization_status_E6m.json、registration/record_B_mode_A.json。只读交接目录与代码目录；不读任何行情。"""
import os
import sys
import json
import shutil
import argparse
import subprocess

import e6m_core as M

HANDOFF = os.path.join(M.RUNS, 'handoff', 'E6m')
PLAN_SHA = 'df20f5f4c420ed58eb58ffb2659e66031cf015290135e8b25fc36f8ed9623ef8'
SPEC_SHA = '25020c8239adb9b7a2ee86a45aa653005689b38127d94187a1be546fe062cca9'
ENV_LOCK = dict(python='3.10.13', numpy='1.26.1', pandas='2.2.3', scipy='1.11.3', statsmodels='0.14.0', numba='0.58.1')
HEAD_EXP = 'eb2f51f'
# 转交消息原话（用户 2026-10-04 本地日期；不含粘贴的交接段落）
USER_QUOTE = '开始E6m轮执行 … 记得好好思考效率优化方案 要是跑的吃力随时和我说 我在云服务器上加卡 中途不需要特意停下来汇报 避免空转'
MODE_B_WORDS = ('B', '事前整表授权', '按这个完整方案一口气执行')
N8_WORDS = '含云机 B3 先行'


def git(*args):
    code = M.CODE
    cmd = ['git', '-c', 'safe.directory=%s' % os.path.realpath(code), '--no-optional-locks', '-C', code] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--user-quote-date', default='2026-10-04')
    a = ap.parse_args()
    os.makedirs(M.P('stage0'), exist_ok=True)
    # A1-1 交接件全长 sha
    rows = []
    listed = {}
    for ln in open(os.path.join(HANDOFF, 'HANDOFF_SHA256.txt'), encoding='utf-8'):
        p = ln.split()
        if len(p) == 2:
            listed[p[1]] = p[0]
    for f, exp in sorted(listed.items()):
        fp = os.path.join(HANDOFF, f)
        got = M.sha_file(fp) if os.path.exists(fp) else 'MISSING'
        rows.append(dict(probe='A1-1', file=f, expected_sha256=exp, sha256=got, bytes=os.path.getsize(fp) if os.path.exists(fp) else -1,
                         status='PASS' if got == exp else 'FAIL'))
    # PLAN_COPY 与 spec 的额外身份（字节数 / 行数）
    plan = os.path.join(HANDOFF, 'E6m_plan_web_final.md')
    shutil.copyfile(plan, M.P('PLAN_COPY.md'))
    pc = M.P('PLAN_COPY.md')
    nb, nl = os.path.getsize(pc), sum(1 for _ in open(pc, 'rb'))
    rows.append(dict(probe='A1-1', file='PLAN_COPY.md', expected_sha256=PLAN_SHA, sha256=M.sha_file(pc), bytes=nb,
                     status='PASS' if (M.sha_file(pc) == PLAN_SHA and nb == 165115 and nl == 1811) else 'FAIL'))
    spec = os.path.join(HANDOFF, 'e6m_spec_tests.py')
    sl = sum(1 for _ in open(spec, 'rb'))
    rows.append(dict(probe='A1-1', file='e6m_spec_tests.py（712 行）', expected_sha256=SPEC_SHA, sha256=M.sha_file(spec), bytes=os.path.getsize(spec),
                     status='PASS' if (M.sha_file(spec) == SPEC_SHA and sl == 712) else 'FAIL'))
    df = M.pd.DataFrame(rows)
    M.atomic_write_csv(M.P('stage0', 'c1_identity_handoff.csv'), df)
    # A1-4 HEAD（manifest 部分 = S）
    head, om = git('rev-parse', 'HEAD').strip(), git('rev-parse', '--verify', '-q', 'origin/main').strip()
    tracked = [l for l in git('status', '--porcelain', '--untracked-files=no').split('\n') if l.strip()]
    untracked = sorted(l[3:] for l in git('status', '--porcelain', '--untracked-files=all').split('\n') if l.startswith('?? '))
    # A1-6 环境锁
    env = M.env_versions()
    env_rows = [dict(probe='A1-6', package=k, expected=v, actual=env.get(k, 'NOT_INSTALLED'), status='PASS' if env.get(k) == v else 'FAIL')
                for k, v in ENV_LOCK.items()]
    M.atomic_write_csv(M.P('stage0', 'c1_env_lock.csv'), M.pd.DataFrame(env_rows))
    # A1-3 授权登记（转交消息原话）
    has_b = any(w in USER_QUOTE for w in MODE_B_WORDS[1:]) or ('B' in USER_QUOTE.replace('E6m', '').replace('B3', ''))
    has_n8 = N8_WORDS in USER_QUOTE
    auth = dict(written_at=M.time.strftime('%Y-%m-%d %H:%M:%S'), machine=M.MACHINE, user_quote=USER_QUOTE, user_quote_date=a.user_quote_date,
                user_quote_note='转交消息里用户自己的话；粘贴的交接段落（交接件清单）不计为用户原话',
                w11_mode='B' if has_b else 'A',
                w11_basis='brief W11：转交消息含 "B" / "事前整表授权" / "按这个完整方案一口气执行"（含两后段）→ 方式 B；本条消息不含 → 方式 A（推导两段算完、封存、记录 B 草稿后停等用户一句话）',
                n8_b3_prelim='AUTHORIZED' if has_n8 else 'NOT_AUTHORIZED',
                n8_basis='brief §5 N8：转交消息须含"含云机 B3 先行"；本条消息不含 → N8 不跑',
                stage_s_gate='47 可达（或 X01 + P3 锚文件到云机）且 brief 未被新版本替代')
    M.atomic_write_json(M.P('registration', 'authorization_status_E6m.json'), auth)
    if not has_b:
        M.atomic_write_json(M.P('registration', 'record_B_mode_A.json'), dict(mode='A', user_quote=USER_QUOTE, user_quote_date=a.user_quote_date,
                                                                             written_at=auth['written_at'], basis=auth['w11_basis']))
    ident = dict(written_at=M.time.strftime('%Y-%m-%d %H:%M:%S'), machine=M.MACHINE, stage='N', work_dir=M.san(M.work()),
                 code_dir=M.san(M.CODE), git_head=head, origin_main=om, head_expected_prefix=HEAD_EXP,
                 head_ok=head.startswith(HEAD_EXP) and om == head, tracked_changes=len(tracked), untracked_n=len(untracked),
                 untracked=[M.san(u) for u in untracked], handoff_all_pass=bool((df.status == 'PASS').all()), handoff_rows=len(df),
                 env=env, env_lock_pass=all(r['status'] == 'PASS' for r in env_rows),
                 brief_sha256=listed.get('E6m_access_form_stage.md'), appendix_sha256=listed.get('E6m_brief_appendix_probes.md'),
                 plan_sha256=PLAN_SHA, spec_sha256=SPEC_SHA, authorization=dict(w11_mode=auth['w11_mode'], n8=auth['n8_b3_prelim']),
                 market_data_end_max=M.MARKET_DATA_END_MAX, python_executable=M.san(sys.executable))
    M.atomic_write_json(M.P('identity_at_start.json'), ident)
    outs = [M.P('identity_at_start.json'), M.P('PLAN_COPY.md'), M.P('stage0', 'c1_identity_handoff.csv'), M.P('stage0', 'c1_env_lock.csv'),
            M.P('registration', 'authorization_status_E6m.json')] + ([M.P('registration', 'record_B_mode_A.json')] if not has_b else [])
    ok = ident['head_ok'] and not tracked and ident['handoff_all_pass'] and ident['env_lock_pass']
    M.write_receipt('stage0_c1_identity_N', outs, status='SUCCEEDED' if ok else 'FAILED', inputs=[os.path.join(HANDOFF, 'HANDOFF_SHA256.txt')],
                    code=[__file__, M.__file__], head=head[:12], untracked_n=len(untracked))
    print(json.dumps(dict(head_ok=ident['head_ok'], tracked=len(tracked), untracked=len(untracked), handoff=ident['handoff_all_pass'],
                          env=ident['env_lock_pass'], w11=auth['w11_mode'], n8=auth['n8_b3_prelim']), ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
