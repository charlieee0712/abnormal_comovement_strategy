# -*- coding: utf-8 -*-
"""E6p 旧滚动源父 P_SOURCE（brief §2 S0-2；plan §4.1：P_SOURCE(H) 固定滚动权重，与新 P_ACCOUNT 自融资账户的会计桥如实登记）。
源引擎 e6i 稀疏引擎 SE.pnl 支持任意 H → SOURCE_H_SET = {5, 10, 15, 20, 30, 40}；8 坐标（主母体 × 三记忆 + 其余 5 形态 × HG10）；四段（段首 19 日预热，源原口径）。
形成名单与源 DEV 权重直接取 E6o 源抽取（硬链缓存 fm_t / fm_c / fm_w）；H5 / 10 / 20 与 E6n 冻结账户 d_* 逐日比对（SOURCE_REPLICATION）并与 E6o 源账本逐位比对。
另出每日源目标权重和 ΣW（SOURCE_EXPOSURE_EQ_MEAN_SUMW 用）。输出 <cache>/source_e6p/<段>.npz、replication_<段>.csv。用法：python3 e6p_source.py --seg 2010-2014"""
import os
import sys
import json
import time
import argparse
import resource

import numpy as np
import pandas as pd

import e6p_core as O

COORDS = [(O.MAIN_FORM, m) for m in O.MEMS] + [(f, 'HG10') for f in O.FORMS if f != O.MAIN_FORM]
E6O_HS = (5, 10, 20)


def run(seg_name):
    import e6l_env as V
    t0 = time.time()
    seg = V.SegL(seg_name, state=False)
    cd = O.cache_dir()
    z = np.load(os.path.join(cd, 'source', '%s.npz' % seg_name), allow_pickle=False)
    T = seg.T
    arr = dict(dates=z['dates'], codes=z['codes'])
    rows = []
    for form, mem in COORDS:
        t_ = z['fm_t|%s|%s' % (form, mem)]
        c_ = z['fm_c|%s|%s' % (form, mem)]
        w_ = z['fm_w|%s|%s' % (form, mem)]
        sw = np.zeros(T)
        np.add.at(sw, t_.astype(np.int64), w_)
        arr['sumw|%s|%s' % (form, mem)] = sw
        led = seg.SE.pnl(t_.astype(np.int64), c_.astype(np.int64), w_, list(O.HS), 8.0)
        acc = np.load(O.E6N('accounts', seg_name, '%s.npz' % form), allow_pickle=False)
        adesc = [str(x) for x in acc['desc']]
        for H in O.HS:
            g, p, u, nt = led[H]
            for k, v in (('gross', g), ('pos', p), ('turn', u), ('net8', nt)):
                arr['src_%s|%s|%s|H%d' % (k, form, mem, H)] = v
            row = dict(segment=seg_name, form=form, memory=mem, H=H, n_targets=int(len(t_)))
            did = 'ANCHOR|Q0|%s|%s|H%d|s0|ALL|a0.25|f5|d+1' % (form, mem, H)
            if H in E6O_HS and did in adesc:
                i = adesc.index(did)
                mx = 0.0
                same = True
                for k, v in (('gross', g), ('pos', p), ('turn', u), ('net8', nt)):
                    ref = acc['d_' + k][i]
                    fa, fb = np.isfinite(v), np.isfinite(ref)
                    same = same and bool(np.array_equal(fa, fb))
                    if (fa & fb).any():
                        mx = max(mx, float(np.max(np.abs(v[fa & fb] - ref[fa & fb]))))
                    e6o = z['src_%s|%s|%s|H%d' % (k, form, mem, H)]
                    fe = np.isfinite(e6o)
                    same = same and bool(np.array_equal(fa, fe))
                    if (fa & fe).any():
                        mx = max(mx, float(np.max(np.abs(v[fa & fe] - e6o[fa & fe]))))
                row.update(replicated=True, nan_pattern_same=same, max_abs_diff=mx, status='PASS' if (same and mx <= 1e-9) else 'DIFFERS')
            else:
                row.update(replicated=False, nan_pattern_same='', max_abs_diff='', status='NOT_APPLICABLE')
            rows.append(row)
    od = os.path.join(cd, 'source_e6p')
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, '%s.npz' % seg_name)
    O.atomic_write_npz(p, **arr)
    pr = os.path.join(od, 'replication_%s.csv' % seg_name)
    O.atomic_write_csv(pr, pd.DataFrame(rows))
    facts = dict(segment=seg_name, T=int(T), coords=len(COORDS), H=list(O.HS), wall_s=round(time.time() - t0, 1),
                 replication_bad=int(sum(1 for r in rows if r['status'] == 'DIFFERS')),
                 rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.write_receipt('E6p_source_%s' % seg_name, [p, pr], code=[__file__, O.__file__], **facts)
    return facts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    a = ap.parse_args()
    f = run(a.seg)
    print(json.dumps(f, ensure_ascii=False), flush=True)
    if f['replication_bad']:
        sys.exit(1)


if __name__ == '__main__':
    main()
