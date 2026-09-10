#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 补跑: 块 A 的 A_depth_extra 深度 15 四个配置 (E6e 的 P2G 锁定表无 15, 已在
   e6f_core.P2G 按同一规则补 15->g=20)。产物单独落盘, 由 merge 阶段并入。
   用法: python e6f_fix15.py --out DIR --period P --support SUP
"""
import os, sys, json, time, argparse
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K
import e6f_core as F
import e6f_desc as D
import e6f_blockA_lib as BA

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--period', required=True)
ap.add_argument('--support', default='legacy_all')
A = ap.parse_args()
TAG = '%s__%s' % (A.period, A.support)
S = F.build_segment(A.period, A.support)
if A.support == 'history_warmed' and S.warm_tag == 'no_prior_data':
    print('no_prior_data, skip'); sys.exit(0)
ctx = BA.Ctx(S)
CF = [c for c in D.gen_all() if c['layer'] == 'A_depth_extra' and c['core']['s'] == 15]
print('补跑 %d 个配置 [%s]' % (len(CF), TAG), flush=True)
rows, daily = [], {}
for c in CF:
    mk = ctx.full_mask(c)[0]
    (g, p_, u_, _), _ = F.eval_dense(S, mk, H=5)
    nh = mk.sum(axis=1)
    daily[c['config_id']] = (g, p_, u_)
    m = ~np.isnan(g)
    rows.append(dict(config_id=c['config_id'], period=A.period, support=A.support,
                     net8=F.ann(g - u_ * (F.COST / 1e4)),
                     net12=F.ann(g - u_ * (F.COST_HI / 1e4)), gross=F.ann(g),
                     turn=252 * float(np.mean(u_[m])), pos=float(np.mean(p_[m])),
                     days_valid=int(m.sum()), cost=F.ann(g) - F.ann(g - u_ * (F.COST / 1e4)),
                     layer=c['layer'], core_id=c['core_id'], veto_id=c['veto_id'],
                     family=c['family'], parent_id=c['parent_id'], H=5, neu='NS',
                     neu_veto='', anchor='', role='primary',
                     avg_nh=float(nh[nh > 0].mean()) if (nh > 0).any() else np.nan,
                     days_nohold=int((nh == 0).sum()), n_zero_weight=0))
    print('  %-34s net8 %+.3f nh %.0f' % (c['config_id'], rows[-1]['net8'], rows[-1]['avg_nh']),
          flush=True)
idx = pd.DatetimeIndex(S.dates)
cols = sorted(daily)
for nm, k in (('gross', 0), ('pos', 1), ('turn', 2)):
    p = os.path.join(A.out, 'daily', 'A_%s_%s_fix15.parquet' % (nm, TAG))
    pd.DataFrame({c: daily[c][k] for c in cols}, index=idx).to_parquet(p + '.tmp')
    os.replace(p + '.tmp', p)
p = os.path.join(A.out, 'A_oat', 'A_summary_%s_fix15.csv' % TAG)
pd.DataFrame(rows).to_csv(p + '.tmp', index=False)
os.replace(p + '.tmp', p)
open(os.path.join(A.out, 'task_status', '_DONE_A15_%s' % TAG), 'w').write(
    '%s n=%d\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), len(rows)))
print('done %d' % len(rows), flush=True)
