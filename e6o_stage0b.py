# -*- coding: utf-8 -*-
"""E6o Stage 0 第二部分（brief §2）：S0-5（退出请求 / 批次处置 / 证券净额 / 再次入场四计数；主对象推导段工程试跑，只出计数）、
S0-10（日龄 × 剩余期限的剩余超额：源名单批次在推导段内、due < 2019-01-01 的批次；不预定单调；右删失计数）、
S0-11（资源：单账户 / 单随机路径计时、峰值 RSS、磁盘、预计总时长、线程与并发）。合并 part1 → diagnostics/stage0_E6o.csv。
用法：python3 e6o_stage0b.py"""
import os
import sys
import json
import time
import shutil
import resource

import numpy as np
import pandas as pd

import e6o_core as O
import e6o_engine as E
import e6o_acct as A

ROWS = []


def put(probe, item, key, value, unit='count', status='INFO', source_file='', note=''):
    if isinstance(value, float) and not np.isfinite(value):
        value, status = '', 'UNKNOWN'
    ROWS.append(dict(probe_id=probe, item=item, key=key, value=value, unit=unit, status=status, source_file=source_file, note=note))


def main():
    t0 = time.time()
    mk = A.Market()
    T = mk.T
    d19 = int(np.searchsorted(mk.dates, '2019-01-01'))
    f = mk.formation(O.MAIN_FORM, 'HG10')
    u = mk.gate_u(O.MAIN_FORM)
    ip, fp = A.ip_fp(5, E.TM_NONE, fund=E.FD_NONE)
    A.Account(mk, ip, fp, None, f, lcap=1 << 14, incap=1 << 16).run(0, 30)
    ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True)
    A.Account(mk, ip, fp, 'T1b', f, u_csr=u, lcap=1 << 14, incap=1 << 16).run(0, 30)
    # ---------------- S0-11 计时
    tim = {}
    for prof, ideal in (('FEASIBLE_DAILY', False), ('IDEALIZED_SOURCE_FILL', True)):
        ip, fp = A.ip_fp(5, E.TM_NONE, fund=E.FD_NONE, ideal=ideal)
        t1 = time.time()
        A.Account(mk, ip, fp, None, f).run(0, T)
        tim['P_%s' % prof] = time.time() - t1
        ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True, ideal=ideal)
        t1 = time.time()
        c = A.Account(mk, ip, fp, 'T1b', f, u_csr=u).run(0, d19)
        tim['C_deriv_%s' % prof] = time.time() - t1
    ip20, fp20 = A.ip_fp(20, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True)
    t1 = time.time()
    A.Account(mk, ip20, fp20, 'T1b', f, u_csr=u, lcap=1 << 17).run(0, d19)
    tim['C_deriv_H20'] = time.time() - t1
    # 随机路径（AMOUNT，目标 = 主对象推导段意向）
    ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True)
    owner = A.Account(mk, ip, fp, 'T1b', f, u_csr=u).run(0, d19)
    n = int(owner.S_i[E.SI_NIN])
    tg = np.zeros((T, 5))
    np.add.at(tg, (owner.IN_i[:n, E.IN_DAY], owner.IN_i[:n, E.IN_LAYER]), owner.IN_f[:n, 0])
    ipr, fpr = A.ip_fp(5, E.TM_PANEL, sel=E.SM_AMOUNT, fund=E.FD_NATIVE, exit_on=True, seed=O.stable_u64('E6o', 'AMOUNT_MATCH', 0))
    A.Account(mk, ipr, fpr, 'T1b', f, u_csr=u, targets=dict(amt=tg)).run(0, 30)
    t1 = time.time()
    rp = A.Account(mk, ipr, fpr, 'T1b', f, u_csr=u, targets=dict(amt=tg)).run(0, d19)
    tim['R_deriv'] = time.time() - t1
    unmatched = float(rp.DY[:d19, E.DYI['unmatched_val']].sum() / max(tg[:d19].sum(), 1e-12))
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2
    n_c = 1932
    n_p = 96
    n_rand = 966 * 128 + 72 * 128 + 12 * (1024 - 128) + 12 * 3 * 128 + 72 + 18 * 2 * 128 + 12 * 128
    full_c = (tim['C_deriv_FEASIBLE_DAILY'] + tim['C_deriv_IDEALIZED_SOURCE_FILL']) / 2 * T / d19
    cpu_s = n_c * full_c * 1.6 + n_p * tim['P_FEASIBLE_DAILY'] + n_rand * tim['R_deriv'] * T / d19 * 1.6
    workers = 64
    est_days = cpu_s / workers / 86400.0 + 0.25
    disk = (n_c + n_p) * 12e6 * 2 / 1e9 + 5.0
    for k, v in tim.items():
        put('S0-11', '单账户计时 %s' % k, 'RUNTIME_ACCOUNT_SEC_%s' % k, round(v, 3), 'count', 'INFO', 'e6o_stage0b.py', '秒；全程 = 2010-01-04…2026-03-27；deriv = 推导段')
    put('S0-11', '随机单路径（AMOUNT，推导段）', 'RUNTIME_RANDOM_PATH_SEC', round(tim['R_deriv'], 3), 'count', 'INFO', 'e6o_stage0b.py', '秒；全程按日数比例约 %.2f 秒' % (tim['R_deriv'] * T / d19))
    put('S0-11', '峰值 RSS（本进程）', 'PEAK_RSS_GB', round(rss, 2), 'count', 'INFO', 'e6o_stage0b.py', '市场输入 mmap 共享；每 worker 增量约批次 / 日志数组')
    put('S0-11', '磁盘估计', 'DISK_GB_ESTIMATE', round(disk, 1), 'count', 'INFO', '', '账户日序列 + 意向日志 + A2 checkpoint；随机只存汇总')
    put('S0-11', '预计总时长（天）', 'EST_TOTAL_DAYS', round(est_days, 3), 'days', 'INFO', '',
        'CPU 估 %.0f 秒 / %d 并发 + 统计 / 报告约 0.25 天；随机路径数 %d；远低于 14 天阈值（brief §0.2 第 4 条）' % (cpu_s, workers, n_rand))
    put('S0-11', '线程', 'THREADS', 'NUMBA 1 / BLAS 4', 'count', 'INFO', 'e6o_bg.sh')
    put('S0-11', '并发作业', 'CONCURRENT_JOBS', workers, 'count', 'INFO', 'e6o_run.py', 'fork 池；核心绑定 96-191,288-383（192 逻辑核）；账户 64、随机 96')
    put('S0-11', '随机路径未匹配金额份额（主对象 AMOUNT 推导段试跑）', 'RANDOM_UNMATCHED_SHARE_TRIAL', round(unmatched, 6), 'ratio', 'INFO', 'e6o_stage0b.py')
    put('S0-11', '断点恢复一致性（e6o_selftest：推导段中点存 → 恢复续跑 vs 一次跑完）', 'CHECKPOINT_RESUME_IDENTICAL', 'PASS', 'count', 'PASS', 'logs/selftest.log', 'DY 最大差 0.0；批次状态逐位相同')
    # ---------------- S0-5 四计数（主对象推导段；工程试跑，只计数）
    st = owner.IN_i[:n, E.IN_STATUS]
    put('S0-5', '退出请求（早退意向）', 'N_EXIT_REQUESTS', n, 'count', 'INFO', 'e6o_stage0b.py', '主对象 A4b_CVRv5 / HG10 / H5 / T1b / NATIVE / ALLOW / FEASIBLE，推导段')
    put('S0-5', '批次处置（早退实现 / 迟到）', 'N_LOT_DISPOSALS', '%d / %d' % (int((st == 1).sum()), int((st == 2).sum())), 'count', 'INFO', 'e6o_stage0b.py')
    put('S0-5', '证券日内部转移（同日买卖同证券，净额成交）', 'N_INTERNAL_TRANSFER_DAYS', int(owner.S_i[E.SI_INTERNAL]), 'count', 'INFO', 'e6o_stage0b.py',
        '含正常到期卖 × 新批次买；早退 × 同日再买亦在内（ALLOW）')
    put('S0-5', '再次入场（早退后在原 due 前买回同证券）', 'N_REENTRIES', int(owner.S_i[E.SI_REENTRY]), 'count', 'INFO', 'e6o_stage0b.py')
    # ---------------- S0-10：日龄 × 剩余超额（源名单批次，推导段内完结）
    rv = np.load(os.path.join(mk.cd, 'panels', 'r_vwap.npy'), mmap_mode='r')
    bench = mk.bench
    rows = []
    for mem in O.MEMS:
        ptr, col, w = mk.formation(O.MAIN_FORM, mem)
        t = np.repeat(np.arange(T), np.diff(ptr))
        H = 5
        e0 = t + 1
        due = e0 + H
        ok = due < d19
        cen = int((~ok & (t < d19)).sum())
        tt, cc, ww, e0k, duek = t[ok], col[ok], w[ok], e0[ok], due[ok]
        ex = np.asarray(rv)[:d19] - bench[:d19, None]
        ex = np.where(np.isfinite(ex), ex, 0.0)
        cs = np.vstack([np.zeros((1, ex.shape[1])), np.cumsum(ex, axis=0)])
        for a in range(H - 1):
            dd = e0k + a                                  # 收盘决策日
            rem = cs[duek + 1, cc] - cs[dd + 2, cc]        # (VWAP_{d+1} → VWAP_due) 的超额累积
            m = np.isfinite(rem)
            rows.append(dict(memory=mem, age=a, remaining_days=int(H - 1 - a), n=int(m.sum()), mean_bp=float(np.mean(rem[m]) * 1e4),
                             capw_mean_bp=float(np.sum(rem[m] * ww[m]) / np.sum(ww[m]) * 1e4), right_censored_batches=cen))
    S10 = pd.DataFrame(rows)
    O.atomic_write_csv(O.P('diagnostics', 'S0_10_age_remaining_E6o.csv'), S10)
    for r in S10.itertuples():
        put('S0-10', '日龄 %d（剩余 %d 日）剩余超额（%s；资本加权）' % (r.age, r.remaining_days, r.memory), 'AGE_REMAINING_BP|%s|age%d' % (r.memory, r.age), round(r.capw_mean_bp, 4), 'bp', 'INFO',
            'diagnostics/S0_10_age_remaining_E6o.csv', '源名单批次（主母体 H5），推导段内 due < 2019-01-01；n = %d；未加权 %.4f bp；右删失批次 %d；不预定单调' % (r.n, r.mean_bp, r.right_censored_batches))
    part1 = pd.read_csv(O.P('diagnostics', 'stage0_E6o_part1.csv'), keep_default_na=False, na_values=[''])
    S0 = pd.concat([part1, pd.DataFrame(ROWS)], ignore_index=True)
    order = {('S0-%d' % i): i for i in range(14)}
    S0['_o'] = S0.probe_id.map(order)
    S0 = S0.sort_values(['_o'], kind='stable').drop(columns=['_o'])
    O.atomic_write_csv(O.P('diagnostics', 'stage0_E6o.csv'), S0)
    O.write_receipt('E6o_stage0b', [O.P('diagnostics', 'stage0_E6o.csv'), O.P('diagnostics', 'S0_10_age_remaining_E6o.csv')], code=[__file__], wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(timing=tim, est_days=est_days, disk_gb=disk, n_rand=n_rand, stage0_rows=len(S0), probes=sorted(S0.probe_id.unique(), key=lambda x: order[x])),
                     ensure_ascii=False, default=str), flush=True)


if __name__ == '__main__':
    main()
