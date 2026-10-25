# -*- coding: utf-8 -*-
"""E6o 主母体随机精度增补（brief §6"按 MCSE ≤ .01 ann_pp 增补至 ≤ 1,024"；附录 B.7 / D 脚本 S11）：
  python3 e6o_topup.py --workers 96 [--list]
精度集 = random_scope 中 AMOUNT_MATCH topup_to = 1024 的 owner（主母体 × 3 记忆 × 4 主触发）
       ∪ D 脚本 S11 规则命中的 owner（FEASIBLE、A4b_CVRv5、H5、主触发 4、ENGINE_NATIVE、ALLOW）。
按 FULL 段 MCSE 分两档增补：先把精度集全部补到 384 路径；FULL mcse 仍 > .01 的再补到 1,024（上限；仍 > .01 由 e6o_policy 记 MC_LIMIT）。
档位事前固定（384 / 1,024），每档只看 FULL mcse（不看 D 的大小或符号）。种子同 B 主文件（stable_u64('E6o', 机制, path_id)）。
输出 randoms/random_paths_B_topup1.csv、random_paths_B_topup2.csv（与 B 主文件同列；e6o_policy 以 random_paths_B*.csv 合并）。"""
import sys
import glob
import time
import argparse
import resource
from multiprocessing import get_context

import numpy as np
import pandas as pd

import e6o_core as O
import e6o_engine as E
import e6o_acct as A
import e6o_run as RUN

PRIMARY4 = ('T1a', 'T1b', 'T3c15_X', 'T4a')
STAGES = (384, 1024)
TARGET_MCSE = 0.01


def precision_owners(R, RS):
    am = RS[RS.mechanism == 'AMOUNT_MATCH']
    s = set(am[pd.to_numeric(am.topup_to, errors='coerce').fillna(0) >= 1024].owner_exec_id)
    c = R[(R.series == 'C_ACCOUNT') & (R.execution_profile == 'FEASIBLE_DAILY')]
    for e in c.exec_id:
        p = e.split('|')
        if len(p) == 16 and p[0] == O.MAIN_FORM and p[3] == 'H5' and p[4] in PRIMARY4 and p[5] == 'ENGINE_NATIVE' and p[8] == 'ALLOW':
            s.add(e)
    return sorted(s & set(am.owner_exec_id))


def full_mcse(owners):
    """当前全部 B 路径（主文件 + 已有增补）的 FULL D（四段有效日 n 加权，同 e6o_policy）→ 每 owner (路径数, mcse)。"""
    fs = sorted(glob.glob(O.P('randoms', 'random_paths_B*.csv')))
    D = pd.concat([pd.read_csv(f, keep_default_na=False, na_values=['']) for f in fs], ignore_index=True)
    D = D[(D.mechanism == 'AMOUNT_MATCH') & D.owner_exec_id.isin(owners)]
    out = {}
    for e, g in D.groupby('owner_exec_id'):
        Dm = np.vstack([g['D_%s' % s].to_numpy(float) for s in O.SEGS])
        W = np.vstack([g['n_%s' % s].to_numpy(float) for s in O.SEGS])
        with np.errstate(all='ignore'):
            full = np.nansum(Dm * W, 0) / np.nansum(np.where(np.isfinite(Dm), W, 0), 0)
        ok = np.isfinite(full)
        n = int(ok.sum())
        out[e] = (int(g.path_id.max()) + 1, float(np.std(full[ok], ddof=1) / np.sqrt(n)) if n > 1 else np.inf)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=96)
    ap.add_argument('--batch', type=int, default=16)
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    R = pd.read_csv(O.P('registration', 'registry_E6o.csv'), keep_default_na=False, na_values=[''])
    RS = pd.read_csv(O.P('registration', 'random_scope_E6o.csv'), keep_default_na=False)
    owners = precision_owners(R, RS)
    fam = R.set_index('exec_id').loc[owners, 'family'].value_counts().to_dict()
    O.log('精度集 %d 个 owner：%s' % (len(owners), fam))
    if a.list:
        for e in owners:
            print(e)
        return
    RUN.gate_post('topup B')
    RUN.setup()
    RUN.G['segmask'] = RUN.segmasks()
    P = RUN.plan().set_index('exec_id', drop=False)
    t0 = time.time()
    outs = []
    hist = []
    nf = 0
    for k, target in enumerate(STAGES, 1):
        cur = full_mcse(owners)
        need = [e for e in owners if cur.get(e, (0, np.inf))[1] > TARGET_MCSE and cur.get(e, (0, np.inf))[0] < target]
        hist.append(dict(stage=k, target=target, n_need=len(need), mcse_before={e: [cur.get(e, (0, np.inf))[0], round(cur.get(e, (0, np.inf))[1], 5)] for e in owners}))
        O.log('增补第 %d 档（→ %d 路径）：%d / %d 个 owner FULL mcse > %.2f' % (k, target, len(need), len(owners), TARGET_MCSE))
        if not need:
            continue
        jobs = []
        for e in need:
            p = P.loc[e].to_dict()
            ph = p['parent_exec_id'] and P.loc[p['parent_exec_id']]['exec_hash']
            for b0 in range(cur[e][0], target, a.batch):
                jobs.append(('B', p, ph, 'AMOUNT_MATCH', list(range(b0, min(target, b0 + a.batch)))))
        jobs.sort(key=lambda j: (j[1]['exec_hash'], j[4][0]))
        rows = []
        t1 = time.time()
        with get_context('fork').Pool(a.workers) as pool:
            for i, r in enumerate(pool.imap(RUN.job_random, jobs, chunksize=1)):
                rows.extend(r)
                if (i + 1) % 500 == 0:
                    O.log('增补第 %d 档 %d/%d 批（%.0f s）' % (k, i + 1, len(jobs), time.time() - t1))
        D = pd.DataFrame(rows)
        p_ = O.P('randoms', 'random_paths_B_topup%d.csv' % k)
        O.atomic_write_csv(p_, D.drop(columns=[c for c in ('tb',) if c in D.columns]))
        outs.append(p_)
        nf += int((D.status == 'FAILED').sum()) if 'status' in D.columns else 0
        O.log('增补第 %d 档完成：%d 行，%.0f s' % (k, len(D), time.time() - t1))
        if nf:
            break
    fin = full_mcse(owners)
    O.write_receipt('E6o_randoms_B_topup', outs, code=[__file__, RUN.__file__, E.__file__, A.__file__], failed=nf, owners=len(owners), families=fam,
                    stages=hist, final={e: dict(paths=v[0], mcse=round(v[1], 5)) for e, v in fin.items()},
                    wall_s=round(time.time() - t0, 1), rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.log('增补完成：最终路径数 %s；FULL mcse 最大 %.4f；失败 %d；%.0f s' % (sorted(set(v[0] for v in fin.values())), max(v[1] for v in fin.values()), nf, time.time() - t0))
    if nf:
        sys.exit(1)


if __name__ == '__main__':
    main()
