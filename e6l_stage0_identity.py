# -*- coding: utf-8 -*-
"""E6l Stage 0 第 1 类：身份 / 权限（brief §2 第 1 类；附录 A1-1 … A1-7；plan §13.1）。
A1-1 三处输入 sha 全长（本地 = 决策端给出的 E6l_local_hashes.txt → stage0/local_exec_briefs_hashes.json；47 exec_briefs；结果目录 *_copy.md）
     + PLAN_COPY.md 全长（= plan；47 tmp/e6l_handoff）+ spec 脚本
A1-2 E6k / E6j 原件可读 + sha 与 E6k REVIEW_input（16 位前缀）/ E6k_MIRROR.md5（全长）一致；三本内部手册 NOT_REQUIRED（brief A8）
A1-3 授权：registration/authorization_intake_E6l.json（方式 B 原话 + 日期）；post_gate 在临时目录两向实测（无授权拒绝 / 授权放行 / 清单变更拒绝 / 推导段不拦）
A1-4 E6k source_manifest.readonly_code_sha256（217 文件；e6k_core 以交付 sha 为准）+ e6k 交付代码（E6k REVIEW_input 48 个前缀）= 现 sha
A1-5 数据截止 2026-03-27 + E7 守卫攻击（E6k 九入口 + 本轮：全程缓存入口、状态序列入口、连续面板入口、e6l post_gate）
A1-6 HEAD = ec91def；git status 只有开工基线 untracked + 本轮新 e6l_*（未提交）；无已跟踪改动
A1-7 环境锁：Python 3.10.13 / NumPy 1.26.1 / pandas 2.2.3 / SciPy 1.11.3 / statsmodels 0.14.0 / numba 0.58.1；BLAS 线程 ≤ 4
只写 E6l 结果目录；不读 2026-03-27 之后任何真实行情。"""
import e6l_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import shutil
import subprocess
import importlib

import numpy as np
import pandas as pd

import e6l_core as L
import e6j_core as J

RERUN = '--rerun' in sys.argv
TASK = 'stage0_c1_identity' + ('_rerun' if RERUN else '')
OUT = L.P('stage0', 'c1_identity' + ('_rerun' if RERUN else ''))
EB = os.path.join(L.CODE, 'exec_briefs')
HANDOFF = '/mnt/sda2/lichenchen/tmp/e6l_handoff'
INPUTS = {  # exec_briefs 文件名 → 结果目录副本名
    'E6l_time_memory_stage.md': 'brief_copy.md',
    'E6l_brief_appendix_probes.md': 'brief_appendix_copy.md',
    'E6l_proposal.md': 'E6l_proposal_copy.md',
    'E6k_REVIEW.md': 'E6k_REVIEW_copy.md',
    'E6k_RULING_20260930.md': 'E6k_RULING_copy.md',
    'E6k_VERIFY_report.md': 'E6k_VERIFY_report_copy.md',
    'E6k_REPORT_supplement_1.md': 'E6k_REPORT_supplement_1_copy.md',
    'E6k_code_change_register.md': 'E6k_code_change_register_copy.md',
    'REVIEW_protocol_v1.md': 'REVIEW_protocol_copy.md',
    '00_协议.md': '00_协议_copy.md',
}
EXPECT_PREFIX = {  # brief §0 / 附录 A1-1 给出的前缀
    'E6l_time_memory_stage.md': '4c55fb4b', 'E6l_brief_appendix_probes.md': 'f5c33bc7', 'E6l_proposal.md': 'f79c523a',
    'E6k_REVIEW.md': '8ef42f86', 'E6k_RULING_20260930.md': 'b0a87798', 'E6k_VERIFY_report.md': '7281cd63',
    'E6k_REPORT_supplement_1.md': '8b6dedc9', 'E6k_code_change_register.md': 'fd822bcb', 'REVIEW_protocol_v1.md': '0b15019e',
    '00_协议.md': 'f685e538'}
PLAN_PREFIX, PLAN_BYTES, SPEC_PREFIX = 'e7385cb7', 152579, 'fb9908d6'
HEAD = 'ec91def'
ENV_LOCK = dict(python='3.10.13', numpy='1.26.1', pandas='2.2.3', scipy='1.11.3', statsmodels='0.14.0', numba='0.58.1')


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []

    def chk(cid, obj, metric, expected, got, ok, note=''):
        st = 'INFO' if ok is None else ('PASS' if ok else 'FAIL')
        rows.append(dict(check_id=cid, object=obj, metric=metric, expected=str(expected), got=str(got), status=st, note=note))

    # ---------------- A1-1
    loc = json.load(open(L.P('stage0', 'local_exec_briefs_hashes.json'), encoding='utf-8'))['files']
    for f, cp in INPUTS.items():
        s47 = L.sha_file(os.path.join(EB, f))
        dst = L.P(cp)
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(EB, f), dst)
        sres = L.sha_file(dst)
        sloc = loc.get(f, {}).get('sha256')
        ok = (s47 == sres == sloc) and s47.startswith(EXPECT_PREFIX[f])
        chk('A1-1', f, 'sha256 本地 = 47 exec_briefs = 结果目录副本 且前缀 = brief', EXPECT_PREFIX[f], '%s|%s|%s' % (sloc, s47, sres), ok)
    sp = L.sha_file(L.P('PLAN_COPY.md'))
    sh = L.sha_file(os.path.join(HANDOFF, 'E6l_plan_web_final.md'))
    sl = loc.get('plans/E6l_plan_web_final.md', {}).get('sha256')
    nb = os.path.getsize(L.P('PLAN_COPY.md'))
    chk('A1-1', 'PLAN_COPY.md', 'sha256 全长：本地 plans/ = 47 tmp/e6l_handoff = 结果目录；字节数', '%s… / %d' % (PLAN_PREFIX, PLAN_BYTES),
        '%s|%s|%s / %d' % (sl, sh, sp, nb), sp == sh == sl and sp.startswith(PLAN_PREFIX) and nb == PLAN_BYTES)
    ss = L.sha_file(L.P('stage0', 'plan_tests', 'e6l_spec_tests.py'))
    sh2 = L.sha_file(os.path.join(HANDOFF, 'e6l_spec_tests.py'))
    chk('A1-1', 'stage0/plan_tests/e6l_spec_tests.py', 'sha256 = 47 tmp/e6l_handoff 且前缀 = brief W01', SPEC_PREFIX, '%s|%s' % (sh2, ss),
        ss == sh2 and ss.startswith(SPEC_PREFIX))

    # ---------------- A1-2
    K6 = L.E6K_RES
    ri = open(os.path.join(K6, 'reports', 'E6k_REVIEW_input.md'), encoding='utf-8').read()
    mir = open(os.path.join(K6, 'reports', 'E6k_MIRROR.md5'), encoding='utf-8').read()
    originals = ['results/full/policy_E6k.csv', 'registry/descriptors_E6k.csv', 'registry/accessory_E6k.csv', 'registry/randoms_E6k.csv',
                 'registration/policy_profiles_E6k.json', 'registration/policy_profiles_E6k_amend_1.json', 'registration/policy_profiles_E6k_amend_2.json',
                 'verify/probe_results.csv', 'results/full/random_refs_2010-2014.csv', 'results/full/random_refs_2015-2018.csv',
                 'results/full/random_refs_2019-2023.csv', 'results/full/random_refs_2024-2026.csv', 'registry/mask_facts_deriv_E6k.csv',
                 'registry/mask_facts_post_E6k.csv', 'source_manifest.json', 'engine_contract.md']
    for r in originals:
        p = os.path.join(K6, r)
        if not os.path.exists(p):
            chk('A1-2', 'E6k ' + r, '存在', True, False, False)
            continue
        s = L.sha_file(p)
        m_ri = re.search(re.escape('`' + r + '`') + r'（([0-9a-f]{16})）', ri)
        if r == 'results/full/policy_E6k.csv':
            chk('A1-2', 'E6k ' + r, 'sha256 前缀 = brief W08', '3ab02a59', s[:16], s.startswith('3ab02a59'))
        elif m_ri:
            chk('A1-2', 'E6k ' + r, 'sha256 前缀 = E6k REVIEW_input', m_ri.group(1), s[:16], s.startswith(m_ri.group(1)))
        else:
            chk('A1-2', 'E6k ' + r, '存在 + sha（E6k 交付清单未列 → 本轮只读基线）', '', s, None)
    for seg in L.SEGMENTS:
        na = len([f for f in glob.glob(os.path.join(K6, 'accounts', seg, '*.npz')) if not os.path.basename(f).startswith('weights_')])
        nr = len(glob.glob(os.path.join(K6, 'randoms', '*', seg, '*.npz')))
        chk('A1-2', 'E6k accounts / randoms %s' % seg, '账户 npz 数（不含 weights_）/ 随机分片数（只读）', '58 / —', '%d / %d' % (na, nr), na == 58)
    for r in ('verify/probe_results.csv', 'reports/E6k_VERIFY_report.md', 'reports/E6k_REPORT_supplement_1.md', 'reports/E6k_code_change_register.md'):
        p = os.path.join(K6, r)
        s = L.sha_file(p) if os.path.exists(p) else ''
        m_mi = re.search(r'[0-9a-f]{32}\s+([0-9a-f]{64})\s+RD\s+' + re.escape(r) + r'\s*$', mir, re.M)
        if m_mi:
            chk('A1-2', 'E6k ' + r, 'sha256 = E6k_MIRROR.md5 第三节（全长）', m_mi.group(1), s, s == m_mi.group(1))
        else:
            chk('A1-2', 'E6k ' + r, '存在 + sha', '', s, bool(s) or None)
    E = L.E6J_RES
    for r in ('results_P/pilot_policy.csv', 'results_B/part2_main_config_all_objects.csv', 'stage0/anchor2_rerun/e6i_parent_anchor.csv',
              'carried/leader_six_forms_capital.csv'):
        p = os.path.join(E, r)
        chk('A1-2', 'E6j ' + r, '存在（只读锚）', True, os.path.exists(p), os.path.exists(p), note=L.sha_file(p)[:16] if os.path.exists(p) else '')
    for m in ('内部手册：时序', '内部手册：时序补充', '内部手册：市场状态'):
        chk('A1-2', m, 'NOT_REQUIRED（无任何可执行定义依赖，brief A8）', 'NOT_REQUIRED', 'NOT_REQUIRED', None)

    # ---------------- A1-3 授权 + post_gate 两向实测
    pi = L.P('registration', 'authorization_intake_E6l.json')
    d = json.load(open(pi, encoding='utf-8')) if os.path.exists(pi) else {}
    chk('A1-3', 'registration/authorization_intake_E6l.json', '方式 B：用户原话（转交消息 + 当场问答）与日期', 'quotes + date',
        '%s | %s | %s' % (d.get('user_forwarding_message_quote'), d.get('user_answer_quote'), d.get('user_quote_date')),
        bool(d.get('user_forwarding_message_quote')) and bool(d.get('user_answer_quote')) and bool(d.get('user_quote_date')) and d.get('mode', '').startswith('B'))
    for r in gate_two_way():
        chk('A1-3', 'e6l_core.post_gate', r['case'], r['expect'], r['got'], r['ok'])

    # ---------------- A1-4
    sm = json.load(open(os.path.join(K6, 'source_manifest.json'), encoding='utf-8'))
    baseline = {}
    delivered = dict(re.findall(r'`code/(e6k_[A-Za-z0-9_]+\.(?:py|sh))`（([0-9a-f]{16})）', ri))
    for f, s0 in sorted(sm['readonly_code_sha256'].items()):
        s = L.sha_file(os.path.join(L.CODE, f))
        baseline[f] = s
        if f in delivered:
            chk('A1-4', f, 'sha 前缀 = E6k 交付版（REVIEW_input；Stage 0 后改动见 E6k code_change_register）', delivered[f], s[:16],
                s.startswith(delivered[f]), note='E6k Stage 0 manifest 记 %s' % s0[:16])
        else:
            chk('A1-4', f, 'sha = E6k source_manifest.readonly_code_sha256', s0, s, s == s0)
    for f, pre in sorted(delivered.items()):
        if f in baseline:
            continue
        s = L.sha_file(os.path.join(L.CODE, f))
        baseline[f] = s
        chk('A1-4', f, 'sha 前缀 = E6k 交付版（REVIEW_input）', pre, s[:16], s.startswith(pre))
    for f in sorted(os.path.basename(p) for p in glob.glob(os.path.join(L.CODE, 'e6k_*.py')) + glob.glob(os.path.join(L.CODE, 'verify_e6*.py'))):
        if f in baseline:
            continue
        s = L.sha_file(os.path.join(L.CODE, f))
        baseline[f] = s
        chk('A1-4', f, '只读基线（E6k 交付后提交或未列；本轮闭包复核不变）', '', s, None)
    L.atomic_write_json(os.path.join(OUT, 'readonly_code_baseline.json'), dict(written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), sha256=baseline))

    # ---------------- A1-5 数据截止 + E7 守卫攻击
    cal = pd.read_csv(os.path.join(E, 'registry', 'trade_calendar.csv'))
    chk('A1-5', 'E6j registry/trade_calendar.csv', '日历末日 ≤ 2026-03-27', L.MARKET_DATA_END_MAX, cal.date.max(), cal.date.max() <= L.MARKET_DATA_END_MAX)
    for r in guard_attack():
        chk('A1-5', r['entry'], r['attack'], 'raise / 静态末日 ≤ 截止', r['detail'], r['ok'])

    # ---------------- A1-6
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=L.CODE, capture_output=True, text=True).stdout.strip()
    om = subprocess.run(['git', 'rev-parse', 'origin/main'], cwd=L.CODE, capture_output=True, text=True).stdout.strip()
    chk('A1-6', 'git HEAD / origin/main', 'HEAD = origin/main = ec91def', HEAD, '%s / %s' % (head[:7], om[:7]), head.startswith(HEAD) and om.startswith(HEAD))
    stt = subprocess.run(['git', 'status', '--short'], cwd=L.CODE, capture_output=True, text=True).stdout
    base = open(L.P('stage0', 'git_status_baseline.txt'), encoding='utf-8').read()
    cur = set(l for l in stt.splitlines() if l.strip())
    bl = set(l for l in base.splitlines() if l.strip())
    new_e6l = set(l for l in cur - bl if re.match(r'^\?\? e6l_[A-Za-z0-9_]+\.(py|sh)$', l))
    other = cur - bl - new_e6l
    tracked_mod = [l for l in cur if not l.startswith('??')]
    chk('A1-6', 'git status', '只有开工基线 untracked + 本轮新 e6l_*（未提交）；无已跟踪改动', '基线 %d 行' % len(bl),
        '当前 %d 行；新增 e6l %d；其他 %s；已跟踪改动 %s' % (len(cur), len(new_e6l), sorted(other), tracked_mod),
        not other and not tracked_mod and bl <= cur)
    kn = dict(chain_wave=sum(1 for l in bl if re.search(r'(chain|wave)[0-9]*\.sh$', l)),
              single_factor=sum(1 for l in bl if l.endswith('.py') and '/' not in l),
              exec_briefs=sum(1 for l in bl if 'exec_briefs/' in l))
    chk('A1-6', 'git status 基线构成', 'brief §1.1 / A1-6 写 7 + 3 + 11 + 2（另有本轮决策端交接件）', '7 / 3 / 13+', json.dumps(kn), None,
        note='基线 = 开工时 git status 原样（stage0/git_status_baseline.txt）')

    # ---------------- A1-7
    v = L.env_versions()
    for k, want in ENV_LOCK.items():
        chk('A1-7', 'env.%s' % k, '版本 = brief W14', want, v.get(k), v.get(k) == want)
    chk('A1-7', 'env.polars', '若用须写版本 + 纯 numpy 回退（本轮不依赖）', 'NOT_REQUIRED', v.get('polars'), None)
    blas = {k: os.environ.get(k) for k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS')}
    chk('A1-7', 'BLAS 线程', '≤ 4（e6l_boot）', '≤ 4', json.dumps(blas), all(x is not None and int(x) <= 4 for x in blas.values()))

    df = pd.DataFrame(rows)
    p = os.path.join(OUT, 'identity_checks.csv')
    L.atomic_write_csv(p, df)
    n = df.status.value_counts().to_dict()
    ok = not (df.status == 'FAIL').any()
    L.write_receipt(TASK, [p, os.path.join(OUT, 'readonly_code_baseline.json'), os.path.join(OUT, 'guard_attack.csv'),
                           os.path.join(OUT, 'post_gate_two_way.csv')], 'SUCCEEDED' if ok else 'FAILED', counts=n, blocker=not ok)
    print(df[df.status != 'PASS'].to_string(max_colwidth=90), flush=True)
    print(n, 'OK' if ok else 'FAIL', flush=True)
    return 0 if ok else 2


def gate_two_way():
    """post_gate 在临时 RES 里两向实测（E6k lessons 17 / 纪律 51）：伪造 registration 文件，只写 TRIAL。"""
    tmp = os.path.join(L.TRIAL, 'post_gate_two_way')
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(os.path.join(tmp, 'registration'))
    rows = []
    old = L.RES
    L.RES = tmp
    try:
        def case(name, expect_pass, seg='2019-2023'):
            try:
                L.post_gate(seg, 'two-way ' + name)
                got = 'PASS'
            except RuntimeError as e:
                got = 'RAISE ' + str(e)[:60]
            rows.append(dict(case=name, expect='PASS' if expect_pass else 'RAISE', got=got, ok=(got == 'PASS') == expect_pass))
        case('无授权文件 → 拒绝', False)
        case('推导段不拦', True, seg='2010-2014')
        man = os.path.join(tmp, 'registration', L.MANIFEST_B)
        json.dump({'x': 1}, open(man, 'w'))
        json.dump({'mode': 'B'}, open(os.path.join(tmp, 'registration', L.AUTH_PRE), 'w'))
        case('有授权、缺条件回执 → 拒绝', False)
        json.dump(dict(all_pass=True, frozen_manifest_sha256=L.sha_file(man)), open(os.path.join(tmp, 'registration', L.AUTH_COND), 'w'))
        case('授权 + 条件全过 + 清单 sha 相同 → 放行', True)
        json.dump({'x': 2}, open(man, 'w'))
        case('清单 sha 已变 → 拒绝', False)
        json.dump(dict(all_pass=False, frozen_manifest_sha256=L.sha_file(man)), open(os.path.join(tmp, 'registration', L.AUTH_COND), 'w'))
        case('条件未全过 → 拒绝', False)
    finally:
        L.RES = old
    L.atomic_write_csv(os.path.join(OUT, 'post_gate_two_way.csv'), pd.DataFrame(rows))
    return rows


def guard_attack():
    """E6k 九入口（G1–G7 含 b 子项）逐项重做 + 本轮 G8 e6l post_gate / G9 推导段限定 / G10 全程缓存入口 / G11 状态序列入口 / G12 连续面板入口。"""
    ga = os.path.join(OUT, 'guard_attack')
    os.makedirs(ga, exist_ok=True)
    rows = []

    def add(gid, entry, attack, ok, detail=''):
        rows.append(dict(entry_id=gid, entry=entry, attack=attack, ok=bool(ok), detail=str(detail)[:200]))

    def raises(fn):
        try:
            fn()
        except (RuntimeError, ValueError, AssertionError) as e:
            return True, repr(e)[:160]
        return False, 'no exception'

    import e6j_prod as PR
    calls = []
    orig = PR.load_all_daily_data
    PR.load_all_daily_data = lambda *a, **k: calls.append((a, k))
    PR.PERIODS['__ATTACK__'] = ('20260301', '20260410')
    ok, why = raises(lambda: PR.build_period('__ATTACK__'))
    add('G1', 'e6j_prod.build_period', "段 ('20260301','20260410')", ok and not calls, '%s; load calls=%d' % (why, len(calls)))
    del PR.PERIODS['__ATTACK__']
    PR.load_all_daily_data = orig
    import e6f_core as F
    ok, why = raises(lambda: F.guarded_load('20260301', '20260401'))
    add('G2', 'e6f_core.guarded_load（seg_i 唯一取数口）', "guarded_load('20260301','20260401')", ok, why)
    import e6j_slot as SL
    fake = os.path.join(ga, 'fake_cache', '2024-2026')
    os.makedirs(fake, exist_ok=True)
    arr = np.zeros((3, 2))
    for nm in ('FAKE__OBS', 'FAKE_J'):
        pth = os.path.join(fake, nm + '.npy')
        np.save(pth, arr)
        meta = dict(shape=[3, 2], sha256=L.sha_file(pth), max_feature_date='2026-04-01', segment='2024-2026', synthetic=True)
        json.dump(meta, open(pth.replace('.npy', '.json'), 'w'))
    o3, o4 = SL.E6I_CACHE, SL.J_CACHE
    SL.E6I_CACHE = SL.J_CACHE = os.path.join(ga, 'fake_cache')
    ok, why = raises(lambda: SL.e6i_member_raw('2024-2026', 'FAKE'))
    add('G3', 'e6j_slot.e6i_member_raw', 'sidecar max_feature_date=2026-04-01', ok, why)
    ok, why = raises(lambda: SL.j_member_raw('2024-2026', 'FAKE_J'))
    add('G4', 'e6j_slot.j_member_raw', 'sidecar max_feature_date=2026-04-01', ok, why)
    SL.E6I_CACHE, SL.J_CACHE = o3, o4
    ok, why = raises(lambda: J.assert_index_ok(pd.Index([20260325, 20260327, 20260330]), 'attack'))
    add('G5', 'e6j_core.assert_index_ok', '索引含 20260330', ok, why)
    ok2, _ = raises(lambda: J.assert_index_ok(pd.Index([20260325, 20260327]), 'ok'))
    add('G5b', 'e6j_core.assert_index_ok', '合法索引（止于 20260327）不应误报', not ok2)
    import e6j_random as R
    cal = pd.Index(pd.to_datetime(pd.read_csv(os.path.join(L.E6J_RES, 'registry', 'trade_calendar.csv')).date))
    ok, why = raises(lambda: R.Grid(pd.to_datetime(['2026-03-27', '2026-03-30']), ['000001.SZ'], cal))
    add('G6', 'e6j_random.Grid / day_index', '日期 2026-03-30 不在日历', ok, why)
    add('G6b', 'E6j registry/trade_calendar.csv', '日历末日', str(cal.max().date()) <= L.MARKET_DATA_END_MAX, str(cal.max().date()))
    led = pd.read_parquet(os.path.join(L.E6J_RES, 'anchors', 'mother_ledger_prod_v2.parquet'), columns=['date'])
    add('G7a', 'E6j anchors/mother_ledger_prod_v2.parquet', '账本末日', led.date.max() <= L.MARKET_DATA_END_MAX, led.date.max())
    mx = max(json.load(open(p))['max_feature_date'] for p in glob.glob(os.path.join(L.E6J_RES, 'cache', '*', '*.json')))
    add('G7b', 'E6j cache/<段>/J_*.json', 'J 成员 max_feature_date 最大值', mx <= L.MARKET_DATA_END_MAX, mx)
    tmp_res = os.path.join(L.TRIAL, 'guard_empty_res')
    os.makedirs(os.path.join(tmp_res, 'registration'), exist_ok=True)
    old = L.RES
    L.RES = tmp_res
    ok, why = raises(lambda: L.post_gate('2019-2023', 'attack'))
    L.RES = old
    add('G8', 'e6l_core.post_gate', '无 E6l 授权文件时计算后段新对象', ok, why)
    ok, why = raises(lambda: L.deriv_only('2024-2026', 'attack'))
    add('G9', 'e6l_core.deriv_only', '推导段限定步骤调用后段', ok, why)
    try:
        ST = importlib.import_module('e6l_state')
    except ImportError as e:
        add('G10', 'e6l_state.load_full（全程缓存入口）', '模块缺', False, repr(e))
        add('G11', 'e6l_state.state_series（状态序列入口）', '模块缺', False, repr(e))
    else:
        ok, why = raises(lambda: ST.load_full(end='20260410'))
        add('G10', 'e6l_state.load_full（全程缓存入口）', "end='20260410'", ok, why)
        ok, why = raises(lambda: ST.assert_state_dates(pd.to_datetime(['2026-03-27', '2026-03-30'])))
        add('G11', 'e6l_state.assert_state_dates（状态序列入口）', '状态日期含 2026-03-30', ok, why)
        ok, why = raises(lambda: ST.full_period_ctx(end='20260410', dry_run=True))
        add('G12', 'e6l_state.full_period_ctx（连续面板源上下文入口）', "end='20260410'", ok, why)
        ok2, _ = raises(lambda: ST.full_period_ctx(end='20260327', dry_run=True))
        add('G12b', 'e6l_state.full_period_ctx', "end='20260327' 不应误报", not ok2)
    df = pd.DataFrame(rows)
    L.atomic_write_csv(os.path.join(OUT, 'guard_attack.csv'), df)
    return rows


if __name__ == '__main__':
    sys.exit(main())
