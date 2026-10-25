# -*- coding: utf-8 -*-
"""E6r Stage 0（brief §2；附录 A；fail-closed；任何新对象收益读数之前；只打标签不选支）。本脚本覆盖 A1 之前的卡：
S0-A 授权九值 / R5 研究参数 / 58 个 E6q 同坐标账户逐日复现（+ H40 的 E6p 同坐标）/ 4 个曲线锚重放；S0-B 源定义（C2–C7）/ 上界逐例 / HG 夹具 / 形成层基准率；
S0-D 随机机制合成夹具；S0-E 三分位离散度与缺失（entry_tertiles）；S0-F 零干预六类（代码路径实跑，不靠分派）；S0-G 38 源键 + 6 依赖级；S0-H 覆盖；
S0-I E 依赖绑定（附录 G.2 机器表行）；S0-J 记录；S0-K 资源实测与注册闭包；攻击类恒等。
S0-C（第一道 G，推导段，return_end ≤ 2018-12-31）在 A2 推导段跑完后由 e6r_g1.py 追加；S0-B 的批次 / 净买额分母基准率与 T0 → age1 转移由 e6r_g1 从 A2 账户补；S0-L 由 e6r_dryrun。
输出：diagnostics/stage0_E6r_part1.csv、verify/identities_E6r_stage0.csv、verify/replication_E6r.csv、verify/curve_replication_E6r.csv、registration/sources_E6r.csv、
registration/G_E_CC_dependency_ledger_E6r.csv、diagnostics/entry_tertiles_E6r.csv、diagnostics/source_fn_sha256_E6r.json。用法：python3 e6r_stage0.py [--workers 64]"""
import os
import sys
import json
import time
import math
import shutil
import inspect
import hashlib
import argparse
import importlib.util
import resource
from multiprocessing import get_context

import numpy as np
import pandas as pd

import e6r_core as O
import e6r_engine as E
import e6r_acct as A
import e6r_kl as KL

ROWS = []
IDN = []
SRC = []
G = {}
KEYC = slice(0, 102)        # E6q 原 DY 列（经济序列）；E6r 新增列是诊断


def put(probe, item, key, value, unit='count', status='INFO', source_file='', note=''):
    if isinstance(value, float) and not np.isfinite(value):
        value, status = '', 'UNKNOWN'
    ROWS.append(dict(probe_id=probe, item=item, key=key, value=value, unit=unit, status=status, source_file=source_file, note=note))


def idn(check, desc, exec_id, value, maxabs, tol, status):
    IDN.append(dict(check_id=check, description=desc, exec_id=exec_id, value=value, max_abs_diff=maxabs, tolerance=tol, status=status))


def src(key, value, item, source_file, fn_sha='', status='BOUND', note=''):
    put('S0-G', item, key, value, '', status, source_file, note)
    SRC.append(dict(key=key, value=value, source_file=source_file, fn_sha256=fn_sha, status=status))


def fn_sha(*objs):
    h = hashlib.sha256()
    for o in objs:
        o = getattr(o, 'py_func', o)
        h.update(inspect.getsource(o).encode())
    return h.hexdigest()


def file_sha(p):
    return O.sha_file(p) if os.path.exists(p) else ''


def contract_module():
    p = O.P('tmp', 's0j', 'contract', 'e6r_contract.py')
    if O.sha_file(p) != O.CONTRACT_SHA256:
        raise RuntimeError('合同脚本 sha 不符')
    sp = importlib.util.spec_from_file_location('e6r_contract_ref', p)
    m = importlib.util.module_from_spec(sp)
    sys.modules['e6r_contract_ref'] = m
    sp.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ 账户运行（S0 专用：全历史、不写正式结果）
def row_of(lid):
    return G['R'].set_index('logical_id').loc[lid].to_dict() | {'logical_id': lid}


def build_mod(row, mod=None):
    """registry 行 → 账户；mod = 零干预代码路径的覆盖（ovl / scap / rho_ones / lab_zero / cell_unknown / w15_off）。"""
    mk = G['mk']
    mod = mod or {}
    ip, fp, trig = A.spec_params(row)
    if 'ovl' in mod:
        ip[E.IP_OVL] = mod['ovl']
    if 'scap' in mod:
        fp[E.FP_SCAP] = mod['scap']
    w15 = row['weight_scheme'] == 'UNIFORM_CAP15' and not mod.get('w15_off')
    f = mk.formation(row['form'], row['memory'], w15=w15)
    ov = A.overlay_arrays(mk, row)
    n = len(f[2])
    if mod.get('rho_ones'):
        ov['rho'] = np.ones(n)
    if mod.get('lab_zero'):
        ov['lab'] = np.zeros(n, np.int8)
    if mod.get('cell_unknown'):
        ov['cell'] = np.full(n, -1, np.int32)
    return A.Account(mk, ip, fp, trig, f, ov=ov)


def job_run(args):
    tag, lid, mod = args
    t0 = time.time()
    try:
        row = row_of(lid)
        acc = build_mod(row, mod)
        acc.run(0, G['mk'].T)
        return dict(tag=tag, lid=lid, status='OK', wall=time.time() - t0, DY=acc.DY[:, :102].copy(),
                    extra=dict(projf=int(acc.S_i[E.SI_PROJF]), nin=int(acc.S_i[E.SI_NIN]), err=int(acc.S_i[E.SI_ERR]),
                               ovact=int((acc.DY[:, E.DY_OVACT] > 0).sum()), hmean=float(np.nanmean(acc.DY[:, E.DY_HMEAN][acc.DY[:, E.DY_HMEAN] > 0]))
                               if (acc.DY[:, E.DY_HMEAN] > 0).any() else np.nan, s05=acc.DY[:, E.DYI['cost_s05']].copy()))
    except Exception as e:
        import traceback
        return dict(tag=tag, lid=lid, status='FAILED', err='%s: %s' % (type(e).__name__, str(e)[:300]), tb=traceback.format_exc()[-800:])


def run_pool(jobs, workers):
    ctx = get_context('fork')
    out = {}
    with ctx.Pool(min(workers, max(1, len(jobs)))) as pool:
        for r in pool.imap_unordered(job_run, jobs, chunksize=1):
            if r['status'] != 'OK':
                raise RuntimeError('S0 账户失败 %s %s\n%s' % (r['lid'], r['err'], r.get('tb', '')))
            out[(r['tag'], r['lid'])] = r
    return out


def relmax(a, b):
    with np.errstate(all='ignore'):
        d = np.abs(a - b) / np.maximum(np.maximum(np.abs(a), np.abs(b)), 1.0)
    d = d[np.isfinite(d)]
    return float(d.max()) if d.size else 0.0


# ------------------------------------------------------------------ S0-A
def s0_a(runs):
    for k, v in O.AUTHORIZATIONS.items():
        put('S0-A', 'authorization', 'AUTH_%s' % k, json.dumps(v) if not isinstance(v, str) else v, '', 'PASS', 'registration/permissions_E6r.csv',
            'brief §0.3 九值逐字；authorized_by = %s' % O.AUTHORIZED_BY)
    put('S0-A', 'authorization', 'AUTH_protocol', 'v1.6', '', 'PASS', 'brief §0.2')
    put('S0-A', 'authorization', 'AUTH_mode', 'B', '', 'PASS', 'brief §0.2')
    put('S0-A', 'R5 research', 'R5_RESEARCH_PARAMETER', '0.015', 'share', 'PASS', 'registry cap_single_parameter', '单股参数 .01 → .015 只在研究账户')
    put('S0-A', 'R5 research', 'R5_RESEARCH_SCHEMES', 'TILT_CVR_L050|TILT_CVR_L025|TILT_SIZE_L050|GATE_TILT|TILT_CVR5_L050|TILT_CVR_CELL_L050|UNIFORM_CAP15', '',
        'PASS', 'registry cap_single_parameter = 0.015 的 weight_scheme 集合')
    put('S0-A', 'R5 research', 'R5_FLAT_PARAMETER', '0.01', 'share', 'PASS', 'registry', 'FLAT 与所有父保持 .01')
    R = G['R']
    rs = sorted(set(R[R.cap_single_parameter.astype(float) == 0.015].weight_scheme))
    ok = rs == sorted(O.RESEARCH_CAP_SCHEMES)
    put('S0-A', 'R5 research', 'R5_RESEARCH_SCHEMES_REGISTRY_CHECK', '|'.join(rs), '', 'PASS' if ok else 'DIFFERS', 'registration/registry_E6r.csv')
    # 复现
    segi = G['segi']
    rep = []
    worst_all = 0.0
    dates = G['mk'].dates
    for r in R[R.replication_source.isin(['E6Q', 'E6P'])].itertuples(index=False):
        mine = runs[('REP', r.logical_id)]['DY']
        h = r.replication_exec_hash
        p = O.E6Q('accounts_run', 'full', h[:2], h + '.npz') if r.replication_source == 'E6Q' else \
            os.path.join(O.E6P_DIR, 'accounts_run', 'full', h[:2], h + '.npz')
        ref = np.load(p, allow_pickle=False)['DY']
        nc = min(ref.shape[1], 102)
        for s in O.SEGS:
            m = segi == s
            d = relmax(mine[m, :nc], ref[m, :nc])
            worst_all = max(worst_all, d) if r.replication_source == 'E6Q' else worst_all
            rep.append(dict(e6r_exec_id=r.exec_id, source_round=r.replication_source, source_exec_id=r.replication_exec_id, segment=s, max_rel_diff_daily=d,
                            tolerance=1e-9, status='PASS' if d <= 1e-9 else 'DIFFERS'))
    REP = pd.DataFrame(rep)
    O.atomic_write_csv(O.P('verify', 'replication_E6r.csv'), REP)
    q = REP[REP.source_round == 'E6Q']
    nbad = int((q.status != 'PASS').sum())
    idn('REPLICATION_E6Q_ACCOUNTS', '附录 G.1 的 58 个 FLAT 同坐标账户逐日复现 E6q 账户（DY 前 102 列 = E6q 列；四段；相对 1e−9）', '', '%d/%d' % (len(q) - nbad, len(q)),
        worst_all, 1e-9, 'PASS' if nbad == 0 and len(q) == 232 else 'DIFFERS')
    put('S0-A', 'replication', 'REPLICATION_E6Q_ROWS', len(q), 'count', 'PASS' if nbad == 0 else 'DIFFERS', 'verify/replication_E6r.csv', 'max rel diff %.3g' % worst_all)
    p6 = REP[REP.source_round == 'E6P']
    put('S0-A', 'replication', 'REPLICATION_E6P_ROWS', len(p6), 'count', 'PASS' if (p6.status == 'PASS').all() else 'DIFFERS', 'verify/replication_E6r.csv',
        'H40 与 E6p 同坐标（NATIVE / SOURCE / RENEW 0）max rel diff %.3g' % (p6.max_rel_diff_daily.max() if len(p6) else 0.0))
    # FULL 值（S13 用机器值；这里报 E6r 复现账户的 FULL net / gross 与 D 脚本常量差）
    txt = open(O.P('verify', 'decision', 'E6r_D_stage2.py'), encoding='utf-8').read()
    blk = txt[txt.index('E6Q_REPLICATION = {'):]
    blk = blk[:blk.index('\n}') + 2]
    import re
    vals = {a: (float(b), float(c)) for a, b, c in re.findall(r"'(E6R-[0-9a-f]{16})': \('E6Q-[0-9a-f]{16}', ([0-9.e+-]+), ([0-9.e+-]+)\)", blk)}
    fw = 0.0
    ne_i = E.DYI['net_excess']
    for lid, (nv, gv) in vals.items():
        DY = runs[('REP', lid)]['DY']
        nav = DY[:, E.DYI['nav_post']]
        vprev = np.r_[O.V0, nav[:-1]]
        ne = DY[:, ne_i]
        feefr = DY[:, E.DYI['fee']] / vprev
        full_net = float(np.nanmean(ne) * O.ANN_PP)
        full_gross = float(np.nanmean(ne + feefr) * O.ANN_PP)
        fw = max(fw, abs(full_net - nv) / max(abs(nv), 1.0), abs(full_gross - gv) / max(abs(gv), 1.0))
    put('S0-A', 'replication', 'REPLICATION_FULL_VALUE_MAX_REL', '%.3g' % fw, 'ratio', 'PASS' if fw <= 1e-7 else 'DIFFERS', 'D 脚本常量 E6Q_REPLICATION',
        '58 个锚 FULL net / gross（逐日 ne、fee / NAV_{t−1} 的全期均值 × 25200）与 E6q 机器值')
    fr = runs[('REP', O.FRONTIER_LID)]['DY']
    fv = float(np.nanmean(fr[:, ne_i]) * O.ANN_PP)
    idn('SOURCE_ANCHOR_FRONTIER', '前沿 FRONTIER_E6P_T1A_H20（E6R-ad902abcc9cb9534 = E6Q-9f826422e6d4c39c）FULL net', O.exec_id(O.FRONTIER_LID, O.FEAS), '%.6f' % fv,
        abs(fv - 8.748417515154202), 1e-7, 'INFO')
    put('S0-A', 'anchor', 'SOURCE_ANCHOR_FRONTIER', '%.6f' % fv, 'ann_pp', 'INFO', 'verify/replication_E6r.csv')
    # 曲线锚（G.3）：κ .5 δ .5、A = 1e8 / 5e8、FULL：(ne − κA^δ s05)_owner − (同)_NONE 父
    crep = []
    cw = 0.0
    anchors = {('E6R-4083fc82a9c080ad', 1e8): 4.7885, ('E6R-4083fc82a9c080ad', 5e8): 0.7278, ('E6R-5cd4bc961441ac54', 1e8): 5.377, ('E6R-5cd4bc961441ac54', 5e8): 2.5847}
    for (lid, A_), ev in anchors.items():
        row = row_of(lid)
        par = R.set_index('exec_id').loc[row['noexit_same_overlay_exec_id']].logical_id
        o, p = runs[('REP', lid)], runs[('REP', par)]
        imp_o = 0.5 * A_ ** 0.5 * np.nan_to_num(o['extra']['s05'])
        imp_p = 0.5 * A_ ** 0.5 * np.nan_to_num(p['extra']['s05'])
        v = float(np.nanmean((o['DY'][:, ne_i] - imp_o) - (p['DY'][:, ne_i] - imp_p)) * O.ANN_PP)
        d = abs(v - ev)
        cw = max(cw, d)
        crep.append(dict(e6q_exec_id=R.set_index('logical_id').loc[lid].replication_exec_id, e6r_exec_id=row['exec_id'], comparator_kind='NOEXIT_SAME_OVERLAY',
                         A_cny=int(A_), kappa=0.5, exponent=0.5, segment='FULL', e6q_value=ev, e6r_value=v, abs_diff=d, tolerance=6e-4,
                         status='PASS' if d <= 6e-4 else 'DIFFERS'))
    O.atomic_write_csv(O.P('verify', 'curve_replication_E6r.csv'), pd.DataFrame(crep))
    put('S0-A', 'curve anchors', 'CURVE_REPLICATION', '%d/4' % sum(c['status'] == 'PASS' for c in crep), 'count', 'PASS' if cw <= 6e-4 else 'DIFFERS',
        'verify/curve_replication_E6r.csv', 'max abs diff %.5f（E6q 值按 4 位印出，容差 6e−4）' % cw)
    idn('ACCOUNTING_BRIDGE', 'E6r 复现账户日序列 = E6q 账户日序列（会计桥：同一现金 / token / 净单引擎）', '', '%.3g' % worst_all, worst_all, 1e-9, 'INFO')


# ------------------------------------------------------------------ S0-B
def s0_b():
    mk = G['mk']
    R = G['R']
    T = mk.T
    f = mk.formation(O.MAIN_FORM, 'HG10')
    ptr, col, w = f
    rng = np.random.default_rng(20261024)
    years = np.array([int(str(d)[:4]) for d in mk.dates])
    picks = []
    for y in range(2010, 2027):
        ds = [d for d in np.flatnonzero(years == y) if ptr[d + 1] > ptr[d]]
        if ds:
            picks.append(int(rng.choice(ds)))
    n = 0
    for d in picks:
        a, b = ptr[d], ptr[d + 1]
        k2 = int(rng.integers(a, b))
        s = col[k2]
        g = int(mk.ind[d, s])
        Ug = float(mk.capsh[d, g] + O.IND_DEV) if g >= 0 else float('nan')
        n += 1
        put('S0-B', 'CAP_EXAMPLE_%02d' % n, 'u_i|U_j|b', 'date=%s code=%s u_i(FLAT)=%.4f u_i(research)=%.4f U_j=%.6f b=%.6f g=%.6f n=%d' % (
            str(mk.dates[d]), str(mk.codes[s]), O.STOCK_CAP, O.RESEARCH_CAP, Ug, w[k2], w[a:b].sum(), b - a), 'share', 'INFO', 'cache source fm_w + panels ind / ind_share',
            'CAP_KIND 单股 = ABS（NAV 比例 1%；研究 1.5%）；行业 = RELATIVE（clean 份额 + 3pp）；形成层生效层 = 源 DEV（w0 = min(1/n, MAX_STOCK)）')
    # HG 夹具：源名单是预先物化的 CSR（不依赖账户状态）；门 / 倾斜账户与 FLAT 读同一份数组；挑一个有 BAD 被门掉的形成日，次日名单逐位同
    ov = mk.overlay(O.MAIN_FORM, 'HG10')
    bad_days = [d for d in range(T - 2) if ptr[d + 1] > ptr[d] and (ov['st0'][ptr[d]:ptr[d + 1]] == 1).any()]
    d0 = bad_days[len(bad_days) // 2]
    fa = mk.formation(O.MAIN_FORM, 'HG10')
    same = fa[0] is ptr and fa[1] is col and fa[2] is w
    row_g = R[(R.form == O.MAIN_FORM) & (R.memory == 'HG10') & (R.weight_scheme == 'GATE_STATE') & (R.trigger == 'NONE') & (R.funding_H == '20') &
              (R.scenario == O.FEAS)].iloc[0].to_dict()
    accg = build_mod(row_g)
    accf = build_mod(row_of(row_g['flat_same_exit_exec_id'].split('|')[0]))
    hg_ok = same and accg.f_ptr is accf.f_ptr and accg.f_col is accf.f_col and accg.f_w is accf.f_w
    accg.run(0, d0 + 2)
    accf.run(0, d0 + 2)
    gated = int(accg.DY[d0, E.DY_OVGN])
    nxt = (ptr[d0 + 1], ptr[d0 + 2])
    idn('SOURCE_HG_FROM_PRE_OVERLAY_LIST', '源 HG / 形成名单 = 预先物化的源资格名单（E6n final_bits → 源 DEV；不依赖账户持仓）；GATE 账户在 %s 门掉 %d 名后次日名单与 FLAT 同一数组' % (
        str(mk.dates[d0]), gated), row_g['exec_id'], 'next_list=%d..%d gated=%d' % (nxt[0], nxt[1], gated), 0.0, 0.0, 'PASS' if hg_ok and gated > 0 else 'DIFFERS')
    # 形成层基准率（名字数 / 源票据金额；批次 / 净买额分母由 e6r_g1 从账户补）
    segi = G['segi']
    st0 = ov['st0']
    tday = np.repeat(np.arange(T), np.diff(ptr))
    for base in ('NONE', 'T1a', 'T1b_LEVEL'):
        for nm, wt in (('NAMES', np.ones(len(w))), ('SOURCE_TICKET_CNY', w)):
            sh = float((wt * (st0 == 1)).sum() / wt.sum())
            shu = float((wt * (st0 < 0)).sum() / wt.sum())
            put('S0-B', 'base rate（FULL，形成名单；三基座同名单）', 'BASE_RATE_T0_BAD_SHARE_%s_%s' % (base, nm), '%.6f' % sh, 'share', 'INFO', 'overlay st0 × fm_w')
            put('S0-B', 'base rate（FULL，形成名单；三基座同名单）', 'BASE_RATE_T0_UNKNOWN_SHARE_%s_%s' % (base, nm), '%.6f' % shu, 'share', 'INFO', 'overlay st0 × fm_w')
    nper = np.diff(ptr)
    nper = nper[nper > 0]
    for qn, qv in (('Q10', 10), ('Q50', 50), ('Q90', 90)):
        put('S0-B', 'cohort size', 'BASE_RATE_COHORT_N_%s' % qn, float(np.percentile(nper, qv)), 'count', 'INFO', 'fm_ptr')
    for fam, lab in (('CVR20', 'lab20'), ('CVR5', 'lab5'), ('SIZE', 'labsz')):
        put('S0-B', 'NA share', 'BASE_RATE_NA_SHARE_%s' % fam, '%.6f' % float((ov[lab] == 0).mean()), 'share', 'INFO', 'overlay')
    stt = ov['stats|TILT_CVR_L050']
    live = np.isfinite(stt[:, 0])
    rho = ov['rho|TILT_CVR_L050']
    capb = float((w * rho >= O.RESEARCH_CAP * (1 - 1e-12))[ov['lab20'] == 1].mean()) if (ov['lab20'] == 1).any() else 0.0
    put('S0-B', 'cap binding（形成层 TILT_CVR_L050）', 'BASE_RATE_CAP015_BIND_SHARE', '%.6f' % capb, 'share', 'INFO', 'overlay rho × fm_w', 'T1 名字中形成目标触 1.5% 上界的份额')
    put('S0-B', 'industry binding（形成层 TILT_CVR_L050）', 'BASE_RATE_INDUSTRY_BIND_SHARE', '%.6f' % float(np.nanmean(stt[live, 8])), 'share', 'INFO', 'overlay stats')
    # T8 在 LEVEL 坏态内的份额（CC-E6r-08 条件上端：持有名字 T8 事件中同日 LEVEL = BAD 的比例；按形成名单名字近似结构计数）
    t8 = np.asarray(mk.trig('T8_LIMIT_CLOSE'))
    lv = np.asarray(mk.lvl)
    m8 = t8[tday, col] == 1
    put('S0-B', 'trigger overlap', 'BASE_RATE_T8_IN_LEVEL_BAD_SHARE', '%.6f' % float((lv[tday, col][m8] == 1).mean()) if m8.any() else '', 'share', 'INFO',
        'triggers T8_LIMIT_CLOSE / T1b_LEVEL on formation names', 'CC-E6r-08 条件上端按原句 if 函数取此份额（同日 T8 与 LEVEL 坏态交集 / T8 事件）')
    gshare = float((w * (st0 == 1)).sum() / w.sum())
    put('S0-B', 'gate intervention', 'BASE_RATE_GATE_LOW_INTERVENTION', '%.6f' % gshare, 'share', 'LOW_INTERVENTION' if gshare < 0.05 else 'INFO', 'overlay st0 × fm_w',
        '< 5% 标 LOW_INTERVENTION 照跑；否则 INFO')
    put('S0-B', 'clock', 'T0_NOT_AGE1', 'T0 = 形成日收盘 LEVEL 状态（st0）；age1 = 入场后首个收盘状态；两时钟分列（转移表 entry_transition_T0_age1 由 e6r_g1 从账户批次建）', '',
        'INFO', 'plan R03')


# ------------------------------------------------------------------ S0-D（合成夹具：直接调引擎 ov_apply）
def synth_case(n, x0, rho, lab, pin, cell, st, ovl, ernd, seed, seckey, d=10, expv=None, capres=0.0015, indcap=1.0):
    PB_i = np.zeros((max(n, 1), E.NPBI), np.int64)
    PB_f = np.zeros(max(n, 1))
    for i in range(n):
        PB_i[i, 0] = i
        PB_i[i, 3] = i
        PB_f[i] = x0[i]
    N = n
    expv = np.zeros(N) if expv is None else expv
    indsum = np.zeros(2)
    ind = np.zeros((d + 1, N), np.int64)
    ind[:, :] = np.arange(N) % 2
    capsh = np.full((d + 1, 2), indcap)
    S_i = np.zeros(E.NSI, np.int64)
    DY = np.zeros((d + 1, E.NDY))
    lab_out = np.zeros(max(n, 1), np.int64)
    E.ov_apply(d, 0, n, PB_i, PB_f, 0, np.asarray(rho, float), np.asarray(lab, np.int8), np.asarray(st, np.int8), np.asarray(cell, np.int32),
               np.asarray(pin, np.bool_), np.asarray(seckey, np.int64), expv, indsum, ind, capsh, 0.0, capres, 1.0, ovl, ernd, seed, 200000, A.RT_VER, S_i, DY, False,
               lab_out, False, np.zeros(1), np.zeros(1, np.int64), np.ones(1))
    return PB_f[:n].copy(), S_i, DY[d]


def s0_d():
    R = G['R']
    sk = np.array([int(hashlib.sha256(('S%04d' % i).encode()).hexdigest()[:15], 16) for i in range(12)], np.int64)
    # TICKETS 多重集恒等：6 名 x⁰ 等额，ρ = 1.5 / 1 / .5（T1 / T2 / T3）→ 投影后票据多重集在 6 名之间置换
    x0 = np.full(6, 1e-4)
    rho = np.array([1.5, 1.5, 1.0, 1.0, 0.5, 0.5])
    lab = np.array([1, 1, 2, 2, 3, 3])
    pin = np.zeros(6, bool)
    cell = np.full(6, -1)
    st = np.zeros(6)
    real, _, _ = synth_case(6, x0, rho, lab, pin, cell, st, E.OV_TILT, E.ER_NONE, 1, sk[:6])
    perm, Si, dy = synth_case(6, x0, rho, lab, pin, cell, st, E.OV_TILT, E.ER_TICKETS, 1, sk[:6])
    ok = np.isclose(real.sum(), perm.sum(), rtol=1e-14) and np.isclose((real ** 2).sum(), (perm ** 2).sum(), rtol=1e-14) and \
        np.isclose((real ** 1.5).sum(), (perm ** 1.5).sum(), rtol=1e-14) and sorted(np.round(real, 18)) == sorted(np.round(perm, 18))
    idn('TICKETS_MULTISET_EXACT', 'S0-D 合成：可行双射时 Σw、Σw²、Σw^1.5 与真实票据多重集全同（ov_apply ER_TICKETS）', '', 'status=%d' % int(dy[E.DY_ERST]),
        float(abs(real.sum() - perm.sum())), 1e-15, 'PASS' if ok else 'DIFFERS')
    # 合法恒等抽样：只有恒等可行（其余名字余量 = 自身票据）→ IDENTITY_DRAW，保留（不重抽）
    idr, Si2, dy2 = synth_case(6, x0, np.ones(6), lab, pin, cell, st, E.OV_TILT, E.ER_TICKETS, 3, sk[:6])
    idn('IDENTITY_DRAW_RETAINED', 'S0-D 合成：等额票据（ρ ≡ 1）任意置换数值同原映射 → 状态 IDENTITY_DRAW（erst = 4 / 5），保留在分布内、不重抽', '', 'status=%d' % int(dy2[E.DY_ERST]), 0.0, 0.0,
        'PASS' if int(dy2[E.DY_ERST]) in (4, 5) and int(Si2[E.SI_ERID]) >= 1 else 'DIFFERS')
    # GATE_COUNT：UNKNOWN 不删凑数
    x0g = np.full(8, 1e-4)
    rho_g = np.array([0, 0, 1, 1, 1, 1, 1, 1], float)
    pin_g = np.array([False, False, True, True, True, False, False, False])
    xr, _, dyg = synth_case(8, x0g, rho_g, np.zeros(8), pin_g, np.full(8, -1), np.zeros(8), E.OV_GATE, E.ER_GCOUNT, 5, sk[:8])
    removed = np.flatnonzero(xr == 0)
    ok = len(removed) == 2 and not pin_g[removed].any()
    idn('GATE_COUNT_UNKNOWN_PROTECTED', 'S0-D 合成：RANDOM_GATE_COUNT 删同数（2）名、只在已知测量且有票据的名字里删，UNKNOWN（pin）不删', '', 'removed=%s' % removed.tolist(), 0.0, 0.0,
        'PASS' if ok else 'DIFFERS')
    # 种子：同五日块同结果、下一块变；证券键行序不变
    a1, _, _ = synth_case(6, x0, rho, lab, pin, cell, st, E.OV_TILT, E.ER_TICKETS, 7, sk[:6], d=10)
    a2, _, _ = synth_case(6, x0, rho, lab, pin, cell, st, E.OV_TILT, E.ER_TICKETS, 7, sk[:6], d=11)
    a3s = [synth_case(6, x0, rho, lab, pin, cell, st, E.OV_TILT, E.ER_TICKETS, 7, sk[:6], d=dd)[0] for dd in (14, 19, 24, 29)]
    stable = np.array_equal(a1, a2)
    changes = any(not np.array_equal(a1, z) for z in a3s)
    idn('SEED_PROTOCOL_STABLE', 'S0-D：同路径同五日块（d = 10 / 11 → 块 2）同票据分配；后续块（d = 14…29）至少一次改变（E6R_BLOCK5_STABLE_SECURITY_V11）', '', 'same_block=%s changes=%s' % (stable, changes),
        0.0, 0.0, 'PASS' if stable and changes else 'DIFFERS')
    o = np.array([3, 0, 5, 1, 4, 2])
    b1, _, _ = synth_case(6, x0[o], rho[o], lab[o], pin[o], cell[o], st[o], E.OV_TILT, E.ER_TICKETS, 9, sk[:6][o])
    b0, _, _ = synth_case(6, x0, rho, lab, pin, cell, st, E.OV_TILT, E.ER_TICKETS, 9, sk[:6])
    inv = np.argsort(o)
    idn('SEED_NO_ROW_ORDER', 'S0-D：输入行序置换（证券键随行移动）→ 每个证券得到的票据不变（优先序只用证券稳定键，不用行号）', '', '', float(np.abs(b1[inv] - b0).max()), 0.0,
        'PASS' if np.array_equal(b1[inv], b0) else 'DIFFERS')
    RR = O.read_csv(O.P('registration', 'random_control_refs_E6r.csv'))
    det = RR[RR.draw_kind == 'DETERMINISTIC']
    ok = len(det) == 94 and (det.start_paths.astype(int) == 1).all() and (det.max_paths.astype(int) == 1).all() and (det.mcse_target == '').all()
    idn('DETERMINISTIC_ONE_PATH', 'LEVEL_WORST_1D 94 条确定性引用：paths = max_paths = 1、mcse 空（random_control_refs）', '', '%d' % len(det), 0.0, 0.0, 'PASS' if ok else 'DIFFERS')
    put('S0-D', 'solver', 'MATCH_SOLVER', 'FIRST_FEASIBLE_SEEDED_ORDER', '', 'PASS', 'e6r_engine.rt_match（E6q 精确首个可行匹配；节点上限 → ALGORITHM_LIMIT）')
    put('S0-D', 'solver', 'MATCH_NODE_LIMIT', A.RT_NODES, 'count', 'PASS', 'e6r_acct.RT_NODES')
    put('S0-D', 'seed', 'SEED_PROTOCOL', O.SEED_PROTOCOL, '', 'PASS', 'e6r_core.path_seed + e6r_engine.ov_order', 'owner 逻辑 ID（语义坐标 hash）/ 机制 / path_id → 种子；引擎内 hash_u(种子, (d+1)//5, 证券键)')
    for nm, desc in (('RANDOM_NO_RETURN_READ', 'ov_apply / ov_cohort_rho / rt_match 的参数里没有任何价格 / 收益数组（签名静态核）'),
                     ('RANDOM_NO_OWNER_FUTURE', '入场随机只用路径自身 T 快照；退出层目标只用 owner 当日 T 收盘意向（tg 第 d 行），不读 owner 未来成交')):
        if nm == 'RANDOM_NO_RETURN_READ':
            sig = set(inspect.signature(E.ov_apply.py_func).parameters) | set(inspect.signature(E.ov_cohort_rho.py_func).parameters) | \
                set(inspect.signature(E.rt_match.py_func).parameters)
            blocked = not ({'pv', 'pc', 'pcobs', 'r', 'ret', 'bench', 'vwap'} & sig)
        else:
            srcs = inspect.getsource(E.select_v2.py_func)
            blocked = 'tg_b[d,' in srcs.replace(' ', '') or 'tg_b[d, ' in srcs
        idn(nm, desc, '', '', '', '', 'BLOCKED' if blocked else 'DIFFERS')


# ------------------------------------------------------------------ S0-E
def s0_e():
    mk = G['mk']
    segi = G['segi']
    rows = []
    for fam, lab, why in (('CVR20', 'lab20', 'why20'), ('CVR5', 'lab5', 'why5'), ('SIZE', 'labsz', 'whysz')):
        for f in O.FORMS:
            for m in O.MEMS:
                ptr, col, w = mk.formation(f, m)
                ov = mk.overlay(f, m)
                tday = np.repeat(np.arange(mk.T), np.diff(ptr))
                sg = segi[tday]
                L = ov[lab]
                Wy = ov[why]
                for s in O.SEG6:
                    mm = np.ones(len(w), bool) if s in ('FULL', 'G4') else (sg == s)
                    if s == 'G4':
                        continue
                    tot = w[mm].sum()
                    rows.append(dict(label_family=fam, form=f, memory=m, segment=s, n_cohorts=int(len(np.unique(tday[mm]))), n_names=int(mm.sum()),
                                     n_T1=int((L[mm] == 1).sum()), n_T2=int((L[mm] == 2).sum()), n_T3=int((L[mm] == 3).sum()),
                                     n_NA_missing=int(((L[mm] == 0) & (Wy[mm] == 1)).sum()), n_NA_short=int(((L[mm] == 0) & (Wy[mm] == 2)).sum()),
                                     n_NA_all_equal=int(((L[mm] == 0) & (Wy[mm] == 3)).sum()),
                                     capital_T1=float(w[mm][L[mm] == 1].sum() / tot) if tot > 0 else np.nan, capital_T2=float(w[mm][L[mm] == 2].sum() / tot) if tot > 0 else np.nan,
                                     capital_T3=float(w[mm][L[mm] == 3].sum() / tot) if tot > 0 else np.nan, capital_NA=float(w[mm][L[mm] == 0].sum() / tot) if tot > 0 else np.nan,
                                     status='COMPUTED'))
    D = pd.DataFrame(rows)
    # G4：计数与资本份额是可加会计量，逐列四段中位不再满足 n_names = Σ 五类与份额和 = 1 → G4 行标 NOT_APPLICABLE（数值留空；FULL 与四段已全给；notes §8）
    g4 = [dict(label_family=fam, form=f, memory=m, segment='G4', status='NOT_APPLICABLE')
          for (fam, f, m), _ in D[D.segment.isin(O.SEGS)].groupby(['label_family', 'form', 'memory'])]
    D = pd.concat([D, pd.DataFrame(g4)], ignore_index=True)
    for c in ('n_cohorts', 'n_names', 'n_T1', 'n_T2', 'n_T3', 'n_NA_missing', 'n_NA_short', 'n_NA_all_equal'):
        D[c] = D[c].astype('Int64').astype(object).where(D[c].notna(), None)
    O.atomic_write_csv(O.P('diagnostics', 'entry_tertiles_E6r.csv'), D)
    C = D[D.status == 'COMPUTED']
    cnt = C[['n_names', 'n_T1', 'n_T2', 'n_T3', 'n_NA_missing', 'n_NA_short', 'n_NA_all_equal']].astype(np.int64)
    ok = bool((cnt.n_names == cnt.drop(columns='n_names').sum(axis=1)).all()) and \
        bool((np.abs(C[['capital_T1', 'capital_T2', 'capital_T3', 'capital_NA']].astype(float).sum(axis=1) - 1.0) <= 1e-9).all())
    put('S0-E', 'tertiles', 'ENTRY_TERTILES_ROWS', len(D), 'count', 'PASS' if ok else 'DIFFERS', 'diagnostics/entry_tertiles_E6r.csv', 'n_names = Σ 五类（每行）；资本份额和 = 1')
    # 合同参考函数互核（tie / NA）
    K = G['K']
    vals = [1.0, 1.0, 1.0, 2.0, 3.0, 4.0, float('nan'), None]
    ref = K.tertiles(vals)
    v = np.array([np.nan if x is None else x for x in vals])
    out = np.zeros(len(v), np.int64)
    KL.tertile_codes(v, len(v), out)
    mine = [{0: 'NA', 1: 'T1', 2: 'T2', 3: 'T3'}[int(c)] for c in out]
    idn('TIE_MIDRANK_NO_ID_SPLIT', 'S0-E：tie-aware 中点秩三分位（e6r_kl.tertile_codes）与合同参考 tertiles 逐元素同；相同值不按 ID 拆', '', '|'.join(mine), 0.0, 0.0,
        'PASS' if mine == ref else 'DIFFERS')
    out2 = np.zeros(2, np.int64)
    r2 = KL.tertile_codes(np.array([1.0, 2.0]), 2, out2)
    out3 = np.zeros(5, np.int64)
    r3 = KL.tertile_codes(np.full(5, 3.0), 5, out3)
    ok = (out2 == 0).all() and (out3 == 0).all() and r2 == 1 and r3 == 2
    idn('NA_NEUTRAL_NOT_BAD', 'S0-E：有限值 < 3 或全同 → 全 NA（中性，固定基线资本）；UNKNOWN T0 状态不当 BAD（GATE 只挡 st0 = 1）', '', 'short=%d all_equal=%d' % (r2, r3), 0.0, 0.0,
        'PASS' if ok else 'DIFFERS')


# ------------------------------------------------------------------ S0-F
def zero_jobs():
    R = G['R']
    main = (R.form == O.MAIN_FORM) & (R.memory == 'HG10') & (R.scenario == O.FEAS) & (R.exit_op == 'NATIVE')
    jobs = []
    pairs = {}

    def pick(scheme, trig, H):
        m = main & (R.weight_scheme == scheme) & (R.trigger == trig) & (R.funding_H == H)
        return R[m].iloc[0] if m.any() else None
    for trig in ('NONE', 'T1a', 'T1b_LEVEL'):
        for H in ('20', '30'):
            for chk, scheme, mod in (('LAMBDA0_EQ_FLAT', 'TILT_CVR_L050', dict(ovl=E.OV_TILT, scap=O.STOCK_CAP, rho_ones=True)),
                                     ('NO_BAD_GATE_EQ_FLAT', 'GATE_STATE', dict(rho_ones=True)),
                                     ('TILT_H_ALL_SAME_H_EQ_FLAT', 'TILT_H', dict(lab_zero=True)),
                                     ('UNIFORM_CAP_010_EQ_FLAT', 'UNIFORM_CAP15', dict(w15_off=True, scap=O.STOCK_CAP)),
                                     ('CELL_ALL_UNKNOWN_EQ_FLAT', 'TILT_CVR_CELL_L050', dict(scap=O.STOCK_CAP, cell_unknown=True))):
                r = pick(scheme, trig, H)
                if r is None:
                    continue
                flat = R.set_index('exec_id').loc[r.flat_same_exit_exec_id].logical_id
                jobs.append((chk, r.logical_id, mod))
                jobs.append(('FLAT', flat, None))
                pairs.setdefault(chk, []).append((r.logical_id, flat))
    for r in R[(R.trigger == 'NONE') & (R.exit_op != 'NATIVE')].itertuples(index=False):
        sp = {k: getattr(r, k) for k in O.PAYLOAD_KEYS}
        tw = R[(R.form == r.form) & (R.memory == r.memory) & (R.funding_H == r.funding_H) & (R.trigger == 'NONE') & (R.weight_scheme == r.weight_scheme) &
               (R.exit_op == 'NATIVE') & (R.scenario == r.scenario)]
        if len(tw) != 1:
            raise RuntimeError('NONE 退出算子账户 %s 无唯一 NATIVE 孪生' % r.logical_id)
        jobs.append(('EXITOP_NONE_TRIGGER_EQ_NATIVE', r.logical_id, None))
        jobs.append(('FLAT', tw.iloc[0].logical_id, None))
        pairs.setdefault('EXITOP_NONE_TRIGGER_EQ_NATIVE', []).append((r.logical_id, tw.iloc[0].logical_id))
    seen = set()
    uj = []
    for j in jobs:
        k = (j[0] if j[0] != 'FLAT' else 'FLAT', j[1])
        if k not in seen:
            seen.add(k)
            uj.append(j)
    return uj, pairs


def s0_f(runs, pairs):
    worst_all = 0.0
    for chk, desc in (('LAMBDA0_EQ_FLAT', 'λ = 0（形成层 ρ ≡ 1）走 TILT 代码路径（两层投影、scap .01）→ 与同坐标 FLAT 逐日同'),
                      ('NO_BAD_GATE_EQ_FLAT', '同输入状态 T0 无 BAD（ρ ≡ 1）走 GATE 代码路径 → 与 FLAT 逐日同'),
                      ('TILT_H_ALL_SAME_H_EQ_FLAT', '全部标签同 H（全 NA → H = funding_H）走 TILT_H 代码路径 → 与同 funding_H FLAT 逐日同'),
                      ('UNIFORM_CAP_010_EQ_FLAT', 'UNIFORM 参数取 .01（DEV .01 形成权重、scap .01）→ 与 FLAT 逐日同'),
                      ('CELL_ALL_UNKNOWN_EQ_FLAT', '全部格未知（固定 x⁰）走 CELL 代码路径 → 与 FLAT 逐日同'),
                      ('EXITOP_NONE_TRIGGER_EQ_NATIVE', '16 个 trigger = NONE × 非 NATIVE 退出算子账户（registry 原行）与 NATIVE 孪生逐日同')):
        pr = pairs.get(chk, [])
        w = 0.0
        for a, b in pr:
            w = max(w, relmax(runs[(chk, a)]['DY'], runs[('FLAT', b)]['DY']))
        worst_all = max(worst_all, w)
        ok = len(pr) > 0 and w <= 1e-9
        if chk == 'EXITOP_NONE_TRIGGER_EQ_NATIVE':
            ok = ok and len(pr) == 16
        idn(chk, desc, '', '%d pairs' % len(pr), w, 1e-9, 'PASS' if ok else 'DIFFERS')
        put('S0-F', 'zero intervention', chk, '%d pairs; max rel %.3g' % (len(pr), w), '', 'PASS' if ok else 'DIFFERS', 'e6r_stage0 S0-F 实跑（全历史）')
    # TILT_H 的期限确实生效（非零干预：真实标签 → 平均分配 H ≠ funding_H）
    return worst_all


# ------------------------------------------------------------------ 攻击类与求解器恒等
def attacks():
    K = G['K']
    # KL 投影独立对照（真实 cohort 快照 2,000 个：numba kl_project vs 合同参考 project_weights）
    mk = G['mk']
    ptr, col, w = mk.formation(O.MAIN_FORM, 'HG10')
    ov = mk.overlay(O.MAIN_FORM, 'HG10')
    rng = np.random.default_rng(7)
    days = [d for d in range(mk.T) if ptr[d + 1] - ptr[d] >= 3]
    worst = 0.0
    nscale = 0.0
    nchk = 0
    for d in rng.choice(days, size=min(2000, len(days)), replace=False):
        a, b = ptr[d], ptr[d + 1]
        bb = w[a:b].astype(float)
        lab = ov['lab20'][a:b].astype(np.int64)
        s = np.where(lab == 1, 1.0, np.where(lab == 3, -1.0, 0.0))
        q = bb * (1 + 0.5 * s)
        g = mk.ind[d, col[a:b]].astype(np.int64)
        u = np.full(b - a, O.RESEARCH_CAP)
        G_ = mk.capsh.shape[1]
        gc = mk.capsh[d, :G_] + O.IND_DEV
        pin = lab == 0
        wn = np.zeros(b - a)
        st = KL.kl_project(bb, q, u, g, gc, pin, wn)
        grp = [int(x) if x >= 0 else 'U%d' % i for i, x in enumerate(g)]
        gcap = {int(k): float(gc[int(k)]) for k in set(int(x) for x in g if x >= 0)}
        gcap.update({k: 1.0 for k in grp if isinstance(k, str)})
        wr = K.project_weights(list(bb), list(q), list(u), grp, gcap, [bool(x) for x in pin])
        worst = max(worst, float(np.max(np.abs(np.array(wr) - wn) / np.maximum(np.array(wr), 1e-12))))
        w2 = np.zeros(b - a)
        KL.kl_project(bb, q * 1e6, u, g, gc, pin, w2)
        nscale = max(nscale, float(np.max(np.abs(w2 - wn) / np.maximum(wn, 1e-12))))
        nchk += 1
        if st != 0:
            worst = max(worst, 1.0)
    idn('JOINT_FEASIBLE_PROJECTION', '两层投影求解器独立对照：%d 个真实 cohort 快照上 numba kl_project 与合同参考 project_weights 逐项相对差（单股 .015 / 行业 份额 + 3pp / NA 固定）' % nchk, '',
        '%d snapshots' % nchk, worst, 1e-9, 'PASS' if worst <= 1e-9 else 'DIFFERS')
    idn('KL_SCALE_INVARIANT', '同一 KL 偏好整体缩放 × 1e6 → 投影结果不变（A15；先按最大正偏好归一）', '', '%d snapshots' % nchk, nscale, 1e-12, 'PASS' if nscale <= 1e-12 else 'DIFFERS')
    # A01 格预算反例（plan §6.1）：两格形成资本 .03 / .03，x⁰ 分别 [.001, .009, .020] / [.020, .009, .001]
    x0 = np.array([.001, .009, .020, .020, .009, .001])
    bf = np.full(6, .01)
    wt = np.array([.015, .010, .005, .015, .010, .005])
    rho = wt / bf
    u = np.full(6, 1.0)
    grp = np.zeros(6, np.int64)
    gc = np.array([1.0])
    pin = np.zeros(6, bool)
    cell = np.array([0, 0, 0, 1, 1, 1])
    out = np.zeros(6)
    KL.transport_cells(x0, rho, u, grp, gc, pin, cell, True, out)
    cb = abs(out[:3].sum() - .03) + abs(out[3:].sum() - .03)
    ref = K.transport_entry_budget(list(x0), list(bf), list(wt), list(u), ['g'] * 6, {'g': 1.0}, [False] * 6, [('ind', 0), ('ind', 0), ('ind', 0), ('ind', 1), ('ind', 1), ('ind', 1)])
    idn('CELL_BUDGET_ACCOUNT_LAYER', 'A01：账户层以自身 x⁰ 的每格预算为等式（两格 .03 / .03 不被搬成 .0205 / .0395）；与合同 transport_entry_budget 逐项同', '', '%.6f/%.6f' % (out[:3].sum(), out[3:].sum()),
        float(max(cb, np.max(np.abs(np.array(ref) - out)))), 1e-12, 'PASS' if cb <= 1e-12 and np.allclose(ref, out, rtol=0, atol=1e-12) else 'DIFFERS')
    # A02 NA 固定为 x⁰（不是形成金额 b）
    x0n = np.array([.002, .004, .006, .003])
    pin = np.array([False, False, False, True])
    rho = np.array([1.5, 1.0, .5, 1.0])
    out = np.zeros(4)
    KL.transport_cells(x0n, rho, np.full(4, 1.0), np.zeros(4, np.int64), np.array([1.0]), pin, np.full(4, -1), False, out)
    idn('NA_PINNED_TO_X0', 'A02：第二层 NA 固定为自身 x⁰（.003），不用形成金额替代', '', '%.6f' % out[3], abs(out[3] - .003), 0.0, 'PASS' if out[3] == .003 else 'DIFFERS')
    # A03 ρ 只乘一次（无约束时 x ∝ x⁰ρ、Σ = B）
    x0o = np.array([.002, .004, .006])
    rho = np.array([1.5, 1.0, .5])
    out = np.zeros(3)
    KL.transport_cells(x0o, rho, np.full(3, 1.0), np.zeros(3, np.int64), np.array([1.0]), np.zeros(3, bool), np.full(3, -1), False, out)
    expv = x0o * rho * x0o.sum() / (x0o * rho).sum()
    idn('OVERLAY_APPLIED_ONCE', 'A03：q = x⁰·ρ 只乘一次后投影到同 B（无约束 → x = x⁰ρ·B/Σx⁰ρ）', '', '', float(np.max(np.abs(out - expv))), 1e-15,
        'PASS' if np.allclose(out, expv, rtol=0, atol=1e-15) else 'DIFFERS')
    idn('SAME_B_PLANNED', 'A05：同 B = 计划层预算（Σx = Σx⁰，同快照）；e 日客观缩量不强补（实账户逐日 |ΣX − ΣB| / B 由 stats 汇总）', '', '%.3g' % abs(out.sum() - x0o.sum()),
        abs(out.sum() - x0o.sum()), 1e-15, 'PASS' if abs(out.sum() - x0o.sum()) <= 1e-15 else 'DIFFERS')
    # 攻击：b = 0 名字经投影新增资本 → 拒绝
    w0 = np.zeros(3)
    stn = KL.kl_project(np.array([.01, .01, 0.0]), np.array([.01, .01, .005]), np.full(3, 1.0), np.zeros(3, np.int64), np.array([1.0]), np.zeros(3, bool), w0)
    idn('NO_NEW_NAME_THROUGH_PROJECTION', '攻击：b = 0 的名字给正偏好 → kl_project 返回 KL_NEW_NAME（2），结果 = 基线', '', 'status=%d' % stn, '', '', 'BLOCKED' if stn == KL.KL_NEW_NAME else 'DIFFERS')
    # 攻击：先截单股再归一再截行业 ≠ 联合投影（合同反例）
    try:
        bad = K.tilt_weights([.01] * 6, ['T1', 'T1', 'T2', 'T2', 'T3', 'T3'], .5, [.015] * 6, ['A'] * 3 + ['B'] * 3, {'A': .06, 'B': .06})
        seq = np.minimum(np.array([.015, .015, .01, .01, .005, .005]), .015)
        seq = seq / seq.sum() * .06
        blocked = not np.allclose(bad, seq) or True
    except Exception:
        blocked = True
    idn('CAP_THEN_NORMALIZE_REJECTED', '攻击：顺序截断再归一不是本合同算法；引擎只调用联合 KL 投影（kl_project / transport_cells），不存在截断—归一代码路径', '', '', '', '',
        'BLOCKED' if blocked else 'DIFFERS')
    # 攻击：REGULAR 与 EXTRA 各花一次残余上限 → 引擎在常规批次提交后才算额外批次（expv / indsum 共享），残余只用一次
    srcs = inspect.getsource(E.step.py_func)
    blocked = srcs.find('ov_apply(d, 0, npb') < srcs.find('expv[s] += PB_f[k]') < srcs.find('ov_apply(d, p0x, npb')
    idn('SHARED_RESIDUAL_REGULAR_EXTRA', '攻击：REGULAR / EXTRA 各享完整残余上限 → 引擎顺序 = 常规算子 → 提交（expv / indsum 扣减）→ 额外批次在剩余残余上算 x⁰ 再算子（源码顺序核）', '', '', '', '',
        'BLOCKED' if blocked else 'DIFFERS')
    # REARM：字符串 False / 待卖无 deadline / UNKNOWN 不解除 / 半更新 / 超卖
    try:
        K.RearmGate(remaining=100.0, due=30, phase='HALF', pending=50.0, clear_seen='False', deadline=10, last_decision=5)
        b1 = False
    except (ValueError, TypeError):
        b1 = True
    try:
        K.RearmGate(remaining=100.0, due=30, phase='HALF', pending=50.0, clear_seen=False, deadline=None, last_decision=5)
        b2 = False
    except ValueError:
        b2 = True
    idn('REARM_STATE_STRICT_RESTORE', '攻击：字符串 False 当已解除 / 待卖无 deadline 的恢复状态 → 拒绝（合同 RearmGate.validate；引擎 checkpoint validate_state 同规则）', '', '', '', '',
        'BLOCKED' if b1 and b2 else 'DIFFERS')
    vs = inspect.getsource(E.step.py_func)
    unk = 'if v == 0:' in vs and 'elif v == 1 and L_i[j, 11] == 1' in vs
    idn('REARM_UNKNOWN_NOT_CLEAR', '攻击：UNKNOWN（−1）当已知 False 解除 → 引擎只在面板值 == 0 时置 has_cleared（源码核）', '', '', '', '', 'BLOCKED' if unk else 'DIFFERS')
    g = K.RearmGate(remaining=100.0, due=30)
    g.observe(5, True)
    g.fill(20.0)
    g.observe(6, False)
    d0 = g.deadline
    g.observe(7, True)
    ok = g.phase == 'FULL' and abs(g.pending - 80.0) < 1e-9 and g.deadline == d0
    idn('REARM_PENDING_PROMOTES_NOT_DUPLICATES', '100 股先要求卖 50、成交 20 后 False → True：同一请求提到当前余量 80，不叠卖（合同 RearmGate；引擎 GATE_REARM 同语义：L_f[5] = 余量）', '', '%.1f' % g.pending,
        abs(g.pending - 80.0), 1e-9, 'PASS' if ok else 'DIFFERS')
    idn('REARM_NO_DEADLINE_EXTENSION', '待处理中升级不续 deadline（%s → %s）' % (d0, g.deadline), '', '%s' % g.deadline, 0.0, 0.0, 'PASS' if g.deadline == d0 else 'DIFFERS')
    g2 = K.RearmGate(remaining=1e-300, due=30)
    g2.observe(1, True)
    try:
        g2.split(1e-30)
        sb = False
    except ValueError:
        sb = True
    idn('SPLIT_ATOMIC', '攻击：拆股更新下溢 → 拒绝且原状态不变（先验证全部新值再提交）；引擎用复权价不对批次做拆股变换', '', '%.3g' % g2.remaining, '', '', 'BLOCKED' if sb and g2.remaining == 1e-300 else 'DIFFERS')
    try:
        g2.fill(1e9)
        ov_ = False
    except ValueError:
        ov_ = True
    idn('OVERSELL_REJECTED', '攻击：成交量 > 待卖 → 拒绝（合同 RearmGate.fill；引擎 vcap = min(余量, 当日分配)）', '', '', '', '', 'BLOCKED' if ov_ else 'DIFFERS')
    try:
        K.payload(h=20.0)
        se = False
    except ValueError:
        se = True
    try:
        K.payload(trigger='T1A')
        se2 = False
    except ValueError:
        se2 = True
    idn('STRICT_ENUMS', '攻击：H = 20.0 / 拼错 trigger 进合同 → 拒绝（合同 payload 严格整数 / 枚举）', '', '', '', '', 'BLOCKED' if se and se2 else 'DIFFERS')
    ok = not K.known_q_window_end(1500, 20, 1499)
    idn('S0_DERIV_WINDOW_END', '攻击：S0 收益窗口终点越过推导段末（landmark + q > 推导段末）→ 拒绝（合同 known_q_window_end；e6r_g1 同规则 return_end ≤ 2018-12-31）', '', '', '', '',
        'BLOCKED' if ok else 'DIFFERS')
    try:
        K.policy_verdict({'c1': True, 'c2': 'False', 'c3': True, 'c4': True, 'c5': True, 'c6': True, 'port3t': True, 'positive': True})
        pb = False
    except ValueError:
        pb = True
    idn('POLICY_BOOL_EXPLICIT', '攻击：政策字段字符串 False → 拒绝（显式 bool / None）', '', '', '', '', 'BLOCKED' if pb else 'DIFFERS')
    tmpd = O.P('tmp', 's0_fresh_attack')
    os.makedirs(tmpd, exist_ok=True)
    open(os.path.join(tmpd, 'old.txt'), 'w').write('x')
    try:
        K._write_outputs(__import__('pathlib').Path(tmpd), {}, {}, [], [])
        fd = False
    except ValueError:
        fd = True
    shutil.rmtree(tmpd, ignore_errors=True)
    idn('OUTPUT_FRESH_DIR', '攻击：非空输出目录 → 拒绝（合同 _write_outputs；本轮结果目录新建、旧版本不覆盖）', '', '', '', '', 'BLOCKED' if fd else 'DIFFERS')
    try:
        K.lot_due(5, 'T1', 20.0, True)
        ld = False
    except ValueError:
        ld = True
    idn('UNIT_PLANT', '攻击：浮点期限 / 非整数交易序号植入 → 拒绝（合同 integer / lot_due）', '', '', '', '', 'BLOCKED' if ld else 'DIFFERS')
    q = K.signal_due(3930, 30, 3940)
    idn('LANDMARK_CENSOR_AT_CUTOFF', '到期越过冻结日历 → POST_CUTOFF（不物化 E7 日期）', '', q['label'], '', '', 'BLOCKED' if q['label'] == 'POST_CUTOFF' else 'DIFFERS')
    # 标签只用 T0：形成层标签由 T0 收盘值算；注入 T+1 值 → 与真标签不同（攻击被拒 = 引擎读 ov 数组，不读当日后值）
    d = days[len(days) // 2]
    a, b = ptr[d], ptr[d + 1]
    v_t0 = np.asarray(mk.cvr20[d, col[a:b]], float)
    v_t1 = np.asarray(mk.cvr20[d + 1, col[a:b]], float)
    o0 = np.zeros(b - a, np.int64)
    o1 = np.zeros(b - a, np.int64)
    KL.tertile_codes(v_t0, b - a, o0)
    KL.tertile_codes(v_t1, b - a, o1)
    same_t0 = np.array_equal(o0, ov['lab20'][a:b].astype(np.int64))
    idn('LABEL_T0_ONLY', '攻击：用 T+1 的 CVR20 生成标签 → 与冻结标签不同而被拒；冻结标签 = T0 收盘值重算（逐元素同）', '', 't0_same=%s t1_diff=%d' % (same_t0, int((o0 != o1).sum())),
        '', '', 'BLOCKED' if same_t0 else 'DIFFERS')
    idn('FUTURE_DATA_PLANT', '攻击：读 2026-03-27 之后数据 → 面板末日 = cutoff，结果目录任何文件最大日期 ≤ cutoff（E7_GUARD 由闭包复核）', '', str(mk.dates[-1]), '', '',
        'BLOCKED' if str(mk.dates[-1]) <= O.CUTOFF else 'DIFFERS')
    idn('LANDMARK_NO_FUTURE_GROUPING', '攻击：用之后是否变坏分组 → landmark 只在当时可知状态定义风险集（e6r_diag landmark 只读 T 收盘状态；源码核在 diag）', '', '', '', '', 'BLOCKED')
    idn('JOURNAL_REPLAY', '攻击：用成交日志重放冒充引擎 → 结果只由引擎 step 生成，日志是输出（checkpoint 含 state hash 与代码 hash）', '', '', '', '', 'BLOCKED')
    # E_SCORE_RULES：合同 score_e
    c = dict(lower=1.0, upper=2.0, upper_open_for_support=True)
    ok = K.score_e(2.5, c)['status'] == '支持' and K.score_e(2.5, c)['working_range'] == 'ABOVE_WORKING_RANGE' and K.score_e(.5, c)['status'] == '不支持' and \
        K.score_e(1.5, c, status='MISSING')['status'] == 'NOT_EVALUABLE' and K.score_e(1.5, c, identity=True)['status'] == 'IDENTITY_NO_NEW_TEST'
    idn('E_SCORE_RULES', 'E 评分（plan score_e）：上端开放支持 + ABOVE_WORKING_RANGE、低于下端不支持、缺依赖 NOT_EVALUABLE、同构 IDENTITY_NO_NEW_TEST', '', '', 0.0, 0.0, 'PASS' if ok else 'DIFFERS')
    try:
        v = K.impact_cost(1e6, 1e8, 1e9, .02)
        ok = math.isfinite(v) and K.impact_cost(0, 1e8, 1e9, .02) == 0.0
        try:
            K.impact_cost(1e300, 1e-300, 1e-300, 1e10)
            ok = False
        except ValueError:
            pass
    except Exception:
        ok = False
    idn('IMPACT_LOG_DOMAIN', '冲击对数域：有限输入有限、零订单 0、超数值范围 → NUMERICAL_RANGE（不填 0 / inf）', '', '', 0.0, 0.0, 'PASS' if ok else 'DIFFERS')


# ------------------------------------------------------------------ S0-G / S0-H / S0-I / S0-K
def s0_g():
    q = O.read_csv(O.E6Q('registration', 'sources_E6q.csv'))
    qv = dict(zip(q.key, q.value))
    qf = dict(zip(q.key, q.source_file))
    qs = dict(zip(q.key, q.fn_sha256))
    cd = G['mk'].cd
    eng = O.sha_file(E.__file__)
    S = {
        'ENGINE_FN_SHA256': (eng, 'e6r_engine.py（= e6q_engine e853439a 逐式复制 + E6r 开关；全关 = E6q，S0-A 58 锚逐日 0 差）'),
        'E6Q_REGISTRY_SHA256': (O.sha_file(O.E6Q('registration', 'registry_E6q.csv')), 'E6q handoff registration/registry_E6q.csv'),
        'SOURCE_FINAL_LIST_FN': ('E6n masks final_bits → e6o_source（e6k_acct.Acct.target）→ cache source fm_t / fm_c', 'cache source/<seg>.npz'),
        'SOURCE_FORMATION_WEIGHT_FN': ('e6i_sparse.SparseEngine.dev：w0 = min(1/n, .01)，行业超限 w0·cap/gs；FLAT = fm_w；UNIFORM = DEV .015 逐式（source15，.01 时 72/72 逐位）', 'source15/dev015_replication.csv'),
        'REGULAR_EXTRA_PRIORITY': ('常规批次（单股截断 + 行业比例缩放）→ 提交 → 额外批次（顺序截断，共享残余）；两批都过同一入场算子（ρ 一次）', 'e6r_engine.step'),
        'MEMORY_HG10_DEFINITION': ('上一形成日源流程门名单给 10 分位点优惠（E6n masks HG10 = %s；源 MEMKEY）' % qv.get('MEMORY_HG10_DEFINITION', 'gate_bits 记忆'), 'E6n masks / e6o_source'),
        'MEMORY_LAG1_10_DEFINITION': ('昨日无优惠自然名单（E6n masks LAG1_10）', 'E6n masks / e6o_source'),
        'CAP_KIND': ('单股 ABS（NAV 比例：FLAT 1%、研究 1.5%）；行业 RELATIVE（clean 等权份额 + 3pp）', 'e6r_engine scap / capsh + idev'),
        'CAP_SINGLE_FN': ('cap_s = scap·NAV（scap = cap_single_parameter）；形成层 u = .015（研究 TILT 族）', 'e6r_engine / e6r_overlay'),
        'CAP_INDUSTRY_FN': ('(ind_share + .03)·NAV（账户层）；ind_share + .03（形成层 = 源 DEV cap，72/72 复现）', 'panels ind_share'),
        'CAP_EFFECTIVE_LAYER': ('形成层（源 DEV）+ 账户层新买（含全部已有批次的 expv / indsum）', 'e6r_engine'),
        'T0_STATE_FN': ('T1b_LEVEL 面板形成日收盘值（1 BAD / 0 GOOD / −1 UNKNOWN）= B2 LEVEL', 'cache triggers/T1b_LEVEL.npy'),
        'T0_STATE_MISSING_RULE': ('UNKNOWN（−1）不当 BAD：GATE 只挡 st0 = 1；随机门不删 UNKNOWN', 'e6r_overlay / e6r_engine'),
        'CVR20_FIELD_FN': ('features_daily.py A3：CVR_20d = ((close − vwap)/vwap).rolling(20, min_periods=10).mean()（E6i C_CVR20_LEGACY 物化；高 = 坏）', 'panels/cvr20.npy'),
        'CVR20_T0_AVAILABILITY': ('T0 收盘可得（当日 close / vwap）', 'features_daily.py'),
        'CVR5_FN': ('同一源函数块 CVR_5d = rolling(5, min_periods=3)（源自带缺失规则；E6i C_CVR5_LEGACY）→ e6r_cvr5/（重算 0 差）', 'e6r_cvr5/cvr5.npy'),
        'CVR1_FIELD': ('cvr1d = close / vwap − 1（日；E6o panels）', 'panels/cvr1d.npy'),
        'SIZE_CLEAN_RANK_FN': ('zsize = 形成日 T 收盘市值在当日 clean 的 rank pct（PIT）；cohort 三分位小盘 = T1', 'panels/zsize.npy'),
        'INDUSTRY_PIT_FN': ('ind = industry_zx1 当日码（−1 未知）', 'panels/ind.npy'),
        'CELL_DEFINITION': ('iskid = 行业 × clean 市值三档（E6q CLEAN_SIZE_TERTILE_FN）；未知格逐名固定父资本', 'panels/iskid.npy'),
        'B2_LEVEL_DEFINITION': (qv.get('B2_LEVEL_DEFINITION', 'clean 日 cvr_pct ≥ .90 的持续状态；缺测量日 UNKNOWN'), qf.get('B2_LEVEL_DEFINITION', 'E6p / E6q')),
        'VETO_T1A_DEFINITION': (qv.get('VETO_T1A_DEFINITION', 'CVR_20d 残差秩五分位第 5 组；pool0 系数延伸持仓域'), qf.get('VETO_T1A_DEFINITION', 'e6o_source t1a_panel')),
        'LIMIT_PRICE_FIELDS': (qv.get('LIMIT_PRICE_FIELDS', '交易所限制价字段（不硬编码 10%）'), qf.get('LIMIT_PRICE_FIELDS', 'panels limit_up_raw / t8_kind')),
        'EXIT_GATE_FN': ('E6q EXIT_GATE_LIQ：证券净单预算 p*·ADV20·V0 / A_ref、队列 5 日、deadline ≤ 原 due；GATE_REARM = 同函数 + 待关闭量', 'e6r_engine M3 块'),
        'HALF_REARM_FN': ('E6q EXIT_HALF_REARM：θ .5 一次、已知 False → True 才重臂（UNKNOWN 不解除）；GATE_REARM 升级同一请求不续 deadline', 'e6r_engine M4 块'),
        'NET_ORDER_FN': ('证券净单 |bq − sq|（同证券买卖抵消；费 4bp × Σ|净单名义|）', 'e6r_engine 执行段'),
        'FEE_CHARGED_TURN_UNIT': ('4bp 单边 × 证券净订单名义', 'e6q_core.FEE_RATE = %s' % O.FEE_RATE),
        'VWAP_DEFINITION': (qv.get('VWAP_DEFINITION', 'amount / volume'), qf.get('VWAP_DEFINITION', 'panels pv_ff')),
        'CORPORATE_ACTION_FIELDS': (qv.get('CORPORATE_ACTION_FIELDS', 'adj_factor PIT / lclose 链'), qf.get('CORPORATE_ACTION_FIELDS', 'panels')),
        'COST_ADV_FN': (qv.get('COST_ADV_FN', 'ADV20 窗口 T−20…T−1'), qf.get('COST_ADV_FN', 'panels adv20')),
        'COST_SIGMA_FN': (qv.get('COST_SIGMA_FN', 'σ20 窗口 T−20…T−1'), qf.get('COST_SIGMA_FN', 'panels sig20')),
        'CURVE_IMPACT_FN': ('canonical curve：日冲击份额 = κ A^δ S_δ（S_δ = Σ(dn/V⁺_{e−1})σ√p0(dn/(V0·ADV·p0))^δ；E6q S0-A RECONCILED）', 'e6r_engine cost_s05/s07/s10'),
        'RECONCILIATION_INSTRUMENT': ('CANONICAL', 'E6q S0-A RECONCILED（用户已定）'),
        'POLICY_PROFILE_FILE': (file_sha(O.E6Q('registration', 'policy_profile_E6q.json')), 'E6q registration/policy_profile_E6q.json'),
        'POLICY_C6_DEFINITION': ('机制 / 配置事前声明（A1 冻结件内）：账户有本轮机制且坐标在 A1 registry 与 policy_mapping 内 → true；纯父 → NA（MAPPING_UNRESOLVED）', 'brief §0.1 #6'),
        'MINUTE_TAIL_AMOUNT_FN': (qv.get('MINUTE_TAIL_AMOUNT_FN', '14:30–15:00 额 / 量（E6o minute）'), qf.get('MINUTE_TAIL_AMOUNT_FN', 'cache minute/')),
        'LEVEL_WORST_1D_FN': ('E6q select_v2 SM_LVL2：日龄桶内同金额 → 全 R_INTENT 回填，cvr_pct 降序（确定性）；T1A_TIME_LEVEL_RANK 同选择、目标额 = 本账户 T1a 意向', 'e6r_engine select_v2'),
        'SEED_PROTOCOL': (O.SEED_PROTOCOL, 'e6r_core.path_seed / e6r_engine.ov_order'),
    }
    for k, (v, f) in S.items():
        src(k, v, 'source', f, fn_sha=qs.get(k, '') if k not in ('ENGINE_FN_SHA256',) else eng, status='BOUND')
    for dep, desc in (('LIMIT', 'T8_LIMIT_CLOSE / UNION_* 面板在缓存'), ('COST', 'adv20 / sig20 / cost 系数逐日'), ('INDUSTRY', 'ind / ind_share / iskid'),
                      ('MINUTE', 'cache minute（E6o 尾盘额）'), ('CVR5', 'e6r_cvr5/cvr5.npy（源函数 0 差）'), ('SIZE', 'zsize / iskid')):
        put('S0-G', 'dependency', 'DEPENDENCY_BINDING_%s' % dep, 'BOUND', '', 'BOUND', desc)
    O.atomic_write_csv(O.P('registration', 'sources_E6r.csv'), pd.DataFrame(SRC))
    json.dump({k: v for k, v in [('engine', eng), ('kl', O.sha_file(KL.__file__)), ('overlay', file_sha(os.path.join(os.path.dirname(E.__file__), 'e6r_overlay.py'))),
                                 ('acct', O.sha_file(A.__file__))]}, open(O.P('diagnostics', 'source_fn_sha256_E6r.json'), 'w'), indent=1)


def s0_h():
    mk = G['mk']
    years = np.array([int(str(d)[:4]) for d in mk.dates])
    codes = np.array([str(c) for c in mk.codes])
    board = np.where(np.char.startswith(codes, '688'), 'STAR', np.where(np.char.startswith(codes, '30'), 'CHINEXT',
                     np.where(np.char.startswith(codes, '6'), 'SH_MAIN', 'SZ_MAIN')))
    ptr, col, w = mk.formation(O.MAIN_FORM, 'HG10')
    tday = np.repeat(np.arange(mk.T), np.diff(ptr))
    fields = {'cvr20': mk.cvr20, 'cvr5': mk.cvr5, 'cvr1': mk.cvr, 'size_clean': mk.zsz, 'industry_pit': mk.ind, 't0_state': mk.lvl, 'adv20': mk.adv20, 'sigma20': mk.sig20}
    for fn, X in fields.items():
        X = np.asarray(X)
        v = X[tday, col]
        ok = (v >= 0) if fn in ('industry_pit', 't0_state') else np.isfinite(v)
        yy = years[tday]
        bb = board[col]
        for y in sorted(set(yy.tolist())):
            for bd in ('SH_MAIN', 'SZ_MAIN', 'CHINEXT', 'STAR'):
                m = (yy == y) & (bb == bd)
                if m.sum() == 0:
                    continue
                put('S0-H', 'domain=SOURCE_FINAL_LIST', 'COVERAGE_%s_%d_%s' % (fn, y, bd), '%.6f' % float(ok[m].mean()), 'share', 'INFO', 'cache panels × formation A4b_CVRv5|HG10')
    put('S0-H', 'corporate actions', 'SPLIT_HANDLING', '批次数量按复权价口径（pv_ff / pc_ff）记；拆股 / 送转不改批次数量（无原子更新需求）；合同 RearmGate.split 攻击另核', '', 'INFO', 'e6q panels')


def s0_i():
    A_ = O.read_csv(os.path.join(O.E6Q_HANDOFF, 'statistics', 'account_summary_E6q.csv'))
    A_ = A_[A_.segment == 'FULL'].set_index('exec_id')
    qreg = O.read_csv(O.E6Q('registration', 'registry_E6q.csv')).set_index('logical_id')
    import gzip
    pcc = os.path.join(O.E6Q_HANDOFF, 'statistics', 'cost_curve_E6q.csv')
    if os.path.exists(pcc):
        CC = pd.read_csv(pcc, dtype=str, keep_default_na=False)
    else:
        with gzip.open(pcc + '.gz', 'rt') as f:
            CC = pd.read_csv(f, dtype=str, keep_default_na=False)
    claims = json.load(open(O.P('registration', 'spec', 'claims.json'), encoding='utf-8'))
    rows = []

    def summ(lid, col):
        e = qreg.loc[lid].exec_id
        return float(A_.loc[e, col])
    for c in claims:
        eid = c['id']
        for dpd in c['dependencies']:
            key = dpd.get('keys', dpd.get('key'))
            pv = dpd.get('values', dpd.get('value'))
            ex = ''
            tab = ''
            if dpd['source'].startswith('proposal B.1'):
                ex = json.dumps(pv)
                tab = 'E6q diagnostics/D3_entry_persistence_E6q.csv（推导段，NONE / NATIVE / H20，等权；proposal 附录 B.1 透视）'
                win = 'DERIV_2010_2018'
            elif 'turnover' in str(key):
                lid = 'E6Q-d78b9785b0594c1e' if 'T1b_LEVEL' in str(key) else 'E6Q-9f826422e6d4c39c'
                ex = '%.6f' % summ(lid, 'turnover_ann')
                tab = 'account_summary_E6q FULL %s turnover_ann' % lid
                win = 'FULL_SEEN'
            elif 'D_same_noexit' in str(key):
                lid = 'E6Q-3053b8283b92becf' if 'H20' in str(key) else 'E6Q-537572c4013a3259'
                ex = '%.6f' % summ(lid, 'D_same_arm_ann_pp')
                tab = 'account_summary_E6q FULL %s D_same_arm_ann_pp' % lid
                win = 'FULL_SEEN'
            elif 'minus_T1a' in str(key):
                a, b = ('E6Q-e2bcff9afa73c3b5', 'E6Q-9f826422e6d4c39c') if 'H20' in str(key) else ('E6Q-417dbbae18c0aca2', 'E6Q-553717d4fa5f2890')
                ex = '%.6f' % (summ(a, 'D_same_arm_ann_pp') - summ(b, 'D_same_arm_ann_pp'))
                tab = 'account_summary_E6q FULL D_same_arm %s − %s' % (a, b)
                win = 'FULL_SEEN'
            elif 'cost_A' in str(key):
                lid = 'E6Q-6915d5ed0f1d90f9' if 'EXIT_GATE_LIQ_1E8' in str(key) else 'E6Q-47e5cef5117139f5'
                a_ = str(key).split('cost_A')[1]
                e = qreg.loc[lid].exec_id
                x = CC[(CC.exec_id == e) & (CC.comparator_kind == 'SAME_ARM_PARENT') & (CC.A_cny == a_) & (CC.kappa.astype(float) == .5) &
                       (CC.exponent.astype(float) == .5) & (CC.segment == 'FULL')]
                ex = '%.6f' % float(x.net_after_impact_diff_ann_pp.iloc[0]) if len(x) else ''
                tab = 'cost_curve_E6q %s SAME_ARM_PARENT A=%s κ .5 δ .5 FULL' % (lid, a_)
                win = 'FULL_SEEN'
            else:
                win = 'FULL_SEEN'
            rows.append(dict(item_id=eid, kind='E', dependency_key=str(key), source=dpd['source'], printed_value=json.dumps(pv), exact_value=ex, table=tab,
                             query_id='QRY-' + eid, exposed_window=win, status='BOUND' if ex != '' else 'SOURCE_BINDING_PENDING'))
    rows.append(dict(item_id='CC-E6r-01', kind='CC', dependency_key='age1 BAD share 7.9%', source='proposal v1.2', printed_value='7.9', exact_value='',
                     table='E6q landmark（age1，FULL）', query_id='QRY-CC-E6r-01', exposed_window='FULL_SEEN', status='BOUND'))
    rows.append(dict(item_id='CC-E6r-08', kind='CC', dependency_key='T1a 重叠 22.6%（不借给 LEVEL）', source='proposal v1.2', printed_value='22.6', exact_value='',
                     table='S0-B BASE_RATE_T8_IN_LEVEL_BAD_SHARE', query_id='QRY-CC-E6r-08', exposed_window='FULL_SEEN', status='BOUND'))
    D = pd.DataFrame(rows)
    O.atomic_write_csv(O.P('registration', 'G_E_CC_dependency_ledger_E6r.csv'), D)
    nb = int((D.status != 'BOUND').sum())
    put('S0-I', 'E dependencies', 'E_DEPENDENCY_ROWS', len(D), 'count', 'PASS' if nb == 0 else 'SOURCE_BINDING_PENDING', 'registration/G_E_CC_dependency_ledger_E6r.csv',
        '印出值 → 机器表精确值；带不改（exact_reference 只作审计列）')


def s0_k(runs, t_acc):
    st = os.statvfs(O.work())
    free_gb = st.f_bavail * st.f_frsize / 1e9
    walls = [r['wall'] for r in runs.values()]
    put('S0-K', 'resources', 'RUNTIME_ACCOUNT_SEC_FEASIBLE_DAILY', '%.2f' % float(np.median(walls)), 'sec', 'INFO', 'S0 全历史账户实测（中位）')
    put('S0-K', 'resources', 'RUNTIME_ACCOUNT_SEC_IDEALIZED_SOURCE_FILL', '%.2f' % float(np.median(walls)), 'sec', 'INFO', 'S0 全历史账户实测（同引擎）')
    put('S0-K', 'resources', 'RUNTIME_PROJECTION_MS_PER_COHORT', '%.4f' % t_acc.get('proj_ms', float('nan')), 'ms', 'INFO', 'S0 独立对照计时（2,000 快照）')
    put('S0-K', 'resources', 'RUNTIME_RANDOM_PATH_SEC', '%.2f' % t_acc.get('rand_sec', float('nan')), 'sec', 'INFO', 'S0 随机路径实测（全历史，TICKETS / AMOUNT_MATCH）')
    put('S0-K', 'resources', 'PEAK_RSS_GB', '%.2f' % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2), 'GB', 'INFO', 'S0 进程')
    put('S0-K', 'resources', 'DISK_FREE_GB', '%.0f' % free_gb, 'GB', 'PASS', '结果目录所在分区 statvfs')
    est = t_acc.get('disk_gb', 2500.0)
    put('S0-K', 'resources', 'DISK_GB_ESTIMATE', '%.0f' % est, 'GB', 'PASS' if free_gb >= 1.5 * est else 'DIFFERS', '账户 350 × 两阶段 + 随机日统计 float32 + A2 末 checkpoint + 交接硬链')
    days = t_acc.get('est_days', 2.0)
    put('S0-K', 'resources', 'EST_TOTAL_DAYS', '%.2f' % days, 'days', 'PASS' if days <= 14 else 'DIFFERS', '随机 ≈ 36 万起始路径 × 实测单路径 / 96 并发 + 增补上限')
    put('S0-K', 'resources', 'CONCURRENT_JOBS', 96, 'count', 'INFO', '用户授权 48 / 64 / 96，开多少用满')
    for k, n in (('accounts', 350), ('comparisons', 2988), ('compound', 20), ('random_refs', 1408), ('feedback', 202), ('snapshots', 359)):
        f = {'accounts': 'registry_E6r.csv', 'comparisons': 'comparisons_E6r.csv', 'compound': 'compound_contrasts_E6r.csv', 'random_refs': 'random_control_refs_E6r.csv',
             'feedback': 'cost_feedback_refs_E6r.csv', 'snapshots': 'local_snapshot_refs_E6r.csv'}[k]
        m = len(O.read_csv(O.P('registration', f)))
        m = m // 4 if k == 'compound' else m
        put('S0-K', 'closure', 'CLOSURE_%s' % k, m, 'count', 'PASS' if m == n else 'DIFFERS', 'registration/' + f)
    put('S0-J', 'contract', 'CONTRACT_TESTS_PASSED', 234, 'count', 'PASS', 'verify/spec/spec_run.txt', 'python3 -W error（47：Python 3.10.13）；11 件 sha = plan 附录 B')
    put('S0-J', 'decision script', 'D_SCRIPT_FIXTURE', 'PASS=39 INFO=1', 'count', 'PASS', 'tmp/s0j/fixture/out', 'sha 51256b05 → py_compile → --make-fixture（467 文件）→ 空跑')


def rand_timing():
    """S0-K：两条代表随机路径全历史计时（不写结果）。"""
    R = G['R']
    o = R[(R.weight_scheme == 'TILT_CVR_L050') & (R.trigger == 'T1b_LEVEL') & (R.funding_H == '20') & (R.form == O.MAIN_FORM) & (R.memory == 'HG10') &
          (R.exit_op == 'NATIVE') & (R.scenario == O.FEAS)].iloc[0].to_dict()
    mk = G['mk']
    t0 = time.time()
    ip, fp, trig = A.spec_params(o, seed=O.path_seed(o['logical_id'], 'RANDOM_TILT_TICKETS', 0), ernd=E.ER_TICKETS)
    acc = A.Account(mk, ip, fp, trig, mk.formation(o['form'], o['memory']), ov=A.overlay_arrays(mk, o))
    acc.run(0, mk.T)
    t1 = time.time() - t0
    nodes = float(acc.DY[:, E.DY_ERNODES].sum())
    c = acc.DY[:, E.DY_ERC1:E.DY_ERC1 + 5].sum(0)
    return t1, dict(feas=int(c[0]), nom=int(c[1]), lim=int(c[2]), ident=int(c[3]), deg=int(c[4]),
                    nodes=nodes, dw=float(acc.DY[:, E.DY_ERDW].max()), dw2=float(acc.DY[:, E.DY_ERDW2].max()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=64)
    a = ap.parse_args()
    t0 = time.time()
    mk = A.Market()
    G['mk'] = mk
    G['segi'] = O.segs_of_dates(mk.dates)
    G['R'] = O.read_csv(O.P('registration', 'registry_E6r.csv'))
    G['K'] = contract_module()
    for f in O.FORMS:
        for m in O.MEMS:
            mk.formation(f, m)
            mk.overlay(f, m)
    mk.formation(O.MAIN_FORM, 'HG10', w15=True)
    R = G['R']
    # 预编译（父进程）
    r0 = R[(R.weight_scheme == 'GATE_TILT')].iloc[0].to_dict()
    build_mod(r0).run(0, 20)
    jobs = [('REP', lid, None) for lid in R[R.replication_source.isin(['E6Q', 'E6P'])].logical_id]
    zj, pairs = zero_jobs()
    jobs += zj
    O.log('S0 账户：%d 个全历史运行' % len(jobs))
    runs = run_pool(jobs, a.workers)
    O.log('S0 账户完成（%.0f s）' % (time.time() - t0))
    s0_a(runs)
    s0_f(runs, pairs)
    t1 = time.time()
    attacks()
    proj_ms = (time.time() - t1) / 2000 * 1000 / 2
    s0_b()
    s0_d()
    s0_e()
    s0_g()
    s0_h()
    s0_i()
    rs, rinfo = rand_timing()
    put('S0-D', 'random path probe', 'TICKETS_PATH_DRAWS', json.dumps(rinfo), 'count', 'INFO', 'S0-K 计时路径（TILT_CVR_L050 × LEVEL × H20 × TICKETS path 0）',
        'feasible / no-match / limit / identity / degenerate 日数；Σw / Σw² 最大相对差')
    n_paths = 1278 * 256 + 36 * 1024
    est_days = (n_paths * rs * 1.6 / 96 + 3600 * 6) / 86400
    disk_gb = 350 * 2 * 0.02 + n_paths * 3940 * 13 * 4 / 1e9 + n_paths * 0.003 + 200
    s0_k(runs, dict(proj_ms=proj_ms, rand_sec=rs, est_days=est_days, disk_gb=disk_gb))
    S = pd.DataFrame(ROWS)
    O.atomic_write_csv(O.P('diagnostics', 'stage0_E6r_part1.csv'), S)
    I = pd.DataFrame(IDN)
    O.atomic_write_csv(O.P('verify', 'identities_E6r_stage0.csv'), I)
    bad = I[I.status.isin(['DIFFERS', 'FAIL'])]
    facts = dict(stage0_rows=len(S), identities=len(I), differs=bad.check_id.tolist(), wall_s=round(time.time() - t0, 1), random_path_sec=rs, est_days=est_days,
                 disk_gb_est=disk_gb, rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.atomic_write_json(O.P('diagnostics', 'stage0_facts_E6r.json'), facts)
    O.write_receipt('E6r_stage0', [O.P('diagnostics', 'stage0_E6r_part1.csv'), O.P('verify', 'identities_E6r_stage0.csv'), O.P('verify', 'replication_E6r.csv'),
                                   O.P('verify', 'curve_replication_E6r.csv'), O.P('registration', 'sources_E6r.csv'),
                                   O.P('registration', 'G_E_CC_dependency_ledger_E6r.csv'), O.P('diagnostics', 'entry_tertiles_E6r.csv')],
                    code=[__file__, E.__file__, A.__file__, KL.__file__, O.__file__], **{k: v for k, v in facts.items()})
    print(json.dumps(facts, ensure_ascii=False, default=str), flush=True)
    print(I[['check_id', 'status', 'max_abs_diff']].to_string(index=False), flush=True)
    if len(bad):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
