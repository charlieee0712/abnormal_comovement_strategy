# -*- coding: utf-8 -*-
"""E6j MC 增补计划（plan §8.1 / brief W14）：P 包政策 e-随机 = R-MATCH-SRC（IID）两后段主比较。
只在 P 包最新封存核对通过后读取随机分片；只计算 MCSE = sd(配对路径差) / √n（真实账户固定 → 等于随机路径年化 net8 的 sd / √n），
不读真实账户、不算真实 − 随机，因此增补与否不依赖结果方向。
规则（读数前冻结）：某 (后段, 形态, 臂) 的 12 个 (α, H) 格中最大 MCSE > .03 → 按当前 sd 估计需要的路径数，
以 512 路径为单位增补（新 path_index 接在已有最大路径号之后，不挑 seed），总数到 8,192 为首个资源复核点（到点仍 > .03 → 列出，交用户，不静默停止）。
输出 checks/mc_topup_P_round<k>.csv（逐 (段, 形态, 臂, α, H) 的 n 与 MCSE）+ queue_mc_topup_P_round<k>.txt（增补命令）。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob
import math

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_seal as SEAL

RAN = os.path.join(J.RES, 'randoms', 'P')
FORMS = ('A4b', 'M_mean3_v2', 'M_union3_v2', 'A4b_CVRv5', 'M_mean3_v2_CVRv5', 'M_union3_v2_CVRv5')
ARMS_MAIN = ('S', 'M', 'SM', 'C1')
TARGET, BLOCK, CAP = 0.03, 512, 8192


def shards(seg, form, arm):
    files = [os.path.join(RAN, seg, '%s__%s.npz' % (form, arm))] + sorted(glob.glob(os.path.join(RAN, seg, '%s__%s_p*.npz' % (form, arm))))
    return [f for f in files if os.path.exists(f)]


def iid_paths(seg, form, arm):
    """合并全部分片的 IID 年化 net8：(路径, α, H)；返回 (数组, α, H, 下一个空闲 path_index, 已用区间)。"""
    xs, end, spans, al, hs = [], 0, [], None, None
    for f in shards(seg, form, arm):
        z = np.load(f, allow_pickle=False)
        mechs = [str(m) for m in z['mechs']]
        if 'IID' not in mechs:
            continue
        a = z['ann'][mechs.index('IID')][..., 0]
        p0 = int(z['path0'][0]); spans.append((p0, p0 + a.shape[0])); end = max(end, p0 + a.shape[0])
        xs.append(a); al, hs = z['alphas'], z['Hs']
    spans.sort()
    for (a0, a1), (b0, b1) in zip(spans, spans[1:]):
        if b0 < a1:
            raise RuntimeError('路径区间重叠：%s %s %s %s' % (seg, form, arm, spans))
    return (np.concatenate(xs, axis=0) if xs else None), al, hs, end, spans


def main():
    ok, bad = SEAL.verify('P')
    if not ok:
        raise RuntimeError('P 包封存核对未过（%d 项）：先封存再读' % len(bad))
    k = 1
    while os.path.exists(os.path.join(J.RES, 'checks', 'mc_topup_P_round%d.csv' % k)):
        k += 1
    rows, cmds, capped = [], [], []
    for seg in J.POST_SEGS:
        for form in FORMS:
            for arm in ARMS_MAIN:
                x, al, hs, end, spans = iid_paths(seg, form, arm)
                if x is None:
                    raise RuntimeError('缺随机分片：%s %s %s' % (seg, form, arm))
                n = np.sum(np.isfinite(x), axis=0)
                sd = np.nanstd(x, axis=0, ddof=1)
                mcse = sd / np.sqrt(n)
                for ai, a in enumerate(al):
                    for hi, H in enumerate(hs):
                        rows.append(dict(segment=seg, form=form, arm=arm, alpha=float(a), H=int(H), n_paths=int(n[ai, hi]),
                                         mcse=float(mcse[ai, hi]), over_target=bool(mcse[ai, hi] > TARGET)))
                worst = float(np.nanmax(mcse)); ncur = int(np.min(n))
                if worst > TARGET:
                    need = int(math.ceil(ncur * (worst / TARGET) ** 2))
                    blocks = int(math.ceil(max(need - ncur, 1) / BLOCK))
                    blocks = min(blocks, max((CAP - ncur) // BLOCK, 0))
                    if blocks == 0:
                        capped.append((seg, form, arm, ncur, worst))
                    for b in range(blocks):                   # 与其余队列同格式（xargs 在代码目录启动；CPU 亲和同 brief §14）
                        cmds.append('taskset -c 96-191,288-383 python3 -u -B e6j_run_prand.py --segment %s --form %s --arm %s --paths %d --path0 %d '
                                    '--mechs IID > %s/logs/run_prand_%s_%s_%s_p%d.stdout 2>&1'
                                    % (seg, form, arm, BLOCK, end + b * BLOCK, J.RES, seg, form, arm, end + b * BLOCK))
    df = pd.DataFrame(rows)
    p = os.path.join(J.RES, 'checks', 'mc_topup_P_round%d.csv' % k); J.atomic_write_csv(p, df)
    os.makedirs(os.path.join(J.RES, 'logs'), exist_ok=True)
    q = os.path.join(J.RES, 'logs', 'queue_mc_topup_P_round%d.txt' % k); J.atomic_write_text(q, '\n'.join(cmds) + ('\n' if cmds else ''))
    J.write_receipt('mc_topup_P_round%d' % k, [p, q], 'SUCCEEDED', cells=len(df), cells_over=int(df.over_target.sum()), shards_queued=len(cmds),
                    capped=[list(map(str, c)) for c in capped])
    print('round', k, 'cells', len(df), 'over', int(df.over_target.sum()), 'max_mcse %.4f' % df.mcse.max(), 'queued', len(cmds), 'capped', len(capped))
    return 0


if __name__ == '__main__':
    sys.exit(main())
