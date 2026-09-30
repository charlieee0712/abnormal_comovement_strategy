# -*- coding: utf-8 -*-
"""E6l MC 增补驱动（plan §7.5；brief W13）：对一段反复 规划 → 增补 → 再规划，直到全部共享路径组（机制 × 测量）MCSE ≤ .03 或到 8,192。
每轮：e6l_stats --mc-plan（只读随机路径离散，不读真实账户）→ topup > 0 的组按（机制, have, topup）合并为一次 e6l_run_rand 调用
（--meas 列表 --path0 have --npaths topup --chunk 64，全部分片由 --workers 个进程并行；路径逐条按种子生成，分片大小不影响路径内容）。
首 1,024 路径永久保留；增补以 512 为块、不因均值符号停止。
（16:4x 改：原为每组一次调用、512 一片、逐组串行——后段 COND 单组 512 路径约 30 分钟，多组串行会成为关键路径。）"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import time
import argparse
import subprocess

import pandas as pd

import e6l_core as L

TOPUP_CHUNK = 64                                   # 增补分片路径数（e6l_seal.planned 按此推队列）


def latest_plan(pname, phase):
    fs = sorted(glob.glob(L.P('results', phase, 'mc_plan_%s_*.csv' % pname)), key=os.path.getmtime)
    return pd.read_csv(fs[-1]) if fs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--phase', default='deriv')
    ap.add_argument('--workers', type=int, default=24)
    ap.add_argument('--rounds', type=int, default=16)
    ap.add_argument('--chunk', type=int, default=TOPUP_CHUNK)
    a = ap.parse_args()
    run = os.path.join(L.CODE, 'e6l_run.sh')
    for rnd in range(a.rounds):
        log = L.P('logs', 'mc_plan_%s_r%d.log' % (a.segment, rnd))
        r = subprocess.run([run, log, os.path.join(L.CODE, 'e6l_stats.py'), '--segment', a.segment, '--phase', a.phase, '--mc-plan'])
        if r.returncode != 0:
            print('MC 规划失败 rc=%d' % r.returncode, flush=True)
            return 2
        P = latest_plan(a.segment, a.phase)
        need = P[P.topup > 0]
        print('%s 第 %d 轮：%d / %d 组需增补' % (a.segment, rnd, len(need), len(P)), flush=True)
        if not len(need):
            L.write_receipt(L.next_rerun('mc_done_%s_%s' % (a.phase, a.segment)), [], 'SUCCEEDED', rounds=rnd, groups=len(P),
                            worst_mcse=float(P.worst_mcse.max()))
            return 0
        need = need.assign(mech=need.rtask.str.split('|').str[0], meas=need.rtask.str.split('|').str[1])
        for (mech, have, topup), g in need.groupby(['mech', 'have', 'topup']):
            meas = ','.join(sorted(g.meas))
            log = L.P('logs', 'rand_%s_topup_%s_p%d_n%d_r%d.log' % (a.segment, mech, have, topup, rnd))
            print('%s 增补：%s × [%s] 路径 %d..%d（分片 %d，%d 进程）' % (a.segment, mech, meas, have, have + topup - 1, a.chunk, a.workers), flush=True)
            r = subprocess.run([run, log, os.path.join(L.CODE, 'e6l_run_rand.py'), '--segment', a.segment, '--mechs', mech, '--meas', meas,
                                '--path0', str(int(have)), '--npaths', str(int(topup)), '--chunk', str(a.chunk), '--workers', str(a.workers)])
            if r.returncode != 0:
                print('增补失败 %s [%s] rc=%d' % (mech, meas, r.returncode), flush=True)
                return 2
    print('到达轮数上限 %d' % a.rounds, flush=True)
    return 2


if __name__ == '__main__':
    sys.exit(main())
