# -*- coding: utf-8 -*-
"""E6k Stage 0 第 1 类：身份 / 权限（brief §2 第 1 类；附录 A1-1 … A1-6；plan §13.1 第 1 条）。
A1-1 三处输入 sha 全长（本地 = 工作站现算的 stage0/local_exec_briefs_hashes.json；47 exec_briefs；结果目录 *_copy.md）+ PLAN_COPY.md 全长
A1-2 E6j 原件可读 + sha 与 E6j REVIEW_input（16 位前缀）/ E6j_MIRROR.md5（全长）一致；无参照者记 sha（INFO）
A1-3 后段授权文件（方式 A：record_B_mode_A.json；方式 B：record_B_preauthorized_E6k.json）存在且引用用户原话与日期
A1-4 四地基 + e6e–e6i + export_delivery_pools_v2.py = E6j source_manifest.code_sha256；e6j 代码 = e6j_code_sha256（提速修订后以
     code_amendment_20260927_fast.json 的 after 为准）；E6j Stage 0 之后新增的 e6j 脚本记当前 sha 作本轮只读基线（INFO）
A1-5 数据截止 2026-03-27 + E7 守卫攻击（合成未来数据 / 伪造 sidecar；覆盖 ≥ E6j 十入口 + 本轮后段授权门）
A1-6 HEAD = 82b6cf3；git status 只有开工基线里的 untracked（开工时记录 stage0/git_status_baseline.txt）
只写 E6k 结果目录；不读 2026-03-27 之后任何真实行情。"""
import e6j_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import shutil
import subprocess

import numpy as np
import pandas as pd

import e6k_core as K
import e6j_core as J

TASK = 'stage0_c1_identity' + ('_rerun' if '--rerun' in sys.argv else '')
OUT = K.P('stage0', 'c1_identity' + ('_rerun' if '--rerun' in sys.argv else ''))
EB = os.path.join(K.CODE, 'exec_briefs')
INPUTS = {  # 本地 / 47 exec_briefs 文件名 → 结果目录副本名
    'E6k_k_binding_stage.md': 'brief_copy.md',
    'E6k_brief_appendix_probes.md': 'brief_appendix_copy.md',
    'E6k_proposal.md': 'E6k_proposal_copy.md',
    'E6j_REVIEW.md': 'E6j_REVIEW_copy.md',
    'E6j_RULING_20260926.md': 'E6j_RULING_copy.md',
    'E6j_VERIFY_report.md': 'E6j_VERIFY_report_copy.md',
    'E6j_REPORT_supplement_1.md': 'E6j_REPORT_supplement_1_copy.md',
    'E6j_delivery_addendum_1.md': 'E6j_delivery_addendum_1_copy.md',
    'REVIEW_protocol_v1.md': 'REVIEW_protocol_copy.md',
    '00_协议.md': '00_协议_copy.md',
}
EXPECT_PREFIX = {  # brief §1.1 / 附录 A1-1 给出的前缀
    'E6k_k_binding_stage.md': '8be4df3d', 'E6k_brief_appendix_probes.md': '2258b2c6', 'E6k_proposal.md': '65d2b010',
    'E6j_REVIEW.md': 'b036617d', 'E6j_RULING_20260926.md': 'cb3b8a5f', 'E6j_VERIFY_report.md': '3e6345e1',
    'E6j_REPORT_supplement_1.md': '727f4892', 'E6j_delivery_addendum_1.md': '5c662cd5', 'REVIEW_protocol_v1.md': '0b15019e',
    '00_协议.md': 'f685e538'}
PLAN_FULL = '1f9e949c238b91258aea7346d22628620d7e6b9318babc7eca012290933bf3da'
HEAD = '82b6cf3'
FOUNDATION = ['data_loader.py', 'features_daily.py', 'event_study.py', 'pool_screening_v2.py']


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []

    def chk(cid, obj, metric, expected, got, ok, note='', gate=True):
        st = 'INFO' if ok is None else ('PASS' if ok else ('FAIL' if gate else 'DIFFERS'))
        rows.append(dict(check_id=cid, object=obj, metric=metric, expected=str(expected), got=str(got), status=st, note=note))

    # ---------------- A1-1
    loc = json.load(open(K.P('stage0', 'local_exec_briefs_hashes.json'), encoding='utf-8'))['files']
    for f, cp in INPUTS.items():
        s47 = K.sha_file(os.path.join(EB, f))
        dst = K.P(cp)
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(EB, f), dst)
        sres = K.sha_file(dst)
        sloc = loc.get(f, {}).get('sha256')
        ok = (s47 == sres == sloc) and s47.startswith(EXPECT_PREFIX[f])
        chk('A1-1', f, 'sha256 本地 = 47 exec_briefs = 结果目录副本 且前缀 = brief', EXPECT_PREFIX[f], '%s|%s|%s' % (sloc, s47, sres), ok)
    sp = K.sha_file(K.P('PLAN_COPY.md'))
    sl = loc.get('plans/E6k_plan_web_final.md', {}).get('sha256')
    chk('A1-1', 'PLAN_COPY.md', 'sha256 全长 = plan（本地 plans/ 与结果目录；47 仓库无 plans/）', PLAN_FULL, '%s|%s' % (sl, sp),
        sp == PLAN_FULL and sl == PLAN_FULL)

    # ---------------- A1-2
    E = K.E6J_RES
    ri = open(os.path.join(EB, 'E6j_REVIEW_input.md'), encoding='utf-8').read() if os.path.exists(os.path.join(EB, 'E6j_REVIEW_input.md')) else ''
    mir = open(os.path.join(EB, 'E6j_MIRROR.md5'), encoding='utf-8').read() if os.path.exists(os.path.join(EB, 'E6j_MIRROR.md5')) else ''
    originals = ['registration/policy_P_operational_addendum.json', 'registration/P_package_manifest.json',
                 'registration/B_package_manifest.json', 'stage0/anchor2_rerun/parent_identity_map_rerun.csv', 'verify/probe_results.csv',
                 'registration/record_B_preauthorized_E6j.json', 'registration/seal_P.json', 'registration/seal_B_post.json',
                 'registration/record_B_conditions_receipt.json', 'stage0/replay/serial.json']
    originals += sorted(os.path.relpath(p, E) for p in glob.glob(os.path.join(E, 'results_P', 'supplement_1', '*')) if os.path.isfile(p))
    e6j_orig = {}
    for r in originals:
        p = os.path.join(E, r)
        if not os.path.exists(p):
            chk('A1-2', r, '存在', True, False, False)
            continue
        s = K.sha_file(p)
        e6j_orig[r] = s
        m_ri = re.search(re.escape('`' + r + '`') + r'（([0-9a-f]{16})）', ri)
        m_mi = re.search(r'[0-9a-f]{32}\s+([0-9a-f]{64})\s+RD\s+' + re.escape(r) + r'\s*$', mir, re.M)
        if m_mi:
            chk('A1-2', r, 'sha256 = E6j_MIRROR.md5（全长）', m_mi.group(1), s, s == m_mi.group(1))
        elif m_ri:
            chk('A1-2', r, 'sha256 前缀 = E6j_REVIEW_input', m_ri.group(1), s[:16], s.startswith(m_ri.group(1)))
        else:
            chk('A1-2', r, '存在 + sha（E6j 交付清单未列 → 本轮只读基线）', '', s, None)
    dp = os.path.join(EB, 'E6j_D_probes.csv')
    s = K.sha_file(dp)
    chk('A1-2', 'exec_briefs/E6j_D_probes.csv', 'sha256 本地 = 47', loc.get('E6j_D_probes.csv', {}).get('sha256'), s,
        s == loc.get('E6j_D_probes.csv', {}).get('sha256'))

    # ---------------- A1-3
    pa = K.P('registration', 'record_B_mode_A.json'); pb = K.P('registration', 'record_B_preauthorized_E6k.json')
    if os.path.exists(pb):
        d = json.load(open(pb, encoding='utf-8'))
        chk('A1-3', rel_(pb), '方式 B 文件：引用用户原话与日期', 'user_quote + user_quote_date', '%s | %s' % (d.get('user_quote'), d.get('user_quote_date')),
            bool(d.get('user_quote')) and bool(d.get('user_quote_date')))
    elif os.path.exists(pa):
        d = json.load(open(pa, encoding='utf-8'))
        chk('A1-3', rel_(pa), '方式 A 文件：引用用户原话与日期', 'user_quote + user_quote_date', '%s | %s' % (d.get('user_quote')[:60], d.get('user_quote_date')),
            bool(d.get('user_quote')) and bool(d.get('user_quote_date')))
    else:
        chk('A1-3', 'registration/record_B_*', '授权文件存在', True, False, False)

    # ---------------- A1-4
    sm = json.load(open(os.path.join(E, 'source_manifest.json'), encoding='utf-8'))
    amend = json.load(open(os.path.join(E, 'registration', 'code_amendment_20260927_fast.json'), encoding='utf-8'))
    after = {k.split('/', 1)[1]: v for k, v in amend['files'].items() if k.startswith('after/')}
    baseline = {}
    for f, s0 in sorted(sm['code_sha256'].items()):
        s = K.sha_file(os.path.join(K.CODE, f)); baseline[f] = s
        chk('A1-4', f, 'sha = E6j source_manifest.code_sha256', s0, s, s == s0)
    for f, s0 in sorted(sm['e6j_code_sha256'].items()):
        s = K.sha_file(os.path.join(K.CODE, f)); baseline[f] = s
        m_ri = re.search(re.escape('`' + f + '`') + r'（([0-9a-f]{16})）', ri)
        if m_ri and not s0.startswith(m_ri.group(1)):
            # E6j Stage 0 之后改过、交付版本记在 E6j_REVIEW_input 且经 V（VA 探针）复现：以交付版本为准，差异登记
            chk('A1-4', f, 'sha 前缀 = E6j 交付版本（E6j_REVIEW_input；Stage 0 后改动见 E6j lessons 9）', m_ri.group(1), s[:16],
                s.startswith(m_ri.group(1)), note='E6j Stage 0 manifest 记 %s' % s0[:16])
            continue
        exp = after.get(f, s0)
        chk('A1-4', f, 'sha = E6j e6j_code_sha256（提速修订后取 after）', exp, s, s == exp)
    for f, s0 in sorted(after.items()):
        if f in baseline:
            continue
        s = K.sha_file(os.path.join(K.CODE, f)); baseline[f] = s
        chk('A1-4', f, 'sha = E6j code_amendment after', s0, s, s == s0)
    extra = sorted(os.path.basename(p) for p in glob.glob(os.path.join(K.CODE, 'e6[e-j]_*.py')) + glob.glob(os.path.join(K.CODE, 'e6*_core.py')))
    for f in extra:
        if f in baseline:
            continue
        s = K.sha_file(os.path.join(K.CODE, f)); baseline[f] = s
        chk('A1-4', f, '只读基线（E6j Stage 0 后新增或未列；本轮闭包复核不变）', '', s, None)
    for f in FOUNDATION + ['comprehensive_factor_diagnosis.py', 'export_delivery_pools_v2.py']:
        if f not in baseline:
            baseline[f] = K.sha_file(os.path.join(K.CODE, f))
    K.atomic_write_json(os.path.join(OUT, 'readonly_code_baseline.json'), dict(written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), sha256=baseline))

    # ---------------- A1-5 数据截止 + E7 守卫攻击
    cal = pd.read_csv(os.path.join(E, 'registry', 'trade_calendar.csv'))
    chk('A1-5', 'E6j registry/trade_calendar.csv', '日历末日 ≤ 2026-03-27', K.MARKET_DATA_END_MAX, cal.date.max(), cal.date.max() <= K.MARKET_DATA_END_MAX)
    g = guard_attack()
    for r in g:
        chk('A1-5', r['entry'], r['attack'], 'raise / 静态末日 ≤ 截止', r['detail'], r['ok'])

    # ---------------- A1-6
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=K.CODE, capture_output=True, text=True).stdout.strip()
    chk('A1-6', 'git HEAD', 'HEAD = 82b6cf3', HEAD, head, head.startswith(HEAD))
    stt = subprocess.run(['git', 'status', '--short'], cwd=K.CODE, capture_output=True, text=True).stdout
    base = open(K.P('stage0', 'git_status_baseline.txt'), encoding='utf-8').read()
    cur = set(l for l in stt.splitlines() if l.strip())
    bl = set(l for l in base.splitlines() if l.strip())
    new_e6k = set(l for l in cur - bl if re.match(r'^\?\? e6k_[A-Za-z0-9_]+\.py$', l))
    other = cur - bl - new_e6k
    tracked_mod = [l for l in cur if not l.startswith('??')]
    chk('A1-6', 'git status', '只有开工基线 untracked + 本轮新 e6k_*.py（未提交）；无已跟踪文件改动', '基线 %d 行' % len(bl),
        '当前 %d 行；新增 e6k %d；其他 %s；已跟踪改动 %s' % (len(cur), len(new_e6k), sorted(other), tracked_mod),
        not other and not tracked_mod and bl <= cur)

    df = pd.DataFrame(rows)
    p = os.path.join(OUT, 'identity_checks.csv'); K.atomic_write_csv(p, df)
    n = df.status.value_counts().to_dict()
    ok = not (df.status == 'FAIL').any()
    K.write_receipt(TASK, [p, os.path.join(OUT, 'readonly_code_baseline.json'), os.path.join(OUT, 'guard_attack.csv')],
                    'SUCCEEDED' if ok else 'FAILED', counts=n, blocker=not ok)
    print(df.to_string(max_colwidth=70), flush=True)
    print(n, 'OK' if ok else 'FAIL', flush=True)
    return 0 if ok else 2


def rel_(p):
    return K.rel(p)


def guard_attack():
    """E6j 十入口（G1–G7 含 b 子项）逐项重做 + 本轮 G8 后段授权门 / G9 推导段限定；伪造物写 OUT/guard_attack/。"""
    ga = os.path.join(OUT, 'guard_attack')
    os.makedirs(ga, exist_ok=True)
    rows = []

    def add(gid, entry, attack, ok, detail=''):
        rows.append(dict(entry_id=gid, entry=entry, attack=attack, ok=bool(ok), detail=str(detail)[:200]))

    def raises(fn):
        try:
            fn()
        except (RuntimeError, ValueError) as e:
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
        meta = dict(shape=[3, 2], sha256=K.sha_file(pth), max_feature_date='2026-04-01', segment='2024-2026', synthetic=True)
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
    cal = pd.Index(pd.to_datetime(pd.read_csv(os.path.join(K.E6J_RES, 'registry', 'trade_calendar.csv')).date))
    ok, why = raises(lambda: R.Grid(pd.to_datetime(['2026-03-27', '2026-03-30']), ['000001.SZ'], cal))
    add('G6', 'e6j_random.Grid / day_index', '日期 2026-03-30 不在日历', ok, why)
    add('G6b', 'E6j registry/trade_calendar.csv', '日历末日', str(cal.max().date()) <= K.MARKET_DATA_END_MAX, str(cal.max().date()))
    led = pd.read_parquet(os.path.join(K.E6J_RES, 'anchors', 'mother_ledger_prod_v2.parquet'), columns=['date'])
    add('G7a', 'E6j anchors/mother_ledger_prod_v2.parquet', '账本末日', led.date.max() <= K.MARKET_DATA_END_MAX, led.date.max())
    mx = max(json.load(open(p))['max_feature_date'] for p in glob.glob(os.path.join(K.E6J_RES, 'cache', '*', '*.json')))
    add('G7b', 'E6j cache/<段>/J_*.json', 'J 成员 max_feature_date 最大值', mx <= K.MARKET_DATA_END_MAX, mx)
    ok, why = raises(lambda: K.post_gate('2019-2023', 'attack'))
    add('G8', 'e6k_core.post_gate', '无 E6k 授权文件时计算后段新对象', ok, why)
    ok2, _ = raises(lambda: K.post_gate('2010-2014', 'ok'))
    add('G8b', 'e6k_core.post_gate', '推导段不应误报', not ok2)
    ok, why = raises(lambda: K.deriv_only('2024-2026', 'attack'))
    add('G9', 'e6k_core.deriv_only', '推导段限定步骤调用后段', ok, why)
    df = pd.DataFrame(rows)
    K.atomic_write_csv(os.path.join(OUT, 'guard_attack.csv'), df)
    return rows


if __name__ == '__main__':
    sys.exit(main())
