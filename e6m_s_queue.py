# -*- coding: utf-8 -*-
"""E6m 阶段 S 队列（brief §5 S2–S4；附录 D-1 / D-2；plan §13.3）。每个任务一个子进程，E6M_TASK = 任务号 → 回执 task_status/<任务号>.receipt.json。
已有 SUCCEEDED 回执的任务跳过（断点续跑）；失败任务不覆盖旧回执，重跑用 --rerun 生成 <任务号>_rerun<k>。并发上限 24（云机指南）。
任务清单由 tasks(phase, segs) 唯一给出——封存（e6m_s_seal）按同一函数推算"应有任务"，不另写常量。
  masks | aux | stage_a   段 × 八形态（掩码层；Stage A 在 Stage B 冻结前跑四段，STAGE_S_IMPL_PLAN §5 第 12 项）
  accounts                段 × 八形态（后段由 e6m_s_accounts 内部 post_gate 拦）
  randoms                 段 × 八形态 × 登记机制（首 1,024 路径）
  topup                   逐段 MC 增补循环：e6m_s_stats.random_refs → mc_plan → 只跑需增补的共享路径组（机制 × 测量）→ 再规划；
                          全部 MCSE ≤ .03 或到 8,192 → 回执 mc_done_<段>
  list                    只列任务（不运行）"""
import e6j_boot  # noqa: F401
import os
import re
import sys
import json
import time
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

import e6m_core as M

FORMS = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5', 'R2', 'A06')
MAX_WORKERS = int(os.environ.get('E6M_MAX_WORKERS', '24'))      # 47：E6M_MAX_WORKERS（2026-10-11）；缺省 = 云机
RAND_CHUNK = int(os.environ.get('E6M_RAND_CHUNK', '1024'))       # 随机路径分块（1024 的约数；逐路径种子只由路径号定，分块不改结果）
assert RAND_CHUNK > 0 and 1024 % RAND_CHUNK == 0
RAND_ORDER = {'CONTENT_ISK_P5': 0, 'LEGACY_POLICY_RANDOM': 1, 'R-BAND': 2}
DEFAULT_WORKERS = dict(masks=12, aux=12, stage_a=12, memage=12, accounts=8, randoms=12, topup=12)


def mechs():
    A = M.read_csv_keep(M.P('registry', 'auxiliary_manifest_E6m.csv'), dtype=str, usecols=['item', 'mechanism'])
    return sorted(set(A[A.item.isin(['2', '3', '4']) & (A.mechanism != 'NO_NEW_CONTENT_TO_PERMUTE')].mechanism))


def py(mod, *args):
    return [sys.executable, os.path.join(M.CODE, mod)] + [str(x) for x in args]


def tasks(phase, segs):
    T = []
    for s in segs:
        for f in FORMS:
            if phase == 'masks':
                T.append(dict(task_id='S_masks_%s_%s' % (s, f), argv=py('e6m_s_run_masks.py', '--seg', s, '--form', f, '--struct', 'real')))
            elif phase == 'aux':
                T.append(dict(task_id='S_aux_%s_%s' % (s, f), argv=py('e6m_s_aux.py', '--seg', s, '--form', f, '--struct', 'real')))
            elif phase == 'memage':
                T.append(dict(task_id='S_memage_%s_%s' % (s, f), argv=py('e6m_s_memage.py', '--seg', s, '--form', f, '--struct', 'real')))
            elif phase == 'stage_a':
                T.append(dict(task_id='S_stage_a_%s_%s' % (s, f), argv=py('e6m_s_stage_a.py', '--seg', s, '--form', f, '--struct', 'real')))
            elif phase == 'accounts':
                T.append(dict(task_id='S_accounts_%s_%s' % (s, f), argv=py('e6m_s_accounts.py', '--seg', s, '--form', f)))
            elif phase == 'randoms':
                for m in mechs():
                    if RAND_CHUNK != 1024 and receipt_status('S_rand_%s_%s_%s_p0_1024' % (s, f, m)) == 'SUCCEEDED':   # 已有整段分片：不再分块（防重复计数）
                        continue
                    for p0 in range(0, 1024, RAND_CHUNK):
                        T.append(dict(task_id='S_rand_%s_%s_%s_p%d_%d' % (s, f, m, p0, RAND_CHUNK), mech=m,
                                      argv=py('e6m_s_rand_run.py', '--seg', s, '--form', f, '--mode', 'accounts', '--mech', m, '--path0', p0,
                                              '--npaths', RAND_CHUNK)))
            else:
                raise ValueError(phase)
    if phase == 'randoms':                       # 大机制先跑（缩短尾部；2026-10-11）
        T.sort(key=lambda t: RAND_ORDER.get(t.get('mech'), 9))
    return T


def receipt_status(task_id):
    p = M.P('task_status', '%s.receipt.json' % re.sub(r'[:/|]', '_', task_id))
    return json.load(open(p, encoding='utf-8')).get('status') if os.path.exists(p) else 'MISSING'


MEM_BUDGET_GB = float(os.environ.get('E6M_MEM_BUDGET_GB', '78.0'))                         # 云机指南总内存 ≤ 80 GB，留 2 GB 余量


def receipt_rss(task_id):
    p = M.P('task_status', '%s.receipt.json' % re.sub(r'[:/|]', '_', task_id))
    return json.load(open(p, encoding='utf-8')).get('rss_peak_gb') if os.path.exists(p) else None


def canary_first(T):
    """金丝雀：最重的任务先单独跑（优先 2019-2023 × A4b，名单阶段 A4b 最慢、该段最长），用其回执 rss_peak_gb 定并发。"""
    k = next((i for i, t in enumerate(T) if '2019-2023' in t['task_id'] and '_A4b_' in t['task_id'] + '_'), 0)
    return [T[k]] + T[:k] + T[k + 1:]


def run_tasks(T, workers, tag, rerun=False, canary=True):
    workers = max(1, min(int(workers), MAX_WORKERS))
    canary = canary and os.environ.get('E6M_CANARY', '1') != '0'      # 47 试跑已得 rss（≈ 8.7 GB）：E6M_CANARY=0 不再单跑金丝雀
    os.makedirs(M.P('queue'), exist_ok=True)
    os.makedirs(M.P('logs', 'queue'), exist_ok=True)
    rows = []
    if canary and len(T) > 1:
        T = canary_first(T)

    def one(t):
        tid = t['task_id']
        if receipt_status(tid) == 'SUCCEEDED' and not rerun:
            return dict(task_id=tid, status='SKIPPED_ALREADY_SUCCEEDED', rc=0, start='', end='')
        if rerun:
            k = 1
            while receipt_status('%s_rerun%s' % (tid, '' if k == 1 else k)) != 'MISSING':
                k += 1
            tid = '%s_rerun%s' % (tid, '' if k == 1 else k)
        env = dict(os.environ, E6M_TASK=tid, E6M_STAGE='S')
        st = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(M.P('logs', 'queue', '%s.log' % re.sub(r'[:/|]', '_', tid)), 'w', encoding='utf-8') as fh:
            rc = subprocess.run(t['argv'], env=env, stdout=fh, stderr=subprocess.STDOUT).returncode
        return dict(task_id=tid, status=receipt_status(tid) if rc == 0 else 'FAILED_RC', rc=rc, start=st, end=time.strftime('%Y-%m-%d %H:%M:%S'))
    if canary and len(T) > 1:
        r0 = one(T[0])
        rows.append(r0)
        print(json.dumps(r0, ensure_ascii=False), flush=True)
        rss = receipt_rss(r0['task_id'])
        if rss:
            w2 = max(1, min(workers, int(MEM_BUDGET_GB // max(float(rss) * 1.15, 0.5))))     # 15% 余量（其它任务可能略重）
            print(json.dumps(dict(canary=r0['task_id'], rss_peak_gb=rss, workers_requested=workers, workers_used=w2), ensure_ascii=False), flush=True)
            workers = w2
        T = T[1:]
    with ThreadPoolExecutor(workers) as ex:
        for r in ex.map(one, T):
            rows.append(r)
            print(json.dumps(r, ensure_ascii=False), flush=True)
    df = pd.DataFrame(rows)
    p = M.P('queue', '%s_%s.csv' % (tag, time.strftime('%Y%m%d_%H%M%S')))
    M.atomic_write_csv(p, df)
    return df


def topup(seg, workers, rounds=16):
    """e6l_topup 同构：规划 → 只跑需增补的共享路径组 → 再规划。规划只读随机路径离散（不读真实账户）。"""
    import e6m_s_stats as ST
    import e6m_s_rand_run as RR
    for rnd in range(rounds):
        R, _, _ = ST.random_refs(M.P('randoms'), seg, {})
        P = ST.mc_plan(R)
        os.makedirs(M.P('results', 'mc'), exist_ok=True)
        M.atomic_write_csv(M.P('results', 'mc', 'mc_plan_%s_r%d.csv' % (seg, rnd)), P)
        need = P[P.topup > 0] if len(P) else P
        print('%s 第 %d 轮：%d / %d 组需增补' % (seg, rnd, len(need), len(P)), flush=True)
        if not len(need):
            M.write_receipt('mc_done_%s' % seg, [M.P('results', 'mc', 'mc_plan_%s_r%d.csv' % (seg, rnd))], status='SUCCEEDED', code=[__file__, M.__file__],
                            rounds=rnd, groups=len(P), worst_mcse=float(P.worst_mcse.max()) if len(P) else None)
            return 0
        T = []
        for r in need.itertuples():
            mech, grp = r.rtask.split('|', 1)
            for f in FORMS:
                if any(RR.group_of(x['owner_id']) == grp for x in RR.rand_rows(f, mech)):
                    T.append(dict(task_id='S_rand_%s_%s_%s_p%d_%d_%s' % (seg, f, mech, r.have, r.topup, grp),
                                  argv=py('e6m_s_rand_run.py', '--seg', seg, '--form', f, '--mode', 'accounts', '--mech', mech, '--group', grp,
                                          '--path0', int(r.have), '--npaths', int(r.topup))))
        df = run_tasks(T, workers, 'topup_%s_r%d' % (seg, rnd))
        if (df.rc != 0).any():
            print('增补失败：%s' % list(df[df.rc != 0].task_id[:5]), flush=True)
            return 2
    print('到达轮数上限 %d' % rounds, flush=True)
    return 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('phase', choices=['masks', 'aux', 'stage_a', 'memage', 'accounts', 'randoms', 'topup', 'list'])
    ap.add_argument('--segs', default=','.join(M.SEGMENTS))
    ap.add_argument('--workers', type=int, default=0)
    ap.add_argument('--rerun', action='store_true')
    ap.add_argument('--of', default='masks', help='list：列哪一类')
    a = ap.parse_args()
    segs = [s for s in a.segs.split(',') if s]
    if a.phase == 'list':
        T = tasks(a.of, segs)
        st = pd.Series([receipt_status(t['task_id']) for t in T]).value_counts().to_dict()
        print(json.dumps(dict(of=a.of, segs=segs, tasks=len(T), receipt_status=st), ensure_ascii=False))
        return 0
    w = a.workers or int(os.environ.get('E6M_WORKERS', '0')) or DEFAULT_WORKERS[a.phase]
    if a.phase == 'topup':
        rc = 0
        for s in segs:
            rc = max(rc, topup(s, w))
        return rc
    df = run_tasks(tasks(a.phase, segs), w, '%s_%s' % (a.phase, '_'.join(segs)), rerun=a.rerun)
    return 0 if (df.rc == 0).all() else 1


if __name__ == '__main__':
    sys.exit(main())
