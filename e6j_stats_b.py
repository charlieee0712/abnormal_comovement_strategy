# -*- coding: utf-8 -*-
"""E6j B 块逐描述符统计（plan §5 / §7 / §8）：子 − 同 H 母体（8bp 日配对）、同资本、冲击（A5 κ.5 / A10 κ1）、6 / 12bp、
Δturn、Δ投入资金、HAC SE（H 与 max(2H,20)）、逐年；随机参照（有分片时）：真实 − 各机制路径均值与 MCSE。
写 results_B/descriptor_stats_<段>.csv；不写判词。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_stats as ST

ACC = os.path.join(J.RES, 'accounts', 'B')
RAN = os.path.join(J.RES, 'randoms', 'B')
OUT = os.path.join(J.RES, 'results_B')


MC_Z = 2.0          # registration/policy_P_operational_addendum.json B-1 / MC-5：|真实 − 随机均值| < 2·MCSE → 符号未定


def mc_status(d, se):
    """POS / NONPOS：符号已定（|d| ≥ MC_Z·MCSE）；MC_UNRESOLVED：MC 误差仍影响符号；NA：缺。"""
    if not (np.isfinite(d) and np.isfinite(se)):
        return 'NA'
    if d > 0 and d >= MC_Z * se:
        return 'POS'
    if d <= 0 and -d >= MC_Z * se:
        return 'NONPOS'
    return 'MC_UNRESOLVED'


def random_table(seg):
    """合并该段全部随机分片 → {描述符: {机制: (路径 ann 数组)}}。"""
    out = {}
    for p in sorted(glob.glob(os.path.join(RAN, seg, '*.npz'))):
        z = np.load(p, allow_pickle=False)
        mechs = [str(m) for m in z['mechs']]
        ann = z['ann']                                         # (机制, 路径, 描述符, 3)
        for di, d in enumerate(z['desc']):
            e = out.setdefault(str(d), {})
            for mi, m in enumerate(mechs):
                x = ann[mi, :, di, 0].astype(float)
                e.setdefault(m, []).append(x[np.isfinite(x)])
    return {d: {m: np.concatenate(v) for m, v in e.items()} for d, e in out.items()}


def run(seg):
    if seg in J.POST_SEGS:                                # 后段：封存回执之后才读（plan §10.4）
        import e6j_seal as SEAL
        ok, bad = SEAL.verify('B_post')
        if not ok:
            raise RuntimeError('后段封存核对失败：%d 个文件 hash 不符或回执不全' % len(bad))
    pz = np.load(os.path.join(ACC, seg, 'parents.npz'), allow_pickle=False)
    par = {str(k): i for i, k in enumerate(pz['keys'])}
    dates = pz['dates']
    rnd = random_table(seg)
    rows = []
    for p in sorted(glob.glob(os.path.join(ACC, seg, '*__*.npz'))):
        if os.path.basename(p).startswith('masks_'):
            continue
        z = np.load(p, allow_pickle=False)
        mother, block = os.path.basename(p)[:-4].split('__')
        sm = pd.read_csv(os.path.join(ACC, seg, 'summary_%s__%s.csv' % (mother, block))).set_index('descriptor_id')
        for i, did in enumerate(z['desc']):
            did = str(did); H = int(did.split('|')[-1][1:])
            j = par['%s|H%d' % (mother, H)]
            d, _ = ST.paired(z['net8'][i], pz['net8'][j]); D, n = ST.seg_D(d)
            dsc, _ = ST.paired(z['sc_child'][i], z['sc_parent'][i]); Dsc, _ = ST.seg_D(dsc)
            ci_ = z['net8'][i] - ST.impact_cost(z['bracket'][i], 5.0, 0.5); pi_ = pz['net8'][j] - ST.impact_cost(pz['bracket'][j], 5.0, 0.5)
            Dimp = ST.seg_D(ST.paired(ci_, pi_)[0])[0]
            cs_ = z['net8'][i] - ST.impact_cost(z['bracket'][i], 10.0, 1.0); ps_ = pz['net8'][j] - ST.impact_cost(pz['bracket'][j], 10.0, 1.0)
            Dstr = ST.seg_D(ST.paired(cs_, ps_)[0])[0]
            g6 = ST.seg_D(ST.paired(z['gross'][i] - z['turn'][i] * 6e-4, pz['gross'][j] - pz['turn'][j] * 6e-4)[0])[0]
            g12 = ST.seg_D(ST.paired(z['gross'][i] - z['turn'][i] * 12e-4, pz['gross'][j] - pz['turn'][j] * 12e-4)[0])[0]
            se = ST.hac_se(d, H)[0] * ST.ANN; se2 = ST.hac_se(d, max(2 * H, 20))[0] * ST.ANN
            y = ST.yearly(d, dates)
            s = sm.loc[did]
            real_ann = float(np.nanmean(z['net8'][i])) * ST.ANN
            r = dict(segment=seg, descriptor_id=did, row_id=s.row_id, block=block, mother=mother, slot=s.slot, measurement_id=s.measurement_id,
                     direction=s.direction, alpha=float(s.alpha), H=H, D=D, n=n, D_sc=Dsc, D_imp=Dimp, D_str=Dstr, D_6bp=g6, D_12bp=g12,
                     se_H=se, se_2H=se2, MDE80=2.80 * se, net8_ann=real_ann,
                     turn_rel=(float(np.mean(z['turn'][i])) / float(np.mean(pz['turn'][j])) - 1.0) if np.mean(pz['turn'][j]) > 0 else np.nan,
                     pos_diff=float(np.mean(z['pos'][i]) - np.mean(pz['pos'][j])), cells_changed=int(s.cells_changed_vs_parent),
                     matched_capital_share=float(s.matched_capital_share), qmiss_share=float(np.nansum(z['qmiss'][i]) / max(np.sum(z['turn'][i]), 1e-300)),
                     **{'Y%d' % k: v for k, v in y.items() if np.isfinite(v)})
            for m, x in rnd.get(did, {}).items():
                r['rand_%s' % m] = real_ann - float(x.mean()) if len(x) else np.nan
                r['mcse_%s' % m] = float(x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else np.nan
                r['npaths_%s' % m] = len(x)
                r['mc_status_%s' % m] = mc_status(r['rand_%s' % m], r['mcse_%s' % m])
            rows.append(r)
    os.makedirs(OUT, exist_ok=True)
    tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else ''
    out = os.path.join(OUT, 'descriptor_stats_%s%s.csv' % (seg, ('_' + tag) if tag else ''))
    if os.path.exists(out):
        raise RuntimeError('只增不删：%s 已存在，换 --tag' % out)
    J.atomic_write_csv(out, pd.DataFrame(rows))
    J.write_receipt('stats_b_%s%s' % (seg, ('_' + tag) if tag else ''), [out], 'SUCCEEDED', n=len(rows), random_desc=len(rnd))
    print(seg, len(rows), 'descriptors;', len(rnd), 'with randoms', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(run(sys.argv[sys.argv.index('--segment') + 1]))
