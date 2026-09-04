# -*- coding: utf-8 -*-
"""E6c 锚点核对: h5 net8(legacy_all) vs E6/E6b scan_all  [硬闸 TOL 0.02]
   + 日序列逐日比 vs E6/E6b daily_all               [诊断列, 非硬闸 —— 用户 2026-09-04 调整 1]
   用法: python e6c_anchor.py <OUT> [seg ...]"""
import sys, os
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
from e6c_holding_horizon import ANCHOR_MAP, E6, E6B, TOL_ANCHOR
from event_study import PERIODS

OUT = sys.argv[1]; segs = sys.argv[2:] or list(PERIODS.keys())
src = {'E6': (pd.read_csv(E6 + '/scan_all.csv').set_index('cfg'), pd.read_parquet(E6 + '/daily_all.parquet')),
       'E6b': (pd.read_csv(E6B + '/scan_all.csv').set_index('cfg'), pd.read_parquet(E6B + '/daily_all.parquet'))}
rows = []
for seg in segs:
    sf = pd.read_csv(os.path.join(OUT, 'sf_%s.csv' % seg))
    dl = pd.read_parquet(os.path.join(OUT, 'daily_%s.parquet' % seg))
    h5 = dl[dl.hold == 5]
    a, e = pd.to_datetime(PERIODS[seg][0]), pd.to_datetime(PERIODS[seg][1])
    for cfg, (which, name) in ANCHOR_MAP.items():
        scan, daily = src[which]
        got = float(sf[(sf.cfg == cfg) & (sf.hold == 5) & (sf.scope == 'legacy_all')].net8_ann.iloc[0])
        anc = float(scan.loc[name, 'net_%s' % seg[:4]])
        d = abs(got - anc)
        # 诊断: 日序列
        dd = np.nan; nan_mismatch = -1
        if name in daily.columns:
            mine = h5[h5.cfg == cfg].set_index('date').net8
            theirs = daily.loc[(daily.index >= a) & (daily.index <= e), name]
            j = pd.concat([mine.rename('m'), theirs.rename('t')], axis=1)
            dd = float(np.nanmax(np.abs(j.m - j.t))) if len(j) else np.nan
            nan_mismatch = int((j.m.isna() != j.t.isna()).sum())
        rows.append(dict(period=seg, cfg=cfg, src=which, got=round(got, 4), anchor=round(anc, 4),
                         dabs=round(d, 4), ok=bool(d < TOL_ANCHOR), daily_maxdiff=dd, nan_mismatch=nan_mismatch))
chk = pd.DataFrame(rows)
p = os.path.join(OUT, 'check.csv')
if os.path.exists(p):
    old = pd.read_csv(p); chk = pd.concat([old[~old.period.isin(segs)], chk], ignore_index=True)
chk.to_csv(p, index=False)
bad = chk[~chk.ok]
print(chk.to_string(index=False))
print('\n[ANCHOR] %d/%d OK (TOL %.2f)' % (int(chk.ok.sum()), len(chk), TOL_ANCHOR))
print('[DIAG] 日序列 max|diff| 最大值 = %.3e; NaN 位置不一致格数合计 = %d'
      % (np.nanmax(chk.daily_maxdiff.values), int(chk.nan_mismatch[chk.nan_mismatch >= 0].sum())))
# 会计/重构诊断
for seg in segs:
    sf = pd.read_csv(os.path.join(OUT, 'sf_%s.csv' % seg))
    print('[RECON] %s pos_recon_err max=%.2e   bridge_err(common_mature) max=%.2e'
          % (seg, sf.pos_recon_err.max(), np.nanmax(sf.bridge_err.values)))
sys.exit(0 if bad.empty else 1)
