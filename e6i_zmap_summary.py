#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Z-MAP 汇总 (plan §6.4 / §8.3)。读 randoms/<seg>/<route>_NN*.csv/.npz 与 Stage 2 逐日序列:
  每 (描述符 x 机制): 真实 net8 − 随机均值、随机 SD、MCSE、diagnostic_tail_fraction (含原样本约定)、
  逐日配对 (真实 − 路径均值) 的 NW(lag H) 标准误 (市场历史不确定性; 与 MCSE 分开列)、
  MCSE > 0.05 个年化百分点 -> need_more_paths (加轮依据 = MCSE, 不看收益)。
确定性附加对照 (reverse_sameM / reverse_new_order) 单列。输出 statistics/zmap_summary_<seg>.csv 与加轮清单。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import glob
import time

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_stats as ST

MCSE_TARGET = 0.05
KINDS = ('basic', 'industry', 'persist20')


def main():
    t0 = time.time()
    post = "--post" in sys.argv[1:]          # Stage 3 技术修复: 后段汇总 (默认推导段, 行为不变)
    od = os.path.join(I.RES, 'statistics')
    os.makedirs(od, exist_ok=True)
    more = []
    for seg in (I.POST_SEGS if post else I.DERIV_SEGS):
        rd = os.path.join(I.RES, 'randoms', seg)
        fs = [f for f in sorted(glob.glob(os.path.join(rd, '*.csv')))
              if not (os.path.basename(f).startswith('selftest') or f.endswith('_anchor.csv'))]
        if not fs:
            continue
        d = pd.concat([pd.read_csv(f, low_memory=False).assign(_src=os.path.basename(f)) for f in fs],
                      ignore_index=True)
        d = d[d.status == 'SUCCEEDED'].copy()
        # 加轮 (--path-start, 文件名带 _pNNN) 是新 draw: 同一 (描述符, 机制) 的逐路径数组拼接后重算;
        # 首轮行作底, 统计量覆盖为合并值; 路径均值逐日序列按路径数加权 (写入 statistics/zmap_merged_dmean_<seg>.npz)
        multi = d[d.kind.isin(KINDS)].groupby(['descriptor_id', 'kind'])._src.nunique()
        multi = multi[multi > 1]
        merged_dmean = {}
        if len(multi):
            srcs = d[d.kind.isin(KINDS)].groupby(['descriptor_id', 'kind'])._src.apply(list).to_dict()
            cache = {}

            def arr(src, key):
                if src not in cache:
                    z = np.load(os.path.join(rd, src.replace('.csv', '.npz')))
                    cache[src] = (z, {k: j for j, k in enumerate(z['keys'])})
                z, kp = cache[src]
                return z['a%d' % kp[key]] if key in kp else None
            upd = {}
            for (did, kind) in multi.index:
                nets, dms, ns = [], [], []
                for src in srcs[(did, kind)]:
                    x = arr(src, '%s||%s||net' % (did, kind))
                    dm = arr(src, '%s||%s||dmean' % (did, kind))
                    if x is not None:
                        nets.append(x)
                        ns.append(len(x))
                        dms.append(dm)
                if len(nets) < 2:
                    continue
                x = np.concatenate(nets)
                k = len(x)
                real_n = float(d[(d.descriptor_id == did) & (d.kind == kind)].real_net8_ann.iloc[0])
                upd[(did, kind)] = dict(n_paths=k, rand_net8_mean=float(x.mean()), rand_net8_sd=float(x.std(ddof=1)),
                                        rand_net8_mcse=float(x.std(ddof=1) / np.sqrt(k)),
                                        d_real_minus_rand=real_n - float(x.mean()),
                                        diagnostic_tail_fraction=float((1 + np.sum(x >= real_n)) / (1 + k)))
                merged_dmean[(did, kind)] = sum(dm * n for dm, n in zip(dms, ns)) / sum(ns)
            first = d.sort_values('n_paths').drop_duplicates(['descriptor_id', 'kind'], keep='last')
            for (did, kind), u in upd.items():
                ix = first.index[(first.descriptor_id == did) & (first.kind == kind)]
                for c_, v in u.items():
                    first.loc[ix, c_] = v
            d = first
        else:
            d = d.sort_values('n_paths').drop_duplicates(['descriptor_id', 'kind'], keep='last')
        # 逐日配对: 真实 (Stage 2) − 路径均值 (Z-MAP)
        idx = pd.read_csv(os.path.join(I.RES, 'accounts', seg, 'merged_index.csv'))
        pos = dict(zip(idx.descriptor_id, zip(idx.npz, idx.row)))
        real = {}
        for f, g in idx.groupby('npz'):
            with np.load(os.path.join(I.RES, 'accounts', seg, f)) as z:
                net = z['net8']
                for did, r in zip(g.descriptor_id, g.row):
                    real[did] = net[r]
        se_pair = np.full(len(d), np.nan)
        keys_by_src = {}
        for i, (src, did, kind) in enumerate(zip(d._src, d.descriptor_id, d.kind)):
            keys_by_src.setdefault(src, []).append((i, did, kind))
        for src, lst in keys_by_src.items():
            npz = os.path.join(rd, src.replace('.csv', '.npz'))
            if not os.path.exists(npz):
                continue
            with np.load(npz) as z:
                ks = list(z['keys'])
                kpos = {k: j for j, k in enumerate(ks)}
                for i, did, kind in lst:
                    if kind in KINDS:
                        k = '%s||%s||dmean' % (did, kind)
                    else:
                        k = '%s||%s||daily' % (did, kind)
                    if did not in real:
                        continue
                    if (did, kind) in merged_dmean:
                        x = real[did] - merged_dmean[(did, kind)]
                    elif k in kpos:
                        x = real[did] - z['a%d' % kpos[k]]
                    else:
                        continue
                    H = int(d.H.iloc[i])
                    _, s_, _ = ST.nw_se_masked(x[:, None], H)
                    se_pair[i] = s_[0] * I.ANN
        d['se_pair_nwH'] = se_pair
        d['need_more_paths'] = d.kind.isin(KINDS) & (d.rand_net8_mcse > MCSE_TARGET)
        keep = ['descriptor_id', 'kind', 'n_paths', 'route_id', 'mother_id', 'member_id', 'role', 'H',
                'representative', 'real_net8_ann', 'rand_net8_mean', 'rand_net8_sd', 'rand_net8_mcse',
                'd_real_minus_rand', 'se_pair_nwH', 'diagnostic_tail_fraction', 'rand_gross_mean',
                'rand_turn_mean', 'rand_pos_mean', 'real_turn', 'real_pos', 'pick_shortfall', 'noop_mismatch',
                'restricted_shortfall', 'need_more_paths', '_src']
        out = d[[c for c in keep if c in d.columns]]
        I.atomic_write_csv(os.path.join(od, 'zmap_summary_%s.csv' % seg), out)
        mm = out[out.need_more_paths]
        more.append(mm.assign(segment=seg))
        print('[%s] Z-MAP 行 %d (描述符 %d); MCSE>%.2fpp 的 (描述符, 机制) %d 个; 最大 MCSE %.3f; %.0fs' % (
            seg, len(out), out.descriptor_id.nunique(), MCSE_TARGET, len(mm),
            out.rand_net8_mcse.max(), time.time() - t0), flush=True)
    if more:
        I.atomic_write_csv(os.path.join(od, 'zmap_need_more_paths%s.csv' % ('_post' if post else '')),
                           pd.concat(more, ignore_index=True))


if __name__ == '__main__':
    main()
