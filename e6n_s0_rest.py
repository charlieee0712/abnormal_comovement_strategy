# -*- coding: utf-8 -*-
"""E6n Stage 0 其余各类与收尾（brief §2；附录 A1 / A2 / A3 / A4 / A5 / A6 / A7-1 / A7-10 / A7-12）。除 c2 的源对象锚（已评对象，SECOND_EVALUATION）
与 A4-4 前向标签函数复现外不读收益；新对象一律只到名单层。状态词：PASS / FAIL / SOURCE_WAIT / INFO / NOT_RUN（e6m_stage0_S.Book 同表头）。
  c1        A1-1 交接件 sha；A1-2 外部输入（e6m_stage0_S.a1_2 原样复用 + 本轮新增读取件）→ registry/external_inputs_E6n.csv；A1-3 授权与两向；
            A1-4（e6m_stage0_S.a1_4 + E6m 部署日志末版 sha + git）；A1-5 E7 守卫攻击矩阵（e6m_stage0_S.a1_5 G1–G17 原样 + 本轮 N1–N10）；A1-6 环境锁
  c2        A2-1 六形态 α = 0 → pool2 逐字节；A2-3 R2 / A06 / 六形态对 E6j 锚；A2-4 锚对象段 D 对 policy_E6m；A2-5 源 Q 回退 / 跳过日；
            A2-6 Q0 × 三记忆 × α .25 × H5 的 LEGACY / ISK 逐路径对 E6m randoms（E6m 代码在进程内重放，不写 E6m 目录）
  c3        A3-1…A3-13（名单层 / 合成）；A3-5 四账户闭合 = --a35（推导段账户后回填）
  c4        A4-1…A4-5   c5 随机层登记与合成演示   c6 A6-1…A6-4   contract data_contract / data_request / A7-12   imports import 闭包
  close     汇总 → stage0/stage0_summary.csv + stage0/stage0_gate.json（all_pass = 无 FAIL / SOURCE_WAIT / NOT_RUN；INFO 不计）"""
import os
import re
import sys
import glob
import json
import time
import pickle
import shutil
import hashlib
import tarfile
import argparse
import subprocess

import numpy as np
import pandas as pd

import e6n_core as N

E6M_W = N.E6M_WORK
RES = N.RES_ROOT
E6J = os.path.join(RES, '20260927_0038_E6j_k_two_dimension_pilot')
E6L = os.path.join(RES, '20260930_1141_E6l_time_memory_stage')
E6K = os.path.join(RES, '20260928_2325_E6k_k_binding_stage')
E6I = os.path.join(RES, '20260923_0254_E6i_measurement_need_fit')
E5A = os.path.join(RES, '20260903_1214_delivery_pools_v2')
FORMS6 = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')


def S0mod():
    """E6m 阶段 S 的 Stage 0 模块（只读复用；E6M_WORK 指 E6m 工作目录只为读其 refs / 缓存，所有写出改到本轮目录）。"""
    os.environ['E6M_WORK'] = E6M_W
    import e6m_stage0_S as S0
    return S0


def book():
    return S0mod().Book()


def out_dir(c):
    d = N.P('stage0', c)
    os.makedirs(d, exist_ok=True)
    return d


def snapshot_e6m():
    """E6m 工作目录的轻量快照（文件数 + 最新 mtime），用于证明 Stage 0 复用 E6m 代码时没写 E6m 目录。"""
    n, mt = 0, 0.0
    for dp, dn, fn in os.walk(E6M_W):
        for f in fn:
            n += 1
            try:
                mt = max(mt, os.path.getmtime(os.path.join(dp, f)))
            except OSError:
                pass
    return n, mt


# ====================================================================== c1
def a1_1(B):
    d = N.P('handoff_in')
    lst = os.path.join(d, 'exec_briefs', 'E6n_HANDOFF_SHA256.txt')
    for ln in open(lst, encoding='utf-8'):
        p = ln.split()
        if len(p) < 2 or not re.fullmatch(r'[0-9a-f]{64}', p[0]):
            continue
        sha, rel = p[0], ' '.join(p[1:])
        cands = [os.path.join(d, rel)] + glob.glob(os.path.join(d, '**', os.path.basename(rel)), recursive=True)
        f = next((c for c in cands if os.path.isfile(c)), None)
        got = N.sha_file(f) if f else 'MISSING'
        B.ok('A1-1', rel, 'sha256 = E6n_HANDOFF_SHA256.txt', sha[:16], got[:16], got == sha)
    pc = N.P('PLAN_COPY.md')
    raw = open(pc, 'rb').read()
    B.ok('A1-1', 'PLAN_COPY.md', 'sha256 / 字节 / 行', '%s / 149086 / 1535' % N.PLAN_SHA256[:16],
         '%s / %d / %d' % (hashlib.sha256(raw).hexdigest()[:16], len(raw), raw.count(b'\n')),
         hashlib.sha256(raw).hexdigest() == N.PLAN_SHA256 and len(raw) == 149086 and raw.count(b'\n') in (1534, 1535))
    sp = N.P('stage0', 'plan_tests', 'e6n_spec_tests.py')
    s = open(sp, 'rb').read()
    B.ok('A1-1', 'stage0/plan_tests/e6n_spec_tests.py', 'sha256 前缀 / 行', '14c3991f / 635', '%s / %d' % (hashlib.sha256(s).hexdigest()[:8], s.count(b'\n')),
         hashlib.sha256(s).hexdigest().startswith('14c3991f') and s.count(b'\n') in (634, 635))


def replica_index():
    out = {}
    for f in glob.glob(os.path.join(E6M_W, 'replica', 'replica_manifest_P*_final.json')):
        for r in json.load(open(f, encoding='utf-8')).get('files', []):
            out[r['path']] = r['sha256']
    return out


def ext_inputs(B, H):
    """本轮实际读取的外部输入（brief A8）：sha + 参照（E6m 副本包清单 / E6m 外部输入表 / 各轮 MIRROR）→ registry/external_inputs_E6n.csv。"""
    S0 = S0mod()
    rep = replica_index()
    e6m_x = pd.read_csv(os.path.join(E6M_W, 'registry', 'external_inputs_E6m.csv'), keep_default_na=False)
    x24 = {os.path.basename(p): s for p, s in zip(e6m_x.path, e6m_x.sha256) if s}
    mirrors = {}
    for rn in ('E6i', 'E6j', 'E6k', 'E6l'):
        mp_ = os.path.join(S0.refs_dir(), '%s_MIRROR.md5' % rn)
        mirrors[rn] = S0.mirror_rd(mp_) if os.path.exists(mp_) else {}
    rows = []

    def add(xid, path, purpose, step, ref_kind, ref=None):
        sha = H.one(path) if os.path.isfile(path) else None
        if sha is None:
            st, refv = 'SOURCE_WAIT', ''
        elif ref is None:
            st, refv = 'INFO', '无上一轮清单条目（sha 只登记）'
        else:
            refv = ' | '.join(ref) if isinstance(ref, (list, tuple)) else ref
            st = 'PASS' if (sha in ref if isinstance(ref, (list, tuple)) else sha == ref) else 'FAIL'
        rel = N.san(os.path.relpath(path, RES)) if path.startswith(RES) else N.san(path)
        rows.append(dict(id=xid, path=rel, purpose=purpose, read_step=step, sha256=sha or '', ref_kind=ref_kind, ref_sha256=str(refv)[:200], status=st))
        if st in ('PASS', 'FAIL'):
            B.add('A1-2', rel, 'sha = %s' % ref_kind, str(refv)[:16], (sha or '')[:16], st)
        elif st == 'SOURCE_WAIT':
            B.add('A1-2', rel, '原件存在', '存在', '缺', 'SOURCE_WAIT')
    for seg in N.SEGMENTS:
        add('Y01', os.path.join(E6M_W, 'tmp', 'ctx_%s.pkl' % seg), '段上下文（源 build_period 落盘件）：pool0 / clean / pcond / log_mcap / 行业', 'meas / masks / B1-0', 'E6m 副本包', rep.get('tmp/ctx_%s.pkl' % seg))
        for f in FORMS6 + ('R2', 'A06'):
            add('Y02', os.path.join(E6M_W, 'masks', seg, '%s.npz' % f), 'E6m 名单（A2-4 / A2-8 名单层锚）', 'Stage 0 c2', 'E6m 副本包 P1',
                rep.get('masks/%s/%s.npz' % (seg, f)))
            add('Y03', os.path.join(E6M_W, 'accounts', seg, '%s.npz' % f), 'E6m 账户（A2-4 账户层锚）', 'Stage 0 c2', 'E6m 副本包 P1',
                rep.get('accounts/%s/%s.npz' % (seg, f)))
        add('Y04', os.path.join(E6M_W, 'results', 'full', 'random_refs_%s.csv' % seg), 'E6m 随机参照（原资格 e随机复用：同对象）', '政策', 'E6m 副本包',
            rep.get('results/full/random_refs_%s.csv' % seg))
        for dom in ('POOL0', 'CLEAN', 'A4B_CVRV5_GATE_IN', 'A4B_CVRV5_REJECTED'):
            p = os.path.join(E6M_W, 'stageN', 'B3_prelim', 'work', 'events_%s__%s.npz' % (seg, dom))
            add('Y05', p, 'E6m B3 事件标签 / 调节变量（B1-0 只取派生段）', 'B1-0', 'E6m 副本包', rep.get(os.path.relpath(p, E6M_W)))
        for nm in ('J_B1_qCC', 'J_B2_POINT_TR_RANGE'):
            for ext in ('npy', 'json'):
                rel = 'cache/%s/%s.%s' % (seg, nm, ext)
                add('X04', os.path.join(E6J, rel), 'E6j 成员缓存（Q 源原值 / K_RANGE_SOURCE 桥）', 'meas', 'E6j MIRROR', mirrors['E6j'].get(rel))
        for ext in ('npy', 'json'):
            rel = 'cache/%s/C_clv20__OBS.%s' % (seg, ext)
            add('X03b', os.path.join(E6I, rel), 'E6i 成员缓存（CLV20_SOURCE 桥）', 'meas', 'E6i MIRROR', mirrors['E6i'].get(rel))
    add('Y06', os.path.join(E6M_W, 'results', 'full', 'policy_E6m.csv'), 'E6m 政策表（A2-4 逐值锚）', 'Stage 0 c2', 'E6m 副本包', rep.get('results/full/policy_E6m.csv'))
    add('Y07', os.path.join(E6M_W, 'stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), 'E6m 全程状态缓存（B2 触发重建）', 'B2', 'E6m 副本包',
        rep.get('stage0/cache_cloud/state_full_E6m_cloud.npz'))
    add('Y08', os.path.join(E6M_W, 'stageS_dev', 'b6', 'b6_triggers_full.npz'), 'E6m B6 触发面板（B2 触发重建对照）', 'B2', 'E6m 副本包',
        rep.get('stageS_dev/b6/b6_triggers_full.npz'))
    add('X05', os.path.join(E6J, 'registry', 'trade_calendar.csv'), '全样本交易日历（随机 P5 绝对日序）', '随机', 'E6j MIRROR', mirrors['E6j'].get('registry/trade_calendar.csv'))
    add('X07', os.path.join(E6J, 'stage0', 'anchor2_rerun', 'e6i_parent_anchor.csv'), 'R2 / A06 母体锚（A2-3）', 'Stage 0 c2', 'E6j MIRROR',
        mirrors['E6j'].get('stage0/anchor2_rerun/e6i_parent_anchor.csv'))
    add('X08', os.path.join(E6J, 'carried', 'leader_six_forms_capital.csv'), '六形态资本锚（A2-3）', 'Stage 0 c2', 'E6j MIRROR',
        mirrors['E6j'].get('carried/leader_six_forms_capital.csv'))
    add('X11', os.path.join(E6K, 'results', 'full', 'policy_E6k.csv'), 'E6k 政策表（A2-4 第三层）', 'Stage 0 c2', 'E6k MIRROR',
        mirrors['E6k'].get('results/full/policy_E6k.csv'))
    add('X17', os.path.join(E6L, 'results', 'full', 'policy_E6l.csv'), 'E6l 政策表（A2-4 第二层）', 'Stage 0 c2', 'E6l MIRROR',
        mirrors['E6l'].get('results/full/policy_E6l.csv'))
    for f in sorted(glob.glob(os.path.join(E5A, 'pool2_*.csv'))) + [os.path.join(E5A, 'pool1_I11_screening.csv')]:
        add('X10', f, 'E5a 交付池原件（A2-1 逐字节锚）', 'Stage 0 c2', '（逐字节锚在 c2 核）', None)
    add('X01', os.path.join(RES, '20260904_1051_E6_wide_scan', 'roles.csv'), 'e6e_core 模块级读取（源账户侧 import 期）', 'import', 'E6m 文本重建（a1_2 核）', None)
    dc = N.DATA_CACHE
    for f in ('daily_kline_20100101_20260327.parquet', 'daily_kline_20100104_20141231.parquet', 'daily_kline_20150101_20181231.parquet',
              'daily_kline_20190101_20231231.parquet', 'daily_kline_20240101_20260327.parquet', 'ftl_flag_buy.parquet', 'ftl_flag_sell.parquet',
              'ftl_flag_st_new.parquet', 'ftl_industry_zx_1_all.parquet', 'ftl_limitDownPrice.parquet', 'ftl_limitUpPrice.parquet'):
        add('X24', os.path.join(dc, f), '日频缓存（段 / 全程；官方价 / 行业 / 涨跌停）', 'meas / B2 / 源段', 'E6m 外部输入表', x24.get(f))
    # 分钟分区：抽样复算 sha 对分区清单
    import e6n_meas as ME
    pr = ME.panel_root()
    pm = json.load(open(os.path.join(pr, 'panel_manifest.json'), encoding='utf-8'))
    man = pd.read_csv(os.path.join(pr, 'partition_manifest.csv'), keep_default_na=False)
    rng = np.random.default_rng(N.stable_seed_int('E6n.A1-2.partition_sample') % (2 ** 63))
    pick = man.iloc[np.sort(rng.choice(len(man), size=min(60, len(man)), replace=False))]
    import e6n_minute as MN
    bad = 0
    for r in pick.itertuples():
        s = H.one(os.path.join(MN.root(), r.file))
        bad += s != r.sha256
    B.ok('A1-2', '分钟分区（%d 个源文件；清单 sha %s）' % (len(man), pm['partition_manifest_sha256'][:16]), '抽样 60 个源文件复算 sha = 分区清单', '0 不一致',
         '%d 不一致' % bad, bad == 0)
    rows.append(dict(id='M01', path='<分钟源根>/{1,5}min/<YYYYMMDD>/*.csv（%d 个文件，%s..%s）' % (len(man), pm['first'], pm['last']),
                     purpose='分钟 OHLCV 分区（ETL 一次拉取，读取接口截断 ≤ 2026-03-27）', read_step='ETL', sha256=pm['partition_manifest_sha256'],
                     ref_kind='分区清单 sha（本轮 ETL 落盘；抽样复算 60 个）', ref_sha256=pm['partition_manifest_sha256'], status='PASS' if bad == 0 else 'FAIL'))
    for nm, why in (('分钟指数（000852 / 000985 / 000300）', 'A13：源分钟表中这三个代码是同号股票，无宽基指数分钟 bar → UNKNOWN'),
                    ('交易所 / 板块历史映射', '代码前缀推断（6 = 沪；0 / 3 = 深；688 = 科创；300 / 301 = 创业）；无历史映射表 → SOURCE_WAIT'),
                    ('竞价 / 盘后标志', '源分钟表 09:25 竞价独立行；无盘后行（A7-11 实测）；无显式标志列 → 规则识别'),
                    ('成交额单位字典', '实测：量 = 股、额 = 元（A7-4 对日频）；无官方字典 → 实测登记'),
                    ('修订规则 / 版本号', '源目录无版本 / 修订说明 → SOURCE_WAIT（分区清单 sha 作数据指纹）')):
        rows.append(dict(id='M02', path=nm, purpose='数据合同字段', read_step='Stage 0 第 7 类', sha256='', ref_kind='', ref_sha256='',
                         status='UNKNOWN' if '指数' in nm else ('SOURCE_WAIT' if 'SOURCE_WAIT' in why else 'INFO'), note=why))
    df = pd.DataFrame(rows)
    p = N.P('registry', 'external_inputs_E6n.csv')
    N.atomic_write_csv(p, N.to_status(df))
    return df


def a1_3(B):
    import e6n_gate as GT
    p = N.P('registration', GT.AUTH_STATUS)
    ok = os.path.exists(p) and json.load(open(p, encoding='utf-8')).get('user_quote') == GT.USER_QUOTE
    B.ok('A1-3', 'registration/' + GT.AUTH_STATUS, '方式 B 登记 = 用户原话照录', GT.USER_QUOTE, 'OK' if ok else '缺 / 不符', ok)
    tw = pd.read_csv(N.P('stage0', 'a1_3_post_gate_two_way.csv'), keep_default_na=False)
    B.ok('A1-3', 'e6n_gate.post_gate 两向', '%d 例全对' % len(tw), len(tw), int(tw.ok.astype(str).eq('True').sum()), bool(tw.ok.astype(str).eq('True').all()))
    tmp = N.P('tmp', 'deriv_ready_two_way')
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    res = []
    for name, files, expect in (('无冻结 / 无 seal_B1_0 → 拒绝', (), False), ('只有冻结 → 拒绝', (GT.FREEZE,), False),
                                ('冻结 + seal_B1_0 → 放行', (GT.FREEZE, GT.SEAL_B10), True)):
        for f in files:
            open(os.path.join(tmp, f), 'w').write('{}')
        try:
            GT.deriv_ready('2010-2014', 'two-way', root=tmp)
            got = True
        except RuntimeError:
            got = False
        res.append(got == expect)
        B.ok('A1-3', 'e6n_gate.deriv_ready', name, 'PASS' if expect else 'RAISE', 'PASS' if got else 'RAISE', got == expect)
    shutil.rmtree(tmp, ignore_errors=True)


def a1_4_extra(B, H):
    lg = pd.read_csv(os.path.join(E6M_W, 'code_register', 'deploy_log.csv'), keep_default_na=False)
    last = lg.groupby('file').tail(1).set_index('file')
    bad = []
    for f, r in last.iterrows():
        cur = H.one(os.path.join(N.CODE, f))
        if cur != r.sha256:
            bad.append(f)
    B.ok('A1-4', 'E6m 部署日志末版（%d 个 e6m 文件）' % len(last), '当前 sha = E6m 最后一次部署', '0 不一致', '%d：%s' % (len(bad), bad[:5]), not bad)
    g = lambda *a: subprocess.run(['git', '-c', 'safe.directory=%s' % os.path.realpath(N.CODE), '--no-optional-locks'] + list(a), cwd=N.CODE,
                                  capture_output=True, text=True).stdout.strip()
    head, om = g('rev-parse', 'HEAD'), g('rev-parse', 'origin/main')
    porc = g('status', '--porcelain', '--untracked-files=no')
    B.ok('A1-4', 'git HEAD', 'HEAD = origin/main（E6l 交付提交；E6m 无交付提交 → 待决 P01）', om[:12], head[:12], head == om and bool(head))
    B.ok('A1-4', 'git 已跟踪改动', 'status --porcelain --untracked-files=no 为空', 0, len([x for x in porc.split('\n') if x.strip()]), not porc.strip())


def guard_e6n(tmp):
    """本轮新增入口的 E7 守卫攻击（合成未来日期 / 伪造面板，只写 tmp）。"""
    import e6n_minute as MN
    import e6n_meas as ME
    import e6n_b2 as B2
    import e6n_gate as GT
    rows = []

    def add(gid, entry, attack, ok, detail=''):
        rows.append(dict(entry_id=gid, entry=entry, attack=attack, status='PASS' if ok else 'FAIL', detail=N.san(str(detail))[:200]))

    def raises(fn):
        try:
            fn()
        except (RuntimeError, ValueError, AssertionError) as e:
            return True, repr(e)[:160]
        return False, 'no exception'
    os.makedirs(tmp, exist_ok=True)
    ok, why = raises(lambda: MN.read_day(20260330, 5))
    add('N1', 'e6n_minute.read_day（分钟读取：5 分钟主网格）', 'read_day(20260330, 5)', ok, why)
    ok, why = raises(lambda: MN.read_day(20260330, 1))
    add('N2', 'e6n_minute.read_day（1 / 10 分钟桥：10 分钟端点取自 1 分钟表）', 'read_day(20260330, 1)', ok, why)
    ok, why = raises(lambda: MN.day_features(20260330))
    add('N3', 'e6n_minute.day_features（逐日全部分钟量：路径 / 8 格 / 六点价 / 481 源桥 / 1·10 分钟桥）', 'day_features(20260330)', ok, why)
    ok, why = raises(lambda: MN.read_day(20260330, 5))
    add('N4', '分钟指数（A13：无独立指数表，000852 / 000985 / 000300 只能经 read_day 取列）', 'read_day(20260330, 5) 取指数列', ok, why)
    ok, why = raises(lambda: MN.read_day(20260330, 1))
    add('N5', '盘后固定价格标志（A7-11：源无盘后行与标志列；任何盘后识别经 read_day 1 分钟表）', 'read_day(20260330, 1) 查 15:00 后行', ok, why)
    fake = os.path.join(tmp, 'fake_panel')
    os.makedirs(os.path.join(fake, 'Y2026'), exist_ok=True)
    np.save(os.path.join(fake, 'Y2026', 'dates.npy'), np.array([20260327, 20260330], np.int64))
    np.save(os.path.join(fake, 'Y2026', 'codes.npy'), np.array(['000001'], dtype='U6'))
    open(os.path.join(fake, 'panel_manifest.json'), 'w').write('{}')
    orig = ME.panel_root
    ME.panel_root = lambda: fake
    try:
        ok, why = raises(lambda: ME.load_minute(np.array([20260327, 20260330]), np.array(['000001'], dtype='U6'), fields=('pl_5',)))
        add('N6', 'e6n_meas.load_minute（基线预热：b20 / PRE20 / 8 格 profile 的全日历面板）', '伪造面板含 20260330', ok, why)
    finally:
        ME.panel_root = orig
    fp = os.path.join(tmp, 'fake_daily.parquet')
    pd.DataFrame(dict(trade_date=pd.to_datetime(['2026-03-27', '2026-03-30']), stock_code=['000001', '000001'], open=[1.0, 1.0], close=[1.0, 1.0],
                      high=[1.0, 1.0], low=[1.0, 1.0], lclose=[1.0, 1.0], is_open=[1, 1], volume=[1.0, 1.0])).to_parquet(fp)
    od = ME.DAILY
    ME.DAILY = fp
    try:
        ok, why = raises(ME.load_daily)
        add('N7', 'e6n_meas.load_daily（日频官方价：d / 官方桥 / 基线）', '伪造日频缓存含 2026-03-30', ok, why)
    finally:
        ME.DAILY = od
    ft = os.path.join(tmp, 'fake_triggers.npz')
    np.savez(ft, dates=np.array(['2026-03-27', '2026-03-30']), columns=np.array(['000001']), sell=np.ones((2, 1), bool))
    ok, why = raises(lambda: B2.load_triggers(ft))
    add('N8', 'e6n_b2.load_triggers（B2 冻结源风险集 / 触发面板唯一入口）', '伪造触发面板含 2026-03-30', ok, why)
    emp = os.path.join(tmp, 'gate_empty')
    os.makedirs(emp, exist_ok=True)
    ok, why = raises(lambda: GT.deriv_ready('2010-2014', 'attack', root=emp))
    add('N9', 'e6n_gate.deriv_ready（推导段账户 / 随机 / 统计入口）', '无冻结与 seal_B1_0', ok, why)
    ok, why = raises(lambda: GT.post_gate('2024-2026', 'attack', root=emp))
    add('N10', 'e6n_gate.post_gate（后段账户 / 随机 / 统计入口）', '无授权文件', ok, why)
    mx = max(MN.list_days(5))
    add('N11', 'e6n_minute.list_days（ETL 日集；元数据）', '缺省日集末日 ≤ 截止', mx <= N.MARKET_DATA_END_INT, mx)
    return rows


def a1_6(B):
    import scipy
    import statsmodels
    import numba
    from scipy.optimize import linear_sum_assignment  # noqa: F401
    from scipy.spatial.distance import jensenshannon  # noqa: F401
    exp = dict(python='3.10.13', numpy='1.26.1', pandas='2.2.3', scipy='1.11.3', statsmodels='0.14.0', numba='0.58.1')
    got = dict(python=sys.version.split()[0], numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__, statsmodels=statsmodels.__version__,
               numba=numba.__version__)
    for k in exp:
        B.ok('A1-6', k, '版本', exp[k], got[k], exp[k] == got[k])
    for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        v = os.environ.get(k, '')
        B.ok('A1-6', k, 'BLAS 线程 ≤ 4', '≤ 4', v or '未设', v.isdigit() and int(v) <= 4)
    B.add('A1-6', 'scipy.optimize.linear_sum_assignment / scipy.spatial.distance.jensenshannon / pandas.merge_asof', '版本记录', '', 'scipy %s / pandas %s'
          % (scipy.__version__, pd.__version__), 'INFO')


def task_c1():
    S0 = S0mod()
    B = book()
    od = out_dir('c1')
    H = S0.Hasher(8)
    root = S0.default_root()
    before = snapshot_e6m()
    a1_1(B)
    S0.a1_2(B, root, H, S0.refs_dir())
    ext_inputs(B, H)
    a1_3(B)
    S0.a1_4(B, root, H, S0.refs_dir())
    a1_4_extra(B, H)
    B.out = od
    tmp = N.P('tmp', 'stage0_guard_attack')
    S0.a1_5(B, root, tmp)
    g6m = pd.read_csv(os.path.join(od, 'guard_attack.csv'), keep_default_na=False)
    g6n = pd.DataFrame(guard_e6n(N.P('tmp', 'stage0_guard_attack_e6n')))
    shutil.rmtree(N.P('tmp', 'stage0_guard_attack_e6n'), ignore_errors=True)
    for r in g6n.itertuples():
        B.add('A1-5', r.entry, r.attack, 'raise / 静态末日 ≤ 截止', r.detail, r.status)
    G = pd.concat([g6m.assign(round='E6m 入口（e6m_stage0_S.a1_5 原样）'), g6n.assign(round='E6n 新入口')], ignore_index=True)
    N.atomic_write_csv(os.path.join(od, 'guard_attack_E6n.csv'), G)
    a1_6(B)
    after = snapshot_e6m()
    B.ok('A1-5', 'E6m 工作目录', '复用 E6m Stage 0 代码前后文件数 / 最新 mtime 不变（未写 E6m 目录）', str(before), str(after), before == after)
    return B, 'c1'


# ====================================================================== c2
def seg_cells(seg):
    z = np.load(N.P('meas', seg, 'cells_t.npy')), np.load(N.P('meas', seg, 'cells_c.npy'))
    return z


def a2_1(B):
    import e6j_prod as PR
    parts = {f: [] for f in PR.DELIV}
    for seg in N.SEGMENTS:
        with open(os.path.join(E6M_W, 'tmp', 'ctx_%s.pkl' % seg), 'rb') as fh:
            ctx = pickle.load(fh)
        p0 = ctx['p0']
        cc = np.flatnonzero(p0.any(0))
        t, c = seg_cells(seg)
        for f in PR.DELIV:
            z = np.load(N.P('masks', seg, '%s.npz' % f), allow_pickle=False)
            keys = [str(k) for k in z['mask_keys']]
            n = int(z['n_cells'][0])
            F = np.unpackbits(z['final_bits'][keys.index('NONE|a0|NATIVE')])[:n].astype(bool)
            M_ = np.zeros(p0.shape, bool)
            M_[t[F], cc[c[F]]] = True
            hold, w = PR.weights_of(ctx, M_)
            parts[f].append(PR.pool2_part(ctx, w))
        del ctx
    tz = os.path.join(N.CODE, 'delivery', 'I11_candidate_pools_v2_20260903', 'I11_candidate_pools_v2_20260903.tar.gz')
    mem = {}
    if os.path.exists(tz):
        with tarfile.open(tz, 'r:gz') as tf:
            for m in tf.getmembers():
                if m.isfile() and m.name.endswith('.csv'):
                    mem[os.path.basename(m.name)] = hashlib.sha256(tf.extractfile(m).read()).hexdigest()
    rows = []
    for f in PR.DELIV:
        fn = 'pool2_%s.csv' % PR.FNAME[f]
        b, dfp = PR.pool2_bytes(parts[f])
        s = hashlib.sha256(b).hexdigest()
        rp = os.path.join(E5A, fn)
        ref = N.sha_file(rp) if os.path.exists(rp) else None
        B.ok('A2-1', fn, '六形态 α = 0（本轮 NATIVE 名单 → 源 DEV → pool2 字节）= E5a 结果目录原件', (ref or 'MISSING')[:16], s[:16], s == ref)
        B.ok('A2-1', fn, '= 仓库交付包同名成员', mem.get(fn, 'MISSING')[:16], s[:16], s == mem.get(fn))
        rows.append(dict(file=fn, rows=len(dfp), bytes=len(b), sha256=s, e5a_results_sha256=ref or 'MISSING', repo_member_sha256=mem.get(fn, 'MISSING')))
    N.atomic_write_csv(N.P('stage0', 'c2', 'a2_1_pool2_bytes.csv'), pd.DataFrame(rows))


def acct_ann(seg, form):
    z = np.load(N.P('stage0', 'anchor_accounts', seg, '%s.npz' % form), allow_pickle=False)
    return z


def a2_3_a2_4(B):
    """A2-3：R2 / A06 原父段 net8 年化 = E6j e6i_parent_anchor；六形态原父 = E6j 领导表。A2-4：本轮锚对象（源对象，已逐日 = E6m 账户）段 D = policy_E6m（1e−9）。"""
    pa = pd.read_csv(os.path.join(E6J, 'stage0', 'anchor2_rerun', 'e6i_parent_anchor.csv'), keep_default_na=False)
    ld = pd.read_csv(os.path.join(E6J, 'carried', 'leader_six_forms_capital.csv'), keep_default_na=False)
    N.atomic_write_json(N.P('stage0', 'c2', 'a2_3_ref_columns.json'), dict(parent_anchor=pa.columns.tolist(), leader=ld.columns.tolist()))
    pol = pd.read_csv(os.path.join(E6M_W, 'results', 'full', 'policy_E6m.csv'), keep_default_na=False)
    pol = pol.set_index('desc_id')
    import e6n_s0_anchor_acct as AA
    worst, n, miss = 0.0, 0, 0
    nat = {}
    for seg in N.SEGMENTS:
        for f in FORMS6 + ('R2', 'A06'):
            z = acct_ann(seg, f)
            ids = [str(x) for x in z['desc']]
            net = z['d_net8']
            for j, did in enumerate(ids):
                p = did.split('|')
                if p[0] == 'STRONG_ANCHOR' or p[1] == 'ORIGINAL':
                    nat[(seg, f, p[4])] = net[j]
            for j, did in enumerate(ids):
                p = did.split('|')
                if p[0] == 'STRONG_ANCHOR' or p[1] == 'ORIGINAL':
                    continue
                e = AA.e6m_id(did)
                if e not in pol.index:
                    miss += 1
                    continue
                par = nat.get((seg, f, p[4]))
                if par is None:
                    continue
                ok = np.isfinite(net[j]) & np.isfinite(par)
                D = N.ANN * float(np.mean(net[j][ok] - par[ok]))
                ref = pol.at[e, 'D_%s' % seg] if ('D_%s' % seg) in pol.columns else np.nan
                ref = float(ref) if str(ref) not in ('', 'UNDEFINED') else np.nan
                if np.isfinite(ref):
                    worst = max(worst, abs(D - ref))
                    n += 1
    B.ok('A2-4', '锚对象（Q0 / C1 × 三记忆 × 六形态 × α .125 / .25 / .5 × H 1 / 3 / 5 / 10 / 20）', '段 D = policy_E6m D_<段>（1e−9）', '≤ 1e−9',
         'max|Δ| %.2e（%d 值；E6m 无同对象 %d）' % (worst, n, miss), worst <= 1e-9 and n > 0)
    # A2-3：R2 / A06 / 六形态原父段年化 net8（本轮锚账户）vs E6j 两表（列名在 a2_3_ref_columns.json；按表内可识别列逐值比对）
    got = {k: N.ANN * float(np.nanmean(v)) for k, v in nat.items() if k[2] == 'H5'}
    rows = []
    for (seg, f, H), v in sorted(got.items()):
        rows.append(dict(segment=seg, form=f, H=H, net8_ann_pp=v))
    G = pd.DataFrame(rows)
    N.atomic_write_csv(N.P('stage0', 'c2', 'a2_3_parent_net8_E6n.csv'), G)
    cmp_rows = []
    for ref, tag in ((pa, 'E6j e6i_parent_anchor'), (ld, 'E6j leader_six_forms_capital')):
        num = [c for c in ref.columns if ref[c].dtype != object]
        keyc = [c for c in ref.columns if ref[c].dtype == object]
        for r in ref.itertuples(index=False):
            d = r._asdict()
            txt = ' '.join(str(d[c]) for c in keyc)
            for seg in N.SEGMENTS:
                for f in FORMS6 + ('R2', 'A06'):
                    if seg in txt and re.search(r'(^|[^A-Za-z0-9_])%s($|[^A-Za-z0-9_])' % re.escape(f), txt):
                        v = got.get((seg, f, 'H5'))
                        if v is None:
                            continue
                        best = min((abs(float(d[c]) - v), c) for c in num if np.isfinite(float(d[c]))) if num else (np.inf, '')
                        cmp_rows.append(dict(ref=tag, segment=seg, form=f, e6n=v, nearest_col=best[1], absdiff=best[0]))
    C = pd.DataFrame(cmp_rows)
    N.atomic_write_csv(N.P('stage0', 'c2', 'a2_3_compare.csv'), C)
    for tag in ('E6j e6i_parent_anchor', 'E6j leader_six_forms_capital'):
        sub = C[C.ref == tag] if len(C) else C
        if not len(sub):
            B.add('A2-3', tag, '段 net8 年化 = 锚表', '≤ 1e−9', '锚表无可识别 (段, 形态) 行（列见 a2_3_ref_columns.json）', 'INFO')
            continue
        w = float(sub.groupby(['segment', 'form']).absdiff.min().max())
        B.ok('A2-3', tag, '段 net8 年化 = 锚表最近列（%d 对）' % sub.groupby(['segment', 'form']).ngroups, '≤ 1e−9', 'max|Δ| %.2e' % w, w <= 1e-9)


def a2_5(B):
    import e6n_rand as RN
    for seg in N.SEGMENTS:
        t = np.load(N.P('meas', seg, 'cells_t.npy'))
        q = np.load(N.P('meas', seg, 'q0raw.npy'))
        off = np.r_[0, np.cumsum(np.bincount(t))]
        import e6n_meas as ME
        S = ME.SegM(seg)
        lm = S.cells(S.ctx['log_mcap'].reindex(index=S.pool0.index, columns=S.pool0.columns).to_numpy(float)[:, S.ccols])
        skip = raw_ret = neu = 0
        for d in range(len(off) - 1):
            a, b = off[d], off[d + 1]
            if b - a < 6:
                skip += 1
                continue
            both = np.isfinite(q[a:b]) & np.isfinite(lm[a:b])
            if both.sum() < 10 or np.var(lm[a:b][both]) < 1e-10:
                raw_ret += 1
            else:
                neu += 1
        mf = json.load(open(N.P('meas', seg, 'manifest_base.json'), encoding='utf-8'))
        qb = mf.get('q0raw_vs_J_B1_qCC', {})
        B.ok('A2-5', '%s kQ' % seg, 'q0raw = J_B1_qCC（逐位）；kQ = 源中性化 lo 秩（= E6m kQ0 逐位，meas 构建已核）', 'mismatch 0',
             'finite_mismatch %s / bitwise %s / n %s' % (qb.get('finite_mismatch'), qb.get('bitwise_equal'), qb.get('n_both')),
             qb.get('finite_mismatch') == 0 and qb.get('bitwise_equal') == qb.get('n_both'))
        B.add('A2-5', '%s 中性化分支日数' % seg, 'pool0 < 6 跳过 / 双有限 < 10 或 var < 1e−10 回原值 / 正常中性化', '', '%d / %d / %d' % (skip, raw_ret, neu), 'INFO')


def a2_6(B, npaths=64):
    """Q0 × NONE / HG10 / LAG1_10 × α .25 × H5 × 六形态（2010-2014）的 LEGACY / ISK 逐路径（前 npaths 条）= E6m randoms（同 E6m 代码进程内重放，写本轮 stage0）。"""
    S0mod()
    import e6l_fast as FA
    import e6m_s_rand_run as RR
    import e6m_s_real as RL
    import e6m_stage0_S_engine as EN
    seg_name = '2010-2014'
    seg = RL.seg_of(seg_name, 'real')
    AF = FA.AcctFast(seg)
    cal = np.load(os.path.join(E6M_W, 'stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), allow_pickle=False)['dates']
    draws = EN.make_draws(seg)
    od = N.P('stage0', 'c2', 'a2_6_randoms')
    rows = []
    for form in FORMS6:
        rt = RR.RT(seg, form, None, cal, None, None, {'Q0': seg.meas_kf('Q0')}, mem_gate=EN.source_mem_gate)
        if os.environ.get('E6M_STAGE2_FAST', '1') != '0':
            import e6j_fast as FJ
            rt.st.stage2 = FJ.stage2_fast
        own = [dict(owner_id='Q0|%s|LINEAR|-|a0.25|%s|H5|SOURCE|-' % (form, mem), H=5, aux_id='E6n_A2_6|%s|%s' % (form, mem))
               for mem in ('NONE', 'HG10', 'LAG1_10')]
        for mech in ('LEGACY_POLICY_RANDOM', 'CONTENT_ISK_P5'):
            p = os.path.join(od, mech, '%s__p0_%d.npz' % (form, npaths))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            RR.run_accounts(rt, AF, own, mech, 0, npaths, p, draws=draws)
            z = np.load(p, allow_pickle=False)
            ref = {}
            for f in sorted(glob.glob(os.path.join(E6M_W, 'randoms', mech, seg_name, '%s__p0_*.npz' % form))):
                e = np.load(f, allow_pickle=False)
                for i, did in enumerate([str(x) for x in e['desc']]):
                    ref[(did, int(e['H'][i]))] = (e['s_net'][i], e['n_net'][i])
            for i, did in enumerate([str(x) for x in z['desc']]):
                r = ref.get((did, 5))
                if r is None:
                    rows.append(dict(form=form, mech=mech, desc=did, status='FAIL', note='E6m 无同对象路径文件'))
                    continue
                a = z['s_net'][i] / np.maximum(z['n_net'][i], 1)
                b = r[0][:npaths] / np.maximum(r[1][:npaths], 1)
                d = float(np.nanmax(np.abs(a - b))) * N.ANN
                rows.append(dict(form=form, mech=mech, desc=did, paths=npaths, maxabs_ann_pp=d, n_equal=bool((z['n_net'][i] == r[1][:npaths]).all()),
                                 status='PASS' if (d <= 1e-12 and (z['n_net'][i] == r[1][:npaths]).all()) else 'FAIL'))
    df = pd.DataFrame(rows)
    N.atomic_write_csv(N.P('stage0', 'c2', 'a2_6_random_paths_vs_E6m.csv'), N.to_status(df))
    for mech, g in df.groupby('mech'):
        B.ok('A2-6', 'Q0 × 三记忆 × 六形态 %s（2010-2014，前 %d 路径）' % (mech, npaths), '逐路径年化 = E6m randoms（1e−12）', '%d 对象全过' % len(g),
             '%d PASS；max|Δ| %.2e' % (int((g.status == 'PASS').sum()), float(pd.to_numeric(g.get('maxabs_ann_pp', pd.Series([np.nan])), errors='coerce').max())),
             bool((g.status == 'PASS').all()))


def task_c2(parts):
    B = book()
    out_dir('c2')
    if 'a21' in parts:
        a2_1(B)
    if 'a234' in parts:
        a2_3_a2_4(B)
    if 'a25' in parts:
        a2_5(B)
    if 'a26' in parts:
        a2_6(B)
    m = json.load(open(N.P('stage0', 'c2_mask_anchor_E6m.json'), encoding='utf-8'))
    B.ok('A2-8', '名单层锚（stage0/c2_mask_anchor_E6m.csv）', '本轮 NATIVE / Q0 / C1 × 三记忆 × 三 α 名单 = E6m 名单逐格', 'FAIL 0',
         json.dumps(m.get('counts'), ensure_ascii=False), m.get('counts', {}).get('FAIL', 0) == 0 and m.get('counts', {}).get('PASS', 0) > 0)
    a = json.load(open(N.P('stage0', 'c2_anchor_accounts_E6m.json'), encoding='utf-8'))
    B.ok('A2-2', '锚账户（stage0/c2_anchor_accounts_E6m.csv）', '8bp 恒等 net8 = gross − 8e−4·turn（1e−12）', '≤ 1e−12', a.get('net8_identity_worst'),
         a.get('net8_identity_worst', 1) <= 1e-12)
    B.ok('A2-4', '锚账户逐日（stage0/c2_anchor_accounts_E6m.csv）', '逐日 net8 / gross / turn / pos / sc_child / sc_parent = E6m 账户', 'worst ≤ 1e−12',
         '%s；%s' % (a.get('worst'), {k: v for k, v in a.items() if k in ('PASS', 'FAIL')}), a.get('worst', 1) <= 1e-12 and a.get('FAIL', 0) == 0)
    return B, 'c2_' + '_'.join(sorted(parts))


# ====================================================================== c3（名单层 / 合成；不读收益）
def lsa_bruteforce(C):
    """≤ 12 × 12 精确最小总距离（先最大配对数 = min(a, b)，再最小总距离）：位掩码 DP（a ≤ b）。"""
    a, b = C.shape
    T = False
    if a > b:
        C = C.T
        a, b = b, a
        T = True
    INF = np.inf
    dp = {0: (0.0, ())}
    for i in range(a):
        nd = {}
        for mask, (cost, asg) in dp.items():
            for j in range(b):
                if not (mask >> j) & 1:
                    m2 = mask | (1 << j)
                    c2 = cost + C[i, j]
                    if m2 not in nd or c2 < nd[m2][0]:
                        nd[m2] = (c2, asg + (j,))
        dp = nd
    best = min(dp.values(), key=lambda x: x[0])
    return best[0]


def task_c3():
    import e6n_vars as VR
    import e6n_rand as RN
    from scipy.optimize import linear_sum_assignment
    B = book()
    out_dir('c3')
    rep = json.load(open(N.P('stage0', 'plan_tests', 'report.json'), encoding='utf-8'))
    tr = open(N.P('stage0', 'plan_tests', 'test_results.txt'), encoding='utf-8').read()
    nok = len(re.findall(r'\.\.\. ok\b', tr))
    nrun, nfail = int(rep.get('tests_run', 0)), int(rep.get('failures', 0)) + int(rep.get('errors', 0))
    B.ok('A3-1', 'plan 附录 B 合成检查（47 factor 环境）', '134 / 134', '134 run / 0 fail', '%d run / %d fail / %d ok 行；计数 %s / %s / %s / %s / %s / %s' % (
        nrun, nfail, nok, rep.get('main_descriptors'), rep.get('auxiliary_descriptors'), rep.get('primary_display'), rep.get('matched_component_controls'),
        rep.get('component_dose_controls'), rep.get('component_comparisons')), nfail == 0 and nrun == 134 and nok == 134)
    # A3-13 匹配：linear_sum_assignment vs 位掩码 DP（合成 ≤ 12 × 12）
    rng = np.random.default_rng(20261015)
    worst = 0.0
    for k in range(60):
        a, b = int(rng.integers(1, 9)), int(rng.integers(1, 13))
        C = np.round(rng.random((a, b)) * 10, 1)
        r, c = linear_sum_assignment(C)
        worst = max(worst, abs(C[r, c].sum() - lsa_bruteforce(C)))
    B.ok('A3-13', 'scipy.optimize.linear_sum_assignment', '60 个 ≤ 8 × 12 合成矩阵：总距离 = 位掩码 DP 穷举；配对数 = min(a, b)', '0', '%.2e' % worst, worst < 1e-9)
    for seg in ('2015-2018', '2024-2026'):
        RN.load_ctx(seg, ('A4b', 'M_mean3_v2'), acct=False)
        Bb = RN.CTX['B']
        # A3-2 η = 0 / λ = 0 ≡ 源 Q0：kf 逐位 = kQ；名单 = Q0 名单（三记忆）
        for v in ('FACET|PL_REL20|eta0|QGOOD|f5|d+1', 'RAW|Q_PATH|lam0|QGOOD|f5|sup:Q_PATH', 'RAW|Q_CLOSE_THIN|lam0|QGOOD|f5|sup:Q_CLOSE_THIN'):
            kf = VR.facet(Bb, v)[0] if v.startswith('FACET') else VR.raw_kf(Bb, None, v)[0]
            same = bool((np.isfinite(kf) == np.isfinite(Bb.kQ)).all() and (kf[np.isfinite(kf)] == Bb.kQ[np.isfinite(Bb.kQ)]).all())
            for form in ('A4b', 'M_mean3_v2'):
                z = np.load(N.P('masks', seg, '%s.npz' % form), allow_pickle=False)
                keys = [str(k) for k in z['mask_keys']]
                n = int(z['n_cells'][0])
                for mem in ('NONE', 'HG10', 'LAG1_10'):
                    F = RN.gate_final(form, mem, 0.25, kf[None, :], v, 'NOT_APPLICABLE')[0]
                    ref = np.unpackbits(z['final_bits'][keys.index('%s|a0.25|Q0' % mem)])[:n].astype(bool)
                    B.ok('A3-2', '%s %s %s %s' % (seg, form, v.split('|')[1], mem), 'η / λ = 0 → kf ≡ kQ 且名单 ≡ Q0|α.25 同记忆', 'kf 逐位 + 名单 0 差',
                         'kf %s；名单差 %d' % ('逐位' if same else '不同', int((F != ref).sum())), same and bool((F == ref).all()))
        # A3-3 整日缺分钟：20 个孤立日的新增内容置缺 → 当日回源评分（NONE 名单 = Q0 NONE），但 HG 的昨日 G 来自本账户（不重置）→ 缺日门名单与 Q0|HG10 门仍有分歧
        v = 'FACET|PL_REL20|eta0.25|QGOOD|f5|d+1'
        kf, act = VR.facet(Bb, v)
        days = np.unique(Bb.t[act])
        pick = days[20::max(1, len(days) // 21)][:20]
        kfm = kf.copy()
        for d in pick:
            kfm[Bb.t == d] = Bb.kQ[Bb.t == d]
        for form in ('A4b', 'M_mean3_v2'):
            z = np.load(N.P('masks', seg, '%s.npz' % form), allow_pickle=False)
            keys = [str(k) for k in z['mask_keys']]
            n = int(z['n_cells'][0])
            Gv = RN.gate_only(form, 'HG10', 0.25, kfm[None, :])[0]
            Gq = RN.gate_only(form, 'HG10', 0.25, Bb.kQ[None, :])[0]
            dt = RN.CTX['structs'][form][0].seg.ci.t[RN.CTX['structs'][form][0].ids]
            div = sum(int((Gv[dt == d] != Gq[dt == d]).any()) for d in pick)
            G0 = RN.gate_final(form, 'NONE', 0.25, kfm[None, :], v, 'NOT_APPLICABLE')[0]
            Fq0 = np.unpackbits(z['final_bits'][keys.index('NONE|a0.25|Q0')])[:n].astype(bool)
            same0 = all(bool((G0[Bb.t == d] == Fq0[Bb.t == d]).all()) for d in pick)
            B.ok('A3-3', '%s %s PL_REL20 η.25 置缺 %d 个孤立日' % (seg, form, len(pick)),
                 'NONE：缺日名单 = Q0 NONE（当日回源）；HG10：缺日门名单与 Q0 HG10 门的分歧日数 > 0（昨日 G 来自本账户、不重置）',
                 'NONE 相同；HG 分歧 > 0', 'NONE %s；HG 门分歧 %d / %d 日' % ('相同' if same0 else '不同', div, len(pick)), same0 and div > 0)
        # A3-4 MASK_CLONE：raw 类 ≡ kQ；五面克隆与全域 kQ 的差异格 / 日（覆盖效应）
        man = pd.read_csv(N.P('meas', seg, 'kf', 'kf_manifest.csv'), keep_default_na=False)
        cr = man[man.variant == 'CLONE_RAW']
        info = json.loads(cr['info'].iloc[0]) if len(cr) else {}
        B.ok('A3-4', '%s CLONE_RAW' % seg, 'raw 类 MASK_CLONE（Q0 原值替换全部新 raw）≡ 源 kQ 逐位', 'True', info.get('bitwise_equal_kQ'), info.get('bitwise_equal_kQ') is True)
        cl = man[man.variant.str.startswith('CLONE|') & ~man.variant.str.contains('K_RANGE_SOURCE|CLV20_SOURCE')]
        okv, det = [], []
        for v, x in zip(cl.variant, cl['info']):
            d_ = json.loads(x).get('clone_vs_kQ_cells_differ', 0)
            pv = VR.parse(v)
            km = Bb.get(VR.km_name(pv['feature'], pv['fr'], 1))
            gap = int((np.isfinite(Bb.kQ) & ~np.isfinite(km)).sum())
            okv.append(d_ > 0 or gap == 0)
            if d_ == 0:
                det.append('%s：差 0、覆盖缺口 %d' % (v.split('|')[1] + '|' + v.split('|')[4], gap))
        dif = [json.loads(x).get('clone_vs_kQ_cells_differ', 0) for x in cl['info']]
        B.ok('A3-4', '%s 五面 CLONE（%d 个分钟变体）' % (seg, len(cl)), 'owner 有限域内重建 Q 秩 ≠ 全域 kQ 的格数 > 0（覆盖效应）；差 = 0 只允许在该成员无覆盖缺口时',
             '有缺口 → > 0', 'min %s / max %s；%s' % (min(dif) if dif else 0, max(dif) if dif else 0, '；'.join(det[:4])), bool(okv) and all(okv))
        cb = man[man.variant.str.startswith('CLONE|') & man.variant.str.contains('K_RANGE_SOURCE|CLV20_SOURCE')]
        B.add('A3-4', '%s OHLC 桥 CLONE（%d 变体）' % (seg, len(cb)), '日频桥有限域 ≈ 全域 → 差异格数（INFO）', '',
              ' / '.join(str(json.loads(x).get('clone_vs_kQ_cells_differ', 0)) for x in cb['info']), 'INFO')
        # A3-6 DOSE 矩：逐日激活集上 mean / RMS(D_control) = mean / RMS(D_new)
        for v in ('FACET|TAIL_PUSH|eta0.25|QGOOD|f5|d+1', 'RAW|Q_PATH|lam0.25|QGOOD|f5|sup:Q_PATH'):
            kfo, act = VR.variant_kf(Bb, v)
            k0 = Bb.get('k0')
            K, info = VR.dose_K(k0, Bb.kQ, kfo, act, 0.25, Bb.t)
            Kc = VR.native_q(k0, kfo, 0.25)
            ok = act & np.isfinite(k0) & np.isfinite(K) & np.isfinite(Kc)
            w1 = w2 = 0.0
            for d in np.unique(Bb.t[ok])[:400]:
                s = ok & (Bb.t == d)
                dn, dc = Kc[s] - k0[s], K[s] - k0[s]
                if np.allclose(dc, VR.native_q(k0, Bb.kQ, 0.25)[s] - k0[s]):
                    continue
                w1 = max(w1, abs(dn.mean() - dc.mean()))
                w2 = max(w2, abs(np.sqrt((dn ** 2).mean()) - np.sqrt((dc ** 2).mean())))
            B.ok('A3-6', '%s DOSE %s' % (seg, v.split('|')[1]), '逐日激活集 mean / RMS(D_control) = D_new（1e−9）；不可构造日计数', '≤ 1e−9',
                 'mean %.1e / RMS %.1e；%s' % (w1, w2, json.dumps(info)), w1 <= 1e-9 and w2 <= 1e-9)
        # A3-7 四项变化：h_close = 0 的激活股票 normalized 仍可变（反例）；整日无激活 → 逐位回源
        v = 'RAW|Q_CLOSE_THIN|lam0.25|QGOOD|f5|sup:Q_CLOSE_THIN'
        kfo, act = VR.variant_kf(Bb, v)
        hc = Bb.get('comp_h_close_f5')
        zero = act & (hc == 0)
        chg = zero & np.isfinite(kfo) & (kfo != Bb.kQ)
        noact_days = np.setdiff1d(np.unique(Bb.t), np.unique(Bb.t[act]))
        idn = all(bool((kfo[Bb.t == d][np.isfinite(Bb.kQ[Bb.t == d])] == Bb.kQ[Bb.t == d][np.isfinite(Bb.kQ[Bb.t == d])]).all()) for d in noact_days)
        B.ok('A3-7', '%s Q_CLOSE_THIN λ.25' % seg, 'h_close = 0 的激活格 normalized_score_changed > 0（零惩罚 ≠ 分数不动）；整日无激活日 kf 逐位 = kQ',
             '反例 > 0；恒等', '零惩罚格 %d 中分数变 %d；无激活日 %d 逐位 %s' % (int(zero.sum()), int(chg.sum()), len(noact_days), idn), chg.sum() > 0 and idn)
        # A3-8 门适配器身份（masks 进程开头实核结果）
        for form in FORMS6:
            idj = json.load(open(N.P('masks', seg, 'identity_%s.json' % form), encoding='utf-8'))
            B.ok('A3-8', '%s %s' % (seg, form), '段单元 = 测量单元；st.q0 = k0；meas_kf(Q0) = kQ（逐位）', 'True ×3',
                 '%s / %s / %s' % (idj.get('cells_equal'), idj.get('k0_eq_st_q0'), idj.get('kQ_eq_meas_kf_Q0')),
                 idj.get('cells_equal') and idj.get('k0_eq_st_q0') and idj.get('kQ_eq_meas_kf_Q0'))
        RN.CTX.clear()
    # A3-9 / A7-8 官方桥；A3-10 量桶；A3-11 B2 时钟；A3-12 B3 可行
    c7 = json.load(open(N.P('stage0', 'c7_minute', 'c7_summary.json'), encoding='utf-8'))
    it = {x['item']: x for x in c7['items']}
    B.ok('A3-9', '官方桥分解（= A7-8）', '每制度期 ≥ 1,000 股票日 log(C/O) = 起点桥 + Σr + 收盘桥（1e−12）', 'PASS', it['A7-8']['status'], it['A7-8']['status'] == 'PASS')
    import e6n_meas as ME
    pr = ME.panel_root()
    worst, n, bad = 0.0, 0, 0
    for y in ('Y2014', 'Y2018', 'Y2019', 'Y2025'):
        V = np.stack([np.load(os.path.join(pr, y, 'vb%d.npy' % k)) for k in range(1, 9)], -1)
        tot = np.load(os.path.join(pr, y, 'vol_min.npy'))
        ok = np.isfinite(V).all(-1) & np.isfinite(tot)
        d = np.abs(V.sum(-1) - tot)[ok] / np.maximum(1.0, tot[ok])
        worst = max(worst, float(d.max()) if d.size else 0.0)
        n += int(ok.sum())
        bad += int((d > 1e-9).sum())
    B.ok('A3-10', '8 格量（右闭；竞价归第 1 格、15:00 撮合归第 8 格）', 'Σ 8 格 = 全天分钟量（含竞价行；相对 1e−9）', '0 超差', '%d 股票日；最大相对差 %.1e；超差 %d' % (n, worst, bad), bad == 0)
    s11 = pd.read_csv(N.P('stage0', 'a3_11_b2_clock_selftest.csv'), keep_default_na=False)
    allok = bool(s11['ok'].astype(str).eq('True').all()) if 'ok' in s11.columns else False
    B.ok('A3-11', 'B2 时钟（stage0/a3_11_b2_clock_selftest.csv）', 'a = max(最早合法卖日, T+1)；NO_EARLY_OPPORTUNITY；e_early < e_base；右删失', '全对', '%d 例' % len(s11), allok)
    mf = pd.read_csv(N.P('registration', 'mask_facts_E6n.csv'), keep_default_na=False)
    b3 = mf[mf.fact.str.startswith('b3_feasible')]
    B.ok('A3-12', 'B3 同数对照可行率（Stage A 掩码事实 %d 行）' % len(b3), '三种同数对照逐日可行份额已登记', '> 0 行', len(b3), len(b3) > 0)
    B.add('A3-5', '四账户支持桥 / 信息 × 记忆 I + R + X 逐日闭合', '1e−12（账户层）', '推导段账户后回填（--a35）', 'NOT_RUN', 'NOT_RUN',
          '需要账户；闭包门 ③ 在后段再核')
    return B, 'c3'


def task_a35():
    """A3-5 回填：推导两段（及已有的后段）账户上四账户 / 支持桥逐日闭合（e6n_stats.closure_check 的输出）。"""
    B = book()
    p = N.P('results', 'checks', 'closure_four_accounts.csv')
    if not os.path.exists(p):
        B.add('A3-5', '四账户 / 支持桥闭合', '1e−12', 'closure_four_accounts.csv', '未生成', 'NOT_RUN')
        return B, 'c3_a35'
    D = pd.read_csv(p, keep_default_na=False)
    for (seg, kind), g in D.groupby(['segment', 'kind']):
        w = float(pd.to_numeric(g.closure_maxabs, errors='coerce').max())
        B.ok('A3-5', '%s %s（%d 组）' % (seg, kind, len(g)), '逐日闭合 max|残差|', '≤ 1e−12', '%.2e' % w, w <= 1e-12)
    return B, 'c3_a35'


# ====================================================================== c4
def task_c4():
    B = book()
    out_dir('c4')
    exp = {'2010-2014': 1212, '2015-2018': 975, '2019-2023': 1214, '2024-2026': 539}
    for seg in N.SEGMENTS:
        d = np.load(N.P('meas', seg, 'dates.npy'))
        B.ok('A4-1', seg, '段日历日数（含 19 日预热的源段）', exp[seg], len(d), len(d) == exp[seg])
    c7 = json.load(open(N.P('stage0', 'c7_minute', 'c7_summary.json'), encoding='utf-8'))
    it = {x['item']: x for x in c7['items']}
    B.add('A4-2', '分钟价 vs 日频（= A7-5）', '竞价价 = 官方开盘；15:00 末成交 vs 官方收盘（按制度）；未复权同口径', '', it['A7-5']['detail'][:240], 'INFO')
    for seg in N.SEGMENTS:
        mf = json.load(open(N.P('meas', seg, 'manifest_base.json'), encoding='utf-8'))
        q = mf.get('q0raw_vs_J_B1_qCC', {})
        B.ok('A4-2', seg, 'd = |log(C/lclose)| 源口径：q0raw = J_B1_qCC 逐位', 'bitwise = n', '%s / %s' % (q.get('bitwise_equal'), q.get('n_both')),
             q.get('bitwise_equal') == q.get('n_both') and q.get('finite_mismatch') == 0)
    m = json.load(open(N.P('stage0', 'c2_mask_anchor_E6m.json'), encoding='utf-8'))
    B.ok('A4-3', 'pool0 / 六母体名单', '= E6m 名单逐格（E6m 已对 E5a pool2 逐字节）', 'FAIL 0', json.dumps(m.get('counts')), m.get('counts', {}).get('FAIL', 0) == 0)
    tf = json.load(open(N.P('b2', 'triggers_facts.json'), encoding='utf-8'))
    v = tf.get('vs_e6m_dev_panel', {})
    B.ok('A4-3', 'B2 触发 / 状态面板（E6m 源函数在 47 全程数据重建）', '= E6m 开发面板逐格', '0 差', json.dumps(v), v.get('axes_equal') and all(x == 0 for k, x in v.items() if k != 'axes_equal'))
    # A4-4 前向标签：E6m B3 事件 FWD_SOURCE h5 与源前向函数现算（2010-2014 抽 40 个形成日）
    try:
        z = np.load(os.path.join(E6M_W, 'stageN', 'B3_prelim', 'work', 'events_2010-2014__POOL0.npz'), allow_pickle=False)
        B.add('A4-4', 'E6m B3 事件标签键', '键名', '', ','.join(sorted(z.files))[:240], 'INFO')
    except Exception as e:                                                       # noqa: BLE001
        B.add('A4-4', 'E6m B3 事件标签', '可读', '', repr(e)[:120], 'FAIL')
    for seg in N.SEGMENTS:
        t = np.load(N.P('meas', seg, 'cells_t.npy'))
        d = np.load(N.P('meas', seg, 'd.npy'))
        qg = np.load(N.P('meas', seg, 'QGOOD.npy')).astype(bool)
        fin = np.isfinite(d)
        lowr = np.zeros(len(d), bool)
        import e6n_rand as RN
        off = np.r_[0, np.cumsum(np.bincount(t))]
        tr = RN.terc_mid(np.where(fin, d, np.nan), off)
        lowr = tr == 0
        per = np.bincount(t[qg], minlength=len(off) - 1)
        B.add('A4-5', seg, '真实零 d 份额 / d < ε 份额 / QGOOD 份额 / QGOOD 逐日中位 / |r| 最低三分与 QGOOD 重叠（Jaccard）', '',
              '%.4f / %.4f / %.4f / %d / %.3f' % (float((d[fin] == 0).mean()), float((d[fin] < 1e-4).mean()), float(qg.mean()), int(np.median(per)),
                                                  float((lowr & qg).sum() / max(1, (lowr | qg).sum()))), 'INFO')
    return B, 'c4'


# ====================================================================== c5
def task_c5():
    import e6n_rand as RN
    B = book()
    out_dir('c5')
    for f in sorted(glob.glob(N.P('stage0', 'c5_random', 'selftest_*.csv'))):
        D = pd.read_csv(f, keep_default_na=False)
        seg = os.path.basename(f)[9:-4]
        for item, g in D.groupby('item'):
            B.ok('A5-1/A5-2/A6' if item != 'IDENTITY_MASK_EQ_DETERMINISTIC' else 'A6-vectorization', '%s %s' % (seg, item), '逐项 PASS', len(g),
                 int((g.status == 'PASS').sum()), bool((g.status == 'PASS').all()))
    segs = {os.path.basename(f)[9:-4] for f in glob.glob(N.P('stage0', 'c5_random', 'selftest_*.csv'))}
    for s in N.SEGMENTS:
        if s not in segs:
            B.add('A5-1', s, 'selftest 已跑', '存在', '缺', 'NOT_RUN')
    M = pd.read_csv(N.P('registry', 'random_manifest_E6n.csv'), keep_default_na=False)
    D = pd.read_csv(N.P('registry', 'descriptors_E6n.csv'), keep_default_na=False)
    rm = M[M.mechanism == 'R_MEMORY']
    p72 = set(D.desc_id[(D.is_primary72.astype(str) == 'True') & (D.memory != 'NONE') & ~D.feature.isin(['Q0', 'C1'])])
    B.ok('A5-4', 'R_MEMORY 行', '只在主 72 带记忆的新行（%d）' % len(p72), len(p72), len(set(rm.obj)), set(rm.obj) == p72)
    B.ok('A5-5', 'MC 常数（e6n_rand 一处定义）', '首 1,024 / 增补 512 / 上限 8,192 / MCSE .03 ann_pp', '1024/512/8192/0.03',
         '%d/%d/%d/%g' % (RN.FIRST, RN.TOPUP, RN.MAXP, RN.MCSE_MAX), (RN.FIRST, RN.TOPUP, RN.MAXP, RN.MCSE_MAX) == (1024, 512, 8192, 0.03))
    rb = D[D.random_bound.astype(str) == 'True']
    cov = M[M.mechanism.isin(['CONTENT_IID', 'CONTENT_ISK_P5'])].groupby('obj').mechanism.nunique()
    B.ok('A5-5', '随机绑定主对象 × IID / ISK 覆盖', '每个随机绑定对象两机制都在 manifest', len(rb), int((cov.reindex(rb.desc_id).fillna(0) == 2).sum()),
         int((cov.reindex(rb.desc_id).fillna(0) == 2).sum()) == len(rb))
    qr = set(rb.desc_id[rb.random_mechanisms.str.contains('QRANGE')])
    B.ok('A5-5', 'CONTENT_QRANGE_P5 覆盖', '主 72 新行 H5 + 两适应构造 CORE 全 H', len(qr), M[M.mechanism == 'CONTENT_QRANGE_P5'].obj.nunique(),
         set(M[M.mechanism == 'CONTENT_QRANGE_P5'].obj) == qr)
    lg = M[M.mechanism == 'LEGACY_POLICY_RANDOM']
    B.ok('A5-6', 'LEGACY_POLICY_RANDOM（原资格 e随机）', '进政策表的随机绑定主对象全覆盖；合同 = E6l / E6m 新测量 P 机制（对象自身 Q 槽 kf 当日 IID 置换）', len(rb),
         lg.obj.nunique(), lg.obj.nunique() == len(rb))
    contract = dict(
        source_e_random=dict(owner='对象的 Q 槽测量（kf）', intervention='形成日内 IID 置换 kf 有限值（成员键 E6n.<变体>；E6j P 机制 path_key("E6j.P", 成员, "P_production_v2", "native", "IID", p) 同式）',
                             matching='无（当日全部有限格一层）', aggregation='路径段年化 → rand_mean / rand_sd / MCSE；rmr = real − rand_mean；资格 e随机 = 两后段 rmr ≥ 2·MCSE',
                             reuse='锚对象（Q0 / C1 × 三记忆 × α .25 × H5）= E6m random_refs 同对象（SECOND_EVALUATION，A2-6 逐路径复现）；新对象另跑本合同'),
        new_content_random=dict(mechanisms=list(RN.MECHS_CONTENT) + ['R_MEMORY'], role='诊断（不替代原资格 e随机；不新增资格门）'),
        not_isomorphic_note='新增内容随机只置换新增信息（源 Q0 / 旧 K / T / CVR 不随机），与源 e_random 的干预对象不同 → 不复用为资格项（plan §7.1 末段）')
    N.atomic_write_json(N.P('registry', 'e_random_contract_E6n.json'), contract)
    B.add('A5-6', 'registry/e_random_contract_E6n.json', '源 e_random 合同 owner / 干预 / 匹配 / 聚合登记', '', '已写', 'PASS')
    return B, 'c5'


# ====================================================================== c6
def task_c6():
    B = book()
    out_dir('c6')
    rows = []
    for f in sorted(glob.glob(N.P('task_status', '*.receipt.json'))):
        r = json.load(open(f, encoding='utf-8'))
        w = r.get('wall_s', r.get('secs'))
        if w is None:
            continue
        rows.append(dict(task=r['task_id'], wall_s=w, rss_peak_gb=r.get('rss_peak_gb', r.get('maxrss_gb', '')), written_at=r.get('written_at')))
    T = pd.DataFrame(rows)
    N.atomic_write_csv(N.P('stage0', 'c6', 'a6_1_task_timing.csv'), T)
    B.add('A6-1', '技术基准（回执实测 %d 任务）' % len(T), '读取 / 测量 / 名单 / 账户 / 随机自检耗时与 RSS；外推见 c6_extrapolation（随机试跑后补）', '', 'stage0/c6/a6_1_task_timing.csv', 'INFO')
    bad = []
    pats = re.compile(r'(^|[,|"\s])(N/A|NA|nan|NaN|null|None)([,|"\s]|$)')
    nscan = 0
    for d in ('registry', 'registration', 'stage0'):
        for f in glob.glob(N.P(d, '**', '*'), recursive=True):
            if not f.endswith(('.csv', '.json', '.md')) or os.path.getsize(f) > 50 << 20:
                continue
            nscan += 1
            txt = open(f, encoding='utf-8', errors='replace').read()
            if f.endswith('.csv'):
                try:
                    df = pd.read_csv(f, keep_default_na=False, dtype=str)
                    st = [c for c in df.columns if c.lower() in ('status', 'state', 'result', 'label')]
                    for c in st:
                        if df[c].isin(['N/A', 'NA', 'nan', 'NaN', 'null', 'None']).any():
                            bad.append('%s:%s' % (N.rel(f), c))
                except Exception:                                                # noqa: BLE001
                    pass
            elif f.endswith('.md') and pats.search(txt):
                bad.append(N.rel(f))
    B.ok('A6-2', '状态词扫描（registry / registration / stage0 的 CSV 状态列与 MD 正文；%d 文件）' % nscan, '无 N/A / NA / nan / null / None 作状态', '0', '%d：%s' % (len(bad), bad[:4]),
         not bad)
    B.add('A6-3', '列名单位约定', 'ann_pp / bp_per_h / _segavg / halfwidth_ann_pp / pct_pt / decimal / log_return', '', '交付时 SCHEMA.md 逐列核（闭包门 ⑤）', 'INFO')
    B.add('A6-4', 'SCHEMA.md dry-run', 'Stage B 骨架生成（A1-auto ㉘）', '', 'Stage B 冻结前生成', 'INFO')
    return B, 'c6'


# ====================================================================== contract（A7-1 / A7-10 / A7-12 / A14）
def task_contract():
    import e6n_meas as ME
    B = book()
    pr = ME.panel_root()
    pm = json.load(open(os.path.join(pr, 'panel_manifest.json'), encoding='utf-8'))
    c7 = json.load(open(N.P('stage0', 'c7_minute', 'c7_summary.json'), encoding='utf-8'))
    it = {x['item']: x for x in c7['items']}
    rules = sorted(glob.glob(N.P('stage0', 'c7_minute', 'rules', '*')))
    dc = dict(
        provider='47 只读公共目录（MatrixDailyFix；供应商未在源内声明 → SOURCE_WAIT）', table='{1,5,15,30,60,120}min/<YYYYMMDD>/{open,high,low,close}price.csv、turnoverVol.csv、turnoverValue.csv；本轮只读 1 / 5 分钟',
        schema='宽表：行 = bar 终点时刻（09:25 开盘竞价行 + 09:30+f…11:30 + 13:00+f…15:00），列 = 6 位代码；停牌股当日不出现',
        version='SOURCE_WAIT（源无版本号）', asof='SOURCE_WAIT（源无发布时间戳；分区清单 sha 作指纹）',
        window='%s..%s（读取接口截断 ≤ %s）' % (pm['first'], pm['last'], N.MARKET_DATA_END_MAX), cutoff=N.MARKET_DATA_END_MAX,
        coverage='首个分钟日 %s；2010-01-04..2013-07-31 无分钟（推导段 2010-2014 约 33.5%% 可覆盖）；pool0 股票日总体 %.3f（A7-6）' % (pm['first'], json.loads(it['A7-6']['detail']).get('pool0_overall', float('nan'))),
        units='量 = 股；额 = 元；分钟价 = 未复权（与日频同口径）；逐 bar（非累计），午休不重置（A7-4 实测）',
        calendar='日频缓存交易日历（分钟日 ⊂ 日频日）', auction='09:25 开盘竞价独立行（竞价价 = 官方开盘价，A7-5）；收盘集合竞价：深市全期、沪市 2018-08-20 起（14:58 / 14:59 1 分钟量 = 0，A7-9）；竞价虚拟量不入路径',
        timestamp_convention='bar 标签 = 终点（A7-2 实测：5 分钟 bar 收 = 同标签 1 分钟收；量 / 额 = (L−5, L] 1 分钟之和）；端点只向后取 ≤ 标签的最后真实成交',
        revisions='SOURCE_WAIT（源无修订说明；数据指纹 = 分区清单 sha）', sha=pm['partition_manifest_sha256'], n_source_files=pm['n_source_files'],
        index_minutes=dict(order=['000852', '000985', '000300'], chosen='UNKNOWN', reason='源分钟表中这三个代码是同号股票列，无宽基指数分钟 bar（A7-10）；β 诊断 UNKNOWN，不临时换指数'),
        regime_table=[dict(exchange='SZ', period='全样本', close_call_auction='14:57–15:00（2006-07-01 起）'),
                      dict(exchange='SH', period='< 2018-08-20', close_call_auction='无（官方收盘 = 最后一分钟成交量加权，2017 规则 4.1.3）'),
                      dict(exchange='SH', period='≥ 2018-08-20', close_call_auction='14:57–15:00')],
        rule_files=[dict(file=os.path.basename(r), sha256=N.sha_file(r)) for r in rules],
        after_hours='源分钟表止于 15:00，无盘后行 / 标志列（A7-11）；盘后固定价格成交不入路径（天然排除）',
        five_states='PATH_OK / FLAT_TRADED / NO_TRADE_PRESENT / HOLE（分钟表内）+ SUSPENDED / SOURCE_MISSING（日频 is_open 区分）',
        open_bar_fact='5 分钟 bar 开盘价在部分年份为上一根收盘沿用价 → 路径起点用竞价价或 1 分钟第一笔成交开盘价（读取器 sha %s）' % pm.get('reader_sha256', '')[:16])
    p = N.P('stage0', 'data_contract.json')
    N.atomic_write_json(p, dc)
    miss = [k for k, v in dc.items() if v in ('', None)]
    B.ok('A7-1', 'stage0/data_contract.json', '每字段有值或 SOURCE_WAIT / UNKNOWN', '0 空字段', len(miss), not miss)
    B.add('A7-10', 'data_contract.index_minutes', 'A13 顺序 000852 → 000985 → 000300', '', 'UNKNOWN（无宽基分钟指数源）', 'INFO')
    # A7-12 字段依赖表 + 可算份额
    mf = pd.read_csv(N.P('registration', 'mask_facts_E6n.csv'), keep_default_na=False)
    share = mf[mf.fact == 'computable_share_pool0'].pivot_table(index='key', columns='segment', values='value', aggfunc='first')
    dep = [('PL_REL20_f5', '5 分钟价（起点 + 47 端点）+ 过去 20 日同频 PL'), ('RV_REL20_f5', '5 分钟价 + 过去 20 日 RV'), ('TAIL_PUSH', '官方收盘 + 14:30 端点价 + 过去 20 日 |L|'),
           ('TAIL_VOL_REL20', '5 分钟量（尾盘 30 分钟 / 全天）+ 过去 20 日同制度份额'), ('JSD_PROFILE20', '5 分钟量 8 格 + 过去 20 日同制度 profile'),
           ('Q_PATH_h_path_f5', '5 分钟价（RV, E_path）+ 日频 d'), ('Q_CLOSE_THIN_h_close', '六点尾盘价（14:30…14:55）+ 官方收盘 + 尾盘量份额 + 过去 20 日份额'),
           ('PL_REL20_f1', '1 分钟价'), ('PL_REL20_f10', '1 分钟价（10 分钟端点）'), ('RV_REL20_f1', '1 分钟价'), ('RV_REL20_f10', '1 分钟价（10 分钟端点）'),
           ('Q_PATH_h_path_f1', '1 分钟价'), ('Q_PATH_h_path_f10', '1 分钟价'), ('Q_RV_sqrtRV_f5', '5 分钟价'), ('Q_RANGE_log_hl', '日频 H / L'),
           ('Q_CLOSE_LEVEL_u_close', '六点尾盘价 + 官方收盘'), ('K_RANGE_SOURCE', '日频 OHLC（E6j 缓存）'), ('CLV20_SOURCE', '日频 OHLC（E6i 缓存）')]
    rows = []
    for k, need in dep:
        r = dict(member=k, fields=need)
        for s in N.SEGMENTS:
            r['computable_share_pool0_%s' % s] = float(share.at[k, s]) if (k in share.index and s in share.columns) else np.nan
        rows.append(r)
    FD = pd.DataFrame(rows)
    N.atomic_write_csv(N.P('stage0', 'c7_minute', 'a7_12_field_dependency.csv'), FD)
    B.add('A7-12', 'stage0/c7_minute/a7_12_field_dependency.csv', '每个测量成员的字段依赖与各段可算份额', '', '%d 行' % len(FD), 'PASS')
    cov = pd.read_csv(N.P('stage0', 'c7_minute', 'a7_6_coverage_year_exchange_pool0.csv'), keep_default_na=False)
    md = ['# E6n 数据请求（stage0/data_request_E6n.md；brief A14；执行端不阻塞，缺口标未覆盖 / SOURCE_WAIT，不作因子经济失败）', '',
          '本轮在可用历史上照常做；以下缺口由决策端转用户（用户 10-03："缺任何方面的数据 我来想办法"）。', '',
          '| # | 缺口 | 影响 | 本轮处理 |', '|---|---|---|---|',
          '| 1 | 分钟数据 2010-01-04..2013-07-31（源首日 %s） | 推导段 2010-2014 只约 1/3 股票日可算五面 / 两构造；该段新对象多数日子回源 Q0 | 未覆盖日逐股回 Q0 源分支；覆盖表按年 × 交易所列出；原政策需要早段年数时标 POLICY_UNDECIDABLE_HISTORY + 可用期研究表 |' % pm['first'],
          '| 2 | 宽基分钟指数（000852 / 000985 / 000300） | TAIL_PUSH 的 β 残差诊断与公共标量减法诊断无指数 | β 诊断 UNKNOWN（A13 顺序都不可得）；主成员不剔市场，不受影响 |',
          '| 3 | 交易所 / 板块历史映射表 | 板块按代码前缀推断（无历史改板记录） | 代码前缀规则登记；改板个例不可识别 |',
          '| 4 | 竞价 / 盘后显式标志列、修订规则、数据版本号 | 竞价按 09:25 独立行规则识别；盘后无行（天然排除）；修订不可追溯 | 分区清单 sha 作数据指纹；规则识别写进 data_contract |',
          '| 5 | 成交额单位官方字典 | 无 | 实测：量 = 股、额 = 元（A7-4） |', '',
          '## 按年 × 交易所 × pool0 的分钟覆盖（A7-6；股票日份额）', '', cov.to_markdown(index=False) if hasattr(cov, 'to_markdown') else cov.to_string(index=False)]
    pr_ = N.P('stage0', 'data_request_E6n.md')
    N.atomic_write_text(pr_, '\n'.join(md) + '\n')
    B.add('A14', 'stage0/data_request_E6n.md', '数据请求（缺口五项 + 覆盖表）', '', '已写', 'PASS')
    return B, 'contract'


# ====================================================================== imports
PROBE = r'''
import sys, os, json
CODE = %(code)r
sys.path.insert(0, CODE)
opened = []
def hook(ev, args):
    if ev == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
        p = os.fsdecode(args[0])
        if not p.endswith(('.py', '.pyc', '.so', '.pth')) and '/lib/python' not in p and 'site-packages' not in p and '__pycache__' not in p:
            opened.append(os.path.realpath(p))
sys.addaudithook(hook)
before = set(sys.modules)
res = dict(target=%(t)r, ok=True, error='')
try:
    __import__(%(t)r)
except BaseException as e:
    res.update(ok=False, error='%%s: %%s' %% (type(e).__name__, str(e)[:300]))
mods = []
for m in sorted(set(sys.modules) - before):
    f = getattr(sys.modules.get(m), '__file__', None) or ''
    if f and os.path.realpath(f).startswith(os.path.realpath(CODE) + os.sep):
        mods.append(m)
res['project_modules'] = mods
res['opened_non_code'] = sorted(set(opened))
print('__JSON__' + json.dumps(res))
'''


def task_imports():
    B = book()
    rows = []
    mods = sorted(os.path.basename(f)[:-3] for f in glob.glob(os.path.join(N.CODE, 'e6n_*.py')))
    for m in mods:
        p = subprocess.run([sys.executable, '-c', PROBE % dict(code=N.CODE, t=m)], capture_output=True, text=True, cwd=N.CODE, env=dict(os.environ))
        line = [l for l in p.stdout.split('\n') if l.startswith('__JSON__')]
        r = json.loads(line[0][8:]) if line else dict(target=m, ok=False, error=N.san(p.stderr[-300:]), project_modules=[], opened_non_code=[])
        data_reads = [x for x in r['opened_non_code'] if not x.endswith(('roles.csv',)) and not x.startswith(('/dev/', '/proc/', '/etc/', '/sys/', '/usr/'))]
        e6n_side = [x for x in data_reads]
        rows.append(dict(module=m, import_ok=r['ok'], error=N.san(r.get('error', '')), project_modules=len(r['project_modules']),
                         e6e_core_in_closure='e6e_core' in r['project_modules'], opened_non_code=N.san('; '.join(r['opened_non_code'])[:400]),
                         opened_data_files_excl_known=len(e6n_side)))
        B.ok('A8', m, 'import 成功且 import 期不读数据文件（源账户侧 e6e_core 读 roles.csv 为已登记 X01）', '0 个数据文件', len(e6n_side), r['ok'] and not e6n_side,
             N.san(r.get('error', ''))[:120])
    df = pd.DataFrame(rows)
    N.atomic_write_csv(N.P('registry', 'import_closure_E6n.csv'), df)
    return B, 'imports'


# ====================================================================== close
def task_close():
    fs = sorted(glob.glob(N.P('stage0', 'checks', 'checks_*.csv')))
    D = pd.concat([pd.read_csv(f, keep_default_na=False, dtype=str).assign(table=os.path.basename(f)) for f in fs], ignore_index=True) if fs else pd.DataFrame()
    if len(D):                                   # 回填表（如 checks_c3_a35）对同一项给了 PASS / FAIL → 原表里的 NOT_RUN 占位行作废
        filled = set(D[(D.table != 'checks_c3.csv') & D.status.isin(['PASS', 'FAIL'])].item)
        D = D[~((D.status == 'NOT_RUN') & D.item.isin(filled))]
        N.atomic_write_csv(N.P('stage0', 'stage0_checks_all.csv'), D)
    S = D.groupby(['item', 'status']).size().unstack(fill_value=0).reset_index() if len(D) else pd.DataFrame()
    N.atomic_write_csv(N.P('stage0', 'stage0_summary.csv'), S)
    # c7 汇总（第 7 类在 e6n_s0_c7 已出；INFO 项为数据事实）
    c7 = json.load(open(N.P('stage0', 'c7_minute', 'c7_summary.json'), encoding='utf-8'))
    c7f = [x['item'] for x in c7['items'] if x['status'] == 'FAIL']
    cnt = D.status.value_counts().to_dict() if len(D) else {}
    bad = D[D.status.isin(['FAIL', 'SOURCE_WAIT', 'NOT_RUN'])] if len(D) else D
    g = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), counts=cnt, c7_fail=c7f, n_tables=len(fs),
             all_pass=bool(len(D) and not len(bad) and not c7f), blocking=[dict(item=r.item, object=r.object, status=r.status) for r in bad.itertuples()][:60])
    N.atomic_write_json(N.P('stage0', 'stage0_gate.json'), g)
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['c1', 'c2', 'c3', 'a35', 'c4', 'c5', 'c6', 'contract', 'imports', 'close'])
    ap.add_argument('--parts', default='a21,a234,a25,a26')
    a = ap.parse_args()
    t0 = time.time()
    if a.task == 'close':
        g = task_close()
        N.write_receipt('E6n_s0_close', [N.P('stage0', 'stage0_gate.json'), N.P('stage0', 'stage0_summary.csv')], code=[__file__], all_pass=g['all_pass'], counts=g['counts'])
        print(json.dumps({k: v for k, v in g.items() if k != 'blocking'}, ensure_ascii=False))
        for b in g['blocking'][:30]:
            print('  BLOCK', b)
        return 0
    fn = dict(c1=task_c1, c2=lambda: task_c2(set(a.parts.split(','))), c3=task_c3, a35=task_a35, c4=task_c4, c5=task_c5, c6=task_c6, contract=task_contract,
              imports=task_imports)[a.task]
    B, tag = fn()
    p = N.P('stage0', 'checks', 'checks_%s.csv' % tag)
    B.write(p)
    df = B.df()
    cnt = df.status.value_counts().to_dict()
    N.write_receipt('E6n_s0_%s' % tag, [p], code=[__file__], counts=cnt, wall_s=round(time.time() - t0, 1),
                    note='FAIL 行是检查结果（Stage 0 门在 close 汇总），不是任务失败')
    print(json.dumps(dict(task=tag, counts=cnt, wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    for r in df[df.status.isin(['FAIL', 'SOURCE_WAIT', 'NOT_RUN'])].itertuples():
        print('  %s | %s | %s | %s | %s' % (r.item, r.object[:70], r.metric[:60], str(r.got)[:80], r.status))
    return 0


if __name__ == '__main__':
    sys.exit(main())
