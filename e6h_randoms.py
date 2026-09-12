#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 主路径的随机参照 (plan §4.4, brief §5)。

每条卡的【中心代表】(事前按源清楚选, 不按收益) 在其主母体上, 做三层匹配随机:
  U_IID    同日同人数, 在【该操作真正能动的域】内均匀抽
  I_IID    同日同【行业人数】
  I_P20    固定 20 交易日块的持续性抽样 (plan §4.4: 不声称精确匹配真实换手)
各 256 起; **MCSE > 0.05 个年化百分点时补到 512 / 1024**, 补样规则事前写死,
不依据增量正负补样。

域按操作定 (plan §4.4: "ADD 的随机候选从同 D 取, 同日同新增人数"):
  加型 (ADD/SWAP/CONJ/I-P up) -> 在 D 内随机挑同样多只加进 B
  减型 (FOCAL_*/VETO_IN_B/I-P down) -> 在 B 内随机删同样多只
  混合 (SLOT/MARGIN) -> 在合法域内随机取同样多只组成名单

输出 `reference_tail_fraction` = 真实结果在随机分布里的位置。
**它不是 p 值** (plan §4.4 / R8): 本项目的匹配随机不满足精确检验的不变性条件。

用法: python3 e6h_randoms.py --segment 2010-2014 [--draws 256]
"""
from __future__ import annotations
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_rules as RU
import e6h_run_routes as RR
import e6h_expand as EX
import e6g_core as G
import e6f_core as F
import e6e_core as K

RES = H.RES
SEED0 = 20260912
MCSE_TARGET = 0.05          # 年化百分点

# 中心代表: (route_id, 主母体, 选描述符的过滤条件) —— 事前按源清楚选
CENTERS = [
    ('M-T-tcv-vs-t60', 'A06', dict(new_key='TCV_20', alpha=0.5, policy='FALLBACK')),
    ('M-C-position-window', 'A06', dict(new_key='CVR_5d', alpha=0.5, policy='FALLBACK')),
    ('E-V-quiet-price', 'R1', dict(vol_key='volume_ratio_3d', cond_mode='joint',
                                   price_cond='REL_LOW_q20', q=0.2, eta=0.25,
                                   role='ADD')),
    ('E-V-surge-price', 'R1', dict(vol_key='volume_ratio_3d', cond_mode='joint',
                                   price_cond='REL_LOW_q20', q=0.2, eta=0.25,
                                   role='ADD')),
    ('E-P-path-conditional-focal', 'R2', dict(state_key='positive_day_ratio_5d',
                                              state_cmp='ge', state_th=0.8,
                                              mode='exempt', k=10)),
    ('R-O-overnight-risk', 'A06', dict(risk_key='JUMP_20', k=10, role='VETO_IN_B')),
    ('I-P-peer-up-laggard', 'R1', dict(w=20, q=0.2, eta=0.25, role='ADD')),
    ('I-P-peer-down-risk', 'R1', dict(w=20, k=10)),
    ('L-Q-margin-liquidity', 'A06', dict(liq_key='amihud_daily', e=0.25,
                                         order='cheap_first')),
]


def pick(rows, rid, parent, filt):
    for r in rows:
        if r['route_id'] != rid or r['parent'] != parent or r.get('is_identity'):
            continue
        if all(str(r.get(k)) == str(v) for k, v in filt.items()):
            return r
    return None


def draw_matched(S, domain, counts, level, rng, icodes):
    """在 domain 内按 level 抽 counts[t] 只。返回 (T,Nc) bool。"""
    T, Nc = domain.shape
    out = np.zeros((T, Nc), bool)
    if level == 'I_P20':
        # 固定 20 交易日块: 块内沿用同一优先级序
        prio = rng.random(Nc)
        for t in range(T):
            k = int(counts[t])
            if k <= 0:
                continue
            if t % 20 == 0:
                prio = rng.random(Nc)
            v = np.where(domain[t])[0]
            if len(v) == 0:
                continue
            out[t, v[np.argsort(prio[v])[:min(k, len(v))]]] = True
        return out
    for t in range(T):
        k = int(counts[t])
        if k <= 0:
            continue
        v = np.where(domain[t])[0]
        if len(v) == 0:
            continue
        if level == 'U_IID':
            out[t, v[rng.permutation(len(v))[:min(k, len(v))]]] = True
        else:                                   # I_IID: 同行业人数
            # counts 按行业拆: 用真实动作在各行业的人数
            pass
    return out


def industry_plan(S, domain, target_set):
    """预计算逐日的行业配额与可选位置 —— 只算一次, 256 个 draw 复用。
       返回 [(t, pos_sorted_by_industry, group_starts, group_sizes, quotas)]。"""
    ic = S.icodes
    plan = []
    for t in range(S.T):
        tg = target_set[t]
        if not tg.any():
            continue
        codes = ic[t]
        dom = domain[t] & (codes >= 0)
        if not dom.any():
            continue
        pos = np.where(dom)[0]
        cp = codes[pos]
        order = np.argsort(cp, kind='stable')
        pos, cp = pos[order], cp[order]
        uq, starts = np.unique(cp, return_index=True)
        sizes = np.diff(np.append(starts, len(cp)))
        tq = np.bincount(codes[tg & (codes >= 0)], minlength=S.G)
        quotas = np.minimum(tq[uq], sizes)
        keep = quotas > 0
        if not keep.any():
            continue
        plan.append((t, pos, starts[keep], sizes[keep], quotas[keep]))
    return plan


def draw_industry_fast(S, plan, rng):
    """用预计算的配额抽一次。组内用随机键取前 k 个 (等价于无放回抽样)。"""
    out = np.zeros((S.T, S.Nc), bool)
    for t, pos, starts, sizes, quotas in plan:
        r = rng.random(len(pos))
        for st, sz, q in zip(starts, sizes, quotas):
            seg = slice(st, st + sz)
            idx = pos[seg]
            if q >= sz:
                out[t, idx] = True
            else:
                out[t, idx[np.argpartition(r[seg], q - 1)[:q]]] = True
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--draws', type=int, default=256)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshard', type=int, default=1)
    a = ap.parse_args()
    assert a.segment in H.DERIV_SEGS
    t0 = time.time()
    rows_all = EX.all_descriptors()
    S = H.seg(a.segment, verbose=False)
    od = os.path.join(RES, 'random_registry')
    os.makedirs(od, exist_ok=True)

    out, pctx = [], {}
    for ci, (rid, parent, filt) in enumerate(CENTERS):
        if ci % a.nshard != a.shard:
            continue
        r = pick(rows_all, rid, parent, filt)
        if r is None:
            out.append(dict(route_id=rid, parent=parent, segment=a.segment,
                            status='center_not_found', filt=str(filt)))
            print('  !! %s 的中心代表没找到: %s' % (rid, filt), flush=True)
            continue
        if parent not in pctx:
            pctx[parent] = RR.ParentCtx(S, parent)
        P = pctx[parent]
        mask, wmul, _ = RR.build_mask(P, r)
        real = RU.run_mask(S, mask, wmul)
        added = mask & ~P.B
        removed = P.B & ~mask
        if added.sum() > 0 and removed.sum() == 0:
            kind, domain, changed = 'additive', P.D, added
        elif removed.sum() > 0 and added.sum() == 0:
            kind, domain, changed = 'subtractive', P.B, removed
        else:
            kind, domain, changed = 'mixed', P.legal, mask
        counts = changed.sum(axis=1)
        iplan = industry_plan(S, domain, changed)
        for level in ("U_IID", "I_IID", "I_P20"):
            n_draw, means = a.draws, []
            while True:
                rng = np.random.default_rng(SEED0 + abs(hash((rid, parent, level))) % 10 ** 6)
                means = []
                for j in range(n_draw):
                    if level == 'I_IID':
                        rs = draw_industry_fast(S, iplan, rng)
                    else:
                        rs = draw_matched(S, domain, counts, level, rng, S.icodes)
                    if kind == 'additive':
                        m2 = P.B | rs
                    elif kind == 'subtractive':
                        m2 = P.B & ~rs
                    else:
                        m2 = rs
                    means.append(H.ann(RU.run_mask(S, m2)[3]))
                mm = float(np.mean(means))
                sd = float(np.std(means, ddof=1))
                mcse = sd / np.sqrt(n_draw)
                if mcse <= MCSE_TARGET or n_draw >= 1024:
                    break
                n_draw = 512 if n_draw < 512 else 1024
            real8 = H.ann(real[3])
            tail = float(np.mean(np.asarray(means) >= real8))
            out.append(dict(route_id=rid, parent=parent, segment=a.segment,
                            descriptor_id=r['descriptor_id'], kind=kind,
                            match_level=level, n_draws=n_draw,
                            real_net8=real8, parent_net8=H.ann(P.pnl[3]),
                            random_mean=mm, random_sd=sd, mcse=mcse,
                            mcse_ok=bool(mcse <= MCSE_TARGET),
                            real_minus_random=real8 - mm,
                            reference_tail_fraction=tail,
                            n_changed_cells=int(changed.sum()),
                            note='tail_fraction 不是 p 值 (plan §4.4 / R8)'))
            print('    %-28s %-7s n=%4d 真实 %+.3f 随机 %+.3f 差 %+.3f MCSE %.4f 尾部 %.3f'
                  % (rid, level, n_draw, real8, mm, real8 - mm, mcse, tail), flush=True)
    pd.DataFrame(out).to_csv(
        os.path.join(od, 'random_refs_%s%s.csv' % (a.segment, '' if a.nshard==1 else '_s%d'%a.shard)), index=False)
    print('  [%s] 随机参照 %d 行, %.0fs' % (a.segment, len(out), time.time() - t0))


if __name__ == '__main__':
    main()
